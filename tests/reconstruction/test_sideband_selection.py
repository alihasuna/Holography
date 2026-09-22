"""Sideband selection is declared and protected (audit A2 finding M1; model_assumptions B15).

The auditor's case (A2 M1, scratch script e4): flat object phase 0.7 rad, R1 reference relative phase
0.2 rad, so phi_o - phi_r = +0.5 rad; Poisson dose 1e3 e/px, seed 3; 128 x 128 grid, pixel 1 A
(TEST_ONLY); the declared guess is always the correct phi_o - phi_r sideband (-q_ref). With a search
disc that contains both Hermitian partners (radius 0.3 or inf cycles/A for |q_ref| = 0.125 or 0.14),
the unfixed locate_carrier picked the conjugate by array order for three of five directions and
returned -0.500 rad. Now any search region that is not confined to one side of a line through the
origin (disc radius >= |guess|), or that holds a Hermitian pair on the grid (Nyquist aliasing), is
refused, and the sideband must be declared with its evidence.

Tolerance for the recovered phase: the median over the field of the wrapped phase must equal
+0.500 rad within T25's 5e-3 rad (tests/reconstruction/holo_cases.py).
"""
import numpy as np
import pytest

from holo_cases import NO_ARTEFACTS, T25_TOL_RAD
from reflection_holo.optics import (Grid, Hologram, Wave, apply_poisson_noise, hologram_intensity,
                                    reference_r1_vacuum_plane_wave, vacuum_object_wave)
from reflection_holo.reconstruction import CarrierSearch, MaskSpec, locate_carrier, reconstruct_sideband

N = 128
DECL = "TEST_ONLY: -q_ref of the simulated R1 reference (phi_o - phi_r sideband)"
# all four quadrants, both axes (the auditor's five directions plus their partners)
Q_REFS = [(0.0, 0.125), (0.0, -0.125), (0.125, 0.0), (-0.125, 0.0), (0.0625, -0.125),
          (-0.0625, 0.125), (0.0625, 0.125), (-0.0625, -0.125)]


def grid():
    return Grid(shape=(N, N), pixel_size_A=(1.0, 1.0), axes=("y", "x"),
                plane="image plane (TEST_ONLY audit M1 case)")


def holograms(q_ref):
    g = grid()
    u_o = Wave(np.full(g.shape, np.exp(0.7j)), g, "flat", None)
    u_r = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=q_ref, amplitude=1.0,
                                         relative_phase_rad=0.2, aperture_passage="no_aperture",
                                         realisation=None)
    H = hologram_intensity(u_o, u_r, artefacts=NO_ARTEFACTS, content="object")
    E = hologram_intensity(vacuum_object_wave(g, amplitude=1.0, realisation=None), u_r,
                           artefacts=NO_ARTEFACTS, content="empty")
    H, E = apply_poisson_noise([H, E], dose_e_per_px=1e3, seed=3)
    # the same data as an experimental record: no reference carrier in the metadata
    Hx = Hologram(H.intensity, g, "object", {"source": "experiment-like"}, None)
    Ex = Hologram(E.intensity, g, "empty", {"source": "experiment-like"}, None)
    return H, E, Hx, Ex


@pytest.mark.parametrize("q_ref", Q_REFS)
@pytest.mark.parametrize("radius", [0.3, np.inf, 0.125, 0.2])
def test_search_region_containing_both_sidebands_is_refused(q_ref, radius):
    """The auditor's radii 0.3 and inf, and the boundary radius = |guess| (the disc touches q = 0),
    are refused whatever the carrier direction."""
    guess = (-q_ref[0], -q_ref[1])
    r = radius if radius != 0.125 else float(np.hypot(*guess))
    with pytest.raises(ValueError, match="one side of a line through the origin"):
        CarrierSearch(sideband_guess_cycles_per_A=guess, search_radius_cycles_per_A=r,
                      exclusion_radius_cycles_per_A=0.03, subpixel="none", sideband_declaration=DECL)


@pytest.mark.parametrize("q_ref", Q_REFS)
def test_half_plane_search_returns_phi_o_minus_phi_r(q_ref):
    """Radius 0.06 < |guess|: the declared sideband is found for every direction, on simulated and
    on experiment-like records, and the phase is +0.500 rad."""
    H, E, Hx, Ex = holograms(q_ref)
    guess = (-q_ref[0], -q_ref[1])
    search = CarrierSearch(guess, 0.06, 0.03, "none", DECL)
    mask = MaskSpec(0.125 / 3, "disc", "hann")
    for obj, emp in ((H, E), (Hx, Ex)):
        c = locate_carrier(emp, search)
        assert np.allclose(c.sideband_centre_cycles_per_A, guess, atol=1e-12)
        res = reconstruct_sideband(obj, carrier=c, mask=mask, empty_hologram=None,
                                   reference_correction="none", unwrapping="none")
        assert abs(np.median(res.wrapped_phase) - 0.5) <= T25_TOL_RAD
        assert res.parameters["sideband_declaration"] == DECL
    assert res.sideband_sign_check.startswith("unknown")


def test_hermitian_pair_through_nyquist_aliasing_is_refused():
    """A disc confined to one side of the origin can still hold a Hermitian pair on the grid: the
    bins (-Nyquist, +q1) and (-Nyquist, -q1) are partners because -(-Nyquist) aliases to -Nyquist."""
    _, E, _, _ = holograms((0.0, 0.125))
    search = CarrierSearch((-0.45, 0.0), 0.1, 0.03, "none", DECL)      # 0.1 < |guess| = 0.45
    with pytest.raises(ValueError, match="Hermitian partner"):
        locate_carrier(E, search)


def test_sideband_must_be_declared_explicitly():
    with pytest.raises(TypeError):
        CarrierSearch((0.0, -0.125), 0.06, 0.03, "none")                   # no declaration
    for bad in ("", "   ", None):
        with pytest.raises(ValueError, match="declar"):
            CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", bad)
    with pytest.raises(ValueError, match="non-zero"):
        CarrierSearch((0.0, 0.0), 0.06, 0.03, "none", DECL)               # no sideband named


def test_conjugate_sideband_on_a_simulated_hologram_raises():
    """Declaring +q_ref (the conjugate) on a simulated hologram is detected from the recorded
    reference carrier and refused; only an explicit trap demonstration may proceed."""
    q_ref = (0.0, 0.125)
    H, E, _, _ = holograms(q_ref)
    c = locate_carrier(E, CarrierSearch(q_ref, 0.06, 0.03, "none", "TEST_ONLY: conjugate on purpose"))
    mask = MaskSpec(0.125 / 3, "disc", "hann")
    with pytest.raises(ValueError, match="CONJUGATE"):
        reconstruct_sideband(H, carrier=c, mask=mask, empty_hologram=None,
                             reference_correction="none", unwrapping="none")
    res = reconstruct_sideband(H, carrier=c, mask=mask, empty_hologram=None,
                               reference_correction="none", unwrapping="none",
                               trap_demonstration=True)
    assert res.sideband_sign_check.startswith("CONJUGATE")
    assert abs(np.median(res.wrapped_phase) + 0.5) <= T25_TOL_RAD
