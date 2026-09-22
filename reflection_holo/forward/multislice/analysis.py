"""Measurements on exit waves used by the validation tests and by the pipeline.

Conventions (docs/physics_conventions.md): exp(+i k.r), numpy FFT sign; the reflected (outgoing)
beam rises away from the surface, so its transverse spatial frequency is +sin(theta_out)/lambda;
the step phase is Delta_phi = phi(upper terrace) - phi(lower terrace), wrapped to (-pi, pi].

* ``terrace_step_phase``: the specular beam is selected in k-space (a circular aperture of declared
  radius about (+sin(theta_out)/lambda, 0)); on each terrace region (a y range, all x) the selected
  wave is demodulated by exp(-2 pi i f_c x) and summed, which is its Fourier component at exactly
  f_c = sin(theta_out)/lambda. For two terraces related by a translation R with R.n = h the
  components differ by exp(-i 4 pi f_c h) = exp(-(4 pi/lambda) h sin(theta)) (DERIVED_HERE).
* ``flat_reflection_coefficient``: for a flat surface at x = x_s, each incident plane-wave component
  a(-f) exp(-2 pi i f x) returns as a(-f) r(f) exp(-i 4 pi f x_s) exp(+2 pi i f x), and both carry
  the vacuum propagation factor P_L(f) of the whole length L (k_z is conserved), so
  r(f) = Psi_exit(+f) exp(+i 4 pi f (x_s - x0)) / (Psi_0(-f) P_L(f)) (DERIVED_HERE).
* ``refracted_frequency``: the dominant transverse frequency of the wave inside the crystal (a
  window of x inside the crystal, Hann-weighted), from a fine DFT and a parabolic peak fit.
"""
from __future__ import annotations

import numpy as np

from .propagator import propagator_phase


def wrap(phi):
    return (np.asarray(phi) + np.pi) % (2 * np.pi) - np.pi


def _xy(ew):
    nx, ny = ew.psi.shape
    return ew.x0_A + np.arange(nx) * ew.dx_A, ew.y0_A + np.arange(ny) * ew.dy_A


def select_beam(ew, *, fx_centre_per_A: float, fy_centre_per_A: float,
                radius_per_A: float) -> np.ndarray:
    """k-space selection of one beam: circular aperture about (fx, fy), inverse FFT."""
    nx, ny = ew.psi.shape
    fx = np.fft.fftfreq(nx, ew.dx_A)[:, None]
    fy = np.fft.fftfreq(ny, ew.dy_A)[None, :]
    A = (fx - fx_centre_per_A) ** 2 + (fy - fy_centre_per_A) ** 2 <= radius_per_A**2
    return np.fft.ifft2(np.fft.fft2(ew.psi.astype(np.complex128)) * A)


def terrace_step_phase(ew, *, theta_out_ext_rad: float, aperture_radius_per_A: float,
                       upper_y_range_A, lower_y_range_A) -> dict:
    """Step phase of the specular beam between two terrace regions (module docstring)."""
    lam = ew.metadata["beam"]["wavelength_A"]
    fc = np.sin(theta_out_ext_rad) / lam
    sel = select_beam(ew, fx_centre_per_A=fc, fy_centre_per_A=0.0,
                      radius_per_A=aperture_radius_per_A)
    x, y = _xy(ew)
    demod = sel * np.exp(-2j * np.pi * fc * x)[:, None]

    def comp(rng):
        m = (y >= rng[0]) & (y < rng[1])
        if not np.any(m):
            raise ValueError(f"empty y range {rng}")
        return demod[:, m].sum() * ew.dx_A * ew.dy_A / (rng[1] - rng[0])

    cu, cl = comp(upper_y_range_A), comp(lower_y_range_A)
    return dict(delta_phi_rad=float(wrap(np.angle(cu) - np.angle(cl))),
                phase_upper_rad=float(np.angle(cu)), phase_lower_rad=float(np.angle(cl)),
                amplitude_upper=float(abs(cu)), amplitude_lower=float(abs(cl)),
                f_c_per_A=float(fc), aperture_radius_per_A=float(aperture_radius_per_A),
                convention="Delta_phi = phi(upper) - phi(lower), wrapped to (-pi, pi]")


def geometric_step_phase(h_A: float, theta_ext_rad: float, wavelength_A: float) -> float:
    """-(4 pi / lambda) h sin(theta_ext) (docs/physics_conventions.md, specular beam)."""
    return float(-4 * np.pi / wavelength_A * h_A * np.sin(theta_ext_rad))


def analytic_step_reflection(q1, dK: float):
    """Fresnel coefficient of the 1D step barrier, r = (q1 - q2)/(q1 + q2), q2 = sqrt(q1^2+dK^2),
    for the reference plane at the step (SM04 for dK; DERIVED_HERE)."""
    q1 = np.asarray(q1, float)
    q2 = np.sqrt(q1**2 + dK**2)
    return (q1 - q2) / (q1 + q2)


def flat_reflection_coefficient(ew, psi0: np.ndarray, *, x_surface_A: float,
                                propagator: str, rel_threshold: float) -> dict:
    """r(f) per incident frequency bin whose |Psi_0| >= rel_threshold * max (module docstring).
    psi0 is the launched wave (same grid); the wave is averaged over y (y-invariant problems)."""
    nx = ew.psi.shape[0]
    lam = ew.metadata["beam"]["wavelength_A"]
    out1 = np.fft.fft(ew.psi.astype(np.complex128).mean(axis=1))
    in1 = np.fft.fft(np.asarray(psi0, np.complex128).mean(axis=1))
    f = np.fft.fftfreq(nx, ew.dx_A)

    class _G:
        pass
    g = _G()
    g.fx = lambda: f
    g.fy = lambda: np.zeros(1)
    phase, _ = propagator_phase(g, dz_A=ew.z_A, wavelength_A=lam, kind=propagator)
    PL = np.exp(1j * phase[:, 0])
    thr = rel_threshold * np.abs(in1).max()
    rows = []
    for m in range(1, nx // 2):
        mi = (-m) % nx                      # incident bin at -f
        if f[mi] >= 0 or abs(in1[mi]) < thr:
            continue
        fp = f[m]                           # reflected bin at +f
        r = out1[m] * np.exp(4j * np.pi * fp * (x_surface_A - ew.x0_A)) / (in1[mi] * PL[mi])
        rows.append((fp, r, abs(in1[mi])))
    arr = np.array(rows, dtype=complex)
    return dict(f_per_A=arr[:, 0].real, r=arr[:, 1], weight=arr[:, 2].real)


def refracted_frequency(ew, *, x_range_A, f_guess_per_A: float, half_width_per_A: float,
                        n_fine: int) -> float:
    """Dominant transverse frequency of the wave in x_range (y-averaged, Hann window)."""
    x, _ = _xy(ew)
    m = (x >= x_range_A[0]) & (x < x_range_A[1])
    col = ew.psi.astype(np.complex128).mean(axis=1)[m]
    xs = x[m]
    w = np.hanning(len(xs))
    fs = np.linspace(f_guess_per_A - half_width_per_A, f_guess_per_A + half_width_per_A, n_fine)
    G = np.abs(np.exp(-2j * np.pi * fs[:, None] * xs[None, :]) @ (w * col))
    i = int(np.argmax(G))
    if i == 0 or i == n_fine - 1:
        raise ValueError("refracted peak at the edge of the search window")
    a, b, c = G[i - 1], G[i], G[i + 1]
    return float(fs[i] + 0.5 * (a - c) / (a - 2 * b + c) * (fs[1] - fs[0]))
