"""Sideband reconstruction of off-axis holograms: one code path for simulated and experimental holograms.

Runs in: em-holography (CPU): numpy, scikit-image (unwrapping), HoloSpy 0.3 (engine "holospy", statistics).

Fixes relative to the si110 pipeline's specular_filter.py (audit docs/agent_reports/A_code_audit.md):
  C3   the carrier is located on the REFERENCE (vacuum) hologram, in a declared half plane, refined sub-pixel;
       never argmax of the object hologram (for a phase step > 2.008 rad that bin is a harmonic, not the carrier)
  M6   aperture radius and taper in 1/Å (or as a fraction of |q_c|), reported as resolution and mrad
  M5   no detrending by default; an optional plane fit uses only the declared vacuum region and is saved
  M13  the sideband is moved to the origin by an integer Fourier shift; the sub-pixel remainder cancels in the
       reference normalisation (and is reported)
  M14  2-D unwrapping with skimage.restoration.unwrap_phase (Herráez), residues counted and reported
  M15  raw wrapped phase, unwrapped phase, aperture and any fitted ramp are all saved

Sign convention (holo_optics): the sideband at +q_c carries psi_obj · psi_ref*. HoloSpy's reconstruct() rolls
the FFT by +sb_position, i.e. it reconstructs the sideband at -sb_position (checked against HoloSpy 0.3); we
therefore pass sb_position = -index mod N so both engines select the same sideband.
"""

import math

import numpy as np

from holo_common import fft_freqs
from holo_optics import aperture_profile


def locate_carrier(holo, sampling, half_plane, exclude_radius_q, expected_q=None, tolerance_q=None):
    """Sideband position on a (reference) hologram: argmax of |FFT| over the half plane q·d > 0 outside the
    centre band, then a 3-point parabolic refinement on log|FFT| along each axis. half_plane: unit vector d."""
    F = np.abs(np.fft.fft2(holo - holo.mean()))
    qx, qy = fft_freqs(holo.shape, sampling)
    d = np.asarray(half_plane, float)
    m = (qx * d[0] + qy * d[1] > 0) & (np.hypot(qx, qy) > exclude_radius_q)
    if not m.any():
        raise SystemExit("no Fourier pixel left after the centre-band exclusion and the half-plane selection")
    idx = np.unravel_index(int(np.argmax(np.where(m, F, -1.0))), F.shape)
    L = np.log(F + F.max() * 1e-12)
    frac = []
    for ax in (0, 1):
        n = F.shape[ax]
        i = idx[ax]
        sl_m = list(idx)
        sl_p = list(idx)
        sl_m[ax] = (i - 1) % n
        sl_p[ax] = (i + 1) % n
        a, b, c = L[tuple(sl_m)], L[idx], L[tuple(sl_p)]
        den = a - 2 * b + c
        frac.append(0.5 * (a - c) / den if den < 0 else 0.0)
    q_int = np.array([qx[idx], qy[idx]])
    dq = np.array([1.0 / (holo.shape[0] * sampling[0]), 1.0 / (holo.shape[1] * sampling[1])])
    q_ref = q_int + np.array(frac) * dq
    res = {"index": [int(idx[0]), int(idx[1])], "q_bin_inv_A": q_int.tolist(), "q_refined_inv_A": q_ref.tolist(),
           "spacing_A": float(1.0 / np.hypot(*q_ref)),
           "orientation_deg": float(math.degrees(math.atan2(q_ref[1], q_ref[0]))),
           "peak_to_centre": float(F[idx] / max(np.abs(np.fft.fft2(holo))[0, 0], 1e-300))}
    if expected_q is not None:
        err = float(np.hypot(*(q_ref - np.asarray(expected_q))))
        res["expected_q_inv_A"] = list(expected_q)
        res["distance_to_expected_inv_A"] = err
        if tolerance_q is not None and err > tolerance_q:
            raise SystemExit(f"carrier found at {q_ref.round(5).tolist()} 1/Å, {err:.4g} 1/Å from the expected "
                             f"{list(expected_q)} (tolerance {tolerance_q}); check the half plane and the biprism")
    return res


def aperture_at_origin(shape, sampling, radius_q, edge, taper_q):
    qx, qy = fft_freqs(shape, sampling)
    return aperture_profile(np.hypot(qx, qy), radius_q, edge, taper_q)


def sideband_numpy(holo, index, aperture):
    """IFFT of the sideband at `index`, moved to the origin by an integer (periodic) shift, times the aperture."""
    F = np.fft.fft2(holo)
    F = np.roll(F, (-index[0], -index[1]), axis=(0, 1))
    return np.fft.ifft2(F * aperture)


def sideband_holospy(holo, sampling, index, radius_q, taper_q):
    """The same through HoloSpy 0.3's reconstruct() (tanh aperture of radius radius_q, half-width taper_q/2)."""
    from holospy.reconstruct import reconstruct
    n = holo.shape
    f_s = np.array([1.0 / (n[0] * sampling[0]), 1.0 / (n[1] * sampling[1])])
    pos = ((-index[0]) % n[0], (-index[1]) % n[1])
    # HoloSpy converts sizes in pixels to 1/length with the mean Fourier sampling; give it the exact ratio
    return reconstruct(np.asarray(holo, float), tuple(sampling), radius_q / f_s.mean(), pos, taper_q / f_s.mean())


def holospy_statistics(holo, sampling, q_carrier, energy_keV):
    """HoloSpy's own fringe statistics on the reference hologram, on a centred SQUARE crop: HoloSpy 0.3's
    statistics() divides by signal_shape, which is (x, y), while sb_position is (row, column), so on a
    non-square image it mixes the axes (192 × 128 px, 0.1 nm fringes along x: it reports 0.067 nm). Its
    'Fringe contrast' is std/mean of the hologram, i.e. μ/√2 for cosine fringes (not the visibility μ)."""
    if not np.isclose(sampling[0], sampling[1], rtol=5e-3):  # its error is at most this anisotropy
        return {"skipped": f"non-square pixels {list(sampling)} Å: HoloSpy 0.3 statistics() assumes square pixels"}
    import holospy  # noqa: F401  (registers the 'hologram' signal type)
    from holospy.signals import HologramImage
    m = min(holo.shape)
    x0, y0 = (holo.shape[0] - m) // 2, (holo.shape[1] - m) // 2
    crop = np.asarray(holo, float)[x0:x0 + m, y0:y0 + m]
    q = np.asarray(q_carrier, float)
    idx = locate_carrier(crop, sampling, q / np.linalg.norm(q), 0.5 * np.linalg.norm(q))["index"]
    s = HologramImage(crop)
    for ax, d in zip(s.axes_manager.signal_axes, (sampling[1], sampling[0])):
        ax.scale = d / 10.0  # nm
        ax.units = "nm"
    s.set_microscope_parameters(beam_energy=float(energy_keV), biprism_voltage=0.0, tilt_stage=0.0)
    # with HoloSpy's roll convention the position it expects is that of the conjugate sideband
    pos = np.array([(-idx[0]) % m, (-idx[1]) % m])
    st = {str(k): float(v) for k, v in s.statistics(sb_position=pos).items()}
    st["computed_on"] = f"centred {m} x {m} crop (HoloSpy 0.3 statistics() assumes a square image)"
    return st


def tukey_window(shape, alpha):
    """Separable Tukey (tapered cosine) window, as the si110 filter's tukey2d: 0 = none, 1 = Hann. Applied to the
    object AND reference hologram alike, it cancels in their ratio while suppressing the leakage of fringes that
    are not periodic in the field (a carrier off the Fourier grid, every experimental hologram)."""
    def w1(n):
        w = np.ones(n)
        e = int(alpha * (n - 1) / 2)
        if e > 0:
            r = 0.5 * (1 - np.cos(np.linspace(0, np.pi, e, endpoint=False)))
            w[:e] = r
            w[-e:] = r[::-1]
        return w
    return np.outer(w1(shape[0]), w1(shape[1]))


def unwrap(phase_wrapped, seed):
    from skimage.restoration import unwrap_phase
    return unwrap_phase(np.asarray(phase_wrapped, float), wrap_around=False, rng=seed)


def wrap(p):
    return (p + np.pi) % (2 * np.pi) - np.pi


def count_residues(phase_wrapped):
    """Number of phase residues: 2×2 loops whose wrapped differences do not sum to zero."""
    p = np.asarray(phase_wrapped, float)
    d1 = wrap(p[1:, :-1] - p[:-1, :-1])
    d2 = wrap(p[1:, 1:] - p[1:, :-1])
    d3 = wrap(p[:-1, 1:] - p[1:, 1:])
    d4 = wrap(p[:-1, :-1] - p[:-1, 1:])
    s = np.rint((d1 + d2 + d3 + d4) / (2 * np.pi))
    return int(np.count_nonzero(s))


def fringe_contrast_map(holo, index, aperture):
    """μ(r) = 2 |sideband| / centre band (both through the same aperture): the local fringe visibility."""
    sb = sideband_numpy(holo, index, aperture)
    cb = np.real(np.fft.ifft2(np.fft.fft2(holo) * aperture))
    return 2.0 * np.abs(sb) / np.maximum(cb, 1e-12 * np.abs(cb).max())


def fit_plane(phase, mask, sampling):
    """Least-squares plane a + b x + c y over mask; returns (plane, [a, b, c])."""
    x = (np.arange(phase.shape[0]) * sampling[0])[:, None] * np.ones(phase.shape)
    y = (np.arange(phase.shape[1]) * sampling[1])[None, :] * np.ones(phase.shape)
    A = np.stack([np.ones(mask.sum()), x[mask], y[mask]], axis=1)
    coef, *_ = np.linalg.lstsq(A, phase[mask], rcond=None)
    return coef[0] + coef[1] * x + coef[2] * y, coef.tolist()
