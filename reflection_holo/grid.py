"""Simulation grid in the (x, y) plane perpendicular to the beam (z)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _fft_friendly(n):
    m = n
    for p in (2, 3, 5, 7):
        while m % p == 0:
            m //= p
    return m == 1


@dataclass
class Grid:
    Nx: int
    Ny: int
    Lx: float
    Ly: float
    x0: float          # x of the first sample (absolute slab-frame coordinate)
    y0: float = 0.0
    band_fraction: float = 2.0 / 3.0

    def __post_init__(self):
        for n in (self.Nx, self.Ny):
            if not _fft_friendly(n):
                raise ValueError(f"grid size {n} has prime factors > 7")
        self.dx = self.Lx / self.Nx
        self.dy = self.Ly / self.Ny
        self.x = self.x0 + self.dx * np.arange(self.Nx)
        self.y = self.y0 + self.dy * np.arange(self.Ny)
        self.qx = np.fft.fftfreq(self.Nx, self.dx)        # cycles/A
        self.qy = np.fft.fftfreq(self.Ny, self.dy)
        self.q_nyquist = min(0.5 / self.dx, 0.5 / self.dy)
        self.q_band = self.band_fraction * self.q_nyquist
        self.q2 = self.qx[:, None] ** 2 + self.qy[None, :] ** 2
        self.band = self.q2 <= self.q_band**2

    def band_indices(self):
        """Indices of qx and qy inside the rectangular hull of the band."""
        ix = np.nonzero(np.abs(self.qx) <= self.q_band)[0]
        iy = np.nonzero(np.abs(self.qy) <= self.q_band)[0]
        return ix, iy

    def max_angle_mrad(self, wavelength_A):
        """Largest scattering angle represented inside the band (|q| lambda)."""
        return 1e3 * self.q_band * wavelength_A

    def describe(self):
        return dict(Nx=self.Nx, Ny=self.Ny, Lx_A=self.Lx, Ly_A=self.Ly, dx_A=self.dx,
                    dy_A=self.dy, x0_A=self.x0, y0_A=self.y0,
                    band_fraction=self.band_fraction, q_band_per_A=self.q_band)
