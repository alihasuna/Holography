"""Refraction with the relativistic Delta (source map SM04). T5 uses exactly the calculator's
reference value and tolerance (line 1023). V0 = 12.0 V is the ASSUMPTION of model_assumptions B1,
passed explicitly (reflection_holo.constants.V0_SI_ASSUMPTION_V)."""
import numpy as np
import pytest

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.errors import InaccessibleReflectionError
from reflection_holo.geometry.refraction import (delta_K_per_A, effective_energy_V,
                                                 k_internal_per_A, refraction_delta,
                                                 refraction_delta_first_order, theta_c_rad,
                                                 theta_ext_from_int_rad, theta_int_from_ext_rad)
from reflection_holo.geometry.wavelength import k_ang_per_A


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def test_T5_critical_angle():
    """T5: theta_c(200 keV, V0 = 12 V) = 8.3560 mrad +/- 1e-3 mrad (internal escape angle,
    sin theta_c = dK / k_int, physics_conventions revision 2)."""
    check(theta_c_rad(200.0, 12.0) * 1e3, 8.3560, 1e-3)


def test_delta_value_and_first_order_form():
    """physics_conventions: Delta = 6.98e-5 at 200 keV, 12 V (printed digits); the printed
    first-order form agrees with the exact form to 1e-5 relative."""
    d = refraction_delta(E, V0)
    check(d, 6.98e-5, 5e-8)
    assert abs(refraction_delta_first_order(E, V0) / d - 1.0) < 1e-5


def test_relativistic_delta_is_16_percent_larger_than_nonrelativistic():
    """docs/03 section 3: V0/T is 14 percent too small; the relativistic Delta is 16 percent
    larger (printed digits)."""
    ratio = refraction_delta(E, V0) / (V0 / (E * 1e3))
    check(ratio - 1.0, 0.16, 0.005)
    check(1.0 - 1.0 / ratio, 0.14, 0.005)


def test_escape_angle_equals_theta_int_at_zero_external_angle():
    check(theta_int_from_ext_rad(0.0, E, V0), theta_c_rad(E, V0), 1e-15)
    check(np.sin(theta_c_rad(E, V0)), delta_K_per_A(E, V0) / k_internal_per_A(E, V0), 1e-15)


def test_exact_normal_component_relation():
    """(k_int sin theta_int)^2 = (k sin theta_ext)^2 + dK^2 exactly (calculator section 3)."""
    th = np.array([0.005, 0.0136, 0.0225, 0.04])
    ti = theta_int_from_ext_rad(th, E, V0)
    lhs = (k_internal_per_A(E, V0) * np.sin(ti)) ** 2
    rhs = (k_ang_per_A(E) * np.sin(th)) ** 2 + delta_K_per_A(E, V0) ** 2
    assert np.allclose(lhs, rhs, rtol=1e-12, atol=0)
    check(effective_energy_V(E, V0) / (E * 1e3), 1 / 1.16, 0.01)


def test_inverse_round_trip():
    th = np.linspace(1e-4, 0.08, 50)
    back = theta_ext_from_int_rad(theta_int_from_ext_rad(th, E, V0), E, V0)
    assert np.allclose(back, th, rtol=0, atol=1e-12)


def test_below_escape_angle_is_refused():
    with pytest.raises(InaccessibleReflectionError):
        theta_ext_from_int_rad(0.5 * theta_c_rad(E, V0), E, V0)


def test_V0_is_required():
    with pytest.raises(TypeError):
        theta_c_rad(E)                    # no default mean inner potential
    with pytest.raises(ValueError):
        theta_c_rad(E, None)


def test_zero_V0_is_vacuum():
    th = np.array([0.01, 0.02])
    assert np.allclose(theta_int_from_ext_rad(th, E, 0.0), th, rtol=0, atol=1e-15)
