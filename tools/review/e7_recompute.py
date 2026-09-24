#!/usr/bin/env python3
"""E7: independent recomputation for the review of P2's rung-2 reference (docs/agent_reports/
P2_rung2_reference.md) and of the proposed engine test R2-A.

Written by review agent E7 (2026-09-24) WITHOUT reading tools/physics_checks/rung2_reference.py; that
tool is imported only in section 9, as a black box, to compare numbers. Every number quoted in
docs/agent_reports/E7_rung2_review.md is printed here; the saved run is
tools/review/e7_recompute_output.txt.

Methods (all written here from the physics; conventions of docs/physics_conventions.md: exp(+i k.r),
x = outward normal, theta = external glancing angle, R referred to the truncation plane x_s):
  A  continued fractions of the three-term Bloch recurrence of the single-harmonic (Mathieu)
     potential, complex Newton iteration for the Bloch wavenumber kappa, matching at x_s;
  B  one-period transfer matrix by a 4th-order Magnus integrator (exact 2x2 exponentials, my own),
     Floquet eigenvector with |mu| < 1 (flux criterion on the real circle);
  C  finite crystal on an absorbing uniform substrate, transfer matrices upwards (r > 0 only).
The engine is used only in section 2 (its AtomicPotential on a flat Si(001) cell, the quantity under
test there) and section 8 (a stand-in continuum periodic potential class written HERE, run through
the unmodified engine to test the R2-A protocol; it is not the class E1 is writing).

Run:  venv/bin/python tools/review/e7_recompute.py [--sections 1,2,...]   (default: all)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np                                        # noqa: E402
from scipy import optimize, special                       # noqa: E402

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from reflection_holo.constants import A_SI_A, HC_EV_M, M_E_C2_EV   # noqa: E402

# ------------------------------------------------------------------------------------------------
# 1. beam constants from the three exact constants of reflection_holo.constants (own formulas)
# ------------------------------------------------------------------------------------------------
T_EV = 200.0e3                                   # PROJECT_INPUT item 1
HC_EV_A = HC_EV_M * 1e10                         # eV A
HBARC_EV_A = HC_EV_A / (2 * np.pi)
LAM = HC_EV_A / np.sqrt(T_EV * (T_EV + 2 * M_E_C2_EV))   # relativistic wavelength (A)
KV = 2 * np.pi / LAM                             # rad/A
# sigma = 2 pi m_rel e lambda / h^2 = 2 pi (T + m c^2) lambda / (h c)^2  [rad/(V A)]
SIG = 2 * np.pi * (T_EV + M_E_C2_EV) * LAM / HC_EV_A**2
A = A_SI_A
V0_ENGINE = 13.902843      # V: P2's value, checked in section 2 (engine MIP)
VG_ENGINE = 1.035742       # V: P2's value, checked in section 2 (engine V_008)
G8 = 8.0 / A               # cycles/A
TH_C = None                # set in section 3 (two-beam centre)


def hr(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


CHECKS = []


def check(name, got, want, tol, rel=False):
    err = abs(got - want) / (abs(want) if rel else 1.0)
    ok = bool(err <= tol)
    CHECKS.append((name, ok))
    print(f"   CHECK {'PASS' if ok else 'FAIL'}  {name}: got {got!r} want {want!r} err {err:.3e} "
          f"tol {tol:.1e}{' (relative)' if rel else ''}")
    return ok


# ------------------------------------------------------------------------------------------------
# Solvers
# ------------------------------------------------------------------------------------------------
def U_of(V):
    return 2.0 * KV * SIG * V


def R_from_L(L, K):
    """vacuum u = exp(-iK x') + R exp(+iK x'), x' = x - x_s; crystal log-derivative L at x_s."""
    return (L + 1j * K) / (1j * K - L)


def two_beam_kappa(K, U0c, Up, Um, G):
    """both two-beam roots kappa = G/2 +- delta (starting values for method A)."""
    q2 = K**2 + U0c
    eps = q2 - G**2 / 4
    s = np.sqrt(G**4 + 4 * eps * G**2 + 4 * Up * Um + 0j)
    d2 = 2 * (eps**2 - Up * Um) / ((2 * eps + G**2) + s)
    d = np.sqrt(d2 + 0j)
    return G / 2 + d, G / 2 - d


def _cf_parts(kap, K, U0c, Up, Um, G, M):
    D = lambda m: K**2 + U0c - (m * G - kap) ** 2          # noqa: E731
    rp = {M + 1: 0.0}
    for m in range(M, 1, -1):
        rp[m] = -Up / (D(m) + Um * rp[m + 1])
    rm = {-M - 1: 0.0}
    for m in range(-M, 0):
        rm[m] = -Um / (D(m) + Up * rm[m - 1])
    return D, rp, rm


def cf_F(kap, K, U0c, Up, Um, G, M):
    D, rp, rm = _cf_parts(kap, K, U0c, Up, Um, G, M)
    return (D(0) + Up * rm[-1]) * (D(1) + Um * rp[2]) - Up * Um


def cf_bloch(kap, K, U0c, Up, Um, G, M):
    D, rp, rm = _cf_parts(kap, K, U0c, Up, Um, G, M)
    c = {0: 1.0 + 0j}
    c[1] = -Up / (D(1) + Um * rp[2])
    for m in range(2, M + 1):
        c[m] = rp[m] * c[m - 1]
    for m in range(-1, -M - 1, -1):
        c[m] = rm[m] * c[m + 1]
    return c


def R_cf(K, V0, Vg, g, r, t=0.0, M=10, return_kappa=False):
    """Method A: exact R(K) at x_s for V = (1 + i r)(V0 + 2 Vg cos(2 pi g (x - x_s + t))) below x_s."""
    G = 2 * np.pi * g
    U0c = U_of(V0) * (1 + 1j * r)
    Ugc = U_of(Vg) * (1 + 1j * r)
    Up, Um = Ugc * np.exp(1j * G * t), Ugc * np.exp(-1j * G * t)
    best = []
    for k0 in two_beam_kappa(K, U0c, Up, Um, G):
        kap = complex(k0)
        for _ in range(60):
            h = 1e-7 * (1 + abs(kap))
            f0 = cf_F(kap, K, U0c, Up, Um, G, M)
            df = (cf_F(kap + h, K, U0c, Up, Um, G, M) - cf_F(kap - h, K, U0c, Up, Um, G, M)) / (2 * h)
            step = f0 / df
            kap -= step
            if abs(step) < 1e-15 * (1 + abs(kap)):
                break
        c = cf_bloch(kap, K, U0c, Up, Um, G, M)
        flux = sum(abs(v) ** 2 * (m * G - kap.real) for m, v in c.items())
        best.append((kap, c, flux))
    # physical: Im kappa > 0 (decay towards -x); on the real axis the one carrying flux towards -x
    tol = 1e-12 * G
    phys = [b for b in best if b[0].imag > tol]
    if not phys:
        phys = [b for b in best if abs(b[0].imag) <= tol and b[2] < 0]
    if len(phys) != 1:
        raise RuntimeError(f"root selection failed: {[(b[0], b[2]) for b in best]}")
    kap, c, _ = phys[0]
    u = sum(c.values())
    du = sum(1j * (m * G - kap) * v for m, v in c.items())
    R = R_from_L(du / u, K)
    return (R, kap) if return_kappa else R


def V_profile(xp, V0, harmonics, r):
    """crystal potential below x_s (xp = x - x_s <= 0); harmonics = [(g, Vg, t), ...]."""
    v = V0 + sum(2 * Vg * np.cos(2 * np.pi * g * (xp + t)) for g, Vg, t in harmonics)
    return v * (1 + 1j * r)


def magnus_P(K, x_lo, x_hi, wfun, n):
    """transfer matrix (u, u')(x_lo) -> (u, u')(x_hi) of u'' = -w(x) u, 4th-order Magnus, n steps.
    K may be an array; wfun(x) returns w for all K (broadcast)."""
    K = np.atleast_1d(np.asarray(K, complex))
    h = (x_hi - x_lo) / n
    c1, c2 = 0.5 - np.sqrt(3) / 6, 0.5 + np.sqrt(3) / 6
    P = np.zeros((len(K), 2, 2), complex)
    P[:, 0, 0] = P[:, 1, 1] = 1.0
    for i in range(n):
        x0 = x_lo + i * h
        w1, w2 = wfun(x0 + c1 * h), wfun(x0 + c2 * h)
        # A = [[0, 1], [-w, 0]]; [A2, A1] = A2 A1 - A1 A2 = [[w2 - w1, 0], [0, w1 - w2]]
        O = np.zeros_like(P)
        O[:, 0, 1] = h
        O[:, 1, 0] = -(h / 2) * (w1 + w2)
        cc = np.sqrt(3) * h**2 / 12
        O[:, 0, 0] += cc * (w2 - w1)
        O[:, 1, 1] += cc * (w1 - w2)
        mu2 = -(O[:, 0, 0] * O[:, 1, 1] - O[:, 0, 1] * O[:, 1, 0])
        mu = np.sqrt(mu2)
        small = np.abs(mu) < 1e-6
        ch = np.where(small, 1 + mu2 / 2 + mu2**2 / 24, np.cosh(mu))
        sh = np.where(small, 1 + mu2 / 6 + mu2**2 / 120, np.sinh(mu) / np.where(small, 1, mu))
        E = sh[:, None, None] * O
        E[:, 0, 0] += ch
        E[:, 1, 1] += ch
        P = E @ P
    return P


def period_matrix(K, V0, harmonics, r, d, n_sub):
    """(u, u')(x_s - d) -> (u, u')(x_s) through one period of the crystal potential."""
    Karr = np.atleast_1d(np.asarray(K, complex))
    wf = lambda x: Karr**2 + U_of(V_profile(x, V0, harmonics, r))   # noqa: E731
    return magnus_P(Karr, -d, 0.0, wf, n_sub)


def R_floquet(K, V0, harmonics, r, d, n_sub=256):
    """Method B: Floquet eigenvector of the downward one-period map with |mu| < 1."""
    Karr = np.atleast_1d(np.asarray(K, float))
    P = period_matrix(Karr, V0, harmonics, r, d, n_sub)
    out = np.empty(len(Karr), complex)
    for i, Kv in enumerate(Karr):
        Mdown = np.linalg.inv(P[i])
        mu, vec = np.linalg.eig(Mdown)
        a = np.abs(mu)
        if abs(a[0] - a[1]) > 1e-9:
            j = int(np.argmin(a))
        else:   # on the unit circle: the Floquet solution carrying flux towards -x
            fl = [np.imag(np.conj(vec[0, jj]) * vec[1, jj]) for jj in range(2)]
            j = int(np.argmin(fl))
        out[i] = R_from_L(vec[1, j] / vec[0, j], Kv)
    return out if np.ndim(K) else out[0]


def R_depth(K, V0, harmonics, r, d, n_periods, n_sub=256):
    """Method C: crystal of n_periods periods on a uniform substrate (1 + i r) V0 with a decaying
    wave below it; the (u, u') vector is carried upwards (r > 0)."""
    Karr = np.atleast_1d(np.asarray(K, float))
    P = period_matrix(Karr, V0, harmonics, r, d, n_sub)
    qs = np.sqrt(Karr**2 + U_of(V0) * (1 + 1j * r) + 0j)
    qs = np.where(qs.imag < 0, -qs, qs)
    y = np.stack([np.ones_like(qs), -1j * qs], axis=1)[:, :, None]
    for _ in range(n_periods):
        y = P @ y
        y /= np.abs(y[:, :1, :])
    L = y[:, 1, 0] / y[:, 0, 0]
    out = R_from_L(L, Karr)
    return out if np.ndim(K) else out[0]


def K_of(theta):
    return KV * np.sin(theta)


def theta_of_K(K):
    return np.arcsin(K / KV)


def R_cf_vec(K, V0, Vg, g, r, t=0.0, M=8, n_newton=40):
    """Method A vectorised over K (complex K allowed: analytic continuation, Im K^2 > 0 selects the
    decaying root). Same equations as R_cf."""
    K = np.atleast_1d(np.asarray(K, complex))
    G = 2 * np.pi * g
    U0c = U_of(V0) * (1 + 1j * r)
    Ugc = U_of(Vg) * (1 + 1j * r)
    Up, Um = Ugc * np.exp(1j * G * t), Ugc * np.exp(-1j * G * t)
    K2 = K**2

    def F(kap):
        D = lambda m: K2 + U0c - (m * G - kap) ** 2          # noqa: E731
        rp = 0.0
        for m in range(M, 1, -1):
            rp = -Up / (D(m) + Um * rp)
        rm = 0.0
        for m in range(-M, 0):
            rm = -Um / (D(m) + Up * rm)
        return (D(0) + Up * rm) * (D(1) + Um * rp) - Up * Um, rp, rm

    res = []
    for k0 in two_beam_kappa(K, U0c, Up, Um, G):
        kap = np.array(k0, complex)
        for _ in range(n_newton):
            h = 1e-7 * (1 + np.abs(kap))
            f0 = F(kap)[0]
            df = (F(kap + h)[0] - F(kap - h)[0]) / (2 * h)
            kap = kap - f0 / df
        # Bloch coefficients, u(0), u'(0), flux
        D = lambda m: K2 + U0c - (m * G - kap) ** 2          # noqa: E731
        rps = {M + 1: 0.0}
        for m in range(M, 1, -1):
            rps[m] = -Up / (D(m) + Um * rps[m + 1])
        rms = {-M - 1: 0.0}
        for m in range(-M, 0):
            rms[m] = -Um / (D(m) + Up * rms[m - 1])
        c = {0: np.ones_like(kap)}
        c[1] = -Up / (D(1) + Um * rps[2])
        for m in range(2, M + 1):
            c[m] = rps[m] * c[m - 1]
        for m in range(-1, -M - 1, -1):
            c[m] = rms[m] * c[m + 1]
        u = sum(c.values())
        du = sum(1j * (m * G - kap) * v for m, v in c.items())
        flux = sum(np.abs(v) ** 2 * (m * G - kap.real) for m, v in c.items())
        resid = np.abs(F(kap)[0])
        res.append((kap, du / u, flux, resid))
    (k1, L1, f1, e1), (k2, L2, f2, e2) = res
    tol = 1e-12 * G
    pick1 = np.where(np.abs(k1.imag - k2.imag) > tol, k1.imag > k2.imag, f1 < f2)
    L = np.where(pick1, L1, L2)
    kap = np.where(pick1, k1, k2)
    out = R_from_L(L, K)
    return out, kap, np.maximum(e1, e2)


def R_exact(theta, r, V0=None, Vg=None, t=0.0):
    V0 = V0_ENGINE if V0 is None else V0
    Vg = VG_ENGINE if Vg is None else Vg
    R, _, _ = R_cf_vec(K_of(np.atleast_1d(theta)), V0, Vg, G8, r, t)
    return R if np.ndim(theta) else R[0]


# --------------------------------------------------------------- two-beam closed forms (own)
def darwin_R(K, r, V0=None, Vg=None, t=0.0):
    """Darwin/TT amplitude: rho = c1/c0 of the two-beam Bloch wave with delta^2 dropped and the
    prefactors at q = G/2: (eps - G d)(eps + G d) = U+ U-, rho = -(eps - G d)/U-, Im(G d) > 0."""
    V0 = V0_ENGINE if V0 is None else V0
    Vg = VG_ENGINE if Vg is None else Vg
    K = np.asarray(K, complex)
    G = 2 * np.pi * G8
    U0c = U_of(V0) * (1 + 1j * r)
    Ugc = U_of(Vg) * (1 + 1j * r)
    Up, Um = Ugc * np.exp(1j * G * t), Ugc * np.exp(-1j * G * t)
    eps = K**2 + U0c - G**2 / 4
    Gd = np.sqrt(eps**2 - Up * Um + 0j)
    Gd = np.where(Gd.imag < 0, -Gd, Gd)
    # on the real axis (r = 0, outside the gap) Im(Gd) = 0: take the branch with |rho| < 1
    rho_a = -(eps - Gd) / Um
    rho_b = -(eps + Gd) / Um
    onaxis = np.abs(Gd.imag) < 1e-14
    return np.where(onaxis & (np.abs(rho_b) < np.abs(rho_a)), rho_b, rho_a)


def fresnel_rF(K, r, V0=None):
    V0 = V0_ENGINE if V0 is None else V0
    K = np.asarray(K, complex)
    q = np.sqrt(K**2 + U_of(V0) * (1 + 1j * r))
    return (K - q) / (K + q)


def darwin_refracted_R(K, r, V0=None, Vg=None, t=0.0):
    """Airy composition of the Fresnel step (vacuum -> mean medium) and the Darwin crystal at the
    same plane: R = rF + tF tF' RD / (1 - rF' RD) with rF' = -rF, tF tF' = 1 - rF^2."""
    rF = fresnel_rF(K, r, V0)
    RD = darwin_R(K, r, V0, Vg, t)
    return (rF + RD) / (1 + rF * RD)


def two_beam_matched_R(K, r, V0=None, Vg=None, t=0.0):
    """two plane waves {0, 1} with the exact two-beam quartic root and exact matching at x_s."""
    V0 = V0_ENGINE if V0 is None else V0
    Vg = VG_ENGINE if Vg is None else Vg
    K = np.atleast_1d(np.asarray(K, complex))
    G = 2 * np.pi * G8
    U0c = U_of(V0) * (1 + 1j * r)
    Ugc = U_of(Vg) * (1 + 1j * r)
    Up, Um = Ugc * np.exp(1j * G * t), Ugc * np.exp(-1j * G * t)
    out = []
    for kp in two_beam_kappa(K, U0c, Up, Um, G):
        c1 = -Up / (K**2 + U0c - (G - kp) ** 2)
        L = 1j * (-kp + (G - kp) * c1) / (1 + c1)
        flux = -kp.real + (G - kp.real) * np.abs(c1) ** 2
        out.append((kp, R_from_L(L, K), flux))
    (k1, R1, f1), (k2, R2, f2) = out
    pick1 = np.where(np.abs(k1.imag - k2.imag) > 1e-12 * G, k1.imag > k2.imag, f1 < f2)
    return np.where(pick1, R1, R2)


# ================================================================================================
# report sections
# ================================================================================================
P2_CENTRE_MRAD = 16.13477          # P2's two-beam centre (report 6.2), checked in section 3


def sec1():
    hr("1. Beam constants (own formulas from the SI-2019 constants of reflection_holo.constants)")
    print(f"lambda = {LAM:.10f} A, k = {KV:.7f} rad/A, sigma = {SIG:.9e} rad/(V A)")
    print(f"2 k sigma = {2 * KV * SIG:.8f} rad^2/(A^2 V) (U = 2 k sigma V)")
    # Klein-Gordon check of 2 k sigma = 2 E_tot / (hbar c)^2 (per volt, e V in eV)
    print(f"2 E_tot/(hbar c)^2 = {2 * (T_EV + M_E_C2_EV) / HBARC_EV_A**2:.8f} (same quantity)")
    check("lambda vs physics_conventions 0.02507934 A", LAM, 0.02507934, 5e-9)
    check("k vs physics_conventions 250.5323 rad/A", KV, 250.5323, 5e-5)
    check("sigma vs P2 7.288401e-4", SIG, 7.288401e-4, 5e-10)
    check("2 k sigma = 2 E_tot/(hbar c)^2", 2 * KV * SIG, 2 * (T_EV + M_E_C2_EV) / HBARC_EV_A**2,
          1e-12, rel=True)


# ---------------------------------------------------------------------------- section 2
H2PIM0E = 2 * np.pi * HBARC_EV_A**2 / M_E_C2_EV      # h^2/(2 pi m0 e) in V A^2


def kirkland_fe_table():
    """Si parameters of Kirkland's parameterisation as stored in abTEM 1.0.10's kirkland.json
    (rows a_i, b_i, c_i, d_i); only the DATA are read, the formula is written here."""
    import json
    from abtem import parametrizations as ap
    d = json.load(open(os.path.join(os.path.dirname(ap.__file__), "data", "kirkland.json")))
    return np.array(d["Si"], float)


def kirkland_fe(q, tab):
    """f_e(q) = sum a_i/(q^2 + b_i) + sum c_i exp(-d_i q^2), q in 1/A (|g|), f_e in A."""
    q2 = np.asarray(q, float) ** 2
    a, b, c, d = tab
    return sum(a[i] / (q2 + b[i]) for i in range(3)) + sum(c[i] * np.exp(-d[i] * q2)
                                                            for i in range(3))


def Vl_kirkland(l, tab):
    """V_(0,0,l) of bulk diamond Si for l = 4n: 8 atoms in phase, V_l = 8 (h^2/(2 pi m0 e)) f_e / a^3."""
    return 8.0 * H2PIM0E * kirkland_fe(l / A, tab) / A**3


def sec2():
    hr("2. Engine potential: V0 and V_(0,0,l) (own Kirkland formula; engine scattering factor; "
       "engine-realised laterally averaged potential of a flat [100] Si(001) cell, DFT)")
    tab = kirkland_fe_table()
    print(f"h^2/(2 pi m0 e) = {H2PIM0E:.6f} V A^2; a^3 = {A**3:.6f} A^3")
    print(f"f_e(0) = {kirkland_fe(0.0, tab):.8f} A; f_e(8/a) = {kirkland_fe(8 / A, tab):.8f} A")
    ls = [0, 4, 8, 12, 16, 20, 24]
    own = {l: Vl_kirkland(l, tab) for l in ls}
    from reflection_holo.constants import A_SI_A as _a  # noqa: F401
    from reflection_holo.forward.cell import build_reflection_cell
    from reflection_holo.forward.multislice import (AtomicPotential, PhysicalAbsorption,
                                                    make_grid)
    from reflection_holo.forward.multislice.backend import get_backend
    from reflection_holo.structure import Staircase, build_si001_terraces
    st = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(1,),
                   boundary_step_layers=0)
    q = A / 4
    s = build_si001_terraces(azimuth_uvw=(1, 0, 0),
                             azimuth_label="TEST_ONLY: E7 review, flat [100] strip",
                             staircase=st, edge_periods=1, substrate_layers=45,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A,
                             lattice_parameter_label="ASSUMPTION B2")
    cell = build_reflection_cell(s, vacuum_above_A=8 * q, depth_below_A=40 * q,
                                 bulk_absorber_A=2 * q, top_absorber_A=2 * q,
                                 entrance_vacuum_z_A=q)
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(
                              model="proportional", ratio=0.0,
                              label="TEST_ONLY: E7 review, real potential only"),
                          frozen_phonons=None, static_lattice_label="TEST_ONLY: E7 review")
    print(f"engine MIP (8 F(0)/a^3) = {pot.mean_inner_potential_V():.7f} V")
    eng = {l: 8.0 * pot.scattering_factor(14, np.array([(l / A) ** 2]))[0] / A**3 for l in ls}
    be = get_backend("numpy", "complex128", 1)
    res = {}
    for m in (64, 128):
        nq = int(round(cell.extent_x_A / q))
        assert abs(cell.extent_x_A - nq * q) < 1e-9
        grid = make_grid(cell, nx=nq * m, ny=16)
        n_sl = int(round(cell.length_z_A / q))
        rl = pot.realise(grid=grid, dz_A=q, n_slices=n_sl, backend=be, rng=None)
        Vp = sum(np.asarray(rl.projected(i)).real for i in range(n_sl))
        Vx = Vp.mean(axis=1) / A                    # lateral average over y and one period in z
        xs = cell.surface_x_A
        # window: an integer number of layer periods starting at an atomic plane, >= 8 q from both ends
        j0 = int(round((xs - 30 * q) / grid.dx_A))
        nw = 20 * m
        w = Vx[j0:j0 + nw]
        xw = grid.x_A()[j0:j0 + nw]
        assert abs((xw[0] - (xs - 30 * q))) < 1e-9
        F = np.fft.fft(w) / nw
        res[m] = {"V0": F[0].real, **{l: F[(l // 4) * 20] for l in ls if l}}
        print(f"engine-realised lateral average, dx = a/{4 * m} = {grid.dx_A:.6f} A, window 20 layer "
              f"periods from x_s - 30 a/4: V0 = {F[0].real:.7f} V")
        for l in ls[1:]:
            c = F[(l // 4) * 20]
            print(f"   (0,0,{l:2d}) f = {l / A:.5f} 1/A: DFT {c.real:.7f} V (imag {c.imag:+.1e} V); "
                  f"engine 8F/a^3 {eng[l]:.7f} V; own Kirkland formula {own[l]:.7f} V")
    print(f"own Kirkland formula: V0 = {own[0]:.7f} V, V_008 = {own[8]:.7f} V")
    check("own V0 vs engine MIP", own[0], pot.mean_inner_potential_V(), 1e-6)
    check("own V_008 vs engine 8F/a^3", own[8], eng[8], 1e-7)
    check("engine-realised V_008 (dx a/512) vs P2 1.035742", res[128][8].real, VG_ENGINE, 1e-6)
    check("engine-realised V0 (dx a/512) vs P2 13.902843", res[128]["V0"], V0_ENGINE, 1e-6)
    check("V_008 vs H2/H5 1.036 V (rounded)", own[8], 1.036, 5e-4)
    check("V0 vs IAM MIP 13.903 V (rounded)", own[0], 13.903, 5e-4)
    return own


# ---------------------------------------------------------------------------- section 3
def band_edges(V0, harmonics, d, tr_target, K_lo, K_hi, n_sub=512):
    f = lambda K: (np.trace(period_matrix(K, V0, harmonics, 0.0, d, n_sub)[0]).real  # noqa: E731
                   - tr_target)
    return optimize.brentq(f, K_lo, K_hi, xtol=1e-14, rtol=1e-15)


def sec3(own):
    global TH_C
    hr("3. Plateau parameters of (0,0,8) (r = 0), exact band edges")
    G = 2 * np.pi * G8
    U0, Ug = U_of(V0_ENGINE), U_of(VG_ENGINE)
    Kc = np.sqrt(G**2 / 4 - U0)
    TH_C = theta_of_K(Kc)
    th_int = np.arccos(np.sqrt(KV**2 - Kc**2) / np.sqrt(KV**2 + U0))   # internal glancing angle
    print(f"G = {G:.6f} rad/A, d = a/8 = {1 / G8:.6f} A, U_0 = {U0:.6f}, |U_g| = {Ug:.6f} rad^2/A^2")
    print(f"two-beam centre K_c = {Kc:.6f} rad/A, theta_ext = {1e3 * TH_C:.5f} mrad, "
          f"theta_int = {1e3 * th_int:.5f} mrad")
    check("centre vs P2 16.13477 mrad", 1e3 * TH_C, P2_CENTRE_MRAD, 5e-6)
    t_lo, t_hi = theta_of_K(np.sqrt(Kc**2 - Ug)), theta_of_K(np.sqrt(Kc**2 + Ug))
    print(f"two-beam edges {1e3 * t_lo:.5f} to {1e3 * t_hi:.5f} mrad, width {1e6 * (t_hi - t_lo):.2f} urad")
    d8 = 1 / G8
    h1 = [(G8, VG_ENGINE, 0.0)]
    K_lo = band_edges(V0_ENGINE, h1, d8, -2.0, np.sqrt(Kc**2 - 1.2 * Ug), Kc)
    K_hi = band_edges(V0_ENGINE, h1, d8, -2.0, Kc, np.sqrt(Kc**2 + 1.2 * Ug))
    e_lo, e_hi = theta_of_K(K_lo), theta_of_K(K_hi)
    print(f"EXACT gap (single harmonic, tr M = -2): {1e3 * e_lo:.5f} to {1e3 * e_hi:.5f} mrad, width "
          f"{1e6 * (e_hi - e_lo):.3f} urad, midpoint {1e3 * (e_lo + e_hi) / 2:.5f} mrad; shifts vs "
          f"two-beam {1e6 * (e_lo - t_lo):+.3f} / {1e6 * (e_hi - t_hi):+.3f} urad")
    dK2 = -Ug**2 / (2 * G**2)
    print(f"Mathieu second-order edge shift -U_g^2/(2 G^2) = {dK2:.4e} rad^2/A^2 = "
          f"{1e6 * dK2 / (2 * Kc * KV * np.cos(TH_C)):+.3f} urad (both edges)")
    check("exact low edge vs P2 15.94648 mrad", 1e3 * e_lo, 15.94648, 6e-6)
    check("exact high edge vs P2 16.32008 mrad", 1e3 * e_hi, 16.32008, 6e-6)
    # full laterally averaged layer potential: harmonics (0,0,4n), n = 1..12, period a/4
    hf = [(4 * n / A, Vl_kirkland(4 * n, kirkland_fe_table()), 0.0) for n in range(1, 13)]
    d4 = A / 4
    Kf_lo = band_edges(V0_ENGINE, hf, d4, 2.0, np.sqrt(Kc**2 - 1.5 * Ug), Kc)
    Kf_hi = band_edges(V0_ENGINE, hf, d4, 2.0, Kc, np.sqrt(Kc**2 + 1.5 * Ug))
    f_lo, f_hi = theta_of_K(Kf_lo), theta_of_K(Kf_hi)
    print(f"EXACT gap, full layer potential (V_004..V_048, tr M = +2 over a/4): {1e3 * f_lo:.5f} to "
          f"{1e3 * f_hi:.5f} mrad, width {1e6 * (f_hi - f_lo):.3f} urad ({100 * ((f_hi - f_lo) / (e_hi - e_lo) - 1):+.1f} %), "
          f"midpoint shift {1e6 * ((f_lo + f_hi) - (e_lo + e_hi)) / 2:+.2f} urad")
    print(f"extinction depth G/|U_g| = {G / Ug:.3f} A; kc = sigma V_g = {SIG * VG_ENGINE:.6e} rad/A, "
          f"1/kc = {1 / (SIG * VG_ENGINE):.1f} A, xi_g = pi/kc = {np.pi / (SIG * VG_ENGINE):.1f} A")
    print(f"phase slope at the centre K_c/(sigma V_g) = {Kc / (SIG * VG_ENGINE) * 1e-3:.4f} rad/mrad; "
          f"1/V_g = {1 / VG_ENGINE:.4f} rad/V")
    return dict(Kc=Kc, e_lo=e_lo, e_hi=e_hi, hf=hf, f_lo=f_lo, f_hi=f_hi)


# ---------------------------------------------------------------------------- section 4
# P2 report section 6.3, columns "ex" (|R|, arg R) at eta = -3..3 (quoted to compare)
P2_EX = {
    0.0: [(0.10099, 0.0), (0.20165, 0.0), (0.32159, 0.0), (1.0, 0.0762), (1.0, 0.5207),
          (1.0, 1.1722), (1.0, 1.7080), (1.0, 2.2088), (1.0, 2.7497), (0.94342, np.pi),
          (0.43592, np.pi), (0.32690, np.pi), (0.23263, np.pi)],
    0.05: [(0.09949, 0.4651), (0.18661, 0.5665), (0.26631, 0.7042), (0.37881, 0.9693),
           (0.40233, 1.0399), (0.48204, 1.3547), (0.53532, 1.7627), (0.53497, 2.1636),
           (0.48919, 2.4676), (0.47167, 2.5353), (0.37711, 2.7829), (0.30632, 2.9101),
           (0.22725, 3.0251)],
    0.1: [(0.09611, 0.8888), (0.16092, 1.0177), (0.20675, 1.1544), (0.25860, 1.3508),
          (0.26890, 1.3970), (0.30648, 1.5991), (0.33836, 1.8755), (0.34655, 2.1544),
          (0.33531, 2.3614), (0.33045, 2.4089), (0.29920, 2.6125), (0.26579, 2.7585),
          (0.21364, 2.9306)]}
ETAS = np.array([-3, -2, -1.5, -1, -0.9, -0.5, 0, 0.5, 0.9, 1, 1.5, 2, 3.0])


def K_of_eta(eta):
    G = 2 * np.pi * G8
    Kc2 = G**2 / 4 - U_of(V0_ENGINE)
    return np.sqrt(Kc2 + np.asarray(eta) * U_of(VG_ENGINE))


def wrapd(a):
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


def sec4(p3):
    hr("4. Exact R(theta) at x_s (cosine maximum at x_s): methods A, B, C; P2's table")
    K = K_of_eta(ETAS)
    worst = 0.0
    for r in (0.0, 0.05, 0.1):
        Ra, _, res = R_cf_vec(K, V0_ENGINE, VG_ENGINE, G8, r)
        Rb = R_floquet(K, V0_ENGINE, [(G8, VG_ENGINE, 0.0)], r, 1 / G8, 512)
        line = f"r = {r}: max |R_A - R_B| = {np.abs(Ra - Rb).max():.1e} (13 angles)"
        if r > 0:
            Rc = R_depth(K, V0_ENGINE, [(G8, VG_ENGINE, 0.0)], r, 1 / G8, 3000, 512)
            line += f", max |R_A - R_C| = {np.abs(Ra - Rc).max():.1e} (C: 3000 periods = {3000 / G8:.0f} A)"
        print(line)
        print("   eta    theta(mrad)   |R|      arg R   | P2 |R|   P2 arg  | d|R|     d arg")
        for i, et in enumerate(ETAS):
            pa, pp = P2_EX[r][i]
            da, dp = abs(Ra[i]) - pa, wrapd(np.angle(Ra[i]) - pp)
            if not (abs(et) == 1.0 and r == 0.0):      # the edges are where P2 rounds eta
                worst = max(worst, abs(da), abs(dp))
            print(f"   {et:+.1f}  {1e3 * theta_of_K(K[i]):.5f}   {abs(Ra[i]):.5f}  {np.angle(Ra[i]):+.4f}  | "
                  f"{pa:.5f}  {pp:+.4f}  | {da:+.1e}  {dp:+.1e}")
    check("P2 table 6.3 'ex' columns reproduced to the printed digits", worst, 0.0, 6e-5)
    # centre, midpoint, edges, sweep
    Rc0 = R_exact(TH_C, 0.0)
    mid = 0.5 * (p3["e_lo"] + p3["e_hi"])
    Rmid, Rlo, Rhi = R_exact(mid, 0.0), R_exact(p3["e_lo"] + 1e-13, 0.0), R_exact(p3["e_hi"] - 1e-13, 0.0)
    print(f"r = 0: arg R at the two-beam centre {np.angle(Rc0):.6f} rad; at the exact midpoint "
          f"{np.angle(Rmid):.6f}; at the exact edges {np.angle(Rlo):+.6f} and {np.angle(Rhi):+.6f} "
          f"(sweep {np.angle(Rhi) - np.angle(Rlo):.6f} rad); |R| - 1 at the centre {abs(Rc0) - 1:+.1e}")
    check("arg R at the centre vs P2 1.70798", np.angle(Rc0), 1.70798, 6e-6)
    for tt in (A / 32, A / 16):
        Rt = R_cf(K_of(TH_C), V0_ENGINE, VG_ENGINE, G8, 0.0, t=tt)
        print(f"truncation offset t = {tt:.5f} A (cosine maximum t below x_s): arg R(centre) = "
              f"{np.angle(Rt):+.5f} rad (two-beam factor exp(i G t) adds {wrapd(2 * np.pi * G8 * tt):+.5f})")
    # plateau maxima with absorption (fine search)
    for r in (0.05, 0.1):
        th = np.linspace(15.9e-3, 16.5e-3, 6001)
        Rv = R_exact(th, r)
        i = int(np.argmax(np.abs(Rv)))
        print(f"r = {r}: max |R| = {abs(Rv[i]):.5f} at {1e3 * th[i]:.5f} mrad (grid 0.1 urad)")
    # |R|^2 FWHM, its centre and the phase at the FWHM edges (P2 6.4)
    th = np.linspace(15.3e-3, 17.0e-3, 17001)
    for r in (0.0, 0.05, 0.1):
        Rv = R_exact(th, r)
        I = np.abs(Rv) ** 2
        half = I.max() / 2
        above = np.nonzero(I >= half)[0]
        i0, i1 = above[0], above[-1]
        t0 = np.interp(half, [I[i0 - 1], I[i0]], [th[i0 - 1], th[i0]])
        t1 = np.interp(half, [I[i1 + 1], I[i1]], [th[i1 + 1], th[i1]])
        a0, a1 = np.angle(R_exact(t0, r)), np.angle(R_exact(t1, r))
        print(f"r = {r:4.2f}: |R|^2 FWHM {1e6 * (t1 - t0):.2f} urad centred {1e3 * (t0 + t1) / 2:.5f} mrad; "
              f"arg R at the FWHM edges {a0:+.4f} -> {a1:+.4f} (sweep {a1 - a0:.4f} rad)")
    # full layer potential at the centre angle (method B only: 12 harmonics)
    Rf = R_floquet(K_of(TH_C), V0_ENGINE, p3["hf"], 0.0, A / 4, 1024)
    Rf2 = R_floquet(K_of(TH_C), V0_ENGINE, p3["hf"], 0.0, A / 4, 2048)
    print(f"full layer potential, r = 0, at {1e3 * TH_C:.5f} mrad: |R| = {abs(Rf):.6f}, arg R = "
          f"{np.angle(Rf):.5f} rad (Magnus 1024 vs 2048 steps per a/4: {abs(Rf - Rf2):.1e})")
    # exhaustive A-B agreement over a fine grid
    th = np.linspace(15.4e-3, 16.9e-3, 301)
    for r in (0.0, 0.05, 0.1):
        Ra = R_exact(th, r)
        Rb = R_floquet(K_of(th), V0_ENGINE, [(G8, VG_ENGINE, 0.0)], r, 1 / G8, 512)
        print(f"r = {r}: 301 angles 15.4-16.9 mrad: max |R_A - R_B| = {np.abs(Ra - Rb).max():.1e}; "
              f"max |R| = {np.abs(Ra).max():.6f}")
    return Rc0


# ---------------------------------------------------------------------------- section 5
def sec5():
    hr("5. Two-beam closed forms against the exact solution (fine eta grids, 4001 points)")
    rF = fresnel_rF(K_of(TH_C), 0.0).real
    print(f"Fresnel step at the centre r_F = {rF:.6f}; 2 atan|r_F| = {2 * np.arctan(abs(rF)):.6f} rad")
    Rc = R_exact(TH_C, 0.0)
    print(f"Darwin/TT phase at the centre pi/2 = {np.pi / 2:.6f}; exact {np.angle(Rc):.6f}; "
          f"exact - Darwin = {np.angle(Rc) - np.pi / 2:.6f} rad; refracted Darwin "
          f"{np.angle(darwin_refracted_R(K_of(TH_C), 0.0)):.6f}")
    out = {}
    for r, emax in ((0.0, 0.9), (0.05, 3.0), (0.1, 3.0)):
        eta = np.linspace(-emax, emax, 4001)
        K = K_of_eta(eta)
        Rex, _, _ = R_cf_vec(K, V0_ENGINE, VG_ENGINE, G8, r)
        for name, fn in (("two-beam matched", two_beam_matched_R),
                         ("Darwin + Fresnel", darwin_refracted_R), ("Darwin/TT", darwin_R)):
            Rf = fn(K, r)
            dR = np.abs(Rf - Rex)
            dph = np.abs(wrapd(np.angle(Rf / Rex)))
            out[(r, name)] = dR.max()
            print(f"r = {r:4.2f}, |eta| <= {emax}: {name:17s} max |dR| = {dR.max():.2e} at eta "
                  f"{eta[int(np.argmax(dR))]:+.3f}; max |d arg| = {dph.max():.2e} rad")
    check("Darwin + Fresnel vs exact, r = 0, |eta|<=0.9 (P2 5.7e-3)", out[(0.0, "Darwin + Fresnel")],
          5.73e-3, 5e-5)
    check("Darwin + Fresnel vs exact, r = 0.05, |eta|<=3 (P2 1.0e-3)", out[(0.05, "Darwin + Fresnel")],
          1.04e-3, 5e-5)


# ---------------------------------------------------------------------------- section 6
def dV0_exact_propagator(K, V):
    """uniform medium: the engine's 'exact' propagator + exp(i sigma V dz) gives
    q^2 = k^2 - (k_z - sigma V)^2, k_z = sqrt(k^2 - K^2); the paraxial (Helmholtz) problem gives
    q^2 = K^2 + 2 k sigma V. Equal q for V_eff = V + dV, dV = V (k_z/k - 1) - sigma V^2/(2 k)."""
    kz = np.sqrt(KV**2 - K**2)
    return V * (kz / KV - 1) - SIG * V**2 / (2 * KV)


def sec6():
    hr("6. Paraxial and 'exact' propagators (stationary R(K), laterally uniform potential)")
    for et in (-0.9, 0.0, 0.9):
        K = K_of_eta(et)
        dV = dV0_exact_propagator(K, V0_ENGINE)
        R0 = R_cf(K, V0_ENGINE, VG_ENGINE, G8, 0.0)
        R1 = R_cf(K, V0_ENGINE + dV, VG_ENGINE, G8, 0.0)
        print(f"eta = {et:+.1f}: dV0_eff = {1e3 * dV:+.4f} mV; arg(R(V0+dV)/R(V0)) = "
              f"{np.angle(R1 / R0):+.4e} rad; |R1| - |R0| = {abs(R1) - abs(R0):+.1e}")
    dV = dV0_exact_propagator(K_of(TH_C), V0_ENGINE)
    dth = -U_of(dV) / (2 * K_of(TH_C) * KV * np.cos(TH_C))
    print(f"plateau shift for dV0 = {1e3 * dV:+.4f} mV: d(theta) = {1e6 * dth:+.4f} urad = "
          f"{dth / 373.59e-6:+.2e} of the width")
    # P2 uses [N(q_in) - N(K)]/sigma (first order in N); the exact uniform-medium match differs by O(theta^4)
    check("dV0_eff at the centre vs P2 -2.0911 mV (to 1 uV)", 1e3 * dV, -2.0911, 1e-3)
    print("rung 1 (V_g = 0, V0 = 12 V): |r_exact-prop|/|r_Fresnel| - 1 (exact dispersion of both "
          "schemes; M2 section 2 measured differences quoted: -0.005, -0.013, -0.045 %)")
    for th_m in (10.0, 16.47, 30.0):
        th = th_m * 1e-3
        K = K_of(th)
        kz = np.sqrt(KV**2 - K**2)
        qe = np.sqrt(KV**2 - (kz - SIG * 12.0) ** 2)
        qp = np.sqrt(K**2 + U_of(12.0))
        re, rp = (K - qe) / (K + qe), (K - qp) / (K + qp)
        print(f"   {th_m:5.2f} mrad: predicted {100 * (abs(re) / abs(rp) - 1):+.4f} %")
    # (e V)^2 term: V -> (e V)^2 / (hbar c)^2 added to U; mean over the cell V0^2 + 2 Vg^2
    dU = (V0_ENGINE**2 + 2 * VG_ENGINE**2) / HBARC_EV_A**2
    dVeq = dU / (2 * KV * SIG)
    K = K_of(TH_C)
    R0 = R_cf(K, V0_ENGINE, VG_ENGINE, G8, 0.0)
    R1 = R_cf(K, V0_ENGINE + dVeq, VG_ENGINE, G8, 0.0)
    print(f"(e V)^2 term: dU0 = {dU:.4e} rad^2/A^2 ({dU / U_of(V0_ENGINE):.3e} of U_0) = V0 + "
          f"{1e3 * dVeq:.4f} mV; arg R changes by {np.angle(R1 / R0):+.3e} rad at the centre "
          f"(mean-potential part only)")


# ---------------------------------------------------------------------------- section 7
def A_two_beam(Z, eta, r, dtau=5.0):
    """A_D(Z) = i ph int_0^Z J1(kc tau)/tau exp(i (E_K - E_B) tau) dtau (t = 0: ph = 1), E-units of
    the paraxial z-evolution (E = K^2/2k); cumulative Simpson on a uniform grid."""
    kc = SIG * VG_ENGINE * (1 + 1j * r)
    dE = eta * SIG * VG_ENGINE + 1j * r * SIG * V0_ENGINE       # E_K - E_B
    tau = np.arange(0.0, Z + dtau / 2, dtau)
    f = np.empty(len(tau), complex)
    f[0] = kc / 2
    f[1:] = special.jv(1, kc * tau[1:]) / tau[1:] * np.exp(1j * dE * tau[1:])
    # cumulative Simpson on pairs of intervals, trapezoid refinement for odd points
    cum = np.zeros(len(tau), complex)
    s2 = (f[0:-2:2] + 4 * f[1:-1:2] + f[2::2]) * dtau / 3
    cum[2::2] = np.cumsum(s2)
    cum[1::2] = cum[0:-1:2] + (5 * f[0:-1:2] + 8 * f[1::2] - f[2::2] if len(f) % 2 else
                               5 * f[0:-1:2] + 8 * f[1::2] - np.append(f[2::2], 0)) * dtau / 12
    return tau, 1j * cum


def R_darwin_eta(eta, r):
    return darwin_R(K_of_eta(eta), r)


def build_len(tau, A, Rinf, tol, kind, grid=20.0):
    if kind == "abs":
        bad = np.abs(A - Rinf) > tol
    elif kind == "rel":
        bad = np.abs(A / Rinf - 1) > tol
    else:
        bad = np.abs(wrapd(np.angle(A / Rinf))) > tol
    step = int(round(grid / (tau[1] - tau[0])))
    idx = np.arange(0, len(tau), step)
    b = bad[idx]
    if not b.any():
        return 0.0
    last = int(np.nonzero(b)[0][-1])
    return float(tau[idx[min(last + 1, len(idx) - 1)]])


def exact_transient(Zs, eta, r, w, Rfun, gamma=4e-5, Omega=0.03, n=30001):
    """|A_S(Z) - R(E_K)| for a smooth switch S = (1 + erf(z/w))/2 of the incident wave, from the
    causal R(E) (E = K^2/2k): A_S(Z) = R(E_K) S(Z) + (1/2pi) int [R(E) - R(E_K)] S^(E - E_K)
    exp(-i (E - E_K) Z) dE on Im E = gamma (pole at E_K subtracted), S^(s) = i exp(-s^2 w^2/4)/s."""
    from scipy.special import erf
    K0 = K_of_eta(eta)
    EK = K0**2 / (2 * KV)
    om = np.linspace(-Omega, Omega, n)
    s = om + 1j * gamma
    RE = Rfun(np.sqrt(2 * KV * (EK + s)), r)
    RK = Rfun(np.array([K0 + 0j]), r)[0]
    Sh = 1j * np.exp(-(s**2) * w**2 / 4) / s
    out = []
    for Z in Zs:
        dA = np.trapezoid((RE - RK) * Sh * np.exp(-1j * s * Z), om) / (2 * np.pi)
        A = RK * 0.5 * (1 + erf(Z / w)) + dA
        out.append((A, RK))
    return out


def sec7():
    hr("7. Build-up after a leading edge: two-beam closed form (sharp edge) and exact transient")
    kc = SIG * VG_ENGINE
    for r in (0.05, 0.1):
        print(f"r = {r}: slowest decay Z_a = 1/(r sigma (V0 - V_g)) = {1 / (r * SIG * (V0_ENGINE - VG_ENGINE)):.0f} A; "
              f"fastest 1/(r sigma (V0 + V_g)) = {1 / (r * SIG * (V0_ENGINE + VG_ENGINE)):.0f} A")
    rows = {}
    for r in (0.0, 0.05, 0.1):
        for eta in (-0.5, 0.0, 0.5, 0.9):
            Zmax = 4.0e5 if r == 0 else 6.0e4
            tau, A = A_two_beam(Zmax, eta, r)
            Rinf = R_darwin_eta(eta, r)
            L = {(k, t): build_len(tau, A, Rinf, t, k) for k in ("abs", "rel", "phase")
                 for t in (1e-2, 1e-3)}
            rows[(r, eta)] = L
            print(f"r = {r:4.2f} eta = {eta:+.1f} |R_D| = {abs(Rinf):.4f}: abs 1e-2 {L[('abs', 1e-2)]:8.0f} A, "
                  f"abs 1e-3 {L[('abs', 1e-3)]:8.0f} A, phase 1e-2 rad {L[('phase', 1e-2)]:8.0f} A, "
                  f"rel 1e-2 {L[('rel', 1e-2)]:8.0f} A, rel 1e-3 {L[('rel', 1e-3)]:8.0f} A; "
                  f"|A(Zmax) - R_D| = {abs(A[-1] - Rinf):.1e}")
            if eta == 0.0:
                zs = [1000, 2000, 3000, 4000, 5000, 8000, 10000]
                vals = [abs(A[int(round(z / 5.0))] - Rinf) for z in zs]
                print("      |A - R_D| at " + ", ".join(f"{z} A: {v:.1e}" for z, v in zip(zs, vals)))
    Zasym = [(np.sqrt(2 / np.pi) / tol) ** (2 / 3) / kc for tol in (1e-2, 1e-3)]
    print(f"asymptote sqrt(2/pi)(kc Z)^(-3/2) at eta = 0: Z(1e-2) = {Zasym[0]:.0f} A, Z(1e-3) = {Zasym[1]:.0f} A")
    check("r = 0, eta = 0, abs 1e-2 build-up vs P2 22 580 A", rows[(0.0, 0.0)][("abs", 1e-2)], 22580, 40)
    check("r = 0, eta = 0, abs 1e-3 vs P2 113 560 A", rows[(0.0, 0.0)][("abs", 1e-3)], 113560, 40)
    check("r = 0, eta = 0.9, abs 1e-3 vs P2 342 680 A", rows[(0.0, 0.9)][("abs", 1e-3)], 342680, 40)
    check("r = 0.05, eta = 0, abs 1e-3 vs P2 7120 A", rows[(0.05, 0.0)][("abs", 1e-3)], 7120, 40)
    check("r = 0.1, eta = 0, abs 1e-3 vs P2 3760 A", rows[(0.1, 0.0)][("abs", 1e-3)], 3760, 40)
    check("r = 0.05, eta = 0, rel 1e-3 vs H2 7538 A", rows[(0.05, 0.0)][("rel", 1e-3)], 7538, 40)
    check("r = 0.1, eta = 0, rel 1e-2 vs H2 3194 A", rows[(0.1, 0.0)][("rel", 1e-2)], 3194, 40)
    # exact transient (smooth edge) at P2's Z values and at the R2-A exit distances
    Rex = lambda K, r: R_cf_vec(K, V0_ENGINE, VG_ENGINE, G8, r)[0]      # noqa: E731
    Rtt = lambda K, r: darwin_R(K, r)                                    # noqa: E731
    Zs = [1953.0, 4004.0, 8008.0, 16016.0, 32031.0]
    for r in (0.0, 0.1):
        ex = exact_transient(Zs, 0.0, r, 400.0, Rex)
        tt = exact_transient(Zs, 0.0, r, 400.0, Rtt)
        for Z, (Ae, Re), (At, Rt) in zip(Zs, ex, tt):
            print(f"   w = 400 A, r = {r}, eta = 0, Z = {Z:7.0f} A: |A_ex - R_ex| = {abs(Ae - Re):.2e}, "
                  f"|A_TT - R_TT| = {abs(At - Rt):.2e}, |arg(A_ex/R_ex)| = {abs(np.angle(Ae / Re)):.1e}")
    # R2-A: sheet-beam edge 4 A -> about 4/tan(theta) = 248 A along z; transient at the exit distance
    for r, Ze in ((0.1, 5000.0), (0.05, 10000.0)):
        for eta in (-0.9, 0.0, 0.9, 3.0):
            (Ae, Re), = exact_transient([Ze], eta, r, 248.0, Rex)
            print(f"   R2-A exit distance: r = {r}, eta = {eta:+.1f}, Z = {Ze:.0f} A (w = 248 A): exact "
                  f"|A - R| = {abs(Ae - Re):.1e}")


# ---------------------------------------------------------------------------- section 8
def R_cell_absorber(K, D, r, harmonics, d, W0=100.0, Wthick=15.0, n_per=512, h_abs=0.0025,
                    V0=None):
    """R at x_s of a crystal with clean depth D above the engine's bulk absorber
    W(x') = W0 sin^2(pi u/2), u = (-D - x')/Wthick in [0, 1] (crystal potential continuing through
    it), then 10 A of crystal + W0 and a uniform (1 + i r) V0 + i W0 substrate with a decaying wave.
    Transfer matrices: my Magnus integrator (one period, then powers; absorber stepped directly)."""
    V0 = V0_ENGINE if V0 is None else V0
    Karr = np.atleast_1d(np.asarray(K, complex))
    Pp = period_matrix(Karr, V0, harmonics, r, d, n_per)
    nfull = int(np.floor(D / d + 1e-12))
    rem = D - nfull * d

    def wf_crys(x):
        return Karr**2 + U_of(V_profile(x, V0, harmonics, r))

    def wf_abs(x):
        u = np.clip((-D - x) / Wthick, 0.0, 1.0)
        W = W0 * np.sin(0.5 * np.pi * u) ** 2
        return Karr**2 + U_of(V_profile(x, V0, harmonics, r) + 1j * W)

    y = None
    qs = np.sqrt(Karr**2 + U_of(V0 * (1 + 1j * r) + 1j * W0))
    qs = np.where(qs.imag < 0, -qs, qs)
    y = np.stack([np.ones_like(qs), -1j * qs], axis=1)[:, :, None]
    xb = -D - Wthick - 10.0
    y = magnus_P(Karr, xb, -D - Wthick, lambda x: Karr**2 + U_of(
        V_profile(x, V0, harmonics, r) + 1j * W0), int(np.ceil(10.0 / h_abs))) @ y
    y = magnus_P(Karr, -D - Wthick, -D, wf_abs, int(np.ceil(Wthick / h_abs))) @ y
    if rem > 1e-12:
        y = magnus_P(Karr, -D, -nfull * d, wf_crys, max(8, int(np.ceil(rem / d * n_per)))) @ y
    Pn = np.linalg.matrix_power(Pp, nfull) if nfull else np.eye(2)[None]
    y = Pn @ y
    L = y[:, 1, 0] / y[:, 0, 0]
    out = R_from_L(L, Karr.real)
    return out if np.ndim(K) else out[0]


def sec8(p3):
    hr("8. Numerical bulk absorber (100 V sin^2, 15 A) below a clean depth D: 1D model")
    h1 = [(G8, VG_ENGINE, 0.0)]
    d8 = 1 / G8
    etas = np.array([-3.0, -1.5, -1.0, -0.9, 0.0, 0.9, 1.0, 1.5, 3.0])
    K = K_of_eta(etas)
    for r, Ds in ((0.0, (60.0, 100.0, 150.0, 250.0)), (0.05, (60.0, 100.0, 150.0)),
                  (0.1, (60.0, 100.0))):
        Rinf = R_cf_vec(K, V0_ENGINE, VG_ENGINE, G8, r)[0]
        for D in Ds:
            Rc = R_cell_absorber(K, D, r, h1, d8)
            print(f"r = {r:4.2f} D = {D:5.0f} A: |R_cell - R_inf| at eta " +
                  " ".join(f"{e:+.1f}:{v:.1e}" for e, v in zip(etas, np.abs(Rc - Rinf))))
    Rc = R_cell_absorber(K, 150.0, 0.0, h1, d8, h_abs=0.00125, n_per=1024)
    Rc2 = R_cell_absorber(K, 150.0, 0.0, h1, d8)
    print(f"step check (r = 0, D = 150 A, half steps): max change {np.abs(Rc - Rc2).max():.1e}")
    Rf = R_cell_absorber(K_of_eta(np.array([-1.5])), 150.0, 0.0, [], d8)
    print(f"V_g = 0 (rung-1 geometry), D = 150 A, eta = -1.5: |R_cell - R_Fresnel| = "
          f"{abs(Rf[0] - fresnel_rF(K_of_eta(-1.5), 0.0)):.1e}")
    Kr = K_of_eta(np.array([-1.5, 1.5]))
    Rinf = R_cf_vec(Kr, V0_ENGINE, VG_ENGINE, G8, 0.0)[0]
    for W0, Wt in ((20.0, 400.0), (20.0, 800.0)):
        Rc = R_cell_absorber(Kr, 150.0, 0.0, h1, d8, W0=W0, Wthick=Wt, h_abs=0.005)
        print(f"r = 0, D = 150 A, ramp {Wt:.0f} A at {W0:.0f} V: |R_cell - R_inf| at eta -1.5, +1.5 = "
              f"{abs(Rc[0] - Rinf[0]):.2e}, {abs(Rc[1] - Rinf[1]):.2e}")
    # null-test translation residual (M2 geometry, 1D): A with clean depth D, B = A + 2 layers
    hf = p3["hf"]
    Kt = np.array([K_of(TH_C)])
    print(f"null-test pair at {1e3 * TH_C:.5f} mrad (R at each crystal's own surface; B = A + a/2):")
    for name, harm, dd, nper in (("single (0,0,8)", h1, d8, 512), ("full layer pot.", hf, A / 4, 1024)):
        for r in (0.0, 0.05, 0.1):
            Rinf = (R_cf_vec(Kt, V0_ENGINE, VG_ENGINE, G8, r)[0][0] if harm is h1 else
                    R_floquet(Kt, V0_ENGINE, harm, r, dd, nper)[0])
            parts = []
            for D in (21.0, 55.0, 60.0, 65.0, 100.0):
                RA = R_cell_absorber(Kt, D, r, harm, dd, n_per=nper, h_abs=0.002)[0]
                RB = R_cell_absorber(Kt, D + A / 2, r, harm, dd, n_per=nper, h_abs=0.002)[0]
                parts.append(f"D {D:4.0f}: arg(B/A) {np.angle(RB / RA):+.1e}, |B/A|-1 {abs(RB / RA) - 1:+.1e}, "
                             f"|R_A - R_inf| {abs(RA - Rinf):.1e}")
            print(f"   {name} r = {r:4.2f} (|R_inf| = {abs(Rinf):.4f}): " + "; ".join(parts))


def sec8b():
    hr("8b. 1D stationary intensity below the surface at the (0,0,8) centre (compare H2's atomistic "
       "exit-plane depths: [100] r = 0.1 26.0 / 53.2 A, r = 0.05 30.2 / 60.6 A for 1e-2 / 1e-4)")
    hf = [(4 * n / A, Vl_kirkland(4 * n, kirkland_fe_table()), 0.0) for n in range(1, 13)]
    for name, harm, dd, nper in (("single (0,0,8)", [(G8, VG_ENGINE, 0.0)], 1 / G8, 512),
                                 ("full layer pot.", hf, A / 4, 1024)):
        for r in (0.0, 0.05, 0.1):
            K = K_of(TH_C)
            P = period_matrix(K, V0_ENGINE, harm, r, dd, nper)[0]
            mu, vec = np.linalg.eig(np.linalg.inv(P))
            j = int(np.argmin(np.abs(mu)))
            R = R_from_L(vec[1, j] / vec[0, j], K)
            I0 = abs(1 + R) ** 2
            lam = -2 * np.log(abs(mu[j])) / dd          # intensity decay rate per A
            depth = [np.log(I0 / tol) / lam for tol in (1e-2, 1e-4)]
            print(f"   {name} r = {r:4.2f}: |R| = {abs(R):.4f}, |u(x_s)|^2 = {I0:.3f}, intensity decay "
                  f"length 1/(2 Im kappa) = {1 / lam:.2f} A; |u|^2 below 1e-2 / 1e-4 beyond "
                  f"{depth[0]:.1f} / {depth[1]:.1f} A (at the planes)")


# ---------------------------------------------------------------------------- section 9 (engine)
class E7PeriodicContinuum:
    """Review-only stand-in (NOT E1's class): V_j = f_j [V0 + sum 2 Vg cos(2 pi g (x_j - x_s + t))]
    (1 + i r) as specified in P2 section 8.1, f_j from the engine's ContinuumTerracePotential.fill,
    harmonic point-sampled (or cell-averaged if cell_average=True, to test the tolerance)."""
    kind = "continuum"

    def __init__(self, cell, *, V0, harmonics, r, cell_average=False):
        from reflection_holo.forward.multislice import (ContinuumTerracePotential,
                                                        PhysicalAbsorption)
        self.cell, self.V0, self.harmonics, self.r = cell, float(V0), list(harmonics), float(r)
        self.cell_average = cell_average
        self._terr = ContinuumTerracePotential(
            cell, V0_V=V0, V0_label="TEST_ONLY: E7 review stand-in",
            physical_absorption=PhysicalAbsorption(model="proportional", ratio=r,
                                                   label="TEST_ONLY: E7 review stand-in"),
            surface_profile="sharp")

    def mean_inner_potential_V(self):
        return self.V0

    def provenance(self):
        return dict(kind="E7 review stand-in continuum periodic potential", V0_V=self.V0,
                    harmonics=[list(h) for h in self.harmonics], ratio=self.r,
                    cell_average=self.cell_average)

    def realise(self, *, grid, dz_A, n_slices, backend, rng):
        f = self._terr.fill(grid)
        x = grid.x_A()
        xs = self.cell.surface_x_A
        v = np.full(x.shape, self.V0)
        for g, Vg, t in self.harmonics:
            fac = np.sinc(g * grid.dx_A) if self.cell_average else 1.0   # np.sinc(u) = sin(pi u)/(pi u)
            v = v + 2 * Vg * fac * np.cos(2 * np.pi * g * (x - xs + t))
        base = f * v[:, None] * (1 + 1j * self.r)
        c = self.cell
        z0, z1 = float(c.crystal_start_z_A), float(c.length_z_A)
        i = np.arange(n_slices)
        overlap = np.clip(np.minimum((i + 1) * dz_A, z1) - np.maximum(i * dz_A, z0), 0.0, dz_A)

        class _R:
            metadata = dict(stand_in="E7")

            def slice_key(self_, k):
                return ("e7", round(float(overlap[k]), 12))

            def projected(self_, k):
                return backend.asarray(base * overlap[k], dtype=backend.complex_dtype)
        return _R()


def run_r2a(*, r, D, Ze, dx, nx, propagator, dz=1.0, x_shift=0.0, cell_average=False,
            V0=None, theta0=None, threads=1):
    """One engine run of P2's R2-A protocol (P2 8.2-8.3) with the stand-in class. Returns the bins
    (f, r_engine) and the setup numbers."""
    from reflection_holo.forward.cell import build_continuum_cell
    from reflection_holo.forward.multislice import (MultisliceParams, NumericalAbsorber, SheetBeam,
                                                    flat_reflection_coefficient, run_realisation,
                                                    sheet_beam_wave)
    V0 = V0_ENGINE if V0 is None else V0
    theta0 = TH_C if theta0 is None else theta0
    H, e_, gap = 24.0, 4.0, 2.0
    z_top = (gap + H) / np.tan(theta0)
    L = float(np.ceil((z_top + Ze) / dz) * dz)
    extent = nx * dx
    depth = 15.0 + D + x_shift
    vac = extent - depth - 10.0
    need = H + gap + L * np.tan(theta0) + 150.0
    assert vac >= need - 1e-9, (vac, need)
    cell = build_continuum_cell(extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0],
                                terrace_heights_A=[0.0], crystal_length_z_A=L - 10.0,
                                vacuum_above_A=vac, depth_below_A=depth, bulk_absorber_A=15.0,
                                top_absorber_A=10.0, entrance_vacuum_z_A=10.0)
    xs = cell.surface_x_A
    pot = E7PeriodicContinuum(cell, V0=V0, harmonics=[(G8, VG_ENGINE, 0.0)], r=r,
                              cell_average=cell_average)
    beam = SheetBeam(height_A=H, edge_A=e_, x_bottom_A=xs + gap, theta_in_ext_rad=theta0,
                     theta_label="TEST_ONLY: E7 review, P2 R2-A beam")
    params = MultisliceParams(energy_keV=200.0, nx=nx, ny=1, dz_A=dz, propagator=propagator,
                              band_limit="2/3", backend="numpy", precision="complex128",
                              threads=threads, absorber=NumericalAbsorber(strength_V=100.0,
                                                                          profile="sin2"),
                              theta_out_ext_rad=theta0, buildup_depth_A=20.0,
                              working_reflections_hkl=())
    t0 = time.time()
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    from reflection_holo.forward.multislice import make_grid
    psi0 = sheet_beam_wave(beam, make_grid(cell, nx=nx, ny=1), LAM)
    out = flat_reflection_coefficient(ew, psi0, x_surface_A=xs, propagator=propagator,
                                      rel_threshold=0.05)
    return dict(f=out["f_per_A"], r=out["r"], xs=xs, L=L, nx=nx, dx=ew.dx_A,
                n_slices=int(round(L / dz)), t=time.time() - t0)


def _bins_eval(res, r, model="exact", V0=None):
    V0 = V0_ENGINE if V0 is None else V0
    G = 2 * np.pi * G8
    K = 2 * np.pi * res["f"]
    eta = (K**2 - (G**2 / 4 - U_of(V0_ENGINE))) / U_of(VG_ENGINE)
    if model == "exact":
        Rref = R_cf_vec(K, V0, VG_ENGINE, G8, r)[0]
    else:   # engine 'exact' propagator: paraxial problem with V0 + dV0_eff(K) (section 6)
        Rref = np.array([R_cf(k, V0 + dV0_exact_propagator(k, V0), VG_ENGINE, G8, r) for k in K])
    return eta, Rref


def sec9():
    hr("9. P2's R2-A protocol run through the UNMODIFIED engine with a review-only stand-in class "
       "(P2 8.1 specification; not E1's class); bins compared with method A at their own K")
    runs = [
        ("F", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.025, nx=16384, propagator="fresnel")),
        ("X", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.025, nx=16384, propagator="exact")),
        ("F_dx05", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.05, nx=8192, propagator="fresnel")),
        ("F_dx0125", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.0125, nx=32768, propagator="fresnel")),
        ("F_dz05", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.025, nx=16384, propagator="fresnel",
                        dz=0.5)),
        ("F_xs_edge", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.025, nx=16384, propagator="fresnel",
                           x_shift=0.0125)),
        ("F_xs_q", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.025, nx=16384, propagator="fresnel",
                        x_shift=0.00625)),
        ("F_dx05_edge", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.05, nx=8192, propagator="fresnel",
                             x_shift=0.025)),
        ("F_dx05_q", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.05, nx=8192, propagator="fresnel",
                          x_shift=0.0125)),
        ("F_Ze10k", dict(r=0.1, D=100.0, Ze=10000.0, dx=0.025, nx=19600, propagator="fresnel")),
        ("F_r005", dict(r=0.05, D=150.0, Ze=10000.0, dx=0.025, nx=21600, propagator="fresnel")),
        ("F_r005_dx05", dict(r=0.05, D=150.0, Ze=10000.0, dx=0.05, nx=10800,
                             propagator="fresnel")),
        ("WRONG_cellavg", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.025, nx=16384,
                               propagator="fresnel", cell_average=True)),
        ("WRONG_V0+5mV", dict(r=0.1, D=100.0, Ze=5000.0, dx=0.025, nx=16384,
                              propagator="fresnel", V0=V0_ENGINE + 5e-3)),
        ("WRONG_V0+5mV_r005", dict(r=0.05, D=150.0, Ze=10000.0, dx=0.025, nx=21600,
                                   propagator="fresnel", V0=V0_ENGINE + 5e-3)),
    ]
    out = {}
    for name, kw in runs:
        res = run_r2a(**kw)
        r = kw["r"]
        model = "oneway" if kw["propagator"] == "exact" else "exact"
        eta, Rref = _bins_eval(res, r, model)       # reference: always the UNperturbed V0
        m3, m09 = np.abs(eta) <= 3, np.abs(eta) <= 0.9
        dR = np.abs(res["r"] - Rref)
        dph = np.abs(wrapd(np.angle(res["r"] / Rref)))
        out[name] = dict(res=res, eta=eta, Rref=Rref, dR3=dR[m3].max(), dR09=dR[m09].max())
        print(f"{name:18s} r = {r:4.2f} {kw['propagator']:7s} dx = {res['dx']:.5f} dz = {kw.get('dz', 1.0)} "
              f"x_s = {res['xs']:.5f} (x_s/dx = {res['xs'] / res['dx']:.2f}) L = {res['L']:.0f} A "
              f"nx = {res['nx']}, slices {res['n_slices']}, bins |eta|<=3: {int(m3.sum())}; vs "
              f"{'one-way model' if model == 'oneway' else 'exact R'}: max |dR| = {dR[m3].max():.2e} "
              f"(|eta|<=0.9: {dR[m09].max():.2e}), max |d arg| = {dph[m3].max():.2e} rad; "
              f"run {res['t']:.0f} s")
    F, X = out["F"], out["X"]
    assert np.allclose(F["res"]["f"], X["res"]["f"])
    m = np.abs(F["eta"]) <= 0.9
    meas = np.angle(X["res"]["r"] / F["res"]["r"])[m]
    pred = np.angle(X["Rref"] / F["Rref"])[m]
    print(f"criterion (b): arg(r_X/r_F) in [{meas.min():+.3e}, {meas.max():+.3e}] rad, predicted "
          f"[{pred.min():+.3e}, {pred.max():+.3e}]; max |measured - predicted| = "
          f"{np.abs(meas - pred).max():.1e} rad (P2 tolerance 2e-4)")
    for a, b in (("F_dx05", "F"), ("F", "F_dx0125"), ("F_r005_dx05", "F_r005"),
                 ("F_dx05_edge", "F_xs_edge"), ("F_dx05_q", "F_xs_q"), ("F_dx05_edge", "F")):
        ratio = out[a]["dR3"] / out[b]["dR3"]
        print(f"criterion (c): max|dR|({a}) / max|dR|({b}) = {ratio:.2f} (order {np.log2(ratio):.2f}; "
              f"P2 requires >= 2^1.5 = {2**1.5:.2f} between 0.05 and 0.025 A)")
    # per-bin Richardson: is the dx error of the engine second order bin by bin?
    Fd = out["F_dx05"]
    common = np.intersect1d(np.round(F["res"]["f"], 9), np.round(Fd["res"]["f"], 9))
    if len(common):
        i1 = np.isin(np.round(F["res"]["f"], 9), common)
        i2 = np.isin(np.round(Fd["res"]["f"], 9), common)
        e1 = F["res"]["r"][i1] - F["Rref"][i1]
        e2 = Fd["res"]["r"][i2] - Fd["Rref"][i2]
        mm = np.abs(F["eta"][i1]) <= 3
        rich = F["res"]["r"][i1] + (F["res"]["r"][i1] - Fd["res"]["r"][i2]) / 3
        print(f"common bins of F and F_dx05 (|eta| <= 3): {int(mm.sum())}; per-bin |e(0.05)|/|e(0.025)| "
              f"from {np.min(np.abs(e2[mm]) / np.abs(e1[mm])):.2f} to {np.max(np.abs(e2[mm]) / np.abs(e1[mm])):.2f}; "
              f"Richardson (p = 2) residual max {np.abs(rich - F['Rref'][i1])[mm].max():.2e}")
    return out


def sec9b():
    hr("9b. What a tolerance on max |r - R_ref| (|eta| <= 3) can detect: perturbed references "
       "(method A) at the R2-A angles, same bins as run F (dx 0.025 A, extent 409.6 A)")
    G = 2 * np.pi * G8
    f = np.arange(1, 8192) / 409.6
    K = 2 * np.pi * f
    eta = (K**2 - (G**2 / 4 - U_of(V0_ENGINE))) / U_of(VG_ENGINE)
    K = K[np.abs(eta) <= 3]
    for r in (0.1, 0.05):
        R0 = R_cf_vec(K, V0_ENGINE, VG_ENGINE, G8, r)[0]
        cases = [("V0 + 1 mV", dict(V0=V0_ENGINE + 1e-3)), ("V0 + 3 mV", dict(V0=V0_ENGINE + 3e-3)),
                 ("V0 + 5 mV", dict(V0=V0_ENGINE + 5e-3)), ("V0 - 2.09 mV (exact propagator)",
                                                            dict(V0=V0_ENGINE - 2.0908e-3)),
                 ("V_g x (1 - 2.2e-3) (cell-averaged, dx 0.025)", dict(Vg=VG_ENGINE * np.sinc(G8 * 0.025))),
                 ("V_g x (1 - 8.9e-3) (cell-averaged, dx 0.05)", dict(Vg=VG_ENGINE * np.sinc(G8 * 0.05))),
                 ("sigma x (1 + 1e-4) (V0 and V_g scaled)", dict(V0=V0_ENGINE * 1.0001, Vg=VG_ENGINE * 1.0001)),
                 ("cosine origin dx/2 = 0.0125 A below x_s", dict(t=0.0125)),
                 ("cosine origin 0.001 A below x_s", dict(t=0.001))]
        for name, kw in cases:
            R1 = R_cf_vec(K, kw.get("V0", V0_ENGINE), kw.get("Vg", VG_ENGINE), G8, r, t=kw.get("t", 0.0))[0]
            print(f"   r = {r:4.2f}: {name:48s}: max |dR| = {np.abs(R1 - R0).max():.2e}, max |d arg| = "
                  f"{np.abs(wrapd(np.angle(R1 / R0))).max():.2e} rad")
        # absorption missing on the harmonic (U_g real, U_0 absorbing)
        Uc = U_of(V0_ENGINE) * (1 + 1j * r)
        R2 = []
        for k in K:
            # method B with a harmonic without absorption: V = (1+ir) V0 + 2 Vg cos
            P = magnus_P(np.array([k]), -1 / G8, 0.0, lambda x: k**2 + Uc + U_of(
                2 * VG_ENGINE * np.cos(2 * np.pi * G8 * x)), 512)[0]
            mu, vec = np.linalg.eig(np.linalg.inv(P))
            j = int(np.argmin(np.abs(mu)))
            R2.append(R_from_L(vec[1, j] / vec[0, j], k))
        R2 = np.array(R2)
        print(f"   r = {r:4.2f}: {'absorption on V0 only (harmonic real)':48s}: max |dR| = "
              f"{np.abs(R2 - R0).max():.2e}")
        print(f"   r = {r:4.2f}: read-out plane dx/2 = 0.0125 A off x_s: arg R changes by 2 K (0.0125 A) = "
              f"{2 * K.min() * 0.0125:.4f} to {2 * K.max() * 0.0125:.4f} rad")


# ---------------------------------------------------------------------------- section 10
def sec10():
    hr("10. Comparison with P2's tool (imported ONLY here, as a black box, after sections 1-9)")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "physics_checks")))
    import rung2_reference as p2
    th = theta_of_K(K_of_eta(ETAS))
    for r in (0.0, 0.05, 0.1):
        Rp = np.asarray(p2.reflection_amplitude(th, 200.0, V0_ENGINE, [VG_ENGINE], G8, r))
        Rm = R_exact(th, r)
        Rp2 = np.asarray(p2.reflection_amplitude(th, 200.0, V0_ENGINE, [VG_ENGINE], G8, r,
                                                 model="engine_exact_propagator"))
        Rm2 = np.array([R_cf_vec(np.array([K_of(t)]), V0_ENGINE + dV0_exact_propagator(K_of(t), V0_ENGINE),
                                 VG_ENGINE, G8, r)[0][0] for t in th])
        forms = []
        for form, fn in (("bloch_matched", two_beam_matched_R), ("darwin_refracted", darwin_refracted_R),
                         ("darwin", darwin_R)):
            Pf = np.asarray(p2.two_beam_reflection(th, 200.0, V0_ENGINE, [VG_ENGINE], G8, r, order=1,
                                                   form=form))
            forms.append(f"{form} {np.abs(Pf - fn(K_of(th), r)).max():.1e}")
        ne = np.abs(np.abs(ETAS) - 1.0) > 1e-9     # the r = 0 band-edge angles are hypersensitive
        print(f"r = {r:4.2f}: max |R_P2 - R_E7| exact {np.abs(Rp - Rm).max():.1e}; engine_exact_propagator "
              f"model {np.abs(Rp2 - Rm2)[ne].max():.1e} (eta = +-1 excluded; there "
              f"{np.abs(Rp2 - Rm2)[~ne].max():.1e}); two-beam forms: " + ", ".join(forms))
    Kb = K_of_eta(np.array([-1.5, 0.0, 3.0]))
    Rg = np.asarray(p2.reflection_amplitude_engine_geometry(theta_of_K(Kb), 200.0, V0_ENGINE, [VG_ENGINE], G8,
                                                            0.0, clean_depth_A=150.0, absorber_A=15.0,
                                                            absorber_W0_V=100.0))
    Rm = R_cell_absorber(Kb, 150.0, 0.0, [(G8, VG_ENGINE, 0.0)], 1 / G8)
    print(f"engine-geometry cell (r = 0, D = 150 A, eta -1.5, 0, 3): max |R_P2 - R_E7| = {np.abs(Rg - Rm).max():.1e}")
    Zs, _ = p2.build_up_length(TH_C, 200.0, V0_ENGINE, VG_ENGINE, G8, 0.1,
                               tols=(("abs", 1e-3), ("phase", 1e-2)))
    print(f"build_up_length r = 0.1, eta = 0 (P2 tool): abs 1e-3 {Zs[0]:.0f} A, phase 1e-2 {Zs[1]:.0f} A")
    # P2's independent split step and the ENGINE (stand-in class) on identical grids
    for r, D, Ze, nx in ((0.1, 100.0, 5000.0, 16308), (0.05, 150.0, 10000.0, 21536)):
        ss = p2.split_step_1d(theta0_rad=TH_C, V0_V=V0_ENGINE, Vg_V=VG_ENGINE, g_per_A=G8,
                              absorption_ratio=r, propagator="fresnel", dx_A=0.025, dz_A=1.0, H_A=24.0,
                              edge_A=4.0, gap_A=2.0, clean_depth_A=D, exit_after_top_contact_A=Ze,
                              extra_vacuum_A=150.0)
        res = run_r2a(r=r, D=D, Ze=Ze, dx=float(ss["dx_A"]), nx=int(ss["n_x"]), propagator="fresnel")
        f_ss = np.sin(np.asarray(ss["theta_bins"])) / LAM
        r_ss = np.asarray(ss["r"])
        print(f"   P2 split step dx {ss['dx_A']:.10f} A, n_x {ss['n_x']}, x_s/dx = {(15.0 + D) / ss['dx_A']:.3f}; "
              f"engine run on the same grid: dx {res['dx']:.10f} A")
        j = np.array([int(np.argmin(np.abs(f_ss - fv))) for fv in res["f"]])
        ok = np.abs(f_ss[j] - res["f"]) < 1e-7
        i1, i2 = np.nonzero(ok)[0], j[ok]
        eta, Rref = _bins_eval(res, r, "exact")
        m = np.abs(eta[i1]) <= 3
        print(f"r = {r}: P2 split step nx {ss['n_x']}, L {ss['L_A']:.0f} A; engine nx {res['nx']}, L {res['L']:.0f} A; "
              f"common bins |eta|<=3: {int(m.sum())}: max |r_engine - R| = "
              f"{np.abs(res['r'][i1] - Rref[i1])[m].max():.2e}, max |r_P2ss - R| = "
              f"{np.abs(r_ss[i2] - Rref[i1])[m].max():.2e}, max |r_engine - r_P2ss| = "
              f"{np.abs(res['r'][i1] - r_ss[i2])[m].max():.2e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", default="1,2,3,4,5,6,7,8,8b,9b,9,10")
    a = ap.parse_args()
    want = a.sections.split(",")
    t0 = time.time()
    print(f"E7 recompute, numpy {np.__version__}; started {time.strftime('%Y-%m-%d %H:%M:%S')}")
    own = p3 = None
    G = 2 * np.pi * G8
    global TH_C
    TH_C = theta_of_K(np.sqrt(G**2 / 4 - U_of(V0_ENGINE)))
    if "1" in want:
        sec1()
    if "2" in want:
        own = sec2()
    if "3" in want or "4" in want or "8" in want:
        p3 = sec3(own)
    if "4" in want:
        sec4(p3)
    if "5" in want:
        sec5()
    if "6" in want:
        sec6()
    if "7" in want:
        sec7()
    if "8" in want:
        sec8(p3)
    if "8b" in want:
        sec8b()
    if "9b" in want:
        sec9b()
    if "9" in want:
        sec9()
    if "10" in want:
        sec10()
    hr("Summary of self-checks")
    nfail = sum(1 for _, ok in CHECKS if not ok)
    print(f"{len(CHECKS)} checks, {nfail} failed; wall time {time.time() - t0:.0f} s")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
