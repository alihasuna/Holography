#!/usr/bin/env python3
"""X6: the B41 demo path after the X6 changes must be bitwise unchanged (re-audit A10b; report X6).
Runs one demo variant of configs/demo_smoke_si001.yaml into --out (a scratch directory outside the
repository; never under outputs/) and compares its arrays.npz bitwise with earlier runs of the same
variant (--ref, one or more run directories, e.g. the saved runs of audits A10b and A9b and of report
X5); also compares the item-12 record of the manifest and the structure's spec hash.

Usage:  PYTHONPATH=. venv/bin/python tools/review/x6/x6_demo_bitid.py --variant V --out DIR
            --ref NAME=DIR [--ref NAME=DIR ...]
Saved:  tools/review/x6/x6_demo_bitid_output.txt (both demo variants; the reference runs lie in the
        session scratchpad of the audits, so the comparison itself is reproducible only there)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
import reflection_holo                                                   # noqa: E402
from reflection_holo.pipeline import load_pipeline_dict, read_pipeline_file, run  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--ref", action="append", required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    if out == REPO or REPO in out.parents:
        raise SystemExit("--out must lie outside the repository")
    print(f"package: {Path(reflection_holo.__file__).relative_to(REPO)} (repository {REPO.name})")
    d = read_pipeline_file(REPO / "configs" / "demo_smoke_si001.yaml")
    t0 = time.time()
    s = run(load_pipeline_dict(d, variant=a.variant), out)
    print(f"run {a.variant}: {time.time() - t0:.1f} s")
    for st in s["quantification"]["steps"]:
        h = st.get("height")
        print("built", round(st.get("built_height_A"), 6), "measured",
              None if not h else f"{h['h_A']:+.4f} +- {h['sigma_h_A']:.4f}")
    arr = np.load(out / "arrays.npz")
    man = json.loads((out / "manifest.json").read_text())
    ox_rec = man["extra"]["oxide_item12"]
    for item in a.ref:
        name, _, path = item.partition("=")
        p = Path(path)
        if not (p / "arrays.npz").exists():
            print(f"reference {name}: absent")
            continue
        b = np.load(p / "arrays.npz")
        same = [k for k in arr.files if k in b.files and arr[k].shape == b[k].shape
                and np.array_equal(arr[k], b[k], equal_nan=arr[k].dtype.kind in "fc")]
        print(f"vs {name}: arrays {len(arr.files)} vs {len(b.files)}; bitwise identical "
              f"{len(same)}; differing {sorted(set(arr.files) - set(same))}")
        mb = json.loads((p / "manifest.json").read_text())
        ob = mb["extra"].get("oxide_item12")
        if ob is None:
            print("   item-12 record: absent in the reference (it predates the record)")
        else:
            print(f"   item-12 record: labels equal {ox_rec['labels'] == ob['labels']}; headline "
                  f"equal {ox_rec['headline_label'] == ob['headline_label']}; keys added "
                  f"{sorted(set(ox_rec) - set(ob))}; keys removed {sorted(set(ob) - set(ox_rec))}")
        sb = p / "summary.json"
        if sb.exists():
            ha = s["structure"]["options"]["overlayer"]["spec_sha256"]
            hb = json.loads(sb.read_text())["structure"]["options"]["overlayer"].get("spec_sha256")
            print(f"   spec_sha256 equal: {ha == hb} ({ha[:8]}...)")
    print("consumed_layers record:", ox_rec["consumed_layers"])


if __name__ == "__main__":
    main()
