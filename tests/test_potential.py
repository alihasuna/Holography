"""Projected potential normalisation against the analytic Kirkland projection."""
import numpy as np
import pytest

from reflection_holo.constants import TWO_PI_A0_E_V_A2
from reflection_holo.grid import Grid
from reflection_holo.potential import (PotentialBuilder,
                                       mean_inner_potential, scattering_factor)


def test_two_pi_a0_e():
    assert TWO_PI_A0_E_V_A2 == pytest.approx(47.8776, abs=2e-4)


def test_mean_inner_potential_of_parametrisations():
    assert scattering_factor(0.0, "kirkland") == pytest.approx(5.81428, abs=1e-5)
    assert mean_inner_potential("kirkland", 5.4309) == pytest.approx(13.903, abs=1e-3)
    assert mean_inner_potential("lobato", 5.4309) == pytest.approx(13.955, abs=1e-3)


def test_projected_potential_normalisation(monkeypatch):
    """Real-space values against the analytic projection for a smooth (Gaussian-only)
    parameter set, for which the band limit is irrelevant: tests the 2 pi a0 e
    prefactor and the Fourier conventions (the Kirkland core terms have a slowly
    decaying 1/q^2 tail, so their band-limited real-space form rings and cannot be
    compared pointwise)."""
    import reflection_holo.potential as P
    gauss = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [1.0, 0.5, 0.2], [0.5, 1.0, 2.0]])
    monkeypatch.setattr(P, "load_parameters", lambda name: gauss)
    N, L = 256, 16.0
    g = Grid(N, N, L, L, x0=0.0)
    pb = P.PotentialBuilder(g, np, 200.0, parametrization="kirkland", dtype="complex128")
    v = pb.projected(np.array([8.0]), np.array([8.0 + 0.0137]))
    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    r = np.hypot(X - 8.0, Y - 8.0137)
    a, b, c, d = gauss
    ref = TWO_PI_A0_E_V_A2 * sum(np.pi * c[i] / d[i] * np.exp(-np.pi**2 * r**2 / d[i])
                                 for i in range(3))
    # residual: band-limit tail of the narrowest Gaussian, exp(-0.5 q_band^2) ~ 7e-7
    assert np.max(np.abs(v - ref)) < 2e-6 * ref.max()


def test_projected_potential_integral():
    g = Grid(128, 128, 12.0, 12.0, x0=0.0)
    pb = PotentialBuilder(g, np, 200.0, parametrization="kirkland", dtype="complex128")
    v = pb.projected(np.array([6.0]), np.array([6.0]))
    assert v.sum() * g.dx * g.dy == pytest.approx(TWO_PI_A0_E_V_A2 * scattering_factor(0.0),
                                                  rel=1e-10)


def test_subpixel_translation_is_exact():
    # shifting an atom by a non-integer number of pixels shifts the band-limited
    # potential exactly (phase ramp), so the Fourier coefficients have equal moduli
    g = Grid(64, 64, 10.0, 10.0, x0=0.0)
    pb = PotentialBuilder(g, np, 200.0, dtype="complex128")
    v1 = pb.projected(np.array([3.0]), np.array([4.0]))
    v2 = pb.projected(np.array([3.0 + 0.0371]), np.array([4.0 - 0.0213]))
    F1, F2 = np.fft.fft2(v1), np.fft.fft2(v2)
    assert np.allclose(np.abs(F1), np.abs(F2), atol=1e-9 * np.abs(F1).max())
    ramp = np.exp(-2j * np.pi * (g.qx[:, None] * 0.0371 - g.qy[None, :] * 0.0213))
    assert np.allclose(F2, F1 * ramp, atol=1e-9 * np.abs(F1).max())
