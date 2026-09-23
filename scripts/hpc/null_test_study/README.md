# Atomistic a/2 null-test study (HPC)

Purpose: decide whether atomistic step phases from the multislice engine converge to the geometric
translation phase `-(k_out - k_in).R` once the cell is long enough and absorbing, and at which cell
length. Background and the in-container results: `docs/agent_reports/M2_multislice_engine.md`,
section 10 "Atomistic null-test diagnosis". Engine status: UNVALIDATED.

Run from the repository root after `scripts/hpc/setup_env.sh` (with `RH_CUPY=cupy-cuda12x` for GPU):

```
# 1. print grid, slices, memory and expected runtime of every point (no simulation)
venv/bin/python scripts/hpc/null_test_study/run_study.py \
    --config scripts/hpc/null_test_study/study.yaml --out $SCRATCH/null_study --estimate
# 2. run all points (or one: --only NAME); results and manifests in $SCRATCH/null_study/outputs/
venv/bin/python scripts/hpc/null_test_study/run_study.py \
    --config scripts/hpc/null_test_study/study.yaml --out $SCRATCH/null_study
```

In a SLURM job, request one GPU (runtime.backend: cupy) or set `runtime.backend: numpy` and
`runtime.threads` to `--cpus-per-task`. Everything in study.yaml is required; absorption values
other than zero are TEST_ONLY stand-ins for PROJECT_INPUT item 21.

Reading the results (`outputs/null_test_study/<name>.json`):
* translation points: `err_rad` is (phase of the translated crystal minus the original) minus
  `-(k_out - k_in).R`, wrapped; `amp_ratio` should tend to 1. A fixed-beam point converges when
  `|err_rad| <= 1e-2` and `|amp_ratio - 1| <= 1e-2` and stays so for the next longer cell.
* step points: `rows[*].residual` is the a/2 step phase minus the geometric value per aperture and
  window distance `d_A` from the step edge (6 A wide windows on each side).
* The CPU runtimes printed by `--estimate` include a x1.5 factor (the estimator under-read the one
  measured atomistic run by that much); GPU runtimes come from a labelled ASSUMPTION model (no GPU
  was available to measure) and should be checked on the first point.

The cupy backend was never executed in the build container (no GPU): run the first point alone
(`--only tfix_bragg_abs0_L0`) and compare with the in-container value (err +0.569 rad) before the
rest.
