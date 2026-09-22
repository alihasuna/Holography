"""Beam constants of the multislice engine: energy guard, wavelength, interaction constant.

Convention (docs/physics_conventions.md): exp(+i k.r); the transmission function of a slice is
exp(+i sigma V_p) with V_p the projected potential in V A, so a positive potential ADVANCES the
phase (the electron speeds up inside the crystal, refractive index > 1).

The interaction constant is DERIVED_HERE from the constants of reflection_holo.constants:

    sigma = 2 pi m_rel e lambda / h^2 = 2 pi (T + m_e c^2) lambda / (h c)^2      [rad / (V A)]

with T and m_e c^2 in eV, h c in eV A and lambda the relativistic wavelength in A
(reflection_holo.geometry.wavelength, SM01). It is cross-checked against abTEM's
abtem.core.energy.energy2sigma in tests/forward (ASE CODATA 2014 constants; 6e-9 relative, D3).
Consistency with refraction (SM04): 2 k sigma V0 = k_int^2 - k^2 to first order in e V0 / T
(the exact relativistic form adds (e V0)^2 / (h c / 2 pi)^2, 8.4e-6 relative at 12 V, 200 keV).
"""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV, HC_EV_M, M_E_C2_EV
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A

HC_EV_A = HC_EV_M * 1.0e10          # eV A


def require_beam_energy(energy_keV) -> float:
    """Return the beam energy after asserting that it is the supplied 200 keV (PROJECT_INPUT item 1,
    Ali 2026-09-22; 300 keV is never used). No default exists."""
    if energy_keV is None:
        raise ValueError("energy_keV is required (PROJECT_INPUT item 1)")
    E = float(energy_keV)
    if E != BEAM_ENERGY_SUPPLIED_KEV:
        raise ValueError(f"beam energy {energy_keV!r} keV refused: the beam energy is "
                         f"{BEAM_ENERGY_SUPPLIED_KEV:g} keV for every configuration "
                         f"(PROJECT_INPUT item 1)")
    return E


def interaction_constant_rad_per_VA(energy_keV: float) -> float:
    """Relativistic interaction constant sigma in rad/(V A); DERIVED_HERE (module docstring).

    0.00072884 rad/(V A) at 200 keV.
    """
    T = float(energy_keV) * 1.0e3
    if not np.isfinite(T) or T <= 0:
        raise ValueError(f"energy must be positive, got {energy_keV!r}")
    lam = wavelength_A(energy_keV)
    return float(2.0 * np.pi * (T + M_E_C2_EV) * lam / HC_EV_A**2)


def beam_constants(energy_keV: float) -> dict:
    """Wavelength (A), angular wavenumber k (rad/A) and sigma (rad/(V A)) after the energy guard."""
    E = require_beam_energy(energy_keV)
    return dict(energy_keV=E, wavelength_A=float(wavelength_A(E)), k_rad_per_A=float(k_ang_per_A(E)),
                sigma_rad_per_VA=interaction_constant_rad_per_VA(E),
                sigma_label="DERIVED_HERE: sigma = 2 pi (T + m_e c^2) lambda / (h c)^2, constants "
                            "of reflection_holo.constants (SM01)")
