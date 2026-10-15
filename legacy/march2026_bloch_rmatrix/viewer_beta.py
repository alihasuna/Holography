#!/usr/bin/env python3
"""
viewer.py -- Interactive Reflection Electron Diffraction Simulator
==================================================================

Professional UI for:
  - Simulating diffraction patterns from any crystal structure (CIF/XYZ)
  - Overlaying kinematical predictions on experimental .hm data
  - Interactive control of grazing angle, azimuth, beam energy
  - 3D crystal structure preview
  - Side-by-side experiment vs simulation comparison

Usage:
    python -m simulation.viewer                         # Si[110] default
    python -m simulation.viewer --cif mycrystal.cif     # load custom structure
    python -m simulation.viewer --xyz atoms.xyz         # load XYZ file
"""

import argparse
import glob
from pathlib import Path

import numpy as np
import matplotlib
# pick a working backend: Qt5 > Qt6 > macosx > Agg
for _backend in ["Qt5Agg", "Qt6Agg", "macosx"]:
    try:
        matplotlib.use(_backend)
        break
    except Exception:
        continue
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, TextBox
from matplotlib.colors import PowerNorm
from mpl_toolkits.mplot3d import Axes3D

from simulation.constants import (
    K_200KV, SI_LATTICE_PARAM, ANGULAR_SCALE, DETECTOR_SHAPE, LAMBDA_200KV,
)
from simulation.supercell import PC_X, PC_Y, PC_Z
from simulation.structure_factors import (
    is_allowed_diamond_cubic, structure_factor, electron_scattering_factor,
)

# ── crystal structure loading ────────────────────────────────────────────────

class CrystalStructure:
    """Holds crystal structure data from CIF, XYZ, or built-in Si."""

    def __init__(self):
        self.name = ""
        self.atoms = []         # list of (symbol, x, y, z) in Angstroms
        self.cell = None        # (a, b, c, alpha, beta, gamma) or None
        self.space_group = "P1"
        self.lattice_param = SI_LATTICE_PARAM
        self.source = ""

    @staticmethod
    def from_si_default():
        """Built-in Si[110] diamond cubic."""
        cs = CrystalStructure()
        cs.name = "Si diamond cubic (built-in)"
        cs.lattice_param = SI_LATTICE_PARAM
        a = SI_LATTICE_PARAM
        cs.cell = (a, a, a, 90, 90, 90)
        cs.space_group = "Fd-3m"
        cs.source = "built-in"
        # 8 atoms in conventional cell
        frac = [
            [0.00, 0.00, 0.00], [0.50, 0.50, 0.00],
            [0.50, 0.00, 0.50], [0.00, 0.50, 0.50],
            [0.25, 0.25, 0.25], [0.75, 0.75, 0.25],
            [0.75, 0.25, 0.75], [0.25, 0.75, 0.75],
        ]
        cs.atoms = [("Si", f[0]*a, f[1]*a, f[2]*a) for f in frac]
        return cs

    @staticmethod
    def from_cif(path):
        """Load crystal structure from CIF using ASE."""
        try:
            from ase.io import read as ase_read
            atoms = ase_read(str(path))
        except Exception as e:
            print(f"Error loading CIF: {e}")
            print("Falling back to built-in Si")
            return CrystalStructure.from_si_default()

        cs = CrystalStructure()
        cs.name = Path(path).stem
        cs.source = str(path)
        cell = atoms.get_cell()
        cs.cell = (*cell.lengths(), *cell.angles())
        cs.lattice_param = cs.cell[0]
        cs.space_group = "P1"

        positions = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()
        cs.atoms = [(s, p[0], p[1], p[2]) for s, p in zip(symbols, positions)]

        print(f"Loaded CIF: {cs.name}")
        print(f"  Cell: {cs.cell[0]:.3f} {cs.cell[1]:.3f} {cs.cell[2]:.3f} A")
        print(f"  Angles: {cs.cell[3]:.1f} {cs.cell[4]:.1f} {cs.cell[5]:.1f}")
        print(f"  Atoms: {len(cs.atoms)}")
        print(f"  Species: {set(symbols)}")
        return cs

    @staticmethod
    def from_xyz(path):
        """Load structure from XYZ file."""
        try:
            from ase.io import read as ase_read
            atoms = ase_read(str(path))
        except Exception as e:
            print(f"Error loading XYZ: {e}")
            return CrystalStructure.from_si_default()

        cs = CrystalStructure()
        cs.name = Path(path).stem
        cs.source = str(path)

        if atoms.get_cell().any():
            cell = atoms.get_cell()
            cs.cell = (*cell.lengths(), *cell.angles())
        else:
            pos = atoms.get_positions()
            span = pos.max(axis=0) - pos.min(axis=0) + 2.0
            cs.cell = (span[0], span[1], span[2], 90, 90, 90)

        cs.lattice_param = cs.cell[0]
        positions = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()
        cs.atoms = [(s, p[0], p[1], p[2]) for s, p in zip(symbols, positions)]

        print(f"Loaded XYZ: {cs.name}, {len(cs.atoms)} atoms")
        return cs

    def get_positions_array(self):
        """Return (N, 3) array of positions in Angstroms."""
        return np.array([[a[1], a[2], a[3]] for a in self.atoms])

    def get_symbols(self):
        return [a[0] for a in self.atoms]

    def summary(self):
        species = set(self.get_symbols())
        lines = [
            f"Structure: {self.name}",
            f"Source: {self.source}",
            f"Atoms: {len(self.atoms)}",
            f"Species: {', '.join(sorted(species))}",
        ]
        if self.cell:
            lines.append(f"Cell: {self.cell[0]:.3f} {self.cell[1]:.3f} {self.cell[2]:.3f} A")
            lines.append(f"Angles: {self.cell[3]:.1f} {self.cell[4]:.1f} {self.cell[5]:.1f} deg")
            vol = self.cell[0] * self.cell[1] * self.cell[2]
            lines.append(f"Volume: {vol:.1f} A^3")
            lines.append(f"Density: {len(self.atoms)/vol:.4f} atoms/A^3")
        return "\n".join(lines)


# ── kinematical spot prediction ──────────────────────────────────────────────

def predict_spots(grazing_mrad, azimuth_mrad, voltage_kv=200.0,
                  lattice_param=SI_LATTICE_PARAM, max_index=8,
                  use_diamond_rules=True):
    """Predict Bragg spot positions in reflection geometry.

    Returns list of spot dicts and the incident wavevector.
    """
    lam = 12.2643 / np.sqrt(voltage_kv * 1e3 * (1 + 0.978476e-6 * voltage_kv * 1e3))
    K = 2 * np.pi / lam

    alpha = grazing_mrad * 1e-3
    phi = azimuth_mrad * 1e-3
    k_dir = PC_Z - alpha * PC_Y + phi * PC_X
    k_dir /= np.linalg.norm(k_dir)
    k_i = K * k_dir

    recip = 2 * np.pi / lattice_param
    spots = []

    for h in range(-max_index, max_index + 1):
        for k in range(-max_index, max_index + 1):
            for l_idx in range(-max_index, max_index + 1):
                if h == 0 and k == 0 and l_idx == 0:
                    continue

                if use_diamond_rules:
                    allowed, _ = is_allowed_diamond_cubic(h, k, l_idx)
                    if not allowed:
                        continue

                g = recip * np.array([h, k, l_idx], dtype=float)
                k_f = k_i + g
                s_g = (K**2 - np.dot(k_f, k_f)) / (2 * K)

                if abs(s_g) > 2.0:
                    continue

                delta_kx = np.dot(k_f, PC_X) - np.dot(k_i, PC_X)
                delta_ky = np.dot(k_f, PC_Y) - np.dot(k_i, PC_Y)
                theta_x = delta_kx / K * 1e3
                theta_y = delta_ky / K * 1e3

                try:
                    F = structure_factor(h, k, l_idx)
                    F_sq = abs(F)**2
                except:
                    F_sq = 1.0

                # classify spot type
                # Laue zone: N = h*u + k*v + l*w for zone axis [uvw]=[110]
                laue_zone = h + k  # h*1 + k*1 + l*0

                # reflection vs transmission:
                # k_f . surface_normal > 0 means reflected (exits toward vacuum)
                k_f_dot_n = np.dot(k_f, PC_Y)  # PC_Y = surface outward normal
                if k_f_dot_n > 0:
                    spot_type = "reflection"
                else:
                    spot_type = "transmission"

                # d-spacing
                g_mag = np.linalg.norm(g)
                d_spacing = 2 * np.pi / g_mag if g_mag > 0 else np.inf

                spots.append({
                    "hkl": (h, k, l_idx),
                    "theta_x": theta_x,
                    "theta_y": theta_y,
                    "s_g": s_g,
                    "F_sq": F_sq,
                    "g_mag": g_mag,
                    "d_spacing": d_spacing,
                    "laue_zone": laue_zone,
                    "type": spot_type,
                })

    return spots, k_i


# ── synthetic pattern generator ──────────────────────────────────────────────

def generate_synthetic(grazing_mrad, azimuth_mrad, nx=256, ny=256,
                       scale=ANGULAR_SCALE, voltage_kv=200.0,
                       spot_sigma=2.5, noise=50, direct_beam_I=1e5,
                       lattice_param=SI_LATTICE_PARAM):
    """Generate a synthetic detector image with Bragg spots."""
    pattern = np.zeros((ny, nx), dtype=float)
    cx, cy = nx / 2, ny / 2
    x = np.arange(nx, dtype=float)
    y = np.arange(ny, dtype=float)
    X, Y = np.meshgrid(x, y)

    # direct beam
    pattern += direct_beam_I * np.exp(-((X-cx)**2+(Y-cy)**2) / (2*spot_sigma**2))

    spots, k_i = predict_spots(grazing_mrad, azimuth_mrad,
                                voltage_kv=voltage_kv,
                                lattice_param=lattice_param)

    for s in spots:
        px = cx + s["theta_x"] / scale
        py = cy + s["theta_y"] / scale
        if not (-20 <= px <= nx+20 and -20 <= py <= ny+20):
            continue
        xi = 80.0 * (20.0 / max(s["F_sq"], 1.0))**0.5
        lorentz = 1.0 / (1.0 + (s["s_g"] * xi * 10)**2)
        intensity = s["F_sq"] * lorentz * direct_beam_I / 500.0
        if intensity < 1:
            continue
        pattern += intensity * np.exp(-((X-px)**2+(Y-py)**2) / (2*spot_sigma**2))

    # specular
    spec_py = cy + 2 * grazing_mrad / scale
    pattern += direct_beam_I * 0.3 * np.exp(
        -((X-cx)**2+(Y-spec_py)**2) / (2*spot_sigma**2))

    # shadow edge
    shadow = 0.5 * (1 + np.tanh((Y - cy - 2*grazing_mrad/scale) / 20))
    pattern *= (0.3 + 0.7 * shadow)

    # noise
    if noise > 0:
        pattern = np.random.poisson(np.clip(pattern + noise, 0, None)).astype(float)

    return pattern


# ── data loading ─────────────────────────────────────────────────────────────

def load_hm(path):
    """Load .hm diffraction frame."""
    import h5py, json
    with h5py.File(path, "r") as f:
        data = f["micrograph"][:]
    frame = np.sum(data, axis=0).astype(np.float64) if data.ndim == 3 else data.astype(np.float64)
    return np.clip(frame, 0, None)


# ── main viewer class ────────────────────────────────────────────────────────

class DiffractionLab:
    """Professional reflection diffraction simulation and analysis tool."""

    def __init__(self, crystal=None, data_dir=None):
        self.crystal = crystal or CrystalStructure.from_si_default()
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent
        self.hm_files = sorted(glob.glob(str(self.data_dir / "*.hm")))
        self.current_idx = 0
        self.frame = None

        # state
        self.grazing = 28.0
        self.azimuth = 0.0
        self.voltage = 200.0
        self.gamma_disp = 0.3
        self.origin_y = 128.0
        self.origin_x = 128.0
        self.scale = ANGULAR_SCALE
        self.mode = "simulate"  # "simulate", "experiment", "compare"

        self._build()
        if self.hm_files:
            self.frame = load_hm(self.hm_files[0])
        self._refresh()

    def _build(self):
        self.fig = plt.figure(figsize=(18, 11), facecolor="#1a1a2e")
        self.fig.canvas.manager.set_window_title(
            "Reflection Diffraction Lab -- Si[110] / (1-11)")

        # color scheme
        text_c = "#e0e0e0"
        bg_c = "#1a1a2e"
        panel_c = "#16213e"
        accent = "#e94560"

        # === LEFT: diffraction pattern ===
        self.ax_diff = self.fig.add_axes([0.03, 0.28, 0.42, 0.65],
                                          facecolor="black")
        self.ax_diff.tick_params(colors=text_c, labelsize=7)

        # === CENTER: simulated pattern ===
        self.ax_sim = self.fig.add_axes([0.48, 0.28, 0.22, 0.65],
                                         facecolor="black")
        self.ax_sim.tick_params(colors=text_c, labelsize=7)

        # === RIGHT TOP: live geometry schematic ===
        self.ax_geom = self.fig.add_axes([0.72, 0.55, 0.26, 0.38],
                                          facecolor="#0a0a1a")
        # === RIGHT BOTTOM: info panel ===
        self.ax_info = self.fig.add_axes([0.72, 0.28, 0.26, 0.25],
                                          facecolor=panel_c)
        self.ax_info.axis("off")

        # === SLIDERS (bottom) ===
        slider_kw = dict(color=accent, track_color="#333355")

        y0 = 0.19
        dy = 0.035
        self.sl_grazing = Slider(
            self.fig.add_axes([0.12, y0, 0.25, 0.02]),
            "Grazing", 1, 80, valinit=self.grazing, valstep=0.5, **slider_kw)
        self.sl_azimuth = Slider(
            self.fig.add_axes([0.12, y0-dy, 0.25, 0.02]),
            "Azimuth", -100, 100, valinit=self.azimuth, valstep=0.5, **slider_kw)
        self.sl_oy = Slider(
            self.fig.add_axes([0.12, y0-2*dy, 0.25, 0.02]),
            "Origin Y", 0, 255, valinit=self.origin_y, valstep=1, **slider_kw)
        self.sl_ox = Slider(
            self.fig.add_axes([0.12, y0-3*dy, 0.25, 0.02]),
            "Origin X", 0, 255, valinit=self.origin_x, valstep=1, **slider_kw)
        self.sl_scale = Slider(
            self.fig.add_axes([0.55, y0, 0.20, 0.02]),
            "Scale", 0.05, 0.3, valinit=self.scale, valstep=0.005, **slider_kw)
        self.sl_gamma = Slider(
            self.fig.add_axes([0.55, y0-dy, 0.20, 0.02]),
            "Gamma", 0.05, 1.0, valinit=self.gamma_disp, valstep=0.05, **slider_kw)
        self.sl_voltage = Slider(
            self.fig.add_axes([0.55, y0-2*dy, 0.20, 0.02]),
            "kV", 60, 300, valinit=self.voltage, valstep=10, **slider_kw)

        for sl in [self.sl_grazing, self.sl_azimuth, self.sl_oy, self.sl_ox,
                    self.sl_scale, self.sl_gamma, self.sl_voltage]:
            sl.on_changed(self._on_slider)
            sl.label.set_color(text_c)
            sl.valtext.set_color(text_c)

        # === BUTTONS ===
        btn_kw = dict(color="#0f3460", hovercolor="#533483")
        bw, bh = 0.07, 0.035
        bx = 0.82

        self.btn_sim = Button(
            self.fig.add_axes([bx, 0.04, bw, bh]), "Simulate", **btn_kw)
        self.btn_exp = Button(
            self.fig.add_axes([bx+bw+0.01, 0.04, bw, bh]), "Exper.", **btn_kw)
        self.btn_prev = Button(
            self.fig.add_axes([0.03, 0.04, 0.05, bh]), "< Prev", **btn_kw)
        self.btn_next = Button(
            self.fig.add_axes([0.09, 0.04, 0.05, bh]), "Next >", **btn_kw)
        self.btn_load = Button(
            self.fig.add_axes([0.16, 0.04, 0.08, bh]), "Load CIF", **btn_kw)
        self.btn_save = Button(
            self.fig.add_axes([0.25, 0.04, 0.08, bh]), "Save TIFF", **btn_kw)

        for btn in [self.btn_sim, self.btn_exp, self.btn_prev, self.btn_next,
                     self.btn_load, self.btn_save]:
            btn.label.set_color(text_c)
            btn.label.set_fontsize(9)

        self.btn_sim.on_clicked(lambda e: self._set_mode("simulate"))
        self.btn_exp.on_clicked(lambda e: self._set_mode("experiment"))
        self.btn_prev.on_clicked(self._prev)
        self.btn_next.on_clicked(self._next)
        self.btn_load.on_clicked(self._load_file)
        self.btn_save.on_clicked(self._save)

        # title
        self.fig.text(0.5, 0.96, "Reflection Electron Diffraction Lab",
                      ha="center", fontsize=14, fontweight="bold", color=accent)
        self.fig.text(0.5, 0.935, "Si[110] / (1-11) surface | 200 kV | Peng-Cowley geometry",
                      ha="center", fontsize=9, color="#8899aa")

    def _on_slider(self, val):
        self.grazing = self.sl_grazing.val
        self.azimuth = self.sl_azimuth.val
        self.origin_y = self.sl_oy.val
        self.origin_x = self.sl_ox.val
        self.scale = self.sl_scale.val
        self.gamma_disp = self.sl_gamma.val
        self.voltage = self.sl_voltage.val
        self._refresh()

    def _set_mode(self, mode):
        self.mode = mode
        self._refresh()

    def _prev(self, event):
        if self.hm_files:
            self.current_idx = (self.current_idx - 1) % len(self.hm_files)
            self.frame = load_hm(self.hm_files[self.current_idx])
            self._refresh()

    def _next(self, event):
        if self.hm_files:
            self.current_idx = (self.current_idx + 1) % len(self.hm_files)
            self.frame = load_hm(self.hm_files[self.current_idx])
            self._refresh()

    def _load_file(self, event):
        """Load CIF or XYZ file via file dialog or path input."""
        try:
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                filetypes=[("Crystal files", "*.cif *.xyz *.pdb"),
                           ("All files", "*.*")])
        except:
            # no tkinter -- ask in terminal
            path = input("Enter CIF/XYZ file path: ").strip()

        if not path:
            return

        p = Path(path)
        if p.suffix.lower() == ".cif":
            self.crystal = CrystalStructure.from_cif(path)
        elif p.suffix.lower() in (".xyz", ".pdb"):
            self.crystal = CrystalStructure.from_xyz(path)
        else:
            print(f"Unknown format: {p.suffix}. Trying CIF parser...")
            self.crystal = CrystalStructure.from_cif(path)

        self._refresh()

    def _save(self, event):
        outdir = self.data_dir / "simulation_results"
        outdir.mkdir(exist_ok=True)
        fname = f"difflab_g{self.grazing:.0f}_a{self.azimuth:.0f}_{self.crystal.name}.tiff"
        outpath = outdir / fname
        self.fig.savefig(str(outpath), dpi=200, format="tiff",
                         facecolor=self.fig.get_facecolor(), bbox_inches="tight")
        print(f"Saved: {outpath}")

    def _draw_geometry(self, grazing_mrad, azimuth_mrad, on_det, text_c):
        """Draw live geometry schematic that updates with sliders."""
        from matplotlib.patches import Arc, Rectangle, FancyArrowPatch

        ax = self.ax_geom
        ax.clear()
        ax.set_facecolor("#0a0a1a")
        ax.set_xlim(-1, 9)
        ax.set_ylim(-3, 4)
        ax.set_aspect("equal")
        ax.axis("off")

        alpha_rad = grazing_mrad * 1e-3
        alpha_vis = max(alpha_rad * 8, 0.05)  # exaggerated for visibility

        # crystal body
        ax.add_patch(Rectangle((-1, -3), 10, 3,
                     facecolor="#1a1a3a", edgecolor="none"))
        # lattice dots
        for ix in np.arange(-0.5, 8.5, 0.9):
            for iy in np.arange(-2.5, 0, 0.65):
                ax.plot(ix, iy, "o", color="#4444aa", markersize=1.8, alpha=0.4)

        # surface
        ax.plot([-1, 9], [0, 0], "-", color="#e94560", linewidth=2)

        # incident beam
        bl = 5.5
        bx0 = 4.0 - bl * np.cos(alpha_vis)
        by0 = bl * np.sin(alpha_vis)
        ax.annotate("", xy=(4.0, 0), xytext=(bx0, by0),
                    arrowprops=dict(arrowstyle="-|>", color="#44ff44",
                                    lw=2.5, mutation_scale=14))
        ax.text(bx0 + 0.2, by0 + 0.15,
                f"$k_i$ ({grazing_mrad:.0f} mrad)",
                fontsize=7, color="#44ff44", fontweight="bold")

        # specular
        sx = 4.0 + bl * 0.6 * np.cos(alpha_vis)
        sy = bl * 0.6 * np.sin(alpha_vis)
        ax.annotate("", xy=(sx, sy), xytext=(4.0, 0),
                    arrowprops=dict(arrowstyle="-|>", color="#ff8844",
                                    lw=1.8, mutation_scale=10))
        ax.text(sx - 0.3, sy + 0.25, "specular", fontsize=6, color="#ff8844")

        # strongest Bragg reflections from the prediction
        bragg_drawn = 0
        strong = sorted(on_det, key=lambda s: s["F_sq"], reverse=True)
        for s in strong:
            if s.get("type") != "reflection" or bragg_drawn >= 3:
                continue
            # draw at progressively larger angles
            bragg_vis = alpha_vis + (bragg_drawn + 1) * 0.12
            bx = 4.0 + bl * 0.5 * np.cos(bragg_vis)
            by = bl * 0.5 * np.sin(bragg_vis)
            h, k, l = s["hkl"]
            ax.annotate("", xy=(bx, by), xytext=(4.0, 0),
                        arrowprops=dict(arrowstyle="-|>", color="#ff4444",
                                        lw=1, mutation_scale=7,
                                        linestyle="--"))
            ax.text(bx + 0.1, by + 0.1, f"({h}{k}{l})",
                    fontsize=5, color="#ff4444")
            bragg_drawn += 1

        # grazing angle arc (exaggerated)
        arc = Arc((4.0, 0), 2.5, 2.5, angle=0, theta1=0,
                  theta2=np.degrees(alpha_vis),
                  color="#ffcc00", linewidth=1.2)
        ax.add_patch(arc)
        ax.text(5.5, 0.15, f"$\\alpha$={grazing_mrad:.0f} mrad",
                fontsize=6, color="#ffcc00")

        # penetration depth
        xi = 80.0  # nm extinction distance
        d_perp = xi * np.sin(alpha_rad) * 10  # in A, capped for display
        d_vis = min(d_perp / 20, 2.0)  # scale for diagram
        ax.annotate("", xy=(1.5, -d_vis), xytext=(1.5, 0),
                    arrowprops=dict(arrowstyle="<->", color="#88ccff", lw=1))
        ax.text(1.7, -d_vis/2,
                f"$d_\\perp$={d_perp:.0f} A",
                fontsize=6, color="#88ccff")

        # surface normal
        ax.annotate("", xy=(7.5, 1.8), xytext=(7.5, 0),
                    arrowprops=dict(arrowstyle="-|>", color="#e94560",
                                    lw=1.2, mutation_scale=8))
        ax.text(7.7, 0.9, "$\\hat{n}$", fontsize=8, color="#e94560")

        # azimuth indicator
        if abs(azimuth_mrad) > 1:
            ax.text(4.0, -0.5,
                    f"azimuth: {azimuth_mrad:+.0f} mrad (into page)",
                    fontsize=6, color="#4488ff", ha="center", style="italic")

        # labels
        ax.text(4.0, 3.2, "VACUUM", fontsize=8, color="#555577",
                ha="center", alpha=0.5)
        ax.text(4.0, -2.5, f"Si CRYSTAL ({self.crystal.name})",
                fontsize=7, color="#555577", ha="center", alpha=0.5)
        ax.text(4.0, -0.25, f"surface $(1\\bar{{1}}1)$ | beam $[110]$",
                fontsize=5, color="#888888", ha="center")

        # counts
        n_r = sum(1 for s in on_det if s.get("type") == "reflection")
        ax.text(0, 3.2,
                f"{n_r} refl. spots\n{len(on_det)} total",
                fontsize=6, color=text_c, alpha=0.7)

        ax.set_title("Live Geometry", fontsize=9, color=text_c, pad=2)

    def _refresh(self):
        text_c = "#e0e0e0"
        spots, k_i = predict_spots(
            self.grazing, self.azimuth, voltage_kv=self.voltage,
            lattice_param=self.crystal.lattice_param)

        # === LEFT panel: experiment or simulation with overlay ===
        ax = self.ax_diff
        ax.clear()
        ax.set_facecolor("black")

        if self.mode == "experiment" and self.frame is not None:
            vmax = np.percentile(self.frame, 99.5)
            ax.imshow(self.frame, cmap="gray",
                      norm=PowerNorm(gamma=self.gamma_disp, vmin=0, vmax=max(vmax,1)),
                      origin="upper")
            ox, oy = self.origin_x, self.origin_y
            ax.set_title(f"EXPERIMENT: {Path(self.hm_files[self.current_idx]).stem}" if self.hm_files else "No data",
                         fontsize=9, color=text_c)
        else:
            synth = generate_synthetic(
                self.grazing, self.azimuth, scale=self.scale,
                voltage_kv=self.voltage,
                lattice_param=self.crystal.lattice_param)
            vmax = np.percentile(synth, 99.5)
            ax.imshow(synth, cmap="gray",
                      norm=PowerNorm(gamma=self.gamma_disp, vmin=0, vmax=max(vmax,1)),
                      origin="upper")
            ox, oy = 128, 128
            ax.set_title("SIMULATED DIFFRACTION PATTERN",
                         fontsize=9, color="#e94560")

        # origin cross
        ax.plot(ox, oy, "+", color="cyan", markersize=14, markeredgewidth=1.5, alpha=0.7)

        # overlay predicted spots
        on_det = []
        for s in spots:
            px = ox + s["theta_x"] / self.scale
            py = oy + s["theta_y"] / self.scale
            s["px"], s["py"] = px, py
            if 0 <= px <= 256 and 0 <= py <= 256:
                on_det.append(s)

        # spot colors by type:
        #   RED circle   = reflection, ZOLZ
        #   ORANGE circle = reflection, HOLZ
        #   BLUE square  = transmission, ZOLZ
        #   CYAN square  = transmission, HOLZ
        n_refl, n_trans = 0, 0
        for s in on_det:
            is_holz = s.get("laue_zone", 0) != 0
            is_refl = s.get("type", "transmission") == "reflection"
            if is_refl:
                color = "#ff8800" if is_holz else "#ff4444"
                marker = "o"
                n_refl += 1
            else:
                color = "#44ccff" if is_holz else "#4488ff"
                marker = "s"
                n_trans += 1
            sz = max(3, min(14, np.sqrt(s["F_sq"]) / 2))
            ax.plot(s["px"], s["py"], marker, markerfacecolor="none",
                    markeredgecolor=color, markersize=sz, markeredgewidth=0.8, alpha=0.8)
            h, k, l = s["hkl"]
            if abs(s["s_g"]) < 0.5 and s["F_sq"] > 10:
                lz = s.get("laue_zone", 0)
                lbl = f"{h}{k}{l}" if lz == 0 else f"{h}{k}{l}[L{lz}]"
                ax.annotate(lbl, (s["px"], s["py"]),
                            xytext=(4, -4), textcoords="offset points",
                            fontsize=4.5, color=color, alpha=0.9)

        # pixel size annotation
        px_um = 55.0  # Merlin pixel pitch
        fov_mrad = 256 * self.scale
        fov_inv_A = fov_mrad * 1e-3 * K_200KV / (2*np.pi)  # approximate
        ax.text(0.98, 0.02,
                f"{px_um:.0f} um/px | {self.scale:.3f} mrad/px | FOV {fov_mrad:.1f} mrad",
                transform=ax.transAxes, fontsize=6, color="#888888",
                ha="right", va="bottom")

        # legend
        ax.text(0.02, 0.02,
                f"R:{n_refl} T:{n_trans}",
                transform=ax.transAxes, fontsize=7, color="#aaaaaa",
                ha="left", va="bottom",
                bbox=dict(fc="black", alpha=0.5, ec="none", pad=2))

        ax.set_xlim(-0.5, 255.5)
        ax.set_ylim(255.5, -0.5)
        ax.tick_params(colors=text_c, labelsize=6)

        # === CENTER panel: clean simulated pattern (always) ===
        ax2 = self.ax_sim
        ax2.clear()
        ax2.set_facecolor("black")
        synth_clean = generate_synthetic(
            self.grazing, self.azimuth, nx=128, ny=128,
            scale=self.scale*2, voltage_kv=self.voltage,
            lattice_param=self.crystal.lattice_param,
            noise=10, spot_sigma=1.5)
        ax2.imshow(synth_clean, cmap="inferno",
                   norm=PowerNorm(gamma=0.4, vmin=0,
                                  vmax=np.percentile(synth_clean, 99.5)),
                   origin="upper")
        ax2.set_title("SIMULATED (clean)", fontsize=8, color="#e0e0e0")
        ax2.tick_params(colors=text_c, labelsize=6)

        # === LIVE GEOMETRY SCHEMATIC ===
        self._draw_geometry(self.grazing, self.azimuth, on_det, text_c)

        # === INFO panel ===
        ax_i = self.ax_info
        ax_i.clear()
        ax_i.axis("off")
        ax_i.set_facecolor("#16213e")

        g_deg = self.grazing / 1e3 * 180 / np.pi
        lam = 12.2643 / np.sqrt(self.voltage*1e3*(1+0.978476e-6*self.voltage*1e3))

        # count spots by type
        n_r_zolz = sum(1 for s in on_det if s.get("type")=="reflection" and s.get("laue_zone",0)==0)
        n_r_holz = sum(1 for s in on_det if s.get("type")=="reflection" and s.get("laue_zone",0)!=0)
        n_t_zolz = sum(1 for s in on_det if s.get("type")=="transmission" and s.get("laue_zone",0)==0)
        n_t_holz = sum(1 for s in on_det if s.get("type")=="transmission" and s.get("laue_zone",0)!=0)

        info = (
            f"{self.crystal.summary()}\n"
            f"\n"
            f"--- Beam ---\n"
            f"Voltage: {self.voltage:.0f} kV | lam={lam:.4f} A\n"
            f"K = {2*np.pi/lam:.1f} A-1\n"
            f"\n"
            f"--- Geometry ---\n"
            f"Grazing: {self.grazing:.1f} mrad ({g_deg:.2f} deg)\n"
            f"Azimuth: {self.azimuth:.1f} mrad\n"
            f"Surface: (1-11), Beam: [110]\n"
            f"\n"
            f"--- Detector ---\n"
            f"Pixel: 55 um | {self.scale:.3f} mrad/px\n"
            f"FOV: {256*self.scale:.1f} x {256*self.scale:.1f} mrad\n"
            f"\n"
            f"--- Spots: {len(on_det)} total ---\n"
            f"  Refl ZOLZ:  {n_r_zolz:3d}  (red O)\n"
            f"  Refl HOLZ:  {n_r_holz:3d}  (orange O)\n"
            f"  Trans ZOLZ: {n_t_zolz:3d}  (blue sq)\n"
            f"  Trans HOLZ: {n_t_holz:3d}  (cyan sq)\n"
            f"\n"
            f"Mode: {self.mode.upper()}"
        )
        ax_i.text(0.05, 0.95, info, transform=ax_i.transAxes,
                  fontsize=7, fontfamily="monospace", color=text_c,
                  verticalalignment="top")

        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reflection Electron Diffraction Lab")
    parser.add_argument("--cif", type=str, default=None, help="Load CIF file")
    parser.add_argument("--xyz", type=str, default=None, help="Load XYZ file")
    parser.add_argument("--dir", type=str, default=None, help="Data directory with .hm files")
    parser.add_argument("--file", type=str, default=None, help="Specific .hm file")
    args = parser.parse_args()

    # load crystal structure
    if args.cif:
        crystal = CrystalStructure.from_cif(args.cif)
    elif args.xyz:
        crystal = CrystalStructure.from_xyz(args.xyz)
    else:
        crystal = CrystalStructure.from_si_default()

    data_dir = args.dir or str(Path(__file__).resolve().parent.parent)
    lab = DiffractionLab(crystal=crystal, data_dir=data_dir)
    lab.show()
