# L9 - The microscope (Hitachi HF-3300, UVic) and the detector (Quantum Detectors, Medipix-based): sourced parameters

Prepared: 2026-09-24 by agent L9 (literature). Status: IN PROGRESS (written incrementally).
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
