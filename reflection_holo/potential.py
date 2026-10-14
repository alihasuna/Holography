"""Projected atomic potentials, absorbers and transmission functions.

Projected potential of the atoms of one plane (all atoms whose nominal position lies
on that plane; projection approximation), as a Fourier series on the periodic grid:

    v(r) = sum_q c(q) exp(2 pi i q.r),
    c(q) = (2 pi a0 e / (Lx Ly)) f_e(|q|) D(q) sum_j exp(-2 pi i q.r_j)     [V A]

DERIVED_HERE from V(r) = 2 pi a0 e int f_e(q) exp(2 pi i q.r) d^3q (first Born
relation between f_e and V with the rest mass) integrated along z.  D(q) =
exp(-B q^2/4) is an optional Debye-Waller factor for static-lattice runs (B = 8 pi^2
u_rms^2, q = 2 sin(theta)/lambda); frozen-phonon runs use D = 1 and displaced atoms.
c(q) is computed only inside the anti-aliasing band |q| <= q_band and is zero
outside (band-limited potential); the structure-factor sum is evaluated exactly as
a matrix product Ex @ Ey with phase arguments reduced modulo 1 in float64.
"""
from __future__ import annotations

import json
import os

import numpy as np

from .constants import TWO_PI_A0_E_V_A2, interaction_constant

_DATA = os.path.join(os.path.dirname(__file__), "data", "si_parametrizations.json")


def load_parameters(name: str):
    with open(_DATA) as fh:
        d = json.load(fh)
    return np.array(d[name]["Si"], dtype=float)


def scattering_factor(q, name="kirkland"):
    """Electron scattering factor f_e(q) of Si in A, q = |g| in cycles/A."""
    p = load_parameters(name)
    q2 = np.asarray(q, float) ** 2
    if name == "kirkland":
        a, b, c, d = p
        return (sum(a[i] / (q2 + b[i]) for i in range(3))
                + sum(c[i] * np.exp(-d[i] * q2) for i in range(3)))
    if name == "lobato":
        a, b = p
        return sum(a[i] * (2.0 + b[i] * q2) / (1.0 + b[i] * q2) ** 2 for i in range(5))
    raise ValueError(name)


def mean_inner_potential(name="kirkland", a_A=5.4309):
    """Mean inner potential of the superposition of free-atom potentials:
    V0 = 2 pi a0 e f_e(0) n with n = 8/a^3 atoms per A^3 (DERIVED_HERE)."""
    return float(TWO_PI_A0_E_V_A2 * scattering_factor(0.0, name) * 8.0 / a_A**3)


class PotentialBuilder:
    """Builds band-limited projected potentials and transmission functions."""

    def __init__(self, grid, xp, E_keV, parametrization="kirkland", debye_waller_B=0.0,
                 absorptive_fraction=0.0, absorber_W=None, dtype="complex128",
                 atom_chunk=4096):
        self.g = grid
        self.xp = xp
        self.sigma = interaction_constant(E_keV)
        self.ctype = np.dtype(dtype)
        self.rtype = np.float64 if self.ctype == np.complex128 else np.float32
        self.alpha = float(absorptive_fraction)
        self.atom_chunk = int(atom_chunk)
        ix, iy = grid.band_indices()
        self.ix, self.iy = ix, iy
        qx, qy = grid.qx[ix], grid.qy[iy]
        q = np.sqrt(qx[:, None] ** 2 + qy[None, :] ** 2)
        f = scattering_factor(q, parametrization) * np.exp(-debye_waller_B * q**2 / 4.0)
        f = f * (q <= grid.q_band)
        pref = TWO_PI_A0_E_V_A2 / (grid.Lx * grid.Ly) * grid.Nx * grid.Ny
        self._form = xp.asarray((pref * f).astype(self.ctype))
        self._qx = qx
        self._qy = qy
        self._ixg = xp.asarray(ix)
        self._iyg = xp.asarray(iy)
        self._band = xp.asarray(grid.band)
        W = np.zeros(grid.Nx) if absorber_W is None else np.asarray(absorber_W, float)
        self.W = W
        self._W = xp.asarray(W.astype(self.rtype))

    # -- structure factor by GEMM -------------------------------------------
    def _phase_matrix(self, q, r):
        """exp(-2 pi i q r) on the backend; the product q r is formed and reduced
        modulo 1 in float64 before the exponential (phase error < 1e-12 rad)."""
        xp = self.xp
        qa = xp.asarray(q, dtype=xp.float64)
        ra = xp.asarray(r, dtype=xp.float64)
        frac = xp.mod(qa[:, None] * ra[None, :], 1.0)
        return xp.exp(-2j * np.pi * frac).astype(self.ctype)

    def projected(self, ax, ay):
        """Real projected potential v(x, y) [V A] of atoms at (ax, ay) (slab frame)."""
        xp = self.xp
        g = self.g
        S = xp.zeros((len(self.ix), len(self.iy)), dtype=self.ctype)
        rx = np.asarray(ax, float) - g.x0
        ry = np.asarray(ay, float) - g.y0
        for s in range(0, len(rx), self.atom_chunk):
            Ex = self._phase_matrix(self._qx, rx[s:s + self.atom_chunk])
            Ey = self._phase_matrix(ry[s:s + self.atom_chunk], self._qy)
            S += Ex @ Ey
        C = xp.zeros((g.Nx, g.Ny), dtype=self.ctype)
        C[xp.ix_(self._ixg, self._iyg)] = S * self._form
        return xp.fft.ifft2(C).real

    def uniform(self, V_of_x, dz):
        """Projected potential of a z-uniform potential profile V(x) over dz [V A],
        band-limited like the atomic potentials."""
        xp = self.xp
        g = self.g
        v = np.repeat(np.asarray(V_of_x, float)[:, None], g.Ny, axis=1) * dz
        V = xp.fft.fft2(xp.asarray(v.astype(self.rtype)))
        V = V * self._band
        return xp.fft.ifft2(V).real

    def transmission(self, v, dz, W_extra=None):
        """t = exp(i sigma v (1 + i alpha) - sigma (W_abs(x) + W_extra(x, y)) dz),
        band-limited.

        v: real projected potential [V A] of the plane; dz: slice thickness that the
        plane represents; W_abs: the artificial absorber profile [V]; W_extra: an
        optional (Nx, Ny) imaginary potential [V] (inelastic absorption inside the
        crystal)."""
        xp = self.xp
        phase = self.sigma * v
        damp = self.sigma * (self.alpha * v + self._W[:, None] * dz)
        if W_extra is not None:
            damp = damp + self.sigma * dz * W_extra
        t = xp.exp((1j * phase - damp).astype(self.ctype))
        T = xp.fft.fft2(t) * self._band
        return xp.fft.ifft2(T).astype(self.ctype)


def absorber_profile(x, bottom_top, bottom_width, top_start, top_width, W_max, power=3):
    """Imaginary potential W(x) [V] of the artificial absorbers: power-law ramps
    W = W_max s^power (s = 0 at the inner edge, 1 at the cell edge) on the bulk side
    and at the top of the vacuum.  Both reach W_max at the cell edges, so W is
    continuous across the periodic wrap.  A cubic ramp (power 3) has continuous value,
    slope and curvature at its inner edge, which keeps its reflection below 2e-5 for
    a 60 A ramp with W_max = 40 V at all angles above 3 mrad (Parratt computation in
    docs/08 section 3.4), while attenuating the amplitude of a wave crossing it at
    45 mrad by more than exp(-9.7) one way.
    """
    x = np.asarray(x, float)
    W = np.zeros_like(x)
    lo = x < bottom_top
    W[lo] = W_max * np.clip((bottom_top - x[lo]) / bottom_width, 0, 1) ** power
    hi = x > top_start
    W[hi] = W_max * np.clip((x[hi] - top_start) / top_width, 0, 1) ** power
    return W


def onset_profile(u, width):
    """Smooth step S(u) = (1 - tanh(u / width)) / 2: 1 inside the crystal (u < 0)."""
    return 0.5 * (1.0 - np.tanh(np.asarray(u, float) / width))
