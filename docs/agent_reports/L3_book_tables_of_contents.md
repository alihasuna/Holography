# L3 - Publisher tables of contents for B01-B15 and chapters C01-C03 (reading plan, step 3)

Prepared: 2026-09-22. Agent: literature agent L3. Network: Full (HTTPS proxy).
Scope: for each book in `docs/references.bib` (B01-B15) and chapters C01-C03, the table of contents of
EXACTLY the edition named in the bib, read from the publisher (or, where the publisher page is blocked
or has no TOC, a second authoritative route that is named). Raw pages were saved outside the
repository in the session scratchpad (`.../scratchpad/tocs/`).

## Label rules applied in this report

- A TOC read on a publisher page (or a publisher-deposited Crossref record) makes the book's CHAPTER
  STRUCTURE (numbers, titles, page ranges as printed there) METADATA_VERIFIED, route = the URL given.
- It does NOT make any chapter CONTENT SECTION_READ. No chapter content is described beyond its
  printed title.
- Chapter titles below are copied exactly as they appear on the page read (capitalisation included);
  page ranges are those printed on the page read. Where the page shows no page range, "n/p" (not
  printed) is written, and no page range is supplied from elsewhere.
- "Fact" = what the page shows. "Inference" = marked explicitly as such.

## Access log (hosts)

| Host | Result | Consequence |
|---|---|---|
| api.crossref.org | 200 | used for chapter DOIs and page ranges |
| link.springer.com | 200 | Springer TOCs read directly |
| www.cambridge.org (Cambridge Core) | 200 | CUP TOCs read directly |
| shop.elsevier.com | 200 | Elsevier shop page tried for TOC |
| www.wiley.com | 200 | Wiley product page tried for TOC |
| academic.oup.com | 403, `cf-mitigated: challenge` (Cloudflare bot challenge of the publisher, not the egress proxy; proxy status shows no relay failure) | not read; not routed around |
| www.sciencedirect.com | 403 (publisher bot protection) | not read |
| onlinelibrary.wiley.com | 403 (publisher bot protection) | not read |
| global.oup.com | curl: HTTP 202 with `x-amzn-waf-action: challenge` (AWS WAF bot challenge); the WebFetch tool did obtain the product page (its output is a model-mediated extraction, not raw HTML) | used for B01 numbering only, flagged |
| media.wiley.com | 200 | Wiley front-matter excerpt PDF (Contents) read |
| link.springer.com/content/pdf/bfm:... | 200 (free front-matter PDFs) | printed "Contents" of every Springer book read; source of printed chapter numbers |

Note on Springer: with a browser-like User-Agent string link.springer.com returned a JavaScript "Client
Challenge" page; with curl's own default User-Agent (no disguise) it returned the normal page. Nothing was
routed around a block of the egress proxy.

Machine-readable output: `docs/agent_reports/L3_book_tocs.tsv`, written by `tools/lit/record_tocs.py`
(run: `python3 tools/lit/record_tocs.py --raw-dir <scratch>/tocs --out docs/agent_reports/L3_book_tocs.tsv
--fetch`; pypdf needed for the front-matter PDFs). One TSV row = what one route shows; empty
`chapter_number` = that route prints no number (explained per book below).

---

## B01 - Spence, High-Resolution Electron Microscopy, 4th ed., OUP 2013

Bib record: `doi 10.1093/acprof:oso/9780199668632.001.0001`, edition 4, OUP, 2013.

Routes read:
1. `https://academic.oup.com/...` - blocked (Cloudflare challenge). Not read.
2. `https://global.oup.com/academic/product/high-resolution-electron-microscopy-9780199668632` - curl blocked
   (AWS WAF); read through WebFetch. Shown: "Fourth Edition", publication date "01 December 2013",
   ISBN 9780199668632, "432 pages". The TOC it returned numbers chapters 1-13 plus "Appendices"; no page
   numbers. CAVEAT: WebFetch output is produced by a summarising model, so the capitalisation and wording
   of these titles are not guaranteed character-exact.
3. Crossref (publisher-deposited records, raw JSON):
   `https://api.crossref.org/works?filter=prefix:10.1093,type:book-chapter&query.container-title=High-Resolution+Electron+Microscopy&query.author=Spence&rows=40`
   and the book record `https://api.crossref.org/works/10.1093/acprof:oso/9780199668632.001.0001`
   (type monograph, ISBN 9780199668632, published-print 2013-09-12). The 13 chapter records with DOIs
   `10.1093/acprof:oso/9780199668632.003.0001` ... `.0013` carry titles and page ranges. The same query also
   returned 3rd-edition records (`...9780199552757.003.00NN`, different pages); these are NOT this edition
   and were discarded.

TOC (number and product-page title from route 2; Crossref title, pages and DOI from route 3; joined by
order - both lists have 13 entries in the same sequence; the join is an inference, not printed anywhere):

| No. (OUP product page) | Title, OUP product page (WebFetch) | Title, Crossref deposit | Pages (Crossref) | Chapter DOI (Crossref) |
|---|---|---|---|---|
| 1 | Preliminaries | Preliminaries | 1-12 | 10.1093/acprof:oso/9780199668632.003.0001 |
| 2 | Electron Optics | Electron optics | 13-45 | ...003.0002 |
| 3 | Wave Optics | Wave optics | 46-66 | ...003.0003 |
| 4 | Coherence and Fourier Optics | Coherence and Fourier optics | 67-87 | ...003.0004 |
| 5 | Imaging Thin Crystals and their Defects | TEM imaging of thin crystals and their defects | 88-153 | ...003.0005 |
| 6 | Imaging Molecules: Radiation Damage | Imaging molecules: radiation damage | 154-203 | ...003.0006 |
| 7 | Image Processing, Super-Resolution, Diffractive Imaging | Image processing, super-resolution, and diffractive imaging | 204-232 | ...003.0007 |
| 8 | STEM and Z-contrast | Scanning transmission electron microscopy and Z-contrast | 233-263 | ...003.0008 |
| 9 | Electron Sources and Detectors | Electron sources and detectors | 264-288 | ...003.0009 |
| 10 | Measurement of Electron-Optical Parameters | Measurement of electron-optical parameters | 289-314 | ...003.0010 |
| 11 | Instabilities and the Microscope Environment | Instabilities and the microscope environment | 315-323 | ...003.0011 |
| 12 | Experimental Methods | Experimental methods | 324-347 | ...003.0012 |
| 13 | Associated Techniques and Software Resources | Associated techniques | 348-387 | ...003.0013 |
| - | Appendices | (no Crossref record returned) | n/p | - |

Reading-plan mapping (`docs/07_reading_plan.md:28`, "chapters on coherent image formation, aberrations,
diffraction"). Mapping is by printed TITLE only; content unread:
- coherent image formation -> ch. 3 "Wave optics" (pp. 46-66) and ch. 4 "Coherence and Fourier optics"
  (pp. 67-87).
- aberrations -> no chapter title contains "aberration". Candidates by title: ch. 2 "Electron optics"
  (pp. 13-45), ch. 10 "Measurement of electron-optical parameters" (pp. 289-314). UNRESOLVED without the
  printed section-level Contents.
- diffraction -> no chapter title contains "diffraction" (only ch. 7 "... diffractive imaging"). Candidate
  by title: ch. 5 (pp. 88-153). UNRESOLVED.
- Label: chapter structure METADATA_VERIFIED (Crossref deposit; product-page numbering via WebFetch).
  Content: not read.

## B02 - De Graef, Introduction to Conventional Transmission Electron Microscopy, CUP 2003

Bib record: `doi 10.1017/CBO9780511615092`, CUP, 2003.

Route read: `https://doi.org/10.1017/CBO9780511615092` resolved to
`https://www.cambridge.org/core/books/introduction-to-conventional-transmission-electron-microscopy/257FBB684B79174B1C6D3ACCC256ECC0`
(Cambridge Core, HTTP 200; one TOC page). Shown: publication dates "02 December 2009" (online) and
"27 March 2003" (print); ISBN 9780511615092 and 9780521629959 in the visible block, plus
`citation_isbn` 9780521620062 in the page metadata; DOI 10.1017/CBO9780511615092; "742 Pages";
`citation_publication_date` 2003/03. No edition statement (first edition). Chapter number is printed as
"N - Title"; pages as "pp a-b".

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Frontmatter | i-vi |
| - | Contents | vii-xiii |
| - | Preface | xiv-xviii |
| - | Acknowledgements | xix-xx |
| - | Figure reproductions | xxi-xxii |
| 1 | Basic crystallography | 1-78 |
| 2 | Basic quantum mechanics, Bragg's Law and other tools | 79-135 |
| 3 | The transmission electron microscope | 136-234 |
| 4 | Getting started | 235-302 |
| 5 | Dynamical electron scattering in perfect crystals | 303-344 |
| 6 | Two-beam theory in defect-free crystals | 345-394 |
| 7 | Systematic row and zone axis orientations | 395-459 |
| 8 | Defects in crystals | 460-517 |
| 9 | Electron diffraction patterns | 518-584 |
| 10 | Phase contrast microscopy | 585-660 |
| - | Appendix A1 - Explicit crystallographic equations | 661-664 |
| - | Appendix A2 - Physical constants | 665-665 |
| - | Appendix A3 - Space group encoding and other software | 666-666 |
| - | Appendix A4 - Point groups and space groups | 667-676 |
| - | List of symbols | 677-684 |
| - | Bibliography | 685-704 |
| - | Index | 705-718 |

Reading-plan mapping (`docs/07_reading_plan.md:29`, "crystallography and reciprocal-space chapters;
structure-factor section"):
- crystallography -> ch. 1 "Basic crystallography", pp. 1-78.
- reciprocal space -> no chapter title names reciprocal space; by title it is most likely inside ch. 1
  (inference). Cambridge Core lists chapters only, so section titles and the location of the
  "structure-factor section" are UNRESOLVED; the printed "Contents" (pp. vii-xiii) is behind the paywall.
- Also relevant by title for the dynamical-diffraction audit: ch. 5 "Dynamical electron scattering in
  perfect crystals" (pp. 303-344), ch. 7 "Systematic row and zone axis orientations" (pp. 395-459),
  Appendix A1 "Explicit crystallographic equations" (pp. 661-664).
- Label: chapter structure METADATA_VERIFIED (Cambridge Core TOC). Content: not read.

## B03 - Hawkes and Kasper, Principles of Electron Optics, Vol. 3: Fundamental Wave Optics, 2nd ed., 2022

Bib record: ISBN 9780128189795, Academic Press, 2022, edition 2.

Routes read:
1. `https://shop.elsevier.com/books/principles-of-electron-optics-volume-3/hawkes/978-0-12-818979-5`
   (HTTP 200). Shown: "2nd Edition - February 18, 2022"; "Edition: 2"; "Published: February 18, 2022";
   ISBNs in the page 978-0-12-818979-5 and 978-0-12-818980-1; 558 pages (`numberOfPages` in the page
   data). Its "Table of contents" gives chapter numbers and titles, no pages.
2. Crossref records filtered by the print ISBN,
   `https://api.crossref.org/works?filter=isbn:9780128189795&rows=200` (24 records deposited by Elsevier:
   15 chapters, front matter, "Notes and References", "Index", and the book record
   `10.1016/c2018-0-04650-2`). Titles and page ranges; no chapter numbers.
3. `https://www.sciencedirect.com/book/9780128189795/...` - 403 (publisher bot protection); not read.

Shop-page TOC (route 1, exactly as printed; part headings in brackets):

| No. | Title as printed on the route | Pages |
|---|---|---|
| 54 | Introduction | n/p |
| 55 | The Schrödinger Equation  [part: Part XI – Wave Mechanics] | n/p |
| 56 | The Relativistic Wave Equation  [part: Part XI – Wave Mechanics] | n/p |
| 57 | The Eikonal Approximation  [part: Part XI – Wave Mechanics] | n/p |
| 58 | Paraxial Wave Optics  [part: Part XI – Wave Mechanics] | n/p |
| 59 | The General Theory of Electron Diffraction and Interference  [part: Part XI – Wave Mechanics] | n/p |
| 60 | Elementary Diffraction Patterns  [part: Part XI – Wave Mechanics] | n/p |
| 61 | General Introduction  [part: Part XII, Electron Interference and Electron Holography] | n/p |
| 62 | Interferometry  [part: Part XII, Electron Interference and Electron Holography] | n/p |
| 63 | Holography  [part: Part XII, Electron Interference and Electron Holography] | n/p |
| 64 | General Introduction  [part: Part XIII, Theory of Image Formation] | n/p |
| 65 | Fundamentals of Transfer Theory  [part: Part XIII, Theory of Image Formation] | n/p |
| 66 | The Theory of Bright-field Imaging.  [part: Part XIII, Theory of Image Formation] | n/p |
| 67 | Image Formation in the Scanning Transmission Electron Microscope  [part: Part XIII, Theory of Image Formation] | n/p |
| 68 | Statistical Parameter Estimation Theory  [part: Part XIII, Theory of Image Formation] | n/p |
| 69 | Electron Interactions in Thin Specimens  [part: Part XIV – Electron–specimen Interactions] | n/p |
| 70 | Introduction  [part: Part XV – Digital Image Processing] | n/p |
| 71 | Acquisition, Sampling and Coding  [part: Part XV – Digital Image Processing] | n/p |
| 72 | Enhancement  [part: Part XV – Digital Image Processing] | n/p |
| 73 | Linear Restoration  [part: Part XV – Digital Image Processing] | n/p |
| 74 | Nonlinear Restoration – the Phase Problem  [part: Part XV – Digital Image Processing] | n/p |
| 75 | Three-dimensional Reconstruction  [part: Part XV – Digital Image Processing] | n/p |
| 76 | Image Analysis  [part: Part XV – Digital Image Processing] | n/p |
| 77 | Microscope Parameter Measurement and Instrument Control  [part: Part XV – Digital Image Processing] | n/p |
| 78 | Coherence and the Brightness Functions  [part: Part XVI – Coherence, Brightness and Spectral Functions] | n/p |
| 79 | Wigner Optics  [part: Part XVI – Coherence, Brightness and Spectral Functions] | n/p |
| 80 | Orbital Angular Momentum, Vortex Beams and the Quantum Electron Microscope  [part: PART XVII – Vortex Studies, the Quantum Electron Microscope] | n/p |

Crossref deposit for ISBN 9780128189795 (route 2, exactly as deposited):

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Preface to the Second Edition | xiii-xv |
| - | Contents | vii-xii |
| - | Preface to the First Edition | xvii-xviii |
| - | Dedication | v |
| - | Title page | i-iii |
| - | Copyright | iv |
| - | Introduction | 1457-1472 |
| - | The Schrödinger Equation | 1475-1480 |
| - | The Relativistic Wave Equation | 1481-1493 |
| - | The Eikonal Approximation | 1495-1504 |
| - | Paraxial Wave Optics | 1505-1520 |
| - | The General Theory of Electron Diffraction and Interference | 1521-1540 |
| - | Elementary Diffraction Patterns | 1541-1565 |
| - | General Introduction | 1569-1580 |
| - | Interferometry | 1581-1621 |
| - | Holography | 1623-1681 |
| - | General Introduction | 1685-1690 |
| - | Fundamentals of Transfer Theory | 1691-1705 |
| - | Image Formation in the Conventional Transmission Electron Microscope | 1707-1796 |
| - | Image Formation in the Scanning Transmission Electron Microscope | 1797-1851 |
| - | Statistical Parameter Estimation Theory | 1853-1867 |
| - | Notes and References | 1869-1988 |
| - | Index | 1989-1998 |

Facts and one inference:
- FACT: the Vol. 3 shop page lists chapters 54-80, but the Crossref deposit for the Vol. 3 ISBN contains
  only the 15 chapters titled as shop-page ch. 54-68 (pp. 1457-1867), then "Notes and References"
  (pp. 1869-1988) and "Index" (pp. 1989-1998). Chapters titled as 69-80 are deposited under the Vol. 4
  ISBN (see B04), pp. 1999-2476.
- INFERENCE: Vol. 3 = chapters 54-68 (Parts XI-XIII); the Vol. 3 shop page prints the TOC of Vols. 3 and 4
  together.
- FACT: title conflict for ch. 66 - shop page "The Theory of Bright-field Imaging."; Crossref
  "Image Formation in the Conventional Transmission Electron Microscope" (pp. 1707-1796). Resolve from the
  printed Contents (pp. vii-xii, Crossref DOI 10.1016/b978-0-12-818979-5.00083-8) if uploaded.

"Check chapter numbering in this edition" (`docs/07_reading_plan.md:30`): DONE. Chapter numbering is
continuous across the four-volume second edition: Vol. 3 opens with ch. 54 "Introduction" and runs to
ch. 68; page numbers are also continuous (Vol. 3 starts at p. 1457). Any locator must therefore be of the
form "ch. 58, pp. 1505-1520", never "ch. 5".

Reading-plan mapping (`docs/07_reading_plan.md:30`, "wave mechanics, propagation approximations,
interference and holography, coherence chapters"):
- wave mechanics -> Part XI "Wave Mechanics", ch. 55-60, pp. 1475-1565.
- propagation approximations -> by title ch. 57 "The Eikonal Approximation" (pp. 1495-1504) and ch. 58
  "Paraxial Wave Optics" (pp. 1505-1520).
- interference and holography -> Part XII, ch. 61 "General Introduction" (pp. 1569-1580), ch. 62
  "Interferometry" (pp. 1581-1621), ch. 63 "Holography" (pp. 1623-1681).
- coherence -> NOT IN VOL. 3. Ch. 78 "Coherence and the Brightness Functions" (pp. 2323-2369) and ch. 79
  "Wigner Optics" (pp. 2371-2392) are in Vol. 4 (B04) per the Crossref deposit and the B04 shop page.
- Label: chapter structure METADATA_VERIFIED (Elsevier shop TOC + Elsevier Crossref deposit). Content: not
  read.

## B04 - Hawkes and Kasper, Principles of Electron Optics, Vol. 4: Advanced Wave Optics, 2nd ed., 2022

Bib record: ISBN 9780323916462, Academic Press, 2022, edition 2.

Routes read:
1. `https://shop.elsevier.com/books/principles-of-electron-optics-volume-4/hawkes/978-0-323-91646-2`
   (HTTP 200). Shown: "2nd Edition - May 10, 2022"; "Edition: 2"; "Published: May 10, 2022"; ISBNs in the
   page 978-0-323-91646-2 and 978-0-323-91647-9; 664 pages (`numberOfPages`). TOC: numbers and titles, no
   pages.
2. `https://api.crossref.org/works?filter=isbn:9780323916462&rows=200` (22 records; book record
   `10.1016/c2021-0-01238-4`, published 2022). Titles and pages; no numbers.

Shop-page TOC (route 1):

| No. | Title as printed on the route | Pages |
|---|---|---|
| 69 | Electron Interactions in Thin Specimens  [part: Part XIV Electron–specimen Interactions] | n/p |
| 70 | Introduction  [part: Part XV Digital Image Processing] | n/p |
| 71 | Acquisition, Sampling and Coding  [part: Part XV Digital Image Processing] | n/p |
| 72 | Enhancement  [part: Part XV Digital Image Processing] | n/p |
| 73 | Linear Restoration  [part: Part XV Digital Image Processing] | n/p |
| 74 | Nonlinear Restoration – the Phase Problem  [part: Part XV Digital Image Processing] | n/p |
| 75 | Three-dimensional Reconstruction  [part: Part XV Digital Image Processing] | n/p |
| 76 | Image Analysis  [part: Part XV Digital Image Processing] | n/p |
| 77 | Instrument Control and Instrumental Image Manipulation  [part: Part XV Digital Image Processing] | n/p |
| 78 | Coherence and the Brightness Functions  [part: Part XVI Coherence, Brightness and Spectral Functions] | n/p |
| 79 | Wigner Optics  [part: Part XVI Coherence, Brightness and Spectral Functions] | n/p |
| 80 | Orbital Angular Momentum, Vortex Beams and the Quantum Electron Microscope  [part: Part XVII Vortex Studies, the Quantum Electron Microscope] | n/p |

Crossref deposit (route 2):

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Dedication | v |
| - | Copyright | iv |
| - | Preface to the First Edition | xix-xx |
| - | Contents | vii-xiii |
| - | Preface to the Second Edition | xv-xviii |
| - | Title page | i-iii |
| - | Electron–Specimen Interactions | 1999-2083 |
| - | Introduction | 2087-2099 |
| - | Acquisition, Sampling and Coding | 2101-2117 |
| - | Enhancement | 2119-2150 |
| - | Linear Restoration | 2151-2168 |
| - | Nonlinear Restoration – The Phase Problem | 2169-2219 |
| - | Three-Dimensional Reconstruction | 2221-2274 |
| - | Image Analysis | 2275-2294 |
| - | Microscope Parameter Measurement and Instrument Control | 2295-2320 |
| - | Coherence and the Brightness Functions | 2323-2369 |
| - | Wigner Optics | 2371-2392 |
| - | Orbital Angular Momentum, Vortex Beams and the Quantum Electron Microscope | 2395-2476 |
| - | Corrections and additions to volumes 1, 2 and 3 | 2479-2487 |
| - | Notes and References | 2489-2631 |
| - | Index | 2633-2647 |

Facts:
- Title conflicts between the two Elsevier routes: ch. 69 shop "Electron Interactions in Thin Specimens" vs
  Crossref "Electron–Specimen Interactions" (pp. 1999-2083); ch. 77 shop (Vol. 4 page) "Instrument Control
  and Instrumental Image Manipulation" vs Crossref and the Vol. 3 shop page "Microscope Parameter
  Measurement and Instrument Control" (pp. 2295-2320). The printed Contents (pp. vii-xiii, Crossref DOI
  10.1016/b978-0-323-91646-2.00083-9) would settle them.
- Vol. 4 also contains "Corrections and additions to volumes 1, 2 and 3" (pp. 2479-2487).

Reading-plan mapping (`docs/07_reading_plan.md:31`, "image formation, phase problems, reconstruction,
sampling"):
- image formation -> NOT IN VOL. 4. It is Vol. 3 (B03) Part XIII, ch. 64-68 (pp. 1685-1867): ch. 65
  "Fundamentals of Transfer Theory" (pp. 1691-1705), ch. 66 (pp. 1707-1796; title conflict above), ch. 67
  "Image Formation in the Scanning Transmission Electron Microscope" (pp. 1797-1851).
- phase problems -> ch. 74 "Nonlinear Restoration – the Phase Problem" (shop) / "Nonlinear Restoration –
  The Phase Problem" (Crossref), pp. 2169-2219; also ch. 73 "Linear Restoration", pp. 2151-2168.
- reconstruction -> ch. 75 "Three-dimensional Reconstruction", pp. 2221-2274 (by title this is 3D
  reconstruction, not hologram reconstruction; hologram reconstruction is by title in B03 ch. 63).
- sampling -> ch. 71 "Acquisition, Sampling and Coding", pp. 2101-2117.
- plus the coherence chapters the plan puts under B03: ch. 78 (pp. 2323-2369), ch. 79 (pp. 2371-2392).
- Label: chapter structure METADATA_VERIFIED. Content: not read.

## Springer books: common route (B05, B06, B09, B10, B12, B13, B14, B15)

For every Springer book two publisher routes were read:
(a) the book page `https://link.springer.com/book/10.1007/<isbn>` (all `?page=N` TOC pages): chapter
titles, authors, page ranges, chapter-DOI links, and the "Bibliographic Information" block (edition
number, copyright, ISBNs with dates);
(b) the free front-matter PDF linked on that page (`https://link.springer.com/content/pdf/bfm:<isbn>/1`),
whose printed "Contents" gives the chapter NUMBERS (the HTML TOC prints none). Numbers were joined to the
HTML entries by title (script `match_contents`, first 30 characters, case/spacing ignored) and checked by
eye. Where the printed Contents gives a first page different from the HTML range, both are recorded.

## B05 - Rose, Geometrical Charged-Particle Optics, 2nd ed., Springer 2012/2013

Bib record: `doi 10.1007/978-3-642-32119-1`, edition 2, year 2013 (bib note: copyright 2012).

Routes: `https://link.springer.com/book/10.1007/978-3-642-32119-1` (1 TOC page) and
`https://link.springer.com/content/pdf/bfm:978-3-642-32119-1/1` (18 pp.). Bibliographic block: "Edition
number : 2"; "Copyright information : Springer-Verlag Berlin Heidelberg 2012"; Hardcover ISBN
978-3-642-32118-4 "Published: 03 February 2013"; Softcover ISBN 978-3-642-42787-9 (07 March 2015); eBook
ISBN 978-3-642-32119-1 "Published: 02 February 2013". This confirms the bib's 2012-copyright / 2013
publication flag.

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Front Matter | i-xviii |
| 1 | Introduction | 1-3 |
| 2 | General Properties of the Electron | 5-43 |
| 3 | Multipole Expansion of the Stationary Electromagnetic Field | 45-88 |
| 4 | Gaussian Optics | 89-188 |
| 5 | General Principles of Particle Motion | 189-222 |
| 6 | Beam Properties | 223-249 |
| 7 | Path Deviations | 251-280 |
| 8 | Aberrations | 281-332 |
| 9 | Correction of Aberrations | 333-385 |
| 10 | Electron Mirrors | 387-412 |
| 11 | Optics of Electron Guns | 413-423 |
| 12 | Confinement of Charged Particles | 425-428 |
| 13 | Monochromators and Imaging Energy Filters | 429-442 |
| 14 | Relativistic Electron Motion and Spin Precession | 443-476 |
| 15 | Electron Self-Action | 477-487 |
| - | Back Matter | 489-507 |

Reading-plan mapping (`docs/07_reading_plan.md:32`, "aberration theory sections as needed"): by title
ch. 7 "Path Deviations" (pp. 251-280), ch. 8 "Aberrations" (pp. 281-332), ch. 9 "Correction of
Aberrations" (pp. 333-385). Section-level locators: to be chosen from the printed Contents in the
front-matter PDF when a specific transfer parameter is needed. No chapter title mentions a biprism
(consistent with the plan's "cannot supply biprism data"). Label: structure METADATA_VERIFIED.

## B06 - Kirkland, Advanced Computing in Electron Microscopy, 3rd ed., Springer 2020

Bib record: `doi 10.1007/978-3-030-33260-0`, edition 3, 2020. The bib note "UNRESOLVED: the table of
contents was never obtained" is now resolved.

Routes: `https://link.springer.com/book/10.1007/978-3-030-33260-0` (1 TOC page) and
`https://link.springer.com/content/pdf/bfm:978-3-030-33260-0/1` (10 pp.). Bibliographic block: "Edition
number : 3"; "Copyright information : Springer Nature Switzerland AG 2020"; Hardcover 978-3-030-33259-4
(10 March 2020); Softcover 978-3-030-33262-4 (10 March 2021); eBook 978-3-030-33260-0 (09 March 2020). The
chapter page `https://link.springer.com/chapter/10.1007/978-3-030-33260-0_5` carries
`citation_firstpage` 99 and `citation_lastpage` 141, consistent with the TOC.

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Front Matter | i-xii |
| 1 | Introduction | 1-7 |
| 2 | The Transmission Electron Microscope | 9-36 |
| 3 | Some Image Approximations | 37-80 |
| 4 | Sampling and the Fast Fourier Transform | 81-98 |
| 5 | Calculation of Images of Thin Specimens | 99-141 |
| 6 | Theory of Calculation of Images of Thick Specimens | 143-195 |
| 7 | Multislice Applications and Examples | 197-239 |
| 8 | The Programs | 241-272 |
| - | Back Matter | 273-354 |
| A | Appendix A: Plotting Transfer Functions | starts p. 273 (front-matter Contents; inside Back Matter online) |
| B | Appendix B: The Fourier Projection Theorem | starts p. 281 (front-matter Contents; inside Back Matter online) |
| C | Appendix C: Atomic Potentials and Scattering Factors | starts p. 283 (front-matter Contents; inside Back Matter online) |
| D | Appendix D: The Inverse Problem | starts p. 303 (front-matter Contents; inside Back Matter online) |
| E | Appendix E: Bilinear Interpolation | starts p. 307 (front-matter Contents; inside Back Matter online) |
| F | Appendix F: 3D Perspective View | starts p. 311 (front-matter Contents; inside Back Matter online) |

Section titles printed in the front-matter Contents that the plan's items point to (titles and first pages
only; content unread):
- 4.1 "Sampling" (p. 81); 4.4 "Wrap Around Error and Rearrangement" (p. 90).
- 5.2 "Single Atom Properties" (p. 102) with 5.2.2 "Potential" (p. 103) and 5.2.4 "Scattering Factors"
  (p. 108); 5.3 "Total Specimen Potential" (p. 111); 5.7 "Summary of Sampling Suggestions" (p. 138).
- 6.2 "The Wave Equation for Fast Electrons" (p. 156); 6.4 "The Multislice Solution" (p. 162); 6.4.3 "Free
  Space Propagation" (p. 167); 6.7 "Slicing the Specimen" (p. 171); 6.8 "Aliasing and Bandwidth" (p. 175);
  6.10.1 "The Propagator Function and Specimen Tilt" (p. 181).
- Appendix C "Atomic Potentials and Scattering Factors" (p. 283).
(Some words in the PDF text layer carry spurious spaces, e.g. "Dif fraction"; they were read through.)

Reading-plan mapping (`docs/07_reading_plan.md:33`):
- "Sampling and the FFT" -> ch. 4 "Sampling and the Fast Fourier Transform", pp. 81-98. Confirmed.
- "Theory of calculation of images of thick specimens" -> ch. 6 "Theory of Calculation of Images of Thick
  Specimens", pp. 143-195. Confirmed.
- "Multislice applications" -> ch. 7 "Multislice Applications and Examples", pp. 197-239 (plan title
  truncated).
- propagator form (SM08) -> by section title 6.4.3 (p. 167) and 6.10.1 (p. 181) in ch. 6.
- 2/3 anti-aliasing rule (SM15) -> by section title 6.8 "Aliasing and Bandwidth" (p. 175); also 5.7
  (p. 138). Whether the 2/3 rule is stated there is NOT known until read.
- atomic potential parameterisation (SM17) -> ch. 5 section 5.2 (pp. 102 ff.) and Appendix C (p. 283,
  inside the online "Back Matter" pp. 273-354). The plan does not list ch. 5 or Appendix C; they are
  needed for SM17.
- slice thickness -> by section title 6.7 "Slicing the Specimen" (p. 171).
- Label: structure METADATA_VERIFIED (Springer TOC + front-matter Contents). Content: not read.

## B07 - Ichimiya and Cohen, Reflection High-Energy Electron Diffraction, CUP 2004

Bib record: CUP, 2004, URL of Cambridge Core book page; no DOI field.

Route read: `https://www.cambridge.org/core/books/reflection-highenergy-electron-diffraction/162FE7186C89C6A8269619B7EDF5F1E8`
(HTTP 200; TOC pages `?pageNum=1` and `?pageNum=2`). Shown: publication dates "06 July 2010" (online) and
"13 December 2004" (print); ISBN 9780511735097, 9780521453738, 9780521184021; DOI
`https://doi.org/10.1017/CBO9780511735097`; "366 Pages". Crossref
`https://api.crossref.org/works/10.1017/CBO9780511735097`: type monograph, same title, authors Ayahiko
Ichimiya and Philip I. Cohen, published-print 2004-12-13, published-online 2010-07-06, same three ISBNs.
(Fact for the bibliography keeper: the book has a DOI, 10.1017/CBO9780511735097, now Crossref-confirmed;
the bib entry has none.)

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Frontmatter | i-vi |
| - | Contents | vii-x |
| - | Preface | xi-xii |
| 1 | Introduction | 1-2 |
| 2 | Historical survey | 3-11 |
| 3 | Instrumentation | 12-18 |
| 4 | Wave properties of electrons | 19-27 |
| 5 | The diffraction conditions | 28-42 |
| 6 | Geometrical features of the pattern | 43-61 |
| 7 | Kikuchi and resonance patterns | 62-76 |
| 8 | Real diffraction patterns | 77-112 |
| 9 | Electron scattering by atoms | 113-129 |
| 10 | Kinematic electron diffraction | 130-153 |
| 11 | Fourier components of the crystal potential | 154-160 |
| 12 | Dynamical theory – transfer matrix method | 161-172 |
| 13 | Dynamical theory – embedded R-matrix method | 173-191 |
| 14 | Dynamical theory – integral method | 192-194 |
| 15 | Structural analysis of crystal surfaces | 195-210 |
| 16 | Inelastic scattering in a crystal | 211-233 |
| 17 | Weakly disordered surfaces | 234-259 |
| 18 | Strongly disordered surfaces | 260-269 |
| 19 | RHEED intensity oscillations | 270-313 |
| - | Appendix A: Fourier representations | 314-317 |
| - | Appendix B: Green's functions | 318-319 |
| - | Appendix C: Kirchhoff's diffraction theory | 320-322 |
| - | Appendix D: A simple eigenvalue problem | 323-325 |
| - | Appendix E: Waller and Hartree equation | 326-327 |
| - | Appendix F: Optimization of dynamical calculation | 328-332 |
| - | Appendix G: Scattering factor | 333-334 |
| - | References | 335-349 |
| - | Index | 350-353 |

Reading-plan mapping (`docs/07_reading_plan.md:34`):
- "The diffraction conditions" -> ch. 5, pp. 28-42. Confirmed.
- "Dynamical theory: transfer matrix" -> ch. 12 "Dynamical theory – transfer matrix method", pp. 161-172.
- "embedded R-matrix" -> ch. 13 "Dynamical theory – embedded R-matrix method", pp. 173-191.
- "integral methods" -> ch. 14 "Dynamical theory – integral method" (singular), pp. 192-194 (confirms
  the bib note "ch. 14").
- "Kikuchi and resonance patterns" -> ch. 7, pp. 62-76. Confirmed.
- Not in the plan but relevant by title to the same items: ch. 11 "Fourier components of the crystal
  potential" (pp. 154-160), ch. 16 "Inelastic scattering in a crystal" (pp. 211-233), Appendix F
  "Optimization of dynamical calculation" (pp. 328-332), Appendix G "Scattering factor" (pp. 333-334).
- "refraction and critical angle as printed (SM04)": no chapter title names refraction; which chapter
  holds it is UNRESOLVED (candidates by title: ch. 4 "Wave properties of electrons", ch. 5).
- Label: structure METADATA_VERIFIED (Cambridge Core TOC; book DOI via Crossref). Content: not read.

## B08 - Peng, Dudarev and Whelan, High-Energy Electron Diffraction and Microscopy, OUP 2004

Bib record: `doi 10.1093/oso/9780198500742.001.0001`, OUP, 2004 (bib flags a 2003/2004 year conflict).

Routes:
1. `https://academic.oup.com/book/54675` - Cloudflare challenge (403); WebFetch also returned no TOC. Not
   read.
2. `https://global.oup.com/academic/product/high-energy-electron-diffraction-and-microscopy-9780198500742`
   via WebFetch (curl: AWS WAF challenge): shows "Publication Date: 11 March 2004", ISBN 9780198500742,
   "558 Pages"; NO table of contents on that page. (Model-mediated extraction.)
3. Crossref: `https://api.crossref.org/works/10.1093/oso/9780198500742.001.0001` (type book; title "High-Energy
   Electron Diffraction And Microscopy"; ISBN print 9780198500742, electronic 9781383019926;
   published-print 2004-01-08) and `https://api.crossref.org/works?filter=isbn:9780198500742&rows=100`
   (23 records deposited by OUP: book, 4 front-matter items, 14 chapters `...003.0001`-`...003.0014`,
   4 appendices `...005.0001`-`...005.0004`). Titles below are exactly as deposited (OUP's deposit
   title-cases them, e.g. "Iii", "crystal").

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Title Page | i-iv |
| - | Preface | xi-xiii |
| - | Foreword By Sir Peter Hirsch Frs | vii-ix |
| - | Dedication | v-vi |
| - | Basic Concepts Of High-Energy Electron Diffraction | 1-23 |
| - | Kinematic Theory | 24-53 |
| - | Dynamical Theory I. General Theory | 54-74 |
| - | Dynamical Theory Ii. Transmission High-Energy Electron Diffraction | 75-116 |
| - | Dynamical Theory Iii. Reflection High-Energy Electron Diffraction | 117-185 |
| - | Resonance Effects In Transmission And Reflection High-Energy Electron Diffraction | 186-227 |
| - | Diffuse And Inelastic Scattering – Elementary Processes | 228-263 |
| - | Diffuse And Inelastic Scattering – Multiple Scattering Effects | 264-310 |
| - | crystal And Diffraction Symmetry | 311-349 |
| - | Perturbation Methods And Tensor Theory | 350-387 |
| - | Digital Electron Micrograph Recording And Basic Processing | 388-405 |
| - | Image Formation And The Retrieval Of The Electron Wave Function | 406-426 |
| - | The Atomic Scattering Factor And The Optical Potential | 427-453 |
| - | Temperature-Dependent Debye–Waller Factors | 454-469 |
| - | Appendix A | 470-472 |
| - | Appendix B | 473-476 |
| - | Appendix C | 477-489 |
| - | Appendix D | 490-500 |

Chapter numbers: NO page read prints them. INFERENCE: chapter n = the n-th chapter record in page order
(= DOI suffix `.003.000n`); this gives ch. 1-14 as listed. Appendix TITLES are not deposited (only
"Appendix A" ... "Appendix D", pp. 470-500).

Year conflict (bib note): facts now on record - Crossref published-print 2004-01-08; OUP product page
(WebFetch) 11 March 2004. Both are 2004. The IUCr review page cited in the bib note (2003) was not
re-read in this pass. The front-matter copyright line would settle it.

Reading-plan mapping (`docs/07_reading_plan.md:35`):
- "ch. 5 Dynamical theory III: RHEED" -> 5th chapter record, "Dynamical Theory Iii. Reflection High-Energy
  Electron Diffraction", pp. 117-185, DOI 10.1093/oso/9780198500742.003.0005. Number 5 is inferred, not
  printed; title confirmed (plan abbreviates).
- "ch. 6 Resonance effects" -> "Resonance Effects In Transmission And Reflection High-Energy Electron
  Diffraction", pp. 186-227, `...003.0006`.
- "ch. 13 atomic scattering factor and optical potential" -> "The Atomic Scattering Factor And The Optical
  Potential", pp. 427-453, `...003.0013`.
- "RHEED routine appendix" -> UNRESOLVED: four appendices exist (A pp. 470-472, B 473-476, C 477-489,
  D 490-500) but their titles are not on any readable route. Ask Ali for the printed Contents pages (or
  scan of pp. 470-500) to identify it.
- By title also relevant to the absorptive potential (input item 21): "Diffuse And Inelastic Scattering –
  Elementary Processes" (pp. 228-263, `.0007`) and "... – Multiple Scattering Effects" (pp. 264-310,
  `.0008`); "Temperature-Dependent Debye–Waller Factors" (pp. 454-469, `.0014`).
- Label: chapter structure METADATA_VERIFIED (OUP Crossref deposit); chapter numbers inferred. Content:
  not read.

## B09 and C01 - Völkl, Allard and Joy (eds.), Introduction to Electron Holography, 1999

Bib record: `doi 10.1007/978-1-4615-4817-1`, Springer/Plenum, 1999; editors given as "Völkl, Ernst".

Routes: `https://link.springer.com/book/10.1007/978-1-4615-4817-1` (1 TOC page) and
`https://link.springer.com/content/pdf/bfm:978-1-4615-4817-1/1` (14 pp., scanned; text layer is OCR, so
the printed Contents gives chapter numbers and titles reliably but its page column is detached from the
titles). Bibliographic block: "Authors : Edgar Völkl, Lawrence F. Allard, David C. Joy" (Springer labels
the editors "Authors"); "Edition number : 1"; "Copyright information : Springer Science+Business Media
New York 1999"; Hardcover ISBN 978-0-306-44920-8 "Published: 30 April 1999"; Softcover 978-1-4613-7183-0
(23 October 2012); eBook 978-1-4615-4817-1 (11 November 2013). Crossref book record
`https://api.crossref.org/works/10.1007/978-1-4615-4817-1`: editors-as-authors "Edgar Völkl", "Lawrence F.
Allard", "David C. Joy", published 1999. The front-matter CIP block (OCR) reads "Edgar V61kl" [sic, OCR].

| No. (printed Contents) | Title (Springer TOC) | Authors (Springer TOC) | Pages | Chapter DOI (link on page) |
|---|---|---|---|---|
| - | Front Matter |  | i-xviii | - |
| 1 | The History of the Electron Biprism | G. Möllenstedt | 1-15 | 10.1007/978-1-4615-4817-1_1 |
| 2 | Principles and Theory of Electron Holography | J. M. Cowley, J. C. H. Spence | 17-56 | 10.1007/978-1-4615-4817-1_2 |
| 3 | Optical Characteristics of an Holography Electron Microscope | L. F. Allard, E. Völkl | 57-86 | 10.1007/978-1-4615-4817-1_3 |
| 4 | Practical Electron Holography | David J. Smith, M. R. McCartney | 87-106 | 10.1007/978-1-4615-4817-1_4 |
| 5 | Quantitative Electron Holography | D. J. Smith, W. J. de Ruijter, J. K. Weiss, M. R. McCartney | 107-124 | 10.1007/978-1-4615-4817-1_5 |
| 6 | The Reconstruction of Off-Axis Electron Holograms | E. Völkl, M. Lehmann | 125-151 | 10.1007/978-1-4615-4817-1_6 |
| 7 | Electron Holography of Electromagnetic Fields | J. E. Bonevich, G. Pozzi, A. Tonomura | 153-181 | 10.1007/978-1-4615-4817-1_7 |
| 8 | On Recording, Processing and Interpretation of Low Magnification Electron Holograms | B. G. Frost, G. Matteucci | 183-200 | 10.1007/978-1-4615-4817-1_8 |
| 9 | High Resolution Off-Axis Electron Holography | W. D. Rau, H. Lichte | 201-229 | 10.1007/978-1-4615-4817-1_9 |
| 10 | Off-Axis Stem Holography | M. A. Gribelyuk, J. Sum | 231-248 | 10.1007/978-1-4615-4817-1_10 |
| 11 | Focus Variation Electron Holography | Dirk Van Dyck, Marc Op de Beeck | 249-266 | 10.1007/978-1-4615-4817-1_11 |
| 12 | Applications of Electron Holography | M. Gajdardziska-Josifovska, A. H. Carim | 267-293 | 10.1007/978-1-4615-4817-1_12 |
| 13 | Electron Holography Using Diffracted Electron Beams (DBH) | R. A. Herring, G. Pozzi | 295-310 | 10.1007/978-1-4615-4817-1_13 |
| 14 | Electron Holography at Low Energy | J. C. H. Spence, J. M. Cowley | 311-331 | 10.1007/978-1-4615-4817-1_14 |
| 15 | A Plus or Minus Sign in the Fourier Transform? | F. Lenz, J. M. Cowley | 333-338 | 10.1007/978-1-4615-4817-1_15 |
| - | Back Matter |  | 339-354 | - |

C01 (Crossref `https://api.crossref.org/works/10.1007/978-1-4615-4817-1_6`, fetched): type book-chapter;
title "The Reconstruction of Off-Axis Electron Holograms"; authors "E. Völkl", "M. Lehmann"; page
"125-151"; container "Introduction to Electron Holography"; published 1999; publisher "Springer US".
=> C01 = ch. 6, pp. 125-151, DOI 10.1007/978-1-4615-4817-1_6: bib record CONFIRMED (title, authors' initials
and surnames, pages, DOI). Section titles printed in the Contents for ch. 6 (OCR): 1 Introduction;
2 Basic reconstruction process; 3 Minimizing the effects of sampling [OCR text: "'\!Iinimizing"];
4 Lens aberrations: Distortions; 5 The reconstruction process using a reference hologram [OCR:
"reconstruct.ion"]; 6 Other reconstruction methods; 7 Methods for lower carrier frequencies; 8 Display of
phase information. (Their page numbers are in a detached OCR column; not assigned here.)

Chapter 13 (resolves bib key U07): Springer TOC and Crossref
`https://api.crossref.org/works/10.1007/978-1-4615-4817-1_13` agree: "Electron Holography Using Diffracted
Electron Beams (DBH)", authors "R. A. Herring", "G. Pozzi", pp. 295-310, DOI 10.1007/978-1-4615-4817-1_13
(DOI taken from the chapter link on the Springer page and confirmed by Crossref; not constructed).
Printed section titles of ch. 13 (OCR): 1 Introduction (295); 2 Basic theoretical considerations (295);
3 Analysis of the interference phenomena (298); 4 Influence of coherence (300); 5 The holography mode (301);
6 Experimental method (303); 7 Spherical aberration (304); 8 Material science applications (305);
9 "Interesting peropectives" [sic, OCR]; 10 Conclusions; 11 Appendix.

Chapter 15: Crossref `https://api.crossref.org/works/10.1007/978-1-4615-4817-1_15`: "A Plus or Minus Sign
in the Fourier Transform?", F. Lenz, J. M. Cowley, pp. 333-338.

Section titles that bear on this project (printed Contents, OCR; titles only, content unread):
- ch. 12 (Gajdardziska-Josifovska, Carim): 2 "Mean inner potential and its effects on phase images" (268);
  3 "Theoretical calculations of mean inner potential" (271); 4 "Holographic experimental measurements of
  mean inner potential" (275); 7 "Applications of holography to surfaces" (287).
- ch. 14 (Spence, Cowley): 7 "The reflection mode" (page by column alignment 328; inferred).
- ch. 2 (Cowley, Spence): 10 "Studies of surface structure."
So the bib's "IMPORTANT NEGATIVE RESULT" (no reflection-geometry chapter) holds at CHAPTER level only;
there are surface / reflection SECTIONS in ch. 2, 12 and 14.

Reading-plan mapping (`docs/07_reading_plan.md:36`, "C01 in full; ch. 13 on diffracted-beam holography"):
- C01 -> ch. 6, pp. 125-151. Confirmed.
- ch. 13 -> "Electron Holography Using Diffracted Electron Beams (DBH)", Herring and Pozzi, pp. 295-310.
  Confirmed.
- Label: structure METADATA_VERIFIED; C01 and ch. 13 identity METADATA_VERIFIED via Crossref. Content: not
  read.

## B10 - Tonomura, Electron Holography, 2nd ed., Springer 1999

Bib record: `doi 10.1007/978-3-540-37204-2`, edition 2, 1999.

Routes: `https://link.springer.com/book/10.1007/978-3-540-37204-2` (1 TOC page) and
`https://link.springer.com/content/pdf/bfm:978-3-540-37204-2/1` (9 pp.). Bibliographic block: "Edition
number : 2"; "Copyright information : Springer-Verlag Berlin Heidelberg 1999"; Hardcover ISBN
978-3-540-64555-9 "Published: 02 July 1999"; Softcover 978-3-642-08421-8 (07 December 2010); eBook
978-3-540-37204-2 (11 November 2013). All chapters by Akira Tonomura. Printed Contents numbers chapters
"1." to "9." and they match the HTML order and first pages.

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Front Matter | I-XI |
| 1 | Introduction | 1-1 |
| 2 | Principles of Holography | 2-9 |
| 3 | Electron Optics | 10-19 |
| 4 | Historical Development of Electron Holography | 20-28 |
| 5 | Electron Holography | 29-49 |
| 6 | Aharonov-Bohm Effect: The Principle Behind the Interaction of Electrons with Electromagnetic Fields | 50-77 |
| 7 | Electron-Holographic Interferometry | 78-132 |
| 8 | High-Resolution Microscopy | 133-145 |
| 9 | Conclusions | 146-146 |
| - | Back Matter | 147-163 |

Printed section titles of ch. 7 (front-matter Contents, pp. as printed): 7.1 Thickness Measurements (78);
7.2 Surface Topography (83); 7.3 Electric Field Distribution (84); 7.4 Domain Structures in Ferromagnetic
Thin Films (85); 7.5 Domain Structures in Fine Ferromagnetic Particles (90); 7.6 Magnetic Devices (93);
7.7 Domain Structures in Three-Dimensional Particles (96); 7.8 Three-Dimensional Image (99); 7.9 Dynamic
Observation of Domain Structures (102); 7.10 Static Observation of Fluxons in the Profile Mode (103);
7.11 Dynamic Observation of Fluxons in the Profile Mode (108); 7.12 Observation of Fluxons in the
Transmission Mode (117). No section title in the whole printed Contents contains "reflection"; the only
"surface" title is 7.2.

Reading-plan mapping (`docs/07_reading_plan.md:37`, "ch. 7 Electron-holographic interferometry and any
surface or reflection section"):
- ch. 7 -> "Electron-Holographic Interferometry", pp. 78-132. Number and title confirmed.
- surface/reflection section -> 7.2 "Surface Topography", p. 83 (next section starts p. 84). Whether it
  concerns reflection holography is unknown until read. The bib's warning "ch. 7 is a guess" is now
  narrowed to a one-page section locator.
- Label: structure METADATA_VERIFIED. Content: not read.

## B11 - Shindo and Tomita, Material Characterization Using Electron Holography, Wiley-VCH 2022

Bib record: ISBN 9783527348046, Wiley-VCH, 2022; URL the wiley.com product page.

Routes:
1. `https://www.wiley.com/en-us/material-characterization-using-electron-holography-p-9783527348046`
   (HTTP 200). Shown: authors "Daisuke Shindo, Takeshi Tomita"; hardcover ISBN 978-3-527-34804-6
   "October 2022", "240 pages"; E-Book 978-3-527-82970-5 "August 2022"; O-Book 978-3-527-82971-2
   "September 2022"; `wEditionNumber` "1". Its "Table of Contents" (embedded page data) is an OUTLINE that
   does not match the published book: "PART I THEORY AND PRINCIPLES" 1.1-1.7 and "PART II APPLICATION"
   2.1-2.7 (e.g. "1.5 Principles of electron holography", "2.1 Electric field analysis").
2. The publisher's excerpt PDF linked on that page,
   `https://media.wiley.com/product_data/excerpt/42/35273480/3527348042-23.pdf` = the printed "Contents"
   (pp. v-viii). Two other excerpts on the same page: `...-12.pdf` = ch. 1 opening pages; `...-19.pdf` =
   Index pp. 221-227 (their running footer: "Material Characterization using Electron Holography, First
   Edition. Daisuke Shindo and Takeshi Tomita. © 2023 WILEY-VCH GmbH. Published 2023 by WILEY-VCH GmbH.").
3. Crossref `https://api.crossref.org/works?filter=isbn:9783527348046&rows=100` (20 records: monograph
   `10.1002/9783527829712`, published 2022-09-02, ISBNs 9783527348046 and 9783527829712; 4 parts, 12
   chapters `.ch1`-`.ch12`, appendix `.app1`, index). `onlinelibrary.wiley.com` itself: 403.

TOC (numbers from the printed Contents, route 2; titles and pages from Crossref, route 3; joined by title):

| No. | Title as printed on the route | Pages |
|---|---|---|
| - | Part: Introduction | 1-1 |
| 1 | Importance of Electromagnetic Field and Its Visualization | 3-6 |
| 2 | M axwell's Equations and Special Relativity | 7-10 |
| 3 | Basis of Transmission Electron Microscopy | 11-12 |
| - | Part: Principles and Practice | 13-13 |
| 4 | Principles of Electron Holography | 15-27 |
| 5 | Microscope Constitution and Hologram Formation | 29-57 |
| 6 | Related Techniques and Specialized Instrumentation | 59-97 |
| - | Part: Application | 99-99 |
| 7 | Electric Field Analysis | 101-121 |
| 8 | Magnetic Field Analysis | 123-165 |
| - | Part: Visualization of Collective Motions of Electrons and Their Interpretation | 167-168 |
| 9 | Charging Effects and Secondary Electron Distribution of Biological Specimens | 169-184 |
| 10 | Collective Motions of Electrons Around Various Charged Insulators | 185-194 |
| 11 | Extension of Analysis of Collective Motions of Electrons | 195-198 |
| 12 | Theoretical Consideration on Visualizing Collective Motions of Electrons | 199-218 |
| A | Physical Constants, Conversion Factors, and Electron Wavelength | 219-220 |
| - | Index | 221-227 |

(Title "M axwell's Equations..." is Crossref's `<scp>M</scp>axwell's` markup; the printed Contents reads
"Maxwell’s Equations and Special Relativity". The printed Contents gives the same first pages as Crossref.)

Printed section titles relevant to the plan (route 2): 4.2 Outline of Electron Holography (16); 4.3
Comparison of Phase Shifts Due to Scalar and Vector Potentials (20); 4.4 Analysis of Reconstructed Phase
Images by Computer Simulation (23); 5.2 Biprism System (41); 5.3 Coherence Lengths (44); 5.4 Formation of
Interference Fringes (46); 6.1 Split-Illumination Electron Holography (59); 6.2 Dark-Field Electron
Holographic Interferometry (62); 7.1 Measurement of Inner Potential (101). (The PDF text layer drops the
spaces between words in section titles; spaces restored here.)

Year: bib 2022; Crossref published 2022-09-02; product page hardcover "October 2022"; but the book's own
running footer in the excerpts reads "© 2023 ... Published 2023". Fact recorded; not resolved here.

Reading-plan mapping (`docs/07_reading_plan.md:38`, "reconstruction and quantitative-phase chapters"):
no chapter title contains "reconstruction" or "quantitative". By title: ch. 4 "Principles of Electron
Holography" (pp. 15-27; §4.4 on reconstructed phase images), ch. 5 "Microscope Constitution and Hologram
Formation" (pp. 29-57), ch. 6 "Related Techniques and Specialized Instrumentation" (pp. 59-97; §6.2
"Dark-Field Electron Holographic Interferometry", p. 62), ch. 7 §7.1 "Measurement of Inner Potential"
(p. 101). Label: structure METADATA_VERIFIED (Wiley Contents PDF + Wiley Crossref deposit). Content: not
read.

