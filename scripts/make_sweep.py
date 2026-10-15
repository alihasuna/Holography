#!/usr/bin/env python3
"""Generate config variants for a parameter sweep (one config per Slurm array task).

Each variant is the base config with some values replaced. The evidence labels are kept, and a
note records the change. A list file gives one config path per line; the array job picks line
SLURM_ARRAY_TASK_ID + 1.

Usage:
  python scripts/make_sweep.py --base configs/si001_three_sections_cpu.yaml --out configs/sweep_depth \
      --depths 15 25 50 --reflections 008 0012 --offsets -0.3 0 0.3
Axes left out keep the base value. --offsets are added to the base operating offset of each
reflection (mrad), which gives a rocking series around the reflectivity maximum.
"""

from __future__ import annotations

import argparse
import copy
import itertools
from pathlib import Path

import yaml

HKL = {"004": [0, 0, 4], "008": [0, 0, 8], "0012": [0, 0, 12]}
NAME = {"004": "(0,0,4)", "008": "(0,0,8)", "0012": "(0,0,12)"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depths", type=float, nargs="*", default=None, help="dislocation depths (A)")
    ap.add_argument("--reflections", nargs="*", default=None, choices=sorted(HKL), help="one reflection per variant")
    ap.add_argument("--offsets", type=float, nargs="*", default=None, help="extra angle offsets (mrad)")
    args = ap.parse_args()

    base = yaml.safe_load(Path(args.base).read_text())
    depths = args.depths or [None]
    refl = args.reflections or [None]
    offs = args.offsets or [None]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for d, r, o in itertools.product(depths, refl, offs):
        c = copy.deepcopy(base)
        tag = []
        if d is not None:
            for e in c["defects"]["dislocations"]["value"]:
                e["depth_A"] = float(d)
            c["defects"]["dislocations"]["note"] += f" SWEEP: depth set to {d:g} A."
            tag.append(f"d{d:g}")
        if r is not None:
            c["reflections_to_run"]["value"] = [HKL[r]]
            tag.append(r)
        if o is not None:
            oo = c["multislice"]["operating_offset_mrad"]
            oo["value"] = {k: round(v + o, 4) for k, v in oo["value"].items()}
            oo["note"] += f" SWEEP: base offsets shifted by {o:+g} mrad."
            oo["label"] = "ASSUMPTION"
            tag.append(f"off{o:+g}")
        c["name"] = base["name"] + ("_" + "_".join(tag) if tag else "")
        p = out / f"{c['name']}.yaml"
        p.write_text(yaml.safe_dump(c, sort_keys=False, width=110))
        paths.append(str(p))
    (out / "list.txt").write_text("\n".join(paths) + "\n")
    print(f"{len(paths)} configs written to {out}; array range for Slurm: --array=0-{len(paths) - 1}")


if __name__ == "__main__":
    main()
