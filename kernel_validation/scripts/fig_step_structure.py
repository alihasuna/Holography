"""Atomic coordinates of the simulated single-layer (a/4) step on Si(001) and their Nature-style figure.

Rebuilds the structure exactly as run_step_quick.py simulates it: bulk-terminated Si(001), x = [110]
(beam), y = [-110], z = [001] outward; the cell repeats one surface unit (3.840 x 3.840 A) per atomic
layer; for x >= 0 (the step, at a period boundary) the top atomic layer is removed. Writes
outputs/si001_a4_step_region.xyz (extended XYZ, A) and figures/fig_step_structure.{pdf,png}.
Style: the repository's Nature style (reflection_holo/plotstyle.py at the repository root).
"""
import importlib.util, pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parent                                   # repository root (kernel_validation/ lives in it)
PLOTSTYLE = next(p for p in (ROOT / "reflection_holo/plotstyle.py", HERE.parents[2] / "ee/reflection_holo/plotstyle.py") if p.exists())
sys.path.insert(0, str(HERE))
from reflection_holo.multislice import cell as CL
from reflection_holo.geometry import Surface
from reflection_holo.constants import A_SI

spec = importlib.util.spec_from_file_location("plotstyle", PLOTSTYLE)
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)

a = A_SI.value
unit, disp, per = CL._unit_with_termination(Surface((0, 0, 1), (1, 1, 0)), a, None)
px, py, pz = per
BOND = a * np.sqrt(3) / 4


def build(nx_lo, nx_hi, ny, ncell_z, step=True):
    pts = []
    for i in range(nx_lo, nx_hi):
        for j in range(ny):
            for k in range(ncell_z):
                q = unit + np.array([i * px, j * py, -k * pz])
                if step and i >= 0:
                    q = q[q[:, 2] < -a / 8]          # top atomic layer removed on the lower terrace
                pts.append(q)
    P = np.vstack(pts)
    layer = np.rint(-P[:, 2] / (a / 4)).astype(int)
    return P, layer


def bonds(P):
    from scipy.spatial import cKDTree
    pr = cKDTree(P).query_pairs(BOND * 1.05)
    return np.array(sorted(pr))


# ---- coordinates file -------------------------------------------------------------------------
P, lay = build(-10, 10, 4, 3)
xyz = HERE / "outputs" / "si001_a4_step_region.xyz"
with open(xyz, "w") as f:
    f.write(f"{len(P)}\n")
    f.write(f'Lattice="{20*px:.6f} 0 0 0 {4*py:.6f} 0 0 0 {3*pz:.6f}" Properties=species:S:1:pos:R:3:layer:I:1 '
            f'pbc="F T F" comment="Si(001) bulk-terminated, x=[110] beam, y=[-110], z=[001]; a/4 down-step at x=0 '
            f'(top layer removed for x>=0); a={a} A; region x in [{-10*px:.2f},{10*px:.2f}) A of the simulated cell"\n')
    for (x, y, z), l in zip(P, lay):
        f.write(f"Si {x:12.6f} {y:12.6f} {z:12.6f} {l:3d}\n")
print("wrote", xyz, len(P), "atoms")

# ---- figure -------------------------------------------------------------------------------------
plt = ps.apply()
from matplotlib.lines import Line2D
def col(l):
    """layer 0 orange, layer 1 blue, deeper layers grey"""
    return ps.C2 if l == 0 else (ps.C1 if l == 1 else "#9a9a9a")


def backbond_axis(P, lay, l_top, xsel):
    """in-plane direction ('x' or 'y') of bonds from layer l_top to l_top+1, computed from the coordinates"""
    Bx = bonds(P); v = []
    for i, j in Bx:
        if {lay[i], lay[j]} == {l_top, l_top + 1} and xsel(P[i, 0]):
            d = P[j] - P[i]; v.append(np.abs(d[:2]))
    v = np.array(v).mean(axis=0)
    return ("x" if v[0] > v[1] else "y"), v

fig = plt.figure(figsize=(ps.DOUBLE, 0.55 * ps.DOUBLE))
gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.15], width_ratios=[1.6, 1, 1], hspace=0.30, wspace=0.32)

# a: side view along y (x-z), around the step
Pa, la = build(-6, 6, 1, 2)
ax = fig.add_subplot(gs[0, :])
B = bonds(Pa)
for i, j in B:
    ax.plot(Pa[[i, j], 0], Pa[[i, j], 2], color="#bdbdbd", lw=0.6, zorder=1)
for l in sorted(set(la)):
    m = la == l
    ax.scatter(Pa[m, 0], Pa[m, 2], s=14, color=col(l), edgecolor=ps.INK, linewidth=0.3, zorder=3)
ax.axvline(0, color=ps.INK, lw=0.5, ls=(0, (2, 2)))
ax.annotate("", xy=(-14, 2.2), xytext=(-22, 2.6), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=ps.INK))
ax.text(-22.5, 2.75, "beam (θ = 16.25 mrad, drawn steeper)", fontsize=6, va="bottom")
ax.text(-12, 0.9, "terrace A", fontsize=6, ha="center"); ax.text(12, 0.9, "terrace B (layer 0 removed)", fontsize=6, ha="center")
ax.set_xlim(-23.5, 23.5); ax.set_ylim(-10.5, 3.6); ax.set_aspect("equal")
ax.set_xlabel("x along beam [110] (Å)"); ax.set_ylabel("z [001] (Å)")
ps.panel_label(ax, "a")
handles = [Line2D([], [], marker="o", ls="", color=col(0), mec=ps.INK, mew=0.3, ms=4, label="layer 0"),
           Line2D([], [], marker="o", ls="", color=col(1), mec=ps.INK, mew=0.3, ms=4, label="layer 1 (a/4 below)"),
           Line2D([], [], marker="o", ls="", color=col(2), mec=ps.INK, mew=0.3, ms=4, label="deeper layers")]
ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, handletextpad=0.3, columnspacing=1.0, borderaxespad=0.1)

# b, c: end-on views along the beam (y-z) of terraces A and B, 4 periods in y
for k, (lab, side) in enumerate([("c", "A"), ("d", "B")]):
    Pb, lb = build(-3, -2, 4, 2) if side == "A" else build(2, 3, 4, 2)
    axb = fig.add_subplot(gs[1, 1 + k])
    for i, j in bonds(Pb):
        axb.plot(Pb[[i, j], 1], Pb[[i, j], 2], color="#bdbdbd", lw=0.6, zorder=1)
    for l in sorted(set(lb)):
        m = lb == l
        axb.scatter(Pb[m, 1], Pb[m, 2], s=14, color=col(l), edgecolor=ps.INK, linewidth=0.3, zorder=3)
    axb.set_xlim(-0.8, 4 * py + 0.8); axb.set_ylim(-10.5, 1.4); axb.set_aspect("equal")
    axb.set_xlabel("y [−110] (Å)")
    if k == 0: axb.set_ylabel("z [001] (Å)")
    else: axb.tick_params(labelleft=False)
    axb.text(0.5, 1.02, f"terrace {side}, viewed along the beam", transform=axb.transAxes, ha="center", fontsize=6)
    ps.panel_label(axb, lab)

# d: top view (x-y) of the exposed layer on both sides with back-bonds to the layer below
Pd, ld = build(-4, 4, 3, 1)
axd = fig.add_subplot(gs[1, 0])
Bd = bonds(Pd)
for i, j in Bd:
    li, lj = ld[i], ld[j]
    top_side = (Pd[i, 0] < 0 and min(li, lj) == 0) or (Pd[i, 0] >= 0 and min(li, lj) == 1)
    if top_side and abs(li - lj) == 1:
        axd.plot(Pd[[i, j], 0], Pd[[i, j], 1], color=col(min(li, lj)), lw=1.0, zorder=2)
for side, l in (("A", 0), ("B", 1)):
    m = (ld == l) & ((Pd[:, 0] < 0) if side == "A" else (Pd[:, 0] >= 0))
    axd.scatter(Pd[m, 0], Pd[m, 1], s=16, color=col(l), edgecolor=ps.INK, linewidth=0.3, zorder=3)
    m2 = (ld == l + 1) & ((Pd[:, 0] < 0) if side == "A" else (Pd[:, 0] >= 0))
    axd.scatter(Pd[m2, 0], Pd[m2, 1], s=6, color="white", edgecolor=ps.INK2, linewidth=0.3, zorder=2)
axd.axvline(0, color=ps.INK, lw=0.5, ls=(0, (2, 2)))
axd.set_xlim(-4 * px - 0.5, 4 * px + 0.5); axd.set_ylim(-0.8, 3 * py + 0.3); axd.set_aspect("equal")
axd.set_xlabel("x along beam [110] (Å)"); axd.set_ylabel("y [−110] (Å)")
axA, vA = backbond_axis(Pd, ld, 0, lambda x: x < 0); axB, vB = backbond_axis(Pd, ld, 1, lambda x: x >= 0)
print(f"back-bond in-plane |components| A (layer0->1): {vA}, -> along {axA};  B (layer1->2): {vB}, -> along {axB}")
axd.text(-2 * px, 3 * py + 0.5, f"A: back-bonds along {axA}", ha="center", fontsize=6, color=col(0))
axd.text(2 * px, 3 * py + 0.5, f"B: back-bonds along {axB}", ha="center", fontsize=6, color=col(1))
ps.panel_label(axd, "b")
out = HERE / "figures"; out.mkdir(exist_ok=True)
ps.save(fig, str(out / "fig_step_structure"))
print("saved", out / "fig_step_structure.png")
