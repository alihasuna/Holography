#!/usr/bin/env python3
"""Render a multi-section sample (e.g. configs/si001_three_sections_cpu.yaml).

Usage:
  python scripts/render_sections.py --config configs/si001_three_sections_cpu.yaml [--out outputs]

Writes to outputs/<config name>/sample/:
  endon.png         the simulation cell viewed along the beam, bonds drawn, zooms on the step and
                    on the dislocation core with the terminating (extra) atomic columns in red
  block3d.png       3D block of a REDUCED-SIZE copy built by the same code (illustration only)
  sample.xyz        extended XYZ of the full simulation cell (species, position, displacement, section)
  checks.txt        atom counts, merged atoms, seam strain, nearest-neighbour distances
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import geometry as geo  # noqa: E402
from reflection_holo.defects.dislocation import from_config  # noqa: E402
from reflection_holo.provenance import Config  # noqa: E402
from reflection_holo.structure.sections import build_sections, nearest_neighbour_distances  # noqa: E402

FRAMES = {"CFG-B": geo.SI001_FRAME, "CFG-A": geo.SI111_FRAME}
SEC_COLORS = ["#4C78A8", "#54A24B", "#B279A2"]
BOND = 2.6


def frame_of(cfg):
    return FRAMES[cfg.data["configuration"].split()[0]]


def build(cfg, periods=None, depth=None, disl_override=None, seam_y="config"):
    a = float(cfg.get("crystal.a_A"))
    frame = frame_of(cfg)
    periods = periods or cfg.get("sample.periods_per_section")
    depth = depth or float(cfg.get("sample.depth_A"))
    entries = disl_override or cfg.get("defects.dislocations")
    if seam_y == "config":
        seam_y = cfg.get("sample.seam_y_A")
    defects = from_config(entries, float(cfg.get("defects.nu")), a, frame, None, 0)
    perfect = build_sections(frame, a, periods, cfg.get("sample.raise_layers"), depth)
    sample = build_sections(frame, a, periods, cfg.get("sample.raise_layers"), depth, defects, seam_y=seam_y)
    return perfect, sample, entries


def bonds(pos, Ly, Lz, n_z=1):
    """Bond segments (minimum image in y and z) as pairs of 3D points."""
    from scipy.spatial import cKDTree

    shift = np.array([pos[:, 0].min() - 1.0, 0, 0])
    t = cKDTree(pos - shift, boxsize=[1e9, Ly, Lz * n_z])
    pairs = t.query_pairs(BOND, output_type="ndarray")
    d = pos[pairs[:, 1]] - pos[pairs[:, 0]]
    d[:, 1] -= Ly * np.round(d[:, 1] / Ly)
    d[:, 2] -= Lz * n_z * np.round(d[:, 2] / (Lz * n_z))
    return pos[pairs[:, 0]], pos[pairs[:, 0]] + d


def extra_columns(pos, yc, xc, half_width=12.0):
    """Atoms of the (220) columns that terminate near the core: the extra half-plane(s)."""
    win = (np.abs(pos[:, 1] - yc) < half_width) & (pos[:, 0] > xc - 1.0)
    P = pos[win]
    idx = np.where(win)[0]
    ends = []
    for k, p in enumerate(P):
        if abs(p[1] - yc) > 4.0 or p[0] > xc + 4.0:
            continue
        below = (np.abs(P[:, 1] - p[1]) < 0.9) & (P[:, 0] < p[0] - 0.5) & (P[:, 0] > p[0] - 6.0)
        if not below.any():
            ends.append(k)
    members = set()
    for k in ends:  # walk up the column
        y = P[k, 1]
        col = np.where((np.abs(P[:, 1] - y) < 1.2) & (P[:, 0] >= P[k, 0] - 0.1))[0]
        members.update(idx[col].tolist())
    return np.array(sorted(members), int)


def endon(out, sample, entries, Lz):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    pos = sample.positions
    A, B = bonds(pos, sample.Ly, Lz)
    seg = np.stack([A[:, [1, 0]], B[:, [1, 0]]], axis=1)
    e = entries[0]
    yc, xc = e["position_yz_A"][0], -e["depth_A"]
    extra = extra_columns(pos, yc, xc)

    fig = plt.figure(figsize=(17, 9.5))
    ax0 = fig.add_axes([0.04, 0.56, 0.93, 0.40])
    for k in range(len(sample.heights)):
        y0, y1 = sample.boundaries[k], sample.boundaries[k + 1]
        ax0.axvspan(y0, y1, color=SEC_COLORS[k], alpha=0.08, lw=0)
        label = ["1: reference", f"2: raised {sample.heights[k]:.2f} A", "3: buried edge dislocation"][k] \
            if len(sample.heights) == 3 else f"section {k + 1}"
        ax0.text(0.5 * (y0 + y1), 9.5, label, ha="center", fontsize=11, color=SEC_COLORS[k], weight="bold")
    ax0.add_collection(LineCollection(seg, colors="0.55", linewidths=0.35))
    ax0.scatter(pos[:, 1], pos[:, 0], s=1.5, c=[SEC_COLORS[s] for s in sample.section], zorder=3)
    ax0.plot(yc, xc, marker="$\\perp$", color="red", ms=16, zorder=5)
    ax0.annotate("beam along [110], into the page, at 16 mrad to the surface", (5, -62), fontsize=9)
    ax0.set(xlim=(0, sample.Ly), ylim=(-64, 13), xlabel="y along [1-10] (A)", ylabel="x along [001] (A)",
            title="Si(001) three-section sample, simulation cell viewed along the beam (all atoms of one 3.84 A period)")
    ax0.set_aspect("equal")

    # zoom on the up-step 1 -> 2
    ax1 = fig.add_axes([0.04, 0.05, 0.42, 0.44])
    yb = sample.boundaries[1]
    _zoom(ax1, pos, seg, sample, (yb - 14, yb + 14), (-14, 7), extra=None)
    ax1.set_title("step between sections 1 and 2 (+4 layers = a = 5.43 A)")
    # zoom on the core
    ax2 = fig.add_axes([0.52, 0.05, 0.45, 0.44])
    _zoom(ax2, pos, seg, sample, (yc - 16, yc + 16), (xc - 11, 2.5), extra=extra)
    ax2.plot(yc, xc, marker="$\\perp$", color="red", ms=22, zorder=6)
    ax2.set_title("section 3: Lomer edge dislocation 25 A deep; red = extra half-plane (2 x (220) columns)")
    fig.savefig(out / "endon.png", dpi=120)
    plt.close(fig)
    return extra


def _zoom(ax, pos, seg, sample, ylim, xlim, extra):
    from matplotlib.collections import LineCollection

    ax.add_collection(LineCollection(seg, colors="0.35", linewidths=1.0))
    c = np.array([SEC_COLORS[s] for s in sample.section], dtype=object)
    ax.scatter(pos[:, 1], pos[:, 0], s=40, c=list(c), edgecolors="k", linewidths=0.4, zorder=3)
    if extra is not None and len(extra):
        ax.scatter(pos[extra, 1], pos[extra, 0], s=60, c="red", edgecolors="k", linewidths=0.5, zorder=4)
    ax.set(xlim=ylim, ylim=xlim, xlabel="y (A)", ylabel="x (A)")
    ax.set_aspect("equal")


def block3d(out, cfg, n_z=5):
    """Reduced-size copy (6 periods per section, 16 A deep, core 8 A deep) drawn as a 3D block."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection

    py = 3.8402262179460216  # a/2[1-10]
    per = [6] * len(cfg.get("sample.periods_per_section"))
    e = copy.deepcopy(cfg.get("defects.dislocations")[0])
    e["depth_A"] = 8.0
    e["position_yz_A"] = [py * (sum(per) - per[-1] / 2), 0.0]
    _, s, _ = build(cfg, periods=per, depth=16.0, disl_override=[e], seam_y=py * per[0] / 2)
    extra = extra_columns(s.positions, e["position_yz_A"][0], -e["depth_A"], half_width=8.0)
    is_extra = np.zeros(len(s.positions), bool)
    is_extra[extra] = True
    pos = np.concatenate([s.positions + np.array([0, 0, k * s.Lz]) for k in range(n_z)])
    sec = np.tile(s.section, n_z)
    ext = np.tile(is_extra, n_z)
    A, B = bonds(pos, s.Ly, s.Lz, n_z)
    keep = (np.abs(B[:, 1] - A[:, 1]) < s.Ly / 2) & (np.abs(B[:, 2] - A[:, 2]) < s.Lz * n_z / 2)
    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    seg = np.stack([A[keep][:, [1, 2, 0]], B[keep][:, [1, 2, 0]]], axis=1)
    ax.add_collection3d(Line3DCollection(seg, colors="0.25", linewidths=0.7, alpha=0.7))
    col = np.array([SEC_COLORS[k] for k in sec], dtype=object)
    col[ext] = "red"
    ax.scatter(pos[:, 1], pos[:, 2], pos[:, 0], s=np.where(ext, 34, 22), c=list(col),
               edgecolors="k", linewidths=0.3, depthshade=False)
    yc, xc = e["position_yz_A"][0], -e["depth_A"]
    ax.plot([yc, yc], [-3, s.Lz * n_z + 3], [xc, xc], color="red", lw=3)
    ax.text(yc + 2, -6, xc - 2, "dislocation line (along the beam)", color="red", fontsize=10)
    names = ["1 reference", "2 raised +4 layers (5.43 A)", "3 buried edge dislocation"]
    for k in range(3):
        ax.text(0.5 * (s.boundaries[k] + s.boundaries[k + 1]), s.Lz * n_z, s.heights[k] + 4,
                names[k], color=SEC_COLORS[k], weight="bold", ha="center", fontsize=11)
    ax.quiver(s.Ly * 0.25, s.Lz * n_z + 12, 9, 0, -10, -0.5, color="darkorange", lw=2.5, arrow_length_ratio=0.25)
    ax.text(s.Ly * 0.25, s.Lz * n_z + 14, 11, "e- beam [110]\n(grazing)", color="darkorange", fontsize=10)
    ax.set_box_aspect((s.Ly, s.Lz * n_z + 10, 24))
    ax.set(xlim=(0, s.Ly), ylim=(-5, s.Lz * n_z + 5), zlim=(-17, 7))
    ax.view_init(elev=16, azim=-72)
    ax.set_axis_off()
    fig.suptitle("Si(001) three-section sample: reduced-size 3D illustration built with the same code "
                 "(6 periods per section, core 8 A deep); red = extra half-plane", fontsize=11)
    fig.savefig(out / "block3d.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    cfg = Config(args.config)
    out = Path(args.out) / cfg.data["name"] / "sample"
    out.mkdir(parents=True, exist_ok=True)
    perfect, s, entries = build(cfg)
    nn = nearest_neighbour_distances(s)
    extra = endon(out, s, entries, s.Lz)
    block3d(out, cfg)
    lines = [
        f"cell: Ly = {s.Ly:.3f} A (y, [1-10]), Lz = {s.Lz:.4f} A (z, beam [110]), depth {cfg.get('sample.depth_A')} A",
        f"section boundaries (A): {np.round(s.boundaries, 2).tolist()}; terrace heights (A): {np.round(s.heights, 4).tolist()}",
        f"atoms: perfect {len(perfect.positions)}, with dislocation {len(s.positions)} "
        f"(difference {len(s.positions) - len(perfect.positions)} = extra half-plane atoms per 3.84 A period)",
        f"builder info: {s.info}",
        f"nearest-neighbour distance: min {nn[:, 0].min():.3f} A, atoms with NN < 2.0 A: {(nn[:, 0] < 2.0).sum()}",
        f"highest atom per section (A): {[round(float(s.positions[s.section == k, 0].max()), 3) for k in range(len(s.heights))]}",
        f"atoms highlighted as extra half-plane: {len(extra)}",
    ]
    (out / "checks.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    with open(out / "sample.xyz", "w") as f:
        f.write(f"{len(s.positions)}\n")
        x0 = s.positions[:, 0].min() - 2
        f.write(f'Lattice="{s.positions[:, 0].max() + 2 - x0:.6f} 0 0 0 {s.Ly:.6f} 0 0 0 {s.Lz:.6f}" '
                f'Origin="{x0:.6f} 0 0" Properties=species:S:1:pos:R:3:disp:R:3:section:I:1 pbc="F T T" '
                f'frame="x=[001] outward normal, y=[1-10], z=beam [110]; A"\n')
        for p, u, k in zip(s.positions, s.displacement, s.section):
            f.write(f"Si {p[0]:12.6f} {p[1]:12.6f} {p[2]:12.6f} {u[0]:10.6f} {u[1]:10.6f} {u[2]:10.6f} {k + 1}\n")
    print(f"written to {out}")


if __name__ == "__main__":
    main()
