# Literature position (summary; full review in `docs/agent_reports/B_literature.md`)

Status: 2026-09-21, revision 2 (after `docs/agent_reports/E2_review.md`). Read the access conditions
first: the analysis environment blocked every scholarly host, so the full review rests on the web-search
index only. Its labels `METADATA_VERIFIED(index)` and `+ABSTRACT(index)` are weaker than
`METADATA_VERIFIED` and `SECTION_READ`; no paper or book chapter was read. The bibliography
`docs/references.bib` (96 entries, 78 index-verified, 18 quarantined as UNVERIFIED) and the
verification log `docs/agent_reports/B2_bib_verification_log.md` record the provenance of every entry.

## Starting point: Osakabe's reflection electron holography

| ID | Record | What is supportable here |
|---|---|---|
| P01 | Osakabe, Matsuda, Endo, Tonomura, Jpn. J. Appl. Phys. 27, L1772 (1988), "Observation of Atomic Steps by Reflection Electron Holography" | Identity only (instruction-file record). Surface, energy, reflection, glancing angle, reference-wave arrangement, phase equation and measured values: UNVERIFIED. The pi and 0.9 pi step phases that a search summariser attributed to this paper belong to P09. |
| P02, P02E | Osakabe et al., Phys. Rev. Lett. 62, 2969 (1989) and erratum PRL 63, 584 | Abstract level: screw dislocation emerging on cleaved GaAs(110), spiral surface deformation, about 0.01 A height precision, asymmetric deformation explained by surface stress relaxation. What the erratum corrects: unknown. |
| P08 | Osakabe, J. Electron Microsc. Tech. (renamed Microsc. Res. Tech.) 20(4), 457-462 (1992), "Observation of surfaces by reflection electron holography" [a] | Abstract-index level: phase shift of a Bragg-reflected wave measured by holographic interferometry with a field-emission gun and a biprism; geometrical path differences measured in units of the wavelength; monatomic-step phase and dislocation displacement field observed. Best accessible statement of the method. |
| P03 | Banzhof and Herrmann, Ultramicroscopy 48, 475 (1993), "Reflection electron holography" | Identity only; not by Osakabe (instruction-file correction). |
| P09 | Banzhof, Herrmann and Lichte, J. Electron Microsc. Tech. (renamed Microsc. Res. Tech.) 20(4), 450-456 (1992) [a] | Abstract level: biprism at the selected-area-diaphragm position; pi step phase on Au(111), 0.9 pi on Pt(111). |
| PAT01 | US 4,998,788, "Reflection electron holography apparatus" (Hitachi) | Identity index-level; the reported description (reflected wave superposed with a direct wave passing beside the specimen, single biprism) is UNVERIFIED. |

[a] P08 and P09 are adjacent articles of the same issue (DOIs 10.1002/jemt.1070200415 and
10.1002/jemt.1070200414). Which masthead volume 20 carried, the old or the new journal name, is
UNVERIFIED (B section 1.4); the DOI stem is the old one.

## Theory needed for a reflection forward model

Peng and Cowley 1986 (Acta Cryst. A42, 545) and 1988 (Surf. Sci. 199, 609): transmission-type
multislice applied to the Bragg case; Ichimiya 1983 (JJAP 22, 176): surface-parallel slicing
(implemented in the open-source `sim-trhepd-rheed`); Ma and Marks 1989 to 1992: Bloch-wave Bragg case
and the consistency of multislice and Bloch waves in reflection; Yao and Cowley 1990 (Ultramicroscopy
33, 237): Bragg-Bragg versus Bragg-channelling resonances and the double-contour step contrast;
Uchida and Lehmpfuhl 1987: double contours of monatomic steps; Ichimiya and Cohen (B07) and Peng,
Dudarev and Whelan (B08) chapters on dynamical RHEED; Z. L. Wang 1996 (REM book, chapter 3
"Dynamical theories of RHEED" recovered by the bibliography pass). All index-level; none read.

## Methodological analogues

* Dark-field electron holography in transmission: Hÿtch et al. 2008 (Nature 453, 1086) and 2011
  (Ultramicroscopy 111, 1328; geometric phase as one of four phase contributions; sign not read here);
  Lubk et al. 2014 and Meißner et al. 2019 show that dynamical effects must be included in the
  interpretation even in transmission.
* Reflection-mode X-ray ptychography and CTR imaging: Zhu et al. 2015 (Appl. Phys. Lett. 106, 101604;
  Pt(111) steps on the crystal truncation rod) is the closest analogue; Godard 2011, Hruszkewycz 2017,
  Jørgensen 2024, Myint 2024, Guenzing 2026: all multiplicative-object forward models, not dynamical.
* No peer-reviewed electron reflection-mode ptychography and no post-2015 reflection electron holography
  experiment was found; the citation-graph search could not be run, so this is a search failure.
* Biprism architecture: Harada et al. 2004 (double biprism), Tanigaki et al. 2012 and 2014
  (split-illumination holography with condenser-side biprisms). Public University of Victoria work:
  Blackburn and McLeod 2021 (ptychography versus off-axis holography), Herring 2021 and 2022
  (diffracted-beam interferometry with a biprism).
* Modern reflection simulation software, verified from READMEs read verbatim: `sim-trhepd-rheed`
  (dynamical, Fortran, GPL, Ichimiya-type surface-parallel slicing) and `rheedium` (JAX, kinematic with
  optional multislice, pre-1.0); abTEM and py_multislice have no reflection mode. Separately, Kudo et
  al. 2023 (`+ABSTRACT(index)`; no code located, and the journal title differs from the preprint title,
  UNVERIFIED) reformulate the RHEED/TRHEPD boundary-value problem as an initial-value matrix ODE.

## What must be done with normal network access (about an hour)

Read P07 (Harada 2021, open access at PMC7850541), P01, P02E, P08 and Hÿtch 2011; Crossref every
bibliography entry; run the Semantic Scholar or OpenAlex citation lists of P01, P02 and P03 to settle the
"nothing since 1993" question honestly. Details in `docs/agent_reports/B_literature.md` section 12.
