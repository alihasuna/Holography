#!/bin/bash
# One-time setup of the reflection-holography environment on an Alliance LOGIN node.
#
#   cd <your clone>      # e.g. $HOME/Holography (see README_ALLIANCE.md for why $HOME)
#   bash scripts/hpc/alliance/setup_alliance.sh <cluster> [--recreate]
#        [--python-module python/3.11.5] [--cuda-module cuda/12.6] [--cupy-spec cupy==14.1.0]
#        [--abtem-wheel PATH] [--allow-cupy-import-failure]
#
# cluster: fir | nibi | rorqual | narval | trillium (one clone and one setup per cluster).
# RESUMABLE (H4 F3): each install step leaves a stamp in venv/alliance/steps/ with the inputs it was
# done with; after a failure, fix the cause and rerun the SAME command: completed steps are skipped
# (no reinstall). A stamp made with different inputs (e.g. another --cupy-spec) is refused: then
# --recreate deletes venv/ and starts from scratch. A complete environment is left alone (exit 0);
# a complete environment with another --cuda-module is superseded (new records and env id, no
# reinstall: the CUDA module does not change the installed wheels).
# What it does, failing loudly at the first problem (set -e; no fallback anywhere):
#   1. module purge; module load StdEnv/2023, python/3.11.5, cuda/12.6 (clusters.yaml "common"
#      for the locators) and checks that each is loaded (every run: modules are per shell);
#   2. [stamp venv] virtualenv --no-download venv; pip install --no-index --upgrade pip (Python §
#      Creating and using a virtual environment);
#   3. abTEM 1.0.10 is NOT in the wheelhouse: pip download --no-deps --only-binary=:all: on this
#      login node (Python § Pre-downloading packages), FIRST (before the long install, so that a
#      login node without PyPI access fails early), file name must end in none-any, SHA-256 checked
#      against PyPI (34e09866...); kept in venv/alliance/wheels/ and re-verified on every run;
#   4. [stamp wheelhouse] pip install --no-index from the Alliance wheelhouse: numpy, pyyaml,
#      scipy, matplotlib, pytest, setuptools, cupy and every requirement of abTEM 1.0.10;
#   5. [stamp abtem] pip install --no-index <abTEM wheel>; [stamp repo] pip install --no-index
#      --no-build-isolation -e ".[test]" (our package; editable, so that the manifests find the git
#      state); pip check (every run);
#   6. import check (numpy, scipy, yaml, abtem Kirkland, reflection_holo, cupy) and a CPU physics
#      check of the INSTALLED environment (H4 F1: not tests/hpc, which test the kit): the 200 keV
#      wavelength and constants, tiny multislice runs on numpy (rung 1, vacuum propagation, engine
#      contract), the Kirkland potential through abTEM, the geometric smoke pipeline, the
#      provenance manifest (about 1-2 min on 4 threads; 52 tests);
#   7. records in venv/alliance/: modules.sh (the load sequence every job repeats), module_list.txt
#      (`module -t list`, compared by every job), env.json (written last), pip_freeze.txt,
#      package_sources.tsv (which package came from where), pip reports, avail_wheels.txt, the
#      setup logs (hard links of alliance_setup_<cluster>_<stamp>.log in the repository root).
# Exit status: 0 ready (or already complete); 2 refused (wrong place, no module command, a stamp
# made with other inputs, ...); other = the failing command's status.
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
A=venv/alliance
STEPS="$A/steps"
if [ -e venv ] && [ "$RECREATE" -eq 1 ]; then
  rm -rf venv
fi
if [ -e venv ] && [ ! -f "$STEPS/venv.done" ]; then
  die 2 "venv/ exists but was not made by this setup (or its creation was interrupted): rerun with --recreate"
fi
# what this call asks for (compared with a complete environment's record)
REQUEST="cluster=$CLUSTER stdenv=$STDENV_MOD python=$PY_MOD cuda=$CUDA_MOD cupy=$CUPY_SPEC abtem=$ABTEM_SHA256"
SUPERSEDE=0
if [ -f "$A/env.json" ]; then
  OLDREQ="$(cat "$A/request.txt" 2>/dev/null || true)"
  if [ "$OLDREQ" = "$REQUEST" ]; then
    echo "== environment already complete ($A/env.json, $(sed -n 's/.*"env_id": "\([^"]*\)".*/\1/p' "$A/env.json")): nothing to do; --recreate rebuilds it"
    exit 0
  fi
  # only the CUDA module may change without a reinstall (it does not change the installed wheels)
  if [ -z "$OLDREQ" ] || [ "${OLDREQ/ cuda=* cupy=/ cupy=}" != "${REQUEST/ cuda=* cupy=/ cupy=}" ]; then
    die 2 "the complete environment in venv/ was made with ($OLDREQ); this call asks for ($REQUEST): rerun with --recreate to rebuild it"
  fi
  SUPERSEDE=1
fi
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$REPO/alliance_setup_${CLUSTER}_${STAMP}.log"     # gitignored (alliance_setup_*.log)
exec > >(tee -a "$LOG") 2>&1
echo "== setup_alliance.sh $CLUSTER on $(hostname) at $STAMP; repository $REPO ($(git rev-parse HEAD))"
echo "   request: $REQUEST"
if [ "$SUPERSEDE" -eq 1 ]; then
  mv "$A/env.json" "$A/env.json.superseded_$STAMP"
  echo "== the complete environment used another CUDA module ($OLDREQ): its env.json is superseded ($A/env.json.superseded_$STAMP), no reinstall; jobs queued against it will refuse to start, and GPU jobs need a new gpu-check PASS"
fi

# stamps: <name>.done holds the inputs the step was done with
stamp_done() {       # $1 name, $2 key: 0 = done with this key; 1 = not done; exit 2 = other key
  local f="$STEPS/$1.done"
  [ -f "$f" ] || return 1
  [ "$(cat "$f")" = "$2" ] && return 0
  die 2 "step '$1' was done with other inputs ($(cat "$f")); this run asks for ($2): rerun with --recreate"
}
stamp_write() { mkdir -p "$STEPS"; printf '%s' "$2" > "$STEPS/$1.done"; echo "   step '$1' complete"; }

# ---- 1. modules (every run) ---------------------------------------------------------------------
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
AGAIN="fix the cause and rerun the same command (completed steps are skipped)"

# ---- 2. virtual environment --------------------------------------------------------------------
KEY_VENV="cluster=$CLUSTER stdenv=$STDENV_MOD python=$PY_MOD"
if ! stamp_done venv "$KEY_VENV"; then
  [ ! -e venv ] || die 2 "internal: venv/ exists without its stamp"
  virtualenv --no-download venv
  set +u
  # shellcheck disable=SC1091
  source venv/bin/activate
  set -u
  pip install --no-index --upgrade pip
  mkdir -p "$A/wheels"
  stamp_write venv "$KEY_VENV"
else
  echo "== venv: already made ($KEY_VENV)"
  set +u
  # shellcheck disable=SC1091
  source venv/bin/activate
  set -u
fi
export PYTHONNOUSERSITE=1
mkdir -p "$A/wheels"

# ---- 3. abTEM 1.0.10 wheel: before the long install (fails early without PyPI access) ---------
AW="$A/wheels/$ABTEM_WHEEL_NAME"
if [ -f "$AW" ] && [ "$(sha256sum "$AW" | cut -d' ' -f1)" = "$ABTEM_SHA256" ]; then
  echo "== abTEM wheel present and verified ($AW)"
else
  rm -f "$AW"
  if [ -n "$ABTEM_WHEEL" ]; then
    [ "$(basename "$ABTEM_WHEEL")" = "$ABTEM_WHEEL_NAME" ] || die 2 "--abtem-wheel must be $ABTEM_WHEEL_NAME"
    cp "$ABTEM_WHEEL" "$A/wheels/"
  else
    echo "== pip download --no-deps --only-binary=:all: abtem==1.0.10 (login node, Python § Pre-downloading packages)"
    (cd "$A/wheels" && pip download --no-deps --only-binary=:all: "abtem==1.0.10") || \
      die 2 "pip download of abtem failed (no PyPI access from this login node?). Copy $ABTEM_WHEEL_NAME to this cluster and rerun the same command with --abtem-wheel PATH (no --recreate needed)"
  fi
  [ -f "$AW" ] || die 2 "expected $AW (a none-any wheel); got: $(ls "$A/wheels")"
fi
GOT="$(sha256sum "$AW" | cut -d' ' -f1)"
[ "$GOT" = "$ABTEM_SHA256" ] || { rm -f "$AW"; die 2 "SHA-256 of $ABTEM_WHEEL_NAME is $GOT, PyPI says $ABTEM_SHA256 (file removed)"; }
echo "abtem wheel SHA-256 verified: $GOT"

# ---- 4. wheelhouse packages ---------------------------------------------------------------------
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
KEY_WH="requirements sha256 $(sha256sum "$A/requirements_wheelhouse.txt" | cut -d' ' -f1)"
if ! stamp_done wheelhouse "$KEY_WH"; then
  grep -v '^#' "$A/requirements_wheelhouse.txt" | sed -e 's/[<>=!].*$//' > "$A/wheel_names.txt"
  echo "== avail_wheels -r $A/wheel_names.txt   (a record of what the wheelhouse offers here)"
  AVAIL_STATUS="OK"
  if ! avail_wheels -r "$A/wheel_names.txt" > "$A/avail_wheels.txt" 2>&1; then
    # a record only: the pip install below is the check, and it fails loudly on a missing wheel
    AVAIL_STATUS="FAILED (see avail_wheels.txt)"
    echo "WARNING: avail_wheels failed; the pip install below decides (output: $A/avail_wheels.txt)" >&2
  fi
  printf '%s' "$AVAIL_STATUS" > "$A/avail_status.txt"
  cat "$A/avail_wheels.txt"
  # one report per attempt: an interrupted attempt keeps its report (package_sources merges them)
  pip install --no-index --report "$A/pip_report_wheelhouse_$STAMP.json" -r "$A/requirements_wheelhouse.txt" || \
    die 2 "pip install from the wheelhouse failed (see above: a missing wheel?). $AGAIN; or --recreate --python-module python/3.12.4"
  stamp_write wheelhouse "$KEY_WH"
else
  echo "== wheelhouse packages: already installed ($KEY_WH)"
fi
AVAIL_STATUS="$(cat "$A/avail_status.txt" 2>/dev/null || echo "not recorded")"

# ---- 5. abTEM and this repository ---------------------------------------------------------------
KEY_AB="abtem $ABTEM_SHA256"
if ! stamp_done abtem "$KEY_AB"; then
  pip install --no-index --report "$A/pip_report_abtem_$STAMP.json" "$AW"
  stamp_write abtem "$KEY_AB"
else
  echo "== abTEM: already installed"
fi
KEY_REPO="editable $REPO"
if ! stamp_done repo "$KEY_REPO"; then
  pip install --no-index --no-build-isolation --report "$A/pip_report_repo_$STAMP.json" -e ".[test]"
  stamp_write repo "$KEY_REPO"
else
  echo "== reflection_holo: already installed (editable, $REPO)"
fi
pip check
pip freeze --all > "$A/pip_freeze.txt"
python - "$A" <<'EOF'
import json, sys
from importlib import metadata
from pathlib import Path
A = Path(sys.argv[1])
src = {}
for step, label in (("wheelhouse", "Alliance wheelhouse (pip --no-index)"),
                    ("abtem", "PyPI wheel pre-downloaded on the login node, SHA-256 checked"),
                    ("repo", "this repository (editable)")):
    for rep in sorted(A.glob(f"pip_report_{step}_*.json")):       # attempts in time order
        for it in json.loads(rep.read_text()).get("install", []):
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

# ---- 6. checks (every run until complete) --------------------------------------------------------
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
    die 2 "'import cupy' failed on this login node. If the error names the NVIDIA driver (libcuda), the login node may simply have no GPU driver: rerun the same command with --allow-cupy-import-failure (no reinstall) and let the gpu-check job decide"
  fi
fi
python -c "import cupy; print('CUDA runtime seen by cupy:', cupy.cuda.runtime.runtimeGetVersion())" || \
  echo "NOTE: cupy.cuda.runtime.runtimeGetVersion() failed here (no GPU/driver on the login node?); the gpu-check job records it" >&2
echo "== CPU physics check of the installed environment (no GPU; login-node friendly: 4 threads)"
# Not tests/hpc: those test the kit with fake Slurm/Lmod and depend on the login shell (BASH_ENV,
# a noexec temporary directory), not on this environment (H4 F1). Excluded by name:
# test_cupy_is_lazy_and_not_a_fallback asserts that cupy is not imported in the pytest process,
# which fails wherever cupy imports (abTEM imports it; H6 report), independent of this setup.
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
python -m pytest -q -p no:cacheprovider tests/geometry/test_geom_wavelength.py \
  tests/forward/test_engine_contract.py tests/forward/test_vacuum_propagation.py \
  tests/forward/test_rung1_refraction.py tests/forward/test_potential_atomic.py \
  tests/pipeline/test_pipeline_geometric.py tests/provenance \
  -k "not test_cupy_is_lazy_and_not_a_fallback" || \
  die 2 "the CPU physics check of the installed environment failed (see above); $AGAIN"

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
# the setup logs: hard links (same file, so always complete: H4 F13), one per run of this setup
for lg in "$REPO"/alliance_setup_"${CLUSTER}"_*.log; do
  [ -f "$lg" ] || continue
  dst="$A/$(basename "$lg")"
  [ -e "$dst" ] || ln "$lg" "$dst" || { cp "$lg" "$dst"; echo "NOTE: $dst is a copy (hard link failed): it may lack the last lines of $lg" >&2; }
done
printf '%s' "$REQUEST" > "$A/request.txt"
python - "$A" "$CLUSTER" "$ENV_ID" "$STDENV_MOD" "$PY_MOD" "$CUDA_MOD" "$CUPY_STATUS" "$GOT" "$LOG" "$AVAIL_STATUS" "$REQUEST" <<'EOF'
import datetime, json, platform, socket, subprocess, sys
from pathlib import Path
A, cluster, env_id, stdenv, pymod, cudamod, cupy_status, abtem_sha, log, avail, request = sys.argv[1:]
rec = dict(schema="reflholo_alliance_env/1", cluster=cluster, env_id=env_id,
           created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           host=socket.gethostname(), modules=dict(stdenv=stdenv, python=pymod, cuda=cudamod),
           module_list=(Path(A) / "module_list.txt").read_text().split(),
           python=sys.version, platform=platform.platform(),
           repository_commit=subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
           cupy_import_on_login=cupy_status, abtem_wheel_sha256=abtem_sha, setup_log=log,
           avail_wheels=avail, request=request,
           steps={p.stem: p.read_text() for p in sorted((Path(A) / "steps").glob("*.done"))},
           setup_complete=True)
tmp = Path(A) / "env.json.tmp"
tmp.write_text(json.dumps(rec, indent=1))
tmp.replace(Path(A) / "env.json")
print("environment id", env_id)
EOF
echo "== DONE: environment $ENV_ID ready in $REPO/venv (records in $A)."
echo "   Next: bash scripts/hpc/alliance/submit.sh $CLUSTER gpu-check --account <RAP> --time 00:15:00 --dry-run"
