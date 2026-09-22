"""Rocking-series (tilt-series) resolution of the 2 pi branch, giving absolute heights.

Source map SM05, evidence DERIVED_HERE (C report section 3.8; docs/03 section 4). For a
lattice-translation step the vacuum step phase is a known function of the glancing angles,
    Delta_phi(theta) = -(2 pi / lambda) h s(theta),  s = sin theta_in + sin theta_out,
with h the only unknown. Unwrapping the measured (wrapped) phases along s recovers h absolutely,
provided consecutive tilts change the phase by less than pi for every |h| <= h_max:
    Delta theta < lambda / (4 h cos theta)   for the specular beam (check T23: 0.627 mrad for
    h = 1 nm at 200 keV).

Algorithm (resolve_rocking_series):
  1. sort by s; refuse (TiltStepTooLargeError) if (2 pi / lambda) h_max max|Delta s| >= pi;
  2. unwrap the wrapped phases along s (numpy.unwrap);
  3. fit phi_u = c - (2 pi / lambda) h s; for a pure translation step c = 2 pi M with M integer;
     refuse (BranchAmbiguityError) if |c/(2 pi) - round(c/(2 pi))| > max_intercept_offset_cycles
     (a dynamical residual, a screw-related a/4 step or excessive noise);
  4. refit h with c = 2 pi M fixed, and report per-angle branch indices m_i
     (Delta_phi_i = wrapped_i + 2 pi m_i), the wrap periods and the residuals.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.geometry.specular import wrap_to_pi
from reflection_holo.quantification.errors import BranchAmbiguityError, TiltStepTooLargeError

CONVENTION = ("exp(+i(k.r - omega t)); Delta_phi = phi(upper) - phi(lower); h = R.n_hat; "
              "external glancing angles; vacuum wavelength")


def max_tilt_step_rad(*, h_A: float, wavelength_A: float, theta_ext_rad: float) -> float:
    """Largest specular tilt step keeping the phase increment below pi: lambda / (4 |h| cos theta).

    Check T23 (0.6270 mrad for h = 1 nm at 200 keV; the calculator's T23 expression omits
    cos(theta), a 2.5e-4 relative difference at 22.5 mrad). Source map SM05, DERIVED_HERE.
    """
    if not abs(h_A) > 0:
        raise ValueError("h_A must be non-zero")
    if not 0.0 <= theta_ext_rad < np.pi / 2:
        raise ValueError("theta_ext_rad must lie in [0, pi/2)")
    return float(wavelength_A / (4.0 * abs(h_A) * np.cos(theta_ext_rad)))


@dataclass(frozen=True)
class RockingSeriesResult:
    """Result of resolve_rocking_series (source map SM05, evidence DERIVED_HERE)."""
    h_A: float
    sigma_h_A: float                      # from the fit residuals (0 for noise-free data)
    branch_indices: np.ndarray            # m_i, input order: Delta_phi_i = wrapped_i + 2 pi m_i
    unwrapped_phases_rad: np.ndarray      # model-consistent unwrapped phases, input order
    wrap_periods_A: np.ndarray            # lambda / s_i, input order
    residuals_rad: np.ndarray             # wrapped_i - model_i, wrapped, input order
    intercept_cycles: float               # free-fit intercept / (2 pi), integer in theory
    max_phase_increment_rad: float        # (2 pi / lambda) h_max max|Delta s|
    convention: str = CONVENTION


def resolve_rocking_series(theta_in_ext_rad, theta_out_ext_rad, wrapped_phases_rad, *,
                           wavelength_A: float, h_max_A: float,
                           max_intercept_offset_cycles: float) -> RockingSeriesResult:
    """Absolute signed height from a tilt series of wrapped step phases (SM05, DERIVED_HERE).

    theta_in_ext_rad, theta_out_ext_rad, wrapped_phases_rad: 1-D arrays of equal length >= 3
    (angles in rad; phases wrapped to (-pi, pi]). h_max_A: the prior upper bound on |h| used by the
    tilt-step guard (required). max_intercept_offset_cycles: tolerance of the integer-intercept test
    (required; 0.25 is a quarter wrap).
    """
    ti = np.atleast_1d(np.asarray(theta_in_ext_rad, dtype=float))
    to = np.atleast_1d(np.asarray(theta_out_ext_rad, dtype=float))
    w = np.atleast_1d(np.asarray(wrapped_phases_rad, dtype=float))
    if not (ti.shape == to.shape == w.shape) or ti.ndim != 1:
        raise ValueError("angle and phase arrays must be 1-D and of equal length")
    if ti.size < 3:
        raise ValueError("a rocking series needs at least 3 tilts")
    if np.any(np.abs(w) > np.pi + 1e-12):
        raise ValueError("phases must be wrapped to (-pi, pi]")
    if not h_max_A > 0:
        raise ValueError("h_max_A must be positive")
    if not 0.0 < max_intercept_offset_cycles < 0.5:
        raise ValueError("max_intercept_offset_cycles must lie in (0, 0.5)")

    kfac = TWO_PI / wavelength_A
    s = np.sin(ti) + np.sin(to)
    order = np.argsort(s)
    s_sorted = s[order]
    if np.any(np.diff(s_sorted) <= 0.0):
        raise ValueError("tilts must be distinct (strictly increasing sin theta_in + sin theta_out)")
    max_inc = float(kfac * h_max_A * np.max(np.diff(s_sorted)))
    if max_inc >= np.pi:
        raise TiltStepTooLargeError(
            f"largest tilt step changes the phase by up to {max_inc:.3f} rad >= pi for "
            f"|h| <= {h_max_A} A; the branch cannot be followed (C report section 3.8)")

    phi_u_sorted = np.unwrap(w[order])
    A = np.column_stack([np.ones_like(s_sorted), s_sorted])
    (c, _b), *_ = np.linalg.lstsq(A, phi_u_sorted, rcond=None)
    c_cycles = float(c / TWO_PI)
    M = int(np.rint(c_cycles))
    if abs(c_cycles - M) > max_intercept_offset_cycles:
        raise BranchAmbiguityError(
            f"fitted intercept {c_cycles:.3f} x 2 pi is not an integer within "
            f"{max_intercept_offset_cycles}: the series is not described by a single "
            f"lattice-translation height (dynamical residual, screw-related step, or noise)")

    y = phi_u_sorted - TWO_PI * M
    h = float(-(s_sorted @ y) / (kfac * (s_sorted @ s_sorted)))
    model_sorted = -kfac * h * s_sorted
    resid_sorted = y - model_sorted
    n = s_sorted.size
    rms = float(np.sqrt(resid_sorted @ resid_sorted / (n - 1)))
    sigma_h = float(rms / (kfac * np.sqrt(s_sorted @ s_sorted)))

    model = -kfac * h * s                                  # input order
    m = np.rint((model - w) / TWO_PI).astype(int)
    unwrapped = w + TWO_PI * m
    return RockingSeriesResult(
        h_A=h, sigma_h_A=sigma_h, branch_indices=m, unwrapped_phases_rad=unwrapped,
        wrap_periods_A=wavelength_A / s, residuals_rad=wrap_to_pi(w - model),
        intercept_cycles=c_cycles, max_phase_increment_rad=max_inc)
