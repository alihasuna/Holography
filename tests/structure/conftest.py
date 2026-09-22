"""Fixtures for tests/structure; the TEST_ONLY inputs live in si001_test_inputs.py."""
import importlib.util

import pytest

from si001_test_inputs import REPO_ROOT, build
from reflection_holo.structure import Staircase


@pytest.fixture(scope="session")
def mixed_110():
    """[110] azimuth, edges transverse: a/2 up, a/4 down, a/4 down at the cell edge."""
    st = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(4, 3, 3),
                   boundary_step_layers=-1)
    return build(st, azimuth=(1, 1, 0), edge_periods=3, substrate_layers=5)


@pytest.fixture(scope="session")
def calculator():
    path = REPO_ROOT / "tools" / "reflection_step_phase_calculator.py"
    spec = importlib.util.spec_from_file_location("reflection_step_phase_calculator", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
