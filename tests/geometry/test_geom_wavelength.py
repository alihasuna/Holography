"""Wavelength, wavevector, Lorentz factor (source map SM01). Checks T1-T3 use exactly the
calculator's reference values and tolerances (tools/reflection_step_phase_calculator.py,
lines 1019-1021)."""
import numpy as np
import pytest

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.geometry.wavelength import (beta_v_over_c, gamma_lorentz, k_ang_per_A,
                                                 wavelength_A)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def test_T1_wavelength_200keV():
    """T1: lambda(200 keV) = 0.0250793 A +/- 1e-6 (calculator)."""
    check(wavelength_A(200.0), 0.0250793, 1e-6)


def test_T2_wavelength_100keV():
    """T2: lambda(100 keV) = 0.0370144 A +/- 1e-6 (calculator)."""
    check(wavelength_A(100.0), 0.0370144, 1e-6)


def test_T3_wavelength_formula_check_300keV():
    """T3: lambda(300 keV) = 0.0196875 A +/- 1e-6 (calculator). A FORMULA CHECK OF THE WAVELENGTH
    FUNCTION ONLY: 300 keV is never used in any configuration (the beam energy is 200 keV,
    PROJECT_INPUT item 1)."""
    check(wavelength_A(300.0), 0.0196875, 1e-6)


def test_conventions_values_at_supplied_energy():
    """physics_conventions: lambda = 0.02507934 A, k = 250.5323 rad/A at 200 keV (printed digits);
    calculator output section 1: gamma 1.391390, beta 0.695314."""
    assert BEAM_ENERGY_SUPPLIED_KEV == 200.0
    check(wavelength_A(BEAM_ENERGY_SUPPLIED_KEV), 0.02507934, 5e-9)
    check(k_ang_per_A(BEAM_ENERGY_SUPPLIED_KEV), 250.5323, 5e-5)
    check(gamma_lorentz(BEAM_ENERGY_SUPPLIED_KEV), 1.391390, 5e-7)
    check(beta_v_over_c(BEAM_ENERGY_SUPPLIED_KEV), 0.695314, 5e-7)


def test_wavelength_array_and_k_consistency():
    E = np.array([100.0, 200.0])
    lam = wavelength_A(E)
    assert lam.shape == (2,)
    assert np.allclose(k_ang_per_A(E) * lam, 2 * np.pi, rtol=1e-15, atol=0)


@pytest.mark.parametrize("bad", [0.0, -200.0, np.nan])
def test_wavelength_refuses_nonpositive_energy(bad):
    with pytest.raises(ValueError):
        wavelength_A(bad)
