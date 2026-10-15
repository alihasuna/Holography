#!/usr/bin/env python3
"""
geometry_diagram.py
===================
Generate publication-quality schematic diagrams of the reflection
electron diffraction geometry for the Si[110] / (1-11) experiment.

Produces:
  1. Real-space geometry (beam, crystal, surface, angles)
  2. Reciprocal-space Ewald construction
  3. Peng-Cowley supercell frame
  4. Detector mapping

Usage:
    python -m simulation.geometry_diagram
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc, Rectangle, Wedge
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

from simulation.constants import K_200KV, LAMBDA_200KV, SI_LATTICE_PARAM


def draw_real_space(ax):
    """Diagram 1: Real-space reflection geometry."""
    ax.set_xlim(-1.5, 8)
    ax.set_ylim(-3, 4.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # crystal body (filled region below surface)
    crystal = Rectangle((-1.5, -3), 9.5, 3, facecolor="#2a2a5a",
                         edgecolor="none", alpha=0.8)
    ax.add_patch(crystal)

    # crystal lattice dots
    for ix in np.arange(-1, 8, 0.8):
        for iy in np.arange(-2.5, 0, 0.7):
            ax.plot(ix, iy, "o", color="#6666aa", markersize=2.5, alpha=0.5)

    # surface line
    ax.plot([-1.5, 8], [0, 0], "-", color="#e94560", linewidth=2.5)
    ax.text(8.1, 0, "surface\n$(1\\bar{1}1)$", fontsize=8, color="#e94560",
            va="center")

    # vacuum label
    ax.text(3.5, 3.5, "VACUUM", fontsize=12, color="#aaaacc",
            ha="center", fontweight="bold", alpha=0.5)
    ax.text(3.5, -2.2, "CRYSTAL (Si)", fontsize=10, color="#8888bb",
            ha="center", fontweight="bold", alpha=0.6)

    # incident beam
    # beam comes from upper-left at grazing angle alpha
    alpha_deg = 1.6
    alpha_rad = np.radians(alpha_deg)
    beam_len = 6.0
    bx0 = 3.5 - beam_len * np.cos(alpha_rad)
    by0 = beam_len * np.sin(alpha_rad)
    ax.annotate("", xy=(3.5, 0), xytext=(bx0, by0),
                arrowprops=dict(arrowstyle="-|>", color="#44ff44",
                                lw=2.5, mutation_scale=15))
    ax.text(bx0 + 0.5, by0 - 0.3, "$\\mathbf{k}_i$\n(200 kV beam)",
            fontsize=9, color="#44ff44", fontweight="bold")

    # grazing angle arc
    arc = Arc((3.5, 0), 3.0, 3.0, angle=0, theta1=0,
              theta2=alpha_deg * 15,  # exaggerated for visibility
              color="#ffcc00", linewidth=1.5)
    ax.add_patch(arc)
    ax.text(5.2, 0.35, "$\\alpha \\approx 28$ mrad\n($1.6^\\circ$)",
            fontsize=8, color="#ffcc00")

    # reflected beam (specular)
    rx1 = 3.5 + beam_len * 0.7 * np.cos(alpha_rad)
    ry1 = beam_len * 0.7 * np.sin(alpha_rad)
    ax.annotate("", xy=(rx1, ry1), xytext=(3.5, 0),
                arrowprops=dict(arrowstyle="-|>", color="#ff8844",
                                lw=2, mutation_scale=12))
    ax.text(rx1 - 0.5, ry1 + 0.3, "specular\n(000 reflected)",
            fontsize=7, color="#ff8844")

    # Bragg reflected beam (at larger angle)
    bragg_angle = alpha_rad + 0.15  # exaggerated
    bx1 = 3.5 + beam_len * 0.6 * np.cos(bragg_angle)
    by1 = beam_len * 0.6 * np.sin(bragg_angle)
    ax.annotate("", xy=(bx1, by1), xytext=(3.5, 0),
                arrowprops=dict(arrowstyle="-|>", color="#ff4444",
                                lw=1.5, mutation_scale=10, linestyle="--"))
    ax.text(bx1 - 1.2, by1 + 0.3, "Bragg\n$\\mathbf{k}_f = \\mathbf{k}_i + \\mathbf{g}$",
            fontsize=7, color="#ff4444")

    # penetration depth arrow
    ax.annotate("", xy=(1.5, -1.2), xytext=(1.5, 0),
                arrowprops=dict(arrowstyle="<->", color="#88ccff", lw=1.2))
    ax.text(1.7, -0.6, "$d_\\perp \\sim 5$ nm", fontsize=7, color="#88ccff")

    # surface normal arrow
    ax.annotate("", xy=(6.5, 2.0), xytext=(6.5, 0),
                arrowprops=dict(arrowstyle="-|>", color="#e94560",
                                lw=1.5, mutation_scale=10))
    ax.text(6.7, 1.0, "$\\hat{n}$", fontsize=10, color="#e94560",
            fontweight="bold")

    # beam direction label
    ax.text(3.5, -0.4, "[110] zone axis", fontsize=7, color="#88ff88",
            ha="center", style="italic")

    # shadow edge annotation
    ax.plot([3.5, 3.5], [0, 0.15], "|", color="white", markersize=8)

    ax.set_title("Real-Space Reflection Geometry", fontsize=11,
                 color="white", fontweight="bold", pad=10)


def draw_ewald(ax):
    """Diagram 2: Ewald sphere construction at grazing incidence."""
    ax.set_xlim(-4, 6)
    ax.set_ylim(-3.5, 4.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # reciprocal lattice points (2D projection)
    for h in range(-3, 5):
        for k in range(-2, 4):
            x = h * 1.2
            y = k * 1.0
            color = "#555588"
            size = 3
            # highlight allowed reflections
            if (h + k) % 2 == 0:  # simplified rule for diagram
                color = "#8888cc"
                size = 5
            ax.plot(x, y, "o", color=color, markersize=size, alpha=0.6)

    # Ewald sphere (large radius, shown as arc)
    R = 8.0  # exaggerated radius for visibility
    alpha = 0.12  # grazing angle (exaggerated)
    cx = -R * np.cos(alpha)
    cy = R * np.sin(alpha)
    theta = np.linspace(-0.3, 0.5, 200)
    ex = cx + R * np.cos(theta)
    ey = cy - R * np.sin(theta)
    ax.plot(ex, ey, "-", color="#ffcc00", linewidth=2, alpha=0.8)
    ax.text(ex[0] - 0.3, ey[0] + 0.3, "Ewald sphere\n($R = K$)",
            fontsize=7, color="#ffcc00")

    # origin and k_i
    ax.plot(0, 0, "o", color="white", markersize=8, zorder=5)
    ax.text(0.2, -0.3, "O", fontsize=9, color="white", fontweight="bold")

    # k_i vector
    ax.annotate("", xy=(0, 0), xytext=(cx, cy),
                arrowprops=dict(arrowstyle="-|>", color="#44ff44",
                                lw=2, mutation_scale=12))
    ax.text(cx + 0.3, cy + 0.3, "$-\\mathbf{k}_i$", fontsize=9,
            color="#44ff44")

    # surface normal direction
    ax.annotate("", xy=(0, 3.5), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color="#e94560",
                                lw=1.2, mutation_scale=8, linestyle="--"))
    ax.text(0.2, 3.2, "$\\hat{n}$", fontsize=9, color="#e94560")

    # surface plane (horizontal line through origin)
    ax.plot([-3.5, 5.5], [0, 0], "--", color="#e94560", linewidth=0.8, alpha=0.5)

    # mark some excited reflections (where Ewald sphere passes near lattice points)
    for h, k in [(1, 0), (2, 1), (0, 1), (-1, 1), (1, 1)]:
        x = h * 1.2
        y = k * 1.0
        dist = np.sqrt((x - cx)**2 + (y - cy)**2) - R
        if abs(dist) < 0.5:
            ax.plot(x, y, "o", color="#ff4444", markersize=9,
                    markerfacecolor="none", markeredgewidth=2)

    # reflected beams go upward
    ax.text(3, 3, "reflected\nbeams", fontsize=7, color="#ff8844",
            ha="center", style="italic")
    ax.annotate("", xy=(2.5, 2.8), xytext=(2.4, 1.0),
                arrowprops=dict(arrowstyle="-|>", color="#ff8844",
                                lw=1, mutation_scale=8))

    ax.set_title("Ewald Sphere at Grazing Incidence", fontsize=11,
                 color="white", fontweight="bold", pad=10)


def draw_peng_cowley_frame(ax):
    """Diagram 3: The Peng-Cowley supercell frame."""
    ax.set_xlim(-1, 9)
    ax.set_ylim(-3.5, 4)
    ax.set_aspect("equal")
    ax.axis("off")

    # vacuum region
    vac = Rectangle((-0.5, 0), 8, 3.5, facecolor="#111133", edgecolor="none")
    ax.add_patch(vac)

    # crystal region
    cryst = Rectangle((-0.5, -3), 8, 3, facecolor="#2a2a5a", edgecolor="none")
    ax.add_patch(cryst)

    # surface at y=0
    ax.plot([-0.5, 7.5], [0, 0], "-", color="#e94560", linewidth=2.5)

    # lattice dots in crystal
    for ix in np.arange(0, 7.5, 1.0):
        for iy in np.arange(-2.5, 0, 0.6):
            ax.plot(ix, iy, "s", color="#6666aa", markersize=3, alpha=0.4)

    # axis arrows
    # z arrow (beam, horizontal)
    ax.annotate("", xy=(8.5, -1.5), xytext=(0, -1.5),
                arrowprops=dict(arrowstyle="-|>", color="#44ff44", lw=2.5))
    ax.text(8.6, -1.5, "$z = [110]$\n(beam)", fontsize=8,
            color="#44ff44", va="center")

    # y arrow (surface normal, vertical)
    ax.annotate("", xy=(0, 3.8), xytext=(0, -1.5),
                arrowprops=dict(arrowstyle="-|>", color="#e94560", lw=2.5))
    ax.text(-0.8, 3.5, "$y = [\\bar{1}1\\bar{1}]$\n(normal)", fontsize=8,
            color="#e94560", ha="center")

    # x arrow (into page, small)
    ax.plot(0, -1.5, "o", color="#4488ff", markersize=12, markerfacecolor="none",
            markeredgewidth=2)
    ax.plot(0, -1.5, ".", color="#4488ff", markersize=4)
    ax.text(-0.8, -2.2, "$x = [\\bar{1}1 2]$\n(in-surface)", fontsize=7,
            color="#4488ff", ha="center")

    # beam direction with tilt
    ax.annotate("", xy=(7, -0.3), xytext=(1, -0.3),
                arrowprops=dict(arrowstyle="-|>", color="#44ff44",
                                lw=1.5, linestyle="--", mutation_scale=10))

    # tilted beam (slightly downward toward crystal)
    ax.annotate("", xy=(7, -0.7), xytext=(1, 0.1),
                arrowprops=dict(arrowstyle="-|>", color="#88ff88",
                                lw=2, mutation_scale=12))
    ax.text(4, 0.5, "tilted beam\n($\\alpha = 28$ mrad)", fontsize=7,
            color="#88ff88", ha="center")

    # absorber region
    absorber = Rectangle((-0.5, -3), 8, 0.6, facecolor="#440000",
                          edgecolor="none", alpha=0.5)
    ax.add_patch(absorber)
    ax.text(3.5, -2.8, "absorber (semi-$\\infty$ bulk)", fontsize=7,
            color="#ff6666", ha="center", alpha=0.8)

    # labels
    ax.text(4, 2.5, "VACUUM ($y > 0$)", fontsize=9, color="#aaaacc",
            ha="center", alpha=0.6)
    ax.text(4, -1.8, "CRYSTAL ($y < 0$)", fontsize=9, color="#8888bb",
            ha="center", alpha=0.6)

    # slice lines
    for z in np.arange(0.5, 7.5, 1.0):
        ax.plot([z, z], [-3, 3.5], "-", color="#333355", linewidth=0.3, alpha=0.5)
    ax.text(7, -2.8, "slices\n($\\Delta z$)", fontsize=6, color="#555577")

    ax.set_title("Peng-Cowley Supercell Frame", fontsize=11,
                 color="white", fontweight="bold", pad=10)


def draw_cl3_tilt(ax):
    """Diagram 4: CL3 beam tilt decomposition."""
    ax.set_xlim(-5, 5)
    ax.set_ylim(-4, 4)
    ax.set_aspect("equal")
    ax.axis("off")

    # detector plane (x-y plane of zone-axis frame)
    ax.add_patch(Rectangle((-4.5, -3.5), 9, 7, facecolor="#0a0a1a",
                            edgecolor="#333355", linewidth=1))

    # ZA frame axes
    ax.annotate("", xy=(4.2, 0), xytext=(-4.2, 0),
                arrowprops=dict(arrowstyle="-|>", color="#666688", lw=1))
    ax.text(4.3, -0.3, "$\\hat{x}_{det} = [1\\bar{1}0]$", fontsize=7,
            color="#666688")

    ax.annotate("", xy=(0, 3.8), xytext=(0, -3.8),
                arrowprops=dict(arrowstyle="-|>", color="#666688", lw=1))
    ax.text(0.2, 3.5, "$\\hat{y}_{det} = [00\\bar{1}]$", fontsize=7,
            color="#666688")

    # CL3 tilt vector
    tx, ty = 53.2, 26.7  # mrad
    scale = 0.05
    ax.annotate("", xy=(tx*scale, ty*scale), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color="#ffcc00", lw=3,
                                mutation_scale=15))
    ax.text(tx*scale + 0.3, ty*scale + 0.3,
            f"CL3 tilt\n$\\theta_x = {tx:.1f}$ mrad\n$\\theta_y = {ty:.1f}$ mrad\n"
            f"total = 59.5 mrad",
            fontsize=7, color="#ffcc00")

    # surface normal projection in detector plane
    # n_proj in ZA frame: n_x = 2/sqrt(6) ~ 0.816, n_y = -1/sqrt(3) ~ -0.577
    nx, ny = 0.816, -0.577
    proj_scale = 3.0
    ax.annotate("", xy=(nx*proj_scale, ny*proj_scale), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color="#e94560", lw=2,
                                mutation_scale=12, linestyle="--"))
    ax.text(nx*proj_scale + 0.2, ny*proj_scale - 0.4,
            "$\\hat{n}$ projected\nonto detector",
            fontsize=7, color="#e94560")

    # grazing component (projection of CL3 tilt onto n_proj)
    # grazing = tilt . n_hat
    grazing = tx * 0.816 + ty * (-0.577)  # ~28 mrad
    g_vec = np.array([nx, ny]) * grazing * scale / np.sqrt(nx**2 + ny**2)
    ax.annotate("", xy=(g_vec[0], g_vec[1]), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color="#ff8844", lw=2,
                                mutation_scale=10))
    ax.text(g_vec[0] - 1.5, g_vec[1] - 0.5,
            f"grazing\ncomponent\n$\\alpha = {grazing:.0f}$ mrad",
            fontsize=7, color="#ff8844")

    # in-surface component
    in_surf = np.array([tx, ty]) * scale - g_vec
    ax.annotate("", xy=(tx*scale, ty*scale), xytext=(g_vec[0], g_vec[1]),
                arrowprops=dict(arrowstyle="-|>", color="#4488ff", lw=1.5,
                                mutation_scale=8, linestyle="--"))
    ax.text(tx*scale - 2, ty*scale + 0.8,
            "in-surface\n(azimuthal)",
            fontsize=6, color="#4488ff")

    # origin
    ax.plot(0, 0, "o", color="white", markersize=6)
    ax.text(-0.5, 0.3, "O\n(on-zone)", fontsize=7, color="white")

    ax.set_title("CL3 Beam Tilt Decomposition", fontsize=11,
                 color="white", fontweight="bold", pad=10)


def main():
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), facecolor="#0d0d1a")
    fig.subplots_adjust(hspace=0.25, wspace=0.15)

    draw_real_space(axes[0, 0])
    draw_ewald(axes[0, 1])
    draw_peng_cowley_frame(axes[1, 0])
    draw_cl3_tilt(axes[1, 1])

    fig.suptitle("Reflection Electron Diffraction: Si[110] / $(1\\bar{1}1)$ at 200 kV",
                 fontsize=16, color="#e94560", fontweight="bold", y=0.98)

    fig.text(0.5, 0.005,
             "H. Ballouk, CAMTEC, University of Victoria | "
             f"$\\lambda$ = {LAMBDA_200KV:.5f} A | "
             f"K = {K_200KV:.1f} A$^{{-1}}$ | "
             f"a$_{{Si}}$ = {SI_LATTICE_PARAM:.3f} A",
             ha="center", fontsize=8, color="#555577")

    from pathlib import Path
    outdir = Path(__file__).resolve().parent.parent / "simulation_results"
    outdir.mkdir(exist_ok=True)

    outpath = outdir / "geometry_schematic.pdf"
    fig.savefig(str(outpath), dpi=300, facecolor=fig.get_facecolor(),
                bbox_inches="tight", format="pdf")
    print(f"Saved: {outpath}")

    outpath_tiff = outdir / "geometry_schematic.tiff"
    fig.savefig(str(outpath_tiff), dpi=200, facecolor=fig.get_facecolor(),
                bbox_inches="tight", format="tiff")
    print(f"Saved: {outpath_tiff}")

    plt.close()


if __name__ == "__main__":
    main()
