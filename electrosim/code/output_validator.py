#!/usr/bin/env python3
"""Check stage output folders: sidecar format, every array present with the declared shape, dtype, axes and
sampling, finite values, and a short statistics table. Replaces the si110 hdf5_output_validator.py (audit M19:
12 lines, a hard-coded laptop path, no assertions; the old pipeline's intensity file was all NaN unnoticed).

Runs in: em-holography or em-abtem (numpy only). Read-only on its inputs.

    gemicro run --kind analysis --name check-outputs --params params/output_validator.yaml \
        --output derived/check-outputs -- /opt/envs/em-holography/bin/python code/output_validator.py \
        --params params/output_validator.yaml --stage sims/exit-wave --stage derived/hologram \
        --stage derived/holo-recon --output derived/check-outputs

Exit status 0 when every folder passes, 4 otherwise.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402

SPATIAL = {"x", "y"}


def check_folder(folder, require_plots):
    folder = Path(folder)
    sides = [p for p in folder.glob("*.json") if _is_sidecar(p)]
    if len(sides) != 1:
        return {"folder": str(folder), "ok": False, "errors": [f"expected one stage sidecar, found {len(sides)}"]}
    meta = json.loads(sides[0].read_text())
    errors, arrays = [], {}
    for key, e in meta.get("arrays", {}).items():
        f = folder / e["file"]
        if not f.is_file():
            errors.append(f"{key}: {e['file']} missing")
            continue
        a = np.load(f, allow_pickle=False)
        st = {"shape": list(a.shape), "dtype": str(a.dtype)}
        if list(a.shape) != e["shape"] or str(a.dtype) != e["dtype"]:
            errors.append(f"{key}: file {a.shape} {a.dtype} vs sidecar {e['shape']} {e['dtype']}")
        if len(e.get("axes", [])) != a.ndim:
            errors.append(f"{key}: axes {e.get('axes')} for a {a.ndim}-D array")
        if SPATIAL & set(e.get("axes", [])) and "sampling_A" not in e:
            errors.append(f"{key}: spatial axes but no sampling_A")
        if a.dtype.kind in "fc":
            n_bad = int(np.count_nonzero(~np.isfinite(a)))
            if n_bad:
                errors.append(f"{key}: {n_bad} non-finite values")
            v = np.abs(a) if a.dtype.kind == "c" else a
            if a.size:
                st.update({"min": float(np.nanmin(v)), "max": float(np.nanmax(v)), "mean": float(np.nanmean(v))})
                if float(np.nanmax(v)) == float(np.nanmin(v)) and a.size > 1 and key not in ("phase_ramp",):
                    st["note"] = "constant array"
        arrays[key] = st
    plots = meta.get("summary", {}).get("plots", [])
    for p in plots:
        if not (folder / p).is_file():
            errors.append(f"plot {p} listed but missing")
    if require_plots and not plots and meta.get("stage") not in ("slab",):
        errors.append("no plots (matplotlib missing in the environment?)")
    return {"folder": str(folder), "stage": meta.get("stage"), "ok": not errors, "errors": errors,
            "arrays": arrays, "wall_time_s": meta.get("wall_time_s"), "warnings":
            meta.get("summary", {}).get("warnings", [])}


def _is_sidecar(p):
    try:
        d = json.loads(p.read_text())
    except Exception:
        return False
    return isinstance(d, dict) and d.get("format") == hc.FORMAT and "stage" in d


def main(argv=None):
    ap = hc.common_cli("Check stage output folders (env: either)", [])
    ap.add_argument("--stage", action="append", required=True, help="a stage output folder (repeatable)")
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    P = hc.Section(raw)
    require_plots = P.boolean("require_plots")
    P.finish()
    with hc.Output(a.output, a.overwrite) as out:
        reports = [check_folder(f, require_plots) for f in a.stage]
        ok = all(r["ok"] for r in reports)
        summary = {"folders": len(reports), "all_ok": ok,
                   "failed": [r["folder"] for r in reports if not r["ok"]]}
        hc.write_sidecar(out, "output_check", raw, hc.provenance(sys.argv, a.params, {}), {"reports": reports},
                         summary)
        out.publish()
    for r in reports:
        print(f"   {'OK  ' if r['ok'] else 'FAIL'} {r['folder']} ({r.get('stage')})"
              + ("" if r["ok"] else ": " + "; ".join(r["errors"])))
    hc.print_summary("output check", summary, out.final, out.files)
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
