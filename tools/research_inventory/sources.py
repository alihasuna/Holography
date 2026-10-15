#!/usr/bin/env python3
"""Step 3: the list of SOURCES the new simulation may rely on. Local and free.

Only two kinds of material count as sources:
  1. literature: papers, books and chapters, manuals and datasheets (from triage/triage.csv);
  2. real measurements: the raw microscope files (from experiments.csv, read from file headers).
Everything else (AI-generated notes, earlier simulations, reports, posters, figures) is left out:
the simulation is being redone so that it rests only on the literature and on measured data.

Writes <out>/sources.md and <out>/sources_literature.csv.

Usage:
  ~/venvs/holo-tools/bin/python tools/research_inventory/sources.py --out ~/Desktop/research_inventory
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

LIT_KINDS = {"paper", "book_or_chapter", "manual_or_datasheet"}
NOT_DATA = ["simul", "prismatique", "output", "multislice", "kinematic", "figure", "export"]  # session folders
EXCLUDE = ["magnetite", "Fe3O4", "CuSn", "NRK", "Mn0.15"]


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()[:80]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="the research_inventory folder")
    ap.add_argument("--min-relevance", type=int, default=3, help="literature: keep relevance >= this (1-5)")
    args = ap.parse_args()
    out = args.out.expanduser()

    # 1. literature
    lit, seen = [], set()
    for r in csv.DictReader(open(out / "triage" / "triage.csv", encoding="utf-8")):
        if r["kind"] not in LIT_KINDS or int(r["relevance"]) < args.min_relevance:
            continue
        if any(x.lower() in r["path"].lower() for x in EXCLUDE):
            continue
        key = norm_title(r["title"])
        if key in seen:  # the same paper saved twice under different names
            continue
        seen.add(key)
        lit.append(r)
    lit.sort(key=lambda r: (-int(r["relevance"]), r["kind"], r["title"].lower()))
    cols = ["relevance", "kind", "title", "authors_or_source", "year", "topics", "path"]
    with open(out / "sources_literature.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(lit)

    # 2. measurements
    sessions = defaultdict(list)
    for r in csv.DictReader(open(out / "experiments.csv", encoding="utf-8")):
        s = r["session"]
        if any(x.lower() in s.lower() for x in NOT_DATA + EXCLUDE):
            continue
        sessions[s].append(r)

    def vals(rows, col):
        v = sorted({r[col] for r in rows if r.get(col)})
        return ", ".join(v[:6]) + (" ..." if len(v) > 6 else "")

    L = ["# Sources for the simulation", "",
         "Only literature and real measurements. AI-generated notes, earlier simulations, reports, posters",
         "and figures are deliberately left out.", "",
         f"## 1. Literature ({len(lit)} items, relevance >= {args.min_relevance})", "",
         "| Rel. | Kind | Title | Authors / source | Year | File |", "|---|---|---|---|---|---|"]
    for r in lit:
        L.append(f"| {r['relevance']} | {r['kind']} | {r['title']} | {r['authors_or_source']} | {r['year']} | "
                 f"`{r['path']}` |".replace("\n", " "))
    n_files = sum(len(v) for v in sessions.values())
    L += ["", f"## 2. Measurements ({n_files} raw files in {len(sessions)} session folders)", "",
          "Settings are read from the file headers and file names (experiments.csv).", "",
          "| Session folder | Files | Formats | Voltage (V) | Stage alpha (deg, name) | Biprism (V, name) | "
          "Camera length | Dates |", "|---|---|---|---|---|---|---|---|"]
    for s in sorted(sessions):
        rows = sessions[s]
        L.append(f"| `{s}` | {len(rows)} | {vals(rows, 'ext')} | {vals(rows, 'voltage_V')} | "
                 f"{vals(rows, 'name_alpha_deg')} | {vals(rows, 'name_biprism_V')} | "
                 f"{vals(rows, 'camera_length') or vals(rows, 'name_CL')} | {vals(rows, 'date')} |")
    (out / "sources.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out / 'sources.md'} and sources_literature.csv: {len(lit)} literature items, "
          f"{n_files} raw files in {len(sessions)} sessions")


if __name__ == "__main__":
    main()
