#!/usr/bin/env python3
"""B3 Crossref / publisher-record check of docs/references.bib.

Subcommands (run from anywhere; paths are resolved from the repository root):

  fetch     GET https://api.crossref.org/works/<DOI> for every entry with a doi
            field; for entries without one, GET /works?query.bibliographic=...
            (plus ISBN filter, arXiv API, DataCite, GitHub API, Google Patents
            where the entry calls for it).  Accepted search candidates are then
            fetched from /works/<DOI>.  Responses are cached (see CACHE); an
            existing 200 response is never re-downloaded unless --refresh.
  apply     apply tools/bib/b3_corrections.yaml to docs/references.bib.  Every
            value written from Crossref is copied from the cached record; DOIs
            are never typed, only copied from a cached /works response.
  report    compare the BASELINE bib (git rev below) and the CURRENT bib against
            the cached records; write docs/agent_reports/B3_crossref_results.tsv
            and the generated block of B3_crossref_verification_log.md; print
            the counts.  Every count in the log is produced here.
  validate  syntax check of docs/references.bib (balanced braces, unique keys,
            notes, DOI shape, no doi in the UNVERIFIED section, every doi backed
            by a cached HTTP-200 registry record carrying that DOI).

No e-mail address is sent anywhere; the User-Agent is "Holography-bibcheck/1.0".
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import html
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bibtools as bt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BIB = ROOT / "docs" / "references.bib"
REPORTS = ROOT / "docs" / "agent_reports"
CACHE = REPORTS / "crossref_cache"
INDEX = CACHE / "_index.json"
TSV = REPORTS / "B3_crossref_results.tsv"
LOG = REPORTS / "B3_crossref_verification_log.md"
CORR = Path(__file__).resolve().parent / "b3_corrections.yaml"
SCRATCH = Path("/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/bib")
BASELINE_REV = "4a9df525a7d33ad974293e0cac04f31e479fc816"
UA = "Holography-bibcheck/1.0"
CROSSREF = "https://api.crossref.org/works"

# Titles in the baseline that are placeholders, not article titles (their own
# notes say so).  For these the title is untestable and is left out of queries.
PLACEHOLDER_TITLE = {"U04", "U06", "U13", "U14", "HANADA95", "SIMTRHEPD-CPC"}
# Software / web records: verified on the publisher (repository or vendor) page.
SOFTWARE = {"S01", "S02", "SIMTRHEPD", "PYMULTISLICE", "U12", "U17", "U18", "RHEEDIUM"}


# ======================================================================= HTTP
def load_index():
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}


def save_index(idx):
    INDEX.write_text(json.dumps(idx, indent=1, sort_keys=True) + "\n")


def http_get(url, accept="application/json", tries=4):
    last = (None, b"")
    for k in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as exc:
            last = (exc.code, exc.read())
            if exc.code not in (429, 500, 502, 503, 504):
                return last
        except Exception as exc:  # network error
            last = (None, str(exc).encode())
        time.sleep(2 * (k + 1))
    return last


def cached_get(name, url, idx, refresh=False, accept="application/json", where=CACHE):
    """Fetch url into where/name unless a 200 copy exists. Returns (status, bytes|None)."""
    path = where / name
    rec = idx.get(name)
    if rec and rec.get("status") == 200 and path.exists() and not refresh:
        return 200, path.read_bytes()
    status, body = http_get(url, accept=accept)
    idx[name] = {"url": url, "status": status,
                 "fetched_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "stored": str(path.relative_to(ROOT)) if str(path).startswith(str(ROOT)) else str(path)}
    if status == 200:
        path.write_bytes(body)
    elif path.exists():
        path.unlink()
    save_index(idx)
    time.sleep(0.4)
    return status, (body if status == 200 else None)


def works_url(doi):
    return f"{CROSSREF}/{urllib.parse.quote(doi, safe='/()._;:-')}"


# ======================================================================= bib access
def read_baseline():
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{BASELINE_REV}:docs/references.bib"],
                          check=True, capture_output=True, text=True).stdout


def entries_by_key(text):
    return {e.key: e for e in bt.parse(text)}


def u(e, name):
    v = e.get(name)
    return bt.latex_to_unicode(v) if v is not None else None


def bib_names(e):
    raw = e.get("author") or e.get("editor")
    if not raw:
        return [], None
    role = "author" if e.get("author") else "editor"
    return [bt.parse_name(n) for n in bt.split_names(raw)], role


def bib_piis(e):
    blob = " ".join(f.value for f in e.fields if f.name in ("url", "howpublished", "note"))
    out = set()
    for m in re.finditer(r"pii/(S?[0-9X]{4}-?[0-9X]{4}\(?\d{2}\)?[0-9X-]{5,8}[0-9A-Z])", blob):
        out.add(re.sub(r"[^0-9A-Z]", "", m.group(1).upper()))
    for m in re.finditer(r"PII\s+(S?[0-9X]{8,}[0-9A-Z]*)", blob):
        out.add(re.sub(r"[^0-9A-Z]", "", m.group(1).upper()))
    return out


def query_string(key, e):
    names, _ = bib_names(e)
    parts = [n["family"] for n in names[:3] if "family" in n]
    title = u(e, "title") or ""
    if key == "U01":
        title = title.split(" (title as displayed")[0]
    if key == "U05":
        title = title.split(" (proceedings")[0] + " International Workshop on Electron Holography"
    if key not in PLACEHOLDER_TITLE:
        parts.append(title)
    for f in ("journal", "booktitle", "publisher", "volume", "year"):
        if e.get(f):
            parts.append(u(e, f))
    if e.get("pages"):
        parts.append(u(e, "pages").split("\u2013")[0])
    return " ".join(p for p in parts if p)


# ======================================================================= comparison
def cr_title(rec):
    t = " ".join(rec.get("title") or [])
    sub = " ".join(rec.get("subtitle") or [])
    t = re.sub(r"<[^>]+>", "", html.unescape(t)).strip()
    sub = re.sub(r"<[^>]+>", "", html.unescape(sub)).strip()
    return (t + (": " + sub if sub and fold_eq_missing(t, sub) else "")).strip()


def fold_eq_missing(t, sub):
    return bt.fold(sub) not in bt.fold(t)


def cr_years(rec):
    out = {}
    for k in ("published-print", "published-online", "issued", "published"):
        dp = (rec.get(k) or {}).get("date-parts") or [[None]]
        if dp and dp[0] and dp[0][0]:
            out[k] = "-".join(str(x) for x in dp[0])
    return out


def cr_pages(rec):
    if rec.get("page"):
        p = rec["page"].replace("\u2013", "-")
        a, _, b = p.partition("-")
        return a.strip(), b.strip()
    if rec.get("article-number"):
        return str(rec["article-number"]), ""
    return None, None


def bib_pages(e):
    p = u(e, "pages")
    if not p:
        return None, None
    a, _, b = p.replace("\u2013", "-").partition("-")
    return a.strip(), b.strip().lstrip("-")


def names_of(rec, role):
    lst = rec.get(role) or []
    out = []
    for a in lst:
        if "family" in a:
            out.append({"family": html.unescape(a["family"]).strip(), "given": html.unescape(a.get("given", "")).strip()})
        elif "name" in a:
            out.append({"family": a["name"].strip(), "given": ""})
    return out


def given_conflict(bg, cg):
    bi, ci = bt.initials(bg), bt.initials(cg)
    if bi and ci and not (bi.startswith(ci) or ci.startswith(bi)):
        return True
    btok = [t for t in re.split(r"[\s.\-]+", bt.fold(bg)) if t]
    ctok = [t for t in re.split(r"[\s.\-]+", bt.fold(cg)) if t]
    return any(len(x) > 1 and len(y) > 1 and x != y for x, y in zip(btok, ctok))


def compare(key, e, rec, placeholder=None):
    """Compare a bib entry with a Crossref /works message. Returns (checked, discrepancies, info)."""
    checked, disc, info = [], [], {}
    # ---- authors / editors
    names, role = bib_names(e)
    artlike = e.etype == "article" or bool(e.get("journal"))
    if e.etype == "incollection" and role == "editor":
        names = []          # the book's editors are not compared with the chapter's authors
    if not names and names_of(rec, "author"):
        disc.append(("author", "(absent)", fmt_names(names_of(rec, "author")), "missing"))
    if names:
        crn = names_of(rec, role) or names_of(rec, "author" if role == "editor" else "editor")
        checked.append(role)
        others = any(n.get("others") for n in names)
        real = [n for n in names if not n.get("others")]
        if not crn:
            info["names"] = "Crossref record carries no author/editor list; names checked on the publisher page only"
        else:
            if (others and len(real) >= len(crn)) or (not others and len(real) != len(crn)):
                disc.append((role + "-count", f"{len(real)}{' + others' if others else ''}", str(len(crn)), "count"))
            elif others:
                disc.append((role + "-count", f"{len(real)} + others", f"{len(crn)} (full list available)", "incomplete"))
            for i, (bn, cn) in enumerate(zip(real, crn)):
                if bn["family"].replace("\u2019", "'") != cn["family"].replace("\u2019", "'"):
                    kind = "diacritics" if bt.fold(bn["family"]) == bt.fold(cn["family"]) else "family"
                    if kind == "family" and bt.fold(bn["family"]).replace(" ", "") == bt.fold(cn["family"]).replace(" ", ""):
                        kind = "spacing"
                    disc.append((f"{role}[{i+1}].family", bn["family"], cn["family"], kind))
                bi, ci = bt.initials(bn["given"]), bt.initials(cn["given"])
                if given_conflict(bn["given"], cn["given"]):
                    # inconsistent initials, or two spelled-out given names that differ
                    # (a fuller or shorter form of the same name is not a discrepancy)
                    disc.append((f"{role}[{i+1}].given", bn["given"], cn["given"], "given"))
                elif not bi and ci:
                    disc.append((f"{role}[{i+1}].given", "(none)", cn["given"], "given-missing"))
    # ---- title
    if placeholder is None:
        placeholder = key in PLACEHOLDER_TITLE
    if not placeholder:
        checked.append("title")
        bt_ = u(e, "title")
        ct = cr_title(rec)
        if bt.fold(bt_) != bt.fold(ct):
            r = difflib.SequenceMatcher(None, bt.fold(bt_), bt.fold(ct)).ratio()
            if ":" in bt_ and bt.fold(bt_.split(":")[0]) == bt.fold(ct):
                info["title"] = "Crossref record has the main title only (no subtitle); subtitle checked on the publisher page"
            else:
                disc.append(("title", bt_, ct, f"ratio={r:.2f}"))
    else:
        disc.append(("title", "(placeholder)", cr_title(rec), "placeholder"))
    # ---- container
    cont = u(e, "journal") or u(e, "booktitle")
    ccont = [html.unescape(c) for c in (rec.get("container-title") or [])]
    if cont:
        checked.append("container-title")
        fb = bt.fold(cont)
        if not any(fb == bt.fold(c) for c in ccont):
            if any(bt.fold(c).startswith(fb) or fb.startswith(bt.fold(c)) for c in ccont if c):
                info["container_form"] = f"bib '{cont}' is a prefix form of Crossref '{ccont[0]}'"
            else:
                disc.append(("container-title", cont, " | ".join(ccont) or "(none)", "container"))
    # ---- volume / issue / pages
    if e.get("volume") or rec.get("volume"):
        if e.get("volume"):
            checked.append("volume")
            if u(e, "volume") != str(rec.get("volume", "")):
                disc.append(("volume", u(e, "volume"), str(rec.get("volume", "(none)")), "volume"))
        elif artlike:
            disc.append(("volume", "(absent)", str(rec["volume"]), "missing"))
    num = u(e, "number")
    if num:
        num = num.replace("\u2013", "-")          # BibTeX range 2--3 == Crossref 2-3
    if num or rec.get("issue"):
        checked.append("issue")
        if num and num != str(rec.get("issue", "")):
            if num == str(rec.get("article-number", "")):
                info["number_is_article_number"] = num
            else:
                disc.append(("issue", num, str(rec.get("issue", "(none)")), "issue"))
        elif not num and artlike and rec.get("issue"):
            disc.append(("issue", "(absent)", str(rec["issue"]), "missing"))
    bp, cp = bib_pages(e), cr_pages(rec)
    art = str(rec.get("article-number", "") or "")
    if bp[0] or cp[0]:
        checked.append("pages")
        if bp[0] and cp[0]:
            same_first = bp[0] == cp[0] or (art and bp[0] == art)
            same_last = (not bp[1] or not cp[1]) or bp[1] == cp[1]
            if not (same_first and same_last):
                disc.append(("pages", u(e, "pages"), (rec.get("page") or art), "pages"))
            elif bp[1] == "" and cp[1] and artlike and cp[1] != cp[0]:
                disc.append(("pages", u(e, "pages"), rec.get("page"), "last-page-missing"))
        elif not bp[0] and cp[0] and (artlike or e.etype == "incollection"):
            if not (num and num == cp[0]):
                disc.append(("pages", "(absent)", rec.get("page") or art, "missing"))
    # ---- year
    yrs = cr_years(rec)
    info["dates"] = yrs
    if e.get("year"):
        checked.append("year")
        y = u(e, "year")
        which = [k for k, v in yrs.items() if v.split("-")[0] == y]
        info["year_matches"] = which
        if not which:
            disc.append(("year", y, "; ".join(f"{k} {v}" for k, v in yrs.items()), "year"))
    elif artlike or e.etype in ("book", "incollection"):
        disc.append(("year", "(absent)", "; ".join(f"{k} {v}" for k, v in yrs.items()), "missing"))
    # ---- publisher (books and chapters only; articles do not carry one)
    if e.get("publisher"):
        checked.append("publisher")
        bpub, cpub = u(e, "publisher"), html.unescape(rec.get("publisher", ""))
        fb, fc = set(bt.fold(bpub).split()), set(bt.fold(cpub).split())
        if not (fb & fc - {"press", "university", "the", "of"}):
            disc.append(("publisher", bpub, cpub, "publisher"))
        elif bt.fold(bpub) != bt.fold(cpub):
            info["publisher_form"] = f"bib '{bpub}' vs Crossref '{cpub}'"
    info["type"] = rec.get("type")
    return checked, disc, info


# ======================================================================= search evaluation
PARENT_ISBNS = {}   # fold(book title) -> ISBNs of that book's cached Crossref /works record


def build_parent_isbns(base):
    PARENT_ISBNS.clear()
    for k, e in base.items():
        if e.etype == "book" and e.get("doi"):
            rec = load_rec(k)
            if rec and rec.get("ISBN"):
                PARENT_ISBNS[bt.fold(u(e, "title"))] = {re.sub(r"[^0-9X]", "", x) for x in rec["ISBN"]}

def evaluate_candidate(key, e, c):
    """Five-field acceptance test (first author, title, container/publisher, year, volume)
    plus substitute identifiers (first page / article number, PII, ISBN)."""
    res = {}
    names, role = bib_names(e)
    real = [n for n in names if not n.get("others")]
    if e.etype == "incollection" and not e.get("author"):
        real = []                                  # bib gives only the book editors
    crn = names_of(c, "author") if role != "editor" else (names_of(c, "editor") or names_of(c, "author"))
    if real and crn:
        res["A"] = "match" if bt.fold(real[0]["family"]) == bt.fold(crn[0]["family"]) else "mismatch"
    else:
        res["A"] = "untestable"                    # absent in bib, or record carries no names
    # identifiers first (they relax nothing by themselves)
    piis = bib_piis(e)
    alt = {re.sub(r"[^0-9A-Z]", "", a.upper()) for a in (c.get("alternative-id") or [])}
    if piis:
        res["I"] = "match" if piis & alt else "mismatch"
    cisbn = {re.sub(r"[^0-9X]", "", x) for x in (c.get("ISBN") or [])}
    if e.get("isbn"):
        res["I"] = "match" if re.sub(r"[^0-9X]", "", e.get("isbn")) in cisbn else "mismatch"
    if e.etype == "incollection" and "I" not in res:
        parent = PARENT_ISBNS.get(bt.fold(u(e, "booktitle") or ""))
        if parent is not None:
            res["I"] = "match" if parent & cisbn else "mismatch"
    if key in PLACEHOLDER_TITLE:
        res["T"] = "untestable"
    else:
        t = u(e, "title")
        if key == "U01":
            t = t.split(" (title as displayed")[0]
        if key == "U05":
            t = t.split(" (proceedings")[0]
        ct = cr_title(c)
        r = difflib.SequenceMatcher(None, bt.fold(t), bt.fold(ct)).ratio()
        main = bt.fold(t.split(":")[0]) if ":" in t else None
        if r >= 0.90:
            res["T"] = "match"
        elif main and bt.fold(ct) == main:
            res["T"] = "match"
            res["T_note"] = "main title only (record has no subtitle)"
        elif res.get("I") == "match" and r >= 0.80:
            res["T"] = "match"
            res["T_note"] = "near match accepted because the bib-recorded PII/ISBN matches"
        else:
            res["T"] = "mismatch"
        res["T_ratio"] = round(r, 3)
    cont = u(e, "journal") or u(e, "booktitle")
    ccont = [bt.fold(html.unescape(x)) for x in (c.get("container-title") or [])]
    if cont:
        fb = bt.fold(cont)
        res["C"] = "match" if any(fb == x or x.startswith(fb) or fb.startswith(x) for x in ccont if x) else "mismatch"
    elif e.get("publisher"):
        fb = set(bt.fold(u(e, "publisher")).split()) - {"press", "university", "the", "of"}
        fc = set(bt.fold(c.get("publisher", "")).split())
        if fb & fc:
            res["C"] = "match"
        elif e.etype == "book" and res.get("I") == "match":
            res["C"] = "match"
            res["C_note"] = f"imprint '{u(e, 'publisher')}' vs registrant '{c.get('publisher')}'; ISBN matches"
        else:
            res["C"] = "mismatch"
    else:
        res["C"] = "untestable"
    if e.get("year"):
        yrs = {v.split("-")[0] for v in cr_years(c).values()}
        res["Y"] = "match" if u(e, "year") in yrs else "mismatch"
    else:
        res["Y"] = "untestable"
    if e.etype in ("book", "incollection", "proceedings") and not e.get("volume"):
        res["V"] = "n/a"
    elif e.get("volume"):
        res["V"] = "match" if u(e, "volume") == str(c.get("volume", "")) else "mismatch"
    else:
        res["V"] = "untestable"
    bp, cp = bib_pages(e), cr_pages(c)
    if bp[0]:
        res["P"] = "match" if cp[0] and bp[0] == cp[0] else "mismatch"
    core = [res[k] for k in "ATCYV"]
    mism = [k for k in res if res[k] == "mismatch"]
    if all(x in ("match", "n/a") for x in core):
        verdict = "ACCEPT-5FIELD"
    elif mism:
        verdict = "REJECT(" + ",".join(mism) + ")"
    else:
        untest = [k for k in "ATCYV" if res[k] == "untestable"]
        subs = [k for k in ("P", "I") if res.get(k) == "match"]
        title_ok = res["T"] == "match" or (res["T"] == "untestable" and res.get("P") == "match")
        if title_ok and (res.get("I") == "match" or len(untest) <= len(subs)):
            verdict = "ACCEPT-SUBSTITUTED(" + ",".join(untest) + "<-" + ",".join(subs) + ")"
        else:
            verdict = "NOT-ACCEPTED(untestable:" + ",".join(untest) + ")"
    res["verdict"] = verdict
    return res


# ======================================================================= fetch
def route_of(key, e):
    if key in ("PAT01", "U03"):
        return "patent"
    if key in SOFTWARE and not e.get("doi"):
        return "software"
    if e.get("doi"):
        return "doi"
    return "search"


def github_repo(e):
    blob = " ".join(f.value for f in e.fields)
    m = re.search(r"github\.com/([\w.-]+)/([\w.+-]+)", blob)
    return (m.group(1), m.group(2).rstrip(".")) if m else None


def patent_number(e):
    blob = e.get("howpublished") or ""
    m = re.search(r"US\s*([\d,]{9,10})", blob)
    return "US" + m.group(1).replace(",", "") if m else None


# Additional queries, logged like the others.  The ISBN 9780444820518 is copied from the
# Crossref chapter records returned by the U05 search (see U05.search.json), not typed.
EXTRA = {
    "U05": [("U05.isbn.json", CROSSREF + "?" + urllib.parse.urlencode({"filter": "isbn:9780444820518", "rows": 100}))],
    "U06": [("U06.isbn-osakabe.json", CROSSREF + "?" + urllib.parse.urlencode({"filter": "isbn:9780444820518", "query.author": "Osakabe", "rows": 20}))],
    # ISBNs below copied from the cached /works records B13.json and B14.json: chapter
    # records are the only Crossref source of the author list (B13) and subtitle (B14).
    "B13": [("B13.isbn.json", CROSSREF + "?" + urllib.parse.urlencode({"filter": "isbn:9780387400938", "rows": 40}))],
    "B14": [("B14.isbn.json", CROSSREF + "?" + urllib.parse.urlencode({"filter": "isbn:9780387765006", "rows": 60}))],
    # Zenodo DOI read verbatim in the prismatique README (quoted in the S01 note since B2).
    "S01": [("S01.datacite.json", "https://api.datacite.org/dois/10.5281/zenodo.18296081")],
    "U13": [("U13.search2.json", CROSSREF + "?" + urllib.parse.urlencode({"query.bibliographic": "Ishizuka multislice inclined illumination", "rows": 5}))],
    "U14": [("U14.search2.json", CROSSREF + "?" + urllib.parse.urlencode({"query.bibliographic": "multislice inclined illumination Philosophical Magazine Letters 71 1995", "rows": 5}))],
}
# Publisher pages (raw HTML kept in the scratch directory, not committed).
PAGES = {
    "B03": "https://shop.elsevier.com/books/principles-of-electron-optics-volume-3/hawkes/978-0-12-818979-5",
    "B04": "https://shop.elsevier.com/books/principles-of-electron-optics-volume-4/hawkes/978-0-323-91646-2",
    "B05": "https://link.springer.com/book/10.1007/978-3-642-32119-1",
    "B13": "https://link.springer.com/book/10.1007/978-0-387-40093-8",
    "B14": "https://link.springer.com/book/10.1007/978-0-387-76501-3",
    "B08": "https://academic.oup.com/book/54675",
    "S01": "https://mrfitzpa.github.io/prismatique/",
    "S02": "https://prism-em.github.io/about-cite/",
    "U12": "https://www.hremresearch.com/holodark/",
}


def cmd_fetch(args):
    CACHE.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    idx = load_index()
    base = entries_by_key(read_baseline())
    cur = entries_by_key(BIB.read_text())
    keys = args.keys or list(base)
    for key in keys:
        e = base.get(key) or cur[key]
        r = route_of(key, e)
        print(f"[{key}] route={r}", flush=True)
        if r == "doi":
            doi = e.get("doi")
            st, _ = cached_get(f"{key}.json", works_url(doi), idx, args.refresh)
            print(f"   crossref /works/{doi} -> {st}")
            if st != 200:
                st2, _ = cached_get(f"{key}.ra.json", "https://doi.org/ra/" + urllib.parse.quote(doi, safe="/()._;:-"), idx, args.refresh)
                print(f"   doi.org/ra -> {st2}")
                st3, _ = cached_get(f"{key}.datacite.json", "https://api.datacite.org/dois/" + urllib.parse.quote(doi, safe="/()._;:-"), idx, args.refresh)
                print(f"   datacite -> {st3}")
        elif r == "search":
            q = query_string(key, e)
            url = CROSSREF + "?" + urllib.parse.urlencode({"query.bibliographic": q, "rows": 5})
            st, body = cached_get(f"{key}.search.json", url, idx, args.refresh)
            print(f"   search -> {st}  q={q[:90]!r}")
            if e.get("isbn"):
                url = CROSSREF + "?" + urllib.parse.urlencode({"filter": "isbn:" + e.get("isbn"), "rows": 20})
                st, _ = cached_get(f"{key}.isbn.json", url, idx, args.refresh)
                print(f"   isbn filter -> {st}")
        for name, url in EXTRA.get(key, []):
            st, _ = cached_get(name, url, idx, args.refresh)
            print(f"   extra {name} -> {st}")
        if key in PAGES:
            st, _ = cached_get(f"{key}.publisher.html", PAGES[key], idx, args.refresh, accept="text/html", where=SCRATCH)
            print(f"   publisher page {PAGES[key]} -> {st}")
        if e.get("eprint"):
            url = "https://export.arxiv.org/api/query?id_list=" + e.get("eprint")
            st, _ = cached_get(f"{key}.arxiv.xml", url, idx, args.refresh, accept="*/*")
            print(f"   arXiv -> {st}")
        if r == "software":
            gh = github_repo(e)
            if gh:
                # github.com and api.github.com are blocked for this session (HTTP 403 from the
                # proxy); raw.githubusercontent.com is reachable, so the README is the record.
                for br in ("main", "master"):
                    st, _ = cached_get(f"{key}.readme.md", f"https://raw.githubusercontent.com/{gh[0]}/{gh[1]}/{br}/README.md",
                                       idx, args.refresh, accept="*/*", where=SCRATCH)
                    if st == 200:
                        break
                print(f"   raw README {gh} -> {st}")
            if e.get("url") and "github.com" not in e.get("url"):
                st, _ = cached_get(f"{key}.page.html", e.get("url"), idx, args.refresh, accept="text/html", where=SCRATCH)
                print(f"   page {e.get('url')} -> {st}")
            if key == "U18":
                q = "rheed++ RHEED intensity oscillations epitaxial growth SoftwareX"
                url = CROSSREF + "?" + urllib.parse.urlencode({"query.bibliographic": q, "rows": 5})
                st, _ = cached_get(f"{key}.search.json", url, idx, args.refresh)
                print(f"   search -> {st}")
        if r == "patent":
            pn = patent_number(e)
            if pn:
                st, _ = cached_get(f"{key}.patent.html", f"https://patents.google.com/patent/{pn}A/en", idx, args.refresh, accept="text/html", where=SCRATCH)
                if st != 200:
                    st, _ = cached_get(f"{key}.patent.html", f"https://patents.google.com/patent/{pn}B2/en", idx, args.refresh, accept="text/html", where=SCRATCH)
                print(f"   patent {pn} -> {st}")
    # evaluate search candidates and fetch accepted DOIs
    build_parent_isbns(base)
    for key in keys:
        e = base.get(key) or cur[key]
        p = CACHE / f"{key}.search.json"
        if e.get("doi") or not p.exists():
            continue
        items = json.loads(p.read_text())["message"]["items"]
        pi = CACHE / f"{key}.isbn.json"
        if pi.exists():
            items = items + json.loads(pi.read_text())["message"]["items"]
        best = None
        for c in items:
            ev = evaluate_candidate(key, e, c)
            if ev["verdict"].startswith("ACCEPT") and best is None:
                best = (c["DOI"], ev)
        if best:
            st, _ = cached_get(f"{key}.json", works_url(best[0]), idx, args.refresh)
            print(f"[{key}] accepted {best[0]} {best[1]['verdict']} -> /works {st}")
    return 0


# ======================================================================= apply corrections
def fmt_names(names):
    out = []
    for n in names:
        fam, _ = bt.unicode_to_latex(n["family"])
        giv, _ = bt.unicode_to_latex(n["given"])
        if " " in fam.strip() and not fam.startswith("{"):
            fam = "{" + fam + "}"
        out.append(f"{fam}, {giv}" if giv else fam)
    return " and ".join(out)


def value_from_record(field, rec, e):
    if field in ("author", "editor"):
        return fmt_names(names_of(rec, field))
    if field == "title":
        return bt.unicode_to_latex(cr_title(rec))[0]
    if field == "journal":
        return bt.unicode_to_latex(html.unescape((rec.get("container-title") or [""])[0]))[0]
    if field == "booktitle":
        return bt.unicode_to_latex(html.unescape((rec.get("container-title") or [""])[0]))[0]
    if field == "volume":
        return str(rec["volume"])
    if field == "number":
        return re.sub(r"^(\w+)-(\w+)$", r"\1--\2", str(rec.get("issue") or rec.get("article-number")))
    if field == "pages":
        a, b = cr_pages(rec)
        return f"{a}--{b}" if b else a
    if field == "year:print":
        return cr_years(rec)["published-print"].split("-")[0]
    if field == "year:online":
        return cr_years(rec)["published-online"].split("-")[0]
    if field == "year:issued":
        return cr_years(rec)["issued"].split("-")[0]
    if field == "doi":
        return rec["DOI"]
    if field == "publisher":
        return bt.unicode_to_latex(rec["publisher"])[0]
    raise KeyError(field)


ORDER = ["author", "editor", "title", "journal", "booktitle", "publisher", "volume", "number", "pages",
         "year", "edition", "version", "isbn", "doi", "url", "eprint", "archiveprefix", "howpublished", "note"]


def render_entry(text, e):
    """Re-render a touched entry with fields in a canonical order, keeping each raw value
    and the entry's own label width."""
    fs = e.fields
    width = max(len(f.raw_name) for f in fs)
    rank = {n: i for i, n in enumerate(ORDER)}
    fs = sorted(fs, key=lambda f: (rank.get(f.name, len(ORDER) - 1.5), fs.index(f)))
    lines = [f"@{e.etype}{{{e.key},"]
    for f in fs:
        lines.append(f"  {f.raw_name.ljust(width)} = {{{f.value}}},")
    lines[-1] = lines[-1].rstrip(",")
    return "\n".join(lines) + "\n}"


def cmd_apply(args):
    import yaml
    spec = yaml.safe_load(CORR.read_text()) or {}
    # Always rebuild from the baseline commit, so that `apply` is idempotent and the
    # current file is exactly baseline + b3_corrections.yaml.
    text = read_baseline()
    for old, rep in spec.get("header_replace") or []:
        if old not in text:
            raise SystemExit(f"header_replace text not found: {old[:60]!r}")
        text = text.replace(old, rep)
    touched = []
    for key, ops in (spec.get("entries") or {}).items():
        touched.append(key)
        ents = entries_by_key(text)
        e = ents[key]
        rec = None
        rp = CACHE / f"{key}.json"
        if rp.exists():
            rec = json.loads(rp.read_text())["message"]
        new = {}
        for fld in ops.get("from_crossref", []) or []:
            if rec is None:
                raise SystemExit(f"{key}: from_crossref requested but no /works record cached")
            name = fld.split(":")[0]
            new[name] = value_from_record(fld, rec, e)
        for name, val in (ops.get("set") or {}).items():
            new[name] = str(val).strip()
        for pair in ops.get("note_replace", []) or []:
            old, rep = pair
            note = new.get("note", e.get("note"))
            if old not in note:
                raise SystemExit(f"{key}: note_replace text not found: {old[:60]!r}")
            new["note"] = note.replace(old, rep.strip())
        if "relabel" in ops:
            note = new.get("note", e.get("note"))
            m = re.match(r"evidence:\s*(.*?);\s*provenance:", note, re.S)
            if not m:
                raise SystemExit(f"{key}: note has no 'evidence: ...; provenance:' head")
            lab = ops["relabel"].strip()
            if lab == "crossref":
                lab = ("METADATA\\_VERIFIED (route: Crossref API /works record of the doi field, cached as "
                       f"docs/agent\\_reports/crossref\\_cache/{key}.json; B3, 2026-09-22)")
            new["note"] = f"evidence: {lab}; label before B3: {m.group(1).strip()}; provenance:" + note[m.end():]
        if "note_prefix" in ops:
            note = new.get("note", e.get("note"))
            m = re.match(r"evidence:.*?; provenance:", note, re.S)
            if not m:
                raise SystemExit(f"{key}: note has no 'evidence: ...; provenance:' head")
            new["note"] = ops["note_prefix"].strip() + note[m.end():]
        # write fields: replace in place (from last offset to first), or insert before note
        edits = []
        for name, val in new.items():
            f = e.fieldobj(name)
            if f is not None:
                edits.append((f.vstart, f.vend, val))
            else:
                nf = e.fieldobj("note") or e.fields[-1]
                pad = text[nf.fstart:nf.vstart]
                indent = pad[:len(pad) - len(pad.lstrip())]
                eq = pad.index("=")
                label_w = eq - len(indent)
                line = f"{indent}{name.ljust(label_w)}= {{{val}}},\n"
                edits.append((nf.fstart, nf.fstart, line))
        for name in ops.get("remove", []) or []:
            f = e.fieldobj(name)
            if f is not None:
                end = text.index("\n", f.vend) + 1
                edits.append((f.fstart, end, ""))
        for s, t_, val in sorted(edits, key=lambda x: -x[0]):
            text = text[:s] + val + text[t_:]
        if ops.get("move_to_verified"):
            ents = entries_by_key(text)
            e = ents[key]
            block = text[e.start:e.end]
            s = e.start
            t_ = e.end
            while t_ < len(text) and text[t_] == "\n":
                t_ += 1
            text = text[:s] + text[t_:]
            anchor = "%% --- 4j. Records moved from the UNVERIFIED section by the B3 Crossref pass"
            if anchor not in text:
                m = re.search(r"\n\n%% =+\n%% PART 5\n", text)
                text = text[:m.start()] + "\n\n" + anchor + " ---\n" + text[m.start():]
            m = re.search(r"\n\n%% =+\n%% PART 5\n", text)
            text = text[:m.start()] + "\n\n" + block + text[m.start():]
            if e.etype != ops.get("type", e.etype):
                pass
        if ops.get("type"):
            ents = entries_by_key(text)
            e = ents[key]
            text = text[:e.start] + "@" + ops["type"] + text[e.start + 1 + len(e.etype):]
    for key in touched:
        e = entries_by_key(text)[key]
        text = text[:e.start] + render_entry(text, e) + text[e.end:]
    BIB.write_text(text)
    errs, warns, stats = bt.validate(text)
    print("validate:", stats, "errors:", errs)
    return 1 if errs else 0


# ======================================================================= report
def label_of(e):
    note = e.get("note") or ""
    m = re.match(r"evidence:\s*(.*?);\s*provenance:", note, re.S)
    lab = m.group(1) if m else "?"
    lab = lab.split("; label before B3")[0]
    return re.sub(r"\s+", " ", lab.replace("\\_", "_"))


def load_rec(key):
    p = CACHE / f"{key}.json"
    return json.loads(p.read_text())["message"] if p.exists() else None


def load_accept(spec):
    return (spec or {}).get("accepted_residual") or {}


def cmd_report(args):
    import yaml
    spec = yaml.safe_load(CORR.read_text()) if CORR.exists() else {}
    manual = (spec or {}).get("manual_routes") or {}
    partial = (spec or {}).get("partial") or {}
    accepted_res = load_accept(spec)
    idx = load_index()
    base_t, cur_t = read_baseline(), BIB.read_text()
    base, cur = entries_by_key(base_t), entries_by_key(cur_t)
    build_parent_isbns(base)
    rows, blocks, corrections = [], [], []
    counts = dict(checked=0, verified_unchanged=0, verified_corrected=0, new_doi=0,
                  still_unverified=0, http_failures=0, moved_to_verified=0,
                  doi_resolved=0, doi_total=0, search_run=0, search_accept_strict=0,
                  search_accept_subst=0, verified_partial=0)
    for name, rec in idx.items():
        if rec["status"] != 200 and not name.endswith((".ra.json", ".datacite.json")):
            if rec["status"] is None or rec["status"] >= 500 or rec["status"] == 429:
                counts["http_failures"] += 1
    for key, e0 in base.items():
        e1 = cur.get(key)
        counts["checked"] += 1
        r = route_of(key, e0)
        recs = load_rec(key)
        base_doi, cur_doi = e0.get("doi"), (e1.get("doi") if e1 else None)
        http_status = ""
        qurl = ""
        search_note = ""
        if base_doi:
            counts["doi_total"] += 1
            st = idx.get(f"{key}.json", {}).get("status")
            http_status = str(st)
            qurl = works_url(base_doi)
            if st == 200:
                counts["doi_resolved"] += 1
        sp = CACHE / f"{key}.search.json"
        if not base_doi and sp.exists():
            counts["search_run"] += 1
            sidx = idx.get(f"{key}.search.json", {})
            qurl = sidx.get("url", "")
            http_status = f"search {sidx.get('status')}"
            items = json.loads(sp.read_text())["message"]["items"]
            ip = CACHE / f"{key}.isbn.json"
            if ip.exists():
                items += json.loads(ip.read_text())["message"]["items"]
            cand = []
            for c in items:
                ev = evaluate_candidate(key, e0, c)
                cand.append((c.get("DOI"), c.get("score"), ev, cr_title(c)[:80],
                             (names_of(c, "author") or names_of(c, "editor") or [{"family": "-"}])[0]["family"],
                             "/".join(sorted({v.split('-')[0] for v in cr_years(c).values()})),
                             (c.get("container-title") or [c.get("publisher", "")])[0], c.get("volume", "")))
            acc = next((c for c in cand if c[2]["verdict"].startswith("ACCEPT")), None)
            if acc:
                if acc[2]["verdict"].startswith("ACCEPT-5"):
                    counts["search_accept_strict"] += 1
                else:
                    counts["search_accept_subst"] += 1
                if recs is not None:
                    http_status += f"; works {idx.get(f'{key}.json', {}).get('status')}"
            search_note = cand
        # --- which record verifies this entry?
        route_ok, route_desc = False, ""
        if recs is not None and (base_doi or (search_note and any(c[2]["verdict"].startswith("ACCEPT") and c[0] == recs["DOI"] for c in search_note))):
            route_ok, route_desc = True, f"Crossref API /works/{recs['DOI']}"
        elif key in manual:
            route_ok, route_desc = bool(manual[key].get("verified")), manual[key].get("route", "")
            http_status = http_status or manual[key].get("http", "")
            qurl = qurl or manual[key].get("url", "")
        # --- compare
        b_chk, b_disc, b_info = compare(key, e0, recs) if recs is not None else ([], [], {})
        ph1 = key in PLACEHOLDER_TITLE and e1 is not None and e1.get("title") == e0.get("title")
        c_chk, c_disc, c_info = compare(key, e1, recs, placeholder=ph1) if (recs is not None and e1) else ([], [], {})
        acc_keys = accepted_res.get(key, {}) or {}
        c_disc_resid = [d for d in c_disc if d[0] not in acc_keys and d[3] not in ("placeholder",)]
        b_disc_mat = [d for d in b_disc if d[3] not in ("placeholder",)]
        # field diffs baseline -> current
        fdiff = []
        if e1:
            names = [f.name for f in e0.fields] + [f.name for f in e1.fields if f.name not in [g.name for g in e0.fields]]
            for n in names:
                a, b = e0.get(n), e1.get(n)
                if a != b and n != "note":
                    fdiff.append((n, a, b))
                    corrections.append((key, n, a, b))
        actions = []
        if fdiff:
            actions.append("corrected: " + ",".join(n for n, _, _ in fdiff))
        if not base_doi and cur_doi:
            actions.append("doi added from Crossref record")
            counts["new_doi"] += 1
        if e1 and e0.section != e1.section:
            actions.append(f"moved {e0.section}->{e1.section}")
            if e1.section == "verified":
                counts["moved_to_verified"] += 1
        if e1 and e0.etype != e1.etype:
            actions.append(f"type @{e0.etype}->@{e1.etype}")
        if e1 and (e0.get("note") != e1.get("note")):
            actions.append("note updated")
        if route_ok and not c_disc_resid and key in partial:
            counts["verified_partial"] += 1
            status = "VERIFIED-PARTIAL" + ("-CORRECTED" if fdiff else "")
        elif route_ok and not c_disc_resid:
            if not fdiff and not (not base_doi and cur_doi):
                counts["verified_unchanged"] += 1
                status = "VERIFIED-UNCHANGED"
            else:
                counts["verified_corrected"] += 1
                status = "VERIFIED-CORRECTED"
        elif route_ok:
            counts["still_unverified"] += 1
            status = "RESIDUAL-DISCREPANCY"
        else:
            counts["still_unverified"] += 1
            status = "UNVERIFIED"
        actions.insert(0, status)
        rows.append([key, cur_doi or base_doi or "", http_status, ",".join(b_chk or c_chk),
                     " | ".join(f"{d[0]}: '{d[1]}' vs '{d[2]}' ({d[3]})" for d in b_disc_mat) or ("none" if recs is not None else "n/a (no record)"),
                     "; ".join(actions), label_of(e0), label_of(e1) if e1 else ""])
        blocks.append(dict(key=key, route=route_desc or r, url=qurl, http=http_status, status=status,
                           b_disc=b_disc_mat, c_disc=c_disc, acc=acc_keys, info=c_info or b_info,
                           cand=search_note, fdiff=fdiff, lab0=label_of(e0), lab1=label_of(e1) if e1 else "",
                           manual=manual.get(key), partial=partial.get(key)))
    # ---- TSV
    with TSV.open("w") as fh:
        fh.write("\t".join(["key", "doi", "http_status", "fields_checked", "discrepancies", "action", "label_before", "label_after"]) + "\n")
        for r in rows:
            fh.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")
    errs, warns, stats = bt.validate(cur_t)
    doi_ok = check_dois_backed(cur)
    write_log(counts, blocks, corrections, stats, errs, doi_ok, spec)
    print(json.dumps(counts, indent=1))
    print("validate:", stats, "errors:", errs, "doi-backing:", doi_ok)
    return 0


def check_dois_backed(cur):
    bad = []
    for key, e in cur.items():
        d = e.get("doi")
        if not d:
            continue
        rec = load_rec(key)
        if rec is not None and rec.get("DOI", "").lower() == d.lower():
            continue
        dp = CACHE / f"{key}.datacite.json"
        if dp.exists():
            dd = json.loads(dp.read_text())["data"]["attributes"]["doi"]
            if dd.lower() == d.lower():
                continue
        bad.append(key)
    return bad


def md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def write_log(counts, blocks, corrections, stats, errs, doi_bad, spec):
    L = []
    L.append("## Counts (produced by `tools/bib/crossref_check.py report`)\n")
    L.append("| Quantity | Count |\n|---|---|")
    for k, lab in [("checked", "entries checked (baseline file)"),
                   ("doi_total", "baseline entries with a doi field"),
                   ("doi_resolved", "... of which Crossref /works returned HTTP 200"),
                   ("search_run", "Crossref bibliographic searches run (entries without doi)"),
                   ("search_accept_strict", "... candidate accepted on the five-field rule"),
                   ("search_accept_subst", "... candidate accepted with identifier substitution"),
                   ("verified_unchanged", "VERIFIED, record unchanged"),
                   ("verified_corrected", "VERIFIED, record corrected (fields and/or doi added)"),
                   ("verified_partial", "VERIFIED except for a field no reachable record carries (listed per entry)"),
                   ("new_doi", "newly found DOIs (copied from Crossref, never constructed)"),
                   ("moved_to_verified", "entries moved out of the UNVERIFIED section"),
                   ("still_unverified", "still unverified (no accepted record, or residual discrepancy)"),
                   ("http_failures", "HTTP failures (network error, 429 or 5xx after retries)")]:
        L.append(f"| {lab} | {counts[k]} |")
    L.append("")
    L.append("Syntax validation of the current `references.bib`: " + json.dumps(stats) +
             f"; errors: {errs or 'none'}; entries whose doi is not backed by a cached registry record: {doi_bad or 'none'}.\n")
    byfield = {}
    for key, n, a, b in corrections:
        byfield.setdefault(n if a is not None else n + " (added)", set()).add(key)
    L.append("Entries changed, by field (baseline -> current; `note` excluded): " + "; ".join(
        f"{n}: {len(ks)}" for n, ks in sorted(byfield.items())) + ".\n")
    L.append("## Corrections (baseline -> current, every changed field except `note`)\n")
    L.append("| key | field | before | after |\n|---|---|---|---|")
    for key, n, a, b in corrections:
        L.append(f"| {key} | {n} | {md(a) if a is not None else '(absent)'} | {md(b) if b is not None else '(removed)'} |")
    L.append("")
    L.append("## Per-entry record\n")
    L.append("Discrepancy kinds: `family`/`diacritics`/`given`/`count`/`incomplete` (names), `ratio=` (title "
             "similarity after case/punctuation folding), `container`, `volume`, `issue`, `pages`, `year`, "
             "`publisher`, `missing` (field absent in bib but present in record). Search verdicts: A first "
             "author, T title, C container or publisher, Y year, V volume, P first page, I PII/ISBN.\n")
    for b in blocks:
        L.append(f"### {b['key']} -- {b['status']}\n")
        L.append(f"- Route: {md(b['route'])}")
        if b["url"]:
            L.append(f"- Query URL: <{b['url']}>  (HTTP: {b['http']})")
        if b["info"].get("dates"):
            ym = b["info"].get("year_matches")
            L.append(f"- Crossref dates: {b['info']['dates']}; bib year matches: {ym if ym is not None else 'n/a'}")
        for k in ("container_form", "publisher_form", "number_is_article_number", "type"):
            if b["info"].get(k):
                L.append(f"- {k}: {md(b['info'][k])}")
        if b["cand"]:
            L.append("- Candidates (DOI, score, verdict, first author, years, container, volume, title):")
            for c in b["cand"]:
                ev = {k: v for k, v in c[2].items() if k != "verdict"}
                L.append(f"  - `{c[0]}` score {c[1]:.1f} **{c[2]['verdict']}** {ev} -- {md(c[4])}; {c[5]}; {md(c[6])}; vol {c[7]}; \"{md(c[3])}\"")
        if b["b_disc"]:
            L.append("- Discrepancies (baseline vs record): " + "; ".join(f"`{d[0]}` '{md(d[1])}' vs '{md(d[2])}' ({d[3]})" for d in b["b_disc"]))
        elif b["route"].startswith("Crossref"):
            L.append("- Discrepancies (baseline vs record): none")
        if b["c_disc"]:
            L.append("- Remaining differences (current vs record): " + "; ".join(
                f"`{d[0]}` '{md(d[1])}' vs '{md(d[2])}'" + (f" -- kept: {md(b['acc'][d[0]])}" if d[0] in b["acc"] else "") for d in b["c_disc"]))
        if b["manual"]:
            L.append(f"- Publisher-page / registry result: {md(b['manual'].get('result', ''))}")
        if b.get("partial"):
            L.append(f"- NOT verifiable in this pass: {md(b['partial'])}")
        L.append(f"- Label: `{md(b['lab0'])}` -> `{md(b['lab1'])}`\n")
    gen = "\n".join(L)
    text = LOG.read_text()
    a, z = "<!-- BEGIN GENERATED -->", "<!-- END GENERATED -->"
    text = text[:text.index(a) + len(a)] + "\n" + gen + "\n" + text[text.index(z):]
    LOG.write_text(text)


def cmd_validate(args):
    text = BIB.read_text()
    errs, warns, stats = bt.validate(text)
    bad = check_dois_backed(entries_by_key(text))
    print(json.dumps(stats))
    print("errors:", errs or "none")
    print("doi fields without a cached registry record carrying the same DOI:", bad or "none")
    return 1 if (errs or bad) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    f = sp.add_parser("fetch")
    f.add_argument("keys", nargs="*")
    f.add_argument("--refresh", action="store_true")
    sp.add_parser("apply")
    sp.add_parser("report")
    sp.add_parser("validate")
    a = ap.parse_args()
    return {"fetch": cmd_fetch, "apply": cmd_apply, "report": cmd_report, "validate": cmd_validate}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
