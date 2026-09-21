# B2 — Bibliography verification log (companion to `references.bib`)

Prepared: 2026-09-21
Agent: bibliography/verification pass following `B_literature.md`
Tooling available: **WebSearch only**. Every scholarly host (doi.org, Crossref,
OpenAlex, Semantic Scholar, PMC, arXiv, all publishers) is BLOCKED by the egress
proxy. No attempt was made to route around it. **No DOI in `references.bib` was
constructed, guessed or pattern-completed.**

## Label policy used in this pass

| Label | Meaning |
|---|---|
| `METADATA_VERIFIED` | Instruction-file record (default for books per instruction §3 preamble), or a search-index result carrying a DOI-bearing publisher URL / bibliographic listing. |
| `METADATA_VERIFIED(index)` | Corroborated across >=2 independently phrased index queries (inherited from `B_literature.md`). |
| `METADATA_VERIFIED(index, single)` | One query only. Weaker. |
| `+ABSTRACT(index)` | Abstract-level text surfaced by the search summariser. Weaker than `SECTION_READ`. |
| `SECTION_READ` | The technical passage was actually inspected (instruction file: [P04]; B report: GitHub READMEs). |
| `PROJECT_INPUT` | Asserted by the project instruction file. |
| `UNVERIFIED` | Provenance unresolved, or identity rests on one summariser sentence. |

**Upgrade rule applied here (as instructed):** a label was upgraded ONLY when a
DOI-bearing publisher URL or an explicit bibliographic listing (volume/pages/year)
appeared in a search-result URL or result title. Summariser prose alone NEVER
upgraded a label.

---

## Per-entry search record

### [P01] Osakabe, Matsuda, Endo & Tonomura, JJAP **27**, L1772-L1774 (1988)

| # | Query (verbatim) | Result URLs seen | Outcome |
|---|---|---|---|
| 1 | `Osakabe Matsuda Endo Tonomura "Observation of Atomic Steps by Reflection Electron Holography" Japanese Journal of Applied Physics 1988` | https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200415 ; https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200414 ; https://patents.google.com/patent/EP0378237B1/en ; https://data.epo.org/publication-server/rest/v1.2/patents/EP0378237NWA2/document.html | **No URL for [P01] itself.** The index returned [P08] and [P09] instead. |
| 2 | `"10.1143/JJAP.27.L1772" OR "JJAP.27.L1772" Osakabe reflection electron holography atomic steps` | https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200414 ; https://academic.oup.com/jmicro/article/70/1/3/5862540 ; https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4998788 | **No [P01] URL.** An exact-DOI query returned no page carrying that DOI. |
| 3 | `iopscience "JJAP" volume 27 1988 Osakabe "reflection electron holography" L1772 letters` | https://iopscience.iop.org/volume/1347-4065/27 ; https://iopscience.iop.org/issue/1347-4065/27/4A ; https://iopscience.iop.org/article/1347-4065/... (generic JJAP pages only) | Only generic JJAP volume/issue TOC pages; **none carries L1772**. |

**RESULT: label NOT upgraded.** `METADATA_VERIFIED(index)` for authors/title/journal/volume/year;
DOI 10.1143/JJAP.27.L1772 stays `PROJECT_INPUT` (instruction-file record; not seen in any URL in
this pass). Page form L1772-L1774 vs 1772-1774 remains **UNVERIFIED at the digit level** — queries
2 and 3 again reported "27, 1772-1774" without the Letters `L`.

> **REPEAT OF THE B-REPORT WARNING (§0.4), reproduced in this pass.** Query 2's summariser
> attributed the pi / 0.9pi phase shifts on (111)Au and (111)Pt to [P01]. **They belong to [P09]
> (Banzhof, Herrmann & Lichte).** The mis-attribution reproduced identically in an independent
> session, so it is systematic. Do not let it into the paper.

### [P02] Osakabe, Endo, Matsuda, Tonomura & Fukuhara, PRL **62**, 2969-2972 (1989)

| # | Query (verbatim) | Result URL carrying the data | Outcome |
|---|---|---|---|
| 4 | `Osakabe Endo Matsuda Tonomura Fukuhara "Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography" Physical Review Letters 62 2969` | **https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.62.2969** (result title = the exact article title) | **DOI-bearing publisher URL seen with the exact title.** |

Also re-returned: Hitachi ARL affiliation (Kokubunji, Tokyo 185), issue date 19 June 1989,
GaAs(110) screw dislocation, ~0.01 Angstrom precision (all `+ABSTRACT(index)`).

**RESULT: label CONFIRMED at `METADATA_VERIFIED(index)`** (DOI-bearing APS URL re-seen in a second,
independent session). Pages 2969-2972: the index reported only the first page 2969; the end page
2972 comes from the instruction file. DOI matches the instruction file exactly.

### [P02E] Erratum, PRL **63**, 584 (1989)

| # | Query (verbatim) | Result URL | Outcome |
|---|---|---|---|
| 5 | `Physical Review Letters 63 584 1989 erratum Osakabe "surface undulation" reflection electron holography` | **https://journals.aps.org/prl/issues/63/5** (APS volume-63 issue-5 table of contents) ; https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.62.2969 | Issue-level bibliographic listing re-seen; **no URL for the erratum itself**. |

The PRL vol.-63 issue-5 TOC URL has now appeared in two independent sessions, so the *existence*
of the containing issue is corroborated twice; the summariser adds "page 584, published 31 July
1989, same five authors" — **summariser prose, so it did not upgrade anything.**

**RESULT: existence `METADATA_VERIFIED(index)` (upgraded from `(index, single)` by the repeat
TOC hit); DOI 10.1103/PhysRevLett.63.584.3 remains an instruction-file record; the erratum's
CONTENT remains `UNVERIFIED`.** Instruction file, §7: "Its existence was verified; its
corrections were not evaluated here." **Every number taken from [P02] must be re-checked
against this erratum before publication.**

### [P03] Banzhof & Herrmann, *Ultramicroscopy* **48**, 475-481 (1993)

| # | Query (verbatim) | Result URL | Outcome |
|---|---|---|---|
| 6 | `Banzhof Herrmann "Reflection electron holography" Ultramicroscopy 1993 volume 48 pages 475` | No URL for [P03]. Nearest returned: https://www.sciencedirect.com/science/article/abs/pii/003960289390046M (= [P28] Cowley, *Surf. Sci.* 1993) | **No publisher URL for [P03] was returned.** |

Summariser restated "Ultramicroscopy 48, 475, 1993, DOI 10.1016/0304-3991(93)90123-F" —
**prose only, no URL carried that DOI.**

**RESULT: label NOT upgraded.** Identity stays `METADATA_VERIFIED` on the strength of the
**instruction-file record** (§7: "Bibliographic identity checked; full text not inspected"),
which supplies the ScienceDirect PII URL `.../pii/030439919390123F`. The DOI is carried in the
.bib **flagged**: its only provenance is summariser text (B report + this session). Abstract still
not obtained in any session. **Do not attribute any equation or number to [P03].**

### [P09] Banzhof, Herrmann & Lichte, vol. **20**, 450-456 (1992) — the Au(111)/Pt(111) step paper

| # | Query (verbatim) | Result URL carrying the data | Outcome |
|---|---|---|---|
| 7 | `Banzhof Herrmann Lichte "Reflection electron microscopy and interferometry of atomic steps on gold and platinum single crystal surfaces" 1992 volume 20 pages 450` | **https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200414** (result title = the exact article title) | **DOI-bearing publisher URL with exact title.** |

That same Wiley DOI URL was returned by **six** differently-phrased queries in this session
(#1, #2, #3, #4, #5, #6) plus the B report's queries. Pages 450-456 and the year 1992 were
restated by the summariser (prose). The pi / 0.9pi monatomic-step phase shifts on (111)Au and
(111)Pt were again attached to this record.

**RESULT: `METADATA_VERIFIED(index) +ABSTRACT(index)` CONFIRMED** (title + DOI now rest on a
DOI-bearing publisher URL seen repeatedly in two independent sessions). Pages/year remain
summariser-level. **This, not [P01], is the source of pi and 0.9pi.**

### [P08] Osakabe, "Observation of surfaces by reflection electron holography", vol. **20**, 457-462 (1992)

| # | Query (verbatim) | Result URLs carrying the data | Outcome |
|---|---|---|---|
| 8 | `"Observation of surfaces by reflection electron holography" Osakabe "Journal of Electron Microscopy Technique" volume 20 1992 pages 457` | **https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200415** (result title = exact article title) **and https://pubmed.ncbi.nlm.nih.gov/1498359/** (result title = exact article title) | DOI-bearing publisher URL **plus** a PubMed bibliographic record URL, both titled with the exact article title. |

**DOI 10.1002/jemt.1070200415 CONFIRMED** from the publisher URL (returned by six queries this
session). PMID 1498359 CONFIRMED from the PubMed record URL.

**Journal / volume / pages / year — the specific item the task asked me to check:**
the summariser stated "**Microscopy Research and Technique, volume 20, pages 457-462, 1992**" and
explicitly corrected my query's "Journal of Electron Microscopy Technique". It stated the same
journal title for [P09] in query #7. **That is summariser prose in both cases — no URL displayed a
masthead, volume or page range**, and `onlinelibrary.wiley.com` / `pubmed.ncbi.nlm.nih.gov` are
blocked, so neither record could be opened. The Wiley DOI stem is `jemt`. **Which masthead volume
20 (1992) carried is therefore NOT resolved from any URL** — do not assert one without checking.

**RESULT: `METADATA_VERIFIED(index) +ABSTRACT(index)`** for title + DOI + PMID (upgraded route:
publisher DOI URL + PubMed record URL). Journal name, volume, pages and year stay at
summariser level and are flagged in the .bib note. Label NOT upgraded beyond that.

### [P18] Peng & Cowley, *Acta Cryst.* **A42**, 545-552 (1986)

| # | Query (verbatim) | Result URLs | Outcome |
|---|---|---|---|
| 9 | `Peng Cowley "Dynamical diffraction calculations for RHEED and REM" Acta Crystallographica A42 545 1986` | **No URL for [P18].** Returned instead: https://www.numis.northwestern.edu/Research/Articles/1990/2Bloch%20Waves%20and%20Multislice%20in%20Transmission%20and%20Reflection%20Diffraction.pdf (= [P21]) ; https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200407 (= [P12]) ; https://www.science.org.au/fellowship/fellows/biographical-memoirs/john-maxwell-cowley-1923%E2%80%932004 | `journals.iucr.org` did not surface. |

**RESULT: label NOT upgraded.** `METADATA_VERIFIED(index)` for authors/title/journal/volume/pages
(inherited from the B report's two corroborating queries and the Acta Cryst A42 part-6 TOC hit).
**DOI 10.1107/S0108767386098756 remains summariser-only in every session — it is carried in the
.bib flagged `DOI UNVERIFIED`, per the B report.** Abstract still not obtained.

**Side gains from query 9** (recorded because they upgrade other entries):
* **[P12]** Peng, Gjonnes & Gjonnes — DOI-bearing Wiley URL
  https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200407 seen with
  the **full** title *"Bloch wave treatment of symmetry and multiple beam cases in reflection high
  energy electron diffraction and reflection electron microscopy"* (the B report had it
  abbreviated). Title + DOI **upgraded to a DOI-bearing-URL route**; the unabbreviated title is
  used in the .bib.
* **[P21]** Ma & Marks 1990 — a Northwestern (Marks group) PDF URL under `/Research/Articles/1990/`
  whose filename is the exact title. Corroborates title + year; **not** a bibliographic listing
  (no volume/pages), so no label change.

### [P30] Hytch, Houdellier, Hue & Snoeck, *Nature* **453**(7198), 1086-1089 (2008)

| # | Query (verbatim) | Result URLs carrying the data | Outcome |
|---|---|---|---|
| 10 | `Hytch Houdellier Hue Snoeck "Nanoscale holographic interferometry for strain measurements in electronic devices" Nature 453 1086 2008 doi 10.1038/nature07049` | **http://www.nature.com/nature/journal/v453/n7198/abs/nature07049.html** (publisher URL embedding **v453 / n7198** and the article id `nature07049` = the DOI suffix) **and http://www.ncbi.nlm.nih.gov/pubmed/18563161** (PubMed record, exact title) | Publisher URL confirms **volume 453, number 7198**; PubMed record confirms the title and gives **PMID 18563161**. |

**RESULT: `METADATA_VERIFIED(index)` CONFIRMED and strengthened** — volume and issue number now rest
on a publisher URL, not on prose. DOI 10.1038/nature07049 is corroborated by the `nature07049`
article id in that URL. PMID 18563161 **added** (provenance: PubMed record URL in the index).
Pages 1086-1089 remain summariser-level. Title confirmed with the plural "**measurements**".

### [P31] Hytch, Houdellier, Hue & Snoeck, *Ultramicroscopy* **111**(8), 1328-1337 (2011)

| # | Query (verbatim) | Result URLs carrying the data | Outcome |
|---|---|---|---|
| 11 | `Hytch Houdellier Hue Snoeck "Dark-field electron holography for the measurement of geometric phase" Ultramicroscopy 111 2011 1328-1337` | **https://www.sciencedirect.com/science/article/abs/pii/S0304399111001586** (publisher URL, exact title) **and https://www.osti.gov/etdeweb/biblio/22204503** (OSTI/ETDEWEB bibliographic record, exact title) | Publisher article URL + an independent bibliographic listing. |

**RESULT: `METADATA_VERIFIED(index) +ABSTRACT(index)` CONFIRMED** via a publisher PII URL and an
OSTI bibliographic record. **No DOI was obtained in any session, so the .bib entry has NO `doi`
field** — only the PII and the publisher URL. Volume 111, issue 8, pages 1328-37 and the July 2011
date were restated by the summariser (prose). The four-contribution statement (crystalline,
electrostatic, magnetic, geometric) reproduced verbatim for a third time.
**The geometric-phase equation and its SIGN were still not obtained. Do not quote a sign.**

**Side gains from query 11:**
* **[P32]** Lubk et al. 2014 — publisher URL
  https://www.sciencedirect.com/science/article/abs/pii/S0304399113001939 with the exact title
  *"Dynamic scattering theory for dark-field electron holography of 3D strain fields"*. PII
  **added** to the .bib (the B report had no PII for it). Label route upgraded to publisher-URL.
* The §4 "additional but unverified" item *"Differential phase-contrast dark-field electron
  holography for strain mapping"* now has a PubMed record URL
  https://pubmed.ncbi.nlm.nih.gov/26476802/ (PMID 26476802 confirmed by URL). It stays in the
  UNVERIFIED section because authors, volume, pages and year were never obtained.
* **HoloDark** plug-in vendor page https://www.hremresearch.com/holodark/ seen (software, not a
  citable bibliographic record).

### Z. L. Wang, *Reflection Electron Microscopy and Spectroscopy for Surface Analysis*, CUP 1996

| # | Query (verbatim) | Result URLs carrying the data | Outcome |
|---|---|---|---|
| 12 | `"Reflection Electron Microscopy and Spectroscopy for Surface Analysis" Z. L. Wang Cambridge University Press 1996 ISBN` | **https://www.cambridge.org/core/books/reflection-electron-microscopy-and-spectroscopy-for-surface-analysis/4F3C18408D2D686F43DDEC9CAF213394** (Cambridge Core book record) ; **https://www.cambridge.org/core/books/abs/reflection-electron-microscopy-and-spectroscopy-for-surface-analysis/dynamical-theories-of-rheed/3F7C568D2849A99DFB41DFF34A2A6E52** (Cambridge Core **chapter** page, result title *"Dynamical theories of RHEED (Chapter 3)"*) ; https://www.cambridge.org/cu/academic/subjects/engineering/materials-science/reflection-electron-microscopy-and-spectroscopy-surface-analysis ; ISBN-bearing retailer URLs `/dp/0521482666` (= ISBN-13 9780521482660, hardback) and `/dp/0521017955` (= ISBN-13 9780521017954, paperback) ; https://nanoscience.gatech.edu/zlwang/book/book2.htm (author's own book page) | Publisher book record **plus a publisher chapter record**. |

**RESULT: `METADATA_VERIFIED(index)` CONFIRMED and STRENGTHENED.** The B report stated "the chapter
list could not be retrieved". This pass recovered one chapter with a publisher URL:
**Chapter 3 = "Dynamical theories of RHEED"** (Cambridge Core chapter page; the result title states
"(Chapter 3)" explicitly). Both ISBNs are corroborated by ISBN-bearing URLs. The rest of the chapter
list is **still not obtained**, so the step-contrast/imaging chapters remain unidentified —
`UNVERIFIED` at chapter level except for chapter 3. Publication year 1996 and the "three parts:
diffraction, imaging and spectroscopy" structure remain summariser-level.

### [P17] Ichimiya, JJAP **22**, 176-180 (1983) — surface-parallel multislice RHEED

| # | Query (verbatim) | Result URL carrying the data | Outcome |
|---|---|---|---|
| 13 | `Ichimiya 1983 "Many-beam calculation of reflection high energy electron diffraction" multi-slice method Japanese Journal of Applied Physics 22 176` | **https://www.osti.gov/etdeweb/biblio/6510020** — OSTI/ETDEWEB bibliographic record whose result title is the **exact** article title *"Many-beam calculation of reflection high energy electron diffraction (RHEED) intensities by the multi-slice method"* | Independent bibliographic listing found. |

**RESULT: label UPGRADED in route.** [P17] already had the strongest possible secondary
provenance — its citation string was **read verbatim** (`SECTION_READ`) in the
`sim-trhepd-rheed` README, by the authors of the field's own RHEED code. This pass adds an
**independent bibliographic-index record (OSTI) carrying the exact title**. Label:
`METADATA_VERIFIED(index) + SECTION_READ(secondary citation in sim-trhepd-rheed README)`.

**DOI: NOT ADDED.** The summariser offered `10.1143/JJAP.22.176` as prose. It appears in
**neither** the instruction file nor `B_literature.md`, and **no URL carried it**. Under this
task's provenance rule the `doi` field is therefore **omitted**. Recorded here only as an
unadmitted lead.

### [P20] Ma & Marks, "Bloch-wave solution in the Bragg case", *Acta Cryst.* **A45** (1989)

| # | Query (verbatim) | Result URLs carrying the data | Outcome |
|---|---|---|---|
| 14 | `Ma Marks "Bloch-wave solution in the Bragg case" Acta Crystallographica A45 1989 pages` | **http://scripts.iucr.org/cgi-bin/paper?S0108767388010888=** — **IUCr publisher record**, result title *"(IUCr) Bloch-wave solution in the Bragg case"*, URL carries the paper code **S0108767388010888** ; **https://www.osti.gov/etdeweb/biblio/6314963** (OSTI record, exact title) ; https://journals.iucr.org/a/issues/1989/02/00/ (Acta Cryst A **Vol. 45, Part 2, February 1989** TOC) | Publisher record + independent bibliographic record + issue TOC. |

**RESULT: identity UPGRADED to `METADATA_VERIFIED(index)` on a publisher-URL route** — the IUCr
paper code in the B report is now confirmed *inside an IUCr URL* carrying the exact title, and
volume 45 / year 1989 are corroborated by an IUCr issue-TOC URL.

**PAGES STILL UNRESOLVED and therefore OMITTED from the .bib.** The index reported **174-182**
here and in one B-report query, and **182-187** in another B-report query. No URL displayed a page
range. Per "never guess a page number", the entry carries **no `pages` field** and the note states
the conflict. **DOI omitted**: the summariser gave `10.1107/S0108767388010888`, but that string
appears in neither source document except as a *paper code*, and converting a paper code into a DOI
is pattern-completion. The IUCr URL carrying the code is given as `url` instead.

### [P21] Ma & Marks, *Acta Cryst.* **A46**, 11-32 (1990)

| # | Query (verbatim) | Result URLs carrying the data | Outcome |
|---|---|---|---|
| 15 | `Ma Marks "Bloch waves and multislice in transmission and reflection diffraction" Acta Crystallographica A46 1990 11-32` | **https://journals.iucr.org/paper?rc0253=** — IUCr publisher record, result title *"(IUCr) Bloch waves and multislice in transmission and reflection diffraction"* ; **https://journals.iucr.org/a/issues/1990/01/00/** (Acta Cryst A **Vol. 46, Part 1, January 1990** TOC — consistent with pp. 11-32) ; https://www.osti.gov/etdeweb/biblio/6932790 (OSTI) ; https://inis.iaea.org/records/m4253-gq981 (INIS) ; https://www.numis.northwestern.edu/Research/Articles/1990/... (author group PDF) | Publisher record + issue TOC + two independent bibliographic databases. |

**RESULT: `METADATA_VERIFIED(index)` CONFIRMED and strengthened** — title, journal, volume 46 and
year 1990 now rest on IUCr URLs (paper record + Part-1 issue TOC), not on prose. Pages 11-32 remain
summariser-level but are consistent with Part 1. **DOI omitted** (`10.1107/S0108767389009141` was
summariser prose only and is in neither source document); the IUCr paper URL is given instead.
New abstract-level content: "in transmission the two methods yield identical results; for
reflection the Bloch-wave approach yields a stationary solution in multislice, except for a small
effect from surface truncation" (`+ABSTRACT(index)`).

### McCoy & Maksym, *Surface Science* (year disputed) — REQUESTED, **NOT RESOLVED**

| # | Query (verbatim) | Result URLs | Outcome |
|---|---|---|---|
| 16 | `McCoy Maksym Surface Science 1994 RHEED reflection electron microscopy dynamical calculation` | https://www.sciencedirect.com/science/article/abs/pii/003960289390062O (title *"Simulation of high-resolution REM images"*) ; https://www.sciencedirect.com/science/article/abs/pii/003960289390043J (title *"Dynamical theory of RHEED from stepped surfaces"*) ; https://www.semanticscholar.org/paper/Supercell-RHEED-calculations-Maksym/50197ad136884508b5261935ba6a52a92b316a8f | Publisher URLs found, **but no author line and no volume/pages**. |
| 17 | `"McCoy" "Maksym" "Simulation of high-resolution REM images" Surface Science volume pages year` | same ScienceDirect PII URL ; **https://www.semanticscholar.org/paper/Simulation-of-reflection-electron-microscopy-to-of-McCoy-Maksym/e3ceb3ebcf994d4234b2e87a1df7c88192646c0e** — slug carries **`McCoy-Maksym`**, result title *"application to high-resolution imaging of the Si(001)2 x 1 surface"* | Authorship corroborated **by a URL slug**; the summariser this time said **1997**. |
| 18 | `J.M. McCoy P.A. Maksym Surface Science 1994 "reflection electron microscope" images steps Si(001) bilayer monolayer` | No McCoy/Maksym URL at all. The summariser explicitly reported it could not locate the 1994 paper. | Negative result. |

**RESULT: `UNVERIFIED`. Year is contradictory across three sources** — the caller's brief says
**1994**; the ScienceDirect PII string `0039-6028(93)90062-O` carries **93** in its year field; the
query-17 summariser said **1997**. **No year, volume or page range is asserted in the .bib.** Two
distinct McCoy/Maksym-attributed titles exist in the index:
*"Simulation of high-resolution REM images"* (PII 003960289390062O) and *"Simulation of reflection
electron microscopy ... application to high-resolution imaging of the Si(001)2x1 surface"*
(Semantic Scholar). A third relevant title, *"Dynamical theory of RHEED from stepped surfaces"*
(PII 003960289390043J), had **no author attribution** in the index at all.
**Entry placed in the UNVERIFIED CANDIDATES section.** This is scientifically important for Ali
(REM image simulation of Si(001) mono- and bilayer steps is exactly the target observable) and
should be the **first** record resolved when normal network access returns.

### [PAT01] US 4,998,788 "Reflection electron holography apparatus"

Seen incidentally in queries #1, #2 and #5 (no dedicated query was needed):
* **https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4998788** — USPTO full-text
  print URL carrying the patent number, result title *"Reflection electron holography apparatus"*.
* **https://patents.google.com/patent/US4998788** — result title *"US4998788A - Reflection electron
  holography apparatus - Google Patents"* (**confirms the kind code A**).
* **https://patents.google.com/patent/EP0378237B1/en** — result title *"EP0378237B1 - Reflection
  electron holography apparatus - Google Patents"* (**confirms the EP family member**).
* **https://data.epo.org/publication-server/rest/v1.2/patents/EP0378237NWA2/document.html** — EPO
  publication server URL for the same family.

**RESULT: identity UPGRADED from `METADATA_VERIFIED(index, single)` to `METADATA_VERIFIED(index)`**
— number, kind code and title now rest on **four** patent-office / patent-index URLs from two
offices. **Inventors, assignee, filing/priority/grant dates and the whole quoted description
REMAIN `UNVERIFIED`**: `image-ppubs.uspto.gov` and `patents.google.com` are blocked, nothing was
read, and the B report's dates were internally inconsistent with the patent-number series.

### [P09] page-range conflict discovered in this pass

| # | Query (verbatim) | Outcome |
|---|---|---|
| 19 | `Banzhof Herrmann Lichte electron holography reflection gold platinum surfaces Ultramicroscopy 1992 1993 publications list` | Same Wiley DOI URL re-returned. **But the summariser gave pages "20, 450-466"**, where query #7 and the B report both gave **450-456**. |

**CONFLICT RECORDED: 450-456 (2 independent reports) vs 450-466 (1 report).** The .bib keeps
`450--456` and the note carries the conflict. **Verify before citing.** The same answer restated
the pi / 0.9pi result and described the work as "interferometrical and holographical experiments
on the phase shift at steps on (111)Au and (111)Pt single crystal surfaces". No **second**
Banzhof/Herrmann/Lichte paper was found; the pair is [P09] (1992) + [P03] (1993).

### [B08] Peng, Dudarev & Whelan — the 2003/2004 year discrepancy

| # | Query (verbatim) | Result URLs carrying the data | Outcome |
|---|---|---|---|
| 20 | `Peng Dudarev Whelan "High-Energy Electron Diffraction and Microscopy" Oxford University Press 2004 ISBN 0-19-850074-2` | **https://journals.iucr.org/a/issues/2004/04/00/ht5049/index.html** — IUCr book-review page whose **result title is itself a full bibliographic listing**: *"High energy electron diffraction and microscopy. By L. M. Peng, S. L. Dudarev and M. J. Whelan. Pp. 544. Oxford University Press, 2003. Price GBP 69.95. ISBN 0-19-850074-2."* ; https://journals.iucr.org/a/issues/2004/04/00/ht5049/ht5049.pdf ; https://onlinelibrary.wiley.com/doi/pdf/10.1107/S0108767304014412 (same review) ; **https://global.oup.com/academic/product/high-energy-electron-diffraction-and-microscopy-9780198500742** (OUP hardback, ISBN-13 **9780198500742**) ; https://global.oup.com/academic/product/high-energy-electron-diffraction-and-microscopy-9780199602247 (OUP paperback, ISBN-13 9780199602247) | The "2003" claim is now **URL-level**, not prose. |

**RESULT: the discrepancy is REAL and still UNRESOLVED.** The instruction file states **2004**
"following the publisher's publication record"; an IUCr book review published in the 2004/04 issue
states **2003**, 544 pp., ISBN 0-19-850074-2. **The .bib keeps `year = {2004}` (instruction-file
record, per this task's rule) and the note states the conflict and its URL.** New URL-level gains:
OUP product pages confirm ISBN-13 **9780198500742** — the same string inside the instruction file's
DOI `10.1093/oso/9780198500742.001.0001` — and a paperback reissue ISBN 9780199602247.

---

## Summary of label changes made in this pass

| Record | Before (B report) | After this pass | Route |
|---|---|---|---|
| [P01] | `METADATA_VERIFIED(index)`, pages UNVERIFIED | **unchanged** | 3 queries, no URL |
| [P02] | `METADATA_VERIFIED(index) +ABSTRACT(index)` | confirmed | DOI-bearing APS URL |
| [P02E] | `METADATA_VERIFIED(index, single)` | **existence -> `METADATA_VERIFIED(index)`**; content UNVERIFIED | repeat PRL 63(5) TOC URL |
| [P03] | `METADATA_VERIFIED(index, single)` | unchanged; DOI flagged summariser-only | no URL |
| [P08] | `METADATA_VERIFIED(index) +ABSTRACT(index)` | confirmed; **PMID confirmed by URL**; journal name still unresolved | Wiley DOI URL + PubMed URL |
| [P09] | `METADATA_VERIFIED(index) +ABSTRACT(index)` | confirmed; **page conflict found** | Wiley DOI URL x6 |
| [P12] | `METADATA_VERIFIED(index) +ABSTRACT(index)` | confirmed; **full title recovered** | Wiley DOI URL |
| [P17] | `SECTION_READ` (README citation) | **+ independent OSTI record** | OSTI URL |
| [P18] | `METADATA_VERIFIED(index)`, DOI UNVERIFIED | **unchanged** | no URL |
| [P20] | `METADATA_VERIFIED(index)`, pages UNVERIFIED | **identity -> publisher-URL route**; pages still unresolved, omitted | IUCr paper URL + issue TOC |
| [P21] | `METADATA_VERIFIED(index)` | confirmed via IUCr URLs | IUCr paper URL + issue TOC |
| [P30] | `METADATA_VERIFIED(index) +ABSTRACT(index)` | confirmed; **vol/issue now URL-level; PMID added** | nature.com v453/n7198 URL + PubMed |
| [P31] | `METADATA_VERIFIED(index) +ABSTRACT(index)` | confirmed; **no DOI exists in evidence -> field omitted** | ScienceDirect PII + OSTI |
| [P32] | `METADATA_VERIFIED(index) +ABSTRACT(index)` | **PII added** | ScienceDirect URL |
| Z. L. Wang 1996 | `METADATA_VERIFIED(index)`, chapters UNVERIFIED | **ch. 3 "Dynamical theories of RHEED" recovered** | Cambridge Core chapter URL |
| [PAT01] | `METADATA_VERIFIED(index, single)` | **-> `METADATA_VERIFIED(index)`** (identity only) | 4 patent-office/index URLs |
| [B08] | year 2003 vs 2004 unresolved | **still unresolved, now URL-level on the 2003 side**; ISBNs confirmed | IUCr review + OUP product URLs |
| McCoy & Maksym | not in B report | **`UNVERIFIED`** — 3 queries, year contradictory (1993/1994/1997) | 2 ScienceDirect PIIs + 1 S2 slug |

**Queries run in this pass: 20. Records whose evidence route was strengthened: 12.
Records the pass failed to strengthen: [P01], [P03], [P18], McCoy & Maksym.**

---

## Validation of `references.bib`

Checked with a purpose-written brace-depth parser
(`../validate_bib.py` in the scratchpad), not a regex. Checks performed:
balanced braces globally and per field; unique, legal cite keys; a mandatory
`note` on every entry that starts with `evidence:` and contains `provenance:`;
a `title` on every entry; DOI shape (`10.xxxx/...`); **and a verbatim
cross-check of every DOI against the two source documents**.

```
entries parsed                                     : 96
unique cite keys                                   : 96
brace balance (non-comment text)                   : OK
entries ABOVE the UNVERIFIED delimiter  (VERIFIED) : 78
entries BELOW the UNVERIFIED delimiter (UNVERIFIED): 18
entries carrying a doi field                       : 45
entries with NO doi field (deliberately omitted)   : 51
ERRORS   : none
WARNINGS : none
```

**DOI provenance check (the important one): all 45 DOI strings in the file were
found verbatim in the instruction file or in `B_literature.md`. Zero DOIs were
introduced by this pass, and zero were constructed, guessed or
pattern-completed.** Three DOIs offered by the search summariser in this pass
were deliberately REFUSED and are recorded above as unadmitted leads only:
`10.1143/JJAP.22.176` ([P17]), `10.1107/S0108767388010888` ([P20], which is an
IUCr *paper code*, not an attested DOI) and `10.1107/S0108767389009141` ([P21]).

A second pass escaped 216 LaTeX-hostile characters (`_`, `&`, `%`, `#`, `$`) in
text fields, skipping `url`/`doi`/`eprint` fields and the interiors of `\url{}`,
so the notes can be typeset if a bibliography style prints them.

### Coverage

Every source ID defined in either document has an entry:
`[B01]-[B15]`, `[C01]-[C03]`, `[P01]-[P07]`, `[S01]-[S02]` from the instruction
file, and `[P08]-[P51]`, `[PAT01]`, `[PAT02]` from `B_literature.md`. Two policy
IDs sit in the UNVERIFIED section and are keyed `U04` (= `[P29]`, exact title
never established) and `U03` (= `[PAT02]`); both notes say so explicitly.
Records that neither document gave an ID use obviously non-ID keys
(`ZLWANG96`, `SIMTRHEPD`, `SIMTRHEPD-CPC`, `HANADA95`, `ABTEM`, `RHEEDIUM`,
`PYMULTISLICE`, `BLACKBURN14`, `U01`-`U18`) so they can never be mistaken for a
policy source ID.

### Verified-section count by evidence route

Counted programmatically over the 78 entries above the delimiter; each entry is
counted once, under the strongest route its `evidence:` field names.

| Strongest route | Count | Keys |
|---|---|---|
| `SECTION_READ` | 10 | P04 (instruction file), P17 (secondary citation read in a README), S01, S02, SIMTRHEPD, SIMTRHEPD-CPC, HANADA95, ABTEM, RHEEDIUM, PYMULTISLICE |
| `METADATA_VERIFIED` (instruction-file record, not re-verified) | 15 | B01, B02, B03, B04, B05, B11, B12, B13, B14, B15, C01, C02, C03, P05, P06 |
| `METADATA_VERIFIED(index)` and/or `+ABSTRACT(index)` | 47 | B07, B08, B09, B10, P01, P02, P02E, P07, P08, P09, P10, P11, P12, P13, P14, P15, P16, P18, P19, P20, P21, P22, P23, P26, P27, P28, P30-P43, P45-P47, P49, P51, PAT01, ZLWANG96 |
| `METADATA_VERIFIED(index, single)` -- weakest route above the line | 6 | B06, P03, P24, P25, P44, BLACKBURN14 |

Only ten records in the whole project were ever READ, and eight of those are
GitHub READMEs. `SECTION_READ` on [P17] means the *citation string* was read in
the sim-trhepd-rheed README, NOT the Ichimiya paper.

### What this file still is NOT

No entry here has been resolved against Crossref, a DOI resolver or a publisher
record, because every such host is blocked. `METADATA_VERIFIED(index)` is a
weaker claim than the instruction file's `METADATA_VERIFIED`, and
`+ABSTRACT(index)` is NOT `SECTION_READ`. The closing block of
`references.bib` lists, in order, the eight steps that turn this into a citable
bibliography.
