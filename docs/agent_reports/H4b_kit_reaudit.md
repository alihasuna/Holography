# H4b: re-audit of the Alliance kit at commit a1ef2a0 (after H6 and H7)

Agent: H4b (code auditor). Date: 2026-09-24. Status: COMPLETE (written incrementally, consolidated
at the end; the verdict in section 9 is the final word).

Summary: all thirteen H4 findings are fixed and none regressed (H4's own failure cases, including
BASH_ENV, a noexec temporary directory and GNU bash 4.2, now pass). gpu-sanity has a-priori
tolerances, reads its references from the repository, propagates PASS/FAIL (0/1/5) and works with
H7's `working_reflections_hkl` (numpy check in the worktree: PASS, strip bitwise). Every job of
tonight's list went through an emulated submission end to end (bash 4.2, Lmod-like `module`
function with sticky modules, fake sbatch executing job.sbatch). No BLOCKER at a1ef2a0. Two MAJOR
findings, both documentation/process: the README clones a moving in-progress branch instead of the
audited commit (N1), and it does not say that the null study is on hold (N2). Three MINOR (N3-N5).

Scope: everything tonight's list touches (setup_alliance.sh, then gpu-check, gpu-sanity, smoke,
demo-gpu, torus on Fir/Nibi/Rorqual; Narval/Trillium as alternatives): `scripts/hpc/alliance/`
(clusters.yaml, kit.py, setup_alliance.sh, submit.sh, job.sbatch, gpu_check.py, gpu_sanity.py,
dry_run_job.py, collect_results.sh, README_ALLIANCE.md), `scripts/hpc/run_pipeline.slurm`,
`scripts/torus/run_torus_multislice.py`, `scripts/hpc/null_test_study/` (only as a dependency of
gpu-sanity), `tools/hpc/supercell_sizing.py` (`--measure`, used by gpu-sanity), `tests/hpc/`, and the
H7 engine API (`MultisliceParams.working_reflections_hkl`, band assertion, `memory_model`). The null
study itself is on hold and was not audited beyond what tonight's jobs use.

Method: a detached worktree of a1ef2a0 at `scratchpad/h4b_wt` (`git worktree add --detach`), audited
and run there only. The main venv's packages were reached through a venv shim inside the worktree
(`venv/`, gitignored: `python -m venv --without-pip` plus two `.pth` lines, one to
`/home/user/Holography/venv/lib/python3.11/site-packages`, one to the worktree; nothing installed);
`reflection_holo.__file__` resolves to the worktree, and `git status --porcelain` of the worktree
stayed empty to the end. The end-to-end emulation ran in a fresh `git clone` checked out at
a1ef2a0 (same commit, own venv built by setup_alliance.sh from H4's local wheelhouse). Stand-ins
reused from H4/H6: GNU bash 4.2.0 (`scratchpad/h4/bash42bin`), ShellCheck 0.11.0
(`scratchpad/h4/sc_venv`), the Lmod-like BASH_ENV profile, H4's 69-wheel wheelhouse and stand-in cupy
wheel, the SHA-verified abTEM 1.0.10 wheel. Nothing under audit was modified; no commit, no push, no
ssh, no personal data sent anywhere. Machine: 4 CPUs, 15 GB, bash 5.2.21, no GPU/Lmod/Slurm, shared
with other agents' runs (load 7-18 throughout; every duration below is inflated by that).

Severity: BLOCKER = breaks tonight's list on a cluster or gives a wrong verdict; MAJOR = likely
failure or misleading result in a plausible path of tonight, or a guard that does not guard;
MINOR = correctness/documentation issue with a workaround.

Kit and engine at a1ef2a0 are byte-identical to H6's commit 2c0d122 (`git diff --stat 2c0d122
a1ef2a0 -- scripts/hpc tests/hpc tools/hpc reflection_holo scripts/torus configs tests/forward`:
empty; the commits after 2c0d122 touch only docs/agent_reports, tools/review, tools/validation,
tools/physics_checks). `scripts/hpc/run_pipeline.slurm` is unchanged since the H4-audited commit
69d2de0 (A3/A3b fixes intact).

## Command log

Every command run for this audit, in order (S = scratchpad, W = S/h4b_wt, PY = W/venv/bin/python
with PYTHONPATH=W; E = S/h4b/e2e, the emulated login node; "emulated" = unmodified submit.sh ->
fake sbatch that EXECUTES job.sbatch; bash 4.2 for submit and job; `module` only as a BASH_ENV
function; numpy-impersonating cupy on the login shell's PYTHONPATH; fake nvidia-smi/scontrol).

| # | Command (abridged) | Result |
|---|---|---|
| 1 | `git -C /home/user/Holography worktree add --detach W a1ef2a0` | `HEAD is now at a1ef2a0` |
| 2 | `git diff --stat 2c0d122 a1ef2a0 -- <kit, engine, tools/hpc, tests>`; `git log 2c0d122..a1ef2a0 --stat`; `git diff --stat 69d2de0 a1ef2a0 -- scripts/hpc/alliance scripts/hpc/run_pipeline.slurm ...` | empty diff for every audited path after 2c0d122; run_pipeline.slurm untouched since 69d2de0 |
| 3 | venv shim (above); `PYTHONPATH=W PY -c "import reflection_holo, numpy, abtem, pytest; ..."` | resolves to the worktree; numpy 2.4.6, abtem 1.0.10, pytest 9.1.1 |
| 4 | `bash -n` (5.2.21 and GNU 4.2.0) and ShellCheck 0.11.0 `-s bash` on setup_alliance.sh, submit.sh, job.sbatch, collect_results.sh, run_pipeline.slurm, tests/hpc/bin/fake_module (W); `-o all` on the kit scripts | exit 0 on all six, both bash versions, ShellCheck silent; `-o all` adds only optional notes (SC2250/2292 style; SC2310/2312: functions in conditions call `die`, which still exits) |
| 5 | e2e stand-ins in E: Lmod-like `module` FUNCTION from BASH_ENV/ENV, stateful through an exported variable, sticky CCconfig/gentoo/StdEnv that `module purge` keeps (Utiliser_des_modules__en.wiki:63), unknown modules fail; fake nvidia-smi, scontrol; `sbatch` = symlink to W/tests/hpc/bin/fake_sbatch; numpy-impersonating cupy (+cupyx.scipy.ndimage) with threaded scipy.fft; fresh `git clone` of the main repository, `git checkout --detach a1ef2a0` (`git status --porcelain` empty); TMPDIR on `mount -t tmpfs -o noexec` (`findmnt`: `rw,noexec,relatime`) | stand-ins ready |
| 6 | setup run 1: `env -i HOME=E/home PATH=<virtualenv, avail_wheels, python 3.11 stand-ins>:/usr/bin:/bin BASH_ENV=<profile> TMPDIR=<noexec> PIP_INDEX_URL=http://127.0.0.1:9/simple <bash 4.2> scripts/hpc/alliance/setup_alliance.sh fir` | `exit 2 after 6 s`: `ERROR: pip download of abtem failed (no PyPI access from this login node?). Copy abtem-1.0.10-py3-none-any.whl to this cluster and rerun the same command with --abtem-wheel PATH (no --recreate needed)`; only `steps/venv.done` exists |
| 7 | setup run 2: same + `--abtem-wheel <verified wheel>` | `exit 2 after 52 s`: `== venv: already made`, `abtem wheel SHA-256 verified: 34e09866...515d`, wheelhouse/abtem/repo stamped, `No broken requirements found.`, `multislice engine: (True, 'available')`, then `ERROR: 'import cupy' failed on this login node ... rerun the same command with --allow-cupy-import-failure (no reinstall)`; all 14 `module` calls went to the BASH_ENV function |
| 8 | `cd W; PATH=<shellcheck>:$PATH PY -m pytest -q -p no:cacheprovider -rs tests/hpc` (bash 5.2.21) | `114 passed in 350.55s (0:05:50)` (no skip: ShellCheck ran) |
| 9 | setup run 3: run 2 + `--allow-cupy-import-failure` (bash 4.2, BASH_ENV function, noexec TMPDIR) | `exit 0 after 138 s`: every step `already installed`, `WARNING: FAILED on the login node (--allow-cupy-import-failure)`, `52 passed, 1 deselected in 129.11s`, `== DONE: environment fir-20260924T001840Z-d33682f3da69 ready in .../venv (records in venv/alliance).`; module_list.txt = the 8 modules of the Lmod-like state (sticky ones included); setup logs hard-linked (link count 2); clone clean |
| 10 | README §4.1 as written, emulated, `--dry-run`: `bash submit.sh fir gpu-check --account def-XXX --time 00:15:00 --dry-run` | exit 0; `NOTE: time limit 00:15:00 = 00:15:00 (15 min)`; `sbatch --account=def-XXX --time=00:15:00 --gpus=h100:1 --cpus-per-task=12 --mem=280G --job-name=reflholo-gpu-check --output=<scratch>/reflholo/logs/gpu-check_%j.log --chdir=<scratch>/reflholo --export=ALL,...`; `DRY RUN: nothing submitted` |
| 11 | H4 command 17 on the fixed kit (W): control `BASH_ENV=<H4 profile> bash -c 'type -t module'` -> `function`; then `BASH_ENV=<profile> ENV=<profile> pytest tests/hpc -k "(test_dry_run_command_every_cluster_and_job and fir) or test_setup_refuses_without_module_command or test_emulated_smoke_job_end_to_end"` | `10 passed, 104 deselected in 16.11s`; the profile's module() was called 0 times (H4: `8 failed`) |
| 12 | H4 command 22: same selection with `--basetemp` on a `tmpfs -o noexec` (control: a copied `/bin/true` there -> `Permission denied`, exit 126) | `10 passed, 104 deselected in 17.09s` (H4: `7 failed, 1 passed`) |
| 13 | README §4.1 emulated: `bash submit.sh fir gpu-check --account def-XXX --time 00:15:00` | submit exit 0 after 215 s; job 900001 status 0; log: `modules: identical to the setup record (8 modules)`, `environment: fir-20260924T001840Z-d33682f3da69 (as submitted)`, `threads: 12 (declared by the run) of 12 allocated cpus`, `commit: a1ef2a0a...`, FFT c128 `3.83e-16` PASS, c64 `1.60e-07` PASS; rung-1 case c128 `0.00e+00`, c64 `1.78e-05`; atomistic case c128 `0.00e+00`, c64 `9.22e-05` (all PASS); `GPU CHECK: PASS (record .../gpu_check/PASS_fir_fir-20260924T001840Z-d33682f3da69_900001.json; valid for cluster fir, environment ... and engine code bba984420543)`. Job dir: job_status.txt `exit_status 0`, slurm.log, submission.json, module_list.txt, nvidia-smi.txt, scontrol_show_job.txt, job_info.json, gpu_check/gpu_check.json, manifests/gpu_check__outputs__manifests__gpu_check_*.json. PASS content: schema `reflholo_gpu_check_pass/2`, cluster fir, env id, engine sha256 `bba98442...`, commit a1ef2a0 |
| 14 | PASS gate vs engine code: (a) append a comment line to the clone's `reflection_holo/forward/multislice/propagator.py`, `submit.sh fir gpu-sanity ... --dry-run`; (b) restore, submit gpu-sanity in fake-sbatch RECORD mode (PASS valid), change the engine again, start the recorded job (fake sbatch EXECUTE mode, recorded argv); restore | (a) exit 2: `REFUSED: no gpu-check PASS record for cluster fir, environment ... and engine code 52f139b181bc ...; PASS files that do not qualify: PASS_fir_..._900001.json: engine code bba984420543 != current 52f139b181bc`; (b) job 900201 status 2 at start, same text + `ERROR: no valid gpu-check PASS at job start`; job dir holds only records (no nvidia-smi.txt, no gpu_sanity/): nothing computed. Clone clean after each restore |
| 15 | `cd W; PY -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml` (OMP 4) under `getrusage(RUSAGE_CHILDREN)` | `EXIT 4 wall 86.6 s peak RSS 3628 MB`; geometry and the H7 band assertion pass (`reflection_setup` runs in the dry run, pipeline/estimates.py:138), then `multislice backend cupy NOT available` (expected without cupy). Prints `memory per realisation ~230.3 MiB (numpy backend, host); cupy backend: device ~70.2 MiB (lower bound: library workspaces not included), host ~204.9 MiB`, `GPU (ASSUMPTION model, not measured) ~9 s` |
| 16 | gpu-sanity driver on numpy in W (a CPU check of the driver and the stored references, not a GPU run): study copy with `backend: numpy`, `threads: 4`; `PY W/scripts/hpc/alliance/gpu_sanity.py --out ... --study <copy> --backend numpy --threads 4` (OMP 4; load 12-15) | exit 0 after 11 min 1 s: `tfix_bragg_abs0_L0: err +0.568589 rad (dev 4.11e-04), amplitude ratio 0.951007 (dev 7.26e-06); 69.0 s (GPU_ASSUMED model 0.3 s) -> PASS`; `[measure] bu_100_r010: atoms 382840, grid 2500x84, 4514 slices, run 571 s`; `bu_100_r010: plateau |R| 0.270682 (rel dev 0.00e+00), arg -1.539357 rad (dev 0.00e+00) -> PASS`; `GPU SANITY: PASS`. References printed before any sub-run: `docs/agent_reports/M2_multislice_engine.md:361` (+0.569, 0.951) and `tools/hpc/supercell_sizing_measurements.json runs.bu_100_r010.buildup` (0.270682, -1.539357); tolerances printed first |
| 17 | gpu_sanity.main() with its two sub-run paths pointed at stubs (module attributes RUN_STUDY/SIZING replaced in a driver process; kit files untouched) returning the stored values, perturbed values, NaN, a failing exit or no file; `--backend cupy`, repository study.yaml | exact `rc=0 PASS`; study err +0.011, amp -0.011, NaN: `rc=1 FAIL (a comparison exceeded its tolerance)`; strip arg +0.011, amp x1.011: `rc=1`; strip arg +2 pi: `rc=0` (wrapped); study sub-run exit 1, strip without file: `rc=5 FAIL (a sub-run failed or wrote no result)`; gpu_sanity.json `passed` agrees every time |
| 18 | tolerance history: `git show <c>:scripts/hpc/alliance/gpu_sanity.py` / `gpu_check.py` for every commit touching them | gpu_sanity TOL_* = 1e-2 (x4) since its first commit 242b566; gpu_check TOL_* unchanged since 69d2de0 (1e-10, 1e-4, 1e-9, 1e-3) |
| 19 | tests/hpc variant A (W): BASH_ENV = ENV = Lmod-like profile, `--basetemp` on the noexec tmpfs, ShellCheck on PATH, bash 5.2.21 | `114 passed in 420.31s (0:07:00)`; profile module() calls: 0 |
| 20 | README §4.2 emulated: `bash submit.sh fir gpu-sanity --account def-XXX --time 00:30:00` | submit exit 0 after 613 s, job 900301 status 0. Log: `modules: identical ... (8 modules)`, `environment: ... (as submitted)`, `threads: 8 (declared by the run) of 12 allocated cpus`, `gpu-check gate: PASS_fir_..._900001.json matches cluster fir, environment ... and engine code bba984420543`, `study: .../submissions/20260924T002545Z_fir_gpu-sanity_7494_21945.study.yaml SHA-256 ebd82446... as submitted; job copy ...`, tolerances and references first, `tfix_bragg_abs0_L0: err +0.568589 rad (dev 4.11e-04), amplitude ratio 0.951007 (dev 7.26e-06) -> PASS`, `bu_100_r010: ... (rel dev 0.00e+00) ... (dev 0.00e+00); run 532.0 s -> PASS`, `GPU SANITY: PASS`. Job dir: study_used.yaml (byte-identical to the repository study.yaml), gpu_sanity/{gpu_sanity.json, buildup_measure.json, study/, *.log}, manifests/ (gpu_sanity and the study point), slurm.log, submission.json, job_status.txt `exit_status 0`. (cupy = numpy + scipy.fft here: plumbing, not the GPU) |
| 21 | README §4.3 emulated: `bash submit.sh fir smoke --account def-XXX --time 00:15:00 --mem 2G` | submit exit 0 after 7 s, job 900401 status 0; log: `threads: 4 (declared by the run) of 4 allocated cpus`, `heights: 3 of 3 step heights returned`, `h = +2.7156 +- 0.0165 A`, `h = -1.3576 +- 0.0082 A`, `h = -1.3580 +- 0.0082 A`, `no-step control: PASS`, `finished with status 0` (README §4.3's lines exactly); job dir: pipeline/{summary.json, manifest.json, arrays.npz, quicklooks, dry-run text}, manifests/, slurm.log, submission.json, job_status.txt `exit_status 0` |
| 22 | README §4.5 emulated: `bash submit.sh fir torus --account def-XXX --time 01:00:00 --mem 4G` (load 9-15) | submit exit 0 after 1470 s, job 900501 status 0; log: `threads: 4 ... of 4 allocated cpus`, `== torus trench (CPU guard 1440 s, derived from --time 01:00:00 by submit.sh)`, `[trench] atoms 547662, grid 945 x 1134 (dx 0.1258, dy 0.1293 A), 1124 slices`, `[trench] estimate: CPU 1109 s (x1.5), engine arrays 238 MB, RSS after setup 1331 MB; limits CPU 1440 s (--max-cpu-seconds (caller)), memory 10 GB`, `[trench] simulate 791.7 s, total 823.6 s, peak RSS 1331 MB`; ridge estimate 878 s, simulate 621.0 s, peak RSS 1348 MB; both `finished with status 0`; case/summary JSON record `cpu_seconds 1440.0`, source `--max-cpu-seconds (caller)`; both manifests copied. The trench estimate (1109 s) would have been refused by the runner's old 600 s guard |
| 23 | tests/hpc variant B (W): GNU bash 4.2.0 first on PATH, ShellCheck on PATH | `114 passed in 447.68s (0:07:27)` |
| 24 | `git log a1ef2a0..origin/claude/electron-holography-orchestration-nakd7r`; `git diff --stat a1ef2a0 3e99722 -- scripts reflection_holo tests tools/hpc configs docs/agent_reports/M2_multislice_engine.md` (local tracking ref, not fetched) | the branch the README clones moved 5 commits past a1ef2a0 during this audit (tip 3e99722 `Snapshot in-progress agent work: not final`, 00:23 UTC) and already changes the engine the gate hashes: `reflection_holo/forward/multislice/{__init__,engine,potentials}.py` (potentials.py +194 lines: a new `ContinuumPeriodicPotential`, band harmonics in `reflection_setup`, new VALIDATION_STATUS) and `tests/forward/ladder_cases.py` (+115 lines; gpu_check.py takes its rung-1 case from it) |
| 25 | Trillium alternative, emulated (env record copied from the fir setup with cluster/env id changed, `RH_ALLIANCE_ENV_DIR`): README §4.1-§4.5 commands with `trillium --dry-run`, and `gpu-check --time 00:10:00` | gpu-check exit 0: `sbatch --account=def-XXX --time=00:15:00 --nodes=1 --gpus-per-node=h100:1 ...` (no --mem, no -c), `WARNING: this host is 'vm'; Trillium GPU jobs must be submitted from the GPU login node (trig-login01, ...)`; gpu-sanity and demo-gpu exit 2 (the fir PASS in the same run root listed as not qualifying: cluster, environment); smoke and torus exit 2 (`REFUSED: smoke is a CPU job; the kit does not run CPU jobs on trillium ...`); `--time 00:10:00` exit 2 (15 min minimum) |
| 26 | `PY -m reflection_holo.pipeline dry-run` (W) of configs/demo_smoke_si001.yaml, its variant multislice_tiny, demo_smoke_torus_ridge.yaml, demo_smoke_torus_trench.yaml | exit 0 each (geometric; multislice_tiny: `engine multislice`, band assertion with the declared (0,0,8) passes) |
| 27 | README §6 emulated: `collect_results.sh --max-array-mb 50 --max-file-mb 20 --max-total-mb 500 --jobs 900001,900301,900401,900501`; unpack; `sha256sum -c MANIFEST.sha256`; `sha256sum -c <tarball>.sha256` | exit 0: `packed 73 of 73 selected files (63827146 bytes before compression) ... (38406103 bytes)`, `dropped files: 0`; all MANIFEST entries OK, tarball checksum OK; the gpu-check PASS record, the 4 submission records with `.sbatch_output` and the gpu-sanity study copy included |
| 28 | H4 command 21a again (emulated nibi record): `submit.sh nibi smoke --account def-XXX --time 01:00 --mem 2G --dry-run` | exit 2: `REFUSED: --time '01:00' is ambiguous and refused: Slurm reads it as minutes:seconds (= 1 min, i.e. 00:01:00) ... 01:00:00 for one hour` (H4: accepted as one minute) |
| 29 | H4 command 21b again: two `submit.sh rorqual smoke` started together (`--mem 2G`, `--mem 3G`, fake sbatch record mode, bash 4.2) | two records `20260924T010246Z_rorqual_smoke_24188_31326.json` (mem 2G) and `..._24189_25293.json` (mem 3G), each with its `.sbatch_output`; jobs 900801, 900901 (H4: one record for two jobs) |
| 30 | H4 command 20 again: synthetic run root (30 MB summary.json, 20 MB log, 5 MB arrays.npz, a `.bin`); `collect_results.sh --run-root R --max-array-mb 0` (H4's call), then with `--max-file-mb 20 --max-total-mb 100` (bash 4.2) | H4's call now refused: `ERROR: --max-file-mb is required (no default)`; with the caps: `packed 3 of 5 selected files`, the 30 MB json and the npz dropped and listed in DROPPED_FILES.tsv with their reasons, the `.bin` packed (H4: 30 MB json packed, `.bin` dropped silently) |
| 31 | Trillium alternative, emulated gpu-check job (own scratch; the fake sbatch passes no `--cpus-per-task`, so only `SLURM_CPUS_ON_NODE=24` is set: job.sbatch:101-104) | submit exit 0 after 192 s, job 900701 status 0: `threads: 24 (declared by the run) of 24 allocated cpus`, `GPU CHECK: PASS (record .../PASS_trillium_trillium-..._900701.json; valid for cluster trillium, ...)`; no tests/hpc test covers this branch |
| 32 | JSON search of job 900001's job_info.json and copied manifest for `PYTHONPATH` and the stand-in cupy path; `E/home/Holography/venv/bin/python -c "import cupy"` (no PYTHONPATH) | job_info.json: 23 fixed keys, no PYTHONPATH; manifest: neither; gpu_check.json `cupy_version "0.0+numpy-impersonation(h4b)"`; the venv's own cupy fails (`Failed to import CuPy (H4 stand-in)`): the jobs used the login shell's PYTHONPATH copy (N5) |
| 33 | time-limit SIGTERM (not tested by H4/H6): emulated `submit.sh fir torus --account def-XXX --time 01:00:00 --mem 4G --kinds trench` in its own scratch; after 45 s SIGTERM to job.sbatch's bash (my first `kill` also hit the fake sbatch process, an emulation artifact: submit.sh then printed `sbatch failed (status 143)`, which a real sbatch that has already returned cannot do), then SIGTERM to the torus payload, as Slurm signals every process of the job | job.sbatch waited for its payload, then its TERM and EXIT traps ran: log `== torus trench (CPU guard 2880 s, derived from --time 01:00:00 by submit.sh)`, `Terminated`, `job 901001 finished with status 143; outputs in ...`; job dir: job_status.txt `exit_status 143`, slurm.log, submission.json, module_list.txt, job_info.json; the loop over kinds stopped. A time-limit kill is recorded as 143, not as success |
| 34 | README §4.4 emulated: `bash submit.sh fir demo-gpu --account def-XXX --time 01:00:00` (load 12-18; cupy = numpy + scipy.fft, 8 workers) | submit exit 0 after 2051 s, job 900601 status 0; log: `modules: identical to the setup record (8 modules)`, `threads: 8 (declared by the run) of 12 allocated cpus`, `gpu-check gate: PASS_fir_..._900001.json matches cluster fir, environment ... and engine code bba984420543`, `cupy 0.0+numpy-impersonation(h4b) 1 device(s)`, run_pipeline.slurm's own cupy pre-flight, list-inputs, `run-level gate: PASS`, the dry run with `memory per realisation ~230.3 MiB (numpy backend, host); cupy backend: device ~70.2 MiB ...` and `GPU (ASSUMPTION model, not measured) ~9 s`, then, as README §4.4 expects: `NO HEIGHT: no-step control failed or not performed (failed: delta = +0.4367 rad, tolerance 0.2878 rad = 3 correlated standard errors); every height of this run is withheld`, `finished with status 0`. Job dir: pipeline/{summary.json, manifest.json, arrays.npz, quicklooks, outputs/}, manifests/ (pipeline and engine manifests: engine backend `cupy`, commit a1ef2a0, dirty false, threads consistent 8), nvidia-smi.txt, slurm.log, submission.json, job_status.txt `exit_status 0`. Both manifests record `"cupy": "14.1.0"`, the version of the INSTALLED stand-in distribution, although the module that ran was the PYTHONPATH one (N5) |
| 35 | cleanup: `umount` of both noexec tmpfs mounts; `git -C W status --porcelain` (empty); `git -C /home/user/Holography worktree remove W`; `git worktree list` | worktree removed without --force (only the main tree listed); nothing under audit was modified at any point |

## 1. The H4 findings F1-F13 after H6 (item 1)

Line numbers are those of a1ef2a0 (A = `scripts/hpc/alliance/`).

| H4 | Claimed fix (H6) | Checked how | Verdict |
|---|---|---|---|
| F1 BASH_ENV / noexec make setup fail | setup gate = CPU physics subset (A/setup_alliance.sh:301-312); tests/hpc hermetic (tests/hpc/fake_slurm.py:75-83 strips BASH_ENV, ENV, BASH_FUNC_*; fakes are tracked executables reached through symlinks, :35-43) | H4's two reproductions now 10 passed each, with controls proving both triggers live (rows 11, 12; H4: 8 and 7 failures); whole tests/hpc under BASH_ENV+ENV+noexec: 114 passed, the profile never ran (row 19); under bash 4.2: 114 passed (row 23); setup itself under bash 4.2 with `module` served ONLY by the BASH_ENV function and TMPDIR on noexec: `52 passed, 1 deselected`, exit 0 (row 9) | FIXED, no regression |
| F2 login-node dry run; memory hint | README §4.7 sends the dry run to a CPU `dry-run` job (A/dry_run_job.py, A/job.sbatch:180-185); hint A/kit.py:71-84 | README has no login-node dry-run line (test_f2 asserts it); the dry-run job's emulated test passes (row 8); the numbers the wording quotes are stale after H7 | FIXED; wording superseded by H7 (N4) |
| F3 late failures need --recreate | stamps, abTEM first (A/setup_alliance.sh:114-249) | rows 6, 7, 9: PyPI failure after 6 s with only `venv.done`; the cupy gate resumed without reinstall | FIXED |
| F4 null study array default | serial default (A/kit.py:493-494) | test_f4 (row 8); code read | FIXED (the null study is on hold anyway: N2) |
| F5 Trillium GPU model | `--nodes=1 --gpus-per-node=h100:1` (A/clusters.yaml:389-391), `--gpu-instance unpinned` escape (:395-402) | row 25; wiki cache Using_GPUs_with_Slurm.wiki:7-8 (`--gpus-per-node=<model_specifier>:<number>`) and the Trillium row `h100` of its Available GPUs table | FIXED as far as the wiki goes; Trillium's acceptance of `h100:1` NOT RUN (README §4 and §7 give the fallback) |
| F6 array tasks re-read study.yaml | study copy at submission, hash-checked by every job (A/kit.py:405-426, 715-753; A/job.sbatch:147-155) | row 20 (copy under submissions/, SHA-256 checked, `study_used.yaml`); test_f6 (tampered copy -> exit 2) passes | FIXED |
| F7 `--time 01:00` = 1 min | MM:SS and bare minutes refused, parsed duration printed (A/kit.py:141-181, 362-363) | rows 10, 28; test_time_limits, test_f7 | FIXED |
| F8 parallel submissions share a record | record name with PID and $RANDOM, noclobber (A/submit.sh:99-112, 138-142) | row 29 (H4's reproduction: two records); test_f8 | FIXED |
| F9 gate only at submission, not tied to code | PASS content read (cluster, env id, engine SHA-256; A/kit.py:195-266), re-checked at job start (A/job.sbatch:123-134), env id re-checked (:94-95) | row 14 (engine change refused at submission and at job start, nothing computed), row 25 (fir PASS not valid for trillium), row 20 (gate line in the job log); test_f9_* | FIXED |
| F10 collect caps | three required caps, every dropped file listed (A/collect_results.sh) | row 30 (H4's reproduction), row 27 (real run root); test_f10 | FIXED |
| F11 torus 600 s guard | `--max-cpu-seconds` derived from the walltime (A/kit.py:454-465; A/job.sbatch:186-200; runner :201-223) | row 22 (1440 s guard recorded; a 1109 s estimate ran), row 33 (one kind: 2880 s) | FIXED |
| F12 documentation | submit.sh:7-8, README §0, §3, §6 | read: gpu-check duration "never measured"; macOS `shasum -a 256 -c`; CUDA 12.2-13.3 with "match the CUDA runtime printed"; Fir "4 ... the same page's GPU-node layout says 2" | FIXED |
| F13 requeue PASS, setup.log copy, git status pipe | `_requeue<k>` names (A/gpu_check.py:244-255); hard links (A/setup_alliance.sh:326-331); `GITST="$(git ... status --porcelain 2>&1)" || die` (A/submit.sh:89) | row 9 (link count 2); test_f9_f13 | FIXED |

## 2. The gpu-sanity job (item 2)

* Tolerances fixed a priori: module constants A/gpu_sanity.py:47-53 (1e-2 rad and 1e-2 absolute on
  the study point; 1e-2 rad and 1e-2 RELATIVE on the strip plateau), unchanged since the file's
  first commit 242b566 (row 18), printed before any sub-run (rows 16, 20), recorded in
  gpu_sanity.json; no command-line option can change them. OK.
* References read from the repository at run time, never from the job's arguments: the M2 report
  row "beam fixed (as in any step geometry)" (A/gpu_sanity.py:70-85: exactly one such row with four
  cells, else RuntimeError) and `runs.bu_100_r010.buildup` of
  `tools/hpc/supercell_sizing_measurements.json` (:88-98), each printed with its source and its
  file SHA-256 recorded. OK.
* PASS/FAIL propagated: exit 0 PASS, 1 a comparison failed, 5 a sub-run failed or wrote no result
  (row 17: every branch, NaN fails, phases wrapped); job.sbatch:167-171 makes that the job status and
  the EXIT trap writes it to job_status.txt (row 20: `exit_status 0`; the refusal path, row 14:
  status 2; a killed job, row 33: 143). OK.
* Works with H7's engine API: the study point goes through tests/forward/null_test_cases.py:74
  (`working_reflections_hkl=((0, 0, 8),)`), the strip through tools/hpc/supercell_sizing.py:244
  (`WORKING_REFLECTIONS`). On numpy in the worktree both stored references are reproduced (study
  point dev 4.11e-4 rad and 7.26e-6; strip bitwise: row 16); the full emulated job passes (row 20).
  H6's precondition (§4 item 0: the sizing tool must pass `working_reflections_hkl`) holds at
  a1ef2a0.
* What gpu-sanity depends on that the gpu-check engine hash does not cover: step 1 is built from the
  null-study code (`scripts/hpc/null_test_study/study.yaml` point 0, `run_study.py`,
  `tests/forward/null_test_cases.py`) and compared with the M2 report row; gpu-check's cases come
  from `tests/forward/ladder_cases.py` and `null_test_cases.py`. The null study is being redesigned:
  any edit of these files (or of the strip builder) changes what gpu-sanity computes while the
  stored references stay, and gpu-sanity would then FAIL for a reason unrelated to the GPU. At
  a1ef2a0 they agree (rows 16, 20); this is one reason the commit must be pinned (N1). Using point 0
  as a backend-consistency check does not depend on the null study's physics (which is what is on
  hold).
* A gpu-sanity FAIL gates nothing and the README gives no instruction for it (N3).
* The kit only ever passes `--backend cupy`; `--backend numpy` exists for the manual CPU check of the
  driver (row 16). OK.
* Runtime: the strip took 532-571 s on 4 loaded CPUs (rows 16, 20); it has never run on a GPU, so
  `--time 00:30:00` is plausible (3 s structure build, 4514 slices of 2500 x 84) but unmeasured.

## 3. Emulated submissions of tonight's list (item 3)

Every job went through the unmodified submit.sh -> fake sbatch -> job.sbatch chain on a
setup-built fresh clone of a1ef2a0, with README_ALLIANCE.md's command lines (`def-XXX`).

| Job (README) | Rows | Module reload in the job | Outputs under $SCRATCH/reflholo | Manifests / log / record copied | Gate | Status |
|---|---|---|---|---|---|---|
| setup (§3) | 6, 7, 9 | purge + 3 loads, list recorded (8 modules incl. sticky) | n/a | setup logs hard-linked | n/a | 2, 2, 0 as documented |
| gpu-check (§4.1) | 10, 13 | `modules: identical to the setup record (8 modules)`; the Lmod-like function recorded 11 purges over the session | runs/gpu-check_900001_<UTC>/ | manifest, slurm.log, submission.json, job_status.txt | writes the PASS (cluster, env id, engine SHA-256, commit) | 0 |
| gpu-sanity (§4.2) | 20 | identical | runs/gpu-sanity_900301_<UTC>/ (+ study_used.yaml) | 2 manifests, log, record | PASS matched at submission and at job start | 0 |
| smoke (§4.3) | 21 | identical | runs/smoke_900401_<UTC>/pipeline | pipeline manifest, log, record | none (CPU) | 0 |
| demo-gpu (§4.4) | 34 | identical | runs/demo-gpu_900601_<UTC>/pipeline | pipeline and engine manifests, log, record | PASS matched at submission and at job start | 0 (`NO HEIGHT`, as documented) |
| torus (§4.5) | 22 | identical | runs/torus_900501_<UTC>/torus_{trench,ridge} | 2 manifests, log, record | none (CPU) | 0 |
| gpu-check on Trillium (alternative) | 25, 31 | identical | own scratch | as gpu-check | PASS for trillium only | 0 |
| negative cases | 14, 25, 33 | - | - | records written | engine change refused at submission and at job start; fir PASS refused for trillium | 2, 2, 143 |

## 4. H7's engine API change against every kit path (item 4)

| Kit path | How it meets `working_reflections_hkl` / the band assertion / memory_model | Evidence | Verdict |
|---|---|---|---|
| gpu_check.py tiny cases | rung-1 continuum case `()` (tests/forward/ladder_cases.py:61), atomistic step `((0, 0, 8),)` (tests/forward/null_test_cases.py:74) | row 13 (both cases, both precisions); test_gpu_check_pass_record_with_fake_cupy (row 8) | OK |
| gpu_sanity.py | as section 2 | rows 16, 20 | OK |
| smoke (geometric) | not concerned | row 21 | OK |
| demo-gpu (demo_hpc_si001) | pipeline adapter passes the configuration's `target_reflection_hkl` (reflection_holo/pipeline/engines.py:328-331); the dry run runs `reflection_setup` (pipeline/estimates.py:138) | row 15 (band assertion passes; exit 4 only for the missing cupy); row 34 | OK |
| torus runner | `working_reflections_hkl=(c["working_reflection_hkl"],)` (scripts/torus/run_torus_multislice.py:155), dx 0.1258 A | row 22 (both kinds run) | OK |
| dry-run job, other demo configs | pipeline dry run | test_f2_emulated_dry_run_job_reports_peak_rss (row 8); row 26 | OK |
| setup's physics gate | includes the H7-edited test_engine_contract.py and test_vacuum_propagation.py | row 9 (`52 passed, 1 deselected`) | OK |
| memory_model / device_peak_cupy | printed by the dry run and by run_study.py; the kit still takes `--need-gpu-mem-gb` from the user | rows 15, 16 | the known pending item, not a finding; the kit's and README's wording about the printed number is stale (N4) |

No kit file constructs `MultisliceParams`; every path that does (torus runner, pipeline adapter,
test cases, sizing tool) passes the new field at a1ef2a0. Cosmetic, outside the kit: the torus
runner still labels `memory_bytes["total"]` "engine arrays" (run_torus_multislice.py:232-233;
`engine arrays 238 MB` in row 22), which after H7 is the numpy peak of one realisation.

## 5. README_ALLIANCE.md walkthrough for tonight (item 5)

| Step | Runnable as written? | Evidence |
|---|---|---|
| §1 prerequisites (CCDB, keys, MFA, ssh config) | not testable here | NOT RUN |
| §2 clone | runs, but yields the moving branch tip, not the audited commit | N1 (MAJOR), row 24 |
| §3 setup, incl. its three failure recipes | yes: messages and "rerun the same command" advice match the script; the DONE line matches; "52 tests" matches | rows 6, 7, 9 |
| §4 time and limit rules, per-cluster requests | yes | rows 8, 10, 25, 28 |
| §4.1 gpu-check | yes; success line as quoted; the quoted numpy complex64 deviations (1.8e-5, 9.2e-5) reappear | row 13 |
| §4.2 gpu-sanity | yes (refused until the gpu-check PASS exists, as the README says); nothing on FAIL | row 20; N3 |
| §4.3 smoke | yes; every quoted output line reproduced | row 21 |
| §4.4 demo-gpu | yes; `NO HEIGHT: no-step control failed or not performed` then `finished with status 0`, as quoted; its memory figure (127 MiB) is pre-H7 (the job prints 230.3 MiB) | row 34; N4 |
| §4.5 torus | yes | row 22 |
| §4.6 null-study | presented as the next step of "in this order"; not marked ON HOLD | N2 (MAJOR) |
| §6 collect and checksums | yes | row 27 |
| Trillium / Narval alternatives | Trillium: flags, refusals, the job's Trillium branch as described (rows 25, 31); Narval: the tests/hpc dry-run matrix only (row 8) | - |

## 6. New findings, ranked

No BLOCKER at a1ef2a0.

### N1. MAJOR (conditional): the walkthrough clones a moving, in-progress branch, not the audited commit
* Where: scripts/hpc/alliance/README_ALLIANCE.md:60-66 and :74-77 (`git clone --branch
  claude/electron-holography-orchestration-nakd7r ... && git log -1 --oneline`): no commit is named,
  nothing is checked out, and no step says which `git log -1` line to expect.
* What is wrong: the branch receives orchestrator snapshot commits ("Snapshot in-progress agent
  work: not final") every few minutes. During this audit its tip moved from a1ef2a0 to 3e99722
  (row 24), and 3e99722 already changes the engine that gpu-check hashes and exercises
  (`reflection_holo/forward/multislice/potentials.py` +194 lines, `engine.py`, `__init__.py`) and
  `tests/forward/ladder_cases.py`, from which gpu_check.py builds its rung-1 case. Neither H6, H7 nor
  this audit has examined that state.
* Why it matters tonight: whatever the tip is when Ali clones is what runs, on each cluster
  separately (clones made an hour apart can differ). An in-progress change to the engine, to the
  null-study code being redesigned (`study.yaml`, `run_study.py`, `tests/forward/null_test_cases.py`)
  or to the strip builder makes gpu-sanity compare new code with the stored references and FAIL for
  a non-GPU reason (section 2), or breaks a job outright; a gpu-check PASS would then vouch for code
  nobody reviewed. The kit cannot catch this: its gate hashes whatever is checked out.
* Reproduction: row 24.
* Fix: README §2: after the clone, `git checkout --detach a1ef2a0` (or a tag made for tonight) and
  check that `git log -1 --oneline` prints `a1ef2a0 H7: apply H5 to the code ...`, the same on every
  cluster. The kit works on a detached HEAD (the whole emulation ran on one: rows 9-34). Whether
  a1ef2a0 is on GitHub was not checked (no fetch; the local tracking ref contains it): NOT RUN.

### N2. MAJOR: README_ALLIANCE.md does not say that the null study is on hold
* Where: README_ALLIANCE.md:142 (`## 4. Submit, in this order`) continues after torus with §4.6
  `null-study (17 points, GPU, cupy)` (:252-299: "Then all 17 points in ONE job (the default)",
  command at :258, expected sizes); :17-18 lists null-study outputs among the expected results.
  `grep -n "on hold\|redesign"` over README_ALLIANCE.md, null_test_study/README.md, kit.py and
  submit.sh: no match. The kit accepts the job (the tests/hpc dry-run matrix builds a serial GPU
  null-study job on every cluster, row 8).
* Why it matters: the README is tonight's walkthrough and presents the null study as the step after
  torus. Its cells are shallower than the extinction depth (the reason it is on hold), so running it
  spends GPU allocation on results already known to be uninformative, and nothing in the outputs
  would say so. Nothing in tonight's five jobs needs the study (gpu-sanity only reuses point 0 as a
  backend-consistency check, section 2).
* Fix: a note at the top of §4.6 and in §4's order ("ON HOLD: cells shallower than the extinction
  depth; being redesigned; do not run"), the same in null_test_study/README.md; optionally make
  kit.py refuse `null-study` with the default study until the redesign lands.

### N3. MINOR: a gpu-sanity FAIL has no instruction and gates nothing
* Where: README_ALLIANCE.md:192-207 gives only the success line; A/kit.py:591 gates GPU jobs on the
  gpu-check PASS alone.
* Effect: after `GPU SANITY: FAIL` (exit 1 or 5, row 17) demo-gpu is still accepted and nothing
  tells Ali to stop and bring back `runs/gpu-sanity_<jobid>_*/gpu_sanity/gpu_sanity.json`.
* Fix: README §4.2: "On FAIL stop GPU jobs on this cluster; bring back gpu_sanity.json, study.log
  and buildup.log (section 6)". A gate is optional (H2's step 0 is a check, not a proof).

### N4. MINOR: memory statements made stale by H7's memory model
* Where: README_ALLIANCE.md:228-229 (demo-gpu "Memory per realisation about 127 MiB"), :316-322
  (§4.7: the dry run's "memory per realisation" "counts only the engine's arrays of one
  realisation", "about 192-240 B per atom ... not measured"), :275-295 (§4.6 table in the pre-H7
  `engine arrays N MB` format); A/kit.py:71-78 (pipeline hint: "counts only the engine's arrays ...
  printed ~127 MiB per realisation") and :82-84 (null-study hint: "at most 340 MB").
* Measured at a1ef2a0: the demo's dry run prints `memory per realisation ~230.3 MiB (numpy backend,
  host); cupy backend: device ~70.2 MiB (lower bound ...), host ~204.9 MiB` (row 15, and the same
  line in the demo-gpu job log, row 34); run_study.py prints `memory peak 5 MB (numpy/CPU; GPU device
  3 MB, lower bound)` for point 0 (row 16). H7 §1: `memory_bytes["total"]` is now the numpy peak of
  one realisation including the cell's atom arrays and the realise() bytes; 192 B/atom modelled,
  193 B/atom measured by H5.
* Effect: Ali sees 230 MiB where the README says about 127 MiB, and the hint tells him the number
  excludes what it now includes. No job fails (demo-gpu takes the recommended per-GPU memory; the
  structure build's peak RSS is unchanged at 3628 MB, row 15).
* Fix: bring the four places to H7's wording. The planned `--need-gpu-mem-gb` from
  `device_peak_cupy` is the known pending item and not counted here.

### N5. MINOR: a login-shell PYTHONPATH reaches every job, shadows the venv, and is not recorded
* Where: A/job.sbatch:86-92 activates the venv, sets PYTHONNOUSERSITE and checks `sys.prefix`, but
  leaves PYTHONPATH as inherited through `--export=ALL`; A/kit.py:697-702 (job_info.json records a
  fixed list of variables, not PYTHONPATH); setup_alliance.sh runs its import check and physics gate
  with the login shell's PYTHONPATH as well.
* Reproduction: the emulation itself. The setup-built venv's cupy cannot be imported, yet every
  emulated GPU job imported the numpy-impersonating cupy from the login shell's PYTHONPATH
  (gpu_check.json `cupy_version "0.0+numpy-impersonation(h4b)"`), and neither job_info.json nor the
  copied manifest names PYTHONPATH or the module's path (row 32). Worse, the provenance manifests of
  the demo-gpu run record `"cupy": "14.1.0"` (row 34): reflection_holo/provenance/manifest.py:3, 141
  take versions from `importlib.metadata` (the installed distributions), so a shadowing module is
  reported as the installed one.
* Why it matters: Python.wiki:812-813 tells users not to modify PYTHONPATH, but a leftover export in
  `~/.bashrc` would silently replace venv packages (numpy, cupy) in the jobs and the records would
  not show it. Low probability; cheap to close.
* Fix: `unset PYTHONPATH` (or refuse when non-empty) in job.sbatch before activating the venv and in
  setup_alliance.sh; add PYTHONPATH to the keys of `kit.py job-record`.

## 7. Anything new that would break on a cluster (item 6)

The H6 additions (study copy and hash, env-check, gate-check, requeue names, stamps and supersede
logic in setup, collect caps, dry_run_job.py, gpu_sanity.py) were read line by line. They use only
bash 4.2 constructs (ShellCheck clean; every script ran under GNU bash 4.2: rows 4, 6-34), GNU
coreutils/tar options that EL9 has, the Python standard library, and paths under $SCRATCH for
everything a job writes (Trillium's read-only $HOME is only read). A time-limit SIGTERM is handled
(row 33). Nothing new was found that would break on the clusters beyond N1-N5. What this audit
cannot establish is unchanged from H4/H6 (section 8).

Notes (no severity):
* `--mem=280G`/`250G`/`124G` is requested for every full-GPU job, including the 15-minute
  gpu-check, as the wiki's recommended bundle: policy-conformant, but it may lengthen queue waits on
  a busy night (`--mem` lowers it).
* The torus guard (0.8 x walltime / kinds) bounds the calibrated estimate, not the wall time; with
  both kinds near 1440 s and the x1.5 calibration 20 % off, `--time 01:00:00` could be exceeded. At
  T1's speeds (163-213 s) this is far away; a kill is recorded as status 143 (row 33).
* tests/hpc still has no emulated run of gpu-sanity, torus or demo-gpu through job.sbatch, nor of
  job.sbatch's Trillium branch; this audit ran them (rows 20-22, 31, 34). The numpy-impersonating
  cupy cannot reveal host/device mixing (by reading: engine.py:259 `be.to_numpy`,
  gpu_check.py:103-104 `cp.asnumpy`; no mixing found).

## 8. NOT RUN (and why)

* Anything on an Alliance cluster (no ssh by design): real Lmod (`module -t list` on login vs
  compute nodes, sticky and hidden modules; emulated here by a BASH_ENV function), real `sbatch`
  (option validation; `--export` with empty values such as `RH_VARIANT=` is accepted by the fake
  only), `SLURM_CPUS_ON_NODE` on Trillium, Trillium's acceptance of `--gpus-per-node=h100:1`, Slurm's
  own time-limit sequence (SIGTERM, KillWait, SIGKILL; only the SIGTERM part was emulated, row 33),
  requeue.
* Any GPU execution: gpu-check, gpu-sanity and demo-gpu ran with numpy impersonating cupy, which
  tests the kit's plumbing and the engine's backend-agnostic code, not cuFFT/cuBLAS or a device.
  Every GPU time is still the GPU_ASSUMED model; the gpu-sanity strip has never run on a GPU.
* The real Alliance wheelhouse and PyPI (H4's local wheelhouse, stand-in cupy wheel and the local
  SHA-verified abTEM wheel were used), setup with a cupy that imports from the wheelhouse,
  `--recreate` and the `--cuda-module` supersede path (H6 ran them; that code is unchanged).
* `git clone` from GitHub and whether a1ef2a0 is on GitHub (no fetch). The branch tip 3e99722 was
  only diffed, not audited or run.
* A read-only $HOME (Trillium compute nodes); Narval end to end (dry-run matrix only).
* The null study (on hold) beyond its first point inside gpu-sanity.
* The full repository test suite (only tests/hpc in three variants and the setup's 52-test gate;
  H6/H7 ran the full suite, one timing-only failure in test_smoke_atomistic under load).

## 9. Verdict

| ID | Severity | Item | Verdict | Needed before tonight? |
|---|---|---|---|---|
| F1-F13 | - | H4 findings | all FIXED, no regression (section 1) | - |
| N1 | MAJOR (conditional) | README clones the moving in-progress branch, not a1ef2a0 | row 24 | yes: pin the commit (condition 1) |
| N2 | MAJOR | README does not say the null study is on hold | README grep, :142, :252-299 | yes: README note, or Ali told explicitly (condition 2) |
| N3 | MINOR | gpu-sanity FAIL: no instruction, no gate | code/README reading, row 17 | condition 3 covers it |
| N4 | MINOR | memory wording stale after H7 | rows 15, 16, 34 | no (expect 230 MiB) |
| N5 | MINOR | PYTHONPATH inherited by jobs, not recorded; manifests then report the installed version | rows 32, 34 | condition 4 covers it |

**Ready for tonight's job list: yes**, under these exact conditions:
1. On every cluster, right after `git clone`: `git checkout --detach a1ef2a0` and confirm that
   `git log -1 --oneline` prints `a1ef2a0 H7: apply H5 to the code ...` before running
   setup_alliance.sh (N1). Any other commit needs the same checks first (tests/hpc; the gpu-sanity
   numpy check of row 16).
2. Run only setup, gpu-check, gpu-sanity, smoke, demo-gpu and torus; do NOT run §4.6 null-study
   (N2), and either the README gets the ON HOLD note or Ali is told.
3. GPU jobs on a cluster only after that cluster's gpu-check prints `GPU CHECK: PASS` (the kit
   enforces this); if gpu-sanity prints `GPU SANITY: FAIL`, stop GPU jobs on that cluster and bring
   back its gpu_sanity.json and logs (N3).
4. In the login shell before setup and before submitting: `echo "PYTHONPATH=[$PYTHONPATH]"` must
   print `PYTHONPATH=[]`, otherwise `unset PYTHONPATH` (N5).
5. Read demo-gpu's dry-run memory line as the numpy host peak (about 230 MiB) with a cupy device
   lower bound (about 70 MiB), not the README's 127 MiB (N4); `NO HEIGHT` from demo-gpu remains the
   expected outcome.

The GPU path itself stays unverified until the first real gpu-check; nothing in the kit presents an
engine output as validated.
