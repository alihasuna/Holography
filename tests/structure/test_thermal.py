"""Si thermal displacement of the frozen-phonon model (model_assumptions B35, report E2):
B(T) = 0.4761 A^2 + 0.0014 A^2/K (T - 295.5 K) (Heacock et al. 2021, arXiv:2103.05428v3 pp. 6, 25),
u = sqrt(B/(8 pi^2)) per axis; specimen temperature PROJECT_INPUT item 23 (no default); validity
range 273.15-323.15 K and its justification; A7 (0.076 A) still accepted by FrozenPhonons."""
import math

import numpy as np
import pytest

from reflection_holo.structure import thermal

LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 23 (specimen temperature)"


def test_reference_values_E6_confirmed():
    assert thermal.si_debye_waller_B_A2(295.5) == 0.4761
    u = thermal.si_rms_displacement_per_axis_A(295.5)
    assert abs(u - 0.07765) <= 5e-6                       # L6 2.3 / E6 section 2: 0.07765 A
    assert u == pytest.approx(math.sqrt(0.4761 / (8 * math.pi ** 2)), rel=1e-15)
    assert abs(thermal.si_rms_displacement_sigma_A(295.5) - 0.00014) <= 5e-6   # +-0.00014 A
    # slope: 10 K moves B by 0.014 A^2 = 2.94 % (E6 section 2: "2.94 %")
    dB = thermal.si_debye_waller_B_A2(305.5) - thermal.si_debye_waller_B_A2(295.5)
    assert dB == pytest.approx(0.014, abs=1e-12)
    assert round(100 * dB / 0.4761, 2) == 2.94
    # A7 (0.076 A) is 4.2 % low in B and 2.1 % low in u against B35 at 295.5 K (E6: 4.21 %, 2.13 %)
    assert round(100 * (1 - 8 * math.pi ** 2 * 0.076 ** 2 / 0.4761), 2) == 4.21
    assert round(100 * (1 - 0.076 / u), 2) == 2.13


@pytest.mark.parametrize("T", [273.15, 295.5, 300.0, 323.15])
def test_range_is_accepted(T):
    assert thermal.si_debye_waller_B_A2(T) > 0


@pytest.mark.parametrize("T", [273.14, 323.16, 205.0, 77.0, 1023.15])
def test_outside_the_range_is_refused(T):
    with pytest.raises(thermal.TemperatureOutOfRangeError, match="refused rather than extrapolated"):
        thermal.si_rms_displacement_per_axis_A(T)


@pytest.mark.parametrize("T", [float("nan"), float("inf"), True, "295.5", None])
def test_invalid_temperatures(T):
    with pytest.raises((TypeError, ValueError)):
        thermal.si_debye_waller_B_A2(T)


def test_temperature_is_required_and_labelled():
    with pytest.raises(ValueError, match="item 23"):
        thermal.frozen_phonon_arguments(specimen_temperature_K=None, temperature_label=LABEL)
    for bad in ("", "room temperature", "SECTION_READ", None):
        with pytest.raises(ValueError, match="label"):
            thermal.frozen_phonon_arguments(specimen_temperature_K=295.5, temperature_label=bad)
    a = thermal.frozen_phonon_arguments(specimen_temperature_K=295.5, temperature_label=LABEL)
    assert a["label"].startswith("ASSUMPTION B35") and LABEL in a["label"]
    assert a["rms_displacement_A"] == thermal.si_rms_displacement_per_axis_A(295.5)


def test_frozen_phonons_accept_B35_and_keep_A7():
    from reflection_holo.forward.multislice import FrozenPhonons
    fp = FrozenPhonons(**thermal.frozen_phonon_arguments(specimen_temperature_K=300.0,
                                                         temperature_label=LABEL))
    assert fp.rms_displacement_A == pytest.approx(
        math.sqrt((0.4761 + 0.0014 * 4.5) / (8 * math.pi ** 2)), rel=1e-15)
    a7 = FrozenPhonons(rms_displacement_A=0.076,
                       label="ASSUMPTION A7: 0.076 A per axis (inspected repository)")
    assert a7.rms_displacement_A == 0.076                    # A7 keeps working unchanged


def test_validity_range_justification_numbers():
    """The docstring's range argument: Einstein and Debye models matched to B and dB/dT at
    295.5 K differ from the linear form by <= 2.4e-4 A^2 inside [273.15, 323.15] K (below one
    seventh of the 0.0017 A^2 measurement uncertainty) and reach 0.0017 A^2 only near 225 K and
    375 K. The model forms are not sourced; they size the unknown curvature."""
    from scipy.integrate import quad
    from scipy.optimize import brentq
    T0, B0, S = thermal.T_REF_K, thermal.B_REF_A2, thermal.DB_DT_A2_PER_K
    y = brentq(lambda v: v / np.sinh(v) - S / B0 * T0, 0.1, 3.0)
    th_e = y * T0
    C = B0 * np.tanh(th_e / (2 * T0))

    def einstein(T):
        return C / np.tanh(th_e / (2 * T))

    def u_debye(T, th):
        integ = quad(lambda x: x / np.expm1(x) if x > 0 else 1.0, 0, th / T)[0]
        return (0.25 + (T / th) ** 2 * integ) / th

    def dlog(th, h=0.01):
        return (math.log(u_debye(T0 + h, th)) - math.log(u_debye(T0 - h, th))) / (2 * h)

    th_d = brentq(lambda t: dlog(t) - S / B0, 100.0, 2000.0)
    CD = B0 / u_debye(T0, th_d)
    assert round(th_e, 1) == 275.1 and round(th_d, 1) == 482.1

    def lin(T):
        return B0 + S * (T - T0)

    Ts = np.linspace(thermal.T_MIN_K, thermal.T_MAX_K, 201)
    dev_e = max(abs(einstein(T) - lin(T)) for T in Ts)
    dev_d = max(abs(CD * u_debye(T, th_d) - lin(T)) for T in Ts)
    assert dev_e <= 2.4e-4 and dev_d <= 2.4e-4
    assert max(dev_e, dev_d) <= thermal.B_REF_SIGMA_A2 / 7
    for T in (225.0, 375.0):
        assert abs(einstein(T) - lin(T)) >= 0.0015           # near the stated uncertainty there


def test_numpy_floating_temperatures_are_accepted_and_bools_refused():
    """A5 F12: numpy float32 was refused with a TypeError; any real number is a temperature in K,
    a bool (Python or numpy) is not."""
    import numpy as np
    for T in (np.float32(295.5), np.float64(295.5), np.int64(300), 300):
        assert thermal.si_debye_waller_B_A2(T) == thermal.si_debye_waller_B_A2(float(T))
    for bad in (True, np.bool_(True), "295.5"):
        with pytest.raises(TypeError):
            thermal.si_debye_waller_B_A2(bad)
