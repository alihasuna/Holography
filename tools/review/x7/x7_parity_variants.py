#!/usr/bin/env python3
"""X7 (re-audit A12 m3, orchestrator's decision 3): the two parity variants of the 2.0 nm item-12
record run through the pipeline in the geometric engine (variant oxide_2p0nm) and in the multislice
engine (variant multislice_tiny_oxide_2p0nm), and their arrays are compared (reproduces A12 D6 and
D7 with committed code).

The record: thickness, density and a-Si thickness labelled PROJECT_INPUT with a FABRICATED TEST
supply, V_ox, V'_ox and the widths under the model row B43, the item-12 uncertainties 1 A,
0.05 g/cm^3 and 0.1 A as half-widths (count interval [6, 7]), purpose demo (a comparison run is
refused for the demo's other stand-ins). Nothing here is an item-12 value.

What this shows: in the geometric engine the variants give byte-identical arrays (its layer phase
uses the continuum boundaries, which do not depend on the count); in the multislice engine they
differ. The multislice difference mixes the parity effect with the overlap of the lower variant
(+0.6838 A, not the nearest count) and the arrays are shifted by one layer, so the pointwise
differences printed are NOT a size of the parity effect. The physical effect of the overlap is NOT
computed here.

Usage:  PYTHONPATH=. venv/bin/python tools/review/x7/x7_parity_variants.py --out DIR
        DIR: a scratch directory outside the repository (never outputs/).
Saved:  tools/review/x7/x7_parity_variants_output.txt
"""
from __future__ import annotations

import argparse
import copy
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
import reflection_holo                                                   # noqa: E402
from reflection_holo.pipeline import load_pipeline_dict, read_pipeline_file, run  # noqa: E402
from reflection_holo.pipeline.config import oxide_item12_record          # noqa: E402

SUPPLY = dict(label="PROJECT_INPUT", supplied_by="Agent X7", supplied_on="2026-09-24",
              source="TEST: fabricated supply (report X7, re-audit A12 m3)")
LABELS = dict(thickness="PROJECT_INPUT", density="PROJECT_INPUT", amorphous_si="PROJECT_INPUT",
              consumed_layers="DERIVED_HERE", V_real="ASSUMPTION B43", V_imag="ASSUMPTION B43",
              vacuum_edge="ASSUMPTION B43", interface="ASSUMPTION B43")
UNC = dict(thickness_uncertainty_A=1.0, density_uncertainty_g_cm3=0.05,
           amorphous_si_thickness_uncertainty_A=0.1, uncertainty_kind="half_width")
ENGINES = {"geometric": "oxide_2p0nm", "multislice": "multislice_tiny_oxide_2p0nm"}


def config(base: dict, variant: str, parity: str, n: int) -> dict:
    d = copy.deepcopy(base)
    rec = d["variants"][variant]["cfg_b_parameters"]["surface_preparation_details"]
    for k in ("stands_in_for_item", "assumption_id"):
        rec.pop(k, None)
    rec.update(SUPPLY)
    over = rec["value"]["overlayer"]
    over.update(UNC, consumed_layers=n, consumed_layers_parity=parity)
    over["labels"] = dict(over["labels"], **LABELS)
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.resolve()
    if out == REPO or REPO in out.parents:
        raise SystemExit("--out must lie outside the repository")
    print(f"package: {Path(reflection_holo.__file__).relative_to(REPO)} (repository {REPO.name})")
    base = read_pipeline_file(REPO / "configs" / "demo_smoke_si001.yaml")
    for engine, variant in ENGINES.items():
        res = {}
        for parity, n in (("lower", 6), ("upper", 7)):
            cfg = load_pipeline_dict(config(base, variant, parity, n), variant=variant)
            pv = oxide_item12_record(cfg.cfg_b)["consumed_layers"]["parity_variant"]
            t0 = time.time()
            s = run(cfg, out / f"{engine}_{parity}")
            ov = s["structure"]["options"]["overlayer"]
            steps = [(round(st["built_height_A"], 6),
                      None if not st.get("height") else round(st["height"]["h_A"], 4))
                     for st in s["quantification"]["steps"]]
            print(f"{engine} {variant} {parity} ({n}): {time.time() - t0:.1f} s; interval "
                  f"{pv['interval_counts']}, nearest count {pv['nearest_count']} "
                  f"(nearest_count_variant {pv['nearest_count_variant']!r}); per-terrace consumed "
                  f"{[p['consumed_layers'] for p in ov['per_terrace']]}; interface overlap "
                  f"{sorted({round(p['interface_overlap_A'], 4) for p in ov['per_terrace']})} A; "
                  f"steps (built, measured) {steps}")
            res[parity] = np.load(out / f"{engine}_{parity}" / "arrays.npz")
        x, y = res["lower"], res["upper"]
        same = [k for k in x.files if k in y.files and x[k].dtype == y[k].dtype
                and x[k].shape == y[k].shape and x[k].tobytes() == y[k].tobytes()]
        diff = sorted(set(x.files) - set(same))
        print(f"{engine} {variant} lower (6) vs upper (7): {len(x.files)} arrays; byte-identical "
              f"{len(same)}; differing {diff}")
        for k in diff:
            if x[k].shape != y[k].shape:
                print(f"   {k}: shapes {x[k].shape} vs {y[k].shape}")
            elif x[k].dtype.kind in "fc":
                nan = np.isnan(x[k]) | np.isnan(y[k])
                d = np.abs(x[k] - y[k])[~nan]
                print(f"   {k}: max |diff| {float(d.max()) if d.size else 0.0:.3f} (max |lower| "
                      f"{float(np.nanmax(np.abs(x[k]))):.3f}; NaN in "
                      f"{int(np.isnan(x[k]).sum())} / {int(np.isnan(y[k]).sum())} of {x[k].size})")
            else:
                print(f"   {k}: {x[k].dtype} {x[k].shape}; {int(np.sum(x[k] != y[k]))} of "
                      f"{x[k].size} elements differ")
    print("NOT a size of the parity effect: the multislice difference mixes the parity with the "
          "lower variant's overlap (+0.6838 A) and a one-layer shift of the kept crystal; the "
          "effect of the overlap is not computed")


if __name__ == "__main__":
    main()
