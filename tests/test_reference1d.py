"""One-dimensional reflection references (Parratt and transfer matrix)."""
import numpy as np
import pytest

from reflection_holo.constants import interaction_constant, k_rad_per_A
from reflection_holo.reference1d import (fermi_step_R, layers_from_profile, parratt,
                                         transfer_matrix)

K = float(k_rad_per_A(200.0))
SIG = interaction_constant(200.0)


def test_parratt_equals_transfer_matrix_on_random_stacks():
    rng = np.random.default_rng(3)
    Kx = 2 * np.pi * np.linspace(0.2, 1.6, 9)
    for model in ("schroedinger", "multislice"):
        V = np.concatenate([[0.0], rng.uniform(-5, 25, 12) + 1j * rng.uniform(0, 2, 12),
                            [14.0 + 1.0j]])
        d = rng.uniform(0.1, 2.0, 12)
        r1 = parratt(Kx, K, SIG, V, d, x_top=0.0, x_ref=0.7, model=model)
        r2, _, _ = transfer_matrix(Kx, K, SIG, V, d, x_top=0.0, x_ref=0.7, model=model)
        assert np.max(np.abs(r1 - r2)) < 1e-10


def test_single_interface_is_fresnel():
    Kx = 2 * np.pi * np.array([0.3, 0.9])
    r = parratt(Kx, K, SIG, np.array([0.0, 14.0]), np.array([]), x_top=0.0, x_ref=0.0)
    K1 = np.sqrt(Kx**2 + 2 * K * SIG * 14.0)
    assert np.allclose(r, (Kx - K1) / (Kx + K1), atol=1e-14)


def test_flux_conservation_without_absorption():
    rng = np.random.default_rng(5)
    Kx = 2 * np.pi * np.linspace(0.3, 1.2, 7)
    V = np.concatenate([[0.0], rng.uniform(0, 25, 8), [14.0]])
    d = rng.uniform(0.2, 1.5, 8)
    r, t, Kl = transfer_matrix(Kx, K, SIG, V, d, x_top=0.0, x_ref=0.0)
    flux = np.abs(r) ** 2 + (Kl[:, -1].real / Kl[:, 0].real) * np.abs(t) ** 2
    assert np.allclose(flux, 1.0, atol=1e-12)


def test_fermi_step_closed_form():
    a = 0.3
    x = np.arange(-40.0, 40.0, 0.004)
    V = 14.0 / (1 + np.exp(np.clip(x / a, -60, 60)))
    V[x > 30] = 0.0
    Vl, d, xb = layers_from_profile(x, V, x_top=30.0)
    Kx = 2 * np.pi * np.array([0.2, 0.5, 0.8])
    r = parratt(Kx, K, SIG, Vl, d, x_top=xb, x_ref=0.0)
    K2 = np.sqrt(Kx**2 + 2 * K * SIG * 14.0)
    assert np.allclose(np.abs(r) ** 2, fermi_step_R(Kx, K2, a), rtol=2e-3)
