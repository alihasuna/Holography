# L1 — Holography open sources: P07 (Harada 2021) and PAT01 (US 4,998,788)

Prepared 2026-09-22 by the literature-researcher agent, step 2 of `docs/07_reading_plan.md`
(holography sources). Network access: Full. Report written incrementally.

Raw downloads are kept only in the session scratchpad
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/sources/`
(not in the repository; copyrighted text is not committed). Retrieval date of every file: 2026-09-22.

Status: complete (all seven sections written). Nothing in the repository other than this file was edited;
nothing was committed.

Evidence labels: METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT, ASSUMPTION,
DERIVED_HERE, UNVERIFIED. `SECTION_READ(P07)` means "read in P07 at the stated locator"; a
statement that P07 makes about another paper is SECTION_READ of P07 only and stays UNVERIFIED for
the cited paper.

## 1. Sources read

### 1.1 P07 — K. Harada, "Interference and interferometry in electron holography", Microscopy 70(1), 3-16 (2021)

| Item | Value |
|---|---|
| Identity | METADATA_VERIFIED (Crossref `api.crossref.org/works/10.1093/jmicro/dfaa033`: title as above, container "Microscopy", volume 70, issue 1, page 3-16, single author Ken Harada, published online 2020-06-26, print 2021-02-01, licence CC BY 4.0, 99 references) |
| Full text read | JATS XML from NCBI E-utilities `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=7850541&retmode=xml` (file `P07_PMC7850541_efetch.xml`, SHA-256 `6ba6b928b0ade5cb7ee4ba67d7d258d2cc30c36f1bd4b5c58cdfb555fdbed4a9`), converted locally to text; cross-checked against the PMC HTML `https://pmc.ncbi.nlm.nih.gov/articles/PMC7850541/` (file `P07_PMC7850541.html`, SHA-256 `76b0c8de97066622d9072a503d56b13ed2dccd315d44e3b2a3a2ab29310af57f`) for headings and the wording of the reflection-holography sentence |
| What was read | The whole article: abstract, all body sections (Introduction to Conclusion), all 14 figure captions, Table 1, equations (1)-(33), acknowledgement, funding, all 99 reference-list entries |
| Figures viewed as images | Fig. 8 (`P07_dfaa033f8.jpg`, SHA-256 `d619b9a5bd47b4e7ea326382666463a3ea6a34e5a57907b2544299f132c68dcd`), Fig. 9 (`P07_dfaa033f9.jpg`, `31d440a762057c38936cdbeb8492dfddb13dd9a7d186da425205cb40b7b187c1`), Fig. 11 (`P07_dfaa033f11.jpg`, `31b483569f0e8f519436308639f26597ef36fbea99cee012aad624b432a9eded`); Fig. 7 downloaded (`P07_dfaa033f7.jpg`, `ee4f3a7cd8636c9e875de627d5450a8913d98956ce89eca3308cbb0381a2a67f`), caption only used. Source URLs `https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4c62/7850541/<id>/dfaa033f{7,8,9,11}.jpg` |
| Crossref record | `crossref_P07.json`, SHA-256 `63ce9784c01033d36bd3e52d352a0f291e9ed106eb6ff058d733e92216acdd38` |
| Not obtained | The journal-typeset PDF. `https://pmc.ncbi.nlm.nih.gov/articles/PMC7850541/pdf/dfaa033.pdf` returned a browser proof-of-work page ("Preparing to download ..."), Europe PMC's PDF renderer returned a Cloudflare challenge (403), `https://academic.oup.com/jmicro/article/70/1/3/5862540` (the DOI redirect target) returned 403. None of these was circumvented. |
| Consequence for locators | The PMC HTML and the JATS XML show **no section numbers and no journal page breaks** (checked: no page markers in either file). Locators below are therefore given as PMC section heading, paragraph number counted in the JATS body (¶1 to ¶69, my count, reproducible from the XML), equation number and figure number as printed. Journal page numbers are NOT given for any statement: they would need the typeset PDF (request from Ali, or any reader with a browser: it is open access). Section numbers: P07's own text refers to "Section 6.1" for the optical reconstruction method (¶53), which is consistent with numbering the top-level headings 1 Introduction, 2 Principle of holography, 3 Coherence, 4 Wave/particle duality, 5 Electron interference optical systems, 6 Reconstruction systems, 7 Conclusion; this numbering is DERIVED_HERE from that one cross-reference and the heading order, not read as printed labels. |

### 1.2 PAT01 — US 4,998,788, "Reflection electron holography apparatus"

| Item | Value |
|---|---|
| Identity (front page of the printed patent, read as an image) | Inventors "Nobuyuki Osakabe, Kodaira; Akira Tonomura, Koganei, both of Japan"; assignee "Hitachi, Ltd., Tokyo, Japan"; Appl. No. 462,769; filed Jan. 10, 1990; foreign priority Jan. 13, 1989 [JP] 1-4999; date of patent Mar. 12, 1991; Int. Cl. G03H 5/00; 8 claims, 3 drawing sheets; other publications cited: "Optic Suppl. 377 (1987), p. 4." and "Jpn. J. Appl. Phys. vol. 27, No. 9, (1988/9), pp. L1772-L1774." Label: METADATA_VERIFIED (read on the printed front page) |
| Printed patent read | `https://patentimages.storage.googleapis.com/52/82/be/74e9d4589620ff/US4998788.pdf` (file `PAT01_US4998788.pdf`, 7 pages, SHA-256 `953d8a81b0df4c3bbd4c5b382d16462afbba3fdd308aad94c67cbd670b52cf06`), rendered locally page by page and read as images: front page with abstract and Fig. 1, drawing sheets 1-3 (Figs. 1-4), columns 1-6 (background, summary, brief description of drawings, description of both embodiments, claims 1-8). Column/line locators below are the printed column numbers and the gutter line numbers (every 5 lines; intermediate lines counted by me) |
| Machine text read | `https://patents.google.com/patent/US4998788A/en` (file `PAT01_US4998788A_google.html`, SHA-256 `8bbdff8d52913c7de1dfe752b11e67e3c297ee5e19a457a620627f81b9b011c6`): abstract, description, claims, bibliographic events, family, citations. Used only to navigate; every quotation below was checked against the printed image. The Google text contains OCR errors (claim 2 appears as "according to claim 4 ... 1," where the print reads "according to claim 1"; Eq. (2) and the fraction "1/3" are mangled) |
| Family member read (secondary) | EP 0 378 237 B1: Google Patents text `https://patents.google.com/patent/EP0378237B1/en` (file `EP0378237B1_google.html`, SHA-256 `99710b59e2ad1c4d301026e95489ad4e55c9960685cf6bcde39c777bf2571430`) read for description and claims; printed EP B1 `https://patentimages.storage.googleapis.com/c7/3b/e1/c64129eff9efe4/EP0378237B1.pdf` (file `EP0378237B1.pdf`, SHA-256 `a3c2791314443fd6eb29a2a2760e18c9476f2f7fc71339c5c96f8c06858a81e2`) viewed only at Eq. (2) (page 3, right column, lines 10-19). EP bibliographic data (filed 1990-01-12, published 1997-12-03, same inventors) are from the Google record only |
| Related patent, partly read | US 5,192,867 "Electron optical measurement apparatus", USPTO image `https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5192867` (file `US5192867.pdf`, 14 pages, image only, SHA-256 `befb511585006a80aafbfd8d20ed70cd3eb7c2255bbfa534c4f249c984f272b5`). Read: front page; page 11 (cols. 3-4, objects, brief description of drawings, Figs. 3 and 4 embodiments); page 13 middle (col. 7, biprism deflection and fringe-scanning equations). Viewed as thumbnails only: drawing sheets 1-8. Not read: cols. 1-2, 5-6, 8-10 (rest of description and claims). See section 6 |
| Not obtained | USPTO full-text (ppubs) record of US 4,998,788 was not needed because the printed image was read. Google Patents started returning a rate-limit page ("Sorry...", HTTP 503) for further patents (US 5,192,867 text, US 10,424,458 B2, EP 4 411 783 A1); not circumvented |

## 2. P07 extraction table

Locators: PMC section heading; top-level section number in brackets is DERIVED_HERE (see 1.1); ¶ = paragraph number counted in the JATS body; equation and figure numbers as printed. No journal page numbers (not shown by PMC; typeset PDF not obtained).

### 2.1 Reflection holography and Osakabe's arrangement

| # | Fact | Locator | Label | Note |
|---|---|---|---|---|
| P07-1 | The only passage of P07 on reflection holography: after Eq. (11), "The first term gives a geometrical optical path difference exemplified in miller microscopy [44] and reflection electron holography [45, 46]" | "Electron waves and their interaction with electromagnetic fields" [4.3], ¶29, Eq. (11) | SECTION_READ(P07) | "miller microscopy" is printed so in both the PMC HTML and the JATS XML; P07's ref 44 is a Michelson interferometer paper, so the word may be a typo; not resolved here |
| P07-2 | Eq. (11): `Delta S/hbar ~ closed-loop integral of (k - (eV/2E) k - (e/hbar) A) . ds`, with `abs(k) = sqrt(2mE)/hbar`, obtained from Eq. (10) under `E >> eV`; Eqs. (7)-(10) are the Schrodinger equation, WKB phase and loop phase difference in a "non-relativistic approximation" (¶26) for weak fields where electrons "are not largely deflected" | ¶26-¶29, Eqs. (7)-(11) | SECTION_READ(P07) | P07's framework is a phase-object (WKB, small-deflection) picture; it does not treat Bragg reflection, refraction or dynamical scattering |
| P07-3 | P07 attributes the reflection-holography phase to the first (geometric path) term of Eq. (11) | ¶29 | SECTION_READ(P07) about P01/P02; UNVERIFIED for P01 and P02 | Statement about other papers; consistent with the P08 abstract-index wording in B report 1.4, but that is not evidence for P01 |
| P07-4 | Reference-list entry 45, verbatim (JATS): "Osakabe N, Matsuda T, Endo J, and Tonomura A (1988) Observation of atomic steps by reflection electron holography. Jpn. J. Appl. Phys. 27: L1772–L1774." | reference list, ref. 45 | SECTION_READ(P07) | = project P01. Crossref's reference match for P07 ref 45 gives DOI 10.1143/JJAP.27.L1772 |
| P07-5 | Reference-list entry 46, verbatim (JATS): "Osakabe N, Endo J, Matsuda T A, and Fukuhara A (1989) Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography. Phys. Rev. Lett. 62: 2969–2972." with DOI 10.1103/PhysRevLett.62.2969 | reference list, ref. 46 | SECTION_READ(P07) | = project P02. The author list is garbled in P07: Crossref gives Osakabe, Endo, Matsuda, Tonomura, Fukuhara (Tonomura is merged into "Matsuda T A"). Do not copy P07's author string |
| P07-6 | P07 does NOT describe Osakabe's arrangement: no surface, energy, reflection order, glancing angle, reference-wave path or biprism position is given for reflection holography anywhere in the text, captions, table or figures | whole article (full text read; also searched for reflect, surface, glanc, grazing, Bragg, Osakabe, step) | SECTION_READ(P07) (negative result) | The task items "Osakabe's arrangement as P07 describes it" therefore have no content in P07. P07 is not a source for CFG-O parameters |
| P07-7 | P07 makes no statement on reflection holography after 1993, and does not cite P03 (Banzhof and Herrmann 1993), P08 (Osakabe 1992) or P09 (Banzhof, Herrmann and Lichte 1992); no reference-list entry by Banzhof exists | whole article; reference list refs. 1-99 | SECTION_READ(P07) (negative result) | The "nothing since 1993" question is not addressed by P07 |
| P07-8 | History given: holography invented 1947 by Gabor as an aberration-correction method [3, 4]; laser holography 1962 by Leith and Upatnieks [9]; "In 1978 Tonomura et al. realized a practical-level electron holography using a field-emission transmission electron microscopy (TEM) with an acceleration voltage of 70 kV [12]"; biprism invented 1955 by Möllenstedt and Düker [25] | Introduction [1], ¶2-¶4; "Electron biprism" [5.1], ¶31 | SECTION_READ(P07) | P07 gives no history of reflection holography beyond P07-1 |

### 2.2 Holography principle, coherence and biprism optics

| # | Fact | Locator | Label | Note |
|---|---|---|---|---|
| P07-9 | Hologram of object wave `Phi_Obj = phi_Obj exp(i eta_Obj)` and reference `Phi_Ref`; with the object wave parallel to the axis and a plane reference "tilted by an angle α in the x-direction", `I = abs(phi_Obj)^2 + 1 + 2 phi_Obj cos[eta_Obj - 2 pi R0x x]` with carrier `R0x = (sin α)/λ` | "Two-wave interferometry as holography" [2.1], ¶10-¶12, Eqs. (1)-(4) | SECTION_READ(P07) | R1-type reference (tilted plane wave). P07 assumes a real object amplitude and unit reference in Eq. (4) |
| P07-10 | "The component by the tilt angle of the reference wave can be easily corrected during the reconstruction procedure" | [2.1], ¶14 | SECTION_READ(P07) | Pure tilt only; residual curvature (R3) is not discussed anywhere in P07 |
| P07-11 | Table 1 classifies image holography (Δf = 0), Fresnel (Δf ≤ d²/λ), Fraunhofer (Δf >> d²/λ), Fourier transform (Δf = ∞) and lens-less Fourier transform holography | "Categorization of holography" [2.2], ¶15, Table 1 | SECTION_READ(P07) | |
| P07-12 | Spatial coherence length `l_s = λ/(2β)` (Eq. 5); temporal coherence length `l_t = λ²/Δλ` (Eq. 6) | [3.1] ¶17, Eq. (5); [3.2] ¶19, Eq. (6) | SECTION_READ(P07) | P07's numerical example in ¶18 is for 300 kV; not used in this project (200 keV) |
| P07-13 | Electrostatic biprism: filament electrode (metal-coated glass wire, diameter "about 1 μm or less") between grounded plates; positive filament potential deflects both waves "in the linearly converging directions", negative in diverging directions; deflection `α = k_f V_f` independent of incidence position, `k_f` "~10^−6 rad V^−1" | "Electron biprism" [5.1], ¶31-¶32, Eq. (13), Fig. 7 | SECTION_READ(P07) | |
| P07-14 | Single-biprism system: one biprism "placed between an objective lens and an image plane"; object wave through the specimen passes one side of the filament, "the reference wave passed through the vacuum area passes through the left side"; fringe spacing and width at the object plane `s_obj = (1/M_obj) Dλ/(2α(D−L))`, `W_obj = (1/M_obj) 2αL − (1/M_obj) D d_f/(D−L)` | "Single biprism interference system" [5.2], ¶33-¶34, Eqs. (14)-(15), Fig. 8 (viewed) | SECTION_READ(P07) | Transmission geometry. Disadvantages stated in ¶35: s and W not independently adjustable; filament Fresnel fringes superimposed on holograms |
| P07-15 | Double-biprism system: upper filament "placed just on the image plane (a real space) of the objective lens"; lower filament "between the crossover plane of the magnifying lens (a Fourier-transformed reciprocal space) and the image plane, which is in the shadow area of the upper filament electrode"; s and W independently controllable (Eqs. 16-17; procedure ¶38-¶39); Fresnel fringes of the upper filament fall only on the edges of the interference region, so the method "in principle does not create Fresnel fringes on the holograms" | "Double biprism interference system" [5.3], ¶36-¶42, Eqs. (16)-(17), Figs. 9 (viewed) and 10 | SECTION_READ(P07) | P07 cites refs. 64 (Harada et al. 2004, = project P47) and 65 (Harada et al. 2005). What P07 says about refs 64/65 is UNVERIFIED for those papers |
| P07-16 | Coherence limit: "the coherence length can be taken to be about 10 times the diameter of the filament electrode on the first image plane for the specimen", so object and reference waves must be close; split illumination removes this restriction "partially but effectively" | "Split illumination interference system" [5.4], ¶43 | SECTION_READ(P07) | Relevant to how far a vacuum reference may be from the reflecting area (R1) |
| P07-17 | Split illumination: "The condenser biprism placed above the specimen separates the irradiating electron wave into two waves"; the object wave irradiates regions far from the specimen edge; the reference passes a region far from the edge "where leaked magnetic fields from the specimen are sufficiently small"; Fresnel fringes of the condenser biprism can be removed with a double-biprism irradiation system [67]; Fig. 11 shows condenser, upper and lower biprisms | [5.4], ¶44, Fig. 11 (viewed) | SECTION_READ(P07) | Refs. 66 (= P45), 67 (= P46). Transmission geometry only; P07 does not discuss split illumination for reflection |
| P07-18 | Outlook: "The double biprism holography and the split illumination holography are expected to be the mainstream of the interference microscopy in the near future" | [5.4], ¶45 | SECTION_READ(P07) | Upgrades the B report's +ABSTRACT(index) quotation to SECTION_READ |
| P07-19 | Other systems: amplitude-division (Mach-Zehnder, crystal-film beam splitters) ¶47; scanning-type ¶48; Fraunhofer and lens-less Fourier transform holography with "Bragg diffraction waves as the vortex beams from the grating" as object waves and a transmitted spherical wave as reference (Figs. 12-13) ¶49-¶50 | "Other optical systems of electron holography" [5.5], ¶46-¶50 | SECTION_READ(P07) | Diffracted beams as object waves, but transmission gratings, not reflection |

### 2.3 Reconstruction methods

| # | Fact | Locator | Label | Note |
|---|---|---|---|---|
| P07-20 | Optical reconstruction is "so cumbersome that it is no longer used" | "Optical method" [6.1], ¶52 | SECTION_READ(P07) | |
| P07-21 | Fourier transform method: FT of the hologram (Eqs. 18-20), select one sideband, move it by R0 to the origin (Eq. 21), inverse FT (Eqs. 22-23), amplitude and phase from real and imaginary parts (Eqs. 24-25), cosine interferogram display (Eq. 26); described as "the most common method" | "Fourier transform method" [6.2], ¶53-¶61, Eqs. (18)-(26), Fig. 14 | SECTION_READ(P07) | Eq. (25) is written as `tan^−1(Î_I/Î_R)`; an implementation needs the two-argument arctangent (DERIVED_HERE remark). P07 does not state its Fourier-transform sign convention while placing the sideband of `phi_0 exp(i(eta_0 − 2 pi R0 x))` at `R_x − R0` (Eq. 19); the project must fix its own convention (`docs/physics_conventions.md`) rather than copy P07's labelling (DERIVED_HERE remark) |
| P07-22 | Sideband separation rule, verbatim: "the spreads of the distributions of terms A must be two-third or less than R0, and those of B and B* must be one-third or less than R0. Therefore, three times the interference fringe spacing {1/(3R0)} becomes the maximum resolution" | [6.2], ¶56 | SECTION_READ(P07) | Supports SM12's "about three fringe spacings". The bracketed expression as printed, 1/(3R0), is one third of a fringe spacing and contradicts the words "three times the interference fringe spacing" (3/R0); cite the words, not the bracket |
| P07-23 | Phase-shift method: M holograms with known phase offsets φ(m), `I_H(x,y;m) = a + c e^{iφ(m)} + c* e^{−iφ(m)}` (Eqs. 27-28), least-squares matrix inversion (Eqs. 29-30), diagonal when the offsets divide 2π equally, amplitude and phase from Eqs. (31)-(33); requires changing the phase of reference or object wave "while keeping the other optical conditions, such as the specimen position and its focus constant" (¶51); "now most commonly used for achieving high-resolution and high-precision" data (¶62) | "Reconstruction systems" [6], ¶51; "Phase shift method" [6.3], ¶62-¶67, Eqs. (27)-(33) | SECTION_READ(P07) | For the project: a phase-shift series needs hardware phase stepping (e.g. biprism or beam tilt), which is a PROJECT_INPUT; the simulation parameter "freely adjustable relative phase" (docs/05 section 5 item 3) is not evidence of it |

## 3. PAT01 extraction table

Locators: printed column (col.) and line (l.) numbers of US 4,998,788; Fig. numbers as printed. The patent prints a line number every fifth line; intermediate line numbers were counted on the image and may be off by one line. Quotations are at most two sentences, copied from the printed image.

### 3.1 Bibliographic facts

| # | Fact | Locator | Label |
|---|---|---|---|
| PAT-1 | Inventors: Nobuyuki Osakabe (Kodaira) and Akira Tonomura (Koganei), only these two | front page [75] | METADATA_VERIFIED |
| PAT-2 | Assignee Hitachi, Ltd., Tokyo | front page [73] | METADATA_VERIFIED |
| PAT-3 | Appl. No. 462,769, filed Jan. 10, 1990; priority JP 1-4999 of Jan. 13, 1989; patent dated Mar. 12, 1991 | front page [21], [22], [30], [45] | METADATA_VERIFIED |
| PAT-4 | Prior art cited: "Optic Suppl. 377 (1987), p. 4." (front page) printed in col. 1 as "Optic Suppl. 3 77 (1987) page 4"; EP 0 378 237 B1 (Google citation metadata) gives "Optik Supplement 3, 77 (1987), page 4"; and "Jpn. J. Appl. Phys. vol. 27, No. 9, (1988/9), pp. L1772-L1774" (= P01) | front page "Other publications"; col. 1 l. 13-15 | METADATA_VERIFIED for the citation strings as printed; the Optik item itself is UNVERIFIED (not identified) |
| PAT-5 | The B report's inventor list (Osakabe, Endo, Tonomura, Tomita, Furutsu) and dates ("filed 9 May 1991, granted 9 March 1993") belong to the related US 5,192,867, not to US 4,998,788 | US 5,192,867 front page [75], [22], [45], [63] | METADATA_VERIFIED (both front pages read) |

### 3.2 Technical content

| # | Fact (quotation or paraphrase) | Locator | Label | Note |
|---|---|---|---|---|
| PAT-6 | Field: an apparatus "suitable for the precise measurement of undulation of the surface of a solid specimen and for the measurement of magnetic field perpendicular to a specimen" | col. 1 l. 6-12 | SECTION_READ | |
| PAT-7 | Prior art (including P01): "electron waves reflected from a specimen are caused to interfere with each other in an electron microscope to obtain about ten interference fringes whose shifts are measured to determine the height of a surface step." | col. 1 l. 13-19 | SECTION_READ(PAT01) about P01; UNVERIFIED for P01 | Written by P01's first and last authors about one year after P01, but it is still not P01. Suggests an R2-type (reflected-reflected) interference for P01 |
| PAT-8 | "In the prior art, the interference pattern is produced between object waves (reflected waves from a specimen) and therefore difficult for the analysis thereof, which is quite different from that of an usual interference micrograph where a reference plane wave interferes with an object wave modulated by a specimen." | col. 1 l. 21-27 | SECTION_READ(PAT01) about the prior art; UNVERIFIED for P01 | |
| PAT-9 | "If a reflected wave were made to interfere with a direct wave (a wave not illuminating a specimen), the interval between interference fringes would become narrower than the resolution limit of a presently available electron holography apparatus, necessarily leading to an electron hologram generated by interference between reflected waves as in the prior art." | col. 1 l. 27-33 | SECTION_READ | The patent's statement of the 2θ problem for a vacuum reference |
| PAT-10 | Object of the invention: an optical system "capable of superimposing a reflected wave upon a direct wave within a coherence length of an electron wave and forming a reflection electron hologram having a recordable fringe interval" | col. 1 l. 36-41 | SECTION_READ | R1-type reference |
| PAT-11 | The relative image-plane position of the reflection image and of the image of the non-illuminating wave changes with focus; "An electron biprism is provided between the specimen and an image recording device"; defocus and biprism potential are set to superimpose the two waves within the coherence length with a recordable fringe interval | col. 1 l. 42-57 | SECTION_READ | |
| PAT-12 | "by providing a plurality of electron biprisms, it becomes possible to change the intersecting angle between, and also change overlapping region of, the reflected wave and direct wave, independently from each other." | col. 1 l. 58-62 | SECTION_READ | Same principle P07 describes for double-biprism holography (P07-15), 14 years earlier in a patent |
| PAT-13 | Eq. (1): "d=Csα³−Δfα", the distance at the specimen position between reflection image and direct-wave image, "where Cs is the spherical aberration coefficient of the objective lens, and α is the angle between the reflected wave and direct wave"; the image order reverses when the defocus passes Csα²; with the biprism between image plane and specimen the intersecting angle becomes smaller than α for one ordering and larger for the other | col. 1 l. 65-68; col. 2 l. 1-16 | SECTION_READ | Handling of the reflected-direct inclination α in embodiment 1: choose the defocus sign so that the biprism reduces the intersecting angle |
| PAT-14 | Embodiment 1 (Fig. 1): condenser lens 2, aperture 3, "collimated electron wave"; "The electron wave is directed to a specimen 5 by means of a deflector 4, at an angle, e.g., at the Bragg angle causing a total reflection of the wave." | col. 2 l. 45-52; Fig. 1 | SECTION_READ | Only statement on the reflection: "e.g., at the Bragg angle"; no specimen material, surface, reflection order or angle value is given |
| PAT-15 | "The position of the specimen 5 and the position of the electron wave are so adjusted that a half of the electron wave does not illuminate the specimen." Reflected and direct waves are focused by objective lens 6 and pass an aperture 7 at the back focal plane, which intercepts inelastically scattered electrons | col. 2 l. 52-60; Fig. 1 | SECTION_READ | The reference (direct wave) passes beside the specimen, in vacuum, and is never reflected |
| PAT-16 | Single biprism 8 "mounted downstream of the aperture" (i.e. below the objective back focal plane, above magnifying lens 9); objective "over-focused by an amount of Δf so that Δf·α is larger than Csα³"; filament at negative potential "to diverge the reflected wave and direct wave"; result: superposition at the image plane "while making the intersection angle smaller than the angle between the reflected wave and direct wave at the specimen position" | col. 2 l. 60-68; col. 3 l. 1-4; Fig. 1 | SECTION_READ | Biprism number 1, position image side. Controller 13 sets objective and biprism supplies for the requested interference region and fringe interval (col. 3 l. 4-11) |
| PAT-17 | "Since this embodiment uses a single stage of an electron biprism, it is advantageous in that the apparatus does not require angle adjustment of biprism wire directions or the like so that it is easy to use." | col. 3 l. 17-20 | SECTION_READ | Upgrades the B report's UNVERIFIED summariser quotation |
| PAT-18 | Embodiment 1 needs a two-hole objective aperture: "The first embodiment requires two holes the distance between which varies with a diffraction condition." | col. 4 l. 30-32 | SECTION_READ | In an R1 geometry the objective aperture must pass both the reflected and the direct beam |
| PAT-19 | Fig. 2: step of height h, wave (I) reflected by the lower terrace, wave (II) by the upper; "the phase difference Δφ between two electron waves is simply obtained on the basis of a geometrical path difference therebetween"; Eq. (2) printed as "Δφ=2h sin θλ", "where λ is the wavelength of an electron wave, θ is the glancing angle of an electron wave" | col. 3 l. 21-34; Fig. 2 (sheet 2) | SECTION_READ | Eq. (2) is dimensionally inconsistent as printed in the US patent; the EP B1 prints "Δφ = 2 sin θ/λ" (page 3, right col., l. 10-13), which lacks h. No version read gives a consistent form, a 2π or a sign. Reading it as Δφ (in wavelengths) = 2h sinθ/λ is an inference (section 4.3) |
| PAT-20 | "Assuming that there is used an electron wave accelerated with 100 kV, the phase changes by about ⅓ of a wavelength if the step h is 0.1 Å. The measurement precision now available is about 1/100 of a wavelength." | col. 3 l. 34-38 | SECTION_READ | 100 kV is an assumption in a worked example, not a statement of the apparatus voltage. No angle is given for the example (see 4.3 for the angle it implies) |
| PAT-21 | Perpendicular magnetic field measurable in reflection because the beam travels "substantially in parallel to the specimen surface"; Eqs. (3) B = rot A and (4) Δφ = ∫A·ds (printed with ƒ for the integral sign) | col. 3 l. 43-64; Fig. 3 | SECTION_READ | Not needed for Si topography; relevant only if charging or stray fields are modelled |
| PAT-22 | Embodiment 2 (Fig. 4): the wave "is deflected by a deflector 4 and split into two electron waves by a first electron biprism 8'. By setting the angle between two split electron waves equal to the sum of the reflection angle and incident angle at a specimen, the reflected wave and direct wave incident to an objective lens 6 can be made approximately parallel." | col. 3 l. 65-68; col. 4 l. 1-7; Fig. 4 | SECTION_READ | Handling of the inclination in embodiment 2: pre-compensation by a condenser-side (illumination) biprism, i.e. a split-illumination arrangement for reflection |
| PAT-23 | Embodiment 2 needs only a single-hole objective aperture (parallel entry); "Second and third electron biprisms 8" and 8 are provided for superimposing the reflected wave and direct wave one upon the other. The use of the two stages of electron biprisms allows independent control of the intersecting angle and overlapping region." | col. 4 l. 7-18; Fig. 4 | SECTION_READ | Three biprisms in total (8', 8", 8): one illumination-side, two image-side in cascade below the back-focal-plane aperture (Fig. 4) |
| PAT-24 | Embodiment 2 splits the direct wave upstream of the specimen and suits specimens too large for embodiment 1; the three biprisms are controlled together with the objective lens | col. 4 l. 23-38 | SECTION_READ | |
| PAT-25 | Stated capability: "undulation on the surface of a specimen can be measured with a precision better than 0.1 Å by using reflection electron holography"; also perpendicular magnetic fields; bulk specimens | col. 4 l. 39-49 | SECTION_READ | A capability claim of the patent, not a reported measurement |
| PAT-26 | Claims: claim 1 (source; guiding means so that one part is reflected along a first path and another part "is directly passed along a second predetermined path without illuminating the surface of the specimen"; means controlling both paths to form an interference image); claim 3 (objective lens, apertured plate, "at least one biprism"); claim 4 (single aperture); claim 5 (two biprisms in cascade); claim 6 (biprism in the guiding means separating the illuminating and direct parts); claims 7 and 8 (independent; 8 combines illumination biprism, single-aperture plate and two cascaded biprisms) | col. 4 l. 50 to col. 6 l. 50 | SECTION_READ | |
| PAT-27 | Nothing in the patent states the accelerating voltage of an actual apparatus, the specimen material, the surface orientation, the reflection used or a glancing-angle value | whole document | SECTION_READ (negative result) | |

## 4. Items bearing on CFG-O and on the reference-wave models R1/R2/R3

### 4.1 Facts stated by the sources themselves

| # | Fact | Source, locator | Label | Bears on |
|---|---|---|---|---|
| F1 | P01 record: "Observation of Atomic Steps by Reflection Electron Holography", N. Osakabe, T. Matsuda, J. Endo, A. Tonomura, Japanese Journal of Applied Physics 27, issue 9A, first page L1772, issue date 1988-09-01 | Crossref `api.crossref.org/works/10.1143/JJAP.27.L1772` (file `crossref_10_1143_JJAP_27_L1772.json`, SHA-256 `991fae5ee764388e5f76379a0261b54f289d2e6d6d1059b2907a247ad5a720f1`) | METADATA_VERIFIED | CFG-O identity. Crossref gives no last page; "L1772–L1774" is printed in P07 ref. 45 and in PAT01 (front page; col. 1 l. 14-15); US 5,192,867 prints "pp. 1772-1774" without the L |
| F2 | P07 gives no CFG-O parameter (surface, energy, reflection, glancing angle, reference path, biprism) | P07 whole text | SECTION_READ(P07), negative | CFG-O stays UNVERIFIED after reading P07 |
| F3 | Hitachi's reflection-holography apparatus (1989 priority) interferes a reflected wave with a direct wave that does not illuminate the specimen | PAT01 abstract; col. 1 l. 36-41; claim 1 (col. 4 l. 51-66) | SECTION_READ | R1 |
| F4 | Embodiment 1: half the collimated beam misses the specimen; objective BFP aperture passes both beams (two holes, spacing depends on the diffraction condition); one image-side biprism at negative potential below the aperture; objective over-focused with Δf·α > Csα³ so the biprism reduces the intersecting angle below the reflected-direct angle α | PAT01 col. 2 l. 45-68; col. 3 l. 1-20; col. 4 l. 30-32; Fig. 1 | SECTION_READ | R1 with compensation of the inclination by defocus and a diverging biprism |
| F5 | Image offset at the specimen position between reflection image and direct-wave image: d = Csα³ − Δfα, α the angle between reflected and direct wave | PAT01 Eq. (1), col. 1 l. 65-68, col. 2 l. 1-11 | SECTION_READ | R1 (lateral registration of object and reference; spherical-aberration term) |
| F6 | Embodiment 2: a first biprism 8' in the illumination splits the beam; the split angle is set "equal to the sum of the reflection angle and incident angle at a specimen", so reflected and direct waves enter the objective approximately parallel; single-hole aperture; two cascaded image-side biprisms 8" and 8 set intersecting angle and overlap independently | PAT01 col. 3 l. 65-68; col. 4 l. 1-38; Fig. 4; claims 6 and 8 | SECTION_READ | R1 with pre-compensation of 2θ by a condenser-side biprism |
| F7 | The same reflection arrangement (beam split by deflector 38 and biprism 8', one beam to the specimen, "the other is used as a reference wave"; objective aperture 39; biprisms 8 and 8") appears in the later Hitachi patent, which adds biprism rotation about the optic axis | US 5,192,867 col. 4 l. 35-68; Fig. 4 | SECTION_READ | R1 |
| F8 | Phase at a step of height h from the geometric path difference between waves reflected by the lower and upper terraces, with θ "the glancing angle" and λ "the wavelength of an electron wave"; printed Eq. (2) is "Δφ=2h sin θλ" (US) and "Δφ = 2 sin θ/λ" (EP B1) | PAT01 col. 3 l. 21-34; Fig. 2; EP 0 378 237 B1 p. 3 right col. l. 10-16 | SECTION_READ (the equation as printed is defective in both publications) | SM03 premise; phase relation for CFG-O |
| F9 | Worked example: 100 kV assumed, about 1/3 wavelength for h = 0.1 Å; precision "about 1/100 of a wavelength" | PAT01 col. 3 l. 34-38 | SECTION_READ | 100 kV is an assumption of the example, not P01's energy |
| F10 | P07 classifies the phase in reflection holography (refs. 45, 46) as the geometric optical-path term of its Eq. (11) | P07 ¶29 | SECTION_READ(P07) | SM03 premise |
| F11 | For a tilted plane reference the carrier `R0x = sinα/λ` and the tilt "can be easily corrected during the reconstruction procedure" | P07 ¶12, ¶14, Eq. (4) | SECTION_READ(P07) | R1 carrier; R3 not covered |
| F12 | Object and reference must lie within a coherence length of about ten filament diameters (image-plane referred) in the standard system; split illumination relaxes this | P07 ¶43-¶44 | SECTION_READ(P07) | R1 distance between reflecting area and vacuum reference |

### 4.2 Statements by the sources about other papers (UNVERIFIED for the cited paper)

| # | Statement | Where | Label | Cited paper |
|---|---|---|---|---|
| S1 | In the prior art, "electron waves reflected from a specimen are caused to interfere with each other" giving "about ten interference fringes" whose shifts give the step height; the pattern is "produced between object waves (reflected waves from a specimen)" | PAT01 col. 1 l. 13-27 | SECTION_READ(PAT01); UNVERIFIED for P01 | P01 and "Optic Suppl. 3 77 (1987) page 4" jointly; the patent does not say which statement applies to which of the two |
| S2 | A reflected-direct (vacuum-reference) hologram was not recordable with the then available apparatus because the fringes would be finer than its resolution limit, "necessarily leading to an electron hologram generated by interference between reflected waves as in the prior art" | PAT01 col. 1 l. 27-33 | SECTION_READ(PAT01); UNVERIFIED for P01 | P01 (implied) |
| S3 | Reflection electron holography (refs. 45, 46) exemplifies the geometric optical-path term of Eq. (11) | P07 ¶29 | SECTION_READ(P07); UNVERIFIED for P01, P02 | P01, P02 |
| S4 | Double-biprism and split-illumination optics as summarised in P07-15 to P07-17 | P07 ¶36-¶45 | SECTION_READ(P07); UNVERIFIED for refs. 64-67 | P47, Harada 2005, P45, P46 |

### 4.3 Inferences (DERIVED_HERE; not stated by any source)

* **I1 (CFG-O reference model).** If S1 describes P01, the 1988 experiment used interference between reflected
  waves, not a vacuum reference: the CFG-O placeholder should default to an R2-type configuration (both arms
  reflected from the specimen) rather than R1. "Reflected waves ... interfere with each other" does not say
  whether the two arms were two regions of the same Bragg-reflected beam overlapped by a biprism (a
  self-reference, R2 proper) or two different reflected beams; both readings remain open until P01 is read.
  Confidence moderate: the statement is by P01's first and last authors, one year later, but it is not P01.
* **I2 (CFG-O reconstruction).** "About ten interference fringes whose shifts are measured" indicates
  fringe-shift interferometry over a small overlap region, not sideband reconstruction of a finely sampled
  hologram. A CFG-O reproduction should therefore compare fringe displacements (or a sideband
  reconstruction at a resolution of a few fringe spacings, P07-22) rather than a full-resolution phase map.
* **I3 (Eq. (2) and the worked example).** Neither printed form of PAT01 Eq. (2) is dimensionally consistent;
  the geometric-path reading is Δφ (in wavelengths) = 2h sinθ/λ, identical to SM03 in magnitude. With the
  patent's own example (λ = 0.037014 Å at 100 kV, relativistic; h = 0.1 Å; Δφ = 1/3 wavelength) this
  reading requires sinθ = λ/(6h) = 0.0617, θ = 61.7 mrad (3.54°). At 10, 20 and 30 mrad the same step gives
  0.054, 0.108 and 0.162 wavelength. The example therefore either assumes a large glancing angle or is
  rounded; it gives no information on P01's angle. Neither source states a sign, a 2π factor, refraction
  or which angle (external or internal) is meant.
* **I4 (the 2θ inclination).** For the specular beam and a vacuum reference parallel to the incident beam,
  PAT01's α ("the angle between the reflected wave and direct wave") and its "sum of the reflection angle
  and incident angle" (embodiment 2) both equal θ_in + θ_out = 2θ, measured in vacuum, i.e. `2 theta_ext`
  in docs/05 section 5 item 3. Uncompensated, the fringe spacing referred to the specimen would be
  λ/(2θ_ext) = 0.025079 Å / 0.033 = 0.76 Å for CFG-B (008) at 200 keV (θ_ext 16.5 mrad), which is the
  quantitative content of PAT01's statement S2 (it equals the height wrap period, as it must).
* **I5 (lateral registration, Eq. (1)).** With α = 2θ_ext the reflection and direct-wave images are offset
  by d = Csα³ − Δfα at the specimen plane. For Cs = 0.5 to 2 mm (ASSUMPTION; the laboratory value is a
  PROJECT_INPUT) and θ_ext = 13.6, 16.5, 22.5 mrad, Csα³ = 10-40, 18-72, 46-182 nm and the reversal defocus
  Csα² = 0.37-1.5, 0.54-2.2, 1.0-4.1 μm. An R1 model therefore needs the α-dependent image offset, the
  defocus and the objective Cs as explicit inputs, and it must say which of the two superposition branches
  (angle reduced or increased) the experiment uses.
* **I6 (dark-field aperture versus R1).** docs/05 section 5 item 1 applies the objective aperture around
  `k_out`. In PAT01 embodiment 1 the aperture has a second hole for the direct beam; in embodiment 2 the
  reference is pre-tilted by 2θ so that one hole passes both. A single aperture centred on `k_out` with an
  un-tilted vacuum reference blocks the reference. The optics module must therefore declare how the
  reference passes the objective aperture (second hole, pre-tilt by a condenser biprism, or no aperture).
* **I7 (Ali's condenser biprism).** PAT01 embodiment 2 and US 5,192,867 Fig. 4 are published
  reflection-mode split-illumination arrangements with a condenser-side biprism, the family to which the
  laboratory's gun-side biprism belongs (B report 6.2). This establishes a published precedent only; the
  laboratory's split angle, conjugate planes and residual inclination remain PROJECT_INPUT (item 16).
* **I8 (R3).** Neither source discusses reference curvature. P07 ¶44 motivates a distant reference by
  specimen stray fields; for reflection, a reference passing close above a charging or magnetised surface
  would acquire such a phase (PAT01 col. 3 l. 43-63 shows the reflected beam is sensitive to fields normal
  to the surface). R3 remains an ASSUMPTION without a source.

## 5. Proposed changes (proposals only; nothing applied)

### 5.1 `docs/source_map.tsv` rows (IDs provisional; tab-separated in the file)

```
SM18	Reflection-holography phase belongs to the geometric optical-path term of the WKB phase (P07 Eq. 11; non-relativistic phase-object framework)	P07	SECTION_READ	P07 section "Electron waves and their interaction with electromagnetic fields", para 29, Eqs. (7)-(11)	project uses relativistic vacuum wavelength; P07 does not treat Bragg reflection or refraction	none (context)	kinematic, lattice-translation steps	none	n/a
SM19	Vacuum ("direct") reference beside the specimen superimposed on the reflected wave; inclination alpha between them reduced by objective over-focus (Delta f alpha > Cs alpha^3) and one diverging image-side biprism below a two-hole BFP aperture; image offset d = Cs alpha^3 - Delta f alpha	PAT01	SECTION_READ	US 4,998,788 col. 1 l. 36-68; col. 2 l. 1-16, 45-68; col. 3 l. 1-20; col. 4 l. 30-32; Eq. (1); Fig. 1	alpha = 2 theta_ext for the specular beam (DERIVED_HERE, L1 report I4)	future optics/ R1 model	R1	planned (R1 offset and angle unit tests)	NOT RUN
SM20	Reflection split illumination: condenser-side biprism split angle equal to incidence plus reflection angle makes reflected and direct waves enter the objective parallel; two cascaded image-side biprisms set fringe spacing and overlap independently	PAT01; US 5,192,867	SECTION_READ	US 4,998,788 col. 3 l. 65 to col. 4 l. 38, Fig. 4, claims 6 and 8; US 5,192,867 col. 4 l. 35-68, Fig. 4	residual inclination is a parameter	future optics/ R1 model	R1 with pre-tilt	planned	NOT RUN
SM21	Prior-art reflection holography (P01 era) interfered reflected waves with each other, about ten fringes, fringe shifts give step height	PAT01 (statement about P01 and Optik Suppl. 3 77 (1987) p. 4)	SECTION_READ(PAT01); UNVERIFIED for P01	US 4,998,788 col. 1 l. 13-33	candidate R2 for CFG-O	configs/CFG-O (placeholder)	CFG-O only	none	UNVERIFIED until P01 read
SM22	Biprism deflection alpha = k_f V_f with k_f ~ 1e-6 rad/V (P07) ; gamma = gamma_0 U_F with gamma_0 about 2e-6 rad/V at 100 kV, fringe pitch lambda/(2 gamma) (US 5,192,867)	P07; US 5,192,867	SECTION_READ	P07 para 32, Eq. (13); US 5,192,867 col. 7 l. 21-52 (page 13)	coefficient depends on energy and biprism geometry; laboratory value is PROJECT_INPUT	future optics/ biprism model	all	none	n/a
```

Update of existing rows (proposed):

* SM03: add PAT01 col. 3 l. 21-34 (Eq. (2), Fig. 2) and P07 ¶29 as sources stating that the step phase is a
  geometric path difference with the glancing angle; evidence becomes "DERIVED_HERE; geometric-path premise
  SECTION_READ in PAT01 and P07 (neither states sign, 2π, refraction or external/internal angle; PAT01 Eq. (2)
  printed defectively)". Keep P08 as +ABSTRACT(index).
* SM12: add P07 ¶56 for the sideband separation rule (A ≤ 2/3 R0, B ≤ 1/3 R0, resolution "three times the
  interference fringe spacing"), label SECTION_READ(P07) for the rule, noting the printed bracket
  {1/(3R0)} contradicts the words. Add P07 Eqs. (18)-(26) for the Fourier method and Eqs. (27)-(33) for the
  phase-shift method.

### 5.2 `docs/model_assumptions.md` (proposed wording)

* B5: "R1 corresponds to the published Hitachi arrangement of a direct wave that does not illuminate the
  specimen (US 4,998,788 col. 1 l. 36-41, both embodiments; US 5,192,867 Fig. 4); R2 corresponds to the
  interference 'between reflected waves' that US 4,998,788 col. 1 l. 13-33 attributes to the prior art
  including P01 (UNVERIFIED for P01); R3 has no source. The laboratory arrangement remains PROJECT_INPUT."
* New limitation: "An R1 reference must pass the dark-field objective aperture; the model must declare
  whether it uses a second aperture hole, a condenser-biprism pre-tilt of 2θ_ext, or no aperture
  (US 4,998,788 col. 4 l. 1-7, 30-32)."
* Open question 1: add "Per US 4,998,788 col. 1 l. 13-33 the P01-era experiment interfered reflected waves
  with each other (about ten fringes); to be confirmed in P01 itself."
* Open question 5: add "Two published compensation schemes exist: objective over-focus with a diverging
  image-side biprism, and a condenser-side biprism pre-tilt equal to θ_in + θ_out (US 4,998,788)."

### 5.3 `docs/references.bib` (proposed corrections)

* PAT01: authors "Osakabe, Nobuyuki and Tonomura, Akira" (front page [75]); year 1991; filed 1990-01-10;
  priority JP 1-4999 of 1989-01-13; issued 1991-03-12; label METADATA_VERIFIED + SECTION_READ; delete the two
  summariser quotations and the "no year" warning; record that the five-inventor list and the 1991/1993
  dates belong to US 5,192,867.
* P07: add `doi = {10.1093/jmicro/dfaa033}` (Crossref match: title, journal, 70(1), 3-16, author Ken Harada);
  label SECTION_READ; note that P07 contains nothing on Osakabe's arrangement.
* P01: add `number = {9A}` (Crossref); DOI now Crossref-matched (title, four authors, volume, first page).
* P02: Crossref matches title, five authors (Osakabe, Endo, Matsuda, Tonomura, Fukuhara), 62(25), 2969-2972,
  1989-06-19; P07's reference 46 garbles this author list.
* P47, P45, P46: DOIs Crossref-matched (section 6).

## 6. New references found (with Crossref checks where a DOI exists)

| Record | How found | Check | Status |
|---|---|---|---|
| US 5,192,867, "Electron optical measurement apparatus", N. Osakabe, J. Endo, A. Tonomura, M. Tomita, T. Furutsu; Hitachi; appl. 697,576 filed May 9, 1991; patent Mar. 9, 1993; continuation-in-part of Ser. No. 663,472 (Mar. 4, 1991, abandoned), itself a continuation of Ser. No. 462,769 (printed there as "Nov. 10, 1990", whereas US 4,998,788 prints the filing date Jan. 10, 1990); priorities JP 1-004999 (Jan. 13, 1989) and JP 2-117544 (May 9, 1990) | PAT01 "Cited by" list on Google Patents; front page read on the USPTO image | Patent, no DOI | METADATA_VERIFIED (front page); SECTION_READ for col. 3-4 and part of col. 7 only. Resolves the B report's inventor and date confusion. Contains a reflection embodiment (Fig. 4) with condenser biprism 8' |
| EP 0 378 237 B1 (and JP 2776862 B2, DE 69031765 T2), family of PAT01 | Google Patents family table | Patent | Description and claims read on Google text; Eq. (2) read on the printed EP B1; bibliographic data from Google only (METADATA of Google record) |
| "Optik Supplement 3, 77 (1987), page 4" (form given in the EP record; US prints "Optic Suppl. 377 (1987), p. 4" and "Optic Suppl. 3 77 (1987) page 4") | PAT01 prior art | No DOI; not identified | UNVERIFIED. Apparently an earlier (1987) report of reflection interferometry of surface steps (PAT01 col. 1 l. 13-19 lumps it with P01). Author and title unknown. Request from Ali or a library |
| K. Harada et al., "Optical system for double-biprism electron holography", J. Electron Microsc. 54, 19-27 (2005) | P07 ref. 65 (DOI 10.1093/jmicro/dfh098 given in the PMC XML) | Crossref `works/10.1093/jmicro/dfh098` (SHA-256 `217bf3b5...f7b0`): title, journal, 54(1), 19-27, 2005 match; Crossref author list has only "K. Harada", P07 lists Harada, Akashi, Togawa, Matsuda, Tonomura | METADATA_VERIFIED for title/journal/volume/pages/DOI; author list UNVERIFIED (Crossref and P07 disagree) |
| P47 Harada et al. 2004, APL 84(17), 3229-3231 | already in bib | Crossref `works/10.1063/1.1715155` (SHA-256 `1502ce62...403e`): title, five authors, volume, issue, pages, 2004-04-26 match | METADATA_VERIFIED (upgrade from index) |
| P45 Tanigaki et al. 2012, APL 101(4), 043101 | already in bib | Crossref `works/10.1063/1.4737152` (SHA-256 `f54115dc...f01`): title, nine authors, volume, issue, article 043101, 2012-07-23 match | METADATA_VERIFIED (upgrade) |
| P46 Tanigaki et al. 2014, Ultramicroscopy 137, 7-11 | already in bib; DOI also in P07's XML | Crossref `works/10.1016/j.ultramic.2013.11.002` (SHA-256 `dfc6ccd6...5f5d`): title, six authors, volume, pages match | METADATA_VERIFIED (upgrade) |
| P02 Osakabe et al. 1989, PRL 62, 2969 | already in bib | Crossref `works/10.1103/PhysRevLett.62.2969` (SHA-256 `ba44b7e0...75f1`): title, five authors, 62(25), 2969-2972 match | METADATA_VERIFIED (upgrade) |
| Post-1993 patents citing PAT01 with reflection-related titles: US 10,424,458 B2 "Electron reflectometer and process for performing shape metrology" (NIST, priority 2017-08-21); EP 4 411 783 A1 "Leem based holography" (ASML, priority 2023-01-31) | PAT01 "Cited by" list on Google Patents (titles only) | Not read (Google rate-limited) | UNVERIFIED; leads for the "reflection holography since 1993" question in the patent literature, not evidence of experiments |

Full Crossref hashes: P01 `991fae5ee764388e5f76379a0261b54f289d2e6d6d1059b2907a247ad5a720f1`; P02 `ba44b7e02f63341de005451f4ccd3afd1e58ba4b672a5f6117328d49bb692475`; Harada 2005 `217bf3b5cc2118ffd93e6a68be5df656c7e6592e7614730dac8dea318127f7b0`; P47 `1502ce62d30750712bec18b70bfce71177c7d761fc087c1c1c3a0ee4c8c1403e`; P45 `f54115dc060b92f988276959c3000b9374a44e69214eec8fb596546a9e429f01`; P46 `dfc6ccd6d57d50f712ad3d776423215a9ea8dc048d7316f260a4cdf9a8dd5f5d`. No DOI was constructed; every DOI above was either printed in a document read (P07 XML) or already in `docs/references.bib`, and each was resolved through Crossref.

## 7. What remains UNVERIFIED and the uploads it needs

1. **P01 content (all CFG-O parameters):** surface, energy, reflection, glancing angle, reference-wave
   arrangement, biprism position, phase relation and sign, measured values. Neither P07 nor PAT01 supplies
   them; PAT01 supplies only an indirect description (S1, S2). Upload needed: **P01 PDF (JJAP 27, L1772,
   1988)**, first priority.
2. **Whether the P01 interference was a self-reference of one Bragg beam or two different reflected beams**
   (I1): P01, then P08 (Osakabe 1992, doi 10.1002/jemt.1070200415).
3. **"Optik Suppl. 3, 77 (1987) p. 4"**: identity, authors and content unknown. Request from Ali or an
   interlibrary loan; it may be a conference abstract of the German microscopy society issue of Optik.
4. **P07 journal page numbers** for the locators in section 2: need the typeset PDF (open access, blocked
   here only by the PDF challenge pages). Any browser download of `https://pmc.ncbi.nlm.nih.gov/articles/PMC7850541/pdf/dfaa033.pdf`
   uploaded by Ali would settle them; content is already fully read.
5. **PAT01 Eq. (2) intended form** (I3): both printed versions are defective; no further source in the
   family was found. P01 or P08 may give the relation properly.
6. **US 5,192,867 remaining columns** (1-2, 5-6, 8-10) and **US 10,424,458 B2 / EP 4 411 783 A1**: not read
   (time and Google rate limit); the USPTO image route worked for US 5,192,867 and can be used for the others.
7. **Harada et al. 2005 author list** (Crossref shows one author, P07 five): publisher page or PDF.
8. **Statements P07 makes about refs. 64-67** (double biprism, split illumination) remain UNVERIFIED for those
   papers; P47 and P45 are paywalled (AIP), P46 (Elsevier), Harada 2005 (OUP; possibly free as an older
   J. Electron Microsc. article, not checked).
9. **Laboratory optics** (reference path, compensation of 2θ_ext, aperture, Cs, biprism coefficient at
   200 keV): PROJECT_INPUT items 4 and 16; no literature source can supply them.
