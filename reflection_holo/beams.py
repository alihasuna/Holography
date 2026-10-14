"""Incident illumination: a Gaussian sheet beam confined to the vacuum band.

The beam is uniform along y (qy = 0) and Gaussian across x.  It is defined by its
plane-wave spectrum at the focus (waist) plane z_f, where the beam axis passes
through height x_f:

    psi_f(x) = sum_q g(q) exp(2 pi i q (x - x_f)),  g(q) = exp(-(pi w0 (q - q0))^2),
    q0 = -sin(theta0)/lambda  (descending beam, exp(+ik.r) convention).

At the entrance plane z = 0 the coefficient of exp(2 pi i q x) is
    a(q) = g(q) exp(-2 pi i q x_f) exp(-i (kz(q) - k) z_f)
(exact vacuum back-propagation with kz = 2 pi sqrt(1/lambda^2 - q^2)).
w0 is the 1/e amplitude half-width of the waist; the 1/e amplitude half-width of the
angular spectrum is lambda/(pi w0).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def kz_minus_k(q2, lam):
    """2 pi (sqrt(1/lam^2 - q^2) - 1/lam), written without cancellation [rad/A]."""
    inv = 1.0 / lam
    return -2.0 * np.pi * q2 / (np.sqrt(inv * inv - q2) + inv)


@dataclass
class GaussianSheetBeam:
    theta0: float      # rad, external glancing angle of the beam axis
    w0: float          # A, waist (1/e amplitude half-width)
    x_f: float         # A, height of the beam axis at the waist plane
    z_f: float         # A, waist plane along the beam

    def spectrum(self, qx, lam):
        q0 = -np.sin(self.theta0) / lam
        g = np.exp(-(np.pi * self.w0 * (qx - q0)) ** 2)
        return g * np.exp(-2j * np.pi * qx * self.x_f) * np.exp(
            -1j * kz_minus_k(qx**2, lam) * self.z_f)

    def width_at(self, dz, lam):
        """1/e amplitude half-width at distance dz from the waist."""
        zR = np.pi * self.w0**2 / lam
        return self.w0 * np.sqrt(1.0 + (dz / zR) ** 2)

    def axis_height(self, z):
        return self.x_f + (self.z_f - z) * np.tan(self.theta0)


def plan_beam(theta0, w0, lam, clearance_sigmas, margin_A, x_surface_top):
    """Place a beam whose waist sits on the surface plane (x = 0 at the level-0 top
    sheet) such that at the entrance plane z = 0 the beam is entirely above
    ``x_surface_top`` (the highest atom of the structure) by ``clearance_sigmas``
    1/e half-widths plus ``margin_A``.  Returns (beam, z_hit)."""
    z_hit = (clearance_sigmas * w0 + margin_A + x_surface_top) / np.tan(theta0)
    for _ in range(200):
        w = GaussianSheetBeam(theta0, w0, 0.0, z_hit).width_at(z_hit, lam)
        z_new = (clearance_sigmas * w + margin_A + x_surface_top) / np.tan(theta0)
        if abs(z_new - z_hit) < 1e-6:
            break
        z_hit = z_new
    return GaussianSheetBeam(theta0, w0, 0.0, z_hit), z_hit


def entrance_wave(beam, grid, lam, xp, dtype):
    """psi(x, y) at z = 0 on the grid, uniform along y; also returns a(q)."""
    a = beam.spectrum(grid.qx, lam)
    if np.any(np.abs(a[~(np.abs(grid.qx) <= grid.q_band)]) > 1e-12):
        raise ValueError("incident beam spectrum extends outside the band")
    psi_x = grid.Nx * np.fft.ifft(a * np.exp(2j * np.pi * grid.qx * grid.x0))
    psi = np.repeat(psi_x[:, None], grid.Ny, axis=1)
    return xp.asarray(psi.astype(dtype)), a
