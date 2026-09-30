"""Off-axis hologram formation and sideband reconstruction (milestone M3, minimal subset).

Implemented: reference model R1 (tilted plane wave of uniform amplitude; perfectly coherent and
stable), intensity I = |psi_o + R|^2, optional Poisson detector noise at a stated dose (seeded),
carrier located on an EMPTY hologram (never on the object hologram: docs/03 section 6), a circular
sideband mask, reference correction by the empty hologram, and phase unwrapping along one axis.

Not implemented (declared options of docs/05 section 5 still to come): R2/R3 references, biprism
Fresnel fringes and finite overlap width, partial coherence envelopes, drift, charging, detector
MTF. The same reconstruct() must be used on experimental holograms.
"""

from __future__ import annotations

import numpy as np


def form_hologram(psi_obj, dx, dy, carrier, ref_amplitude, dose=None, rng=None):
    """I = |psi + A_r exp(2 pi i q_c . r)|^2 on the (x, y) grid of psi.

    carrier : (q_cx, q_cy) in cycles/A. dose : mean counts per pixel of the empty hologram
    (Poisson noise), or None for a noiseless hologram.
    """
    nx, ny = psi_obj.shape
    x = dx * np.arange(nx)[:, None]
    y = dy * np.arange(ny)[None, :]
    R = ref_amplitude * np.exp(2j * np.pi * (carrier[0] * x + carrier[1] * y))
    I = np.abs(psi_obj + R) ** 2
    if dose is not None:
        rng = rng or np.random.default_rng(0)
        scale = dose / (2 * ref_amplitude**2)
        I = rng.poisson(I * scale) / scale
    return I


def locate_carrier(I_empty, dx, dy, exclude=0.05):
    """Brightest Fourier component of an empty hologram outside |q| < exclude, with qy < 0 kept
    (the psi R* sideband). Returns (qx, qy) in cycles/A on the FFT grid."""
    F = np.abs(np.fft.fft2(I_empty - I_empty.mean()))
    qx = np.fft.fftfreq(I_empty.shape[0], dx)[:, None]
    qy = np.fft.fftfreq(I_empty.shape[1], dy)[None, :]
    F = np.where((qx**2 + qy**2 < exclude**2) | (qy >= 0), 0, F)
    i, j = np.unravel_index(np.argmax(F), F.shape)
    return float(qx[i, 0]), float(qy[0, j])


def sideband(I, dx, dy, q_side, radius):
    """Complex image from the sideband at q_side (circular mask of `radius`), re-centred."""
    nx, ny = I.shape
    qx = np.fft.fftfreq(nx, dx)[:, None]
    qy = np.fft.fftfreq(ny, dy)[None, :]
    mask = (qx - q_side[0]) ** 2 + (qy - q_side[1]) ** 2 < radius**2
    s = np.fft.ifft2(np.fft.fft2(I) * mask)
    x = dx * np.arange(nx)[:, None]
    y = dy * np.arange(ny)[None, :]
    return s * np.exp(-2j * np.pi * (q_side[0] * x + q_side[1] * y))


def reconstruct(I_obj, I_empty, dx, dy, radius):
    """Reference-corrected complex wave psi_o/psi_empty from two holograms.

    Returns (wave, carrier) with arg(wave) = phi_o - phi_empty and |wave| the amplitude ratio.
    """
    q = locate_carrier(I_empty, dx, dy)
    s_obj = sideband(I_obj, dx, dy, q, radius)
    s_emp = sideband(I_empty, dx, dy, q, radius)
    return s_obj / np.where(np.abs(s_emp) > 1e-12, s_emp, 1e-12), q
