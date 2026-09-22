# L4 - Citation-graph search for reflection electron holography (P01, P02, P02E, P03, P08, P09)

Prepared: 2026-09-22 (session with Full network access). Status: IN PROGRESS (written incrementally).
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
(2026-09-22). Every number in sections 2 to 4 is printed by `build` (REPRODUCED: rerunning `build`
offline from the cache reprints them). Endpoints:

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
that S2 or COCI returned with a DOI (60 DOIs) was looked up as a single OpenAlex record. The OpenAlex
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

| Seed | OpenAlex `cites:` list | OAref (reverse check) | S2 list | COCI list | Union (unique records) | Only S2 | Only COCI | OpenAlex count minus OAref |
|---|---|---|---|---|---|---|---|---|
| P01 | NOT RETRIEVED (429) | 22 | 14 | 22 | 23 | 1 | 0 | 0 |
| P02 | NOT RETRIEVED (429) | 42 | 32 (33 raw) | 40 | 43 | 1 | 0 | 0 |
| P02E | NOT RETRIEVED (429) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P03 | NOT RETRIEVED (429) | 10 | 1 | 10 | 10 | 0 | 0 | 0 |
| P08 | NOT RETRIEVED (429) | 8 | 4 | 8 | 8 | 0 | 0 | 0 |
| P09 | NOT RETRIEVED (429) | 10 | 3 | 10 | 10 | 0 | 0 | 0 |

Overall: **61 unique records** (60 with DOI, 1 without). **59 cite at least one of P01/P02/P02E/P03**;
2 cite only P08 and/or P09. Links by source: OAref 60 records, S2 40, COCI 58. For P02 the S2 list has 33
raw entries but 32 after merging. S2 holds Jiang et al., "The interaction of a screw dislocation with a
circular inhomogeneity near the free surface" (DOI 10.1007/s00419-013-0803-0) twice, as paperIds
7f8372e4... (year 2014) and c065aeda... (year 2013), with the same DOI (read in
`citation_cache/s2/P02_citations_p1.json`).

Coverage findings (DERIVED_HERE, from the counts):
* **Semantic Scholar is the weakest source for this 1988-1993 cluster.** It has 1 of 10 links for P03,
  4 of 8 for P08 and 3 of 10 for P09. The only link S2 has that no other database has, for both P01 and
  P02, is S2 paperId 14e6f2104493e79f551116629ddba47588119abd: year 2004, no DOI, authors "H. Banzhof,
  K. Herrmann, H. Lichte", title "Reflection Electron Steps on Gold and Microscopy and Interferometry of
  Atomic Platinum Single Crystal Surfaces". Same three authors and the same words as P09's title, reordered.
  Inference (DERIVED_HERE): a title-scrambled S2 duplicate of P09 (1992), not a 2004 work. The script
  collapses it into P09 through a hand-verified alias table (section 3).
* **COCI and OpenAlex agree closely.** The union adds nothing beyond OpenAlex's own count for any seed.
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

