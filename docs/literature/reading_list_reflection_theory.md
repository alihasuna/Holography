# Reading list: theory of reflection electron diffraction and imaging

Status: COMPLETE (2026-10-15, literature-researcher agent). 35 items: 10 MUST, 12 SHOULD, 13 OPTIONAL. Nothing here may be cited for content until it is SECTION_READ; see section 0.

Scope: what a PhD student must download to ground the forward model of this repository
(reflection-mode, RHEED-geometry dark-field electron holography at 200 keV and about 1 degree glancing
incidence; next milestone reflection-mode electron ptychography) in the theory of reflection high-energy
electron diffraction (RHEED) and reflection electron microscopy (REM).


## 0. Access log, labels and how to use this list

**What was done (2026-10-15).** Network access was available this time, unlike in the session that built
`docs/literature/references.bib`. Routes that worked and were used:

* **Crossref REST API** (`api.crossref.org/works/<DOI>` and `?query.bibliographic=`): every DOI, volume,
  issue, page range and author list in the tables below was read from the Crossref record.
  This gives **METADATA_VERIFIED**. It was also used to obtain the chapter list of the OUP and Springer
  books, because Crossref holds one record per chapter, with its title and page range.
* **Cambridge Core** book pages: the tables of contents of Ichimiya and Cohen (2004) and Z. L. Wang
  (1996) were read on the publisher's page. For some chapters, the free "Summary" extract on the chapter
  page was also read. These are labelled **TOC_READ** (a form of METADATA_VERIFIED) and, where the
  summary was read, **SUMMARY_READ**. Neither label counts as SECTION_READ for the content.
* **raw.githubusercontent.com and arXiv** (see section 4).

**Blocked hosts.** These returned site-level 403s, JavaScript challenges or authentication redirects;
the proxy itself recorded no failures.

* **journals.iucr.org:** HTTP 403. All Acta Cryst. A and J. Appl. Cryst. articles could not be opened.
* **academic.oup.com:** HTTP 403. The Peng, Dudarev and Whelan chapter pages could not be opened.
* **link.springer.com:** JavaScript client challenge, or a redirect to idp.springer.com. The Kirkland
  chapter pages could not be opened.

**What nothing here is.** No full text of any paper or chapter in this list was read. So nothing below
may be cited as the source of an equation, value or figure. The "WHAT TO READ" locators are chapter
titles and page ranges from publisher or Crossref metadata; they are not claims about content. Where a
chapter summary was read, the facts it gives are quoted in section 6.

**Labels used in the tables.**
* `MV-CR`: METADATA_VERIFIED from the Crossref record (DOI, authors, journal, volume, issue, pages).
* `TOC`: the publisher's or Crossref's chapter list, read.
* `SUM`: the publisher's free chapter summary, read.
* `README`: the GitHub README, read.
* `ABS-arXiv`: the arXiv abstract page, read.
* `NOT VERIFIED`: anything else.

**Priorities.**
* **MUST:** needed to defend a step of the current pipeline.
* **SHOULD:** needed for the next milestone (independent validation, M2) or to source a placeholder value.
* **OPTIONAL:** background, or an alternative method.

**Cross-reference.** The IDs in `references.bib` (B07, P19, ...) are given where an entry already exists.
Several bib entries are corrected or completed here (section 6.3); `references.bib` itself was NOT edited.

## 1. Dynamical RHEED theory (Bloch-wave, Maksym-Beeby, Ichimiya; rocking curves; surface resonance)

| ID | PRIORITY | Citation (DOI / ISBN) | WHAT TO READ | WHY (pipeline step) | ACCESS | VERIFIED |
|---|---|---|---|---|---|---|
| RT01 (bib B07) | **MUST** | Ichimiya, A. & Cohen, P. I. *Reflection High-Energy Electron Diffraction.* Cambridge University Press, print 13 Dec 2004. DOI 10.1017/CBO9780511735097. ISBN 9780521453738 (hb), 9780521184021 (pb), 9780511735097 (online). | ch. 4 "Wave properties of electrons" pp. 19-27 and ch. 5 "The diffraction conditions" pp. 28-42 (refraction is expected here from the titles; NOT VERIFIED); ch. 11 "Fourier components of the crystal potential" pp. 154-160; **ch. 12 "Dynamical theory - transfer matrix method" pp. 161-172** (Ichimiya's method, the one used by sim-trhepd-rheed); ch. 14 "Dynamical theory - integral method" pp. 192-194; App. F "Optimization of dynamical calculation" pp. 328-332. Skim: ch. 7 "Kikuchi and resonance patterns" pp. 62-76; ch. 13 "embedded R-matrix method" pp. 173-191; ch. 16 "Inelastic scattering in a crystal" pp. 211-233. | Refraction and the internal/external angle (step 3a illumination angle; geometric model q_int/q_ext; source-map row SM04). Theory of the flat-surface rocking curve (`scripts/rocking_flat.py`, 16.93 mrad for (008)). Surface-parallel slicing for the M2 benchmark. | Library e-book (Cambridge Core). | `TOC` read on the Cambridge Core book page. `SUM` read for ch. 7, 11, 12 and 13. Chapter DOIs .013 (ch. 12) and .014 (ch. 13) read on the chapter pages. |
| RT02 (bib B08) | **MUST** | Peng, L.-M., Dudarev, S. L. & Whelan, M. J. *High-Energy Electron Diffraction and Microscopy.* Oxford University Press. Crossref year 2004 (the year conflict with the 2003 print year in `references.bib` is unresolved). DOI 10.1093/oso/9780198500742.001.0001. ISBN 9780198500742 (Crossref also lists 9781383019926). | **ch. 5 "Dynamical Theory III. Reflection High-Energy Electron Diffraction" pp. 117-185** (DOI ...003.0005); ch. 6 "Resonance Effects in Transmission and Reflection High-Energy Electron Diffraction" pp. 186-227; **ch. 13 "The Atomic Scattering Factor and the Optical Potential" pp. 427-453**; ch. 14 "Temperature-Dependent Debye-Waller Factors" pp. 454-469. Background: ch. 3 "Dynamical Theory I. General Theory" pp. 54-74; ch. 4 "Dynamical Theory II. THEED" pp. 75-116; ch. 7-8 "Diffuse and Inelastic Scattering" pp. 228-310; App. A-D pp. 470-500 (contents not seen). | Bragg-case reference solution for the phase-validation ladder (M2). Optical (absorptive) potential to replace the V_i = 0.05 V_r placeholder (README limitation 2; experiment input 21). Debye-Waller factor of Si used in the slice potential (step 3a). Resonance conditions when choosing the operating angle. | Library e-book (Oxford Academic; host blocked here). | `TOC`: all 14 chapters and 4 appendices, with page ranges, from Crossref chapter records. Book abstract and the abstracts of ch. 5, 6, 7, 8 and 13 read in the Crossref deposit. |
| RT03 | SHOULD | Maksym, P. A. & Beeby, J. L. (1981). A theory of RHEED. *Surface Science* 110(2), 423-438. DOI 10.1016/0039-6028(81)90649-X. | Whole paper (16 pp.). | The original 2-D-periodic (LEED-type) dynamical RHEED theory for rocking curves. The Ichimiya-Cohen ch. 12 summary says that ch. 12-14 present it, so read it after RT01. Rocking-curve benchmark. | Library journal (Elsevier). | `MV-CR` (not in `references.bib`). |
| RT04 (bib P17) | SHOULD | Ichimiya, A. (1983). Many-beam calculation of reflection high energy electron diffraction (RHEED) intensities by the multi-slice method. *Jpn. J. Appl. Phys.* 22(1R), 176. DOI 10.1143/JJAP.22.176. **Plus the correction:** Ichimiya, A. (1985). *Jpn. J. Appl. Phys.* 24(10R), 1365, DOI 10.1143/JJAP.24.1365. | Both, in full. Crossref gives only the first page, 176; the sim-trhepd-rheed README prints "176-180". | The algorithm inside sim-trhepd-rheed (benchmark, RT27); the surface-parallel slicing alternative to this repository's beam-perpendicular slicing. The 1985 correction was not known to `references.bib`. | Library journal (IOP/JSAP). | `MV-CR` for both. The DOI of P17 is now verified, so the bib can admit it. |
| RT05 (bib P20) | OPTIONAL | Ma, Y. & Marks, L. D. (1989). Bloch-wave solution in the Bragg case. *Acta Cryst.* A45(2), 174-182. DOI 10.1107/S0108767388010888. | Abstract and sect. I (pp. 174-175, read); the rest for the current-flow selection of Bloch waves. | Bragg-case Bloch waves; the abstract lists resonance diffraction, splitting of spots from stepped surfaces, and the reflection equivalent of thickness fringes. | **Open:** author copy at numis.northwestern.edu/Research/Articles/1989/ ("7Bloch wave solutions in the Bragg case.pdf"), opened. | `MV-CR`. SECTION_READ of the abstract. The page range 174-182 is now settled (the bib had left it open). |
| RT06 (bib U04 -> P29) | OPTIONAL | Zhao, T. C., Poon, H. C. & Tong, S. Y. (1988). Invariant-embedding R-matrix scheme for reflection high-energy electron diffraction. *Phys. Rev. B* 38(2), 1172-1182. DOI 10.1103/PhysRevB.38.1172. | Only if implementing an R-matrix solver; Ichimiya-Cohen ch. 13 presents the method. | An alternative stable rocking-curve solver. | Library journal (APS). | `MV-CR`. This resolves the placeholder title of bib entry U04. |
| RT07 | OPTIONAL | Colella, R. (1972). *n*-Beam dynamical diffraction of high-energy electrons at glancing incidence. General theory and computational methods. *Acta Cryst.* A28(1), 11-15. DOI 10.1107/S0567739472000026. | Whole paper (5 pp.). | Historical origin of n-beam glancing-incidence theory, cited by Ma and Marks (1990, sect. I) for the finite-slab approach. | Library journal (IUCr; host blocked here). | `MV-CR`. |

## 2. REM imaging theory; contrast of steps and dislocations

| ID | PRIORITY | Citation (DOI / ISBN) | WHAT TO READ | WHY (pipeline step) | ACCESS | VERIFIED |
|---|---|---|---|---|---|---|
| RT08 (bib ZLWANG96) | **MUST** | Wang, Z. L. *Reflection Electron Microscopy and Spectroscopy for Surface Analysis.* Cambridge University Press, print 23 May 1996. DOI 10.1017/CBO9780511525254. ISBN 9780521482660 (hb), 9780521017954 (pb), 9780511525254 (online). | **ch. 6 "Contrast mechanisms of reflected electron imaging" pp. 166-198** (chapter DOI ...525254.008); ch. 3 "Dynamical theories of RHEED" pp. 60-88; ch. 4 "Resonance reflections in RHEED" pp. 89-128; ch. 5 "Imaging surfaces in TEM" pp. 131-165; ch. 9 "Phonon scattering in RHEED" pp. 243-269; App. B "The crystal inner potential and electron scattering factor" pp. 369-373. Use App. F "A bibliography of REM, SREM and REELS" (pp. 403-418) to find primary papers. | Step contrast (strip 2, the calibration step) and diffraction contrast of buried dislocations (strip 3). The ch. 6 summary separates phase (Fresnel) contrast of atom-high steps from diffraction (Bragg) contrast due to dislocations and strain. INFERENCE: these correspond to the repository's two signals, the step phase (strip 2) and the strain contrast of the buried dislocation (strip 3). It also covers resonance (operating angle), TDS (absorption) and the inner potential (refraction). | Library e-book (Cambridge Core). | `TOC` read on the Cambridge Core book page. `SUM` read for ch. 2, 3, 4, 5, 6 and 9. The App. B page gave no summary. |
| RT09 (bib U01 resolved) | **MUST** | McCoy, J. M. & Maksym, P. A. (1994). Multiple scattering calculations of step contrast in REM images of the Si(001) surface. *Surface Science* 310(1-3), 217-225. DOI 10.1016/0039-6028(94)91386-2. | Whole paper (9 pp.). | The closest published dynamical simulation of this repository's own calibration object: atomic steps on Si(001) in REM. Use it as the acceptance test for step contrast in the multislice (step 6 metric "step phase"). | Library journal (Elsevier). | `MV-CR` (abstract not available in Crossref; content NOT read). |
| RT10 (bib U01 resolved) | SHOULD | McCoy, J. M. & Maksym, P. A. (1993). Simulation of reflection electron microscopy images: application to high-resolution imaging of the Si(001)2 x 1 surface. *Surface Science* 297(2), 113-126. DOI 10.1016/0039-6028(93)90254-H. Companion: McCoy & Maksym (1993). Simulation of high-resolution REM images. *Surface Science* 298(2-3), 468-472. DOI 10.1016/0039-6028(93)90062-O. | Method sections of the 297 paper first. | REM image-simulation method behind RT09. The (2x1) reconstruction is absent from the repository (README limitation 3). | Library journal (Elsevier). | `MV-CR` for both. This settles the "two titles / three years" confusion of bib entry U01: there are three distinct papers (1993 x 2, 1994). |
| RT11 (bib P26) | SHOULD | Yao, N. & Cowley, J. M. (1990). Electron diffraction conditions and surface imaging in reflection electron microscopy. *Ultramicroscopy* 33(4), 237-254. DOI 10.1016/0304-3991(90)90041-J. | Whole paper (18 pp.). | Choosing the operating angle: the Bragg-Bragg versus Bragg-channelling resonance conditions, and double-contour step contrast (abstract level, from the bib entry). It decides whether the 16.93 mrad flat-surface peak is the right imaging condition. | Library journal (Elsevier). | `MV-CR`. The DOI is now verified (the bib gave only the PII). |
| RT12 (bib P23) | SHOULD | Yagi, K. (1993). Reflection electron microscopy: studies of surface structures and surface dynamic processes. *Surface Science Reports* 17(6), 307-362. DOI 10.1016/0167-5729(93)90002-7. Also: Yagi, K. (1987). Reflection electron microscopy. *J. Appl. Cryst.* 20(3), 147-160, DOI 10.1107/S0021889887086916; and Yagi, K. (1993). "RHEED and REM", in Cowley, J. M. (ed.), *Electron Diffraction Techniques* vol. 2, OUP, pp. 260-308, DOI 10.1093/oso/9780198557333.003.0003. | The 1993 *Surf. Sci. Rep.* review (56 pp.): its sections on image contrast of steps and dislocations (section numbers NOT VERIFIED). The other two are alternatives. | Experimental REM practice (foreshortening, step and dislocation images, defocus) against which simulated images will be judged. | Library journal (Elsevier / IUCr); the chapter is a library e-book (Oxford Academic). | `MV-CR` for all three. |
| RT13 (bib P24, P25) | OPTIONAL | Uchida, Y. & Lehmpfuhl, G. (1987). Observation of double contours of monoatomic steps on single crystal surfaces in reflection electron microscopy. *Ultramicroscopy* 23(1), 53-59. DOI 10.1016/0304-3991(87)90226-9. And: Uchida, Y., Jäger, J. & Lehmpfuhl, G. (1984). Direct imaging of atomic steps in reflection electron microscopy. *Ultramicroscopy* 13(3), 325-327. DOI 10.1016/0304-3991(84)90210-9. | Figures of the step images. | Experimental targets for step contrast. | Library journal (Elsevier). | `MV-CR`. **Corrections to the bib:** first author "Y. Uchida" (bib: "N."); pages 53-59 (bib: 53-60) and 325-327 (bib: 325-328); second 1984 author "J. Jäger" in Crossref (bib: "W."). |
| RT14 (bib U02 resolved) | OPTIONAL | Beeby, J. L. (1993). Dynamical theory of RHEED from stepped surfaces. *Surface Science* 298(2-3), 307-315. DOI 10.1016/0039-6028(93)90043-J. Also: Ichimiya, A. (1987). RHEED intensities from stepped surfaces. *Surface Science* 187(1), 194-200. DOI 10.1016/S0039-6028(87)80131-0. | Whole papers. | Diffraction (not imaging) theory for vicinal and stepped surfaces: the spot splitting expected from the strip geometry. | Library journal (Elsevier). | `MV-CR`. This resolves bib U02 (author Beeby). |
| RT15 | OPTIONAL | Liu, J. & Cowley, J. M. (1993). Scanning reflection electron microscopy and associated techniques for surface studies. *Ultramicroscopy* 48(4), 381-416. DOI 10.1016/0304-3991(93)90116-F. | Sections on probe formation and contrast (section numbers NOT VERIFIED). | Scanning (focused-probe) reflection imaging: the precursor geometry of **reflection-mode ptychography**, the next milestone. | Library journal (Elsevier). | `MV-CR`. |

## 3. Refraction, mean inner potential, absorption (imaginary potential) and thermal diffuse scattering

The refraction formula itself is treated in RT01 (ch. 4-5), RT02 (ch. 5) and RT08 (ch. 2-3, App. B). The
items below supply the numbers the pipeline currently assumes: V0 = 12 V, V_i = 0.05 V_r, and the
Debye-Waller factor.

| ID | PRIORITY | Citation (DOI / ISBN) | WHAT TO READ | WHY (pipeline step) | ACCESS | VERIFIED |
|---|---|---|---|---|---|---|
| RT16 | **MUST** | Peng, L.-M., Ren, G., Dudarev, S. L. & Whelan, M. J. (1996). Robust parameterization of elastic and absorptive electron atomic scattering factors. *Acta Cryst.* A52(2), 257-276. DOI 10.1107/S0108767395014371. | Whole paper (20 pp.): the fitting form, its validity range in s, and the absorptive part and how it depends on the Debye-Waller factor. Table and section numbers NOT VERIFIED. | **Absorption** and the **potential.** The code already uses the "Peng 1996" elastic parameterisation through abTEM's `peng_high.json` (source map SM17, "Peng et al. 1996 not read"), so this paper is a provenance gap in the current code. Its absorptive counterpart is the sourced replacement for the V_i = 0.05 V_r placeholder, which sets the amplitude contrast (README limitation 2). | Library journal (IUCr; host blocked here). | `MV-CR`. |
| RT17 | SHOULD | Peng, L.-M., Ren, G., Dudarev, S. L. & Whelan, M. J. (1996). Debye-Waller factors and absorptive scattering factors of elemental crystals. *Acta Cryst.* A52(3), 456-470. DOI 10.1107/S010876739600089X. | The Si entries and how the temperature dependence enters. Locators NOT VERIFIED. | A sourced Si Debye-Waller factor (step 3a potential) and temperature-dependent absorptive factors for 200 keV. | Library journal (IUCr). | `MV-CR`. |
| RT18 | SHOULD | Kruse, P., Schowalter, M., Lamoen, D., Rosenauer, A. & Gerthsen, D. (2006). Determination of the mean inner potential in III-V semiconductors, Si and Ge by density functional theory and electron holography. *Ultramicroscopy* 106(2), 105-113. DOI 10.1016/j.ultramic.2005.06.057. | The Si result, its uncertainty, and how the DFT value differs from the neutral-atom (independent-atom) value. | **Refraction.** V0 is a first-order systematic (physics_summary section 3: -0.34 rad/V at (4,-4,4)). The pipeline uses V0 = 12 V (ASSUMPTION), while the MIP of its own Peng potential is 13.91 V (SM17). This paper is a candidate sourced value; its number was NOT read here. | Library journal (Elsevier). | `MV-CR` (title, authors, pages). The Si value is NOT VERIFIED. |
| RT19 | SHOULD | Peng, L.-M. & Cowley, J. M. (1989). Thermal diffuse scattering and REM image-contrast preservation. *Ultramicroscopy* 29(1-4), 168-174. DOI 10.1016/0304-3991(89)90243-X. | Whole paper (7 pp.). | **TDS in reflection imaging.** Whether TDS electrons keep REM contrast decides whether TDS can be treated as pure absorption (current code) or needs a frozen-phonon or incoherent term in the hologram ensemble (physics_summary section 1, step 4). | Library journal (Elsevier). | `MV-CR`. |
| RT20 | OPTIONAL | Peng, L.-M. (2005). Electron atomic scattering factors, Debye-Waller factors and the optical potential for high-energy electron diffraction. *Microscopy* (J. Electron Microsc.) 54(3), 199-207. DOI 10.1093/jmicro/dfi045. Longer review: Peng, L.-M. (1999). Electron atomic scattering factors and scattering potentials of crystals. *Micron* 30(6), 625-648. DOI 10.1016/S0968-4328(99)00033-5. | The 2005 review (9 pp.) as an entry point to RT16-RT17. | Overview of the optical potential and mean inner potential (absorption, refraction). | Library journal (Oxford Academic, blocked here; Elsevier). | `MV-CR` for both. |
| RT21 | OPTIONAL | Bird, D. M. & King, Q. A. (1990). Absorptive form factors for high-energy electron diffraction. *Acta Cryst.* A46(3), 202-208. DOI 10.1107/S0108767389011906. Weickenmeier, A. & Kohl, H. (1991). Computation of absorptive form factors for high-energy electron diffraction. *Acta Cryst.* A47(5), 590-597. DOI 10.1107/S0108767391004804. | The algorithms. | An independent route to the phonon absorptive potential, to cross-check RT16 (absorption). | Library journal (IUCr). | `MV-CR`. |
| RT22 | OPTIONAL | Gajdardziska-Josifovska, M., McCartney, M. R., de Ruijter, W. J., Smith, D. J., Weiss, J. K. & Zuo, J. M. (1993). Accurate measurements of mean inner potential of crystal wedges using digital electron holograms. *Ultramicroscopy* 50(3), 285-299. DOI 10.1016/0304-3991(93)90197-6. | The method and the list of materials measured (whether Si is included is NOT VERIFIED). | A holographic measurement route for V0 (refraction), relevant to experiment input item 20. | Library journal (Elsevier). | `MV-CR`. |
| RT23 | OPTIONAL | Wang, Z. L. (1995). *Elastic and Inelastic Scattering in Electron Diffraction and Imaging.* Plenum (Springer record). DOI 10.1007/978-1-4899-1579-5. ISBN 9781489915795 (Crossref also lists 9781489915818). | ch. 5 "Diffraction and Imaging of Reflected High-Energy Electrons from Bulk Crystal Surfaces" pp. 97-126; ch. 6 "Inelastic Excitations and Absorption Effect in Electron Diffraction" pp. 129-187; ch. 7 "Semiclassical Theory of Thermal Diffuse Scattering" pp. 189-216; ch. 3 "Dynamic Elastic Electron Scattering II: Multislice Theory" pp. 61-81. | Absorption and TDS theory, including a multislice treatment of inelastic scattering (ch. 11, pp. 265-320). | Library e-book (Springer). | `TOC` from Crossref chapter records. |

## 4. Multislice: general references, grazing/reflection validity, edge effects, boundaries; reflection codes as benchmarks

### 4a. Multislice theory

| ID | PRIORITY | Citation (DOI / ISBN) | WHAT TO READ | WHY (pipeline step) | ACCESS | VERIFIED |
|---|---|---|---|---|---|---|
| RT24 (bib B06) | **MUST** | Kirkland, E. J. *Advanced Computing in Electron Microscopy*, 3rd ed. Springer, 2020. DOI 10.1007/978-3-030-33260-0. ISBN 9783030332594 (print), 9783030332600 (eBook). | **ch. 6 "Theory of Calculation of Images of Thick Specimens" pp. 143-195** (DOI ..._6): the multislice derivation, propagator, slice thickness. **ch. 4 "Sampling and the Fast Fourier Transform" pp. 81-98** (..._4): band limit and aliasing. ch. 7 "Multislice Applications and Examples" pp. 197-239 (..._7). The appendix on atomic potentials and scattering factors (its letter and pages are NOT VERIFIED). | **Multislice validity** (step 3a): exact versus paraxial propagator (SM08), the 2/3 band limit checked at every run (SM15), the slice thickness (1.92 Å), and the projected-potential parameterisation and its MIP (SM17). | Library e-book (SpringerLink; host blocked here). | `TOC` from Crossref chapter records (8 chapters). CAUTION: a search-engine summary gave different 3rd-edition chapter titles (e.g. "Calculating Images of Thick Specimens"); it is not evidence. Check the printed contents page. |
| RT25 (bib P19, P18) | **MUST** | Peng, L.-M. & Cowley, J. M. (1988). A multislice approach to the RHEED and REM calculation. *Surface Science* 199(3), 609-622. DOI 10.1016/0039-6028(88)90925-9. With: Peng, L.-M. & Cowley, J. M. (1986). Dynamical diffraction calculations for RHEED and REM. *Acta Cryst.* A42(6), 545-552. DOI 10.1107/S0108767386098756. | Both in full: the incident-wave construction, the cell geometry, the absorption used and the step/defect simulations. | **Multislice validity**: this is the method the repository implements (slices perpendicular to the surface, a tilted beam launched in vacuum, beam-direction propagation). Read it before claiming the kernel is a valid reflection solver. | Library journal (Elsevier; IUCr). | `MV-CR` for both. The DOI of P18 is now verified (the bib withheld it). |
| RT26 (bib P21) | **MUST** | Ma, Y. & Marks, L. D. (1990). Bloch waves and multislice in transmission and reflection diffraction. *Acta Cryst.* A46(1), 11-32. DOI 10.1107/S0108767389009141. **Erratum:** *Acta Cryst.* A46(7), 626, DOI 10.1107/S0108767390004810. | Abstract and sect. I (pp. 11-12); sect. IV "Consistency in reflection" (from p. 13), incl. IV.1 "Effect of absorption" (p. 20); **sect. V "Comparison with the solution in multislice only" (p. 30)**; **sect. VI "Discussion" (pp. 31-32)**. Get the erratum too. | **Multislice validity.** Sect. V tests exactly this repository's illumination: a Gaussian-smoothed plane wave tilted towards the surface, launched in vacuum. Sect. VI names the edge effects of periodic continuation (quotes in section 6.1). | **Open:** author copy at numis.northwestern.edu/Research/Articles/1990/ ("2Bloch Waves and Multislice in Transmission and Reflection Diffraction.pdf"), opened. | SECTION_READ (pp. 11-13, 30-32) + `MV-CR`. The bib's pages 11-32 and the DOI are now confirmed. |
| RT27 | **MUST** | Ma, Y. & Marks, L. D. (1991). A robust solution for RHEED. *Acta Cryst.* A47(6), 707-715. DOI 10.1107/S0108767391005871. | Abstract (p. 707); **the edge-patching construction, pp. 708-709**; the discussion of patching (p. 713). | **Edge patching / periodic continuation** (step 3a): the published remedy for the edge effects named in RT26. It is a candidate design change for `forward/multislice.py`, whose current answer is a long cell (about 3100 slices) plus an absorber. | **Open:** author copy at numis.northwestern.edu/Research/Articles/1991/1991_Robust_Solution.pdf, opened. | SECTION_READ (pp. 707-709, 713) + `MV-CR`. Not in `references.bib`. |
| RT28 (bib P22) | SHOULD | Ma, Y. & Marks, L. D. (1990). Surface phenomena in RHEED and REM. *Acta Cryst.* A46(7), 594-606. DOI 10.1107/S0108767390002781. Companions (OPTIONAL): Ma, Y. (1991). A computational method for obtaining stationary solutions in RHEED and REM. *Acta Cryst.* A47(2), 137-139, DOI 10.1107/S010876739001011X. Bonevich, J. E., Ma, Y. & Marks, L. D. (1991). Dynamical RHEED calculations of relaxation on Au(110)-2x1 reconstruction. *Acta Cryst.* A47, 789-794, DOI 10.1107/S0108767391006402. | The step-simulation section of the 1990 paper (its abstract says surface steps were simulated with the combined Bloch-wave/multislice "BMCR" method). | **Step contrast** with a stationary reflection solution; a second published step simulation besides RT09. | **Open:** 1990 paper at numis .../1990/ ("5Surface Phenomena in RHEED and REM.pdf"); Bonevich et al. at numis .../1991/1991_Dynamical_RHEED.pdf. Both opened. Ma 1991: library journal (IUCr). | `MV-CR` for all three. SECTION_READ of the abstracts of the 1990 paper and of Bonevich et al. (the latter states that it uses "the multislice approach with the edge-patching method"). |
| RT29 | SHOULD | Cowley, J. M. *Diffraction Physics*, 3rd ed. Elsevier, 1995. ISBN 9780444822185. Book DOI 10.1016/B978-0-444-82218-5.X5000-7. | "Multi-slice approaches" pp. 231-254 (DOI 10.1016/B978-044482218-5/50013-4); "Diffraction from surfaces" pp. 433-455 (.../50021-3); "Diffuse scattering and absorption effects" pp. 257-285 (.../50014-6); "Dynamical diffraction effects" pp. 189-207 (.../50011-0). | The physical-optics (Cowley-Moodie) foundation of multislice in Cowley's own words; surface diffraction; absorption. | Library e-book (ScienceDirect). | `TOC` from Crossref chapter records; Crossref gives no chapter numbers, so they are not given here. |
| RT30 (bib U13 resolved) | SHOULD | Ishizuka, K. (1982). Multislice formula for inclined illumination. *Acta Cryst.* A38(6), 773-779. DOI 10.1107/S0567739482001594. | Whole paper (7 pp.). | **Propagator for tilted illumination** (step 3a: the sheet beam is tilted 16.93 mrad towards the surface. The specular beam leaves 16.93 mrad on the other side of the beam axis, 33.9 mrad from the incident beam; this is a reading of `pipeline.md`). It shows how tilt enters the propagator, against which to check the exact Fresnel propagator in `multislice.py`. | Library journal (IUCr). | `MV-CR`. It replaces the placeholder bib entry U13 ("Ishizuka 1998"); no 1998 paper was found under this topic. |
| RT31 | OPTIONAL | Cowley, J. M. & Moodie, A. F. (1957). The scattering of electrons by atoms and crystals. I. A new theoretical approach. *Acta Cryst.* 10(10), 609-619. DOI 10.1107/S0365110X57002194. Goodman, P. & Moodie, A. F. (1974). *Acta Cryst.* A30(2), 280-290, DOI 10.1107/S056773947400057X. Ishizuka, K. & Uyeda, N. (1977). *Acta Cryst.* A33(5), 740-749, DOI 10.1107/S0567739477001879. Chen, J. H. & Van Dyck, D. (1997). Accurate multislice theory for elastic electron scattering in transmission electron microscopy. *Ultramicroscopy* 70(1-2), 29-44, DOI 10.1016/S0304-3991(97)00071-5. | As needed. | Original multislice papers, plus a non-paraxial accuracy analysis (Chen and Van Dyck) for the high-angle limit (SM08). | Library journal (IUCr; Elsevier). | `MV-CR` for all four. |
| RT32 | OPTIONAL | Hadley, G. R. (1992). Transparent boundary condition for the beam propagation method. *IEEE J. Quantum Electron.* 28(1), 363-370. DOI 10.1109/3.119536. | Whole paper. | **Absorbing / transparent boundaries.** An optics (beam-propagation-method) alternative to the bulk absorber and vacuum margins of the reflection cell. It is not electron-microscopy literature; transfer to the FFT multislice is an INFERENCE to be tested. | Library journal (IEEE). | `MV-CR`. |

### 4b. Reflection simulation codes as independent benchmarks

| ID | PRIORITY | Citation (DOI / ISBN) | WHAT TO READ | WHY (pipeline step) | ACCESS | VERIFIED |
|---|---|---|---|---|---|---|
| RT33 (bib SIMTRHEPD, SIMTRHEPD-CPC) | **MUST** | Hanada, T., Motoyama, Y., Yoshimi, K. & Hoshi, T. (2022). sim-trhepd-rheed - Open-source simulator of total-reflection high-energy positron diffraction (TRHEPD) and reflection high-energy electron diffraction (RHEED). *Comput. Phys. Commun.* 277, 108371. DOI 10.1016/j.cpc.2022.108371. arXiv:2110.09477. Code: https://github.com/sim-trhepd-rheed/sim-trhepd-rheed (Fortran). | arXiv v3: sect. 2 "Overview of the proposed method" (eq. 1 and the potential and absorption model, PDF pp. 2-3); sect. 3 "Software"; sect. 4 "Numerical examples"; sect. 5.1, the RHEED comparison for Si(111) (PDF pp. 8-9). README: "Mode switching". | **Benchmark (M2):** a flat-surface rocking curve from an independent surface-parallel (Ichimiya) solver, compared with `scripts/rocking_flat.py`. Its absorption model has the same form as the placeholder here (section 6.1), so the two can be compared like for like. | **Open:** arXiv PDF and README (raw.githubusercontent.com), both opened. CPC version: library journal. | `ABS-arXiv`, SECTION_READ (arXiv v3 sect. 2, 5.1), `README`, `MV-CR`. This supplies the real article title missing from the bib entry. The `doc/` manual path given in the README returned 404. |
| RT34 (bib P49) | SHOULD | Kudo, S., Yamamoto, Y. & Hoshi, T. (2024). A fast and efficient computation method for reflective diffraction simulations. *Comput. Phys. Commun.* 296, 109029. DOI 10.1016/j.cpc.2023.109029. Preprint: arXiv:2306.00271 ("A fast and *accurate* computation method ..."). | arXiv abstract read; method sections when rocking series become expensive. | Faster benchmark runs for rocking series (the 2π-branch problem, physics_summary section 4). | **Open:** arXiv. CPC: library journal. | `ABS-arXiv` + `MV-CR`. This resolves the P49 title discrepancy (preprint "accurate", journal "efficient") and adds the full author list, volume, article number and DOI. |
| RT35 (bib HANADA95) | OPTIONAL | Hanada, T., Daimon, H. & Ino, S. (1995). Rocking-curve analysis of reflection high-energy electron diffraction from the Si(111)-(√3 x √3)R30°-Al, -Ga, and -In surfaces. *Phys. Rev. B* 51(19), 13320-13325. DOI 10.1103/PhysRevB.51.13320. | Methods and rocking-curve figures. | Reference rocking-curve data and settings used with the code in RT33 (the README asks users to cite it). | Library journal (APS). | `MV-CR`. This supplies the missing title and DOI of bib HANADA95. |

Not a reflection benchmark: abTEM (bib ABTEM) is transmission-only, as recorded in `references.bib`. It can
check the potential and the propagator in a transmission test (README milestone M2), not the reflection
geometry.

## 5. Download first (in this order; one afternoon)

There are 10 MUST items: RT01, RT02, RT08, RT09, RT16, RT24, RT25, RT26, RT27 and RT33. The checklist
groups them into 8 actions. Items 1 and 2 are free and can be read today.

1. [ ] **RT26 + RT27: Ma and Marks, *Acta Cryst.* A46, 11-32 (1990) and A47, 707-715 (1991).** Free
   author copies at numis.northwestern.edu (`/Research/Articles/1990/` and `/1991/`). Read RT26 sect. V-VI
   (pp. 30-32) and RT27 pp. 707-709. They test this repository's tilted-sheet-beam illumination and give
   the edge-patching fix. Also get the A46 p. 626 erratum (library).
2. [ ] **RT33: Hanada et al., CPC 277, 108371 (2022).** Free preprint arXiv:2110.09477. Clone
   `github.com/sim-trhepd-rheed/sim-trhepd-rheed`, and set `ep='E'` before compiling. This is the
   independent flat-surface rocking-curve benchmark.
3. [ ] **RT25: Peng and Cowley, Surf. Sci. 199, 609-622 (1988), with Acta Cryst. A42, 545-552 (1986).**
   Library journal. This is the method the kernel implements.
4. [ ] **RT24: Kirkland, 3rd ed. (2020), ch. 4 (pp. 81-98) and ch. 6 (pp. 143-195).** Library e-book.
   Propagator, sampling and slice thickness.
5. [ ] **RT01: Ichimiya and Cohen (2004), ch. 4-5, 11, 12, 14 and App. F.** Library e-book (Cambridge Core).
   Refraction and the rocking-curve theory behind RT33.
6. [ ] **RT02: Peng, Dudarev and Whelan (2004), ch. 5 (pp. 117-185), ch. 13 (pp. 427-453) and ch. 14
   (pp. 454-469).** Library e-book (Oxford Academic). RHEED Bloch waves, optical potential and
   Debye-Waller factors.
7. [ ] **RT16: Peng, Ren, Dudarev and Whelan, Acta Cryst. A52, 257-276 (1996).** Library journal. This is
   the source of the parameterisation already in the code and of the absorptive potential. Fetch RT17
   (A52, 456-470) in the same session.
8. [ ] **RT08 + RT09: Wang (1996) ch. 6 (pp. 166-198), plus ch. 3, 4 and 9 and App. B; and McCoy and
   Maksym, Surf. Sci. 310, 217-225 (1994).** Library e-book and library journal. Step and dislocation
   contrast, with the published Si(001) step simulation as the acceptance target.

## 6. Facts read versus inferences

### 6.1 Facts (quoted only from text actually read; source, URL, locator)

**Ma and Marks (1990)**
* URL read: numis.northwestern.edu/Research/Articles/1990/, the PDF named in RT26.
* Abstract, p. 11: "the Bloch-wave approach for reflection is shown to yield a stationary solution in
  multislice, except for a small effect from the surface truncation"; and "The introduction of
  absorption improves the consistency between the two methods."
* Sect. I, p. 12, on the Peng and Cowley approach: "the difficulty is that the incident wave is taken as
  a top-hat function (with smooth sides) that is allowed to impinge upon the surface, and it is hard to
  reach a stationary solution (as dictated by the symmetry in reflection) since the size of the input
  incident wave is limited and edge effects are unavoidable."
* Sect. IV.1, p. 20: "All the following calculations were performed for 100 keV electrons."
* Sect. V, p. 30: "a plane wave smoothed by a Gaussian function tilted towards the crystal surface is
  introduced into the left part of the unit cell in the vacuum. The tilt angle is 25 mrad." Then
  "Owing to the edge effects, it appears, however, that the solution is unstable. If absorption is
  introduced [Fig. 16(ii)], the result is not much better."
* Sect. VI, p. 32: "One obvious problem is edge effects; multislice is not a true numerical solution
  since its periodic continuation leads to edge effects. One can overcome these problems to some extent
  by using very long unit cells as we have done." Also: "using an incident top-hat wave function does not
  seem to be a reliable approach."

**Ma and Marks (1991)**
* URL read: numis.northwestern.edu/Research/Articles/1991/1991_Robust_Solution.pdf.
* Abstract, p. 707: "A new method of solving the reflection diffraction problem using a stabilized edge
  in a multislice-type calculation is described."
* p. 708: "Physically, the patched region plays the role of an infinite plane-wave source in a finite
  numerical unit cell."
* p. 709: "The patching has been implemented on the left outer part of the unit cell (0 < z < 0.25,
  where z is normal to the surface ...) with the crystal located in the region 0.75 < z < 1.0".

**Bonevich, Ma and Marks (1991)**
* URL read: numis.northwestern.edu/Research/Articles/1991/1991_Dynamical_RHEED.pdf.
* Abstract, p. 789: simulated "using the multislice approach with the edge-patching method."

**Ma and Marks (1990b)**
* URL read: numis.northwestern.edu/Research/Articles/1990/, the PDF named in RT28.
* Abstract, p. 594: "the results of simulations of surface steps are shown and their effects on the
  wave field analyzed numerically."

**Hanada et al., arXiv:2110.09477v3**
* URL read: arxiv.org/pdf/2110.09477v3.
* Sect. 2, PDF p. 3: "The absorption effect of the beams is taken into account through the imaginary
  potential, which is simply assumed as εm(n) times the real potential in terms of the individual
  contribution from atom n."
* Sect. 2, PDF p. 2: the method solves the equation "in a two-dimensional periodic potential of the
  crystal surface".
* Fig. 1(b) caption, PDF p. 2: "the beam energy is 15 keV, the glancing angle θ is 2°".
* Sect. 5.1, PDF p. 9: "STR employs a much simpler parameter of sap, which can fairly approximate the
  absorption effect of beams by adjusting its value."

**sim-trhepd-rheed README**
* URL read: raw.githubusercontent.com/sim-trhepd-rheed/sim-trhepd-rheed/master/README.md.
* "The default setting is the TRHEPD (positron) mode. If one would like to use the RHEED (electron)
  mode, one should modify the line ep='P' into ep='E' of the files src/surfm.f90 and src/bulkm.f90 before
  the compilation."
* The quote marks in the README are typographic; they are rendered as plain quotes here.

**Wang (1996), Cambridge Core chapter summaries (`SUM`)**
* Ch. 6, chapter DOI 10.1017/CBO9780511525254.008: "Attempts have been made to simulate surface step
  images (Peng and Cowley, 1986; Ma and Marks, 1990), but the results are still not very satisfactory."
* Ch. 6 also: "Phase contrast (or Fresnel contrast) is produced by the path-length difference (or phase
  shift) of electron waves due to the change in surface morphology. This contrast dominates the images of
  atom-high surface steps." And: "Diffraction contrast (or Bragg contrast) is produced by the variation
  of local Bragg reflection angles due to lattice distortion from dislocations, local strain and crystal
  boundaries."
* Ch. 2, chapter DOI ...525254.004: "the incident electron beam strikes the sample surface at a grazing
  angle of 1–3°. The electron energy can be as low as a few kilo-electron-volts and as high as 1000 keV
  (in TEM only)."
* Ch. 4, chapter DOI ...525254.006: "The intensity is increased by almost an order of magnitude if the
  surface resonance is excited".
* Ch. 9, chapter DOI ...525254.011: "The mean-free-path length of inelastic scattering is about 50–300 nm
  for most materials".

**Ichimiya and Cohen (2004), Cambridge Core chapter summaries (`SUM`)**
* Ch. 12, chapter DOI 10.1017/CBO9780511735097.013: "In Chapters 12–14 we present methods due to
  Ichimiya (1983, 1985), Zhao et al. (1988) and Maksym and Beeby (1981) in sufficient detail that the
  reader should be able to perform these calculations for real surfaces."
* Ch. 12 also: "Only elastic scattering is considered, with the electron momentum conserved up to a
  reciprocal lattice vector of the two-dimiensional [sic] crystal."
* Ch. 13, chapter DOI ...735097.014: "It is also a multi-slice method, in which the crystal is modelled
  as a slab divided into many thin slices parallel to the surface."

**Peng, Dudarev and Whelan (2004), abstracts in the Crossref deposit**
* Ch. 13: "the effects of inelastic scattering on the elastic scattering may be taken into account by
  representing the interaction between the incident electron and the solid by a complex potential
  (Yoshioka, 1957). This complex potential is usually called the optical potential".
* Book abstract: "temperature dependent Debye-Waller factors given for over 100 elemental crystals and
  compounds".

### 6.2 Inferences (mine, to be tested; not findings from the sources)

* **I1, stationarity of the kernel.**
  * The repository launches a sheet beam in vacuum, tilted towards the surface (`pipeline.md` 3a.2).
    This is the kind of illumination that Ma and Marks (1990, sect. V) found unstable because of edge
    effects. Their test used 100 keV and 25 mrad, with cells up to 405 Å along the beam (Fig. 16
    caption).
  * The repository's countermeasures are about 3100 slices (about 0.6 µm), a bulk absorber and a vacuum
    mask. These belong to the "very long unit cells" remedy, which Ma and Marks say helps "to some
    extent".
  * Whether the repository's dark-field wave is stationary is therefore open. The agreement with the
    geometric model to 0.05 rad tests the phase, not stationarity.
  * Proposed tests:
    1. the flat-surface rocking curve against RT33;
    2. the exit wave versus cell length;
    3. an edge-patched run (RT27).
* **I2, scope of the benchmark.** RT33 assumes a 2-D-periodic surface (fact above). So it can benchmark
  only the flat reference strip (reflectivity and rocking curve), not steps or dislocations. Its use at
  200 keV is NOT VERIFIED: the examples seen were at 10 and 15 keV.
* **I3, absorption.** RT33 and this repository both use an imaginary potential proportional to the real
  one. Agreement between them would therefore not validate the absorption value. RT16 and RT17 (or RT21)
  are needed for a physically sourced V_i.
* **I4, a possible V0 inconsistency (check the code).**
  * The multislice refracts with the potential it is given, whose mean is 13.91 V (SM17).
  * The geometric model and the step-phase calculator are documented with V0 = 12 V.
  * If the geometric model in a run really uses 12 V, the 0.05 rad agreement between the two models may
    involve compensating choices.
  * This was not checked in the code during this literature pass.
* **I5, novelty.** No item found here treats a 200 keV beam-perpendicular multislice with an absorber
  for off-axis holography. This is based on a targeted search, not a citation-graph search, so it is
  not evidence of absence.
* **I6, ptychography.** Reflection-mode ptychography theory was outside this list's four topics. Only
  RT15 (scanning REM) bears on it; see `references.bib` C03 and U03.

### 6.3 Corrections and additions for `references.bib` (from Crossref; NOT applied to the file)

| Bib key | Correction or addition (all from Crossref records read in this pass) |
|---|---|
| P17 | DOI 10.1143/JJAP.22.176 verified. Add the correction JJAP 24(10R), 1365 (1985), DOI 10.1143/JJAP.24.1365. |
| P18 | DOI 10.1107/S0108767386098756 verified; issue 6. |
| P19 | Confirmed: Surf. Sci. 199(3), 609-622, DOI 10.1016/0039-6028(88)90925-9. |
| P20 | Pages 174-182, issue 2; DOI 10.1107/S0108767388010888 verified. |
| P21 | DOI 10.1107/S0108767389009141 verified. Add the erratum A46(7), 626, DOI 10.1107/S0108767390004810. |
| P22 | Issue 7; DOI 10.1107/S0108767390002781. |
| P23 | Confirmed: DOI 10.1107/S0021889887086916. |
| P24 | First author Y. Uchida (not N.); Crossref gives "J. Jäger" (the bib has W.); pages 325-327; issue 3; DOI 10.1016/0304-3991(84)90210-9. |
| P25 | First author Y. Uchida; pages 53-59; issue 1; DOI 10.1016/0304-3991(87)90226-9. |
| P26 | Issue 4; DOI 10.1016/0304-3991(90)90041-J. |
| P49 | Journal version: Kudo, S., Yamamoto, Y. & Hoshi, T., "A fast and efficient computation method for reflective diffraction simulations", CPC 296, 109029 (2024), DOI 10.1016/j.cpc.2023.109029. The arXiv title says "accurate". |
| B06 | Crossref chapter list: 8 chapters (ch. 4 pp. 81-98, ch. 6 pp. 143-195, ch. 7 pp. 197-239). ISBNs 9783030332594 and 9783030332600. |
| B07 | DOI 10.1017/CBO9780511735097; ISBNs 9780521453738, 9780521184021; full contents in RT01. |
| B08 | Chapter DOIs 10.1093/oso/9780198500742.003.0001 to .0014 with pages; the year conflict is still open. |
| ZLWANG96 | DOI 10.1017/CBO9780511525254; full contents in RT08. |
| SIMTRHEPD-CPC | Real title: "sim-trhepd-rheed – Open-source simulator of total-reflection high-energy positron diffraction (TRHEPD) and reflection high-energy electron diffraction (RHEED)"; arXiv:2110.09477. |
| HANADA95 | Title "Rocking-curve analysis of reflection high-energy electron diffraction from the Si(111)-(√3 × √3)R30°-Al, -Ga, and -In surfaces"; issue 19; DOI 10.1103/PhysRevB.51.13320. |
| U01 | Resolved into three McCoy and Maksym papers: Surf. Sci. 297, 113-126 (1993); 298, 468-472 (1993); 310, 217-225 (1994). |
| U02 | Beeby, J. L., Surf. Sci. 298(2-3), 307-315 (1993), DOI 10.1016/0039-6028(93)90043-J. |
| U04 | Title "Invariant-embedding R-matrix scheme for reflection high-energy electron diffraction"; PRB 38(2), 1172-1182; DOI 10.1103/PhysRevB.38.1172. |
| U13 | Ishizuka, K., "Multislice formula for inclined illumination", Acta Cryst. A38(6), 773-779 (1982), DOI 10.1107/S0567739482001594. |

## 7. Documents to request from Ali (paywalled or blocked here; nothing below was read)

In priority order:

1. Peng and Cowley 1988 (Surf. Sci. 199, 609) and 1986 (Acta Cryst. A42, 545): full PDFs.
2. McCoy and Maksym 1994 (Surf. Sci. 310, 217) and 1993 (Surf. Sci. 297, 113): full PDFs.
3. Peng, Ren, Dudarev and Whelan 1996: Acta Cryst. A52, 257 and A52, 456.
4. Kirkland 3rd ed.: ch. 4 and 6, and the atomic-potential appendix. Also a scan of the printed contents
   pages, to settle the chapter-title discrepancy.
5. Ichimiya and Cohen 2004: ch. 4, 5, 11, 12, 14 and App. F.
6. Peng, Dudarev and Whelan 2004: ch. 5, 13 and 14, plus the appendix list (it is unclear which holds
   the RHEED program).
7. Wang 1996: ch. 6, 3, 4 and 9, and App. B.
8. Kruse et al. 2006 (Ultramicroscopy 106, 105): for the Si mean inner potential.
9. Ma and Marks 1990 erratum (Acta Cryst. A46, 626) and Ma 1991 (Acta Cryst. A47, 137).
10. Ishizuka 1982 (Acta Cryst. A38, 773); Yao and Cowley 1990 (Ultramicroscopy 33, 237); Ichimiya 1983
    and the 1985 correction (JJAP); Maksym and Beeby 1981 (Surf. Sci. 110, 423); Peng and Cowley 1989
    (Ultramicroscopy 29, 168).

**Hosts that blocked this session:**
* journals.iucr.org (HTTP 403);
* academic.oup.com (HTTP 403);
* link.springer.com (JavaScript challenge);
* github.com HTML and the GitHub API for sim-trhepd-rheed (403). raw.githubusercontent.com worked.
