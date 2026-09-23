#!/bin/bash
# Batch script of the Alliance kit. Submitted ONLY by scripts/hpc/alliance/submit.sh, which puts
# every Slurm option on the sbatch command line (account, time, GPU, cpus, memory, output, chdir,
# array) and describes the run in RH_* variables (--export=ALL,RH_...). No #SBATCH defaults here:
# nothing is assumed about the account, the time limit or the GPU.
#
# What every job does (README_ALLIANCE.md):
#   * creates its own directory under $SCRATCH: <run root>/runs/<job>_<jobid>_<UTC stamp>/
#     (arrays: <run root>/runs/<job>_<arrayjobid>/task<NNN>_<jobid>_<UTC stamp>/), never reused;
#   * `module purge`, then loads the modules recorded by setup_alliance.sh and refuses to run if
#     the loaded set differs from the record (Running_jobs § Troubleshooting > Jobs inherit
#     environment variables);
#   * activates the venv and refuses if the environment was rebuilt after submission (env id);
#   * sets OMP/OpenBLAS/MKL/NumExpr threads (bounded by --cpus-per-task), checks the git state
#     BEFORE computing (A3 M5);
#   * GPU jobs: re-checks the gpu-check PASS against the cluster, the environment and the engine
#     code AS IT IS NOW (H4 F9), prints nvidia-smi and checks that cupy sees a GPU before computing;
#   * study jobs: reads only the study copy made at submission, after checking its SHA-256 (H4 F6);
#   * at exit (also on the SIGTERM of a time limit): copies the Slurm log, the submission record
#     and every provenance manifest into the job directory, and writes job_status.txt.
set -euo pipefail

die() { local st=$1; shift; echo "ERROR: $*" >&2; exit "$st"; }

[ -n "${SLURM_JOB_ID:-}" ] || die 2 "job.sbatch runs inside a Slurm job; submit it with scripts/hpc/alliance/submit.sh"
for v in RH_KIT_JOB RH_KIT_CLUSTER RH_REPO RH_ENV_DIR RH_RUN_ROOT RH_KIT_THREADS RH_KIT_CPUS \
         RH_KIT_GPU RH_TIME_LIMIT RH_ACCOUNT RH_ENV_ID RH_GPU_GATE; do
  [ -n "${!v:-}" ] || die 2 "$v is not set: submit with scripts/hpc/alliance/submit.sh"
done
KIT="$RH_REPO/scripts/hpc/alliance"
PY="$RH_REPO/venv/bin/python"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
if [ -n "${SLURM_ARRAY_JOB_ID:-}" ] && [ -n "${SLURM_ARRAY_TASK_ID:-}" ]; then
  JOBDIR="$RH_RUN_ROOT/runs/${RH_KIT_JOB}_${SLURM_ARRAY_JOB_ID}/task$(printf '%03d' "$SLURM_ARRAY_TASK_ID")_${SLURM_JOB_ID}_${STAMP}"
  LOG="$RH_RUN_ROOT/logs/${RH_KIT_JOB}_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"
else
  JOBDIR="$RH_RUN_ROOT/runs/${RH_KIT_JOB}_${SLURM_JOB_ID}_${STAMP}"
  LOG="$RH_RUN_ROOT/logs/${RH_KIT_JOB}_${SLURM_JOB_ID}.log"
fi
mkdir -p "$(dirname "$JOBDIR")"
mkdir "$JOBDIR" || die 2 "$JOBDIR exists: outputs are never overwritten"

# shellcheck disable=SC2329  # invoked by the EXIT trap
finish() {
  local st=$?
  set +e
  mkdir -p "$JOBDIR/manifests"
  # provenance manifests written by the runs (pipeline manifest.json; engine and study manifests
  # under */outputs/manifests/) are copied to one flat folder
  while IFS= read -r -d '' f; do
    rel="${f#"$JOBDIR"/}"
    cp "$f" "$JOBDIR/manifests/${rel//\//__}" || echo "WARNING: could not copy $f" >&2
  done < <(find "$JOBDIR" -path "$JOBDIR/manifests" -prune -o -type f \
             \( -name manifest.json -o -path '*/outputs/manifests/*.json' \) -print0)
  if [ -n "${RH_SUBMISSION_RECORD:-}" ] && [ -f "$RH_SUBMISSION_RECORD" ]; then
    cp "$RH_SUBMISSION_RECORD" "$JOBDIR/submission.json" || echo "WARNING: submission record not copied" >&2
  fi
  printf 'exit_status %s\nend_utc %s\njob %s\n' "$st" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SLURM_JOB_ID" \
    > "$JOBDIR/job_status.txt"
  echo "job ${SLURM_JOB_ID} finished with status $st; outputs in $JOBDIR"
  # the Slurm log is copied last (it is still being written: the lines after this one are missing
  # from the copy; the full log stays in $LOG)
  if [ -f "$LOG" ]; then cp "$LOG" "$JOBDIR/slurm.log" || echo "WARNING: log not copied" >&2
  else echo "WARNING: Slurm log $LOG not found (was --output changed?)" >&2; fi
  exit "$st"
}
trap finish EXIT
trap 'exit 143' TERM
cd "$JOBDIR"
echo "== reflholo kit job ${SLURM_JOB_ID}: ${RH_KIT_JOB} on ${RH_KIT_CLUSTER} ($(hostname)), $(date -u +%FT%TZ)"
echo "   job directory: $JOBDIR"

# ---- modules: exactly the set recorded by setup_alliance.sh -----------------------------------
type module >/dev/null 2>&1 || die 2 "the module command is not available in this job"
[ -f "$RH_ENV_DIR/modules.sh" ] || die 2 "$RH_ENV_DIR/modules.sh missing: rerun setup_alliance.sh"
# a failing `module load` inside modules.sh is caught by the comparison below (exit 7)
set +eu
# shellcheck disable=SC1091
source "$RH_ENV_DIR/modules.sh"
module -t list > "$JOBDIR/module_list.txt" 2>&1
set -eu
"$PY" "$KIT/kit.py" modules-diff --recorded "$RH_ENV_DIR/module_list.txt" \
  --current "$JOBDIR/module_list.txt" || die 7 "module set differs from the setup record"

# ---- Python environment ------------------------------------------------------------------------
set +u
# shellcheck disable=SC1091
source "$RH_REPO/venv/bin/activate"
set -u
export PYTHONNOUSERSITE=1
[ "$(python -c 'import os, sys; print(os.path.realpath(sys.prefix))')" = "$(readlink -f "$RH_REPO/venv")" ] || \
  die 2 "python is not the venv of $RH_REPO"
# the environment the job was submitted against (a setup --recreate while the job waited: refused)
"$PY" "$KIT/kit.py" env-check --env-dir "$RH_ENV_DIR" --env-id "$RH_ENV_ID" || \
  die 2 "environment changed since submission"
CACHE="$RH_RUN_ROOT/cache"
export CUPY_CACHE_DIR="$CACHE/cupy" NUMBA_CACHE_DIR="$CACHE/numba" MPLCONFIGDIR="$CACHE/matplotlib"
mkdir -p "$CUPY_CACHE_DIR" "$NUMBA_CACHE_DIR" "$MPLCONFIGDIR"

# ---- threads: bounded by the allocation ------------------------------------------------------
CPUS="${SLURM_CPUS_PER_TASK:-}"
if [ -z "$CPUS" ] && [ "$RH_KIT_CLUSTER" = "trillium" ]; then
  CPUS="${SLURM_CPUS_ON_NODE:-}"      # Trillium: cores come with the GPU (24 per GPU), not -c
fi
[ -n "$CPUS" ] || die 2 "SLURM_CPUS_PER_TASK is not set (submit.sh passes --cpus-per-task)"
[ "$CPUS" -ge "$RH_KIT_THREADS" ] || die 2 "allocated cpus $CPUS < the $RH_KIT_THREADS threads the run declares"
export OMP_NUM_THREADS="$RH_KIT_THREADS" OPENBLAS_NUM_THREADS="$RH_KIT_THREADS" \
       MKL_NUM_THREADS="$RH_KIT_THREADS" NUMEXPR_NUM_THREADS="$RH_KIT_THREADS"
echo "   threads: $RH_KIT_THREADS (declared by the run) of $CPUS allocated cpus"

# ---- code identity before any computation (A3 M5) --------------------------------------------
COMMIT="$(git -C "$RH_REPO" rev-parse HEAD 2>/dev/null)" || \
  die 2 "$RH_REPO has no usable git state: the manifests could not identify the code; nothing was computed"
if [ -n "${RH_SUBMIT_COMMIT:-}" ] && [ "$COMMIT" != "$RH_SUBMIT_COMMIT" ]; then
  echo "WARNING: HEAD is $COMMIT but was $RH_SUBMIT_COMMIT at submission (the manifests record $COMMIT)" >&2
fi
echo "   commit: $COMMIT"
"$PY" "$KIT/kit.py" job-record --out "$JOBDIR/job_info.json" --extra "commit=$COMMIT" \
  --extra "jobdir=$JOBDIR" --extra "log=$LOG"
scontrol show job "$SLURM_JOB_ID" > "$JOBDIR/scontrol_show_job.txt" 2>&1 || \
  echo "WARNING: scontrol show job failed (see scontrol_show_job.txt)" >&2

# ---- GPU gate, re-checked now (H4 F9): cluster, environment and the engine code as it is now ----
case "$RH_GPU_GATE" in
  pass)
    "$PY" "$KIT/kit.py" gate-check --run-root "$RH_RUN_ROOT" --cluster "$RH_KIT_CLUSTER" \
      --env-id "$RH_ENV_ID" --repo "$RH_REPO" || die 2 "no valid gpu-check PASS at job start"
    ;;
  skipped)
    echo "WARNING: submitted with --skip-gpu-check-gate: the GPU path of this engine code is UNVERIFIED on $RH_KIT_CLUSTER" >&2
    ;;
  none) ;;
  *) die 2 "RH_GPU_GATE=$RH_GPU_GATE is not pass, skipped or none" ;;
esac

# ---- GPU pre-flight ---------------------------------------------------------------------------
if [ "$RH_KIT_GPU" != "none" ]; then
  command -v nvidia-smi >/dev/null 2>&1 || die 4 "nvidia-smi not found on a GPU job ($(hostname))"
  nvidia-smi > "$JOBDIR/nvidia-smi.txt" 2>&1 || die 4 "nvidia-smi failed (see nvidia-smi.txt)"
  cat "$JOBDIR/nvidia-smi.txt"
  if [ "$RH_KIT_JOB" != "gpu-check" ]; then
    python -c "import sys, cupy; n = cupy.cuda.runtime.getDeviceCount(); print('cupy', cupy.__version__, n, 'device(s)'); sys.exit(0 if n > 0 else 1)" \
      || die 4 "cupy is not importable or sees no GPU on $(hostname); nothing was computed"
  fi
fi

# ---- the study copy made at submission (H4 F6): hash-checked, copied here, read from here -----
STUDY_USED=""
case "$RH_KIT_JOB" in
  null-study|gpu-sanity)
    STUDY_USED="$JOBDIR/study_used.yaml"
    "$PY" "$KIT/kit.py" verify-study --study "${RH_STUDY:?}" --sha256 "${RH_STUDY_SHA256:?}" \
      --copy-to "$STUDY_USED" || die 2 "study copy check failed"
    ;;
esac

# ---- the run ----------------------------------------------------------------------------------
status=0
set +e
case "$RH_KIT_JOB" in
  gpu-check)
    python "$KIT/gpu_check.py" --out "$JOBDIR/gpu_check" --threads "$RH_KIT_THREADS" \
      --pass-dir "$RH_RUN_ROOT/gpu_check" --cluster "$RH_KIT_CLUSTER" --env-id "$RH_ENV_ID" \
      --seed 20260923
    status=$?
    ;;
  gpu-sanity)
    python "$KIT/gpu_sanity.py" --out "$JOBDIR/gpu_sanity" --study "$STUDY_USED" \
      --backend cupy --threads "$RH_KIT_THREADS"
    status=$?
    ;;
  smoke|demo-gpu|pipeline)
    # delegated to the audited runner (job mode because SLURM_JOB_ID is set); it prints
    # list-inputs and the dry run, checks cupy again, sets the threads to runtime.threads
    RH_PARTITION=none RH_GPU="$RH_KIT_GPU" RH_MODE=full RH_CONFIG="$RH_CONFIG" \
      RH_VARIANT="${RH_VARIANT:-}" RH_CPUS="$CPUS" RH_OUT="$JOBDIR/pipeline" RH_WORKDIR="$JOBDIR" \
      bash "$RH_REPO/scripts/hpc/run_pipeline.slurm"
    status=$?
    ;;
  dry-run)
    python "$KIT/dry_run_job.py" --config "${RH_CONFIG:?}" --variant "${RH_VARIANT:-}" \
      --repo "$RH_REPO" --out "$JOBDIR/dry_run" --threads "$RH_KIT_THREADS" \
      --backend "${RH_PIPE_BACKEND:-none}"
    status=$?
    ;;
  torus)
    IFS=':' read -r -a KINDS <<< "${RH_TORUS_KINDS:-}"
    [ "${#KINDS[@]}" -gt 0 ] || { echo "ERROR: RH_TORUS_KINDS is empty" >&2; status=2; }
    [ -n "${RH_TORUS_MAX_CPU_S:-}" ] || { echo "ERROR: RH_TORUS_MAX_CPU_S is empty" >&2; status=2; }
    if [ "$status" -eq 0 ]; then
      for k in ${KINDS[@]+"${KINDS[@]}"}; do
        echo "== torus $k (CPU guard ${RH_TORUS_MAX_CPU_S} s, derived from --time $RH_TIME_LIMIT by submit.sh)"
        python "$RH_REPO/scripts/torus/run_torus_multislice.py" --kind "$k" --out "$JOBDIR/torus_$k" \
          --max-cpu-seconds "$RH_TORUS_MAX_CPU_S"
        st=$?
        echo "== torus $k finished with status $st"
        if [ "$st" -ne 0 ] && [ "$status" -eq 0 ]; then status=$st; fi
      done
    fi
    ;;
  null-study)
    case "${RH_STUDY_MODE:?}" in
      array) NAME="$("$PY" "$KIT/kit.py" study-point --study "$STUDY_USED" --index "${SLURM_ARRAY_TASK_ID:?}")" ;;
      only)  NAME="${RH_STUDY_ONLY:?}" ;;
      serial) NAME="" ;;
      *) NAME="__invalid__" ;;
    esac
    if [ "$NAME" = "__invalid__" ] || { [ "$RH_STUDY_MODE" != "serial" ] && [ -z "$NAME" ]; }; then
      echo "ERROR: cannot determine the study point (mode $RH_STUDY_MODE)" >&2; status=2
    elif [ -n "$NAME" ]; then
      echo "== null-study point $NAME"
      python "$RH_REPO/scripts/hpc/null_test_study/run_study.py" --config "$STUDY_USED" \
        --out "$JOBDIR/study" --only "$NAME"
      status=$?
      if [ "$status" -eq 0 ] && [ ! -f "$JOBDIR/study/outputs/null_test_study/$NAME.json" ]; then
        echo "ERROR: run_study.py exited 0 but wrote no result for $NAME" >&2; status=5
      fi
    else
      python "$RH_REPO/scripts/hpc/null_test_study/run_study.py" --config "$STUDY_USED" --out "$JOBDIR/study"
      status=$?
      n="$(find "$JOBDIR/study/outputs/null_test_study" -name '*.json' -type f 2>/dev/null | wc -l)"
      if [ "$status" -eq 0 ] && [ "$n" -ne "${RH_STUDY_N:?}" ]; then
        echo "ERROR: $n results for ${RH_STUDY_N} points" >&2; status=5
      fi
    fi
    ;;
  *)
    echo "ERROR: unknown job $RH_KIT_JOB" >&2; status=2 ;;
esac
set -e
exit "$status"
