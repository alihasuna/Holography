#!/usr/bin/env python3
"""
viewer_v1.py -- Simple Reflection Diffraction Viewer (v1)
=========================================================

Minimal, clean viewer. One panel, sliders, spot overlay.
The original concept before feature creep.

  /opt/anaconda3/bin/python -m simulation.viewer_v1
"""

import argparse, glob
from pathlib import Path
import numpy as np

import matplotlib
for _bk in ["Qt5Agg", "Qt6Agg", "macosx"]:
    try: matplotlib.use(_bk); break
    except: continue
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.colors import PowerNorm

from simulation.constants import K_200KV, SI_LATTICE_PARAM, ANGULAR_SCALE, LAMBDA_200KV
from simulation.supercell import PC_X, PC_Y, PC_Z
from simulation.structure_factors import is_allowed_diamond_cubic, structure_factor


def predict_spots(grazing_mrad, azimuth_mrad, kv=200.0, a=SI_LATTICE_PARAM, max_idx=8):
    lam = 12.2643 / np.sqrt(kv*1e3*(1+0.978476e-6*kv*1e3))
    K = 2*np.pi/lam
    al = grazing_mrad*1e-3; ph = azimuth_mrad*1e-3
    kd = PC_Z - al*PC_Y + ph*PC_X; kd /= np.linalg.norm(kd)
    ki = K*kd; rec = 2*np.pi/a
    spots = []
    for h in range(-max_idx, max_idx+1):
      for k in range(-max_idx, max_idx+1):
        for l in range(-max_idx, max_idx+1):
            if h==k==l==0: continue
            ok, _ = is_allowed_diamond_cubic(h,k,l)
            if not ok: continue
            g = rec*np.array([h,k,l],dtype=float)
            kf = ki+g
            sg = (K**2 - np.dot(kf,kf))/(2*K)
            if abs(sg)>2: continue
            tx = (np.dot(kf,PC_X)-np.dot(ki,PC_X))/K*1e3
            ty = (np.dot(kf,PC_Y)-np.dot(ki,PC_Y))/K*1e3
            try: Fsq = abs(structure_factor(h,k,l))**2
            except: Fsq=1
            spots.append(dict(hkl=(h,k,l), tx=tx, ty=ty, sg=sg, Fsq=Fsq))
    return spots


def generate_synthetic(grazing, azimuth, nx=256, ny=256, sc=ANGULAR_SCALE,
                       kv=200.0, a=SI_LATTICE_PARAM):
    pat = np.zeros((ny,nx)); cx,cy=nx/2,ny/2
    X,Y = np.meshgrid(np.arange(nx,dtype=float),np.arange(ny,dtype=float))
    I0 = 1e5
    pat += I0*np.exp(-((X-cx)**2+(Y-cy)**2)/(2*2.5**2))
    spots = predict_spots(grazing, azimuth, kv=kv, a=a)
    for s in spots:
        px=cx+s["tx"]/sc; py=cy+s["ty"]/sc
        if not(-20<=px<=nx+20 and -20<=py<=ny+20): continue
        xi=80*(20/max(s["Fsq"],1))**0.5
        lor=1/(1+(s["sg"]*xi*10)**2)
        I=s["Fsq"]*lor*I0/500
        if I<1: continue
        pat += I*np.exp(-((X-px)**2+(Y-py)**2)/(2*2.5**2))
    sp=cy+2*grazing/sc
    pat += I0*0.3*np.exp(-((X-cx)**2+(Y-sp)**2)/(2*2.5**2))
    shadow=0.5*(1+np.tanh((Y-cy-2*grazing/sc)/20))
    pat *= (0.3+0.7*shadow)
    pat = np.random.poisson(np.clip(pat+40,0,None)).astype(float)
    return pat


def load_hm(path):
    import h5py
    with h5py.File(path,"r") as f: d=f["micrograph"][:]
    fr = np.sum(d,axis=0).astype(float) if d.ndim==3 else d.astype(float)
    return np.clip(fr, 0, None)


class SimpleViewer:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent
        self.hm = sorted(glob.glob(str(self.data_dir/"*.hm")))
        self.idx = 0; self.frame = None
        self.grazing = 28.0; self.azimuth = 0.0
        self.gamma = 0.3; self.oy = 128; self.ox = 128
        self.scale = ANGULAR_SCALE; self.mode = "sim"

        self.fig, self.ax = plt.subplots(figsize=(10, 10), facecolor="black")
        self.fig.canvas.manager.set_window_title("Reflection Viewer v1")
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.93, bottom=0.30)
        self.ax.set_facecolor("black")

        # sliders
        c = "#e94560"
        self.sl_gr = Slider(self.fig.add_axes([0.15,0.22,0.7,0.02]),
                            "Grazing (mrad)", 1, 80, valinit=28, valstep=0.5,
                            color=c, track_color="#222")
        self.sl_az = Slider(self.fig.add_axes([0.15,0.18,0.7,0.02]),
                            "Azimuth (mrad)", -100, 100, valinit=0, valstep=0.5,
                            color=c, track_color="#222")
        self.sl_oy = Slider(self.fig.add_axes([0.15,0.14,0.7,0.02]),
                            "Origin Y", 0, 255, valinit=128, valstep=1,
                            color=c, track_color="#222")
        self.sl_ox = Slider(self.fig.add_axes([0.15,0.10,0.7,0.02]),
                            "Origin X", 0, 255, valinit=128, valstep=1,
                            color=c, track_color="#222")
        self.sl_sc = Slider(self.fig.add_axes([0.15,0.06,0.7,0.02]),
                            "Scale (mrad/px)", 0.04, 0.3, valinit=ANGULAR_SCALE,
                            valstep=0.002, color=c, track_color="#222")

        for sl in [self.sl_gr, self.sl_az, self.sl_oy, self.sl_ox, self.sl_sc]:
            sl.on_changed(self._update)
            sl.label.set_color("white"); sl.valtext.set_color("white")

        # buttons
        bk = dict(color="#222", hovercolor="#444")
        self.b_mode = Button(self.fig.add_axes([0.15,0.02,0.12,0.03]), "Simulate", **bk)
        self.b_prev = Button(self.fig.add_axes([0.30,0.02,0.08,0.03]), "< Prev", **bk)
        self.b_next = Button(self.fig.add_axes([0.40,0.02,0.08,0.03]), "Next >", **bk)
        self.b_save = Button(self.fig.add_axes([0.50,0.02,0.08,0.03]), "Save", **bk)
        for b in [self.b_mode,self.b_prev,self.b_next,self.b_save]:
            b.label.set_color("white")
        self.b_mode.on_clicked(self._toggle)
        self.b_prev.on_clicked(self._prev)
        self.b_next.on_clicked(self._next)
        self.b_save.on_clicked(self._save)

        if self.hm: self.frame = load_hm(self.hm[0])
        self._update(None)

    def _toggle(self, _):
        self.mode = "exp" if self.mode=="sim" else "sim"
        self.b_mode.label.set_text("Experiment" if self.mode=="sim" else "Simulate")
        self._update(None)

    def _prev(self, _):
        if self.hm:
            self.idx=(self.idx-1)%len(self.hm)
            self.frame=load_hm(self.hm[self.idx]); self._update(None)

    def _next(self, _):
        if self.hm:
            self.idx=(self.idx+1)%len(self.hm)
            self.frame=load_hm(self.hm[self.idx]); self._update(None)

    def _save(self, _):
        od = self.data_dir/"simulation_results"; od.mkdir(exist_ok=True)
        self.fig.savefig(str(od/"viewer_v1.png"), dpi=200, facecolor="black")
        print(f"Saved: {od}/viewer_v1.png")

    def _update(self, _):
        self.grazing = self.sl_gr.val; self.azimuth = self.sl_az.val
        self.oy = self.sl_oy.val; self.ox = self.sl_ox.val
        self.scale = self.sl_sc.val

        ax = self.ax; ax.clear(); ax.set_facecolor("black")

        if self.mode == "exp" and self.frame is not None:
            fr = self.frame
            name = Path(self.hm[self.idx]).stem if self.hm else "no data"
            ax.set_title(f"EXPERIMENT: {name}", fontsize=9, color="white")
            ocx, ocy = self.ox, self.oy
        else:
            fr = generate_synthetic(self.grazing, self.azimuth, sc=self.scale)
            ax.set_title("SIMULATED", fontsize=9, color="#e94560")
            ocx, ocy = 128, 128

        vmax = np.percentile(fr, 99.5)
        ax.imshow(fr, cmap="gray", norm=PowerNorm(gamma=0.3, vmin=0, vmax=max(vmax,1)),
                  origin="upper")
        ax.plot(ocx, ocy, "+", color="cyan", ms=12, mew=1.5)

        spots = predict_spots(self.grazing, self.azimuth)
        for s in spots:
            px = ocx + s["tx"]/self.scale
            py = ocy + s["ty"]/self.scale
            if not(0<=px<=256 and 0<=py<=256): continue
            sz = max(3, min(12, np.sqrt(s["Fsq"])/2.5))
            ax.plot(px, py, "o", mfc="none", mec="red", ms=sz, mew=0.7, alpha=0.8)
            if abs(s["sg"])<0.3 and s["Fsq"]>15:
                h,k,l = s["hkl"]
                ax.annotate(f"{h}{k}{l}", (px,py), xytext=(3,-3),
                            textcoords="offset points", fontsize=4.5, color="red", alpha=0.8)

        ax.set_xlim(-0.5, 255.5); ax.set_ylim(255.5, -0.5)
        ax.tick_params(colors="white", labelsize=6)
        ax.text(0.01, 0.01,
                f"{self.grazing:.0f} mrad | {self.scale:.3f} mrad/px | "
                f"{len([s for s in spots if 0<=ocx+s['tx']/self.scale<=256 and 0<=ocy+s['ty']/self.scale<=256])} spots",
                transform=ax.transAxes, fontsize=7, color="#666", va="bottom")

        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=str, default=None)
    a = p.parse_args()
    dd = a.dir or str(Path(__file__).resolve().parent.parent)
    SimpleViewer(data_dir=dd).show()
