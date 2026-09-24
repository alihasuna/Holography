#!/usr/bin/env python
"""Atomistic a/2 null-test study for the HPC (M2 report, section "Atomistic null-test diagnosis").

Runs the points of a study YAML (study.yaml next to this file): whole-crystal translation of a
flat Si(001) terrace with the beam fixed (tests convergence of the contact-position dependence
with cell length) or moved (covariant control), and a/2 steps with edges parallel to the beam
(terrace width, window distance from the edge, aperture, angle, absorption). Every point writes a
JSON result and a run manifest (reflection_holo.provenance.manifest) under <out>/outputs/.

Usage (repository root, venv from scripts/hpc/setup_env.sh):
    venv/bin/python scripts/hpc/null_test_study/run_study.py --config scripts/hpc/null_test_study/study.yaml \
        --out /path/to/scratch --estimate            # print estimate_resources per point, no run
    venv/bin/python scripts/hpc/null_test_study/run_study.py --config ... --out ... [--only NAME]

Every value in a study file is required (no defaults): per point also `clean_depth_A` (crystal
between the lowest surface and the 15 A bulk absorber; study.yaml carries the LEGACY M2 value 21 A,
shallower than the 24.5 A extinction depth, P2 6.5), `azimuth` ("110" or "100") and the sheet beam
`beam_height_A`, `beam_edge_A`, `beam_gap_A` (full height, sin^2 edge width, bottom edge above the
highest surface at the entrance plane; study.yaml carries the LEGACY M2 beam 8/2/2 A, formerly a
silent default; study_depth100.yaml a beam lit to the exit plane, H = L_z tan(theta) - gap - a/2 -
1 A, H2 2.6; audit A6 N-1/N-3); at the top level `build.tile_above_periods` (flat terraces and
parallel steps longer than this many periods are built as one verified period and tiled along z,
exact; 400 in study.yaml as in M2). An optional top-level `surface_resolved` block (all keys of
null_test_cases.RESOLVED_KEYS, including the amplitude floor `amp_floor_rel`) adds the
surface-position-resolved read-out of H2 section 2.4 to every translation point (N12); a
translation point whose beam meets either crystal before L_z - exit_excl_A is then refused
(null_test_cases.check_lit_to_exit, also with --estimate); without the block that read-out is not
computed (and the result says so). TEST_ONLY labels mark stand-ins for PROJECT_INPUT items (azimuth
item 8, angle item 7, absorption item 21). Status: UNVALIDATED engine. Ladder rungs 1 and 2 (R2-A)
pass; rung 3 has passed ONLY for the continuum null tests and the atomistic MOVED-beam translation:
the atomistic FIXED-beam translation check that docs/05 4.4 item 3 requires before any step-phase
run has NOT passed (this study is meant to test it); the abTEM multislice cross-check is not run.
Study files: study.yaml (the M2 reproduction set, legacy clean depth), study_depth100.yaml (clean
depth >= 100 A, r >= 0.05, [110] and exact [100], surface-resolved read-out; E1 wave 2a).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tests" / "forward"))

from null_test_cases import (AZIMUTHS, RESOLVED_KEYS, check_lit_to_exit,  # noqa: E402
                             run_translation, step_case, step_phase_rows, theta_0008,
                             translation_pair)
from reflection_holo.forward.multislice import (PhysicalAbsorption, estimate_resources,  # noqa: E402
                                                run_realisation)
from reflection_holo.io.config import load_yaml_unique  # noqa: E402
from reflection_holo.provenance.manifest import build_manifest, write_manifest  # noqa: E402

# The study feeds TEST_ONLY stand-ins from study.yaml straight to the engine: it is an engine null
# test, never a pipeline run, and says so in every result and manifest (audit A3 m7).
STUDY_PURPOSE = ("engine null test with TEST_ONLY stand-ins read from the study file (not a "
                 "pipeline run, bypasses the pipeline gate); not comparable to experiment")

KINDS = ("translation_fixed_beam", "translation_moved_beam", "step_parallel")
POINT_KEYS = ("name", "kind", "theta", "extra_length_A", "width_periods", "absorption_ratio",
              "absorption_label", "precision", "clean_depth_A", "azimuth", "beam_height_A",
              "beam_edge_A", "beam_gap_A")
RUNTIME_KEYS = ("backend", "threads")
BUILD_KEYS = ("tile_above_periods",)
STEP_KEYS = ("apertures_per_A", "window_offsets_A", "window_width_A")


def _theta(v) -> float:
    if v == "bragg_0008_mip":
        return theta_0008()
    return float(v) * 1e-3                     # mrad


def _absorption(p):
    if p["absorption_ratio"] == 0:
        return PhysicalAbsorption(model="proportional", ratio=0.0, label=p["absorption_label"])
    return PhysicalAbsorption(model="proportional", ratio=float(p["absorption_ratio"]),
                              label=p["absorption_label"])


def _build(p, rt, build):
    th = _theta(p["theta"])
    ab = _absorption(p)
    cellkw = dict(clean_depth_A=float(p["clean_depth_A"]), azimuth=str(p["azimuth"]),
                  tile_above_periods=int(build["tile_above_periods"]),
                  H=float(p["beam_height_A"]), edge=float(p["beam_edge_A"]),
                  gap=float(p["beam_gap_A"]))
    if p["kind"].startswith("translation"):
        pair = translation_pair(theta=th, width_periods=int(p["width_periods"]),
                                extra_A=float(p["extra_length_A"]), absorption=ab,
                                precision=p["precision"],
                                move_beam=p["kind"] == "translation_moved_beam", **cellkw)
        pair["params"] = dataclasses.replace(pair["params"], backend=rt["backend"],
                                             threads=int(rt["threads"]))
        return th, pair
    cell, pot, beam, params = step_case(theta=th, width_periods=int(p["width_periods"]),
                                        extra_A=float(p["extra_length_A"]), absorption=ab,
                                        precision=p["precision"], **cellkw)
    params = dataclasses.replace(params, backend=rt["backend"], threads=int(rt["threads"]))
    return th, (cell, pot, beam, params)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--only", default=None)
    a = ap.parse_args(argv)
    cfg = load_yaml_unique(Path(a.config).read_bytes())      # duplicate keys refused (A3 m7)
    rt = cfg["runtime"]
    for k in RUNTIME_KEYS:
        if k not in rt:
            raise SystemExit(f"runtime.{k} is required")
    build = cfg.get("build")
    if not isinstance(build, dict) or any(k not in build for k in BUILD_KEYS):
        raise SystemExit(f"build.{BUILD_KEYS} is required (study.yaml: tile_above_periods 400, "
                         f"as in M2)")
    resolved = cfg.get("surface_resolved")
    if resolved is not None:
        bad = sorted(set(RESOLVED_KEYS) ^ set(resolved))
        if bad:
            raise SystemExit(f"surface_resolved must have exactly the keys {RESOLVED_KEYS}; "
                             f"missing or unknown: {bad}")
        resolved = {k: float(resolved[k]) for k in RESOLVED_KEYS}
    out = Path(a.out) / "outputs"
    (out / "null_test_study").mkdir(parents=True, exist_ok=True)
    for p in cfg["points"]:
        miss = [k for k in POINT_KEYS if k not in p]
        if p.get("kind") == "step_parallel":
            miss += [k for k in STEP_KEYS if k not in p]
        if miss:
            raise SystemExit(f"point {p.get('name')}: missing keys {miss}")
        if p["kind"] not in KINDS:
            raise SystemExit(f"point {p['name']}: kind must be one of {KINDS}")
        if str(p["azimuth"]) not in AZIMUTHS:
            raise SystemExit(f"point {p['name']}: azimuth must be one of {tuple(AZIMUTHS)}")
        if not float(p["clean_depth_A"]) > 0:
            raise SystemExit(f"point {p['name']}: clean_depth_A must be > 0")
        for k in ("beam_height_A", "beam_edge_A", "beam_gap_A"):
            if isinstance(p[k], bool) or not float(p[k]) > 0:
                raise SystemExit(f"point {p['name']}: {k} must be a number > 0")
        if a.only and p["name"] != a.only:
            continue
        path = out / "null_test_study" / f"{p['name']}.json"
        if path.exists() and not a.estimate:
            raise SystemExit(f"{path} exists: results are never overwritten (audit A3 m7); use "
                             f"another --out")
        th, obj = _build(p, rt, build)
        if p["kind"].startswith("translation"):
            cell, params = obj["A"][0], obj["params"]
            n_runs = 2
            if resolved is not None:                     # A6 N-1: lit up to the read-out window
                try:
                    check_lit_to_exit(obj, exit_excl_A=resolved["exit_excl_A"])
                except ValueError as exc:
                    raise SystemExit(f"point {p['name']}: {exc}") from None
        else:
            cell, params = obj[0], obj[3]
            n_runs = 1
        est = estimate_resources(cell, params, realisations=n_runs,
                                 calibrate_cpu=rt["backend"] == "numpy")
        line = (f"{p['name']}: [{p['azimuth']}] clean depth {float(p['clean_depth_A']):g} A, "
                f"beam H {float(p['beam_height_A']):g} A, L_z {cell.length_z_A:.1f} A, "
                f"grid {est['grid']['nx']}x{est['grid']['ny']}, {est['n_slices']} "
                f"slices, {est['n_atoms']} atoms, memory peak "
                f"{est['memory_bytes']['total'] / 1e6:.0f} MB (numpy/CPU; GPU device "
                f"{est['memory_bytes']['device_peak_cupy'] / 1e6:.0f} MB, lower bound), ")
        if "cpu" in est:
            line += f"CPU ~{est['cpu']['seconds_total'] * 1.5:.0f} s (x1.5 calibration), "
        line += f"GPU ~{est['gpu']['seconds_total']:.1f} s (ASSUMPTION model)"
        print(line, flush=True)
        if a.estimate:
            continue
        t0 = time.time()
        if p["kind"].startswith("translation"):
            res = run_translation(obj, surface_resolved=resolved)
            res["grid"] = list(res["grid"])
            if resolved is None:
                res["surface_resolved"] = ("not computed: no surface_resolved block in the study "
                                           "file")
        else:
            cell, pot, beam, params = obj
            ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0,
                                 seed=None)
            geo, rows = step_phase_rows(ew, cell, th, apertures=p["apertures_per_A"],
                                        window_offsets_A=p["window_offsets_A"],
                                        window_width_A=p["window_width_A"])
            res = dict(geometric_rad=geo, rows=rows, n_slices=ew.metadata["slices"]["n_slices"],
                       grid=[params.nx, params.ny])
        res.update(point=p, theta_rad=th, wall_s=time.time() - t0, estimate=est,
                   purpose=STUDY_PURPOSE, test_only=True)
        with open(path, "x", encoding="utf-8") as fh:        # never overwrite (A3 m7)
            fh.write(json.dumps(res, indent=1, default=str))
        m = build_manifest(run_name=f"null_test_{p['name']}", config=Path(a.config),
                           input_paths=[path], seeds={}, thread_count=int(rt["threads"]),
                           precision={"complex": p["precision"]},
                           engines={"reflection_holo.forward.multislice": dict(
                               status="UNVALIDATED (M2 report)")},
                           wave_planes={"exit_wave": "exit plane z = L_z (no further "
                                                     "propagation)"},
                           beam_energy_keV=200.0,
                           extra=dict(point=p, purpose=STUDY_PURPOSE, test_only=True))
        print(f"  -> {path} ({res['wall_s']:.0f} s), manifest {write_manifest(m, outputs_root=out)}",
              flush=True)


if __name__ == "__main__":
    main()
