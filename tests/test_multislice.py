"""Propagation identities of the multislice kernel."""
import numpy as np
import pytest

from reflection_holo.beams import kz_minus_k
from reflection_holo.constants import k_rad_per_A, wavelength_A
from reflection_holo.grid import Grid
from reflection_holo.multislice import Propagator, propagate, run_multislice

LAM = float(wavelength_A(200.0))
K = float(k_rad_per_A(200.0))


def _grid():
    return Grid(512, 8, 51.2, 0.8, x0=-20.0)


def test_tilted_plane_wave_phase_advance():
    g = _grid()
    n = 37
    q0 = n / g.Lx
    psi0 = np.exp(2j * np.pi * q0 * g.x)[:, None] * np.ones((1, g.Ny))
    planes = np.arange(1, 501) * 1.92
    prop = Propagator(g, LAM, np, np.complex128)
    ex, rec, zs, _, _ = run_multislice(psi0[None], planes, lambda i: np.ones((g.Nx, g.Ny)),
                                       [planes[-1] + 0.5], prop, np, record_rows=[[100, 104]])
    assert zs[0] == planes[-1]          # planes exhausted: stops at the last plane
    expected = psi0 * np.exp(1j * kz_minus_k(q0**2, LAM) * planes[-1])
    assert np.max(np.abs(ex[0] - expected)) < 1e-10
    # detector record on row 100 at every plane
    rec_expected = (np.exp(2j * np.pi * q0 * g.x[100])
                    * np.exp(1j * kz_minus_k(q0**2, LAM) * planes))
    assert np.max(np.abs(rec[0, 0, :, 0] - rec_expected)) < 1e-10


def test_norm_conservation_and_inverse_propagation():
    g = _grid()
    rng = np.random.default_rng(0)
    psi = rng.normal(size=(g.Nx, g.Ny)) + 1j * rng.normal(size=(g.Nx, g.Ny))
    psi = np.fft.ifft2(np.fft.fft2(psi) * g.band)
    prop = Propagator(g, LAM, np, np.complex128)
    out = propagate(psi[None], prop(250.0), np)[0]
    assert np.linalg.norm(out) == pytest.approx(np.linalg.norm(psi), rel=1e-12)
    back = propagate(out[None], prop(-250.0), np)[0]
    assert np.max(np.abs(back - psi)) < 1e-10 * np.abs(psi).max()
    # a real phase grating conserves the norm
    t = np.exp(1j * rng.normal(size=(g.Nx, g.Ny)))
    assert np.linalg.norm(t * out) == pytest.approx(np.linalg.norm(out), rel=1e-12)


def test_fresnel_versus_exact_error():
    # paraxial error k dz sin^4(alpha)/8: 0.026 rad at 45 mrad over 198 A (docs/03 s.5)
    s = np.sin(0.045)
    q2 = (s / LAM) ** 2
    exact = kz_minus_k(q2, LAM) * 198.0
    fresnel = -np.pi * LAM * q2 * 198.0
    assert exact - fresnel == pytest.approx(-K * 198.0 * s**4 / 8, rel=2e-3)
    assert abs(exact - fresnel) == pytest.approx(0.0254, abs=5e-4)


def test_exit_order_with_unsorted_exits():
    g = _grid()
    q = np.array([5, 11, 17]) / g.Lx
    psi0 = np.stack([np.exp(2j * np.pi * qi * g.x)[:, None] * np.ones((1, g.Ny)) for qi in q])
    planes = np.arange(1, 101) * 2.0
    ze = [150.0, 60.5, 199.0]
    prop = Propagator(g, LAM, np, np.complex128)
    ex, _, zs, _, _ = run_multislice(psi0, planes, lambda i: np.ones((g.Nx, g.Ny)), ze, prop, np)
    # each element stops at the first plane at or beyond its exit position
    assert list(zs) == [150.0, 62.0, 200.0]
    for b in range(3):
        expected = psi0[b] * np.exp(1j * kz_minus_k(q[b] ** 2, LAM) * zs[b])
        assert np.max(np.abs(ex[b] - expected)) < 1e-10


def test_adaptive_stop_on_decayed_record():
    # a record that vanishes after the wave is removed by an absorbing plane: the
    # element stops at the first check after z_min once the tail is below tolerance
    g = _grid()
    psi0 = np.exp(2j * np.pi * (5 / g.Lx) * g.x)[:, None] * np.ones((1, g.Ny))
    planes = np.arange(1, 2001) * 2.0
    kill = np.zeros((g.Nx, g.Ny))
    prop = Propagator(g, LAM, np, np.complex128)
    trans = lambda i: np.ones((g.Nx, g.Ny)) if i < 300 else kill  # noqa: E731
    ex, rec, zs, _, _ = run_multislice(psi0[None], planes, trans, [4000.0], prop, np,
                                       record_rows=[[10, 12]], z_min=[1000.0], tail_tol=1e-4,
                                       tail_window=100, check_every=50)
    assert zs[0] == 1000.0
