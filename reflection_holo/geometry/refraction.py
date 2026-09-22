"""Refraction by the mean inner potential, relativistic.

Source map SM04; evidence DERIVED_HERE from conservation of the surface-parallel wavevector (the
textbook expressions of B07/B08 are not read). The mean inner potential V0 is a REQUIRED argument of
every function (no default): the repository value 12.0 V is an ASSUMPTION (model_assumptions B1) and
the measured or sourced value is PROJECT_INPUT item 20. Ported from
tools/reflection_step_phase_calculator.py section 3.

Conventions (docs/physics_conventions.md): theta is the GLANCING angle to the surface plane;
T (kinetic energy) in eV inside the formulas, beam energy stored in keV; V0 in V; the potential
energy of the electron inside the crystal is -e V0 < 0.

    k_int^2 = k^2 (1 + Delta),  Delta = (k_int^2 - k^2)/k^2 = V0 / E_eff,
    E_eff = T (T + 2 m_e c^2) / (2 T + e V0 + 2 m_e c^2)            (exact, calculator E_eff_V)
    sin^2(theta_int) = (sin^2(theta_ext) + Delta) / (1 + Delta)     (exact, K_par conserved)
    sin(theta_c) = dK / k_int,  dK = k sqrt(Delta)                   (INTERNAL escape angle)

docs/physics_conventions.md writes Delta = V0 (1 + T/m_e c^2) / (T (1 + T/(2 m_e c^2))); that is the
first-order expansion of the exact form in e V0 / T (relative difference 8e-6 at 200 keV and 12 V,
tested). The non-relativistic Delta = V0/T is 14 percent too small at 200 keV and is not provided.
"""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import M_E_C2_EV
from reflection_holo.geometry.errors import InaccessibleReflectionError
from reflection_holo.geometry.wavelength import k_ang_per_A


def _check_V0(V0_V) -> float:
    if V0_V is None:
        raise ValueError("V0_V (mean inner potential, PROJECT_INPUT item 20) is required; "
                         "pass the value explicitly and record its evidence label")
    V0 = float(V0_V)
    if not np.isfinite(V0) or V0 < 0.0:
        raise ValueError(f"mean inner potential must be finite and >= 0 V, got {V0_V!r}")
    return V0


def _T_eV(E_keV) -> float:
    T = float(E_keV) * 1.0e3
    if not np.isfinite(T) or T <= 0.0:
        raise ValueError(f"beam energy must be finite and positive (keV), got {E_keV!r}")
    return T


def effective_energy_V(E_keV: float, V0_V: float) -> float:
    """E_eff [V] defined by (k_int^2 - k^2)/k^2 = V0 / E_eff (exact, relativistic).

    E_eff = T (T + 2 m_e c^2) / (2 T + e V0 + 2 m_e c^2). Source map SM04, evidence DERIVED_HERE
    (calculator E_eff_V).
    """
    T = _T_eV(E_keV)
    U = _check_V0(V0_V)
    return T * (T + 2.0 * M_E_C2_EV) / (2.0 * T + U + 2.0 * M_E_C2_EV)


def refraction_delta(E_keV: float, V0_V: float) -> float:
    """Relativistic Delta = (k_int^2 - k^2)/k^2 = V0 / E_eff (exact form).

    6.98e-5 at 200 keV and V0 = 12 V (physics_conventions). Source map SM04, evidence DERIVED_HERE.
    """
    V0 = _check_V0(V0_V)
    return V0 / effective_energy_V(E_keV, V0)


def refraction_delta_first_order(E_keV: float, V0_V: float) -> float:
    """Delta = V0 (1 + T/m_e c^2) / (T (1 + T/(2 m_e c^2))), the form printed in
    docs/physics_conventions.md (first order in e V0 / T; 8e-6 relative to the exact form at
    200 keV, 12 V). Source map SM04, evidence DERIVED_HERE. Provided for cross-checking only.
    """
    T = _T_eV(E_keV)
    V0 = _check_V0(V0_V)
    return V0 * (1.0 + T / M_E_C2_EV) / (T * (1.0 + T / (2.0 * M_E_C2_EV)))


def delta_K_per_A(E_keV: float, V0_V: float) -> float:
    """Surface-normal wavevector boost dK = sqrt(k_int^2 - k^2) = k sqrt(Delta) in rad/A.

    Exactly K_int^2 = K_ext^2 + dK^2 for the normal components. Source map SM04 and SM06,
    evidence DERIVED_HERE.
    """
    return float(k_ang_per_A(E_keV) * np.sqrt(refraction_delta(E_keV, V0_V)))


def k_internal_per_A(E_keV: float, V0_V: float) -> float:
    """|k_int| = k sqrt(1 + Delta) in rad/A. Source map SM04, evidence DERIVED_HERE."""
    return float(k_ang_per_A(E_keV) * np.sqrt(1.0 + refraction_delta(E_keV, V0_V)))


def theta_c_rad(E_keV: float, V0_V: float) -> float:
    """INTERNAL escape (critical) glancing angle: sin(theta_c) = dK / k_int.

    Below theta_c a beam inside the crystal cannot escape into vacuum; every externally incident
    beam enters with theta_int >= theta_c (no total external reflection for V0 > 0). 8.356 mrad at
    200 keV, V0 = 12 V (calculator check T5; physics_conventions revision 2). Note: the calculator's
    theta_critical_rad uses dK / k and calls it an external angle; the two differ by 3.5e-5 relative
    (0.3 urad), well inside the T5 tolerance of 1e-3 mrad. Source map SM04, evidence DERIVED_HERE.
    """
    dK = delta_K_per_A(E_keV, V0_V)
    return float(np.arcsin(dK / k_internal_per_A(E_keV, V0_V)))


def theta_int_from_ext_rad(theta_ext_rad, E_keV: float, V0_V: float):
    """Internal glancing angle from the external one (surface-parallel wavevector conserved).

    sin^2(theta_int) = (sin^2(theta_ext) + Delta)/(1 + Delta). Accepts scalars or arrays of
    theta_ext >= 0 (radians). Source map SM04, evidence DERIVED_HERE (calculator
    theta_int_from_ext_rad).
    """
    th = np.asarray(theta_ext_rad, dtype=float)
    if np.any(th < 0.0) or np.any(th > np.pi / 2):
        raise ValueError("glancing angles must lie in [0, pi/2] rad")
    k = k_ang_per_A(E_keV)
    dK = delta_K_per_A(E_keV, V0_V)
    k_int = np.sqrt(k**2 + dK**2)
    K_int = np.sqrt((k * np.sin(th))**2 + dK**2)
    out = np.arcsin(np.clip(K_int / k_int, -1.0, 1.0))
    return float(out) if np.ndim(out) == 0 else out


def theta_ext_from_int_rad(theta_int_rad, E_keV: float, V0_V: float):
    """External glancing angle from the internal one (inverse of theta_int_from_ext_rad).

    sin^2(theta_ext) = (1 + Delta) sin^2(theta_int) - Delta. Raises InaccessibleReflectionError if
    theta_int < theta_c (the beam cannot escape into vacuum). Source map SM04, evidence DERIVED_HERE.
    """
    th = np.asarray(theta_int_rad, dtype=float)
    if np.any(th < 0.0) or np.any(th > np.pi / 2):
        raise ValueError("glancing angles must lie in [0, pi/2] rad")
    k = k_ang_per_A(E_keV)
    dK = delta_K_per_A(E_keV, V0_V)
    k_int = np.sqrt(k**2 + dK**2)
    arg = (k_int * np.sin(th))**2 - dK**2
    if np.any(arg < 0.0):
        tc = theta_c_rad(E_keV, V0_V)
        raise InaccessibleReflectionError(
            f"internal glancing angle below the escape angle theta_c = {tc * 1e3:.4f} mrad "
            f"(E = {E_keV} keV, V0 = {V0_V} V): the beam cannot leave the crystal")
    out = np.arcsin(np.clip(np.sqrt(arg) / k, -1.0, 1.0))
    return float(out) if np.ndim(out) == 0 else out
