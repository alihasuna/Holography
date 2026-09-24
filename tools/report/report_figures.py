#!/usr/bin/env python3
"""Report figures of the R1 smoke campaign (pipeline overview, S1, S2, S3, S4, S5) and the copies of
the reused figures (S6 made by tools/plots/torus_compact.py, S7 and S8 from reports T1/T5).

Usage (repository root; stdout saved as tools/report/report_figures_output.txt):
    PYTHONPATH=. venv/bin/python tools/report/report_figures.py --runs SP/report_smoke \
        --out SP/report_smoke/figures --t1-figures SP/torus/figures --t5-figures SP/buried_t5/figures

Every figure reads the runs of tools/report/run_smoke_campaign.py (arrays.npz and summary.json of
``python -m reflection_holo.pipeline run``). Axes, units and the plane of every array are read from
summary.json["arrays"] and asserted, pixel sizes from summary.json["detector"] / ["exit_wave"] and
asserted against the coordinate arrays. Every number written on a figure is printed here. DEMO runs:
not comparable to experiment; the multislice engine is UNVALIDATED for step heights. 200 keV.
PNG, 150 dpi, white background, 7.5 in wide (readable at 7 in).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from reflection_holo.forward.multislice.overlayer import edge_profile  # noqa: E402
from reflection_holo.geometry.specular import wrap_to_pi  # noqa: E402

DPI = 150
W = 7.5
BLUE, ORANGE, GREEN, PURPLE, RED = "#2a78d6", "#eb6834", "#1baf7a", "#7b3fa0", "#c0392b"
INK, MUTED, LIGHT = "#1f1f1e", "#6b6a64", "#d9d8d2"
TERRACE = [BLUE, ORANGE, GREEN]
DET_AXES = ["along_beam", "perpendicular"]
DET_PLANE = "detector, specimen-referred image-plane coordinates"
EXIT_PLANE = "exit plane z = L_z (no further propagation)"
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "legend.fontsize": 7, "figure.facecolor": "white",
                     "axes.facecolor": "white", "savefig.facecolor": "white", "axes.edgecolor": INK,
                     "text.color": INK, "axes.labelcolor": INK})
DEMO = "DEMO, not comparable to experiment; 200 keV"


# ------------------------------------------------------------------------------------------------
# loading with asserted axes, planes and pixel sizes
# ------------------------------------------------------------------------------------------------
class Run:
    def __init__(self, runs: Path, name: str):
        self.name, self.dir = name, runs / name
        self.s = json.loads((self.dir / "summary.json").read_text())
        self.a = np.load(self.dir / "arrays.npz")
        assert self.s["beam_energy_keV"] == 200.0

    def arr(self, key: str, axes: list, plane: str):
        idx = self.s["arrays"][key]
        assert idx["axes"] == axes, (self.name, key, idx["axes"])
        assert idx["plane"].startswith(plane), (self.name, key, idx["plane"])
        v = self.a[key]
        assert list(v.shape) == idx["shape"], (self.name, key)
        return v

    def det(self, key: str):
        return self.arr(key, DET_AXES, DET_PLANE)

    def det_coords(self):
        u = self.arr("detector_u_A", ["along_beam"], DET_PLANE)
        y = self.arr("detector_y_A", ["perpendicular"], DET_PLANE)
        p = self.s["detector"]["pixel_A"]
        assert np.allclose(np.diff(u), p[0]) and np.allclose(np.diff(y), p[1]), self.name
        return u, y, p

    def exit_coords(self):
        x = self.arr("exit_x_A", ["x"], EXIT_PLANE)
        y = self.arr("exit_y_A", ["y"], EXIT_PLANE)
        ew = self.s["exit_wave"]
        assert np.allclose(np.diff(x), ew["dx_A"]) and np.allclose(np.diff(y), ew["dy_A"]), self.name
        return x, y

    def status_code(self, name: str) -> int:
        units = self.s["arrays"]["trace_status"]["units"]
        codes = eval(units.split("code ", 1)[1], {})          # "code {'lit': 0, ...}" as written
        return int(codes[name])


def _clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def _save(fig, out: Path, name: str) -> Path:
    p = out / name
    fig.savefig(p, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"figure: {p} ({fig.get_size_inches()[0]:.2f} x {fig.get_size_inches()[1]:.2f} in, {DPI} dpi)")
    return p


def _suptitle(fig, text: str, x=0.01, ha="left", fontsize=8):
    """Suptitle with every line wrapped at the width of a 7.5 in figure (about 118 characters at 8 pt)."""
    import textwrap
    width = int(118 * 8 / fontsize)
    lines = []
    for part in text.split("\n"):
        lines += textwrap.wrap(part, width=width) or [""]
    fig.suptitle("\n".join(lines), x=x, ha=ha, fontsize=fontsize)


def _det_extent(u, y):
    du, dy = u[1] - u[0], y[1] - y[0]
    return [y[0] - dy / 2, y[-1] + dy / 2, u[-1] + du / 2, u[0] - du / 2]   # downstream down


# ------------------------------------------------------------------------------------------------
# F0 pipeline overview
# ------------------------------------------------------------------------------------------------
def fig_overview(out: Path) -> Path:
    fig = plt.figure(figsize=(W, 8.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    stages = [
        ("1  Configuration and input gate",
         "reflection_holo.pipeline.config, io.config, io/assumption_registry.yaml",
         "every PROJECT_INPUT supplied or a registered ASSUMPTION Bxx stand-in;\n"
         "glancing angle computed from the declared rule (geometry.specular)"),
        ("2  Structure",
         "structure.si001 | features, shapes | oxide | thermal",
         "Si(001) atoms: staircase or surface feature, optional continuum oxide;\n"
         "step relations measured on the built atoms"),
        ("3  Forward engine  ->  exit wave",
         "forward.geometric  |  forward.multislice (+ forward.cell)",
         "geometric phase + ray trace (no dynamical amplitude), or multislice\n"
         "(UNVALIDATED for step heights); exit plane z = L_z"),
        ("4  Optics",
         "optics.darkfield, optics.projection, optics.inelastic, optics.coherence",
         "aperture around k_out (specular beam), projection along k_out,\n"
         "surface-plasmon loss, convergence members (pipeline.convergence)"),
        ("5  Reference, hologram, detector",
         "optics.fields, optics.hologram, optics.detector",
         "R1 vacuum reference, I = |u_o + u_r|^2 averaged AFTER squaring;\n"
         "empty hologram; magnification, pixel, Poisson dose, gain"),
        ("6  Reconstruction",
         "reconstruction.sideband",
         "carrier found on the EMPTY hologram, Hann mask |q_c|/3,\n"
         "division by the empty hologram, Itoh unwrapping"),
        ("7  Quantification: unwrapping and wrap resolution",
         "pipeline.quantify | pipeline.feature; quantification.shadow | height | controls",
         "ray-traced terrace regions; h_2pi = lambda / (2 sin theta); branch from the\n"
         "lattice constraint h = n a/4; no-step control on a flat terrace"),
        ("8  Height map / step heights",
         "summary.json, arrays.npz, manifest.json (provenance.manifest)",
         "signed heights +- sigma or a height map with its reliability map;\n"
         "manifest: versions, commit, precision, seeds, threads, input hashes"),
    ]
    gates = {
        0: "REFUSED, exit 3: a missing PROJECT_INPUT,\nan unregistered stand-in, TEST_ONLY in a\n"
           "file, a schema error; exit 6: git state\nunknown; exit 5: output directory not empty",
        2: "REFUSED, exit 3: outside the B4 scope\n(geometric engine); exit 4: engine or array\n"
           "backend unavailable; cell geometry\nassertions (docs/05 4.3) must pass",
        5: "pixel invalid: empty-hologram visibility < 0.5",
        6: "pixels excluded: shadow, riser, blocked view,\namplitude < 0.25 of the empty one, < 3\n"
           "resolutions from an unusable pixel; NO\nHEIGHT if the no-step control fails or is\n"
           "not performed; a height is refused if its\nlattice branch is ambiguous",
    }
    n = len(stages)
    top, bot = 0.925, 0.02
    h = (top - bot) / n
    x0, x1 = 0.02, 0.60
    for i, (title, mods, text) in enumerate(stages):
        yc = top - (i + 0.5) * h
        box = FancyBboxPatch((x0, yc - 0.42 * h), x1 - x0, 0.84 * h, boxstyle="round,pad=0.004,rounding_size=0.01",
                             fc="#eef3fb" if i not in (2,) else "#fdf0e9", ec=BLUE if i != 2 else ORANGE, lw=1.0)
        ax.add_patch(box)
        ax.text(x0 + 0.012, yc + 0.30 * h, title, fontsize=8.5, weight="bold", va="center")
        ax.text(x0 + 0.012, yc + 0.12 * h, mods, fontsize=6.6, family="monospace", color=MUTED, va="center")
        ax.text(x0 + 0.012, yc - 0.17 * h, text, fontsize=7, va="center", linespacing=1.25)
        if i < n - 1:
            ax.add_patch(FancyArrowPatch((0.31, yc - 0.42 * h), (0.31, yc - 0.58 * h), arrowstyle="-|>",
                                         mutation_scale=9, color=INK, lw=1.0))
        if i in gates:
            gy = yc
            ax.add_patch(FancyBboxPatch((0.64, gy - 0.42 * h), 0.35, 0.84 * h,
                                        boxstyle="round,pad=0.004,rounding_size=0.01", fc="#fbecea", ec=RED,
                                        lw=0.9, ls=(0, (3, 2))))
            ax.text(0.65, gy, gates[i], fontsize=6.9, va="center", color="#7a1f15", linespacing=1.15)
            ax.add_patch(FancyArrowPatch((x1, gy), (0.64, gy), arrowstyle="-|>", mutation_scale=8,
                                         color=RED, lw=0.9))
    ax.text(0.02, 0.975, "Reflection dark-field holography pipeline: python -m reflection_holo.pipeline run",
            fontsize=10, weight="bold", va="center")
    ax.text(0.02, 0.952, "main chain (left) and refusal gates (right, red); " + DEMO +
            "; stages as in reflection_holo/pipeline/run.py", fontsize=7, color=MUTED, va="center")
    print("F0 overview: stages and gates as listed in reflection_holo/pipeline/run.py (docstring) and "
          "reflection_holo/pipeline/__main__.py (exit codes); thresholds from configs/demo_smoke_si001.yaml "
          "(B29: visibility 0.5, amplitude 0.25, margin 3 resolutions)")
    return _save(fig, out, "f0_pipeline_overview.png")


# ------------------------------------------------------------------------------------------------
# S1 geometric staircase
# ------------------------------------------------------------------------------------------------
def fig_s1(runs: Path, out: Path) -> Path:
    r = Run(runs, "S1_base")
    u, y, p = r.det_coords()
    H = r.det("hologram_object_counts")
    ph = r.det("phase_wrapped")
    amp = r.det("amplitude")
    reg = r.det("region_map")
    ft = r.det("trace_field_terrace")
    zsrc = r.det("trace_source_z_A")
    usable = r.det("usable_mask")
    s = r.s
    tmap = s["structure"]["terrace_map"]
    steps = [st for st in s["quantification"]["steps"]]
    # the traced source z of every usable pixel lies inside its terrace's range (asserted)
    for t in tmap:
        m = usable & (ft == t["index"])
        z = zsrc[m]
        assert np.all((z >= t["s_range_A"][0] - 1e-6) & (z <= t["s_range_A"][1] + 1e-6)), t["index"]
    fig = plt.figure(figsize=(W, 7.4))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.35, 1.0], hspace=0.45, wspace=0.6,
                          left=0.08, right=0.97, top=0.84, bottom=0.07)
    ext = _det_extent(u, y)
    # (a) hologram crop across step 0 -> 1
    row_t = np.array([np.bincount(ft[i][usable[i]]).argmax() if usable[i].any() else -1
                      for i in range(len(u))])
    r0 = int(np.where(row_t == 0)[0].max())                  # last row of terrace 0 before step 0->1
    assert row_t[r0 + 1:][row_t[r0 + 1:] >= 0][0] == 1
    rs = slice(max(r0 - 24, 0), r0 + 24)
    cs = slice(0, 24)
    ax = fig.add_subplot(gs[0, 0])
    ax.imshow(H[rs, cs], cmap="gray", aspect="auto", interpolation="nearest",
              extent=[y[cs][0] - p[1] / 2, y[cs][-1] + p[1] / 2, u[rs][-1] + p[0] / 2, u[rs][0] - p[0] / 2])
    ax.axhline(u[r0] + p[0] / 2, color=ORANGE, lw=0.8, ls=(0, (3, 2)))
    ax.set_title("(a) object hologram (counts),\ncrop across step 0->1", loc="left")
    ax.set_xlabel("perpendicular y (A)")
    ax.set_ylabel("along the beam u (A, image plane)")
    # (b) wrapped phase, (c) amplitude, (d) regions
    ax = fig.add_subplot(gs[0, 1])
    im = ax.imshow(ph, cmap="twilight", vmin=-np.pi, vmax=np.pi, aspect="auto", extent=ext,
                   interpolation="nearest")
    fig.colorbar(im, ax=ax, fraction=0.08, pad=0.03)
    ax.set_title("(b) reconstructed\nwrapped phase (rad)", loc="left")
    ax.set_xlabel("y (A)")
    ax = fig.add_subplot(gs[0, 2])
    im = ax.imshow(amp, cmap="gray", vmin=0, vmax=1.2, aspect="auto", extent=ext, interpolation="nearest")
    fig.colorbar(im, ax=ax, fraction=0.08, pad=0.03)
    ax.set_title("(c) reconstructed amp-\nlitude (/ empty)", loc="left")
    ax.set_xlabel("y (A)")
    ax = fig.add_subplot(gs[0, 3])
    cm = ListedColormap(["#f2f1ec"] + TERRACE)
    ax.imshow(reg, cmap=cm, vmin=-1.5, vmax=2.5, aspect="auto", extent=ext, interpolation="nearest")
    ax.set_title("(d) quantification\nregions (terraces 0-2)", loc="left")
    ax.set_xlabel("y (A)")
    # (e) wrapped phase along the beam, (f) heights
    rows = np.where(usable.any(axis=1))[0]
    zrow = np.array([np.median(zsrc[i][usable[i]]) for i in rows])
    prow = np.array([np.median(ph[i][usable[i]]) for i in rows])
    ax = fig.add_subplot(gs[1, :2])
    ax.plot(zrow, prow, ".", ms=2.2, color=INK, label="row median of usable pixels")
    for k, rg in s["quantification"]["regions"].items():
        if "phase" in rg:
            t = tmap[int(k) % len(tmap)]
            ax.hlines(rg["phase"]["median_rad"], *t["s_range_A"], color=TERRACE[int(k) % 3], lw=2,
                      label=f"terrace {k} region median {rg['phase']['median_rad']:+.3f} rad")
    ax.set_ylim(-np.pi, np.pi)
    ax.set_xlabel("surface coordinate z along the beam (A)")
    ax.set_ylabel("wrapped phase (rad)")
    ax.set_title("(e) wrapped phase along the beam", loc="left")
    ax.legend(frameon=False, loc="upper left", fontsize=6.3)
    _clean(ax)
    ax = fig.add_subplot(gs[1, 2:])
    base = tmap[0]["top_height_A"]
    for t in tmap:
        ax.hlines(t["top_height_A"] - base, *t["s_range_A"], color=LIGHT, lw=6, zorder=1)
    ax.plot([], [], color=LIGHT, lw=6, label="built terrace tops")
    lv = {0: 0.0}
    for st in steps[:2]:
        lv[st["to_field_terrace"]] = lv[st["from_field_terrace"]] + st["height"]["h_A"]
    closure = sum(st["height"]["h_A"] for st in steps)
    for k, v in lv.items():
        t = tmap[k]
        ax.plot(0.5 * sum(t["s_range_A"]), v, "o", color=TERRACE[k], ms=5, zorder=3)
    ax.plot([], [], "o", color=INK, ms=4, label="recovered (from the measured steps)")
    for st in steps[:2]:
        h = st["height"]
        zb = tmap[st["from_field_terrace"]]["s_range_A"][1]
        y0_ = lv[st["from_field_terrace"]]
        ax.add_patch(FancyArrowPatch((zb, y0_), (zb, y0_ + h["h_A"]), arrowstyle="-|>", mutation_scale=8,
                                     color=INK, lw=0.9))
        ax.annotate(f"step {st['from_field_terrace']}->{st['to_field_terrace']}:\n{h['h_A']:+.4f} +- "
                    f"{h['sigma_h_A']:.4f} A\n(built {st['built_height_A']:+.4f} A)",
                    (zb, y0_ + h["h_A"] / 2), xytext=(-4 if h["h_A"] > 0 else 4, 0),
                    textcoords="offset points", fontsize=6.3, va="center",
                    ha="right" if h["h_A"] > 0 else "left")
    ax.set_xlabel("surface coordinate z along the beam (A)")
    ax.set_ylabel("height relative to terrace 0 (A)")
    ax.set_title("(f) terrace heights: built vs recovered", loc="left")
    ax.set_ylim(-0.6, 3.4)
    ax.legend(frameon=False, loc="upper right", fontsize=6.3)
    _clean(ax)
    c = s["quantification"]["no_step_control"]
    _suptitle(fig, "S1 geometric smoke test: Si(001) staircase (a/2 up, a/4 down twice), specular (0,0,8) at "
                 f"{s['glancing_angle']['value_mrad']:.4f} mrad (B19)\ngeometric engine (no dynamical "
                 f"amplitude); {DEMO}\nno-step control {c['delta_rad']:+.4f} rad vs tolerance "
                 f"{c['tolerance_rad']:.4f} rad (passed); closure of the three steps "
                 f"{closure:+.5f} A", x=0.01, ha="left", fontsize=8)
    print(f"S1: crop rows {rs.start}-{rs.stop} (step 0->1 after row {r0}), columns {cs.start}-{cs.stop}")
    for st in steps:
        h = st["height"]
        print(f"S1: step {st['from_field_terrace']}->{st['to_field_terrace']}: {h['h_A']:+.4f} +- "
              f"{h['sigma_h_A']:.4f} A, built {st['built_height_A']:+.4f} A")
    print(f"S1: recovered levels {dict((k, round(v, 5)) for k, v in lv.items())} A; closure of the three "
          f"steps {closure:+.5f} A; built levels "
          f"{[round(t['top_height_A'] - base, 5) for t in tmap]} A")
    print(f"S1: no-step control {c['delta_rad']:+.4f} rad vs tolerance {c['tolerance_rad']:.4f} rad")
    return _save(fig, out, "s1_staircase_geometric.png")


# ------------------------------------------------------------------------------------------------
# S2 tiny multislice: supercell and complex exit wave
# ------------------------------------------------------------------------------------------------
def fig_s2(runs: Path, out: Path) -> Path:
    from reflection_holo.pipeline.config import load_pipeline_file
    from reflection_holo.pipeline.engines import build_structure, reflection_cell
    r = Run(runs, "S2_multislice_tiny")
    cfg = load_pipeline_file(REPO / "configs/demo_smoke_si001.yaml", variant="multislice_tiny")
    assert cfg.sha256_resolved == r.s["config"]["sha256_resolved"]
    cell = reflection_cell(build_structure(cfg), cfg)
    man = json.loads(Path(r.s["engine"]["engine_manifest"]).read_text())
    mc = man["extra"]["run_configuration"]["cell"]
    xyz = np.asarray(cell.atoms_xyz_A)
    assert len(xyz) == mc["n_atoms"] and abs(cell.length_z_A - mc["length_z_A"]) < 1e-9
    x, y = r.exit_coords()
    psi = r.arr("exit_psi_r0", ["x", "y"], EXIT_PLANE)
    df = r.arr("darkfield_r0", ["x", "y"], EXIT_PLANE)
    lay = r.s["engine"]["cell_layout"]
    tlen = tm_len = r.s["structure"]["terrace_map"][0]["s_range_A"][1] - r.s["structure"]["terrace_map"][0]["s_range_A"][0]
    res_s = r.s["reconstruction"]["resolution_A"] / math.sin(r.s["glancing_angle"]["value_rad"])
    print(f"S2: terrace length {tm_len:.3f} A; reconstruction resolution on the surface {res_s:.1f} A; "
          f"margin {r.s['quantification']['shadow_exclusion']['margin_resolutions']} resolutions")
    fig = plt.figure(figsize=(W, 6.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[0.9, 1.25], hspace=0.5, wspace=0.55,
                          left=0.09, right=0.96, top=0.84, bottom=0.08)
    ax = fig.add_subplot(gs[0, :])
    sel = np.abs(xyz[:, 1] - np.median(xyz[:, 1])) < 1.0
    tm = r.s["structure"]["terrace_map"]
    zrel = xyz[:, 2] - cell.crystal_start_z_A
    for t in tm:
        m = sel & (zrel >= t["s_range_A"][0] - 1e-6) & (zrel < t["s_range_A"][1] - 1e-6)
        ax.scatter(xyz[m, 2], xyz[m, 0], s=0.25, color=TERRACE[t["index"] % 3], rasterized=True)
        ax.text(cell.crystal_start_z_A + 0.5 * sum(t["s_range_A"]), lay["highest_surface_x_A"] + 20,
                f"terrace {t['index']}: top layer +{t['top_layer_relative']} x a/4", ha="center", fontsize=6.5,
                color=TERRACE[t["index"] % 3])
    for lo, hi, lab in ((lay["bulk_absorber_x_A"][0], lay["bulk_absorber_x_A"][1], "bulk absorber"),
                        (lay["top_absorber_x_A"][0], lay["top_absorber_x_A"][1], "top absorber")):
        ax.axhspan(lo, hi, color=LIGHT, alpha=0.6, lw=0)
        ax.text(1250, 0.5 * (lo + hi), lab + " (numerical)", fontsize=6, va="center", color=MUTED,
                bbox=dict(fc="white", ec="none", pad=0.5))
    bm = r.s["engine"]["beam"]
    ax.axhspan(bm["x_bottom_A"], bm["x_bottom_A"] + bm["height_A"], xmax=0.02, color=ORANGE, alpha=0.8)
    ax.text(40, bm["x_bottom_A"] + bm["height_A"] / 2, f"<- sheet beam at launch ({bm['height_A']} A high)",
            fontsize=6, va="center", color=ORANGE)
    ax.set_xlim(0, cell.length_z_A)
    ax.set_ylim(0, lay["top_absorber_x_A"][1])
    ax.set_xlabel("z along the beam (A)")
    ax.set_ylabel("x, outward normal (A)")
    ax.set_title(f"(a) supercell, side view (atoms within 1 A of the y mid-plane); {len(xyz):,} atoms; box "
                 f"{mc['extent_x_A']:.1f} x {mc['extent_y_A']:.2f} x {mc['length_z_A']:.1f} A (x, y, z)",
                 loc="left", fontsize=7.5)
    _clean(ax)
    ext = [y[0], y[-1], x[0], x[-1]]
    ax = fig.add_subplot(gs[1, 0])
    im = ax.imshow(np.abs(psi), origin="lower", aspect="auto", extent=ext, cmap="gray")
    fig.colorbar(im, ax=ax, fraction=0.08, pad=0.03)
    ax.set_title("(b) |psi| at the exit plane", loc="left")
    ax.set_xlabel("y (A)")
    ax.set_ylabel("x, outward normal (A)")
    ax = fig.add_subplot(gs[1, 1])
    im = ax.imshow(np.angle(psi), origin="lower", aspect="auto", extent=ext, cmap="twilight",
                   vmin=-np.pi, vmax=np.pi)
    fig.colorbar(im, ax=ax, fraction=0.08, pad=0.03)
    ax.set_title("(c) arg psi (rad, cyclic)", loc="left")
    ax.set_xlabel("y (A)")
    ax = fig.add_subplot(gs[1, 2])
    ax.plot(np.abs(psi).mean(axis=1), x, color=MUTED, lw=1, label="|psi| (all beams)")
    ap_mrad = r.s["dark_field"]["semi_angle_rad"] * 1e3
    ax.plot(np.abs(df).mean(axis=1), x, color=BLUE, lw=1.4, label=f"|psi_specular| ({ap_mrad:g} mrad aperture)")
    ax.axhline(lay["lowest_surface_x_A"], color=INK, lw=0.6, ls=(0, (3, 2)))
    ax.axhline(lay["highest_surface_x_A"], color=INK, lw=0.6, ls=(0, (1, 2)))
    ax.set_xlabel("mean over y")
    ax.set_ylabel("x (A)")
    ax.set_title("(d) amplitude profiles", loc="left")
    ax.legend(frameon=False, fontsize=6, loc="upper right", bbox_to_anchor=(1.05, 1.0))
    _clean(ax)
    _suptitle(fig, "S2 tiny multislice smoke test (variant multislice_tiny): Kirkland IAM potential, static "
                 f"lattice,\nno absorption (B30), glancing angle {r.s['glancing_angle']['value_mrad']:.4f} mrad "
                 f"(B32); engine UNVALIDATED for step heights;\nterraces of {tlen:.0f} A are shorter than the "
                 f"3-resolution margin (3 x {res_s:.0f} A of surface), so no region survives: NO HEIGHT; {DEMO}",
                 x=0.01, ha="left", fontsize=8)
    print(f"S2: {len(xyz)} atoms; box {mc['extent_x_A']:.4f} x {mc['extent_y_A']:.4f} x {mc['length_z_A']:.4f} A; "
          f"exit grid {psi.shape} dx {x[1] - x[0]:.4f} dy {y[1] - y[0]:.4f} A; surfaces x "
          f"{lay['lowest_surface_x_A']} / {lay['highest_surface_x_A']} A; beam x_bottom {bm['x_bottom_A']} A")
    return _save(fig, out, "s2_multislice_tiny_supercell_exitwave.png")


# ------------------------------------------------------------------------------------------------
# S3 thermal vs static
# ------------------------------------------------------------------------------------------------
def fig_s3(runs: Path, out: Path) -> Path:
    r2, r3 = Run(runs, "S2_multislice_tiny"), Run(runs, "S3_multislice_tiny_thermal")
    x2, _ = r2.exit_coords()
    x3, _ = r3.exit_coords()
    assert np.array_equal(x2, x3)
    d2 = r2.arr("darkfield_r0", ["x", "y"], EXIT_PLANE)
    d3 = r3.arr("darkfield_r0", ["x", "y"], EXIT_PLANE)
    u2, y2, _ = r2.det_coords()
    u3, _, _ = r3.det_coords()
    assert np.array_equal(u2, u3)
    o2, o3 = r2.det("detector_object_r0"), r3.det("detector_object_r0")
    lit2 = r2.det("trace_status") == r2.status_code("lit")
    lit3 = r3.det("trace_status") == r3.status_code("lit")
    assert np.array_equal(lit2, lit3)
    rms2 = float(np.sqrt(np.mean(np.abs(o2[lit2]) ** 2)))
    rms3 = float(np.sqrt(np.mean(np.abs(o3[lit3]) ** 2)))
    th = r3.s["engine"]["thermal_model"]
    B = th["B_A2"]
    g = 8.0 / 5.4309                         # |g_008| = 8/a (cycles/A); a = 5.4309 A (B2)
    dw = math.exp(-B * (g / 2.0) ** 2)
    fig, axs = plt.subplots(1, 2, figsize=(W, 3.9))
    ax = axs[0]
    ax.plot(np.abs(d2).mean(axis=1), x2, color=BLUE, lw=1.3, label="static lattice (S2)")
    ax.plot(np.abs(d3).mean(axis=1), x3, color=ORANGE, lw=1.3, label="frozen phonons, realisation 0 (S3)")
    ax.set_xlabel("|psi_specular| at the exit plane (mean over y)")
    ax.set_ylabel("x, outward normal (A)")
    ax.set_title("(a) specular (dark-field) beam at the exit plane", loc="left")
    ax.legend(frameon=False, fontsize=6.5)
    _clean(ax)
    ax = axs[1]
    p2 = np.array([np.sqrt(np.mean(np.abs(o2[i][lit2[i]]) ** 2)) if lit2[i].any() else np.nan for i in range(len(u2))])
    p3 = np.array([np.sqrt(np.mean(np.abs(o3[i][lit3[i]]) ** 2)) if lit3[i].any() else np.nan for i in range(len(u3))])
    ax.plot(u2, p2, "o-", ms=3, color=BLUE, lw=1, label=f"static: RMS {rms2:.4f}")
    ax.plot(u3, p3, "s-", ms=3, color=ORANGE, lw=1, label=f"thermal r0: RMS {rms3:.4f}")
    ax.set_xlabel("along the beam u (A, image plane)")
    ax.set_ylabel("|object wave| on the detector (lit px, RMS per row)")
    ax.set_title("(b) object amplitude on the detector", loc="left")
    ax.legend(frameon=False, fontsize=6.5)
    _clean(ax)
    _suptitle(fig, f"S3 frozen phonons (B35, T = {th['specimen_temperature_K']} K B36, u = "
                 f"{th['u_per_axis_A']:.4f} A per axis, {r3.s['exit_wave']['n_realisations']} realisations "
                 f"averaged after squaring) vs static S2\nratio thermal/static {rms3 / rms2:.3f} (one "
                 f"realisation; tiny cell, UNVALIDATED engine, indicative only); (0,0,8) Debye-Waller "
                 f"amplitude exp(-B (g/2)^2) = {dw:.4f}; {DEMO}", x=0.01, ha="left", fontsize=7.5)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.76, bottom=0.13, wspace=0.35)
    print(f"S3: RMS |detector object| over lit pixels (realisation 0): static {rms2:.5f}, thermal "
          f"{rms3:.5f}, ratio {rms3 / rms2:.4f}; summary empty_object_amplitude static "
          f"{r2.s['detector']['empty_object_amplitude']:.5f}, thermal {r3.s['detector']['empty_object_amplitude']:.5f}")
    print(f"S3: B = {B} A^2 (B35 at {th['specimen_temperature_K']} K), |g_008| = 8/a = {g:.5f} 1/A, "
          f"Debye-Waller amplitude exp(-B (g/2)^2) = {dw:.4f} (DERIVED_HERE)")
    return _save(fig, out, "s3_thermal_vs_static.png")


# ------------------------------------------------------------------------------------------------
# S4 plasmon loss: fringe contrast
# ------------------------------------------------------------------------------------------------
def _contrast(profile):
    return float((profile.max() - profile.min()) / (profile.max() + profile.min()))


def fig_s4(runs: Path, out: Path) -> Path:
    r1, r4 = Run(runs, "S1_base"), Run(runs, "S4_plasmon_losses")
    u, y, p = r1.det_coords()
    lit = r1.det("trace_status") == r1.status_code("lit")
    fig = plt.figure(figsize=(W, 5.6))
    gs = fig.add_gridspec(2, 3, hspace=0.6, wspace=0.45, left=0.08, right=0.97, top=0.82, bottom=0.09)
    out_rec = {}
    n1_ = r1.s["surface_plasmon_losses"]["mean_excitations_object"]
    n4_ = r4.s["surface_plasmon_losses"]["mean_excitations_object"]
    dose = r4.s["detector"]["dose_e_per_px"]
    assert dose == r1.s["detector"]["dose_e_per_px"]
    short = [f"S1, n = {n1_:g}", f"S4, n = {n4_:g}"]
    for k, (r, lab, col) in enumerate(((r1, f"no loss (S1, n = {n1_:g})", BLUE),
                                       (r4, f"plasmon loss (S4, n = {n4_:g})", ORANGE))):
        He = r.det("hologram_empty_noiseless")
        Hc = r.det("hologram_object_counts")
        rows = np.where(lit.all(axis=1))[0]
        prof = He[rows].mean(axis=0)
        prof = prof / prof.mean()
        c = _contrast(He[rows[len(rows) // 2]])
        out_rec[r.name] = dict(contrast=c, summary=r.s["reference"]["empty_hologram_fringe_contrast"])
        ax = fig.add_subplot(gs[k, 0])
        rs, cs = slice(200, 216), slice(0, 16)
        crop = Hc[rs, cs] / Hc[rs, cs].mean()
        ax.imshow(crop, cmap="gray", vmin=0.0, vmax=2.2, aspect="auto", interpolation="nearest",
                  extent=[y[cs][0], y[cs][-1] + p[1], u[rs][-1] + p[0], u[rs][0]])
        ax.set_title(f"({'ab'[k]}) object hologram, {short[k]}\n(counts / mean; "
                     f"grey 0-2.2)", loc="left", fontsize=7)
        ax.set_xlabel("y (A)")
        ax.set_ylabel("u (A)")
        ax = fig.add_subplot(gs[0, 1:]) if k == 0 else ax2
        ax2 = ax
        ax.plot(y[:24], prof[:24], "-o", ms=2.5, color=col, lw=1.2,
                label=f"{lab}: contrast {c:.4f}")
        # measured phase noise inside the terrace-1 region
        ph = r.det("phase_wrapped")
        reg = r.det("region_map")
        m = reg == 1
        res = np.asarray(wrap_to_pi(ph[m] - np.median(ph[m])))
        out_rec[r.name]["std"] = float(np.std(res))
        out_rec[r.name]["scatter"] = r.s["quantification"]["regions"]["1"]["phase"]["scatter_rad"]
        out_rec[r.name]["pred"] = r.s["reconstruction"]["predicted_phase_noise_per_px"]["sigma_phi_rad"]
        axh = fig.add_subplot(gs[1, 1:]) if k == 0 else axh
        axh.hist(res, bins=np.linspace(-0.05, 0.05, 81), histtype="step", color=col, lw=1.3,
                 label=f"{lab}: std {np.std(res):.4f} rad (predicted {out_rec[r.name]['pred']:.4f})")
    ax2.set_xlabel("perpendicular y (A)")
    ax2.set_ylabel("empty hologram / mean (noiseless)")
    ax2.set_title("(c) fringes of the empty hologram (mean over fully lit rows)", loc="left")
    ax2.legend(frameon=False, fontsize=6.5, loc="upper right")
    ax2.set_ylim(-0.05, 2.6)
    _clean(ax2)
    axh.set_xlabel("wrapped phase - median, terrace-1 region (rad)")
    axh.set_ylabel("pixels")
    axh.set_title(f"(d) phase noise at the same dose ({dose:g} e/px)", loc="left")
    axh.set_ylim(0, axh.get_ylim()[1] * 1.45)
    axh.legend(frameon=False, fontsize=6.3, loc="upper left")
    _clean(axh)
    s4 = r4.s["surface_plasmon_losses"]
    sid = r4.s["surface_plasmon_losses"]["object_label"].split()[1]
    _suptitle(fig, f"S4 surface-plasmon loss of the object beam (stand-in {sid}, n = {n4_:g} per reflection): "
                 f"zero-loss amplitude exp(-n/2) = {s4['zero_loss_amplitude_object']:.4f}; "
                 f"{100 * s4['loss_fraction_object']:.1f} % of the object intensity is fringe-free background "
                 f"(R1 vacuum reference).\nGeometric engine; {DEMO}", x=0.01, ha="left", fontsize=8)
    for k, v in out_rec.items():
        print(f"S4: {k}: empty-hologram fringe contrast measured on a noiseless lit row {v['contrast']:.4f} "
              f"(summary {v['summary']:.4f}); terrace-1 phase residual std {v['std']:.5f} rad (summary "
              f"scatter {v['scatter']:.5f}; predicted per px {v['pred']:.5f})")
    return _save(fig, out, "s4_plasmon_fringe_contrast.png")


# ------------------------------------------------------------------------------------------------
# S5 oxide
# ------------------------------------------------------------------------------------------------
def fig_s5(runs: Path, out: Path) -> Path:
    names = ["S1_base", "S5_oxide_2p0nm", "S5_oxide_2p0nm_no_absorption", "S5_oxide_1p5nm",
             "S5_oxide_1p5nm_no_absorption"]
    labels = ["no oxide (S1)"]
    cols = [INK, PURPLE, "#b48ad6", GREEN, "#8fd9b8"]
    rr = [Run(runs, n) for n in names]
    for r in rr[1:]:
        o_ = r.s["structure"]["options"]["overlayer"]
        labels.append(f"{o_['thickness_A'] / 10:.1f} nm, V' {o_['V_imag_V']:g} V")
    ox = rr[1].s
    tm = ox["structure"]["terrace_map"]
    opt = ox["structure"]["options"]["overlayer"]
    a4 = 5.4309 / 4
    fig = plt.figure(figsize=(W, 6.8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.35, 1], hspace=0.45, wspace=0.38,
                          left=0.1, right=0.97, top=0.85, bottom=0.08)
    # (a) cross-section across step 0 -> 1 (a/2 up-step), 2.0 nm oxide, from the built record
    ax = fig.add_subplot(gs[0, 0])
    zstep = tm[0]["s_range_A"][1]
    win = 30.0
    xg = np.linspace(-1.0, 32.0, 700)
    Vmax = opt["V_real_V"]
    for t, (z0, z1) in ((tm[0], (zstep - win, zstep)), (tm[1], (zstep, zstep + win))):
        o = t["oxide"]
        prof = (edge_profile(xg, o["top_x_A"], opt["vacuum_edge_width_A"], xg[1] - xg[0])
                - edge_profile(xg, o["interface_x_A"], opt["interface_width_A"], xg[1] - xg[0]))
        ax.pcolormesh([z0 - zstep, z1 - zstep], xg, np.repeat(prof[:, None], 1, axis=1)[:-1],
                      cmap="Purples", vmin=0, vmax=1.6, shading="flat")
        top = o["measured_crystal_top_x_A"]
        k = np.arange(0, int(round(top / a4)) + 1)
        for xl in top - k * a4:
            ax.hlines(xl, z0 - zstep, z1 - zstep, color=INK, lw=1.1)
        for j in range(1, o["consumed_layers"] + 1):
            ax.hlines(top + j * a4, z0 - zstep, z1 - zstep, color=MUTED, lw=0.6, ls=(0, (1, 2)))
        ax.hlines(o["pre_oxidation_surface_x_A"], z0 - zstep, z1 - zstep, color=ORANGE, lw=0.8,
                  ls=(0, (4, 2)))
        ax.hlines([o["interface_x_A"], o["top_x_A"]], z0 - zstep, z1 - zstep, color=PURPLE, lw=0.8)
    ax.axvline(0, color=MUTED, lw=0.5)
    ax.plot([], [], color=INK, lw=1.1, label="kept atomic planes (a/4 apart)")
    ax.plot([], [], color=MUTED, lw=0.6, ls=(0, (1, 2)), label=f"consumed planes ({opt['consumed_layers']})")
    ax.plot([], [], color=ORANGE, lw=0.8, ls=(0, (4, 2)), label="pre-oxidation surface H")
    ax.plot([], [], color=PURPLE, lw=0.8, label="oxide interface / top (graded 0.5 A)")
    ax.set_xlim(-win, win)
    ax.set_ylim(-1, 44)
    ax.set_yticks(range(0, 35, 5))
    ax.set_xlabel("z - z_step (A), step 0->1 (a/2 up-step)")
    ax.set_ylabel("x, outward normal (A)")
    ax.set_title(f"(a) stack across the a/2 step, {labels[1]} (schematic from the\nbuilt record; shading = "
                 "oxide potential fraction; riser not modelled)", loc="left", fontsize=7.5)
    ax.legend(frameon=False, fontsize=6, loc="upper center", ncol=2)
    ax.text(-win + 1, 31.5, "vacuum", fontsize=6.5, color=MUTED)
    # (b) layer potential profile of terrace 0, both thicknesses
    ax = fig.add_subplot(gs[0, 1])
    for r, lab, col in ((rr[1], labels[1], PURPLE), (rr[3], labels[3], GREEN)):
        o = r.s["structure"]["terrace_map"][0]["oxide"]
        op = r.s["structure"]["options"]["overlayer"]
        xl = np.linspace(o["interface_x_A"] - 4, o["top_x_A"] + 4, 1200)
        prof = op["V_real_V"] * (edge_profile(xl, o["top_x_A"], op["vacuum_edge_width_A"], xl[1] - xl[0])
                                 - edge_profile(xl, o["interface_x_A"], op["interface_width_A"], xl[1] - xl[0]))
        ax.plot(xl - o["interface_x_A"], prof, color=col, lw=1.3, label=f"{lab}: t = {op['thickness_A']} A")
    ax.set_xlabel("x - x_interface (A), terrace 0")
    ax.set_ylabel("V_ox, real part (V)")
    ax.set_title(f"(b) continuum oxide potential (erfc edges,\nw = {opt['vacuum_edge_width_A']:g} / "
                 f"{opt['interface_width_A']:g} A; B41)", loc="left", fontsize=7.5)
    ax.legend(frameon=False, fontsize=6.3, loc="lower center")
    _clean(ax)
    # (c) recovered heights - built
    ax = fig.add_subplot(gs[1, 0])
    for j, (r, lab, col) in enumerate(zip(rr, labels, cols)):
        sts = [st for st in r.s["quantification"]["steps"] if st.get("height")]
        for i, st in enumerate(sts):
            d = st["height"]["h_A"] - st["built_height_A"]
            ax.errorbar(i + (j - 2) * 0.12, d, yerr=st["height"]["sigma_h_A"], fmt="o", ms=3.5, color=col,
                        capsize=2, lw=1, label=lab if i == 0 else None)
            print(f"S5: {r.name} step {st['from_field_terrace']}->{st['to_field_terrace']}: h - built = "
                  f"{d:+.5f} +- {st['height']['sigma_h_A']:.5f} A")
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_xticks([0, 1, 2], ["0->1\n(a/2 up)", "1->2\n(a/4 down)", "2->0\n(a/4 down)"])
    ax.set_ylabel("recovered - built height (A), 1 sigma")
    ax.set_title("(c) step heights with and without oxide", loc="left")
    ax.set_ylim(-0.02, 0.032)
    ax.legend(frameon=False, fontsize=6, ncol=3, loc="upper center")
    _clean(ax)
    # (d) object amplitude on the detector along the beam
    ax = fig.add_subplot(gs[1, 1])
    for r, lab, col in zip(rr, labels, cols):
        u, _, _ = r.det_coords()
        o = r.det("detector_object_r0")
        lit = r.det("trace_status") == r.status_code("lit")
        prof = np.array([np.median(np.abs(o[i][lit[i]])) if lit[i].any() else np.nan for i in range(len(u))])
        ax.plot(u, prof, color=col, lw=1.1, label=f"{lab}: {r.s['detector']['empty_object_amplitude']:.4f}")
    ax.set_xlabel("along the beam u (A, image plane)")
    ax.set_ylabel("|object wave| on the detector (row median, lit)")
    ax.set_title("(d) reflected amplitude (legend: RMS over lit px)", loc="left", fontsize=7.5)
    ax.set_ylim(0, 1.75)
    ax.legend(frameon=False, fontsize=5.8, loc="upper center", ncol=2)
    _clean(ax)
    _suptitle(fig, "S5 continuum oxide overlayer (stand-in B41, conformal; geometric engine): step heights "
                 "unchanged, terrace phases shifted by a common offset, amplitude reduced by the zero-loss "
                 f"factor exp(-2 Im k'_perp t).\n{DEMO}", x=0.01, ha="left", fontsize=8)
    for t in tm:
        o = t["oxide"]
        print(f"S5: {labels[1]}, terrace {t['index']}: kept crystal top x {o['measured_crystal_top_x_A']:.4f} A, "
              f"{o['consumed_layers']} consumed planes up to H = {o['pre_oxidation_surface_x_A']:.4f} A, "
              f"interface {o['interface_x_A']:.4f} A, top {o['top_x_A']:.4f} A")
    for r in rr:
        print(f"S5: {r.name}: RMS detector object amplitude over lit px {r.s['detector']['empty_object_amplitude']:.4f}")
    return _save(fig, out, "s5_oxide_stack_heights.png")


# ------------------------------------------------------------------------------------------------
# reused figures (copied with their SHA-256)
# ------------------------------------------------------------------------------------------------
def copy_reused(src: Path, dst: Path) -> None:
    shutil.copyfile(src, dst)
    h = hashlib.sha256(dst.read_bytes()).hexdigest()
    print(f"reused: {src} -> {dst} (sha256 {h})")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--t1-figures", required=True, type=Path)
    ap.add_argument("--t5-figures", required=True, type=Path)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    todo = args.only or ["overview", "s1", "s2", "s3", "s4", "s5", "reuse"]
    if "overview" in todo:
        fig_overview(args.out)
    if "s1" in todo:
        fig_s1(args.runs, args.out)
    if "s2" in todo:
        fig_s2(args.runs, args.out)
    if "s3" in todo:
        fig_s3(args.runs, args.out)
    if "s4" in todo:
        fig_s4(args.runs, args.out)
    if "s5" in todo:
        fig_s5(args.runs, args.out)
    if "reuse" in todo:
        for name, new in (("supercell_trench.png", "s7_supercell_trench_T1.png"),
                          ("exitwave_trench.png", "s7_exitwave_trench_T1.png"),
                          ("exitwave_ridge.png", "s7_exitwave_ridge_T1.png")):
            copy_reused(args.t1_figures / name, args.out / new)
        copy_reused(args.t5_figures / "buried_compact.png", args.out / "s8_buried_compact_T5.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
