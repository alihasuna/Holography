# Running the reflection-holography jobs on the Alliance clusters (tonight's checklist)

You run everything yourself: no agent logs in anywhere (the Alliance automation nodes "are not
suitable for usage of AI agents", Automation_in_the_context_of_multifactor_authentication). Every
cluster fact below comes from the Alliance wiki as retrieved on 2026-09-23 (agent H1,
`docs/agent_reports/H1_alliance_wiki.md`); locators are written `Page § Section` on
https://docs.alliancecan.ca/wiki/. The cluster values the scripts use are in `clusters.yaml`, each
with its locator; what the wiki does not state is marked NOT_FOUND and never invented.

What the results mean, before you start:

* Everything is a DEMO: `purpose: demo; not comparable to experiment`. The laboratory inputs you have
  not supplied are registered ASSUMPTION stand-ins (docs/model_assumptions.md; `list-inputs` shows
  them). The beam energy is 200 keV.
* The **multislice engine is UNVALIDATED** for atomistic reflection (docs/05 4.4 rung 2 and the abTEM
  cross-check NOT RUN). `demo-gpu` printing `NO HEIGHT: no-step control failed or not performed` is
  the **correct** outcome (README_HPC.md §4; the control failed on CPU in P1's run too). The torus
  and null-study outputs are UNVALIDATED engine outputs as well.
* The **geometric engine** (the `smoke` job) is the one whose heights are trustworthy within its model
  scope (B4): the smoke demo prints `h = +2.7156 +- 0.0165 A` (built a/2 = 2.7155 A).
* The cupy (GPU) path of the engine has **never been executed**. `gpu-check` is therefore the first
  job on every cluster, then `gpu-sanity`; `submit.sh` refuses the other GPU jobs until a gpu-check
  PASS is recorded for that cluster, that environment and the engine code as it is now (a `git
  pull` that changes `reflection_holo/forward/multislice/` needs a new gpu-check), and every GPU job
  checks this again when it starts (override: `--skip-gpu-check-gate`, not recommended).

## 0. Where to run

In production (National_systems § List of compute clusters): Fir (4 x H100 80 GB per GPU node in
the node table; the same page's GPU-node layout says 2: no request of the kit depends on it),
Nibi (8 x H100 80 GB), Rorqual (4 x H100 80 GB), Narval (4 x A100 40 GB), Trillium (4 x H100 80 GB;
24 h maximum; one GPU or whole nodes; CPU jobs take whole 192-core nodes). Cedar is retired
(Infrastructure_renewal). The kit refuses its two CPU jobs (`smoke`, `torus`) on Trillium: run them
on Fir, Nibi, Rorqual or Narval. Compute nodes of Rorqual, Narval and Trillium have no internet
(none of our jobs needs it; setup runs on a login node).

## 1. Prerequisites (once, from your laptop/browser)

1. CCDB account and your RAP name: CCDB "My Projects -> My Resources and Allocations", the "Group
   Name" (Running_jobs § Accounts and projects). It starts with `def-` (default allocation) or
   `rrg-`/`rpp-` (RAC) (Job_scheduling_policies § Priority and fair-share). A RAC is bound to one
   cluster (Trillium_Quickstart § Submitting jobs to the scheduler). **The scripts need it on every
   submission (`--account`); there is no default.** If you exported `SBATCH_ACCOUNT` in `~/.bashrc`,
   note that the kit's command-line `--account` overrides it (Running_jobs § Accounts and projects).
2. Request access to each cluster: https://ccdb.alliancecan.ca/me/access_systems (SSH § What you
   need). "It can take up to one hour" (Fir § Access, Rorqual/en § Access); Rorqual also asks you to
   accept three Calcul Quebec agreements (Rorqual/en § Access).
3. SSH key: upload the public key at https://ccdb.alliancecan.ca/ssh_authorized_keys (SSH_Keys §
   Using CCDB); propagation "can take up to approximately 30 minutes". Trillium accepts only keys
   (Trillium § Logging in).
4. Multifactor authentication is mandatory (Multifactor_authentication § FAQ): register Duo Mobile
   or a YubiKey, ideally two factors (§ Registering factors).
5. Copy the Host blocks of `scripts/hpc/alliance/ssh_config.example` into `~/.ssh/config` on your
   laptop, replace `USERNAME` and the key path. The ControlMaster lines (verbatim from
   Multifactor_authentication § Configuring your SSH client with ControlMaster) let later ssh/scp
   connections reuse the first authenticated one for up to 10 minutes.

## 2. Log in and clone (per cluster)

```bash
ssh fir                       # or nibi, rorqual, narval, trillium-gpu (Trillium: GPU login node)
cd $HOME
git clone --branch claude/electron-holography-orchestration-nakd7r \
    https://github.com/alihasuna/Holography.git Holography
cd Holography && git log -1 --oneline
```

On Trillium do everything (clone, setup, submit) on the GPU login node `trillium-gpu`: the login
nodes "have the same architecture, operating system, and software stack as the CPU and GPU compute
nodes, respectively", and GPU jobs "must be submitted from the GPU login node"
(Trillium_Quickstart § Logging in, § Submitting jobs to the scheduler); submit.sh warns if the host
is not `trig-login01`.

If the GitHub repository is private, git asks for credentials: use a GitHub personal access token as
the password, or make a bundle on your laptop (`git bundle create holo.bundle --all`, `scp
holo.bundle fir:`) and `git clone --branch claude/electron-holography-orchestration-nakd7r
holo.bundle Holography`. Keep `.git`: every job refuses to compute without it (audit A3 M5).

Why `$HOME` (not `$SCRATCH`, not `$PROJECT`): the virtual environment lives inside the clone
(`venv/`), and the wiki says "Do not create your virtual environment under $SCRATCH as it may get
partially deleted" (Python § Creating and using a virtual environment; scratch is purged after 60
days on Fir, Narval, Rorqual: Storage_and_file_management). `$HOME` is backed up, per user, mounted
on the compute nodes (read-only on Trillium, which is fine: jobs only read the clone) and large
enough (50 GB and 500K files; Trillium 100 GB; our clone is about 30 MB and the local venv here
about 0.8 GB and 26,000 files before cupy). `$PROJECT` would also work (the Python page allows it),
but it is shared by your group and on Nibi "user directories are no longer created by default"
(Nibi § /project and /nearline spaces). All outputs go to `$SCRATCH` (below).

## 3. Set up the environment (once per cluster, on the login node; duration NOT measured)

```bash
bash scripts/hpc/alliance/setup_alliance.sh fir        # the cluster you are on
```

If it stops, fix the cause and run the SAME command again: every install step leaves a stamp in
`venv/alliance/steps/`, and completed steps are skipped (no reinstall). `--recreate` deletes `venv/`
and starts from scratch (needed only if you change `--python-module` or `--cupy-spec`, or if venv
creation itself was interrupted). Run on a complete environment, the script says so and exits 0.

It loads `StdEnv/2023`, `python/3.11.5`, `cuda/12.6` (the combination of the wiki's own GPU job
example, Trillium_Quickstart § Example: Single-GPU Job; Python 3.11 because pyproject.toml needs
>= 3.11 and the 3.11 wheelhouse has cupy 14.1.0, pyfftw and every abTEM requirement), creates
`venv/` with `virtualenv --no-download`, installs everything with `pip install --no-index` from the
Alliance wheelhouse, downloads abTEM 1.0.10 (not in the wheelhouse) with `pip download --no-deps` on
the login node (Python § Pre-downloading packages), checks its SHA-256 against PyPI, installs this
package, imports everything and runs a short CPU check of the INSTALLED physics (52 tests: the
200 keV wavelength and constants, tiny multislice runs on numpy, the Kirkland potential through
abTEM, the geometric smoke pipeline, the provenance manifest; 74 s here on 4 threads of a shared
machine, with a cupy that imports and without). The kit's own tests (`tests/hpc`, fake Slurm and
Lmod) are not part of it: they test the kit, not your environment. abTEM is downloaded BEFORE the
long wheelhouse install, so a login node without PyPI access fails in seconds. It stops at the
first error (`avail_wheels` is only recorded: a failure there prints a WARNING, and the `pip install
--no-index` that follows is the check). Success ends with:

```
== DONE: environment fir-<UTC stamp>-<hash> ready in /home/<you>/Holography/venv (records in venv/alliance).
```

Records: `venv/alliance/modules.sh` (the module sequence every job repeats after `module purge`),
`module_list.txt` (every job compares its loaded modules with it and refuses on a difference),
`env.json` (written last; every job checks that its environment id is still the current one),
`pip_freeze.txt`, `package_sources.tsv` (which package came from the wheelhouse, which from PyPI),
`avail_wheels.txt`, `steps/`, and the setup logs `alliance_setup_<cluster>_<stamp>.log` (hard links
of the logs in the repository root).

If it fails:
* `No matching distribution found` for a wheel: the 3.11 wheelhouse of StdEnv/2023 lacks it (the
  wiki says new wheels target the 3 newest Pythons, Python § Python version supported). Rerun with
  `--recreate --python-module python/3.12.4` (Wheels3.12 also has cupy 14.1.0).
* `pip download` of abTEM fails (login node without PyPI access; the wiki does not state login-node
  internet explicitly): download `abtem-1.0.10-py3-none-any.whl` on your laptop, `scp` it over and
  rerun the same command with `--abtem-wheel <path>` (no `--recreate`).
* `import cupy` fails on the login node with an NVIDIA driver/libcuda message: login nodes may have
  no GPU driver. Rerun the same command with `--allow-cupy-import-failure` (no reinstall);
  gpu-check then decides. (The PyPI build of cupy 14.1.0 imports without a driver: H4 §2.3.)
* The CUDA version the wheelhouse cupy was built for is NOT stated on the wiki. Setup and gpu-check
  both print `CUDA runtime` as seen by cupy; if gpu-check fails on a CUDA mismatch, rerun setup with
  the `cuda/<x.y>` module matching that runtime (Modules_avx512 lists cuda 12.2, 12.6, 12.9, 13.2,
  13.3), e.g. `--cuda-module cuda/12.9`: without `--recreate` this makes new records and a new
  environment id without reinstalling (then gpu-check again).

## 4. Submit, in this order

All jobs go through `submit.sh <cluster> <job> --account <RAP> --time <limit> [options]`. Add
`--dry-run` first to see the exact `sbatch` command (nothing is submitted or created). There is no
default account and no default time limit; CPU jobs also need `--mem`. Times: `HH:MM:SS` or
`D-HH:MM:SS` (also `D-HH`, `D-HH:MM`; Running_jobs § Use sbatch to submit jobs). The kit REFUSES
`MM:SS` and bare minutes: `--time 01:00` is ONE MINUTE to Slurm, `--time 2` two minutes. The parsed
duration is printed (`NOTE: time limit 01:00:00 = 01:00:00 (60 min)`). Limits enforced from
clusters.yaml: at most 168 h (24 h on Trillium), at least 5 min on Fir/Narval/Rorqual (test jobs)
and 15 min on Trillium; below 60 min you get a warning ("production jobs should have a duration of
at least an hour", Running_jobs § Cluster particularities). Watch jobs with `squeue -u $USER`.

Replace `def-XXX` by your RAP. The resource requests the kit builds (per GPU, from
Allocations_and_compute_scheduling § Ratios in bundles, recommended values): Fir `--gpus=h100:1
--cpus-per-task=12 --mem=280G`; Nibi `--gpus=h100:1 --cpus-per-task=14 --mem=250G`; Rorqual
`--gpus=h100:1 --cpus-per-task=16 --mem=124G`; Narval `--gpus=a100:1 --cpus-per-task=12
--mem=124G`; Trillium `--nodes=1 --gpus-per-node=h100:1` (24 cores and 188 GiB come with the GPU;
`--mem` is ignored there, Trillium_Quickstart § Memory requests are ignored). No partition is ever
given (Running_jobs § Do not specify a partition).

Trillium and the GPU model: Trillium has 63 H100 nodes, 1 H200 node and 52 B200 nodes ("the B200s
are not yet available", Trillium § Node characteristics). The kit names the model with the wiki's
general form `--gpus-per-node=<model_specifier>:<number>` and Trillium's specifier `h100`
(Using_GPUs_with_Slurm § Introduction and § Available GPUs), although the Trillium pages themselves
write `--gpus-per-node=1`. If `sbatch` on Trillium rejects `h100:1`, add `--gpu-instance unpinned`
(exactly the Quickstart's request; the kit prints that the job may then land on an H200 or, later,
a B200, for which the H100 gpu-check says nothing; `nvidia-smi.txt` shows what you got).

### 4.1 gpu-check (first, on every cluster; a short job)

```bash
bash scripts/hpc/alliance/submit.sh fir gpu-check --account def-XXX --time 00:15:00
```

It prints `nvidia-smi`, the cupy/CUDA versions and the device, compares a cupy FFT with numpy, and
runs two tiny multislice cases (a continuum refraction case and a 40,000-atom Si(001) a/2 step) with
numpy complex128 as reference and cupy in complex128 and complex64. Tolerances were fixed before any
GPU run (gpu_check.py: 1e-9 for complex128, 1e-3 for complex64, relative to max |psi|; numpy
complex64 deviates by 1.8e-5 and 9.2e-5 on these cases). Success, at the end of
`$SCRATCH/reflholo/logs/gpu-check_<jobid>.log`:

```
GPU CHECK: PASS (record .../reflholo/gpu_check/PASS_fir_<env id>_<jobid>.json; valid for cluster fir, environment <env id> and engine code <hash>)
```

On `GPU CHECK: FAIL` stop: no other GPU job will be accepted; bring back
`runs/gpu-check_<jobid>_*/gpu_check/gpu_check.json` (section 6). Runtime: the numpy reference of the
atomistic case took 15 s on 4 CPUs here; the GPU part has never run (NOT RUN), so no duration of
this job has been measured.

### 4.2 gpu-sanity (second, on every cluster; 1 GPU)

```bash
bash scripts/hpc/alliance/submit.sh fir gpu-sanity --account def-XXX --time 00:30:00
```

Step 0 of the H2 report's run order (H2 is under review): on the GPU, (1) the first null-study
point `tfix_bragg_abs0_L0` must reproduce its stored CPU value (M2 report: error +0.569 rad,
amplitude ratio 0.951) within 1e-2 rad and 1e-2, and (2) the H2 build-up strip `bu_100_r010`
(`tools/hpc/supercell_sizing.py --measure ... --backend cupy`) must reproduce the stored plateau
(|R| 0.2707, arg -1.5394 rad, `tools/hpc/supercell_sizing_measurements.json`) within 1e-2 rad and
1e-2 relative. The tolerances were fixed before any GPU run (`gpu_sanity.py`) and are printed first
in the log. Success: `GPU SANITY: PASS`. The same script on the numpy backend here: study point
+0.568589 rad (deviation 4.1e-4) and 0.951007, strip deviation 0 (bitwise), 2 min 43 s on 4
threads of a shared machine; the GPU durations are NOT measured (GPU_ASSUMED model: 0.3 s for the
point). It also prints the first measured GPU times against the GPU_ASSUMED model.

### 4.3 smoke (geometric engine, CPU)

```bash
bash scripts/hpc/alliance/submit.sh fir smoke --account def-XXX --time 00:15:00 --mem 2G
```

Success: the log shows `list-inputs`, the dry run, then `heights: 3 of 3 step heights returned`,
`h = +2.7156 +- 0.0165 A`, `h = -1.3576 +- 0.0082 A`, `h = -1.3580 +- 0.0082 A`,
`no-step control: PASS`, `finished with status 0`. Measured here: 3.4 s wall and 132 MB peak RSS for
the run; the whole emulated job 5 s.

### 4.4 demo-gpu (multislice demo, 1 GPU, cupy, complex64)

```bash
bash scripts/hpc/alliance/submit.sh fir demo-gpu --account def-XXX --time 01:00:00
```

The job re-checks cupy on the node, prints `list-inputs` and the dry run (it builds 1.44 million
atoms: 39 s in P1's measurement; 52 s here while another job shared the 4 CPUs), then runs. Expected first result line:
`NO HEIGHT: no-step control failed or not performed` (correct, see above), then
`finished with status 0`. Memory per realisation about 127 MiB; GPU propagation about 9 s according
to the engine's GPU_ASSUMPTION model (`dry-run` here: "GPU (ASSUMPTION model, not measured) ~9 s"),
NOT measured. The same demo on CPU (`pipeline --config configs/demo_hpc_si001.yaml --variant
cpu_numpy --mem 32G --time 01:00:00`) took 18.8 min wall with 8 threads on 4 CPUs (README_HPC §5).

### 4.5 torus (half-torus trench then ridge; CPU, 4 threads; not on Trillium)

```bash
bash scripts/hpc/alliance/submit.sh fir torus --account def-XXX --time 01:00:00 --mem 4G
```

Runs `scripts/torus/run_torus_multislice.py --kind trench`, then `--kind ridge` (`--kinds` to
change). Success per kind: `[trench] simulate ... s, total ... s, peak RSS ... MB, manifest ...`.
T1 measured about 190-210 s of simulation and 1.35 GB peak RSS per kind on 4 CPUs. The runner
calibrates its CPU estimate on the node (x1.5) and REFUSES a kind (status 2, before computing) if the
estimate exceeds its CPU limit. Run by hand, that limit is 600 s (T1's CASE limits, set for the
build machine); in a kit job it is derived from your `--time`: 80 % of the walltime divided by the
number of kinds (`--time 01:00:00`, two kinds: 1440 s per kind), passed as `--max-cpu-seconds` and
recorded in `case_<kind>.json` and `summary_<kind>.json`. What was measured (never on a cluster):
estimates of 163-213 s (T1), 502-865 s (H3, 4 CPUs shared with other runs), and ridge 420-763 s,
trench 265-515 s (H4, four runs each on a shared 4-CPU machine). A refusal is reported in the log
with exit status 2; resubmit that kind (`--kinds ridge`) with a longer `--time`.

### 4.6 null-study (17 points, GPU, cupy)

`gpu-sanity` (4.2) already ran the first point on the GPU against its stored CPU value, as the
study's README asks. Then all 17 points in ONE job (the default, `--serial`):

```bash
bash scripts/hpc/alliance/submit.sh fir null-study --account def-XXX --time 01:00:00
```

One point alone: `--only <point>`. An array with one point per task is available with `--array`
(`%N` with `--array-throttle N`), but the kit prints the wiki's advice against it: "You should not
use a job array to submit tasks with very short run times, e.g. much less than an hour"
(Job_arrays § A simple example); every point here is estimated at seconds of GPU time. Each array
task counts as a job against the 1000-job limit (500 submitted on Trillium). Caveat of the one-job
mode: run_study.py stops at the first exception (earlier points stay on disk). At submission the
study file is copied next to the submission record (`submissions/<record>.study.yaml`, SHA-256 in
the record); every job checks that hash, copies it into its directory (`study_used.yaml`) and reads
only that copy, so a `git pull` or an edit of `study.yaml` while jobs wait changes nothing. Success
per point: `-> .../study/outputs/null_test_study/<point>.json (<n> s), manifest ...`.
Expected sizes and times, from `run_study.py --estimate` (this is its output here, numpy backend,
4 threads; the CPU numbers include the study's x1.5 calibration; the GPU numbers are the engine's
GPU_ASSUMPTION model, not measured):

```
tfix_bragg_abs0_L0: grid 640x60, 1434 slices, 19224 atoms, engine arrays 4 MB, CPU ~8 s (x1.5 calibration), GPU ~0.3 s (ASSUMPTION model)
tfix_bragg_abs0_L10k: grid 1875x60, 11850 slices, 159840 atoms, engine arrays 16 MB, CPU ~166 s (x1.5 calibration), GPU ~3.7 s (ASSUMPTION model)
tfix_bragg_abs0_L20k: grid 3125x60, 22266 slices, 300456 atoms, engine arrays 29 MB, CPU ~554 s (x1.5 calibration), GPU ~9.5 s (ASSUMPTION model)
tfix_bragg_abs05_L0: grid 640x60, 1434 slices, 19224 atoms, engine arrays 4 MB, CPU ~9 s (x1.5 calibration), GPU ~0.3 s (ASSUMPTION model)
tfix_bragg_abs05_L5k: grid 1260x60, 6642 slices, 89532 atoms, engine arrays 10 MB, CPU ~68 s (x1.5 calibration), GPU ~1.7 s (ASSUMPTION model)
tfix_bragg_abs05_L10k: grid 1875x60, 11850 slices, 159840 atoms, engine arrays 16 MB, CPU ~186 s (x1.5 calibration), GPU ~3.7 s (ASSUMPTION model)
tfix_bragg_abs10_L5k: grid 1260x60, 6642 slices, 89532 atoms, engine arrays 10 MB, CPU ~78 s (x1.5 calibration), GPU ~1.7 s (ASSUMPTION model)
tfix_bragg_abs10_L10k: grid 1875x60, 11850 slices, 159840 atoms, engine arrays 16 MB, CPU ~193 s (x1.5 calibration), GPU ~3.7 s (ASSUMPTION model)
tfix_off12_abs10_L5k: grid 1120x60, 7010 slices, 94500 atoms, engine arrays 10 MB, CPU ~61 s (x1.5 calibration), GPU ~1.7 s (ASSUMPTION model)
tfix_off20_abs10_L5k: grid 1440x60, 6406 slices, 86346 atoms, engine arrays 11 MB, CPU ~78 s (x1.5 calibration), GPU ~1.7 s (ASSUMPTION model)
tmov_bragg_abs10_L10k: grid 1875x60, 11850 slices, 159840 atoms, engine arrays 16 MB, CPU ~176 s (x1.5 calibration), GPU ~3.7 s (ASSUMPTION model)
step_w8_bragg_abs10_L5k: grid 1260x480, 6642 slices, 742784 atoms, engine arrays 82 MB, CPU ~267 s (x1.5 calibration), GPU ~4.3 s (ASSUMPTION model)
step_w16_bragg_abs10_L5k: grid 1260x960, 6642 slices, 1485568 atoms, engine arrays 167 MB, CPU ~559 s (x1.5 calibration), GPU ~9.6 s (ASSUMPTION model)
step_w32_bragg_abs10_L5k: grid 1260x1920, 6642 slices, 2971136 atoms, engine arrays 340 MB, CPU ~1486 s (x1.5 calibration), GPU ~22.8 s (ASSUMPTION model)
step_w16_bragg_abs0_L5k: grid 1260x960, 6642 slices, 1485568 atoms, engine arrays 167 MB, CPU ~527 s (x1.5 calibration), GPU ~9.6 s (ASSUMPTION model)
step_w16_off20_abs10_L5k: grid 1440x960, 6406 slices, 1432704 atoms, engine arrays 177 MB, CPU ~626 s (x1.5 calibration), GPU ~10.7 s (ASSUMPTION model)
step_w16_bragg_abs10_L10k: grid 1875x960, 11850 slices, 2652160 atoms, engine arrays 267 MB, CPU ~1546 s (x1.5 calibration), GPU ~26.0 s (ASSUMPTION model)
```

Sum: 6588 s of CPU (1.8 h on 4 threads) or 115 s of GPU_ASSUMPTION time; the largest engine
memory estimate is 340 MB. The estimate for all 17 points took 26 s here (it builds every cell);
with the default cupy study the CPU column is not printed. The study declares 8 threads, so a MIG
instance (fewer recommended cores) would need a study copy with a smaller `runtime.threads`
(`--study <copy>`).

### 4.7 Production-size configurations (agent H2)

Any pipeline configuration, any GPU instance, no code change. Do NOT run `pipeline dry-run` of a
production-size configuration on a login node: it builds the whole structure (the 1.44 M-atom
`demo_hpc_si001.yaml` alone peaked at 3.6 GB RSS in 52 s, H4 audit; Trillium's login-node guidance
is 1-2 GB, Trillium_Quickstart § Testing and debugging; H2's production cells have 10^7-10^8
atoms). Size it in a CPU job instead:

```bash
bash scripts/hpc/alliance/submit.sh nibi dry-run --config <H2 config> --account def-XXX --time 01:00:00 --mem <SIZE>
bash scripts/hpc/alliance/submit.sh nibi pipeline --config <H2 config> --account def-XXX --time 06:00:00 \
     [--gpu-instance full|3g.40gb|...] [--need-gpu-mem-gb <from dry-run>] [--cpus N] [--mem SIZE]
     [--gpu-mem-from-dry-run <dry-run job dir> --gpu-mem-margin <fraction>]
bash scripts/hpc/alliance/submit.sh nibi null-study --study <H2 study.yaml> --account def-XXX --time 02:00:00
```

The `dry-run` job prints the configuration check, the engine's estimates and the PEAK RSS of the
structure build (`dry_run/dry_run_resources.json`). For a cupy configuration it then exits 4 (no GPU
on a CPU node): expected, the estimates are complete. Its "memory per realisation" counts only the
engine's arrays of one realisation, not the job: a CPU run also holds the structure and cell (the
measured peak RSS) and, while realising, about 192-240 B per atom (H2 §8 and §12, from reading the
code, not measured; H2 is under review). No number of H2 is used as a default: `--mem` stays
required for every CPU job, and `--mem` of the dry-run job itself must cover the structure build.
H2 N9: the builders cannot yet build 10^8 atoms in memory.

A configuration whose backend is `numpy` becomes a CPU job (then `--mem` is required); `cupy` a GPU
job. `--need-gpu-mem-gb` refuses an instance with less memory than you need. Instead of reading it
off the dry run by hand, `--gpu-mem-from-dry-run <dry-run job dir or its dry_run/dry_run_report.json>
--gpu-mem-margin <fraction>` derives it: the engine's cupy device peak (`engine.memory_model`, a
LOWER BOUND: cuFFT/cuBLAS workspaces and the cupy pool are not modelled, no GPU was available to
measure them) times (1 + margin); the margin has no default. The derivation is printed and recorded
in the submission record, the dry-run report must be the one of the same configuration and variant
(SHA-256 checked), the host memory of the GPU run (cupy host peak + 48 B/atom of builder structure,
192 B/atom in total, H7) is compared with `--mem`, and an explicit `--need-gpu-mem-gb` overrides the
derived value. MIG instances per
cluster (one per job, Multi-Instance_GPU § Limitations): Fir/Nibi/Rorqual 1g.10gb, 2g.20gb,
3g.40gb; Narval 1g.5gb, 2g.10gb, 3g.20gb; Trillium none.

## 5. Where the outputs are

Everything under `$SCRATCH/reflholo/` (scratch is not backed up and is purged after 60 days on Fir,
Narval and Rorqual; Nibi has a 1 TB soft quota; Storage_and_file_management, Scratch_purging_policy):

| Path | Content |
|---|---|
| `logs/<job>_<jobid>.log` (`<job>_<arrayjobid>_<task>.log`) | the Slurm log |
| `runs/<job>_<jobid>_<UTC stamp>/` (`runs/null-study_<arrayjobid>/task<NNN>_<jobid>_<stamp>/`) | one directory per job, never reused |
| ... `/pipeline/` | pipeline jobs: summary.json, manifest.json, arrays.npz, quick looks, dry-run text |
| ... `/torus_<kind>/`, `/study/` (+ `study_used.yaml`), `/gpu_check/`, `/gpu_sanity/`, `/dry_run/` | the other jobs' outputs |
| ... `/manifests/` | copies of every provenance manifest of the job |
| ... `/slurm.log`, `job_info.json`, `job_status.txt`, `module_list.txt`, `nvidia-smi.txt`, `scontrol_show_job.txt`, `submission.json` | job records |
| `submissions/` | one record per submission, never overwritten (`<UTC>_<cluster>_<job>_<pid>_<random>.json`: the sbatch command, profile values, gate, study hash), sbatch's reply (`.json.sbatch_output`) and, for study jobs, the study copy the jobs read (`.study.yaml`) |
| `gpu_check/PASS_*.json` | gpu-check passes: cluster, environment id and engine-code SHA-256 (read by submit.sh and by every GPU job when it starts) |
| `cache/` | cupy kernel, numba and matplotlib caches (home is read-only on Trillium compute nodes) |

## 6. Bring the results back

```bash
bash scripts/hpc/alliance/collect_results.sh --max-array-mb 50 --max-file-mb 20 --max-total-mb 500   # all runs
bash scripts/hpc/alliance/collect_results.sh --max-array-mb 0 --max-file-mb 20 --max-total-mb 100 --jobs 1234567,1234599
```

It packs every file of the selected runs, their logs, submission records and gpu-check PASS records
within three required caps: arrays (`*.npz`, `*.npy`, `*.h5`) up to `--max-array-mb` each, every
other file up to `--max-file-mb` each, all together up to `--max-total-mb` (non-array files first,
then arrays). EVERY file left out is listed with its size and the cap that dropped it in
`DROPPED_FILES.tsv` inside the tarball (and printed); arrays dropped by their cap also in
`SKIPPED_ARRAYS.tsv`. Output: `$SCRATCH/reflholo/collect/reflholo_results_<host>_<stamp>.tar.gz` with
`MANIFEST.sha256` inside and a `.sha256` next to it. On your laptop (Linux: `sha256sum -c`; macOS
has no `sha256sum` by default: `shasum -a 256 -c`):

```bash
scp fir:/path/printed/reflholo_results_*.tar.gz* .     # Fir, Nibi: login node (no DTN yet / "use login nodes")
sha256sum -c reflholo_results_*.tar.gz.sha256            # macOS: shasum -a 256 -c reflholo_results_*.tar.gz.sha256
mkdir -p outputs/alliance && tar -xzf reflholo_results_*.tar.gz -C outputs/alliance
(cd outputs/alliance && sha256sum -c MANIFEST.sha256)   # macOS: shasum -a 256 -c MANIFEST.sha256
```

`outputs/` is gitignored; hand the tarball (or the unpacked folder) to the orchestrator. Data transfer
nodes: Narval and Rorqual use their login host name; Trillium `tri-dm{1,2,3,4}.scinet.utoronto.ca`
(Transferring_data asks to prefer DTNs for transfers).

## 7. What this kit does not know (NOT_FOUND on the wiki; check on the cluster)

* The CUDA version of the wheelhouse cupy (gpu-check decides), the default StdEnv on Fir, Nibi and
  Rorqual (setup loads StdEnv/2023 explicitly), whether login nodes reach PyPI (setup tells you).
* The maximum job-array size (`scontrol show config | grep -i MaxArraySize` is a standard Slurm
  command, not from the wiki); the running-job limits of the general-purpose clusters.
* The `$SCRATCH` variable is documented only for Trillium; Fir documents `$HOME/scratch`, Rorqual
  `$HOME/links/scratch`. If `$SCRATCH` is unset, pass `--scratch <dir>` to submit.sh.
* The minimum test-job length on Nibi (only the one-hour production advice is stated); the kit
  warns below 5 min there.
* Whether Trillium's sbatch accepts the model in `--gpus-per-node=h100:1` (the general syntax and
  Trillium's specifier are on the wiki, a Trillium example with a model is not); if it is
  rejected, use `--gpu-instance unpinned` (section 4).
