#!/usr/bin/env python3
"""Export the atomic coordinates used by the multislice: perfect and dislocated cells.

Usage:
  python scripts/export_atoms.py --config configs/smoke/buried_dislocation_cpu.yaml [--out outputs]

Writes to outputs/<config name>/atoms/:
  perfect.xyz, dislocated.xyz   extended XYZ (OVITO, ASE, VESTA via ASE): slab frame, A,
                                columns species, x, y, z and, for the dislocated cell, the
                                displacement ux, uy, uz; periodic along y and z, open along x
  cross_section.png             projection along the beam (z) and zoom on one core
The positions are exactly those passed to reflection_holo.forward.multislice.slice_potentials.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import geometry as geo  # noqa: E402
from reflection_holo.crystal import build_slab  # noqa: E402
from reflection_holo.defects.dislocation import from_config  # noqa: E402
from reflection_holo.provenance import Config  # noqa: E402

FRAME = geo.SI111_FRAME


def write_extxyz(path, pos, Ly, Lz, x_extent, u=None, comment=""):
    x0, x1 = x_extent
    lattice = f"{x1 - x0:.6f} 0 0 0 {Ly:.6f} 0 0 0 {Lz:.6f}"
    props = "species:S:1:pos:R:3" + (":disp:R:3" if u is not None else "")
    with open(path, "w") as f:
        f.write(f"{len(pos)}\n")
        f.write(f'Lattice="{lattice}" Origin="{x0:.6f} 0 0" Properties={props} pbc="F T T" '
                f'frame="x=outward normal [1,-1,1], y=[1,-1,-2], z=beam [110]; A" {comment}\n')
        for i, p in enumerate(pos):
            row = f"Si {p[0]:12.6f} {p[1]:12.6f} {p[2]:12.6f}"
            if u is not None:
                row += f" {u[i, 0]:10.6f} {u[i, 1]:10.6f} {u[i, 2]:10.6f}"
            f.write(row + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    cfg = Config(args.config)
    a = float(cfg.get("crystal.a_A"))
    depth = float(cfg.get("multislice.crystal_depth_A"))
    pos, Ly, Lz = build_slab(FRAME, a, int(cfg.get("multislice.n_y_periods")), depth)
    n_img = int(cfg.get("defects.periodic_images_y"))
    entries = cfg.get("defects.dislocations")
    defects = from_config(entries, float(cfg.get("defects.nu")), a, FRAME, Ly, n_img)
    u = defects.displacement(pos)
    pos_def = pos + u
    pos_def[:, 1] = np.mod(pos_def[:, 1], Ly)
    pos_def[:, 2] = np.mod(pos_def[:, 2], Lz)

    out = Path(args.out) / cfg.data["name"] / "atoms"
    out.mkdir(parents=True, exist_ok=True)
    ext = (-depth - 2.0, 2.0)
    write_extxyz(out / "perfect.xyz", pos, Ly, Lz, ext, comment='state="perfect"')
    write_extxyz(out / "dislocated.xyz", pos_def, Ly, Lz, ext, u=u, comment='state="dislocated"')

    print(f"{len(pos)} atoms; cell y {Ly:.3f} A x z {Lz:.4f} A, x from 0 (surface) to {-depth} A")
    print(f"max |u| = {np.linalg.norm(u, axis=1).max():.3f} A; surface u_x range "
          f"{u[pos[:, 0] > -0.1, 0].min():.3f} to {u[pos[:, 0] > -0.1, 0].max():.3f} A")
    _plot(out, pos, pos_def, u, Ly, entries)
    print(f"written to {out}")


def _plot(out, pos, pos_def, u, Ly, entries):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    y_core, d_core = entries[0]["position_yz_A"][0], entries[0]["depth_A"]
    fig, ax = plt.subplots(1, 2, figsize=(16, 5.5), gridspec_kw={"width_ratios": [2.2, 1]})
    sc = ax[0].scatter(pos_def[:, 1], pos_def[:, 0], c=u[:, 0], s=4, cmap="RdBu_r", vmin=-1.2, vmax=1.2)
    for e in entries:
        ax[0].plot(e["position_yz_A"][0], -e["depth_A"], "k^" if e["sign"] > 0 else "kv", ms=9)
    ax[0].set(xlabel="y (A)", ylabel="x, height (A); surface at 0", xlim=(0, Ly),
              title="dislocated cell viewed along the beam [110], colour = u_x (A); triangles = cores")
    ax[0].set_aspect("equal")
    fig.colorbar(sc, ax=ax[0], shrink=0.7, label="u_x (A)")
    w = 14.0
    sel = (np.abs(pos[:, 1] - y_core) < w + 3) & (np.abs(pos[:, 0] + d_core) < w + 3)
    # the field carries a near-uniform rigid shift (cut convention + periodic images); remove the
    # window mean for display only, so the distortion around the core is visible
    rel = pos[sel] + (u[sel] - u[sel].mean(axis=0))
    ax[1].scatter(pos[sel, 1], pos[sel, 0], s=18, facecolors="none", edgecolors="0.6", label="perfect")
    ax[1].scatter(rel[:, 1], rel[:, 0], s=18, c="C3", label="dislocated (window-mean u removed)")
    ax[1].plot(y_core, -d_core, "k^", ms=10)
    ax[1].axhline(-d_core, color="k", lw=0.5, ls=":")
    ax[1].set(xlim=(y_core - w, y_core + w), ylim=(-d_core - w, -d_core + w), xlabel="y (A)",
              ylabel="x (A)", title="core, projected along [110]; dotted = glide plane (1,-1,1)")
    ax[1].set_aspect("equal")
    ax[1].legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "cross_section.png", dpi=110)


if __name__ == "__main__":
    main()
