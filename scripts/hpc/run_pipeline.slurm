#!/bin/bash
# SLURM runner of the reflection-holography pipeline (reflection_holo.pipeline).
#
# REQUIRED placeholders: ACCOUNT, PARTITION, TIME_LIMIT and GPU below (or the environment variables
# RH_ACCOUNT, RH_PARTITION, RH_TIME_LIMIT, RH_GPU). There is NO default account, partition, time or
# GPU: if one is left at __FILL_ME__ the script prints what is missing and exits (status 2), both
# when you launch it and inside the job.
#
# Usage (from the repository root):
#   bash scripts/hpc/run_pipeline.slurm            # checks the placeholders, then submits itself
#   RH_MODE=smoke bash scripts/hpc/run_pipeline.slurm   # smoke test first (geometric, < 1 min)
# or submit directly with every option on the command line:
#   sbatch --account=A --partition=P --time=HH:MM:SS --gres=gpu:1 --cpus-per-task=8 \
#          --export=ALL,RH_ACCOUNT=A,RH_PARTITION=P,RH_TIME_LIMIT=HH:MM:SS,RH_GPU=gpu:1 \
#          scripts/hpc/run_pipeline.slurm
# See scripts/hpc/README_HPC.md.
#SBATCH --job-name=reflholo
#SBATCH --output=reflholo_%j.log

set -euo pipefail

# ---- REQUIRED (no defaults) -----------------------------------------------------------------
ACCOUNT="${RH_ACCOUNT:-__FILL_ME__}"        # your SLURM account
PARTITION="${RH_PARTITION:-__FILL_ME__}"    # partition (GPU partition for the multislice run)
TIME_LIMIT="${RH_TIME_LIMIT:-__FILL_ME__}"  # wall time, e.g. 02:00:00
GPU="${RH_GPU:-__FILL_ME__}"                # GPU request, e.g. gpu:1 or gpu:a100:1; "none" = CPU only
# ---- run selection (explicit; change as needed) -----------------------------------------------
MODE="${RH_MODE:-full}"                     # smoke | full
CPUS="${RH_CPUS:-8}"                        # cpus-per-task; must be >= runtime.threads of the config
MEM="${RH_MEM:-32G}"
if [ "$MODE" = "smoke" ]; then
  CONFIG="${RH_CONFIG:-configs/demo_smoke_si001.yaml}"
  VARIANT="${RH_VARIANT:-}"
else
  CONFIG="${RH_CONFIG:-configs/demo_hpc_si001.yaml}"
  VARIANT="${RH_VARIANT:-}"                 # "" = GPU (cupy) run; cpu_numpy = CPU-only run
fi
REPO="${RH_REPO:-$(pwd)}"
PY="${REPO}/venv/bin/python"

missing=()
for v in ACCOUNT PARTITION TIME_LIMIT GPU; do
  if [ -z "${!v}" ] || [ "${!v}" = "__FILL_ME__" ]; then missing+=("$v"); fi
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "ERROR: required placeholder(s) not filled: ${missing[*]}" >&2
  echo "       Edit scripts/hpc/run_pipeline.slurm or export RH_ACCOUNT, RH_PARTITION," >&2
  echo "       RH_TIME_LIMIT, RH_GPU. There is no default account, partition, time or GPU." >&2
  exit 2
fi
if [ ! -x "$PY" ]; then
  echo "ERROR: $PY not found: run 'bash scripts/hpc/setup_env.sh' in the repository first" >&2
  exit 2
fi

VARIANT_ARGS=()
if [ -n "$VARIANT" ]; then VARIANT_ARGS=(--variant "$VARIANT"); fi

# the configuration decides the backend and the thread count; check them against the request
read -r BACKEND THREADS < <("$PY" - "$CONFIG" "$VARIANT" <<'EOF'
import sys
from reflection_holo.pipeline.config import load_pipeline_file
cfg = load_pipeline_file(sys.argv[1], variant=sys.argv[2] or None)
eng = cfg.value("engine", "name")
backend = cfg.value("engine", "multislice")["backend"] if eng == "multislice" else "none"
print(backend, cfg.value("runtime", "threads"))
EOF
)
if [ "$BACKEND" = "cupy" ] && [ "$GPU" = "none" ]; then
  echo "ERROR: the configuration uses the cupy backend but GPU=none; request a GPU or use" >&2
  echo "       RH_VARIANT=cpu_numpy for demo_hpc_si001.yaml" >&2
  exit 2
fi
if [ "$CPUS" -lt "$THREADS" ]; then
  echo "ERROR: cpus-per-task $CPUS < runtime.threads $THREADS of $CONFIG" >&2
  exit 2
fi

if [ -z "${SLURM_JOB_ID:-}" ]; then
  # submission mode: submit this file with the filled options
  GRES=()
  if [ "$GPU" != "none" ]; then GRES=(--gres="$GPU"); fi
  exec sbatch --account="$ACCOUNT" --partition="$PARTITION" --time="$TIME_LIMIT" "${GRES[@]}" \
       --cpus-per-task="$CPUS" --mem="$MEM" \
       --export=ALL,RH_ACCOUNT="$ACCOUNT",RH_PARTITION="$PARTITION",RH_TIME_LIMIT="$TIME_LIMIT",RH_GPU="$GPU",RH_MODE="$MODE",RH_CONFIG="$CONFIG",RH_VARIANT="$VARIANT",RH_REPO="$REPO",RH_CPUS="$CPUS" \
       "$0"
fi

# ---- job mode ----------------------------------------------------------------------------------
cd "$REPO"
export OMP_NUM_THREADS="$THREADS" OPENBLAS_NUM_THREADS="$THREADS" MKL_NUM_THREADS="$THREADS" \
       NUMEXPR_NUM_THREADS="$THREADS"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NAME="$(basename "$CONFIG" .yaml)${VARIANT:+_$VARIANT}"
OUT="${RH_OUT:-outputs/pipeline/${NAME}_${SLURM_JOB_ID}_${STAMP}}"
echo "job ${SLURM_JOB_ID} on $(hostname): mode=$MODE config=$CONFIG variant=${VARIANT:-none}"
echo "account=$ACCOUNT partition=$PARTITION time=$TIME_LIMIT gpu=$GPU threads=$THREADS out=$OUT"
if [ "$GPU" != "none" ] && command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi; fi
"$PY" -m reflection_holo.pipeline list-inputs --config "$CONFIG" "${VARIANT_ARGS[@]}"
"$PY" -m reflection_holo.pipeline dry-run --config "$CONFIG" "${VARIANT_ARGS[@]}" | head -12
"$PY" -m reflection_holo.pipeline run --config "$CONFIG" "${VARIANT_ARGS[@]}" --out "$OUT"
status=$?
if [ -f "reflholo_${SLURM_JOB_ID}.log" ]; then cp "reflholo_${SLURM_JOB_ID}.log" "$OUT/" || true; fi
echo "finished with status $status; outputs in $OUT"
exit $status
