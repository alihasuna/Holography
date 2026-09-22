"""T24, T25 and the sign test through the full chain: package waves -> R1 hologram -> Poisson noise ->
carrier on the EMPTY hologram -> sideband reconstruction (docs/05 section 8 "Holography"; SM12).

Reference values and tolerances are the calculator's own (tools/reflection_step_phase_calculator.py,
section 13): T24 wants sc666.step_phase(d111)['wrapped'] (printed 2.359613) within 5e-3 rad; T25 wants
0 within 5e-3 rad; both at dose 1e4 e/px, seed 12345, n = 512, fringe 8 px.
"""
import inspect

import numpy as np
import pytest

from holo_cases import (CALCULATOR_PATH, T24_TOL_RAD, T25_TOL_RAD, calculator, calculator_T24_reference,
                        roundtrip)


def test_calculator_definitions_unchanged():
    """Guard: the calculator still defines T24/T25 with the reference values and tolerances used here."""
    src = CALCULATOR_PATH.read_text()
    assert ('chk("T24 hologram round trip recovers the (666) single-step phase",\n'
            '        hr[\'recovered\'], sc666.step_phase(d111)[\'wrapped\'], 5e-3, "rad")') in src
    assert ('chk("T25 hologram round trip, no-step control", hr0[\'recovered\'], 0.0,\n'
            '        5e-3, "rad")') in src
    assert "hr = hologram_roundtrip(sc666.step_phase(d111)['wrapped'],\n" \
           "                            dose_per_px=1e4, seed=12345)" in src
    assert "hr0 = hologram_roundtrip(0.0, dose_per_px=1e4, seed=12345)" in src
    sig = inspect.signature(calculator().hologram_roundtrip)
    assert sig.parameters["n"].default == 512 and sig.parameters["fringe_px"].default == 8.0
    assert inspect.signature(calculator()._sideband_wave).parameters["ap_frac"].default == 1.0 / 3.0
    wrapped, mod2pi = calculator_T24_reference()
    assert abs(wrapped - 2.359613) <= 5e-7          # the value printed by the calculator (T24 "want")
    assert abs(mod2pi - 3.9236) <= 5e-5             # T10, printed to 4 decimals


def test_T24_single_step_phase_recovered():
    want, _ = calculator_T24_reference()
    got = roundtrip(want, dose_per_px=1e4, seed=12345)
    assert abs(got["recovered"] - want) <= T24_TOL_RAD, got["recovered"]
    assert got["result"].sideband_sign_check.startswith("phi_o - phi_r")


def test_T25_no_step_control():
    got = roundtrip(0.0, dose_per_px=1e4, seed=12345)
    assert abs(got["recovered"] - 0.0) <= T25_TOL_RAD, got["recovered"]


def test_T24_T25_identical_to_calculator_implementation():
    """Stronger than T24/T25: the package chain reproduces the calculator's own hologram_roundtrip
    output (same waves, same Poisson draws, same carrier bin, same mask) to rounding (1e-9 rad)."""
    want, _ = calculator_T24_reference()
    for dphi in (want, 0.0):
        ref = calculator().hologram_roundtrip(dphi, dose_per_px=1e4, seed=12345)
        got = roundtrip(dphi, dose_per_px=1e4, seed=12345)
        assert abs(got["recovered"] - ref["recovered"]) <= 1e-9
        assert abs(got["sigma"] - ref["sigma"]) <= 1e-9
        assert got["res_px"] == ref["res_px"]


# Calculator section 12 table (docs/agent_reports/C_calculator_output.txt lines 474-481), printed to
# 4 decimals: (dphi_true, fringe_px, dose, recovered, sigma_terr, res_px). Tolerance: half a unit of
# the last printed digit (5e-5).
SECTION12_ROWS = [
    ("wrapped", 8.0, 0.0, 2.3596, 0.0001, 24.0),
    ("wrapped", 8.0, 1.0e4, 2.3597, 0.0006, 24.0),
    ("wrapped", 8.0, 1.0e2, 2.3597, 0.0059, 24.0),
    ("wrapped", 4.0, 1.0e4, 2.3596, 0.0012, 12.0),
    ("wrapped", 16.0, 1.0e4, 2.3585, 0.0003, 48.0),
    ("mod2pi", 8.0, 1.0e4, -2.3594, 0.0006, 24.0),
    (0.0, 8.0, 1.0e4, 0.0003, 0.0006, 24.0),
    (-1.5640, 8.0, 1.0e4, -1.5637, 0.0006, 24.0),
]


@pytest.mark.parametrize("dphi,fringe,dose,rec,sig,res", SECTION12_ROWS)
def test_calculator_section12_table_reproduced(dphi, fringe, dose, rec, sig, res):
    wrapped, mod2pi = calculator_T24_reference()
    d = {"wrapped": wrapped, "mod2pi": mod2pi}.get(dphi, dphi)
    got = roundtrip(d, fringe_px=fringe, dose_per_px=dose, seed=12345)
    assert abs(got["recovered"] - rec) <= 5e-5
    assert abs(got["sigma"] - sig) <= 5e-5
    assert got["res_px"] == res


@pytest.mark.parametrize("carrier_sign", [+1.0, -1.0])
def test_sign_reversing_the_step_reverses_the_phase(carrier_sign):
    """Up-step and down-step through the whole chain, with the reference on either side (the
    phi_o - phi_r sideband is selected at -q_ref in both cases). Tolerance: T24's 5e-3 rad."""
    want, _ = calculator_T24_reference()
    up = roundtrip(+want, dose_per_px=1e4, seed=12345, carrier_sign=carrier_sign)["recovered"]
    down = roundtrip(-want, dose_per_px=1e4, seed=12345, carrier_sign=carrier_sign)["recovered"]
    assert abs(up - want) <= T24_TOL_RAD
    assert abs(down + want) <= T24_TOL_RAD
    assert np.sign(up) == -np.sign(down)


def test_T24_with_subpixel_refinement():
    """The declared sub-pixel refinement ('dft_ratio') leaves T24 within its tolerance."""
    want, _ = calculator_T24_reference()
    got = roundtrip(want, dose_per_px=1e4, seed=12345, subpixel="dft_ratio")
    assert abs(got["recovered"] - want) <= T24_TOL_RAD
    assert max(abs(v) for v in got["carrier"].subpixel_offset_bins) < 0.01
