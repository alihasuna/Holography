#!/usr/bin/env python3
"""Citation-graph search for the reflection electron holography seed papers.

For the seed papers P01, P02, P02E, P03 (primary) and P08, P09 (supplement), whose DOIs are read
from docs/references.bib, this script

  fetch      retrieves the citing works from OpenAlex (filter=cites:<openalex id>), Semantic
             Scholar (/graph/v1/paper/DOI:<doi>/citations) and OpenCitations COCI
             (https://opencitations.net/index/coci/api/v1/citations/<doi>), and caches the raw
             JSON responses under docs/agent_reports/citation_cache/. Only bibliographic metadata
             is requested and cached (no abstracts and no full text; OpenAlex `referenced_works`
             identifier lists are cached for the reverse check described below).
             OpenAlex charges list queries (filter=..., search=...) against a daily budget. When
             that budget is exhausted (HTTP 429) the list is recorded as NOT RETRIEVED in
             citation_cache/openalex/<seed>_cites_STATUS.json, and a reverse check is made
             instead: every citing work returned by Semantic Scholar or COCI that has a DOI is
             looked up as a single OpenAlex record (free of charge), and the OpenAlex citation
             link is counted when the seed's OpenAlex id is in that record's `referenced_works`
             (code "OAref"). Works that only OpenAlex knows are then missing; `build` prints how
             many (OpenAlex cited_by_count minus the confirmed links). Set OPENALEX_API_KEY (a free
             personal key) or re-run after the budget resets at 00:00 UTC to complete the lists.
  build      merges and de-duplicates the cached lists (by DOI, else by normalised title + year),
             attaches the manual classification recorded in CLASSIFICATION below, writes
             docs/agent_reports/L4_citing_works.tsv and prints every count used in the report.
  abstracts  writes the abstracts available in the OpenAlex, Semantic Scholar and Crossref API
             records of the merged citing works to a directory OUTSIDE the repository (--out),
             for manual reading. Abstracts are not cached in the repository.
  search     runs the topic searches of task 3 (OpenAlex, Semantic Scholar, arXiv, Europe PMC,
             Crossref), caches the bibliographic results under citation_cache/search/ and prints
             the queries and hit counts.
  oa         prints the OpenAlex open-access status of the seed papers and of DOIs given on the
             command line, and the Crossref metadata of those DOIs (cached).

Standard library only. Network access goes through the environment's HTTPS proxy settings.
No e-mail address or other personal identifier is sent to any API.

Usage (from the repository root):
  python3 tools/lit/citation_lists.py fetch [--refresh]
  python3 tools/lit/citation_lists.py build [--list]
  python3 tools/lit/citation_lists.py abstracts --out /some/scratch/dir
  python3 tools/lit/citation_lists.py search [--refresh] [--list]
  python3 tools/lit/citation_lists.py oa [DOI ...]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BIB = REPO / "docs" / "references.bib"
CACHE = REPO / "docs" / "agent_reports" / "citation_cache"
TSV = REPO / "docs" / "agent_reports" / "L4_citing_works.tsv"

SEEDS_PRIMARY = ["P01", "P02", "P02E", "P03"]
SEEDS_SUPPLEMENT = ["P08", "P09"]
SEEDS = SEEDS_PRIMARY + SEEDS_SUPPLEMENT
# citation-link sources: OpenAlex cites: list, OpenAlex reverse check, Semantic Scholar, COCI
LINK_DBS = ["openalex", "openalex_ref", "s2", "coci"]
DB_CODE = {"openalex": "OA", "openalex_ref": "OAref", "s2": "S2", "coci": "COCI"}

USER_AGENT = "Holography-literature-script/1.0 (citation-graph search; python-urllib)"
OPENALEX_KEY = os.environ.get("OPENALEX_API_KEY")

OPENALEX_SELECT = ("id,doi,title,display_name,publication_year,publication_date,type,"
                   "authorships,primary_location,cited_by_count,open_access,best_oa_location")
S2_CITATION_FIELDS = "title,year,venue,externalIds,authors,publicationTypes,journal"

CLASSES = [
    "REH-experiment",
    "REH-method/theory",
    "REM/RHEED imaging",
    "transmission holography",
    "review/history",
    "reflection ptychography",
    "other",
]

# ---------------------------------------------------------------------------------------------
# Manual classification (task 2). Key: merge key printed by `build --list` ("doi:<lower-case
# doi>" or "ty:<normalised title>|<year>"). Value: (class, evidence). Evidence is either
#   "SECTION_READ (abstract only) <URL of the record in which the abstract was read>" or
#   "UNVERIFIED classification (title only)" (+ optional note).
# Entries are added only after reading the abstract (or, failing that, the title). Records
# missing from this table are written as class "UNCLASSIFIED".
# ---------------------------------------------------------------------------------------------
CLASSIFICATION: dict[str, tuple[str, str]] = {
}


# ----------------------------------------------------------------------------- HTTP helpers --

class RateLimited(RuntimeError):
    def __init__(self, url, retry_after, message):
        super().__init__(f"rate limited ({retry_after} s): {url}")
        self.url, self.retry_after, self.message = url, retry_after, message


def with_key(url: str) -> str:
    if OPENALEX_KEY and "api.openalex.org" in url:
        return url + ("&" if "?" in url else "?") + "api_key=" + urllib.parse.quote(OPENALEX_KEY)
    return url


def http_get(url: str, *, accept: str = "application/json", tries: int = 8,
             allow_404: bool = True) -> tuple[int, bytes]:
    """GET with retries on short 429s and 5xx. A 429 whose Retry-After exceeds 120 s raises
    RateLimited at once. Returns (status, body). Redirects are followed."""
    delay = 3.0
    last_err = None
    for attempt in range(tries):
        req = urllib.request.Request(with_key(url), headers={"User-Agent": USER_AGENT,
                                                             "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            body = e.read() or b""
            if e.code == 404 and allow_404:
                return 404, body
            if e.code == 429:
                ra = e.headers.get("Retry-After")
                ra = int(ra) if ra and ra.isdigit() else None
                if ra is not None and ra > 120:
                    raise RateLimited(url, ra, body.decode("utf-8", "replace")[:600])
                last_err = e
                time.sleep(ra if ra else delay)
                delay = min(delay * 2, 60)
                continue
            if e.code in (500, 502, 503, 504):
                last_err = e
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_err = e
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise RuntimeError(f"GET failed after {tries} tries: {url}: {last_err}")


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)


def cached_json(path: Path, url: str, refresh: bool, *, allow_404: bool = True,
                drop: tuple[str, ...] = ()):
    """Return parsed JSON for url, reading/writing the cache file `path`.
    404 responses are cached as {"_http_status": 404, "_url": url}. Keys in `drop` are removed
    from a top-level dict (or from its "message") before caching."""
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    status, body = http_get(url, allow_404=allow_404)
    if status == 404:
        data = {"_http_status": 404, "_url": url}
    else:
        data = json.loads(body.decode("utf-8"))
        if isinstance(data, dict):
            for k in drop:
                data.pop(k, None)
                if isinstance(data.get("message"), dict):
                    data["message"].pop(k, None)
            data = {"_url": url, "_retrieved": dt.date.today().isoformat(), **data}
        else:
            data = {"_url": url, "_retrieved": dt.date.today().isoformat(), "_list": data}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return data


# ---------------------------------------------------------------------------- seed parsing --

def read_seed_dois() -> dict[str, str]:
    text = BIB.read_text(encoding="utf-8")
    out = {}
    for key in SEEDS:
        m = re.search(r"@\w+\{" + re.escape(key) + r",(.*?)\n\}", text, re.S)
        if not m:
            raise SystemExit(f"{key} not found in {BIB}")
        d = re.search(r"\n\s*doi\s*=\s*\{([^}]*)\}", m.group(1))
        if not d:
            raise SystemExit(f"{key} has no doi field in {BIB}")
        out[key] = d.group(1).strip()
    return out


def doi_path(doi: str) -> str:
    """DOI for use in a URL path."""
    return urllib.parse.quote(doi, safe="/:.;-_")


# --------------------------------------------------------------------------------- fetching --

def fetch_crossref_seed(seed: str, doi: str, refresh: bool) -> dict:
    return cached_json(CACHE / "crossref" / f"{seed}_seed.json",
                       f"https://api.crossref.org/works/{doi_path(doi)}", refresh,
                       drop=("abstract", "reference"))


def fetch_openalex(seed: str, doi: str, refresh: bool) -> dict:
    sdir = CACHE / "openalex"
    rec = cached_json(sdir / f"{seed}_seed.json",
                      f"https://api.openalex.org/works/doi:{doi_path(doi)}?select={OPENALEX_SELECT},ids",
                      refresh)
    status_file = sdir / f"{seed}_cites_STATUS.json"
    if rec.get("_http_status") == 404:
        return {"seed_record": rec, "citing": [], "pages": 0, "status": "seed not in OpenAlex"}
    wid = rec["id"].rsplit("/", 1)[-1]
    citing, cursor, page = [], "*", 0
    try:
        while cursor:
            page += 1
            url = ("https://api.openalex.org/works?" + urllib.parse.urlencode({
                "filter": f"cites:{wid}", "per-page": "200", "cursor": cursor,
                "select": OPENALEX_SELECT}))
            data = cached_json(sdir / f"{seed}_cites_{wid}_p{page}.json", url, refresh)
            citing.extend(data.get("results", []))
            cursor = data.get("meta", {}).get("next_cursor")
            if not data.get("results"):
                break
    except RateLimited as e:
        status_file.write_text(json.dumps({
            "status": "NOT RETRIEVED: HTTP 429 (OpenAlex daily budget for unauthenticated list "
                      "queries exhausted)",
            "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "url": e.url, "retry_after_s": e.retry_after, "server_message": e.message}, indent=1))
        for f in sdir.glob(f"{seed}_cites_{wid}_p*.json"):
            f.unlink()              # never keep a partial list
        return {"seed_record": rec, "citing": None, "pages": 0, "status": "rate-limited"}
    if status_file.exists():
        status_file.unlink()
    return {"seed_record": rec, "citing": citing, "pages": page, "status": "ok"}


def fetch_s2(seed: str, doi: str, refresh: bool) -> dict:
    sdir = CACHE / "s2"
    rec = cached_json(sdir / f"{seed}_seed.json",
                      f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi_path(doi)}"
                      "?fields=title,year,externalIds,citationCount,venue", refresh)
    if rec.get("_http_status") == 404:
        return {"seed_record": rec, "citing": [], "pages": 0}
    citing, offset, page = [], 0, 0
    while offset is not None:
        page += 1
        url = (f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi_path(doi)}/citations?"
               + urllib.parse.urlencode({"fields": S2_CITATION_FIELDS, "limit": "1000",
                                         "offset": str(offset)}))
        data = cached_json(sdir / f"{seed}_citations_p{page}.json", url, refresh)
        for item in data.get("data", []):
            if item.get("citingPaper"):
                citing.append(item["citingPaper"])
        offset = data.get("next")
        time.sleep(1.1)
    return {"seed_record": rec, "citing": citing, "pages": page}


def fetch_coci(seed: str, doi: str, refresh: bool) -> dict:
    url = f"https://opencitations.net/index/coci/api/v1/citations/{doi_path(doi)}"
    data = cached_json(CACHE / "coci" / f"{seed}_citations.json", url, refresh)
    lst = data.get("_list", []) if isinstance(data, dict) else []
    return {"citing": [{"doi": r["citing"].lower(), "creation": r.get("creation")} for r in lst]}


def openalex_single(doi: str, refresh: bool = False) -> dict:
    """Single OpenAlex record for a DOI (free of charge), with referenced_works."""
    return cached_json(CACHE / "lookup" / f"openalex_{safe_name(doi)}.json",
                       f"https://api.openalex.org/works/doi:{doi_path(doi)}"
                       f"?select={OPENALEX_SELECT},referenced_works", refresh)


def crossref_single(doi: str, refresh: bool = False) -> dict:
    return cached_json(CACHE / "lookup" / f"crossref_{safe_name(doi)}.json",
                       f"https://api.crossref.org/works/{doi_path(doi)}", refresh,
                       drop=("abstract", "reference"))


def cmd_fetch(args) -> None:
    seeds = read_seed_dois()
    cand_dois = set()
    for seed, doi in seeds.items():
        fetch_crossref_seed(seed, doi, args.refresh)
        oa = fetch_openalex(seed, doi, args.refresh)
        s2 = fetch_s2(seed, doi, args.refresh)
        co = fetch_coci(seed, doi, args.refresh)
        for p in s2["citing"]:
            d = clean_doi((p.get("externalIds") or {}).get("DOI"))
            if d:
                cand_dois.add(d)
        cand_dois.update(clean_doi(x["doi"]) for x in co["citing"])
        n_oa = "NOT RETRIEVED (429)" if oa["citing"] is None else f"{len(oa['citing']):4d}"
        print(f"{seed:5s} {doi:32s} OpenAlex list={n_oa}  S2={len(s2['citing']):4d}  "
              f"COCI={len(co['citing']):4d}", flush=True)
    # single-record lookups (free): reverse check of OpenAlex links + metadata for COCI-only DOIs
    print(f"OpenAlex single-record lookups for {len(cand_dois)} candidate DOIs ...", flush=True)
    for d in sorted(cand_dois):
        openalex_single(d, args.refresh)
    print("done; run `build` to merge.")


# ---------------------------------------------------------------------------------- merging --

def norm_title(t: str | None) -> str:
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"<[^>]+>", " ", t)          # strip markup such as <i>
    t = re.sub(r"[^a-z0-9]+", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def clean_doi(d: str | None) -> str | None:
    if not d:
        return None
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d or None


def oa_to_meta(w: dict) -> dict:
    auths = w.get("authorships") or []
    first = None
    for a in auths:
        if a.get("author_position") == "first":
            first = (a.get("author") or {}).get("display_name")
            break
    if first is None and auths:
        first = (auths[0].get("author") or {}).get("display_name")
    src = ((w.get("primary_location") or {}).get("source") or {})
    return {"doi": clean_doi(w.get("doi")), "title": w.get("title") or w.get("display_name"),
            "first_author": first, "year": w.get("publication_year"),
            "venue": src.get("display_name"), "openalex_id": (w.get("id") or "").rsplit("/", 1)[-1]}


def s2_to_meta(p: dict) -> dict:
    ext = p.get("externalIds") or {}
    auths = p.get("authors") or []
    venue = p.get("venue") or ((p.get("journal") or {}).get("name"))
    return {"doi": clean_doi(ext.get("DOI")), "title": p.get("title"),
            "first_author": auths[0].get("name") if auths else None, "year": p.get("year"),
            "venue": venue or None, "s2_id": p.get("paperId"), "arxiv": ext.get("ArXiv")}


def crossref_to_meta(m: dict) -> dict:
    au = m.get("author") or []
    first = None
    if au:
        first = " ".join(x for x in [au[0].get("given"), au[0].get("family")] if x) or au[0].get("name")
    year = None
    for k in ("issued", "published-print", "published-online", "created"):
        dp = (m.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            year = dp[0][0]
            break
    return {"doi": clean_doi(m.get("DOI")), "title": (m.get("title") or [None])[0],
            "first_author": first, "year": year,
            "venue": (m.get("container-title") or [None])[0]}


def load_cached_lists() -> dict:
    """Read cached citing lists (no network)."""
    seeds = read_seed_dois()
    out = {}
    for seed in seeds:
        d = {}
        seedrec = json.loads((CACHE / "openalex" / f"{seed}_seed.json").read_text())
        items, status = [], "seed not in OpenAlex"
        if seedrec.get("_http_status") != 404:
            wid = seedrec["id"].rsplit("/", 1)[-1]
            sf = CACHE / "openalex" / f"{seed}_cites_STATUS.json"
            if sf.exists():
                items, status = None, "NOT RETRIEVED (HTTP 429)"
            else:
                for f in sorted((CACHE / "openalex").glob(f"{seed}_cites_{wid}_p*.json")):
                    items.extend(json.loads(f.read_text()).get("results", []))
                status = "ok"
        d["openalex"] = {"seed": seedrec, "items": items, "status": status}
        seedrec = json.loads((CACHE / "s2" / f"{seed}_seed.json").read_text())
        items = []
        for f in sorted((CACHE / "s2").glob(f"{seed}_citations_p*.json")):
            items.extend(x["citingPaper"] for x in json.loads(f.read_text()).get("data", [])
                         if x.get("citingPaper"))
        d["s2"] = {"seed": seedrec, "items": items}
        data = json.loads((CACHE / "coci" / f"{seed}_citations.json").read_text())
        d["coci"] = {"items": [r["citing"].lower() for r in data.get("_list", [])]}
        cr = CACHE / "crossref" / f"{seed}_seed.json"
        d["crossref"] = {"seed": json.loads(cr.read_text()) if cr.exists() else {}}
        out[seed] = d
    return out


def build_records():
    lists = load_cached_lists()
    seed_wid = {}
    for seed, d in lists.items():
        if d["openalex"]["seed"].get("id"):
            seed_wid[seed] = d["openalex"]["seed"]["id"]
    hits = []   # (db, seed, meta)
    raw_counts = {}
    for seed, d in lists.items():
        items = d["openalex"]["items"]
        raw_counts[(seed, "openalex")] = None if items is None else len(items)
        for w in items or []:
            hits.append(("openalex", seed, oa_to_meta(w)))
        raw_counts[(seed, "s2")] = len(d["s2"]["items"])
        for p in d["s2"]["items"]:
            hits.append(("s2", seed, s2_to_meta(p)))
        raw_counts[(seed, "coci")] = len(d["coci"]["items"])
        for doi in d["coci"]["items"]:
            hits.append(("coci", seed, {"doi": clean_doi(doi), "title": None, "first_author": None,
                                        "year": None, "venue": None}))

    # reverse check: OpenAlex single records of candidate DOIs
    single: dict[str, dict] = {}
    for f in (CACHE / "lookup").glob("openalex_*.json"):
        rec = json.loads(f.read_text())
        if rec.get("_http_status") == 404:
            m = re.search(r"works/doi:(.*?)\?", rec.get("_url", ""))
            if m:
                single[clean_doi(urllib.parse.unquote(m.group(1)))] = rec
            continue
        single[clean_doi(rec.get("doi")) or ""] = rec
    reverse_checked = {s: 0 for s in SEEDS}
    for doi, rec in single.items():
        if rec.get("_http_status") == 404 or not doi:
            continue
        refs = set(rec.get("referenced_works") or [])
        for seed, wid in seed_wid.items():
            if wid in refs:
                hits.append(("openalex_ref", seed, oa_to_meta(rec)))

    records: dict[str, dict] = {}
    ty_index: dict[str, str] = {}

    def add(key, db, seed, meta):
        r = records.setdefault(key, {"key": key, "doi": meta.get("doi"), "meta": {},
                                     "cites": {s: set() for s in SEEDS}, "found": set(),
                                     "openalex_id": None, "s2_id": None, "arxiv": None})
        r["cites"][seed].add(db)
        r["found"].add(db)
        if meta.get("doi") and not r["doi"]:
            r["doi"] = meta["doi"]
        for k in ("openalex_id", "s2_id", "arxiv"):
            if meta.get(k) and not r.get(k):
                r[k] = meta[k]
        # metadata preference: OpenAlex > S2 > (lookup for COCI-only records, filled later)
        if db != "coci" and meta.get("title"):
            cur = r["meta"].get("_db")
            if not cur or (db.startswith("openalex") and not cur.startswith("openalex")):
                r["meta"] = {**meta, "_db": db}
        return r

    for db, seed, meta in hits:                       # 1) records with a DOI
        if meta.get("doi"):
            add("doi:" + meta["doi"], db, seed, meta)
    for key, r in records.items():
        if r["meta"].get("title") and r["meta"].get("year"):
            ty_index.setdefault(f"{norm_title(r['meta']['title'])}|{r['meta']['year']}", key)
    for db, seed, meta in hits:                       # 2) no DOI: normalised title + year
        if meta.get("doi"):
            continue
        tkey = f"{norm_title(meta.get('title'))}|{meta.get('year')}"
        key = ty_index.get(tkey) or ("ty:" + tkey)
        add(key, db, seed, meta)
        ty_index.setdefault(tkey, key)

    for r in records.values():                        # 3) metadata for COCI-only records
        if r["doi"]:
            rec = single.get(r["doi"])
            if rec and rec.get("_http_status") != 404:
                r["openalex_id"] = r["openalex_id"] or oa_to_meta(rec).get("openalex_id")
        if not r["meta"].get("title") and r["doi"]:
            rec = single.get(r["doi"])
            if rec and rec.get("_http_status") != 404:
                r["meta"] = {**oa_to_meta(rec), "_db": "openalex-single"}
            else:
                cr = crossref_single(r["doi"])
                if cr.get("_http_status") != 404:
                    r["meta"] = {**crossref_to_meta(cr["message"]), "_db": "crossref-single"}
                else:
                    r["meta"] = {"doi": r["doi"], "_db": "none"}
    return records, raw_counts, lists, single


def cmd_build(args) -> None:
    records, raw_counts, lists, single = build_records()
    seeds = read_seed_dois()

    print("== Seed identifiers and database citation counts")
    for seed in SEEDS:
        oa = lists[seed]["openalex"]["seed"]
        s2 = lists[seed]["s2"]["seed"]
        cr = (lists[seed]["crossref"]["seed"] or {}).get("message", {})
        print(f"{seed:5s} doi={seeds[seed]}  openalex={oa.get('id', 'NOT FOUND (404)')} "
              f"OA_cited_by_count={oa.get('cited_by_count')}  "
              f"s2={s2.get('paperId', 'NOT FOUND (404)')} S2_citationCount={s2.get('citationCount')}  "
              f"Crossref_is_referenced_by_count={cr.get('is-referenced-by-count')}")

    print("\n== Raw citing-link counts returned by each list endpoint (before de-duplication)")
    print(f"{'seed':5s} {'OpenAlex cites: list':>22s} {'S2':>5s} {'COCI':>5s}")
    for seed in SEEDS:
        oa = raw_counts[(seed, "openalex")]
        print(f"{seed:5s} {('NOT RETRIEVED (429)' if oa is None else str(oa)):>22s} "
              f"{raw_counts[(seed, 's2')]:5d} {raw_counts[(seed, 'coci')]:5d}")

    n_single = sum(1 for r in single.values())
    n_single_404 = sum(1 for r in single.values() if r.get("_http_status") == 404)
    print(f"\n== OpenAlex single-record lookups of candidate DOIs: {n_single} "
          f"(not in OpenAlex: {n_single_404})")

    print("\n== Unique citing works per seed after merging, by link source"
          " (OAref = link found in the citing work's OpenAlex referenced_works)")
    print(f"{'seed':5s} {'union':>5s} {'OA':>4s} {'OAref':>6s} {'S2':>4s} {'COCI':>5s} "
          f"{'onlyS2':>7s} {'onlyCOCI':>9s} {'S2&COCI':>8s} {'OAcount-OAref':>14s}")
    for seed in SEEDS:
        rs = [r for r in records.values() if r["cites"][seed]]
        n = {db: sum(1 for r in rs if db in r["cites"][seed]) for db in LINK_DBS}
        oa_any = lambda r: bool(r["cites"][seed] & {"openalex", "openalex_ref"})
        only_s2 = sum(1 for r in rs if r["cites"][seed] == {"s2"})
        only_coci = sum(1 for r in rs if r["cites"][seed] == {"coci"})
        both = sum(1 for r in rs if {"s2", "coci"} <= r["cites"][seed])
        oacount = lists[seed]["openalex"]["seed"].get("cited_by_count")
        gap = (oacount - sum(1 for r in rs if oa_any(r))) if oacount is not None else None
        print(f"{seed:5s} {len(rs):5d} {n['openalex']:4d} {n['openalex_ref']:6d} {n['s2']:4d} "
              f"{n['coci']:5d} {only_s2:7d} {only_coci:9d} {both:8d} {gap!s:>14s}")
    print("   OAcount-OAref = OpenAlex cited_by_count minus the OpenAlex links confirmed here = number"
          " of OpenAlex-known citing works NOT enumerated (list endpoint unavailable).")

    prim = [r for r in records.values() if any(r["cites"][s] for s in SEEDS_PRIMARY)]
    supp_only = [r for r in records.values()
                 if not any(r["cites"][s] for s in SEEDS_PRIMARY)
                 and any(r["cites"][s] for s in SEEDS_SUPPLEMENT)]
    print(f"\n== Unique citing works overall: {len(records)}  (citing at least one of P01/P02/P02E/P03:"
          f" {len(prim)};  citing only P08 and/or P09: {len(supp_only)})")
    print(f"   with DOI: {sum(1 for r in records.values() if r['doi'])};"
          f"  without DOI (title+year key): {sum(1 for r in records.values() if not r['doi'])}")
    for db in LINK_DBS:
        print(f"   link found via {DB_CODE[db]:6s}: {sum(1 for r in records.values() if db in r['found'])}")
    print(f"   metadata source: " + ", ".join(
        f"{k}={sum(1 for r in records.values() if r['meta'].get('_db') == k)}"
        for k in sorted({r['meta'].get('_db') for r in records.values()}, key=str)))

    by_title: dict[str, list] = {}
    for r in records.values():
        by_title.setdefault(norm_title(r["meta"].get("title")), []).append(r)
    dups = {t: rs for t, rs in by_title.items() if t and len(rs) > 1}
    print(f"\n== Same normalised title under different merge keys (not merged; check by hand): {len(dups)}")
    for t, rs in dups.items():
        print("   " + t[:90])
        for r in rs:
            print(f"      {r['key']}  year={r['meta'].get('year')}  found={sorted(r['found'])}")

    years = [(r["meta"].get("year") or 0) for r in records.values()]
    print("\n== Citing works by publication year (all | citing P01/P02/P02E/P03)")
    prim_keys = {r["key"] for r in prim}
    bins = [(0, 0, "unknown"), (1988, 1993, "1988-1993"), (1994, 1999, "1994-1999"),
            (2000, 2009, "2000-2009"), (2010, 2019, "2010-2019"), (2020, 2026, "2020-2026")]
    for lo, hi, lab in bins:
        a = sum(1 for r in records.values() if lo <= (r["meta"].get("year") or 0) <= hi)
        b = sum(1 for r in prim if lo <= (r["meta"].get("year") or 0) <= hi)
        print(f"   {lab:10s} {a:4d} {b:4d}")

    rows = []
    for r in sorted(records.values(), key=lambda r: ((r["meta"].get("year") or 0),
                                                     norm_title(r["meta"].get("title")))):
        cls, ev = CLASSIFICATION.get(r["key"], ("UNCLASSIFIED", ""))
        rows.append({
            "citing_doi": r["doi"] or "",
            "title": re.sub(r"\s+", " ", r["meta"].get("title") or ""),
            "first_author": r["meta"].get("first_author") or "",
            "year": r["meta"].get("year") or "",
            "venue": re.sub(r"\s+", " ", r["meta"].get("venue") or ""),
            **{f"cites_{s}": ("|".join(DB_CODE[d] for d in LINK_DBS if d in r["cites"][s]) or "0")
               for s in SEEDS},
            "found_in_openalex": int(bool(r["found"] & {"openalex", "openalex_ref"})),
            "found_in_s2": int("s2" in r["found"]),
            "found_in_coci": int("coci" in r["found"]),
            "class": cls,
            "evidence": ev,
            "_key": r["key"],
        })
    cols = (["citing_doi", "title", "first_author", "year", "venue"]
            + [f"cites_{s}" for s in SEEDS]
            + ["found_in_openalex", "found_in_s2", "found_in_coci", "class", "evidence"])
    with TSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t", extrasaction="ignore",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"\n== Wrote {len(rows)} rows to {TSV.relative_to(REPO)}")

    unused = set(CLASSIFICATION) - {x["_key"] for x in rows}
    if unused:
        print(f"   WARNING: {len(unused)} CLASSIFICATION keys match no record: {sorted(unused)}")

    print("\n== Class counts (all | citing P01/P02/P02E/P03 | citing only P08/P09)")
    for c in CLASSES + ["UNCLASSIFIED"]:
        a = sum(1 for x in rows if x["class"] == c)
        b = sum(1 for x in rows if x["class"] == c and x["_key"] in prim_keys)
        print(f"   {c:26s} {a:4d} {b:4d} {a - b:4d}")
    n_title = sum(1 for x in rows if x["evidence"].startswith("UNVERIFIED"))
    n_abs = sum(1 for x in rows if x["evidence"].startswith("SECTION_READ"))
    print(f"   classified from an abstract: {n_abs};  from the title only (UNVERIFIED): {n_title}")

    print("\n== Citing works published after 1993 in classes REH-experiment / REH-method/theory")
    for x in rows:
        if x["class"] in ("REH-experiment", "REH-method/theory") and int(x["year"] or 0) > 1993:
            print(f"   {x['year']}  {x['class']:18s} {x['first_author']}  {x['title'][:90]}  "
                  f"{x['citing_doi']}")

    if args.list:
        print("\n== All merged records (key | year | first author | title | venue | cites | class)")
        for x in rows:
            cites = " ".join(f"{s}:{x['cites_' + s]}" for s in SEEDS if x["cites_" + s] != "0")
            print(f"{x['_key']} | {x['year']} | {x['first_author']} | {x['title']} | {x['venue']} | "
                  f"{cites} | {x['class']}")


# -------------------------------------------------------------------------------- abstracts --

def oa_abstract(inv: dict | None) -> str | None:
    if not inv:
        return None
    pos = []
    for word, idxs in inv.items():
        for i in idxs:
            pos.append((i, word))
    return " ".join(w for _, w in sorted(pos))


def cmd_abstracts(args) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    records, _, _, _ = build_records()
    res = []
    for r in records.values():
        entry = {"key": r["key"], "doi": r["doi"], "title": r["meta"].get("title"),
                 "year": r["meta"].get("year"), "venue": r["meta"].get("venue"), "abstracts": []}
        if r.get("openalex_id"):
            url = f"https://api.openalex.org/works/{r['openalex_id']}?select=id,abstract_inverted_index"
            try:
                st, body = http_get(url)
                if st == 200:
                    a = oa_abstract(json.loads(body).get("abstract_inverted_index"))
                    if a:
                        entry["abstracts"].append({"url": url, "text": a})
            except RateLimited:
                pass
        s2id = r.get("s2_id") or (f"DOI:{r['doi']}" if r["doi"] else None)
        if s2id:
            url = f"https://api.semanticscholar.org/graph/v1/paper/{doi_path(s2id)}?fields=abstract"
            st, body = http_get(url)
            if st == 200:
                a = json.loads(body).get("abstract")
                if a:
                    entry["abstracts"].append({"url": url, "text": a})
            time.sleep(1.1)
        if r["doi"]:
            url = f"https://api.crossref.org/works/{doi_path(r['doi'])}"
            st, body = http_get(url)
            if st == 200:
                a = json.loads(body)["message"].get("abstract")
                if a:
                    entry["abstracts"].append({"url": url, "text": re.sub(r"\s+", " ",
                                                                          re.sub(r"<[^>]+>", " ", a))})
        res.append(entry)
        print(f"{r['key'][:70]:70s} abstracts={len(entry['abstracts'])}", flush=True)
    (out / "abstracts.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"wrote {len(res)} entries to {out / 'abstracts.json'}; "
          f"{sum(1 for e in res if e['abstracts'])} have at least one abstract")


# ----------------------------------------------------------------------------------- search --

SEARCHES = [
    # (topic, engine, query)
    # Topic A: reflection electron holography (any year; post-1993 items are selected by hand)
    ("A", "openalex-title_abstract", '"reflection electron holography"'),
    ("A", "openalex-title_abstract", '"electron holography" "reflection electron microscopy"'),
    ("A", "openalex-title_abstract", '"electron holography" RHEED'),
    ("A", "s2-bulk", '"reflection electron holography"'),
    ("A", "s2-bulk", '"reflection electron holographic"'),
    ("A", "s2-bulk", '"electron holography" + "reflection electron microscopy"'),
    ("A", "s2-bulk", '"electron holography" + (RHEED | "reflection high energy electron")'),
    ("A", "s2-bulk", '"electron holography" + reflection + surface + step'),
    ("A", "s2-search", "reflection electron holography surface step phase"),
    ("A", "europepmc", '(TITLE:"reflection electron holography" OR ABSTRACT:"reflection electron holography")'),
    ("A", "europepmc", '(ABSTRACT:"electron holography" AND ABSTRACT:"reflection")'),
    ("A", "crossref-query", "reflection electron holography"),
    ("A", "crossref-query", "reflection electron holography surface steps"),
    ("A", "arxiv", 'abs:"reflection electron holography"'),
    ("A", "arxiv", 'abs:"electron holography" AND abs:reflection AND abs:surface'),
    # Topic B: electron ptychography in reflection geometry
    ("B", "openalex-title_abstract", '"electron ptychography" reflection'),
    ("B", "s2-bulk", '"electron ptychography" + reflection'),
    ("B", "s2-bulk", 'ptychography + (RHEED | "reflection high energy electron")'),
    ("B", "s2-bulk", 'ptychography + "reflection electron microscopy"'),
    ("B", "s2-bulk", 'ptychography + electron + "grazing incidence"'),
    ("B", "s2-bulk", 'ptychography + ("backscattered electron" | "backscattered electrons")'),
    ("B", "s2-bulk", 'ptychography + "scanning electron microscope" + reflection'),
    ("B", "s2-search", "reflection electron ptychography"),
    ("B", "europepmc", '(ABSTRACT:"ptychography" AND ABSTRACT:"electron" AND ABSTRACT:"reflection")'),
    ("B", "arxiv", 'abs:ptychography AND abs:electron AND abs:reflection'),
    ("B", "arxiv", 'abs:ptychography AND abs:RHEED'),
    ("B", "arxiv", 'abs:ptychography AND abs:"electron" AND abs:"grazing"'),
    # Topic C: X-ray / EUV / visible reflection-mode and Bragg-surface ptychography
    ("C", "openalex-title_abstract", '"reflection ptychography"'),
    ("C", "s2-bulk", '"reflection ptychography"'),
    ("C", "s2-bulk", 'ptychography + "reflection geometry"'),
    ("C", "s2-bulk", '"reflective ptychography"'),
    ("C", "s2-bulk", '"grazing incidence ptychography"'),
    ("C", "s2-bulk", '"Bragg ptychography"'),
    ("C", "s2-bulk", 'ptychography + "crystal truncation rod"'),
    ("C", "s2-bulk", 'ptychography + ("extreme ultraviolet" | EUV) + reflection'),
    ("C", "s2-bulk", '"ptychographic reflectometry"'),
    ("C", "europepmc", '(ABSTRACT:"ptychography" AND ABSTRACT:"reflection geometry")'),
    ("C", "arxiv", 'abs:ptychography AND abs:"reflection geometry"'),
    ("C", "arxiv", 'abs:"Bragg ptychography"'),
    ("C", "arxiv", 'abs:ptychography AND abs:"grazing incidence"'),
    ("C", "arxiv", 'abs:ptychography AND abs:"crystal truncation rod"'),
]


def run_search(i: int, topic: str, engine: str, query: str, refresh: bool) -> dict:
    sdir = CACHE / "search"
    fname = sdir / f"q{i:02d}_{topic}_{engine}.json"
    status = "ok"
    items: list = []
    n = None
    if engine == "openalex-title_abstract":
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "filter": f"title_and_abstract.search:{query}", "per-page": "200",
            "select": "id,doi,title,publication_year,authorships,primary_location,type"})
        try:
            data = cached_json(fname, url, refresh)
            n = data.get("meta", {}).get("count")
            items = [oa_to_meta(w) for w in data.get("results", [])]
        except RateLimited as e:
            status = f"NOT RUN: HTTP 429 (OpenAlex budget exhausted; retry-after {e.retry_after} s)"
    elif engine == "s2-search":
        url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({
            "query": query, "limit": "100", "fields": "title,year,venue,externalIds,authors"})
        data = cached_json(fname, url, refresh)
        n = data.get("total")
        items = [s2_to_meta(p) for p in data.get("data", [])]
        time.sleep(1.1)
    elif engine == "s2-bulk":
        url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode({
            "query": query, "fields": "title,year,venue,externalIds,authors"})
        data = cached_json(fname, url, refresh)
        n = data.get("total")
        items = [s2_to_meta(p) for p in data.get("data", [])]
        time.sleep(1.1)
    elif engine == "europepmc":
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({
            "query": query, "format": "json", "pageSize": "200", "resultType": "lite"})
        data = cached_json(fname, url, refresh)
        n = data.get("hitCount")
        for x in (data.get("resultList") or {}).get("result", []):
            items.append({"doi": clean_doi(x.get("doi")), "title": x.get("title"),
                          "first_author": (x.get("authorString") or "").split(",")[0] or None,
                          "year": x.get("pubYear"), "venue": x.get("journalTitle")})
    elif engine == "crossref-query":
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode({
            "query.bibliographic": query, "rows": "100",
            "select": "DOI,title,author,container-title,issued,type"})
        data = cached_json(fname, url, refresh)
        n = (data.get("message") or {}).get("total-results")
        for m in (data.get("message") or {}).get("items", []):
            items.append(crossref_to_meta(m))
        status = "ok (relevance-ranked, any-term matching: total-results is not a phrase hit count)"
    elif engine == "arxiv":
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({
            "search_query": query, "start": "0", "max_results": "200"})
        xml_path = fname.with_suffix(".xml")
        if xml_path.exists() and not refresh:
            body = xml_path.read_bytes()
        else:
            _, body = http_get(url, accept="application/atom+xml")
            sdir.mkdir(parents=True, exist_ok=True)
            # keep bibliographic fields only: drop <summary> (abstract) before caching
            body = re.sub(rb"<summary>.*?</summary>", b"<summary/>", body, flags=re.S)
            xml_path.write_bytes(body)
            time.sleep(3.1)
        ns = {"a": "http://www.w3.org/2005/Atom",
              "os": "http://a9.com/-/spec/opensearch/1.1/",
              "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(body)
        n = int(root.findtext("os:totalResults", default="0", namespaces=ns))
        for e in root.findall("a:entry", ns):
            au = e.find("a:author/a:name", ns)
            items.append({"doi": clean_doi(e.findtext("arxiv:doi", default=None, namespaces=ns)),
                          "title": re.sub(r"\s+", " ", e.findtext("a:title", default="", namespaces=ns)),
                          "first_author": au.text if au is not None else None,
                          "year": (e.findtext("a:published", default="", namespaces=ns) or "")[:4],
                          "venue": "arXiv " + (e.findtext("a:id", default="", namespaces=ns)
                                               .rsplit("/abs/", 1)[-1])})
    else:
        raise ValueError(engine)
    return {"i": i, "topic": topic, "engine": engine, "query": query, "url": url, "total": n,
            "items": items, "status": status}


def cmd_search(args) -> None:
    results = []
    for i, (topic, engine, query) in enumerate(SEARCHES, 1):
        r = run_search(i, topic, engine, query, args.refresh)
        results.append(r)
        print(f"q{i:02d} [{topic}] {engine:24s} total={r['total']!s:>8s} returned={len(r['items']):4d}  "
              f"{query}   [{r['status']}]", flush=True)
    if args.list:
        for r in results:
            print(f"\n--- q{r['i']:02d} [{r['topic']}] {r['engine']} {r['query']}  (total {r['total']})")
            for it in sorted(r["items"], key=lambda x: str(x.get("year"))):
                print(f"   {it.get('year')} | {it.get('first_author')} | {it.get('title')} | "
                      f"{it.get('venue')} | {it.get('doi')}")


# --------------------------------------------------------------------------------------- oa --

def cmd_oa(args) -> None:
    seeds = read_seed_dois()
    targets = [(k, v) for k, v in seeds.items()] + [("cand", d) for d in args.dois]
    for label, doi in targets:
        oa = cached_json(CACHE / "oa" / f"openalex_{safe_name(doi)}.json",
                         f"https://api.openalex.org/works/doi:{doi_path(doi)}"
                         "?select=id,doi,title,publication_year,open_access,best_oa_location", False)
        if oa.get("_http_status") == 404:
            print(f"{label:5s} {doi}: NOT IN OPENALEX")
        else:
            bl = oa.get("best_oa_location") or {}
            print(f"{label:5s} {doi}: oa_status={oa['open_access'].get('oa_status')} "
                  f"is_oa={oa['open_access'].get('is_oa')} oa_url={oa['open_access'].get('oa_url')} "
                  f"best_oa_landing={bl.get('landing_page_url')} best_oa_pdf={bl.get('pdf_url')} "
                  f"best_oa_license={bl.get('license')}")
        if label == "cand":
            cr = cached_json(CACHE / "oa" / f"crossref_{safe_name(doi)}.json",
                             f"https://api.crossref.org/works/{doi_path(doi)}", False,
                             drop=("abstract", "reference"))
            if cr.get("_http_status") == 404:
                print("      CROSSREF: 404 (DOI not registered with Crossref)")
                continue
            m = cr["message"]
            au = "; ".join(f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
                           for a in m.get("author", []))
            print(f"      CROSSREF: {m.get('title')} | {au} | {m.get('container-title')} | "
                  f"vol {m.get('volume')} | issue {m.get('issue')} | page {m.get('page')} | "
                  f"article-number {m.get('article-number')} | issued "
                  f"{(m.get('issued') or {}).get('date-parts')} | type {m.get('type')} | "
                  f"DOI {m.get('DOI')}")


# ------------------------------------------------------------------------------------- main --

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fetch"); p.add_argument("--refresh", action="store_true"); p.set_defaults(f=cmd_fetch)
    p = sub.add_parser("build"); p.add_argument("--list", action="store_true"); p.set_defaults(f=cmd_build)
    p = sub.add_parser("abstracts"); p.add_argument("--out", required=True); p.set_defaults(f=cmd_abstracts)
    p = sub.add_parser("search"); p.add_argument("--refresh", action="store_true")
    p.add_argument("--list", action="store_true"); p.set_defaults(f=cmd_search)
    p = sub.add_parser("oa"); p.add_argument("dois", nargs="*"); p.set_defaults(f=cmd_oa)
    args = ap.parse_args(argv)
    args.f(args)


if __name__ == "__main__":
    main()
