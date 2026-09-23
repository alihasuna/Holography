#!/usr/bin/env python3
"""Quick-look figures of a pipeline smoke run: the atomic supercell and the complex exit wave.

Usage: venv/bin/python tools/plots/smoke_figures.py --config configs/demo_smoke_si001.yaml \
          --variant multislice_tiny --run-dir <out>/multislice_tiny --geometric-run-dir <out>/geometric \
          --out <dir>
DEMO data (configs/demo_*.yaml): not comparable to experiment. Frame: x = outward normal,
y = in-plane transverse, z = beam azimuth (reflection_holo.geometry.frames). exp(+ik.r), numpy FFT.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reflection_holo.pipeline.config import load_pipeline_file
from reflection_holo.pipeline.engines import build_structure, reflection_cell

TERRACE_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a"]   # categorical slots 1-3 (validated, light mode)
INK, MUTED = "#1f1f1e", "#6b6a64"


def supercell_figure(cfg_path, variant, out):
    cfg = load_pipeline_file(cfg_path, variant=variant)
    structure = build_structure(cfg)
    cell = reflection_cell(structure, cfg)
    xyz = np.asarray(cell.atoms_xyz_A)
    tmap = cell.metadata.get("terrace_map") or structure.metadata["terrace_map"]
    # terrace index of each atom from its along-beam coordinate (s_range_A is along z from crystal start)
    z_rel = xyz[:, 2] - cell.crystal_start_z_A
    tid = np.full(len(xyz), -1)
    for t in tmap:
        s0, s1 = t["s_range_A"]
        tid[(z_rel >= s0 - 1e-6) & (z_rel < s1 - 1e-6)] = t["index"]
    fig = plt.figure(figsize=(15, 8.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.25], hspace=0.38, wspace=0.28)
    ax = fig.add_subplot(gs[0, :])
    sel = np.abs(xyz[:, 1] - np.median(xyz[:, 1])) < 1.0     # thin slab in y for the side view
    for t in tmap:
        m = sel & (tid == t["index"])
        ax.scatter(xyz[m, 2], xyz[m, 0], s=0.6, color=TERRACE_COLOURS[t["index"] % 3], rasterized=True)
        zc = cell.crystal_start_z_A + 0.5 * sum(t["s_range_A"])
        ax.text(zc, cell.surface_x_A + 4.5, f"terrace {t['index']}  (top layer +{t['top_layer_relative']} x a/4)",
                ha="center", va="bottom", fontsize=9, color=INK)
    ax.axhline(cell.surface_x_A, color=MUTED, lw=0.8, ls=(0, (4, 3)))
    ax.set_xlabel("z along the beam (A)"); ax.set_ylabel("x, outward normal (A)")
    ax.set_title(f"Si(001) supercell, side view (atoms within 1 A of the y mid-plane); {len(xyz):,} atoms, "
                 f"box {cell.extent_x_A:.0f} x {cell.extent_y_A:.1f} x {cell.length_z_A:.0f} A (x, y, z)",
                 fontsize=10, color=INK, loc="left")
    ax.set_xlim(0, cell.length_z_A); ax.set_ylim(xyz[:, 0].min() - 2, cell.surface_x_A + 12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    # zooms on the two in-field steps (0->1 a/2 up-step, 1->2 a/4 down-step)
    for k, (i, j) in enumerate([(0, 1), (1, 2)]):
        zs = cell.crystal_start_z_A + tmap[i]["s_range_A"][1]
        axz = fig.add_subplot(gs[1, k])
        top = cell.surface_x_A + 4
        m = sel & (np.abs(xyz[:, 2] - zs) < 12) & (xyz[:, 0] > top - 16)
        for t in (i, j):
            mm = m & (tid == t)
            axz.scatter(xyz[mm, 2] - zs, xyz[mm, 0], s=26, color=TERRACE_COLOURS[t % 3],
                        edgecolor="white", linewidth=0.6, label=f"terrace {t}")
        dh = (tmap[j]["top_layer_relative"] - tmap[i]["top_layer_relative"]) * (5.4309 / 4)
        kind = "a/2 translation step" if abs(abs(dh) - 2.71545) < 1e-3 else "a/4 screw/glide step"
        axz.set_title(f"step {i}->{j}: {kind}, dh = {dh:+.4f} A", fontsize=10, color=INK, loc="left")
        axz.set_xlabel("z - z_step (A)"); axz.set_ylabel("x (A)")
        axz.legend(frameon=False, fontsize=8, loc="lower left")
        for s in ("top", "right"):
            axz.spines[s].set_visible(False)
    # top view of the top layers across the a/4 step: back-bond direction of each terrace
    axt = fig.add_subplot(gs[1, 2])
    zs = cell.crystal_start_z_A + tmap[1]["s_range_A"][1]
    for t in (1, 2):
        ztop = cell.surface_x_A + (tmap[t]["top_layer_relative"]) * 5.4309 / 4
        m = (tid == t) & (np.abs(xyz[:, 2] - zs) < 12) & (np.abs(xyz[:, 0] - ztop) < 0.5)
        m2 = (tid == t) & (np.abs(xyz[:, 2] - zs) < 12) & (np.abs(xyz[:, 0] - (ztop - 5.4309 / 4)) < 0.5)
        axt.scatter(xyz[m2, 2] - zs, xyz[m2, 1], s=10, color=TERRACE_COLOURS[t % 3], alpha=0.35)
        axt.scatter(xyz[m, 2] - zs, xyz[m, 1], s=26, color=TERRACE_COLOURS[t % 3], edgecolor="white",
                    linewidth=0.6, label=f"terrace {t}: back-bonds along {tmap[t]['top_layer_backbond_axis_crystal']}")
    axt.set_xlim(-12, 12); axt.set_ylim(0, min(12, cell.extent_y_A))
    axt.set_xlabel("z - z_step (A), beam direction"); axt.set_ylabel("y (A)")
    axt.set_title("top view across the a/4 step (top layer solid, next layer faint)", fontsize=10, color=INK, loc="left")
    axt.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.32))
    axt.set_aspect("equal")
    fig.suptitle("demo_smoke_si001 (multislice_tiny): DEMO structure, bulk-terminated, not comparable to experiment",
                 fontsize=11, color=INK, x=0.01, ha="left")
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    return dict(n_atoms=len(xyz), box=(cell.extent_x_A, cell.extent_y_A, cell.length_z_A))


def exitwave_figure(run_dir, geo_dir, out):
    z = np.load(pathlib.Path(run_dir) / "arrays.npz")
    s = json.load(open(pathlib.Path(run_dir) / "summary.json"))
    psi = z["exit_psi_r0"]; x = z["exit_x_A"]; y = z["exit_y_A"]
    lam = s["wavelength_A"]; th = s["glancing_angle"]
    fig, axs = plt.subplots(2, 2, figsize=(13, 9.6))
    ext = [y[0], y[-1], x[0], x[-1]]
    a = axs[0, 0].imshow(np.abs(psi), origin="lower", aspect="auto", extent=ext, cmap="Greys_r")
    fig.colorbar(a, ax=axs[0, 0], label="|psi|")
    axs[0, 0].set_title("exit wave amplitude |psi(x, y)| on the exit plane", loc="left", fontsize=10)
    p = axs[0, 1].imshow(np.angle(psi), origin="lower", aspect="auto", extent=ext, cmap="twilight",
                         vmin=-np.pi, vmax=np.pi)
    fig.colorbar(p, ax=axs[0, 1], label="arg psi (rad), cyclic")
    axs[0, 1].set_title("exit wave phase arg psi(x, y)", loc="left", fontsize=10)
    for ax in axs[0]:
        ax.set_xlabel("y, in-plane transverse (A)"); ax.set_ylabel("x, outward normal (A)")
    # Fourier space: numpy FFT sign, kx in cycles/A -> angle theta = lambda * q
    F = np.fft.fftshift(np.fft.fft2(psi))
    qx = np.fft.fftshift(np.fft.fftfreq(len(x), x[1] - x[0])); qy = np.fft.fftshift(np.fft.fftfreq(len(y), y[1] - y[0]))
    ang_x = lam * qx * 1e3; ang_y = lam * qy * 1e3
    I = np.log10(np.abs(F) ** 2 + 1e-12 * np.abs(F).max() ** 2)
    f = axs[1, 0].imshow(I, origin="lower", aspect="auto", cmap="Greys",
                         extent=[ang_y[0], ang_y[-1], ang_x[0], ang_x[-1]])
    fig.colorbar(f, ax=axs[1, 0], label="log10 |FFT psi|^2")
    th_in = th.get("theta_rad") or th.get("value_rad")
    if th_in:
        for v, lab in ((-th_in * 1e3, "incident (-theta)"), (th_in * 1e3, "specular (+theta)")):
            axs[1, 0].axhline(v, color="#2a78d6" if v > 0 else "#eb6834", lw=0.8, ls=(0, (4, 3)))
            axs[1, 0].text(ang_y[0] + 0.5, v + 0.6, lab, fontsize=8, color=INK)
    axs[1, 0].set_xlabel("theta_y = lambda q_y (mrad)"); axs[1, 0].set_ylabel("theta_x = lambda q_x (mrad)")
    axs[1, 0].set_ylim(-60, 60)
    axs[1, 0].set_title("exit wave in Fourier space (transverse angles)", loc="left", fontsize=10)
    # geometric-engine complex phase along the surface after dark-field selection and projection
    g = np.load(pathlib.Path(geo_dir) / "arrays.npz")
    pr = g["projected_r0"]; zs = g["projected_surface_z_A"]
    ph = np.angle(pr.mean(axis=1)); amp = np.abs(pr).mean(axis=1)
    ax = axs[1, 1]
    ax.plot(zs, np.unwrap(ph), color="#2a78d6", lw=2, label="phase (unwrapped), geometric engine")
    ax.set_xlabel("surface coordinate z_s along the beam (A)"); ax.set_ylabel("phase (rad)")
    ax2 = ax.twinx(); ax2.plot(zs, amp, color=MUTED, lw=1)
    ax2.set_ylabel("|psi| (mean over y)", color=MUTED); ax2.tick_params(colors=MUTED)
    ax.set_title("dark-field wave projected onto the surface (geometric engine)", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle(f"complex exit wave, multislice_tiny: {s['engine'].get('status', s['engine'].get('label', ''))[:110]}",
                 fontsize=9.5, x=0.01, ha="left", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(out, dpi=150); plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--variant", required=True)
    ap.add_argument("--run-dir", required=True); ap.add_argument("--geometric-run-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(); o = pathlib.Path(a.out); o.mkdir(parents=True, exist_ok=True)
    info = supercell_figure(a.config, a.variant, o / "supercell.png")
    exitwave_figure(a.run_dir, a.geometric_run_dir, o / "exit_wave_complex.png")
    print(info, "->", o)
