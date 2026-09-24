# Paper readiness: what must be true before a simulation result is citable

Status: revision 1, 2026-09-24 (Phase 4); row 2.6 updated and row 2.11 added after audits A9-A10 (review E11 n10). Maintained by the orchestrator; every entry points to the
report, test or script that establishes it. A result enters a paper only when every row it depends on
is DONE (or its gap is stated in the paper as a limitation with its size). Numbers are not repeated
here; they are in the cited reports and scripts. Labels as in `docs/physics_conventions.md` and the
instruction file.

Legend: DONE (reviewed), PARTIAL, OPEN (work on our side), NEEDS ALI (only the laboratory can supply
it), NEEDS UPLOAD (a closed source must be read).

## 1. Inputs that must be real (docs/06)

| # | Input | Why it matters | Status | Where |
|---|---|---|---|---|
| 1.1 | Glancing angle and its calibration (item 7) | Sets the height scale; a measured angle removes the mean inner potential from heights | NEEDS ALI | docs/06 item 7; model_assumptions B1 |
| 1.2 | Beam azimuth and its accuracy (item 8) | Exact [100] makes bulk-terminated a/4 steps geometric; (0,0,8) is then a four-beam case | NEEDS ALI | B4, B20; H2 section 2.2 |
| 1.3 | Convergence semi-angle and source profile (item 3) | Phase spread; with an R1 reference it confines the coherent field | NEEDS ALI (ensemble implemented, E3) | B10, B40; E3 |
| 1.4 | Aperture, detector, magnification, dose (items 4-6) | Resolution, noise, which beam is imaged | PARTLY SUPPLIED (2026-09-24: Hitachi HF-3300 at UVic; Quantum Detectors Medipix-based detector); NEEDS ALI: aperture, magnification, dose, detector mode | docs/06 A; L9 |
| 1.5 | Miscut and terrace widths (item 11) | Fixes the across-beam cell size and whether a converged measuring window exists | NEEDS ALI | H2/H7 sizing, `tools/hpc/supercell_sizing_output.txt` |
| 1.6 | Sample preparation, vacuum, anneal; witness cross-section (item 12) | Decides the surface model (UHV-clean vs oxide/amorphous overlayer) | PARTLY SUPPLIED (2026-09-24: air-exposed, O2/Ar plasma clean about 10 min, so oxide-covered); still NEEDS ALI: milling parameters, plasma power, time to imaging, microscope vacuum, witness cross-section | B7; L7 section 6 |
| 1.7 | Reference-wave path, separation, fringe spacing (items 15-16) | R1 vs R2 changes the loss factor and the coherence limits | NEEDS ALI | B5, B38-B40; E3 |
| 1.8 | Processing choices (item 19) | Simulated and measured holograms must share one code path | NEEDS ALI | B29 |
| 1.9 | Mean inner potential (item 20) | Refraction and the working angle | NEEDS UPLOAD (Kruse 2006; Wu and Spiecker 2017) | B1; L6 section 3 |
| 1.10 | Absorption and inelastic losses (item 21) | Run-in length, reflected amplitude, fringe contrast | PARTIAL: TDS via frozen phonons (sourced); electronic losses a bracket; surface plasmons a transfer. NEEDS ALI: energy-filtered EELS of the specular beam | B6, B30, B38; L6, E6 |
| 1.11 | Specimen temperature (item 23) | Thermal displacement | NEEDS ALI (model implemented, B35) | B35, B36; E2 |
| 1.12 | Charging evidence (item 22) | A charging patch mimics topography | NEEDS ALI | B8 |

## 2. Physics the model must contain

| # | Physics | Status | Where |
|---|---|---|---|
| 2.1 | Dynamical many-beam reflection with a stated atomic potential | DONE (Kirkland IAM via abTEM; the IAM mean inner potential is a stated systematic) | M2, D3, B32 |
| 2.2 | Thermal vibration (frozen phonons, sourced amplitude) | DONE for the model (B35); ensemble size per result: OPEN (convergence criterion on the coherent average, SM13) | E2, A5, E6 m10 |
| 2.3 | Absorption without double counting | PARTIAL (rule fixed: frozen phonons or Bird-King, never both; electronic value bracketed) | B6, SM29 |
| 2.4 | Surface plasmons and partial coherence of loss electrons | DONE for the model (R1/R2 factors, noise); the value is a stand-in | E3, A5, B38, B39 |
| 2.5 | Surface reconstruction (Si(001) 2x1 family, flip-flop at room temperature) | DONE for the builder (sourced coordinates); effect on the step phase: OPEN (sensitivity study) | E2, A5, B3, B37 |
| 2.6 | Oxide or amorphous overlayer of an ion-milled surface | PARTIAL (continuum layer implemented in both engines, reports E4, X4, X5; audits A8, A9b, A10b: final for the B41 demo path; the comparison-run label policy is being fixed after A10b (X6); for a sub-layer thickness difference between terraces the atomistic and geometric engines disagree, so such atomistic cells are refused (B12); atomistic amorphous layer OPEN). REQUIRED (item 12: oxide-covered). Sourced ranges exist (L8 with E9: thickness 1-3 nm ASSUMPTION, inner potential 10.1-11.5 V measured and 10.34 V IAM, absorption 0 or 0.39-0.44 V, graded edge required); continuum layer implemented (E4, X4, X5); open atomistic a-SiO2 model exists (Erhard et al. 2024, CC BY 4.0). Only the conformal case converts to heights; a thickness difference between terraces biases heights by 0.53-0.58 A per A | B7, SM32, SM33; E9 |
| 2.7 | Convergent illumination (ensemble of directions) | DONE for the model; members runnable as cluster jobs | E3, A5, B40 |
| 2.8 | Monotonic (vicinal) staircase | OPEN (only up-down staircases are periodic) | H2 N6 |
| 2.9 | Microscope optics: biprism Fresnel fringes, drift, detector MTF, lens transfer | OPEN | docs/05 section 5 |
| 2.10 | Working angle from a simulated rocking curve at the actual azimuth | OPEN (flat-strip rocking curve on the cluster) | H2 section 7, N11 |
| 2.11 | Sensitivity below the surface (buried void, demo B42) | DEMO ONLY (report T3, analysis T4 and T5; audits A9a, A10a; A11 pending): in a 1499 A cell a void under a 5 A cap changes the vacuum-side beam; deeper caps need a longer cell (the signal surfaces far downstream), a dose model and convergence before any claim | B42; T3, T4, T5 |

## 3. Numerical convergence (each setting shown not to change the answer)

| # | Setting | Status | Where |
|---|---|---|---|
| 3.1 | Cell length along the beam (run-in) | PARTIAL: static and r = 0.1 phonon run-ins computed with the engine; r = 0.05 and r = 0 phonon run-ins OPEN (cluster) | H2, H5, H7 |
| 3.2 | Clean depth and bulk absorber | PARTIAL: >= 65 A reviewed minimum for null tests (E7); absorber reflects without physical absorption (P2) | P2, E7 |
| 3.3 | Pixel size | OPEN and decisive: at 0.13 A the absolute phase carries about -0.03 rad of band-limit error; the step phase must be shown converged in dx before a production pixel is fixed | E8 M3; docs/05 4.4 |
| 3.4 | Slice thickness | OPEN (flat-strip study, H2 run order 2e) | H2 section 12 |
| 3.5 | Lateral width / terrace width | OPEN (terrace-width study at [100], H2 run order 5) | H2, H7 |
| 3.6 | Frozen-phonon and flip-flop ensemble sizes | OPEN | SM13; E2 NOT RUN |
| 3.7 | Fixed-beam null test (translation covariance with the beam fixed) | OPEN: the gate before any step-phase run; redesigned study being fixed (A6 N-1, N-2) | docs/05 4.4; E1, A6 |
| 3.8 | GPU reproduces CPU | OPEN: first GPU run tonight (gpu-check, gpu-sanity) | H4b; `scripts/hpc/alliance/TONIGHT.md` |

## 4. Independent validation (docs/05 4.4)

| # | Check | Status | Where |
|---|---|---|---|
| 4.1 | Rung 1: refraction-only slab against the analytic result | DONE | M2 |
| 4.2 | Rung 2: Bragg-case reflection (amplitude and phase across the plateau) against an exact 1D solution | DONE (R2-A passes; fails for every deliberate engine break) | P2, E7, E1, A6 |
| 4.3 | Rung 3: null tests | PARTIAL: continuum null tests and the atomistic moved-beam translation pass; the atomistic fixed-beam check has NOT passed | M2, A6 S-1 |
| 4.4 | Independent dynamical solver (sim-trhepd-rheed), flat Si(001) | PARTIAL: with the solver's own potential the phase differs by a median of 0.014 rad ([100]) and 0.017 rad ([110]), more than 0.05 rad at five other angles (0.051-0.075 rad, |R|^2 0.0017-0.044) and 0.398 rad at [100] 15.0 mrad where |R|^2 is about 1e-5 (`tools/plots/phase4_figures_solver_output.txt`); not like-for-like along the beam; the amplitude tolerance has no power | S5, E8 |
| 4.5 | abTEM cross-check | OPEN | docs/05 4.4 |
| 4.6 | Reproduction of a published result | OPEN: Tanishiro 2003 (7 pi step phase, Si(111), 200 kV) is open and a candidate; Osakabe 1988 needs uploads | L7, E6; docs/07 |
| 4.7 | Lateral (in-plane) sign convention | OPEN (needs a surface without a two-fold axis along the normal) | E8 M4 |

## 5. Comparison with the experiment (docs/05 section 7)

| # | Item | Status |
|---|---|---|
| 5.1 | Experimental hologram loader and the identical processing path | OPEN |
| 5.2 | Uncertainty budget (angle, mean inner potential, noise, phonon spread, absorption bracket, pixel) | PARTIAL (height uncertainty with the correlated angle error exists, A3/S4; the other terms OPEN) |
| 5.3 | Simulation at the laboratory's measured conditions | NEEDS ALI (section 1) |

## 6. Reproducibility

| # | Item | Status |
|---|---|---|
| 6.1 | Provenance manifests (commit, diff hash, seeds, versions) | DONE |
| 6.2 | Every number in a document printed by a committed script | DONE for the reviewed documents; enforced at every revision |
| 6.3 | Cluster runs from a pinned, re-audited commit, results returned with checksums | DONE for the kit (H4b); first results pending |

## 7. The shortest path to a first citable result

1. Tonight: gpu-check and gpu-sanity (3.8), smoke, demo-gpu, torus on the pinned commit.
2. Our side: finish the null-test fixes (A6 N-1, N-2), then on the cluster: flat-strip rocking curve at
   [100] (2.10), pixel and slice convergence of the step phase (3.3, 3.4), the fixed-beam null test (3.7),
   phonon run-ins (3.1), terrace-width study (3.5).
3. From Ali: items 7, 8, 3, 11, 12, 21 (EELS), 23 and the reference arrangement (15, 16).
4. Then: production single steps at the measured conditions with an uncertainty budget (5.2), and the
   Tanishiro 2003 reproduction as the published benchmark (4.6).
