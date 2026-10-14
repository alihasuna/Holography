# F. M2 reflection-multislice code audit (pre-rocking/steps)

Status: IN PROGRESS (2026-10-14). Auditor: code-auditor subagent. Commit audited: d404587
(branch trixode-studios-claude/sweet-carson-2grkn2). The code under audit was not modified.
Scratch scripts: /tmp/claude-0/-home-user-Holography/57d40492-0c74-558e-a50e-ca09e117ea85/scratchpad/F_audit/
(abbreviated `$S/` below). Python: /tmp/claude-0/venv/bin/python (numpy 2.5.4, scipy 1.18.1, h5py 3.16.0,
pytest 9.1.1). Evidence labels: REPRODUCED (synthetic CPU reproduction in this audit), DERIVED_HERE,
PLAUSIBLE (not reproduced; what would confirm it is stated), SECTION_READ (code read, no run).

## Commands run (log)

| # | Command | Result |
|---|---|---|
| 1 | `python -m pytest -q -m "not slow" -p no:cacheprovider` (repo root) | 49 passed, 5 deselected, 0.74 s |
| 2 | `python -m reflection_holo.campaign plan --config configs/fir_m2_campaign.yaml --stage all --out $S/RUN_plan` | 36 / 172 / 1892 / 867 tasks (2967), max memory 0.72 / 7.47 / 15.98 / 17.40 GB: matches docs/08 |
| 3 | `python $S/mem_check.py $S/RUN_plan` | peak GPU memory incl. analysis temporaries <= 25.4 GB (planner says 17.4): no OOM risk on 80 GB |
| 4 | `python $S/r1_gate_failopen.py` | validation/convergence verdicts pass on missing inputs (F-01) |
| 5 | `python $S/r2_rung1_vacuous.py $S/RUN_plan` and `python $S/r2b_rung1_tolerance.py $S/RUN_plan $S/r2_rung1_vacuous.py` | rung-1 sub-checks at 0.2 A, 30/40 mrad are weak (F-07) |
| 6 | `python $S/r3_vbar_V0.py` | laterally averaged bulk potential of the real atom columns = 13.9021-13.9031 V vs V0 = 13.90284 V (rel. dev <= 4.6e-5) for all surfaces/levels; top sheet of level L at L*h_unit: potential normalisation, atom density and terrace cuts correct |
| 7 | `python $S/r4_vdp_synthetic.py`, `python $S/r4b_vdp_synthetic_down.py` | analytic field of a z-invariant reflector with known rho(theta, qy) plus a 1e-3 down-going wave: vdp_reflectivity error 5.2e-11, D recovered to 3.9e-13, vdp_angle_resolved error 1.5e-11 over all (theta, qy), strip_mean = direct real-space mean to 4e-11. The Jacobian 2 pi q/kz, the up/down split, x_ref and the sinc kernel are correct |
| 8 | `python $S/r5_truncation_bound.py` | bound exact for a single exponential tail; 0.07 x the missing part for a weak slow tail hidden under a fast one at a premature stop (A12 caveat); adaptive stop (1e-5) on that record waits until the slow tail dominates |
| 9 | `python $S/r6_steps_phonon_no_average.py` | aggregate_steps reports each phonon seed separately (F-02) |
| 10 | `python $S/r8_batch_vs_single.py`, `python $S/r8b_batch_adaptive.py` | batched march (B=3, stops at different planes, adaptive and cap) identical to single-beam marches: exits, records, stop planes (0.0 difference) |
| 11 | `python $S/r9_worker_claim_race.py $S` | clean() removes a live-but-empty claim; a vanished claim kills the worker (F-05) |
| 12 | `python -m reflection_holo.campaign check ... --benchmark $S/bench_assumed.json` and `python $S/r10_task_durations.py $S/RUN_plan` | rocking 43.3 GPU-h (10.8 h on 4 GPUs) at planned lengths, 173 GPU-h if all ran to the cap; steps 35.6 / 142.5 GPU-h; longest task 710 s (rocking) / 1348 s (steps) at the cap |
| 13 | task_id uniqueness check (inline python) | 36/172/1892/867 unique ids, no id shared between stages |
| 14 | parallel-step cell parity (inline python) | si001_100 (37 periods) and the 100 A Si(111) cell (15 periods): second riser mid-period (F-08) |
| 15 | `git diff --stat d404587 HEAD` | only docs/agent_reports changed since the audited commit |
| 16 | `python $S/r7_phonon_beam_dependence.py static 0 $S/fp/static.npz` (smoke numerics, 'tall' preset, Si(111) L0, one march with two beams w0 = 6 and 12 A at 16 mrad) | 1389 s; 26585 planes; w0 = 6 A beam stopped at its cap, w0 = 12 A adaptively; static beam independence max \|r_w6 - r_w12\| = 3.6e-4 over 115 shared angles (bounds sum <= 2.5e-3) |
| 17 | `python $S/r7_phonon_beam_dependence.py frozen_phonon {1,2,3} ...` then `python $S/r7_analyse.py $S` | see F-03 |
| 18 | micro end-to-end run: `$S/micro.yaml` (smoke physics, dx 0.2 A, Si(111) only), `campaign plan` (10 rocking + 6 steps tasks), `worker run`, `worker status`, `aggregate --stage rocking` and `--stage steps` (`$S/run_micro.sh`) | 10/10 rocking tasks, aggregate exit 0; steps aggregate on 4 real results exit 0 (one phonon-step worker stopped by me to free CPU): the aggregators do not crash on real `.h5` output |
| 19 | `python $S/r11_tail_content.py $S/RUN_micro/results/rocking/*.h5`, `python $S/r12_r_vs_weight.py ...`, inline stop-behaviour listing | every frozen-phonon window ran to the cap with a near-grazing tail; static 13 mrad windows stopped at 1.0x planned (F-14, F-03) |

NOT RUN: anything on a GPU or with CuPy (no GPU here; CuPy paths checked by reading only); the slow CPU
validation tests (`pytest -m slow`, about 30 min on four free cores; the cores were in use by the
runs above); any production-size task; `validation/abtem_crosscheck.py`; the Slurm scripts (no
Slurm here; checked by reading and a bash pattern check only).


## Findings (ordered by severity)

### F-01 (Major, type a+c) Validation and convergence verdicts fail open on missing or empty inputs — REPRODUCED

* `reflection_holo/aggregate.py:259-261`: `all_pass = all(... for d in S["rung1"] + S["rung2"]) and
  all(v.get("pass", True) ...)`. Empty lists are `True`; rung-3 and beam-independence entries without a
  `pass` key count as passing.
* `aggregate.py:243-245`: a rung-3 entry gets a `pass` key only `if ... and n` (n = points with
  |r| >= 1e-2); n = 0 means no key, i.e. pass. `aggregate.py:228-229`: if the level-0 task is missing
  the whole surface is skipped. `aggregate.py:255-257`: same for beam independence (`if c.get("n")`).
* `aggregate.py:296-297`: `converged` requires only that the gates PRESENT pass; missing gate tasks
  are not counted.
* `fir/run_stage.sbatch:44-55`: tasks that failed twice are excluded from REMAINING, so the stage goes
  to aggregation with them absent. Nothing compares `n_results` with the number of planned tasks.

Reproduction (`$S/r1_gate_failopen.py`, synthetic result dicts fed to the real functions):
```
(a) empty validation stage: all_pass = True
(b) only one rung-1 result: all_pass = True | rung2 entries: 0 | rung3 entries: 0
(c) rung-3 si111 L1 with |r|<1e-2: n = 0 | 'pass' key present: False | all_pass = True
(d) rung-3 level-1 result missing: rung3 entries = 0 | all_pass = True
(e) convergence with 1 of 5 gates present: converged = True | variants: ['delay 9.0 decay lengths']
(f) gate 30 pct off with bound 0.1: max_abs_diff = 0.060, max_abs_excess = -0.040, converged = True
```
Why it matters: a GPU-path exception that hits a whole task kind (for example `uniform_1d` or
`averaged_1d`, which `fir/gpu_selftest.py` does not exercise on CuPy) twice would remove that rung from
the ladder and the chain would still start convergence, rocking and steps. Item (f) is by design
(bounds are subtracted) but there is no cap on the bound or check of `stopped_at_cap`.
Fix: compare the number of results per rung, surface, level, waist and gate with the plan (36 and 172);
require n > 0 for every null test and beam-independence pair; treat a missing gate as a failure.
Immediate action for the running campaign: check `RUN/summary/validation/summary.json` `n_results == 36`,
`RUN/summary/convergence/summary.json` `n_results == 172`, every rung-3 translation/mirror entry has
`n > 0` and a `pass` key, and `RUN/failed/` is empty for these stages, before rocking starts.

### F-02 (Major, type a) Frozen-phonon step runs are never averaged over seeds — REPRODUCED

`reflection_holo/aggregate.py:447-496` loops over every `step_image` result and names each by its seed
(`aggregate.py:457-458`, `|seed{t.get('seed')}`); there is no grouping over seeds and no coherent
average of `ar_rho` (or of the transverse spectra). `$S/r6_steps_phonon_no_average.py`:
```
parallel entries: ['si111_110|steps_parallel|[0, 1]|13.3mrad|frozen_phonon|seed0',
                   'si111_110|steps_parallel|[0, 1]|13.3mrad|frozen_phonon|seed1']
```
Why it matters: 448 of the 867 steps tasks are frozen-phonon runs (32 seeds x 14 parallel conditions).
docs/08 appendix A9 states that the configuration-averaged object wave <u_o>, i.e. the coherent mean
over seeds, is what a hologram measures. A single configuration is not uniform along the beam, so
kappa is not conserved and appendix A13 (rho = U (2 pi q/kz)/A(-q) is the plane-wave response) does
not hold per seed: each seed's rho carries diffuse intensity scattered in from every other angle of
the beam (see F-03). The per-seed step phases, residuals and strip-versus-flat deviations in
`summary/steps/summary.json` are therefore neither the thermal step phase nor a null test.
Fix (aggregation only): group step results by (surface, levels, angle, w0, Ly) and mode, average the
complex `ar_rho` over seeds before forming strip means, report the seed count and standard error.
The per-seed `ar_rho` is stored (complex64) in every `.h5`, so no GPU rerun is needed.

### F-03 (Major, type a) Per-seed frozen-phonon r, the incoherent intensity and the "diffuse fraction" depend on the beam — DERIVED_HERE; reproduction PENDING (see below)

(being filled in)

### F-04 (Major, type c, process) The jobs execute whatever code is checked out at run time — SECTION_READ

`fir/run_stage.sbatch:21-22,25,37,77` `cd` to the submit directory (the repository) and run
`python -m reflection_holo.worker` / `aggregate` from the working tree. Tasks are frozen in
`tasks_<stage>.jsonl` at submission (`fir/submit_campaign.sh:112`), but the simulation and aggregation
code is whatever the checkout contains when each job (and each resubmission) starts. A `git pull`
or edit on Fir while rocking or steps runs would mix code versions inside a stage; the task_id
(content hash) does not change, so finished results are silently reused. `provenance.py:28-37`
records the commit and a dirty flag per task, so a mix is detectable after the fact.
Consequence for the decision now: aggregation-only fixes (F-01, F-02, F-03, F-11) can safely be
applied by re-running `python -m reflection_holo.aggregate` later on the existing `.h5` files, but
nothing in `reflection_holo/` should be changed in the Fir checkout while a stage is running. If a
fix to `aggregate.py` is wanted for the automatic end-of-stage aggregation, it must not touch
simulate/analysis/potential/multislice. Check afterwards that `manifest.git.commit` is identical
for all `.h5` of a stage.

### F-14 (Minor for results, Major for the schedule) Frozen-phonon records never meet the tail criterion: every phonon task runs to the 4x cap, and its truncation bound is meaningless — REPRODUCED (micro scale)

`multislice.py:91-99` stops a beam when max |y-mean of the line-1 record| over the last 400 planes
falls below `tail_tol` x its running maximum. In a frozen-phonon configuration the crystal is not
uniform along z, so diffuse scattering fills near-grazing exit directions (theta_x of 1-2 mrad,
qy = 0 included); those waves cross the detector line tens of micrometres downstream and keep the
record from decaying. Micro run (`$S/micro.yaml`: smoke physics, dx 0.2 A, Si(111) level 1, seed 1;
`python -m reflection_holo.worker run ...`, then `python $S/r11_tail_content.py ...`):
```
si111_110 level 1 phonon 1 th0=13.0: n=24131, stop z=46333 (cap True), |r| 1.36e-02-1.04e+00, bound max 1.4e+00, tail_rho 0.953
   envelope (max|f| per 500 planes / peak, every 10th block): 3e-04 1e+00 9e-03 6e-03 5e-03
   tail power: exit angle < 2 mrad: 0.11; within +-2.5 mrad of the window centre: 0.000; strongest components at theta_x (mrad): [1.79 1.89 1.67 2.   1.55]
si111_110 level 1 phonon 1 th0=16.5: n=18946, stop z=36377 (cap True), |r| 6.17e-03-1.75e+00, bound max 7.1e-01, tail_rho 0.956
   tail power: ... within +-2.5 mrad of the window centre: 0.000; strongest components at theta_x (mrad): [2.09 2.19 2.   2.28 1.89]
```
The tail plateaus at 5e-3 to 2e-2 of the peak, two to three orders above the smoke tail_tol (1e-4)
and three above production (1e-5). Its power sits at theta_x ~ 2 mrad, none near the specular
window, yet `truncation_bound` (`analysis.py:233-254`, an unwindowed transform of the last segment
times rho/(1-rho) = 20) reports 1.4 and 0.71 in r units because the near-grazing tail leaks into the
specular kappa. Consequences:
* Every frozen-phonon task (1792 of 1892 in rocking, 448 of 867 in steps) will run to
  `cell_cap_factor` = 4 times its planned length. The planner's 10.8 h (rocking) and 8.9 h (steps) on
  4 GPUs assume the planned lengths; at the cap they are 43 h and 36 h (command 12). Rocking will
  need the self-resubmission path (F-06), and steps will start correspondingly later than planned.
  The static w0 = 6 A smoke beam also ran to its cap (R7, 0.1 A sampling, tail_tol 1e-4), so static
  tasks may also run long at the stricter production 1e-5.
* `r_truncation_bound` of frozen-phonon windows is not a truncation estimate. The aggregator does
  not use it for phonon ensembles (it uses the seed standard error, `aggregate.py:322-324`), so the
  summary is unaffected, but the stored per-window bounds must not be quoted.
* The coherent mean is not biased by this (the near-grazing field has zero configuration mean), but
  per-seed quantities are contaminated (F-03).
Fix (only if the schedule matters): base the stop test on the up-going part at the window's kappa
range, for example on the windowed spectrum of the record, or on the coherent qy = 0 component
within the beam's kappa band; compute the bound with a tapered transform.

### F-05 (Minor, type c) Claim cleanup races and a vanished claim kills the worker — REPRODUCED

* `reflection_holo/worker.py:141-153`: a claim whose JSON is not yet written (created by O_EXCL a
  moment earlier) parses as `{}`, its job becomes "None", and it is deleted even though its job is
  running. Only possible when two jobs share a run directory (for example the manual rerun in
  fir/README.md section 3 while the chain's job runs).
* `worker.py:110` and `worker.py:116`: `os.remove(c)` is inside the `try`; if the claim is gone the
  successful task is booked as a failure, then the second `os.remove` in the `except` raises and the
  worker process exits, abandoning its remaining tasks for this job.

`$S/r9_worker_claim_race.py`:
```
removed 1 stale claims of 2
(1) claims left: ['def.claim']                    # the empty claim of live job 777 was removed
(2) worker died: FileNotFoundError ... claims/t0.claim
    results: ['t0.h5'] | failed files: ['t0.1.txt']   # success recorded as failure; t1 never tried
```
Fix: write the claim content via a temporary file and `os.link`, or treat unreadable claims younger
than a few minutes as alive; use `os.remove` with `FileNotFoundError` suppressed, outside the try.
Not a risk for the planned chain (stage jobs never overlap), only for manual reruns.

### F-06 (Minor, type c) A worker overrunning the walltime breaks the chain — PLAUSIBLE

`fir/run_stage.sbatch` has no `--signal`/trap; resubmission and the dependency hand-off
(`run_stage.sbatch:55-71`) run only after all workers return. `worker.py:87-91`: the first task of
each worker is never deadline-checked, and later tasks use `need = rate * cost * 1.5` where `cost`
is the PLANNED length, while a task may run to `cell_cap_factor` = 4 times that. Planner cost model
(`$S/r10_task_durations.py`): rocking 10.8 h on 4 GPUs at planned lengths but 43.3 h if every task
ran to its cap; steps 8.9 h vs 35.6 h; longest single task 710 s (rocking) and 1348 s (steps) at the
cap, against a 900 s margin. If a stage needs more than one 24 h job and a long task overruns, Slurm
kills the job, no resubmission happens, the next stage's `afterok` can never be satisfied and steps
never starts. Tasks are sorted longest first, so the risk is small. Confirm with: the rocking job's
`sacct` state (TIMEOUT vs exit 3). Fix: `#SBATCH --signal=B:USR1@1800` with a trap that stops
claiming and runs the resubmission block; base `need` on the cap.

### F-07 (Minor, type b for a stronger test; a for reporting) Rung-1 checks at 0.2 A width, 30 and 40 mrad are nearly vacuous — REPRODUCED

`configs/benchmarks.yaml` rung 1: amp_abs_floor 1e-6, phase only where |r| >= 1e-4. With the production
rung-1 tasks the Parratt |r| over the weight >= 0.05 window is 1.7e-5..4.3e-5 at 30 mrad and
5.8e-7..1.46e-6 at 40 mrad for the 0.2 A step. Largest uniform error that still passes
(`$S/r2b_rung1_tolerance.py`):
```
width  W   theta0  max eps passing   max phase error passing (rad)
 0.20  0.5   30.0     0.0230            0.0230
 0.20  0.5   40.0     0.6825            0.6961
(all 0.05 A cases and the 0.2 A cases at 6-20 mrad: 0.0030 and 0.002-0.003)
```
The 0.05 A step keeps rung 1 meaningful up to 40 mrad (|r| ~ 3e-3), so the ladder as a whole is not
vacuous; the 0.2 A / 40 mrad entries should not be quoted as passing checks.

### F-08 (Minor, type b) Second riser placed mid-period in two parallel-step cell families — REPRODUCED

`campaign.py:281` `periods_for` rounds Ly/Py to the nearest integer; `crystal.py:249-260` puts the
risers at y = 0 and y = Ly/2. Odd period counts (inline check, command 14):
```
si001_100 levels [0, 1]: n_y_periods=37 (Ly=200.9 A), Ly/2 = 18.5 periods, tasks=122  <-- second riser mid-period
si111_110 levels [0, 1]: n_y_periods=15 (Ly=99.8 A),  Ly/2 = 7.5 periods,  tasks=3    <-- second riser mid-period
```
Far-from-riser strip means are unaffected (sinc kernel over whole periods), but the two risers of
these cells have a different atomic structure from those of the even cells, so the 100 / 200 / 400 A
terrace-width series of Si(111) mixes a riser-structure change into the 100 A point, and the
near-riser envelope of si001_100 mixes two riser types. Fix: force an even number of periods.

### F-09 (Minor, missing check) No sampling-convergence test above 30.6 mrad — SECTION_READ

Convergence (`fir_m2_campaign.yaml` stages.convergence.angles_mrad = 13.3, 20.0, 30.6) gates the
dx refinement only up to 32.7 mrad; rocking windows reach 44.5 + 2.1 = 46.6 mrad, where
2q = 3.72 1/A is 89 % of q_band = 4.17 1/A (appendix A8). The 0.05 A Fermi step of rung 1 at 40 mrad
is the only production-sampling check up there and it tests a step profile, not the crystal. The
36-46.6 mrad part of the rocking curves should be labelled "sampling convergence not tested".

### F-10 (Minor) Convergence amplitude tolerance is absolute (3e-3) with |r| >= 1e-2 — SECTION_READ

`configs/benchmarks.yaml` convergence.amp_abs = 3e-3 applied to |r_variant - r_prod|
(`aggregate.py:293`): at |r| = 0.01-0.03, typical off-peak, a 10-30 % pure amplitude change passes
(phase is still held to 5e-3 rad). Worth stating next to the verdict.

### F-11 (Minor, type a) Stated outputs not produced by the aggregator — SECTION_READ

* docs/08 section 5 promises "RHEED rod intensities per window" in the rocking summary;
  `aggregate_rocking` never calls `analysis.rod_intensities` and does not read `pattern`; the
  patterns exist only inside each `.h5`.
* docs/08 section 5: "The 1 mrad scan gives the step phase as a continuous function of angle from 9
  to 32 mrad"; `aggregate_steps` reports each 1 mrad run separately, with `np.angle` wrapped to
  (-pi, pi], and never stitches or unwraps across runs.
* No verdict anywhere uses `stopped_at_cap`, `record_tail_rel` or `record_head_rel`
  (the slow CPU tests assert the latter two < 1e-3; the production gate does not).

### F-12 (Nit) Bragg table uses V0 of an arbitrary result — REPRODUCED (no effect here)

`aggregate.py:316` takes `V0_parametrization_V` from `results[0]` (files sorted by hash). A Lobato
task first would shift the "V0_parametrization" Bragg angles by up to -0.019 mrad. For the planned
ids the first file is `00509b6b360b175d` (Kirkland), so no effect in this campaign.

### F-13 (Nit) Documentation inconsistencies — SECTION_READ

docs/08 section 3.1 gives the adaptive stop as "1e-4 ... cap at 2.5 times" (smoke values); production
is tail_tol 1e-5, cap 4 (section 4 and the YAML). docs/model_assumptions.md C1 cites "docs/08 section
3.6" for the abTEM test; it is section 3.5. docs/08 section 3.7 refers to itself ("rerun ... (section 3.7)").
`fir/setup_env.sh:20` installs an unpinned `abtem` from PyPI after the wheelhouse packages, which can
replace numpy/scipy in the environment (the abTEM check is informational).

### F-15 (Nit) Dependency-match prefix collision; dead code — REPRODUCED / SECTION_READ

* `fir/run_stage.sbatch:65` matches `*"afterok:${SLURM_JOB_ID}"*`, which also matches a dependency on
  any job whose id starts with the current id (bash check: `afterok:123456(unfulfilled)` matches job
  12345). It could move an unrelated job's dependency; with Fir job ids of equal length this needs
  ids differing by a factor of ten, so it is theoretical. Fix: match `afterok:${SLURM_JOB_ID}(`.
* `analysis.py:9-99` (`fourier_coefficients`, `specular_reflectivity`, `rod_intensities`,
  `image_wave_on_plane`) and `simulate.py:185-188` (`extraction_window`, which reads numerics keys
  that no configuration defines) are unused.

