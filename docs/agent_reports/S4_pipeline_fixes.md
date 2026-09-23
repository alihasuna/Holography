# S4: fixes of audit A3 (pipeline) and the A2c residuals G1-G3

Status: IN PROGRESS, 2026-09-23. Agent S4. Written incrementally; nothing committed or pushed.
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
