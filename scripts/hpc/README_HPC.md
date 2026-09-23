# Running the reflection-holography pipeline on an HPC cluster

Everything here is a DEMO: `purpose: demo; not comparable to experiment`. Every laboratory input
that Ali has not supplied is an explicit ASSUMPTION stand-in (B19 to B32, listed by
`list-inputs`); the multislice engine is UNVALIDATED for atomistic reflection (its status is copied
into every output). The beam energy is 200 keV (300 keV is never used).

## 1. Environment (login node, once)

```bash
git clone <repository> Holography && cd Holography   # or copy the tree (keep .git: the manifest records the commit)
module load python/3.11            # site-specific; also a CUDA module for the GPU run
bash scripts/hpc/setup_env.sh                          # numpy, pyyaml, pytest, abTEM 1.0.10, matplotlib
RH_CUPY=cupy-cuda12x bash scripts/hpc/setup_env.sh     # add cupy for the GPU backend (match your CUDA)
venv/bin/pytest -q                                     # optional: the test suite (a few minutes)
```

abTEM 1.0.10 (GPL-3.0-or-later) is an optional dependency, imported lazily by the multislice
atomic potential for the Kirkland parameterisation (report D3); no abTEM code is copied.

Without `.git` the manifest is refused; add `--allow-no-git` to `run` only if you accept a
manifest that cannot identify the code (the failure is then recorded).

## 2. Check a configuration before submitting

```bash
venv/bin/python -m reflection_holo.pipeline list-inputs --config configs/demo_hpc_si001.yaml
venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml
venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml --variant cpu_numpy --calibrate-cpu
```

`list-inputs` prints every PROJECT_INPUT item (1 to 22) with its status (SUPPLIED by whom and when,
ASSUMPTION stand-in, MISSING, NOT USED) and the run-level gate verdict. A run with a missing input
or an unregistered stand-in FAILS (exit status 3); nothing is defaulted. `dry-run` builds the
structure and the reflection cell, runs every engine assertion (docs/05 4.3 items 1 to 4, band
limits, mean-inner-potential consistency) without propagating, and prints memory and time
estimates (GPU time from the engine's labelled ASSUMPTION model, not measured; CPU time measured
on the node with `--calibrate-cpu`).

## 3. Submit: smoke test first, then the full run

Fill the four REQUIRED placeholders at the top of `scripts/hpc/run_pipeline.slurm` (`ACCOUNT`,
`PARTITION`, `TIME_LIMIT`, `GPU`), or export `RH_ACCOUNT`, `RH_PARTITION`, `RH_TIME_LIMIT`,
`RH_GPU`. There is no default: an unfilled placeholder stops the script with a message (status 2).
`RH_GPU=none` means CPU only; the script refuses a cupy configuration without a GPU.

```bash
# smoke test (geometric engine, configs/demo_smoke_si001.yaml; about 3 s of compute)
RH_MODE=smoke RH_ACCOUNT=... RH_PARTITION=... RH_TIME_LIMIT=00:10:00 RH_GPU=none \
  bash scripts/hpc/run_pipeline.slurm
# full multislice demo on a GPU (configs/demo_hpc_si001.yaml, cupy, complex64)
RH_ACCOUNT=... RH_PARTITION=<gpu partition> RH_TIME_LIMIT=01:00:00 RH_GPU=gpu:1 \
  bash scripts/hpc/run_pipeline.slurm
# the same on CPU nodes (numpy, complex128)
RH_VARIANT=cpu_numpy RH_ACCOUNT=... RH_PARTITION=... RH_TIME_LIMIT=02:00:00 RH_GPU=none \
  bash scripts/hpc/run_pipeline.slurm
```

The script submits itself with `sbatch`, then in the job sets `OMP_NUM_THREADS` (and the BLAS
variables) to `runtime.threads` of the configuration (8 for the HPC demo; `--cpus-per-task` must be
at least that, `RH_CPUS`, default request 8), prints `list-inputs` and `dry-run`, runs the
pipeline into `outputs/pipeline/<config>[_<variant>]_<jobid>_<UTC stamp>/` (never overwritten) and
copies the SLURM log there.

## 4. Expected outputs

In the output directory:

| File | Content |
|---|---|
| `summary.json` | purpose banner; every PROJECT_INPUT and its status; glancing angle (rule, V0 used and its source); engine label and status; exit-wave plane, pixel sizes and origin read from the wave; dark-field aperture record; projection samplings (exit plane, surface, image plane); detector record; reference; reconstruction parameters (carrier located on the EMPTY hologram, mask, resolution, sideband sign check); quantification: per step the wrapped phase difference, its measured uncertainty, the branch candidates and decision, the signed height with its propagated uncertainty and wrap period (or the reason no height is given), the no-step control, the shadow/blocked-view strips and excluded pixels; the index of every array with axes and units; timings |
| `manifest.json` | provenance manifest: package versions, repository commit and diff hash, engines, precision, seeds, threads (with the environment check), configuration hashes, wave planes, 200 keV |
| `arrays.npz` | exit wave, dark-field wave, projected image, detector object and reference waves, noiseless and noisy object and empty holograms, raw and corrected wrapped phase, unwrapped phase, amplitude, validity, ray-trace status and terrace maps, usable mask, quantification regions, axis coordinates |
| `quicklook_*.png` | only if matplotlib is importable and `outputs.quicklooks` is true |
| `outputs/manifests/`, `outputs/exit_waves/` | multislice only: the engine's own manifest and (if `save_exit_waves`) the exit waves |

`python -m reflection_holo.pipeline run` prints the signed heights, e.g. for the smoke demo
`h = +2.7156 +- 0.0117 A` (a/2 = 2.7155 A) and `h = -1.3576 +- 0.0058 A` (a/4 down-step).

## 5. Runtimes measured on the build machine (4 CPUs, no GPU; 2026-09-22)

| Run | Measured |
|---|---|
| smoke demo, geometric (`demo_smoke_si001.yaml`) | about 2 s wall (structure 0.9 s) |
| smoke, tiny multislice variant (`--variant multislice_tiny`, 27,000 atoms, 432 x 48 x 1095 slices) | about 7 s wall |
| `dry-run` of `demo_hpc_si001.yaml` (builds 1.44 million atoms and the cell) | 39 s wall |
| `demo_hpc_si001.yaml --variant cpu_numpy` estimate (`--calibrate-cpu`, engine's measured model) | 344 s per realisation |
| `demo_hpc_si001.yaml --variant cpu_numpy`, full run | see docs/agent_reports/P1_pipeline.md |
| GPU run | NOT RUN (no GPU here); the engine's ASSUMPTION model gives about 10 s of propagation |

Memory: about 140 MiB per realisation for the HPC grid (engine estimate) plus the 1.44-million-atom
structure (about 0.5 GB in the builder); 32 GB is ample.

## 6. What the demo does not do

Not comparable to experiment: stand-ins for every blocking input; clean bulk-terminated surface
(no oxide or damage layer); plane-wave illumination (no convergence, energy spread, drift,
charging, biprism Fresnel fringes, detector MTF); the multislice engine is not yet validated
against a dynamical reflection solver (docs/05 4.4 rung 2 and the abTEM cross-check NOT RUN), and
its independent-atom mean inner potential (13.903 V) exceeds B1 (12.0 V) and the DFT value
12.53 V. The tiny multislice variant is below the dark-field resolution along the beam, so its step
heights are reported as not measurable by design.
