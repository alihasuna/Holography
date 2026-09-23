#!/bin/bash
# Submit one of the reflection-holography jobs on an Alliance cluster (run on a LOGIN node).
#
#   bash scripts/hpc/alliance/submit.sh <cluster> <job> --account <RAP> --time <limit> [options]
#
# cluster: fir | nibi | rorqual | narval | trillium          (profiles: clusters.yaml)
# job:     gpu-check   2-minute GPU proof: nvidia-smi, cupy FFT, tiny multislice cupy vs numpy
#          smoke       geometric smoke demo (configs/demo_smoke_si001.yaml), CPU, needs --mem
#          demo-gpu    multislice demo (configs/demo_hpc_si001.yaml), 1 GPU, cupy
#          pipeline    any pipeline configuration: --config PATH [--variant V] (GPU if cupy)
#          torus       scripts/torus/run_torus_multislice.py, trench then ridge, CPU, needs --mem
#          null-study  scripts/hpc/null_test_study, one point per array task (--array=0-16)
#
# REQUIRED, no default:  --account def-xxx|rrg-xxx|rpp-xxx     --time <Slurm time, e.g. 01:00:00>
#                        --mem <size> for CPU jobs
# Options:  --config PATH  --variant NAME         (pipeline jobs)
#           --study PATH  --only POINT  --serial  --array-throttle N   (null-study)
#           --kinds trench,ridge[,flat]           (torus)
#           --gpu-instance full|<MIG size>        (default full: one whole GPU; MIG sizes per
#                                                  cluster in clusters.yaml, e.g. 3g.40gb)
#           --need-gpu-mem-gb X                   (refuse an instance with less GPU memory)
#           --cpus N  --mem SIZE                  (GPU jobs: default = the wiki's recommended
#                                                  cores and memory per GPU instance)
#           --scratch DIR                         (default $SCRATCH; outputs go to DIR/reflholo)
#           --any-account-prefix  --skip-gpu-check-gate
#           --dry-run                             (print the sbatch command, submit nothing)
# Environment: RH_ALLIANCE_ENV_DIR (default <repo>/venv/alliance, written by setup_alliance.sh).
# Exit status: 0 submitted (or printed); 2 refused; 3 configuration refused by the pipeline gate;
# otherwise the status of sbatch.
set -euo pipefail

die() { local st=$1; shift; echo "ERROR: $*" >&2; exit "$st"; }

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$KIT_DIR/../../.." && pwd)"
[ $# -ge 2 ] || die 2 "usage: submit.sh <cluster> <job> --account A --time T [options] [--dry-run] (see the header of $0)"
CLUSTER="$1"; JOB="$2"; shift 2
DRY=0
SCR="${SCRATCH:-}"
PLAN_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --scratch) [ $# -ge 2 ] || die 2 "--scratch needs a directory"; SCR="$2"; shift 2 ;;
    --serial|--any-account-prefix|--skip-gpu-check-gate) PLAN_ARGS+=("$1"); shift ;;
    --account|--time|--config|--variant|--study|--only|--array-throttle|--kinds|--gpu-instance|\
    --need-gpu-mem-gb|--cpus|--mem)
      [ $# -ge 2 ] || die 2 "$1 needs a value"; PLAN_ARGS+=("$1" "$2"); shift 2 ;;
    -h|--help) sed -n '2,32p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) die 2 "unknown option $1 (see the header of $0)" ;;
  esac
done

ENV_DIR="${RH_ALLIANCE_ENV_DIR:-$REPO/venv/alliance}"
[ -f "$ENV_DIR/env.json" ] || die 2 "$ENV_DIR/env.json not found: run 'bash scripts/hpc/alliance/setup_alliance.sh $CLUSTER' on a $CLUSTER login node first"
[ -f "$ENV_DIR/modules.sh" ] || die 2 "$ENV_DIR/modules.sh not found: rerun setup_alliance.sh"
PY="$REPO/venv/bin/python"
[ -x "$PY" ] || die 2 "$PY not found: run setup_alliance.sh first"

# the modules recorded at setup (module purge + the same loads), so that the venv's python runs and
# the job inherits a clean environment
type module >/dev/null 2>&1 || die 2 "the module command is not available (log in to an Alliance login node)"
MODTMP="$(mktemp)"
# a failing `module load` inside modules.sh is caught by the comparison below (with its message)
set +eu
# shellcheck disable=SC1091
source "$ENV_DIR/modules.sh"
module -t list > "$MODTMP" 2>&1
set -eu
if ! "$PY" "$KIT_DIR/kit.py" modules-diff --recorded "$ENV_DIR/module_list.txt" --current "$MODTMP" >/dev/null; then
  rm -f "$MODTMP"
  die 2 "the modules recorded by setup_alliance.sh ($ENV_DIR/modules.sh) could not be loaded as recorded"
fi
rm -f "$MODTMP"

# the manifests must identify the code: refuse before submitting (audit A3 M5)
COMMIT="$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" || \
  die 2 "$REPO has no usable git state (git rev-parse HEAD failed): run from a git clone"
DIRTY="$(git -C "$REPO" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
if [ "$DIRTY" != "0" ]; then
  echo "WARNING: the clone has $DIRTY modified/untracked path(s); the manifests record the diff hash" >&2
fi

[ -n "$SCR" ] || die 2 "\$SCRATCH is not set: pass --scratch <your scratch directory> (Fir: \$HOME/scratch, Fir § Storage; Rorqual: \$HOME/links/scratch, Rorqual/en § Storage)"
[ -d "$SCR" ] || die 2 "scratch directory $SCR does not exist"
RUN_ROOT="$(cd "$SCR" && pwd -P)/reflholo"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RECORD="$RUN_ROOT/submissions/${STAMP}_${CLUSTER}_${JOB}.json"

TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT
set +e
"$PY" "$KIT_DIR/kit.py" plan --cluster "$CLUSTER" --job "$JOB" --repo "$REPO" --env-dir "$ENV_DIR" \
  --run-root "$RUN_ROOT" --commit "$COMMIT" --record "$RECORD" --argv-out "$TMPD/argv" \
  --plan-out "$TMPD/plan.json" ${PLAN_ARGS[@]+"${PLAN_ARGS[@]}"}
pst=$?
set -e
[ "$pst" -eq 0 ] || exit "$pst"
ARGV=()
while IFS= read -r -d '' x; do ARGV+=("$x"); done < "$TMPD/argv"
[ "${#ARGV[@]}" -gt 2 ] && [ "${ARGV[0]}" = "sbatch" ] || die 2 "internal error: empty sbatch command"

echo "sbatch command:"
printf '  %q' "${ARGV[@]}"; echo
if [ "$DRY" -eq 1 ]; then
  echo "DRY RUN: nothing submitted, nothing created (outputs would go to $RUN_ROOT)"
  exit 0
fi
command -v sbatch >/dev/null 2>&1 || die 2 "sbatch not found"
mkdir -p "$RUN_ROOT/logs" "$RUN_ROOT/submissions"
cp "$TMPD/plan.json" "$RECORD"
set +e
OUT="$("${ARGV[@]}" 2>&1)"
sst=$?
set -e
echo "$OUT"
printf '%s\n' "$OUT" > "$RECORD.sbatch_output"
[ "$sst" -eq 0 ] || die "$sst" "sbatch failed (status $sst); record $RECORD"
JOBID="$(printf '%s\n' "$OUT" | sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p')"
echo "submitted: job ${JOBID:-?}; log $RUN_ROOT/logs/; outputs $RUN_ROOT/runs/; record $RECORD"
