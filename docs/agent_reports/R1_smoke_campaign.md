# R1: smoke-test campaign on HEAD with parameters and figures (for the supervisor report)

Status: IN PROGRESS (written incrementally; final status at the end). Agent R1. Nothing committed
by R1 (the orchestrator commits). Branch `claude/electron-holography-orchestration-nakd7r`,
HEAD `2896522` at start. Beam energy 200 keV throughout (300 keV never used).

`SP` = `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`;
outputs (runs, figures) in `SP/report_smoke/` (never under `outputs/` of the repository).
Committed code: `tools/report/` only (new). Not touched: `reflection_holo/`, `configs/`, `tests/`,
`scripts/hpc/`.

## Log

1. Inputs read: configs/demo_smoke_si001.yaml (base and every variant), demo_smoke_torus_{trench,
   ridge}.yaml, demo_convergence_si001.yaml, pipeline CLI (`reflection_holo/pipeline/__main__.py`,
   `run.py` outputs), tools/plots/*.py, reports P1, T1, T2, T5, E3, the S7 run directories
   (`SP/torus/ms_*`, T1, and a later clean rerun `SP/torus_ms/` at a1ef2a0) and the S8 run
   directories (`SP/buried/ms_*`, T3; analysis `tools/review/t5/buried_torus_analysis_output.txt`).
   Machine load before starting: 0.14 (4 cores).
