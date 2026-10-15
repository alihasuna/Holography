#!/usr/bin/env python3
"""Step 1b: a duplicate plan from inventory.csv. It ONLY writes a plan; no file is touched.

For every group of identical files it picks ONE copy to keep, by these rules in order:
  1. not inside a folder that looks like a dump or backup (archived, zips, inbox, To sort, copies, ...)
  2. inside an organised, dated experiment or analysis folder (e.g. research-agent/MARCH/...)
  3. the oldest modification date (most likely the original)
  4. the shortest path
The other copies are listed as extras, with the space they use. Review dedupe_plan.csv, then decide.

Usage:
  python3 dedupe_plan.py ~/Desktop/research_inventory/inventory.csv --out ~/Desktop/research_inventory
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

DUMP = re.compile(r"(archiv|zips?\b|_inbox|inbox_loose|to sort|copy|copia|backup|old|tmp|temp|download"
                  r"|transfer exam/data|-\d{8}T\d{6}Z|\(\d\)|research - 2025 2)", re.I)
ORGANISED = re.compile(r"(research-agent/(march|stage)|\d{4}-\d{2}-\d{2}_|raw-and-exported|valid_measurements)", re.I)


def rank(r):
    p = r["path"]
    return (1 if DUMP.search(p) else 0, 0 if ORGANISED.search(p) else 1, r["modified"], len(p))


def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.1f} {u}"
        n /= 1024


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inventory", type=Path)
    ap.add_argument("--out", type=Path, default=Path("."))
    ap.add_argument("--min-kb", type=float, default=100.0,
                    help="ignore files smaller than this (small identical files are usually settings or empty "
                         "files that programs need in place; they save no space)")
    args = ap.parse_args()
    rows = list(csv.DictReader(open(args.inventory.expanduser(), encoding="utf-8")))
    groups = defaultdict(list)
    small = 0
    for r in rows:
        if r["dup_group"]:
            r["size"] = int(r["size"])
            if r["size"] < args.min_kb * 1024 or any(part.startswith(".") for part in r["path"].split("/")):
                small += 1
                continue
            groups[r["dup_group"]].append(r)
    groups = {g: m for g, m in groups.items() if len(m) > 1}

    out = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True)
    total, by_top = 0, defaultdict(int)
    with open(out / "dedupe_plan.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "action", "size", "path", "keep_copy"])
        for g, members in sorted(groups.items(), key=lambda kv: -kv[1][0]["size"] * (len(kv[1]) - 1)):
            members.sort(key=rank)
            keep = members[0]
            w.writerow([g, "KEEP", keep["size"], keep["path"], ""])
            for m in members[1:]:
                w.writerow([g, "extra", m["size"], m["path"], keep["path"]])
                total += m["size"]
                by_top[m["path"].split("/")[0]] += m["size"]

    L = ["# Duplicate plan (nothing has been changed)", "",
         f"{len(groups)} groups of identical files of {args.min_kb:g} KB or more. Keeping one copy of each "
         f"would free **{human(total)}**. ({small} smaller or hidden duplicate files were left out on purpose: "
         f"settings and empty files that programs expect in place.)",
         "", "The copy to keep is chosen by: not in a dump/backup folder > in an organised, dated folder > "
         "oldest > shortest path. Every decision is in `dedupe_plan.csv` (open it in Numbers or Excel).", "",
         "## Where the extra copies are", "", "| Top folder | Space used by extra copies |", "|---|---|"]
    L += [f"| {k} | {human(v)} |" for k, v in sorted(by_top.items(), key=lambda kv: -kv[1])]
    L += ["", "Nothing is deleted by this tool. When you have reviewed the plan, the extras can be moved to a "
          "single review folder (reversible) before anything is ever deleted."]
    (out / "dedupe_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{len(groups)} groups; extra copies use {human(total)}; wrote dedupe_plan.csv and dedupe_summary.md in {out}")


if __name__ == "__main__":
    main()
