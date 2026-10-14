#!/bin/bash
# Submit the whole campaign as a dependency chain (run on a Fir login node from the
# repository root, after `bash fir/setup_env.sh`):
#
#   export FIR_ACCOUNT=def-<pi>          # your GPU allocation, required
#   bash fir/submit_campaign.sh $SCRATCH/rh_m2_v1
#
# Chain: selftest (1 GPU) -> validation -> convergence -> rocking -> steps (4 GPUs each).
# Each stage starts only if the previous one succeeded (afterok); validation and
# convergence fail if their verdicts fail.  Walltimes below are generous upper bounds
# from fir/README.md; adjust after the self-test prints its cost estimate.
set -euo pipefail
: "${FIR_ACCOUNT:?set FIR_ACCOUNT to your Slurm account, e.g. def-<pi> or rrg-<pi>-ac}"
RUN_DIR=${1:?usage: submit_campaign.sh RUN_DIR}
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO"
source fir/env.sh
mkdir -p "$RUN_DIR"
git rev-parse HEAD > "$RUN_DIR/repository_commit.txt"
git status --porcelain > "$RUN_DIR/repository_status.txt"
cp configs/fir_m2_campaign.yaml configs/benchmarks.yaml "$RUN_DIR/"
pip freeze > "$RUN_DIR/pip-freeze.txt"

echo "planning tasks (dry geometric check of every task) ..."
python -m reflection_holo.campaign plan --config configs/fir_m2_campaign.yaml --stage all --out "$RUN_DIR"

T_VALIDATION=${T_VALIDATION:-02:00:00}
T_CONVERGENCE=${T_CONVERGENCE:-03:00:00}
T_ROCKING=${T_ROCKING:-08:00:00}
T_STEPS=${T_STEPS:-08:00:00}

j0=$(sbatch --parsable --account="$FIR_ACCOUNT" fir/selftest.sbatch "$RUN_DIR")
j1=$(sbatch --parsable --account="$FIR_ACCOUNT" --time="$T_VALIDATION" --dependency=afterok:$j0 \
     --job-name=rh-validation fir/run_stage.sbatch "$RUN_DIR" validation)
j2=$(sbatch --parsable --account="$FIR_ACCOUNT" --time="$T_CONVERGENCE" --dependency=afterok:$j1 \
     --job-name=rh-convergence fir/run_stage.sbatch "$RUN_DIR" convergence)
j3=$(sbatch --parsable --account="$FIR_ACCOUNT" --time="$T_ROCKING" --dependency=afterok:$j2 \
     --job-name=rh-rocking fir/run_stage.sbatch "$RUN_DIR" rocking)
j4=$(sbatch --parsable --account="$FIR_ACCOUNT" --time="$T_STEPS" --dependency=afterok:$j3 \
     --job-name=rh-steps fir/run_stage.sbatch "$RUN_DIR" steps)
echo "submitted: selftest $j0, validation $j1, convergence $j2, rocking $j3, steps $j4"
echo "$j0 $j1 $j2 $j3 $j4" > "$RUN_DIR/job_ids.txt"
