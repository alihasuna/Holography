#!/bin/bash
# Build the Python environment ONCE, on a Fir LOGIN node (compute nodes have no
# internet access).  Usage:  bash fir/setup_env.sh
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$REPO/fir/env.sh"
if [ ! -f "$RH_ENV_DIR/bin/activate" ]; then
    virtualenv --no-download "$RH_ENV_DIR"
fi
source "$RH_ENV_DIR/bin/activate"
pip install --no-index --upgrade pip
# Alliance wheelhouse first (--no-index); these builds are tuned for the cluster
pip install --no-index numpy scipy h5py pyyaml matplotlib pytest
if ! pip install --no-index cupy; then
    echo "cupy is not in the wheelhouse for this Python/CUDA; installing the PyPI wheel"
    pip install cupy-cuda12x
fi
# optional: abTEM for the transmission cross-check (validation/abtem_crosscheck.py)
pip install abtem || echo "abTEM not installed (optional cross-check will be skipped)"
pip freeze > "$RH_ENV_DIR/pip-freeze.txt"
python - <<'PY'
import numpy, scipy, h5py, yaml
print("numpy", numpy.__version__, "scipy", scipy.__version__, "h5py", h5py.__version__)
try:
    import cupy
    print("cupy", cupy.__version__, "(the GPU is only visible inside a GPU job)")
except Exception as exc:
    raise SystemExit(f"cupy import failed: {exc}")
PY
echo "environment ready in $RH_ENV_DIR"
