#!/usr/bin/env python3
"""Rung R0: print the error budget. Fails (exit 2) unless --accept-assumptions is given,
because every achievable-precision input is a MISSING PROJECT_INPUT."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import budget  # noqa: E402

if __name__ == "__main__":
    sys.exit(budget.main(sys.argv[1:]))
