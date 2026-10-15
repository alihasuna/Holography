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
  ~/venvs/holo-tools/bin/pip install rosettasciio h5py
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
NAME_TOKENS = {  # settings written in the file names, e.g. alpha4p1, tilt-10, BP106p8V, 500CL, 41kx, 10frames
    "name_alpha_deg": r"(?:alpha|tilt)[_ ]?(minus[_ ]?)?(-?\d+(?:p\d+)?)",
    "name_biprism_V": r"BP(?:\d[_ ]+)?(?:at[_ ]+)?(\d+(?:p\d+)?)V",
    "name_CL": r"(\d+)CL|CL[_ ]?(\d+)",
    "name_mag": r"(\d+(?:p\d+)?)kx",
    "name_frames": r"(\d+)[_ ]?frames",
}
COLS = (["session", "file", "ext", "size_MB", "shape", "pixel_size"] + list(DM_KEYS) + list(NAME_TOKENS)
        + ["hdf5_content", "mib_header", "note"])


def name_tokens(name: str, row: dict):
    for col, pat in NAME_TOKENS.items():
        m = re.search(pat, name, re.I)
        if not m:
            continue
        if col == "name_alpha_deg":
            v = m.group(2).replace("p", ".")
            if m.group(1) or v.startswith("-"):
                v = "-" + v.lstrip("-")
            row[col] = v
        else:
            row[col] = next(g for g in m.groups() if g).replace("p", ".")


def read_hdf5(path: Path, row: dict, max_items=6):
    """Dataset shapes and small metadata of an HDF5 file (.hm, .h5, .emd); image data is not loaded.
    Text or JSON metadata is shown; pickled Python objects are never unpickled (only flagged)."""
    try:
        import h5py
    except ImportError:
        row["note"] = "install h5py to read HDF5 (.hm) files"
        return
    import json
    items, meta, largest = [], [], (0, "")
    with h5py.File(path, "r") as f:
        def visit(name, obj):
            nonlocal largest
            if not isinstance(obj, h5py.Dataset):
                return
            if len(items) < max_items:
                items.append(f"{name}{list(obj.shape)}")
            if obj.size > largest[0]:
                largest = (obj.size, "x".join(map(str, obj.shape)))
            if obj.size <= 1 and len(meta) < 3:  # small scalar entries usually hold the settings
                try:
                    v = obj[()]
                except Exception:
                    return
                if isinstance(v, bytes):
                    if v[:1] == b"\x80":
                        meta.append(f"{name}: pickled object (not read)")
                        return
                    v = v.decode("utf-8", "replace")
                if isinstance(v, str):
                    try:
                        v = json.dumps(json.loads(v))
                    except ValueError:
                        pass
                meta.append(f"{name}: {str(v)[:200]}")
        f.visititems(visit)
    row["shape"] = largest[1]
    row["hdf5_content"] = ("; ".join(items) + (" | " + " | ".join(meta) if meta else ""))[:400]


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
            elif open(p, "rb").read(4) == b"\x89HDF":
                read_hdf5(p, row)
            else:  # unknown format: the first bytes usually identify it
                with open(p, "rb") as f:
                    head = f.read(24)
                row["note"] = "first bytes: " + "".join(chr(b) if 32 <= b < 127 else "." for b in head) + \
                    " | " + head[:12].hex(" ")
        except Exception as e:
            row["note"] = f"error: {type(e).__name__}: {e}"[:80]
        name_tokens(row["file"], row)
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
             "exposure_s", "name_alpha_deg", "name_biprism_V", "name_CL", "date", "hdf5_content", "note"]
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
