"""Interaction constant, mean inner potential and atomic slice potential (docs/05 4.3 item 6).

Tolerances:
* sigma vs abTEM energy2sigma: 1e-7 relative. The two differ only by the CODATA edition of the
  constants (ASE uses CODATA 2014, this repository 2018): 6e-9 measured in report D3 (F8).
* 2 k sigma V0 = k^2 Delta_first_order: an algebraic identity, 1e-12 relative (round-off).
* Kirkland mean inner potential 13.903 V: D3 F16 prints 3 decimals; 5e-4 V.
* Slice potential vs a FRESH abTEM ScatteringFactorProjectionIntegrals("kirkland").integrate_on_grid
  (float64): identical mean (1e-12 relative: same F(0) and normalisation); Fourier coefficients
  inside |f| <= 2.5 1/A (the 2/3 band at 0.13 A) agree to 1e-3 of the largest coefficient at
  dx = 0.025 A. Convergence study (5 random Si positions in a 9.6 x 6.4 A slice): 5.35e-3, 1.62e-3,
  2.97e-4, 8.70e-5 at dx = 0.1, 0.05, 0.025, 0.0125 A -- abTEM's bilinear delta spreading with
  sinc compensation converges to the exact structure factor used here; 1e-3 is 3.4x the dx = 0.025
  value. The test also checks that the difference falls by >= 3x from dx = 0.05 to 0.025.
"""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.multislice import (FrozenPhonons, Grid, PhysicalAbsorption,
                                                interaction_constant_rad_per_VA)
from reflection_holo.forward.multislice.backend import get_backend
from reflection_holo.geometry.refraction import refraction_delta, refraction_delta_first_order
from reflection_holo.geometry.wavelength import k_ang_per_A

abtem = pytest.importorskip("abtem")


def test_sigma_matches_abtem_and_refraction():
    from abtem.core.energy import energy2sigma
    s = interaction_constant_rad_per_VA(200.0)
    assert s == pytest.approx(energy2sigma(200e3), rel=1e-7)
    assert s == pytest.approx(7.28840e-4, abs=5e-10)
    k = k_ang_per_A(200.0)
    assert 2 * k * s * 12.0 == pytest.approx(k**2 * refraction_delta_first_order(200.0, 12.0),
                                             rel=1e-12)
    rel = k**2 * refraction_delta(200.0, 12.0) / (2 * k * s * 12.0) - 1
    assert 8.3e-6 < rel < 8.5e-6                    # documented 8.4e-6 (physics_conventions)


def test_kirkland_mean_inner_potential_and_lobato_refused(small_cell):
    from reflection_holo.forward.multislice import AtomicPotential, potential_mean_inner_potential_V
    pot = AtomicPotential(small_cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(
                              model="proportional", ratio=0.0, label="ASSUMPTION: none"),
                          frozen_phonons=None, static_lattice_label="ASSUMPTION: static")
    assert potential_mean_inner_potential_V(pot) == pytest.approx(13.903, abs=5e-4)
    prov = pot.provenance()
    assert prov["abtem_version"] == "1.0.10" and prov["abtem_commit"].startswith("164e644f")
    assert prov["parameterisation"] == "kirkland"
    assert prov["provenance_label"].startswith("SECTION_READ")
    assert "not read by us (SM17)" in prov["parameterisation_label"]
    with pytest.raises(ValueError, match="Lobato refused"):
        AtomicPotential(small_cell, parameterisation="lobato", physical_absorption=pot.absorption,
                        frozen_phonons=None, static_lattice_label="ASSUMPTION: static")


def _ours(pos, grid):
    from abtem.parametrizations import KirklandParametrization
    from reflection_holo.forward.multislice.potentials import _RealisedAtomic

    class _Cell:
        atoms_xyz_A = np.column_stack([pos[:, 0], pos[:, 1], np.full(len(pos), 0.5)])
        Z = np.full(len(pos), 14)

    class _Pot:
        cell = _Cell()
        frozen_phonons = None
        absorption = PhysicalAbsorption(model="proportional", ratio=0.0, label="ASSUMPTION: none")

        def scattering_factor(self, Z, f2):
            return KirklandParametrization().projected_scattering_factor("Si")(f2)

    be = get_backend("numpy", "complex128", 1)
    r = _RealisedAtomic(_Pot(), grid, 1.0, 1, be, None)
    return np.asarray(r.projected(0)).real


def test_slice_potential_matches_fresh_abtem_integrator():
    from ase import Atoms
    from abtem.integrals import ScatteringFactorProjectionIntegrals
    abtem.config.set({"precision": "float64"})
    rng = np.random.default_rng(3)
    Lx, Ly = 9.6, 6.4
    pos = np.column_stack([rng.uniform(0, Lx, 5), rng.uniform(0, Ly, 5)])
    errs = []
    for dx in (0.05, 0.025):
        nx, ny = int(round(Lx / dx)), int(round(Ly / dx))
        grid = Grid(nx=nx, ny=ny, dx_A=Lx / nx, dy_A=Ly / ny, x0_A=0.0, y0_A=0.0)
        atoms = Atoms("Si5", positions=np.column_stack([pos, np.full(5, 0.3)]),
                      cell=[Lx, Ly, 1.0], pbc=True)
        va = ScatteringFactorProjectionIntegrals("kirkland").integrate_on_grid(
            atoms, 0.0, 1.0, (nx, ny), (Lx / nx, Ly / ny))            # fresh integrator per grid
        vo = _ours(pos, grid)
        assert vo.mean() == pytest.approx(va.mean(), rel=1e-12)
        A, O = np.fft.fft2(va), np.fft.fft2(vo)
        f = np.sqrt(grid.fx()[:, None] ** 2 + grid.fy()[None, :] ** 2)
        errs.append(np.abs(A - O)[f <= 2.5].max() / np.abs(O).max())
    print("low-frequency max relative difference at dx 0.05, 0.025:", errs)
    assert errs[1] <= 1e-3
    assert errs[0] / errs[1] >= 3.0


def test_physical_absorption_and_frozen_phonon_inputs(small_cell):
    from reflection_holo.forward.multislice import AtomicPotential
    with pytest.raises(ValueError):                 # zero absorption must be an ASSUMPTION
        PhysicalAbsorption(model="proportional", ratio=0.0, label="PROJECT_INPUT item 21")
    with pytest.raises(ValueError):
        PhysicalAbsorption(model="proportional", ratio=0.1, label="")
    with pytest.raises(ValueError):
        FrozenPhonons(rms_displacement_A=0.076, label="made up")
    absn = PhysicalAbsorption(model="proportional", ratio=0.1, label="TEST_ONLY: item 21")
    pot = AtomicPotential(small_cell, parameterisation="kirkland", physical_absorption=absn,
                          frozen_phonons=None, static_lattice_label="ASSUMPTION: static")
    grid = Grid(nx=128, ny=48, dx_A=small_cell.extent_x_A / 128,
                dy_A=small_cell.extent_y_A / 48, x0_A=0.0, y0_A=0.0)
    be = get_backend("numpy", "complex128", 1)
    dz = A_SI_A / np.sqrt(2) / 4
    n = int(round(small_cell.length_z_A / dz))
    r = pot.realise(grid=grid, dz_A=dz, n_slices=n, backend=be, rng=None)
    i = next(j for j in range(n) if r.slice_key(j) is None)
    V = np.asarray(r.projected(i))
    assert np.allclose(V.imag, 0.1 * V.real)
    fp = FrozenPhonons(rms_displacement_A=0.076, label="TEST_ONLY: stands in for a sourced "
                                                        "Debye-Waller value")
    potf = AtomicPotential(small_cell, parameterisation="kirkland", physical_absorption=absn,
                           frozen_phonons=fp, static_lattice_label=None)
    with pytest.raises(ValueError):
        potf.realise(grid=grid, dz_A=dz, n_slices=n, backend=be, rng=None)
    a = potf.realise(grid=grid, dz_A=dz, n_slices=n, backend=be,
                     rng=np.random.default_rng([7, 0])).metadata["displaced_positions_sha256"]
    b = potf.realise(grid=grid, dz_A=dz, n_slices=n, backend=be,
                     rng=np.random.default_rng([7, 0])).metadata["displaced_positions_sha256"]
    c = potf.realise(grid=grid, dz_A=dz, n_slices=n, backend=be,
                     rng=np.random.default_rng([7, 1])).metadata["displaced_positions_sha256"]
    assert a == b != c


def test_slice_assignment_rule(small_cell):
    from reflection_holo.forward.multislice import AtomicPotential
    pot = AtomicPotential(small_cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(
                              model="proportional", ratio=0.0, label="ASSUMPTION: none"),
                          frozen_phonons=None, static_lattice_label="ASSUMPTION: static")
    grid = Grid(nx=64, ny=24, dx_A=small_cell.extent_x_A / 64, dy_A=small_cell.extent_y_A / 24,
                x0_A=0.0, y0_A=0.0)
    dz = A_SI_A / np.sqrt(2) / 4                     # atomic planes (p/2 apart) on boundaries
    n = int(round(small_cell.length_z_A / dz))
    r = pot.realise(grid=grid, dz_A=dz, n_slices=n, backend=get_backend("numpy", "complex64", 1),
                    rng=None)
    z = small_cell.atoms_xyz_A[:, 2]
    expected = np.floor((z + 1e-9) / dz).astype(int)
    assert np.array_equal(np.sort(expected), r.idx_sorted)
    assert r.metadata["max_atom_offset_from_slice_centre_A"] == pytest.approx(dz / 2, abs=1e-6)
    empty = [i for i in range(n) if r.slice_key(i) == "empty"]
    assert len(empty) >= n // 2 - 1                  # every other slice holds no atomic plane
