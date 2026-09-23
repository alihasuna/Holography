"""estimate_resources' memory model against tracemalloc measurements of the engine itself (numpy
backend): H5 finding M4 (the complex128 temporaries of the structure-factor exponentials were not
counted), fixed by engine.memory_model (report H7).

What is measured: the tracemalloc peak of one run_realisation call above the memory held before
the call (the cell, the potential object and the imports), i.e. every numpy array the run
allocates. tracemalloc does not see FFT library scratch buffers (pocketfft) or Python-object
overhead; the model does not count them either. Stated tolerance: 2 % of the model, which is the
size of the arrays of length O(nx + ny + n_slices) and the Python objects that the model leaves
out, on cells of 4.8e4 to 1.1e6 pixels (the measured deviations were 0.01-0.9 %).

The cells are 2-3 lattice periods long: far too short for the reflection geometry assertions
(build-up length, footprint), which are therefore BYPASSED here with monkeypatch, explicitly and
only for these memory measurements (the memory of a run does not depend on them). The band
assertion, including the (0,0,8) working reflection, still runs (pixels <= 0.13 A)."""
import dataclasses
import tracemalloc

import numpy as np
import pytest

import reflection_holo.forward.multislice.engine as engine
from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_reflection_cell
from reflection_holo.forward.multislice import (AtomicPotential, FrozenPhonons, MultisliceParams,
                                                NumericalAbsorber, PhysicalAbsorption, SheetBeam,
                                                estimate_resources, fft_friendly, memory_model,
                                                run_realisation)
from reflection_holo.forward.multislice.backend import get_backend
from reflection_holo.forward.multislice.grid import make_grid
from reflection_holo.structure import Staircase, build_si001_terraces

Q = A_SI_A / 4
TOL = 0.02                     # stated in the module docstring
THETA = 16.1347e-3             # TEST_ONLY: the (0,0,8) angle with the potential's MIP (B32)


def _cell_100(y_periods, z_periods, *, depth, vac):
    """Flat Si(001) strip at the exact [100] azimuth (TEST_ONLY), one z period built with every
    builder assertion and tiled along z (exact for a flat terrace)."""
    one = build_si001_terraces(
        azimuth_uvw=(1, 0, 0), azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
        staircase=Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(y_periods,),
                            boundary_step_layers=0),
        edge_periods=1, substrate_layers=int(np.ceil(depth / Q)) + 2,
        first_terrace_backbond_uvw=(1, 1, 0), termination="bulk", overlayer=None,
        vacuum_above_A=10.0, lattice_parameter_A=A_SI_A, lattice_parameter_label="ASSUMPTION B2")
    n = one.n_atoms
    pos = np.tile(one.positions_A, (z_periods, 1))
    pos[:, 2] += np.repeat(np.arange(z_periods), n) * A_SI_A
    cell_A = one.cell_A.copy()
    cell_A[2, 2] = z_periods * A_SI_A
    s = dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, z_periods),
                            cell_A=cell_A, layer_index=np.tile(one.layer_index, z_periods),
                            terrace_index=np.tile(one.terrace_index, z_periods),
                            metadata=dict(one.metadata))
    return build_reflection_cell(s, vacuum_above_A=vac, depth_below_A=depth, bulk_absorber_A=15.0,
                                 top_absorber_A=8.0, entrance_vacuum_z_A=2 * Q)


def _case(cell, *, precision, ratio, phonons):
    absn = PhysicalAbsorption(model="proportional", ratio=ratio,
                              label="TEST_ONLY: stands in for PROJECT_INPUT item 21" if ratio
                              else "ASSUMPTION: no physical absorption")
    pot = AtomicPotential(
        cell, parameterisation="kirkland", physical_absorption=absn,
        frozen_phonons=(FrozenPhonons(rms_displacement_A=0.076, label="TEST_ONLY: u")
                        if phonons else None),
        static_lattice_label=None if phonons else "ASSUMPTION: static lattice")
    beam = SheetBeam(height_A=8.0, edge_A=2.0,
                     x_bottom_A=cell.metadata["layout"]["highest_surface_x_A"] + 2.0,
                     theta_in_ext_rad=THETA, theta_label="TEST_ONLY: item 7")
    params = MultisliceParams(
        energy_keV=200.0, nx=fft_friendly(int(np.ceil(cell.extent_x_A / 0.13))),
        ny=fft_friendly(int(np.ceil(cell.extent_y_A / 0.13))), dz_A=Q, propagator="exact",
        band_limit="2/3", backend="numpy", precision=precision, threads=2,
        absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"), theta_out_ext_rad=THETA,
        buildup_depth_A=20.0, working_reflections_hkl=((0, 0, 8),))
    return pot, beam, params


def _measured_peak(cell, pot, beam, params, phonons, monkeypatch):
    monkeypatch.setattr(engine, "check_reflection_geometry",
                        lambda *a, **k: {"label": "BYPASSED in the memory test (cell too short)"})
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0,
                        seed=(7 if phonons else None))
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    return peak


@pytest.fixture(scope="module")
def cells():
    narrow = _cell_100(2, 3, depth=36.0, vac=30.0)      # pixel-dominated (576 x 84 px)
    wide = _cell_100(60, 2, depth=36.0, vac=12.0)       # exponential-dominated (432 x 2520 px)
    return dict(narrow=narrow, wide=wide)


@pytest.fixture(scope="module", autouse=True)
def warm_up(cells):
    """First-call allocations of a process (lazy imports, caches: 4-7 MB) are not part of a run."""
    pot, beam, params = _case(cells["narrow"], precision="complex64", ratio=0.1, phonons=False)
    mp = pytest.MonkeyPatch()
    try:
        _measured_peak(cells["narrow"], pot, beam, params, False, mp)
    finally:
        mp.undo()


@pytest.mark.parametrize("which,precision,phonons,stage", [
    ("narrow", "complex64", False, "pixel"),
    ("narrow", "complex128", False, "pixel"),
    ("narrow", "complex64", True, "pixel"),
    ("wide", "complex64", False, "exponentials"),
])
def test_estimate_equals_tracemalloc_peak(cells, monkeypatch, which, precision, phonons, stage):
    cell = cells[which]
    pot, beam, params = _case(cell, precision=precision, ratio=0.1, phonons=phonons)
    est = estimate_resources(cell, params, realisations=1, calibrate_cpu=False)
    mm = est["memory_bytes"]["model"]
    predicted = est["memory_bytes"]["total"] - mm["cell_atom_arrays_B"]   # the cell pre-exists
    measured = _measured_peak(cell, pot, beam, params, phonons, monkeypatch)
    assert mm["numpy"]["peak_phase"] == "slice loop (largest slice)"
    ls = mm["largest_slice"]
    assert (ls["exponentials_B"] > ls["pixel_stage_B"]) == (stage == "exponentials")
    assert measured == pytest.approx(predicted, rel=TOL), (measured, predicted)


def test_wide_slice_needs_the_complex128_temporaries(cells, monkeypatch):
    """H5 M4: the accounting before the fix (72 B/px of named arrays, 8 (nx + ny) n for Ex and Ey,
    48 B/atom; no complex128 temporaries) lies more than 15 % below the measured peak of this cell;
    the exponential term of the model is 32 ny n + 8 nx n (+ 25 n for the selected positions)."""
    cell = cells["wide"]
    pot, beam, params = _case(cell, precision="complex64", ratio=0.1, phonons=False)
    est = estimate_resources(cell, params, realisations=1, calibrate_cpu=False)
    nx, ny, n = params.nx, params.ny, est["atoms_per_slice_max"]
    assert est["memory_bytes"]["model"]["largest_slice"]["exponentials_B"] == \
        25 * n + 32 * ny * n + 8 * nx * n
    measured = _measured_peak(cell, pot, beam, params, False, monkeypatch)
    px = nx * ny
    old = 72 * px + 8 * (nx + ny) * n + 48 * len(cell.Z)               # engine before H7
    assert measured > 1.15 * old


def test_zero_absorption_is_bounded_by_one_array(cells, monkeypatch):
    """The model assumes non-zero absorption (one more complex array in projected()); with r = 0 the
    measured peak is the model minus exactly that array, within the stated tolerance."""
    cell = cells["narrow"]
    pot, beam, params = _case(cell, precision="complex64", ratio=0.0, phonons=False)
    est = estimate_resources(cell, params, realisations=1, calibrate_cpu=False)
    predicted = est["memory_bytes"]["total"] - est["memory_bytes"]["model"]["cell_atom_arrays_B"]
    measured = _measured_peak(cell, pot, beam, params, False, monkeypatch)
    one_array = 8 * params.nx * params.ny
    assert measured < predicted
    assert measured == pytest.approx(predicted - one_array, rel=TOL)


def test_realise_bytes_per_atom():
    """_RealisedAtomic.__init__ peak: 112 B/atom (code reading) + the f2 grid, F and slice starts."""
    cell = _cell_100(2, 300, depth=60.0, vac=12.0)
    nat = len(cell.Z)
    be = get_backend("numpy", "complex64", 2)
    grid = make_grid(cell, nx=fft_friendly(int(np.ceil(cell.extent_x_A / 0.13))),
                     ny=fft_friendly(int(np.ceil(cell.extent_y_A / 0.13))))
    N = int(round(cell.length_z_A / Q))
    pot, _, _ = _case(cell, precision="complex64", ratio=0.1, phonons=False)
    pot.realise(grid=grid, dz_A=Q, n_slices=N, backend=be, rng=None)             # warm
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        rl = pot.realise(grid=grid, dz_A=Q, n_slices=N, backend=be, rng=None)
        cur, peak = (v - base for v in tracemalloc.get_traced_memory())
    finally:
        tracemalloc.stop()
    px = grid.nx * grid.ny
    pred_peak = (engine.MEM_REALISE_PEAK_B_PER_ATOM * nat + (4 + 8) * px
                 + 8 * (grid.nx + grid.ny) + 8 * (N + 1))
    pred_kept = engine.MEM_REALISED_B_PER_ATOM * nat + 4 * px + 8 * (grid.nx + grid.ny) + 8 * (N + 1)
    assert peak == pytest.approx(pred_peak, rel=TOL)
    assert cur == pytest.approx(pred_kept, rel=TOL)
    del rl


def test_memory_model_contract():
    """Required arguments, the device/host split of the cupy figures and the phase names."""
    mm = memory_model(nx=2000, ny=12096, n_slices=4126, n_atoms=31_116_960,
                      atoms_per_slice_max=7632, n_species=1, precision="complex64")
    assert mm["cupy"]["device_peak"] < mm["numpy"]["peak"]
    assert mm["numpy"]["peak"] - mm["cupy"]["device_peak"] >= 72 * 31_116_960
    assert "UNVERIFIED on a GPU" in mm["label"]
    with pytest.raises(TypeError):
        memory_model(nx=10, ny=10, n_slices=1, n_atoms=1, atoms_per_slice_max=1, n_species=1)
    with pytest.raises(ValueError):
        memory_model(nx=10, ny=10, n_slices=1, n_atoms=1, atoms_per_slice_max=1, n_species=1,
                     precision="float32")
