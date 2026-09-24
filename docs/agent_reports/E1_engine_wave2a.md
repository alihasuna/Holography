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
