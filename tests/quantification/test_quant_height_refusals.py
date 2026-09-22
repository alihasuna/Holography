"""Refusals of the phase-to-height conversion (audit A2 finding m2 and two NITs; scratch script e8).

m2: with every declared uncertainty 0 the small-denominator refusal could never fire; at
theta = 1e-9 rad the unfixed code returned h = -9.979e+05 A with sigma_h = 0, and it accepted
sigma_phi = 5 rad (> pi). Now every uncertainty must be finite and > 0, sigma_phi < pi, and a zero
sensitivity is refused before anything else.
NITs: the documented wrapped range (-pi, pi] excludes -pi (the unfixed code accepted it, and
|w| up to pi + 1e-12); a non-positive wavelength surfaced as a misleading SmallDenominatorError.
TEST_ONLY uncertainties as in test_quant_height.py.
"""
import numpy as np
import pytest

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.quantification.errors import SmallDenominatorError
from reflection_holo.quantification.height import height_from_phase, sensitivity_rad_per_A

LAM = wavelength_A(E)
SIG = dict(sigma_phi_rad=0.03, sigma_theta_in_rad=0.05e-3, sigma_theta_out_rad=0.05e-3,
           sigma_wavelength_rel=1e-6)


def call(w=0.5, th=0.02, lam=LAM, **over):
    kw = dict(SIG)
    kw.update(over)
    return height_from_phase(w, branch_index=0, branch_source="test", wavelength_A=lam,
                             theta_in_ext_rad=th, theta_out_ext_rad=th, **kw)


@pytest.mark.parametrize("th", [1e-9, 1e-6, 1e-4])
def test_all_zero_uncertainties_are_refused(th):
    """The auditor's case: all sigmas 0 at small angles returned heights up to -9.979e+05 A."""
    with pytest.raises(ValueError, match="> 0"):
        call(th=th, sigma_phi_rad=0.0, sigma_theta_in_rad=0.0, sigma_theta_out_rad=0.0,
             sigma_wavelength_rel=0.0)


@pytest.mark.parametrize("name", list(SIG))
@pytest.mark.parametrize("bad", [0.0, -1e-3, np.nan, np.inf])
def test_each_uncertainty_must_be_positive_and_finite(name, bad):
    with pytest.raises(ValueError, match=name):
        call(**{name: bad})


def test_with_positive_uncertainties_the_small_angle_is_refused_not_divided():
    with pytest.raises(SmallDenominatorError, match="refused"):
        call(th=1e-9)


@pytest.mark.parametrize("sphi", [np.pi, 5.0])
def test_phase_uncertainty_of_pi_or_more_is_refused(sphi):
    with pytest.raises(ValueError, match="sigma_phi_rad"):
        call(sigma_phi_rad=sphi)


def test_zero_sensitivity_refused_first():
    with pytest.raises(SmallDenominatorError):
        call(th=0.0)


@pytest.mark.parametrize("w", [-np.pi, -np.pi - 5e-13, np.pi + 5e-13])
def test_wrapped_phase_range_is_minus_pi_exclusive_to_pi(w):
    with pytest.raises(ValueError, match="wrapped"):
        call(w=w)
    assert call(w=np.pi).wrapped_phase_rad == np.pi


@pytest.mark.parametrize("lam", [-LAM, 0.0, np.nan])
def test_wavelength_is_validated(lam):
    with pytest.raises(ValueError, match="wavelength_A"):
        call(lam=lam)
    with pytest.raises(ValueError, match="wavelength_A"):
        sensitivity_rad_per_A(wavelength_A=lam, theta_in_ext_rad=0.02, theta_out_ext_rad=0.02)
