"""Shadowed strips behind transverse steps and patterned features (SM07, B9, docs/03 section 4)."""
import math

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import (EdgeProfile, PatternedFeature, Staircase,
                                       feature_shadow_intervals, feature_shadow_mask,
                                       shadow_length_A, terrace_shadow_strips)
from reflection_holo.structure.shadows import periodic_shadowed_intervals, shadowed_intervals
from si001_test_inputs import FEATURE_LABEL, THETA_22P5_MRAD, THETA_LABEL, build

Q = A_SI_A / 4.0
P110 = A_SI_A / math.sqrt(2.0)


def flat(intervals):
    """Flatten an interval list for pytest.approx (which refuses nested sequences)."""
    return [float(v) for iv in intervals for v in iv]


# --- printed numbers of docs/03 section 4 (tolerance = half a unit of the last printed digit) ------
def test_docs03_60A_per_si001_layer_at_22p5_mrad():
    L = shadow_length_A(Q, THETA_22P5_MRAD, THETA_LABEL)
    assert abs(L - 60.0) <= 0.5                          # printed "60 A per Si(001) layer"


def test_docs03_444nm_for_10nm_mesa_at_22p5_mrad():
    L = shadow_length_A(100.0, THETA_22P5_MRAD, THETA_LABEL)
    assert abs(L / 10.0 - 444.0) <= 0.5                  # printed "444 nm for a 10 nm mesa"


def test_docs03_139A_per_si111_bilayer_at_22p5_mrad():
    d111 = A_SI_A / math.sqrt(3.0)
    L = shadow_length_A(d111, THETA_22P5_MRAD, THETA_LABEL)
    assert abs(L - 139.0) <= 0.5                         # printed "139 A per Si(111) bilayer"


def test_theta_requires_label_and_range():
    with pytest.raises(ValueError, match="label"):
        shadow_length_A(Q, THETA_22P5_MRAD, "")
    for bad in (0.0, -0.01, math.pi / 2):
        with pytest.raises(ValueError, match="theta_ext_rad"):
            shadow_length_A(Q, bad, THETA_LABEL)


# --- built staircases ----------------------------------------------------------------------------
def test_built_single_a4_step_shadow_is_60A():
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(30, 30),
                   boundary_step_layers=-1)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)
    # the down-step along the beam is the one at the cell edge (terrace 1 -> terrace 0)
    down = [x for x in s.metadata["steps"] if x["upper_terrace_upstream"]]
    assert len(down) == 1 and down[0]["position_A"] == 0.0
    assert len(sh.intervals_A) == 1
    z0, z1 = sh.intervals_A[0]
    assert z0 == pytest.approx(0.0, abs=1e-9)
    assert abs((z1 - z0) - 60.0) <= 0.5                  # docs/03: 60 A per Si(001) layer
    assert z1 - z0 == pytest.approx(Q / math.tan(THETA_22P5_MRAD), abs=1e-9)
    # the up-step along the beam (at 30 periods) casts no shadow
    up = [x for x in s.metadata["steps"] if x["upper_terrace_upstream"] is False]
    assert up and all(not sh.mask(np.array([u["position_A"] + 1.0]))[0] for u in up)
    per = {p["step"]: p["nominal_shadow_length_A"] for p in sh.per_step}
    assert per[down[0]["index"]] == pytest.approx(60.33, abs=0.005)


def test_built_a2_step_shadow_is_twice():
    st = Staircase(edges="transverse", terrace_layers=(2, 0), terrace_widths=(10, 40),
                   boundary_step_layers=2)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)
    (z0, z1), = sh.intervals_A
    assert z0 == pytest.approx(10 * P110, abs=1e-9)
    assert z1 - z0 == pytest.approx(2 * Q / math.tan(THETA_22P5_MRAD), abs=1e-9)


def test_shadow_cut_short_by_next_rise():
    # terrace 1 is lower and only 5 periods (19.2 A < 60 A) wide: shadowed entirely, no more
    st = Staircase(edges="transverse", terrace_layers=(1, 0, 1), terrace_widths=(20, 5, 20),
                   boundary_step_layers=0)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)
    assert flat(sh.intervals_A) == pytest.approx([20 * P110, 25 * P110], abs=1e-9)


def test_shadow_over_two_descending_steps():
    st = Staircase(edges="transverse", terrace_layers=(2, 1, 0), terrace_widths=(10, 10, 10),
                   boundary_step_layers=2)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)
    # 60.3 A from the first edge exceeds the 38.4 A terrace, and the line from that edge stays
    # above the lower terraces up to the a/2 rise at the cell edge
    assert flat(sh.intervals_A) == pytest.approx([10 * P110, 30 * P110], abs=1e-9)


def test_shadow_wraps_across_the_periodic_boundary():
    st = Staircase(edges="transverse", terrace_layers=(0, 1, 0), terrace_widths=(10, 5, 10),
                   boundary_step_layers=0)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)
    L = 25 * P110
    z_edge = 15 * P110
    lsh = Q / math.tan(THETA_22P5_MRAD)
    assert flat(sh.intervals_A) == pytest.approx([0.0, z_edge + lsh - L, z_edge, L], abs=1e-9)
    z = np.array([z_edge - 0.1, z_edge + 0.1, L - 0.1, 0.1, z_edge + lsh - L + 0.1, L + 0.1])
    assert sh.mask(z).tolist() == [False, True, True, True, False, True]


def test_parallel_edges_cast_no_shadow_along_the_beam():
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(5, 5),
                   boundary_step_layers=-2)
    s = build(st, edge_periods=2, substrate_layers=4)
    sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)
    assert sh.intervals_A == () and "parallel" in sh.note


def test_raytrace_primitives():
    t = math.tan(0.02)
    # descending riser of 2 A at z = 0, then flat: shadow 2/tan
    assert flat(shadowed_intervals([(-10, 2), (0, 2), (0, 0), (500, 0)], t)) == pytest.approx(
        [0.0, 2 / t], abs=1e-9)
    # rising riser: no shadow
    assert shadowed_intervals([(-10, 0), (0, 0), (0, 2), (500, 2)], t) == []
    # slope steeper than the beam (descending): the slope itself is shadowed
    iv = shadowed_intervals([(-10, 2), (0, 2), (1, 0), (500, 0)], t)
    assert flat(iv) == pytest.approx([0.0, 2 / t], abs=1e-9)
    # gentle descending slope (less steep than the beam): lit
    assert shadowed_intervals([(-10, 2), (0, 2), (2 / (0.5 * t), 0), (1e4, 0)], t) == []
    with pytest.raises(ValueError):
        periodic_shadowed_intervals([(1, 0), (2, 0)], 2.0, t)


# --- patterned features (PROJECT_INPUT item 13; TEST_ONLY values) ----------------------------------
def _feature(kind="mesa", h=100.0, dims=(5000.0, 3000.0), at="top", orient=0.0,
             edge=EdgeProfile("vertical", None), center=(0.0, 0.0)):
    return PatternedFeature(kind=kind, height_A=h, lateral_dimensions_A=dims, dimensions_at=at,
                            orientation_deg=orient, edge_profile=edge, center_A=center,
                            label=FEATURE_LABEL)


def test_mesa_10nm_vertical_shadow_444nm():
    f = _feature()
    (z0, z1), = feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL)
    assert z0 == pytest.approx(2500.0, abs=1e-9)                 # downstream top edge
    assert abs((z1 - z0) / 10.0 - 444.0) <= 0.5                  # docs/03: 444 nm


def test_mesa_orientation_swaps_along_beam_dimension():
    f = _feature(orient=90.0)
    (z0, _), = feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL)
    assert z0 == pytest.approx(1500.0, abs=1e-9)


def test_mesa_sloped_sidewall_steeper_than_beam():
    f = _feature(edge=EdgeProfile("linear", 0.3))
    (z0, z1), = feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL)
    assert z0 == pytest.approx(2500.0, abs=1e-6)                 # from the top edge
    assert z1 - z0 == pytest.approx(100.0 / math.tan(THETA_22P5_MRAD), abs=1e-6)


def test_mesa_sidewall_gentler_than_beam_is_lit():
    f = _feature(edge=EdgeProfile("linear", 0.01))               # 10 mrad < 22.5 mrad
    assert feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL) == []


def test_trench_narrower_than_shadow_floor_fully_shadowed():
    f = _feature(kind="trench", dims=(2000.0, 3000.0))
    (z0, z1), = feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL)
    assert (z0, z1) == pytest.approx((-1000.0, 1000.0), abs=1e-9)


def test_trench_wider_than_shadow():
    f = _feature(kind="trench", dims=(10000.0, 3000.0))
    (z0, z1), = feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL)
    assert z0 == pytest.approx(-5000.0, abs=1e-9)
    assert abs((z1 - z0) / 10.0 - 444.0) <= 0.5


def test_feature_mask_2d():
    f = _feature(edge=EdgeProfile("linear", 0.3), at="top")
    y = np.array([0.0, 1400.0, 1500.0 + 100.0 / math.tan(0.3) * 0.5, 5000.0])
    z = np.linspace(-6000.0, 12000.0, 1801)
    m = feature_shadow_mask(f, THETA_22P5_MRAD, THETA_LABEL, y, z)
    lens = m.sum(axis=1) * (z[1] - z[0])
    assert lens[0] == pytest.approx(lens[1], abs=20.0)           # on the top face: full height
    assert 0 < lens[2] < lens[1]                                 # on the side slope: lower
    assert lens[3] == 0                                          # outside the feature


def test_feature_inputs_required_and_checked():
    with pytest.raises(TypeError):
        PatternedFeature(kind="mesa", height_A=100.0, lateral_dimensions_A=(1.0, 1.0),
                         dimensions_at="top", orientation_deg=0.0, center_A=(0, 0),
                         label=FEATURE_LABEL)
    with pytest.raises(NotImplementedError):
        feature_shadow_intervals(_feature(orient=45.0), THETA_22P5_MRAD, THETA_LABEL)
    with pytest.raises(NotImplementedError):
        feature_shadow_intervals(_feature(edge=EdgeProfile("gaussian", 0.2)), THETA_22P5_MRAD,
                                 THETA_LABEL)
    with pytest.raises(ValueError, match="linear edge profile"):
        feature_shadow_intervals(_feature(edge=EdgeProfile("linear", None)), THETA_22P5_MRAD,
                                 THETA_LABEL)
    with pytest.raises(ValueError, match="consume"):
        feature_shadow_intervals(_feature(dims=(100.0, 100.0), at="base",
                                          edge=EdgeProfile("linear", 0.3)),
                                 THETA_22P5_MRAD, THETA_LABEL)
    bad = PatternedFeature(kind="mesa", height_A=100.0, lateral_dimensions_A=(1.0, 1.0),
                           dimensions_at="top", orientation_deg=0.0,
                           edge_profile=EdgeProfile("vertical", None), center_A=(0, 0),
                           label="from memory")
    with pytest.raises(ValueError, match="label"):
        feature_shadow_intervals(bad, THETA_22P5_MRAD, THETA_LABEL)


def test_private_shadow_helper_matches_geometry_module():
    """Consolidation guard: structure's private helper equals geometry.projection.shadow_length_A."""
    from reflection_holo.geometry.projection import shadow_length_A as geom_shadow
    from reflection_holo.structure.shadows import _shadow_length_A
    for h in (Q, 2 * Q, 100.0, 1000.0):
        for th in (0.0136, THETA_22P5_MRAD, 0.05):
            assert _shadow_length_A(h, th) == pytest.approx(float(geom_shadow(h, th)), rel=1e-15)
