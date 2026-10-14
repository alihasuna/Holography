#!/usr/bin/env python3
"""Nature-style figure of the realistic buried-dislocation case (configs/si001_60deg_50nm.yaml):
a 60 degree dislocation 50 nm deep with its slip step, in the three-strip Si(001) sample.

  a  surface relief from the elastic field (what the electrons see) and the cross-section:
     dislocation core, (1-11) glide plane, slip step, strips
  b  reconstructed phase across the 0.74 um cell, (008) and (0,0,12), multislice and geometric
  c  reconstructed amplitude, same series
  d  zoom over the dislocation: phase and the surface relief converted to phase, -q_ext u_n

Usage:
  python scripts/figures_60deg.py --config configs/si001_60deg_50nm.yaml \
      --results outputs/si001_60deg_50nm/reconstruction/results.npz --out docs/figures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import geometry as geo  # noqa: E402
from reflection_holo import plotstyle as ps  # noqa: E402
from reflection_holo.crystal import lattice_period  # noqa: E402
from reflection_holo.defects.dislocation import from_config  # noqa: E402
from reflection_holo.provenance import Config  # noqa: E402
from reflection_holo.structure.sections import build_sections  # noqa: E402

FRAME = geo.SI001_FRAME


def surface(cfg):
    a = float(cfg.get("crystal.a_A"))
    entries = cfg.get("defects.dislocations")
    n_img = int(cfg.get("defects.periodic_images_y"))
    Ly = sum(cfg.get("sample.periods_per_section")) * lattice_period(FRAME, FRAME.y_uvw, a)
    D = from_config(entries, float(cfg.get("defects.nu")), a, FRAME, Ly if n_img else None, n_img)
    s = build_sections(FRAME, a, cfg.get("sample.periods_per_section"), cfg.get("sample.raise_layers"),
                       float(cfg.get("sample.depth_A")), D, seam_y=cfg.get("sample.seam_y_A"))
    y = np.linspace(0, s.Ly, 4000, endpoint=False)
    sec = np.clip(np.searchsorted(s.boundaries, y, side="right") - 1, 0, len(s.heights) - 1)
    r = np.stack([np.zeros_like(y), y, np.zeros_like(y)], -1)
    un = s.u_func(r)[:, 0]
    # the seam carries the slip step; u_func wraps at the seam, so the step is where it jumps
    return s, y, un, s.heights[sec], entries[0]


def strips(ax, bounds_um, top=True):
    for b in bounds_um[1:-1]:
        ax.axvline(b, color=ps.GRID, lw=0.6, ls=(0, (3, 2)), zorder=0)
    if top:
        yl = ax.get_ylim()
        for k in range(len(bounds_um) - 1):
            ax.text((bounds_um[k] + bounds_um[k + 1]) / 2, yl[1], str(k + 1), ha="center", va="bottom",
                    fontsize=6, color=ps.INK2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="docs/figures")
    args = ap.parse_args()
    cfg = Config(args.config)
    plt = ps.apply()
    out = Path(args.out)

    s, ys, un, hs, e = surface(cfg)
    r = np.load(args.results)
    y = r["y"]
    um = 1e-4  # A -> um
    bounds = s.boundaries * um
    core_y = float(e["position_yz_A"][0])
    depth = float(e["depth_A"])
    trace = float(cfg.get("sample.seam_y_A"))
    summ = json.loads((Path(args.results).parent / "summary.json").read_text())

    fig = plt.figure(figsize=(ps.DOUBLE, 4.6))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.55, 1], height_ratios=[1, 1, 1], hspace=0.45, wspace=0.28)
    gsa = gs[0, 0].subgridspec(2, 1, height_ratios=[1, 1.15], hspace=0.08)
    ax_rel = fig.add_subplot(gsa[0])
    ax_xs = fig.add_subplot(gsa[1], sharex=ax_rel)
    ax_ph = fig.add_subplot(gs[1, 0], sharex=ax_rel)
    ax_am = fig.add_subplot(gs[2, 0], sharex=ax_rel)
    ax_z = fig.add_subplot(gs[0:2, 1])
    ax_za = fig.add_subplot(gs[2, 1], sharex=ax_z)

    # a: relief and cross-section
    h = un + hs
    ax_rel.plot(ys * um, h, color=ps.INK, lw=0.8)
    ax_rel.set_ylabel("Surface\nheight (Å)")
    ax_rel.set_xlim(0, s.Ly * um)
    plt.setp(ax_rel.get_xticklabels(), visible=False)
    strips(ax_rel, bounds)
    ax_xs.axhline(0, color=ps.INK, lw=0.8)
    ax_xs.plot([trace * um, core_y * um], [0, -depth / 10], color=ps.C2, lw=0.8, ls=(0, (3, 1.5)))
    ax_xs.plot([core_y * um], [-depth / 10], marker=(3, 0, 0), ms=5, color=ps.ACCENT, zorder=5)
    ax_xs.text(core_y * um + 0.02, -depth / 10, "60° dislocation\n50 nm deep", fontsize=5.5, va="center",
               ha="left", color=ps.INK2)
    ax_xs.text(trace * um - 0.02, -14, "(1$\\bar{1}$1) glide\nplane", fontsize=5.5, ha="right", va="center",
               color=ps.C2)
    ax_xs.annotate("slip step", xy=(trace * um, 0), xytext=(trace * um - 0.12, 22), fontsize=5.5,
                   color=ps.INK2, ha="right", va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color=ps.INK2))
    ax_xs.set_ylim(-62, 32)
    ax_xs.set_ylabel("Depth (nm)")
    for b in bounds[1:-1]:
        ax_xs.axvline(b, color=ps.GRID, lw=0.6, ls=(0, (3, 2)), zorder=0)
    plt.setp(ax_xs.get_xticklabels(), visible=False)
    ps.panel_label(ax_rel, "a", x=-0.09)

    series = [("(0,0,8)", ps.C1, "(008)"), ("(0,0,12)", ps.C2, "(0,0,12)")]
    for ax, key, ylab, ref in ((ax_ph, "phase", "Phase (rad)", 0.0), (ax_am, "amp", "Amplitude (rel.)", 1.0)):
        ax.axhline(ref, color=ps.GRID, lw=0.5)
        for name, col, lab in series:
            if f"{name}_ms_{key}" in r.files:
                ax.plot(y * um, r[f"{name}_ms_{key}"], color=col, lw=0.9, label=f"{lab} multislice")
            if f"{name}_geo3_{key}" in r.files:
                ax.plot(y * um, r[f"{name}_geo3_{key}"], color=col, lw=0.6, ls=(0, (3, 1.5)),
                        label=f"{lab} geometric")
        ax.set_ylabel(ylab)
        strips(ax, bounds, top=False)
    ax_ph.legend(loc="lower left", ncol=2, handlelength=2.2)
    plt.setp(ax_ph.get_xticklabels(), visible=False)
    ax_am.set_xlabel("Position across the beam, y (µm)")
    ps.panel_label(ax_ph, "b", x=-0.09)
    ps.panel_label(ax_am, "c", x=-0.09)

    # d: zoom over the dislocation, with -q_ext u_n of the relief for comparison
    win = (y > core_y - 2500) & (y < core_y + 2500)
    wins = (ys > core_y - 2500) & (ys < core_y + 2500)
    for name, col, lab in series:
        k = f"{name}_ms_phase"
        if k not in r.files:
            continue
        ph = r[k]
        base = np.median(ph[(y > core_y - 2500) & (y < core_y - 2000)])
        ax_z.plot((y[win] - core_y) / 10, ph[win] - base, color=col, lw=0.9, label=f"{lab} multislice")
        m = summ["reflections"][name]["multislice"]
        th = m["theta_ext_effective_mrad"] * 1e-3
        q_ext = 2 * geo.k_rad_per_A(float(cfg.get("beam.energy_keV"))) * np.sin(th)
        rel = -q_ext * h[wins]
        rel = rel - np.median(rel[(ys[wins] > core_y - 2500) & (ys[wins] < core_y - 2000)])
        ax_z.plot((ys[wins] - core_y) / 10, rel, color=col, lw=0.6, ls=(0, (1, 1)),
                  label=f"{lab}: $-q_{{ext}}u_n$ (relief only)")
        ax_za.plot((y[win] - core_y) / 10, r[f"{name}_ms_amp"][win], color=col, lw=0.9)
    for ax in (ax_z, ax_za):
        ax.axvline(0, color=ps.ACCENT, lw=0.5, ls=(0, (1, 1)))
        ax.axvline((trace - core_y) / 10, color=ps.C2, lw=0.5, ls=(0, (3, 1.5)))
    ax_z.text(0.5, ax_z.get_ylim()[1], " core", fontsize=5.5, color=ps.ACCENT, va="top", ha="left")
    ax_z.text((trace - core_y) / 10, ax_z.get_ylim()[1], "slip step ", fontsize=5.5, color=ps.C2, va="top", ha="right")
    ax_z.set_ylabel("Phase (rad)")
    ax_z.legend(loc="lower right", fontsize=5.5, handlelength=2.2)
    plt.setp(ax_z.get_xticklabels(), visible=False)
    ax_za.set_ylabel("Amplitude (rel.)")
    ax_za.set_xlabel("Distance from the core, y (nm)")
    ax_z.set_xlim(-250, 250)
    ps.panel_label(ax_z, "d", x=-0.14)
    ps.panel_label(ax_za, "e", x=-0.14)
    ps.save(fig, out / "fig_60deg_50nm")
    plt.close(fig)
    print("wrote", out / "fig_60deg_50nm.pdf/.png")


if __name__ == "__main__":
    main()
