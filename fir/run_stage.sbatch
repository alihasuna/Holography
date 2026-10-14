#!/bin/bash
#SBATCH --job-name=rh-stage
#SBATCH --gpus-per-node=h100:4
#SBATCH --cpus-per-task=48
#SBATCH --mem=480G
#SBATCH --output=%x-%j.out
# One campaign stage on one full Fir GPU node: four workers, one per H100, pulling
# tasks from RUN_DIR/tasks_<stage>.jsonl.  Restartable: finished tasks are skipped,
# stale claims of dead jobs are removed at start.  If tasks remain when the time
# limit approaches, the job resubmits itself (up to RH_MAX_RESUBMIT times).
# When the stage is complete it is aggregated; the validation and convergence
# stages exit non-zero if their verdict fails, so that dependent stages do not start.
#
# Usage (repository root):
#   sbatch --account=$FIR_ACCOUNT --time=08:00:00 fir/run_stage.sbatch RUN_DIR STAGE
set -euo pipefail
RUN_DIR=${1:?usage: run_stage.sbatch RUN_DIR STAGE}
STAGE=${2:?usage: run_stage.sbatch RUN_DIR STAGE}
RH_MAX_RESUBMIT=${RH_MAX_RESUBMIT:-8}
RH_RESUBMIT_COUNT=${RH_RESUBMIT_COUNT:-0}
cd "${SLURM_SUBMIT_DIR:-$(pwd)}"
source fir/env.sh
nvidia-smi -L

python -m reflection_holo.worker clean --run-dir "$RUN_DIR"

# deadline: job end minus a safety margin (seconds)
END=$(squeue -h -j "$SLURM_JOB_ID" -o %e)
END_EPOCH=$(date -d "$END" +%s)
DEADLINE=$((END_EPOCH - ${RH_MARGIN_SECONDS:-900}))

IFS=',' read -ra GPUS <<< "${CUDA_VISIBLE_DEVICES:-0,1,2,3}"
NW=${#GPUS[@]}
pids=()
for i in $(seq 0 $((NW - 1))); do
    CUDA_VISIBLE_DEVICES=${GPUS[$i]} OMP_NUM_THREADS=$((SLURM_CPUS_PER_TASK / NW)) \
        python -m reflection_holo.worker run --run-dir "$RUN_DIR" --stage "$STAGE" \
        --worker-index "$i" --deadline "$DEADLINE" &
    pids+=($!)
done
for p in "${pids[@]}"; do wait "$p" || true; done

python -m reflection_holo.worker status --run-dir "$RUN_DIR" --stage "$STAGE" | tee "$RUN_DIR/status_${STAGE}.txt"
REMAINING=$(python - "$RUN_DIR" "$STAGE" <<'PY'
import json, os, sys, glob
run, stage = sys.argv[1], sys.argv[2]
tasks = [json.loads(l) for l in open(os.path.join(run, f"tasks_{stage}.jsonl")) if l.strip()]
def failed_twice(tid):
    return len(glob.glob(os.path.join(run, "failed", f"{tid}.*.txt"))) >= 2
left = [t for t in tasks if not os.path.exists(os.path.join(run, "results", stage, t["task_id"] + ".h5"))
        and not failed_twice(t["task_id"])]
print(len(left))
PY
)
if [ "$REMAINING" -gt 0 ]; then
    if [ "$RH_RESUBMIT_COUNT" -lt "$RH_MAX_RESUBMIT" ]; then
        echo "$REMAINING tasks remain: resubmitting"
        NEW=$(sbatch --parsable --account="$SLURM_JOB_ACCOUNT" --job-name="$SLURM_JOB_NAME" \
               --time="$(squeue -h -j "$SLURM_JOB_ID" -o %l)" \
               --export=ALL,RH_RESUBMIT_COUNT=$((RH_RESUBMIT_COUNT + 1)) \
               --dependency=afterany:"$SLURM_JOB_ID" fir/run_stage.sbatch "$RUN_DIR" "$STAGE")
        # move the dependency of the next stage (afterok on this job) to the new job,
        # before this job exits non-zero
        squeue -h -u "$USER" -o "%i %E" | while read -r jid dep; do
            if [[ "$dep" == *"afterok:${SLURM_JOB_ID}"* ]]; then
                scontrol update JobId="$jid" Dependency="afterok:${NEW}" && \
                    echo "dependency of job $jid moved to $NEW"
            fi
        done
        echo "$STAGE continued in job $NEW" >> "$RUN_DIR/job_ids.txt"
        exit 3
    fi
    echo "$REMAINING tasks remain and the resubmission limit is reached"
    exit 4
fi

python -m reflection_holo.aggregate --run-dir "$RUN_DIR" --stage "$STAGE" | tee "$RUN_DIR/aggregate_${STAGE}.txt"
python - "$RUN_DIR" "$STAGE" <<'PY'
import json, sys
run, stage = sys.argv[1], sys.argv[2]
S = json.load(open(f"{run}/summary/{stage}/summary.json"))
if stage == "validation" and not S.get("all_pass"):
    sys.exit("validation ladder FAILED: production stages must not run (see summary.json)")
if stage == "convergence" and not S.get("converged"):
    sys.exit("production numerics NOT converged (see summary.json)")
print(f"stage {stage}: verdict OK")
PY
