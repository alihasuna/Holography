"""Surface-position-resolved null-test read-out (H2 section 2.4, finding N12; E1 wave 2a):
null_test_cases.resolved_translation uses H2's specular_column (tools/hpc/supercell_sizing.py) and
pairs the two crystals by surface point z_s = L_z - (x - x_s)/tan(theta).

Synthetic exit waves with a KNOWN envelope as a function of the surface point, translated by an
integer number of pixels (so that the construction is exactly covariant on the grid). Convention of
the code (as run_translation): expected = -(k_out - k_in).R and E_B = E_A exp(+i expected):
  * identical envelopes times exp(+i Delta): every bin has err = 0 and amp = 1 (1e-9);
  * ray mapping: a phase ramp kappa z_s (kappa = 2 pi/1e4 A) gives each full bin the phase at its
    centre within 5e-3 rad (= 8 A of z_s: half a pixel of z_s is 3.1 A, 2e-3 rad, and the
    read-out's own band-pass ringing from the vacuum-window edge was measured here at <= 7e-4 rad
    per bin, 3.7e-3 rad per pixel); a misplaced reference plane or a sign error is 0.05-0.3 rad; and
    an amplitude bump centred at z_s = 7250 A peaks in the bin [7000, 7500);
  * a smooth Gaussian excess on B only: the bins and the convergence distance follow from the bin
    means of the known excess (tolerances 1e-2 as in the null-test criteria);
  * no phase factor on B: every bin fails and converged_beyond_A is None.
Also: the function used is H2's (identity), and the study-file checks refuse missing keys.
"""
from types import SimpleNamespace

import numpy as np
import pytest

import null_test_cases as ntc
from reflection_holo.forward.contracts import ExitWave
from reflection_holo.forward.multislice import beam_constants

TH = 16.1347e-3
LAM = beam_constants(200.0)["wavelength_A"]
RX = 2.71545                      # a/2
NSHIFT = 27
DX = RX / NSHIFT                  # R_x is exactly 27 pixels
NX = 6000
L = 12000.0
XS_A = 60.0
XS_B = XS_A + RX
X_TOP = NX * DX - 10.0
DELTA = 1.2345                    # expected phase (rad), arbitrary
KW = dict(radius_per_A=0.1, x_cut_A=2.0, taper_A=3.0, min_height_A=5.0, bin_A=500.0,
          exit_excl_A=750.0, tol_phase_rad=1e-2, tol_amp=1e-2)


def _ew(env_of_zs, xs):
    x = np.arange(NX) * DX
    zs = L - (x - xs) / np.tan(TH)
    fc = np.sin(TH) / LAM
    psi = env_of_zs(zs) * np.exp(2j * np.pi * fc * x)
    psi[x < xs] = 0.3                                    # "crystal": masked by the read-out
    return ExitWave(psi=psi[:, None].astype(np.complex128), dx_A=DX, dy_A=1.0, x0_A=0.0, y0_A=0.0,
                    plane="exit plane z = L_z (no further propagation)", z_A=L, energy_keV=200.0,
                    theta_in_ext_rad=TH, realisation=0, seed=None,
                    metadata=dict(beam=dict(wavelength_A=LAM)))


def _pair(zc_A, zc_B):
    def cell(xs):
        return SimpleNamespace(metadata=dict(layout=dict(highest_surface_x_A=xs,
                                                         top_absorber_x_A=[X_TOP, X_TOP + 10])))
    return dict(params=SimpleNamespace(theta_out_ext_rad=TH), A=(cell(XS_A), None),
                B=(cell(XS_B), None),
                beams=dict(A=SimpleNamespace(x_bottom_A=XS_A + zc_A * np.tan(TH)),
                           B=SimpleNamespace(x_bottom_A=XS_B + zc_B * np.tan(TH))))


def _flat(zs):
    # lit smoothly well before the analysed region (turn-on centred 2500 A before z = 3000 A)
    return 0.3 * np.exp(0.7j) * 0.5 * (1 + np.tanh((zs - 500.0) / 300.0))


def test_uses_h2_specular_column():
    import sys
    ntc._h2_specular_column()
    mod = sys.modules["supercell_sizing_h2"]
    assert ntc._h2_specular_column() is mod.specular_column
    assert mod.__file__.endswith("tools/hpc/supercell_sizing.py")


def test_covariant_fields_give_zero_error_in_every_bin():
    eA = _ew(_flat, XS_A)
    eB = _ew(lambda z: np.exp(1j * DELTA) * _flat(z), XS_B)
    r = ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA, **KW)
    assert r["n_bins"] == int(np.ceil((L - 750.0 - 3000.0) / 500.0))
    for q in r["rows"]:
        assert abs(q["err_rad"]) < 1e-9 and abs(q["amp_ratio"] - 1) < 1e-9
        assert q["n_px_A"] == q["n_px_B"] > 0
    assert r["converged_beyond_A"] == 0.0


def test_ray_mapping_of_the_surface_coordinate():
    kappa = 2 * np.pi / 10000.0                       # phase ramp along the surface
    env = lambda z: _flat(z) * np.exp(1j * kappa * z)  # noqa: E731
    eA = _ew(env, XS_A)
    eB = _ew(lambda z: np.exp(1j * DELTA) * env(z), XS_B)
    r = ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA, **KW)
    full = [q for q in r["rows"] if abs(q["z_end_A"] - q["z_start_A"] - 500.0) < 1e-6]
    assert len(full) >= 15
    for q in full:
        mid = 0.5 * (q["z_start_A"] + q["z_end_A"])
        assert abs(np.angle(np.exp(1j * (q["E_A_arg"] - 0.7 - kappa * mid)))) < 5e-3
    bump = lambda z: _flat(z) * (1 + 0.5 * np.exp(-((z - 7250.0) / 400.0) ** 2))  # noqa: E731
    r = ntc.resolved_translation(_ew(bump, XS_A), _ew(bump, XS_B), _pair(3000.0, 3000.0),
                                 expected_rad=0.0, **KW)
    peak = max(r["rows"], key=lambda q: q["E_A_abs"])
    assert (peak["z_start_A"], peak["z_end_A"]) == (7000.0, 7500.0)


def test_local_excess_sets_the_convergence_distance():
    z0 = 3000.0
    excess = lambda z: 0.1 * np.exp(-((z - z0) / 1000.0) ** 2)  # noqa: E731
    eA = _ew(_flat, XS_A)
    eB = _ew(lambda z: np.exp(1j * DELTA) * _flat(z) * (1 + excess(z)), XS_B)
    r = ntc.resolved_translation(eA, eB, _pair(z0, z0 - 168.0), expected_rad=DELTA, **KW)
    # expected bin deviations from the known excess (bin means; E_A is flat there)
    for q in r["rows"]:
        zz = np.linspace(q["z_start_A"], q["z_end_A"], 2001)
        want = float(np.mean(excess(zz)))
        assert abs((q["amp_ratio"] - 1) - want) < 2e-3
    fails = [q["d_end_A"] for q in r["rows"] if abs(q["amp_ratio"] - 1) > 1e-2]
    assert fails == pytest.approx([500.0, 1000.0, 1500.0])
    assert r["converged_beyond_A"] == pytest.approx(1500.0)
    assert r["z_contact_A"]["A"] == pytest.approx(z0) and r["z_contact_A"]["B"] == pytest.approx(
        z0 - 168.0)


def test_unconverged_last_bin_gives_none():
    eA = _ew(_flat, XS_A)
    eB = _ew(_flat, XS_B)                            # phase factor missing: every bin fails
    r = ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA, **KW)
    assert r["n_bins"] > 5 and r["converged_beyond_A"] is None
    assert all(abs(q["err_rad"] + DELTA) < 1e-9 for q in r["rows"])   # err = 0 - Delta


def test_case_functions_require_clean_depth_and_azimuth():
    th = 16.1347e-3
    with pytest.raises(TypeError, match="clean_depth_A"):
        ntc.translation_pair(theta=th, azimuth="110")
    with pytest.raises(TypeError, match="azimuth"):
        ntc.step_case(theta=th, width_periods=2, clean_depth_A=100.0)
    with pytest.raises(ValueError, match="azimuth"):
        ntc.translation_pair(theta=th, azimuth="111", clean_depth_A=100.0)
    with pytest.raises(ValueError, match="clean_depth_A"):
        ntc.translation_pair(theta=th, azimuth="110", clean_depth_A=None)
    with pytest.raises(ValueError, match="surface_resolved"):
        ntc.run_translation(dict(), surface_resolved=dict(radius_per_A=0.1))


def test_study_files_carry_the_required_keys():
    from pathlib import Path

    from reflection_holo.io.config import load_yaml_unique
    here = Path(__file__).resolve().parents[2] / "scripts" / "hpc" / "null_test_study"
    old = load_yaml_unique((here / "study.yaml").read_bytes())
    assert old["build"]["tile_above_periods"] == ntc.TILE_ABOVE_PERIODS_M2
    assert len(old["points"]) == 17
    assert all(p["clean_depth_A"] == ntc.LEGACY_M2_CLEAN_DEPTH_A and p["azimuth"] == "110"
               for p in old["points"])
    assert "surface_resolved" not in old
    new = load_yaml_unique((here / "study_depth100.yaml").read_bytes())
    assert set(new["surface_resolved"]) == set(ntc.RESOLVED_KEYS)
    pts = new["points"]
    assert all(p["clean_depth_A"] >= 100.0 for p in pts)
    assert all(p["absorption_ratio"] >= 0.05 and p["absorption_label"].startswith("TEST_ONLY")
               for p in pts)
    kinds = {(p["kind"], p["azimuth"]) for p in pts}
    assert {("translation_fixed_beam", "110"), ("translation_fixed_beam", "100"),
            ("translation_moved_beam", "110"), ("translation_moved_beam", "100"),
            ("step_parallel", "110")} <= kinds
    assert any(p["kind"] == "translation_fixed_beam" and p["azimuth"] == "100"
               and p["theta"] == "bragg_0008_mip" for p in pts)
