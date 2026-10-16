"""Complex exit wave of the a/4 down-step on Si(001), (008) specular, 200 keV, theta = 16.25 mrad, W = 0.

Input: outputs/step_quick_a4_full.npz (run_step_quick.py, N_LAYERS=1, SAVE_FULL=1). Exit plane x = L = 5.0 um;
the step is at x_step = 1.5 um, so the exit-plane crystal is terrace B. The incident strip ends at
X_END = 4.0 um, so the vacuum at the exit plane holds only reflected/diffusely scattered waves.
A ray reflected at surface point x_hit crosses the exit plane at height h = theta (L - x_hit).
Checks printed: flux partition, consistency with step_quick.npz / step_quick_analysis.npz, rod partition.
Style: repository Nature style (reflection_holo/plotstyle.py at the repository root).
"""
import sys, pathlib, importlib.util
import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parent                                   # repository root (kernel_validation/ lives in it)
PLOTSTYLE = next(p for p in (ROOT / "reflection_holo/plotstyle.py", HERE.parents[2] / "ee/reflection_holo/plotstyle.py") if p.exists())
spec = importlib.util.spec_from_file_location("plotstyle", PLOTSTYLE)
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
sys.path.insert(0, str(HERE / "scripts"))
from analyse_step_quick import object_wave

d = np.load(HERE / "outputs" / "step_quick_a4_full.npz", allow_pickle=True)
ew = d["ew_step"].astype(complex); psi0 = d["psi0"].astype(complex)
z = d["z"]; zs = float(d["zs"]); dy = float(d["dy"]); dz = float(d["dz"]); ny = int(d["ny"])
th = float(d["theta"]); lam = float(d["lam"]); L = float(d["L"]); xst = float(d["x_step"]); a = float(d["a"])
K = 2 * np.pi / lam; k0 = K * np.sin(th); X_END = 40000.0
zB = zs - a / 4                                   # terrace-B top layer (exit plane lies on terrace B)
hz = z - zs                                       # height above terrace-A top layer

# ---------- flux partition (psi0 normalised to unit flux by run_step_quick) ----------
fl = lambda f, m=slice(None): float(np.sum(np.abs(f[m]) ** 2) * dy * dz)
F_in = fl(psi0); F_out = fl(ew)
vac = hz > 5.0; cry = hz <= 5.0
F_vac = fl(ew, vac); F_cry = fl(ew, cry)
# rod decomposition of the vacuum part: FFT along y gives G_y = m * 2 pi / b, b = ny dy (one surface period)
b = ny * dy
Ey = np.fft.fft(ew, axis=1) / ny                  # column m = rod m
rod_flux = {m: float(np.sum(np.abs(Ey[vac, m % ny]) ** 2) * b * dz) for m in range(-3, 4)}
print(f"flux in {F_in:.4f}; out {F_out:.4f} (rest absorbed by bottom absorber slice)")
print(f"  vacuum (h > 5 A) {F_vac:.4f} = {F_vac/F_out:.3f} of out;  crystal {F_cry:.4f}")
print("  vacuum rods: " + ", ".join(f"m={m:+d}: {v:.4f}" for m, v in rod_flux.items()))

# ---------- consistency with earlier saved runs ----------
prof = ew.mean(axis=1)
old = np.load(HERE / "outputs" / "step_quick.npz")
print(f"y-mean vs step_quick.npz prof_step: max|diff| = {np.abs(prof - old['prof_step']).max():.2e}"
      f" (max|prof| {np.abs(prof).max():.3f})")
an = np.load(HERE / "outputs" / "step_quick_analysis.npz")
s_o, o_new = object_wave(old, prof)
print(f"object wave (back-propagated to step) vs step_quick_analysis o_step: max|diff| = {np.abs(o_new - an['o_step']).max():.2e}")

# ---------- specular (G_y = 0) component in the exit plane, carrier removed ----------
a_inc = float(old["a_inc"])
spec0 = Ey[:, 0] * np.exp(-1j * k0 * hz) / a_inc   # reflected plane wave travels +z: carrier exp(+i k0 h)
h_A = th * (L - xst)                               # h above which rays come from terrace A
h_lo = th * (L - X_END)                            # lowest height reached by reflected rays
bandA = (hz > h_A + 60) & (hz < th * L - 40); bandB = (hz > h_lo + 40) & (hz < h_A - 60)
phA = np.angle(np.mean(spec0[bandA])); spec_r = spec0 * np.exp(-1j * phA)
far = (hz > h_lo + 40) & (hz < h_lo + 120)         # far downstream part of terrace B (x_hit 3.3-3.8 um)
print(f"exit plane: h_A = {h_A:.0f} A, h_lo = {h_lo:.0f} A")
print(f"  |spec|^2 terrace A band {np.mean(np.abs(spec0[bandA])**2):.3f}, terrace B band {np.mean(np.abs(spec0[bandB])**2):.3f}")
print(f"  arg(B/A) far-downstream B band {np.angle(np.mean(spec_r[far])):+.3f} rad; geometric 2K sin(th) h mod 2pi"
      f" {np.angle(np.exp(1j*2*K*np.sin(th)*a/4)):+.3f}")

# ---------- 2D angular spectrum of the vacuum part ----------
pad = 1 << int(np.ceil(np.log2(4 * len(z))))
Vz = np.where(vac[:, None], ew, 0)
Fz = np.fft.fft(Ey * vac[:, None], n=pad, axis=0)
kz = 2 * np.pi * np.fft.fftfreq(pad, dz); ang = kz / K * 1e3     # exit angle (mrad) to the surface
order = np.argsort(ang)
spec_I = {m: np.abs(Fz[order, m % ny]) ** 2 for m in (0, 1, -1, 2)}
norm = spec_I[0].max()
pk = ang[order][np.argmax(spec_I[0])]
print(f"specular rod peak at {pk:.2f} mrad (incidence {th*1e3:.2f})")
inap = np.abs(ang[order] - th * 1e3) < 1.0
for m in (1, 2):
    pred = np.sqrt(th**2 - (m * lam / b)**2) * 1e3
    obs = ang[order][np.argmax(spec_I[m])]
    print(f"rod m={m}: peak exit angle {obs:.2f} mrad; elastic prediction sqrt(theta^2-(m lam/b)^2) = {pred:.2f} mrad")
print(f"fraction of m=0 vacuum spectral weight inside 1 mrad aperture: {spec_I[0][inap].sum()/spec_I[0].sum():.3f}")

# ---------- figure ----------
plt = ps.apply()
from matplotlib.gridspec import GridSpec
fig = plt.figure(figsize=(ps.DOUBLE, 0.62 * ps.DOUBLE))
gs = GridSpec(2, 6, figure=fig, height_ratios=[1, 0.9], hspace=0.55, wspace=1.6,
              left=0.08, right=0.985, top=0.94, bottom=0.10)
win = (hz > -14) & (hz < 6)
nt = 3; yy = np.arange(nt * ny) * dy
W = np.tile(ew[win], (1, nt)) / a_inc; hw = hz[win]
ext = [0, nt * b, hw[0], hw[-1]]
atoms = [at for at in d["upper_atoms"]]
def overlay(ax):
    for at in atoms:
        for yv, zv in at:
            if zv > zs - 0.5:                     # top layer removed on terrace B
                continue
            if zv - zs < -14: continue
            for t in range(nt):
                ax.plot(yv + t * b, zv - zs, "o", ms=2.2, mfc="none", mec="white", mew=0.4)
    ax.axhline(zB - zs, color="white", lw=0.4, ls=(0, (2, 2)))
ax = fig.add_subplot(gs[0, 0:2])
im = ax.imshow(np.abs(W), origin="lower", extent=ext, aspect="auto", cmap="magma")
overlay(ax); ax.set_xlabel("y [−110] (Å)"); ax.set_ylabel("z − z$_s$ (Å)")
cb = fig.colorbar(im, ax=ax, fraction=0.06, pad=0.03); cb.ax.set_title("|ψ|/|ψ$_{inc}$|", fontsize=5.5, pad=3)
ax.set_title("amplitude, exit plane (terrace B)", fontsize=6.5)
ps.panel_label(ax, "a", x=-0.26, y=1.04)
ax = fig.add_subplot(gs[0, 2:4])
ph = np.angle(W * np.exp(-1j * k0 * hw)[:, None])
im = ax.imshow(ph, origin="lower", extent=ext, aspect="auto", cmap=ps.phase_cmap(), vmin=-np.pi, vmax=np.pi)
overlay(ax); ax.set_xlabel("y [−110] (Å)"); ax.set_ylabel("z − z$_s$ (Å)")
cb = fig.colorbar(im, ax=ax, fraction=0.06, pad=0.03, ticks=[-np.pi, 0, np.pi]); cb.ax.set_yticklabels(["−π", "0", "π"])
cb.ax.set_title("rad", fontsize=5.5, pad=3)
ax.set_title("phase arg ψ − k$_0$(z − z$_s$)", fontsize=6.5)
ps.panel_label(ax, "b", x=-0.26, y=1.04)
ax = fig.add_subplot(gs[0, 4:6])
cols = {0: ps.C1, 1: ps.C2, 2: "#9a9a9a"}
labs = {0: "m = 0 (specular)", 1: "m = ±1", 2: "m = ±2"}
for m in (2, 1, 0):
    ax.semilogy(ang[order], spec_I[m] / norm + 1e-12, color=cols[m], lw=0.6, label=labs[m])
    if m:
        ax.plot(np.sqrt(th**2 - (m * lam / b)**2) * 1e3, 5 * spec_I[m].max() / norm, "v", ms=3, color=cols[m], clip_on=False)
ax.axvspan(th * 1e3 - 1, th * 1e3 + 1, color=ps.GRID, alpha=0.6, lw=0)
ax.set_xlim(0, 50); ax.set_ylim(1e-7, 30)
from matplotlib.lines import Line2D; from matplotlib.patches import Patch
ax.set_xlabel("exit angle k$_z$/K (mrad)"); ax.set_ylabel("vacuum spectral intensity")
h_, l_ = ax.get_legend_handles_labels(); h_ = h_[::-1] + [Line2D([], [], marker="v", ls="", color=ps.INK2, ms=3), Patch(color=ps.GRID, alpha=0.6, lw=0)]
l_ = l_[::-1] + ["elastic √(θ² − (mλ/b)²)", "±1 mrad aperture"]
ax.legend(h_, l_, loc="upper right", borderaxespad=0.2, frameon=False, fontsize=5.5, handlelength=1.2)
from matplotlib.lines import Line2D; from matplotlib.patches import Patch
ps.panel_label(ax, "c", x=-0.30, y=1.04)
ax.set_title("angular spectrum per rod", fontsize=6.5)
# bottom row: specular component across the vacuum band
sel = (hz > 0) & (hz < th * L + 20)
xh = (L - hz[sel] / th) / 1e4                    # surface hit point (um)
ax = fig.add_subplot(gs[1, 0:3])
ax.plot(xh, np.abs(spec_r[sel]) ** 2, color=ps.C1, lw=0.6)
ax.axvline(xst / 1e4, color=ps.INK, lw=0.5, ls=(0, (2, 2)))
ax.set_xlim(0, L / 1e4); ax.set_ylim(0, 0.85)
ax.set_xlabel("surface hit point x = L − h/θ (µm)"); ax.set_ylabel("|ψ$_{00}$|² / |ψ$_{inc}$|²")
ax.text(0.75, 0.78, "terrace A", ha="center", fontsize=6); ax.text(2.75, 0.78, "terrace B", ha="center", fontsize=6)
ax.axvspan(X_END / 1e4, L / 1e4, color=ps.GRID, alpha=0.5, lw=0)
ax.text(4.5, 0.45, "not\nilluminated", ha="center", fontsize=5.5, color=ps.INK2)
sec = ax.secondary_xaxis("top", functions=(lambda x: th * (L - x * 1e4), lambda h: (L - h / th) / 1e4))
sec.set_xlabel("height above surface in exit plane h (Å)", fontsize=6)
ps.panel_label(ax, "d", x=-0.10, y=1.10)
ax = fig.add_subplot(gs[1, 3:6])
m_ok = (np.abs(spec_r[sel]) ** 2 > 0.05) & (xh < X_END / 1e4)
p = np.where(m_ok, np.angle(spec_r[sel]), np.nan)
ax.plot(xh, p, color=ps.C2, lw=0.6)
ax.axvline(xst / 1e4, color=ps.INK, lw=0.5, ls=(0, (2, 2)))
geo = np.angle(np.exp(1j * 2 * K * np.sin(th) * a / 4))
ax.axhline(geo, color=ps.INK2, lw=0.5, ls=(0, (1, 1))); ax.axvspan(X_END / 1e4, L / 1e4, color=ps.GRID, alpha=0.5, lw=0)
ax.text(2.4, geo + 0.22, "geometric 2Kh sinθ (mod 2π)", fontsize=5.5, color=ps.INK2)
ax.set_xlim(0, L / 1e4); ax.set_ylim(-np.pi, np.pi); ax.set_yticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
ax.set_yticklabels(["−π", "−π/2", "0", "π/2", "π"])
ax.set_xlabel("surface hit point x (µm)"); ax.set_ylabel("arg ψ$_{00}$ − arg ψ$_{00}$(A) (rad)")
ps.panel_label(ax, "e", x=-0.10, y=1.10)
out = HERE / "figures"; out.mkdir(exist_ok=True)
ps.save(fig, str(out / "fig_exit_wave"))
np.savez(HERE / "outputs" / "exit_wave_analysis.npz", hz=hz, spec0=spec0, spec_r=spec_r, ang=ang[order],
         **{f"rod_I_{m:+d}": v for m, v in spec_I.items()}, F_in=F_in, F_out=F_out, F_vac=F_vac, F_cry=F_cry,
         rod_flux=np.array([rod_flux[m] for m in range(-3, 4)]))
print("saved figures/fig_exit_wave.{pdf,png}, outputs/exit_wave_analysis.npz")
