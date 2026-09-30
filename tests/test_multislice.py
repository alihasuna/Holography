"""Multislice kernel: propagation, tilt sign, potential normalisation (no validation claims)."""

import numpy as np
import pytest

from reflection_holo import geometry as geo
from reflection_holo.crystal import build_slab
from reflection_holo.forward import multislice as ms
from reflection_holo.provenance import Config

LAM = geo.wavelength_A(200)


def test_interaction_constant_200keV():
    assert geo.interaction_constant(200) == pytest.approx(7.2884e-4, rel=2e-4)


def test_vacuum_plane_wave_phase_advance_and_norm():
    g = ms.Grid(nx=256, ny=64, dx=0.1, dy=0.2, x0=0.0)
    theta = 0.0134
    q0 = np.round(np.sin(theta) / LAM * g.nx * g.dx) / (g.nx * g.dx)  # on a grid frequency
    psi0 = np.exp(-2j * np.pi * q0 * g.x)[:, None] * np.ones((1, g.ny))
    P = ms.propagator(g, 1.92, LAM)
    t = [np.ones((g.nx, g.ny), np.complex64)]
    psi = ms.run(psi0, t, P, 100)
    kz = np.sqrt(1 / LAM**2 - q0**2)
    expected = psi0 * np.exp(2j * np.pi * 1.92 * 100 * (kz - 1 / LAM))
    np.testing.assert_allclose(psi, expected, atol=5e-4)
    assert np.sum(np.abs(psi) ** 2) == pytest.approx(np.sum(np.abs(psi0) ** 2), rel=1e-4)


def test_sheet_beam_descends_towards_the_surface():
    g = ms.Grid(nx=1024, ny=8, dx=0.1, dy=0.5, x0=-50.0)
    theta = 0.0132
    psi0 = ms.illumination(g, theta, LAM, x_center=30.0, height=10.0, edge=3.0)
    P = ms.propagator(g, 1.92, LAM)
    n = 500
    psi = ms.run(psi0, [np.ones((g.nx, g.ny), np.complex64)], P, n)
    I = np.abs(psi[:, 0]) ** 2
    xc = np.sum(g.x * I) / I.sum()
    assert xc == pytest.approx(30.0 - n * 1.92 * np.tan(theta), abs=0.3)


def test_band_assertion():
    g = ms.Grid(nx=64, ny=64, dx=0.5, dy=0.5, x0=0.0)
    with pytest.raises(ValueError, match="outside 2/3 band"):
        g.assert_angle_in_band(0.024, LAM)  # 0.5 A pixel cannot carry 24 mrad (check T22)


def test_potential_mean_equals_parameterisation_mip():
    a = 5.4309
    pos, Ly, Lz = build_slab(geo.SI111_FRAME, a, 4, 40.0)
    g = ms.Grid(nx=512, ny=128, dx=0.1, dy=Ly / 128, x0=-48.0)
    V, dz = ms.slice_potentials(pos, Lz, 2, g, 0.46, 0.0)
    d = a / np.sqrt(3)
    sel = (g.x < -3) & (g.x >= -3 - 8 * d)
    V0 = sum(v.real[sel].mean() for v in V) / Lz
    assert V0 == pytest.approx(ms.mean_inner_potential(8 / a**3), rel=0.01)
    assert ms.mean_inner_potential(8 / a**3) == pytest.approx(13.91, abs=0.01)


def test_config_refuses_unlabelled_or_missing(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("a: {value: 1, label: ASSUMPTION}\nb: 3\nc: {value: 2, label: GUESS}\n")
    c = Config(p)
    assert c.get("a") == 1
    with pytest.raises(ValueError):
        c.get("b")
    with pytest.raises(ValueError):
        c.get("c")
    with pytest.raises(KeyError):
        c.get("d")


def test_cupy_backend_matches_numpy():
    """Run on the GPU machine first: the cupy path must reproduce the numpy path."""
    pytest.importorskip("cupy")
    a = 5.4309
    pos, Ly, Lz = build_slab(geo.SI111_FRAME, a, 4, 20.0)
    g = ms.Grid(nx=256, ny=64, dx=0.1, dy=Ly / 64, x0=-24.0)
    out = {}
    for backend in ("numpy", "cupy"):
        xp = ms.get_xp(backend)
        V, dz = ms.slice_potentials(pos, Lz, 2, g, 0.46, 0.05, xp=xp)
        band = xp.asarray(g.band_mask())
        absorber = ms.absorber_profile(g, -14.0, 8.0, 60.0)
        t = [ms.transmission(v, geo.interaction_constant(200), absorber, dz, band, xp=xp) for v in V]
        P = ms.propagator(g, dz, LAM, xp=xp)
        psi0 = ms.illumination(g, 0.0132, LAM, 8.0, 6.0, 2.0)
        out[backend] = ms.to_numpy(ms.run(psi0, t, P, 300, xp=xp))
    np.testing.assert_allclose(out["cupy"], out["numpy"], atol=2e-3 * np.abs(out["numpy"]).max())
