"""Reflection cell of a buried torus void (reflection_holo.forward.feature_cell, agent T3): the void
in cell coordinates, the depth rule F5 (clean crystal >= 65 A below the flat top plane AND >= 30 A
below the void bottom) passing and failing, and the T1/T3 runner's argument rules for the buried
kinds (no default cap, absorption or CPU limit).

TEST_ONLY inputs (items 7, 8, 13); no propagation is run here (the engine's own assertions are
exercised by the T3 runs, docs/agent_reports/T3_buried_torus.md)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import ReflectionGeometryError
from reflection_holo.forward.feature_cell import (BURIED_MIN_CLEAN_BELOW_SURFACE_A,
                                                  BURIED_MIN_CLEAN_BELOW_VOID_A,
                                                  build_feature_reflection_cell,
                                                  check_buried_void_depth, check_feature_geometry)
from reflection_holo.forward.multislice import SheetBeam
from reflection_holo.structure.features import build_si001_with_feature
from reflection_holo.structure.shapes import BuriedTorus

A = A_SI_A
Q = A / 4
LAB = "TEST_ONLY: stands in for PROJECT_INPUT item {}"
THETA = 16.1347e-3                       # TEST_ONLY glancing angle (item 7)
TH_INT = 18.4719e-3
ENT = 20 * Q
BULK = 5.0
REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / "scripts" / "torus" / "run_torus_multislice.py"


def structure(depth, cap):
    Ly, Lz = 13 * A, 60 * A
    f = BuriedTorus(center_y_A=0.5 * Ly, center_z_A=150.0, major_radius_A=20.0, minor_radius_A=6.0,
                    cap_A=cap, label=LAB.format(13), source="TEST_ONLY")
    return build_si001_with_feature(azimuth_uvw=(1, 0, 0), azimuth_label=LAB.format(8), feature=f,
                                    extent_y_A=Ly, extent_z_A=Lz, depth_layers=depth,
                                    lattice_parameter_A=A, lattice_label="ASSUMPTION B2",
                                    ring_margin_A=A, vacuum_above_A=10.0)


def cell_of(s):
    x_s = s.metadata["terrace_map"][0]["top_height_A"]
    return build_feature_reflection_cell(s, vacuum_above_flat_surface_A=20.0, depth_below_A=x_s,
                                         bulk_absorber_A=BULK, top_absorber_A=5.0,
                                         entrance_vacuum_z_A=ENT)


def beam_above(cell, gap, H=4.0, e=1.0):
    return SheetBeam(height_A=H, edge_A=e, x_bottom_A=cell.metadata["layout"]
                     ["highest_surface_x_A"] + gap, theta_in_ext_rad=THETA,
                     theta_label=LAB.format(7))


@pytest.fixture(scope="module")
def deep():
    """53 layers: clean 52 a/4 - 5 A = 65.60 A below the surface; void bottom at 17 A: 48.6 A."""
    return structure(53, 5.0)


def test_rule_constants():
    assert BURIED_MIN_CLEAN_BELOW_SURFACE_A == 65.0 and BURIED_MIN_CLEAN_BELOW_VOID_A == 30.0


def test_void_in_cell_coordinates(deep):
    c = cell_of(deep)
    lay, f = c.metadata["layout"], c.metadata["feature"]
    x_flat = 52 * Q
    assert np.isclose(lay["lowest_surface_x_A"], x_flat)
    assert np.isclose(lay["highest_surface_x_A"], x_flat)
    assert f["kind"] == "buried_void" and f["cap_A"] == 5.0
    assert np.isclose(f["void_top_x_A"], x_flat - 5.0)
    assert np.isclose(f["tube_centre_x_A"], x_flat - 11.0)
    assert np.isclose(f["void_bottom_x_A"], x_flat - 17.0)
    assert np.allclose(f["top_layer_x_range_A"], [x_flat, x_flat])
    assert np.isclose(f["highest_atom_x_A"], x_flat)            # nothing above the flat surface
    assert f["n_removed"] == len(deep.feature_sites_A) and f["n_added"] == 0
    assert np.isclose(f["center_z_A"], 150.0 + ENT)
    assert len(c.Z) == deep.n_atoms


def test_f5_passes_and_feature_checks_record_it(deep):
    c = cell_of(deep)
    out = check_feature_geometry(c, beam=beam_above(c, 0.5), theta_out_ext_rad=THETA,
                                 theta_int_rad=TH_INT, buildup_depth_A=20.0,
                                 footprint_margin_A=10.0)
    f5 = out["F5_buried_void_depth"]
    assert f5["passed"]
    assert np.isclose(f5["clean_below_surface_A"], 52 * Q - BULK)
    assert np.isclose(f5["clean_below_void_bottom_A"], 52 * Q - 17.0 - BULK)
    assert out["F4_conservative_reading"]["shadow_or_blocked_view_length_A"] == 0.0
    assert check_buried_void_depth(c)["F5_buried_void_depth"]["passed"]


def test_f5_fails_below_the_surface_rule():
    c = cell_of(structure(51, 5.0))      # 50 a/4 - 5 = 62.9 A < 65 A (void rule: 45.9 A >= 30 A)
    with pytest.raises(ReflectionGeometryError, match="F5_buried_void_depth"):
        check_buried_void_depth(c)


def test_f5_fails_below_the_void_rule():
    c = cell_of(structure(53, 30.0))     # surface 65.6 A >= 65 A, void bottom 42 A: 23.6 A < 30 A
    with pytest.raises(ReflectionGeometryError, match="F5_buried_void_depth") as exc:
        check_buried_void_depth(c)
    assert "below the void bottom" in str(exc.value)


def test_void_reaching_the_absorber_is_refused():
    s = structure(24, 5.0)               # void bottom at 23 a/4 - 17 = 14.2 A above the box bottom
    x_s = s.metadata["terrace_map"][0]["top_height_A"]
    with pytest.raises(ReflectionGeometryError, match="reaches the bulk absorber"):
        build_feature_reflection_cell(s, vacuum_above_flat_surface_A=20.0, depth_below_A=x_s,
                                      bulk_absorber_A=15.0, top_absorber_A=5.0,
                                      entrance_vacuum_z_A=ENT)


def test_check_buried_void_depth_needs_a_buried_void():
    s = structure(53, 5.0)
    c = cell_of(s)
    c.metadata["feature"] = None
    with pytest.raises(ValueError, match="buried void"):
        check_buried_void_depth(c)


# ---- the runner's buried kinds (argument rules; no engine run) -----------------------------------
def _runner():
    spec = importlib.util.spec_from_file_location("run_torus_multislice_t3", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_runner_case_depth_is_the_smallest_satisfying_f5():
    m = _runner()
    c = m.BURIED_CASE
    n = c["depth_layers"]
    clean = (n - 1) * Q - c["bulk_absorber_A"]
    need = max(65.0, max(c["study_caps_A"]) + 2 * c["feature"]["minor_radius_A"] + 30.0)
    assert clean >= need and (n - 2) * Q - c["bulk_absorber_A"] < need
    assert n == m.buried_min_depth_layers(Q, c["bulk_absorber_A"], 12.0, 30.0) == 74
    assert c["energy_keV"] == 200.0
    assert c["physical_absorption"]["test_only_r0.1"]["ratio"] == 0.1
    assert c["physical_absorption"]["test_only_r0.1"]["label"].startswith("TEST_ONLY")
    assert c["physical_absorption"]["none"]["label"].startswith("ASSUMPTION B30")
    assert c["limits"]["cpu_seconds"] is None                     # no default for the buried kinds
    assert m.run_name("buried", 10.0, "test_only_r0.1") == "buried_cap10A_r010"
    assert m.run_name("buried_flat", None, "none") == "buried_flat_r000"
    assert m.run_name("trench", None, None) == "trench"


@pytest.mark.parametrize("args, msg", [
    (["--kind", "buried", "--absorption", "none", "--max-cpu-seconds", "10"], "--cap-A is required"),
    (["--kind", "buried", "--cap-A", "0", "--absorption", "none", "--max-cpu-seconds", "10"],
     "--cap-A must be finite and > 0"),
    (["--kind", "buried", "--cap-A", "10", "--max-cpu-seconds", "10"], "--absorption is required"),
    (["--kind", "buried_flat", "--absorption", "none"], "--max-cpu-seconds is required"),
    (["--kind", "buried_flat", "--cap-A", "5", "--absorption", "none", "--max-cpu-seconds", "10"],
     "--cap-A is only for --kind buried"),
    (["--kind", "trench", "--absorption", "none"], "--absorption is only for the buried kinds"),
])
def test_runner_refuses_missing_or_misplaced_buried_arguments(tmp_path, args, msg):
    r = subprocess.run([sys.executable, str(RUNNER), *args, "--out", str(tmp_path / "o")],
                       capture_output=True, text=True)
    assert r.returncode == 2 and msg in r.stderr
    assert not (tmp_path / "o").exists()                  # refused before anything is written
