#!/usr/bin/env python3
"""Three-section Si(001) sample: dark-field wave (multislice and geometry mode), off-axis
hologram and reconstructed phase and amplitude, for each requested specular reflection.

Usage:
  python scripts/run_sections.py --config configs/si001_three_sections_cpu.yaml [--backend cupy]

Outputs in outputs/<config name>/reconstruction/: recon_<hkl>.png per reflection, overview.png,
results.npz, manifest.json. The multislice kernel is smoke-tested only (docs/08).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import geometry as geo  # noqa: E402
from reflection_holo import holography as H  # noqa: E402
from reflection_holo.defects.dislocation import from_config  # noqa: E402
from reflection_holo.forward import geometric as gm  # noqa: E402
from reflection_holo.forward import multislice as ms  # noqa: E402
from reflection_holo.provenance import Config, write_manifest  # noqa: E402
from reflection_holo.structure.sections import build_sections  # noqa: E402

FRAME = geo.SI001_FRAME
SEC_COLORS = ["#4C78A8", "#54A24B", "#B279A2"]


def circ_mean(p, w=None):
    return float(np.angle(np.average(np.exp(1j * p), weights=w)))


def hkl_name(hkl):
    return "(" + ",".join(str(int(v)) for v in hkl) + ")"


def strip_windows(s, core_y, core_half=110.0, edge=25.0):
    """Interior windows of each strip, excluding step edges and the dislocation field."""
    wins = []
    for k in range(len(s.heights)):
        lo, hi = s.boundaries[k] + edge, s.boundaries[k + 1] - edge
        wins.append((lo, hi))
    return wins


def geometric_wave(s, cond, y, pens, n_layers, q_ap, dy):
    """Complex specular wave along y from the column model, same displacement as the atoms, plus
    the terrace heights; mapped to deformed coordinates and band-limited by the aperture."""
    d = s.info["layer_spacing_A"]
    depths = d * np.arange(n_layers)
    sec = np.clip(np.searchsorted(s.boundaries, y, side="right") - 1, 0, len(s.heights) - 1)
    h = s.heights[sec]
    r = np.stack(np.broadcast_arrays(-depths[:, None], y[None, :], 0.0 * y[None, :]), -1)
    u = s.u_func(r)
    u[..., 0] += h[None, :]
    G, qi, qe = gm.specular_vectors(cond)
    out = {}
    for p in pens:
        ph, am = gm.column_phase(u, depths, G, qi, qe, float(p))
        f = gm.to_deformed_coordinates(am * np.exp(1j * ph), y, u[0, :, 1], s.Ly)
        out[p] = gm.band_limit_1d(f, dy, q_ap)
    return out, u[0, :, 0]


def process(psi2d, s, y, dy, dx, carrier, mask_r, dose, seed):
    """Hologram -> reconstruction -> unwrapped, ramp-corrected phase map and amplitude map."""
    amp_ref = float(np.mean(np.abs(psi2d[:, (y > s.boundaries[0] + 25) & (y < s.boundaries[1] - 25)])))
    empty = np.full_like(psi2d, amp_ref)
    res = {}
    for tag, dz in (("noiseless", None), ("noisy", dose)):
        rng = np.random.default_rng(seed)
        I = H.form_hologram(psi2d, dx, dy, carrier, amp_ref, dose=dz, rng=rng)
        I0 = H.form_hologram(empty, dx, dy, carrier, amp_ref, dose=dz, rng=np.random.default_rng(seed + 1))
        w, q = H.reconstruct(I, I0, dx, dy, mask_r)
        prof = np.mean(w, axis=0)  # complex average over the image rows (along the beam)
        ph = np.unwrap(np.angle(prof))
        ref = (y > s.boundaries[0] + 25) & (y < s.boundaries[1] - 25)
        c = np.polyfit(y[ref], ph[ref], 1)  # ramp fit on the reference strip only
        ph_c = ph - np.polyval(c, y)
        wmap = w * np.exp(-1j * np.polyval(c, y))[None, :]
        res[tag] = dict(I=I, w=wmap, phase=ph_c, amp=np.abs(prof) / np.mean(np.abs(prof[ref])),
                        carrier=q, ramp=c.tolist())
    return res


def metrics(ph, y, s, core_y):
    wins = strip_windows(s, core_y)
    lvl = []
    for lo, hi in wins[:2]:  # strip 3 has no field-free interior: its signal is the profile itself
        sel = (y > lo) & (y < hi)
        lvl.append(float(np.median(ph[sel])))
    core = np.abs(y - core_y) < 60
    j = np.argmax(np.abs(ph[core] - lvl[0]))
    peak = float(ph[core][j] - lvl[0])
    half = np.abs(ph - lvl[0]) > abs(peak) / 2
    fwhm = float(np.sum(half & (np.abs(y - core_y) < 100)) * (y[1] - y[0]))
    s3 = (y > s.boundaries[2] + 8) & (y < s.boundaries[3] - 8)
    flank = s3 & (np.abs(y - core_y) > 55)
    local = float(np.mean(ph[np.abs(y - core_y) < 1.5]) - np.mean(ph[flank]))  # no path through strip 2
    return {"dislocation_rel_strip3_flanks_rad": local, "step_21_rad": lvl[1] - lvl[0], "step_21_wrapped_rad": float(np.angle(np.exp(1j * (lvl[1] - lvl[0])))),
            "dislocation_peak_rad": peak, "dislocation_fwhm_A": fwhm}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--backend", default="numpy", choices=["numpy", "cupy"])
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--only", default=None, help='run the multislice only for this reflection, e.g. "(0,0,12)"')
    args = ap.parse_args()
    cfg = Config(args.config)
    out = Path(args.out) / cfg.data["name"] / "reconstruction"
    out.mkdir(parents=True, exist_ok=True)
    xp = ms.get_xp(args.backend)

    E = float(cfg.get("beam.energy_keV"))
    a = float(cfg.get("crystal.a_A"))
    V0_geo = float(cfg.get("crystal.V0_V"))
    entries = cfg.get("defects.dislocations")
    defects = from_config(entries, float(cfg.get("defects.nu")), a, FRAME, None, 0)
    s = build_sections(FRAME, a, cfg.get("sample.periods_per_section"), cfg.get("sample.raise_layers"),
                       float(cfg.get("sample.depth_A")), defects, seam_y=cfg.get("sample.seam_y_A"))
    core_y = float(entries[0]["position_yz_A"][0])

    nx, ny = int(cfg.get("multislice.nx")), int(cfg.get("multislice.ny"))
    grid = ms.Grid(nx=nx, ny=ny, dx=float(cfg.get("multislice.dx_A")), dy=s.Ly / ny, x0=float(cfg.get("multislice.x0_A")))
    lam, sigma = geo.wavelength_A(E), geo.interaction_constant(E)
    V0_ms = ms.mean_inner_potential(8 / a**3)
    q_ap = float(cfg.get("multislice.aperture_radius_per_A"))
    abs_top, abs_w, abs_V = cfg.get("multislice.bulk_absorber_top_width_Vmax")
    xc, Hh, edge = cfg.get("multislice.illumination_center_height_edge_A")
    vac_x, vac_e = cfg.get("multislice.vacuum_mask_x_edge_A")
    pens = [float(p) for p in cfg.get("geometric.penetration_A")]
    n_layers = int(cfg.get("geometric.n_layers"))
    carrier = tuple(cfg.get("holography.carrier_per_A"))
    mask_r = float(cfg.get("holography.mask_radius_per_A"))
    dose = float(cfg.get("holography.dose_counts_per_pixel"))
    seed = int(cfg.get("holography.noise_seed"))
    y = grid.y

    t0 = time.time()
    V, dz = ms.slice_potentials(s.positions, s.Lz, int(cfg.get("multislice.slices_per_period")), grid,
                                float(cfg.get("multislice.debye_waller_B_A2")),
                                float(cfg.get("multislice.absorption_ratio")), xp=xp)
    band = xp.asarray(grid.band_mask())
    absorber = ms.absorber_profile(grid, abs_top, abs_w, abs_V)
    T = [ms.transmission(v, sigma, absorber, dz, band, xp=xp) for v in V]
    print(f"{len(s.positions)} atoms, potentials in {time.time() - t0:.1f} s; V0 of potential {V0_ms:.2f} V")

    summary = {"n_atoms": len(s.positions), "V0_potential_V": V0_ms, "V0_geometric_V": V0_geo, "reflections": {}}
    store = {}
    for hkl in [tuple(h) for h in cfg.get("reflections_to_run")] + [(0, 0, 4)]:
        name = hkl_name(hkl)
        c_ms = geo.SpecularCondition(E, V0_ms, a, hkl)
        c_geo = geo.SpecularCondition(E, V0_geo, a, hkl)
        c_geo_run = c_ms
        if hkl in [tuple(h) for h in cfg.get("reflections_to_run")]:
            off = float(cfg.get("multislice.operating_offset_mrad")[name])
            c_geo_run = geo.SpecularAtAngle(E, V0_ms, a, hkl, c_ms.theta_ext + off * 1e-3)
        geo_w, ux_s = geometric_wave(s, c_geo_run, y, pens, n_layers, q_ap, grid.dy)
        entry = {"theta_int_mrad": c_ms.theta_int * 1e3, "theta_ext_mrad_V0potential": c_ms.theta_ext * 1e3,
                 "theta_ext_mrad_V0_12V": c_geo.theta_ext * 1e3, "wrap_period_A": 2 * np.pi / c_ms.q_ext,
                 "step_phase_geometric_V0potential_rad": float(np.angle(np.exp(-1j * c_ms.q_ext * s.heights[1]))),
                 "step_phase_geometric_V0_12V_rad": float(np.angle(np.exp(-1j * c_geo.q_ext * s.heights[1])))}
        # geometric mode through the same hologram chain (image rows: 40 identical rows)
        g_rows = {p: np.broadcast_to(w, (40, ny)) for p, w in geo_w.items()}
        rec_geo = {p: process(np.ascontiguousarray(g), s, y, grid.dy, 0.5, carrier, mask_r, dose, seed)
                   for p, g in g_rows.items()}
        entry["geometric"] = {str(p): metrics(r["noiseless"]["phase"], y, s, core_y) for p, r in rec_geo.items()}
        rec_ms = None
        if hkl in [tuple(h) for h in cfg.get("reflections_to_run")] and args.only in (None, name):
            off = float(cfg.get("multislice.operating_offset_mrad")[name])
            theta = c_ms.theta_ext + off * 1e-3
            grid.assert_angle_in_band(theta, lam)
            n_steps = int(np.ceil(2 * xc / np.tan(theta) / dz))
            psi0 = ms.illumination(grid, theta, lam, xc, Hh, edge)
            t1 = time.time()
            psi = ms.to_numpy(ms.run(psi0, T, ms.propagator(grid, dz, lam, xp=xp), n_steps, xp=xp))
            psi_df, spec = ms.dark_field(psi, grid, theta, lam, q_ap, vac_x, vac_e)
            # effective reflected angle: intensity centroid of the specular spot inside the aperture
            QX = grid.qx[:, None] * np.ones((1, ny))
            QY = np.ones((nx, 1)) * grid.qy[None, :]
            inap = (QX - np.sin(theta) / lam) ** 2 + QY**2 < q_ap**2
            q_eff = float(np.sum(QX * spec * inap) / np.sum(spec * inap))
            th_eff = float(np.arcsin(q_eff * lam))
            c_eff = geo.SpecularAtAngle(E, V0_ms, a, hkl, th_eff)
            # image rows: where every strip's reflected band is at > 50 % of its own maximum (a raised
            # strip's band exits 2h higher, so the usable rows are the intersection)
            roi = np.ones(nx, bool)
            for hk in np.unique(s.heights):  # one representative strip per terrace height
                k = int(np.argmax(s.heights == hk))
                cols = (y > s.boundaries[k] + 25) & (y < s.boundaries[k + 1] - 25)
                rI = np.mean(np.abs(psi_df[:, cols]) ** 2, axis=1)
                roi &= rI > 0.5 * rI.max()
            # per-row diagnostic: step phase and strip intensities along the exit height
            c1 = (y > s.boundaries[0] + 25) & (y < s.boundaries[1] - 25)
            c2 = (y > s.boundaries[1] + 25) & (y < s.boundaries[2] - 25)
            np.savez_compressed(out / f"rows_{name.strip('()').replace(',', '')}.npz", x=grid.x,
                                psi_df=psi_df.astype(np.complex64), y=y,
                                I1=np.mean(np.abs(psi_df[:, c1]) ** 2, 1), I2=np.mean(np.abs(psi_df[:, c2]) ** 2, 1),
                                dphi21=np.angle(np.mean(psi_df[:, c2], 1) / np.mean(psi_df[:, c1], 1)))
            if roi.sum() < 20:
                raise RuntimeError(f"only {roi.sum()} image rows are illuminated on every strip; enlarge the sheet beam")
            rec_ms = process(psi_df[roi], s, y, grid.dy, grid.dx, carrier, mask_r, dose, seed)
            R = float(np.sum(np.abs(psi_df) ** 2) / np.sum(np.abs(psi0) ** 2))
            entry["multislice"] = {"operating_offset_mrad": off, "theta_ext_nominal_mrad": theta * 1e3,
                                   "theta_ext_effective_mrad": th_eff * 1e3,
                                   "step_phase_predicted_at_effective_angle_rad":
                                       float(np.angle(np.exp(-1j * c_eff.q_ext * s.heights[1]))),
                                   "n_slices": n_steps, "runtime_s": time.time() - t1, "specular_fraction": R,
                                   "image_rows_exit_height_A": [float(grid.x[roi].min()), float(grid.x[roi].max())],
                                   "noiseless": metrics(rec_ms["noiseless"]["phase"], y, s, core_y),
                                   "noisy": metrics(rec_ms["noisy"]["phase"], y, s, core_y),
                                   "carrier_found": rec_ms["noiseless"]["carrier"]}
            print(f"{name}: theta_ext {theta*1e3:.2f} mrad, {n_steps} slices, {entry['multislice']['runtime_s']:.0f} s, "
                  f"R {R:.3f}; step {entry['multislice']['noiseless']['step_21_wrapped_rad']:+.3f} rad "
                  f"(-q_ext h at the effective angle {th_eff*1e3:.2f} mrad: "
                  f"{entry['multislice']['step_phase_predicted_at_effective_angle_rad']:+.3f}); "
                  f"dislocation {entry['multislice']['noiseless']['dislocation_peak_rad']:+.2f} rad")
            store[name] = dict(rec_ms=rec_ms, x_roi=grid.x[roi], rec_geo=rec_geo, cond=c_ms)
            plot_reflection(out, name, s, y, grid, store[name], core_y, pens, entry, carrier)
        else:
            store[name] = dict(rec_ms=None, rec_geo=rec_geo, cond=c_ms)
        summary["reflections"][name] = entry

    plot_overview(out, s, y, store, pens, core_y)
    np.savez_compressed(out / "results.npz", y=y, **{
        f"{k}_{t}_{q}": v[t]["noiseless"][q] for k, v in
        {n: {"ms": d["rec_ms"], **{f"geo{p:g}": d["rec_geo"][p] for p in pens}} for n, d in store.items()}.items()
        for t in v if v[t] is not None for q in ("phase", "amp")})
    write_manifest(out, cfg, {"mode": "sections_reconstruction", "summary": summary,
                              "status": "SMOKE TEST: multislice not validated (docs/08)"}, backend=args.backend)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps(summary, indent=2, default=float))


def _strips(ax, s):
    for k in range(len(s.heights)):
        ax.axvspan(s.boundaries[k], s.boundaries[k + 1], color=SEC_COLORS[k], alpha=0.08, lw=0)


def plot_reflection(out, name, s, y, grid, d, core_y, pens, entry, carrier):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = d["rec_ms"]
    xr = d["x_roi"]
    fig, ax = plt.subplots(3, 2, figsize=(16, 11), gridspec_kw={"height_ratios": [1, 1, 1.25]})
    ext = [y[0], y[-1], xr[0], xr[-1]]
    zoom = (y > core_y - 30) & (y < core_y + 30)
    ax[0, 0].imshow(r["noisy"]["I"][:, zoom], aspect="auto", origin="lower", cmap="gray",
                    extent=[y[zoom][0], y[zoom][-1], xr[0], xr[-1]])
    ax[0, 0].set(title=f"{name} hologram (with Poisson noise), zoom over the dislocation; fringes 1/{carrier[1]:g} = "
                 f"{1/carrier[1]:.0f} A", xlabel="y (A)", ylabel="image row = exit height (A)")
    ph_map = np.angle(r["noiseless"]["w"])
    im = ax[0, 1].imshow(ph_map, aspect="auto", origin="lower", cmap="twilight", extent=ext, vmin=-np.pi, vmax=np.pi)
    fig.colorbar(im, ax=ax[0, 1], label="rad")
    ax[0, 1].set(title="reconstructed phase (wrapped), noiseless, reference strip ramp removed", xlabel="y (A)",
                 ylabel="image row (A)")
    am_map = np.abs(r["noiseless"]["w"])
    im = ax[1, 1].imshow(am_map / np.median(am_map), aspect="auto", origin="lower", cmap="gray", extent=ext,
                         vmin=0.3, vmax=1.5)
    fig.colorbar(im, ax=ax[1, 1], label="relative amplitude")
    ax[1, 1].set(title="reconstructed amplitude, noiseless", xlabel="y (A)", ylabel="image row (A)")
    im = ax[1, 0].imshow(np.angle(r["noisy"]["w"]), aspect="auto", origin="lower", cmap="twilight", extent=ext,
                         vmin=-np.pi, vmax=np.pi)
    ax[1, 0].set(title=f"reconstructed phase (wrapped) with Poisson noise", xlabel="y (A)", ylabel="image row (A)")
    for k, key in enumerate(("phase", "amp")):
        a_ = ax[2, k]
        _strips(a_, s)
        a_.plot(y, r["noisy"][key], color="0.7", lw=0.8, label="multislice, noisy hologram")
        a_.plot(y, r["noiseless"][key], "k", lw=2, label="multislice")
        for p in pens:
            a_.plot(y, d["rec_geo"][p]["noiseless"][key], lw=1.2, ls="--", label=f"geometry mode, Lambda={p:g} A")
        a_.axvline(core_y, color="r", lw=0.6, ls=":")
        a_.set(xlabel="y (A)   strips: 1 reference | 2 raised 5.43 A | 3 dislocation (dotted: core)",
               ylabel="phase (rad), unwrapped, strip 1 = 0" if key == "phase" else "amplitude / strip 1")
        a_.legend(fontsize=8, loc="lower left" if key == "phase" else "lower left")
    m = entry["multislice"]["noiseless"]
    gmet = entry["geometric"][str(pens[0])]
    ax[2, 0].set_title(f"step 2-1: {m['step_21_wrapped_rad']:+.2f} rad (geometry mode {gmet['step_21_wrapped_rad']:+.2f}); "
                       f"dislocation {m['dislocation_peak_rad']:+.1f} rad, FWHM {m['dislocation_fwhm_A']:.0f} A")
    ax[2, 1].set_title("amplitude profile (average over image rows)")
    fig.suptitle(f"Si(001) three strips, specular {name}, 200 keV, theta_ext {entry['multislice']['theta_ext_nominal_mrad']:.2f} mrad "
                 f"(rocking-curve maximum), wrap period {geo.wavelength_A(200) / (2 * np.sin(entry['multislice']['theta_ext_nominal_mrad'] * 1e-3)):.3f} A. "
                 f"SMOKE TEST (kernel not validated)")
    fig.tight_layout()
    fig.savefig(out / f"recon_{name.strip('()').replace(',', '')}.png", dpi=105)
    plt.close(fig)


def plot_overview(out, s, y, store, pens, core_y):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 1, figsize=(14, 8.5), sharex=True)
    for k, key in enumerate(("phase", "amp")):
        _strips(ax[k], s)
        for i, (name, d) in enumerate(store.items()):
            col = f"C{i}"
            if d["rec_ms"] is not None:
                ax[k].plot(y, d["rec_ms"]["noiseless"][key], color=col, lw=2, label=f"{name} multislice")
            ax[k].plot(y, d["rec_geo"][pens[0]]["noiseless"][key], color=col, lw=1, ls="--",
                       label=f"{name} geometry mode (Lambda={pens[0]:g} A)")
        ax[k].axvline(core_y, color="r", lw=0.6, ls=":")
    ax[0].set(ylabel="reconstructed phase (rad), strip 1 = 0", title="Reconstructed phase and amplitude across the three strips, by reflection")
    ax[1].set(ylabel="reconstructed amplitude / strip 1", xlabel="y (A): 1 reference | 2 raised 5.43 A | 3 buried Lomer dislocation")
    ax[0].legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out / "overview.png", dpi=105)
    plt.close(fig)


if __name__ == "__main__":
    main()
