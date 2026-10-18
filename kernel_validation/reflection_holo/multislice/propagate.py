"""Fresnel propagator, bandwidth limit, slice loop and optional sub-slicing (rung R2, item 2b).

Geometry (CONTRACT): x is the beam axis. A slice is a (z, y) array of shape (nz, ny).
z is the OUTWARD surface normal (vacuum at +z). The wave is the slowly varying
envelope psi, with the carrier exp(+i K x) removed [kirkland_ch06 p.15, Eq. 6.35; p.28].

Equations and their evidence
----------------------------
P1  Paraxial equation  d psi/dx = [ i lambda/(4 pi) lap_yz + i sigma V ] psi
    SECTION_READ [kirkland_ch06 p.17, Eq. 6.43]. Kirkland's z (beam axis) is our x.
P2  Propagator in Fourier space  P(q, dx) = exp(-i pi lambda q^2 dx), with q in cycles/A
    SECTION_READ [kirkland_ch06 p.23, Eq. 6.65]. P is even in q, so the opposite FFT
    sign of numpy [kirkland_ch04-05 p.7] does not change it. DERIVED_HERE.
P3  Slice step  psi_{n+1} = IFFT{ P * FFT[t_n psi_n] }
    SECTION_READ [kirkland_ch06 p.28, Eq. 6.86]. This is the ordering that the card
    recommends for anti-aliasing [kirkland_ch06 p.36].
P4  Bandwidth: both P and t are set to zero outside 2/3 k_max, k_max = min(1/2dy, 1/2dz)
    SECTION_READ [kirkland_ch06 p.35-36, Eq. 6.92; Table 6.3 step 3].
P5  Composition  P(dx1) P(dx2) = P(dx1 + dx2)  [kirkland_ch06 p.31, Eq. 6.88].
P6  Optional propagator tilt. Kirkland writes exp(+2 pi i dz (k_x tan th_x + k_y tan th_y))
    [kirkland_ch06 p.39, Eq. 6.93; Kirkland 2020 printed p.181] under HIS transform pair,
    FT = sum exp(+2 pi i k.x), FT^-1 = (1/N) sum exp(-2 pi i k.x) [Kirkland 2020 Eqs. 4.6-4.7,
    printed p.87]. numpy's fft2/ifft2 use the opposite signs, so the same physical tilt
    (the wave moves by +dx tan th as it advances by dx) is exp(-2 pi i dx (q_y tan th_y +
    q_z tan th_z)) here. DERIVED_HERE (shift theorem); checked by test_tilt_direction.
    The card limits it to about 1 degree, so a warning is raised above 17.45 mrad. The
    engine does NOT use it: the glancing angle enters as a phase ramp on the incident wave
    (illumination.py).
P7  Paraxial phase error (DERIVED_HERE from the expansion of R, [kirkland_ch06 p.27,
    Eq. 6.81]). The exact angular-spectrum phase per unit length minus the paraxial one is
        d_phi/dx = (2 pi/lambda)(sqrt(1 - alpha^2) - 1) + pi alpha^2/lambda
                 ~ -pi alpha^4/(4 lambda),  with alpha = lambda q.
    The leading relative error of the phase is alpha^2/4. The exact angular-spectrum
    form is NOT on any card; it is used here only to quote the error (label
    UNVERIFIED for any use beyond that).
P8  Sub-slicing: a slice of thickness dx with projected potential v is replaced by
    n_sub steps of dx/n_sub with v/n_sub each. This is the Eq. 6.86 step applied
    with a smaller slice. DERIVED_HERE. The card warns that full-projection
    potentials are not valid below about 1 A [kirkland_ch06 p.33, Eq. 6.90]; this
    module only splits an already projected v and does not re-project.
P9  Flux  I = sum |psi|^2 dy dz.  Unitarity check [kirkland_ch06 p.41, Eq. 6.95].
    With a real potential, no band limit on t and no band limit on P, each step is
    exactly unitary [kirkland_ch06 p.52]. DERIVED_HERE: this holds only for W = 0.
"""
from __future__ import annotations

import math
import warnings
from typing import Iterable, Iterator

import numpy as np

from reflection_holo.constants import interaction_constant, wavelength
from reflection_holo.multislice.potential import Grid, absorber_profile, bandwidth_mask

TILT_LIMIT_RAD: float = math.radians(1.0)   # SECTION_READ [kirkland_ch06 p.39]


def _mask(grid: Grid, bandwidth: float | None) -> np.ndarray | None:
    """Return None (no limit) or the circular mask |q| < bandwidth * k_max (P4)."""
    if bandwidth is None:
        return None
    if not 0 < bandwidth <= 1:
        raise ValueError("bandwidth must be in (0, 1] or None")
    return bandwidth_mask(grid, bandwidth)


def fresnel_propagator(grid: Grid, dx: float, lam: float, bandwidth: float | None = 2 / 3,
                       tilt: tuple[float, float] = (0.0, 0.0)) -> np.ndarray:
    """Fourier-space paraxial propagator P (P2) of shape (nz, ny) in numpy FFT order.

    dx: slice thickness along the beam (A). lam: relativistic wavelength (A).
    bandwidth: fraction of k_max kept (P4). None means no limit, so |P| = 1 everywhere.
    tilt: (theta_y, theta_z) in rad (P6). This is valid only up to about 1 degree,
    and is not used by the engine.
    Labels: SECTION_READ (P2, P4, P6).
    """
    if dx <= 0 or lam <= 0:
        raise ValueError("dx and lam must be > 0 (A)")
    qz, qy = grid.freqs()
    P = np.exp(-1j * np.pi * lam * (qz**2 + qy**2) * dx)
    ty, tz = tilt
    if ty or tz:
        if max(abs(ty), abs(tz)) > TILT_LIMIT_RAD:
            warnings.warn("propagator tilt > 1 degree is outside the card's validity "
                          "[kirkland_ch06 p.39]", UserWarning, stacklevel=2)
        P = P * np.exp(-2j * np.pi * dx * (qy * np.tan(ty) + qz * np.tan(tz)))   # numpy sign (P6)
    m = _mask(grid, bandwidth)
    return P if m is None else P * m


def bandlimit(f: np.ndarray, grid: Grid, bandwidth: float | None = 2 / 3) -> np.ndarray:
    """Set Fourier components of f outside bandwidth * k_max to zero (P4)."""
    m = _mask(grid, bandwidth)
    return f if m is None else np.fft.ifft2(np.fft.fft2(f) * m)


def transmissions_from_potentials(potentials: Iterable[np.ndarray], sigma: float, grid: Grid,
                                  n_sub: int = 1, bandwidth: float | None = 2 / 3
                                  ) -> Iterator[np.ndarray]:
    """Yield the transmission functions exp(i sigma v / n_sub), each repeated n_sub times (P8).

    potentials: complex projected potentials (V*A) per slice. With bandwidth not
    None, each t is band-limited (P4). In that case |t| != 1 in general, and
    unitarity is no longer exact.
    """
    if n_sub < 1:
        raise ValueError("n_sub >= 1")
    for v in potentials:
        t = np.exp(1j * sigma * np.asarray(v) / n_sub)
        t = bandlimit(t, grid, bandwidth)
        for _ in range(n_sub):
            yield t


def multislice(psi0: np.ndarray, slices: Iterable[np.ndarray], propagator: np.ndarray, *,
               grid: Grid | None = None, record_flux: bool = False):
    """Slice loop psi_{n+1} = IFFT{P FFT[t_n psi_n]} (P3). Returns the exit wave.

    slices: transmission functions (one per (sub)slice), each of shape (nz, ny).
    propagator: from fresnel_propagator for the matching (sub)slice thickness.
    With record_flux=True (grid required) this returns (exit_wave, fluxes), where
    fluxes[0] is the incident flux and fluxes[n] is the flux after step n (P9).
    """
    psi = np.array(psi0, dtype=complex, copy=True)
    if psi.shape != propagator.shape:
        raise ValueError("psi0 and propagator shapes differ")
    fl = [flux(psi, grid)] if record_flux else None
    if record_flux and grid is None:
        raise ValueError("record_flux needs grid")
    for t in slices:
        psi = np.fft.ifft2(propagator * np.fft.fft2(t * psi))
        if record_flux:
            fl.append(flux(psi, grid))
    return (psi, np.array(fl)) if record_flux else psi


def flux(psi: np.ndarray, grid: Grid) -> float:
    """Integrated intensity sum |psi|^2 dy dz (P9) [kirkland_ch06 Eq. 6.95]."""
    return float(np.sum(np.abs(psi) ** 2) * grid.dy * grid.dz)


def paraxial_phase_error(alpha: float | np.ndarray, lam: float) -> np.ndarray:
    """Exact minus paraxial propagation phase, in rad per A of beam path (P7). DERIVED_HERE."""
    a = np.asarray(alpha, float)
    exact = (2 * np.pi / lam) * (np.sqrt(1.0 - a**2) - 1.0)
    parax = -np.pi * a**2 / lam
    return exact - parax


def measure_absorber_reflection(theta: float, E_eV: float, strength_V: float = 10.0,
                                z_top: float = 60.0, shape: str = "cos2", dz: float = 0.15,
                                nz: int = 2048, dx: float = 5.0, z_start: float = 200.0,
                                width: float = 15.0) -> dict:
    """Numerical reflection test of the graded absorber (NOTES_B section 3). DERIVED_HERE.

    A Gaussian packet (1/e half-width `width`, centred at z_start) travels toward
    -z at transverse angle theta (exp(-i K sin(theta) z), as in illumination.py)
    into absorber_profile(z_top, strength_V, shape). The run is free space except
    for the absorber. It is propagated until the packet reflected from z_top
    would be back at z_start. Under the numpy FFT convention a +z-travelling
    component sits at q_z > 0.
    Returns R = flux(q_z > 0)/flux_in and remaining_incident = flux(q_z < 0)/flux_in.
    """
    lam = wavelength(E_eV)
    sig = interaction_constant(E_eV)
    grid = Grid(ny=1, nz=nz, dy=1.0, dz=dz)
    z = grid.z[:, None]
    q0 = math.sin(theta) / lam
    psi = np.exp(-((z - z_start) / width) ** 2) * np.exp(-2j * np.pi * q0 * z)
    psi /= math.sqrt(flux(psi, grid))
    t = np.exp(1j * sig * absorber_profile(grid, z_top, strength_V, shape, dx_slice=dx))
    P = fresnel_propagator(grid, dx, lam, bandwidth=None)
    L = 2.0 * (z_start - z_top) / math.tan(theta)
    n = int(math.ceil(L / dx))
    for _ in range(n):
        psi = np.fft.ifft2(P * np.fft.fft2(t * psi))
    Psi = np.abs(np.fft.fft2(psi)) ** 2
    qz = grid.freqs()[0][:, 0]
    tot = np.sum(Psi) / flux(psi, grid) if flux(psi, grid) > 0 else 1.0  # Parseval scale
    up = float(np.sum(Psi[qz > 0]) / tot)
    down = float(np.sum(Psi[qz < 0]) / tot)
    return {"R": up, "remaining_incident": down, "path_A": n * dx, "n_slices": n,
            "theta": theta, "shape": shape, "strength_V": strength_V, "z_top": z_top}


def _main() -> None:  # prints every number quoted in NOTES_B.md for this module
    from reflection_holo import project_inputs as _pi
    E0 = _pi.get("E0")
    lam = wavelength(E0)
    print(f"lambda(E0)                    = {lam:.8f} A")
    for a in (0.010, 0.020, 0.030):
        e = float(paraxial_phase_error(a, lam))
        print(f"paraxial error alpha={a*1e3:4.0f} mrad: {e:+.4e} rad/A, {e*1e4:+.4f} rad/um, "
              f"leading -pi a^4/(4 lam) = {-np.pi*a**4/(4*lam):+.4e}, rel a^2/4 = {a*a/4:.2e}")
    for th in (8.4e-3, 20e-3):
        for sh in ("cos2", "step"):
            r = measure_absorber_reflection(th, E0, shape=sh)
            print(f"absorber 10 V, z_top 60 A, {sh:4s}, theta={th*1e3:4.1f} mrad: "
                  f"R = {r['R']:.3e}, remaining incident = {r['remaining_incident']:.3e}, "
                  f"path {r['path_A']:.0f} A")


if __name__ == "__main__":
    _main()
