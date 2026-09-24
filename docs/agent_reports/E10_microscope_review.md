# E10 - Adversarial review of L9 (UVic HF-3300V microscope and Quantum Detectors Merlin/Medipix3 detector)

Reviewer: agent E10, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`.
Status: COMPLETE (written incrementally, sections 0-11).

Scope: `docs/agent_reports/L9_microscope_detector.md` (726 lines, commit 7a0a7e1),
`docs/agent_reports/L9_new_refs.bib` (287 lines, 25 entries) and the scripts in `tools/lit/l9/`
(`digitise_paton_fig8.py`, `fit_mtf.py`, `l9_numbers.py` and their `.out` files, `README.md`), before the
orchestrator adopts a detector model (MTF, DQE, counting noise) and a minimum carrier sampling for the
simulated holograms. Context read: PROJECT_INPUT (Ali, 2026-09-24: Hitachi HF-3300 at UVic, 200 keV,
Quantum Detectors Medipix-based detector); `docs/06_project_inputs_required.md` items 1-6, 15-18, 21;
`docs/model_assumptions.md` B5, B10, B23, B24, B28, B29, B38; `reflection_holo/optics/detector.py`;
`reflection_holo/optics/hologram.py` (noise, fringe contrast); `reflection_holo/reconstruction/sideband.py`
(visibility rule); `docs/03_physics_summary.md` section 6 and `docs/agent_reports/C_physics_derivations.md`
section 7.4 (phase-noise relation); `configs/demo_smoke_si001.yaml` (B23/B28/B29 values).

Files written by E10: this report, `tools/review/e10_recompute.py` and its saved output
`tools/review/e10_recompute_output.txt`. No other repository file is edited; nothing is committed or pushed.
Raw downloads are kept outside the repository in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/e10/` (called `e10/`).
Every web page and PDF quoted below was downloaded again by E10 through the session proxy on 2026-09-24
(no form submitted, no personal data sent). L9's scratch copies in `l9/` were used only to compare hashes.
Independence: L9's three scripts are part of the material under review and were read (and rerun) before E10 wrote
its own; E10's digitiser therefore uses a deliberately different calibration (spines plus grid, jointly) and curve
tracing (colour-difference classes, column tracking), and the phase-noise derivation, the Monte Carlo and the B29,
demo and sideband-weighting numbers have no counterpart in L9's code.

Severity scale (as E6/E9): BLOCKER (must be fixed before anything is adopted), MAJOR (must be fixed or
re-worded before the affected item is adopted), MINOR (fix when adopting), NIT.

## 0. Access log (E10, 2026-09-24, UTC)

| Time | Host | Result |
|---|---|---|
| 05:05-05:06 | www.uvic.ca (U1, U6, U7, U8, U9 pages; U2-U5 PDFs), onlineacademiccommunity.uvic.ca (U10) | HTTP 200 for all; files byte-identical to L9's scratch copies (U1 a9a8881e...3dcc1e97, U2 f9a06591...2acdc5ba, U3 36f8b359...bd16b559, U4 d8a8e591...a24db043, U5 694bcaf1...e4d10114); L9's report prints the U4 suffix as "...a043" (the file ends "...b043"; nit, m4) |
| 05:06 | onlineacademiccommunity.uvic.ca WordPress REST API, `/emicro/wp-json/wp/v2/pages?slug=facilities&_fields=date,modified,link` | HTTP 200: page created 2020-01-20T21:22:32, modified 2023-01-04T22:08:48 |
| 05:08-05:16 | Europe PMC REST (PMC7910301 05:08; PMC2864625 05:13; PMC9233697 and PMIDs 26624513, 26630072, 32986121, 33269799, 35753170, 41202789 core records 05:16) | HTTP 200 |
| 05:08 | eprints.gla.ac.uk/240505 (record page and `240505.pdf`) | HTTP 200; PDF SHA-256 555e925c628ba9eb...6e80fc95c6, identical to L9's copy; the record page labels the file "Published Version", CC BY |
| 05:13 | quantumdetectors.com (MerlinEM, MerlinEM RDP pages), mmc-series.org.uk (abstract 210), arxiv.org (1911.11560, 2411.16258v2), iopscience.iop.org (C02016, C01038 PDFs), eprints.gla.ac.uk/143680 (Mir 2017) | HTTP 200. Mir 2017 and Nord arXiv hashes identical to L9's; the IOP PDFs and the QD pages differ in hash from L9's (dynamic pages / download-stamped PDFs; text checked instead) |
| 05:15 | api.crossref.org `/works/<doi>` for all 22 distinct DOIs in the L9 report and bib (User-Agent "E10-review/1.0", no mailto) | HTTP 200 for all 22 |
| 05:15-05:16 | www.hitachihyoron.com (Hitachi Review 2008 PDF), milexia.com | HTTP 200; H1 hash identical (f170b885...5be9c) |

No form was submitted and no personal data was sent. Staff names and contact details printed on some slides (U4 slide 27, U5) are not recorded here.

## 1. Task 1 - the UVic claims, re-read against their locators

Every UVic claim listed in the brief was found verbatim at L9's locator (E10 re-download, text layer; U5 slides
5 and 6 also rendered at 110 dpi and viewed):

| Claim (L9) | Locator | E10 result |
|---|---|---|
| "Hitachi HF-3300V STEHM", "Based on the Hitachi HF-3300 TEM" | U1 heading and first paragraph | CONFIRMED verbatim |
| cold FEG: "High brightness (measured as 6x10e13 A/m2 sr), high stability and high coherence cold-field-emmision electron source." | U1 "Instrument specifications", bullet 1 | CONFIRMED verbatim (spelling as on the page); also U4 slide 5 "New Cold-FEG Electron Gun Assembly", U5 slide 5 "Cold-field Electron Source (10-13 torr)" |
| 60/200/300 kV | U1 "60 keV, 200 keV, and 300 keV acceleration voltage."; U6 para. 2; U4 slide 4; U10 "60 – 300 kV" | CONFIRMED |
| four biprisms, "One above specimen, and three below the specimen with magnification between lower biprisms equal to one." | U1; U7 "4 holographic biprisms"; U10 "an illumination side bi-prism and 3 image side bi-prisms"; U4 slides 8 and 16 | CONFIRMED verbatim |
| CEOS correctors: "STEM Cs + Cc aberration corrector (ExB Wien filter) (CEOS SC-COR)", "Aplanatic TEM Cs + Coma aberration corrector (CEOS B-COR)" | U5 slide 5 (rendered) | CONFIRMED on the rendered slide (labels and arrow positions as L9 describes: "1 electron biprism + dislocated hologram aperture" at the upper column, "3 electron biprisms + extra lenses" below the TEM corrector, "EELS + GIF" at the base) |
| "Imaging energy filter (Gatan Quantum)." | U1, list under "Detectors:" | CONFIRMED verbatim |
| "is fitted with a Merlin (Medipix3) high speed pixelated direct-electron detector" | U10 | CONFIRMED verbatim |
| 0.32 eV (0.1 s) and 0.34 eV (1.0 s) FWHM at 60 kV, "Beam current - 7 uA", "Convergence angle, alpha - ?" | U5 slide 6 (rendered) | CONFIRMED on the rendered slide; the in-plot caption reads "60kv 16ev disp 0.32ev rez 0.10 sec" |

Claims that rest on inference (L9 labels most of them; the ones marked "not flagged" are findings below):
* Ali's detector is the U10 Merlin: inference I1.2, correctly labelled.
* H5 (Reidy et al. 2021) is "the UVic instrument": not flagged (finding m1).
* "the requested energy-filtered measurement ... is instrumentally possible in principle": labelled DERIVED_HERE, but
  worded more strongly than the sources allow (finding m5, section 6).
* the U1 brightness is "6 x 10^13" (I1.1): correctly labelled as a reading of an ambiguous notation.

Other facility statements E10 found that L9 did not use (relevant to tasks 1 and 6):
* U10 hyperlinks the word "Merlin" to `https://quantumdetectors.com/n/products/merlinem/` (HTML source of U10), i.e.
  the group links its detector to the MerlinEM product page. L9 writes "The page does not say "MerlinEM"", which is
  true of the visible text; the link target is supporting evidence for the product family only (head variant, chip
  count and sensor remain PROJECT_INPUT). Finding m2.
* U10 is not a 2017 page: the site's WordPress REST record for the same URL gives `"date":"2020-01-20T21:22:32"`,
  `"modified":"2023-01-04T22:08:48"`; the "(c) 2017" is the theme footer. The Merlin sentence therefore stood on the
  page at its last change (2023-01-04), not necessarily at creation. Finding m3.
* U10 also states "energy filtered imaging and electron energy loss spectroscopy"; U9 (tool list) "HF-3300V ... with
  aberration correction, EELS/EFTEM, EDX, holography and tomography"; U9 (facilities) "equipped for holography, EDS,
  and GIF"; U4 slide 6 "Necessary for energy-filtered imaging (GIF) and energy-filtered holography measuring bandgaps
  and quasiparticle properties"; U5 slide 5 "EELS + GIF" (at the base of the column). Used in section 6.
* U5 slide 6 also prints "The energy spread will improve with age as the tip flattens." and the spectrum caption
  "0.32ev rez": the 0.32/0.34 eV values are zero-loss widths measured with the spectrometer (source spread
  convolved with the spectrometer response), i.e. upper bounds on the source spread at 60 kV. Nit n1.

## 2. Task 2 - Paton et al. 2021 (D6), re-read

Copy read: `eprints.gla.ac.uk/240505/1/240505.pdf`, 13 pages, PDF metadata subject "Ultramicroscopy, 227 (2021)
113298", running heads "Ultramicroscopy 227 (2021) 113298" with article page numbers 1-13, "Available online 29 April
2021", CC BY 4.0. The Glasgow record page labels this file "Published Version". **It is not the accepted
manuscript**: L9's report ("Publisher version") is right, while `tools/lit/l9/README.md` ("Glasgow
accepted-manuscript PDF"), the script's file name `pdf/Paton2021_gla_AAM.pdf` and the E10 brief ("the Glasgow
accepted manuscript") are wrong. Page numbers below are the article's own (= PDF pages). Finding m4.

| L9 statement | Locator | E10 result |
|---|---|---|
| 200 keV Si: MTF(omega_N) 0.01, DQE(0) 0.80, DQE(0.5 omega_N) 0.17, DQE(omega_N) 0.00 | Table 1, p. 5 ("Comparison of key values summarising the low threshold MTF and DQE measurements presented in Figs. 2, 3, 7, 8 and 9") | CONFIRMED (text layer; columns Energy, Sensor, MTF(omega_N), DQE(0), DQE(0.5 omega_N), DQE(omega_N), Max. Diff., Min. Diff.) |
| GaAs:Cr 200 keV 0.26/0.91/0.79/0.51; Si 120 keV 0.14/0.85/0.55/0.11; 80 keV 0.31/0.96/0.81/0.37; 60 keV 0.38/0.87/0.73/0.35 | Table 1, p. 5 | CONFIRMED |
| Fig. 8 caption and legend TH0 = 12.4, 58.3, 117.1 keV (Si) | Fig. 8, p. 7 | CONFIRMED (embedded raster xref 246 viewed). D6 p. 6 gives the choice: "the lowest threshold above the noise level of both detectors; the highest threshold common to both devices at which the knife-edge data could be fit and the threshold equal to half the highest threshold" |
| the 12.4 and 58.3 keV MTF curves coincide | Fig. 8(a) | CONFIRMED visually, and by D6's own text, p. 7: "Increasing the counting threshold does not initially improve the MTF (which is also apparent in Figs. 8(a) and 9(a))" |
| CSM: "confirms the failure of the CSM algorithm to enhance detector performance for high-energy electrons in both sensors"; "The Si detector CSM DQE(omega_N) for 200 keV electrons never exceeds 0.00 for all thresholds" | sec. 4, p. 9 | CONFIRMED verbatim. The CSM evidence is at omega_N (Figs. 10(b), 12(b)) and DQE(0) (Fig. 11(b)); no CSM curve at the carrier frequencies is published, so "no benefit at 200 keV" is D6's conclusion, not a measured statement at 0.25-0.5 omega_N (L9 I3.4 is labelled DERIVED_HERE; acceptable) |
| "MTF(omega_N) decreases to a minimum of 0.00 at a threshold of 109.3 kV [sic]" | p. 7 | CONFIRMED |
| Si DQE(omega_N) 0.00 at low threshold, 0.01 above 106.9 keV | sec. 4, p. 9 | CONFIRMED |
| bias 110 V, holes collected, about 28 C; T-20 "35 mm port above the viewing screen" | sec. 2 p. 2; sec. 3 p. 4 | CONFIRMED (L9's combined locator "sec. 2, sec. 3 p. 4" is right: the bias and temperature are on p. 2, the T-20 mount on p. 4) |
| sensor thickness: "500 um thick GaAs:Cr and Si sensors" (D6) vs "a 300 um p-on-n silicon sensor bonded to a Medipix3 ASIC, with a threshold set at 12.4 keV" (D12) | D6 sec. 1, p. 2; D12 sec. 4.1 (arXiv v2) | CONFIRMED verbatim; the ONLY thickness statement in D6 is the p. 2 sentence (E10 searched the whole text layer for "um", "thick"); D6 sec. 2 describes the Si device as "high resistivity n-type Si with p+ on n implants", consistent with D12's "p-on-n". UNRESOLVED stands; the most natural reading of the D6 sentence is 500 um for both |
| "The Si sensor is homogeneous"; flat-field variation "due to the slight dispersion of the threshold" | sec. 5, p. 9 | CONFIRMED |

**Not stated by L9 and material for the detector model (finding M1):** D6 sec. 3, p. 3 obtains every MTF by fitting
the edge-spread function with ONE error function, "ESF_fit(x) = A/2 (1 + erf((mu - x)/sigma)) (1)", "We have found
that a single error function, as defined in Eq. (1), provided a good fit to the ESF", and "The MTF was then
calculated as the modulus of the Fourier transform of the LSF that is calculated from differentiating ESF_fit". The
derivative of an error function is a Gaussian, so every published D6 MTF curve is exactly
MTF(omega) = exp(-(pi sigma omega)^2). D6 also computes DQE(omega) from this model MTF (Eq. (6), p. 4:
DQE(omega) = DQE(0) MTF_pre^2(omega) / NNPS(omega)).

## 3. Task 3 - digitisation and fit, rerun and redone independently

**Rerun (REPRODUCED).** L9's three scripts, copied to `e10/l9rerun/` with the E10 download of the D6 PDF under the file
name the script expects, reproduce `digitise_paton_fig8.out`, `fit_mtf.out` and `l9_numbers.out` byte for byte
(`diff` empty). `digitise_paton_fig8.py` needs `pymupdf`, which is not installed in the project `venv/`
(`ModuleNotFoundError`); the README does not say so (finding m4). `fit_mtf.py` and `l9_numbers.py` hard-code the
digitised numbers (they match the `.out` of the digitiser).

**Independent digitisation (E10, `tools/review/e10_recompute.py` section B).** Same embedded raster, different method:
axes from the black spines and the grid jointly (x = 0 at the left spine, right spine found at x = 1.0001 in panel
(a)), colour classes by channel differences, column-to-column tracking of the nearest pixel run. Validation: square-pixel
MTF 0.901 / 0.786 / 0.641 at 0.5 / 0.75 / 1.0 omega_N (sinc 0.900 / 0.784 / 0.637), square-pixel DQE 0.811 / 0.617 /
0.448 at 0.5 / 0.75 / 0.95 (sinc^2 0.811 / 0.615 / 0.446). Against Table 1: MTF(omega_N) 0.013 (0.01), DQE(0.5
omega_N) 0.168-0.170 (0.17), DQE(0) 0.787 (0.80; the curve is noisy below 0.1 omega_N). Against L9: max |difference|
0.004 on the 58.3 keV MTF (20 points) and 0.004 on the 12.4 keV DQE excluding omega = 0 (0.013 at omega = 0). **The
digitised Fig. 8 reproduces Table 1 within the stated +-0.02.**

One systematic detail: the 58.3 keV (navy) curve is drawn on top of the 12.4 keV (dark red) one, so only the lower
edge of the red line is visible; its trace reads 0.28 at 0.5 omega_N against 0.297 for the fully visible navy line.
L9's "mean of the two coincident curves" (0.288 at 4 px/fringe, 0.728 at 8) is therefore biased low by about 0.01.
The navy trace gives 0.298 and 0.741; the Table-1-only Gaussian (next paragraph) gives 0.316 [0.266, 0.350] and
0.750 [0.718, 0.769]. Finding m6.

**Is the Gaussian fit adequate, and is a Gaussian the right form?** Fit to the navy trace 0.05-0.95 omega_N (19
points): Gaussian, linear least squares, omega_0 = 0.4558 omega_N (q_0 = 0.2279 cycles/px; PSF s.d. 0.988 px = 54.3 um;
D6 erf width sigma = 1.397 px = 76.8 um), rms residual 0.0028, no systematic trend (residuals -0.007 at 0.05, else
within +-0.004). A two-parameter stretched exponential exp(-(omega/a)^n) returns n = 2.000. The 117.1 keV curve is
also a Gaussian to 0.004. L9's value (omega_0 = 0.452 omega_N, sigma_PSF = 0.997 px) is within 1 % of this; the
difference is the occlusion bias above. So the fit is adequate **because D6's curve is a Gaussian by construction**
(section 2): the residual measures the digitisation, not the physics. Whether the true PSF of 200 keV electrons in
a 300-500 um Si sensor is Gaussian is not tested by D6: a single-erf ESF fit cannot represent a long-range tail
(D5 sec. 7, p. 52: lateral dispersion "for 200 keV ~190 um, i.e. larger than two pixels range"), which would show as
a low-frequency drop of the MTF and a lower MTF at the carrier relative to the mean. The Gaussian is the right
functional form for **reproducing D6** (it is D6's model, fully fixed by Table 1: MTF(omega) = 0.01^((omega/omega_N)^2)),
not a demonstrated form for a Medipix3 at 200 keV. For the UVic detector only a knife-edge measurement at the
threshold used (L9 section 6 item 7) can settle it. Finding M1.

## 4. Task 4 - fringe-contrast and phase-noise factors, B29, and the demo sampling

All numbers in this section are printed by `tools/review/e10_recompute.py` (saved output
`tools/review/e10_recompute_output.txt`, run with a Python that has `pymupdf`; without it the script falls back to the
frozen E10 traces and prints so).

**Fringe-contrast factor MTF(q_c)** (p pixels per fringe, omega = 2/p omega_N; section D of the output):

| p (px/fringe) | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|
| E10 digitised (58.3 keV curve, fully visible) | 0.117 | 0.298 | 0.463 | 0.587 | 0.741 | 0.826 | 0.877 | 0.928 |
| Gaussian fit (omega_0 = 0.4558) | 0.118 | 0.300 | 0.463 | 0.586 | 0.740 | 0.825 | 0.875 | 0.928 |
| Table 1 only (Gaussian through 0.01 at omega_N) | 0.129 | 0.316 | 0.479 | 0.599 | 0.750 | 0.832 | 0.880 | 0.931 |
| L9 (mean of navy and occluded red) | 0.112 | 0.288 | 0.453 | 0.576 | 0.728 | 0.815 | 0.864 | - |

L9's "0.29 at 4 px per fringe, 0.73 at 8" are CONFIRMED to within 0.01 (they are 0.30 and 0.74 on the unoccluded
curve; 0.27-0.35 and 0.72-0.77 from Table 1's rounding alone).

**Phase-noise formula (derivation, DERIVED_HERE, printed in section E).** With incident electrons
n(r) = nbar [1 + mu cos(2 pi q_c.r + phi)] (mu = incident, specimen-plane contrast), output counts of mean
g nbar [1 + mu MTF(q_c) cos(...)] and digital noise power spectrum NPS(q), the sideband estimate over M pixels has
<c> = g nbar mu MTF(q_c) e^{i phi}/2 and var(c) = NPS(q_c)/M (equal quadratures), so
sigma_phi = sqrt(2 NPS(q_c)/M) / (g nbar mu MTF(q_c)). Inserting D6 Eq. (3), DQE(q) = g^2 nbar MTF(q)^2 / NPS(q):

  **sigma_phi = sqrt(2) / (mu sqrt(N DQE(q_c)))**, N = M nbar incident electrons in the reconstruction area.

The MTF cancels: relative to a DQE = 1 detector at the same incident dose and contrast the factor is
**1/sqrt(DQE(q_c))**, not an "MTF-type" 1/(MTF sqrt(DQE)). L9's I3.2 and section 5 item 6 state exactly this and are
CONFIRMED. If instead the measured contrast mu_m = mu MTF(q_c) and measured counts N_c = g N are inserted into the
repository formula, the correction factor is sqrt(g NNPS(q_c)/DQE(0)) (0.72 sqrt(g) at 4 px/fringe on D6's curves),
because the noise is correlated (NNPS < 1); this is how an experimental phase-noise figure must be read.

| p | DQE(q_c) | 1/sqrt(DQE) (vs DQE = 1, the present code) | vs ideal square-pixel counter sqrt(sinc^2/DQE) | "MTF-type" 1/(MTF sqrt(DQE)) (wrong) |
|---|---|---|---|---|
| 4 | 0.170 (Table 1: 0.17) | **2.42** (Table 1 rounding: 2.39-2.46) | 2.18 | 8.14 |
| 5 | 0.300 | 1.82 | 1.71 | 3.94 |
| 6 | 0.400 | 1.58 | 1.51 | 2.69 |
| 8 | 0.540 | **1.36** | 1.33 | 1.84 |
| 10 | 0.612 | 1.28 | 1.26 | 1.55 |

L9's 2.4x and 1.36x are CONFIRMED. L9 calls the reference "an ideal counting detector"; the reference that gives
these numbers is a DQE = 1 (point-sampling) detector, i.e. the present `record_holograms`; a real square-pixel
counter already has DQE = sinc^2 (D6 p. 4), against which the factors are 2.18 and 1.33 (nit n2).

**Monte Carlo check (REPRODUCED, section F).** A 1-D compound-Poisson counting detector (multiplicities 1-4 with
P = 0.45/0.30/0.15/0.10, each count displaced by N(0, 0.95^2 px^2), 1024 px, 20 e/px, mu = 0.8; 3000 realisations per
case; fixed seeds): flat fields give g = 1.8998 counts/e and DQE(0) = 0.797 (64-px bins) / 0.792 (256-px bins) against
E[m]^2/E[m^2] = 0.785 (L9 I3.3 CONFIRMED); modulated fields give MTF(q_c) = 0.2956 / 0.7378 at 4 / 8 px/fringe
(D6-like by design) and DQE(q_c) = 0.146 / 0.585 from the measured NPS. Measured phase noise 0.03184 / 0.01608 rad
against sqrt(2)/(mu sqrt(N DQE)) = 0.03233 / 0.01615 rad (ratios 0.985 / 0.995, standard error about 1.3 %); the
"MTF-type" scaling would predict 0.109 / 0.022 rad (ratios 0.29 / 0.74), the naive formula with measured contrast
and counts 0.0303 / 0.0122 rad (ratios 1.05 / 1.32). Control: point-sampled Poisson (the present code) gives 0.01239 /
0.01224 rad against 0.01235 rad.

**Finite sideband mask (section G).** Averaging NNPS over the Hann disc of radius |q_c|/3 (2-D, isotropic D6 curves)
changes the effective DQE from 0.170 to 0.169 (4 px) and 0.540 to 0.542 (8 px): L9's carrier-frequency approximation
is adequate (its caveat can stay as a remark).

**B29 minimum visibility (section H).** The empty-hologram visibility used by the reconstruction is
V = 2|w_empty|/D (`reconstruction/sideband.py`, step 5), i.e. the measured contrast mu_inc MTF(q_c) (the centre band
has MTF(0) = 1). With V_min = 0.5:

| p | 4 | 5 | 6 | 8 | 10 | 12 | 16 | 17 |
|---|---|---|---|---|---|---|---|---|
| mu_inc needed | 1.68 (impossible) | 1.08 (impossible) | 0.85 | 0.675 | 0.605 | 0.570 | 0.539 | 0.534 |
| V with the B38 R1 plasmon factor 0.536 (mu_inc <= 0.536) | 0.160 FAIL | 0.248 FAIL | 0.315 FAIL | 0.397 FAIL | 0.443 FAIL | 0.470 FAIL | 0.497 FAIL | 0.502 pass |

L9's statement that B29 fails "always, at 4 px/fringe" is CONFIRMED (and also at 5 px/fringe). It is incomplete:
V >= 0.5 needs p >= 5.3 px/fringe even at mu_inc = 1, fails at 8 px/fringe for any incident contrast below 0.675, and,
with the repository's own plasmon-loss stand-in B38 (R1 fringe factor exp(-n/2) = 0.536), needs MTF >= 0.933, i.e.
**p >= 16.6 px/fringe**. L9's "Recommended carrier sampling >= 8 detector pixels per fringe" (section 4 table, item 5)
does not make B29 pass in the `plasmon_losses` variants. Finding M2.

**Must the demo configurations change? (sections H, I).**
* While the demos keep B24 (`mtf: none`, gain x Poisson), nothing fails: they are ideal-detector demos (DQE = 1,
  MTF = 1). Their fringe visibility is then 1/0.30 = 3.4 times, and their phase noise 1/2.42 of, what a
  D6-like Si Medipix3 would give at 4 px/fringe. This must be stated wherever demo holograms or phase-noise figures are
  shown (B24 wording).
* If a Medipix3-like MTF is adopted in the demos, B23 (4 px/fringe) and B29 (V_min = 0.5) must change together. To go
  to 8 px/fringe, halve the pixel (0.25 A: M = 6.0e5 at 15 um, 2.2e6 at 55 um; ROI [512, 128] -> [1024, 256] for the
  same field, 4x the pixels). Do NOT double the carrier spacing instead: at 4.0 A the |q_c|/3 mask is 0.0833 cycles/A,
  below the 3 mrad aperture band 0.1196 cycles/A (lambda = 0.025079 A), which breaks B28's rationale; the largest
  carrier keeping the band inside the mask is 2.787 A, so 8 px/fringe needs a pixel <= 0.348 A.
* The asymmetric sideband weighting (section J) is a further, unmentioned consequence: after division by the empty
  hologram the object sideband is multiplied by MTF(q_c + q)/MTF(q_c), which is 1.95 at q_c - R and 0.39 at q_c + R
  at 4 px/fringe (ratio 5.0 across the mask) and 1.18 / 0.79 at 8 px/fringe (ratio 1.5). Terrace-median phases far
  from edges are unaffected (the factor is 1 at the sideband centre), edge profiles and the effective resolution are
  not. Finding m7.

## 5. Task 5 - L9 section 5 (recommendations for `reflection_holo/optics/detector.py`) against the code

L9's description of the current code is accurate (E10 read `detector.py` in full and `hologram.apply_poisson_noise`):
pitch/M consistency check (relative 1e-9); band-limited DFT resampling of the complex wave to pixel centres (point
sampling); `MTFS = ("none",)` with `NotImplementedError` otherwise; `counts = gain * Poisson(dose * I / mean(I))`, so
mean g n and variance g^2 n, i.e. DQE = 1 at every frequency whatever the gain (E10 MC control, section 4); no readout
noise; drift not implemented. The hologram intensity is formed at the detector pixel centres from the resampled object
wave and the analytic reference, and the reconstruction checks that the sideband mask lies inside the Nyquist band
(`sideband.py` l. 311-313).

| L9 item | Logic | For a paper |
|---|---|---|
| 1 Declared detector identity (model/head, chips, sensor, mode, thresholds, depth, frame time, frames, flat field, masked pixels) | sound; metadata, cheap; the "comparison refuses without them" rule matches the existing stand-in refusal | NECESSARY as provenance of a comparison run (values are PROJECT_INPUT) |
| 2 Pitch 55 um and M calibrated at the Merlin plane | sound; no code change (the pitch/M mapping exists); numbers CONFIRMED (M = 2.2e6 for a 2.0 A carrier at 8 px; 1.1e6 for B23's 0.5 A pixel; 1/sin(16.1347 mrad) = 61.98) | NECESSARY for comparison (as PROJECT_INPUT); demo values optional |
| 3 ROI within the physical array; quad-chip gaps masked | sound | OPTIONAL unless the holograms span chip gaps (gap width UNVERIFIED) |
| 4 MTF on the recorded intensity, once | physically right (the detector responds to intensity; the coherent transfer is separate); D6's presampling MTF includes the pixel aperture (D6 p. 3: "The presampling forms also account for integration over the effective pixel area"), so no extra sinc. Two corrections: (i) the x2 oversampling is not needed for the mean response when the hologram band |q_c| + band lies below the detector Nyquist frequency (then filtering the DFT of the pixel-centre samples by MTF(q) is exact up to the no-wrap padding); it is needed only for sub-pixel cluster positions in item 5; (ii) items 4 and 5 are ALTERNATIVE ways to produce the mean blur: electrons of item 5 must be drawn from the unfiltered intensity, or the MTF is applied twice (finding m8) | NECESSARY: without it the simulated visibility is 3.4x too high at 4 px/fringe (1.35x at 8), the B29 test is meaningless, and the asymmetric sideband weighting (section 4) is missing |
| 5 Compound-Poisson counting (clusters, g = E[m], DQE(0) = E[m]^2/E[m^2], correlated noise) | sound (E10 MC: DQE(0) and the phase-noise law reproduced). The NNPS targets quoted (0.87/0.78/0.54/0.39 at 0.2/0.25/0.4/0.5 omega_N) inherit the occlusion bias; E10 gets 0.89/0.81/0.57/0.42; the uncertainty of a derived NNPS is about +-0.04 at 0.5 omega_N (finding m6) | NECESSARY in its second-order form (noise with the right NPS at the carrier, which sets sigma_phi: x2.42 at 4 px); the full cluster simulation is OPTIONAL except in the few-counts-per-pixel regime (the demo dose is 500 e/px) |
| 6 Phase-noise bookkeeping sigma_phi = sqrt(2)/(mu sqrt(N DQE(q_c))) | CONFIRMED analytically and by MC | NECESSARY (every reported phase-noise figure and the 3-sigma rules of B29 depend on it) |
| 7 Readout noise "none" | CONFIRMED by D1 ("virtually zero readout noise") and D7 ("noiseless operation by the setting of an appropriate threshold for counting") | no change |
| 8 Frames and counter caps (63, 4095, 16,777,215) | sound; at 500 e/px per hologram and about 2 counts/e (E10 MC g = 1.90 for a D6-like model; D6 gives no g at 200 keV) a single 12-bit frame would not overflow | OPTIONAL (a refusal check); drift per frame is a separate NOT IMPLEMENTED item |
| 9 Fixed-pattern gain map | sound; a static map cancels in the empty-hologram division | OPTIONAL |
| 10 SPM, low threshold as the default | a declaration; D6's CSM evidence is at omega_N and DQE(0) only | NECESSARY to declare (PROJECT_INPUT) |
| 11 Tests (knife edge, flat field, fringe contrast, phase noise, ROI and overflow refusals) | sound | NECESSARY for whatever of items 4-6 is implemented |

## 6. Task 6 - does the energy filter make item 21 feasible? (what the sources say, and nothing more)

The sources state that the instrument has an energy-loss spectrometer and an imaging energy filter: U1 "Electron
energy loss spectrometer." and "Imaging energy filter (Gatan Quantum)."; U6 "the Gatan electron energy loss
spectrometer (EELS) and Gatan Imaging Filter (GIF) is available"; U7 "EELS (Gatan)"; U9 "EELS/EFTEM" and "equipped
for holography, EDS, and GIF"; U10 "energy filtered imaging and electron energy loss spectroscopy"; U5 slide 5
"EELS + GIF". Energy-filtered holography appears only as an intention: U3 p. 2 (future tense) "Energy-filtered
electron holography, which combines electron holography with the imaging energy filter (GIF) will make it possible to
characterize the coherence properties of surface plasmons and surface phonons"; U4 slide 6 "Necessary for
energy-filtered imaging (GIF) and energy-filtered holography"; U4 slide 16 "Enables lensless, double energy-filtered
lattice imaging".

No source read by L9 or E10 (i) reports EELS or energy filtering of a reflected (RHEED-geometry) beam on this
instrument, (ii) reports an energy-filtered hologram recorded on it, (iii) states where the Merlin sits relative to the
filter (before it, e.g. above the screen as in D5/D6's mounts, or after it), so whether energy-filtered holograms can be
recorded on the Merlin is not stated, or (iv) gives the filter's slit widths or energy resolution at 200 kV (the only
resolution figure is "0.32ev rez" at 60 kV, U5 slide 6). The HF-3300 family article H1 (not UVic) states that the
HF-3300 "is equipped with electron energy filter [GIF (Gatan Imaging Filter)] and the biprism system".

Therefore the sources establish that the hardware needed to attempt the item-21 measurement (an energy-filtered EELS
of the specular beam; holograms with and without the filter) is listed for this microscope; they do not establish that
either measurement is feasible in the reflection geometry or with the Merlin. L9's "the requested energy-filtered
measurement of the specular beam (docs/06 item 21) is instrumentally possible in principle" (section 1.3) is labelled
DERIVED_HERE but reads as a feasibility statement (finding m5). Proposed wording: "The facility lists an EELS
spectrometer and a Gatan Quantum imaging filter (U1, U6, U10). No source describes EELS or energy filtering of a
reflected beam, or an energy-filtered hologram recorded on this instrument (U3 and U4 describe energy-filtered
holography as planned), or the position of the Merlin relative to the filter. Whether item 21 can be measured is for
Ali to confirm."

## 7. Task 7 - consistency with docs/06 and model_assumptions; statements that must change

No L9 value contradicts a value in `docs/06_project_inputs_required.md` or `docs/model_assumptions.md`; the changes
below follow from what L9 adds (and from sections 4-6 above). Proposed wording is for the orchestrator, who owns those
files.

| Where | Current text (quoted) | Must change? | Proposed change |
|---|---|---|---|
| docs/06 section A header | "Its published specifications (source, biprisms, energy spread, energy filter if any) are being sourced (report L9)." | YES (stale once L9 is adopted) | "Published facility specifications (L9, reviewed by E10): HF-3300V STEHM, cold FEG, 60/200/300 kV, four biprisms (one condenser-side, three image-side), CEOS B-COR and SC-COR correctors, EELS and a Gatan Quantum imaging filter, a Merlin (Medipix3) detector. No 200 kV energy spread, source size, convergence, biprism or detector configuration is published." |
| docs/06 item 2 | "Energy spread (FWHM, eV) and effective source size ... (Energy spread is a minor effect: below 0.004 rad ... at 0.7 eV.)" | no (consistent) | optional annotation: "Published for this instrument only at 60 kV: 0.32-0.34 eV zero-loss FWHM (2013; L9 U5 slide 6); the 0.3-0.7 eV bracket is an ASSUMPTION." |
| docs/06 item 5 | "(blocking) Image pixel size at the detector (nm/pixel, both axes) and the magnification for holograms." | no (consistent) | add: "If recorded on the Merlin: 55 um pitch; calibrate M at the Merlin plane (the screen magnification does not apply); state the pixels per carrier fringe, which set the detector-attenuated contrast." |
| docs/06 item 6 | "Detector: type, MTF or its published parameters, gain, dose per hologram ... its published pixel pitch, MTF/DQE at 200 kV and counting mode are being sourced (report L9)." | YES | "Detector: model and head (e.g. "Merlin 1R", the name used by D7 and D14), chip count, sensor material and thickness, SPM/CSM, threshold(s) in keV, counter depth, frame time and frames per hologram, flat-field correction, masked pixels; MTF AND DQE (or NPS) at 200 kV at the threshold used (a knife edge and a flat-field series on this detector replace the published stand-in); counts per electron at that threshold (not a 'gain': one 200 keV electron is counted in several pixels); dose per hologram in incident electrons; exposure; drift. Published stand-in (not the UVic device): Paton et al. 2021, Si Medipix3, 200 keV, SPM low threshold, MTF(omega_N) 0.01, DQE(0) 0.80, DQE(0.5 omega_N) 0.17 (Table 1, p. 5)." |
| docs/06 item 15 | "(blocking) Trajectory of the reference beam at the specimen plane ..." | add | "... and which of the instrument's four biprisms (one condenser-side, three image-side; L9 U1) were used." |
| docs/06 item 16 | "... measured carrier fringe spacing (in image pixels and in specimen nanometres, stating which axis) and fringe contrast on an empty or flat-surface hologram." | YES (interpretation) | add: "The contrast measured on the detector includes the detector MTF at the carrier (about 0.30 at 4 px/fringe and 0.74 at 8 px/fringe for the Paton et al. device); the simulation must be compared after its detector model, not before." |
| docs/06 items 17, 18 | - | no | - |
| docs/06 item 21 (working tree of 2026-09-24, already edited after L9) | "REQUESTED MEASUREMENT (the UVic HF-3300V has an imaging energy filter, report L9): an energy-filtered EELS ... Also useful: fringe visibility of a hologram recorded with and without an energy filter." | the new parenthetical is supported (U1 "Imaging energy filter (Gatan Quantum)."); add the limit | append: "No source states that EELS of a reflected beam, or energy-filtered holography with the Merlin, has been done on this instrument, nor where the Merlin sits relative to the filter (E10 section 6); feasibility is for Ali to confirm." |
| model_assumptions B23 | "Demo detector: pitch 15 um, magnification 3.0e5, image pixel 0.05 nm ... Samples the demo carrier fringes with 4 pixels per fringe" | YES if any detector MTF is adopted; otherwise add a sentence | either keep and add "ideal detector; 15 um is not the Merlin's 55 um (the specimen-referred pixel is what matters)", or change to a 0.025 nm pixel (8 px/fringe at the 2.0 A carrier; ROI x2 per axis). Never reach 8 px/fringe by doubling the carrier (section 4) |
| model_assumptions B24 | "gain 1 count per electron, 500 electrons per pixel per hologram, Poisson noise only, no MTF, no readout noise, no drift" | YES (add) | add: "An ideal detector (MTF = 1, DQE = 1): for a Si Medipix3 at 200 keV (Paton et al. 2021) the fringe visibility would be lower by MTF(q_c) (0.30 at 4 px/fringe) and the phase noise higher by 1/sqrt(DQE(q_c)) (2.42 at 4 px/fringe)." |
| model_assumptions B28 | "carrier fringe spacing 2.0 A ... the fringe spacing keeps the object band inside the |q_c|/3 sideband mask" | no, provided the sampling is changed through the pixel (B23), not the carrier | - |
| model_assumptions B29 | "division by the empty hologram with minimum visibility 0.5" | YES, together with any detector MTF | "V_min is a detector-plane visibility; with a detector MTF it must be set from the expected mu_inc MTF(q_c): V_min = 0.5 fails for every contrast at <= 5 px/fringe, needs mu_inc >= 0.675 at 8 px/fringe, and with the B38 loss factor needs >= 17 px/fringe." |
| model_assumptions B38 | "With R2 and B39 the fringe factor falls below the 0.5 minimum visibility of the demo processing B29" | add | "... and, with a Medipix3-like detector MTF, so does R1 below 17 px/fringe." |
| docs/03 section 6 (and C report 7.4) | "Phase noise of the sideband estimate: `sigma_phi = sqrt(2)/(mu sqrt(N))` with fringe contrast `mu` and `N` counts in the reconstruction aperture area." | YES (qualify) | "... for an ideal (DQE = 1) detector. For a detector with DQE(q): sigma_phi = sqrt(2)/(mu sqrt(N DQE(q_c))) with mu the incident contrast and N the incident electrons (E10, reproduced by Monte Carlo); with the measured contrast and counts multiply by sqrt(g NNPS(q_c)/DQE(0))." |

## 8. Findings, ranked

No BLOCKER was found: every sourced UVic and D6 value checked is at its locator, every DOI resolves, and L9's derived
factors and phase-noise law reproduce.

### MAJOR

**M1 - The Gaussian MTF is D6's own model, not an empirical finding about the detector (L9 sections 3.3, 5 item 4,
parameter table row 6).**
Quoted: "Gaussian fit (DERIVED_HERE, `l9/fit_mtf.py`): MTF(omega) = exp(-(omega/omega_0)^2) with omega_0 = 0.452
omega_N, i.e. q_0 = 0.226 cycles/pixel, reproduces the digitised curve within 0.01 from 0.15 to 0.85 omega_N; it is
equivalent to a Gaussian presampling PSF of sigma = 0.997 pixel = 54.8 um".
Evidence: D6 sec. 3, p. 3, Eq. (1): every ESF is fitted with a single error function and the MTF is the Fourier
transform of its derivative, i.e. a Gaussian by construction; the DQE curves use this MTF (Eq. (6), p. 4). E10: a free
exponent fit returns n = 2.000 and rms 0.0028 (digitisation noise); Table 1 alone fixes the curve,
MTF(omega) = 0.01^((omega/omega_N)^2) (0.316 at 4 px/fringe, 0.750 at 8). A long-range PSF tail (D5 sec. 7, p. 52:
"~190 um" lateral dispersion at 200 keV) cannot appear in such a curve.
Proposed wording: "D6 fitted every edge-spread function with a single error function (D6 sec. 3, Eq. (1), p. 3), so
its 200 keV Si MTF is a Gaussian by construction; our fit recovers D6's width (Gaussian PSF s.d. 0.99 px = 54 um;
erf width 1.40 px) and does not show that the PSF of 200 keV electrons in Si is Gaussian. A long-range tail would
lower the MTF at low frequency and is not represented. The Gaussian is a stand-in for D6's device only (ASSUMPTION);
a knife-edge measurement on the UVic detector at the threshold used replaces it."

**M2 - The minimum-sampling recommendation (">= 8 detector pixels per fringe") is not derived from a criterion and does
not make B29 pass; the B29 analysis stops at 4 px/fringe (L9 section 4 table, row item 5; section 5 item 6).**
Quoted: "Recommended carrier sampling | >= 8 detector pixels per fringe (MTF >= 0.73, DQE(q_c) >= 0.54 on Si at 200
keV); 4 px/fringe gives MTF 0.29" and "the B29 minimum visibility of 0.5 would be failed by a specimen-plane contrast
below 0.5/0.29 = 1.7, i.e. always, at 4 px/fringe".
Evidence (e10_recompute sections H, I): V = mu_inc MTF(q_c) >= 0.5 fails for every contrast at 4 and 5 px/fringe,
needs mu_inc >= 0.675 at 8 px/fringe, and with the repository's B38 R1 plasmon factor 0.536 needs MTF >= 0.933, i.e.
p >= 16.6 px/fringe (V = 0.397 at 8 px). At mu_inc = 1 the V criterion alone needs p >= 5.3. Reaching 8 px/fringe in
the demo requires a 0.25 A pixel (ROI 4x) because a 4.0 A carrier would put the 3 mrad band (0.1196 cycles/A) outside
the |q_c|/3 mask (0.0833). Item 5 is PROJECT_INPUT: comparison runs use Ali's sampling, not a recommendation.
Proposed wording: remove the row from the parameter table and state in section 3.4/5: "The detector-plane visibility
is mu_inc MTF(q_c). With B29's V_min = 0.5 the demo needs >= 6 px/fringe at mu_inc = 1 and >= 17 px/fringe with the
B38 loss factor 0.536; V_min must be re-derived together with any detector MTF (orchestrator). For comparison runs the
sampling is Ali's (items 5, 16)."

### MINOR

* **m1 - H5 treated as the UVic instrument.** Quoted (section 2.2): "This is the only peer-reviewed methods text read
  here that names the UVic instrument; it confirms the B-COR image corrector, U5 slide 5." Evidence: H5 Methods
  (PMC7910301) names "a Hitachi HF-3300V with CEOS BCOR imaging aberration corrector, operated at 60 kV" and no
  location; "Victoria" occurs only in the affiliations. The parameter-table rows "(lens)" and "(22, drift)" carry H5's
  corrector and "< 7 pm/sec" as UVic SECTION_READ. Proposed: "H5 names a Hitachi HF-3300V without a location; that it
  is the UVic instrument is an inference (U1 names the UVic microscope HF-3300V; H5 has a UVic co-author)."
* **m2 - U10's link target not recorded.** Quoted (section 1.3): "The page does not say "MerlinEM"". Evidence: the
  U10 HTML links "Merlin" to `https://quantumdetectors.com/n/products/merlinem/`. Proposed addition to I1.2: "U10
  links the word Merlin to the Quantum Detectors MerlinEM product page (supporting the product family; head variant,
  chip count and sensor remain PROJECT_INPUT)."
* **m3 - U10 dating.** Quoted: "(page footer "(c) 2017 University of Victoria"; the page carries no date of last
  change)"; table row 6 "page undated (footer 2017)"; bib note "footer 2017, no date of change". Evidence: the site's
  WordPress REST record of the page: created 2020-01-20, modified 2023-01-04 (retrieved 2026-09-24). Proposed:
  "page created 2020-01-20, last modified 2023-01-04 (site REST record); the 2017 footer is not a content date".
* **m4 - Provenance of the D6 copy and of the scripts.** Quoted: README "Glasgow accepted-manuscript PDF"; script
  `d = pymupdf.open('pdf/Paton2021_gla_AAM.pdf')`; report and docstring "sha256 555e925c...0e5"; report "sha256
  d8a8e591...a043" (U4); report section 5 "Numbers below are from `l9/l9_numbers.py` (output `l9/l9_numbers.out`)".
  Evidence: the Glasgow record labels 240505.pdf "Published Version" (L9's report is right, the README is not); the
  file hashes are 555e925c628ba9eb...6e80fc95c6 and d8a8e591...a24db043 (E10's and L9's copies byte-identical, so the
  printed suffixes are typos); `pymupdf` is absent from `venv/`; the committed scripts are in `tools/lit/l9/`.
  Proposed: README "Glasgow copy of the published version (CC BY; eprints.gla.ac.uk/240505, 'Published Version');
  needs pymupdf (not in venv/)"; rename to `Paton2021_gla_published.pdf`; print full hashes; cite `tools/lit/l9/`
  paths in sections 3.3, 5 and 8.
* **m5 - Energy-filter feasibility.** Quoted (section 1.3): "the requested energy-filtered measurement of the specular
  beam (docs/06 item 21) is instrumentally possible in principle". Evidence and proposed wording: section 6 above.
* **m6 - Occlusion bias of the "mean of the two coincident curves".** Quoted: "MTF 0.29 ... p = 8: 0.73" (I3.1),
  "omega_0 = 0.452 omega_N", "sigma = 0.997 pixel", "NNPS = ... 0.87 / 0.78 / 0.54 / 0.39". Evidence: the 12.4 keV MTF
  line is hidden under the 58.3 keV line; on the visible line E10 gets 0.298 and 0.741, omega_0 = 0.456, PSF s.d.
  0.988 px, NNPS 0.89 / 0.81 / 0.57 / 0.42 (uncertainty about +-0.04 at 0.5 omega_N). Proposed: "MTF(q_c) = 0.30 at
  4 px/fringe (0.27-0.35 from Table 1's rounding) and 0.74 at 8 px/fringe (0.72-0.77), from the 58.3 keV curve, which
  is drawn over the coincident 12.4 keV curve"; give NNPS to two figures with +-0.04.
* **m7 - Asymmetric sideband weighting not mentioned.** Quoted (section 5 item 4): "The detector responds to intensity,
  so the MTF belongs after hologram formation". Evidence (e10_recompute section J): after division by the empty
  hologram the object sideband is weighted by MTF(q_c + q)/MTF(q_c): 1.95 to 0.39 across the |q_c|/3 mask at 4
  px/fringe, 1.18 to 0.79 at 8. Proposed addition: "The MTF also weights the object sideband asymmetrically
  (MTF(q_c + q)/MTF(q_c), a factor 5.0 across the mask at 4 px/fringe, 1.5 at 8); division by the empty hologram
  removes only MTF(q_c). Terrace phases far from edges are unaffected; edge profiles and resolution are not."
* **m8 - Items 4 and 5 must be alternatives; oversampling only for clusters.** Quoted (item 4): "Form the hologram
  intensity on a grid oversampled at least x2 relative to the detector pixels"; (item 5) "each electron adds a random
  cluster of counts whose mean footprint is the PSF of item 4". Evidence: with the hologram band |q_c| + band below the
  detector Nyquist frequency (checked by `sideband.py` l. 311-313 for the mask), filtering the DFT of the pixel-centre
  samples is exact; applying item 4's filter and then item 5's clusters to the same intensity would give MTF^2.
  Proposed: "Either filter the intensity by the MTF and add noise with the prescribed NPS (item 4 + the second-order
  form of item 5), or draw electrons from the UNFILTERED intensity and spread them with the cluster model (item 5
  alone); oversample only for the latter."

### NIT

* **n1** U5 slide 6 values are spectrometer zero-loss widths ("0.32ev rez"), upper bounds on the source spread.
* **n2** "relative to an ideal counting detector" -> "relative to a DQE = 1 point-sampling detector (the present
  code)"; against an ideal square-pixel counter (DQE = sinc^2, D6 p. 4) the factors are 2.18 and 1.33.
* **n3** I2.1 "the upper end 0.7 eV is a safe bracket" -> "a bracket (ASSUMPTION)": H1's 0.7 eV is at 100 uA with the
  voltage not stated, and no UVic emission current at 200 kV is published (the step phase is insensitive anyway).
* **n4** D6 sec. 3 p. 4 paraphrase "the maximum energy deposited in one pixel is well below the primary energy": D6's
  words are "the maximum threshold at which it was possible to fit the knife-edge data with Eq. (1) is lower than the
  counting threshold that corresponds to the primary electron energy, substantially so for electrons with energies
  >=120 keV".
* **n5** Hashes of D1, D2, D8, D9 cannot be re-obtained (dynamic pages, download-stamped IOP PDFs); say so where a
  hash is given.
* **n6** "MerlinEM 1R" (section 5 item 1; section 6 item 1 has "MerlinEM with head variant 1R, 4R, 4S") is not a
  name found in the sources: D7 writes "Merlin 1R retractable Medipix3 mount" and D14's keywords list "MerlinEM;
  Merlin 4S; Merlin 4R; Merlin 1R". Write "Merlin 1R".

## 9. Verdict table

| L9 item | Verdict |
|---|---|
| Section 0 access log | CONFIRMED where re-tested (uvic.ca, Glasgow, arXiv, IOP, QD, mmc, Crossref, Europe PMC: HTTP 200) |
| 1.1-1.3 UVic facts (U1-U10) | CONFIRMED verbatim at every locator; add U10 link target and dates (m2, m3); energy-filter consequence re-worded (m5) |
| 1.4 inferences I1.1-I1.5 | CONFIRMED as labelled inferences (I1.4 correctly refuses to infer the reference trajectory) |
| 2.1-2.2 HF-3300 family (H1, H2, H4, H5, H6, H11, H12) | CONFIRMED verbatim (H1 Table 1 re-rendered at 220 dpi); H5-as-UVic is an inference (m1) |
| 2.3 not found | CONFIRMED as a search statement |
| 2.4 I2.1-I2.2 | CONFIRMED with n3 |
| 3.1-3.2 detector sources D1-D14 | CONFIRMED verbatim (D1, D2, D5, D6, D7, D8, D9, D10, D12, D13, D14 re-read at the locators) |
| 3.2 D6 Table 1 and p. 9 statements | CONFIRMED |
| 3.2 Si thickness 500 vs 300 um | CONFIRMED: sources disagree; UNRESOLVED stands |
| 3.3 digitisation | REPRODUCED (byte-identical rerun; independent E10 digitisation within 0.004) |
| 3.3 Gaussian fit | numerically CONFIRMED (omega_0 0.456 vs 0.452); interpretation CORRECTED (M1) |
| 3.4 I3.1 fringe factors | CONFIRMED within 0.01 (0.30 / 0.74 on the unoccluded curve; m6) |
| 3.4 I3.2 phase-noise law and factors 2.42 / 1.36 | CONFIRMED analytically and REPRODUCED by Monte Carlo (ratio 0.985 / 0.995) |
| 3.4 I3.3 compound Poisson, DQE(0) = E[m]^2/E[m^2] | REPRODUCED by Monte Carlo (0.792 vs 0.785) |
| 3.4 I3.4-I3.7 | CONFIRMED as labelled inferences |
| 4 parameter table | CONFIRMED except the "Recommended carrier sampling" row (M2) and the H5/U10 rows (m1, m3) |
| 5 detector.py recommendations | logic sound; necessity graded in section 5 above; m7, m8 |
| 6-7 open items and upload list | CONFIRMED (no personal data recorded) |
| 8 scope statement | CONFIRMED except script paths (m4) |
| `L9_new_refs.bib` (25 entries) | CONFIRMED against Crossref for all 18 DOI entries (titles, first authors, author counts, volumes, issues, pages/article numbers, years); SATO2008HITACHIREVIEW (no DOI) against the PDF metadata ("HITACHI REVIEW Volume 57 Number 3 June 2008") and running heads (pp. 133, 135); the 6 @misc entries match their pages; the header's list of entries already in `docs/references.bib` (P42-P47, dfh098) is correct; only the U10 note needs the dates (m3) |
| `tools/lit/l9/` scripts | REPRODUCED; README provenance wrong (m4) |

## 10. Values E10 CONFIRMS (quotable, with locator)

* UVic instrument: "Hitachi HF-3300V STEHM", cold-field-emission source, "60 keV, 200 keV, and 300 keV acceleration
  voltage", four biprisms ("One above specimen, and three below the specimen with magnification between lower biprisms
  equal to one"), "Imaging energy filter (Gatan Quantum)" and "Electron energy loss spectrometer" (all U1,
  `https://www.uvic.ca/research/advancedmicroscopy/about/microscopes/stehm/index.php`, retrieved 2026-09-24,
  SECTION_READ); CEOS B-COR (TEM) and CEOS SC-COR (STEM) correctors (U5 slide 5, 2013); "fitted with a Merlin
  (Medipix3) high speed pixelated direct-electron detector" (U10, page created 2020-01-20, modified 2023-01-04).
* Energy spread: 0.32 eV (0.1 s) and 0.34 eV (1.0 s) zero-loss FWHM at 60 kV, 2013 (U5 slide 6); no 200 kV value
  published. Brightness "6x10e13 A/m2 sr" as printed, conditions not stated (U1).
* Medipix3: 256 x 256 pixels of 55 um; Nyquist 9.1 lp/mm (D5 sec. 2, p. 45); counters 1/6/12/24 bit, readout 70.8 us /
  412 us / 822 us / 1.64 ms at 120 MHz (D7 sec. II); continuous read-write dead-time free (D8 sec. 3); "virtually zero
  readout noise" (D1).
* Paton et al. 2021 (D6) Table 1, p. 5, 200 keV, Si, SPM low threshold (12.4 keV): MTF(omega_N) = 0.01,
  DQE(0) = 0.80, DQE(0.5 omega_N) = 0.17, DQE(omega_N) = 0.00; CSM "never exceeds 0.00" in DQE(omega_N) (p. 9); the
  D6 MTF is a single-erf (Gaussian) model (sec. 3, Eq. (1), p. 3). Si thickness: 500 um (D6 p. 2 wording) or 300 um
  (D12 sec. 4.1), unresolved.
* Derived from D6 (DERIVED_HERE, `tools/review/e10_recompute.py`): fringe-contrast factor 0.30 at 4 px/fringe
  (Table-1 range 0.27-0.35) and 0.74 at 8 px/fringe (0.72-0.77); Gaussian PSF s.d. 0.99 px (54 um).
* Phase noise with a detector: sigma_phi = sqrt(2)/(mu sqrt(N DQE(q_c))) (mu incident contrast, N incident electrons);
  factor relative to a DQE = 1 detector 2.42 at 4 px/fringe (2.39-2.46 from Table 1) and 1.36 at 8 px/fringe
  (REPRODUCED by Monte Carlo to 1.5 %); the Hann |q_c|/3 mask changes these by < 1 %.
* B29 with a D6-like MTF: V_min = 0.5 unreachable at 4-5 px/fringe; needs mu_inc >= 0.675 at 8 px/fringe; with the
  B38 factor 0.536 needs >= 17 px/fringe.
* Demo arithmetic: 55 um pitch and a 0.5 A pixel need M = 1.1e6; a 2.0 A carrier at 8 px/fringe needs a 0.25 A pixel
  (M = 2.2e6 at 55 um); 1/sin(16.1347 mrad) = 61.98.

## 11. What must NOT be adopted yet

1. The Gaussian MTF (q_0 = 0.226-0.228 cycles/px) as a model of the UVic detector: only as a labelled stand-in of D6's
   device (ASSUMPTION), with M1's wording.
2. ">= 8 px/fringe" as the demo minimum, or any detector MTF in the demos, without re-deriving B29's V_min together
   with it (M2); and never by doubling the carrier spacing (B28).
3. The NNPS/DQE curve targets beyond two significant figures (m6).
4. Any configuration of the UVic Merlin (head variant, chip count, sensor thickness, threshold, SPM/CSM, counts per
   electron): PROJECT_INPUT (U10's link supports the MerlinEM family only).
5. The feasibility of docs/06 item 21 on this instrument (section 6).
6. The 0.3-0.7 eV energy-spread bracket as anything but an ASSUMPTION; the U1 brightness as a model parameter.
7. H5's drift and corrector as UVic facts (m1).
8. The CSM "no benefit" conclusion as a statement at the carrier frequencies (D6 shows it at omega_N and DQE(0) only).

