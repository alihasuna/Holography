#!/usr/bin/env python3
"""Signed terrace step phases and heights from a reconstructed REFLECTION hologram phase.

Runs in: em-holography (CPU; numpy).

    gemicro run --kind analysis --name step-height --input derived/holo-recon/phase_unwrapped.npy \
        --params params/step_height.yaml --output derived/step-height -- /opt/envs/em-holography/bin/python \
        code/step_height_reflection_formula.py --params params/step_height.yaml --recon derived/holo-recon \
        --slab sims/slab --output derived/step-height

Relation (docs/physics_conventions.md, exp(+i k·r) convention): for the specular beam
    Δφ = φ(terrace j) - φ(terrace i) = -(4π/λ) h sin θ_ext,    h = height(j) - height(i),
so h = -Δφ λ / (4π sin θ_ext), known only modulo the wrap period h_2π = λ / (2 sin θ_ext). Every height is
reported with its branch family h + n h_2π; a single hologram does not fix n (a rocking series does).

Fixes relative to the si110 script (audit A): the sign is kept, steps are taken in a fixed spatial order
(terrace i -> i+1 along y, cyclic) from the known terrace geometry, not from sorted histogram peaks (C8,
M11); the wrap period and branch are stated (C4); the external glancing angle is a required input, as are
λ (from the reconstruction's energy) and every other value: no silent default (M12); a step below
`no_step_sigma` × its uncertainty is reported as "no step detected" (M11); a height is refused when its
uncertainty exceeds `max_sigma_h_over_wrap` × h_2π (small-denominator policy, spec §5.8).
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402


def read(P):
    p = {"theta": P.num("theta_ext_mrad", lo=0.0, lo_open=True) * 1e-3,
         "xband": P.vec("terrace_x_band_A", 2),
         "margin": P.num("terrace_margin_A", lo=0.0),
         "nsig": P.num("no_step_sigma", lo=0.0, lo_open=True),
         "maxfrac": P.num("max_sigma_h_over_wrap", lo=0.0, lo_open=True, hi=0.5)}
    if p["xband"][1] <= p["xband"][0]:
        raise hc.ParamError("terrace_x_band_A must be [x_min, x_max] with x_max > x_min")
    return p


def terrace_stats(phase, pix, y_edges, xband, margin, area_q):
    """Mean phase of every terrace band and its standard error (independent samples = resolution cells)."""
    x = (np.arange(phase.shape[0]) + 0.5) * pix[0]
    y = (np.arange(phase.shape[1]) + 0.5) * pix[1]
    rows = (x >= xband[0]) & (x <= xband[1])
    out = []
    for i in range(len(y_edges) - 1):
        cols = (y > y_edges[i] + margin) & (y < y_edges[i + 1] - margin)
        v = phase[np.ix_(rows, cols)]
        if v.size < 4:
            raise SystemExit(f"terrace {i}: fewer than 4 pixels in the measurement box; check terrace_x_band_A")
        n_cells = max(1.0, v.size * pix[0] * pix[1] * area_q)  # pixels × (resolution cells per pixel)
        out.append({"terrace": i, "mean_rad": float(v.mean()), "std_rad": float(v.std()),
                    "pixels": int(v.size), "resolution_cells": n_cells,
                    "sem_rad": float(v.std() / math.sqrt(n_cells))})
    return out


def quantify(stats, lam, theta, nsig, maxfrac, true_tops=None):
    s = math.sin(theta)
    h2pi = lam / (2.0 * s)
    k = 4.0 * math.pi * s / lam  # rad per Å of height
    steps = []
    n = len(stats)
    for i in range(n):
        j = (i + 1) % n
        if n == 1:
            break
        dphi = stats[j]["mean_rad"] - stats[i]["mean_rad"]
        sig = math.hypot(stats[i]["sem_rad"], stats[j]["sem_rad"])
        dw = (dphi + math.pi) % (2 * math.pi) - math.pi
        row = {"from": i, "to": j, "delta_phi_rad": dphi, "delta_phi_wrapped_rad": dw, "sigma_rad": sig,
               "wrap_period_A": h2pi}
        if abs(dw) < nsig * sig:
            row["result"] = "no step detected"
            row["height_A"] = None
        else:
            sig_h = sig / k
            if sig_h > maxfrac * h2pi:
                row["result"] = "refused: height uncertainty exceeds the policy fraction of the wrap period"
                row["height_A"] = None
            else:
                row["result"] = "measured"
                row["height_A"] = -dw / k
                row["sigma_h_A"] = sig_h
                row["branch_family_A"] = [row["height_A"] + m * h2pi for m in (-2, -1, 0, 1, 2)]
        if true_tops is not None:  # simulation only: reported, never used in the estimate
            ht = true_tops[j] - true_tops[i]
            row["true_height_A"] = ht
            row["true_delta_phi_wrapped_rad"] = ((-k * ht) + math.pi) % (2 * math.pi) - math.pi
            if row.get("height_A") is not None:
                row["branch_matching_truth"] = int(round((ht - row["height_A"]) / h2pi))
        steps.append(row)
    return steps, h2pi


def run(P, recon_dir, slab_dir, out):
    p = read(P)
    P.finish()
    rs = hc.Stage(recon_dir, "recon")
    phase = rs.array("phase_unwrapped").astype(np.float64)
    pix = rs.sampling("phase_unwrapped")
    lam = rs.meta["physics"]["wavelength_A"]
    area_q = rs.meta["physics"]["aperture"]["noise_equivalent_area_inv_A2"]
    slab = hc.Stage(slab_dir, "slab").meta["physics"]
    g = slab["geometry"]
    stats = terrace_stats(phase, pix, g["terrace_y_edges_A"], p["xband"], p["margin"], area_q)
    steps, h2pi = quantify(stats, lam, p["theta"], p["nsig"], p["maxfrac"], g["x_top_atom_A"])
    physics = {"theta_ext_mrad": p["theta"] * 1e3, "wavelength_A": lam, "wrap_period_A": h2pi,
               "relation": "h = -Δφ λ / (4π sin θ_ext), Δφ = φ(to) - φ(from), modulo h_2π = λ/(2 sin θ_ext)",
               "terraces": stats, "steps": steps, "terrace_x_band_A": p["xband"],
               "recon_sidecar": str(rs.sidecar_path)}
    summary = {"wrap_period_A": round(h2pi, 5),
               "steps": [{"from": s["from"], "to": s["to"], "dphi_rad": round(s["delta_phi_wrapped_rad"], 4),
                          "sigma_rad": round(s["sigma_rad"], 4), "result": s["result"],
                          "height_A": None if s["height_A"] is None else round(s["height_A"], 4),
                          "true_height_A": round(s.get("true_height_A", float("nan")), 4)} for s in steps]}
    out.save_json("step_height_table.json", steps)
    return physics, summary, rs


def main(argv=None):
    ap = hc.common_cli("Signed step phases and heights, reflection geometry (env: em-holography)",
                       [("--recon", "output folder of holo_recon.py"),
                        ("--slab", "output folder of si110_cleave_slab_generator.py (terrace geometry)")])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    out = hc.Output(a.output, a.overwrite)
    physics, summary, rs = run(hc.Section(raw), a.recon, a.slab, out)
    hc.write_sidecar(out, "step_height", raw, hc.provenance(sys.argv, a.params, {"recon": rs.sidecar_path}),
                     physics, summary)
    out.publish()
    hc.print_summary("step heights", summary, out.final, out.files)


if __name__ == "__main__":
    main()
