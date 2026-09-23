"""Engine contract: required inputs, energy guard, backend and precision, slicing rules, the ExitWave
on the declared plane, file round trip with assertions, run manifest, frozen-phonon seeds, resource
estimate. No numerical tolerances beyond exact equalities (round trip) are involved."""
import dataclasses
import inspect
import json
import sys

import numpy as np
import pytest

from ladder_cases import THETA_0008, rung1_case
from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_reflection_cell
from reflection_holo.forward.contracts import ExitWave
from reflection_holo.forward.multislice import (PLANE_TEXT, VALIDATION_STATUS, AtomicPotential,
                                                ExitWaveFileError, FrozenPhonons,
                                                MultisliceParams, NumericalAbsorber,
                                                PhysicalAbsorption, SheetBeam, estimate_resources,
                                                load_exit_wave, run_realisation, save_exit_wave,
                                                simulate)
from reflection_holo.forward.multislice.backend import get_backend
from reflection_holo.structure import Staircase, build_si001_terraces


def _fast():
    return rung1_case(THETA_0008, dx=0.1, dz=4.0, propagator="exact", precision="complex64")


def test_no_defaults_anywhere():
    for cls in (MultisliceParams, SheetBeam, NumericalAbsorber, PhysicalAbsorption, FrozenPhonons):
        assert all(f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
                   for f in dataclasses.fields(cls)), cls
    for fn in (run_realisation, simulate, estimate_resources, AtomicPotential.__init__):
        params = inspect.signature(fn).parameters.values()
        assert all(p.default is inspect.Parameter.empty for p in params), fn


def test_energy_guard_and_names():
    cell, pot, beam, params, _ = _fast()
    for bad in (dict(energy_keV=300.0), dict(propagator="paraxial"), dict(band_limit="0.7"),
                dict(precision="float32"), dict(backend="torch")):
        with pytest.raises((ValueError, TypeError)):
            run_realisation(cell, potential=pot, beam=beam,
                            params=dataclasses.replace(params, **bad), realisation=0, seed=None)


def test_cupy_is_lazy_and_not_a_fallback():
    assert "cupy" not in sys.modules
    get_backend("numpy", "complex64", 1)
    assert "cupy" not in sys.modules
    try:
        import cupy  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            get_backend("cupy", "complex64", 1)


def test_slices_must_tile_the_cell_exactly():
    cell, pot, beam, params, _ = _fast()
    with pytest.raises(ValueError, match="integer number of slices"):
        run_realisation(cell, potential=pot, beam=beam,
                        params=dataclasses.replace(params, dz_A=3.7), realisation=0, seed=None)


def test_exit_wave_declared_plane_and_round_trip(tmp_path):
    cell, pot, beam, params, _ = _fast()
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    assert isinstance(ew, ExitWave)
    assert ew.plane == PLANE_TEXT and ew.z_A == pytest.approx(cell.length_z_A)
    assert ew.psi.dtype == np.complex64 and ew.psi.shape == (params.nx, params.ny)
    assert ew.dx_A == pytest.approx(cell.extent_x_A / params.nx)
    assert ew.energy_keV == 200.0 and ew.seed is None
    md = ew.metadata
    assert md["validation_status"] == VALIDATION_STATUS and "UNVALIDATED" in VALIDATION_STATUS
    assert md["absorbers"]["numerical"]["label"].startswith("NUMERICAL")
    assert md["potential"]["physical_absorption"]["label"].startswith("ASSUMPTION")
    assert md["band_limit"]["rule_label"].startswith("UNVERIFIED")
    assert all(v["passed"] for k, v in md["geometry_checks"].items() if k != "label")
    p = save_exit_wave(tmp_path / "ew.npz", ew)
    back = load_exit_wave(p, expected_plane=PLANE_TEXT)
    assert np.array_equal(back.psi, ew.psi) and back.dx_A == ew.dx_A and back.dy_A == ew.dy_A
    with pytest.raises(ExitWaveFileError, match="plane"):
        load_exit_wave(p, expected_plane="mid-plane")
    bad = dict(np.load(p))
    bad["dx_A"] = np.float64(0.2)
    np.savez(tmp_path / "bad.npz", **bad)
    with pytest.raises(ExitWaveFileError, match="inconsistent"):
        load_exit_wave(tmp_path / "bad.npz", expected_plane=PLANE_TEXT)
    with pytest.raises(FileExistsError):
        save_exit_wave(p, ew)


def test_simulate_writes_manifest(tmp_path):
    cell, pot, beam, params, _ = _fast()
    out = tmp_path / "outputs"
    waves, mpath = simulate(cell, potential=pot, beam=beam, params=params, realisations=1,
                            seed=None, outputs_root=out, run_name="m2_manifest_test",
                            save_waves=True, config=None, input_paths=[],
                            caller_record=None)
    m = json.loads(mpath.read_text())
    for key in ("packages", "engines", "precision", "seeds", "threads", "inputs", "repository",
                "wave_planes", "config"):
        assert key in m
    assert m["beam_energy_keV"] == 200.0
    assert m["precision"] == {"complex": "complex64"}
    assert m["threads"]["requested"] == 4
    assert m["wave_planes"] == {"exit_wave_r0": PLANE_TEXT}
    assert m["repository"]["commit"]
    eng = m["engines"]["reflection_holo.forward.multislice"]
    assert eng["commit"] == m["repository"]["commit"] and "UNVALIDATED" in eng["status"]
    assert len(m["extra"]["configuration_sha256"]) == 64
    assert m["extra"]["input_hashes"]["cell_atoms_sha256"]
    assert len(m["inputs"]) == 1 and m["inputs"][0]["path"].endswith("_r0000.npz")
    assert "after squaring" in m["extra"]["ensemble_rule"]


@pytest.fixture(scope="module")
def phonon_case():
    """Short atomistic cell at 30 mrad (TEST_ONLY angle) that satisfies every geometry check."""
    p = A_SI_A / np.sqrt(2)
    dz = p / 4
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(1, 1),
                   boundary_step_layers=-2)
    s = build_si001_terraces(azimuth_uvw=(1, 1, 0), azimuth_label="TEST_ONLY: item 8",
                             staircase=st, edge_periods=215, substrate_layers=29,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                             lattice_parameter_label="ASSUMPTION B2")
    cell = build_reflection_cell(s, vacuum_above_A=38.0, depth_below_A=36.0, bulk_absorber_A=15.0,
                                 top_absorber_A=8.0, entrance_vacuum_z_A=10 * dz)
    th = 30e-3
    beam = SheetBeam(height_A=8.0, edge_A=2.0,
                     x_bottom_A=cell.metadata["layout"]["highest_surface_x_A"] + 2.0,
                     theta_in_ext_rad=th, theta_label="TEST_ONLY: item 7")
    params = MultisliceParams(energy_keV=200.0, nx=640, ny=60, dz_A=dz, propagator="exact",
                              band_limit="2/3", backend="numpy", precision="complex64", threads=4,
                              absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                              theta_out_ext_rad=th, buildup_depth_A=20.0)
    absn = PhysicalAbsorption(model="proportional", ratio=0.0, label="ASSUMPTION: none")
    fp = FrozenPhonons(rms_displacement_A=0.076, label="TEST_ONLY: stands in for a sourced value")
    pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=absn,
                          frozen_phonons=fp, static_lattice_label=None)
    return cell, beam, params, pot


def test_frozen_phonon_realisations_and_seeds(phonon_case, tmp_path):
    cell, beam, params, pot = phonon_case
    with pytest.raises(ValueError, match="seed"):
        run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    with pytest.raises(ValueError, match="commensurate"):     # tiles L_z, not the period p
        run_realisation(cell, potential=pot, beam=beam,
                        params=dataclasses.replace(params, dz_A=cell.length_z_A / 869),
                        realisation=0, seed=5)
    waves, mpath = simulate(cell, potential=pot, beam=beam, params=params, realisations=2,
                            seed=20260922, outputs_root=tmp_path / "outputs",
                            run_name="m2_phonons", save_waves=False, config=None, input_paths=[],
                            caller_record=None)
    a, b = waves
    assert (a.realisation, b.realisation, a.seed, b.seed) == (0, 1, 20260922, 20260922)
    assert not np.array_equal(a.psi, b.psi)
    again = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=1,
                            seed=20260922)
    assert np.array_equal(again.psi, b.psi)                  # reproducible from (seed, index)
    m = json.loads(mpath.read_text())
    assert m["seeds"] == {"frozen_phonons": 20260922}
    assert m["engines"]["abTEM (Kirkland parameterisation functions only)"]["version"] == "1.0.10"
    assert a.metadata["potential"]["mean_inner_potential_V"] == pytest.approx(13.903, abs=5e-4)


def test_estimate_resources(phonon_case):
    cell, beam, params, pot = phonon_case
    est = estimate_resources(cell, params, realisations=3, calibrate_cpu=True)
    assert est["n_slices"] == int(round(cell.length_z_A / params.dz_A))
    assert est["memory_bytes"]["total"] > 7 * 8 * params.nx * params.ny
    assert est["cpu"]["seconds_total"] == pytest.approx(3 * est["cpu"]["seconds_per_realisation"])
    assert "NOT MEASURED" in est["gpu"]["note"]
