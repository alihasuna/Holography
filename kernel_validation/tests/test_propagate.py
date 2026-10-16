"""Tests for reflection_holo.multislice.propagate (rung R2, item 2b), plus the 2a absorber reflection test.

Run:  pytest tests/test_propagate.py -v
Expected: all tests PASSED (no xfail in this file).
"""
import math

import numpy as np
import pytest

from reflection_holo.constants import interaction_constant, wavelength
from reflection_holo.multislice.potential import Grid, projected_potential
from reflection_holo.multislice import propagate as pr

E0 = 200e3  # eV, PROJECT_INPUT supplied (Ali, 2026-09-22)
LAM = wavelength(E0)


def test_plane_wave_eigenphase():
    """External fact: P = exp(-i pi lambda q^2 dx) [kirkland_ch06 Eq. 6.65]. Tol 1e-12."""
    g = Grid(ny=32, nz=64, dy=0.2, dz=0.2)
    iz, iy = 5, 3
    qz = np.fft.fftfreq(g.nz, g.dz)[iz]
    qy = np.fft.fftfreq(g.ny, g.dy)[iy]
    psi = np.exp(2j * np.pi * (qz * g.z[:, None] + qy * g.y[None, :]))
    P = pr.fresnel_propagator(g, 7.0, LAM, bandwidth=None)
    out = pr.multislice(psi, [np.ones_like(psi)], P)
    ratio = out / psi
    expect = np.exp(-1j * np.pi * LAM * (qz**2 + qy**2) * 7.0)
    assert np.max(np.abs(ratio - expect)) < 1e-12


def test_composition():
    """External fact: p(dx) = p(dx - dxa) (x) p(dxa) [kirkland_ch06 Eq. 6.88]. Tol 1e-12."""
    g = Grid(ny=16, nz=32, dy=0.3, dz=0.25)
    P1 = pr.fresnel_propagator(g, 1.3, LAM, None)
    P2 = pr.fresnel_propagator(g, 2.2, LAM, None)
    P3 = pr.fresnel_propagator(g, 3.5, LAM, None)
    assert np.max(np.abs(P1 * P2 - P3)) < 1e-12


def test_bandwidth_two_thirds():
    """External fact: P = 0 outside 2/3 k_max, k_max = min(N/2a, N/2b) [kirkland_ch06 p.36, Eq. 6.92]. Exact."""
    g = Grid(ny=40, nz=64, dy=0.25, dz=0.2)
    P = pr.fresnel_propagator(g, 2.0, LAM)
    qz, qy = g.freqs()
    q = np.sqrt(qz**2 + qy**2)
    kmax = min(1 / (2 * 0.25), 1 / (2 * 0.2))
    assert np.all(P[q >= 2 / 3 * kmax] == 0)
    assert np.allclose(np.abs(P[q < 2 / 3 * kmax]), 1.0, atol=1e-14)


def test_gaussian_spreading():
    """External fact (DERIVED_HERE from Eq. 6.65): exp(-z^2/w^2) spreads as
    w(x) = w sqrt(1 + (lambda x / (pi w^2))^2), so <z^2> = w(x)^2/4. Tol 1e-6 relative."""
    g = Grid(ny=1, nz=2048, dy=1.0, dz=0.05, z0=-51.2)
    w, X = 3.0, 2000.0
    psi = np.exp(-(g.z[:, None] / w) ** 2).astype(complex)
    out = pr.multislice(psi, [np.ones_like(psi)], pr.fresnel_propagator(g, X, LAM, None))
    I = np.abs(out[:, 0]) ** 2
    m2 = np.sum(I * g.z**2) / np.sum(I)
    wx2 = w**2 * (1 + (LAM * X / (np.pi * w**2)) ** 2)
    assert abs(m2 / (wx2 / 4) - 1) < 1e-6


def test_tilted_packet_drift():
    """External fact (DERIVED_HERE from Eq. 6.65): a packet with carrier q0 drifts by lambda*q0*x. Tol 1e-6 A."""
    g = Grid(ny=1, nz=4096, dy=1.0, dz=0.1, z0=-204.8)
    q0 = np.fft.fftfreq(g.nz, g.dz)[-300]  # negative: travels toward -z, like the illumination
    psi = np.exp(-(g.z[:, None] / 10.0) ** 2) * np.exp(2j * np.pi * q0 * g.z[:, None])
    X = 4000.0
    out = pr.multislice(psi, [np.ones_like(psi)] * 4, pr.fresnel_propagator(g, X / 4, LAM, None))
    I = np.abs(out[:, 0]) ** 2
    zc = np.sum(I * g.z) / np.sum(I)
    assert abs(zc - LAM * q0 * X) < 1e-6


def test_unitarity_real_potential():
    """External fact: with a real potential each step is unitary [kirkland_ch06 p.52, Eq. 6.95].
    W = 0, no band limits on t or P: flux conserved per slice to 1e-6 (contract T-unitarity)."""
    g = Grid(ny=24, nz=96, dy=0.16, dz=0.16)
    rng = np.random.default_rng(1)
    atoms = np.column_stack([rng.uniform(0, 3.84, 6), rng.uniform(0, 8.0, 6)])
    V = projected_potential(atoms, 14, g, 0.5, 1.92, absorption=False)
    sig = interaction_constant(E0)
    ts = list(pr.transmissions_from_potentials([V] * 20, sig, g, bandwidth=None))
    psi0 = np.ones((g.nz, g.ny), complex) / math.sqrt(g.area)
    _, fl = pr.multislice(psi0, ts, pr.fresnel_propagator(g, 1.92, LAM, None), grid=g,
                          record_flux=True)
    assert np.max(np.abs(np.diff(fl))) < 1e-6
    assert abs(fl[-1] - 1.0) < 1e-6


def test_subslicing_free_space_identical():
    """External fact: Eq. 6.88 composition; with v = 0, n_sub slices of dx/n equal one slice. Tol 1e-12."""
    g = Grid(ny=8, nz=64, dy=0.2, dz=0.2)
    psi = np.exp(-((g.z[:, None] - 6) / 2) ** 2).astype(complex) * np.ones((1, g.ny))
    Z = np.zeros((g.nz, g.ny))
    a = pr.multislice(psi, pr.transmissions_from_potentials([Z], 1.0, g, 1, None),
                      pr.fresnel_propagator(g, 4.0, LAM, None))
    b = pr.multislice(psi, pr.transmissions_from_potentials([Z], 1.0, g, 4, None),
                      pr.fresnel_propagator(g, 1.0, LAM, None))
    assert np.max(np.abs(a - b)) < 1e-12


def test_subslicing_converges():
    """External fact: the multislice global error falls with slice thickness [kirkland_ch06 p.23, p.48].
    Criterion: |psi(2)-psi(4)| < 0.7 |psi(1)-psi(2)|."""
    g = Grid(ny=1, nz=512, dy=1.0, dz=0.1, z0=-25.6)
    v = 30.0 * np.exp(-(g.z[:, None] / 2.0) ** 2)  # V*A per 4 A slice, smooth
    sig = interaction_constant(E0)
    q0 = np.fft.fftfreq(g.nz, g.dz)[-40]
    psi = np.exp(-((g.z[:, None] - 8) / 4) ** 2) * np.exp(2j * np.pi * q0 * g.z[:, None])

    def run(n):
        return pr.multislice(psi, pr.transmissions_from_potentials([v] * 40, sig, g, n, None),
                             pr.fresnel_propagator(g, 4.0 / n, LAM, None))
    r1, r2, r4 = run(1), run(2), run(4)
    d12 = np.linalg.norm(r1 - r2)
    d24 = np.linalg.norm(r2 - r4)
    assert d12 > 0 and d24 < 0.7 * d12


def test_paraxial_error_20mrad():
    """External fact: expansion of R [kirkland_ch06 Eq. 6.81]. Leading error -pi a^4/(4 lam);
    at 20 mrad this is -5.011e-6 rad/A (hand value in NOTES_B). Tol 1e-3 relative / 1e-3 absolute."""
    e = float(pr.paraxial_phase_error(0.02, LAM))
    lead = -np.pi * 0.02**4 / (4 * LAM)
    assert abs(e / lead - 1) < 1e-3
    assert abs(e - (-5.011e-6)) < 5e-9


def test_tilt_warning():
    """External fact: propagator tilt valid only up to about 1 degree [kirkland_ch06 p.39]."""
    g = Grid(ny=8, nz=8, dy=0.2, dz=0.2)
    with pytest.warns(UserWarning):
        pr.fresnel_propagator(g, 1.0, LAM, tilt=(0.0, 0.03))


@pytest.mark.parametrize("theta", [8.4e-3, 20e-3])
def test_absorber_cos2_reflection_below_level(theta):
    """External fact: stationary transverse dispersion of Eq. 6.43 (NOTES_B E10). The cos^2 absorber
    (10 V, 60 A) reflects < 1e-6 of the incident flux and leaves < 1e-6 unabsorbed. Stated level 1e-6."""
    r = pr.measure_absorber_reflection(theta, E0, shape="cos2")
    assert r["R"] < 1e-6
    assert r["remaining_incident"] < 1e-6


def test_absorber_step_reflection_detectable():
    """Sensitivity check: an abrupt 10 V step reflects |(k-k')/(k+k')|^2 ~ 1.3e-3 at 20 mrad
    (DERIVED_HERE, NOTES_B section 3). The test must see > 1e-4; this shows that the cos2 test is not vacuous."""
    r = pr.measure_absorber_reflection(20e-3, E0, shape="step")
    assert r["R"] > 1e-4
