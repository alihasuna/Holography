"""T-step-invisibility: geometry-only checks of the signed step phase, using the CONTRACT geometry functions.

Run with: pytest -q tests/test_step_invisibility.py

Convention (physics_conventions.md 'Step phase'): Delta_phi = -(k_out - k_in).R, where R maps the lower
terrace onto the upper one and R.n_hat = h; specular form -(4 pi/lambda) h sin(theta_ext).

V0 is PROJECT_INPUT item 20 (MISSING). It is taken from project_inputs.get('V0_SI',
accept_assumptions=True), which returns the documented ASSUMPTION 12.0 V and prints
'ASSUMPTION used: V0_SI = 12.0'. It is never read silently from constants.

Findings encoded here (DERIVED_HERE):
1. If k_out - k_in = G exactly (internal Bragg condition), a lattice-translation step gives
   Delta_phi = -G.R, which is in 2 pi Z for every specular order.
2. Si(001) single-layer a/4 step: Delta_phi/2pi = -l/4 at (00l): integer at the ALLOWED l = 4n,
   pi mod 2pi at the forbidden l = 2, 6, ...
3. The hologram measures the VACUUM phase, Delta_phi_vac = -2 K sin(theta_ext) h. At the vacuum Bragg
   angle of a rod order this is -G.R in 2 pi Z (invisible); at the refraction-shifted (internal Bragg)
   peak it differs from 2 pi n by -2h (K sin theta_ext - K_int sin theta_int) != 0 when V0 != 0.
"""
import math

import numpy as np
import pytest

from reflection_holo import constants as C
from reflection_holo import geometry as G
from reflection_holo import project_inputs as P

E = 200e3
A = float(C.A_SI.value)
V0 = float(P.get("V0_SI", accept_assumptions=True))     # ASSUMPTION 12.0 V (item 20), printed
K = 2 * math.pi / float(C.wavelength(E))
U0 = 2 * K * float(C.interaction_constant(E)) * V0
K_INT = math.sqrt(K * K + U0)
SURFACES = [G.Surface((0, 0, 1), (1, 1, 0)), G.Surface((1, -1, 1), (1, 1, 0))]


def _basis(surf):
    F = np.asarray(G.frame(surf), float)
    n = F[2]
    hkl = np.asarray(surf.hkl, float)
    assert abs(n @ hkl / np.linalg.norm(hkl) - 1) < 1e-12, "frame z row must be the outward normal +hkl"
    return F[0], n


def _orders(surf):
    out = []
    for o in G.specular_orders(surf, E, V0=V0):
        if o.get("forbidden", False):
            continue
        out.append(o)
    assert out, "specular_orders returned no allowed orders"
    return out


def _internal_k(Gvec, u):
    g = np.linalg.norm(Gvec)
    c = math.sqrt(1 - (g / (2 * K_INT)) ** 2)
    return K_INT * c * u - Gvec / 2, K_INT * c * u + Gvec / 2


@pytest.mark.parametrize("surf", SURFACES, ids=["Si001", "Si111"])
def test_lattice_step_is_2pi_multiple_internal(surf):
    """Invariant: G.R in 2 pi Z for a reciprocal vector G and a lattice translation R.
    R = m (a/2)(1,0,1) (fcc translation; normal component m a/2 for (001), m d111 for (1,-1,1)), m = 1..4,
    at every allowed specular order. Tolerance: |Delta_phi/2pi - round| < 1e-9."""
    u, _ = _basis(surf)
    for o in _orders(surf):
        Gv = 2 * math.pi / A * np.asarray(o["hkl"], float)
        k_in, k_out = _internal_k(Gv, u)
        for m in range(1, 5):
            R = m * A / 2 * np.array([1.0, 0.0, 1.0])
            x = G.step_phase(R, k_in, k_out) / (2 * math.pi)
            assert abs(x - round(x)) < 1e-9, (o["hkl"], m, x)
            assert abs(x + Gv @ R / (2 * math.pi)) < 1e-9          # sign: -(k_out - k_in).R


def test_single_layer_si001_step_and_forbidden_orders():
    """External fact: diamond (00l) is allowed iff l = 4n (conventions; geometry.is_forbidden).
    A single a/4 layer step R = (a/4)(1,1,1) gives Delta_phi/2pi = -l/4, which is an integer exactly at the
    allowed orders. Tolerance 1e-9."""
    u, _ = _basis(SURFACES[0])
    R = A / 4 * np.array([1.0, 1.0, 1.0])
    for l in range(1, 17):
        Gv = np.array([0.0, 0.0, 2 * math.pi * l / A])
        k_in, k_out = _internal_k(Gv, u)
        x = G.step_phase(R, k_in, k_out) / (2 * math.pi)
        assert abs(x + l / 4) < 1e-9
        assert G.is_forbidden(0, 0, l) == (abs(x - round(x)) > 1e-6)


@pytest.mark.parametrize("surf", SURFACES, ids=["Si001", "Si111"])
def test_vacuum_step_phase_formula_and_inverse(surf):
    """External fact: conventions specular step phase Delta_phi = -(4 pi/lambda) h sin(theta_ext), with
    inverse h = -Delta_phi lambda/(2 pi (2 sin theta_ext)). Tolerance 1e-12 rel."""
    u, n = _basis(surf)
    lam = float(C.wavelength(E))
    for o in _orders(surf):
        te = o["theta_ext"]
        if not np.isfinite(te):
            continue
        k_in = K * (math.cos(te) * u - math.sin(te) * n)
        k_out = K * (math.cos(te) * u + math.sin(te) * n)
        h = 3.1355
        dphi = G.step_phase(h * n + 0.7 * u, k_in, k_out)
        assert abs(dphi / (-(4 * math.pi / lam) * h * math.sin(te)) - 1) < 1e-12
        assert abs(-dphi * lam / (2 * math.pi * 2 * math.sin(te)) / h - 1) < 1e-12


def test_refraction_breaks_vacuum_invisibility_si001_008():
    """DERIVED_HERE finding 3, checked against the conventions refraction law.
    For h = a/4 at the (008) external peak, Delta_phi_vac - Delta_phi_int = -2h(K sin te - K_int sin ti).
    It agrees with the step_phase difference to 1e-9 rad and exceeds 0.5 rad for V0 = 12 V
    (ASSUMPTION value), so the measured step phase is NOT 2 pi n."""
    u, n = _basis(SURFACES[0])
    o = next(o for o in _orders(SURFACES[0]) if tuple(o["hkl"]) == (0, 0, 8))
    g = 2 * math.pi * 8 / A
    ti = math.asin(g / (2 * K_INT))
    te = math.acos(K_INT * math.cos(ti) / K)
    assert abs(G.refraction(te, E, V0) - ti) < 1e-9
    h = A / 4
    R = h * n
    k_in_v = K * (math.cos(te) * u - math.sin(te) * n)
    k_out_v = K * (math.cos(te) * u + math.sin(te) * n)
    k_in_i, k_out_i = _internal_k(g * n, u)
    d = G.step_phase(R, k_in_v, k_out_v) - G.step_phase(R, k_in_i, k_out_i)
    expect = -2 * h * (K * math.sin(te) - K_INT * math.sin(ti))
    assert abs(d - expect) < 1e-9
    assert abs(expect) > 0.5
    assert abs(o["theta_ext"] - te) < 1e-6 * te          # consistency with the geometry module


def test_v0_zero_limit_restores_invisibility():
    """Limit: with V0 = 0, refraction(theta, E, 0) = theta, and at the vacuum Bragg angle of (008)
    (2 K sin t = G = 2 pi 8/a) a step h = m a/2 gives Delta_phi = -G h = -2 pi * 4 m
    (conventions: Delta_phi = -(4 pi/lambda) h sin theta). Tolerance 1e-9.

    Integration fix: the earlier expectation -2 pi * 2 m used G h / 2 pi = 2 m; the correct value is
    (8/a)(m a/2) = 4 m (cf. test_geometry.test_step_invisibility_all_orders, which only asserts an
    integer)."""
    u, n = _basis(SURFACES[0])
    g = 2 * math.pi * 8 / A
    t = math.asin(g / (2 * K))
    assert abs(G.refraction(t, E, 0.0) - t) < 1e-12
    k_in = K * (math.cos(t) * u - math.sin(t) * n)
    k_out = K * (math.cos(t) * u + math.sin(t) * n)
    for m in range(1, 4):
        x = G.step_phase(m * A / 2 * n, k_in, k_out) / (2 * math.pi)
        assert abs(x + 4 * m) < 1e-9


def test_wrap_period_gives_minus_2pi():
    """External fact: conventions h_2pi = lambda/(2 sin theta_ext). A step of h_2pi has Delta_phi = -2 pi.
    Tolerance 1e-12 rel."""
    u, n = _basis(SURFACES[0])
    for te in (10e-3, 16e-3, 26e-3):
        h2 = G.wrap_period(te, E)
        assert abs(h2 / (float(C.wavelength(E)) / (2 * math.sin(te))) - 1) < 1e-12
        k_in = K * (math.cos(te) * u - math.sin(te) * n)
        k_out = K * (math.cos(te) * u + math.sin(te) * n)
        assert abs(G.step_phase(h2 * n, k_in, k_out) / (-2 * math.pi) - 1) < 1e-12


@pytest.mark.parametrize("surf", SURFACES, ids=["Si001", "Si111"])
def test_specular_orders_use_internal_bragg(surf):
    """External fact: Peng 5.75 with the crystal wavelength and 5.76 tangential conservation [p.29].
    The geometry's (theta_int, theta_ext) must satisfy 2 K_int sin(theta_int) = |G| with
    K_int = K cos(te)/cos(ti) (rel 1e-6). A failure means specular_orders used the vacuum wavelength
    inside the crystal."""
    for o in _orders(surf):
        te, ti = o["theta_ext"], o["theta_int"]
        if not (np.isfinite(te) and o.get("accessible", True)):
            continue
        k_int = K * math.cos(te) / math.cos(ti)
        g = 2 * math.pi / A * np.linalg.norm(o["hkl"])
        assert abs(2 * k_int * math.sin(ti) / g - 1) < 1e-6, o
