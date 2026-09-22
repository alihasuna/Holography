# Reading plan for the reference library of the instruction file

Status: 2026-09-22, revision 2 (after Phase 1: steps 1 to 3 of the order of work are done; see
"Status after Phase 1" at the end). Every source below is in `docs/references.bib` under the same ID. "Access" is the
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

## Books and chapters (locators from the publisher tables of contents, report L3; chapters need upload)

Chapter numbers, titles and page ranges below are METADATA_VERIFIED from the publisher's table of
contents or its Crossref chapter records (`docs/agent_reports/L3_book_tables_of_contents.md`,
`L3_book_tocs.tsv`); no chapter content has been read. OUP, ScienceDirect and Wiley Online Library
pages are blocked here by bot checks, so B01 and B08 rest on OUP's Crossref deposit and the chapter
numbers of B08 are inferred from the deposit order.

| ID | Record | What to read (exact locator) | Why |
|---|---|---|---|
| B01 | Spence, High-Resolution Electron Microscopy, 4th ed., OUP 2013 | ch. 3 "Wave optics" (pp. 46-66), ch. 4 "Coherence and Fourier optics" (pp. 67-87); no chapter is titled "aberrations" or "diffraction": the printed Contents are needed to place them | transfer-function and coherence conventions for the optics module |
| B02 | De Graef, Introduction to Conventional TEM, CUP 2003 | ch. 1 "Basic crystallography" (pp. 1-78); there is no reciprocal-space chapter and the structure-factor section is not locatable online: printed Contents (pp. vii-xiii) first | (hkl) vs [uvw] conventions, diamond structure factor (SM02) |
| B03 | Hawkes and Kasper, Principles of Electron Optics vol. 3, 2nd ed., 2022 (chapters 54-68, pp. 1457-1998, series-continuous numbering) | wave mechanics, propagation, interference and holography: ch. 55-60 (pp. 1475-1565), ch. 61-63 (pp. 1569-1681), ch. 58 and 63 first; IMAGE FORMATION is here, ch. 64-68 (pp. 1685-1867), esp. ch. 65 (1691-1705) and ch. 66 (1707-1796) | propagation approximations; image formation |
| B04 | Hawkes and Kasper, vol. 4, 2nd ed., 2022 | COHERENCE is here, not in vol. 3: ch. 78 "Coherence and the Brightness Functions" (pp. 2323-2369), ch. 79 "Wigner Optics" (pp. 2371-2392); phase problem ch. 74 (pp. 2169-2219); sampling ch. 71 (pp. 2101-2117); ch. 75 is three-dimensional reconstruction, not hologram reconstruction | ensemble and coherence treatment (SM13) |
| B05 | Rose, Geometrical Charged-Particle Optics, 2nd ed., 2012 (Crossref; revision 1 gave 2012/2013) | ch. 7-9 (pp. 251-385) as needed | lens transfer parameters; cannot supply biprism data |
| B06 | Kirkland, Advanced Computing in Electron Microscopy, 3rd ed., 2020 | ch. 4 "Sampling and the Fast Fourier Transform" (pp. 81-98); ch. 6 "Theory of Calculation of Images of Thick Specimens" (pp. 143-195); ch. 7 "Multislice Applications and Examples" (pp. 197-239); for SM17 also ch. 5 "Calculation of Images of Thin Specimens" (pp. 99-141, sec. 5.2 from p. 102) and App. C "Atomic Potentials and Scattering Factors" (from p. 283) | propagator form and paraxial limits (SM08), the 2/3 anti-aliasing rule (SM15; P04 does not state it), potential parameterisation and its mean inner potential (SM17) |
| B07 | Ichimiya and Cohen, Reflection High-Energy Electron Diffraction, CUP 2004 (DOI 10.1017/CBO9780511735097) | ch. 5 "The diffraction conditions" (pp. 28-42); ch. 7 "Kikuchi and resonance patterns" (pp. 62-76); ch. 12 "Dynamical theory - transfer matrix method" (pp. 161-172); ch. 13 "Dynamical theory - embedded R-matrix method" (pp. 173-191); ch. 14 "Dynamical theory - integral method" (pp. 192-194); optional ch. 11 "Fourier components of the crystal potential" (pp. 154-160) for the RHEED definition of `V0` | refraction and critical angle as printed (SM04), surface-parallel slicing, rocking-curve theory, resonance conditions |
| B08 | Peng, Dudarev and Whelan, High-Energy Electron Diffraction and Microscopy, OUP 2004 | "Dynamical Theory III. Reflection High-Energy Electron Diffraction" (pp. 117-185; ch. 5 by deposit order); "The Atomic Scattering Factor and the Optical Potential" (pp. 427-453; ch. 13); optional "Resonance Effects in Transmission and Reflection High-Energy Electron Diffraction" (pp. 186-227; ch. 6); the RHEED-routine appendix is one of App. A-D (pp. 470-500) and needs the printed Contents to identify | Bragg-case Bloch waves for the phase-validation ladder, absorptive potential (input item 21), resonance conditions |
| B09, C01 | Völkl, Allard and Joy (eds.), Introduction to Electron Holography, 1999 (editor Edgar Völkl) | C01 = ch. 6 "The Reconstruction of Off-Axis Electron Holograms", Völkl and Lehmann (pp. 125-151); ch. 13 "Electron Holography Using Diffracted Electron Beams (DBH)", Herring and Pozzi (pp. 295-310); ch. 2, 12 and 14 have sections on surfaces or the reflection mode (by title); ch. 12 sec. 2-4 (pp. 268-279) concern the mean inner potential (by title) | sideband reconstruction algorithm, carrier and mask rules (SM12), diffracted-beam holography precedent |
| B10 | Tonomura, Electron Holography, 2nd ed., 1999 | ch. 7 "Electron-Holographic Interferometry" (pp. 78-132); its only surface section is sec. 7.2 "Surface Topography" (p. 83) | Hitachi reflection-holography arrangement and sensitivity claims |
| B11 | Shindo and Tomita, Material Characterization Using Electron Holography, Wiley 2022 | no chapter is titled reconstruction or quantitative phase: ch. 4 (pp. 15-27) and sec. 6.2 (p. 62) are nearest; sec. 7.1 (p. 101) concerns the mean inner potential (by title) | modern reconstruction practice |
| B12, C02 | Springer Handbook of Microscopy, 2019 | C02 = ch. 16 "Electron Holography", Dunin-Borkowski, Kovács, Kasama, McCartney, Smith (pp. 767-818) | quantitative phase measurement, ensemble and detector treatment (SM12, SM13) |
| C03 | Rodenburg and Maiden, "Ptychography", ch. 17 of B12 (pp. 819-904) | the author accepted manuscript is READ (L5 section 2.5; SM24); the version of record is needed only to convert AM page locators to book pages | multiplicative-object assumption versus dynamical reflection (M6) |
| B13 | Kohl and Reimer, TEM: Physics of Image Formation, 5th ed., 2008 | ch. 5 (online pp. 139-192, printed from p. 141), sec. 6.5, sec. 7.4; state which pagination is used | cross-check of transfer and coherence conventions |
| B14 | Williams and Carter, TEM: A Textbook for Materials Science, 2nd ed., 2009 | as needed | experimental context only |
| B15 | Egerton, EELS in the Electron Microscope, 3rd ed., 2011 | one chapter, ch. 3 (pp. 111-229), sec. 3.2-3.4 (pp. 124-177), and App. C (pp. 419-422) | sourcing the absorptive potential and mean free path instead of tuning them (assumption B6) |

## Additional records found by the literature review (revision 1 wording; all now Crossref-checked in report B3)

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

## Status after Phase 1 (2026-09-22)

1. Step 1 done: every record of `docs/references.bib` checked (report B3; counts printed by
   `tools/bib/crossref_check.py report`). Eleven records were accepted with an identifier already
   carried by the entry (ScienceDirect PII, ISBN, chapter ISBN or first page) standing in for a field
   the entry lacked; the orchestrator keeps them, because a PII or ISBN match with the title, container
   and year identifies the record more strictly than the volume would, and each is marked "accepted by
   identifier substitution" in its note. New records added in the second pass follow the strict rule.
2. Step 2 done: P04, P07, S01, S02, P49 (preprint and code) and the patent US 4,998,788 read in full
   (reports L1, L2); in addition P02E, the C03 accepted manuscript, Hÿtch et al. 2010 and the Si
   mean-inner-potential preprint arXiv:2607.05948v1 were read (L5). P07 contains nothing on Osakabe's
   arrangement; the P01 abstract gives Pt(111) and a self-reference (docs/02).
3. Step 3 done: publisher tables of contents recorded (L3); the book table above carries the exact
   locators. Printed Contents pages are still needed for B01, B02, B03, B04 and B08.
4. Citation lists of P01, P02, P02E, P03, P08 and P09 run (L4); the answer on post-1993 reflection
   holography and reflection ptychography is in `docs/02_literature_position.md`.

### Upload list for Ali (step 4, in the plan's order; items now read are removed)

| # | Item | Exact locator | Note |
|---|---|---|---|
| 1 | P01 | Osakabe, Matsuda, Endo, Tonomura, Jpn. J. Appl. Phys. 27 (9A), L1772 (1988), doi:10.1143/JJAP.27.L1772 | OpenAlex flags it free, but the IOP page says the computer is not registered for a subscription; a browser download may work, else JSAP member access |
| 2 | P08 | Osakabe, Microsc. Res. Tech. 20(4), 457-462 (1992), doi:10.1002/jemt.1070200415 | closed |
| 3 | P02 | Osakabe et al., Phys. Rev. Lett. 62, 2969-2972 (1989), doi:10.1103/PhysRevLett.62.2969 | closed; P02E no longer needed (read) |
| 4 | P03 | Banzhof and Herrmann, Ultramicroscopy 48, 475-481 (1993), doi:10.1016/0304-3991(93)90123-F | closed |
| 5 | B07 | ch. 5, 7, 12, 13, 14 (pp. 28-42, 62-76, 161-194); optional ch. 11 (pp. 154-160) | see book table |
| 6 | B08 | pp. 117-185 and pp. 427-453, plus the printed Contents pages; optional pp. 186-227 | see book table |
| 7 | B06 | ch. 4, 6, 7 (pp. 81-98, 143-195, 197-239); for SM17 also ch. 5 (pp. 99-141) and App. C (from p. 283) | see book table |
| 8 | C01 | B09 ch. 6, pp. 125-151, doi:10.1007/978-1-4615-4817-1_6 | closed |
| 9 | C02 | B12 ch. 16, pp. 767-818, doi:10.1007/978-3-030-00069-1_16 | closed |
| 10 | P31 | Hÿtch, Houdellier, Hüe, Snoeck, Ultramicroscopy 111, 1328-1337 (2011), doi:10.1016/j.ultramic.2011.04.008 | closed; the 2010 companion is read, P31's own sign is not |
| 11 | Si mean inner potential, measured | Kruse et al., Ultramicroscopy 106, 105-113 (2006), doi:10.1016/j.ultramic.2005.06.057 (first choice) or Wang et al., Appl. Phys. Lett. 70, 1296 (1997), doi:10.1063/1.118556 | a DFT value is read (12.53 V); a measured value with uncertainty is still needed |
| 12 | P05 | Rangel DaCosta et al., Micron 151, 103141 (2021), doi:10.1016/j.micron.2021.103141 | open access (CC BY): a browser download is enough |
| 13 | P06 | Maiden and Rodenburg, Ultramicroscopy 109, 1256-1262 (2009), doi:10.1016/j.ultramic.2009.05.012 | closed |
| 14 | B10 | ch. 7, pp. 78-132 (minimum p. 83-84, sec. 7.2) | closed |

Added by Phase 1, after the plan's list: 15 Suzuki et al., Jpn. J. Appl. Phys. 40, 2527 (2001),
doi:10.1143/jjap.40.2527 (the only post-1993 reflection interferometry paper with a stated specimen;
flagged free by OpenAlex, not retrievable here); 16 Osakabe et al., Ultramicroscopy 48, 483 (1993) and
Osakabe, Surf. Sci. 298, 345 (1993); 17 Herring, Proc. MSA 53, 116 (1995); 18 Takeguchi, Harada and
Shimizu, J. Electron Microsc. (1990), doi:10.1093/oxfordjournals.jmicro.a050815; 19 the journal version
of P49 (Comput. Phys. Commun. 296, 109029); 20 "Optik Suppl. 3, 77 (1987) p. 4", the prior art cited by
the patent (unidentified; library request); 21 the printed Contents pages of B01, B02, B03, B04 and B08;
22 optionally an OpenAlex API key to rerun six rate-limited searches.
