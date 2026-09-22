# Reading plan for the reference library of the instruction file

Status: 2026-09-22. Every source below is in `docs/references.bib` under the same ID. "Access" is the
expected route once the environment's network access is Full; paywalled items need a PDF or chapter
uploaded by Ali (instruction file section 1.6: a legitimately supplied chapter or author manuscript).
The target label after reading is SECTION_READ with a chapter, section or equation locator recorded in
`docs/source_map.tsv`; identity checks alone give METADATA_VERIFIED. Nothing below is to be attributed
to a source before it has been read.

## Papers and software

| ID | Record | Access | What to extract (locators required) |
|---|---|---|---|
| P01 | Osakabe, Matsuda, Endo, Tonomura, JJAP 27, L1772 (1988) | paywalled (IOP); abstract readable | surface, energy, reflection order, glancing angle, reference-wave arrangement, phase-step relation as written (refraction, sign), measured phases, limitations; fills CFG-O |
| P02, P02E | Osakabe et al., PRL 62, 2969 (1989) and erratum PRL 63, 584 | paywalled (APS); abstract readable | same items for GaAs(110); what the erratum corrects |
| P03 | Banzhof and Herrmann, Ultramicroscopy 48, 475 (1993) | paywalled (Elsevier); abstract readable | geometry, biprism position, reference wave, phase relation, materials |
| P04 | Ophus, Adv. Struct. Chem. Imaging 3, 13 (2017) | open access; read in full | multislice equations (1) to (5), propagator convention, PRISM interpolation error statements |
| P05 | Rangel DaCosta et al., Micron 151, 103141 (2021) | paywalled (Elsevier); check OSTI or eScholarship for an accepted manuscript | HRTEM mode description: output plane, anti-aliasing rule, tilt implementation, frozen-phonon handling; compare with report D |
| P06 | Maiden and Rodenburg, Ultramicroscopy 109, 1256 (2009) | paywalled (Elsevier); abstract readable | ePIE update equations and their multiplicative-object assumption (for the ptychography milestone) |
| P07 | Harada, Microscopy 70, 3 (2021) | open access at PMC7850541; read in full | reflection-holography history, Osakabe's arrangement, split-illumination and double-biprism optics, reconstruction methods; figure numbers |
| S01 | prismatique documentation and source | GitHub pages and repository; read | version-matched API of 0.0.1 (already SECTION_READ from source in report D; confirm against the rendered docs) |
| S02 | Prismatic project and citation page | prism-em.com, prism-em.github.io; read | citation requirements, HRTEM mode notes, maintenance status |

## Books and chapters (publisher tables of contents are readable; chapters need upload)

| ID | Record | What to read | Why |
|---|---|---|---|
| B01 | Spence, High-Resolution Electron Microscopy, 4th ed., OUP 2013 | chapters on coherent image formation, aberrations, diffraction | transfer-function and coherence conventions for the optics module |
| B02 | De Graef, Introduction to Conventional TEM, CUP 2003 | crystallography and reciprocal-space chapters; structure-factor section | (hkl) vs [uvw] conventions, diamond structure factor (source map SM02) |
| B03 | Hawkes and Kasper, Principles of Electron Optics vol. 3, 2nd ed., 2022 | wave mechanics, propagation approximations, interference and holography, coherence chapters | ensemble and coherence treatment (SM13); check chapter numbering in this edition |
| B04 | Hawkes and Kasper, vol. 4, 2nd ed., 2022 | image formation, phase problems, reconstruction, sampling | reconstruction theory and sampling rules |
| B05 | Rose, Geometrical Charged-Particle Optics, 2nd ed., 2012/2013 | aberration theory sections as needed | lens transfer parameters; cannot supply biprism data |
| B06 | Kirkland, Advanced Computing in Electron Microscopy, 3rd ed., 2020 | Sampling and the FFT; Theory of calculation of images of thick specimens; Multislice applications | propagator form and paraxial limits (SM08), 2/3 anti-aliasing rule (SM15), atomic potential parameterisation and its mean inner potential (SM17), slice thickness |
| B07 | Ichimiya and Cohen, Reflection High-Energy Electron Diffraction, CUP 2004 | The diffraction conditions; Dynamical theory: transfer matrix, embedded R-matrix, integral methods; Kikuchi and resonance patterns | refraction and critical angle as printed (SM04), surface-parallel slicing, rocking-curve theory, resonance conditions |
| B08 | Peng, Dudarev and Whelan, High-Energy Electron Diffraction and Microscopy, OUP 2004 | ch. 5 Dynamical theory III: RHEED; ch. 6 Resonance effects; ch. 13 atomic scattering factor and optical potential; RHEED routine appendix | Bragg-case Bloch waves for the phase-validation ladder, absorptive potential source (input item 21), resonance conditions |
| B09, C01 | Völkl, Allard and Joy (eds.), Introduction to Electron Holography, 1999; Völkl and Lehmann, The Reconstruction of Off-Axis Electron Holograms, pp. 125-151 | C01 in full; ch. 13 on diffracted-beam holography | sideband reconstruction algorithm, carrier and mask rules (SM12), dark-field holography precedent |
| B10 | Tonomura, Electron Holography, 2nd ed., 1999 | ch. 7 Electron-holographic interferometry and any surface or reflection section | Hitachi reflection-holography arrangement and sensitivity claims |
| B11 | Shindo and Tomita, Material Characterization Using Electron Holography, Wiley 2022 | reconstruction and quantitative-phase chapters | modern reconstruction practice; author order Shindo, Tomita |
| B12, C02 | Springer Handbook of Microscopy, 2019; Dunin-Borkowski et al., Electron Holography, pp. 767-818 | C02 in full | quantitative phase measurement, ensemble and detector treatment (SM12, SM13) |
| C03 | Rodenburg and Maiden, Ptychography, pp. 819-904 | forward-model and algorithm sections | multiplicative-object assumption versus dynamical reflection (ptychography milestone) |
| B13 | Kohl and Reimer, TEM: Physics of Image Formation, 5th ed., 2008 | electron-specimen interaction and image-formation chapters | cross-check of transfer and coherence conventions |
| B14 | Williams and Carter, TEM: A Textbook for Materials Science, 2nd ed., 2009 | as needed | experimental context only |
| B15 | Egerton, EELS in the Electron Microscope, 3rd ed., 2011 | inelastic scattering chapters | sourcing the absorptive potential and mean free path instead of tuning them (assumption B6) |

## Additional records found by the literature review (index-level; verify and read where accessible)

P08 Osakabe 1992 (Microsc. Res. Tech. 20, 457), P09 Banzhof, Herrmann and Lichte 1992 (same volume,
450), P17 Ichimiya 1983, P18 and P19 Peng and Cowley 1986 and 1988, P20 to P22 Ma and Marks 1989 to 1990,
P23 Yagi 1987, P25 Uchida and Lehmpfuhl 1987, P26 Yao and Cowley 1990, P30 and P31 Hÿtch et al. 2008
and 2011, P32 Lubk et al. 2014, P33 Meißner et al. 2019, P36 Zhu et al. 2015, P45 and P46 Tanigaki
et al. 2012 and 2014, P47 Harada et al. 2004, P42 Blackburn and McLeod 2021, P43 and P44 Herring
2021 and 2022, P49 Kudo et al. 2023 (arXiv, open), Z. L. Wang 1996 chapter 3, and the Hitachi patent
US 4,998,788 (patent full text is public). Details and current labels: `docs/agent_reports/B_literature.md`.

## Order of work for the session with network access

1. Crossref check of every DOI in `docs/references.bib`; fix any record that differs; log in `B2_bib_verification_log.md`.
2. Read P04, P07, S01, S02, P49 and the patent in full; upgrade labels; extract the items in the tables above.
3. Fetch publisher tables of contents for B01 to B15 and record chapter titles and numbers for the edition named.
4. Request uploads, in this order: P01, P08, P02 with P02E, P03, B07 dynamical chapters, B08 ch. 5 and 13,
   B06 sampling and multislice chapters, C01, C02, Hÿtch 2011, a Si mean-inner-potential paper, P05, P06, C03, B10 ch. 7.
5. After each upload: read, extract, update the source map row and the assumptions file, commit.
