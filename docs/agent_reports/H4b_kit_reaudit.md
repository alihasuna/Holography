# H4b: re-audit of the Alliance kit at commit a1ef2a0 (after H6 and H7)

Agent: H4b (code auditor). Date: 2026-09-24. Status: IN PROGRESS (written incrementally; the verdict
in the last section is the final word).

Scope: everything tonight's list touches (setup_alliance.sh, then gpu-check, gpu-sanity, smoke,
demo-gpu, torus on Fir/Nibi/Rorqual, Narval/Trillium as alternatives): `scripts/hpc/alliance/`
(clusters.yaml, kit.py, setup_alliance.sh, submit.sh, job.sbatch, gpu_check.py, gpu_sanity.py,
dry_run_job.py, collect_results.sh, README_ALLIANCE.md), `scripts/hpc/run_pipeline.slurm`,
`scripts/torus/run_torus_multislice.py`, `scripts/hpc/null_test_study/` (only as a dependency of
gpu-sanity), `tools/hpc/supercell_sizing.py` (`--measure`, used by gpu-sanity), `tests/hpc/`, and the
H7 engine API (`MultisliceParams.working_reflections_hkl`, band assertion, `memory_model`).

Method: a detached worktree of a1ef2a0 at
`scratchpad/h4b_wt` (`git worktree add --detach`), audited and run there only; the main venv's
packages reached through a venv shim inside the worktree (`venv/`, gitignored: `python -m venv
--without-pip` plus two `.pth` lines, one to `/home/user/Holography/venv/lib/python3.11/site-packages`
and one to the worktree, so `reflection_holo` resolves to the worktree; nothing installed). Verified:
`reflection_holo.__file__` = `.../h4b_wt/reflection_holo/__init__.py`, `git status --porcelain` of
the worktree empty. Stand-ins reused from H4/H6: GNU bash 4.2.0 (`scratchpad/h4/bash42bin`),
ShellCheck 0.11.0 (`scratchpad/h4/sc_venv`), the Lmod-like BASH_ENV profile, H4's 69-wheel wheelhouse
and stand-in cupy wheel. Nothing under audit was modified; no commit, no push, no ssh, no personal
data sent anywhere. Machine: 4 CPUs, 15 GB, bash 5.2.21, no GPU/Lmod/Slurm; shared with other
agents' runs (load 7-12 at the start).

Severity: BLOCKER = breaks tonight's list on a cluster or gives a wrong verdict; MAJOR = likely
failure or misleading result in a plausible path of tonight, or a guard that does not guard;
MINOR = correctness/documentation issue with a workaround.

Kit and engine at a1ef2a0 are byte-identical to H6's commit 2c0d122 (`git diff --stat 2c0d122
a1ef2a0 -- scripts/hpc tests/hpc tools/hpc reflection_holo scripts/torus configs tests/forward`:
empty; the commits after 2c0d122 touch only docs/agent_reports, tools/review, tools/validation,
tools/physics_checks).

## Command log

(filled in as the audit proceeds; S = scratchpad, W = S/h4b_wt, PY = W/venv/bin/python with
PYTHONPATH=W)

| # | Command (abridged) | Result |
|---|---|---|
| 1 | `git -C /home/user/Holography worktree add --detach W a1ef2a0` | `HEAD is now at a1ef2a0` |
| 2 | `git diff --stat 2c0d122 a1ef2a0 -- <kit, engine, tools/hpc, tests>`; `git log 2c0d122..a1ef2a0 --stat` | empty diff for every audited path |
| 3 | venv shim (above); `PYTHONPATH=W PY -c "import reflection_holo; ..."` | resolves to the worktree; numpy 2.4.6, abtem 1.0.10, pytest 9.1.1 |
| 4 | `bash -n` (5.2.21 and GNU 4.2.0) and ShellCheck 0.11.0 `-s bash` on setup_alliance.sh, submit.sh, job.sbatch, collect_results.sh, run_pipeline.slurm, tests/hpc/bin/fake_module (in W) | exit 0 on all six, both bash versions, ShellCheck silent; `-o all` adds only optional notes (SC2250/2292 style, SC2310/2312: functions in conditions call `die`/`exit`, which still exits) |
| 5 | e2e stand-ins in S/h4b/e2e: Lmod-like `module` as a shell FUNCTION from BASH_ENV/ENV, stateful through an exported variable, sticky CCconfig/gentoo/StdEnv that `module purge` keeps (Utiliser_des_modules__en.wiki:63), unknown modules fail; fake `nvidia-smi`, `scontrol`; `sbatch` = symlink to W/tests/hpc/bin/fake_sbatch; numpy-impersonating `cupy` (+`cupyx.scipy.ndimage`) with threaded scipy.fft; fresh `git clone` of the main repository checked out at a1ef2a0 (`git status --porcelain` empty); TMPDIR on `mount -t tmpfs -o noexec` (`findmnt`: `rw,noexec,relatime`) | stand-ins ready |
| 6 | setup run 1: `env -i ... BASH_ENV=<profile> TMPDIR=<noexec> <bash 4.2> setup_alliance.sh fir` (PyPI blocked: `PIP_INDEX_URL=http://127.0.0.1:9/simple`) | `exit 2 after 6 s`: `ERROR: pip download of abtem failed (no PyPI access from this login node?). Copy abtem-1.0.10-py3-none-any.whl to this cluster and rerun the same command with --abtem-wheel PATH (no --recreate needed)`; only `steps/venv.done` (F3 fixed: fails before the wheelhouse install) |
| 7 | setup run 2: same + `--abtem-wheel <verified wheel>` | `exit 2 after 52 s`: `== venv: already made`, `abtem wheel SHA-256 verified: 34e09866...515d`, wheelhouse/abtem/repo stamped, `No broken requirements found.`, `multislice engine: (True, 'available')`, then `ERROR: 'import cupy' failed on this login node ... rerun the same command with --allow-cupy-import-failure (no reinstall)`; every `module` call went to the BASH_ENV function (14 recorded) |
| 8 | `cd W; PYTHONPATH=W PATH=<shellcheck>:$PATH PY -m pytest -q -p no:cacheprovider -rs tests/hpc` (bash 5.2.21) | `114 passed in 350.55s (0:05:50)` (no skip: ShellCheck ran) |
| 9 | setup run 3: same as run 2 + `--allow-cupy-import-failure` (bash 4.2, BASH_ENV function, noexec TMPDIR) | `exit 0 after 138 s`: every step `already installed`, `WARNING: FAILED on the login node (--allow-cupy-import-failure)`, `52 passed, 1 deselected in 129.11s`, `== DONE: environment fir-20260924T001840Z-d33682f3da69 ready`; module_list.txt = the 8 modules of the Lmod-like state (sticky ones included); setup logs hard-linked (link count 2); `git status --porcelain` of the clone empty (F1 gate and F3/F13 fixes hold under the H4 triggers) |
| 10 | README §4.1 as written, emulated login node: `bash submit.sh fir gpu-check --account def-XXX --time 00:15:00 --dry-run` (bash 4.2) | exit 0; `NOTE: time limit 00:15:00 = 00:15:00 (15 min)`; `sbatch --account=def-XXX --time=00:15:00 --gpus=h100:1 --cpus-per-task=12 --mem=280G --job-name=reflholo-gpu-check --output=<scratch>/reflholo/logs/gpu-check_%j.log --chdir=<scratch>/reflholo --export=ALL,...`; `DRY RUN: nothing submitted` |
