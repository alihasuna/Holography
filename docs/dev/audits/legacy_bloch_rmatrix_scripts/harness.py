"""Audit harness: run the legacy code unmodified, plus independent references.

Reference R1: exact 1-D semi-infinite crystal (laterally averaged potential of one surface,
i.e. the specular rod only), transfer matrix over one period by piecewise-constant exact
2x2 propagation, Bloch mode of the monodromy matrix that decays (|lambda|<1) or carries flux
into the crystal, matched to exp(i kappa z) + R exp(-i kappa z) at the cut plane z = 0.
Same surface model as the legacy code: bulk potential for z > 0 (z inward), vacuum for z < 0.
"""
import numpy as np
import simulation.constants as C
import simulation.structure_factors as SF
import simulation.bloch_wave as BW
import simulation.r_matrix as RM

A = C.SI_LATTICE_PARAM
OMEGA = A**3
POS = C.SI_ATOM_POSITIONS
h = 6.62607015e-34; c = 299792458.0; e = 1.602176634e-19; MEC2 = 510998.95
T = 200e3
LAM = h * c / e * 1e10 / np.sqrt(T * (T + 2 * MEC2))
K_TRUE = 2 * np.pi / LAM
GAMMA = 1 + T / MEC2
K_LEG = C.K_200KV

# parametrisations: (a, b) Gaussians in s = q/2
LEG5 = (C.SI_SCATTERING_A, C.SI_SCATTERING_B)
DT4 = (C.SI_SCATTERING_A[:4], C.SI_SCATTERING_B[:4])


def fe(s, par=LEG5):
    a, b = par
    return float(np.sum(a * np.exp(-b * s**2)))


def F_hkl(hkl, par=LEG5, B=C.SI_DEBYE_WALLER_B):
    hkl = np.asarray(hkl, float)
    s = np.linalg.norm(hkl) / (2 * A)
    geo = np.sum(np.exp(-2j * np.pi * POS @ hkl))
    return fe(s, par) * np.exp(-B * s**2) * geo


def U_hkl(hkl, par=LEG5, gamma=GAMMA, mu=0.0, B=C.SI_DEBYE_WALLER_B):
    """U_g = 4 pi gamma F_g / Omega * (1 + i mu)  [1/A^2]."""
    return 4 * np.pi * gamma * F_hkl(hkl, par, B) / OMEGA * (1 + 1j * mu)


# ---------------------------------------------------------------- geometry
SURF = {
    # name: (outward normal used by legacy (unit), rod direction hkl pointing INTO crystal, beam azimuth unit)
    "111": (np.array([-1, 1, -1]) / np.sqrt(3), np.array([1, -1, 1]), np.array([1, 1, 0]) / np.sqrt(2)),
    "001": (np.array([0, 0, 1.0]), np.array([0, 0, -1]), np.array([1, 1, 0]) / np.sqrt(2)),
}


def k_in(theta, surf="111", K=K_LEG):
    n_out, _, az = SURF[surf]
    return K * (np.cos(theta) * az - np.sin(theta) * n_out)


def rod_period(surf):
    """reciprocal period b along the inward normal (1/A) and the hkl step of the rod"""
    _, rod, _ = SURF[surf]
    if surf == "111":
        step = rod  # (1,-1,1): orders m = 1,2,3...
    else:
        step = rod  # (0,0,-1): only (0,0,4m) allowed, but use step 1 and let F vanish
    b = 2 * np.pi / A * np.linalg.norm(step)
    return b, step


# ---------------------------------------------------------------- reference R1 (1-D exact)
def rod_potential_coeffs(surf, mmax, par=LEG5, gamma=GAMMA, mu=0.0, include_U0=True, only=None, B=C.SI_DEBYE_WALLER_B):
    """U_m for U(z) = sum_m U_m exp(i m b z), z inward."""
    b, step = rod_period(surf)
    coeffs = {}
    for m in range(-mmax, mmax + 1):
        if m == 0 and not include_U0:
            continue
        if only is not None and m not in only:
            continue
        hkl = m * step
        U = U_hkl(hkl, par, gamma, mu, B)
        if abs(U) > 1e-14:
            coeffs[m] = U
    return b, coeffs


def exact_1d_R(kappa, b, coeffs, nsub=4000):
    """Complex specular amplitude R at the cut plane for vacuum normal wavevector kappa."""
    d = 2 * np.pi / b
    hz = d / nsub
    zs = (np.arange(nsub) + 0.5) * hz
    Uz = np.zeros(nsub, complex)
    for m, U in coeffs.items():
        Uz += U * np.exp(1j * m * b * zs)
    k2 = kappa**2 + Uz
    kl = np.sqrt(k2.astype(complex))
    M = np.eye(2, dtype=complex)
    cs, sn = np.cos(kl * hz), np.sin(kl * hz)
    for i in range(nsub):
        P = np.array([[cs[i], sn[i] / kl[i]], [-kl[i] * sn[i], cs[i]]])
        M = P @ M
    w, v = np.linalg.eig(M)
    # choose inward mode
    if abs(abs(w[0]) - abs(w[1])) > 1e-9 * max(abs(w)):
        j = int(np.argmin(np.abs(w)))
    else:  # propagating: flux into crystal Im(psi* psi') > 0
        flux = [np.imag(np.conj(v[0, i]) * v[1, i]) for i in range(2)]
        j = int(np.argmax(flux))
    beta = v[1, j] / v[0, j]
    R = (1j * kappa - beta) / (1j * kappa + beta)
    return R, w[j]


def exact_1d_rocking(thetas, surf, mmax=24, par=LEG5, gamma=GAMMA, mu=0.0, include_U0=True, only=None, K=K_TRUE, nsub=3000):
    b, co = rod_potential_coeffs(surf, mmax, par, gamma, mu, include_U0, only)
    return np.array([exact_1d_R(K * np.sin(t), b, co, nsub)[0] for t in thetas])


# ---------------------------------------------------------------- legacy, unmodified
def legacy_full(theta, surf="111", hkl_list=None, g_vectors=None, n_strong=20, absorption_ratio=0.07):
    """r_matrix.compute_reflected_intensities as shipped (111 only: it hard-codes SURFACE_NORMAL)."""
    k = k_in(theta, surf)
    res = RM.compute_reflected_intensities(k, hkl_list, g_vectors, n_strong=n_strong, absorption_ratio=absorption_ratio)
    return {r["hkl"]: r["R_g"] for r in res}, res


def legacy_pieces(theta, hkl_sel, surf="111", absorption_ratio=0.07, solve="legacy"):
    """Legacy building blocks with an explicit beam list (000 first) and an explicit normal.

    solve='legacy' -> r_matrix.solve_reflection_amplitudes (SVD-truncation sweep, as shipped)
    solve='exact'  -> the same 2N boundary equations solved by np.linalg.solve (no truncation)
    """
    n_out = SURF[surf][0]
    k = k_in(theta, surf)
    g = 2 * np.pi / A * np.array(hkl_sel, float)
    ev, evec, s_g, kz = BW.solve_bloch(k, hkl_sel, g, absorption_ratio=absorption_ratio, surface_normal=n_out)
    n = len(hkl_sel)
    n_pos = int(np.sum(np.imag(ev) > 0))
    gam, Cv = BW.select_evanescent(ev, evec, n)
    if solve == "legacy":
        R, alpha = RM.solve_reflection_amplitudes(gam, Cv, kz, k, g, surface_normal=n_out)
    else:
        kappa = RM.compute_vacuum_kz(k, g, n_out)
        kinc = np.dot(k, n_out)
        S = np.zeros((n, n), complex)
        for j in range(n):
            S[:, j] = (kz + gam[j] + kappa) * Cv[:, j]
        bb = np.zeros(n, complex); bb[0] = kappa[0] - kinc
        alpha = np.linalg.solve(S, bb)
        R = Cv @ alpha; R[0] -= 1.0
    kappa = RM.compute_vacuum_kz(k, g, n_out)
    return dict(R=R, kappa=kappa, kappa0=abs(np.dot(k, n_out)), n_pos=n_pos, gamma=gam, ev=ev, kz=kz, s_g=s_g)


def rod_members(hkl_sel, surf):
    """indices of beams on the specular rod (in-plane component zero)"""
    n_out = SURF[surf][0]
    out = []
    for i, hkl in enumerate(hkl_sel):
        g = np.asarray(hkl, float)
        gt = g - np.dot(g, n_out) * n_out
        if np.linalg.norm(gt) < 1e-9:
            out.append(i)
    return out


def rod_hkls(surf, mmax, allowed_only=True):
    _, step = rod_period(surf)
    out = [(0, 0, 0)]
    for m in list(range(1, mmax + 1)) + list(range(-1, -mmax - 1, -1)):
        hkl = tuple(int(x) for x in m * step)
        ok, _ = SF.is_allowed_diamond_cubic(*hkl)
        if ok or not allowed_only:
            out.append(hkl)
    return out


def theta_B(order_hkl):
    d = A / np.linalg.norm(order_hkl)
    return np.arcsin(LAM / (2 * d))


def theta_ext_refr(theta_int, V0):
    D = V0 * (1 + T / MEC2) / (T * (1 + T / (2 * MEC2)))
    s2 = np.sin(theta_int)**2 * (1 + D) - D
    return np.arcsin(np.sqrt(s2)) if s2 > 0 else np.nan
