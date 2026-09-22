#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
record_tocs.py -- reading plan step 3: record publisher tables of contents
==========================================================================
Fetches (optional) and parses the publisher pages that carry the tables of
contents (TOCs) of books B01-B15 of docs/references.bib, and writes one
machine-readable row per TOC entry to a TSV with the columns

    book_id  edition  isbn  chapter_number  chapter_title  pages  source_url

Report: docs/agent_reports/L3_book_tables_of_contents.md (written by hand
from the same raw pages; this script only makes the TSV reproducible).

Rules implemented here (project source policy):
  * Every cell is copied from a page that was actually fetched.  Nothing is
    completed from memory, no DOI is constructed: chapter DOIs are taken
    from links on the publisher page or from Crossref records.
  * A row records what ONE route shows.  Where two routes are combined
    (e.g. Springer HTML titles/pages + chapter numbers printed in Springer's
    free front-matter "Contents" PDF), the join key is the chapter TITLE
    (first 30 characters, case, punctuation and spaces ignored), and both
    URLs are written into source_url.  When the printed Contents gives a
    first page different from the online page range, both are kept.
  * If a route does not print a value, the cell is empty ("" = not printed
    by that route).  The report explains every empty cell.
  * Raw pages are cached in --raw-dir (outside the repository).

Routes (per publisher)
  Springer (B05 B06 B09 B10 B12 B13 B14 B15): link.springer.com/book/<doi>
      (all ?page=N TOC pages) -> title, authors, page range, chapter DOI;
      front-matter PDF link.springer.com/content/pdf/bfm:<isbn>/1 -> printed
      chapter numbers (joined on title).  Needs pypdf for the PDF step.
  Cambridge Core (B02 B07): TOC on the book landing page (?pageNum=N).
  Elsevier (B03 B04): shop.elsevier.com product page TOC (numbers, titles,
      no pages) + Crossref records filtered by print ISBN (titles, pages).
  OUP (B01 B08): academic.oup.com and global.oup.com refuse automated
      clients (bot challenge); Crossref records deposited by OUP are used
      (titles, pages).  They carry no chapter number: the column is left
      empty and the report states the inferred number separately.
  Wiley (B11): Crossref records (titles, pages) + the publisher's free
      front-matter excerpt PDF "Contents" (printed numbers, first pages).

Usage
  python3 tools/lit/record_tocs.py --raw-dir DIR --out docs/agent_reports/L3_book_tocs.tsv [--fetch]

Dependencies: CPython 3.9+, curl on PATH (only with --fetch), pypdf
(optional; without it the Springer/Wiley chapter-number join is skipped and
the chapter_number column stays empty for those rows).
"""
from __future__ import annotations

import argparse
import csv
import html as htmlmod
import json
import os
import re
import subprocess
import sys
import time
import unicodedata

# ---------------------------------------------------------------------------
# Book configuration: edition string and ISBN exactly as used in the TSV.
# The "edition" column records the edition named in docs/references.bib;
# the ISBN is the one printed on the route that was read (see report).
# ---------------------------------------------------------------------------
SPRINGER = {
    # id: (suffix of the book DOI as given in references.bib, edition label);
    # ISBNs are read from the page's "Bibliographic Information" block
    "B05": ("978-3-642-32119-1", "2nd ed. (Springer 2013; bib year 2013)"),
    "B06": ("978-3-030-33260-0", "3rd ed. (Springer 2020)"),
    "B09": ("978-1-4615-4817-1", "1999 (Springer/Plenum)"),
    "B10": ("978-3-540-37204-2", "2nd ed. (Springer 1999)"),
    "B12": ("978-3-030-00069-1", "1st ed. (Springer 2019)"),
    "B13": ("978-0-387-40093-8", "5th ed. (Springer 2008)"),
    "B14": ("978-0-387-76501-3", "2nd ed. (Springer 2009)"),
    "B15": ("978-1-4419-9583-4", "3rd ed. (Springer 2011)"),
}
CUP = {
    "B02": ("https://www.cambridge.org/core/books/introduction-to-conventional-transmission-electron-microscopy/257FBB684B79174B1C6D3ACCC256ECC0",
            "2003 (CUP)"),
    "B07": ("https://www.cambridge.org/core/books/reflection-highenergy-electron-diffraction/162FE7186C89C6A8269619B7EDF5F1E8",
            "2004 print (CUP)"),
}
ELSEVIER = {
    "B03": ("https://shop.elsevier.com/books/principles-of-electron-optics-volume-3/hawkes/978-0-12-818979-5",
            "9780128189795", "2nd ed. (Academic Press 2022)"),
    "B04": ("https://shop.elsevier.com/books/principles-of-electron-optics-volume-4/hawkes/978-0-323-91646-2",
            "9780323916462", "2nd ed. (Academic Press 2022)"),
}
# OUP: Crossref query URLs.  B01 chapters of the 4th edition carry no ISBN
# field in Crossref, so they are selected by the book identifier that is part
# of the DOIs Crossref returns (never by constructing a DOI).
OUP = {
    "B01": ("https://api.crossref.org/works?filter=prefix:10.1093,type:book-chapter"
            "&query.container-title=High-Resolution+Electron+Microscopy&query.author=Spence&rows=40",
            "9780199668632", "4th ed. (OUP 2013)"),
    "B08": ("https://api.crossref.org/works?filter=isbn:9780198500742&rows=100",
            "9780198500742", "2004 (OUP)"),
}
WILEY = {
    "B11": ("https://api.crossref.org/works?filter=isbn:9783527348046&rows=100",
            "https://media.wiley.com/product_data/excerpt/42/35273480/3527348042-23.pdf",
            "9783527348046", "1st ed. (Wiley-VCH; bib year 2022)"),
}

# ---------------------------------------------------------------------------
# Fetching (curl, cookie jar, honest default user agent of curl)
# ---------------------------------------------------------------------------
def fetch(url: str, path: str, cookie: str, tries: int = 4, is_json: bool = False) -> bool:
    for k in range(tries):
        r = subprocess.run(["curl", "-sS", "-L", "-c", cookie, "-b", cookie, "--max-time", "120",
                            "-o", path, "-w", "%{http_code}", url], capture_output=True, text=True)
        ok = r.stdout.strip() == "200" and os.path.exists(path) and os.path.getsize(path) > 0
        if ok and is_json:
            try:
                json.load(open(path, encoding="utf-8"))
            except Exception:
                ok = False
        if ok:
            return True
        time.sleep(3 + 2 * k)
    sys.stderr.write(f"FETCH FAILED {url}\n")
    return False


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def norm(s: str) -> str:
    """Normalisation used ONLY for joining two routes, never for output."""
    s = unicodedata.normalize("NFKC", s).lower()
    s = s.replace("–", "-").replace("—", "-").replace("’", "'")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


# ---------------------------------------------------------------------------
# Springer
# ---------------------------------------------------------------------------
def springer_pages(raw: str, bid: str) -> list[str]:
    files = sorted(f for f in os.listdir(raw) if re.fullmatch(rf"{bid}_springer_p\d+\.html", f))
    return [os.path.join(raw, f) for f in sorted(files, key=lambda x: int(re.search(r"p(\d+)", x).group(1)))]


def springer_fetch(raw: str, bid: str, doi_suffix: str, cookie: str) -> None:
    base = f"https://link.springer.com/book/10.1007/{doi_suffix}"
    p1 = os.path.join(raw, f"{bid}_springer_p1.html")
    fetch(base, p1, cookie)
    s = open(p1, encoding="utf-8").read()
    npages = max([1] + [int(n) for n in re.findall(r"\?page=(\d+)#toc", s)])
    for n in range(2, npages + 1):
        fetch(f"{base}?page={n}", os.path.join(raw, f"{bid}_springer_p{n}.html"), cookie)
    bl = re.search(r'href="(/content/pdf/bfm:[^"/]+/1)"', s)  # link as printed on the page
    if bl:
        fetch("https://link.springer.com" + bl.group(1), os.path.join(raw, f"{bid}_bfm.pdf"), cookie)


def springer_parse(raw: str, bid: str) -> tuple[dict, list[dict]]:
    info: dict = {}
    entries: list[dict] = []
    for fp in springer_pages(raw, bid):
        s = open(fp, encoding="utf-8").read()
        if not info:
            for m in re.finditer(r"c-bibliographic-information__list-item(.*?)</li>", s, re.S):
                t = clean(re.sub(r"<[^>]+>", " ", m.group(1).split(">", 1)[1]))
                k, _, v = t.partition(":")
                if k and v:
                    info[k.strip()] = v.strip()
        # walk parts and chapters in document order: every part heading and
        # every <li data-test="chapter"> start is a token; a chapter item
        # runs from its token to the next token.
        toks = [(m.start(), "part", m.group(1)) for m in re.finditer(r'data-title="part-title">(.*?)</h3>', s, re.S)]
        toks += [(m.start(), "li", None) for m in re.finditer(r'<li data-test="chapter">', s)]
        toks.sort()
        for n, (pos, kind0, ptitle) in enumerate(toks):
            if kind0 == "part":
                entries.append({"kind": "part", "title": clean(ptitle)})
                continue
            end = toks[n + 1][0] if n + 1 < len(toks) else len(s)
            it = s[pos:end]
            t = re.search(r'data-test="(chapter-title-[^"]*|front-matter|back-matter)"[^>]*>(.*?)</h[34]>', it, re.S)
            if not t:
                continue
            kind = "chapter" if t.group(1).startswith("chapter-title") else t.group(1)
            href = re.search(r'href="(/chapter/10\.1007/[^"]+)"', it)
            pages = re.search(r'data-test="page-number">([^<]+)<', it)
            auth = re.search(r'app-author-list__item">([^<]+)<', it)
            entries.append({
                "kind": kind,
                "title": clean(t.group(2)) if kind == "chapter" else ("Front Matter" if kind == "front-matter" else "Back Matter"),
                "url": "https://link.springer.com" + href.group(1) if href else "",
                "pages": pages.group(1).replace("Pages ", "").strip() if pages else "",
                "authors": clean(auth.group(1)) if auth else "",
            })
    return info, entries


def pdf_text(path: str) -> str | None:
    try:
        import pypdf  # type: ignore
    except Exception:
        return None
    if not os.path.exists(path):
        return None
    try:
        r = pypdf.PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in r.pages)
    except Exception:
        return None


def contents_entries(txt: str) -> list[tuple[str, str, str]]:
    """Top-level entries (number, title, printed first page) of a printed
    'Contents' list extracted from a front-matter PDF.  Chapter lines look
    like '<N>[.] <Title> ....... <page>' (appendices: a capital letter).
    Section lines '<N>.<M> ...' are skipped.  A title without dot leaders
    is joined with the next line (wrapped titles).  Digits separated by
    spaces in the page number ('2 9') are joined (PDF text artefact).
    OCR'd front matter (B09) often has no page on the same line: the page
    is then left empty."""
    lines = [l.strip() for l in txt.splitlines()]
    start = next((i for i, l in enumerate(lines) if l.lower() == "contents"), 0)
    lines = lines[start:]
    out: list[tuple[str, str, str]] = []
    for idx, l in enumerate(lines):
        if re.match(r"^\d{1,3}\.\d", l):
            continue
        m = re.match(r"^(?:Appendix\s+)?(\d{1,2}|[A-H])\.?\s+(\S.*)$", l)
        if not m:
            continue
        num, rest = m.group(1), m.group(2)
        if not re.search(r"\.\s?\.", rest) and idx + 1 < len(lines) \
                and not re.match(r"^(\d|[A-H]\s)", lines[idx + 1]):
            rest = rest + " " + lines[idx + 1]
        pm = re.search(r"(?:\.\s?){2,}[\s.,]*((?:\d\s?){1,4})\s*$", rest)
        page = re.sub(r"\s", "", pm.group(1)) if pm else ""
        title = re.split(r"\s*(?:\.\s?){2,}", rest)[0].strip()
        out.append((num, title, page))
    return out


def match_contents(title: str, entries: list[tuple[str, str, str]]) -> tuple[str, str]:
    """(printed number, printed first page) of the first Contents entry whose
    normalised title shares its first min(30, len) characters with the
    normalised online title; ('', '') if none."""
    a = norm(title).replace(" ", "")      # PDF text often drops or inserts spaces
    for num, t, page in entries:
        b = norm(t).replace(" ", "")
        k = min(len(a), len(b), 30)
        if k >= 8 and a[:k] == b[:k]:
            return num, page
    return "", ""


def rows_springer(raw: str) -> list[list[str]]:
    rows = []
    for bid, (suffix, edition) in SPRINGER.items():
        if not springer_pages(raw, bid):
            sys.stderr.write(f"{bid}: no cached Springer page\n")
            continue
        info, entries = springer_parse(raw, bid)
        isbn = "; ".join(f"{k.replace(' ISBN', '')} {info[k].split(' Published')[0]}"
                         for k in ("Hardcover ISBN", "Softcover ISBN", "eBook ISBN") if k in info)
        p1 = open(springer_pages(raw, bid)[0], encoding="utf-8").read()
        bl = re.search(r'href="(/content/pdf/bfm:[^"/]+/1)"', p1)
        bfm_url = "https://link.springer.com" + bl.group(1) if bl else ""
        txt = pdf_text(os.path.join(raw, f"{bid}_bfm.pdf"))
        centries = contents_entries(txt) if txt else []
        base = f"https://link.springer.com/book/10.1007/{suffix}"
        part = ""
        for e in entries:
            if e["kind"] == "part":
                part = e["title"]
                continue
            num, printed = match_contents(e["title"], centries) if e["kind"] == "chapter" else ("", "")
            pages = e.get("pages", "")
            if printed and printed != pages.split("-")[0]:
                pages += f" [front-matter Contents prints first page {printed}]"
            src = base + (" + " + bfm_url if num else "")
            if e.get("url"):
                src += " ; chapter: " + e["url"]
            rows.append([bid, edition, isbn, num,
                         e["title"] + (f"  [part: {part}]" if part else ""), pages, src])
        # appendices printed in the front-matter Contents but folded into
        # "Back Matter" on the HTML page: one extra row each (first page only)
        for num, t, page in centries:
            if not re.fullmatch(r"[A-H]", num) or not page or len(t) < 8:
                continue
            if t.startswith(".") or re.search(r"(\b\w ){4,}", t):   # section line or spaced-letter artefact
                continue
            if any(match_contents(e["title"], [(num, t, page)])[0] for e in entries if e["kind"] == "chapter"):
                continue
            inside = False                      # a page inside a chapter's range is a wrapped author line
            for e in entries:
                r = re.fullmatch(r"(\d+)-(\d+)", e.get("pages", "")) if e["kind"] == "chapter" else None
                if r and int(r.group(1)) <= int(page) <= int(r.group(2)):
                    inside = True
            if inside:
                continue
            rows.append([bid, edition, isbn, num, "Appendix " + num + ": " + t,
                         f"starts p. {page} (front-matter Contents; inside Back Matter online)", bfm_url])
    return rows


# ---------------------------------------------------------------------------
# Cambridge Core
# ---------------------------------------------------------------------------
def cup_fetch(raw: str, bid: str, url: str, cookie: str) -> None:
    p1 = os.path.join(raw, f"{bid}_cup_p1.html")
    fetch(url, p1, cookie)
    s = open(p1, encoding="utf-8").read()
    n = max([1] + [int(x) for x in re.findall(r'href="\?pageNum=(\d+)"', s)])
    for k in range(2, n + 1):
        fetch(f"{url}?pageNum={k}", os.path.join(raw, f"{bid}_cup_p{k}.html"), cookie)


def rows_cup(raw: str) -> list[list[str]]:
    rows = []
    for bid, (url, edition) in CUP.items():
        files = sorted(f for f in os.listdir(raw) if re.fullmatch(rf"{bid}_cup_p\d+\.html", f))
        isbn = ""
        for f in files:
            s = open(os.path.join(raw, f), encoding="utf-8").read()
            if not isbn:
                isbns = re.findall(r'<meta name="citation_isbn"\s+content="(\d+)"', s)
                isbn = "/".join(isbns)
            for m in re.finditer(r'<a href="(/core/books/[^"]+)" class="part-link">\s*(.*?)\s*<div class="pages right">([^<]+)</div>',
                                 s, re.S):
                title = clean(m.group(2))
                mm = re.match(r"^(\d+|[IVX]+)\s+-\s+(.*)$", title)
                num, t = (mm.group(1), mm.group(2)) if mm else ("", title)
                pages = m.group(3).replace("pp", "").strip()
                rows.append([bid, edition, isbn, num, t, pages,
                             f"{url} ; chapter: https://www.cambridge.org{m.group(1)}"])
    return rows


# ---------------------------------------------------------------------------
# Crossref helpers
# ---------------------------------------------------------------------------
def crossref_items(path: str) -> list[dict]:
    d = json.load(open(path, encoding="utf-8"))
    return d["message"]["items"]


def first_page(p: str | None) -> str:
    return (p or "").split("-")[0]


# ---------------------------------------------------------------------------
# Elsevier
# ---------------------------------------------------------------------------
def elsevier_shop_toc(path: str) -> list[tuple[str, str, str]]:
    """Returns (part, number, title) from the shop page TOC."""
    s = open(path, encoding="utf-8").read()
    i = s.find('id="tableOfContents"')
    j = s.find("Product details", i)
    seg = s[i:j]
    seg = re.sub(r"<(br|/li|/p|/div|/h\d)[^>]*>", "\n", seg)
    lines = [clean(x) for x in seg.split("\n")]
    out, part = [], ""
    for l in lines:
        if not l or l == "Table of contents":
            continue
        m = re.match(r"^(\d+)\.\s+(.*?)\.?$", l)
        if m:
            out.append((part, m.group(1), l[len(m.group(1)) + 1:].strip()))
        elif re.match(r"^(Part|PART)\b", l):
            part = l
    return out


def rows_elsevier(raw: str) -> list[list[str]]:
    rows = []
    for bid, (url, isbn, edition) in ELSEVIER.items():
        shop = os.path.join(raw, f"{bid}_elsevier.html")
        cr = os.path.join(raw, f"cr_isbn_{isbn}.json")
        cr_url = f"https://api.crossref.org/works?filter=isbn:{isbn}&rows=200"
        if os.path.exists(shop):
            for part, num, title in elsevier_shop_toc(shop):
                rows.append([bid, edition, isbn, num, title + (f"  [part: {part}]" if part else ""), "", url])
        if os.path.exists(cr):
            def pkey(it):
                fp = first_page(it.get("page"))
                return (1, int(fp)) if fp.isdigit() else (0, 0)
            for it in sorted(crossref_items(cr), key=pkey):
                if it.get("type") != "book-chapter":
                    continue
                rows.append([bid, edition, isbn, "", clean((it.get("title") or [""])[0]),
                             it.get("page", ""), f"{cr_url} ; doi: https://doi.org/{it['DOI']}"])
    return rows


# ---------------------------------------------------------------------------
# OUP (Crossref only)
# ---------------------------------------------------------------------------
def rows_oup(raw: str) -> list[list[str]]:
    rows = []
    for bid, (q, isbn, edition) in OUP.items():
        cr = os.path.join(raw, f"cr_{bid}_oup.json")
        if not os.path.exists(cr):
            continue
        items = [it for it in crossref_items(cr) if isbn in it["DOI"] and it.get("page")]
        items.sort(key=lambda it: (0 if ".002." in it["DOI"] else 1 if ".003." in it["DOI"] else 2,
                                   int(re.sub(r"\D", "", first_page(it.get("page"))) or 0)
                                   if first_page(it.get("page")).isdigit() else -1))
        for it in items:
            rows.append([bid, edition, isbn, "", clean((it.get("title") or [""])[0]), it.get("page", ""),
                         f"{q} ; doi: https://doi.org/{it['DOI']}"])
    return rows


# ---------------------------------------------------------------------------
# Wiley
# ---------------------------------------------------------------------------
def rows_wiley(raw: str) -> list[list[str]]:
    rows = []
    for bid, (q, pdf_url, isbn, edition) in WILEY.items():
        cr = os.path.join(raw, f"cr_{bid}_wiley.json")
        if not os.path.exists(cr):
            continue
        txt = pdf_text(os.path.join(raw, f"{bid}_contents.pdf"))
        centries = contents_entries(txt) if txt else []
        items = [it for it in crossref_items(cr) if it.get("page")]

        def key(it):
            fp = first_page(it.get("page"))
            return int(fp) if fp.isdigit() else -1
        for it in sorted(items, key=key):
            fp = first_page(it.get("page"))
            is_part = ".part" in it["DOI"]
            title = clean((it.get("title") or [""])[0])
            num = "" if is_part else match_contents(title, centries)[0]
            rows.append([bid, edition, isbn, num, ("Part: " if is_part else "") + title, it.get("page", ""),
                         f"{q} ; doi: https://doi.org/{it['DOI']}" + (f" + {pdf_url}" if num else "")])
    return rows


# ---------------------------------------------------------------------------
def do_fetch(raw: str) -> None:
    cookie = os.path.join(raw, "cookies.txt")
    for bid, (suffix, _) in SPRINGER.items():
        springer_fetch(raw, bid, suffix, cookie)
    for bid, (url, _) in CUP.items():
        cup_fetch(raw, bid, url, cookie)
    for bid, (url, isbn, _) in ELSEVIER.items():
        fetch(url, os.path.join(raw, f"{bid}_elsevier.html"), cookie)
        fetch(f"https://api.crossref.org/works?filter=isbn:{isbn}&rows=200",
              os.path.join(raw, f"cr_isbn_{isbn}.json"), cookie, is_json=True)
    for bid, (q, _, _) in OUP.items():
        fetch(q, os.path.join(raw, f"cr_{bid}_oup.json"), cookie, is_json=True)
    for bid, (q, pdf_url, _, _) in WILEY.items():
        fetch(q, os.path.join(raw, f"cr_{bid}_wiley.json"), cookie, is_json=True)
        fetch(pdf_url, os.path.join(raw, f"{bid}_contents.pdf"), cookie)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", required=True, help="cache directory for raw pages (outside the repository)")
    ap.add_argument("--out", required=True, help="output TSV path")
    ap.add_argument("--fetch", action="store_true", help="download the pages before parsing")
    a = ap.parse_args()
    os.makedirs(a.raw_dir, exist_ok=True)
    if a.fetch:
        do_fetch(a.raw_dir)
    rows = rows_oup(a.raw_dir) + rows_cup(a.raw_dir) + rows_elsevier(a.raw_dir) + \
        rows_springer(a.raw_dir) + rows_wiley(a.raw_dir)
    order = {f"B{n:02d}": n for n in range(1, 16)}
    rows.sort(key=lambda r: order.get(r[0], 99))  # stable: keeps page order within a book
    with open(a.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["book_id", "edition", "isbn", "chapter_number", "chapter_title", "pages", "source_url"])
        w.writerows(rows)
    sys.stderr.write(f"wrote {len(rows)} rows to {a.out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
