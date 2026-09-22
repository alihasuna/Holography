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


def specular_strips(s):
    """terrace_shadow_strips for the specular beam, theta_out = theta_in (TEST_ONLY angle)."""
    return terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL,
                                 theta_out_ext_rad=THETA_22P5_MRAD, theta_out_label=THETA_LABEL)


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
    sh = specular_strips(s)
    # the down-step along the beam is the one at the cell edge (terrace 1 -> terrace 0)
    down = [x for x in s.metadata["steps"] if x["upper_terrace_upstream"]]
    assert len(down) == 1 and down[0]["position_A"] == 0.0
    assert len(sh.illumination_intervals_A) == 1
    z0, z1 = sh.illumination_intervals_A[0]
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
    sh = specular_strips(s)
    (z0, z1), = sh.illumination_intervals_A
    assert z0 == pytest.approx(10 * P110, abs=1e-9)
    assert z1 - z0 == pytest.approx(2 * Q / math.tan(THETA_22P5_MRAD), abs=1e-9)


def test_shadow_cut_short_by_next_rise():
    # terrace 1 is lower and only 5 periods (19.2 A < 60 A) wide: shadowed entirely, no more
    st = Staircase(edges="transverse", terrace_layers=(1, 0, 1), terrace_widths=(20, 5, 20),
                   boundary_step_layers=0)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = specular_strips(s)
    assert flat(sh.illumination_intervals_A) == pytest.approx([20 * P110, 25 * P110], abs=1e-9)


def test_shadow_over_two_descending_steps():
    st = Staircase(edges="transverse", terrace_layers=(2, 1, 0), terrace_widths=(10, 10, 10),
                   boundary_step_layers=2)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = specular_strips(s)
    # 60.3 A from the first edge exceeds the 38.4 A terrace, and the line from that edge stays
    # above the lower terraces up to the a/2 rise at the cell edge
    assert flat(sh.illumination_intervals_A) == pytest.approx([10 * P110, 30 * P110], abs=1e-9)


def test_shadow_wraps_across_the_periodic_boundary():
    st = Staircase(edges="transverse", terrace_layers=(0, 1, 0), terrace_widths=(10, 5, 10),
                   boundary_step_layers=0)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = specular_strips(s)
    L = 25 * P110
    z_edge = 15 * P110
    lsh = Q / math.tan(THETA_22P5_MRAD)
    assert flat(sh.illumination_intervals_A) == pytest.approx([0.0, z_edge + lsh - L, z_edge, L],
                                                           abs=1e-9)
    z = np.array([z_edge - 0.1, z_edge + 0.1, L - 0.1, 0.1, z_edge + lsh - L + 0.1, L + 0.1])
    assert sh.illumination_mask(z).tolist() == [False, True, True, True, False, True]


def test_parallel_edges_cast_no_shadow_along_the_beam():
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(5, 5),
                   boundary_step_layers=-2)
    s = build(st, edge_periods=2, substrate_layers=4)
    sh = specular_strips(s)
    assert sh.intervals_A == () and "parallel" in sh.note


# --- blocked-view strip (docs/03 section 4: reflected beam intercepted by a rise downstream) ------
THETA_OUT_30MRAD = 30.0e-3      # TEST_ONLY non-specular exit angle (tells theta_out from theta_in)
THETA_OUT_LABEL = "TEST_ONLY: exit angle of a non-specular test beam (no docs/06 item)"


def _single_a4_step():
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(30, 30),
                   boundary_step_layers=-1)
    s = build(st, edge_periods=1, substrate_layers=4)
    up = [x for x in s.metadata["steps"] if x["upper_terrace_upstream"] is False]
    down = [x for x in s.metadata["steps"] if x["upper_terrace_upstream"]]
    assert len(up) == 1 and len(down) == 1 and down[0]["position_A"] == 0.0
    return s, up[0], down[0]


def test_blocked_view_strip_in_front_of_upper_terrace_downstream_step():
    s, up, _ = _single_a4_step()
    z_up = up["position_A"]
    assert z_up == pytest.approx(30 * P110, abs=1e-9)
    sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL,
                               theta_out_ext_rad=THETA_OUT_30MRAD, theta_out_label=THETA_OUT_LABEL)
    l_out = Q / math.tan(THETA_OUT_30MRAD)                      # 45.26 A, not 60.33 A
    (b0, b1), = sh.blocked_view_intervals_A
    assert b1 == pytest.approx(z_up, abs=1e-9)                   # ends at the riser
    assert b1 - b0 == pytest.approx(l_out, abs=1e-9)             # length h / tan(theta_out)
    (i0, i1), = sh.illumination_intervals_A
    assert i1 - i0 == pytest.approx(Q / math.tan(THETA_22P5_MRAD), abs=1e-9)
    assert flat(sh.intervals_A) == pytest.approx([i0, i1, b0, b1], abs=1e-9)
    z = np.array([z_up - l_out - 0.1, z_up - l_out + 0.1, z_up - 0.1, z_up + 0.1])
    assert sh.blocked_view_mask(z).tolist() == [False, True, True, False]
    assert sh.mask(z).tolist() == [False, True, True, False]
    assert not sh.illumination_mask(z).any()
    rec, = [p for p in sh.per_step if p["step"] == up["index"]]
    assert rec["strip"] == "blocked_view" and rec["strip_angle"] == "theta_out"
    assert rec["nominal_blocked_view_length_A"] == pytest.approx(l_out, abs=1e-12)
    assert rec["nominal_strip_A"] == pytest.approx((z_up - l_out, z_up), abs=1e-9)
    assert rec["nominal_shadow_length_A"] == 0.0
    # specular beam: the blocked-view strip has the illumination-shadow length
    sp = specular_strips(s)
    (b0, b1), = sp.blocked_view_intervals_A
    (i0, i1), = sp.illumination_intervals_A
    assert b1 - b0 == pytest.approx(i1 - i0, abs=1e-9)
    assert b1 - b0 == pytest.approx(Q / math.tan(THETA_22P5_MRAD), abs=1e-9)


def test_no_blocked_view_in_front_of_upper_terrace_upstream_step():
    s, up, down = _single_a4_step()
    L = float(s.cell_A[2, 2])
    for th_out, label in ((THETA_22P5_MRAD, THETA_LABEL), (THETA_OUT_30MRAD, THETA_OUT_LABEL)):
        sh = terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL,
                                   theta_out_ext_rad=th_out, theta_out_label=label)
        # the down-step riser is at z = 0 = L (cell edge); in front of it lies the upper terrace
        z_front = np.array([L - 0.1, L - 1.0, L - 30.0, L - 100.0])
        assert not sh.blocked_view_mask(z_front).any()
        assert not sh.mask(z_front).any()
        # the only blocked-view strip is the one ending at the up-step
        (_, b1), = sh.blocked_view_intervals_A
        assert b1 == pytest.approx(up["position_A"], abs=1e-9)
        rec, = [p for p in sh.per_step if p["step"] == down["index"]]
        assert rec["strip"] == "illumination_shadow" and rec["strip_angle"] == "theta_in"
        assert rec["nominal_blocked_view_length_A"] == 0.0
        assert rec["nominal_strip_A"][0] == pytest.approx(0.0, abs=1e-12)


def test_blocked_view_cut_short_by_preceding_rise():
    # mirror of test_shadow_cut_short_by_next_rise: the lower terrace 1 (5 periods, 19.2 A < 60 A)
    # in front of the up-step at 25 periods is blocked entirely, and nothing on the higher terrace
    st = Staircase(edges="transverse", terrace_layers=(1, 0, 1), terrace_widths=(20, 5, 20),
                   boundary_step_layers=0)
    s = build(st, edge_periods=1, substrate_layers=4)
    sh = specular_strips(s)
    assert flat(sh.blocked_view_intervals_A) == pytest.approx([20 * P110, 25 * P110], abs=1e-9)


def test_exit_angle_required_labelled_and_checked():
    s, _, _ = _single_a4_step()
    with pytest.raises(TypeError, match="theta_out"):
        terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)
    with pytest.raises(ValueError, match="label"):
        terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL, theta_out_ext_rad=THETA_OUT_30MRAD,
                              theta_out_label="same as incidence")
    for bad in (0.0, -0.01, math.pi / 2):
        with pytest.raises(ValueError, match="theta_out_ext_rad"):
            terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL, theta_out_ext_rad=bad,
                                  theta_out_label=THETA_OUT_LABEL)


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


@pytest.mark.parametrize("period_A", [0.2, 0.3, 0.7, P110, 2 * P110, 3 * P110, 25 * P110, 100.1])
def test_periodic_ray_trace_inexact_periods_regression(period_A):
    """Regression (S2 follow-up 2): unrolling with pts + k*period made period joins non-monotone
    by one ulp for periods such as 0.2 A or 1-2 x P110 ("profile z coordinates must be
    non-decreasing"). Profile: a riser falling by Q at half the period, rising again at the cell
    edge; the shadow is [period/2, min(period/2 + Q/tan(theta), period)) exactly."""
    t = math.tan(THETA_22P5_MRAD)
    a = 0.5 * period_A
    iv = periodic_shadowed_intervals([(0.0, Q), (a, Q), (a, 0.0), (period_A, 0.0)], period_A, t)
    assert flat(iv) == pytest.approx([a, min(a + Q / t, period_A)], abs=1e-9)


def test_periodic_ray_trace_end_point_within_accepted_tolerance_regression():
    """Regression (S2 follow-up 2): an end point accepted by the existing 1e-9 A end check but
    lying above the period (here by 5e-10 A) made the unrolled profile decrease at every join."""
    t = math.tan(THETA_22P5_MRAD)
    iv = periodic_shadowed_intervals([(0.0, Q), (50.0, Q), (50.0, 0.0), (100.0 + 5e-10, 0.0)],
                                     100.0, t)
    assert flat(iv) == pytest.approx([50.0, 100.0], abs=1e-9)
    with pytest.raises(ValueError, match="end at z = period"):
        periodic_shadowed_intervals([(0.0, Q), (50.0, 0.0), (100.0 + 2e-9, 0.0)], 100.0, t)


# --- patterned features (PROJECT_INPUT item 13; TEST_ONLY values) ----------------------------------
def _feature(kind="mesa", h=100.0, dims=(5000.0, 3000.0), at="top", orient=0.0,
             edge=EdgeProfile("vertical", None), center=(0.0, 0.0)):
    return PatternedFeature(kind=kind, height_A=h, lateral_dimensions_A=dims, dimensions_at=at,
                            orientation_deg=orient, edge_profile=edge, center_A=center,
                            label=FEATURE_LABEL)


SPECULAR_EXIT = dict(theta_out_ext_rad=THETA_22P5_MRAD, theta_out_label=THETA_LABEL)


def specular_feature(f, y_A=None):
    """feature_shadow_intervals for the specular beam, theta_out = theta_in (TEST_ONLY angle)."""
    return feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL, y_A, **SPECULAR_EXIT)


def test_mesa_10nm_vertical_shadow_444nm():
    f = _feature()
    (z0, z1), = specular_feature(f).illumination_intervals_A
    assert z0 == pytest.approx(2500.0, abs=1e-9)                 # downstream top edge
    assert abs((z1 - z0) / 10.0 - 444.0) <= 0.5                  # docs/03: 444 nm


def test_mesa_orientation_swaps_along_beam_dimension():
    f = _feature(orient=90.0)
    (z0, _), = specular_feature(f).illumination_intervals_A
    assert z0 == pytest.approx(1500.0, abs=1e-9)


def test_mesa_sloped_sidewall_steeper_than_beam():
    f = _feature(edge=EdgeProfile("linear", 0.3))
    (z0, z1), = specular_feature(f).illumination_intervals_A
    assert z0 == pytest.approx(2500.0, abs=1e-6)                 # from the top edge
    assert z1 - z0 == pytest.approx(100.0 / math.tan(THETA_22P5_MRAD), abs=1e-6)


def test_mesa_sidewall_gentler_than_beam_is_lit():
    f = _feature(edge=EdgeProfile("linear", 0.01))               # 10 mrad < 22.5 mrad
    assert specular_feature(f).illumination_intervals_A == ()


def test_trench_narrower_than_shadow_floor_fully_shadowed():
    f = _feature(kind="trench", dims=(2000.0, 3000.0))
    (z0, z1), = specular_feature(f).illumination_intervals_A
    assert (z0, z1) == pytest.approx((-1000.0, 1000.0), abs=1e-9)


def test_trench_wider_than_shadow():
    f = _feature(kind="trench", dims=(10000.0, 3000.0))
    (z0, z1), = specular_feature(f).illumination_intervals_A
    assert z0 == pytest.approx(-5000.0, abs=1e-9)
    assert abs((z1 - z0) / 10.0 - 444.0) <= 0.5


def test_feature_mask_2d():
    f = _feature(edge=EdgeProfile("linear", 0.3), at="top")
    y = np.array([0.0, 1400.0, 1500.0 + 100.0 / math.tan(0.3) * 0.5, 5000.0])
    z = np.linspace(-6000.0, 12000.0, 1801)
    m = feature_shadow_mask(f, THETA_22P5_MRAD, THETA_LABEL, y, z, **SPECULAR_EXIT)
    lens = m.illumination_mask.sum(axis=1) * (z[1] - z[0])
    assert lens[0] == pytest.approx(lens[1], abs=20.0)           # on the top face: full height
    assert 0 < lens[2] < lens[1]                                 # on the side slope: lower
    assert lens[3] == 0                                          # outside the feature


def test_feature_inputs_required_and_checked():
    with pytest.raises(TypeError):
        PatternedFeature(kind="mesa", height_A=100.0, lateral_dimensions_A=(1.0, 1.0),
                         dimensions_at="top", orientation_deg=0.0, center_A=(0, 0),
                         label=FEATURE_LABEL)
    with pytest.raises(NotImplementedError):
        feature_shadow_intervals(_feature(orient=45.0), THETA_22P5_MRAD, THETA_LABEL,
                                 **SPECULAR_EXIT)
    with pytest.raises(NotImplementedError):
        feature_shadow_intervals(_feature(edge=EdgeProfile("gaussian", 0.2)), THETA_22P5_MRAD,
                                 THETA_LABEL, **SPECULAR_EXIT)
    with pytest.raises(ValueError, match="linear edge profile"):
        feature_shadow_intervals(_feature(edge=EdgeProfile("linear", None)), THETA_22P5_MRAD,
                                 THETA_LABEL, **SPECULAR_EXIT)
    with pytest.raises(ValueError, match="consume"):
        feature_shadow_intervals(_feature(dims=(100.0, 100.0), at="base",
                                          edge=EdgeProfile("linear", 0.3)),
                                 THETA_22P5_MRAD, THETA_LABEL, **SPECULAR_EXIT)
    bad = PatternedFeature(kind="mesa", height_A=100.0, lateral_dimensions_A=(1.0, 1.0),
                           dimensions_at="top", orientation_deg=0.0,
                           edge_profile=EdgeProfile("vertical", None), center_A=(0, 0),
                           label="from memory")
    with pytest.raises(ValueError, match="label"):
        feature_shadow_intervals(bad, THETA_22P5_MRAD, THETA_LABEL, **SPECULAR_EXIT)


def test_structure_shadow_lengths_use_geometry_module(monkeypatch):
    """Consolidation guard (S2): structure.shadows has no copy of the shadow-length formula; its
    labelled wrapper and the per-step nominal lengths of a built staircase are computed by the
    canonical geometry.projection.shadow_length_A (spy on the canonical function)."""
    from reflection_holo.geometry import projection
    from reflection_holo.structure import shadows as structure_shadows
    assert not hasattr(structure_shadows, "_shadow_length_A")
    canonical = projection.shadow_length_A
    calls = []

    def spy(h_A, theta_ext_rad):
        calls.append((h_A, theta_ext_rad))
        return canonical(h_A, theta_ext_rad)

    monkeypatch.setattr(projection, "shadow_length_A", spy)
    for h in (Q, 2 * Q, 100.0, 1000.0):
        for th in (0.0136, THETA_22P5_MRAD, 0.05):
            calls.clear()
            assert shadow_length_A(h, th, THETA_LABEL) == canonical(h, th)
            assert calls == [(h, th)]
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(30, 30),
                   boundary_step_layers=-1)
    s = build(st, edge_periods=1, substrate_layers=4)
    calls.clear()
    sh = specular_strips(s)
    down = [p for p in sh.per_step if p["upper_terrace_upstream"]]
    assert len(down) == 1 and (Q, THETA_22P5_MRAD) in calls
    assert down[0]["nominal_shadow_length_A"] == canonical(Q, THETA_22P5_MRAD)


# --- patterned features: both strips per edge (S2 follow-up 2) ------------------------------------
def _qshadow_reference(kind, half, h, z, th_in, th_out):
    """Independent reference for vertical edges: quantification.shadow.shadow_masks."""
    from reflection_holo.quantification.shadow import shadow_masks
    top = h if kind == "mesa" else -h
    return shadow_masks(z, edges_A=[-half, half], h_start_A=0.0, heights_after_A=[top, 0.0],
                        theta_in_ext_rad=th_in, theta_out_ext_rad=th_out)


@pytest.mark.parametrize("orient", [0.0, 90.0])
@pytest.mark.parametrize("kind", ["mesa", "trench"])
def test_feature_both_strips_per_edge_mesa_and_trench(kind, orient):
    """Vertical edges, h = 10 nm, (d1, d2) = (1000 nm, 300 nm) at the top; theta_in = 22.5 mrad,
    theta_out = 30 mrad (TEST_ONLY, non-specular so the two strips differ in length)."""
    h = 100.0
    f = _feature(kind=kind, h=h, dims=(10000.0, 3000.0), orient=orient)
    half = 0.5 * (10000.0 if orient == 0.0 else 3000.0)          # half-length along the beam
    l_in = h / math.tan(THETA_22P5_MRAD)                         # 4443.7 A
    l_out = h / math.tan(THETA_OUT_30MRAD)                       # 3332.3 A
    exit_30 = dict(theta_out_ext_rad=THETA_OUT_30MRAD, theta_out_label=THETA_OUT_LABEL)
    sh = feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL, **exit_30)
    up, down = sh.per_step
    assert (up["edge"], down["edge"]) == ("upstream", "downstream")
    if kind == "mesa":
        # front edge rises (upper side downstream): blocked view in front; back edge: shadow behind
        want_blk, want_ill = [-half - l_out, -half], [half, half + l_in]
        assert (up["strip"], down["strip"]) == ("blocked_view", "illumination_shadow")
    else:
        # front wall falls (upper side upstream): shadow on the floor behind it; back wall rises:
        # blocked view on the floor in front of it; each cut by the other wall on a short floor
        want_ill, want_blk = [-half, min(-half + l_in, half)], [max(half - l_out, -half), half]
        assert (up["strip"], down["strip"]) == ("illumination_shadow", "blocked_view")
    assert flat(sh.illumination_intervals_A) == pytest.approx(want_ill, abs=1e-9)
    assert flat(sh.blocked_view_intervals_A) == pytest.approx(want_blk, abs=1e-9)
    assert up["upper_terrace_upstream"] is (kind == "trench")
    assert down["upper_terrace_upstream"] is (kind == "mesa")
    for rec in (up, down):
        want_len = l_out if rec["strip"] == "blocked_view" else l_in
        assert rec["casts_strip"] and rec["nominal_length_A"] == pytest.approx(want_len, abs=1e-9)
        assert rec["sidewall_run_A"] == 0.0 and not rec["sidewall_in_strip"]
    # independent reference for vertical edges (quantification.shadow), away from strip ends
    z = np.linspace(-half - l_out - 500.0, half + l_in + 500.0, 4001)
    ends = np.array(flat(sh.illumination_intervals_A) + flat(sh.blocked_view_intervals_A))
    keep = np.min(np.abs(z[:, None] - ends[None, :]), axis=1) > 1e-6
    ref = _qshadow_reference(kind, half, h, z, THETA_22P5_MRAD, THETA_OUT_30MRAD)
    assert np.array_equal(sh.illumination_mask(z)[keep], ~ref.illuminated[keep])
    assert np.array_equal(sh.blocked_view_mask(z)[keep], ~ref.visible[keep])
    # the 2-D mask carries each strip alone and their union; a line outside the feature is clear
    m = feature_shadow_mask(f, THETA_22P5_MRAD, THETA_LABEL, [0.0, 10000.0], z, **exit_30)
    assert np.array_equal(m.illumination_mask[0], sh.illumination_mask(z))
    assert np.array_equal(m.blocked_view_mask[0], sh.blocked_view_mask(z))
    assert np.array_equal(m.mask, m.illumination_mask | m.blocked_view_mask)
    assert not m.mask[1].any()


def test_feature_sloped_edges_compared_with_their_own_ray_angle():
    """DERIVED_HERE rule for linear edges (module docstring): a wall steeper than the ray that meets
    it lies inside its strip, measured from the top edge; a wall at a lower angle casts none.
    theta_in = 22.5 mrad, theta_out = 30 mrad (TEST_ONLY)."""
    h = 100.0
    l_in = h / math.tan(THETA_22P5_MRAD)
    l_out = h / math.tan(THETA_OUT_30MRAD)
    kw = dict(theta_out_ext_rad=THETA_OUT_30MRAD, theta_out_label=THETA_OUT_LABEL)
    # alpha = 0.3 rad, steeper than both rays: the front wall [-2500 - run, -2500) lies inside the
    # blocked-view strip [-2500 - l_out, -2500); the back wall inside the shadow [2500, 2500 + l_in)
    run = h / math.tan(0.3)
    sh = feature_shadow_intervals(_feature(edge=EdgeProfile("linear", 0.3)), THETA_22P5_MRAD,
                                  THETA_LABEL, **kw)
    assert flat(sh.blocked_view_intervals_A) == pytest.approx([-2500.0 - l_out, -2500.0], abs=1e-6)
    assert flat(sh.illumination_intervals_A) == pytest.approx([2500.0, 2500.0 + l_in], abs=1e-6)
    up, down = sh.per_step
    assert up["sidewall_in_strip"] and down["sidewall_in_strip"]
    assert up["foot_A"] == pytest.approx(-2500.0 - run, abs=1e-9)
    assert up["nominal_strip_A"] == pytest.approx((-2500.0 - l_out, -2500.0), abs=1e-9)
    # alpha = 26 mrad: steeper than theta_in (the back wall shadows, 598 A beyond its foot) but
    # gentler than theta_out (the front wall blocks nothing)
    run = h / math.tan(0.026)
    sh = feature_shadow_intervals(_feature(edge=EdgeProfile("linear", 0.026)), THETA_22P5_MRAD,
                                  THETA_LABEL, **kw)
    assert sh.blocked_view_intervals_A == ()
    assert flat(sh.illumination_intervals_A) == pytest.approx([2500.0, 2500.0 + l_in], abs=1e-6)
    assert 2500.0 + l_in - (2500.0 + run) == pytest.approx(598.4, abs=0.05)
    up, down = sh.per_step
    assert not up["casts_strip"] and up["nominal_strip_A"] is None
    assert up["nominal_length_A"] == 0.0
    assert down["casts_strip"] and down["sidewall_in_strip"]
    # a trench with the same walls at the specular angle: the falling front wall (22.5 mrad ray)
    # shadows, the rising back wall (22.5 mrad ray) blocks as well
    sh = specular_feature(_feature(kind="trench", dims=(20000.0, 10000.0),
                                   edge=EdgeProfile("linear", 0.026)))
    assert flat(sh.illumination_intervals_A) == pytest.approx([-10000.0, -10000.0 + l_in],
                                                              abs=1e-6)
    assert flat(sh.blocked_view_intervals_A) == pytest.approx([10000.0 - l_in, 10000.0], abs=1e-6)


def test_feature_exit_angle_required_labelled_and_checked():
    f = _feature()
    with pytest.raises(TypeError, match="theta_out"):
        feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL)
    with pytest.raises(TypeError, match="theta_out"):
        feature_shadow_mask(f, THETA_22P5_MRAD, THETA_LABEL, [0.0], [0.0])
    with pytest.raises(ValueError, match="label"):
        feature_shadow_intervals(f, THETA_22P5_MRAD, THETA_LABEL, theta_out_ext_rad=0.03,
                                 theta_out_label="same as incidence")
    with pytest.raises(ValueError, match="theta_out_ext_rad"):
        feature_shadow_mask(f, THETA_22P5_MRAD, THETA_LABEL, [0.0], [0.0], theta_out_ext_rad=0.0,
                            theta_out_label=THETA_OUT_LABEL)
