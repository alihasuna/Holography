"""Hologram formation (docs/05 section 5 items 3-6; SM12, SM13, SM21, SM22; B5, B8).

TEST_ONLY values: pixel sizes, carriers, amplitudes, seeds and the 'no_aperture' R1 declaration stand in
for PROJECT_INPUT items 5, 6 and 16. Tolerances: 1e-12 for exact identities in double precision.
"""
import numpy as np
import pytest

from reflection_holo.optics import (ArtefactOptions, Grid, Hologram, Wave, apply_poisson_noise,
                                    ensemble_hologram_intensity, fringe_contrast, hologram_intensity,
                                    make_reference, reference_r1_vacuum_plane_wave, reference_r2_self_reference,
                                    reference_r3_curved_tilted, vacuum_object_wave)

NONE = ArtefactOptions(biprism_fresnel_fringes=None, drift=None, charging_phase_rad=None)


def grid(shape=(64, 96), px=(0.5, 2.0)):
    return Grid(shape=shape, pixel_size_A=px, axes=("y", "x"), plane="image plane (TEST_ONLY)")


def r1(g, q=(0.25, 0.0625), phase=0.3, amp=0.8, realisation=None):
    return reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=q, amplitude=amp, relative_phase_rad=phase,
                                          aperture_passage="no_aperture", realisation=realisation)


def random_wave(g, seed, label="object", realisation=None):
    rng = np.random.default_rng(seed)
    a = 0.5 + rng.random(g.shape)
    p = rng.uniform(-np.pi, np.pi, g.shape)
    return Wave(a * np.exp(1j * p), g, label, realisation)


# -- intensity and reference models -----------------------------------------------------------------

def test_intensity_is_modulus_squared_of_the_sum():
    g = grid()
    u_o, u_r = random_wave(g, 1), r1(g)
    H = hologram_intensity(u_o, u_r, artefacts=NONE, content="object")
    expanded = (np.abs(u_o.data) ** 2 + np.abs(u_r.data) ** 2
                + 2 * np.abs(u_o.data) * np.abs(u_r.data) * np.cos(np.angle(u_o.data) - np.angle(u_r.data)))
    assert np.max(np.abs(H.intensity - np.abs(u_o.data + u_r.data) ** 2)) <= 1e-12
    assert np.max(np.abs(H.intensity - expanded)) <= 1e-12
    assert H.grid == g and H.content == "object" and H.metadata["n_realisations"] == 1
    assert H.metadata["reference"]["reference_model"] == "R1"
    assert H.metadata["reference"]["aperture_passage"] == "no_aperture"


def test_r1_field_on_anisotropic_grid_and_fourier_position():
    g = grid()
    q, ph, amp = (0.25, 0.0625), 0.3, 0.8
    u = r1(g, q, ph, amp)
    i0, i1 = 7, 11
    want = amp * np.exp(1j * (2 * np.pi * (q[0] * i0 * 0.5 + q[1] * i1 * 2.0) + ph))
    assert abs(u.data[i0, i1] - want) <= 1e-12
    # numpy fft sign: exp(+2 pi i q0.r) appears at +q0 (docs/physics_conventions.md)
    F = np.abs(np.fft.fft2(u.data))
    k = np.unravel_index(np.argmax(F), F.shape)
    f0 = np.fft.fftfreq(g.shape[0], 0.5)[k[0]]
    f1 = np.fft.fftfreq(g.shape[1], 2.0)[k[1]]
    assert (f0, f1) == pytest.approx(q, abs=1e-12)


def test_r2_reference_is_the_shifted_object_without_wrap():
    g = grid(px=(1.0, 1.0))
    u_o = random_wave(g, 2)
    u_r = reference_r2_self_reference(u_o, shift_A=(3.0, -5.0), carrier_cycles_per_A=(0.0, 0.25),
                                      amplitude_scale=0.7, relative_phase_rad=0.1)
    valid = u_r.metadata["valid_mask"]
    r0, r1_ = g.coordinates_A()
    carrier = np.exp(1j * (2 * np.pi * 0.25 * r1_ + 0.1))
    expect = np.zeros(g.shape, complex)
    expect[:-3, 5:] = 0.7 * u_o.data[3:, :-5]
    expect *= carrier
    assert np.max(np.abs(u_r.data - expect)) <= 1e-12
    assert valid[:-3, 5:].all() and not valid[-3:, :].any() and not valid[:, :5].any()
    with pytest.raises(ValueError):
        reference_r2_self_reference(u_o, shift_A=(0.5, 0.0), carrier_cycles_per_A=(0.0, 0.25),
                                    amplitude_scale=1.0, relative_phase_rad=0.0)


def test_r3_reference_phase():
    g = grid()
    q, t, c, rc = (0.25, 0.0625), (0.01, -0.005), (1e-3, 2e-4, -5e-5), (10.0, 90.0)
    u = reference_r3_curved_tilted(g, carrier_cycles_per_A=q, amplitude=1.0, relative_phase_rad=0.2,
                                   residual_tilt_cycles_per_A=t, residual_curvature_rad_per_A2=c,
                                   curvature_centre_A=rc, aperture_passage="no_aperture",
                                   realisation=None)
    i0, i1 = 5, 40
    r0, r1_ = i0 * 0.5, i1 * 2.0
    d0, d1 = r0 - rc[0], r1_ - rc[1]
    ph = 2 * np.pi * ((q[0] + t[0]) * r0 + (q[1] + t[1]) * r1_) + 0.2 + c[0] * d0 ** 2 + 2 * c[1] * d0 * d1 + c[2] * d1 ** 2
    assert abs(u.data[i0, i1] - np.exp(1j * ph)) <= 1e-9
    assert u.metadata["effective_carrier_cycles_per_A"] == [q[0] + t[0], q[1] + t[1]]


def test_reference_selectable_by_name():
    g = grid()
    a = make_reference("R1", grid=g, carrier_cycles_per_A=(0.25, 0.0625), amplitude=0.8, relative_phase_rad=0.3,
                       aperture_passage="no_aperture", realisation=None)
    assert np.array_equal(a.data, r1(g).data)
    with pytest.raises(ValueError):
        make_reference("R4", grid=g)


# -- ensembles (SM13) ---------------------------------------------------------------------------------

def _ensemble(common_phase: bool, K=8, seed=7):
    g = grid(shape=(32, 64), px=(1.0, 1.0))
    rng = np.random.default_rng(seed)
    psi = rng.uniform(0, 2 * np.pi, K)          # always drawn, so delta is the same in both cases
    delta = rng.normal(0.0, 0.8, K)
    if not common_phase:
        psi = np.zeros(K)
    pairs = []
    for k in range(K):
        u_o = Wave(np.full(g.shape, np.exp(1j * (0.4 + psi[k]))), g, "flat object", k)
        u_r = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.0, 0.125), amplitude=1.0,
                                             relative_phase_rad=psi[k] + delta[k], aperture_passage="no_aperture",
                                             realisation=k)
        pairs.append((u_o, u_r))
    return g, pairs, delta


def test_ensemble_averages_intensities_not_waves():
    g, pairs, delta = _ensemble(common_phase=True)
    H = ensemble_hologram_intensity(pairs, artefacts=NONE, content="object")
    mean_of_intensities = np.mean([np.abs(o.data + r.data) ** 2 for o, r in pairs], axis=0)
    intensity_of_mean = np.abs(np.mean([o.data for o, _ in pairs], axis=0)
                               + np.mean([r.data for _, r in pairs], axis=0)) ** 2
    assert np.max(np.abs(H.intensity - mean_of_intensities)) <= 1e-12
    assert np.max(np.abs(H.intensity - intensity_of_mean)) > 0.5
    assert H.metadata["n_realisations"] == 8
    # fringe contrast of the intensity average = |<exp(i delta_k)>| (partial coherence)
    F = np.fft.fft2(H.intensity)
    mu = 2 * np.abs(F[0, -8]) / np.abs(F[0, 0])            # carrier (0, 1/8): bin 64/8 = 8
    assert abs(mu - np.abs(np.mean(np.exp(1j * delta)))) <= 1e-12


def test_phase_common_to_both_branches_cancels_in_each_realisation():
    _, with_common, _ = _ensemble(common_phase=True)
    _, without, _ = _ensemble(common_phase=False)
    H1 = ensemble_hologram_intensity(with_common, artefacts=NONE, content="object")
    H0 = ensemble_hologram_intensity(without, artefacts=NONE, content="object")
    assert np.max(np.abs(H1.intensity - H0.intensity)) <= 1e-12


def test_ensemble_rejects_mispaired_or_duplicated_realisations():
    _, pairs, _ = _ensemble(common_phase=True)
    swapped = [(pairs[0][0], pairs[1][1])] + pairs[2:]
    with pytest.raises(ValueError):
        ensemble_hologram_intensity(swapped, artefacts=NONE, content="object")
    with pytest.raises(ValueError):
        ensemble_hologram_intensity([pairs[0], pairs[0]], artefacts=NONE, content="object")
    with pytest.raises(ValueError):
        ensemble_hologram_intensity([], artefacts=NONE, content="object")


# -- detector ------------------------------------------------------------------------------------------

def test_poisson_noise_seeded_and_recorded():
    g = grid(shape=(128, 128), px=(1.0, 1.0))
    H = hologram_intensity(vacuum_object_wave(g, amplitude=1.0, realisation=None), r1(g, (0.0, 0.125)),
                           artefacts=NONE, content="empty")
    a = apply_poisson_noise([H], dose_e_per_px=400.0, seed=11)[0]
    b = apply_poisson_noise([H], dose_e_per_px=400.0, seed=11)[0]
    c = apply_poisson_noise([H], dose_e_per_px=400.0, seed=12)[0]
    assert np.array_equal(a.intensity, b.intensity) and not np.array_equal(a.intensity, c.intensity)
    assert np.array_equal(a.noiseless_intensity, H.intensity)
    assert np.all(a.intensity == np.round(a.intensity)) and a.intensity.min() >= 0
    # mean counts = dose within 5 standard errors of the mean (Poisson, 16384 pixels)
    assert abs(a.intensity.mean() - 400.0) <= 5 * np.sqrt(400.0 / a.intensity.size)
    det = a.metadata["detector"]
    assert det["seed"] == 11 and det["dose_e_per_px"] == 400.0 and det["mtf"] == "NOT IMPLEMENTED"


# -- artefacts -----------------------------------------------------------------------------------------

def test_fresnel_fringes_and_drift_declared_but_not_implemented():
    g = grid()
    u_o, u_r = random_wave(g, 3), r1(g)
    with pytest.raises(NotImplementedError):
        hologram_intensity(u_o, u_r, artefacts=ArtefactOptions({"overlap_width_A": 100.0}, None, None),
                           content="object")
    with pytest.raises(NotImplementedError):
        hologram_intensity(u_o, u_r, artefacts=ArtefactOptions(None, {"amplitude_A": 1.0}, None),
                           content="object")
    with pytest.raises(TypeError):
        ArtefactOptions(None, None)                               # every artefact must be declared
    with pytest.raises(TypeError):
        hologram_intensity(u_o, u_r, content="object")            # artefacts not declared


def test_charging_phase_is_indistinguishable_from_topography():
    g = grid()
    u_o, u_r = random_wave(g, 4), r1(g)
    r0, r1_ = g.coordinates_A()
    charge = 0.3 * np.exp(-((r0 - 16) ** 2 + (r1_ - 96) ** 2) / (2 * 20.0 ** 2))
    H_c = hologram_intensity(u_o, u_r, artefacts=ArtefactOptions(None, None, charge), content="object")
    u_topo = Wave(u_o.data * np.exp(1j * charge), g, "object with the same phase as topography", None)
    H_t = hologram_intensity(u_topo, u_r, artefacts=NONE, content="object")
    assert np.max(np.abs(H_c.intensity - H_t.intensity)) <= 1e-12
    assert H_c.metadata["artefacts"]["charging"]["label"] == "PROJECT_INPUT item 22"
    assert H_t.metadata["artefacts"]["charging"].startswith("none")


# -- required inputs -----------------------------------------------------------------------------------

def test_missing_pixel_size_raises():
    with pytest.raises(TypeError):
        Grid(shape=(8, 8), axes=("y", "x"), plane="p")
    for bad in (None, (1.0,), (0.0, 1.0), (1.0, -2.0), (1.0, np.nan), (np.inf, 1.0)):
        with pytest.raises(ValueError):
            Grid(shape=(8, 8), pixel_size_A=bad, axes=("y", "x"), plane="p")
    with pytest.raises(ValueError):
        Grid(shape=(8, 8), pixel_size_A=(1.0, 1.0), axes=("y", "y"), plane="p")
    with pytest.raises(ValueError):
        Grid(shape=(8, 8), pixel_size_A=(1.0, 1.0), axes=("y", "x"), plane="")


def test_missing_carrier_raises():
    g = grid()
    with pytest.raises(TypeError):
        reference_r1_vacuum_plane_wave(g, amplitude=1.0, relative_phase_rad=0.0, aperture_passage="no_aperture",
                                       realisation=None)
    for bad in (None, (0.0, 0.0), (0.25,), (0.25, np.nan), (1.5, 0.0)):   # 1.5 > Nyquist 1.0 on axis 0
        with pytest.raises(ValueError):
            reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=bad, amplitude=1.0, relative_phase_rad=0.0,
                                           aperture_passage="no_aperture", realisation=None)
    with pytest.raises(TypeError):
        reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.25, 0.0), amplitude=1.0,
                                       aperture_passage="no_aperture", realisation=None)  # phase undeclared
    with pytest.raises(ValueError):
        reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.25, 0.0), amplitude=1.0, relative_phase_rad=0.0,
                                       aperture_passage="unspecified", realisation=None)
    with pytest.raises(ValueError):
        reference_r2_self_reference(random_wave(g, 5), shift_A=(1.0, 0.0), carrier_cycles_per_A=None,
                                    amplitude_scale=1.0, relative_phase_rad=0.0)


def test_missing_dose_or_seed_raises():
    g = grid()
    H = hologram_intensity(random_wave(g, 6), r1(g), artefacts=NONE, content="object")
    with pytest.raises(TypeError):
        apply_poisson_noise([H], seed=1)
    with pytest.raises(TypeError):
        apply_poisson_noise([H], dose_e_per_px=100.0)
    for bad in (None, 0.0, -1.0, np.nan):
        with pytest.raises(ValueError):
            apply_poisson_noise([H], dose_e_per_px=bad, seed=1)
    for bad in (None, -1, 1.5):
        with pytest.raises(ValueError):
            apply_poisson_noise([H], dose_e_per_px=100.0, seed=bad)
    with pytest.raises(TypeError):
        apply_poisson_noise(H, dose_e_per_px=100.0, seed=1)       # a list is required (draw order)


def test_grid_and_realisation_consistency_enforced():
    g = grid()
    other = Grid(g.shape, (0.5, 2.5), g.axes, g.plane)
    with pytest.raises(ValueError):
        hologram_intensity(random_wave(g, 7), r1(other), artefacts=NONE, content="object")
    with pytest.raises(ValueError):
        hologram_intensity(random_wave(g, 7, realisation=1), r1(g, realisation=2), artefacts=NONE,
                           content="object")
    with pytest.raises(ValueError):
        hologram_intensity(random_wave(g, 7), r1(g), artefacts=NONE, content="specimen")
    with pytest.raises(ValueError):
        Hologram(np.ones(g.shape, complex), g, "object", {}, None)
    with pytest.raises(ValueError):
        Wave(np.ones((3, 3)), g, "wrong shape", None)


def test_fringe_contrast():
    assert fringe_contrast(1.0, 1.0) == 1.0
    assert fringe_contrast(1.0, 2 - np.sqrt(3)) == pytest.approx(0.5, abs=1e-15)
