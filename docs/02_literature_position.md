# Literature position (summary; full reports under `docs/agent_reports/`)

Status: 2026-09-22, revision 3 (network access Full). Sources of this revision: the bibliography
verification B3, the open-source readings L1 (P07, the Hitachi patent) and L2 (P04, prismatique docs,
Prismatic pages, P49), the publisher tables of contents L3, the citation-graph search L4 and the
open-access check L5. Revision 2 rested on the web-search index only; its report
(`docs/agent_reports/B_literature.md`) is kept unedited as the record, and where it differs from what
follows, this revision holds. Labels: METADATA_VERIFIED (Crossref or publisher record), SECTION_READ
(text read, with locator), `+ABSTRACT(publisher)` and `+ABSTRACT(PubMed)` (the abstract read on the
publisher page or on PubMed/Europe PMC; this is SECTION_READ of the abstract and of nothing else),
UNVERIFIED.

## Access in this revision

* Every record of `docs/references.bib` was checked against Crossref, DataCite, arXiv or the patent
  office (B3; counts printed by `tools/bib/crossref_check.py report`).
* Read in full: P04, P07, the patent US 4,998,788 (PAT01) with part of US 5,192,867, the prismatique
  rendered documentation (S01), the Prismatic project pages (S02), the P49 preprint and its code, the
  erratum P02E, the accepted manuscript of chapter C03, Hÿtch et al. 2010 (companion of P31), and the
  Si mean-inner-potential preprint arXiv:2607.05948v1.
* Read at abstract level only: P01 (IOP page), P08, P09, P31, P05 (PubMed), and the post-1993 reflection
  papers listed below.
* Closed here (landing pages checked, L5 section 1): the bodies of P01, P02, P03, P06, P08, P09, P31 and
  all book chapters. P05 is open access (CC BY 4.0) but ScienceDirect, eScholarship and TARA block
  automated clients. OpenAlex flags P01 as free ("bronze"); the IOP page itself states that the
  computer is not registered for a subscription (L5), so the flag is not relied on.
* Not searched: Scopus, Web of Science, Google Scholar, and the Japanese databases (CiNii, J-STAGE
  full text); six OpenAlex search queries failed on the rate limit (L4 section 4.5).

## Starting point: Osakabe's reflection electron holography

| ID | Record | What is now supportable |
|---|---|---|
| P01 | Osakabe, Matsuda, Endo, Tonomura, Jpn. J. Appl. Phys. 27 (9A), L1772 (1988) | `+ABSTRACT(publisher)`, IOP landing page, abstract sentences 1 to 4: a Pt(111) surface at glancing incidence; an electron biprism overlaps two regions of the reflection electron image to form an off-axis hologram; optical reconstruction of the phase of the diffracted wave; a sensitivity "of the order of 0.01 nm" on mono-atomic steps. That both waves are reflected, i.e. a self-reference of type R2, is DERIVED_HERE. The body is unread: energy, reflection order, glancing angle, phase relation, sign and measured phases are UNVERIFIED. P01 is therefore a Pt(111) benchmark, not a silicon one. |
| PAT01 | US 4,998,788, "Reflection electron holography apparatus", N. Osakabe and A. Tonomura (Hitachi); filed 1990-01-10, JP priority 1989-01-13, issued 1991-03-12 | SECTION_READ in full (L1 section 3). The invention superposes the reflected wave on a direct (vacuum) wave that does not illuminate the specimen (R1), in two embodiments: objective over-focus with one diverging image-side biprism under a two-hole aperture (image offset `d = Cs alpha^3 - Delta f alpha`, Eq. (1)), or a condenser-side biprism that pre-tilts the beam by the sum of incidence and reflection angles, followed by two image-side biprisms. The prior art, which the patent cites as P01 and "Optik Suppl. 3, 77 (1987) p. 4", is described as interference between reflected waves giving about ten fringes (col. 1 l. 13-33; a statement about P01, UNVERIFIED for P01). Eq. (2) is printed defectively in both the US and the EP publication; the 100 kV of the text is the assumption of a worked example. Revision 2's five-inventor list and its 1991/1993 dates belong to the related US 5,192,867, which has its own reflection embodiment. |
| P02, P02E | Osakabe, Endo, Matsuda, Tonomura, Fukuhara, Phys. Rev. Lett. 62, 2969 (1989); erratum PRL 63, 584 | P02E SECTION_READ in full: it only reprints Fig. 3, whose caption gives GaAs(110), the (880) Bragg reflection and a foreshortening factor of 28; it corrects no number. P02's body is closed. |
| P08 | Osakabe, Microsc. Res. Tech. 20(4), 457-462 (1992) | `+ABSTRACT(PubMed)`, sentences 2 and 3: the phase shift of a Bragg-reflected wave measured by holographic interferometry with a field-emission gun and a biprism; geometrical path differences measured in units of the wavelength; a monatomic-step phase and a dislocation displacement field observed. |
| P09 | Banzhof, Herrmann and Lichte, Microsc. Res. Tech. 20(4), 450-456 (1992) | `+ABSTRACT(PubMed)`: biprism at the selected-area-diaphragm position; step phases of pi on Au(111) and 0.9 pi on Pt(111), interpreted "in terms of refraction". |
| P03 | Banzhof and Herrmann, Ultramicroscopy 48, 475-481 (1993) | Identity METADATA_VERIFIED (Crossref); content closed. |
| other Osakabe-era records | Osakabe et al., Proc. EMSA 47, 536 (1989) (abstract read); Osakabe et al., Ultramicroscopy 48, 483 (1993) and Osakabe, Surf. Sci. 298, 345 (1993) (titles only); Takeguchi, Harada and Shimizu, J. Electron Microsc. (1990), reflection holography of GaAs(110) with numerical reconstruction (abstract read; Crossref lacks authors, volume and pages) | METADATA_VERIFIED where Crossref is complete (L4 section 6.2). The 1987 Optik supplement cited by the patent is unidentified. |

## Reflection electron holography after 1993: the citation-graph answer

`tools/lit/citation_lists.py` merged the citing works of P01, P02, P02E, P03, P08 and P09 from OpenAlex
(completed through per-record reference lists because the list endpoint was rate-limited), Semantic
Scholar and OpenCitations COCI: 60 records, 57 distinct works, 32 classified from an abstract and 28
from the title only (L4 sections 2 and 3). Result:

* Reflection electron holography was performed after 1993 by one group found here, the Yagi and
  Tanishiro group at the Tokyo Institute of Technology, in 2001 to 2003, on clean Si(111)7x7:
  Suzuki et al., Jpn. J. Appl. Phys. 40, 2527 (2001) (`+ABSTRACT`: energy-filtered interferometry in
  REM geometry, field-emission gun, Möllenstedt biprism, omega filter; lateral coherence length about
  90 nm for no-loss and about 45 nm for one-plasmon-loss electrons) and Tanishiro, Hyomen Kagaku 24, 166
  (2003) (abstract, English figure captions and reference list read: reflection holograms "produced by
  overlapping of two REM images using an electron biprism", i.e. both waves reflected). The operating
  voltage (about 200 kV) is inferred from undecodable Japanese text and is UNVERIFIED. Their subject is
  interferometry, energy filtering and coherence, not height measurement.
* Herring, Proc. MSA 53, 116 (1995) proposes reflection diffracted-beam interferometry; the abstract read
  does not show that a reflection interferogram was recorded.
* Nothing after 2003, and nothing on Si(001) or on ion-milled surfaces, was found in OpenAlex, Semantic
  Scholar, COCI, Europe PMC, arXiv or the Crossref top-100 lists with the queries recorded in L4
  section 4. The nine citing works after 2003 are reviews, transmission holography, one REM encyclopedia
  entry and three unrelated papers. This is an absence in the databases and queries named, not proof of
  absence; the Japanese databases are the most likely place for more work by the Tokyo group.

## Reflection ptychography

* No peer-reviewed electron reflection-mode ptychography was found (Semantic Scholar returned zero hits
  for ptychography with RHEED, REM or backscattered electrons; arXiv zero for ptychography with RHEED;
  L4 section 4.2). Every electron-ptychography abstract read is in transmission, including the 20 keV SEM
  work of Blackburn et al. (Nat. Commun. 16, 8977, 2025). A reflection-mode electron-beam ptychography
  patent (US 10,755,892) exists but is not peer reviewed and was not read.
* X-ray, EUV and visible reflection ptychography exists and is the analogue: Zhu et al. 2015 (Pt(111)
  steps along the crystal truncation rod), Jørgensen et al. 2024, Myint et al. 2024 and Guenzing et al.
  2026 are confirmed at abstract level; Godard et al. 2011 and Hruszkewycz et al. 2017 at identity level
  (L4 section 4.3). All use multiplicative-object forward models.
* Senhorst, Witte and Coene, Opt. Express 34, 22163 (2026) (abstract read) show that the two-dimensional
  thin-sample approximation breaks down in reflection geometry much earlier than in transmission, even
  for weak (single) scattering of light. Chapter C03 (accepted manuscript, read) states the
  multiplicative exit-wave model (sec. 3.4, Eq. (2)) and a multislice ptychography that "does not account
  for backwardly propagating waves that have been reflected off the layers" (sec. 6.2, AM p. 76). Neither
  treats dynamical electron reflection; a dynamical forward model remains a precondition of milestone M6.

## Theory needed for a reflection forward model

Peng and Cowley 1986 and 1988 (transmission-type multislice applied to the Bragg case), Ichimiya 1983
(surface-parallel slicing; DOI now Crossref-verified), Ma and Marks 1989 to 1992 (Bloch-wave Bragg case),
Yao and Cowley 1990 (Bragg-Bragg and Bragg-channelling resonances), Z. L. Wang 1996 (REM book): identities
METADATA_VERIFIED by Crossref (B3), none read. P49 (Kudo, Yamamoto and Hoshi; preprint read, journal
version Comput. Phys. Commun. 296, 109029, 2024, not read) recasts the RHEED/TRHEPD boundary-value
problem as a matrix initial-value problem for the full Schroedinger equation and returns the complex
reflection amplitude; its released code writes intensities only (L2 section D). The book chapters to read
are now located on the publisher tables of contents (L3; `docs/07_reading_plan.md`).

## Methodological analogues

* Dark-field holography in transmission: Hÿtch et al. 2010 (J. Phys.: Conf. Ser. 241, 012027; read): four
  phase contributions (crystalline, magnetic, electrostatic, geometric), with `phi_g^G = -2 pi g.u` for
  `psi = sum_g psi_g exp(+2 pi i g.r)` (sec. 2, Eqs. (1), (3), (4)); the same sign structure as this
  repository's step phase. P31 (Ultramicroscopy 111, 1328, 2011) is read at abstract level only, so its
  own sign is UNVERIFIED. Lubk et al. 2014 and Meißner et al. 2019: METADATA_VERIFIED, not read.
* Biprism optics: P07 (read) describes single-, double-biprism and split-illumination optics
  (Eqs. (13) to (17), Figs. 7 to 11), the Fourier reconstruction method (Eqs. (18) to (26); sideband
  separation and a resolution of about three fringe spacings, para 56) and the phase-shift method
  (Eqs. (27) to (33)); it treats reflection holography only in para 29, as an instance of the geometric
  optical-path phase, and says nothing on Osakabe's arrangement. PAT01 embodiment 2 is a published
  reflection-mode split-illumination arrangement with a condenser-side biprism.
* University of Victoria work: Blackburn and McLeod 2021, Herring 2021 and 2022 (METADATA_VERIFIED), and
  Herring 1995 above.

## Computational sources (L2)

P04 (read) prints the paraxial propagator `exp(-i pi lambda |q|^2 t)` (Eq. (3)) and an anti-aliasing
aperture at half the maximum scattering angle (p. 3); it does not state the 2/3 rule. The prismatique
documentation confirms the schema facts of report D. The Prismatic citation page asks for three papers
(P04, Pryor et al. 2017, P05), and the project is no longer actively maintained (notice of January 2026).
The back-propagation of the saved HRTEM wave to the supercell mid-plane is stated in no public document
read. Details and source-map rows: `docs/04_software_provenance_summary.md`, SM08 to SM20.

## Silicon mean inner potential

One value is read: 12.53 V, the Si endpoint of the density-functional fit printed in Fig. 2c of
arXiv:2607.05948v1 (Schowalter, Kruse and Rosenauer; bulk-terminated (110) slab; no uncertainty stated).
The abstracts of Pennington et al. 2015 and Auslender et al. 2024 report a surface dependence of the mean
inner potential. Measured silicon values (Kruse et al. 2006, Gajdardziska-Josifovska et al. 1993, Wang et
al. 1997) are closed. `V0 = 12.0 V` stays an ASSUMPTION (`docs/model_assumptions.md` B1).

## What is still needed

The uploads listed in `docs/07_reading_plan.md` (P01 first), a search of the Japanese databases for
reflection electron holography (反射電子ホログラフィー; Tanishiro, Minoda, Suzuki, Yagi), and, optionally, an
OpenAlex API key to rerun the six rate-limited searches.
