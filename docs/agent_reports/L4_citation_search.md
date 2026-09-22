# L4 - Citation-graph search for reflection electron holography (P01, P02, P02E, P03, P08, P09)

Prepared: 2026-09-22 (session with Full network access). Status: COMPLETE for this session (written incrementally).
Script: `tools/lit/citation_lists.py`. Table: `docs/agent_reports/L4_citing_works.tsv`.
Raw API cache (bibliographic metadata only): `docs/agent_reports/citation_cache/`.

Evidence labels: METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE,
UNVERIFIED, as in the project instruction file. "SECTION_READ (abstract only)" means that the abstract was
read in an API record or on a publisher page whose URL is given; no full text is implied.

## 0. Access conditions of this session

Reachable and used (HTTP 200 on 2026-09-22): `api.openalex.org`, `api.semanticscholar.org`,
`api.crossref.org`, `opencitations.net` (the COCI v1 URL
`https://opencitations.net/index/coci/api/v1/citations/<doi>` answers HTTP 308 and redirects to
`https://api.opencitations.net/index/v1/citations/<doi>`; the script follows the redirect), and
`export.arxiv.org`. No proxy denial was met for these hosts.

## 1. Seed records, verified on Crossref

The DOIs were taken from `docs/references.bib` (keys P01, P02, P02E, P03, P08, P09) and each was resolved at
`https://api.crossref.org/works/<DOI>`. All six resolve, and author list, title, journal, volume and year
match the bib entry in each case. Label: METADATA_VERIFIED (Crossref), 2026-09-22.

| ID | DOI (as in references.bib) | Crossref record read (title; authors; container; vol(issue); page; issued; type) | Differences from references.bib |
|---|---|---|---|
| P01 | 10.1143/JJAP.27.L1772 | "Observation of Atomic Steps by Reflection Electron Holography"; Osakabe, Nobuyuki; Matsuda, Tsuyoshi; Endo, Junji; Tonomura, Akira; Japanese Journal of Applied Physics; 27(9A); page "L1772"; 1988-09-01; journal-article | Crossref gives the first page only ("L1772"), so the L prefix is confirmed; the end page L1774 is not in Crossref (still instruction-file only). Issue 9A is new. |
| P02 | 10.1103/PhysRevLett.62.2969 | "Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography"; Osakabe, Endo, Matsuda, Tonomura, Fukuhara; Physical Review Letters; 62(25); 2969-2972; 1989-06-19; journal-article | Issue 25 is new; pages 2969-2972 confirmed. |
| P02E | 10.1103/PhysRevLett.63.584.3 | "Observation of Surface Undulation Due to Single-Atomic Shear of a Dislocation by Reflection-Electron Holography"; same five authors; Physical Review Letters; 63(5); 584-584; 1989-07-31; journal-article | The author list, previously reconstructed from P02, is now confirmed by Crossref. Crossref does not carry the word "Erratum" in the title and has no `relation`/`update-to` link to P02. What the erratum corrects is still unknown. |
| P03 | 10.1016/0304-3991(93)90123-F | "Reflection electron holography"; Banzhof, H.; Herrmann, K.-H.; Ultramicroscopy; 48(4); 475-481; 1993-04; journal-article | The DOI, which had only search-summariser provenance, is now METADATA_VERIFIED (Crossref); issue 4 and April 1993 are new. |
| P08 | 10.1002/jemt.1070200415 | "Observation of surfaces by reflection electron holography"; Osakabe, Nobuyuki; Microscopy Research and Technique; 20(4); 457-462; 1992-02-15; journal-article | Crossref's container title is "Microscopy Research and Technique". This is Crossref's current journal title, not the 1992 masthead, so the old/new name question stays UNVERIFIED. |
| P09 | 10.1002/jemt.1070200414 | "Reflection electron microscopy and interferometry of atomic steps on gold and platinum single crystal surfaces"; Banzhof, H.; Herrmann, K. H.; Lichte, H.; Microscopy Research and Technique; 20(4); 450-456; 1992-02-15; journal-article | This settles the 450-456 versus 450-466 conflict in favour of 450-456. |

Crossref `is-referenced-by-count` on 2026-09-22 (Crossref's own count; it is not used as a citing list here):
P01 22, P02 40, P02E 0, P03 10, P08 7, P09 9.

## 2. Citation-graph retrieval (task 1): method and per-database coverage

### 2.1 What was run

`python3 tools/lit/citation_lists.py fetch` then `python3 tools/lit/citation_lists.py build --list`
(2026-09-22). Every count in this report is printed by one of the script's subcommands: `build` for
sections 2-3 and 5.1, `search` and `chain` for section 4, `oa` for section 6. REPRODUCED: rerunning
`build` offline from the cache reprints the section 2-3 numbers. Endpoints:

* OpenAlex: `https://api.openalex.org/works/doi:<DOI>` (seed record) and
  `https://api.openalex.org/works?filter=cites:<W id>` (citing list).
* Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/DOI:<DOI>` and `.../citations`.
* OpenCitations COCI: `https://opencitations.net/index/coci/api/v1/citations/<DOI>` (redirected to
  `api.opencitations.net/index/v1/...`).
* Crossref `https://api.crossref.org/works/<DOI>` for the seed records (its `is-referenced-by-count`).

**OpenAlex list endpoint refused (finding about access, not about the literature).** Every
`filter=cites:` request returned HTTP 429. The server message, recorded verbatim in
`citation_cache/openalex/<seed>_cites_STATUS.json`, said the request "has no API key, so it counts
against the free daily budget shared by everyone on your network's IP address, and that budget is used up
($0 remaining; resets at midnight UTC)". Single-record lookups (`/works/<id>`) carry
`x-ratelimit-cost-usd: 0` and still worked. The script therefore made a **reverse check**. Each citing work
that S2 or COCI returned with a DOI (60 DOIs, printed by `fetch`) was looked up as a single OpenAlex
record. `build` now reports 69 lookups because it also scans the 9 records added by `chain` (section 4.4);
none of those 9 references a seed, so the counts below are unchanged. The OpenAlex
citation link was counted (code `OAref`) when the seed's OpenAlex id appears in that record's
`referenced_works`. This cannot discover works that only OpenAlex knows. The script measures that gap as
OpenAlex `cited_by_count` minus the links it confirmed. **The gap is 0 for every seed** (table below).
The confirmed links are a subset of OpenAlex's citing set, and their number equals `cited_by_count`, so
they are that whole set as of 2026-09-22. DERIVED_HERE, from the printed counts; it assumes that
`cited_by_count` is consistent with `referenced_works`, which OpenAlex does not guarantee for every
record. To rerun the list endpoint itself, set a free personal `OPENALEX_API_KEY` or rerun after 00:00
UTC. **Request from Ali:** an OpenAlex API key only if a direct `cites:` confirmation is wanted; it is not
needed for the conclusions below.

### 2.2 Seed identifiers and database citation counts (printed by `build`)

| Seed | OpenAlex id | OpenAlex cited_by_count | S2 paperId (short) | S2 citationCount | Crossref is-referenced-by-count |
|---|---|---|---|---|---|
| P01 | W2054923936 | 22 | 1238381a... | 14 | 22 |
| P02 | W1990705543 | 42 | 6813b2f6... | 33 | 40 |
| P02E | W3033879513 | 0 | ac2a4a7d... | 0 | 0 |
| P03 | W2001540499 | 10 | 231c14ae... | 1 | 10 |
| P08 | W1989898237 | 8 | dace843b... | 4 | 7 |
| P09 | W2163735975 | 10 | ec957447... | 3 | 9 |

### 2.3 Citing links returned per database and after merging (printed by `build`)

Raw list lengths returned by the endpoints, before any merging: S2 14 / 33 / 0 / 1 / 4 / 3 and COCI
22 / 40 / 0 / 10 / 8 / 10 for P01 / P02 / P02E / P03 / P08 / P09. After merging and the one
hand-verified alias (section 3):

| Seed | OpenAlex `cites:` list | OAref (reverse check) | S2 | COCI | Union (unique records) | Only S2 | Only COCI | In both S2 and COCI | OpenAlex count minus OAref |
|---|---|---|---|---|---|---|---|---|---|
| P01 | NOT RETRIEVED (429) | 22 | 13 | 22 | 22 | 0 | 0 | 13 | 0 |
| P02 | NOT RETRIEVED (429) | 42 | 31 | 40 | 42 | 0 | 0 | 29 | 0 |
| P02E | NOT RETRIEVED (429) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P03 | NOT RETRIEVED (429) | 10 | 1 | 10 | 10 | 0 | 0 | 1 | 0 |
| P08 | NOT RETRIEVED (429) | 8 | 4 | 8 | 8 | 0 | 0 | 4 | 0 |
| P09 | NOT RETRIEVED (429) | 10 | 3 | 10 | 10 | 0 | 0 | 3 | 0 |

Overall: **60 unique citing records** (all with a DOI). **58 cite at least one of P01/P02/P02E/P03**; 2
cite only P08 and/or P09. Links by source: OAref 60 records, S2 39, COCI 58. The difference between raw S2
lengths and merged S2 counts has two causes:
* S2 holds Jiang et al., "The interaction of a screw dislocation with a circular inhomogeneity near the
  free surface" (DOI 10.1007/s00419-013-0803-0), twice: paperIds 7f8372e4... (year 2014) and c065aeda...
  (year 2013), same DOI (read in `citation_cache/s2/P02_citations_p1.json`).
* S2 paperId 14e6f2104493e79f551116629ddba47588119abd, which cites P01 and P02: year 2004, no DOI, authors
  "H. Banzhof, K. Herrmann, H. Lichte", title "Reflection Electron Steps on Gold and Microscopy and
  Interferometry of Atomic Platinum Single Crystal Surfaces". These are P09's authors and the words of P09's
  title reordered. Inference (DERIVED_HERE): a title-scrambled S2 duplicate of P09 (1992), not a 2004 work.
  It is merged into P09 through the hand-verified `ALIASES` table in the script. Before the merge it was the
  only link that S2 alone supplied.

Coverage findings (DERIVED_HERE, from the counts):
* **Semantic Scholar is the weakest source for this 1988-1993 cluster.** It has 13 of 22 links for P01,
  31 of 42 for P02, 1 of 10 for P03, 4 of 8 for P08 and 3 of 10 for P09. It contributes no unique real
  work, and it adds one duplicate record and one scrambled record.
* **OpenAlex is the most complete source.** Every link found anywhere is also in OpenAlex
  (`referenced_works`), and OpenAlex's `cited_by_count` equals the union for every seed. COCI misses 2 of
  P02's 42: Komoda 1996 (10.1016/s1076-5670(08)70063-6) and Tonomura 1998 Physica Scripta
  (10.1238/physica.topical.076a00016), both found by OAref and S2 only.
* **P02E has no citing work in any of the four databases.** OpenAlex, S2 and Crossref list it as a
  separate record with count 0. The erratum is invisible in citation graphs, so any use of P02 numbers
  must still be checked against it by reading it.
* **Same-content duplicates.** The DOI-or-title+year rule leaves 7 title groups with more than one DOI.
  Crossref records read for each DOI (`https://api.crossref.org/works/<DOI>`):
  - Same content under two DOIs: Wiley *Handbook of Microscopy* vs *Handbook of Microscopy Set* ("Reflection
    Electron Microscopy", pp. 407-424, both DOIs; "Electron Holography Methods", pp. 515-536, both DOIs).
  - Same content, pages differ by one: Hawkes-Kasper *Principles of Electron Optics* "Notes and References",
    1994 (ISBN 9780123333544, pp. 1775-1899) vs 1996 (ISBN 9780123333407, pp. 1775-1900).
  - Genuinely different works that share a title: Tonomura, "Electron-Holographic Interferometry", book
    chapter in two editions (1993 and 1999); Dunin-Borkowski, RSC chapter in 2007 and 2015 editions;
    Tonomura 1998 in *Physica Scripta* T76 vs *Nucl. Instrum. Methods A* 403; Komoda 1996, two sections
    with different page ranges (685-722 and 653-657); *Principles of Electron Optics* 2nd edition (2022).
  The collapsed count is given in section 3.

## 3. Classification of the citing works (task 2)

### 3.1 Rules used (ASSUMPTION: my operational definitions of the orchestrator's classes)

* **REH-experiment**: the record reports a measurement made by interfering electron waves reflected from
  a surface (reflection electron holography or interferometry, biprism-based).
* **REH-method/theory**: method, simulation or proposal for reflection holography or interferometry,
  with no reflection measurement in the text read.
* **REM/RHEED imaging**: REM, RHEED, REELS or RHEED-based analysis without holography, including reviews
  of REM.
* **transmission holography**: electron holography or interferometry confined to transmission (original
  work or reviews limited to transmission).
* **review/history**: reviews, textbooks, handbook chapters and histories covering electron holography in
  general, and the bibliography ("Notes and References") sections of textbooks.
* **reflection ptychography**: any ptychography in reflection. None of the citing works falls here.
* **other**: everything else (STM, continuum mechanics, optical digital holography, LEED holography,
  X-ray, surface microscopy surveys).

Evidence per row (TSV `evidence` column) takes one of two forms:
* `SECTION_READ (abstract only) <URL>`: the abstract was read in the OpenAlex, Crossref or S2 API record at
  that URL. For five Wiley handbook chapters the "abstract" is the list of section titles.
* `UNVERIFIED classification (title only)`: no abstract exists in any of the three API records, and the
  publisher pages were not readable. ScienceDirect returned HTTP 403 to WebFetch for
  `https://www.sciencedirect.com/science/article/pii/030439919390123F` and `.../030439919390124G`.
  Springer (`link.springer.com/chapter/...`) redirected to `idp.springer.com` and then served a
  JavaScript "Client Challenge" page, which was not bypassed.
  Europe PMC holds none of the 15 Elsevier/Wiley/Springer DOIs queried.

### 3.2 Counts (printed by `build`)

60 TSV rows: the DOI / title+year rule yields 61 records, and the scrambled S2 duplicate of P09 is merged
into P09 by a documented alias (section 2.3). 58 rows cite at least one of P01/P02/P02E/P03, and 2 cite only P08 and/or P09.
Counting the 3 same-content DOI pairs once gives **57 distinct works (55 citing P01/P02/P02E/P03)**.
32 rows were classified from an abstract and 28 from the title only.

| Class | All rows | Citing P01/P02/P02E/P03 | Citing only P08/P09 | Distinct works | Rows published after 1993 |
|---|---|---|---|---|---|
| REH-experiment | 7 | 6 | 1 | 7 | 2 |
| REH-method/theory | 4 | 4 | 0 | 4 | 1 |
| REM/RHEED imaging | 13 | 12 | 1 | 12 | 6 |
| transmission holography | 8 | 8 | 0 | 7 | 6 |
| review/history | 18 | 18 | 0 | 17 | 12 |
| reflection ptychography | 0 | 0 | 0 | 0 | 0 |
| other | 10 | 10 | 0 | 10 | 5 |

Citing works by year (all | citing P01/P02/P02E/P03): 1988-1993 28 | 28; 1994-1999 19 | 18;
2000-2009 5 | 4; 2010-2019 6 | 6; 2020-2026 2 | 2.

### 3.3 The REH rows

| Year | Work (DOI) | Class | Evidence | Cites (databases) |
|---|---|---|---|---|
| 1989 | Osakabe et al., Proc. EMSA, "Observation of surface morphology by reflection electron holography" (10.1017/s0424820100154652) | REH-method/theory | SECTION_READ (abstract only), Crossref record | P01 |
| 1989 | P02 (10.1103/physrevlett.62.2969) | REH-experiment | SECTION_READ (abstract only), OpenAlex W1990705543 | P01 |
| 1991 | Tanji et al., Ultramicroscopy, "Contrast simulation of high resolution electron holography on surface structures" (10.1016/0304-3991(91)90076-i) | REH-method/theory | UNVERIFIED (title only); the title does not state reflection | P02 |
| 1992 | P08 (10.1002/jemt.1070200415) | REH-experiment | SECTION_READ (abstract only), Crossref record | P01, P02 |
| 1992 | P09 (10.1002/jemt.1070200414) | REH-experiment | SECTION_READ (abstract only), Crossref record | P01, P02 (OAref, S2 and COCI for the DOI record; the scrambled S2 alias adds nothing new) |
| 1993 | Osakabe et al., Surf. Sci., "Application of electron holography to surface topography observation" (10.1016/0039-6028(93)90047-n) | REH-experiment | UNVERIFIED (title only) | P01, P02 |
| 1993 | Osakabe et al., Ultramicroscopy, "Reflection electron holographic observation of surface displacement field" (10.1016/0304-3991(93)90124-g) | REH-experiment | UNVERIFIED (title only) | P01, P02, P08 |
| 1993 | P03 (10.1016/0304-3991(93)90123-f) | REH-method/theory | UNVERIFIED (title only) | P01 |
| **1995** | Herring, Proc. MSA, "Reflection diffracted beam interferometry (RDBI) applied to the study of surfaces" (10.1017/s0424820100136957) | REH-method/theory | SECTION_READ (abstract only), `https://api.crossref.org/works/10.1017/s0424820100136957` | P02 |
| **2001** | Suzuki, Tanishiro, Ishiguro, Minoda, Yagi, Jpn. J. Appl. Phys. 40(4R), 2527, "Energy-filtered Electron Interferometry in Reflection Electron Microscopy" (10.1143/jjap.40.2527) | REH-experiment | SECTION_READ (abstract only), `https://api.crossref.org/works/10.1143/jjap.40.2527` | P08, P09 only |
| **2003** | Tanishiro, Hyomen Kagaku 24(3), 166-173, "Electron Energy Loss Spectroscopy in REM-RHEED: Energy Filtering by Omega-type Energy Filter" (10.1380/jsssj.24.166) | REH-experiment | SECTION_READ (abstract, English figure captions and reference list of the J-STAGE PDF; section 5.1) | P02 |

Quotations from abstracts read (verbatim):
* Herring 1995 (Crossref record): "So far, DBI has been applied only to transmission electron diffraction,
  although there is no reason why it shouldn't be applicable to all electron diffraction methods including
  reflection high (low) energy electron diffraction, RH(L)EED and, possibly, back-scattered electron
  diffraction, BSED, in the SEM for the study of surfaces." The abstract text in the record stops there. It
  does not show whether a reflection interferogram was recorded, hence REH-method/theory. The title
  ("applied to the study of surfaces") suggests more; the 2-page proceedings paper is needed (**request
  from Ali**: R. Herring, Proc. MSA 1995, DOI 10.1017/s0424820100136957). It is a UVic-relevant precedent.
* Suzuki et al. 2001 (Crossref record): "We studied energy-filtered interferometry in reflection electron
  microscopy (REM) geometry for the first time. An ultra-high vacuum electron microscope (UHV-EM) equipped
  with a field emission gun (FEG), a Möllenstedt-type electron biprism and an omega-type energy-filter was
  used. The specimen was a well-defined Si(111) 7×7 clean surface." Also: "The lateral coherent length of
  the electrons exciting the surface plasmon once is narrower (about 45 nm) than that of the no-plasmon-loss
  electrons (about 90 nm)."
* Tanishiro 2003 (OpenAlex W1994085323, identical on J-STAGE): "Energy filtering of reflection electron
  microscopy, diffraction and holography (REM, RHEED and REH) on clean silicon surfaces has been performed
  by using an omega-type energy filter built into a high-resolution UHV electron microscope with a field
  emission gun." ... "By removing plasmon-loss electrons, background intensity in RHEED has been lowered and
  contrast of REM images and holograms has been improved."

## 4. Topic searches (task 3): queries, engines, hit counts

Run with `python3 tools/lit/citation_lists.py search` (queries in `SEARCHES`, results cached in
`citation_cache/search/q<NN>_<topic>_<engine>.json|.xml`). Engines and syntax:
* OpenAlex `filter=title_and_abstract.search:`. **All 5 OpenAlex queries were NOT RUN**: HTTP 429, the
  same exhausted shared budget as in section 2.1.
* S2 `/paper/search/bulk`: title and abstract match; quotes mark phrases, `+` is AND, `|` is OR, `*` is a
  prefix wildcard.
* S2 `/paper/search`: relevance ranking, fuzzy; its total is not a phrase count.
* Europe PMC REST `TITLE:`/`ABSTRACT:` fields.
* arXiv API `abs:` field. Python's urllib got HTTP 406 from `export.arxiv.org` here while curl got HTTP
  200 with the same headers, so the script fetches arXiv through curl.
* Crossref `query.bibliographic`: relevance ranking with any-term matching, so its `total-results` is not a
  hit count and only the top 100 were inspected.

Hit counts are the engine's reported total (S2 `total`, Europe PMC `hitCount`, arXiv
`opensearch:totalResults`) as printed by the script on 2026-09-22.

### 4.1 Topic A: reflection electron holography (any year; post-1993 items picked by hand)

| q | Engine | Query | Hits |
|---|---|---|---|
| q01 | OpenAlex | `"reflection electron holography"` | NOT RUN (429) |
| q02 | OpenAlex | `"electron holography" "reflection electron microscopy"` | NOT RUN (429) |
| q03 | OpenAlex | `"electron holography" RHEED` | NOT RUN (429) |
| q04 | S2 bulk | `"reflection electron holography"` | 11 |
| q05 | S2 bulk | `"reflection electron holographic"` | 1 |
| q06 | S2 bulk | `"electron holography" + "reflection electron microscopy"` | 6 |
| q07 | S2 bulk | `"electron holography" + (RHEED \| "reflection high energy electron")` | 4 |
| q08 | S2 bulk | `"electron holography" + reflection + surface + step` | 6 |
| q09 | S2 relevance | `reflection electron holography surface step phase` | NOT RUN (S2 429 after 8 retries) |
| q10 | Europe PMC | `TITLE/ABSTRACT:"reflection electron holography"` | 2 |
| q11 | Europe PMC | `ABSTRACT:"electron holography" AND ABSTRACT:"reflection"` | 28 |
| q12 | Crossref | `reflection electron holography` | top 100 inspected |
| q13 | Crossref | `reflection electron holography surface steps` | top 100 inspected |
| q14 | arXiv | `abs:"reflection electron holography"` | 0 |
| q15 | arXiv | `abs:"electron holography" AND abs:reflection AND abs:surface` | 0 |
| q42 | S2 bulk | `"electron interferometry" + "reflection electron microscopy"` | 1 |
| q43 | S2 bulk | `biprism + ("reflection electron microscopy" \| RHEED \| "reflection high energy electron")` | 4 |
| q44 | S2 bulk | `"reflection electron" + hologra*` | 23 |
| q45 | Europe PMC | `ABSTRACT:"biprism" AND (ABSTRACT:"reflection electron microscopy" OR ABSTRACT:"RHEED")` | 1 |
| q46 | arXiv | `abs:biprism AND abs:reflection` | 1 (unrelated: 3-D monotile) |
| q47 | Crossref | `reflection electron microscopy interferometry biprism` | top 100 inspected |

What topic A added beyond the citing lists (abstracts read in the OpenAlex single record or the Crossref
record, 2026-09-22):
* **Takeguchi, Harada and Shimizu, "Observation of GaAs(110) Surface Defect by Reflection Electron
  Holography", J. Electron Microsc. (Aug. 1990), DOI 10.1093/oxfordjournals.jmicro.a050815.** From q04,
  q08, q44 and Crossref q12. The Crossref record has no authors, volume or pages; the authors come from
  OpenAlex W1954243266. Abstract (OpenAlex): "Reflection electron holography was successfully performed for
  observation of GaAs(110) surface defect. The phase distribution of object and/or conjugate wave reflected
  from the surface was reconstructed numerically to reveal how the monoatomic step is gradually converted
  into the concentrated strain field near the dislocation core." Class REH-experiment, pre-1993. It shows a
  **second group (Takeguchi, Harada, Shimizu)** doing REH in 1990. It is not in any seed's citing list:
  OpenAlex has cited_by_count 2, and Crossref deposits no reference list for it.
* **Tanishiro, Okamoto, Takeguchi, Minoda, Suzuki, Yagi, "Design features of a new ultra-high vacuum electron
  microscope with an omega filter", J. Electron Microsc. 48(6), 837-842 (1999), DOI
  10.1093/oxfordjournals.jmicro.a023755.** Found in Tanishiro 2003's reference list (ref. 9) and resolved by
  Crossref full match. This is the instrument paper: "energy-filtered diffraction patterns and images in
  transmission and reflection electron microscopy for well defined surfaces". Class: instrument; no
  holography in the abstract.
* **Tanishiro et al., "Image Conservation in Inelastically Scattered Electrons in Reflection Electron
  Microscopy", Jpn. J. Appl. Phys. 38(11R), 6540 (1999), DOI 10.1143/jjap.38.6540** (ref. 10 of Tanishiro
  2003; Crossref spells one author "Mimoda"). Energy-filtered REM of Si(111)7×7 and Si(111)5×2-Au. Class
  REM/RHEED imaging; no holography.
* Gajdardziska-Josifovska, Frost, Völkl, Allard, Proc. MSA 54, 366-367 (1996), DOI
  10.1017/s0424820100164295. MgO(111) faceting studied by "a combination of optical microscopy, transmission
  electron microscopy, and electron holography". The abstract does not state the holography geometry;
  inference (DERIVED_HERE): transmission. Not REH evidence.
* Rosenauer et al., Ultramicroscopy 88(1), 51-61 (2001), DOI 10.1016/s0304-3991(00)00115-7, "Compositional
  analysis based on electron holography and a chemically sensitive reflection". No abstract in any API
  record. From the title alone, "reflection" means a Bragg reflection in transmission, i.e. a dark-field
  holography analogue, not REH (UNVERIFIED classification).
* Everything else returned by topic A was already in the citing set, or was unrelated. Europe PMC q11
  returned mostly microwave-absorber papers, which match "reflection" (microwave reflection loss).

### 4.2 Topic B: electron ptychography in reflection geometry

| q | Engine | Query | Hits |
|---|---|---|---|
| q16 | OpenAlex | `"electron ptychography" reflection` | NOT RUN (429) |
| q17 | S2 bulk | `"electron ptychography" + reflection` | 5 |
| q18 | S2 bulk | `ptychography + (RHEED \| "reflection high energy electron")` | **0** |
| q19 | S2 bulk | `ptychography + "reflection electron microscopy"` | **0** |
| q20 | S2 bulk | `ptychography + electron + "grazing incidence"` | 3 |
| q21 | S2 bulk | `ptychography + ("backscattered electron" \| "backscattered electrons")` | **0** |
| q22 | S2 bulk | `ptychography + "scanning electron microscope" + reflection` | 2 |
| q23 | S2 relevance | `reflection electron ptychography` | 48270 (fuzzy; top 100 inspected) |
| q24 | Europe PMC | `ABSTRACT:"ptychography" AND ABSTRACT:"electron" AND ABSTRACT:"reflection"` | 2 |
| q25 | arXiv | `abs:ptychography AND abs:electron AND abs:reflection` | 7 |
| q26 | arXiv | `abs:ptychography AND abs:RHEED` | **0** |
| q27 | arXiv | `abs:ptychography AND abs:"electron" AND abs:"grazing"` | 1 |
| q48 | S2 bulk | `ptychograph* + ("low energy electron" \| LEEM \| LEED)` | 5 |
| q49 | S2 bulk | `ptychograph* + electron + (reflected \| reflection) + surface` | 8 |
| q50 | S2 bulk | `"4D-STEM" + (reflection \| RHEED \| "grazing incidence")` | 13 |
| q51 | Europe PMC | `ABSTRACT:"ptychography" AND (ABSTRACT:"RHEED" OR ABSTRACT:"reflection electron microscopy" OR ABSTRACT:"grazing incidence")` | 1 (on rerun: de Beurs et al. 2022, aPIE, visible/EUV) |
| q52 | arXiv | `abs:ptychography AND abs:"low energy electron"` | 0 |
| q53 | Crossref | `reflection electron ptychography` | top 100 inspected |

Every electron-ptychography hit whose abstract was read is **transmission**. Abstracts read in the OpenAlex
single records:
* Humphry et al., Nat. Commun. 3, 730 (2012), 10.1038/ncomms1733: "sub-atomic scale transmission imaging".
* Wang, Liu, Rodenburg, Microscopy 64(2), 105-110 (2015), 10.1093/jmicro/dfu109: 30 keV, SEM used "as a
  transmission electron microscopy".
* Blackburn, Cordoba, Fitzpatrick, McLeod, Nat. Commun. 16, 8977 (2025), 10.1038/s41467-025-64133-3: "a
  20 keV SEM operated in transmission mode".
* Blackburn, Fitzpatrick, Cordoba, Microsc. Microanal. 28(S1), 430-432 (2022), 10.1017/S1431927622002422:
  low-energy electron ptychography. The abstract in the record is only the author line, so the geometry was
  not read.
* Shpiro et al., CLEO/Europe 2025, 10.1109/cleo/europe-eqec65582.2025.11110191, "Near-Field Electron
  Ptychography of Metasurfaces". The abstract read covers only the metasurface motivation and no geometry;
  UNVERIFIED.
The remaining hits of q17, q20, q22, q23 (top 100), q25, q27, q48, q49 and q50 were judged **from their
titles only** (UNVERIFIED, abstracts not read). Titles indicate X-ray, EUV or visible ptychography,
transmission electron ptychography or 4D-STEM ("reflection" there meaning a Bragg reflection), or unrelated
work. No title indicates electron ptychography in a reflection geometry.

### 4.3 Topic C: X-ray, EUV and visible reflection-mode and Bragg-surface ptychography

| q | Engine | Query | Hits |
|---|---|---|---|
| q28 | OpenAlex | `"reflection ptychography"` | NOT RUN (429) |
| q29 | S2 bulk | `"reflection ptychography"` | 14 |
| q30 | S2 bulk | `ptychography + "reflection geometry"` | 13 |
| q31 | S2 bulk | `"reflective ptychography"` | 8 |
| q32 | S2 bulk | `"grazing incidence ptychography"` | 1 |
| q33 | S2 bulk | `"Bragg ptychography"` | 50 |
| q34 | S2 bulk | `ptychography + "crystal truncation rod"` | 2 |
| q35 | S2 bulk | `ptychography + ("extreme ultraviolet" \| EUV) + reflection` | 34 |
| q36 | S2 bulk | `"ptychographic reflectometry"` | 1 |
| q37 | Europe PMC | `ABSTRACT:"ptychography" AND ABSTRACT:"reflection geometry"` | 1 |
| q38 | arXiv | `abs:ptychography AND abs:"reflection geometry"` | 6 |
| q39 | arXiv | `abs:"Bragg ptychography"` | 2 |
| q40 | arXiv | `abs:ptychography AND abs:"grazing incidence"` | 2 |
| q41 | arXiv | `abs:ptychography AND abs:"crystal truncation rod"` | 0 |

Confirmation of the docs/02 analogues. Crossref record read at `https://api.crossref.org/works/<DOI>`;
abstract read in the OpenAlex single record unless marked otherwise.

| docs/02 item | DOI | Crossref (METADATA_VERIFIED) | Abstract read | Confirms docs/02? |
|---|---|---|---|---|
| Zhu et al. 2015 (P36) | 10.1063/1.4914927 | Appl. Phys. Lett. 106(10), 101604 (2015-03-09) | yes: "ptychography can be used to image atomic step structures using coherent diffraction patterns recorded along the crystal truncation rod"; Pt(111) proof of concept | yes |
| Godard et al. 2011 (P35) | 10.1038/ncomms1569 | Nat. Commun. 2(1), 568 (2011-11-29) | no abstract in OpenAlex/Crossref | identity only |
| Hruszkewycz et al. 2017 (P37) | 10.1038/nmat4798 | Nat. Mater. 16(2), 244-251, issued 2016-11-21 (online) | no abstract in OpenAlex/Crossref | identity only; the bib year 2017 is the print year |
| Jørgensen et al. 2024 (P38) | 10.1364/optica.505478 | Optica 11(2), 197 (2024-02-01) | yes: combines "imaging, reflectometry, and grazing-incidence small angle scattering"; "surface profile sensitivity better than 1 nm normal to the surface" | yes |
| Myint et al. 2024 (P39) | 10.1063/5.0204240 | APL Photonics 9(6), 066118 (2024-06-01) | yes: merges ptychography of extended objects "with the high-resolution depth profiling capabilities of x-ray reflectivity" | yes |
| Guenzing et al. 2026 (P40) | 10.1364/OE.591755 | Opt. Express 34(16), 30230 (2026-08-04) | yes: "reflection geometry soft X-ray ptychography as a robust imaging mode"; "ca. 45 nm" full-pitch resolution | yes |

New topic C items that bear on the project's forward-model warning (instruction C03, multiplicative object
in reflection):
* **Senhorst, Witte, Coene, "2D approximation quickly breaks down in reflection ptychography", Opt. Express
  34(12), 22163 (2026-06-08), DOI 10.1364/oe.601179.** Abstract (OpenAlex W7162459012, read): "Ptychographic
  reconstructions in reflection geometries are commonly interpreted with the same two-dimensional
  thin-sample model used in transmission, yet the validity of this approximation has not been established."
  ... "reflection geometries impose far stricter thin-sample conditions than transmission geometries. The
  allowable thickness is reduced by one to two orders of magnitude for a representative extreme ultraviolet
  geometry" ... "incorporating the correct depth-dependent propagation into the forward model resolves these
  distortions". It is a weak-scattering (single-scattering) 3-D theory for light. Inference (DERIVED_HERE):
  the failure of the 2-D multiplicative model in reflection is now published even for weak scattering, which
  strengthens the case for a dynamical electron forward model; it does not address dynamical electron
  scattering itself.
* Seaberg et al., Optica 1(1), 39 (2014), DOI 10.1364/optica.1.000039: "the first (to our knowledge) general
  purpose full-field reflection-mode extreme ultraviolet (EUV) microscope based on coherent diffractive
  imaging", ptychography "combined with tilted plane correction".
* Senhorst et al., Opt. Express 32(25), 44017 (2024-11-18), DOI 10.1364/oe.542569: tilted propagation
  included in the forward model, with tilt angles optimised by automatic differentiation. The first Crossref
  request got HTTP 429; the `oa` run then retrieved the record.
* de Beurs et al., Opt. Lett. 47(8), 1949 (2022), DOI 10.1364/ol.453655 (aPIE, tilt estimation in
  reflection ptychography). Shao et al., Light Sci. Appl. 13, 196 (2024), DOI 10.1038/s41377-024-01558-3
  (EUV reflection ptychography of wafers). Zhang et al., Ultramicroscopy 158, 98-104 (2015), DOI
  10.1016/j.ultramic.2015.07.006: reflection-mode EUV ptychography, "surface profilometry with ultra-high,
  6 Å axial resolution".
* Lu et al., Ultramicroscopy 249, 113720 (2023), DOI 10.1016/j.ultramic.2023.113720, and Chen et al., Light
  Adv. Manuf. 7 (2026), DOI 10.37188/lam.2026.112: identity only, no abstract in the records.

### 4.4 Topic A, forward chaining from the later REH papers

`python3 tools/lit/citation_lists.py chain` collects the works citing seven REH and reflection-interferometry
papers found above (`CHAIN_SEEDS`). Sources: S2 citations, COCI, and the OpenAlex single-record reverse
check. Printed counts (OpenAlex cited_by_count / S2 / COCI / union):
Osakabe 1989 EMSA 0/0/0/0; Takeguchi 1990 JEM 2/1/0/1; Osakabe 1993 Surf. Sci. 0/0/0/0; Osakabe 1993
Ultramicroscopy 10/3/10/10; Herring 1995 0/0/0/0; Suzuki 2001 JJAP 3/3/3/3; Tanishiro 2003 Hyomen Kagaku
6/4/6/6. The union is **20 records, 9 of them not already in the P01-P09 citing set**. Abstracts of the 9
new records were read in their OpenAlex single records (`https://api.openalex.org/works/<W id>`):
* Carr et al. 2008 (Stud. Conserv., vegetable textile fibres; cites Takeguchi 1990, apparently in error):
  other.
* Nakahara et al. 2003, Hyomen Kagaku 24, 159 (10.1380/jsssj.24.159): energy-filtered RHEED and EELS of
  Si(111)7×7; REM/RHEED, no holography.
* Five reflection high-energy positron diffraction papers by Fukaya et al., 2009-2018 (10.1103/physrevb.79.193310,
  10.1380/ejssnt.2010.190, 10.1088/1742-6596/225/1/012009, 10.1088/1742-6596/443/1/012068,
  10.1088/1361-6463/aadf14): positron diffraction; other.
* Horio 2022 (10.1380/ejssnt.2022-013): energy-filtered RHEED plasmon loss on Si(111)7×7; REM/RHEED.
* Yagi 2002, "Spectro-microscopy by TEM-SEM" (10.1007/3-540-45850-6_2): no abstract, title only
  (UNVERIFIED); a review chapter.
**None is a reflection electron holography or interferometry paper.** Osakabe 1989 EMSA, Osakabe 1993 Surf.
Sci. and Herring 1995 have no citing work in any of the three databases.

### 4.5 Search failures to record

* OpenAlex: q01-q03, q16 and q28 were not run (HTTP 429, shared budget exhausted; resets 00:00 UTC).
* S2 relevance search q09: HTTP 429 on all 8 retries, in two separate runs. The S2 bulk endpoint worked
  throughout.
* Europe PMC q51: the first response carried no `hitCount`. The cache file was deleted and the query
  rerun, giving 1 hit.
* Publisher pages: ScienceDirect HTTP 403; Springer JavaScript challenge; IOPscience served a "Search" or
  bot-check page instead of the article; APS Cloudflare challenge; Cambridge Core HTTP 400 (for
  `https://www.cambridge.org/core/product/identifier/S0424820100136957/type/journal_article`); Google
  Patents HTTP 503 (for US 10,755,892 B2, the reflection-mode electron ptychography patent of B section 5.2,
  which therefore remains UNVERIFIED). J-STAGE worked.

## 5. Answers

### 5.1 (a) Has reflection electron holography been performed or developed after 1993, by whom, on what surfaces, at what energies?

**Answer: yes, at least by one group, the Yagi/Tanishiro group at Tokyo Institute of Technology, in
2001-2003, on clean Si(111)7×7.** Their work concerns interferometry, energy filtering and coherence rather
than surface-height measurement. No later reflection-holography measurement was found in the databases and
queries listed. The evidence splits into three levels.

**Found and read (abstract, or abstract plus PDF captions):**
1. **Suzuki, Tanishiro, Ishiguro, Minoda, Yagi, Jpn. J. Appl. Phys. 40(4R), 2527 (2001), DOI
   10.1143/jjap.40.2527** (SECTION_READ, abstract only, Crossref record). Stated in the abstract:
   * "energy-filtered interferometry in reflection electron microscopy (REM) geometry for the first time";
   * UHV-EM with FEG, "a Möllenstedt-type electron biprism and an omega-type energy-filter";
   * specimen "a well-defined Si(111) 7×7 clean surface";
   * carrier-fringe visibility higher for no-loss electrons; carrier fringes also visible for one and two
     surface-plasmon losses;
   * lateral coherence length about 45 nm (one plasmon) versus about 90 nm (no loss).
   The energy is not stated in the abstract. The databases show it citing P08 and P09 but not P01-P03.
2. **Tanishiro, Hyomen Kagaku 24(3), 166-173 (2003), DOI 10.1380/jsssj.24.166** (Japanese article, English
   abstract). SECTION_READ of the abstract (OpenAlex and J-STAGE), of the English figure captions and of the
   reference list in the J-STAGE PDF
   (`https://www.jstage.jst.go.jp/article/jsssj/24/3/24_3_166/_pdf/-char/en`). Verbatim from the captions:
   * Fig. 1: "An energy-filtered, no-plasmon-loss RHEED pattern from Si(111) 7×7 surface".
   * Fig. 4: "Reflection electron holograms produced by overlapping of two REM images using an electron
     biprism. (a) Unfiltered, (b) no-plasmon-loss, (c) single-plasmon-loss." "Visibility of the carrier
     fringes was greatly improved by energy filtering in (b)."
   * Fig. 5: "A series of energy-filtered reflection electron holograms taken with 2 eV wide energy
     filtering slit."
   All four quotations have their spacing and ligatures normalised. The extracted text reads, for example,
   "As e r i e so fe n ergy-ﬁltered reﬂection elect ron holograms". Fig. 1 continues "... at 750" followed
   by an undecodable temperature unit.
   The reference list cites P02 (ref. 15) and Suzuki et al. 2001 (ref. 11).
   **Energy:** the Japanese body text could not be decoded from the PDF's embedded fonts, but the numerals
   are legible. "200 kV" appears after the same garbled token that also precedes "10 kV" in a RHEED
   context, and "200 keV+ΔE" appears in the energy-filter description. Inference (UNVERIFIED): the
   instrument was operated at 200 kV. The instrument itself is described in Tanishiro et al., J. Electron
   Microsc. 48(6), 837-842 (1999) (abstract read; no energy stated).
   Inference (DERIVED_HERE) from the Fig. 4 caption: the Tokyo Tech holograms interfered **two regions of the
   same REM image**, i.e. both waves reflected from the surface. That differs from the vacuum-reference
   arrangement attributed (UNVERIFIED) to the Hitachi patent PAT01.
3. **Herring, Proc. MSA 53, 116-117 (1995), DOI 10.1017/s0424820100136957** (SECTION_READ, abstract only):
   proposes extending biprism diffracted-beam interferometry to RHEED/RLEED/BSED. The abstract text read
   does not show a recorded reflection interferogram, so it is classed as development (method), not
   performance.
4. Before 1994, for context: a second group, **Takeguchi, Harada, Shimizu, J. Electron Microsc. (1990), DOI
   10.1093/oxfordjournals.jmicro.a050815**, performed REH on GaAs(110) with numerical reconstruction
   (abstract read). Osakabe's own 1993 papers (Ultramicroscopy 48, 483-488; Surf. Sci. 298, 345-350) are
   title-only.

**Found, not read (title only):** Tanji, Ito, Yada, Ultramicroscopy 35, 245-253 (1991): contrast simulation
of high-resolution holography of surface structures, geometry unknown. Yagi 2002, "Spectro-microscopy by
TEM-SEM" (a chapter citing Suzuki 2001). The book and review chapters (Tonomura 1994, 1995, 1999;
Dunin-Borkowski 2019; Hawkes-Kasper 2022) may describe REH, but only as reviews.

**Not found**, with the databases and queries searched:
* No reflection-electron-holography or reflection-interferometry measurement published after 2003.
* No post-1993 REH work on Si(001) or on ion-milled surfaces. The only surfaces named in the post-1993 REH
  abstracts and captions read are clean Si(111)7×7 (and "clean silicon surfaces"), and the only energy
  information is the inferred 200 kV.
Searched:
* all works citing P01, P02, P02E, P03, P08 and P09 in OpenAlex (complete via the reverse check), Semantic
  Scholar and COCI;
* the citing works of the 7 later REH papers (section 4.4);
* S2 bulk q04-q08 and q42-q44, Europe PMC q10, q11 and q45, arXiv q14, q15 and q46, and the Crossref top
  100 of q12, q13 and q47.
Not searched: OpenAlex full-text search (429), Scopus and Web of Science (no access), and Japanese-language
databases (CiNii, J-STAGE full-text search). The last are the most likely home of further work by the Tokyo
Tech group. **Recommended next step:** a J-STAGE/CiNii search for 反射電子ホログラフィー (reflection electron
holography), plus the author names Tanishiro, Minoda, Suzuki and Yagi.

The citing record after 2003 contains **9 rows, and none is REH** (printed by `build`). By class:
* review/history 3: Dunin-Borkowski 2019, Harada 2020 (P07), Hawkes-Kasper notes 2022;
* transmission holography 2: Dunin-Borkowski 2007 and 2015;
* REM/RHEED 1: Cowley 2015 encyclopedia entry;
* other 3: Jiang 2013, Zhang 2015, Lee 2019.

### 5.2 (b) Does peer-reviewed electron reflection-mode ptychography exist?

**Answer: none was found.** State it only with the scope below.

* **Found and read (abstracts): only transmission electron ptychography.** Humphry et al. 2012; Wang, Liu,
  Rodenburg 2015; Blackburn et al. 2025 ("a 20 keV SEM operated in transmission mode"). Also a large
  literature of **X-ray, EUV and visible reflection ptychography**, including the six docs/02 analogues (4
  confirmed at abstract level, 2 at identity level) and Senhorst et al. 2026, which shows the 2-D
  (multiplicative) model breaking down in reflection.
* **Found, not read:** Blackburn et al. 2022 (low-energy electron ptychography; the record shows only the
  author line), and Shpiro et al. 2025 ("Near-Field Electron Ptychography of Metasurfaces"; the abstract read
  does not state the geometry). The reflection-mode electron-beam ptychography patent US 10,755,892 is not
  peer reviewed, and Google Patents returned 503.
* **Not found**, in these databases and queries:
  - S2 bulk, which returned **zero hits** for `ptychography + (RHEED | "reflection high energy
    electron")` (q18), `ptychography + "reflection electron microscopy"` (q19) and
    `ptychography + ("backscattered electron" | "backscattered electrons")` (q21), and hits that were
    not reflection electron ptychography for q17, q20, q22 and q48-q50;
  - the S2 relevance top 100 of q23;
  - Europe PMC q24 (2 hits, both EUV) and q51 (1 hit, aPIE);
  - arXiv q25-q27 and q52 (q26 `ptychography AND RHEED`: 0);
  - the Crossref top 100 of q53.
  Not searched: OpenAlex (429), Scopus, Web of Science, Google Scholar, and conference abstracts outside S2
  and Crossref (e.g. the Microscopy and Microanalysis supplements are only partly indexed).

## 6. Open-access status and candidate new references (task 5)

`python3 tools/lit/citation_lists.py oa <DOIs>` reads the OpenAlex single record
(`https://api.openalex.org/works/doi:<DOI>?select=...open_access,best_oa_location`) and the Crossref record
(`https://api.crossref.org/works/<DOI>`), and caches both under `citation_cache/oa/`. OpenAlex OA status is
a database claim; whether the URL served the paper to this environment was tested separately and is
stated.

### 6.1 Seed papers

| ID | OpenAlex oa_status | best_oa_location / oa_url | Tested from here |
|---|---|---|---|
| P01 | bronze | https://iopscience.iop.org/article/10.1143/JJAP.27.L1772/pdf | HTTP 200, but the body is an HTML page titled "Search", not the PDF. **Request from Ali: download P01 in a browser (free per OpenAlex).** |
| P02 | closed | none | not tested (paywalled; request from Ali) |
| P02E | bronze | http://link.aps.org/pdf/10.1103/PhysRevLett.63.584.3 | HTTP 403 with a Cloudflare "Just a moment..." page. **Request from Ali: download P02E in a browser (free per OpenAlex, one page).** |
| P03 | closed | none | ScienceDirect PII page HTTP 403 to WebFetch (request from Ali) |
| P08 | closed | none | not tested (request from Ali) |
| P09 | closed | none | not tested (request from Ali) |

### 6.2 Candidate references recommended for `references.bib`

Every DOI below was returned by an API (Crossref, OpenAlex, S2 or COCI) and resolved at
`https://api.crossref.org/works/<DOI>` on 2026-09-22. None was pattern-completed. The metadata fields are
copied from the Crossref record (METADATA_VERIFIED) except where stated. None is in `references.bib` at
present (grep on the DOI, 2026-09-22).

**Tier 1: post-1988 reflection electron holography and interferometry (the primary record for question (a)).**

| Key suggestion | Crossref metadata (verbatim fields) | DOI | OpenAlex OA | Evidence for content |
|---|---|---|---|---|
| SUZUKI2001 | Suzuki, Takayuki; Tanishiro, Yasumasa; Ishiguro, Nami; Minoda, Hiroki; Yagi, Katsumichi. "Energy-filtered Electron Interferometry in Reflection Electron Microscopy". Japanese Journal of Applied Physics 40(4R), 2527; issued 2001-04-01 | 10.1143/jjap.40.2527 | bronze, https://iopscience.iop.org/article/10.1143/JJAP.40.2527/pdf (the WebFetch of the article page got a bot-check/search page) | SECTION_READ (abstract only), Crossref record |
| TANISHIRO2003 | TANISHIRO, Yasumasa. "Electron Energy Loss Spectroscopy in REM-RHEED: Energy Filtering by Omega-type Energy Filter." Hyomen Kagaku 24(3), 166-173; 2003 (Japanese title also in the record) | 10.1380/jsssj.24.166 | diamond, cc-by-nc, https://www.jstage.jst.go.jp/article/jsssj/24/3/24_3_166/_pdf (downloaded) | SECTION_READ: abstract, English figure captions and reference list of the PDF (section 5.1) |
| TAKEGUCHI1990 | Crossref: title "Observation of GaAs(110) Surface Defect by Reflection Electron Holography", Journal of Electron Microscopy, issued 1990-08; **no authors, volume or pages in Crossref**. Authors from OpenAlex W1954243266: Masaki Takeguchi, Ken Harada, Ryuichi Shimizu | 10.1093/oxfordjournals.jmicro.a050815 | closed | SECTION_READ (abstract only), OpenAlex record. Volume and pages still UNVERIFIED (read them on the OUP page) |
| OSAKABE1993UM | Osakabe, N.; Matsuda, T.; Endo, J.; Tonomura, A. "Reflection electron holographic observation of surface displacement field". Ultramicroscopy 48(4), 483-488; 1993-04 (same issue as P03, 475-481) | 10.1016/0304-3991(93)90124-g | closed | title only |
| OSAKABE1993SS | Osakabe, Nobuyuki. "Application of electron holography to surface topography observation". Surface Science 298(2-3), 345-350; 1993-12 (same volume as P28, Cowley, 336-344) | 10.1016/0039-6028(93)90047-n | closed | title only |
| OSAKABE1989EMSA | Osakabe, N.; Endo, J.; Matsuda, T.; Tonomura, A. "Observation of surface morphology by reflection electron holography". Proceedings, annual meeting, Electron Microscopy Society of America 47, 536-537; 1989-08-06 | 10.1017/s0424820100154652 | closed | SECTION_READ (abstract only), Crossref record |
| HERRING1995 | Herring, Rodney A. "Reflection diffracted beam interferometry (RDBI) applied to the study of surfaces". Proceedings, annual meeting, Electron Microscopy Society of America 53, 116-117; 1995-08-13 | 10.1017/s0424820100136957 | closed | SECTION_READ (abstract only), Crossref record |
| TANJI1991 (check before citing) | Tanji, T.; Ito, J.; Yada, K. "Contrast simulation of high resolution electron holography on surface structures". Ultramicroscopy 35(3-4), 245-253; 1991-06 | 10.1016/0304-3991(91)90076-i | closed | title only; the geometry (reflection or profile) is unknown |

**Tier 2: instrument and REM context for the Tokyo Tech REH work.**

| Key suggestion | Crossref metadata | DOI | OpenAlex OA |
|---|---|---|---|
| TANISHIRO1999JEM | Tanishiro, Y.; Okamoto, K.; Takeguchi, M.; Minoda, H.; Suzuki, T.; Yagi, K. "Design features of a new ultra-high vacuum electron microscope with an omega filter". Journal of Electron Microscopy 48(6), 837-842; issued 1999-01-01 (Crossref date) | 10.1093/oxfordjournals.jmicro.a023755 | closed |
| TANISHIRO1999JJAP | Tanishiro, Yasumasa; Okamoto, Kimiharu; Suzuki, Takayuki; Ishiguro, Nami; "Mimoda" [sic in Crossref; "Minoda" in Tanishiro 2003 ref. 10], Hiroki; Miura, Hidetoshi; Yagi, Katsumichi; Takeguchi, Masaki. "Image Conservation in Inelastically Scattered Electrons in Reflection Electron Microscopy". Japanese Journal of Applied Physics 38(11R), 6540; 1999-11-01 | 10.1143/jjap.38.6540 | bronze, https://iopscience.iop.org/article/10.1143/JJAP.38.6540/pdf |
| WANG1993RPP | Wang, Z L. "Electron reflection, diffraction and imaging of bulk crystal surfaces in TEM and STEM". Reports on Progress in Physics 56(8), 997-1065; 1993-08-01 | 10.1088/0034-4885/56/8/002 | closed |
| YAGI1993SSR | Yagi, Katsumichi. "Reflection electron microscopy: studies of surface structures and surface dynamic processes". Surface Science Reports 17(6), 307-362; 1993-01 | 10.1016/0167-5729(93)90002-7 | closed |

Note on YAGI1993SSR: Tanishiro 2003's reference list (PDF, ref. 1) reads "K. Yagi: Surf. Sci. Rep. 19, 305
(1993)", which differs from Crossref (volume 17, pages 307-362). It is not established that these are the
same article. Use the Crossref record for this DOI and check the Tanishiro citation separately.

**Tier 3: reflection-ptychography forward-model literature (analogue, not electrons).**

| Key suggestion | Crossref metadata | DOI | OpenAlex OA |
|---|---|---|---|
| SENHORST2026 | Senhorst, Sander; Witte, Stefan; Coene, Wim. "2D approximation quickly breaks down in reflection ptychography". Optics Express 34(12), 22163; 2026-06-08 | 10.1364/oe.601179 | gold, cc-by, https://doi.org/10.1364/oe.601179 |
| SENHORST2024 | Senhorst, Sander; Shao, Yifeng; Weerdenburg, Sven; Horsten, Roland; Porter, Christina; Coene, Wim. "Mitigating tilt-induced artifacts in reflection ptychography via optimization of the tilt angles". Optics Express 32(25), 44017; 2024-11-18 | 10.1364/oe.542569 | gold, cc-by, https://doi.org/10.1364/oe.542569 |
| SEABERG2014 | Seaberg, Matthew D.; Zhang, Bosheng; Gardner, Dennis F.; Shanblatt, Elisabeth R.; Murnane, Margaret M.; Kapteyn, Henry C.; Adams, Daniel E. "Tabletop nanometer extreme ultraviolet imaging in an extended reflection mode using coherent Fresnel ptychography". Optica 1(1), 39; 2014-07-22 | 10.1364/optica.1.000039 | gold, https://doi.org/10.1364/optica.1.000039 |
| BLACKBURN2025 | Blackburn, Arthur M.; Cordoba, Cristina; Fitzpatrick, Matthew R.; McLeod, Robert A. "Sub-ångström resolution ptychography in a scanning electron microscope at 20 keV". Nature Communications 16(1), article 8977; 2025-10-14 | 10.1038/s41467-025-64133-3 | gold, cc-by, https://www.nature.com/articles/s41467-025-64133-3.pdf |

BLACKBURN2025 is a transmission-mode SEM result (abstract read). It is listed because B_literature
section 5.2 cites it by title only without a DOI, and it is the University of Victoria authors' own
low-energy ptychography precedent.

Confirmed but already in the bib: P07 = Harada, Microscopy 70(1), 3-16, DOI 10.1093/jmicro/dfaa033
(Crossref: online 2020-06-26; OpenAlex OA "hybrid"). It is itself a citing work of P01 and P02 (TSV
row, review/history). P35 to P40 are in section 4.3.

## 7. Documents to request from Ali, open items, reproduction

Documents to request (none was readable from this environment):
1. **P01** (JJAP 27, L1772): free (bronze) per OpenAlex, but IOPscience served a non-article page here. A
   browser download should work.
2. **P02E** (PRL 63, 584): free (bronze) per OpenAlex; APS served a Cloudflare challenge. One page; it
   settles what the erratum corrects.
3. **Suzuki et al. 2001** (JJAP 40, 2527): free (bronze) per OpenAlex. Needed for the energy, glancing
   angle, reflection, biprism position and the reference-wave arrangement of the only post-1993 REH/REM
   interferometry paper found.
4. **P03**, **Osakabe et al. 1993 Ultramicroscopy 48, 483-488** and **Osakabe 1993 Surf. Sci. 298,
   345-350** (all Elsevier, closed; ScienceDirect HTTP 403). These are the last Osakabe/Banzhof REH papers,
   classified here from titles only.
5. **Herring 1995** (Proc. MSA 53, 116-117; Cambridge, closed): was a reflection interferogram recorded?
   It is a University of Victoria precedent.
6. **Takeguchi, Harada, Shimizu 1990** (J. Electron Microsc.; OUP, closed): volume and pages missing from
   Crossref.
7. Optional: a free personal **OpenAlex API key**, to rerun the `cites:` lists and the OpenAlex topic
   searches directly (`OPENALEX_API_KEY=... python3 tools/lit/citation_lists.py fetch --refresh`).

Open items:
* The Japanese-language literature (J-STAGE and CiNii full text) was not searched. It is the most likely
  place for further REH work by the Tokyo Tech group.
* 28 of 60 TSV classifications are title-only (UNVERIFIED). Of the REH rows, P03, both Osakabe 1993 papers
  and Tanji 1991 are title-only. None of them is after 1993, so the answer to (a) does not depend on them.
* Hand merges: the S2 alias (P09) and the 3 same-content DOI pairs are documented in the script (`ALIASES`,
  `SAME_CONTENT`) with the Crossref evidence.

Reproduction (from the repository root; standard library only, network needed except for `build`):

```
python3 tools/lit/citation_lists.py fetch        # citing lists -> docs/agent_reports/citation_cache/
python3 tools/lit/citation_lists.py build --list # merge, classify, write L4_citing_works.tsv, print counts
python3 tools/lit/citation_lists.py search --list
python3 tools/lit/citation_lists.py chain
python3 tools/lit/citation_lists.py oa <DOI ...>
python3 tools/lit/citation_lists.py abstracts --out <scratch dir>   # abstracts are never cached in the repo
```
