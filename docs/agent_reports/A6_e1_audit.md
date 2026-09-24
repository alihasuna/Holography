# A6: audit of E1 engine wave 2a at commit 67f3bf5

Agent A6, 2026-09-24. Written incrementally. Scope: E1's work as recorded in
`docs/agent_reports/E1_engine_wave2a.md`, audited at commit 67f3bf5 in a detached worktree
(`<scratchpad>/a6_wt`), run with the main venv (`/home/user/Holography/venv/bin/python`, numpy
2.4.6, abTEM 1.0.10) and `PYTHONPATH=<worktree>` (checked: `reflection_holo.__file__` resolves to
the worktree, not to the editable install). Nothing installed; no code under audit modified; nothing
committed or pushed. E2/E3 code (illumination tilt, convergence members, reconstructions, coherence)
is out of scope (auditor A5). `<scratchpad>` =
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`; all A6
scripts named below are there (not in the repository).

Status: FINAL (2026-09-24, 03:07 UTC). Worktree removed at the end (section 10).

## Findings (ranked)

No BLOCKER. Two MAJOR findings, both in the null-test redesign (task 2); the rung-2 potential,
test R2-A, the blocked exponentials and the memory model hold up under every check run here.

| id | severity | file:line | finding (reproduction in the section named) |
|---|---|---|---|
| N-1 | MAJOR | tests/forward/null_test_cases.py:124-125 (H = 8, edge 2, gap 2 defaults); scripts/hpc/null_test_study/run_study.py:81-85; study_depth100.yaml:18-23, 62 | study_depth100's translation points use an 8 A sheet beam (footprint 496 A); the surface-resolved read-out of H2 2.4 needs the strip lit up to the exit plane. On an exactly covariant continuum case with the study's beam, the fixed-beam comparison never converges (amp ratio 0.15-11.9, err to 2.9 rad) and the moved-beam control fails on noise-floor bins (abs E_A ~ 1e-5): `converged_beyond_A = None` for a correct engine. E1 read its one run as "not converged, as the build-up lengths predict" (E1_engine_wave2a.md:222-226). Section 4 |
| N-2 | MAJOR | tests/forward/null_test_cases.py:278-285 | `converged_beyond_A` is None whenever the LAST bin fails; no amplitude floor. A converged strip-long-beam case (<= 2.1e-3 rad, <= 6.8e-3 in bins d = 2500-4000 A) returns None because its last, partial bin (12-20 A above the surface) has amp 1.029. Section 4 |
| N-3 | MINOR | null_test_cases.py:124-125, 345-346; run_study.py:15 | beam height, edge and gap of the null test (physical inputs of the illumination) remain silent defaults, while run_study.py says "every value in a study file is required (no defaults)". Section 4 |
| S-1 | MINOR | engine.py:13-15; run_study.py:23-24; study_depth100.yaml:27 | "rung 3 pass" without the "(continuum null tests)" qualifier that VALIDATION_STATUS (engine.py:52) carries; the atomistic fixed-beam gate of docs/05 4.4 item 3 has not passed. Section 3 |
| S-2 | MINOR | engine.py:53-54 (and 15-16) | "flat-surface rocking curve against a dynamical solver ... NOT RUN" was stale at 67f3bf5: S5 ran it (872e949); docs/05 4.4 was updated after 67f3bf5 (21d1930), VALIDATION_STATUS was not. Section 3 |
| B-1 | MINOR | potentials.py:70-72; test_potential_blocked_exponentials.py:99; E1 report 235-237 | "up to 2 x EXP_BLOCK_ROWS rows the unblocked form needs less memory" is false for complex64 above 1365 rows: measured 32.00 vs 23.63 B/element at 2048 rows. No numerical effect. Section 5 |
| K-1 | MINOR | reflection_holo/pipeline/__main__.py:124-132; scripts/hpc/alliance/kit.py:366-373 | the dry-run report carries the configuration's SHA-256 but no code identity; the kit already computes `engine_code_sha256` (kit.py:221) for the gpu-check gate but does not compare it here, so a dry run made with other engine code (another memory model) is accepted. Section 6 |
| K-2 | MINOR | kit.py:638-642 | an explicit `--need-gpu-mem-gb` below the derived need (even below the model's lower bound) is accepted with a NOTE only. Section 6 |
| Z-1 | MINOR | tools/hpc/supercell_sizing.py:1735-1743 (orchestrator) | the replacement check `device >= 48 px` is vacuous: the model's device peak is >= 84 B/px (complex64) and >= 168 B/px (complex128) for every input; 11 of the "60/60" checks cannot fail. H5's formula with the blocked stage is a real bound and holds for all 22 rows. Section 9 |
| n1-n9 | NIT | various | t_n >= 0 documented, not enforced (potentials.py:415 vs 450-455); R2-B's x_s not asserted on a pixel centre (test_rung2_bragg.py:138-149); the rounded-key `check` of `translation_pair` is False for every pair incl. the legacy one (null_test_cases.py:152-163, pre-existing); the KD-tree method of test_atomistic_translation.py reports a false mismatch for [100] (non-periodic in z); stale "rung 2 NOT RUN" texts (smoke_case.py:3, test_smoke_atomistic.py:6, run_torus_multislice.py:7, README_HPC.md:139, README_ALLIANCE.md:15); E1's line count of the H5 diff (8/6, not 6/5); margin 0 accepted (kit.py:357); engine and reference share constants and the read-out shares `propagator_phase` with the engine (inherent); the reference angle uses the engine's own lambda from the exit wave (ladder_cases.py:267, 278) where `reflection_amplitude_K(2 pi f)` would avoid the coupling |

## Verdict table (orchestrator's items)

| item | question | verdict |
|---|---|---|
| 1 | ContinuumPeriodicPotential: required inputs, point sampling, harmonics vs band, byte identity at V_g = 0, phase origin x_s | CONFIRMED (29,646 byte comparisons, 0 differences; point samples exact; origin exact); NIT t_n |
| 2 | R2-A: reference imported, criteria (a) 1.5e-3 / (b) 2e-4 rad unchanged, x_s on pixel centres, per-bin guard >= 2; fails for a wrong engine | CONFIRMED; 11 deliberate breaks all caught (V_g +-1 %, propagator sign, exact-kernel sign, exact->Fresnel, half-pixel cosine origin / truncation / crystal / read-out plane, sigma x 1.001, V0 + 5 mV at r = 0.05) |
| 3 | VALIDATION_STATUS wording | rung 1 and rung 2 (R2-A) JUSTIFIED; rung 3 qualified correctly in VALIDATION_STATUS but OVERSTATED in engine.py docstring, run_study.py and study_depth100.yaml (S-1); "rocking curve NOT RUN" stale (S-2) |
| 4 | null-test redesign: required depth/azimuth, legacy 21 A, [100], resolved read-out vs known answer, study_depth100 content, study.yaml unchanged | inputs, [100] (exact translation, exact tiling), study.yaml (17/17 byte-identical builds), study_depth100 content (24 points, r >= 0.05, 100 A, E7 M3 header) CONFIRMED; resolved read-out CORRECT on a known answer (moved beam 5e-8 rad; abs E_A = abs R_exact to 8e-5) but the study as configured cannot use it (N-1, N-2 MAJOR; N-3) |
| 5 | blocked exponentials: byte identity (stepped, large-ny, large-nx cells), memory_model vs tracemalloc, pinned unblocked cases | CONFIRMED (0 differences incl. a full run at the default block; model/measured 1.0001-1.0019; pinning legitimate); B-1 MINOR |
| 6 | kit --gpu-mem-from-dry-run: margin, SHA-256, override, --report-json | margin required, SHA and variant checked, report written: CONFIRMED; K-1, K-2 MINOR |
| 7 | H5 script edit signature-only | CONFIRMED (8 insertions / 6 deletions, all call signatures) |
| 8 | no test or tolerance weakened | CONFIRMED |
| 9 | orchestrator's `device_peak_ge_H5_pixel_term` | true but VACUOUS (Z-1 MINOR); E1's proposed blocked H5 bound is sound and passes all rows |
| suites | tests/forward, tests/hpc, full suite in the worktree | tests/forward 114 passed, 1 skipped; tests/hpc 116 passed, 5 skipped; full suite 1130 passed, 6 skipped (all skips optional R2-B or shellcheck absent); smoke test within 120 s; earlier failures were environmental (no venv in a worktree), section 10 |

## 1. ContinuumPeriodicPotential (potentials.py:403-543)

Read in full (potentials.py:60-81 `_phase_factors`, 336-560; engine.py:209-246; grid.py:141-204).

* Required inputs: every keyword of `__init__` (potentials.py:430-431) is required (no defaults);
  refusals for missing/unlabelled V0 and harmonics, non-triples, g <= 0, non-finite values,
  duplicate g, surface profile other than "sharp", more than one terrace, non-continuum cell
  (potentials.py:432-466). CONFIRMED by reading and by E1's `test_required_inputs_and_refusals`
  (run, passes). t_n is not restricted to t >= 0 (docstring says "t_n >= 0"); harmless (periodic),
  NIT.
* Point sampling and phase origin: `profile_V` (potentials.py:481-488) evaluates
  V0 + sum 2 V_n cos(2 pi g_n (x - x_s + t_n)) at `grid.x_A()` = j dx (x0 = 0, grid.py:68-69), i.e.
  at the pixel centres of the crystal-fraction convention (`_continuum_crystal_fraction`,
  potentials.py:378-398, pixel j = [x_j - dx/2, x_j + dx/2]); x_s is the single terrace's
  `surface_x_A`, the same s the crystal fraction uses. A6 check (`check_periodic_identity.py`):
  sub-pixel surface (fraction 0.792213), t = 0 and 0.25: max |V - f (V0 + 2 V_g cos(2 pi g (x_j - x_s
  + t)))| = 0.00e+00 V over 3000 px; profile(x_s - t) = V0 + 2 V_g exactly; realised-harmonics fit
  V0 12.000000000000, V_g 1.000000000000, sin term 1e-16. CONFIRMED.
* Harmonics vs band limit: `band_harmonics_per_A()` (potentials.py:475-479) returns (g, 0) per
  harmonic; `reflection_setup` merges them into `reflections_per_A` of `check_band`
  (engine.py:214-219), which refuses (g_x/fx_max)^2 > 1 (grid.py:181-194). E1's test refuses 3.4
  1/A at dx 0.1 A (fx_max 3.33 1/A). CONFIRMED. Only the declared g is asserted (the transmission
  function's own higher harmonics n g are cut by the 2/3 aperture, as for atomic cells).
* Byte identity with the rung-1 class at V_g = 0: A6 check over 36 cell/grid/absorption/harmonic
  combinations E1 did not use (ny 1, 3, 8; nx 1001, 1437, 2048; surface at 35.0, 35.0137, 50.00001 A;
  r 0, 0.05, 0.1; harmonics (), ((g,0,0),), ((g,-0.0,0.2),(2g,0,0),(3g,0,0.37))), `complex_potential`
  and all 30 realised slices in complex64 and complex128: 29,646 comparisons, 0 differences.
  CONFIRMED.

```
PYTHONPATH=<wt> venv/bin/python <scratchpad>/check_periodic_identity.py
identity checks: 29646 comparisons, 0 differences
t = 0.0: profile at x_s - t = 14.000000000000 V (V0 + 2 V_g = 14); ...
   point-sampled at x_j = j dx (x0 = 0.0): max |V - f (V0 + 2 V_g cos(2 pi g (x_j - x_s + t)))| = 0.00e+00 V over 3000 px; boundary pixel fraction(s) [0.792213]
t = 0.25: ... max |...| = 0.00e+00 V ...; realised V0 12.000000000000, V_g cos 1.000000000000, sin -1.06e-16
```


## 2. Test R2-A (tests/forward/test_rung2_bragg.py, ladder_cases.py:170-292)

Read in full. Against P2 8.2-8.4 and E7 M1-M3:

* Reference: `ladder_cases.rung2_reference()` (ladder_cases.py:186-199) loads
  `tools/physics_checks/rung2_reference.py` by path and calls its `reflection_amplitude(asin(lambda
  f), 200, V0, [V_g], g, r, plane_offset_A=0, model="exact" | "engine_exact_propagator")`
  (ladder_cases.py:278-280, with lambda from the exit wave, 267) and `darwin_plateau` (theta, K_c, |U_g|). Nothing is re-derived; eta is
  computed from P2's K_c and |U_g| as P2 8.3 defines it. CONFIRMED.
* Cell, beam and run parameters equal P2 8.2 (one terrace, extent_y 10 A, ny 1, absorbers 15/10 A
  100 V sin^2, entrance 10 A, H 24 A, edge 4 A, x_bottom = x_s + 2 A, theta = P2's two-beam centre
  16.134773 mrad, Z_e 5000/10000 A after the top-edge contact, vacuum H + 2 + L tan(theta) + 150 A,
  dz 1 A, 2/3 band, complex128, buildup 20 A; D 100/150 A). The only departure is E7 M1's
  `extent_multiple_A` rounding (top absorber >= 10 A takes it). CONFIRMED.
* Criteria unchanged: (a) `T_A = 1.5e-3` over |eta| <= 3, both r, both propagators with the right
  reference model (test_rung2_bragg.py:42, 81-92); (b) `T_PROP = 2e-4` rad over |eta| <= 0.9, same
  bins asserted with `np.array_equal` (95-107); (c) E7 M1 per-bin guard `ec >= 2 ef` over |eta| <= 3,
  equal extent and identical bin frequencies asserted (110-122); x_s on a pixel centre asserted
  for every R2-A run in `_run` (58-63; x_j = j dx with x0 = 0, grid.py:68-69, 101-107). R2-B is
  optional and skipped by default (138-149; it does not go through `_run`, so its pixel-centre
  position is not asserted: NIT, R2-B is qualitative). Non-vacuity guards (>= 10 bins, bins at
  eta < -1 and > 1, >= 4 inside |eta| <= 0.9) (75-78). CONFIRMED.
* Deliberately broken engine (A6 `r2a_perturb.py`: monkeypatches applied in-process, then E1's test
  functions called; the code under audit is not edited). Numbers are the test's own printed lines.

| perturbation (engine side unless stated) | (a) max abs(dR), r 0.1 F / X; r 0.05 F / X (T_A 1.5e-3) | (b) max dev (2e-4 rad) | (c) per-bin ratio range (>= 2) | tests failing |
|---|---|---|---|---|
| none (baseline) | 4.557e-4 / 4.618e-4; 5.172e-4 / 5.263e-4 | 5.07e-5 | 3.05-6.50 | none (7/7 pass; = E1's numbers) |
| V_g x 1.01 | 2.78e-3 / 2.74e-3; 4.38e-3 / 4.31e-3 | 5.09e-5 | 0.58-1.42 | (a) x4, (c) |
| V_g x 0.99 | 2.93e-3 / 2.97e-3; 4.42e-3 / 4.49e-3 | 5.06e-5 | 0.63-1.46 | (a) x4, (c) |
| propagator phase sign flipped (both kernels) | 3.46e-1 / 3.46e-1; 5.41e-1 / 5.41e-1 | 5.7e-2 | 1.00-1.00 | (a) x4, (b), (c) |
| sign of the "exact" kernel only | 4.56e-4 (F, passes) / 3.46e-1; 5.17e-4 (F) / 5.41e-1 | 3.14 | 3.05-6.50 | (a) X x2, (b) |
| "exact" kernel silently replaced by Fresnel | X: 5.16e-3; 1.41e-2 | 1.56e-2 | not run | (a) X x2, (b) |
| cosine origin at x_s + dx/2 | 3.93e-2 / 3.93e-2; 6.29e-2 / 6.29e-2 | 3.02e-5 | 2.01-2.03 (passes) | (a) x4 |
| truncation (crystal fraction) at x_s + dx/2 | 1.10e-2 / 1.10e-2; 1.41e-2 / 1.41e-2 | 8.15e-5 | 1.94-2.01 | (a) x4, (c) |
| whole crystal at x_s + dx/2 | 3.49e-2 / 3.49e-2; 5.47e-2 / 5.47e-2 | 5.89e-5 | 1.98-2.00 | (a) x4, (c) |
| read-out plane x_s + dx/2 (test side) | 3.49e-2 / 3.49e-2; 5.44e-2 / 5.44e-2 | 5.07e-5 | 1.96-1.99 | (a) x4, (c) |
| sigma x 1.001 | 2.43e-3 / 2.44e-3; 5.72e-3 / 5.70e-3 | 5.63e-5 | 0.59-2.23 | (a) x4, (c) |
| V0 + 5 mV (E7 m1) | 8.15e-4 / 8.49e-4 (PASS); 1.94e-3 / 1.99e-3 | 5.27e-5 | 0.44-3.19 | (a) r 0.05 x2, (c) |

Every perturbation is caught, each by the criterion designed for it; (d) (realised potential and
band record) passes throughout because the perturbations act after the record is made (by design of
the experiment). The x_s pixel-centre assertion cannot catch engine-side offsets (it checks the
test's geometry, as E7 M1 intended). Observations, not defects: (c) sits exactly at its threshold
for errors that are first order in dx (half-pixel offsets give ratios 1.94-2.03, pass or fail by a
few per cent), so it is a guard against a non-converging discretisation, not a detector of offsets;
(a) does not detect V0 errors below about 4-5 mV (V0 + 5 mV passes at r = 0.1, fails at r = 0.05),
exactly as E7 m1 states. The reference and the engine share `reflection_holo.constants` (lambda,
sigma) and the read-out shares `propagator_phase` with the engine; a wrong physical constant common
to both would not be seen (P2 1 states the constants are shared; NIT, inherent to the design).
Verdict on R2-A: it tests what P2 8 specified with E7's corrections; it cannot pass for any of the
wrong engines tried. CONFIRMED.

```
PYTHONPATH=<wt> venv/bin/python <scratchpad>/r2a_perturb.py <name> <wt>   (11 runs, 02:06-02:31 UTC, load 3-9)
baseline: 7 PASS
R2-A r = 0.1, fresnel: 18 bins |eta| <= 3.0, max |dR| = 4.557e-04 (T_A = 0.0015), max |d arg| = 1.906e-03 rad
R2-A r = 0.05, exact: 24 bins |eta| <= 3.0, max |dR| = 5.263e-04 (T_A = 0.0015), max |d arg| = 1.728e-03 rad
R2-A (c) guard, r = 0.1, Fresnel, 18 bins: per-bin |dR(0.05)|/|dR(0.025)| from 3.05 to 6.50 (>= 2.0); ...
vg_x1.01: R2-A r = 0.1, fresnel: ... max |dR| = 2.776e-03 (T_A = 0.0015) -> FAIL
harmonic_origin_half_pixel: R2-A r = 0.05, fresnel: ... max |dR| = 6.289e-02 -> FAIL
V0_plus_5mV: R2-A r = 0.1, fresnel: ... max |dR| = 8.154e-04 -> PASS; r = 0.05, fresnel: 1.937e-03 -> FAIL
```


## 3. VALIDATION_STATUS and the other status strings

Read: engine.py:13-17 (module docstring), 47-54 (`VALIDATION_STATUS`, copied into every
ExitWave), run_study.py:23-24, study_depth100.yaml:27, scripts/torus/run_torus_multislice.py:42-44;
docs/05 4.4 items 1-3; tests/forward/test_rung1_refraction.py, test_rung3_null.py (read),
test_atomistic_translation.py.

* Rung 1 "pass": justified (test_rung1_refraction.py, unchanged; run in the suites below).
* Rung 2 "test R2-A ... pass": justified and correctly scoped in `VALIDATION_STATUS` (R2-A named,
  absorbing r = 0.1 and 0.05 only, R2-B optional/qualitative); the tests pass here (section 2) and
  fail for every deliberately broken engine that exceeds P2's stated sensitivity.
* Rung 3 "pass": docs/05 4.4 item 3 defines rung 3 as the null tests INCLUDING the gate "every
  multislice setting used for step phases must first pass this fixed-beam translation check, with a
  sourced absorption (item 21) and a cell several build-up lengths longer than the first-contact
  point". What passes in tests/forward is (i) the continuum terrace null tests (test_rung3_null.py)
  and (ii) the atomistic MOVED-beam translation (test_atomistic_translation.py); the atomistic
  FIXED-beam translation is asserted to FAIL (`test_fixed_beam_translation_is_not_converged_at_minimum_buildup`,
  |err| > 1e-2) and the redesigned study that would test it has not run (and cannot pass its
  resolved read-out as configured, N-1). `VALIDATION_STATUS` (engine.py:52) qualifies rung 3 as
  "(continuum null tests)", which is accurate; but the engine's module docstring (engine.py:13-15:
  "Ladder rungs 1 and 3 (M2 report) and rung 2 test R2-A ... pass"), run_study.py:24 ("ladder rungs
  1, 2 (R2-A) and 3 pass") and study_depth100.yaml:27 ("rungs 1, 2 R2-A, 3 pass") drop the
  qualifier, the last two in the very files whose purpose is the unpassed atomistic fixed-beam part
  of rung 3. MINOR (S-1): wording overstates rung 3; fix: "rung 3: continuum null tests and the
  atomistic moved-beam translation pass; the atomistic fixed-beam translation gate (docs/05 4.4
  item 3) NOT PASSED".
* "the atomistic flat-surface rocking curve against a dynamical solver were NOT RUN"
  (engine.py:53-54): S5 ran exactly that comparison (docs/agent_reports/S5_independent_rheed_solver.md,
  committed in 872e949 before 67f3bf5; section 9: engine within S5's declared tolerance at 22 of 23
  angles at [100] and 15 of 15 at [110], |R| 1-13 % low), and E8 is reviewing it. "NOT RUN" is
  stale; "run by S5, under review (E8), not a pass" would be accurate. MINOR (S-2; the orchestrator
  may have told E1 to leave S5 out: not verified).
* Stale "rung 2 NOT RUN" text left in tests/forward/smoke_case.py:3, test_smoke_atomistic.py:6,
  scripts/torus/run_torus_multislice.py:7, scripts/hpc/README_HPC.md:139,
  scripts/hpc/alliance/README_ALLIANCE.md:15 (E1 lists some of these as not edited). NIT.

## 4. Null-test redesign (null_test_cases.py, run_study.py, study.yaml, study_depth100.yaml)

Read in full: null_test_cases.py (diff and whole file), run_study.py, both study files, README, the
new test file, test_atomistic_translation.py; H2 2.2, 2.4, N12, section 12 step 3.

* Required clean depth and azimuth: `translation_pair` and `step_case` take `clean_depth_A` and
  `azimuth` as keyword-only arguments without defaults (null_test_cases.py:124, 345);
  `_clean_depth(None)` refuses (56-63); `_azimuth` refuses anything but "110"/"100" (49-54);
  `LEGACY_M2_CLEAN_DEPTH_A = 21.0` is explicit and documented as shallower than the extinction
  depth (40-41, module docstring 6-12); run_study.py refuses a point without either key
  (POINT_KEYS, 55; checks 121-131) and a file without `build.tile_above_periods` (108-110).
  CONFIRMED (and E1's `test_case_functions_require_clean_depth_and_azimuth` passes).
  Not required: the beam height H, edge and gap of the null-test sheet beam are still silent
  defaults of `translation_pair` (H = 8 A, edge 2 A, gap 2 A; null_test_cases.py:124-125) and are not
  keys of the study files; this matters for the resolved read-out (finding N-1 below).
* [100] support: `AZIMUTHS["100"]` (uvw (1,0,0), period a, dz = a/4). A6 checks
  (`check_azimuth_tiling.py`, `check_lc.py`): tiling one period (tile_above_periods = 0, as
  study_depth100.yaml) equals the direct build for flat and stepped staircases at both azimuths
  (identical atom sets and cells); the [100] pair at clean depth 100 A is an exact translation
  B = A + R with the builder's R = (a/2, 0, -a/2) (max distance 2.3e-13 A, KD-tree periodic in y and
  z); dz 1.35773 A = a/4; grid 1250 x 84 as in E1's estimate. CONFIRMED. Side observation
  (pre-existing M2 code, not E1's): the rounded-key `check` returned by `translation_pair`
  (null_test_cases.py:152-163) is `identical_sets: False` for EVERY pair, the legacy M2 pair included
  (whose exact translation `test_translated_crystal_is_the_builders_crystal` confirms), so that
  field is uninformative; nothing asserts it. NIT. Also: the KD-tree method of
  test_atomistic_translation.py (tree non-periodic in z) reports a false 2.35 A mismatch for the
  [100] pair; it is correct only for the [110] geometry it is used on (NIT, only relevant if that
  test is extended to [100]).
* study.yaml numerically unchanged: A6 `study_points_fingerprint.py` builds every point with the
  tree's own `run_study._build` in an export of a1ef2a0 and in the 67f3bf5 worktree (hashes of all
  atom positions and species, box, layout numbers, both beams, MultisliceParams, R, absorption):
  17/17 points byte-identical (`diff` of the two outputs empty). CONFIRMED.
* study_depth100.yaml content: 24 points (8 [110] fixed, 8 [100] fixed, 2 moved, 6 [110] steps),
  every point clean_depth_A 100.0, absorption 0.05 or 0.1 with TEST_ONLY labels, [100] fixed-beam
  points at bragg_0008_mip, header lines 4-12 state 65 A as the reviewed minimum, 100 A as a margin
  and r >= 0.05 because no depth converges r = 0 (E7 M3 wording, numbers match E7's table).
  CONFIRMED. Its saved estimate (`study_depth100_estimate_numpy4.txt`) quotes the file's SHA-256
  9423d8ac..., which equals the file at 67f3bf5.

### Surface-resolved read-out against a known answer (A6 `resolved_known_answer.py`)

Case: the rung-2 continuum (ContinuumPeriodicPotential, V0 13.902843 V, V_008 1.035742 V, r = 0.1,
16.134773 mrad, Fresnel, complex128, dx 0.025 A, dz 1 A, L 6000 A, clean depth 100 A) and the same
crystal translated by R = (R_x, 0, 0) in an identical box, read with `resolved_translation` and the
study_depth100 parameters. Known answers (derivation: B = A translated and the incident envelope
translated with a fixed carrier give psi_B(r) = exp(i k_in.R) psi_A(r - R); demodulating by
exp(-2 pi i f_c x) and mapping x to z_s with each cell's own x_s gives E_B(z_s) = E_A(z_s)
exp(-i (k_out - k_in).R) exactly for the moved beam; with the beam fixed, the same where the
reflection has built up; and in the built-up region |E_A| = |R_exact(theta)| and arg E_A = arg
R_exact - 4 pi f_c x_s - pi lambda L f_c^2 for the Fresnel envelope). With a sheet beam that
illuminates the whole strip (H = L tan(theta) - 6 A, H2 2.4's design):

| case | result | verdict |
|---|---|---|
| moved beam, R_x = 2.7 A (108 px) | every bin err <= 5.3e-8 rad, amp 1.00000 | exact, CONFIRMED |
| moved beam, R_x = a/2 (108.618 px) | every bin err 8.6e-4 to 2.4e-3 rad, amp within 6.1e-4 (sub-pixel step) | CONFIRMED |
| built-up bins (d = 3500-4000 A), A alone | abs E_A 0.33620, 0.33828 vs abs R_exact 0.33836; arg E_A - prediction -2.7e-4, -2.0e-3 rad | CONFIRMED: the read-out returns P2's exact R |
| fixed beam, R_x = a/2 | bins d = 2500-4000 A: err -2.0e-4 to +2.1e-3 rad, amp 0.9955-1.0068 (converged); LAST bin (d 4500, partial 458 A): amp 1.029, so `converged_beyond_A` = None | see N-2 |

The mapping, the pairing by own x_s, the phase convention and the bins are therefore right.

### N-1 (MAJOR). study_depth100.yaml's translation points cannot show convergence in the resolved read-out: the 8 A sheet beam illuminates only ~500 A of surface

`run_study._build` (run_study.py:81-85) calls `translation_pair` without H, edge or gap, so every
translation point of study_depth100.yaml uses H = 8 A, edge 2 A, gap 2 A
(null_test_cases.py:124-125). The footprint is H/tan(theta) = 496 A (bottom-edge contact 124 A,
top-edge contact 620 A). H2 2.4's read-out, which E1 adopted, maps exit-plane height to the surface
point and presumes the surface is lit up to the exit plane (H2 2.4: "sheet beam ... whose top
edge lands 1 A before the exit plane (H = L tan(theta) - 3 A)"). Downstream of the footprint there is
no steady state: E_A(z_s) is the decaying tail of the Bragg-case field, never close to R(theta). In
the fixed-beam pair the footprints are 168 A apart, so the ratio of tails is not
exp(i expected) at any z_s. Reproduction (`resolved_beamheight.py <wt> r L H edge`, same continuum
case, H = 8 A, edge 2 A as the study):

```
r = 0.1, L 6000:  max |E_A| 0.078 (|R_exact| 0.338); fixed beam amp ratio 0.69-0.89 from d = 1000 A on; converged_beyond_A None
r = 0.1, L 11000: fixed beam amp 0.15-11.9, err up to 2.9 rad; |E_A| 1e-5-1e-4 beyond d = 5000 A; converged_beyond_A None
                  MOVED beam (covariant control): bins at d >= 5000 A have |E_A| 4e-5-2e-4 and err up to -1.8e-2 rad, amp 1.035: converged_beyond_A None
r = 0.05, L 11000: fixed beam amp 0.15-11.9 (d >= 4000 A); moved beam err -5.05e-2 rad in bin d = 9000 A (|E_A| 1e-5): converged_beyond_A None
```

Consequences: for a CORRECT engine and an exactly translation-covariant crystal, every fixed-beam
point of study_depth100.yaml (16 points, L up to ~11 400 A) will report `converged_beyond_A: None`,
and the two moved-beam controls, which the file says "must match -(k_out - k_in).R in every bin"
(study_depth100.yaml:62), will also fail because their far bins sit at the noise floor. E1's one
end-to-end point (tfix110_bragg_abs10_L0: amp 1.397, None) was read as "not converged ... as the
build-up lengths predict (P2 5.3: >= 2600 A at r = 0.1)"; P2 5.3's lengths assume continuous
illumination, which these cells do not have. The HPC study would spend its ~213 GPU-s (and
~53 000 CPU-s) producing a surface-resolved verdict that is undefined by construction. The
x-summed M2 measurement is not affected by N-1 (it is the Fourier component at f_c of the whole exit plane, `specular_component`, null_test_cases.py:186-195). Fix: make H, edge and
gap required keys of the study files and of `translation_pair`; for surface-resolved points use a
beam whose top edge lands before the exit plane (H = L tan(theta) - a few A, which roughly doubles
the vacuum: re-estimate); and see N-2.

### N-2 (MAJOR). `converged_beyond_A` has no amplitude floor and fails on the last bin

`resolved_translation` (null_test_cases.py:229-294) declares the whole point unconverged (`None`)
if the LAST bin fails (lines 280-285), and compares bins whatever their amplitude. The last bin
(ending exit_excl_A = 750 A before the exit plane, rays 12-20 A above the surface) is where the
pass band and the vacuum-window edge contaminate the field (H2 2.4: the last 500 A are off by
0.04 rad) and, in the fixed-beam case, where the end of B's illumination (168 A earlier than A's)
is within two read-out resolution elements (310 A each; a likely cause, not isolated). Reproduction: the strip-long-beam fixed
case above, converged to <= 2.1e-3 rad and <= 6.8e-3 in bins d = 2500-4000 A, returns None
because its last, partial bin has amp 1.029. With the study's 8 A beam, bins with |E_A| ~ 1e-5 at
the noise floor decide the verdict (N-1). Fix: exclude or flag bins whose |E_A| is below a stated
fraction of the plateau (or of max |E_A|), report the last bin separately, and state the verdict
over a declared window (H2 2.4 used a reference window before the exit margin); the exit margin
should be at least H2's 3-resolution-element 1115 A (H2 2.6) rather than 750 A.


## 5. Blocked structure-factor exponentials (potentials.py:59-81, 325-326; engine.py:468-517)

* Byte identity, A6 `check_blocked_identity.py` (reference = E1's verbatim copy of the old
  `projected`, `test_potential_blocked_exponentials._projected_before`, checked against
  `git show a1ef2a0:reflection_holo/forward/multislice/potentials.py` lines 299-310 by reading):
  (1) `_phase_factors` for rows 1..24000 (incl. 2047, 2048, 2049, 4097, 5003), n 1..101, blocks
  1..1024 and the default, complex64/128: 1792 comparisons, 0 differences; (2) every compared
  non-empty slice of a STEPPED [110] cell (step_case w4, 640 x 240 px, blocks 7 and 100: 60 slices
  each), of a LARGE-NY [100] cell at the DEFAULT block (432 x 2520 px; complex64 r = 0.1, complex128
  r = 0, complex64 frozen phonons) and of a LARGE-NX cell at the default block (2304 x 84 px, Ex
  blocked): 0 differences; (3) full run of the large-ny cell at the default block against the old
  `projected`: exit waves byte-identical. CONFIRMED (numpy/CPU only; the cupy path is UNVERIFIED on a
  GPU, as E1 states).

```
PYTHONPATH=<wt> venv/bin/python <scratchpad>/check_blocked_identity.py <wt>
(1) phase factors: 1792 comparisons, 0 differences (13 s)
(2) stepped [110] w4 c64 r=0.1 (nx 640, ny 240): grid 640 x 240, block 7, 60 non-empty slices compared, 0 differ
(2) stepped [110] w4 c64 r=0.1 (nx 640, ny 240): grid 640 x 240, block 100, 60 non-empty slices compared, 0 differ
(2) large-ny [100] complex64 r=0.1 phonons=False: grid 432 x 2520, block 1024, 8 non-empty slices compared, 0 differ
(2) large-ny [100] complex128 r=0.0 phonons=False: grid 432 x 2520, block 1024, 8 non-empty slices compared, 0 differ
(2) large-ny [100] complex64 r=0.1 phonons=True: grid 432 x 2520, block 1024, 9 non-empty slices compared, 0 differ
(2) large-nx [100] complex64 r=0.1: grid 2304 x 84, block 1024, 8 non-empty slices compared, 0 differ
(3) full run large-ny cell, default block: exit waves byte-identical: True
TOTAL differences: 0
```

* memory_model vs tracemalloc on blocked cases E1's tests do not measure (A6 `check_memory.py`,
  E1's `_measured_peak` and TOL = 2 %):

```
large-nx (Ex blocked) c64 r=0.1: grid 2304 x 84, n 170, stage exponentials; measured 19,851,691 B, model 19,813,394 B, ratio 1.0019 (TOL 0.02)
large-ny (Ey blocked) c128 r=0.1: grid 432 x 2520, n 840, stage pixel; measured 223,974,832 B, model 223,958,944 B, ratio 1.0001 (TOL 0.02)
large-nx and large-ny c64 r=0.1: grid 2304 x 2520, n 5100, stage exponentials; measured 696,716,799 B, model 696,680,740 B, ratio 1.0001 (TOL 0.02)
```

  CONFIRMED (Ex-blocked branch, complex128 blocked branch, and both blocked).
* MINOR (B-1). The claim in `_phase_factors`' docstring (potentials.py:70-72), in E1's report (E1_engine_wave2a.md:235-237) and in
  `test_default_block_is_used_only_where_it_saves_memory`'s docstring
  (test_potential_blocked_exponentials.py:99: "32 m n <= cb m n + 32 B n there for cb <= 16") that
  up to 2 x EXP_BLOCK_ROWS rows the unblocked form needs less memory is false for complex64: 32 m <
  8 m + 32 B only for m < 4B/3 = 1365 rows. Measured (A6 `check_memory.py`, tracemalloc of
  `_phase_factors` alone, 2048 x 2000, complex64): unblocked (default) 131,072,224 B = 32.00 B per
  element; blocked (block 1000) 96,768,432 B = 23.63 B per element. Consequence: complex64 grids with
  1366-2048 rows keep a peak up to 25 % higher in that stage than necessary; no numerical effect, and
  E1's statement "no grid gets a larger peak" is true. Fix: threshold max(B, ceil(32 B/(32 - cb)))
  or correct the docstrings.


## 6. Kit `--gpu-mem-from-dry-run` and `pipeline dry-run --report-json`

Read in full: kit.py diff (88-104, 338-407, 518-529, 598-609, 631-680, 764, 959-960), submit.sh diff,
dry_run_job.py diff, pipeline/__main__.py:62-76 and 121-132 (E1's `--report-json`), the new test
file.

* Required margin: refused when absent (kit.py:352-356), negative, NaN or >= 100
  (357-358); `--gpu-mem-margin` without the report refused (600-601); CPU jobs, smoke, gpu-check and
  the dry-run job itself refused (602-605). CONFIRMED by reading and by the tests (section 10).
  A margin of exactly 0 is accepted, which turns the derived need into the model's documented LOWER
  BOUND (no workspace, no pool). NIT (stated and recorded, but a 0 margin could be refused or
  warned).
* SHA-256 check: the report's `config_sha256` must equal the SHA-256 of the submitted
  configuration file and the variants must match (kit.py:366-373). The pipeline configuration is a
  single self-contained YAML (config.py:1099-1105 loads one file), so the file hash covers the
  inputs. It does NOT cover the code: the report records no git commit, and the kit does not compare
  the dry run's engine code with the submission's `engine_code` record. A memory-model change
  between the dry run and the submission (as E1's own task 3 was) goes undetected. MINOR (K-1);
  fix: write `git rev-parse HEAD` (and dirty state) into the report and refuse or warn on mismatch.
* Override semantics: an explicit `--need-gpu-mem-gb` replaces the derived need even when it is
  SMALLER, with only a NOTE (kit.py:638-642; E1's test asserts return code 0 for 30 GB against a
  derived 50 GB, test_kit_gpu_mem_from_dry_run.py:71-74). A smaller explicit value than the
  model's lower bound (device peak without margin) is almost certainly an error; it should at least
  be a WARNING. MINOR (K-2).
* Host memory: WARNING (not refusal) when `--mem` is below cupy host peak + 48 B/atom
  (kit.py:670-676); consistent with H7 4. CONFIRMED.
* `dry-run --report-json` (pipeline/__main__.py:124-132) writes schema, absolute config path,
  SHA-256, variant and the full report; stdout unchanged. CONFIRMED.

## 7. tools/hpc/review_h5_recompute.py

`git diff a1ef2a0 67f3bf5 -- tools/hpc/review_h5_recompute.py`: 8 insertions, 6 deletions, all
call signatures: `working_reflections_hkl=((0, 0, 8),)` in three `MultisliceParams(...)` calls
(lines 437, 570, 692), `clean_depth_A=21.0, azimuth="110"` in `translation_pair`/`step_case`
(730-735), `reflections_per_A={}` in the direct `check_band` call (943-944). No number, tolerance,
check or print changed. The (0,0,8) band assertion is inert on H5's grids (dx <= 0.13 A; fx_max
>= 2.56 1/A > g_008 = 1.473 1/A). Signature-only: CONFIRMED. (E1's report says "6 insertions,
5 deletions"; the diff has 8 and 6: NIT.) The script's report mode fails 5/13 checks by design
(they pin H5's pre-H7 replica); not rerun here (NOT RUN).

## 8. Existing tests and tolerances

`git diff a1ef2a0 67f3bf5 -- tests/` restricted to E1's files (ladder_cases.py, null_test_cases.py,
test_atomistic_translation.py, test_memory_model.py) removes no assertion and changes no tolerance
(the only removed `assert` line in tests/ is E2's, test_si001_options.py). test_memory_model.py:
TOL = 0.02 unchanged; the two pre-existing cases that measure the unblocked exponential stage
("wide/exponentials" and `test_wide_slice_needs_the_complex128_temporaries`) now set
`potentials.EXP_BLOCK_ROWS = 4096` (lines 122-127, 148). Legitimate: engine (potentials.py:74) and
model (engine.py:471) read the same module constant at call time, the unblocked path remains the
production path for <= 2048 rows, and the blocked default is measured by the two new tests plus A6's
three extra cases (section 5, ratios 1.0001-1.0019). test_atomistic_translation.py: the covariant
pair moved into a module fixture; its assertions are unchanged. CONFIRMED: nothing weakened.

## 9. Orchestrator's check `device_peak_ge_H5_pixel_term_<row>` (supercell_sizing.py:1735-1743)

The replacement check is `mr["device"] >= 48 * npx`. It is TRUE but VACUOUS: engine.memory_model's
device peak is `dev_pers + in_loop` with `dev_pers >= (3 cb + 2 rb) px` (propagators, entrance
wave, mask, one scattering factor) and `in_loop >= 3 cb px + (3 cb + rb) px`
(engine.py:503-525), i.e. >= 84 B/px for complex64 and >= 168 B/px for complex128 for ANY input,
so no row can ever fail 48 B/px. A6 `sizing_check_audit.py`: (a) minimum device peak per pixel over
probes including n = 0 atoms: 84.00 B/px (complex64), 168.00 B/px (complex128); (b) report mode rerun
(exit 0, "60/60 checks pass") with every scenario row recorded: device/48px between 1.83 and 2.98.
H5's measured model with the BLOCKED stage, 48 px + max(E(nx), 8 nx n + E(ny)) (E1's proposal),
is a non-trivial bound that the engine model meets for all 22 rows (e.g. 2a_a2: 7.731 GB model vs
6.285 GB bound; torus r = 0.05: 8.665 vs 6.671 GB; model/bound between 1.23 (2a_a2) and 1.51
from the printed GB values). MINOR (Z-1): the self-check count "60/60" includes 11 checks that cannot fail; replace
the pixel term by the blocked H5 formula.

```
PYTHONPATH=<wt> venv/bin/python <scratchpad>/sizing_check_audit.py <wt>
(a) minimum model device peak per pixel over the probes: complex64 84.00 B/px, complex128 168.00 B/px (the check compares with 48 B/px)
(b) report mode exit status 0; last line: 60/60 checks pass; runtime 42 s
    2250 x 24000, n 15211, complex64: 7.731 | 2.592 (dev/48px 2.98) | 14.548 (<) | 6.285 (PASS)
    3969 x 17640, n 16098, complex64: 8.665 | 3.361 (dev/48px 2.58) | 12.959 (<) | 6.671 (PASS)
    (columns: model device GB | 48 px | H5 unblocked | H5 with blocked E; all 22 rows PASS the last)
```

## 10. Test suites in the worktree (67f3bf5)

Environment note. The worktree has no `venv/`; the Alliance kit and its emulated jobs require
`<repo>/venv/bin/python` and check `realpath(sys.prefix) == readlink -f <repo>/venv`
(scripts/hpc/alliance/job.sbatch:88-91), and the run manifest refuses an untracked path it cannot
hash. Final arrangement (no repository file touched, nothing installed): `<wt>/venv` = symlink to
`/home/user/Holography/venv`, hidden from git by an ENVIRONMENT-scoped excludes file
(`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.excludesFile GIT_CONFIG_VALUE_0=<scratchpad>/a6_git_excludes`).
Earlier attempts, recorded because their failures are environmental and not E1's:

| run | arrangement | result |
|---|---|---|
| tests/hpc (02:15:10-02:18:29) | no venv in the worktree | 90 failed, 26 passed, 5 skipped: "venv/bin/python not found: run setup_alliance.sh first" |
| tests/hpc (02:20:14-02:23:50) | venv = symlink to the main venv, no excludes | 4 failed, 112 passed, 5 skipped: the run manifest refuses the untracked symlink (GitStateError, IsADirectoryError on <wt>/venv) and one gpu-check emulation |
| 4-5 targeted reruns (02:24) | venv = directory of links (python, pyvenv.cfg, lib, lib64, then activate) | 3-4 failed: `venv/bin/activate` missing, then "python is not the venv of <wt>" |
| full suite (02:33:37-02:44:27, load 4.4 -> 1.6) | directory of links + activate | 9 failed, 1121 passed, 6 skipped, 12 warnings in 648 s; all 9 = emulated kit jobs refusing with "python is not the venv of <wt>" (job.sbatch:90-91) |
| the 10 env-bound kit tests (02:46) | venv symlink + env-scoped excludes | 10 passed in 30.7 s |
| 5 env-bound tests in the MAIN checkout (02:26) | main repo at dae587c, whose reflection_holo/, scripts/, tests/, tools/hpc/ equalled 67f3bf5 at that moment (`git diff --stat 67f3bf5 -- ...` empty) | 5 passed in 36.7 s |
| 9 env-bound tests in the MAIN checkout (02:45) | main repo at 2038454 with ANOTHER agent's uncommitted edits to reflection_holo/structure/si001.py and reconstruction.py (not 67f3bf5) | 9 passed in 30.3 s; superseded by the worktree run above |

Results with the final arrangement are in the blocks below. `tests/forward` does not use the venv
path and was run once:

```
venv/bin/python -m pytest -q -p no:cacheprovider tests/forward      (02:25:58-02:33:27, load 4.8 -> 5.1)
SKIPPED [1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1
114 passed, 1 skipped in 447.05s (0:07:27)
```

```
venv/bin/python -m pytest -q -p no:cacheprovider tests/hpc          (02:46:29-02:49:38, load 1.0 -> 2.0; final arrangement)
SKIPPED [5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed
116 passed, 5 skipped in 187.82s (0:03:07)
```

(E1 reported the same 116 passed, 5 skipped.)

```
venv/bin/python -m pytest -q -p no:cacheprovider                    (full suite, 02:49:38-03:01:57, load 2.0 -> 4.3; final arrangement)
SKIPPED [1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1
SKIPPED [5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed
1130 passed, 6 skipped, 12 warnings in 736.89s (0:12:16)
```

(E1's full-suite run had 1 failure caused by another agent's registry edit, since resolved; at
67f3bf5 the suite is clean.)

```
RH_RUNG2_R2B=1 venv/bin/python -m pytest -q -s -p no:cacheprovider tests/forward/test_rung2_bragg.py -k r2b   (03:02:12-03:06:18, load 3.6)
R2-B (optional, qualitative) r = 0: 7 bins |eta| <= 0.5, max |dR| = 1.120e-02 (T_B = 0.03); arg R_ref from +1.2212 to +2.0823 rad
  fresnel r-model exact, dx 0.02500 A, nx 38444, 31612 slices, x_s 265.000 A, run 244.7 s
1 passed, 7 deselected in 245.54s (0:04:05)
```

R2-B reproduces E1's 1.120e-2 exactly; its x_s = 265 A = 10600 dx is on a pixel centre, although
the test does not assert it (NIT above). The 120 s wall-time smoke test
(tests/forward/test_smoke_atomistic.py) passed in the tests/forward run and in the 02:33 full
suite; no rerun alone was needed.

## Commands run (log)

All in the worktree `<wt>` = `<scratchpad>/a6_wt` (detached 67f3bf5) with
`PYTHONPATH=<wt>` and `/home/user/Holography/venv/bin/python` (written `venv/bin/python` below),
unless stated. Times UTC, 2026-09-24; the machine (4 cores) was shared; load averages quoted.

```
git -C /home/user/Holography worktree add --detach <scratchpad>/a6_wt 67f3bf5
git diff --stat a1ef2a0 67f3bf5 ; git diff a1ef2a0 67f3bf5 -- <each E1 file>; git show 67f3bf5 --stat
git -C /home/user/Holography archive a1ef2a0 | tar -x -C <scratchpad>/a1ef2a0_tree    (read-only export)
venv/bin/python -c "import reflection_holo; print(reflection_holo.__file__)"   -> <wt>/reflection_holo/__init__.py
venv/bin/python -m pytest -q -p no:cacheprovider tests/forward/test_potential_periodic.py \
    tests/forward/test_null_study_readout.py tests/forward/test_potential_blocked_exponentials.py
                                                        -> 30 passed in 5.48s (02:04, load 2.1)
venv/bin/python <scratchpad>/check_periodic_identity.py              -> exit 0 (section 1)
venv/bin/python <scratchpad>/r2a_perturb.py <name> <wt> [tests]      -> 12 runs, section 2 (02:06-02:34)
venv/bin/python <scratchpad>/check_blocked_identity.py <wt>          -> exit 0, 63 s (section 5)
venv/bin/python <scratchpad>/check_memory.py <wt>                    -> exit 0 (section 5)
venv/bin/python <scratchpad>/resolved_known_answer.py <wt>           -> exit 0 (section 4; a first
    attempt with H = L tan(theta) - 3 A was refused by the engine's footprint assertion for A's
    higher-lying fixed beam, item3_footprint; H = L tan(theta) - 6 A used)
venv/bin/python <scratchpad>/resolved_beamheight.py <wt> 0.1 6000 8 2 ; ... 0.1 11000 8 2 ; ... 0.05 11000 8 2
                                                                     -> section 4, N-1
PYTHONPATH=<scratchpad>/a1ef2a0_tree venv/bin/python <scratchpad>/study_points_fingerprint.py \
    <scratchpad>/a1ef2a0_tree <a1ef2a0_tree>/scripts/hpc/null_test_study/study.yaml > fp_old.txt
venv/bin/python <scratchpad>/study_points_fingerprint.py <wt> <wt>/scripts/hpc/null_test_study/study.yaml > fp_new.txt
diff fp_old.txt fp_new.txt                                           -> empty (17 points identical)
venv/bin/python <scratchpad>/check_azimuth_tiling.py <wt>            -> section 4
venv/bin/python <scratchpad>/check_translation_kdtree.py <wt>        -> [100] false mismatch with the
    non-periodic tree (section 4)
venv/bin/python <scratchpad>/check_translation_search.py <wt> ; check_lc.py <wt>  -> [100] exact translation
venv/bin/python <scratchpad>/sizing_check_audit.py <wt>              -> section 9 (runs the sizing
    tool's report mode in-process: 60/60, 42 s)
venv/bin/python -m pytest -q -p no:cacheprovider tests/hpc           (see section 10)
venv/bin/python -m pytest -q -p no:cacheprovider tests/forward       (see section 10)
venv/bin/python -m pytest -q -p no:cacheprovider                     (full suite, see section 10)
RH_RUNG2_R2B=1 venv/bin/python -m pytest -q -s tests/forward/test_rung2_bragg.py -k r2b  (section 10)
rm <wt>/venv; git -C <wt> status --short (clean); git -C /home/user/Holography worktree remove <wt>
  -> worktree list shows only /home/user/Holography; rm -rf <scratchpad>/a1ef2a0_tree
```

NOT RUN: anything on a GPU or with cupy (the cupy path of `_phase_factors`, the device peaks);
the other modes of tools/hpc/review_h5_recompute.py (`--rerun` 408 s, `--memtime`) and its report
mode; any point of study_depth100.yaml with the atomistic engine (A6's N-1/N-2 evidence is on the
continuum known-answer case, which isolates the read-out); run_study.py `--estimate`; the tighter
R2-A variant (dx 0.0125 A). (R2-B WAS run by A6: section 10.)
