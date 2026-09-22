"""Rocking-series branch resolution (source map SM05). T23 uses exactly the calculator's reference
value and tolerance (line 1060)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.specular import (SpecularCondition, specular_condition_for,
                                               specular_step_phase, wrap_to_pi)
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.quantification.errors import BranchAmbiguityError, TiltStepTooLargeError
from reflection_holo.quantification.rocking import max_tilt_step_rad, resolve_rocking_series

LAM = wavelength_A(E)
D111 = A_SI_A / np.sqrt(3.0)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def test_T23_max_tilt_step_1nm():
    """T23: max tilt step for h = 1 nm (phase increment < pi) = 0.6270 mrad +/- 1e-3, evaluated at
    the (6,-6,6) setting's external angle as in calculator section 7 (lambda/(4 h cos theta))."""
    th = SpecularCondition(D111, 6, 200.0, 12.0).theta_ext
    check(max_tilt_step_rad(h_A=10.0, wavelength_A=wavelength_A(200.0), theta_ext_rad=th) * 1e3,
          0.6270, 1e-3)


def test_docs03_10nm_tilt_step():
    """docs/03 section 4 (not asserted by the calculator): about 0.06 mrad for h = 10 nm."""
    th = specular_condition_for((4, -4, 4), (1, -1, 1), E_keV=E, V0_V=V0, a_A=A_SI_A).theta_ext
    check(max_tilt_step_rad(h_A=100.0, wavelength_A=LAM, theta_ext_rad=th) * 1e3, 0.06, 0.005)


def series(h, thetas):
    return wrap_to_pi(specular_step_phase(h, thetas, LAM))


@pytest.mark.parametrize("h", [10.0, -10.0, D111, 2.7155, -3 * D111])
def test_absolute_height_recovered_noise_free(h):
    """>= 3 tilts spanning more than one h_2pi: h recovered absolutely, not modulo h_2pi."""
    th = np.arange(20.0, 25.01, 0.5) * 1e-3              # 0.5 mrad < 0.627 mrad for 1 nm
    res = resolve_rocking_series(th, th, series(h, th), wavelength_A=LAM, h_max_A=10.5,
                                 max_intercept_offset_cycles=0.25)
    check(res.h_A, h, 1e-9)
    total = specular_step_phase(h, th, LAM)
    assert np.all(res.branch_indices == np.rint((total - wrap_to_pi(total)) / (2 * np.pi)))
    assert np.allclose(res.unwrapped_phases_rad, total, atol=1e-9)
    assert np.allclose(res.wrap_periods_A, LAM / (2 * np.sin(th)), rtol=1e-15)
    # the height exceeds every wrap period of the series: a single hologram would be ambiguous
    assert abs(h) > res.wrap_periods_A.max()


def test_absolute_height_with_noise_and_unsorted_input():
    rng = np.random.default_rng(12345)
    h = 10.0
    th = np.arange(20.0, 25.01, 0.25) * 1e-3
    perm = rng.permutation(th.size)
    w = wrap_to_pi(specular_step_phase(h, th, LAM) + rng.normal(0.0, 0.05, th.size))
    res = resolve_rocking_series(th[perm], th[perm], w[perm], wavelength_A=LAM, h_max_A=10.5,
                                 max_intercept_offset_cycles=0.25)
    assert abs(res.h_A - h) < 4 * res.sigma_h_A + 1e-6
    assert res.sigma_h_A < 0.05


def test_tilt_step_guard_refuses_coarse_series():
    th = np.arange(20.0, 25.01, 0.8) * 1e-3              # 0.8 mrad > 0.627 mrad for 1 nm
    with pytest.raises(TiltStepTooLargeError):
        resolve_rocking_series(th, th, series(10.0, th), wavelength_A=LAM, h_max_A=10.0,
                               max_intercept_offset_cycles=0.25)


def test_non_translation_phase_is_refused():
    """A constant extra phase (e.g. a dynamical residual of screw-related a/4 terraces) makes the
    intercept non-integer: refused instead of a wrong absolute height."""
    th = np.arange(20.0, 25.01, 0.5) * 1e-3
    w = wrap_to_pi(specular_step_phase(10.0, th, LAM) + 2.0)
    with pytest.raises(BranchAmbiguityError):
        resolve_rocking_series(th, th, w, wavelength_A=LAM, h_max_A=10.5,
                               max_intercept_offset_cycles=0.25)


def test_needs_three_tilts_and_prior_bound():
    th = np.array([20e-3, 21e-3])
    with pytest.raises(ValueError):
        resolve_rocking_series(th, th, series(1.0, th), wavelength_A=LAM, h_max_A=2.0,
                               max_intercept_offset_cycles=0.25)
    with pytest.raises(TypeError):
        resolve_rocking_series(th, th, series(1.0, th), wavelength_A=LAM)
