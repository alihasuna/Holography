"""Image formation and off-axis hologram formation (numpy; scipy only for biprism Fresnel edges).

Runs in: em-holography (CPU). Also importable in em-abtem. No GPU code here.

Model (docs/05_final_repository_specification.md §5, docs/03_physics_summary.md §6):

  image wave        psi_img = IFFT[ T(q - q_spot) FFT[psi_exit] ]   (objective aperture + optional defocus/Cs,
                                                                     centred on the selected spot; recentred)
  hologram          I = |O|² + |R|² + 2 mu Re(O R*)                  (intensity, averaged over phonon configs)
                    O = a_o psi_img E_o,   R = a_r exp(-2πi q_c·r) exp(i phi_d) E_r
  detector          bin to pixels (pixel integration) -> MTF -> counts (dose × pixel area × gain) -> Poisson

With this sign choice the sideband at +q_c (numpy FFT) carries O R* ∝ psi_img exp(-i phi_d): +phase of the
object. mu = (degree of coherence) × |sinc(drift / s)|; the detector MTF reduces the recorded contrast further.
E_o, E_r are the biprism edge functions (straight-edge Fresnel diffraction), 1 everywhere if no overlap width.
"""

import math

import numpy as np

from holo_common import fft_freqs


# ---------------------------------------------------------------------------------------------------------------
# Crystallography for spot selection (Si, diamond cubic; slab frame from si110_cleave_slab_generator)
# ---------------------------------------------------------------------------------------------------------------
DIAMOND_BASIS = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0],
                          [.25, .25, .25], [.25, .75, .75], [.75, .25, .75], [.75, .75, .25]])


def diamond_structure_factor(hkl):
    """F_hkl / f for the 8-atom diamond cell, exp(+2πi g·r) convention. |F| = 0: kinematically forbidden."""
    h = np.asarray(hkl, float)
    return complex(np.exp(2j * np.pi * DIAMOND_BASIS @ h).sum())


def spot_vector(hkl, a_A, rotation_rows):
    """g = (h, k, l)/a in cycles/Å, rotated into the slab frame (rows = slab x, y, z in crystal coordinates)."""
    R = np.asarray(rotation_rows, float)
    return R @ (np.asarray(hkl, float) / a_A)


# ---------------------------------------------------------------------------------------------------------------
# Apertures (radius and taper in cycles/Å, never in pixels: audit A-M6)
# ---------------------------------------------------------------------------------------------------------------
def aperture_profile(r, radius, edge, taper):
    """Radial aperture profile. edge: hard | hann | hamming | tanh.

    hann / hamming: flat to radius - taper/2, raised-cosine roll-off to 0 at radius + taper/2 (the si110
    specular_filter's raised_cosine_disk, here in physical units; its 'hamming' is a rescaled raised cosine that
    reaches 0, kept for continuity). tanh: HoloSpy's aperture_function, 0.5 (1 - tanh((r - radius)/(taper/2)))."""
    r = np.asarray(r, float)
    if edge == "hard":
        return (r <= radius).astype(float)
    if edge == "tanh":
        if taper <= 0:
            raise ValueError("tanh aperture needs taper > 0")
        return 0.5 * (1.0 - np.tanh((r - radius) / (0.5 * taper)))
    if edge in ("hann", "hamming"):
        if taper <= 0:
            return (r <= radius).astype(float)
        r_in, r_out = radius - 0.5 * taper, radius + 0.5 * taper
        if r_in < 0:
            raise ValueError(f"taper {taper} larger than twice the radius {radius}")
        t = np.clip((r - r_in) / (r_out - r_in), 0.0, 1.0)
        if edge == "hann":
            w = 0.5 * (1.0 + np.cos(np.pi * t))
        else:
            a = 0.54
            b = 2 * a - 1
            w = (a + (1 - a) * np.cos(np.pi * t) - b) / (1 - b)
        return np.where(r <= r_in, 1.0, np.where(r >= r_out, 0.0, w))
    raise ValueError(f"unknown aperture edge {edge!r}")


def aperture_area(profile, shape, sampling):
    """Noise-equivalent area ∫|A|² d²q in Å⁻² (sets the phase noise and the resolution)."""
    dq2 = 1.0 / (shape[0] * sampling[0] * shape[1] * sampling[1])
    return float(np.sum(np.abs(profile) ** 2) * dq2)


def objective_transfer(shape, sampling, spot_q, radius_q, edge, taper_q, wavelength, defocus_A, Cs_A):
    """Complex transfer centred on the selected spot: aperture × exp(-i chi(q - q_spot)).

    chi = π λ C10 |q|² + (π/2) Cs λ³ |q|⁴ with C10 = -defocus (abTEM convention: defocus = -C10, positive =
    underfocus), evaluated relative to the spot (equivalent to centred dark field: the spot on the optic axis)."""
    qx, qy = fft_freqs(shape, sampling)
    dx = qx - spot_q[0]
    dy = qy - spot_q[1]
    q2 = dx * dx + dy * dy
    A = aperture_profile(np.sqrt(q2), radius_q, edge, taper_q)
    chi = math.pi * wavelength * (-defocus_A) * q2 + 0.5 * math.pi * Cs_A * wavelength ** 3 * q2 * q2
    return A * np.exp(-1j * chi), A


def shift_by_phase_ramp(psi, sampling, q):
    """Multiply by exp(-2πi q·r): moves Fourier content at +q to the origin without circular rolls (A-M13)."""
    x = (np.arange(psi.shape[-2]) * sampling[0])[:, None]
    y = (np.arange(psi.shape[-1]) * sampling[1])[None, :]
    return psi * np.exp(-2j * np.pi * (q[0] * x + q[1] * y))


def refine_spot(psi, sampling, q0, radius_q):
    """Intensity-weighted centroid of |FFT|² within radius_q of q0 (audit A-C3: never argmax of one bin)."""
    F2 = np.abs(np.fft.fft2(psi, axes=(-2, -1))) ** 2
    if F2.ndim == 3:
        F2 = F2.sum(axis=0)
    qx, qy = fft_freqs(F2.shape, sampling)
    m = (qx - q0[0]) ** 2 + (qy - q0[1]) ** 2 <= radius_q ** 2
    w = F2 * m
    s = w.sum()
    if s <= 0:
        raise SystemExit(f"no intensity within {radius_q:.4g} 1/Å of the requested spot {q0}")
    return np.array([(w * qx).sum() / s, (w * qy).sum() / s]), float(s / F2.sum())


# ---------------------------------------------------------------------------------------------------------------
# Biprism and reference wave
# ---------------------------------------------------------------------------------------------------------------
def carrier_vector(spacing_A, orientation_deg):
    """q_c (cycles/Å) of fringes with spacing s; orientation = angle of q_c from +x (fringes run perpendicular)."""
    t = math.radians(orientation_deg)
    return np.array([math.cos(t), math.sin(t)]) / spacing_A


def fresnel_edge(u, width_A):
    """Straight-edge Fresnel diffraction amplitude, illuminated for u > 0: (1-i)/2 [(½ + C(ν)) + i(½ + S(ν))],
    ν = u / width_A with width_A = sqrt(λ L / 2) (scipy's π/2 Fresnel integrals). 1/2 at the geometric edge
    (intensity 1/4), oscillating fringes on the lit side. width_A = 0: hard edge."""
    u = np.asarray(u, float)
    if width_A <= 0:
        return (u > 0).astype(complex)
    from scipy.special import fresnel
    S, C = fresnel(u / width_A)
    return 0.5 * (1 - 1j) * ((0.5 + C) + 1j * (0.5 + S))


def biprism_edges(shape, sampling, q_c, overlap_width_A, fresnel_width_A):
    """(E_o, E_r): the object beam lit for u < +W/2, the reference for u > -W/2, u = (r - centre)·q̂_c."""
    if overlap_width_A is None:
        one = np.ones(shape, complex)
        return one, one
    qhat = q_c / np.linalg.norm(q_c)
    x = (np.arange(shape[0]) * sampling[0] - 0.5 * shape[0] * sampling[0])[:, None]
    y = (np.arange(shape[1]) * sampling[1] - 0.5 * shape[1] * sampling[1])[None, :]
    u = x * qhat[0] + y * qhat[1]
    return fresnel_edge(0.5 * overlap_width_A - u, fresnel_width_A), fresnel_edge(u + 0.5 * overlap_width_A,
                                                                                    fresnel_width_A)


def reference_distortion(shape, sampling, curvature_rad, ramp_rad):
    """Smooth phase on the reference wave (model R3: residual curvature and tilt from biprism/projector/detector).
    curvature_rad: phase at a field corner relative to the centre (quadratic); ramp_rad: [Δφ across x, across y]."""
    nx, ny = shape
    x = (np.arange(nx) - 0.5 * (nx - 1))[:, None] / (0.5 * nx)
    y = (np.arange(ny) - 0.5 * (ny - 1))[None, :] / (0.5 * ny)
    return curvature_rad * 0.5 * (x * x + y * y) + 0.5 * ramp_rad[0] * x + 0.5 * ramp_rad[1] * y


def coherence_factor(degree_of_coherence, drift_A, q_c):
    """Contrast factor of the interference term: |γ| × |sinc(q_c·d)| for a linear fringe drift d (Å, along q̂_c)
    during the exposure (numpy sinc(x) = sin(πx)/(πx))."""
    return float(degree_of_coherence * abs(np.sinc(np.linalg.norm(q_c) * drift_A)))


def hologram_intensity(psi_stack, sampling, q_c, amp_obj, amp_ref, mu, phi_ref, E_o, E_r):
    """Expected hologram intensity on the simulation grid, averaged over the leading (phonon) axis.

    psi_stack: (n_cfg, nx, ny) image waves (vacuum = 1). Returns float64 (nx, ny), vacuum mean = amp_obj²+amp_ref²
    inside the overlap. Intensities are averaged after squaring (spec §5.4); the reference branch is common."""
    x = (np.arange(psi_stack.shape[-2]) * sampling[0])[:, None]
    y = (np.arange(psi_stack.shape[-1]) * sampling[1])[None, :]
    R = amp_ref * np.exp(-2j * np.pi * (q_c[0] * x + q_c[1] * y) + 1j * phi_ref) * E_r
    I = np.zeros(psi_stack.shape[-2:])
    for psi in psi_stack:
        O = amp_obj * psi * E_o
        I += np.abs(O) ** 2 + np.abs(R) ** 2 + 2.0 * mu * np.real(O * np.conj(R))
    return I / psi_stack.shape[0]


# ---------------------------------------------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------------------------------------------
def bin_pixels(img, b):
    """Mean over b×b blocks (pixel integration). Trailing rows/columns that do not fill a block are dropped."""
    if b == 1:
        return np.asarray(img, float).copy()
    nx, ny = img.shape[-2] // b, img.shape[-1] // b
    v = np.asarray(img)[..., :nx * b, :ny * b]
    return v.reshape(v.shape[:-2] + (nx, b, ny, b)).mean(axis=(-3, -1))


def resample_to_pixel_centres(psi, b):
    """Band-limited decimation of a complex wave sampled at x_k = k Δ to detector pixel centres
    X_K = (K b + (b - 1)/2) Δ, so it registers with bin_pixels of an intensity on the same grid."""
    if b == 1:
        return np.asarray(psi).copy()
    lead = psi.shape[:-2]
    nx, ny = psi.shape[-2], psi.shape[-1]
    Nx, Ny = nx // b, ny // b
    if Nx * b != nx or Ny * b != ny:
        psi = psi[..., :Nx * b, :Ny * b]
        nx, ny = Nx * b, Ny * b
    F = np.fft.fft2(psi, axes=(-2, -1))
    s = 0.5 * (b - 1)
    kx = np.rint(np.fft.fftfreq(nx) * nx)[:, None]  # integer frequency indices
    ky = np.rint(np.fft.fftfreq(ny) * ny)[None, :]
    F = F * np.exp(2j * np.pi * (kx * s / nx + ky * s / ny))
    ix = np.rint(np.fft.fftfreq(Nx) * Nx).astype(int) % nx  # rint: fftfreq(N)*N gives 28.999999...
    iy = np.rint(np.fft.fftfreq(Ny) * Ny).astype(int) % ny
    Fc = F[..., ix[:, None], iy[None, :]]
    out = np.fft.ifft2(Fc, axes=(-2, -1)) / (b * b)
    return out.reshape(lead + (Nx, Ny))


def mtf_value(f, model, sigma_px=None, table=None):
    """Detector MTF at spatial frequency f (cycles/pixel). model: none | gaussian | table.
    gaussian: exp(-2 π² σ² f²) for a Gaussian point spread of σ pixels. table: [[f (cycles/px), MTF], ...],
    linearly interpolated (a measured MTF). Pixel integration (sinc) is already in bin_pixels."""
    f = np.asarray(f, float)
    if model == "none":
        return np.ones_like(f)
    if model == "gaussian":
        return np.exp(-2.0 * math.pi ** 2 * sigma_px ** 2 * f * f)
    if model == "table":
        t = np.asarray(table, float)
        if t.ndim != 2 or t.shape[1] != 2 or np.any(np.diff(t[:, 0]) <= 0):
            raise ValueError("MTF table must be [[f, mtf], ...] with increasing f (cycles/pixel)")
        return np.interp(f, t[:, 0], t[:, 1], left=t[0, 1], right=t[-1, 1])
    raise ValueError(f"unknown MTF model {model!r}")


def mtf_curve(shape, model, sigma_px=None, table=None):
    """The MTF on the detector's FFT grid (unshifted)."""
    fx = np.fft.fftfreq(shape[0])[:, None]
    fy = np.fft.fftfreq(shape[1])[None, :]
    return mtf_value(np.sqrt(fx * fx + fy * fy), model, sigma_px, table)


def apply_mtf(img, mtf):
    return np.real(np.fft.ifft2(np.fft.fft2(img) * mtf))


def record(expected_intensity, dose_e_per_A2, pixel_A, counts_per_electron, gain_map, rng):
    """Expected counts and one Poisson realisation. expected_intensity is normalised so that 1 = the dose."""
    lam = np.clip(expected_intensity, 0, None) * dose_e_per_A2 * pixel_A[0] * pixel_A[1] * gain_map
    noisy = rng.poisson(lam).astype(float) * counts_per_electron
    return lam * counts_per_electron, noisy


def predicted_phase_noise(contrast, dose_obj, dose_ref, area_q):
    """σ_φ of a reference-normalised sideband phase (rad) in vacuum: sqrt(2)/(μ sqrt(N)) per hologram with
    N = dose × (1/∫|A|²d²q) electrons per resolution area, added in quadrature for object and reference."""
    v = 2.0 * area_q / (contrast ** 2 * dose_obj)
    if dose_ref is not None:
        v += 2.0 * area_q / (contrast ** 2 * dose_ref)
    return math.sqrt(v)
