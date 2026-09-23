# H3 — Alliance (Digital Research Alliance of Canada) run kit

Agent: H3. Date: 2026-09-23. Status: see section 6 (written incrementally).

Scope: a ready-to-run kit under `scripts/hpc/alliance/` so that Ali can ssh into Fir, Nibi, Rorqual,
Narval or Trillium tonight and run our jobs himself. No agent ssh'es anywhere (the wiki: automation
nodes "are not suitable for usage of AI agents", H1 §4.5). Every cluster fact comes from H1
(`docs/agent_reports/H1_alliance_wiki.md`, `H1_alliance_clusters.tsv`) and the cached wikitext
(`scratchpad/alliance_wiki_cache/`), with a locator; anything the wiki does not state is NOT_FOUND
and must be supplied by the user. Nothing was committed or pushed.

## 1. What was built

| File | What it is |
|---|---|
| `scripts/hpc/alliance/clusters.yaml` | The single source of cluster facts: one profile per cluster (fir, nibi, rorqual, narval, trillium) plus `common`. Every value is `{value, locator}`; NOT_FOUND where the wiki is silent (max array size, running-job limits of the GP clusters, Nibi test-job minimum, scratch path on Nibi/Narval, cupy's CUDA build). Login hosts, GPU request syntax per instance (full GPU and MIG), recommended cores and memory per instance (bundle table), max/min walltime, job limits, storage quotas and purge, internet, Trillium specifics (no MIG, no --mem, no -c, 24 cores per GPU, GPU login node, CPU jobs refused). |
| `scripts/hpc/alliance/kit.py` | Python helper: validates a submission and builds the sbatch argv from clusters.yaml (`plan`), maps an array index to a study point (`study-point`), compares module lists (`modules-diff`), writes the job record (`job-record`). |
| `scripts/hpc/alliance/setup_alliance.sh` | Once per cluster on a login node: `module purge`; `StdEnv/2023`, `python/3.11.5`, `cuda/12.6` (each verified loaded); `virtualenv --no-download venv`; `pip install --no-index` from the wheelhouse (numpy, pyyaml, pytest, setuptools, wheel, scipy, matplotlib, `cupy==14.1.0`, and every requirement of abTEM 1.0.10); abTEM 1.0.10 by `pip download --no-deps --only-binary=:all:` on the login node, filename must be the none-any wheel, SHA-256 checked against PyPI (`34e09866…`, D3 item 0.2), installed with `--no-index`; our package `pip install --no-index --no-build-isolation -e ".[test]"`; `pip check`; import check; test subset (no GPU); records in `venv/alliance/` (modules.sh, module_list.txt, env.json, pip_freeze.txt, package_sources.tsv from `pip install --report`, avail_wheels.txt, setup.log). Options: `--recreate`, `--python-module`, `--cuda-module`, `--cupy-spec`, `--abtem-wheel`, `--allow-cupy-import-failure`. Refuses without the `module` command, outside the repo root, without git, with an existing venv. |
| `scripts/hpc/alliance/submit.sh` | `submit.sh <cluster> <job> --account A --time T [options] [--dry-run]`. Jobs: gpu-check, smoke, demo-gpu, pipeline (any `--config`, `--variant`), torus (`--kinds`), null-study (array `0-16`; `--only`, `--serial`, `--array-throttle`, `--study`). Resource options: `--gpu-instance full|<MIG>`, `--need-gpu-mem-gb`, `--cpus`, `--mem`, `--scratch`. No default account or time; `--mem` required for CPU jobs; GPU jobs default to the wiki's recommended cores and memory per instance. Checks git before submitting, loads the recorded modules, refuses GPU jobs until a gpu-check PASS exists for the environment. |
| `scripts/hpc/alliance/job.sbatch` | The batch script (no `#SBATCH` defaults). Job dir `$SCRATCH/reflholo/runs/<job>_<jobid>_<UTC>/` (arrays: `runs/<job>_<arrayjob>/task<NNN>_<jobid>_<UTC>/`), never reused; `module purge` + recorded modules, refuses if the loaded set differs; venv; threads = the run's declared threads, checked against `--cpus-per-task`; git check before computing; GPU: nvidia-smi and cupy pre-flight; runs the job (pipeline jobs are delegated to `scripts/hpc/run_pipeline.slurm` in job mode); EXIT/TERM trap copies the Slurm log, the submission record and every manifest into the job dir and writes job_status.txt. CuPy/numba/matplotlib caches under `$SCRATCH/reflholo/cache` (home is read-only on Trillium compute nodes). |
| `scripts/hpc/alliance/gpu_check.py` | cupy import, CUDA runtime/driver, device; cupy FFT vs numpy (complex128 tol 1e-10, complex64 1e-4); two tiny multislice cases (rung-1 continuum, 40k-atom a/2 step) numpy complex128 reference vs cupy complex128 (tol 1e-9) and complex64 (tol 1e-3); tolerances fixed before any GPU run; writes gpu_check.json, a run manifest, and on success the PASS record. Exit 0/1/4. |
| `scripts/hpc/alliance/collect_results.sh` | `--max-array-mb N` required; optional `--jobs`, `--run-root`, `--out`; tarball with MANIFEST.sha256, SKIPPED_ARRAYS.tsv, COLLECT_INFO.txt, and a `.sha256` next to it. |
| `scripts/hpc/alliance/ssh_config.example` | Host blocks fir, nibi, rorqual, narval, trillium, trillium-gpu with USERNAME placeholders and the ControlMaster lines verbatim from the MFA page. |
| `scripts/hpc/alliance/README_ALLIANCE.md` | Tonight's checklist (prerequisites, ssh, clone into $HOME and why, setup, gpu-check, smoke, demo-gpu, torus, null-study, H2 hook, outputs, collection, NOT_FOUND list). |
| `tests/hpc/test_alliance_kit.py`, `tests/hpc/fake_slurm.py` | Tests (section 3) with a fake `module`, a recording `sbatch` and a small sbatch emulator that runs job.sbatch. |
| `scripts/hpc/run_pipeline.slurm` (changed) | Two backward-compatible additions: `RH_PARTITION=none` omits `--partition` (Running_jobs § Do not specify a partition); `RH_WORKDIR` (default: the repository, unchanged) receives the job's dry-run text. The A3/A3b fixes are untouched (dry-run to a file then `head` on the file, no pipefail pipe into head; `${A[@]+"${A[@]}"}` for every possibly empty array incl. the new `PART`; git check in both modes; no default account/partition/time/GPU). |
| `scripts/hpc/README_HPC.md` (changed) | A pointer to the kit at the top. |
| `.gitignore` (changed) | `alliance_setup_*.log`. |

### Choices and their sources
* Python module `python/3.11.5`: pyproject requires >= 3.11; Wheels3.11 has cupy 14.1.0, pyfftw 0.15.1
  (row "pyfftw, pyFFTW") and a row for every abTEM 1.0.10 requirement; the wiki's own GPU job example
  loads exactly `StdEnv/2023`, `cuda/12.6`, `python/3.11.5` (Trillium_Quickstart § Example:
  Single-GPU Job); this repository's venv here is Python 3.11. Caveat (Python § Python version
  supported: wheels "only for the 3 most recent Python versions"): if a 3.11 wheel is missing, pip
  fails loudly and `--python-module python/3.12.4` is the documented alternative (Wheels3.12 has
  cupy 14.1.0 too). pyfftw is in the 3.11 table as the row "pyfftw, pyFFTW" (0.15.1, 0.13.1);
  PyYAML as "pyyaml, PyYAML" (6.0.3 ...); a plain-name grep misses both (checked).
* CUDA module `cuda/12.6`: which CUDA the wheelhouse cupy was built for is NOT_FOUND on the wiki
  (the CUDA page has no version list; wheel tables have no build info). 12.6 is the version the
  wiki's GPU examples load with python/3.11.5; the gpu-check job is the arbiter.
* abTEM 1.0.10 requirements (PyPI JSON, cached by H1): numpy>=2.0.0, pandas, matplotlib>=3.6, pyfftw,
  scipy, numba, dask (!=2025.12.*, !=2026.1.0, !=2026.1.1, >=2022.12.1), distributed, zarr>=3.1,
  ase, threadpoolctl, tabulate, ipywidgets, ipympl, tqdm. All have rows in Wheels3.11; all are
  installed from the wheelhouse; only abTEM itself comes from PyPI (pre-downloaded). The actual
  origin of every installed distribution is written by setup to `venv/alliance/package_sources.tsv`
  (from pip's `--report`); that file does not exist yet (setup NOT RUN on a cluster).
* GPU request syntax is the cluster page's own (`--gpus=h100:1`, `--gpus=a100:1`, MIG long names on
  Fir, short names on Nibi/Rorqual, `--nodes=1 --gpus-per-node=1` on Trillium); the model is always
  named (Scheduling_policy_updates § GPU jobs). Memory strings: the bundle table's "GB" read as Slurm
  "G" (INFERENCE, consistent with the node tables: e.g. Rorqual 4 x 124 <= 498G).
* Jobs refuse to compute without git (A3 M5); `module purge` then the recorded modules in every job
  (Running_jobs § Troubleshooting > Jobs inherit environment variables).
* Gate: GPU jobs other than gpu-check are refused until `$SCRATCH/reflholo/gpu_check/PASS_<cluster>_<env id>_*.json`
  exists (override `--skip-gpu-check-gate`, recorded as UNVERIFIED in the submission record).

## 2. What was run here (no cluster, no GPU; 4 CPUs shared with agent H2's background engine runs)

1. Null-study estimator, numpy backend, 4 threads (copy of study.yaml with `backend: numpy`,
   `threads: 4`): `run_study.py --config <copy> --out <scratch> --estimate`, 26 s wall, exit 0. The
   17 lines are quoted verbatim in README_ALLIANCE.md §4.5; sums: 6588 s CPU (x1.5 calibration
   included), 114.7 s GPU_ASSUMPTION, largest engine arrays 340 MB.
2. `python -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml`: exit 4 (cupy not
   installed here, as designed), grid 1920 x 432, 7215 slices, 1,440,000 atoms, "memory per
   realisation ~126.6 MiB", "GPU (ASSUMPTION model, not measured) ~9 s"; 52 s wall (machine shared).
3. Smoke run (`pipeline run --config configs/demo_smoke_si001.yaml`): exit 0, 3.4 s wall, peak RSS
   131.5 MB (used for the `--mem 2G` advice).
4. Tiny multislice cases (numpy): rung-1 continuum 2550 x 1 x 1030 slices, 0.50 s complex128;
   complex64 vs complex128 max relative deviation 1.78e-5. Atomistic a/2 step, width 2 periods,
   640 x 120 x 1434 slices, 39,872 atoms: build 2.5 s, run 14.7 s (complex128); complex64 deviation
   9.22e-5. These fixed the gpu-check complex64 tolerance at 1e-3 (about ten times), before any GPU
   run.
5. shellcheck: not installed; installed `shellcheck-py` (ShellCheck 0.11.0) into a scratch venv
   only. Result on setup_alliance.sh, submit.sh, job.sbatch, collect_results.sh,
   run_pipeline.slurm: two info-level notes (SC2015 `A && B || C` in setup; SC2329 trap-invoked
   function), both fixed; now clean (exit 0). `bash -n` clean on every script.
6. Emulated batch jobs (tests/hpc/fake_slurm.py: fake `module`, an sbatch that runs job.sbatch with
   the exported variables):
   * smoke on "fir": exit 0 in 5 s; heights `+2.7156 +- 0.0165`, `-1.3576 +- 0.0082`,
     `-1.3580 +- 0.0082 A`, no-step control PASS; job dir with pipeline/, manifests/,
     slurm.log, job_info.json, module_list.txt, submission.json, the dry-run text; the clone's
     `git status` unchanged.
   * torus on "nibi", first attempt (machine loaded by other runs): both kinds REFUSED by the
     runner's own guard (calibrated estimates 668 s and 865 s > 600 s), job exit 2 after 44 s.
     Second attempt: trench completed (estimate 502 s; simulate 376.8 s, total 396.0 s, peak RSS
     1329 MB; manifest copied), ridge REFUSED (762 s), job exit 2. T1 had 213 s / 163 s estimates on
     a less loaded machine. The kit's torus branch works; the refusal is T1's CASE-limit guard,
     which H3 did not change (not my code; the limit is a safety of the T1 runner).
   * null-study array task 0 (numpy study copy, 2 threads) and gpu-check without a GPU (exit 4 at
     "nvidia-smi not found", no PASS record): in the test suite.
7. gpu_check.py end to end with numpy impersonating cupy (a fake `cupy`/`cupyx` package in a temp
   dir; a test of the PASS-record plumbing, NOT of a GPU): exit 0 and PASS record; with a fake
   cuFFT that raises: exit 1, error recorded, no PASS record. This surfaced a real-world fact:
   `import abtem` imports cupy, cupyx and cupyx.scipy.ndimage whenever cupy is importable and asserts
   that cupyx imports if cupy did (abtem/core/backend.py lines 17-42); it also builds
   `cp.ElementwiseKernel` objects and `@cp.fuse` functions at import time. With a real, working cupy
   this is harmless; a partially broken cupy would break `import abtem` and with it the Kirkland
   potential of every job, CPU jobs included. setup_alliance.sh imports abtem with cupy installed on
   the login node, so it would show this before any job.
8. Setup test subset (the exact command in setup_alliance.sh, 4 threads): see section 3.
9. Full suite `venv/bin/python -m pytest -q`: see section 3.

## 3. Tests

New: `tests/hpc/test_alliance_kit.py` (with `tests/hpc/fake_slurm.py`). They cover: `--dry-run` for
every cluster x every job (30 cases: sbatch argv, GPU flags per cluster with the model named,
Trillium `--nodes=1 --gpus-per-node=1` without `--mem`/`--cpus-per-task`, recommended cores/memory
per GPU, no partition, no `--gres`, `--output`/`--chdir`/`RH_RUN_ROOT` under `$SCRATCH`, job-id
stamped log names, `--array=0-16` and `%A_%a` for the null study, CPU jobs refused on Trillium, dry
run creates nothing and never calls sbatch); account required (dry and real; sbatch never called);
time required and never defaulted (dry and real); account prefix; walltime max/min per cluster
(Nibi: no test minimum stated, warning only); time format; `--mem` required for CPU jobs; GPU gate
(no PASS, PASS of another environment, override); MIG requests on Fir/Nibi/Rorqual/Narval and
refusals on Trillium; `--need-gpu-mem-gb`; the `pipeline` job with any config (cupy -> GPU,
numpy variant -> CPU); `$SCRATCH` required; environment of another cluster refused; unknown
cluster (Cedar: "retired") and job; real submission equals the dry run and is recorded; module set
mismatch refused; null-study option combinations; setup_alliance.sh refuses without the module
command (exit 2, before logging), with an unknown cluster, outside the repository; `bash -n` of every
script; shellcheck when installed (skipped otherwise); every clusters.yaml value has a locator;
clusters.yaml agrees with H1_alliance_clusters.tsv (login host, max walltime, GPUs per node, GPU
memory, internet, MIG sizes); the time parser; gpu_check without cupy (exit 4, no PASS) and its
comparison plumbing; gpu_check with numpy impersonating cupy (PASS record; raising cuFFT -> exit 1);
emulated smoke, null-study array task and gpu-check jobs end to end; collect_results.sh (cap
required, job selection, arrays over the cap listed, `sha256sum -c` passes after unpacking);
run_pipeline.slurm with `RH_PARTITION=none` (no `--partition`), with a real partition (unchanged),
and still refusing an unfilled PARTITION placeholder.

## 4. NOT RUN

* Anything on an Alliance cluster: no ssh, no login node, no Slurm, no Lmod, no GPU (by design; Ali
  runs the jobs). In particular:
  * `setup_alliance.sh` beyond its refusal paths: the module loads, `virtualenv --no-download`,
    `avail_wheels`, the `pip install --no-index` resolution of the 16 wheelhouse requirements for
    Python 3.11 in StdEnv/2023, `pip download` of abTEM from a login node (login-node internet is
    NOT_FOUND on the wiki), the editable install, the import check with a real cupy, the subset on
    a cluster. Whether every wheel resolves in StdEnv/2023 for Python 3.11 is UNTESTED.
  * Real `sbatch`: every submission was a dry run or went to a fake sbatch; job.sbatch ran only under
    the emulator (no real `scontrol`, `nvidia-smi`, cgroups, `SLURM_CPUS_ON_NODE` on Trillium).
  * **The cupy path of the engine: never executed** (gpu-check, demo-gpu, the null study on GPU).
    Every GPU time quoted is the engine's GPU_ASSUMPTION model, not a measurement.
  * Lmod behaviour: `module purge` with sticky modules, the exact `module -t list` format, the
    `set -u` safety of the `module` function (wrapped defensively, not tested with real Lmod).
  * The SSH config example (no ssh from here).
* The full torus pair did not complete in the emulated job (trench done, ridge refused by the
  runner's guard under load); the complete null study (17 points) was not run here (task 0 only, in
  the tests, on numpy).
* `collect_results.sh` ran on a synthetic run tree, not on real outputs.

## 5. Open questions for Ali / the orchestrator

1. Ali's RAP name on each cluster (`def-...`, `rrg-...`); required by every submission.
2. Is `github.com/alihasuna/Holography` private? Then the clone needs a token or the bundle route
   (README §2).
3. The torus runner's own 600 s CPU guard (T1 CASE limits, "about 10 minutes ... on this machine")
   may refuse on slower or loaded CPUs; raising it for cluster runs is a code decision for the
   orchestrator (H3 did not change T1 code).
4. Null study: the requested array (one point per task) against the wiki's advice for tasks much
   shorter than an hour (Job_arrays § A simple example); `--serial` is provided. Which one?
5. The CUDA module for the wheelhouse cupy (NOT_FOUND): cuda/12.6 is the wiki example's version;
   gpu-check decides; alternative `--cuda-module`.
6. `import abtem` imports cupy/cupyx whenever cupy is installed (section 2 item 7): acceptable, or
   should the Kirkland import be isolated from abTEM's backend module (a code change, not done)?
7. Agent H2's production configurations: pass them with `pipeline --config` (and `--gpu-instance`,
   `--need-gpu-mem-gb`, `--cpus`, `--mem`) or `null-study --study`; no kit change is needed. H2's
   report and tools (`docs/agent_reports/H2_realistic_supercell_sizing.md`, `tools/hpc/`) appeared
   during this work and were not modified or used.

## 6. Final state
