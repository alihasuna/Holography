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
  job on every cluster; `submit.sh` refuses the other GPU jobs until a gpu-check PASS is recorded for
  that environment (override: `--skip-gpu-check-gate`, not recommended).

## 0. Where to run

In production (National_systems § List of compute clusters): Fir (4 x H100 80 GB per GPU node),
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

It loads `StdEnv/2023`, `python/3.11.5`, `cuda/12.6` (the combination of the wiki's own GPU job
example, Trillium_Quickstart § Example: Single-GPU Job; Python 3.11 because pyproject.toml needs
>= 3.11 and the 3.11 wheelhouse has cupy 14.1.0, pyfftw and every abTEM requirement), creates
`venv/` with `virtualenv --no-download`, installs everything with `pip install --no-index` from the
Alliance wheelhouse, downloads abTEM 1.0.10 (not in the wheelhouse) with `pip download --no-deps` on
the login node (Python § Pre-downloading packages), checks its SHA-256 against PyPI, installs this
package, imports everything and runs a short CPU test subset (here: 780 tests in 2 min 15 s on 4
CPUs shared with another job). It stops at the first error (`avail_wheels` is only recorded: a
failure there prints a WARNING, and the `pip install --no-index` that follows is the check). Success
ends with:

```
== DONE: environment fir-<UTC stamp>-<hash> ready in /home/<you>/Holography/venv (records in venv/alliance).
```

Records: `venv/alliance/modules.sh` (the module sequence every job repeats after `module purge`),
`module_list.txt` (every job compares its loaded modules with it and refuses on a difference),
`env.json`, `pip_freeze.txt`, `package_sources.tsv` (which package came from the wheelhouse, which
from PyPI), `avail_wheels.txt`, `setup.log`.

If it fails:
* `No matching distribution found` for a wheel: the 3.11 wheelhouse of StdEnv/2023 lacks it (the
  wiki says new wheels target the 3 newest Pythons, Python § Python version supported). Rerun with
  `--recreate --python-module python/3.12.4` (Wheels3.12 also has cupy 14.1.0).
* `pip download` of abTEM fails (login node without PyPI access; the wiki does not state login-node
  internet explicitly): download `abtem-1.0.10-py3-none-any.whl` on your laptop, `scp` it over and
  rerun with `--recreate --abtem-wheel <path>`.
* `import cupy` fails on the login node with an NVIDIA driver/libcuda message: login nodes may have
  no GPU driver. Rerun with `--recreate --allow-cupy-import-failure`; gpu-check then decides.
* The CUDA version the wheelhouse cupy was built for is NOT stated on the wiki; if gpu-check fails
  on a CUDA version mismatch, try `--recreate --cuda-module cuda/12.9` (listed in Modules_avx512).

## 4. Submit, in this order

All jobs go through `submit.sh <cluster> <job> --account <RAP> --time <limit> [options]`. Add
`--dry-run` first to see the exact `sbatch` command (nothing is submitted or created). There is no
default account and no default time limit; CPU jobs also need `--mem`. Times: Slurm formats
(`MM`, `HH:MM:SS`, `D-HH`...; Running_jobs § Use sbatch to submit jobs). Limits enforced from
clusters.yaml: at most 168 h (24 h on Trillium), at least 5 min on Fir/Narval/Rorqual (test jobs)
and 15 min on Trillium; below 60 min you get a warning ("production jobs should have a duration of
at least an hour", Running_jobs § Cluster particularities). Watch jobs with `squeue -u $USER`.

Replace `def-XXX` by your RAP. The resource requests the kit builds (per GPU, from
Allocations_and_compute_scheduling § Ratios in bundles, recommended values): Fir `--gpus=h100:1
--cpus-per-task=12 --mem=280G`; Nibi `--gpus=h100:1 --cpus-per-task=14 --mem=250G`; Rorqual
`--gpus=h100:1 --cpus-per-task=16 --mem=124G`; Narval `--gpus=a100:1 --cpus-per-task=12
--mem=124G`; Trillium `--nodes=1 --gpus-per-node=1` (24 cores and 188 GiB come with the GPU;
`--mem` is ignored there, Trillium_Quickstart § Memory requests are ignored). No partition is ever
given (Running_jobs § Do not specify a partition).

### 4.1 gpu-check (first, on every cluster; a short job)

```bash
bash scripts/hpc/alliance/submit.sh fir gpu-check --account def-XXX --time 00:10:00   # Trillium: 00:15:00
```

It prints `nvidia-smi`, the cupy/CUDA versions and the device, compares a cupy FFT with numpy, and
runs two tiny multislice cases (a continuum refraction case and a 40,000-atom Si(001) a/2 step) with
numpy complex128 as reference and cupy in complex128 and complex64. Tolerances were fixed before any
GPU run (gpu_check.py: 1e-9 for complex128, 1e-3 for complex64, relative to max |psi|; numpy
complex64 deviates by 1.8e-5 and 9.2e-5 on these cases). Success, at the end of
`$SCRATCH/reflholo/logs/gpu-check_<jobid>.log`:

```
GPU CHECK: PASS (record .../reflholo/gpu_check/PASS_fir_<env id>_<jobid>.json)
```

On `GPU CHECK: FAIL` stop: no other GPU job will be accepted; bring back
`runs/gpu-check_<jobid>_*/gpu_check/gpu_check.json` (section 6). Runtime: the numpy reference of the
atomistic case took 15 s on 4 CPUs here; the GPU part has never run (NOT RUN).

### 4.2 smoke (geometric engine, CPU)

```bash
bash scripts/hpc/alliance/submit.sh fir smoke --account def-XXX --time 00:15:00 --mem 2G
```

Success: the log shows `list-inputs`, the dry run, then `heights: 3 of 3 step heights returned`,
`h = +2.7156 +- 0.0165 A`, `h = -1.3576 +- 0.0082 A`, `h = -1.3580 +- 0.0082 A`,
`no-step control: PASS`, `finished with status 0`. Measured here: 3.4 s wall and 132 MB peak RSS for
the run; the whole emulated job 5 s.

### 4.3 demo-gpu (multislice demo, 1 GPU, cupy, complex64)

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

### 4.4 torus (half-torus trench then ridge; CPU, 4 threads; not on Trillium)

```bash
bash scripts/hpc/alliance/submit.sh fir torus --account def-XXX --time 01:00:00 --mem 4G
```

Runs `scripts/torus/run_torus_multislice.py --kind trench`, then `--kind ridge` (`--kinds` to
change). Success per kind: `[trench] simulate ... s, total ... s, peak RSS ... MB, manifest ...`.
T1 measured about 190-210 s of simulation and 1.35 GB peak RSS per kind on 4 CPUs. Note: the runner
calibrates its CPU estimate on the node and REFUSES (status 2, before computing, about 20 s) if the
estimate exceeds its own 600 s limit (T1's CASE limits, set for the build machine). In the emulated
job here (4 CPUs shared with other agents' runs) the first attempt refused both kinds (estimates
668 s and 865 s); the second ran the trench (estimate 502 s; simulate 376.8 s, total 396.0 s, peak
RSS 1329 MB) and refused the ridge (762 s). On a Slurm allocation the 4 cores are yours, so the
calibration should be closer to T1's (213 s and 163 s); a refusal is reported in the log with exit
status 2 and is the runner's own guard, not a kit failure. Resubmit with `--kinds ridge` if only one
kind was refused.

### 4.5 null-study (17 points, GPU, cupy)

As the study's README asks, run the first point alone and compare it with the in-container value
(err +0.569 rad) before the rest:

```bash
bash scripts/hpc/alliance/submit.sh fir null-study --account def-XXX --time 00:30:00 --only tfix_bragg_abs0_L0
```

Then all 17 points, one per array task (`--array=0-16`; `%N` with `--array-throttle N`):

```bash
bash scripts/hpc/alliance/submit.sh fir null-study --account def-XXX --time 00:30:00
```

The wiki advises against arrays of tasks much shorter than an hour (Job_arrays § A simple example):
`--serial` runs all 17 points in one job instead (`--time 01:00:00`). Each array task counts as a job
against the 1000-job limit (500 submitted on Trillium). Success per point:
`-> .../study/outputs/null_test_study/<point>.json (<n> s), manifest ...`.
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

### 4.6 Production-size configurations (agent H2)

Any pipeline configuration, any GPU instance, no code change:

```bash
venv/bin/python -m reflection_holo.pipeline dry-run --config <H2 config>     # login node: memory and GPU estimate
bash scripts/hpc/alliance/submit.sh nibi pipeline --config <H2 config> --account def-XXX --time 06:00:00 \
     [--gpu-instance full|3g.40gb|...] [--need-gpu-mem-gb <from dry-run>] [--cpus N] [--mem SIZE]
bash scripts/hpc/alliance/submit.sh nibi null-study --study <H2 study.yaml> --account def-XXX --time 02:00:00
```

A configuration whose backend is `numpy` becomes a CPU job (then `--mem` is required); `cupy` a GPU
job. `--need-gpu-mem-gb` refuses an instance with less memory than you need. MIG instances per
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
| ... `/torus_<kind>/`, `/study/`, `/gpu_check/` | the other jobs' outputs |
| ... `/manifests/` | copies of every provenance manifest of the job |
| ... `/slurm.log`, `job_info.json`, `job_status.txt`, `module_list.txt`, `nvidia-smi.txt`, `scontrol_show_job.txt`, `submission.json` | job records |
| `submissions/` | the plan (sbatch command, profile values) of every submission and sbatch's reply |
| `gpu_check/PASS_*.json` | gpu-check passes (read by submit.sh) |
| `cache/` | cupy kernel, numba and matplotlib caches (home is read-only on Trillium compute nodes) |

## 6. Bring the results back

```bash
bash scripts/hpc/alliance/collect_results.sh --max-array-mb 50            # all runs
bash scripts/hpc/alliance/collect_results.sh --max-array-mb 0 --jobs 1234567,1234599
```

It packs JSON, CSV/TSV, text, logs, PNG quick looks, manifests and submission records (and arrays
only up to the size you set; larger ones are listed in `SKIPPED_ARRAYS.tsv`) into
`$SCRATCH/reflholo/collect/reflholo_results_<host>_<stamp>.tar.gz` with `MANIFEST.sha256` inside and
a `.sha256` next to it. On your laptop:

```bash
scp fir:/path/printed/reflholo_results_*.tar.gz* .     # Fir, Nibi: login node (no DTN yet / "use login nodes")
sha256sum -c reflholo_results_*.tar.gz.sha256
mkdir -p outputs/alliance && tar -xzf reflholo_results_*.tar.gz -C outputs/alliance
(cd outputs/alliance && sha256sum -c MANIFEST.sha256)
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
* The minimum test-job length on Nibi (only the one-hour production advice is stated).
