#!/bin/bash
# One-time setup of the reflection-holography environment on an Alliance LOGIN node.
#
#   cd <your clone>      # e.g. $HOME/Holography (see README_ALLIANCE.md for why $HOME)
#   bash scripts/hpc/alliance/setup_alliance.sh <cluster> [--recreate]
#        [--python-module python/3.11.5] [--cuda-module cuda/12.6] [--cupy-spec cupy==14.1.0]
#        [--abtem-wheel PATH] [--allow-cupy-import-failure]
#
# cluster: fir | nibi | rorqual | narval | trillium (one clone and one setup per cluster).
# What it does, failing loudly at the first problem (set -e; no fallback anywhere):
#   1. module purge; module load StdEnv/2023, python/3.11.5, cuda/12.6 (clusters.yaml "common"
#      for the locators) and checks that each is loaded;
#   2. virtualenv --no-download venv; pip install --no-index --upgrade pip (Python § Creating and
#      using a virtual environment);
#   3. pip install --no-index from the Alliance wheelhouse: numpy, pyyaml, scipy, matplotlib,
#      pytest, setuptools, cupy and every requirement of abTEM 1.0.10 (avail_wheels output kept);
#   4. abTEM 1.0.10 is NOT in the wheelhouse: pip download --no-deps --only-binary=:all: on this
#      login node (Python § Pre-downloading packages), file name must end in none-any, SHA-256
#      checked against PyPI (34e09866...), then pip install --no-index <wheel>;
#   5. pip install --no-index --no-build-isolation -e ".[test]" (our package; editable, so that
#      the manifests find the git state), then pip check;
#   6. import check (numpy, scipy, yaml, abtem Kirkland, reflection_holo, cupy) and a short test
#      subset that needs no GPU (about one minute, 4 threads);
#   7. records in venv/alliance/: modules.sh (the load sequence every job repeats), module_list.txt
#      (`module -t list`, compared by every job), env.json, pip_freeze.txt, package_sources.tsv
#      (which package came from where), pip reports, avail_wheels.txt, the setup log.
# Exit status: 0 ready; 2 refused (wrong place, no module command, venv exists, ...); other = the
# failing command's status.
set -euo pipefail

die() { local st=$1; shift; echo "ERROR: $*" >&2; exit "$st"; }

CLUSTERS="fir nibi rorqual narval trillium"
[ $# -ge 1 ] || die 2 "usage: setup_alliance.sh <cluster> [options]; clusters: $CLUSTERS"
CLUSTER="$1"; shift
case " $CLUSTERS " in *" $CLUSTER "*) ;; *) die 2 "unknown cluster '$CLUSTER'; clusters: $CLUSTERS (Cedar is retired)" ;; esac
# module versions: clusters.yaml "common" (Trillium_Quickstart § Example: Single-GPU Job loads
# exactly StdEnv/2023, cuda/12.6, python/3.11.5; Wheels3.11 has cupy 14.1.0)
STDENV_MOD="StdEnv/2023"
PY_MOD="python/3.11.5"
CUDA_MOD="cuda/12.6"
CUPY_SPEC="cupy==14.1.0"
ABTEM_WHEEL_NAME="abtem-1.0.10-py3-none-any.whl"
ABTEM_SHA256="34e098662a26cedebd0154ae0660c49efb6149cba161a605f02ecf381f45515d"
ABTEM_WHEEL=""
RECREATE=0
ALLOW_CUPY_FAIL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --recreate) RECREATE=1; shift ;;
    --allow-cupy-import-failure) ALLOW_CUPY_FAIL=1; shift ;;
    --python-module) [ $# -ge 2 ] || die 2 "$1 needs a value"; PY_MOD="$2"; shift 2 ;;
    --cuda-module) [ $# -ge 2 ] || die 2 "$1 needs a value"; CUDA_MOD="$2"; shift 2 ;;
    --cupy-spec) [ $# -ge 2 ] || die 2 "$1 needs a value"; CUPY_SPEC="$2"; shift 2 ;;
    --abtem-wheel) [ $# -ge 2 ] || die 2 "$1 needs a value"; ABTEM_WHEEL="$2"; shift 2 ;;
    *) die 2 "unknown option $1" ;;
  esac
done

# ---- where we are -----------------------------------------------------------------------------
type module >/dev/null 2>&1 || die 2 "the 'module' command is not available: run this on an Alliance login node, in a login shell (Lmod provides 'module')"
if ! { [ -f pyproject.toml ] && grep -q '^name = "reflection_holo"' pyproject.toml; }; then
  die 2 "run from the repository root (the directory with pyproject.toml of reflection_holo)"
fi
REPO="$(pwd -P)"
git rev-parse HEAD >/dev/null 2>&1 || die 2 "$REPO is not a git clone (git rev-parse HEAD failed): the manifests need the git state"
grep -q "^  $CLUSTER:" scripts/hpc/alliance/clusters.yaml || die 2 "$CLUSTER has no profile in clusters.yaml"
[ -z "${SLURM_JOB_ID:-}" ] || echo "WARNING: SLURM_JOB_ID is set: this setup is meant for a login node" >&2
if [ -e venv ]; then
  [ "$RECREATE" -eq 1 ] || die 2 "venv/ exists; rerun with --recreate to delete and rebuild it"
  rm -rf venv
fi
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$REPO/alliance_setup_${CLUSTER}_${STAMP}.log"     # gitignored (alliance_setup_*.log)
exec > >(tee -a "$LOG") 2>&1
echo "== setup_alliance.sh $CLUSTER on $(hostname) at $STAMP; repository $REPO ($(git rev-parse HEAD))"

# ---- 1. modules -------------------------------------------------------------------------------
# Lmod's module function is not guaranteed to be `set -u` clean: call it through mod()
mod() { local st=0; set +u; module "$@" || st=$?; set -u; return "$st"; }
# no `| grep -q` under pipefail (an early-closing reader can fail the writer: audit A3 M4)
loaded() {
  local l
  l="$(mod -t list 2>&1)"
  case $'\n'"$l"$'\n' in *$'\n'"$1"$'\n'*) return 0 ;; esac
  return 1
}
mod purge || die 2 "module purge failed"
for m in "$STDENV_MOD" "$PY_MOD" "$CUDA_MOD"; do
  echo "== module load $m"
  mod load "$m" || die 2 "module load $m failed (module spider ${m%%/*})"
  loaded "$m" || die 2 "module $m is not loaded after 'module load $m' (module spider ${m%%/*})"
done
python -c 'import sys; assert sys.version_info >= (3, 11), sys.version; print("python", sys.version)'
command -v virtualenv >/dev/null 2>&1 || die 2 "virtualenv not found after loading $PY_MOD"
command -v avail_wheels >/dev/null 2>&1 || die 2 "avail_wheels not found (Python § Available wheels)"

# ---- 2. virtual environment -------------------------------------------------------------------
virtualenv --no-download venv
set +u
# shellcheck disable=SC1091
source venv/bin/activate
set -u
export PYTHONNOUSERSITE=1
pip install --no-index --upgrade pip
A=venv/alliance
mkdir -p "$A/wheels"

# ---- 3. wheelhouse packages -------------------------------------------------------------------
cat > "$A/requirements_wheelhouse.txt" <<EOF
# written by setup_alliance.sh; installed with pip install --no-index (Alliance wheelhouse only)
# reflection_holo (pyproject.toml) and its tests
numpy>=2.0
pyyaml>=6.0
pytest>=8
setuptools>=68
wheel
# numpy backend of the multislice engine (scipy.fft) and optional PNG quicklooks
scipy
matplotlib>=3.6
# cupy backend (Available_Python_wheels, Wheels3.11: 14.1.0)
$CUPY_SPEC
# requirements of abTEM 1.0.10 (requires_dist of https://pypi.org/pypi/abtem/1.0.10/json)
numba
pandas
pyfftw
dask!=2025.12.*,!=2026.1.0,!=2026.1.1,>=2022.12.1
distributed
zarr>=3.1
ase
threadpoolctl
tabulate
ipywidgets
ipympl
tqdm
EOF
grep -v '^#' "$A/requirements_wheelhouse.txt" | sed -e 's/[<>=!].*$//' > "$A/wheel_names.txt"
echo "== avail_wheels -r $A/wheel_names.txt   (a record of what the wheelhouse offers here)"
AVAIL_STATUS="OK"
if ! avail_wheels -r "$A/wheel_names.txt" > "$A/avail_wheels.txt" 2>&1; then
  # a record only: the pip install below is the check, and it fails loudly on a missing wheel
  AVAIL_STATUS="FAILED (see avail_wheels.txt)"
  echo "WARNING: avail_wheels failed; the pip install below decides (output: $A/avail_wheels.txt)" >&2
fi
cat "$A/avail_wheels.txt"
pip install --no-index --report "$A/pip_report_wheelhouse.json" -r "$A/requirements_wheelhouse.txt"

# ---- 4. abTEM 1.0.10 (pre-downloaded wheel) ---------------------------------------------------
if [ -n "$ABTEM_WHEEL" ]; then
  [ "$(basename "$ABTEM_WHEEL")" = "$ABTEM_WHEEL_NAME" ] || die 2 "--abtem-wheel must be $ABTEM_WHEEL_NAME"
  cp "$ABTEM_WHEEL" "$A/wheels/"
else
  echo "== pip download --no-deps --only-binary=:all: abtem==1.0.10 (login node, Python § Pre-downloading packages)"
  (cd "$A/wheels" && pip download --no-deps --only-binary=:all: "abtem==1.0.10") || \
    die 2 "pip download of abtem failed (no PyPI access from this login node?). Copy $ABTEM_WHEEL_NAME here and rerun with --recreate --abtem-wheel PATH"
fi
[ -f "$A/wheels/$ABTEM_WHEEL_NAME" ] || die 2 "expected $A/wheels/$ABTEM_WHEEL_NAME (a none-any wheel); got: $(ls "$A/wheels")"
GOT="$(sha256sum "$A/wheels/$ABTEM_WHEEL_NAME" | cut -d' ' -f1)"
[ "$GOT" = "$ABTEM_SHA256" ] || die 2 "SHA-256 of $ABTEM_WHEEL_NAME is $GOT, PyPI says $ABTEM_SHA256"
echo "abtem wheel SHA-256 verified: $GOT"
pip install --no-index --report "$A/pip_report_abtem.json" "$A/wheels/$ABTEM_WHEEL_NAME"

# ---- 5. this repository ---------------------------------------------------------------------
pip install --no-index --no-build-isolation --report "$A/pip_report_repo.json" -e ".[test]"
pip check
pip freeze --all > "$A/pip_freeze.txt"
python - "$A" <<'EOF'
import json, sys
from importlib import metadata
from pathlib import Path
A = Path(sys.argv[1])
src = {}
for rep, label in (("pip_report_wheelhouse.json", "Alliance wheelhouse (pip --no-index)"),
                   ("pip_report_abtem.json", "PyPI wheel pre-downloaded on the login node, SHA-256 checked"),
                   ("pip_report_repo.json", "this repository (editable)")):
    for it in json.loads((A / rep).read_text()).get("install", []):
        name = it["metadata"]["name"].lower().replace("_", "-")
        src[name] = (label, (it.get("download_info") or {}).get("url", ""))
rows = []
for d in metadata.distributions():
    name = d.metadata["Name"]
    key = name.lower().replace("_", "-")
    label, url = src.get(key, ("present before the installs (virtualenv seed)", ""))
    rows.append((name, d.version, label, url))
rows.sort(key=lambda r: r[0].lower())
with open(A / "package_sources.tsv", "w") as fh:
    fh.write("package\tversion\tsource\turl\n")
    for r in rows:
        fh.write("\t".join(r) + "\n")
not_wh = [r for r in rows if not r[2].startswith("Alliance wheelhouse")]
print(f"{len(rows)} packages; not from the wheelhouse: " + ", ".join(f"{r[0]} {r[1]} ({r[2]})" for r in not_wh))
EOF

# ---- 6. checks ----------------------------------------------------------------------------------
python - <<'EOF'
import numpy, scipy, yaml, abtem, reflection_holo
from abtem.parametrizations import KirklandParametrization
from reflection_holo.pipeline.engines import multislice_status
KirklandParametrization().projected_scattering_factor("Si")
print("reflection_holo", reflection_holo.__version__, "numpy", numpy.__version__, "scipy",
      scipy.__version__, "abtem", abtem.__version__)
print("multislice engine:", multislice_status())
EOF
CUPY_STATUS="OK"
if ! python -c "import cupy; print('cupy', cupy.__version__, 'imported (a GPU is not needed on the login node)')"; then
  if [ "$ALLOW_CUPY_FAIL" -eq 1 ]; then
    CUPY_STATUS="FAILED on the login node (--allow-cupy-import-failure); the gpu-check job decides"
    echo "WARNING: $CUPY_STATUS" >&2
  else
    die 2 "'import cupy' failed on this login node. If the error names the NVIDIA driver (libcuda), the login node may simply have no GPU driver: rerun with --recreate --allow-cupy-import-failure and let the gpu-check job decide"
  fi
fi
python -c "import cupy; print('CUDA runtime seen by cupy:', cupy.cuda.runtime.runtimeGetVersion())" || \
  echo "NOTE: cupy.cuda.runtime.runtimeGetVersion() failed here (no GPU/driver on the login node?); the gpu-check job records it" >&2
echo "== test subset (no GPU; login-node friendly: 4 threads)"
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
python -m pytest -q -p no:cacheprovider tests/test_frames.py tests/io tests/provenance tests/geometry \
  tests/structure tests/forward/test_cell.py tests/forward/test_vacuum_propagation.py \
  tests/forward/test_potential_atomic.py tests/forward_geometric tests/optics tests/reconstruction \
  tests/quantification tests/pipeline/test_pipeline_geometric.py tests/pipeline/test_a3_priority3.py \
  tests/hpc -k "not test_gpu_check_pass_record_with_fake_cupy"

# ---- 7. records -------------------------------------------------------------------------------
mod -t list > "$A/module_list.txt" 2>&1
cat > "$A/modules.sh" <<EOF
# written by setup_alliance.sh on $STAMP for $CLUSTER; sourced by submit.sh and by every job
# (Running_jobs § Troubleshooting > Jobs inherit environment variables: module purge first)
module purge
module load $STDENV_MOD
module load $PY_MOD
module load $CUDA_MOD
EOF
FREEZE_SHA="$(sha256sum "$A/pip_freeze.txt" | cut -c1-12)"
ENV_ID="${CLUSTER}-${STAMP}-${FREEZE_SHA}"
python - "$A" "$CLUSTER" "$ENV_ID" "$STDENV_MOD" "$PY_MOD" "$CUDA_MOD" "$CUPY_STATUS" "$GOT" "$LOG" "$AVAIL_STATUS" <<'EOF'
import datetime, json, platform, socket, subprocess, sys
from pathlib import Path
A, cluster, env_id, stdenv, pymod, cudamod, cupy_status, abtem_sha, log, avail = sys.argv[1:]
rec = dict(schema="reflholo_alliance_env/1", cluster=cluster, env_id=env_id,
           created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           host=socket.gethostname(), modules=dict(stdenv=stdenv, python=pymod, cuda=cudamod),
           module_list=(Path(A) / "module_list.txt").read_text().split(),
           python=sys.version, platform=platform.platform(),
           repository_commit=subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
           cupy_import_on_login=cupy_status, abtem_wheel_sha256=abtem_sha, setup_log=log,
           avail_wheels=avail,
           setup_complete=True)
(Path(A) / "env.json").write_text(json.dumps(rec, indent=1))
print("environment id", env_id)
EOF
cp "$LOG" "$A/setup.log"
echo "== DONE: environment $ENV_ID ready in $REPO/venv (records in $A)."
echo "   Next: bash scripts/hpc/alliance/submit.sh $CLUSTER gpu-check --account <RAP> --time <limit> --dry-run"
