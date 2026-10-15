#!/usr/bin/env python3
"""
viewer.py -- Reflection Electron Diffraction Laboratory
========================================================

Academic-grade interactive simulation and analysis tool for bulk
Bragg reflection electron diffraction from Si[110] / (1-11).

  /opt/anaconda3/bin/python -m simulation.viewer
  /opt/anaconda3/bin/python -m simulation.viewer --cif structure.cif
"""

import argparse, glob
from pathlib import Path
import numpy as np

import matplotlib
for _bk in ["Qt5Agg", "Qt6Agg", "macosx"]:
    try: matplotlib.use(_bk); break
    except Exception: continue
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.colors import PowerNorm
from matplotlib.patches import Arc, Rectangle, FancyArrowPatch
from matplotlib.gridspec import GridSpec

from simulation.constants import (
    K_200KV, SI_LATTICE_PARAM, ANGULAR_SCALE, LAMBDA_200KV,
)
from simulation.supercell import PC_X, PC_Y, PC_Z
from simulation.structure_factors import is_allowed_diamond_cubic, structure_factor

# ── palette ──────────────────────────────────────────────────────────────────
C_BG      = "#0b0b1e"
C_PANEL   = "#101030"
C_SURFACE = "#e94560"
C_BEAM    = "#00e676"
C_SPEC    = "#ff9100"
C_BRAGG_R = "#ff1744"
C_BRAGG_T = "#448aff"
C_HOLZ    = "#7c4dff"
C_TEXT    = "#cfd8dc"
C_DIM     = "#455a64"
C_ACCENT  = "#e94560"
C_GOLD    = "#ffd740"

# ── crystal structure ────────────────────────────────────────────────────────

class Crystal:
    def __init__(self):
        self.name = "Si (built-in)"
        self.a = SI_LATTICE_PARAM
        self.cell = (self.a,)*3 + (90,)*3
        self.source = "built-in"
        self.atoms = []
        self._init_si()

    def _init_si(self):
        a = self.a
        frac = [[0,0,0],[.5,.5,0],[.5,0,.5],[0,.5,.5],
                [.25,.25,.25],[.75,.75,.25],[.75,.25,.75],[.25,.75,.75]]
        self.atoms = [("Si", f[0]*a, f[1]*a, f[2]*a) for f in frac]

    @staticmethod
    def from_file(path):
        try:
            from ase.io import read as ase_read
            at = ase_read(str(path))
            c = Crystal()
            c.name = Path(path).stem
            c.source = str(path)
            cl = at.get_cell()
            c.cell = (*cl.lengths(), *cl.angles())
            c.a = c.cell[0]
            pos = at.get_positions()
            sym = at.get_chemical_symbols()
            c.atoms = [(s, p[0], p[1], p[2]) for s, p in zip(sym, pos)]
            return c
        except Exception as e:
            print(f"Load error: {e}")
            return Crystal()

    def info(self):
        sp = sorted(set(s for s,*_ in self.atoms))
        vol = self.cell[0]*self.cell[1]*self.cell[2]
        return (f"{self.name}\n"
                f"{len(self.atoms)} atoms | {', '.join(sp)}\n"
                f"a={self.cell[0]:.3f} b={self.cell[1]:.3f} c={self.cell[2]:.3f} A\n"
                f"V={vol:.0f} A^3 | rho={len(self.atoms)/vol:.4f} at/A^3")


# ── physics ──────────────────────────────────────────────────────────────────

def compute_wavelength(kv):
    return 12.2643 / np.sqrt(kv*1e3 * (1 + 0.978476e-6 * kv*1e3))

def predict(grazing, azimuth, kv=200.0, a=SI_LATTICE_PARAM, max_idx=8):
    lam = compute_wavelength(kv)
    K = 2*np.pi / lam
    al = grazing*1e-3; ph = azimuth*1e-3
    kd = PC_Z - al*PC_Y + ph*PC_X; kd /= np.linalg.norm(kd)
    ki = K * kd
    rec = 2*np.pi / a
    spots = []
    for h in range(-max_idx, max_idx+1):
      for k in range(-max_idx, max_idx+1):
        for l in range(-max_idx, max_idx+1):
            if h==0 and k==0 and l==0: continue
            ok, _ = is_allowed_diamond_cubic(h, k, l)
            if not ok: continue
            g = rec * np.array([h,k,l], dtype=float)
            kf = ki + g
            sg = (K**2 - np.dot(kf,kf)) / (2*K)
            if abs(sg) > 2.0: continue
            dkx = np.dot(kf,PC_X) - np.dot(ki,PC_X)
            dky = np.dot(kf,PC_Y) - np.dot(ki,PC_Y)
            tx = dkx/K*1e3; ty = dky/K*1e3
            try: Fsq = abs(structure_factor(h,k,l))**2
            except: Fsq = 1.0
            lz = h + k
            stype = "R" if np.dot(kf, PC_Y) > 0 else "T"
            gm = np.linalg.norm(g)
            spots.append(dict(hkl=(h,k,l), tx=tx, ty=ty, sg=sg, Fsq=Fsq,
                              lz=lz, type=stype, gm=gm,
                              d=2*np.pi/gm if gm>0 else np.inf))
    return spots, ki

def synth_pattern(grazing, azimuth, nx=256, ny=256, sc=ANGULAR_SCALE,
                  kv=200.0, a=SI_LATTICE_PARAM, sigma_px=2.5,
                  noise=40, I0=1e5):
    pat = np.zeros((ny, nx))
    cx, cy = nx/2, ny/2
    X, Y = np.meshgrid(np.arange(nx, dtype=float), np.arange(ny, dtype=float))
    pat += I0 * np.exp(-((X-cx)**2+(Y-cy)**2)/(2*sigma_px**2))
    spots, _ = predict(grazing, azimuth, kv=kv, a=a)
    for s in spots:
        px = cx + s["tx"]/sc; py = cy + s["ty"]/sc
        if not (-20<=px<=nx+20 and -20<=py<=ny+20): continue
        xi = 80*(20/max(s["Fsq"],1))**0.5
        lor = 1/(1+(s["sg"]*xi*10)**2)
        I = s["Fsq"]*lor*I0/500
        if I < 1: continue
        pat += I*np.exp(-((X-px)**2+(Y-py)**2)/(2*sigma_px**2))
    sp = cy + 2*grazing/sc
    pat += I0*0.3*np.exp(-((X-cx)**2+(Y-sp)**2)/(2*sigma_px**2))
    shadow = 0.5*(1+np.tanh((Y-cy-2*grazing/sc)/20))
    pat *= (0.3+0.7*shadow)
    if noise > 0:
        pat = np.random.poisson(np.clip(pat+noise, 0, None)).astype(float)
    return pat

def load_hm(path):
    import h5py, json
    with h5py.File(path,"r") as f: d = f["micrograph"][:]
    fr = np.sum(d, axis=0).astype(float) if d.ndim==3 else d.astype(float)
    return np.clip(fr, 0, None)


# ── main application ─────────────────────────────────────────────────────────

class ReflectionLab:
    def __init__(self, crystal=None, data_dir=None):
        self.crystal = crystal or Crystal()
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent
        self.hm = sorted(glob.glob(str(self.data_dir/"*.hm")))
        self.idx = 0
        self.frame = None
        # state
        self.gr = 28.0; self.az = 0.0; self.kv = 200.0
        self.gam = 0.30; self.oy = 128; self.ox = 128; self.sc = ANGULAR_SCALE
        self.mode = "sim"
        self._build()
        if self.hm: self.frame = load_hm(self.hm[0])
        self._draw()

    # ── layout ───────────────────────────────────────────────────────────────

    def _build(self):
        self.fig = plt.figure(figsize=(20, 12), facecolor=C_BG)
        self.fig.canvas.manager.set_window_title("Reflection Diffraction Lab")

        gs = GridSpec(20, 32, figure=self.fig, hspace=0.4, wspace=0.6)

        # A: main diffraction panel
        self.ax_main = self.fig.add_subplot(gs[0:14, 0:14], facecolor="black")
        # B: simulated (clean)
        self.ax_sim  = self.fig.add_subplot(gs[0:7, 14:22], facecolor="black")
        # C: geometry schematic
        self.ax_geo  = self.fig.add_subplot(gs[7:14, 14:22], facecolor=C_PANEL)
        # D: Ewald construction
        self.ax_ew   = self.fig.add_subplot(gs[0:7, 22:32], facecolor=C_PANEL)
        # E: info + spot table
        self.ax_info = self.fig.add_subplot(gs[7:14, 22:32], facecolor=C_PANEL)

        for a in [self.ax_main, self.ax_sim, self.ax_geo, self.ax_ew, self.ax_info]:
            a.tick_params(colors=C_DIM, labelsize=6)

        # sliders
        skw = dict(color=C_ACCENT, track_color="#1a1a3e")
        row = lambda r: self.fig.add_subplot(gs[14+r, 1:10])
        row2 = lambda r: self.fig.add_subplot(gs[14+r, 12:21])

        self.s_gr = Slider(row(0), "Grazing", 1, 80, valinit=self.gr, valstep=0.5, **skw)
        self.s_az = Slider(row(1), "Azimuth", -100, 100, valinit=self.az, valstep=0.5, **skw)
        self.s_oy = Slider(row(2), "Origin Y", 0, 255, valinit=self.oy, valstep=1, **skw)
        self.s_ox = Slider(row(3), "Origin X", 0, 255, valinit=self.ox, valstep=1, **skw)
        self.s_sc = Slider(row2(0), "Scale", 0.04, 0.3, valinit=self.sc, valstep=0.002, **skw)
        self.s_gm = Slider(row2(1), "Gamma", 0.05, 1.0, valinit=self.gam, valstep=0.05, **skw)
        self.s_kv = Slider(row2(2), "kV", 60, 300, valinit=self.kv, valstep=10, **skw)

        for s in [self.s_gr,self.s_az,self.s_oy,self.s_ox,self.s_sc,self.s_gm,self.s_kv]:
            s.on_changed(self._on_sl)
            s.label.set_color(C_TEXT); s.label.set_fontsize(8)
            s.valtext.set_color(C_TEXT); s.valtext.set_fontsize(8)

        # buttons
        bkw = dict(color="#0f3460", hovercolor="#533483")
        self.b_sim  = Button(self.fig.add_subplot(gs[18, 22:25]), "Simulate", **bkw)
        self.b_exp  = Button(self.fig.add_subplot(gs[18, 25:28]), "Experiment", **bkw)
        self.b_prev = Button(self.fig.add_subplot(gs[19, 22:24]), "< Prev", **bkw)
        self.b_next = Button(self.fig.add_subplot(gs[19, 24:26]), "Next >", **bkw)
        self.b_cif  = Button(self.fig.add_subplot(gs[19, 26:28]), "Load CIF", **bkw)
        self.b_save = Button(self.fig.add_subplot(gs[19, 28:30]), "Save", **bkw)
        for b in [self.b_sim,self.b_exp,self.b_prev,self.b_next,self.b_cif,self.b_save]:
            b.label.set_color(C_TEXT); b.label.set_fontsize(8)
        self.b_sim.on_clicked(lambda e: self._set("sim"))
        self.b_exp.on_clicked(lambda e: self._set("exp"))
        self.b_prev.on_clicked(self._prev)
        self.b_next.on_clicked(self._next)
        self.b_cif.on_clicked(self._load_cif)
        self.b_save.on_clicked(self._save)

        # title
        self.fig.text(0.44, 0.97,
            "REFLECTION ELECTRON DIFFRACTION LABORATORY",
            ha="center", fontsize=13, fontweight="bold", color=C_ACCENT,
            fontfamily="monospace")
        self.fig.text(0.44, 0.955,
            f"Si[110] / (1\u03111) | {self.kv:.0f} kV | "
            f"\u03bb = {LAMBDA_200KV:.5f} \u00c5 | K = {K_200KV:.1f} \u00c5\u207b\u00b9",
            ha="center", fontsize=8, color=C_DIM, fontfamily="monospace")

    # ── callbacks ────────────────────────────────────────────────────────────

    def _on_sl(self, _):
        self.gr=self.s_gr.val; self.az=self.s_az.val
        self.oy=self.s_oy.val; self.ox=self.s_ox.val
        self.sc=self.s_sc.val; self.gam=self.s_gm.val; self.kv=self.s_kv.val
        self._draw()

    def _set(self, m):
        self.mode = m; self._draw()

    def _prev(self, _):
        if self.hm:
            self.idx = (self.idx-1)%len(self.hm)
            self.frame = load_hm(self.hm[self.idx]); self._draw()

    def _next(self, _):
        if self.hm:
            self.idx = (self.idx+1)%len(self.hm)
            self.frame = load_hm(self.hm[self.idx]); self._draw()

    def _load_cif(self, _):
        # Use the Qt that matplotlib's backend already loaded; a tkinter
        # filedialog crashes inside the Qt/Cocoa loop on macOS (NSException).
        p = ""
        try:
            from matplotlib.backends.qt_compat import QtWidgets
            p, _f = QtWidgets.QFileDialog.getOpenFileName(
                None, "Open crystal file", str(self.data_dir),
                "Crystal (*.cif *.xyz *.pdb);;All files (*)")
        except Exception:
            try: p = input("CIF/XYZ path: ").strip()
            except Exception: p = ""
        if p: self.crystal = Crystal.from_file(p); self._draw()

    def _save(self, _):
        od = self.data_dir/"simulation_results"; od.mkdir(exist_ok=True)
        op = od/f"lab_g{self.gr:.0f}_a{self.az:.0f}.pdf"
        self.fig.savefig(str(op), dpi=200, facecolor=C_BG, bbox_inches="tight")
        print(f"Saved: {op}")

    # ── drawing ──────────────────────────────────────────────────────────────

    def _draw(self):
        spots, ki = predict(self.gr, self.az, kv=self.kv, a=self.crystal.a)

        # ── A: main panel ────────────────────────────────────────────────────
        ax = self.ax_main; ax.clear(); ax.set_facecolor("black")
        if self.mode == "exp" and self.frame is not None:
            fr = self.frame
            ax.set_title(f"EXPERIMENT: {Path(self.hm[self.idx]).stem}",
                         fontsize=8, color=C_TEXT, loc="left")
        else:
            fr = synth_pattern(self.gr, self.az, sc=self.sc, kv=self.kv,
                               a=self.crystal.a)
            ax.set_title("SIMULATED PATTERN", fontsize=8, color=C_ACCENT, loc="left")
        vmax = np.percentile(fr, 99.5)
        ax.imshow(fr, cmap="gray", norm=PowerNorm(gamma=self.gam, vmin=0,
                  vmax=max(vmax,1)), origin="upper")
        ocx = self.ox if self.mode=="exp" else 128
        ocy = self.oy if self.mode=="exp" else 128
        ax.plot(ocx, ocy, "+", color="cyan", ms=10, mew=1.2, alpha=0.6)

        on = []
        for s in spots:
            px = ocx + s["tx"]/self.sc; py = ocy + s["ty"]/self.sc
            s["px"]=px; s["py"]=py
            if -5<=px<=260 and -5<=py<=260: on.append(s)

        nr = nt = 0
        for s in on:
            is_h = s["lz"]!=0
            if s["type"]=="R":
                col = C_HOLZ if is_h else C_BRAGG_R; mk="o"; nr+=1
            else:
                col = C_HOLZ if is_h else C_BRAGG_T; mk="s"; nt+=1
            sz = max(3, min(13, np.sqrt(s["Fsq"])/2.5))
            ax.plot(s["px"],s["py"], mk, mfc="none", mec=col, ms=sz, mew=0.7, alpha=0.75)
            if abs(s["sg"])<0.3 and s["Fsq"]>15:
                h,k,l = s["hkl"]
                lb = f"{h}{k}{l}" + (f"[{s['lz']}]" if is_h else "")
                ax.annotate(lb, (s["px"],s["py"]), xytext=(3,-3),
                            textcoords="offset points", fontsize=4.2, color=col, alpha=0.85)

        ax.text(0.01,0.01, f"55\u00b5m/px | {self.sc:.3f} mrad/px | "
                f"FOV {256*self.sc:.1f} mrad | R:{nr} T:{nt}",
                transform=ax.transAxes, fontsize=5.5, color=C_DIM, va="bottom")
        ax.set_xlim(-0.5,255.5); ax.set_ylim(255.5,-0.5)
        ax.tick_params(colors=C_DIM, labelsize=5)

        # ── B: clean sim ─────────────────────────────────────────────────────
        ax2 = self.ax_sim; ax2.clear(); ax2.set_facecolor("black")
        s2 = synth_pattern(self.gr, self.az, nx=128, ny=128, sc=self.sc*2,
                           kv=self.kv, a=self.crystal.a, noise=5, sigma_px=1.3)
        ax2.imshow(s2, cmap="inferno",
                   norm=PowerNorm(gamma=0.35, vmin=0, vmax=np.percentile(s2,99.5)),
                   origin="upper")
        ax2.set_title("SIMULATION (clean)", fontsize=7, color=C_GOLD, loc="left")
        ax2.tick_params(labelsize=4, colors=C_DIM)

        # ── C: geometry schematic ────────────────────────────────────────────
        self._draw_geo(on)

        # ── D: Ewald construction ────────────────────────────────────────────
        self._draw_ewald()

        # ── E: info panel ────────────────────────────────────────────────────
        self._draw_info(on, nr, nt)

        self.fig.canvas.draw_idle()

    # ── geometry schematic ───────────────────────────────────────────────────

    def _draw_geo(self, on):
        ax = self.ax_geo; ax.clear(); ax.set_facecolor(C_PANEL)
        ax.set_xlim(-0.5, 8.5); ax.set_ylim(-2.8, 3.5); ax.set_aspect("equal")
        ax.axis("off")

        # crystal
        ax.add_patch(Rectangle((-0.5,-2.8), 9, 2.8, fc="#151535", ec="none"))
        for ix in np.arange(0, 8, 0.7):
            for iy in np.arange(-2.3, 0, 0.5):
                ax.plot(ix, iy, "o", color="#333366", ms=1.5, alpha=0.5)
        ax.plot([-0.5,8.5], [0,0], color=C_SURFACE, lw=2)

        al = max(self.gr*1e-3*10, 0.04)  # exaggerated
        bl = 5.0
        # incident beam
        bx = 4 - bl*np.cos(al); by = bl*np.sin(al)
        ax.annotate("", xy=(4,0), xytext=(bx, by),
                    arrowprops=dict(arrowstyle="-|>", color=C_BEAM, lw=2.2, mutation_scale=13))
        ax.text(bx+0.1, by+0.15, f"$k_i$ ({self.gr:.0f} mrad)", fontsize=6.5,
                color=C_BEAM, fontweight="bold")

        # specular
        sx = 4+bl*0.55*np.cos(al); sy = bl*0.55*np.sin(al)
        ax.annotate("", xy=(sx,sy), xytext=(4,0),
                    arrowprops=dict(arrowstyle="-|>", color=C_SPEC, lw=1.5, mutation_scale=9))
        ax.text(sx+0.1, sy+0.15, "specular", fontsize=5.5, color=C_SPEC)

        # Bragg beams
        strong_r = sorted([s for s in on if s["type"]=="R"], key=lambda s: s["Fsq"], reverse=True)
        for i, s in enumerate(strong_r[:3]):
            ba = al + (i+1)*0.1
            ex = 4+bl*0.45*np.cos(ba); ey = bl*0.45*np.sin(ba)
            h,k,l = s["hkl"]
            ax.annotate("", xy=(ex,ey), xytext=(4,0),
                        arrowprops=dict(arrowstyle="-|>", color=C_BRAGG_R, lw=0.9,
                                        mutation_scale=6, ls="--"))
            ax.text(ex+0.1, ey+0.05, f"({h}{k}{l})", fontsize=4.5, color=C_BRAGG_R)

        # angle arc
        ax.add_patch(Arc((4,0), 2.2, 2.2, angle=0, theta1=0,
                         theta2=np.degrees(al), color=C_GOLD, lw=1))
        ax.text(5.3, 0.12, f"\u03b1", fontsize=7, color=C_GOLD)

        # penetration depth
        dp = 80*np.sin(self.gr*1e-3)*10  # Angstroms
        dv = min(dp/25, 2.0)
        ax.annotate("", xy=(1.2,-dv), xytext=(1.2,0),
                    arrowprops=dict(arrowstyle="<->", color="#64b5f6", lw=0.8))
        ax.text(1.4, -dv/2, f"{dp:.0f} \u00c5", fontsize=5, color="#64b5f6")

        # normal
        ax.annotate("", xy=(7.5,1.6), xytext=(7.5,0),
                    arrowprops=dict(arrowstyle="-|>", color=C_SURFACE, lw=1, mutation_scale=7))
        ax.text(7.7, 0.7, "$\\hat{n}$", fontsize=7, color=C_SURFACE)

        # azimuth
        if abs(self.az) > 1:
            ax.text(4, -0.3, f"azimuth {self.az:+.0f} mrad (\u2299)",
                    fontsize=5, color=C_BRAGG_T, ha="center", style="italic")

        ax.text(4, 2.8, "VACUUM", fontsize=7, color=C_DIM, ha="center", alpha=0.4)
        ax.text(4, -2.3, "CRYSTAL", fontsize=6, color=C_DIM, ha="center", alpha=0.4)
        ax.set_title("GEOMETRY", fontsize=7, color=C_TEXT, loc="left", pad=2)

    # ── Ewald construction ───────────────────────────────────────────────────

    def _draw_ewald(self):
        ax = self.ax_ew; ax.clear(); ax.set_facecolor(C_PANEL)
        ax.set_xlim(-3.5, 5); ax.set_ylim(-3, 4); ax.set_aspect("equal")
        ax.axis("off")

        # reciprocal lattice
        for h in range(-2, 4):
            for k in range(-2, 3):
                x = h*1.1; y = k*0.95
                ok, _ = is_allowed_diamond_cubic(h, -h, k)  # ZOLZ simplified
                c = "#444477" if ok else "#222244"
                ax.plot(x, y, "o", color=c, ms=3 if ok else 1.5, alpha=0.6)

        # Ewald sphere arc
        R = 7; al = self.gr * 1e-3 * 1.5  # slightly exaggerated
        cx = -R*np.cos(al); cy = R*np.sin(al)
        th = np.linspace(-0.25, 0.45, 150)
        ax.plot(cx+R*np.cos(th), cy-R*np.sin(th), color=C_GOLD, lw=1.5, alpha=0.7)

        # k_i vector
        ax.annotate("", xy=(0,0), xytext=(cx*0.4, cy*0.4),
                    arrowprops=dict(arrowstyle="-|>", color=C_BEAM, lw=1.5, mutation_scale=10))
        ax.text(cx*0.4+0.2, cy*0.4+0.2, "$-k_i$", fontsize=7, color=C_BEAM)

        # origin
        ax.plot(0, 0, "o", color="white", ms=5, zorder=5)
        ax.text(0.15, -0.25, "O", fontsize=7, color="white")

        # surface
        ax.plot([-3, 4.5], [0, 0], "--", color=C_SURFACE, lw=0.5, alpha=0.4)
        ax.text(4, 0.15, "surface", fontsize=5, color=C_SURFACE, alpha=0.5)

        # mark excited spots
        for h in range(-2, 4):
            for k in range(-2, 3):
                x = h*1.1; y = k*0.95
                d = np.sqrt((x-cx)**2+(y-cy)**2) - R
                if abs(d) < 0.35:
                    ax.plot(x, y, "o", mfc="none", mec=C_BRAGG_R, ms=8, mew=1.5)

        ax.set_title("EWALD SPHERE", fontsize=7, color=C_TEXT, loc="left", pad=2)

    # ── info panel ───────────────────────────────────────────────────────────

    def _draw_info(self, on, nr, nt):
        ax = self.ax_info; ax.clear(); ax.axis("off"); ax.set_facecolor(C_PANEL)

        gdeg = self.gr/1e3*180/np.pi
        lam = compute_wavelength(self.kv)
        K = 2*np.pi/lam

        # left column: parameters
        left = (
            f"{self.crystal.info()}\n"
            f"\n"
            f"\u2500\u2500 Beam \u2500\u2500\n"
            f"{self.kv:.0f} kV | \u03bb={lam:.5f} \u00c5\n"
            f"K={K:.1f} \u00c5\u207b\u00b9\n"
            f"\n"
            f"\u2500\u2500 Geometry \u2500\u2500\n"
            f"Grazing: {self.gr:.1f} mrad ({gdeg:.2f}\u00b0)\n"
            f"Azimuth: {self.az:.1f} mrad\n"
            f"d_perp: {80*np.sin(self.gr*1e-3)*10:.0f} \u00c5\n"
            f"\n"
            f"\u2500\u2500 Detector \u2500\u2500\n"
            f"55 \u00b5m | {self.sc:.3f} mrad/px\n"
            f"FOV: {256*self.sc:.1f}\u00d7{256*self.sc:.1f} mrad\n"
            f"\n"
            f"\u2500\u2500 Spots: {len(on)} \u2500\u2500\n"
            f"Refl: {nr} | Trans: {nt}\n"
            f"Mode: {self.mode.upper()}"
        )
        ax.text(0.02, 0.98, left, transform=ax.transAxes, fontsize=6,
                fontfamily="monospace", color=C_TEXT, va="top")

        # right column: spot table
        strong = sorted(on, key=lambda s: abs(s["sg"]))[:10]
        if strong:
            table = "Nearest Bragg:\n" + "\u2500"*28 + "\n"
            table += f"{'hkl':>9s} {'sg':>7s} {'|F|2':>6s} {'type':>3s}\n"
            for s in strong:
                h,k,l = s["hkl"]
                table += f"({h:2d},{k:2d},{l:2d}) {s['sg']:+.4f} {s['Fsq']:6.0f}  {s['type']}\n"
            ax.text(0.55, 0.98, table, transform=ax.transAxes, fontsize=5.5,
                    fontfamily="monospace", color=C_GOLD, va="top")

        ax.set_title("PARAMETERS", fontsize=7, color=C_TEXT, loc="left", pad=2)

    def show(self):
        plt.show()


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--cif", type=str, default=None)
    p.add_argument("--xyz", type=str, default=None)
    p.add_argument("--dir", type=str, default=None)
    a = p.parse_args()
    cry = Crystal.from_file(a.cif or a.xyz) if (a.cif or a.xyz) else Crystal()
    dd = a.dir or str(Path(__file__).resolve().parent.parent)
    ReflectionLab(crystal=cry, data_dir=dd).show()
