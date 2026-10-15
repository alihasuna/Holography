#!/bin/bash
#SBATCH --job-name=holo-sweep
#SBATCH --account=def-CHANGEME
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%A_%a.out
# Parameter sweep, one config per array task.
#   python scripts/make_sweep.py --base configs/si001_three_sections_cpu.yaml --out configs/sweep_x ...
#   sbatch --array=0-<N-1> hpc/job_sweep.sh configs/sweep_x/list.txt
set -euo pipefail
source hpc/common.sh
LIST=${1:?usage: sbatch --array=0-N hpc/job_sweep.sh <list.txt>}
CFG=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$LIST")
echo "task $SLURM_ARRAY_TASK_ID -> $CFG"
python scripts/run_sections.py --config "$CFG" --backend cupy --out "$HOLO_OUT"
