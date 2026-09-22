"""Detection of the invisibility condition of a lattice-translation step.

Source map SM03, evidence DERIVED_HERE (C report sections 2.2-2.3; docs/03 section 2): if the
vacuum momentum transfer equals a bulk reciprocal-lattice vector g (cycles/A) and R is a lattice
translation, exp(2 pi i g.R) = 1 and the step is invisible. Check T16: for g = (2,-2,0)/a and the
Si(111) bilayer step R = (a/2)[1,0,1], g.R = 1 exactly (the inspected repository's formula, which
drops g_par.R_par, gives 4/3 instead). Near the condition the phase step is small and the height
cannot be quantified; the geometric-phase model must flag it.

For a vacuum momentum transfer q in rad/A (q = k_out - k_in), pass g = q / (2 pi).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class InvisibilityReport:
    """Result of detect_invisibility (source map SM03, evidence DERIVED_HERE)."""
    g_dot_R: float            # g.R in cycles (the step phase is -2 pi g.R)
    nearest_integer: int
    distance_cycles: float    # |g.R - nearest integer|
    invisible: bool           # distance_cycles <= tol_cycles


def detect_invisibility(g_cycles_per_A, R_A, *, tol_cycles: float) -> InvisibilityReport:
    """Report g.R and whether it is an integer within tol_cycles (required; e.g. the phase
    uncertainty divided by 2 pi). Source map SM03, evidence DERIVED_HERE; check T16."""
    if not (np.isfinite(tol_cycles) and tol_cycles >= 0.0):
        raise ValueError("tol_cycles must be finite and >= 0")
    gR = float(np.asarray(g_cycles_per_A, dtype=float) @ np.asarray(R_A, dtype=float))
    n = int(np.rint(gR))
    dist = abs(gR - n)
    return InvisibilityReport(g_dot_R=gR, nearest_integer=n, distance_cycles=float(dist),
                              invisible=bool(dist <= tol_cycles))
