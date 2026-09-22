"""Aliasing of |h| > h_max in a rocking series (re-audit A2b N4; scratch script r10b_alias.py).

On the re-auditor's uniform grid (21 tilts, 0.25 mrad steps from 20 mrad, h_max 10.5 A, sigma
0.05 rad) every increment of a true h = 30 A (3.76 rad/step) aliases to the same value, so the
unwrapped series is exactly linear and every B16 check passes: 1981 of 2000 trials returned a wrong
height (about -20 A). Aliasing is a property of the grid: with non-uniform steps the aliased
increments differ, the unwrapped series is not linear, and the chi-square or intercept check refuses.

Now every accepted result carries aliasing_undetectable, h_max_A and assumes_abs_h_le_h_max, from a
noise-free scan of all heights h_max < |h| <= alias_scan_max_A through the same unwrap, fit and B16
checks; when an alias would be accepted the flag is True and a RuntimeWarning is issued.
design_rocking_series builds a non-uniform series on which the scan finds no accepted alias.
2000 trials per case, seed 20260923.
"""
import warnings

import numpy as np
import pytest

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.geometry.specular import specular_step_phase, wrap_to_pi
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.quantification.errors import BranchAmbiguityError, TiltStepTooLargeError
from reflection_holo.quantification.rocking import resolve_rocking_series

LAM = wavelength_A(E)
UNIFORM = np.arange(20.0, 25.001, 0.25) * 1e-3
SIG, H_MAX, TRIALS = 0.05, 10.5, 2000


def trials(th, h, rng):
    accepted, refused_msgs = [], []
    for _ in range(TRIALS):
        w = wrap_to_pi(specular_step_phase(h, th, LAM) + rng.normal(0.0, SIG, th.size))
        try:
            with warnings.catch_warnings(record=True) as rec:
                warnings.simplefilter("always")
                r = resolve_rocking_series(th, th, w, sigma_phi_rad=np.full(th.size, SIG),
                                           wavelength_A=LAM, h_max_A=H_MAX)
            accepted.append((r, [str(x.message) for x in rec]))
        except BranchAmbiguityError as exc:
            refused_msgs.append(str(exc))
    return accepted, refused_msgs


def test_uniform_grid_flags_undetectable_aliasing_and_warns():
    w = wrap_to_pi(specular_step_phase(10.0, UNIFORM, LAM))
    with pytest.warns(RuntimeWarning, match="aliasing"):
        r = resolve_rocking_series(UNIFORM, UNIFORM, w, sigma_phi_rad=np.full(UNIFORM.size, SIG),
                                   wavelength_A=LAM, h_max_A=H_MAX)
    assert r.aliasing_undetectable is True and r.assumes_abs_h_le_h_max is True
    assert r.h_max_A == H_MAX and r.alias_scan_max_A > H_MAX and r.alias_examples_A
    # the re-auditor's h = 30 A: still accepted with a wrong height on the uniform grid, but flagged
    acc, _ = trials(UNIFORM, 30.0, np.random.default_rng(20260923))
    assert len(acc) > 0.9 * TRIALS
    assert all(abs(r.h_A - 30.0) > 5.0 and r.aliasing_undetectable for r, _ in acc)
    assert all(any("aliasing" in m for m in msgs) for _, msgs in acc)


def test_design_helper_gives_a_non_uniform_detectable_series():
    from reflection_holo.quantification.rocking import aliasing_scan, design_rocking_series
    th = design_rocking_series(theta_min_rad=20e-3, theta_max_rad=25e-3, h_max_A=H_MAX,
                               wavelength_A=LAM, sigma_phi_rad=SIG)
    d = np.diff(th)
    assert th[0] == 20e-3 and th[-1] <= 25e-3 and th.size >= 3
    assert np.ptp(d) > 0.2 * d.max()                            # clearly non-uniform
    scan = aliasing_scan(th, th, np.full(th.size, SIG), wavelength_A=LAM, h_max_A=H_MAX)
    assert scan.undetectable is False
    w = wrap_to_pi(specular_step_phase(10.0, th, LAM))
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        r = resolve_rocking_series(th, th, w, sigma_phi_rad=np.full(th.size, SIG), wavelength_A=LAM,
                                   h_max_A=H_MAX)
    assert r.aliasing_undetectable is False and r.assumes_abs_h_le_h_max is False
    assert abs(r.h_A - 10.0) <= 1e-6
    with pytest.raises(ValueError):                             # noise too large for h_max
        design_rocking_series(theta_min_rad=20e-3, theta_max_rad=25e-3, h_max_A=H_MAX,
                              wavelength_A=LAM, sigma_phi_rad=0.8)


@pytest.mark.parametrize("h", [26.0, 30.0, 40.0])
def test_non_uniform_series_refuses_the_aliased_heights(h):
    """The re-auditor's |h| > h_max cases: refused by the chi-square or the intercept check in
    every trial on the designed series (the uniform grid accepted 622, 1981 and 1979 of 2000)."""
    from reflection_holo.quantification.rocking import design_rocking_series
    th = design_rocking_series(theta_min_rad=20e-3, theta_max_rad=25e-3, h_max_A=H_MAX,
                               wavelength_A=LAM, sigma_phi_rad=SIG)
    acc, msgs = trials(th, h, np.random.default_rng(20260923))
    print(f"h = {h} A on the designed series ({th.size} tilts): accepted {len(acc)}, refused "
          f"{len(msgs)} of {TRIALS} (chi-square {sum('chi-square' in m for m in msgs)}, intercept "
          f"{sum('standard errors' in m for m in msgs)}); seed 20260923")
    assert acc == []
    assert all(("chi-square" in m) or ("standard errors" in m) for m in msgs)


def test_guard_still_uses_h_max():
    from reflection_holo.quantification.rocking import design_rocking_series
    th = design_rocking_series(theta_min_rad=20e-3, theta_max_rad=25e-3, h_max_A=H_MAX,
                               wavelength_A=LAM, sigma_phi_rad=SIG)
    w = wrap_to_pi(specular_step_phase(3.0, th, LAM))
    with pytest.raises(TiltStepTooLargeError):
        resolve_rocking_series(th, th, w, sigma_phi_rad=np.full(th.size, SIG), wavelength_A=LAM,
                               h_max_A=3 * H_MAX)
