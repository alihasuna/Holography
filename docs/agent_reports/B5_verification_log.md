# B5 -- verification of the L8 and L9 bibliography proposals and their merge into `docs/references.bib`

Prepared: 2026-09-24. Inputs: `docs/agent_reports/L8_new_refs.bib` (29 entries, report `L8_oxide_plasma.md`; its 27
DOIs had been resolved by review E9, section 0) and `docs/agent_reports/L9_new_refs.bib` (25 entries, report
`L9_microscope_detector.md`; 9 of them without a DOI). Neither file nor either report was edited. Baseline:
`docs/references.bib` at commit `11219d523b2203c25c79a94ac8b98f851aa98369` (the B4 commit, the last change of the file;
218 entries: 212 verified, 6 unverified). Method and formatting follow B4 (`B4_verification_log.md`). Every count below
is produced by `tools/bib/b5_check.py report`. Nothing was committed by B5.

## Reproduce

```
venv/bin/python tools/bib/b5_check.py fetch      # network; a cached HTTP-200 response is never re-fetched
venv/bin/python tools/bib/b5_check.py merge      # baseline revision + verified proposals -> docs/references.bib
venv/bin/python tools/bib/b5_check.py report     # B5_results.tsv + generated block of this log + counts
venv/bin/python tools/bib/b5_check.py validate   # = crossref_check.py validate (braces, keys, notes, doi backing)
```

`tools/bib/b5_check.py` is a copy of `tools/bib/b4_check.py` (unchanged) with the B5 additions: DataCite and J-STAGE
readers, the page route for items without a DOI, declared record-title normalisations, the report-text check and the
docs citation-key check. `merge` refuses to write if `references.bib` carries edits other than B5's own since the
baseline. Routes, extra record identifiers and every declared decision (title prefixes, values set rather than copied,
record artefacts kept, the entry not merged, sentences added to notes) are in `tools/bib/b5_routes.yaml`. Records are
cached in `docs/agent_reports/crossref_cache/` as `<KEY>.json` (Crossref `/works`), `<KEY>.ra.json` and
`<KEY>.jalc.json` / `<KEY>.datacite.json`, `<KEY>.oai-arxiv*.xml`, `<KEY>.cinii.json`, `<KEY>.epmc.json`,
`<KEY>.altdoi.json`, `<KEY>.jstage.json` (citation meta tags only), `<KEY>.crquery.json`, `<KEY>.wprest.json`,
`<KEY>.openalex.json`, `<KEY>.s2.json` and `<KEY>.page<N>.json`; `_index.json` records URL, HTTP status and fetch
time of every request, including the failed ones.

## Access conditions and privacy

* Crossref `https://api.crossref.org/works/<DOI>` and the bibliographic query endpoint, with NO `mailto` parameter;
  User-Agent `Holography-bibcheck/1.0` (as B4). No name, e-mail address or other personal data was sent to any
  service; no form was submitted.
* Crossref 404 for two DOIs; `https://doi.org/ra/<DOI>` gave JaLC (Butsuri 55, 846) and DataCite (Zenodo 10419194);
  the JaLC API and the DataCite API returned the records (HTTP 200).
* arXiv (LUHMANN2017): the query API answered HTTP 406 again; the OAI-PMH records were used (as B4).
* Page route (items without a DOI): each URL was fetched once (HTTP 200 for all 11 files/pages). ONLY the checks are
  cached (HTTP status, final URL, content type, SHA-256, size, the HTML `<title>`/`<h1>` or the PDF title metadata
  and page count, and for each tested string whether it occurs); the page text is not stored, because facility pages
  and slides carry staff e-mail addresses and telephone numbers. No staff name or contact is recorded here beyond
  the author lists of the items themselves.
* Not reachable: `academic.oup.com` (doi.org -> OUP landing page, HTTP 403, for HATA2006). Nothing was worked around.

## Method

1. **Comparison** (as B4): every proposal field against its registry record with the B3/B4 comparator
   (`crossref_check.compare`): author count, order, family names, initials; title after case/punctuation/markup
   folding; container; volume; issue; pages or article number; year. L9's `eid` (article number) is compared as
   pages. Not counted but listed: record-silent fields, white-space-only differences, a fuller given name with the
   same initials ("David R. G." vs "D.R.G."), and an en dash vs hyphen in a volume range.
2. **Record normalisations** (listed per entry below and in the entry's note): J-STAGE deposits family names,
   some given names and the container title "SHINKU" in capitals, and a closing full stop after English titles;
   the Yamamura-Tawara Crossref title is in capitals (the proposal's capitalisation of the same words is used);
   three J-STAGE Crossref records prefix the issue's feature title (declared prefixes removed); HATTORI2001's Crossref
   title is empty (the English title of the J-STAGE landing page is used); MathML (HIMPSEL1988, DIMOVA2025), escaped
   `<SUB>` (LEE2000MT) and a doubly escaped `<` (FANG2024MM) are transcribed.
3. **Items without a DOI (9)**: the URL was fetched, and the entry's title, owner or authors and the other stated
   fields (document number, running head, first/last page, meeting, abstract number) were searched in the page text.
   They are labelled **PAGE_CHECKED** (defined in the header of `references.bib`), not METADATA_VERIFIED: no
   registry record exists. For ROBINSON2004SVC and SATO2008HITACHIREVIEW a Crossref bibliographic query was also run
   (logged): no record with the title, so no DOI. No DOI, page, volume or year was invented.
4. **Duplicates**: against the 218 entries by DOI, arXiv id, key (a same key with a different item would be a
   collision) and first author + title similarity >= 0.90; and between L8 and L9.
5. **Merge**: verified proposals under a new section "4o" (L8 then L9, file order) after 4n and before PART 5, keys
   unchanged. Fields with a DOI are rendered from the record (LaTeX-encoded as in 4n); page-checked items keep the
   proposal's fields. Each note starts with the proposer's reading label marked "as labelled by L8/L9; not
   re-checked in B5", then `METADATA_VERIFIED (route: ...; B5, 2026-09-24)` or `PAGE_CHECKED (route: <URL>, HTTP,
   SHA-256, access date; ...)`, then "label before B5", provenance, the B5 check result, normalisations, fields set,
   and the proposer's note verbatim (apart from LaTeX encoding).
6. **Report text**: every line of the L8 and L9 reports that names a proposal DOI was tested for the record's
   volume, first page (or article number) and year in the citation printed next to it (58 lines).
7. **Citation keys in docs**: every key-like token of `docs/*.md` and `docs/source_map.tsv` was looked up in
   `references.bib`; ID families that are not citations (SM, T, E, D, N, assumption rows B16-B42, ...) are excluded
   (list in the generated section).

## Findings

1. **HATA2006 (L8) NOT MERGED.** The Crossref record (OUP deposit) lists one author, "S. Hata" (OpenAlex marks him as
   corresponding author); the CiNii/NII record crid 1571135650339084160 (NAID 10018006189) lists six, Sosiati, Hata,
   Kuwano, Itakura, Nakano, Umakoshi; Semantic Scholar lists the same six with Hata first; Europe PMC has no record;
   the OUP page answered 403. Title, journal, 55(1), 23-26 and 2006 agree in all records, but the author list and
   order cannot be established, and the proposal (`author = {Hata, S.}`) would cite a six-author paper under one
   name. L8 itself flagged this (L8_new_refs.bib line 162, note; L8 report line 145, row P8). Merge after the byline
   is read (L8 upload item 4). No doc cites HATA2006.
2. **KIM1996JVSTB (L8): container title short form** (`L8_new_refs.bib` line 297, "Journal of Vacuum Science and
   Technology B"); corrected to the record's full title "Journal of Vacuum Science \& Technology B: Microelectronics
   and Nanometer Structures Processing, Measurement, and Phenomena". The only field corrected.
3. **WATANABE2000BUTSURI (L8): JaLC record artefact.** The JaLC record writes the third author "lchikawa" (lower-case
   L) beside the kanji 市川 昌和; the proposal's "Ichikawa" is kept (declared residual; the Crossref record of
   WATANABE1999HK, same three authors, has ICHIKAWA). L8's note does not mention it.
4. **ICHIKAWA2002IEEJ (L8): author romanisation rests on linked records.** L8 says the author "is taken from the
   J-STAGE article page" (`L8_new_refs.bib` line 198; report line 264, row R3: "the J-STAGE page gives author and
   title"). The J-STAGE page (Japanese and English views, meta tags and body) and CiNii give the author only in kanji,
   市川 昌和, and the title only in Japanese; the English title is the Crossref one without its feature prefix. The
   romanisation "Ichikawa, Masakazu" is supported by the same kanji name being creator 3 of the JaLC record of
   WATANABE2000BUTSURI (English "lchikawa, Masakazu" [sic]); flagged in the note.
5. **UVIC_EMRG_FACILITIES (L9): dating statement superseded.** The L9 note ("footer 2017, no date of change",
   `L9_new_refs.bib` line 247; report line 80, row U10) is kept verbatim; B5 adds the site's WordPress REST record:
   created 2020-01-20, last modified 2023-01-04 (as E10 m3 found).
6. **Record forms replacing proposal forms (not mismatches):** MITCHELL2015 author "D.R.G." (record) for "David R.
   G."; SUGITA1996 volume "100--101"; titles and journals rendered from the records (e.g. "Shinku" for "Shinku
   (Journal of the Vacuum Society of Japan)", "Butsuri" for "Butsuri (Nihon Butsuri Gakkaishi)", ERHARD2024 title
   with the record's en dash "silicon--oxygen"). SNOECK2014MM keeps the deposited third author "Taniguch" [sic], as
   L9 did. MCCARTNEY2005: the second DOI 10.1093/jmicro/54.3.239 carries the same metadata (checked); the doi field
   keeps dfi035.
7. **Page-checked items.** All 9 resolve and print the stated title and owner/authors. The SHA-256 of the fetched
   files equals the value L8/L9 printed for sp1020.pdf, pb1020.pdf, svc04.pdf, the Hitachi Review PDF, the UVic
   STEHM page (U1) and both slide sets (U4 ends ...a24db043; L9 printed "...a043", a typo already noted by E10 m4);
   the Quantum Detectors page differs (dynamic page, as E10 found). FISCHIONE1020: L8's abbreviated second URL
   (".../pb1020.pdf") was written out after fetching it (the product page links both files).
8. **Report text: no wrong field.** None of the 58 report lines naming a proposal DOI prints a volume, first page
   or year that differs from the record; the no-DOI citations in the reports (Hitachi Review 57(3) 132-135 (2008);
   SVC 2004 pp. 368-376; mmc2023 abstract 210) match the documents. L9's author counts (Puttock seven, Reidy ten,
   Harada five) match the records.
9. **No duplicate** of the 218 entries and none between L8 and L9; HARADA2006JAP (triple biprism, JAP 2006) is
   related to, but distinct from, [P47] (double biprism, APL 2004).
10. **Citation keys in docs.** Before the merge, 9 L8 keys cited in `docs/source_map.tsv` line 37 (row SM33:
    LEE2000MT, IAKOUBOVSKII2008PRB, KITAJIMA1994, ROBINSON2004SVC, WATANABE1999HK, WATANABE2000BUTSURI,
    ICHIKAWA2002IEEJ, HONDA1988, ERHARD2024DATA) were missing from `references.bib`; after the merge no citation key
    used in `docs/*.md` or `docs/source_map.tsv` is missing. Caveat: `docs/model_assumptions.md` row ids B10-B15
    have the same form as the book keys B10-B15, so those tokens count as present whichever is meant.
11. Every doi field in 4o is the DOI of the cached Crossref, JaLC or DataCite record it was checked against
    (validator: 0 unbacked); none was typed. Reading labels (SECTION_READ, +ABSTRACT, REPRODUCED) are L8's and L9's,
    not re-checked.
12. **Parse check.** `validate` (brace balance, unique keys, note form, doi shape and backing): 0 errors; an
    independent parse with bibtexparser 1.x (installed in a scratch venv outside the repository) reads 271 entries
    with 271 unique keys.

## Flags for the orchestrator

1. HATA2006 not merged (Finding 1); cite it only after reading the byline.
2. ICHIKAWA2002IEEJ author by linked records (Finding 4); WATANABE2000BUTSURI author set against a JaLC artefact
   (Finding 3).
3. New evidence label PAGE_CHECKED for 9 no-DOI items (header of `references.bib`); these are not registry-verified.
4. The narrative above is written by hand; everything between the GENERATED markers is regenerated by `report`.

<!-- BEGIN GENERATED BY tools/bib/b5_check.py report -->

### Counts (generated)

| quantity | value |
|---|---|
| proposals checked | 54 |
| L8 | 29 |
| L9 | 25 |
| with a DOI (registry route: Crossref / JaLC / DataCite) | 45 (43 / 1 / 1) |
| without a DOI (page route) | 9 |
| VERIFIED (every field agrees, or differs only by a declared record artefact) | 43 |
| VERIFIED-CORRECTED (a field corrected to the record value) | 1 |
| PAGE-CHECKED (no registry record; URL resolves, page prints the fields) | 9 |
| field mismatches (counted) | 5 |
| entries with counted mismatches | 3 |
| entries with record normalisations (logged) | 12 |
| entries whose proposal had formatting defects (fixed) | 7 |
| entries with a value set rather than copied (b5_routes.yaml) | 3 |
| NOT MERGED | 1 |
| DUPLICATE (not merged) | 0 |
| MERGED into references.bib (section 4o) | 53 |
| references.bib entries after merge | 271 |
| references.bib verified / unverified section | 265 / 6 |
| validation errors | 0 |
| doi fields not backed by a cached record | 0 |
| report-text citations checked (lines naming a proposal DOI) | 58 |
| report-text field differences (see list) | 0 |
| citation keys used in docs/*.md and docs/source_map.tsv (distinct) | 93 |
| citation keys missing from references.bib | 0 |

### Per-entry table (generated; full rows in B5_results.tsv)

| key | proposer | verdict | detail | route | fields compared | differences |
|---|---|---|---|---|---|---|
| LEE2000MT | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | normalised: the record title's HTML-escaped SUB markup transcribed as a subscript |
| IAKOUBOVSKII2008PRB | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| IAKOUBOVSKII2008MRT | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| RAU1996 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| BASHA2022 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | none |
| ISABELL1999 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| FISCHIONE1020 | L8 | MERGED | PAGE-CHECKED | page (no registry record) | document, owner, title | none |
| KITAJIMA1994 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | normalised: family names deposited in capitals (KITAJIMA) read as capitalised; normalised: container title deposited in capitals ('SHINKU') read as capitalised; normalised: closing full stop of the J-STAGE record title dropped |
| ROBINSON2004SVC | L8 | MERGED | PAGE-CHECKED | page (no registry record) + Crossref query | author family name, booktitle, date and place, entry title, first page, issn, last page, place, publisher | none |
| MITCHELL2015 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | author[1].given (given-form, Crossref) |
| YAMAMURA1996 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | normalised: family names deposited in capitals (YAMAMURA, TAWARA) read as capitalised; normalised: given names deposited in capitals (YASUNORI, HIRO) read as capitalised; normalised: record title deposited in capitals; the proposal's capitalisation of the same words is used |
| LUHMANN2017 | L8 | MERGED | VERIFIED | Crossref /works + arXiv OAI-PMH | author, container-title, issue, pages, title, version v1, volume, year | none |
| HATA2006 | L8 | NOT MERGED | NOT-MERGED | Crossref /works + CiNii, openalex (HTTP 200), s2 (HTTP 200), oup (HTTP 403) | author, container-title, issue, pages, title, volume, year | author-count: '1' -> '6' [CiNii; entry not merged (see reason)]; author[1].family: 'Hata' -> 'Sosiati' [CiNii; entry not merged (see reason)]; author[1].given: 'S.' -> 'Harini' [CiNii; entry not merged (see reason)]; not merged: author list unresolved. The Crossref record (OUP deposit) lists one author, 'S. Hata' (OpenAlex marks him as the corresponding author); the CiNii/NII article record (NAID 10018006189) lists six authors starting with H. Sosiati (Sosiati, Hata, Kuwano, Itakura, Nakano, Umakoshi); Semantic Scholar lists the same six starting with S. Hata; the printed byline (academic.oup.com) answered HTTP 403 and PubMed has no record. The proposal (author = 'Hata, S.') would cite a six-author paper under one name, and the author order cannot be settled from the records. Title, journal, volume 55, issue 1, pages 23-26 and year 2006 agree in all records; merge once the byline is read. |
| WATANABE1999HK | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | normalised: family names deposited in capitals (WATANABE, MIYATA, ICHIKAWA) read as capitalised; normalised: closing full stop of the J-STAGE record title dropped |
| WATANABE2000BUTSURI | L8 | MERGED | VERIFIED | JaLC (Crossref 404) | author, container-title, issue, pages, title, volume, year | author[3].family: 'Ichikawa' -> 'lchikawa' [JaLC; proposal kept (record artefact; tools/bib/b5_routes.yaml accepted_residual)] |
| ICHIKAWA2002IEEJ | L8 | MERGED | VERIFIED | Crossref /works + J-STAGE page | author, container-title, issue, pages, title, volume, year | author (record-silent, Crossref); author (record-silent, J-STAGE); title (record-silent, J-STAGE); container-title (record-silent, J-STAGE); normalised: the record title carries the issue's feature title 'Nanotechnologies Support The 21st Century Based on The Information and The Communication Technologies.' before the article title; that prefix is removed (declared in tools/bib/b5\_routes.yaml); normalised: closing full stop of the J-STAGE record title dropped |
| TAKAKUWA2002HK | L8 | MERGED | VERIFIED | Crossref /works + J-STAGE page | author, container-title, issue, pages, title, volume, year | author (record-silent, J-STAGE); title (record-silent, J-STAGE); container-title (record-silent, J-STAGE); normalised: family names deposited in capitals (TAKAKUWA) read as capitalised; normalised: the record title carries the issue's feature title 'Oxidation Mechanism of Silicon Surface.' before the article title; that prefix is removed (declared in tools/bib/b5\_routes.yaml); normalised: closing full stop of the J-STAGE record title dropped |
| HONDA1988 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | normalised: family names deposited in capitals (HONDA, OHSAWA) read as capitalised; normalised: container title deposited in capitals ('SHINKU') read as capitalised; normalised: closing full stop of the J-STAGE record title dropped |
| HATTORI2001 | L8 | MERGED | VERIFIED | Crossref /works + J-STAGE page | author, container-title, issue, pages, title, volume, year | normalised: family names deposited in capitals (HATTORI) read as capitalised; normalised: container title deposited in capitals ('SHINKU') read as capitalised; normalised: the Crossref record's title is empty; the English title of the J-STAGE landing page (citation\_title, cached as HATTORI2001.jstage.json) is used |
| KOMIYA1997 | L8 | MERGED | VERIFIED | Crossref /works + J-STAGE page | author, container-title, issue, pages, title, volume, year | normalised: family names deposited in capitals (KOMIYA, AWAJI, HORII, TOMITA) read as capitalised; normalised: the record title carries the issue's feature title 'Frontiers in Crystallography with Synchrotron Radiation. Utilizing of Various Properties of Synchrotron Radiation.' before the article title; that prefix is removed (declared in tools/bib/b5\_routes.yaml); normalised: closing full stop of the J-STAGE record title dropped |
| ERHARD2024 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| ERHARD2024DATA | L8 | MERGED | VERIFIED | DataCite (Crossref 404) | author, container-title, title, year | none |
| TINOCO2003 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| TINOCO2006 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| KIM1996JVSTB | L8 | MERGED | VERIFIED-CORRECTED | Crossref /works | author, container-title, issue, pages, title, volume, year | container-title: 'Journal of Vacuum Science and Technology B' -> 'Journal of Vacuum Science & Technology B: Microelectronics and Nanometer Structures Processing, Measurement, and Phenomena' [Crossref; corrected to the record value] |
| SUGITA1996 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | volume (dash-form, Crossref) |
| MCCARTNEY2005 | L8 | MERGED | VERIFIED | Crossref /works + Crossref (2nd DOI) | author, container-title, issue, pages, title, volume, year | none |
| WATANABE1998PRL | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| HIMPSEL1988 | L8 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | normalised: the record title's MathML transcribed (subscripts, spaces) |
| RODER2016 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | none |
| CHANG2016 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | none |
| MIR2017 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | none |
| PATON2021 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | none |
| NORD2020 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| BALLABRIGA2013 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| PLACKETT2013 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| MCMULLAN2009 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| MCMULLAN2007 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| DIMOVA2025 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | normalised: the record title's MathML transcribed (subscripts, spaces) |
| HERRING2013MM | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| HERRING2015MM | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| SNOECK2014MM | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| HARADA2006JAP | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| PUTTOCK2022 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| REIDY2021 | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | none |
| HERRING2026MICRON | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, pages, title, volume, year | none |
| FANG2024MM | L9 | MERGED | VERIFIED | Crossref /works | author, container-title, issue, pages, title, volume, year | normalised: the record title is doubly HTML-escaped ('&amp;lt;'); unescaped twice |
| SATO2008HITACHIREVIEW | L9 | MERGED | PAGE-CHECKED | page (no registry record) + Crossref query | author family name, entry title, first page, last page, running head | none |
| UVIC_STEHM_PAGE | L9 | MERGED | PAGE-CHECKED | page (no registry record) | entry title, owner | none |
| UVIC_EMRG_FACILITIES | L9 | MERGED | PAGE-CHECKED | page (no registry record) | entry title, owner, quoted sentence | none |
| HERRING2012STEHMSLIDES | L9 | MERGED | PAGE-CHECKED | page (no registry record) | author, entry title, meeting, owner, place | none |
| HERRING2013STEHMSLIDES | L9 | MERGED | PAGE-CHECKED | page (no registry record) | author, entry title, meeting, owner | none |
| QD_MERLINEM_PAGE | L9 | MERGED | PAGE-CHECKED | page (no registry record) | entry title, owner | none |
| KRAJNAK2023MMC | L9 | MERGED | PAGE-CHECKED | page (no registry record) | abstract number, author family name, entry title, form, meeting, owner | none |

### Every counted mismatch, with the record's value (generated)

| key | field | proposal | record | record source | resolution |
|---|---|---|---|---|---|
| HATA2006 | author-count | 1 | 6 | CiNii | entry not merged (see reason) |
| HATA2006 | author[1].family | Hata | Sosiati | CiNii | entry not merged (see reason) |
| HATA2006 | author[1].given | S. | Harini | CiNii | entry not merged (see reason) |
| WATANABE2000BUTSURI | author[3].family | Ichikawa | lchikawa | JaLC | proposal kept (record artefact; tools/bib/b5_routes.yaml accepted_residual) |
| KIM1996JVSTB | container-title | Journal of Vacuum Science and Technology B | Journal of Vacuum Science & Technology B: Microelectronics and Nanometer Structures Processing, Measurement, and Phenomena | Crossref | corrected to the record value |

Differences not counted as mismatches (record silent, white space, same initials, dash form):

* MITCHELL2015: author[1].given proposal 'David R. G.', Crossref record 'D.R.G.' (given-form)
* ICHIKAWA2002IEEJ: author proposal 'Ichikawa, Masakazu', Crossref record '(none)' (record-silent)
* ICHIKAWA2002IEEJ: author proposal 'Ichikawa, Masakazu', J-STAGE record '(none)' (record-silent)
* ICHIKAWA2002IEEJ: title proposal 'Technology to Observe Si Surface and Interfaces on The Nanoscale', J-STAGE record '' (record-silent)
* ICHIKAWA2002IEEJ: container-title proposal 'The Journal of The Institute of Electrical Engineers of Japan', J-STAGE record '(none)' (record-silent)
* TAKAKUWA2002HK: author proposal 'Takakuwa, Yuji', J-STAGE record '(none)' (record-silent)
* TAKAKUWA2002HK: title proposal 'Growth Kinetics of Very Thin Oxide Layers on Si(001) Surface Monitored in Real-time by Auger Electron Spectroscopy Combined with Reflection High Energy Electron Diffraction', J-STAGE record '' (record-silent)
* TAKAKUWA2002HK: container-title proposal 'Hyomen Kagaku', J-STAGE record '(none)' (record-silent)
* SUGITA1996: volume proposal '100–101', Crossref record '100-101' (dash-form)

### Record normalisations applied before comparing and rendering (generated)

* LEE2000MT: the record title's HTML-escaped SUB markup transcribed as a subscript
* KITAJIMA1994: family names deposited in capitals (KITAJIMA) read as capitalised
* KITAJIMA1994: container title deposited in capitals ('SHINKU') read as capitalised
* KITAJIMA1994: closing full stop of the J-STAGE record title dropped
* YAMAMURA1996: family names deposited in capitals (YAMAMURA, TAWARA) read as capitalised
* YAMAMURA1996: given names deposited in capitals (YASUNORI, HIRO) read as capitalised
* YAMAMURA1996: record title deposited in capitals; the proposal's capitalisation of the same words is used
* WATANABE1999HK: family names deposited in capitals (WATANABE, MIYATA, ICHIKAWA) read as capitalised
* WATANABE1999HK: closing full stop of the J-STAGE record title dropped
* ICHIKAWA2002IEEJ: the record title carries the issue's feature title 'Nanotechnologies Support The 21st Century Based on The Information and The Communication Technologies.' before the article title; that prefix is removed (declared in tools/bib/b5\_routes.yaml)
* ICHIKAWA2002IEEJ: closing full stop of the J-STAGE record title dropped
* TAKAKUWA2002HK: family names deposited in capitals (TAKAKUWA) read as capitalised
* TAKAKUWA2002HK: the record title carries the issue's feature title 'Oxidation Mechanism of Silicon Surface.' before the article title; that prefix is removed (declared in tools/bib/b5\_routes.yaml)
* TAKAKUWA2002HK: closing full stop of the J-STAGE record title dropped
* HONDA1988: family names deposited in capitals (HONDA, OHSAWA) read as capitalised
* HONDA1988: container title deposited in capitals ('SHINKU') read as capitalised
* HONDA1988: closing full stop of the J-STAGE record title dropped
* HATTORI2001: family names deposited in capitals (HATTORI) read as capitalised
* HATTORI2001: container title deposited in capitals ('SHINKU') read as capitalised
* HATTORI2001: the Crossref record's title is empty; the English title of the J-STAGE landing page (citation\_title, cached as HATTORI2001.jstage.json) is used
* KOMIYA1997: family names deposited in capitals (KOMIYA, AWAJI, HORII, TOMITA) read as capitalised
* KOMIYA1997: the record title carries the issue's feature title 'Frontiers in Crystallography with Synchrotron Radiation. Utilizing of Various Properties of Synchrotron Radiation.' before the article title; that prefix is removed (declared in tools/bib/b5\_routes.yaml)
* KOMIYA1997: closing full stop of the J-STAGE record title dropped
* HIMPSEL1988: the record title's MathML transcribed (subscripts, spaces)
* DIMOVA2025: the record title's MathML transcribed (subscripts, spaces)
* FANG2024MM: the record title is doubly HTML-escaped ('&amp;lt;'); unescaped twice

### Values set rather than copied from the record (generated from tools/bib/b5_routes.yaml)

* WATANABE2000BUTSURI: author = 'Watanabe, Heiji and Miyata, Noriyuki and Ichikawa, Masakazu'
* ICHIKAWA2002IEEJ: author = 'Ichikawa, Masakazu'
* FISCHIONE1020: howpublished = 'Manufacturer documents, \url{https://www.fischione.com/files/products/17/sp1020.pdf} and \url{https://www.fischione.com/files/products/17/pb1020.pdf}'; url = 'https://www.fischione.com/products/m1020'

### Page checks of the entries without a DOI (generated)

| key | URL | HTTP | kind | SHA-256 (first 16) | accessed (UTC) | strings found / tested |
|---|---|---|---|---|---|---|
| FISCHIONE1020 | https://www.fischione.com/products/m1020 | 200 | HTML | 19f5f1052cb0da12 | 2026-09-24T09:31:58Z | 2 / 2 |
| FISCHIONE1020 | https://www.fischione.com/files/products/17/sp1020.pdf | 200 | PDF, 2 p. | cd77bf838ca3b309 | 2026-09-24T09:31:58Z | 3 / 3 |
| FISCHIONE1020 | https://www.fischione.com/files/products/17/pb1020.pdf | 200 | PDF, 5 p. | 5abf7728d49164b2 | 2026-09-24T09:31:59Z | 3 / 3 |
| ROBINSON2004SVC | https://physics.byu.edu/faculty/allred/docs/svc04.pdf | 200 | PDF, 9 p. | 99574c40268d5c47 | 2026-09-24T09:32:04Z | 18 / 18 |
| SATO2008HITACHIREVIEW | https://www.hitachihyoron.com/rev/pdf/2008/r2008_03_104.pdf | 200 | PDF, 4 p. | f170b8851bc579b1 | 2026-09-24T09:33:17Z | 9 / 9 |
| UVIC_STEHM_PAGE | https://www.uvic.ca/research/advancedmicroscopy/about/microscopes/stehm/index.php | 200 | HTML | a9a8881eac91adb5 | 2026-09-24T09:33:17Z | 3 / 3 |
| UVIC_EMRG_FACILITIES | https://onlineacademiccommunity.uvic.ca/emicro/facilities/ | 200 | HTML | eabe26da14f7ea8e | 2026-09-24T09:33:19Z | 3 / 3 |
| HERRING2012STEHMSLIDES | https://www.uvic.ca/research/advancedmicroscopy/assets/docs/STEHM/STEHM_Special_Features_CAMTEC_2013.pdf | 200 | PDF, 28 p. | d8a8e59131fb8c58 | 2026-09-24T09:33:21Z | 5 / 5 |
| HERRING2013STEHMSLIDES | https://www.uvic.ca/research/advancedmicroscopy/assets/docs/STEHM/STEHM_Presentation_CAMTEC_July_2013.pdf | 200 | PDF, 55 p. | 694bcaf151a13c24 | 2026-09-24T09:33:27Z | 4 / 4 |
| QD_MERLINEM_PAGE | https://quantumdetectors.com/products/merlinem/ | 200 | HTML | 001f42c145df2584 | 2026-09-24T09:33:31Z | 2 / 2 |
| KRAJNAK2023MMC | https://www.mmc-series.org.uk/abstract/1024-merlinem-hybrid-pixel-array-counting-detector-for-transmission-electron-microscopy.html | 200 | HTML | dd8473827a932eb9 | 2026-09-24T09:33:31Z | 8 / 8 |

### Other routes (generated)

* ROBINSON2004SVC: Crossref query.bibliographic 'Removing Surface Contaminants from Silicon Wafers to Facilitate EUV Optical Characterization Robinson 2004': 5 results, none with the entry's title
* HATA2006: CiNii record https://cir.nii.ac.jp/crid/1571135650339084160: authors Sosiati, Harini; Hata, Satoshi; Kuwano, Noriyuki; Itakura, Masaru; Nakano, Takayoshi; Umakoshi, Yukichi
* HATA2006: Europe PMC search by DOI: HTTP 200, 0 hits (not in PubMed/Europe PMC)
* HATA2006: OpenAlex work record (aggregator; corroboration only): HTTP 200 -- authorships: Satoshi Hata (raw name 'S. Hata', is_corresponding True)
* HATA2006: Semantic Scholar paper record (aggregator; corroboration only): HTTP 200 -- authors: S. Hata; H. Sosiati; N. Kuwano; M. Itakura; T. Nakano; Y. Umakoshi
* HATA2006: publisher landing page via doi.org, requested as text/html (for the printed byline): HTTP 403
* ICHIKAWA2002IEEJ: J-STAGE page: title ["シリコン表面界面のナノスケール観察技術"]; authors ["市川 昌和"]
* ICHIKAWA2002IEEJ: linked-record check {"kanji": "市川 昌和", "other_key": "WATANABE2000BUTSURI", "other_ja": "市川 昌和", "other_en": "lchikawa, Masakazu", "same_kanji": true, "given_equal": true, "family_equal": false}
* TAKAKUWA2002HK: J-STAGE page: title ["極薄シリコン酸化膜形成過程のリアルタイムRHEED-AES観察"]; authors ["高桑 雄二"]
* HATTORI2001: J-STAGE page: title ["Studies on Ultrathin Silicon Oxide Films and Their Current Problems"]; authors ["Hattori, Takeo"]
* KOMIYA1997: J-STAGE page: title ["Characterization of Thin Films with X-ray Total Reflection Technology"]; authors ["Komiya, Satoshi", "Awaji, Naoki", "Horii, Yoshimasa", "Tomita, Hirofumi"]
* MCCARTNEY2005: second Crossref record 10.1093/jmicro/54.3.239: every compared field agrees with the proposal
* SATO2008HITACHIREVIEW: Crossref query.bibliographic 'Hitachi's High-end Analytical Electron Microscope HF-3300 Sato Hitachi Review 2008': 5 results, none with the entry's title
* UVIC_EMRG_FACILITIES: site REST record: page created 2020-01-20T21:22:32, modified 2023-01-04T22:08:48

### Duplicates and key collisions (generated)

* none: no proposal has the DOI, arXiv id, key or (first author + title) of an entry of references.bib, and L8 and L9 share none.

Related items with the same first author and a similar title that are NOT duplicates:

* HARADA2006JAP ~ [P47] (title similarity 0.89): related title, same first author

### Formatting defects of the proposals fixed (generated)

* 7 x article number in an eid field (references.bib writes article numbers as pages)
* 1 x unescaped underscore

### Report text: citations printed next to each proposal DOI in L8/L9 reports (generated)

58 report lines name a proposal DOI; for each, the citation printed before the DOI in the same table cell or sentence was tested for the record's volume, first page (or article number) and year.

No difference found.

### Citation keys used in docs/*.md and docs/source_map.tsv (generated)

93 distinct keys of references.bib are used; citation-like tokens missing from references.bib: none.
Tokens of non-citation ID families were excluded: source_map claim ids (SM\d+); model_assumptions row ids B16-B99 (B(?:1[6-9]|[2-9]\d)); model_assumptions row ids B1-B9 (bib book keys are zero-padded, B01-B15) (B\d); test ids (T\d+); agent, item, section and source ids of the reports (E\d+|D\d+|N\d+|L\d+|A\d+|X\d+|H\d+|U\d|P\d|R\d|O\d|M\d|S\d|C\d|I\d+(?:\.\d+)?); PubMed Central ids (PMC\d+); page numbers (e.g. L1772) (L\d{4}) -- 167 distinct tokens.

Validation of docs/references.bib: {"entries": 271, "unique_keys": 271, "verified_section": 265, "unverified_section": 6, "with_doi": 241}; errors: none; doi fields without a cached record carrying the same DOI: none

<!-- END GENERATED -->
