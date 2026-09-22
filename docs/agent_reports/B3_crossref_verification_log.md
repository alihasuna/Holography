# B3 -- Crossref / publisher verification log for `docs/references.bib`

Prepared: 2026-09-22 (reading plan `docs/07_reading_plan.md`, order of work, step 1). Network access:
Full (HTTPS proxy). The index-only record `B2_bib_verification_log.md` is kept unedited; this log
supersedes it for every field it covers.

Baseline: `docs/references.bib` at commit `4a9df525a7d33ad974293e0cac04f31e479fc816` (96 entries,
45 with a `doi` field, 18 in the UNVERIFIED section). Every count below is produced by
`tools/bib/crossref_check.py report`, which compares both the baseline and the current file with the
cached records.

## Reproduce

```
venv/bin/python tools/bib/crossref_check.py fetch      # network; cached responses are reused
venv/bin/python tools/bib/crossref_check.py apply      # baseline + tools/bib/b3_corrections.yaml -> references.bib
venv/bin/python tools/bib/crossref_check.py report     # TSV + generated block below + counts
venv/bin/python tools/bib/crossref_check.py validate   # syntax, unique keys, every doi backed by a cached record
```

Cached registry responses (Crossref, DataCite, arXiv; openly licensed metadata) are in
`docs/agent_reports/crossref_cache/`, with `_index.json` recording URL, HTTP status and fetch time of
every request. Publisher pages, patent pages and README files were kept in the session scratch
directory only (not committed). No e-mail address was sent; the User-Agent was
`Holography-bibcheck/1.0`.

## Method

1. Entries with a `doi`: `GET https://api.crossref.org/works/<DOI>`; compared authors or editors
   (count, order, family-name spelling and diacritics, consistency of given names -- initials or
   spelled-out first names), title (after case, punctuation and markup folding), container title,
   volume, issue, pages or article number, year (against published-print, published-online and issued;
   the per-entry record states which one the bib year equals) and, for books and chapters, publisher.
   A DOI that Crossref does not know (404) was sent to `doi.org/ra` and, for DataCite, to
   `api.datacite.org`.
2. Entries without a `doi`: `GET /works?query.bibliographic=<authors title journal volume year page>`
   (5 rows; plus `filter=isbn:` for books). A candidate DOI was accepted **only** if the candidate's
   first author, title (similarity >= 0.90 after folding), journal or publisher, year and volume all
   matched the BASELINE entry ("ACCEPT-5FIELD"); then `/works/<DOI>` was fetched and compared as in 1.
3. **Deviation from the five-field rule, flagged for the orchestrator.** Eleven entries lacked one or
   more of the five fields (mostly the quarantined ones, which had no author, year or volume, or a
   placeholder title). For these an identifier the entry ALREADY carried was allowed to stand in for the
   missing field(s), provided no tested field mismatched ("ACCEPT-SUBSTITUTED"): the ScienceDirect PII
   recorded in B2 / B_literature.md equals the record's PII (U01, U02, U08, U09, U10); the ISBN in the
   `isbn` field equals the record's ISBN (B03, B04); the chapter record carries the ISBNs of the
   verified parent book and its exact title (U07); the first page matches together with author,
   journal, volume and year (U04, HANADA95 -- placeholder titles; U16 -- no author). The verdict and all
   tested fields are listed per entry below. If the orchestrator wants the strict rule, these eleven
   (and their DOIs) are the ones to revert: move U01, U02, U04, U07, U08, U09, U10, U16 back and drop
   the doi fields of B03, B04, HANADA95.
4. Books without a Crossref record, software, patents and preprints were checked on the publisher page
   or registry (Elsevier shop page, DataCite, arXiv API, Google Patents, raw README, vendor page); the
   URL and HTTP status are recorded per entry. `github.com` and `api.github.com` return HTTP 403 for
   this session and `link.springer.com` serves a JavaScript challenge; neither was worked around.
5. Corrections are declared in `tools/bib/b3_corrections.yaml` and applied by the script: fields named
   `from_crossref` (including every added DOI) are copied from the cached record; `set` values are
   transcriptions named in the entry's note. Keys are unchanged. Accepted residual differences (kept on
   purpose) are listed per entry with the reason.
6. Labels: a successful match gives `METADATA_VERIFIED (route: ...)`; the previous label is kept in
   each note as "label before B3". Nothing in this pass was read, so nothing was raised to
   `SECTION_READ`; existing `SECTION_READ` labels (P04, READMEs) are kept as they were.

## Coordinator's three checks (message received during the pass)

1. **B09 editor first name.** Query <https://api.crossref.org/works/10.1007/978-1-4615-4817-1>
   (HTTP 200): the record lists "Edgar Völkl", "Lawrence F. Allard", "David C. Joy" (deposited in the
   author role). The C01 chapter record (<https://api.crossref.org/works/10.1007/978-1-4615-4817-1_6>)
   gives "E. Völkl", "M. Lehmann". **Confirmed: Edgar, not Ernst.** Corrected in B09 (editor), C01
   (author and editor) and U07 (editor). The comparator originally missed this because the initials
   agree; it now also compares spelled-out first names, and the rerun flags B09 and nothing else.
2. **B07 DOI.** Found independently by the bibliographic search
   <https://api.crossref.org/works?query.bibliographic=Ichimiya+Cohen+Reflection+High-Energy+Electron+Diffraction+Cambridge+University+Press+2004&rows=5>
   and accepted on the five-field rule (authors Ichimiya, Ayahiko and Cohen, Philip I. in this order;
   title; Cambridge University Press; published-print 2004-12-13, online 2010-07-06; no volume). The
   record `/works/10.1017/cbo9780511735097` was fetched (HTTP 200) and every field matches; the DOI was
   added.
3. **U07 (B09 chapter 13).** Found independently by
   <https://api.crossref.org/works?query.bibliographic=V%C3%B6lkl+Allard+Joy+Electron+Holography+using+Diffracted+Electron+Beams+%28DBH%29+Introduction+to+Electron+Holography+Springer%2FPlenum+1999&rows=5>;
   record `/works/10.1007/978-1-4615-4817-1_13` (HTTP 200): "Electron Holography Using Diffracted
   Electron Beams (DBH)", authors R. A. Herring and G. Pozzi, pages 295-310, 1999, ISBNs equal to B09's.
   **Confirmed**; U07 corrected and moved to the verified section (acceptance by identifier substitution,
   see Method 3, because the entry had no author to test).

## Findings that change what the summary documents say (docs/00-07 not edited here)

| File:line | Current statement | What the records show |
|---|---|---|
| docs/00_executive_summary.md:75-77 | Hitachi patent suggests "at second hand" a vacuum reference wave passing beside the specimen; UNVERIFIED | Google Patents record of US 4,998,788 A (HTTP 200): abstract states the non-illuminating part of the wave "passes aside, the specimen" and is superimposed on the reflected wave. Confirmed at abstract (metadata) level; the description was not read. Inventors are **Osakabe and Tonomura only**; filed 1990-01-10, issued 1991-03-12, assignee Hitachi Ltd. |
| docs/00_executive_summary.md:92-93 | "Literature evidence is index-level only" | 90 of 96 entries now carry METADATA_VERIFIED from Crossref or a publisher/registry record (2 of them partially); no content was read. |
| docs/02_literature_position.md:16, 18, 21-23 | P08, P09 cited as "J. Electron Microsc. Tech. (renamed Microsc. Res. Tech.)"; masthead UNVERIFIED | Crossref gives container "Microscopy Research and Technique", vol. 20, issue 4, P08 457-462, P09 **450-456** (the 450-466 report was wrong), published-print 1992-02-15. Crossref stores the journal title at journal level, so the printed masthead is still not displayed. |
| docs/02_literature_position.md:19 | PAT01 identity index-level; description UNVERIFIED | As for 00:75-77. The single-biprism detail is still unverified. |
| docs/02_literature_position.md:53-55 | Kudo et al. 2023: journal title differs from the preprint, UNVERIFIED | Confirmed: arXiv 2306.00271 (Kudo, Yamamoto, Hoshi) "A fast and accurate ..."; journal version in Computer Physics Communications 296 (2024), "A fast and efficient computation method for reflective diffraction simulations" (Crossref, PII match). Not merged into P49 (year differs from the preprint's). |
| docs/02_literature_position.md:59-60 | "Crossref every bibliography entry" still to do | Done (this log). |
| docs/05_final_repository_specification.md:290 | "Literature position (... index-level evidence only)" | As for 00:92-93. |
| docs/07_reading_plan.md:32 | B05 Rose "2012/2013" | Crossref (Springer deposit): published-print **2012**; bib year corrected from 2013 to 2012. |
| docs/07_reading_plan.md:36 | B09/C01 "Völkl" (first name not stated); "ch. 13 on diffracted-beam holography" | Editor is **Edgar** Völkl; ch. 13 is by **R. A. Herring and G. Pozzi**, pp. 295-310 -- the same Herring as P43/P44 (University of Victoria). |
| docs/07_reading_plan.md:41 | B13 "Kohl and Reimer" | Not contradicted, but still unverified: no reachable record carries the author list or order. |
| docs/07_reading_plan.md:57 | Step 1 logs "in `B2_bib_verification_log.md`" | Logged here in B3 as instructed; B2 kept unedited. |

Other corrections with no statement in docs/00-07: P24 and P25 first author **Y.** Uchida (not N.),
P24 second author J. Jäger (not W.), pages P24 325-327 and P25 53-59; P51's published title is
"... mapping of structural reconstruction ..." (the old title was the arXiv one); P20 pages 174-182;
B08 year 2004 confirmed (published-print 2004-01-08; the IUCr review's "2003" is not the publisher
date); U01 McCoy and Maksym is Surface Science **298, 468-472 (1993)**, not 1994 or 1997 -- but the same
Crossref search returned two further McCoy and Maksym papers that are closer to this project and are
NOT in the bib (leads only, not added): "Multiple scattering calculations of step contrast in REM images
of the Si(001) surface", Surface Science 310(1-3), 217-225 (1994), 10.1016/0039-6028(94)91386-2 --
probably the "1994" paper the B2 brief meant -- and "Simulation of reflection electron microscopy
images: application to high-resolution imaging of the Si(001)2 x 1 surface", Surface Science 297(2),
113-126 (1993), 10.1016/0039-6028(93)90254-h; U02
"Dynamical theory of RHEED from stepped surfaces" is by **J. L. Beeby** alone (same issue), not McCoy and
Maksym; U04 (policy ID P29) is Zhao, Poon and Tong, "Invariant-embedding R-matrix scheme for reflection
high-energy electron diffraction" (the summariser's title was wrong); U06 (the alleged Osakabe chapter
in the 1995 proceedings) is **contradicted**: Crossref lists all 38 items of that volume
(ISBN 9780444820518) and none is by Osakabe or on reflection holography; U03 (policy ID PAT02) is
US 10,755,892 B2, inventor Weijie Huang, KLA Tencor Corp; S01's author is Matthew R. C. Fitzpatrick
(DataCite); the Prismatic citation page (S02) also asks for Pryor, Ophus and Miao 2017, which is not in
the bib.

## Still unverified (six entries, kept in the UNVERIFIED section)

U06 (contradicted, see above); U11, U15 and U18 (Crossref returned a record with the same or a
closely related title, but the entry has no author, year or volume to test, so the strict rule cannot
accept it -- candidate DOIs are in the per-entry records below: U11 10.1088/0022-3727/49/24/244003,
first author Denneulin 2016; U15 10.1038/s41467-025-64133-3, first author Blackburn 2025; U18
10.1016/j.softx.2020.100593, first author Daniluk 2020); U13 (the only Ishizuka inclined-illumination
papers Crossref returns are Acta Cryst. A 37 (1981) and A 38 (1982), not 1998); U14 (a plausible Phil.
Mag. Lett. 71 (1995) multislice paper, first author Chen, but the entry has no author or title).

## Limitations

* B13: authors and their order are not carried by the Crossref book record or its chapter records;
  Springer page not readable. B14: subtitle likewise. Both are counted as "verified except" below.
* B05: the 2012 year rests on the Crossref deposit alone (Springer page not readable).
* Crossref DOIs are returned in lower case (e.g. `10.1016/0039-6028(93)90062-o`); DOIs are
  case-insensitive, and the added ones are copied exactly as the record gives them.
* Crossref container titles for Acta Cryst. A records read "Acta Crystallographica Section A
  Foundations of Crystallography"; the bib keeps the shorter prefix form (reported per entry, not
  counted as a discrepancy). Book publishers are compared as registrant vs imprint (e.g. "Springer US"
  vs "Springer/Plenum", "Wiley" vs "Wiley-VCH"); these are reported per entry and not changed.

<!-- BEGIN GENERATED -->
## Counts (produced by `tools/bib/crossref_check.py report`)

| Quantity | Count |
|---|---|
| entries checked (baseline file) | 96 |
| baseline entries with a doi field | 45 |
| ... of which Crossref /works returned HTTP 200 | 44 |
| Crossref bibliographic searches run (entries without doi) | 43 |
| ... candidate accepted on the five-field rule | 24 |
| ... candidate accepted with identifier substitution | 11 |
| VERIFIED, record unchanged | 33 |
| VERIFIED, record corrected (fields and/or doi added) | 55 |
| VERIFIED except for a field no reachable record carries (listed per entry) | 2 |
| newly found DOIs (copied from Crossref, never constructed) | 35 |
| entries moved out of the UNVERIFIED section | 12 |
| still unverified (no accepted record, or residual discrepancy) | 6 |
| HTTP failures (network error, 429 or 5xx after retries) | 0 |

Syntax validation of the current `references.bib`: {"entries": 96, "unique_keys": 96, "verified_section": 90, "unverified_section": 6, "with_doi": 80}; errors: none; entries whose doi is not backed by a cached registry record: none.

Entries changed, by field (baseline -> current; `note` excluded): author: 9; author (added): 7; doi (added): 35; editor: 3; howpublished: 8; isbn (added): 1; number (added): 24; pages: 3; pages (added): 9; publisher (added): 1; title: 9; url: 1; url (added): 1; version (added): 1; volume (added): 5; year: 1; year (added): 4.

## Corrections (baseline -> current, every changed field except `note`)

| key | field | before | after |
|---|---|---|---|
| B03 | doi | (absent) | 10.1016/c2018-0-04650-2 |
| B04 | doi | (absent) | 10.1016/c2021-0-01238-4 |
| B05 | year | 2013 | 2012 |
| B07 | doi | (absent) | 10.1017/cbo9780511735097 |
| B09 | editor | V{\"o}lkl, Ernst and Allard, Lawrence F. and Joy, David C. | V{\"o}lkl, Edgar and Allard, Lawrence F. and Joy, David C. |
| C01 | author | V{\"o}lkl, Ernst and Lehmann, Michael | V{\"o}lkl, Edgar and Lehmann, Michael |
| C01 | editor | V{\"o}lkl, Ernst and Allard, Lawrence F. and Joy, David C. | V{\"o}lkl, Edgar and Allard, Lawrence F. and Joy, David C. |
| B11 | doi | (absent) | 10.1002/9783527829712 |
| P01 | number | (absent) | 9A |
| P02 | number | (absent) | 25 |
| P02E | number | (absent) | 5 |
| P03 | number | (absent) | 4 |
| P05 | author | Rangel DaCosta, Luis and others | {Rangel DaCosta}, Luis and Brown, Hamish G. and Pelz, Philipp M. and Rakowski, Alexander and Barber, Natolya and O'Donovan, Peter and McBean, Patrick and Jones, Lewys and Ciston, Jim and Scott, M.C. and Ophus, Colin |
| P07 | doi | (absent) | 10.1093/jmicro/dfaa033 |
| S01 | author | Fitzpatrick, Matthew R. | Fitzpatrick, Matthew R. C. |
| PAT01 | author | Osakabe, N. and Endo, J. and Tonomura, A. and Tomita, M. and Furutsu, T. | Osakabe, Nobuyuki and Tonomura, Akira |
| PAT01 | howpublished | United States Patent US 4,998,788 A; assignee reported as Hitachi, Ltd.; US application 07/462,769; European family member EP 0 378 237 B1. Search index showed: USPTO full-text URL \url{https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4998788} titled "Reflection electron holography apparatus"; \url{https://patents.google.com/patent/US4998788} titled "US4998788A - Reflection electron holography apparatus"; \url{https://patents.google.com/patent/EP0378237B1/en} titled "EP0378237B1 - Reflection electron holography apparatus"; \url{https://data.epo.org/publication-server/rest/v1.2/patents/EP0378237NWA2/document.html} | US Patent 4,998,788 A, ``Reflection electron holography apparatus''; application US 07/462,769 filed 10 January 1990, Japanese priority 13 January 1989; issued 12 March 1991; assignee Hitachi Ltd. Family member EP 0 378 237 B1. Record: \url{https://patents.google.com/patent/US4998788A/en} |
| PAT01 | url | https://patents.google.com/patent/US4998788 | https://patents.google.com/patent/US4998788A/en |
| PAT01 | year | (absent) | 1991 |
| P14 | number | (absent) | 2--3 |
| P14 | doi | (absent) | 10.1016/0039-6028(80)90675-5 |
| P15 | number | (absent) | 3 |
| P15 | doi | (absent) | 10.1103/revmodphys.59.639 |
| P27 | number | (absent) | 4 |
| P28 | number | (absent) | 2--3 |
| P28 | doi | (absent) | 10.1016/0039-6028(93)90046-m |
| P17 | number | (absent) | 1R |
| P17 | doi | (absent) | 10.1143/jjap.22.176 |
| P18 | number | (absent) | 6 |
| P18 | doi | (absent) | 10.1107/s0108767386098756 |
| P20 | number | (absent) | 2 |
| P20 | pages | (absent) | 174--182 |
| P20 | doi | (absent) | 10.1107/s0108767388010888 |
| P21 | number | (absent) | 1 |
| P21 | doi | (absent) | 10.1107/s0108767389009141 |
| P22 | number | (absent) | 7 |
| P22 | doi | (absent) | 10.1107/s0108767390002781 |
| P24 | author | Uchida, N. and J{\"a}ger, W. and Lehmpfuhl, G. | Uchida, Y. and J{\"a}ger, J. and Lehmpfuhl, G. |
| P24 | pages | 325--328 | 325--327 |
| P24 | number | (absent) | 3 |
| P24 | doi | (absent) | 10.1016/0304-3991(84)90210-9 |
| P25 | author | Uchida, N. and Lehmpfuhl, G. | Uchida, Y. and Lehmpfuhl, G. |
| P25 | pages | 53--60 | 53--59 |
| P25 | number | (absent) | 1 |
| P25 | doi | (absent) | 10.1016/0304-3991(87)90226-9 |
| P26 | number | (absent) | 4 |
| P26 | doi | (absent) | 10.1016/0304-3991(90)90041-j |
| ZLWANG96 | doi | (absent) | 10.1017/cbo9780511525254 |
| P31 | doi | (absent) | 10.1016/j.ultramic.2011.04.008 |
| P32 | doi | (absent) | 10.1016/j.ultramic.2013.07.007 |
| P33 | doi | (absent) | 10.1016/j.ultramic.2019.112844 |
| P34 | author | Roy, S. and others | Roy, S. and Parks, D. and Seu, K. A. and Su, R. and Turner, J. J. and Chao, W. and Anderson, E. H. and Cabrini, S. and Kevan, S. D. |
| P34 | number | (absent) | 4 |
| P34 | pages | (absent) | 243--245 |
| P35 | doi | (absent) | 10.1038/ncomms1569 |
| P37 | number | (absent) | 2 |
| P38 | doi | (absent) | 10.1364/optica.505478 |
| P41 | author | Wang, R. and Zhao, Q. and Loetgering, L. and others | Wang, Ruihai and Zhao, Qianhao and Loetgering, Lars and Allars, Frederick and Hong, Zhixuan and Pennycook, Timothy J. and Horstmeyer, Roarke and Rodenburg, John and Maiden, Andrew and Zheng, Guoan |
| P42 | doi | (absent) | 10.1093/jmicro/dfaa055 |
| P44 | pages | (absent) | 297--301 |
| P44 | doi | (absent) | 10.1093/jmicro/dfaa066 |
| P51 | title | Electron holographic mapping of structural and electronic reconstruction at mono- and bilayer steps of h-BN | Electron holographic mapping of structural reconstruction at mono- and bilayer steps of {h-BN} |
| P51 | number | (absent) | 3 |
| P51 | doi | (absent) | 10.1103/physrevresearch.5.033137 |
| P49 | author | Kudo, S. and others | Kudo, Shuhei and Yamamoto, Yusaku and Hoshi, Takeo |
| SIMTRHEPD-CPC | title | Comput. Phys. Commun. 277, 108371 (2022) -- reference [1] of the sim-trhepd-rheed README | sim-trhepd-rheed -- Open-source simulator of total-reflection high-energy positron diffraction (TRHEPD) and reflection high-energy electron diffraction (RHEED) |
| HANADA95 | title | Phys. Rev. B 51, 13320 (1995) -- reference [2] of the sim-trhepd-rheed README | Rocking-curve analysis of reflection high-energy electron diffraction from the {Si(111)-($\sqrt{3}\times\sqrt{3}$)$R30^\circ$-Al}, -{Ga}, and -{In} surfaces |
| HANADA95 | number | (absent) | 19 |
| HANADA95 | doi | (absent) | 10.1103/physrevb.51.13320 |
| RHEEDIUM | title | Rheedium | {dxm447/rheedium: Basic Unit Cell Operations} |
| RHEEDIUM | publisher | (absent) | Zenodo |
| RHEEDIUM | version | (absent) | 2025.01.24 |
| BLACKBURN14 | doi | (absent) | 10.1016/j.ultramic.2013.08.009 |
| U01 | title | Simulation of high-resolution REM images (title as displayed in the search index) | Simulation of high-resolution REM images |
| U01 | howpublished | Search index showed: \url{https://www.sciencedirect.com/science/article/abs/pii/003960289390062O} titled "Simulation of high-resolution REM images"; \url{https://www.semanticscholar.org/paper/Simulation-of-reflection-electron-microscopy-to-of-McCoy-Maksym/e3ceb3ebcf994d4234b2e87a1df7c88192646c0e}, whose slug carries "McCoy-Maksym" and whose displayed title is "application to high-resolution imaging of the Si(001)2 x 1 surface" | (removed) |
| U01 | volume | (absent) | 298 |
| U01 | number | (absent) | 2--3 |
| U01 | pages | (absent) | 468--472 |
| U01 | year | (absent) | 1993 |
| U01 | doi | (absent) | 10.1016/0039-6028(93)90062-o |
| U02 | howpublished | Search index showed \url{https://www.sciencedirect.com/science/article/abs/pii/003960289390043J} with this title and NO author attribution | (removed) |
| U02 | author | (absent) | Beeby, J.L. |
| U02 | volume | (absent) | 298 |
| U02 | number | (absent) | 2--3 |
| U02 | pages | (absent) | 307--315 |
| U02 | year | (absent) | 1993 |
| U02 | doi | (absent) | 10.1016/0039-6028(93)90043-j |
| U03 | howpublished | United States Patent reported as US 10,755,892 (kind code not established) | US Patent 10,755,892 B2; application US 16/412,505 filed 15 May 2019, priority US provisional 62/675,645 of 23 May 2018; issued 25 August 2020; original assignee KLA Tencor Corp (current assignee KLA Corp). Record: \url{https://patents.google.com/patent/US10755892B2/en} |
| U03 | author | (absent) | Huang, Weijie |
| U03 | year | (absent) | 2020 |
| U03 | url | (absent) | https://patents.google.com/patent/US10755892B2/en |
| U04 | pages | 1172 | 1172--1182 |
| U04 | title | TITLE NOT ESTABLISHED | Invariant-embedding {$R$}-matrix scheme for reflection high-energy electron diffraction |
| U04 | howpublished | B\_literature.md section 3.2 [P29]: the summariser offered "Accurate Dynamical Theory of RHEED Rocking-curve Intensity Spectra", which B\_literature.md could not corroborate | (removed) |
| U04 | number | (absent) | 2 |
| U04 | doi | (absent) | 10.1103/physrevb.38.1172 |
| U05 | title | Electron Holography (proceedings of the International Workshop on Electron Holography, Knoxville TN, 29--31 August 1994) | Electron Holography |
| U05 | isbn | (absent) | 9780444820518 |
| U07 | editor | V{\"o}lkl, Ernst and Allard, Lawrence F. and Joy, David C. | V{\"o}lkl, Edgar and Allard, Lawrence F. and Joy, David C. |
| U07 | author | (absent) | Herring, R. A. and Pozzi, G. |
| U07 | pages | (absent) | 295--310 |
| U07 | doi | (absent) | 10.1007/978-1-4615-4817-1_13 |
| U08 | howpublished | ScienceDirect PII S0304399114001211 | (removed) |
| U08 | author | (absent) | Javon, E. and Lubk, A. and Cours, R. and Reboh, S. and Cherkashin, N. and Houdellier, F. and Gatel, C. and H{\"y}tch, M.J. |
| U08 | volume | (absent) | 147 |
| U08 | pages | (absent) | 70--85 |
| U08 | doi | (absent) | 10.1016/j.ultramic.2014.06.005 |
| U09 | howpublished | ScienceDirect PII S0304399115300413; PubMed record \url{https://pubmed.ncbi.nlm.nih.gov/26476802/} (PMID 26476802) seen in this pass with this exact title | (removed) |
| U09 | author | (absent) | Denneulin, Thibaud and Houdellier, Florent and H{\"y}tch, Martin |
| U09 | volume | (absent) | 160 |
| U09 | pages | (absent) | 98--109 |
| U09 | doi | (absent) | 10.1016/j.ultramic.2015.10.002 |
| U10 | title | Dynamical diffraction effects of inhomogeneous strain fields investigated by scanning CBED and dark-field electron holography | Dynamical diffraction effects of inhomogeneous strain fields investigated by scanning convergent electron beam diffraction and dark field electron holography |
| U10 | howpublished | ScienceDirect PII S030439912500021X; PMID 40068240 | (removed) |
| U10 | author | (absent) | Niermann, L. and Niermann, T. and Lehmann, M. |
| U10 | volume | (absent) | 271 |
| U10 | pages | (absent) | 114122 |
| U10 | doi | (absent) | 10.1016/j.ultramic.2025.114122 |
| U16 | author | (absent) | Reidy, Kate and Varnavides, Georgios and Thomsen, Joachim Dahl and Blackburn, Arthur and Pham, Thang and Kumar, Abinash and LeBeau, James and Ross, Frances |
| U16 | number | (absent) | S2 |
| U16 | doi | (absent) | 10.1017/s1431927620016104 |
| U17 | title | PyRHEED: RHEED analysis and simulation | PyRHEED |

## Per-entry record

Discrepancy kinds: `family`/`diacritics`/`given`/`count`/`incomplete` (names), `ratio=` (title similarity after case/punctuation folding), `container`, `volume`, `issue`, `pages`, `year`, `publisher`, `missing` (field absent in bib but present in record). Search verdicts: A first author, T title, C container or publisher, Y year, V volume, P first page, I PII/ISBN.

### B01 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1093/acprof:oso/9780199668632.001.0001
- Query URL: <https://api.crossref.org/works/10.1093/acprof:oso/9780199668632.001.0001>  (HTTP: 200)
- Crossref dates: {'published-print': '2013-9-12', 'issued': '2013-9-12', 'published': '2013-9-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B01.json; B3, 2026-09-22)`

### B02 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1017/cbo9780511615092
- Query URL: <https://api.crossref.org/works/10.1017/CBO9780511615092>  (HTTP: 200)
- Crossref dates: {'published-print': '2003-3-27', 'published-online': '2009-12-2', 'issued': '2003-3-27', 'published': '2003-3-27'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B02.json; B3, 2026-09-22)`

### B03 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/c2018-0-04650-2
- Query URL: <https://api.crossref.org/works?query.bibliographic=Hawkes+Kasper+Principles+of+Electron+Optics%2C+Volume+3%3A+Fundamental+Wave+Optics+Academic+Press+2022&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2022', 'issued': '2022', 'published': '2022'}; bib year matches: ['published-print', 'issued', 'published']
- type: edited-book
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/b978-0-12-818979-5.00058-9` score 72.6 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00056-5` score 67.6 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.326, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Relativistic Wave Equation"
  - `10.1016/b978-0-323-91646-2.00079-7` score 66.1 **REJECT(I,T,C)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.213, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Wigner Optics"
  - `10.1016/b978-0-12-333354-4.50008-2` score 63.7 **REJECT(I,T,C,Y)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- HAWKES; 1994; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-012333340-7/50237-4` score 63.7 **REJECT(I,T,C,Y)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Hawkes; 1996; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00102-9` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.09, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Index"
  - `10.1016/b978-0-12-818979-5.00084-x` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.176, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Preface to the Second Edition"
  - `10.1016/b978-0-12-818979-5.00060-7` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.28, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Elementary Diffraction Patterns"
  - `10.1016/b978-0-12-818979-5.00083-8` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.229, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Contents"
  - `10.1016/b978-0-12-818979-5.00061-9` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.244, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "General Introduction"
  - `10.1016/c2018-0-04650-2` score 0.0 **ACCEPT-SUBSTITUTED(A<-I)** {'A': 'untestable', 'I': 'match', 'T': 'match', 'T_note': 'main title only (record has no subtitle)', 'T_ratio': 0.76, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Elsevier; vol ; "Principles of Electron Optics, Volume 3"
  - `10.1016/b978-0-12-818979-5.00066-8` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.323, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Image Formation in the Conventional Transmission Electron Microscope"
  - `10.1016/b978-0-12-818979-5.00085-1` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.2, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Preface to the First Edition"
  - `10.1016/b978-0-12-818979-5.00068-1` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.178, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Statistical Parameter Estimation Theory"
  - `10.1016/b978-0-12-818979-5.00101-7` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.244, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Notes and References"
  - `10.1016/b978-0-12-818979-5.00059-0` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.397, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The General Theory of Electron Diffraction and Interference"
  - `10.1016/b978-0-12-818979-5.00086-3` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.139, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Dedication"
  - `10.1016/b978-0-12-818979-5.00064-4` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.244, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "General Introduction"
  - `10.1016/b978-0-12-818979-5.00055-3` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.209, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Schrödinger Equation"
  - `10.1016/b978-0-12-818979-5.00081-4` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.139, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Title page"
  - `10.1016/b978-0-12-818979-5.00067-x` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.317, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Image Formation in the Scanning Transmission Electron Microscope"
  - `10.1016/b978-0-12-818979-5.00082-6` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.113, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Copyright"
  - `10.1016/b978-0-12-818979-5.00065-6` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.323, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Fundamentals of Transfer Theory"
  - `10.1016/b978-0-12-818979-5.00058-9` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00056-5` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.326, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Relativistic Wave Equation"
- Discrepancies (baseline vs record): `publisher` 'Academic Press' vs 'Elsevier' (publisher)
- Remaining differences (current vs record): `publisher` 'Academic Press' vs 'Elsevier' -- kept: imprint Academic Press (Elsevier page: imprint and copyright holder "Academic Press") vs Crossref registrant Elsevier
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API edited-book record matched by ISBN, cached as docs/agent_reports/crossref_cache/B03.json, plus the Elsevier page in the url field; B3, 2026-09-22)`

### B04 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/c2021-0-01238-4
- Query URL: <https://api.crossref.org/works?query.bibliographic=Hawkes+Kasper+Principles+of+Electron+Optics%2C+Volume+4%3A+Advanced+Wave+Optics+Academic+Press+2022&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2022', 'issued': '2022', 'published': '2022'}; bib year matches: ['published-print', 'issued', 'published']
- type: edited-book
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/b978-0-12-818979-5.00058-9` score 72.6 **REJECT(I,T,C)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.405, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00056-5` score 67.6 **REJECT(I,T,C)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.337, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Relativistic Wave Equation"
  - `10.1016/b978-0-323-91646-2.00079-7` score 66.1 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.222, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Wigner Optics"
  - `10.1016/b978-0-12-333354-4.50008-2` score 63.8 **REJECT(I,T,C,Y)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.405, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- HAWKES; 1994; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-012333340-7/50237-4` score 63.7 **REJECT(I,T,C,Y)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.405, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Hawkes; 1996; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-323-91646-2.00089-x` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.145, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Dedication"
  - `10.1016/b978-0-323-91646-2.00072-4` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.2, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Enhancement"
  - `10.1016/b978-0-323-91646-2.00086-4` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.278, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Notes and References"
  - `10.1016/b978-0-323-91646-2.00075-x` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.264, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Three-Dimensional Reconstruction"
  - `10.1016/b978-0-323-91646-2.00082-7` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.118, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Copyright"
  - `10.1016/b978-0-323-91646-2.00021-9` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.438, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Corrections and additions to volumes 1, 2 and 3"
  - `10.1016/b978-0-323-91646-2.00070-0` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.254, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Introduction"
  - `10.1016/c2021-0-01238-4` score 0.0 **ACCEPT-SUBSTITUTED(A<-I)** {'A': 'untestable', 'I': 'match', 'T': 'match', 'T_note': 'main title only (record has no subtitle)', 'T_ratio': 0.784, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Elsevier; vol ; "Principles of Electron Optics, Volume 4"
  - `10.1016/b978-0-323-91646-2.00078-5` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.247, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Coherence and the Brightness Functions"
  - `10.1016/b978-0-323-91646-2.00085-2` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.207, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Preface to the First Edition"
  - `10.1016/b978-0-323-91646-2.00079-7` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.222, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Wigner Optics"
  - `10.1016/b978-0-323-91646-2.00083-9` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.149, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Contents"
  - `10.1016/b978-0-323-91646-2.00088-8` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.094, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Index"
  - `10.1016/b978-0-323-91646-2.00084-0` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.182, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Preface to the Second Edition"
  - `10.1016/b978-0-323-91646-2.00077-3` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.175, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Microscope Parameter Measurement and Instrument Control"
  - `10.1016/b978-0-323-91646-2.00071-2` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.333, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Acquisition, Sampling and Coding"
  - `10.1016/b978-0-323-91646-2.00080-3` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.303, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Orbital Angular Momentum, Vortex Beams and the Quantum Electron Microscope"
  - `10.1016/b978-0-323-91646-2.00074-8` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.327, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Nonlinear Restoration – The Phase Problem"
  - `10.1016/b978-0-323-91646-2.00081-5` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.145, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Title page"
  - `10.1016/b978-0-323-91646-2.00073-6` score 0.0 **REJECT(T)** {'A': 'match', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.208, 'C': 'match', 'C_note': "imprint 'Academic Press' vs registrant 'Elsevier'; ISBN matches", 'Y': 'match', 'V': 'n/a'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Linear Restoration"
- Discrepancies (baseline vs record): `publisher` 'Academic Press' vs 'Elsevier' (publisher)
- Remaining differences (current vs record): `publisher` 'Academic Press' vs 'Elsevier' -- kept: imprint Academic Press (Elsevier page: imprint and copyright holder "Academic Press") vs Crossref registrant Elsevier
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API edited-book record matched by ISBN, cached as docs/agent_reports/crossref_cache/B04.json, plus the Elsevier page in the url field; B3, 2026-09-22)`

### B05 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1007/978-3-642-32119-1
- Query URL: <https://api.crossref.org/works/10.1007/978-3-642-32119-1>  (HTTP: 200)
- Crossref dates: {'published-print': '2012', 'issued': '2012', 'published': '2012'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer Berlin Heidelberg'
- type: book
- Discrepancies (baseline vs record): `year` '2013' vs 'published-print 2012; issued 2012; published 2012' (year)
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B05.json; B3, 2026-09-22)`

### B06 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-33260-0
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-33260-0>  (HTTP: 200)
- Crossref dates: {'published-print': '2020', 'issued': '2020', 'published': '2020'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index, single) (B report)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B06.json; B3, 2026-09-22)`

### B07 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1017/cbo9780511735097
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ichimiya+Cohen+Reflection+High-Energy+Electron+Diffraction+Cambridge+University+Press+2004&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2004-12-13', 'published-online': '2010-7-6', 'issued': '2004-12-13', 'published': '2004-12-13'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1017/cbo9780511735097` score 65.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Ichimiya; 2004/2010; Cambridge University Press; vol ; "Reflection High-Energy Electron Diffraction"
  - `10.1002/adma.200590112` score 47.7 **REJECT(A,T,C,Y)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.628, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Osten; 2005; Advanced Materials; vol 17; "Book Review: Reflection High Energy Electron Diffraction. By Ayahiko Ichimiya an"
  - `10.1017/cbo9780511735097.011` score 46.2 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.658, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2004; Reflection High-Energy Electron Diffraction; vol ; "Kinematic electron diffraction"
  - `10.1017/cbo9780511735097.023` score 45.1 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.41, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2004; Reflection High-Energy Electron Diffraction; vol ; "Appendix C: Kirchhoff's diffraction theory"
  - `10.1017/cbo9780511735097.009` score 44.5 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.441, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2004; Reflection High-Energy Electron Diffraction; vol ; "Real diffraction patterns"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (route: Crossref API monograph record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/B07.json; B3, 2026-09-22)`

### B08 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1093/oso/9780198500742.001.0001
- Query URL: <https://api.crossref.org/works/10.1093/oso/9780198500742.001.0001>  (HTTP: 200)
- Crossref dates: {'published-print': '2004-1-8', 'issued': '2004-1-8', 'published': '2004-1-8'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Oxford University Press' vs Crossref 'Oxford University PressOxford'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B08.json; B3, 2026-09-22)`

### B09 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1007/978-1-4615-4817-1
- Query URL: <https://api.crossref.org/works/10.1007/978-1-4615-4817-1>  (HTTP: 200)
- Crossref dates: {'published-print': '1999', 'issued': '1999', 'published': '1999'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer/Plenum' vs Crossref 'Springer US'
- type: book
- Discrepancies (baseline vs record): `editor[1].given` 'Ernst' vs 'Edgar' (given)
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B09.json; B3, 2026-09-22)`

### C01 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1007/978-1-4615-4817-1_6
- Query URL: <https://api.crossref.org/works/10.1007/978-1-4615-4817-1_6>  (HTTP: 200)
- Crossref dates: {'published-print': '1999', 'issued': '1999', 'published': '1999'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer/Plenum' vs Crossref 'Springer US'
- type: book-chapter
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/C01.json; B3, 2026-09-22)`

### B10 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-540-37204-2
- Query URL: <https://api.crossref.org/works/10.1007/978-3-540-37204-2>  (HTTP: 200)
- Crossref dates: {'published-print': '1999', 'issued': '1999', 'published': '1999'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer Berlin Heidelberg'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B10.json; B3, 2026-09-22)`

### B11 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1002/9783527829712
- Query URL: <https://api.crossref.org/works?query.bibliographic=Shindo+Tomita+Material+Characterization+Using+Electron+Holography+Wiley-VCH+2022&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2022-11-14', 'published-online': '2022-9-2', 'issued': '2022-9-2', 'published': '2022-9-2'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Wiley-VCH' vs Crossref 'Wiley'
- type: monograph
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1002/9783527829712` score 67.0 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Shindo; 2022; Wiley; vol ; "Material Characterization using Electron Holography"
  - `10.1002/9783527829712.ch4` score 46.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.595, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Principles of Electron Holography"
  - `10.1002/9783527829712.fmatter` score 43.8 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.19, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Front Matter"
  - `10.1002/9783527829712.part3` score 43.2 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.258, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Application"
  - `10.1002/9783527829712.index` score 43.2 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.107, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Index"
  - `10.1002/9783527829712.ch11` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.449, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Extension of Analysis of Collective Motions of Electrons"
  - `10.1002/9783527829712.part1` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.222, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Introduction"
  - `10.1002/9783527829712.ch2` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.409, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "M             axwell's Equations and Special Relativity"
  - `10.1002/9783527829712.fmatter` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.19, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Front Matter"
  - `10.1002/9783527829712.ch9` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.362, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Charging Effects and Secondary Electron Distribution of Biological Specimens"
  - `10.1002/9783527829712.part3` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.258, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Application"
  - `10.1002/9783527829712` score 0.0 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Shindo; 2022; Wiley; vol ; "Material Characterization using Electron Holography"
  - `10.1002/9783527829712.ch12` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.472, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Theoretical Consideration on Visualizing Collective Motions of Electrons"
  - `10.1002/9783527829712.app1` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.464, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Physical Constants, Conversion Factors, and Electron Wavelength"
  - `10.1002/9783527829712.part2` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.243, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Principles and Practice"
  - `10.1002/9783527829712.part4` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.387, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Visualization of Collective Motions of Electrons and Their Interpretation"
  - `10.1002/9783527829712.ch3` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.478, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Basis of Transmission Electron Microscopy"
  - `10.1002/9783527829712.ch8` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.216, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Magnetic Field Analysis"
  - `10.1002/9783527829712.ch6` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.257, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Related Techniques and Specialized Instrumentation"
  - `10.1002/9783527829712.ch10` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.379, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Collective Motions of Electrons Around Various Charged Insulators"
  - `10.1002/9783527829712.index` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.107, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Index"
  - `10.1002/9783527829712.ch5` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.412, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Microscope Constitution and Hologram Formation"
  - `10.1002/9783527829712.ch4` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.595, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Principles of Electron Holography"
  - `10.1002/9783527829712.ch1` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.296, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Importance of Electromagnetic Field and Its Visualization"
  - `10.1002/9783527829712.ch7` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.243, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Electric Field Analysis"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED / PROJECT_INPUT` -> `METADATA_VERIFIED (route: Crossref API monograph record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/B11.json; B3, 2026-09-22)`

### B12 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-00069-1
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-00069-1>  (HTTP: 200)
- Crossref dates: {'published-print': '2019', 'published-online': '2019-11-2', 'issued': '2019', 'published': '2019'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B12.json; B3, 2026-09-22)`

### C02 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-00069-1_16
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-00069-1_16>  (HTTP: 200)
- Crossref dates: {'published-print': '2019', 'published-online': '2019-11-2', 'issued': '2019', 'published': '2019'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book-chapter
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/C02.json; B3, 2026-09-22)`

### C03 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-00069-1_17
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-00069-1_17>  (HTTP: 200)
- Crossref dates: {'published-print': '2019', 'published-online': '2019-11-2', 'issued': '2019', 'published': '2019'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book-chapter
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/C03.json; B3, 2026-09-22)`

### B13 -- VERIFIED-PARTIAL

- Route: Crossref API /works/10.1007/978-0-387-40093-8
- Query URL: <https://api.crossref.org/works/10.1007/978-0-387-40093-8>  (HTTP: 200)
- Crossref dates: {'published-print': '2008', 'issued': '2008', 'published': '2008'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer New York'
- type: book
- Discrepancies (baseline vs record): none
- NOT verifiable in this pass: author names and order: neither the Crossref book record nor its twelve chapter records carry names; link.springer.com serves a JavaScript challenge
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED except authors (route: Crossref API /works record, cached as docs/agent_reports/crossref_cache/B13.json; B3, 2026-09-22)`

### B14 -- VERIFIED-PARTIAL

- Route: Crossref API /works/10.1007/978-0-387-76501-3
- Query URL: <https://api.crossref.org/works/10.1007/978-0-387-76501-3>  (HTTP: 200)
- Crossref dates: {'published-print': '2009', 'issued': '2009', 'published': '2009'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer US'
- type: book
- Discrepancies (baseline vs record): none
- NOT verifiable in this pass: subtitle "A Textbook for Materials Science": the Crossref record has the main title only; link.springer.com serves a JavaScript challenge
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED except subtitle (route: Crossref API /works record, cached as docs/agent_reports/crossref_cache/B14.json; B3, 2026-09-22)`

### B15 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-1-4419-9583-4
- Query URL: <https://api.crossref.org/works/10.1007/978-1-4419-9583-4>  (HTTP: 200)
- Crossref dates: {'published-print': '2011', 'issued': '2011', 'published': '2011'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer US'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/B15.json; B3, 2026-09-22)`

### P01 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1143/jjap.27.l1772
- Query URL: <https://api.crossref.org/works/10.1143/JJAP.27.L1772>  (HTTP: 200)
- Crossref dates: {'published-print': '1988-9-1', 'issued': '1988-9-1', 'published': '1988-9-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '9A' (missing)
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report, authors/title/journal/volume/year only)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P01.json; B3, 2026-09-22)`

### P02 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1103/physrevlett.62.2969
- Query URL: <https://api.crossref.org/works/10.1103/PhysRevLett.62.2969>  (HTTP: 200)
- Crossref dates: {'published-online': '1989-6-19', 'issued': '1989-6-19', 'published': '1989-6-19'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '25' (missing)
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) +ABSTRACT(index) (B report, re-confirmed here)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P02.json; B3, 2026-09-22)`

### P02E -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1103/physrevlett.63.584.3
- Query URL: <https://api.crossref.org/works/10.1103/PhysRevLett.63.584.3>  (HTTP: 200)
- Crossref dates: {'published-online': '1989-7-31', 'issued': '1989-7-31', 'published': '1989-7-31'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `title` 'Erratum: Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography' vs 'Observation of Surface Undulation Due to Single-Atomic Shear of a Dislocation by Reflection-Electron Holography' (ratio=0.97); `issue` '(absent)' vs '5' (missing)
- Remaining differences (current vs record): `title` 'Erratum: Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography' vs 'Observation of Surface Undulation Due to Single-Atomic Shear of a Dislocation by Reflection-Electron Holography' -- kept: Crossref deposits the erratum under the original title; "Erratum:" prefix kept to distinguish P02E from P02
- Label: `existence METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (upgraded in this pass from "index, single"); CONTENT UNVERIFIED` -> `existence METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P02E.json; B3, 2026-09-22); CONTENT UNVERIFIED`

### P03 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0304-3991(93)90123-f
- Query URL: <https://api.crossref.org/works/10.1016/0304-3991(93)90123-F>  (HTTP: 200)
- Crossref dates: {'published-print': '1993-4', 'issued': '1993-4', 'published': '1993-4'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '4' (missing)
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index, single) (B report)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P03.json; B3, 2026-09-22)`

### P04 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1186/s40679-017-0046-1
- Query URL: <https://api.crossref.org/works/10.1186/s40679-017-0046-1>  (HTTP: 200)
- Crossref dates: {'published-print': '2017-12', 'published-online': '2017-5-10', 'issued': '2017-5-10', 'published': '2017-5-10'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- number_is_article_number: 13
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `SECTION_READ` -> `SECTION_READ (instruction file) + METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P04.json; B3, 2026-09-22)`

### P05 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.micron.2021.103141
- Query URL: <https://api.crossref.org/works/10.1016/j.micron.2021.103141>  (HTTP: 200)
- Crossref dates: {'published-print': '2021-12', 'issued': '2021-12', 'published': '2021-12'}; bib year matches: ['published-print', 'issued', 'published']
- number_is_article_number: 103141
- type: journal-article
- Discrepancies (baseline vs record): `author-count` '1 + others' vs '11 (full list available)' (incomplete)
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P05.json; B3, 2026-09-22)`

### P06 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2009.05.012
- Query URL: <https://api.crossref.org/works/10.1016/j.ultramic.2009.05.012>  (HTTP: 200)
- Crossref dates: {'published-print': '2009-9', 'issued': '2009-9', 'published': '2009-9'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P06.json; B3, 2026-09-22)`

### P07 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1093/jmicro/dfaa033
- Query URL: <https://api.crossref.org/works?query.bibliographic=Harada+Interference+and+interferometry+in+electron+holography+Microscopy+70+2021+3&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2021-2-1', 'published-online': '2020-6-26', 'issued': '2020-6-26', 'published': '2020-6-26'}; bib year matches: ['published-print']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1093/jmicro/dfaa033` score 63.7 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Harada; 2020/2021; Microscopy; vol 70; "Interference and interferometry in electron holography"
  - `10.1093/jmicro/dfaa067` score 44.1 **REJECT(T,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.333, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Harada; 2020/2021; Microscopy; vol 70; "Introduction to ‘electron interference microscopy’"
  - `10.22443/rms.emc2020.134` score 37.7 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.479, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- RIKEN; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Lens-less Fourier Transform Electron Holography for Vortex Beam"
  - `10.1016/b978-044482051-8/50003-8` score 37.4 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.473, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 1995; Electron Holography; vol ; "Progress in Holographic Interference Electron Microscopy"
  - `10.1093/jmicro/dfh098` score 36.1 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.542, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Harada; 2005; Journal of Electron Microscopy; vol 54; "Optical system for double-biprism electron holography"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) +ABSTRACT(index) (B report)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P07.json; B3, 2026-09-22)`

### S01 -- VERIFIED-CORRECTED

- Route: DataCite API record of 10.5281/zenodo.18296081 (the Zenodo DOI in the README) + documentation page
- Query URL: <https://api.datacite.org/dois/10.5281/zenodo.18296081>  (HTTP: datacite 200; docs page 200; README 200 (raw.githubusercontent.com); github.com 403)
- Publisher-page / registry result: DataCite creator "Fitzpatrick, Matthew R. C.", title Prismatique, publisher Zenodo, 2026, version 0.0.4, IsSupplementTo 10.1016/j.micron.2021.103141 and github.com/prism-em/prismatic. Author corrected; no doi field (version differs from the pinned 0.0.1).
- Label: `METADATA_VERIFIED (instruction file, URLs) + SECTION_READ (GitHub README only)` -> `METADATA_VERIFIED (route: DataCite record of the Zenodo DOI printed in the README, cached as docs/agent_reports/crossref_cache/S01.datacite.json, plus the documentation page https://mrfitzpa.github.io/prismatique/; B3, 2026-09-22) + SECTION_READ (GitHub README only, B_literature.md)`

### S02 -- VERIFIED-UNCHANGED

- Route: project pages prism-em.com and prism-em.github.io/about-cite
- Query URL: <https://prism-em.github.io/about-cite/>  (HTTP: 200 (both pages))
- Publisher-page / registry result: Citation page asks for Ophus 2017 (P04), Pryor, Ophus and Miao 2017 (ASCI 3; not in references.bib) and Rangel DaCosta et al. 2021 (P05).
- Label: `METADATA_VERIFIED (instruction file, URLs) + SECTION_READ (GitHub README only)` -> `METADATA_VERIFIED (route: project pages https://prism-em.com/ and https://prism-em.github.io/about-cite/, HTTP 200; B3, 2026-09-22) + SECTION_READ (GitHub README only, B_literature.md)`

### P08 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200415
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200415>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P08.json; B3, 2026-09-22)`

### P09 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200414
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200414>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P09.json; B3, 2026-09-22)`

### PAT01 -- VERIFIED-CORRECTED

- Route: Google Patents record of US 4,998,788 A
- Query URL: <https://patents.google.com/patent/US4998788A/en>  (HTTP: 200)
- Publisher-page / registry result: Inventors Nobuyuki Osakabe and Akira Tonomura (two, not five); assignee Hitachi Ltd; application 07/462,769 filed 1990-01-10; priority JP 1989-01-13; issued 1991-03-12. Abstract: reference wave passes beside the specimen.
- Label: `identity METADATA_VERIFIED(index) (UPGRADED in this pass from "index, single"); INVENTORS, ASSIGNEE, ALL DATES AND THE ENTIRE DESCRIPTION UNVERIFIED` -> `METADATA_VERIFIED (route: Google Patents record https://patents.google.com/patent/US4998788A/en, HTTP 200; B3, 2026-09-22); DESCRIPTION NOT READ`

### P14 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0039-6028(80)90675-5
- Query URL: <https://api.crossref.org/works?query.bibliographic=Osakabe+Tanishiro+Yagi+Reflection+electron+microscopy+of+clean+and+gold+deposited+%28111%29+silicon+surfaces+Surface+Science+97+1980+393&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1980-7', 'issued': '1980-7', 'published': '1980-7'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(80)90675-5` score 123.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Osakabe; 1980; Surface Science; vol 97; "Reflection electron microscopy of clean and gold deposited (111) silicon surface"
  - `10.1016/0167-2584(80)90432-6` score 115.6 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Osakabe; 1980; Surface Science Letters; vol 97; "Reflection electron microscopy of clean and gold deposited (111) silicon surface"
  - `10.1016/0167-2584(81)90396-0` score 72.2 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.328, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Osakabe; 1981; Surface Science Letters; vol 102; "Image contrast of dislocations and atomic steps on (111) silicon surface in refl"
  - `10.1016/0039-6028(81)90493-3` score 64.9 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.516, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Osakabe; 1981; Surface Science; vol 109; "Direct observation of the phase transition between the (7 × 7) and (1 × 1) struc"
  - `10.1143/jjap.19.l309` score 64.9 **REJECT(T,C,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.57, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Osakabe; 1980; Japanese Journal of Applied Physics; vol 19; "Reflection Electron Microscope Observations of Dislocations and Surface Structur"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2-3' (missing)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P14.json; B3, 2026-09-22)`

### P15 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1103/revmodphys.59.639
- Query URL: <https://api.crossref.org/works?query.bibliographic=Tonomura+Applications+of+electron+holography+Reviews+of+Modern+Physics+59+1987+639&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '1987-7-1', 'issued': '1987-7-1', 'published': '1987-7-1'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/revmodphys.59.639` score 73.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Tonomura; 1987; Reviews of Modern Physics; vol 59; "Applications of electron holography"
  - `10.5772/14280` score 42.4 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.805, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 2011; Holography, Research and Technologies; vol ; "Fundamentals and Applications of Electron Holography"
  - `10.1063/1.338452` score 41.6 **REJECT(T,C,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.432, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 1987; Journal of Applied Physics; vol 61; "Electron holography to image magnetic domains (invited)"
  - `10.1002/3527600434.eap174` score 40.1 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.37, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 2003; digital Encyclopedia of Applied Physics; vol ; "Holography, Electron"
  - `10.1063/1.106019` score 37.0 **REJECT(A,T,C,Y,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.588, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'match', 'P': 'mismatch'} -- Ru; 1991; Applied Physics Letters; vol 59; "Phase-shifting electron holography by beam tilting"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '3' (missing)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P15.json; B3, 2026-09-22)`

### P16 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1080/00018739200101473
- Query URL: <https://api.crossref.org/works/10.1080/00018739200101473>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2', 'issued': '1992-2', 'published': '1992-2'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P16.json; B3, 2026-09-22)`

### P27 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0304-3991(92)90213-4
- Query URL: <https://api.crossref.org/works/10.1016/0304-3991(92)90213-4>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-6', 'issued': '1992-6', 'published': '1992-6'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '4' (missing)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P27.json; B3, 2026-09-22)`

### P28 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0039-6028(93)90046-m
- Query URL: <https://api.crossref.org/works?query.bibliographic=Cowley+Electron+holography+and+holographic+diffraction+for+surface+studies+Surface+Science+298+1993+336&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1993-12', 'issued': '1993-12', 'published': '1993-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(93)90046-m` score 92.6 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Cowley; 1993; Surface Science; vol 298; "Electron holography and holographic diffraction for surface studies"
  - `10.1016/0039-6028(93)90047-n` score 51.7 **REJECT(A,I,T,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.489, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Osakabe; 1993; Surface Science; vol 298; "Application of electron holography to surface topography observation"
  - `10.1016/0039-6028(93)90049-p` score 49.6 **REJECT(A,I,T,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.329, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Kono; 1993; Surface Science; vol 298; "Surface-structure analysis by forward scattering in photoelectron and Auger-elec"
  - `10.1016/0039-6028(93)90044-k` score 45.9 **REJECT(A,I,T,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Peng; 1993; Surface Science; vol 298; "Tensor theories of high energy electron diffraction and their use in surface cry"
  - `10.1016/0039-6028(73)90273-2` score 45.7 **REJECT(I,T,Y,V,P)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.525, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Cowley; 1973; Surface Science; vol 38; "Electron diffraction from a statistically rough surface"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2-3' (missing)
- Label: `METADATA_VERIFIED(index, single) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P28.json; B3, 2026-09-22)`

### P17 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1143/jjap.22.176
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ichimiya+Many-beam+calculation+of+reflection+high+energy+electron+diffraction+%28RHEED%29+intensities+by+the+multi-slice+method+Japanese+Journal+of+Applied+Physics+22+1983+176&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1983-1-1', 'issued': '1983-1-1', 'published': '1983-1-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1143/jjap.22.176` score 126.3 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Ichimiya; 1983; Japanese Journal of Applied Physics; vol 22; "Many-Beam Calculation of Reflection High Energy Electron Diffraction (RHEED) Int"
  - `10.1143/jjap.24.1365` score 85.1 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.701, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ichimiya; 1985; Japanese Journal of Applied Physics; vol 24; "Correction to “Many-Beam Calculation of RHEED Intensities by the Multi-Slice Met"
  - `10.1007/bfb0109550` score 64.6 **REJECT(T,C,Y,V,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.609, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- -; ; Springer Tracts in Modern Physics; vol ; "Reflection high-energy electron diffraction (RHEED)"
  - `10.1016/j.cpc.2022.108371` score 55.0 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.477, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Hanada; 2022; Computer Physics Communications; vol 277; "sim-trhepd-rheed – Open-source simulator of total-reflection high-energy positro"
  - `10.1016/0039-6028(90)90108-k` score 53.4 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.706, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ichimiya; 1990; Surface Science; vol 235; "Numerical convergence of dynamical calculations of reflection high-energy electr"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '1R' (missing)
- Label: `METADATA_VERIFIED(index) + SECTION_READ (of the secondary citation only)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P17.json; B3, 2026-09-22) + SECTION_READ (of the secondary citation in the sim-trhepd-rheed README only)`

### P18 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1107/s0108767386098756
- Query URL: <https://api.crossref.org/works?query.bibliographic=Peng+Cowley+Dynamical+diffraction+calculations+for+RHEED+and+REM+Acta+Crystallographica+Section+A+42+1986+545&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1986-11-1', 'issued': '1986-11-1', 'published': '1986-11-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767386098756` score 82.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Peng; 1986; Acta Crystallographica Section A Foundations of Crystallography; vol 42; "Dynamical diffraction calculations for RHEED and REM"
  - `10.1107/s0108767387078796` score 66.3 **REJECT(Y,V,P)** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Peng; 1987; Acta Crystallographica Section A Foundations of Crystallography; vol 43; "Dynamical diffraction calculations for RHEED and REM"
  - `10.1107/s0108767387078899` score 47.0 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.478, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Cowley; 1987; Acta Crystallographica Section A Foundations of Crystallography; vol 43; "Surface channeling in RHEED, REM and EELS"
  - `10.1107/s0108767396008057` score 44.6 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.466, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Peng; 1996; Acta Crystallographica Section A Foundations of Crystallography; vol 52; "Approximate Methods in Dynamical RHEED Calculations"
  - `10.1016/b978-0-444-88864-8.50150-3` score 43.2 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.73, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Peng; 1991; Computer Aided Innovation of New Materials; vol ; "DYNAMICAL DIFFRACTION CALCULATIONS FOR RHEED INTENSITY OSCILLATIONS DURING MBE G"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '6' (missing)
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P18.json; B3, 2026-09-22)`

### P19 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/0039-6028(88)90925-9
- Query URL: <https://api.crossref.org/works/10.1016/0039-6028(88)90925-9>  (HTTP: 200)
- Crossref dates: {'published-print': '1988-1', 'issued': '1988-1', 'published': '1988-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P19.json; B3, 2026-09-22)`

### P20 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1107/s0108767388010888
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ma+Marks+Bloch-wave+solution+in+the+Bragg+case+Acta+Crystallographica+Section+A+45+1989&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1989-2-1', 'issued': '1989-2-1', 'published': '1989-2-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767388010888` score 65.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Ma; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Bloch-wave solution in the Bragg case"
  - `10.1107/s0108767389005982` score 39.1 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.306, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Peng; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Bloch-wave channeling and HOLZ effects in high-energy electron diffraction"
  - `10.1107/s0108767389001054` score 39.1 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.407, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Wright; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Observation of dependent to independent Bloch wave transition in Kikuchi pattern"
  - `10.1107/s0108767389007269` score 37.9 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.43, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Chukhovskii; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Theoretical study of X-ray diffraction in homogeneously bent crystals – the Brag"
  - `10.1107/s0108767388010657` score 35.8 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.361, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Durbin; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Grazing-incidence Bragg–Laue X-ray diffraction"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2' (missing); `pages` '(absent)' vs '174-182' (missing)
- Label: `identity METADATA_VERIFIED(index) (route UPGRADED in this pass to a publisher-URL route) +ABSTRACT(index); PAGE RANGE UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P20.json; B3, 2026-09-22)`

### P21 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1107/s0108767389009141
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ma+Marks+Bloch+waves+and+multislice+in+transmission+and+reflection+diffraction+Acta+Crystallographica+Section+A+46+1990+11&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1990-1-1', 'issued': '1990-1-1', 'published': '1990-1-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767389009141` score 78.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Bloch waves and multislice in transmission and reflection diffraction"
  - `10.1107/s0108767390004810` score 75.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 0.945, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Bloch waves and multislice in transmission and reflection diffraction. Erratum"
  - `10.1111/aya.1990.46.issue-1` score 41.3 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- -; 1990; Acta Crystallographica Section A; vol 46; ""
  - `10.1107/s0108767390002781` score 40.0 **REJECT(T,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.291, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Surface phenomena in RHEED and REM"
  - `10.1107/s0108767306032892` score 39.5 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.452, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Own; 2006; Acta Crystallographica Section A Foundations of Crystallography; vol 62; "Precession electron diffraction 1: multislice simulation"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '1' (missing)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED and strengthened in this pass: title, journal, volume and year now rest on IUCr URLs rather than on prose)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P21.json; B3, 2026-09-22)`

### P22 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1107/s0108767390002781
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ma+Marks+Surface+phenomena+in+RHEED+and+REM+Acta+Crystallographica+Section+A+46+1990+594&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1990-7-1', 'issued': '1990-7-1', 'published': '1990-7-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767390002781` score 73.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Surface phenomena in RHEED and REM"
  - `10.1111/aya.1990.46.issue-1` score 41.3 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- -; 1990; Acta Crystallographica Section A; vol 46; ""
  - `10.1107/s010876739001011x` score 40.1 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.426, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ma; 1991; Acta Crystallographica Section A Foundations of Crystallography; vol 47; "A computational method for obtaining stationary solutions in RHEED and REM"
  - `10.1107/s0108767391005871` score 39.8 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.328, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ma; 1991; Acta Crystallographica Section A Foundations of Crystallography; vol 47; "A robust solution for RHEED"
  - `10.1107/s0108767387011243` score 39.0 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.311, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Marks; 1988; Acta Crystallographica Section A Foundations of Crystallography; vol 44; "Current flow in reflection electron microscopy and RHEED"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '7' (missing)
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P22.json; B3, 2026-09-22)`

### P13 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200408
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200408>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P13.json; B3, 2026-09-22)`

### P12 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200407
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200407>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (route UPGRADED in this pass to a DOI-bearing publisher URL)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P12.json; B3, 2026-09-22)`

### P10 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200403
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200403>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P10.json; B3, 2026-09-22)`

### P11 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200404
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200404>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P11.json; B3, 2026-09-22)`

### P23 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1107/s0021889887086916
- Query URL: <https://api.crossref.org/works/10.1107/S0021889887086916>  (HTTP: 200)
- Crossref dates: {'published-print': '1987-6-1', 'issued': '1987-6-1', 'published': '1987-6-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P23.json; B3, 2026-09-22)`

### P24 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0304-3991(84)90210-9
- Query URL: <https://api.crossref.org/works?query.bibliographic=Uchida+J%C3%A4ger+Lehmpfuhl+Direct+imaging+of+atomic+steps+in+reflection+electron+microscopy+Ultramicroscopy+13+1984+325&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1984-1', 'issued': '1984-1', 'published': '1984-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0304-3991(84)90210-9` score 117.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Uchida; 1984; Ultramicroscopy; vol 13; "Direct imaging of atomic steps in reflection electron microscopy"
  - `10.1016/0304-3991(84)90080-9` score 74.4 **REJECT(T,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.6, 'C': 'match', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1984; Ultramicroscopy; vol 15; "Observation of surface treatments on single crystals by reflection electron micr"
  - `10.1016/0304-3991(87)90226-9` score 66.9 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.594, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1987; Ultramicroscopy; vol 23; "Observation of double contours of monoatomic steps on single crystal surfaces in"
  - `10.1016/0304-3991(92)90140-f` score 60.5 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.63, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; 1992; Ultramicroscopy; vol 45; "Method of directly imaging the reconstruction on Au(111) and Au(100) by reflecti"
  - `10.1016/s0304-3991(79)80037-6` score 57.5 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.326, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Lehmpfuhl; 1979; Ultramicroscopy; vol 4; "Darkfield and brightfield techniques for electron microscopic observation of ato"
- Discrepancies (baseline vs record): `author[1].given` 'N.' vs 'Y.' (given); `author[2].given` 'W.' vs 'J.' (given); `issue` '(absent)' vs '3' (missing); `pages` '325–328' vs '325-327' (pages)
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P24.json; B3, 2026-09-22)`

### P25 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0304-3991(87)90226-9
- Query URL: <https://api.crossref.org/works?query.bibliographic=Uchida+Lehmpfuhl+Observation+of+double+contours+of+monoatomic+steps+on+single+crystal+surfaces+in+reflection+electron+microscopy+Ultramicroscopy+23+1987+53&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1987-1', 'issued': '1987-1', 'published': '1987-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0304-3991(87)90226-9` score 138.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Uchida; 1987; Ultramicroscopy; vol 23; "Observation of double contours of monoatomic steps on single crystal surfaces in"
  - `10.1016/s0304-3991(79)80037-6` score 75.7 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.468, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Lehmpfuhl; 1979; Ultramicroscopy; vol 4; "Darkfield and brightfield techniques for electron microscopic observation of ato"
  - `10.1016/0304-3991(84)90080-9` score 69.9 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.731, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1984; Ultramicroscopy; vol 15; "Observation of surface treatments on single crystals by reflection electron micr"
  - `10.1016/0304-3991(84)90210-9` score 69.4 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.617, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1984; Ultramicroscopy; vol 13; "Direct imaging of atomic steps in reflection electron microscopy"
  - `10.1002/jemt.1070200410` score 65.4 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.724, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1992/2005; Microscopy Research and Technique; vol 20; "Observation of atomic steps on single crystal surfaces by a commercial scanning "
- Discrepancies (baseline vs record): `author[1].given` 'N.' vs 'Y.' (given); `issue` '(absent)' vs '1' (missing); `pages` '53–60' vs '53-59' (pages)
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P25.json; B3, 2026-09-22)`

### P26 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0304-3991(90)90041-j
- Query URL: <https://api.crossref.org/works?query.bibliographic=Yao+Cowley+Electron+diffraction+conditions+and+surface+imaging+in+reflection+electron+microscopy+Ultramicroscopy+33+1990+237&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1990-10', 'issued': '1990-10', 'published': '1990-10'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0304-3991(90)90041-j` score 108.1 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Yao; 1990; Ultramicroscopy; vol 33; "Electron diffraction conditions and surface imaging in reflection electron micro"
  - `10.1016/0304-3991(90)90101-q` score 65.8 **REJECT(A,I,T,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.541, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Banzhof; 1990; Ultramicroscopy; vol 33; "Comparison of surface step images in reflection electron microscopy and scanning"
  - `10.1016/0304-3991(93)90116-f` score 57.9 **REJECT(A,I,T,Y,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.435, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Liu; 1993; Ultramicroscopy; vol 48; "Scanning reflection electron microscopy and associated techniques for surface st"
  - `10.1016/s0304-3991(85)80008-5` score 57.9 **REJECT(A,I,T,Y,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.662, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Cowley; 1985; Ultramicroscopy; vol 16; "The image contrast of surface steps in reflection electron microscopy"
  - `10.1017/s0424820100180410` score 57.3 **REJECT(I,T,C,V,P)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.471, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Yao; 1990/2020; Proceedings, annual meeting, Electron Microscopy Society of America; vol 48; "Characterization of Surface Resonance Conditions for Surface Imaging"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '4' (missing)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P26.json; B3, 2026-09-22)`

### ZLWANG96 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1017/cbo9780511525254
- Query URL: <https://api.crossref.org/works?query.bibliographic=Wang+Reflection+Electron+Microscopy+and+Spectroscopy+for+Surface+Analysis+Cambridge+University+Press+1996&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1996-5-23', 'published-online': '2010-1-18', 'issued': '1996-5-23', 'published': '1996-5-23'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1017/cbo9780511525254` score 53.3 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Wang; 1996/2010; Cambridge University Press; vol ; "Reflection Electron Microscopy and Spectroscopy for Surface Analysis"
  - `10.1017/cbo9780511525254.004` score 49.8 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.486, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Reflection high-energy electron diffraction"
  - `10.1017/cbo9780511525254.017` score 49.0 **REJECT(I,T)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.137, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Crystallographic structure systems"
  - `10.1017/cbo9780511525254.003` score 48.5 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.4, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Kinematical electron diffraction"
  - `10.1017/cbo9780511525254.014` score 48.5 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.359, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Novel techniques associated with reflection electron imaging"
  - `10.1017/cbo9780511525254.007` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.264, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Imaging surfaces in TEM"
  - `10.1017/cbo9780511525254.009` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.198, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Applications of UHV REM"
  - `10.1017/cbo9780511525254.011` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.191, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Phonon scattering in RHEED"
  - `10.1017/cbo9780511525254.008` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.342, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Contrast mechanisms of reflected electron imaging"
  - `10.1017/cbo9780511525254.004` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.486, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Reflection high-energy electron diffraction"
  - `10.1017/cbo9780511525254.001` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.16, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Preface"
  - `10.1017/cbo9780511525254.006` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.306, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Resonance reflections in RHEED"
  - `10.1017/cbo9780511525254.010` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.232, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Applications of non-UHV REM"
  - `10.1017/cbo9780511525254.002` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.15, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Introduction"
  - `10.1017/cbo9780511525254` score 0.0 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Wang; 1996/2010; Cambridge University Press; vol ; "Reflection Electron Microscopy and Spectroscopy for Surface Analysis"
  - `10.1017/cbo9780511525254.012` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.253, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Valence excitation in RHEED"
  - `10.1017/cbo9780511525254.003` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.4, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Kinematical electron diffraction"
  - `10.1017/cbo9780511525254.025` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.205, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "References"
  - `10.1017/cbo9780511525254.013` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.262, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Atomic inner shell excitations in RHEED"
  - `10.1017/cbo9780511525254.014` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.359, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Novel techniques associated with reflection electron imaging"
  - `10.1017/cbo9780511525254.005` score 0.0 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.232, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Dynamical theories of RHEED"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) (STRENGTHENED in this pass)` -> `METADATA_VERIFIED (route: Crossref API monograph record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/ZLWANG96.json; B3, 2026-09-22)`

### P30 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1038/nature07049
- Query URL: <https://api.crossref.org/works/10.1038/nature07049>  (HTTP: 200)
- Crossref dates: {'published-print': '2008-6', 'issued': '2008-6', 'published': '2008-6'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED and strengthened in this pass)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P30.json; B3, 2026-09-22)`

### P31 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.ultramic.2011.04.008
- Query URL: <https://api.crossref.org/works?query.bibliographic=H%C3%BFtch+Houdellier+H%C3%BCe+Dark-field+electron+holography+for+the+measurement+of+geometric+phase+Ultramicroscopy+111+2011+1328&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2011-7', 'issued': '2011-7', 'published': '2011-7'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2011.04.008` score 122.8 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Hÿtch; 2011; Ultramicroscopy; vol 111; "Dark-field electron holography for the measurement of geometric phase"
  - `10.1016/j.ultramic.2015.10.002` score 80.1 **REJECT(A,I,T,Y,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.562, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Denneulin; 2016; Ultramicroscopy; vol 160; "Differential phase-contrast dark-field electron holography for strain mapping"
  - `10.1007/978-3-540-85226-1_3` score 67.7 **REJECT(I,T,C,Y,V,P)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.742, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Hÿtch; ; EMC 2008 14th European Microscopy Congress 1–5 September 2008, Aachen, Germany; vol ; "Dark-field electron holography for the measurement of strain in nanostructures a"
  - `10.1007/978-3-540-85156-1_131` score 67.4 **REJECT(A,I,T,C,Y,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.488, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Houdellier; ; EMC 2008 14th European Microscopy Congress 1–5 September 2008, Aachen, Germany; vol ; "Strain determination by dark-field electron holography"
  - `10.1016/j.ultramic.2014.06.005` score 65.5 **REJECT(A,I,T,Y,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.42, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED in this pass via a publisher PII URL plus an independent bibliographic record)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P31.json; B3, 2026-09-22)`

### P32 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.ultramic.2013.07.007
- Query URL: <https://api.crossref.org/works?query.bibliographic=Lubk+Javon+Cherkashin+Dynamic+scattering+theory+for+dark-field+electron+holography+of+3D+strain+fields+Ultramicroscopy+136+2014+42&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2014-1', 'issued': '2014-1', 'published': '2014-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2013.07.007` score 129.1 **ACCEPT-5FIELD** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Lubk; 2014; Ultramicroscopy; vol 136; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1017/s1431927613008957` score 89.7 **REJECT(I,C,Y,V,P)** {'A': 'match', 'I': 'mismatch', 'T': 'match', 'T_ratio': 1.0, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Lubk; 2013; Microscopy and Microanalysis; vol 19; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1016/j.ultramic.2014.06.005` score 88.6 **REJECT(A,I,T,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.597, 'C': 'match', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
  - `10.1002/9781118579022.ch4` score 57.8 **REJECT(A,I,T,C,Y,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.636, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Hÿtch; 2012/2013; Transmission Electron Microscopy in Micro‐Nanoelectronics; vol ; "Dark‐Field Electron Holography for Strain Mapping"
  - `10.1016/j.ultramic.2014.04.002` score 56.5 **REJECT(A,I,T,V,P)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.512, 'C': 'match', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Röder; 2014; Ultramicroscopy; vol 144; "Noise estimation for off-axis electron holography"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (publisher URL added in this pass)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P32.json; B3, 2026-09-22)`

### P33 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.ultramic.2019.112844
- Query URL: <https://api.crossref.org/works?query.bibliographic=Mei%C3%9Fner+Niermann+Berger+Dynamical+diffraction+effects+on+the+geometric+phase+of+inhomogeneous+strain+fields+Ultramicroscopy+207+2019&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2019-12', 'issued': '2019-12', 'published': '2019-12'}; bib year matches: ['published-print', 'issued', 'published']
- number_is_article_number: 112844
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2019.112844` score 114.3 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Meißner; 2019; Ultramicroscopy; vol 207; "Dynamical diffraction effects on the geometric phase of inhomogeneous strain fie"
  - `10.1016/j.ultramic.2025.114122` score 72.4 **REJECT(A,T,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.5, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.1017/s1431927618005378` score 56.3 **REJECT(T,C,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.65, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Meißner; 2018; Microscopy and Microanalysis; vol 24; "Dynamical Effects on the Geometric Phase"
  - `10.22443/rms.emc2020.1137` score 41.4 **REJECT(A,T,C,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.231, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Technische Universität Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Determination of 3D strain fields by dark field electron holography utilizing dy"
  - `10.1016/j.ultramic.2019.112837` score 40.2 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.273, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Yuan; 2019; Ultramicroscopy; vol 207; "Lattice strain mapping using circular Hough transform for electron diffraction d"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P33.json; B3, 2026-09-22)`

### P34 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1038/nphoton.2011.11
- Query URL: <https://api.crossref.org/works/10.1038/nphoton.2011.11>  (HTTP: 200)
- Crossref dates: {'published-print': '2011-4', 'published-online': '2011-2-20', 'issued': '2011-2-20', 'published': '2011-2-20'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `author-count` '1 + others' vs '9 (full list available)' (incomplete); `issue` '(absent)' vs '4' (missing); `pages` '(absent)' vs '243-245' (missing)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P34.json; B3, 2026-09-22)`

### P35 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1038/ncomms1569
- Query URL: <https://api.crossref.org/works?query.bibliographic=Godard+Carbone+Allain+Three-dimensional+high-resolution+quantitative+microscopy+of+extended+crystals+Nature+Communications+2+2011&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '2011-11-29', 'issued': '2011-11-29', 'published': '2011-11-29'}; bib year matches: ['published-online', 'issued', 'published']
- number_is_article_number: 568
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1038/ncomms1569` score 84.0 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Godard; 2011; Nature Communications; vol 2; "Three-dimensional high-resolution quantitative microscopy of extended crystals"
  - `10.1038/nmat4798` score 39.1 **REJECT(A,T,C,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.417, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Hruszkewycz; 2016/2017; Nature Materials; vol 16; "High-resolution three-dimensional structural microscopy by single-angle Bragg pt"
  - `10.1021/acsphotonics.4c01106.s001` score 36.7 **REJECT(T,C,Y,V)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.349, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- -; ; American Chemical Society (ACS); vol ; "Spatiotemporal Three-Dimensional Quantitative Visualization of Macrophage Phagoc"
  - `10.1021/acsphotonics.4c01106.s002` score 36.6 **REJECT(T,C,Y,V)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.349, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- -; ; American Chemical Society (ACS); vol ; "Spatiotemporal Three-Dimensional Quantitative Visualization of Macrophage Phagoc"
  - `10.4016/5116.01` score 35.2 **REJECT(T,C,Y,V)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.486, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- -; 2008; SciVee; vol ; "High Resolution Three Dimensional Lung Reconstruction by Synchrotron Radiation X"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P35.json; B3, 2026-09-22)`

### P36 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/1.4914927
- Query URL: <https://api.crossref.org/works/10.1063/1.4914927>  (HTTP: 200)
- Crossref dates: {'published-print': '2015-3-9', 'published-online': '2015-3-12', 'issued': '2015-3-9', 'published': '2015-3-9'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P36.json; B3, 2026-09-22)`

### P37 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1038/nmat4798
- Query URL: <https://api.crossref.org/works/10.1038/nmat4798>  (HTTP: 200)
- Crossref dates: {'published-print': '2017-2', 'published-online': '2016-11-21', 'issued': '2016-11-21', 'published': '2016-11-21'}; bib year matches: ['published-print']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2' (missing)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P37.json; B3, 2026-09-22)`

### P38 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1364/optica.505478
- Query URL: <https://api.crossref.org/works?query.bibliographic=J%C3%B8rgensen+Besley+Slyamov+Hard+X-ray+grazing-incidence+ptychography%3A+large+field-of-view+nanostructure+imaging+with+ultra-high+surface+sensitivity+Optica+11+2024+197&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2024-2-20', 'published-online': '2024-2-1', 'issued': '2024-2-1', 'published': '2024-2-1'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1364/optica.505478` score 124.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Jørgensen; 2024; Optica; vol 11; "Hard x-ray grazing-incidence ptychography: large field-of-view nanostructure ima"
  - `10.1107/s2053273323083778` score 68.6 **REJECT(C,Y,V,P)** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Jørgensen; 2023; Acta Crystallographica Section A Foundations and Advances; vol 79; "Hard X-ray grazing-incidence ptychography: large field-of-view nanostructure ima"
  - `10.1117/12.3063903` score 41.4 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.377, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Sung; 2025; X-Ray Nanoimaging: Instruments and Methods VII; vol ; "Automatic differentiation for x-ray grazing-incidence surface imaging using ptyc"
  - `10.1364/optica.2.000933` score 40.2 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.197, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; 2015; Optica; vol 2; "Ultra-high-sensitivity color imaging via a transparent diffractive-filter array "
  - `10.1364/jsapo.2024.16p_a37_5` score 39.7 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.426, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Shibukawa; 2024; JSAP-Optica Joint Symposia 2024 Abstracts; vol ; "Ultra-wide field-of-view optical focusing with high-speed complex wavefront shap"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P38.json, plus the arXiv API record; B3, 2026-09-22)`

### P39 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/5.0204240
- Query URL: <https://api.crossref.org/works/10.1063/5.0204240>  (HTTP: 200)
- Crossref dates: {'published-print': '2024-6-1', 'published-online': '2024-6-26', 'issued': '2024-6-1', 'published': '2024-6-1'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P39.json, plus the arXiv API record, which carries the same DOI; B3, 2026-09-22)`

### P40 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1364/oe.591755
- Query URL: <https://api.crossref.org/works/10.1364/OE.591755>  (HTTP: 200)
- Crossref dates: {'published-print': '2026-8-10', 'published-online': '2026-8-4', 'issued': '2026-8-4', 'published': '2026-8-4'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P40.json; B3, 2026-09-22)`

### P41 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1038/s43586-025-00438-3
- Query URL: <https://api.crossref.org/works/10.1038/s43586-025-00438-3>  (HTTP: 200)
- Crossref dates: {'published-online': '2025-10-30', 'issued': '2025-10-30', 'published': '2025-10-30'}; bib year matches: ['published-online', 'issued', 'published']
- number_is_article_number: 68
- type: journal-article
- Discrepancies (baseline vs record): `author-count` '3 + others' vs '10 (full list available)' (incomplete)
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P41.json; B3, 2026-09-22)`

### P47 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/1.1715155
- Query URL: <https://api.crossref.org/works/10.1063/1.1715155>  (HTTP: 200)
- Crossref dates: {'published-print': '2004-4-26', 'issued': '2004-4-26', 'published': '2004-4-26'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P47.json; B3, 2026-09-22)`

### P45 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/1.4737152
- Query URL: <https://api.crossref.org/works/10.1063/1.4737152>  (HTTP: 200)
- Crossref dates: {'published-print': '2012-7-23', 'issued': '2012-7-23', 'published': '2012-7-23'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P45.json; B3, 2026-09-22)`

### P46 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2013.11.002
- Query URL: <https://api.crossref.org/works/10.1016/j.ultramic.2013.11.002>  (HTTP: 200)
- Crossref dates: {'published-print': '2014-2', 'issued': '2014-2', 'published': '2014-2'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P46.json; B3, 2026-09-22)`

### P42 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1093/jmicro/dfaa055
- Query URL: <https://api.crossref.org/works?query.bibliographic=Blackburn+McLeod+Practical+implementation+of+high-resolution+electron+ptychography+and+comparison+with+off-axis+electron+holography+Microscopy+70+2021+131&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2021-2-1', 'published-online': '2020-8-27', 'issued': '2020-8-27', 'published': '2020-8-27'}; bib year matches: ['published-print']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1093/jmicro/dfaa055` score 116.8 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Blackburn; 2020/2021; Microscopy; vol 70; "Practical implementation of high-resolution electron ptychography and comparison"
  - `10.1007/978-1-4615-4817-1_9` score 57.6 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.557, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Rau; 1999; Introduction to Electron Holography; vol ; "High Resolution Off-Axis Electron Holography"
  - `10.22443/rms.emc2020.283` score 57.3 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.297, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Humboldt-Universität zu Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Comparison of off-axis electron holography, differential phase contrast, 4D STEM"
  - `10.22443/rms.emc2020.350` score 52.8 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.502, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Bhat; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Quantitative counting of Zn and O atoms by atomic resolution off-axis and in-lin"
  - `10.1201/9781482289510-124` score 50.8 **REJECT(T,C,Y,V,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.273, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- -; 2001; Electron Microscopy and Analysis 2001; vol ; "Off-axis electron holography of nanomagnet arrays fabricated by interferometric "
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P42.json; B3, 2026-09-22)`

### P43 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.micron.2022.103317
- Query URL: <https://api.crossref.org/works/10.1016/j.micron.2022.103317>  (HTTP: 200)
- Crossref dates: {'published-print': '2022-9', 'issued': '2022-9', 'published': '2022-9'}; bib year matches: ['published-print', 'issued', 'published']
- number_is_article_number: 103317
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/P43.json; B3, 2026-09-22)`

### P44 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1093/jmicro/dfaa066
- Query URL: <https://api.crossref.org/works?query.bibliographic=Herring+Phase+imaging+dislocations+using+diffracted+beam+interferometry+Microscopy+70+2021&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2021-6-6', 'published-online': '2020-12-2', 'issued': '2020-12-2', 'published': '2020-12-2'}; bib year matches: ['published-print']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1093/jmicro/dfaa066` score 87.2 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Herring; 2020/2021; Microscopy; vol 70; "Phase imaging dislocations using diffracted beam interferometry"
  - `10.1093/jmicro/dfn027` score 52.2 **REJECT(T,C,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.612, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2009; Journal of Electron Microscopy; vol 58; "Electron beam coherence measurements using diffracted beam interferometry/hologr"
  - `10.1017/s1431927607073825` score 51.0 **REJECT(T,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.613, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2007; Microscopy and Microanalysis; vol 13; "Planar Diffracted-beam Interferometry/Holography"
  - `10.1017/s1431927607073886` score 49.5 **REJECT(T,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.497, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2007; Microscopy and Microanalysis; vol 13; "Coherence Property Measurements of Plasmons and Phonons using Planar Diffracted "
  - `10.1016/j.micron.2022.103317` score 45.7 **REJECT(T,C,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.37, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2022; Micron; vol 160; "Diffracted beam interferometry – Differential phase contrast image of an amorpho"
- Discrepancies (baseline vs record): `pages` '(absent)' vs '297-301' (missing)
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P44.json; B3, 2026-09-22)`

### P51 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1103/physrevresearch.5.033137
- Query URL: <https://api.crossref.org/works?query.bibliographic=Subakti+Daqiqshirazi+Wolf+Electron+holographic+mapping+of+structural+and+electronic+reconstruction+at+mono-+and+bilayer+steps+of+h-BN+Physical+Review+Research+5+2023+033137&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '2023-8-28', 'issued': '2023-8-28', 'published': '2023-8-28'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/physrevresearch.5.033137` score 86.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 0.924, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Subakti; 2023; Physical Review Research; vol 5; "Electron holographic mapping of structural reconstruction at mono- and bilayer s"
  - `10.32657/10356/199668` score 35.2 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.5, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; ; Nanyang Technological University; vol ; "Engineering moiré superlattices: structural and electronic properties of twisted"
  - `10.33612/diss.1276909022` score 35.2 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.5, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; ; University of Groningen Press; vol ; "Engineering Moiré Superlattices: Structural and Electronic Properties of Twisted"
  - `10.1103/physrevb.71.132503` score 32.0 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.435, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Arita; 2005; Physical Review B; vol 71; "Electronic structure of sodium cobalt oxide: Comparing mono- and bilayer hydrate"
  - `10.1103/physrevb.108.125126` score 30.3 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.367, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Zollner; 2023; Physical Review B; vol 108; "Electronic and spin-orbit properties of  h -BN encapsulated bilayer graphene"
- Discrepancies (baseline vs record): `author[1].given` '(none)' vs 'Subakti' (given-missing); `title` 'Electron holographic mapping of structural and electronic reconstruction at mono- and bilayer steps of h-BN' vs 'Electron holographic mapping of structural reconstruction at mono- and bilayer steps of  h−BN' (ratio=0.92); `issue` '(absent)' vs '3' (missing)
- Remaining differences (current vs record): `author[1].given` '(none)' vs 'Subakti' -- kept: mononym "Subakti"; the record repeats it as given and family name
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/P51.json, plus the arXiv API record; B3, 2026-09-22)`

### P49 -- VERIFIED-CORRECTED

- Route: arXiv API record of 2306.00271
- Query URL: <https://api.crossref.org/works?query.bibliographic=Kudo+A+fast+and+accurate+computation+method+for+reflective+diffraction+simulations+2023&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.cpc.2023.109029` score 51.3 **REJECT(Y)** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 0.916, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- Kudo; 2024; Computer Physics Communications; vol 296; "A fast and efficient computation method for reflective diffraction simulations"
  - `10.1021/acs.langmuir.5c00924.s001` score 32.8 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.623, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- -; ; American Chemical Society (ACS); vol ; "A Fast and Accurate Method for Contact Angle Calculation via Molecular Dynamic S"
  - `10.1021/acs.jctc.3c00674.s002` score 31.9 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.431, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- -; ; American Chemical Society (ACS); vol ; "RPA, an Accurate and Fast Method for the Computation of Static Nonlinear Optical"
  - `10.1021/acs.jctc.3c00674.s001` score 31.8 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.431, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- -; ; American Chemical Society (ACS); vol ; "RPA, an Accurate and Fast Method for the Computation of Static Nonlinear Optical"
  - `10.1109/ultsym.1986.198701` score 31.0 **REJECT(A,I,T,Y)** {'A': 'mismatch', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.62, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- Flory; 1986; IEEE 1986 Ultrasonics Symposium; vol ; "Fast and accurate computation of SAW diffraction effects using asymptotic expans"
- Publisher-page / registry result: Title as in the bib; authors Shuhei Kudo, Yusaku Yamamoto, Takeo Hoshi; submitted 2023-06-01; no DOI or journal_ref in the arXiv record. Journal version found in Crossref (CPC 296, 2024; PII match) but not merged (year).
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index); TITLE OF THE JOURNAL VERSION UNVERIFIED` -> `METADATA_VERIFIED (route: arXiv API record of 2306.00271, cached as docs/agent_reports/crossref_cache/P49.arxiv.xml; B3, 2026-09-22) -- preprint`

### SIMTRHEPD -- VERIFIED-UNCHANGED

- Route: README at raw.githubusercontent.com/sim-trhepd-rheed/sim-trhepd-rheed/main/README.md
- Query URL: <https://raw.githubusercontent.com/sim-trhepd-rheed/sim-trhepd-rheed/main/README.md>  (HTTP: 200)
- Publisher-page / registry result: README names Takashi Hanada (original author) and Takeo Hoshi (maintainer); cites SIMTRHEPD-CPC as ref. [1] with the article title now in the bib.
- Label: `SECTION_READ (of the README only)` -> `SECTION_READ (of the README only, B_literature.md) + METADATA_VERIFIED (route: README re-fetched at raw.githubusercontent.com, HTTP 200; B3, 2026-09-22)`

### SIMTRHEPD-CPC -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.cpc.2022.108371
- Query URL: <https://api.crossref.org/works/10.1016/j.cpc.2022.108371>  (HTTP: 200)
- Crossref dates: {'published-print': '2022-8', 'issued': '2022-8', 'published': '2022-8'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `SECTION_READ (of the citing README)` -> `METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/SIMTRHEPD-CPC.json; B3, 2026-09-22) + SECTION_READ (of the citing README)`

### HANADA95 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1103/physrevb.51.13320
- Query URL: <https://api.crossref.org/works?query.bibliographic=Hanada+Daimon+Ino+Physical+Review+B+51+1995+13320&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '1995-5-15', 'issued': '1995-5-15', 'published': '1995-5-15'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/physrevb.51.13320` score 53.7 **ACCEPT-SUBSTITUTED(T<-P)** {'A': 'match', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Hanada; 1995; Physical Review B; vol 51; "Rocking-curve analysis of reflection high-energy electron diffraction from the S"
  - `10.1016/0039-6028(94)91162-2` score 31.5 **REJECT(C,Y,V,P)** {'A': 'match', 'T': 'untestable', 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Hanada; 1994; Surface Science; vol 313; "Study of the Si(111)7 × 7 surface by RHEED rocking curve analysis"
  - `10.1143/jpsj.53.1911` score 30.9 **REJECT(A,C,Y,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ino; 1984; Journal of the Physical Society of Japan; vol 53; "New Models for the 7 ×7, 5 ×5, 2 ×8 Structures on Si(111) and Ge(111) Surfaces"
  - `10.1103/physrevlett.75.669` score 30.8 **REJECT(A,C,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Yamanaka; 1995; Physical Review Letters; vol 75; "Electron Standing Wave at a Surface during Reflection High Energy Electron Diffr"
  - `10.1016/0167-2584(89)90019-4` score 27.9 **REJECT(A,C,Y,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Daimon; 1989; Surface Science Letters; vol 221; "Study of Si(111)-Al surface structure by kinetic-energy dependence of polar-angl"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '19' (missing)
- Remaining differences (current vs record): `title` 'Rocking-curve analysis of reflection high-energy electron diffraction from the Si(111)-($\sqrt3\times\sqrt3$)$R30^\circ$-Al, -Ga, and -In surfaces' vs 'Rocking-curve analysis of reflection high-energy electron diffraction from the Si(111)-(√3 × √3 )R30°-Al, -Ga, and -In surfaces' -- kept: LaTeX transcription of the record title (square roots, times sign and degree sign typeset in math mode)
- Label: `SECTION_READ (of the citing README)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted with the first page standing in for the placeholder title, cached as docs/agent_reports/crossref_cache/HANADA95.json; B3, 2026-09-22) + SECTION_READ (of the citing README)`

### ABTEM -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.12688/openreseurope.13015.2
- Query URL: <https://api.crossref.org/works/10.12688/openreseurope.13015.2>  (HTTP: 200)
- Crossref dates: {'published-online': '2021-5-21', 'issued': '2021-5-21', 'published': '2021-5-21'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `SECTION_READ (of the citing README)` -> `SECTION_READ (of the citing README) + METADATA_VERIFIED (route: Crossref API /works record of the doi field, cached as docs/agent_reports/crossref_cache/ABTEM.json; B3, 2026-09-22)`

### RHEEDIUM -- VERIFIED-CORRECTED

- Route: DataCite API (Crossref /works gives 404; doi.org/ra reports DataCite)
- Query URL: <https://api.crossref.org/works/10.5281/zenodo.14757400>  (HTTP: 404)
- Publisher-page / registry result: Creator Debangshu Mukherjee; title "dxm447/rheedium: Basic Unit Cell Operations"; Zenodo 2025; version 2025.01.24. Title, version and publisher set from this record.
- Label: `SECTION_READ (of the README only)` -> `SECTION_READ (of the README only, B_literature.md) + METADATA_VERIFIED (route: DataCite record of the doi field -- Crossref /works returns 404 because the registration agency is DataCite -- cached as docs/agent_reports/crossref_cache/RHEEDIUM.datacite.json; B3, 2026-09-22)`

### PYMULTISLICE -- VERIFIED-UNCHANGED

- Route: README at raw.githubusercontent.com/HamishGBrown/py_multislice/master/README.md
- Query URL: <https://raw.githubusercontent.com/HamishGBrown/py_multislice/master/README.md>  (HTTP: 200)
- Publisher-page / registry result: Repository exists; README carries a Zenodo badge but no citation byline. No field changed.
- Label: `SECTION_READ (of the README only)` -> `SECTION_READ (of the README only, B_literature.md) + METADATA_VERIFIED (route: README re-fetched at raw.githubusercontent.com, HTTP 200; B3, 2026-09-22)`

### BLACKBURN14 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.ultramic.2013.08.009
- Query URL: <https://api.crossref.org/works?query.bibliographic=Blackburn+Loudon+Vortex+beam+production+and+contrast+enhancement+from+a+magnetic+spiral+phase+plate+Ultramicroscopy+136+2014+127&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2014-1', 'issued': '2014-1', 'published': '2014-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2013.08.009` score 122.1 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Blackburn; 2014; Ultramicroscopy; vol 136; "Vortex beam production and contrast enhancement from a magnetic spiral phase pla"
  - `10.1017/s1431927613007836` score 70.1 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.676, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Blackburn; 2013; Microscopy and Microanalysis; vol 19; "Production of Vortex Beam Modes from a Magnetic Spiral Phase Plate"
  - `10.1016/j.ultramic.2013.09.004` score 43.2 **REJECT(A,T,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.309, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Edgcombe; 2014; Ultramicroscopy; vol 136; "Imaging of weak phase objects by a Zernike phase plate"
  - `10.1016/j.ultramic.2017.07.006` score 42.7 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.577, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Minoda; 2017; Ultramicroscopy; vol 182; "Contrast enhancement of nanomaterials using phase plate STEM"
  - `10.1016/j.ultramic.2012.02.004` score 40.8 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.629, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Malac; 2012; Ultramicroscopy; vol 118; "Convenient contrast enhancement by a hole-free phase plate"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search and accepted on the five-field rule, cached as docs/agent_reports/crossref_cache/BLACKBURN14.json; B3, 2026-09-22)`

### U01 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0039-6028(93)90062-o
- Query URL: <https://api.crossref.org/works?query.bibliographic=McCoy+Maksym+Simulation+of+high-resolution+REM+images+Surface+Science&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1993-12', 'issued': '1993-12', 'published': '1993-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(93)90062-o` score 70.3 **ACCEPT-SUBSTITUTED(Y,V<-I)** {'A': 'match', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- McCoy; 1993; Surface Science; vol 298; "Simulation of high-resolution REM images"
  - `10.1016/0039-6028(93)90254-h` score 53.6 **REJECT(I,T)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.468, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- McCoy; 1993; Surface Science; vol 297; "Simulation of reflection electron microscopy images: application to high-resolut"
  - `10.1016/0039-6028(94)91386-2` score 49.1 **REJECT(I,T)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.419, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- McCoy; 1994; Surface Science; vol 310; "Multiple scattering calculations of step contrast in REM images of the Si(001) s"
  - `10.1016/s0039-6028(96)01284-8` score 42.3 **REJECT(I,T)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.471, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- McCoy; 1997; Surface Science; vol 375; "Dynamical calculation of high-resolution reflection electron microscopy lattice "
  - `10.1016/0039-6028(91)90806-4` score 37.7 **REJECT(I,T)** {'A': 'match', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.383, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- McCoy; 1991; Surface Science; vol 257; "Monte Carlo simulation of equilibrium thermal roughening of the Ge(001)2 × 1 sur"
- Discrepancies (baseline vs record): `title` 'Simulation of high-resolution REM images (title as displayed in the search index)' vs 'Simulation of high-resolution REM images' (ratio=0.67); `volume` '(absent)' vs '298' (missing); `issue` '(absent)' vs '2-3' (missing); `pages` '(absent)' vs '468-472' (missing); `year` '(absent)' vs 'published-print 1993-12; issued 1993-12; published 1993-12' (missing)
- Label: `UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted by identifier substitution -- the ScienceDirect PII 003960289390062O recorded in B2 equals the record's PII, standing in for the year and volume the entry lacked -- cached as docs/agent_reports/crossref_cache/U01.json; B3, 2026-09-22)`

### U02 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/0039-6028(93)90043-j
- Query URL: <https://api.crossref.org/works?query.bibliographic=Dynamical+theory+of+RHEED+from+stepped+surfaces+Surface+Science&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1993-12', 'issued': '1993-12', 'published': '1993-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(93)90043-j` score 60.9 **ACCEPT-SUBSTITUTED(A,Y,V<-I)** {'A': 'untestable', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- Beeby; 1993; Surface Science; vol 298; "Dynamical theory of RHEED from stepped surfaces"
  - `10.1016/s0039-6028(87)80131-0` score 49.2 **REJECT(I,T)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.628, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- Ichimiya; 1987; Surface Science; vol 187; "Rheed intensities from stepped surfaces"
  - `10.1016/0167-2584(87)90877-2` score 48.3 **REJECT(I,T)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.628, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- Ichimiya; 1987; Surface Science Letters; vol 187; "RHEED intensities from stepped surfaces"
  - `10.1016/0039-6028(85)90724-1` score 47.3 **REJECT(I,T)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.378, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- Kawamura; 1985; Surface Science; vol 161; "RHEED from stepped surfaces and its relation to RHEED intensity oscillations obs"
  - `10.1016/0167-2584(85)90509-2` score 46.7 **REJECT(I,T)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.378, 'C': 'match', 'Y': 'untestable', 'V': 'untestable'} -- Kawamura; 1985; Surface Science Letters; vol 161; "Rheed from stepped surfaces and its relation to rheed intensity oscillations obs"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Beeby, J.L.' (missing); `volume` '(absent)' vs '298' (missing); `issue` '(absent)' vs '2-3' (missing); `pages` '(absent)' vs '307-315' (missing); `year` '(absent)' vs 'published-print 1993-12; issued 1993-12; published 1993-12' (missing)
- Label: `UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted by identifier substitution -- the ScienceDirect PII 003960289390043J recorded in B2 equals the record's PII, standing in for the author, year and volume the entry lacked -- cached as docs/agent_reports/crossref_cache/U02.json; B3, 2026-09-22)`

### U03 -- VERIFIED-CORRECTED

- Route: Google Patents record of US 10,755,892 B2
- Query URL: <https://patents.google.com/patent/US10755892B2/en>  (HTTP: 200 (the A-suffixed URL tried first did not resolve))
- Publisher-page / registry result: Inventor Weijie Huang; assignee KLA Tencor Corp (now KLA Corp); filed 2019-05-15; issued 2020-08-25.
- Label: `UNVERIFIED` -> `METADATA_VERIFIED (route: Google Patents record https://patents.google.com/patent/US10755892B2/en, HTTP 200; B3, 2026-09-22); DESCRIPTION NOT READ`

### U04 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1103/physrevb.38.1172
- Query URL: <https://api.crossref.org/works?query.bibliographic=Zhao+Poon+Tong+Physical+Review+B+38+1988+1172&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '1988-7-15', 'issued': '1988-7-15', 'published': '1988-7-15'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/physrevb.38.1172` score 45.0 **ACCEPT-SUBSTITUTED(T<-P)** {'A': 'match', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Zhao; 1988; Physical Review B; vol 38; "Invariant-embeddingR-matrix scheme for reflection high-energy electron diffracti"
  - `10.1103/physrevb.38.5332` score 26.9 **REJECT(A,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Shen; 1988; Physical Review B; vol 38; "Stability and formation of Al-Cu-(Li,Mg) icosahedral phases"
  - `10.1103/physreva.38.1172` score 26.4 **REJECT(A,C)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Padial; 1988; Physical Review A; vol 38; "Impact broadening of thedtμformation resonances"
  - `10.1016/0375-9601(88)90128-4` score 25.7 **REJECT(A,C,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Tong; 1988; Physics Letters A; vol 128; "Multiple scattering analysis of reflection high-energy electron diffraction inte"
  - `10.1086/ahr/93.4.1172-b` score 25.6 **REJECT(C,V)** {'A': 'untestable', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'match'} -- -; 1988; The American Historical Review; vol 93; "Erratum"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2' (missing); `pages` '1172' vs '1172-1182' (last-page-missing)
- Remaining differences (current vs record): `title` 'Invariant-embedding $R$-matrix scheme for reflection high-energy electron diffraction' vs 'Invariant-embeddingR-matrix scheme for reflection high-energy electron diffraction' -- kept: the record itself has no space before the italic R ("Invariant-embedding<i>R</i>-matrix"); the bib keeps the space
- Label: `METADATA_VERIFIED(index, single) for the citation string; TITLE UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted with the first page standing in for the placeholder title, cached as docs/agent_reports/crossref_cache/U04.json; B3, 2026-09-22)`

### U05 -- VERIFIED-CORRECTED

- Route: Crossref API chapter records of ISBN 9780444820518 (no book-level record)
- Query URL: <https://api.crossref.org/works?query.bibliographic=Tonomura+Allard+Pozzi+Electron+Holography+International+Workshop+on+Electron+Holography+Elsevier+1995&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/b978-044482051-8/50000-2` score 80.0 **REJECT(T)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.154, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Tonomura; 1995; Electron Holography; vol ; "Preface"
  - `10.1016/b978-044482051-8/50014-2` score 67.8 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.384, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Bonevich; 1995; Electron Holography; vol ; "Magnetic field observation of vortices in superconductors by electron holography"
  - `10.1007/978-1-4615-4817-1_7` score 67.2 **REJECT(A,T,C,Y)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.594, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Bonevich; 1999; Introduction to Electron Holography; vol ; "Electron Holography of Electromagnetic Fields"
  - `10.1016/b978-044482051-8/50011-7` score 64.9 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.792, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Völkl; 1995; Electron Holography; vol ; "Practical Electron Holography"
  - `10.1016/b978-044482051-8/50025-7` score 62.9 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.447, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Matsumoto; 1995; Electron Holography; vol ; "Fraunhofer in-line electron holography of small weak-phase objects"
  - `10.1016/b978-044482051-8/50008-7` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.34, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Lehmann; 1995; Electron Holography; vol ; "Holographic Reconstruction Methods"
  - `10.1016/b978-044482051-8/50029-4` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.197, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Herring; 1995; Electron Holography; vol ; "Modeling of convergent beam interferometry"
  - `10.1016/b978-044482051-8/50019-1` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.691, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- McCartney; 1995; Electron Holography; vol ; "Electron holography of p-n junctions"
  - `10.1016/b978-044482051-8/50036-1` score 0.0 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.154, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1995; Electron Holography; vol ; "List of participants"
  - `10.1016/b978-044482051-8/50021-x` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.644, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Lin; 1995; Electron Holography; vol ; "Electron Holography in Materials Science"
  - `10.1016/b978-044482051-8/50023-3` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.494, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Libera; 1995; Electron Holography; vol ; "Transmission Electron Holography of Polymer Microstructure"
  - `10.1016/b978-044482051-8/50016-6` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.507, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Matteucci; 1995; Electron Holography; vol ; "Electron holography of magnetic and electric microfields"
  - `10.1016/b978-044482051-8/50015-4` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.234, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Hirayama; 1995; Electron Holography; vol ; "Holographic studies on magnetic phenomena in small regions"
  - `10.1016/b978-044482051-8/50011-7` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.792, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Völkl; 1995; Electron Holography; vol ; "Practical Electron Holography"
  - `10.1016/b978-044482051-8/50032-4` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.441, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Ishizuka; 1995; Electron Holography; vol ; "High-resolution tilted single-sideband holography"
  - `10.1016/b978-044482051-8/50014-2` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.384, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Bonevich; 1995; Electron Holography; vol ; "Magnetic field observation of vortices in superconductors by electron holography"
  - `10.1016/b978-044482051-8/50020-8` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.585, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Datye; 1995; Electron Holography; vol ; "Electron Holography of Heterogeneous Catalysts"
  - `10.1016/b978-044482051-8/50034-8` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.667, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Ru; 1995; Electron Holography; vol ; "Amplitude-division electron holography"
  - `10.1016/b978-044482051-8/50018-x` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.5, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Smith; 1995; Electron Holography; vol ; "Quantitative applications of off-axis electron holography"
  - `10.1016/b978-044482051-8/50035-x` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.409, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Joy; 1995; Electron Holography; vol ; "The First International Workshop on Electron Holography - Concluding Remarks -"
  - `10.1016/b978-044482051-8/50013-0` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.13, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Pozzi; 1995; Electron Holography; vol ; "Interference- and Lorentz-Image Simulations of Vortices in Superconductors"
  - `10.1016/b978-044482051-8/50005-1` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.458, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Ade; 1995; Electron Holography; vol ; "Digital recording and processing in electron off-axis holography"
  - `10.1016/b978-044482051-8/50028-2` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.603, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Steeds; 1995; Electron Holography; vol ; "Coherent electron diffraction and holography"
  - `10.1016/b978-044482051-8/50010-5` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.644, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Lai; 1995; Electron Holography; vol ; "Electron Holographic Computed Tomography"
  - `10.1016/b978-044482051-8/50024-5` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.45, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Aoyama; 1995; Electron Holography; vol ; "Electron holographic observation of thin biological filaments"
  - `10.1016/b978-044482051-8/50030-0` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.197, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Van Dyck; 1995; Electron Holography; vol ; "Interpreting the reconstructed object wave"
  - `10.1016/b978-044482051-8/50000-2` score 0.0 **REJECT(T)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.154, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Tonomura; 1995; Electron Holography; vol ; "Preface"
  - `10.1016/b978-044482051-8/50025-7` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.447, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Matsumoto; 1995; Electron Holography; vol ; "Fraunhofer in-line electron holography of small weak-phase objects"
  - `10.1016/b978-044482051-8/50009-9` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.494, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Chen; 1995; Electron Holography; vol ; "Real-time electron holography using a liquid-crystal panel"
  - `10.1016/b978-044482051-8/50027-0` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.366, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Spence; 1995; Electron Holography; vol ; "On the reconstruction of low voltage point projection holograms"
  - `10.1016/b978-044482051-8/50007-5` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.567, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Ru; 1995; Electron Holography; vol ; "Phase-shifting techniques in electron holography"
  - `10.1016/b978-044482051-8/50002-6` score 0.0 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.138, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1995; Electron Holography; vol ; "Committees"
  - `10.1016/b978-044482051-8/50004-x` score 0.0 **REJECT(A)** {'A': 'mismatch', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Lichte; 1995; Electron Holography; vol ; "Electron Holography"
  - `10.1016/b978-044482051-8/50026-9` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.551, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Fink; 1995; Electron Holography; vol ; "State of the Art of Low-Energy Electron Holography"
  - `10.1016/b978-044482051-8/50033-6` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.429, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Mankos; 1995; Electron Holography; vol ; "STEM Holography of Magnetic Materials"
  - `10.1016/b978-044482051-8/50031-2` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.261, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Op de Beeck; 1995; Electron Holography; vol ; "Focal Series Wave Function Reconstruction in HRTEM"
  - `10.1016/b978-044482051-8/50006-3` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.469, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Tanji; 1995; Electron Holography; vol ; "Observation of atomic surface potential by electron holography"
  - `10.1016/b978-044482051-8/50003-8` score 0.0 **REJECT(T)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.373, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Tonomura; 1995; Electron Holography; vol ; "Progress in Holographic Interference Electron Microscopy"
  - `10.1016/b978-044482051-8/50022-1` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.463, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Allard; 1995; Electron Holography; vol ; "Electron Holography Applied to the Study of Fullerene Materials"
  - `10.1016/b978-044482051-8/50001-4` score 0.0 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.25, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1995; Electron Holography; vol ; "Photo"
  - `10.1016/b978-044482051-8/50037-3` score 0.0 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.258, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 1995; Electron Holography; vol ; "Author index"
  - `10.1016/b978-044482051-8/50012-9` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.186, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Scheerschmidt; 1995; Electron Holography; vol ; "Retrieval of atomic displacements from reconstructed electron waves as an ill-po"
  - `10.1016/b978-044482051-8/50017-8` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.377, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Frost; 1995; Electron Holography; vol ; "Holography of electrostatic fields"
- Discrepancies (baseline vs record): none
- Publisher-page / registry result: 38 items; Preface by Tonomura, Allard, Pozzi, Joy, Ono; Elsevier 1995; no Osakabe chapter.
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED (route: Crossref API chapter records of ISBN 9780444820518, cached as docs/agent_reports/crossref_cache/U05.isbn.json; B3, 2026-09-22)`

### U06 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Osakabe+1995&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1007/bf00032674` score 20.5 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Osakabe; 1995; Plant Molecular Biology; vol 28; "Characterization of the structure and determination of mRNA levels of the phenyl"
  - `10.1093/benz/9780199773787.article.b00133760` score 18.9 **REJECT(Y)** {'A': 'untestable', 'T': 'untestable', 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- -; 2011; Benezit Dictionary of Artists; vol ; "Osakabe, Tatsuo"
  - `10.1002/9780470015902.a0001319.pub2` score 18.3 **REJECT(Y)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- Osakabe; 2012; Encyclopedia of Life Sciences; vol ; "Plant Light Stress"
  - `10.1080/00150199508217339` score 18.3 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Horiuchi; 1995; Ferroelectrics; vol 169; "Nonlinear optical properties of new ferroelectric LaBGeO5"
  - `10.1063/1.1146208` score 17.8 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Isobe; 1995; Review of Scientific Instruments; vol 66; "Absolute calibration of neutron counters on the Compact Helical System"
- Label: `UNVERIFIED -- DO NOT CITE` -> `UNVERIFIED -- DO NOT CITE (B3: contradicted by the Crossref contents list of [U05])`

### U07 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1007/978-1-4615-4817-1_13
- Query URL: <https://api.crossref.org/works?query.bibliographic=V%C3%B6lkl+Allard+Joy+Electron+Holography+using+Diffracted+Electron+Beams+%28DBH%29+Introduction+to+Electron+Holography+Springer%2FPlenum+1999&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1999', 'issued': '1999', 'published': '1999'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer/Plenum' vs Crossref 'Springer US'
- type: book-chapter
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1007/978-1-4615-4817-1_13` score 106.2 **ACCEPT-SUBSTITUTED(A<-I)** {'A': 'untestable', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Herring; 1999; Introduction to Electron Holography; vol ; "Electron Holography Using Diffracted Electron Beams (DBH)"
  - `10.1007/978-1-4615-4817-1` score 93.3 **REJECT(T,C)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.422, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a'} -- Völkl; 1999; Springer US; vol ; "Introduction to Electron Holography"
  - `10.1007/978-1-4615-4817-1_3` score 87.9 **REJECT(T)** {'A': 'untestable', 'I': 'match', 'T': 'mismatch', 'T_ratio': 0.487, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Allard; 1999; Introduction to Electron Holography; vol ; "Optical Characteristics of an Holography Electron Microscope"
  - `10.1016/b978-044482051-8/50017-8` score 83.4 **REJECT(I,T,C,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.517, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Frost; 1995; Electron Holography; vol ; "Holography of electrostatic fields"
  - `10.1016/b978-044482051-8/50011-7` score 80.1 **REJECT(I,T,C,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.452, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Völkl; 1995; Electron Holography; vol ; "Practical Electron Holography"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Herring, R. A. and Pozzi, G.' (missing); `pages` '(absent)' vs '295-310' (missing)
- Label: `chapter TITLE and NUMBER METADATA_VERIFIED(index) (it is chapter 13 of [B09], from the chapter-title list B_literature.md section 7 obtained); AUTHORS AND PAGES UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API book-chapter record found by bibliographic search, accepted by identifier substitution -- the chapter record carries the ISBNs of the verified parent book [B09] and its exact title, standing in for the author the entry lacked -- cached as docs/agent_reports/crossref_cache/U07.json; B3, 2026-09-22)`

### U08 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.ultramic.2014.06.005
- Query URL: <https://api.crossref.org/works?query.bibliographic=Dynamical+effects+in+strain+measurements+by+dark-field+electron+holography+Ultramicroscopy+2014&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2014-12', 'issued': '2014-12', 'published': '2014-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2014.06.005` score 66.8 **ACCEPT-SUBSTITUTED(A,V<-I)** {'A': 'untestable', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'untestable'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
  - `10.1016/j.ultramic.2025.114122` score 59.6 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.589, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.1016/j.ultramic.2013.07.007` score 51.1 **REJECT(I,T)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.61, 'C': 'match', 'Y': 'match', 'V': 'untestable'} -- Lubk; 2014; Ultramicroscopy; vol 136; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1016/j.ultramic.2015.10.002` score 50.8 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.596, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Denneulin; 2016; Ultramicroscopy; vol 160; "Differential phase-contrast dark-field electron holography for strain mapping"
  - `10.1016/j.ultramic.2010.11.030` score 50.4 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.472, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Béché; 2011; Ultramicroscopy; vol 111; "Dark field electron holography for strain measurement"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Javon, E. and Lubk, A. and Cours, R. and Reboh, S. and Cherkashin, N. and Houdellier, F. and Gatel, C. and H{\"y}tch, M.J.' (missing); `volume` '(absent)' vs '147' (missing); `pages` '(absent)' vs '70-85' (missing)
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted by identifier substitution -- ScienceDirect PII S0304399114001211 recorded in B_literature.md equals the record's PII, standing in for the authors and volume the entry lacked -- cached as docs/agent_reports/crossref_cache/U08.json; B3, 2026-09-22)`

### U09 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.ultramic.2015.10.002
- Query URL: <https://api.crossref.org/works?query.bibliographic=Differential+phase-contrast+dark-field+electron+holography+for+strain+mapping+Ultramicroscopy+2016&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2016-1', 'issued': '2016-1', 'published': '2016-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2015.10.002` score 82.8 **ACCEPT-SUBSTITUTED(A,V<-I)** {'A': 'untestable', 'I': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'untestable'} -- Denneulin; 2016; Ultramicroscopy; vol 160; "Differential phase-contrast dark-field electron holography for strain mapping"
  - `10.1016/j.ultramic.2012.07.010` score 52.0 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.443, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Song; 2013; Ultramicroscopy; vol 127; "Strain mapping of LED devices by dark-field inline electron holography: Comparis"
  - `10.1016/j.ultramic.2010.11.030` score 50.5 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.692, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Béché; 2011; Ultramicroscopy; vol 111; "Dark field electron holography for strain measurement"
  - `10.1016/j.ultramic.2021.113225` score 49.4 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.373, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Pofelski; 2021; Ultramicroscopy; vol 223; "Assessment of the strain depth sensitivity of Moiré sampling Scanning Transmissi"
  - `10.1016/j.ultramic.2025.114122` score 48.2 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.436, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Denneulin, Thibaud and Houdellier, Florent and H{\"y}tch, Martin' (missing); `volume` '(absent)' vs '160' (missing); `pages` '(absent)' vs '98-109' (missing)
- Label: `METADATA_VERIFIED(index, single), strengthened only in that a PubMed record URL carrying the exact title was seen in this pass; AUTHORS UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted by identifier substitution -- ScienceDirect PII S0304399115300413 recorded in B_literature.md equals the record's PII, standing in for the authors and volume the entry lacked -- cached as docs/agent_reports/crossref_cache/U09.json; B3, 2026-09-22)`

### U10 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1016/j.ultramic.2025.114122
- Query URL: <https://api.crossref.org/works?query.bibliographic=Dynamical+diffraction+effects+of+inhomogeneous+strain+fields+investigated+by+scanning+CBED+and+dark-field+electron+holography+Ultramicroscopy+2025&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2025-5', 'issued': '2025-5', 'published': '2025-5'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2025.114122` score 104.9 **ACCEPT-SUBSTITUTED(A,V<-I)** {'A': 'untestable', 'I': 'match', 'T': 'match', 'T_note': 'near match accepted because the bib-recorded PII/ISBN matches', 'T_ratio': 0.887, 'C': 'match', 'Y': 'match', 'V': 'untestable'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.22443/rms.emc2020.1137` score 58.7 **REJECT(I,T,C,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.527, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'untestable'} -- Technische Universität Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Determination of 3D strain fields by dark field electron holography utilizing dy"
  - `10.1016/j.ultramic.2019.112844` score 57.6 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.577, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Meißner; 2019; Ultramicroscopy; vol 207; "Dynamical diffraction effects on the geometric phase of inhomogeneous strain fie"
  - `10.1016/j.ultramic.2014.06.005` score 56.2 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.663, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
  - `10.1016/j.ultramic.2013.03.014` score 55.3 **REJECT(I,T,Y)** {'A': 'untestable', 'I': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.431, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Béché; 2013; Ultramicroscopy; vol 131; "Strain measurement at the nanoscale: Comparison between convergent beam electron"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Niermann, L. and Niermann, T. and Lehmann, M.' (missing); `title` 'Dynamical diffraction effects of inhomogeneous strain fields investigated by scanning CBED and dark-field electron holography' vs 'Dynamical diffraction effects of inhomogeneous strain fields investigated by scanning convergent electron beam diffraction and dark field electron holography' (ratio=0.89); `volume` '(absent)' vs '271' (missing); `pages` '(absent)' vs '114122' (missing)
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted by identifier substitution -- ScienceDirect PII S030439912500021X recorded in B_literature.md equals the record's PII, standing in for the authors and volume the entry lacked; the title matched at similarity 0.89 because the old title abbreviated "scanning convergent electron beam diffraction" as "scanning CBED" -- cached as docs/agent_reports/crossref_cache/U10.json; B3, 2026-09-22)`

### U11 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Four-wave+dark-field+electron+holography+for+imaging+strain+fields&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1088/0022-3727/49/24/244003` score 55.7 **NOT-ACCEPTED(untestable:A,C,Y,V)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Denneulin; 2016; Journal of Physics D: Applied Physics; vol 49; "Four-wave dark-field electron holography for imaging strain fields"
  - `10.22443/rms.emc2020.1137` score 42.9 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.545, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Technische Universität Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Determination of 3D strain fields by dark field electron holography utilizing dy"
  - `10.1016/j.ultramic.2025.114122` score 41.1 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.341, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.1016/j.ultramic.2013.07.007` score 39.2 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.699, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Lubk; 2014; Ultramicroscopy; vol 136; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1017/s1431927613008957` score 39.2 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.699, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Lubk; 2013; Microscopy and Microanalysis; vol 19; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
- Label: `METADATA_VERIFIED(index, single); AUTHORS, JOURNAL, YEAR, VOLUME AND PAGES ALL UNVERIFIED` -> `METADATA_VERIFIED(index, single); AUTHORS, JOURNAL, YEAR, VOLUME AND PAGES ALL UNVERIFIED`

### U12 -- VERIFIED-UNCHANGED

- Route: vendor page
- Query URL: <https://www.hremresearch.com/holodark/>  (HTTP: 200)
- Publisher-page / registry result: Page titled "HoloDark for DigitalMicrograph - HREM Research Inc." exists; existence only.
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED for existence (route: vendor page https://www.hremresearch.com/holodark/, HTTP 200, titled "HoloDark for DigitalMicrograph -- HREM Research Inc."; B3, 2026-09-22)`

### U13 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ishizuka+1998&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/s0010-2180(97)00266-6` score 18.7 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Ishizuka; 1998; Combustion and Flame; vol 113; "Flame Speeds in Combustible Vortex Rings"
  - `10.1097/00001756-199801260-00004` score 18.3 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Ishizuka; 1998; NeuroReport; vol 9; "Physiological properties of mouse hippocampal mossy cells"
  - `10.1007/978-1-4612-1642-1_10` score 17.8 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Catalano; 1998; Principles of Perinatal—Neonatal Metabolism; vol ; "Glucose Metabolism in Pregnancy"
  - `10.2514/6.1998-4329` score 17.4 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Ishizuka; 1998; Guidance, Navigation, and Control Conference and Exhibit; vol ; "A re-entry guidance law employing simple real-time integration"
  - `10.1016/s0168-0102(98)81946-9` score 17.1 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Abe; 1998; Neuroscience Research; vol 31; "Synaphin/complexin binds to the H3 domain of syntaxin 1"
- Label: `METADATA_VERIFIED(index, single); TITLE, JOURNAL, VOLUME AND PAGES UNVERIFIED` -> `METADATA_VERIFIED(index, single); TITLE, JOURNAL, VOLUME AND PAGES UNVERIFIED`

### U14 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Philosophical+Magazine+Letters+71+1995&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1080/09500839508240524` score 41.5 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- -; 1995; Philosophical Magazine Letters; vol 71; "Erratum"
  - `10.1080/09500839508241283` score 38.3 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Sinha; 1995/2006; Philosophical Magazine Letters; vol 71; "On the grey Penrose tiling"
  - `10.1080/09500839508241002` score 37.5 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Vitta; 1995; Philosophical Magazine Letters; vol 71; "Thermal-history-dependent magnetization behaviour in Cr/Cu multilayers"
  - `10.1080/09500839508240514` score 37.5 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Watson; 1995/2006; Philosophical Magazine Letters; vol 71; "Quartz amorphization: A dynamical instability"
  - `10.1080/09500839508240523` score 36.8 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Suzuki; 1995; Philosophical Magazine Letters; vol 71; "Grain boundary in cemented carbide"
- Label: `METADATA_VERIFIED(index, single) for the journal/volume/issue/year string only; AUTHORS, TITLE AND PAGES UNVERIFIED` -> `METADATA_VERIFIED(index, single) for the journal/volume/issue/year string only; AUTHORS, TITLE AND PAGES UNVERIFIED`

### U15 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Sub-%C3%A5ngstr%C3%B6m+resolution+ptychography+in+a+scanning+electron+microscope+at+20+keV+Nature+Communications+2025&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1038/s41467-025-64133-3` score 82.3 **NOT-ACCEPTED(untestable:A,V)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'untestable'} -- Blackburn; 2025; Nature Communications; vol 16; "Sub-ångström resolution ptychography in a scanning electron microscope at 20 keV"
  - `10.1038/s41586-018-0298-5` score 39.4 **REJECT(T,Y)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.309, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Jiang; 2018; Nature; vol 559; "Electron ptychography of 2D materials to deep sub-ångström resolution"
  - `10.1126/sciadv.adr0438` score 38.2 **REJECT(T,C)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.507, 'C': 'mismatch', 'Y': 'match', 'V': 'untestable'} -- Venugopal; 2025; Science Advances; vol 11; "High-resolution cryo-EM using a common LaB             6             120-keV ele"
  - `10.1093/oxfordjournals.jmicro.a051100` score 35.9 **REJECT(T,C,Y)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.681, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'untestable'} -- -; 1994; Journal of Electron Microscopy; vol ; "Twenty-nm Resolution Spin-polarized Scanning Electron Microscope"
  - `10.1021/acs.nanolett.8b03166.s001` score 35.3 **REJECT(T,C,Y)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.557, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'untestable'} -- -; ; American Chemical Society (ACS); vol ; "Probing Light Atoms at Subnanometer Resolution: Realization of Scanning Transmis"
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED`

### U16 -- VERIFIED-CORRECTED

- Route: Crossref API /works/10.1017/s1431927620016104
- Query URL: <https://api.crossref.org/works?query.bibliographic=Forbidden+reflection+moir%C3%A9+patterns+in+metal%E2%80%932D+material+interfaces+Microscopy+and+Microanalysis+26+2020+860&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2020-8', 'published-online': '2020-7-30', 'issued': '2020-7-30', 'published': '2020-7-30'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1017/s1431927620016104` score 82.5 **ACCEPT-SUBSTITUTED(A<-P)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Reidy; 2020; Microscopy and Microanalysis; vol 26; "Forbidden Reflection Moiré Patterns in Metal-2D Material Interfaces"
  - `10.1093/mam/ozag053.807` score 40.0 **REJECT(T,Y,V,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.267, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; 2026; Microscopy and Microanalysis; vol 32; "Symmetry-Forbidden Oxide Interfaces with Moiré-Type Reconstruction in 3D Stacked"
  - `10.1017/s1431927620016906` score 36.8 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.309, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Warner; 2020; Microscopy and Microanalysis; vol 26; "In-Situ Atomic Level Studies of Unusual Phase Transformations in Metal-chalcogen"
  - `10.1017/s1431927620013859` score 36.2 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- de Graaf; 2020; Microscopy and Microanalysis; vol 26; "Resolving Hydrogen at Metal-metal Hydride Interfaces Using iDPC-STEM"
  - `10.1017/s1431927620016943` score 35.9 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.383, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Fu; 2020; Microscopy and Microanalysis; vol 26; "In-situ TEM Investigation of Lithiation and Sodiation of 2D Metal Sulfides"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Reidy, Kate and Varnavides, Georgios and Thomsen, Joachim Dahl and Blackburn, Arthur and Pham, Thang and Kumar, Abinash and LeBeau, James and Ross, Frances' (missing); `issue` '(absent)' vs 'S2' (missing)
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED (route: Crossref API record found by bibliographic search, accepted with the first page standing in for the first author the entry lacked -- journal, volume 26, pages 860-863 and year 2020 all match -- cached as docs/agent_reports/crossref_cache/U16.json; B3, 2026-09-22)`

### U17 -- VERIFIED-CORRECTED

- Route: README at raw.githubusercontent.com/yux1991/PyRHEED/master/README.md
- Query URL: <https://raw.githubusercontent.com/yux1991/PyRHEED/master/README.md>  (HTTP: 200)
- Publisher-page / registry result: README heading "PyRHEED"; describes RHEED data analysis and simulation. Title corrected to the heading.
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED for existence (route: README fetched at raw.githubusercontent.com/yux1991/PyRHEED/master/README.md, HTTP 200; B3, 2026-09-22)`

### U18 -- UNVERIFIED

- Route: software
- Query URL: <https://api.crossref.org/works?query.bibliographic=rheed%2B%2B+RHEED+intensity+oscillations+epitaxial+growth+SoftwareX&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.softx.2020.100593` score 79.1 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.63, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Daniluk; 2020; SoftwareX; vol 12; "rheed++: A C++ framework to simulation of RHEED intensity oscillations during th"
  - `10.1016/j.softx.2022.101040` score 65.9 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.402, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Daniluk; 2022; SoftwareX; vol 18; "Update 2.0 to rheed++: A complex computer model for dynamical one-beam calculati"
  - `10.1007/978-94-009-0245-9_8` score 54.4 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.433, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Papajová; 1996; Heterostructure Epitaxy and Devices; vol ; "Computer Simulations of Epitaxial Growth, Surface Kinetic Processes and Rheed In"
  - `10.1016/j.cpc.2005.04.005` score 54.3 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.615, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Daniluk; 2005; Computer Physics Communications; vol 170; "Kinematical calculations of RHEED intensity oscillations during the growth of th"
  - `10.1007/bfb0109551` score 51.3 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.474, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- -; ; Springer Tracts in Modern Physics; vol ; "RHEED oscillations"
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED(index, single) for existence`

<!-- END GENERATED -->
