"""Surface-plasmon (inelastic) losses in hologram formation (report E3 section 3; optics.inelastic;
E6 M1, M2; docs/06 items 16 and 21).

TEST_ONLY values: excitation numbers, loss visibilities, amplitudes, grids, carriers, doses, seeds.
The E6 transfer n = 1.25 (DERIVED_HERE by E6 from Tanishiro 2003 p. 167, SECTION_READ) and the
loss visibility 0.1 (Tanishiro 2003 p. 171 via E6) are used as TEST_ONLY stand-ins here.

Tolerances (fixed before running; DERIVED_HERE):
* n = 0: bit-for-bit equality (the factors are exactly 1.0 and 0.0);
* Fourier coefficients of uniform synthetic holograms: 1e-12 relative (FFT rounding of O(1) data);
* noiseless phase invariance: 1e-10 rad (the sideband is multiplied by a real positive constant;
  rounding of the FFT demodulation only);
* noisy phase: |mean - true| <= 4 sigma_mean with sigma_mean^2 = sigma_phi^2 A_eff / P (P pixels,
  noise correlated over the effective resolution area A_eff = n_pix / sum W^2), sigma_phi from
  sqrt(2)/(mu sqrt(N)) with the REDUCED mu;
* noise magnitude: |sigma_meas/sigma_pred - 1| <= 4 relative standard errors
  sqrt(sum W^4 / (2 K (sum W^2)^2)) (tests/reconstruction/test_phase_noise.py).
"""
import math

import numpy as np
import pytest

from reflection_holo.optics import (ArtefactOptions, Grid, MemberPairs, SurfacePlasmonLoss, Wave,
                                    apply_poisson_noise, ensemble_hologram_intensity,
                                    fringe_contrast, fringe_contrast_with_losses,
                                    hologram_intensity, inelastic_hologram_intensity,
                                    partially_coherent_hologram, reference_r1_vacuum_plane_wave,
                                    reference_r2_self_reference, vacuum_object_wave)
from reflection_holo.optics.inelastic import for_reference_model
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier,
                                            reconstruct_sideband, sideband_mask,
                                            sideband_phase_noise, wrap_to_pi)

NONE = ArtefactOptions(biprism_fresnel_fringes=None, drift=None, charging_phase_rad=None)
SIDE = "simulation: -q_ref of the declared reference (phi_o - phi_r sideband)"
N_E6 = 1.44 * math.sin(math.radians(0.8)) / math.sin(16.1347e-3)   # E6 section F transfer


def loss(n, v=0.1, model="R1", filt="none"):
    return for_reference_model(model, mean_excitations=n,
                               excitation_label="TEST_ONLY: stands in for the item-21 EELS request",
                               loss_visibility=v, visibility_label="TEST_ONLY: item 16",
                               energy_filter=filt, energy_filter_label="TEST_ONLY: declared")


def grid(n0=64, n1=64):
    return Grid(shape=(n0, n1), pixel_size_A=(1.0, 1.0), axes=("along_beam", "perpendicular"),
                plane="image plane (TEST_ONLY)")


def r1(g, q=(0.0, 0.125), amp=1.0, realisation=None):
    return reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=q, amplitude=amp,
                                          relative_phase_rad=0.0, aperture_passage="no_aperture",
                                          realisation=realisation)


def random_object(g, seed, realisation=None):
    rng = np.random.default_rng(seed)
    return Wave((0.5 + rng.random(g.shape)) * np.exp(1j * rng.uniform(-3, 3, g.shape)), g,
                "object (TEST_ONLY)", realisation)


# ---------------------------------------------------------------------------------------------
def test_zero_excitations_reproduce_the_existing_hologram_bit_for_bit():
    g = grid()
    obj = random_object(g, 7)
    charge = ArtefactOptions(biprism_fresnel_fringes=None, drift=None,
                             charging_phase_rad=np.linspace(0, 1, g.shape[0] * g.shape[1]).reshape(g.shape))
    refs = {"R1": r1(g, amp=0.8),
            "R2": reference_r2_self_reference(obj, shift_A=(3.0, 5.0),
                                              carrier_cycles_per_A=(0.0, 0.125),
                                              amplitude_scale=0.9, relative_phase_rad=0.2)}
    for model, ref in refs.items():
        for filt in ("none", "zero_loss"):
            for art in (NONE, charge):
                want = hologram_intensity(obj, ref, artefacts=art, content="object").intensity
                got = inelastic_hologram_intensity(obj, ref, loss=loss(0.0, 0.3, model, filt),
                                                   artefacts=art, content="object").intensity
                assert np.array_equal(got, want), (model, filt)
    objs = [random_object(g, s, realisation=s) for s in range(3)]
    pairs = [(o, r1(g, realisation=o.realisation)) for o in objs]
    want = ensemble_hologram_intensity(pairs, artefacts=NONE, content="object").intensity
    got = partially_coherent_hologram([MemberPairs(0, 1.0, tuple(pairs))], loss=loss(0.0),
                                      artefacts=NONE, content="object").intensity
    assert np.array_equal(got, want)


@pytest.mark.parametrize("n", [0.3, N_E6, 3.0])
@pytest.mark.parametrize("v", [0.0, 0.1, 0.6])
@pytest.mark.parametrize("model", ["R1", "R2"])
def test_sideband_amplitude_and_visibility_follow_the_derived_formulas(n, v, model):
    """Uniform lossless waves A_O e^(i phi) and A_R e^(i 2 pi q.r) (R2: the reference arm is a
    reflected wave of the same surface, n_R = n). From optics.inelastic (DERIVED_HERE):
        DC = A_O^2 + A_R^2 (unfiltered: the loss electrons are detected),
        sideband = A_O A_R F,  F = e^(-(n_O + n_R)/2) + V_loss sqrt((1 - e^(-n_O))(1 - e^(-n_R))),
    i.e. R1: F = e^(-n/2) for every V_loss; R2: F = e^(-n) + V_loss (1 - e^(-n)); and the visibility
    2 sideband/DC = fringe_contrast_with_losses. Zero-loss filter: DC = e^(-n_O) A_O^2 +
    e^(-n_R) A_R^2 and F = e^(-(n_O + n_R)/2)."""
    g = grid()
    AO, AR, phi = 1.0, 0.7, 0.4
    obj = Wave(np.full(g.shape, AO * np.exp(1j * phi)), g, "uniform object", None)
    ref = r1(g, amp=AR)
    nR = 0.0 if model == "R1" else n
    for filt in ("none", "zero_loss"):
        lo = loss(n, v, model, filt)
        H = inelastic_hologram_intensity(obj, ref, loss=lo, artefacts=NONE, content="object")
        F = np.fft.fft2(H.intensity) / (g.shape[0] * g.shape[1])
        side = F[0, (-8) % 64]                            # -q_c: the phi_o - phi_r sideband
        if filt == "none":
            dc_want = AO ** 2 + AR ** 2
            f_want = math.exp(-(n + nR) / 2) + v * math.sqrt(-math.expm1(-n) * -math.expm1(-nR))
        else:
            dc_want = math.exp(-n) * AO ** 2 + math.exp(-nR) * AR ** 2
            f_want = math.exp(-(n + nR) / 2)
        assert F[0, 0].real == pytest.approx(dc_want, rel=1e-12)
        assert abs(side) == pytest.approx(AO * AR * f_want, rel=1e-12)
        assert np.angle(side) == pytest.approx(phi, abs=1e-12)          # phase unchanged
        assert lo.fringe_factor() == pytest.approx(f_want, rel=1e-15)
        mu = 2 * abs(side) / F[0, 0].real
        assert mu == pytest.approx(fringe_contrast_with_losses(AO, AR, lo), rel=1e-12)
        if model == "R1" and filt == "none":
            assert f_want == pytest.approx(math.exp(-n / 2), rel=1e-15)    # V_loss inert
            assert mu == pytest.approx(fringe_contrast(AO, AR) * math.exp(-n / 2), rel=1e-12)
        if model == "R2" and filt == "none":
            assert f_want == pytest.approx(math.exp(-n) + v * -math.expm1(-n), rel=1e-15)


def test_E6_transfer_numbers_are_reproduced():
    """E6 section F (tools/review/e6_recompute_output.txt): 1.44 at 0.8 deg scaled by 1/sin(theta)
    to 16.1347 mrad is 1.246; zero-loss fraction 0.288; elastic amplitude 0.536; R2 sideband
    factor exp(-n) = 0.288. With V_loss = 0.1 the R2 factor becomes 0.359 (DERIVED_HERE)."""
    assert round(N_E6, 3) == 1.246
    lo1, lo2 = loss(N_E6, 0.1, "R1"), loss(N_E6, 0.1, "R2")
    assert round(math.exp(-N_E6), 3) == 0.288
    assert round(lo1.zero_loss_amplitude_object, 3) == 0.536
    assert round(lo1.fringe_factor(), 3) == 0.536
    assert round(lo2.zero_loss_amplitude_object * lo2.zero_loss_amplitude_reference, 3) == 0.288
    assert round(lo2.fringe_factor(), 3) == 0.359


def _step_object(g, delta):
    ph = np.where(np.arange(g.shape[0])[:, None] < g.shape[0] // 2, 0.0, delta)
    return Wave(np.exp(1j * np.broadcast_to(ph, g.shape)), g, "phase step (TEST_ONLY)", None)


@pytest.mark.parametrize("model", ["R1", "R2"])
def test_reconstructed_phase_is_unchanged_by_a_uniform_loss_without_noise(model):
    """Noiseless holograms of a 1 rad phase step, n = 0 and n = 1.25 (V_loss = 0.1). DERIVED_HERE:
    the demodulated sideband is w_n = F S + E, S the lossless fringe term and E the leakage of the
    zero-order (DC) term through the sideband mask; the unfiltered DC |u_o|^2 + |u_r|^2 does not
    depend on n, so E does not either. Hence |phi_n - phi_0| <= asin(|E|/(F|S|)) + asin(|E|/|S|)
    pixel by pixel (both angles measured from arg S). R1 with a uniform-amplitude object: the DC
    is constant, E = 0 inside the mask and the phase is unchanged to rounding (1e-10). R2: the
    reference is the shifted object, zero outside the field (no wrap), so the DC steps at the
    edge of the reference field and E != 0 there (decaying slowly with the distance from it); the
    bound is evaluated pixel by pixel with E and S computed with the same mask.""" 
    g = grid(128, 128) if model == "R1" else grid(128, 512)
    obj = _step_object(g, 1.0)
    q = (0.0, 0.125)
    if model == "R1":
        ref = r1(g, q=q)
    else:
        ref = reference_r2_self_reference(obj, shift_A=(0.0, 20.0), carrier_cycles_per_A=q,
                                          amplitude_scale=1.0, relative_phase_rad=0.0)
    emp_obj = vacuum_object_wave(g, amplitude=1.0, realisation=None)
    emp_ref = r1(g, q=q)
    carrier = locate_carrier(hologram_intensity(emp_obj, emp_ref, artefacts=NONE, content="empty"),
                             CarrierSearch((-q[0], -q[1]), 0.5 * q[1], 0.05, "none", SIDE))
    mask = MaskSpec(carrier.carrier_magnitude_cycles_per_A / 3.0, "disc", "hann")
    out, H = {}, {}
    for n in (0.0, N_E6):
        lo = loss(n, 0.1, model)
        H[n] = inelastic_hologram_intensity(obj, ref, loss=lo, artefacts=NONE, content="object")
        out[n] = reconstruct_sideband(H[n], carrier=carrier, mask=mask, empty_hologram=None,
                                      reference_correction="none", object_min_visibility=0.05,
                                      unwrapping="none")
    a, b = out[0.0], out[N_E6]
    ok = a.valid_mask & b.valid_mask
    if "valid_mask" in ref.metadata:
        ok &= ref.metadata["valid_mask"]
    dphi = np.abs(wrap_to_pi(b.wrapped_phase - a.wrapped_phase))
    W = sideband_mask(g, carrier.sideband_centre_cycles_per_A, mask)
    dc = np.abs(obj.data) ** 2 + np.abs(ref.data) ** 2
    E = np.abs(np.fft.ifft2(np.fft.fft2(dc) * W))
    S = np.abs(np.fft.ifft2(np.fft.fft2(H[0.0].intensity - dc) * W))
    F = loss(N_E6, 0.1, model).fringe_factor()
    good = ok & (E < 0.5 * F * S)
    bound = (np.arcsin(np.clip(E / (F * np.maximum(S, 1e-300)), 0, 1))
             + np.arcsin(np.clip(E / np.maximum(S, 1e-300), 0, 1)))
    assert good.sum() > 0.5 * ok.sum()
    assert np.all(dphi[good] <= bound[good] + 1e-10)
    if model == "R1":
        assert np.max(E[ok]) <= 1e-12 * np.max(S) and np.max(dphi[ok]) <= 1e-10
    else:
        # the leakage is a processing effect present at n = 0 too; the loss only rescales the
        # sideband against it (by 1/F): 2.4e-5 rad at 150 px from the reference-field edge here
        assert np.max(E[ok]) > 1e-6


def test_phase_unchanged_within_noise_and_noise_follows_the_reduced_visibility():
    """R1, flat object (phase 0.3 rad) or a 1 rad step, reference amplitude = object amplitude
    (mu_0 = 1), n = E6's 1.25: mu = e^(-n/2) = 0.536. K Poisson realisations at 100 e/px. The
    measured phase noise matches sqrt(2)/(mu sqrt(N)) with the REDUCED mu and is 1/0.536 = 1.87
    times the lossless prediction (so a noise model with mu_0 would be wrong by 87 %); the mean
    phase and the step are unchanged within their noise."""
    n_pix, K, counts, seed = 512, 12, 100.0, 20260924
    g = grid(n_pix, 256)
    q = (0.0, 0.125)
    lo = loss(N_E6, 0.1, "R1")
    mu = fringe_contrast_with_losses(1.0, 1.0, lo)
    assert mu == pytest.approx(math.exp(-N_E6 / 2), rel=1e-15)
    flat = Wave(np.full(g.shape, np.exp(0.3j)), g, "flat object", None)
    step = _step_object(g, 1.0)
    ref = r1(g, q=q)
    emp = inelastic_hologram_intensity(vacuum_object_wave(g, amplitude=1.0, realisation=None),
                                       ref, loss=lo, artefacts=NONE, content="empty")
    Hf = inelastic_hologram_intensity(flat, ref, loss=lo, artefacts=NONE, content="object")
    Hs = inelastic_hologram_intensity(step, ref, loss=lo, artefacts=NONE, content="object")
    noisy = apply_poisson_noise([emp] + [Hf] * K + [Hs] * K, dose_e_per_px=counts, seed=seed)
    carrier = locate_carrier(noisy[0], CarrierSearch((-q[0], -q[1]), 0.5 * q[1], 0.05, "none",
                                                     SIDE))
    mask = MaskSpec(carrier.carrier_magnitude_cycles_per_A / 3.0, "disc", "hann")

    def rec(h):
        return reconstruct_sideband(h, carrier=carrier, mask=mask, empty_hologram=None,
                                    reference_correction="none", object_min_visibility=0.05,
                                    unwrapping="none")
    flats = [rec(h) for h in noisy[1:K + 1]]
    steps = [rec(h) for h in noisy[K + 1:]]
    W = flats[0].mask
    pred = sideband_phase_noise(mu, counts, W)["sigma_phi_rad"]
    pred0 = sideband_phase_noise(1.0, counts, W)["sigma_phi_rad"]
    dev = np.concatenate([wrap_to_pi(r.wrapped_phase - 0.3).ravel() for r in flats])
    sigma = float(np.sqrt(np.mean(dev ** 2)))
    rel_se = float(np.sqrt(np.sum(W ** 4) / (2 * K * np.sum(W ** 2) ** 2)))
    print(f"mu={mu:.4f} sigma_pred(mu)={pred:.5f} sigma_pred(mu_0=1)={pred0:.5f} "
          f"sigma_meas={sigma:.5f} ratio={sigma / pred:.4f} ratio_to_mu0={sigma / pred0:.4f} "
          f"rel_se={rel_se:.4f} K={K} seed={seed}")
    assert pred <= 0.07                                              # small-noise regime
    assert abs(sigma / pred - 1.0) <= 4 * rel_se
    assert abs(sigma / pred0 - 1.0) > 20 * rel_se                   # mu_0 would be wrong
    a_eff = float(W.size / np.sum(W ** 2))
    s_mean = pred * math.sqrt(a_eff / dev.size)
    assert abs(float(np.mean(dev))) <= 4 * s_mean                    # flat phase unchanged
    # the 1 rad step: interior of each half, 3 resolution lengths (1/R_mask) from the edges
    r_px = int(math.ceil(3 * 3 / carrier.carrier_magnitude_cycles_per_A))
    lo_rows = slice(r_px, n_pix // 2 - r_px)
    hi_rows = slice(n_pix // 2 + r_px, n_pix - r_px)
    d = [float(np.mean(wrap_to_pi(r.wrapped_phase[hi_rows] - 1.0))
               - np.mean(wrap_to_pi(r.wrapped_phase[lo_rows]))) for r in steps]
    p_half = (lo_rows.stop - lo_rows.start) * g.shape[1] * K
    assert lo_rows.stop - lo_rows.start >= 100
    s_step = math.sqrt(2.0) * pred * math.sqrt(a_eff / p_half)
    print(f"mean flat phase - 0.3 = {float(np.mean(dev)):+.2e} (4 sigma_mean = {4 * s_mean:.2e}); "
          f"step - 1 rad = {float(np.mean(d)):+.2e} (4 sigma = {4 * s_step:.2e})")
    assert abs(float(np.mean(d))) <= 4 * s_step


def test_loss_model_inputs_are_required_and_checked():
    ok = dict(mean_excitations_object=1.25, object_label="TEST_ONLY: n",
              mean_excitations_reference=0.0, reference_label="DERIVED_HERE: R1",
              loss_visibility=0.1, visibility_label="TEST_ONLY: V", energy_filter="none",
              energy_filter_label="TEST_ONLY: none")
    SurfacePlasmonLoss(**ok)
    for bad in (dict(mean_excitations_object=None), dict(mean_excitations_object=-0.1),
                dict(mean_excitations_object=float("nan")), dict(loss_visibility=1.5),
                dict(loss_visibility=None), dict(energy_filter="omega"),
                dict(object_label="1.25 from somewhere"), dict(visibility_label=""),
                dict(mean_excitations_object=True)):
        with pytest.raises((ValueError, TypeError)):
            SurfacePlasmonLoss(**dict(ok, **bad))
    with pytest.raises(TypeError):
        SurfacePlasmonLoss(**{k: v for k, v in ok.items() if k != "loss_visibility"})
    assert loss(2.0, 0.1, "R1").mean_excitations_reference == 0.0
    assert loss(2.0, 0.1, "R2").mean_excitations_reference == 2.0
    assert loss(2.0, 0.1, "R3").mean_excitations_reference == 0.0
    with pytest.raises(ValueError):
        loss(2.0, 0.1, "R4")
    rec = loss(N_E6, 0.1, "R2").as_record()
    assert rec["phase"].startswith("unchanged") and rec["fringe_factor"] == pytest.approx(
        math.exp(-N_E6) + 0.1 * -math.expm1(-N_E6))
