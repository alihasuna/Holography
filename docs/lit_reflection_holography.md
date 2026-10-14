# Literature survey: reflection electron holography (REM holography) and modern off-axis holography

Status: IN PROGRESS (written incrementally, 2026-10-14). Source policy: project instruction file
(labels METADATA_VERIFIED, SECTION_READ, UNVERIFIED, +ABSTRACT(index)). Every claim below is tagged
READ (text actually opened and read in this session, with the URL) or NOT VERIFIED.

## Access conditions in this session (2026-10-14)

Reachable (HTTP 200 through the agent proxy): api.crossref.org, api.openalex.org,
api.semanticscholar.org, export.arxiv.org, pmc.ncbi.nlm.nih.gov, ebi.ac.uk (Europe PMC),
iopscience.iop.org (article pages; the PDF of JJAP 27 L1772 redirects to a sign-in page),
www.jstage.jst.go.jp.
Blocked by the publisher host itself (HTTP 403 returned by the host, not by the proxy; the proxy status
shows no relay failure): journals.aps.org, www.sciencedirect.com, onlinelibrary.wiley.com,
academic.oup.com.

## Working notes (incremental)

* Osakabe, Matsuda, Endo, Tonomura, JJAP 27 (9A) L1772 (1988): IOP article page opened
  (https://iopscience.iop.org/article/10.1143/JJAP.27.L1772/pdf, served as the HTML article page);
  abstract READ; full-text PDF behind sign-in.
* Endo and Tonomura, Materials Transactions JIM 31(7) 551-560 (1990), DOI 10.2320/matertrans1989.31.551
  (DOI from Crossref record read via api.crossref.org): full scanned PDF opened from J-STAGE
  (https://www.jstage.jst.go.jp/article/matertrans1989/31/7/31_7_551/_pdf), pages rendered and READ;
  section VI "Measurement of Surface Morphology" (pp. 559-560), Figs. 20 and 21.
* Citation-graph check (Semantic Scholar Graph API, citations endpoint, read 2026-10-14) of JJAP 27 L1772,
  PRL 62 2969, JEMT 20 450 and 457, Ultramicroscopy 48 475, 483 and Surf. Sci. 298 345: no citing work after
  1995 is a reflection electron holography experiment (details in section 4). OpenAlex citing-works query
  failed (daily anonymous budget exhausted, HTTP 429).
* Tonomura, "Electron holography and its applications to nanoworld observation", Trans. Mater. Res. Soc.
  Jpn. vol. 2, p. 14 onward (year not printed on the pages read; latest cited reference 1990; no DOI found):
  scanned PDF (OCR text layer) opened at https://www.mrs-j.org/pub/tmrsj/vol02/vol02_014.pdf; text pp. 16-18
  and Fig. 7 (p. 30) READ.
* Osakabe and Tonomura (inventors), Hitachi Ltd, US 4,998,788 "Reflection electron holography apparatus"
  (dates shown 1990-01-10 and 1991-03-12): Google Patents full text opened at
  https://patents.google.com/patent/US4998788A/en and READ (description, equations (1)-(2), claims).
* Harada, "Interference and interferometry in electron holography", Microscopy 70(1) 3-16 (2021),
  PMC7850541, PMID 32589205: full text READ at https://pmc.ncbi.nlm.nih.gov/articles/PMC7850541/
  (equations are images in the PMC HTML and were not read; text and captions read).
* Akase and Shindo, "Effects of Dynamical Electron Diffraction on Phase Shift Detected by Electron
  Holography", Mater. Trans. 60(10) 2120-2124 (2019), DOI 10.2320/matertrans.MT-MI2019007 (DOI printed on
  p. 1): full text READ from https://www.jstage.jst.go.jp/article/matertrans/60/10/60_MT-MI2019007/_pdf .
* Cho, Niitsu, Midoh, Nakamae, Shindo, Yang, Murakami, "Suppressing Geometric Phase Shift Owing to
  Antiphase Boundaries in Dark-Field Electron Holography", Mater. Trans. 60(5) 698-703 (2019), DOI
  10.2320/matertrans.MC201809 (printed on p. 1): full text READ from
  https://www.jstage.jst.go.jp/article/matertrans/60/5/60_MC201809/_pdf .
* Subakti et al., arXiv:2210.04027v1 (published as Phys. Rev. Research 5, 033137 (2023), DOI
  10.1103/PhysRevResearch.5.033137 per the Crossref record read via api.crossref.org): arXiv PDF READ
  (https://arxiv.org/pdf/2210.04027); experimental conditions are deferred to their Ref. [27].
* Boureau et al., J. Appl. Cryst. 53, 885-895 (2020), DOI 10.1107/S1600576720006020: only the HAL API
  record (title, authors, abstract) read at
  https://api.archives-ouvertes.fr/search/?q=halId_s:hal-03001931 ; the HAL full text and journals.iucr.org
  were blocked (bot check / HTTP 403). Not in the table.
* Osakabe, Endo, Matsuda, Fukuhara, Tonomura, "Observation of surface morphologies by reflection electron
  holography" (反射型電子線ホログラフィーによる結晶表面の観察), JPS meeting abstract 6p-T-5, Meeting
  Abstracts of the Physical Society of Japan 1989.2, p. 439: one-page scanned abstract READ (Japanese) at
  https://www.jstage.jst.go.jp/article/jpsgaiyok/1989.2/0/1989.2_439_1/_pdf (record
  https://www.jstage.jst.go.jp/article/jpsgaiyok/1989.2/0/1989.2_439_1/_article).
* Osakabe, "Observation of Surfaces by Reflection Electron Holography" (反射型電子線ホログラフィー法による
  表面の観察), JPS meeting abstract 2a-T-7, Meeting Abstracts of the Physical Society of Japan 45.2,
  pp. 451-452 (1990): two-page scanned abstract READ (Japanese) at
  https://www.jstage.jst.go.jp/article/jpsgaiyod/45.2/0/45.2_451/_pdf . Contains the refraction-corrected
  kinematic step-phase formula and the integer-fringe argument for b_z (see table).
* Europe PMC REST records (abstract text as indexed, read 2026-10-14 via
  https://www.ebi.ac.uk/europepmc/webservices/rest/search): Osakabe, Microsc. Res. Tech. 20, 457-462 (1992),
  PMID 1498359, DOI 10.1002/jemt.1070200415, abstract READ; Banzhof, Herrmann, Lichte, Microsc. Res. Tech.
  20, 450-456 (1992), PMID 1498358, DOI 10.1002/jemt.1070200414, abstract READ (resolves the 450-456 vs
  450-466 page conflict of references.bib in favour of 450-456); Osakabe et al. PRL 62, 2969-2972 (1989),
  PMID 10040140: record has no abstract.
