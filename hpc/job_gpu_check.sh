#!/bin/bash
#SBATCH --job-name=holo-gpucheck
#SBATCH --account=def-CHANGEME          # your allocation (def-<PI> or rrg-<PI>)
#SBATCH --gpus-per-node=1               # optionally a type, e.g. a100:1 or h100:1 (cluster-dependent)
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
# FIRST job on any cluster: the cupy path must reproduce numpy before production runs.
set -euo pipefail
source hpc/common.sh
python -m pytest -q -rs tests/          # expect all passed, the cupy test RUN (not skipped)
python scripts/run_sections.py --config configs/si001_three_sections_cpu.yaml --dry-run
