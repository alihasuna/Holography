"""Geometric engine with the continuum oxide (report E4, test (b)).

A priori tolerances are the printed precision of the E9 lines they compare with
(tools/review/e9_recompute_output.txt, "out:N"), plus, where the engine uses f computed from the
density rather than E9's f rounded to 4 decimals, the bound 2 k_perp x 5e-5 of that rounding.
Values standing in for PROJECT_INPUT items are TEST_ONLY.
"""
import math

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.geometric import (GeometricParams, OutsideB4ScopeError,
                                               geometric_exit_wave, oxide_phase_rates,
                                               terrace_model_from_structure)
from reflection_holo.forward.multislice.physics import interaction_constant_rad_per_VA
from reflection_holo.geometry.wavelength import k_ang_per_A
from reflection_holo.structure import OverlayerSpec, Staircase, build_si001_terraces
from reflection_holo.structure import oxide as ox

L12 = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (continuum oxide)"
THETA = 16.1347e-3                     # (0,0,8) at the IAM MIP (B32; out:10), TEST_ONLY here
THETA_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7"
Q = A_SI_A / 4
KP = k_ang_per_A(200.0) * math.sin(THETA)
F_ROUNDING_RAD_PER_A = 2 * KP * 5e-5   # E9 uses f rounded to 4 decimals (e9_recompute.py)
PARAMS = GeometricParams(exit_plane_pixel_A=(0.25, 0.5), n_y=4, x_margin_A=20.0,
                         periods_along_beam=1, reflectivity_amplitude=1.0,
                         invisibility_tol_cycles=0.01)


def _near_rounding_boundary(d):
    """TEST helper (audit A8 m4): the acknowledgement is stated exactly when some terrace's count
    lies within ox.MIN_ROUNDING_MARGIN_LAYERS of its rounding boundary (the gate itself is tested in
    tests/structure/test_oxide_structure_a8_fixes.py)."""
    tt = d["terrace_thickness_A"] or (d["thickness_A"],)
    tn = d["terrace_consumed_layers"] or (d["consumed_layers"],)
    return any(ox.rounding_margin(thickness_A=t, density_g_cm3=d["density_g_cm3"],
                                  amorphous_si_thickness_A=d["amorphous_si_thickness_A"],
                                  consumed_layers=n, a_A=A_SI_A)["near_boundary"]
               for t, n in zip(tt, tn))


def spec(**kw):
    base = dict(material="amorphous SiO2", thickness_A=20.0, density_g_cm3=2.20, consumed_layers=7,
                V_real_V=10.34, V_imag_V=0.40, vacuum_edge_width_A=0.5, interface_width_A=0.5,
                amorphous_si_thickness_A=0.0, amorphous_si_V_real_V=None,
                amorphous_si_V_imag_V=None, terrace_thickness_A=None, terrace_consumed_layers=None,
                sharp_edge_test_flag=False, sharp_interface_test_flag=False,
                nonconformal_sublayer_acknowledged=False,     # audit A9b M1 (stated)
                labels={k: L12 for k in ox.LABEL_KEYS})
    if kw.get("terrace_thickness_A") is not None or kw.get("terrace_consumed_layers") is not None:
        base["labels"] = dict(base["labels"], overrides=L12)
    base.update(kw)
    base.setdefault("rounding_boundary_acknowledged", _near_rounding_boundary(base))
    return ox.ContinuumOxideSpec(**base)


def run(overlayer, layers, boundary, *, az=(1, 0, 0), widths=(100, 100)):
    st = Staircase(edges="transverse", terrace_layers=layers, terrace_widths=widths,
                   boundary_step_layers=boundary)
    s = build_si001_terraces(azimuth_uvw=az, azimuth_label="TEST_ONLY: item 8", staircase=st,
                             edge_periods=1, substrate_layers=14,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=overlayer, vacuum_above_A=22.0, lattice_parameter_A=A_SI_A,
                             lattice_parameter_label="ASSUMPTION B2")
    m = terrace_model_from_structure(s)
    return geometric_exit_wave(m, energy_keV=200.0, theta_in_ext_rad=THETA,
                               theta_label=THETA_LABEL, params=PARAMS, illumination="plane_wave",
                               beam="specular")


def _phases(r):
    md = r.exit_wave.metadata
    return np.asarray(md.get("terrace_phase_with_overlayer_rad", md["terrace_phase_rad"]))


@pytest.mark.parametrize("layers,boundary,phase_e9", [((0, 1), -1, 10.9761), ((0, 2), -2, 21.9522)],
                         ids=["a/4", "a/2"])
def test_conformal_step_phase_unchanged(layers, boundary, phase_e9):
    """E9 section 3 item 1 / out:91: 10.9761 (a/4), 21.9522 (a/2) rad with or without the layer."""
    bare, oxd = run(None, layers, boundary), run(spec(), layers, boundary)
    d_bare = _phases(bare)[1] - _phases(bare)[0]
    d_ox = _phases(oxd)[1] - _phases(oxd)[0]
    assert abs(d_ox) == pytest.approx(phase_e9, abs=5e-5)
    assert d_ox == pytest.approx(d_bare, abs=1e-9)
    # the exit wave itself: phase difference between lit pixels of the two terraces, carrier removed
    ew = oxd.exit_wave
    tr = oxd.trace
    X = ew.x0_A + np.arange(ew.psi.shape[0])[:, None] * ew.dx_A + 0 * tr["source_terrace"]
    kx = ew.metadata["k_out_rad_per_A"][0]
    lit = tr["status"] == 0
    ph = np.angle(ew.psi * np.exp(-1j * kx * X))
    p0 = ph[lit & (tr["source_terrace"] == 0)]
    p1 = ph[lit & (tr["source_terrace"] == 1)]
    assert np.ptp(np.unwrap(p0)) < 1e-9 and np.ptp(np.unwrap(p1)) < 1e-9
    expect = (d_bare + np.pi) % (2 * np.pi) - np.pi
    assert (p1[0] - p0[0] - expect + np.pi) % (2 * np.pi) - np.pi == pytest.approx(0, abs=1e-9)
    # the conformal layer multiplies every terrace's amplitude by the same zero-loss factor
    amp = np.abs(ew.psi[lit])
    assert np.ptp(amp) < 1e-12 and amp[0] < 1.0
    assert oxd.layout.x_offset_A == pytest.approx(11.1699, abs=5e-5)          # out:143


@pytest.mark.parametrize("f,V,line,rate", [
    (0.4214, 10.1, 109, 4.27280), (0.4214, 10.34, 110, 4.29236), (0.4214, 11.5, 111, 4.38633),
    (0.4415, 10.1, 112, 4.43529), (0.4415, 10.34, 113, 4.45486), (0.4415, 11.5, 114, 4.54882),
    (0.4616, 10.1, 115, 4.59778), (0.4616, 10.34, 116, 4.61735), (0.4616, 11.5, 117, 4.71131)])
def test_grown_oxide_rate_equals_e9(f, V, line, rate):
    r = oxide_phase_rates(theta_ext_rad=THETA, energy_keV=200.0, V_real_V=V, V_imag_V=0.0, f=f,
                          layer_spacing_A=Q)
    assert r["grown_oxide_rad_per_A"] == pytest.approx(rate, abs=5e-6), line


@pytest.mark.parametrize("V,line,top", [(10.1, 96, 0.8661), (10.34, 98, 0.8857),
                                        (11.5, 102, 0.9797)])
def test_top_surface_rate_equals_e9(V, line, top):
    r = oxide_phase_rates(theta_ext_rad=THETA, energy_keV=200.0, V_real_V=V, V_imag_V=0.0,
                          f=0.4415, layer_spacing_A=Q)
    assert r["top_surface_rad_per_A"] == pytest.approx(top, abs=5e-5), line


def test_one_consumed_layer_equals_e9():
    r = oxide_phase_rates(theta_ext_rad=THETA, energy_keV=200.0, V_real_V=10.34, V_imag_V=0.0,
                          f=0.4415, layer_spacing_A=Q)
    assert r["one_consumed_layer_oxide_A"] == pytest.approx(3.0753, abs=5e-5)          # out:123
    assert r["one_consumed_layer_rad"] == pytest.approx(13.6998, abs=5e-5)


def test_engine_grown_oxide_differential():
    """A 0.5 A thicker grown oxide on the upper terrace of an a/2 step: the engine's step phase
    changes by rate x Dt exactly (rate with the density's f) and by E9's 4.45486 rad/A (out:113)
    within its printed precision plus the f-rounding bound."""
    Dt = 0.5
    bare = run(spec(V_imag_V=0.0, labels={k: L12 for k in ox.LABEL_KEYS}), (0, 2), -2)
    grown = run(spec(V_imag_V=0.0, terrace_thickness_A=(20.0, 20.0 + Dt),
                     terrace_consumed_layers=(7, 7)), (0, 2), -2)
    dphi = (_phases(grown)[1] - _phases(grown)[0]) - (_phases(bare)[1] - _phases(bare)[0])
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    r = oxide_phase_rates(theta_ext_rad=THETA, energy_keV=200.0, V_real_V=10.34, V_imag_V=0.0,
                          f=f, layer_spacing_A=Q)
    assert dphi == pytest.approx(r["grown_oxide_rad_per_A"] * Dt, abs=1e-9)
    assert dphi / Dt == pytest.approx(4.45486, abs=5e-6 + F_ROUNDING_RAD_PER_A)
    assert grown.exit_wave.metadata["overlayer"]["conformal"] is False


def test_engine_one_extra_consumed_layer():
    """One extra consumed layer on the upper terrace of an a/2 step (E9 section 3 item 5): 13.6998
    rad more (out:123), and the buried step becomes a/4."""
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    bare = run(spec(V_imag_V=0.0, labels={k: L12 for k in ox.LABEL_KEYS}), (0, 2), -2)
    extra = run(spec(V_imag_V=0.0, terrace_thickness_A=(20.0, 20.0 + Q / f),
                     terrace_consumed_layers=(7, 8)), (0, 2), -2)
    dphi = (_phases(extra)[1] - _phases(extra)[0]) - (_phases(bare)[1] - _phases(bare)[0])
    bound = 5e-5 + 2 * (4.4849 - KP) * Q / f ** 2 * 5e-5      # printed + f rounding (d/df)
    assert dphi == pytest.approx(13.6998, abs=bound)
    st = extra.exit_wave.metadata["steps"][0]["overlayer"]
    assert st["buried_delta_layers"] == 1 and st["buried_relation"] == "screw"


def test_zero_loss_amplitude_equals_e9_complex_k():
    """2 nm, V_ox 10.34 V, V'_ox = 1/(2 sigma Lambda) with Lambda = 1780 A: intensity 0.2850
    (out:57, complex-k column); a MODEL value (E9 M1)."""
    sigma = interaction_constant_rad_per_VA(200.0)
    Vi = 1.0 / (2 * sigma * 1780.0)
    assert Vi == pytest.approx(0.3854, abs=5e-5)                                    # out:19
    r = run(spec(V_imag_V=Vi), (0, 2), -2)
    amp = r.exit_wave.metadata["overlayer"]["per_terrace"][0]["zero_loss_amplitude"]
    assert amp ** 2 == pytest.approx(0.2850, abs=5e-5)


def test_b4_scope_with_the_oxide_at_110():
    """<110>: a conformal a/4 step is refused (buried a/4, parity note); an a/2 step is accepted;
    an a/4 step with one extra consumed layer on one terrace is a buried a/2 translation and is
    accepted (E9 section 3 item 2)."""
    with pytest.raises(OutsideB4ScopeError, match="parity of the consumed-layer count"):
        run(spec(), (0, 1), -1, az=(1, 1, 0))
    run(spec(), (0, 2), -2, az=(1, 1, 0))
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    r = run(spec(terrace_thickness_A=(20.0 + Q / f, 20.0), terrace_consumed_layers=(8, 7)),
            (0, 1), -1, az=(1, 1, 0))
    st = r.exit_wave.metadata["steps"][0]["overlayer"]
    assert st["buried_delta_layers"] == 2 and st["buried_relation"] == "translation"


def test_legacy_declared_region_still_refused():
    ov = OverlayerSpec(material="amorphous SiO2", thickness_A=8.0, density_g_cm3=2.2, label=L12)
    with pytest.raises(OutsideB4ScopeError, match="overlayer"):
        run(ov, (0, 2), -2)


def test_no_oxide_metadata_without_an_oxide():
    md = run(None, (0, 2), -2).exit_wave.metadata
    assert "overlayer" not in md and "terrace_phase_with_overlayer_rad" not in md
    assert all("overlayer" not in s for s in md["steps"])
