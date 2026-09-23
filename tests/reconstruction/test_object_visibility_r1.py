"""A2c residual R1 (docs/agent_reports/A2c_verification.md, "Residuals and decisions"; scratch probe
r7d_none_and_speed.py): with reference_correction="none" (no empty hologram: R2, or an experiment
without a reference hologram) there was no visibility criterion; only exact zeros were flagged, and
at 30 % overlap 8448 of 8448 fringe-free pixels were flagged VALID (rms phase error 2.02 rad).
Now "none" requires a declared object_min_visibility, applied to the OBJECT hologram's local fringe
visibility 2 |w_obj| / D_obj (the same definition as the empty-hologram criterion of N6).
Grid 128 x 128, pixel 1 A, carrier (0, 1/8) cycles/A (TEST_ONLY), as test_validity_round2.py.
"""
import math

import numpy as np
import pytest

from holo_cases import NO_ARTEFACTS, SIM_SIDEBAND
from reflection_holo.optics import (Grid, Hologram, Wave, apply_poisson_noise, hologram_intensity,
                                    reference_r1_vacuum_plane_wave)
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier,
                                            reconstruct_sideband, wrap_to_pi)

N = 128


def _object_hologram(frac):
    g = Grid(shape=(N, N), pixel_size_A=(1.0, 1.0), axes=("y", "x"),
             plane="image plane (TEST_ONLY A2c R1)")
    u_r = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.0, 0.125), amplitude=1.0,
                                         relative_phase_rad=0.0, aperture_passage="no_aperture",
                                         realisation=None)
    H = hologram_intensity(Wave(np.full(g.shape, np.exp(0.3j)), g, "flat", None), u_r,
                           artefacts=NO_ARTEFACTS, content="flat_region")
    nov = int(round(frac * N))
    Hi = H.intensity.copy()
    Hi[nov:, :] = 2.0                                  # no fringes outside the overlap
    (Hn,) = apply_poisson_noise([Hologram(Hi, g, "flat_region", {}, None)], dose_e_per_px=100.0,
                                seed=5)
    c = locate_carrier(Hn, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    return g, Hn, c, nov


def test_none_correction_requires_a_declared_object_visibility():
    g, Hn, c, _ = _object_hologram(0.3)
    with pytest.raises(ValueError, match="object_min_visibility"):
        reconstruct_sideband(Hn, carrier=c, mask=MaskSpec(0.125 / 3, "disc", "none"),
                             empty_hologram=None, reference_correction="none", unwrapping="none")


@pytest.mark.parametrize("frac", [0.8, 0.45, 0.3])
def test_fringe_free_area_is_invalid_without_an_empty_hologram(frac):
    """The auditor's case (30 % overlap: 8448 of 8448 outside pixels VALID). Declared minimum 0.3
    (TEST_ONLY), as the N6 test: the outside visibility is noise (about 0.013), the inside 1."""
    g, Hn, c, nov = _object_hologram(frac)
    with pytest.warns(RuntimeWarning, match="visibility"):
        r = reconstruct_sideband(Hn, carrier=c, mask=MaskSpec(0.125 / 3, "disc", "none"),
                                 empty_hologram=None, reference_correction="none",
                                 unwrapping="none", object_min_visibility=0.3)
    inside = np.zeros(g.shape, bool)
    inside[12:nov - 12, :] = True
    outside = np.zeros(g.shape, bool)
    outside[nov + 12:N - 12, :] = True
    assert r.valid_mask[inside].all()
    assert not r.valid_mask[outside].any(), int(r.valid_mask[outside].sum())
    assert np.all(np.isnan(r.wrapped_phase[outside]))
    err = np.abs(wrap_to_pi(r.wrapped_phase[inside] - 0.3))
    # one noisy hologram (no division): sqrt(2)/(mu sqrt(N)) per SM12, 3 sigma
    assert float(np.sqrt(np.mean(err ** 2))) <= 3 * math.sqrt(2) / math.sqrt(
        100.0 / (math.pi * (0.125 / 3) ** 2))
    assert r.parameters["validity"]["object_min_visibility"] == 0.3


def test_object_visibility_is_refused_with_divide_empty():
    g, Hn, c, _ = _object_hologram(0.8)
    with pytest.raises(ValueError, match="object_min_visibility"):
        reconstruct_sideband(Hn, carrier=c, mask=MaskSpec(0.04, "disc", "none"),
                             empty_hologram=Hn, reference_correction="divide_empty",
                             unwrapping="none", empty_min_visibility=0.5,
                             object_min_visibility=0.5)
