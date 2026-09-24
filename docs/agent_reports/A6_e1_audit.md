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

Status: IN PROGRESS.

## Findings so far (ranked; details in the numbered sections)

(filled in at the end)

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
  (ladder_cases.py:275-277) and `darwin_plateau` (theta, K_c, |U_g|). Nothing is re-derived; eta is
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

(perturbation table below, filled in when the runs end)


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
x-summed M2 measurement is unaffected (it is the exact f_c Fourier component). Fix: make H, edge and
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


## 3. VALIDATION_STATUS and the other status strings

Read: engine.py:13-17 (module docstring), 47-54 (`VALIDATION_STATUS`, copied into every
ExitWave), run_study.py:22-24, study_depth100.yaml:27, scripts/torus/run_torus_multislice.py:42-44;
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
6.285 GB bound; torus r = 0.05: 8.665 vs 6.671 GB; smallest margins about 1.0-1.1 on the thin
flat rows). MINOR (Z-1): the self-check count "60/60" includes 11 checks that cannot fail; replace
the pixel term by the blocked H5 formula.

```
PYTHONPATH=<wt> venv/bin/python <scratchpad>/sizing_check_audit.py <wt>
(a) minimum model device peak per pixel over the probes: complex64 84.00 B/px, complex128 168.00 B/px (the check compares with 48 B/px)
(b) report mode exit status 0; last line: 60/60 checks pass; runtime 42 s
    2250 x 24000, n 15211, complex64: 7.731 | 2.592 (dev/48px 2.98) | 14.548 (<) | 6.285 (PASS)
    3969 x 17640, n 16098, complex64: 8.665 | 3.361 (dev/48px 2.58) | 12.959 (<) | 6.671 (PASS)
    (columns: model device GB | 48 px | H5 unblocked | H5 with blocked E; all 22 rows PASS the last)
```

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


## Commands run (log)

```
git -C /home/user/Holography worktree add --detach <scratchpad>/a6_wt 67f3bf5
git diff --stat a1ef2a0 67f3bf5 ; git diff a1ef2a0 67f3bf5 -- <each E1 file>
PYTHONPATH=<wt> venv/bin/python -c "import reflection_holo; print(reflection_holo.__file__)"
PYTHONPATH=<wt> venv/bin/python -m pytest -q -p no:cacheprovider tests/forward/test_potential_periodic.py \
    tests/forward/test_null_study_readout.py tests/forward/test_potential_blocked_exponentials.py
  -> 30 passed in 5.48s   (load 2.1)
PYTHONPATH=<wt> venv/bin/python <scratchpad>/check_periodic_identity.py      -> exit 0
PYTHONPATH=<wt> venv/bin/python <scratchpad>/check_blocked_identity.py <wt>  -> exit 0 (63 s)
PYTHONPATH=<wt> venv/bin/python <scratchpad>/check_memory.py <wt>
PYTHONPATH=<wt> venv/bin/python <scratchpad>/r2a_perturb.py <perturbation> <wt>   (section 2)
```
