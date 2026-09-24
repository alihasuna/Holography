#!/usr/bin/env python3
"""Half-torus smoke test T1: atomistic Si(001) structure with a ring trench or ridge (or the flat
reference) and a small grazing-incidence multislice run at 200 keV.

STATUS OF EVERY OUTPUT: UNVALIDATED. The reflection has not converged along the beam in a cell of
this length (finite-cell build-up), there is no physical absorption (ASSUMPTION B30), and the
engine is UNVALIDATED for atomistic reflection (engine.VALIDATION_STATUS: the atomistic fixed-beam
null test of rung 3 has not passed, the abTEM cross-check was not run). Demo stand-ins: azimuth [100] (B20), feature geometry (B33 trench, B34 ridge; PROJECT_INPUT
item 13), glancing angle from the engine's mean inner potential (B32), lattice parameter (B2).

BURIED VOID STUDY (agent T3, Ali 2026-09-24): kind "buried" builds a FULL torus-shaped empty cavity
(shapes.BuriedTorus, demo stand-in B42) under an intact cap of --cap-A (required) below the flat
surface; kind "buried_flat" is its flat reference in the IDENTICAL cell (BURIED_CASE: 74 layers,
the smallest depth that satisfies the depth rule F5 of forward.feature_cell for the deepest study cap
of 30 A). Both require --absorption ("test_only_r0.1": TEST_ONLY proportional r = 0.1; "none":
ASSUMPTION B30) and an explicit --max-cpu-seconds (no default for these kinds). Detectability
only: the engine is UNVALIDATED for step heights.

Usage (threads fixed by the environment so the manifest's thread check is consistent):
  OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
  venv/bin/python scripts/torus/run_torus_multislice.py --kind trench --out <dir> [--estimate-only]
  (buried kinds: the *_NUM_THREADS variables = 2, BURIED_CASE threads)
  ... --kind buried --cap-A 10 --absorption test_only_r0.1 --max-cpu-seconds 3600 --out <dir>
Writes into <dir>: case_<name>.json (every input with its label), structure_<name>.npz (atoms,
feature sites, cell, metadata), summary_<name>.json, and outputs/exit_waves/ and
outputs/manifests/ written by the engine (the manifest writer requires a directory named outputs).
<name> is the kind for trench, ridge and flat, buried_cap<cap>A_<r010|r000> and
buried_flat_<r010|r000> for the buried study.
"""
from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.feature_cell import (build_feature_reflection_cell,
                                                  check_feature_geometry)
from reflection_holo.forward.multislice import (VALIDATION_STATUS, AtomicPotential,
                                                MultisliceParams, NumericalAbsorber,
                                                PhysicalAbsorption, SheetBeam, estimate_resources,
                                                fft_friendly, potential_mean_inner_potential_V,
                                                reflection_setup, simulate)
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.structure.features import (build_si001_flat_reference,
                                                build_si001_with_feature)
from reflection_holo.structure.shapes import BuriedTorus, HalfTorus
from reflection_holo.forward.feature_cell import (BURIED_MIN_CLEAN_BELOW_SURFACE_A,
                                                  BURIED_MIN_CLEAN_BELOW_VOID_A)

STATUS = ("UNVALIDATED: finite-cell build-up not converged along z, no physical absorption "
          "(ASSUMPTION B30), engine abTEM cross-check NOT RUN (report M2 section 10). Engine: "
          + VALIDATION_STATUS)
A = A_SI_A
# ---- demo case (every value labelled; nothing here is comparable to experiment) ----------------
CASE = dict(
    energy_keV=200.0,                                   # PROJECT_INPUT item 1 (asserted)
    lattice_parameter_A=A, lattice_label="ASSUMPTION B2",
    azimuth_uvw=(1, 0, 0),
    azimuth_label="ASSUMPTION B20: demo beam azimuth exactly [100] (stands in for PROJECT_INPUT "
                  "item 8)",
    feature=dict(major_radius_A=50.0, minor_radius_A=12.0, center_z_A=1000.0,
                 center_y="middle of the y window",
                 label="ASSUMPTION",
                 source={"trench": "demo stand-in B33 (trench), docs/model_assumptions.md",
                         "ridge": "demo stand-in B34 (ridge), docs/model_assumptions.md"}),
    periods_y=27,            # 146.63 A >= 2R + 2r + 20 A = 144 A
    periods_z=276,           # 1498.93 A crystal length along the beam
    depth_layers=37,         # flat top layer 36 a/4 = 48.88 A above the bottom layer
    ring_margin_A=2 * A,     # clearance to the periodic y/z edges (>= one period, asserted)
    structure_vacuum_A=10.0,  # x box of the structure only (the reflection cell sets its own)
    vacuum_above_flat_surface_A=60.0, bulk_absorber_A=15.0, top_absorber_A=10.0,
    entrance_vacuum_slices=20,
    beam=dict(height_A=22.0, edge_A=2.0, bottom_above_flat_surface_at_launch_A=1.0),
    absorber=dict(strength_V=100.0, profile="sin2"),     # NUMERICAL (not physical), as M2 smoke
    physical_absorption=dict(model="proportional", ratio=0.0,
                             label="ASSUMPTION B30: no physical absorption (PROJECT_INPUT item "
                                   "21 not supplied)"),
    static_lattice_label="ASSUMPTION: static lattice (no frozen phonons) for the half-torus "
                         "smoke run",
    theta_label="ASSUMPTION B32: external angle of the (0,0,8) internal Bragg condition computed "
                "with the engine's mean inner potential (stands in for PROJECT_INPUT item 7)",
    working_reflection_hkl=(0, 0, 8),
    working_reflection_label="ASSUMPTION B17: (0,0,8) working condition (stands in for "
                             "PROJECT_INPUT item 9); asserted inside the band (H2 N8, H5 A7)",
    buildup_depth_A=20.0, footprint_margin_A=100.0,
    max_pixel_A=0.13, slices_per_period=4, propagator="exact", band_limit="2/3",
    backend="numpy", precision="complex128", threads=4,
    limits=dict(cpu_seconds=600.0, memory_bytes=10e9, cpu_calibration_factor=1.5,
                note="about 10 minutes and 10 GB on this machine (orchestrator); CPU estimate x1.5 "
                     "(M2 report section 7 calibration)"),
)

# ---- buried-void study (agent T3; every value labelled; DEMO, detectability only) --------------
BURIED_KINDS = ("buried", "buried_flat")
BURIED_STATUS = (
    "UNVALIDATED, DETECTABILITY ONLY: the engine is not validated for step heights (the atomistic "
    "fixed-beam null test has not passed), the reflection has not converged along z in a crystal "
    "of 1499 A (H2 2.4: run-in 2500 A at r = 0.1), the absorption is a TEST_ONLY stand-in (r = 0.1) "
    "or absent (ASSUMPTION B30; r = 0 converges at no clean depth outside the plateau, P2 6.5 / E7 "
    "3.7). Signals are differences to the flat reference in the identical cell. Engine: "
    + VALIDATION_STATUS)
BURIED_CASE = dict(
    energy_keV=200.0,                                   # PROJECT_INPUT item 1 (asserted)
    lattice_parameter_A=A, lattice_label="ASSUMPTION B2",
    azimuth_uvw=(1, 0, 0),
    azimuth_label="ASSUMPTION B20: demo beam azimuth exactly [100] (stands in for PROJECT_INPUT "
                  "item 8)",
    feature=dict(shape="reflection_holo.structure.shapes.BuriedTorus",
                 major_radius_A=50.0, minor_radius_A=12.0, center_z_A=1000.0,
                 center_y="middle of the y window", cap_A="per run (--cap-A, required)",
                 label="ASSUMPTION",
                 source="demo stand-in B42 (buried torus void under an intact cap), "
                        "docs/model_assumptions.md; geometry confirmed by Ali 2026-09-24"),
    study_caps_A=(5.0, 10.0, 20.0, 30.0),   # the cell depth is sized for the deepest cap
    periods_y=27,            # as T1: 146.63 A >= 2R + 2r + 20 A = 144 A
    periods_z=276,           # as T1: 1498.93 A crystal length along the beam
    # smallest depth satisfying F5 (forward.feature_cell) for the deepest study cap (30 A):
    # clean = (74 - 1) a/4 - 15 A = 84.114 A >= max(65, 30 + 2 r + 30 = 84) A (asserted below)
    depth_layers=74,
    ring_margin_A=2 * A,
    structure_vacuum_A=10.0,
    vacuum_above_flat_surface_A=60.0, bulk_absorber_A=15.0, top_absorber_A=10.0,
    entrance_vacuum_slices=20,
    beam=dict(height_A=22.0, edge_A=2.0, bottom_above_flat_surface_at_launch_A=1.0),
    absorber=dict(strength_V=100.0, profile="sin2"),     # NUMERICAL (not physical), as T1
    physical_absorption={
        "test_only_r0.1": dict(
            model="proportional", ratio=0.1,
            label="TEST_ONLY: proportional absorption V_imag = 0.1 V_real, a numerical stand-in "
                  "for PROJECT_INPUT item 21 (not supplied) in the T3 buried-void demo only (the "
                  "value used by H2, P2 and S5); not a sourced property of Si, not comparable to "
                  "experiment (B30-style stand-in; H2 2.5: amplitude 1/e path 987 A)"),
        "none": dict(model="proportional", ratio=0.0,
                     label="ASSUMPTION B30: no physical absorption (PROJECT_INPUT item 21 not "
                           "supplied)"),
    },
    static_lattice_label="ASSUMPTION: static lattice (no frozen phonons) for the buried-void "
                         "demo runs",
    theta_label="ASSUMPTION B32: external angle of the (0,0,8) internal Bragg condition computed "
                "with the engine's mean inner potential (stands in for PROJECT_INPUT item 7)",
    working_reflection_hkl=(0, 0, 8),
    working_reflection_label="ASSUMPTION B17: (0,0,8) working condition (stands in for "
                             "PROJECT_INPUT item 9); asserted inside the band (H2 N8, H5 A7)",
    buildup_depth_A=20.0, footprint_margin_A=100.0,
    max_pixel_A=0.13, slices_per_period=4, propagator="exact", band_limit="2/3",
    # 2 FFT workers (T1: 4): two engine processes share the 4-core machine without
    # oversubscription; the environment must set OMP/OPENBLAS/MKL/NUMEXPR_NUM_THREADS=2 (manifest
    # thread check); the exit wave does not depend on the worker count
    backend="numpy", precision="complex128", threads=2,
    limits=dict(cpu_seconds=None, memory_bytes=3e9, cpu_calibration_factor=1.5,
                note="--max-cpu-seconds is REQUIRED for the buried kinds (no default); memory "
                     "limit 3 GB per process (orchestrator), applied to the engine estimate; the "
                     "builder's peak RSS is recorded in the summary"),
)


def buried_min_depth_layers(q_A: float, bulk_absorber_A: float, r_A: float, cap_max_A: float) -> int:
    """Smallest depth_layers whose clean depth (depth_layers - 1) q - bulk absorber satisfies F5
    for the deepest cap (forward.feature_cell BURIED_MIN_CLEAN_BELOW_*)."""
    need = max(BURIED_MIN_CLEAN_BELOW_SURFACE_A,
               cap_max_A + 2.0 * r_A + BURIED_MIN_CLEAN_BELOW_VOID_A) + bulk_absorber_A
    return int(np.ceil(need / q_A - 1e-12)) + 1


_bc = BURIED_CASE
if _bc["depth_layers"] != buried_min_depth_layers(A / 4.0, _bc["bulk_absorber_A"],
                                                  _bc["feature"]["minor_radius_A"],
                                                  max(_bc["study_caps_A"])):
    raise RuntimeError("BURIED_CASE depth_layers is not the smallest depth satisfying F5")


def run_name(kind: str, cap_A, absorption) -> str:
    if kind not in BURIED_KINDS:
        return kind
    tag = {"test_only_r0.1": "r010", "none": "r000"}[absorption]
    return f"buried_flat_{tag}" if kind == "buried_flat" else f"buried_cap{cap_A:g}A_{tag}"


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def build_structure(kind: str, cap_A=None):
    c = BURIED_CASE if kind in BURIED_KINDS else CASE
    Ly = c["periods_y"] * A
    Lz = c["periods_z"] * A
    common = dict(azimuth_uvw=c["azimuth_uvw"], azimuth_label=c["azimuth_label"], extent_y_A=Ly,
                  extent_z_A=Lz, depth_layers=c["depth_layers"],
                  lattice_parameter_A=c["lattice_parameter_A"], lattice_label=c["lattice_label"],
                  vacuum_above_A=c["structure_vacuum_A"])
    if kind in ("flat", "buried_flat"):
        return build_si001_flat_reference(**common)
    f = c["feature"]
    if kind == "buried":
        feat = BuriedTorus(center_y_A=0.5 * Ly, center_z_A=f["center_z_A"],
                           major_radius_A=f["major_radius_A"], minor_radius_A=f["minor_radius_A"],
                           cap_A=float(cap_A), label=f["label"], source=f["source"])
        return build_si001_with_feature(feature=feat, ring_margin_A=c["ring_margin_A"], **common)
    feat = HalfTorus(center_y_A=0.5 * Ly, center_z_A=f["center_z_A"],
                     major_radius_A=f["major_radius_A"], minor_radius_A=f["minor_radius_A"],
                     kind=kind, label=f["label"], source=f["source"][kind])
    return build_si001_with_feature(feature=feat, ring_margin_A=c["ring_margin_A"], **common)


def _jsonable(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, tuple):
        return list(o)
    return str(o)


def setup(kind: str, out: Path, cap_A=None, absorption=None):
    buried = kind in BURIED_KINDS
    c = BURIED_CASE if buried else CASE
    name = run_name(kind, cap_A, absorption)
    status = BURIED_STATUS if buried else STATUS
    t0 = time.perf_counter()
    s = build_structure(kind, cap_A)
    t_build = time.perf_counter() - t0
    rss_build = _rss_mb()
    q = A / 4.0
    dz = A / c["slices_per_period"]
    depth_below = (c["depth_layers"] - 1) * q
    cell = build_feature_reflection_cell(
        s, vacuum_above_flat_surface_A=c["vacuum_above_flat_surface_A"],
        depth_below_A=depth_below, bulk_absorber_A=c["bulk_absorber_A"],
        top_absorber_A=c["top_absorber_A"], entrance_vacuum_z_A=c["entrance_vacuum_slices"] * dz)
    abs_ = c["physical_absorption"][absorption] if buried else c["physical_absorption"]
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(**abs_),
                          frozen_phonons=None, static_lattice_label=c["static_lattice_label"])
    V0 = potential_mean_inner_potential_V(pot)
    from abtem.parametrizations import KirklandParametrization
    V0_check = 8.0 / A ** 3 * float(KirklandParametrization().projected_scattering_factor("Si")(
        np.array([0.0]))[0])
    if abs(V0 - V0_check) > 5e-4:                                  # B32: asserted to 5e-4 V
        raise RuntimeError(f"engine MIP {V0} V != independent value {V0_check} V")
    sc = specular_condition_for(c["working_reflection_hkl"], (0, 0, 1), E_keV=c["energy_keV"],
                                V0_V=V0, a_A=A)
    theta = float(sc.theta_ext)
    x_flat = cell.metadata["layout"]["highest_surface_x_A"]
    b = c["beam"]
    beam = SheetBeam(height_A=b["height_A"], edge_A=b["edge_A"],
                     x_bottom_A=x_flat + b["bottom_above_flat_surface_at_launch_A"],
                     theta_in_ext_rad=theta, theta_label=c["theta_label"])
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / c["max_pixel_A"] - 1e-9)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / c["max_pixel_A"] - 1e-9)))
    params = MultisliceParams(energy_keV=c["energy_keV"], nx=nx, ny=ny, dz_A=dz,
                              propagator=c["propagator"], band_limit=c["band_limit"],
                              backend=c["backend"], precision=c["precision"],
                              threads=c["threads"],
                              absorber=NumericalAbsorber(**c["absorber"]),
                              theta_out_ext_rad=theta, buildup_depth_A=c["buildup_depth_A"],
                              working_reflections_hkl=(c["working_reflection_hkl"],))
    engine_setup = reflection_setup(cell, potential=pot, beam=beam, params=params)
    feat_checks = None
    if kind not in ("flat", "buried_flat"):
        feat_checks = check_feature_geometry(cell, beam=beam, theta_out_ext_rad=theta,
                                             theta_int_rad=engine_setup["theta_int_in_rad"],
                                             buildup_depth_A=c["buildup_depth_A"],
                                             footprint_margin_A=c["footprint_margin_A"])
        f4 = feat_checks["F4_conservative_reading"]
        if f4["ring_start_fraction_of_crystal"] < 0.5:
            raise RuntimeError("the ring must lie in the downstream half of the crystal")
    # structure file (read by tools/plots/torus_atomistic.py; hashed into the run manifest)
    out.mkdir(parents=True, exist_ok=True)
    spath = out / f"structure_{name}.npz"
    if spath.exists():
        raise FileExistsError(f"refusing to overwrite {spath}")
    extra = dict(cap_A=np.array(np.nan if cap_A is None else float(cap_A)),
                 physical_absorption_json=np.array(json.dumps(abs_))) if buried else {}
    np.savez(spath, schema=np.array("T3 buried torus structure/1" if buried
                                    else "T1 torus structure/1"), positions_A=s.positions_A,
             feature_sites_A=s.feature_sites_A, cell_A=s.cell_A,
             axes=np.array(["x: outward normal [001]", "y: z cross x", "z: beam azimuth"]),
             units=np.array("angstrom"),
             # reflection-cell coordinates = structure coordinates - this shift
             structure_to_cell_shift_A=np.array([s.metadata["terrace_map"][0]["top_height_A"]
                                                 - depth_below, 0.0,
                                                 -cell.crystal_start_z_A]),
             metadata_json=np.array(json.dumps(s.metadata, default=_jsonable)),
             cell_feature_json=np.array(json.dumps(cell.metadata["feature"], default=_jsonable)),
             status=np.array(status), **extra)
    rec = dict(kind=kind, status=status, n_atoms=int(len(cell.Z)),
               n_atoms_structure=s.n_atoms, structure_build_s=t_build,
               structure_assertions=s.metadata["assertions_passed"],
               structure_checks=s.metadata["checks"], feature=s.metadata["feature"],
               cell_feature=cell.metadata["feature"],
               cell=dict(extent_x_A=cell.extent_x_A, extent_y_A=cell.extent_y_A,
                         length_z_A=cell.length_z_A, crystal_start_z_A=cell.crystal_start_z_A,
                         layout=cell.metadata["layout"]),
               mean_inner_potential_V=V0, theta_ext_rad=theta,
               theta_int_rad=engine_setup["theta_int_in_rad"],
               beam=beam.describe(engine_setup["bc"]["wavelength_A"]),
               grid=dict(nx=nx, ny=ny, dx_A=engine_setup["grid"].dx_A,
                         dy_A=engine_setup["grid"].dy_A),
               n_slices=engine_setup["n_slices"], band=engine_setup["band"],
               engine_geometry_checks=engine_setup["geometry"], feature_geometry_checks=feat_checks,
               structure_file=str(spath))
    if buried:
        rec.update(name=name, cap_A=cap_A, absorption=absorption, physical_absorption=abs_,
                   peak_rss_after_structure_build_MB=rss_build,
                   cell_depth_rule=dict(
                       depth_layers=c["depth_layers"],
                       clean_below_surface_A=float(cell.metadata["layout"]["lowest_surface_x_A"]
                                                   - cell.metadata["layout"]["bulk_absorber_x_A"][1]),
                       required_below_surface_A=BURIED_MIN_CLEAN_BELOW_SURFACE_A,
                       required_below_void_bottom_A=BURIED_MIN_CLEAN_BELOW_VOID_A,
                       deepest_study_cap_A=max(c["study_caps_A"])))
    return s, cell, pot, beam, params, rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kind", required=True, choices=("trench", "ridge", "flat") + BURIED_KINDS)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("--max-cpu-seconds", type=float, default=None,
                    help="refuse above this calibrated CPU estimate (s); default for trench, "
                         "ridge and flat: CASE limits cpu_seconds (600 s, set for the build "
                         "machine); REQUIRED for the buried kinds. Batch jobs pass a value "
                         "derived from their walltime (scripts/hpc/alliance); recorded in "
                         "case_<name>.json and summary_<name>.json")
    ap.add_argument("--cap-A", type=float, default=None,
                    help="kind buried only (required there): intact crystal between the top atomic "
                         "plane of the flat surface and the top of the void (A)")
    ap.add_argument("--absorption", choices=tuple(BURIED_CASE["physical_absorption"]),
                    default=None,
                    help="buried kinds only (required there): 'test_only_r0.1' (TEST_ONLY "
                         "proportional r = 0.1) or 'none' (ASSUMPTION B30)")
    args = ap.parse_args(argv)
    out = args.out
    kind = args.kind
    buried = kind in BURIED_KINDS
    if kind == "buried":
        if args.cap_A is None:
            ap.error("--cap-A is required for --kind buried (no default)")
        if not (np.isfinite(args.cap_A) and args.cap_A > 0):
            ap.error("--cap-A must be finite and > 0")
    elif args.cap_A is not None:
        ap.error(f"--cap-A is only for --kind buried, not {kind}")
    if buried and args.absorption is None:
        ap.error(f"--absorption is required for --kind {kind} (no default)")
    if not buried and args.absorption is not None:
        ap.error(f"--absorption is only for the buried kinds; {kind} uses the T1 CASE (B30)")
    if buried and args.max_cpu_seconds is None:
        ap.error(f"--max-cpu-seconds is required for --kind {kind} (no default)")
    case = BURIED_CASE if buried else CASE
    name = run_name(kind, args.cap_A, args.absorption)
    status = BURIED_STATUS if buried else STATUS
    lim = dict(case["limits"])
    if args.max_cpu_seconds is None:
        lim["cpu_seconds_source"] = "CASE default (build machine)"
    else:
        if not args.max_cpu_seconds > 0:
            ap.error("--max-cpu-seconds must be > 0")
        lim["cpu_seconds"] = float(args.max_cpu_seconds)
        lim["cpu_seconds_source"] = "--max-cpu-seconds (caller)"
    t0 = time.perf_counter()
    s, cell, pot, beam, params, rec = setup(kind, out, args.cap_A, args.absorption)
    est = estimate_resources(cell, params, realisations=1, calibrate_cpu=True)
    cpu_s = est["cpu"]["seconds_per_realisation"] * lim["cpu_calibration_factor"]
    mem = est["memory_bytes"]["total"]
    rec["estimate"] = dict(cpu_seconds_calibrated=cpu_s, raw=est, rss_after_setup_MB=_rss_mb())
    rec["limits_used"] = lim
    print(f"[{name}] atoms {rec['n_atoms']}, grid {params.nx} x {params.ny} (dx {rec['grid']['dx_A']:.4f}, "
          f"dy {rec['grid']['dy_A']:.4f} A), {rec['n_slices']} slices of {params.dz_A:.4f} A, "
          f"theta {rec['theta_ext_rad'] * 1e3:.4f} mrad, MIP {rec['mean_inner_potential_V']:.4f} V")
    print(f"[{name}] estimate: CPU {cpu_s:.0f} s (x{lim['cpu_calibration_factor']}), engine arrays "
          f"{mem / 1e6:.0f} MB, RSS after setup {_rss_mb():.0f} MB; limits CPU "
          f"{lim['cpu_seconds']:.0f} s ({lim['cpu_seconds_source']}), memory "
          f"{lim['memory_bytes'] / 1e9:.0f} GB")
    over = cpu_s > lim["cpu_seconds"] or mem > lim["memory_bytes"]
    rec["over_limits"] = bool(over)
    case_rec = dict(CASE=case, kind=kind, status=status, limits_used=lim)
    if buried:
        case_rec.update(name=name, cap_A=args.cap_A, absorption=args.absorption)
    (out / f"case_{name}.json").write_text(json.dumps(case_rec, indent=2, default=_jsonable))
    if args.estimate_only or over:
        if over:
            print(f"[{name}] REFUSED: estimate exceeds the limits {lim}; shrink the cell")
        (out / f"summary_{name}.json").write_text(json.dumps(rec, indent=2, default=_jsonable))
        return 2 if over else 0
    t1 = time.perf_counter()
    purpose = ("buried torus void study T3 (Ali, 2026-09-24), DEMO, detectability only, not "
               "comparable to experiment" if buried else
               "half-torus smoke test T1 (Ali), DEMO, not comparable to experiment")
    waves, manifest = simulate(cell, potential=pot, beam=beam, params=params, realisations=1,
                               seed=None, outputs_root=out / "outputs", run_name=f"torus_{name}",
                               save_waves=True, config=out / f"case_{name}.json",
                               input_paths=[Path(rec["structure_file"])],
                               caller_record=dict(purpose=purpose,
                                                  status=status, kind=kind,
                                                  feature=rec["cell_feature"],
                                                  structure_positions_sha256=s.metadata[
                                                      "positions_sha256"]))
    t2 = time.perf_counter()
    rec["run"] = dict(simulate_s=t2 - t1, total_s=t2 - t0, peak_rss_MB=_rss_mb(),
                      manifest=str(manifest),
                      exit_waves=sorted(str(p) for p in (out / "outputs" / "exit_waves")
                                        .glob("*.npz")),
                      engine_timing_s=waves[0].metadata["timing_s"],
                      potential_realised=waves[0].metadata["potential"]["realised"])
    (out / f"summary_{name}.json").write_text(json.dumps(rec, indent=2, default=_jsonable))
    print(f"[{name}] simulate {t2 - t1:.1f} s, total {t2 - t0:.1f} s, peak RSS {_rss_mb():.0f} MB, "
          f"manifest {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
