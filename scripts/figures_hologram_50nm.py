#!/usr/bin/env python3
"""Nature-style figure: the off-axis hologram and the reconstructed complex wave of the 50 nm deep
60 degree and Lomer dislocations at (008).

Columns: 60 degree (configs/si001_60deg_50nm.yaml), Lomer (configs/si001_lomer_50nm.yaml).
  row 1  recorded hologram, 400 counts per pixel, 10 nm crop: object hologram (bottom) under the
         empty reference hologram (top), so the fringe shift reads directly
  row 2  reconstructed complex wave over +-200 nm: hue = phase, brightness = amplitude
  row 3  holographic interferogram cos(phase): one dark band per 2 pi

Input: results.npz of scripts/run_sections.py (the reconstructed (008) wave along y). Geometric
mode has no dependence on the image row (exit height), so its maps are uniform along that axis;
multislice results (when --kind ms and present) carry the same 1D profile, averaged over the rows.

Usage:
  python scripts/figures_hologram_50nm.py --results60 <dir>/results.npz --resultsL <dir>/results.npz \
      [--kind geo3|ms] [--out docs/figures] [--stem fig_hologram_50nm]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import holography as H  # noqa: E402
from reflection_holo import plotstyle as ps  # noqa: E402

REFL = "(0,0,8)"
CORE = 4915.49  # A, both configs
TRACE = 4561.94  # A, slip step of the 60 degree case
CARRIER = (0.0, 0.2)  # cycles/A, as in the configs
DOSE, SEED = 400, 20260930
ROWS, DX = 40, 0.5  # image rows for display (geometric mode: identical rows)


def wave(path, kind):
    r = np.load(path)
    k = f"{REFL}_{kind}_" if f"{REFL}_{kind}_phase" in r.files else f"{REFL}_geo3_"
    src = "multislice" if k.endswith("_ms_") else "geometric"
    return r["y"], r[k + "amp"] * np.exp(1j * r[k + "phase"]), src


def wave2d(rows_path, results_path):
    """2D dark-field wave over the image rows used for the reconstruction, with the reference-strip
    ramp of the 1D reconstruction removed and the amplitude normalised to the reference strip."""
    import json

    d = np.load(rows_path)
    x, y, psi = d["x"], d["y"], d["psi_df"]
    m = json.loads((Path(results_path).parent / "summary.json").read_text())["reflections"][REFL]["multislice"]
    lo, hi = m["image_rows_exit_height_A"]
    roi = (x >= lo - 1e-6) & (x <= hi + 1e-6)
    w = psi[roi]
    r = np.load(results_path)
    raw = np.unwrap(np.angle(w.mean(axis=0)))
    c = np.polyfit(y, raw - r[f"{REFL}_ms_phase"], 1)
    w = w * np.exp(-1j * np.polyval(c, y))[None, :]
    ref = (y > 25) & (y < 1229 - 25)
    w = w / np.mean(np.abs(w.mean(axis=0)[ref]))
    return x[roi], y, w


def hsv_wave(w):
    from matplotlib.colors import hsv_to_rgb

    hue = np.mod(np.angle(w), 2 * np.pi) / (2 * np.pi)
    val = np.clip(np.abs(w) / 1.1, 0, 1)
    return hsv_to_rgb(np.stack([hue, np.full_like(hue, 0.85), val], -1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results60", required=True)
    ap.add_argument("--resultsL", required=True)
    ap.add_argument("--kind", default="geo3")
    ap.add_argument("--rows60", default=None,
                    help="rows_008.npz of the 60 degree multislice run: use its 2D wave (image rows = exit height)")
    ap.add_argument("--out", default="docs/figures")
    ap.add_argument("--stem", default="fig_hologram_50nm")
    args = ap.parse_args()
    plt = ps.apply()

    cases = [("60° dislocation, g·b = 4", args.results60, TRACE, "slip step"),
             ("Lomer dislocation, g·b = 0", args.resultsL, CORE, "core")]
    fig, axes = plt.subplots(3, 2, figsize=(ps.DOUBLE, 3.9), gridspec_kw={"height_ratios": [1.3, 1, 1]})
    W = 2000.0
    for j, (title, path, crop_c, crop_lab) in enumerate(cases):
        y, w, src = wave(path, args.kind)
        dy = y[1] - y[0]
        w2 = None
        if j == 0 and args.rows60:
            xr, _, w2 = wave2d(args.rows60, path)
            src = "multislice"
        # row 1: hologram crop (object under empty reference), Poisson noise
        sel = np.abs(y - crop_c) < 50.0
        if w2 is not None:
            obj = w2[:, sel]
            dxr, h = xr[1] - xr[0], (xr[-1] - xr[0]) / 10
        else:
            obj = np.broadcast_to(w[sel], (ROWS, sel.sum()))
            dxr, h = DX, ROWS * DX / 10
        I = H.form_hologram(np.ascontiguousarray(obj), dxr, dy, CARRIER, 1.0, dose=DOSE,
                            rng=np.random.default_rng(SEED))
        I0 = H.form_hologram(np.ones_like(obj), dxr, dy, CARRIER, 1.0, dose=DOSE, rng=np.random.default_rng(SEED + 1))
        yy = (y[sel] - CORE) / 10
        ax = axes[0, j]
        vmax = np.percentile(I, 99.5)
        ax.imshow(I, extent=[yy[0], yy[-1], 0, h], origin="lower", aspect="auto", cmap="gray", vmin=0, vmax=vmax)
        ax.imshow(I0, extent=[yy[0], yy[-1], h, 2 * h], origin="lower", aspect="auto", cmap="gray", vmin=0,
                  vmax=vmax)
        ax.axhline(h, color=ps.C2, lw=0.8)
        ax.set_ylim(0, 2 * h)
        ax.set_yticks([h / 2, 1.5 * h])
        ax.set_yticklabels(["object", "reference"], fontsize=6)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel(f"y from the core (nm); crop at the {crop_lab}")
        ax.set_title(title, fontsize=7, loc="left")
        ps.panel_label(ax, "abcdef"[j], x=-0.12)

        # rows 2 and 3: complex wave and interferogram over +-200 nm
        win = np.abs(y - CORE) < W
        if w2 is not None:
            ext = [-W / 10, W / 10, xr[0] / 10, xr[-1] / 10]
            ww = w2[:, win][:, ::4]  # display sampling 0.5 A
        else:
            ext = [-W / 10, W / 10, 0, ROWS * DX / 10]
            ww = np.broadcast_to(w[win][::4], (ROWS, win[win].size // 4 + (win.sum() % 4 > 0)))
        rgb = hsv_wave(ww)
        axes[1, j].imshow(rgb, extent=ext, origin="lower", aspect="auto", interpolation="antialiased")
        ifg = np.cos(np.angle(ww))
        axes[2, j].imshow(ifg, extent=ext, origin="lower", aspect="auto", cmap="gray", vmin=-1, vmax=1)
        for i, letter in ((1, "cd"[j]), (2, "ef"[j])):
            a = axes[i, j]
            a.axvline(0, color="white", lw=0.4, ls=(0, (1, 1)))
            if j == 0:
                a.axvline((TRACE - CORE) / 10, color="white", lw=0.4, ls=(0, (3, 1.5)))
            ps.panel_label(a, letter, x=-0.12)
        rl = "Exit height (nm)" if w2 is not None else "Image row"
        axes[1, j].set_ylabel(rl, fontsize=6)
        axes[2, j].set_ylabel(rl, fontsize=6)
        if w2 is None:
            for i in (1, 2):
                axes[i, j].set_yticks([])
        axes[2, j].set_xlabel("y from the core (nm)")
        axes[1, j].set_xticklabels([])
        axes[2, j].text(0.99, 0.92, f"{src} model", transform=axes[2, j].transAxes, ha="right", va="top",
                        fontsize=5.5, color=ps.C2)

    # colour wheel for the complex-wave rows
    cax = fig.add_axes([0.905, 0.4, 0.09, 0.14])
    g = np.linspace(-1, 1, 201)
    X, Y = np.meshgrid(g, g)
    disc = hsv_wave(np.hypot(X, Y) * 1.1 * np.exp(1j * np.arctan2(Y, X)))
    disc = np.concatenate([disc, (np.hypot(X, Y) <= 1)[..., None].astype(float)], -1)  # RGBA, round
    cax.imshow(disc, extent=[-1, 1, -1, 1], origin="lower")
    for ang, lab in ((0, "0"), (np.pi / 2, "π/2"), (np.pi, "π"), (-np.pi / 2, "−π/2")):
        cax.text(1.32 * np.cos(ang), 1.32 * np.sin(ang), lab, ha="center", va="center", fontsize=5)
    cax.set_xlim(-1.6, 1.6)
    cax.set_ylim(-2.6, 1.6)
    cax.set_aspect("equal")
    cax.axis("off")
    cax.text(0, -1.9, "phase (hue)\namplitude (brightness)", ha="center", va="top", fontsize=5)
    fig.subplots_adjust(left=0.08, right=0.9, top=0.94, bottom=0.1, hspace=0.55, wspace=0.18)
    ps.save(fig, Path(args.out) / args.stem)
    plt.close(fig)
    print("wrote", Path(args.out) / f"{args.stem}.pdf", "and .png")


if __name__ == "__main__":
    main()
