# Literature survey: dark-field electron holography (DFEH) for strain, and holography of dislocations

Prepared 2026-10-14 by a delegated literature agent for Ali (reflection-geometry DFEH of buried
dislocations under Si(001), 200 keV, specular (008)). Source policy of the project instruction file
applies: labels METADATA_VERIFIED, SECTION_READ, UNVERIFIED (+ABSTRACT(index) when only a search
summary was seen). In this report every claim is additionally marked **READ** (text seen by me on the
page/PDF named) or **NOT VERIFIED**.

Access in this session (differs from earlier sessions recorded in `docs/02_literature_position.md`):
reachable and used: HAL (hal.science + API), PubMed/PMC E-utilities, Crossref API, arXiv API, J-STAGE,
TU Berlin DepositOnce, University of Groningen Pure; IOPscience served abstract pages only (PDF links
returned a bot-check page). Refused with HTTP 403 by the site (no proxy relay failure logged):
ScienceDirect, Wiley, AIP (pubs.aip.org), OUP (academic.oup.com), APS (journals.aps.org), Europe PMC,
CORE. Connections closed by the agent proxy (relay failures logged, treated as blocked, not retried):
web.archive.org, api.fatcat.wiki. OpenAlex and Semantic Scholar APIs were rate-limited after a few
calls. Unpaywall was not used because it requires an e-mail address in every call.

Status: COMPLETE (written incrementally on 2026-10-14). Geometry caveat (inference): every paper
below is TRANSMISSION DFEH/holography or 4D-STEM; no reflection-geometry (RHEED/REM) dark-field
holography of strain or dislocations was found in this pass.

---

## Summary table (only papers whose full text I opened; label SECTION_READ for all rows)

| # | Paper (DOI) | URL actually read | What was read | Instrument / conditions (READ) | Figures shown (READ, captions) | Figures of merit and dislocation treatment (READ) |
|---|---|---|---|---|---|---|
| P1 | Boureau et al., J. Appl. Cryst. 53, 885-895 (2020), 10.1107/S1600576720006020 | hal.science/hal-03001931/document | full text + captions (author manuscript) | Hitachi HF-3300C (I2TEM), 300 kV, Lorentz mode, B-COR, two biprisms, fringe spacing 1.08 nm, g = 004 and 220, two-beam, 10 s, 0.1143 nm/px, lamella 110 nm, HoloDark 1.3, COMSOL FEM | DF hologram + fringe inset; geometric-phase map (amorphous blanked); displacement map; eps_zz map; RSMs from DFEH vs HRXRD; flow chart with hologram FT next to RSM | fringe contrast 13 %; resolution 4 nm (mask); strain sensitivity 5e-4 = std in unstrained Si substrate; FOV 546 nm; reference = Si substrate; no dislocation analysis |
| P2 | L. Niermann, T. Niermann, M. Lehmann, Ultramicroscopy 271, 114122 (2025), 10.1016/j.ultramic.2025.114122 | depositonce.tu-berlin.de bitstream aab621d1-... (CC BY journal PDF) | full text + captions | FEI Titan 80-300 Berlin Holography Special, 300 kV, single biprism, g = (01-12) two-beam, tilt series, 15 x 5 s holograms per tilt averaged (holoaverage), aperture 1.16 nm^-1 Butterworth; SCBED at 200 kV; DHW multi-beam + FEM | DFEH contrast and phase at one tilt; measured vs calculated phase/contrast (q, x) tilt-position maps; calculated phase/contrast/intensity over wide tilt range; FEM displacement fields | phase ramp removal; 2 pi phase jumps at amplitude zeros reproduced by calculation; DFEH phase breaks the mid-plane depth ambiguity of intensities; no strain map or precision number |
| P3 (related, 4D-STEM) | T. Niermann, L. Niermann, M. Lehmann, Nat. Commun. 15, 1356 (2024), 10.1038/s41467-024-45642-z | PMC10866901 (E-utilities JATS) | full text + captions (SI not read) | JEOL GrandArm F2, 300 kV, 3.3 mrad, 256 x 256 scan at 0.78 nm, MerlinEM; DHW column-approximation simulation | experimental vs simulated (q, x) planes across dislocations; MSE maps over (thickness, depth) | dislocation type and DEPTH: t = 132 nm/d = 55 nm and t = 172 nm/d = 85 nm, 5 nm depth precision; mid-plane ambiguity |
| P4 | Cho et al., Mater. Trans. 60, 698-703 (2019), 10.2320/matertrans.MC201809 | jstage.jst.go.jp .../60_MC201809/_pdf | full text + captions | Hitachi HF3300S, 300 kV, two biprisms, g = 100 (superlattice) and 200 (fundamental) and 000; reference inside specimen | holograms and phase images for 000/100/200; phase profiles across an antiphase boundary; wavelet denoising of a DF hologram | defect phase step 2 pi g.R: measured about 2.3 rad vs pi expected; no step for g.R = 0; phase uncertainty about 0.3 rad |
| P5 | Park et al., Adv. Sci. 9, 2200323 (2022), 10.1002/advs.202200323 | PMC9353496 (E-utilities JATS) | main text + captions (SI not read) | DARK-FIELD INLINE holography (focal series -8..+8 um, FRWR), JEM-2200F 200 kV, omega filter, g = (11-20), (0004); STEM-GPA 200 kV; 4D-STEM 300 kV; 3D FEM | same region by STEM-GPA, DIH and projected FEM with colour-coded line profiles; averaged-value bar chart; polarisation maps | STEM-GPA averages with +- (e.g. 1.2 +- 0.12 %); 4D-STEM resolution about 2 nm; DIH described as higher resolution/sensitivity, no number in main text; reference = unstrained GaN |
| P6 (foundational) | Hÿtch, Houdellier, Hüe, Snoeck, J. Phys.: Conf. Ser. 241, 012027 (2010), 10.1088/1742-6596/241/1/012027 | hal.science/hal-01742031/document | full text + captions | Tecnai F20 (SACTEM), 200 kV, pseudo-Lorentz and aberration-corrected Lorentz mode, rotatable biprism, fringe spacing 1-2 nm, hologram width 300-500 nm, g = (111), (004) | DF hologram + FT + zoom; phase; amplitude; planar-spacing and rotation maps; DF and BF holograms/phases and their difference; rotation maps before/after correction | phase = crystalline + magnetic + electrostatic + geometric; phi_G = -2 pi g.u; BF-phase subtraction removes thickness artefacts; 2e-4 at 4 nm (cited); +60 % SNR with corrected Lorentz mode |
| P7 | Denneulin et al., J. Phys.: Condens. Matter 30, 215701 (2018), 10.1088/1361-648X/aabd00 | pure.rug.nl .../Denneulin_2018_..._1_.pdf (publisher PDF) | full text + captions | Hitachi HF-3300 (I2TEM), 300 kV, Lorentz upper stage, double biprism, fringe spacing 2 nm, hologram width 300 nm, g = (002), (200); HRTEM-GPA on Tecnai 200 kV; 2D anisotropic FEM | DF holograms; eps_zz, eps_xx, eps_xz, R_xz maps vs FEM; profiles; numerical moiré magnification of hologram fringes vs FEM moiré | DFEH +-0.1 % at 6 nm vs HRTEM-GPA +-0.5 % at 2 nm; extra 2 nm Gaussian smoothing; threading dislocations seen as dark lines in the (200) hologram and abrupt jumps in eps_xx |
| P8 (older) | Denneulin, Cooper, Hartmann, Rouvière, J. Appl. Phys. 112, 094314 (2012), 10.1063/1.4764045 | hal.science/hal-02145343/document | full text + captions | FEI Titan, 200 kV, Lorentz lens, single biprism at +180 V giving 2 nm fringes, 10 um aperture, g = (004), (220), 64 s exposure, Gaussian mask (resolution 6.6 nm FWHM); 3D FEM | Lorentz images; DF holograms; exx/ezz maps vs FEM; profiles; zoom of hologram and exx map at two misfit dislocations next to STEM-HAADF and its GPA map; depth profiles for 5 process variants | precision = std in non-strained Si: 0.02-0.06 %; misfit (60 deg, 1/2<110>) dislocations visible as "rupture of the interference fringes"; DFEH and HAADF-GPA maps around them "fairly coherent" with the same mask |

## Paper entries

### P1. Boureau et al. 2020, J. Appl. Cryst. (DFEH vs HRXRD on 22 nm-node MOSFETs)

* Citation (READ on the PDF title page and running footer): V. Boureau, A. Durand, P. Gergaud,
  D. Le Cunff, M. Wormington, D. Rouchon, A. Claverie, D. Benoit, M. Hÿtch, "Dark-field electron
  holography as a recording of crystal diffraction in real space: a comparative study with
  high-resolution X-ray diffraction for strain analysis of MOSFETs", *J. Appl. Cryst.* **53**, 885-895
  (2020). doi:10.1107/S1600576720006020 (DOI printed in the PDF footer and matched by Crossref).
* URL read: https://hal.science/hal-03001931/document (author manuscript, 29 pages, HAL deposit
  2021-11-18). Label: SECTION_READ (full text of the accepted manuscript incl. figure captions; the
  figures themselves were not viewed as images).
* Instrument/conditions (READ, section 2.3): I2TEM-Toulouse, Hitachi HF-3300C, cold FEG, CEOS B-COR
  image corrector; 300 kV; Lorentz mode with the objective lens used as Lorentz lens; "spatial
  resolution of 0.5 nm" for the optics; two biprisms (to avoid Fresnel fringes); hologram fringe
  spacing 1.08 nm; reflections 004 and 220; specimen in two-beam condition; 4k x 4k CCD (Gatan
  USC1000), 10 s exposure, 0.1143 nm/pixel; FIB lamella about 110 nm thick; processing with HoloDark
  1.3 (HREM Research) in DigitalMicrograph; FEM with COMSOL.
* Theory (READ, section 3): geometric phase written as phi_G(r) = -2 pi g.u(r) (their Eq. 10);
  DFEH treated kinematically (WKB + weak-phase-object, Eqs. 11-24), sideband selection, inverse FT,
  strain from the displacement gradient (Eq. 25); 2D tensor needs two non-collinear g (cites Hÿtch
  et al. 2011). They state the WPO treatment is approximate and that dynamical two-beam theory (Lubk
  et al. 2014) "leads to a weighting of the geometric phase contribution" (section 5).
* Figures (READ from captions): Fig. 1 schematic + bright-field TEM of 3 repeat units; Fig. 2
  schematic of HRXRD and DFEH set-ups; Fig. 3 experimental X-ray RSM around 004; Fig. 4 (a) 004
  dark-field hologram with enlarged inset showing fringes, (b) geometric phase map (amorphous parts
  blanked), (c) displacement field of (004) planes, (d) out-of-plane strain eps_zz superimposed on a
  bright-field image; Fig. 5 RSMs computed from the DFEH displacement field before/after FEM
  thin-lamella correction + plot of satellite-peak positions; Fig. 6 processing flow chart showing the
  hologram FT around the carrier frequency side by side with the HRXRD RSM.
* Numbers (READ, sections 4.2, 4.3, 5): fringe contrast 13 % in the crystal; phase spatial resolution
  4 nm set by the Fourier mask radius; strain sensitivity 5e-4 "estimated ... from the standard
  deviation of the strain fluctuations in the region of the substrate where no strain should be
  present"; eps_zz about 1.65 % at S/D centre, 1.05 % near the edge; histogram maximum 1.17 % vs 1.18 %
  from the RSM peak; thin-lamella relaxation estimated 27 % in the S/D; hologram field of view 546 nm
  (FT sampling 2.14e-3 nm^-1); extinction distance of Si 004 quoted as 188 nm at their energy.
* Reference: the reference wave passes through unstrained Si substrate; strain is relative to the Si
  substrate lattice (READ, sections 2.3 and 4.2). No dislocation analysis (stacking faults are only
  noted in Fig. 1) (READ).
* Relevance (inference): template for the processing figure chain hologram -> FT/sideband -> phase ->
  displacement -> strain, for the "std of strain in an unstrained region" precision metric, and for
  the explicit statement of the mask-limited resolution.

### P2. L. Niermann, T. Niermann, M. Lehmann 2025, Ultramicroscopy (DFEH tilt series + scanning CBED of a 3D strain field)

* Citation (READ on the PDF first page): L. Niermann, T. Niermann, M. Lehmann, "Dynamical diffraction
  effects of inhomogeneous strain fields investigated by scanning convergent electron beam diffraction
  and dark field electron holography", *Ultramicroscopy* **271**, 114122 (2025), CC BY 4.0.
  doi:10.1016/j.ultramic.2025.114122 (printed on the PDF; Crossref agrees).
* URL read: https://depositonce.tu-berlin.de/bitstreams/aab621d1-471f-4d0f-8c5a-88a71642086f/download
  (TU Berlin repository copy; the PDF carries the journal layout and CC BY statement). ScienceDirect
  itself answered 403. Label: SECTION_READ (full text, figure captions; figures not viewed as images).
* Specimen (READ, 3.1): FIB lamella of GaN containing a 5 nm Al0.47Ga0.53N layer inclined 45 deg to the
  lamella surfaces, so the depth of the strain inhomogeneity varies linearly with x; thicknesses 50 nm
  and 115 nm (48 nm measured in the holograms).
* DFEH conditions (READ, 3.3): FEI Titan 80-300 "Berlin Holography Special", 300 kV, single biprism,
  20 um objective aperture selecting the (01-12) reflection (two-beam), reference wave from the GaN
  matrix below the layer; biprism skewed to the layer to reduce Fresnel-fringe artefacts; incident-beam
  tilt series along g by beam deflectors; 15 holograms x 5 s per tilt; reconstruction aperture radius
  1.16 nm^-1 with a 14th-order Butterworth soft edge; series averaged with drift compensation using
  holoaverage. Biprism voltage and fringe spacing: not stated in the text I read (NOT VERIFIED).
  SCBED conditions (READ, 3.2): JEOL GrandArm F2, 200 kV, 6.6 mrad semi-convergence, MerlinEM.
* Theory (READ, section 2): geometric phase phi_g(r,z) = -2 pi g.u(r,z) (Eq. 3) inserted into the
  Darwin-Howie-Whelan equations; only for a z-constant displacement is the DFEH phase the pure geometric
  phase; otherwise intensity and phase depend non-linearly on t, tilt and depth (READ). DFEH contrast
  C = sqrt(I_g(r) I_g(r_ref)) (Eq. 5), DFEH phase = phase(r) - phase(r_ref) (Eq. 6). Simulations: DHW
  multi-beam, systematic row up to +-(0448), RK4 step 0.1 nm, column approximation, PyCTEM; FEM for
  surface relaxation.
* Figures (READ from captions): Fig. 4 reconstructed DFEH contrast and phase at one tilt with the
  projected layer edges and the profile box; Fig. 5 measured vs calculated DFEH phase and contrast as
  (q, x) "tilt-position" maps; Fig. 10 calculated phase, DFEH contrast and intensity over a wider tilt
  range; Figs. 3, 6-8 SCBED (q, x) plots incl. effect of specimen curvature (C = 0.01467 nm^-2), defocus
  (+-1.5 um) and FEM surface relaxation; Fig. 9 FEM displacement fields u_x and u_z of the lamella.
* Measurements and processing facts (READ): phase gradient from thickness variation removed by
  subtracting a linear ramp so that phases above/below the layer are flat; global offset set to -pi/2
  above the layer; profiles averaged parallel to the layer; phases noisier where the amplitude is small
  (cites Röder et al. 2014 noise paper); "The (q, x) positions of the 2 pi-phase jumps exhibit an excellent
  agreement between the measurement and the calculation"; abrupt phase changes where the contrast
  vanishes, at t = n xi_g(q) (Eq. 9); intensities show a mid-plane symmetry (depth ambiguity) that the
  DFEH phase does NOT show (sections 5.1-5.2, using Lubk et al. 2014 Eq. B.6). No strain precision
  number, no strain map, no dislocation is reported (READ: the dislocation case is referred to ref. 25,
  i.e. P3 below).
* Relevance (inference): the closest published analogue of what a dynamical forward model of a buried
  strain source predicts for DFEH phase: phase depends on depth and excitation error, 2 pi jumps appear
  at amplitude zeros, and the comparison format is measured-vs-calculated phase/contrast maps across
  a tilt series. A reflection-mode simulation that reports phase vs depth and vs excitation error is
  directly comparable to Figs. 5 and 10.

### P3 (related method, not holography). T. Niermann, L. Niermann, M. Lehmann 2024, Nat. Commun. (dislocation type and depth from 4D-STEM)

* Citation (READ in the PMC JATS record): T. Niermann, L. Niermann, M. Lehmann, "Three dimensional
  classification of dislocations from single projections", *Nat. Commun.* **15**, 1356 (2024).
  doi:10.1038/s41467-024-45642-z, PMID 38355701, PMCID PMC10866901.
* URL read: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=10866901 (full JATS
  XML of https://pmc.ncbi.nlm.nih.gov/articles/PMC10866901/). Label: SECTION_READ (full text and
  captions; Supplementary not read).
* Conditions (READ, Methods): JEOL GrandArm F2, 300 kV, Cs-corrected STEM, 3.3 mrad semi-convergence,
  256 x 256 scan at 0.78 nm steps, MerlinEM, 1.3 ms dwell; GaN on sapphire, threading dislocations,
  systematic rows (0002) and (2-1-10).
* Method/figures (READ): 4D data reduced to (q, x) planes across a dislocation (Fig. 1); experimental
  vs simulated (q, x) planes plus mean-squared-error maps over specimen thickness t and dislocation
  depth d (Figs. 2, 3); DHW multi-beam simulation in column approximation, isotropic analytic
  dislocation displacement fields, RK4 step 0.1 nm, detector PSF from knife-edge MTF, Gaussian
  background model.
* Numbers (READ): best fits t = 132 nm, d = 55 nm (screw, b = [000-1]) and t = 172 nm, d = 85 nm
  (mixed, b = 1/3[-12-10]); depth precision claimed at the 5 nm step size; second-lowest MSE minimum
  42 % and 18 % above the global minimum; mid-plane ambiguity for centrosymmetric directions; "The
  reported thicknesses were verified by electron holography" (Supplementary Note 2, not read).
* Relevance (inference): the only paper found that recovers the DEPTH of individual dislocations from
  dynamical-diffraction contrast compared with simulation; its "simulated vs experimental map + MSE
  map over (t, d)" figure is a natural template for a buried-dislocation simulation paper.

### P4. Cho et al. 2019, Mater. Trans. (DFEH phase step at a planar defect: g.R selection)

* Citation (READ on the PDF first page): Y. Cho, K. Niitsu, Y. Midoh, K. Nakamae, D. Shindo, J.-M. Yang,
  Y. Murakami, "Suppressing Geometric Phase Shift Owing to Antiphase Boundaries in Dark-Field Electron
  Holography", *Materials Transactions* **60**(5), 698-703 (2019). doi:10.2320/matertrans.MC201809
  (printed on the PDF).
* URL read: https://www.jstage.jst.go.jp/article/matertrans/60/5/60_MC201809/_pdf (J-STAGE, 6 pages).
  Label: SECTION_READ (full text and captions; figures not viewed as images).
* Conditions (READ, 2.1): Hitachi HF3300S, 300 kV, two biprisms (to remove Fresnel fringes), Bragg
  reflection selected by the objective aperture, Gatan USC 4000 CCD; Fe70Al30 (B2) foil, thickness
  about 100 nm or less; reference region inside the specimen (APB-free matrix), not vacuum. Fringe
  spacing, biprism voltage, field of view: not stated in the text I read (NOT VERIFIED).
* Physics (READ, 3.1): within kinematical two-beam theory the phase shift across a planar fault is
  2 pi g.R (their Eq. 1; the phase symbol is garbled in the PDF text layer); for B2 APBs R = 1/2<111>,
  so superlattice 100 gives a pi step and fundamental 200 gives zero.
* Figures (READ from captions): Fig. 4 bright field and dark-field (100 and 200) images + sketch of
  object/reference regions; Fig. 5 holograms (000, 100, 200) and reconstructed phase images; Fig. 6
  phase line profiles across the APB for the three beams; Fig. 7 wavelet/hidden-Markov denoising of a
  dark-field hologram with intensity profiles.
* Numbers (READ, 3.2-3.3): measured APB phase step about 2.3 rad with the 100 reflection (vs pi
  expected kinematically; attributed to excitation error/multiple scattering, off-stoichiometry and
  order degree); no step above the uncertainty with 200; phase uncertainty about 0.3 rad "evaluated by
  the deviations between the observation and background fitting"; poor signal-to-noise of DF
  holograms is stated as the main limitation; averaging limited by beam damage/contamination.
* Relevance (inference): the cleanest published DFEH demonstration that a defect produces a phase
  discontinuity of 2 pi g.R whose measured size falls short of the kinematic value under dynamical
  conditions; the analogous statement for a dislocation is a 2 pi g.b winding (not measured here). Its
  "phase profile across the defect for several g, with the invisible g as a control" is a figure type a
  buried-dislocation simulation can mirror (e.g. (008) vs a g with g.b = 0).

### P5. Park et al. 2022, Adv. Sci. (dark-field INLINE holography vs STEM-GPA vs 4D-STEM vs 3D FEM)

* Citation (READ in the PMC JATS record): B. Park, J. K. Lee, C. T. Koch, M. Wölz, L. Geelhaar, S. H.
  Oh, "High-Resolution Mapping of Strain Partitioning and Relaxation in InGaN/GaN Nanowire
  Heterostructures", *Adv. Sci.* **9**(22), 2200323 (2022). doi:10.1002/advs.202200323, PMID 35665488,
  PMCID PMC9353496.
* URL read: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=9353496 (full JATS of
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9353496/). Label: SECTION_READ (main text and captions;
  Supporting Information, where the DIH raw data are, NOT read).
* Conditions (READ, Experimental): DIH on JEOL JEM-2200F, 200 kV, in-column omega filter (+-10 eV),
  10 um objective aperture selecting (11-20) or (0004); dark-field focal series from -8 to +8 um,
  2k x 2k UltraScan 1000, 6 s per image; phase from the FRWR algorithm. This is inline (focal-series)
  dark-field holography, NOT off-axis: there is no biprism (READ). STEM-GPA on ARM200F (200 kV);
  4D-STEM on ARM300F (300 kV, 8.3 mrad, OneView); 3D FEM in COMSOL.
* Figures (READ from captions): Fig. 2 FEM strain maps and profiles for 4 geometric models; Fig. 3
  STEM-GPA eps_xx/eps_zz maps side by side with beam-averaged FEM maps + profiles + bar chart of
  averaged values vs analytic and FEM; Figs. 4-5 the same region by STEM-GPA, DIH and FEM with three
  colour-coded line profiles each; Fig. 6 piezoelectric polarisation maps derived from strain.
  Through-focal DF series and reconstructed amplitude/phase are in Supplementary Figs. S4-S5 (not read).
* Numbers (READ, 2.3): STEM-GPA central-region averages eps_xx = 1.2 +- 0.12 % (InGaN QD) and
  1.02 +- 0.19 % (GaN QB) relative to a GaN reference region (unstrained GaN foot); analytic 0.80 % and
  FEM 0.98 % for the QB; GaN shell -0.3 +- 0.2 % vs FEM -0.5 %; eps_zz 4.3 +- 1.1 % and -1.9 +- 0.33 %;
  4D-STEM resolution about 2 nm (probe 0.2 nm, convergence broadening about 1 nm, bending about
  0.7 nm); STEM depth of field about 30 nm. DIH is described qualitatively as giving "much higher
  spatial resolution and strain sensitivity" and profiles that "match well" FEM; no DIH precision number
  is given in the main text I read (NOT VERIFIED whether the SI gives one). They note the MIP step
  (0.16 V InGaN/GaN) adds a phase step whose derivative gives interface peaks, judged negligible here.
* Relevance (inference): the standard modern comparison layout (same region by two or three strain
  techniques + projected FEM, with line profiles) that a simulation paper would be compared against;
  also an explicit example of separating a mean-inner-potential phase from the geometric phase.

### P6 (foundational, older). Hÿtch, Houdellier, Hüe, Snoeck 2010, J. Phys.: Conf. Ser. (HoloDark technique: phase decomposition, artefacts)

* Citation (READ on the PDF page header): M. J. Hÿtch, F. Houdellier, F. Hüe, E. Snoeck, "Dark-field
  electron holography for the mapping of strain in nanostructures: correcting artefacts and
  aberrations", *J. Phys.: Conf. Ser.* **241**, 012027 (2010) (EMAG 2009).
  doi:10.1088/1742-6596/241/1/012027 (printed on every page).
* URL read: https://hal.science/hal-01742031/document (HAL copy of the publisher PDF). Label:
  SECTION_READ (full text and captions; figures not viewed as images).
* Conditions (READ, section 1): SACTEM-Toulouse, Tecnai F20, 200 kV, CEOS corrector, rotatable
  biprism, 2k CCD; objective lens off, corrector transfer lens used as Lorentz lens ("pseudo-Lorentz"),
  later a CEOS aberration-corrected Lorentz mode; FIB specimens 100-200 nm thick; "Typical fringe
  spacings are 1-2 nm and hologram widths from 300-500 nm allowing lengthwise fields of view of
  several microns"; processing with a modified GPA Phase 2.0.
* Theory (READ, section 2): total phase of a Fourier component = crystalline + magnetic +
  electrostatic + geometric (their Eq. 3); geometric phase "-2 pi g.u(r)" (their Eq. 4, origin on a
  symmetry axis of the crystal); strain from the gradient, so constant crystalline/electrostatic terms
  drop out only if the specimen is uniformly thick. A two-beam condition was chosen "to maximise the
  diffracted intensity and to limit multi-beam dynamical scattering effects" (section 3).
* Figures (READ from captions; NB the caption numbering is offset from the text): schematic of
  conventional vs dark-field holography; bright-field image of a Si comb test structure under a
  Si3N4 stressor; (111) dark-field hologram with its FT and zoom, phase, amplitude, local variation of
  planar spacing and local lattice rotation (+-2 % and +-2 deg scales); DF and BF holograms and phases
  of the same area and their difference (thickness-artefact removal); rotation maps before/after
  correction; (004) DF holograms and deformation maps in pseudo-Lorentz vs aberration-corrected
  Lorentz mode.
* Numbers and procedures (READ, sections 3-4): no fringes in vacuum in a DF hologram except biprism
  Fresnel fringes; thickness (curtaining) artefacts removed by subtracting the bright-field-hologram
  phase; Fresnel-fringe artefacts removed by Fourier filtering; strain precision "2.10-4 at 4 nm spatial
  resolution" (quoted from their ref. 10, Hüe et al. APL 2009, not read here); aberration-corrected
  Lorentz mode gave a deformation map with "signal-to-noise 60% higher" with identical processing.
* Nature 2008 (the founding paper): only the PubMed abstract was read (PMID 18563161, URL
  https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=18563161&rettype=abstract):
  M. Hÿtch, F. Houdellier, F. Hüe, E. Snoeck, "Nanoscale holographic interferometry for strain
  measurements in electronic devices", Nature 453(7198), 1086-1089 (2008), doi:10.1038/nature07049.
  The abstract claims high precision "with nanometre spatial resolution and for micrometre fields of
  view" and applicability to "relatively thick samples, thus reducing the influence of thin-film
  relaxation effects". Its figures and numbers were NOT read (paywalled; HAL record has no file).
  Label: METADATA_VERIFIED + abstract read (PubMed).

### P7. Denneulin et al. 2018, J. Phys.: Condens. Matter (DFEH of ferroelastic domains in PZT, vs HRTEM-GPA and FEM)

* Citation (READ on the PDF): T. Denneulin, N. Wollschläger, A. S. Everhardt, S. Farokhipoor,
  B. Noheda, E. Snoeck, M. Hÿtch, "Local deformation gradients in epitaxial Pb(Zr0.2Ti0.8)O3 layers
  investigated by transmission electron microscopy", *J. Phys.: Condens. Matter* **30**, 215701 (2018).
  doi:10.1088/1361-648X/aabd00.
* URL read: https://pure.rug.nl/ws/files/60328898/Denneulin_2018_J._Phys._Condens._Matter_30_215701_1_.pdf
  (University of Groningen repository, publisher's PDF; linked from HAL record hal-01838701). Label:
  SECTION_READ (full text and captions; figures not viewed as images).
* Conditions (READ, section 2): DFEH on Hitachi HF-3300 (I2TEM), 300 kV, cold FEG, specimen in the
  upper (Lorentz, field-free) stage, CEOS B-COR, four biprisms available; double-biprism set-up to
  avoid Fresnel fringes; two-beam condition a few degrees off zone axis, beam tilted to put g on axis,
  objective aperture; (002) and (200) holograms for each region; fringe spacing 2 nm; hologram width
  300 nm; FIB lamellae 100-150 nm; HoloDark processing with half-cosine Fourier mask; projector- and
  camera-distortion correction; extra 2 nm Gaussian smoothing of the deformation maps; HRTEM-GPA on a
  Tecnai (200 kV) for comparison; 2D anisotropic FEM (COMSOL).
* Numbers (READ, section 1 and 3): DFEH "strain sensitivity is +-0.1% and the spatial resolution is
  6 nm" vs HRTEM-GPA "2 nm" and "+-0.5%"; abstract: "good sensitivity (0.1%) and a large field-of-view
  (hundreds of nanometers)"; reference lattice = SrTiO3 substrate; measured eps_zz 5.2 % -> 6.3 % across
  a c-domain (gradients about 1e5 m^-1), rotations +-0.4 deg (+-0.1 deg), eps_xx 1.1 % -> 1.6 %.
* Figures (READ from captions): HRTEM + GPA maps of eps_zz, eps_xx, eps_xz, R_xz with FEM; experimental
  vs simulated profiles (Fig. 3, profiles averaged over 10 nm parallel to the walls); (002) and (200)
  DF holograms, sketches, experimental vs FEM eps_zz/eps_xx/eps_xz/R_xz maps and profiles (Figs. 4-6);
  Fig. 7 a (002) DF hologram, a numerically magnified moiré of its fringes (hologram superimposed
  with a constant-spacing fringe pattern) and the same moiré computed from FEM.
* Dislocations (READ, 3.2): the eps_xx map "contains vertical lines where the deformation appears to
  vary abruptly. These are related to vertical dark lines in the (2 0 0) hologram ... and most probably
  correspond to threading dislocations"; artefacts in eps_xz where the (200) fringe contrast is low.
  No Burgers-vector or phase-winding analysis is made (READ).
* Relevance (inference): shows how dislocations appear incidentally in DFEH (dark lines in the
  hologram, abrupt jumps in the strain map, low-contrast artefacts) and gives the standard
  "experimental vs FEM maps + profiles" layout and the numerical-moiré visualisation of fringe bending
  (Fig. 7), which a simulation can reproduce directly from its hologram.

### P8 (older, included for its dislocation content). Denneulin, Cooper, Hartmann, Rouvière 2012, J. Appl. Phys. (DFEH of strained pMOSFETs incl. misfit dislocations, vs FEM and STEM-GPA)

* Citation (READ on the PDF): T. Denneulin, D. Cooper, J.-M. Hartmann, J.-L. Rouvière, "The addition
  of strain in uniaxially strained transistors by both SiN contact etch stop layers and recessed SiGe
  sources and drains", *J. Appl. Phys.* **112**, 094314 (2012). doi:10.1063/1.4764045.
* URL read: https://hal.science/hal-02145343/document (HAL copy of the AIP PDF). Label: SECTION_READ
  (sections I-VIII read in the text layer; captions of Figs. 1-8 read; figures not viewed as images).
* Conditions (READ, section II): FEI Titan, 200 kV, objective lens off, Lorentz lens on; conventional
  single-biprism off-axis set-up with the biprism "biased with a voltage of +180 V corresponding to a
  fringe spacing of 2 nm"; 10 um objective aperture selecting (004) or (220); "Acquisitions were
  performed for 64 s for signal-to-noise improvement"; FIB [110] lamellae 100-200 nm; spatial
  resolution 6.6 nm "according to the full width at half maximum (FWHM) of the inverse Fourier
  transform of the Gaussian mask"; 3D FEM (COMSOL) averaged over the foil thickness; crystalline
  thickness by CBED.
* Precision definition and values (READ, section III-IV): "The precision is usually defined by the
  standard deviation of the strain calculated in a non-strained region of the substrate": 0.04 %
  (exx) and 0.02 % (ezz) for one sample, 0.03 % and 0.06 % for another; strain defined relative to the
  relaxed Si substrate, (d_ROI - d_Si)/d_Si; device-to-device variation > 0.1 % noted. The
  introduction cites (not read) Lorentz-mode DFEH sensitivity 2e-4 at 5 nm resolution over about
  600 x 600 nm^2, CBED 2e-4 and NBED 6e-4.
* Dislocations (READ, sections IV-V and Fig. 4 caption): misfit dislocations at the (001) and inclined
  (111) Si/SiGe interfaces; "relaxation in the SiGe region flows from the dislocations"; in the (220)
  DF hologram two misfit dislocations "can be seen by the rupture of the interference fringes"; they
  were identified (STEM-HAADF) as 60 deg dissociated dislocations with 1/2<110> Burgers vectors; the
  DFEH exx map around them is compared with a GPA exx map from a STEM-HAADF image processed with the
  same Gaussian mask (radius 3 sigma = 0.17 nm^-1), and the two maps are "fairly coherent"; the
  conclusion states DFEH has "a nanometric spatial resolution that allows to map the strain field
  around dislocations". No phase-winding / g.b counting is reported (READ).
* Other figure facts (READ from captions): Lorentz images; (220) and (004) DF holograms with gates
  drawn on; exx/ezz maps; FEM maps; line profiles averaged over 6 nm; Fig. 5 (220) holograms before
  and after silicidation; Fig. 8 depth profiles of exx in the channel for five process
  configurations, averaged over 15 nm, plus sums of individual cases; regions of low fringe contrast
  in the (004) hologram caused by surface relaxation of the lamella and plane curvature, giving noise
  in the strain map.
* Relevance (inference): the only openly readable DFEH paper found that shows dislocations directly
  in a dark-field hologram (fringe "rupture") and a DFEH vs GPA strain map around them with the
  reconstruction mask stated; also gives the biprism voltage, fringe spacing, exposure and the
  "std in the unstrained substrate" precision recipe in one place.
