"""Buried torus void (reflection_holo.structure.shapes.BuriedTorus, structure.features builder, agent
T3): the shape's rule and required inputs, and every builder assertion on the built structure and on
deliberately corrupted ones: no atom inside the void (h), the cap and the flat surface identical to
the flat build (i), the removed count against the analytic torus volume times the Si site density
(d), the flat top-layer height map (e), bond bookkeeping at the void wall (c), the void inside the
cell (f).

TEST_ONLY inputs: azimuths (item 8), feature geometries (item 13); lattice parameter ASSUMPTION B2.
Tolerances are the builder's stated ones, never loosened here.
"""
import dataclasses

import numpy as np
import pytest

from si001_test_inputs import AZIMUTH_LABEL, FEATURE_LABEL, LATTICE_LABEL
from reflection_holo.constants import A_SI_A, DIAMOND_BASIS
from reflection_holo.structure import checks
from reflection_holo.structure.checks import StructureAssertionError
from reflection_holo.structure.features import (
    HEIGHT_MAP_GRID_A, MIN_LAYERS_BELOW_FEATURE, assert_cap_intact, assert_feature_count,
    assert_feature_inside, assert_flat_top, assert_void_bond_bookkeeping, assert_void_empty,
    build_si001_flat_reference, build_si001_with_feature, buried_layer_window,
    feature_count_expectation, independent_feature_site_count, verify_feature_structure)
from reflection_holo.structure.lattice import neighbour_pairs
from reflection_holo.structure.shapes import BURIED_KIND, BuriedTorus, HalfTorus

A = A_SI_A
Q = A / 4.0
D_NN = A * np.sqrt(3.0) / 4.0
SRC = "TEST_ONLY geometry (tests/structure/test_features_buried.py)"


def void(yc, zc, R=20.0, r=6.0, cap=5.0):
    return BuriedTorus(center_y_A=yc, center_z_A=zc, major_radius_A=R, minor_radius_A=r, cap_A=cap,
                       label=FEATURE_LABEL, source=SRC)


def _p(az):
    return A if az in ((1, 0, 0), (0, 1, 0)) else A / np.sqrt(2.0)


def build(*, az=(1, 0, 0), py=13, pz=13, depth=24, R=20.0, r=6.0, cap=5.0, yc=None, zc=None,
          margin=None):
    p = _p(az)
    Ly, Lz = py * p, pz * p
    f = void(0.5 * Ly if yc is None else yc, 0.5 * Lz if zc is None else zc, R, r, cap)
    return build_si001_with_feature(azimuth_uvw=az, azimuth_label=AZIMUTH_LABEL, feature=f,
                                    extent_y_A=Ly, extent_z_A=Lz, depth_layers=depth,
                                    lattice_parameter_A=A, lattice_label=LATTICE_LABEL,
                                    ring_margin_A=p if margin is None else margin,
                                    vacuum_above_A=10.0)


def flat(*, az=(1, 0, 0), py=13, pz=13, depth=24):
    p = _p(az)
    return build_si001_flat_reference(azimuth_uvw=az, azimuth_label=AZIMUTH_LABEL,
                                      extent_y_A=py * p, extent_z_A=pz * p, depth_layers=depth,
                                      lattice_parameter_A=A, lattice_label=LATTICE_LABEL,
                                      vacuum_above_A=10.0)


@pytest.fixture(scope="module")
def buried():
    return build()


@pytest.fixture(scope="module")
def flat_ref():
    return flat()


@pytest.fixture(scope="module", params=[5.0, 10.0, 20.0, 30.0], ids=lambda c: f"cap{c:g}")
def demo_caps(request):
    """The study radii R = 50 A, r = 12 A and caps on a short 27 x 27 period [100] cell."""
    cap = request.param
    depth = int(np.ceil((cap + 24.0) / Q)) + MIN_LAYERS_BELOW_FEATURE + 3
    return build(py=27, pz=27, depth=depth, R=50.0, r=12.0, cap=cap, margin=2 * A)


def rows(a):
    return {tuple(v) for v in np.round(np.asarray(a, float), 6)}


def corrupted(s, positions):
    return dataclasses.replace(s, positions_A=np.asarray(positions, float))


def brute_force_ideal(frame, Ly, Lz, depth, feature):
    """Independent construction: conventional cells x DIAMOND_BASIS, slab window, void rule written
    out here: (rho - R)^2 + (x_rel + cap + r)^2 < r^2 removed."""
    l_s = depth - 1
    nmax = int(np.ceil(np.sqrt(2.0) * max(Ly, Lz) / A)) + 2
    rng = np.arange(-nmax, nmax + 1)
    cells = np.stack(np.meshgrid(rng, rng, np.arange(-1, depth // 4 + 5), indexing="ij"),
                     -1).reshape(-1, 3)
    sites = (cells[:, None, :] + DIAMOND_BASIS[None]).reshape(-1, 3) * A
    rs = frame.to_slab(sites)
    lay = np.rint(rs[:, 0] / Q).astype(int)
    t = 1e-6
    w = ((rs[:, 1] >= -t) & (rs[:, 1] < Ly - t) & (rs[:, 2] >= -t) & (rs[:, 2] < Lz - t)
         & (lay >= 0) & (lay <= l_s))
    rs, lay = rs[w], lay[w]
    if feature is not None:
        rho = np.hypot(rs[:, 1] - feature.center_y_A, rs[:, 2] - feature.center_z_A)
        x_rel = (lay - l_s) * Q
        gone = ((rho - feature.major_radius_A) ** 2
                + (x_rel + feature.cap_A + feature.minor_radius_A) ** 2
                < feature.minor_radius_A ** 2)
        rs = rs[~gone]
    out = rs.copy()
    out[:, 1:][np.abs(out[:, 1:]) < t] = 0.0
    return out


# ---- the shape --------------------------------------------------------------------------------
def test_every_field_required_and_validated():
    kw = dict(center_y_A=0.0, center_z_A=0.0, major_radius_A=20.0, minor_radius_A=6.0, cap_A=5.0,
              label=FEATURE_LABEL, source=SRC)
    for k in kw:
        with pytest.raises(TypeError):
            BuriedTorus(**{kk: v for kk, v in kw.items() if kk != k})
    for bad in (dict(cap_A=0.0), dict(cap_A=-1.0), dict(minor_radius_A=20.0),
                dict(minor_radius_A=0.0), dict(major_radius_A=np.nan), dict(cap_A=np.inf),
                dict(cap_A=True), dict(label=""), dict(source="")):
        with pytest.raises(ValueError):
            BuriedTorus(**dict(kw, **bad))


def test_shape_rule_and_derived_geometry():
    f = void(100.0, 200.0, R=50.0, r=12.0, cap=10.0)
    assert f.kind == BURIED_KIND == "buried_void"
    assert f.tube_centre_x_rel_A == -22.0
    assert f.void_top_x_rel_A == -10.0 and f.void_bottom_x_rel_A == -34.0
    assert np.isclose(f.volume_A3, 2 * np.pi ** 2 * 50 * 144)
    assert np.isclose(f.surface_A2, 4 * np.pi ** 2 * 50 * 12)
    y_on = 100.0 + 50.0                                     # on the ring (rho = R), z = z_c
    assert f.contains(-22.0, y_on, 200.0)                   # tube centre line
    eps = 1e-9
    assert f.contains(-10.0 - eps, y_on, 200.0) and not f.contains(-10.0, y_on, 200.0)  # top
    assert f.contains(-34.0 + eps, y_on, 200.0) and not f.contains(-34.0, y_on, 200.0)  # bottom
    assert not f.contains(-22.0, y_on + 12.0, 200.0) and f.contains(-22.0, y_on + 12.0 - eps, 200.0)
    assert not f.contains(-22.0, 100.0, 200.0)              # ring centre: crystal
    assert not f.contains(0.0, y_on, 200.0)                 # the surface above is never removed
    assert np.isclose(f.distance_to_tube_centre_line_A(-22.0 + 3.0, y_on + 4.0, 200.0), 5.0)
    # the flat surface is untouched: zero height (what the geometric engine would see)
    y, z = np.meshgrid(np.linspace(0, 200, 41), np.linspace(100, 300, 37), indexing="ij")
    assert np.all(f.layer_height_A(y, z, layer_spacing_A=Q) == 0.0)
    assert np.all(f.continuous_height_A(y, z) == 0.0) and f.layer_height_A(y, z, layer_spacing_A=Q
                                                                           ).shape == y.shape
    with pytest.raises(ValueError):
        f.layer_height_A(y, z, layer_spacing_A=0.0)
    assert np.isclose(f.footprint_half_width_A(y_on, 200.0), 12.0)


def test_layer_window_is_strictly_between_void_top_and_bottom():
    for cap in (5.0, 4 * Q, 10.0, 30.0):
        f = void(0, 0, R=50.0, r=12.0, cap=cap)
        lo, hi = buried_layer_window(f, 60, Q)
        t = 1e-9                                            # floating-point slack only
        assert (hi - 60) * Q < -cap + t and (hi + 1 - 60) * Q >= -cap - t
        assert (lo - 60) * Q > f.void_bottom_x_rel_A - t
        assert (lo - 1 - 60) * Q <= f.void_bottom_x_rel_A + t


# ---- the built set -----------------------------------------------------------------------------
@pytest.mark.parametrize("az", [(1, 0, 0), (1, 1, 0)])
def test_atoms_equal_independent_ideal_set(az):
    kw = dict(py=13, pz=13) if az == (1, 0, 0) else dict(py=20, pz=20)
    s = build(az=az, depth=22, **kw)
    ideal = brute_force_ideal(s.frame, s.cell_A[1, 1], s.cell_A[2, 2], 22, s.feature)
    assert len(ideal) == s.n_atoms
    assert rows(ideal) == rows(s.positions_A)
    checks.assert_on_lattice_sites(s.positions_A, s.frame, np.zeros(3), A)
    assert s.metadata["feature"]["kind"] == "buried_void"


def test_cap_and_surface_identical_to_the_flat_build(buried, flat_ref):
    """Every layer at or above the void top (x_rel >= -cap) and every layer below the void is the
    flat build's layer atom for atom; built + removed = flat, disjoint."""
    l_s = 23
    F = flat_ref.positions_A
    B = buried.positions_A
    lf = np.rint(F[:, 0] / Q) - l_s
    lb = np.rint(B[:, 0] / Q) - l_s
    f = buried.feature
    untouched = lambda l: (l * Q >= -f.cap_A) | (l * Q <= f.void_bottom_x_rel_A)
    assert rows(F[untouched(lf)]) == rows(B[untouched(lb)])
    assert rows(F[lf == 0]) == rows(B[lb == 0])                        # the flat top layer
    assert rows(B) | rows(buried.feature_sites_A) == rows(F)
    assert not rows(B) & rows(buried.feature_sites_A)
    cap = buried.metadata["checks"]["cap"]
    assert cap["highest_removed_layer_x_rel_A"] < -f.cap_A
    assert cap["intact_cap_layers"] >= int(np.floor(f.cap_A / Q)) + 1        # 4 layers at 5 A
    assert np.max(np.rint(B[:, 0] / Q)) == l_s                          # nothing above the surface


def test_h_no_atom_inside_the_void(buried):
    rec = buried.metadata["checks"]["void_empty"]
    pos = buried.positions_A
    f = buried.feature
    x_rel = pos[:, 0] - 23 * Q
    d = np.hypot(np.hypot(pos[:, 1] - f.center_y_A, pos[:, 2] - f.center_z_A) - f.major_radius_A,
                 x_rel - f.tube_centre_x_rel_A)
    assert d.min() >= f.minor_radius_A
    assert np.isclose(rec["min_distance_to_tube_centre_line_A"], d.min())
    assert rec["clearance_A"] >= 0.0
    # a removed site put back: (h) on the positions, and (a) (feature rule) in the full verify
    back = np.vstack([pos, buried.feature_sites_A[:1]])
    with pytest.raises(StructureAssertionError, match=r"\(h\) 1 atom\(s\) inside the buried void"):
        assert_void_empty(back, f, 23 * Q, A)
    with pytest.raises(StructureAssertionError, match=r"\(a\).*violate the buried_void rule"):
        verify_feature_structure(corrupted(buried, back))


def test_i_fails_on_a_missing_cap_or_surface_atom(buried):
    l_s = 23
    pos = buried.positions_A
    lay = np.rint(pos[:, 0] / Q).astype(int)
    per_layer = 2 * 13 * 13
    f = buried.feature
    rec = assert_cap_intact(lay, buried.feature_sites_A, f, l_s, Q, per_layer)
    assert rec["complete_layers"] == l_s + 1 - (rec["void_layer_window"][1]
                                                - rec["void_layer_window"][0] + 1)
    # the atom of the lowest cap layer closest to the tube centre line (directly above the void)
    cap_l = rec["void_layer_window"][1] + 1
    m = np.nonzero(lay == cap_l)[0]
    d = f.distance_to_tube_centre_line_A((lay[m] - l_s) * Q, pos[m, 1], pos[m, 2])
    k = int(m[np.argmin(d)])
    with pytest.raises(StructureAssertionError, match=r"\(i\) layer .* the cap / flat surface is "
                                                      r"not intact"):
        assert_cap_intact(np.delete(lay, k), buried.feature_sites_A, f, l_s, Q, per_layer)
    top = int(np.nonzero(lay == l_s)[0][0])
    with pytest.raises(StructureAssertionError, match=r"\(i\) layer 23 "):
        assert_cap_intact(np.delete(lay, top), buried.feature_sites_A, f, l_s, Q, per_layer)
    # the full verification refuses the same structure (count (b) is checked first)
    with pytest.raises(StructureAssertionError, match=r"\(b\) atom count"):
        verify_feature_structure(corrupted(buried, np.delete(pos, k, axis=0)))
    # a removed site recorded in the cap is refused
    fs = buried.feature_sites_A.copy()
    fs[0, 0] = (l_s - 1) * Q
    with pytest.raises(StructureAssertionError, match=r"\(i\) removed site"):
        assert_cap_intact(lay, fs, f, l_s, Q, per_layer)


# ---- (b) counts -------------------------------------------------------------------------------
def test_b_counts(buried):
    c = buried.metadata["checks"]["count"]
    assert c["built"] == buried.n_atoms == c["flat_slab_count"] - c["feature_sites_independent"]
    assert c["feature_sites_independent"] == len(buried.feature_sites_A)
    assert independent_feature_site_count(buried.feature, buried.frame, A, 23) == \
        len(buried.feature_sites_A)
    assert buried.metadata["feature"]["n_removed"] == len(buried.feature_sites_A) > 0


# ---- (c) bonds ---------------------------------------------------------------------------------
def test_c_bond_bookkeeping(buried):
    rec = buried.metadata["checks"]["void_bonds"]
    assert rec["n_atoms_bonded_to_the_void"] > 0
    assert set(rec["missing_bonds_histogram"]) <= {1, 2, 3}
    pos = buried.positions_A
    per = [None, buried.cell_A[1, 1], buried.cell_A[2, 2]]
    lay = np.rint(pos[:, 0] / Q).astype(int)
    i, j, d, _ = neighbour_pairs(pos, per, 1.05 * D_NN)
    assert abs(d.min() - D_NN) < checks.POSITION_TOL_A
    # independent count: bonds of the flat build that end on a removed site
    F = np.vstack([pos, buried.feature_sites_A])
    fi, fj, _, _ = neighbour_pairs(F, per, 1.05 * D_NN)
    n = len(pos)
    to_removed = np.bincount(fi[(fi < n) & (fj >= n)], minlength=n)
    coord = np.bincount(i, minlength=n)
    interior = (lay >= 1) & (lay <= 22)
    assert np.all(coord[interior] + to_removed[interior] == 4)
    assert int(np.sum(to_removed > 0)) == rec["n_atoms_bonded_to_the_void"]
    # one removed site dropped from the record: its neighbours no longer balance
    with pytest.raises(StructureAssertionError, match=r"\(c\) bond bookkeeping"):
        assert_void_bond_bookkeeping(pos, lay, i, buried.feature_sites_A[1:], 23, A)


# ---- (d) count vs torus volume ------------------------------------------------------------------
def test_d_tolerance_is_the_surface_shell():
    f = void(0, 0, R=50.0, r=12.0, cap=10.0)
    e = feature_count_expectation(f, A)
    n = 8 / A ** 3
    assert np.isclose(e["expected_count"], n * 2 * np.pi ** 2 * 50 * 144)      # 7098.0
    assert np.isclose(e["relative_tolerance"], A / (4 * 12))                  # a/(4 r) = 11.3 %
    assert e["flat_face_bias_count"] == 0.0


def test_d_passes_at_the_study_radii_and_caps(demo_caps):
    v = demo_caps.metadata["checks"]["volume_count"]
    assert abs(v["deviation"]) <= v["tolerance_count"]
    assert v["measured_count"] == len(demo_caps.feature_sites_A)
    assert demo_caps.metadata["checks"]["height_map"]["built_top_range_A"] == [0.0, 0.0]
    assert demo_caps.metadata["checks"]["cap"]["highest_removed_layer_x_rel_A"] < \
        -demo_caps.feature.cap_A


def test_d_fails_on_wrong_count(buried):
    n = len(buried.feature_sites_A)
    e = feature_count_expectation(buried.feature, A)
    with pytest.raises(StructureAssertionError, match=r"\(d\).*full-torus"):
        assert_feature_count(int(n + 2 * e["tolerance_count"]), buried.feature, A)
    with pytest.raises(StructureAssertionError, match=r"\(d\)"):
        assert_feature_count(n, dataclasses.replace(buried.feature, minor_radius_A=3.0), A)


# ---- (e) flat surface --------------------------------------------------------------------------
def test_e_flat_top_everywhere(buried):
    h = buried.metadata["checks"]["height_map"]
    assert h["n_checked"] == h["n_points"] and h["n_checked_inside_ring"] > 0
    assert h["built_top_range_A"] == [0.0, 0.0] and h["exclusion_distance_A"] == 0.0
    pos = buried.positions_A
    f = buried.feature
    lay = np.rint(pos[:, 0] / Q)
    rho = np.hypot(pos[:, 1] - f.center_y_A, pos[:, 2] - f.center_z_A)
    k = int(np.nonzero((lay == 23) & (np.abs(rho - f.major_radius_A) < 1.5))[0][0])  # over the void
    with pytest.raises(StructureAssertionError, match=r"\(e\) the flat surface above the buried "
                                                      r"void is not intact"):
        assert_flat_top(np.delete(pos, k, axis=0), buried.frame, A, 23, f, buried.cell_A[1, 1],
                        buried.cell_A[2, 2], HEIGHT_MAP_GRID_A)


# ---- (f) inside the cell ------------------------------------------------------------------------
def test_f_void_inside_and_depth_refusal(buried):
    ins = buried.metadata["checks"]["inside"]
    assert ins["intact_layers_below_void"] >= MIN_LAYERS_BELOW_FEATURE
    assert ins["intact_layers_above_void"] == buried.metadata["checks"]["cap"]["intact_cap_layers"]
    # r = 6, cap = 5: void bottom at x_rel = -17 A; 16 layers leave < 4 intact layers below it
    with pytest.raises(ValueError, match="too thin for a buried void"):
        build(depth=16)
    with pytest.raises(StructureAssertionError, match=r"\(f\) the ring"):
        build(yc=20.0)
    fs = buried.feature_sites_A.copy()
    fs[0, 1] = 0.5 * A
    with pytest.raises(StructureAssertionError, match=r"\(f\)"):
        assert_feature_inside(fs, buried.feature, 23, Q, np.diag(buried.cell_A), A)


# ---- (g) frame, metadata, refusals --------------------------------------------------------------
def test_g_metadata_and_refusals(buried):
    md = buried.metadata
    f = md["feature"]
    assert f["shape"] == "reflection_holo.structure.shapes.BuriedTorus"
    assert f["cap_A"] == 5.0 and f["label"] == FEATURE_LABEL and f["source"] == SRC
    assert np.isclose(f["void_top_x_A"], 23 * Q - 5.0)
    assert np.isclose(f["void_bottom_x_A"], 23 * Q - 17.0)
    assert f["top_layer_x_range_A"] == [23 * Q, 23 * Q]
    assert len(md["assertions_passed"]) == 9
    assert [p[:3] for p in md["assertions_passed"]] == ["(g)", "(a)", "(b)", "(c)", "(d)", "(e)",
                                                        "(f)", "(h)", "(i)"]
    with pytest.raises(ValueError):
        build_si001_with_feature(azimuth_uvw=(1, 0, 0), azimuth_label=AZIMUTH_LABEL,
                                 feature=dataclasses.replace(buried.feature, label="guess"),
                                 extent_y_A=13 * A, extent_z_A=13 * A, depth_layers=24,
                                 lattice_parameter_A=A, lattice_label=LATTICE_LABEL,
                                 ring_margin_A=A, vacuum_above_A=10.0)
    with pytest.raises(TypeError):
        build_si001_with_feature(azimuth_uvw=(1, 0, 0), azimuth_label=AZIMUTH_LABEL,
                                 feature=object(), extent_y_A=13 * A, extent_z_A=13 * A,
                                 depth_layers=24, lattice_parameter_A=A,
                                 lattice_label=LATTICE_LABEL, ring_margin_A=A, vacuum_above_A=10.0)
    assert isinstance(HalfTorus, type)       # the half torus is untouched (T1 tests)
