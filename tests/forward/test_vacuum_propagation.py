"""Ladder item (a): vacuum propagation, norm, inverse propagation, band limit, paraxial error.

Tolerances (complex128): the propagator is a product of unimodular factors, so the only error is
floating-point round-off of the FFTs, measured here at <= 3e-14 (phase) and <= 1e-15 (norm) for
the sizes used; the tolerances 1e-11 are 300x that and far below any physical effect."""
import numpy as np
import pytest

from reflection_holo.forward.multislice import (Grid, band_limit_mask, check_band, propagate,
                                                propagate_slices, propagator_kernel,
                                                propagator_phase)
from reflection_holo.forward.multislice.backend import get_backend
from reflection_holo.geometry.errors import SamplingError
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A

LAM = wavelength_A(200.0)
K = k_ang_per_A(200.0)
GRID = Grid(nx=256, ny=64, dx_A=0.1, dy_A=0.13, x0_A=0.0, y0_A=0.0)
TOL = 1e-11


def _plane_wave(grid, mx, my):
    fx, fy = mx / (grid.nx * grid.dx_A), my / (grid.ny * grid.dy_A)
    x, y = grid.x_A()[:, None], grid.y_A()[None, :]
    return np.exp(2j * np.pi * (fx * x + fy * y)), fx, fy


@pytest.mark.parametrize("kind", ["exact", "fresnel"])
def test_tilted_plane_wave_exact_phase_per_slice(kind):
    be = get_backend("numpy", "complex128", 1)
    mask = band_limit_mask(GRID, "2/3")
    mx = -int(round(np.sin(16.47e-3) / LAM * GRID.nx * GRID.dx_A))   # descending, on-grid
    psi0, fx, fy = _plane_wave(GRID, mx, 3)
    dz, n = 1.0, 200
    ker, _ = propagator_kernel(GRID, dz_A=dz, wavelength_A=LAM, kind=kind, band_mask=mask)
    psi = psi0.copy()
    for _ in range(n):
        psi = be.ifft2(be.fft2(psi) * ker)
    q2 = (2 * np.pi) ** 2 * (fx**2 + fy**2)
    if kind == "exact":
        per_slice = dz * (np.sqrt(K**2 - q2) - K)
    else:
        per_slice = -np.pi * LAM * dz * (fx**2 + fy**2)
    expected = psi0 * np.exp(1j * n * per_slice)
    assert np.max(np.abs(psi - expected)) < TOL
    # the phase advance per slice is the analytic one for this component (not only |psi| = 1)
    assert abs(np.angle(psi[0, 0] / psi0[0, 0]) - np.angle(np.exp(1j * n * per_slice))) < TOL


def test_forward_then_inverse_propagation_is_identity():
    be = get_backend("numpy", "complex128", 1)
    mask = band_limit_mask(GRID, "2/3")
    rng = np.random.default_rng(1)
    psi = be.ifft2(be.fft2(rng.standard_normal(GRID.shape) + 1j * rng.standard_normal(
        GRID.shape)) * mask)                       # band-limited random wave
    for kind in ("exact", "fresnel"):
        out = propagate(propagate(psi, GRID, distance_A=750.0, wavelength_A=LAM, kind=kind,
                                  band_mask=mask, backend=be),
                        GRID, distance_A=-750.0, wavelength_A=LAM, kind=kind, band_mask=mask,
                        backend=be)
        assert np.max(np.abs(out - psi)) / np.max(np.abs(psi)) < TOL


class _SmoothRealPotential:
    """Real potential with a few low harmonics (changes with the slice): exp(i sigma V) then has no
    content outside the band (Bessel tails J_n(0.05) with n > 30 underflow), so band limiting the
    transmission function is exact and the loop must conserve the norm."""

    def __init__(self, grid):
        x, y = grid.x_A()[:, None], grid.y_A()[None, :]
        self.Lx, self.Ly = grid.extent_x_A, grid.extent_y_A
        self.x, self.y = x, y

    def slice_key(self, i):
        return None

    def projected(self, i):
        return (40.0 * np.cos(2 * np.pi * (2 * self.x / self.Lx + 0.1 * i))
                * np.cos(2 * np.pi * 3 * self.y / self.Ly) + 25.0).astype(complex)


class _RoughRealPotential(_SmoothRealPotential):
    def projected(self, i):
        rng = np.random.default_rng(i)
        return 300.0 * rng.random(self.x.shape[0:1] + self.y.shape[1:2]).astype(complex)


def _loop(potential, *, n, psi0):
    be = get_backend("numpy", "complex128", 1)
    mask = band_limit_mask(GRID, "2/3")
    Pf, _ = propagator_kernel(GRID, dz_A=1.0, wavelength_A=LAM, kind="exact", band_mask=mask)
    Ph, _ = propagator_kernel(GRID, dz_A=0.5, wavelength_A=LAM, kind="exact", band_mask=mask)
    sigma = 7.2884e-4
    return propagate_slices(psi0, realised=potential, n_slices=n, backend=be, P_full=Pf,
                            P_half=Ph, band_mask=mask.astype(float), sigma=sigma,
                            absorber_factor=np.ones((GRID.nx, 1)))[0], mask


def test_norm_conserved_real_potential_without_absorbers():
    mx = -int(round(np.sin(16.47e-3) / LAM * GRID.nx * GRID.dx_A))
    psi0, _, _ = _plane_wave(GRID, mx, 0)
    psi, _ = _loop(_SmoothRealPotential(GRID), n=300, psi0=psi0)
    n0, n1 = np.sum(np.abs(psi0) ** 2), np.sum(np.abs(psi) ** 2)
    assert abs(n1 / n0 - 1) < TOL
    assert np.std(np.abs(psi)) > 1e-3        # the potential did scatter (not a trivial pass)


def test_band_limit_enforced_on_the_propagated_wave():
    rng = np.random.default_rng(2)
    psi0 = rng.standard_normal(GRID.shape) + 0j
    psi, mask = _loop(_RoughRealPotential(GRID), n=20, psi0=psi0)
    spec = np.fft.fft2(psi)
    out = np.sum(np.abs(spec[~mask]) ** 2) / np.sum(np.abs(spec) ** 2)
    assert out < 1e-28


def test_band_limit_refuses_outgoing_beam_outside_band():
    # docs/03 section 5: 0.13 A supports 64.3 mrad (2/3) and 48 mrad (half-Nyquist) at 200 keV
    g = Grid(nx=100, ny=100, dx_A=0.13, dy_A=0.13, x0_A=0.0, y0_A=0.0)
    rec = check_band(g, rule="2/3", wavelength_A=LAM, angles_rad={"out": 45e-3},
                     reflections_per_A={})               # vacuum: no crystal
    assert rec["angle_ceiling_x_mrad"] == pytest.approx(64.31, abs=0.01)
    assert "UNVERIFIED" in rec["rule_label"]
    rec = check_band(g, rule="half_nyquist", wavelength_A=LAM, angles_rad={"out": 45e-3},
                     reflections_per_A={})               # vacuum: no crystal
    assert rec["angle_ceiling_x_mrad"] == pytest.approx(48.23, abs=0.01)
    with pytest.raises(SamplingError):
        check_band(g, rule="half_nyquist", wavelength_A=LAM, angles_rad={"out": 50e-3},
                   reflections_per_A={})
    coarse = Grid(nx=100, ny=100, dx_A=0.5, dy_A=0.5, x0_A=0.0, y0_A=0.0)
    with pytest.raises(SamplingError):          # the realised 0.5 A pixel cannot carry 24 mrad
        check_band(coarse, rule="2/3", wavelength_A=LAM, angles_rad={"out": 24e-3},
                   reflections_per_A={})


def test_paraxial_error_at_45_mrad():
    """Fresnel minus exact phase over 198 A for a beam at exactly 45 mrad (a grid bin is placed
    there). Leading term k L sin^4(alpha)/8 = 0.02539 rad; exact difference 0.02542 rad.
    docs/03 section 5 prints 0.026 rad: E_review computed 0.0255 and its proposed wording rounded
    it up; the correct 2-s.f. value is 0.025 (recorded in the M2 report; not asserted)."""
    f45 = np.sin(45e-3) / LAM
    g = Grid(nx=64, ny=1, dx_A=10 / (64 * f45), dy_A=1.0, x0_A=0.0, y0_A=0.0)
    m = 10
    assert g.fx()[m] == pytest.approx(f45, rel=1e-12)
    pe, _ = propagator_phase(g, dz_A=198.0, wavelength_A=LAM, kind="exact")
    pf, _ = propagator_phase(g, dz_A=198.0, wavelength_A=LAM, kind="fresnel")
    s = np.sin(45e-3)
    exact_diff = K * 198.0 * (1 - s**2 / 2 - np.sqrt(1 - s**2))
    assert pf[m, 0] - pe[m, 0] == pytest.approx(exact_diff, abs=1e-9)
    assert pf[m, 0] - pe[m, 0] == pytest.approx(K * 198.0 * s**4 / 8, rel=2e-3)  # s^6 term 1e-3


def test_evanescent_components_removed():
    g = Grid(nx=64, ny=1, dx_A=0.005, dy_A=1.0, x0_A=0.0, y0_A=0.0)   # Nyquist 100/A > 1/lambda
    mask = np.ones(g.shape, bool)
    ker, n_ev = propagator_kernel(g, dz_A=1.0, wavelength_A=LAM, kind="exact", band_mask=mask)
    ev = np.abs(g.fx()) >= 1 / LAM
    assert n_ev == int(ev.sum()) > 0
    assert np.all(ker[ev, 0] == 0)
