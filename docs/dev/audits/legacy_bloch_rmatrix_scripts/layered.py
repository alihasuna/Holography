"""Auditor's layered 1-D reference: semi-infinite stack of planar-averaged atomic layers
(full atoms, no truncation through atom centres), exact transfer matrix, R referenced to the
lab plane z = 0 (z inward). U(z) = 4 pi gamma sigma sum_i a_i sqrt(4 pi/(b_i+B)) exp(-4 pi^2 z^2/(b_i+B)) (1 + i mu)."""
import numpy as np
from harness import GAMMA, K_TRUE, LEG5

PENG_HIGH = (np.array([0.0567, 0.3365, 0.8104, 2.496, 2.1186]), np.array([0.0582, 0.6155, 3.2522, 16.7929, 57.6767]))


def layer_U(z, z0, sigma, par, B, gamma=GAMMA):
    a, b = par
    bb = b + B
    return 4 * np.pi * gamma * sigma * np.sum(a[None, :] * np.sqrt(4 * np.pi / bb)[None, :] * np.exp(-4 * np.pi**2 * (z[:, None] - z0)**2 / bb[None, :]), 1)


def stack(surface, a_lat):
    """layer offsets within one period (inward), period d, areal density per layer"""
    if surface == "001":
        d = a_lat / 4; return [0.0], d, 2 / a_lat**2
    if surface == "111":
        d = a_lat / np.sqrt(3); return [0.0, d / 4], d, 4 / (np.sqrt(3) * a_lat**2)
    raise ValueError


def U_profile(z, surface, a_lat, par, B, mu, shift=0.0, n_layers_deep=None):
    offs, d, sig = stack(surface, a_lat)
    U = np.zeros_like(z, dtype=complex)
    zmax = z.max() + 8
    p = 0
    while p * d + shift < zmax:
        for o in offs:
            z0 = p * d + o + shift
            if z0 >= shift - 1e-12:
                U += layer_U(z, z0, sig, par, B)
        p += 1
    return U * (1 + 1j * mu)


def _transfer(kappa, U, hz):
    kl = np.sqrt((kappa**2 + U).astype(complex))
    cs, sn = np.cos(kl * hz), np.sin(kl * hz)
    M = np.eye(2, dtype=complex)
    for i in range(len(U)):
        M = np.array([[cs[i], sn[i] / kl[i]], [-kl[i] * sn[i], cs[i]]]) @ M
    return M


class Layered:
    def __init__(self, surface, a_lat=5.4309, par=PENG_HIGH, B=0.46, mu=0.05, shift=0.0, hz=0.004, z_vac=-7.0, n_bulk=4):
        offs, d, sig = stack(surface, a_lat)
        self.d = d
        self.z_vac = z_vac + shift
        self.z_b = shift + n_bulk * d + (np.ceil(8.0 / d)) * d * 0  # bulk reference plane
        self.z_b = shift + max(n_bulk, int(np.ceil(9.0 / d))) * d
        n1 = int(round((self.z_b - self.z_vac) / hz)); self.h1 = (self.z_b - self.z_vac) / n1
        z1 = self.z_vac + (np.arange(n1) + 0.5) * self.h1
        n2 = int(round(d / hz)); self.h2 = d / n2
        z2 = self.z_b + (np.arange(n2) + 0.5) * self.h2
        self.U1 = U_profile(z1, surface, a_lat, par, B, mu, shift)
        self.U2 = U_profile(z2, surface, a_lat, par, B, mu, shift)

    def R(self, theta, K=K_TRUE):
        kappa = K * np.sin(theta)
        Mb = _transfer(kappa, self.U2, self.h2)
        w, v = np.linalg.eig(Mb)
        j = int(np.argmin(np.abs(w))) if abs(abs(w[0]) - abs(w[1])) > 1e-10 else int(np.argmax([np.imag(np.conj(v[0, i]) * v[1, i]) for i in range(2)]))
        Mvb = _transfer(kappa, self.U1, self.h1)
        psi = np.linalg.solve(Mvb, v[:, j])
        zv = self.z_vac
        # psi = A e^{ik zv} + B e^{-ik zv}; psi' = ik (A e^{ik zv} - B e^{-ik zv})
        Ae = 0.5 * (psi[0] + psi[1] / (1j * kappa))
        Be = 0.5 * (psi[0] - psi[1] / (1j * kappa))
        A_ = Ae * np.exp(-1j * kappa * zv); B_ = Be * np.exp(1j * kappa * zv)
        return B_ / A_
