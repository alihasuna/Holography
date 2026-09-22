"""Plate-cell illumination fractions behind T17-T19 (source map SM09). Exactly the calculator's
reference values and tolerances (lines 1048-1053). The cell parameters are the inspected
repository's defaults (PROJECT_INPUT (repository defaults), commit 6694959,
si110_cleave_slab_generator.py: n_x_si=9, n_y=12, n_z_si=36, x_vac=10 A, z_vac=30 A), stated here
as test inputs; the angle is the (6,-6,6) setting, evaluated as the calculator does."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.geometry.plate_cell import plate_cell_geometry
from reflection_holo.geometry.specular import SpecularCondition

REPO_DEFAULT_CELL = dict(a_A=A_SI_A, n_x_si=9, n_y=12, n_z_si=36, x_vac_A=10.0, z_vac_A=30.0)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


@pytest.fixture(scope="module")
def cell():
    th = SpecularCondition(A_SI_A / np.sqrt(3.0), 6, 200.0, 12.0).theta_ext
    return plate_cell_geometry(theta_ext_rad=th, **REPO_DEFAULT_CELL)


def test_T17_top_gap_fraction(cell):
    """T17: top-gap illumination reaching the surface = 31.10 % +/- 0.05."""
    check(cell.top_gap_fraction * 100, 31.10, 0.05)


def test_T18_end_face_fraction(cell):
    """T18: incident wave entering the front end face = 80.89 % +/- 0.05."""
    check(cell.end_face_fraction * 100, 80.89, 0.05)


def test_T19_rise_over_cell(cell):
    """T19: reflected-beam rise over the cell = 4.4604 A +/- 1e-3, below x_vac."""
    check(cell.rise_over_cell_A, 4.4604, 1e-3)
    assert cell.no_wraparound


def test_all_parameters_required():
    with pytest.raises(TypeError):
        plate_cell_geometry(theta_ext_rad=0.02, a_A=A_SI_A)
