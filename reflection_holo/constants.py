"""Physical constants and material parameters: the single source for the whole package.

Every value carries its evidence label (docs/physics_conventions.md, docs/model_assumptions.md).
Ported from tools/reflection_step_phase_calculator.py section 0 so that the same quantity carries the
same value everywhere; no other module may define these numbers.

Rule: library functions take material parameters that are PROJECT_INPUT (e.g. the mean inner
potential V0, PROJECT_INPUT item 20) as REQUIRED arguments without defaults. The repository's
ASSUMPTION values below may be passed explicitly by a caller that records the label; they are never
used implicitly.
"""
from __future__ import annotations

import numpy as np

# --- Fundamental constants (source map SM01) ----------------------------------------------------
PLANCK_J_S = 6.626_070_15e-34        # J s   SI-2019 exact definition
C_M_S = 299_792_458.0                # m/s   SI-2019 exact definition
ELEM_CHARGE_C = 1.602_176_634e-19    # C     SI-2019 exact definition
M_E_C2_EV = 510_998.950_00           # eV    CODATA 2018 recommended value (stated, not fetched)
HC_EV_M = PLANCK_J_S * C_M_S / ELEM_CHARGE_C   # eV m, derived from the three exact constants
TWO_PI = 2.0 * np.pi

# --- Beam energy ------------------------------------------------------------------------------
# PROJECT_INPUT item 1, supplied by Ali on 2026-09-22: 200 keV for all reflection holography work;
# 300 keV is never used. Configurations must state it; this constant is the value to assert against.
BEAM_ENERGY_SUPPLIED_KEV = 200.0

# --- Silicon ----------------------------------------------------------------------------------
# Lattice parameter at room temperature. ASSUMPTION (standard), model_assumptions B2; the value is the
# inspected repository's generator default (calculator A_SI_A).
A_SI_A = 5.4309                      # A

# Mean inner potential. ASSUMPTION, model_assumptions B1; the measured or sourced value is
# PROJECT_INPUT item 20. Never a function default: pass it explicitly and record the label.
V0_SI_ASSUMPTION_V = 12.0            # V

# Diamond-cubic 8-atom conventional basis, fractional coordinates (source map SM02).
DIAMOND_BASIS = np.array([
    [0.00, 0.00, 0.00], [0.50, 0.50, 0.00],
    [0.50, 0.00, 0.50], [0.00, 0.50, 0.50],
    [0.25, 0.25, 0.25], [0.75, 0.75, 0.25],
    [0.75, 0.25, 0.75], [0.25, 0.75, 0.75],
])
