# R2: How the code works (the `reflection_holo` package), for Dr Arthur Blackburn

Status: FINAL. Agent R2, 2026-09-24. Repository state: branch `claude/electron-holography-orchestration-nakd7r`,
HEAD `2896522`; nothing but this file was written. Locators are `file:line` at that commit (paths under
`reflection_holo/` unless stated) or document rows (`B` = row of `docs/model_assumptions.md`, `docs/08 n.m` =
row of `docs/08_paper_readiness.md`). Evidence labels are the repository's own. Beam energy 200 keV throughout.

## 1. Purpose and measurand

The package simulates reflection-mode, dark-field, off-axis electron holography of atomic steps on Si(001)
(configuration CFG-B `si001_patterned` [docs/05:67]) and processes the simulated holograms with the same
reconstruction and height code that is meant for Ali's experimental holograms [docs/03:18-35]. The beam
energy is fixed at 200 keV and any other value is refused [constants.py:27; forward/multislice/physics.py:27-37].
The working condition is the specular (0,0,8) reflection, an ASSUMPTION (B17) standing in for PROJECT_INPUT
item 9. The measurand is the phase difference of the specular dark-field wave between two terraces,
Δφ = φ(upper) − φ(lower) = −(k_out − k_in)·R, which for the specular beam is −(4π/λ) h sin θ_ext with the
vacuum wavelength and the external glancing angle (DERIVED_HERE from translation covariance, exact far from
the riser for translation-related terraces [docs/03:60-69; docs/physics_conventions.md:19]). The height is
h = −Δφ λ / (2π (sin θ_in + sin θ_out)). Because the wrap period λ/(2 sin θ_ext) is smaller than an atomic
step [docs/03:143-146], branch resolution is part of the measurement.

## 2. The chain, stage by stage

The order is fixed in `pipeline/run.py:3-32`. For each stage: physics, equation as implemented, inputs, refusals.

**2.1 Structure builder.** Terraces are truncations of ONE diamond lattice with (001) layers at x = l a/4
[structure/si001.py:1-8]. An a/2 step joins terraces related by a lattice translation; an a/4 step joins
terraces related only by the 4₁/4₃ screws and the <100> d-glides, and the top-layer back-bond axis rotates by
90° [si001.py:11-21]. These relations are measured on the built atoms, not assumed: `find_terrace_relations`
searches rotations times a/8-grid translations [si001.py:23-25, 306], `classify_relation` demands a translation
for a/2 and a screw (and no translation) for a/4 [si001.py:353-380], and `b4_statement` records whether the
dynamical phase cancels (B4): for a/2 far from the riser; for a/4 only at an exact <100> azimuth with the incidence-plane
glide found, specular beam, bulk termination; never at <110>, where the residual δ is unknown (open question 3)
[si001.py:383-416]. Options: bulk termination (ASSUMPTION B3, default); the p(2×1)s, p(2×1)a, p(2×2), c(4×2)
geometries of [RAMSTAD1995] (SECTION_READ; their use at room temperature is an ASSUMPTION) and the flip-flop
ensemble (ASSUMPTION B37, a model choice) [structure/reconstruction.py:98-140]; a half-torus trench or ridge
(B33, B34) and a buried torus void under an intact cap (B42) [structure/shapes.py:8-36, 74-91, 161-181]; a
continuum oxide grown from the crystal, with consumed-Si fraction f = (ρ_ox/M_SiO2)/(ρ_Si/M_Si), interface at
H_s − f t, top at H_s + (1 − f) t, and the atomistic crystal losing the nearest whole number of layers
(count DERIVED_HERE) [structure/oxide.py:13-27, 764-773]; the frozen-phonon amplitude B(T) of [HEACOCK21]
(SECTION_READ, B35) [structure/thermal.py:16, 46-51]. Inputs: azimuth (item 8; demo B20, exact [100]),
staircase (item 11; demo B25), features (item 13; demo B27, B33, B34, B42), surface (item 12; demo B26 clean
or B41 oxide, model row B43), temperature (item 23; demo B36). Refuses: steps other than a/4 or a/2, and
staircases that do not close under the periodic boundary (a vicinal cell is NOT IMPLEMENTED)
[si001.py:195-226]; reconstructions on the half-torus [structure/features.py:717-741]; a static buckled
reconstruction without an explicit buckling registry, which is labelled "not physics"
[reconstruction.py:123-133; B3]; oxide edges graded over less than 0.5 Å, consumed-layer counts near a
rounding boundary unless acknowledged, and count intervals of more than two counts [oxide.py:28-48, 117-131];
temperatures outside the B35 range [thermal.py:50-51].

**2.2 Geometric engine.** Every lit surface point reflects with one declared amplitude |A| and phase
−(k_out − k_in)·R_k, with R_k summed from the step translations measured on the atoms
[forward/geometric/model.py:11-19, 587]; for a height field φ = −2k sin θ_ext h(y, z)
[forward/geometric/height_field.py:15]. Refraction enters twice: the operating angle is the external angle of
the internal (0,0,8) Bragg condition, from sin²θ_int = (sin²θ_ext + Δ)/(1 + Δ) with the exact relativistic
Δ = V0/E_eff [geometry/refraction.py:15, 59-65; geometry/specular.py:79-92] (the demo rule, B19); and an oxide
adds Re[T_k + I_k], built with refracted normal wavevectors k′⊥ = k√(sin²θ + Δ(V + iV′)), and attenuates by
exp(−Im[T_k + I_k]) [model.py:36-45; refraction.py:159-169; oxide.py:1019-1043]. Visibility is ray-traced:
each exit-plane point is followed back along −k_out; the illumination shadow (h/tan θ_in behind a riser whose
upper terrace is upstream) and the blocked-view strip (h/tan θ_out in front of one whose upper terrace is
downstream) carry no wave, and the trace is checked against `quantification/shadow.py` [model.py:20-29;
geometry/projection.py:53-60; B9, B13]. Invisibility (g·R integer) is flagged [model.py:30, 617]. Every output
carries "geometric model, no dynamical amplitude, B4 scope applies" [model.py:87]. Refuses: energy ≠ 200 keV,
non-plane-wave illumination, non-specular beams, non-bulk terminations, overlayers other than the continuum
oxide, and any a/4 step outside the <100> B4 scope, e.g. at <110> [model.py:215-258, 542-552].

**2.3 Multislice engine.** Our own forward multislice with slices perpendicular to the beam, i.e. a
transmission-type multislice applied to the Bragg case ("Peng-Cowley-type" [docs/agent_reports/
S5_independent_rheed_solver.md:24]; the Peng and Cowley papers [P18, P19] are METADATA_VERIFIED, not read
[docs/05:439-440]). Symmetric split step ψ(L_z) = P(dz/2) T_{N−1} P(dz) … T_0 P(dz/2) ψ_0 with
T_i = BL[exp(iσV_p,i) exp(−σW dz)] [forward/multislice/engine.py:4-11, 185-205] and σ = 2π(T + m_ec²)λ/(hc)²
[physics.py:9]; exact propagator exp(i dz (k_z − k)) or Fresnel, evanescent components removed
[propagator.py:5-13]. The projected potential is the independent-atom Kirkland parameterisation evaluated
through abTEM 1.0.10 [ABTEM], infinitely projected per slice and built in Fourier space [potentials.py:9-25];
the parameterisation itself [B06] is UNVERIFIED by us (SM17), and its mean inner potential, 13.903 V, sets every
refraction angle of multislice runs (B32) instead of B1's 12.0 V [potentials.py:26-30]. Illumination is an
apodised sheet beam in the vacuum band, tilted by an entrance-plane Fourier component and projected on its
downward components [illumination.py:3-16]. The box emulates a semi-infinite crystal: no vacuum below,
numerical absorbers (label NUMERICAL) on the bulk side and at the top, a vacuum margin larger than
H + L_z tan θ, a footprint H/tan θ, and a run-in of D/tan θ_int after first contact so that the reflection can
build up [forward/cell.py:3-19, 410-465]. Band limit: the 2/3 rule (attribution UNVERIFIED) or half-Nyquist,
with the (0,0,8) coefficient required inside the band [grid.py:9-27, 40]. Physical absorption is V′ = ratio·V
(item 21; demo B30: none) [potentials.py:35-37]. Frozen phonons are Gaussian displacements (the pipeline's sourced amplitude is B35) from a
generator seeded with [seed, realisation]; intensities are averaged after squaring
[potentials.py:153-168, 286; engine.py:289-296]. An oxide is a graded continuum layer added to the potential
[overlayer.py:1-13]. Status "UNVALIDATED" (section 3) [engine.py:52]. Refuses: energy ≠ 200 keV,
incommensurate slicing, a working reflection outside the band, any violation of the box geometry, abTEM other
than 1.0.10, and a mean inner potential differing from the one used for the angle by more than 5e-4 V
[engine.py:120-140; cell.py:371-465; potentials.py:181-183; pipeline/engines.py:28-31].

**2.4 Optics.** Dark-field aperture: an exact angular disc of semi-angle α about k_out, then demodulation by
exp(−2πi q_out x) [optics/darkfield.py:10-20, 171, 178]; only the specular beam is selectable; α is item 4
(demo B22). Projection along k_out: z_s = (x0 − x)/tan θ, the image foreshortened by sin θ along the beam
[optics/projection.py:4-14]. Surface-plasmon losses (coherent-state bookkeeping, DERIVED_HERE): the fringe
term is multiplied by F = e^{−(n_O+n_R)/2} + V_loss √(L_O L_R), i.e. e^{−n/2} for R1 and e^{−n} + V_loss(1 − e^{−n})
for R2; the phase is unchanged and the noise grows [optics/inelastic.py:21-50, 155-161]; n is item 21 (demo
B38, a transfer of the [TANISHIRO2003] measurement, DERIVED_HERE by E6), V_loss item 16 (demo B39, required for
R2, refused for R1). Convergence: I = Σ_s w_s I_s over quadrature members, each an independent engine run
[optics/coherence.py:4-10; forward/multislice/convergence.py:1-17]; the quadrature is refused if its derived
error bound exceeds the declared tolerance (B40), and with R1 only a condenser-biprism pre-tilt is implemented
[coherence.py:514-543]; item 3 (demo B21 plane wave, B40 disc); multislice engine only.

**2.5 Reference wave and carrier.** R1: u_r = A exp(i(2π q_c·r + φ_rel)), q_c being the measured carrier AFTER
compensation of the 2θ_ext inclination, which is not modelled; the aperture passage is recorded and has no
effect [optics/hologram.py:15-22, 106-125; B28]. R2: u_r(r) = s u_o(r + shift) e^{i(…)}, so the reconstruction
gives φ(r) − φ(r + s), with features of the reference region repeated sign-inverted and translated by −s
(DERIVED_HERE) [hologram.py:23-28; B5]. R3 exists in the optics but not in the pipeline [run.py:79]. φ_rel is
a simulation parameter, not evidence of hardware control [hologram.py:36-37]. Inputs: items 15, 16 (demo B28).

**2.6 Hologram and detector.** I = |u_o + u_r|², object and reference sharing each realisation, averaged over
realisations and members after squaring [hologram.py:269-279; SM13]. Detector: specimen-referred pixel
p = pitch/M, band-limited resampling, then counts = gain × Poisson(dose·I/⟨I⟩) from one declared seed, object
then empty hologram [optics/detector.py:3-24; hologram.py:479-511]; an empty hologram is formed with the same
reference and dose [run.py:18-22]. MTF: only "none" [detector.py:42]. Items 5, 6 (demo B23, B24). Refuses:
unshared realisations; biprism Fresnel fringes and drift (NotImplementedError) [hologram.py:241-247]; pitch/M
inconsistent with the pixel; an aperture band above the detector Nyquist frequency [detector.py:4-18].

**2.7 Reconstruction.** One code path for simulated and experimental holograms [reconstruction/sideband.py:1-3].
The carrier is the brightest bin inside a declared one-sideband disc of an EMPTY (or flat-region) hologram
(the object-hologram trap, B15, is refused); disc mask with optional Hann apodisation; demodulation; division by the empty
hologram; validity V = 2|w_empty|/D ≥ V_min, else NaN; no ramp is removed [sideband.py:10-62]. Demo choices
(B29): mask |q_c|/3, Hann, V_min 0.5, Itoh unwrapping [configs/demo_smoke_si001.yaml:324-328]; the real
choices are item 19. Refuses: carrier location on an object hologram, a search disc holding both sidebands, a
mask containing q = 0 or crossing Nyquist, a conjugate sideband [sideband.py:238, 310-313, 602].

**2.8 Unwrapping and joint branch resolution.** Itoh raster unwrapping in connected valid regions with
independent 2π offsets, not residue-aware [sideband.py:51-60, 353]. Terrace regions come from the ray-traced
BUILT geometry, eroded by a resolution margin; the step phase is a difference of circular medians whose
uncertainty is measured from the phase scatter [pipeline/quantify.py:4-17]. The branch is fixed jointly for
the K steps of a run by the lattice constraint φ_i + 2πm_i = −s(1 + ε) n_i a/4 + r_i, n_i ∈ ±{1…n_max},
|r_i| ≤ n_σ σ_φ,i, one common |ε| ≤ n_σ σ_s/s (one angle calibration); "resolved" only if exactly one
assignment survives and the chance bound (probability that phases carrying no height information pass) is at
most P(|Z| > n_σ) [quantify.py:19-40, 116-127, 132-233]; n_σ = 3 in the demo [configs/demo_smoke_si001.yaml:341]. The returned height is the measured −(φ + 2πm)/s, not the
lattice value [quantify.py:41-44]. Open (A3b N1): the closing step of a periodic staircase is not independent,
so the printed bound is too small (smoke demo: printed 1.22e-4, true rate 2.04e-3) [docs/05:407-411]. A
rocking-series inversion (B16) exists [quantification/rocking.py:1-40] but the pipeline does not use it
[run.py:81].

**2.9 No-step control.** A flat region is split at its median row along the beam; the circular medians of the
halves must agree within n_σ correlated standard errors [quantify.py:325-354; quantification/controls.py:38-70]. A failed or unperformed control withholds every height of the run
[run.py:171-182]; heights are also withheld for R2 (differential phase) and for a/4 steps outside B4
[quantify.py:44-48].

**2.10 Heights.** h = −(φ_w + 2πm)/s, s = (2π/λ)(sin θ_in + sin θ_out); σ_h² = (σ_φ/s)² + (h σ_s/s)², with
σ_s = k(cos θ_in σ_θ,in + cos θ_out σ_θ,out) (one common angle error for the specular beam) plus the
wavelength term (B31) [quantification/height.py:6-40, 100-121, 210-211]. Refused before division when
s ≤ σ_s or σ_φ ≥ π [height.py:190-206]. The geometric smoke demo returns +2.7156 ± 0.0165 Å for the built a/2
step (2.7155 Å) and ±0.0082 Å for the two a/4 steps [tests/pipeline/test_a3_priority1.py:234-247;
scripts/hpc/alliance/README_ALLIANCE.md:20, 216]. The feature path returns a masked height map
[quantification/height_map.py:1-40].

**2.11 Provenance and configuration gate.** Every parameter carries value, label, source and unit; one tied to
a docs/06 item is either PROJECT_INPUT (with `supplied_by`, `supplied_on`) or an ASSUMPTION registered for that
item, and at run level a null PROJECT_INPUT fails [io/config.py:4-53]. Run here: loading
`configs/cfg_b_si001_patterned.yaml` at run level raises `MissingProjectInputError` for items 3, 4, 5, 7, 8,
12, 13 and 15. A pipeline run declares its purpose; "comparison" refuses every demo stand-in (registry
`demo_only`), any ASSUMPTION for a blocking item, TEST_ONLY values and a static lattice
[pipeline/config.py:129-130, 796-812, 2025-2050; io/assumption_registry.yaml:61-62], and an angle computed from
an assumed V0 cannot carry PROJECT_INPUT [config.py:669-677]. Every run writes a manifest: package versions,
git commit and diff hash, seeds, precision, threads, SHA-256 of configuration and inputs, wave planes
[provenance/manifest.py:1-16, 35-37].

## 3. Validation ladder and status

The string opens with "UNVALIDATED" [forward/multislice/engine.py:52-67]; the middle column quotes it.

| Check | Engine `VALIDATION_STATUS` | docs/08 |
|---|---|---|
| Rung 1: refraction-only slab vs the analytic step-barrier amplitude and phase | "rung 1 (refraction-only analytic limit) and rung 2 test R2-A (...) pass in tests/forward" | 4.1 "DONE" |
| Rung 2, R2-A: Bragg-case (0,0,8) of a periodic continuum potential vs the exact semi-infinite solution, amplitude and phase across the plateau | as above; "R2-B (r = 0) is optional and qualitative" | 4.2 "DONE (R2-A passes; fails for every deliberate engine break)" |
| Independent solver sim-trhepd-rheed [SIMTRHEPD, SIMTRHEPD-CPC], flat Si(001) | "was RUN ... but the comparison is not like-for-like along the beam and its amplitude tolerance has no power (E8 M1, M2): not an amplitude validation" | 4.4 "PARTIAL" |
| Rung 3, continuum null tests and atomistic MOVED beam | "rung 3 has passed ONLY for the continuum null tests and the atomistic MOVED-beam translation" | 4.3 "PARTIAL" |
| Rung 3, atomistic FIXED beam | "the atomistic FIXED-beam translation check that docs/05 4.4 item 3 requires before any step-phase run has NOT passed" | 4.3; 3.7 "OPEN: the gate before any step-phase run" |
| abTEM cross-check | "was NOT RUN" | 4.5 "OPEN" |

Tolerances were fixed before the engine runs: rung 1 phase ≤ 1.0e-3 rad [tests/forward/test_rung1_refraction.py:10-11,
21]; R2-A complex difference ≤ 1.5e-3 and propagator phase ≤ 2e-4 rad [test_rung2_bragg.py:11-19]; continuum
rung 3 1.0e-2 rad, largest error 3.6e-3 rad [test_rung3_null.py:7-9]. The moved-beam translation agrees to
1.1e-3 rad; with the beam fixed the same comparison gives +0.57 rad, because the (0,0,8) reflection has not built
up by the exit plane [tests/forward/test_atomistic_translation.py:7-13; docs/05:396-400]. Against the solver
(with its own potential) the median phase difference is 0.014 rad at [100] and 0.017 rad at [110], and 0.398 rad
at [100] 15.0 mrad where |R|² is about 1e-5 [tools/plots/phase4_figures_solver_output.txt:1-8]. Consequence:
geometric heights are trustworthy within the B4 scope; the multislice pipeline runs but returns no heights
[docs/05:400-401; README_ALLIANCE.md:15-20]. Two wording inconsistencies: README_ALLIANCE.md:15-16 still says
rung 2 was not run (superseded by `engine.py:53-57` and docs/08 4.2); and `engine.py:63-64` says "up to 0.05 rad
at five other angles (0.051-0.075 rad)", where docs/08 4.4 correctly says "more than 0.05 rad".

## 4. What is not yet represented

* Instrument: lens transfer; biprism Fresnel fringes and overlap width; drift; detector MTF, pixel integration
  and readout noise; source-size and energy-spread ensembles; an energy filter; the R1 2θ_ext inclination and
  its compensation; R3 in the pipeline [run.py:69-79; docs/08 2.9; B24, B28]. Charging only as a static phase
  option of the optics, not in the pipeline [hologram.py:39-43; run.py:75; B8, item 22].
* Surface: the atomistic amorphous oxide, non-conformal layers in the multislice, carbon, the transition
  layer, TDS and diffuse scattering in the layer [B12, B41; docs/08 2.6]; riser relaxation [B11]; the effect
  of reconstructions on the step phase and the B37 sensitivity test [docs/08 2.5; B37]; monotonic (vicinal)
  staircases [docs/08 2.8]; patterned mesas and trenches in the engines [run.py:84-86]; buried voids beyond a
  demo [docs/08 2.11; B42].
* Physics: a/4 steps at <110> (δ unknown) and off-specular beams [B4; darkfield.py:48]; the azimuthal spread on
  a/4 steps [B4]; a sourced electronic absorption (bracket only) and a measured plasmon loss [B6, B30, B38;
  docs/08 1.10]; the IAM mean inner potential exceeds B1 by a model systematic [B32].
* Numerics and validation: pixel, slice, width and ensemble convergence, the fixed-beam null test, GPU = CPU
  [docs/08 3.1-3.8]; abTEM cross-check, a published-result reproduction, the lateral sign convention
  [docs/08 4.5-4.7]; a simulated rocking curve for the working angle [docs/08 2.10].
* Processing and comparison: rocking series and terrace segmentation from data in the pipeline [run.py:80-81];
  the A3b N1 chance bound [docs/05:407-411]; an experimental loader and the full uncertainty budget
  [docs/08 5.1, 5.2]; every PROJECT_INPUT marked NEEDS ALI [docs/08 1.1-1.12].

## Module map

| Stage | Module path | Main function/class | Role |
|---|---|---|---|
| Geometry | `geometry/specular.py`, `geometry/refraction.py` | `specular_condition_for`, `theta_int_from_ext_rad` | Bragg angles, relativistic refraction, wrap period |
| Structure | `structure/si001.py` | `build_si001_terraces`, `find_terrace_relations` | Staircase; relations and B4 verdict measured on atoms |
| Structure | `structure/reconstruction.py`, `forward/dimer_ensemble.py` | `build_reconstruction`, `DimerFlipFlopPotential` | Ramstad reconstructions; flip-flop ensemble |
| Structure | `structure/shapes.py`, `structure/features.py` | `HalfTorus`, `BuriedTorus`, `build_si001_with_feature` | Torus trench/ridge, buried void |
| Structure | `structure/oxide.py`, `structure/thermal.py` | `ContinuumOxideSpec`, `stack_phase_terms`; `si_rms_displacement_per_axis_A` | Grown oxide; thermal amplitude |
| Geometric engine | `forward/geometric/model.py`, `height_field.py` | `geometric_exit_wave`, `height_field_exit_wave` | −q·R phase, ray-traced visibility |
| Multislice engine | `forward/cell.py`, `forward/multislice/` | `build_reflection_cell`, `simulate`, `AtomicPotential`, `SheetBeam` | Reflection box, split-step slices |
| Optics | `optics/darkfield.py`, `optics/projection.py` | `select_dark_field`, `project_along_k_out` | Aperture about k_out; foreshortening |
| Optics | `optics/inelastic.py`, `optics/coherence.py` | `SurfacePlasmonLoss`, `ConvergenceQuadrature` | Loss fringe factor; convergence ensemble |
| Reference, hologram | `optics/hologram.py` | `reference_r1_vacuum_plane_wave`, `reference_r2_self_reference`, `partially_coherent_hologram` | R1/R2/R3, intensity after squaring |
| Detector | `optics/detector.py` | `DetectorSpec`, `record_holograms` | Pixel mapping, Poisson counts, gain |
| Reconstruction | `reconstruction/sideband.py` | `locate_carrier`, `reconstruct_sideband`, `unwrap_itoh_raster` | Carrier on empty hologram, mask, visibility, unwrap |
| Branch, control | `pipeline/quantify.py`, `quantification/controls.py` | `lattice_branch`, `no_step` | Joint h = n a/4 branch; no-step gate |
| Heights | `quantification/height.py`, `height_map.py`, `rocking.py` | `height_from_phase`, `height_map` | Signed h, σ_h, refusals; map; rocking series |
| Gate | `io/config.py`, `pipeline/config.py` | `load_config_file`, `load_pipeline_file` | PROJECT_INPUT refusal, demo vs comparison |
| Provenance | `provenance/manifest.py` | `build_manifest` | Versions, commit, seeds, hashes |
| Driver | `pipeline/run.py`, `pipeline/feature.py` | `run` | Staircase and feature chains end to end |
