"""Diamond-cubic structure factor, selection rule, d-spacings, reciprocal vectors and the
forbidden-reflection guard.

Source map SM02: the selection rule "allowed iff all odd, or all even with h+k+l = 4n" is
DERIVED_HERE from the 8-atom basis (the general result is attributed to B02, De Graef,
METADATA_VERIFIED, not read). Ported from tools/reflection_step_phase_calculator.py section 2.

Conventions (docs/physics_conventions.md): F_hkl = sum_j f_j exp(+2 pi i (h x_j + k y_j + l z_j));
the crystallographic reciprocal vector g is in cycles/A with |g_hkl| = 1/d_hkl; G = 2 pi g in rad/A.
Reflections are written with their signs: the CFG-A specular rod is (n,-n,n), not (n,n,n).

The lattice parameter is a required argument everywhere (no default): the repository value
reflection_holo.constants.A_SI_A is an ASSUMPTION (model_assumptions B2) that the caller passes and
records explicitly.
"""
from __future__ import annotations

from math import gcd

import numpy as np

from reflection_holo.constants import DIAMOND_BASIS, TWO_PI
from reflection_holo.geometry.errors import ForbiddenReflectionError

# Forbidden reflections on the two specular rods named in docs/05 section 4.1 (SM02, DERIVED_HERE).
# They are consequences of diamond_allowed(); tests assert that the general rule reproduces them.
FORBIDDEN_ON_CFG_A_ROD = ((2, -2, 2), (6, -6, 6), (10, -10, 10))
FORBIDDEN_ON_CFG_B_ROD = ((0, 0, 2), (0, 0, 6), (0, 0, 10))


def _as_hkl(hkl) -> tuple[int, int, int]:
    arr = np.asarray(hkl)
    if arr.shape != (3,):
        raise ValueError(f"Miller indices must be a 3-vector, got {hkl!r}")
    if not np.all(np.equal(np.mod(arr, 1), 0)):
        raise ValueError(f"Miller indices must be integers, got {hkl!r}")
    out = tuple(int(v) for v in arr)
    if out == (0, 0, 0):
        raise ValueError("(000) is not a reflection")
    return out


def structure_factor_over_f(hkl) -> complex:
    """F_hkl / f for the 8-atom diamond conventional cell (equal spherical f, no Debye-Waller factor).

    Direct sum F/f = sum_j exp(+2 pi i g.r_j) over reflection_holo.constants.DIAMOND_BASIS.
    Source map SM02, evidence DERIVED_HERE. Calculator checks T7 (|F(666)|/f = 0), T8
    (|F(444)|/f = 8) and T9 (|F(555)|/f = 4 sqrt 2).
    """
    g = np.asarray(_as_hkl(hkl), dtype=float)
    return complex(np.sum(np.exp(2j * np.pi * (DIAMOND_BASIS @ g))))


def diamond_allowed(hkl) -> bool:
    """Kinematic selection rule of diamond cubic: allowed iff (h, k, l all odd) or (all even and
    h + k + l = 4n).

    Source map SM02, evidence DERIVED_HERE (closed form |F| = 4 f |1 + i^(h+k+l)| x [same parity],
    cross-checked against structure_factor_over_f in tests/geometry). Spherical atoms: the weak
    bonding-charge intensity of (222)-type reflections is ignored.
    """
    h, k, l = _as_hkl(hkl)
    par = (h % 2, k % 2, l % 2)
    if par == (1, 1, 1):
        return True
    if par == (0, 0, 0):
        return (h + k + l) % 4 == 0
    return False


def require_allowed_target(hkl, *, allow_forbidden: bool = False) -> tuple[int, int, int]:
    """Forbidden-reflection guard: refuse a kinematically forbidden reflection as a TARGET.

    Raises ForbiddenReflectionError when F_hkl = 0 (e.g. (2,-2,2), (6,-6,6), (10,-10,10) on the
    CFG-A rod; (002), (006), (0,0,10) on the CFG-B rod). allow_forbidden=True exists only for the
    documented legacy checks of the calculator (T4, T6, T10, T14 evaluate the forbidden (6,-6,6)
    setting of the inspected repository); it must never be used to choose an operating condition.
    Source map SM02, evidence DERIVED_HERE; docs/05 section 4.1.
    """
    t = _as_hkl(hkl)
    if not allow_forbidden and not diamond_allowed(t):
        raise ForbiddenReflectionError(
            f"reflection {t} is kinematically forbidden in diamond-cubic Si (F_hkl = 0; source map "
            f"SM02) and cannot be used as a target; allowed specular choices are e.g. (4,-4,4), "
            f"(5,-5,5), (7,-7,7), (8,-8,8) on (1,-1,1) or (004), (008), (0,0,12) on (001)")
    return t


def d_spacing_A(hkl, a_A: float) -> float:
    """Interplanar spacing d_hkl = a / sqrt(h^2 + k^2 + l^2) for a cubic lattice, in A.

    The lattice parameter a_A is REQUIRED (no default). Source map SM02, evidence DERIVED_HERE.
    """
    h, k, l = _as_hkl(hkl)
    if not a_A > 0:
        raise ValueError(f"lattice parameter must be positive, got {a_A!r}")
    return float(a_A / np.sqrt(h * h + k * k + l * l))


def reciprocal_vector_cycles(hkl, a_A: float) -> np.ndarray:
    """Crystallographic reciprocal vector g_hkl = (h, k, l)/a in cycles/A, cubic crystal axes.

    |g_hkl| = 1/d_hkl. Rotate into a surface frame with SurfaceFrame.to_slab. Source map SM02,
    evidence DERIVED_HERE.
    """
    if not a_A > 0:
        raise ValueError(f"lattice parameter must be positive, got {a_A!r}")
    return np.asarray(_as_hkl(hkl), dtype=float) / float(a_A)


def reciprocal_vector_rad(hkl, a_A: float) -> np.ndarray:
    """G_hkl = 2 pi g_hkl in rad/A, cubic crystal axes (|G| = 2 pi / d_hkl).

    Source map SM02, evidence DERIVED_HERE.
    """
    return TWO_PI * reciprocal_vector_cycles(hkl, a_A)


def reciprocal_lattice_cycles(direct_vectors) -> np.ndarray:
    """Reciprocal basis b_j (rows, cycles/A) of a direct basis a_i (rows, A): a_i . b_j = delta_ij.

    General (any lattice), b = (A^-1)^T with A the matrix of direct vectors as rows. Raises for a
    singular basis. Source map SM02 (reciprocal lattice), evidence DERIVED_HERE (standard definition).
    """
    A = np.asarray(direct_vectors, dtype=float)
    if A.shape != (3, 3):
        raise ValueError("direct basis must be a 3x3 array of row vectors")
    if abs(np.linalg.det(A)) < 1e-12:
        raise ValueError("direct basis is singular")
    return np.linalg.inv(A).T


def rod_decomposition(hkl) -> tuple[tuple[int, int, int], int]:
    """Split a reflection into its primitive rod direction p and order n, hkl = n p (n = gcd > 0).

    Example: (6,-6,6) -> ((1,-1,1), 6); (0,0,8) -> ((0,0,1), 8). Source map SM02, evidence
    DERIVED_HERE.
    """
    h, k, l = _as_hkl(hkl)
    n = gcd(gcd(abs(h), abs(k)), abs(l))
    return (h // n, k // n, l // n), n


def rod_reflections(normal_hkl, n_max: int) -> list[dict]:
    """List the reflections n p (n = 1..n_max) of the specular rod along the primitive normal p,
    with their structure factor and selection-rule verdict (SM02, DERIVED_HERE)."""
    p, _ = rod_decomposition(normal_hkl)
    out = []
    for n in range(1, int(n_max) + 1):
        hkl = tuple(n * v for v in p)
        out.append(dict(hkl=hkl, allowed=diamond_allowed(hkl),
                        abs_F_over_f=abs(structure_factor_over_f(hkl))))
    return out
