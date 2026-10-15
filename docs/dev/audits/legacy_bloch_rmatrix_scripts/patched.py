"""In-memory corrected variant of the legacy 2N eigenproblem, for diagnosis only (no file is modified).

Differences from legacy bloch_wave.build_eigenvalue_matrix:
  * U_g = 4 pi gamma F_g / Omega (gamma = 1.3914 at 200 kV)   [legacy: no gamma]
  * diagonal M[g,g] = 2 K s_g + U_0 (1 + i mu)                 [legacy: no U_0]
  * optional: absorption ratio mu applied to every U_g incl. U_0
Boundary matching: legacy per-g equations solved exactly, or rod-summed.
"""
import numpy as np
import simulation.bloch_wave as BW
import simulation.r_matrix as RM
from harness import *


def patched_matrix(k, hkl_sel, n_out, mu=0.07, gamma=GAMMA, include_U0=True, par=LEG5):
    n = len(hkl_sel)
    g = 2 * np.pi / A * np.array(hkl_sel, float)
    kmag = np.linalg.norm(k)
    kf = k[None, :] + g
    s_g = (kmag**2 - np.sum(kf**2, 1)) / (2 * kmag)
    kz = kf @ (-n_out)
    M = np.zeros((n, n), complex)
    for i in range(n):
        for j in range(n):
            dh = tuple(int(x) for x in np.array(hkl_sel[i]) - np.array(hkl_sel[j]))
            if i == j:
                M[i, i] = 2 * kmag * s_g[i] + (U_hkl((0, 0, 0), par, gamma, mu) if include_U0 else 0.0)
            else:
                M[i, j] = U_hkl(dh, par, gamma, mu)
    mat = np.zeros((2 * n, 2 * n), complex)
    mat[:n, n:] = np.eye(n)
    mat[n:, :n] = M
    mat[n:, n:] = -np.diag(2 * kz)
    return mat, g, kz, s_g


def patched_R(theta, hkl_sel, surf="111", mu=0.07, gamma=GAMMA, include_U0=True, match="per_g", select="legacy", par=LEG5):
    n_out = SURF[surf][0]
    k = k_in(theta, surf)
    mat, g, kz, s_g = patched_matrix(k, hkl_sel, n_out, mu, gamma, include_U0, par)
    ev, evec = np.linalg.eig(mat)
    n = len(hkl_sel)
    gam, Cv = BW.select_evanescent(ev, evec, n)
    kappa = RM.compute_vacuum_kz(k, g, n_out)
    kinc = np.dot(k, n_out)
    rod = rod_members(hkl_sel, surf)
    if match == "per_g":
        S = np.zeros((n, n), complex)
        for j in range(n):
            S[:, j] = (kz + gam[j] + kappa) * Cv[:, j]
        bb = np.zeros(n, complex); bb[0] = kappa[0] - kinc
        alpha = np.linalg.solve(S, bb)
        R = Cv @ alpha; R[0] -= 1.0
        return np.sum(R[rod]), R, gam
    raise ValueError(match)
