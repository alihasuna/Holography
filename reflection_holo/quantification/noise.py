"""Phase noise of the sideband estimate of an off-axis hologram.

Source map SM12: sigma_phi = sqrt(2) / (mu sqrt(N)) with fringe contrast mu and N detected counts in
the reconstruction aperture area (docs/03 section 6), i.e. in the real-space area of one
reconstruction resolution element (definition of N: phase_noise_sigma_rad); evidence DERIVED_HERE
(C report section 7.4; Poisson noise, coherent superposition). Example: mu = 0.5, N = 1e4 gives
0.028 rad, i.e. 0.004 A at (4,-4,4) where h_2pi = 0.919 A (docs/03 section 4).

phase_noise_sigma_rad is the package's one definition of sigma_phi (S2 consolidation);
reflection_holo.reconstruction.sideband_phase_noise computes N for a given sideband mask and calls
it.
"""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import TWO_PI


def phase_noise_sigma_rad(*, contrast_mu, counts_N):
    """sigma_phi = sqrt(2) / (mu sqrt(N)) in rad (SM12, DERIVED_HERE). Both arguments required.

    contrast_mu  fringe contrast mu of the hologram, in (0, 1].
    counts_N     N, the number of detected electrons in the REAL-SPACE area of ONE
                 reconstruction resolution element, i.e. the area over which one reconstructed
                 pixel averages the hologram: A_eff = n_pix / sum_q W(q)^2 pixels for a
                 Fourier-space sideband mask W on an n_pix grid (about 1/(pi R^2) A^2 for a top-hat
                 disc of radius R in cycles/A). This is the "reconstruction aperture area" of
                 docs/03 section 6 and SM12: C report section 7.4, eq. (7.3), sets N = M I_bar for
                 one sideband coefficient estimated over M pixels, the single-bin case of the same
                 definition (sum W^2 = 1, A_eff = M). For a mask wider than one bin, N is a
                 fraction of the hologram's total count.
    Result: the standard deviation of the sideband phase of ONE hologram (no reference division),
    for white Poisson noise (detector gain 1, no MTF) in the small-noise limit sigma_phi << 1.
    reconstruction.sideband_phase_noise computes N from counts per pixel and the mask, then calls
    this function.
    """
    mu = np.asarray(contrast_mu, dtype=float)
    N = np.asarray(counts_N, dtype=float)
    if np.any(~(mu > 0)) or np.any(mu > 1) or np.any(~(N > 0)):
        raise ValueError("contrast must lie in (0, 1] and counts must be positive")
    out = np.sqrt(2.0) / (mu * np.sqrt(N))
    return float(out) if np.ndim(out) == 0 else out


def height_sigma_from_phase_sigma_A(sigma_phi_rad: float, wrap_period_A: float) -> float:
    """sigma_h = h_2pi sigma_phi / (2 pi) (SM05, SM12; DERIVED_HERE)."""
    return float(wrap_period_A * sigma_phi_rad / TWO_PI)
