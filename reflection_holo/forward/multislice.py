"""Custom grazing-incidence multislice kernel (numpy or cupy backend).

STATUS: smoke-tested only. Not yet validated against abTEM or a dynamical reflection solver
(docs/05_final_repository_specification.md section 4.3 and milestone M2). Do not use its absolute
phases or reflectivities as results.

Cell (slab frame of docs/physics_conventions.md): x = outward surface normal (grid axis 0),
y = in-plane perpendicular to the beam (grid axis 1, periodic with a lattice period), z = beam
azimuth = propagation axis (slices). The crystal fills x < 0 over the whole z range and is periodic
along z with the lattice period of the beam azimuth, so only a few distinct slice potentials exist.
That is exact for defects whose fields do not vary along z (dislocation lines parallel to the beam).

Requirements of docs/05 section 4.3 implemented here:
 1. semi-infinite emulation: imaginary-potential absorber on the bulk side, nothing below it;
 2./3. illumination confined to an apodised band in the vacuum above the surface, tilted towards
    the surface by theta_ext as an entrance-plane Fourier component;
 5. 2/3 band limit per axis; the incoming and outgoing beam angles are asserted inside the band;
 6. the mean inner potential of the parameterisation is computed and reported;
 7. absorption as an imaginary potential proportional to the real one (ASSUMPTION, not sourced);
 8. output on the DECLARED exit plane z = L (no back-propagation), dtype recorded;
 9. exact (non-paraxial) propagator.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..geometry import FE_TO_POTENTIAL_V_A2, interaction_constant, wavelength_A

# Peng, Ren, Dudarev and Whelan (1996), Acta Cryst. A52, 257-276, high-angle (0 < s < 6 A^-1) fit,
# f_e(s) = sum a_i exp(-b_i s^2), s = q/2, f_e in A. Si coefficients copied from abTEM 1.0.6
# abtem/parametrizations/data/peng_high.json (sha256 d0bc6b8b...515856), SECTION_READ of that
# file; the paper itself was not read in this environment.
PENG_HIGH_SI = np.array([[0.0567, 0.3365, 0.8104, 2.496, 2.1186],
                         [0.0582, 0.6155, 3.2522, 16.7929, 57.6767]])


def get_xp(backend: str):
    if backend == "numpy":
        return np
    if backend == "cupy":
        import cupy  # noqa: F401  (GPU run: pip install cupy-cuda12x)
        return cupy
    raise ValueError(f"unknown backend {backend!r}")


def to_numpy(a):
    return a.get() if hasattr(a, "get") else np.asarray(a)


def fe_peng(q, params=PENG_HIGH_SI):
    """Electron scattering factor (A) at spatial frequency q (cycles/A)."""
    s2 = (q / 2.0) ** 2
    return sum(a * np.exp(-b * s2) for a, b in params.T)


def mean_inner_potential(n_atoms_per_A3: float, params=PENG_HIGH_SI) -> float:
    """V0 of the parameterisation: (h^2/2 pi m e) f_e(0) n (V)."""
    return float(FE_TO_POTENTIAL_V_A2 * params[0].sum() * n_atoms_per_A3)


@dataclass
class Grid:
    nx: int
    ny: int
    dx: float
    dy: float
    x0: float  # x coordinate (A) of grid row 0; x increases with the row index

    @property
    def x(self):
        return self.x0 + self.dx * np.arange(self.nx)

    @property
    def y(self):
        return self.dy * np.arange(self.ny)

    @property
    def qx(self):
        return np.fft.fftfreq(self.nx, self.dx)

    @property
    def qy(self):
        return np.fft.fftfreq(self.ny, self.dy)

    def band_mask(self):
        """2/3 anti-aliasing band, elliptical in (qx, qy)."""
        qxm = (2 / 3) / (2 * self.dx)
        qym = (2 / 3) / (2 * self.dy)
        QX, QY = np.meshgrid(self.qx, self.qy, indexing="ij")
        return (QX / qxm) ** 2 + (QY / qym) ** 2 < 1.0

    def assert_angle_in_band(self, theta: float, lam: float):
        q = np.sin(theta) / lam
        qxm = (2 / 3) / (2 * self.dx)
        if not q < qxm:
            raise ValueError(f"beam at {theta*1e3:.2f} mrad (q={q:.3f}/A) outside 2/3 band {qxm:.3f}/A")


def slice_potentials(positions, Lz, n_slices, grid: Grid, B_A2: float, absorption_ratio: float,
                     xp=np, chunk: int = 4096, params=PENG_HIGH_SI):
    """Projected potentials (V A) of the n_slices slices of one z-period, complex (V_r + i V_i).

    Each atom is projected entirely into the slice whose centre is nearest to it (projection
    approximation). Structure factors are evaluated exactly (no pixel splatting) by a separable
    matrix product. The Debye-Waller factor exp(-B s^2) damps f_e (static-lattice average).
    """
    dz = Lz / n_slices
    zc = (np.floor(np.mod(positions[:, 2] + dz / 2, Lz) / dz)).astype(int) % n_slices
    qx = xp.asarray(grid.qx)
    qy = xp.asarray(grid.qy)
    q2 = qx[:, None] ** 2 + qy[None, :] ** 2
    fe = xp.zeros_like(q2)
    for a, b in params.T:
        fe = fe + a * xp.exp(-(b + B_A2) * q2 / 4.0)
    out = []
    for s in range(n_slices):
        p = positions[zc == s]
        S = xp.zeros((grid.nx, grid.ny), dtype=xp.complex128)
        for i in range(0, len(p), chunk):
            xs = xp.asarray(p[i:i + chunk, 0] - grid.x0)
            ys = xp.asarray(p[i:i + chunk, 1])
            A = xp.exp(-2j * np.pi * qx[:, None] * xs[None, :])
            Bm = xp.exp(-2j * np.pi * ys[:, None] * qy[None, :])
            S += A @ Bm
        V = xp.fft.ifft2(FE_TO_POTENTIAL_V_A2 * fe * S).real / (grid.dx * grid.dy)
        out.append(V * (1.0 + 1j * absorption_ratio))
    return out, dz


def absorber_profile(grid: Grid, x_top: float, width: float, V_max: float):
    """Imaginary potential (V A per slice thickness, to be multiplied by dz) ramping quadratically
    from 0 at x_top to V_max at x_top - width and constant below, on the bulk side."""
    x = grid.x
    t = np.clip((x_top - x) / width, 0.0, 1.0)
    return V_max * t**2


def illumination(grid: Grid, theta: float, lam: float, x_center: float, height: float, edge: float):
    """Sheet beam in the vacuum band, travelling towards -x at glancing angle theta.

    Flat top of full width `height` with cosine edges of width `edge`, uniform along y.
    """
    x = grid.x
    d = np.abs(x - x_center) - (height / 2 - edge)
    env = np.where(d <= 0, 1.0, np.where(d >= edge, 0.0, 0.5 * (1 + np.cos(np.pi * d / edge))))
    q0 = np.sin(theta) / lam
    psi = (env * np.exp(-2j * np.pi * q0 * x))[:, None] * np.ones((1, grid.ny))
    return psi


def propagator(grid: Grid, dz: float, lam: float, xp=np):
    """Exact free-space propagator over dz with the 2/3 band limit."""
    QX, QY = np.meshgrid(grid.qx, grid.qy, indexing="ij")
    q2 = QX**2 + QY**2
    kz = np.sqrt(np.maximum(1 / lam**2 - q2, 0.0))
    P = np.exp(2j * np.pi * dz * (kz - 1 / lam)) * grid.band_mask()
    return xp.asarray(P.astype(np.complex64))


def transmission(V_slice, sigma, absorber_x, dz, band, xp=np):
    """t = exp(i sigma (V_r + i V_i)) with the bulk absorber added, then band-limited."""
    Vabs = xp.asarray(absorber_x)[:, None] * dz
    t = xp.exp(1j * sigma * (V_slice + 1j * Vabs))
    t = xp.fft.ifft2(xp.fft.fft2(t) * band)
    return t.astype(xp.complex64)


def run(psi0, transmissions, P, n_steps, xp=np, callback=None):
    """psi_{j+1} = P * (t_{j mod m} psi_j), n_steps slices."""
    psi = xp.asarray(psi0.astype(np.complex64))
    m = len(transmissions)
    for j in range(n_steps):
        psi = xp.fft.ifft2(xp.fft.fft2(psi * transmissions[j % m]) * P)
        if callback is not None:
            callback(j, psi)
    return psi


def dark_field(psi_exit, grid: Grid, theta_out: float, lam: float, q_aperture: float,
               vacuum_x: float, vacuum_edge: float):
    """Select the specular beam: vacuum mask, circular aperture of radius q_aperture (cycles/A)
    around (+sin(theta_out)/lam, 0), demodulate the carrier. Returns (psi_df, spectrum_intensity)."""
    x = grid.x
    m = np.clip((x - vacuum_x) / vacuum_edge, 0.0, 1.0)
    m = 0.5 * (1 - np.cos(np.pi * m))
    F = np.fft.fft2(psi_exit * m[:, None])
    q0 = np.sin(theta_out) / lam
    QX, QY = np.meshgrid(grid.qx, grid.qy, indexing="ij")
    ap = (QX - q0) ** 2 + QY**2 < q_aperture**2
    psi = np.fft.ifft2(F * ap) * np.exp(-2j * np.pi * q0 * x)[:, None]
    return psi, np.abs(F) ** 2


def band_profile(psi_df, weights_x=None):
    """Complex average over the x (exit-height) axis, intensity-weighted: phase and amplitude vs y."""
    w = np.abs(psi_df) ** 2 if weights_x is None else weights_x[:, None]
    z = np.sum(psi_df * w, axis=0) / np.maximum(np.sum(w, axis=0), 1e-30)
    return np.angle(z), np.abs(z)


def interaction(E_keV):
    return interaction_constant(E_keV), wavelength_A(E_keV)
