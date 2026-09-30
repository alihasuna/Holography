#!/usr/bin/env bash
# Buried-dislocation smoke tests on a GPU machine (see docs/09_gpu_runbook_arbutus.md).
# Usage: bash scripts/run_gpu_smoke.sh   (from the repository root, venv already set up)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=venv/bin/python
LOG=outputs/gpu_smoke_$(date -u +%Y%m%dT%H%M%SZ).log
mkdir -p outputs
{
  echo "== host $(hostname), commit $(git rev-parse --short HEAD)"
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
  echo "== 1. unit tests incl. cupy-vs-numpy backend check"
  $PY -m pytest -q -rs
  echo "== 2. geometry mode"
  $PY scripts/run_buried_dislocation.py geometric --config configs/smoke/buried_dislocation_gpu.yaml
  $PY scripts/run_buried_dislocation.py geometric --config configs/smoke/buried_dislocation_single_geometric.yaml
  echo "== 3. multislice, CPU-sized config on the GPU (compare with the numbers in docs/08)"
  $PY scripts/run_buried_dislocation.py multislice --backend cupy --config configs/smoke/buried_dislocation_cpu.yaml
  echo "== 4. multislice, full GPU config (5-angle rocking scan)"
  $PY scripts/run_buried_dislocation.py multislice --backend cupy --config configs/smoke/buried_dislocation_gpu.yaml
  echo "== done"
} 2>&1 | tee "$LOG"
echo "log: $LOG"
