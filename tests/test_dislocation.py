"""Buried dislocation in an isotropic half-space: the elastic solution is checked, not assumed."""

import numpy as np
import pytest

from reflection_holo.defects.dislocation import BuriedDislocation, from_config
from reflection_holo.geometry import SI111_FRAME

NU = 0.22
LAM = 2 * NU / (1 - 2 * NU)  # Lame lambda with mu = 1

CASES = [[0, 3.0, 0], [0, 0, 3.0], [3.0, 0, 0], [0, 2.0, 1.5]]  # slab frame, line along z


def _stress(D, s, h, e=1e-4):
    u = lambda s_, h_: np.array(D.displacement_local(s_, h_))  # noqa: E731
    dus = (u(s + e, h) - u(s - e, h)) / (2 * e)
    duh = (u(s, h + e) - u(s, h - e)) / (2 * e)
    tr = dus[0] + duh[1]
    return (LAM * tr + 2 * dus[0], LAM * tr + 2 * duh[1], duh[0] + dus[1], dus[2], duh[2])


@pytest.mark.parametrize("b", CASES)
def test_surface_is_traction_free(b):
    D = BuriedDislocation(burgers=b, line=[0, 0, 1], depth=20.0, offset=5.0, nu=NU)
    s = np.linspace(-200, 200, 41)
    _, s_hh, s_sh, _, s_23 = _stress(D, s, np.full_like(s, -1e-4))
    scale = np.abs(np.array(_stress(D, s, np.full_like(s, -40.0)))).max()
    assert np.abs(s_hh).max() < 1e-5 * scale + 1e-12
    assert np.abs(s_sh).max() < 1e-4 * scale + 1e-12
    assert np.abs(s_23).max() < 1e-4 * scale + 1e-12


@pytest.mark.parametrize("b", CASES)
def test_burgers_circuit_closes_to_b(b):
    D = BuriedDislocation(burgers=b, line=[0, 0, 1], depth=20.0, offset=5.0, nu=NU)
    t = np.linspace(0, 2 * np.pi, 40001)
    U = np.array(D.displacement_local(5.0 + 4.0 * np.cos(t), -20.0 + 4.0 * np.sin(t)))
    dU = np.diff(U, axis=1)
    cut = np.abs(dU).max(axis=0) > 0.5  # the one step across the Volterra cut
    assert cut.sum() == 1
    np.testing.assert_allclose(dU[:, ~cut].sum(axis=1), D.b_local, atol=2e-3)


@pytest.mark.parametrize("b", CASES)
def test_bulk_equilibrium(b):
    D = BuriedDislocation(burgers=b, line=[0, 0, 1], depth=20.0, offset=5.0, nu=NU)
    s0, h0, E = -13.0, -7.0, 1e-2
    st = lambda s, h: np.array(_stress(D, np.array([s]), np.array([h]))).ravel()  # noqa: E731
    ds = (st(s0 + E, h0) - st(s0 - E, h0)) / (2 * E)
    dh = (st(s0, h0 + E) - st(s0, h0 - E)) / (2 * E)
    scale = np.abs(st(s0, h0)).max()
    assert abs(ds[0] + dh[2]) < 1e-5 * scale
    assert abs(ds[2] + dh[1]) < 1e-5 * scale
    assert abs(ds[3] + dh[4]) < 1e-5 * scale


@pytest.mark.parametrize("nu", [0.0, 0.22, 0.45])
def test_surface_relief_closed_form_independent_of_nu(nu):
    d, b1, b2, b3 = 20.0, 3.0, 1.2, 1.9
    D = BuriedDislocation(burgers=[b2, -b1, b3], line=[0, 0, 1], depth=d, offset=0.0, nu=nu)  # e1 = -y
    np.testing.assert_allclose(D.b_local, [b1, b2, b3], atol=1e-12)
    s = np.linspace(-150, 150, 61)
    u1, u2, u3 = D.displacement_local(s, np.zeros_like(s))
    r2 = s**2 + d**2
    u2_ref = b1 / np.pi * d**2 / r2 - b1 / (2 * np.pi) + b2 / np.pi * (np.arctan2(d, s) - s * d / r2)
    u3_ref = b3 / np.pi * np.arctan2(d, s)
    np.testing.assert_allclose(u2, u2_ref, atol=1e-10)
    np.testing.assert_allclose(u3, u3_ref, atol=1e-10)


def test_partial_burgers_vector_refused():
    entries = [{"burgers_over_a": [1 / 6, -1 / 6, -1 / 3], "line_uvw": [1, 1, 0], "depth_A": 20,
                "position_yz_A": [0, 0], "sign": 1}]
    with pytest.raises(ValueError, match="not a lattice vector"):
        from_config(entries, 0.22, 5.4309, SI111_FRAME)


def test_from_config_places_line_at_requested_y():
    entries = [{"burgers_over_a": [0, 0.5, 0.5], "line_uvw": [1, 1, 0], "depth_A": 20,
                "position_yz_A": [37.0, 0], "sign": 1}]
    D = from_config(entries, 0.22, 5.4309, SI111_FRAME).items[0]
    y = np.linspace(-100, 200, 3001)
    ux = D.displacement(np.stack([0 * y, y, 0 * y], -1))[:, 0]
    assert y[np.argmax(np.abs(ux - ux[0]))] == pytest.approx(37.0, abs=0.2)  # bump centred on the line


def test_line_must_be_parallel_to_surface():
    with pytest.raises(ValueError):
        BuriedDislocation(burgers=[0, 1, 0], line=[1, 0, 1], depth=10.0, offset=0.0, nu=NU)
