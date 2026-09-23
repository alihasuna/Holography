# S4: fixes of audit A3 (pipeline) and the A2c residuals G1-G3

Status: COMPLETE (priorities 1, 2 and 3), 2026-09-23. Agent S4. Written incrementally; nothing committed or pushed by S4 (the orchestrator snapshotted work in progress as 1154a3a, 0e57dc0, 8c70fc1).
Branch `claude/electron-holography-orchestration-nakd7r`, HEAD `fdabd67` ("Fix the SLURM runner's
random failure under pipefail", A3 M4 already fixed there).
Scratch directory: `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/`
(written `$S` below; before/after test logs in `$S/s4/`).

## Baseline (HEAD fdabd67, unmodified)

`venv/bin/pytest -q`: `646 passed, 6 warnings in 204.78s (0:03:24)`.

Smoke CLI (`--out $S/s4_smoke_0`), exit 0:
```
purpose: demo; not comparable to experiment
engine: geometric model, no dynamical amplitude, B4 scope applies
step field terraces 0->1 (translation): h = +2.7156 +- 0.0117 A (branch -4, wrap period 0.7612 A)
step field terraces 1->2 (screw): h = -1.3576 +- 0.0058 A (branch 2, wrap period 0.7612 A)
step field terraces 2->0 (screw): h = -1.3580 +- 0.0058 A (branch 2, wrap period 0.7612 A)
no-step control: PASS {'performed': True, 'delta_rad': -0.0036868859167245027, 'tolerance_rad': 0.012310012257320535, 'n_sigma': 3.0, 'se_correlated_rad': 0.004103337419106845, 'passed': True, 'n_a': 1960, 'n_b': 2016, 'controls_sigma_uncorrelated_rad': 0.0002516205842901576, 'field_terrace': 1}
outputs in /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/s4_smoke_0: summary.json, manifest.json, arrays.npz quicklook_detector.png quicklook_exit_wave.png
```

## Method for "fails before, passes after"

The new regression tests of each group are run twice: on the fixed tree, and on an extracted copy of
the unmodified code at fdabd67 (`git archive fdabd67` into `$S/s4/before`, with its own throwaway git
repository so that the old manifest code can run, and `venv` linked) with the new test files copied
in. `venv/bin/python -m pytest` from that directory imports the old package (checked:
`reflection_holo.__file__` resolves inside `$S/s4/before`). Full outputs: `$S/s4/p*_before_*.txt`,
`$S/s4/p*_after_*.txt`.

## Priority 1: COMPLETE

### (a) A3 B1: the no-step control gates every height; the branch rule refuses pure noise

Implemented:
* `pipeline/run.py`: the no-step control is computed BEFORE the steps. `_withhold_reason` returns
  "no-step control failed or not performed (failed: delta = ..., tolerance ... = 3 correlated
  standard errors); every height of this run is withheld" (or "(not performed: <reason>)"). It is
  passed to `quantify.measure_steps(withhold_reason=...)` (a required keyword): every measured step
  keeps its phase difference and gets `height: None`, that reason and `heights_withheld: True`.
  `summary.json["height_verdict"]` (also at `quantification.height_verdict` and in the manifest
  `extra`) holds `line`, `withheld`, `heights_returned`. The CLI prints the verdict FIRST, framed by
  a line of asterisks, as `NO HEIGHT: no-step control failed or not performed (...)`; each step
  line then reads `no height: no-step control failed or not performed ...`.
* `pipeline/quantify.py`: the branch rule is now JOINT over the measured steps of a run, because
  the steps share one angle calibration, so the sensitivity error is a common scale
  `s_true = s (1 + eps)`. The rule:
  `phi_i + 2 pi m_i = -s (1 + eps) n_i a/4 + r_i`, `|r_i| <= 3 sigma_phi_i` (measured),
  `|eps| <= 3 sigma_s/s` (correlated sigma_s, item (b)), `1 <= |n_i| <= n_max`. `n = 0` is excluded
  because the two regions straddle a step of the ray-traced geometry (the A3 M1 bullet). A
  consistent assignment is accepted only if it is SIGNIFICANT, i.e. only if an upper bound on the
  probability that K phases carrying no height information (uniform on the circle) pass the rule
  is at most alpha = P(|Z| > 3) = 2.6998e-3, the false-acceptance rate the 3-sigma criterion implies.
  The bound is exact geometry: the zonotope volume (box of half-widths w_i = 3 sigma_phi_i plus
  the eps segment) summed over the (2 n_max)^K assignments, over (2 pi)^K:
  `P_chance = prod_i(2 n_max 2 w_i / 2 pi) [1 + sum_i E s (a/4)(n_max + 1)/(2 w_i)]`,
  with `E = 3 sigma_s/s`. Decisions: "resolved", "not significant", "ambiguous" or "inconsistent".
  The chance bound and alpha are stored in every step's `branch` record and in
  `quantification.joint_branch`.
* Consequence, stated plainly: a SINGLE step can never be certified at the demo angle calibration
  (0.1 mrad): its bound is 0.40 at sigma_phi 0.003 rad. The three demo steps together give
  1.22e-4. A run needs several steps sharing one calibration before the lattice constraint means
  anything. For true lattice steps the rule accepts the right assignment with probability
  `>= (1 - alpha)^(K+1)`.
* This changes the content of the B29 stand-in ("branch from the lattice constraint ... refused
  unless exactly one candidate lies within 3 sigma"). docs/model_assumptions.md B29 must be updated
  by the orchestrator (I may not edit docs/): the rule is now joint over the steps of a run, excludes
  n = 0, and requires the chance bound to be <= P(|Z| > 3).

Monte Carlo (on the fixed code; `$S/s4/mc_counts.py`, seeds as in the test file). The auditor's
single-phase case (seed 1, 4000 uniform phases per setting, correlated sigma_s):
```
K=1 smoke B19 sigma_phi 0.003: {'inconsistent': 2385, 'not significant': 1615} of 4000; chance bound 0.401
K=1 smoke B19 sigma_phi 0.1: {'inconsistent': 1269, 'not significant': 2369, 'ambiguous': 362} of 4000; chance bound 0.772
K=1 smoke B19 sigma_phi 0.29: {'inconsistent': 372, 'ambiguous': 2172, 'not significant': 1456} of 4000; chance bound 1
K=1 HPC B32 sigma_phi 0.003: {'inconsistent': 2881, 'ambiguous': 503, 'not significant': 616} of 4000; chance bound 0.401
K=1 HPC B32 sigma_phi 0.1: {'inconsistent': 1745, 'ambiguous': 867, 'not significant': 1388} of 4000; chance bound 0.772
K=1 HPC B32 sigma_phi 0.29: {'inconsistent': 665, 'ambiguous': 1700, 'not significant': 1635} of 4000; chance bound 1
K=3 smoke uniform triples: {'inconsistent': 19996, 'resolved': 4} of 20000; chance bound 0.000122; alpha 0.0027; binomial 1-alpha quantiles: at bound 8, at alpha 75
```
The old rule, on the same draws with the correlated sigma_s, resolved 1593, 586, 2418, 1383, 2146
and 2493 of 4000 (the "before" failures below). The auditor's 28-66 % used the independent
sigma_s.

### (b) A3 M3: one common angle-calibration error

Derivation. For the specular beam `theta_out = theta_in = theta + delta` with ONE calibration error
delta, `s = 2 k sin(theta + delta)`, `ds/d delta = 2 k cos(theta)`. Hence
`sigma_s = sqrt((2 k cos(theta) sigma_theta)^2 + (s sigma_lambda/lambda)^2)`. Two independent
errors would give `sqrt(2) k cos(theta) sigma_theta`. The smoke demo has k = 250.53 /A,
theta = 16.4743 mrad, sigma_theta = 0.1 mrad and s = 8.2543 rad/A. This gives sigma_s = 0.050100
rad/A, against the old 0.035426. Then `sigma_h = hypot(sigma_phi/s, h sigma_s/s)`: for h = +2.7156,
`h sigma_s/s = 0.01648` and `sigma_phi/s = 0.00033`, so sigma_h = 0.0165 A. For h = -1.3576,
sigma_h = 0.0082 A.
Implemented: `quantification/height.py`. `sensitivity_uncertainty_rad_per_A` and
`height_from_phase` take a REQUIRED keyword `angle_errors` in ("independent", "common"). "common"
means fully correlated errors: `k (cos theta_in sigma_in + cos theta_out sigma_out)`. The value is
recorded in `HeightEstimate.angle_errors`. The pipeline uses "common" for the branch window
(`E = 3 sigma_s/s`) and for the height. The existing unit tests of height.py now state
`angle_errors="independent"`, their old relation, explicitly, so their numbers are unchanged. The
existing parametrised refusal test `test_each_uncertainty_must_be_positive_and_finite` iterates
over the keys of its `SIG` dictionary, so it gained 4 cases (non-string `angle_errors` refused;
they pass).

### (c) A3 M5: the git state is checked before the simulation

`provenance/manifest.py`: `require_git_state(allow_no_git=...)` raises the new `GitStateError`
(a RuntimeError) unless git works or `allow_no_git` is set. It records `package_tree`, a SHA-256
over every `*.py` and `*.yaml` file of `reflection_holo/`, so that a run without git still
identifies its code. `run()` calls it FIRST, before the output directory is created. The CLI maps
the error to exit 6 ("REFUSED (git state, before any computation)"). The manifest records
`extra.git_preflight`. `scripts/hpc/run_pipeline.slurm` checks `git -C $REPO rev-parse HEAD` before
submitting and before the job computes: exit 2 with a message, or `RH_ALLOW_NO_GIT=1`, which is
exported to the job and passes `--allow-no-git`.

### Regression tests: `tests/pipeline/test_a3_priority1.py` (17 tests)

Before (fdabd67 copy, `--tb=line`, verbatim final line per test, `$S/s4/p1_before_line.txt`):
```
$S/s4/before/tests/pipeline/test_a3_priority1.py:105: AssertionError: {'h_A': 2.723869148623508, 'sigma_h_A': 0.01171039375187009, 'branch_index': -4, 'branch_source': "lattice constraint: h = n a/4 with |n| <= 2 (the builder's a/4 and a/2 steps; stand-in B29); not a rocking series", ...}
$S/s4/before/tests/pipeline/test_a3_priority1.py:120: AssertionError: ['purpose: demo; not comparable to experiment', 'engine: geometric model, no dynamical amplitude, B4 scope applies', '...': False, 'n_a': 1960, 'n_b': 2016, 'controls_sigma_uncorrelated_rad': 0.000345818031314142, 'field_terrace': 1}", ...]
$S/s4/before/tests/pipeline/test_a3_priority1.py:130: assert {'h_A': 2.7156350652931436, 'sigma_h_A': 0.011659507373534035, 'branch_index': -4, 'branch_source': "lattice constraint: h = n a/4 with |n| <= 2 (the builder's a/4 and a/2 steps; stand-in B29); not a rocking series", ...} is None
$S/s4/before/tests/pipeline/test_a3_priority1.py:151: AssertionError: (1593, 4000)
$S/s4/before/tests/pipeline/test_a3_priority1.py:151: AssertionError: (586, 4000)
$S/s4/before/tests/pipeline/test_a3_priority1.py:151: AssertionError: (2418, 4000)
$S/s4/before/tests/pipeline/test_a3_priority1.py:151: AssertionError: (1383, 4000)
$S/s4/before/tests/pipeline/test_a3_priority1.py:151: AssertionError: (2146, 4000)
$S/s4/before/tests/pipeline/test_a3_priority1.py:151: AssertionError: (2493, 4000)
$S/s4/before/tests/pipeline/test_a3_priority1.py:161: AttributeError: module 'reflection_holo.pipeline.quantify' has no attribute 'chance_probability_bound'
$S/s4/before/reflection_holo/pipeline/quantify.py:98: TypeError: can only concatenate list (not "float") to list
$S/s4/before/tests/pipeline/test_a3_priority1.py:212: TypeError: sensitivity_uncertainty_rad_per_A() got an unexpected keyword argument 'angle_errors'
$S/s4/before/tests/pipeline/test_a3_priority1.py:244: assert 0.011659507373534035 == 0.016485789748637913 ± 1.6e-11
$S/s4/before/tests/pipeline/test_a3_priority1.py:268: AssertionError: ['arrays.npz', 'quicklook_detector.png', 'quicklook_exit_wave.png']
$S/s4/before/reflection_holo/provenance/manifest.py:180: RuntimeError: git state of the repository unavailable (CalledProcessError: TEST: git rev-parse HEAD failed (no .git)): the manifest cannot identify the code that ran; pass allow_no_git=True to record the failure explicitly (audit A2 m8)
$S/s4/before/tests/pipeline/test_a3_priority1.py:285: KeyError: 'package_tree'
$S/s4/before/tests/pipeline/test_a3_priority1.py:307: AssertionError: (0, '', '')
17 failed in 12.80s
```
(In order: B1 control failed; CLI verdict; control not performed; six single-phase MC cases;
joint MC (old API); power MC (old API); M3 formula (old API); M3 smoke sigma_h 0.01166 vs
0.01649; M5 arrays written; M5 CLI uncaught RuntimeError; M5 package tree; SLURM submitted.)

After (fixed tree): `17 passed in 12.20s`.

### Priority-1 checkpoint

`venv/bin/pytest -q`: `667 passed, 6 warnings in 214.99s (0:03:34)` (646 + 17 new + the 4
`angle_errors` parametrisations).

Smoke CLI (`--out $S/s4_smoke_1`):
```
purpose: demo; not comparable to experiment
engine: geometric model, no dynamical amplitude, B4 scope applies
heights: 3 of 3 step heights returned (joint lattice branch resolved, chance-acceptance bound 0.000122 <= alpha 0.0027)
step field terraces 0->1 (translation): h = +2.7156 +- 0.0165 A (branch -4, wrap period 0.7612 A)
step field terraces 1->2 (screw): h = -1.3576 +- 0.0082 A (branch 2, wrap period 0.7612 A)
step field terraces 2->0 (screw): h = -1.3580 +- 0.0082 A (branch 2, wrap period 0.7612 A)
no-step control: PASS {'performed': True, 'delta_rad': -0.0036868859167245027, 'tolerance_rad': 0.012310012257320535, 'n_sigma': 3.0, 'se_correlated_rad': 0.004103337419106845, 'passed': True, 'n_a': 1960, 'n_b': 2016, 'controls_sigma_uncorrelated_rad': 0.0002516205842901576, 'field_terrace': 1}
outputs in /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/s4_smoke_1: summary.json, manifest.json, arrays.npz quicklook_detector.png quicklook_exit_wave.png
cli exit 0
```

## Priority 2: COMPLETE

### (d) A3 M1: R2 heights near 0 marked "resolved"

Cause: `run.py` built the R2 reference as the object shifted by s, so the reconstructed phase is the
differential `phi(r) - phi(r + s)` (docs/03 section 6). Region medians of that phase were then
quantified as terrace phases. On a terrace where r and r + s lie together the phase is 0, and the
old lattice rule accepted n = 0, so h ~ 0 was returned as "resolved". Fix: (1) under R2 every
height is withheld with the reason `R2 self-reference: the reconstructed phase is the DIFFERENTIAL
phi(r) - phi(r + s) ... Quantification of a differential phase is NOT IMPLEMENTED ...` (holograms
and reconstruction are still produced); (2) the joint rule excludes n = 0 for regions that
straddle a step (see (a)). `NOT_IMPLEMENTED` in the summary lists it.

### (e) A3 M2: the comparison gate

* `reflection_holo/io/assumption_registry.yaml` gains the key `demo_only: [B19 ... B32]`. The loader
  requires it, checks that every id is a stand-in, and exposes `demo_only_stand_ins()`.
* `purpose: comparison` (`pipeline/config._comparison_gate`) refuses every demo-only stand-in
  whatever its item, every ASSUMPTION standing in for a blocking item, and TEST_ONLY. It now sees
  the records nested in `sections.engine.multislice` too (`_all_records`; the old gate did not, so
  B30 on item 21 was invisible to it).
* The rule form of item 7 labelled PROJECT_INPUT is refused at every purpose unless the V0 it used is
  itself a PROJECT_INPUT: "the computed angle cannot carry the label PROJECT_INPUT ...".
* `summary.json["assumptions_in_use"]` lists every remaining ASSUMPTION (parameter, item, id,
  demo_only, source).

### (f) A3 M6: supplied inputs that no path represents

Refused in the gate (`_refuse_unused_physical_inputs`), for every engine, because each one changes
the physics and would otherwise be silently ignored:
* a non-zero convergence semi-angle (item 3): the multislice path ran a plane wave;
* an overlayer other than none, or a termination other than bulk (item 12): not built, and docs/06
  item 12 says "must be modelled rather than ignored";
* `pattern_geometry` other than `{features: none}` (item 13): no mesa or trench is built;
* a rule `reflection_hkl` that differs from `target_reflection_hkl` (item 9).
Everything else that is accepted but not used on the selected path is listed by `list-inputs` (and
in `summary.json["inputs"]`) as `SUPPLIED, NOT USED on this path` or `ASSUMPTION Bxx stand-in, NOT
USED on this path`, with the reason on the next line. This covers: `step_types`,
`surface_preparation_method`, `second_reflection_hkl`, `recommended_reflections_hkl`,
`reconstruction_method`, `aperture_passage` (recorded only), `reference.shift` under R1, item 9 for a
typed angle, and the CFG-B V0 when the multislice engine uses the potential's MIP. For the multislice
path, item 20 lists `sections.engine.multislice.potential_mip` (13.903 V, REPRODUCED) as USED (this
is also A3 m2).

### (g) A2c G1, G2, G3 and the reference_correction="none" residual

* G1 (`io/config.PINNED`): CFG-A is defined by material Si, surface [1,-1,1] and azimuth [1,1,0];
  CFG-B by Si and [0,0,1]; CFG-O by Pt. Any other value is refused ("... CFG-A is defined by
  surface_normal_hkl = [1, -1, 1] ... cannot use its gate"). The CFG-A imaging parameters now carry
  the CFG-B docs/06 items: glancing angle 7, convergence 3, aperture 4, pixel size 5, reference
  trajectory 15, reconstruction method 19. They therefore pass the same PROJECT_INPUT gate:
  DERIVED_HERE and similar labels are refused. The shipped CFG-A has none of them and still loads
  at run level.
* G2 (`io/config.check_supply`, used by both the CFG and the pipeline gates): a PROJECT_INPUT with a
  value needs `supplied_by` (a non-empty name; placeholders such as "nobody", "unknown" or "the
  simulation", and negations starting "not "/"no ", are refused) and `supplied_on` (ISO
  `YYYY-MM-DD` or a YAML date; valid; not after today at UTC+14, the latest calendar date anywhere).
  The fields are refused on anything else. The free-text `SUPPLIER_DATE_RE` no longer gates
  anything. The supply record is kept (`Parameter.supply`, `Record.supply`) and travels with the
  item-7 value into CFG-B. The shipped configs now carry `supplied_by: Ali`,
  `supplied_on: "2026-09-22"` on the values whose sources already said so: cfg_a (1 parameter),
  cfg_b, demo_smoke and demo_hpc (4 each).
* G3: `run()` refuses a configuration with `test_only=True` before any computation ("a pipeline run
  refuses them"). The CLI has no switch for it. The manifest records `extra.test_only` and
  `extra.allow_test_only: "never set by a pipeline run or the CLI"`. `load_pipeline_dict(...,
  allow_test_only=True)` remains for gate tests only.
* Residual R1: `reconstruct_sideband(..., reference_correction="none")` now REQUIRES
  `object_min_visibility`, computed as for the empty hologram from the OBJECT hologram
  (`2 |w_obj| / D_obj`), and refuses it with divide_empty. The pipeline requires the key in
  `reconstruction.processing` exactly when `reference_correction` is "none".

Existing tests and tools changed (values unchanged, no tolerance touched):
* `tests/io/test_io_config.py` (the `ALI` fixture now has the structured fields; the null-energy
  case drops them with the value); `tests/io/test_io_config_gate.py` (one fixture);
  `tests/io/test_io_config_stand_ins.py` (`test_project_input_value_names_supplier_and_date` keeps
  its five cases in the structured form that replaces the free-text rule, and the non-finite
  fixture).
* `tests/pipeline/test_pipeline_geometric.py::test_outside_b4_scope_is_refused`: `run()` now
  refuses the TEST_ONLY configuration first (asserted), so the B4 refusal is asserted on the
  engine adapter that `run()` calls (`run_geometric(build_structure(cfg), cfg)`), same error, same
  match.
* 23 test calls of `reconstruct_sideband(reference_correction="none")` and the helper in
  `test_carrier_trap.py` declare `object_min_visibility=0.05`. Their outcomes are unchanged:
  `tests/reconstruction tests/optics tests/quantification`: 235 passed. The same applies to
  `tools/physics_checks/q2_carrier_trap.py` (21/21 self-checks pass) and `q3_r2_twin.py`
  (7/7 pass).

### Regression tests (44)

`tests/pipeline/test_a3_priority2.py` (M1 x2, M2 x3, M6 x7, G3 x3, R1-in-pipeline x1),
`tests/io/test_a2c_gate_fixes.py` (G1 x9, G2 x12), `tests/reconstruction/test_object_visibility_r1.py`
(R1 x5). Fabricated supplies in them are marked TEST.

Before (fdabd67 copy), `42 failed, 2 passed in 7.74s`. The two that pass there guard behaviour
that already existed: `test_cli_offers_no_test_only_switch` and
`test_cfg_a_defining_values_are_pinned[surface_material-Pt]` (the material was already checked).
Verbatim final lines (`$S/s4/p2_before_line.txt`):
```
$S/before/tests/pipeline/test_a3_priority2.py:61: AssertionError: (2.7154500000000006, {'h_A': -0.0001381555762252291, 'sigma_h_A': 0.0003696462460876539, 'branch_index': 0, 'branch_so...ttice constraint: h = n a/4 with |n| <= 2 (the builde
$S/before/tests/pipeline/test_a3_priority2.py:61: AssertionError: (2.7154500000000006, {'h_A': 7.556900569911431e-05, 'sigma_h_A': 0.021099010987653058, 'branch_index': 0, 'branch_sour...ttice constraint: h = n a/4 with |n| <= 2 (the builde
$S/before/tests/pipeline/test_a3_priority2.py:92: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:110: ImportError: cannot import name 'assumptions_in_use' from 'reflection_holo.pipeline.config' ($S/before/reflection_holo/pipeline/config.py)
$S/before/tests/pipeline/test_a3_priority2.py:120: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:136: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:136: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:146: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:146: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:157: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:157: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:165: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:175: AssertionError: assert False
$S/before/tests/pipeline/test_a3_priority2.py:195: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/pipeline/test_a3_priority2.py:203: KeyError: 'test_only'
$S/before/tests/pipeline/test_a3_priority2.py:218: Failed: DID NOT RAISE PipelineConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:54: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:64: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:64: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:71: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:83: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:83: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:83: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:83: Failed: DID NOT RAISE ConfigError
$S/before/reflection_holo/io/config.py:439: reflection_holo.io.config.ConfigError: CFG-A: parameter glancing_angle_ext has unknown keys ['supplied_by', 'supplied_on']
$S/before/tests/io/test_a2c_gate_fixes.py:123: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:123: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:123: Failed: DID NOT RAISE ConfigError
$S/before/tests/io/test_a2c_gate_fixes.py:140: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:140: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:140: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:140: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:140: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:140: AssertionError: Regex pattern did not match.
$S/before/tests/io/test_a2c_gate_fixes.py:138: ImportError: cannot import name 'latest_today' from 'reflection_holo.io.config' ($S/before/reflection_holo/io/config.py)
$S/before/reflection_holo/io/config.py:439: reflection_holo.io.config.ConfigError: CFG-B: parameter beam_azimuth_uvw has unknown keys ['supplied_by', 'supplied_on']
$S/before/tests/io/test_a2c_gate_fixes.py:158: AssertionError: Regex pattern did not match.
$S/before/tests/reconstruction/test_object_visibility_r1.py:42: Failed: DID NOT RAISE ValueError
$S/before/tests/reconstruction/test_object_visibility_r1.py:52: Failed: DID NOT WARN. No warnings of type (<class 'RuntimeWarning'>,) were emitted.
$S/before/tests/reconstruction/test_object_visibility_r1.py:52: Failed: DID NOT WARN. No warnings of type (<class 'RuntimeWarning'>,) were emitted.
$S/before/tests/reconstruction/test_object_visibility_r1.py:52: Failed: DID NOT WARN. No warnings of type (<class 'RuntimeWarning'>,) were emitted.
$S/before/tests/reconstruction/test_object_visibility_r1.py:73: TypeError: reconstruct_sideband() got an unexpected keyword argument 'object_min_visibility'
42 failed, 2 passed in 7.74s
```
(The R2 lines show the auditor's h = -0.00014 and +0.00008 A for the step built at +2.7155 A.)

After: `44 passed in 6.26s`.

### Priority-2 checkpoint

`venv/bin/pytest -q`: `711 passed, 12 warnings in 219.22s (0:03:39)`.

Smoke CLI (`--out $S/s4_smoke_2`):
```
purpose: demo; not comparable to experiment
engine: geometric model, no dynamical amplitude, B4 scope applies
heights: 3 of 3 step heights returned (joint lattice branch resolved, chance-acceptance bound 0.000122 <= alpha 0.0027)
step field terraces 0->1 (translation): h = +2.7156 +- 0.0165 A (branch -4, wrap period 0.7612 A)
step field terraces 1->2 (screw): h = -1.3576 +- 0.0082 A (branch 2, wrap period 0.7612 A)
step field terraces 2->0 (screw): h = -1.3580 +- 0.0082 A (branch 2, wrap period 0.7612 A)
no-step control: PASS {'performed': True, 'delta_rad': -0.0036868859167245027, 'tolerance_rad': 0.012310012257320535, 'n_sigma': 3.0, 'se_correlated_rad': 0.004103337419106845, 'passed': True, 'n_a': 1960, 'n_b': 2016, 'controls_sigma_uncorrelated_rad': 0.0002516205842901576, 'field_terrace': 1}
outputs in /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/s4_smoke_2: summary.json, manifest.json, arrays.npz quicklook_detector.png quicklook_exit_wave.png
cli exit 0
```

## Priority 3: COMPLETE (minors m1-m8; nits n2, n3; n1, n5, n6, n7 not done)

* m1: `arrays.npz` stores `purpose` as a 0-d text array, indexed in `summary.json["arrays"]`. The
  multislice engine's manifest now records the pipeline configuration path and file hash (`config`,
  `inputs`) and `extra.caller`: purpose, run name, variant, test_only and config hashes.
  `forward.multislice.simulate` gains a REQUIRED keyword `caller_record` (a mapping, or None stated
  explicitly). The engine's own no-defaults contract test holds; its three other callers pass
  `caller_record=None`.
* m2: `list-inputs` shows item 20 as `sections.engine.multislice.potential_mip` 13.903 V, "USED",
  for multislice runs, and the CFG-B V0 as "NOT USED on this path" (see (f)).
* m3: the detector trace is computed before the references. The empty-object amplitude is the RMS
  over LIT terrace-top pixels at or above half their maximum; the below-surface field of the
  multislice exit plane no longer enters it. The summary records
  `detector.object_amplitude_by_trace_status` (pixel count and mean |obj| per trace status). For
  the geometric smoke run the value is unchanged (0.9978630959369624 before and after). No
  real-space mask of the in-crystal field was added; the regions use lit pixels only, as before.
* m4: `quantification.sign_degeneracy` lists, per n <= n_max, the wrapped separation of +n a/4
  and -n a/4 against the single-step window, with a note. The CLI prints the note when a pair is
  degenerate. At B32: n = 2 separation 0.0779 rad, degenerate for a single step. At B19: 0.846 rad,
  not degenerate. Checked with the new rule: at B32, noise-free +a/2, -a/4, -a/4 (sigma_phi 0.003)
  are "resolved", assignment [2, -1, -1], bound 1.55e-4; the a/2 step alone is "ambiguous". The A3
  statement "the HPC demo can never return an a/2 height" therefore no longer holds when both a/4
  steps are measured.
* m5: `engines.backend_status` checks that cupy imports and sees at least one GPU. `require_engine`
  runs at the start of `run()`, before any computation, and raises EngineUnavailableError (exit 4).
  `dry-run` still runs every geometry check, reports `backend`, and exits 4 with "multislice backend
  cupy NOT available" (it exited 0 before). SLURM: in submission mode `import cupy` failing is a
  WARNING (login nodes often lack CUDA); in the job, cupy and a GPU are checked before the first
  step (exit 4).
* m6 (SLURM): the script path is made absolute, `REPO` is absolute, and `cd "$REPO"` happens before
  the configuration check in both modes. In the job, `CPUS` falls back to `SLURM_CPUS_PER_TASK`
  before 8. A failed dry-run is reported with its status and stops the job before the run.
* m7 (`scripts/hpc/null_test_study/run_study.py`): the study YAML is read with `load_yaml_unique`
  (duplicate keys refused). An existing result stops the point BEFORE any computation, and results
  are written with exclusive creation. Every result and manifest records the purpose "engine null
  test with TEST_ONLY stand-ins ... not a pipeline run" and `test_only: true`. The shipped
  `study.yaml` loads (17 points).
* m8: the CLI maps `OutsideB4ScopeError` to exit 3, a missing git state to 6, and backend or engine
  unavailability to 4. `BrokenPipeError` ends the command quietly with status 0 (stdout redirected
  to /dev/null), which also covers A3 M4's `| head` case.
* n2: the stale docstrings in `optics/__init__.py` and `optics/detector.py` are updated. n3:
  `arrays.npz` is written with exclusive creation. Not done: n1 (the dark-field angle
  self-validation; the pipeline checks the angle in `engines.py`), n5 (the builder's boundary step in
  the multislice summary strips), n6 (the HPC config cites B19 for the 0.1 mrad sigma; the value is
  B19's, so the citation is correct), n7 (dry-run rebuilds the structure).
* `scripts/hpc/README_HPC.md` (outside docs/) is updated with the new uncertainties (+-0.0165 and
  +-0.0082 A), the height verdict, the git and cupy pre-flights, and the B32 sign note.

### Regression tests: `tests/pipeline/test_a3_priority3.py` (13)

m1 x2, m3, m4 x2, m5 x2 (skipped where cupy is installed), m6 x2 (SLURM with a fake sbatch), m7 x2,
m8 x2 (the closed-pipe test closes the read end before the command writes, so it is
deterministic). `tests/pipeline/test_pipeline_multislice.py::test_hpc_config_passes_the_gate_and_the_engine_geometry_checks`
now expects exit 4 with the "NOT available" line where cupy is unusable, and 0 where it is usable,
after the same geometry assertions (m5 reverses its old expectation of 0).

Before (fdabd67 copy), `13 failed in 93.82s (0:01:33)`. Verbatim final lines
(`$S/s4/p3_before_line.txt`; the m6 and m8 lines are truncated tracebacks of the old script and CLI):
```
$S/before/venv/lib/python3.11/site-packages/numpy/lib/_npyio_impl.py:243: KeyError: 'purpose is not a file in the archive'
$S/before/tests/pipeline/test_a3_priority3.py:66: KeyError: 'caller'
$S/before/tests/pipeline/test_a3_priority3.py:82: assert 0.09157143118256607 == 0.09475863770409504 ± 1.0e-12
$S/before/tests/pipeline/test_a3_priority3.py:103: AttributeError: module 'reflection_holo.pipeline.run' has no attribute '_sign_degeneracy'
$S/before/tests/pipeline/test_a3_priority3.py:114: KeyError: 'sign_degeneracy'
$S/before/reflection_holo/forward/multislice/backend.py:65: ModuleNotFoundError: No module named 'cupy'
$S/before/reflection_holo/forward/multislice/backend.py:65: ModuleNotFoundError: No module named 'cupy'
$S/before/tests/pipeline/test_a3_priority3.py:163: AssertionError: ('', 'Traceback (most recent call last):
$S/before/tests/pipeline/test_a3_priority3.py:175: AssertionError: (0, 'attice_constraint", "edge_margin_resolu...
$S/before/scripts/hpc/null_test_study/run_study.py:89: SystemExit: runtime.backend is required
$S/before/tests/pipeline/test_a3_priority3.py:212: AssertionError: computation started although the result exists
$S/before/tests/pipeline/test_a3_priority3.py:226: reflection_holo.forward.geometric.model.OutsideB4ScopeError: TEST: a/4 step outside the B4 scope
$S/before/tests/pipeline/test_a3_priority3.py:244: AssertionError: Traceback (most recent call last):
13 failed in 93.82s (0:01:33)
```
After: 13 passed, plus the two multislice tests (`15 passed in 56.30s`).

The first full-suite run after priority 3 gave `1 failed, 723 passed`:
`FAILED tests/forward/test_engine_contract.py::test_no_defaults_anywhere - Ass...`
(`AssertionError: <function simulate ...>`: my first `caller_record=None` DEFAULT broke the engine's
no-defaults contract). Fixed by making the keyword required (above); the test was not changed. In the
same pass, my m5 test's skip condition was changed so that it never imports cupy (`find_spec`).
Otherwise it would import cupy at collection on a machine with cupy, and
`test_cupy_is_lazy_and_not_a_fallback` there would fail.

### Priority-3 checkpoint

`venv/bin/pytest -q`: `724 passed, 12 warnings in 228.97s (0:03:48)`.

Smoke CLI (`--out $S/s4_smoke_3`):
```
purpose: demo; not comparable to experiment
engine: geometric model, no dynamical amplitude, B4 scope applies
heights: 3 of 3 step heights returned (joint lattice branch resolved, chance-acceptance bound 0.000122 <= alpha 0.0027)
step field terraces 0->1 (translation): h = +2.7156 +- 0.0165 A (branch -4, wrap period 0.7612 A)
step field terraces 1->2 (screw): h = -1.3576 +- 0.0082 A (branch 2, wrap period 0.7612 A)
step field terraces 2->0 (screw): h = -1.3580 +- 0.0082 A (branch 2, wrap period 0.7612 A)
no-step control: PASS {'performed': True, 'delta_rad': -0.0036868859167245027, 'tolerance_rad': 0.012310012257320535, 'n_sigma': 3.0, 'se_correlated_rad': 0.004103337419106845, 'passed': True, 'n_a': 1960, 'n_b': 2016, 'controls_sigma_uncorrelated_rad': 0.0002516205842901576, 'field_terrace': 1}
outputs in /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/s4_smoke_3: summary.json, manifest.json, arrays.npz quicklook_detector.png quicklook_exit_wave.png
cli exit 0
```

Additional checks (fixed tree):
* A simulated SLURM job (`SLURM_JOB_ID` set, smoke mode, fake account; output in `$S/s4/`) exits 0
  with and without `PYTHONUNBUFFERED=1`; the output directory holds summary, manifest, arrays,
  quicklooks and the dry-run text. The runner writes its `reflholo_<job>_dryrun.txt` into the
  repository root; I deleted the two I produced.
* `dry-run --config configs/demo_hpc_si001.yaml` (43.5 s): all geometry lines are printed, then
  `multislice backend cupy NOT available: backend cupy requested but cupy is not installed in this
  Python environment ...`, exit 4. `list-inputs` of the HPC config: gate PASS; item 20 lists
  `cfg_b.mean_inner_potential_V` 12.0 "NOT USED on this path" and `potential_mip` 13.903 "USED".
* HPC geometric variant (`--variant geometric_same_structure`, 12 s; B19 angle): +2.7151 +- 0.0165,
  -1.3578 +- 0.0083, -1.3573 +- 0.0082 A; joint branch resolved, bound 1.40e-4; control PASS.
* `tools/physics_checks/q2_carrier_trap.py`: 21/21 self-checks pass;
  `tools/physics_checks/q3_r2_twin.py`: 7/7 pass.

## What tonight's HPC run will do (not run here)

With cupy on a GPU node the pre-flights pass. If the multislice no-step control fails, as in P1's
second run (0.441 vs 0.290 rad), the first result line reads `NO HEIGHT: no-step control failed or
not performed (failed: ...)`. If it passes, the joint chance bound for three steps at the B32 angle
is 1.0 at sigma_phi = 0.29 rad per step, 0.23 at 0.1 rad and 0.017 at 0.03 rad. All three are
above alpha = 2.7e-3, so the branch is "not significant" (or "ambiguous" or "inconsistent") and no
height is returned. With three steps, heights appear only if the step phase uncertainties are
below about 0.012 rad (bound 2.55e-3 at 0.012 rad, 4.0e-3 at 0.015 rad; the demo level is
0.003 rad).

## Documents to update (not edited: docs/ is outside my remit)

* docs/model_assumptions.md B29: the branch rule is now the joint lattice constraint over the steps
  of a run (n != 0, one common eps within 3 sigma_s/s, significance bound <= P(|Z| > 3)).
  B19-B32: "a run with purpose comparison refuses stand-ins for blocking items" should read "refuses
  every one of B19-B32 (registry demo_only)".
* docs/model_assumptions.md B16 is unaffected (rocking series).
* docs/05 9.1 "Open after the fixes (A2c)": G1, G2, G3 and the reference_correction="none" residual
  are fixed here (the aliasing flag and the B16 noise-declaration items remain).
* The P1 report quotes +- 0.0117 / 0.0058 A; the values with the common angle error are +- 0.0165 /
  0.0082 A.

## NOT RUN

* The HPC multislice run itself (cupy on a GPU or cpu_numpy, 18.8 min on CPU per P1): there is no
  GPU here. The m5 refusal was exercised only where cupy is absent; the cupy-present path of
  `backend_status` (`getDeviceCount`) is NOT RUN.
* A real `sbatch` submission (fake sbatch only); `setup_env.sh`.
* `scripts/hpc/null_test_study/run_study.py` beyond the duplicate-key and no-overwrite checks (no
  study point was computed).
* `tools/phase1_numbers.py` and the calculator (not affected by these changes; not re-run).
* Frozen-phonon ensembles through the pipeline; a comparison-purpose run end to end (only its gate
  was tested).
