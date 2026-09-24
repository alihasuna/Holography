#!/usr/bin/env bash
# Build every figure of the R1 smoke report from the campaign runs (agent R1).
# Usage (repository root):  bash tools/report/make_report_figures.sh SP
#   SP = the scratchpad root holding report_smoke/ (runs of tools/report/run_smoke_campaign.py),
#        torus/figures (report T1) and buried_t5/figures (report T5). Required, no default.
# Writes SP/report_smoke/figures/*.png, SP/report_smoke/figures/s2_detail/*.png, and the stdout of
# the figure scripts to tools/report/report_figures_output.txt; then the figure manifest
# tools/report/figure_manifest.txt (tools/report/figure_manifest.py).
set -euo pipefail
if [ "$#" -ne 1 ]; then echo "usage: $0 SP" >&2; exit 2; fi
SP="$1"
R="$SP/report_smoke"
F="$R/figures"
PY="venv/bin/python"
export PYTHONPATH=.
mkdir -p "$F"
OUT=tools/report/report_figures_output.txt
{
  echo "# tools/report/make_report_figures.sh $SP ($(date -u +%Y-%m-%dT%H:%M:%SZ), HEAD $(git rev-parse HEAD))"
  echo "\$ $PY tools/report/report_figures.py --runs $R --out $F --t1-figures $SP/torus/figures --t5-figures $SP/buried_t5/figures"
  "$PY" tools/report/report_figures.py --runs "$R" --out "$F" --t1-figures "$SP/torus/figures" \
        --t5-figures "$SP/buried_t5/figures"
  echo "\$ $PY tools/plots/torus_compact.py --trench $R/S6_torus_trench --ridge $R/S6_torus_ridge --out $F/s6_torus_compact.png"
  "$PY" tools/plots/torus_compact.py --trench "$R/S6_torus_trench" --ridge "$R/S6_torus_ridge" \
        --out "$F/s6_torus_compact.png"
  echo "\$ $PY tools/plots/smoke_figures.py --config configs/demo_smoke_si001.yaml --variant multislice_tiny --run-dir $R/S2_multislice_tiny --geometric-run-dir $R/S1_base --out $F/s2_detail"
  "$PY" tools/plots/smoke_figures.py --config configs/demo_smoke_si001.yaml --variant multislice_tiny \
        --run-dir "$R/S2_multislice_tiny" --geometric-run-dir "$R/S1_base" --out "$F/s2_detail"
} 2>&1 | sed "s#$SP#SP#g" > "$OUT"
"$PY" tools/report/figure_manifest.py --sp "$SP" > tools/report/figure_manifest.txt
echo "wrote $OUT and tools/report/figure_manifest.txt"
