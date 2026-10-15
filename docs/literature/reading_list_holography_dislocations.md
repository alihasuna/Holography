# Reading list: electron holography and the elasticity of dislocations near surfaces

Status: COMPLETE, 2026-10-15 (literature-researcher agent; written incrementally).

**Scope.** This file lists what a PhD student should download to understand and extend this
repository: a simulation of reflection-mode dark-field off-axis electron holography of buried
dislocations under Si(001), at 200 keV. It complements, and does not repeat, the following files:

* `docs/literature/reflection_holography.md` (the Hitachi and Tübingen abstracts, Harada 2021,
  Dunin-Borkowski 2019);
* `docs/literature/dark_field_strain.md` (dark-field electron holography papers already read);
* `docs/literature/reading_plan.md` (multislice and RHEED books).

Items those files already read appear here only where the student must still read them.

**Pipeline steps** (README.md):

1. crystal;
2. defect elastic field;
3. forward model: (3a) multislice, (3b) geometric model;
4. hologram formation and noise;
5. reconstruction;
6. analysis (step phase, g·b fringes, width about 2 × depth).

**Verified column.**

* **TOC READ:** I opened the publisher's (or a library's) table of contents in this session.
* **META:** I checked the metadata on Crossref in this session. This equals METADATA_VERIFIED.
* **ABS READ:** I read the abstract on the page named.
* **TEXT READ:** I read the text.
* **NOT VERIFIED:** content I did not see.

The URLs for every check are in the appendix.

**Priorities.** MUST = needed to understand or defend a pipeline step now. SHOULD = needed for the
next upgrades (anisotropy, dissociated partials, a dynamical comparison). OPTIONAL = background.

## 1. Off-axis electron holography: fundamentals, reconstruction, phase precision against dose, biprism, coherence

| Pri. | Citation | What to read | Why (pipeline step) | Access route | Verified |
|---|---|---|---|---|---|
| **MUST** | R. E. Dunin-Borkowski, A. Kovács, T. Kasama, M. R. McCartney, D. J. Smith, "Electron Holography", ch. 16 in P. W. Hawkes, J. C. H. Spence (eds.), *Springer Handbook of Microscopy* (Springer 2019), pp. 767-818, DOI 10.1007/978-3-030-00069-1_16 | §16.1 "Introduction to Electron Holography" in full. It contains fringe contrast, Eq. (16.9), and phase noise Δφ_min = (SNR/μ)·√(2/N_el), Eq. (16.10), p. 771 (locators from `reflection_holography.md` B2). §16.6 "Alternative Forms" (reflection holography is mentioned there). Skip §16.3-16.4. | Steps 4-5: the Poisson noise model (400 counts per pixel), the empty-hologram correction, and the σ_φ formula in source map SM12 | **Open author copy**, opened this session: https://rafaldb.com/papers/B-2019-Science-of-Microscopy-Electron-holography.pdf | META; section headings 16.1-16.7 TEXT READ in the PDF text layer; equations SECTION_READ earlier (B2), not re-read (lost in my text extraction) |
| **MUST** | E. Völkl, M. Lehmann, "The Reconstruction of Off-Axis Electron Holograms", ch. 6 in E. Völkl, L. F. Allard, D. C. Joy (eds.), *Introduction to Electron Holography* (Springer 1999), pp. 125-151, DOI 10.1007/978-1-4615-4817-1_6 | Whole chapter (27 pp.) | Step 5: FFT, sideband selection, mask, division by the reference hologram, unwrapping; grounds `tests/test_holography.py` | Library e-book (Springer Link; chapter page is paywalled) | TOC READ (Springer book page and Crossref chapter records); text NOT VERIFIED |
| SHOULD | Same book: ch. 3, L. F. Allard, E. Völkl, "Optical Characteristics of an Holography Electron Microscope", pp. 57-86; ch. 15, F. Lenz, J. M. Cowley, "A Plus or Minus Sign in the Fourier Transform?", pp. 333-338; ch. 1, G. Möllenstedt, "The History of the Electron Biprism", pp. 1-15 | Ch. 3 (field-emission coherence and biprism; the abstract says the field-emission source "provided a large jump in capability for making interferograms with high contrast fringes"). Ch. 15 before fixing any phase-sign convention. | Steps 4-5 (coherence, biprism optics, fringe contrast); `docs/theory/physics_conventions.md` (FFT sign) | Library e-book (same download) | TOC READ; ch. 3 ABS READ |
| SHOULD | M. Lehmann, H. Lichte, "Tutorial on Off-Axis Electron Holography", *Microsc. Microanal.* 8(6), 447-466 (2002), DOI 10.1017/S1431927602020147 | Whole tutorial. The abstract (Crossref deposit) says it gives "a step-by-step procedure for recording and reconstruction of holograms". | Steps 4-5; use it if the Springer e-book is not licensed | Library journal (the DOI resolves to academic.oup.com, which served a Cloudflare challenge here) | META; ABS READ |
| SHOULD | H. Lichte, M. Lehmann, "Electron holography - basics and applications", *Rep. Prog. Phys.* 71(1), 016102 (2008), DOI 10.1088/0034-4885/71/1/016102 | Basics, coherence and detection-limit sections (section numbers NOT VERIFIED) | Steps 4-5, the theory behind the noise model | Library journal (IOP; bot-check here) | META |
| SHOULD | H. Lichte, "Performance limits of electron holography", *Ultramicroscopy* 108(3), 256-262 (2008), DOI 10.1016/j.ultramic.2007.06.006 | Whole paper (7 pp.) | Step 4: phase precision against dose and fringe contrast | Library journal | META |
| SHOULD | F. Röder, A. Lubk, D. Wolf, T. Niermann, "Noise estimation for off-axis electron holography", *Ultramicroscopy* 144, 32-42 (2014), DOI 10.1016/j.ultramic.2014.04.002 | Whole paper | Steps 4-6: propagating detector noise into phase-error maps for the "noisy against noiseless" metric | Library journal | META |
| SHOULD | A. Tonomura, *Electron Holography*, 2nd ed. (Springer 1999), DOI 10.1007/978-3-540-37204-2 | Ch. 7 "Electron-Holographic Interferometry", pp. 78-132. Its abstract covers beams "transmitted through or reflected from a sample" and phase precision "as high as 2π/100". Its reference 12 is Osakabe et al., PRL 62, 2969. Also ch. 3 "Electron Optics", pp. 10-19 (for holography, per its abstract). | Steps 4-6: Hitachi interference-micrograph practice and phase-amplified maps | Library e-book (Springer) | TOC READ (Crossref); ch. 3, 5 and 7 ABS READ; ch. 7 reference list READ |
| SHOULD | K. Harada, "Interference and interferometry in electron holography", *Microscopy* 70(1), 3-16 (2021), DOI 10.1093/jmicro/dfaa033 | Already SECTION_READ in `reflection_holography.md` B1. Read the sections on biprism optics and coherence. | Step 4 (biprism geometry, double biprism, carrier ≥ 3 × aperture rule) | **Open**: PMC7850541 (CC BY 4.0 per Crossref) | META (this session); text read earlier |
| OPTIONAL | W. J. de Ruijter, J. K. Weiss, *Ultramicroscopy* 50(3), 269-283 (1993), DOI 10.1016/0304-3991(93)90196-5; A. Harscher, H. Lichte, *Ultramicroscopy* 64, 57-66 (1996), DOI 10.1016/0304-3991(96)00019-8; A. Tonomura, *Rev. Mod. Phys.* 59(3), 639-669 (1987), DOI 10.1103/RevModPhys.59.639; M. R. McCartney, D. J. Smith, *Annu. Rev. Mater. Res.* 37, 729-767 (2007), DOI 10.1146/annurev.matsci.37.052506.084219; H. Lichte et al., *Annu. Rev. Mater. Res.* 37, 539-588 (2007), DOI 10.1146/annurev.matsci.37.052506.084232; P. A. Midgley, R. E. Dunin-Borkowski, *Nat. Mater.* 8, 271-280 (2009), DOI 10.1038/nmat2406; G. Möllenstedt, H. Düker, *Z. Phys.* 145, 377-397 (1956), DOI 10.1007/BF01326780; M. Takeda, H. Ina, S. Kobayashi, *J. Opt. Soc. Am.* 72(1), 156 (1982), DOI 10.1364/JOSA.72.000156; M. Lehmann, H. Lichte, "Holographic Reconstruction Methods", in A. Tonomura et al. (eds.), *Electron Holography* (Elsevier 1995), pp. 69-79, DOI 10.1016/b978-044482051-8/50008-7; T. Kasama, R. E. Dunin-Borkowski, M. Beleggia, "Electron Holography of Magnetic Materials" (InTech 2011), DOI 10.5772/22366 (open-access publisher; not opened) | As needed | Detection limits, history of the biprism, origin of Fourier fringe analysis | Library journals; the InTech chapter is open | META |

## 2. Reflection electron holography: the 1988-1993 Hitachi and Tübingen originals (paywalled)

| Pri. | Citation | What to read | Why (pipeline step) | Access route | Verified |
|---|---|---|---|---|---|
| **MUST** | N. Osakabe, J. Endo, T. Matsuda, A. Tonomura, A. Fukuhara, "Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography", *Phys. Rev. Lett.* 62(25), 2969-2972 (19 June 1989), DOI 10.1103/PhysRevLett.62.2969, **plus the erratum** in *PRL* 63(5), 584 (31 July 1989), DOI 10.1103/PhysRevLett.63.584.3 | Whole letter and erratum. Extract: energy, reflection, glancing angle, reference wave, the phase-to-height relation and its sign, and the isotropic-elasticity comparison. | Steps 2, 3b and 6: the only peer-reviewed reflection-holography measurement of a dislocation's surface displacement, so the benchmark for the surface-relaxation phase | Library journal (APS host blocked here) | META (Crossref lists the same five authors on the erratum); text NOT VERIFIED |
| **MUST** | N. Osakabe, T. Matsuda, J. Endo, A. Tonomura, "Reflection electron holographic observation of surface displacement field", *Ultramicroscopy* 48(4), 483-488 (1993), DOI 10.1016/0304-3991(93)90124-G | Whole paper (6 pp.) | Step 6: the title names exactly this pipeline's observable, the surface displacement field (INFERENCE: probably the full-length follow-up to PRL 1989) | Library journal (Elsevier) | META; text NOT VERIFIED |
| SHOULD | H. Banzhof, K.-H. Herrmann, "Reflection electron holography", *Ultramicroscopy* 48(4), 475-481 (1993), DOI 10.1016/0304-3991(93)90123-F | Whole paper. It is in the same issue as the item above, so download both together. | Steps 3a/3b: the Tübingen geometry and the refraction reading of step phases (checks the step phase of strip 2) | Library journal | META; **Crossref now confirms this DOI**, which `references.bib` P03 had flagged as weak |
| SHOULD | T. Tanji, J. Ito, K. Yada, "Contrast simulation of high resolution electron holography on surface structures", *Ultramicroscopy* 35(3-4), 245-253 (1991), DOI 10.1016/0304-3991(91)90076-I | Abstract first, then the whole paper if it simulates reflected waves | Steps 3-5: the earliest simulation of holographic contrast of surface structures | Library journal | META. **Geometry NOT VERIFIED.** Semantic Scholar lists one citing work: T. Tanji, K. Urata, K. Ishizuka, Q. Ru, A. Tonomura, "Observation of atomic surface potential by electron holography", *Ultramicroscopy* 49, 259-264 (1993), DOI 10.1016/0304-3991(93)90232-M. That suggests (INFERENCE) high-resolution profile (transmission) holography of surfaces rather than reflection. Upgrade to MUST if the abstract shows a reflection simulation. |
| SHOULD | N. Osakabe, "Observation of surfaces by reflection electron holography", *Microsc. Res. Tech.* 20(4), 457-462 (1992), DOI 10.1002/jemt.1070200415; and H. Banzhof, K.-H. Herrmann, H. Lichte, same issue, pp. 450-456, DOI 10.1002/jemt.1070200414 | Whole papers. The abstracts were read earlier (A7). | Steps 3b and 6: Osakabe's method paper; π and 0.9π step phases on Au and Pt | Library journal (Wiley) | META (Crossref container title: *Microscopy Research and Technique*, issued 1992-02-15) |
| SHOULD | N. Osakabe, "Application of electron holography to surface topography observation", *Surf. Sci.* 298(2-3), 345-350 (1993), DOI 10.1016/0039-6028(93)90047-N | Whole paper | Step 6: overview of what the method measures | Library journal | META |
| SHOULD | N. Osakabe, T. Matsuda, J. Endo, A. Tonomura, "Observation of Atomic Steps by Reflection Electron Holography", *Jpn. J. Appl. Phys.* 27(9A), L1772 (1988), DOI 10.1143/JJAP.27.L1772 | Whole letter. The abstract was read earlier (A1). | Step 6: step-phase calibration (strip 2) | Library journal (IOP/JSAP sign-in) | META |
| OPTIONAL | Osakabe, Endo, Matsuda, Tonomura, "Observation of surface morphology by reflection electron holography", *Proc. EMSA* 47, 536-537 (1989), DOI 10.1017/s0424820100154652. J. M. Cowley, "Electron holography and holographic diffraction for surface studies", *Surf. Sci.* 298, 336-344 (1993), DOI 10.1016/0039-6028(93)90046-M. Lead only: "Observation of GaAs(110) Surface Defect by Reflection Electron Holography", *J. Electron Microsc.* (Aug. 1990), DOI 10.1093/oxfordjournals.jmicro.a050815; the Crossref record has **no authors, volume or pages**, so treat it as an unidentified meeting abstract. | As available | History and context | Library or interlibrary loan | META (the 1990 lead is incomplete) |

Negative finding (META): Crossref holds 38 chapter records for the 1995 Elsevier workshop volume
*Electron Holography* (A. Tonomura, L. F. Allard, G. Pozzi, D. C. Joy, Y. A. Ono, eds.), ISBN
9780444820518. They run from the front matter to the author index. None is by Osakabe and none is
about reflection holography, so the alleged Osakabe chapter (`references.bib` U06) is not in that
volume's deposit.

## 3. Dark-field electron holography (DFEH) of strain

| Pri. | Citation | What to read | Why (pipeline step) | Access route | Verified |
|---|---|---|---|---|---|
| **MUST** | M. J. Hÿtch, F. Houdellier, F. Hüe, E. Snoeck, "Dark-field electron holography for the measurement of geometric phase", *Ultramicroscopy* 111(8), 1328-1337 (2011), DOI 10.1016/j.ultramic.2011.04.008 | Whole paper (10 pp.). Extract the geometric-phase equation **with its sign** and validity conditions, the four phase contributions, and the bright-field thickness correction. | Step 3b (the −G·u phase convention) and step 6 (reading g·b fringes). Closes the sign gap flagged in `references.bib` P31, whose entry has no DOI; this DOI is Crossref-verified. | Library journal (Elsevier) | META; ABS READ (PubMed PMID 21864773): "total phase ... described as a sum of four contributions: crystalline, electrostatic, magnetic and geometric" |
| **MUST** | Y.-Y. Wang, Z. Wang, Z. Yang, Q. Jin, "Dislocation Strain Field Mapping Using Dark-Field Electron Holography", *Microscopy Today* 33(6), 43-49 (2025), DOI 10.1093/mictod/qaaf097 | Whole article (7 pp.) | Step 6: the only DFEH paper found on dislocation strain fields in SiGe/Si. It is a comparison target for the 60° case. | Library journal (OUP; blocked here) | META; ABS READ (Crossref deposit): "Strain fields of dislocation on SiGe/Si structures were measured by dark-field electron holography"; "two edge dislocation cores of 2.9nm apart were resolved"; DFEH "can be used to determine Burgers vector orientation" |
| SHOULD | M. Hÿtch, F. Houdellier, F. Hüe, E. Snoeck, "Nanoscale holographic interferometry for strain measurements in electronic devices", *Nature* 453(7198), 1086-1089 (2008), DOI 10.1038/nature07049 | Whole letter and the Methods | The founding paper, to be cited with D1 | Library journal | META |
| SHOULD | A. Lubk, E. Javon, N. Cherkashin, S. Reboh, C. Gatel, M. Hÿtch, "Dynamic scattering theory for dark-field electron holography of 3D strain fields", *Ultramicroscopy* 136, 42-49 (2014), DOI 10.1016/j.ultramic.2013.07.007 | Whole paper | Step 3b: the transmission analogue of the depth weighting w_l = exp(−depth/Λ); dynamical correction of the geometric phase | Library journal | META; ABS READ (PubMed PMID 24012934): "analytic linear projection rules for 3D strain fields ... strain magnitude, specimen thickness, excitation error and surface relaxation" |
| SHOULD | M. Hÿtch, F. Houdellier, N. Cherkashin, S. Reboh, E. Javon, P. Benzo, C. Gatel, E. Snoeck, A. Claverie, "Dark-Field Electron Holography for Strain Mapping", in *Transmission Electron Microscopy in Micro-Nanoelectronics* (ISTE/Wiley 2012), pp. 81-106, DOI 10.1002/9781118579022.ch4 (editor not verified) | Whole chapter (tutorial length) | Steps 5-6: the method end to end | Library e-book (Wiley) | META |
| SHOULD | M. J. Hÿtch, E. Snoeck, R. Kilaas, "Quantitative measurement of displacement and strain fields from HREM micrographs", *Ultramicroscopy* 74(3), 131-146 (1998), DOI 10.1016/S0304-3991(98)00035-7 | Definition of the geometric phase and of strain from phase gradients | Step 6: displacement and strain from the reconstructed phase | Library journal | META |
| SHOULD | R. A. Herring, G. Pozzi, "Electron Holography Using Diffracted Electron Beams (DBH)", ch. 13 of Völkl, Allard, Joy (1999), pp. 295-310, DOI 10.1007/978-1-4615-4817-1_13 | Whole chapter (part of the same e-book download as section 1) | Step 6: diffracted-beam holography of crystal defects. **This resolves the authors and pages of `references.bib` U07.** | Library e-book | TOC READ; ABS READ: "the phase change at crystal regions such as dislocations, compositional gradients, etc., causes the interference fringes to shift" |
| OPTIONAL | A. Béché, J. L. Rouvière, J. P. Barnes, D. Cooper, *Ultramicroscopy* 111(3), 227-238 (2011), DOI 10.1016/j.ultramic.2010.11.030; E. Javon et al., *Ultramicroscopy* 147, 70-85 (2014), DOI 10.1016/j.ultramic.2014.06.005; D. Cooper et al., *Micron* 80, 145-165 (2016), DOI 10.1016/j.micron.2015.09.001; Hÿtch et al., *J. Phys.: Conf. Ser.* 241, 012027 (2010), DOI 10.1088/1742-6596/241/1/012027 (open; already read as P6 in `dark_field_strain.md`) | As needed | Parameter studies and benchmarks | Library journals | META |

## 4. Elasticity of dislocations near a free surface (isotropic and anisotropic)

| Pri. | Citation | What to read | Why (pipeline step) | Access route | Verified |
|---|---|---|---|---|---|
| **MUST** | A. K. Head, "Edge Dislocations in Inhomogeneous Media", *Proc. Phys. Soc. B* 66(9), 793-801 (1953), DOI 10.1088/0370-1301/66/9/309 | Whole paper (9 pp.) | Step 2: the classical isotropic solution for an edge dislocation near a planar boundary. The free surface is the limiting case (INFERENCE from the title; confirm on reading). It is the primary citation for the image construction in `reflection_holo/defects/dislocation.py` and source map SM18. | Library journal (IOP; bot-check here) | META; text NOT VERIFIED |
| OPTIONAL | A. K. Head, "The Interaction of Dislocations and Boundaries", *Phil. Mag.* 44(348), 92-94 (1953), DOI 10.1080/14786440108520278 | Whole note (3 pp.) | Step 2, companion note | Library journal (T&F) | META |
| **MUST** | J. P. Hirth, J. Lothe, *Theory of Dislocations*, 2nd ed. (Wiley 1982), ISBN 0471091251, 857 pp. (the Open Library work record also lists ISBN 0894646176, the Krieger reprint). Or the 3rd ed.: P. M. Anderson, J. P. Hirth, J. Lothe (Cambridge University Press 2017), ISBN 9780521864367, on Cambridge Core (chapter DOI stem 10.1017/9780511977732). | **3rd ed. (chapter numbers READ):** ch. 3 "Theory of straight dislocations" (edge, screw and mixed fields); ch. 5 "Applications to dislocation interactions"; ch. 11 "Partial dislocations in other structures" (diamond cubic: INFERENCE); ch. 13 "Dislocations in anisotropic elastic media". **Which chapter holds the free-surface and image-force treatment is NOT VERIFIED.** Find it in the index under "free surface", "image force" and "Head". No 2nd-edition table of contents could be opened, so 2nd-edition chapter numbers are NOT VERIFIED. | Step 2 (the isotropic field, the mixed 60° dislocation, image forces) and the planned anisotropic upgrade (README: Zener ratio 1.56) | Library e-book (Cambridge Core, 3rd ed.) or print (2nd ed.) | 3rd-ed. TOC READ (retailer page reproducing the CUP contents; the Cambridge Core page of ch. 12 was opened); 2nd-ed. metadata read on Open Library; text NOT VERIFIED |
| **MUST** | D. Hull, D. J. Bacon, *Introduction to Dislocations*, 5th ed. (Butterworth-Heinemann/Elsevier 2011), ISBN 9780080966724, book DOI 10.1016/C2009-0-64358-0 | §4.3 "Stress Field of a Straight Dislocation" and §4.8 "Image Forces" (ch. 4, pp. 63-83); §5.1-5.6 (perfect and Shockley partials, Thompson's tetrahedron, "Dislocation Locks and Stair-Rod Partials"; ch. 5, pp. 85-107); §6.6 "Dislocations in Covalent Crystals" (ch. 6, pp. 109-136). About 60 pages. | Step 2 and the choice between the 60° and Lomer cases: the gentlest route into the notation | Library e-book (ScienceDirect) | Section TOC READ (Elsevier shop page); chapter pages META (Crossref) |
| SHOULD | R. W. Balluffi, *Introduction to Elasticity Theory for Crystal Defects* (CUP 2012), DOI 10.1017/CBO9780511998379: ch. 12 "Dislocations in infinite homogeneous regions", pp. 229-303, and ch. 13 "Dislocations and stress - image effects in finite regions", pp. 304-339. The 2nd ed. (World Scientific 2016, DOI 10.1142/9939) has, by DOI suffix (INFERENCE), ch. 13 "Interactions between Dislocations and Stress: Image Effects", pp. 413-457, DOI 10.1142/9789814749732_0013. | Ch. 13 in full; ch. 12 as needed | Step 2: a rigorous textbook derivation of image effects, with verified chapter numbers | Library e-book (the Cambridge Core page says the CUP edition is no longer for sale; use World Scientific) | TOC READ (Cambridge Core); 2nd ed. META |
| SHOULD | T. C. T. Ting, *Anisotropic Elasticity: Theory and Applications* (Oxford University Press 1996), ISBN 0195074475, DOI 10.1093/oso/9780195074475.001.0001 | Ch. 5 "The Stroh Formalism", pp. 134-159; §7.6 "The Barnett-Lothe Integral Formalism", p. 222; ch. 8 "Green's Functions for Infinite Space, Half-Space, and Composite Space", pp. 243-315, especially §8.1 "Line Force and Line Dislocation in Infinite Space" (p. 243), §8.5 "Surface Green's Function" (p. 258), §8.6 "Green's Functions for Half-Space" (p. 260) and §8.7 "Image Singularities" (p. 268) | Step 2 anisotropic upgrade: the half-space solution for a line dislocation parallel to the surface in cubic Si | Library e-book (Oxford Academic; blocked here) | Section-level TOC READ (library contents scan, prometeus.nsc.ru); chapter titles META |
| SHOULD | J. Lothe, "Dislocations Interacting with Surfaces, Interfaces or Cracks", pp. 329-389, and "Dislocations in Anisotropic Media", pp. 269-328, in V. L. Indenbom, J. Lothe (eds.), *Elastic Strain Fields and Dislocation Mobility* (Elsevier/North-Holland 1992, series Modern Problems in Condensed Matter Sciences), ISBN 9780444887733, DOIs 10.1016/B978-0-444-88773-3.50012-1 and 10.1016/B978-0-444-88773-3.50011-X | Surfaces chapter in full | Step 2 anisotropic upgrade: Lothe's own account of image theory | Library e-book or interlibrary loan | META (Crossref chapter records) |
| SHOULD | P. Segall, *Earthquake and Volcano Deformation* (Princeton University Press 2010), DOI 10.1515/9781400833856: ch. 2 "Dislocation Models of Strike-Slip Faults", pp. 32-50; ch. 3 "Dip-Slip Faults and Dislocations in Three Dimensions", pp. 51-91 | Ch. 2-3 | Step 2: an independent check of the closed-form surface displacements u_n and u_3 in SM18 / `buried_defects.md` §1. SM18 notes that this geophysics literature was never read. INFERENCE from the chapter titles that they contain the half-space formulas. | Library e-book (De Gruyter; bot-check here) | META |
| SHOULD | J. R. Willis, S. C. Jain, R. Bullough, "The energy of an array of dislocations: Implications for strain relaxation in semiconductor heterostructures", *Phil. Mag. A* 62(1), 115-129 (1990), DOI 10.1080/01418619008244339; follow-up *Phil. Mag. A* 64(3), 629-640 (1991), DOI 10.1080/01418619108204865 | Whole paper | Step 2: periodic arrays of dislocations near a free surface (INFERENCE from the title). A check of the ±20 periodic-image sum. | Library journal | META |
| OPTIONAL | D. J. Bacon, D. M. Barnett, R. O. Scattergood, *Prog. Mater. Sci.* 23, 51-262 (1980), DOI 10.1016/0079-6425(80)90007-9. A. N. Stroh, *Phil. Mag.* 3(30), 625-646 (1958), DOI 10.1080/14786435808565804. D. M. Barnett, J. Lothe, *J. Phys. F* 4(10), 1618-1635 (1974), DOI 10.1088/0305-4608/4/10/010 (Semantic Scholar flags a free copy at IOP, which gave a bot-check here). E. H. Yoffe, "A dislocation at a free surface", *Phil. Mag.* 6(69), 1147-1155 (1961), DOI 10.1080/14786436108239675, and J. D. Eshelby, A. N. Stroh, *Phil. Mag.* 42, 1401-1405 (1951), DOI 10.1080/14786445108560958 (emerging lines, Osakabe's geometry). T. J. Gosling, J. R. Willis, *J. Mech. Phys. Solids* 42(8), 1199-1221 (1994), DOI 10.1016/0022-5096(94)90032-9 (an arbitrary dislocation in an isotropic half-space, for inclined lines). A. Yu. Belov, "Dislocations Emerging at Planar Boundaries", pp. 391-446 of the Indenbom-Lothe volume, DOI 10.1016/B978-0-444-88773-3.50013-3. L. B. Freund, S. Suresh, *Thin Film Materials* (CUP 2004), DOI 10.1017/CBO9780511754715, ch. 6 "Dislocation formation in epitaxial systems", pp. 387-463, and ch. 7, pp. 464-549. R. Bonnet, *Acta Metall.* 29, 437-445 (1981), DOI 10.1016/0001-6160(81)90169-3. | As needed | Anisotropic theory, and emerging or inclined lines (not implemented; `buried_defects.md` §5) | Library | META; Freund-Suresh chapter numbers TOC READ |

## 5. Dislocations in silicon: 60° glide dislocations, dissociation, Lomer dislocations, misfit networks, elastic constants

| Pri. | Citation | What to read | Why (pipeline step) | Access route | Verified |
|---|---|---|---|---|---|
| **MUST** | Yu. B. Bolkhovityanov, O. P. Pchelyakov, S. I. Chikichev, "Silicon-germanium epilayers: physical fundamentals of growing strained and fully relaxed heterostructures", *Phys. Usp.* 44(7), 655-680 (2001), DOI 10.1070/PU2001v044n07ABEH000879 | The opening of section 2, on misfit-dislocation (MD) types, before §2.2 "Critical thickness". Skim §2.2-2.6. | Configs and step 6. It grounds the repository's two defect cases, the 60° and Lomer dislocations at Si(001), and the g·b = 0 extinction of Lomer dislocations (the analogue of the pipeline's zero-fringe Lomer case). | **Open**: https://ufn.ru/ufn01/ufn01_7/ufn017a.pdf (opened; the journal page permits individual use by students) | META; TEXT READ (quotations in section 7) |
| SHOULD | J. Hornstra, "Dislocations in the diamond lattice", *J. Phys. Chem. Solids* 5(1-2), 129-141 (1958), DOI 10.1016/0022-3697(58)90138-0 | Whole paper | Steps 1-2: dislocation types in the diamond structure (INFERENCE from the title) | Library journal | META |
| SHOULD | R. Hull, J. C. Bean, "Misfit dislocations in lattice-mismatched epitaxial films", *Crit. Rev. Solid State Mater. Sci.* 17(6), 507-546 (1992), DOI 10.1080/10408439208244585 | Sections on 60° misfit dislocation geometry | Defect choice and realistic depths | Library journal | META |
| SHOULD | I. L. F. Ray, D. J. H. Cockayne, "The dissociation of dislocations in silicon", *Proc. R. Soc. A* 325(1563), 543-554 (1971), DOI 10.1098/rspa.1971.0184 | Whole paper | Grounds the README limitation "dislocations are perfect, not dissociated": partial separation sets when that matters | Library journal | META |
| SHOULD | P. B. Hirsch, "Dislocations in semiconductors", *Mater. Sci. Technol.* 1(9), 666-677 (1985). Crossref holds two DOIs: 10.1179/mst.1985.1.9.666 and 10.1179/026708385790124242. | Whole review | Core structure, glide and shuffle sets, partials | Library journal | META |
| SHOULD | M. A. Hopcroft, W. D. Nix, T. W. Kenny, "What is the Young's Modulus of Silicon?", *J. Microelectromech. Syst.* 19(2), 229-238 (2010), DOI 10.1109/JMEMS.2009.2039697 | Sec. IV-VII, Eqs. (7)-(8), p. 233 | Step 2 anisotropic upgrade: C11, C12, C44 of Si. Eq. (8) is given in the wafer frame [110], [1-10], [001]; that is the slab frame with relabelled axes (the bar is lost in the text layer, so the sign is inferred). | **Open author copy**: http://mems.stanford.edu/~hopcroft/Publications/Hopcroft_Youngs_Modulus_Silicon.pdf (opened) | META; TEXT READ |
| OPTIONAL | H. Alexander, P. Haasen, "Dislocations and Plastic Flow in the Diamond Structure", *Solid State Physics* (Academic Press 1969), pp. 27-158, DOI 10.1016/S0081-1947(08)60031-4 (volume not in the record). J. W. Matthews, A. E. Blakeslee, *J. Cryst. Growth* 27, 118-125 (1974), DOI 10.1016/S0022-0248(74)80055-2. L. B. Freund, "The Mechanics of Dislocations in Strained-Layer Semiconductor Materials", *Adv. Appl. Mech.* (1993), pp. 1-66, DOI 10.1016/S0065-2156(08)70173-X. S. C. Jain, A. H. Harker, R. A. Cowley, *Phil. Mag. A* 75(6), 1461-1515 (1997), DOI 10.1080/01418619708223740. Yu. B. Bolkhovityanov, A. S. Deryabin, A. K. Gutakovskii, L. V. Sokolov, "Edge misfit dislocations in the GeSi/Si(001) pair: Conditions and specific features of high-quantity generation", *J. Cryst. Growth* 338(1), 12-15 (2012), DOI 10.1016/j.jcrysgro.2011.10.005. M. S. Duesbery, *Phil. Mag. Lett.* 74(4), 253-258 (1996), DOI 10.1080/095008396180191. J. F. Justo et al., *Phys. Rev. B* 58, 2539-2550 (1998), DOI 10.1103/PhysRevB.58.2539 (the EDIP potential, if a relaxed core is ever needed; `buried_defects.md` §8). | As needed | Background, critical thickness, Lomer generation, cores | Library | META |

## 6. Download first (in this order; one afternoon)

1. **Dunin-Borkowski et al. 2019, Springer Handbook ch. 16.** Open author copy:
   https://rafaldb.com/papers/B-2019-Science-of-Microscopy-Electron-holography.pdf. Read §16.1 and
   Eq. (16.10).
2. **Bolkhovityanov, Pchelyakov, Chikichev 2001, Phys. Usp. 44, 655.** Open:
   https://ufn.ru/ufn01/ufn01_7/ufn017a.pdf. Read the section 2 passage on 60° and Lomer
   misfit dislocations.
3. **Osakabe et al., PRL 62, 2969 (1989), and its erratum, PRL 63, 584 (1989).**
   * DOIs: 10.1103/PhysRevLett.62.2969 and 10.1103/PhysRevLett.63.584.3.
   * Route: library journal (APS).
4. **Osakabe et al., Ultramicroscopy 48, 483 (1993).**
   * DOI: 10.1016/0304-3991(93)90124-G.
   * While in that issue, also take Banzhof and Herrmann, 48, 475, DOI 10.1016/0304-3991(93)90123-F.
5. **Völkl and Lehmann, ch. 6 of Introduction to Electron Holography (1999).**
   * DOI: 10.1007/978-1-4615-4817-1_6.
   * From the same e-book, also take ch. 13 (Herring and Pozzi) and ch. 15 (Lenz and Cowley).
6. **The dark-field holography pair:**
   * Hÿtch et al., Ultramicroscopy 111, 1328 (2011), DOI 10.1016/j.ultramic.2011.04.008;
   * Wang et al., Microscopy Today 33(6), 43 (2025), DOI 10.1093/mictod/qaaf097.
7. **Head, Proc. Phys. Soc. B 66, 793 (1953).** DOI 10.1088/0370-1301/66/9/309.
8. **Elasticity chapters from library e-books:**
   * Hull and Bacon, 5th ed., §4.3, §4.8, §5.1-5.6 and §6.6 (ScienceDirect);
   * Anderson, Hirth and Lothe, 3rd ed., ch. 3 and ch. 13 (Cambridge Core), plus the index
     entries "image force" and "free surface".

Next, if time allows:

* Tanji, Ito and Yada 1991 (abstract first);
* Lehmann and Lichte 2002;
* Ting 1996, ch. 5 and ch. 8;
* Balluffi, ch. 13;
* Hopcroft et al. 2010 (open).

## 7. Facts and inferences

**Facts**, each read on the page named in the appendix:

* all bibliographic fields above (Crossref);
* the chapter and section lists of the following books:
  * Völkl-Allard-Joy, Tonomura, Hull-Bacon;
  * Ting (sections and pages);
  * Balluffi, Freund-Suresh, Indenbom-Lothe, Segall;
  * Hirth-Lothe 3rd ed. (chapter level only);
* the abstracts quoted, and the absence of an Osakabe chapter in the 1995 Elsevier volume's Crossref
  deposit;
* the following quotations from Bolkhovityanov et al. 2001, read in the ufn.ru PDF text layer.
  * "There are two basic types of MD, which differ in the angle between the dislocation line and the
    direction of the Burgers vector, the angle being 60° and 90°."
  * "The 90° dislocations (Lomer dislocations, or L dislocations) are sessile dislocations. From the
    viewpoint of energy, Lomer dislocations, being edge dislocations, are more suitable for layer
    relaxation than 60° dislocations, since for the former the fraction of the introduced plastic
    strain is twice as large as for the latter."
  * "In GexSi1−x/Si(001) layers with small mismatches (<1.5%), the MDs that form the orthogonal
    network are mostly of the 60° type. When the mismatches are large (>2.3%), an orthogonal network
    of mostly short edge L dislocations is formed [1]."
  * The same text describes two-wave images from {220} planes that "illustrate the complete
    extinction of purely edge Lomer misfit dislocations when g·b = 0".
* Hopcroft et al. 2010, Eq. (7): C11 = 165.7 GPa, C12 = 63.9 GPa, C44 = 79.6 GPa.

**DERIVED_HERE:**

* From Eq. (7) of Hopcroft et al. 2010, the Zener ratio is 2C44/(C11 − C12) = 1.564, consistent with
  the README's 1.56.
* C12/(C11 + C12) = 0.278.

**Inferences, all labelled in the tables:**

* what Head 1953, Hornstra 1958, Willis et al. 1990 and Segall ch. 2-3 contain (from their titles);
* that Osakabe et al. 1993 (Ultramicroscopy 48, 483) is the full paper following PRL 1989;
* that Tanji et al. 1991 may be profile (transmission) holography and not reflection holography;
* that Hirth-Lothe ch. 11 covers diamond-cubic partials;
* that Hull-Bacon §5.6 covers the Lomer-Cottrell lock;
* which pipeline step each item grounds.

**Not verified:**

* the location of the free-surface and image-force material in Hirth-Lothe (either edition);
* the chapter numbering of the Hirth-Lothe 2nd edition;
* the section numbers of Lichte and Lehmann 2008;
* the content of every paywalled paper.

## 8. Documents to request from Ali (paywalled or blocked here)

Request in this order; all are MUST items unless marked otherwise.

1. PRL 62, 2969 (1989) and its erratum, PRL 63, 584 (1989).
2. Ultramicroscopy 48, 483-488 and 475-481 (1993).
3. Hÿtch et al., Ultramicroscopy 111, 1328 (2011).
4. Wang et al., Microscopy Today 33(6), 43 (2025).
5. Head, Proc. Phys. Soc. B 66, 793 (1953).
6. Völkl and Lehmann, ch. 6 of Völkl, Allard and Joy (1999), plus ch. 13 and 15.
7. Hull and Bacon, 5th ed., ch. 4-6.
8. Hirth-Lothe: ch. 3 and 13 of the 3rd ed. (or the 2nd ed.), plus its table of contents and index
   pages, so that the free-surface chapter can be located.
9. SHOULD items:
   * Tanji, Ito and Yada 1991;
   * Lehmann and Lichte 2002;
   * Ting 1996, ch. 5 and ch. 8;
   * Balluffi, ch. 13.

---

## Appendix: verification log (what was opened, and where)

**Access in this session:**

* **Reachable:**
  * api.crossref.org (works, bibliographic queries and chapter records by ISBN);
  * link.springer.com (book and chapter pages);
  * www.cambridge.org (chapter pages; the Hirth-Lothe 3rd-ed. book page returned HTTP 500);
  * shop.elsevier.com;
  * openlibrary.org (intermittent connection resets);
  * archive.org metadata (the Hirth-Lothe 1967 scan is access-restricted and was not opened);
  * eutils.ncbi.nlm.nih.gov;
  * api.semanticscholar.org (abstracts elided by the publisher);
  * ufn.ru;
  * prometeus.nsc.ru;
  * rafaldb.com;
  * mems.stanford.edu;
  * kinokuniya.co.jp.
* **Blocked:**
  * academic.oup.com (Cloudflare challenge);
  * iopscience.iop.org (Radware bot-check);
  * degruyter.com (HTTP 202, empty);
  * research.birmingham.ac.uk (403);
  * lccn.loc.gov MARC (404);
  * oeaw.ac.at (challenge).

APS, ScienceDirect and Wiley were not retried; earlier reports record them as blocked. A
proxy-status check was refused by the permission system, so it was not run. Unpaywall was not used,
because it needs an e-mail address in every call.

**Crossref records read in this session** (api.crossref.org/works/{DOI} or query.bibliographic). All
DOIs in sections 1-5 come from these records, except the following:

* Herring, Proc. EMSA 53 (cited only by reference to `reflection_holography.md`);
* the Cambridge Core chapter DOI 10.1017/9780511977732.015, read on its chapter page. Crossref
  returned no record for the book DOI stem, so no book DOI is given.

**Notable record details:**

* Javon et al. 2014: the author list is truncated at six names in my query output.
* Matthews and Blakeslee 1974: Crossref has a duplicate single-author record,
  10.1016/0022-0248(74)90424-2; use the two-author record.
* Hirsch 1985: two DOIs.
* Lichte and Lehmann, Rep. Prog. Phys. 71, 016102: Crossref date 2008-01-01.
* Harada, Microscopy 70(1), 3-16: Crossref issued date 2020-06-26 (online).

**Tables of contents read:**

* Völkl, Allard and Joy (eds.) 1999:
  * Crossref ISBN 9781461548171;
  * https://link.springer.com/book/10.1007/978-1-4615-4817-1;
  * abstracts of ch. 3 and 13 read on their Springer chapter pages.
* Tonomura, 2nd ed.:
  * Crossref ISBN 9783540372042;
  * https://link.springer.com/chapter/10.1007/978-3-540-37204-2_7 (abstract, and a reference list of
    69 entries, of which ref. 12 is PRL 62, 2969);
  * abstracts of ch. 3 and 5 on Springer.
* Elsevier 1995 workshop volume: Crossref ISBN 9780444820518, 38 records.
* Hull and Bacon, 5th ed.:
  * Crossref ISBN 9780080966724 (chapter pages);
  * https://shop.elsevier.com/books/introduction-to-dislocations/hull/978-0-08-096672-4 (sections).
* Ting 1996:
  * Crossref ISBN 9780195074475 (15 chapter titles, no numbers);
  * https://prometeus.nsc.ru/acquisitions/10-11-23/cont60f.ssi (section-level contents with pages;
    chapter 8 runs pp. 243-315 and chapter 9 starts at p. 316).
* Freund and Suresh 2004: Crossref ISBN 9780521822817, and https://doi.org/10.1017/cbo9780511754715.007
  (the Cambridge chapter page with numbering and the ch. 6 summary).
* Balluffi:
  * Crossref (CUP container query; World Scientific ISBN 9789814749718);
  * https://doi.org/10.1017/cbo9780511998379.015 (Cambridge page with chapter numbers).
* Indenbom and Lothe (eds.) 1992: Crossref ISBN 9780444887733.
* Segall 2010: Crossref container query (chapter titles and pages).
* Hirth and Lothe:
  * Open Library OL4269829M (2nd ed. Wiley 1982, ISBN 0471091251, 857 pp., LCCN 81015939);
  * OL27408351M (3rd ed. CUP, ISBN 0521864364 / 9780521864367, 718 pp., LCCN 2016024204);
  * work record OL4089240W (lists ISBN 0894646176);
  * https://www.kinokuniya.co.jp/f/dsg-12-EY00156116 (3rd-ed. chapter list, 23 chapters in four
    parts);
  * https://www.cambridge.org/core/books/abs/theory-of-dislocations/dislocations-in-ionic-crystals/F0CC3EAB4D46D924B5635D33698169BA
    (ch. 12, pp. 313-330, DOI 10.1017/9780511977732.015; the "Book contents" panel showed "Coming
    soon").

**Abstracts read:**

* PubMed efetch, PMIDs 21864773 (Hÿtch 2011) and 24012934 (Lubk 2014).
* Crossref deposits: Wang 2025 (Microscopy Today) and Lehmann-Lichte 2002 (the abstract was in the
  deposit).
* The Semantic Scholar batch endpoint returned no abstracts ("elided by the publisher"). It flagged
  open copies for Barnett-Lothe 1974 (IOP, bot-check) and Hopcroft 2010 (opened).
* Semantic Scholar's citation list for Tanji 1991 contains one entry, "Observation of atomic surface
  potential by electron holography" (1993). The Crossref match is Ultramicroscopy 49, 259-264,
  DOI 10.1016/0304-3991(93)90232-M.

**Full texts read:**

* Hopcroft et al. 2010 (open PDF; text layer via a stdlib parser; Eqs. (7)-(8), p. 233).
* Bolkhovityanov et al. 2001 (https://ufn.ru/ufn01/ufn01_7/ufn017a.pdf; text layer; the misfit
  dislocation passage). Section numbers from the PDF stream order are unreliable, so the passage is
  located as "before §2.2".
* Dunin-Borkowski et al. 2019 (rafaldb.com PDF; section headings 16.1-16.7 only; equations not
  recoverable from the text layer).

**Consequences for `references.bib`** (the orchestrator must apply them; this file did not edit the
bib):

* P03: DOI confirmed by Crossref.
* P15: DOI 10.1103/RevModPhys.59.639.
* P31: DOI 10.1016/j.ultramic.2011.04.008.
* P32: DOI 10.1016/j.ultramic.2013.07.007.
* U07: authors R. A. Herring and G. Pozzi, pp. 295-310, DOI 10.1007/978-1-4615-4817-1_13.
* U06: not in the Crossref deposit of the 1995 volume.
* U08: Javon et al., Ultramicroscopy 147, 70-85, DOI 10.1016/j.ultramic.2014.06.005.
* P08/P09: Crossref container title is *Microscopy Research and Technique*, 20(4), issued 1992-02-15.
