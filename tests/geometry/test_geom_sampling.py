"""Anti-aliasing angle ceilings (source map SM15; the 2/3 rule's attribution is UNVERIFIED).
T21 and T22 use exactly the calculator's reference values and tolerances (lines 1056-1059)."""
import pytest

from reflection_holo.geometry.errors import SamplingError
from reflection_holo.geometry.sampling import antialias_max_angle_rad, require_angle_in_band
from reflection_holo.geometry.wavelength import wavelength_A

LAM = wavelength_A(200.0)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def test_T21_two_thirds_at_013():
    """T21: 2/3-rule ceiling at 0.13 A, 200 keV = 64.31 mrad +/- 0.02."""
    check(antialias_max_angle_rad(0.13, LAM, rule="two_thirds") * 1e3, 64.31, 0.02)


def test_T22_two_thirds_at_050():
    """T22: 2/3-rule ceiling at 0.50 A, 200 keV = 16.72 mrad +/- 0.02 (too small for 24 mrad)."""
    got = antialias_max_angle_rad(0.50, LAM, rule="two_thirds")
    check(got * 1e3, 16.72, 0.02)
    with pytest.raises(SamplingError):
        require_angle_in_band(24e-3, 0.50, LAM, rule="two_thirds")


def test_sm15_other_printed_values():
    """Source map SM15 (printed digits): half-Nyquist 48 mrad at 0.13 A, 12.9 mrad at 0.4845 A,
    12.5 mrad at 0.5 A; 2/3 rule 17.3 mrad at 0.4845 A."""
    check(antialias_max_angle_rad(0.13, LAM, rule="half_nyquist") * 1e3, 48.0, 0.5)
    check(antialias_max_angle_rad(0.4845, LAM, rule="half_nyquist") * 1e3, 12.9, 0.05)
    check(antialias_max_angle_rad(0.50, LAM, rule="half_nyquist") * 1e3, 12.5, 0.05)
    check(antialias_max_angle_rad(0.4845, LAM, rule="two_thirds") * 1e3, 17.3, 0.05)


def test_band_accepts_45_mrad_specular_at_013():
    require_angle_in_band(45e-3, 0.13, LAM, rule="two_thirds")
    require_angle_in_band(45e-3, 0.13, LAM, rule="half_nyquist")


def test_rule_is_required_and_validated():
    with pytest.raises(TypeError):
        antialias_max_angle_rad(0.13, LAM)
    with pytest.raises(ValueError):
        antialias_max_angle_rad(0.13, LAM, rule="nyquist")
