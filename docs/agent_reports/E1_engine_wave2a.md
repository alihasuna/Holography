# E1: engine wave 2a (rung 2, null-test redesign, memory, kit hook, H5 script)

Agent E1, 2026-09-24. Written incrementally: task -> files:lines -> tests -> results verbatim -> NOT
RUN. Nothing committed or pushed. Machine shared with other agents (4 cores; load averages are
quoted with the runs).

Read first: P2_rung2_reference.md (all of sections 1-10, output section 12), H7_sizing_fixes.md,
H2 sections 2.1-2.6, 3, 10, 12, H5 A9/A10 and D.8, M2 (engine sections), docs/05 4.4,
docs/physics_conventions.md, the engine package, tests/forward (ladder_cases, null_test_cases, the
rung tests), scripts/hpc/null_test_study/, tools/physics_checks/rung2_reference.py.

Baseline before any edit: `run_study.py --config study.yaml --estimate` (17 points, grid, slices,
atoms, memory per point; peak RSS 831 MB, 34.5 s) saved in the scratchpad for the comparison of
task 2.

## Task 1: rung 2 (continuum periodic potential and test R2-A)

### Code

* `reflection_holo/forward/multislice/potentials.py`
  * `_continuum_crystal_fraction(cell, grid)` (new module function): the body of
    `ContinuumTerracePotential.fill`, moved unchanged (same operations, so the rung-1 class is
    bit-identical; tested below). `ContinuumTerracePotential.fill` calls it;
    `ContinuumTerracePotential.complex_potential(grid)` returns `fill(grid) * (V0 (1 + i r))`, the
    expression `_RealisedContinuum` used before.
  * `ContinuumPeriodicPotential(cell, *, V0_V, V0_label, harmonics, harmonics_label,
    physical_absorption, surface_profile)` (new; every argument required, no defaults): P2 8.1,
    V_j = f_j [V0 + sum_n 2 V_n cos(2 pi g_n (x_j - x_s + t_n))] (1 + i r), harmonics
    `((g_per_A, V_g_V, t_A), ...)` (an explicitly empty tuple is the rung-1 constant potential),
    harmonics POINT-SAMPLED at the pixel centres, f_j the crystal fraction of the rung-1 class,
    front-face overlap along z as the rung-1 class (`_RealisedContinuum`), `mean_inner_potential_V()`
    = V0. Refusals: missing/unlabelled V0 or harmonics, non-triples, g <= 0, non-finite values,
    duplicate g, surface_profile other than "sharp", more than one terrace (the phase origin of the
    harmonics across a step is not defined; not implemented), non-continuum cell.
    `provenance()` records V0, every (g, V_g, t) and both labels; `realised_harmonics(grid)`
    records the realised V0 and V_g (cos and sin) by a least-squares fit to the interior pixels
    (f = 1, exact for point samples) plus max |Im - r Re|; the engine stores it in
    `ExitWave.metadata["potential"]["realised"]["realised_harmonics"]`.
  * `_RealisedContinuum`: `base = pot.complex_potential(grid)` (same expression for the rung-1
    class) and the realised-harmonics record when the potential has one.
* `reflection_holo/forward/multislice/engine.py` `reflection_setup`: the harmonics of a periodic
  continuum potential (`band_harmonics_per_A()`, (g, 0) along x) are asserted inside the band of the
  transmission function together with the declared working reflections (grid.check_band;
  SamplingError otherwise) and recorded in the band record. Choice (P2 8.1 left it to the engine
  owner): `working_reflections_hkl` stays `()` for a continuum cell (no reciprocal lattice); the
  harmonics are part of the potential's definition, so the potential supplies them. MultisliceParams
  docstring updated accordingly.
* `reflection_holo/forward/multislice/__init__.py`: exports `ContinuumPeriodicPotential`.
* `tests/forward/ladder_cases.py` (appended): `rung2_reference()` imports P2's
  `tools/physics_checks/rung2_reference.py` (no re-derivation); `rung2_case` builds P2 8.2's cell
  (one terrace, extent_y 10 A, ny = 1, absorbers 15/10 A 100 V sin^2, entrance 10 A, sheet beam H 24 A,
  edge 4 A, 2 A above x_s, theta = P2's `darwin_plateau(...)["theta_centre"]` = 16.134773 mrad,
  exit plane Z_e after the top-edge contact, vacuum H + 2 + L tan(theta) + 150 A, dx exact);
  `rung2_measure` reads r(f) with `flat_reflection_coefficient(x_surface_A = x_s, propagator = the
  run's, rel_threshold = 0.05)` and compares each bin with P2's `reflection_amplitude(asin(lambda f),
  200, V0, [V_g], g, r, plane_offset_A = 0, model = "exact" | "engine_exact_propagator")`; no fitted
  phase or angle offset. Values: V0 = 13.902843 V, V_008 = 1.035742 V, g = 8/a (TEST_ONLY, P2 6.1).
* `tests/forward/test_potential_periodic.py` (new, 10 tests): bit-for-bit identity with the rung-1
  class when every V_g = 0 (potential arrays, six realised slices including the front-face slice, in
  complex64 and complex128, r = 0 and 0.1; and a full small run, exit waves byte-identical), point
  sampling and the realised-harmonics record (1e-12), refusals, band assertion of a harmonic
  (3.4 1/A at dx 0.1 A refused with SamplingError).
* `tests/forward/test_rung2_bragg.py` (new): R2-A with P2 8.4's criteria copied unchanged:
  (a) max |r - R_ref| <= 1.5e-3 over |eta| <= 3 for r = 0.1 (D 100 A, Z_e 5000 A) and r = 0.05
  (D 150 A, Z_e 10000 A), each with the Fresnel propagator (model "exact") and the exact propagator
  (model "engine_exact_propagator"); (b) r = 0.1, |eta| <= 0.9: |arg(r_X/r_F) -
  arg(R_eep/R_exact)| <= 2e-4 rad on identical bins; (c) dx 0.05 vs 0.025 A order >= 1.5; plus the
  realised potential and band record. Non-vacuity guards (>= 10 bins, bins with eta < -1 and > 1, >= 4
  bins inside |eta| <= 0.9) are not tolerances. R2-B (r = 0; D 250 A, Z_e 30000 A, vacuum-only
  read-out from x_s + 60 A, |eta| <= 0.5, T_B = 3e-2) is marked OPTIONAL and QUALITATIVE (runs only
  with RH_RUNG2_R2B=1) and is not part of the engine status.
* Engine status (`engine.py` VALIDATION_STATUS and module docstring): now lists rung 1, rung 2
  test R2-A and rung 3 as passed; R2-B optional/qualitative; abTEM cross-check and the atomistic
  flat-surface rocking curve against a dynamical solver NOT RUN. Still "UNVALIDATED".

### Results (first and only run of the tolerances; load average 11.3 at the start)

`venv/bin/python -m pytest -q tests/forward/test_potential_periodic.py` -> `10 passed in 0.73s`

`venv/bin/python -m pytest -q -s tests/forward/test_rung2_bragg.py` -> `7 passed, 1 skipped in
103.75s (0:01:43)` (the skip is R2-B without RH_RUNG2_R2B=1). Summary lines verbatim:

```
R2-A r = 0.1, fresnel: 18 bins |eta| <= 3.0, max |dR| = 4.557e-04 (T_A = 0.0015), max |d arg| = 1.906e-03 rad
  fresnel r-model exact, dx 0.02500 A, nx 16308, 6612 slices, x_s 115.000 A, run 15.0 s
R2-A r = 0.1, exact: 18 bins |eta| <= 3.0, max |dR| = 4.618e-04 (T_A = 0.0015), max |d arg| = 1.889e-03 rad
  exact r-model engine_exact_propagator, dx 0.02500 A, nx 16308, 6612 slices, x_s 115.000 A, run 15.9 s
R2-A r = 0.05, fresnel: 24 bins |eta| <= 3.0, max |dR| = 5.186e-04 (T_A = 0.0015), max |d arg| = 1.740e-03 rad
  fresnel r-model exact, dx 0.02500 A, nx 21535, 11612 slices, x_s 165.000 A, run 31.3 s
R2-A r = 0.05, exact: 24 bins |eta| <= 3.0, max |dR| = 5.267e-04 (T_A = 0.0015), max |d arg| = 1.714e-03 rad
  exact r-model engine_exact_propagator, dx 0.02500 A, nx 21535, 11612 slices, x_s 165.000 A, run 30.9 s
R2-A (b), r = 0.1, |eta| <= 0.9 (6 bins): measured arg(r_X/r_F) in [-1.181e-03, -9.489e-04] rad, predicted [-1.201e-03, -9.996e-04] rad, max |measured - predicted| = 5.074e-05 rad (T = 0.0002)
R2-A (c), r = 0.1, Fresnel: max |dR| 1.454e-03 (dx 0.05) -> 4.557e-04 (dx 0.025): order 1.67 (>= 1.5)
```

Selected bins (r = 0.1, Fresnel), engine against the exact reference at the same angle:

```
    eta  -1.074: engine 0.25091 exp(+1.31703 i), ref 0.25084 exp(+1.31793 i), |dR| 2.37e-04
    eta  -0.421: engine 0.31279 exp(+1.63997 i), ref 0.31283 exp(+1.64142 i), |dR| 4.56e-04
    eta  -0.093: engine 0.33413 exp(+1.82201 i), ref 0.33409 exp(+1.82321 i), |dR| 4.05e-04
    eta  +0.568: engine 0.34543 exp(+2.19029 i), ref 0.34570 exp(+2.19091 i), |dR| 3.42e-04
    eta  +0.900: engine 0.33505 exp(+2.36021 i), ref 0.33532 exp(+2.36129 i), |dR| 4.49e-04
```

Reading: every criterion passes with margin (a: 4.6e-4 and 5.3e-4 against 1.5e-3, the budget P2
predicted was <= 4.5e-4 and <= 3.2e-4; b: 5.1e-5 rad against 2e-4; c: order 1.67). The engine
agrees with P2's independent split step (P2 section 7: 4.39e-4, 4.47e-4, 2.78e-4, order 1.71,
propagator pair 4.7e-5 rad) to within a few 1e-5. The r = 0.05 residual (5.2e-4) is larger than the
split step's 2.8e-4 but inside the tolerance; its bins differ from P2's (nx 21535 here with dx
exactly 0.025 A, 21536 in the split step, which rounds nx to even). The phase sweep across the
plateau (arg R from 1.32 to 2.36 rad for r = 0.1 over |eta| <= 1.07) is reproduced bin by bin
without any fitted offset, so the effective V0 and V_g, the phase origin at x_s and the read-out
plane are right at the level P2 8.4 quantifies (a 5 mV error of V0 or a 0.01 A origin error would
exceed T_A at r = 0.05).

R2-B (optional, qualitative; `RH_RUNG2_R2B=1 venv/bin/python -m pytest -q -s
tests/forward/test_rung2_bragg.py -k r2b` -> `1 passed, 7 deselected in 317.76s (0:05:17)`):

```
R2-B (optional, qualitative) r = 0: 7 bins |eta| <= 0.5, max |dR| = 1.120e-02 (T_B = 0.03); arg R_ref from +1.2212 to +2.0823 rad
  fresnel r-model exact, dx 0.02500 A, nx 38444, 31612 slices, x_s 265.000 A, run 316.5 s
    eta  -0.459: engine 1.00881 exp(+1.22805 i), ref 1.00000 exp(+1.22118 i), |dR| 1.12e-02
    eta  -0.041: engine 0.99426 exp(+1.67285 i), ref 1.00000 exp(+1.66700 i), |dR| 8.19e-03
    eta  +0.379: engine 0.99331 exp(+2.07479 i), ref 1.00000 exp(+2.08232 i), |dR| 1.01e-02
    eta  +0.942: engine 0.97315 exp(+2.88580 i), ref 1.00000 exp(+2.84652 i), |dR| 4.71e-02
```

The same 1.12e-2 as P2's split step with the vacuum-only read-out (P2 8.4); qualitative only
(outside |eta| <= 0.5 the r = 0 build-up and the absorber are not converged, P2 6.5).

## Task 2: null-test redesign (clean depth, [100], surface-resolved read-out)

### Code

* `tests/forward/null_test_cases.py`: `translation_pair(*, theta, clean_depth_A, azimuth, ...)` and
  `step_case(*, theta, width_periods, clean_depth_A, azimuth, ...)`: clean depth and azimuth are
  REQUIRED (no default; `clean_depth_A=None` raises). `LEGACY_M2_CLEAN_DEPTH_A = 21.0` is the
  explicit legacy value (M2: buildup 20 + 1 A), documented as shallower than the 24.5 A extinction
  depth. `AZIMUTHS`: "110" (period a/sqrt2, as M2) and "100" (period a, dz = a/4 as H2; label notes
  the four-beam case of H2 2.2). `tile_above_periods` (default 400 = M2's threshold, an exact
  implementation choice, not a physical input) is passed explicitly by the study runner. The
  private builders lost their defaults.
* Surface-position-resolved read-out (H2 2.4, finding N12): it existed in code as H2's
  `specular_column` in `tools/hpc/supercell_sizing.py` (reproduced by H5, A10), so it is USED, not
  re-implemented: `_h2_specular_column()` imports it. New: `resolved_translation(ewA, ewB, pair, *,
  expected_rad, radius_per_A, x_cut_A, taper_A, min_height_A, bin_A, exit_excl_A, tol_phase_rad,
  tol_amp)` maps each exit wave to the surface coordinate z_s = L_z - (x - x_s)/tan(theta) with its
  OWN surface x_s, averages A and B in the same z_s bins (from the later bottom-edge contact to
  L_z - exit_excl_A; a final sliver shorter than half a bin is dropped), and reports per bin
  err = wrap(arg(<E_B>/<E_A>) - expected) and |<E_B>/<E_A>|, plus `converged_beyond_A` (end of the
  last bin failing either tolerance; None if the last bin fails). Convention as run_translation:
  expected = -(k_out - k_in).R and E_B = E_A exp(+i expected) where converged (DERIVED_HERE in the
  docstring). `run_translation(..., surface_resolved=None | dict)` computes it from the same two runs.
* `scripts/hpc/null_test_study/run_study.py`: per point `clean_depth_A` and `azimuth` required;
  top-level `build.tile_above_periods` required; optional top-level `surface_resolved` block (exactly
  the keys of `RESOLVED_KEYS`; without it the result says "not computed"). The estimate line names
  azimuth and clean depth. Docstring updated (study files, engine status).
* `scripts/hpc/null_test_study/study.yaml`: its 17 points unchanged; each point now carries the
  explicit legacy values `clean_depth_A: 21.0, azimuth: "110"`, and `build: {tile_above_periods:
  400}`; header comment says it is the M2-reproduction set only. The runtime block text is unchanged
  (the kit tests replace it verbatim).
* `scripts/hpc/null_test_study/study_depth100.yaml` (new, 24 points): clean depth 100 A for every
  point; r = 0.05 and 0.1 only (TEST_ONLY labels); fixed-beam translation at [110] and at exact
  [100] (bragg_0008_mip = 16.1347 mrad, L0/L5k/L10k for both r, plus 12 and 20 mrad off-Bragg at
  r = 0.1); moved-beam controls at both azimuths (r = 0.1, L10k); the M2 step points at [110] with
  r >= 0.05 (w8/w16/w32 at L5k, w16 at r = 0.05, w16 at 20 mrad, w16 at L10k);
  `surface_resolved` with H2's parameters (0.1 1/A, x_cut 2 A, taper 3 A, 5 A minimum height,
  500 A bins, 750 A exit exclusion, tolerances 1e-2 rad and 1e-2 as the README criteria);
  `build.tile_above_periods: 0` (every cell one verified period tiled: exact, keeps the host build
  memory low).
* Callers updated for the required arguments (legacy values where they reproduce M2):
  `tests/forward/test_atomistic_translation.py` (`M2_CELL`), `scripts/hpc/alliance/gpu_check.py`
  (kit, step_case of the tiny GPU check), `tools/hpc/supercell_sizing.py` (H7's tool: passes the
  study point's `clean_depth_A`, `azimuth` and `build.tile_above_periods`), and task 5.

### Tests

* `tests/forward/test_null_study_readout.py` (new, 7 tests): H2's function is the one used; synthetic
  exit waves translated by an integer number of pixels: covariant fields give err = 0 and amp = 1 in
  every bin (1e-9); ray mapping (phase ramp: bin phase = phase at the bin centre within 5e-3 rad,
  tolerance derived in the docstring; a bump centred at z_s = 7250 A peaks in [7000, 7500)); a
  known Gaussian excess on B gives the bin deviations (2e-3) and converged_beyond_A = 1500 A; a
  missing phase gives None; the case functions refuse missing clean depth/azimuth; both study files
  carry the required keys (study.yaml: 17 points, 21 A, [110], no resolved block; study_depth100:
  >= 100 A, r >= 0.05 TEST_ONLY, [110] and [100] fixed and moved, steps, [100] at bragg_0008_mip).
  Correction during development: my first synthetic construction used E_B = E_A exp(-i expected)
  (the opposite of the code's documented convention) and a 1e-3 rad ray-mapping tolerance chosen
  without analysis; the read-out's own band-pass ringing is up to 3.7e-3 rad per pixel and 7e-4 rad
  per bin (measured), so the test now uses a stronger ramp, the derived 5e-3 rad and a bump test.
  These were new tests of this task, not existing ones.
* `tests/forward/test_atomistic_translation.py`: the covariant pair is run once (module fixture)
  with the resolved read-out; the existing whole-x assertions are unchanged; new
  `test_whole_configuration_translation_surface_resolved` requires every bin within 1e-2 rad and
  1e-2 amplitude (the same criteria). Result (`4 passed in 204.54s`):

```
covariant translation: Delta_phi -3.10158 rad, expected -3.10269, error +1.11e-03, |B|/|A| 1.0024
fixed beam: Delta_phi -2.53410 rad, error +5.69e-01
z_s   123.9-  373.9 A (from contact    0.0): err -5.43e-05 rad, |B|/|A| 1.0008, |E_A| 0.0555
z_s   373.9-  623.9 A (from contact  250.0): err +4.06e-04 rad, |B|/|A| 0.9996, |E_A| 0.1047
z_s   623.9-  873.9 A (from contact  500.0): err +8.35e-04 rad, |B|/|A| 1.0010, |E_A| 0.0894
```

  (that run still showed a 2.8 A sliver bin, err +1.88e-4; slivers are dropped since.) The legacy
  whole-x numbers equal M2's (+1.11e-3 rad, 1.0024; fixed beam +0.569 rad).

### Runs

* study.yaml estimate after the change against the baseline taken before any edit: all 17 points
  identical in grid, slices, atoms, numpy peak and GPU device peak (parsed and compared; the line
  only gained "[110] clean depth 21 A"); peak RSS 830 MB.
* study_depth100.yaml estimate, numpy, 4 threads (a scratch copy differing only in the runtime
  block; the file keeps cupy/8 for the cluster): 24 points, exit 0, peak RSS 1.60 GB (RSS watchdog at
  2.8 GB), 98 s, load 11-13. Saved with a provenance header (file hashes, HEAD, load, what the
  numbers are) as `scripts/hpc/null_test_study/study_depth100_estimate_numpy4.txt` (final engine
  code, i.e. after task 3; an earlier run with the task-2 code differed only in the GPU device peak
  of the four nx = 2500 points: 15 -> 14 MB and 246 -> 240 MB). Largest point
  step110_w32_bragg_abs10_L5k: grid 1875x1920, 6642 slices, 9,125,632 atoms, numpy peak 1462 MB,
  GPU device 415 MB (lower bound). Sum over the 24 points: GPU ~213 s (ASSUMPTION model); CPU
  ~53,000 s (x1.5, timed under load 11-13, so pessimistic).
* One point run end to end (`--only tfix110_bragg_abs10_L0`, numpy, 4 threads): 122 s, peak RSS
  340 MB, JSON and manifest written. Result (TEST_ONLY, not a verdict: the shortest cell): whole-x
  err +0.348 rad, amp 0.944; resolved: 1 bin (z_s 292-627 A), err +0.119 rad, amp 1.397,
  converged_beyond_A None, i.e. not converged within this cell, as the build-up lengths predict
  (P2 5.3: >= 2600 A at r = 0.1).
* NOT RUN: the other 23 points of study_depth100.yaml (HPC work, about 3.5 GPU-minutes by the
  ASSUMPTION model).

## Task 3: memory (blocked structure-factor exponentials)

Applied: H7's proposal for the complex128 temporaries. `potentials._phase_factors(xp, f64, p,
dtype)` (new) forms exp(-2 pi i f p) exactly as before (float64 product, complex128 multiply,
complex128 exp, cast); with more than 2 x `EXP_BLOCK_ROWS` (= 1024) rows it forms blocks of 1024
rows into a preallocated array of the working precision (per-element operations unchanged). Up to
2048 rows the unblocked form is kept because it needs less memory there (32 m n against
(cb m + 32 x 1024) n), so no grid gets a larger peak. `_RealisedAtomic.projected` calls it for Ex
and Ey. NOT applied: H7's second proposal (`astype(copy=False)` of V (1 + i r), a complex64 copy,
not a complex128 temporary; it would also make r = 0 and r > 0 equal, which
`test_zero_absorption_is_bounded_by_one_array` states the opposite of).

Numerical identity (`tests/forward/test_potential_blocked_exponentials.py`, new, 13 tests; the
reference is a VERBATIM copy of `projected` before the change; criterion: byte equality):
phase factors for block sizes 1, 7, 16, 1000 and complex64/complex128; 5 slices each of a realised
576 x 84 potential with the blocked path forced (block 16) for complex64 r = 0.1, complex128 r = 0 and
complex64 frozen phonons; a full small run (exit waves). `13 passed in 9.73s`: bit-identical.

Memory model (`engine.py`): `_exp_stage_B(rows, n, cb)` = 32 rows n (unblocked) or
cb rows n + 32 x 1024 n (blocked); the exponential stage is `max(E(nx), cb nx n + E(ny))` (+25 n);
`largest_slice` records `exp_block_rows`; the multi-species upper bound uses E() the same way.
`tests/forward/test_memory_model.py`: the H5-M4 test and the "wide/exponentials" case measure the
UNBLOCKED exponential stage; since this cell (ny = 2520) is now blocked at the default, they select
the unblocked path explicitly (`EXP_BLOCK_ROWS = 4096`; engine and model read the same constant)
with their assertions and the 2 % tolerance unchanged. New: `test_wide_slice_blocked_exponentials`
(block 1200: blocked exponentials dominate; default 1024: the pixel stage dominates; measured = model
within 2 %) and `test_blocking_saves_the_modelled_amount`. `11 passed in 48.86s`. Measured
(tracemalloc) / model on the wide cell (432 x 2520, complex64, r = 0.1):

```
wide 432x2520 c64 r=0.1 block 4096: measured 133,012,165 B, model 132,997,024 B, ratio 1.0001; exponentials 70,661,640 B, pixel stage 50,340,360 B
wide 432x2520 c64 r=0.1 block 1200: measured 114,464,077 B, model 114,449,824 B, ratio 1.0001; exponentials 52,114,440 B, pixel stage 50,340,360 B
wide 432x2520 c64 r=0.1 block 1024: measured 112,689,845 B, model 112,675,744 B, ratio 1.0001; exponentials 47,383,560 B, pixel stage 50,340,360 B
2a_a2 row (2250 x 24000, n 15211, 73.8 M atoms), block 1000000000: numpy peak 20.35 GB, cupy device peak 14.98 GB, exponentials 11.96 GB, pixel stage 4.71 GB
2a_a2 row (2250 x 24000, n 15211, 73.8 M atoms), block 1024: numpy peak 13.10 GB, cupy device peak 7.73 GB, exponentials 3.69 GB, pixel stage 4.71 GB
```

H7's 2a_a2 row: the Ey transient 32 ny n = 11.7 GB becomes 32 x 1024 x n = 0.50 GB; the modelled
GPU device peak falls from 14.98 to 7.73 GB (UNVERIFIED on a GPU, a lower bound).

Consequence found (NOT fixed; H7's tool, a check I did not write): `venv/bin/python
tools/hpc/supercell_sizing.py` (report mode) now ends `54/60 checks pass`; the six failures are
`device_peak_ge_H5_model_<row>`, which require the engine's device peak to be at least H5's formula
48 px + max(32 nx n, 8 nx n + 32 ny n), i.e. the UNBLOCKED temporaries of the pre-change code:

```
  FAILED: device_peak_ge_H5_model_2a_a4_miscut0.1_r0.10: model device peak 3.162 GB >= H5's measured-model 4.398 GB (48 B/px + max(32 nx n, 8 nx n + 32 ny n); the engine model adds the entrance wave and the pixel stage of the potential construction)
  FAILED: device_peak_ge_H5_model_2a_a4_miscut0.1_r0.05: model device peak 3.766 GB >= H5's measured-model 5.099 GB (...)
  FAILED: device_peak_ge_H5_model_2a_a2_miscut0.1_r0.10: model device peak 7.731 GB >= H5's measured-model 14.548 GB (...)
  FAILED: device_peak_ge_H5_model_2a_a4_miscut0.1_r0.00: model device peak 4.906 GB >= H5's measured-model 5.781 GB (...)
  FAILED: device_peak_ge_H5_model_3_torus_R1000_r20_r0.10: model device peak 7.438 GB >= H5's measured-model 11.245 GB (...)
  FAILED: device_peak_ge_H5_model_3_torus_R1000_r20_r0.05: model device peak 8.665 GB >= H5's measured-model 12.959 GB (...)
```

Diagnosis: expected consequence of the reduction; the check's premise no longer describes the
engine. Proposed (for the tool's owner/orchestrator, not applied): compare with H5's formula with
the blocked stage, 48 px + max(E(nx), 8 nx n + E(ny)). The tool's saved output
(`tools/hpc/supercell_sizing_output.txt`, H7's record) was not regenerated. No test runs the
tool's report mode (the kit's gpu_sanity uses only its --measure mode, unaffected).

## Task 4: kit hook (GPU memory from the dry run)

* `reflection_holo/pipeline/__main__.py`: `dry-run --report-json PATH` writes the full dry-run
  report plus the configuration's absolute path, SHA-256 and variant (schema
  `reflholo_pipeline_dry_run_report/1`); stdout unchanged.
* `scripts/hpc/alliance/dry_run_job.py`: the dry-run job passes `--report-json
  <job dir>/dry_run/dry_run_report.json` and records its path in dry_run_resources.json.
* `scripts/hpc/alliance/kit.py`: `plan --gpu-mem-from-dry-run PATH --gpu-mem-margin F`
  (`gpu_need_from_dry_run`): PATH is the report or the dry-run job directory; F is REQUIRED with it
  (no default; refused if absent or < 0); the report must match the submitted configuration's
  SHA-256 and variant, have a multislice estimate and backend cupy, and the job must be a pipeline
  job of a cupy configuration (else refused). NOTE lines print the derivation: device_peak_cupy
  (engine.memory_model, UNVERIFIED on a GPU, LOWER BOUND: cuFFT/cuBLAS workspaces and the cupy pool
  not modelled) x (1 + F) = need in GB (1e9 B); host = cupy host peak + 48 B/atom builder structure
  (192 B/atom in total, H7 4), compared with the resolved --mem (WARNING if below) or noted where
  the cluster fixes it. The derived need drives the existing instance refusal; an explicit
  `--need-gpu-mem-gb` overrides it (NOTE says so; its refusal message is unchanged). The derivation
  is recorded as `gpu_memory_need` in the submission record.
* `scripts/hpc/alliance/submit.sh`: passes both options (header documents them; `-h` range updated).
* `scripts/hpc/alliance/README_ALLIANCE.md` 4.7: one paragraph and the usage line.
* `tests/hpc/test_kit_gpu_mem_from_dry_run.py` (new, 7 tests): derivation printed and used
  (25 GB x 1.5 = 37.5 GB fits a 3g.40gb instance, x 2.0 = 50 GB is refused, the full 80 GB instance
  accepted); margin required, margin without report refused, negative margin refused, explicit
  override; report of another configuration/variant/schema, numpy backend, no multislice estimate,
  missing file refused, job directory accepted; not for CPU jobs or gpu-check; host warning with
  --mem 4G against 7.26 GiB, none with 16G, the submission record's fields; the pipeline writes the
  report (demo_smoke_si001 multislice_tiny); the emulated dry-run job writes it.
  `7 passed in 24.89s`.

## Task 5: tools/hpc/review_h5_recompute.py

Minimal call-signature fixes only (diff: 6 insertions, 5 deletions): `working_reflections_hkl=((0,
0, 8),)` in the three `MultisliceParams(...)` calls (all atomic Si(001), the B17 stand-in used
everywhere else); `clean_depth_A=21.0, azimuth="110"` in the `translation_pair` and `step_case`
calls (the new required arguments of task 2, with the M2 values the script reproduces); and
`reflections_per_A={}` in its direct `check_band(...)` call (the other H7 signature change, found
when the first fix let the script run further): an empty mapping keeps exactly the beam-angle band
check H5 measured (A7: passes up to 0.450 A). Nothing else changed.

Run (report mode): `8/13 checks pass; runtime 58 s`, exit 1. Comparison with H5's own run: H5's
commit 47256f3 extracted with `git archive` into the scratchpad and its script run there gives
`13/13 checks pass`; the diff of the two outputs (runtime and load lines excluded) is exactly five
lines of the engine's `estimate_resources` memory and the five checks that compare it with H5's
replica of the pre-H7 accounting; every other printed number is identical:

```
<   study point tfix_bragg_abs0_L0: ... engine 3,844,352 B ... my replica 3,844,352 B / 0.314 s ...
>   study point tfix_bragg_abs0_L0: ... engine 4,822,708 B ... my replica 3,844,352 B / 0.314 s ...
<   study point tfix_off20_abs10_L5k: ... engine 10,701,408 B ...     >  ... engine 16,039,480 B ...
<   study point step_w32_bragg_abs10_L5k: ... engine 340,405,248 B ...  >  ... engine 527,109,368 B ...
<       engine estimate_resources: 23,236,480 B (row V)      >  37,758,296 B
<       engine estimate_resources: 630,765,808 B (row Wmin)  >  988,441,472 B
FAILED: replica_vs_engine_tfix_bragg_abs0_L0, replica_vs_engine_tfix_off20_abs10_L5k, replica_vs_engine_step_w32_bragg_abs10_L5k, V_row_built, Wmin_row_built
```

Diagnosis: these checks encode "the engine's estimate equals H5's replica of the engine as of
47256f3"; H7 changed the engine's accounting (H5's own finding M4: the temporaries were missing),
and the Wmin row (ny = 2187 > 2048) also carries task 3's blocking. The script is H5's record; per
the instruction nothing but the call signatures was changed, so these five checks now fail by
design of the record, not by a numerical change of the engine (the GPU seconds, grids, slices and
atoms still agree).

The other two modes of the script also run after the fix (outputs to the scratchpad, the stored
JSONs untouched): `--rerun` (static, 408 s, peak RSS 381 MB): its read-outs of H2's bu_100_r010
strip are identical, JSON-exact, to H5's stored `tools/hpc/review_h5_rerun.json` (the engine's
numerics are unchanged since H5). `--memtime` (exit 0, peak RSS 1.04 GB): host bytes per atom
unchanged (frozen 113.27 identical; static 118.58 against 118.45, first-call effect as H7 noted);
H5's wide-slice probe (1470 x 4032 px, n = 4992 atoms in the slice, ny > 2048 so the exponentials are
now blocked) measures projected() 385,810,728 B (H5: 702,919,128 B) and a slice-loop increment of
528,060,264 B (H5: 845,168,784 B); the updated memory model gives 385,809,792 B and 528,058,752 B
(ratios 1.0000024 and 1.0000029): an independent confirmation of task 3 on H5's own probe.
