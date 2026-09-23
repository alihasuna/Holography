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
SCRIPT="$(readlink -f "$0")"                # absolute: the script may be launched from anywhere

# ---- REQUIRED (no defaults) -----------------------------------------------------------------
ACCOUNT="${RH_ACCOUNT:-__FILL_ME__}"        # your SLURM account
PARTITION="${RH_PARTITION:-__FILL_ME__}"    # partition (GPU partition for the multislice run)
TIME_LIMIT="${RH_TIME_LIMIT:-__FILL_ME__}"  # wall time, e.g. 02:00:00
GPU="${RH_GPU:-__FILL_ME__}"                # GPU request, e.g. gpu:1 or gpu:a100:1; "none" = CPU only
# ---- run selection (explicit; change as needed) -----------------------------------------------
MODE="${RH_MODE:-full}"                     # smoke | full
# cpus-per-task; must be >= runtime.threads of the config. Inside a job submitted directly with
# sbatch --cpus-per-task=N (no RH_CPUS), N is used (audit A3 m6).
CPUS="${RH_CPUS:-${SLURM_CPUS_PER_TASK:-8}}"
MEM="${RH_MEM:-32G}"
if [ "$MODE" = "smoke" ]; then
  CONFIG="${RH_CONFIG:-configs/demo_smoke_si001.yaml}"
  VARIANT="${RH_VARIANT:-}"
else
  CONFIG="${RH_CONFIG:-configs/demo_hpc_si001.yaml}"
  VARIANT="${RH_VARIANT:-}"                 # "" = GPU (cupy) run; cpu_numpy = CPU-only run
fi
REPO="$(cd "${RH_REPO:-$(pwd)}" && pwd)"    # absolute
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

# the manifest must identify the code: check the git state before submitting and before any
# computation (audit A3 M5); RH_ALLOW_NO_GIT=1 records the package-tree hash instead
NOGIT_ARGS=()
if ! git -C "$REPO" rev-parse HEAD >/dev/null 2>&1; then
  if [ "${RH_ALLOW_NO_GIT:-0}" = "1" ]; then
    echo "WARNING: $REPO has no usable git state; RH_ALLOW_NO_GIT=1: the run records the failure" >&2
    echo "         and the package-tree hash in its manifest" >&2
    NOGIT_ARGS=(--allow-no-git)
  else
    echo "ERROR: $REPO has no usable git state (git rev-parse HEAD failed); the pipeline would" >&2
    echo "       refuse the run. Run from a git clone, or export RH_ALLOW_NO_GIT=1 to record the" >&2
    echo "       package-tree hash instead (audit A3 M5)." >&2
    exit 2
  fi
fi

VARIANT_ARGS=()
if [ -n "$VARIANT" ]; then VARIANT_ARGS=(--variant "$VARIANT"); fi
# relative config paths are relative to the repository, in both modes (audit A3 m6)
cd "$REPO"

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
# cupy pre-flight (audit A3 m5): the pipeline refuses a cupy run without an importable cupy and a
# visible GPU (exit 4, before computing). Submission host: a warning only (login nodes often lack
# CUDA); inside the job: checked before any step, so a missing cupy costs seconds, not the dry run.
if [ "$BACKEND" = "cupy" ]; then
  if [ -z "${SLURM_JOB_ID:-}" ]; then
    if ! "$PY" -c "import cupy" >/dev/null 2>&1; then
      echo "WARNING: 'import cupy' fails with $PY on this host; the job will be refused on the" >&2
      echo "         GPU node (exit 4) unless cupy is installed there (scripts/hpc/setup_env.sh)" >&2
    fi
  elif ! "$PY" -c "import sys, cupy; sys.exit(0 if cupy.cuda.runtime.getDeviceCount() > 0 else 1)"; then
    echo "ERROR: the configuration uses the cupy backend but cupy is not importable or sees no" >&2
    echo "       GPU on $(hostname); nothing was computed" >&2
    exit 4
  fi
fi

if [ -z "${SLURM_JOB_ID:-}" ]; then
  # submission mode: submit this file with the filled options
  GRES=()
  if [ "$GPU" != "none" ]; then GRES=(--gres="$GPU"); fi
  exec sbatch --account="$ACCOUNT" --partition="$PARTITION" --time="$TIME_LIMIT" "${GRES[@]}" \
       --cpus-per-task="$CPUS" --mem="$MEM" \
       --export=ALL,RH_ACCOUNT="$ACCOUNT",RH_PARTITION="$PARTITION",RH_TIME_LIMIT="$TIME_LIMIT",RH_GPU="$GPU",RH_MODE="$MODE",RH_CONFIG="$CONFIG",RH_VARIANT="$VARIANT",RH_REPO="$REPO",RH_CPUS="$CPUS",RH_ALLOW_NO_GIT="${RH_ALLOW_NO_GIT:-0}" \
       "$SCRIPT"
fi

# ---- job mode ----------------------------------------------------------------------------------
export OMP_NUM_THREADS="$THREADS" OPENBLAS_NUM_THREADS="$THREADS" MKL_NUM_THREADS="$THREADS" \
       NUMEXPR_NUM_THREADS="$THREADS"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NAME="$(basename "$CONFIG" .yaml)${VARIANT:+_$VARIANT}"
OUT="${RH_OUT:-outputs/pipeline/${NAME}_${SLURM_JOB_ID}_${STAMP}}"
echo "job ${SLURM_JOB_ID} on $(hostname): mode=$MODE config=$CONFIG variant=${VARIANT:-none}"
echo "account=$ACCOUNT partition=$PARTITION time=$TIME_LIMIT gpu=$GPU threads=$THREADS out=$OUT"
if [ "$GPU" != "none" ] && command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi; fi
"$PY" -m reflection_holo.pipeline list-inputs --config "$CONFIG" "${VARIANT_ARGS[@]}"
# dry-run output goes to a file first: piping into head under `set -o pipefail` failed at random
# (SIGPIPE on the writer; audit A3 M4)
DRYRUN_TXT="reflholo_${SLURM_JOB_ID}_dryrun.txt"
set +e
"$PY" -m reflection_holo.pipeline dry-run --config "$CONFIG" "${VARIANT_ARGS[@]}" > "$DRYRUN_TXT"
dstatus=$?
set -e
head -n 12 "$DRYRUN_TXT"
if [ "$dstatus" -ne 0 ]; then
  echo "dry-run failed with status $dstatus (see $DRYRUN_TXT); the run was not started" >&2
  exit "$dstatus"
fi
set +e
"$PY" -m reflection_holo.pipeline run --config "$CONFIG" "${VARIANT_ARGS[@]}" "${NOGIT_ARGS[@]}" --out "$OUT"
status=$?
set -e
if [ -d "$OUT" ]; then cp "$DRYRUN_TXT" "$OUT/" || true; fi
if [ -f "reflholo_${SLURM_JOB_ID}.log" ]; then cp "reflholo_${SLURM_JOB_ID}.log" "$OUT/" || true; fi
echo "finished with status $status; outputs in $OUT"
exit $status
