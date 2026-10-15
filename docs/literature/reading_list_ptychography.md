# Reading list: ptychography for a reflection-mode (RHEED-geometry) electron ptychography engine

Status: 2026-10-15, literature-researcher agent, revision 1. Every DOI below was checked against its
Crossref record in this session; nothing here was copied from memory. The raw verification results and
reading notes are in the "Working log" at the end of this file.

Target engine: simulate scanned-probe diffraction patterns of a crystal surface at grazing incidence
(200 keV, lambda = 0.0251 A, glancing angle about 1 deg; 16.93 mrad for Si (008) in this repository)
with the repository's grazing-incidence multislice (`reflection_holo/forward/multislice.py`), then
reconstruct the surface / near-surface object.

## Three-line summary

1. Twelve MUST items cover four areas: the Rodenburg-Maiden review chapter (free accepted manuscript); the ePIE, maximum-likelihood and LSQ-ML
   algorithms; multislice and inverse-dynamical ptychography (3PIE, Chen 2021, Van den Broek and Koch 2013, PtyRAD); and the uniqueness
   condition for non-overlapping Bragg disks (Ribet 2026).
2. Reflection precedent exists only for X-rays and EUV: Besley et al. 2025 (arXiv, code PyGRAPES) is the one ptychographic
   reconstruction with a grazing-incidence multislice model. Zhu et al. 2015 (Pt(111) steps on the crystal truncation rod) is the
   closest surface-step analogue, and it is kinematic.
3. No peer-reviewed electron reflection (RHEED-geometry) ptychography was found. The nearest are an ASML patent application for
   LEED-energy (1-100 eV) reflection ptychography and a 2025 4D-RHEED-in-SEM conference abstract with no phase retrieval stated.
   This is the niche, with the caveat that the citation-graph search could not be run (OpenAlex and Semantic Scholar returned HTTP 429).

## Download first (in this order; at most 10)

| # | Item | Route |
|---|---|---|
| 1 | Rodenburg and Maiden 2019, "Ptychography", Springer Handbook of Microscopy, pp. 819-904 (T1-1) | open accepted manuscript https://eprints.whiterose.ac.uk/127795/ |
| 2 | Besley et al. 2025, arXiv:2510.06877, plus the PyGRAPES repository (T3-1) | https://arxiv.org/abs/2510.06877 ; https://github.com/lsbesley/pygrapes |
| 3 | Maiden and Rodenburg 2009, ePIE, Ultramicroscopy 109, 1256 (T1-2) | library journal (ScienceDirect) |
| 4 | Thibault and Guizar-Sicairos 2012, New J. Phys. 14, 063004 (T1-3) | open, IOPscience |
| 5 | Maiden, Humphry and Rodenburg 2012, JOSA A 29, 1606 (T2-1) | library journal (Optica Publishing Group) |
| 6 | Van den Broek and Koch 2013, PRB 87, 184108 (T2-3) | library journal (APS) |
| 7 | Chen et al. 2021, Science 372, 826, arXiv:2101.00465 (T2-2) | arXiv now; Science version and supplement via library |
| 8 | Zhu et al. 2015, APL 106, 101604 (T3-2) | open full text, PSI DORA https://www.dora.lib4ri.ch/psi/dload/psi:7274/PDF/view |
| 9 | Lee et al. 2025, PtyRAD, Microsc. Microanal. 31, ozaf070, arXiv:2505.07814, plus the repository (T2-4) | arXiv; https://github.com/chiahao3/ptyrad |
| 10 | Odstrcil, Menzel and Guizar-Sicairos 2018, Opt. Express 26, 3108 (T1-4) | open-access journal (Optica) |

The two remaining MUST items are open access and take a minute each, so fetch them in the same
session: Chen et al. 2020, Nat. Commun. 11, 2994 (T4-1), and Ribet et al. 2026, arXiv:2608.30359 (T1-5).

## Evidence labels used here

* METADATA_VERIFIED: authors, title, journal, volume, issue, pages or article number, year and DOI
  matched the Crossref record fetched in this session (api.crossref.org/works/<DOI>, or the record
  returned by a Crossref bibliographic search, marked "(search record)").
* +ABSTRACT(source): the abstract was read on the named page or API record in this session (PubMed,
  arXiv, Crossref, OpenAlex, Semantic Scholar). These are publisher abstracts, not search summaries.
* SECTION_READ: the named sections were read in this session in the version named (arXiv version,
  accepted manuscript or publisher HTML). Locators are given in the "What to read" column and in the
  log.
* UNVERIFIED: not checked; do not cite as is.

Column "Why" codes: FM = forward model; ALG = reconstruction algorithm; SAMP = sampling / overlap /
uniqueness condition; REFL = reflection or grazing geometry; SW = software benchmark; PRAC = electron
practice (dose, detector, coherence, probe modes).

## Topic 1: ptychography fundamentals, algorithms, convergence and uniqueness conditions

| ID | Priority | Citation | What to read | Why | Access route | Verified |
|---|---|---|---|---|---|---|
| T1-1 | MUST | Rodenburg, J. M. and Maiden, A. M. (2019). Ptychography. In P. W. Hawkes and J. C. H. Spence (eds), *Springer Handbook of Microscopy*, pp. 819-904. Springer. DOI 10.1007/978-3-030-00069-1_17. ISBN 978-3-030-00068-4 (print), 978-3-030-00069-1 (e-book). | Accepted-manuscript numbering: Sec. 3.3-3.5 (the algorithm, an example update, a survey of algorithms); Sec. 4 (sampling and artefacts: 4.1 probe recovery, 4.2 "pathological instances", 4.3 non-periodic scan, 4.4 refining positions, 4.7 shot noise); Sec. 5.7 Bragg, 5.8 visible reflective, 5.9 EUV reflection; Sec. 6.2 multi-slice reconstruction; Sec. 8 mixed states (8.3 electron modes); Sec. 9.1-9.4 PIE family, projection methods, implementation, comparison. Skip Sec. 10 (WDD) at first. | FM, ALG, SAMP, REFL. The single best overview. Sec. 6.2 states that the multislice reconstruction is forward-only and that "forward-only scattering is a good approximation for the behaviour of high-energy electrons and X-rays". Sec. 5.9 warns that for glancing-angle reflection "care must be taken to map the detector coordinates to the scattering configuration and the elongated probe shape and phase". | Open accepted manuscript (White Rose, opened, 138 pp.); final version via library e-book. | METADATA_VERIFIED; SECTION_READ (full heading list; Secs. 5.7-5.9 and 6.2 read). Whether the published chapter keeps the same section numbering is UNVERIFIED. |
| T1-2 | MUST | Maiden, A. M. and Rodenburg, J. M. (2009). An improved ptychographical phase retrieval algorithm for diffractive imaging. *Ultramicroscopy* 109(10), 1256-1262. DOI 10.1016/j.ultramic.2009.05.012. | Whole paper (7 pp.): the ePIE object and probe update equations and the step parameters. | ALG. The simplest engine to implement first and the baseline every code compares against. Its update assumes a multiplicative object; do not transplant it into the dynamical reflection model without deriving the matching gradient (instruction-file warning; reading plan P06). | Library journal (ScienceDirect blocked here). | METADATA_VERIFIED +ABSTRACT(PubMed 19541420). |
| T1-3 | MUST | Thibault, P. and Guizar-Sicairos, M. (2012). Maximum-likelihood refinement for coherent diffractive imaging. *New J. Phys.* 14, 063004. DOI 10.1088/1367-2630/14/6/063004. | Sec. 2 (Poisson likelihood Eq. 4, probe and object gradients Eqs. 5-6, Gaussian Eq. 8, amplitude model Eq. 11); Sec. 3.1-3.2 (preconditioning, regularisation); Sec. 5.1 (difference map first, then ML refinement). | ALG. Gives the loss functions and gradient bookkeeping that any gradient or automatic-differentiation (AD) engine needs. PtyRAD's Gaussian and Poisson losses follow this paper. | Open (IOPscience "Free article", opened). | METADATA_VERIFIED; SECTION_READ (headings and equation map; the equations are images and were not transcribed). |
| T1-4 | MUST | Odstrčil, M., Menzel, A. and Guizar-Sicairos, M. (2018). Iterative least-squares solver for generalized maximum-likelihood ptychography. *Opt. Express* 26(3), 3108. DOI 10.1364/OE.26.003108. | The LSQ-ML method part: update directions, analytic step size, position and probe-variation refinement. Section numbers not verified. | ALG. The engine behind fold_slice's multislice GPU_MS used in Chen 2020 and Chen 2021. Its closed-form step size is a cheaper alternative to Adam when each forward pass is a long grazing multislice. | Open-access journal (Optica); its pages return a JavaScript challenge here, so it was not opened. The student can download it normally. | METADATA_VERIFIED +ABSTRACT(Semantic Scholar record). |
| T1-5 | MUST | Ribet, S. M., Danaie, M., de Kleijne, W. P. M., McCray, A. R. C., Allars, F., Allen, C. S., Ophus, C. and Varnavides, G. (2026). Real-space overlap is not enough: ambiguity in nanobeam iterative ptychography. arXiv:2608.30359 (preprint, not peer reviewed). | Abstract; end of Sec. 1; Sec. 3.2 "Origin of the ambiguity"; Fig. 5; Sec. 5. | SAMP. When no diffracted disks overlap (2 alpha < lambda abs(g)), the data fix only the moduli of the reflections. The reconstruction is then degenerate (rigid lattice shifts, contrast reversal), and "Real-space overlap ... does not lift this degeneracy". This decides what a reflection engine can reconstruct (see Inference 4). | Open arXiv (opened). | SECTION_READ (arXiv v1). |
| T1-6 | SHOULD | Thibault, P., Dierolf, M., Menzel, A., Bunk, O., David, C. and Pfeiffer, F. (2008). High-resolution scanning X-ray diffraction microscopy. *Science* 321(5887), 379-382. DOI 10.1126/science.1158573. | Whole (4 pp.) plus the supplement: difference map, simultaneous probe retrieval, scan pattern. | ALG, SAMP. Canonical scanning ptychography; the difference map is the usual initialiser before ML (T1-3, Sec. 5.1). | Library journal (science.org blocked here). Semantic Scholar points to EPFL Infoscience record 125719 (not opened). | METADATA_VERIFIED +ABSTRACT(PubMed 18635796). |
| T1-7 | SHOULD | Maiden, A., Johnson, D. and Li, P. (2017). Further improvements to the ptychographical iterative engine. *Optica* 4(7), 736. DOI 10.1364/OPTICA.4.000736. | rPIE and mPIE update rules. | ALG. Abstract: "an order of magnitude speed increase", and it handles data sets where the original version fails. | Open-access journal (Optica; blocked here). | METADATA_VERIFIED +ABSTRACT(OpenAlex). |
| T1-8 | SHOULD | Bunk, O., Dierolf, M., Kynde, S., Johnson, I., Marti, O. and Pfeiffer, F. (2008). Influence of the overlap parameter on the convergence of the ptychographical iterative engine. *Ultramicroscopy* 108(5), 481-487. DOI 10.1016/j.ultramic.2007.08.003. | Sec. 2, Eq. 4 (overlap o = 1 - a/2r); Sec. 3 results (accepted-manuscript PDF pp. 12-13). | SAMP. "About 85 %" overlap is optimal; "60 %" is adequate; do not exceed 85 %; overlap along one dimension is sufficient. | Open accepted manuscript, PSI DORA psi:18937 (opened). | METADATA_VERIFIED; SECTION_READ. |
| T1-9 | SHOULD | Edo, T. B., Batey, D. J., Maiden, A. M., Rau, C., Wagner, U., Pešić, Z. D., Waigh, T. A. and Rodenburg, J. M. (2013). Sampling in x-ray ptychography. *Phys. Rev. A* 87, 053850. DOI 10.1103/PhysRevA.87.053850. | Whole. | SAMP. Abstract: "the sampling requirement in ptychography is independent of illumination size". This sets the detector-sampling rule for the very long reflection footprint. | Library journal (APS blocked here). | METADATA_VERIFIED +ABSTRACT(OpenAlex). |
| T1-10 | SHOULD | Thibault, P. and Menzel, A. (2013). Reconstructing state mixtures from diffraction measurements. *Nature* 494, 68-71. DOI 10.1038/nature11806. | Whole plus Methods. | ALG, PRAC. The mixed-state (modal) formalism that every electron code uses for partial coherence. | Library journal. | METADATA_VERIFIED +ABSTRACT(PubMed 23389541). |
| T1-11 | SHOULD | Wang, R., Zhao, Q., Loetgering, L., Allars, F., Hong, Z., Pennycook, T. J., Horstmeyer, R., Rodenburg, J., Maiden, A. and Zheng, G. (2025). Ptychography at all wavelengths. *Nat. Rev. Methods Primers* 5, 68. DOI 10.1038/s43586-025-00438-3. | Sec. 2.1 (configurations, including Bragg and reflection), 2.2 (Table 1, gradient-based reconstruction; system calibration), 3.4 (electron), 5 (reproducibility, software), 6 (limitations). | ALG, SW, REFL. The current cross-wavelength review, with data and code. It completes the author list that is truncated in references.bib P41. | Open author manuscript PMC13024499 (opened). | METADATA_VERIFIED; SECTION_READ (headings and quoted sentences). |
| T1-12 | OPTIONAL | Rodenburg, J. M. (2008). Ptychography and related diffractive imaging methods. *Adv. Imaging Electron Phys.* 150, 87-184. DOI 10.1016/S1076-5670(07)00003-1. ISBN 978-0-12-374217-9. | History and theory, if T1-1 is not enough. | ALG. Superseded by T1-1. | Library e-book. | METADATA_VERIFIED. |
| T1-13 | OPTIONAL | Rodenburg, J. M. and Faulkner, H. M. L. (2004). A phase retrieval algorithm for shifting illumination. *Appl. Phys. Lett.* 85(20), 4795-4797. DOI 10.1063/1.1823034. Also Faulkner, H. M. L. and Rodenburg, J. M. (2004), *Phys. Rev. Lett.* 93, 023903, DOI 10.1103/PhysRevLett.93.023903. | Original PIE. | ALG (history). | Library journal. | METADATA_VERIFIED (both). |
| T1-14 | OPTIONAL | Thibault, P., Dierolf, M., Bunk, O., Menzel, A. and Pfeiffer, F. (2009). Probe retrieval in ptychographic coherent diffractive imaging. *Ultramicroscopy* 109(4), 338-343. DOI 10.1016/j.ultramic.2008.12.011. | Probe-retrieval section. | ALG. | Library journal. | METADATA_VERIFIED. |
| T1-15 | OPTIONAL | Guizar-Sicairos, M. and Fienup, J. R. (2008). Phase retrieval with transverse translation diversity: a nonlinear optimization approach. *Opt. Express* 16(10), 7264. DOI 10.1364/OE.16.007264. | Gradient expressions, including position refinement. | ALG. The first gradient-based formulation. | Open-access journal. | METADATA_VERIFIED. |
| T1-16 | OPTIONAL | Maiden, A. M., Humphry, M. J., Sarahan, M. C., Kraus, B. and Rodenburg, J. M. (2012). An annealing algorithm to correct positioning errors in ptychography. *Ultramicroscopy* 120, 64-72. DOI 10.1016/j.ultramic.2012.06.001. Also Zhang, F. et al. (2013), *Opt. Express* 21(11), 13592, DOI 10.1364/OE.21.013592. | Position-correction algorithms. | ALG, PRAC. Abstract: corrects errors "tens of times larger than the pixel size"; the electron scan-coil case. | Library / open. | METADATA_VERIFIED +ABSTRACT(PubMed 22813888) for Maiden; METADATA_VERIFIED for Zhang. |
| T1-17 | OPTIONAL | da Silva, J. C. and Menzel, A. (2015). Elementary signals in ptychography. *Opt. Express* 23(26), 33812. DOI 10.1364/OE.23.033812. | Derivation of the sampling requirements. | SAMP. | Open-access journal. | METADATA_VERIFIED +ABSTRACT(OpenAlex). |
| T1-18 | OPTIONAL | Fannjiang, A. and Chen, P. (2020). Blind ptychography: uniqueness and ambiguities. *Inverse Problems* 36(4), 045005. DOI 10.1088/1361-6420/ab6504. | Uniqueness theorems and raster-scan ambiguities. | SAMP (mathematics). | Library journal. | METADATA_VERIFIED. |
| T1-19 | OPTIONAL | Godard, P., Allain, M., Chamard, V. and Rodenburg, J. (2012). Noise models for low counting rate coherent diffraction imaging. *Opt. Express* 20(23), 25914. DOI 10.1364/OE.20.025914. Li, P., Edo, T., Batey, D., Rodenburg, J. and Maiden, A. (2016). Breaking ambiguities in mixed state ptychography. *Opt. Express* 24(8), 9038. DOI 10.1364/OE.24.009038. Odstrcil, M. et al. (2016). Ptychographic coherent diffractive imaging with orthogonal probe relaxation. *Opt. Express* 24(8), 8360. DOI 10.1364/OE.24.008360. | As needed. | ALG, PRAC. | Open-access journals. | METADATA_VERIFIED (all three). |
| T1-20 | OPTIONAL | Short reviews: Pfeiffer, F. (2018). X-ray ptychography. *Nat. Photon.* 12, 9-17, DOI 10.1038/s41566-017-0072-5. Guizar-Sicairos, M. and Thibault, P. (2021). Ptychography: a solution to the phase problem. *Physics Today* 74(9), 42-48, DOI 10.1063/PT.3.4835. Loetgering, L. et al. (2023). PtyLab.m/py/jl. *Opt. Express* 31(9), 13763, DOI 10.1364/OE.485370. | Orientation reading. | ALG, SW. | Library / open. | METADATA_VERIFIED (all three). |

## Topic 2: multislice and thick-sample ptychography, gradient / AD reconstruction, open codes

| ID | Priority | Citation | What to read | Why | Access route | Verified |
|---|---|---|---|---|---|---|
| T2-1 | MUST | Maiden, A. M., Humphry, M. J. and Rodenburg, J. M. (2012). Ptychographic transmission microscopy in three dimensions using a multi-slice approach. *J. Opt. Soc. Am. A* 29(8), 1606-1614. DOI 10.1364/JOSAA.29.001606. | Whole: the multislice forward model and the layer-by-layer update with back-propagation (summarised in T1-1, Sec. 6.2, Fig. 52). | FM, ALG. The first multislice ptychography (3PIE). It is the hand-derived template for updating slices, the alternative to AD. Abstract: recovers images "in the presence of multiple scattering and when the projection approximation is not applicable". | Library journal. | METADATA_VERIFIED +ABSTRACT(PubMed 23201876). Crossref gives first page 1606; the range 1606-1614 is from the reference list of T2-2, read. |
| T2-2 | MUST | Chen, Z., Jiang, Y., Shao, Y.-T., Holtz, M. E., Odstrčil, M., Guizar-Sicairos, M., Hanke, I., Ganschow, S., Schlom, D. G. and Muller, D. A. (2021). Electron ptychography achieves atomic-resolution limits set by lattice vibrations. *Science* 372(6544), 826-831. DOI 10.1126/science.abg2533. arXiv:2101.00465. | Main text; Materials and Methods (arXiv PDF pp. 15-18: experimental conditions, reconstruction algorithms, slice-thickness tests, scan step, computing cost); Figs. S5-S10. | FM, ALG, PRAC. The reference electron multislice ptychography: mixed-state probe (12 modes), 42 slices of 0.5 nm, LSQ-ML, inter-slice regularisation. It gives the multiplicative-approximation limit "T < 1.3 lambda / theta_max^2" and a cost of about 45 min per iteration on one GPU. | arXiv open (opened); Science version via library. | METADATA_VERIFIED; SECTION_READ (arXiv v1). |
| T2-3 | MUST | Van den Broek, W. and Koch, C. T. (2013). General framework for quantitative three-dimensional reconstruction from arbitrary detection geometries in TEM. *Phys. Rev. B* 87, 184108. DOI 10.1103/PhysRevB.87.184108. | Whole: gradient of the multislice model with respect to the 3-D potential; the ptychography and confocal extensions; joint estimation of defocus. | FM, ALG. Inversion of dynamical electron scattering for "arbitrary detection geometries", the conceptual basis for inverting a grazing-incidence multislice. Abstract: "an extension to ptychography and scanning confocal electron microscopy". | Library journal (APS blocked here). | METADATA_VERIFIED +ABSTRACT(OpenAlex). |
| T2-4 | MUST | Lee, C.-H., Zeltmann, S. E., Yoon, D., Ma, D. and Muller, D. A. (2025). PtyRAD: a high-performance and flexible ptychographic reconstruction framework with automatic differentiation. *Microsc. Microanal.* 31(4), ozaf070. DOI 10.1093/mam/ozaf070. arXiv:2505.07814. | PtyRAD model section (Eqs. 3-4; Eq. 4 is the tilted multislice propagator "following equation 6.99 in Kirkland (2010)"); "Optimizers and loss functions"; the benchmarks against PtychoShelves/fold_slice and py4DSTEM. | SW, ALG, FM. The open PyTorch AD code for electron multislice ptychography: mixed probe and object states, per-position tilt, slice thickness, positions. Install with `pip install ptyrad`; licence LGPL-3.0 (README read). | arXiv open (opened); journal (OUP blocked here). | METADATA_VERIFIED; SECTION_READ (arXiv v2). Version note: v1 abstract says "17x speedup", v2 text says "24 x". |
| T2-5 | SHOULD | Van den Broek, W. and Koch, C. T. (2012). Method for retrieval of the three-dimensional object potential by inversion of dynamical electron scattering. *Phys. Rev. Lett.* 109, 245502. DOI 10.1103/PhysRevLett.109.245502. | Whole (4 pp.). Read before T2-3. | FM, ALG. Abstract: "recasting the multislice algorithm as an artificial neural network"; includes the detector MTF, partial coherence and an absorptive potential. | Library journal. | METADATA_VERIFIED +ABSTRACT(PubMed 23368342). |
| T2-6 | SHOULD | Tsai, E. H. R., Usov, I., Diaz, A., Menzel, A. and Guizar-Sicairos, M. (2016). X-ray ptychography with extended depth of field. *Opt. Express* 24(25), 29089. DOI 10.1364/OE.24.029089. | Multislice algorithm and the thickness-retrieval section. | FM, ALG, SAMP. The multislice method that fold_slice asks users to cite. Abstract: "smaller scanning steps surprisingly increase the depth of field". | Open-access journal (Optica; blocked here). | METADATA_VERIFIED +ABSTRACT(Semantic Scholar). |
| T2-7 | SHOULD | Kandel, S., Maddali, S., Allain, M., Hruszkewycz, S. O., Jacobsen, C. and Nashed, Y. S. G. (2019). Using automatic differentiation as a general framework for ptychographic reconstruction. *Opt. Express* 27(13), 18653. DOI 10.1364/OE.27.018653. | Framework and the worked forward models. | ALG. Shows how reconstruction needs only the physics forward model, which is exactly what a new reflection model requires. | Open-access journal (Optica; blocked here). | METADATA_VERIFIED +ABSTRACT(Semantic Scholar). |
| T2-8 | SHOULD | Diederichs, B., Herdegen, Z., Strauch, A., Filbir, F. and Müller-Caspary, K. (2024). Exact inversion of partially coherent dynamical electron scattering for picometric structure retrieval. *Nat. Commun.* 15, 101. DOI 10.1038/s41467-023-44268-x. | Abstract; Methods, "Details of inversion scheme"; Supplementary Notes 1-2. | FM, ALG. An atom-parametrised, fully differentiable PyTorch inversion with frozen phonons, partial coherence and a tilted Fresnel propagator. It points to reconstructing displacements (strain) instead of voxels. | Open (nature.com, opened, CC BY). | METADATA_VERIFIED; SECTION_READ. |
| T2-9 | SHOULD | Sha, H., Cui, J. and Yu, R. (2022). Deep sub-angstrom resolution imaging by electron ptychography with misorientation correction. *Sci. Adv.* 8(19), eabn2275. DOI 10.1126/sciadv.abn2275. | Method for specimen misorientation in multislice. | FM. A tilted beam relative to the slices is the normal state in grazing geometry. | Open-access journal (science.org blocked here). | METADATA_VERIFIED +ABSTRACT(Crossref). |
| T2-10 | SHOULD | Varnavides, G., Ribet, S. M., Zeltmann, S. E., Yu, Y., Savitzky, B. H., Byrne, D. O., Allen, F. I., Dravid, V. P., Scott, M. C. and Ophus, C. (2023). Iterative phase retrieval algorithms for scanning transmission electron microscopy. arXiv:2309.05250. Also Savitzky, B. H. et al. (2021). py4DSTEM. *Microsc. Microanal.* 27(4), 712-743, DOI 10.1017/S1431927621000477. | arXiv: the ptychography "Inverse Problem Formalism" and "Preprocessing and Results" (gradient descent in 2D and multislice). | SW, ALG. The py4DSTEM implementation, GPL-3.0. Its phase-retrieval modules were refactored in 0.14.9 (README read). The 2026 work by the same group runs in quantEM (MIT; README read). | arXiv open (opened); py4DSTEM paper open (Cambridge). | SECTION_READ (arXiv v2); py4DSTEM METADATA_VERIFIED +ABSTRACT(Crossref). |
| T2-11 | SHOULD | Wakonig, K., Stadler, H.-C., Odstrčil, M., Tsai, E. H. R., Diaz, A., Holler, M., Usov, I., Raabe, J., Menzel, A. and Guizar-Sicairos, M. (2020). PtychoShelves, a versatile high-level framework for high-performance analysis of ptychographic data. *J. Appl. Cryst.* 53(2), 574-586. DOI 10.1107/S1600576720001776. | Engine overview (DM, LSQ-ML). | SW. The fold_slice fork (MATLAB) holds the GPU_MS multislice engine of T2-2. README read: academic non-commercial licence; archived (read-only) on 5 Aug 2026. | Open (IUCr) / GitHub yijiang1/fold_slice. | METADATA_VERIFIED +ABSTRACT(Crossref). |
| T2-12 | SHOULD | Madsen, J. and Susi, T. (2021). The abTEM code: transmission electron microscopy from first principles. *Open Res. Europe* 1, 24. DOI 10.12688/openreseurope.13015.2 (version 1: 10.12688/openreseurope.13015.1). | Multislice and 4D-STEM simulation chapters of the paper and documentation. | SW, FM. The README describes simulation only, with no reconstruction module. Use it as the independent transmission 4D-STEM simulator to validate the engine in its transmission limit (this also serves milestone M2). GPL-3.0. | Open. | METADATA_VERIFIED +ABSTRACT(Crossref). |
| T2-13 | OPTIONAL | Gao, S. et al. (2017). Electron ptychographic microscopy for three-dimensional imaging. *Nat. Commun.* 8, 163, DOI 10.1038/s41467-017-00150-1. Godden, T. M. et al. (2014). *Opt. Express* 22(10), 12513, DOI 10.1364/OE.22.012513. Schloz, M. et al. (2020). *Opt. Express* 28(19), 28306, DOI 10.1364/OE.396925. | Early electron and optical multislice ptychography; regularised optimisation. | FM, ALG. | Open. | METADATA_VERIFIED; +ABSTRACT(Crossref) for Gao and Schloz. |
| T2-14 | OPTIONAL | Du, M. et al. (2021). Adorym. *Opt. Express* 29(7), 10000, DOI 10.1364/OE.418296 (the PyGRAPES propagator is adapted from Adorym). Wu, L. et al. (2024). Dose-efficient automatic differentiation for ptychographic reconstruction. *Optica* 11(6), 821, DOI 10.1364/OPTICA.522380. | Frameworks. | SW, ALG. | Open. | METADATA_VERIFIED +ABSTRACT(Crossref) (both). |
| T2-15 | OPTIONAL | Clark, L. et al. (2023; issue dated Feb 2023, online 20 Dec 2022). The effect of dynamical scattering on single-plane phase retrieval in electron ptychography. *Microsc. Microanal.* 29(1), 384-394, DOI 10.1093/micmic/ozac022. Denzer, B. R., Gilgenbach, C. and LeBeau, J. M. (2026). On transmission function amplitude and phase recovery in multislice electron ptychography. arXiv:2608.21007. | Breakdown of the multiplicative approximation (Clark); absorptive potential versus thermal diffuse scattering in multislice ptychography (Denzer). | FM. Denzer bears on the repository's placeholder absorption. | Open (OUP blocked here; arXiv). | METADATA_VERIFIED +ABSTRACT(Crossref) for Clark; +ABSTRACT(arXiv) for Denzer. |
| T2-16 | OPTIONAL | Enders, B. and Thibault, P. (2016). A computational framework for ptychographic reconstructions. *Proc. R. Soc. A* 472, 20160640, DOI 10.1098/rspa.2016.0640 (PtyPy). Favre-Nicolin, V. et al. (2020). PyNX. *J. Appl. Cryst.* 53(5), 1404-1413, DOI 10.1107/S1600576720010985. | Framework design. | SW. The PtyPy README carries a Phase Focus patent-licence notice (royalty-free for non-commercial academic research). | Open. | METADATA_VERIFIED; +ABSTRACT(Crossref) for PtyPy. |

## Topic 3: reflection and grazing-incidence ptychography (any radiation), and the electron search

| ID | Priority | Citation | What to read | Why | Access route | Verified |
|---|---|---|---|---|---|---|
| T3-1 | MUST | Besley, L., Jørgensen, P. S., Diaz, A., Detlefs, C., De Angelis, S., Carlsen, M., Chang, B., Silvestre, C. and Andreasen, J. W. (2025). Versatile 3D reconstruction framework for hard X-ray grazing incidence imaging of nanostructures. arXiv:2510.06877 (preprint; no journal reference on arXiv). Code: PyGRAPES. | Sec. 1 and Fig. 2 (geometry); Sec. 2.2-2.3.1 (Eqs. 6-9, Algorithm 1, optimisers, position refinement); Sec. 3.2-3.3 (projection approximation against multislice); Secs. 2.4 and 4.4 (data and hardware). | FM, ALG, REFL. The one ptychographic reconstruction found that uses a grazing-incidence multislice forward model. Its geometry matches this repository's slab frame: "aligning the optical axis parallel to the substrate surface", with the incidence angle applied "in the form of a constant phase gradient". | Open arXiv (opened via HTML; CC BY-NC-SA 4.0); PyGRAPES README read (GPL-3.0). | SECTION_READ (arXiv v1). |
| T3-2 | MUST | Zhu, C., Harder, R., Diaz, A., Komanicky, V., Barbour, A., Xu, R., Huang, X., Liu, Y., Pierce, M. S., Menzel, A. and You, H. (2015). Ptychographic x-ray imaging of surfaces on crystal truncation rod. *Appl. Phys. Lett.* 106(10), 101604. DOI 10.1063/1.4914927. | Whole (5 pp.), especially Eq. (1) and the step-phase discussion on p. 101604-4. | FM, REFL. The closest published analogue: atomic steps on Pt(111) imaged by reflection ptychography. It maps reflection onto a transmission phase object "except for the sin theta factor", then measures about 2 rad against "the expected phase steps of 3 pi/2 = 4.7 rad". | Open full text, PSI DORA psi:7274 (opened); journal (AIP blocked here). | METADATA_VERIFIED; SECTION_READ. |
| T3-3 | SHOULD | Jørgensen, P. S., Besley, L., Slyamov, A. M., Diaz, A., Guizar-Sicairos, M., Odstrčil, M., Holler, M., Silvestre, C., Chang, B., Detlefs, C. and Andreasen, J. W. (2024). Hard x-ray grazing-incidence ptychography: large field-of-view nanostructure imaging with ultra-high surface sensitivity. *Optica* 11(2), 197. DOI 10.1364/OPTICA.505478 (Crossref stores it in lower case; DOIs are case-insensitive). arXiv:2307.01735. | Methods (footprint and step scaling); Discussion (h = phi/(2k sin theta); DWBA); the multislice simulation section. | REFL, SAMP. The first hard X-ray grazing-incidence ptychography. Its reconstruction is not multislice (multislice is used only to simulate validation data). "the beam footprint is elongated in the longitudinal direction by a factor of 1/sin(theta)", so the scan step along the beam must be scaled. | Open-access journal (Optica, blocked here); arXiv (opened). | METADATA_VERIFIED; SECTION_READ (arXiv v1; the journal text may differ). |
| T3-4 | SHOULD | Seaberg, M. D., Zhang, B., Gardner, D. F., Shanblatt, E. R., Murnane, M. M., Kapteyn, H. C. and Adams, D. E. (2014). Tabletop nanometer extreme ultraviolet imaging in an extended reflection mode using coherent Fresnel ptychography. *Optica* 1(1), 39. DOI 10.1364/OPTICA.1.000039. arXiv:1312.2049. | The remapping paragraph and Methods steps 1-4. | REFL, ALG. Tilted-plane correction: patterns "must be remapped onto a grid that is linear in spatial frequencies of the sample plane". The method comes from Gardner et al. 2012 (T3-11). | Open (Optica blocked here; arXiv opened). | METADATA_VERIFIED; SECTION_READ (arXiv v1). |
| T3-5 | SHOULD | Takahashi, Y., Suzuki, A., Furutaku, S., Yamauchi, K., Kohmura, Y. and Ishikawa, T. (2013). Bragg x-ray ptychography of a silicon crystal: visualization of the dislocation strain field and the production of a vortex beam. *Phys. Rev. B* 87, 121201. DOI 10.1103/PhysRevB.87.121201. | Whole (short). | REFL, FM. Dislocation strain fields in thick silicon imaged by Bragg ptychography: the same object class as this repository. | Library journal (APS blocked here). | METADATA_VERIFIED +ABSTRACT(OpenAlex). |
| T3-6 | SHOULD | Godard, P., Carbone, G., Allain, M., Mastropietro, F., Chen, G., Capello, L., Diaz, A., Metzger, T. H., Stangl, J. and Chamard, V. (2011). Three-dimensional high-resolution quantitative microscopy of extended crystals. *Nat. Commun.* 2, 568. DOI 10.1038/ncomms1569. | Methods, "Phase retrieval" and "Data inversion". | REFL, FM, ALG. The first Bragg ptychography; the exit field is computed in the Born approximation (Eq. 1). Its DOI was missing from references.bib P35 and is now verified. | Open (nature.com, opened). | METADATA_VERIFIED; SECTION_READ (Methods). |
| T3-7 | SHOULD | Li, K., Wojcik, M. and Jacobsen, C. (2017). Multislice does it all - calculating the performance of nanofocusing X-ray optics. *Opt. Express* 25(3), 1831. DOI 10.1364/OE.25.001831. | Grazing-incidence reflectivity section. | FM, REFL. Abstract: multislice reproduces "grazing incidence reflectivity where the direction of energy flow is changed significantly". This is the X-ray precedent for the repository's multislice-in-reflection kernel, and T3-1 and T3-3 build on it. | Open-access journal. | METADATA_VERIFIED +ABSTRACT(Semantic Scholar). |
| T3-8 | OPTIONAL | Hruszkewycz, S. O. et al. (2012). Quantitative nanoscale imaging of lattice distortions in epitaxial semiconductor heterostructures using nanofocused X-ray Bragg projection ptychography. *Nano Lett.* 12(10), 5148-5154. DOI 10.1021/nl303201w. Hruszkewycz, S. O. et al. (2017). High-resolution three-dimensional structural microscopy by single-angle Bragg ptychography. *Nat. Mater.* 16(2), 244-251. DOI 10.1038/nmat4798. | Bragg projection forward model. | REFL, FM. | Library journals. | METADATA_VERIFIED (both); +ABSTRACT(PubMed 27869823) for 2017. |
| T3-9 | OPTIONAL | Godard, P., Allain, M. and Chamard, V. (2011). Imaging of highly inhomogeneous strain field in nanocrystals using x-ray Bragg ptychography: a numerical study. *Phys. Rev. B* 84, 144109. DOI 10.1103/PhysRevB.84.144109. Chamard, V. et al. (2015). *Sci. Rep.* 5, 9827. DOI 10.1038/srep09827. Suzuki, A. and Takahashi, Y. (2015). Dark-field X-ray ptychography. *Opt. Express* 23(12), 16429. DOI 10.1364/OE.23.016429. | Strain-field and dark-field variants. | REFL, SAMP. Dark-field selection is the analogue of this repository's single-reflection aperture. | Library / open. | METADATA_VERIFIED (all three). |
| T3-10 | OPTIONAL | Roy, S., Parks, D., Seu, K. A., Su, R., Turner, J. J., Chao, W., Anderson, E. H., Cabrini, S. and Kevan, S. D. (2011). Lensless X-ray imaging in reflection geometry. *Nat. Photon.* 5(4), 243-245. DOI 10.1038/nphoton.2011.11. | Whole. | REFL. Completes the truncated author list and missing pages of references.bib P34. | Library journal. | METADATA_VERIFIED. |
| T3-11 | OPTIONAL | Gardner, D. F. et al. (2012). High numerical aperture reflection mode coherent diffraction microscopy using off-axis apertured illumination. *Opt. Express* 20(17), 19050. DOI 10.1364/OE.20.019050. Tanksalvala, M. et al. (2021). Nondestructive, high-resolution, chemically specific 3D nanostructure characterization using phase-sensitive EUV imaging reflectometry. *Sci. Adv.* 7(5), eabd9667. DOI 10.1126/sciadv.abd9667 (arXiv:2404.02170). | Tilted-plane correction (Gardner); variable-angle reflection ptychography (Tanksalvala). | REFL. | Open. | METADATA_VERIFIED (both); +ABSTRACT(arXiv) for Tanksalvala. |
| T3-12 | OPTIONAL | Myint, P. et al. (2024). *APL Photonics* 9(6), 066118. DOI 10.1063/5.0204240 (arXiv:2402.06762). Guenzing, D. et al. (2026). Soft X-ray reflection ptychography. *Opt. Express* 34(16), 30230. DOI 10.1364/OE.591755. Sung, J., Gao, Y., Griffith, J., Gao, Z., Hunag [sic], X., Williams, G. and Chu, Y. S. (2025). Automatic differentiation for x-ray grazing-incidence surface imaging using ptychography. Proc. SPIE, *X-Ray Nanoimaging: Instruments and Methods VII*, paper 24. DOI 10.1117/12.3063903. | As needed. | REFL. The Sung paper is a second AD grazing-incidence engine. Its Crossref record has no abstract and no volume number; the author spelled "Hunag" in Crossref is presumably Huang (INFERENCE; check the SPIE page). | Library (SPIE, AIP); open (Optica). | METADATA_VERIFIED (all three); +ABSTRACT(arXiv) for Myint. |
| T3-13 | OPTIONAL | Electron-side nearest neighbours (none is ptychography in RHEED geometry): (a) Holm, J. (2025). 4-Dimensional reflection high energy electron diffraction on 2-dimensional materials in a scanning electron microscope. *Microsc. Microanal.* 31(Suppl. 1), ozaf048.197. DOI 10.1093/mam/ozaf048.197. (b) Ichikawa, M. and Doi, T. (1988). Microprobe reflection high-energy electron diffraction. In *Reflection High-Energy Electron Diffraction and Reflection Electron Imaging of Surfaces*, NATO ASI Series, pp. 343-369. DOI 10.1007/978-1-4684-5580-9_25. (c) ASML Netherlands BV, patent application WO2025131995A1, "LEED and ptychography based surface profile determination and inspection" (priority 2023-12-20, published 2025-06-26; family member TW202542655A). | (a) the abstract, once obtained; (b) the scanning microprobe RHEED arrangement; (c) the claims and the description of geometry and algorithms. | REFL, PRAC. (a) is scanned-probe RHEED data in an SEM, the acquisition side of the target. The NIST record lists only grain size and orientation keywords, and no phase retrieval is stated. (b) is the historical scanned focused probe in RHEED geometry. (c) claims low-energy (1-100 eV) oblique-incidence ptychography with overlapping probe positions. It is a patent claim, not a demonstrated result. | (a) OUP blocked: request it. (b) library e-book. (c) Google Patents (opened). | (a), (b) METADATA_VERIFIED; (a) NIST record read; (c) abstract and energy statements read on Google Patents. |

### Is there any electron reflection / RHEED-geometry ptychography? (topic 3 conclusion)

FACT (this session): no peer-reviewed paper or preprint on ptychography with high-energy electrons in
reflection (RHEED or REM geometry), and none on 4D-STEM-style phase retrieval in reflection, was found.
The following searches were run: arXiv API searches (ptychograph* with RHEED, LEED, LEEM, backscatter*,
"reflection electron microscopy", "scanning reflection electron microscopy", "Bragg ptychography" with
multislice: 0 hits); Crossref bibliographic searches; and three general web searches. What was found
is: an ASML patent application for LEED-energy reflection ptychography (T3-13c); a 2025 4D-RHEED-in-SEM
conference abstract with no phase retrieval stated (T3-13a); and the X-ray and EUV reflection and
grazing-incidence work above. The citation-graph searches (OpenAlex, Semantic Scholar) could not be run
because both returned HTTP 429, so this is a negative search result, not proof of absence.
INFERENCE: a 200 keV grazing-incidence electron ptychography engine with a dynamical multislice
forward model appears to be an open niche. Its closest algorithmic precedent is T3-1 (X-ray), and its
closest object precedent is T3-2 and T3-5.

## Topic 4: electron ptychography in practice (dose, detectors, partial coherence, probe modes)

| ID | Priority | Citation | What to read | Why | Access route | Verified |
|---|---|---|---|---|---|---|
| T4-1 | MUST | Chen, Z., Odstrcil, M., Jiang, Y., Han, Y., Chiu, M.-H., Li, L.-J. and Muller, D. A. (2020). Mixed-state electron ptychography enables sub-angstrom resolution imaging with picometer precision at low dose. *Nat. Commun.* 11, 2994. DOI 10.1038/s41467-020-16688-6. | Results: "Experimental setup of electron ptychography" and "Low-dose atomic-resolution imaging". Methods: "Experimental method", "Mixed-state ptychography", "Fourier ring correlation". | PRAC, ALG. Probe modes for partial coherence; dose against resolution (both WS2 sublattices resolved above 3300 e/A^2; lattice still visible at 375 e/A^2); defocused probe with large scan steps; EMPAD settings; LSQ-ML with mini-batches. | Open (nature.com, opened, CC BY 4.0). | METADATA_VERIFIED; SECTION_READ. |
| T4-2 | SHOULD | Clark, L. and Nellist, P. D. (2025). Electron ptychography. arXiv:2503.10917 (review; no journal reference found). | III.D (detectors for 4D-STEM); IV.B.3 ("Solution stability (or why PIEs should be round)"); IV.C-IV.D (mixed-state, multislice); IV.F (sampling, sensitivity and precision); Appendix B (open codes). | PRAC, SAMP, SW. An electron-specific guide to choosing acquisition parameters and algorithms. | Open arXiv (opened). | SECTION_READ (arXiv v1). |
| T4-3 | SHOULD | Jiang, Y., Chen, Z., Han, Y., Deb, P., Gao, H., Xie, S., Purohit, P., Tate, M. W., Park, J., Gruner, S. M., Elser, V. and Muller, D. A. (2018). Electron ptychography of 2D materials to deep sub-ångström resolution. *Nature* 559, 343-349. DOI 10.1038/s41586-018-0298-5. | Main text plus Methods. | PRAC. Why a full-dynamic-range pixel detector matters: 80 keV, information limit close to 5 alpha, 0.39 A. | Library journal. | METADATA_VERIFIED +ABSTRACT(Semantic Scholar). |
| T4-4 | SHOULD | Ophus, C. (2019). Four-dimensional scanning transmission electron microscopy (4D-STEM): from scanning nanodiffraction to ptychography and beyond. *Microsc. Microanal.* 25(3), 563-582. DOI 10.1017/S1431927619000497. | Sections on detectors, data and phase-contrast methods. | PRAC. 4D-STEM data practice. | Open (Cambridge). | METADATA_VERIFIED +ABSTRACT(Crossref). |
| T4-5 | OPTIONAL | Tate, M. W. et al. (2016). High dynamic range pixel array detector for scanning transmission electron microscopy. *Microsc. Microanal.* 22(1), 237-249. DOI 10.1017/S1431927615015664. | Detector architecture. | PRAC. Abstract: 128 x 128 pixels, "1,000,000:1 dynamic range", 1.1 kHz. | Open (Cambridge). | METADATA_VERIFIED +ABSTRACT(Crossref). |
| T4-6 | OPTIONAL | Humphry, M. J., Kraus, B., Hurst, A. C., Maiden, A. M. and Rodenburg, J. M. (2012). Ptychographic electron microscopy using high-angle dark-field scattering for sub-nanometre resolution imaging. *Nat. Commun.* 3, 730. DOI 10.1038/ncomms1733. Pennycook, T. J. et al. (2015). Efficient phase contrast imaging in STEM using a pixelated detector. Part 1. *Ultramicroscopy* 151, 160-167. DOI 10.1016/j.ultramic.2014.09.013. | As needed. | PRAC, ALG. | Open / library. | METADATA_VERIFIED (both). |
| T4-7 | OPTIONAL | Dwyer, C. and Paganin, D. M. (2024). Quantum and classical Fisher information in four-dimensional scanning transmission electron microscopy. *Phys. Rev. B* 110, 024110. DOI 10.1103/PhysRevB.110.024110. Varnavides, G. et al. (2025). Beyond contrast transfer: spectral SNR as a dose-aware metric for STEM phase retrieval. arXiv:2507.19476. Varnavides, G., de Kleijne, W. P. M. and Ribet, S. M. (2026). The ABCs of phase retrieval. *MRS Bull.* 51(7), 897-912. DOI 10.1557/s43577-026-01100-3. | Dose limits and metrics. | PRAC. | Library / arXiv. | METADATA_VERIFIED for Dwyer and Paganin; +ABSTRACT(arXiv) for Varnavides 2025; METADATA_VERIFIED for the MRS Bulletin article (a correction notice exists, DOI 10.1557/s43577-026-01149-0). |

## Inferences for the engine (not facts from the sources; numbers DERIVED_HERE)

1. **Geometry already matches.** The repository's multislice already uses the frame that T3-1 uses:
   the beam axis is parallel to the surface, and the glancing angle enters as a tilt of the incident
   wave. A ptychography engine needs three additions: a localised (convergent or defocused) probe in
   place of the sheet beam; a differentiable version of the kernel, built either with AD in the manner
   of T2-3, T2-4 and T2-8, or with a hand-derived 3PIE-style back-propagation (T2-1); and a detector
   model for the far field of the wave leaving the surface.
2. **Cost.** T2-2 used 42 slices. The repository's (008) run uses about 3100 slices, so each probe
   position needs about 74 times more propagation steps (3100/42 = 73.8). Gradient memory grows with
   the number of stored slices; T3-1 buffers only the illuminated sub-volume. The crystal is periodic
   along the beam (3.84 A repeat), and T2-8 supports "models that are periodic in beam direction". Both
   could reduce memory, but neither has been tested here.
3. **Overlap and positions.** At 16.93 mrad the footprint is elongated by 1/sin(theta) = 59.1 (T3-3).
   For the same relative linear overlap (about 60 %, T1-8), the scan step along the beam can therefore be
   about 59 times the step across it. A height change dx moves the footprint by dx/tan(theta) = 59.1 dx
   along the beam (repository SM07), so sample height and tilt become position parameters to refine.
4. **Uniqueness (T1-5).** The Si(001) 1x1 in-plane period is 3.84 A, so neighbouring surface rods are
   lambda/3.84 A = 6.54 mrad apart at 200 keV. Their disks overlap only if the probe semi-angle alpha
   exceeds 3.27 mrad. The repository's dark-field aperture (radius 1.5 mrad) keeps a single
   reflection, so there is no interference between beams at all. A dark-field reflection ptychography
   can therefore reconstruct only the slowly varying complex field of that one reflection (as in Bragg
   ptychography, T3-5 and T3-6, and dark-field X-ray ptychography, T3-9), not the atomic lattice. The
   probe convergence must also stay well below the 16.93 mrad glancing angle, or the probe spans the
   rocking curve. Together these give a design window for alpha that must be computed, not assumed.
5. **Validity of simple models.** T3-2 (kinematic) underestimates step phases. T3-3's height relation
   assumes single scattering. T1-1 Sec. 6.2 says forward-only multislice is adequate for high-energy
   electrons. A forward-only grazing multislice inside the reconstruction is therefore consistent with
   the literature. The specular beam leaves at 2 theta = 33.9 mrad, inside the repository's 64.3 mrad
   band limit at 0.13 A (SM15).
6. **Licences.** The repository is MIT. PyGRAPES, py4DSTEM and abTEM are GPL-3.0; PtyRAD is LGPL-3.0;
   quantEM is MIT; fold_slice has an academic non-commercial licence; the PtyPy README notes Phase Focus
   patent licences. Use GPL code as an external benchmark or dependency, and do not copy it into this
   repository without a licence decision. (Not legal advice.)
7. **Kirkland edition.** PtyRAD's tilted propagator cites "equation 6.99 in Kirkland (2010)", the 2nd
   edition. The repository's B06 is the 3rd edition (2020), so the equation numbers may differ
   (UNVERIFIED).

## Documents to request from Ali (paywalled, or blocked from this environment)

1. Maiden and Rodenburg 2009, Ultramicroscopy 109, 1256 (T1-2; also reading-plan P06).
2. Maiden, Humphry and Rodenburg 2012, JOSA A 29, 1606 (T2-1).
3. Van den Broek and Koch 2013, PRB 87, 184108, and 2012, PRL 109, 245502 (T2-3, T2-5).
4. Chen et al. 2021, Science 372, 826: the published version and the supplementary materials (T2-2).
5. Thibault et al. 2008, Science 321, 379, with its supporting online material (T1-6).
6. Edo et al. 2013, PRA 87, 053850 (T1-9) and Takahashi et al. 2013, PRB 87, 121201 (T3-5).
7. The published Springer chapter (pp. 819-904), to turn the accepted-manuscript section locators into
   page numbers (T1-1).
8. Holm 2025, M&M 31 (Suppl. 1), ozaf048.197 (T3-13a), and Ichikawa and Doi 1988 (T3-13b).
9. Open access but blocked here (the student can download these directly): Odstrčil 2018, Maiden 2017,
   Tsai 2016, Kandel 2019, the Optica version of Jørgensen 2024, and Seaberg 2014.

## Notes for the bibliography-verifier (not edited here)

New verified records that are not yet in `docs/literature/references.bib`: every item above apart from
C03, P06, P34 to P41. Corrections to existing entries: P35 (Godard 2011) has DOI 10.1038/ncomms1569;
P34 (Roy 2011) has pages 243-245 and the full author list given in T3-10; P38 (Jørgensen 2024) has DOI
10.1364/OPTICA.505478; P41 has the full author list given in T1-11. This agent did not edit
references.bib.

## Working log (raw verification results; kept for audit)

### Access conditions in this session (2026-10-15)

Reachable: api.crossref.org, export.arxiv.org and arxiv.org, api.openalex.org (rate-limited, HTTP 429
at times), api.semanticscholar.org, ncbi.nlm.nih.gov (PMC), opg.optica.org, link.springer.com,
nature.com, iopscience.iop.org. Blocked (HTTP 403 through the proxy): doi.org redirects to science.org,
science.org, sciencedirect.com, journals.aps.org, pubs.aip.org, onlinelibrary.wiley.com,
academic.oup.com, europepmc.org.

### Crossref batch 1 (topic 1), all fields matched the record queried

10.1007/978-3-030-00069-1_17 (Rodenburg, Maiden, Ptychography, Springer Handbook of Microscopy 2019,
pp. 819-904, ISBN 9783030000684 / 9783030000691); 10.1016/S1076-5670(07)00003-1 (Rodenburg, AIEP 2008,
pp. 87-184, ISBN 9780123742179); 10.1126/science.1158573; 10.1016/j.ultramic.2008.12.011;
10.1016/j.ultramic.2009.05.012; 10.1063/1.1823034; 10.1103/PhysRevLett.93.023903;
10.1088/1367-2630/14/6/063004; 10.1038/nature11806; 10.1364/OE.26.003108; 10.1364/OPTICA.4.000736;
10.1016/j.ultramic.2012.06.001; 10.1364/OE.21.013592; 10.1364/OE.16.007264;
10.1016/j.ultramic.2007.08.003; 10.1364/OE.23.033812; 10.1103/PhysRevA.87.053850;
10.1038/s41566-017-0072-5; 10.1063/PT.3.4835; 10.1364/OE.485370; 10.1038/s43586-025-00438-3
(full author list now known: Wang, Zhao, Loetgering, Allars, Hong, Pennycook, Horstmeyer, Rodenburg,
Maiden, Zheng; Nat. Rev. Methods Primers 5, 68, 2025).

### Crossref batch 2 (topic 2), all matched except one

10.1364/JOSAA.29.001606; 10.1364/OE.24.029089; 10.1126/science.abg2533; 10.1038/s41586-018-0298-5;
10.1038/s41467-017-00150-1; 10.1103/PhysRevLett.109.245502; 10.1103/PhysRevB.87.184108;
10.1364/OE.27.018653; 10.1364/OE.418296; 10.1364/OE.396925; 10.1017/S1431927621000477;
10.1107/S1600576720001776; 10.1098/rspa.2016.0640; 10.12688/openreseurope.13015.1 and .2;
10.1017/S1431927619000497; 10.1126/sciadv.abn2275; 10.1038/s41467-020-16688-6; 10.1364/OE.22.012513;
10.1107/S1600576720010985.
A guessed DOI for Diederichs et al. 2024 returned 404; the Crossref bibliographic search gives
10.1038/s41467-023-44268-x (to be confirmed by direct lookup).

### Search for electron reflection / RHEED-geometry ptychography (first pass)

arXiv API queries (abstract field): ptychograph* + RHEED: 0 hits; ptychograph* + backscatter*: 0;
"reflection electron microscopy" + (4D, ptychograph*, pixelated): 0; ptychograph* + LEEM: 0;
"Bragg ptychography" + multislice: 0; ptychography + reflection + electron: 7 hits, none an
electron reflection experiment (X-ray/EUV reflection or transmission electron work). Two web searches
(extended mode) returned only RHEED background and transmission 4D-STEM pages.

### Search for electron reflection ptychography (second pass, 2026-10-15)

* arXiv (all fields): ptychograph* + LEED: 0; ptychograph* + "electron reflectivity": 0;
  "reflection electron" + "phase retrieval": 0; "scanning reflection electron microscopy": 0;
  au:van_der_Molen + ptychograph*: 0; ptychograph* + "reflection mode" + electron: 1 hit (Seaberg 2013,
  EUV, not electrons).
* Crossref bibliographic queries ("electron ptychography reflection geometry surface", "reflection
  electron microscopy ptychography", "ptychography reflection high energy electron diffraction",
  "four-dimensional scanning reflection electron microscopy") returned no ptychography-in-reflection
  electron paper. They did return: Holm, "4-Dimensional Reflection High Energy Electron Diffraction on
  2-Dimensional Materials in a Scanning Electron Microscope", Microsc. Microanal. 31 (Suppl. 1),
  ozaf048.197 (2025), DOI 10.1093/mam/ozaf048.197 (Crossref record; no abstract deposited; OUP blocked).
  The NIST record https://www.nist.gov/node/1898226 was read: keywords "RHEED, SEM, electron diffraction,
  2D Materials, MoS2, grain size, grain orientation"; no abstract and no mention of phase retrieval or
  ptychography. And: Ichikawa and Doi, "Microprobe Reflection High-Energy Electron Diffraction", NATO ASI
  Series (RHEED and Reflection Electron Imaging of Surfaces), pp. 343-369 (1988), DOI
  10.1007/978-1-4684-5580-9_25 (Crossref record only).
* Patent application read on Google Patents (https://patents.google.com/patent/WO2025131995A1/en and
  the Taiwanese family member TW202542655A): ASML Netherlands BV, "LEED and ptychography based surface
  profile determination and inspection", WO2025131995A1, priority 2023-12-20, published 2025-06-26;
  inventors Coene, van Rens, Krecinic, Garming, Kooiman, van der Molen. Abstract text read, including
  "LEED in combination with ptychography (to generate a series of diffraction patterns which are each
  associated with a given particle beam position, where particle beams centered at neighboring
  positions are partially overlapping)". Landing energies stated as "low-energy (e.g., 1-100 eV)";
  incidence "at a certain angle" (no number found in the part read). This is a patent claim, not a
  demonstrated or peer-reviewed result, and it is low-energy (LEED/LEEM), not RHEED geometry.
* OpenAlex and Semantic Scholar searches failed (HTTP 429 on every retry): the citation-graph search
  could NOT be run. The "none found" conclusion below therefore rests on arXiv, Crossref and three
  general web searches only.

### Reading notes (facts read in this session; locators given)

**Besley et al. 2025, arXiv:2510.06877v1** (read via https://arxiv.org/html/2510.06877v1; 27 pages,
11 figures; licence CC BY-NC-SA 4.0; no journal reference on the abstract page). Facts: the optical axis
is aligned parallel to the substrate surface and "The angle of incidence is then applied to the incident
wave field in the form of a constant phase gradient" (Fig. 2 caption); slice transmission
O_j = exp[ik ∫ n dz] (Sec. 2.2, Eq. 6); psi_j = P(dz) O_j psi_{j-1} with a Fresnel propagator adapted
from Adorym (Sec. 2.2, Eq. 7); "Reflection and multiple scattering arise naturally" (Fig. 2 caption);
loss = MSE + regulariser + noise term (Sec. 2.3, Eq. 8); reverse-mode automatic differentiation, SGD for
the volume and Adam for probe and positions (Sec. 2.3.1); reconstructs a 3-D volume of complex
delta + i beta (Sec. 2.3.1); position refinement by Fourier shift of the probe (Sec. 2.3.1); 6.2 keV
X-rays, incidence 0.5, 0.6, 0.8 deg, Au critical angle about 0.72 deg (Sec. 2.4); the projection
approximation "fails to capture the significant multiple scattering that occurs in grazing incidence"
(abstract) and "breaks down at higher spatial frequencies when compared to multislice" (Sec. 3.3).
Code: PyGRAPES, https://github.com/lsbesley/pygrapes (README read: "a versatile pytorch-based multislice
framework for 3D reconstruction and simulation of ptychographic data in grazing incidence"; GPL-3.0).
It cites a "Li et al." multislice reflection approach needing about 10^2 to 10^3 slices (Sec. 1); the
matching record is Li, Wojcik, Jacobsen, "Multislice does it all - calculating the performance of
nanofocusing X-ray optics", Opt. Express 25, 1831 (2017), DOI 10.1364/OE.25.001831 (Crossref search
hit; that the "Li et al." of Besley is this paper is an INFERENCE until the reference list is checked).

**Chen et al. 2021, Science 372, 826, arXiv:2101.00465v1** (PDF text read, Materials and Methods, PDF
pp. 15-18). Facts: 300 keV Titan Themis, probe semi-angle 21.4 mrad, EMPAD 128 x 128 pixels, probe
focused about 20 nm above the top surface, scan step 0.41 A, 128 x 128 positions, dose 1.2 x 10^6 e/A^2,
diffraction sampling 0.823 mrad per pixel, maximum angle about 2.5 x the probe semi-angle; thickness
limit of the multiplicative approximation "T < 1.3 lambda / theta_max^2"; implemented "in the framework
of the generalized maximum-likelihood method with gradient descent" with a Fresnel propagator inside the
sample; mixed-state probe (12 modes) with each mode propagated separately and intensities summed; 42
slices of 0.5 nm; slice thickness below about 2 nm needed; position refinement from a middle slice
works best; a low-spatial-frequency inter-slice regularisation was added; about 45 min per iteration on
a Quadro P5000 for 256 x 256 detector pixels, 128 x 128 patterns, 12 modes, 42 slices.

**Ribet et al. 2026, arXiv:2608.30359v1** (PDF text read: abstract, Sec. 1 end, Sec. 3.2 heading,
Sec. 5). Facts: "once the convergence angle is small enough that no diffracted disks overlap, the
resulting reconstruction is ambiguous"; "Real-space overlap between adjacent probe positions does not
lift this degeneracy, rendering it a necessary but insufficient criterion for unique convergence"; an
amorphous substrate can supply the missing phase relationships but "this phasing is not robust" and
survives only for a forward model that matches the experiment; reconstructions were run in quantEM.
Disk overlap requires 2 alpha / (lambda g) > 1 (their Fig. caption gives 2 alpha / lambda g_111 = 2.9 at
30 mrad, overlapping, and 0.8 at 8 mrad, not overlapping). Preprint, not peer reviewed.

**Lee et al. 2025 (PtyRAD), Microsc. Microanal. 31, ozaf070, arXiv:2505.07814v2** (PDF text read,
Sec. "PtyRAD", Eqs. 3-4, "Optimizers and loss functions"). Facts: PyTorch, automatic differentiation;
mixed probe and object states with multislice; optimises probe positions, local tilts and slice
thickness; multislice propagator with local mistilt "following equation 6.99 in Kirkland (2010)",
M(k) = exp[-i pi lambda |k|^2 dz + 2 pi i dz (k_x tan theta_x + k_y tan theta_y)] (Eq. 4); Adam
optimiser; Gaussian and Poisson negative log-likelihood losses following Thibault and Guizar-Sicairos
(2012); PACBED loss; imports objects/probes from PtychoShelves/fold_slice and py4DSTEM. Version note:
the arXiv-API abstract (v1) says "up to a 17x speedup"; the v2 PDF text says "up to a 24 x speedup".

**Zhu et al. 2015, Appl. Phys. Lett. 106, 101604** (full text read from PSI DORA,
https://www.dora.lib4ri.ch/psi/dload/psi:7274/PDF/view, published layout, 5 pages). Facts: Eq. (1)
writes the diffraction amplitude for a surface height h(x_s, y_s) under probe p as
A proportional to (1/q_zs) |∫∫ p exp(-i q_zs h) exp(-i(q_xs x_s + q_ys y_s)) dx_s dy_s| (p. 101604-2);
"the diffraction from the height variation on a crystal surface in reflection mode is identical to the
diffraction from a two-dimensional pure phase object in transmission geometry, except for the sin
theta factor. This similarity enables us to adopt ptychographic algorithms developed for the
transmission geometry to the reflection geometry" (p. 101604-2); difference map with simultaneous probe
retrieval; 9 keV, Pt(0 0 1.5) at theta = 15.3 deg, CCD at 2 theta, 543 mm; probe pre-reconstructed in
transmission on a test object; reconstructed pixel 15 nm along x_s but 57 nm along y_s "due to the
incidence angle"; observed phase steps of about 2 rad and 1 rad against "the expected phase steps of
3 pi/2 = 4.7 rad"; apparent resolution about 100 nm (p. 101604-4). INFERENCE: Eq. (1) is the X-ray
kinematic counterpart of the repository's step phase (SM03, SM19); it is exactly the multiplicative
reflection model that the instruction file warns does not carry over to dynamical 200 keV RHEED.

**Bunk et al. 2008, Ultramicroscopy 108, 481** (accepted-manuscript text read from PSI DORA,
https://www.dora.lib4ri.ch/psi/dload/psi:18937/PDF2/view, "Preprint submitted to Elsevier 19 July
2007"; the PDF uses a custom font encoding, decoded here with a substitution script). Facts: overlap
is a linear distance, relative overlap o = 1 - a/(2r) for circles of radius r at spacing a (Sec. 2,
Eq. 4); "The optimum image quality is obtained for a very high overlap of about 85 %"; "a relative
overlap of 60 % of the diameter of the defining pinhole seems to be adequate"; "the overlap should not
exceed 85 %"; for dose-sensitive samples "relative overlaps of only 30 % seem to be advisable"; overlap
along one dimension is sufficient to constrain PIE (Sec. 3, PDF pp. 12-13).

**Thibault and Guizar-Sicairos 2012, New J. Phys. 14, 063004** (IOPscience landing page read,
labelled "Free article"; licence not stated on the page). Section list read: 1 Introduction;
2 Fundamentals; 3 Implementation details (3.1 Preconditioning, 3.2 Regularization, 3.3 Alternative
models); 4 Results; 5 Discussion (5.1 Convergence and computation time, 5.2 Application to other
coherent diffractive imaging techniques); 6 Conclusion; Appendix A (Gaussian parameters from Poisson
measurements); Appendix B (polynomial expansion of the Gaussian model). Equation numbers as reported by
the page reader (the equations are images, formulas not read): Poisson negative log-likelihood Eq. (4);
probe and object gradients Eqs. (5)-(6) with Wirtinger derivatives; Gaussian (weighted least squares)
Eq. (8); amplitude (Euclidean) model Eq. (11); conjugate gradient Eqs. (13)-(15) (Polak-Ribiere);
line search Eq. (17); preconditioning Eqs. (18)-(29); regularisation Eqs. (30)-(36); probe support
Eq. (37); per-frame intensity scale Eqs. (38)-(42). Strategy stated in Sec. 5.1: "the most efficient
strategy for ptychographic reconstruction is to use both reconstruction procedures successively"
(difference map, then ML refinement).

**Jorgensen et al. 2024, Optica 11, 197** (Optica blocks automated access with a JavaScript challenge;
arXiv:2307.01735v1 text read instead; the journal version may differ). Facts: 6.2 keV; Pilatus 2M,
172 um pixels; reconstruction in PtychoShelves with difference map followed by LSQ-MLc; multislice
(following Li et al.) is used only to SIMULATE validation data, "the reconstruction, which does not use
a multislice approach" (Introduction); height from phase "h = phi/(2k sin(theta))" assuming constant
refractive index and single scattering (Discussion); the footprint "is elongated in the longitudinal
direction by a factor of 1/sin(theta). To keep the probe overlap consistent in both directions, the
scanning step size along the grazing axis has to be scaled accordingly" (Methods); higher-order DWBA
terms "need to be explored further" (Discussion).

**Seaberg et al. 2014, Optica 1, 39** (arXiv:1312.2049v1 text read). Facts: 29 nm HHG light at 45 deg
incidence; "Due to the non-normal angle-of-incidence on the sample, the patterns must be remapped onto a
grid that is linear in spatial frequencies of the sample plane, in order to use fast Fourier transforms";
"We used tilted plane correction to accomplish this[19]" with [19] = Gardner et al., Opt. Express 20,
19050 (2012); reconstruction by ePIE with sub-pixel position correction (Methods steps 1-4); round-trip
path difference "-2h cos theta" (theta from the normal).

**Chen et al. 2020, Nat. Commun. 11, 2994** (nature.com HTML read; CC BY 4.0). Facts (Methods,
"Experimental method"): EMPAD 128 x 128, 80 keV, 21.4 mrad, about 55 nm defocus, 1 ms frames, scan
step 2.36 A; ("Mixed-state ptychography"): generalized maximum-likelihood ptychography with
preconditioned gradient descent, amplitude likelihood "provides more robust convergence than direction
optimization of Poisson likelihood", mini-batch scheme, modal decomposition of the probe, illumination
wavefront correction as a cheaper approximation of orthogonal probe relaxation; mixed-state
reconstruction "is not sensitive to the initial guess of the illumination probe and the number of the
mixed modes for datasets with a sufficient probe overlap". ("Low-dose atomic-resolution imaging"):
both WS2 sublattices resolved above 3300 e/A^2; lattice still recognised at 375 e/A^2 (about 1.59 A).

**Diederichs et al. 2024, Nat. Commun. 15, 101** (nature.com HTML read). Facts (Abstract; Methods,
"Details of inversion scheme"): a "parametrized, fully differentiable scheme" in PyTorch inverts 4D-STEM
data in terms of atom types and positions, frozen phonons, partial coherence and aberrations; Adam or
SGD; "The relative orientation between specimen and illumination is taken into account via tilting the
Fresnel propagator"; source code as Supplementary Software 1. INFERENCE: an atom- or
displacement-parametrised object is the natural way to reconstruct a near-surface dislocation strain
field in reflection, with far fewer unknowns than a voxel grid.

**Godard et al. 2011, Nat. Commun. 2, 568** (nature.com HTML read). Facts (Methods, "Phase retrieval"):
the exit wave is computed "using the Born approximation (equation (1))"; lambda = 0.154 nm, G_220;
Bragg-adapted ptychographic iterative engine retrieving density and displacement-field phase.

**Wang et al. 2025, Nat. Rev. Methods Primers 5, 68** (PMC author manuscript PMC13024499, HTML read to
about 200 000 characters). Section list read: 1 Introduction; 2 Experimentation (2.1 Experimental
configurations; 2.2 Computational framework, incl. Table 1 "Gradient-based ptychographic reconstruction",
"System calibration", "Advanced modeling and specialized reconstructions"; 2.3 Wavelength specific
considerations); 3 Results (3.1 optical, 3.2 EUV, 3.3 X-ray, 3.4 electron); 4 Applications;
5 Reproducibility and data deposition; 6 Limitations and optimizations; 7 Outlook. Quotes: "Typically
adjacent measurements overlap by 50% or more" (Sec. 1); "general reflection ptychography operates at
arbitrary incident angles without Bragg constraints" (Sec. 2.1); X-ray work "leverages reflection
geometry at shallow angles (<1 deg) for total external reflection" (Sec. 3.3); "The multiplication
between the object and probe beam assumes that specimens are thin" (Sec. 6).

**Clark and Nellist 2025, arXiv:2503.10917v1, "Electron Ptychography"** (PDF text read). Section list:
I Introduction; II Historical view; III Geometries and data structures (III.D Detectors for 4D-STEM,
III.E Generalised description of a 4D-STEM dataset); IV Ptychographic algorithms (IV.A Direct methods:
SSB, WDD; IV.B Iterative methods: PIE, flavours, "Solution stability (or why PIEs should be round)";
IV.C Mixed-state; IV.D Multislice STEM ptychography; IV.E Fourier ptychography; IV.F Sampling,
sensitivity and precision); V Applications; VI Summary; Appendix B "Available open access codes for
ptychography" (PtychoSTEM, PyPtychoSTEM, PtyPy, py4DSTEM, LiberTEM, FPD, Muller group codes, Sheffield
codes, PtychoShelves, PtychoPy). No journal reference found.

**Varnavides et al. 2023, arXiv:2309.05250v2** (PDF text read: structure and ptychography "Inverse
Problem Formalism", "Preprocessing and Results"). Facts: iterative DPC, parallax and a generalized
gradient-descent ptychography in 2D and 3D (multislice) implemented in py4DSTEM; stochastic gradient
descent and proximal gradient variants. No journal reference on arXiv; a related review by the same
group is Varnavides, de Kleijne, Ribet, "The ABCs of phase retrieval", MRS Bull. 51, 897-912 (2026),
DOI 10.1557/s43577-026-01100-3 (Crossref only; a correction notice 10.1557/s43577-026-01149-0 exists).

**PubMed abstracts read (pubmed.ncbi.nlm.nih.gov via E-utilities):** Maiden and Rodenburg 2009 (PMID
19541420: PIE "extended so that the requirement for an accurate model of the illumination function is
removed"); Thibault et al. 2008 (PMID 18635796); Van den Broek and Koch 2012 (PMID 23368342: "Dynamical
scattering of fast electrons can be inverted by recasting the multislice algorithm as an artificial
neural network"; handles detector MTF, partial spatial and temporal coherence, absorptive potential;
demonstrated on simulated bright-field images at 40 kV); Maiden, Humphry, Rodenburg 2012 (PMID 23201876:
3-D ptychography "can successfully recover images in the presence of multiple scattering and when the
projection approximation is not applicable"); Thibault and Menzel 2013 (PMID 23389541); Maiden et al.
2012 annealing (PMID 22813888: corrects positioning errors "tens of times larger than the pixel size");
Godard 2011 (PMID 22127064); Hruszkewycz 2017 (PMID 27869823). No PubMed record: Edo 2013 (PRA),
Takahashi 2013 (PRB), Maiden 2017 (Optica), Thibault and Guizar-Sicairos 2012.

**Semantic Scholar abstracts read (api.semanticscholar.org batch record):** Odstrcil 2018; Tsai 2016
("smaller scanning steps surprisingly increase the depth of field"); Kandel 2019 (object recovery "by
specifying only the physics-based experimental forward model"); Li, Wojcik, Jacobsen 2017 (multislice
"allows one to reproduce other X-ray optical phenomena such as grazing incidence reflectivity where the
direction of energy flow is changed significantly"); Clark et al. 2022/2023 M&M (breakdown of the
multiplicative and weak-phase approximations for iCoM, SSB, WDD over a GaN thickness series); Jiang 2018.

**Rodenburg and Maiden 2019, Springer Handbook chapter** (accepted manuscript read from White Rose,
https://eprints.whiterose.ac.uk/127795/1/Ptychography_Chapter-Rodenburg%2BMaiden_final.pdf, "Version:
Accepted Version", 138 PDF pages; SpringerLink served a bot challenge and was not readable). Heading
list read (manuscript numbering): 1 Introduction (1.1 Nomenclature); 2 A Brief History; 3 How
Ptychography Solves the Phase Problem (3.1-3.5); 4 Sampling and removal of artefacts in images (4.1
Probe recovery; 4.2 Some pathological instances where Ptychography struggles; 4.3 Non-periodic scan;
4.4 Refining probe positions; 4.5 Field of view; 4.6 Missing data and data truncation; 4.7 Shot noise;
4.8 Artefacts in Figure 10); 5 (configurations: 5.1 Focused probe; 5.2 Fourier; 5.3 Selected Area;
5.4 Fresnel full-field; 5.5 Defocused probe; 5.6 Diffusers; 5.7 Bragg ptychography; 5.8 Visible light
reflective ptychography; 5.9 Transmission and reflection EUV ptychography; 5.10 The simple aperture;
5.11 Probe reconstruction in the Fresnel configurations); 6 Volumetric imaging (6.1 X-ray
ptycho-tomography; 6.2 Multi-slice reconstruction); 7 Spectroscopic imaging; 8 Mixed State
Decomposition and Handling Partial Coherence (8.1-8.6, 8.3 Electron modes); 9 Theory (9.1 The PIE
family of algorithms; 9.2 Projection between sets methods; 9.3 Implementing ptychographic algorithms
on the computer; 9.4 A basic comparison of algorithms); 10 Wigner distribution deconvolution (10.1-
10.6.6); 11 Conclusions. The title of Sec. 5 was not captured by the text extraction. Read in full:
Sec. 5.7-5.9 (PDF pp. 63-67) and Sec. 6.2 (PDF pp. 72-77). Quotes: Sec. 5.9, glancing-angle reflection,
"care must be taken to map the detector coordinates to the scattering configuration and the elongated
probe shape and phase"; Sec. 6.2, "This particular multi-slice formulation also does not account for
backwardly propagating waves that have been reflected off the layers: forward-only scattering is a
good approximation for the behaviour of high-energy electrons and X-rays, but not for visible light";
Sec. 6.2, layer separation and refractive index "can just be put into the algorithm as another set of
free variables".

**Software READMEs read on GitHub (2026-10-15):** fold_slice (yijiang1): GPU_MS "modified least-squares
maximum likelihood multi-slice ptychography algorithm"; Academic License Agreement (non-commercial);
"archived by the owner on Aug 5, 2026"; asks to cite Chen et al. 2021 for GPU_MS. abTEM: "simulations of
(scanning) transmission electron microscopy images and diffraction patterns using the multislice or
PRISM algorithms"; no reconstruction module mentioned; GPL-3.0; cite Madsen and Susi 2021 (.13015.2).
py4DSTEM: phase-retrieval modules "underwent a major refactor in version 0.14.9"; GPLv3; cite Savitzky
et al. 2021. quantEM: "a quantitative electron microscopy data analysis toolkit built on PyTorch";
ptychographic phase retrieval; MIT; cite the Zenodo record named in the README (that DOI was not
resolved here). PtyRAD (chiahao3/ptyrad): LGPL-3.0; `pip install ptyrad`; documentation
https://ptyrad.readthedocs.io. PtyPy: DM and ML engines, with RAAR, sDR and ePIE among "a few more
engines"; GPU via CuPy and PyCUDA; Phase Focus patent-licence notice. PyGRAPES: see Besley above.
GitHub API access to these repositories is not enabled for this session; the pages were read through
WebFetch.

**Abstracts read via OpenAlex single-work records:** Edo 2013 (quoted in T1-9); Takahashi 2013;
Maiden 2017; Van den Broek and Koch 2013; da Silva and Menzel 2015. No abstract in OpenAlex for the
Springer chapter or for Rodenburg 2008.

**Crossref direct lookups, final batch:** Dwyer, Christian and Paganin, David M., PRB 110(2), 024110
(2024); Pennycook, Timothy J. et al., Ultramicroscopy 151, 160-167 (2015); Fannjiang, Albert and Chen,
Pengwen, Inverse Problems 36(4), 045005 (2020); Li, Kenan, Wojcik, Michael and Jacobsen, Chris, Opt.
Express 25(3), 1831 (2017); Clark, Laura et al., Microsc. Microanal. 29(1), 384-394 (print 2023-02-01,
issued 2022-12-20). Batch 3 (topics 3 and 4; all matched): 10.1038/s41467-023-44268-x;
10.1038/ncomms1569; 10.1103/PhysRevB.84.144109; 10.1021/nl303201w; 10.1038/nmat4798;
10.1103/PhysRevB.87.121201; 10.1063/1.4914927; 10.1038/srep09827; 10.1038/nphoton.2011.11;
10.1364/OPTICA.1.000039; 10.1364/OE.20.019050; 10.1126/sciadv.abd9667; 10.1063/5.0204240;
10.1364/OE.591755; 10.1093/mam/ozaf070; 10.1364/OPTICA.522380; 10.1557/s43577-026-01100-3;
10.1038/ncomms1733; 10.1017/S1431927615015664; 10.1364/OE.20.025914; 10.1364/OE.24.009038;
10.1364/OE.24.008360. Records with abstracts: 10.1364/optica.505478, 10.1093/mam/ozaf048.197 (no
abstract), 10.1117/12.3063903 (no abstract), 10.1093/micmic/ozac022, 10.1007/978-1-4684-5580-9_25,
10.1364/oe.23.016429.

**Not done:** citation-graph search (OpenAlex and Semantic Scholar search returned HTTP 429); reading
of any paywalled full text; resolution of the quantEM Zenodo DOI; reading of the Optica-hosted versions
(JavaScript challenge, HTTP 202).

(end of report)
