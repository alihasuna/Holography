# Sourced by every Fir job script and by setup_env.sh.
# Module names follow the Alliance software stack (StdEnv/2023). If a version below
# is not available on Fir, `module spider python` / `module spider cuda` lists the
# installed ones; override with RH_PYTHON_MODULE / RH_CUDA_MODULE.
RH_PYTHON_MODULE=${RH_PYTHON_MODULE:-python/3.11}
RH_CUDA_MODULE=${RH_CUDA_MODULE:-cuda}
RH_ENV_DIR=${RH_ENV_DIR:-$HOME/envs/reflection_holo}
# start from a clean module set: modules loaded by the login profile (for example
# jupyterlab-apps) must not leak into the environment build or the jobs
module purge
module load StdEnv/2023 "$RH_PYTHON_MODULE" "$RH_CUDA_MODULE"
if [ -f "$RH_ENV_DIR/bin/activate" ]; then
    source "$RH_ENV_DIR/bin/activate"
fi
export CUPY_CACHE_DIR=${CUPY_CACHE_DIR:-$HOME/.cupy/kernel_cache}
# one host thread per worker is enough: the work is on the GPU
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}
export PYTHONUNBUFFERED=1
