"""Internal-Bragg specular condition, beam wavevectors in the surface frame and the step phase.

Source map SM03 (step phase, translation covariance) and SM05 (wrap period h_2pi); refraction from
SM04. Evidence DERIVED_HERE. Ported from tools/reflection_step_phase_calculator.py section 4
(class SpecularCondition) and C report sections 2.1-2.2.

Conventions (docs/physics_conventions.md): exp(+i(k.r - omega t)); |k| = 2 pi / lambda in rad/A;
glancing angles to the surface plane; n_hat is the OUTWARD normal; the step phase is
Delta_phi = phi(upper) - phi(lower) = -(k_out - k_in).R with R.n_hat = h (vacuum wavelength,
EXTERNAL angles). For the specular beam Delta_phi = -(4 pi / lambda) h sin(theta_ext).

Two entry points for the specular condition:
  * SpecularCondition(d_A, order_n, E_keV, V0_V): the lower-level port of the calculator class. It
    does not apply the forbidden-reflection guard; it is used for the calculator's legacy checks
    T4, T6, T10, T14 that evaluate the forbidden (6,-6,6) setting.
  * specular_condition_for(hkl, normal_hkl, ...): the TARGET-level call. It refuses a forbidden
    reflection (ForbiddenReflectionError) unless allow_forbidden=True, a reflection that is not on
    the specular rod (NotSpecularError), and an inaccessible one (InaccessibleReflectionError).
"""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.geometry.crystal import (d_spacing_A, require_allowed_target,
                                              rod_decomposition)
from reflection_holo.geometry.errors import InaccessibleReflectionError, NotSpecularError
from reflection_holo.geometry.refraction import delta_K_per_A
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A


def wrap_to_pi(x):
    """Wrap an angle to (-pi, +pi] (calculator wrap_to_pi). Evidence DERIVED_HERE."""
    out = -((-np.asarray(x, dtype=float) + np.pi) % TWO_PI - np.pi)
    return float(out) if np.ndim(out) == 0 else out


class SpecularCondition:
    """Order-n specular Bragg condition on a rod of spacing d, satisfied INSIDE the crystal.

    Premises (DERIVED_HERE; calculator section 4): P1 the surface-averaged potential is a step of
    depth V0, so K_int^2 = K_ext^2 + dK^2 for the normal components; P2 the Bragg condition holds
    for the internal wavevectors, 2 K_int = |G| = 2 pi n / d; P3 the terraces are rigid translates,
    R.n_hat = h; P4 vacuum step phase Delta_phi = -(k_out - k_in).R = -2 h K_ext.
    Source map SM03 (step phase), SM04 (refraction), SM05 (h_2pi).

    All four arguments are REQUIRED (V0_V is PROJECT_INPUT item 20; 12.0 V is an ASSUMPTION the
    caller passes explicitly). This lower-level class applies NO forbidden-reflection guard; use
    specular_condition_for() to choose a target.

    Attributes (angles in rad, wavevectors in rad/A, lengths in A): lam_A, k, dK, k_int,
    theta_B_vac (vacuum Bragg angle), K_int, theta_int, accessible, K_ext, theta_ext, rho,
    h_2pi_A. For an inaccessible condition (K_int <= dK) theta_ext, K_ext, rho and h_2pi_A are NaN,
    as in the calculator, and the methods raise InaccessibleReflectionError.
    """

    def __init__(self, d_A: float, order_n: int, E_keV: float, V0_V: float):
        if not d_A > 0:
            raise ValueError(f"d_A must be positive, got {d_A!r}")
        if int(order_n) != order_n or int(order_n) < 1:
            raise ValueError(f"order_n must be a positive integer, got {order_n!r}")
        self.d_A = float(d_A)
        self.n = int(order_n)
        self.E_keV = float(E_keV)
        self.V0_V = float(V0_V)

        self.lam_A = float(wavelength_A(E_keV))
        self.k = float(k_ang_per_A(E_keV))
        self.dK = delta_K_per_A(E_keV, V0_V)
        self.k_int = float(np.sqrt(self.k**2 + self.dK**2))

        s = self.n * self.lam_A / (2.0 * self.d_A)
        self.theta_B_vac = float(np.arcsin(s)) if s <= 1.0 else np.nan

        self.K_int = np.pi * self.n / self.d_A
        self.theta_int = float(np.arcsin(np.clip(self.K_int / self.k_int, -1, 1)))

        arg = self.K_int**2 - self.dK**2
        self.accessible = bool(arg > 0.0)
        self.K_ext = float(np.sqrt(arg)) if self.accessible else np.nan
        self.theta_ext = (float(np.arcsin(np.clip(self.K_ext / self.k, -1, 1)))
                          if self.accessible else np.nan)
        self.rho = self.K_ext / self.K_int if self.accessible else np.nan
        self.h_2pi_A = (self.lam_A / (2.0 * np.sin(self.theta_ext))
                        if self.accessible else np.nan)

    def _require_accessible(self) -> None:
        if not self.accessible:
            raise InaccessibleReflectionError(
                f"order {self.n} of d = {self.d_A:.6f} A: internal Bragg angle "
                f"{self.theta_int * 1e3:.4f} mrad is below the escape angle; no external beam")

    @property
    def foreshortening(self) -> float:
        """1/sin(theta_ext), the image foreshortening along the beam (SM07, check T20)."""
        self._require_accessible()
        return float(1.0 / np.sin(self.theta_ext))

    def step_phase(self, h_A: float) -> dict:
        """Signed and wrapped step phase for a step of signed height h_A (h > 0: up-step).

        Returns total (signed, phi_up - phi_low = -2 h K_ext), abstotal, over2pi, frac2pi,
        mod2pi (|total| mod 2 pi, the calculator's T10-T13 quantity) and wrapped (total wrapped to
        (-pi, pi]). Source map SM03, evidence DERIVED_HERE.
        """
        self._require_accessible()
        signed = -2.0 * float(h_A) * self.K_ext
        absval = abs(signed)
        over = absval / TWO_PI
        frac = over - np.floor(over)
        return dict(total=signed, abstotal=absval, over2pi=over, frac2pi=frac,
                    mod2pi=frac * TWO_PI, wrapped=wrap_to_pi(signed))

    def dphi_dtheta(self, h_A: float) -> float:
        """d|Delta_phi|/d(theta_ext) = (4 pi h / lambda) cos(theta_ext) in rad/rad (SM05)."""
        self._require_accessible()
        return float(4.0 * np.pi * abs(h_A) / self.lam_A * np.cos(self.theta_ext))


def specular_condition_for(hkl, normal_hkl, *, E_keV: float, V0_V: float, a_A: float,
                           allow_forbidden: bool = False) -> SpecularCondition:
    """TARGET-level specular condition for the reflection hkl of the surface with normal normal_hkl.

    Checks, in order: hkl lies on the specular rod with the outward sense (hkl = n p, p the
    primitive normal, n > 0; else NotSpecularError); the forbidden-reflection guard (SM02;
    ForbiddenReflectionError unless allow_forbidden=True, which exists only for the calculator's
    legacy (6,-6,6) checks); accessibility (InaccessibleReflectionError if K_int <= dK). Returns
    SpecularCondition(d_p, n, ...) with d_p = a/|p| (e.g. d_111 and order 6 for (6,-6,6); d_001 = a
    and order 8 for (0,0,8)). Source map SM02, SM03, SM04, SM05, evidence DERIVED_HERE.
    E_keV, V0_V and a_A are required keywords (no defaults).
    """
    p_hkl, n = rod_decomposition(hkl)
    p_nrm, _ = rod_decomposition(normal_hkl)
    if p_hkl != p_nrm:
        raise NotSpecularError(
            f"reflection {tuple(int(v) for v in hkl)} is not on the specular rod of the "
            f"{tuple(int(v) for v in normal_hkl)} surface (outward rod direction {p_nrm}); "
            f"signs matter: the (1,-1,1) rod is (n,-n,n), not (n,n,n)")
    require_allowed_target(hkl, allow_forbidden=allow_forbidden)
    sc = SpecularCondition(d_spacing_A(p_nrm, a_A), n, E_keV, V0_V)
    sc.hkl = tuple(int(v) for v in hkl)
    if not sc.accessible:
        raise InaccessibleReflectionError(
            f"specular reflection {sc.hkl}: internal Bragg angle {sc.theta_int * 1e3:.4f} mrad "
            f"is below the escape angle (E = {E_keV} keV, V0 = {V0_V} V)")
    return sc


def beam_wavevectors_slab(theta_in_ext: float, theta_out_ext: float, k: float):
    """Vacuum wavevectors k_in, k_out (rad/A) in the slab frame (x_hat outward normal, y_hat, z_hat
    beam azimuth; reflection_holo.geometry.frames), for glancing angles theta_in_ext (incidence,
    beam travelling INTO the surface) and theta_out_ext (exit), both in the (x, z) plane:
        k_in  = k (-sin theta_in,  0, cos theta_in)
        k_out = k (+sin theta_out, 0, cos theta_out)
    Use SurfaceFrame.to_crystal to express them on cubic axes. q = k_out - k_in has
    q.n_hat = k (sin theta_in + sin theta_out). Evidence DERIVED_HERE (C report section 2.2).
    """
    for th in (theta_in_ext, theta_out_ext):
        if not 0.0 <= th <= np.pi / 2:
            raise ValueError("glancing angles must lie in [0, pi/2] rad")
    k_in = k * np.array([-np.sin(theta_in_ext), 0.0, np.cos(theta_in_ext)])
    k_out = k * np.array([np.sin(theta_out_ext), 0.0, np.cos(theta_out_ext)])
    return k_in, k_out


def step_phase_translation(k_in, k_out, R_A) -> float:
    """Exact step phase Delta_phi = phi(upper) - phi(lower) = -(k_out - k_in).R.

    k_in, k_out in rad/A and R (the translation mapping the lower-terrace crystal onto the upper
    one, R.n_hat = h) in A, all in the same Cartesian frame. Holds in full dynamical theory for
    lattice-translation steps between identical terraces (translation covariance); NOT valid for
    Si(001) a/4 steps (screw-related terraces). Source map SM03, evidence DERIVED_HERE.
    """
    q = np.asarray(k_out, dtype=float) - np.asarray(k_in, dtype=float)
    return float(-(q @ np.asarray(R_A, dtype=float)))


def specular_step_phase(h_A, theta_ext_rad, wavelength_A_: float):
    """Specular step phase Delta_phi = -(4 pi / lambda) h sin(theta_ext) (signed; h > 0 up-step).

    Vacuum wavelength and EXTERNAL glancing angle. Source map SM03, evidence DERIVED_HERE.
    """
    out = -(4.0 * np.pi / wavelength_A_) * np.asarray(h_A, dtype=float) * np.sin(theta_ext_rad)
    return float(out) if np.ndim(out) == 0 else out
