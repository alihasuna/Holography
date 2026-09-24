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
  * no phase factor on B: every bin fails; the verdict is "not converged" (X2: converged_beyond_A
    is then the end of the last included bin and `converged` is False; E1's code returned None);
  * X2 (audit A6 N-2): bins beyond the lit-end limit and bins below the amplitude floor are
    excluded from the verdict with their reason; a failing bin that is excluded does not decide it;
  * X2 (A6 N-1/N-3): the sheet beam (H, edge, gap) is required; study_depth100.yaml's beams light
    the surface to the exit plane (H = L_z tan(theta) - gap - a/2 - 1 A, H2 2.6) and a short beam
    is refused by check_lit_to_exit.
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
          exit_excl_A=750.0, tol_phase_rad=1e-2, tol_amp=1e-2, amp_floor_rel=0.05)
EDGE = 2.0


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


def _pair(zc_A, zc_B, z_top=L):
    """Synthetic pair: bottom-edge contacts zc_A, zc_B; the beams' top edges meet each surface at
    z_top (default: the exit plane, i.e. the strip is lit to the exit plane)."""
    def cell(xs):
        return SimpleNamespace(length_z_A=L,
                               metadata=dict(layout=dict(highest_surface_x_A=xs,
                                                         top_absorber_x_A=[X_TOP, X_TOP + 10])))

    def beam(xs, zc):
        return SimpleNamespace(x_bottom_A=xs + zc * np.tan(TH), height_A=(z_top - zc) * np.tan(TH),
                               edge_A=EDGE)
    return dict(params=SimpleNamespace(theta_out_ext_rad=TH), A=(cell(XS_A), None),
                B=(cell(XS_B), None), beams=dict(A=beam(XS_A, zc_A), B=beam(XS_B, zc_B)))


def _lit_limit(z_top=L):
    """lit_strip's rule, written out: end of the lit core minus radius lambda L_z / tan(theta)."""
    return z_top - EDGE / np.tan(TH) - KW["radius_per_A"] * LAM * L / np.tan(TH)


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
    # X2: the bins ending beyond the lit-end limit are reported but excluded from the verdict
    lim = _lit_limit()
    assert r["lit_strip"]["lit_limit_A"] == pytest.approx(lim, abs=1e-6)
    for q in r["rows"]:
        assert q["included"] == (q["z_end_A"] <= lim + 1e-9)
        assert q["status"] == ("pass" if q["included"] else "excluded")
    assert r["converged"] and r["n_bins_beyond"] == r["n_included"] == sum(
        q["z_end_A"] <= lim + 1e-9 for q in r["rows"]) >= 10


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


def test_unconverged_last_bin_gives_not_converged():
    """E1 asserted `converged_beyond_A is None` here; X2 (A6 N-2, orchestrator: the definition must
    not return None because of a single last bin) returns the first distance beyond which every
    included bin passes, i.e. the end of the last included bin when that one fails, with
    converged = False and no bin beyond."""
    eA = _ew(_flat, XS_A)
    eB = _ew(_flat, XS_B)                            # phase factor missing: every bin fails
    r = ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA, **KW)
    assert r["n_bins"] > 5
    inc = [q for q in r["rows"] if q["included"]]
    assert len(inc) > 5 and all(q["status"] == "fail" for q in inc)
    assert r["converged"] is False and r["n_bins_beyond"] == 0
    assert r["converged_beyond_A"] == inc[-1]["d_end_A"]
    assert r["verdict"].startswith("NOT converged")
    assert all(abs(q["err_rad"] + DELTA) < 1e-9 for q in r["rows"])   # err = 0 - Delta


def test_excluded_last_bins_do_not_decide_the_verdict():
    """A6 N-2 in synthetic form: B deviates only where the strip ends (a fringe-like excess in the
    last 1500 A before the top-edge contact); those bins lie beyond the lit-end limit, are reported
    with their reason and do not make the verdict "not converged". With the strip lit only up to
    z_top = 9000 A the limit moves and the same rule excludes the bins beyond it."""
    edge_bump = lambda z: 0.05 * np.exp(-((z - 11000.0) / 400.0) ** 2)  # noqa: E731
    eA = _ew(_flat, XS_A)
    eB = _ew(lambda z: np.exp(1j * DELTA) * _flat(z) * (1 + edge_bump(z)), XS_B)
    r = ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA, **KW)
    bad = [q for q in r["rows"] if not q["passes"]]
    assert bad and all(not q["included"] and "lit-end limit" in q["excluded_because"][0]
                       for q in bad)
    assert r["converged"] and r["converged_beyond_A"] == 0.0
    assert r["last_bin"]["status"] == "excluded"
    r9 = ntc.resolved_translation(eA, eA, _pair(3000.0, 3000.0, z_top=9000.0), expected_rad=0.0,
                                  **KW)
    assert r9["lit_strip"]["lit_limit_A"] == pytest.approx(_lit_limit(9000.0), abs=1e-6)
    assert all(q["included"] == (q["z_end_A"] <= _lit_limit(9000.0) + 1e-9) for q in r9["rows"])


def test_amplitude_floor_excludes_the_noise_floor_and_is_required():
    """Bins whose amplitude falls below amp_floor_rel x the largest bin amplitude are excluded
    (reason given): here the translated field dies smoothly at z_s = 8000 A and a residual field of
    1e-3 of the plateau WITHOUT the translation phase remains (a noise floor); those bins fail but
    do not decide the verdict. Without the floor (0) they do. amp_floor_rel is required."""
    w = lambda z: 0.5 * (1 - np.tanh((z - 8000.0) / 150.0))  # noqa: E731
    eA = _ew(lambda z: _flat(z) * (w(z) + 1e-3 * (1 - w(z))), XS_A)
    eB = _ew(lambda z: _flat(z) * (np.exp(1j * DELTA) * w(z) + 1e-3 * (1 - w(z))), XS_B)
    r = ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA, **KW)
    low = [q for q in r["rows"] if q["z_start_A"] >= 8500.0 and q["z_end_A"] <= _lit_limit()]
    assert len(low) >= 2
    for q in low:
        assert not q["passes"] and not q["included"]
        assert any("amplitude floor" in why for why in q["excluded_because"])
    assert r["converged"] and r["converged_beyond_A"] == 0.0
    r0 = ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA,
                                  **dict(KW, amp_floor_rel=0.0))
    assert not r0["converged"] and r0["converged_beyond_A"] == low[-1]["d_end_A"]
    kw = dict(KW)
    del kw["amp_floor_rel"]
    with pytest.raises(TypeError, match="amp_floor_rel"):
        ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA, **kw)
    with pytest.raises(ValueError, match="amp_floor_rel"):
        ntc.resolved_translation(eA, eB, _pair(3000.0, 3000.0), expected_rad=DELTA,
                                 **dict(KW, amp_floor_rel=1.5))


def test_case_functions_require_clean_depth_and_azimuth():
    th = 16.1347e-3
    beam = ntc.LEGACY_M2_BEAM                  # X2: the sheet beam is required too (below)
    with pytest.raises(TypeError, match="clean_depth_A"):
        ntc.translation_pair(theta=th, azimuth="110", **beam)
    with pytest.raises(TypeError, match="azimuth"):
        ntc.step_case(theta=th, width_periods=2, clean_depth_A=100.0, **beam)
    with pytest.raises(ValueError, match="azimuth"):
        ntc.translation_pair(theta=th, azimuth="111", clean_depth_A=100.0, **beam)
    with pytest.raises(ValueError, match="clean_depth_A"):
        ntc.translation_pair(theta=th, azimuth="110", clean_depth_A=None, **beam)
    with pytest.raises(ValueError, match="surface_resolved"):
        ntc.run_translation(dict(), surface_resolved=dict(radius_per_A=0.1))


def test_case_functions_require_the_sheet_beam():
    """A6 N-1/N-3 (X2): H, edge and gap have no default in translation_pair and step_case."""
    th = 16.1347e-3
    cell = dict(clean_depth_A=100.0, azimuth="110")
    for missing in ("H", "edge", "gap"):
        beam = {k: v for k, v in ntc.LEGACY_M2_BEAM.items() if k != missing}
        with pytest.raises(TypeError, match=f"'{missing}'"):
            ntc.translation_pair(theta=th, **cell, **beam)
        with pytest.raises(TypeError, match=f"'{missing}'"):
            ntc.step_case(theta=th, width_periods=2, **cell, **beam)
        with pytest.raises(ValueError, match="required"):
            ntc.translation_pair(theta=th, **cell, **beam, **{missing: None})
    with pytest.raises(ValueError, match="finite and > 0"):
        ntc.translation_pair(theta=th, **cell, **dict(ntc.LEGACY_M2_BEAM, H=-8.0))
    assert ntc.LEGACY_M2_BEAM == dict(H=8.0, edge=2.0, gap=2.0)


def test_lit_to_exit_height_and_refusal_of_a_short_beam():
    """H2 2.6: H = L_z tan(theta) - gap - a/2 - 1 A puts the top edge 1 A (in height) above the
    LOWER surface at the exit plane; check_lit_to_exit refuses the legacy 8 A beam for the
    read-out window and accepts the lit-to-exit beam (geometry only, nothing is run)."""
    th = ntc.theta_0008()
    Lz = ntc.cell_length_z_A(theta=th, azimuth="110", gap=2.0, extra_A=5000.0)
    H = ntc.sheet_height_lit_to_exit_A(L_z_A=Lz, theta=th, gap=2.0)
    assert H == pytest.approx(Lz * np.tan(th) - 2.0 - 2 * ntc.Q - 1.0, abs=1e-3)
    assert H <= Lz * np.tan(th) - 2.0 - 2 * ntc.Q - 1.0
    beams = {}
    for name, b in (("short", ntc.LEGACY_M2_BEAM), ("lit", dict(H=H, edge=2.0, gap=2.0))):
        pair = ntc.translation_pair(theta=th, clean_depth_A=21.0, azimuth="110", extra_A=5000.0,
                                    tile_above_periods=0, **b)
        assert pair["A"][0].length_z_A == pytest.approx(Lz, abs=1e-9)
        beams[name] = pair
    with pytest.raises(ValueError, match="does not light the surface"):
        ntc.check_lit_to_exit(beams["short"], exit_excl_A=1115.5)
    ntc.check_lit_to_exit(beams["lit"], exit_excl_A=1115.5)
    p = beams["lit"]
    zt = (p["beams"]["A"].x_bottom_A + H - p["A"][0].metadata["layout"]["highest_surface_x_A"]) \
        / np.tan(th)
    assert Lz - 1.0 / np.tan(th) - 1.0 < zt <= Lz - 1.0 / np.tan(th) + 1e-6   # A (lower) surface
    assert p["check"]["identical_sets"] and p["check"]["max_distance_A"] < 1e-9


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
    # X2 (A6 N-1/N-3): the sheet beam is explicit in every point of both files; study.yaml keeps
    # the legacy M2 beam; study_depth100.yaml lights every cell to the exit plane (H2 2.6 formula,
    # recomputed here from the cell length and the angle)
    beam = ("beam_height_A", "beam_edge_A", "beam_gap_A")
    assert all(all(k in p for k in beam) for p in old["points"] + pts)
    assert all((p["beam_height_A"], p["beam_edge_A"], p["beam_gap_A"]) == (8.0, 2.0, 2.0)
               for p in old["points"])
    for p in pts:
        th = ntc.theta_0008() if p["theta"] == "bragg_0008_mip" else float(p["theta"]) * 1e-3
        Lz = ntc.cell_length_z_A(theta=th, azimuth=p["azimuth"], gap=p["beam_gap_A"],
                                 extra_A=float(p["extra_length_A"]))
        assert p["beam_height_A"] == ntc.sheet_height_lit_to_exit_A(L_z_A=Lz, theta=th,
                                                                    gap=p["beam_gap_A"]), p["name"]
        assert (p["beam_edge_A"], p["beam_gap_A"]) == (2.0, 2.0)
    sr = new["surface_resolved"]
    assert sr["exit_excl_A"] == 1115.5 and sr["amp_floor_rel"] == 0.05
    assert (sr["tol_phase_rad"], sr["tol_amp"]) == (0.01, 0.01)
