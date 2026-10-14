import importlib.util
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


@pytest.fixture(scope="session")
def calculator():
    path = os.path.join(ROOT, "tools", "reflection_step_phase_calculator.py")
    spec = importlib.util.spec_from_file_location("calc", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


