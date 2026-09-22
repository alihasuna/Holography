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
  python3 tools/lit/citation_lists.py chain      # works citing the later REH papers (topic A)
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
    'doi:10.1002/pssa.2211160113': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W1964912842?select=id,abstract_inverted_index; time-resolved REM of laser-induced surface processes; no holography'),
    'doi:10.1017/s0424820100154652': ('REH-method/theory',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1017/s0424820100154652; REH described as REM optics measuring the phase of reflected electrons; abstract text covers the sensitivity argument (geometrical path difference, ~0.01 A) but no specific measurement'),
    'doi:10.1103/physrevlett.62.2969': ('REH-experiment',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W1990705543?select=id,abstract_inverted_index; = P02; screw dislocation on GaAs(110) observed by measuring the phase of reflected electrons'),
    'doi:10.1557/proc-209-629': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1557/proc-209-629; REM and variants with forward-scattered high-energy electrons'),
    'doi:10.1103/physrevlett.65.1607': ('other',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2036111952?select=id,abstract_inverted_index; STM of a dislocation on Cu(111)'),
    'doi:10.2320/matertrans1989.31.551': ('review/history',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W1993895665?select=id,abstract_inverted_index; review of electron-holography applications (transmission set-up described; lists surface morphology among applications)'),
    'doi:10.1063/1.881230': ('review/history',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1063/1.881230; one-sentence abstract: holography with coherent field-emission beams (general article)'),
    'doi:10.1017/s0424820100086714': ('other',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1017/s0424820100086714; resolution limits of surface imaging; abstract discusses transmission and profile imaging, no holography'),
    'doi:10.1002/jemt.1070200415': ('REH-experiment',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1002/jemt.1070200415; = P08; phase of a Bragg-reflected wave measured with FEG + biprism; monoatomic-step phase and dislocation displacement field observed (whether the observations are new is not stated)'),
    'doi:10.1002/jemt.1070200414': ('REH-experiment',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1002/jemt.1070200414; = P09; biprism at the selected-area-diaphragm position; pi (Au(111)) and 0.9 pi (Pt(111)) step phases measured'),
    'doi:10.1080/00018739200101473': ('review/history',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W1992093684?select=id,abstract_inverted_index; review of electron-holographic interference microscopy, beams transmitted through or reflected from an object'),
    'doi:10.1557/proc-295-271': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1557/proc-295-271; RHEED, REM, SREM and REELS of oxide surfaces'),
    'doi:10.1017/s0424820100129322': ('transmission holography',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1017/s0424820100129322; low-voltage field-emission point-projection (in-line) interferograms in transmission'),
    'doi:10.1002/jemt.1070200409': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2119419090?select=id,abstract_inverted_index; review of REELS and REM in (S)TEM; phase-contrast REM with FEG, no holography'),
    'doi:10.1017/s0424820100150642': ('other',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1017/s0424820100150642; survey of SEM, glancing-incidence (S)TEM reflection modes and AFM for ceramic surfaces; no holography'),
    'doi:10.1088/0034-4885/56/8/002': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2021786678?select=id,abstract_inverted_index; review of REM/RHEED/REELS; lists electron holography among techniques used with REM'),
    'doi:10.1017/s0424820100136957': ('REH-method/theory',
        "SECTION_READ (abstract only) https://api.crossref.org/works/10.1017/s0424820100136957; diffracted-beam interferometry with a biprism; abstract states DBI 'has been applied only to transmission' and argues it should apply to RHEED/RLEED/BSED; no reflection measurement in the abstract text"),
    'doi:10.1002/9783527620647.ch15': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2218635183?select=id,abstract_inverted_index; handbook chapter; section titles only (RHEED patterns, step contrast, RHEED/REM theory)'),
    'doi:10.1002/9783527619283.ch15a': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W3143095438?select=id,abstract_inverted_index; same content as doi:10.1002/9783527620647.ch15 (Crossref pp. 407-424 for both); section titles only'),
    'doi:10.1002/9783527620647.ch21': ('transmission holography',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W4233407748?select=id,abstract_inverted_index; handbook chapter; section titles only (conventional TEM, off-axis image-plane holography)'),
    'doi:10.1002/9783527619283.ch21a': ('transmission holography',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2482034483?select=id,abstract_inverted_index; same content as doi:10.1002/9783527620647.ch21 (Crossref pp. 515-536 for both); section titles only'),
    'doi:10.1002/9783527614561.ch1': ('review/history',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W4211075259?select=id,abstract_inverted_index; handbook chapter; section titles only (TEM, REM, EELS, ..., electron holography methods)'),
    'doi:10.1238/physica.topical.076a00016': ('transmission holography',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2044893665?select=id,abstract_inverted_index; phase of a beam transmitted through an object; superconducting vortices'),
    'doi:10.1142/s0217979200002326': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1142/s0217979200002326; review: electron standing waves and X-ray emission under RHEED conditions; no holography'),
    'doi:10.1103/physrevlett.84.4389': ('REM/RHEED imaging',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2022894019?select=id,abstract_inverted_index; X-ray yields under RHEED surface-wave resonance, Si(111)-sqrt3-In; no holography'),
    'doi:10.1143/jjap.40.2527': ('REH-experiment',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1143/jjap.40.2527; energy-filtered electron interferometry in REM geometry, UHV-EM with FEG, Moellenstedt biprism and omega filter, Si(111) 7x7; carrier-fringe visibility and lateral coherence length (~45 nm one-plasmon, ~90 nm no-loss) measured'),
    'doi:10.1380/jsssj.24.166': ('REH-experiment',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W1994085323?select=id,abstract_inverted_index; energy filtering of REM, RHEED and REH on clean Si surfaces with an omega filter in a UHV FEG microscope; contrast of REM images and holograms improved'),
    'doi:10.1039/9781847557926-00138': ('transmission holography',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2344883807?select=id,abstract_inverted_index; review chapter; hologram formed in the TEM (abstract truncated in the record)'),
    'doi:10.1117/1.jmm.14.4.041304': ('other',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W1085130950?select=id,abstract_inverted_index; compression of optical digital holograms of wafer surfaces'),
    'doi:10.1039/9781782621867-00158': ('transmission holography',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1039/9781782621867-00158; review chapter on off-axis holography of thin samples in the TEM'),
    'doi:10.1021/acs.cgd.9b00339': ('other',
        'SECTION_READ (abstract only) https://api.openalex.org/works/W2969661582?select=id,abstract_inverted_index; elastic properties of cubic GaN in v-grooved Si(001); no holography'),
    'doi:10.1093/jmicro/dfaa033': ('review/history',
        'SECTION_READ (abstract only) https://api.crossref.org/works/10.1093/jmicro/dfaa033; review of the basics of electron holography and interferometry (special-issue introduction)'),
    'doi:10.1016/0039-6028(90)90669-y': ('REM/RHEED imaging',
        'UNVERIFIED classification (title only); title: magnetic contrast in REM'),
    'doi:10.1016/0304-3991(91)90076-i': ('REH-method/theory',
        'UNVERIFIED classification (title only); title: contrast simulation of high-resolution electron holography on surface structures; the title does not say whether the geometry is reflection or profile transmission'),
    'doi:10.1016/0304-3991(92)90195-p': ('other',
        'UNVERIFIED classification (title only); title: resolution limitation in the electron microscopy of surfaces (companion EMSA abstract doi:10.1017/s0424820100086714 read: transmission/profile imaging)'),
    'doi:10.1016/0039-6028(92)91219-2': ('other',
        'UNVERIFIED classification (title only); title: diffuse LEED pattern as a hologram (LEED direct methods, not off-axis electron holography)'),
    'doi:10.1016/0168-9002(92)90973-8': ('transmission holography',
        'UNVERIFIED classification (title only); title: electron holography and the Aharonov-Bohm effect'),
    'doi:10.1007/978-3-642-84482-9_4': ('review/history',
        'UNVERIFIED classification (title only); title: electron holography and its applications to surface observation (book chapter)'),
    'doi:10.1016/0039-6028(93)90047-n': ('REH-experiment',
        'UNVERIFIED classification (title only); title: application of electron holography to surface topography observation (Osakabe); the title does not state the geometry'),
    'doi:10.1007/978-3-662-13913-4_7': ('review/history',
        "UNVERIFIED classification (title only); title: book chapter 'Electron-Holographic Interferometry' (1993 edition)"),
    'doi:10.1016/0039-6028(93)90046-m': ('review/history',
        'UNVERIFIED classification (title only); title: electron holography and holographic diffraction for surface studies (Cowley); whether reflection holography is treated is not determinable'),
    'doi:10.1016/0304-3991(93)90124-g': ('REH-experiment',
        'UNVERIFIED classification (title only); title: reflection electron holographic observation of surface displacement field (Osakabe 1993)'),
    'doi:10.1016/0304-3991(93)90123-f': ('REH-method/theory',
        "UNVERIFIED classification (title only); = P03; title 'Reflection electron holography' only; whether it reports new measurements is unknown"),
    'doi:10.1016/0167-5729(93)90002-7': ('REM/RHEED imaging',
        'UNVERIFIED classification (title only); title: REM studies of surface structures and dynamic processes (review)'),
    'doi:10.1007/978-3-642-79232-8_1': ('review/history',
        'UNVERIFIED classification (title only); title: electron holography and its applications (book chapter)'),
    'doi:10.1016/b978-0-12-333354-4.50031-8': ('review/history',
        "UNVERIFIED classification (title only); bibliography section; Crossref container title 'Principles of Electron Optics' (1994)"),
    'doi:10.1016/0167-5729(94)90005-1': ('review/history',
        'UNVERIFIED classification (title only); title: recent advances in electron phase microscopy (review)'),
    'doi:10.1007/978-3-540-48995-5_8': ('REM/RHEED imaging',
        'UNVERIFIED classification (title only); title: energy-filtered reflection electron microscopy (book chapter)'),
    'doi:10.1111/j.1749-6632.1995.tb38969.x': ('review/history',
        'UNVERIFIED classification (title only); title: recent advances in electron interferometry'),
    'doi:10.1016/s1076-5670(08)70068-5': ('review/history',
        'UNVERIFIED classification (title only); title: electron microscopes and microscopy in Japan (history; Crossref pp. 685-722)'),
    'doi:10.1016/s1076-5670(08)70063-6': ('review/history',
        'UNVERIFIED classification (title only); title: electron microscopes and microscopy in Japan (history; Crossref pp. 653-657)'),
    'doi:10.1016/b978-012333340-7/50264-7': ('review/history',
        "UNVERIFIED classification (title only); bibliography section; Crossref container 'Principles of Electron Optics' (1996; same pages as the 1994 record +1)"),
    'doi:10.1007/978-3-662-14824-2_6': ('other',
        'UNVERIFIED classification (title only); title: scattering and phase contrast for amorphous specimens (TEM textbook chapter)'),
    'doi:10.1016/s0001-8686(97)90026-9': ('other',
        'UNVERIFIED classification (title only); title: possibility of measuring the spin polarization of electrons from the top atomic layer'),
    'doi:10.1016/s0168-9002(97)01067-x': ('transmission holography',
        'UNVERIFIED classification (title only); title: observation of quantized vortices in superconductors by electron waves (NIM A version)'),
    'doi:10.1007/978-3-540-37204-2_7': ('review/history',
        "UNVERIFIED classification (title only); title: book chapter 'Electron-Holographic Interferometry' (1999 edition)"),
    'doi:10.1007/s00419-013-0803-0': ('other',
        'UNVERIFIED classification (title only); title: continuum mechanics of a screw dislocation near a free surface'),
    'doi:10.1081/e-escs3-120028068': ('REM/RHEED imaging',
        "UNVERIFIED classification (title only); title: encyclopedia entry 'Electron Microscopy: Surface Diffraction'"),
    'doi:10.1007/978-3-030-00069-1_16': ('review/history',
        "UNVERIFIED classification (title only); title: handbook chapter 'Electron Holography'"),
    'doi:10.1016/b978-0-12-818979-5.00101-7': ('review/history',
        "UNVERIFIED classification (title only); bibliography section; Crossref container 'Principles of Electron Optics, Volume 3' (2022)"),
}

# Hand-verified aliases: records that the DOI / title+year rule cannot merge but that are the same
# work. Merged into the canonical key before the TSV is written.
#   S2 paperId 14e6f2104493e79f551116629ddba47588119abd: no DOI, year 2004, authors H. Banzhof,
#   K. Herrmann, H. Lichte, title "Reflection Electron Steps on Gold and Microscopy and
#   Interferometry of Atomic Platinum Single Crystal Surfaces" = P09's title words reordered.
ALIASES = {
    "ty:reflection electron steps on gold and microscopy and interferometry of atomic platinum "
    "single crystal surfaces|2004": "doi:10.1002/jemt.1070200414",
}

# Same content registered under two DOIs (Crossref: same title, same page range, same year; or
# pages differing by one for the Hawkes-Kasper printings). Kept as separate TSV rows (different
# DOIs) but counted once in the "distinct works" totals printed by `build`.
SAME_CONTENT = [
    ("doi:10.1002/9783527620647.ch15", "doi:10.1002/9783527619283.ch15a"),
    ("doi:10.1002/9783527620647.ch21", "doi:10.1002/9783527619283.ch21a"),
    ("doi:10.1016/b978-0-12-333354-4.50031-8", "doi:10.1016/b978-012333340-7/50264-7"),
]


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
    for alias, canon in ALIASES.items():                # 4) hand-verified aliases
        if alias in records and canon in records:
            a = records.pop(alias)
            for sd in SEEDS:
                records[canon]["cites"][sd] |= a["cites"][sd]
            records[canon]["found"] |= a["found"]
            records[canon].setdefault("aliases", []).append(alias)
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
    n_alias = sum(len(r.get("aliases", [])) for r in records.values())
    dup_keys = {b for a, b in SAME_CONTENT if a in records and b in records}
    print(f"\n== Unique citing records overall: {len(records)} after merging {n_alias} hand-verified "
          f"alias record(s)  (citing at least one of P01/P02/P02E/P03: {len(prim)};  citing only P08"
          f" and/or P09: {len(supp_only)})")
    print(f"   distinct works after counting {len(dup_keys)} same-content DOI pair(s) once: "
          f"{len(records) - len(dup_keys)}  (citing P01/P02/P02E/P03: "
          f"{len(prim) - sum(1 for r in prim if r['key'] in dup_keys)})")
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

    print("\n== Class counts over TSV rows (all | citing P01/P02/P02E/P03 | citing only P08/P09 |"
          " distinct works | rows published after 1993)")
    for c in CLASSES + ["UNCLASSIFIED"]:
        a = sum(1 for x in rows if x["class"] == c)
        b = sum(1 for x in rows if x["class"] == c and x["_key"] in prim_keys)
        d = a - sum(1 for x in rows if x["class"] == c and x["_key"] in dup_keys)
        e = sum(1 for x in rows if x["class"] == c and int(x["year"] or 0) > 1993)
        print(f"   {c:26s} {a:4d} {b:4d} {a - b:4d} {d:4d} {e:4d}")
    n_title = sum(1 for x in rows if x["evidence"].startswith("UNVERIFIED"))
    n_abs = sum(1 for x in rows if x["evidence"].startswith("SECTION_READ"))
    print(f"   classified from an abstract: {n_abs};  from the title only (UNVERIFIED): {n_title}")

    print("\n== Rows published after 2003, by class: " + ", ".join(
        f"{c}={sum(1 for x in rows if x['class'] == c and int(x['year'] or 0) > 2003)}"
        for c in CLASSES) + f"  (total {sum(1 for x in rows if int(x['year'] or 0) > 2003)})")
    for x in rows:
        if int(x["year"] or 0) > 2003:
            print(f"   {x['year']}  {x['class']:24s} {x['first_author']}  {x['title'][:70]}")

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


def http_post_json(url: str, payload: dict, tries: int = 8) -> tuple[int, bytes]:
    delay = 3.0
    for attempt in range(tries):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"User-Agent": USER_AGENT,
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            raise
    raise RuntimeError(f"POST failed after {tries} tries: {url}")


def cmd_abstracts(args) -> None:
    """Abstracts for manual classification, written (incrementally, resumable) to --out only."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jl = out / "abstracts.jsonl"
    done = set()
    if jl.exists():
        done = {json.loads(line)["key"] for line in jl.read_text().splitlines() if line.strip()}
    records, _, _, _ = build_records()
    todo = [r for r in records.values() if r["key"] not in done]
    # Semantic Scholar: one batch request for all records
    s2_abs = {}
    ids = [r.get("s2_id") or f"DOI:{r['doi']}" for r in todo if r.get("s2_id") or r["doi"]]
    if ids:
        url = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=abstract,externalIds"
        st, body = http_post_json(url, {"ids": ids})
        for i, rec in zip(ids, json.loads(body)):
            if rec and rec.get("abstract"):
                s2_abs[i] = (f"https://api.semanticscholar.org/graph/v1/paper/"
                             f"{rec.get('paperId')}?fields=abstract", rec["abstract"])
    with jl.open("a") as fh:
        for r in todo:
            entry = {"key": r["key"], "doi": r["doi"], "title": r["meta"].get("title"),
                     "year": r["meta"].get("year"), "venue": r["meta"].get("venue"),
                     "abstracts": []}
            if r.get("openalex_id"):
                url = (f"https://api.openalex.org/works/{r['openalex_id']}"
                       "?select=id,abstract_inverted_index")
                try:
                    st, body = http_get(url)
                    if st == 200:
                        a = oa_abstract(json.loads(body).get("abstract_inverted_index"))
                        if a:
                            entry["abstracts"].append({"url": url, "text": a})
                except RateLimited:
                    entry["abstracts"].append({"url": url, "text": None, "note": "429"})
            sid = r.get("s2_id") or (f"DOI:{r['doi']}" if r["doi"] else None)
            if sid in s2_abs:
                entry["abstracts"].append({"url": s2_abs[sid][0], "text": s2_abs[sid][1]})
            if r["doi"]:
                url = f"https://api.crossref.org/works/{doi_path(r['doi'])}"
                st, body = http_get(url)
                if st == 200:
                    a = json.loads(body)["message"].get("abstract")
                    if a:
                        entry["abstracts"].append({"url": url, "text": re.sub(
                            r"\s+", " ", re.sub(r"<[^>]+>", " ", a))})
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"{r['key'][:70]:70s} abstracts={len([a for a in entry['abstracts'] if a['text']])}",
                  flush=True)
    print(f"done; {jl}")


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
    # appended after the first run (indices of the queries above are fixed by the cache names)
    ("A", "s2-bulk", '"electron interferometry" + "reflection electron microscopy"'),
    ("A", "s2-bulk", 'biprism + ("reflection electron microscopy" | RHEED | "reflection high energy electron")'),
    ("A", "s2-bulk", '"reflection electron" + hologra*'),
    ("A", "europepmc", '(ABSTRACT:"biprism" AND (ABSTRACT:"reflection electron microscopy" OR ABSTRACT:"RHEED"))'),
    ("A", "arxiv", 'abs:biprism AND abs:reflection'),
    ("A", "crossref-query", "reflection electron microscopy interferometry biprism"),
    ("B", "s2-bulk", 'ptychograph* + ("low energy electron" | LEEM | LEED)'),
    ("B", "s2-bulk", 'ptychograph* + electron + (reflected | reflection) + surface'),
    ("B", "s2-bulk", '"4D-STEM" + (reflection | RHEED | "grazing incidence")'),
    ("B", "europepmc", '(ABSTRACT:"ptychography" AND (ABSTRACT:"RHEED" OR ABSTRACT:"reflection electron microscopy" OR ABSTRACT:"grazing incidence"))'),
    ("B", "arxiv", 'abs:ptychography AND abs:"low energy electron"'),
    ("B", "crossref-query", "reflection electron ptychography"),
]

# Forward chaining for topic A: works citing the post-1988 reflection-electron-holography /
# reflection-interferometry papers located by the citation lists and searches (their DOIs were
# returned by the APIs; see the report).
CHAIN_SEEDS = {
    "Osakabe1989EMSA": "10.1017/s0424820100154652",
    "Takeguchi1990JEM": "10.1093/oxfordjournals.jmicro.a050815",
    "Osakabe1993SS": "10.1016/0039-6028(93)90047-n",
    "Osakabe1993UM": "10.1016/0304-3991(93)90124-g",
    "Herring1995EMSA": "10.1017/s0424820100136957",
    "Suzuki2001JJAP": "10.1143/jjap.40.2527",
    "Tanishiro2003HK": "10.1380/jsssj.24.166",
}


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
            # export.arxiv.org answers HTTP 406 to Python's urllib in this environment (it
            # answers 200 to curl with the same headers), so arXiv is fetched with curl.
            import subprocess
            body = subprocess.run(["curl", "-sS", "-f", "-m", "90", "-A", USER_AGENT, url],
                                  check=True, capture_output=True).stdout
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
        try:
            r = run_search(i, topic, engine, query, args.refresh)
        except (RuntimeError, urllib.error.HTTPError) as e:   # e.g. S2 429 after all retries
            r = {"i": i, "topic": topic, "engine": engine, "query": query, "url": None,
                 "total": None, "items": [], "status": f"NOT RUN: {str(e)[-60:]}"}
        results.append(r)
        print(f"q{i:02d} [{topic}] {engine:24s} total={r['total']!s:>8s} returned={len(r['items']):4d}  "
              f"{query}   [{r['status']}]", flush=True)
    if args.list:
        for r in results:
            print(f"\n--- q{r['i']:02d} [{r['topic']}] {r['engine']} {r['query']}  (total {r['total']})")
            for it in sorted(r["items"], key=lambda x: str(x.get("year"))):
                print(f"   {it.get('year')} | {it.get('first_author')} | {it.get('title')} | "
                      f"{it.get('venue')} | {it.get('doi')}")


def cmd_chain(args) -> None:
    """Citing works (S2 + COCI + OpenAlex single-record reverse check) of CHAIN_SEEDS."""
    main_records, _, _, _ = build_records()
    known = set(main_records)
    union: dict[str, dict] = {}
    for name, doi in CHAIN_SEEDS.items():
        cdir = CACHE / "chain"
        oa = cached_json(cdir / f"{name}_openalex_seed.json",
                         f"https://api.openalex.org/works/doi:{doi_path(doi)}?select=id,cited_by_count",
                         False)
        wid = oa.get("id")
        s2 = cached_json(cdir / f"{name}_s2_citations.json",
                         f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi_path(doi)}/citations?"
                         + urllib.parse.urlencode({"fields": S2_CITATION_FIELDS, "limit": "1000"}),
                         False)
        time.sleep(1.1)
        co = cached_json(cdir / f"{name}_coci_citations.json",
                         f"https://opencitations.net/index/coci/api/v1/citations/{doi_path(doi)}", False)
        s2_items = [x["citingPaper"] for x in s2.get("data", []) if x.get("citingPaper")]
        coci = [clean_doi(r["citing"]) for r in co.get("_list", [])]
        links = {}
        for p in s2_items:
            m = s2_to_meta(p)
            k = "doi:" + m["doi"] if m["doi"] else "ty:" + norm_title(m["title"]) + "|" + str(m["year"])
            links.setdefault(k, {"meta": m, "src": set()})["src"].add("S2")
        for d in coci:
            links.setdefault("doi:" + d, {"meta": {"doi": d}, "src": set()})["src"].add("COCI")
        for k, v in links.items():
            if v["meta"].get("doi"):
                rec = openalex_single(v["meta"]["doi"])
                if rec.get("_http_status") != 404:
                    if wid and wid in (rec.get("referenced_works") or []):
                        v["src"].add("OAref")
                    if not v["meta"].get("title"):
                        v["meta"] = oa_to_meta(rec)
        print(f"\n--- {name} {doi}: OpenAlex cited_by_count={oa.get('cited_by_count')} "
              f"S2={len(s2_items)} COCI={len(coci)} union={len(links)}")
        for k, v in sorted(links.items(), key=lambda kv: str(kv[1]['meta'].get('year'))):
            m = v["meta"]
            flag = "" if k in known else "  [NEW: not in the P01-P09 citing set]"
            print(f"   {m.get('year')} | {m.get('first_author')} | {m.get('title')} | {m.get('venue')} | "
                  f"{m.get('doi')} | {'+'.join(sorted(v['src']))}{flag}")
            union.setdefault(k, v)
    new = [k for k in union if k not in known]
    print(f"\n== chain union: {len(union)} citing records; not in the P01-P09 citing set: {len(new)}")


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
    p = sub.add_parser("chain"); p.set_defaults(f=cmd_chain)
    args = ap.parse_args(argv)
    args.f(args)


if __name__ == "__main__":
    main()
