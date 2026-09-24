"""tools/plots/buried_torus.py (T3's buried-void analysis, revised by agent T4 after audit A9a M-2,
m-2, m-5, m-6): the region definitions, the identical-cell assertion, the x-location, the apodised
vacuum-origin split applied BEFORE the specular aperture, the steepest in-band systematic beam, the
supervisor-facing wording (no detection rule, no fitted lengths, the geometric zero stated as a
consequence of the surface-height model). The script is imported with importlib, as the tests of
scripts/torus and tools/reflection_step_phase_calculator.py do. Nothing is written to disk.

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


def test_reading_lines(bt):
    geom = dict(x_V_two_beam_A=0.317, surfacing_distance_void_top_two_beam_A=541.3)
    m = dict(max_rel_diff=8e-3, max_abs_dphi_rad=6e-3, max_abs_ratio_minus_1=8e-3)
    line = bt.reading_line(10.0, geom, m, dict(max_rel_diff=1.7e-3), 8.5e-3, m, m)
    assert "NOT DEMONSTRATED" in line and "0.317 A" in line
    geom = dict(x_V_two_beam_A=-17.0, surfacing_distance_void_top_two_beam_A=1623.9)
    line = bt.reading_line(30.0, geom, m, m, 0.0, dict(max_rel_diff=1.6e-4),
                           dict(max_rel_diff=1.59e-4))
    assert "no two-beam path" in line and "NOT DEMONSTRATED" in line and "0.00016" in line
    geom = dict(x_V_two_beam_A=4.68, surfacing_distance_void_top_two_beam_A=270.7)
    line = bt.reading_line(5.0, geom, m, dict(max_rel_diff=0.085, max_abs_dphi_rad=0.034,
                                              max_abs_ratio_minus_1=0.086), 0.1, m, m)
    assert "no dose model" in line and "NOT RUN" in line
    for w in ("detected", "marginal", "floor"):
        assert w not in line


def test_geometric_zero_statement(bt):
    s = bt.geometric_zero_statement("buried_cap5A_r010", 0.0, -0.0)
    assert "zero by construction of the surface-height model" in s
    assert "not a geometric-engine run" in s
