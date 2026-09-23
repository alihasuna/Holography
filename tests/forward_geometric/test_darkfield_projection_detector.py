"""optics.darkfield, optics.projection and optics.detector (docs/05 section 5 items 1, 2, 6).
TEST_ONLY values stand in for PROJECT_INPUT items 4, 5 and 6 and never appear in configs/.
Tolerances are stated per test and were chosen before running."""
import math

import numpy as np
import pytest

from reflection_holo.forward.contracts import ExitWave
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.optics.darkfield import DarkFieldAperture, select_dark_field
from reflection_holo.optics.detector import DetectorSpec, record_holograms, resample_to_detector
from reflection_holo.optics.fields import Grid, Hologram
from reflection_holo.optics.projection import project_along_k_out

LAM = wavelength_A(200.0)
THETA = 16.47e-3
AP = DarkFieldAperture(semi_angle_rad=3e-3, beam="specular",
                       label="TEST_ONLY: stands in for PROJECT_INPUT item 4")
L5 = "TEST_ONLY: stands in for PROJECT_INPUT item 5"
L6 = "TEST_ONLY: stands in for PROJECT_INPUT item 6"


def exit_wave(env_fn, *, nx=1024, ny=16, dx=0.25, dy=0.5, x0=-30.0, energy=200.0,
              with_incident=False):
    """Envelope times the k_out carrier (plus optionally the incident k_in component)."""
    x = x0 + dx * np.arange(nx)
    y = dy * np.arange(ny)
    X, Y = np.meshgrid(x, y, indexing="ij")
    qo = math.sin(THETA) / LAM
    psi = env_fn(X, Y) * np.exp(2j * np.pi * qo * X)
    if with_incident:
        psi = psi + env_fn(X, Y) * np.exp(-2j * np.pi * qo * X)
    return ExitWave(psi=psi.astype(np.complex128), dx_A=dx, dy_A=dy, x0_A=x0, y0_A=0.0,
                    plane="exit plane z = L_z (TEST_ONLY synthetic)", z_A=100.0, energy_keV=energy,
                    theta_in_ext_rad=THETA, realisation=0, seed=None, metadata={})


def gauss(X, Y):
    return np.exp(-((X - 98.0) / 20.0) ** 2)


def test_aperture_selects_k_out_and_demodulates():
    """The incident component (at -q_out) is removed; the demodulated envelope equals the input
    envelope (smooth Gaussian, band far inside the aperture) to 1e-6 relative."""
    ew = exit_wave(gauss, with_incident=True)
    df = select_dark_field(ew, AP, energy_keV=200.0, theta_out_ext_rad=THETA)
    x = ew.x0_A + ew.dx_A * np.arange(ew.psi.shape[0])
    want = np.exp(-((x - 98.0) / 20.0) ** 2)
    got = np.asarray(df.wave.data)[:, 3]
    assert np.max(np.abs(got - want)) <= 1e-6
    rec = df.record
    assert rec["aperture_centre_cycles_per_A"][0] == pytest.approx(math.sin(THETA) / LAM, rel=1e-12)
    assert rec["semi_angle_rad"] == 3e-3 and rec["label"].startswith("TEST_ONLY")
    assert 0.49 < rec["fraction_of_power_passed"] < 0.51      # half the power was incident beam


def test_aperture_beyond_nyquist_and_wrong_energy_are_refused():
    ew = exit_wave(gauss, dx=0.7)
    with pytest.raises(ValueError, match="Nyquist"):
        select_dark_field(ew, AP, energy_keV=200.0, theta_out_ext_rad=THETA)
    ew = exit_wave(gauss, energy=300.0)
    with pytest.raises(ValueError, match="200"):
        select_dark_field(ew, AP, energy_keV=200.0, theta_out_ext_rad=THETA)


def test_projection_mapping_and_stated_samplings():
    ew = exit_wave(gauss)
    df = select_dark_field(ew, AP, energy_keV=200.0, theta_out_ext_rad=THETA)
    x0 = 150.0
    img = project_along_k_out(df, x0_A=x0, x0_definition="TEST_ONLY reference height",
                              aperture_semi_angle_rad=3e-3)
    x = img.exit_x_A
    assert np.allclose(img.surface_z_A, (x0 - x) / math.tan(THETA), rtol=0, atol=1e-9)
    assert np.allclose(img.image_u_A, img.surface_z_A * math.sin(THETA), rtol=0, atol=1e-9)
    assert np.all(np.diff(img.surface_z_A) > 0)                # along-beam axis runs downstream
    s = img.sampling
    assert s["surface_dz_s_A"] == pytest.approx(0.25 / math.tan(THETA), rel=1e-12)
    assert s["image_du_A"] == pytest.approx(0.25 * math.cos(THETA), rel=1e-12)
    assert img.wave.grid.pixel_size_A == pytest.approx((0.25 * math.cos(THETA), 0.5))
    assert np.array_equal(np.asarray(img.wave.data), np.asarray(df.wave.data)[::-1])


def spec(**kw):
    base = dict(pixel_pitch_um=(15.0, 15.0), magnification=3.0e5, image_pixel_size_A=(0.5, 0.5),
                roi_shape=(64, 8), alignment="centre", dose_e_per_px=400.0, gain_counts_per_e=2.0,
                mtf="none", label_item5=L5, label_item6=L6)
    base.update(kw)
    return DetectorSpec(**base)


def test_detector_item5_consistency_and_mtf():
    with pytest.raises(ValueError, match="item 5 inconsistent"):
        spec(magnification=2.0e5)
    with pytest.raises(NotImplementedError, match="MTF"):
        spec(mtf="measured")


def test_band_limited_resampling_matches_the_analytic_envelope():
    """The Gaussian envelope resampled onto 0.5 A detector pixels equals the analytic value at
    the pixel centres to 1e-6 (band-limited DFT interpolation)."""
    ew = exit_wave(gauss)
    df = select_dark_field(ew, AP, energy_keV=200.0, theta_out_ext_rad=THETA)
    img = project_along_k_out(df, x0_A=150.0, x0_definition="TEST_ONLY",
                              aperture_semi_angle_rad=3e-3)
    band = math.sin(3e-3) / LAM
    w, pl = resample_to_detector(img, spec(), band_cycles_per_A=band)
    x_det = 150.0 - pl.u_A / math.cos(THETA)
    want = np.exp(-((x_det - 98.0) / 20.0) ** 2)
    assert np.max(np.abs(np.asarray(w.data)[:, 2] - want)) <= 1e-6
    assert w.grid.axes == ("along_beam", "perpendicular") and w.grid.pixel_size_A == (0.5, 0.5)
    with pytest.raises(ValueError, match="outside"):
        resample_to_detector(img, spec(roi_shape=(1024, 8)), band_cycles_per_A=band)
    with pytest.raises(ValueError, match="alias"):
        resample_to_detector(img, spec(), band_cycles_per_A=1.5)


def test_gain_and_dose():
    g = Grid(shape=(64, 64), pixel_size_A=(0.5, 0.5), axes=("along_beam", "perpendicular"),
             plane="TEST_ONLY")
    h = Hologram(np.ones((64, 64)), g, "empty", {}, None)
    out = record_holograms([h], spec(), seed=7)[0]
    assert out.metadata["detector"]["gain_counts_per_e"] == 2.0
    assert np.mean(out.intensity) == pytest.approx(2.0 * 400.0, rel=0.01)
    assert np.all(np.mod(out.intensity, 2.0) == 0)


def test_field_of_view_alignment_needs_the_interval():
    ew = exit_wave(gauss)
    df = select_dark_field(ew, AP, energy_keV=200.0, theta_out_ext_rad=THETA)
    img = project_along_k_out(df, x0_A=150.0, x0_definition="TEST_ONLY",
                              aperture_semi_angle_rad=3e-3)
    band = math.sin(3e-3) / LAM
    with pytest.raises(ValueError, match="field_of_view"):
        resample_to_detector(img, spec(alignment="field_of_view"), band_cycles_per_A=band)
    w, pl = resample_to_detector(img, spec(alignment="field_of_view"), band_cycles_per_A=band,
                                 field_of_view_u_A=(0.0, 1.0))
    assert abs(0.5 * (pl.u_A[0] + pl.u_A[-1]) - 0.5) <= 1e-12
