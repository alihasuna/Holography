"""Rocking-series inversion under phase noise (audit A2 finding B1; proposed model assumption B16).

The auditor's case (A2, scratch script e10): true h = +10 A, 200 keV, specular beam, Gaussian phase
noise per hologram; the unfixed code returned wrong 2 pi branches (h off by one or more h_2pi) with a
sigma_h about 100 times too small in 3 to 28 % of trials. Here every series is inverted with its
per-point phase uncertainties declared (sigma_phi_rad, required), and the B16 criterion decides:

* unwrap guard: (2 pi / lambda) h_max |ds_i| + 3 sqrt(sigma_i^2 + sigma_{i+1}^2) < pi for every
  consecutive pair, else TiltStepTooLargeError;
* weighted least squares Delta_phi = -(2 pi / lambda) h s + 2 pi n (s = sin th_in + sin th_out) with
  a free intercept c: the branch n = round(c / 2 pi) is accepted only if sigma_c < pi/3 and
  |c - 2 pi n| < pi (and, as model checks, |c - 2 pi n| <= 3 sigma_c and chi-square p >= 1e-3);
  otherwise BranchAmbiguityError ("branch unresolved").

Statistical tolerances (stated before the runs, never tuned):
* wrong-branch rate among accepted results: at most the 3-sigma rate p3 = P(|Z| > 3) = 2.70e-3. The
  count k_wrong must not exceed the (1 - 1e-4) quantile of Binomial(n_accepted, p3).
* reported sigma_h against the observed scatter of the correct-branch heights (K results): the ratio
  std/sigma_h within 1 +- 4/sqrt(2 (K - 1)) (4 standard errors of a sample standard deviation), and
  |mean error| <= 4 sigma_h / sqrt(K).
Trials: 2000 per regime; one generator, seed 20260922 (the auditor's seed), regimes in the order
listed.

Round 2 (re-audit A2b N2): h and sigma_h now come from the slope of the free fit, so the height no
longer depends on the branch n. "Wrong branch" is therefore judged on the absolute phase branches
returned with the result (branch_indices m_i, Delta_phi_i = wrapped_i + 2 pi m_i) against the true
ones; the bounds above are unchanged. The uniform grids used here trigger the aliasing warning
(A2b N4), which is filtered in this module.
"""
import math

import numpy as np
import pytest

pytestmark = pytest.mark.filterwarnings("ignore:aliasing above h_max:RuntimeWarning")

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.geometry.specular import specular_step_phase, wrap_to_pi
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.quantification.errors import BranchAmbiguityError, TiltStepTooLargeError
from reflection_holo.quantification.rocking import resolve_rocking_series

LAM = wavelength_A(E)
SEED = 20260922
TRIALS = 2000
P3 = math.erfc(3.0 / math.sqrt(2.0))          # P(|Z| > 3) = 2.6998e-3
ALPHA = 1e-4


def binom_upper_quantile(n: int, p: float, alpha: float) -> int:
    """Smallest k with P(Binomial(n, p) > k) < alpha (exact sum, log space)."""
    if n == 0:
        return 0
    cdf = 0.0
    for k in range(n + 1):
        logpmf = (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                  + k * math.log(p) + (n - k) * math.log1p(-p))
        cdf += math.exp(logpmf)
        if 1.0 - cdf < alpha:
            return k
    return n


def intercept_se_rad(th, sigma):
    """Standard error of the free-fit intercept for equal per-point sigma (auditor's formula)."""
    s = 2.0 * np.sin(th)
    return sigma * np.sqrt(1.0 / s.size + s.mean() ** 2 / np.sum((s - s.mean()) ** 2))


def run_regime(rng, th, sigma, h_true, h_max):
    ok, wrong, refused_branch, refused_guard = [], [], 0, 0
    sig = np.full(th.size, sigma)
    for _ in range(TRIALS):
        phi = specular_step_phase(h_true, th, LAM) + rng.normal(0.0, sigma, th.size)
        w = wrap_to_pi(phi)
        m_true = np.rint((phi - w) / (2 * np.pi)).astype(int)
        try:
            r = resolve_rocking_series(th, th, w, sigma_phi_rad=sig, wavelength_A=LAM, h_max_A=h_max)
        except BranchAmbiguityError as exc:
            assert str(exc).startswith("branch unresolved")
            refused_branch += 1
            continue
        except TiltStepTooLargeError:
            refused_guard += 1
            continue
        (ok if np.array_equal(r.branch_indices, m_true) else wrong).append(r)
    return ok, wrong, refused_branch, refused_guard


# The auditor's five regimes (A2 B1, e10): (tilts lo, hi, step in mrad), noise rad; h = 10 A,
# h_max = 10.5 A. Expected after the fix: none returns a height.
AUDITOR_REGIMES = [((20.0, 21.0, 0.25), 0.05), ((20.0, 21.0, 0.25), 0.1), ((20.0, 21.0, 0.25), 0.2),
                   ((20.0, 25.0, 0.5), 0.2), ((16.0, 17.0, 0.25), 0.1)]


def test_auditor_regimes_return_no_silently_wrong_height():
    rng = np.random.default_rng(SEED)
    for (lo, hi, step), sigma in AUDITOR_REGIMES:
        th = np.arange(lo, hi + 1e-9, step) * 1e-3
        ok, wrong, rb, rg = run_regime(rng, th, sigma, 10.0, 10.5)
        se = intercept_se_rad(th, sigma)
        print(f"tilts {lo}-{hi} mrad step {step} ({th.size}), noise {sigma} rad: intercept s.e. "
              f"{se:.3f} rad ({se / (2 * np.pi):.2f} cycles) -> correct {len(ok)}, WRONG {len(wrong)}, "
              f"refused branch {rb}, refused guard {rg} (of {TRIALS}; seed {SEED})")
        assert len(wrong) == 0
        if se >= np.pi / 3:          # the branch cannot be resolved at 3 sigma: always refused
            assert rb + rg == TRIALS
        # the 11-tilt row is the unwrap-slip regime: the noise-free guard passed (2.63 rad < pi) but
        # 2.63 + 3 sqrt(2) 0.2 = 3.48 rad >= pi, so the noise-aware guard refuses every trial
        if th.size == 11:
            assert rg == TRIALS


# Regimes in which B16 accepts results: (tilts), noise, h_true, h_max. The second is chosen with the
# intercept standard error just below pi/3 (0.90 rad), where the wrong-branch bound is tightest.
ACCEPTED_REGIMES = [((20.0, 25.0, 0.25), 0.05, 10.0, 10.5),
                    ((20.0, 25.0, 0.5), 0.21, 3.0, 3.5)]


@pytest.mark.parametrize("regime", ACCEPTED_REGIMES, ids=["narrow_noise", "near_pi_over_3"])
def test_accepted_results_meet_the_3_sigma_branch_criterion_and_sigma_h(regime):
    (lo, hi, step), sigma, h_true, h_max = regime
    rng = np.random.default_rng(SEED)
    th = np.arange(lo, hi + 1e-9, step) * 1e-3
    se = intercept_se_rad(th, sigma)
    assert se < np.pi / 3
    ok, wrong, rb, rg = run_regime(rng, th, sigma, h_true, h_max)
    n_acc = len(ok) + len(wrong)
    k_max = binom_upper_quantile(n_acc, P3, ALPHA)
    err = np.array([r.h_A - h_true for r in ok])
    sig_h = np.array([r.sigma_h_A for r in ok])
    K = err.size
    ratio = float(np.std(err, ddof=1) / np.median(sig_h))
    bound = 4.0 / math.sqrt(2.0 * (K - 1))
    print(f"tilts {lo}-{hi} mrad step {step} ({th.size}), noise {sigma} rad, h {h_true} A: intercept "
          f"s.e. {se:.3f} rad; accepted {n_acc} (correct {len(ok)}, WRONG {len(wrong)}, allowed "
          f"<= {k_max} at p3 = {P3:.3e}, alpha {ALPHA}), refused branch {rb}, guard {rg}; "
          f"std(h err)/sigma_h = {ratio:.4f} (bound 1 +- {bound:.4f}, K = {K}); mean err "
          f"{err.mean():+.2e} A; seed {SEED}, {TRIALS} trials")
    assert rg == 0
    assert n_acc > 0.99 * TRIALS          # the B16 checks refuse only ~0.4 % of valid series here
    assert len(wrong) <= k_max
    assert np.allclose(sig_h, sig_h[0], rtol=1e-12)     # sigma_h depends on design and sigmas only
    assert abs(ratio - 1.0) <= bound
    assert abs(err.mean()) <= 4.0 * sig_h[0] / math.sqrt(K)
    # the branch statistics are reported with every result
    r = ok[0]
    assert r.sigma_intercept_rad == pytest.approx(se, rel=1e-9)
    assert 0.0 < r.wrong_branch_probability_bound < P3
    assert 0.0 < r.branch_probability <= 1.0
    assert r.sigma_offset_residual_rad == pytest.approx(se, rel=1e-9)
    assert abs(r.offset_residual_rad) <= 3 * r.sigma_offset_residual_rad


def test_unwrap_guard_includes_the_noise_per_increment():
    """|dphi_i| + 3 sigma_inc_i < pi with dphi_i = (2 pi / lambda) h_max |ds_i| and sigma_inc_i =
    sqrt(sigma_i^2 + sigma_{i+1}^2): the prior-only guard passes (2.634 rad) but the noise margin
    does not; one noisy point raises the margin only on its own two increments."""
    th = np.arange(20.0, 25.0 + 1e-9, 0.5) * 1e-3
    w = wrap_to_pi(specular_step_phase(10.0, th, LAM))
    s = 2.0 * np.sin(th)
    inc = 2 * np.pi / LAM * 10.5 * np.max(np.diff(s))
    assert inc < np.pi                                   # the unfixed guard alone would pass
    margin = (np.pi - inc) / 3.0                         # largest allowed sigma_inc
    sig_ok = np.full(th.size, 0.95 * margin / np.sqrt(2.0))
    resolve_rocking_series(th, th, w, sigma_phi_rad=sig_ok, wavelength_A=LAM, h_max_A=10.5)
    sig_bad = np.full(th.size, 1.05 * margin / np.sqrt(2.0))
    with pytest.raises(TiltStepTooLargeError, match="3 sigma"):
        resolve_rocking_series(th, th, w, sigma_phi_rad=sig_bad, wavelength_A=LAM, h_max_A=10.5)
    one = sig_ok.copy()
    one[5] = 2.0 * margin                                # one noisy hologram in the middle
    with pytest.raises(TiltStepTooLargeError, match="tilts 4 and 5|tilts 5 and 6"):
        resolve_rocking_series(th, th, w, sigma_phi_rad=one, wavelength_A=LAM, h_max_A=10.5)


def test_sigma_phi_is_required_per_point_and_positive():
    th = np.arange(20.0, 25.0 + 1e-9, 0.5) * 1e-3
    w = wrap_to_pi(specular_step_phase(3.0, th, LAM))
    with pytest.raises(TypeError):
        resolve_rocking_series(th, th, w, wavelength_A=LAM, h_max_A=3.5)
    for bad in (np.zeros(th.size), np.full(th.size, -0.1), np.full(th.size, np.nan),
                np.full(th.size - 1, 0.1), 0.1, None):
        with pytest.raises(ValueError):
            resolve_rocking_series(th, th, w, sigma_phi_rad=bad, wavelength_A=LAM, h_max_A=3.5)


def test_branch_unresolved_message_and_no_height():
    """sigma_c >= pi/3: refused with a message that says the branch is unresolved and gives sigma_c."""
    th = np.arange(20.0, 21.0 + 1e-9, 0.25) * 1e-3
    w = wrap_to_pi(specular_step_phase(10.0, th, LAM))   # noise-free data, declared sigma 0.05 rad
    with pytest.raises(BranchAmbiguityError, match=r"^branch unresolved.*pi/3"):
        resolve_rocking_series(th, th, w, sigma_phi_rad=np.full(th.size, 0.05), wavelength_A=LAM,
                               h_max_A=10.5)


def test_underdeclared_noise_is_refused():
    """Noise 0.2 rad declared as 0.02 rad: refused ("branch unresolved"), not returned with a
    sigma_h ten times too small."""
    rng = np.random.default_rng(SEED)
    th = np.arange(20.0, 25.0 + 1e-9, 0.25) * 1e-3
    w = wrap_to_pi(specular_step_phase(3.0, th, LAM) + rng.normal(0.0, 0.2, th.size))
    with pytest.raises(BranchAmbiguityError, match="^branch unresolved"):
        resolve_rocking_series(th, th, w, sigma_phi_rad=np.full(th.size, 0.02), wavelength_A=LAM,
                               h_max_A=3.5)


def test_chi_square_check_refuses_residuals_inconsistent_with_sigma():
    """A residual pattern orthogonal to the model (it moves neither the intercept nor the slope)
    of RMS 0.1 rad with declared sigma 0.01 rad: only the chi-square check can see it."""
    rng = np.random.default_rng(SEED)
    th = np.arange(20.0, 25.0 + 1e-9, 0.25) * 1e-3
    s = 2.0 * np.sin(th)
    basis = np.column_stack([np.ones_like(s), s])
    v = rng.normal(0.0, 1.0, th.size)
    v -= basis @ np.linalg.lstsq(basis, v, rcond=None)[0]
    v *= 0.1 / np.sqrt(np.mean(v ** 2))
    w = wrap_to_pi(specular_step_phase(3.0, th, LAM) + v)
    with pytest.raises(BranchAmbiguityError, match="^branch unresolved: chi-square"):
        resolve_rocking_series(th, th, w, sigma_phi_rad=np.full(th.size, 0.01), wavelength_A=LAM,
                               h_max_A=3.5)
    r = resolve_rocking_series(th, th, w, sigma_phi_rad=np.full(th.size, 0.1), wavelength_A=LAM,
                               h_max_A=3.5)                 # declared honestly: accepted
    assert abs(r.h_A - 3.0) <= 4 * r.sigma_h_A and r.chi2_p_value >= 1e-3


def test_chi2_survival_function_against_scipy():
    scipy_stats = pytest.importorskip("scipy.stats")
    from reflection_holo.quantification.rocking import chi2_sf
    for dof in (1, 2, 3, 9, 20, 40):
        for x in (0.0, 0.1, 1.0, dof - 1.0 if dof > 1 else 0.5, dof + 3.0, 3.0 * dof, 60.0):
            assert chi2_sf(x, dof) == pytest.approx(float(scipy_stats.chi2.sf(x, dof)), rel=1e-10,
                                                    abs=1e-300)


def test_wrapped_phases_exclude_minus_pi():
    """NIT (audit A2): the documented range is (-pi, pi]; -pi and values beyond pi are refused."""
    th = np.arange(20.0, 25.0 + 1e-9, 0.5) * 1e-3
    w = wrap_to_pi(specular_step_phase(3.0, th, LAM))
    for bad in (-np.pi, np.pi + 5e-13):
        w2 = w.copy()
        w2[3] = bad
        with pytest.raises(ValueError, match="wrapped"):
            resolve_rocking_series(th, th, w2, sigma_phi_rad=np.full(th.size, 0.01),
                                   wavelength_A=LAM, h_max_A=3.5)
