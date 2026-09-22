"""Signed phase-to-height conversion with wrap period, branch index and the small-denominator policy.

docs/05_final_repository_specification.md section 5 item 8; source map SM03 (step phase) and SM05
(wrap period, branch). Evidence DERIVED_HERE.

Convention (docs/physics_conventions.md): exp(+i(k.r - omega t)); the step phase is
Delta_phi = phi(upper terrace) - phi(lower terrace) = -(k_out - k_in).R with R.n_hat = h, so for
beams at EXTERNAL glancing angles theta_in, theta_out (vacuum wavelength lambda)

    h = -Delta_phi lambda / (2 pi (sin theta_in,ext + sin theta_out,ext)) = -Delta_phi / (q.n_hat),
    q.n_hat = (2 pi / lambda)(sin theta_in + sin theta_out)   (the sensitivity, rad/A),
    h_2pi   = lambda / (sin theta_in + sin theta_out)          (wrap period; lambda/(2 sin theta)
                                                                for the specular beam).

The height is SIGNED: h > 0 is an up-step (upper terrace higher along the outward normal); a
down-step reverses the sign. Valid for lattice-translation steps between identical terraces and
for specular (or fully in-plane-resolved) reflections; for a non-specular g the in-plane term
q_par.R_par must be removed from Delta_phi first (C report section 4.3).

A single hologram gives the phase modulo 2 pi. The caller therefore passes the WRAPPED phase and a
branch index m explicitly, with the source of m (principal branch of a single hologram, rocking
series, lattice constraint); the unwrapped phase is Delta_phi_wrapped + 2 pi m. The wrap period,
the branch index and its source are always reported.

Small-denominator policy (C report section 4.3 and test-plan item "small-denominator guard"): the
sensitivity s = |q.n_hat| is compared with its propagated uncertainty
    sigma_s^2 = (2 pi / lambda)^2 (cos^2 theta_in sigma_theta_in^2 + cos^2 theta_out sigma_theta_out^2)
                + (s sigma_lambda/lambda)^2,
and the conversion is REFUSED (SmallDenominatorError, before any division) when s <= sigma_s.
Otherwise the height uncertainty sigma_h^2 = (sigma_phi / s)^2 + (h sigma_s / s)^2 is returned
with h.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.geometry.specular import wrap_to_pi
from reflection_holo.quantification.errors import SmallDenominatorError

CONVENTION = ("exp(+i(k.r - omega t)); Delta_phi = phi(upper) - phi(lower) = -(k_out - k_in).R; "
              "h = R.n_hat, n_hat outward; external glancing angles; vacuum wavelength")


def _angles(theta_in_ext_rad, theta_out_ext_rad):
    ti = float(theta_in_ext_rad)
    to = float(theta_out_ext_rad)
    for th in (ti, to):
        if not np.isfinite(th) or th < 0.0 or th > np.pi / 2:
            raise ValueError(f"glancing angles must lie in [0, pi/2] rad, got {th!r}")
    return ti, to


def sensitivity_rad_per_A(*, wavelength_A: float, theta_in_ext_rad: float,
                          theta_out_ext_rad: float) -> float:
    """|q.n_hat| = (2 pi / lambda)(sin theta_in + sin theta_out) in rad/A (SM03, DERIVED_HERE)."""
    ti, to = _angles(theta_in_ext_rad, theta_out_ext_rad)
    return float(TWO_PI / wavelength_A * (np.sin(ti) + np.sin(to)))


def sensitivity_uncertainty_rad_per_A(*, wavelength_A: float, theta_in_ext_rad: float,
                                      theta_out_ext_rad: float, sigma_theta_in_rad: float,
                                      sigma_theta_out_rad: float,
                                      sigma_wavelength_rel: float) -> float:
    """Propagated 1-sigma uncertainty of |q.n_hat| from the angle calibration and the relative
    wavelength (energy) uncertainty, first order (SM03, DERIVED_HERE). All arguments required."""
    ti, to = _angles(theta_in_ext_rad, theta_out_ext_rad)
    for name, v in (("sigma_theta_in_rad", sigma_theta_in_rad),
                    ("sigma_theta_out_rad", sigma_theta_out_rad),
                    ("sigma_wavelength_rel", sigma_wavelength_rel)):
        if not (np.isfinite(v) and v >= 0.0):
            raise ValueError(f"{name} must be finite and >= 0, got {v!r}")
    s = sensitivity_rad_per_A(wavelength_A=wavelength_A, theta_in_ext_rad=ti,
                              theta_out_ext_rad=to)
    k = TWO_PI / wavelength_A
    var = (k**2 * ((np.cos(ti) * sigma_theta_in_rad)**2 + (np.cos(to) * sigma_theta_out_rad)**2)
           + (s * sigma_wavelength_rel)**2)
    return float(np.sqrt(var))


def wrap_period_A(*, wavelength_A: float, theta_in_ext_rad: float,
                  theta_out_ext_rad: float) -> float:
    """Height wrap period h_2pi = lambda / (sin theta_in + sin theta_out) in A; lambda/(2 sin theta)
    for the specular beam (SM05, DERIVED_HERE; check T14). Refuses a zero sensitivity."""
    ti, to = _angles(theta_in_ext_rad, theta_out_ext_rad)
    den = np.sin(ti) + np.sin(to)
    if not den > 0.0:
        raise SmallDenominatorError("sin(theta_in) + sin(theta_out) = 0: no height sensitivity")
    return float(wavelength_A / den)


def branch_index_of(phase_unwrapped_rad) -> int:
    """Branch index m such that phase = wrap_to_pi(phase) + 2 pi m (SM05, DERIVED_HERE)."""
    p = float(phase_unwrapped_rad)
    return int(round((p - wrap_to_pi(p)) / TWO_PI))


@dataclass(frozen=True)
class HeightEstimate:
    """Signed height with its uncertainty, wrap period and branch information (always reported).
    Source map SM03, SM05; evidence DERIVED_HERE."""
    h_A: float
    sigma_h_A: float
    wrapped_phase_rad: float
    branch_index: int
    branch_source: str
    unwrapped_phase_rad: float
    wrap_period_A: float
    h_principal_A: float                 # height of the principal branch (m = 0)
    sensitivity_rad_per_A: float
    sigma_sensitivity_rad_per_A: float
    theta_in_ext_rad: float
    theta_out_ext_rad: float
    convention: str = CONVENTION


def height_from_phase(wrapped_phase_rad: float, *, branch_index: int, branch_source: str,
                      wavelength_A: float, theta_in_ext_rad: float, theta_out_ext_rad: float,
                      sigma_phi_rad: float, sigma_theta_in_rad: float,
                      sigma_theta_out_rad: float, sigma_wavelength_rel: float) -> HeightEstimate:
    """Signed height h = -Delta_phi lambda / (2 pi (sin theta_in,ext + sin theta_out,ext)).

    wrapped_phase_rad must lie in (-pi, pi]; the unwrapped phase is wrapped + 2 pi branch_index,
    and branch_source states where the branch comes from (e.g. "principal branch, single
    hologram: NOT resolved", "rocking series", "lattice constraint"). All keywords are required.
    Applies the small-denominator policy BEFORE dividing (SmallDenominatorError when
    |q.n_hat| <= its propagated uncertainty). docs/05 section 5 item 8; SM03, SM05; DERIVED_HERE.
    """
    w = float(wrapped_phase_rad)
    if not np.isfinite(w) or w <= -np.pi - 1e-12 or w > np.pi + 1e-12:
        raise ValueError(f"wrapped_phase_rad must lie in (-pi, pi]; got {w!r}. Pass the wrapped "
                         f"phase and the branch index separately")
    if int(branch_index) != branch_index:
        raise ValueError("branch_index must be an integer")
    if not isinstance(branch_source, str) or not branch_source.strip():
        raise ValueError("branch_source must state where the branch index comes from")
    if not (np.isfinite(sigma_phi_rad) and sigma_phi_rad >= 0.0):
        raise ValueError("sigma_phi_rad must be finite and >= 0")
    ti, to = _angles(theta_in_ext_rad, theta_out_ext_rad)

    s = sensitivity_rad_per_A(wavelength_A=wavelength_A, theta_in_ext_rad=ti,
                              theta_out_ext_rad=to)
    sigma_s = sensitivity_uncertainty_rad_per_A(
        wavelength_A=wavelength_A, theta_in_ext_rad=ti, theta_out_ext_rad=to,
        sigma_theta_in_rad=sigma_theta_in_rad, sigma_theta_out_rad=sigma_theta_out_rad,
        sigma_wavelength_rel=sigma_wavelength_rel)
    if not s > sigma_s:
        raise SmallDenominatorError(
            f"sensitivity |q.n_hat| = {s:.6g} rad/A is not larger than its propagated "
            f"uncertainty {sigma_s:.6g} rad/A (theta_in = {ti * 1e3:.4f} mrad, theta_out = "
            f"{to * 1e3:.4f} mrad): height refused (small-denominator policy, docs/05 5.8)")

    m = int(branch_index)
    phi = w + TWO_PI * m
    h = -phi / s
    sigma_h = float(np.hypot(sigma_phi_rad / s, h * sigma_s / s))
    return HeightEstimate(
        h_A=float(h), sigma_h_A=sigma_h, wrapped_phase_rad=w, branch_index=m,
        branch_source=branch_source, unwrapped_phase_rad=float(phi),
        wrap_period_A=float(TWO_PI / s), h_principal_A=float(-w / s),
        sensitivity_rad_per_A=s, sigma_sensitivity_rad_per_A=sigma_s,
        theta_in_ext_rad=ti, theta_out_ext_rad=to)


def height_candidates_A(wrapped_phase_rad: float, branches, *, wavelength_A: float,
                        theta_in_ext_rad: float, theta_out_ext_rad: float) -> np.ndarray:
    """Heights -(wrapped + 2 pi m)/|q.n_hat| for each branch m in `branches` (SM05). Used with a
    lattice constraint (h an integer multiple of the layer spacing) to choose the branch.
    Evidence DERIVED_HERE."""
    s = sensitivity_rad_per_A(wavelength_A=wavelength_A, theta_in_ext_rad=theta_in_ext_rad,
                              theta_out_ext_rad=theta_out_ext_rad)
    m = np.asarray(list(branches), dtype=float)
    return -(float(wrapped_phase_rad) + TWO_PI * m) / s
