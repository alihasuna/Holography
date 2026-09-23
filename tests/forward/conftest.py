"""Fixtures for tests/forward (TEST_ONLY inputs labelled; see ladder_cases.py, smoke_case.py)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reflection_holo.constants import A_SI_A  # noqa: E402
from reflection_holo.forward.cell import build_reflection_cell  # noqa: E402
from reflection_holo.structure import Staircase, build_si001_terraces  # noqa: E402


@pytest.fixture(scope="session")
def small_cell():
    """Small Si(001) [110] cell with an a/2 step parallel to the beam (TEST_ONLY azimuth)."""
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(2, 2),
                   boundary_step_layers=-2)
    s = build_si001_terraces(azimuth_uvw=(1, 1, 0),
                             azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
                             staircase=st, edge_periods=12, substrate_layers=10,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                             lattice_parameter_label="ASSUMPTION B2")
    p = A_SI_A / 2 ** 0.5
    return build_reflection_cell(s, vacuum_above_A=12.0, depth_below_A=10.0,
                                 bulk_absorber_A=4.0, top_absorber_A=5.0,
                                 entrance_vacuum_z_A=2 * p / 4 * 2)
