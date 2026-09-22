"""Free-space propagators of the multislice (docs/05 section 4.3 item 9; SM14 for the method).

Convention exp(+i k.r), numpy FFT sign; the wave psi is the envelope relative to the carrier
exp(+i k z) along the beam axis z. A plane-wave component exp(2 pi i (fx x + fy y)) advances over dz

  "exact":   exp(+i dz (k_z - k)),  k_z = sqrt(k^2 - q^2),  q = 2 pi |f|;
             computed as k_z - k = -q^2 / (k + k_z) (no cancellation). Components with q >= k are
             EVANESCENT: they are REMOVED (set to zero) rather than attenuated, because a forward
             multislice cannot represent them; inside the 2/3 band this can only occur for
             dx < lambda/3 = 0.0084 A at 200 keV, so for every practical grid the removal is inert,
             and the count of removed components is recorded. DERIVED_HERE.
  "fresnel": exp(-i pi lambda dz f^2) (paraxial). Its phase error relative to "exact" is
             k dz sin^4(alpha)/8 per slice (docs/03 section 5: 0.026 rad at 45 mrad over 198 A).

The tilt of the illumination is carried by the entrance-plane Fourier component (illumination.py),
never by a propagator shear. Both kernels are multiplied by the band-limit aperture.
"""
from __future__ import annotations

import numpy as np

PROPAGATORS = ("exact", "fresnel")


def propagator_phase(grid, *, dz_A: float, wavelength_A: float, kind: str):
    """(phase (nx, ny) float64 in rad, evanescent mask) of the propagation over dz_A."""
    if kind not in PROPAGATORS:
        raise ValueError(f"propagator must be one of {PROPAGATORS}, got {kind!r}")
    fx = grid.fx()[:, None]
    fy = grid.fy()[None, :]
    f2 = fx**2 + fy**2
    if kind == "fresnel":
        return -np.pi * wavelength_A * dz_A * f2, np.zeros(f2.shape, bool)
    k = 2.0 * np.pi / wavelength_A
    q2 = (2.0 * np.pi) ** 2 * f2
    evanescent = q2 >= k**2
    kz = np.sqrt(np.where(evanescent, 0.0, k**2 - q2))
    phase = dz_A * (-q2 / (k + kz))
    return np.where(evanescent, 0.0, phase), evanescent


def propagator_kernel(grid, *, dz_A: float, wavelength_A: float, kind: str, band_mask):
    """Complex (nx, ny) kernel = exp(i phase) * band mask, evanescent components removed."""
    phase, ev = propagator_phase(grid, dz_A=dz_A, wavelength_A=wavelength_A, kind=kind)
    ker = np.exp(1j * phase) * band_mask
    ker[ev] = 0.0
    return ker, int(np.count_nonzero(ev & band_mask))


def propagate(psi, grid, *, distance_A: float, wavelength_A: float, kind: str, band_mask,
              backend):
    """Propagate psi (backend array) through vacuum by distance_A (negative = inverse)."""
    ker, _ = propagator_kernel(grid, dz_A=distance_A, wavelength_A=wavelength_A, kind=kind,
                               band_mask=band_mask)
    ker = backend.asarray(ker, dtype=backend.complex_dtype)
    return backend.ifft2(backend.fft2(psi) * ker)
