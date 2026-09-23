"""Reflection cell of a half-torus feature (reflection_holo.forward.feature_cell): layout of the
flat surface, the feature record in cell coordinates, and checks F1 to F3 passing and failing.

TEST_ONLY inputs (items 7, 8, 13); no propagation is run here (the engine's own geometry assertions
are exercised by the half-torus smoke runs, docs/agent_reports/T1_torus_atomistic.md)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import ReflectionGeometryError
from reflection_holo.forward.feature_cell import (build_feature_reflection_cell,
                                                  check_feature_geometry)
from reflection_holo.forward.multislice import SheetBeam
from reflection_holo.structure.features import (build_si001_flat_reference,
                                                build_si001_with_feature)
from reflection_holo.structure.shapes import HalfTorus

A = A_SI_A
Q = A / 4
LAB = "TEST_ONLY: stands in for PROJECT_INPUT item {}"
THETA = 16.1347e-3                       # TEST_ONLY glancing angle (item 7)
TH_INT = 18.4719e-3
ENT = 20 * Q


def structure(kind, depth):
    Ly, Lz = 13 * A, 60 * A
    common = dict(azimuth_uvw=(1, 0, 0), azimuth_label=LAB.format(8), extent_y_A=Ly,
                  extent_z_A=Lz, depth_layers=depth, lattice_parameter_A=A,
                  lattice_label="ASSUMPTION B2", vacuum_above_A=10.0)
    if kind == "flat":
        return build_si001_flat_reference(**common)
    f = HalfTorus(center_y_A=0.5 * Ly, center_z_A=150.0, major_radius_A=20.0, minor_radius_A=6.0,
                  kind=kind, label=LAB.format(13), source="TEST_ONLY")
    return build_si001_with_feature(feature=f, ring_margin_A=A, **common)


def cell_of(s, vac):
    x_s = s.metadata["terrace_map"][0]["top_height_A"]
    return build_feature_reflection_cell(s, vacuum_above_flat_surface_A=vac, depth_below_A=x_s,
                                         bulk_absorber_A=5.0, top_absorber_A=5.0,
                                         entrance_vacuum_z_A=ENT)


def beam_above(cell, gap, H=4.0, e=1.0):
    return SheetBeam(height_A=H, edge_A=e, x_bottom_A=cell.metadata["layout"]
                     ["highest_surface_x_A"] + gap, theta_in_ext_rad=THETA,
                     theta_label=LAB.format(7))


def check(cell, beam, margin=10.0):
    return check_feature_geometry(cell, beam=beam, theta_out_ext_rad=THETA, theta_int_rad=TH_INT,
                                  buildup_depth_A=20.0, footprint_margin_A=margin)


@pytest.fixture(scope="module")
def ridge():
    return structure("ridge", 25)


@pytest.fixture(scope="module")
def trench():
    return structure("trench", 25)


def test_layout_is_the_flat_surface_and_feature_in_cell_coordinates(ridge):
    c = cell_of(ridge, 20.0)
    lay, f = c.metadata["layout"], c.metadata["feature"]
    x_flat = 24 * Q                                   # depth_below = flat top layer height
    assert np.isclose(lay["lowest_surface_x_A"], x_flat)
    assert np.isclose(lay["highest_surface_x_A"], x_flat)
    assert np.isclose(f["top_layer_x_range_A"][0], x_flat)
    assert np.isclose(f["top_layer_x_range_A"][1], x_flat + 4 * Q)   # r = 6 A: layers 1..4
    assert np.isclose(f["highest_atom_x_A"], x_flat + 4 * Q)
    assert np.isclose(f["center_z_A"], 150.0 + ENT)
    assert f["n_added"] == len(ridge.feature_sites_A) and f["label"] == LAB.format(13)
    assert len(c.Z) == ridge.n_atoms and c.metadata["kind"] == "atomic"


def test_checks_pass_and_record_the_conservative_reading(ridge):
    c = cell_of(ridge, 20.0)
    out = check(c, beam_above(c, 0.5))
    assert all(out[k]["passed"] for k in ("F1_vacuum_above_feature",
                                          "F2_ring_inside_lit_footprint", "F3_depth_below_feature"))
    f4 = out["F4_conservative_reading"]
    assert np.isclose(f4["shadow_or_blocked_view_length_A"], 4 * Q / np.tan(THETA))
    assert f4["crystal_length_required_if_feature_extremes_were_terraces_A"] > \
        f4["crystal_length_required_flat_surface_A"]


def test_f1_fails_when_the_ridge_eats_the_vacuum_margin(ridge):
    c = cell_of(ridge, 15.0)          # 15 A > H + L tan(theta) = 9.7 A above the flat surface,
    b = beam_above(c, 0.5)            # but only 9.6 A above the ridge top
    need = b.height_A + c.length_z_A * np.tan(THETA)
    assert 15.0 > need > 15.0 - 4 * Q
    with pytest.raises(ReflectionGeometryError, match="F1_vacuum_above_feature"):
        check(c, b)


def test_f2_fails_when_the_ring_is_not_inside_the_lit_footprint(ridge):
    c = cell_of(ridge, 20.0)
    with pytest.raises(ReflectionGeometryError, match="F2_ring_inside_lit_footprint"):
        check(c, beam_above(c, 3.0))    # footprint core moves downstream past the ring start
    with pytest.raises(ReflectionGeometryError, match="F2_ring_inside_lit_footprint"):
        check(c, beam_above(c, 0.5), margin=60.0)


def test_f3_fails_on_thin_crystal_below_the_trench_floor(trench):
    c = cell_of(trench, 20.0)
    out = check(c, beam_above(c, 0.5))
    assert np.isclose(out["F3_depth_below_feature"]["clean_depth_A"], 24 * Q - 5 * Q - 5.0)
    thin = structure("trench", 20)          # 19 a/4 - 5 a/4 - 5 A = 14.0 A < D = 20 A
    c2 = cell_of(thin, 20.0)
    with pytest.raises(ReflectionGeometryError, match="F3_depth_below_feature"):
        check(c2, beam_above(c2, 0.5))


def test_flat_reference_has_no_feature():
    c = cell_of(structure("flat", 12), 20.0)
    assert c.metadata["feature"] is None
    with pytest.raises(ValueError, match="no feature"):
        check(c, beam_above(c, 0.5))
