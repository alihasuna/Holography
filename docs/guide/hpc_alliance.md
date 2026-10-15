# Running on the Digital Research Alliance of Canada

Status: 2026-10-12. None of the job scripts in `hpc/` has been executed on an Alliance cluster
yet, and the cupy path is untested on real hardware (no GPU in the development environment).
The Alliance documentation (docs.alliancecan.ca) could not be read from the development
environment, so module versions, GPU types and allocation details are marked "check".

## 1. What runs where

| Resource | Use it for |
|---|---|
| **Arbutus VM** (your 12 GB GPU, persistent, you are admin) | development; the first GPU check; small runs (the 46 nm three-strip cell needs about 0.4 GB); interactive analysis and figures |
| **Alliance clusters with Slurm GPU partitions** (data-centre GPUs, e.g. A100 or H100; check the current list of national systems) | production runs; parameter sweeps as job arrays; large cells (0.5 µm wide, several GB); frozen-phonon ensembles |
| **Any CPU** (laptop included) | geometric model at full size (seconds); building and rendering samples; holography reconstruction from saved waves |

Allocation:
* A default account (`def-<PI>`) gives opportunistic GPU time, which is enough for checks and
  modest sweeps.
* A large campaign (hundreds of GPU-hours) is worth a Resource Allocation Competition request
  (`rrg-<PI>`). Check the yearly deadline.

## 2. Workflow

```bash
# on a cluster LOGIN node, once
git clone https://github.com/alihasuna/Holography.git && cd Holography
git checkout trixode-studios-claude/ecstatic-euler-a2b4y1
bash hpc/setup_env.sh                      # virtualenv with numpy, scipy, matplotlib, pyyaml, pytest, cupy
sed -i 's/def-CHANGEME/def-<your PI>/' hpc/job_*.sh

# 1. gate: the GPU must reproduce the CPU before anything else
sbatch hpc/job_gpu_check.sh                # all tests pass, and the cupy test RUNS (not skipped)

# 2. rocking curves (sets the operating angles)
sbatch hpc/job_rocking.sh

# 3. size a run, then submit it
python scripts/run_sections.py --config configs/si001_three_sections_cpu.yaml --dry-run
sbatch hpc/job_sections.sh configs/si001_three_sections_cpu.yaml

# 4. parameter sweep as a job array
python scripts/make_sweep.py --base configs/si001_three_sections_cpu.yaml --out configs/sweep_depth \
    --depths 15 25 50 --reflections 008 0012 --offsets -0.3 0 0.3      # 18 configurations
sbatch --array=0-17 hpc/job_sweep.sh configs/sweep_depth/list.txt
```

* **Storage.** Results go to `$SCRATCH/holo_outputs`, which is fast but purged after a period
  without use. Copy the outputs to keep (`summary.json`, `manifest.json`, figures, `rows_*.npz`)
  to `$PROJECT`. The `rows_*.npz` waves are about 45 MB each; they are not for git.
* **Figures.** Regenerate them anywhere with `scripts/figures_holography.py --data <folder with
  rows_*.npz>`; no multislice re-run is needed.
* **Provenance.** Every run writes `manifest.json` with the GPU name, CUDA runtime, package
  versions, configuration hash and repository commit.

## 3. Sizes (from `--dry-run`) and what fits where

| Case | Grid | Memory (waves + potential build) | Fits |
|---|---|---|---|
| Three-strip cell, 46 nm, converged (this repository) | 1728 × 3600 (6.2 M points) | about 0.3 + 0.1 GB | everything, including the 12 GB VM |
| Same with ten-times-wider strips (about 0.46 µm cell, dislocations up to about 100 nm deep) | about 1728 × 36 000 (62 M points) | about 3 + 1 GB, plus 2–3 GB of matrix chunks while building the potential | 40/80 GB data-centre GPU comfortably; the 12 GB VM only just |
| Micrometre-wide fields | above 10⁸ points | more than 10 GB | one large-memory GPU or several; better: geometric model at full size, multislice patches |

The number of slices does not depend on the cell width: about 3100 at (008) and 2100 at
(0,0,12) for an 80 Å sheet.

Known limit before the 0.5 µm runs: building the slice potential costs about grid points × atoms
per slice. For a 0.46 µm cell that is about 10¹² complex multiply-adds per distinct slice. This is
quick on a data-centre GPU in double precision, but slow on a consumer GPU. If needed, the
potential builder can switch to single precision or to an FFT-based method; neither change has
been made yet.

## 4. Suggested first campaign

| Step | Jobs | Purpose |
|---|---|---|
| GPU check | 1 | the cupy path agrees with numpy; establishes the GPU timings |
| Rocking curves (008), (0,0,12) | 1 | operating angles on the production GPU |
| Converged three-strip run | 1 | reproduces docs/results/three_strips_results.md on the GPU (step −2.61 rad, dislocation −11.2 rad at (008)) |
| Footprint convergence of the (0,0,12) step (sheet height 160–320 Å) | 3–4 | settles the open (0,0,12) step phase (docs/results/three_strips_results.md section 3) |
| Depth × reflection × angle sweep | 18 | how the dislocation signal scales with depth; sensitivity to the angle |
| Wide cell with a realistic dislocation (50 nm deep, 60° and Lomer types) | 2–4 | the lab-scale prediction; needs a new wide config and the 60° Burgers vector |
| abTEM cross-validation of the kernel | a few | milestone M2: required before any result is called validated |

## 5. The 50 nm deep dislocation cases (Fir or any cluster with a data-centre GPU)

Configs: `configs/si001_60deg_50nm.yaml` (60 degree dislocation with its slip step) and
`configs/si001_lomer_50nm.yaml` (Lomer, for comparison). Both use a 0.74 µm cell, 1728 × 57 600 =
99.5 M grid points and about 82 000 atoms per 3.84 Å repeat. Expected footprint: under 12 GB of GPU
memory and about 12 GB of host memory. The 2 h default of `job_sections.sh` is ample on a GPU.

```bash
python scripts/run_sections.py --config configs/si001_60deg_50nm.yaml --dry-run      # check the sizes
sbatch hpc/job_sections.sh configs/si001_60deg_50nm.yaml     # both (008) and (0,0,12)
sbatch hpc/job_sections.sh configs/si001_lomer_50nm.yaml
```

**Fir (checked 2026-10-14).** A GPU model is mandatory. Fir accepts `h100` (the whole 80 GB card)
or MIG slices `nvidia_h100_80gb_hbm3_3g.40gb`, `nvidia_h100_80gb_hbm3_2g.20gb` and
`nvidia_h100_80gb_hbm3_1g.10gb`. Command-line options override the `#SBATCH` lines, so the scripts
need no edits:

```bash
sbatch --account=def-<PI> --gpus-per-node=nvidia_h100_80gb_hbm3_1g.10gb:1 hpc/job_gpu_check.sh
sbatch --account=def-<PI> --gpus-per-node=nvidia_h100_80gb_hbm3_2g.20gb:1 hpc/job_sections.sh configs/si001_60deg_50nm.yaml
sbatch --account=def-<PI> --gpus-per-node=nvidia_h100_80gb_hbm3_2g.20gb:1 hpc/job_sections.sh configs/si001_lomer_50nm.yaml
```

Replace `<PI>` with your group's account name, without spaces or angle brackets (list accounts with
`sacctmgr show assoc user=$USER format=account%30`). If the job's virtualenv is not
`$HOME/venvs/holo`, run `export HOLO_VENV=<path>` before `sbatch`.

On a 4-core CPU the same run takes about 40 min for the potentials plus about 1.7 h per
reflection, using the multithreaded scipy.fft path. `--geometric-only` gives the column-model
prediction for the full cell in a few minutes on any CPU.
