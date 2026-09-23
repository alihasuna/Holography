# A3: Audit of the Phase 3 end-to-end pipeline (P1, commit 281074a)

Status: IN PROGRESS (written incrementally; the final version replaces this line).

Auditor: code-audit agent A3, 2026-09-23. Code under audit was not modified. Scratch scripts and
run outputs: `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/audit3/`
(abbreviated `$S` below).

Scope: `reflection_holo/pipeline/`, `reflection_holo/forward/geometric/`,
`reflection_holo/optics/{darkfield,projection,detector}.py`, `configs/demo_smoke_si001.yaml`,
`configs/demo_hpc_si001.yaml`, `scripts/hpc/`, `tests/pipeline/`, `tests/forward_geometric/`.
The multislice engine itself is out of scope; only the pipeline adapter
(`pipeline/engines.py`, the multislice branch of `pipeline/run.py`) is audited.

Repository state. HEAD moved during the audit (orchestrator snapshot commits 8c3a61a, b8d0650,
060b45c). `git diff --stat 281074a HEAD -- reflection_holo configs scripts tests/pipeline
tests/forward_geometric` shows only `scripts/hpc/null_test_study/study.yaml` added: every audited
code file is byte-identical to 281074a. The runs below were made at HEAD 060b45c (their manifests
record that commit, correctly).

## Findings

Severity scale: Blocker (tonight's HPC run gives a wrong or mislabelled result), Major (a wrong or
silently mislabelled number is reachable through the supported interface), Minor (defect with
limited or conditional effect), Nit.

### M1 (Major). A failed no-step control neither blocks nor flags the step heights

* Where: `reflection_holo/pipeline/run.py:341-357` (steps are measured first; the control is
  computed afterwards and never consulted), `reflection_holo/pipeline/quantify.py:113-176`
  (`measure_steps` has no control input), `reflection_holo/pipeline/__main__.py:101-109` (heights
  printed before the control verdict).
* What is wrong: spec 5.8 requires a "no-step control on every dataset"; the control is the only
  in-pipeline test that the phase is flat inside a terrace (charging B8, reference curvature,
  engine artefacts). When it fails, every step record still carries `height` with no field that
  refers to the control, so `summary.json["quantification"]["steps"][i]["height"]` is a number
  from a dataset that failed its own control.
* Reproduction (`$S/repro_nostep.py`, adds a slow phase `exp(i g x)` to the geometric exit wave,
  the signature of charging B8):
  ```
  venv/bin/python $S/repro_nostep.py 0.001
  slope 0.001 rad/A: no-step control passed=False delta=-0.0191 tol=0.0169
    step 0->1 built +2.7155: h = +2.7239 +- 0.0117 (+0.7 sigma) | control-related keys in the step record: []
    step 1->2 built -1.3577: h = -1.3489 +- 0.0058 (+1.5 sigma) | control-related keys in the step record: []
    step 2->0 built -1.3577: h = -1.3750 +- 0.0059 (-2.9 sigma) | control-related keys in the step record: []
  ```
  The HPC README (section 4) says the multislice demo returns no height; that is because its
  branch is "inconsistent", not because its failed control (0.44 vs 0.29 rad) stopped anything.
  Had the branch resolved, heights would have been printed next to a failed control.
* Fix: make the control a gate: if `performed` and not `passed`, set `height=None` with reason
  "no-step control failed (delta ..., tolerance ...)" on every step (or at least attach
  `no_step_control_passed: false` to every step record and print it on the same line); decide
  and record what happens when the control could not be performed.

### M2 (Major). R2 (self-reference) is accepted and its differential phase is quantified as an absolute phase: confident zero heights

* Where: `reflection_holo/pipeline/run.py:242-266` (R2 accepted, reference = shifted object
  wave), `run.py:341-349` and `quantify.py:113-176` (quantification unchanged for R2).
* What is wrong: with R2 the reconstructed phase is `phi(r) - phi(r + s)` (model_assumptions B5).
  The pipeline takes region medians of it as terrace phases. Wherever `r` and `r + s` lie on the
  same terrace the phase is 0, so every step phase is about 0 and the lattice constraint accepts
  branch 0 (h = 0 is a lattice height, n = 0). The no-step control passes (the phase is flat).
* Reproduction (`$S/repro_r2.py`: smoke demo with `reference_model: R2`,
  `reference_trajectory: reflected_flat_area`, a B28 shift record; every other value unchanged):
  ```
  R2 shift {'along_beam': 0.0, 'perpendicular': 10.0}
    step 0->1 built +2.7155: h = -0.0001 +- 0.0004 (decision resolved)
    step 1->2 built -1.3577: h = +0.0002 +- 0.0004 (decision resolved)
    no-step control: True
  R2 shift {'along_beam': 20.0, 'perpendicular': 0.0}
    step 0->1 built +2.7155: h = +0.0001 +- 0.0211 (decision resolved)
    step 1->2 built -1.3577: h = -0.0003 +- 0.0057 (decision resolved)
    no-step control: True
  ```
  Silent, wrong, and reported with a smaller uncertainty than the true answer. Not reachable
  from the two demo configurations (both R1), but reachable by changing two CFG-B values, and R2
  is how the repository reads the P01 arrangement.
* Fix: until an R2 quantification exists (differential phase with the reference region traced
  through the same ray trace, or regions chosen so that `r + s` is on one known terrace),
  refuse quantification for R2 (`height=None`, reason "R2: differential phase, quantification
  NOT IMPLEMENTED") or refuse R2 in the pipeline gate.

### M3 (Major). The "comparison" gate lets demo stand-ins through for every non-blocking item, and accepts a rule-computed angle labelled PROJECT_INPUT

* Where: `reflection_holo/pipeline/config.py:58` (`BLOCKING_ITEMS`), `config.py:589-598` (the
  only purpose-dependent check), `config.py:440-489` and `501-510` (rule form of item 7).
* What is wrong: (a) a run with `purpose: comparison` refuses ASSUMPTION stand-ins only for the
  blocking items 3, 4, 5, 7, 8, 11, 12, 15. The demo stand-ins B24 (dose, gain, MTF; item 6),
  B28 (carrier spacing, direction, amplitude ratio; item 16), B29 (all reconstruction and
  quantification processing; item 19, which docs/06 says must be the laboratory's own code path),
  B31 (item 1 stability), B1 (V0; item 20), B17, B18, B27 all pass, and nothing in the outputs of
  a comparison run lists them as demo stand-ins (the registry comment calls them "used by
  configs/demo_*.yaml only", which nothing enforces). (b) `glancing_angle` in rule form may carry
  the label PROJECT_INPUT with a "supplied by" source; the pipeline then computes the angle from
  the CFG-B V0, which may be the ASSUMPTION B1, and records the angle as PROJECT_INPUT
  (`_cfg_b_with_angle`, `summary.json["glancing_angle"]["label"]`). docs/06 item 20 states that
  an angle computed from V0 biases h by 1.07 %/V at (0,0,8).
* Reproduction (`$S/repro_comparison_leak.py`: smoke config, `purpose: comparison`, every blocking
  stand-in replaced by a fabricated `PROJECT_INPUT` "supplied by Auditor 2026-09-23"):
  ```
  purpose: comparison -> gate PASSED
  demo ASSUMPTION stand-ins still in the comparison run:
     illumination.wavelength_sigma_rel item 1 B31
     reference.carrier_fringe_spacing item 16 B28
     reference.carrier_direction item 16 B28
     reference.amplitude_ratio item 16 B28
     detector.dose item 6 B24
     detector.gain item 6 B24
     detector.mtf item 6 B24
     reconstruction.processing item 19 B29
     quantification.processing item 19 B29
     cfg_b.mean_inner_potential_V item 20 B1
     cfg_b.target_reflection_hkl item 9 B17
     cfg_b.step_types item 14 B18
     cfg_b.pattern_geometry item 13 B27
  glancing angle computed from V0 = 12.0 V, V0 label ASSUMPTION B1 ; item-7 label PROJECT_INPUT
  ```
* Fix: mark B19-B32 as demo-only in the registry (e.g. a `demo_only` list) and refuse them
  whenever `purpose == "comparison"`, whatever the item; list every remaining ASSUMPTION in the
  comparison summary; refuse the rule form of item 7 with label PROJECT_INPUT (a supplied angle is
  a number), or label the computed angle with the label of the V0 it used.

### M4 (Major). The height uncertainty treats the incidence and exit angle errors of the specular beam as independent: sigma_h is 29 % too small

* Where: `reflection_holo/pipeline/quantify.py:120-123` and `160-165` pass the same
  `angle_calibration_sigma` as `sigma_theta_in_rad` and `sigma_theta_out_rad`;
  `reflection_holo/quantification/height.py:96` (out of scope) adds the two in quadrature.
  The same `sigma_s` enters the branch test `quantify.py:102`.
* What is wrong: for the specular beam theta_out = theta_in exactly (docs/06 item 7: "the exit
  angle is not a separate input"), so a calibration error moves both by the same amount:
  `sigma_s = 2 k cos(theta) sigma_theta`, not `sqrt(2) k cos(theta) sigma_theta`. The angle term
  dominates sigma_h for every demo step, so the printed uncertainties are low by 1/sqrt(2).
* Reproduction (smoke run `$S/smoke_run1`, recomputed from its summary):
  ```
  pipeline sigma_s 0.035425908523705946
  independent (in quadrature) 0.035425812359492714  fully correlated (theta_out = theta_in) 0.050099664296879
  h=+2.7156 reported sigma_h=0.0117  correlated-angle sigma_h=0.0165  ratio=0.707
  h=-1.3576 reported sigma_h=0.0058  correlated-angle sigma_h=0.0082  ratio=0.708
  ```
  The P1 claim "+2.7156 +- 0.0117 A" should read about +- 0.0165 A under the declared B19
  calibration uncertainty. The pipeline tests cannot see this (the simulation has no angle error).
* Fix: for the specular beam propagate one angle error (`d s / d theta = 2 k cos(theta)`),
  e.g. a `correlated=True` path in `sensitivity_uncertainty_rad_per_A`, and use it both in
  `lattice_branch` and `height_from_phase`; add a unit test with sigma_in = sigma_out.

### M5 (Major, operational). The SLURM job dies at random before the run when PYTHONUNBUFFERED is set: `dry-run | head -12` under `set -euo pipefail`

* Where: `scripts/hpc/run_pipeline.slurm:20` (`set -euo pipefail`) with `:100`
  (`"$PY" -m reflection_holo.pipeline dry-run ... | head -12`).
* What is wrong: `head` exits after 12 lines; if Python writes after that (unbuffered stdout: each
  `print` is one or two `write` calls), it gets EPIPE, raises `BrokenPipeError` and exits 1;
  `pipefail` makes the pipeline fail and `set -e` ends the job before `run` is reached. With
  buffered stdout the whole dry-run output (4.6 kB for the HPC demo) is one write at exit, so the
  race is (almost) never lost; many HPC job templates export `PYTHONUNBUFFERED=1` (this sandbox
  does).
* Reproduction (my first simulated job-mode run died this way):
  ```
  SLURM_JOB_ID=4242 RH_OUT=$S/slurm_job_smoke RH_MODE=smoke RH_ACCOUNT=a RH_PARTITION=p \
    RH_TIME_LIMIT=00:10:00 RH_GPU=none bash scripts/hpc/run_pipeline.slurm      -> exit 1
    File ".../reflection_holo/pipeline/__main__.py", line 91, in main
      print(json.dumps(rep, indent=1, default=str)[:4000])
  BrokenPipeError: [Errno 32] Broken pipe
  # 60 repetitions of: bash -c 'set -euo pipefail; venv/bin/python -m reflection_holo.pipeline
  #   dry-run --config configs/demo_smoke_si001.yaml | head -12 > /dev/null'
  PYTHONUNBUFFERED=1: 26 / 60 failed
  PYTHONUNBUFFERED unset: 0 / 60 failed
  ```
  On the GPU job this happens after the 46 s dry-run and before any propagation; no result, no
  summary, exit 1.
* Fix: do not truncate with `head` under `pipefail` (write the dry-run to a file in `$OUT`, or
  `... | head -12 || true`, or `set +o pipefail` around it); also handle `BrokenPipeError` in
  `__main__.py`.

### M6 (Major). Without `.git` the whole simulation runs, then the manifest refuses: no summary, no manifest, unlabelled arrays left behind

* Where: `reflection_holo/pipeline/run.py:441` (`arrays.npz` written) and `:501` (quicklooks)
  before `:503-519` (`build_manifest`, which raises `RuntimeError` without git unless
  `allow_no_git`); `reflection_holo/pipeline/__main__.py:113-121` does not catch it;
  `scripts/hpc/run_pipeline.slurm:101` never passes `--allow-no-git` and never checks the git
  state before submitting.
* What is wrong: the git check is the last step. A tree copied without `.git` (README_HPC section
  1 warns, but rsync/scp copies are common) spends the full engine time (18.8 min CPU for the HPC
  demo per P1) and then exits 1 with a traceback, leaving `arrays.npz` and PNGs without
  `summary.json`, `manifest.json` or any purpose label in the arrays.
* Reproduction (copy of `reflection_holo/` and `configs/` in `$S/nogit`, no `.git`):
  ```
  PYTHONPATH=$S/nogit venv/bin/python -m reflection_holo.pipeline run \
      --config configs/demo_smoke_si001.yaml --out $S/nogit_out1          -> exit 1
  RuntimeError: git state of the repository unavailable (CalledProcessError: ... rev-parse HEAD ...
  ls $S/nogit_out1 -> arrays.npz quicklook_detector.png quicklook_exit_wave.png
  ```
  With `--allow-no-git` the run completes and the manifest records the error and
  `allowed_without_git: true` (verified).
* Fix: call `git_state()` (or build the manifest skeleton) in `run()` before the structure is
  built and refuse there; in the SLURM script check `git -C "$REPO" rev-parse HEAD` in submission
  mode; when running without git, hash the package source tree instead so the code is still
  identified.

### M7 (Major). Supplied PROJECT_INPUT values that the run cannot represent are accepted, not applied, and listed as SUPPLIED

* Where: `reflection_holo/pipeline/run.py:185-201` and `engines.py:161-215` (the multislice path
  never reads `convergence_semi_angle`, item 3, and builds no overlayer, item 12);
  `pipeline/` never reads `cfg_b.pattern_geometry` (item 13) or `cfg_b.target_reflection_hkl`
  (item 9) (`grep` counts: 0 references each); the glancing-angle rule uses its own
  `reflection_hkl` (`config.py:449`) with no consistency check against item 9.
* What is wrong: the geometric engine refuses a non-zero convergence and an overlayer
  (`forward/geometric/model.py:193-209`), but the other paths run with the input silently
  replaced by the default the engine happens to have (plane wave, clean surface, no pattern,
  (0,0,8)). The summary's `inputs` table then shows the item as SUPPLIED with its value, so the
  output claims an input it did not use. This is the situation of docs/05 criterion 5 ("no result
  depends on a default silently substituted"), and docs/06 item 12 says the overlayer "must be
  modelled rather than ignored".
* Reproductions (`$S/repro_convergence.py`, `$S/repro_ignored_inputs.py`, `$S/repro_item9.py`;
  fabricated "supplied by Auditor 2026-09-23" values):
  ```
  convergence 0.5 mrad (item 3), geometric:  REFUSED OutsideB4ScopeError: illumination 'convergent' ...
  convergence 0.5 mrad (item 3), multislice_tiny: RAN. engine multislice; item 3 in summary:
      [{'item': 3, ..., 'status': 'SUPPLIED (Auditor 2026-09-23)', 'value': 0.5, ...}]
      'convergen' mentioned in engine record/params: False
  pattern_geometry {features: [mesa 10 nm x 200 nm]} (item 13), geometric: RAN, heights
      [(0, 1, 2.7156), (1, 2, -1.3576), (2, 0, -1.3580)]
  overlayer SiO2 10 A (item 12), multislice_tiny: RAN (engine multislice)
  target_reflection_hkl [0, 0, 12] SUPPLIED (item 9): gate PASSED; angle computed for [0, 0, 8] = 16.474333 mrad
  ```
  Not triggered by the two demo configurations (plane wave, no overlayer, no pattern, (0,0,8)
  in both places), so tonight's demo outputs are not affected.
* Fix: in the pipeline gate, per engine, refuse what is not implemented: convergence != 0 (both
  engines until partial-coherence ensembles exist), overlayer != none (multislice as well),
  `pattern_geometry.features != none`; require the rule's `reflection_hkl` to equal
  `target_reflection_hkl` (or take it from there).

### Addendum to M1 (raises it to Blocker for tonight's multislice run): the lattice constraint accepts phases that carry no height information

* Where: `reflection_holo/pipeline/quantify.py:89-110` (`lattice_branch`: "resolved" when exactly
  one of the 5 lattice heights |n| <= 2 lies within 3 sigma_h of a candidate).
* Evidence (`$S/branch_power.py`, the pipeline's own `lattice_branch`, demo settings, uniform
  random wrapped phases, i.e. a phase with no height in it):
  ```
  smoke B19 sigma_phi 0.003 rad (sigma_h(a/4) ~ 0.0058 A): resolved 28.4%, ambiguous 0.0%, inconsistent 71.6%
  smoke B19 sigma_phi 0.100 rad (sigma_h(a/4) ~ 0.0134 A): resolved 57.8%, ambiguous 0.0%, inconsistent 42.2%
  HPC B32 sigma_phi 0.003 rad (sigma_h(a/4) ~ 0.0060 A): resolved 11.6%, ambiguous 8.1%, inconsistent 80.3%
  HPC B32 sigma_phi 0.100 rad (sigma_h(a/4) ~ 0.0137 A): resolved 32.0%, ambiguous 12.8%, inconsistent 55.1%
  HPC B32 sigma_phi 0.290 rad (sigma_h(a/4) ~ 0.0364 A): resolved 65.5%, ambiguous 34.5%, inconsistent 0.0%
  ```
  P1 (report item 7) already saw it: the first HPC multislice run returned the a/4 down-step as
  "resolved" h = +1.4272 +- 0.0355 A (built -1.3577 A, wrong sign). The second run's refusal
  ("inconsistent") is luck of the draw, not a guarantee, and the GPU run (complex64, cupy) is a
  different numerical path. With M1, a resolved branch is printed as a height even though the
  same run's no-step control fails.
* Fix for tonight (no code change needed to be safe): treat every multislice height as invalid
  when the printed no-step control is "NOT PASSED". Code fix: M1's gate, plus report the
  resolved-by-chance rate of the constraint for the run's sigma (the numbers above) next to the
  decision.

