#!/usr/bin/env python3
"""Nature-style single-column figures of the supporting results (captions: docs/figures/CAPTIONS.md).

  fig_rocking        flat-surface rocking curves of (008) and (0,0,12), operating angles marked
  fig_reflections    reconstructed phase and amplitude profiles of the three-strip sample by reflection
  fig_convergence    reflectivity vs lateral pixel size; step phase vs illuminated footprint
  fig_step_rows      (0,0,12): reflected intensity and step phase along the image rows

Usage:
  python scripts/figures_results.py --data docs/figures/data \
      --results outputs/si001_three_sections_cpu/reconstruction/results.npz \
      --rows outputs/holo_data/si001_three_sections_cpu/reconstruction/rows_0012.npz --out docs/figures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import plotstyle as ps  # noqa: E402

BOUNDS_NM = [0.0, 15.36, 30.72, 46.08]  # strip boundaries of configs/si001_three_sections_cpu.yaml
CORE_NM = 38.4


def strips(ax):
    for b in BOUNDS_NM[1:-1]:
        ax.axvline(b, color=ps.GRID, lw=0.6, ls=(0, (3, 2)))
    yl = ax.get_ylim()
    for k in range(3):
        ax.text((BOUNDS_NM[k] + BOUNDS_NM[k + 1]) / 2, yl[1], str(k + 1), ha="center", va="bottom", fontsize=6,
                color=ps.INK2)


def fig_rocking(plt, data, out):
    fig, axes = plt.subplots(2, 1, figsize=(ps.SINGLE, 3.3))
    for ax, tag, label, letter in ((axes[0], "008", "(008)", "a"), (axes[1], "0012", "(0,0,12)", "b")):
        d = json.loads((data / f"rocking_001_{tag}.json").read_text())
        th = d["theta_ext_bragg_mrad_V0potential"] + np.array(d["offsets_mrad"])
        R = np.array(d["R"]) * 100
        ax.plot(th, R, color=ps.C1, lw=1.0, marker="o", ms=2.2)
        ax.axvline(d["theta_ext_bragg_mrad_V0potential"], color=ps.INK2, lw=0.6, ls=(0, (3, 2)))
        op = d["theta_ext_bragg_mrad_V0potential"] + d["peak_offset_mrad"]
        ax.plot([op], [d["R_peak"] * 100], marker="v", ms=4, color=ps.C2, zorder=5)
        ax.text(op, d["R_peak"] * 100 * 1.08, "operating angle", ha="center", va="bottom", fontsize=6, color=ps.INK2)
        right = d["peak_offset_mrad"] < 0  # put the Bragg label on the side away from the operating angle
        ax.text(d["theta_ext_bragg_mrad_V0potential"] + (0.08 if right else -0.08), ax.get_ylim()[1] * 0.95,
                "Bragg (refraction-\ncorrected)", ha="left" if right else "right", va="top", fontsize=5.5,
                color=ps.INK2)
        ax.set_ylabel(f"{label} reflected (%)")
        ps.panel_label(ax, letter, x=-0.13)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.18)
    axes[1].set_xlabel("Glancing angle (mrad)")
    fig.tight_layout(h_pad=0.8)
    ps.save(fig, out / "fig_rocking_si001")
    plt.close(fig)


def fig_reflections(plt, results, out):
    r = np.load(results)
    y = r["y"] / 10
    fig, axes = plt.subplots(2, 1, figsize=(ps.SINGLE, 3.5), sharex=True)
    series = [("(0,0,8)", ps.C1, "(008)"), ("(0,0,12)", ps.C2, "(0,0,12)"), ("(0,0,4)", ps.C3, "(004)")]
    for j, (key, ylab) in enumerate((("phase", "Phase (rad)"), ("amp", "Amplitude (rel.)"))):
        ax = axes[j]
        ax.axhline(0 if j == 0 else 1, color=ps.GRID, lw=0.5)
        for name, col, lab in series:
            ms_key, geo_key = f"{name}_ms_{key}", f"{name}_geo3_{key}"
            if ms_key in r.files:
                ax.plot(y, r[ms_key], color=col, lw=1.0, label=f"{lab} multislice")
            if geo_key in r.files:
                ax.plot(y, r[geo_key], color=col, lw=0.7, ls=(0, (3, 1.5)),
                        label=f"{lab} geometric" + (" (only)" if ms_key not in r.files else ""))
        ax.set_xlim(y[0], y[-1])
        ax.set_ylabel(ylab)
        strips(ax)
        ps.panel_label(ax, "ab"[j], x=-0.13)
    axes[0].legend(loc="lower left", ncol=2, handlelength=1.6, columnspacing=1.0)
    axes[1].set_xlabel("Position across beam (nm)")
    fig.tight_layout(h_pad=0.6)
    ps.save(fig, out / "fig_reflections_si001")
    plt.close(fig)


def fig_convergence(plt, data, out):
    c = json.loads((data / "convergence_dy.json").read_text())
    b = json.loads((data / "step_buildup_check.json").read_text())
    fig, axes = plt.subplots(2, 1, figsize=(ps.SINGLE, 3.4))
    ax = axes[0]
    for key, col, lab in (("si111_444", ps.C3, "Si(111) (4,-4,4)"), ("si001_008", ps.C1, "Si(001) (008)"),
                          ("si001_0012", ps.C2, "Si(001) (0,0,12)")):
        ax.plot(c[key]["dy_A"], np.array(c[key]["R"]) * 100, color=col, marker="o", ms=2.5, lw=1.0, label=lab)
    ax.axvspan(0, 0.13, color="#eeeeee", lw=0, zorder=0)
    ax.text(0.065, 0.3, "used", ha="center", fontsize=6, color=ps.INK2)
    ax.set_xscale("linear")
    ax.set_xlim(0, 0.7)
    ax.set_yscale("log")
    ax.set_xlabel("Lateral pixel size (Å)")
    ax.set_ylabel("Reflected (%)")
    ax.legend(loc="lower right", handlelength=1.6)
    ps.panel_label(ax, "a", x=-0.13)
    ax = axes[1]
    for hkl, col, lab in (([0, 0, 8], ps.C1, "(008)"), ([0, 0, 12], ps.C2, "(0,0,12)")):
        rows = [x for x in b if x["hkl"] == hkl]
        fp = np.array([x["footprint_A"] for x in rows]) / 1e4
        dev = np.array([np.angle(np.exp(1j * (x["step_ms_rad"] - x["step_minus_q_ext_h_rad"]))) for x in rows])
        ax.plot(fp, dev, color=col, marker="o", ms=2.5, lw=1.0, label=lab)
    ax.axhline(0, color=ps.GRID, lw=0.5)
    ax.set_xlabel("Illuminated footprint along beam (µm)")
    ax.set_ylabel("Step phase error (rad)")
    ax.legend(loc="lower right", handlelength=1.6)
    ps.panel_label(ax, "b", x=-0.13)
    fig.tight_layout(h_pad=0.8)
    ps.save(fig, out / "fig_convergence")
    plt.close(fig)


def fig_step_rows(plt, rows, out):
    d = np.load(rows)
    x, I1, I2, dp = d["x"], d["I1"], d["I2"], d["dphi21"]
    m = max(I1.max(), I2.max())
    sel = ((I1 > 0.02 * m) | (I2 > 0.02 * m)) & (x > 5)
    t = (x[sel] - x[sel].min()) / 10
    fig, axes = plt.subplots(2, 1, figsize=(ps.SINGLE, 3.2), sharex=True)
    axes[0].plot(t, I1[sel] / m, color=ps.C1, lw=1.0, label="Strip 1 (reference)")
    axes[0].plot(t, I2[sel] / m, color=ps.C2, lw=1.0, label="Strip 2 (raised 0.54 nm)")
    axes[0].set_ylabel("Reflected intensity (rel.)")
    axes[0].legend(loc="upper left", handlelength=1.6)
    axes[0].set_ylim(0, 1.35)
    axes[1].plot(t, dp[sel], color=ps.INK, lw=1.0)
    axes[1].axhline(-1.23, color=ps.C1, lw=0.7, ls=(0, (3, 1.5)))
    axes[1].text(t[-1], -1.23, "geometric model ", ha="right", va="bottom", fontsize=6, color=ps.C1)
    axes[1].set_ylabel("Step phase (rad)")
    axes[1].set_xlabel("Image coordinate along beam (nm)")
    for k, ax in enumerate(axes):
        ps.panel_label(ax, "ab"[k], x=-0.13)
    fig.tight_layout(h_pad=0.6)
    ps.save(fig, out / "fig_step_rows_0012")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="docs/figures/data")
    ap.add_argument("--results", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", default="docs/figures")
    args = ap.parse_args()
    plt = ps.apply()
    data, out = Path(args.data), Path(args.out)
    fig_rocking(plt, data, out)
    fig_reflections(plt, args.results, out)
    fig_convergence(plt, data, out)
    fig_step_rows(plt, args.rows, out)
    print("written: fig_rocking_si001, fig_reflections_si001, fig_convergence, fig_step_rows_0012 (.png/.pdf)")


if __name__ == "__main__":
    main()
