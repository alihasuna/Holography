"""Validity mask of the reconstruction (audit A2 finding m1; S1c NOT IMPLEMENTED item).

The auditor's cases (A2 m1, scratch scripts e7 and e9), 128 x 128 or 64 x 64 grids, pixel 1 A,
carrier (0, 1/8) cycles/A (TEST_ONLY):
* a fringe-free "empty" hologram has an empty sideband exactly 0; the unfixed divide_empty gave
  inf + inf j and a finite phase pi/4 everywhere, with no warning and no mask;
* rows 0..15 outside the biprism overlap (no fringes) give a near-zero empty sideband (median about
  0.09 of the overlap value) and finite garbage phases that the raster unwrapper walked through;
* the R2 valid_mask was dropped by ensemble_hologram_intensity and never reached SidebandResult.
Now: pixels whose empty-hologram sideband amplitude is at or below the DECLARED relative threshold
(empty_amplitude_threshold x median over the field; exact zeros always) get NaN phase and amplitude,
valid_mask False, and a RuntimeWarning; the R2 mask is ANDed into valid_mask; the Itoh raster
unwrapper starts at the first valid pixel of column 0 and returns NaN where its path meets an
invalid pixel; fit_phase_plane refuses invalid pixels in its region.
Tolerance for recovered phases far from invalid regions: T25's 5e-3 rad.
"""
import numpy as np
import pytest

from holo_cases import NO_ARTEFACTS, SIM_SIDEBAND, T25_TOL_RAD
from reflection_holo.optics import (Grid, Hologram, Wave, apply_poisson_noise,
                                    ensemble_hologram_intensity, hologram_intensity,
                                    reference_r1_vacuum_plane_wave, reference_r2_self_reference,
                                    vacuum_object_wave)
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, fit_phase_plane, locate_carrier,
                                            reconstruct_sideband, unwrap_itoh_raster)

Q = (0.0, 0.125)


def grid(n):
    return Grid(shape=(n, n), pixel_size_A=(1.0, 1.0), axes=("y", "x"),
                plane="image plane (TEST_ONLY audit m1 case)")


def pair(n=128, phi=0.3):
    g = grid(n)
    u_r = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=Q, amplitude=1.0,
                                         relative_phase_rad=0.0, aperture_passage="no_aperture",
                                         realisation=None)
    E = hologram_intensity(vacuum_object_wave(g, amplitude=1.0, realisation=None), u_r,
                           artefacts=NO_ARTEFACTS, content="empty")
    H = hologram_intensity(Wave(np.full(g.shape, np.exp(1j * phi)), g, "flat", None), u_r,
                           artefacts=NO_ARTEFACTS, content="object")
    c = locate_carrier(E, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    return g, E, H, c


def test_fringe_free_empty_hologram_gives_nan_mask_and_warning():
    g, E, H, c = pair()
    Ez = Hologram(np.full(g.shape, 5.0), g, "empty", {}, None)     # empty sideband exactly 0
    with pytest.warns(RuntimeWarning, match="empty-hologram sideband"):
        res = reconstruct_sideband(H, carrier=c, mask=MaskSpec(0.125 / 3, "disc", "none"),
                                   empty_hologram=Ez, reference_correction="divide_empty",
                                   unwrapping="itoh_raster", empty_amplitude_threshold=0.0)
    assert np.max(np.abs(res.empty_sideband)) == 0.0
    assert not res.valid_mask.any()
    assert np.all(np.isnan(res.wrapped_phase)) and np.all(np.isnan(res.amplitude))
    assert np.all(np.isnan(res.unwrapped_phase))
    assert np.all(np.isfinite(res.wrapped_phase_raw))              # the raw phase is kept
    assert res.parameters["validity"]["n_invalid_amplitude"] == g.shape[0] * g.shape[1]


def test_rows_outside_the_overlap_are_flagged_and_not_unwrapped_through():
    g, E, H, c = pair()
    Ei = E.intensity.copy()
    Ei[:16, :] = 1.0
    Hi = H.intensity.copy()
    Hi[:16, :] = 1.0
    E2 = Hologram(Ei, g, "empty", {}, None)
    H2 = Hologram(Hi, g, "object", {}, None)
    with pytest.warns(RuntimeWarning, match="empty-hologram sideband"):
        res = reconstruct_sideband(H2, carrier=c, mask=MaskSpec(0.125 / 3, "disc", "none"),
                                   empty_hologram=E2, reference_correction="divide_empty",
                                   unwrapping="itoh_raster", empty_amplitude_threshold=0.5)
    assert not res.valid_mask[:8].any() and res.valid_mask[40:].all()
    assert np.all(np.isnan(res.wrapped_phase[~res.valid_mask]))
    assert np.max(np.abs(res.wrapped_phase[40:-8, 8:-8] - 0.3)) <= T25_TOL_RAD
    un = res.unwrapped_phase
    assert np.all(np.isnan(un[~res.valid_mask]))
    assert np.max(np.abs(un[40:-8, 8:-8] - 0.3)) <= T25_TOL_RAD


def test_r2_valid_mask_reaches_the_result_through_ensemble_and_noise():
    g = grid(64)
    u = Wave(np.ones(g.shape), g, "flat", None)
    ref2 = reference_r2_self_reference(u, shift_A=(0.0, 16.0), carrier_cycles_per_A=Q,
                                       amplitude_scale=1.0, relative_phase_rad=0.0)
    want = ref2.metadata["valid_mask"]
    H1 = hologram_intensity(u, ref2, artefacts=NO_ARTEFACTS, content="flat_region")
    He = ensemble_hologram_intensity([(u, ref2)], artefacts=NO_ARTEFACTS, content="flat_region")
    Hn, = apply_poisson_noise([H1], dose_e_per_px=100.0, seed=1)
    for h in (H1, He, Hn):
        assert np.array_equal(h.metadata["valid_mask"], want)
    assert Hn.metadata["valid_mask"] is not H1.metadata["valid_mask"]       # no shared state
    c = locate_carrier(H1, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    res = reconstruct_sideband(He, carrier=c, mask=MaskSpec(0.04, "disc", "hann"),
                               empty_hologram=None, reference_correction="none", unwrapping="none")
    assert np.array_equal(res.valid_mask, want)
    assert not res.valid_mask.flags.writeable


def test_fit_phase_plane_refuses_invalid_pixels():
    g = grid(32)
    p = np.zeros(g.shape)
    p[5, 5] = np.nan
    region = np.zeros(g.shape, bool)
    region[2:10, 2:10] = True
    with pytest.raises(ValueError, match="invalid"):
        fit_phase_plane(p, g, region, region_description="square with a NaN pixel")


def test_unwrapper_unchanged_for_valid_input_and_starts_at_first_valid_pixel():
    g = grid(64)
    r0, r1 = g.coordinates_A()
    true = 0.09 * r0 - 0.07 * r1
    w = np.angle(np.exp(1j * true))
    assert np.array_equal(unwrap_itoh_raster(w), np.unwrap(w, axis=1)
                          + (np.unwrap(w[:, 0]) - w[:, 0])[:, None])
    w2 = w.copy()
    w2[:3, :] = np.nan
    un = unwrap_itoh_raster(w2)
    assert np.all(np.isnan(un[:3])) and np.all(np.isfinite(un[3:]))
    assert np.max(np.abs(un[3:] - (true[3:] - true[3, 0] + w[3, 0]))) <= 1e-9


def test_threshold_is_declared_when_dividing():
    g, E, H, c = pair(64)
    mask = MaskSpec(0.04, "disc", "none")
    with pytest.raises(ValueError, match="empty_amplitude_threshold"):
        reconstruct_sideband(H, carrier=c, mask=mask, empty_hologram=E,
                             reference_correction="divide_empty", unwrapping="none")
    with pytest.raises(ValueError, match="empty_amplitude_threshold"):
        reconstruct_sideband(H, carrier=c, mask=mask, empty_hologram=None,
                             reference_correction="none", unwrapping="none",
                             empty_amplitude_threshold=0.1)
    for bad in (-0.1, 1.0, np.nan):
        with pytest.raises(ValueError, match="empty_amplitude_threshold"):
            reconstruct_sideband(H, carrier=c, mask=mask, empty_hologram=E,
                                 reference_correction="divide_empty", unwrapping="none",
                                 empty_amplitude_threshold=bad)


def test_zero_object_sideband_without_correction_is_nan():
    g, E, H, c = pair(64)
    Hz = Hologram(np.full(g.shape, 2.0), g, "object", {}, None)
    with pytest.warns(RuntimeWarning, match="object-hologram sideband"):
        res = reconstruct_sideband(Hz, carrier=c, mask=MaskSpec(0.04, "disc", "none"),
                                   empty_hologram=None, reference_correction="none",
                                   unwrapping="none")
    assert not res.valid_mask.any() and np.all(np.isnan(res.wrapped_phase))
