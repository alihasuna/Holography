# A3: Audit of the Phase 3 end-to-end pipeline (P1, commit 281074a)

Status: FINAL, 2026-09-23. Auditor: code-audit agent A3. The code under audit was not modified.
Scratch scripts and run outputs: `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/audit3/`
(written `$S` below).

Scope: `reflection_holo/pipeline/`, `reflection_holo/forward/geometric/`,
`reflection_holo/optics/{darkfield,projection,detector}.py`, `configs/demo_smoke_si001.yaml`,
`configs/demo_hpc_si001.yaml`, `scripts/hpc/`, `tests/pipeline/`, `tests/forward_geometric/`.
The multislice engine itself is out of scope. Only the pipeline adapter (`pipeline/engines.py`, the
multislice branch of `pipeline/run.py`) is audited.

Repository state. HEAD moved during the audit because the orchestrator made snapshot commits
(8c3a61a, b8d0650, 060b45c, ea1ca21). The command `git diff --stat 281074a HEAD -- reflection_holo
configs scripts/hpc/{run_pipeline.slurm,setup_env.sh,README_HPC.md} tests/pipeline
tests/forward_geometric` is empty, so every audited file is byte-identical to 281074a. The only
in-scope change is the new `scripts/hpc/null_test_study/study.yaml`, which another agent is still
editing. My runs used HEAD 060b45c, and their manifests record that commit correctly.

Severity scale:
* Blocker: tonight's HPC demo can print a wrong number as a result.
* Major: the supported interface can produce a wrong or silently mislabelled number, or the HPC
  job can fail after it has spent its allocation.
* Minor: a defect with a limited or conditional effect.
* Nit: a small issue.

## What matters for tonight (the run is `configs/demo_hpc_si001.yaml`, multislice)

1. B1: when the multislice no-step control fails, the step heights are not withheld. When a branch
   "resolves", the height is printed anyway. A phase that carries no height information resolves
   32-65 % of the time at the multislice noise level, and P1's first HPC run printed an a/4 height
   with the wrong sign. Treat every multislice height as invalid if the control line says
   "NOT PASSED".
2. M4: if the job environment exports `PYTHONUNBUFFERED=1`, the SLURM job dies at random, with
   status 1, before the run starts. This happened in 26 of 60 trials. Unset that variable or edit
   line 100.
3. M5 and m5: before submitting, check that `.git` is present (`git rev-parse HEAD`) and that
   `venv/bin/python -c "import cupy"` works on the GPU node. Neither is checked before the compute
   starts.
4. m4: at the B32 angle the HPC demo can never return an a/2 height, even with a perfect engine,
   because +a/2 and -a/2 differ by 0.078 rad of wrapped phase and the branch is always
   "ambiguous". Expect this refusal. It says nothing about the engine.
5. M3: the smoke demo's printed uncertainties (+- 0.0117 A and +- 0.0058 A) are 29 % too small.

## Findings

### B1 (Blocker for tonight's multislice run). A failed no-step control neither blocks nor flags the heights, and the lattice constraint accepts phases that carry no height information

* Where:
  * `reflection_holo/pipeline/run.py:341-357`: steps are measured first, and the control is
    computed afterwards and never consulted.
  * `reflection_holo/pipeline/quantify.py:113-176`: `measure_steps` has no control input.
  * `quantify.py:89-110`: `lattice_branch` returns "resolved" when exactly one of the 5 lattice
    heights |n| <= 2 lies within 3 sigma_h of a candidate.
  * `reflection_holo/pipeline/__main__.py:101-109`: heights are printed before the control
    verdict.
* What is wrong:
  * Spec 5.8 requires a no-step control on every dataset. Inside the pipeline, this control is the
    only check that the phase is flat within a terrace, which is what exposes charging (B8),
    reference curvature and engine artefacts.
  * When the control fails, every step record still carries `height`, and no field refers to the
    control.
  * The lattice constraint is not a validity test. A random phase lands within 3 sigma of one
    lattice height often.
  * P1 report item 7 shows this already happened: the first HPC multislice run returned the a/4
    down-step as "resolved" h = +1.4272 +- 0.0355 A, while the built height is -1.3577 A (wrong
    sign).
  * P1's second run refused ("inconsistent") by chance, and its control failed (0.441 against
    0.290 rad). The GPU run (cupy, complex64) is a numerical path nobody has run.
* Reproduction 1 (`$S/repro_nostep.py`). The script adds a slow phase `exp(i g x)`, the signature
  of charging, to the geometric exit wave:
  ```
  venv/bin/python $S/repro_nostep.py 0.001
  slope 0.001 rad/A: no-step control passed=False delta=-0.0191 tol=0.0169
    step 0->1 built +2.7155: h = +2.7239 +- 0.0117 (+0.7 sigma) | control-related keys in the step record: []
    step 1->2 built -1.3577: h = -1.3489 +- 0.0058 (+1.5 sigma) | control-related keys in the step record: []
    step 2->0 built -1.3577: h = -1.3750 +- 0.0059 (-2.9 sigma) | control-related keys in the step record: []
  ```
* Reproduction 2 (`$S/branch_power.py`). It runs the pipeline's own `lattice_branch` with the demo
  settings on uniform random wrapped phases, i.e. phases with no height in them:
  ```
  smoke B19 sigma_phi 0.003 rad (sigma_h(a/4) ~ 0.0058 A): resolved 28.4%, ambiguous 0.0%, inconsistent 71.6%
  smoke B19 sigma_phi 0.100 rad (sigma_h(a/4) ~ 0.0134 A): resolved 57.8%, ambiguous 0.0%, inconsistent 42.2%
  HPC B32 sigma_phi 0.003 rad (sigma_h(a/4) ~ 0.0060 A): resolved 11.6%, ambiguous 8.1%, inconsistent 80.3%
  HPC B32 sigma_phi 0.100 rad (sigma_h(a/4) ~ 0.0137 A): resolved 32.0%, ambiguous 12.8%, inconsistent 55.1%
  HPC B32 sigma_phi 0.290 rad (sigma_h(a/4) ~ 0.0364 A): resolved 65.5%, ambiguous 34.5%, inconsistent 0.0%
  ```
* Mitigation: the summary's engine label says "multislice: UNVALIDATED", and the CLI prints the
  control verdict on the line after the heights. The step record itself carries no warning.
* Fix:
  * If the control was performed and did not pass, set `height=None` on every step with a reason
    that states delta and the tolerance.
  * Decide what happens when the control could not be performed, and record it in every step.
  * Report the chance-resolution rate of the lattice constraint for the run's sigma next to each
    "resolved" decision.
  * Until the multislice engine is validated, withhold multislice heights, or mark them invalid.

### M1 (Major). R2 (self-reference) is accepted, and its differential phase is quantified as an absolute phase: confident zero heights

* Where: `run.py:242-266` accepts R2 and builds the reference as the shifted object wave.
  `run.py:341-349` and `quantify.py:113-176` quantify it without change.
* What is wrong:
  * R2 reconstructs `phi(r) - phi(r + s)` (model_assumptions B5), but the pipeline uses region
    medians of this phase as terrace phases.
  * Wherever `r` and `r + s` lie on the same terrace, this phase is 0. The step phases are
    therefore about 0.
  * The lattice constraint accepts n = 0 (h = 0), although the pipeline itself knows that a step
    lies between the two regions. The no-step control passes because the phase is flat.
* Reproduction (`$S/repro_r2.py`). The smoke demo is run with `reference_model: R2`,
  `reference_trajectory: reflected_flat_area` and a B28 shift record; nothing else changes:
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
  Both demo configurations use R1, so the demos cannot reach this. Changing two CFG-B values is
  enough to reach it, and R2 is how the repository reads the P01 arrangement. P1 lists "R2
  through the pipeline" as NOT RUN.
* Fix:
  * Refuse quantification under R2 (reason: "differential phase, NOT IMPLEMENTED"), or build the
    R2 quantification, tracing the reference region through the same ray trace.
  * Exclude n = 0, or flag it, when the two regions straddle a known step.

### M2 (Major). The "comparison" gate lets demo stand-ins through for every non-blocking item, and accepts a rule-computed angle labelled PROJECT_INPUT

* Where: `config.py:58` (`BLOCKING_ITEMS`), `config.py:589-598` (the only purpose-dependent
  check), and `config.py:440-489` and `501-510` (the rule form of item 7).
* What is wrong (a):
  * `purpose: comparison` refuses ASSUMPTION stand-ins only for items 3, 4, 5, 7, 8, 11, 12 and 15.
  * These demo stand-ins still pass:
    * B24 (dose, gain, MTF; item 6).
    * B28 (carrier; item 16).
    * B29 (all processing; item 19, which docs/06 says must be the laboratory's own code path).
    * B31 (item 1).
    * B1 (item 20).
    * B17 (item 9).
    * B18 (item 14).
    * B27 (item 13).
  * Nothing in a comparison run's outputs singles these out. The registry comment says they are
    "used by configs/demo_*.yaml only", but nothing enforces that.
* What is wrong (b):
  * The rule form of `glancing_angle` may carry the label PROJECT_INPUT. The angle is then computed
    from the CFG-B V0, which may be the ASSUMPTION B1, and is recorded as PROJECT_INPUT.
  * docs/06 item 20 states that an angle computed from V0 biases h by 1.07 %/V at (0,0,8).
* Reproduction (`$S/repro_comparison_leak.py`). The script sets `purpose: comparison` and replaces
  every blocking stand-in with a fabricated PROJECT_INPUT "supplied by Auditor 2026-09-23":
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
* Fix:
  * Mark B19-B32 as demo-only in the registry, and refuse them under "comparison" whatever the
    item.
  * List every remaining ASSUMPTION in the comparison summary.
  * Refuse the PROJECT_INPUT label on the rule form of item 7, or give the computed angle the label
    of the V0 it used.

### M3 (Major). sigma_h treats the incidence and exit angle errors of the specular beam as independent, so it is 29 % too small

* Where:
  * `quantify.py:120-123` and `160-165` pass the same `angle_calibration_sigma` as both
    `sigma_theta_in_rad` and `sigma_theta_out_rad`.
  * `quantification/height.py:96` (out of scope) adds the two in quadrature.
  * The same sigma_s enters the branch window at `quantify.py:102`.
* What is wrong:
  * For the specular beam theta_out equals theta_in (docs/06 item 7), so one calibration error
    moves both angles together.
  * Hence `sigma_s = 2 k cos(theta) sigma_theta`, not `sqrt(2) k cos(theta) sigma_theta`.
  * The angle term dominates sigma_h for every demo step.
* Reproduction (recomputed from the summary of the smoke run `$S/smoke_run1`):
  ```
  pipeline sigma_s 0.035425908523705946
  independent (in quadrature) 0.035425812359492714  fully correlated (theta_out = theta_in) 0.050099664296879
  h=+2.7156 reported sigma_h=0.0117  correlated-angle sigma_h=0.0165  ratio=0.707
  h=-1.3576 reported sigma_h=0.0058  correlated-angle sigma_h=0.0082  ratio=0.708
  ```
  The P1 and README value "+2.7156 +- 0.0117 A" should read about +- 0.0165 A. The tests cannot see
  this because the simulation has no angle error.
* Fix: add a correlated specular path to the uncertainty (`ds/dtheta = 2 k cos theta`), use it in
  `lattice_branch` and in `height_from_phase`, and unit-test it.

### M4 (Major, operational). The SLURM job dies at random before the run when PYTHONUNBUFFERED is set: `dry-run | head -12` under `set -euo pipefail`

* Where: `scripts/hpc/run_pipeline.slurm:20` and `:100`.
* What is wrong:
  * `head` exits after 12 lines. With unbuffered stdout, Python can still be writing at that
    point.
  * The pending write raises `BrokenPipeError` and Python exits with status 1.
  * `pipefail` then marks the pipeline as failed, and `set -e` ends the job before `run`.
  * With buffered stdout the 4.6 kB of output is written once at exit, and this has not been seen
    to fail.
  * Many job templates export `PYTHONUNBUFFERED=1`, and this sandbox does too.
* Reproduction. My first simulated job-mode run died this way:
  ```
  SLURM_JOB_ID=4242 RH_OUT=$S/slurm_job_smoke RH_MODE=smoke RH_ACCOUNT=a RH_PARTITION=p \
    RH_TIME_LIMIT=00:10:00 RH_GPU=none bash scripts/hpc/run_pipeline.slurm      -> exit 1
    File ".../reflection_holo/pipeline/__main__.py", line 91, in main
      print(json.dumps(rep, indent=1, default=str)[:4000])
  BrokenPipeError: [Errno 32] Broken pipe
  60 x: bash -c 'set -euo pipefail; venv/bin/python -m reflection_holo.pipeline dry-run \
        --config configs/demo_smoke_si001.yaml | head -12 > /dev/null'
  PYTHONUNBUFFERED=1: 26 / 60 failed
  PYTHONUNBUFFERED unset: 0 / 60 failed
  ```
  On the GPU job the failure comes after a 46 s dry-run. The job produces no summary and exits 1.
* Fix: write the dry-run output to a file in `$OUT`, or append `|| true`, or disable `pipefail`
  locally. Also catch `BrokenPipeError` in `__main__.py`.

### M5 (Major). Without `.git` the whole simulation runs, then the manifest refuses, leaving no summary, no manifest and unlabelled arrays

* Where:
  * `run.py:441` (arrays) and `:501` (quicklooks) run before `run.py:503-519` (`build_manifest`,
    which raises `RuntimeError` unless `allow_no_git` is set).
  * `__main__.py:113-121` does not catch the error.
  * `run_pipeline.slurm:101` has no way to pass `--allow-no-git` and never checks the git state.
* Reproduction. `$S/nogit` is a copy of `reflection_holo/` and `configs/` without `.git`:
  ```
  PYTHONPATH=$S/nogit venv/bin/python -m reflection_holo.pipeline run --config configs/demo_smoke_si001.yaml --out $S/nogit_out1   -> exit 1
  RuntimeError: git state of the repository unavailable (CalledProcessError: ... rev-parse HEAD ...
  ls $S/nogit_out1 -> arrays.npz quicklook_detector.png quicklook_exit_wave.png
  ```
  With `--allow-no-git` the run completes, and the manifest records the error and
  `allowed_without_git: true` (verified). On the HPC demo, the late failure wastes the full engine
  time (18.8 min on CPU per P1).
* Fix: check the git state at the start of `run()`, and in submission mode of the SLURM script.
  Without git, hash the package tree so the code is still identified.

### M6 (Major). Supplied PROJECT_INPUT values that the run cannot represent are accepted, not applied, and listed as SUPPLIED

* Where:
  * `run.py:185-201` and `engines.py:161-215`: the multislice path never reads
    `convergence_semi_angle` (item 3) and builds no overlayer (item 12).
  * `pipeline/` never reads `pattern_geometry` (item 13) or `target_reflection_hkl` (item 9); grep
    finds 0 references to each.
  * The angle rule takes its `reflection_hkl` from its own record (`config.py:449`) and never
    checks it against item 9.
* What is wrong:
  * The geometric engine refuses convergence and overlayers (`model.py:193-209`), but the other
    paths run with the default the engine happens to have.
  * The summary's `inputs` table still shows the item as SUPPLIED, so the output claims an input
    the simulation never used.
  * This contradicts docs/05 criterion 5 and docs/06 item 12 ("must be modelled rather than
    ignored").
* Reproductions (`$S/repro_convergence.py`, `$S/repro_ignored_inputs.py`, `$S/repro_item9.py`; all
  values are fabricated as "supplied"):
  ```
  convergence 0.5 mrad, geometric: REFUSED OutsideB4ScopeError: illumination 'convergent' ...
  convergence 0.5 mrad, multislice_tiny: RAN; item 3 in summary: status 'SUPPLIED (Auditor 2026-09-23)', value 0.5;
      'convergen' mentioned in engine record/params: False
  pattern_geometry {features: [mesa 10 nm x 200 nm]}, geometric: RAN, heights [(0,1,2.7156), (1,2,-1.3576), (2,0,-1.3580)]
  overlayer SiO2 10 A, multislice_tiny: RAN (engine multislice)
  target_reflection_hkl [0,0,12] SUPPLIED: gate PASSED; angle computed for [0, 0, 8] = 16.474333 mrad
  ```
  The demo configurations do not trigger any of these.
* Fix: in the gate, per engine, refuse:
  * a non-zero convergence;
  * an overlayer other than none;
  * pattern features other than none;
  * a rule `reflection_hkl` that differs from item 9.

### Minor

* m1. "purpose: demo" does not reach every output.
  * Where: `run.py:441` writes `arrays.npz` with no purpose. `engines.py:225-228` calls
    `ms.simulate(..., config=None, input_paths=[])`.
  * As a result, the multislice engine's own manifest (and the exit waves it saves: the HPC demo
    sets `save_exit_waves: true`) carries no purpose. It also states "no configuration file
    (stated explicitly by the caller)", which is false.
  * Reproduction:
    ```
    np.load(smoke_run1/arrays.npz).files -> no purpose key
    ms_tiny/outputs/manifests/*.json: config {'path': None, ..., 'note': 'no configuration file (stated explicitly by the caller)'}, inputs [], 'purpose' anywhere: False
    ```
  * Fix: store a `purpose` scalar in the npz, and pass the config path and purpose to the engine.
* m2. `list-inputs` misreports item 20 for multislice runs (`config.py:713-743`).
  * It shows `ASSUMPTION B1 stand-in cfg_b.mean_inner_potential_V 12.0`.
  * The angle and the potential actually use `potential_mip` = 13.903 V (label REPRODUCED), which
    is not listed at all.
  * Evidence: `$S/listinputs_hpc.txt`, row 20.
  * Items 9 and 13 are listed as if the run used them (see M6).
* m3. The multislice dark field includes the field inside the crystal.
  * The internal Bragg wave (theta_int = 18.47 mrad) lies 2.34 mrad from k_out (16.13 mrad),
    inside the 3 mrad aperture. No real-space mask removes it (`darkfield.py:162-165`).
  * `A_emp` is computed over all bright pixels regardless of trace status (`run.py:235-237`).
  * In the tiny run, the exit |psi| RMS is 0.378 below the surface against 0.060 in vacuum above
    it.
  * On the detector, below-surface pixels have |obj| mean 0.094, above the lit mean of 0.069.
  * 32 of the 400 bright pixels are below the surface, and 48 lie on shadow or riser pixels.
  * The eroded regions probably avoid this at HPC scale, but it is not checked.
  * The engine band-limit check at `darkfield.py:149-153` is inert for the multislice engine,
    because its metadata has no `band_limit_cycles_per_A`.
* m4. The HPC demo angle (B32, 16.1347 mrad) makes the sign of the a/2 step degenerate.
  * Relevant lines: `configs/demo_hpc_si001.yaml:222` and `quantify.py:89-110`.
  * +a/2 and -a/2 differ by 0.078 rad (0.0096 A) of wrapped phase, so a noise-free a/2 phase is
    always "ambiguous":
    ```
    true h +2.7155, sigma_phi 0.003: decision ambiguous  [(2.7155, 0.0, 0.0119), (-2.7251, 0.0096, 0.0119)]
    ```
    (`$S/branch_degeneracy.py`). At B19 the separation is 0.846 rad, and the step resolves.
  * The HPC demo can therefore never report an a/2 height. The fix is to choose a different angle,
    or to state this in the README.
* m5. No pre-flight check that cupy imports or that a GPU is visible.
  * `dry-run` reports `multislice_available: true` and exits 0 without cupy (`engines.py:128-149`,
    `estimates.py:72-73`).
  * The script submits a cupy job with `RH_GPU=gpu:1` without checking (`run_pipeline.slurm:69-73`).
  * Reproduction: `import cupy` raises ModuleNotFoundError, yet the HPC dry-run exits 0 and the
    fake `sbatch` accepts the submission.
  * The engine has no fallback (`backend.py`), so the failure comes late: the run fails with an
    uncaught ImportError.
* m6. Robustness of the SLURM script.
  * `status=$?` and the log copy never run after a failure, because of `set -e` (lines 101-104).
  * The config pre-check (line 60) runs before `cd "$REPO"` (line 90). A job submitted from another
    directory therefore fails with `FileNotFoundError: 'configs/demo_smoke_si001.yaml'`
    (reproduced).
  * `RH_CPUS` defaults to 8 whatever `--cpus-per-task` was given to a direct `sbatch`.
* m7. `scripts/hpc/null_test_study/run_study.py`.
  * At 281074a it imported the untracked `tests/forward/null_test_cases.py` and read a
    `study.yaml` that did not exist, so it cannot run from a clone of 281074a.
  * It overwrites its result JSONs (line 135, `write_text`).
  * It reads YAML with `yaml.safe_load` (line 85), so duplicate keys are not refused.
  * It reads TEST_ONLY stand-ins from a file, bypassing the pipeline gate.
  * Another agent is still editing it.
* m8. Several refusals end in a traceback with exit status 1 instead of a mapped exit code
  (`__main__.py:113-121`): the documented B4 refusal (`OutsideB4ScopeError`), a missing cupy
  (`ImportError`) and a missing git state (`RuntimeError`).

### Nits

* n1. `darkfield.py:135` validates the wave's angle against itself, a no-op. The pipeline does
  check the angle in `engines.py:123/236`.
* n2. Stale docstrings:
  * `optics/__init__.py:5-6` says dark-field and projection are not implemented.
  * `detector.py:56` lists only "centre".
* n3. `_prepare_out` reuses an empty existing directory. Two concurrent runs into one directory
  overwrite `arrays.npz` (`run.py:83-89, 441`).
* n4. Each hologram is scaled to its own mean dose (`hologram.py:370-373`), so the reference-beam
  dose differs between the object and empty holograms. This affects the noise only.
* n5. In a multislice run, the summary's `surface_strips` list the builder's boundary step, which
  the open cell lacks (`run.py:358-362`).
* n6. In the HPC config, `angle_calibration_sigma` cites B19 (`demo_hpc_si001.yaml:235`) in a run whose angle is B32.
* n7. The job rebuilds the 1.44-million-atom structure in `dry-run` (46 s) only to print 12
  lines.

## Test adequacy (tests/pipeline, tests/forward_geometric: 26 passed, 68 s)

What the tests check, and check well:
* Signed heights, including the required down-step sign reversal.
* The step phase against `wrap(-q.n h_built)` within 3 sigma_phi, which is tight (0.008 rad).
* Region pixels are lit only.
* The shadow and riser bands on the exit plane (within 2 px).
* B4, overlayer, convergence and 300 keV refusals.
* The aperture sign: an incident component at -q_out is removed.
* Projection direction and samplings.
* Band-limited resampling and refusals.
* Refusal of a missing input and of an unregistered stand-in.
* No overwrite.

Gaps:
* No test that a failed control blocks heights (B1), no R2 test through the pipeline (M1), and no
  "comparison" run with non-blocking stand-ins (M2).
* sigma_h is never tested (M3). The criterion |h - h_built| <= 3 sigma_h is about 35x looser than
  the phase precision (sigma_phi/s = 0.0003 A). The phase criterion covers this.
* The detector tests use isotropic pixels, so a swap of the along-beam and perpendicular axes
  would pass.
* `purpose` is asserted only in `summary.json`.
* The `list-inputs` test checks one string.
* No test for the SLURM script, a missing `.git`, or a missing cupy.
* The geometric tests never use `periods_along_beam > 1` with transverse edges. This is harmless:
  `R_period` has x = 0, and only x matters for the specular q.
* `test_shadow_exclusion` checks the strip lengths from `structure.shadows`, not the pipeline's ray
  trace (the ray trace is checked in `forward_geometric`).
* The multislice tests check bookkeeping only, as they say.

## Verified correct

1. Refraction-corrected angle. An independent script (CODATA constants, exact relativistic
   Delta, internal Bragg (0,0,8), no package code) gives:

   | V0 | theta_int | theta_ext |
   |---|---|---|
   | 12.0 V | 18.471996 mrad | 16.474333 mrad |
   | 13.903 V | — | 16.134720 mrad |

   These equal the smoke summary (16.474332799 mrad; theta_int 18.471996329) and the HPC dry-run
   (16.134720 mrad).
2. Signs of the step phase and the height.
   * The engine phase is `-q.R_k`, so a higher terrace has a more negative phase. This follows
     physics_conventions.
   * Recomputed independently, the expected wrapped phases are +2.718515 rad (a/2 up) and
     -1.359257 rad (a/4 down). The measured values are:

     | Step | Measured | Deviation |
     |---|---|---|
     | a/2 up | +2.716987 | 0.6 sigma |
     | a/4 down | -1.359887 | 0.2 sigma |
     | a/4 down | -1.357101 | 0.9 sigma |

   * Heights recomputed independently from the measured phases and chosen branches are +2.715635,
     -1.357649 and -1.357986 A, identical to the pipeline's.
   * A conjugated reconstruction would give -2.7155, which the tests would catch.
3. Smoke CLI output. It reproduces P1 exactly: +2.7156 +- 0.0117, -1.3576 +- 0.0058 and -1.3580 +-
   0.0058 A, all branches "resolved", and the control passes (-0.0037 against 0.0123 rad).
4. Dark-field aperture. It is an exact angular disc of 3 mrad centred on +sin(theta)/lambda (k_out,
   k_x > 0). Demodulation multiplies by exp(-2 pi i q_out x) at the absolute x, and the carrier of
   the geometric engine is `k_out[0] x`, which is consistent.
5. Projection.
   * z_s = (x0 - x)/tan(theta), with x0 = H_ref + (L - z_start) tan(theta).
   * The rows are flipped, so u increases downstream, and du = dx cos(theta).
   * The detector trace inverts this correctly (x = x0 - u/cos(theta)).
   * On the detector, the shadow and riser bands are 2-3 px wide against the expected
     h cos(theta)/p = 2.72 px. The a/2 blocked-view strip is not imaged, as the physics requires.
6. Detector.
   * pitch/M matches the image pixel on both axes.
   * The aperture band (0.120 cycles/A) is below the Nyquist frequency on both axes.
   * The hologram's highest frequency (carrier 0.5 + 0.12) is below the detector Nyquist frequency
     (1.0).
   * The ROI lies inside the field.
7. Same optics and carrier.
   * The object and empty holograms use the same R1 reference (same function, carrier, amplitude
     and phase), the same detector spec and one seeded generator.
   * The empty object branch is a uniform vacuum wave. This is valid because the aperture is
     centred on k_out.
   * The carrier is located on the EMPTY hologram (`run.py:289`) at the -q_ref sideband
     (phi_o - phi_r).
8. Refusals and safe outcomes.
   * Refusals give a reason: not measurable, a/4 outside B4 (the phase is reported), zero scatter,
     an inconsistent or ambiguous branch, a small denominator.
   * With a coarse carrier (4.0 and 6.4 A) the steps are "not measurable" rather than given a
     number (`$S/repro_carrier.py`).
   * The multislice MIP check holds: 13.90284 against 13.903 V, tolerance 5e-4 V.
9. Output directories are never overwritten. A non-empty output directory gives exit 5, both from
   the CLI and in SLURM job mode.
10. Manifest. It records the commit, dirty flag, branch, diff hash and untracked files. With
    `--allow-no-git` it records the error.
11. SLURM checks.
    * Unfilled placeholders give exit 2 in both modes, including an empty `RH_GPU`.
    * cupy with GPU=none is refused.
    * CPUS < threads is refused.
    * The OMP, OpenBLAS, MKL and NumExpr thread variables are set to `runtime.threads`.
    * The job directory name is unique (job id plus UTC stamp).
12. The purpose banner appears in `summary.json`, in the manifest's `extra`, in the CLI stdout and
    in the quicklook titles. The smoke `list-inputs` output is truthful, except as noted in m2 and
    M6.

## Commands run (repository root unless stated; all outputs under `$S`)

```
git log --oneline -6; git status --short; git show --stat HEAD; git diff --stat 281074a HEAD -- <scope>
venv/bin/python -m reflection_holo.pipeline list-inputs --config configs/demo_smoke_si001.yaml   (exit 0)
venv/bin/python -m reflection_holo.pipeline list-inputs --config configs/demo_hpc_si001.yaml     (exit 0)
venv/bin/python -m reflection_holo.pipeline run --config configs/demo_smoke_si001.yaml --out $S/smoke_run1   (exit 0, 2.8 s)
venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml        (exit 0, 46.5 s)
venv/bin/python -m reflection_holo.pipeline run --config configs/demo_smoke_si001.yaml --variant multislice_tiny --out $S/ms_tiny   (exit 0, 18.6 s)
venv/bin/python -m reflection_holo.pipeline run --config configs/demo_hpc_si001.yaml --variant geometric_same_structure --out $S/hpc_geom   (exit 0, 13 s; +2.7151, -1.3578, -1.3573 A)
venv/bin/python -c "import cupy"                                                                (ModuleNotFoundError)
venv/bin/python $S/indep_height.py; $S/repro_comparison_leak.py; $S/repro_r2.py; $S/repro_nostep.py 0.001|0.002;
  $S/repro_convergence.py; $S/repro_ignored_inputs.py; $S/repro_item9.py; $S/repro_carrier.py;
  $S/branch_degeneracy.py; $S/branch_power.py; inline checks of summary/arrays (sigma_s, npz keys, strip widths, ms_tiny amplitudes)
PATH=$S/fakebin:$PATH bash scripts/hpc/run_pipeline.slurm   (T1-T6 submission mode with a fake sbatch; J1-J3 job mode with SLURM_JOB_ID set, smoke config)
60+60 x bash -c 'set -euo pipefail; venv/bin/python -m reflection_holo.pipeline dry-run ... | head -12'
PYTHONPATH=$S/nogit venv/bin/python -m reflection_holo.pipeline run ... [--allow-no-git]   (copy without .git)
venv/bin/pytest -q -p no:cacheprovider tests/pipeline tests/forward_geometric                  (26 passed, 68.37 s)
```

## NOT RUN

* The HPC multislice run itself (`demo_hpc_si001.yaml`, cupy on GPU or `cpu_numpy`). There is no
  GPU here, and the 18.8 min CPU run was not repeated while another agent diagnoses the engine.
* A real `sbatch` submission (only the fake `sbatch`).
* `setup_env.sh`, which would install packages.
* The full test suite (only the in-scope suites were run).
* `run_study.py`, whose files are being edited by another agent.
* Frozen-phonon ensembles (`n_realisations > 1`) and parallel step edges through the pipeline.
