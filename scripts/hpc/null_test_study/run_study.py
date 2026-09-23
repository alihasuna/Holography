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

Every value in study.yaml is required (no defaults). TEST_ONLY labels mark stand-ins for
PROJECT_INPUT items (azimuth item 8, angle item 7, absorption item 21). Status: UNVALIDATED engine
(rung 2 and the abTEM multislice cross-check not run).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tests" / "forward"))

from null_test_cases import (run_translation, step_case, step_phase_rows,  # noqa: E402
                             theta_0008, translation_pair)
from reflection_holo.forward.multislice import (PhysicalAbsorption, estimate_resources,  # noqa: E402
                                                run_realisation)
from reflection_holo.provenance.manifest import build_manifest, write_manifest  # noqa: E402

KINDS = ("translation_fixed_beam", "translation_moved_beam", "step_parallel")
POINT_KEYS = ("name", "kind", "theta", "extra_length_A", "width_periods", "absorption_ratio",
              "absorption_label", "precision")
RUNTIME_KEYS = ("backend", "threads")
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


def _build(p, rt):
    th = _theta(p["theta"])
    ab = _absorption(p)
    if p["kind"].startswith("translation"):
        pair = translation_pair(theta=th, width_periods=int(p["width_periods"]),
                                extra_A=float(p["extra_length_A"]), absorption=ab,
                                precision=p["precision"],
                                move_beam=p["kind"] == "translation_moved_beam")
        pair["params"] = dataclasses.replace(pair["params"], backend=rt["backend"],
                                             threads=int(rt["threads"]))
        return th, pair
    cell, pot, beam, params = step_case(theta=th, width_periods=int(p["width_periods"]),
                                        extra_A=float(p["extra_length_A"]), absorption=ab,
                                        precision=p["precision"])
    params = dataclasses.replace(params, backend=rt["backend"], threads=int(rt["threads"]))
    return th, (cell, pot, beam, params)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--only", default=None)
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(Path(a.config).read_text())
    rt = cfg["runtime"]
    for k in RUNTIME_KEYS:
        if k not in rt:
            raise SystemExit(f"runtime.{k} is required")
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
        if a.only and p["name"] != a.only:
            continue
        th, obj = _build(p, rt)
        if p["kind"].startswith("translation"):
            cell, params = obj["A"][0], obj["params"]
            n_runs = 2
        else:
            cell, params = obj[0], obj[3]
            n_runs = 1
        est = estimate_resources(cell, params, realisations=n_runs,
                                 calibrate_cpu=rt["backend"] == "numpy")
        line = (f"{p['name']}: grid {est['grid']['nx']}x{est['grid']['ny']}, {est['n_slices']} "
                f"slices, {est['n_atoms']} atoms, engine arrays "
                f"{est['memory_bytes']['total'] / 1e6:.0f} MB, ")
        if "cpu" in est:
            line += f"CPU ~{est['cpu']['seconds_total'] * 1.5:.0f} s (x1.5 calibration), "
        line += f"GPU ~{est['gpu']['seconds_total']:.1f} s (ASSUMPTION model)"
        print(line, flush=True)
        if a.estimate:
            continue
        t0 = time.time()
        if p["kind"].startswith("translation"):
            res = run_translation(obj)
            res["grid"] = list(res["grid"])
        else:
            cell, pot, beam, params = obj
            ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0,
                                 seed=None)
            geo, rows = step_phase_rows(ew, cell, th, apertures=p["apertures_per_A"],
                                        window_offsets_A=p["window_offsets_A"],
                                        window_width_A=p["window_width_A"])
            res = dict(geometric_rad=geo, rows=rows, n_slices=ew.metadata["slices"]["n_slices"],
                       grid=[params.nx, params.ny])
        res.update(point=p, theta_rad=th, wall_s=time.time() - t0, estimate=est)
        path = out / "null_test_study" / f"{p['name']}.json"
        path.write_text(json.dumps(res, indent=1, default=str))
        m = build_manifest(run_name=f"null_test_{p['name']}", config=Path(a.config),
                           input_paths=[path], seeds={}, thread_count=int(rt["threads"]),
                           precision={"complex": p["precision"]},
                           engines={"reflection_holo.forward.multislice": dict(
                               status="UNVALIDATED (M2 report)")},
                           wave_planes={"exit_wave": "exit plane z = L_z (no further "
                                                     "propagation)"},
                           beam_energy_keV=200.0, extra=dict(point=p))
        print(f"  -> {path} ({res['wall_s']:.0f} s), manifest {write_manifest(m, outputs_root=out)}",
              flush=True)


if __name__ == "__main__":
    main()
