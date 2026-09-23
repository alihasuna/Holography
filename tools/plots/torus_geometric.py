#!/usr/bin/env python3
"""Figure of a half-torus pipeline run with the geometric engine (agent T2).

Usage: venv/bin/python tools/plots/torus_geometric.py --run-dir <pipeline output dir> --out <png>

Reads arrays.npz and summary.json of ``python -m reflection_holo.pipeline run`` on
configs/demo_smoke_torus_{trench,ridge}.yaml; every array's axes and plane are read from
summary.json["arrays"] and asserted. DEMO data: not comparable to experiment. Panels: object hologram
(detector), reconstructed wrapped phase (cyclic map), height map with masks and the unwrapped phase of
every reliable region (diverging maps centred on 0), the reason-code and trace-status masks on the
detector and the shadowed / blocked-view map on the surface, and profile cuts against the built
profile (HalfTorus.continuous_height_A and the a/4-quantised layer_height_A).
Frame: x = outward normal, y = in-plane transverse, z = beam azimuth; image axes u (along the beam,
downstream down) and y.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap, TwoSlopeNorm

from reflection_holo.structure.shapes import HalfTorus

DET_AXES = ["along_beam", "perpendicular"]
REASON_COLOURS = ["#2a78d6", "#1f1f1e", "#b9b8b0", "#eb6834", "#c2185b", "#7b3fa0", "#f2c14e",
                  "#1baf7a"]
STATUS_COLOURS = ["#2a78d6", "#6b6a64", "#1f1f1e", "#b9b8b0", "#f2e6c9"]
SURF_COLOURS = ["#e8eef7", "#1f1f1e", "#eb6834", "#7b3fa0"]


def _load(run_dir: pathlib.Path):
    s = json.loads((run_dir / "summary.json").read_text())
    a = np.load(run_dir / "arrays.npz")
    idx = s["arrays"]
    for k in ("hologram_object_counts", "phase_wrapped", "height_A", "unwrapped_phase",
              "reason_code", "trace_status", "trace_source_z_A"):
        assert idx[k]["axes"] == DET_AXES, (k, idx[k]["axes"])
        assert idx[k]["plane"] == idx["hologram_object_counts"]["plane"], k
        assert list(a[k].shape) == idx[k]["shape"], k
    assert idx["surface_mask_code"]["axes"] == ["y", "z"]
    assert "not comparable to experiment" in s["purpose"]
    return s, a


def _extent(u, y):
    du, dy = u[1] - u[0], y[1] - y[0]
    return [y[0] - dy / 2, y[-1] + dy / 2, u[-1] + du / 2, u[0] - du / 2]


def _img(ax, data, u, y, cols, title, **kw):
    im = ax.imshow(data[:, cols], extent=_extent(u, y[cols]), aspect="auto",
                   interpolation="nearest", **kw)
    ax.set_title(title, fontsize=8.5)
    ax.set_xlabel("perpendicular y (A)", fontsize=8)
    ax.set_ylabel("along beam u (A, image plane)", fontsize=8)
    ax.tick_params(labelsize=7)
    return im


def figure(run_dir: pathlib.Path, out: pathlib.Path) -> None:
    s, a = _load(run_dir)
    sh = s["feature"]["shape"]
    torus = HalfTorus(sh["center_y_A"], sh["center_z_A"], sh["major_radius_A"],
                      sh["minor_radius_A"], sh["sub_kind"], sh["label"], sh["source"])
    layer = s["feature"]["layer_spacing_A"]
    u, y = a["detector_u_A"], a["detector_y_A"]
    allc = np.arange(y.size)
    yc, R, r = torus.center_y_A, torus.major_radius_A, torus.minor_radius_A
    zoom = np.nonzero(np.abs(y - (yc + R)) <= 3 * r)[0]
    q = s["quantification"]
    fig = plt.figure(figsize=(17, 21))
    gs = fig.add_gridspec(6, 3, width_ratios=[2.2, 1, 0.9], hspace=0.5, wspace=0.28, top=0.955,
                          bottom=0.035, left=0.05, right=0.98)
    # 1. hologram
    ax = fig.add_subplot(gs[0, 0])
    im = _img(ax, a["hologram_object_counts"], u, y, allc, "object hologram (counts), whole ROI",
              cmap="gray")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax = fig.add_subplot(gs[0, 1])
    im = _img(ax, a["hologram_object_counts"], u, y, zoom,
              f"object hologram, ring side y_c + R +- {3 * r:g} A (fringes 2 A)", cmap="gray")
    fig.colorbar(im, ax=ax, shrink=0.8)
    # 2. wrapped phase (cyclic)
    for col, cols, t in ((0, allc, "whole ROI"), (1, zoom, "ring side")):
        ax = fig.add_subplot(gs[1, col])
        im = _img(ax, a["phase_wrapped"], u, y, cols, f"reconstructed wrapped phase (rad), {t}",
                  cmap="twilight", vmin=-np.pi, vmax=np.pi)
        fig.colorbar(im, ax=ax, shrink=0.8)
    # 3. height map and unwrapped phase of every reliable region (diverging, centred on 0)
    h = a["height_A"]
    hm = float(np.nanmax(np.abs(h))) if np.isfinite(h).any() else 1.0
    cm = matplotlib.colormaps["RdBu_r"].copy()
    cm.set_bad("#d9d8d2")
    ax = fig.add_subplot(gs[2, 0])
    im = _img(ax, h, u, y, allc, "HEIGHT MAP h (A): measurable pixels only (grey = masked, reason "
              "codes below)", cmap=cm, norm=TwoSlopeNorm(0.0, -hm, hm))
    fig.colorbar(im, ax=ax, shrink=0.8)
    ref = q["height_map"].get("reference_phase_rad", 0.0)
    un = a["unwrapped_phase"] - ref
    um = float(np.nanmax(np.abs(un[:, zoom]))) if np.isfinite(un[:, zoom]).any() else 1.0
    ax = fig.add_subplot(gs[2, 1])
    im = _img(ax, un, u, y, zoom, "unwrapped phase - reference (rad), every reliable region "
              "(isolated regions: own 2 pi offset)", cmap=cm, norm=TwoSlopeNorm(0.0, -um, um))
    fig.colorbar(im, ax=ax, shrink=0.8)
    # 4. masks: reason codes and trace status on the detector
    rc = q["height_map"]["reason_codes"]
    names = sorted(rc, key=rc.get)
    cmr = ListedColormap(REASON_COLOURS[:len(names)])
    nr = BoundaryNorm(np.arange(len(names) + 1) - 0.5, len(names))
    for col, cols in ((0, allc), (1, zoom)):
        ax = fig.add_subplot(gs[3, col])
        im = _img(ax, a["reason_code"], u, y, cols, "reliability map (reason code per pixel)",
                  cmap=cmr, norm=nr)
        cb = fig.colorbar(im, ax=ax, shrink=0.8, ticks=np.arange(len(names)))
        cb.ax.set_yticklabels(names, fontsize=6.5)
    st = s["arrays"]["trace_status"]["units"]
    status_names = ["lit", "illumination_shadow", "riser", "below_surface", "outside_field_of_view"]
    cms = ListedColormap(STATUS_COLOURS)
    ns = BoundaryNorm(np.arange(6) - 0.5, 5)
    ax = fig.add_subplot(gs[4, 1])
    im = _img(ax, a["trace_status"], u, y, zoom, "ray-trace status of each pixel (ring side)",
              cmap=cms, norm=ns)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, ticks=np.arange(5))
    cb.ax.set_yticklabels(status_names, fontsize=6.5)
    assert all(n in st for n in status_names)
    # surface-plane shadow / blocked map
    ax = fig.add_subplot(gs[4, 0])
    ys, zs, sc = a["surface_mask_y_A"], a["surface_mask_z_A"], a["surface_mask_code"]
    im = ax.imshow(sc.T, extent=[ys[0], ys[-1], zs[-1], zs[0]], aspect="auto",
                   interpolation="nearest", cmap=ListedColormap(SURF_COLOURS),
                   norm=BoundaryNorm(np.arange(5) - 0.5, 4))
    th = np.linspace(0, 2 * np.pi, 721)
    for rad in (R - r, R + r):
        ax.plot(yc + rad * np.cos(th), torus.center_z_A + rad * np.sin(th), color="#f2c14e", lw=0.6)
    ax.set_title("surface plane: shadowed (black), blocked view (orange), both (purple); ring "
                 "footprint outlined (beam travels downward)", fontsize=8.5)
    ax.set_xlabel("y (A)", fontsize=8)
    ax.set_ylabel("z along the beam (A)", fontsize=8)
    ax.tick_params(labelsize=7)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, ticks=range(4))
    cb.ax.set_yticklabels(["usable", "shadowed", "blocked", "both"], fontsize=6.5)
    # 5. profile cuts
    yy = np.linspace(y[0], y[-1], 20001)
    zc = torus.center_z_A
    built_c = torus.continuous_height_A(yy, zc)
    built_l = torus.layer_height_A(yy, zc, layer_spacing_A=layer)
    cy = {k[6:]: a[k] for k in a.files if k.startswith("cut_y_")}
    cz = {k[6:]: a[k] for k in a.files if k.startswith("cut_z_")}
    stats = q["profile_cuts"]
    for col, (lo, hi, t) in enumerate(((y[0], y[-1], "whole ROI"),
                                       (yc + R - 3 * r, yc + R + 3 * r, "ring side y_c + R"))):
        ax = fig.add_subplot(gs[5, col])
        sel = (yy >= lo) & (yy <= hi)
        ax.plot(yy[sel], built_l[sel], color="#1f1f1e", lw=1.0, label="built: layer_height_A (a/4)")
        ax.plot(yy[sel], built_c[sel], color="#6b6a64", lw=0.8, ls="--",
                label="built: continuous_height_A")
        m = cy["measurable"].astype(bool) & (cy["y_A"] >= lo) & (cy["y_A"] <= hi)
        ax.errorbar(cy["y_A"][m], cy["h_meas_A"][m], yerr=3 * cy["sigma_h_A"][m], fmt=".",
                    ms=2, color="#2a78d6", elinewidth=0.5, label="measured h (+-3 sigma)")
        d = np.isfinite(cy["h_data_only_A"]) & (cy["y_A"] >= lo) & (cy["y_A"] <= hi) & ~m
        ax.plot(cy["y_A"][d], cy["h_data_only_A"][d], "x", ms=3, color="#eb6834",
                label="data-only unwrapping, masked (NOT a height)")
        ax.set_title(f"profile: y cut at z_c (source z nearest z_c), {t}", fontsize=8.5)
        ax.set_xlabel("y (A)", fontsize=8)
        ax.set_ylabel("height (A)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6.5, loc="best")
    ax = fig.add_subplot(gs[5, 2])
    ycol = float(cz["y_A"])
    zz = np.linspace(0.0, s["feature"]["height_field"]["z_end_A"], 40001)
    ax.plot(zz, torus.layer_height_A(ycol, zz, layer_spacing_A=layer), color="#1f1f1e", lw=1.0,
            label="built: layer_height_A (a/4)")
    ax.plot(zz, torus.continuous_height_A(ycol, zz), color="#6b6a64", lw=0.8, ls="--",
            label="built: continuous_height_A")
    m = cz["measurable"].astype(bool)
    ax.errorbar(cz["z_src_A"][m], cz["h_meas_A"][m], yerr=3 * cz["sigma_h_A"][m], fmt=".", ms=3,
                color="#2a78d6", elinewidth=0.5, label="measured h at the traced source z")
    lit = np.isfinite(cz["z_src_A"]) & ~m
    ax.plot(cz["z_src_A"][lit], np.zeros(lit.sum()) - 0.5, "|", color="#eb6834", ms=6,
            label="lit sources, not measurable")
    ax.set_title("profile: z cut at y_c (along the beam; front and back arcs)", fontsize=8.5)
    ax.set_xlabel("surface z along the beam (A)", fontsize=8)
    ax.set_ylabel("height (A)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, loc="lower left")
    # text panel
    ax = fig.add_subplot(gs[0:5, 2])
    ax.axis("off")
    m = q["measurable"]
    iso = m.get("isolated_reliable_on_footprint", {})
    res = q["resolution"]
    lines = [
        f"{s['run_name']}  ({s['purpose']})",
        f"engine: {s['engine']['label']}",
        f"half torus {sh['sub_kind']}: R = {R:g} A, r = {r:g} A",
        f"theta = {s['glancing_angle']['value_mrad']:.4f} mrad, 200 keV, wrap period "
        f"{q['height_map']['wrap_period_A']:.4f} A",
        "",
        f"detector px: {m['detector_px']}",
        f"lit: {m['lit_px']}  (footprint {m['footprint_source_px']})",
        f"measurable: {m['measurable_px']} ({100 * m['measurable_fraction_of_detector']:.1f} %)",
        f"measurable on the ring footprint: {m['measurable_footprint_px']}",
        f"isolated reliable footprint px: {iso.get('n_px', 0)}",
    ]
    if iso.get("rms_wrapped_residual_A") is not None:
        lines.append(f"  {iso['n_px_half_resolution_inside']} of them >= res/2 inside: phase mod")
        lines.append(f"  2 pi vs built rms {iso['rms_wrapped_residual_A']:.4f} A")
    fmt = (lambda v: "-" if v is None else f"{v:.4f}")
    for name, c in q["profile_cuts"].items():
        lines += ["", f"{name}:",
                  f"  measurable {c['n_measurable']} of {c['n_px']} px,",
                  f"  on the footprint {c['n_measurable_on_footprint']} of {c['n_on_footprint']}",
                  f"  rms vs layer {fmt(c['rms_vs_layer_A'])} A,",
                  f"  vs continuous {fmt(c['rms_vs_continuous_A'])} A"]
    lines += ["", "reason counts on the footprint:"]
    lines += [f"  {k}: {v}" for k, v in m["reason_counts_on_footprint"].items() if v]
    lines += ["", "no-step control: " + ("PASS" if q["no_step_control"].get("passed") else
                                        "NOT PASSED"),
              f"  delta {q['no_step_control'].get('delta_rad', float('nan')):+.2e} rad, tol "
              f"{q['no_step_control'].get('tolerance_rad', float('nan')):.2e} rad",
              "", "resolution:"]
    lines += ["  " + res["summary"]]
    lines += ["", f"a/4 step: {res['a4_step']['wraps']:.3f} wraps, apparent "
                  f"{res['a4_step']['apparent_height_A']:+.3f} A",
              f"aperture passes |dh/dy| < {res['aperture_slope_acceptance']['across_beam_dh_dy']:.3f},",
              f"  |dh/dz| < {res['aperture_slope_acceptance']['along_beam_dh_dz']:.4f}",
              f"parallax of the extreme layer: {res['extreme_layer']['parallax_image_A']:+.1f} A "
              f"({res['extreme_layer']['parallax_rows']:+.0f} rows)"]
    wrapped = []
    for ln in lines:
        indent = " " * (len(ln) - len(ln.lstrip()))
        wrapped += textwrap.wrap(ln, width=46, subsequent_indent=indent + "  ") or [""]
    ax.text(0.0, 1.0, "\n".join(wrapped), va="top", ha="left", fontsize=7.5, family="monospace",
            transform=ax.transAxes)
    fig.suptitle(f"{s['run_name']}: half-torus {sh['sub_kind']} on Si(001), geometric model (no "
                 f"dynamical amplitude, B4 scope applies); demo, not comparable to experiment",
                 fontsize=11)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=85)
    plt.close(fig)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--run-dir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    figure(pathlib.Path(args.run_dir), pathlib.Path(args.out))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
