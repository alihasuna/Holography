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

