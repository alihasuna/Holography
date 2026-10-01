#!/usr/bin/env python3
"""Nature-style figure of the simulated hologram and its reconstructed phase and amplitude.

One double-column figure per reflection, from the dark-field waves saved by
scripts/run_sections.py (rows_<hkl>.npz), using the same holography code as the analysis:
  a  hologram (recorded intensity), full field
  b  reconstructed phase (unwrapped, relative to the reference strip)
  c  reconstructed amplitude (relative to the reference strip)
  d  hologram zoom over the dislocation, empty (reference-only) hologram above for comparison
  e  phase profile, multislice and geometry mode
  f  amplitude profile, multislice and geometry mode
Captions: docs/figures/CAPTIONS.md.

Usage:
  python scripts/figures_holography.py --config configs/si001_three_sections_cpu.yaml \
      --data <folder with rows_*.npz> [--geo <results.npz>] --out docs/figures
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import geometry as geo  # noqa: E402
from reflection_holo import holography as H  # noqa: E402
from reflection_holo import plotstyle as ps  # noqa: E402
from reflection_holo.forward import multislice as ms  # noqa: E402
from reflection_holo.provenance import Config  # noqa: E402


def sample_layout(cfg):
    a = float(cfg.get("crystal.a_A"))
    periods = np.array(cfg.get("sample.periods_per_section"))
    bounds = np.concatenate([[0.0], np.cumsum(periods) * a / np.sqrt(2)])
    heights = np.array(cfg.get("sample.raise_layers")) * a / 4
    core = cfg.get("defects.dislocations")[0]
    return bounds, heights, float(core["position_yz_A"][0]), float(core["depth_A"]), a


def reconstruct(cfg, d, bounds):
    x, y, psi = d["x"], d["y"], d["psi_df"]
    dy, dx = y[1] - y[0], x[1] - x[0]
    roi = np.ones(len(x), bool)
    for k in (0, 1):  # image rows where both terrace heights are fully illuminated
        cols = (y > bounds[k] + 25) & (y < bounds[k + 1] - 25)
        rI = np.mean(np.abs(psi[:, cols]) ** 2, axis=1)
        roi &= rI > 0.5 * rI.max()
    P = psi[roi]
    ref = (y > bounds[0] + 25) & (y < bounds[1] - 25)
    amp_ref = float(np.mean(np.abs(P[:, ref])))
    carrier = tuple(cfg.get("holography.carrier_per_A"))
    dose = float(cfg.get("holography.dose_counts_per_pixel"))
    seed = int(cfg.get("holography.noise_seed"))
    I = H.form_hologram(P, dx, dy, carrier, amp_ref, dose=dose, rng=np.random.default_rng(seed))
    I0 = H.form_hologram(np.full_like(P, amp_ref), dx, dy, carrier, amp_ref, dose=dose,
                         rng=np.random.default_rng(seed + 1))
    w, q = H.reconstruct(I, I0, dx, dy, float(cfg.get("holography.mask_radius_per_A")))
    prof = np.unwrap(np.angle(np.mean(w, axis=0)))  # row average fixes the 2 pi branches
    c = np.polyfit(y[ref], prof[ref], 1)  # linear ramp fitted on the reference strip only
    prof = prof - np.polyval(c, y)
    wr = w * np.exp(-1j * np.polyval(c, y))[None, :]
    phase = prof[None, :] + np.angle(wr * np.exp(-1j * prof)[None, :])
    amp = np.abs(wr) / np.mean(np.abs(wr[:, ref]))
    return dict(x=x[roi], y=y, I=I / np.mean(I0), I0=I0 / np.mean(I0), phase=phase, amp=amp,
                prof_phase=prof, prof_amp=np.mean(amp, axis=0), carrier=q, dose=dose)


def measure(y, ph, bounds, core):
    lvl = [np.median(ph[(y > bounds[k] + 25) & (y < bounds[k + 1] - 25)]) for k in (0, 1)]
    corev = np.mean(ph[np.abs(y - core) < 1.5])
    half = (np.abs(ph - lvl[0]) > abs(corev - lvl[0]) / 2) & (np.abs(y - core) < 100)
    return dict(step=lvl[1] - lvl[0], peak=corev - lvl[0], fwhm=half.sum() * (y[1] - y[0]))


def figure(hkl, r, bounds, heights, core, depth, theta, geo_prof, stem):
    plt = ps.apply()
    import matplotlib.patheffects as pe

    y_nm = r["y"] / 10
    t = (r["x"] - r["x"].min()) / 10
    ext = [y_nm[0], y_nm[-1], 0, t[-1]]
    m = measure(r["y"], r["prof_phase"], bounds, core)

    fig = plt.figure(figsize=(ps.DOUBLE, 5.2))
    top = fig.add_gridspec(3, 2, width_ratios=[1, 0.015], left=0.045, right=0.93, top=0.90, bottom=0.40,
                           hspace=0.28, wspace=0.015)
    bot = fig.add_gridspec(1, 3, left=0.085, right=0.985, top=0.30, bottom=0.075, wspace=0.36)

    def image(row, data, cmap, vmin, vmax, letter, cb_label, bar=False):
        ax = fig.add_subplot(top[row, 0])
        im = ax.imshow(data, extent=ext, origin="lower", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_yticks([])
        for s_ in ax.spines.values():
            s_.set_visible(True)
            s_.set_linewidth(0.5)
        for b in bounds[1:-1]:
            ax.axvline(b / 10, color="white", lw=0.6, ls=(0, (3, 2)), alpha=0.9)
        ax.plot([core / 10], [ext[3] * 0.06], marker="^", ms=4, color=ps.ACCENT, mec="white", mew=0.4)
        ax.set_ylabel("Along beam", fontsize=6, labelpad=2)
        ps.panel_label(ax, letter, x=-0.025)
        if bar:  # one scale bar: a, b and c share the same scale
            x0 = ext[0] + 0.012 * (ext[1] - ext[0])
            ax.add_patch(plt.Rectangle((x0 - 0.3, ext[3] * 0.08), 5.6, ext[3] * 0.42, color="black", alpha=0.55, lw=0))
            ax.plot([x0, x0 + 5], [ext[3] * 0.16] * 2, color="white", lw=1.4, solid_capstyle="butt")
            ax.text(x0 + 2.5, ext[3] * 0.24, "5 nm", color="white", ha="center", va="bottom", fontsize=6)
        cax = fig.add_subplot(top[row, 1])
        cb = fig.colorbar(im, cax=cax)
        cb.set_label(cb_label, fontsize=6, labelpad=2)
        cb.ax.tick_params(labelsize=5.5, width=0.4, length=2)
        cb.outline.set_linewidth(0.4)
        return ax

    # a hologram
    vmax = np.percentile(r["I"], 99.5)
    axa = image(0, r["I"], "gray", 0, vmax, "a", "Intensity\n(rel.)", bar=True)
    names = ["1  Reference", f"2  Raised {heights[1]/10:.2f} nm (4 layers)", f"3  Dislocation {depth/10:.1f} nm deep"]
    for k in range(3):
        axa.text((bounds[k] + bounds[k + 1]) / 20, ext[3] * 1.06, names[k], ha="center", va="bottom", fontsize=6.5)
    sep = "" if max(abs(v) for v in hkl) < 10 else ","  # (008) but (0,0,12)
    axa.text(1.0, 1.36, f"Si(001)   ({sep.join(str(v) for v in hkl)}) reflection   200 keV   "
             f"{theta*1e3:.1f} mrad", transform=axa.transAxes, ha="right", va="bottom", fontsize=6.5, color=ps.INK2)
    lo, hi = core - 30, core + 30
    axa.add_patch(plt.Rectangle((lo / 10, 0.02 * ext[3]), (hi - lo) / 10, 0.96 * ext[3], fill=False, ec="#eda100",
                                lw=0.8))
    axa.text(hi / 10 + 0.2, ext[3] * 0.85, "d", color="#eda100", fontsize=6.5, fontweight="bold",
             path_effects=[pe.withStroke(linewidth=1.2, foreground="black")])

    # b phase, c amplitude
    lim = float(np.ceil(np.max(np.abs(r["phase"]))))
    image(1, r["phase"], ps.phase_cmap(), -lim, lim, "b", "Phase (rad)")
    image(2, r["amp"], "gray", 0, 1.4, "c", "Amplitude\n(rel.)")

    # d zoom: reference fringes above, object hologram below
    axd = fig.add_subplot(bot[0, 0])
    sel = (r["y"] >= lo) & (r["y"] <= hi)
    h_ref = 0.6 * ext[3]
    axd.imshow(r["I"][:, sel], extent=[lo / 10, hi / 10, 0, ext[3]], origin="lower", aspect="auto", cmap="gray",
               vmin=0, vmax=vmax)
    axd.imshow(r["I0"][: max(2, int(len(r["I0"]) * 0.6)), sel], extent=[lo / 10, hi / 10, ext[3], ext[3] + h_ref],
               origin="lower", aspect="auto", cmap="gray", vmin=0, vmax=vmax)
    axd.axhline(ext[3], color="white", lw=1.0)
    axd.set_ylim(0, ext[3] + h_ref)
    axd.set_yticks([ext[3] / 2, ext[3] + h_ref / 2])
    axd.set_yticklabels(["Object", "Reference"], fontsize=6)
    axd.tick_params(axis="y", length=0)
    axd.plot([core / 10], [ext[3] * 0.08], marker="^", ms=4, color=ps.ACCENT, mec="white", mew=0.4)
    axd.set_xlabel("Position across beam (nm)")
    for s_ in axd.spines.values():
        s_.set_visible(True)
        s_.set_linewidth(0.5)
    ps.panel_label(axd, "d", x=-0.27)

    # e, f profiles
    for ax, key, j, ylab, letter in ((fig.add_subplot(bot[0, 1]), "prof_phase", 0, "Phase (rad)", "e"),
                                     (fig.add_subplot(bot[0, 2]), "prof_amp", 1, "Amplitude (rel.)", "f")):
        for b in bounds[1:-1]:
            ax.axvline(b / 10, color=ps.GRID, lw=0.6, ls=(0, (3, 2)))
        ax.axhline(0 if j == 0 else 1, color=ps.GRID, lw=0.5)
        ax.plot(y_nm, r[key], color=ps.C1, lw=1.0, label="Multislice")
        if geo_prof is not None:
            ax.plot(y_nm, geo_prof[j], color=ps.C2, lw=0.8, ls=(0, (3, 1.5)), label="Geometric model")
        ax.set_xlim(ext[:2])
        ax.set_xlabel("Position across beam (nm)")
        ax.set_ylabel(ylab)
        yl = ax.get_ylim()
        for k in range(3):
            ax.text((bounds[k] + bounds[k + 1]) / 20, yl[1], str(k + 1), ha="center", va="bottom", fontsize=6,
                    color=ps.INK2)
        ps.panel_label(ax, letter, x=-0.2)
        if j == 0:
            ax.text((bounds[1] + bounds[2]) / 20, m["step"] + 0.12 * (yl[1] - yl[0]), f"{m['step']:+.1f} rad",
                    fontsize=6, ha="center", color=ps.INK2)
            ax.text(core / 10 + 1.2, m["peak"], f"{m['peak']:+.1f} rad", fontsize=6, ha="left", va="center",
                    color=ps.INK2)
            ax.legend(loc="lower left", handlelength=1.6)
    ps.save(fig, stem)
    plt.close(fig)
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", required=True, help="folder with rows_<hkl>.npz from run_sections.py")
    ap.add_argument("--geo", default=None, help="results.npz of run_sections.py (geometry-mode profiles)")
    ap.add_argument("--out", default="docs/figures")
    args = ap.parse_args()
    cfg = Config(args.config)
    bounds, heights, core, depth, a = sample_layout(cfg)
    V0 = ms.mean_inner_potential(8 / a**3)
    geo_npz = np.load(args.geo) if args.geo else None
    for f in sorted(Path(args.data).glob("rows_*.npz")):
        hkl = (0, 0, int(f.stem.split("_")[1][2:]))
        name = "(" + ",".join(str(v) for v in hkl) + ")"
        theta = (geo.SpecularCondition(200, V0, a, hkl).theta_ext
                 + float(cfg.get("multislice.operating_offset_mrad")[name]) * 1e-3)
        r = reconstruct(cfg, np.load(f), bounds)
        gp = None
        if geo_npz is not None and f"{name}_geo3_phase" in geo_npz.files:
            gp = (geo_npz[f"{name}_geo3_phase"], geo_npz[f"{name}_geo3_amp"])
        stem = Path(args.out) / f"fig_hologram_si001_{''.join(str(v) for v in hkl)}"
        m = figure(hkl, r, bounds, heights, core, depth, theta, gp, stem)
        print(f"{name}: {stem}.png/.pdf  step {m['step']:+.2f} rad, dislocation {m['peak']:+.2f} rad, "
              f"FWHM {m['fwhm']:.0f} A, foreshortening 1/sin(theta) = {1/np.sin(theta):.0f}")


if __name__ == "__main__":
    main()
