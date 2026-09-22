"""Validity by the empty hologram's fringe visibility, and region-wise unwrapping (re-audit A2b N5,
N6; scratch scripts r7_divide_empty.py, r7b_threshold_unwrap.py, r7c_threshold_noise.py).

N6: the earlier threshold was relative to the MEDIAN |empty sideband|; once the fringe-free area
approaches half the field the median collapses and fringe-free pixels passed as valid (30 %
coverage: 8236 of 8448 outside pixels VALID, rms phase error 0.67 rad). Now validity is the empty
hologram's local fringe visibility V = 2 |w_empty| / (the empty intensity low-passed by the same
mask centred on q = 0), against a REQUIRED declared minimum visibility (empty_min_visibility).
N5: the validity-aware Itoh unwrapper stopped at the first invalid pixel of column 0 (an invalid band
crossing column 0 turned everything below it to NaN; R2 with a shift towards -axis 1 gave no
unwrapped pixel). Now each connected valid region (4-connectivity) is unwrapped from its own seed;
different regions carry independent 2 pi offsets and are labelled.
Grid 128 x 128, pixel 1 A, carrier (0, 1/8) cycles/A (TEST_ONLY).
"""
import math
import warnings

import numpy as np
import pytest

from holo_cases import NO_ARTEFACTS, SIM_SIDEBAND
from reflection_holo.optics import (Grid, Hologram, Wave, apply_poisson_noise, hologram_intensity,
                                    reference_r1_vacuum_plane_wave, reference_r2_self_reference,
                                    vacuum_object_wave)
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier, reconstruct_sideband,
                                            unwrap_itoh_raster, wrap_to_pi)

N = 128


def grid():
    return Grid(shape=(N, N), pixel_size_A=(1.0, 1.0), axes=("y", "x"),
                plane="image plane (TEST_ONLY re-audit N5/N6)")


def pair():
    g = grid()
    u_r = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.0, 0.125), amplitude=1.0,
                                         relative_phase_rad=0.0, aperture_passage="no_aperture",
                                         realisation=None)
    E = hologram_intensity(vacuum_object_wave(g, amplitude=1.0, realisation=None), u_r,
                           artefacts=NO_ARTEFACTS, content="empty")
    H = hologram_intensity(Wave(np.full(g.shape, np.exp(0.3j)), g, "flat", None), u_r,
                           artefacts=NO_ARTEFACTS, content="object")
    return g, E, H


@pytest.mark.parametrize("frac", [0.8, 0.45, 0.3])
def test_fringe_free_area_is_invalid_whatever_its_size(frac):
    """The re-auditor's case r7c: dose 100 e/px, seed 5, fringes only in the first frac of the rows,
    top-hat mask |q|/3. Declared minimum visibility 0.3 (TEST_ONLY): the in-overlap visibility is 1,
    the fringe-free visibility is noise (about 2 x 0.66/100 = 0.013). Every pixel 12 rows or more
    inside the overlap is valid, every pixel 12 rows or more outside it is invalid (NaN). The valid
    phase error is bounded by 3 x the SM12 prediction sqrt(2) x sqrt(2)/(mu sqrt(N)) = 0.0148 rad
    (division by an equally noisy empty hologram)."""
    g, E, H = pair()
    nov = int(round(frac * N))
    Ei = E.intensity.copy()
    Ei[nov:, :] = 2.0
    Hi = H.intensity.copy()
    Hi[nov:, :] = 2.0
    En, Hn = apply_poisson_noise([Hologram(Ei, g, "empty", {}, None), Hologram(Hi, g, "object", {}, None)],
                                 dose_e_per_px=100.0, seed=5)
    c = locate_carrier(En, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    with pytest.warns(RuntimeWarning, match="visibility"):
        r = reconstruct_sideband(Hn, carrier=c, mask=MaskSpec(0.125 / 3, "disc", "none"),
                                 empty_hologram=En, reference_correction="divide_empty",
                                 unwrapping="none", empty_min_visibility=0.3)
    inside = np.zeros(g.shape, bool)
    inside[12:nov - 12, :] = True
    outside = np.zeros(g.shape, bool)
    outside[nov + 12:N - 12, :] = True
    err = np.abs(wrap_to_pi(r.wrapped_phase - 0.3))
    rms_in = float(np.sqrt(np.mean(err[inside] ** 2)))
    vis = r.parameters["validity"]
    print(f"overlap {frac:.0%}: inside valid {int(r.valid_mask[inside].sum())} of {int(inside.sum())}, "
          f"outside valid {int(r.valid_mask[outside].sum())} of {int(outside.sum())}; inside rms err "
          f"{rms_in:.4f} rad; visibility median inside {vis['visibility_median_valid']:.3f}")
    assert r.valid_mask[inside].all()
    assert not r.valid_mask[outside].any()
    assert np.all(np.isnan(r.wrapped_phase[outside]))
    assert rms_in <= 3 * math.sqrt(2) * math.sqrt(2) / math.sqrt(100.0 / (math.pi * (0.125 / 3) ** 2))


def test_minimum_visibility_is_required_and_bounded():
    g, E, H = pair()
    c = locate_carrier(E, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    kw = dict(carrier=c, mask=MaskSpec(0.04, "disc", "none"), empty_hologram=E,
              reference_correction="divide_empty", unwrapping="none")
    with pytest.raises(ValueError, match="empty_min_visibility"):
        reconstruct_sideband(H, **kw)
    for bad in (0.0, -0.1, 1.5, float("nan")):
        with pytest.raises(ValueError, match="empty_min_visibility"):
            reconstruct_sideband(H, **kw, empty_min_visibility=bad)
    r = reconstruct_sideband(H, **kw, empty_min_visibility=0.9)      # visibility 1 everywhere
    assert r.valid_mask.all()
    assert r.parameters["validity"]["empty_min_visibility"] == 0.9


def test_invalid_band_across_column_0_does_not_blank_the_field():
    """r7: rows 4-11 of the empty and object holograms fringe-free; rows 12-127 must be unwrapped.
    Declared minimum visibility 0.7 (TEST_ONLY): the band is narrower than the 24 px resolution,
    so its smoothed visibility is about 0.6 and 0.7 makes rows 3-12 invalid (as in r7)."""
    g, E, H = pair()
    Ei = E.intensity.copy()
    Ei[4:12, :] = 1.0
    Hi = H.intensity.copy()
    Hi[4:12, :] = 1.0
    c = locate_carrier(E, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        r = reconstruct_sideband(Hologram(Hi, g, "object", {}, None), carrier=c,
                                 mask=MaskSpec(0.125 / 3, "disc", "none"),
                                 empty_hologram=Hologram(Ei, g, "empty", {}, None),
                                 reference_correction="divide_empty", unwrapping="itoh_raster",
                                 empty_min_visibility=0.7)
    assert not r.valid_mask[4:12].any()
    un = r.unwrapped_phase
    assert np.array_equal(np.isfinite(un), r.valid_mask)             # every valid pixel unwrapped
    assert r.parameters["unwrapping_regions"] >= 2
    assert np.max(np.abs(un[40:-8, 8:-8] - 0.3)) <= 5e-3              # T25 tolerance, as before
    labels = r.unwrap_regions
    assert labels.shape == g.shape and set(np.unique(labels[r.valid_mask])) >= {1, 2}
    assert np.all(labels[~r.valid_mask] == 0)


@pytest.mark.parametrize("shift", [(0.0, 16.0), (0.0, -16.0), (16.0, 0.0), (-16.0, 0.0)])
def test_r2_shift_in_any_direction_is_unwrapped(shift):
    """r7b: R2 with a shift towards -axis 1 left no unwrapped pixel."""
    g = grid()
    u = Wave(np.ones(g.shape), g, "flat", None)
    ref2 = reference_r2_self_reference(u, shift_A=shift, carrier_cycles_per_A=(0.0, 0.125),
                                       amplitude_scale=1.0, relative_phase_rad=0.0)
    H2 = hologram_intensity(u, ref2, artefacts=NO_ARTEFACTS, content="flat_region")
    c2 = locate_carrier(H2, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    r2 = reconstruct_sideband(H2, carrier=c2, mask=MaskSpec(0.04, "disc", "hann"),
                              empty_hologram=None, reference_correction="none",
                              unwrapping="itoh_raster")
    assert int(r2.valid_mask.sum()) == 14336
    assert np.array_equal(np.isfinite(r2.unwrapped_phase), r2.valid_mask)


def test_regions_are_unwrapped_up_to_one_2pi_offset_each():
    """A smooth ramp (up to 40 rad) with an invalid band across column 0 and an invalid hole: inside
    each connected region the unwrapped phase equals the true phase plus one constant multiple of
    2 pi (1e-9 rad); for an all-valid field the result is the plain raster unwrap."""
    g = grid()
    r0, r1 = g.coordinates_A()
    true = 0.17 * r0 - 0.11 * r1 + 3e-4 * (r1 - 40.0) ** 2
    valid = np.ones(g.shape, bool)
    valid[30:36, :] = False                      # band across column 0: two regions
    valid[70:80, 0:50] = False                   # block at the left edge
    valid[90:95, 60:70] = False                  # hole
    w = wrap_to_pi(true)
    un, labels = unwrap_itoh_raster(np.where(valid, w, np.nan), valid, return_regions=True)
    assert np.array_equal(np.isfinite(un), valid)
    assert labels.max() == 2
    for k in (1, 2):
        dk = (un - true)[labels == k]
        assert np.max(np.abs(dk - dk[0])) <= 1e-9
        assert abs(dk[0] / (2 * np.pi) - round(dk[0] / (2 * np.pi))) <= 1e-9
    full = unwrap_itoh_raster(w)
    assert np.array_equal(full, np.unwrap(w, axis=1) + (np.unwrap(w[:, 0]) - w[:, 0])[:, None])
