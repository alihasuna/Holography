#!/usr/bin/env python3
"""Half-torus smoke test T1: atomistic Si(001) structure with a ring trench or ridge (or the flat
reference) and a small grazing-incidence multislice run at 200 keV.

STATUS OF EVERY OUTPUT: UNVALIDATED. The reflection has not converged along the beam in a cell of
this length (finite-cell build-up), there is no physical absorption (ASSUMPTION B30), and the
engine's rung 2 and abTEM cross-check were not run (docs/agent_reports/M2_multislice_engine.md
section 10). Demo stand-ins: azimuth [100] (B20), feature geometry (B33 trench, B34 ridge; PROJECT_INPUT
item 13), glancing angle from the engine's mean inner potential (B32), lattice parameter (B2).

Usage (threads fixed by the environment so the manifest's thread check is consistent):
  OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
  venv/bin/python scripts/torus/run_torus_multislice.py --kind trench --out <dir> [--estimate-only]
Writes into <dir>: case_<kind>.json (every input with its label), structure_<kind>.npz (atoms,
feature sites, cell, metadata), summary_<kind>.json, and outputs/exit_waves/ and
outputs/manifests/ written by the engine (the manifest writer requires a directory named outputs).
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
from reflection_holo.structure.shapes import HalfTorus

STATUS = ("UNVALIDATED: finite-cell build-up not converged along z, no physical absorption "
          "(ASSUMPTION B30), engine rung 2 and abTEM cross-check NOT RUN (report M2 section 10). "
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
    buildup_depth_A=20.0, footprint_margin_A=100.0,
    max_pixel_A=0.13, slices_per_period=4, propagator="exact", band_limit="2/3",
    backend="numpy", precision="complex128", threads=4,
    limits=dict(cpu_seconds=600.0, memory_bytes=10e9, cpu_calibration_factor=1.5,
                note="about 10 minutes and 10 GB on this machine (orchestrator); CPU estimate x1.5 "
                     "(M2 report section 7 calibration)"),
)


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def build_structure(kind: str):
    c = CASE
    Ly = c["periods_y"] * A
    Lz = c["periods_z"] * A
    common = dict(azimuth_uvw=c["azimuth_uvw"], azimuth_label=c["azimuth_label"], extent_y_A=Ly,
                  extent_z_A=Lz, depth_layers=c["depth_layers"],
                  lattice_parameter_A=c["lattice_parameter_A"], lattice_label=c["lattice_label"],
                  vacuum_above_A=c["structure_vacuum_A"])
    if kind == "flat":
        return build_si001_flat_reference(**common)
    f = c["feature"]
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


def setup(kind: str, out: Path):
    c = CASE
    t0 = time.perf_counter()
    s = build_structure(kind)
    t_build = time.perf_counter() - t0
    q = A / 4.0
    dz = A / c["slices_per_period"]
    depth_below = (c["depth_layers"] - 1) * q
    cell = build_feature_reflection_cell(
        s, vacuum_above_flat_surface_A=c["vacuum_above_flat_surface_A"],
        depth_below_A=depth_below, bulk_absorber_A=c["bulk_absorber_A"],
        top_absorber_A=c["top_absorber_A"], entrance_vacuum_z_A=c["entrance_vacuum_slices"] * dz)
    abs_ = c["physical_absorption"]
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(**abs_),
                          frozen_phonons=None, static_lattice_label=c["static_lattice_label"])
    V0 = potential_mean_inner_potential_V(pot)
    from abtem.parametrizations import KirklandParametrization
    V0_check = 8.0 / A ** 3 * float(KirklandParametrization().projected_scattering_factor("Si")(
        np.array([0.0]))[0])
    if abs(V0 - V0_check) > 5e-4:                                  # B32: asserted to 5e-4 V
        raise RuntimeError(f"engine MIP {V0} V != independent value {V0_check} V")
    sc = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=c["energy_keV"], V0_V=V0, a_A=A)
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
                              theta_out_ext_rad=theta, buildup_depth_A=c["buildup_depth_A"])
    engine_setup = reflection_setup(cell, potential=pot, beam=beam, params=params)
    feat_checks = None
    if kind != "flat":
        feat_checks = check_feature_geometry(cell, beam=beam, theta_out_ext_rad=theta,
                                             theta_int_rad=engine_setup["theta_int_in_rad"],
                                             buildup_depth_A=c["buildup_depth_A"],
                                             footprint_margin_A=c["footprint_margin_A"])
        f4 = feat_checks["F4_conservative_reading"]
        if f4["ring_start_fraction_of_crystal"] < 0.5:
            raise RuntimeError("the ring must lie in the downstream half of the crystal")
    # structure file (read by tools/plots/torus_atomistic.py; hashed into the run manifest)
    out.mkdir(parents=True, exist_ok=True)
    spath = out / f"structure_{kind}.npz"
    if spath.exists():
        raise FileExistsError(f"refusing to overwrite {spath}")
    np.savez(spath, schema=np.array("T1 torus structure/1"), positions_A=s.positions_A,
             feature_sites_A=s.feature_sites_A, cell_A=s.cell_A,
             axes=np.array(["x: outward normal [001]", "y: z cross x", "z: beam azimuth"]),
             units=np.array("angstrom"),
             # reflection-cell coordinates = structure coordinates - this shift
             structure_to_cell_shift_A=np.array([s.metadata["terrace_map"][0]["top_height_A"]
                                                 - depth_below, 0.0,
                                                 -cell.crystal_start_z_A]),
             metadata_json=np.array(json.dumps(s.metadata, default=_jsonable)),
             cell_feature_json=np.array(json.dumps(cell.metadata["feature"], default=_jsonable)),
             status=np.array(STATUS))
    rec = dict(kind=kind, status=STATUS, n_atoms=int(len(cell.Z)),
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
    return s, cell, pot, beam, params, rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kind", required=True, choices=("trench", "ridge", "flat"))
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--estimate-only", action="store_true")
    args = ap.parse_args(argv)
    out = args.out
    kind = args.kind
    t0 = time.perf_counter()
    s, cell, pot, beam, params, rec = setup(kind, out)
    est = estimate_resources(cell, params, realisations=1, calibrate_cpu=True)
    lim = CASE["limits"]
    cpu_s = est["cpu"]["seconds_per_realisation"] * lim["cpu_calibration_factor"]
    mem = est["memory_bytes"]["total"]
    rec["estimate"] = dict(cpu_seconds_calibrated=cpu_s, raw=est, rss_after_setup_MB=_rss_mb())
    print(f"[{kind}] atoms {rec['n_atoms']}, grid {params.nx} x {params.ny} (dx {rec['grid']['dx_A']:.4f}, "
          f"dy {rec['grid']['dy_A']:.4f} A), {rec['n_slices']} slices of {params.dz_A:.4f} A, "
          f"theta {rec['theta_ext_rad'] * 1e3:.4f} mrad, MIP {rec['mean_inner_potential_V']:.4f} V")
    print(f"[{kind}] estimate: CPU {cpu_s:.0f} s (x{lim['cpu_calibration_factor']}), engine arrays "
          f"{mem / 1e6:.0f} MB, RSS after setup {_rss_mb():.0f} MB")
    over = cpu_s > lim["cpu_seconds"] or mem > lim["memory_bytes"]
    rec["over_limits"] = bool(over)
    (out / f"case_{kind}.json").write_text(json.dumps(dict(CASE=CASE, kind=kind, status=STATUS),
                                                      indent=2, default=_jsonable))
    if args.estimate_only or over:
        if over:
            print(f"[{kind}] REFUSED: estimate exceeds the limits {lim}; shrink the cell")
        (out / f"summary_{kind}.json").write_text(json.dumps(rec, indent=2, default=_jsonable))
        return 2 if over else 0
    t1 = time.perf_counter()
    waves, manifest = simulate(cell, potential=pot, beam=beam, params=params, realisations=1,
                               seed=None, outputs_root=out / "outputs", run_name=f"torus_{kind}",
                               save_waves=True, config=out / f"case_{kind}.json",
                               input_paths=[Path(rec["structure_file"])],
                               caller_record=dict(purpose="half-torus smoke test T1 (Ali), "
                                                          "DEMO, not comparable to experiment",
                                                  status=STATUS, kind=kind,
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
    (out / f"summary_{kind}.json").write_text(json.dumps(rec, indent=2, default=_jsonable))
    print(f"[{kind}] simulate {t2 - t1:.1f} s, total {t2 - t0:.1f} s, peak RSS {_rss_mb():.0f} MB, "
          f"manifest {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
