"""Anti-aliasing angle ceilings of a real-space grid (multislice sampling assertions).

Source map SM15. Numbers DERIVED_HERE; rules:
  * "two_thirds": band limit at 2/3 of the Nyquist frequency, q_max = (2/3) / (2 dx), angle
    lambda q_max. Its attribution to B06 (Kirkland) is UNVERIFIED: P04 does not state it and B06 is
    not read. 64.31 mrad at 0.13 A and 16.72 mrad at 0.50 A, 200 keV (checks T21, T22).
  * "half_nyquist": Prismatic's anti-aliasing aperture at half the maximum scattering angle,
    lambda / (4 dx) (SECTION_READ of P04 p. 3 and of the Prismatic source, params.h:241-242);
    48 mrad at 0.13 A.
The OUTGOING beam angle must lie inside the band; the pixel size is read from the data or derived
from the grid, never taken from an advisory parameter.
"""
from __future__ import annotations

import numpy as np

from reflection_holo.geometry.errors import SamplingError

RULES = ("two_thirds", "half_nyquist")


def antialias_max_angle_rad(pixel_A: float, wavelength_A_: float, *, rule: str) -> float:
    """Largest representable scattering angle lambda q_max for a pixel size dx (A).

    rule is REQUIRED: "two_thirds" (q_max = 1/(3 dx); source UNVERIFIED, see module docstring) or
    "half_nyquist" (q_max = 1/(4 dx); Prismatic, SECTION_READ). Source map SM15, numbers
    DERIVED_HERE. Small-angle relation angle = lambda q (valid at these mrad angles).
    """
    if not pixel_A > 0:
        raise ValueError(f"pixel size must be positive, got {pixel_A!r}")
    if rule == "two_thirds":
        q_max = (2.0 / 3.0) / (2.0 * pixel_A)
    elif rule == "half_nyquist":
        q_max = 1.0 / (4.0 * pixel_A)
    else:
        raise ValueError(f"unknown anti-aliasing rule {rule!r}; choose one of {RULES}")
    return float(wavelength_A_ * q_max)


def require_angle_in_band(angle_rad: float, pixel_A: float, wavelength_A_: float, *,
                          rule: str) -> None:
    """Refuse (SamplingError) an outgoing-beam angle outside the anti-aliasing band (SM15;
    ceiling DERIVED_HERE, 2/3 rule source UNVERIFIED)."""
    ceiling = antialias_max_angle_rad(pixel_A, wavelength_A_, rule=rule)
    if abs(angle_rad) > ceiling:
        raise SamplingError(
            f"angle {abs(angle_rad) * 1e3:.3f} mrad exceeds the {rule} anti-aliasing ceiling "
            f"{ceiling * 1e3:.3f} mrad at pixel {pixel_A} A (source map SM15)")
