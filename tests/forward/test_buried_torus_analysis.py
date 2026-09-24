"""tools/plots/buried_torus.py (T3's buried-void analysis, revised by agent T4 after audit A9a M-2,
m-2, m-5, m-6): the region definitions, the identical-cell assertion, the x-location, the apodised
vacuum-origin split applied BEFORE the specular aperture, the steepest in-band systematic beam, the
supervisor-facing wording (no detection rule, no fitted lengths, the geometric zero stated as a
consequence of the surface-height model). The script is imported with importlib, as the tests of
scripts/torus and tools/reflection_step_phase_calculator.py do. Nothing is written to disk.

T5 (re-audit A10a) adds: the mask family and its refusal of masks admitting the top atomic plane
(M1), the band-edge causal path and the band edge read from the exit-wave metadata (m-2), analyse_pair
on synthetic exit waves with a known vacuum-only, end-face-only and mixed difference and the cap-5
reading wired from it (m-3), and the compact figure's shared colour scale and titles (m-4).

TEST_ONLY inputs: synthetic grids, waves and lattice sites; lattice parameter ASSUMPTION B2; 200 keV.
"""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.multislice.physics import beam_constants
from reflection_holo.geometry.frames import surface_frame

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "plots" / "buried_torus.py"
A = A_SI_A
Q = A / 4.0
LAM = beam_constants(200.0)["wavelength_A"]
TH_OUT = 16.1347e-3          # TEST_ONLY angles (as the T3 runs)
TH_INT = 18.4719e-3


@pytest.fixture(scope="module")
def bt():
    spec = importlib.util.spec_from_file_location("buried_torus_t4_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ew(psi, dx=0.125, dy=0.125):
    return SimpleNamespace(psi=psi, dx_A=dx, dy_A=dy, x0_A=0.0, y0_A=0.0,
                           metadata=dict(beam=dict(wavelength_A=LAM), theta_out_ext_rad=TH_OUT))


# ---- the apodised vacuum mask and the split (M-2) ---------------------------------------------
def test_vacuum_mask_shape(bt):
    x = np.linspace(-5, 5, 2001)
    m = bt.vacuum_mask(x, 2.5)
    assert np.all(m[x <= 0] == 0.0) and np.all(m[x >= 2.5] == 1.0)
    assert np.all(np.diff(m) >= 0)
    assert bt.vacuum_mask(np.array([1.25]), 2.5)[0] == pytest.approx(0.5, abs=1e-12)
    assert bt.VAC_RAMP_A == bt.RES_A == 2.5
    for bad in (0.0, -1.0, np.inf, np.nan):
        with pytest.raises(ValueError):
            bt.vacuum_mask(x, bad)


def _plane(nx=240, ny=64, dx=0.125, x_surf_index=120):
    x_rel = (np.arange(nx) - x_surf_index) * dx
    return x_rel, nx, ny


def test_split_is_linear_and_exact(bt):
    x_rel, nx, ny = _plane()
    rng = np.random.default_rng(1)
    D = rng.normal(size=(nx, ny)) + 1j * rng.normal(size=(nx, ny))
    ew = _ew(np.zeros((nx, ny), complex))
    p = bt.split_parts(D, ew, x_rel)
    np.testing.assert_allclose(p["vacuum_origin"] + p["end_face"], p["total"], rtol=0,
                               atol=1e-12 * np.abs(p["total"]).max())
    np.testing.assert_allclose(p["total"], bt.specular_of(D, ew), rtol=0, atol=1e-12)


def test_end_face_signal_leaks_through_the_aperture_but_not_into_the_vacuum_origin_part(bt):
    """The A9a M-2 mechanism: a difference confined to the crystal (x_rel <= 0) appears in the
    vacuum pixels after the sharp aperture; its vacuum-origin part is exactly zero."""
    x_rel, nx, ny = _plane()
    ew = _ew(np.zeros((nx, ny), complex))
    fc = np.sin(TH_OUT) / LAM
    X = x_rel[:, None] * np.ones((1, ny))
    D = np.where((X <= 0) & (X > -6), np.exp(2j * np.pi * fc * X), 0.0)      # end-face band
    p = bt.split_parts(D, ew, x_rel)
    vac = (x_rel > 0.5) & (x_rel < 5.0)
    assert np.abs(p["total"][vac]).max() > 1e-2          # leakage through the aperture
    assert np.abs(p["vacuum_origin"]).max() == 0.0       # the mask acts before the aperture
    # a difference confined to x_rel >= ramp has no end-face part
    D2 = np.where(X >= 2.5, np.exp(2j * np.pi * fc * X), 0.0)
    p2 = bt.split_parts(D2, ew, x_rel)
    assert np.abs(p2["end_face"]).max() == 0.0


# ---- regions (DERIVED_HERE definitions) ----------------------------------------------------------
def _g(bt, cap, R=20.0, r=6.0, nx=400, ny=200, dx=0.125, dy=0.5):
    x = np.arange(nx) * dx
    xs = 25.0
    Lz = 1526.0
    g = dict(x=x, y=np.arange(ny) * dy, x_rel=x - xs, xs=xs, Lz=Lz, th_out=TH_OUT, th_int=TH_INT,
             yc=50.0, zc=1027.0, R=R, r=r, cap=cap, lam=LAM,
             row=bt.steepest_row_beam(A, dx, LAM), crystal_start_z_A=27.0,
             core_z0_A=190.0, contact_z_A=62.0)
    return g


def test_regions_follow_their_definitions(bt):
    g = _g(bt, cap=5.0)
    reg = bt.regions(g, g["core_z0_A"])
    X, Y = np.meshgrid(g["x_rel"], g["y"], indexing="ij")
    to, ti = np.tan(TH_OUT), np.tan(TH_INT)
    zmin, zmax = g["zc"] - 26.0, g["zc"] + 26.0
    geom = reg["geom"]
    assert geom["x_V_two_beam_A"] == pytest.approx((g["Lz"] - zmin - 5.0 / ti) * to, rel=1e-12)
    assert geom["x_projection_A"] == pytest.approx([(g["Lz"] - zmax) * to, (g["Lz"] - zmin) * to])
    assert geom["surfacing_distance_void_top_two_beam_A"] == pytest.approx(5.0 / ti)
    ring_y = np.abs(Y - 50.0) <= 26.0 + bt.RES_A
    # V: vacuum, below x_V + d, ring band; VAC: vacuum up to 25 A, ring band
    assert reg["V"].any()
    assert np.all(X[reg["V"]] > 0) and np.all(X[reg["V"]] <= geom["x_V_two_beam_A"] + bt.RES_A)
    assert np.all(ring_y[reg["V"]]) and np.all(ring_y[reg["VAC"]])
    assert np.all((X[reg["VAC"]] > 0) & (X[reg["VAC"]] <= bt.VAC_BAND_A))
    # P: every projected-annulus pixel is in P, and P lies within d of it
    zs = g["Lz"] - X / to
    proj = (X > 0) & (np.abs(np.hypot(Y - 50.0, zs - g["zc"]) - 20.0) < 6.0)
    assert proj.any() and np.all(reg["P"][proj])
    assert np.all(X[reg["P"]] > geom["x_projection_A"][0] - bt.RES_A - 0.2)
    # E inside the crystal only; the references outside the ring's projection
    assert np.all(X[reg["E"]] < 0)
    assert np.all(X[reg["C_up"]] >= geom["x_projection_A"][1] + 2 * bt.RES_A - 1e-9)
    assert np.all(np.abs(Y[reg["C_y"]] - 50.0) >= 26.0 + 2 * bt.RES_A)
    assert not np.any(reg["P"] & reg["C_up"])


def test_deep_cap_has_no_two_beam_vacuum_region(bt):
    g = _g(bt, cap=30.0)
    reg = bt.regions(g, g["core_z0_A"])
    assert reg["geom"]["x_V_two_beam_A"] + bt.RES_A <= 0
    assert not reg["V"].any()
    assert reg["P"].any() and reg["VAC"].any()
    assert bt.vacuum_class(reg["geom"]["x_V_two_beam_A"]) == "no_two_beam_path"


def test_vacuum_class_is_geometric(bt):
    assert bt.vacuum_class(4.68) == "shown"
    assert bt.vacuum_class(0.317) == "not_demonstrated"
    assert bt.vacuum_class(-9.0) == "no_two_beam_path"
    assert bt.vacuum_class(bt.RES_A) == "shown"


def test_steepest_row_beam(bt):
    s = bt.steepest_row_beam(A, 0.127826, LAM)              # T3's grid: (0,0,16) inside the band
    assert s["l"] == 16
    assert s["fx_per_A"] == pytest.approx(12.0 / A, rel=1e-12)
    assert s["angle_rad"] == pytest.approx(np.arcsin(LAM * 12.0 / A), rel=1e-12)
    assert s["fx_per_A"] <= s["band_edge_fx_per_A"] < (16.0 / A)
    assert bt.steepest_row_beam(A, 0.2, LAM)["l"] == 12     # coarser grid: (0,0,16) cut


# ---- assert_same_cell (the flat = cap + void check) ----------------------------------------------
def _pair():
    fr = surface_frame((0, 0, 1), (1, 0, 0))
    grid = np.array([(i, j, k) for i in range(4) for j in range(3) for k in range(3)], float) * Q
    void = grid[[5, 17, 30]]
    cap = np.delete(grid, [5, 17, 30], axis=0)
    md = dict(cell=dict(extent_x_A=10.0, extent_y_A=5.0, length_z_A=100.0, crystal_start_z_A=2.0,
                        surface_x_A=4.0),
              absorbers=dict(numerical="x"), theta_out_ext_rad=TH_OUT, slices=dict(dz_A=Q),
              potential=dict(physical_absorption=dict(ratio=0.1)), band_limit=dict(rule="2/3"))

    def ew():
        return SimpleNamespace(psi=np.zeros((4, 3), complex), dx_A=0.1, dy_A=0.1, x0_A=0.0,
                               y0_A=0.0, z_A=100.0, energy_keV=200.0, theta_in_ext_rad=TH_OUT,
                               plane="exit plane", metadata=json.loads(json.dumps(md)))

    def st(pos, fs):
        return dict(positions_A=pos, feature_sites_A=fs, cell_A=np.eye(3),
                    physical_absorption=dict(ratio=0.1), metadata=dict(lattice=dict(a_A=A)),
                    frame=fr)

    return ew, st, grid, cap, void


def test_assert_same_cell_passes_and_counts(bt):
    ew, st, grid, cap, void = _pair()
    rec = bt.assert_same_cell(ew(), ew(), st(cap, void), st(grid, np.zeros((0, 3))))
    assert (rec["n_atoms_flat"], rec["n_atoms_cap"], rec["n_removed"]) == (36, 33, 3)


def test_assert_same_cell_refusals(bt):
    ew, st, grid, cap, void = _pair()
    flat = st(grid, np.zeros((0, 3)))
    moved = cap.copy()
    moved[0, 0] += Q
    with pytest.raises(ValueError, match="flat reference minus the void"):
        bt.assert_same_cell(ew(), ew(), st(moved, void), flat)
    with pytest.raises(ValueError, match="flat reference minus the void"):
        bt.assert_same_cell(ew(), ew(), st(grid, void), flat)          # void sites not removed
    e = ew()
    e.dx_A = 0.11
    with pytest.raises(ValueError, match="differ in dx_A"):
        bt.assert_same_cell(e, ew(), st(cap, void), flat)
    e = ew()
    e.metadata["potential"]["physical_absorption"]["ratio"] = 0.0
    with pytest.raises(ValueError, match="physical_absorption"):
        bt.assert_same_cell(e, ew(), st(cap, void), flat)
    s2 = st(cap, void)
    s2["physical_absorption"] = dict(ratio=0.0)
    with pytest.raises(ValueError, match="structure files record different"):
        bt.assert_same_cell(ew(), ew(), s2, flat)


# ---- x_centroid and cross_cap ---------------------------------------------------------------------
def test_x_centroid(bt):
    x_rel = np.arange(-60.0, 25.0, 0.5)
    g = dict(x_rel=x_rel)
    diff = np.zeros((x_rel.size, 4))
    diff[x_rel == -10.0, :2] = 1.0          # 2 units at -10 A
    diff[x_rel == 8.0, :2] = 3.0            # 6 units at +8 A (in vacuum)
    diff[x_rel == 8.0, 2:] = 100.0          # outside the y band: ignored
    loc = bt.x_centroid(diff, g, np.array([True, True, False, False]))
    assert loc["peak_x_rel_A"] == 8.0
    assert loc["centroid_x_rel_A"] == pytest.approx((2 * -10.0 + 6 * 8.0) / 8.0)
    assert loc["fraction_in_vacuum"] == pytest.approx(0.75)


def test_cross_cap(bt):
    rng = np.random.default_rng(2)
    F = rng.normal(size=(20, 10)) + 1j * rng.normal(size=(20, 10))
    R = np.zeros((20, 10), bool)
    R[5:15, 2:8] = True
    c = bt.cross_cap(F, 2j * F, R, 2.0)
    assert c["abs_corr"] == pytest.approx(1.0)
    assert c["rms_b"] == pytest.approx(2 * c["rms_a"])


# ---- wording (A9a M-1, M-2, m-2, m-6) -------------------------------------------------------------
def test_no_detection_rule_and_no_fitted_lengths(bt):
    assert not hasattr(bt, "FLOOR_FACTOR") and not hasattr(bt, "fit_decay")
    rec = dict(n_pixels=10, max_abs_dphi_rad=1e-3, rms_dphi_rad=1e-4, max_abs_ratio_minus_1=2e-3,
               max_rel_diff=3e-3, rms_rel_diff=4e-4)
    res = dict(cap=10.0, metrics=dict(regions={k: dict(rec) for k in bt.REGIONS}),
               metrics_vac=dict(regions={k: dict(rec) for k in bt.REGIONS}))
    res["metrics"]["regions"]["V"] = dict(n_pixels=0)
    lines = bt._fmt_table([res], "metrics", "TOTAL")
    text = "\n".join(lines)
    assert "[" not in text                       # no value / floor ratios
    assert "leakage references, not a noise floor" in text
    assert "empty" in text
    for word in ("detected", "marginal", "x floor"):
        assert word not in text


def _geom_for_reading(bt, cap, x_V):
    """TEST_ONLY geometry record for reading_line (T5: the causal paths, P's extent, the cell length
    and V's source points are now required inputs of the reading)."""
    g = _g(bt, cap)
    reg = bt.regions(g, g["core_z0_A"])
    geom = dict(reg["geom"])
    geom["x_V_two_beam_A"] = x_V
    return geom


def _family(lo_hi: dict, n=9):
    rows = [dict(label=f"m{i}", **{k: v[0] + (v[1] - v[0]) * i / (n - 1) for k, v in lo_hi.items()})
            for i in range(n)]
    return dict(region="V", rows=rows, range={k: list(v) for k, v in lo_hi.items()})


def test_reading_lines(bt):
    # T4's assertions, unchanged; T5 supplies the inputs the revised reading needs (A10a-M1, m-2)
    geom = dict(_geom_for_reading(bt, 10.0, 0.317), surfacing_distance_void_top_two_beam_A=541.3)
    m = dict(max_rel_diff=8e-3, max_abs_dphi_rad=6e-3, max_abs_ratio_minus_1=8e-3)
    fam = _family(dict(max_abs_dphi_rad=(1.3e-4, 5.4e-3), max_abs_ratio_minus_1=(1.3e-4, 3.3e-3),
                       max_rel_diff=(1.7e-4, 5.0e-3)))
    line = bt.reading_line(10.0, geom, m, dict(max_rel_diff=1.7e-3), 8.5e-3, m, m, family=fam)
    assert "NOT DEMONSTRATED" in line and "0.317 A" in line
    geom = dict(_geom_for_reading(bt, 30.0, -17.0), surfacing_distance_void_top_two_beam_A=1623.9)
    line = bt.reading_line(30.0, geom, m, m, 0.0, dict(max_rel_diff=1.6e-4),
                           dict(max_rel_diff=1.59e-4), family=fam)
    assert "no two-beam path" in line and "NOT DEMONSTRATED" in line and "0.00016" in line
    geom = dict(_geom_for_reading(bt, 5.0, 4.68), surfacing_distance_void_top_two_beam_A=270.7)
    fam5 = _family(dict(max_abs_dphi_rad=(0.0274, 0.0789), max_abs_ratio_minus_1=(0.026, 0.103),
                        max_rel_diff=(0.0304, 0.105)))
    line = bt.reading_line(5.0, geom, m, dict(max_rel_diff=0.085, max_abs_dphi_rad=0.034,
                                              max_abs_ratio_minus_1=0.086), 0.1, m, m, family=fam5,
                           loc_vac=dict(peak_x_rel_A=2.64, centroid_x_rel_A=0.32),
                           raw_frac_first_res=0.52)
    assert "no dose model" in line and "NOT RUN" in line
    for w in ("detected", "marginal", "floor"):
        assert w not in line


def test_geometric_zero_statement(bt):
    s = bt.geometric_zero_statement("buried_cap5A_r010", 0.0, -0.0)
    assert "zero by construction of the surface-height model" in s
    assert "not a geometric-engine run" in s


# ==================================================================================================
# T5 (re-audit A10a): mask family (M1), band-edge causal path (m-2), analyse wiring on synthetic exit
# waves (m-3), compact figure on one shared scale (m-4). TEST_ONLY synthetic inputs; 200 keV.
# ==================================================================================================
A10A_NINE = ((0.0, 0.0), (0.0, 1.0), (0.0, 2.5), (0.0, 5.0), (1.0, 1.0), (2.5, 2.5),
             (A / 8, 0.0), (A / 8, 2.5), (A / 4, 2.5))


def test_mask_family_is_a10a_nine_and_admits_nothing_at_or_below_the_top_plane(bt):
    fam = bt.mask_family(A)
    assert [(s, w) for _, s, w in fam] == [pytest.approx(v) for v in A10A_NINE]
    assert len({lab for lab, _, _ in fam}) == 9
    x = np.linspace(-6.0, 12.0, 14401)
    for lab, s, w in fam:
        m = bt.family_mask(x, s, w)
        assert np.all(m[x <= 0.0] == 0.0) and np.all(m[x <= s] == 0.0), lab
        assert np.all(m[x >= s + w + 1e-12] == 1.0) and np.all(np.diff(m) >= 0), lab
        assert np.all((m >= 0) & (m <= 1)), lab
    # the main mask of the family is T4's vacuum_mask, bit for bit
    main = [f for f in fam if "main mask" in f[0]]
    assert len(main) == 1 and main[0][1:] == (0.0, bt.VAC_RAMP_A)
    np.testing.assert_array_equal(bt.family_mask(x, 0.0, bt.VAC_RAMP_A), bt.vacuum_mask(x, 2.5))
    # a mask admitting the top atomic plane or below (e.g. A10a's ramp centred on it) is refused
    for bad in ((-1.25, 2.5), (-1e-9, 0.0), (np.nan, 1.0), (0.0, -1.0), (0.0, np.inf)):
        with pytest.raises(ValueError):
            bt.family_mask(x, *bad)
    with pytest.raises(ValueError):
        bt.mask_family(0.0)


def test_causal_paths_band_edge_row_and_two_beam(bt):
    """V16 with the (0,0,16) angle, the band edge asin(lambda / (3 dx)) and the aperture's steepest
    accepted exit angle; every reach from the formula of the module docstring."""
    for cap in (5.0, 10.0, 20.0, 30.0):
        g = _g(bt, cap)
        reg = bt.regions(g, g["core_z0_A"])
        geom = reg["geom"]
        zmin = g["zc"] - g["R"] - g["r"]
        to = np.tan(TH_OUT)
        a16 = np.arcsin(LAM * 12.0 / A)
        abe = np.arcsin(LAM / (3 * 0.125))
        aap = np.arcsin(np.sin(TH_OUT) + LAM * 0.2)
        assert geom["x_V16_A"] == pytest.approx((g["Lz"] - zmin - cap / np.tan(a16)) * to, rel=1e-12)
        assert geom["surfacing_distance_void_top_steepest_row_beam_A"] == pytest.approx(
            cap / np.tan(a16), rel=1e-12)
        cp = geom["causal_paths"]
        assert cp["aperture_max_exit_angle_rad"] == pytest.approx(aap, rel=1e-12)
        assert set(cp["paths"]) == {"two_beam", "row_0_0_16", "band_edge"}
        for key, ang in (("two_beam", TH_INT), ("row_0_0_16", a16), ("band_edge", abe)):
            p = cp["paths"][key]
            d = cap / np.tan(ang)
            assert p["internal_angle_rad"] == pytest.approx(ang, rel=1e-12)
            assert p["surfacing_distance_void_top_A"] == pytest.approx(d, rel=1e-12)
            assert p["reach_x_rel_at_theta_out_A"] == pytest.approx((g["Lz"] - zmin - d) * to,
                                                                    rel=1e-12)
            assert p["reach_x_rel_at_aperture_max_A"] == pytest.approx(
                (g["Lz"] - zmin - d) * np.tan(aap), rel=1e-12)
        # consistency with the regions: V and V16 are the two-beam and row reaches at theta_out
        assert cp["paths"]["two_beam"]["reach_x_rel_at_theta_out_A"] == pytest.approx(
            geom["x_V_two_beam_A"], rel=1e-12)
        assert cp["paths"]["row_0_0_16"]["reach_x_rel_at_theta_out_A"] == pytest.approx(
            geom["x_V16_A"], rel=1e-12)
        s = [cp["paths"][k]["surfacing_distance_void_top_A"] for k in ("band_edge", "row_0_0_16",
                                                                       "two_beam")]
        assert s[0] < s[1] < s[2]


def test_causal_paths_on_t3_geometry_match_the_independent_a10a_values(bt):
    """T3's cell geometry (values from its exit-wave and structure files) against A10a's independent
    recomputation (SP/a10a/split_family.out), to its printed digits."""
    lam = 0.02507934045046928
    row = bt.steepest_row_beam(A, 0.12782609599395314, lam)
    assert row["band_edge_fx_per_A"] == pytest.approx(2.607709566199235, rel=1e-9)
    base = dict(th_out=0.016134748438027965, th_int=0.018471894068541668, lam=lam, zc=1027.1545,
                R=50.0, r=12.0, Lz=1526.0829, row=row)
    a10a = {5.0: (76.3, 7.82, 10.25), 10.0: (152.6, 6.59, 8.64), 20.0: (305.2, 4.13, 5.41),
            30.0: (457.7, 1.67, 2.18)}
    for cap, (d, r1, r2) in a10a.items():
        cp = bt.causal_paths(dict(base, cap=cap))
        be = cp["paths"]["band_edge"]
        assert be["surfacing_distance_void_top_A"] == pytest.approx(d, abs=0.05)
        assert be["reach_x_rel_at_theta_out_A"] == pytest.approx(r1, abs=0.005)
        assert be["reach_x_rel_at_aperture_max_A"] == pytest.approx(r2, abs=0.005)
        assert 1e3 * cp["aperture_max_exit_angle_rad"] == pytest.approx(21.15, abs=0.005)


def test_band_edge_vs_P_wording(bt):
    def geom(r1, r2):
        return dict(causal_paths=dict(paths=dict(band_edge=dict(reach_x_rel_at_theta_out_A=r1,
                                                                reach_x_rel_at_aperture_max_A=r2))),
                    P_x_rel_A=[4.68, 11.46], x_projection_A=[7.05, 9.05])
    assert "both reaches lie below region P" in bt.band_edge_vs_P(geom(1.67, 2.18))
    s = bt.band_edge_vs_P(geom(4.13, 5.41))
    assert "enters P but stays below the ring's undilated projection" in s
    assert "both reaches lie below" not in s
    assert "an in-band causal path to region P" in bt.band_edge_vs_P(geom(7.8, 10.25))
    for r in ((1.67, 2.18), (4.13, 5.41), (7.8, 10.25)):
        assert "not a hard edge" in bt.band_edge_vs_P(geom(*r))


# ---- synthetic pair of exit waves through analyse_pair (A10a-m3) -----------------------------------
NX, NY, DX, DY, XS = 512, 96, 0.125, 0.75, 32.0
FC = 41.0 / (NX * DX)                       # on an FFT bin: the flat plane wave passes the aperture
TH_OUT_S = float(np.arcsin(LAM * FC))       # TEST_ONLY exit angle (16.07 mrad)


def _meta(fx_max=1.0 / (3 * DX), rule="2/3"):
    return dict(cell=dict(surface_x_A=XS, length_z_A=1526.0, crystal_start_z_A=27.0),
                slices=dict(dz_A=Q), beam=dict(wavelength_A=LAM), theta_out_ext_rad=TH_OUT_S,
                theta_int_out_rad=TH_INT,
                illumination=dict(x_bottom_A=XS + 1.0, edge_A=2.0, theta_in_ext_rad=TH_OUT_S),
                band_limit=dict(rule=rule, fx_max_per_A=fx_max))


def _wave(psi, meta=None):
    return SimpleNamespace(psi=psi, dx_A=DX, dy_A=DY, x0_A=0.0, y0_A=0.0, z_A=1526.0,
                           energy_keV=200.0, metadata=meta or _meta())


def _st(cap):
    return dict(cell_feature=dict(center_y_A=36.0, center_z_A=1027.0, major_radius_A=20.0,
                                  minor_radius_A=6.0, cap_A=cap),
                metadata=dict(lattice=dict(a_A=A)))


def _x_rel():
    return np.arange(NX) * DX - XS


def _carrier():
    return np.exp(2j * np.pi * FC * (_x_rel() + XS))[:, None] * np.ones((1, NY))


def _d_vacuum(amp=0.05j):
    """Known VACUUM-ONLY difference: a Hann bump on 6 <= x_rel <= 18 A (beyond every mask's ramp)."""
    x = _x_rel()
    b = np.where((x >= 6.0) & (x <= 18.0), np.sin(np.pi * (x - 6.0) / 12.0) ** 2, 0.0)
    return amp * b[:, None] * _carrier()


def _d_end_face(amp=0.2):
    """Known END-FACE-ONLY difference: a sharp band -6 < x_rel <= 0 (inside the crystal)."""
    x = _x_rel()
    return amp * ((x > -6.0) & (x <= 0.0)).astype(float)[:, None] * _carrier()


def _d_layer(amp=0.04j):
    """A difference inside the first resolution layer, 0.5 < x_rel < 3 A (mask-dependent)."""
    x = _x_rel()
    return amp * ((x > 0.5) & (x < 3.0)).astype(float)[:, None] * _carrier()


def _synthetic_pair(bt, D, cap=5.0):
    flat = _carrier()
    return bt.analyse_pair(_wave(flat + D), _wave(flat), _st(cap), cap, "synthetic")


def test_raw_fraction_first_layer_known_answer(bt):
    x_rel = np.arange(-40.0, 40.0, 0.5)
    g = dict(x_rel=x_rel)
    D = np.zeros((x_rel.size, 4), complex)
    D[(x_rel > 0) & (x_rel <= 2.5), :2] = 1.0            # 5 pixels x 2 columns, |D|^2 = 1
    D[(x_rel > 2.5) & (x_rel <= 25.0), :2] = np.sqrt(3.0 * 5 / 45)   # 45 pixels, total power 3x
    D[(x_rel > 25.0) | (x_rel <= 0.0), :2] = 7.0          # outside the vacuum band: ignored
    D[:, 2:] = 9.0                                        # outside the y band: ignored
    f = bt.raw_fraction_first_layer(D, g, np.array([True, True, False, False]))
    assert f == pytest.approx(0.25, rel=1e-12)
    assert np.isnan(bt.raw_fraction_first_layer(np.zeros_like(D), g, np.ones(4, bool)))


def test_x_centroid_of_a_zero_profile_is_nan(bt):
    x_rel = np.arange(-60.0, 25.0, 0.5)
    loc = bt.x_centroid(np.zeros((x_rel.size, 3)), dict(x_rel=x_rel), np.ones(3, bool))
    assert all(np.isnan(v) for v in loc.values())


def test_geometry_reads_and_asserts_the_band_edge(bt):
    g = bt.geometry(_wave(_carrier()), _st(5.0))
    assert g["row"]["band_edge_fx_per_A"] == pytest.approx(1.0 / (3 * DX), rel=1e-12)
    assert g["a_A"] == A and g["energy_keV"] == 200.0
    with pytest.raises(ValueError, match="band edge in the exit-wave metadata"):
        bt.geometry(_wave(_carrier(), _meta(fx_max=2.0)), _st(5.0))
    with pytest.raises(ValueError, match="2/3 rule"):
        bt.geometry(_wave(_carrier(), _meta(rule="1/2")), _st(5.0))


def test_analyse_pair_end_face_only_difference_has_no_vacuum_origin_part(bt):
    res = _synthetic_pair(bt, _d_end_face(0.3j))
    reg, met, mv = res["regions"], res["metrics"]["regions"], res["metrics_vac"]["regions"]
    assert bt.vacuum_class(reg["geom"]["x_V_two_beam_A"]) == "shown" and reg["V"].any()
    assert res["metrics"]["A_ref"] == pytest.approx(1.0, abs=1e-12)
    # the total over the vacuum regions is aperture leakage of the end face (A9a M-2) ...
    assert met["V"]["max_rel_diff"] > 1e-2 and met["V"]["max_abs_dphi_rad"] > 1e-2
    # ... and the vacuum-origin part is exactly zero there (|dpsi| and |rho - 1| bit-exact; the phase
    # arg(pf conj(pf)) of an unchanged wave is 0 up to the rounding of the complex product, which
    # may use a fused multiply-add: bound 1e-15 rad), for the main mask and every family member
    for k in ("V", "P", "VAC", "V16", "C_up"):
        assert mv[k]["max_rel_diff"] == 0.0 and mv[k]["max_abs_ratio_minus_1"] == 0.0, k
        assert mv[k]["max_abs_dphi_rad"] <= 1e-15, k
    assert res["family"]["region"] == "V" and len(res["family"]["rows"]) == 9
    for row in res["family"]["rows"]:
        assert row["max_rel_diff"] == 0.0 and row["max_abs_ratio_minus_1"] == 0.0, row["label"]
        assert row["max_abs_dphi_rad"] <= 1e-15 and row["P_max_rel_diff"] == 0.0, row["label"]
    assert res["family"]["range"]["max_rel_diff"] == [0.0, 0.0]
    # the whole vacuum-side total is end-face part
    assert res["end_face_max"]["V"] == pytest.approx(met["V"]["max_rel_diff"], rel=1e-9)
    assert np.isnan(res["raw_frac_first_res"])          # no vacuum-side raw difference at all


def test_analyse_pair_vacuum_only_difference_is_all_vacuum_origin(bt):
    res = _synthetic_pair(bt, _d_vacuum())
    met, mv = res["metrics"]["regions"], res["metrics_vac"]["regions"]
    for k in ("V", "P", "VAC", "V16", "C_up", "C_y"):
        for q in ("max_rel_diff", "max_abs_dphi_rad", "max_abs_ratio_minus_1", "rms_rel_diff"):
            if q in met[k]:
                assert mv[k][q] == pytest.approx(met[k][q], rel=1e-9, abs=1e-15), (k, q)
    assert all(v == 0.0 for v in res["end_face_max"].values())
    # known answer: psi_s = psi_flat (1 + 0.05 i b), b <= 1 (aperture ringing of the Hann bump
    # below 1 %)
    assert mv["VAC"]["max_rel_diff"] == pytest.approx(0.05, rel=1e-2)
    assert mv["VAC"]["max_abs_dphi_rad"] == pytest.approx(np.arctan(0.05), rel=1e-2)
    assert 10.0 < res["loc_vac"]["peak_x_rel_A"] < 14.0
    rows = res["family"]["rows"]
    for row in rows:          # every member of the family admits the whole bump
        for q in bt.FAMILY_METRICS:
            assert row[q] == pytest.approx(rows[0][q], rel=1e-9, abs=1e-15), (row["label"], q)
        assert row[q] == pytest.approx(mv["V"][q], rel=1e-9, abs=1e-15)
    assert res["raw_frac_first_res"] == 0.0


def test_analyse_pair_mixed_difference_wiring_and_cap5_reading(bt):
    """vacuum + end face + first-layer difference: the main mask's metrics are the family's main
    member; the family spreads; the cap-5 reading quotes the family RANGE, not the total."""
    res = _synthetic_pair(bt, _d_vacuum() + _d_end_face(0.3j) + _d_layer())
    fam, mv, met = res["family"], res["metrics_vac"]["regions"], res["metrics"]["regions"]
    main = [row for row in fam["rows"] if "main mask" in row["label"]][0]
    for q in bt.FAMILY_METRICS:
        assert main[q] == mv["V"][q]
        vals = [row[q] for row in fam["rows"]]
        assert fam["range"][q] == [min(vals), max(vals)]
    lo, hi = fam["range"]["max_abs_dphi_rad"]
    assert hi > 1.05 * lo                                    # the first layer makes it mask-dependent
    assert met["V"]["max_abs_dphi_rad"] > 1.05 * hi          # and the total is larger still
    assert 0.0 < res["raw_frac_first_res"] < 1.0
    line = bt.reading_for(res)
    assert line.startswith("cap 5 A: in this 1499 A cell")
    assert f"is {lo:.3g}-{hi:.3g} rad in phase" in line
    rlo, rhi = fam["range"]["max_abs_ratio_minus_1"]
    assert f"{rlo:.3g}-{rhi:.3g} in amplitude ratio" in line
    assert f"{100 * rlo:.1f}-{100 * rhi:.1f} %" in line
    dlo, dhi = fam["range"]["max_rel_diff"]
    assert f"{dlo:.3g}-{dhi:.3g} in max |dpsi|/A_ref over the 9 masks" in line
    tot = f"is {met['V']['max_abs_dphi_rad']:.3g} rad, "
    assert ("The total over V, which includes end-face signal carried by the aperture, " + tot) in line
    assert line.index(f"{lo:.3g}-{hi:.3g} rad") < line.index("The total over V")
    assert "not a bound" in line and "depends on how that layer is assigned" in line
    assert f"({res['raw_frac_first_res']:.2f} of the raw vacuum-side |D|^2" in line
    assert f"peaks at x_rel {res['loc_vac']['peak_x_rel_A']:+.2f} A" in line
    assert "robust" not in line
    with pytest.raises(ValueError, match="mask-family"):
        bt.reading_line(5.0, res["regions"]["geom"], met["V"], mv["V"], 0.1, met["P"], mv["P"],
                        family=None)


def test_deep_and_cap10_readings_carry_the_band_edge_and_the_attribution_history(bt):
    for cap, x_V in ((10.0, 0.317), (20.0, -8.4), (30.0, -17.2)):
        geom = dict(_geom_for_reading(bt, cap, x_V), surfacing_distance_void_top_two_beam_A=999.9)
        m = dict(max_rel_diff=8e-3, max_abs_dphi_rad=6e-3, max_abs_ratio_minus_1=8e-3)
        fam = _family(dict(max_abs_dphi_rad=(1.3e-4, 5.4e-3), max_abs_ratio_minus_1=(1.3e-4, 3.3e-3),
                           max_rel_diff=(1.7e-4, 5.0e-3)))
        line = bt.reading_line(cap, geom, m, m, 8.5e-3, dict(max_rel_diff=2.3e-4),
                               dict(max_rel_diff=2.0e-4), family=fam)
        be = geom["causal_paths"]["paths"]["band_edge"]
        assert "band edge" in line
        assert f"surfaces {be['surfacing_distance_void_top_A']:.1f} A downstream" in line
        assert f"x_rel <= {be['reach_x_rel_at_theta_out_A']:.2f} A" in line
        assert f"{be['reach_x_rel_at_aperture_max_A']:.2f} A at the aperture's steepest" in line
        assert "outside every in-band causal path" not in line
        if cap == 10.0:
            assert "NOT DEMONSTRATED" in line and "not a bound of the engine" in line
            assert "0.00017-0.005" in line and "mostly end-face signal in amplitude" in line
        else:
            assert ("BY ANALOGY, UNVALIDATED in this cell; CONFIRMED in a TEST_ONLY small cell on a "
                    "criterion set after a first stage whose pre-stated criterion gave NOT "
                    "CONFIRMED (aperture leakage)") in line
            assert bt.band_edge_vs_P(geom) in line
    assert "BY ANALOGY, UNVALIDATED in this cell" in bt.M1_ATTRIBUTION
    assert "CONFIRMED there" not in bt.M1_ATTRIBUTION


# ---- compact figure: one shared scale (A10a-m4) -------------------------------------------------
def _compact_results(bt):
    out = []
    for cap, x_V, peak in ((5.0, 4.68, 0.0848), (10.0, 0.317, 1.7e-3), (20.0, -8.4, 2.03e-4),
                           (30.0, -17.2, 1.59e-4)):
        g = _g(bt, cap)
        reg = bt.regions(g, g["core_z0_A"])
        reg["geom"]["x_V_two_beam_A"] = x_V
        diff = np.full(reg["P"].shape, peak * 1e-3)
        diff[(g["x_rel"] > 3) & (g["x_rel"] < 4)] = peak
        fam = _family(dict(max_abs_dphi_rad=(0.0274, 0.0789), max_abs_ratio_minus_1=(0.026, 0.103),
                           max_rel_diff=(0.0304, 0.105)))
        out.append(dict(cap=cap, g=g, regions=reg, metrics_vac=dict(diff=diff), family=fam))
    return out


def test_compact_panel_info_one_shared_scale_and_plain_titles(bt):
    info = bt.compact_panel_info(_compact_results(bt))
    assert info["vmax"] >= np.log10(0.0848) and info["vmin"] == info["vmax"] - 4.0
    assert info["peak"][5.0] == pytest.approx(0.0848)
    assert info["N"][20.0] == pytest.approx(0.0848 / 2.03e-4)
    t = info["titles"]
    assert t[5.0].startswith("cap 5 A: 0.03-0.08 rad in phase, 3-10 % in amplitude")
    assert "first 2.5 A above the surface" in t[5.0]
    assert t[10.0] == "cap 10 A: not demonstrated in this cell"
    assert "numerical artefact by analogy" in t[20.0] and "about 1/420 of the cap-5 level" in t[20.0]
    assert "about 1/530 of the cap-5 level" in t[30.0]
    with pytest.raises(ValueError, match="cap-5"):
        bt.compact_panel_info(_compact_results(bt)[1:])


def test_compact_bottom_panels_share_the_colour_scale(bt):
    import matplotlib.pyplot as plt
    res = _compact_results(bt)
    info = bt.compact_panel_info(res)
    fig, axs = plt.subplots(1, 4)
    try:
        clims = [bt._compact_bottom(ax, r, info).get_clim() for ax, r in zip(axs, res)]
    finally:
        plt.close(fig)
    assert all(c == (info["vmin"], info["vmax"]) for c in clims)
