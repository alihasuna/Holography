#!/bin/bash
#SBATCH --job-name=holo-sections
#SBATCH --account=def-CHANGEME
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00                 # size it from: run_sections.py --config <cfg> --dry-run
#SBATCH --output=logs/%x-%j.out
# One configuration on one GPU. Usage: sbatch hpc/job_sections.sh configs/si001_three_sections_cpu.yaml
set -euo pipefail
source hpc/common.sh
CFG=${1:?usage: sbatch hpc/job_sections.sh <config.yaml>}
python scripts/run_sections.py --config "$CFG" --backend cupy --out "$HOLO_OUT"
