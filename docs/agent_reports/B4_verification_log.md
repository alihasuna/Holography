# B4 -- verification of the L6 and L7 bibliography proposals and their merge into `docs/references.bib`

Prepared: 2026-09-23. Inputs: `docs/agent_reports/L6_new_refs.bib` (42 entries, report
`L6_sourced_si_parameters.md`) and `docs/agent_reports/L7_new_refs.bib` (46 entries, report
`L7_surface_realism.md`; its TAKEGUCHI1990 entry is a proposed correction of the existing entry). Neither
file nor either report was edited. Baseline: `docs/references.bib` at commit
`2a3a999f38c5c18b13eda33ac8b99a0e4ee20dae` (132 entries: 125 verified, 7 unverified). Every count
below is produced by `tools/bib/b4_check.py report`.

## Reproduce

```
venv/bin/python tools/bib/b4_check.py fetch      # network; a cached HTTP-200 response is never re-fetched
venv/bin/python tools/bib/b4_check.py merge      # baseline revision + verified proposals -> docs/references.bib
venv/bin/python tools/bib/b4_check.py report     # B4_results.tsv + generated block of this log + counts
venv/bin/python tools/bib/b4_check.py validate   # = crossref_check.py validate (braces, keys, notes, doi backing)
```

(`fetch` extracts the page-1 text of the muSTEM manual with `pypdf` if it is importable; the text is
already cached as `crossref_cache/MUSTEM53.titlepage.txt`, so the other three steps need no network
and no extra package.)

Routes, extra record identifiers and every declared decision (values set rather than copied, record
artefacts kept, the duplicate to keep, sentences added to notes) are in `tools/bib/b4_routes.yaml`.
All registry responses are cached in `docs/agent_reports/crossref_cache/` as `<KEY>.json` (Crossref
`/works`), `<KEY>.jalc.json` and `<KEY>.ra.json` (JaLC and doi.org/ra), `<KEY>.oai-arxiv.xml` and
`<KEY>.oai-arxivraw.xml` (arXiv), `<KEY>.cinii.json` (CiNii Research), `<KEY>.claim.json` (Crossref
record of a DOI that a report names in its text), `<KEY>.arxivdoi.json` (Crossref record of a DOI named
in an arXiv record) and `MUSTEM53.titlepage.txt`; `_index.json` records URL, HTTP status and fetch time
of every request, including the failed ones.

## Access conditions and privacy

* Crossref: `https://api.crossref.org/works/<DOI>` with NO `mailto` parameter; User-Agent
  `Holography-bibcheck/1.0`. No name, e-mail address or other personal data was sent to any service.
* Crossref `/works` returned 404 for the 11 JaLC DOIs (J-STAGE meeting abstracts, Oyo Buturi,
  SPring-8 reports, NDL theses); `https://doi.org/ra/<DOI>` gave RA = JaLC for all 11, and
  `https://api.japanlinkcenter.org/dois/<DOI>` returned the record (HTTP 200).
* arXiv: the query API `https://export.arxiv.org/api/query?id_list=<id>` answered **HTTP 406** to this
  session (4 attempts each, logged in `_index.json`); the records were taken from arXiv's OAI-PMH
  interface `https://oaipmh.arxiv.org/oai?verb=GetRecord&identifier=oai:arXiv.org:<id>` with
  `metadataPrefix=arXiv` (authors, title, journal-ref, DOI) and `arXivRaw` (version list with dates).
  Note: the `created` element of the arXiv format is the date of the LATEST version, so years and
  version dates were taken from the arXivRaw version list.
* CiNii Research record JSON (`https://cir.nii.ac.jp/crid/<id>.json`, NDL data) for TAKEGUCHI1990 and
  the two theses; the thesis crid of Takeguchi was found by CiNii OpenSearch on the thesis title.
* Not reachable: `journals.aps.org` and `link.aps.org` (Cloudflare, HTTP 403), `harvest.aps.org` (401),
  `academic.oup.com` (HTTP 403). Nothing was worked around.

## Method

1. **Comparison.** Each proposal was compared field by field with its record by the same comparator B3
   used (`crossref_check.compare`: author count, order, family-name spelling and diacritics, initials /
   given-name consistency; title after case, punctuation and markup folding; container; volume; issue;
   pages or article number; year against published-print, published-online and issued; publisher).
   JaLC, arXiv and CiNii records are first converted to the same shape (English JaLC values preferred).
   Extra checks: DOI string, record type vs entry type, arXiv id, the version and date claimed in
   `howpublished`/`note` against the arXivRaw version list, the primary category; for the two theses
   the Japanese title, the kanji name, the romanised name (plain Hepburn of the CiNii katakana reading,
   computed by the script), the degree name, number and grantor and the DOI carried by CiNii; for the
   muSTEM manual the title and the five author names on page 1 of the PDF.
2. **What counts as a mismatch.** A field whose value differs from the record. NOT counted (but listed):
   a field the record does not carry ("record-silent"), and a difference in white space only. Two record
   normalisations are applied before comparing and are stated in the notes: J-STAGE's issue "0" is read
   as "no issue"; Crossref title markup (`<i>`, `<b>`, `<sub>`) is folded for comparison and transcribed
   to LaTeX for the merged entry. Formatting defects of the proposals (double-braced titles, raw
   non-ASCII characters, capitalised family names as deposited, an unparseable thesis author field, a
   doubled backslash before `&`, `number = {0}`, an empty author field) are listed separately; they are
   fixed by rendering the merged entry from the record, not counted as mismatches.
3. **Duplicates.** Against the baseline bib and between L6 and L7: same DOI, same arXiv id, or the same
   work (same first-author family name and folded-title similarity >= 0.90, unless the two items carry
   different DOIs or different years -- then they are separate items, e.g. a meeting abstract and the
   later paper of the same title). Items at similarity >= 0.80 are listed as related.
4. **Merge.** Verified, deduplicated proposals were added under a new section "4n" (L6 then L7, file
   order) just above PART 5, keys unchanged (none collides with the baseline). Every bibliographic field
   is copied from the record by the script; six entries have a value set rather than copied, each
   declared in `b4_routes.yaml` and named in the entry's note (below). The note of every merged entry
   starts with the evidence label: the L agent's reading label, if any, marked "as labelled by L6/L7;
   not re-checked in B4", followed by `METADATA_VERIFIED (route: <record>, cached as <file>; B4,
   2026-09-23)`; then "label before B4", provenance, the B4 check result, and the L note verbatim
   (apart from LaTeX encoding). Only the scratch-cache sentence of the L6 notes was dropped (those files
   are not in the repository; the B4 cache replaces them). B4 read no paper; no reading label was
   raised or lowered.
5. **TAKEGUCHI1990.** Applied only because the CiNii/NDL record confirms the proposed volume, issue,
   pages and byline (see the generated section). The DOI pairing is flagged below.

## Findings

1. **WUSPIECKER17 (L6) carried the wrong DOI.** The L6 entry had the DOI, title ("Publisher's note"),
   volume 177, pages 1-13 and an EMPTY author field of Crossref record 10.1016/j.ultramic.2017.01.011, a
   Publisher's note without authors -- while its own note and L6 report sections 3.1 and 6 say the
   article is 10.1016/j.ultramic.2017.03.029 (Ultramicroscopy 176, 233-245). B4 fetched the report's
   DOI (`WUSPIECKER17.claim.json`) and tested L6's claimed citation (Wu and Spiecker, Ultramicroscopy,
   176, 233-245, 2017) on the five-field rule: first author, container, volume, year and first page
   match; the title is untestable because L6 states none, so the verdict is ACCEPT-SUBSTITUTED(T<-P)
   (the B3 route "first page stands in for the title"). The entry now carries that record: Wu, Mingjian
   and Spiecker, Erdmann, "Correlative micro-diffraction and differential phase contrast study of mean
   inner potential and subtle beam-specimen interaction", Ultramicroscopy 176, 233-245 (2017).
2. **MUSTEM53 (L6).** The title page prints "µSTEM / v5.3 / A transmission electron microscopy
   simulation suite, in particular for scanning transmission electron microscopy." and the five authors
   exactly as proposed; the trailing "(manual)" of the proposal is not printed and was dropped. No year
   is printed (PDF metadata CreationDate 2018-09-24 is not used).
3. **TAKEGUCHI1990 corrected and moved up.** Old: author, title, journal, year 1990; no volume, pages or
   doi (UNVERIFIED section). New: volume 39, number 4, pages 269--272 (CiNii/NDL record crid
   1521417755419074304: byline "Masaki Takeguchi; Ken Harada; Ryuichi Shimizu", "p269"-"272"), doi
   10.1093/oxfordjournals.jmicro.a050815 (Crossref). The CiNii record carries no DOI and the Crossref
   record carries no authors, volume or pages; the two are joined by the publisher-deposited resource URL
   inside the Crossref record, `https://academic.oup.com/jmicro/article/39/4/269/847699/...`, which
   encodes volume 39, issue 4, first page 269. **Flag:** this "linked records" acceptance is not the
   strict five-field rule on one record; to revert, drop the doi field (volume, issue and pages stand on
   the CiNii/NDL record alone).
4. **ALLEN15 (L6).** The Crossref record writes the second author with the Hebrew punctuation geresh
   (U+05F3) in place of the apostrophe; the proposal's "D'Alfonso" is kept (declared record artefact).
5. **ZANDVLIET2001E (L7).** Crossref deposits pages 247-462 for this erratum, and L7 copied that range;
   B4 keeps only the first page 247 (a 216-page erratum is implausible; APS pages were unreachable).
   **Flag:** a record value deliberately not copied in full.
6. **B08CH7, B08CH8, B08CH14 (L6)** are chapter records of the existing [B08] (same ISBNs
   9780198500742 / 9781383019926), not duplicates. The chapter records give the authors as
   "Peng, L -M", "Dudarev, S L", "Whelan, M J" and the publisher as "Oxford University PressOxford";
   the [B08] forms (same initials; publisher "Oxford University Press") were set instead.
7. **Duplicate between L6 and L7:** HORIO14 (L6) = HORIO2014 (L7), same DOI 10.1380/ejssnt.2014.380.
   HORIO14 is merged (L6's `number = {0}` dropped); L7's label and note are appended to its note.
   **No proposal duplicates an entry of `references.bib`** (L7's TAKEGUCHI1990 is the proposed
   correction of the existing entry, handled in Finding 3). L7's OSAKABE1990JPS has the same title and
   first author as [P08] (Microsc. Res. Tech. 1992) and OSAKABE1989JPS nearly the same as
   [OSAKABE1989EMSA] (EMSA proceedings 1989), but they are distinct JPS meeting abstracts with their own
   JaLC DOIs, so both were merged as separate items.
8. **arXiv records.** HAJEK26 v1 2026-08-25 only, no DOI or journal-ref; ZHENG26A v1 2026-03-11, v2
   2026-04-16, journal-ref "Frontiers of Physics, 21(11), 114201 (2026)" and DOI
   10.15302/frontphys.2026.114201, whose Crossref record has title, journal, volume, issue and article
   number but NO authors (as L6 reported; no doi field added); CHALISE22A v1 2022-03-23, v2 2022-03-29,
   and its arXiv record names a journal version, Phys. Rev. Applied 18, 014076 (2022),
   10.1103/PhysRevApplied.18.014076, whose Crossref record has the same four authors (not merged: the
   entry stays the preprint L6 read; recorded in its note); HEACOCK21's arXiv record 2103.05428 (v3
   2021-08-19, as L6 states) links the same Science DOI.
9. **Theses (L7).** No record gives an English title, so OSAKABE1995THESIS and TAKEGUCHI1993THESIS keep
   the Japanese title of the JaLC record, in UTF-8 -- the first non-ASCII titles in `references.bib`
   (the header now says so). L7's author field ("kanji (Roman, Name)") is not a parseable BibTeX name;
   it is now the plain Hepburn romanisation of the CiNii reading (Takeguchi, Masaki; Osakabe,
   Nobuyuki), which also equals L7's romanisation, with the kanji name in the note.
10. **Formatting of the proposals.** All 42 L6 titles were wrapped in a second brace pair; many L6/L7
    fields held raw Unicode (x-sign, square root, en dash, curly quotes, umlauts); J-STAGE records
    deposit some family names in capitals (SHIRASAWA2005HK, OGINO1997, YASAKA1991, YAGI1986); KATO1999
    had `\\&` (a LaTeX line break) for `\&`. All fixed by rendering from the records.
11. Apart from WUSPIECKER17, MUSTEM53 and the ALLEN15 record artefact, **every bibliographic field of
    every proposal agrees with its record.** L6's and L7's reading labels (SECTION_READ, +ABSTRACT) were carried over as theirs and
    were not re-checked.

## Tooling changes

* New `tools/bib/b4_check.py` (fetch / merge / report / validate) and `tools/bib/b4_routes.yaml`.
* `tools/bib/crossref_check.py`, `check_dois_backed()`: a doi field is now also accepted when a cached
  JaLC record (`<KEY>.jalc.json`) carries it, and both `<KEY>.claim.json` and `<KEY>.json` are tried
  (before, a present claim record hid the main record). Re-run on the baseline: no change (0 unbacked).

## Flags for the orchestrator

1. TAKEGUCHI1990 doi rests on linked records (Finding 3).
2. WUSPIECKER17 accepted with the first page standing in for the title L6 did not state (Finding 1).
3. ZANDVLIET2001E pages truncated to the first page (Finding 5).
4. `docs/references.bib` now contains UTF-8 (two thesis titles; Japanese titles quoted in some L7 notes).
5. Reading labels of L6/L7 are carried as "as labelled by L6/L7; not re-checked in B4".

<!-- BEGIN GENERATED BY tools/bib/b4_check.py report -->

### Counts (generated)

| quantity | value |
|---|---|
| proposals checked | 88 |
| L6 | 42 |
| L7 | 46 |
| verified (every field agrees, or differs only by a record artefact) | 84 |
| verified after correction (incl. the TAKEGUCHI1990 correction) | 3 |
| field mismatches (counted) | 7 |
| entries with mismatches | 3 |
| entries whose proposal had formatting defects (fixed by rendering from the record) | 62 |
| entries with a value set rather than copied (b4_routes.yaml) | 6 |
| unverified | 0 |
| duplicates (not merged) | 1 |
| merged into references.bib (verified section) | 87 |
| references.bib entries after merge | 218 |
| references.bib verified / unverified section | 212 / 6 |
| validation errors | 0 |
| doi fields not backed by a cached record | 0 |

### Every counted mismatch, with the record's value (generated)

| key | field | proposal | record | record source | resolution |
|---|---|---|---|---|---|
| ALLEN15 | author[2].family | D'Alfonso | D׳Alfonso | Crossref | proposal kept (record artefact; tools/bib/b4_routes.yaml accepted_residual) |
| WUSPIECKER17 | author | (absent) | Wu, Mingjian and Spiecker, Erdmann | Crossref(claimed DOI) | corrected to the record value |
| WUSPIECKER17 | title | Publisher’s note | Correlative micro-diffraction and differential phase contrast study of mean inner potential and subtle beam-specimen interaction | Crossref(claimed DOI) | corrected to the record value |
| WUSPIECKER17 | volume | 177 | 176 | Crossref(claimed DOI) | corrected to the record value |
| WUSPIECKER17 | pages | 1–13 | 233-245 | Crossref(claimed DOI) | corrected to the record value |
| WUSPIECKER17 | doi | 10.1016/j.ultramic.2017.01.011 | 10.1016/j.ultramic.2017.03.029 | Crossref(claimed DOI) | corrected to the record value |
| MUSTEM53 | title | uSTEM v5.3: A transmission electron microscopy simulation suite, in particular for scanning transmission electron microscopy (manual) | title page prints no '(manual)' | PDF title page | corrected to the record value |

Differences not counted as mismatches (the record is silent on the field, or white space only):

* HORIO14: issue proposal '0', Crossref record '(none)' (record-silent)
* TAKEGUCHI1990: volume proposal '39', Crossref record '(none)' (record-silent)
* TAKEGUCHI1990: issue proposal '4', Crossref record '(none)' (record-silent)
* TAKEGUCHI1990: title proposal 'Observation of GaAs(110) Surface Defect by Reflection Electron Holography', CiNii record 'Observation of GaAs(110)Surface Defect by Reflection Electron Holography' (spacing)

### Values set rather than copied from the record (generated from tools/bib/b4_routes.yaml)

* B08CH7: author = 'Peng, L.-M. and Dudarev, S. L. and Whelan, M. J.'; publisher = 'Oxford University Press'
* B08CH8: author = 'Peng, L.-M. and Dudarev, S. L. and Whelan, M. J.'; publisher = 'Oxford University Press'
* B08CH14: author = 'Peng, L.-M. and Dudarev, S. L. and Whelan, M. J.'; publisher = 'Oxford University Press'
* ALLEN15: author = 'Allen, L.J. and D'Alfonso, A.J. and Findlay, S.D.'
* ZANDVLIET2001E: pages = '247'
* MUSTEM53: title = '$\mu$STEM v5.3: A transmission electron microscopy simulation suite, in particular for scanning transmission electron microscopy'

### TAKEGUCHI1990 correction (generated)

Verdict: CORRECTION-CONFIRMED -- references.bib [TAKEGUCHI1990] corrected and moved from the UNVERIFIED section.

Old values: author = 'Takeguchi, Masaki and Harada, Ken and Shimizu, Ryuichi'; title = 'Observation of GaAs(110) Surface Defect by Reflection Electron Holography'; journal = 'Journal of Electron Microscopy'; year = '1990'.

* CiNii: confirms author list, title, journal, volume, issue, pages, year
* Crossref: title, journal, year agree; record has no authors, volume or pages
* locator: ('39', '4', '269') in https://academic.oup.com/jmicro/article/39/4/269/847699/Observation-of-GaAs110-Surface-Defect-by

### Duplicates (generated)

* HORIO2014 (L7): not merged (duplicate of L6 [HORIO14], same DOI; notes combined)

Related items with the same first author and a similar title that are NOT duplicates (different DOI or different year):

* YAGI1986 ~ [P23] (title similarity 0.81): related title, same first author
* OSAKABE1990JPS ~ [P01] (title similarity 0.88): related title, same first author
* OSAKABE1990JPS ~ [P08] (title similarity 1.0): same first author and title but different DOI (1990 vs 1992): separate item, not a duplicate
* OSAKABE1990JPS ~ [OSAKABE1989EMSA] (title similarity 0.9): same first author and title but different DOI (1990 vs 1989): separate item, not a duplicate
* OSAKABE1989JPS ~ [P08] (title similarity 0.86): related title, same first author
* OSAKABE1989JPS ~ [OSAKABE1989EMSA] (title similarity 0.92): same first author and title but different DOI (1989 vs 1989): separate item, not a duplicate

### Per-entry results (generated; full rows in B4_results.tsv)

| key | src | verdict | records (HTTP) | fields checked | mismatches | formatting fixed |
|---|---|---|---|---|---|---|
| THOMAS24 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| MENDIS24 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| MENDIS19 | L6 | VERIFIED | Crossref 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| MENDIS20C | L6 | VERIFIED | Crossref 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| NI26 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| VOSS80 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); journal: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| BIRDKING90 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| WEICKENMEIER91 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| PENG96ROBUST | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| PENG96DW | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| HALLHIRSCH65 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| RADI70 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HHW62 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HUMPHREYS68 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| ICHIMIYA85 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| ICHIMIYALEHMPFUHL78 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); journal: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| DUDAREV95 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| DUDAREV93 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| ALLEN15 | L6 | VERIFIED | Crossref 200 | 6 | 1 | title wrapped in a second brace pair (suppresses all case handling) |
| BARTHEL18 | L6 | VERIFIED | Crossref 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HOWIESTERN72 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); journal: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| MINAMI08 | L6 | VERIFIED | Crossref 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HORIO14 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded); number = {0}: J-STAGE's placeholder issue for journals without issues |
| HORIO22 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HEACOCK21 | L6 | VERIFIED | Crossref 200; arXiv query API 406; arXiv OAI-PMH (arXiv) 200; arXiv OAI-PMH (arXivRaw) 200 | 10 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| FLENSBURG99 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| SEARS91 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| B08CH14 | L6 | VERIFIED | Crossref 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| B08CH7 | L6 | VERIFIED | Crossref 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| B08CH8 | L6 | VERIFIED | Crossref 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| WUSPIECKER17 | L6 | VERIFIED-CORRECTED | Crossref 200; Crossref (DOI claimed in the report) 200 | 10 | 5 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded); empty author field |
| WU04 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HORIO83 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| MOON72 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling); journal: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| MENADUE72 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| COLELLA72 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| LEHMPFUHLDOWELL86 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HAYAKAWA82 | L6 | VERIFIED | Crossref 200 | 7 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| HAJEK26 | L6 | VERIFIED | arXiv query API 406; arXiv OAI-PMH (arXiv) 200; arXiv OAI-PMH (arXivRaw) 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| ZHENG26A | L6 | VERIFIED | arXiv query API 406; arXiv OAI-PMH (arXiv) 200; arXiv OAI-PMH (arXivRaw) 200; Crossref (DOI claimed in the report) 200 | 6 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| CHALISE22A | L6 | VERIFIED | arXiv query API 406; arXiv OAI-PMH (arXiv) 200; arXiv OAI-PMH (arXivRaw) 200; Crossref (DOI named in the arXiv record) 200 | 3 | 0 | title wrapped in a second brace pair (suppresses all case handling) |
| MUSTEM53 | L6 | VERIFIED-CORRECTED | publisher file (PDF, title page) 200 | 2 | 1 | title wrapped in a second brace pair (suppresses all case handling) |
| RAMSTAD1995 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| ZANDVLIET2000 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| ZANDVLIET2001E | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| HORIO2014 | L7 | DUPLICATE | Crossref 200 | 6 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| SHIRASAWA2005HK | L7 | VERIFIED | Crossref 200 | 7 | 0 | author family name in capitals as deposited: SHIRASAWA; author family name in capitals as deposited: MIZUNO; author family name in capitals as deposited: TOCHIHARA |
| SHIRASAWA2006JPS | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 6 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| HAYASHI2006 | L7 | VERIFIED | Crossref 200 | 6 | 0 | - |
| OGINO1997 | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 7 | 0 | author family name in capitals as deposited: OGINO; author family name in capitals as deposited: HIBINO; author family name in capitals as deposited: HOMMA |
| CHADI1987 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| OVER1997 | L7 | VERIFIED | Crossref 200 | 7 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| FELICI1997 | L7 | VERIFIED | Crossref 200 | 7 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| TAKAHASI1995 | L7 | VERIFIED | Crossref 200 | 7 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| SHIRASAWA2006SS | L7 | VERIFIED | Crossref 200 | 7 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| TABATA1987 | L7 | VERIFIED | Crossref 200 | 7 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| ALERHAND1990 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| PEHLKE1991 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| INOUE1987 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| KAHATA1989 | L7 | VERIFIED | Crossref 200 | 7 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| MCCOY1994 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| MCCOY1993 | L7 | VERIFIED | Crossref 200 | 7 | 0 | title: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| MORITA1990 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| UZUHASHI2024 | L7 | VERIFIED | Crossref 200 | 6 | 0 | - |
| PASTEWKA2009 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| PEDERSEN2017 | L7 | VERIFIED | Crossref 200 | 7 | 0 | author: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| YASAKA1991 | L7 | VERIFIED | Crossref 200 | 7 | 0 | author family name in capitals as deposited: YASAKA; author family name in capitals as deposited: MIYAZAKI; author family name in capitals as deposited: HIROSE |
| AZUMA2007 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| TOKUTAKE2015 | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 7 | 0 | - |
| KOROBTSOV2007 | L7 | VERIFIED | Crossref 200 | 6 | 0 | - |
| YAGI1986 | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 7 | 0 | author family name in capitals as deposited: YAGI; author family name in capitals as deposited: TANISHIRO; author family name in capitals as deposited: TAKAYANAGI |
| CLAVERIE1992 | L7 | VERIFIED | Crossref 200 | 7 | 0 | author: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| CUSTER1994 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| LAAZIRI1999 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| KATO1999 | L7 | VERIFIED | Crossref 200 | 7 | 0 | journal: doubled backslash before the ampersand (a LaTeX line break), not an escaped ampersand |
| KATO2004 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| BARNA1998 | L7 | VERIFIED | Crossref 200 | 7 | 0 | author: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| BARNA1999 | L7 | VERIFIED | Crossref 200 | 7 | 0 | author: raw non-ASCII characters (references.bib is LaTeX-encoded) |
| MAYER2007 | L7 | VERIFIED | Crossref 200 | 7 | 0 | - |
| OSAKABE1990JPS | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 6 | 0 | - |
| OSAKABE1989JPS | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 6 | 0 | - |
| OSAKABE1990JPSB | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 6 | 0 | - |
| SUZUKI2000JPS | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 6 | 0 | - |
| TANISHIRO2001JPS | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200 | 6 | 0 | - |
| OSAKABE1995THESIS | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200; CiNii Research 200 | 6 | 0 | author: raw non-ASCII characters (references.bib is LaTeX-encoded); author '長我部, 信行 (Osakabe, Nobuyuki)' is not a parseable BibTeX name |
| TAKEGUCHI1993THESIS | L7 | VERIFIED | Crossref 404; doi.org/ra 200; JaLC 200; CiNii Research 200 | 6 | 0 | author: raw non-ASCII characters (references.bib is LaTeX-encoded); author '竹口, 雅樹 (Takeguchi, Masaki)' is not a parseable BibTeX name |
| JOY2004 | L7 | VERIFIED | Crossref 200 | 6 | 0 | - |
| TAKEGUCHI1990 | L7 | CORRECTION-CONFIRMED | Crossref 200; CiNii Research 200 | 14 | 0 | - |

### Formatting defects of the proposals fixed by rendering from the records (generated)

* 42 x title wrapped in a second brace pair (suppresses all case handling)
* 29 x raw non-ASCII characters (references.bib is LaTeX-encoded)
* 12 x author family name in capitals as deposited
* 1 x number = {0}: J-STAGE's placeholder issue for journals without issues
* 1 x empty author field
* 1 x doubled backslash before the ampersand (a LaTeX line break), not an escaped ampersand
* 1 x author '長我部, 信行 (Osakabe, Nobuyuki)' is not a parseable BibTeX name
* 1 x author '竹口, 雅樹 (Takeguchi, Masaki)' is not a parseable BibTeX name

Validation of docs/references.bib: {"entries": 218, "unique_keys": 218, "verified_section": 212, "unverified_section": 6, "with_doi": 197}; errors: none; doi fields without a cached record carrying the same DOI: none

<!-- END GENERATED -->
