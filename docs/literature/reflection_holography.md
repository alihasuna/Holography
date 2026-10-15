# Literature survey: reflection electron holography (REM holography) and modern off-axis holography

Compiled 2026-10-14 for a simulation of reflection-geometry (RHEED/REM) dark-field off-axis holography of
Si(001) (200 keV, specular (008), glancing angle about 17 mrad). The source policy of the project
instruction file applies. **READ** means the text was opened and read in this session at the URL given.
**NOT VERIFIED** means it was not read. Search-engine summaries were used only to find leads; every fact
below comes from a page or PDF that was actually opened. Inferences are kept separate, in section 4, and
labelled DERIVED_HERE or INFERENCE. In project labels, every READ full text here counts as SECTION_READ
for the sections cited, and every abstract-only item counts as METADATA_VERIFIED plus a publisher or
Europe PMC abstract (not `+ABSTRACT(index)`).

## 0. Access conditions and how the search was done

* Reachable: api.crossref.org, api.semanticscholar.org, export.arxiv.org/arxiv.org, pmc.ncbi.nlm.nih.gov,
  Europe PMC REST, www.jstage.jst.go.jp (including the J-STAGE search API), iopscience.iop.org (article
  pages only; the JJAP PDF needs sign-in), patents.google.com, www.mrs-j.org, cdn.intechopen.com,
  rafaldb.com, api.archives-ouvertes.fr.
* Blocked by the publisher host (HTTP 403 from the host, not from the proxy; the proxy status showed no
  relay failure): journals.aps.org, www.sciencedirect.com, onlinelibrary.wiley.com, academic.oup.com,
  journals.iucr.org. cambridge.org returned HTTP 400 to both curl and WebFetch. hal.science served a
  bot-check page. The OpenAlex anonymous daily budget was used up (HTTP 429), so OpenAlex citing-work
  lists were not obtained.
* Citation-graph check, READ: Semantic Scholar Graph API citations endpoint for JJAP 27 L1772 (1988),
  PRL 62 2969 (1989), Microsc. Res. Tech. 20 450 and 457 (1992), Ultramicroscopy 48 475 and 483 (1993),
  Surf. Sci. 298 345 (1993), Ultramicroscopy 35 245 (1991), Proc. EMSA 47 536 and 53 116, Mater. Trans. JIM
  31 551. After 1995 the citing works are: Yamanaka and Ino 2000 (RHEED standing waves), Jiang et al.
  2013/2014 (elasticity of a screw dislocation near a free surface), Zhang et al. 2015 (optical wafer
  holograms), a 2015 Cowley encyclopedia entry, Lee et al. 2019 (cubic GaN), the Dunin-Borkowski et al.
  2019 handbook chapter (B2) and Harada 2020 (B1). **None of them is a reflection electron holography
  experiment.**
* J-STAGE search API (READ): queries "reflection electron holography", "dark-field electron holography"
  and the author names "Nobuyuki Osakabe" / 長我部 信行. Two Japanese conference abstracts by Osakabe on
  reflection holography (1989, 1990) were found and read (A2, A3).
* Crossref title search (READ) for "reflection electron holography", "reflection electron microscopy
  holography", "grazing incidence electron holography" and "RHEED holography", restricted to works from
  2005 on: no electron reflection-holography experiment was returned.
* Also opened and found to have no reflection content: Tonomura, "Fundamentals and Applications of
  Electron Holography", in Holography, Research and Technologies (InTech 2011), DOI 10.5772/14280,
  https://cdn.intechopen.com/pdfs/13864.pdf (grep of the full text).

**Finding (search-limited):** no reflection electron holography experiment published after the Hitachi
and Tübingen work of 1988-1993 (and Herring's 1995 conference abstract, title only) was found. In the two
modern reviews that were read, reflection holography appears only as a historical citation (B1, B2).
OpenAlex, Google Scholar and Web of Science could not be queried, so this result is "not found", not
"proven absent". For a simulation paper the consequence is that the published reflection-holography
figures to compare against are the 1988-1993 interferograms. Modern quantitative metrics (phase noise,
dose, simulation-versus-experiment protocols) have to come from transmission work (category B).

## 1. Category A: reflection electron holography (all READ items)

| ID | Citation (verified identifiers) | URL actually read | What was read |
|---|---|---|---|
| A1 | N. Osakabe, T. Matsuda, J. Endo, A. Tonomura, "Observation of Atomic Steps by Reflection Electron Holography", Jpn. J. Appl. Phys. 27 (9A), L1772 (1988), DOI 10.1143/JJAP.27.L1772 (from the IOP page metadata; OpenAlex record W2054923936) | https://iopscience.iop.org/article/10.1143/JJAP.27.L1772/pdf (served the HTML article page) | Abstract and metadata only; the PDF is behind sign-in |
| A2 | N. Osakabe, J. Endo, T. Matsuda, A. Fukuhara, A. Tonomura (Hitachi ARL), "Observation of surface morphologies by reflection electron holography" (反射型電子線ホログラフィーによる結晶表面の観察), JPS meeting abstract 6p-T-5, Meeting Abstracts of the Physical Society of Japan 1989.2, p. 439 | https://www.jstage.jst.go.jp/article/jpsgaiyok/1989.2/0/1989.2_439_1/_pdf | Full one-page abstract (Japanese; translations below are mine) with Figs. 1-2 |
| A3 | N. Osakabe (Hitachi ARL), "Observation of Surfaces by Reflection Electron Holography" (反射型電子線ホログラフィー法による表面の観察), JPS meeting abstract 2a-T-7, Meeting Abstracts of the Physical Society of Japan 45.2, pp. 451-452 (1990) | https://www.jstage.jst.go.jp/article/jpsgaiyod/45.2/0/45.2_451/_pdf | Full two-page abstract (Japanese) with Figs. 1-3 |
| A4 | J. Endo, A. Tonomura, "Applications of Electron Holography to Materials Science", Materials Transactions JIM 31(7), 551-560 (1990), DOI 10.2320/matertrans1989.31.551 (Crossref) | https://www.jstage.jst.go.jp/article/matertrans1989/31/7/31_7_551/_pdf | Full scanned text; section VI "Measurement of Surface Morphology" (pp. 559-560), Figs. 20-21 |
| A5 | A. Tonomura, "Electron holography and its applications to nanoworld observation", Trans. Mater. Res. Soc. Jpn. vol. 2, p. 14 onward (year not printed on the pages read; latest reference cited is 1990; no DOI found) | https://www.mrs-j.org/pub/tmrsj/vol02/vol02_014.pdf | Full text (OCR layer) pp. 16-18 and Fig. 7 (p. 30) |
| A6 | N. Osakabe, A. Tonomura (Hitachi Ltd), US Patent 4,998,788, "Reflection electron holography apparatus" (dates on the record 1990-01-10 and 1991-03-12) | https://patents.google.com/patent/US4998788A/en | Full description, equations (1)-(2), claims |
| A7 | (a) N. Osakabe, "Observation of surfaces by reflection electron holography", Microsc. Res. Tech. 20(4), 457-462 (1992), PMID 1498359, DOI 10.1002/jemt.1070200415; (b) H. Banzhof, K.-H. Herrmann, H. Lichte, "Reflection electron microscopy and interferometry of atomic steps on gold and platinum single crystal surfaces", Microsc. Res. Tech. 20(4), 450-456 (1992), PMID 1498358, DOI 10.1002/jemt.1070200414 | Europe PMC REST record, https://www.ebi.ac.uk/europepmc/webservices/rest/search | Abstracts only (indexed abstract text). The pages 450-456 settle the 450-456 versus 450-466 conflict in references.bib |

### A1 Osakabe et al. 1988 (abstract READ)
* Surface Pt(111), "at glancing angle incidence". The reference is formed by overlapping "Two regions in a
  reflection electron image" with an electron biprism, "to form an off-axis electron hologram"; that is,
  a reflected reference from another part of the surface. Reconstruction is optical ("optically
  reconstructed interferogram"). Stated sensitivity: "of the order of 0.01 nm", tested "by observing
  mono-atomic-height surface steps". **READ.**
* Not read: kV, which reflection was used, glancing angle, biprism voltage, fringe spacing, figures.
  **NOT VERIFIED.** The patent (A6) describes this prior art as giving "about ten interference fringes"
  between two reflected object waves (**READ** in A6).

### A2 Osakabe et al. 1989 JPS abstract (full, READ; translation mine)
* Principle: the geometric path difference of the reflected electrons caused by surface relief is
  measured interferometrically. The path difference Δz sinθ (Fig. 1) is measured in units of the short
  electron wavelength ("~0.01 Å" as printed). Fig. 1 formula: "Δφ = 2KΔz sinθ".
* Optics: the optical system of REM, imaging the specular Bragg reflection of the crystal surface. The
  biprism superposes **the wave reflected from a defect-free region of the surface, used as the reference
  wave**, onto the wave reflected from the observed region.
* Fig. 2: interference micrograph of a screw dislocation with Burgers vector b = a/2[101] emerging
  obliquely at a GaAs(110) surface. It is drawn as a 3-D block with the interferogram on top, "STEP",
  "DISLOCATION CORE" and Δφ labels, crystal axes [1-12], [1-10], [001], and orthogonal scale bars
  "0.5 µm" and "1 µm".
* Numbers: one fringe shift corresponds to a height displacement of 0.5 Å. Around the core the strain is
  concentrated on one side, unlike the nearly uniform spiral strain in the bulk. This is attributed to
  surface stress relaxation and "agrees well" with an isotropic-elasticity calculation. The Burgers
  vector could be determined from the step height and the strain distribution.

### A3 Osakabe 1990 JPS abstract (full, READ; translation mine). The most quantitative reflection source read
* Coherence (section 2-1): cold FEG. Example given: at 10,000x specimen magnification with exposures of a
  few seconds, a temporal coherence length of 3 µm and a spatial coherence length of 1 µm. Section 3-2:
  the incident beam is collimated to a divergence of 10^-6 rad or less, giving a coherence distance of
  several µm.
* Optics (section 2-2, Fig. 1): an ordinary electron microscope in the REM arrangement. The objective
  aperture selects the specular Bragg reflection. The biprism sits below the objective lens and forms the
  hologram by wavefront division. **The beam passing one side of the biprism is the reference and is set
  on a region of the specimen without defects.** Reconstruction used a Mach-Zehnder optical
  interferometer. The interference micrographs "can be interpreted directly as 3-D images".
* Phase (section 2-3): if the electron behaviour inside the crystal is locally uniform, the
  reflected-wave phase difference is purely geometric, Δφ = 2K⊥Δz. K⊥ is the vacuum wave-vector component
  normal to the surface and Δz the normal displacement. Glancing angles are "several tens of mrad", so a
  one-wavelength phase difference corresponds to sub-Å height.
* Steps (section 3-1): a single-atom step height equals the fundamental lattice-plane spacing that
  produces the Bragg reflection, so the phase difference is 2nπ for reflection order n. Refraction shifts
  it from this value. In the kinematic approximation the abstract prints
  "Δφ = √((2πn)² − (2kd)² V₀/E)" (the superscripts appear as primes in the scan). Under dynamical
  conditions that excite simultaneous reflections, the reflection position shifts and the phase deviates
  from this formula. The deviation is said to be of the order of the change of the potential producing the
  simultaneous reflection relative to the mean inner potential producing the refraction.
* Measurement: a Pt(111) interferogram (figure caption "第2図 Pt(111)表面の干渉顕微鏡像", scale bar 0.1 µm;
  the text calls it 第1図) shows a 2.3 Å single-atom step with a phase difference of "about 0.5 λ",
  explained by the formula. It cites Banzhof et al. (Proc. 9th EUREM, York 1988, p. 263) for Pt and Au(111)
  steps measured at several reflection orders.
* Dislocation (section 3-2, Fig. 3, GaAs(110), b = a/2[101]): the strain field differs from the bulk
  because of surface stress relaxation. Key statement (translation): the integer part of the phase
  difference at a step was generally not observed, but **following fringe continuity around the
  dislocation, away from the core, shows that fringes corresponding to the integer part originate or
  terminate at the dislocation core (white arrows, Fig. 3)**. The absolute phase, and hence the
  z-component of b, can therefore be determined.

### A4 Endo and Tonomura 1990 (section VI and Figs. 20-21 READ)
* Fig. 20, "Electron-optical arrangement for reflection holography": specimen, objective lens, aperture,
  biprism, hologram.
* Quoted text: "Sensitivity to thickness changes at the surface is two orders higher than that obtained
  by the transmission method." The specimen is GaAs(110). "The surface undulations around the screw
  dislocation can be directly measured by the shifts of the tilted interference fringes. A fringe shift
  which corresponds to one fringe spacing means a vertical displacement of 0.05 nm."
* Fig. 21, "Surface undulation of a GaAs single crystal. (a) Interferogram and (b) Calculated surface
  topography". (a) is a perspective block with Δφ, "Step" and "Dislocation core" labels and scale bars
  0.5 µm and 1 µm. (b) is a calculated 3-D mesh of a surface with a "STEP".
* The same paper shows transmission "phase-amplified contour maps" at 3x, 5x and 7x (Fig. 17), the figure
  type also used in the reflection work.

### A5 Tonomura, Trans. MRS-J vol. 2 (READ)
* Transmission benchmark: in a 24x amplified interferogram of cleaved molybdenite, a 6.2 Å step gives
  2π/50, and the phase is detectable "with an accuracy of the order of 2 π/100" (OCR text, verified
  against the page image).
* Reflection (pp. 17-18, Fig. 7 "Interference micrograph of GaAs (110) surface"): "Although the
  interferogram is not phase-amplified, one fringe displacement corresponds to only a 0.5 A height
  difference. A monoatomic step of 2 A can be seen until reaching the dislocation core." The undulation
  "is similar to a spiral staircase. However, the staircase slope was found to be steep only in the
  opposite side of the step from the core." The reference wave is not described here.

### A6 US 4,998,788 (READ)
* Prior art (JJAP 1988): reflected waves interfere with each other, giving "about ten interference
  fringes". Interference with a direct (non-illuminating) wave would give fringes narrower than the
  resolution limit.
* Invention: illumination near "the Bragg angle causing a total reflection". "a half of the electron wave
  does not illuminate the specimen". The reflected and direct waves pass an aperture in the back focal
  plane and a biprism with a negative wire potential. Image separation follows "d=Csα^3 -Δfα (1)", where
  α is the angle between the reflected and direct waves, so defocus and biprism voltage set a recordable
  fringe interval. Second embodiment: a first biprism above the specimen splits the beam (angle equal to
  the sum of the incidence and reflection angles), and two further biprisms give independent control of
  the crossing angle and the overlap.
* Phase: the step phase is the geometric path difference, rendered in the Google Patents text as
  "Δφ=2h sin θλ (2)" (layout lost; INFERENCE: 2h sinθ/λ in wavelengths). Quoted: at "100 kV, the phase
  changes by about 1/3 of a wavelength if the step h is 0.1 Å. The measurement precision now available is
  about 1/100 of a wavelength."

### A7 Abstracts (READ, abstract level only)
* Osakabe 1992: "Phase shift of a Bragg-reflected electron wave was measured by means of holographic
  interferometry using an electron microscope equipped with a field emission electron gun and an electron
  biprism"; "Phase shift at a monoatomic step and the displacement field around a dislocation emerging on
  the surface were observed."
* Banzhof, Herrmann, Lichte 1992: biprism "inserted in the position of the selected area diaphragm of a
  commercial electron microscope"; the results are interpreted "in terms of refraction"; "phase shifts of
  pi and 0.9 pi were measured for monatomic steps on (111)gold and (111)platinum surfaces, respectively."
* This is consistent with A3's "about 0.5 λ" for a 2.3 Å Pt(111) step (0.5 λ = π). INFERENCE: both
  measurements agree.

## 2. Category B: modern off-axis holography relevant to a simulation study (all READ)

| ID | Citation (DOI verified on Crossref) | URL read | Read | Conditions | Figures | Numbers |
|---|---|---|---|---|---|---|
| B1 | K. Harada, "Interference and interferometry in electron holography", Microscopy 70(1), 3-16 (2021), DOI 10.1093/jmicro/dfaa033 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7850541/ | Full text and captions (equations are images in PMC, not read) | Review. Single biprism, double biprism (upper wire in the image plane, lower wire between crossover and image plane) and split illumination with a condenser biprism | Holograms and phase of MgO with and without Fresnel fringes (Fig. 10); Fourier reconstruction steps: hologram, power spectrum, sideband, amplitude and phase, cosine "interferogram" (Fig. 14) | Deflection α ∝ V_f with k_f about 10^-6 rad/V. Sideband separation needs a centreband spread of 2/3 R0 or less and sideband spread of 1/3 R0 or less, so the resolution is 3x the fringe spacing. At 300 kV with 2β = 10^-5 rad, l_s = 200 nm. Reflection holography appears only as refs. 45-46 (the first, geometric-path term) |
| B2 | R. E. Dunin-Borkowski, A. Kovács, T. Kasama, M. R. McCartney, D. J. Smith, "Electron Holography", ch. 16 in Springer Handbook of Microscopy, pp. 767-818 (2019), DOI 10.1007/978-3-030-00069-1_16 | https://rafaldb.com/papers/B-2019-Science-of-Microscopy-Electron-holography.pdf (author-hosted) | Sections 16.1-16.2 and 16.6 | Review | n/a | Fringe contrast μ = (Imax − Imin)/(Imax + Imin) (16.9); Δφ_min = (SNR/μ)·√(2/N_el) (16.10, p. 771). Reflection holography is listed as an alternative form "beyond the scope of this chapter", citing Banzhof and Herrmann 1993. Tomography needs tilts of at least ±60° |
| B3 | J. Lindner, U. Ross, T. Meyer, V. Boureau, M. Seibt, Ch. Jooss, "Reconstruction of Angstrom resolution exit-waves by the application of drift-corrected phase-shifting off-axis electron holography", Ultramicroscopy 256, 113880 (2024), DOI 10.1016/j.ultramic.2023.113880 | https://arxiv.org/pdf/2303.16054 (v2) | Full text | 300 kV Titan ETEM; single biprism at 250 V; 1 Å fringe spacing (14 px at 0.068 Å/px); field of view about 14 x 14 nm (2048²); Pt [110], about 2 nm thick | Fit of a phase-shifted hologram series; FFT of the hologram showing centreband/sideband separation; simulated and experimental amplitude (Fig. 6) and phase (Fig. 7) at 0, −4 and −22 nm defocus | Mean fringe contrast about 17% [13-19%]. 51 holograms x 1 s. Dose rate at least 30245 e⁻ nm⁻² s⁻¹. Phase sensitivity (std in vacuum): 0.087 rad per pixel (2π/84 and 2π/74), 2π/181 and 2π/171 over 1 Å wide profiles, 2π/452 after 1 Å low-pass. Camera MTF phase distortion at most 2π/76. Frozen-lattice multislice agrees; "dynamic scattering behaviour becomes relevant in Pt after a few atoms" |
| B4 | S. Borghardt et al., Phys. Rev. Lett. 118, 086101 (2017), DOI 10.1103/PhysRevLett.118.086101 (published title "Quantitative Agreement between Electron-Optical Phase Images of WSe2 and Simulations Based on Electrostatic Potentials that Include Bonding Effects"; Crossref also lists Tavabi) | https://arxiv.org/pdf/1610.06417 (v1, titled "The Effect of Intra-Layer Bonding on Electron-Optical Phase Images of Few-Layer WSe2") | Full arXiv v1 | 80 keV; WSe2 mono- and bilayer; experimental hologram exposure 12 s; multislice with apertures of 15 and 42 mrad, B = 0.3 Å², image-wave convolution 22-43 pm | Simulated phase images (DFT, IDFT, IAA) next to the experiment, plus difference maps (Fig. 4); Table I of mean phases | Mean phase (mrad), monolayer/bilayer: DFT 127.2/243.5, IDFT 134.5/256.7, IAA 138.4/265.4, experiment 126 ± 5/240 ± 10. The independent-atom approximation (IAA) overestimates the phase by up to 9%. Residual about 13 mrad against vacuum phase noise about 10 mrad |
| B5 | Z. Akase, D. Shindo, "Effects of Dynamical Electron Diffraction on Phase Shift Detected by Electron Holography", Mater. Trans. 60(10), 2120-2124 (2019), DOI 10.2320/matertrans.MT-MI2019007 | https://www.jstage.jst.go.jp/article/matertrans/60/10/60_MT-MI2019007/_pdf | Full text | 300 kV JEM-3000F, single biprism; FIB wedge of Si(100), wedge angle about 52°; two-beam 220 condition; Bethe-method calculation with 9 beams (220 systematic row), no absorption, V0(Si) = 11.5 V | Argand-plane trajectory of the object wave against thickness; intensity and phase against thickness (Fig. 1); BF image, phase image and profile (Fig. 2); 14-step tilt series (Fig. 3) | π phase jumps at dark thickness fringes, calculated at 50.8, 152.0 and 253.2 nm (ξ220 = 108 nm); phase slope against thickness depends on the sign of s220; tilt steps of 0.39 mrad over 5.04 mrad |
| B6 | Y. Cho et al., "Suppressing Geometric Phase Shift Owing to Antiphase Boundaries in Dark-Field Electron Holography", Mater. Trans. 60(5), 698-703 (2019), DOI 10.2320/matertrans.MC201809 | https://www.jstage.jst.go.jp/article/matertrans/60/5/60_MC201809/_pdf | Full text | 300 kV Hitachi HF3300S, two biprisms, Gatan USC4000 CCD. Dark-field holograms are formed with one reflection selected by the objective aperture. **The reference region is inside the specimen (free of APBs), not vacuum** | BF/DF images for 000, 100 and 200; holograms and phase images for each spot (Fig. 5); line profiles across an APB (Fig. 6); wavelet/HMM denoising (Fig. 7) | Kinematic phase 2π g·R. With the 100 superlattice reflection Δφ ≈ 2.3 rad, against π expected. With 200 there is no step beyond ±0.3 rad, which is the DF uncertainty; the weak Bragg beam limits precision |
| B7 | T. Wagner, H. Çelik, D. Berger, I. Häusler, M. Lehmann, Phys. Rev. B 109, 085310 (2024), DOI 10.1103/PhysRevB.109.085310 | https://arxiv.org/pdf/2405.08505 | Full arXiv text | 200 kV Titan 80-300 "Berlin Special Holography" TEM, Lorentz mode (wide field), vacuum reference; iGate with a biprism in the condenser aperture plane; Si diodes | Wrapped phase frames against time; normalised unwrapped phase profiles and slopes against bias; phase slope against time | 25 ns gate at 3 MHz, 11.1 ns sampling, 33 frames. Fringe contrast is reduced by the gate fraction, so 5 holograms are averaged per frame (8 s each, Gatan US1000) |
| B8 | A. Šilinga et al., Microsc. Microanal. 31(3), ozaf043 (2025), DOI 10.1093/mam/ozaf043 | https://arxiv.org/pdf/2411.15323 (v4) | Full arXiv text | 300 kV Titan G2 60-300; biprism at 100 V; fringe spacing about 3.1 nm; tilt arcs up to ±60° about two axes; Co nanowire | Workflow; hologram with FFT inset; aligned phase tilt series; 3-D M field; Fourier shell correlation (FSC); point spread function (PSF) | Phase sensitivity 0.016 rad rms for 10 s; 5 x 2 s holograms per tilt; phase resolution no better than 6 nm; FSC 14.8 nm; µ0Ms precision 0.01 T per pixel; reliable for domains larger than 50 nm |

Lesser item (READ, no table row): Subakti et al., arXiv:2210.04027v1, published as Phys. Rev. Research 5,
033137 (2023), DOI 10.1103/PhysRevResearch.5.033137 (Crossref). It is transmission holography of mono-
and bilayer **steps** in h-BN. Fig. 2 places DFT-simulated and experimental projected potentials side by
side, with line profiles across the steps (simulation in red, experiment in black, grey bands for layer
number). The kV and biprism settings are deferred to their Ref. [27].

Not read beyond the record: Boureau et al., J. Appl. Cryst. 53, 885-895 (2020), DOI
10.1107/S1600576720006020. Only the HAL API record was read (title, authors and the abstract on dark-field
holography versus high-resolution X-ray diffraction and the geometric phase). Not used above.

## 3. Common figure types and metrics, and what a simulation paper should show

Figure types found in the reflection papers (READ in A1-A6):
1. Optics schematic of the REM arrangement with the biprism below the objective (A3 Fig. 1, A4 Fig. 20,
   A6 Figs. 1 and 4).
2. Single-step geometry sketch with Δφ = 2KΔz sinθ (A2 Fig. 1; A6 Fig. 2).
3. **Interferogram** (cosine of the phase, from optical reconstruction): parallel fringes that shift at
   steps (A3 Fig. 2, Pt(111), 0.1 µm bar). Fringes bend, end and spiral around an emerging dislocation,
   shown as a 3-D perspective block with step, core and Δφ labels and **two different scale bars
   (0.5 µm / 1 µm)** (A2 Fig. 2 = A4 Fig. 21a = A5 Fig. 7).
4. Calculated surface topography (3-D mesh) derived from the interferogram (A4 Fig. 21b).
5. Phase-amplified contour maps (2x to 32x) are standard in the same group's transmission work (A4
   Fig. 17, A5 Figs. 5-6). No amplified *reflection* map was seen in the pages read.

Reflection numbers that a simulation can be compared with (READ):
* Height per fringe: 0.5 Å (GaAs(110): A2, A5) and 0.05 nm (A4). Sensitivity about 0.01 nm (A1).
  Precision about 1/100 wavelength (A6).
* Phase per monatomic step: about 0.5 λ (π) for a 2.3 Å Pt(111) step (A3); π for Au(111) and 0.9π for
  Pt(111) (A7b). In general this is the refraction residual of 2nπ (A3).
* Dislocation contrast: one-sided strain concentration (surface relaxation, agrees with isotropic
  elasticity); integer fringes starting or ending at the core give b_z (A3); a "spiral staircase" that is
  steep only opposite the step (A5).
* Reference wave: reflected from a defect-free surface region (A1-A3) or a direct vacuum wave with defocus
  and biprism matching (A6).
* Not given in any reflection text read (NOT VERIFIED): kV, which reflection was used, exact glancing
  angle, biprism voltage, fringe spacing, lateral resolution, amplitude maps, line profiles, quantitative
  foreshortening factor.

Modern metrics (READ in B1-B8) a comparable simulation should report: fringe contrast μ; electrons per
pixel or dose (e⁻ nm⁻²); phase noise as the standard deviation in a featureless reference region, quoted
as 2π/N at a stated filter size; sideband separation and an effective resolution of about 3 fringe
spacings; a hologram FFT with the sideband mask; phase and amplitude maps; **line profiles across steps
with error bands**; side-by-side simulated and experimental maps with **difference maps**; tables of mean
phase per feature; phase against thickness or tilt for the dynamical regime (Argand plots, π jumps); and
for dark-field work, which reflection g was used, the g·R selection rule and the DF phase uncertainty
(±0.3 rad in B6).

Recommended set for the Si(001) (008) simulation (INFERENCE from the above):
* (i) A foreshortened REM intensity image with anisotropic scale bars.
* (ii) The simulated hologram, its FFT and the sideband mask.
* (iii) Wrapped phase, unwrapped phase and amplitude.
* (iv) A cosine interferogram, optionally phase-amplified 2^n, styled like A2 Fig. 2 and A3 Fig. 2.
* (v) Phase line profiles across each step, in rad and in Å via h_2π, with the noise band.
* (vi) The step phase compared with the kinematic refraction formula of A3, against glancing angle (a
  rocking series, the analogue of the B5 tilt series).
* (vii) The dislocation: fringe termination count (integer part) and its link to b_z and g·b, plus the
  one-sided strain asymmetry.
* (viii) Phase noise against dose with μ and N_el stated, so that B2 eq. (16.10) can be applied.
* (ix) The reference choice (reflected flat terrace versus vacuum) and its effect.

## 4. Inferences (not facts from the sources)

* DERIVED_HERE: the A3 formula evaluated for Si (008) at 200 keV (λ = 0.025079 Å, d008 = 0.6789 Å,
  θ_B = 18.47 mrad), using the relativistic refraction parameter Δ = V0(1+T/mc²)/(T(1+T/2mc²)):
  * 4-layer step (5.431 Å, n = 8): 44.83 rad (wrapped +0.85 rad) at V0 = 12 V; 43.91 rad (wrapped
    −0.08 rad) at 13.9 V.
  * 1-layer step (1.358 Å, n = 2): 11.21 rad (wrapped −1.36 rad) at V0 = 12 V.
  * This matches the magnitudes in docs/results/three_strips_plan.md (−44.8 rad, wrapped −0.85 at
    12 V; 0.08 at 13.9 V; the sign differs by convention).
  * So the project's "refraction residual" result has a published kinematic counterpart (A3).
  * A3's own wording uses V0/E. That non-relativistic form gives 45.63 rad.
* INFERENCE: at the exact Bragg condition the height per fringe is about d_hkl. "0.5 Å per fringe" with
  2 Å GaAs(110) steps fits a specular reflection with d ≈ 0.5 Å (GaAs (880), d = 0.4997 Å), and so 4
  integer fringes per step. This is consistent with A3's remark that the integer part was "generally not
  observed". The reflection used was not read (NOT VERIFIED). For Si (008), a single-layer a/4 step is
  about 2 fringes plus the residual.
* INFERENCE: B4 (IAA overestimating the phase by about 9% in WSe2) bears on the project's choice between
  the parameterisation MIP (13.9 V) and 12 V. Direct transfer to Si is not established.
* INFERENCE: B6 is the closest modern analogue of a reference taken from a defect-free crystal region and
  of g-dependent defect phase. B5 shows that dynamical phase depends on excitation error, which supports a
  glancing-angle (rocking) series in the reflection simulation.

## 5. Documents to request from Ali (paywalled or blocked here; not used above)

1. Osakabe et al., PRL 62, 2969-2972 (1989), DOI 10.1103/PhysRevLett.62.2969, with the erratum PRL 63, 584
   (APS blocked; Europe PMC has no abstract).
2. Osakabe et al., JJAP 27, L1772 (1988): full PDF (IOP sign-in).
3. Osakabe, Microsc. Res. Tech. 20, 457-462 (1992), and Banzhof, Herrmann, Lichte, ibid. 450-456 (Wiley
   blocked).
4. Banzhof and Herrmann, "Reflection electron holography", Ultramicroscopy 48, 475-481 (1993), DOI
   10.1016/0304-3991(93)90123-F (Elsevier blocked).
5. Osakabe, Matsuda, Endo, Tonomura, "Reflection electron holographic observation of surface displacement
   field", Ultramicroscopy 48, 483-488 (1993), DOI 10.1016/0304-3991(93)90124-G (Crossref verified).
6. Osakabe, "Application of electron holography to surface topography observation", Surf. Sci. 298,
   345-350 (1993), DOI 10.1016/0039-6028(93)90047-N (Crossref verified).
7. **Tanji, Ito, Yada, "Contrast simulation of high resolution electron holography on surface
   structures", Ultramicroscopy 35, 245-253 (1991), DOI 10.1016/0304-3991(91)90076-I.** This is a
   simulation paper that cites PRL 1989 and is the most direct precedent for this project.
8. Herring, "Reflection diffracted beam interferometry (RDBI) applied to the study of surfaces", Proc.
   EMSA 53, 116-117 (1995), DOI 10.1017/s0424820100136957; Osakabe et al., Proc. EMSA 47, 536-537 (1989),
   DOI 10.1017/s0424820100154652 (cambridge.org HTTP 400).
9. Boureau et al., J. Appl. Cryst. 53, 885-895 (2020), DOI 10.1107/S1600576720006020 (dark-field
   holography theory and geometric phase; only the HAL API record was read).
10. Tonomura, "Electron-holographic interference microscopy", Adv. Phys. 41, 59-103 (1992), DOI
    10.1080/00018739200101473 (cites PRL 1989; not attempted).
