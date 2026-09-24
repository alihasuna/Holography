# L9 - The microscope (Hitachi HF-3300, UVic) and the detector (Quantum Detectors, Medipix-based): sourced parameters

Prepared: 2026-09-24 by agent L9 (literature). Status: COMPLETE (written incrementally, sections 0-8).
Branch `claude/electron-holography-orchestration-nakd7r`. No repository file other than this report and
`docs/agent_reports/L9_new_refs.bib` is edited; nothing is committed or pushed. Raw downloads are kept outside
the repository in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/l9/` (called `l9/` below).

Task input (PROJECT_INPUT, Ali, 2026-09-24): the microscope is the Hitachi HF-3300 at the University of Victoria
(UVic), operated at 200 keV for this work (300 keV is never used). The detector is a Medipix-based hybrid-pixel
detector from Quantum Detectors (Ali wrote "midi pixel by quantum detectors"; the exact model, e.g. MerlinEM, is NOT
confirmed). Experiment: reflection-mode dark-field electron holography of ion-milled, oxide-covered Si(001),
specular (0,0,8) at about 16 mrad glancing incidence, with an electron biprism.

Read before starting: `docs/06_project_inputs_required.md` items 1-6 and 15-18; `docs/05_final_repository_specification.md`
section 5 (items 1-8: dark-field selection, image formation, reference models, partial coherence, instrument
artefacts, detector, reconstruction, quantification); `docs/model_assumptions.md` B5 (reference-wave idealisations
R1/R2/R3), B10 (convergence is PROJECT_INPUT), B28 (demo R1 reference), B29 (demo processing), and the demo detector
stand-ins B23 (pitch 15 um, M = 3.0e5, 0.05 nm image pixel) and B24 (gain 1, 500 e/px, Poisson only, no MTF);
`reflection_holo/optics/detector.py` (pixel mapping pitch/M with a consistency check, band-limited DFT resampling
at pixel centres, Poisson counting times a gain; MTF "none" only; pixel integration, readout noise and drift NOT
IMPLEMENTED).

Labels (instruction file section 1.4, as recorded in `README.md` and `.claude/agents/`): METADATA_VERIFIED,
SECTION_READ (only with a locator), REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED. Sub-labels
as in L5-L8: `+ABSTRACT(publisher)` = the abstract read on the publisher's own page; `+ABSTRACT(PubMed)` = read
in Europe PMC/PubMed; `+ABSTRACT(index)` = only a search-engine or index summary seen (NOT evidence).
Manufacturer and facility web pages are SECTION_READ with the URL and the retrieval date (2026-09-24 unless
stated). No personal contact details of staff are recorded in this report (names of authors of publications are
bibliographic data and are kept).

## 0. Log of hosts and access

| Time (UTC) | Host / service | Result |
|---|---|---|
| 04:35 | general web search (WebSearch tool) | used only to find URLs; its summaries are not evidence and are not used as such |
| 04:36 | www.uvic.ca (AMF and CAMTEC pages, AMF PDFs under `/research/advancedmicroscopy/assets/docs/STEHM/`) | HTTP 200 for every page and PDF fetched (curl through the agent proxy); files in `l9/html/`, `l9/pdf/` |
| 04:36 | onlineacademiccommunity.uvic.ca (UVic Electron Microscopy Research Group site) | HTTP 200 |
| 04:39 | www.hitachihyoron.com (Hitachi Review PDF) | HTTP 200 (PDF read; AES-encrypted but text-extractable) |
| 04:39 | www.hitachi-hightech.com (HF-3300 "Unique Functions" brochure PDF; Hitachi Canada HF-3300 datasheet page) | HTTP 403 "Access Denied" from the host's Akamai edge (server-side, not the agent proxy; the proxy status shows no relay failure); WebFetch also 403. NOT READ |
| 04:41 | milexia.com (distributor page) | HTTP 200; the HF-3300 brochure download requires a personal-data form (name, e-mail): NOT submitted, brochure NOT READ |
| 04:41 | qd-europe.com, armgate.lv (distributor pages) | HTTP 404 |
| 04:42 | api.crossref.org (`/works/<doi>` and `/works?query.bibliographic=`; no mailto; User-Agent "L9-literature-check/1.0") | works; JSON cached in `l9/crossref/` |
| 04:42 | api.openalex.org (single-record lookups; OA status only) | works |
| 04:43 | Europe PMC REST (search, core abstracts, fullTextXML) | works; files `l9/epmc_*` |
| 04:44 | academic.oup.com (Microscopy; Microscopy and Microanalysis, which now hosts the pre-2023 M&M abstracts: the Cambridge Core PDF URLs return 404 and doi.org redirects to OUP) | HTTP 403 Cloudflare "Just a moment..." (not bypassed); WebFetch reached only the metadata page ("This content is only available as a PDF"). NOT READ |
| 04:45 | archive.org (Wayback availability API) | HTTP 429 Too Many Requests; not retried |
| 04:46 | api.archives-ouvertes.fr (HAL) | works; hal-01404505 is a notice without a file (external ISTEX link needs institutional login) |
| 04:45 | quantumdetectors.com (MerlinEM, MerlinEM RDP, MerlinEELS pages; Merlin4X application-note PDF) | HTTP 200. The MerlinEM datasheet and application notes are behind a personal-data form (first/last name, company, e-mail): NOT submitted, datasheet NOT READ |
| 04:47 | api.elsevier.com, www.sciencedirect.com | 400 (API) / 403 (site); Elsevier CC-BY papers read from institutional repositories instead |
| 04:47 | eprints.gla.ac.uk (University of Glasgow repository) | HTTP 200; serves the publisher versions (CC BY) of Mir et al. 2017 and Paton et al. 2021 |
| 04:48 | arxiv.org (abs pages and PDFs); export.arxiv.org API | arxiv.org HTTP 200; the export API returned an empty body (not used) |
| 04:48 | iopscience.iop.org (JINST PDFs) | HTTP 200 (CC BY 3.0 papers) |
| 04:52 | www.mmc-series.org.uk (mmc2023 abstract database) | HTTP 200 |
| 04:53 | academic.oup.com via WebFetch (M&M 2024 abstract) | the tool returned only a model-written summary, twice (the second time asked for verbatim text); no verbatim text seen: content UNVERIFIED |


## 1. The UVic instrument: what the facility's own pages and documents state (task 1)

### 1.1 Identification (fact, SECTION_READ)

The instrument at UVic is not a stock HF-3300: the Advanced Microscopy Facility (AMF) calls it the **Hitachi
HF-3300V STEHM** (scanning transmission electron holography microscope), "Based on the Hitachi HF-3300 TEM" (U1).
Every facility statement below refers to that modified instrument. Where this report cites HF-3300 literature
that is not about the UVic HF-3300V, the transfer to the UVic instrument is an inference and is labelled so.

### 1.2 Sources read (all retrieved 2026-09-24; SHA-256 of the saved file in `l9/`)

| # | Document, URL actually read | Locator | Label |
|---|---|---|---|
| U1 | AMF page "Hitachi HF-3300V STEHM", `https://www.uvic.ca/research/advancedmicroscopy/about/microscopes/stehm/index.php` (sha256 a9a8881e...cc1e97) | whole page; section "Instrument specifications" | SECTION_READ |
| U2 | AMF PDF "HF-3300V STEHM - Instrument summary", `https://www.uvic.ca/research/advancedmicroscopy/assets/docs/STEHM/HF-3300V%20STEHM%20-%20Instrument%20summary.pdf` (1 page; PDF creation date 2013-07-15; sha256 f9a06591...acdc5ba) | p. 1 | SECTION_READ |
| U3 | AMF PDF "STEHM highlights", `.../assets/docs/STEHM/STEHM%20highlights.pdf` (3 pages; PDF creation date 2015-10-13; sha256 36f8b359...16b559) | pp. 1-3 | SECTION_READ |
| U4 | AMF PDF, R. Herring, "The Scanning Transmission Electron Holography Microscope (STEHM)", slides of a talk at MSC/SMC, Halifax, June 5-8, 2012 (title slide), file `STEHM_Special_Features_CAMTEC_2013.pdf` (28 slides; sha256 d8a8e591...a043) | slides 1-28 (text layer; slides 5, 6, 16 also rendered and viewed) | SECTION_READ |
| U5 | AMF PDF, R. Herring, "Recent STEHM High-Resolution Performance and Future Applications", CAMTEC Workshop, July 5, 2013 (title slide), file `STEHM_Presentation_CAMTEC_July_2013.pdf` (55 slides; sha256 694bcaf1...0114) | slides 1-55 (text layer; slides 4, 5, 6, 10 rendered and viewed) | SECTION_READ |
| U6 | AMF page "Microscopes", `https://www.uvic.ca/research/advancedmicroscopy/about/microscopes/index.php` | whole page | SECTION_READ |
| U7 | AMF page "The Advanced Microscopy Facility", `https://www.uvic.ca/research/advancedmicroscopy/about/index.php` | whole page | SECTION_READ |
| U8 | AMF page "History", `https://www.uvic.ca/research/advancedmicroscopy/about/history/index.php` | whole page | SECTION_READ |
| U9 | CAMTEC "User facilities", `https://www.uvic.ca/research/centres/camtec/facilities/index.php`, and "Tool list", `https://www.uvic.ca/research/centres/camtec/facilities/tool/index.php` | AMF paragraph; tool list line for the STEHM | SECTION_READ |
| U10 | UVic Electron Microscopy Research Group, "Facilities", `https://onlineacademiccommunity.uvic.ca/emicro/facilities/` (page footer "(c) 2017 University of Victoria"; the page carries no date of last change) | whole page (one paragraph on the HF3300V) | SECTION_READ |

None of these pages states a date for its technical content except U4 (June 2012) and U5 (July 2013); U1 and U6
describe the instrument in the present tense but are not dated. **The facility pages may be out of date** (for
example U3 still speaks of "A large CCD detector", while U10 names a Medipix3 detector); every value below is
"as stated by the page", not "as installed today".

### 1.3 What the pages state (facts, each SECTION_READ with the locator given)

Quotations are copied from the text layer and checked against the rendered slide where a slide is cited.

**Electron source.**
* U1, "Instrument specifications", first bullet: "High brightness (measured as 6x10e13 A/m2 sr), high stability
  and high coherence cold-field-emmision electron source." (spelling as on the page). The page gives no
  accelerating voltage, emission current, extraction voltage or measurement method for this brightness, and the
  notation "6x10e13" is ambiguous (6 x 10^13 is the likely reading; see inference I1.1).
* U4 slide 5 ("The Electron Source"): "New Cold-FEG Electron Gun Assembly"; "Electron emitter - tungsten (W)
  single crystal (~10 nm dia)"; "Improved vacuum to 10-13 torr (10-11 Pa)"; "Now 30x brighter than standard
  Schottky FEG".
* U4 slide 6: "Improved electron energy spread"; "~ 0.3 eV"; "Can be reduced by reducing electron extraction
  voltage"; "Ultimate performance not yet measured (EELS)"; "Energy spread decreases (improves) with age of
  emitter".
* U5 slide 6 ("The STEHM's Energy Spread", rendered and viewed): a zero-loss spectrum labelled "FWHM" with the
  text "60 kV - 0.32 eV for 0.1 s" and "- 0.34 eV for 1.0 s", "Beam current - 7 uA" (as printed; plausibly the
  emission current, not stated), "Convergence angle, alpha - ?", "Source brightness - ?", "Performance needs to
  be measured. Will be reported later." The spectrum's own caption reads "60kv 16ev disp 0.32ev rez 0.10 sec".
  **This energy spread is at 60 kV, not at 200 kV**, and is from 2013.
* U3 p. 1: "A cold-field emitting electron source to increase its coherence (like a laser) and to decrease the
  energy spread of the electron beam".
* U5 slide 5 (rendered): "Cold-field Electron Source (10-13 torr)".

**Accelerating voltage.**
* U1: "60 keV, 200 keV, and 300 keV acceleration voltage." U6: "The STEHM is ready in its high-resolution imaging
  and diffraction mode at 300 kV, 200 kV and 60 kV." U4 slide 4: "Can be used at 300 kV, 200 kV and 60 kV" and
  "200 kV for specimens that damage at 300 kV but not at 200 kV, e.g., silicon." U10: "This 60 - 300 kV electron
  microscope". U5 slide 4 (rendered): "HighVoltage Tank (300,000 to 60,000 Volts)".
  Consistent with the project's 200 keV (PROJECT_INPUT item 1).

**Biprisms (holography capability).**
* U1: "Four electron biprisms for many types of electron holography. One above specimen, and three below the
  specimen with magnification between lower biprisms equal to one."
* U7: "Hitachi HF-3300V STEHM equipped with 4 holographic biprisms, EELS (Gatan) and EDX (Bruker)."
* U10: "an illumination side bi-prism and 3 image side bi-prisms".
* U4 slide 8 ("Probe Forming Lenses (Condenser Lenses)"): "Electron Biprism"; "One electron biprism above
  specimen"; "Forms two beams"; "For STEM holography and Confocal Electron Holography". Same slide: "Dislocated
  hologram aperture" (condenser aperture for vortex beams).
* U4 slide 16 ("The Intermediate Lenses"): "One extra projection lens - higher magnification"; "Accommodate 3
  electron biprisms below specimen"; "Magnification between biprisms made equal to one"; "Can split electron wave
  into four pieces by also using condenser electron biprism above specimen".
* U4 slide 17: "Hologram carrier fringes down to ~4 pm" (no voltage, biprism setting or specimen-plane reference
  stated).
* U3 p. 2: "The use of three biprisms placed below the specimen permits flexible control of all of the
  interference parameters, ie., the interference region, fringe spacing and fringe angle, involved in electron
  holography [2]", with [2] = K. Harada, T. Matsuda, A. Tonomura, T. Akashi, Y. Togawa, "Triple Biprism Electron
  Interferometry", J. Appl. Phys. 99, 113502 (2006) (reference list of U3 p. 3; verified in section 2).
  "Scanning-beam electron holography is made possible by placing an additional biprism above the specimen."
* U5 slide 5 (rendered photograph with labels): "1 electron biprism + dislocated hologram aperture" (upper
  column), "3 electron biprisms + extra lenses" (below the TEM corrector).
* None of U1-U10 gives biprism filament diameters, the exact conjugate planes of the biprisms, the voltage ranges,
  or which biprism is used for a given holography mode. (Fact: not stated.)

**Aberration correctors and lenses.**
* U1: "First Cs and Cc corrected STEM with ExB Wien filter." "First aplanic TEM with Cs and coma correction."
  "Sub angstrom resolution at 60 kV TEM."
* U5 slide 5 (rendered): "STEM Cs + Cc aberration corrector (ExB Wien filter) (CEOS SC-COR)"; "Aplanatic TEM
  Cs + Coma aberration corrector (CEOS B-COR)".
* U4 slide 14 ("Object lens pole piece"): "same as NRC NINT's HF3300"; "+15o rotation using standard holder";
  "tomography holder available with 360o rotation"; "Ultra-clean vacuum using ZoneTEM"; "Cs - who cares?".
  No Cs or Cc value of the objective lens is given anywhere in U1-U10.
* U4 slide 15: "First Cs and coma corrected TEM"; "Cc partially corrected"; "Coma correction increases high
  resolution field-of-view imaging area by 10x"; "Better than 50 pm measured".
* U5 slide 17: "Tilt tableau with an outer tilt angle of 60mrad" (corrector tuning of the aplanatic TEM).
* U4 slide 18: "Necessary for high column (~4.5 m) of STEHM".

**Lorentz mode.** Not mentioned on any of U1-U10 (fact: not stated). Whether the HF-3300V has a Lorentz (field-free)
mode or a Lorentz lens is UNVERIFIED.

**Energy filter and spectrometer.**
* U1, "Detectors": "Electron energy loss spectrometer." and "Imaging energy filter (Gatan Quantum)."
* U6: "the Gatan electron energy loss spectrometer (EELS) and Gatan Imaging Filter (GIF) is available."
* U4 slide 21: "Imaging energy filter (GIF - Gatan Imaging Filter) for energy-filtered imaging and higher
  magnification imaging (20x)". U3 p. 2 proposes "Energy-filtered electron holography, which combines electron
  holography with the imaging energy filter (GIF)".
* **Consequence for PROJECT_INPUT item 21 (inference, DERIVED_HERE):** the facility states that an imaging energy
  filter exists on the instrument, so the requested energy-filtered measurement of the specular beam (docs/06
  item 21) is instrumentally possible in principle; whether the filter can be combined with the reflection
  geometry and the Merlin detector position is not stated.

**Cameras and detectors.**
* U1, "Detectors": "Secondary electron detector in STEM mode.", "X-ray energy dispersive spectrometer (Bruker).",
  "High angle annular dark field for STEM imaging.", "High angle annular bright field detector for STEM
  imaging.", "Electron energy loss spectrometer.", "Imaging energy filter (Gatan Quantum)." **No camera and no
  Quantum Detectors product is listed on U1.**
* U5 slide 10 (rendered): a 120 s TEM exposure "using the Gatan USC 1004 2k x 2k camera" ("the maximum recording
  time available") (2013).
* U3 p. 1: "A large CCD detector to better measure the gray scale of fringes produced in holograms".
* **U10 (the only facility-side statement of the Quantum Detectors detector):** the HF3300V "is fitted with a
  Merlin (Medipix3) high speed pixelated direct-electron detector." The page does not say "MerlinEM", the number of
  chips (single 256 x 256 or quad), the sensor material or thickness, the mounting position (on-axis retractable,
  below the viewing screen, or after the GIF), or the date of installation.
* Inference I1.2 (not evidence of what Ali used): Ali's "midi pixel by quantum detectors" is consistent with
  U10's "Merlin (Medipix3)"; the model name, chip count, sensor and mounting still need Ali's confirmation
  (section 6). The UVic HF-3300V may carry other cameras (the 2013 Gatan UltraScan named in U5) that are not the
  one used for the holograms.

**Specimen holders.** U1: "High stability single tilt holder (Hitachi).", "High stability double tilt holder
(Hitachi).", "Low-background analytical holder (Gatan).", "360 degree tomography holder (Hitachi Pillar).",
"High temperature (1500 C) holder (Hitachi).", "LN2 CryoEM holder (Gatan).", "Farraday cage holder (Gatan)." U4
slide 22 gives a similar list. No reflection (REM) holder or a holder for mounting a bulk wafer piece edge-on is
listed (fact: not stated); how Ali mounts the Si(001) piece for 16 mrad glancing incidence is PROJECT_INPUT.

**Vacuum.** U4 slide 5 and U5 slide 5: gun vacuum "10-13 torr (10-11 Pa)". U4 slide 14: "Ultra-clean vacuum
using ZoneTEM". No specimen-chamber pressure is stated (relevant to docs/06 item 12(c): still PROJECT_INPUT).

**Environment and stability (U1, U4 slide 19, U7).** U1: "Thermal insulation maintaining temperature to +/- 0.025 C
over 1 hour."; "The room is mounted on bedrock, mechanically insulated from the building."; "Stray
electromagnetic field reduction using aluminum shielding."; "Magnetic field reduction using permalloy shielding."
U4 slide 19 gives "+ 0.1 oC per hour" (2012) for the same room (the two values differ; U1 is the later, undated
statement). U7: "STEHM users have the option to control the STEHM remotely from an adjacent room."

**Sample preparation tools at the AMF (relevant to docs/06 item 12; not evidence of what Ali used).** U4 slide 2 and
U9: ion mill "Fischione 1010" and plasma cleaner "Fischione 1020" (U9: "plasma cleaner (Fischione 1020), ion mill
(Fischione 1010)"); FIB "Hitachi FB-2100" (U8, U9; U4 slide 2 prints "HB-2100"). Inference I1.3: if Ali's
"ion-milled" surface and "oxygen-argon plasma clean" were done at the AMF, these would be the instruments; Ali must
confirm (the item-12 checklist in docs/06 already asks for tool, ion, energy and angle).

### 1.4 Inferences from section 1 (labelled; not facts)

* I1.1 (DERIVED_HERE, conditional): if U1's "6x10e13 A/m2 sr" means 6 x 10^13 A m^-2 sr^-1, it is a reduced or
  non-reduced brightness at an unstated voltage; the page does not say which, so it cannot be converted to a
  source size or a spatial-coherence width without an assumption. It is recorded as stated and NOT used as a
  model parameter.
* I1.2: see "Cameras and detectors" above.
* I1.3: see "Sample preparation tools" above.
* I1.4 (DERIVED_HERE): the facility's biprism layout (one condenser-side, three image-side) is the layout needed
  for both reference arrangements the repository models: a condenser-side biprism can pre-tilt or split the
  illumination (R1 with pre-tilt, B28; cf. split illumination P45/P46), and image-side biprisms overlap two image
  regions (R2). The layout does NOT tell which arrangement Ali used (docs/06 items 15-18 remain open), and the
  instruction-file prohibition on inferring the reference trajectory from the biprism's intended function stands.
* I1.5: the only published energy spread for this instrument found so far is 0.32-0.34 eV FWHM at 60 kV (2013).
  The FWHM at 200 kV is not stated on any facility page. For the step phase this is a minor term (docs/06 item 2:
  below 0.004 rad for a 10 nm step at 0.7 eV), so a value of order 0.3-0.5 eV is adequate for the chromatic
  envelope only as an ASSUMPTION until Ali supplies a measured zero-loss FWHM at 200 kV.

## 2. The Hitachi HF-3300 family: manufacturer and peer-reviewed descriptions (task 2)

### 2.1 Sources

| # | Source, URL actually read | Locator | Label |
|---|---|---|---|
| H1 | T. Sato, H. Matsumoto, M. Konno, Y. Taniguchi, S. Mamishin, "Hitachi's High-end Analytical Electron Microscope: HF-3300", Hitachi Review 57(3), 132-135 (June 2008) (volume, issue, date from the PDF metadata and the running heads). `https://www.hitachihyoron.com/rev/pdf/2008/r2008_03_104.pdf` (4 pages; sha256 f170b885...be9c). No DOI found (Hitachi Review is not in Crossref for 2008; none printed on the article) | Overview; "Characteristics of cold FE electron source" and Table 1 (p. 132, Table 1 rendered at 200 dpi and read as an image: `l9/render/hr2008_table1.png`); "Electron holography", Fig. 1 and Fig. 2 (p. 133); "Spatially resolved EELS" (p. 134) | SECTION_READ (whole article) |
| H2 | Milexia (distributor), "Hitachi Field Emission HF-3300 TEM", `https://milexia.com/products/product/h-3300-high-voltage-tem` (sha256 818784ff...b023c) | "Features & Variations" | SECTION_READ (distributor page, not a Hitachi document) |
| H3 | Hitachi High-Tech America, "HF-3300 300 kV Cold-Field Emission Gun TEM/STEM - Unique Functions" (brochure PDF) and Hitachi High-Tech Canada "Datasheet HF-3300 In-Situ FE-TEM System Overview" | host 403 (section 0) | UNVERIFIED (not read; a search-engine summary of H3 exists and is NOT used) |
| H4 | R. Puttock, I. M. Andersen, C. Gatel, et al., "Defect-induced monopole injection and manipulation in artificial spin ice", Nat. Commun. 13, 3641 (2022), DOI 10.1038/s41467-022-31309-0 (Europe PMC full text PMC9233697, `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9233697/fullTextXML`) | Methods, "Lorentz transmission electron microscopy" and "Electron holography" paragraphs | SECTION_READ (Methods) + METADATA_VERIFIED (Crossref: vol. 13, article number 3641, 2022, seven authors) |
| H5 | K. Reidy, G. Varnavides, J. D. Thomsen, et al. (incl. A. M. Blackburn, UVic), "Direct imaging and electronic structure modulation of moire superlattices at the 2D/3D interface", Nat. Commun. 12, 1290 (2021), DOI 10.1038/s41467-021-21363-5 (PMC7910301 full-text XML) | Methods, HRTEM paragraph | SECTION_READ (Methods paragraph) + METADATA_VERIFIED (Crossref: vol. 12, article number 1290, 2021, ten authors) |
| H6 | F. Roder, F. Houdellier, T. Denneulin, E. Snoeck, M. Hytch, "Realization of a tilted reference wave for electron holography by means of a condenser biprism", Ultramicroscopy 161, 23-40 (2016), DOI 10.1016/j.ultramic.2015.11.004 | abstract (Europe PMC, PMID 26624513) | METADATA_VERIFIED (Crossref) +ABSTRACT(PubMed); body CLOSED (OpenAlex closed; HAL notice only) |
| H7 | R. A. Herring, D. Hoyle, Y. Taniguchi, M. Haider, "The Ultra-stable Scanning Transmission Electron Holography Microscope", Microsc. Microanal. 19(S2), 320-321 (2013), DOI 10.1017/s1431927613003590 | not read (OUP Cloudflare; Cambridge PDF 404) | METADATA_VERIFIED (Crossref); content UNVERIFIED |
| H8 | R. A. Herring, D. Hoyle, "The Ultra-stable Scanning Transmission Electron Holography Microscope (STEHM)", Microsc. Microanal. 21(S3), 347-348 (2015), DOI 10.1017/s1431927615002536 | not read (as H7) | METADATA_VERIFIED (Crossref); content UNVERIFIED |
| H9 | E. Snoeck, F. Houdellier, Y. Taniguchi (Crossref spells "Taniguch"), A. Masseboeuf, C. Gatel, J. Nicolai, M. Hytch, "Off-Axial Aberration Correction using a B-COR for Lorentz and HREM Modes", Microsc. Microanal. 20(S3), 932-933 (2014), DOI 10.1017/s1431927614006382 | not read (as H7) | METADATA_VERIFIED (Crossref); content UNVERIFIED |
| H10 | K. Harada, T. Matsuda, A. Tonomura, T. Akashi, Y. Togawa, "Triple-biprism electron interferometry", J. Appl. Phys. 99, 113502 (2006), DOI 10.1063/1.2198987 (cited by U3 as ref. [2] for the three image-side biprisms) | not read (pubs.aip.org blocked for L8 the same day) | METADATA_VERIFIED (Crossref: volume 99, issue 11, article number 113502, 2006-06-01, five authors as listed) |
| H11 | A. M. Blackburn, R. A. McLeod, "Practical implementation of high-resolution electron ptychography and comparison with off-axis electron holography", Microscopy 70(1), 131-147 (2021), DOI 10.1093/jmicro/dfaa055 (already [P42] in references.bib) | abstract (Europe PMC, PMID 32986121); affiliations there: Blackburn, Department of Physics and Astronomy, University of Victoria; McLeod, Hitachi High Technologies Canada | METADATA_VERIFIED (Crossref) +ABSTRACT(PubMed); body CLOSED (OUP 403; OpenAlex closed). The abstract names neither the microscope nor the detector |
| H12 | R. A. Herring, Microscopy 70(3), 297-301 (2021), DOI 10.1093/jmicro/dfaa066 ([P44]); Micron 160, 103317 (2022), DOI 10.1016/j.micron.2022.103317 ([P43]); and "Phase imaging and analysis of the annihilation of a dislocation at a crystal surface", Micron 201, 103945 (2026), DOI 10.1016/j.micron.2025.103945 (new) | abstracts (Europe PMC, PMIDs 33269799, 35753170, 41202789) | +ABSTRACT(PubMed) + METADATA_VERIFIED (Crossref). None of the three abstracts names the microscope or the voltage (a search-engine summary claiming "HF-3300v ... 300 kV" for the 2021 paper is NOT evidence) |

### 2.2 Facts (SECTION_READ with locator)

**Cold-FE source (H1).**
* H1 p. 132, Overview: "A 300-kV cold FE-TEM, the HF-3300, has been developed by Hitachi High-Technologies
  Corporation." Introduction: developed "equipped with spatially resolved EELS (electron energy loss spectroscopy)
  technology and a special electron biprism system for electron holography, as shown in Fig. 1."
* H1 pp. 132-133: "The size of the emitting area of the electron source is in the order of a few nm and, as a
  result, the brightness is high." "The brightness (beta) of the cold FE electron gun is about three times that of
  SE electron gun, and the energy spread (Delta E) of the cold FE electron gun is less than half that of the SE
  electron gun, as shown in Table 1."
* H1 Table 1 ("Performance Comparison of Cold FE Gun with SE Gun"; read on the rendered page), cold FE emitter
  "FE W(310)", work function 4.5 eV, temperature 300 K:

  | Total emission current Ie (uA) | 10 | 30 | 100 |
  |---|---|---|---|
  | Brightness beta (A/cm^2 sr) | 2.9 x 10^8 | 8.7 x 10^8 | 2.9 x 10^9 |
  | Energy spread Delta E (eV) | 0.45 | 0.55 | 0.7 |

  and for the Schottky "SE Zr/O/W(100)" (2.8 eV, 1700 K) at 30/100/300 uA: 8.8 x 10^7 / 2.9 x 10^8 / 8.8 x 10^8
  A/cm^2 sr and 1.0 / 1.3 / 1.8 eV. The caption says "General operating conditions are shown in gray region";
  in the PDF as rendered every data cell is grey, so the "general operating condition" column cannot be
  identified from the file (fact about the file). **The table states neither the accelerating voltage nor whether
  the brightness is reduced**; the article is about the 300 kV instrument, so 300 kV is the likely condition
  (inference, not stated).
* H1 Fig. 1 caption: "HF-3300 is equipped with electron energy filter [GIF (Gatan Imaging Filter)] and the biprism
  system." Fig. 2 (holography scheme) shows one biprism ("Wire", "Electrode") between the objective lens and the
  magnifying lens. H1 p. 134 names the energy filter of that instrument "GIF 863 Tridiem".

**Performance figures on a distributor page (H2)**, voltage not stated: "Crystal lattice TEM resolution: 0.10 nm
(STEM option: 0.20 nm)", "TEM point-to-point image resolution: 0.19 nm", "TEM information limit resolution: 0.13
nm", "TEM magnification: x200 ~ x1.5M (STEM option: x300 ~ x 10M)"; "this new generation source operates from 300
to 100kV". These describe the stock (uncorrected) HF-3300; they are NOT the UVic HF-3300V values (the UVic
instrument has an image corrector, U1/U5) and are recorded only as the manufacturer-family context.

**HF-3300-based holography practice (H4, I2TEM at CEMES Toulouse; not UVic).** H4 Methods: LTEM "in a Hitachi
HF-3300 (I2TEM) microscope operated at 300 kV and fitted with a cold field-emission gun and image corrector
(B-Corr)"; "EH was performed using the dedicated Hitachi HF-3300 (I2TEM) microscope operated at 300 kV, using a
double biprism setup", "exposure time of 60 s per hologram and an inter-fringe distance of 1.4 nm", "resolution of
the treated magnetic phase images ... 3.7 nm", with "homemade corrective software to correct for both a drift in
interference fringes and of the sample".

**The UVic HF-3300V in a peer-reviewed methods section (H5).** H5 Methods: "HRTEM imaging was performed with a
Hitachi HF-3300V with CEOS BCOR imaging aberration corrector, operated at 60 kV", 25 images of 8 s, "The electron
flux was 500 e-/A^2/sec", "average drift of < 7 pm/sec". (The paragraph does not name the camera. The HF-3300V is
the UVic instrument per U1; H5's co-author list includes a UVic affiliation. This is the only peer-reviewed
methods text read here that names the UVic instrument; it confirms the B-COR image corrector, U5 slide 5.)

**Condenser-biprism tilted reference for dark-field holography (H6, abstract only).** "we first realize a tilted
reference wave by employing a biprism placed in the condenser system above three condenser lenses producing a
relative tilt magnitude up to 20/nm at the object plane (300kV)"; "only one half of the round illumination disc
is tilted relative to the optical axis without displacement"; "Holographic measurements ... return the interference
fringe contrast as a function of the relative tilt between both parts of the illumination"; "A first dark-field
hologram with a tilted - object-free - reference wave was acquired and reconstructed." The abstract does not name
the microscope. This is the closest published analogue of the repository's R1 reference with a condenser-biprism
pre-tilt (B28, B5) and of the UVic illumination-side biprism (U1, U10); what is transferable is the principle and
the existence of a fringe-contrast-versus-tilt dependence, not any number (inference).

### 2.3 What was looked for and NOT found in anything read (fact: not stated in the sources read)

* Energy spread of the UVic HF-3300V at 200 kV (only 60 kV, U5 slide 6).
* Source size or a measured spatial-coherence width at the specimen for any HF-3300 (H1 states only "a few nm" for
  the emitting area; U1's brightness has no stated voltage).
* Illumination convergence ranges for holography (U5 slide 6 prints "Convergence angle, alpha - ?").
* Objective-lens Cs and Cc of the HF-3300 or HF-3300V (U4 slide 14: pole piece "same as NRC NINT's HF3300", "Cs -
  who cares?"; with the B-COR corrector the residual Cs is an operator setting; U4 slide 15: "Cc partially
  corrected"). No value at 200 kV was found.
* Lorentz mode of the UVic instrument (the I2TEM's field-free operation is described in H4 via "the normal sample
  stage of the I2TEM with the objective lens switched off"; nothing comparable is stated for UVic).
* Biprism filament diameters, conjugate planes, voltage ranges and fringe-spacing ranges of the UVic biprisms
  (U4 slide 17 only: "Hologram carrier fringes down to ~4 pm").
* Any publication of reflection-mode (REM, RHEED-geometry) work on the UVic HF-3300V: none found in Europe PMC
  full-text searches (`"STEHM" AND Victoria`, `("HF-3300" OR "HF3300" OR "HF-3300V") AND "Victoria"`,
  `"HF-3300" AND (biprism OR holography)`; 04:43 UTC) or in the Crossref bibliographic searches of section 0. This is
  a search result, not evidence of absence.

### 2.4 Inferences (labelled)

* I2.1 (DERIVED_HERE from H1 Table 1, conditional on the table being at 300 kV): the cold-FE energy spread grows
  with emission current from 0.45 eV (10 uA) to 0.7 eV (100 uA); U5 reports 0.32-0.34 eV FWHM at 60 kV and "7 uA".
  The zero-loss FWHM of the UVic source at 200 kV is therefore expected in the range 0.3-0.7 eV depending on the
  emission current and tip age (U4 slide 6: "Energy spread decreases (improves) with age of emitter"). This bracket
  is an ASSUMPTION for the chromatic envelope, not a measurement; per docs/06 item 2 the step phase is insensitive
  to it (< 0.004 rad at 0.7 eV for a 10 nm step), so the upper end 0.7 eV is a safe bracket for the simulation.
* I2.2: brightness figures (H1: 2.9e8-2.9e9 A cm^-2 sr^-1 = 2.9e12-2.9e13 A m^-2 sr^-1; U1: "6x10e13 A/m2 sr")
  cannot be turned into a source size or a transverse coherence length without the probe current and the
  convergence, which are PROJECT_INPUT items 2-3. The repository must keep the convergence semi-angle and the
  source-size ensemble as PROJECT_INPUT/ASSUMPTION (B10 unchanged).

## 3. The detector: Quantum Detectors Merlin / MerlinEM (Medipix3) (task 3)

### 3.1 Sources

| # | Source, URL actually read (retrieved 2026-09-24) | Locator | Label |
|---|---|---|---|
| D1 | Quantum Detectors, "MerlinEM - Direct Electron Detector Optimised for 4D-STEM & Dynamic TEM", `https://quantumdetectors.com/products/merlinem/` (sha256 ffae5ceb...5d2d) | "Overview", "Specifications", "Features" | SECTION_READ (manufacturer page) |
| D2 | Quantum Detectors, "MerlinEM RDP", `https://quantumdetectors.com/products/merlinem-rdp/` (sha256 9fe847ed...cc0) | "Specifications", "Features" | SECTION_READ (manufacturer page) |
| D3 | Quantum Detectors, "Merlin4X Application Notes" (X-ray product, PDF created 2019-02-13), `https://quantumdetectors.com/wp-content/uploads/2022/01/2129-Application-Notes-Merlin4X-R1.pdf` (sha256 a7efd233...c5d6) | p. 1 "Introduction", "Experimental Overview" | SECTION_READ (manufacturer document; X-ray version, context only) |
| D4 | MerlinEM datasheet and "MerlinEM - All Applications" notes | behind a personal-data form | UNVERIFIED (not read) |
| D5 | J. A. Mir, R. Clough, R. MacInnes, C. Gough, R. Plackett, I. Shipsey, H. Sawada, I. MacLaren, R. Ballabriga, D. Maneuski, V. O'Shea, D. McGrouther, A. I. Kirkland, "Characterisation of the Medipix3 detector for 60 and 80 keV electrons", Ultramicroscopy 182, 44-53 (2017), DOI 10.1016/j.ultramic.2017.06.010. Publisher version (CC BY) at `https://eprints.gla.ac.uk/143680/1/143680.pdf` (10 pages; sha256 ed8b56ba...cb18e) | whole paper: abstract; secs. 1-7; Figs. 1-16 captions; pp. 44-53 | SECTION_READ (full text) + METADATA_VERIFIED (Crossref) |
| D6 | K. A. Paton, M. C. Veale, X. Mu, C. S. Allen, D. Maneuski, C. Kubel, V. O'Shea, A. I. Kirkland, D. McGrouther, "Quantifying the performance of a hybrid pixel detector with GaAs:Cr sensor for transmission electron microscopy", Ultramicroscopy 227, 113298 (2021), DOI 10.1016/j.ultramic.2021.113298. Publisher version (CC BY; PDF metadata subject "Ultramicroscopy, 227 (2021) 113298") at `https://eprints.gla.ac.uk/240505/1/240505.pdf` (13 pages; sha256 555e925c...0e5); arXiv:2009.14565 also downloaded, not compared | whole paper: abstract; secs. 1-6; Table 1 (p. 5, rendered and read as an image); Fig. 8 (p. 7, rendered, and digitised, section 3.3) | SECTION_READ (full text) + METADATA_VERIFIED (Crossref) |
| D7 | M. Nord, R. W. H. Webster, K. A. Paton, S. McVitie, D. McGrouther, I. MacLaren, G. W. Paterson, "Fast Pixelated Detectors in Scanning Transmission Electron Microscopy. Part I: Data Acquisition, Live Processing, and Storage", Microsc. Microanal. 26(4), 653-666 (2020), DOI 10.1017/S1431927620001713; read as arXiv:1911.11560v2 (`https://arxiv.org/pdf/1911.11560`, sha256 ba8b32ea...94c76) | sec. II "Medipix3 detector" (arXiv pp. 2-5) | SECTION_READ (arXiv v2, section II only; the published version, CC BY on Cambridge/OUP, was not compared) + METADATA_VERIFIED (Crossref) |
| D8 | R. Ballabriga, J. Alozy, G. Blaj, M. Campbell, M. Fiederle, E. Frojdh, E. H. M. Heijne, X. Llopart, M. Pichotka, S. Procz, L. Tlustos, W. Wong, "The Medipix3RX: a high resolution, zero dead-time pixel detector readout chip allowing spectroscopic imaging", JINST 8, C02016 (2013), DOI 10.1088/1748-0221/8/02/C02016, `https://iopscience.iop.org/article/10.1088/1748-0221/8/02/C02016/pdf` (CC BY 3.0; sha256 b77227c9...c1f) | abstract; secs. 2-3 (chip, pixel architecture, counters, continuous read-write) | SECTION_READ + METADATA_VERIFIED (Crossref) |
| D9 | R. Plackett, I. Horswell, E. N. Gimenez, J. Marchal, D. Omar, N. Tartoni, "Merlin: a fast versatile readout system for Medipix3", JINST 8, C01038 (2013), DOI 10.1088/1748-0221/8/01/C01038, `https://iopscience.iop.org/article/10.1088/1748-0221/8/01/C01038/pdf` (sha256 ac247ce9...b4d3b) | abstract; secs. 2-3 | SECTION_READ + METADATA_VERIFIED (Crossref) |
| D10 | G. McMullan, S. Chen, R. Henderson, A. R. Faruqi, "Detective quantum efficiency of electron area detectors in electron microscopy", Ultramicroscopy 109(9), 1126-1143 (2009), DOI 10.1016/j.ultramic.2009.04.002; Europe PMC full text PMC2864625 (CC BY) | abstract; detector description of the Medipix2; results paragraphs on the Medipix2; Fig. 8 caption | SECTION_READ (those passages) + METADATA_VERIFIED (Crossref) |
| D11 | G. McMullan, D. M. Cattermole, S. Chen, R. Henderson, X. Llopart, C. Summerfield, L. Tlustos, A. R. Faruqi, "Electron imaging with Medipix2 hybrid pixel detector", Ultramicroscopy 107(4-5), 401-413 (2007), DOI 10.1016/j.ultramic.2006.10.005 | not read (OpenAlex closed) | METADATA_VERIFIED (Crossref); content UNVERIFIED |
| D12 | N. Dimova, R. Plackett, D. Weatherill, D. Wood, L. O'Ryan, G. Crevatin, J. S. Barnard, M. Gallagher-Jones, D. Hynds, R. Goldsbrough, I. Shipsey, D. Bortoletto, A. Kirkland, "Measurement of the resolution of the Timepix4 detector for 100 keV and 200 keV electrons for transmission electron microscopy", Nucl. Instrum. Methods Phys. Res. A 1075, 170335 (2025), DOI 10.1016/j.nima.2025.170335; read as arXiv:2411.16258v2 | abstract; sec. 2 (sensor), sec. 3 (setup), sec. 4.1 (comparison with Paton et al.) | SECTION_READ (arXiv v2, those sections) + METADATA_VERIFIED (Crossref) |
| D13 | S. L. Y. Chang, C. Dwyer, J. Barthel, C. B. Boothroyd, R. E. Dunin-Borkowski, "Performance of a direct detection camera for off-axis electron holography", Ultramicroscopy 161, 90-97 (2016), DOI 10.1016/j.ultramic.2015.09.004 | abstract (Europe PMC, PMID 26630072); body CLOSED | +ABSTRACT(PubMed) + METADATA_VERIFIED (Crossref) |

### 3.2 Facts (SECTION_READ with locator)

**What is installed at UVic (U10, section 1):** "a Merlin (Medipix3) high speed pixelated direct-electron detector" on
the HF3300V. Nothing else about it is published on the pages read (chip count, sensor, mount, installation date).

**Chip (Medipix3 / Medipix3RX).**
* D8 sec. 2: "The sensitive area contains a 256x256 matrix of 55 um square pixels. The chip can be tiled on three
  sides." "The Medipix3RX in its usual form measures 15.9 x 14.1 mm". "Region of interest readout is also possible
  by selecting either 32, 64 or 128 column blocks and/or a number of rows to be read out."
* D8 sec. 3: the counters "can be configured as 2 x 1-bit counters, 2 x 6-bit counters, 2 x 12-bit counters or
  1x24-bit counter." "If dead time free operation is desired, the chip can be programmed in "Continuous Read
  Write". In this mode of operation one counter is incremented while the other is being read out."
* D8 abstract: characterisation "with 300 um thick Si sensors"; "~72e- r.m.s. noise and ~40e- r.m.s. of threshold
  dispersion after chip equalization have been measured in Single Pixel Mode of operation."
* D8 sec. 3 (charge summing): "summing circuits physically located at the corners between pixels reconstruct the
  charge in clusters of 2x2 pixels"; the hit goes to the pixel with the largest charge ("single pixel mode
  arbitrated").
* D5 sec. 2 (p. 45): "The sensitive matrix consists of 256 x 256 pixels at 55 um pitch with an overall area of
  15.88 x 14.1 mm2. The readout chip is connected to a 300 um thick silicon layer." "Each pixel contains two
  configurable depth registers (2 x 12-bit) ... the two counters can be linked to provide 24-bit depth counting."
  The Nyquist frequency "corresponds to 9.1 lp/mm". Energy per electron-hole pair in Si "3.6 eV".

**Readout (Merlin) and counting modes.**
* D9 abstract: Merlin "is capable of recording Medipix3 256 by 256 by 12 bit data frames at over 1 kHz in bursts of
  1200 frames and running at over 100 Hz continuously to disk or over a TCP/IP link." (2013 system.)
* D7 sec. II: detector "affixed to a Merlin 1R retractable Medipix3 mount from Quantum Detectors"; "Si sensor layers
  of 500 um are needed for operation at primary electron energies of 300 keV. In our case, a 300 um silicon sensor
  layer was used for all data except that in Fig. 1, where a 500 um layer was used instead."; "The Medipix3
  detector can be operated in 1, 6, 12, and 24 bit depth modes"; "With the 120 MHz clock rate of the Merlin readout
  system ... the readout times are 70.8 us, 412 us, 822 us and 1.64 ms, for 1, 6, 12, and 24 bit modes,
  respectively."; "it would take >4 ms to exceed 12 bits at 1 MHz count rates per pixel"; "12,500 frames per second
  with 1-bit data in continuous read-write mode". The Fig. 1 data of D7 were taken "at 200 kV" on a JEOL ARM 300CF
  with the Medipix3 "in SPM with continuous read-write enabled" (4D-STEM, not imaging).
* D1 "Specifications": "Direct electron detection: Detects electrons directly in silicon"; "Energy range: 30-300
  keV"; "Frame rate: Up to 2000 fps (12-bit mode)"; "Pixel pitch: 55 um"; "Pixel array: 256 x 256: Standard
  configuration ideal for core STEM/TEM workflows. Other array sizes available on request." D1 "Features": "a
  dual-counter pixel architecture that enables continuous, gapless data acquisition"; "ROI Rows feature ...
  predefined vertical segments (e.g., 4, 8, 16, up to 256 rows)"; "virtually zero readout noise"; "MerlinEM's pixel
  architecture can also account for charge-sharing effects between neighbouring pixels". D1 "Overview": "At lower
  accelerating voltages, MerlinEM can deliver excellent Detective Quantum Efficiency (DQE) and Modulation Transfer
  Function (MTF)" (the manufacturer's performance claim is restricted to lower voltages).
* D2 "Specifications": "Hybrid pixel architecture (Medipix3)", "Dual counters per pixel for gapless readout", "Up to
  2000 fps (12-bit mode)", "Pixel pitch: 55 um", "Compact, retractable housing"; "Features": "signal-to-noise ratio
  (SNR) of up to 16.7 million to 1 in a single frame"; ROI bands "4, 8, 16, 32, 64, or 128 rows ... N x 256 pixels".
* D3 p. 1 (X-ray Merlin4X, context only): "rapid readout times of between 14,400 and 600 frames per second depending
  on bit depth"; "The 512 x 512 pixel Merlin4X detector with a 55 micrometer pixel size" (a four-chip version exists
  for X-rays; whether the UVic MerlinEM is 256 x 256 or a four-chip 512 x 512 is PROJECT_INPUT).

**Performance at 60-80 keV (D5; not the project's energy).** D5 abstract: "In single pixel mode, energy threshold
values can be chosen to maximize either the modulation transfer function or the detective quantum efficiency";
"The Medipix3 charge summing mode delivers simultaneous, high values of both modulation transfer function and
detective quantum efficiency." Sec. 4: in CSM at 60 keV "the MTF at the Nyquist frequency value is ca. 0.6 ... (the
theoretical square pixel detector MTF at Nyquist frequency = 0.64)". Sec. 4: CASINO lateral charge spread "(95%) at
60 keV is approximately 25 um and increases to approximately 42 um at 80 keV for a 300 um thick silicon substrate".

**What D5 says about 200 keV (the only 200 keV statement in D5).** Sec. 7 (p. 52): "primary energies between
160-300 keV ... lead to large average lateral dispersion (for 200 keV ~190 um, i.e. larger than two pixels range) in
a silicon sensor material [17]."

**Performance at 200 keV, Si sensor (D6) - the key measurement for this project.**
* Device and setup (D6 sec. 2, sec. 3 p. 4): Medipix3RX, 256 x 256, 55 um; "The Si sensor was operated with a
  positive bias of 110 V, with the ASIC set to collect holes"; typical temperature "approximately 28 C"; 60-200 keV
  data "by mounting the detectors on an FEI Tecnai T-20 TEM using the 35 mm port above the viewing screen";
  thresholds calibrated with fluorescence X-rays (absolute energy scale); knife-edge MTF, NPS by flat fields, DQE by
  Eqs. (3)-(6).
* Sensor thickness of the Si device: D6 sec. 1 (p. 2) says "We then compare the imaging performance of 500 um thick
  GaAs:Cr and Si sensors bonded to Medipix3 ASICs", whereas D12 sec. 4.1 describes the same measurement as "a 300 um
  p-on-n silicon sensor bonded to a Medipix3 ASIC, with a threshold set at 12.4 keV". **The two sources disagree; the
  Si thickness of the D6 device is therefore UNRESOLVED** (the D6 sentence can be read as applying to both sensors).
* D6 Table 1 (p. 5; "key values summarising the low threshold MTF and DQE measurements"), 200 keV, Si: MTF(omega_N)
  = 0.01, DQE(0) = 0.80, DQE(0.5 omega_N) = 0.17, DQE(omega_N) = 0.00 (GaAs:Cr at 200 keV: 0.26, 0.91, 0.79, 0.51).
  120 keV, Si: 0.14, 0.85, 0.55, 0.11. 80 keV, Si: 0.31, 0.96, 0.81, 0.37. 60 keV, Si: 0.38, 0.87, 0.73, 0.35.
  omega_N = 1/(2 x pixel pitch) (D6 sec. 3).
* D6 Fig. 8 caption: "200 keV SPM (a) MTF and (b) DQE for a Si detector at selected thresholds"; legend thresholds
  for the Si device TH0 = 12.4, 58.3 and 117.1 keV (read on the rendered figure). The 12.4 keV and 58.3 keV MTF curves
  coincide (Fig. 8(a), as viewed).
* D6 sec. 4 (p. 9): "the Si detector DQE(omega_N) for 200 keV electrons is 0.00 at low threshold, increasing to 0.01 at
  thresholds greater than 106.9 keV"; "The CSM DQE(omega_N) in Fig. 12(b) confirms the failure of the CSM algorithm to
  enhance detector performance for high-energy electrons in both sensors."; "The Si detector CSM DQE(omega_N) for 200
  keV electrons never exceeds 0.00 for all thresholds"; and (p. 7) "For 200 keV electrons with the Si detector
  operating in CSM, MTF(omega_N) decreases to a minimum of 0.00 at a threshold of 109.3 kV [sic] before increasing at
  thresholds above 130 keV." Sec. 3 (p. 4): at energies >= 120 keV the maximum energy deposited in one pixel is well below the primary
  energy (for 300 keV in GaAs:Cr SPM "160 keV").
* D6 sec. 5 (p. 9): "The Si sensor is homogeneous"; "The variation in intensity in the Si flat field image is due to
  the slight dispersion of the threshold across the pixel matrix."
* D6 sec. 6 (p. 10): "Medipix3 devices with Si sensors, as well as similar HPDs with Si sensors are routinely used at
  200 keV and 300 keV in a number of applications".
* Independent cross-check (D12, Timepix4, 55 um pixels, "300 um thick p-on-n silicon sensor", housing "based on the
  mechanics of their commercial Medipix3 system (the Merlin camera)"): abstract, MTF at Nyquist "dropping from
  approximately 0.16 at 100 keV to 0.0046 at 200 keV" in particle-counting use; event processing improved it "by
  factors of 2.12 for 100 keV and 3.16 for 200 keV". (Different chip; same sensor type and pitch.)

**Counting statistics (D10, Medipix2, 120 keV).** D10 Fig. 8 caption: "DQE(0) = (sum_i i N_i)^2 / [(sum_i i^2 N_i)
(sum_i N_i)], where N_i is the number of events in each frame where a single electron is counted in i adjacent
pixels" and "For a threshold of one half the incident energy only single pixel events are seen". D10 Medipix2
paragraph: "At higher energies the performance rapidly degrades as the range of the primary electrons increases."
(D10 has no 200 keV data: "results are presented for the Medipix2 at 120 keV".)

**Holography with direct-detection cameras (D13, abstract only; a MAPS camera, not a Medipix).** "the improved
modulation transfer functions and detective quantum efficiencies of both modes of the DDC give rise to significant
benefits over the conventional CCD cameras, specifically, a significant improvement in the visibility of the
holographic fringes and a reduction of the statistical error in the phase of the reconstructed electron wave
function." **No publication of off-axis electron holography recorded on a Medipix/Merlin detector was found**
(Europe PMC full-text queries `(holography OR hologram OR holograms) AND (Medipix OR Timepix OR "hybrid pixel")`,
19 hits, none an electron hologram on a hybrid-pixel detector; Crossref bibliographic queries "off-axis electron
holography Medipix", "electron holography Timepix hybrid pixel detector"; 04:49 UTC). This is a search result, not
evidence of absence.

### 3.3 Digitised 200 keV MTF and DQE of the Si Medipix3 (DERIVED_HERE from D6 Fig. 8)

Method: `l9/digitise_paton_fig8.py` extracts the embedded raster of D6 Fig. 8 (xref 246, 1005 x 1013 px), calibrates
both axes on the light-grey grid lines (0.2 spacing; y grid rows 91.0, 159.5, 229.0, 299.5, 368.0, 438.0 px), and
traces each curve by nearest-colour classification (column centroid of the longest run). Validation: the
"Square Pixel" reference curve is read as MTF = 0.899 at 0.5 omega_N and 0.646 at omega_N (sinc: 0.900 and 0.637) and
DQE = 0.81 and 0.416 (sinc^2: 0.81 and 0.405); the traced Si DQE at TH0 = 12.4 keV is 0.800 at 0 and 0.171 at 0.5
omega_N (Table 1: 0.80 and 0.17). Accuracy about +-0.02. Output: `l9/digitise_paton_fig8.out`, fit `l9/fit_mtf.out`.

| omega / omega_N | 0.10 | 0.20 | 0.25 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 | 0.80 | 1.00 |
|---|---|---|---|---|---|---|---|---|---|---|
| MTF, Si, 200 keV, SPM, TH0 = 12.4 / 58.3 keV (mean of the two coincident curves) | 0.95 | 0.815 | 0.73 | 0.64 | 0.45 | 0.29 | 0.17 | 0.09 | 0.045 | 0.01 (Table 1) |
| DQE, Si, 200 keV, SPM, TH0 = 12.4 keV | 0.76 | 0.61 | 0.54 | 0.46 | 0.30 | 0.17 | 0.09 | 0.04 | 0.02 | 0.00 (Table 1) |
| DQE, Si, 200 keV, SPM, TH0 = 58.3 keV | 0.58 | 0.43 | 0.36 | 0.28 | 0.15 | 0.07 | 0.03 | 0.005 | 0.004 | - |

(The 0.10 entry of the MTF row is the 58.3 keV curve, 0.951; the 12.4 keV curve is hidden under it there. The DQE value
at 0.10 omega_N is noisy in the figure.)

Gaussian fit (DERIVED_HERE, `l9/fit_mtf.py`): MTF(omega) = exp(-(omega/omega_0)^2) with omega_0 = 0.452 omega_N, i.e.
q_0 = 0.226 cycles/pixel, reproduces the digitised curve within 0.01 from 0.15 to 0.85 omega_N; it is equivalent to a
Gaussian presampling PSF of sigma = 0.997 pixel = 54.8 um (MTF = exp(-2 pi^2 sigma^2 q^2)). This is a description of
one published device (D6), not of the UVic detector.

### 3.4 Inferences for this project (labelled)

* I3.1 (DERIVED_HERE from D6 and the digitised curve): the hologram carrier is attenuated by MTF(q_c). With p pixels
  per carrier fringe (omega = 2/p in omega_N units): p = 4 (the demo B23 choice) gives MTF 0.29 (ideal square pixel
  0.90); p = 5: 0.45; p = 6: 0.58; p = 8: 0.73; p = 10: 0.815; p = 12: 0.86 (Gaussian fit within 0.01). On a Si Medipix3
  at 200 keV the measured fringe contrast is therefore the specimen-plane contrast times these factors, and holograms
  sampled at 4 pixels per fringe lose about 70 % of their contrast in the detector.
* I3.2 (DERIVED_HERE): extending the repository's phase-noise relation `sigma_phi = sqrt(2)/(mu sqrt(N))` (C report
  7.4, docs/03) to a detector with DQE(q): with N the incident electrons in the reconstruction cell and mu the incident
  fringe contrast, the sideband SNR scales with sqrt(N DQE(q_c)), so sigma_phi = sqrt(2)/(mu sqrt(N DQE(q_c))) for a
  narrow sideband. Using the D6 SPM low-threshold DQE: at 4 px/fringe DQE(q_c) = 0.17, noise x 2.4 relative to an ideal
  counting detector at the same dose; at 8 px/fringe 0.54, x 1.36. (A finite sideband mask averages DQE over the mask;
  the numbers are for the carrier frequency.) This is consistent in direction with D13 (abstract), not a
  reproduction of it.
* I3.3 (DERIVED_HERE from D6 sec. 4 and D10 Fig. 8 caption): at 200 keV and low threshold one electron is counted in
  several pixels (lateral dispersion ~190 um, D5), so counts are not "gain x Poisson(electrons)": they are a compound
  Poisson sum with a cluster multiplicity m, mean counts n E[m] and variance n E[m^2], giving DQE(0) = E[m]^2/E[m^2]
  (times the detection efficiency), spatially correlated noise (NPS not white) and a counts-per-electron factor that
  depends on threshold. The current `record_holograms` (gain x Poisson) has DQE = 1 at all frequencies.
* I3.4 (DERIVED_HERE from D6 and D8): CSM gives no benefit at 200 keV on Si (D6 p. 9), so the relevant mode is SPM;
  which threshold was used decides both MTF and DQE (D6 Fig. 8: the 117 keV threshold raises MTF(omega_N) to about 0.36
  but drops DQE to about 0.02).
* I3.5 (DERIVED_HERE from D1, D7, D8): readout noise is effectively zero (thresholded counting), so the absence of a
  readout-noise term in the repository model is correct for this detector; dead-time and counter overflow do not matter
  at hologram fluxes if frames are summed (12-bit counters saturate at 4095 counts per frame; at low threshold one
  200 keV electron can add more than one count, so the per-frame count budget is below 4095 electrons).
* I3.6 (DERIVED_HERE): a single-chip MerlinEM has 256 x 256 pixels (D1). At 8 pixels per fringe that is 32 carrier
  fringes across the chip, and the reconstruction resolution (about three fringe spacings, docs/05 section 5 item 7)
  is 24 pixels, i.e. about 10 resolution elements across the field. The repository's ROI (`roi_shape`) should not
  exceed the real array (256 or 512 per axis, PROJECT_INPUT), and a four-chip array has inter-chip gaps (their width
  is not stated in any source read; UNVERIFIED).

### 3.5 Two further records on the Merlin (added during the search)

| # | Source | Locator | Label |
|---|---|---|---|
| D14 | M. Krajnak, A. L. Klyszejko (Quantum Detectors Ltd), "MerlinEM, Hybrid Pixel Array Counting Detector for Transmission Electron Microscopy.", mmc2023 incorporating EMAG 2023, abstract 210 (poster), `https://www.mmc-series.org.uk/abstract/1024-merlinem-hybrid-pixel-array-counting-detector-for-transmission-electron-microscopy.html` | abstract page (keywords; abstract text) | SECTION_READ (conference abstract; no DOI) |
| D15 | Z. Fang, A. M. Blackburn (University of Victoria, Department of Physics and Astronomy; Blackburn also CAMTEC), "Pulsed Electron Illumination and Beam Deflection Transfer Function Measurement using Multi-Trigger < 1 us Exposures on the Merlin - Medipix Detector", Microsc. Microanal. 30 (Supplement_1), ozae044.512 (2024), DOI 10.1093/mam/ozae044.512 (authors and affiliations from the Crossref record) | not read verbatim (section 0) | METADATA_VERIFIED (Crossref); content UNVERIFIED. It is the most likely published description of the UVic Merlin in use and is on the upload list |

D14 facts: keywords "MerlinEM; Merlin 4S; Merlin 4R; Merlin 1R; 4D STEM; ptychography; electron diffraction; EELS";
"a Medipix3 detector with a Merlin readout system was commercialised as a MerlinEM detector by a collaboration between
the University of Glasgow and Quantum Detectors Ltd. With more than 60 systems worldwide". Inference I3.7: the product
family has several head variants (1R, 4R, 4S per D14's keywords; 1R is the "retractable" single-chip mount of D7, the
meaning of 4R/4S is not stated in D14); Ali's detector must be identified by the label on the detector head or the
Merlin software's configuration (section 6).

## 4. Parameter table (mapped to docs/06 items)

"Not found" means: not stated in any source read in this report (sections 1-3); it stays PROJECT_INPUT. HF-3300
values that are not about the UVic HF-3300V are marked "(family)". All retrievals 2026-09-24.

| docs/06 item | Quantity | Value | Conditions | Source | Locator | Label |
|---|---|---|---|---|---|---|
| 1 | Accelerating voltages available on the UVic instrument | 60, 200, 300 kV | UVic HF-3300V STEHM | U1; U6; U4 | U1 "Instrument specifications"; U6 para. 2; U4 slide 4 | SECTION_READ |
| 1 | Voltage used for this work | 200 kV | all reflection holography | Ali | docs/06 item 1 | PROJECT_INPUT |
| 2 | Electron source | cold field emission; W single-crystal emitter "(~10 nm dia)" | UVic, 2012 | U1; U4 | U1 first bullet; U4 slide 5 | SECTION_READ |
| 2 | Energy spread (FWHM) | 0.32 eV (0.1 s), 0.34 eV (1.0 s) | 60 kV, "Beam current - 7 uA", 2013 | U5 | slide 6 (rendered) | SECTION_READ |
| 2 | Energy spread | "~ 0.3 eV" | voltage not stated, 2012 | U4 | slide 6 | SECTION_READ |
| 2 | Energy spread vs emission current (family) | 0.45 / 0.55 / 0.7 eV | cold FE W(310), Ie = 10 / 30 / 100 uA, voltage not stated | H1 | Table 1, p. 132 | SECTION_READ |
| 2 | Energy spread at 200 kV, UVic | not found; bracket 0.3-0.7 eV for the chromatic envelope | - | I2.1 | section 2.4 | ASSUMPTION (bracket DERIVED_HERE from U5 and H1) |
| 2 | Brightness | "6x10e13 A/m2 sr" (measured) | voltage, current, reduced or not: not stated | U1 | first bullet | SECTION_READ |
| 2 | Brightness (family) | 2.9e8 / 8.7e8 / 2.9e9 A cm^-2 sr^-1 | Ie = 10 / 30 / 100 uA, voltage not stated | H1 | Table 1 | SECTION_READ |
| 2 | Emitting-area size (family) | "in the order of a few nm" | - | H1 | pp. 132-133 | SECTION_READ |
| 2 | Effective source size / coherence width at the specimen | not found | - | - | - | PROJECT_INPUT |
| 3 | Illumination convergence semi-angle | not found ("Convergence angle, alpha - ?") | UVic, 2013 | U5 | slide 6 | PROJECT_INPUT (blocking) |
| 3 | Condenser optics | "Probe Forming Lenses (Condenser Lenses)", one condenser-side biprism; three condenser lenses below a condenser biprism in the H6 analogue (not UVic) | - | U4; H6 | U4 slides 7-8; H6 abstract | SECTION_READ (U4); +ABSTRACT(PubMed) (H6) |
| 5 | Detector pixel pitch | 55 um (square) | Medipix3/Medipix3RX | D1; D2; D5; D8 | D1/D2 "Specifications"; D5 sec. 2; D8 sec. 2 | SECTION_READ |
| 5 | Pixel array per chip | 256 x 256; "Other array sizes available on request" | MerlinEM standard | D1; D8 | D1 "Specifications"; D8 sec. 2 | SECTION_READ |
| 5 | Array of the UVic detector | not found (1 chip or 4 chips) | - | U10 names only "Merlin (Medipix3)" | U10 | PROJECT_INPUT |
| 5 | Detector Nyquist frequency | 9.1 lp/mm (= 1/(2 x 55 um)) | - | D5 | sec. 2, p. 45 | SECTION_READ |
| 5 | Magnification range (family, stock HF-3300) | TEM x200 to x1.5M | distributor, voltage not stated | H2 | "Features & Variations" | SECTION_READ (distributor) |
| 5 | Magnification at the detector, specimen-referred pixel (both axes) | not found | - | - | - | PROJECT_INPUT (blocking) |
| 5 | Recommended carrier sampling | >= 8 detector pixels per fringe (MTF >= 0.73, DQE(q_c) >= 0.54 on Si at 200 keV); 4 px/fringe gives MTF 0.29 | Si Medipix3, 200 keV, SPM, low threshold | D6 Fig. 8 digitised | section 3.3-3.4 (I3.1, I3.2) | DERIVED_HERE |
| 6 | Detector type at UVic | "Merlin (Medipix3) high speed pixelated direct-electron detector" | page undated (footer 2017) | U10 | whole page | SECTION_READ |
| 6 | Detector type used for the holograms | "midi pixel by quantum detectors" (Medipix-based, Quantum Detectors) | model not confirmed | Ali | docs/06 item 6 | PROJECT_INPUT |
| 6 | Sensor | silicon ("Detects electrons directly in silicon"); Si 300 um standard in D5, D7; 500 um "needed for operation at ... 300 keV" (D7) | MerlinEM | D1; D5; D7 | D1 "Specifications"; D5 sec. 2; D7 sec. II | SECTION_READ; UVic thickness PROJECT_INPUT |
| 6 | Counter depths and readout times | 1 / 6 / 12 / 24 bit; 70.8 us / 412 us / 822 us / 1.64 ms | Merlin, 120 MHz clock | D7; D8 | D7 sec. II; D8 sec. 3 | SECTION_READ |
| 6 | Maximum counts per frame | 1, 63, 4095 (1, 6, 12 bit); 24 bit: "1 to 16.7 x 10^6" | - | D7; D5 | D7 sec. II; D5 sec. 6 | SECTION_READ |
| 6 | Frame rate | "Up to 2000 fps (12-bit mode)"; 12,500 fps at 1 bit (CRW) | MerlinEM; D7 system | D1; D2; D7 | "Specifications"; D7 sec. II | SECTION_READ |
| 6 | Dead time | zero in continuous read-write ("dead time free", gapless) | CRW mode | D8; D1; D2 | D8 sec. 3; D1/D2 "Features" | SECTION_READ |
| 6 | Readout noise | "virtually zero readout noise" (threshold counting); front-end ~72 e- rms, threshold dispersion ~40 e- rms | D8: 300 um Si, SPM, after equalisation | D1; D8 | D1 "Features"; D8 abstract | SECTION_READ |
| 6 | Counting modes | single pixel mode (SPM); charge summing mode (CSM, 2 x 2 summing) | Medipix3RX | D8; D5; D6 | D8 sec. 3; D5 sec. 2; D6 sec. 2 | SECTION_READ |
| 6 | Lateral charge dispersion in Si | ~190 um ("larger than two pixels range") | 200 keV, CASINO | D5 | sec. 7, p. 52 | SECTION_READ |
| 6 | MTF at Nyquist, Si | 0.01 | 200 keV, SPM, low threshold | D6 | Table 1, p. 5 | SECTION_READ |
| 6 | DQE(0), DQE(0.5 omega_N), DQE(omega_N), Si | 0.80, 0.17, 0.00 | 200 keV, SPM, low threshold (TH0 = 12.4 keV per D6 Fig. 8 and D12) | D6 | Table 1, p. 5 | SECTION_READ |
| 6 | MTF(omega), Si, full curve | 0.815 / 0.73 / 0.45 / 0.29 / 0.17 at 0.2 / 0.25 / 0.4 / 0.5 / 0.6 omega_N; Gaussian fit sigma_PSF = 1.0 pixel (q_0 = 0.226 cycles/pixel) | 200 keV, SPM, TH0 = 12.4 and 58.3 keV | D6 Fig. 8(a) | digitised, section 3.3 | DERIVED_HERE (from SECTION_READ figure) |
| 6 | DQE(omega), Si | 0.61 / 0.54 / 0.30 / 0.17 / 0.09 at 0.2 / 0.25 / 0.4 / 0.5 / 0.6 omega_N | 200 keV, SPM, TH0 = 12.4 keV | D6 Fig. 8(b) | digitised, section 3.3 | DERIVED_HERE |
| 6 | CSM at 200 keV, Si | no benefit: CSM DQE(omega_N) "never exceeds 0.00" | 200 keV | D6 | sec. 4, p. 9 | SECTION_READ |
| 6 | Si sensor thickness of the D6 device | 500 um (D6 p. 2 wording) or 300 um (D12 sec. 4.1) | - | D6; D12 | D6 sec. 1; D12 sec. 4.1 | UNVERIFIED (sources disagree) |
| 6 | Gain (counts per electron) at 200 keV | not found | - | - | - | PROJECT_INPUT (or measure) |
| 6 | Operating mode, threshold, counter depth, frame time, frames per hologram, dose per hologram, exposure, drift | not found | - | - | - | PROJECT_INPUT |
| 6 | Other cameras on the instrument | Gatan "USC 1004 2k x 2k" (2013); "A large CCD detector" | UVic | U5; U3 | U5 slide 10; U3 p. 1 | SECTION_READ (which camera recorded the holograms: PROJECT_INPUT) |
| 15 | Biprisms installed | 4: "One above specimen, and three below the specimen with magnification between lower biprisms equal to one" | UVic | U1; U7; U10; U4 | U1; U7; U10; U4 slides 8, 16 | SECTION_READ |
| 15 | Reference trajectory at the specimen | not found | - | - | - | PROJECT_INPUT (blocking) |
| 15 | Published analogue of a condenser-biprism tilted reference for dark-field holography | "relative tilt magnitude up to 20/nm at the object plane (300kV)"; "A first dark-field hologram with a tilted - object-free - reference wave" | not UVic; microscope not named in the abstract | H6 | abstract | +ABSTRACT(PubMed) |
| 16 | Carrier fringe spacing | "Hologram carrier fringes down to ~4 pm" (capability, no conditions) | UVic, 2012 | U4 | slide 17 | SECTION_READ (not a measured carrier of this experiment: PROJECT_INPUT) |
| 16 | HF-3300 family holography practice | double-biprism, 60 s per hologram, "inter-fringe distance of 1.4 nm", 3.7 nm phase resolution | I2TEM, 300 kV (not UVic) | H4 | Methods, "Electron holography" | SECTION_READ |
| 16 | Object-reference separation D0, overlap width, fringe contrast | not found | - | - | - | PROJECT_INPUT |
| 17 | Empty-hologram residual phase, Fresnel fringes, reference-hologram practice | not found | - | - | - | PROJECT_INPUT |
| 18 | Biprism voltages | not found | - | - | - | PROJECT_INPUT (optional) |
| (21) | Imaging energy filter / spectrometer | "Imaging energy filter (Gatan Quantum)"; EELS | UVic | U1; U6 | U1 "Detectors"; U6 | SECTION_READ |
| (lens) | Objective Cs, Cc | not found; image corrector CEOS B-COR (Cs + coma), "Cc partially corrected"; STEM corrector CEOS SC-COR (Cs + Cc, ExB Wien filter) | UVic | U4; U5; U1; H5 | U4 slides 14-15; U5 slide 5; U1; H5 Methods | SECTION_READ (values: PROJECT_INPUT if lens transfer is used) |
| (22, drift) | Stability | room "+/- 0.025 C over 1 hour" (U1; U4 slide 19: "+ 0.1 oC per hour", 2012); HRTEM drift "< 7 pm/sec" at 60 kV | UVic | U1; U4; H5 | U1; U4 slide 19; H5 Methods | SECTION_READ |
| (12c) | Gun vacuum | "10-13 torr (10-11 Pa)" (gun); specimen-area pressure not found | UVic | U4; U5 | U4 slide 5; U5 slide 5 | SECTION_READ |
| (12a) | Ion mill and plasma cleaner at the AMF | Fischione 1010 ion mill, Fischione 1020 plasma cleaner; FIB Hitachi FB-2100 | UVic AMF (not evidence of what Ali used) | U9; U4; U8 | U9 AMF paragraph; U4 slide 2; U8 | SECTION_READ |

## 5. What `reflection_holo/optics/detector.py` would need to represent this detector at 200 kV (recommendation, not code)

Current state (read, section header): pitch/M pixel mapping with a consistency check; band-limited resampling of the
complex wave to pixel centres (point sampling; "pixel integration and the MTF are NOT IMPLEMENTED"); counts =
gain x Poisson(dose x I/mean(I)); `mtf = "none"` only; no readout noise; drift not implemented. Demo stand-ins B23
(15 um pitch, M = 3.0e5, 0.05 nm) and B24 (gain 1, 500 e/px, Poisson only, no MTF). Numbers below are from
`l9/l9_numbers.py` (output `l9/l9_numbers.out`) unless a source is named. All items are DERIVED_HERE recommendations.

1. **Declared identity of the detector (new required fields, PROJECT_INPUT item 6).** model and head variant (e.g.
   MerlinEM 1R, D7/D14), chip layout (1 x 1 = 256 x 256, or 2 x 2 = 512 x 512 with inter-chip gaps), sensor material
   and thickness (Si 300 or 500 um, D7), counting mode (SPM or CSM), threshold(s) TH0 (and TH1) in keV, counter depth
   (1/6/12/24 bit), frame time, number of frames summed per hologram, flat-field (gain) correction applied or not,
   masked-pixel list. A "comparison" run should refuse a detector without them, as it already refuses demo stand-ins.
2. **Pitch and magnification.** pitch = 55 um on both axes (D1, D8) if the holograms were recorded on the Merlin; the
   specimen-referred pixel is 55 um / M with M the magnification at the Merlin plane, which must be calibrated at that
   camera (the Merlin sits on its own port, e.g. "the 35 mm port above the viewing screen" in D5/D6 or a retractable
   mount in D7, so the nominal screen magnification does not apply). For the demo, B23's 0.05 nm image pixel with a 55
   um pitch needs M = 1.1e6 (B23 states 15 um and 3.0e5, which is not this detector). Carrier sampling: pixels per
   fringe = s_c M / 55 um. The along-beam surface sampling stays pixel/sin(theta) (x 61.98 at 16.1347 mrad): for
   example a 2.0 A carrier at 8 px/fringe needs M = 2.2e6 (0.25 A pixel, 15.5 A of surface per pixel along the beam,
   and a 256-pixel chip spans 0.40 um of surface along the beam and 6.4 nm across it); a 10 A carrier at 8 px/fringe
   needs M = 4.4e5 (256 px = 1.98 um along the beam).
3. **ROI limits.** `roi_shape` must not exceed the physical array (256 or 512 per axis); for a four-chip head the
   inter-chip gap columns/rows must be masked (their width is UNVERIFIED here; take it from the Merlin configuration).
4. **MTF, applied to the recorded intensity, once, on an oversampled grid.** The detector responds to intensity, so
   the MTF belongs after hologram formation, never on the complex wave (the coherent lens transfer is separate, docs/05
   section 5 item 2). Form the hologram intensity on a grid oversampled at least x2 relative to the detector pixels,
   multiply its spectrum (padded, with the existing no-wrap rule) by the presampling MTF expressed in cycles per
   detector pixel, then point-sample at the pixel centres. The measured presampling MTF of D6 already includes the
   integration over the pixel (D6 sec. 3), so no extra sinc must be multiplied in. Accept two MTF inputs: (a) a
   tabulated MTF(omega/omega_N) measured on the UVic detector at 200 kV with the threshold actually used (knife edge,
   D6 sec. 3 method), label PROJECT_INPUT; (b) as a demo stand-in only, the Gaussian MTF(q) = exp(-(q/0.226)^2) (q in
   cycles/pixel; sigma_PSF = 1.0 pixel), fitted in section 3.3 to D6 Fig. 8(a) for a Si Medipix3 at 200 keV, SPM,
   TH0 = 12.4-58 keV, label ASSUMPTION (source D6, device not the UVic one). With MTF(omega_N) about 0.01 aliasing of
   the intensity is negligible at 200 keV; the existing band check on the complex wave should be complemented by a check
   that the hologram intensity band (|q_c| plus the object band) lies below the detector Nyquist frequency.
5. **Counting statistics (replaces gain x Poisson for this detector).** At 200 keV and low threshold one electron is
   counted in several pixels (D5: ~190 um lateral dispersion; D6), so the detector is a compound-Poisson counter:
   electrons arrive Poisson(dose x I) on the oversampled grid, and each electron adds a random cluster of counts whose
   mean footprint is the PSF of item 4 and whose multiplicity m fixes counts per electron g = E[m] and DQE(0) = E[m]^2 /
   E[m^2] (D10 Fig. 8 caption, times the detection efficiency). The noise is then spatially correlated. Targets a
   simulated flat field and knife edge must reproduce (from D6 Table 1 and the digitised curves): DQE(0) = 0.80;
   DQE(omega) 0.61 / 0.54 / 0.30 / 0.17 at 0.2 / 0.25 / 0.4 / 0.5 omega_N; implied normalised noise power NNPS =
   DQE(0) MTF^2 / DQE = 0.87 / 0.78 / 0.54 / 0.39 at the same frequencies (D6 Eq. (6) rearranged). The present model
   (white Poisson, g x Poisson) has DQE = 1 at all frequencies and would understate the phase noise. A cheaper
   alternative with the same second-order statistics: Gaussian noise with the prescribed NPS(q) added to g x n x
   (I convolved with PSF); acceptable when the counts per pixel are large (tens or more), not in the few-count regime of
   weak dark-field images.
6. **Phase-noise bookkeeping (for reports and for the acceptance tests).** Extend the repository relation
   sigma_phi = sqrt(2)/(mu sqrt(N)) to sigma_phi = sqrt(2)/(mu sqrt(N DQE(q_c))) with mu the incident (specimen-plane)
   fringe contrast; the measured contrast is mu MTF(q_c). With the D6 curves: 4 px/fringe MTF 0.29, DQE 0.17, noise x
   2.42 relative to an ideal counting detector; 5: 0.45, 0.30, x 1.82; 6: 0.58, 0.41, x 1.57; 8: 0.73, 0.54, x 1.36; 10:
   0.815, 0.61, x 1.28. The demo sampling of 4 px/fringe (B23) is the worst case for this detector; the B29 minimum
   visibility of 0.5 would be failed by a specimen-plane contrast below 0.5/0.29 = 1.7, i.e. always, at 4 px/fringe on a
   Si Medipix3 at 200 keV (DERIVED_HERE; the orchestrator decides whether B23/B29 change).
7. **Readout noise: keep "none".** D1 ("virtually zero readout noise") and D7 (noiseless operation "by the setting of an
   appropriate threshold") support the present omission for this detector.
8. **Frames and counter depth.** Model an exposure as the sum of N_f frames (gapless in continuous read-write, D8), each
   capped at 2^bits - 1 counts (63, 4095 or 16,777,215); at low threshold one 200 keV electron can add more than one
   count, so the per-frame electron budget is below the cap. Frames are also where drift enters (docs/06 item 6: a
   coherent envelope loss per frame, not noise).
9. **Fixed-pattern response.** An optional per-pixel gain map (rms from Ali's flat field) represents threshold
   dispersion (D6 sec. 5: Si flat field variation "due to the slight dispersion of the threshold across the pixel
   matrix"; D8: ~40 e- rms threshold dispersion); division by the empty hologram (B29) cancels a static map, which is a
   useful test. Masked (dead or noisy) pixels enter as a mask that the reconstruction already refuses (B29).
10. **Mode choice.** SPM is the relevant mode at 200 keV (D6: CSM gives no benefit on Si). A high threshold (e.g.
    117 keV) raises MTF(omega_N) to about 0.36 but drops DQE to about 0.02 (D6 Fig. 8, as read): for dose-limited dark-field
    holograms the low-threshold SPM setting is the one to model unless Ali states otherwise.
11. **Tests to add (recommendation).** knife-edge test reproducing the declared MTF; flat-field test reproducing DQE(0)
    and NNPS; fringe test (carrier contrast multiplied by MTF(q_c)); phase-noise test against item 6; ROI-versus-array
    refusal; counter-overflow refusal.

## 6. What Ali must still confirm (PROJECT_INPUT)

1. **Detector identity:** the model on the detector head (MerlinEM with head variant 1R, 4R, 4S or other; D14), number
   of chips and array (256 x 256 or 512 x 512), sensor material and thickness (Si 300 or 500 um, or other), mount
   position (retractable above the screen, below, or after the GIF), and whether the holograms were recorded on this
   Merlin at all (U5 names a Gatan 2k x 2k camera on the same microscope in 2013).
2. **Detector mode:** SPM or CSM; TH0 (and TH1) in keV; counter depth; continuous read-write on or off; frame time;
   frames summed per hologram; flat-field correction used; masked pixels.
3. **Magnification and pixel size:** calibrated magnification at the Merlin plane and the specimen-referred pixel size
   on both axes (item 5), with the calibration method.
4. **Dose and exposure:** electrons (or counts) per pixel per hologram, exposure time, beam current if known (item 6).
5. **Biprisms actually used:** which of the four (the condenser-side one and/or which of the three image-side ones),
   their voltages (only if they may be published, item 18), and, preferably, the measured carrier fringe spacing
   (pixels and specimen nm, which axis) and overlap width (item 16); whether the condenser biprism pre-tilted the
   reference (the H6-type arrangement) and where the reference passed at the specimen (item 15); whether an empty
   reference hologram was recorded with each object hologram (item 17).
6. **Source and illumination at 200 kV:** zero-loss FWHM (the GIF/EELS on the instrument can measure it), emission
   current or extraction voltage, and the illumination convergence semi-angle with the condenser settings (items 2-3,
   blocking).
7. **Detector characterisation data, if any:** a knife-edge image and flat-field series at 200 kV on this Merlin with
   the threshold used (lets the simulation use a measured MTF/DQE instead of D6's).
8. **Imaging mode:** whether the TEM image corrector (B-COR) was on and its residual Cs, the objective-lens state
   (normal or a field-free/Lorentz setting, none of which is described on the facility pages), and whether any hologram
   was energy-filtered (item 21).
9. **Specimen holder** used for the glancing-incidence mounting of the Si(001) piece (not among the holders listed in
   U1).

## 7. Documents to request from Ali (upload list; unread items)

| Priority | Document | Why | Access problem |
|---|---|---|---|
| 1 | MerlinEM datasheet for the installed head, or the Merlin configuration/settings file of the UVic detector | model, array, sensor, thresholds, modes | QD datasheet behind a personal-data form (not submitted) |
| 1 | Z. Fang, A. M. Blackburn, Microsc. Microanal. 30 (Suppl. 1) ozae044.512 (2024), DOI 10.1093/mam/ozae044.512 (D15) | UVic authors on the Merlin; likely names the configuration | academic.oup.com Cloudflare |
| 1 | R. A. Herring, D. Hoyle, Y. Taniguchi, M. Haider, Microsc. Microanal. 19 (S2) 320-321 (2013), DOI 10.1017/s1431927613003590 (H7), and R. A. Herring, D. Hoyle, Microsc. Microanal. 21 (S3) 347-348 (2015), DOI 10.1017/s1431927615002536 (H8) | the only peer-reviewed descriptions of the UVic STEHM found: source, biprisms, stability | OUP Cloudflare; Cambridge PDFs 404 |
| 2 | A. M. Blackburn, R. A. McLeod, Microscopy 70(1) 131-147 (2021), DOI 10.1093/jmicro/dfaa055 (H11, [P42]) | UVic holography and ptychography; may give the detector and holography settings on the HF-3300V | OUP Cloudflare; closed |
| 2 | F. Roder et al., Ultramicroscopy 161, 23-40 (2016), DOI 10.1016/j.ultramic.2015.11.004 (H6) | condenser-biprism tilted reference for dark-field holography (R1 with pre-tilt, B28) | closed; HAL notice only |
| 2 | S. L. Y. Chang et al., Ultramicroscopy 161, 90-97 (2016), DOI 10.1016/j.ultramic.2015.09.004 (D13) | how MTF and DQE enter hologram visibility and phase error | closed |
| 3 | K. Harada et al., J. Appl. Phys. 99, 113502 (2006), DOI 10.1063/1.2198987 (H10) | three image-side biprisms, as cited by UVic (U3) | pubs.aip.org blocked (L8, same day) |
| 3 | Hitachi HF-3300 brochure ("Unique Functions") and datasheet (H3) | manufacturer specification of the family | hitachi-hightech.com 403 (Akamai) |
| 3 | E. Snoeck et al., Microsc. Microanal. 20 (S3) 932-933 (2014), DOI 10.1017/s1431927614006382 (H9) | HF-3300 (I2TEM) B-COR in Lorentz and HREM modes | OUP Cloudflare |
| 4 | G. McMullan et al., Ultramicroscopy 107, 401-413 (2007), DOI 10.1016/j.ultramic.2006.10.005 (D11) | Medipix2 electron imaging (background only) | closed |
| - | Any UVic facility documentation of the HF-3300V biprisms (positions, filament diameters, voltage ranges) and of the Merlin installation | items 15-18 | not public |

## 8. Scope statement: what was read, what was not, and the evidence labels used

* **Read (SECTION_READ, with locators above):** U1-U10 (UVic facility pages and AMF PDFs); H1 (Hitachi Review 2008,
  whole), H2 (distributor page), H4 and H5 (Methods paragraphs); D1-D3 (Quantum Detectors pages and application note),
  D5 and D6 (full text), D7, D8, D9, D10, D12 (the sections listed), D14 (abstract page).
* **Abstract only (+ABSTRACT(PubMed), Europe PMC):** H6, H11, H12 (three Herring abstracts), D13. The OpenAlex abstract
  index was not used.
* **Metadata only (METADATA_VERIFIED, content UNVERIFIED):** H7, H8, H9, H10, D11, D15; H3 and D4 (manufacturer
  documents) are UNVERIFIED and not even metadata-verified.
* **DERIVED_HERE:** the digitisation of D6 Fig. 8 and its Gaussian fit (section 3.3), inferences I1.1-I1.5,
  I2.1-I2.2, I3.1-I3.7, and every number in section 5 (scripts `l9/digitise_paton_fig8.py`, `l9/fit_mtf.py`,
  `l9/l9_numbers.py`, with outputs `*.out`, all in the scratchpad `l9/` directory named at the top; they read only the
  downloaded D6 PDF and constants stated in the scripts).
* **Not searched:** patents on the HF-3300 biprism system (the Hitachi patent PAT01 already in the repository is
  about reflection holography, L1); Japanese-language Hitachi technical news (Hitachi Scientific Instrument News) for
  the HF-3300; UVicSpace theses (a web search found no thesis on the HF-3300V with the Merlin, which is a search
  result only).
* **No personal contact details** (e-mail addresses, telephone numbers) of facility staff, authors or company staff are
  recorded; the facility pages and slides carry some and they were skipped.
* **Every DOI** in this report and in `docs/agent_reports/L9_new_refs.bib` was resolved at `api.crossref.org/works/<doi>`
  on 2026-09-24 without a mailto parameter; no DOI was constructed. Hitachi Review 2008 (H1) has no DOI.
* **Nothing was committed or pushed**; no file other than this report and `docs/agent_reports/L9_new_refs.bib` was
  written in the repository.
