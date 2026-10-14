"""Reflection geometry: refraction, specular Bragg conditions, step phases.

Ported from tools/reflection_step_phase_calculator.py (same premises P1-P4, all
DERIVED_HERE); tests/test_geometry.py asserts agreement with the calculator.
All angles are GLANCING angles to the surface; wavevectors are angular (rad/A).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .constants import TWO_PI, k_rad_per_A, refraction_delta, wavelength_A


def delta_K(E_keV, V0_V):
    """dK = sqrt(k_int^2 - k^2) [rad/A]: normal-wavevector boost on entering."""
    return float(k_rad_per_A(E_keV) * np.sqrt(refraction_delta(E_keV, V0_V)))


def theta_int_from_ext(theta_ext, E_keV, V0_V):
    """Internal glancing angle (surface-parallel wavevector conserved)."""
    k = float(k_rad_per_A(E_keV))
    dK = delta_K(E_keV, V0_V)
    k_int = np.sqrt(k**2 + dK**2)
    K_int = np.sqrt((k * np.sin(theta_ext)) ** 2 + dK**2)
    return np.arcsin(np.clip(K_int / k_int, -1.0, 1.0))


def theta_critical(E_keV, V0_V):
    """Internal escape angle theta_c, sin(theta_c) = dK / k_int."""
    k = float(k_rad_per_A(E_keV))
    dK = delta_K(E_keV, V0_V)
    return float(np.arcsin(dK / np.sqrt(k**2 + dK**2)))


@dataclass(frozen=True)
class SpecularCondition:
    """Order-n specular Bragg condition, satisfied by the INTERNAL wavevector."""

    d_A: float
    order: int
    E_keV: float
    V0_V: float

    @property
    def lam(self):
        return float(wavelength_A(self.E_keV))

    @property
    def k(self):
        return float(k_rad_per_A(self.E_keV))

    @property
    def K_int(self):
        return np.pi * self.order / self.d_A

    @property
    def accessible(self):
        return self.K_int > delta_K(self.E_keV, self.V0_V)

    @property
    def K_ext(self):
        dK = delta_K(self.E_keV, self.V0_V)
        return float(np.sqrt(self.K_int**2 - dK**2)) if self.accessible else np.nan

    @property
    def theta_ext(self):
        return float(np.arcsin(self.K_ext / self.k)) if self.accessible else np.nan

    @property
    def theta_int(self):
        dK = delta_K(self.E_keV, self.V0_V)
        k_int = np.sqrt(self.k**2 + dK**2)
        return float(np.arcsin(self.K_int / k_int))

    @property
    def theta_B_vacuum(self):
        s = self.order * self.lam / (2.0 * self.d_A)
        return float(np.arcsin(s)) if s <= 1 else np.nan


def specular_step_phase(h_A, theta_ext, E_keV):
    """Signed geometric step phase phi(upper) - phi(lower) = -2 h k sin(theta_ext)
    for the specular beam of a lattice-translation step of height h (exp(+ik.r))."""
    return -2.0 * np.asarray(h_A) * k_rad_per_A(E_keV) * np.sin(theta_ext)


def wrap_period(theta_ext, E_keV):
    """h_2pi = lambda / (2 sin theta_ext)."""
    return wavelength_A(E_keV) / (2.0 * np.sin(theta_ext))


def shadow_length(h_A, theta_ext):
    """Geometric shadow on the surface behind a transverse step: h / tan(theta)."""
    return np.asarray(h_A) / np.tan(theta_ext)


def wrap_to_pi(x):
    return -((-np.asarray(x, float) + np.pi) % TWO_PI - np.pi)
