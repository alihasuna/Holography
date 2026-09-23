"""ReflectionCell builder and the docs/05 section 4.3 geometry assertions (items 1 to 4; SM16).

The geometry checks are exact inequalities on derived lengths; the tests place each quantity on
both sides of its bound by a margin of 1 A (or 1e-3 mrad-equivalent), so no numerical tolerance is
involved."""
import inspect

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import (ReflectionGeometryError, build_continuum_cell,
                                          build_reflection_cell, check_reflection_geometry)
from reflection_holo.structure import Staircase, build_si001_terraces

AZ_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 8 (beam azimuth)"


def _structure(edge_periods=20, substrate_layers=12):
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(3, 3),
                   boundary_step_layers=-2)
    return build_si001_terraces(azimuth_uvw=(1, 1, 0), azimuth_label=AZ_LABEL, staircase=st,
                                edge_periods=edge_periods, substrate_layers=substrate_layers,
                                first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                                overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                                lattice_parameter_label="ASSUMPTION B2")


@pytest.fixture(scope="module")
def cell():
    return build_reflection_cell(_structure(), vacuum_above_A=20.0, depth_below_A=12.0,
                                 bulk_absorber_A=5.0, top_absorber_A=6.0,
                                 entrance_vacuum_z_A=9.6)


def test_every_argument_is_required():
    sig = inspect.signature(build_reflection_cell)
    for name in ("vacuum_above_A", "depth_below_A", "bulk_absorber_A", "top_absorber_A",
                 "entrance_vacuum_z_A"):
        assert sig.parameters[name].default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        build_reflection_cell(_structure(), vacuum_above_A=20.0, depth_below_A=12.0,
                              bulk_absorber_A=5.0, top_absorber_A=6.0)
    for fn in (check_reflection_geometry, build_continuum_cell):
        assert all(p.default is inspect.Parameter.empty
                   for p in inspect.signature(fn).parameters.values())


def test_layout_no_vacuum_below_and_absorbers(cell):
    lay = cell.metadata["layout"]
    q = A_SI_A / 4
    assert cell.atoms_xyz_A[:, 0].min() >= -1e-9
    assert cell.atoms_xyz_A[:, 0].min() <= q + 1e-9                     # crystal reaches x = 0
    assert lay["lowest_surface_x_A"] == pytest.approx(12.0)
    assert lay["highest_surface_x_A"] == pytest.approx(12.0 + A_SI_A / 2)
    assert cell.extent_x_A == pytest.approx(12.0 + A_SI_A / 2 + 20.0 + 6.0)
    assert lay["top_absorber_x_A"] == pytest.approx([cell.extent_x_A - 6.0, cell.extent_x_A])
    assert lay["bulk_absorber_x_A"] == [0.0, 5.0]
    assert cell.crystal_start_z_A == pytest.approx(9.6)
    assert cell.atoms_xyz_A[:, 2].min() >= 9.6 - 1e-9
    assert cell.length_z_A == pytest.approx(9.6 + 20 * A_SI_A / np.sqrt(2))
    assert set(np.unique(cell.Z)) == {14}
    assert cell.surface_x_A == pytest.approx(12.0)                       # terrace 0 (lower)
    assert lay["z_period_A"] == pytest.approx(A_SI_A / np.sqrt(2))
    assert cell.metadata["terraces"][1]["surface_x_A"] == pytest.approx(12.0 + A_SI_A / 2)


def test_refusals_of_the_builder():
    s = _structure()
    with pytest.raises(ReflectionGeometryError):          # absorber must lie inside the crystal
        build_reflection_cell(s, vacuum_above_A=20.0, depth_below_A=5.0, bulk_absorber_A=5.0,
                              top_absorber_A=6.0, entrance_vacuum_z_A=9.6)
    with pytest.raises(ReflectionGeometryError):          # structure too thin
        build_reflection_cell(s, vacuum_above_A=20.0, depth_below_A=40.0, bulk_absorber_A=5.0,
                              top_absorber_A=6.0, entrance_vacuum_z_A=9.6)
    with pytest.raises(ValueError):
        build_reflection_cell(s, vacuum_above_A=20.0, depth_below_A=12.0, bulk_absorber_A=5.0,
                              top_absorber_A=6.0, entrance_vacuum_z_A=0.0)


def _cont(vac=40.0, L=1500.0, ent=10.0, dep=40.0, bab=15.0):
    return build_continuum_cell(extent_y_A=10.0, terrace_y_bounds_A=[0, 10.0],
                                terrace_heights_A=[0.0], crystal_length_z_A=L - ent,
                                vacuum_above_A=vac, depth_below_A=dep, bulk_absorber_A=bab,
                                top_absorber_A=10.0, entrance_vacuum_z_A=ent)


def _check(c, xb_gap=2.0, H=8.0, th=16.47e-3, D=20.0):
    xs = c.metadata["layout"]["highest_surface_x_A"]
    return check_reflection_geometry(c, beam_height_A=H, beam_x_bottom_A=xs + xb_gap,
                                     theta_in_ext_rad=th, theta_out_ext_rad=th,
                                     theta_int_rad=18.47e-3, buildup_depth_A=D)


def test_geometry_passes_and_records_numbers():
    rec = _check(_cont())
    assert all(v["passed"] for k, v in rec.items() if k != "label")
    assert rec["item2_vacuum_margin"]["required_A"] == pytest.approx(8.0 + 1500 * np.tan(16.47e-3))


def test_item2_vacuum_margin():
    need = 8.0 + 1500 * np.tan(16.47e-3)                 # 32.71 A
    _check(_cont(vac=need + 1.0))
    with pytest.raises(ReflectionGeometryError, match="item2"):
        _check(_cont(vac=need - 1.0))


def test_item3_beam_confined_and_launched_upstream():
    with pytest.raises(ReflectionGeometryError, match="item3_no_end_face"):
        _check(_cont(ent=200.0), xb_gap=2.0)            # beam descends 3.3 A before the crystal
    with pytest.raises(ReflectionGeometryError, match="item3_beam_in_vacuum_band"):
        _check(_cont(), xb_gap=-1.0)


def test_item3_footprint_and_item4_buildup():
    # footprint H / tan(theta) = 485.7 A for H = 8 A; build-up 20 / tan(18.47 mrad) = 1082.7 A
    with pytest.raises(ReflectionGeometryError, match="item3_footprint|item4"):
        _check(_cont(L=400.0, vac=40.0))
    L_ok = 2.0 / np.tan(16.47e-3) + 20.0 / np.tan(18.47e-3) + 1.0
    _check(_cont(L=L_ok, vac=40.0))
    with pytest.raises(ReflectionGeometryError, match="item4_buildup_length"):
        _check(_cont(L=L_ok - 2.0, vac=40.0))
    with pytest.raises(ReflectionGeometryError, match="item4_depth_above_absorber"):
        _check(_cont(dep=34.0, bab=15.0))                # 19 A of clean crystal < D = 20 A
    with pytest.raises(ReflectionGeometryError, match="20 to 100"):
        _check(_cont(), D=10.0)
