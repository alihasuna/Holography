# Running the reflection-holography pipeline on an HPC cluster

On the Digital Research Alliance of Canada clusters (Fir, Nibi, Rorqual, Narval, Trillium) use the
kit in `scripts/hpc/alliance/` (README_ALLIANCE.md): it sets up the modules and the venv from the
wheelhouse, builds the sbatch command from the cluster profiles and delegates the pipeline jobs to
`run_pipeline.slurm` below (with `RH_PARTITION=none`: no partition, and `RH_WORKDIR`: the job's
text files go to its scratch directory).

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

Without `.git` the run is refused BEFORE any computation (exit status 6; the SLURM script refuses
to submit, status 2). Add `--allow-no-git` to `run` (or export `RH_ALLOW_NO_GIT=1` for the SLURM
script) only if you accept a manifest without a commit; the failure is then recorded together with
a SHA-256 of the package source tree (audit A3 M5).

## 2. Check a configuration before submitting

```bash
venv/bin/python -m reflection_holo.pipeline list-inputs --config configs/demo_hpc_si001.yaml
venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml
venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml --variant cpu_numpy --calibrate-cpu
```

`list-inputs` prints every PROJECT_INPUT item (1 to 22) with its status (SUPPLIED by whom and when,
from the structured fields `supplied_by`/`supplied_on`; ASSUMPTION stand-in; MISSING; NOT USED; and
"..., NOT USED on this path" with the reason for an accepted input that the selected engine path
does not use) and the run-level gate verdict. For the multislice engine item 20 shows the V0 the
engine actually uses (13.903 V, `potential_mip`). A run with a missing input
or an unregistered stand-in FAILS (exit status 3); nothing is defaulted. `dry-run` builds the
structure and the reflection cell, runs every engine assertion (docs/05 4.3 items 1 to 4, band
limits, mean-inner-potential consistency) without propagating, and prints memory and time
estimates (GPU time from the engine's labelled ASSUMPTION model, not measured; CPU time measured
on the node with `--calibrate-cpu`). For a cupy configuration it also checks that cupy imports and
sees a GPU: without one the checks still run but the dry run exits 4 ("multislice backend cupy NOT
available"), and a run is refused (exit 4) before computing. On a login node without CUDA this is
expected; the job checks again on the GPU node before its first step.

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

`python -m reflection_holo.pipeline run` prints a height verdict first, then the signed heights,
e.g. for the smoke demo `h = +2.7156 +- 0.0165 A` (a/2 = 2.7155 A) and `h = -1.3576 +- 0.0082 A`
(a/4 down-step). The uncertainties treat the incidence and exit angles of the specular beam as one
calibration error (audit A3 M3; before, +- 0.0117 and 0.0058 A). Heights are returned only if
(1) the no-step control PASSED (otherwise every height is withheld and the first line reads
`NO HEIGHT: no-step control failed or not performed ...`), and (2) the joint lattice constraint over
the steps of the run is significant: the chance that phases carrying no height information pass it
must be at most P(|Z| > 3) = 2.7e-3 (a single step never qualifies at a 0.1 mrad angle calibration;
the three demo steps give 1.2e-4). R2 (self-reference) runs return no height (differential phase,
not implemented). At the HPC angle (16.1347 mrad) +a/2 and -a/2 differ by only 0.078 rad of
wrapped phase: one a/2 step alone cannot be signed, which the summary and the CLI state; the joint
rule can sign it when the two a/4 steps are measured.

What to expect from the multislice demo (measured on CPU here, the same physics as on a GPU): the
pipeline runs end to end, but the dark-field phase of the UNVALIDATED multislice exit wave is not
flat along the beam within a terrace; the no-step control FAILS (0.44 rad between the two halves of
terrace 1 against a 0.29 rad tolerance). With the S4 fixes a failed control withholds every
height of the run, so expect `NO HEIGHT: no-step control failed or not performed` as the first
result line. This is reported, not hidden: heights from the multislice engine need the validation
ladder of docs/05 4.4 first.

## 5. Runtimes measured on the build machine (4 CPUs, no GPU; 2026-09-22)

| Run | Measured |
|---|---|
| smoke demo, geometric (`demo_smoke_si001.yaml`) | about 2 s wall (structure 0.9 s) |
| smoke, tiny multislice variant (`--variant multislice_tiny`, 27,000 atoms, 432 x 48 x 1095 slices) | about 7 s wall |
| `dry-run` of `demo_hpc_si001.yaml` (builds 1.44 million atoms and the cell) | 39 s wall |
| `demo_hpc_si001.yaml --variant cpu_numpy` estimate (`--calibrate-cpu`, engine's measured model) | 344 s per realisation |
| `demo_hpc_si001.yaml --variant cpu_numpy`, full run (1920 x 432 x 7215 slices, 8 FFT threads on 4 CPUs) | 18.8 min wall, 45 min CPU, about 0.75 GB resident |
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
