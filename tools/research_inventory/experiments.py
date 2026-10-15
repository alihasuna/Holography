#!/usr/bin/env python3
"""Step 1c: catalogue of your own microscope data, from the settings stored inside the files.
Local and free; only file headers are read (no image data is loaded), nothing is changed.

Reads, for each unique raw file in inventory.csv:
  .dm3 / .dm4  (Gatan)   voltage, magnification, camera length, exposure, mode, tilts, date ... (needs rsciio)
  .mib         (Merlin)  frame size, counter depth, threshold, exposure, timestamp (text header)
  .mrc / .mrcs           image size and pixel size (standard header)
Other formats (.hm, .ser, .emd, ...) are listed with folder, size and date only.

Files are grouped into SESSIONS (their folder); folders matching --exclude (default: the magnetite
course project) are left out. Writes experiments.csv (one row per file) and experiments.md (one
section per session).

Usage (in the virtual environment):
  ~/venvs/holo-tools/bin/pip install rosettasciio
  ~/venvs/holo-tools/bin/python experiments.py ~/Desktop/research_inventory/inventory.csv \
      --root ~/Desktop/"Research - 2026" --out ~/Desktop/research_inventory
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

RAW = {".dm3", ".dm4", ".mib", ".mrc", ".mrcs", ".hm", ".ser", ".emd", ".emi", ".tvips", ".blo", ".prz"}
DM_KEYS = {  # regex on the flattened tag path -> column
    "voltage_V": r"Microscope Info\.Voltage$",
    "magnification": r"Microscope Info\.(Indicated Magnification|Actual Magnification)$",
    "camera_length": r"(STEM Camera Length|Camera Length)$",
    "mode": r"Microscope Info\.(Operation Mode|Imaging Mode|Illumination Mode)$",
    "exposure_s": r"(Exposure \(s\)|Acquisition\.Parameters\.High Level\.Exposure \(s\))$",
    "alpha_tilt": r"(Stage Position\.Stage Alpha|Specimen Tilt Alpha|Alpha)$",
    "beta_tilt": r"(Stage Position\.Stage Beta|Beta)$",
    "spot": r"Microscope Info\.Spot",
    "date": r"DataBar\.Acquisition Date$",
    "time": r"DataBar\.Acquisition Time$",
    "device": r"(DataBar\.Device Name|Acquisition\.Device\.Name)$",
    "biprism": r"(Biprism|BP|Filament)[^.]*$",
}
COLS = ["session", "file", "ext", "size_MB", "shape", "pixel_size"] + list(DM_KEYS) + ["mib_header", "note"]


def flatten(d, prefix=""):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from flatten(v, f"{prefix}.{k}" if prefix else str(k))
    else:
        yield prefix, d


def read_dm(path: Path, row: dict):
    try:
        from rsciio.digitalmicrograph import file_reader
    except ImportError:
        row["note"] = "install rosettasciio to read .dm3/.dm4 settings"
        return
    try:
        sigs = file_reader(str(path), lazy=True)
    except Exception as e:
        row["note"] = f"unreadable: {type(e).__name__}"
        return
    s = sigs[0]
    row["shape"] = "x".join(str(a.get("size", "?")) for a in s.get("axes", []))
    sc = [a for a in s.get("axes", []) if a.get("units") and a.get("scale")]
    if sc:
        row["pixel_size"] = f"{sc[-1]['scale']:.4g} {sc[-1]['units']}"
    flat = list(flatten(s.get("original_metadata", {})))
    for col, pat in DM_KEYS.items():
        rx = re.compile(pat, re.I)
        for k, v in flat:
            if rx.search(k) and not isinstance(v, (bytes, bytearray)):
                row[col] = str(v)[:40]
                break
    if len(sigs) > 1:
        row["note"] = f"{len(sigs)} images in file"


def read_mib(path: Path, row: dict):
    with open(path, "rb") as f:
        head = f.read(768).decode("ascii", "replace")
    parts = head.split(",")
    if parts and parts[0].startswith("MQ1"):
        row["shape"] = f"{parts[4]}x{parts[5]}" if len(parts) > 5 else ""
        row["mib_header"] = ",".join(p.strip() for p in parts[:12])[:160]
    else:
        row["note"] = "no MQ1 header"


def read_mrc(path: Path, row: dict):
    import struct
    with open(path, "rb") as f:
        h = f.read(1024)
    nx, ny, nz = struct.unpack("<3i", h[0:12])
    mx = struct.unpack("<i", h[28:32])[0] or 1
    xlen = struct.unpack("<f", h[40:44])[0]
    row["shape"] = f"{nx}x{ny}x{nz}"
    if xlen:
        row["pixel_size"] = f"{xlen / mx:.4g} A"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inventory", type=Path)
    ap.add_argument("--root", type=Path, required=True, help="the research folder the inventory was made of")
    ap.add_argument("--out", type=Path, default=Path("."))
    ap.add_argument("--exclude", nargs="*", default=["magnetite", "CuSn"], help="skip paths containing these words")
    args = ap.parse_args()
    root = args.root.expanduser()
    rows = list(csv.DictReader(open(args.inventory.expanduser(), encoding="utf-8")))
    seen, todo = set(), []
    for r in rows:
        if r["ext"] not in RAW or any(x.lower() in r["path"].lower() for x in args.exclude):
            continue
        g = r["dup_group"]
        if g and g in seen:
            continue
        if g:
            seen.add(g)
        todo.append(r)
    print(f"reading headers of {len(todo)} unique raw files ...")
    out_rows = []
    for k, r in enumerate(todo, 1):
        p = root / r["path"]
        row = {c: "" for c in COLS}
        row.update(session=str(Path(r["path"]).parent), file=Path(r["path"]).name, ext=r["ext"],
                   size_MB=f"{int(r['size']) / 1e6:.1f}")
        try:
            if r["ext"] in (".dm3", ".dm4"):
                read_dm(p, row)
            elif r["ext"] == ".mib":
                read_mib(p, row)
            elif r["ext"] in (".mrc", ".mrcs"):
                read_mrc(p, row)
            else:  # unknown format: the first bytes usually identify it
                with open(p, "rb") as f:
                    head = f.read(24)
                row["note"] = "first bytes: " + "".join(chr(b) if 32 <= b < 127 else "." for b in head) + \
                    " | " + head[:12].hex(" ")
        except Exception as e:
            row["note"] = f"error: {type(e).__name__}: {e}"[:80]
        out_rows.append(row)
        if k % 50 == 0:
            print(f"  {k}/{len(todo)}")

    out = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "experiments.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(out_rows)
    sessions = defaultdict(list)
    for r in out_rows:
        sessions[r["session"]].append(r)
    shown = ["file", "size_MB", "shape", "pixel_size", "voltage_V", "magnification", "camera_length", "mode",
             "exposure_s", "alpha_tilt", "date", "note"]
    L = [f"# Experiment catalogue ({len(out_rows)} unique raw files, {len(sessions)} session folders)", "",
         f"Excluded: paths containing {', '.join(args.exclude)}. Settings read from file headers only.", ""]
    for s in sorted(sessions):
        L += [f"## {s}", "", "| " + " | ".join(shown) + " |", "|" + "---|" * len(shown)]
        for r in sorted(sessions[s], key=lambda r: r["file"]):
            L.append("| " + " | ".join(r[c].replace("|", "/") for c in shown) + " |")
        L.append("")
    (out / "experiments.md").write_text("\n".join(L), encoding="utf-8")
    print(f"wrote experiments.csv and experiments.md ({len(sessions)} sessions) in {out}")


if __name__ == "__main__":
    main()
