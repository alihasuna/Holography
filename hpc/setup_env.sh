#!/bin/bash
# One-time environment setup on an Alliance cluster LOGIN node (compute nodes have no internet).
# Usage: bash hpc/setup_env.sh        (from the repository root)
set -euo pipefail
module load StdEnv/2023 python/3.11 cuda      # check exact versions with: module avail python cuda
VENV=${HOLO_VENV:-$HOME/venvs/holo}
virtualenv --no-download "$VENV"
source "$VENV/bin/activate"
pip install --no-index --upgrade pip
pip install --no-index numpy scipy matplotlib pyyaml pytest
# CuPy: prefer the Alliance wheelhouse build; fall back to PyPI if the login node has internet
pip install --no-index cupy || pip install cupy-cuda12x
python -c "import numpy, cupy; print('numpy', numpy.__version__, 'cupy', cupy.__version__)"
echo "environment ready: source $VENV/bin/activate (after the same module load)"
