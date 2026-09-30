"""Geometric-phase model and geometry core."""

import numpy as np
import pytest

from reflection_holo import geometry as geo
from reflection_holo.crystal import build_slab
from reflection_holo.defects.dislocation import BuriedDislocation
from reflection_holo.forward import geometric as gm

COND = geo.SpecularCondition(200, 12.0, 5.4309, (4, -4, 4))


def test_specular_angles_match_reference_calculator():
    # docs/03_physics_summary.md section 3 table (tools/reflection_step_phase_calculator.py)
    assert COND.theta_int * 1e3 == pytest.approx(16.00, abs=0.005)
    assert COND.theta_ext * 1e3 == pytest.approx(13.64, abs=0.005)
    assert 2 * np.pi / COND.q_ext == pytest.approx(0.919, abs=0.001)  # h_2pi
    assert geo.wavelength_A(200) == pytest.approx(0.02507934, rel=1e-7)


def test_forbidden_reflection_refused():
    with pytest.raises(ValueError, match="forbidden"):
        geo.SpecularCondition(200, 12.0, 5.4309, (6, -6, 6))


@pytest.mark.parametrize("pen", [2.0, 10.0, 50.0])
@pytest.mark.parametrize("h", [3.1355, 0.5, -1.7])
def test_rigid_translation_gives_minus_q_ext_dot_R(pen, h):
    depths = COND.d_A * np.arange(40)
    R = np.array([h, 0.7, -0.3])
    u = np.broadcast_to(R, (40, 1, 3))
    G, qi, qe = gm.specular_vectors(COND)
    phi0, _ = gm.column_phase(np.zeros((40, 1, 3)), depths, G, qi, qe, pen)
    phi, _ = gm.column_phase(u, depths, G, qi, qe, pen)
    expected = gm.rigid_step_phase(COND, R)
    assert np.angle(np.exp(1j * (phi[0] - phi0[0] - expected))) == pytest.approx(0.0, abs=1e-10)


def _profile(b, depth=25.0, pen=8.0):
    D = BuriedDislocation(burgers=b, line=[0, 0, 1], depth=depth, offset=0.0, nu=0.22)
    y = np.linspace(-150, 150, 301)
    depths = COND.d_A * np.arange(60)
    r = np.stack(np.broadcast_arrays(-depths[:, None], y[None, :], 0.0 * y[None, :]), axis=-1)
    u = D.displacement(r)
    G, qi, qe = gm.specular_vectors(COND)
    return gm.column_phase(u, depths, G, qi, qe, pen)


def test_pure_screw_parallel_to_surface_is_invisible_in_specular():
    phi, amp = _profile([0, 0, 3.84])
    assert np.ptp(phi) < 1e-12 and np.ptp(amp) < 1e-12


def test_sign_of_burgers_vector_reverses_phase():
    b = np.array([0, -3.3257, 1.9201])
    p1, _ = _profile(b)
    p2, _ = _profile(-b)
    p1 = np.unwrap(p1) - np.unwrap(p1)[0]
    p2 = np.unwrap(p2) - np.unwrap(p2)[0]
    np.testing.assert_allclose(p1, -p2, atol=1e-9)


def test_buried_relief_phase_is_depth_independent_in_amplitude():
    # surface bump height b1/pi does not depend on depth, only its width (2d FWHM)
    b = np.array([0, -3.3257, 0.0])
    ptp = [np.ptp(np.unwrap(_profile(b, depth=d, pen=3.0)[0])) for d in (15.0, 30.0)]
    assert ptp[0] > 5.0
    assert ptp[1] == pytest.approx(ptp[0], rel=0.08)


def test_deformed_coordinates_identity():
    y = np.linspace(0, 100, 200, endpoint=False)
    f = np.exp(1j * np.sin(2 * np.pi * y / 100))
    np.testing.assert_allclose(gm.to_deformed_coordinates(f, y, 0 * y, 100.0), f, atol=1e-12)


def test_slab_density_and_bilayer_termination():
    pos, Ly, Lz = build_slab(geo.SI111_FRAME, 5.4309, 3, 20.0)
    d = 5.4309 / np.sqrt(3)
    levels = np.unique(np.round(pos[:, 0], 4))[::-1]
    assert levels[0] == pytest.approx(0.0, abs=1e-6)
    assert levels[0] - levels[1] == pytest.approx(d / 4, abs=1e-4)  # top bilayer intact
    assert levels[1] - levels[2] == pytest.approx(3 * d / 4, abs=1e-4)
    n_bilayers = int(np.floor(20.0 / d)) + 1
    assert len(pos) == 4 * n_bilayers * 3  # 4 atoms per bilayer per 6.651 x 3.840 A rectangle
    assert Lz == pytest.approx(5.4309 / np.sqrt(2), rel=1e-12)


def test_specular_at_angle_matches_bragg_condition():
    c = geo.SpecularAtAngle(200, 12.0, 5.4309, (4, -4, 4), COND.theta_ext)
    assert c.theta_int == pytest.approx(COND.theta_int, rel=1e-9)
    assert c.q_int == pytest.approx(COND.G, rel=1e-9)  # internal Bragg condition: q_int = G
    assert c.q_ext == pytest.approx(COND.q_ext, rel=1e-12)
