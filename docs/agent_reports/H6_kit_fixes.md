# H6: fixes to the Alliance kit after the H4 audit (F1-F13) and the gpu-sanity job

Agent H6. Date: 2026-09-23. Status: IN PROGRESS (written incrementally; the table in section 1 is
the final word once the status reads COMPLETE).

Scope: `scripts/hpc/alliance/`, `tests/hpc/`, `scripts/hpc/README_HPC.md`,
`scripts/torus/run_torus_multislice.py` (F11 only). `scripts/hpc/run_pipeline.slurm` is not changed
(A3/A3b fixes untouched). Inputs: H4 audit (read in full), H3 report, H1 wiki facts and the raw
wiki cache (`scratchpad/alliance_wiki_cache/`), H2 report §8, §9, §12 (H2 is under review: cited
as "H2, under review", no H2 number is used as a default). No commit, no push, no ssh, no personal
data sent anywhere.

## 0. Log

- 22:10 UTC: read H4 (all), H3, every kit file, run_pipeline.slurm, README_HPC.md, the torus runner,
  run_study.py, study.yaml, H2 §2.4, §8, §9, §12, `tools/hpc/supercell_sizing.py` (the `--measure
  ... --only ... --backend cupy` CLI exists as H2 describes), wiki cache pages (Using_GPUs_with_Slurm,
  Trillium, Trillium_Quickstart, Running_jobs, Job_arrays).
- 22:16 UTC: F1 reproduced on the unmodified kit, both modes (H4 commands 17 and 22):
  `BASH_ENV=<file defining module()> pytest tests/hpc -k "<fir dry-runs> or
  test_setup_refuses_without_module_command or test_emulated_smoke_job_end_to_end"` ->
  `8 failed, 70 deselected in 0.76s`; the same tests with `--basetemp` on a `tmpfs -o noexec` ->
  `7 failed, 1 passed, 70 deselected in 0.74s`.
- 22:20 UTC: a new trap found while choosing the setup gate: with a cupy that IMPORTS on the login
  node (the real PyPI cupy-cuda12x 14.1.0 of H4 §2.3, linked into a scratch path), `import abtem`
  puts cupy in `sys.modules`, and `tests/forward/test_engine_contract.py::
  test_cupy_is_lazy_and_not_a_fallback` fails (also when test_engine_contract.py runs alone:
  `1 failed, 6 passed, 1 deselected`). The setup gate excludes that one test by name (reason in the
  script); the test itself is outside the kit and unchanged (section 4, for the orchestrator).
- 22:25 UTC: baseline of the unmodified kit tests: `venv/bin/python -m pytest -q -p no:cacheprovider
  tests/hpc` -> `73 passed, 5 skipped in 120.00s (0:02:00)` (skips: shellcheck not on PATH).
- 22:30-22:45 UTC: fixes written (kit.py, submit.sh, job.sbatch, setup_alliance.sh,
  collect_results.sh, gpu_check.py, clusters.yaml, README_ALLIANCE.md, README_HPC.md, torus runner;
  new: gpu_sanity.py, dry_run_job.py, tests/hpc/bin/fake_module, tests/hpc/bin/fake_sbatch).
- 22:37 UTC: gpu-sanity driver run on the numpy backend here (a CPU check of the driver and of the
  references, not a GPU run): `gpu_sanity.py --study <study.yaml with backend numpy, threads 4>
  --backend numpy --threads 4` -> `tfix_bragg_abs0_L0: err +0.568589 rad (dev 4.11e-04), amplitude
  ratio 0.951007 (dev 7.26e-06); 11.6 s (GPU_ASSUMED model 0.3 s) -> PASS`, `bu_100_r010: plateau
  |R| 0.270682 (rel dev 0.00e+00), arg -1.539357 rad (dev 0.00e+00); run 140.8 s -> PASS`,
  `GPU SANITY: PASS`, exit 0, 2 min 43 s wall. The tolerances had been written into the script
  before this run and were not changed after it.
- 22:40 UTC: the orchestrator's second suggestion for F1 (fakes under the repository's ignored
  `outputs/`) collides with the repository's own guard `tests/conftest.py`
  (`repository_outputs_untouched`, audit A2 m8: "tests write only to temporary directories"); my
  first version did that and the guard failed the session. Replaced by tracked executables
  `tests/hpc/bin/fake_{module,sbatch}` and per-test SYMLINKS in the temporary directory. Checked on
  a `tmpfs -o noexec` mount first: a symlink there to an executable on another mount runs, also
  through `exec` (run_pipeline.slurm uses `exec sbatch`), with `$0` = the symlink path; a copy of
  the same file on the mount gets `Permission denied`.
- 22:50 UTC: `tests/hpc` after the fixes: `1 failed, 107 passed, 5 skipped in 208.98s` (the
  failure was my new test helper: `TypeError: write_gpu_pass() got multiple values for argument
  'cluster'`; helper fixed, no assertion changed; the 8 gate/F5/F9 tests then `8 passed`).
