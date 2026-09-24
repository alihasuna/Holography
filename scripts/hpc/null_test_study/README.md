# Atomistic a/2 null-test study (HPC)

Purpose: decide whether atomistic step phases from the multislice engine converge to the geometric
translation phase `-(k_out - k_in).R` once the cell is long enough and absorbing, and at which cell
length. Background and the in-container results: `docs/agent_reports/M2_multislice_engine.md`,
section 10 "Atomistic null-test diagnosis". Engine status: UNVALIDATED (rung 3 has passed only for
the continuum null tests and the atomistic moved-beam translation; the atomistic fixed-beam check
of docs/05 4.4 item 3, which this study tests, has NOT passed).

Run from the repository root after `scripts/hpc/setup_env.sh` (with `RH_CUPY=cupy-cuda12x` for GPU):

```
# 1. print grid, slices, memory and expected runtime of every point (no simulation)
venv/bin/python scripts/hpc/null_test_study/run_study.py \
    --config scripts/hpc/null_test_study/study.yaml --out $SCRATCH/null_study --estimate
# 2. run all points (or one: --only NAME); results and manifests in $SCRATCH/null_study/outputs/
venv/bin/python scripts/hpc/null_test_study/run_study.py \
    --config scripts/hpc/null_test_study/study.yaml --out $SCRATCH/null_study
```

Two study files (every key required; see run_study.py):
* `study.yaml`: the M2-reproduction set (17 points, [110]). Its clean depth of 21 A of crystal above
  the absorber (`clean_depth_A: 21.0`, explicit LEGACY value) is shallower than the 24.5 A (0,0,8)
  extinction depth (P2 report 6.5, H2 3, H5 D.8), and its 8 A sheet beam (`beam_height_A: 8.0,
  beam_edge_A: 2.0, beam_gap_A: 2.0`, the former silent defaults, explicit LEGACY values) lights only
  ~500 A of surface: it tests the engine against M2's numbers, not the convergence of a production
  cell.
* `study_depth100.yaml` (E1 wave 2a): 24 points, clean depth 100 A (65 A is the reviewed minimum
  for the 1e-2 criteria, E7 M3; 100 A is a margin), absorption r = 0.05 and 0.1 only (at r = 0 no
  clean depth converges the absolute reflection), fixed-beam translation at [110] and at exact [100] (16.1347 mrad; a four-beam case there,
  H2 2.2), moved-beam controls at both azimuths, the M2 step points at [110] with r >= 0.05, and the
  surface-position-resolved read-out of H2 2.4 (`surface_resolved`: per z_s bin `err_rad`,
  `amp_ratio`, `status` and `excluded_because`; `converged_beyond_A`, `converged`, `verdict`). Every
  point's sheet beam lights the surface up to the exit plane (`beam_height_A = L_z tan(theta) - gap -
  a/2 - 1 A`, H2 2.6; X2 after audit A6 N-1), bins beyond the lit-end limit or below the amplitude
  floor `amp_floor_rel` are excluded from the verdict with their reason (A6 N-2). Its estimate
  (numpy, 4 threads, this container): `study_depth100_estimate_numpy4.txt`.

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
