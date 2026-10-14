#!/bin/bash
#SBATCH --job-name=rh-selftest
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=120G
#SBATCH --time=01:00:00
#SBATCH --output=%x-%j.out
# GPU self-test and benchmark (one H100).  Usage (from the repository root):
#   sbatch --account=$FIR_ACCOUNT fir/selftest.sbatch RUN_DIR
set -euo pipefail
RUN_DIR=${1:?usage: sbatch fir/selftest.sbatch RUN_DIR}
cd "${SLURM_SUBMIT_DIR:-$(pwd)}"
source fir/env.sh
mkdir -p "$RUN_DIR"
nvidia-smi
echo "== unit tests (CPU)"
python -m pytest -q -m "not slow" tests
echo "== GPU equivalence and throughput"
python fir/gpu_selftest.py --run-dir "$RUN_DIR"
if python -c "import abtem" 2>/dev/null; then
    echo "== abTEM transmission cross-check (optional)"
    python validation/abtem_crosscheck.py --backend cupy --out "$RUN_DIR/abtem_crosscheck.json" || \
        echo "abTEM cross-check failed to run (not a gate)"
fi
echo "== cost estimate with the measured throughput"
python -m reflection_holo.campaign check --config configs/fir_m2_campaign.yaml --stage all \
       --benchmark "$RUN_DIR/benchmark.json" | tee "$RUN_DIR/cost_estimate.txt"
