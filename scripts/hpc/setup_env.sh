#!/usr/bin/env bash
# Create the virtual environment of the repository on an HPC login node (run from the repo root).
#
#   bash scripts/hpc/setup_env.sh                 # numpy only (geometric engine, CPU multislice)
#   RH_CUPY=cupy-cuda12x bash scripts/hpc/setup_env.sh   # plus cupy for the GPU multislice backend
#
# Python >= 3.11 is required (pyproject.toml). Load your site's Python/CUDA modules first, e.g.
# "module load python/3.11 cuda/12" (site-specific; not done here).
# abTEM 1.0.10 (GPL-3.0-or-later) is installed as an OPTIONAL dependency: the multislice atomic
# potential imports its Kirkland parameterisation lazily (report D3); no abTEM code is copied into
# this repository. matplotlib is optional (PNG quicklooks).
set -euo pipefail
PYTHON="${RH_PYTHON:-python3}"
"$PYTHON" -c 'import sys; assert sys.version_info >= (3, 11), sys.version' || {
  echo "ERROR: Python >= 3.11 required (set RH_PYTHON)" >&2; exit 2; }
if [ ! -d venv ]; then "$PYTHON" -m venv venv; fi
venv/bin/pip install --upgrade pip
venv/bin/pip install -e ".[test]"
venv/bin/pip install "abtem==1.0.10" matplotlib
if [ -n "${RH_CUPY:-}" ]; then
  venv/bin/pip install "${RH_CUPY}"
  venv/bin/python -c "import cupy; print('cupy', cupy.__version__, cupy.cuda.runtime.getDeviceCount(), 'device(s)')" \
    || echo "WARNING: cupy installed but no usable GPU here (normal on a login node)"
fi
venv/bin/python - <<'EOF'
import numpy, reflection_holo
from reflection_holo.pipeline.engines import multislice_status
print("reflection_holo", reflection_holo.__version__, "numpy", numpy.__version__)
print("multislice engine:", multislice_status())
EOF
echo "environment ready: venv/bin/python -m reflection_holo.pipeline --help"
