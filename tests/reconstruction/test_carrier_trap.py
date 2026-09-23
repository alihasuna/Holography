"""Carrier-location trap (docs/03 section 6; calculator derivations section 7.5; audit C3).

Calculator setup (hologram_roundtrip defaults and the T24 case): n = 512, fringe 8 px, 50/50 tanh step of
sc666.step_phase(d111)['wrapped'] = 2.3596 rad, Hann aperture |q_c|/3, brightest bin searched over the
whole plane outside r < 0.05 cycles/px (the calculator's _sideband_wave without peak_idx), terrace
medians. Printed numbers: 0.78 rad instead of 2.36 rad, i.e. two decimals; the tolerance used is half a
unit of the last printed digit (0.005 rad). The correct path is held to T24's 5e-3 rad.

The calculator's first version is reproduced with reference_correction='none' (its bin: fftshifted
(255, 320), i.e. the CONJUGATE sideband one row off); with 'divide_empty' at the same wrong bin the
ramp cancels and the conjugate sign error alone remains (-2.3596 rad), which is also asserted.

The package refuses the calculator's whole-plane search (it holds both sidebands; audit A2 M1,
model_assumptions B15). The trap bin is reached here only by DECLARING the conjugate half plane on
purpose, on the object hologram (allow_object_hologram=True), and reconstructed only with
trap_demonstration=True; that it is the whole-plane brightest bin is checked against the calculator's
own search.
"""
import numpy as np
import pytest

from holo_cases import (EMPTY_MIN_VISIBILITY, T24_TOL_RAD, calculator, calculator_T24_reference, calculator_mask,
                        calculator_measure, calculator_search, calculator_setup_holograms)
from reflection_holo.reconstruction import CarrierSearch, locate_carrier, reconstruct_sideband

PRINTED_TOL = 0.005


TRAP_DECLARATION = "TRAP DEMONSTRATION: the conjugate sideband (+q_ref) declared on purpose"


def _step(H_obj, carrier, H_emp, correction, trap=False):
    res = reconstruct_sideband(H_obj, carrier=carrier, mask=calculator_mask(carrier),
                               empty_hologram=H_emp if correction == "divide_empty" else None,
                               reference_correction=correction, unwrapping="none",
                               empty_min_visibility=EMPTY_MIN_VISIBILITY if correction == "divide_empty"
                               else None,
                               object_min_visibility=None if correction == "divide_empty" else 0.05,
                               trap_demonstration=trap)
    return calculator_measure(res.wrapped_phase, res.resolution_A, 512)[0], res


@pytest.mark.parametrize("dose", [0.0, 1.0e4])
def test_brightest_object_bin_is_not_the_carrier_and_gives_078(dose):
    want, _ = calculator_T24_reference()
    grid, q_ref, H_obj, H_emp = calculator_setup_holograms(want, dose_per_px=dose, seed=12345)
    qm = float(np.hypot(*q_ref))
    # the calculator's whole-plane search is refused: it names no sideband / holds both (B15, A2 M1)
    with pytest.raises(ValueError, match="non-zero"):
        CarrierSearch(sideband_guess_cycles_per_A=(0.0, 0.0), search_radius_cycles_per_A=np.inf,
                      exclusion_radius_cycles_per_A=0.05, subpixel="none",
                      sideband_declaration=TRAP_DECLARATION)
    with pytest.raises(ValueError, match="one side of a line through the origin"):
        CarrierSearch(sideband_guess_cycles_per_A=(-q_ref[0], -q_ref[1]), search_radius_cycles_per_A=np.inf,
                      exclusion_radius_cycles_per_A=0.05, subpixel="none",
                      sideband_declaration=TRAP_DECLARATION)
    conj_side = CarrierSearch(sideband_guess_cycles_per_A=q_ref, search_radius_cycles_per_A=0.5 * qm,
                              exclusion_radius_cycles_per_A=0.05, subpixel="none",
                              sideband_declaration=TRAP_DECLARATION)
    with pytest.raises(ValueError):
        locate_carrier(H_obj, conj_side)         # refused by default: object hologram
    trap = locate_carrier(H_obj, conj_side, allow_object_hologram=True)
    good = locate_carrier(H_emp, calculator_search(q_ref, "none"))

    # the brightest object bin is fftshifted (255, 320) = unshifted (511, 64): +q_c, one row off
    assert trap.integer_bin == (511, 64)
    assert good.integer_bin == (0, 448)          # -q_c = (0, -1/8) cycles/px: the true sideband
    assert trap.integer_bin != good.integer_bin
    assert "trap" in trap.located_on

    with pytest.raises(ValueError, match="OBJECT hologram"):
        _step(H_obj, trap, None, "none")         # a trap carrier is refused without the opt-in
    wrong, res = _step(H_obj, trap, None, "none", trap=True)
    assert abs(wrong - 0.78) <= PRINTED_TOL, wrong
    assert res.sideband_sign_check.startswith("CONJUGATE")
    # the calculator's own peak search on the same object hologram gives the same bin
    _, pk, _ = calculator()._sideband_wave(np.asarray(H_obj.intensity))
    assert tuple(int(v) for v in pk) == (255, 320)

    right, res_ok = _step(H_obj, good, H_emp, "divide_empty")
    assert abs(right - 2.36) <= PRINTED_TOL
    assert abs(right - want) <= T24_TOL_RAD
    assert res_ok.sideband_sign_check.startswith("phi_o - phi_r")

    # dividing by the empty hologram demodulated at the SAME wrong bin cancels the ramp but not the
    # conjugate-sideband sign error
    conj, _ = _step(H_obj, trap, H_emp, "divide_empty", trap=True)
    assert abs(conj + want) <= T24_TOL_RAD


def test_brightest_bin_on_the_correct_side_is_also_wrong():
    """Restricting the search to the correct sideband does not rescue an object-hologram search: its
    brightest bin there is the Hermitian partner (1, 448), one row off, and the step is -0.78 rad."""
    want, _ = calculator_T24_reference()
    grid, q_ref, H_obj, H_emp = calculator_setup_holograms(want, dose_per_px=0.0)
    trap = locate_carrier(H_obj, calculator_search(q_ref, "none"), allow_object_hologram=True)
    assert trap.integer_bin == (1, 448)
    wrong, res = _step(H_obj, trap, None, "none", trap=True)
    assert abs(wrong + 0.78) <= PRINTED_TOL
    assert res.sideband_sign_check.startswith("phi_o - phi_r")
