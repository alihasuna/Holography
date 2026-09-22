"""Rocking-series (tilt-series) resolution of the 2 pi branch, giving absolute heights.

Source map SM05, evidence DERIVED_HERE (C report section 3.8; docs/03 section 4). For a
lattice-translation step the vacuum step phase is a known function of the glancing angles,
    Delta_phi(theta) = -(2 pi / lambda) h s(theta) + 2 pi n,  s = sin theta_in + sin theta_out,
(specular: s = 2 sin theta_ext, i.e. -(4 pi h / lambda) sin theta_ext + 2 pi n), with h the only
unknown and n the integer branch left by unwrapping. Consecutive tilts must change the phase by
less than pi for every |h| <= h_max: Delta theta < lambda / (4 h cos theta) for the specular beam
(check T23: 0.627 mrad for h = 1 nm at 200 keV), and the phase noise must not push an increment
over pi.

Procedure and acceptance criterion (model assumption B16; audit A2 B1, re-audit A2b N2, N4). Every
phase carries its declared 1-sigma uncertainty sigma_i (sigma_phi_rad, required, > 0, one per tilt):
  1. unwrap guard: sort by s; for every consecutive pair
         (2 pi / lambda) h_max |s_{i+1} - s_i| + 3 sqrt(sigma_i^2 + sigma_{i+1}^2) < pi,
     otherwise TiltStepTooLargeError (no unwrapping is attempted);
  2. unwrap the wrapped phases along s (numpy.unwrap);
  3. weighted least squares (weights 1/sigma_i^2) of phi_u = c - (2 pi / lambda) h s with a FREE
     intercept c; covariance (A^T W A)^-1 with the DECLARED sigmas. n = round(c / 2 pi);
  4. refusals (BranchAmbiguityError, message starting "branch unresolved"), unchanged from B16:
     sigma_c >= pi/3; |c - 2 pi n| >= pi; |c - 2 pi n| > 3 sigma_c (the intercept of a single
     lattice-translation height is exactly 2 pi n); chi-square of the fit with c fixed at 2 pi n
     below p = CHI2_P_MIN = 1e-3 for N - 1 degrees of freedom;
  5. the height and its uncertainty are the SLOPE of the free fit, h = -b/(2 pi / lambda), sigma_h
     from its covariance (A2b N2): a constant phase offset (a dynamical residual, a reference-phase
     offset) moves only c, and a common angle-calibration offset d theta moves c by
     -(4 pi h/lambda) cos(theta) d theta and the slope only in second order (-tan(theta) d theta
     relative). The offset residual c - 2 pi n and its standard error sigma_c are reported as a
     model-consistency quantity. Conditional on acceptance by step 4, an offset near 3 sigma_c
     shifts the mean of h by up to about 0.8 sigma_h (selection by the intercept check, derived in
     tests/quantification/test_quant_rocking_offsets.py);
  6. aliasing (A2b N4): a true |h| > h_max makes increments exceed pi; unwrapping then returns
     aliased increments. On a grid where the aliased series passes every check of step 4 (for
     uniform steps it is exactly linear), aliasing is undetectable. aliasing_scan() feeds every
     height h_max < |h| <= h_max + 2 lambda/min(Delta s) (the scan limit, reported), noise free,
     through steps 2 to 4; if one is accepted with a height wrong by more than sigma_h (an alias;
     heights above h_max that are still recovered correctly do not count) the result carries aliasing_undetectable = True and
     assumes_abs_h_le_h_max = True and a RuntimeWarning is issued. design_rocking_series() builds a
     non-uniform series (golden-ratio step fractions of the largest guarded step) on which the
     scan accepts no alias, so aliasing is refused through the chi-square or intercept check (up
     to the scan limit, which the result reports).
"""
from __future__ import annotations

import functools
import math
import warnings
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
GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0
CRITERION = ("B16: unwrap guard (2 pi/lambda) h_max |ds_i| + 3 sqrt(sigma_i^2 + sigma_(i+1)^2) < pi; "
             "WLS with free intercept c; refused unless sigma_c < pi/3, |c - 2 pi n| < pi, "
             "|c - 2 pi n| <= 3 sigma_c and chi-square (c = 2 pi n) p >= 1e-3; h and sigma_h from "
             "the free-fit slope; offset residual c - 2 pi n +- sigma_c reported; aliasing above "
             "h_max flagged when undetectable on the grid")


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


@functools.lru_cache(maxsize=64)
def _chi2_crit(dof: int) -> float:
    """x with chi2_sf(x, dof) = CHI2_P_MIN (bisection)."""
    lo, hi = 0.0, 10.0 * dof + 200.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if chi2_sf(mid, dof) > CHI2_P_MIN else (lo, mid)
    return 0.5 * (lo + hi)


@dataclass(frozen=True)
class _Design:
    s: np.ndarray            # sorted sensitivities sin theta_in + sin theta_out
    wt: np.ndarray           # 1 / sigma_i^2, sorted
    kfac: float
    cov: np.ndarray          # (A^T W A)^-1, parameters (c, h)
    P: np.ndarray            # cov A^T W, so that (c, h) = P @ phi
    sigma_c: float
    sigma_h: float
    Sss: float               # sum w s^2 (fit with c fixed)
    chi2_crit: float         # constrained chi-square at p = CHI2_P_MIN, N - 1 dof


def _design(s_sorted: np.ndarray, sig_sorted: np.ndarray, kfac: float) -> _Design:
    wt = 1.0 / sig_sorted ** 2
    A = np.column_stack([np.ones_like(s_sorted), -kfac * s_sorted])
    cov = np.linalg.inv(A.T @ (wt[:, None] * A))
    P = cov @ (A.T * wt)
    return _Design(s_sorted, wt, kfac, cov, P, float(np.sqrt(cov[0, 0])), float(np.sqrt(cov[1, 1])),
                   float(np.sum(wt * s_sorted ** 2)), _chi2_crit(int(s_sorted.size - 1)))


def _fit(phi_u: np.ndarray, D: _Design):
    """Free fit (c, h), branch n, offset residual d and the constrained chi-square for each row of
    phi_u (shape (M, N), sorted by s). The same arithmetic serves resolve_rocking_series and the
    alias scan, so both apply identical checks."""
    ch = phi_u @ D.P.T
    c, h = ch[:, 0], ch[:, 1]
    n = np.rint(c / TWO_PI)
    d = c - TWO_PI * n
    y = phi_u - TWO_PI * n[:, None]
    h_c = -(y @ (D.wt * D.s)) / (D.kfac * D.Sss)
    resid = y + D.kfac * h_c[:, None] * D.s[None, :]
    chi2 = np.sum(D.wt * resid ** 2, axis=1)
    return c, h, n, d, chi2


def _accepted(d, chi2, D: _Design) -> np.ndarray:
    ok = (np.abs(d) < np.pi) & (np.abs(d) <= INTERCEPT_SIGMAS * D.sigma_c) & (chi2 <= D.chi2_crit)
    return ok & (D.sigma_c < BRANCH_SE_LIMIT_RAD)


@dataclass(frozen=True)
class AliasingScan:
    """Noise-free scan of |h| > h_max through the unwrap, fit and B16 checks (A2b N4)."""
    undetectable: bool          # a wrong (aliased) height would be accepted on this grid
    h_max_A: float
    scan_max_A: float           # heights scanned: h_max < |h| <= scan_max_A (both signs)
    step_A: float
    n_heights: int
    examples_A: tuple           # up to 5 (true h, returned wrong h) pairs that would be accepted


_SCAN_CACHE: dict = {}


def _scan(s_sorted: np.ndarray, sig_sorted: np.ndarray, kfac: float, h_max: float) -> AliasingScan:
    key = (s_sorted.tobytes(), sig_sorted.tobytes(), float(kfac), float(h_max))
    if key in _SCAN_CACHE:
        return _SCAN_CACHE[key]
    D = _design(s_sorted, sig_sorted, kfac)
    ds_min = float(np.min(np.diff(s_sorted)))
    scan_max = h_max + 2.0 * TWO_PI / (kfac * ds_min)
    step = 0.5 * float(np.min(sig_sorted)) / (kfac * float(s_sorted[-1] - s_sorted[0]))
    step = max(step, (scan_max - h_max) / 100000.0)
    mags = h_max + step * np.arange(1, int(np.floor((scan_max - h_max) / step)) + 1)
    heights = np.concatenate([mags, -mags])
    examples = []
    for i in range(0, heights.size, 8192):
        hh = heights[i:i + 8192]
        phi_u = np.unwrap(wrap_to_pi(-kfac * hh[:, None] * s_sorted[None, :]), axis=1)
        _, h_fit, _, d, chi2 = _fit(phi_u, D)
        # an alias is an ACCEPTED result whose height is wrong (by more than sigma_h); heights just
        # above h_max that are still recovered correctly are not aliases
        acc = _accepted(d, chi2, D) & (np.abs(h_fit - hh) > D.sigma_h)
        for j in np.flatnonzero(acc)[:5 - len(examples)]:
            examples.append((float(hh[j]), float(h_fit[j])))
        if len(examples) >= 5:
            break
    out = AliasingScan(bool(examples), float(h_max), float(scan_max), float(step), int(heights.size),
                       tuple(examples))
    if len(_SCAN_CACHE) > 256:
        _SCAN_CACHE.clear()
    _SCAN_CACHE[key] = out
    return out


def _sorted_inputs(theta_in_ext_rad, theta_out_ext_rad, sigma_phi_rad):
    ti = np.atleast_1d(np.asarray(theta_in_ext_rad, dtype=float))
    to = np.atleast_1d(np.asarray(theta_out_ext_rad, dtype=float))
    if not (ti.shape == to.shape) or ti.ndim != 1 or ti.size < 3:
        raise ValueError("angle arrays must be 1-D, of equal length >= 3")
    for name, a in (("theta_in_ext_rad", ti), ("theta_out_ext_rad", to)):
        if not np.all(np.isfinite(a)) or np.any(a < 0.0) or np.any(a > np.pi / 2):
            raise ValueError(f"{name} must lie in [0, pi/2] rad")
    if sigma_phi_rad is None:
        raise ValueError("sigma_phi_rad (one phase uncertainty per tilt) is required")
    sig = np.asarray(sigma_phi_rad, dtype=float)
    if sig.shape != ti.shape:
        raise ValueError(f"sigma_phi_rad must give one uncertainty per tilt (shape {ti.shape}), "
                         f"got shape {sig.shape}")
    if not np.all(np.isfinite(sig)) or np.any(sig <= 0.0):
        raise ValueError("every sigma_phi_rad must be finite and > 0 (a zero uncertainty would "
                         "disable the unwrap guard and the branch criterion)")
    s = np.sin(ti) + np.sin(to)
    if np.any(s <= 0.0):
        raise ValueError("every tilt needs sin theta_in + sin theta_out > 0 (height sensitivity)")
    order = np.argsort(s)
    if np.any(np.diff(s[order]) <= 0.0):
        raise ValueError("tilts must be distinct (strictly increasing sin theta_in + sin theta_out)")
    return ti, to, sig, s, order


def aliasing_scan(theta_in_ext_rad, theta_out_ext_rad, sigma_phi_rad, *, wavelength_A: float,
                  h_max_A: float) -> AliasingScan:
    """Would a height |h| > h_max be accepted (as an alias) on this tilt series? Noise-free scan
    of h_max < |h| <= h_max + 2 lambda/min(Delta s) through the unwrap, fit and B16 checks
    (A2b N4; module docstring, step 6). Evidence DERIVED_HERE."""
    lam = _require_wavelength(wavelength_A)
    if not (np.isfinite(h_max_A) and h_max_A > 0):
        raise ValueError("h_max_A must be finite and positive")
    _, _, sig, s, order = _sorted_inputs(theta_in_ext_rad, theta_out_ext_rad, sigma_phi_rad)
    return _scan(s[order], sig[order], TWO_PI / lam, float(h_max_A))


def design_rocking_series(*, theta_min_rad: float, theta_max_rad: float, h_max_A: float,
                          wavelength_A: float, sigma_phi_rad: float,
                          max_tries: int = 64) -> np.ndarray:
    """A NON-UNIFORM specular tilt series (external glancing angles, rad) from theta_min_rad to at
    most theta_max_rad on which aliasing above h_max is detectable (A2b N4).

    Step k in s = 2 sin(theta) is f_k x ds_max with f_k = 0.5 + 0.5 frac(0.5 + (k + 0.37 t) g),
    g the golden ratio conjugate (a low-discrepancy, incommensurate sequence), and ds_max = 0.95
    (pi - 3 sqrt(2) sigma)/((2 pi/lambda) h_max), the largest step the B16 unwrap guard allows with a
    5 % margin. Try t = 0, 1, ... until aliasing_scan() accepts no alias and sigma_c < pi/3;
    ValueError if the noise is too large for h_max, the range too narrow, or no try succeeds.
    sigma_phi_rad: the per-hologram phase uncertainty the series is designed for (all required;
    max_tries only bounds the search). Evidence DERIVED_HERE.
    """
    lam = _require_wavelength(wavelength_A)
    t0, t1, hm, sg = (float(theta_min_rad), float(theta_max_rad), float(h_max_A),
                      float(sigma_phi_rad))
    if not (np.isfinite(t0) and np.isfinite(t1) and 0.0 < t0 < t1 < np.pi / 2):
        raise ValueError("need 0 < theta_min_rad < theta_max_rad < pi/2")
    if not (np.isfinite(hm) and hm > 0.0 and np.isfinite(sg) and sg > 0.0):
        raise ValueError("h_max_A and sigma_phi_rad must be finite and > 0")
    kfac = TWO_PI / lam
    budget = np.pi - GUARD_SIGMAS * math.sqrt(2.0) * sg
    if budget <= 0.0:
        raise ValueError(f"phase noise {sg} rad too large: 3 sqrt(2) sigma >= pi leaves no tilt step")
    ds_max = 0.95 * budget / (kfac * hm)
    for t in range(int(max_tries)):
        th = [t0]
        k = 0
        while True:
            f = 0.5 + 0.5 * ((0.5 + (k + 0.37 * t) * GOLDEN) % 1.0)
            x = math.sin(th[-1]) + 0.5 * f * ds_max
            if x >= 1.0:
                break
            nxt = math.asin(x)
            if nxt > t1:
                break
            th.append(nxt)
            k += 1
        th = np.asarray(th)
        if th.size < 3:
            raise ValueError("the angle range holds fewer than 3 guarded tilts; widen it")
        sig = np.full(th.size, sg)
        s = 2.0 * np.sin(th)
        if not _design(s, sig, kfac).sigma_c < BRANCH_SE_LIMIT_RAD:
            raise ValueError("the angle range is too narrow for this noise: sigma_c >= pi/3")
        if not _scan(s, sig, kfac, hm).undetectable:
            return th
    raise ValueError(f"no non-uniform series without an accepted alias in {max_tries} tries")


@dataclass(frozen=True)
class RockingSeriesResult:
    """Result of resolve_rocking_series (source map SM05, evidence DERIVED_HERE; criterion B16)."""
    h_A: float                            # from the SLOPE of the free fit (A2b N2)
    sigma_h_A: float                      # its standard error (declared sigmas)
    offset_residual_rad: float            # c - 2 pi n: model-consistency quantity (0 in theory)
    sigma_offset_residual_rad: float      # its standard error, = sigma_c
    offset_residual_sigmas: float         # (c - 2 pi n) / sigma_c, |.| <= 3 when accepted
    branch: int                           # intercept branch n (c ~ 2 pi n)
    branch_indices: np.ndarray            # m_i, input order: Delta_phi_i = wrapped_i + 2 pi m_i
    unwrapped_phases_rad: np.ndarray      # fit-consistent unwrapped phases, input order
    wrap_periods_A: np.ndarray            # lambda / s_i, input order
    residuals_rad: np.ndarray             # wrapped_i - model_i, wrapped, input order
    intercept_rad: float                  # free-fit intercept c
    sigma_intercept_rad: float            # its standard error sigma_c
    intercept_cycles: float               # c / (2 pi)
    wrong_branch_probability_bound: float  # P(|Z| > pi / sigma_c) for the branch indices
    branch_probability: float             # posterior of n, flat prior on the integer branch
    chi2: float                           # fit with c = 2 pi n, declared sigmas
    chi2_dof: int
    chi2_p_value: float
    max_phase_increment_rad: float        # (2 pi / lambda) h_max max|Delta s| (noise-free part)
    min_guard_margin_rad: float           # min_i [pi - increment_i - 3 sigma_increment_i] > 0
    h_max_A: float                        # the prior bound used by the guard
    aliasing_undetectable: bool           # an alias of |h| > h_max would pass on this grid (N4)
    assumes_abs_h_le_h_max: bool          # True when aliasing_undetectable
    alias_scan_max_A: float               # beyond this |h| the scan did not look
    alias_scan_step_A: float
    alias_examples_A: tuple               # (true h, returned h) pairs that would be accepted
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
    warns (RuntimeWarning) when aliasing above h_max is undetectable on the grid. See the module
    docstring for the procedure.
    """
    w = np.atleast_1d(np.asarray(wrapped_phases_rad, dtype=float))
    ti = np.atleast_1d(np.asarray(theta_in_ext_rad, dtype=float))
    if w.shape != ti.shape or w.ndim != 1:
        raise ValueError("angle and phase arrays must be 1-D and of equal length")
    if w.size < 3:
        raise ValueError("a rocking series needs at least 3 tilts")
    ti, to, sig, s, order = _sorted_inputs(theta_in_ext_rad, theta_out_ext_rad, sigma_phi_rad)
    if not np.all(np.isfinite(w)) or np.any(w <= -np.pi) or np.any(w > np.pi):
        raise ValueError("phases must be finite and wrapped to (-pi, pi]")
    lam = _require_wavelength(wavelength_A)
    if not (np.isfinite(h_max_A) and h_max_A > 0):
        raise ValueError("h_max_A must be finite and positive")

    kfac = TWO_PI / lam
    s_sorted = s[order]
    sig_sorted = sig[order]

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
    D = _design(s_sorted, sig_sorted, kfac)
    phi_u = np.unwrap(w[order])
    c_a, h_a, n_a, d_a, chi2_a = _fit(phi_u[None, :], D)
    c, h, n, d, chi2 = float(c_a[0]), float(h_a[0]), int(n_a[0]), float(d_a[0]), float(chi2_a[0])
    sigma_c = D.sigma_c

    # 4. refusals (B16)
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
            f"unwrap slip, aliasing or underestimated noise)")
    dof = int(s_sorted.size - 1)
    p = chi2_sf(chi2, dof)
    if p < CHI2_P_MIN:
        raise BranchAmbiguityError(
            f"branch unresolved: chi-square {chi2:.2f} for {dof} degrees of freedom (p = {p:.2e} "
            f"< {CHI2_P_MIN:g}): the residuals are inconsistent with the declared phase "
            f"uncertainties or with a single lattice-translation height (or aliasing)")

    # 5. branch statistics; 6. aliasing scan of this grid
    ks = np.arange(-50, 51)
    logw = -0.5 * ((d - TWO_PI * ks) / sigma_c) ** 2
    post = np.exp(logw - logw.max())
    branch_prob = float(post[ks == 0][0] / post.sum())
    wrong_bound = float(math.erfc(np.pi / (sigma_c * math.sqrt(2.0))))
    scan = _scan(s_sorted, sig_sorted, kfac, float(h_max_A))
    if scan.undetectable:
        ht, hr = scan.examples_A[0]
        warnings.warn(
            f"aliasing above h_max = {h_max_A} A is undetectable on this tilt grid: a true height of "
            f"{ht:.2f} A would be accepted as {hr:.2f} A (noise-free scan up to {scan.scan_max_A:.1f}"
            f" A). The result assumes |h| <= h_max; use design_rocking_series() for a non-uniform "
            f"series (A2b N4)", RuntimeWarning, stacklevel=2)

    model = d - kfac * h * s                               # fitted phases minus 2 pi n, input order
    m = np.rint((model - w) / TWO_PI).astype(int)
    unwrapped = w + TWO_PI * m
    return RockingSeriesResult(
        h_A=h, sigma_h_A=D.sigma_h, offset_residual_rad=d, sigma_offset_residual_rad=sigma_c,
        offset_residual_sigmas=float(d / sigma_c), branch=n, branch_indices=m,
        unwrapped_phases_rad=unwrapped, wrap_periods_A=lam / s,
        residuals_rad=wrap_to_pi(w - model), intercept_rad=c, sigma_intercept_rad=sigma_c,
        intercept_cycles=float(c / TWO_PI), wrong_branch_probability_bound=wrong_bound,
        branch_probability=branch_prob, chi2=chi2, chi2_dof=dof, chi2_p_value=float(p),
        max_phase_increment_rad=max_inc, min_guard_margin_rad=float(np.min(margin)),
        h_max_A=float(h_max_A), aliasing_undetectable=scan.undetectable,
        assumes_abs_h_le_h_max=scan.undetectable, alias_scan_max_A=scan.scan_max_A,
        alias_scan_step_A=scan.step_A, alias_examples_A=scan.examples_A)
