#!/usr/bin/env python3
"""Compact half-torus figure (trench and ridge side by side) for the supervisor page (orchestrator).

Reads the arrays.npz and summary.json of the two geometric-engine pipeline runs of
configs/demo_smoke_torus_{trench,ridge}.yaml (the same files as tools/plots/torus_geometric.py, whose
loader is reused so that axes and planes are asserted). DEMO data, not comparable to experiment.
Panels per feature: object hologram, reconstructed wrapped phase, where a height is measurable
(reason codes), and the built height profile across the ring with the measured points.

Usage: venv/bin/python tools/plots/torus_compact.py --trench DIR --ridge DIR --out PNG
"""
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap, BoundaryNorm  # noqa: E402

_HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("torus_geometric", _HERE / "torus_geometric.py")
tg = importlib.util.module_from_spec(_spec)
sys.modules["torus_geometric"] = tg
_spec.loader.exec_module(tg)

INK, MUTED = "#1f1f1e", "#6b6a64"


def panel_row(axes, run_dir: pathlib.Path, label: str) -> str:
    s, a = tg._load(run_dir)
    u, y = a["detector_u_A"], a["detector_y_A"]
    cols = slice(None)
    ext = tg._extent(u, y)
    # 1. hologram
    im = axes[0].imshow(a["hologram_object_counts"], extent=ext, aspect="auto", cmap="gray",
                        interpolation="nearest")
    axes[0].set_title(f"{label}: object hologram (counts)", fontsize=9, color=INK, loc="left")
    plt.colorbar(im, ax=axes[0], fraction=0.035, pad=0.02)
    # 2. wrapped phase
    im = axes[1].imshow(a["phase_wrapped"], extent=ext, aspect="auto", cmap="twilight", vmin=-np.pi,
                        vmax=np.pi, interpolation="nearest")
    axes[1].set_title("reconstructed wrapped phase (rad)", fontsize=9, color=INK, loc="left")
    plt.colorbar(im, ax=axes[1], fraction=0.035, pad=0.02)
    # 3. measurable map: 1 = height returned, 0 = masked
    m = a["measurable"].astype(int)
    cmap = ListedColormap(["#d9d9d6", "#2a78d6"])
    axes[2].imshow(m, extent=ext, aspect="auto", cmap=cmap, norm=BoundaryNorm([-0.5, 0.5, 1.5], 2),
                   interpolation="nearest")
    frac = 100.0 * m.sum() / m.size
    axes[2].set_title(f"height measurable (blue): {frac:.1f} % of pixels; on the ring: 0", fontsize=9,
                      color=INK, loc="left")
    for ax in axes[:3]:
        ax.set_xlabel("across the beam y (Å)", fontsize=8, color=MUTED)
        ax.set_ylabel("along the beam u (Å, image)", fontsize=8, color=MUTED)
        ax.tick_params(labelsize=7, colors=MUTED)
    # 4. profile across the ring: the built shape evaluated on the ring's centre line z_c (as in
    # torus_geometric.py) and the measured heights of the y cut at their own traced source positions
    from reflection_holo.structure.shapes import HalfTorus
    sh = s["feature"]["shape"]
    torus = HalfTorus(sh["center_y_A"], sh["center_z_A"], sh["major_radius_A"], sh["minor_radius_A"],
                      sh["sub_kind"], sh["label"], sh["source"])
    layer = s["feature"]["layer_spacing_A"]
    yy = np.linspace(y[0], y[-1], 20001)
    axes[3].plot(yy, torus.continuous_height_A(yy, torus.center_z_A), color=MUTED, lw=1, ls="--",
                 label="built (continuous)")
    axes[3].plot(yy, torus.layer_height_A(yy, torus.center_z_A, layer_spacing_A=layer), color=INK, lw=1,
                 label="built (a/4 layers)")
    ycut = a["cut_y_y_A"]
    meas = a["cut_y_measurable"].astype(bool)
    axes[3].errorbar(ycut[meas], a["cut_y_h_meas_A"][meas], yerr=3 * a["cut_y_sigma_h_A"][meas],
                     fmt=".", ms=2, color="#2a78d6", ecolor="#2a78d6", elinewidth=0.6,
                     label="measured h (±3σ), flat surface only")
    axes[3].set_xlabel("across the beam y (Å)", fontsize=8, color=MUTED)
    axes[3].set_ylabel("height (Å)", fontsize=8, color=MUTED)
    axes[3].tick_params(labelsize=7, colors=MUTED)
    axes[3].set_title("profile across the ring at its centre", fontsize=9, color=INK, loc="left")
    axes[3].legend(fontsize=7, frameon=False)
    for sp in ("top", "right"):
        axes[3].spines[sp].set_visible(False)
    return s["quantification"].get("resolution", "") if isinstance(s.get("quantification"), dict) else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trench", required=True, type=pathlib.Path)
    ap.add_argument("--ridge", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    a = ap.parse_args()
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), facecolor="white")
    panel_row(axes[0], a.trench, "trench (atoms removed)")
    panel_row(axes[1], a.ridge, "ridge (atoms added)")
    fig.suptitle("Half-torus (R = 1000 Å, r = 20 Å) on Si(001), geometric engine, demo conditions "
                 "(not comparable to experiment): the flat surface reconstructs, the ring does not",
                 fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(a.out, dpi=130)
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
