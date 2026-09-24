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

Azimuthal (y) tilt: ``TiltedSheetBeam`` (report E3; H2 N3). The beam direction is
u = (-sin theta_g, u_y, sqrt(1 - sin^2 theta_g - u_y^2)), theta_g the glancing angle to the surface
(the member's own, PROJECT_INPUT item 7 or a convergence member of item 3) and u_y the direction
cosine along y (the tilt theta_y = lambda f_y of docs/physics_conventions.md, f_y = u_y/lambda). The
cell is periodic in y, so the y tilt is carried EXACTLY by the Bloch (twisted-boundary) form
(DERIVED_HERE): for a y-periodic transmission function t(x, y), psi = exp(2 pi i f_y y) u with u
periodic in y; t psi = exp(2 pi i f_y y) (t u), and the free propagation of psi is the propagation
of u with the kernel evaluated at the PHYSICAL frequencies (f_x, f_y' + f_y), f_y' the grid
frequencies. The engine therefore launches the untilted, y-uniform envelope u_0 = ``sheet_beam_wave``
and builds its propagators on ``BlochShiftedGrid``; no y frequency has to be commensurate with the
cell, and the band limit (anti-aliasing of the products t u on the grid) applies to the NATIVE
frequencies of u, on which every beam of the member keeps f_y' = 0. The exit wave is the envelope u;
the physical wave is psi = u exp(2 pi i f_y y) exp(i k z) (recorded in ExitWave.metadata["bloch"]).
For u_y = 0 the engine takes the untilted code path exactly (bit-identical exit wave).
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


@dataclass(frozen=True)
class TiltedSheetBeam:
    """Sheet beam tilted in the x-z plane (glancing angle theta_in_ext_rad) AND in y (direction
    cosine direction_cosine_y), e.g. one member of a convergence ensemble (report E3). Every field is
    required (no defaults).

    height_A, edge_A, x_bottom_A, theta_in_ext_rad, theta_label   as SheetBeam; theta_in_ext_rad is
        the GLANCING angle of this direction to the surface plane (arcsin of -u_x)
    direction_cosine_y   u_y = lambda f_y, the tilt theta_y of docs/physics_conventions.md
        (dimensionless; |u_y| < 0.2)
    tilt_label           evidence label of the y tilt (e.g. "PROJECT_INPUT item 3: convergence
        member 5 of ..." or "TEST_ONLY ...")
    The y tilt is carried by the Bloch form (module docstring); ``sheet_beam_wave`` returns the
    y-uniform envelope u_0 for this beam as for a SheetBeam."""
    height_A: float
    edge_A: float
    x_bottom_A: float
    theta_in_ext_rad: float
    theta_label: str
    direction_cosine_y: float
    tilt_label: str

    def __post_init__(self):
        SheetBeam(height_A=self.height_A, edge_A=self.edge_A, x_bottom_A=self.x_bottom_A,
                  theta_in_ext_rad=self.theta_in_ext_rad, theta_label=self.theta_label)
        require_evidence_label(self.tilt_label, "azimuthal (y) tilt of the sheet beam",
                               accepted=("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY"),
                               qualified=True)
        uy = self.direction_cosine_y
        if isinstance(uy, bool) or not isinstance(uy, (int, float, np.floating)) \
                or not np.isfinite(uy) or abs(float(uy)) >= 0.2:
            raise ValueError(f"direction_cosine_y must be a finite number with |u_y| < 0.2, got "
                             f"{uy!r}")
        if np.sin(self.theta_in_ext_rad) ** 2 + float(uy) ** 2 >= 1.0:
            raise ValueError("the beam direction has no component along z")

    def profile(self, x_A: np.ndarray) -> np.ndarray:
        return self._untilted().profile(x_A)

    def fx_per_A(self, wavelength_A: float) -> float:
        return self._untilted().fx_per_A(wavelength_A)

    def fy_per_A(self, wavelength_A: float) -> float:
        """Physical y spatial frequency of the beam, f_y = u_y / lambda (cycles/A)."""
        return float(self.direction_cosine_y) / wavelength_A

    def _untilted(self) -> SheetBeam:
        return SheetBeam(height_A=self.height_A, edge_A=self.edge_A, x_bottom_A=self.x_bottom_A,
                         theta_in_ext_rad=self.theta_in_ext_rad, theta_label=self.theta_label)

    def describe(self, wavelength_A: float) -> dict:
        d = self._untilted().describe(wavelength_A)
        uy = float(self.direction_cosine_y)
        d.update(kind="apodised sheet beam (sin^2 edges), tilted in x-z AND in y (Bloch form)",
                 direction_cosine_y=uy, tilt_label=self.tilt_label,
                 theta_y_mrad=uy * 1e3, fy_per_A=uy / wavelength_A,
                 k_y_rad_per_A=2 * np.pi * uy / wavelength_A,
                 direction=[-float(np.sin(self.theta_in_ext_rad)), uy,
                            float(np.sqrt(1.0 - np.sin(self.theta_in_ext_rad) ** 2 - uy ** 2))],
                 y_tilt_representation=(
                     "Bloch (twisted-boundary) form: the engine launches the y-uniform envelope "
                     "u_0 and evaluates the propagator at f_y' + f_y; the physical wave is "
                     "u exp(2 pi i f_y y); exact for a y-periodic cell (illumination.py docstring)"))
        return d


class BlochShiftedGrid:
    """A view of a multislice Grid whose y frequencies are shifted by the Bloch frequency f_y of a
    y-tilted beam: fy() = grid.fy() + f_y (the PHYSICAL frequencies of the envelope's components).
    Used ONLY to build the propagator kernels (propagator.propagator_phase reads fx() and fy()); the
    band-limit mask stays on the native grid (module docstring)."""

    def __init__(self, grid, fy_shift_per_A: float):
        f = float(fy_shift_per_A)
        if not np.isfinite(f):
            raise ValueError("the Bloch frequency must be finite")
        self._grid = grid
        self.fy_shift_per_A = f

    def __getattr__(self, name):
        if name == "_grid":                      # not yet set (copy/pickle): no recursion
            raise AttributeError(name)
        return getattr(self._grid, name)

    def fx(self) -> np.ndarray:
        return self._grid.fx()

    def fy(self) -> np.ndarray:
        return self._grid.fy() + self.fy_shift_per_A


def bloch_fy_per_A(beam, wavelength_A: float) -> float:
    """Bloch frequency f_y (cycles/A) of a beam: u_y/lambda for a TiltedSheetBeam, exactly 0.0 for a
    SheetBeam (which takes the untilted code path)."""
    if isinstance(beam, TiltedSheetBeam):
        return beam.fy_per_A(wavelength_A)
    if isinstance(beam, SheetBeam):
        return 0.0
    raise TypeError(f"beam must be a SheetBeam or a TiltedSheetBeam, got {type(beam).__name__}")


def bloch_record(beam, wavelength_A: float) -> dict | None:
    """The record stored in ExitWave.metadata["bloch"] for a TiltedSheetBeam (None otherwise)."""
    if not isinstance(beam, TiltedSheetBeam):
        return None
    fy = beam.fy_per_A(wavelength_A)
    return dict(fy_per_A=fy, direction_cosine_y=float(beam.direction_cosine_y),
                tilt_label=beam.tilt_label,
                psi_is="the y-periodic Bloch envelope u; the physical wave is "
                       "psi * exp(2 pi i fy_per_A y) * exp(i k z), y the absolute cell coordinate "
                       "y0_A + j dy_A",
                propagator="kernels evaluated at (f_x, f_y' + fy_per_A); band mask on the native "
                           "frequencies f_y'")


def sheet_beam_wave(beam: SheetBeam, grid, wavelength_A: float) -> np.ndarray:
    """psi_0 on the grid (complex128, numpy): the apodised tilted sheet projected onto f_x < 0
    (module docstring), before band limiting. For a TiltedSheetBeam this is the y-uniform Bloch
    envelope u_0 (the y tilt is carried by the propagator, module docstring)."""
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
