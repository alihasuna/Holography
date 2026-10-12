"""Physics of hologram formation and reconstruction on small arrays (CPU, no GPU, < 10 s).

numpy for everything; scipy for the biprism Fresnel edges; scikit-image for unwrapping (tests skip without it).
"""

import math

import numpy as np

import _helpers
import holo_metrics as hm
import holo_optics as ho
import holo_sideband as hs
import step_height_reflection_formula as shf

N = (256, 256)
PIX = (0.25, 0.25)          # Å: field 64 Å
A_HALF = math.sqrt(0.5)


def form(psi, spacing=1.0, orient=0.0, mu=0.4, phi_d=None, E=None):
    """Noise-free object and vacuum-reference holograms (equal beam intensities), detector = grid."""
    q_c = ho.carrier_vector(spacing, orient)
    one = np.ones(psi.shape, complex)
    phi_d = np.zeros(psi.shape) if phi_d is None else phi_d
    E_o, E_r = (one, one) if E is None else E
    I_o = ho.hologram_intensity(psi[None], PIX, q_c, A_HALF, A_HALF, mu, phi_d, E_o, E_r)
    I_r = ho.hologram_intensity(one[None], PIX, q_c, A_HALF, A_HALF, mu, phi_d, E_o, E_r)
    return I_o, I_r, q_c


def recon(I_o, I_r, q_c, radius=0.3, normalize=True, conjugate=False, tukey=0.0):
    car = hs.locate_carrier(I_r, PIX, q_c / np.linalg.norm(q_c) * (-1 if conjugate else 1), 0.5)
    W = hs.tukey_window(I_o.shape, tukey)
    I_o, I_r = I_o * W, I_r * W
    A = hs.aperture_at_origin(I_o.shape, PIX, radius, "hann", 0.04)
    so, sr = hs.sideband_numpy(I_o, car["index"], A), hs.sideband_numpy(I_r, car["index"], A)
    return (so / sr if normalize else so / np.abs(sr).mean()), A, car


def bandlimit(psi, A):
    return np.fft.ifft2(np.fft.fft2(psi) * A)


def objective(psi, radius=0.2):
    return bandlimit(psi, hs.aperture_at_origin(psi.shape, PIX, radius, "hann", 0.04))


def stripe(height, x0=16.0, x1=48.0, width=0.8):
    x = (np.arange(N[0]) * PIX[0])[:, None] * np.ones(N)
    return height * 0.5 * (np.tanh((x - x0) / width) - np.tanh((x - x1) / width))


def test_fringe_spacing_and_orientation_match_the_biprism_setting():
    for spacing, orient in ((1.0, 25.0), (1.3, -60.0)):
        _, I_r, q_c = form(np.ones(N, complex), spacing, orient)
        car = hs.locate_carrier(I_r, PIX, q_c / np.linalg.norm(q_c), 0.5)
        assert abs(car["spacing_A"] / spacing - 1) < 0.005, (spacing, car["spacing_A"])
        assert abs(car["orientation_deg"] - orient) < 0.5, (orient, car["orientation_deg"])


def test_vacuum_fringe_contrast_equals_the_coherence_budget():
    for mu, drift in ((0.4, 0.0), (0.7, 0.2)):
        q_c = ho.carrier_vector(1.0, 0.0)
        m = ho.coherence_factor(mu, drift, q_c)
        _, I_r, _ = form(np.ones(N, complex), 1.0, 0.0, mu=m)
        car = hs.locate_carrier(I_r, PIX, (1, 0), 0.5)
        cmap = hs.fringe_contrast_map(I_r, car["index"], hs.aperture_at_origin(N, PIX, 0.25, "hard", 0.0))
        expected = mu * abs(np.sinc(1.0 * drift))
        assert abs(np.median(cmap) - expected) < 0.005 * expected, (np.median(cmap), expected)


def test_known_phase_step_is_recovered_including_above_the_carrier_trap_threshold():
    _helpers.need("skimage")
    for h in (1.0, 2.5):  # 2.5 rad > 2.008 rad: argmax of the object FFT would pick a harmonic (audit A-C3)
        psi = objective(np.exp(1j * stripe(h)))
        I_o, I_r, q_c = form(psi, 1.0, 30.0)  # carrier off the Fourier grid: fringes not periodic in the field
        w, A, _ = recon(I_o, I_r, q_c, tukey=0.2)
        truth = bandlimit(psi, A)
        d = hs.wrap(np.angle(w) - np.angle(truth))[16:-16, 16:-16]
        assert np.abs(d).max() < 0.005, (h, np.abs(d).max())
        phase = hs.unwrap(np.angle(w), 0)
        x = np.arange(N[0]) * PIX[0]
        inside = (x > 26) & (x < 38)
        outside = (x < 6) | (x > 58)
        step = phase[inside].mean() - phase[outside].mean()
        assert abs(step - h) < 0.02, (h, step)


def test_carrier_trap_object_hologram_peak_is_not_the_carrier():
    # T24 of docs/03_physics_summary.md: a 50/50 phase step of 2.36 rad; carrier on a Fourier bin (k = 64)
    x = (np.arange(N[0]) * PIX[0])[:, None] * np.ones(N)
    psi = np.exp(1j * 2.36 * (x < 32.0))
    I_o, I_r, q_c = form(psi, 1.0, 0.0)
    true_idx = [64, 0]
    F = np.abs(np.fft.fft2(I_o - I_o.mean()))
    qx, qy = _helpers.need("holo_common").fft_freqs(N, PIX)
    F[(qx <= 0) | (np.hypot(qx, qy) < 0.5)] = 0
    wrong = list(np.unravel_index(int(np.argmax(F)), F.shape))
    assert wrong != true_idx, "the object hologram's brightest bin should be a harmonic here"
    car = hs.locate_carrier(I_r, PIX, (1, 0), 0.5)
    assert car["index"] == true_idx


def test_phase_wrapping_beyond_2pi_is_unwrapped():
    _helpers.need("skimage")
    x = (np.arange(N[0]) * PIX[0])[:, None] * np.ones(N)
    y = (np.arange(N[1]) * PIX[1])[None, :] * np.ones(N)
    phi = 6 * math.pi * x / 64.0 + 0.5 * np.sin(2 * math.pi * y / 64.0)  # periodic, 3 full turns
    psi = np.exp(1j * phi)
    I_o, I_r, q_c = form(psi, 1.0, 45.0)
    w, A, _ = recon(I_o, I_r, q_c, tukey=0.2)
    assert hs.count_residues(np.angle(w)[16:-16, 16:-16]) == 0  # inside the apodisation taper
    u = hs.unwrap(np.angle(w), 0)
    d = (u - u.mean()) - (phi - phi.mean())
    d = d[16:-16, 16:-16] - d[16:-16, 16:-16].mean()
    assert np.abs(d).max() < 0.005
    ui, pi_ = u[16:-16, 16:-16], phi[16:-16, 16:-16]
    assert abs((ui.max() - ui.min()) - (pi_.max() - pi_.min())) < 0.01  # > 4π of phase recovered


def test_phase_noise_matches_sqrt2_over_mu_sqrtN():
    rng_o, rng_r = np.random.default_rng([1, 1]), np.random.default_rng([1, 2])
    _, I_r, q_c = form(np.ones(N, complex), 1.0, 20.0, mu=0.4)
    dose = 2000.0
    gain = np.ones(N)
    _, n_o = ho.record(I_r, dose, PIX, 1.0, gain, rng_o)
    _, n_r = ho.record(I_r, dose, PIX, 1.0, gain, rng_r)
    w, A, car = recon(n_o, n_r, q_c, radius=0.25)
    measured = np.angle(w * np.exp(-1j * np.angle(w.mean()))).std()
    cmap = hs.fringe_contrast_map(n_r, car["index"], hs.aperture_at_origin(N, PIX, 0.25, "hard", 0.0))
    predicted = ho.predicted_phase_noise(float(np.median(cmap)), dose, dose, ho.aperture_area(A, N, PIX))
    assert abs(measured / predicted - 1) < 0.15, (measured, predicted)


def test_reference_normalisation_removes_the_reference_distortion_and_its_absence_is_detected():
    psi = objective(np.exp(1j * stripe(0.8)))
    phi_d = ho.reference_distortion(N, PIX, 1.5, [0.8, -0.5])
    I_o, I_r, q_c = form(psi, 1.0, 30.0, phi_d=phi_d)
    w, A, _ = recon(I_o, I_r, q_c, normalize=True)
    truth = np.angle(bandlimit(psi, A))
    good = hs.wrap(np.angle(w) - truth)
    assert (good - good.mean()).std() < 0.005
    w2, _, _ = recon(I_o, I_r, q_c, normalize=False)
    bad = hs.wrap(np.angle(w2) - truth)
    m = np.ones(N, bool)
    m[:16] = m[-16:] = False
    m[:, :16] = m[:, -16:] = False
    rb = bad - hs.fit_plane(bad, m, PIX)[0]
    dd = -phi_d - hs.fit_plane(-phi_d, m, PIX)[0]
    assert hm.ncc(rb, dd, m) > 0.95  # the residual IS the reference distortion (plus a plane)


def test_wrong_sideband_inverts_the_phase():
    psi = objective(np.exp(1j * stripe(1.0)))
    I_o, I_r, q_c = form(psi, 1.0, 30.0)
    w, A, _ = recon(I_o, I_r, q_c, conjugate=True)
    truth = np.angle(bandlimit(psi, A))
    m = np.ones(N, bool)
    s, _ = hm.slope_fit(np.angle(w), truth, m)
    assert abs(s + 1) < 0.01 and hm.ncc(np.angle(w), truth, m) < -0.99


def test_biprism_overlap_and_fresnel_edges():
    _helpers.need("scipy")
    assert abs(ho.fresnel_edge(np.array([0.0]), 0.5)[0] - 0.5) < 1e-12
    assert abs(abs(ho.fresnel_edge(np.array([50.0]), 0.5)[0]) - 1) < 0.01
    assert abs(ho.fresnel_edge(np.array([-50.0]), 0.5)[0]) < 0.01
    q_c = ho.carrier_vector(1.0, 0.0)
    E = ho.biprism_edges(N, PIX, q_c, 30.0, 0.5)
    _, I_r, _ = form(np.ones(N, complex), 1.0, 0.0, E=E)
    car = hs.locate_carrier(I_r, PIX, (1, 0), 0.5)
    cmap = hs.fringe_contrast_map(I_r, car["index"], hs.aperture_at_origin(N, PIX, 0.25, "hard", 0.0))
    u = np.arange(N[0]) * PIX[0] - 32.0
    assert abs(np.median(cmap[np.abs(u) < 8]) - 0.4) < 0.03       # inside the overlap: full contrast
    assert np.median(cmap[np.abs(u) > 22]) < 0.03                  # outside: one beam, no fringes


def test_noise_is_deterministic_for_a_seed():
    I = np.full(N, 1.0)
    g = np.ones(N)
    a = ho.record(I, 100.0, PIX, 1.0, g, np.random.default_rng([7, 1]))[1]
    b = ho.record(I, 100.0, PIX, 1.0, g, np.random.default_rng([7, 1]))[1]
    c = ho.record(I, 100.0, PIX, 1.0, g, np.random.default_rng([8, 1]))[1]
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_pixel_centre_resampling_registers_with_binning():
    n, b, d = 64, 2, 0.1
    x = (np.arange(n) * d)[:, None] * np.ones((n, n))
    L = n * d
    psi = np.exp(2j * math.pi * 3 * x / L)
    r = ho.resample_to_pixel_centres(psi, b)
    X = ((np.arange(n // b) * b + 0.5 * (b - 1)) * d)[:, None]
    assert np.abs(r - np.exp(2j * math.pi * 3 * X / L)).max() < 1e-10
    amp = 1 + 0.3 * np.cos(2 * math.pi * x / L)
    i_bin = ho.bin_pixels(amp ** 2, b)
    i_res = np.abs(ho.resample_to_pixel_centres(amp.astype(complex), b)) ** 2
    assert np.abs(i_bin - i_res).max() < 2e-3


def test_mtf_models_and_aperture_area():
    assert abs(ho.mtf_value(0.25, "table", table=[[0.0, 1.0], [0.5, 0.2]]) - 0.6) < 1e-12
    assert abs(ho.mtf_value(0.25, "gaussian", sigma_px=0.4) - math.exp(-2 * math.pi ** 2 * 0.16 * 0.0625)) < 1e-12
    A = hs.aperture_at_origin(N, PIX, 0.3, "hard", 0.0)
    assert abs(ho.aperture_area(A, N, PIX) / (math.pi * 0.09) - 1) < 0.03


def test_step_height_sign_branch_and_no_step_control():
    lam, theta = 0.025079340317328468, 13.64e-3
    k = 4 * math.pi * math.sin(theta) / lam
    tops = [10.0, 10.3, 10.0, 10.0]           # up 0.3 Å, down 0.3 Å, flat, flat
    phis = [-k * t for t in tops]
    stats = [{"mean_rad": p, "sem_rad": 0.01} for p in phis]
    steps, h2pi = shf.quantify(stats, lam, theta, 3.0, 0.25, tops)
    assert abs(h2pi - lam / (2 * math.sin(theta))) < 1e-12
    assert abs(steps[0]["height_A"] - 0.3) < 1e-9 and abs(steps[1]["height_A"] + 0.3) < 1e-9
    assert steps[2]["result"] == "no step detected" and steps[2]["height_A"] is None
    assert steps[0]["branch_matching_truth"] == 0
    big = [{"mean_rad": 0.0, "sem_rad": 0.7}, {"mean_rad": 2.0, "sem_rad": 0.7}]
    s2, _ = shf.quantify(big, lam, theta, 1.0, 0.1)
    assert s2[0]["result"].startswith("refused")


def test_metrics():
    rng = np.random.default_rng(0)
    a = rng.standard_normal((32, 32))
    m = np.ones(a.shape, bool)
    assert abs(hm.ncc(0.5 * a + 3, a, m) - 1) < 1e-12        # NCC is blind to the scale...
    assert abs(hm.slope_fit(0.5 * a + 3, a, m)[0] - 0.5) < 1e-12  # ...the slope is not
    assert hm.registration_shift(np.roll(a, (3, -2), axis=(0, 1)), a) == [3, -2]


def test_apodisation_cancels_in_the_ratio_and_removes_boundary_leakage():
    psi = objective(np.exp(1j * stripe(1.5)))
    I_o, I_r, q_c = form(psi, 1.0, 37.0)
    errs = []
    for alpha in (0.0, 0.2):
        w, A, _ = recon(I_o, I_r, q_c, tukey=alpha)
        d = hs.wrap(np.angle(w) - np.angle(bandlimit(psi, A)))[16:-16, 16:-16]
        errs.append(np.abs(d).max())
        amp = np.abs(w / bandlimit(psi, A))[16:-16, 16:-16]
        assert np.abs(amp - 1).max() < 0.05  # the window cancels in object / reference
    assert errs[1] < 0.2 * errs[0], errs


def test_pixel_centre_resampling_on_awkward_grid_sizes():
    # audit MAJOR-1: fftfreq(N)*N truncated to int picked wrong bins for 78 of 182 grid sizes (e.g. 400, 405, 384)
    for nc in (400, 405, 384, 392, 525):
        n, b, d = 2 * nc, 2, 0.1
        L = n * d
        x = (np.arange(n) * d)[:, None] * np.ones((n, 4))
        X = ((np.arange(nc) * b + 0.5 * (b - 1)) * d)[:, None] * np.ones((nc, 2))  # y is binned too
        for m in (7, 28, 29, 58, 116):
            if m >= nc // 2:
                continue
            r = ho.resample_to_pixel_centres(np.exp(2j * math.pi * m * x / L), b)
            assert np.abs(r - np.exp(2j * math.pi * m * X / L)).max() < 1e-9, (nc, m)
