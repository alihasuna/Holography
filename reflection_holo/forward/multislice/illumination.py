"""Confined illumination: an apodised sheet beam in the vacuum band (docs/05 section 4.3 item 3).

psi_0(x, y) = A(x) exp(i k_x x),  k_x = -k sin(theta_in_ext)  (descending towards the surface),
uniform along y, launched at the entrance plane z = 0 upstream of the crystal. A(x) = 1 in the core
and rises and falls as sin^2 over an apodisation width e at each edge; the full height H includes
both edges (0 < 2 e <= H). x is the absolute cell coordinate (x = 0 at the bottom of the box), so
the phase reference of the tilt is x = 0. The tilt is an entrance-plane Fourier component, not a
propagator shear. theta_in_ext is PROJECT_INPUT item 7 and REQUIRED with its label.

Downward projection: the launched wave is projected onto the DOWNWARD-travelling components
(spatial frequency f_x < 0) of the grid, psi_0 <- IFFT[ FFT[A(x) exp(i k_x x)] (f_x < 0) ]. The
sin^2 edges leave a spectral tail of relative size ~1e-3 at the specular frequency +sin(theta)/lambda;
without the projection these upward components would travel to the exit plane without touching
the surface and add to the specular beam (a 1 to 2 percent error of the 0.057 flat-surface
reflection amplitude at 16.47 mrad, found in the rung-1 study, M2 report). The projection changes
A(x) by ~1e-3 of its peak, including a tail of that size outside the nominal band (recorded).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reflection_holo.io.labels import require_evidence_label


@dataclass(frozen=True)
class SheetBeam:
    height_A: float
    edge_A: float
    x_bottom_A: float
    theta_in_ext_rad: float
    theta_label: str

    def __post_init__(self):
        require_evidence_label(self.theta_label, "incidence angle (PROJECT_INPUT item 7)",
                               accepted=("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY"),
                               qualified=True)
        if not (np.isfinite(self.height_A) and self.height_A > 0):
            raise ValueError("height_A must be > 0")
        if not (np.isfinite(self.edge_A) and 0 < 2 * self.edge_A <= self.height_A):
            raise ValueError("edge_A must satisfy 0 < 2 edge_A <= height_A")
        if not (np.isfinite(self.theta_in_ext_rad) and 0 < self.theta_in_ext_rad < 0.2):
            raise ValueError("theta_in_ext_rad must be a positive glancing angle below 0.2 rad")
        if not np.isfinite(self.x_bottom_A):
            raise ValueError("x_bottom_A must be finite")

    def profile(self, x_A: np.ndarray) -> np.ndarray:
        x = np.asarray(x_A, float)
        a, e, H = self.x_bottom_A, self.edge_A, self.height_A
        A = np.zeros_like(x)
        core = (x >= a + e) & (x <= a + H - e)
        A[core] = 1.0
        lo = (x > a) & (x < a + e)
        A[lo] = np.sin(0.5 * np.pi * (x[lo] - a) / e) ** 2
        hi = (x > a + H - e) & (x < a + H)
        A[hi] = np.sin(0.5 * np.pi * (a + H - x[hi]) / e) ** 2
        return A

    def fx_per_A(self, wavelength_A: float) -> float:
        """Transverse spatial frequency of the carrier: -sin(theta)/lambda (cycles/A)."""
        return -np.sin(self.theta_in_ext_rad) / wavelength_A

    def describe(self, wavelength_A: float) -> dict:
        return dict(kind="apodised sheet beam (sin^2 edges), uniform in y",
                    height_A=self.height_A, edge_A=self.edge_A, x_bottom_A=self.x_bottom_A,
                    theta_in_ext_rad=self.theta_in_ext_rad, theta_label=self.theta_label,
                    k_x_rad_per_A=-2 * np.pi * np.sin(self.theta_in_ext_rad) / wavelength_A,
                    launched_at_z_A=0.0, tilt="entrance-plane Fourier component (no shear)",
                    projection="onto downward-travelling components f_x < 0",
                    phase_reference="x = 0 (bottom of the box)")


def sheet_beam_wave(beam: SheetBeam, grid, wavelength_A: float) -> np.ndarray:
    """psi_0 on the grid (complex128, numpy): the apodised tilted sheet projected onto f_x < 0
    (module docstring), before band limiting."""
    x = grid.x_A()
    col = beam.profile(x) * np.exp(2j * np.pi * beam.fx_per_A(wavelength_A) * x)
    spec = np.fft.fft(col)
    spec[grid.fx() >= 0] = 0.0
    col = np.fft.ifft(spec)
    return np.repeat(col[:, None], grid.ny, axis=1)


def outside_band_fraction(beam: SheetBeam, grid, wavelength_A: float) -> float:
    """Largest |psi_0| outside [x_bottom, x_bottom + H] relative to the core amplitude 1."""
    x = grid.x_A()
    col = sheet_beam_wave(beam, grid, wavelength_A)[:, 0]
    out = (x < beam.x_bottom_A) | (x > beam.x_bottom_A + beam.height_A)
    return float(np.abs(col[out]).max()) if np.any(out) else 0.0
