"""Rocking-series (tilt-series) resolution of the 2 pi branch, giving absolute heights.

Source map SM05, evidence DERIVED_HERE (C report section 3.8; docs/03 section 4). For a
lattice-translation step the vacuum step phase is a known function of the glancing angles,
    Delta_phi(theta) = -(2 pi / lambda) h s(theta) + 2 pi n,  s = sin theta_in + sin theta_out,
(specular: s = 2 sin theta_ext, i.e. -(4 pi h / lambda) sin theta_ext + 2 pi n), with h the only
unknown and n the integer branch left by unwrapping. Consecutive tilts must change the phase by
less than pi for every |h| <= h_max: Delta theta < lambda / (4 h cos theta) for the specular beam
(check T23: 0.627 mrad for h = 1 nm at 200 keV), and the phase noise must not push an increment
over pi.

Acceptance criterion (proposed model assumption B16; audit A2 finding B1). Every phase carries its
declared 1-sigma uncertainty sigma_i (sigma_phi_rad, required, > 0, one per tilt):
  1. unwrap guard: sort by s; for every consecutive pair
         (2 pi / lambda) h_max |s_{i+1} - s_i| + 3 sqrt(sigma_i^2 + sigma_{i+1}^2) < pi,
     i.e. the largest phase increment allowed by the prior bound plus three standard deviations
     of the increment's noise; otherwise TiltStepTooLargeError (no unwrapping is attempted);
  2. unwrap the wrapped phases along s (numpy.unwrap);
  3. weighted least squares (weights 1/sigma_i^2) of phi_u = c - (2 pi / lambda) h s with a free
     intercept c; covariance (A^T W A)^-1 with the DECLARED sigmas (not rescaled by the
     residuals). n = round(c / 2 pi);
  4. the branch n is ACCEPTED only if sigma_c < pi/3 (the 3-sigma criterion: a wrong branch
     needs an intercept error > pi = 3 sigma_c, probability < P(|Z| > 3) = 2.7e-3) and
     |c - 2 pi n| < pi. Model checks, also refused: |c - 2 pi n| <= 3 sigma_c (the intercept of a
     single lattice-translation height is exactly 2 pi n; a dynamical residual, a screw-related
     a/4 step or an unwrap slip moves it) and a chi-square goodness of fit of the constrained
     model with p >= CHI2_P_MIN = 1e-3 (the residuals must be consistent with the declared
     sigmas). Every refusal raises BranchAmbiguityError with a message starting
     "branch unresolved";
  5. with c = 2 pi n fixed, weighted least squares for h alone; sigma_h = 1 / ((2 pi / lambda)
     sqrt(sum s_i^2 / sigma_i^2)) is the fit covariance CONDITIONAL on the accepted branch. The
     branch statistics are reported with it: sigma_c, the frequentist bound
     P(|Z| > pi / sigma_c) on choosing a wrong branch, the posterior probability of n under a
     flat prior on the integer branch, and the heights of the neighbouring branches n -+ 1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.geometry.specular import wrap_to_pi
from reflection_holo.quantification.errors import BranchAmbiguityError, TiltStepTooLargeError

CONVENTION = ("exp(+i(k.r - omega t)); Delta_phi = phi(upper) - phi(lower); h = R.n_hat; "
              "external glancing angles; vacuum wavelength")

GUARD_SIGMAS = 3.0                 # unwrap guard: increment + 3 sigma_increment < pi (B16)
BRANCH_SE_LIMIT_RAD = np.pi / 3.0  # sigma_c < pi/3: the 3-sigma branch criterion (B16)
INTERCEPT_SIGMAS = 3.0             # |c - 2 pi n| <= 3 sigma_c (B16 model check)
CHI2_P_MIN = 1e-3                  # chi-square goodness-of-fit refusal level (B16 model check)
CRITERION = ("B16 (proposed): unwrap guard (2 pi/lambda) h_max |ds_i| + 3 sqrt(sigma_i^2 + "
             "sigma_(i+1)^2) < pi; WLS with free intercept c; branch n = round(c/2 pi) accepted "
             "only if sigma_c < pi/3 and |c - 2 pi n| < pi; model checks |c - 2 pi n| <= 3 sigma_c "
             "and chi-square p >= 1e-3")


def chi2_sf(x: float, dof: int) -> float:
    """Survival function of the chi-square distribution, Q(dof/2, x/2) (regularized upper
    incomplete gamma; series for x < a + 1, Lentz continued fraction otherwise). Standard
    numerics, checked against scipy.stats.chi2.sf in the tests (evidence DERIVED_HERE)."""
    if int(dof) != dof or dof < 1:
        raise ValueError("dof must be a positive integer")
    if not np.isfinite(x) or x < 0.0:
        raise ValueError("x must be finite and >= 0")
    a, z = 0.5 * float(dof), 0.5 * float(x)
    if z == 0.0:
        return 1.0
    log_pref = -z + a * math.log(z) - math.lgamma(a)
    if z < a + 1.0:
        ap, term, total = a, 1.0 / a, 1.0 / a
        for _ in range(10000):
            ap += 1.0
            term *= z / ap
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        return float(max(0.0, 1.0 - total * math.exp(log_pref)))
    tiny = 1e-300
    b = z + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return float(math.exp(log_pref) * h)


def max_tilt_step_rad(*, h_A: float, wavelength_A: float, theta_ext_rad: float) -> float:
    """Largest specular tilt step keeping the phase increment below pi: lambda / (4 |h| cos theta).

    Check T23 (0.6270 mrad for h = 1 nm at 200 keV; the calculator's T23 expression omits
    cos(theta), a 2.5e-4 relative difference at 22.5 mrad). Noise-free bound: with phase noise the
    guard of resolve_rocking_series also subtracts 3 standard deviations of each increment.
    Source map SM05, DERIVED_HERE.
    """
    if not abs(h_A) > 0:
        raise ValueError("h_A must be non-zero")
    if not 0.0 <= theta_ext_rad < np.pi / 2:
        raise ValueError("theta_ext_rad must lie in [0, pi/2)")
    _require_wavelength(wavelength_A)
    return float(wavelength_A / (4.0 * abs(h_A) * np.cos(theta_ext_rad)))


def _require_wavelength(wavelength_A) -> float:
    lam = float(wavelength_A)
    if not (np.isfinite(lam) and lam > 0.0):
        raise ValueError(f"wavelength_A must be finite and > 0, got {wavelength_A!r}")
    return lam


@dataclass(frozen=True)
class RockingSeriesResult:
    """Result of resolve_rocking_series (source map SM05, evidence DERIVED_HERE; criterion B16)."""
    h_A: float
    sigma_h_A: float                      # WLS covariance with the declared sigmas, GIVEN branch n
    branch: int                           # accepted intercept branch n (c = 2 pi n)
    branch_indices: np.ndarray            # m_i, input order: Delta_phi_i = wrapped_i + 2 pi m_i
    unwrapped_phases_rad: np.ndarray      # model-consistent unwrapped phases, input order
    wrap_periods_A: np.ndarray            # lambda / s_i, input order
    residuals_rad: np.ndarray             # wrapped_i - model_i, wrapped, input order
    intercept_rad: float                  # free-fit intercept c
    sigma_intercept_rad: float            # its standard error (declared sigmas)
    intercept_offset_sigmas: float        # (c - 2 pi n) / sigma_c
    intercept_cycles: float               # c / (2 pi), integer in theory
    wrong_branch_probability_bound: float  # P(|Z| > pi / sigma_c), frequentist, < 2.7e-3
    branch_probability: float             # posterior of n, flat prior on the integer branch
    alternative_branch_heights_A: tuple   # (h for n - 1, h for n + 1)
    h_free_A: float                       # slope-only estimate (free intercept), for context
    sigma_h_free_A: float                 # its standard error
    chi2: float                           # constrained fit, declared sigmas
    chi2_dof: int
    chi2_p_value: float
    max_phase_increment_rad: float        # (2 pi / lambda) h_max max|Delta s| (noise-free part)
    min_guard_margin_rad: float           # min_i [pi - increment_i - 3 sigma_increment_i] > 0
    criterion: str = CRITERION
    convention: str = CONVENTION


def resolve_rocking_series(theta_in_ext_rad, theta_out_ext_rad, wrapped_phases_rad, *,
                           sigma_phi_rad, wavelength_A: float,
                           h_max_A: float) -> RockingSeriesResult:
    """Absolute signed height from a tilt series of wrapped step phases (SM05, DERIVED_HERE; B16).

    theta_in_ext_rad, theta_out_ext_rad, wrapped_phases_rad: 1-D arrays of equal length >= 3
    (angles in rad; phases wrapped to (-pi, pi]). sigma_phi_rad: the 1-sigma uncertainty of each
    wrapped phase (1-D, same length, every value finite and > 0; required, no default).
    h_max_A: the prior upper bound on |h| used by the unwrap guard (required).
    Refuses (TiltStepTooLargeError, BranchAmbiguityError) instead of returning an unresolved branch;
    see the module docstring for the criterion.
    """
    ti = np.atleast_1d(np.asarray(theta_in_ext_rad, dtype=float))
    to = np.atleast_1d(np.asarray(theta_out_ext_rad, dtype=float))
    w = np.atleast_1d(np.asarray(wrapped_phases_rad, dtype=float))
    if not (ti.shape == to.shape == w.shape) or ti.ndim != 1:
        raise ValueError("angle and phase arrays must be 1-D and of equal length")
    if ti.size < 3:
        raise ValueError("a rocking series needs at least 3 tilts")
    if sigma_phi_rad is None:
        raise ValueError("sigma_phi_rad (one phase uncertainty per tilt) is required")
    sig = np.asarray(sigma_phi_rad, dtype=float)
    if sig.shape != w.shape:
        raise ValueError(f"sigma_phi_rad must give one uncertainty per tilt (shape {w.shape}), "
                         f"got shape {sig.shape}")
    if not np.all(np.isfinite(sig)) or np.any(sig <= 0.0):
        raise ValueError("every sigma_phi_rad must be finite and > 0 (a zero uncertainty would "
                         "disable the unwrap guard and the branch criterion)")
    if not np.all(np.isfinite(w)) or np.any(w <= -np.pi) or np.any(w > np.pi):
        raise ValueError("phases must be finite and wrapped to (-pi, pi]")
    for name, a in (("theta_in_ext_rad", ti), ("theta_out_ext_rad", to)):
        if not np.all(np.isfinite(a)) or np.any(a < 0.0) or np.any(a > np.pi / 2):
            raise ValueError(f"{name} must lie in [0, pi/2] rad")
    lam = _require_wavelength(wavelength_A)
    if not (np.isfinite(h_max_A) and h_max_A > 0):
        raise ValueError("h_max_A must be finite and positive")

    kfac = TWO_PI / lam
    s = np.sin(ti) + np.sin(to)
    if np.any(s <= 0.0):
        raise ValueError("every tilt needs sin theta_in + sin theta_out > 0 (height sensitivity)")
    order = np.argsort(s)
    s_sorted = s[order]
    sig_sorted = sig[order]
    if np.any(np.diff(s_sorted) <= 0.0):
        raise ValueError("tilts must be distinct (strictly increasing sin theta_in + sin theta_out)")

    # 1. unwrap guard with the noise of each increment
    inc = kfac * h_max_A * np.diff(s_sorted)
    sig_inc = np.sqrt(sig_sorted[:-1] ** 2 + sig_sorted[1:] ** 2)
    margin = np.pi - inc - GUARD_SIGMAS * sig_inc
    max_inc = float(np.max(inc))
    if np.any(margin <= 0.0):
        i = int(np.argmin(margin))
        raise TiltStepTooLargeError(
            f"tilts {i} and {i + 1} (sorted by s): the increment for |h| <= {h_max_A} A, "
            f"{inc[i]:.3f} rad, plus 3 sigma of its noise, 3 x {sig_inc[i]:.3f} rad, is "
            f"{inc[i] + GUARD_SIGMAS * sig_inc[i]:.3f} rad >= pi: the branch cannot be followed "
            f"(C report section 3.8; criterion B16)")

    # 2. unwrap; 3. weighted fit with a free intercept
    phi_u = np.unwrap(w[order])
    wt = 1.0 / sig_sorted ** 2
    A = np.column_stack([np.ones_like(s_sorted), -kfac * s_sorted])
    normal = A.T @ (wt[:, None] * A)
    cov = np.linalg.inv(normal)
    c, h_free = cov @ (A.T @ (wt * phi_u))
    sigma_c = float(np.sqrt(cov[0, 0]))
    sigma_h_free = float(np.sqrt(cov[1, 1]))
    n = int(np.rint(c / TWO_PI))
    d = float(c - TWO_PI * n)

    # 4. branch criterion (B16) and model checks
    if not sigma_c < BRANCH_SE_LIMIT_RAD:
        raise BranchAmbiguityError(
            f"branch unresolved: the fitted intercept {c:.3f} rad has standard error "
            f"{sigma_c:.3f} rad, not below pi/3 = {BRANCH_SE_LIMIT_RAD:.3f} rad (the 3-sigma "
            f"criterion, B16); widen the tilt range, add tilts or reduce the phase noise")
    if not abs(d) < np.pi:
        raise BranchAmbiguityError(
            f"branch unresolved: the fitted intercept {c:.3f} rad is not within pi of 2 pi n")
    if abs(d) > INTERCEPT_SIGMAS * sigma_c:
        raise BranchAmbiguityError(
            f"branch unresolved: the fitted intercept {c:.3f} rad lies {abs(d) / sigma_c:.1f} "
            f"standard errors ({sigma_c:.3f} rad) from 2 pi x {n}; the series is not described by "
            f"a single lattice-translation height (dynamical residual, screw-related a/4 step, "
            f"unwrap slip or underestimated noise)")

    # 5. constrained fit with c = 2 pi n
    y = phi_u - TWO_PI * n
    Sss = float(np.sum(wt * s_sorted ** 2))
    Ss = float(np.sum(wt * s_sorted))
    h = float(-np.sum(wt * s_sorted * y) / (kfac * Sss))
    sigma_h = float(1.0 / (kfac * np.sqrt(Sss)))
    resid_sorted = y + kfac * h * s_sorted
    chi2 = float(np.sum(wt * resid_sorted ** 2))
    dof = int(s_sorted.size - 1)
    p = chi2_sf(chi2, dof)
    if p < CHI2_P_MIN:
        raise BranchAmbiguityError(
            f"branch unresolved: chi-square {chi2:.2f} for {dof} degrees of freedom (p = {p:.2e} "
            f"< {CHI2_P_MIN:g}): the residuals are inconsistent with the declared phase "
            f"uncertainties or with a single lattice-translation height")

    dh_branch = TWO_PI * Ss / (kfac * Sss)            # height change per unit change of n
    ks = np.arange(-50, 51)
    logw = -0.5 * ((d - TWO_PI * ks) / sigma_c) ** 2
    post = np.exp(logw - logw.max())
    branch_prob = float(post[ks == 0][0] / post.sum())
    wrong_bound = float(math.erfc(np.pi / (sigma_c * math.sqrt(2.0))))

    model = -kfac * h * s                                  # input order
    m = np.rint((model - w) / TWO_PI).astype(int)
    unwrapped = w + TWO_PI * m
    return RockingSeriesResult(
        h_A=h, sigma_h_A=sigma_h, branch=n, branch_indices=m, unwrapped_phases_rad=unwrapped,
        wrap_periods_A=lam / s, residuals_rad=wrap_to_pi(w - model),
        intercept_rad=float(c), sigma_intercept_rad=sigma_c,
        intercept_offset_sigmas=float(d / sigma_c), intercept_cycles=float(c / TWO_PI),
        wrong_branch_probability_bound=wrong_bound, branch_probability=branch_prob,
        alternative_branch_heights_A=(h - dh_branch, h + dh_branch),
        h_free_A=float(h_free), sigma_h_free_A=sigma_h_free, chi2=chi2, chi2_dof=dof,
        chi2_p_value=float(p), max_phase_increment_rad=max_inc,
        min_guard_margin_rad=float(np.min(margin)))
