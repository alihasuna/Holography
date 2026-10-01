#!/usr/bin/env python3
"""Nature-style figure of the simulated Si(001) three-strip sample (caption: docs/figures/CAPTIONS.md).

  a  the simulation cell viewed along the beam [110] (one 0.384 nm period projected)
  b  the step between strips 1 and 2 (bonds drawn)
  c  the Lomer dislocation core; the extra half-plane is red

Usage: python scripts/figures_structure.py --config configs/si001_three_sections_cpu.yaml --out docs/figures
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reflection_holo import plotstyle as ps  # noqa: E402
from reflection_holo.provenance import Config  # noqa: E402
from render_sections import bonds, build, extra_columns  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="docs/figures")
    args = ap.parse_args()
    cfg = Config(args.config)
    _, s, entries = build(cfg)
    pos = s.positions
    yc, xc = entries[0]["position_yz_A"][0], -entries[0]["depth_A"]
    extra = extra_columns(pos, yc, xc)
    A, B = bonds(pos, s.Ly, s.Lz)
    keep = np.abs(B[:, 1] - A[:, 1]) < 5
    seg = np.stack([A[keep][:, [1, 0]], B[keep][:, [1, 0]]], axis=1) / 10

    plt = ps.apply()
    from matplotlib.collections import LineCollection

    fig = plt.figure(figsize=(ps.DOUBLE, 3.3))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.9, 1.25], left=0.06, right=0.99, top=0.9, bottom=0.11,
                          hspace=0.45, wspace=0.18)
    ax = fig.add_subplot(gs[0, :])
    ax.add_collection(LineCollection(seg, colors="#9a9a9a", linewidths=0.15))
    ax.scatter(pos[:, 1] / 10, pos[:, 0] / 10, s=0.25, c="#333333", lw=0)
    ax.scatter(pos[extra, 1] / 10, pos[extra, 0] / 10, s=0.6, c=ps.ACCENT, lw=0)
    for b in s.boundaries[1:-1]:
        ax.axvline(b / 10, color=ps.C1, lw=0.5, ls=(0, (3, 2)))
    names = ["1  Reference", "2  Raised 0.54 nm (4 layers)", f"3  Lomer dislocation {-xc/10:.1f} nm deep"]
    for k in range(3):
        ax.text((s.boundaries[k] + s.boundaries[k + 1]) / 20, 1.0, names[k], ha="center", va="bottom", fontsize=6.5)
    ax.plot(yc / 10, xc / 10, marker="$\\perp$", ms=7, color=ps.ACCENT)
    ax.set(xlim=(0, s.Ly / 10), ylim=(-5.8, 0.9))
    ax.set_xlabel("Position across beam, [1-10] (nm)")
    ax.set_ylabel("Height, [001] (nm)")
    ax.set_aspect("equal")
    ps.panel_label(ax, "a", x=-0.035, y=1.08)
    windows = ((s.boundaries[1] / 10 + np.array([-1.8, 1.8]), (-2.5, 0.7), "b", False),
               (yc / 10 + np.array([-1.8, 1.8]), (-2.9, 0.3), "c", True))  # same 3.6 x 3.2 nm window
    for j, (yl, xl, letter, show_extra) in enumerate(windows):
        axz = fig.add_subplot(gs[1, j])
        axz.add_collection(LineCollection(seg, colors="#7a7a7a", linewidths=0.6))
        axz.scatter(pos[:, 1] / 10, pos[:, 0] / 10, s=9, c="#d9d9d9", edgecolors="#333333", linewidths=0.4, zorder=3)
        if show_extra:
            axz.scatter(pos[extra, 1] / 10, pos[extra, 0] / 10, s=11, c=ps.ACCENT, edgecolors="#333333",
                        linewidths=0.4, zorder=4)
            axz.plot(yc / 10, xc / 10, marker="$\\perp$", ms=12, color=ps.ACCENT, zorder=5)
        axz.set(xlim=yl, ylim=xl)
        axz.set_aspect("equal")
        axz.set_anchor("E" if j == 0 else "W")
        axz.set_xlabel("Position across beam (nm)")
        axz.set_ylabel("Height (nm)")
        ps.panel_label(axz, letter, x=-0.12)
    ps.save(fig, Path(args.out) / "fig_sample_si001")
    plt.close(fig)
    print("written: fig_sample_si001 (.png/.pdf)")


if __name__ == "__main__":
    main()
