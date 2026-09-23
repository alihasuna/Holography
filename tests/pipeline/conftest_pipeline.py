"""Shared constants of the pipeline tests (not a test module)."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SMOKE = REPO / "configs" / "demo_smoke_si001.yaml"
HPC = REPO / "configs" / "demo_hpc_si001.yaml"
# Acceptance: recovered values within 3 propagated standard deviations (fixed before any run).
TOL_SIGMA = 3.0
