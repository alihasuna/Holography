"""Phase noise of the sideband estimate of an off-axis hologram.

Source map SM12: sigma_phi = sqrt(2) / (mu sqrt(N)) with fringe contrast mu and N detected counts in
the reconstruction aperture area; evidence DERIVED_HERE (C report section 7.4; Poisson noise,
coherent superposition). Example: mu = 0.5, N = 1e4 gives 0.028 rad, i.e. 0.004 A at (4,-4,4)
where h_2pi = 0.919 A (docs/03 section 4).
"""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import TWO_PI


def phase_noise_sigma_rad(*, contrast_mu, counts_N):
    """sigma_phi = sqrt(2) / (mu sqrt(N)) in rad (SM12, DERIVED_HERE). Both arguments required."""
    mu = np.asarray(contrast_mu, dtype=float)
    N = np.asarray(counts_N, dtype=float)
    if np.any(~(mu > 0)) or np.any(mu > 1) or np.any(~(N > 0)):
        raise ValueError("contrast must lie in (0, 1] and counts must be positive")
    out = np.sqrt(2.0) / (mu * np.sqrt(N))
    return float(out) if np.ndim(out) == 0 else out


def height_sigma_from_phase_sigma_A(sigma_phi_rad: float, wrap_period_A: float) -> float:
    """sigma_h = h_2pi sigma_phi / (2 pi) (SM05, SM12; DERIVED_HERE)."""
    return float(wrap_period_A * sigma_phi_rad / TWO_PI)
