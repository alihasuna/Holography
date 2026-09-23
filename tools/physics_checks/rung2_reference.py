#!/usr/bin/env python3
r"""rung2_reference.py: exact and two-beam reference for rung 2 of the phase-validation ladder.

Ladder: docs/05_final_repository_specification.md section 4.4, rung 2 ("Bragg-case Bloch-wave two-beam
solution for one allowed reflection, which gives arg A in closed form across the Darwin plateau; the
multislice must reproduce the phase sweep, not only the width"). Report:
docs/agent_reports/P2_rung2_reference.md (premises, derivations, numbers, proposed engine test).
Run: venv/bin/python tools/physics_checks/rung2_reference.py [--long]  (prints every number of the report
and exits non-zero if a self-check fails; about 6 minutes on one free core, longer on a loaded machine;
peak memory below 0.5 GB; --long adds the r = 0 split-step run of report section 7, about 5 minutes).

Every formula below is DERIVED_HERE from the premises stated in the report (section 1); no textbook
passage was read for it, so no textbook is cited.

CONVENTIONS (docs/physics_conventions.md)
  * exp(+i(k.r - omega t)); angular wavevectors in rad/A; crystallographic g in cycles/A, G = 2 pi g.
  * x = OUTWARD surface normal (into vacuum), z = beam azimuth; theta = EXTERNAL glancing angle.
  * Incident vacuum wave exp(i(-K x + k_z z)), reflected exp(i(+K x + k_z z)), K = k sin(theta).
  * R(theta) = (reflected amplitude)/(incident amplitude), BOTH EVALUATED AT THE TRUNCATION PLANE
    x = x_s (the plane where the crystal potential starts). Referred to another plane x_r:
    R_r = R exp(2 i K (x_r - x_s)). This is the quantity measured by the engine's
    reflection_holo.forward.multislice.analysis.flat_reflection_coefficient(x_surface_A=x_s).
  * Potential (V, electron potential energy -e V < 0 inside):
        V(x) = (1 + i r) [ V0 + sum_n 2 V_n cos(2 pi n g (x - x_s + t)) ]   for x < x_s,
        V(x) = 0                                                              for x > x_s,
    V_n real (n = 1, 2, ...; "Vg_list"), g the FUNDAMENTAL spatial frequency (cycles/A), r the
    proportional absorption ratio (engine PhysicalAbsorption model "proportional"), t
    ("plane_offset_A") the depth of a cosine maximum below x_s. With t = 0 and one harmonic this is
    the orchestrator's V0 + 2 V_g cos(g (x - x_s)) with g read as 2 pi g: the truncation plane is at a
    maximum of the harmonic (an atomic plane for a Si(001) layer potential).
  * Wave equation (premise P1): u'' + (K^2 + U(x)) u = 0 with U = 2 k sigma V (rad^2/A^2),
    sigma = 2 pi (T + m_e c^2) lambda / (h c)^2 the engine's interaction constant, i.e. the
    relativistically corrected Schroedinger (Helmholtz) equation without the (e V)^2 term; the
    (e V)^2 term (Klein-Gordon) is available as an option to quantify it (klein_gordon_V2=True).

METHODS (all DERIVED_HERE; report sections 2 to 6)
  exact:     "bloch"  - Bloch waves of the periodic potential (plane-wave expansion, quadratic
                        eigenvalue problem in the normal Bloch wavevector, linearised), ONE Bloch wave
                        in the semi-infinite crystal (decaying, or carrying flux into the crystal),
                        continuity of u and u' at x_s.
             "floquet"- monodromy matrix of one period by high-order ODE integration, Floquet
                        eigenvector selected by the same rule, same matching (independent of the
                        plane-wave truncation).
             "depth"  - ODE integration from a finite depth D (uniform substrate V0 with an outgoing
                        wave below it) up to x_s: a finite crystal; converges to the semi-infinite
                        result only where the Bloch wave decays (absorption, or inside the gap).
  two-beam:  "bloch_matched" - two plane waves (-kappa, G - kappa), exact quartic, exact matching
                        (closed form, includes the Fresnel reflection at the mean-potential step).
             "darwin" - Takagi-Taupin/Darwin limit (linearised dispersion, no step reflection):
                        R = -(U_g/sqrt(U_g U_-g)) (eta - sqrt(eta^2 - 1)), eta = (K^2 + U_0 - G^2/4)
                        / sqrt(U_g U_-g); arg R sweeps by pi across |eta| <= 1.
  build-up:  two-beam closed form A(Z) = i (U_g/sqrt(U_g U_-g)) int_0^{Z} (J_1(kc tau)/tau)
             exp(i (E_K - E_B) tau) d tau (sharp leading edge), and the exact step response from the
             exact R(E) by a damped FFT (smooth leading edge).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
from scipy import integrate, linalg, optimize, special

sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])  # repository root, for reflection_holo

from reflection_holo.constants import (A_SI_A, BEAM_ENERGY_SUPPLIED_KEV, HC_EV_M,  # noqa: E402
                                       M_E_C2_EV, TWO_PI)

HC_EV_A = HC_EV_M * 1.0e10                   # eV A (from the exact SI-2019 h, c, e)
HBARC_EV_A = HC_EV_A / TWO_PI                # eV A

# =================================================================================================
# 1. Beam constants (from reflection_holo.constants only)
# =================================================================================================


def beam_constants(energy_keV: float) -> dict:
    """lambda (A), k = 2 pi / lambda (rad/A), sigma (rad/(V A)), gamma for the 200 keV beam.

    lambda = h c / sqrt(T (T + 2 m_e c^2)); sigma = 2 pi (T + m_e c^2) lambda / (h c)^2, so that
    2 k sigma V = 2 (T + m_e c^2) e V / (hbar c)^2 (the Klein-Gordon term linear in V). DERIVED_HERE;
    constants from reflection_holo.constants. PROJECT_INPUT item 1: 200 keV only (300 keV refused).
    """
    if energy_keV is None or float(energy_keV) != BEAM_ENERGY_SUPPLIED_KEV:
        raise ValueError(f"beam energy {energy_keV!r} keV refused: 200 keV is the only beam energy "
                         f"of this project (PROJECT_INPUT item 1)")
    T = float(energy_keV) * 1e3
    lam = HC_EV_A / np.sqrt(T * (T + 2.0 * M_E_C2_EV))
    k = TWO_PI / lam
    sigma = TWO_PI * (T + M_E_C2_EV) * lam / HC_EV_A**2
    return dict(energy_keV=float(energy_keV), T_eV=T, wavelength_A=lam, k=k, sigma=sigma,
                gamma=1.0 + T / M_E_C2_EV)


# =================================================================================================
# 2. The potential model
# =================================================================================================


@dataclass(frozen=True)
class Slab:
    """Semi-infinite crystal x < x_s with the laterally uniform potential of the module docstring.

    V0_V: mean potential (V); Vg_list_V: real V_n (V) of the harmonics n = 1, 2, ... of the
    fundamental g_per_A (cycles/A); absorption_ratio r >= 0 (V_imag = r V_real); plane_offset_A t:
    cosine maxima at x = x_s - t - m/g. All required; t = 0 is the orchestrator's form."""
    V0_V: float
    Vg_list_V: tuple
    g_per_A: float
    absorption_ratio: float
    plane_offset_A: float

    def __post_init__(self):
        if not (np.isfinite(self.V0_V) and self.V0_V >= 0):
            raise ValueError("V0_V must be finite and >= 0")
        if not (np.isfinite(self.g_per_A) and self.g_per_A > 0):
            raise ValueError("g_per_A (cycles/A) must be > 0")
        if not (np.isfinite(self.absorption_ratio) and self.absorption_ratio >= 0):
            raise ValueError("absorption_ratio must be finite and >= 0")

    @property
    def G_f(self) -> float:
        """Fundamental reciprocal vector 2 pi g (rad/A)."""
        return TWO_PI * self.g_per_A

    @property
    def period_A(self) -> float:
        return 1.0 / self.g_per_A

    def V_coeffs(self) -> dict:
        """Complex Fourier coefficients V_n^(s) (V) of V(x') = sum_n V_n^(s) exp(i n G_f x'),
        x' = x - x_s, INCLUDING the absorption factor (1 + i r)."""
        c = 1.0 + 1j * self.absorption_ratio
        out = {0: self.V0_V * c}
        for n, v in enumerate(self.Vg_list_V, start=1):
            ph = np.exp(1j * n * self.G_f * self.plane_offset_A)
            out[n] = float(v) * ph * c
            out[-n] = float(v) * np.conj(ph) * c
        return out

    def U_coeffs(self, bc: dict, *, klein_gordon_V2: bool) -> dict:
        """U_n = 2 k sigma V_n (rad^2/A^2); with klein_gordon_V2 the (e V)^2/(hbar c)^2 term is added
        (convolution of the V_n; only for r = 0, where it is a well-defined real correction)."""
        V = self.V_coeffs()
        U = {n: 2.0 * bc["k"] * bc["sigma"] * v for n, v in V.items()}
        if klein_gordon_V2:
            if self.absorption_ratio != 0:
                raise ValueError("klein_gordon_V2 is defined here for r = 0 only")
            for n1, v1 in V.items():
                for n2, v2 in V.items():
                    U[n1 + n2] = U.get(n1 + n2, 0.0) + v1 * v2 / HBARC_EV_A**2
        return U


def _U_of_x(U: dict, G_f: float):
    nn = np.array(sorted(U), dtype=float)
    Un = np.array([U[int(n)] for n in nn], dtype=complex)

    def f(x):
        return np.sum(Un * np.exp(1j * nn * G_f * x))
    return f


# =================================================================================================
# 3. Exact solvers: log-derivative L = u'(x_s)/u(x_s) of the physical crystal solution
# =================================================================================================

def R_from_L(K, L):
    """Matching u = exp(-iK x') + R exp(iK x') to u'/u = L at x' = 0: R = (L + iK)/(iK - L)."""
    return (L + 1j * K) / (1j * K - L)


def L_bloch(K, U: dict, G_f: float, M: int, *, basis=None, return_info=False):
    """Bloch-wave log-derivative at x' = 0 (DERIVED_HERE, report section 2.2).

    b(x') = sum_m c_m exp(i (m G_f - kappa) x'), m in the basis (default -M..M). The Helmholtz
    equation gives, for each m, [K^2 - (m G_f - kappa)^2] c_m + sum_m' U_{m-m'} c_m' = 0, i.e.
    (A + kappa B - kappa^2) c = 0 with A = diag(K^2 - m^2 G_f^2) + [U_{m-m'}], B = diag(2 m G_f),
    linearised as [[0, I], [A, B]] [c; kappa c] = kappa [c; kappa c]. The physical Bloch wave of the
    semi-infinite crystal (x' < 0) decays towards -x (Im kappa > 0) or, if kappa is real, carries its
    flux sum_m |c_m|^2 (m G_f - kappa) towards -x (< 0); among its equivalent representatives
    (kappa + j G_f) the one with Re kappa closest to Re sqrt(K^2 + U_0) is used."""
    m = np.arange(-M, M + 1) if basis is None else np.asarray(basis, dtype=int)
    N = len(m)
    Umat = np.array([[U.get(int(a - b), 0.0) for b in m] for a in m], dtype=complex)
    A = np.diag(K**2 - (m * G_f) ** 2).astype(complex) + Umat
    B = np.diag(2.0 * m * G_f).astype(complex)
    big = np.block([[np.zeros((N, N)), np.eye(N)], [A, B]])
    w, v = linalg.eig(big)
    q0 = np.sqrt(K**2 + U.get(0, 0.0) + 0j)
    tol = 1e-9 * G_f
    best, best_d = None, np.inf
    for j in range(2 * N):
        kap = w[j]
        c = v[:N, j]
        nrm = np.linalg.norm(c)
        if nrm == 0:
            continue
        c = c / nrm
        km = m * G_f - kap
        if abs(kap.imag) > tol:
            phys = kap.imag > 0
        else:
            phys = float(np.sum(np.abs(c) ** 2 * km.real)) < 0.0
        if not phys:
            continue
        d = abs(kap.real - q0.real)
        if d < best_d:
            best, best_d = (kap, c, km), d
    if best is None:
        raise RuntimeError("no physical Bloch wave found")
    kap, c, km = best
    u0 = np.sum(c)
    du0 = np.sum(1j * km * c)
    L = du0 / u0
    if return_info:
        edge = float(np.max(np.abs(c[[0, -1]]) ** 2)) if basis is None else float("nan")
        return L, dict(kappa=kap, c=c, m=m, edge_weight=edge)
    return L


def _ode_rhs(K, Ux):
    def rhs(x, y):
        a = -(K**2 + Ux(x))
        return np.array([y[1], a * y[0], y[3], a * y[2]])
    return rhs


def monodromy(K, U: dict, G_f: float, *, rtol=1e-12, atol=1e-14):
    """2x2 matrix mapping (u, u')(0) to (u, u')(-d), d = 2 pi / G_f, by DOP853 integration."""
    d = TWO_PI / G_f
    sol = integrate.solve_ivp(_ode_rhs(K, _U_of_x(U, G_f)), (0.0, -d),
                              np.array([1, 0, 0, 1], dtype=complex), method="DOP853",
                              rtol=rtol, atol=atol)
    if not sol.success:
        raise RuntimeError(sol.message)
    y = sol.y[:, -1]
    return np.array([[y[0], y[2]], [y[1], y[3]]])


def L_floquet(K, U: dict, G_f: float, *, rtol=1e-12):
    """Floquet log-derivative (DERIVED_HERE, report section 2.3): eigenvectors v of the monodromy M
    (y(-d) = mu y(0)); the physical one has |mu| < 1 (decays towards -x) or, for |mu| = 1, flux
    Im(conj(u) u') < 0. L = v[1]/v[0]."""
    Mo = monodromy(K, U, G_f, rtol=rtol)
    mu, V = np.linalg.eig(Mo)
    cands = []
    for j in range(2):
        u, du = V[0, j], V[1, j]
        dec = 1.0 - abs(mu[j])
        if abs(dec) > 1e-9:
            phys = dec > 0
        else:
            phys = (np.conj(u) * du).imag < 0
        if phys:
            cands.append((u, du, abs(mu[j])))
    if len(cands) != 1:
        raise RuntimeError(f"Floquet selection ambiguous: |mu| = {np.abs(mu)}")
    u, du, _ = cands[0]
    return du / u


def L_depth(K, U: dict, G_f: float, depth_A: float, *, extra_imag_V=None, bc=None, rtol=1e-11,
            substrate_U=None):
    """Finite crystal of thickness depth_A on a uniform substrate (DERIVED_HERE, report 2.4):
    y(-D) = (1, -i q_s), q_s = sqrt(K^2 + U_s) (Im q_s >= 0: outgoing/decaying downwards), integrated
    UPWARDS to x' = 0 (the physical solution grows upwards, so the integration is stable).
    extra_imag_V(x') optional additional imaginary potential W(x') in V (numerical absorber),
    converted with 2 k sigma."""
    Ux0 = _U_of_x(U, G_f)
    if extra_imag_V is not None:
        f2 = 2.0 * bc["k"] * bc["sigma"]

        def Ux(x):
            return Ux0(x) + 1j * f2 * extra_imag_V(x)
    else:
        Ux = Ux0
    Us = U.get(0, 0.0) if substrate_U is None else substrate_U
    qs = np.sqrt(K**2 + Us + 0j)
    if qs.imag < 0:
        qs = -qs

    def rhs(x, y):
        return np.array([y[1], -(K**2 + Ux(x)) * y[0]])
    sol = integrate.solve_ivp(rhs, (-depth_A, 0.0), np.array([1.0, -1j * qs], dtype=complex),
                              method="DOP853", rtol=rtol, atol=1e-300)
    if not sol.success:
        raise RuntimeError(sol.message)
    u, du = sol.y[:, -1]
    return du / u


def L_transfer_matrix(K, U_of_x, x_bottom_A: float, h_A: float, U_substrate):
    """Independent check of L_depth (report 2.4): piecewise-constant potential (midpoint rule) on
    slices of thickness h_A from x' = x_bottom_A (< 0) up to 0, exact 2x2 transfer matrix per
    slice, [[cos qh, sin(qh)/q], [-q sin qh, cos qh]], q = sqrt(K^2 + U_j), applied to the outgoing
    substrate wave (1, -i q_s). Second order in h_A (Richardson-extrapolated by the caller)."""
    n = int(round(-x_bottom_A / h_A))
    h = -x_bottom_A / n
    xm = x_bottom_A + (np.arange(n) + 0.5) * h
    Uj = np.array([U_of_x(x) for x in xm])
    q = np.sqrt(K**2 + Uj + 0j)
    c, sn = np.cos(q * h), np.sin(q * h)
    qs = np.sqrt(K**2 + U_substrate + 0j)
    if qs.imag < 0:
        qs = -qs
    y = np.array([1.0 + 0j, -1j * qs])
    for j in range(n):
        y = np.array([c[j] * y[0] + sn[j] / q[j] * y[1], -q[j] * sn[j] * y[0] + c[j] * y[1]])
        y /= abs(y[0]) + abs(y[1])
    return y[1] / y[0]


def n_plane_waves_default(slab: Slab) -> int:
    """Half-width M of the plane-wave basis: 8 for one harmonic, 2 per harmonic otherwise (>= 8);
    convergence is demonstrated in main() (M = 4 vs 8 for one harmonic, M = 24 vs 48 and Floquet for
    the 12-harmonic layer potential; report section 2.2)."""
    return max(8, 2 * len(slab.Vg_list_V))


def _N_oneway(q, k):
    """N(q) = sqrt(k^2 - q^2) - k + q^2/(2k) = -q^4 / (2 k (k + sqrt(k^2 - q^2))^2) (rad/A)."""
    s = np.sqrt(k**2 - q**2)
    return -q**4 / (2.0 * k * (k + s) ** 2)


def oneway_V0_shift_V(K, slab: Slab, bc: dict) -> float:
    """Effective change of the mean potential seen by the ENGINE'S 'exact'-propagator split step
    (one-way generator sqrt(k^2 + d_x^2) - k + sigma V instead of a function of d_x^2 + 2 k sigma V):
    dV = [N(q_in) - N(K)] / sigma with q_in = Re sqrt(K^2 + 2 k sigma V0) (DERIVED_HERE, first order in
    N, report section 4.2). Negative (the internal wave is steeper than the vacuum wave)."""
    K = float(np.real(K))
    q_in = float(np.sqrt(K**2 + 2 * bc["k"] * bc["sigma"] * slab.V0_V))
    return float((_N_oneway(q_in, bc["k"]) - _N_oneway(K, bc["k"])) / bc["sigma"])


def reflection_amplitude_K(K, energy_keV: float, V0_V: float, Vg_list, g_per_A: float,
                           absorption_ratio: float, *, plane_offset_A: float = 0.0,
                           method: str = "bloch", model: str = "exact", n_plane_waves=None,
                           klein_gordon_V2: bool = False, depth_A=None):
    """R as a function of the vacuum normal wavevector K (rad/A; complex K allowed for 'bloch' and
    'depth', used by the step-response FFT). model: 'exact' (Helmholtz; identical to the paraxial
    Fresnel multislice in the stationary limit, report 4.1) or 'engine_exact_propagator' (one-way
    split step, V0 shifted by oneway_V0_shift_V)."""
    bc = beam_constants(energy_keV)
    Vg = tuple(float(v) for v in np.atleast_1d(Vg_list)) if Vg_list is not None else ()
    slab = Slab(float(V0_V), Vg, float(g_per_A), float(absorption_ratio), float(plane_offset_A))
    if model == "engine_exact_propagator":
        slab = Slab(slab.V0_V + oneway_V0_shift_V(K, slab, bc), Vg, slab.g_per_A,
                    slab.absorption_ratio, slab.plane_offset_A)
    elif model != "exact":
        raise ValueError("model must be 'exact' or 'engine_exact_propagator'")
    U = slab.U_coeffs(bc, klein_gordon_V2=klein_gordon_V2)
    if method == "bloch":
        M = n_plane_waves_default(slab) if n_plane_waves is None else int(n_plane_waves)
        L = L_bloch(K, U, slab.G_f, M)
    elif method == "floquet":
        L = L_floquet(K, U, slab.G_f)
    elif method == "depth":
        if depth_A is None:
            raise ValueError("method 'depth' needs depth_A")
        L = L_depth(K, U, slab.G_f, float(depth_A))
    else:
        raise ValueError("method must be 'bloch', 'floquet' or 'depth'")
    return R_from_L(K, L)


def reflection_amplitude(theta_rad, energy_keV: float, V0_V: float, Vg_list, g_per_A: float,
                         absorption_ratio: float, *, plane_offset_A: float = 0.0,
                         method: str = "bloch", model: str = "exact", n_plane_waves=None,
                         klein_gordon_V2: bool = False, depth_A=None):
    """EXACT complex reflection amplitude R(theta) of the specular beam (report sections 1, 2).

    theta_rad: EXTERNAL glancing angle(s) (scalar or array); energy_keV: 200 (asserted); V0_V (V);
    Vg_list: real V_n (V) of the harmonics n = 1, 2, ... of g_per_A (cycles/A; e.g. [V_008] with
    g = 8/a, or [V_004, V_008, ...] with g = 4/a); absorption_ratio r (V_imag = r V_real).
    Returns R referenced at the truncation plane x_s (module docstring)."""
    bc = beam_constants(energy_keV)
    th = np.asarray(theta_rad, dtype=float)
    Ks = bc["k"] * np.sin(th)
    out = np.array([reflection_amplitude_K(K, energy_keV, V0_V, Vg_list, g_per_A, absorption_ratio,
                                           plane_offset_A=plane_offset_A, method=method,
                                           model=model, n_plane_waves=n_plane_waves,
                                           klein_gordon_V2=klein_gordon_V2, depth_A=depth_A)
                    for K in np.atleast_1d(Ks)])
    return complex(out[0]) if th.ndim == 0 else out


def reflection_amplitude_engine_geometry(theta_rad, energy_keV, V0_V, Vg_list, g_per_A,
                                         absorption_ratio, *, clean_depth_A, absorber_A,
                                         absorber_W0_V, plane_offset_A=0.0):
    """R for the ENGINE'S finite cell (report section 6.3): clean crystal of depth clean_depth_A above
    a numerical absorber W(x) = W0 sin^2(pi u/2) (u = 0 at its inner edge, 1 at the box bottom, the
    crystal potential continuing through it, as in the engine), then a uniform lossy substrate
    U_0 + i 2 k sigma W0 with an outgoing wave (the engine wraps into its top absorber instead; the
    amplitude reaching the box bottom is ~exp(-30), report 6.3)."""
    bc = beam_constants(energy_keV)
    Vg = tuple(float(v) for v in np.atleast_1d(Vg_list))
    slab = Slab(float(V0_V), Vg, float(g_per_A), float(absorption_ratio), float(plane_offset_A))
    U = slab.U_coeffs(bc, klein_gordon_V2=False)
    D = float(clean_depth_A) + float(absorber_A)

    def W(x):
        u = (-(x) - clean_depth_A) / absorber_A
        return absorber_W0_V * np.sin(0.5 * np.pi * min(max(u, 0.0), 1.0)) ** 2
    Us = U[0] + 1j * 2 * bc["k"] * bc["sigma"] * absorber_W0_V
    th = np.atleast_1d(np.asarray(theta_rad, float))
    out = []
    for t in th:
        K = bc["k"] * np.sin(t)
        L = L_depth(K, U, slab.G_f, D, extra_imag_V=W, bc=bc, substrate_U=Us)
        out.append(R_from_L(K, L))
    out = np.array(out)
    return complex(out[0]) if np.ndim(theta_rad) == 0 else out


# =================================================================================================
# 4. Two-beam closed forms
# =================================================================================================

def _two_beam_parts(K, slab: Slab, bc: dict, order: int):
    """(eps, U_g, U_-g, U_0, G) for the reflection n = order of the fundamental."""
    U = slab.U_coeffs(bc, klein_gordon_V2=False)
    G = order * slab.G_f
    Ug, Umg, U0 = U[order], U[-order], U[0]
    eps = K**2 + U0 - G**2 / 4.0
    return eps, Ug, Umg, U0, G


def two_beam_reflection(theta_rad, energy_keV, V0_V, Vg_list, g_per_A, absorption_ratio, *,
                        order: int, form: str, plane_offset_A: float = 0.0):
    """Two-beam R(theta) for the harmonic `order` of g_per_A (report section 3).

    form 'bloch_matched' (closed form, DERIVED_HERE): kappa = G/2 + delta with
        delta^2 = 2 (eps^2 - U_g U_-g) / [(2 eps + G^2) + sqrt(G^4 + 4 eps G^2 + 4 U_g U_-g)],
        rho = c_1/c_0 = -U_g / (eps + G delta - delta^2),
        R = [(K - G/2 - delta) + rho (K + G/2 - delta)] / [(K + G/2 + delta) + rho (K - G/2 + delta)],
    delta chosen with Im delta > 0, or for real delta with flux -(G/2 + delta) + (G/2 - delta)|rho|^2 < 0.
    form 'darwin' (Takagi-Taupin limit; no step reflection, delta^2 and the prefactor refraction
    dropped): R = -U_g / (eps + S), S = sqrt(eps^2 - U_g U_-g) with Im S > 0, or for real S the root
    giving |R| < 1; equivalently R = -(U_g/sqrt(U_g U_-g)) (eta - sqrt(eta^2 - 1)).
    form 'darwin_refracted': the 'bloch_matched' formula with delta -> 0 in the prefactors,
    R = (r_F + rho_D) / (1 + r_F rho_D), rho_D the 'darwin' amplitude and r_F = (K - q)/(K + q),
    q = sqrt(K^2 + U_0), the Fresnel coefficient of the mean-potential step (report section 3.2)."""
    bc = beam_constants(energy_keV)
    Vg = tuple(float(v) for v in np.atleast_1d(Vg_list))
    slab = Slab(float(V0_V), Vg, float(g_per_A), float(absorption_ratio), float(plane_offset_A))
    th = np.atleast_1d(np.asarray(theta_rad, float))
    out = []
    for t in th:
        out.append(_two_beam_R_K(bc["k"] * np.sin(t), slab, bc, order, form))
    out = np.array(out)
    return complex(out[0]) if np.ndim(theta_rad) == 0 else out


def _two_beam_R_K(K, slab, bc, order, form):
    eps, Ug, Umg, U0, G = _two_beam_parts(K, slab, bc, order)
    P = Ug * Umg
    if form == "darwin_refracted":
        rho = _two_beam_R_K(K, slab, bc, order, "darwin")
        q = np.sqrt(K**2 + U0 + 0j)
        if q.imag < 0:
            q = -q
        rF = (K - q) / (K + q)
        return (rF + rho) / (1.0 + rF * rho)
    if form == "darwin":
        S = np.sqrt(eps**2 - P + 0j)
        cands = []
        for s in (S, -S):
            with np.errstate(invalid="ignore", divide="ignore"):     # 0/0 only when U_g = 0
                rho = -Ug / (eps + s)
            dec = (s / G).imag
            if abs(dec) > 1e-12 * abs(G):
                phys = dec > 0
            else:
                phys = abs(rho) < 1.0
            if phys:
                cands.append(rho)
        if len(cands) != 1:
            cands = sorted([-Ug / (eps + S), -Ug / (eps - S)], key=abs)[:1]
        return cands[0]
    if form != "bloch_matched":
        raise ValueError("form must be 'bloch_matched', 'darwin' or 'darwin_refracted'")
    root = np.sqrt(G**4 + 4 * eps * G**2 + 4 * P + 0j)
    d2 = 2.0 * (eps**2 - P) / ((2 * eps + G**2) + root)
    dl = np.sqrt(d2 + 0j)
    best = []
    for d in (dl, -dl):
        rho = -Ug / (eps + G * d - d**2)
        if abs(d.imag) > 1e-12 * G:
            phys = d.imag > 0
        else:
            phys = (-(G / 2 + d.real) + (G / 2 - d.real) * abs(rho) ** 2) < 0
        if phys:
            best.append((d, rho))
    if len(best) != 1:
        # degenerate only for U_g = 0 (decoupled waves): keep the downward wave kappa = q
        q0 = np.sqrt(K**2 + U0 + 0j)
        best = sorted(best, key=lambda b: abs((G / 2 + b[0]) - q0))[:1]
        if not best or abs(Ug) > 0:
            raise RuntimeError("two-beam root selection ambiguous")
    d, rho = best[0]
    num = (K - G / 2 - d) + rho * (K + G / 2 - d)
    den = (K + G / 2 + d) + rho * (K - G / 2 + d)
    return num / den


def darwin_plateau(energy_keV, V0_V, Vg_V, g_per_A, *, order: int = 1) -> dict:
    """Two-beam (Darwin) plateau of the reflection `order` without absorption (report 3.3):
    centre K_c^2 = G^2/4 - U_0, edges K^2 = K_c^2 -+ |U_g|, external angles theta = asin(K/k);
    extinction (amplitude) depth at the centre 1/Im(kappa) = G/|U_g|; coupling kc = sigma |V_g|
    (rad/A) and extinction distance along z xi_g = pi / (sigma |V_g|)."""
    bc = beam_constants(energy_keV)
    G = order * TWO_PI * g_per_A
    U0 = 2 * bc["k"] * bc["sigma"] * V0_V
    Ug = 2 * bc["k"] * bc["sigma"] * abs(Vg_V)
    Kc = np.sqrt(G**2 / 4 - U0)
    Klo, Khi = np.sqrt(G**2 / 4 - U0 - Ug), np.sqrt(G**2 / 4 - U0 + Ug)
    th = lambda K: float(np.arcsin(K / bc["k"]))  # noqa: E731
    kc = bc["sigma"] * abs(Vg_V)
    return dict(G=G, U0=U0, Ug=Ug, K_centre=Kc, K_low=Klo, K_high=Khi,
                theta_centre=th(Kc), theta_low=th(Klo), theta_high=th(Khi),
                width_theta=th(Khi) - th(Klo), extinction_depth_A=G / Ug,
                kc=kc, z_per_efold_A=1.0 / kc, xi_g_A=np.pi / kc,
                theta_int_centre=float(np.arcsin((G / 2) / np.sqrt(bc["k"]**2 + U0))))


def theta_of_eta(eta, energy_keV, V0_V, Vg_V, g_per_A, *, order: int = 1):
    """External angle for the (real, r = 0) Darwin deviation parameter eta."""
    p = darwin_plateau(energy_keV, V0_V, Vg_V, g_per_A, order=order)
    bc = beam_constants(energy_keV)
    K2 = p["K_centre"] ** 2 + np.asarray(eta, float) * p["Ug"]
    return np.arcsin(np.sqrt(K2) / bc["k"])


def exact_band_edges(energy_keV, V0_V, Vg_list, g_per_A, *, order: int, plane_offset_A=0.0):
    """Exact gap edges (r = 0) of the harmonic `order`: trace of the one-period monodromy equals
    2 (-1)^order (Floquet multiplier (-1)^order at kappa d = order pi), bracketed around the
    two-beam edges. Returns (theta_low, theta_high) (rad)."""
    bc = beam_constants(energy_keV)
    Vg = tuple(float(v) for v in np.atleast_1d(Vg_list))
    slab = Slab(float(V0_V), Vg, float(g_per_A), 0.0, float(plane_offset_A))
    U = slab.U_coeffs(bc, klein_gordon_V2=False)
    target = 2.0 * (-1) ** order
    p = darwin_plateau(energy_keV, V0_V, Vg[order - 1], g_per_A, order=order)

    def f(K2):
        return float(np.trace(monodromy(np.sqrt(K2), U, slab.G_f)).real) - target
    # scan +-4 |U_g| around the two-beam centre: the gap is where (-1)^order tr M > 2
    xs = p["K_centre"] ** 2 + np.linspace(-4.0, 4.0, 161) * p["Ug"]
    fs = np.array([f(x) for x in xs])
    roots = [optimize.brentq(f, xs[i], xs[i + 1], xtol=1e-15, rtol=1e-15)
             for i in range(len(xs) - 1) if fs[i] * fs[i + 1] < 0]
    if len(roots) != 2:
        raise RuntimeError(f"expected two band edges, found {len(roots)}")
    out = [float(np.arcsin(np.sqrt(r_) / bc["k"])) for r_ in roots]
    return tuple(out)


# =================================================================================================
# 5. Build-up transient along the surface
# =================================================================================================

def build_up_two_beam(Z_A, theta_rad, energy_keV, V0_V, Vg_V, g_per_A, absorption_ratio, *,
                      order: int = 1, plane_offset_A: float = 0.0):
    """Two-beam (Darwin/Takagi-Taupin) reflected amplitude A(Z) at distance Z (A) downstream of a
    SHARP leading edge of the illumination on the surface (report section 5.1, DERIVED_HERE):

        A(Z) = i ph int_0^Z (J_1(kc tau) / tau) exp(i (E_K - E_B) tau) d tau,   A(inf) = R_darwin,

    E = K^2/(2k) the paraxial 'energy' (rad/A), E_B = (G^2/4 - U_0)/(2k), kc = sqrt(U_g U_-g)/(2k)
    (= sigma V_g (1 + i r)), ph = U_g / sqrt(U_g U_-g). Evaluated by composite Simpson integration."""
    bc = beam_constants(energy_keV)
    slab = Slab(float(V0_V), (float(Vg_V),) if order == 1 else tuple(
        [0.0] * (order - 1) + [float(Vg_V)]), float(g_per_A), float(absorption_ratio),
        float(plane_offset_A))
    K = bc["k"] * np.sin(theta_rad)
    eps, Ug, Umg, U0, G = _two_beam_parts(K, slab, bc, order)
    sq = np.sqrt(Ug * Umg + 0j)
    ph = Ug / sq
    kc = sq / (2 * bc["k"])
    dE = (K**2 - (G**2 / 4 - U0)) / (2 * bc["k"])     # E_K - E_B (complex with absorption)
    Z = np.atleast_1d(np.asarray(Z_A, float))
    Zmax = float(Z.max())
    n = int(np.ceil(Zmax / 2.0)) * 2 + 1                # 1 A spacing at most (integrand period >= 4000 A)
    tau = np.linspace(0.0, Zmax, max(n, 3))
    x = kc * tau
    f = np.where(tau > 0, special.jv(1, x) / np.where(tau > 0, tau, 1.0), kc / 2.0) * np.exp(
        1j * dE * tau)
    cum = integrate.cumulative_simpson(f, x=tau, initial=0.0)
    A = 1j * ph * (np.interp(Z, tau, cum.real) + 1j * np.interp(Z, tau, cum.imag))
    return A if np.ndim(Z_A) else complex(A[0])


def build_up_length(theta_rad, energy_keV, V0_V, Vg_V, g_per_A, absorption_ratio, *, tols,
                    order: int = 1, Z_max_A: float = 4.0e5):
    """Build-up lengths in the two-beam model with a sharp leading edge (report 5.1): for each
    (kind, tol) in tols, kind 'abs' (|A(Z) - R| <= tol) or 'phase' (|arg(A(Z)/R)| <= tol), the
    smallest Z beyond which the criterion holds for every computed Z up to Z_max_A (inf if it
    fails at Z_max_A). Returns (list of Z, R_darwin)."""
    Z = np.linspace(0.0, Z_max_A, int(Z_max_A / 20.0) + 1)
    A = build_up_two_beam(Z, theta_rad, energy_keV, V0_V, Vg_V, g_per_A, absorption_ratio,
                          order=order)
    R = two_beam_reflection(theta_rad, energy_keV, V0_V, [0.0] * (order - 1) + [Vg_V], g_per_A,
                            absorption_ratio, order=order, form="darwin")
    out = []
    for kind, tol in tols:
        err = np.abs(A - R) if kind == "abs" else np.abs(np.angle(A / R))
        bad = np.nonzero(err > tol)[0]
        if len(bad) == 0:
            out.append(0.0)
        elif bad[-1] == len(Z) - 1:
            out.append(float("inf"))
        else:
            out.append(float(Z[bad[-1] + 1]))
    return out, R


def step_response_fft(theta_rad, energy_keV, V0_V, Vg_list, g_per_A, absorption_ratio, *,
                      switch_width_A: float, R_of_K, T_A: float = 2.0e5, n_pts: int = 2048):
    """Step response A(Z) for a SMOOTH leading edge S(z) = (1 + erf(z/w))/2 (w = switch_width_A) from
    any R(K) (report section 5.2, DERIVED_HERE): the incident signal at the surface is
    S(z) exp(-i E_K z), E = K^2/(2k); by causality R(E) is analytic for Im E > 0 and
        A(Z) = exp(gamma Z) (1/2 pi) int R(E_K + w' + i gamma) S^(w' + i gamma) exp(-i w' Z) dw',
        S^(w) = (i/w) exp(-w^2 w_s^2/4),
    evaluated by an FFT with period T_A (aliasing ~ exp(-gamma T_A), gamma T_A = 25).
    R_of_K(K) must accept complex K. Returns (Z, A) for 0 <= Z < T_A/2."""
    bc = beam_constants(energy_keV)
    k = bc["k"]
    K0 = k * np.sin(theta_rad)
    EK = K0**2 / (2 * k)
    gamma = 25.0 / T_A
    dw = TWO_PI / T_A
    j = np.arange(n_pts)
    w = (j - n_pts // 2) * dw
    if abs(w[0]) >= EK:
        raise ValueError("FFT window reaches E <= 0; reduce n_pts or increase T_A")
    wc = w + 1j * gamma
    Kc = np.sqrt(2 * k * (EK + wc))
    Rv = np.array([R_of_K(Kx) for Kx in Kc])
    Sh = 1j / wc * np.exp(-(wc**2) * switch_width_A**2 / 4.0)
    F = Rv * Sh
    l = np.arange(n_pts)
    Z = TWO_PI * l / (n_pts * dw)
    A = np.exp(gamma * Z) * (dw / TWO_PI) * ((-1.0) ** l) * np.fft.fft(F)
    keep = Z < T_A / 2
    return Z[keep], A[keep]


def split_step_1d(*, theta0_rad, V0_V, Vg_V, g_per_A, absorption_ratio, propagator, dx_A, dz_A,
                  H_A, edge_A, gap_A, clean_depth_A, exit_after_top_contact_A, extra_vacuum_A,
                  absorber_A=15.0, top_absorber_A=10.0, W0_V=100.0, entrance_A=10.0,
                  rel_threshold=0.05, readout_window_above_A=None):
    """MINIMAL INDEPENDENT 1D split-step (NOT the engine; report section 7): written here from the
    engine's documented scheme to check the claims of report sections 4 and 5 and the proposed test
    protocol before the engine is run. Symmetric split step P(dz/2) T ... T P(dz/2); P Fresnel
    exp(-i pi lambda dz f^2) or 'exact' exp(i dz (sqrt(k^2 - (2 pi f)^2) - k)), both times the 2/3
    band mask; T = BL[exp(i sigma V dz) exp(-sigma W dz)], V = (1 + i r) frac_j [V0 + 2 Vg
    cos(2 pi g (x_j - x_s))] (point-sampled harmonic times the cell-averaged crystal fraction of
    pixel j), zero for z < entrance_A; sin^2 absorbers W0 at the bottom (inside the crystal) and the
    top. Sheet beam of height H (sin^2 edges), bottom gap_A above x_s at z = 0, tilt -sin(theta0)/
    lambda, projected onto f < 0. Read-out as the engine's flat_reflection_coefficient: r(f) =
    Psi_L(+f) exp(+i 4 pi f x_s) / (Psi_0(-f) P_L(f)) for bins with |Psi_0(-f)| >= rel_threshold max.
    readout_window_above_A = w0: additionally returns r_win, the same read-out after multiplying the
    exit wave by w(x) = sin^2(pi/2 clip((x - x_s - w0)/40 A, 0, 1)) (vacuum-only read-out that drops
    the field left near and below the surface; report section 8).
    Returns dict(theta_bins, r, [r_win,] weight, n_x, n_slices, L_A, dx_A)."""
    bc = beam_constants(200.0)
    lam, k, sigma = bc["wavelength_A"], bc["k"], bc["sigma"]
    th0 = float(theta0_rad)
    x_s = absorber_A + clean_depth_A
    z_top = (gap_A + H_A) / np.tan(th0)
    L = float(np.ceil((z_top + exit_after_top_contact_A) / dz_A) * dz_A)
    vac = H_A + gap_A + L * np.tan(th0) + extra_vacuum_A
    ext = x_s + vac + top_absorber_A
    nx = int(np.ceil(ext / dx_A / 2.0)) * 2
    dx = ext / nx
    x = np.arange(nx) * dx
    f = np.fft.fftfreq(nx, dx)
    frac = np.clip((x_s - (x - 0.5 * dx)) / dx, 0.0, 1.0)
    V = frac * (V0_V + 2.0 * Vg_V * np.cos(TWO_PI * g_per_A * (x - x_s))) * (1 + 1j * absorption_ratio)
    W = np.zeros(nx)
    b = x < absorber_A
    W[b] = W0_V * np.sin(0.5 * np.pi * (absorber_A - x[b]) / absorber_A) ** 2
    t0 = ext - top_absorber_A
    tp = x > t0
    W[tp] = W0_V * np.sin(0.5 * np.pi * (x[tp] - t0) / top_absorber_A) ** 2
    mask = np.abs(f) <= (2.0 / 3.0) / (2.0 * dx)

    def P(d):
        if propagator == "fresnel":
            ph = -np.pi * lam * d * f**2
        else:
            q2 = (TWO_PI * f) ** 2
            ph = d * (-q2 / (k + np.sqrt(np.maximum(k**2 - q2, 0.0))))
        return np.exp(1j * ph) * mask
    t_cr = np.fft.ifft(np.fft.fft(np.exp(1j * sigma * V * dz_A) * np.exp(-sigma * W * dz_A)) * mask)
    t_va = np.fft.ifft(np.fft.fft(np.exp(-sigma * W * dz_A) + 0j) * mask)
    xb = x_s + gap_A
    A = np.zeros(nx)
    core = (x >= xb + edge_A) & (x <= xb + H_A - edge_A)
    A[core] = 1.0
    lo = (x > xb) & (x < xb + edge_A)
    A[lo] = np.sin(0.5 * np.pi * (x[lo] - xb) / edge_A) ** 2
    hi = (x > xb + H_A - edge_A) & (x < xb + H_A)
    A[hi] = np.sin(0.5 * np.pi * (xb + H_A - x[hi]) / edge_A) ** 2
    spec0 = np.fft.fft(A * np.exp(-2j * np.pi * np.sin(th0) / lam * x))
    spec0[f >= 0] = 0.0
    psi0 = np.fft.ifft(spec0)
    N = int(round(L / dz_A))
    Pf, Ph = P(dz_A), P(0.5 * dz_A)
    psi = np.fft.ifft(np.fft.fft(psi0) * Ph)
    for i in range(N):
        psi = psi * (t_cr if (i + 0.5) * dz_A >= entrance_A else t_va)
        psi = np.fft.ifft(np.fft.fft(psi) * (Pf if i < N - 1 else Ph))
    out = np.fft.fft(psi)
    if readout_window_above_A is not None:
        win = np.sin(0.5 * np.pi * np.clip((x - x_s - readout_window_above_A) / 40.0, 0.0, 1.0)) ** 2
        out_w = np.fft.fft(psi * win)
    PL = P(L)
    thr = rel_threshold * np.abs(spec0).max()
    th_b, rr_, rw_, w_ = [], [], [], []
    for m in range(1, nx // 2):
        mi = (-m) % nx
        if abs(spec0[mi]) < thr or not mask[m]:
            continue
        fac = np.exp(4j * np.pi * f[m] * x_s) / (spec0[mi] * PL[mi])
        rr_.append(out[m] * fac)
        if readout_window_above_A is not None:
            rw_.append(out_w[m] * fac)
        th_b.append(float(np.arcsin(f[m] * lam)))
        w_.append(float(abs(spec0[mi])))
    res = dict(theta_bins=np.array(th_b), r=np.array(rr_), weight=np.array(w_), n_x=nx,
               n_slices=N, L_A=L, dx_A=dx)
    if readout_window_above_A is not None:
        res["r_win"] = np.array(rw_)
    return res


# =================================================================================================
# 6. Engine potential: laterally averaged Kirkland potential of a flat Si(001) cell
# =================================================================================================

def engine_potential_harmonics(*, dx_A: float, n_fit: int = 60, layers: int = 41,
                               ny: int = 32) -> dict:
    """Build a flat bulk-terminated Si(001) terrace with the repository's builder
    (reflection_holo.structure.build_si001_terraces, [110] azimuth, one in-plane period), wrap it in a
    reflection cell (reflection_holo.forward.cell.build_reflection_cell), realise the ENGINE'S
    AtomicPotential (Kirkland, abTEM 1.0.10 scattering factors) slice by slice on a grid of pixel
    ~dx_A, average over y and z, and least-squares fit V0 + sum_n 2 V_n cos(2 pi n x'/(a/4)) +
    2 W_n sin(...) over 16 layer periods in the bulk (x' from an atomic plane). Also returns the
    analytic 8 F(f^2)/a^3 from the engine's own scattering factor. Lazy imports (abTEM optional)."""
    from reflection_holo.forward.cell import build_reflection_cell
    from reflection_holo.forward.multislice import AtomicPotential, PhysicalAbsorption, make_grid
    from reflection_holo.forward.multislice.backend import get_backend
    from reflection_holo.structure import Staircase, build_si001_terraces
    a = A_SI_A
    p = a / np.sqrt(2.0)
    q = a / 4.0
    st = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(1,),
                   boundary_step_layers=0)
    s = build_si001_terraces(azimuth_uvw=(1, 1, 0),
                             azimuth_label="TEST_ONLY: flat cell for the rung-2 potential analysis",
                             staircase=st, edge_periods=1, substrate_layers=layers,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=a,
                             lattice_parameter_label="ASSUMPTION B2")
    cell = build_reflection_cell(s, vacuum_above_A=20.0, depth_below_A=(layers - 1) * q,
                                 bulk_absorber_A=5.0, top_absorber_A=5.0, entrance_vacuum_z_A=p / 4)
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(
                              model="proportional", ratio=0.0,
                              label="TEST_ONLY: real potential for the Fourier analysis"),
                          frozen_phonons=None,
                          static_lattice_label="ASSUMPTION: static lattice (engine default model)")
    nx = int(np.ceil(cell.extent_x_A / dx_A))
    grid = make_grid(cell, nx=nx, ny=ny)
    dz = p / 4
    N = int(round(cell.length_z_A / dz))
    be = get_backend("numpy", "complex128", 1)
    real = pot.realise(grid=grid, dz_A=dz, n_slices=N, backend=be, rng=None)
    acc = np.zeros(nx)
    for i in range(N):
        acc += np.asarray(real.projected(i).real).mean(axis=1)
    Vbar = acc / (cell.length_z_A - cell.crystal_start_z_A)
    x = grid.x_A()
    xl = 20 * q                                  # an atomic plane in the bulk (layer 20 of 0..40)
    m = (x >= 12 * q) & (x < 28 * q)
    xr = x[m] - xl
    cols = [np.ones_like(xr)]
    for n in range(1, n_fit + 1):
        cols += [np.cos(TWO_PI * n * xr / q), np.sin(TWO_PI * n * xr / q)]
    Amat = np.array(cols).T
    c, *_ = np.linalg.lstsq(Amat, Vbar[m], rcond=None)
    res = Vbar[m] - Amat @ c
    V0 = float(c[0])
    Vn = np.array([c[2 * n - 1] / 2 for n in range(1, n_fit + 1)])
    Wn = np.array([c[2 * n] / 2 for n in range(1, n_fit + 1)])
    F = lambda f: float(pot.scattering_factor(14, np.array([f * f]))[0])  # noqa: E731
    analytic = np.array([8.0 * F(4 * n / a) / a**3 for n in range(0, n_fit + 1)])
    return dict(V0=V0, Vn=Vn, Wn=Wn, analytic=analytic, mip=pot.mean_inner_potential_V(),
                rms_residual=float(np.sqrt(np.mean(res**2))), dx=grid.dx_A, nx=nx,
                n_atoms=int(len(cell.Z)), surface_x=cell.surface_x_A)


# =================================================================================================
# 7. main: every number of the report, with self-checks
# =================================================================================================

_CHECKS = []


def _fmt(v):
    v = complex(v)
    return f"{v.real:.10g}" if v.imag == 0 else f"({v.real:.10g}{v.imag:+.10g}j)"


def check(name, got, want, tol, *, rel=False):
    err = abs(got - want) / (abs(want) if rel else 1.0)
    ok = bool(err <= tol)
    _CHECKS.append((name, ok))
    print(f"   CHECK {'PASS' if ok else 'FAIL'}  {name}: got {_fmt(got)} want {_fmt(want)} "
          f"err {err:.3e} tol {tol:.1e}{' (relative)' if rel else ''}")
    return ok


def check_true(name, cond, detail=""):
    _CHECKS.append((name, bool(cond)))
    print(f"   CHECK {'PASS' if cond else 'FAIL'}  {name} {detail}")


def rule(t):
    print("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)


def wrap(p):
    return (np.asarray(p) + np.pi) % TWO_PI - np.pi


def main() -> int:  # noqa: C901 (a linear report script)
    E = 200.0
    a = A_SI_A
    bc = beam_constants(E)
    rule("1. Beam constants (reflection_holo.constants only) and cross-checks against the package")
    print(f"lambda = {bc['wavelength_A']:.8f} A, k = {bc['k']:.4f} rad/A, sigma = "
          f"{bc['sigma']:.6e} rad/(V A), gamma = {bc['gamma']:.6f}, hbar c = {HBARC_EV_A:.4f} eV A")
    from reflection_holo.forward.multislice.physics import interaction_constant_rad_per_VA
    from reflection_holo.geometry.refraction import delta_K_per_A, refraction_delta
    from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A
    check("lambda vs reflection_holo.geometry.wavelength", bc["wavelength_A"], wavelength_A(E),
          1e-14, rel=True)
    check("lambda vs physics_conventions 0.02507934 A", bc["wavelength_A"], 0.02507934, 5e-9)
    check("k vs reflection_holo.geometry.wavelength", bc["k"], k_ang_per_A(E), 1e-14, rel=True)
    check("sigma vs engine physics.interaction_constant", bc["sigma"],
          interaction_constant_rad_per_VA(E), 1e-14, rel=True)
    try:
        beam_constants(300.0)
        check_true("300 keV refused", False)
    except ValueError:
        check_true("300 keV refused", True)

    # ---------------------------------------------------------------------------------------------
    rule("2. Engine potential: laterally averaged Kirkland potential of a flat Si(001) cell")
    pots = {}
    for dxp in (0.01, 0.02):
        r = engine_potential_harmonics(dx_A=dxp)
        pots[dxp] = r
        print(f"dx = {r['dx']:.5f} A, nx = {r['nx']}, {r['n_atoms']} atoms, fit rms residual "
              f"{r['rms_residual']:.2e} V; MIP (8 F(0)/a^3) = {r['mip']:.6f} V; fitted V0 = "
              f"{r['V0']:.6f} V")
        for n in range(1, 7):
            print(f"   (0,0,{4 * n:2d}): f = {4 * n / a:.5f} 1/A  V_n(fit) = {r['Vn'][n - 1]:.6f} V  "
                  f"W_n(sine) = {r['Wn'][n - 1]:+.1e} V  8F(f^2)/a^3 = {r['analytic'][n]:.6f} V")
    P = pots[0.01]
    V0 = float(P["mip"])
    V004, V008, V012, V016 = (float(P["analytic"][n]) for n in (1, 2, 3, 4))
    Vn_all = [float(v) for v in P["analytic"][1:13]]      # (0,0,4) ... (0,0,48)
    for dxp, r in pots.items():
        check(f"fitted V_008 vs analytic 8F/a^3 (dx {dxp})", r["Vn"][1], r["analytic"][2], 1e-4)
        check(f"fitted V0 vs MIP (dx {dxp})", r["V0"], r["mip"], 1e-4)
        check(f"sine term of (0,0,8) vanishes (dx {dxp})", r["Wn"][1], 0.0, 1e-5)
    check("MIP 13.903 V (M2, D3 F16)", V0, 13.903, 5e-4)
    print(f"USED: V0 = {V0:.6f} V, V_004 = {V004:.6f} V, V_008 = {V008:.6f} V, V_012 = {V012:.6f} V,"
          f" V_016 = {V016:.6f} V (static lattice, independent atoms; ASSUMPTION of the engine)")

    g8 = 8.0 / a                   # cycles/A: (0,0,8) as the fundamental of a single harmonic
    g4 = 4.0 / a                   # fundamental of the full layer potential (period a/4)
    G8 = TWO_PI * g8
    print(f"(0,0,8): g = 8/a = {g8:.6f} cycles/A, G = 2 pi g = {G8:.6f} rad/A, d = a/8 = "
          f"{1 / g8:.6f} A; (0,0,4) fundamental g = {g4:.6f} cycles/A")

    # ---------------------------------------------------------------------------------------------
    rule("3. Two-beam plateau parameters of (0,0,8) (r = 0) and exact band edges")
    p = darwin_plateau(E, V0, V008, g8)
    print(f"U_0 = 2 k sigma V0 = {p['U0']:.6f} rad^2/A^2, |U_g| = {p['Ug']:.6f} rad^2/A^2")
    print(f"centre: K_c = {p['K_centre']:.6f} rad/A, theta_ext = {p['theta_centre'] * 1e3:.5f} mrad"
          f" (theta_int = {p['theta_int_centre'] * 1e3:.5f} mrad)")
    print(f"two-beam edges: {p['theta_low'] * 1e3:.5f} to {p['theta_high'] * 1e3:.5f} mrad, width "
          f"{p['width_theta'] * 1e3:.5f} mrad = {p['width_theta'] * 1e6:.2f} urad")
    print(f"extinction (amplitude) depth at the centre G/|U_g| = {p['extinction_depth_A']:.3f} A;"
          f" coupling kc = sigma V_g = {p['kc']:.6e} rad/A; 1/kc = {p['z_per_efold_A']:.1f} A along z;"
          f" xi_g = pi/(sigma V_g) = {p['xi_g_A']:.1f} A")
    print(f"closed-form width 2 sigma V_g / K_c = {2 * bc['sigma'] * V008 / p['K_centre'] * 1e6:.2f} urad "
          f"(= 2 kc in E-units: {2 * p['kc']:.4e} rad/A); Darwin phase slope at the centre "
          f"d(arg R)/d(theta) = K_c/(sigma V_g) = {p['K_centre'] / (bc['sigma'] * V008) * 1e-3:.3f} rad/mrad;"
          f" d(arg R)/dV0 = 1/V_g = {1 / V008:.4f} rad/V; d(arg R)/dV_g = 0 at the centre")
    Kc_ = p["K_centre"]
    print(f"derived quantities quoted in the report: U_g/G^2 = {p['Ug'] / G8**2:.3e}; K_c^2/(4 k^2) = "
          f"{Kc_**2 / (4 * bc['k']**2):.2e} (paraxial vs exact z-dispersion); 2 q_c = {G8:.3f} rad/A "
          f"(momentum a smooth absorber ramp must supply for V_g = 0); at eta = 3 the Bloch waves differ"
          f" by 2 delta = {2 * p['Ug'] * np.sqrt(8.0) / G8:.4f} rad/A (beat length pi/delta = "
          f"{np.pi / (p['Ug'] * np.sqrt(8.0) / G8):.1f} A); sinc(pi g dx) = {np.sinc(g8 * 0.025):.5f} "
          f"(dx 0.025 A), {np.sinc(g8 * 0.05):.5f} (dx 0.05 A); sheet-beam edge along z e/tan(theta_c) = "
          f"{2.0 / np.tan(p['theta_centre']):.0f} to {8.0 / np.tan(p['theta_centre']):.0f} A for e = 2 to 8 A;"
          f" top-edge contact of the test beam z_top = (2 + 24 A)/tan(theta_c) = "
          f"{26.0 / np.tan(p['theta_centre']):.1f} A; V_008/0.84 V - 1 = {V008 / 0.84 - 1:+.3f} (M2 estimate)")
    from reflection_holo.geometry.specular import specular_condition_for
    sc = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E, V0_V=V0, a_A=a)
    print(f"package specular_condition_for((0,0,8)) theta_ext = {sc.theta_ext * 1e3:.6f} mrad "
          f"(exact SM04 Delta incl. V0^2 term)")
    check("TT centre vs package specular condition", p["theta_centre"], sc.theta_ext, 1e-7)
    ex_lo, ex_hi = exact_band_edges(E, V0, [V008], g8, order=1)
    ex_c = 0.5 * (ex_lo + ex_hi)
    print(f"EXACT band edges (single harmonic): {ex_lo * 1e3:.5f} to {ex_hi * 1e3:.5f} mrad, width "
          f"{(ex_hi - ex_lo) * 1e6:.3f} urad, midpoint {ex_c * 1e3:.5f} mrad; shifts vs two-beam: "
          f"low {(ex_lo - p['theta_low']) * 1e6:+.3f} urad, high {(ex_hi - p['theta_high']) * 1e6:+.3f} urad")
    mh_lo, mh_hi = exact_band_edges(E, V0, Vn_all, g4, order=2)
    print(f"full layer potential vs single harmonic: width change {((mh_hi - mh_lo) / (ex_hi - ex_lo) - 1) * 100:+.1f} %,"
          f" midpoint shift {(0.5 * (mh_lo + mh_hi) - ex_c) * 1e6:+.2f} urad = "
          f"{(0.5 * (mh_lo + mh_hi) - ex_c) / (ex_hi - ex_lo) * 100:+.1f} % of the single-harmonic width")
    print(f"EXACT band edges (full layer potential, harmonics (0,0,4)...(0,0,48)): {mh_lo * 1e3:.5f} to"
          f" {mh_hi * 1e3:.5f} mrad, width {(mh_hi - mh_lo) * 1e6:.3f} urad, midpoint "
          f"{0.5 * (mh_lo + mh_hi) * 1e3:.5f} mrad")

    # ---------------------------------------------------------------------------------------------
    rule("4. Exact solver cross-checks (r = 0, 0.05, 0.1)")
    thetas_chk = [theta_of_eta(e, E, V0, V008, g8) for e in (-2.0, -0.95, 0.0, 0.6, 1.5)]
    for rr in (0.0, 0.05, 0.1):
        worst_bf, worst_conv = 0.0, 0.0
        for th in thetas_chk:
            Rb = reflection_amplitude(th, E, V0, [V008], g8, rr, method="bloch")
            Rf = reflection_amplitude(th, E, V0, [V008], g8, rr, method="floquet")
            Rb4 = reflection_amplitude(th, E, V0, [V008], g8, rr, method="bloch", n_plane_waves=4)
            worst_bf = max(worst_bf, abs(Rb - Rf))
            worst_conv = max(worst_conv, abs(Rb - Rb4))
        print(f"r = {rr}: max |R_bloch(M=8) - R_floquet| = {worst_bf:.2e}; max |R(M=8) - R(M=4)| = "
              f"{worst_conv:.2e}")
        check(f"Bloch vs Floquet-ODE, single harmonic, r = {rr}", worst_bf, 0.0, 1e-9)
        check(f"plane-wave convergence M=4 vs 8, r = {rr}", worst_conv, 0.0, 1e-9)
    # multi-harmonic convergence
    worst = 0.0
    for th in thetas_chk[1:4]:
        R1 = reflection_amplitude(th, E, V0, Vn_all, g4, 0.0, method="bloch", n_plane_waves=48)
        R2 = reflection_amplitude(th, E, V0, Vn_all, g4, 0.0, method="bloch", n_plane_waves=24)
        R3 = reflection_amplitude(th, E, V0, Vn_all, g4, 0.0, method="floquet")
        worst = max(worst, abs(R1 - R2), abs(R1 - R3))
    print(f"full layer potential (12 harmonics): max |R(M=48) - R(M=24)|, |R(M=48) - R_floquet| = "
          f"{worst:.2e}")
    check("multi-harmonic Bloch M=24/48 vs Floquet", worst, 0.0, 1e-8)
    # finite depth (independent: no Floquet selection)
    for rr, D in ((0.05, 600.0), (0.1, 400.0)):
        worst = 0.0
        for th in thetas_chk:
            Rb = reflection_amplitude(th, E, V0, [V008], g8, rr)
            Rd = reflection_amplitude(th, E, V0, [V008], g8, rr, method="depth", depth_A=D)
            worst = max(worst, abs(Rb - Rd))
        print(f"r = {rr}: finite crystal D = {D:.0f} A on a uniform substrate vs semi-infinite: max "
              f"|dR| = {worst:.2e}")
        check(f"finite depth -> semi-infinite, r = {rr}", worst, 0.0, 1e-7)
    th0 = thetas_chk[2]
    Rb = reflection_amplitude(th0, E, V0, [V008], g8, 0.0)
    for D in (100.0, 200.0, 400.0):
        Rd = reflection_amplitude(th0, E, V0, [V008], g8, 0.0, method="depth", depth_A=D)
        print(f"r = 0, plateau centre, D = {D:.0f} A: |R_D - R_inf| = {abs(Rd - Rb):.2e} "
              f"(expected ~ exp(-2 D / {p['extinction_depth_A']:.2f} A) = "
              f"{np.exp(-2 * D / p['extinction_depth_A']):.1e})")
    Rd = reflection_amplitude(th0, E, V0, [V008], g8, 0.0, method="depth", depth_A=400.0)
    check("r = 0 plateau centre: finite depth 400 A = semi-infinite", abs(Rd - Rb), 0.0, 1e-9)
    thb = thetas_chk[4]
    Rbb = reflection_amplitude(thb, E, V0, [V008], g8, 0.0)
    dd = [abs(reflection_amplitude(thb, E, V0, [V008], g8, 0.0, method="depth", depth_A=D) - Rbb)
          for D in (300.0, 301.0, 302.0, 303.0, 600.0, 601.0)]
    print(f"r = 0, eta = 1.5 (band, propagating): |R_D - R_inf| for D = 300..303, 600, 601 A: "
          + ", ".join(f"{v:.3f}" for v in dd) + "  (no convergence without absorption)")
    # infinitesimal absorption limit
    worst = 0.0
    for th in thetas_chk:
        worst = max(worst, abs(reflection_amplitude(th, E, V0, [V008], g8, 0.0)
                               - reflection_amplitude(th, E, V0, [V008], g8, 1e-10)))
    check("r = 0 selection equals the r -> 0+ limit", worst, 0.0, 1e-7)

    # ---------------------------------------------------------------------------------------------
    rule("5. Limits: Fresnel step (rung 1), unitarity, two-beam basis, Darwin form")
    from reflection_holo.forward.multislice.analysis import analytic_step_reflection
    for thr in (10e-3, 16.47e-3, 30e-3):
        K = bc["k"] * np.sin(thr)
        R0 = reflection_amplitude(thr, E, 12.0, [0.0], g8, 0.0)
        q = np.sqrt(K**2 + 2 * bc["k"] * bc["sigma"] * 12.0)
        rF = (K - q) / (K + q)
        rM2 = analytic_step_reflection(np.array([K]), delta_K_per_A(E, 12.0))[0]
        print(f"V_g = 0, V0 = 12 V, {thr * 1e3:.2f} mrad: R = {R0.real:+.6f}{R0.imag:+.1e}i; "
              f"(K-q)/(K+q) = {rF:+.6f}; M2 analytic (SM04 dK) = {rM2:+.6f}")
        check(f"Fresnel limit at {thr * 1e3:.2f} mrad", R0, rF, 1e-12)
        check(f"rung-1 analytic (SM04 dK incl. V0^2) at {thr * 1e3:.2f} mrad", R0.real, rM2, 1e-5)
    # unitarity
    ths = theta_of_eta(np.linspace(-4, 4, 161), E, V0, V008, g8)
    Rs = reflection_amplitude(ths, E, V0, [V008], g8, 0.0)
    print(f"r = 0, 161 angles over eta in [-4, 4]: max |R| - 1 = {np.max(np.abs(Rs)) - 1:+.2e}")
    check_true("|R| <= 1 + 1e-12 without absorption", np.max(np.abs(Rs)) <= 1 + 1e-12)
    ing = (ths > ex_lo + 1e-9) & (ths < ex_hi - 1e-9)
    check("|R| = 1 inside the exact gap", float(np.max(np.abs(np.abs(Rs[ing]) - 1))), 0.0, 1e-10)
    for rr in (0.05, 0.1):
        Ra = reflection_amplitude(ths, E, V0, [V008], g8, rr)
        check_true(f"|R| < 1 with absorption r = {rr}", np.max(np.abs(Ra)) < 1.0,
                   f"(max |R| = {np.max(np.abs(Ra)):.4f})")
    # two-beam basis
    slab = Slab(V0, (V008,), g8, 0.0, 0.0)
    U = slab.U_coeffs(bc, klein_gordon_V2=False)
    worst = 0.0
    for th in thetas_chk:
        K = bc["k"] * np.sin(th)
        R2b = R_from_L(K, L_bloch(K, U, slab.G_f, 0, basis=[0, 1]))
        Rcf = two_beam_reflection(th, E, V0, [V008], g8, 0.0, order=1, form="bloch_matched")
        worst = max(worst, abs(R2b - Rcf))
    check("two-beam closed form = Bloch method in the basis {0, 1}", worst, 0.0, 1e-10)
    # Darwin form: phases 0, pi/2, pi at eta = -1, 0, 1
    for e_, want in ((-1.0, 0.0), (0.0, np.pi / 2), (1.0, np.pi)):
        th = theta_of_eta(e_, E, V0, V008, g8)
        Rd = two_beam_reflection(th, E, V0, [V008], g8, 0.0, order=1, form="darwin")
        check(f"Darwin arg R at eta = {e_:+.0f}", float(np.angle(Rd)) if e_ < 1 else
              float(abs(np.angle(Rd))), want, 1e-6)
    # Bessel identity for the build-up closed form
    for eta in (0.3 + 0.2j, -0.7 + 0.5j, 1.4 + 0.1j):
        val = integrate.quad(lambda t: (special.jv(1, t) / t * np.exp(1j * eta * t)).real, 0, 400,
                             limit=2000)[0] + 1j * integrate.quad(
            lambda t: (special.jv(1, t) / t * np.exp(1j * eta * t)).imag, 0, 400, limit=2000)[0]
        want = -(eta - np.sqrt(eta - 1) * np.sqrt(eta + 1))
        check(f"i int J1(t)/t exp(i eta t) dt = -(eta - sqrt(eta^2-1)), eta = {eta}", 1j * val, want,
              1e-6)

    # ---------------------------------------------------------------------------------------------
    rule("6. Rocking curves of (0,0,8): exact (single harmonic) vs two-beam, r = 0, 0.05, 0.1")
    print("theta_ext in mrad; dth = theta - theta_c(two-beam centre) in urad; eta = two-beam deviation"
          " parameter (r = 0 definition); phases in rad; R referenced at x_s (cosine maximum at x_s);"
          "\nex = exact (single harmonic V_008); 2b = two-beam matched closed form; DR = Darwin composed "
          "with the Fresnel step; TT = Darwin/Takagi-Taupin; full = exact, full layer potential "
          "(V_004 ... V_048, g = 4/a)")
    etas = [-3.0, -2.0, -1.5, -1.0, -0.9, -0.5, 0.0, 0.5, 0.9, 1.0, 1.5, 2.0, 3.0]
    for rr in (0.0, 0.05, 0.1):
        print(f"\n--- r = {rr} ---")
        print(f"{'eta':>5} {'theta':>9} {'dth':>7} | {'|R|ex':>7} {'arg ex':>7} | {'|R|2b':>7} "
              f"{'arg 2b':>7} | {'|R|DR':>7} {'arg DR':>7} | {'|R|TT':>7} {'arg TT':>7} | "
              f"{'|R|full':>7} {'arg full':>8}")
        for e_ in etas:
            th = float(theta_of_eta(e_, E, V0, V008, g8))
            Rx = reflection_amplitude(th, E, V0, [V008], g8, rr)
            R2 = two_beam_reflection(th, E, V0, [V008], g8, rr, order=1, form="bloch_matched")
            Rd = two_beam_reflection(th, E, V0, [V008], g8, rr, order=1, form="darwin_refracted")
            Rt = two_beam_reflection(th, E, V0, [V008], g8, rr, order=1, form="darwin")
            Rfull = reflection_amplitude(th, E, V0, Vn_all, g4, rr)
            print(f"{e_:5.1f} {th * 1e3:9.5f} {(th - p['theta_centre']) * 1e6:7.1f} | {abs(Rx):7.5f} "
                  f"{np.angle(Rx):+7.4f} | {abs(R2):7.5f} {np.angle(R2):+7.4f} | {abs(Rd):7.5f} "
                  f"{np.angle(Rd):+7.4f} | {abs(Rt):7.5f} {np.angle(Rt):+7.4f} | {abs(Rfull):7.5f} "
                  f"{np.angle(Rfull):+8.4f}")
    # summary statistics on a fine grid
    rule("7. Plateau summary: centre, width, phase sweep (exact vs two-beam)")
    fine_eta = np.linspace(-3, 3, 1201)
    th_f = theta_of_eta(fine_eta, E, V0, V008, g8)
    forms = (("two-beam matched", "bloch_matched"), ("Darwin+Fresnel", "darwin_refracted"),
             ("Darwin/TT", "darwin"))
    for rr in (0.0, 0.05, 0.1):
        Rx = reflection_amplitude(th_f, E, V0, [V008], g8, rr)
        curves = [("exact", Rx)] + [(nm, two_beam_reflection(th_f, E, V0, [V008], g8, rr, order=1,
                                                             form=fm)) for nm, fm in forms]
        for nm, R in curves:
            I = np.abs(R) ** 2
            i_pk = int(np.argmax(I))
            idx = np.nonzero(I >= 0.5 * I[i_pk])[0]
            lo, hi = idx[0], idx[-1]
            ph = np.unwrap(np.angle(R))
            print(f"r = {rr:4.2f} {nm:17s}: max|R| = {np.sqrt(I[i_pk]):.5f} at {th_f[i_pk] * 1e3:.5f} mrad;"
                  f" |R|^2 FWHM {(th_f[hi] - th_f[lo]) * 1e6:7.2f} urad centred "
                  f"{0.5 * (th_f[hi] + th_f[lo]) * 1e3:.5f} mrad; arg R at eta=0: "
                  f"{np.angle(R[np.argmin(np.abs(fine_eta))]):+.4f}; arg R at FWHM edges "
                  f"{ph[lo]:+.4f} -> {ph[hi]:+.4f} (sweep {ph[hi] - ph[lo]:+.4f})")
        for nm, R in curves[1:]:
            for lab, sel in (("|eta|<=0.9", np.abs(fine_eta) <= 0.9), ("|eta|<=3", fine_eta == fine_eta)):
                print(f"      {nm:17s} vs exact, r = {rr:4.2f}, {lab:10s}: max |dR| = "
                      f"{np.max(np.abs(R - Rx)[sel]):.2e}, max |arg(R/R_ex)| = "
                      f"{np.max(np.abs(wrap(np.angle(R / Rx)))[sel]):.2e} rad")
    # r = 0 at the exact band edges
    Rlo = reflection_amplitude(ex_lo, E, V0, [V008], g8, 0.0)
    Rhi = reflection_amplitude(ex_hi, E, V0, [V008], g8, 0.0)
    Rmid = reflection_amplitude(ex_c, E, V0, [V008], g8, 0.0)
    sweep_ex = float(np.angle(Rhi / Rlo)) % TWO_PI
    print(f"r = 0 exact: arg R at the band edges {np.angle(Rlo):+.5f} (low) and {np.angle(Rhi):+.5f}"
          f" (high), at the midpoint {np.angle(Rmid):+.5f}; sweep across the gap {sweep_ex:.5f} rad "
          f"(Darwin: pi = {np.pi:.5f})")
    # Fresnel amplitude at the centre (size of the TT neglect)
    Kc = p["K_centre"]
    qc = np.sqrt(Kc**2 + p["U0"])
    rFc = (Kc - qc) / (Kc + qc)
    print(f"Fresnel step amplitude at the (0,0,8) centre r_F = (K - q)/(K + q) = {rFc:+.5f}; "
          f"refraction phase at the centre 2 atan(|r_F|) = {2 * np.arctan(abs(rFc)):.5f} rad")
    for nm, fm in forms:
        chk_R = two_beam_reflection(0.03, E, V0, [0.0], g8, 0.0, order=1, form=fm) if fm != "darwin" \
            else None
        if chk_R is not None:
            K3 = bc["k"] * np.sin(0.03)
            q3 = np.sqrt(K3**2 + p["U0"])
            check(f"{nm}: V_g = 0 gives the Fresnel step", chk_R, (K3 - q3) / (K3 + q3), 1e-12)
    # plane offset (truncation position) sensitivity
    for t_off in (0.0, 0.25 / g8, 0.5 / g8):
        Rt_ = reflection_amplitude(p["theta_centre"], E, V0, [V008], g8, 0.0, plane_offset_A=t_off)
        print(f"truncation plane offset t = {t_off:.5f} A (cosine maximum t below x_s): R(centre) = "
              f"{abs(Rt_):.5f} exp({np.angle(Rt_):+.5f} i); two-beam phase factor exp(i G t) adds "
              f"{wrap(G8 * t_off):+.5f} rad")
    mg_lo, mg_hi = exact_band_edges(E, V0, Vn_all, g4, order=2, plane_offset_A=a / 8)
    check("band edges independent of the truncation plane (bulk property)",
          abs(mg_lo - mh_lo) + abs(mg_hi - mh_hi), 0.0, 1e-12)
    print(f"full layer potential with the truncation plane a/8 above the top atomic plane (t = a/8):"
          f" band edges {mg_lo * 1e3:.5f} to {mg_hi * 1e3:.5f} mrad (bulk property, unchanged); R at "
          f"the band midpoint: t = 0 {np.angle(reflection_amplitude(0.5 * (mh_lo + mh_hi), E, V0, Vn_all, g4, 0.0)):+.4f}"
          f" rad, t = a/8 {np.angle(reflection_amplitude(0.5 * (mh_lo + mh_hi), E, V0, Vn_all, g4, 0.0, plane_offset_A=a / 8)):+.4f} rad")

    # ---------------------------------------------------------------------------------------------
    rule("8. Paraxial / propagator models (stationary R(K), laterally uniform potential)")
    for e_ in (-0.9, 0.0, 0.9):
        th = float(theta_of_eta(e_, E, V0, V008, g8))
        K = bc["k"] * np.sin(th)
        dV = oneway_V0_shift_V(K, Slab(V0, (V008,), g8, 0.0, 0.0), bc)
        Rx = reflection_amplitude(th, E, V0, [V008], g8, 0.0)
        Re = reflection_amplitude(th, E, V0, [V008], g8, 0.0, model="engine_exact_propagator")
        print(f"eta = {e_:+.1f}: one-way ('exact' propagator) effective dV0 = {dV * 1e3:+.4f} mV; "
              f"|R_oneway| - |R| = {abs(Re) - abs(Rx):+.2e}, arg(R_oneway/R) = "
              f"{np.angle(Re / Rx):+.3e} rad")
    Kc = p["K_centre"]
    dV = oneway_V0_shift_V(Kc, Slab(V0, (V008,), g8, 0.0, 0.0), bc)
    dK2 = -2 * bc["k"] * bc["sigma"] * dV
    dth = (np.arcsin(np.sqrt(Kc**2 + dK2) / bc["k"]) - p["theta_centre"])
    print(f"centre shift for the one-way scheme: d(K^2) = {dK2:.3e} rad^2/A^2, d(theta) = "
          f"{dth * 1e6:+.4f} urad = {dth / p['width_theta']:+.2e} of the plateau width, d(eta) = "
          f"{dK2 / p['Ug']:+.2e}")
    # rung-1 consequence: exact-vs-Fresnel difference of the Fresnel step coefficient (V0 = 12 V)
    m2 = {10.00: (-0.020, -0.015), 16.47: (-0.404, -0.391), 30.00: (-1.254, -1.209)}
    for thm, (e_ex, e_fr) in m2.items():
        th = thm * 1e-3
        Rf = reflection_amplitude(th, E, 12.0, [0.0], g8, 0.0)
        Ro = reflection_amplitude(th, E, 12.0, [0.0], g8, 0.0, model="engine_exact_propagator")
        print(f"rung 1, V0 = 12 V, {thm:5.2f} mrad: predicted |r_exact-prop|/|r_Fresnel| - 1 = "
              f"{(abs(Ro) / abs(Rf) - 1) * 100:+.4f} %; M2 section 2 measured (dx 0.025, dz 1): "
              f"{e_ex - e_fr:+.3f} % (exact {e_ex:+.3f} %, Fresnel {e_fr:+.3f} %)")
    # Klein-Gordon (eV)^2 term
    for e_ in (0.0,):
        th = float(theta_of_eta(e_, E, V0, V008, g8))
        R1 = reflection_amplitude(th, E, V0, [V008], g8, 0.0)
        R2 = reflection_amplitude(th, E, V0, [V008], g8, 0.0, klein_gordon_V2=True)
        print(f"(e V)^2 term at eta = 0: arg(R_KG/R) = {np.angle(R2 / R1):+.2e} rad, |R_KG|-|R| = "
              f"{abs(R2) - abs(R1):+.1e}; U_0 changes by {(V0**2 + 2 * V008**2) / HBARC_EV_A**2:.3e} "
              f"rad^2/A^2 (relative {(V0**2 + 2 * V008**2) / HBARC_EV_A**2 / p['U0']:.2e})")

    # ---------------------------------------------------------------------------------------------
    rule("9. Build-up along the surface after a leading edge (two-beam closed form, sharp edge)")
    Zs = [1000.0, 2000.0, 4000.0, 8000.0, 16000.0, 32000.0]
    print("|A(Z) - R_TT| (and |arg(A/R_TT)| in rad) versus Z downstream of first contact")
    for rr in (0.0, 0.05, 0.1):
        for e_ in (-0.5, 0.0, 0.5):
            th = float(theta_of_eta(e_, E, V0, V008, g8))
            A = build_up_two_beam(np.array(Zs), th, E, V0, V008, g8, rr)
            R = two_beam_reflection(th, E, V0, [V008], g8, rr, order=1, form="darwin")
            s1 = "  ".join(f"{abs(Ai - R):.1e}({abs(np.angle(Ai / R)):.1e})" for Ai in A)
            print(f"r={rr:4.2f} eta={e_:+.1f}: " + s1)
    print("\nbuild-up lengths (two-beam, sharp edge): smallest Z beyond which |A - R| <= tol "
          "(or |arg(A/R)| <= tol)")
    blen = {}
    for rr in (0.0, 0.05, 0.1):
        for e_ in (-0.5, 0.0, 0.5, 0.9):
            th = float(theta_of_eta(e_, E, V0, V008, g8))
            (z1, z2, z3), R = build_up_length(th, E, V0, V008, g8, rr,
                                              tols=(("abs", 1e-2), ("abs", 1e-3), ("phase", 1e-2)))
            blen[(rr, e_)] = (z1, z2, z3)
            print(f"r = {rr:4.2f} eta = {e_:+.1f} |R_TT| = {abs(R):.4f}: Z(|dA|<=1e-2) = {z1:9.0f} A, "
                  f"Z(|dA|<=1e-3) = {z2:9.0f} A, Z(|d arg|<=1e-2 rad) = {z3:9.0f} A")
    kc = p["kc"]
    print(f"asymptote (r = 0, sharp edge): |A - R| ~ sqrt(2/pi) (kc Z)^(-3/2) / (1 - eta^2), "
          f"kc = {kc:.4e} rad/A -> at eta = 0: Z(1e-2) ~ {(np.sqrt(2 / np.pi) / 1e-2) ** (2 / 3) / kc:.0f} A,"
          f" Z(1e-3) ~ {(np.sqrt(2 / np.pi) / 1e-3) ** (2 / 3) / kc:.0f} A")
    for rr in (0.05, 0.1):
        print(f"r = {rr}: slowest decay exp(-Z/Z_a), Z_a = 1/(r sigma (V0 - V_g)) = "
              f"{1 / (rr * bc['sigma'] * (V0 - V008)):.0f} A; fastest 1/(r sigma (V0 + V_g)) = "
              f"{1 / (rr * bc['sigma'] * (V0 + V008)):.0f} A; mean absorption 1/(r sigma V0) = "
              f"{1 / (rr * bc['sigma'] * V0):.0f} A")
    # closed-form limit check
    for rr in (0.05, 0.1):
        th = float(theta_of_eta(0.0, E, V0, V008, g8))
        A = build_up_two_beam(np.array([2.0e5]), th, E, V0, V008, g8, rr)
        R = two_beam_reflection(th, E, V0, [V008], g8, rr, order=1, form="darwin")
        check(f"build-up A(Z -> inf) = R_TT, r = {rr}", abs(A[0] - R), 0.0, 1e-8)
    th = float(theta_of_eta(0.0, E, V0, V008, g8))
    A = build_up_two_beam(np.array([4.0e5]), th, E, V0, V008, g8, 0.0)
    R = two_beam_reflection(th, E, V0, [V008], g8, 0.0, order=1, form="darwin")
    check("build-up A(4e5 A) -> R_TT, r = 0 (power law)", abs(A[0] - R), 0.0, 2e-4)

    # ---------------------------------------------------------------------------------------------
    rule("10. Exact step response (smooth edge, w = 400 A) vs two-beam, from R(E) by damped FFT")
    w_s = 400.0
    resp = {}
    for rr in (0.0, 0.1):
        th = float(theta_of_eta(0.0, E, V0, V008, g8))
        slab_ex = Slab(V0, (V008,), g8, rr, 0.0)
        Uex = slab_ex.U_coeffs(bc, klein_gordon_V2=False)
        f_ex = lambda K, U=Uex: R_from_L(K, L_bloch(K, U, slab_ex.G_f, 8))  # noqa: E731
        f_tt = lambda K, s=slab_ex: _two_beam_R_K(K, s, bc, 1, "darwin")  # noqa: E731
        Z, Aex = step_response_fft(th, E, V0, [V008], g8, rr, switch_width_A=w_s, R_of_K=f_ex)
        _, Att = step_response_fft(th, E, V0, [V008], g8, rr, switch_width_A=w_s, R_of_K=f_tt)
        Rex = reflection_amplitude(th, E, V0, [V008], g8, rr)
        Rtt = two_beam_reflection(th, E, V0, [V008], g8, rr, order=1, form="darwin")
        # sharp-edge closed form convolved with the Gaussian edge derivative, for validation
        Zg = np.arange(0.0, 60000.0, 10.0)
        As = build_up_two_beam(Zg, th, E, V0, V008, g8, rr)
        zz = np.arange(-4 * w_s, 4 * w_s + 1, 10.0)
        ker = np.exp(-(zz / w_s) ** 2) / (w_s * np.sqrt(np.pi)) * 10.0
        Aconv = np.convolve(np.concatenate([np.zeros(len(zz)), As]), ker, mode="same")[len(zz):]
        sel = (Z > 5000) & (Z < 50000)
        dev_valid = np.max(np.abs(np.interp(Z[sel], Zg, Aconv.real) + 1j * np.interp(
            Z[sel], Zg, Aconv.imag) - Att[sel]))
        print(f"r = {rr}: FFT two-beam vs convolved closed form (5000 < Z < 50000 A): max |dA| = "
              f"{dev_valid:.2e}")
        check(f"damped-FFT machinery vs closed form, r = {rr}", dev_valid, 0.0, 2e-3)
        for Zq in (2000.0, 4000.0, 8000.0, 16000.0, 32000.0):
            i = int(np.argmin(np.abs(Z - Zq)))
            print(f"   Z = {Z[i]:7.0f} A: |A_ex - R_ex| = {abs(Aex[i] - Rex):.2e}  "
                  f"|A_TT - R_TT| = {abs(Att[i] - Rtt):.2e}  |arg(A_ex/R_ex)| = "
                  f"{abs(np.angle(Aex[i] / Rex)):.2e}")
        big = Z > 60000
        check(f"exact step response -> R_exact at large Z, r = {rr}",
              float(np.max(np.abs(Aex[big] - Rex))), 0.0, 3e-3 if rr == 0 else 1e-6)
        resp[rr] = (Z, Aex, Att, Rex, Rtt)

    # ---------------------------------------------------------------------------------------------
    rule("11. Engine geometry: finite clean depth above the numerical absorber (sin^2, 100 V, 15 A)")
    eta_e = [-3.0, -1.5, -1.0, -0.9, 0.0, 0.9, 1.0, 1.5, 3.0]
    th_e = theta_of_eta(np.array(eta_e), E, V0, V008, g8)
    for rr in (0.0, 0.05, 0.1):
        Rinf = reflection_amplitude(th_e, E, V0, [V008], g8, rr)
        for Dc in (60.0, 100.0, 150.0, 250.0):
            Rg = reflection_amplitude_engine_geometry(th_e, E, V0, [V008], g8, rr, clean_depth_A=Dc,
                                                      absorber_A=15.0, absorber_W0_V=100.0)
            d = np.abs(Rg - Rinf)
            print(f"r = {rr:4.2f} D = {Dc:5.0f} A: |R_cell - R_inf| at eta " + " ".join(
                f"{e_:+.1f}:{v:.1e}" for e_, v in zip(eta_e, d)))
    # constant potential reflection of the absorber alone (V_g = 0)
    Rg0 = reflection_amplitude_engine_geometry(th_e, E, V0, [0.0], g8, 0.0, clean_depth_A=150.0,
                                               absorber_A=15.0, absorber_W0_V=100.0)
    Rinf0 = reflection_amplitude(th_e, E, V0, [0.0], g8, 0.0)
    print(f"V_g = 0 (rung-1 geometry), D = 150 A: max |R_cell - R_Fresnel| = "
          f"{np.max(np.abs(Rg0 - Rinf0)):.1e} (absorber reflection)")
    # independent discretisation of the same finite cell: piecewise-constant transfer matrices
    th1 = float(theta_of_eta(1.5, E, V0, V008, g8))
    K1 = bc["k"] * np.sin(th1)
    sl = Slab(V0, (V008,), g8, 0.0, 0.0)
    U1 = sl.U_coeffs(bc, klein_gordon_V2=False)
    Ux1 = _U_of_x(U1, sl.G_f)
    f2 = 2 * bc["k"] * bc["sigma"]

    def U_cell(x, Dc=150.0, Ab=15.0, W0=100.0):
        u = (-x - Dc) / Ab
        return Ux1(x) + 1j * f2 * W0 * np.sin(0.5 * np.pi * min(max(u, 0.0), 1.0)) ** 2
    Lh = L_transfer_matrix(K1, U_cell, -165.0, 0.004, U1[0] + 1j * f2 * 100.0)
    Lh2 = L_transfer_matrix(K1, U_cell, -165.0, 0.002, U1[0] + 1j * f2 * 100.0)
    R_tm = R_from_L(K1, (4 * Lh2 - Lh) / 3)
    R_ode = reflection_amplitude_engine_geometry(th1, E, V0, [V008], g8, 0.0, clean_depth_A=150.0,
                                                 absorber_A=15.0, absorber_W0_V=100.0)
    print(f"eta = 1.5, r = 0, D = 150 A: R_cell ODE = {R_ode:.6f}, transfer matrices (h = 0.004, "
          f"0.002 A, Richardson) = {R_tm:.6f}")
    check("finite cell: ODE vs transfer-matrix discretisation", abs(R_ode - R_tm), 0.0, 1e-6)
    print("\nr = 0: absorber reflection of Bragg-case Bloch waves versus the absorber ramp (D = 150 A)")
    th_r = theta_of_eta(np.array([-3.0, -1.5, 1.5, 3.0]), E, V0, V008, g8)
    Rinf_r = reflection_amplitude(th_r, E, V0, [V008], g8, 0.0)
    for Ab, W0 in ((15.0, 100.0), (400.0, 20.0), (800.0, 20.0)):
        Rg = reflection_amplitude_engine_geometry(th_r, E, V0, [V008], g8, 0.0, clean_depth_A=150.0,
                                                  absorber_A=Ab, absorber_W0_V=W0)
        print(f"   ramp {Ab:5.0f} A, W0 = {W0:5.1f} V: |R_cell - R_inf| at eta -3.0, -1.5, +1.5, +3.0 = "
              + ", ".join(f"{v:.1e}" for v in np.abs(Rg - Rinf_r)))
    print("\nM2 null-test geometry (tests/forward/null_test_cases.py: clean depth 21 A above a 15 A, "
          "100 V sin^2 absorber for crystal A; crystal B = A plus two layers, clean depth 21 + a/2 A),"
          " stationary 1D prediction at theta = 16.1347 mrad (R at each crystal's own surface):")
    thN = 16.1347e-3
    for lab, Vl, g in (("single (0,0,8)", [V008], g8), ("full layer potential", Vn_all, g4)):
        for rr in (0.0, 0.05, 0.1):
            Rinf = reflection_amplitude(thN, E, V0, Vl, g, rr)
            RA = reflection_amplitude_engine_geometry(thN, E, V0, Vl, g, rr, clean_depth_A=21.0,
                                                      absorber_A=15.0, absorber_W0_V=100.0)
            RB = reflection_amplitude_engine_geometry(thN, E, V0, Vl, g, rr, clean_depth_A=21.0 + a / 2,
                                                      absorber_A=15.0, absorber_W0_V=100.0)
            print(f"   {lab:21s} r = {rr:4.2f}: |R_inf| = {abs(Rinf):.4f}; |R_A| = {abs(RA):.4f}, "
                  f"|R_B| = {abs(RB):.4f}; arg(R_B/R_A) = {np.angle(RB / RA):+.4f} rad, |R_B/R_A| = "
                  f"{abs(RB / RA):.4f}; arg(R_A/R_inf) = {np.angle(RA / Rinf):+.4f} rad")
    print("   same pair with deeper clean crystal (full layer potential):")
    for Dc in (60.0, 100.0, 150.0):
        for rr in (0.05, 0.1):
            RA = reflection_amplitude_engine_geometry(thN, E, V0, Vn_all, g4, rr, clean_depth_A=Dc,
                                                      absorber_A=15.0, absorber_W0_V=100.0)
            RB = reflection_amplitude_engine_geometry(thN, E, V0, Vn_all, g4, rr,
                                                      clean_depth_A=Dc + a / 2, absorber_A=15.0,
                                                      absorber_W0_V=100.0)
            print(f"      D = {Dc:5.0f} A, r = {rr:4.2f}: arg(R_B/R_A) = {np.angle(RB / RA):+.2e} rad, "
                  f"|R_B/R_A| - 1 = {abs(RB / RA) - 1:+.2e}")

    # ---------------------------------------------------------------------------------------------
    rule("12. Independent minimal 1D split step (NOT the engine): paraxial claims and test protocol")
    thc = p["theta_centre"]

    def ss_eval(res, rr, model):
        thb = res["theta_bins"]
        eta_b = ((bc["k"] * np.sin(thb)) ** 2 - p["K_centre"] ** 2) / p["Ug"]
        sel = np.abs(eta_b) <= 3.0
        Rref = reflection_amplitude(thb[sel], E, V0, [V008], g8, rr, model=model)
        return eta_b[sel], res["r"][sel], Rref
    base = dict(theta0_rad=thc, V0_V=V0, Vg_V=V008, g_per_A=g8, H_A=24.0, edge_A=4.0, gap_A=2.0,
                extra_vacuum_A=150.0)
    runs = {}
    for key, kw in (("F", dict(absorption_ratio=0.1, propagator="fresnel", dx_A=0.025, dz_A=1.0,
                               clean_depth_A=100.0, exit_after_top_contact_A=5000.0)),
                    ("X", dict(absorption_ratio=0.1, propagator="exact", dx_A=0.025, dz_A=1.0,
                               clean_depth_A=100.0, exit_after_top_contact_A=5000.0)),
                    ("F_dx05", dict(absorption_ratio=0.1, propagator="fresnel", dx_A=0.05, dz_A=1.0,
                                    clean_depth_A=100.0, exit_after_top_contact_A=5000.0)),
                    ("F_dx0125", dict(absorption_ratio=0.1, propagator="fresnel", dx_A=0.0125,
                                      dz_A=1.0, clean_depth_A=100.0,
                                      exit_after_top_contact_A=5000.0)),
                    ("F_dz05", dict(absorption_ratio=0.1, propagator="fresnel", dx_A=0.025, dz_A=0.5,
                                    clean_depth_A=100.0, exit_after_top_contact_A=5000.0)),
                    ("F_r005", dict(absorption_ratio=0.05, propagator="fresnel", dx_A=0.025,
                                    dz_A=1.0, clean_depth_A=150.0,
                                    exit_after_top_contact_A=10000.0))):
        res = split_step_1d(**base, **kw)
        rr = kw["absorption_ratio"]
        model = "exact" if kw["propagator"] == "fresnel" else "engine_exact_propagator"
        eb, rm, Rr = ss_eval(res, rr, model)
        runs[key] = (res, eb, rm, Rr)
        s9 = np.abs(eb) <= 0.9
        d = np.abs(rm - Rr)
        ph = np.abs(np.angle(rm / Rr))
        print(f"{key:9s} r = {rr:4.2f} {kw['propagator']:7s} dx = {res['dx_A']:.5f} A dz = {kw['dz_A']} A "
              f"D = {kw['clean_depth_A']:.0f} A Z_e = {kw['exit_after_top_contact_A']:.0f} A: nx = "
              f"{res['n_x']}, {res['n_slices']} slices, bins |eta|<=3: {len(eb)}; vs reference ({model}):"
              f" max |dR| = {d.max():.2e} (|eta|<=0.9: {d[s9].max():.2e}), max |d arg| = {ph.max():.2e}"
              f" (|eta|<=0.9: {ph[s9].max():.2e}) rad")
    resF = runs["F"][0]
    df_bin = 1.0 / (resF["n_x"] * resF["dx_A"])
    print(f"bin spacing of run F: 1/extent = {df_bin:.3e} 1/A = {df_bin * bc['wavelength_A'] * 1e6:.1f} urad "
          f"in theta; L = {resF['L_A']:.0f} A")
    for key in ("F",):
        _, eb, rm, Rr = runs[key]
        for e_, r_, R_ in zip(eb, rm, Rr):
            if abs(e_) <= 1.2:
                print(f"   F bin eta = {e_:+6.3f}: r_ss = {abs(r_):.5f} exp({np.angle(r_):+.5f} i), R_ref = "
                      f"{abs(R_):.5f} exp({np.angle(R_):+.5f} i)")
    d_F = np.max(np.abs(runs["F"][2] - runs["F"][3]))
    check("split step (Fresnel, dx 0.025, dz 1) vs Helmholtz reference, |eta| <= 3", d_F, 0.0, 1e-3)
    d_X = np.max(np.abs(runs["X"][2] - runs["X"][3]))
    check("split step (exact propagator) vs one-way reference model", d_X, 0.0, 1e-3)
    # propagator difference: measured (same discretisation, same bins) vs predicted
    eb, rF_, RpF = runs["F"][1:]
    _, rX_, RpX = runs["X"][1:]
    check_true("F and X runs share their bins", np.array_equal(runs["F"][0]["theta_bins"],
                                                             runs["X"][0]["theta_bins"]))
    meas = np.angle(rX_ / rF_)
    pred = np.angle(RpX / RpF)
    s9 = np.abs(eb) <= 0.9
    print(f"exact minus Fresnel propagator, r = 0.1, |eta| <= 0.9: measured arg(r_X/r_F) in "
          f"[{meas[s9].min():+.2e}, {meas[s9].max():+.2e}] rad, predicted [{pred[s9].min():+.2e}, "
          f"{pred[s9].max():+.2e}] rad; max |measured - predicted| = {np.max(np.abs(meas - pred)[s9]):.1e}")
    check("propagator difference measured vs one-way prediction (|eta| <= 0.9)",
          float(np.max(np.abs(meas - pred)[s9])), 0.0, 2e-4)
    e05 = np.max(np.abs(runs["F_dx05"][2] - runs["F_dx05"][3]))
    e025 = d_F
    e0125 = np.max(np.abs(runs["F_dx0125"][2] - runs["F_dx0125"][3]))
    print(f"dx convergence (max |dR|, |eta| <= 3): 0.05 A {e05:.2e}, 0.025 A {e025:.2e}, 0.0125 A "
          f"{e0125:.2e}; observed orders {np.log2(e05 / e025):.2f}, {np.log2(e025 / e0125):.2f}")
    check_true("dx convergence order >= 1.5 between 0.05 and 0.025 A", np.log2(e05 / e025) >= 1.5)
    print(f"dz 0.5 A (dx 0.025): max |dR| = {np.max(np.abs(runs['F_dz05'][2] - runs['F_dz05'][3])):.2e}")
    print(f"r = 0.05 (D = 150 A, Z_e = 10000 A): max |dR| = "
          f"{np.max(np.abs(runs['F_r005'][2] - runs['F_r005'][3])):.2e}")
    if "--long" in sys.argv:
        res = split_step_1d(**base, absorption_ratio=0.0, propagator="fresnel", dx_A=0.025, dz_A=1.0,
                            clean_depth_A=250.0, exit_after_top_contact_A=30000.0,
                            readout_window_above_A=60.0)
        eb, rm, Rr = ss_eval(res, 0.0, "exact")
        sel = np.abs(((bc["k"] * np.sin(res["theta_bins"])) ** 2 - p["K_centre"] ** 2) / p["Ug"]) <= 3.0
        rw = res["r_win"][sel]
        print(f"r = 0 (D = 250 A, Z_e = 30000 A): nx = {res['n_x']}, {res['n_slices']} slices; whole-"
              f"box read-out and vacuum-only read-out (window from x_s + 60 A, full from x_s + 100 A)")
        for e_, r_, w_, R_ in zip(eb, rm, rw, Rr):
            print(f"   eta = {e_:+6.3f}: whole box |dR| = {abs(r_ - R_):.2e}, d arg = "
                  f"{np.angle(r_ / R_):+.2e} rad; vacuum-only |dR| = {abs(w_ - R_):.2e}, d arg = "
                  f"{np.angle(w_ / R_):+.2e} rad")
        for lim in (0.5, 0.9):
            s_ = np.abs(eb) <= lim
            print(f"   |eta| <= {lim}: max |dR| whole box {np.max(np.abs(rm - Rr)[s_]):.2e}, vacuum-only "
                  f"{np.max(np.abs(rw - Rr)[s_]):.2e}")

    # ---------------------------------------------------------------------------------------------
    rule("12b. Sensitivity of the rung-2 read-out (what a given tolerance can detect)")
    print("max over the bins of |R_perturbed - R| (and of |arg(R_perturbed/R)|), same angles")
    for rr, emax in ((0.1, 3.0), (0.05, 3.0), (0.0, 0.5)):
        eta_s = np.linspace(-emax, emax, 61)
        th_s = theta_of_eta(eta_s, E, V0, V008, g8)
        R0 = reflection_amplitude(th_s, E, V0, [V008], g8, rr)
        cases = (("V0 + 1 mV", dict(V0_V=V0 + 1e-3, Vg_list=[V008])),
                 ("V0 + 5 mV", dict(V0_V=V0 + 5e-3, Vg_list=[V008])),
                 ("V_g x sinc(pi g dx), dx = 0.025 A (cell-averaged harmonic)",
                  dict(V0_V=V0, Vg_list=[V008 * np.sinc(g8 * 0.025)])),
                 ("V_g x sinc(pi g dx), dx = 0.05 A", dict(V0_V=V0, Vg_list=[V008 * np.sinc(g8 * 0.05)])),
                 ("cosine origin 0.01 A below x_s (t = 0.01 A)",
                  dict(V0_V=V0, Vg_list=[V008], plane_offset_A=0.01)),
                 ("engine exact propagator (one-way model)",
                  dict(V0_V=V0, Vg_list=[V008], model="engine_exact_propagator")))
        for lab, kw in cases:
            R1 = reflection_amplitude(th_s, E, kw.pop("V0_V"), kw.pop("Vg_list"), g8, rr, **kw)
            print(f"   r = {rr:4.2f}, |eta| <= {emax}: {lab:58s}: max |dR| = {np.max(np.abs(R1 - R0)):.2e}"
                  f", max |d arg| = {np.max(np.abs(wrap(np.angle(R1 / R0)))):.2e} rad")
        K_s = bc["k"] * np.sin(th_s)
        print(f"   r = {rr:4.2f}: read-out reference plane moved by 0.01 A changes arg R by 2 K (0.01 A) = "
              f"{2 * K_s.min() * 0.01:.4f} to {2 * K_s.max() * 0.01:.4f} rad")
        Rt = two_beam_reflection(th_s, E, V0, [V008], g8, rr, order=1, form="darwin")
        print(f"   r = {rr:4.2f}: Darwin/TT instead of exact: max |dR| = {np.max(np.abs(Rt - R0)):.2e}")

    # ---------------------------------------------------------------------------------------------
    rule("13. Summary of self-checks")
    import resource
    print(f"peak resident memory of this process: "
          f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MB")
    n_fail = sum(1 for _, ok in _CHECKS if not ok)
    print(f"{len(_CHECKS)} checks, {n_fail} failed")
    for nm, ok in _CHECKS:
        if not ok:
            print("   FAILED:", nm)
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
