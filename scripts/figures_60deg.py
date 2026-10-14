#!/usr/bin/env python3
"""Nature-style figure of the realistic buried-dislocation case: a 60 degree dislocation 50 nm deep
with its slip step (configs/si001_60deg_50nm.yaml), optionally compared with a Lomer dislocation at
the same depth (configs/si001_lomer_50nm.yaml). Uses multislice results where present and the
geometric (column) model otherwise; the legend says which.

  a  surface relief from the elastic field, and the cross-section (core, glide plane, slip step)
  b  reconstructed (008) phase across the 0.74 um cell
  c  reconstructed (008) amplitude
  d  zoom over the dislocation: phase; dotted level -2 pi g.b, the far-field offset of a Burgers
     vector with a component along g (g.b = 4 for the 60 degree dislocation at (008), 0 for Lomer)
  e  zoom: amplitude

Usage:
  python scripts/figures_60deg.py --config configs/si001_60deg_50nm.yaml --results <dir>/results.npz \
      [--compare-config configs/si001_lomer_50nm.yaml --compare-results <dir>/results.npz] \
      [--out docs/figures] [--stem fig_60deg_50nm]
"""

from __future__ import annotations

import argparse
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
REFL = "(0,0,8)"


def surface(cfg):
    """Sample, y grid, surface height (elastic field + terrace) and the first dislocation entry."""
    a = float(cfg.get("crystal.a_A"))
    entries = cfg.get("defects.dislocations")
    n_img = int(cfg.get("defects.periodic_images_y"))
    Ly = sum(cfg.get("sample.periods_per_section")) * lattice_period(FRAME, FRAME.y_uvw, a)
    D = from_config(entries, float(cfg.get("defects.nu")), a, FRAME, Ly if n_img else None, n_img)
    s = build_sections(FRAME, a, cfg.get("sample.periods_per_section"), cfg.get("sample.raise_layers"),
                       float(cfg.get("sample.depth_A")), D, seam_y=cfg.get("sample.seam_y_A"))
    y = np.linspace(0, s.Ly, 6000, endpoint=False)
    sec = np.clip(np.searchsorted(s.boundaries, y, side="right") - 1, 0, len(s.heights) - 1)
    un = s.u_func(np.stack([np.zeros_like(y), y, np.zeros_like(y)], -1))[:, 0]
    return s, y, un + s.heights[sec], entries[0]


def series(r, key):
    """(profile, source) for the (008) reflection: multislice if present, else geometric."""
    if f"{REFL}_ms_{key}" in r.files:
        return r[f"{REFL}_ms_{key}"], "multislice"
    return r[f"{REFL}_geo3_{key}"], "geometric"


def g_dot_b(cfg):
    """g.b of the (008) reflection and the first dislocation (cubic indices; integer for a lattice b)."""
    e = cfg.get("defects.dislocations")[0]
    return float(np.dot([0, 0, 8], np.asarray(e["burgers_over_a"], float)) * float(e["sign"]))


def strips(ax, bounds_um, labels=True):
    for b in bounds_um[1:-1]:
        ax.axvline(b, color=ps.GRID, lw=0.6, ls=(0, (3, 2)), zorder=0)
    if labels:
        yl = ax.get_ylim()
        for k in range(len(bounds_um) - 1):
            ax.text((bounds_um[k] + bounds_um[k + 1]) / 2, yl[1], str(k + 1), ha="center", va="bottom",
                    fontsize=6, color=ps.INK2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--compare-config", default=None)
    ap.add_argument("--compare-results", default=None)
    ap.add_argument("--out", default="docs/figures")
    ap.add_argument("--stem", default="fig_60deg_50nm")
    args = ap.parse_args()
    plt = ps.apply()
    out = Path(args.out)

    cases = [(Config(args.config), np.load(args.results), ps.C1, "60°")]
    if args.compare_config:
        cases.append((Config(args.compare_config), np.load(args.compare_results), ps.C2, "Lomer"))
    built = [(cfg, r, col, lab, *surface(cfg)) for cfg, r, col, lab in cases]
    cfg0, r0, _, _, s0, ys0, h0, e0 = built[0]
    um = 1e-4
    bounds = s0.boundaries * um
    core = float(e0["position_yz_A"][0])
    depth = float(e0["depth_A"])
    trace = float(cfg0.get("sample.seam_y_A"))

    fig = plt.figure(figsize=(ps.DOUBLE, 4.8))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.5, 1], hspace=0.5, wspace=0.3)
    gsa = gs[0, 0].subgridspec(2, 1, height_ratios=[1, 1.1], hspace=0.1)
    ax_rel = fig.add_subplot(gsa[0])
    ax_xs = fig.add_subplot(gsa[1], sharex=ax_rel)
    ax_ph = fig.add_subplot(gs[1, 0], sharex=ax_rel)
    ax_am = fig.add_subplot(gs[2, 0], sharex=ax_rel)
    ax_z = fig.add_subplot(gs[0:2, 1])
    ax_za = fig.add_subplot(gs[2, 1], sharex=ax_z)

    # a: relief (top) and cross-section (bottom)
    for cfg, r, col, lab, s, ys, h, e in built:
        ax_rel.plot(ys * um, h, color=col, lw=0.8, label=lab)
    ax_rel.set_ylabel("Height (Å)")
    ax_rel.set_xlim(0, s0.Ly * um)
    ax_rel.legend(loc="upper right", ncol=2, handlelength=1.5)
    plt.setp(ax_rel.get_xticklabels(), visible=False)
    strips(ax_rel, bounds)
    ax_xs.axhline(0, color=ps.INK, lw=0.8)
    ax_xs.plot([trace * um, core * um], [0, -depth / 10], color=ps.C1, lw=0.7, ls=(0, (3, 1.5)))
    ax_xs.plot([core * um], [-depth / 10], marker=(3, 0, 0), ms=5, color=ps.ACCENT, zorder=5)
    ax_xs.text(core * um + 0.03, -depth / 10, "dislocation, 50 nm deep", fontsize=5.5, va="center", ha="left",
               color=ps.INK2)
    ax_xs.text(trace * um - 0.03, -20, "60° glide plane\n(1$\\bar{1}$1)", fontsize=5.5, ha="right", va="center",
               color=ps.C1)
    ax_xs.set_ylim(-62, 8)
    ax_xs.set_ylabel("Depth (nm)")
    strips(ax_xs, bounds, labels=False)
    plt.setp(ax_xs.get_xticklabels(), visible=False)
    ps.panel_label(ax_rel, "a", x=-0.085)

    # b, c: full-cell (008) phase and amplitude
    for ax, key, ylab, ref in ((ax_ph, "phase", "(008) phase (rad)", 0.0), (ax_am, "amp", "(008) amplitude", 1.0)):
        ax.axhline(ref, color=ps.GRID, lw=0.5)
        for cfg, r, col, lab, *_ in built:
            prof, src = series(r, key)
            ax.plot(r["y"] * um, prof, color=col, lw=0.8, label=f"{lab} ({src})")
            if src == "multislice":
                ax.plot(r["y"] * um, r[f"{REFL}_geo3_{key}"], color=col, lw=0.6, ls=(0, (3, 1.5)),
                        label=f"{lab} (geometric)")
        ax.set_ylabel(ylab)
        strips(ax, bounds, labels=False)
    ax_ph.legend(loc="lower left", ncol=2, handlelength=2.0)
    plt.setp(ax_ph.get_xticklabels(), visible=False)
    ax_am.set_xlabel("Position across the beam, y (µm)")
    ps.panel_label(ax_ph, "b", x=-0.085)
    ps.panel_label(ax_am, "c", x=-0.085)

    # d, e: zoom over the dislocation, phase relative to the far left of the window
    W = 2000.0
    for cfg, r, col, lab, s, ys, h, e in built:
        y = r["y"]
        win = np.abs(y - core) < W
        ph, src = series(r, "phase")
        am, _ = series(r, "amp")
        left = (y > core - W) & (y < core - W + 300)
        gb = g_dot_b(cfg)
        ax_z.plot((y[win] - core) / 10, ph[win] - np.median(ph[left]), color=col, lw=0.9,
                  label=f"{lab} ({src}), g·b = {gb:+.0f}")
        if gb:
            ax_z.axhline(-2 * np.pi * gb, color=col, lw=0.5, ls=(0, (1, 1)))
            ax_z.text(-W / 10 + 5, -2 * np.pi * gb + 0.3, f"$-2\\pi\\,$g·b = {-2 * gb:.0f}π", fontsize=5.5, color=col,
                      ha="left", va="bottom")
        ax_za.plot((y[win] - core) / 10, am[win], color=col, lw=0.9)
    for ax in (ax_z, ax_za):
        ax.axvline(0, color=ps.ACCENT, lw=0.5, ls=(0, (1, 1)))
        ax.axvline((trace - core) / 10, color=ps.C1, lw=0.5, ls=(0, (3, 1.5)))
    ax_z.set_xlim(-W / 10, W / 10)
    yl = ax_z.get_ylim()
    ax_z.text(2, yl[1], "core", fontsize=5.5, color=ps.ACCENT, va="top", ha="left")
    ax_z.text((trace - core) / 10 - 2, yl[1], "60° slip step", fontsize=5.5, color=ps.C1, va="top", ha="right")
    ax_z.set_ylabel("(008) phase (rad)")
    ax_z.legend(loc="lower left", bbox_to_anchor=(0.0, 0.12), fontsize=5.5, handlelength=2.0)
    plt.setp(ax_z.get_xticklabels(), visible=False)
    ax_za.set_ylabel("(008) amplitude")
    for ax in (ax_am, ax_za):  # sharp steps ring through the aperture; keep the smooth contrast readable
        ax.set_ylim(0.85, 1.1)
    ax_za.set_xlabel("Distance from the core, y (nm)")
    ps.panel_label(ax_z, "d", x=-0.15)
    ps.panel_label(ax_za, "e", x=-0.15)
    ps.save(fig, out / args.stem)
    plt.close(fig)
    print("wrote", out / f"{args.stem}.pdf", "and .png")


if __name__ == "__main__":
    main()
