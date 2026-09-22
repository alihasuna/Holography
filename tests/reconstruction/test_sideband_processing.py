"""Sideband processing: sign convention, sub-pixel carrier, reference correction (R3), resolution report,
no implicit detrend, explicit plane fit, unwrapping, flat-region carrier location, required inputs
(docs/05 sections 5 item 7 and 8; PROJECT_INPUT item 19; audit C3, M5).

Tolerances stated per test. Where a flat-control tolerance is needed, T25's 5e-3 rad is used.
"""
import numpy as np
import pytest

from holo_cases import (NO_ARTEFACTS, T24_TOL_RAD, T25_TOL_RAD, calculator_T24_reference, calculator_mask,
                        calculator_measure, calculator_search, calculator_setup_holograms, make_grid,
                        r1_reference)
from reflection_holo.optics import (Grid, Hologram, Wave, hologram_intensity, reference_r3_curved_tilted,
                                    vacuum_object_wave)
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, fit_phase_plane, locate_carrier,
                                            reconstruct_sideband, subtract_phase_plane, unwrap_itoh_raster,
                                            wrap_to_pi)


def _flat_pair(grid, q, phi_o, phi_rel):
    u_o = Wave(np.full(grid.shape, np.exp(1j * phi_o)), grid, "flat object", None)
    u_r = r1_reference(grid, q, relative_phase_rad=phi_rel)
    H = hologram_intensity(u_o, u_r, artefacts=NO_ARTEFACTS, content="object")
    H_e = hologram_intensity(vacuum_object_wave(grid, amplitude=1.0, realisation=None), u_r,
                             artefacts=NO_ARTEFACTS, content="empty")
    return H, H_e


def _search(q, subpixel):
    return CarrierSearch((-q[0], -q[1]), 0.5 * float(np.hypot(*q)), 0.02, subpixel)


def _hann_third(c):
    return MaskSpec(c.carrier_magnitude_cycles_per_A / 3.0, "disc", "hann")


@pytest.mark.parametrize("q", [(0.0, 0.125), (0.0, -0.125), (0.0625, 0.125), (-0.125, 0.03125)])
def test_returned_phase_is_phi_o_minus_phi_r(q):
    """Flat object phase 0.7 rad, reference relative phase 0.2 rad: the raw phase is +0.5 rad for any
    carrier direction (noiseless, periodic integer carrier: exact to 1e-9 rad)."""
    grid = make_grid(256)
    H, H_e = _flat_pair(grid, q, 0.7, 0.2)
    c = locate_carrier(H_e, _search(q, "none"))
    assert np.allclose(c.carrier_cycles_per_A, q, atol=1e-15)
    res = reconstruct_sideband(H, carrier=c, mask=_hann_third(c), empty_hologram=None,
                               reference_correction="none", unwrapping="none")
    assert np.max(np.abs(res.wrapped_phase_raw - 0.5)) <= 1e-9
    assert np.allclose(res.amplitude, 1.0, atol=1e-9)          # |u_o||u_r|
    assert res.sideband_sign_check.startswith("phi_o - phi_r")


def test_resolution_reported_three_fringe_spacings():
    grid = make_grid(256)
    q = (0.0, 0.125)
    H, H_e = _flat_pair(grid, q, 0.0, 0.0)
    c = locate_carrier(H_e, _search(q, "none"))
    res = reconstruct_sideband(H, carrier=c, mask=_hann_third(c), empty_hologram=None,
                               reference_correction="none", unwrapping="none")
    assert res.resolution_A == pytest.approx(3.0 * c.fringe_spacing_A, rel=1e-12)
    assert res.resolution_fringe_spacings == pytest.approx(3.0, rel=1e-12)
    assert res.resolution_A == pytest.approx(24.0, rel=1e-12)      # fringe 8 A, pixel 1 A
    assert res.parameters["ramp_removal"].startswith("none")
    assert res.parameters["mask"] == {"radius_cycles_per_A": 0.125 / 3.0, "shape": "disc", "apodisation": "hann"}


@pytest.mark.parametrize("delta", [0.3, -0.27, 0.45])
def test_subpixel_carrier_refinement(delta):
    """Carrier off the bin grid by delta bins: 'dft_ratio' locates it within 1e-3 bins and leaves a
    flat interior (>= 3 resolutions from the edge) within 5e-3 rad of phi_o - phi_r (T25 tolerance);
    'none' leaves a ramp of order 2 pi delta across the field."""
    n = 256
    grid = make_grid(n)
    q = ((5 + delta) / n, (32 + 0.37 * delta) / n)
    H, H_e = _flat_pair(grid, q, 0.7, 0.2)
    c = locate_carrier(H_e, _search(q, "dft_ratio"))
    err_bins = (np.asarray(c.sideband_centre_cycles_per_A) + np.asarray(q)) * n
    assert np.max(np.abs(err_bins)) <= 1e-3
    out = {}
    for sp, carrier in (("dft_ratio", c), ("none", locate_carrier(H_e, _search(q, "none")))):
        res = reconstruct_sideband(H, carrier=carrier, mask=_hann_third(carrier), empty_hologram=None,
                                   reference_correction="none", unwrapping="none")
        pad = int(np.ceil(3 * res.resolution_A))
        out[sp] = np.max(np.abs(wrap_to_pi(res.wrapped_phase[pad:n - pad, pad:n - pad] - 0.5)))
    assert out["dft_ratio"] <= T25_TOL_RAD
    assert out["none"] > 1.0


def test_r3_residual_is_entangled_without_correction_and_removed_with_empty_hologram():
    """R3 reference with residual tilt (1/512, 0) cycles/A and curvature (2e-6, 0.5e-6, 1e-6) rad/A^2
    on a flat object. Without correction the raw phase is -quad + const (within 1e-3 rad in the
    interior, >= 3 resolutions from the edge); dividing by an empty hologram recorded with the same
    reference returns 0 within T25's 5e-3 rad."""
    n = 512
    grid = make_grid(n)
    q, t, curv, cen = (0.0, 0.125), (1.0 / 512, 0.0), (2e-6, 0.5e-6, 1e-6), (256.0, 256.0)
    u_r = reference_r3_curved_tilted(grid, carrier_cycles_per_A=q, amplitude=1.0, relative_phase_rad=0.0,
                                     residual_tilt_cycles_per_A=t, residual_curvature_rad_per_A2=curv,
                                     curvature_centre_A=cen, realisation=None)
    H = hologram_intensity(Wave(np.ones(grid.shape), grid, "flat", None), u_r, artefacts=NO_ARTEFACTS,
                           content="object")
    H_e = hologram_intensity(vacuum_object_wave(grid, amplitude=1.0, realisation=None), u_r,
                             artefacts=NO_ARTEFACTS, content="empty")
    c = locate_carrier(H_e, CarrierSearch((-q[0] - t[0], -q[1] - t[1]), 0.05, 0.05, "none"))
    assert c.integer_bin == (511, 448)          # the residual tilt is part of the located carrier
    r0, r1 = grid.coordinates_A()
    quad = curv[0] * (r0 - cen[0]) ** 2 + 2 * curv[1] * (r0 - cen[0]) * (r1 - cen[1]) + curv[2] * (r1 - cen[1]) ** 2
    sl = (slice(72, n - 72), slice(72, n - 72))
    raw = reconstruct_sideband(H, carrier=c, mask=_hann_third(c), empty_hologram=None,
                               reference_correction="none", unwrapping="itoh_raster")
    d = raw.unwrapped_phase + quad
    d = d - d[256, 256]
    assert np.max(np.abs(d[sl])) <= 1e-3
    assert np.ptp((raw.unwrapped_phase)[sl]) > 0.1                 # the residual is really there
    corr = reconstruct_sideband(H, carrier=c, mask=_hann_third(c), empty_hologram=H_e,
                                reference_correction="divide_empty", unwrapping="none")
    assert np.max(np.abs(corr.wrapped_phase[sl])) <= T25_TOL_RAD
    assert np.array_equal(corr.wrapped_phase_raw, raw.wrapped_phase_raw)   # raw kept, uncorrected


def test_no_implicit_detrend_and_explicit_plane_fit():
    """An object phase ramp survives reconstruction (no default detrend, audit M5); an explicit plane
    fit over a declared region recovers it; the raw phase is never modified."""
    n = 256
    grid = make_grid(n)
    # field-periodic ramp (2 and -1 cycles across the 256 A field), so no FFT boundary leakage enters;
    # it wraps inside the fitting region. (A non-periodic ramp of 0.05/-0.01 rad/A gave a fitted
    # gradient off by 1.7e-6 rad/A from boundary leakage: no real-space window is implemented.)
    g0, g1 = 2 * np.pi * 2 / 256, -2 * np.pi * 1 / 256    # rad/A
    r0, r1 = grid.coordinates_A()
    u_o = Wave(np.exp(1j * (g0 * r0 + g1 * r1)), grid, "ramp object", None)
    q = (0.0, 0.125)
    u_r = r1_reference(grid, q)
    H = hologram_intensity(u_o, u_r, artefacts=NO_ARTEFACTS, content="object")
    H_e = hologram_intensity(vacuum_object_wave(grid, amplitude=1.0, realisation=None), u_r,
                             artefacts=NO_ARTEFACTS, content="empty")
    c = locate_carrier(H_e, _search(q, "none"))
    res = reconstruct_sideband(H, carrier=c, mask=_hann_third(c), empty_hologram=H_e,
                               reference_correction="divide_empty", unwrapping="itoh_raster")
    raw_before = res.wrapped_phase_raw.copy()
    region = np.zeros(grid.shape, bool)
    region[80:176, 80:176] = True
    with pytest.raises(ValueError):                         # wrapped phase: not continuous in region
        fit_phase_plane(res.wrapped_phase, grid, region, region_description="interior square")
    fit = fit_phase_plane(res.unwrapped_phase, grid, region, region_description="interior square 80:176")
    assert fit.gradient_rad_per_A == pytest.approx((g0, g1), abs=1e-6)
    flat = subtract_phase_plane(res.unwrapped_phase, fit)
    assert np.max(np.abs(flat[region])) <= 1e-6
    assert np.array_equal(res.wrapped_phase_raw, raw_before)
    assert not res.wrapped_phase_raw.flags.writeable
    # the reconstructed (unfitted) phase still carries the ramp
    assert np.ptp(res.unwrapped_phase[region]) > 1.0
    assert fit.as_record()["region_description"] == "interior square 80:176"


def test_itoh_raster_unwrap_recovers_smooth_phase():
    grid = make_grid(128)
    r0, r1 = grid.coordinates_A()
    true = 0.09 * r0 - 0.07 * r1 + 2e-4 * (r0 - 64) ** 2
    assert abs(true[0, 0]) < np.pi
    un = unwrap_itoh_raster(wrap_to_pi(true))
    assert np.max(np.abs(un - true)) <= 1e-9


def test_carrier_from_flat_region_crop():
    """Carrier located on a flat-region crop (different shape, same sampling) of the T24 object
    hologram; no empty hologram; the step is recovered within T24's tolerance."""
    want, _ = calculator_T24_reference()
    grid, q_ref, H_obj, _ = calculator_setup_holograms(want, dose_per_px=1e4, seed=12345)
    crop_grid = Grid((128, 512), grid.pixel_size_A, grid.axes, grid.plane)
    crop = Hologram(H_obj.intensity[:128, :], crop_grid, "flat_region",
                    {"source": "rows 0:128 of the object hologram (lower terrace)"}, None)
    c = locate_carrier(crop, calculator_search(q_ref, "none"))
    res = reconstruct_sideband(H_obj, carrier=c, mask=calculator_mask(c), empty_hologram=None,
                               reference_correction="none", unwrapping="none")
    got, _ = calculator_measure(res.wrapped_phase, res.resolution_A, 512)
    assert abs(got - want) <= T24_TOL_RAD


def test_required_processing_inputs():
    grid = make_grid(64)
    q = (0.0, 0.125)
    H, H_e = _flat_pair(grid, q, 0.0, 0.0)
    with pytest.raises(TypeError):
        CarrierSearch((-q[0], -q[1]), 0.05, 0.02)               # subpixel not declared
    with pytest.raises(ValueError):
        CarrierSearch(None, 0.05, 0.02, "none")                 # missing sideband guess
    with pytest.raises(ValueError):
        CarrierSearch((-q[0], -q[1]), 0.05, 0.02, "parabolic")  # undeclared method
    with pytest.raises(ValueError):
        MaskSpec(None, "disc", "hann")
    with pytest.raises(TypeError):
        MaskSpec(0.04, "disc")
    with pytest.raises(ValueError):
        locate_carrier(H, _search(q, "none"))                   # object hologram refused
    c = locate_carrier(H_e, _search(q, "none"))
    m = _hann_third(c)
    with pytest.raises(TypeError):
        reconstruct_sideband(H, carrier=c, mask=m, empty_hologram=None, unwrapping="none")
    with pytest.raises(ValueError):
        reconstruct_sideband(H, carrier=c, mask=m, empty_hologram=None, reference_correction="divide_empty",
                             unwrapping="none")
    with pytest.raises(ValueError):
        reconstruct_sideband(H, carrier=c, mask=m, empty_hologram=H_e, reference_correction="none",
                             unwrapping="none")
    with pytest.raises(ValueError):                             # mask would contain q = 0
        reconstruct_sideband(H, carrier=c, mask=MaskSpec(0.2, "disc", "hann"), empty_hologram=None,
                             reference_correction="none", unwrapping="none")
    q_hi = (0.0, 0.375)                                         # 24 bins of 64, close to Nyquist 0.5
    H_hi, H_hi_e = _flat_pair(grid, q_hi, 0.0, 0.0)
    c_hi = locate_carrier(H_hi_e, _search(q_hi, "none"))
    with pytest.raises(ValueError):                             # 0.375 + 0.13 crosses Nyquist
        reconstruct_sideband(H_hi, carrier=c_hi, mask=MaskSpec(0.13, "disc", "none"), empty_hologram=None,
                             reference_correction="none", unwrapping="none")
    other = Grid(grid.shape, (1.0, 2.0), grid.axes, grid.plane)
    H_other = Hologram(H.intensity, other, "object", {}, None)
    with pytest.raises(ValueError):                             # sampling differs from carrier grid
        reconstruct_sideband(H_other, carrier=c, mask=m, empty_hologram=None, reference_correction="none",
                             unwrapping="none")
