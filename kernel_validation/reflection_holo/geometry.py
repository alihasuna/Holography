"""reflection_holo.geometry -- rung R1: lattice, frames, refraction, specular rods, guards.

Frame (CONTRACT): rows of frame(surface) are (x_beam, y, z_normal) in crystal cartesian;
x = beam azimuth, z = OUTWARD surface normal (vacuum at +z), y = z cross x (right-handed).
The direction of Surface.hkl is declared to be the outward normal. Relation to the
repo:physics_conventions.md frame for si111_cleaved_110azimuth (x_conv = normal, z_conv = beam):
x = z_conv, y = -y_conv, z = x_conv.

Refraction (non-negotiable convention): K_z,int^2 = K_z,ext^2 + dK^2 with
dK^2 = 2 m e V0 / hbar^2, m = gamma m0 (relativistic mass), i.e. dK^2 = 2 gamma (m0 c^2) V0/(hbar c)^2
(energies in eV, V0 in V). Equivalent to repo:physics_conventions.md
Delta = (k_int^2 - k^2)/k^2 = V0 (1 + T/mc^2) / (T (1 + T/2mc^2)) -- SECTION_READ; algebra DERIVED_HERE
and tested. The calculator uses the exact (T+U)(T+U+2E0) kinematics; the two differ by
U/(2T+2E0) = 8.4e-6 relative in dK^2 at 200 keV, far inside every calculator tolerance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import constants as C
from . import project_inputs as P


class GeometryError(ValueError):
    """Inconsistent surface/azimuth geometry."""


class ForbiddenReflectionError(ValueError):
    """A kinematically forbidden reflection (F_hkl = 0) was requested."""


# 8-atom diamond conventional cell, fractional coordinates (repo calculator DIAMOND_BASIS).
DIAMOND_BASIS = np.array([
    [0.00, 0.00, 0.00], [0.50, 0.50, 0.00], [0.50, 0.00, 0.50], [0.00, 0.50, 0.50],
    [0.25, 0.25, 0.25], [0.75, 0.75, 0.25], [0.75, 0.25, 0.75], [0.25, 0.75, 0.75]])

_IPOW = (1.0 + 0j, 1j, -1.0 + 0j, -1j)


def _a(a):
    return C.A_SI.value if a is None else float(a)


# ------------------------------------------------------------------------- lattice
def lattice_vectors(a: float | None = None) -> np.ndarray:
    """Rows a_1, a_2, a_3 of the cubic conventional cell (A). ASSUMPTION a = A_SI."""
    return _a(a) * np.eye(3)


def reciprocal_vectors(a: float | None = None) -> np.ndarray:
    """Rows b_j with a_i . b_j = 2 pi delta_ij (rad/A).
    SECTION_READ: card:peng_ch13 [p.8] (a_i . b_j = 2 pi delta_ij); conventions G = 2 pi g."""
    return 2.0 * math.pi / _a(a) * np.eye(3)


def reciprocal_vector(hkl, a: float | None = None) -> np.ndarray:
    """G_hkl = h b1 + k b2 + l b3 in crystal cartesian, rad/A."""
    return np.asarray(hkl, float) @ reciprocal_vectors(a)


def d_spacing(hkl, a: float | None = None) -> float:
    """d_hkl = a / sqrt(h^2 + k^2 + l^2) (A)."""
    return _a(a) / float(np.linalg.norm(np.asarray(hkl, float)))


# ------------------------------------------------------------------------- structure factor
def structure_factor_si(h, k, l) -> complex:
    """Diamond structure factor with unit atomic amplitude, F = sum_j exp(+2 pi i g.r_j).

    Sign convention SECTION_READ (repo:physics_conventions.md 'Structure factor').
    Closed form DERIVED_HERE: F = F_fcc (1 + i^(h+k+l)), F_fcc = 4 if h, k, l have equal parity
    else 0. Computed in exact integer arithmetic so forbidden reflections return exactly 0j.
    REPRODUCED: calculator sec.2 table (|F| = 4 sqrt2, 8, 0).
    """
    h, k, l = int(h), int(k), int(l)
    if not (h % 2 == k % 2 == l % 2):
        return 0j
    return 4.0 * (1.0 + _IPOW[(h + k + l) % 4])


def structure_factor_si_direct(h, k, l) -> complex:
    """Explicit 8-atom sum (floating point), used only to cross-check the closed form."""
    g = np.array([h, k, l], float)
    return complex(np.sum(np.exp(2j * np.pi * (DIAMOND_BASIS @ g))))


def is_forbidden(h, k, l) -> bool:
    """True iff F_hkl == 0 exactly (kinematically forbidden for spherical atoms)."""
    return structure_factor_si(h, k, l) == 0


def require_allowed(hkl) -> None:
    """Forbidden-reflection guard (spec 4.1): raises ForbiddenReflectionError."""
    if is_forbidden(*hkl):
        raise ForbiddenReflectionError(
            f"{tuple(int(v) for v in hkl)} is kinematically forbidden (F_hkl = 0 for the diamond "
            f"structure); pass allow_forbidden=True only to reproduce legacy numbers")


# ------------------------------------------------------------------------- frames
@dataclass
class Surface:
    hkl: tuple[int, int, int]        # outward surface normal direction [hkl] (cubic)
    azimuth: tuple[int, int, int]    # beam azimuth [uvw], must lie in the surface plane


def frame(surface: Surface) -> np.ndarray:
    """3x3 rows (x_beam, y, z_normal) in crystal cartesian; asserts orthonormal, right-handed.

    In the cubic system [hkl] is normal to (hkl) (repo:physics_conventions.md), so the azimuth
    must satisfy hkl . uvw = 0; otherwise GeometryError (e.g. the README '(1,1,-1) facet' with a
    [110] beam: [1,1,-1].[1,1,0] = 2).
    """
    n = np.asarray(surface.hkl, float)
    u = np.asarray(surface.azimuth, float)
    if np.linalg.norm(n) == 0 or np.linalg.norm(u) == 0:
        raise GeometryError("zero surface normal or azimuth")
    if abs(float(n @ u)) > 1e-12:
        raise GeometryError(f"azimuth {tuple(surface.azimuth)} is not in the surface plane "
                            f"{tuple(surface.hkl)}: n.u = {float(n @ u):g}")
    z = n / np.linalg.norm(n)
    x = u / np.linalg.norm(u)
    y = np.cross(z, x)
    y = y / np.linalg.norm(y)
    F = np.vstack([x, y, z])
    assert np.allclose(F @ F.T, np.eye(3), atol=1e-12), "frame not orthonormal"
    assert abs(np.linalg.det(F) - 1.0) < 1e-12, "frame not right-handed"
    return F


def to_slab(v_crystal, surface: Surface) -> np.ndarray:
    """Components of a crystal-cartesian vector in the (x_beam, y, z_normal) frame."""
    return frame(surface) @ np.asarray(v_crystal, float)


# ------------------------------------------------------------------------- refraction
def delta_refraction(E_eV: float, V0: float) -> float:
    """Delta = (k_int^2 - k^2)/k^2 = V0 (1 + T/mc^2) / (T (1 + T/(2 mc^2))), T in eV, V0 in V.
    SECTION_READ: repo:physics_conventions.md 'Refraction'. At 200 keV, 12 V: 6.98e-5."""
    T = float(E_eV)
    E0 = C.MEC2_EV.value
    return float(V0) * (1.0 + T / E0) / (T * (1.0 + T / (2.0 * E0)))


def delta_K(E_eV: float, V0: float) -> float:
    """dK = sqrt(2 gamma m0 e V0)/hbar in rad/A: dK^2 = 2 gamma (m0 c^2)[eV] V0[V] / (hbar c)^2.
    SECTION_READ (task/convention form K_z,int^2 = K_z,vac^2 + 2 m e V0/hbar^2, m relativistic);
    equals k^2 * delta_refraction (DERIVED_HERE, tested)."""
    if V0 < 0:
        raise ValueError("V0 must be >= 0 V")
    return math.sqrt(2.0 * C.gamma(E_eV) * C.MEC2_EV.value * float(V0)) / C.HBARC_EV_A


def internal_wavenumber(E_eV: float, V0: float) -> float:
    """k_int = sqrt(k^2 + dK^2), rad/A. DERIVED_HERE."""
    return math.hypot(C.wavenumber(E_eV), delta_K(E_eV, V0))


def refraction(theta_ext: float, E_eV: float, V0: float) -> float:
    """Internal glancing angle from the external one (surface-parallel k conserved).

    K_int = sqrt((k sin theta_ext)^2 + dK^2), sin theta_int = K_int / k_int; identical to
    sin^2 theta_int = (sin^2 theta_ext + Delta)/(1 + Delta) [repo:physics_conventions.md].
    Every externally incident beam enters: theta_int >= theta_c.
    """
    k = C.wavenumber(E_eV)
    Kz = math.hypot(k * math.sin(float(theta_ext)), delta_K(E_eV, V0))
    return math.asin(min(1.0, Kz / internal_wavenumber(E_eV, V0)))


def external_angle(theta_int: float, E_eV: float, V0: float) -> float:
    """External glancing angle of an internal beam; nan if theta_int < theta_c (cannot escape)."""
    Kz = internal_wavenumber(E_eV, V0) * math.sin(float(theta_int))
    arg = Kz ** 2 - delta_K(E_eV, V0) ** 2
    if arg < 0:
        return float("nan")
    return math.asin(math.sqrt(arg) / C.wavenumber(E_eV))


def critical_angle(E_eV: float, V0: float) -> float:
    """INTERNAL escape angle theta_c, sin theta_c = dK / k_int [repo:physics_conventions.md].
    200 keV, 12 V: 8.356 mrad (calculator T5 uses sin = dK/k; difference 3.5e-5 relative)."""
    return math.asin(delta_K(E_eV, V0) / internal_wavenumber(E_eV, V0))


def vacuum_bragg_angle(hkl, E_eV: float, a: float | None = None) -> float:
    """sin theta_B = |G| / (2k) = lambda / (2 d_hkl) (half scattering angle). DERIVED_HERE."""
    s = float(np.linalg.norm(reciprocal_vector(hkl, a))) / (2.0 * C.wavenumber(E_eV))
    return math.asin(s) if s <= 1.0 else float("nan")


# ------------------------------------------------------------------------- specular rod
def rod_primitive(surface: Surface) -> tuple[int, int, int]:
    """Smallest integer vector along the surface normal: (0,0,1) or (1,-1,1)."""
    h = [int(v) for v in surface.hkl]
    g = math.gcd(math.gcd(abs(h[0]), abs(h[1])), abs(h[2]))
    if g == 0:
        raise GeometryError("zero normal")
    return tuple(v // g for v in h)


def resolve_V0(V0: float | None, accept_assumptions: bool = False) -> float:
    """Explicit V0, else project_inputs 'V0_SI' (MISSING -> raises unless accepted)."""
    if V0 is not None:
        return float(V0)
    return float(P.get("V0_SI", accept_assumptions=accept_assumptions))


def rod_condition(surface: Surface, n: int, E_eV: float, V0: float, a: float | None = None,
                  allow_forbidden: bool = False) -> dict:
    """Order-n specular Bragg condition G = n * rod_primitive, satisfied by INTERNAL wavevectors.

    Premises (repo calculator 'SpecularCondition', DERIVED_HERE): 2 K_int = |G|; K_ext^2 =
    K_int^2 - dK^2; accessible iff K_int > dK (equivalently G.n_hat > 2 dK); h_2pi = pi/K_ext =
    lambda/(2 sin theta_ext); foreshortening 1/sin theta_ext = k/K_ext.
    Raises ForbiddenReflectionError for F = 0 unless allow_forbidden.
    """
    p = rod_primitive(surface)
    hkl = tuple(int(n) * v for v in p)
    F = structure_factor_si(*hkl)
    allowed = F != 0
    if not allowed and not allow_forbidden:
        require_allowed(hkl)
    k = C.wavenumber(E_eV)
    dK = delta_K(E_eV, V0)
    kint = math.hypot(k, dK)
    Gn = float(np.linalg.norm(reciprocal_vector(hkl, a)))
    K_int = 0.5 * Gn
    acc = K_int > dK
    K_ext = math.sqrt(K_int ** 2 - dK ** 2) if acc else float("nan")
    th_ext = math.asin(K_ext / k) if acc else float("nan")
    return {"n": int(n), "hkl": hkl, "F_abs": abs(F), "allowed": allowed,
            "d_spacing": d_spacing(hkl, a), "G_norm": Gn,
            "theta_B_vac": vacuum_bragg_angle(hkl, E_eV, a),
            "K_int": K_int, "theta_int": math.asin(min(1.0, K_int / kint)),
            "accessible": acc, "K_ext": K_ext, "theta_ext": th_ext,
            "h_2pi": (math.pi / K_ext) if acc else float("nan"),
            "foreshortening": (k / K_ext) if acc else float("nan")}


def specular_orders(surface: Surface, E_eV: float, nmax: int = 16, V0: float | None = None,
                    accept_assumptions: bool = False, a: float | None = None,
                    include_forbidden: bool = False) -> list[dict]:
    """All allowed rod orders n = 1..nmax (forbidden ones skipped unless include_forbidden).
    Keys include n, hkl, d_spacing, theta_int, theta_ext (refraction with V0), accessible.
    V0=None -> project_inputs 'V0_SI' (raises MissingProjectInput unless accepted)."""
    V = resolve_V0(V0, accept_assumptions)
    out = []
    for n in range(1, int(nmax) + 1):
        c = rod_condition(surface, n, E_eV, V, a, allow_forbidden=True)
        if c["allowed"] or include_forbidden:
            out.append(c)
    return out


def forbidden_rod_orders(surface: Surface, nmax: int = 16) -> list[tuple[int, int, int]]:
    """Rod orders refused by the guard (F = 0)."""
    p = rod_primitive(surface)
    return [tuple(n * v for v in p) for n in range(1, nmax + 1)
            if is_forbidden(*(n * v for v in p))]


def reflection_accessibility(hkl, surface: Surface, E_eV: float, V0: float,
                             a: float | None = None) -> dict:
    """Guard for non-specular reflections: G can connect two vacuum beams only if
    |G . n_hat| >= 2 dK [repo:physics_conventions.md 'Reflection accessibility']."""
    n_hat = frame(surface)[2]
    Gn = abs(float(reciprocal_vector(hkl, a) @ n_hat))
    tdk = 2.0 * delta_K(E_eV, V0)
    return {"G_dot_n": Gn, "two_dK": tdk, "accessible": Gn >= tdk}


# ------------------------------------------------------------------------- image geometry
def foreshortening(theta_ext: float) -> float:
    """Foreshortening factor along the beam, 1/sin(theta_ext) [repo:physics_conventions.md]."""
    return 1.0 / math.sin(float(theta_ext))


def shadow_length(h: float, theta_ext: float) -> float:
    """Shadow of a step of height h transverse to the beam: h / tan(theta_ext) (A)."""
    return float(h) / math.tan(float(theta_ext))


def wrap_period(theta_ext: float, E_eV: float) -> float:
    """Specular step-height wrap period h_2pi = lambda / (2 sin theta_ext) (A)."""
    return C.wavelength(E_eV) / (2.0 * math.sin(float(theta_ext)))


def step_phase(R_vec, k_in, k_out) -> float:
    """Signed step phase Delta_phi = phi(upper) - phi(lower) = -(k_out - k_in) . R  (rad).
    SECTION_READ: repo:physics_conventions.md 'Step phase' (exp(+i k.r)); all vectors in one
    frame, k in rad/A, R in A, R.n_hat = h (lower terrace -> upper terrace)."""
    return -float((np.asarray(k_out, float) - np.asarray(k_in, float)) @ np.asarray(R_vec, float))


def specular_step_phase(h: float, theta_ext: float, E_eV: float) -> float:
    """Specular case: Delta_phi = -(4 pi/lambda) h sin(theta_ext) = -2 h K_ext (signed, rad).
    SECTION_READ: repo:physics_conventions.md. Cf. card:osakabe1993 [p.4] '2 K_perp d'."""
    return -4.0 * math.pi / C.wavelength(E_eV) * float(h) * math.sin(float(theta_ext))


def wrap_to_pi(x):
    """Wrap to (-pi, pi]."""
    y = -((-np.asarray(x, float) + np.pi) % (2.0 * np.pi) - np.pi)
    return float(y) if np.ndim(y) == 0 else y


def max_tilt_step(h: float, theta_ext: float, E_eV: float) -> float:
    """Largest tilt step keeping the step-phase increment below pi:
    d|dphi|/dtheta = (4 pi h/lambda) cos theta  ->  dtheta < lambda / (4 h cos theta).
    DERIVED_HERE (repo calculator sec.7; repo item 3 uses the same derivative)."""
    return C.wavelength(E_eV) / (4.0 * float(h) * math.cos(float(theta_ext)))
