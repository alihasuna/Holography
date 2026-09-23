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
- 22:55 UTC: F1 "after", the exact H4 selections (now 10 tests: two job types were added to the
  parametrization): `BASH_ENV=<profile defining module()> pytest tests/hpc -k ...` ->
  `10 passed, 103 deselected in 10.04s` (the profile's module() never ran: no call recorded);
  `--basetemp` on `tmpfs -o noexec` -> `10 passed, 103 deselected in 9.78s`.
- 22:53-23:00 UTC: setup_alliance.sh run end to end six times in a fresh clone (HEAD 242b566, the
  orchestrator's snapshot containing these files) with stand-ins (stateful `module`, `virtualenv`
  = `python3.11 -m venv`, `avail_wheels`), H4's local wheelhouse (69 PyPI wheels) and H4's stand-in
  cupy wheel whose import raises `ImportError: libcuda.so.1`; PyPI blocked
  (`PIP_INDEX_URL=http://127.0.0.1:9/simple`). Section 2.
- 23:00 UTC: whole `tests/hpc` with BASH_ENV and ENV set to the Lmod-like profile, `--basetemp` on a
  noexec tmpfs and ShellCheck 0.11.0 on PATH (bash 5.2.21): `113 passed in 390.51s (0:06:30)` (no
  skip: ShellCheck ran on the five scripts).
- 23:02 UTC: torus runner `--kind trench --estimate-only --max-cpu-seconds 1` -> `[trench] estimate:
  CPU 1379 s (x1.5), engine arrays 198 MB, RSS after setup 1329 MB; limits CPU 1 s (--max-cpu-seconds
  (caller)), memory 10 GB`, `REFUSED`, exit 2; `case_trench.json` and `summary_trench.json` record
  `cpu_seconds_source: --max-cpu-seconds (caller)`. The 1379 s estimate (machine loaded by my own
  parallel runs) is above the runner's 600 s default: one more data point for F11.

## 1. Findings -> fix -> where -> proof

Paths: A = `scripts/hpc/alliance/`, T = `tests/hpc/test_alliance_kit.py`. Line numbers are those
of the working tree at the end of this work.

| H4 | Decision | What was done | file:line | Test / run that proves it |
|---|---|---|---|---|
| F1 (gate) | FIXED | setup's last gate is a CPU physics check of the installed environment, not tests/hpc: `tests/geometry/test_geom_wavelength.py` (200 keV wavelength, constants), `tests/forward/test_engine_contract.py`, `test_vacuum_propagation.py`, `test_rung1_refraction.py` (tiny multislice runs on numpy), `test_potential_atomic.py` (Kirkland via abTEM), `tests/pipeline/test_pipeline_geometric.py` (geometric smoke), `tests/provenance`; 52 tests, one excluded by name (section 4) | A/setup_alliance.sh:301-312 | T `test_f1_setup_gate_is_a_cpu_physics_subset_not_tests_hpc`; setup run 3 (section 2): `52 passed, 1 deselected in 161.71s` under bash 4.2 with BASH_ENV = Lmod-like profile and TMPDIR on a noexec mount; the subset with an importable real cupy-cuda12x 14.1.0: `52 passed, 1 deselected in 74.49s` |
| F1 (hermetic) | FIXED | `clean_environ` also strips `BASH_ENV` and `ENV` (and still `BASH_FUNC_*`); the fakes are tracked executables `tests/hpc/bin/fake_module`, `fake_sbatch` (mode 755) reached through per-test symlinks, records next to the symlink. The orchestrator's "under outputs/" option was not used: tests/conftest.py forbids tests writing there (log 22:40) | tests/hpc/fake_slurm.py:35-43, 75-82; tests/hpc/bin/ | H4's two reproductions before (`8 failed`; `7 failed, 1 passed`) and after (`10 passed` each); whole tests/hpc with BASH_ENV+ENV+noexec basetemp: `113 passed in 390.51s`; T `test_f1_login_shell_hooks_do_not_reach_the_scripts`, `test_f1_fakes_are_not_executed_from_the_test_temp_dir` |
| F2 | FIXED | README: the login-node dry run is gone; new CPU job `dry-run` (`dry_run_job.py`: the pipeline dry run in a job, peak RSS of the process, manifest; exit 4 of a cupy config explained). kit.py memory hint: says the dry run's "memory per realisation" counts only the engine's arrays of one realisation and is not the job's memory; cites the measured 3.6 GB peak (H4) and "about 192-240 B per atom (H2 §8 and §12 ...; H2 is under review)"; no H2 number is a default; `--mem` stays required for every CPU job. (H2 states the B/atom figure in §8 and §12, not §9.) README_HPC.md: note on the dry run's own memory | A/kit.py:64-86; A/dry_run_job.py; A/job.sbatch:180-185; A/README_ALLIANCE.md §4.7; scripts/hpc/README_HPC.md §2, §5 | T `test_f2_pipeline_memory_hint_is_not_the_engine_estimate`, `test_f2_dry_run_job_is_a_cpu_job_even_for_a_cupy_configuration`, `test_f2_emulated_dry_run_job_reports_peak_rss` (emulated job end to end: status 0, peak RSS recorded, manifest copied) |
| F3 | FIXED | setup resumable: stamps `venv/alliance/steps/{venv,wheelhouse,abtem,repo}.done` holding the step's inputs; a stamp with other inputs is refused (`--recreate`); abTEM downloaded and verified BEFORE the wheelhouse install; the cupy gate and the abTEM failure are resumed with the same command (no `--recreate`); one pip report per attempt (package_sources merges them); a complete environment is left alone (exit 0); a complete environment with only another `--cuda-module` is superseded without reinstall (new env id); `--recreate` unchanged | A/setup_alliance.sh:82-112 (complete, supersede), 115-121 (stamps), 145-249 (steps; abTEM first at 166-181) | setup runs 1-6 (section 2); T `test_f3_setup_is_resumable_by_design` |
| F4 | FIXED | null-study default = all points in one job (`serial`); `--array` (or `--array-throttle N`) is the explicit array mode and prints the wiki's sentence (Job_arrays.wiki:45) | A/kit.py:466-495; A/submit.sh:54; README §4.6 | T `test_f4_null_study_array_is_explicit_and_warned`, updated `test_dry_run_command_every_cluster_and_job` (null-study: no `--array`, mode serial), `test_emulated_null_study_array_task` (now passes `--array`) |
| F5 | FIXED (model named) | Trillium: `--nodes=1 --gpus-per-node=h100:1`. Cache lines: Using_GPUs_with_Slurm.wiki:8 `  --gpus-per-node=<model_specifier>:<number>`; :112-113 `\| [[Trillium#Node_characteristics\|Trillium]] \|\| H100-80gb ` / `\| \|\| h100 `. The Trillium pages themselves write `--gpus-per-node=1` (Trillium_Quickstart.wiki:590, 621): explicit escape hatch `--gpu-instance unpinned` = exactly that request, with a printed warning (H200/B200; Trillium.wiki:63-75) | A/clusters.yaml:380-402; A/kit.py:516-527 | T `test_f5_trillium_gpu_model_and_unpinned`; updated GPU_FLAGS of `test_dry_run_command_every_cluster_and_job` |
| F6 | FIXED | at submission the study file is read once (parsed, hashed, copied): the copy `submissions/<record>.study.yaml` is written by `kit.py copy-study` (O_EXCL, hash re-checked), its SHA-256 goes into the record and the export; every job checks the hash, copies it to `<job dir>/study_used.yaml` and reads only that (also `study-point` of array tasks). Not "into the job directory" at submission: the job directory is created by the job (its id is unknown before sbatch), so the copy sits next to the submission record | A/kit.py:405-426, 715-754; A/submit.sh:144-148; A/job.sbatch:147-155, 201-226 | T `test_f6_study_copy_is_made_hashed_and_checked` (copy equals the source, hash in the export, source edited after submission is irrelevant, a tampered copy -> job exit 2, nothing computed) |
| F7 | FIXED | accepted: HH:MM:SS, D-HH:MM:SS, D-HH:MM, D-HH (the wiki's forms that name the hours, Running_jobs.wiki:47); refused as ambiguous: MM:SS (`01:00`) and bare minutes; minutes/seconds >= 60 refused; the parsed duration is printed (`NOTE: time limit ... = HH:MM:SS (N min)`); Nibi (no stated minimum) warns below 5 min | A/kit.py:120-181, 359-381 | T `test_time_limits` (updated: rorqual `00:03:00` still refused by the 5 min minimum; nibi `01:00` and fir `3` now refused; nibi `00:01:00` accepted with warnings), `test_f7_time_forms`; `test_time_parser` unchanged (the parser still reads every Slurm form) |
| F8 | FIXED | record name `<UTC>_<cluster>_<job>_<pid>_<random>.json`, created with noclobber (O_EXCL); never overwritten; created only after the dry-run exit point, removed again if the submission stops before sbatch | A/submit.sh:99-112, 138-142 | T `test_f8_parallel_submissions_get_their_own_records` (3 parallel submissions: 3 records, mem 2G/3G/5G each in its own); `test_real_submission_matches_dry_run_and_is_recorded` unchanged and passing |
| F9 | FIXED | PASS content (schema `reflholo_gpu_check_pass/2`): cluster, env id, SHA-256 of every *.py under `reflection_holo/forward/multislice/` (includes backend.py), device, tolerances. The gate reads the CONTENT (file name not trusted), lists why each PASS does not qualify, and is re-checked by every GPU job at start against the engine code as it is then (`kit.py gate-check`); every job checks that env.json still has the submitted env id (`kit.py env-check`) | A/kit.py:195-266, 586-608, 756-801; A/gpu_check.py:33-35, 173-181, 235-259; A/job.sbatch:93-95, 123-134 | T `test_f9_pass_content_decides` (other engine hash, other cluster in content, no schema: refused), `test_f9_engine_hash_follows_the_engine_code`, `test_f9_gate_rechecked_when_the_job_starts` (PASS removed after submission: job exit 2 before nvidia-smi), `test_f9_environment_rebuilt_while_queued_is_refused`, `test_f9_f13_gpu_check_pass_record_is_valid_and_requeue_safe` |
| F10 | FIXED | three required caps: `--max-array-mb` (arrays, unchanged meaning), `--max-file-mb` (every other file), `--max-total-mb` (fixed order: non-arrays then arrays); files of any extension are taken (no silent extension filter); every selected file left out is listed with size and reason in `DROPPED_FILES.tsv` inside the tarball and printed; `SKIPPED_ARRAYS.tsv` kept; malformed numbers (`.`, `1.2.3`) refused | A/collect_results.sh:8-26, 38-58, 104-174 | T `test_f10_collect_caps_every_file_and_the_total`; `test_collect_results` (only the two new required options added to its call; every assertion unchanged) |
| F11 | FIXED | runner option `--max-cpu-seconds` (default unchanged: CASE 600 s for local use), recorded (`limits_used`, source) in case/summary JSON and printed; the kit passes `0.8 x walltime / number of kinds` (`--time 01:00:00`, two kinds: 1440 s); README states only the measured estimates (T1 163-213 s, H3 502-865 s, H4 265-763 s), no prediction | scripts/torus/run_torus_multislice.py:201-223; A/kit.py:62, 454-465; A/job.sbatch:186-200; README §4.5 | T `test_f11_torus_cpu_limit_from_walltime`; runner run with `--max-cpu-seconds 1` (log 23:02) |
| F12 | FIXED | submit.sh header: gpu-check duration "never measured"; README: macOS `shasum -a 256 -c`; CUDA mismatch -> the `cuda/<x.y>` matching the "CUDA runtime" printed by setup and gpu-check (12.2, 12.6, 12.9, 13.2, 13.3 listed); Fir "4 x H100" with the page's "2" noted | A/submit.sh:7-8; A/README_ALLIANCE.md §0, §3, §6 | reading (README text); `bash submit.sh x y --help` prints the new header |
| F13 | FIXED | requeued gpu-check writes `PASS_..._<jobid>_requeue<k>.json` (no FileExistsError); setup logs are hard links (always complete; a copy only with a NOTE if linking fails); submit.sh: `git status` without a pipe inside `$(...)`, failure reported | A/gpu_check.py:244-255; A/setup_alliance.sh:327-331; A/submit.sh:88-93 | T `test_f9_f13_gpu_check_pass_record_is_valid_and_requeue_safe`; setup run 3: link count 2 and the log copy ends with the final `Next:` line |
| new | DONE | `gpu-sanity` job (1 GPU, gated like every GPU job): (1) `run_study.py --only tfix_bragg_abs0_L0` on the study copy (backend must be cupy) against the M2 row read at run time (docs/agent_reports/M2_multislice_engine.md:361: err +0.569 rad, amplitude ratio 0.951); (2) `tools/hpc/supercell_sizing.py --measure <new file> --only bu_100_r010 --backend cupy` (the CLI exists as H2 describes) against `runs.bu_100_r010.buildup` of tools/hpc/supercell_sizing_measurements.json (|R| 0.27068212717331086, arg -1.5393572904605988). Tolerances fixed before any GPU run, printed first and recorded: 1e-2 rad and 1e-2 (absolute) for the study point; 1e-2 rad and 1e-2 RELATIVE for the plateau (H2's "1e-2" read in the stricter way). Also checks backend, point name, same cell (nx, ny, slices, atoms, precision) and finite values; writes gpu_sanity.json and a manifest | A/gpu_sanity.py (tolerances :39-52); A/kit.py:496-502; A/job.sbatch:167-171 | T `test_gpu_sanity_references_are_read_from_the_repository`, `test_gpu_sanity_comparisons`, `test_gpu_sanity_job_plan`, `test_emulated_gpu_sanity_refuses_without_gpu`; the driver on numpy here: PASS (log 22:37) |

Kept: the A3/A3b fixes (run_pipeline.slurm untouched); no default account, time or GPU (every
refusal test still passes); bash 4.2 compatibility (section 3); outputs under $SCRATCH, never reused.

## 2. setup_alliance.sh, end to end in a fresh clone (stand-ins; no Lmod, no Alliance wheelhouse)

Clone of HEAD 242b566; stand-ins on PATH: `module` (stateful: purge/load/-t list), `virtualenv`
(`python3.11 -m venv`), `avail_wheels` (exit 0), `python` -> python3.11; `PIP_FIND_LINKS` = H4's 69
PyPI wheels + H4's stand-in `cupy-14.1.0` whose import raises `ImportError: libcuda.so.1`;
`PIP_INDEX_URL=http://127.0.0.1:9/simple` (no PyPI). Each run under `env -i`.

| Run | Command (all: `setup_alliance.sh fir ...`) | Result |
|---|---|---|
| 1 | (no option), PyPI unreachable | `exit 2 after 7 s`: `ERROR: pip download of abtem failed (no PyPI access from this login node?). Copy abtem-1.0.10-py3-none-any.whl to this cluster and rerun the same command with --abtem-wheel PATH (no --recreate needed)`; only `steps/venv.done` exists, no wheelhouse install (H4's run 1 failed here after the complete install) |
| 2 | `--abtem-wheel <verified local wheel>` (no `--recreate`) | `exit 2 after 57 s`: `== venv: already made`, `abtem wheel SHA-256 verified`, wheelhouse, abTEM, repo installed and stamped, `No broken requirements found.`, then `ERROR: 'import cupy' failed on this login node ... rerun the same command with --allow-cupy-import-failure (no reinstall)` |
| 3 | same + `--allow-cupy-import-failure`, GNU bash 4.2.0, `BASH_ENV` = the Lmod-like profile (its module() then served every module call: `LMOD-FUNCTION module ...` recorded), `TMPDIR` on a `tmpfs -o noexec` | `exit 0 after 173 s`: every install step `already installed`, `WARNING: FAILED on the login node (--allow-cupy-import-failure)`, `52 passed, 1 deselected in 161.71s (0:02:41)`, `== DONE: environment fir-20260923T225429Z-11f0f8951dcc ready`; records complete; `git status --porcelain` of the clone empty |
| 4 | same again | `exit 0 after 0 s`: `== environment already complete (venv/alliance/env.json, fir-20260923T225429Z-11f0f8951dcc): nothing to do; --recreate rebuilds it` |
| 5 | same + `--cuda-module cuda/12.9` (bash 4.2) | `exit 0 after 126 s`: `== the complete environment used another CUDA module (...)`: env.json superseded (`env.json.superseded_20260923T225739Z`), no reinstall, `52 passed, 1 deselected in 115.37s`, new id `fir-20260923T225739Z-11f0f8951dcc`, modules.sh loads cuda/12.9 |
| 6 | same + `--cupy-spec cupy==14.0.1` | `exit 2 after 0 s`: `ERROR: the complete environment in venv/ was made with (...); this call asks for (...): rerun with --recreate to rebuild it`; env.json byte-identical afterwards |
| 7 | (no option), after moving `steps/venv.done` and `env.json` aside (a venv of unknown state) | `exit 2 after 0 s`: `ERROR: venv/ exists but was not made by this setup (or its creation was interrupted): rerun with --recreate` (stamp restored afterwards) |

## 3. Checks run (outputs verbatim)

| Check | Result |
|---|---|
| `bash -n` on setup_alliance.sh, submit.sh, job.sbatch, collect_results.sh, run_pipeline.slurm, tests/hpc/bin/fake_module | exit 0 (all) |
| ShellCheck 0.11.0 (H4's scratch copy `h4/sc_venv/bin/shellcheck`) `-s bash` on the same six | exit 0, no message |
| tests/hpc before any change (baseline) | `73 passed, 5 skipped in 120.00s (0:02:00)` |
| H4 F1 reproductions before / after | BASH_ENV: `8 failed, 70 deselected in 0.76s` / `10 passed, 103 deselected in 10.04s`; noexec basetemp: `7 failed, 1 passed, 70 deselected in 0.74s` / `10 passed, 103 deselected in 9.78s` |
| tests/hpc, BASH_ENV and ENV = Lmod-like profile, `--basetemp` on `tmpfs -o noexec`, ShellCheck on PATH, bash 5.2.21 | `113 passed in 390.51s (0:06:30)` |
| tests/hpc, GNU bash 4.2.0 (H4's build) first on PATH, ShellCheck on PATH | `113 passed in 410.02s (0:06:50)` |
| setup's physics gate with an importable real cupy-cuda12x 14.1.0 (no driver) | `52 passed, 1 deselected in 74.49s (0:01:14)` |
| setup end to end, 7 runs (section 2) | as in the table of section 2 |
| gpu-sanity driver on numpy (not a GPU) | `GPU SANITY: PASS`, exit 0 (section 0, 22:37) |
| torus runner `--max-cpu-seconds 1 --estimate-only` | `REFUSED`, exit 2, limit and source recorded |

## 4. For the orchestrator (outside the kit or decisions to review)

1. `tests/forward/test_engine_contract.py::test_cupy_is_lazy_and_not_a_fallback` asserts that cupy is
   not in `sys.modules`. Wherever cupy IMPORTS (the PyPI cupy-cuda12x 14.1.0 does without a driver,
   H4 §2.3; very likely the Alliance venv too), `import abtem` imports it, and the test fails even
   when its file runs alone (`1 failed, 6 passed, 1 deselected`, real cupy linked into a scratch
   path). So the FULL suite on a cluster venv would show this one failure. Not a kit defect and not
   changed by me (outside the kit's scope); the setup gate excludes it by name with the reason in
   the script. Suggested fix for its owner: run that assertion in a fresh subprocess that imports
   only the engine's backend module.
2. The repository guard `tests/conftest.py::repository_outputs_untouched` (audit A2 m8) forbids tests
   writing under `outputs/`, which rules out the "fakes under outputs/" option; the tracked
   `tests/hpc/bin/` fakes (mode 755) must keep their executable bit when committed.
3. F6: the study copy lives next to the submission record, not in the job directory (which the job
   creates after sbatch assigns the id); every job copies it into its own directory after the hash
   check. H2's B/atom figure is in §8 and §12 (the brief said §9); cited as "H2 §8 and §12 ... H2 is
   under review".
4. gpu-sanity reads the H2 plateau criterion "within 1e-2 rad and 1e-2" as 1e-2 RELATIVE on |R|
   (stricter than absolute for |R| = 0.27); the study point uses 1e-2 absolute on the amplitude
   ratio (0.951). Both were written before any GPU run and before the numpy check of the driver.
5. Existing tests changed because the decided behaviour changed (no assertion removed, no tolerance
   touched): `test_dry_run_command_every_cluster_and_job` (Trillium flag `--gpus-per-node=h100:1`;
   null-study default serial; two new jobs in the parametrization; study copy and gate exports
   asserted), `test_time_limits` (rorqual `3` -> `00:03:00`, still refused by the 5 min minimum;
   nibi `01:00` flips from accepted to refused, as F7 decides; two cases added), `test_collect_results`
   (the two new required caps added to the call), `test_emulated_null_study_array_task` (passes
   `--array`), fixture `Kit.gpu_pass` (writes a PASS with the content the gate now reads).

## 5. NOT RUN (and why)

* Anything on an Alliance cluster (no ssh by design): real Lmod and whatever the login shell puts in
  BASH_ENV/ENV, the real wheelhouse, `avail_wheels`, whether Trillium's sbatch accepts
  `--gpus-per-node=h100:1` (general syntax and Trillium's specifier are on the wiki, a Trillium
  example with a model is not; `--gpu-instance unpinned` is the documented way out), real sbatch
  option validation, requeue.
* Any GPU execution: gpu-check, gpu-sanity, demo-gpu, the null study on cupy. The gpu-sanity driver
  ran only on the numpy backend (section 0, 22:37); every GPU time is still the GPU_ASSUMED model.
* setup with `--recreate` in the emulation (code path unchanged from H3: `rm -rf venv`, then the
  full run of section 2); setup with a cupy that imports AND installed from the wheelhouse (the
  emulated wheelhouse had the failing stand-in; the importable real cupy was tested only with the
  physics subset through PYTHONPATH).
* A dry-run job of an H2 production-size configuration (none is in configs/; memory beyond the
  1.44 M-atom demo is not measured); a full torus run with the walltime-derived limit (only the
  estimate-only refusal); `shasum` on macOS (documentation).
