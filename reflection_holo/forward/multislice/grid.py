"""Real-space grid, anti-aliasing band limit and the band assertion (docs/05 section 4.3 item 5).

The pixel size is DERIVED from the cell extent and the number of grid points (dx = extent_x / nx,
dy = extent_y / ny) and ASSERTED against the band limit; there is no advisory pixel parameter.
Grid axes: x = surface normal (row index), y = in-plane transverse (column index); x = x0 + i dx
with x0 = 0 at the bottom of the reflection cell, y = y0 + j dy with y0 = 0.

Band-limit rules (source map SM15):
  * "2/3": |f| up to 2/3 of the Nyquist frequency of each axis, f_max = 1/(3 d). Source
    UNVERIFIED (its attribution to Kirkland, B06, is not read; P04 does not state it).
  * "half_nyquist": f_max = 1/(4 d), Prismatic's anti-aliasing aperture (SECTION_READ of P04 p. 3
    and the Prismatic source, params.h:241-242).
The aperture is the ellipse (fx/fx_max)^2 + (fy/fy_max)^2 <= 1 (a circle for dx = dy; an axis
with a single grid point carries only f = 0 and is ignored). Because the ellipse lies inside the
rectangle |fx| <= fx_max, |fy| <= fy_max, the product of two functions limited to it aliases only
outside the band for the "2/3" rule (DERIVED_HERE). The transmission function and the wave are both
band-limited (as abTEM 1.0.10 does, multislice.py:403 and :173, SECTION_READ, D3).

Assertion: every beam declared by the caller (incident and outgoing external glancing angles and
the internal refracted angles) must have its transverse spatial frequency sin(theta)/lambda inside
the x-axis band: the OUTGOING beam angle must lie inside the band limit (docs/05 4.3 item 5).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reflection_holo.geometry.errors import SamplingError
from reflection_holo.geometry.sampling import antialias_max_angle_rad, require_angle_in_band

BAND_LIMIT_RULES = {
    "2/3": dict(fraction_of_nyquist=2.0 / 3.0, geometry_rule="two_thirds",
                label="UNVERIFIED: 2/3 rule; attribution to B06 (Kirkland) not read (SM15)"),
    "half_nyquist": dict(fraction_of_nyquist=0.5, geometry_rule="half_nyquist",
                         label="SECTION_READ: Prismatic anti-aliasing aperture at half the maximum "
                               "scattering angle (P04 p. 3; params.h:241-242) (SM15)"),
}


@dataclass(frozen=True)
class Grid:
    nx: int
    ny: int
    dx_A: float
    dy_A: float
    x0_A: float
    y0_A: float

    @property
    def shape(self) -> tuple[int, int]:
        return (self.nx, self.ny)

    @property
    def extent_x_A(self) -> float:
        return self.nx * self.dx_A

    @property
    def extent_y_A(self) -> float:
        return self.ny * self.dy_A

    def x_A(self) -> np.ndarray:
        return self.x0_A + np.arange(self.nx) * self.dx_A

    def y_A(self) -> np.ndarray:
        return self.y0_A + np.arange(self.ny) * self.dy_A

    def fx(self) -> np.ndarray:
        """Spatial frequencies along x in cycles/A (numpy FFT order)."""
        return np.fft.fftfreq(self.nx, self.dx_A)

    def fy(self) -> np.ndarray:
        return np.fft.fftfreq(self.ny, self.dy_A)


def _positive_int(n, name) -> int:
    if int(n) != n or int(n) < 1:
        raise ValueError(f"{name} must be a positive integer, got {n!r}")
    return int(n)


def fft_friendly(n: int) -> int:
    """Smallest integer >= n whose prime factors are 2, 3, 5, 7 (fast FFT sizes)."""
    m = max(1, int(np.ceil(n)))
    while True:
        k = m
        for p in (2, 3, 5, 7):
            while k % p == 0:
                k //= p
        if k == 1:
            return m
        m += 1


def make_grid(cell, *, nx: int, ny: int) -> Grid:
    """Grid spanning the reflection cell's (x, y) box: dx = extent_x / nx, dy = extent_y / ny
    (DERIVED, never advisory)."""
    nx = _positive_int(nx, "nx")
    ny = _positive_int(ny, "ny")
    return Grid(nx=nx, ny=ny, dx_A=float(cell.extent_x_A) / nx, dy_A=float(cell.extent_y_A) / ny,
                x0_A=0.0, y0_A=0.0)


def grid_shape_for_pixel(cell, *, max_pixel_A: float, fft_sizes: bool) -> tuple[int, int]:
    """(nx, ny) such that the DERIVED pixel sizes do not exceed max_pixel_A (planning helper; the
    band assertion is still made on the derived pixel). fft_sizes: round up to 2,3,5,7-smooth."""
    if not max_pixel_A > 0:
        raise ValueError("max_pixel_A must be positive")
    nx = int(np.ceil(float(cell.extent_x_A) / max_pixel_A - 1e-9))
    ny = int(np.ceil(float(cell.extent_y_A) / max_pixel_A - 1e-9))
    if fft_sizes:
        nx, ny = fft_friendly(nx), fft_friendly(ny)
    return nx, ny


def band_limits_per_A(grid: Grid, rule: str) -> tuple[float, float]:
    """(fx_max, fy_max) in cycles/A; fy_max = inf for ny = 1."""
    if rule not in BAND_LIMIT_RULES:
        raise ValueError(f"band_limit must be one of {tuple(BAND_LIMIT_RULES)}, got {rule!r}")
    frac = BAND_LIMIT_RULES[rule]["fraction_of_nyquist"]
    fxm = frac / (2.0 * grid.dx_A)
    fym = frac / (2.0 * grid.dy_A) if grid.ny > 1 else np.inf
    return float(fxm), float(fym)


def band_limit_mask(grid: Grid, rule: str) -> np.ndarray:
    """Boolean (nx, ny) aperture in numpy FFT order (module docstring)."""
    fxm, fym = band_limits_per_A(grid, rule)
    fx = grid.fx()[:, None]
    fy = grid.fy()[None, :]
    r2 = (fx / fxm) ** 2 + ((fy / fym) ** 2 if np.isfinite(fym) else 0.0 * fy)
    return r2 <= 1.0


def check_band(grid: Grid, *, rule: str, wavelength_A: float, angles_rad: dict) -> dict:
    """Assert that every declared beam lies inside the x-axis band (SamplingError otherwise).

    angles_rad: name -> glancing angle (rad) of a beam tilted in the x-z plane (incident, outgoing,
    internal). The condition is sin(theta)/lambda <= fx_max, and the same angle is passed to
    reflection_holo.geometry.sampling.require_angle_in_band (the SM15 ceiling lambda q_max).
    Returns the record stored in ExitWave.metadata["band_limit"].
    """
    if not angles_rad:
        raise ValueError("at least the incident and outgoing beam angles must be declared")
    fxm, fym = band_limits_per_A(grid, rule)
    geom_rule = BAND_LIMIT_RULES[rule]["geometry_rule"]
    ceiling = antialias_max_angle_rad(grid.dx_A, wavelength_A, rule=geom_rule)
    rows = {}
    for name, th in angles_rad.items():
        th = float(th)
        f = abs(np.sin(th)) / wavelength_A
        if f > fxm:
            raise SamplingError(
                f"beam '{name}' at {th * 1e3:.3f} mrad has |fx| = {f:.4f} 1/A outside the {rule} "
                f"band fx_max = {fxm:.4f} 1/A (derived pixel dx = {grid.dx_A:.5f} A; source map "
                f"SM15)")
        require_angle_in_band(th, grid.dx_A, wavelength_A, rule=geom_rule)
        rows[name] = dict(theta_mrad=th * 1e3, fx_per_A=f, fraction_of_band=f / fxm)
    return dict(rule=rule, rule_label=BAND_LIMIT_RULES[rule]["label"],
                fx_max_per_A=fxm, fy_max_per_A=(None if not np.isfinite(fym) else fym),
                angle_ceiling_x_mrad=ceiling * 1e3,
                aperture="ellipse (fx/fx_max)^2 + (fy/fy_max)^2 <= 1, applied to the wave and to "
                         "the transmission function of every slice",
                pixel_derived=dict(dx_A=grid.dx_A, dy_A=grid.dy_A,
                                   note="dx = extent_x / nx, dy = extent_y / ny (derived)"),
                beams=rows)
