"""Geometry and constants agree with the reference calculator (checks T1-T14)."""
import numpy as np
import pytest

from reflection_holo import constants as C
from reflection_holo import geometry as G


def test_wavelength_matches_calculator(calculator):
    for E in (100.0, 200.0, 300.0):
        assert C.wavelength_A(E) == pytest.approx(calculator.wavelength_A(E), rel=1e-14)
    assert C.wavelength_A(200.0) == pytest.approx(0.02507934, abs=5e-9)


def test_interaction_constant_200kV():
    # sigma = 2 pi m e lambda / h^2; independent evaluation in SI units
    m0 = C.M_E_C2_EV * C.ELEM_CHARGE_C / C.C_M_S**2
    gamma = 1 + 200e3 / C.M_E_C2_EV
    lam_m = C.wavelength_A(200.0) * 1e-10
    sigma_SI = 2 * np.pi * gamma * m0 * C.ELEM_CHARGE_C * lam_m / C.PLANCK_J_S**2  # rad/(V m)
    assert C.interaction_constant(200.0) == pytest.approx(sigma_SI * 1e-10, rel=1e-12)


def test_refraction_matches_calculator(calculator):
    for V0 in (12.0, 13.9):
        assert G.delta_K(200.0, V0) == pytest.approx(calculator.delta_K_per_A(200.0, V0), rel=1e-13)
        for th in (0.005, 0.0136, 0.03):
            assert G.theta_int_from_ext(th, 200.0, V0) == pytest.approx(
                calculator.theta_int_from_ext_rad(th, 200.0, V0), rel=1e-13)
    assert G.theta_critical(200.0, 12.0) * 1e3 == pytest.approx(8.356, abs=5e-4)


@pytest.mark.parametrize("n,theta_ext_mrad,phase_mod", [
    (4, 13.64, 2.58), (5, 18.17, 3.41), (8, 30.89, 4.54)])
def test_specular_table_of_physics_summary(calculator, n, theta_ext_mrad, phase_mod):
    d111 = 5.4309 / np.sqrt(3)
    sc = G.SpecularCondition(d111, n, 200.0, 12.0)
    ref = calculator.SpecularCondition(d111, n, 200.0, 12.0)
    assert sc.theta_ext == pytest.approx(ref.theta_ext, rel=1e-13)
    assert sc.theta_ext * 1e3 == pytest.approx(theta_ext_mrad, abs=0.005)
    phi = G.specular_step_phase(d111, sc.theta_ext, 200.0)
    assert abs(phi) % (2 * np.pi) == pytest.approx(phase_mod, abs=0.005)


def test_step_phase_sign_convention():
    # up-step (upper terrace = lower translated along the outward normal): negative
    phi_up = G.specular_step_phase(+3.1355, 0.0136, 200.0)
    phi_down = G.specular_step_phase(-3.1355, 0.0136, 200.0)
    assert phi_up < 0 and phi_down == pytest.approx(-phi_up)


def test_wrap_period_and_shadow():
    th = 13.64e-3
    assert G.wrap_period(th, 200.0) == pytest.approx(0.919, abs=5e-4)
    assert G.shadow_length(3.1355, th) == pytest.approx(230, abs=1)
