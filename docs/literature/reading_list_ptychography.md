# Reading list: ptychography for a reflection-mode (RHEED-geometry) electron ptychography engine

Status: IN PROGRESS (written incrementally by the literature-researcher agent, 2026-10-15).

Target engine: simulate scanned-probe diffraction patterns of a crystal surface at grazing incidence
(200 keV, glancing angle about 1 degree = 17.5 mrad) with the repository's grazing-incidence multislice
(`reflection_holo/forward/multislice.py`), then reconstruct the surface / near-surface object.

## Evidence labels used here

* METADATA_VERIFIED: authors, title, journal, volume, pages, year and DOI checked against the Crossref
  record (api.crossref.org/works/<DOI>) in this session.
* +ABSTRACT(read): the abstract was read on the publisher, arXiv, PMC or Crossref page in this session.
* SECTION_READ: the named section was read on the page in this session (locator given).
* UNVERIFIED: not checked; do not cite as is.

(sections follow)

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
