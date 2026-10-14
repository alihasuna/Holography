"""Physical constants and relativistic electron-optical quantities.

Provenance
----------
* h, c, e: exact by the SI-2019 definitions.
* m_e c^2 = 510998.95000 eV, epsilon_0 = 8.8541878128e-12 F/m and
  a_0 = 0.529177210903e-10 m: CODATA 2018 recommended values, the same set used by
  tools/reflection_step_phase_calculator.py (m_e c^2) and transcribed here for the
  other two (label: CODATA_2018, values transcribed, the CODATA page itself not
  re-read in this session).
* Formulas are DERIVED_HERE and identical to the reference calculator; the tests in
  tests/test_geometry.py assert agreement with it.
"""
from __future__ import annotations

import numpy as np

PLANCK_J_S = 6.626_070_15e-34          # SI-2019 exact
C_M_S = 299_792_458.0                  # SI-2019 exact
ELEM_CHARGE_C = 1.602_176_634e-19      # SI-2019 exact
M_E_C2_EV = 510_998.950_00             # CODATA 2018
EPSILON0_F_M = 8.854_187_8128e-12      # CODATA 2018
BOHR_RADIUS_A = 0.529_177_210_903      # CODATA 2018, in angstrom

HC_EV_M = PLANCK_J_S * C_M_S / ELEM_CHARGE_C
# e/(4 pi eps0) in V*A (Coulomb potential of an elementary charge at 1 A)
E_OVER_4PIEPS0_V_A = ELEM_CHARGE_C / (4.0 * np.pi * EPSILON0_F_M) * 1.0e10
# 2 pi a0 e: converts the electron scattering factor f_e(q) [A] into potential.
# V(r) = 2 pi a0 e * integral f_e(q) exp(2 pi i q.r) d^3q   (DERIVED_HERE from the
# first Born approximation with the rest mass; relativity enters through sigma).
TWO_PI_A0_E_V_A2 = 2.0 * np.pi * BOHR_RADIUS_A * E_OVER_4PIEPS0_V_A

TWO_PI = 2.0 * np.pi


def wavelength_A(E_keV):
    """Relativistic vacuum wavelength lambda = h c / sqrt(T (T + 2 m c^2)) in A."""
    T = np.asarray(E_keV, dtype=float) * 1.0e3
    return HC_EV_M / np.sqrt(T * (T + 2.0 * M_E_C2_EV)) * 1.0e10


def k_rad_per_A(E_keV):
    """Angular wavenumber 2 pi / lambda in rad/A."""
    return TWO_PI / wavelength_A(E_keV)


def interaction_constant(E_keV):
    """sigma = 2 pi m e lambda / h^2 with the relativistic mass, in rad/(V A).

    Written as sigma = (2 pi / (lambda U)) (m c^2 + e U) / (2 m c^2 + e U), U in V.
    DERIVED_HERE (forward-scattering limit of the relativistically corrected
    Schroedinger equation: sigma V = U(x)/(2k) with U = 2 m gamma e V / hbar^2).
    """
    U = float(E_keV) * 1.0e3
    lam = float(wavelength_A(E_keV))
    return TWO_PI / (lam * U) * (M_E_C2_EV + U) / (2.0 * M_E_C2_EV + U)


def E_eff_V(E_keV, V0_V):
    """Effective energy with (k_int^2 - k^2)/k^2 = V0/E_eff (exact, relativistic)."""
    T = float(E_keV) * 1.0e3
    return T * (T + 2.0 * M_E_C2_EV) / (2.0 * T + V0_V + 2.0 * M_E_C2_EV)


def refraction_delta(E_keV, V0_V):
    """Delta = (k_int^2 - k^2)/k^2 = V0/E_eff."""
    return V0_V / E_eff_V(E_keV, V0_V)


def U_of_V(E_keV, V_V):
    """Optical potential U = k_int^2 - k^2 in rad^2/A^2 for an electrostatic
    potential V (volts, may be complex: V + iW). Exact relativistic form for real V
    is k^2 V/E_eff(V); the first-order form U = 2 k sigma V used here (it also
    accepts complex V + iW) is smaller than it by the factor
    1/(1 + V/(2 (T + m c^2))), i.e. 1e-5 relative for V = 14 V at 200 keV."""
    k = float(k_rad_per_A(E_keV))
    return 2.0 * k * interaction_constant(E_keV) * np.asarray(V_V)
