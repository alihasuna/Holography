"""Relativistic electron wavelength, wavevector and Lorentz factor.

Source map SM01; evidence DERIVED_HERE from (pc)^2 = T (T + 2 m_e c^2) with the constants of
reflection_holo.constants (h, c, e exact SI-2019 definitions; m_e c^2 CODATA 2018, stated, not
fetched). Ported from tools/reflection_step_phase_calculator.py section 1.

Convention (docs/physics_conventions.md): the beam energy is the kinetic energy T, stored in keV and
converted to eV inside each formula; |k| = 2 pi / lambda is an ANGULAR wavevector in rad/A.
"""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import HC_EV_M, M_E_C2_EV, TWO_PI


def _kinetic_energy_eV(E_keV) -> np.ndarray:
    T = np.asarray(E_keV, dtype=float) * 1.0e3
    if np.any(~np.isfinite(T)) or np.any(T <= 0.0):
        raise ValueError(f"beam energy must be finite and positive (keV), got {E_keV!r}")
    return T


def wavelength_A(E_keV):
    """Relativistic vacuum de Broglie wavelength in A for a kinetic energy E_keV (keV).

    lambda = h c / sqrt(T (T + 2 m_e c^2)), exact (no expansion).
    Source map SM01, evidence DERIVED_HERE (constants: SI-2019 exact h, c, e; CODATA 2018 m_e c^2).
    At 200 keV: 0.02507934 A (physics_conventions; calculator check T1).
    """
    T = _kinetic_energy_eV(E_keV)
    pc = np.sqrt(T * (T + 2.0 * M_E_C2_EV))            # eV
    out = HC_EV_M / pc * 1.0e10                        # A
    return float(out) if np.ndim(out) == 0 else out


def k_ang_per_A(E_keV):
    """Angular wavevector magnitude |k| = 2 pi / lambda in rad/A.

    Source map SM01, evidence DERIVED_HERE. At 200 keV: 250.5323 rad/A (physics_conventions).
    """
    out = TWO_PI / np.asarray(wavelength_A(E_keV), dtype=float)
    return float(out) if np.ndim(out) == 0 else out


def gamma_lorentz(E_keV):
    """Lorentz factor gamma = 1 + T / (m_e c^2).

    Source map SM01, evidence DERIVED_HERE. At 200 keV: 1.391390 (calculator output section 1).
    """
    out = 1.0 + _kinetic_energy_eV(E_keV) / M_E_C2_EV
    return float(out) if np.ndim(out) == 0 else out


def beta_v_over_c(E_keV):
    """Speed ratio beta = v/c = sqrt(1 - 1/gamma^2).

    Source map SM01, evidence DERIVED_HERE. At 200 keV: 0.695314 (calculator output section 1).
    """
    g = np.asarray(gamma_lorentz(E_keV), dtype=float)
    out = np.sqrt(1.0 - 1.0 / g**2)
    return float(out) if np.ndim(out) == 0 else out
