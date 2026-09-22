"""Silent acceptances in the hologram chain (audit A2 finding m7; scratch script e9).

* ensemble pairing was enforced only when realisation indices were set: two mis-paired
  (object, reference) pairs with realisation=None were averaged;
* reconstruct_sideband accepted a carrier located on an OBJECT hologram (the brightest-bin trap);
* R3 is a vacuum-type reference but had no aperture_passage declaration (docs/05 5.3).
Grid 64 x 64, pixel 1 A, carrier (0, 1/8) cycles/A (TEST_ONLY).
"""
import numpy as np
import pytest

from reflection_holo.optics import (APERTURE_PASSAGES, ArtefactOptions, Grid, Wave,
                                    ensemble_hologram_intensity, hologram_intensity,
                                    reference_r1_vacuum_plane_wave, reference_r3_curved_tilted)
from reflection_holo.reconstruction import CarrierSearch, MaskSpec, locate_carrier, reconstruct_sideband

NA = ArtefactOptions(None, None, None)


def grid():
    return Grid(shape=(64, 64), pixel_size_A=(1.0, 1.0), axes=("y", "x"),
                plane="image plane (TEST_ONLY audit m7)")


def r1(g, phase, realisation):
    return reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.0, 0.125), amplitude=1.0,
                                          relative_phase_rad=phase, aperture_passage="no_aperture",
                                          realisation=realisation)


def test_ensemble_of_several_pairs_needs_realisation_indices():
    g = grid()
    o = [Wave(np.full(g.shape, np.exp(1j * p)), g, f"obj{p}", None) for p in (0.0, 1.0)]
    r = [r1(g, p, None) for p in (0.0, 1.0)]
    with pytest.raises(ValueError, match="realisation ind"):
        ensemble_hologram_intensity([(o[0], r[1]), (o[1], r[0])], artefacts=NA, content="object")
    H = ensemble_hologram_intensity([(o[0], r[0])], artefacts=NA, content="object")   # one pair
    assert H.metadata["n_realisations"] == 1
    oi = [Wave(np.full(g.shape, np.exp(1j * p)), g, f"obj{p}", k) for k, p in enumerate((0.0, 1.0))]
    ri = [r1(g, p, k) for k, p in enumerate((0.0, 1.0))]
    assert ensemble_hologram_intensity(list(zip(oi, ri)), artefacts=NA,
                                       content="object").metadata["n_realisations"] == 2


def test_trap_carrier_refused_without_explicit_opt_in():
    g = grid()
    step = np.exp(1j * 2.0 * (np.arange(64)[:, None] >= 32) * np.ones((1, 64)))
    Hobj = hologram_intensity(Wave(step, g, "step", None), r1(g, 0.0, None), artefacts=NA,
                              content="object")
    search = CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", "TEST_ONLY: -q_ref")
    trap = locate_carrier(Hobj, search, allow_object_hologram=True)
    kw = dict(carrier=trap, mask=MaskSpec(0.04, "disc", "hann"), empty_hologram=None,
              reference_correction="none", unwrapping="none")
    with pytest.raises(ValueError, match="OBJECT hologram"):
        reconstruct_sideband(Hobj, **kw)
    res = reconstruct_sideband(Hobj, **kw, trap_demonstration=True)
    assert res.parameters["trap_demonstration"] is True


def test_r3_declares_its_aperture_passage():
    g = grid()
    kw = dict(carrier_cycles_per_A=(0.0, 0.125), amplitude=1.0, relative_phase_rad=0.0,
              residual_tilt_cycles_per_A=(0.0, 0.0), residual_curvature_rad_per_A2=(0.0, 0.0, 0.0),
              curvature_centre_A=(32.0, 32.0), realisation=None)
    with pytest.raises(TypeError, match="aperture_passage"):
        reference_r3_curved_tilted(g, **kw)
    with pytest.raises(ValueError, match="aperture_passage"):
        reference_r3_curved_tilted(g, **kw, aperture_passage="unspecified")
    for ap in APERTURE_PASSAGES:
        u = reference_r3_curved_tilted(g, **kw, aperture_passage=ap)
        assert u.metadata["aperture_passage"] == ap
