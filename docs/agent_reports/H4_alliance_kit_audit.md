# H4: audit of the Alliance run kit (H3)

Agent: H4 (code auditor). Date: 2026-09-23. Status: IN PROGRESS (written incrementally; the verdict
table at the end is the final word).

Scope: `scripts/hpc/alliance/` (clusters.yaml, kit.py, setup_alliance.sh, submit.sh, job.sbatch,
gpu_check.py, collect_results.sh, ssh_config.example, README_ALLIANCE.md); the H3 changes to
`scripts/hpc/run_pipeline.slurm`, `scripts/hpc/README_HPC.md`, `.gitignore` (`git diff 1d87c45`);
`tests/hpc/`. Kit files audited as committed in 69d2de0 (working tree identical for every kit file;
`git status` shows only H2 files and the H3 report modified). Facts checked against the raw wikitext
cache `scratchpad/alliance_wiki_cache/` (revision ids in its manifest.tsv), not against H1's summary.

Nothing under audit was modified. No commit, no push, no ssh anywhere, no personal data sent.
Reproductions ran in scratch directories
(`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/h4/`), with
fake `module`/`sbatch`/`virtualenv`/`avail_wheels` on PATH where a cluster tool is needed. This
machine: 4 CPUs, 15 GB RAM, bash 5.2.21, no GPU, no Lmod, no Slurm.

Severity: BLOCKER = breaks tonight on a cluster (Ali loses the evening or gets a wrong result);
MAJOR = likely failure or misleading result in a plausible path, or a guard that does not guard;
MINOR = correctness/documentation issue with a workaround.

## Command log

Every command run for this audit, in order (outputs quoted in the findings). Commands not run are
listed under NOT RUN at the end.

| # | Command (abridged; S = scratchpad/h4) | Result |
|---|---|---|
| 1 | `git status; git log --oneline; git show --stat 69d2de0; git diff --stat 69d2de0 HEAD -- scripts/hpc tests/hpc .gitignore` | kit committed in 69d2de0; later commits touch only the H3 report and H2 files |
| 2 | `curl -sS https://pypi.org/pypi/abtem/1.0.10/json` | wheel sha256 `34e098662a26cedebd0154ae0660c49efb6149cba161a605f02ecf381f45515d` (401704 B, 2026-07-06); requires_python `>=3.11`; 15 runtime requirements (section 1) |
| 3 | setup's step-6 import heredoc with `venv/bin/python` | passes (abtem 1.0.10) |
| 4 | grep/sed of the wiki cache pages named in section 1 | quotes in section 1 |
| 5 | `venv/bin/python -m pytest -q -p no:cacheprovider tests/hpc -x` | `73 passed, 5 skipped` (1 min 45 s; skips = shellcheck absent) |
| 6 | `curl https://pypi.org/pypi/{cupy/14.1.0,cupy-cuda12x/14.1.0,numba/0.65.1}/json` | cupy needs `numpy<2.6,>=2.0`, `cuda-pathfinder==1.*,>=1.3.4`; numba 0.65.1 needs `numpy<2.5`, `llvmlite<0.48,>=0.47` |
| 7 | `venv/bin/pip download --only-binary=:all: -r <kit list minus cupy>` into S/wheelhouse; names checked against Wheels3.11 | 69 wheels, 177 MB; every name has a Wheels3.11 row |
| 8 | `pip wheel` of a stand-in `cupy 14.1.0` whose import raises `ImportError: libcuda.so.1 ...` | S/fakecupy_wheels |
| 9 | `git clone /home/user/Holography S/clone` (661762e) + stand-in `module`, `virtualenv`, `avail_wheels`, `python` in S/fakebin | fresh clone |
| 10 | `env -i ... bash scripts/hpc/alliance/setup_alliance.sh fir` (in S/clone) | exit 2 after full install: abTEM download failed (TLS bundle stripped by my `env -i`) |
| 11 | same with `--recreate`, PyPI reachable | abTEM downloaded, SHA-256 verified, `pip check` clean, import check OK, exit 2 at the cupy gate |
| 12 | same with `--recreate --allow-cupy-import-failure` | exit 0, `778 passed, 7 skipped, 2 deselected`, env id `fir-20260923T215230Z-f049afeca907` |
| 13 | `grep` of the scripts for `@Q`, `mapfile`, `declare -A`, `local -n`, `[[`, unguarded `${A[@]}` | none outside guarded forms |
| 14 | build GNU bash 4.2 from ftp.gnu.org; `PATH=<bash4.2>:$PATH pytest tests/hpc` | `73 passed, 5 skipped in 102.76s` |
| 14b | bash 4.2 explicitly on submit.sh (no args, null-study) and collect_results.sh; control `set -u; A=(); echo "${A[@]}"` | kit OK; control fails `A[@]: unbound variable` |
| 15 | ShellCheck 0.11.0 (shellcheck-py in a scratch venv) on the five scripts; also `-o all` | exit 0 each; only style/SC2154 notes |
| 16 | greedy resolution of the kit list against Wheels3.11 with PyPI metadata (scratch script) | 71 packages, no missing name, no conflict (section 3.3) |
| 17 | `BASH_ENV=<file defining module()> pytest tests/hpc -k <fir dry-runs, setup refusal, smoke>` | `8 failed` (F1) |
| 18 | `pipeline dry-run --config configs/demo_hpc_si001.yaml` under `resource.getrusage` | `EXIT 4 wall 52.4 s peak RSS 3629 MB` (F2) |
| 19 | gpu_check `fft_check` + `multislice_check` (rung-1) with numpy-impersonating cupy whose fft2 is wrong | every perturbation FAILs (section 4) |
| 20 | `collect_results.sh --max-array-mb 0` on a synthetic root (30 MB json, 20 MB log, 5 MB npz, .bin) | 22.7 MB tarball, npz skipped, .bin dropped silently (F10) |
| 21 | submit.sh via fake Slurm: (a) `nibi smoke --time 01:00`; (b) two parallel `rorqual smoke`; (c) `--scratch` with a space | (a) accepted, 1 min (F7); (b) one record for two jobs (F8); (c) clear refusal |
| 22 | `mount -t tmpfs -o noexec`; `pytest --basetemp=<noexec> tests/hpc -k ...`; `umount` | `7 failed, 1 passed`, `Permission denied` (F1) |
| 23 | `run_torus_multislice.py --kind {trench,ridge} --estimate-only`, 4 threads, x4 | ridge 557/461/763/420 s, trench 265/485/515/511 s (F11) |
| 24 | emulated Trillium gpu-check through submit.sh + job.sbatch (fake nvidia-smi) | `threads: 24 ... of 24 allocated cpus`, exit 4 (no cupy), no PASS |
| 25 | emulated jobs on the setup-built clone: smoke; null-study `--only tfix_bragg_abs0_L0`; array task 3 (numpy study copy, 2 threads) | all status 0; task 3 ran `tfix_bragg_abs05_L0` |
| 26 | scratch venv with the real `cupy-cuda12x==14.1.0` (PyPI) + abTEM deps; `import cupy`, `import abtem`, one CPU study point | import OK without driver; study `err_rad 0.5685887531628921` (section 2.3) |
| 27 | setup test subset in S/clone under `getrusage(RUSAGE_CHILDREN)` | `778 passed ... 117.90s`; largest process 631 MB (inside Trillium's 1-2 GB login-node guidance) |
| 28 | `ps aux --sort=-%cpu`; `git status -sb`; `git branch -r --contains 69d2de0` | another agent's 3-core job shared the VM from 22:05; kit commit on the tracking ref |

## 1. Cluster facts in the kit against the wiki cache (item 1)

Every value that reaches an `sbatch` argument, a module load, a host name or a limit was traced to
the cached wikitext. Quotes are verbatim from the cache (file:line of the cache).

| Kit value (file:line) | Wiki (cache file:line, quoted) | Verdict |
|---|---|---|
| Fir full GPU `--gpus=h100:1` (clusters.yaml:147) | Fir.wiki:221 `'''One H100-80gb''' : <code>--gpus=h100:1</code>` | OK |
| Fir MIG `--gpus=nvidia_h100_80gb_hbm3_{1g.10gb,2g.20gb,3g.40gb}:1` (clusters.yaml:154,159,164) | Fir.wiki:244-246 same three strings | OK |
| Nibi / Rorqual full `--gpus=h100:1`, MIG `--gpus=h100_{1g.10gb,2g.20gb,3g.40gb}:1` (clusters.yaml:200-215, 251-266) | Nibi.wiki:122,139-141; Rorqual__en.wiki:160,175-177 | OK |
| Narval full `--gpus=a100:1`, MIG `a100_{1g.5gb,2g.10gb,3g.20gb}` (clusters.yaml:302-317) | Narval__en.wiki:102,117-119 | OK; `a100_4g.20gb` excluded with a note (clusters.yaml:297-299), not silent |
| Trillium `--nodes=1 --gpus-per-node=1`, no `--mem`, no `-c` (clusters.yaml:367-383) | Trillium_Quickstart.wiki:590 "For single-GPU jobs, use `--gpus-per-node=1`"; :332 "It is not possible to request a certain number of core on Trillium"; :343 "Memory requests are ignored" | OK, but no GPU model: see F5 |
| Recommended cores/memory per instance (clusters.yaml:149-167, 202-218, 253-269, 304-320, 382) | Allocations_and_compute_scheduling.wiki:243-336, every "Recommended per GPU" cell (Fir 12 cores 280 GB, 1 / 35, 3 / 70, 6 / 140; Narval 12 / 124, 1 / 15, 3 / 31, 6 / 62; Nibi 14 / 250, 2 / 31, 4 / 62, 6 / 124; Rorqual 16 / 124, 2 / 15, 4 / 31, 8 / 62; Trillium 24 / 188) | OK, all 21 cells match; "GB" passed as Slurm "G" (labelled INFERENCE; 4 x 280G <= Fir node 1125G, 8 x 250G = Nibi 2000G) |
| Max walltime 168 h (fir, nibi, rorqual, narval), 24 h (trillium) (clusters.yaml:119,175,229,277,339) | Fir.wiki:59 "maximum job duration is 7 days (168 hours)"; Running_jobs.wiki:404 "no jobs are permitted longer than 168 hours"; Trillium_Quickstart.wiki:604 GPU "24 hours" | OK |
| Min test walltime 5 min (fir, rorqual, narval), 15 min (trillium), NOT_FOUND (nibi) | Fir.wiki:59, Rorqual__en.wiki:43, Narval__en.wiki:23 "five minutes for test jobs"; Trillium_Quickstart.wiki:604 "15 minutes" | OK (Nibi: see F7) |
| Job limits 1000 (GP), 500 submitted / 150 running (Trillium) | Running_jobs.wiki:404; Job_scheduling_policies.wiki:207; Trillium_Quickstart.wiki:604 | OK |
| Login hosts fir/nibi/rorqual/narval `.alliancecan.ca`, trillium / trillium-gpu `.alliancecan.ca` | Fir.wiki:9; Nibi.wiki:10; Rorqual__en.wiki:7; Narval__en.wiki:6; Trillium.wiki:9,12 (Quickstart :64,:70 give `.scinet.utoronto.ca`) | OK; inconsistency surfaced in clusters.yaml:326 and ssh_config.example:14-16, not silent |
| `trig-login01` (kit.py:353-360 warning) | Trillium_Quickstart.wiki:81 "`trig-login01` (the latter is the GPU login node)" | OK |
| GPU jobs from the GPU login node (Trillium) | Trillium_Quickstart.wiki:296 "GPU compute nodes must be submitted from the GPU login node" | OK (warning only; sbatch itself enforces) |
| Modules `StdEnv/2023`, `python/3.11.5`, `cuda/12.6` (setup_alliance.sh:39-41) | Trillium_Quickstart.wiki:626-628 (Single-GPU example) loads exactly these; Modules_avx512.wiki:984 cuda "... 12.2, 12.6, 12.9, 13.2, 13.3", :4129 python "... 3.11.5, 3.12.4, 3.13.2, 3.14.2, 3.14.7" | OK; the table is not per-StdEnv, so availability inside StdEnv/2023 on Fir/Nibi/Rorqual/Narval is inferred from the Trillium example (setup checks it with `loaded`) |
| `cupy==14.1.0` wheel (setup_alliance.sh:42) | Wheels3.11.wiki:1288 `cupy || 14.1.0, 14.0.1, 13.6.0, ...`; its PyPI requirement `cuda-pathfinder==1.*,>=1.3.4` (PyPI JSON, command 6) is in Wheels3.11.wiki:1268 | OK (CUDA build of the wheel: NOT_FOUND, correctly left to gpu-check) |
| abTEM 1.0.10 requirements (setup_alliance.sh:124-135) | PyPI JSON (command 2): `numpy>=2.0.0, pandas, matplotlib>=3.6, pyfftw, scipy, numba, dask!=2025.12.*,!=2026.1.0,!=2026.1.1,>=2022.12.1, distributed, zarr>=3.1, ase, threadpoolctl, tabulate, ipywidgets, ipympl, tqdm` | OK, identical list; every transitive dependency name that PyPI resolution pulls in (69 wheels) has a Wheels3.11 row (command 7) |
| abTEM SHA-256 `34e09866...515d` (setup_alliance.sh:44, clusters.yaml:77) | PyPI JSON `urls[0].digests.sha256` = `34e098662a26cedebd0154ae0660c49efb6149cba161a605f02ecf381f45515d` | OK (byte-identical); the real download from PyPI in the setup simulation matched it (command 11) |
| `virtualenv --no-download`, `pip install --no-index --upgrade pip`, `pip download --no-deps`, "none-any" | Python.wiki:77 `virtualenv --no-download ENV`; :85 `pip install --no-index --upgrade pip`; :415-416 "`pip download --no-deps tensorboardX` ... If the filename does not end with `none-any`..." | OK |
| venv in $HOME, not $SCRATCH | Python.wiki:71 "Do not create your virtual environment under $SCRATCH"; :130 "On Trillium it is recommended to create virtual environments from a login node in HOME" | OK |
| No partition | Running_jobs.wiki:391 (Do not specify a partition); Trillium_Quickstart.wiki:604 footnote "Do not specify this partition explicitly" | OK |
| Job outputs and `--chdir` on $SCRATCH | Trillium_Quickstart.wiki:314-317 "home and project directories only available for reading on the compute nodes ... you should also submit your jobs from your $SCRATCH directory" | OK (`--chdir` and `--output` under $SCRATCH; caches moved to $SCRATCH) |
| ControlMaster lines (ssh_config.example:31-33) | Multifactor_authentication.wiki:131-134 verbatim | OK |
| MIG: one instance per job | Multi-Instance_GPU.wiki:22 "requesting more than one MIG instance in a job is not permitted" | OK (kit never requests more than one) |

Wiki inconsistencies recorded by H1 (H1 §8) and how the kit treats them:
* Fir 4 vs 2 H100 per node (Fir.wiki:100 table "4 x NVidia H100" vs :187 "2 NVidia H100 80GB
  accelerators"): clusters.yaml:137-139 records both; the kit never uses `gpus_per_node` (only
  per-GPU requests), so no request depends on it. README_ALLIANCE.md:27 states "4 x H100" without the
  caveat (documentation only; the bundle table, 12 cores and 280 GB per GPU on a 48-core 1125G node,
  supports 4).
* Trillium host names: both recorded (not silent).
* Trillium memory (188 GiB vs "192 GB", Trillium_Quickstart.wiki:343 vs :701): the kit never passes
  memory on Trillium; the chosen 188GiB is informational only.
* MIG profiles: Narval 4g.20gb excluded with a note; Fir uses the long names (the only ones on
  Fir.wiki:244-246), Nibi/Rorqual the short synonyms of their own pages. Not silent.
* Trillium GPU hardware is NOT only H100: Trillium.wiki:63-75 lists 63 H100 nodes, 1 H200 node and
  52 B200 nodes ("important: the B200s are not yet available"). clusters.yaml:363-365 records only
  the H100 row; the kit's unpinned request is F5.

## 2. setup_alliance.sh on a login node (item 2)

### 2.1 End-to-end simulation (what was actually run)

No Lmod or Alliance wheelhouse exists here, so the script was run unmodified in a fresh `git clone`
of HEAD (661762e; kit files identical to 69d2de0) with stand-ins on PATH: `module` (records calls,
`-t list` prints the three modules), `virtualenv` (`python3.11 -m venv`, `--no-download` dropped),
`avail_wheels` (exit 0), `python` -> Python 3.11.15; `PIP_FIND_LINKS` = a local wheelhouse of the 69
PyPI wheels that the kit's requirement list resolves to (every name has a Wheels3.11 row, section 1)
plus a stand-in `cupy-14.1.0` wheel whose import raises `ImportError: libcuda.so.1: cannot open
shared object file` (what a cupy linked to the driver does on a node without the NVIDIA driver).
`pip download abtem==1.0.10` went to the real PyPI.

| Run | Command | Result |
|---|---|---|
| 1 | `setup_alliance.sh fir` (PyPI blocked by my `env -i`, TLS bundle missing) | installs the whole wheelhouse (41 s), then `ERROR: pip download of abtem failed (no PyPI access from this login node?). Copy abtem-1.0.10-py3-none-any.whl here and rerun with --recreate --abtem-wheel PATH`, exit 2 |
| 2 | `setup_alliance.sh fir --recreate` (PyPI reachable) | wheelhouse reinstalled, abTEM downloaded, `abtem wheel SHA-256 verified: 34e098662a26...515d`, editable install OK (`--no-index --no-build-isolation` works with the setuptools>=68 of the list), `pip check`: `No broken requirements found.`, import check `reflection_holo 0.0.1 ... abtem 1.0.10`, `multislice engine: (True, 'available')`, then `ERROR: 'import cupy' failed on this login node ... rerun with --recreate --allow-cupy-import-failure`, exit 2 (45 s) |
| 3 | `setup_alliance.sh fir --recreate --allow-cupy-import-failure` | test subset `778 passed, 7 skipped, 2 deselected, 12 warnings in 115.55s`; `== DONE: environment fir-20260923T215230Z-f049afeca907 ready`; exit 0 (2 min 47 s). Records present (env.json, modules.sh, module_list.txt, pip_freeze.txt, package_sources.tsv, 3 pip reports, avail_wheels.txt, setup.log); `git status --porcelain` of the clone empty afterwards |

What this shows: the script's control flow, the pip invocations, the SHA-256 check, the editable
install without build isolation, `pip check`, the records and the test subset all work in a fresh
clone; failure modes stop loudly (exit 2, clear message) and a partial venv cannot be used (env.json is
written last; a rerun without `--recreate` refuses: `venv/ exists; rerun with --recreate`). What it
does not show: Lmod behaviour, the real wheelhouse resolution for cp311/StdEnv/2023 (versions will
be lower than PyPI's: e.g. numba 0.65.1, numpy 2.4.2, distributed 2026.7.1 which pins dask 2026.7.1;
all present in Wheels3.11), the real cupy wheel.

### 2.2 Findings in setup_alliance.sh

* The PyPI download of abTEM (setup_alliance.sh:149-160) and the `import cupy` gate
  (setup_alliance.sh:204-212) run AFTER the complete wheelhouse install, and both failure messages
  require `--recreate`, i.e. a full reinstall (runs 1 and 2 above: each failure cost a complete
  install before failing). See F3.
* The final gate is a pytest subset that includes `tests/hpc` (setup_alliance.sh:217-221). Those
  tests emulate Lmod with a `module` executable on PATH and rely on stripping `BASH_FUNC_*` from
  the environment (tests/hpc/fake_slurm.py:100-105); they do not strip `BASH_ENV`. See F1.
* bash-version safety: no `mapfile`, `${var@Q}`, associative arrays, `local -n`, `wait -n` in any
  kit script (grep, command 13). Every possibly empty array is expanded as `${A[@]+"${A[@]}"}`
  (submit.sh:95, job.sbatch:150, collect_results.sh:57, run_pipeline.slurm:128,143,148,157) or only
  after a non-empty check (collect_results.sh:62-64, 73-77). Verified with a real bash 4.2 (section 7).
  Alliance login and compute nodes run EL9 (Trillium: "Rocky Linux 9.6", Trillium_Quickstart.wiki),
  i.e. bash 5.1, so this is a margin, not a need.
* `set -euo pipefail` (setup_alliance.sh:29); the only pipe (setup_alliance.sh:137 `grep -v | sed`)
  cannot close early; `loaded()` avoids `| grep -q` (A3 M4) by matching in bash. The Lmod `module`
  function is called through `mod()` with `set +u` (setup_alliance.sh:80). No fallback: every step
  either succeeds or exits; the only tolerated failures are `avail_wheels` (recorded, and the
  following `pip install --no-index` is the real check) and `runtimeGetVersion()` (a NOTE), both
  deliberate and printed.
* `exec > >(tee -a "$LOG") 2>&1` (setup_alliance.sh:75) followed by `cp "$LOG" "$A/setup.log"`
  (setup_alliance.sh:251): the copy is taken while tee may still hold the last lines; the copy can
  lack the final `== DONE` lines (the original log in the repository root is complete). Cosmetic.

### 2.3 H3 open question: does `import abtem` (which imports cupy when installed) break CPU jobs?

Reproduced both realistic cases on this GPU-less, driver-less machine:
1. cupy installed but its import fails (stand-in wheel above): abtem/core/backend.py:17-26 catches
   the `ImportError` (`cp = None`), `import cupyx` fails the same way and `assert cp is None` holds.
   The setup import check, the whole test subset (run 3) and an emulated CPU null-study job on the
   setup-built venv (`--only tfix_bragg_abs0_L0`, numpy study copy, job status 0,
   `err_rad = 0.5685887531628921`) all work.
2. the REAL `cupy-cuda12x==14.1.0` from PyPI (no CUDA toolkit, no driver): `import cupy OK 14.1.0`;
   `getDeviceCount: CUDARuntimeError cudaErrorInsufficientDriver`; `runtimeGetVersion` 12090;
   `import abtem OK 1.0.10 abtem sees cupy: True 2.7 s` (abTEM then imports cupyx, builds its
   ElementwiseKernels and numba.cuda dispatchers without touching a device); Kirkland lookup works;
   the same CPU study point run with this venv gives `err_rad 0.5685887531628921, amp_ratio
   0.9510072597201454`, identical to case 1.
Answer: no, a CPU-only job is not broken by an installed cupy, whether cupy imports or fails cleanly,
with or without a driver (the CUDA module was not loadable here: NOT RUN with `module load
cuda/12.6`). Only a cupy that imports while `cupyx.scipy.ndimage` fails would break `import abtem`
(AssertionError at abtem/core/backend.py:37-40); setup's import check would show that on the login
node. It also means the likely outcome on Alliance login nodes is that `import cupy` SUCCEEDS
without a driver (PyPI build of 14.1.0), so the `--allow-cupy-import-failure` detour of F3 may not
even be needed; the Alliance-built wheel was not available to confirm (NOT RUN).

## 3. submit.sh, kit.py, job.sbatch, run_pipeline.slurm (item 3)

Checked by reading every line and by emulated runs (fake `module`, fake `sbatch` that executes
job.sbatch, tests/hpc/fake_slurm.py), including on the setup-built fresh clone of section 2.1.

| Check | Where | Result |
|---|---|---|
| No default account | kit.py:204-212 (`--account is required (no default)`), job.sbatch:23-26, no `#SBATCH` line in job.sbatch | OK (bash 4.2 run: `REFUSED: --account is required`, exit 2) |
| No default time | kit.py:215-230 | OK; limits from clusters.yaml. Nibi has no stated test minimum, so `--time 01:00` (Slurm minutes:seconds = 1 min) is accepted with only a warning (F7) |
| GPU syntax per cluster, model always named on Fir/Nibi/Rorqual/Narval | kit.py:319-351 + clusters.yaml | OK (section 1); Trillium unpinned (F5) |
| CPU/memory per GPU | kit.py:331-349 | OK: recommended values unless `--cpus/--mem`; above-recommended cores warn; Trillium refuses `--cpus/--mem` |
| MIG | kit.py:320-328 | OK: one instance, names per cluster, `--need-gpu-mem-gb` refusal |
| `--array=0-16` and index -> point | kit.py:295-306, 450-460; job.sbatch:161 | OK. Emulated task 3 on the setup-built clone ran `tfix_bragg_abs05_L0` (study.yaml:17, the 4th point: 0-based, no off-by-one); range derived from the study file length (17). The mapping is re-read from the study file when each task starts (F6) |
| Outputs under $SCRATCH, job-id stamped | kit.py:407-412; job.sbatch:30-38 | OK (`runs/<job>_<jobid>_<UTC>/`, arrays `runs/<job>_<arrayjob>/task<NNN>_<jobid>_<UTC>/`; `mkdir` without `-p` refuses reuse) |
| Threads | job.sbatch:95-103 | OK: threads = the run's declared threads, refused if > allocated cpus; Trillium uses `SLURM_CPUS_ON_NODE` (emulated Trillium gpu-check: `threads: 24 (declared by the run) of 24 allocated cpus`) |
| Module reload identical to setup | job.sbatch:70-80 + kit.py:463-481 | OK: `module purge` + modules.sh, set compared with setup's `module -t list`, exit 7 on difference. Not verified against real Lmod (sticky modules, hidden modules): NOT RUN |
| git state before computing | job.sbatch:106-111 (and run_pipeline.slurm:69-80 for pipeline jobs) | OK |
| `--dry-run` never submits or creates | submit.sh:103-108 (exit before `command -v sbatch` and `mkdir`) | OK (tests + my runs) |
| Paths with spaces | kit.py:118-125 `_safe` | refused before submission with a clear message (`run root ... contains a character the kit cannot pass through sbatch --export`), exit 2. Acceptable |
| Exit codes | submit.sh:118 (sbatch status), job.sbatch:189 (run status), finish trap preserves `$?` | OK; emulated gpu-check without GPU: job status 4, `job_status.txt` `exit_status 4` |
| A3/A3b fixes in run_pipeline.slurm | diff 1d87c45 | not regressed: dry-run still written to a file then `head` (run_pipeline.slurm:146-151); new `PART` array expanded as `${PART[@]+"${PART[@]}"}` (:128); git check in both modes (:69-80); ACCOUNT/PARTITION/TIME_LIMIT/GPU still required (`RH_PARTITION=none` must be given explicitly; the placeholder refusal test still passes). `RH_WORKDIR=` exported empty in submission mode falls back to the repository (`${RH_WORKDIR:-$REPO}`, :49): unchanged behaviour |

### 3.1 The gpu-check PASS gate (where, stale, foreign, per cluster)

* Written by gpu_check.py:228-234 only when every comparison passed, to
  `<run root>/gpu_check/PASS_<cluster>_<env id>_<jobid>.json`, opened with mode "x".
* Read by kit.py:387-399 at submission: any file matching `PASS_<cluster>_<env id>_*.json` under
  the run root unlocks GPU jobs. The env id (setup_alliance.sh:233-234) is
  `<cluster>-<setup UTC stamp>-<pip-freeze hash>`, so a PASS from another cluster, another clone or
  an earlier setup (a `--recreate`) does not match: per cluster and per environment. The content of
  the file is not read (an empty `{}` with the right name unlocks; tests use exactly that), which is
  acceptable for a self-protection gate.
* Two gaps (both MINOR, F9): (a) the gate is checked only at submission; job.sbatch never compares
  `RH_ENV_ID` with the env.json present when the job starts (RH_ENV_ID is used only at
  job.sbatch:135), so a GPU job queued against environment A runs on environment B if Ali reruns
  setup with `--recreate` while it waits (for example to try `--cuda-module cuda/12.9` after a FAIL
  on another job); (b) the PASS is not tied to the code: a `git pull` that changes the engine keeps
  the old PASS valid (the commit is recorded in the PASS file but never compared).
* A requeued gpu-check (same Slurm job id) would crash with FileExistsError at the "x" open after
  passing every comparison (gpu_check.py:231), reporting exit 1 although the first PASS stands. Rare.

### 3.2 Submission records

`RECORD=$RUN_ROOT/submissions/${STAMP}_${CLUSTER}_${JOB}.json` has one-second resolution
(submit.sh:87-88) and is overwritten with `cp` (submit.sh:111). Reproduced: two `submit.sh rorqual
smoke` started together with `--mem 2G` and `--mem 3G` (fake sbatch, record mode) produced jobs
900001 and 900101 but ONE record, `20260923T215949Z_rorqual_smoke.json`, containing `mem 2G`; both
jobs' `RH_SUBMISSION_RECORD` point to it, so the 3G job's submission.json is wrong and one
`.sbatch_output` is lost (F8, MINOR; only when submissions are started in parallel, e.g. a loop with
`&`).

### 3.3 Will `pip install --no-index` resolve in the wheelhouse? (approximation)

A greedy resolution of the kit's 20 requirements against the Wheels3.11 table (newest listed
version that satisfies every constraint; dependency lists from PyPI JSON of that exact version;
markers evaluated for CPython 3.11 / Linux x86_64; command 16) closes after 5 iterations with 71
distributions, no missing name and no unsatisfiable constraint: numpy 2.4.2, numba 0.65.1 (numpy<2.5)
with llvmlite 0.47.0, dask 2026.7.1 = distributed 2026.7.1 (distributed pins dask; the table's dask
2026.8.0 has no matching distributed), zarr 3.3.0, pandas 3.0.5, matplotlib 3.11.1, ipympl 0.9.8,
cupy 14.1.0 with cuda-pathfinder 1.8.2, setuptools 84.0.0. Limits: the table does not say which
wheels exist for StdEnv/2023 and each CPU architecture, and Alliance may edit wheel metadata; `pip`
on the login node is the real test (it fails loudly, section 2.1).

## 4. gpu_check.py (item 4)

* Tolerances are module constants with a derivation or a measurement written next to them
  (gpu_check.py:35-49) and recorded in gpu_check.json; they cannot be passed on the command line.
  1e-10 (FFT complex128), 1e-4 (FFT complex64), 1e-9 (multislice complex128 vs numpy complex128),
  1e-3 (multislice complex64 vs numpy complex128, about 11 x the measured numpy complex64 deviation
  9.2e-5). For complex64, 1e-3 relative to max|psi| is ten times below the null study's own
  convergence criterion (|err_rad| <= 1e-2, scripts/hpc/null_test_study/README.md). Sensible.
* It exercises the engine's cupy path, not only cupy.fft: `run_case` (gpu_check.py:130-140) calls
  `run_realisation` with `backend="cupy"`, which builds `Backend("cupy", cp, ...)`
  (reflection_holo/forward/multislice/backend.py:65-68, no fallback) and runs the slice loop, the
  band-limit masks, the atomistic projected potential (cupy exp, complex GEMM `Ex @ Ey.T`, ifft2;
  potentials.py:289-309) and `cupy.asnumpy` at the end (engine.py:200). The atomistic case is
  640 x 120 x 1434 slices with 39,872 atoms (both FFT axes non-trivial; the rung-1 case is 2550 x 1).
* Would a wrong result fail it? Checked by feeding the same code a numpy-impersonating `cupy`
  (the fixture of tests/hpc) whose `fft2` is wrong (command 19):
  * phase error 1e-8 rad per FFT: FFT complex128 `1e-08 FAIL`; multislice complex128 `2.06e-05 FAIL`,
    complex64 `2.50e-05 PASS`: overall FAIL (every comparison must pass, gpu_check.py:206-208);
  * 1e-5 rad per FFT: multislice complex128 and complex64 `2.06e-02 FAIL`;
  * conjugated FFT (sign convention error): every comparison `~1.0 FAIL`.
  The complex128 comparison is the sensitive one; a defect confined to single precision at the
  1e-4 level would pass, which the 1e-2 rad study criterion tolerates.
* What it cannot show: speed (the GPU_ASSUMED model stays unverified; gpu-check prints timings but
  does not compare them with the model), memory headroom of large cases, MIG-specific behaviour
  beyond the instance it ran on (a PASS from any instance unlocks every instance of that
  environment).

## 5. collect_results.sh (item 5)

Reproduction (command 20): run root with a 30 MB `summary.json`, a 20 MB Slurm log, a 5 MB
`arrays.npz` and an unknown-extension file, `--max-array-mb 0`:
```
packed 3 files into .../reflholo_results_vm_20260923T220218Z.tar.gz (22724465 bytes)
checksum: ....tar.gz.sha256; skipped arrays: 1
tar -tv: 20000000 logs/smoke_111.log / 30000000 runs/.../pipeline/summary.json / 3 .../summary_trench.json
sha256sum -c: reflholo_results_vm_20260923T220218Z.tar.gz: OK
```
* The array cap is honoured per file for `*.npz|*.npy|*.h5|*.hdf5` (collect_results.sh:95-98) and
  over-cap arrays are listed with their size; checksums inside (MANIFEST.sha256) and next to the
  tarball verify; failed runs are collected like the others (it only lists files).
* Not capped: every `*.json|*.csv|*.tsv|*.txt|*.log|*.png|*.yaml|*.md` is packed whatever its size
  (collect_results.sh:99-100), and there is no total cap: `--max-array-mb 0` still produced a 22.7 MB
  tarball here. Files with any other extension are dropped silently (not in SKIPPED_ARRAYS.tsv,
  not counted in COLLECT_INFO.txt). None of our runs writes such files today (pipeline: json, npz,
  png, txt; torus: json, npz; study and gpu-check: json), so this is MINOR (F10).
* `--max-array-mb` accepts `.` or `1.2.3` (collect_results.sh:40 only rejects characters outside
  `0-9.`); awk turns them into 0 or 1.2. Cosmetic.

## 6. README_ALLIANCE.md (item 6)

* Commands: every `submit.sh`/`setup_alliance.sh`/`collect_results.sh` line in §3-§6 parses with
  the scripts' option parsers (dry-runs in tests and in my runs). The clone URL matches `git remote
  -v` (`https://github.com/alihasuna/Holography`) and the local tracking ref shows the kit commit on
  `origin/claude/electron-holography-orchestration-nakd7r` (not re-fetched: NOT RUN).
* Runtimes: the 17 lines in §4.5 are the estimator's own output format (run_study.py:121-126); the
  sums quoted (6588 s CPU with the x1.5 factor, 114.7 s ~ "115 s" GPU, 340 MB largest) are exact
  sums of those lines (checked by hand). GPU times are labelled "GPU_ASSUMPTION model, not
  measured" in §4.3 and §4.5, and the smoke/demo CPU times are labelled as build-machine
  measurements. The one unlabelled duration is submit.sh:7 "gpu-check   2-minute GPU proof" (never
  run on a GPU; MINOR, F12).
* Validation status: §"What the results mean" states the multislice engine is UNVALIDATED, that
  `NO HEIGHT` from demo-gpu is the correct outcome, that torus and null-study outputs are UNVALIDATED
  engine outputs, and that only the geometric smoke heights are trustworthy within B4. Nothing in the
  README presents a multislice step phase as a result. OK.
* §4.6 tells Ali to run `venv/bin/python -m reflection_holo.pipeline dry-run --config <H2 config>`
  on the LOGIN node "for memory and GPU estimate": see F2 (measured 3.6 GB peak RSS for the 1.44 M-atom
  demo; H2's production cells are 31-93 M atoms).
* §4.5 makes the 17-task array the default and mentions `--serial` as an alternative: see F4.
* §6 `sha256sum -c` on "your laptop": macOS has no `sha256sum` by default (`shasum -a 256 -c`).
  MINOR (F12).
* §0 states "Fir (4 x H100 80 GB per GPU node)" without the wiki's contradictory "2" (harmless: no
  request depends on it).

## 7. tests/hpc (item 7)

Runs: baseline `73 passed, 5 skipped` (1 min 45 s, command 5); the same suite with a real GNU bash
4.2.0 first on PATH `73 passed, 5 skipped in 102.76s` (command 14); ShellCheck 0.11.0 on the five
scripts: exit 0 each (command 15; `-o all` adds only style notes and SC2154 for the RH_* variables
that job.sbatch:23-26 checks); explicit bash 4.2 runs of submit.sh and collect_results.sh behave
(command 14b; control: an unguarded `"${A[@]}"` under `set -u` fails in 4.2 with `A[@]: unbound
variable`, the kit never uses that form).

What the tests do and do not establish:
* They test real behaviour, not only strings, in: refusals (account, time, limits, MIG, CPU jobs on
  Trillium, module mismatch at submission), the emulated smoke job end to end through
  run_pipeline.slurm, one null-study array task (index 0), gpu-check without GPU (exit 4, no PASS),
  collect_results (inclusion, cap, `sha256sum -c`).
* Not hermetic against the login node's shell: they emulate Lmod with a `module` executable on PATH
  and strip `BASH_FUNC_*`, but not `BASH_ENV` (F1). Reproduced with `BASH_ENV` naming a file that
  defines a `module` function: `8 failed, 70 deselected in 0.77s` (every fir dry-run case,
  test_setup_refuses_without_module_command, test_emulated_smoke_job_end_to_end), e.g.
  `REFUSED: loaded modules differ from the setup record ... only in this job : ['CCconf...`.
  Because setup_alliance.sh runs tests/hpc as its last gate, the same failure would stop the setup.
* Blind spots (a broken kit would still pass):
  * the numpy-impersonating cupy cannot reveal host/device mixing (a `np.asarray(<cupy array>)`
    raises on real cupy but not on the stand-in); I found no such mixing in gpu_check.py or the
    engine by reading (engine.py:200 `be.to_numpy`, gpu_check.py:101-102 `cp.asnumpy`);
  * the fake sbatch accepts any option string, so a misspelt Slurm option is caught only where a
    test hard-codes the expected flag (GPU flags, cpus, mem, output, chdir, array are hard-coded;
    `--job-name` and the `--export` grammar are not);
  * the job-side module comparison (job.sbatch:79-80, exit 7) has no refusal test (only the
    submission-side one is tested); neutering it would leave every test green;
  * no emulated job runs the Trillium branch (job.sbatch:96-98); I ran it (section 3: `threads: 24
    ... of 24 allocated cpus`);
  * `test_profiles_agree_with_h1_table` compares clusters.yaml with H1's TSV, which has the same
    origin; section 1 of this report checks the wiki directly;
  * setup_alliance.sh is tested only on its refusal paths; section 2.1 is the first run of its body.

## 8. H3's open questions (item 8)

1. `import abtem` with cupy installed on a CPU-only node: does NOT break the job (section 2.3,
   reproduced with a failing cupy and with the real cupy-cuda12x 14.1.0 without a driver; identical
   study result `err_rad 0.5685887531628921`). Not reproduced: with `module load cuda/12.6` (no Lmod
   here).
2. The torus runner's 600 s guard (scripts/torus/run_torus_multislice.py:77, 207-223): the estimate
   is calibrated on the node with the run's 4 threads and multiplied by 1.5. T1 measured 163-213 s
   on a shared 4-CPU machine (T1 report table: simulate 187.6-207.3 s); H3's 502-865 s were under
   heavy load from other agents. On a Slurm allocation the 4 cores are dedicated, so a refusal needs
   a per-core FFT/elementwise throughput about 3 x below this VM's: unlikely, and cheap if it
   happens (exit 2 after about 20 s, message in the log). Keep the guard; if it trips, the fix is a
   documented override in the T1 runner, not a kit change. Not measured on a cluster (NOT RUN).
3. Array vs `--serial` for the 17-point study: `--serial` is the better default. Job_arrays.wiki:45:
   "You should not use a job array to submit tasks with very short run times, e.g. much less than an
   hour. Tasks with run times of only a few minutes should be grouped into longer jobs". Per point
   the GPU_ASSUMED model gives 0.3-26 s (sum 114.7 s); each array task would wait in the queue for a
   whole H100 with 12-16 cores and 124-280 GB, re-import abTEM and recompile kernels, for seconds of
   GPU work. `--serial --time 01:00:00` leaves about 30 x margin over the assumed GPU time (the cell
   builds are fast: the estimate of all 17 points, which builds every cell, took 26 s). Keep the
   README's order: `--only tfix_bragg_abs0_L0` first (compare with +0.569 rad; my CPU run gives
   0.5686), then `--serial`. Caveat: run_study.py has no per-point isolation, so one exception ends
   the serial job (earlier results stay on disk; job.sbatch reports status 5 or the Python status).

## 9. Findings, ranked

### F1. BLOCKER (conditional on the login node's shell): setup's last gate runs tests/hpc, which are not hermetic
* Where: setup_alliance.sh:216-221 (test subset includes `tests/hpc`, `set -e`), which precede the
  records (setup_alliance.sh:223-252, env.json written last); tests/hpc/fake_slurm.py:100-105
  (`clean_environ` strips `BASH_FUNC_*` but keeps `BASH_ENV`); tests/hpc/fake_slurm.py:78-85 (the
  fake `module`/`sbatch` are executables created under pytest's temporary directory).
* What is wrong: the kit's own emulation tests become a pass/fail condition of the ENVIRONMENT
  build on the cluster, yet their outcome depends on two properties of the login node that have
  nothing to do with the environment: (a) if `BASH_ENV` names a file that defines Lmod's `module`
  function (Lmod's stock profile exports `BASH_ENV=<lmod>/init/bash`; whether Alliance's profile
  does is NOT_FOUND on the wiki), every child `bash` uses real Lmod instead of the fake, the module
  lists differ and the tests fail; (b) if pytest's temporary directory is mounted `noexec`, the
  fakes cannot run and the tests fail.
* Reproduction (command 17): `BASH_ENV=<file defining module()> venv/bin/python -m pytest tests/hpc
  -k "...fir... or test_setup_refuses_without_module_command or test_emulated_smoke_job_end_to_end"`
  -> `8 failed, 70 deselected in 0.77s`, message `REFUSED: loaded modules differ from the setup
  record ... only in this job : ['CCconf...`. Command 22: the same tests with
  `--basetemp` on a `tmpfs -o noexec` mount -> `7 failed, 1 passed`, message `.../env/modules.sh:
  line 1: .../bin/module: Permission denied ... could not be loaded as recorded`.
* Why it matters tonight: setup then exits non-zero after the complete install, before
  `venv/alliance/env.json` exists, so `submit.sh` refuses every job ("env.json not found") on that
  cluster, and there is no option to skip the gate. The environment itself would be fine.
* Check before running setup (10 s): `echo "BASH_ENV=[$BASH_ENV]"; findmnt -no OPTIONS --target
  "${TMPDIR:-/tmp}"`. Workarounds without code change: if BASH_ENV is set and `env -u BASH_ENV bash
  -c 'type module'` still finds module, run `env -u BASH_ENV bash scripts/hpc/alliance/setup_alliance.sh
  <cluster>`; if the temporary directory is noexec, `mkdir -p $HOME/tmp && TMPDIR=$HOME/tmp bash
  scripts/hpc/alliance/setup_alliance.sh <cluster>`.
* Fix: drop `tests/hpc` from the setup subset (they test the kit, not the environment; H3 already
  ran them), or make them hermetic (`clean_environ` also removes `BASH_ENV` and `ENV`; create the
  fakes in a directory checked for exec, or call them through `bash <file>`), and write env.json
  before a non-essential test step.

### F2. MAJOR: README §4.6 sends production-size structure builds to the login node; the kit's memory hint for CPU pipeline jobs under-requests by ~30x
* Where: README_ALLIANCE.md:260 (`venv/bin/python -m reflection_holo.pipeline dry-run --config
  <H2 config>     # login node: memory and GPU estimate`); kit.py:54 (hint printed when `--mem` is
  missing for a CPU pipeline job: "take the memory from `python -m reflection_holo.pipeline dry-run
  --config ...`").
* Reproduction (command 18): `dry-run --config configs/demo_hpc_si001.yaml` here: `EXIT 4 wall 52.4 s
  peak RSS 3629 MB`, while the dry-run prints `memory per realisation ~126.6 MiB` (engine arrays
  only). The dry-run builds the full structure (1.44 M atoms). H2's production cells are 31 M to
  93 M atoms (H2_realistic_supercell_sizing.md:427-443); at the measured ~2.5 kB/atom that is roughly
  78-235 GB and 20-60 min on a login node. Trillium_Quickstart.wiki:172-173: lightweight login-node
  tests "Use no more than 1–2 GB of memory"; even the demo exceeds that. For a cupy configuration
  the dry-run also exits 4 on a GPU-less login node (after printing the estimate), which the README
  does not say.
* Why it matters: the documented command can be killed on the login node or draw a policy warning,
  and a CPU pipeline job sized from the printed "memory per realisation" is OOM-killed (126.6 MiB
  printed vs 3.6 GB needed for the demo).
* Fix: README: run the dry-run inside a short job (or `salloc`), not on the login node; say it exits 4
  without a GPU; kit.py:54: tell the user that the dry-run's number is engine arrays only and that the
  structure build dominates host memory (quote a measured peak RSS per atom), or measure it in the
  job. Sizing H2's 10^7-10^8-atom cells is outside the kit (H2 N9 already says the builders cannot).

### F3. MINOR: setup fails late, and each late failure costs a full reinstall
* Where: setup_alliance.sh:146 (full wheelhouse install) precedes :149-160 (abTEM download) and
  :204-212 (`import cupy` gate); both messages require `--recreate` (setup_alliance.sh:69-72
  deletes the whole venv).
* Reproduction: section 2.1 runs 1 and 2 (each failed after the complete install, 41-45 s here;
  minutes on a login node).
* Fix: download/verify the abTEM wheel and check PyPI reachability first; install cupy first and test
  its import before the rest; allow resuming (skip installed steps) instead of `--recreate`. My
  PyPI cupy 14.1.0 imports without a driver (section 2.3), so the cupy branch may never trigger.

### F4. MINOR: the null study defaults to a 17-task array against the wiki's advice
* Where: kit.py:292-304 (array mode unless `--only`/`--serial`); README_ALLIANCE.md:215-223.
* Wiki: Job_arrays.wiki:45 "You should not use a job array to submit tasks with very short run
  times, e.g. much less than an hour." Per point 0.3-26 s of GPU_ASSUMED time; each task holds a full
  H100 with 12-16 cores and 124-280 GB. The kit prints a warning but keeps the array default.
* Fix: make `--serial` the default for the study (array on request), `--time 01:00:00`; keep
  `--only <first point>` first (section 8, item 3).

### F5. MINOR: Trillium GPU jobs name no GPU model while Trillium has H100, H200 and (soon) B200 nodes
* Where: clusters.yaml:376-380 (`--nodes=1`, `--gpus-per-node=1`), :363-365 (only the H100 row).
* Wiki: Trillium.wiki:63-75 (63 H100 nodes, 1 H200 node, 52 B200 nodes "not yet available");
  Using_GPUs_with_Slurm.wiki (after the table): "If you do not supply a model specifier your job may
  be rejected or it may be sent to an arbitrary GPU instance ... we strongly recommend that you always
  provide a specific GPU model specifier"; the same page lists `h100` for Trillium. The Trillium
  examples themselves use no model, so the kit follows the site page; the risk is that a PASS earned
  on an H100 unlocks jobs that land on the H200 node today or on B200 (Blackwell) nodes once they
  open, with `cuda/12.6` and an unverified cupy build.
* Fix: request `--gpus-per-node=h100:1` on Trillium after checking `sinfo -o "%G"` on trig-login01
  (the wiki's own command), or record the GPU name in the PASS and compare it in the job.

### F6. MINOR: array tasks read the study file when they start
* Where: job.sbatch:159-161 (`kit.py study-point --study "$STUDY" --index $SLURM_ARRAY_TASK_ID`).
* Wiki: Job_arrays.wiki:85 "The file case_list should not be changed until all the tasks in the array
  have run, since it will be read each time a new task starts." A `git pull` or an edit of study.yaml
  while tasks wait shifts the index -> point mapping silently (the submission commit is only compared
  with a warning, job.sbatch:108-110). Mapping itself is correct (task 3 -> `tfix_bragg_abs05_L0`).
* Fix: copy the study file into the run root at submission and pass that copy (with its hash).

### F7. MINOR: `--time 01:00` on Nibi is accepted as one minute
* Where: kit.py:93 (`MM:SS`, correct Slurm reading), kit.py:222-230 (Nibi has no test minimum, so
  only the production warning fires).
* Reproduction (command 21a): `submit.sh nibi smoke ... --time 01:00 --dry-run` -> exit 0,
  `--time=01:00`, warning only. A user meaning one hour gets a job killed after 60 s.
* Fix: refuse (or require `--force`) below the smallest stated test minimum of the other clusters
  (5 min) when the cluster's own minimum is NOT_FOUND, and echo the parsed duration.

### F8. MINOR: parallel submissions overwrite each other's submission record
* Where: submit.sh:87-88, 111, 117.
* Reproduction (command 21b): two concurrent `submit.sh rorqual smoke` (`--mem 2G`, `--mem 3G`) ->
  jobs 900001 and 900101, ONE record `20260923T215949Z_rorqual_smoke.json` with `mem 2G`.
* Fix: include the PID or `mktemp` in the record name (or write it after sbatch with the job id).

### F9. MINOR: the gpu-check gate is checked only at submission and is not tied to the code
* Where: kit.py:387-399 (gate), job.sbatch:135 (the only use of RH_ENV_ID), gpu_check.py:230-233
  (commit recorded, never compared).
* Effect: a GPU job queued before a `setup --recreate` runs on the new, unchecked environment; an
  engine change pulled after the PASS keeps the gate open.
* Fix: job.sbatch compares `RH_ENV_ID` with env.json and refuses on difference; kit.py requires the
  PASS commit to equal HEAD for engine files (or warns).

### F10. MINOR: collect_results caps arrays only, has no total cap, and drops unknown extensions silently
* Where: collect_results.sh:94-101. Reproduction and effect in section 5 (30 MB json and 20 MB log
  packed with `--max-array-mb 0`; a `.bin` dropped without a record).
* Fix: apply the cap to every file (or a separate `--max-file-mb`), add `--max-total-mb`, and list
  every skipped file in SKIPPED_FILES.tsv.

### F11. MINOR: the torus 600 s guard is marginal; the README's reassurance is not supported
* Where: README_ALLIANCE.md:201-203 ("On a Slurm allocation the 4 cores are yours, so the
  calibration should be closer to T1's (213 s and 163 s)"); guard in
  scripts/torus/run_torus_multislice.py:77, 217.
* Measurement (command 23; this VM, 4 threads, shared with another agent's run, load 0.8-5.8):
  ridge estimates 557, 461, 763, 420 s; trench 265, 485, 515, 511 s (limit 600 s). T1 had 163/213 s.
  The calibration (6 FFT, 3 potential repetitions) is noisy and the ridge sits near the limit, so a
  refusal on a cluster node cannot be excluded. Cost if it trips: exit 2 after about 30 s.
* Fix (T1 runner, not the kit): an explicit, recorded override of the CPU limit for batch runs; README:
  state the spread instead of predicting a pass.

### F12. MINOR: documentation details
* submit.sh:7 "gpu-check   2-minute GPU proof": duration never measured (no GPU run).
* README_ALLIANCE.md:302 `sha256sum -c` on "your laptop": macOS needs `shasum -a 256 -c`.
* README_ALLIANCE.md:121-122: if gpu-check fails on a CUDA mismatch, the README suggests only
  `cuda/12.9`; the module table also has 13.2 and 13.3 (Modules_avx512.wiki:984). Better: load the
  module matching the "CUDA runtime" that setup and gpu-check already print.
* README_ALLIANCE.md:27 "Fir (4 x H100 ...)" without the wiki's "2" (harmless).

### F13. MINOR: small robustness items
* gpu_check.py:231 opens the PASS file with mode "x" under the Slurm job id: a requeued gpu-check
  that passes again raises FileExistsError and exits 1 (the first PASS remains valid).
* setup_alliance.sh:75,251: `cp "$LOG" venv/alliance/setup.log` while `tee` may still be writing;
  the copy can miss the last lines (the log in the repository root is complete).
* submit.sh:79: `git status --porcelain | wc -l` under `pipefail` inside `$(...)`: if `git status`
  failed after `rev-parse` succeeded, submit.sh would exit silently (no message). Unlikely.

