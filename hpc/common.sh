# Sourced by the job scripts: modules, virtualenv, threads, output location.
module load StdEnv/2023 python/3.11 cuda
source "${HOLO_VENV:-$HOME/venvs/holo}/bin/activate"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export HOLO_OUT=${HOLO_OUT:-$SCRATCH/holo_outputs}
mkdir -p "$HOLO_OUT" logs
echo "host $(hostname)  job ${SLURM_JOB_ID:-local}  commit $(git rev-parse --short HEAD)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
