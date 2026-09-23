"""Half-torus feature builder (reflection_holo.structure.features): every assertion (a) to (g) of the
module docstring, each on the built structure and on a deliberately corrupted one.

TEST_ONLY inputs: azimuths (item 8), feature geometries (item 13); lattice parameter ASSUMPTION B2.
Tolerances are the builder's stated ones (checks.POSITION_TOL_A etc.), never loosened here.
"""
import dataclasses

import numpy as np
import pytest

from si001_test_inputs import AZIMUTH_LABEL, FEATURE_LABEL, LATTICE_LABEL, brute_force_pairs
from reflection_holo.constants import A_SI_A, DIAMOND_BASIS
from reflection_holo.geometry.frames import SurfaceFrame, surface_frame
from reflection_holo.structure import Staircase, build_si001_terraces, checks
from reflection_holo.structure.checks import StructureAssertionError
from reflection_holo.structure.features import (
    HEIGHT_MAP_GRID_A, MIN_LAYERS_BELOW_FEATURE, assert_feature_count, assert_feature_inside,
    assert_height_map, build_si001_flat_reference, build_si001_with_feature,
    feature_count_expectation, feature_layer_counts, independent_feature_site_count,
    verify_feature_structure)
from reflection_holo.structure.shapes import HalfTorus

A = A_SI_A
Q = A / 4.0
SRC = "TEST_ONLY geometry (tests/structure/test_features_torus.py)"


def torus(kind, yc, zc, R=20.0, r=6.0):
    return HalfTorus(center_y_A=yc, center_z_A=zc, major_radius_A=R, minor_radius_A=r, kind=kind,
                     label=FEATURE_LABEL, source=SRC)


def build(kind, *, az=(1, 0, 0), py=13, pz=13, depth=12, R=20.0, r=6.0, yc=None, zc=None,
          margin=None):
    p = A if az in ((1, 0, 0), (0, 1, 0)) else A / np.sqrt(2.0)
    Ly, Lz = py * p, pz * p
    f = torus(kind, 0.5 * Ly if yc is None else yc, 0.5 * Lz if zc is None else zc, R, r)
    return build_si001_with_feature(azimuth_uvw=az, azimuth_label=AZIMUTH_LABEL, feature=f,
                                    extent_y_A=Ly, extent_z_A=Lz, depth_layers=depth,
                                    lattice_parameter_A=A, lattice_label=LATTICE_LABEL,
                                    ring_margin_A=p if margin is None else margin,
                                    vacuum_above_A=10.0)


def flat(*, az=(1, 0, 0), py=13, pz=13, depth=12):
    p = A if az in ((1, 0, 0), (0, 1, 0)) else A / np.sqrt(2.0)
    return build_si001_flat_reference(azimuth_uvw=az, azimuth_label=AZIMUTH_LABEL,
                                      extent_y_A=py * p, extent_z_A=pz * p, depth_layers=depth,
                                      lattice_parameter_A=A, lattice_label=LATTICE_LABEL,
                                      vacuum_above_A=10.0)


@pytest.fixture(scope="module")
def trench():
    return build("trench")


@pytest.fixture(scope="module")
def ridge():
    return build("ridge")


@pytest.fixture(scope="module")
def flat100():
    return flat()


@pytest.fixture(scope="module")
def small():
    """R = 10 A, r = 4 A on an 8 x 8 period [100] cell (small enough for O(N^2) brute force)."""
    kw = dict(py=8, pz=8, depth=9, R=10.0, r=4.0)
    return dict(trench=build("trench", **kw), ridge=build("ridge", **kw),
                flat=flat(py=8, pz=8, depth=9))


@pytest.fixture(scope="module", params=["trench", "ridge"])
def demo_radii(request):
    """The demo radii R = 50 A, r = 12 A on a short 27 x 27 period [100] cell."""
    return build(request.param, py=27, pz=27, depth=14, R=50.0, r=12.0, margin=2 * A)


def corrupted(s, positions):
    return dataclasses.replace(s, positions_A=np.asarray(positions, float))


def rows(a):
    """Set of positions rounded to 1e-6 A (for set comparisons)."""
    return {tuple(v) for v in np.round(np.asarray(a, float), 6)}


def brute_force_ideal(kind_or_none, frame, Ly, Lz, depth, feature):
    """Independent construction: conventional cells x DIAMOND_BASIS, slab window, feature rule."""
    l_s = depth - 1
    nmax = int(np.ceil(np.sqrt(2.0) * max(Ly, Lz) / A)) + 2
    rng = np.arange(-nmax, nmax + 1)
    cells = np.stack(np.meshgrid(rng, rng, np.arange(-1, depth // 4 + 5), indexing="ij"),
                     -1).reshape(-1, 3)
    sites = (cells[:, None, :] + DIAMOND_BASIS[None]).reshape(-1, 3) * A
    rs = frame.to_slab(sites)
    lay = np.rint(rs[:, 0] / Q).astype(int)
    t = 1e-6
    w = (rs[:, 1] >= -t) & (rs[:, 1] < Ly - t) & (rs[:, 2] >= -t) & (rs[:, 2] < Lz - t) & (lay >= 0)
    rs, lay = rs[w], lay[w]
    base = lay <= l_s
    if kind_or_none is None:
        keep = base
    else:
        inside = feature.contains((lay - l_s) * Q, rs[:, 1], rs[:, 2])
        keep = (base & ~inside) if kind_or_none == "trench" else (base | ((lay > l_s) & inside))
    out = rs[keep]
    out[:, 1:][np.abs(out[:, 1:]) < t] = 0.0
    return out


# ---- requests --------------------------------------------------------------------------------
def test_every_argument_required():
    f = torus("trench", 35.0, 35.0)
    kw = dict(azimuth_uvw=(1, 0, 0), azimuth_label=AZIMUTH_LABEL, feature=f, extent_y_A=13 * A,
              extent_z_A=13 * A, depth_layers=12, lattice_parameter_A=A,
              lattice_label=LATTICE_LABEL, ring_margin_A=A, vacuum_above_A=10.0)
    for k in kw:
        bad = {kk: v for kk, v in kw.items() if kk != k}
        with pytest.raises(TypeError):
            build_si001_with_feature(**bad)
    with pytest.raises(ValueError, match="label"):
        build_si001_with_feature(**dict(kw, lattice_label=""))
    with pytest.raises(ValueError, match="label"):
        build_si001_with_feature(**dict(kw, azimuth_label="demo"))
    with pytest.raises(ValueError, match="PROJECT_INPUT item 13"):
        build_si001_with_feature(**dict(kw, feature=None))
    with pytest.raises(ValueError):
        build_si001_with_feature(**dict(kw, feature=dataclasses.replace(f, label="guess")))
    with pytest.raises(ValueError, match="integer number of in-plane lattice periods"):
        build_si001_with_feature(**dict(kw, extent_y_A=70.0))


def test_ring_must_fit_with_the_stated_margin():
    with pytest.raises(StructureAssertionError, match=r"\(f\) the ring"):
        build("trench", yc=20.0)                         # ring box reaches y < margin
    with pytest.raises(StructureAssertionError, match="stated minimum"):
        build("trench", margin=0.5 * A)                  # margin below one in-plane period
    with pytest.raises(StructureAssertionError, match=r"\(f\) the ring"):
        build("ridge", zc=13 * A - 20.0)


def test_trench_needs_intact_layers_below():
    N = feature_layer_counts(torus("trench", 35, 35), Q)       # r = 6: 4 -> layers 0..-4 removed
    assert N == 4
    with pytest.raises(ValueError, match="too thin"):
        build("trench", depth=N + MIN_LAYERS_BELOW_FEATURE)
    s = build("trench", depth=N + 1 + MIN_LAYERS_BELOW_FEATURE)
    assert s.metadata["checks"]["inside"]["intact_layers_below_trench"] >= MIN_LAYERS_BELOW_FEATURE


# ---- (a) lattice sites, one continuous lattice -----------------------------------------------
@pytest.mark.parametrize("kind", ["trench", "ridge"])
@pytest.mark.parametrize("az", [(1, 0, 0), (1, 1, 0)])
def test_atoms_equal_independent_ideal_set(kind, az):
    s = build(kind, az=az, py=13 if az == (1, 0, 0) else 20, pz=13 if az == (1, 0, 0) else 20)
    Ly, Lz = s.cell_A[1, 1], s.cell_A[2, 2]
    ideal = brute_force_ideal(kind, s.frame, Ly, Lz, 12, s.feature)
    assert len(ideal) == s.n_atoms
    assert rows(ideal) == rows(s.positions_A)
    checks.assert_on_lattice_sites(s.positions_A, s.frame, np.zeros(3), A)


def test_trench_and_ridge_are_the_same_continuous_lattice(small):
    trench, ridge = small["trench"], small["ridge"]
    F = rows(small["flat"].positions_A)
    assert rows(trench.positions_A) | rows(trench.feature_sites_A) == F
    assert not rows(trench.positions_A) & rows(trench.feature_sites_A)
    assert rows(ridge.positions_A) == F | rows(ridge.feature_sites_A)
    # every added ridge atom is a site of the slab's lattice (same origin) and bonds to it
    checks.assert_on_lattice_sites(ridge.feature_sites_A, ridge.frame, np.zeros(3), A)
    d = brute_force_pairs(ridge.positions_A, ridge.cell_A[1, 1], ridge.cell_A[2, 2], 3.0)
    assert abs(d.min() - A * np.sqrt(3) / 4) < 1e-9


def test_flat_reference_equals_si001_builder(flat100):
    """The flat slab is the si001 builder's lattice: a single 13-period terrace with its top at
    crystal layer 11 (odd, back-bond axis [1,1,0]) coincides atom for atom."""
    st = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(13,),
                   boundary_step_layers=0)
    s = build_si001_terraces(azimuth_uvw=(1, 0, 0), azimuth_label=AZIMUTH_LABEL, staircase=st,
                             edge_periods=13, substrate_layers=12,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A,
                             lattice_parameter_label=LATTICE_LABEL)
    assert np.allclose(s.crystal_origin_slab_A, 0.0)
    assert rows(s.positions_A) == rows(flat100.positions_A)


def test_a_fails_on_displaced_atom(trench):
    pos = trench.positions_A.copy()
    pos[100, 1] += 0.05
    with pytest.raises(StructureAssertionError, match=r"\(a\).*off the a/4 grid"):
        verify_feature_structure(corrupted(trench, pos))


def test_a_fails_on_site_violating_the_feature_rule(trench):
    """A true lattice site above the flat surface (not part of a trench) is refused."""
    l_s = trench.request["depth_layers"] - 1
    top = trench.positions_A[np.rint(trench.positions_A[:, 0] / Q) == l_s - 1][0]  # cell corner
    # fcc translation (a/2)(1,0,1) (crystal): a site of the same lattice two layers higher
    extra = top + trench.frame.to_slab(np.array([0.5, 0.0, 0.5]) * A)
    assert np.rint(extra[0] / Q) == l_s + 1
    extra[1] %= trench.cell_A[1, 1]
    extra[2] %= trench.cell_A[2, 2]
    with pytest.raises(StructureAssertionError, match=r"\(a\).*violate the trench rule"):
        verify_feature_structure(corrupted(trench, np.vstack([trench.positions_A, extra])))


# ---- (b) window, duplicates, count, periodic margin ------------------------------------------
def test_b_passes_and_records_counts(trench, ridge):
    for s, sign in ((trench, -1), (ridge, +1)):
        c = s.metadata["checks"]["count"]
        assert c["built"] == s.n_atoms == c["flat_slab_count"] + sign * c["feature_sites_independent"]
        assert c["feature_sites_independent"] == len(s.feature_sites_A)
        assert independent_feature_site_count(s.feature, s.frame, A, 11) == len(s.feature_sites_A)


def test_b_fails_on_duplicate_atom(ridge):
    pos = np.vstack([ridge.positions_A, ridge.positions_A[:1]])
    with pytest.raises(StructureAssertionError, match=r"\(b\) duplicate"):
        verify_feature_structure(corrupted(ridge, pos))


def test_b_fails_on_periodic_image(ridge):
    i = int(np.argmin(ridge.positions_A[:, 1]))
    img = ridge.positions_A[i] + np.array([0.0, ridge.cell_A[1, 1], 0.0])
    with pytest.raises(StructureAssertionError, match=r"\(b\)"):
        verify_feature_structure(corrupted(ridge, np.vstack([ridge.positions_A, img])))


def test_b_fails_on_missing_atom_far_from_the_ring(trench):
    far = int(np.argmin(trench.positions_A[:, 1] + trench.positions_A[:, 2]))   # cell corner
    pos = np.delete(trench.positions_A, far, axis=0)
    with pytest.raises(StructureAssertionError, match=r"\(b\) atom count"):
        verify_feature_structure(corrupted(trench, pos))


# ---- (c) distances and coordination ----------------------------------------------------------
def test_c_minimum_distance_is_bulk_nn(small):
    d_nn = A * np.sqrt(3.0) / 4.0
    for s in (small["trench"], small["ridge"]):
        d = brute_force_pairs(s.positions_A, s.cell_A[1, 1], s.cell_A[2, 2], 3.0)
        assert abs(d.min() - d_nn) < checks.POSITION_TOL_A
        hist = s.metadata["checks"]["coordination_histogram"]
        assert 0 not in hist and max(hist) == 4


def test_c_fails_on_too_close_atoms(trench):
    pos = trench.positions_A.copy()
    per = [None, trench.cell_A[1, 1], trench.cell_A[2, 2]]
    i, j, _, vec = checks.assert_min_distance_and_coordination(pos, per, A, None)
    pos[i[0]] += 0.3 * vec[0] / np.linalg.norm(vec[0])      # 0.3 A towards a neighbour
    with pytest.raises(StructureAssertionError, match=r"\(c\)"):
        checks.assert_min_distance_and_coordination(pos, per, A, None)


# ---- (d) count vs half-torus volume ----------------------------------------------------------
def test_d_tolerance_is_the_surface_shell():
    f = torus("ridge", 0, 0, R=50.0, r=12.0)
    e = feature_count_expectation(f, A)
    n = 8 / A ** 3
    assert np.isclose(e["expected_count"], n * np.pi ** 2 * 50 * 144)
    # relative tolerance (a/8) S / V = (a/8) (2/r + 4/(pi r))
    assert np.isclose(e["relative_tolerance"], A / 8 * (2 / 12 + 4 / (np.pi * 12)))
    assert np.isclose(e["flat_face_bias_count"], -n * A / 8 * 4 * np.pi * 50 * 12)


def test_d_passes_at_demo_radii(demo_radii):
    v = demo_radii.metadata["checks"]["volume_count"]
    assert abs(v["deviation"]) <= v["tolerance_count"]
    assert v["measured_count"] == len(demo_radii.feature_sites_A)
    # the sign of the deviation is the flat-face bias (layer x_rel = 0 in the trench, not the ridge)
    assert np.sign(v["deviation"]) == np.sign(v["flat_face_bias_count"])


def test_d_fails_on_wrong_count(demo_radii):
    n = len(demo_radii.feature_sites_A)
    with pytest.raises(StructureAssertionError, match=r"\(d\)"):
        assert_feature_count(2 * n, demo_radii.feature, A)
    with pytest.raises(StructureAssertionError, match=r"\(d\)"):
        assert_feature_count(n, dataclasses.replace(demo_radii.feature, minor_radius_A=6.0), A)


# ---- (e) height map --------------------------------------------------------------------------
def test_e_height_map_equals_layer_height(demo_radii):
    h = demo_radii.metadata["checks"]["height_map"]
    assert h["n_checked_inside_ring"] > 0 and h["n_checked"] > 0.3 * h["n_points"]
    # every disagreement lies within the covering radius a/2 of the layer net (nearest-site rule)
    assert h["max_boundary_distance_of_disagreement_A"] <= A / 2
    lo, hi = h["built_top_range_A"]
    if demo_radii.feature.kind == "trench":
        assert np.isclose(lo, -9 * Q) and hi == 0.0      # layers 0..-8 removed at r = 12 A
    else:
        assert lo == 0.0 and np.isclose(hi, 8 * Q)       # layers 1..8 added


def _height_map(s, pos):
    return assert_height_map(pos, s.frame, A, s.request["depth_layers"] - 1, s.feature,
                             s.cell_A[1, 1], s.cell_A[2, 2], HEIGHT_MAP_GRID_A)


def test_e_fails_on_missing_top_atom_in_the_flat_region(ridge):
    l_s = ridge.request["depth_layers"] - 1
    pos = ridge.positions_A
    f = ridge.feature
    rho = np.hypot(pos[:, 1] - f.center_y_A, pos[:, 2] - f.center_z_A)
    reach = f.major_radius_A + f.minor_radius_A
    k = np.nonzero((np.rint(pos[:, 0] / Q) == l_s) & (rho > reach + 5.0)
                   & (np.abs(pos[:, 1] - f.center_y_A) < reach + 7.0)
                   & (np.abs(pos[:, 2] - f.center_z_A) < reach + 7.0))[0][0]
    with pytest.raises(StructureAssertionError, match=r"\(e\)"):
        _height_map(ridge, np.delete(pos, k, axis=0))


def test_e_fails_on_wrong_feature_top_layer(demo_radii):
    """Ridge crest layer (+8 a/4) removed, or trench floor layer (-8 a/4) refilled."""
    s = demo_radii
    l_s = s.request["depth_layers"] - 1
    pos = s.positions_A
    lay = np.rint(pos[:, 0] / Q)
    if s.feature.kind == "ridge":
        pos = pos[lay != lay.max()]                                   # crest layer 8 removed
    else:
        refill = s.feature_sites_A[np.rint(s.feature_sites_A[:, 0] / Q) == l_s - 8]
        pos = np.vstack([pos, refill])                                # trench floor raised
    with pytest.raises(StructureAssertionError, match=r"\(e\)"):
        _height_map(s, pos)


# ---- (f) inside the cell ---------------------------------------------------------------------
def test_f_feature_inside(trench, ridge):
    assert trench.metadata["checks"]["inside"]["intact_layers_below_trench"] >= 4
    assert ridge.metadata["checks"]["inside"]["box_top_clearance_A"] > 0


def test_f_fails_on_feature_site_outside_the_ring_box(ridge):
    fs = ridge.feature_sites_A.copy()
    fs[0, 1] = 0.5 * ridge.request["ring_margin_A"]
    with pytest.raises(StructureAssertionError, match=r"\(f\)"):
        assert_feature_inside(fs, ridge.feature, 11, Q, np.diag(ridge.cell_A),
                              ridge.request["ring_margin_A"])


# ---- (g) frame and metadata ------------------------------------------------------------------
def test_g_frame_and_metadata(trench):
    checks.assert_frame(trench.frame, (0, 0, 1))
    assert np.allclose(trench.frame.z_hat, [1, 0, 0])
    md = trench.metadata
    assert md["feature"]["label"] == FEATURE_LABEL and md["feature"]["source"] == SRC
    assert md["feature"]["n_removed"] == len(trench.feature_sites_A)
    assert set(np.unique(trench.Z)) == {14}
    assert len(md["assertions_passed"]) == 7
    bad = dataclasses.replace(trench, frame=surface_frame((0, 0, 1), (1, 1, 0)))
    with pytest.raises(StructureAssertionError, match=r"\(a\)"):
        verify_feature_structure(bad)            # atoms are not sites of the [110]-frame lattice
    left = SurfaceFrame((0, 0, 1), (1, 0, 0), np.array([[0.0, 0, 1], [0, 1, 0], [1, 0, 0]]))
    with pytest.raises(StructureAssertionError, match=r"\(g\)"):
        verify_feature_structure(dataclasses.replace(trench, frame=left))
