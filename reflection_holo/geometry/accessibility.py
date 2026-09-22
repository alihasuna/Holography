"""Accessibility guard for (non-specular or specular) reflections in reflection geometry.

Source map SM06, evidence DERIVED_HERE (C report section 3.3, equation (3.5)): a bulk reflection G
can connect two vacuum-propagating beams only if G.n_hat >= 2 dK, dK = k sqrt(Delta) (refraction,
SM04). Both beams must reach the internal escape angle; the normal momentum transfer available is
G.n_hat. Example: (2,-2,0) off (1,-1,1) at 200 keV and V0 = 12 V has G.n_hat = 2.672 rad/A
< 2 dK = 4.187 rad/A and is refused (calculator check T15).

Sign: q = k_out - k_in has q.n_hat = k (sin theta_in + sin theta_out) > 0 with the OUTWARD normal,
so a G with a negative normal component cannot be excited in reflection; its negative may be.
"""
from __future__ import annotations

import numpy as np

from reflection_holo.geometry.errors import InaccessibleReflectionError
from reflection_holo.geometry.refraction import delta_K_per_A


def _unit_normal(n_hat) -> np.ndarray:
    n = np.asarray(n_hat, dtype=float)
    if n.shape != (3,) or abs(np.linalg.norm(n) - 1.0) > 1e-12:
        raise ValueError("n_hat must be a unit 3-vector (the outward normal, same axes as G)")
    return n


def accessibility_margin(G_rad_per_A, n_hat, *, E_keV: float, V0_V: float) -> float:
    """G.n_hat - 2 dK in rad/A (>= 0 means accessible). V0_V is required (PROJECT_INPUT item 20).

    Source map SM06, evidence DERIVED_HERE.
    """
    G = np.asarray(G_rad_per_A, dtype=float)
    return float(G @ _unit_normal(n_hat) - 2.0 * delta_K_per_A(E_keV, V0_V))


def is_accessible(G_rad_per_A, n_hat, *, E_keV: float, V0_V: float) -> bool:
    """True iff G.n_hat >= 2 dK (source map SM06, evidence DERIVED_HERE)."""
    return accessibility_margin(G_rad_per_A, n_hat, E_keV=E_keV, V0_V=V0_V) >= 0.0


def require_accessible(G_rad_per_A, n_hat, *, E_keV: float, V0_V: float, label: str = "G") -> None:
    """Refuse (InaccessibleReflectionError) a reflection with G.n_hat < 2 dK (SM06, DERIVED_HERE)."""
    G = np.asarray(G_rad_per_A, dtype=float)
    Gn = float(G @ _unit_normal(n_hat))
    two_dK = 2.0 * delta_K_per_A(E_keV, V0_V)
    if Gn < two_dK:
        raise InaccessibleReflectionError(
            f"reflection {label}: G.n_hat = {Gn:.6f} rad/A < 2 dK = {two_dK:.6f} rad/A at "
            f"E = {E_keV} keV, V0 = {V0_V} V; it cannot connect two vacuum beams in reflection "
            f"geometry (source map SM06)")
