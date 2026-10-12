#!/usr/bin/env python3
"""Tilt series of abTEM exit waves (replaces the si110 pipeline's prismatique tilt-series runner).

Runs in: em-abtem (abTEM 1.0.10; CuPy when device: gpu). GPU step.

    gemicro run --kind sim --name tilt-series --input sims/slab/si110_slab.extxyz \
        --params params/tilt_series.yaml --output sims/tilt-series -- /opt/envs/em-abtem/bin/python \
        code/multislice_tilt_series_runner.py --params params/tilt_series.yaml \
        --structure sims/slab/si110_slab.extxyz --output sims/tilt-series

Same parameters as multislice_forward_model.py, with a `tilt_series` section instead of `illumination`.
Writes exit_waves.npy (tilt, config, x, y) and tilts_mrad.npy; every tilt is stored with its value, and
downstream stages select a tilt BY VALUE (audit C5: the old filter silently read tilt index 0). Each requested
tilt is simulated exactly (abTEM has no tilt grid: audit C2's 0.657 mrad snapping does not occur).

Fixes relative to the old runner (audit A): no invalid keywords swallowed by `except` (C1, m15), the grid that
is simulated is the grid that is reported (C2), no sample-rotation "validation" that breaks periodicity (M9).
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402
import multislice_forward_model as fm  # noqa: E402


def tilt_list(T):
    """Explicit [[θx, θy], ...] or a sweep of |θ| from start to stop (inclusive) along an azimuth."""
    mode = T.choice("mode", ("explicit", "sweep"))
    if mode == "explicit":
        tl = T.req("tilts_mrad")
        if not isinstance(tl, list) or not tl:
            raise hc.ParamError("tilt_series.tilts_mrad must be a non-empty list of [θx, θy]")
        out = []
        for t in tl:
            if not (isinstance(t, list) and len(t) == 2 and all(hc._is_number(v) for v in t)):
                raise hc.ParamError(f"tilt_series.tilts_mrad entry {t!r} is not [θx, θy]")
            out.append([float(t[0]), float(t[1])])
        return out
    az = math.radians(T.num("azimuth_deg"))
    a, b, st = T.num("start_mrad"), T.num("stop_mrad"), T.num("step_mrad", lo=0.0, lo_open=True)
    n = int(math.floor((b - a) / st + 1e-9)) + 1
    if n < 1:
        raise hc.ParamError("tilt_series: stop_mrad must be >= start_mrad")
    mags = a + st * np.arange(n)
    return [[round(float(m * math.cos(az)), 9) + 0.0, round(float(m * math.sin(az)), 9) + 0.0] for m in mags]


def main(argv=None):
    ap = hc.common_cli("abTEM exit-wave tilt series (env: em-abtem, GPU)",
                       [("--structure", "structure file with an orthogonal cell (extxyz/CIF), beam along z")])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    P = hc.Section(raw)
    tilts = tilt_list(P.sub("tilt_series"))
    with hc.Output(a.output, a.overwrite) as out:
        physics, summary, inputs, s = fm.run(raw, a.structure, out, tilts=tilts, series=True, P=P)
        prov = hc.provenance(sys.argv, a.params, inputs, seeds={"phonons": physics["frozen_phonons"]["seeds"]})
        hc.write_sidecar(out, "exit_wave", raw, prov, physics, summary)
        out.publish()
    hc.print_summary(f"exit-wave tilt series ({len(tilts)} tilts)", summary, out.final, out.files)


if __name__ == "__main__":
    main()
