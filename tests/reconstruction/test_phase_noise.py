"""Phase noise of the sideband estimate: sigma_phi = sqrt(2)/(mu sqrt(N)) (SM12; docs/03 section 6).

N is the number of counts in the effective resolution area n_pix / sum(W^2) (reconstruction.sideband.
sideband_phase_noise, DERIVED_HERE). Flat object (phase 0.3 rad), R1 reference of amplitude a giving the
fringe contrast mu = 2a/(1 + a^2); no reference division (a division by an equally noisy empty hologram
multiplies sigma by sqrt(2)); carrier located on a noisy EMPTY hologram.

Statistics: K = 16 independent Poisson realisations per case, one generator, seed 20260922 (draw order:
empty hologram, then the K object holograms). Estimator: RMS of wrap(phase - 0.3) over all pixels of all
realisations. Its relative standard error is sqrt(sum W^4 / (2 K (sum W^2)^2)) (correlated Gaussian
samples; DERIVED_HERE); tolerance |sigma_meas/sigma_pred - 1| <= 4 standard errors. Cases keep
sigma_pred <= 0.07 rad so that the small-noise linearisation holds.
"""
import numpy as np
import pytest

from holo_cases import NO_ARTEFACTS, SIM_SIDEBAND, make_grid, r1_reference
from reflection_holo.optics import Wave, apply_poisson_noise, fringe_contrast, hologram_intensity, vacuum_object_wave
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier, reconstruct_sideband,
                                            sideband_phase_noise, wrap_to_pi)

N_PIX = 256
K = 16
SEED = 20260922
PHI_O = 0.3
Q = (0.0, 1.0 / 8.0)
CASES = [(1.0, 100.0), (0.5, 100.0), (0.25, 100.0), (0.5, 10.0)]   # (target contrast, counts/px)


def _amplitude_for(mu):
    return 1.0 if mu == 1.0 else (1.0 - np.sqrt(1.0 - mu ** 2)) / mu


@pytest.mark.parametrize("apodisation", ["none", "hann"])
@pytest.mark.parametrize("mu_target,counts", CASES)
def test_phase_noise_matches_sqrt2_over_mu_sqrtN(mu_target, counts, apodisation):
    grid = make_grid(N_PIX)
    a = _amplitude_for(mu_target)
    mu = fringe_contrast(1.0, a)
    assert abs(mu - mu_target) < 1e-12
    u_o = Wave(np.full(grid.shape, np.exp(1j * PHI_O)), grid, "flat object", None)
    u_r = r1_reference(grid, Q, amplitude=a)
    H = hologram_intensity(u_o, u_r, artefacts=NO_ARTEFACTS, content="object")
    H_emp = hologram_intensity(vacuum_object_wave(grid, amplitude=1.0, realisation=None), u_r,
                               artefacts=NO_ARTEFACTS, content="empty")
    noisy = apply_poisson_noise([H_emp] + [H] * K, dose_e_per_px=counts, seed=SEED)
    assert [h.metadata["detector"]["draw_index"] for h in noisy] == list(range(K + 1))
    assert all(h.metadata["detector"]["seed"] == SEED for h in noisy)
    carrier = locate_carrier(noisy[0], CarrierSearch((-Q[0], -Q[1]), 0.5 * Q[1], 0.05, "none",
                                                     SIM_SIDEBAND))
    mask = MaskSpec(carrier.carrier_magnitude_cycles_per_A / 3.0, "disc", apodisation)
    devs = []
    for h in noisy[1:]:
        res = reconstruct_sideband(h, carrier=carrier, mask=mask, empty_hologram=None,
                                   reference_correction="none", unwrapping="none")
        devs.append(wrap_to_pi(res.wrapped_phase - PHI_O).ravel())
    sigma_meas = float(np.sqrt(np.mean(np.concatenate(devs) ** 2)))
    pred = sideband_phase_noise(mu, counts, res.mask)
    W = res.mask
    rel_se = float(np.sqrt(np.sum(W ** 4) / (2 * K * np.sum(W ** 2) ** 2)))
    assert pred["sigma_phi_rad"] <= 0.07
    ratio = sigma_meas / pred["sigma_phi_rad"]
    print(f"apod={apodisation} mu={mu:.3f} counts/px={counts:g} N={pred['N_counts']:.0f} "
          f"sigma_pred={pred['sigma_phi_rad']:.5f} sigma_meas={sigma_meas:.5f} ratio={ratio:.4f} "
          f"rel_se={rel_se:.4f} K={K} seed={SEED}")
    assert abs(ratio - 1.0) <= 4.0 * rel_se
