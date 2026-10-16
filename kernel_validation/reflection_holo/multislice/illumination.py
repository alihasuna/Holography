"""Vacuum-confined tilted incident wave for the grazing-incidence (Peng-Cowley) multislice.

Evidence labels used below: SECTION_READ, DERIVED_HERE, ASSUMPTION, UNVERIFIED.

Geometry (CONTRACT): x = beam axis (slices perpendicular to x); z = outward surface normal
(vacuum at +z); y = in-surface transverse direction. Waves are exp(+i k.r) (repo conventions).
The glancing angle theta_ext is measured from the surface plane.

Physics
-------
* Peng's mask lets through only the beam that illuminates the surface, with a rounded edge to
  avoid Fresnel fringes (card:peng_ch05 p.8 as quoted in NOTES_C; that card is not in this
  integration set -> UNVERIFIED here). A compact cos^2 edge is used (ASSUMPTION): the entrance-
  plane end-face fraction is then exactly 0.
* DERIVED_HERE: a beam travelling toward -z at glancing angle theta has k_z = -K sin(theta),
  K = 2 pi/lambda, so psi0(y, z) = w(z) exp(-i K sin(theta) (z - z_surface)); it appears at
  q = -sin(theta)/lambda under the numpy FFT sign (repo conventions 'Fourier transform').
* Bandwidth (integration fix): the guard now uses the SAME isotropic limit as the propagator and
  the potential, 2/3 * k_max with k_max = min(1/(2dy), 1/(2dz)) (potential.Grid.kmax). The old guard
  used 1/(2dz) only; on a grid with dy = 0.48 A it passed a 20 mrad beam (q = 0.797/A) that the
  propagator's 0.694/A circle then deleted, which produced the spurious end-face fraction 0.078.
"""
from __future__ import annotations

import numpy as np

from .potential import Grid
from .propagate import flux


def z_axis(grid: Grid) -> np.ndarray:
    """z coordinate (A) of each grid row; rows index z, columns index y."""
    return grid.z0 + grid.dz * np.arange(grid.nz)


def soft_window(z: np.ndarray, z_window: tuple[float, float], softness: float) -> np.ndarray:
    """Compact window: 1 on [z0+s, z1-s], cos^2 ramps of width s, exactly 0 outside (z0, z1).
    ASSUMPTION (compact support; zero value and slope at both ends of each ramp)."""
    z0, z1 = z_window
    s = float(softness)
    if z1 - z0 <= 2 * s:
        raise ValueError(f"window ({z0},{z1}) narrower than 2*softness={2*s}")
    w = np.zeros_like(z, dtype=float)
    inner = (z >= z0 + s) & (z <= z1 - s)
    w[inner] = 1.0
    lo = (z > z0) & (z < z0 + s)
    w[lo] = np.sin(0.5 * np.pi * (z[lo] - z0) / s) ** 2
    hi = (z > z1 - s) & (z < z1)
    w[hi] = np.sin(0.5 * np.pi * (z1 - z[hi]) / s) ** 2
    return w


def bandwidth_ok(grid: Grid, theta_ext: float, lam: float, softness: float, bandwidth: float = 2 / 3) -> bool:
    """True if |sin(theta)|/lambda + 1/softness < bandwidth * grid.kmax.

    grid.kmax = min(1/(2dy), 1/(2dz)) is the circle used by fresnel_propagator and
    projected_potential (consistency fix, DERIVED_HERE). The 1/softness margin is an ASSUMPTION
    (main lobe of the edge spectrum).
    """
    q = abs(np.sin(theta_ext)) / lam
    return q + 1.0 / softness < bandwidth * grid.kmax


def incident_wave(grid: Grid, theta_ext: float, lam: float, z_surface: float,
                  z_window: tuple[float, float], softness: float) -> np.ndarray:
    """Plane wave at glancing angle theta_ext toward -z, confined to z_window, unit flux.

    psi0 = w(z) exp(-i K sin(theta_ext) (z - z_surface)), uniform in y (DERIVED_HERE).
    Raises ValueError if the window reaches below the surface (end-face leakage), reaches the top
    of the grid (z wrap), or if the tilt is outside the propagator's bandwidth.
    Not band-limited here (so the entrance end-face fraction is exactly 0); the kernel
    (reflectivity.exit_wave) band-limits and renormalises before propagating.
    """
    z0, z1 = z_window
    if z0 < z_surface:
        raise ValueError("illumination window extends below the surface: end-face leakage")
    ztop = grid.z0 + grid.dz * (grid.nz - 1)
    if z1 >= ztop:
        raise ValueError("illumination window reaches the top of the grid (z wrap)")
    if not bandwidth_ok(grid, theta_ext, lam, softness):
        raise ValueError(
            f"tilt sin(theta)/lambda={np.sin(theta_ext)/lam:.3f} 1/A + 1/softness exceeds the 2/3 "
            f"bandwidth {2 * grid.kmax / 3:.3f} 1/A (dy={grid.dy}, dz={grid.dz}); reduce dy/dz")
    z = z_axis(grid)
    K = 2.0 * np.pi / lam
    col = soft_window(z, z_window, softness) * np.exp(-1j * K * np.sin(theta_ext) * (z - z_surface))
    psi = np.repeat(col[:, None], grid.ny, axis=1).astype(complex)
    psi /= np.sqrt(flux(psi, grid))
    return psi


def plateau_amplitude(psi0: np.ndarray, grid: Grid, z_window: tuple[float, float]) -> float:
    """|psi0| at the window centre: the plane-wave amplitude a_inc that r is referred to (DERIVED_HERE)."""
    z = z_axis(grid)
    i = int(np.argmin(np.abs(z - 0.5 * (z_window[0] + z_window[1]))))
    return float(np.abs(psi0[i, 0]))


def end_face_fraction(psi: np.ndarray, grid: Grid, z_surface: float) -> float:
    """Fraction of |psi|^2 at z < z_surface on a plane x = const (task requirement < 1e-3)."""
    z = z_axis(grid)
    tot = float(np.sum(np.abs(psi) ** 2))
    return float(np.sum(np.abs(psi[z < z_surface]) ** 2)) / tot


def _main() -> None:  # prints the end-face fractions quoted in INTEGRATION_NOTES.md
    from ..constants import wavelength
    from ..geometry import Surface
    from .cell import flat_surface_cell
    from .propagate import bandlimit, fresnel_propagator, multislice
    E = 200e3
    lam = wavelength(E)
    g = Grid(32, 4096, 0.12, 0.08, 0.0, 0.0)
    psi = incident_wave(g, 20e-3, lam, 100.0, (103.0, 150.0), 3.0)
    psi1 = multislice(psi, [np.ones_like(psi)], fresnel_propagator(g, 1.92, lam))
    print(f"test grid (dy 0.12, dz 0.08), 20 mrad: end-face x=0 {end_face_fraction(psi, g, 100.0):.3e}, "
          f"after one 1.92 A slice {end_face_fraction(psi1, g, 100.0):.3e}")
    th = 16.474e-3  # (0,0,8) external angle at V0 = 12 V (ASSUMPTION), calculator sec.4b
    c = flat_surface_cell(Surface((0, 0, 1), (1, 1, 0)), E, th, absorption=False)
    ang = c.meta["angle"]
    p0 = incident_wave(c.grid, th, lam, c.z_surface, ang["window"], c.meta["softness"])
    pb = bandlimit(p0, c.grid, 2 / 3)
    pb = pb / np.sqrt(flux(pb, c.grid))
    p1 = multislice(pb, [np.ones_like(pb)], fresnel_propagator(c.grid, c.dx, lam))
    print(f"default Si(001) cell (dy {c.grid.dy:.4f}, dz {c.grid.dz}), {th*1e3:.3f} mrad: end-face raw x=0 "
          f"{end_face_fraction(p0, c.grid, c.z_surface):.3e}, band-limited x=0 "
          f"{end_face_fraction(pb, c.grid, c.z_surface):.3e}, after one slice "
          f"{end_face_fraction(p1, c.grid, c.z_surface):.3e}; q_rod {ang['q_rod']:.3f} < limit "
          f"{ang['q_limit']:.3f}: {ang['rod_in_band']}")


if __name__ == "__main__":
    _main()
