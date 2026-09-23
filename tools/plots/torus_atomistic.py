#!/usr/bin/env python3
"""Figures of the half-torus smoke test T1: the atomistic supercell and the exit waves.

Usage: venv/bin/python tools/plots/torus_atomistic.py --runs <dir containing ms_trench, ms_ridge,
       [ms_flat]> --out <figure dir>

Reads the files written by scripts/torus/run_torus_multislice.py: ms_<kind>/structure_<kind>.npz
(atoms, feature sites, cell, metadata; axes and units asserted) and the exit waves
ms_<kind>/outputs/exit_waves/torus_<kind>_r0000.npz through multislice.load_exit_wave (pixel sizes, axes,
plane and 200 keV asserted from the file). Writes supercell_<kind>.png and exitwave_<kind>.png.
Frame: x = outward normal, y = in-plane transverse, z = beam azimuth; exp(+i k.r), numpy FFT sign.
DEMO (ASSUMPTION B20, B30, B32, B33, B34) and UNVALIDATED (finite-cell build-up, no absorption,
report M2 section 10): not comparable to experiment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reflection_holo.forward.multislice import PLANE_TEXT, load_exit_wave, select_beam
from reflection_holo.geometry.frames import surface_frame
from reflection_holo.structure.features import height_map_grid, top_layer_height_map
from reflection_holo.structure.shapes import HalfTorus

INK, MUTED = "#1f1f1e", "#6b6a64"
BASE, FEAT, REMOVED = "#8c8c86", "#2a78d6", "#eb6834"
UNVAL = "UNVALIDATED (finite-cell build-up, no absorption B30; M2 report section 10)"
MASKED = "#9a9a9a"
APERTURE_PER_A = 0.2          # specular-beam selection radius (1/A), as in M2 report section 10.3
AXES = ["x: outward normal [001]", "y: z cross x", "z: beam azimuth"]


def load_structure(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as f:
        if str(f["schema"]) != "T1 torus structure/1":
            raise ValueError(f"{path}: unexpected schema {f['schema']}")
        if [str(a) for a in f["axes"]] != AXES or str(f["units"]) != "angstrom":
            raise ValueError(f"{path}: axes/units {list(f['axes'])} {f['units']} not as expected")
        d = {k: f[k] for k in ("positions_A", "feature_sites_A", "cell_A",
                               "structure_to_cell_shift_A")}
        d["metadata"] = json.loads(str(f["metadata_json"]))
        d["cell_feature"] = json.loads(str(f["cell_feature_json"]))
    md = d["metadata"]
    fr = surface_frame(tuple(md["surface"]["hkl"]), tuple(md["azimuth"]["uvw"]))
    for k, row in (("x_hat_crystal", fr.x_hat), ("y_hat_crystal", fr.y_hat),
                   ("z_hat_crystal", fr.z_hat)):
        if not np.allclose(md["frame"][k], row, atol=1e-12):
            raise ValueError(f"{path}: frame row {k} differs from surface_frame")
    d["frame"] = fr
    f = md["feature"]
    d["feature"] = HalfTorus(center_y_A=f["center_y_A"], center_z_A=f["center_z_A"],
                             major_radius_A=f["major_radius_A"],
                             minor_radius_A=f["minor_radius_A"], kind=f["kind"],
                             label=f["label"], source=f["source"])
    return d


def _clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def supercell_figure(d: dict, out: Path) -> Path:
    md, feat, fr = d["metadata"], d["feature"], d["frame"]
    a = md["lattice"]["a_A"]
    q = a / 4.0
    l_s = md["feature"]["flat_top_layer_index"]
    x_s = md["feature"]["x_surface_A"]
    L = np.diag(d["cell_A"])
    pos, fs = d["positions_A"], d["feature_sites_A"]
    ys, zs = height_map_grid(feat, L[1], L[2], 0.25)
    N = int(np.ceil(feat.minor_radius_A / q))
    h = top_layer_height_map(pos, fr, a, l_s, ys, zs, L[1], L[2], (l_s - N - 2, l_s + N + 1))

    fig = plt.figure(figsize=(15, 13.5))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.45, 0.8, 0.8], hspace=0.42, wspace=0.22)
    kind = feat.kind
    fig.suptitle(f"Si(001) [100], half-torus {kind.upper()} (R = {feat.major_radius_A:g} A, "
                 f"r = {feat.minor_radius_A:g} A; {feat.label}, {feat.source}); "
                 f"{len(pos):,} atoms, {len(fs):,} {'removed' if kind == 'trench' else 'added'}",
                 fontsize=11, color=INK, x=0.02, ha="left")

    ax = fig.add_subplot(gs[0, 0])
    im = ax.imshow(h.T, origin="lower", cmap="Blues", interpolation="nearest",
                   extent=[ys[0] - 0.125, ys[-1] + 0.125, zs[0] - 0.125, zs[-1] + 0.125])
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("top-layer height relative to the flat surface (A)")
    ax.set_xlabel("y (A)")
    ax.set_ylabel("z along the beam (A)")
    ax.set_aspect("equal")
    ax.set_title("(a) top view: top-layer height map from the built atoms\n(nearest lattice site "
                 "of each layer, grid 0.25 A)", fontsize=10, loc="left", color=INK)
    ax.annotate("", xy=(ys[0] + 6, zs[-1] - 4), xytext=(ys[0] + 6, zs[-1] - 24),
                arrowprops=dict(arrowstyle="->", color=INK))
    ax.text(ys[0] + 8, zs[-1] - 16, "beam", fontsize=8, color=INK)

    # (d) radial profile: built top-layer height vs distance from the ring centre line
    ax = fig.add_subplot(gs[0, 1])
    Y, Zg = np.meshgrid(ys, zs, indexing="ij")
    dr = np.hypot(Y - feat.center_y_A, Zg - feat.center_z_A) - feat.major_radius_A
    m = np.abs(dr) < feat.minor_radius_A + 6
    rng = np.random.default_rng(0)                                  # subsample for plotting only
    sel = np.nonzero(m.ravel())[0]
    sel = rng.choice(sel, size=min(len(sel), 40000), replace=False)
    ax.scatter(dr.ravel()[sel], h.ravel()[sel], s=1.5, color=FEAT, alpha=0.25, lw=0,
               rasterized=True, label="built top layer (grid points, all azimuths)")
    rr = np.linspace(-feat.minor_radius_A - 6, feat.minor_radius_A + 6, 2001)
    yy = feat.center_y_A + feat.major_radius_A + rr
    zz = np.full_like(rr, feat.center_z_A)
    ax.plot(rr, feat.continuous_height_A(yy, zz), color=INK, lw=1.4,
            label="continuous half circle (shapes.continuous_height_A)")
    ax.plot(rr, feat.layer_height_A(yy, zz, layer_spacing_A=q), color=REMOVED, lw=1.2,
            ls=(0, (4, 2)), label="ideal a/4 terraces (shapes.layer_height_A)")
    ax.set_aspect("equal")
    ax.set_xlabel("rho - R, distance from the ring centre line (A)")
    ax.set_ylabel("height relative to the flat surface (A)")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.28), frameon=False)
    hm = md["checks"]["height_map"]
    ax.set_title(f"(d) built profile vs the continuous half circle (1:1)\nassertion (e): equal "
                 f"beyond {hm['exclusion_distance_A']:.2f} A of the ring boundary; "
                 f"{100 * hm['fraction_disagree_near_boundary']:.0f} % disagree within it",
                 fontsize=10, loc="left", color=INK)
    _clean(ax)

    # (b), (c) cross-sections through the ring centre (two atomic planes)
    for row, (axis, other, cen, lab) in enumerate(((1, 2, feat.center_z_A, "y"),
                                                   (2, 1, feat.center_y_A, "z"))):
        ax = fig.add_subplot(gs[1 + row, :])
        n0 = np.floor(cen / q)
        lo, hi = n0 * q - 1e-6, (n0 + 1) * q + 1e-6
        s_at = (pos[:, other] >= lo) & (pos[:, other] <= hi)
        s_fs = (fs[:, other] >= lo) & (fs[:, other] <= hi)
        c0 = feat.center_y_A if axis == 1 else feat.center_z_A
        span = feat.major_radius_A + feat.minor_radius_A + 12
        w = (np.abs(pos[:, axis] - c0) < span) & s_at
        base = w & (np.rint(pos[:, 0] / q) <= l_s)
        ax.scatter(pos[base, axis], pos[base, 0] - x_s, s=7, color=BASE, lw=0, rasterized=True,
                   label="slab atoms")
        wf = s_fs & (np.abs(fs[:, axis] - c0) < span)
        if kind == "ridge":
            ax.scatter(fs[wf, axis], fs[wf, 0] - x_s, s=9, color=FEAT, lw=0,
                       label="added ridge atoms (same lattice)")
        else:
            ax.scatter(fs[wf, axis], fs[wf, 0] - x_s, s=9, facecolors="none",
                       edgecolors=REMOVED, lw=0.6, label="removed sites")
        t = np.linspace(c0 - span, c0 + span, 4001)
        yy, zz = (t, np.full_like(t, cen)) if axis == 1 else (np.full_like(t, cen), t)
        ax.plot(t, feat.continuous_height_A(yy, zz), color=INK, lw=1.0,
                label="continuous half circle")
        ax.plot(t, feat.layer_height_A(yy, zz, layer_spacing_A=q), color=REMOVED, lw=0.9,
                ls=(0, (4, 2)), label="ideal a/4 top layer")
        ax.set_xlim(c0 - span, c0 + span)
        ax.set_ylim(-feat.minor_radius_A - 9, feat.minor_radius_A + 4)
        ax.set_xlabel(f"{lab} (A)" + (" along the beam" if lab == "z" else ""))
        ax.set_ylabel("x - x_surface (A)")
        other_lab = "z" if axis == 1 else "y"
        ax.set_title(f"({'b' if row == 0 else 'c'}) cross-section along {lab} through the ring "
                     f"centre: atoms with {other_lab} in [{lo:.2f}, {hi:.2f}] A (two atomic "
                     f"planes); axes not to scale (1:1 in panel d)",
                     fontsize=10, loc="left", color=INK)
        ax.legend(fontsize=8, ncol=5, loc="lower center" if kind == "ridge" else "upper center",
                  frameon=False)
        _clean(ax)
    p = out / f"supercell_{kind}.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def _same_grid(a, b):
    for k in ("dx_A", "dy_A", "x0_A", "y0_A", "z_A", "energy_keV", "theta_in_ext_rad"):
        if not np.isclose(getattr(a, k), getattr(b, k), rtol=0, atol=1e-12):
            raise ValueError(f"feature and flat exit waves differ in {k}")
    if a.psi.shape != b.psi.shape:
        raise ValueError("feature and flat exit waves differ in shape")


def exitwave_figure(kind: str, ew, flat_ew, cell_feature: dict, out: Path) -> Path:
    psi = ew.psi.astype(np.complex128)
    nx, ny = psi.shape
    x = ew.x0_A + np.arange(nx) * ew.dx_A
    y = ew.y0_A + np.arange(ny) * ew.dy_A
    xs = float(ew.metadata["cell"]["surface_x_A"])
    lam = float(ew.metadata["beam"]["wavelength_A"])
    th_out = float(ew.metadata["theta_out_ext_rad"])
    fc = np.sin(th_out) / lam
    xr = (x - xs >= -15.0) & (x - xs <= 35.0)
    ext = [y[0], y[-1], x[xr][0] - xs, x[xr][-1] - xs]
    fig, axs = plt.subplots(2, 4, figsize=(24, 10.5), gridspec_kw=dict(wspace=0.5, hspace=0.38))
    fig.suptitle(f"Exit plane z = {ew.z_A:.1f} A, half-torus {kind}; 200 keV, theta_ext = "
                 f"{ew.theta_in_ext_rad * 1e3:.4f} mrad (B32), stored {ew.psi.dtype}; {UNVAL}",
                 fontsize=10, color=INK, x=0.01, ha="left")

    def img(ax, data, cmap, title, label, vmin=None, vmax=None):
        cmap = plt.get_cmap(cmap).copy()
        cmap.set_bad(MASKED)                   # masked pixels: mid grey, not a twilight colour
        im = ax.imshow(data[xr], origin="lower", aspect="auto", cmap=cmap, extent=ext,
                       interpolation="nearest", vmin=vmin, vmax=vmax)
        cb = fig.colorbar(im, ax=ax, shrink=0.9)
        cb.set_label(label)
        ax.set_xlabel("y (A)")
        ax.set_ylabel("x - x_surface (A)")
        ax.set_title(title, fontsize=10, loc="left", color=INK)
        for yb in cell_feature["y_range_A"] if cell_feature else []:
            ax.axvline(yb, color="w", lw=0.6, ls=":")
        return im

    def not_run(ax):
        ax.text(0.5, 0.5, "flat-surface reference: NOT RUN", ha="center", va="center",
                transform=ax.transAxes, color=INK)
        ax.set_axis_off()

    amp_all = np.abs(psi)
    img(axs[0, 0], amp_all, "viridis", "(a) |psi| at the exit plane", "|psi| (incident = 1)")
    img(axs[0, 1], np.angle(psi), "twilight", "(b) arg psi (carrier fringes along x included)",
        "phase (rad)", -np.pi, np.pi)
    F = np.fft.fftshift(np.fft.fft2(psi))
    fx = np.fft.fftshift(np.fft.fftfreq(nx, ew.dx_A))
    fy = np.fft.fftshift(np.fft.fftfreq(ny, ew.dy_A))
    I = np.abs(F) ** 2
    ax = axs[0, 2]
    wx = np.abs(fx) <= 1.6
    wy = np.abs(fy) <= 1.0
    im = ax.imshow(np.log10(I[np.ix_(wx, wy)] / I.max() + 1e-12), origin="lower", aspect="auto",
                   cmap="magma", extent=[fy[wy][0], fy[wy][-1], fx[wx][0], fx[wx][-1]],
                   vmin=-9, vmax=0, interpolation="nearest")
    cb = fig.colorbar(im, ax=ax, shrink=0.9)
    cb.set_label("log10 |FFT psi|^2 / max")
    ax.add_patch(plt.Circle((0, fc), APERTURE_PER_A, fill=False, color="#1baf7a", lw=1.2))
    ax.annotate("specular (0,0,8)\n+sin(theta)/lambda", (0, fc), (0.2, fc + 0.55),
                color="#1baf7a", fontsize=8, arrowprops=dict(arrowstyle="->", color="#1baf7a"))
    ax.plot([0], [-fc], "+", color="w", ms=9)
    ax.text(-0.9, -fc - 0.2, "incident, -sin(theta)/lambda (+)", color="w", fontsize=8)
    ax.set_xlabel("f_y (1/A)")
    ax.set_ylabel("f_x (1/A)")
    ax.set_title("(c) Fourier-space intensity; circle = specular selection", fontsize=10,
                 loc="left", color=INK)
    spec = select_beam(ew, fx_centre_per_A=fc, fy_centre_per_A=0.0, radius_per_A=APERTURE_PER_A)
    demod = spec * np.exp(-2j * np.pi * fc * x)[:, None]
    amp = np.abs(spec)
    img(axs[1, 0], amp, "viridis",
        f"(e) specular beam |psi_s| (aperture {APERTURE_PER_A} 1/A)", "|psi_s|")
    ph = np.where(amp > 0.05 * amp[xr].max(), np.angle(demod), np.nan)
    img(axs[1, 1], ph, "twilight", "(f) arg psi_s exp(-2 pi i f_c x)\n(grey: |psi_s| < 5 % of max)",
        "phase (rad)", -np.pi, np.pi)
    if flat_ew is None:
        not_run(axs[0, 3])
        not_run(axs[1, 2])
        not_run(axs[1, 3])
    else:
        _same_grid(ew, flat_ew)
        pf = flat_ew.psi.astype(np.complex128)
        m_raw = (amp_all > 0.05 * amp_all[xr].max()) & (np.abs(pf) > 0.05 * np.abs(pf)[xr].max())
        img(axs[0, 3], np.where(m_raw, np.angle(psi * np.conj(pf)), np.nan), "twilight",
            "(d) arg(psi psi_flat*): exit phase minus the flat\nreference (grey: |psi| or "
            "|psi_flat| < 5 % of max)",
            "phase difference (rad)", -np.pi, np.pi)
        spec_f = select_beam(flat_ew, fx_centre_per_A=fc, fy_centre_per_A=0.0,
                             radius_per_A=APERTURE_PER_A)
        af = np.abs(spec_f)
        m_s = (amp > 0.05 * amp[xr].max()) & (af > 0.05 * af[xr].max())
        img(axs[1, 2], np.where(m_s, np.angle(spec * np.conj(spec_f)), np.nan), "twilight",
            "(g) specular phase minus flat reference\narg(psi_s psi_s,flat*) (grey: < 5 % of max)",
            "phase difference (rad)", -np.pi, np.pi)
        img(axs[1, 3], np.where(m_s, amp / np.where(af > 0, af, np.nan), np.nan), "viridis",
            "(h) specular amplitude ratio |psi_s| / |psi_s,flat|", "ratio", 0.0, 2.0)
    for a in axs.ravel():
        _clean(a)
    p = out / f"exitwave_{kind}.png"
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    flat_path = args.runs / "ms_flat" / "outputs" / "exit_waves" / "torus_flat_r0000.npz"
    flat_ew = load_exit_wave(flat_path, expected_plane=PLANE_TEXT) if flat_path.exists() else None
    for kind in ("trench", "ridge"):
        run = args.runs / f"ms_{kind}"
        d = load_structure(run / f"structure_{kind}.npz")
        print(supercell_figure(d, args.out))
        ew_path = run / "outputs" / "exit_waves" / f"torus_{kind}_r0000.npz"
        if ew_path.exists():
            ew = load_exit_wave(ew_path, expected_plane=PLANE_TEXT)
            print(exitwave_figure(kind, ew, flat_ew, d["cell_feature"], args.out))
        else:
            print(f"{ew_path}: missing, exit-wave figure NOT made")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
