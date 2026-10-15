#!/usr/bin/env python3
"""
viewer_original.py -- Original Interactive Reflection Diffraction Viewer
========================================================================

The very first version. One panel, sliders, red spot overlay.
Uses the original zone-axis frame (ZA_X, ZA_Y, ZA_Z) and
predict_spots_pc from the initial implementation.

Usage:
    /opt/anaconda3/bin/python -m simulation.viewer_original
"""

import argparse
import glob
from pathlib import Path

import numpy as np
import matplotlib
for _bk in ["Qt5Agg", "Qt6Agg", "macosx"]:
    try: matplotlib.use(_bk); break
    except: continue
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.colors import PowerNorm

from simulation.constants import (
    K_200KV, SI_LATTICE_PARAM, ANGULAR_SCALE, DETECTOR_SHAPE,
)
from simulation.supercell import PC_X, PC_Y, PC_Z
from simulation.structure_factors import (
    is_allowed_diamond_cubic, structure_factor,
)
from simulation.calibration import btx_bty_to_tilt_mrad


# ── spot prediction ──────────────────────────────────────────────────────────

def predict_spots_pc(grazing_mrad, azimuth_mrad, max_index=8):
    """Predict Bragg spot positions using the Peng-Cowley frame."""
    lam = 12.2643 / np.sqrt(200e3 * (1 + 0.978476e-6 * 200e3))
    K = 2 * np.pi / lam

    alpha = grazing_mrad * 1e-3
    phi = azimuth_mrad * 1e-3
    k_dir = PC_Z - alpha * PC_Y + phi * PC_X
    k_dir = k_dir / np.linalg.norm(k_dir)
    k_i = K * k_dir

    recip = 2 * np.pi / SI_LATTICE_PARAM
    spots = []

    for h in range(-max_index, max_index + 1):
        for k in range(-max_index, max_index + 1):
            for l in range(-max_index, max_index + 1):
                if h == 0 and k == 0 and l == 0:
                    continue
                allowed, _ = is_allowed_diamond_cubic(h, k, l)
                if not allowed:
                    continue

                g = recip * np.array([h, k, l], dtype=float)
                k_f = k_i + g
                s_g = (K**2 - np.dot(k_f, k_f)) / (2 * K)

                if abs(s_g) > 1.0:
                    continue

                delta_kx = np.dot(k_f, PC_X) - np.dot(k_i, PC_X)
                delta_ky = np.dot(k_f, PC_Y) - np.dot(k_i, PC_Y)
                theta_x = delta_kx / K * 1e3  # mrad
                theta_y = delta_ky / K * 1e3

                try:
                    F = structure_factor(h, k, l)
                    F_sq = abs(F)**2
                except:
                    F_sq = 1.0

                spots.append({
                    "hkl": (h, k, l),
                    "theta_x": theta_x,
                    "theta_y": theta_y,
                    "s_g": s_g,
                    "F_sq": F_sq,
                })

    return spots, k_i


# ── synthetic pattern generator ──────────────────────────────────────────────

def generate_synthetic_pattern(grazing_mrad, azimuth_mrad,
                                nx=256, ny=256,
                                scale=ANGULAR_SCALE,
                                spot_sigma_px=2.5,
                                noise_level=50,
                                direct_beam_intensity=1e5,
                                max_index=8):
    """Generate a synthetic diffraction pattern."""
    pattern = np.zeros((ny, nx), dtype=float)
    cx, cy = nx / 2, ny / 2

    spots, k_i = predict_spots_pc(grazing_mrad, azimuth_mrad, max_index=max_index)

    x = np.arange(nx, dtype=float)
    y = np.arange(ny, dtype=float)
    X, Y = np.meshgrid(x, y)

    # direct beam at center
    pattern += direct_beam_intensity * np.exp(
        -((X - cx)**2 + (Y - cy)**2) / (2 * spot_sigma_px**2))

    xi_avg = 80.0  # nm

    for s in spots:
        px = cx + s["theta_x"] / scale
        py = cy + s["theta_y"] / scale

        if not (-20 <= px <= nx + 20 and -20 <= py <= ny + 20):
            continue

        xi_nm = xi_avg * (20.0 / max(s["F_sq"], 1.0))**0.5
        lorentz = 1.0 / (1.0 + (s["s_g"] * xi_nm * 10)**2)
        intensity = s["F_sq"] * lorentz * direct_beam_intensity / 500.0

        if intensity < 1:
            continue

        pattern += intensity * np.exp(
            -((X - px)**2 + (Y - py)**2) / (2 * spot_sigma_px**2))

    # specular beam
    spec_py = cy + 2 * grazing_mrad / scale
    spec_intensity = direct_beam_intensity * 0.3
    pattern += spec_intensity * np.exp(
        -((X - cx)**2 + (Y - spec_py)**2) / (2 * spot_sigma_px**2))

    # Poisson noise
    if noise_level > 0:
        pattern = np.random.poisson(
            np.clip(pattern + noise_level, 0, None)).astype(float)

    # shadow edge
    shadow = 0.5 * (1 + np.tanh((Y - cy - 2 * grazing_mrad / scale) / 20))
    pattern *= (0.3 + 0.7 * shadow)

    return pattern


# ── data loading ─────────────────────────────────────────────────────────────

def load_hm_frame(path):
    """Load .hm diffraction frame."""
    import h5py
    with h5py.File(path, "r") as f:
        data = f["micrograph"][:]
    if data.ndim == 3:
        frame = np.sum(data, axis=0).astype(np.float64)
    else:
        frame = data.astype(np.float64)
    return np.clip(frame, 0, None)


# ── viewer ───────────────────────────────────────────────────────────────────

class ReflectionViewer:
    def __init__(self, hm_path=None, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent
        self.hm_files = sorted(glob.glob(str(self.data_dir / "*.hm")))

        if hm_path:
            self.current_idx = 0
            for i, f in enumerate(self.hm_files):
                if Path(f).name == Path(hm_path).name:
                    self.current_idx = i
                    break
        else:
            self.current_idx = 0

        # parameters
        self.grazing = 28.0
        self.azimuth = 0.0
        self.gamma_display = 0.3
        self.clip = 99.5
        self.origin_y = 128.0
        self.origin_x = 128.0
        self.scale = ANGULAR_SCALE  # mrad/px
        self.mode = "experiment"  # "experiment" or "simulate"

        self._build_ui()
        self._load_current()
        self._update()

    def _build_ui(self):
        self.fig = plt.figure(figsize=(14, 10))
        self.fig.canvas.manager.set_window_title("Reflection Diffraction Viewer (Original)")

        # main image
        self.ax_img = self.fig.add_axes([0.05, 0.25, 0.55, 0.70])
        self.ax_img.set_title("", fontsize=10)

        # spot info panel
        self.ax_info = self.fig.add_axes([0.65, 0.25, 0.32, 0.70])
        self.ax_info.axis("off")

        # sliders
        ax_gr = self.fig.add_axes([0.15, 0.16, 0.35, 0.03])
        ax_az = self.fig.add_axes([0.15, 0.12, 0.35, 0.03])
        ax_oy = self.fig.add_axes([0.15, 0.08, 0.35, 0.03])
        ax_ox = self.fig.add_axes([0.15, 0.04, 0.35, 0.03])
        ax_sc = self.fig.add_axes([0.65, 0.16, 0.25, 0.03])
        ax_gm = self.fig.add_axes([0.65, 0.12, 0.25, 0.03])

        self.sl_grazing = Slider(ax_gr, "Grazing (mrad)", 1, 80,
                                  valinit=self.grazing, valstep=0.5)
        self.sl_azimuth = Slider(ax_az, "Azimuth (mrad)", -100, 100,
                                  valinit=self.azimuth, valstep=0.5)
        self.sl_oy = Slider(ax_oy, "Origin Y (px)", 0, 255,
                             valinit=self.origin_y, valstep=1)
        self.sl_ox = Slider(ax_ox, "Origin X (px)", 0, 255,
                             valinit=self.origin_x, valstep=1)
        self.sl_scale = Slider(ax_sc, "Scale (mrad/px)", 0.05, 0.3,
                                valinit=self.scale, valstep=0.005)
        self.sl_gamma = Slider(ax_gm, "Display gamma", 0.05, 1.0,
                                valinit=self.gamma_display, valstep=0.05)

        for sl in [self.sl_grazing, self.sl_azimuth, self.sl_oy, self.sl_ox,
                    self.sl_scale, self.sl_gamma]:
            sl.on_changed(self._on_slider)

        # mode toggle + nav buttons
        ax_mode = self.fig.add_axes([0.55, 0.04, 0.08, 0.04])
        ax_prev = self.fig.add_axes([0.65, 0.04, 0.10, 0.04])
        ax_next = self.fig.add_axes([0.76, 0.04, 0.10, 0.04])
        ax_save = self.fig.add_axes([0.87, 0.04, 0.10, 0.04])

        self.btn_mode = Button(ax_mode, "Simulate")
        self.btn_prev = Button(ax_prev, "< Prev")
        self.btn_next = Button(ax_next, "Next >")
        self.btn_save = Button(ax_save, "Save TIFF")

        self.btn_mode.on_clicked(self._toggle_mode)
        self.btn_prev.on_clicked(self._prev)
        self.btn_next.on_clicked(self._next)
        self.btn_save.on_clicked(self._save)

    def _load_current(self):
        if not self.hm_files:
            self.frame = np.zeros(DETECTOR_SHAPE)
            self.current_name = "(no data)"
            return
        path = self.hm_files[self.current_idx]
        self.frame = load_hm_frame(path)
        self.current_name = Path(path).stem

    def _on_slider(self, val):
        self.grazing = self.sl_grazing.val
        self.azimuth = self.sl_azimuth.val
        self.origin_y = self.sl_oy.val
        self.origin_x = self.sl_ox.val
        self.scale = self.sl_scale.val
        self.gamma_display = self.sl_gamma.val
        self._update()

    def _prev(self, event):
        self.current_idx = (self.current_idx - 1) % max(len(self.hm_files), 1)
        self._load_current()
        self._update()

    def _next(self, event):
        self.current_idx = (self.current_idx + 1) % max(len(self.hm_files), 1)
        self._load_current()
        self._update()

    def _toggle_mode(self, event):
        if self.mode == "experiment":
            self.mode = "simulate"
            self.btn_mode.label.set_text("Exper.")
        else:
            self.mode = "experiment"
            self.btn_mode.label.set_text("Simulate")
        self._update()

    def _save(self, event):
        outdir = self.data_dir / "simulation_results"
        outdir.mkdir(exist_ok=True)
        if self.mode == "simulate":
            fname = f"synthetic_g{self.grazing:.0f}_a{self.azimuth:.0f}.tiff"
        else:
            fname = f"overlay_{self.current_name}.tiff"
        outpath = outdir / fname
        self.fig.savefig(str(outpath), dpi=200, format="tiff", bbox_inches="tight")
        print(f"Saved: {outpath}")

    def _update(self):
        ax = self.ax_img
        ax.clear()

        if self.mode == "simulate":
            display_frame = generate_synthetic_pattern(
                self.grazing, self.azimuth,
                nx=256, ny=256, scale=self.scale)
            title_prefix = "SIMULATED"
            ox, oy = 128, 128
        else:
            display_frame = self.frame
            title_prefix = "EXPERIMENT"
            ox, oy = self.origin_x, self.origin_y

        # display pattern
        vmax = np.percentile(display_frame, self.clip)
        ax.imshow(display_frame, cmap="gray",
                  norm=PowerNorm(gamma=self.gamma_display, vmin=0,
                                 vmax=max(vmax, 1)),
                  origin="upper",
                  extent=[0, display_frame.shape[1], display_frame.shape[0], 0])

        # mark origin / direct beam
        ax.plot(ox, oy, "+", color="cyan", markersize=12, markeredgewidth=1.5)

        # predict spots and overlay
        spots, k_i = predict_spots_pc(self.grazing, self.azimuth)

        on_detector = []
        for s in spots:
            px = ox + s["theta_x"] / self.scale
            py = oy + s["theta_y"] / self.scale
            s["px"] = px
            s["py"] = py
            if 0 <= px <= display_frame.shape[1] and 0 <= py <= display_frame.shape[0]:
                on_detector.append(s)

        # draw spots (simple red circles)
        for s in on_detector:
            color = "red" if abs(s["s_g"]) < 0.1 else "orange"
            size = max(4, min(12, s["F_sq"] / 50))
            ax.plot(s["px"], s["py"], "o", markerfacecolor="none",
                    markeredgecolor=color, markersize=size, markeredgewidth=1.0)

            h, k, l = s["hkl"]
            label = f"{h}{k}{l}"
            ax.annotate(label, (s["px"], s["py"]),
                        xytext=(s["px"] + 5, s["py"] - 5),
                        fontsize=5.5, color=color,
                        bbox=dict(boxstyle="round,pad=0.1", fc="black",
                                  alpha=0.4, ec="none"))

        # specular mark in simulate mode
        if self.mode == "simulate":
            spec_py = oy + 2 * self.grazing / self.scale
            ax.plot(ox, spec_py, "x", color="cyan", markersize=10,
                    markeredgewidth=1.5)
            ax.annotate("specular", (ox, spec_py), xytext=(ox + 8, spec_py),
                        fontsize=6, color="cyan")

        ax.set_xlim(-0.5, display_frame.shape[1] - 0.5)
        ax.set_ylim(display_frame.shape[0] - 0.5, -0.5)

        if self.mode == "experiment":
            ax.set_title(f"{title_prefix}: {self.current_name}  "
                         f"[{self.current_idx + 1}/{len(self.hm_files)}]",
                         fontsize=9)
        else:
            ax.set_title(f"{title_prefix}: Si[110] / (1-11) at 200 kV",
                         fontsize=9)

        # info panel
        info_ax = self.ax_info
        info_ax.clear()
        info_ax.axis("off")

        grazing_deg = self.grazing / 1e3 * 180 / np.pi
        info_lines = [
            f"Mode: {self.mode.upper()}",
            f"Grazing: {self.grazing:.1f} mrad ({grazing_deg:.2f} deg)",
            f"Azimuth: {self.azimuth:.1f} mrad",
            f"Origin: ({oy:.0f}, {ox:.0f}) px",
            f"Scale: {self.scale:.3f} mrad/px",
            f"Spots on detector: {len(on_detector)}",
            "",
            "Nearest Bragg condition (|s_g| small):",
        ]

        strong = sorted(on_detector, key=lambda s: abs(s["s_g"]))[:15]
        for s in strong:
            h, k, l = s["hkl"]
            info_lines.append(
                f"  ({h:2d},{k:2d},{l:2d}) s={s['s_g']:+.4f} |F|2={s['F_sq']:6.0f}")

        info_ax.text(0.0, 0.98, "\n".join(info_lines),
                     transform=info_ax.transAxes, fontsize=8,
                     fontfamily="monospace", verticalalignment="top")

        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reflection diffraction viewer (original)")
    parser.add_argument("--file", type=str, default=None,
                        help="Specific .hm file")
    parser.add_argument("--dir", type=str, default=None,
                        help="Data directory")
    args = parser.parse_args()

    data_dir = args.dir or str(Path(__file__).resolve().parent.parent)
    viewer = ReflectionViewer(hm_path=args.file, data_dir=data_dir)
    viewer.show()
