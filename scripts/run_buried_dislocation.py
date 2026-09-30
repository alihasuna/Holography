#!/usr/bin/env python3
"""Buried-dislocation smoke tests: geometric-phase mode and grazing-incidence multislice mode.

Usage:
  python scripts/run_buried_dislocation.py geometric  --config configs/smoke/buried_dislocation_cpu.yaml
  python scripts/run_buried_dislocation.py multislice --config configs/smoke/buried_dislocation_cpu.yaml \
         [--backend cupy]

Outputs go to outputs/<config name>/<mode>/ (git-ignored): results .npz, figure .png, manifest.json.
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
from reflection_holo.crystal import build_slab, lattice_period  # noqa: E402
from reflection_holo.defects.dislocation import from_config  # noqa: E402
from reflection_holo.forward import geometric as gm  # noqa: E402
from reflection_holo.forward import multislice as ms  # noqa: E402
from reflection_holo.provenance import Config, write_manifest  # noqa: E402

FRAME = geo.SI111_FRAME


def build_defects(cfg: Config, a_A: float, Ly: float | None):
    """Dislocations from the config, with periodic images along y when the cell is periodic."""
    n_img = int(cfg.get("defects.periodic_images_y")) if Ly is not None else 0
    return from_config(cfg.get("defects.dislocations"), float(cfg.get("defects.nu")), a_A, FRAME, Ly, n_img)


def geometric_profile(defects, cond, y, z, penetrations, n_layers):
    """Phase map phi[P, Ny, Nz] for each penetration depth; also the surface normal displacement."""
    d = cond.d_A
    depths = d * np.arange(n_layers)
    Y, Z = np.meshgrid(y, z, indexing="ij")
    r = np.stack([np.broadcast_to(-depths[:, None, None], (n_layers,) + Y.shape),
                  np.broadcast_to(Y, (n_layers,) + Y.shape),
                  np.broadcast_to(Z, (n_layers,) + Y.shape)], axis=-1)
    u = defects.displacement(r)
    G, qi, qe = gm.specular_vectors(cond)
    phases, amps = [], []
    for lam_p in penetrations:
        p, a = gm.column_phase(u, depths, G, qi, qe, float(lam_p))
        phases.append(p)
        amps.append(a)
    return np.array(phases), np.array(amps), u[0, ..., 0], u[0, ..., 1]


def unwrap_rel(phi, axis=-1):
    p = np.unwrap(phi, axis=axis)
    return p - np.angle(np.mean(np.exp(1j * p), axis=axis, keepdims=True))


# ---------------------------------------------------------------------------------------------
def run_geometric(cfg: Config, out: Path):
    E = float(cfg.get("beam.energy_keV"))
    a = float(cfg.get("crystal.a_A"))
    V0 = float(cfg.get("crystal.V0_V"))
    cond = geo.SpecularCondition(E, V0, a, tuple(cfg.get("reflection.hkl")))
    y0, y1, ny = cfg.get("geometric.y_window_A")
    z0, z1, nz = cfg.get("geometric.z_window_A")
    pens = [float(p) for p in cfg.get("geometric.penetration_A")]
    n_layers = int(cfg.get("geometric.n_layers"))
    Ly = cfg.get("geometric.periodic_Ly_A")
    defects = build_defects(cfg, a, Ly)
    y = np.linspace(y0, y1, int(ny))
    z = np.linspace(z0, z1, int(nz))
    t0 = time.time()
    phi, amp, ux_s, _ = geometric_profile(defects, cond, y, z, pens, n_layers)
    dt = time.time() - t0
    # foreshortened image coordinate along the beam
    z_img = z * np.sin(cond.theta_ext)
    np.savez_compressed(out / "geometric.npz", y=y, z=z, z_image=z_img, penetration_A=pens,
                        phase=phi.astype(np.float32), amplitude=amp.astype(np.float32),
                        surface_ux=ux_s.astype(np.float32))
    b_loc = [d.b_local.tolist() for d in defects.items[:1]]
    summary = {
        "theta_int_mrad": cond.theta_int * 1e3, "theta_ext_mrad": cond.theta_ext * 1e3,
        "q_ext_rad_per_A": cond.q_ext, "G_rad_per_A": cond.G,
        "h_2pi_A": 2 * np.pi / cond.q_ext,
        "b_local_first_dislocation_A": b_loc,
        "surface_ux_range_A": [float(ux_s.min()), float(ux_s.max())],
        "phase_peak_to_peak_along_y_at_central_z_rad": {
            str(p): float(np.ptp(np.unwrap(ph[:, len(z) // 2]))) for p, ph in zip(pens, phi)},
        "phase_peak_to_peak_along_z_at_central_y_rad": {
            str(p): float(np.ptp(np.unwrap(ph[len(y) // 2, :]))) for p, ph in zip(pens, phi)},
        "pure_path_phase_peak_to_peak_rad": float(cond.q_ext * np.ptp(ux_s)),
        "runtime_s": dt,
    }
    _plot_geometric(out, y, z, z_img, pens, phi, amp, ux_s, cond)
    write_manifest(out, cfg, {"mode": "geometric", "summary": summary})
    print(json.dumps(summary, indent=2))
    return summary


def _plot_geometric(out, y, z, z_img, pens, phi, amp, ux_s, cond):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    line_along_beam = len(z) == 1 or np.allclose(phi[0, :, 0], phi[0, :, -1])
    if line_along_beam:
        iz = 0
        ax[0].plot(y, ux_s[:, iz], color="k")
        ax[0].set(xlabel="y (A), not foreshortened", ylabel="surface u_x (A)", title="surface relief")
        for p, ph, am in zip(pens, phi, amp):
            ax[1].plot(y, unwrap_rel(ph[:, iz], axis=0), label=f"Lambda={p:g} A")
            ax[2].plot(y, am[:, iz], label=f"Lambda={p:g} A")
        ax[1].plot(y, unwrap_rel(-cond.q_ext * ux_s[:, iz], axis=0), "k--", label="-q_ext u_x(surface)")
        ax[1].set(xlabel="y (A)", ylabel="phase (rad, mean removed)", title="specular phase, geometric model")
        ax[2].set(xlabel="y (A)", ylabel="|A| (column coherence)", title="kinematic column amplitude")
        ax[1].legend(fontsize=8)
    else:
        iy = len(y) // 2
        ax[0].imshow(ux_s.T, aspect="auto", origin="lower", extent=[y[0], y[-1], z[0], z[-1]], cmap="RdBu_r")
        ax[0].set(xlabel="y (A)", ylabel="z_s along beam (A)", title="surface u_x (A)")
        k = min(1, len(pens) - 1)
        ax[1].imshow(np.angle(np.exp(1j * phi[k])).T, aspect="auto", origin="lower",
                     extent=[y[0], y[-1], z_img[0], z_img[-1]], cmap="twilight")
        ax[1].set(xlabel="y (A)", ylabel="image coordinate z_s sin(theta) (A)",
                  title=f"wrapped phase, foreshortened, Lambda={pens[k]:g} A")
        for p, ph in zip(pens, phi):
            ax[2].plot(z, unwrap_rel(ph[iy, :], axis=0), label=f"Lambda={p:g} A")
        ax[2].set(xlabel="z_s along beam (A)", ylabel="phase (rad)", title="profile along the beam")
        ax[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "geometric.png", dpi=110)


# ---------------------------------------------------------------------------------------------
def run_multislice(cfg: Config, out: Path, backend: str):
    xp = ms.get_xp(backend)
    E = float(cfg.get("beam.energy_keV"))
    a = float(cfg.get("crystal.a_A"))
    V0_geo = float(cfg.get("crystal.V0_V"))
    hkl = tuple(cfg.get("reflection.hkl"))
    n_y = int(cfg.get("multislice.n_y_periods"))
    ny = int(cfg.get("multislice.ny"))
    nx = int(cfg.get("multislice.nx"))
    dx = float(cfg.get("multislice.dx_A"))
    x0 = float(cfg.get("multislice.x0_A"))
    depth = float(cfg.get("multislice.crystal_depth_A"))
    B = float(cfg.get("multislice.debye_waller_B_A2"))
    absr = float(cfg.get("multislice.absorption_ratio"))
    abs_top, abs_w, abs_V = cfg.get("multislice.bulk_absorber_top_width_Vmax")
    xc, H, edge = cfg.get("multislice.illumination_center_height_edge_A")
    q_ap = float(cfg.get("multislice.aperture_radius_per_A"))
    vac_x, vac_edge = cfg.get("multislice.vacuum_mask_x_edge_A")
    offsets = [float(v) for v in cfg.get("multislice.angle_offsets_mrad")]
    pens = [float(p) for p in cfg.get("geometric.penetration_A")]
    n_layers = int(cfg.get("geometric.n_layers"))

    lam = geo.wavelength_A(E)
    sigma = geo.interaction_constant(E)
    pos, Ly, Lz = build_slab(FRAME, a, n_y, depth)
    grid = ms.Grid(nx=nx, ny=ny, dx=dx, dy=Ly / ny, x0=x0)
    n_density = 8 / a**3
    V0_ms = ms.mean_inner_potential(n_density)
    # operating point: internal Bragg condition of hkl with the potential's own mean inner potential
    cond_ms = geo.SpecularCondition(E, V0_ms, a, hkl)
    cond_geo = geo.SpecularCondition(E, V0_geo, a, hkl)
    pz = lattice_period(FRAME, FRAME.beam_uvw, a)
    n_sl_period = int(cfg.get("multislice.slices_per_period"))

    defects = build_defects(cfg, a, Ly)
    u = defects.displacement(pos)
    pos_def = pos + u
    pos_def[:, 1] = np.mod(pos_def[:, 1], Ly)

    band = xp.asarray(grid.band_mask())
    absorber = ms.absorber_profile(grid, abs_top, abs_w, abs_V)
    t0 = time.time()
    V_flat, dz = ms.slice_potentials(pos, Lz, n_sl_period, grid, B, absr, xp=xp)
    V_def, _ = ms.slice_potentials(pos_def, Lz, n_sl_period, grid, B, absr, xp=xp)
    t_flat = [ms.transmission(V, sigma, absorber, dz, band, xp=xp) for V in V_flat]
    t_def = [ms.transmission(V, sigma, absorber, dz, band, xp=xp) for V in V_def]
    t_pot = time.time() - t0
    d111 = a / np.sqrt(3)
    sel = (grid.x < -3) & (grid.x >= -3 - 8 * d111)  # exactly 8 bilayers, above the absorber
    Vmean_top = float(sum(ms.to_numpy(V).real[sel].mean() for V in V_flat) / Lz)

    results = []
    for off in offsets:
        theta = cond_ms.theta_ext + off * 1e-3
        grid.assert_angle_in_band(theta, lam)
        L = 2 * xc / np.tan(theta)
        n_steps = int(np.ceil(L / dz))
        if (xc + H / 2) + 5 > x0 + nx * dx:
            raise ValueError("illumination band too close to the top of the cell")
        P = ms.propagator(grid, dz, lam, xp=xp)
        psi0 = ms.illumination(grid, theta, lam, xc, H, edge)
        n_in = float(np.sum(np.abs(psi0) ** 2))
        run_out = {}
        for tag, ts in (("flat", t_flat), ("defect", t_def)):
            t1 = time.time()
            psi = ms.to_numpy(ms.run(psi0, ts, P, n_steps, xp=xp))
            psi_df, spec = ms.dark_field(psi, grid, theta, lam, q_ap, vac_x, vac_edge)
            ph, am = ms.band_profile(psi_df)
            run_out[tag] = dict(psi=psi, psi_df=psi_df, phase=ph, amp=am, spec=spec,
                                R=float(np.sum(np.abs(psi_df) ** 2) / n_in), t=time.time() - t1)
        dphi = np.angle(np.exp(1j * (run_out["defect"]["phase"] - run_out["flat"]["phase"])))
        results.append(dict(offset_mrad=off, theta_ext=theta, n_steps=n_steps, L=L, **{
            f"{k}_{t}": v[k] for t, v in run_out.items() for k in ("phase", "amp", "R", "t")}, dphi=dphi,
            psi_df_defect=run_out["defect"]["psi_df"], psi_df_flat=run_out["flat"]["psi_df"],
            spec=run_out["flat"]["spec"], psi_exit_defect=run_out["defect"]["psi"]))
        print(f"offset {off:+.2f} mrad theta_ext {theta*1e3:.3f} mrad: R_flat {run_out['flat']['R']:.4g} "
              f"R_defect {run_out['defect']['R']:.4g}  ({n_steps} slices, {run_out['flat']['t']:.1f} s/run)")

    # geometric model on the multislice grid, with the geometric V0 and with the potential's V0
    y = grid.y
    phi_geo, _, ux_s, _ = geometric_profile(defects, cond_geo, y, np.array([0.0]), pens, n_layers)
    phi_geo_ms, amp_geo_ms, _, uy_s = geometric_profile(defects, cond_ms, y, np.array([0.0]), pens, n_layers)
    # same observable as the multislice: Eulerian (deformed) coordinates, then the objective aperture
    phi_geo_obs = []
    for ph, am in zip(phi_geo_ms[:, :, 0], amp_geo_ms[:, :, 0]):
        f = gm.to_deformed_coordinates(am * np.exp(1j * ph), y, uy_s[:, 0], Ly)
        phi_geo_obs.append(np.angle(gm.band_limit_1d(f, grid.dy, q_ap)))
    phi_geo_obs = np.array(phi_geo_obs)
    best = max(results, key=lambda r: r["R_flat"])
    wts = best["amp_flat"] ** 2
    inner = np.ones_like(y, bool)
    ms_rel = unwrap_rel(best["dphi"], axis=0)
    comp = {}
    for p, ph, pho in zip(pens, phi_geo_ms[:, :, 0], phi_geo_obs):
        row = {}
        for tag, g in (("raw", ph), ("observed", pho)):
            g_rel = unwrap_rel(g, axis=0)
            diff = np.angle(np.exp(1j * (ms_rel - g_rel)))
            diff -= np.angle(np.sum(wts * np.exp(1j * diff)))
            row[f"rms_residual_rad_{tag}"] = float(np.sqrt(np.average(diff[inner] ** 2, weights=wts[inner])))
            row[f"geo_ptp_rad_{tag}"] = float(np.ptp(g_rel))
        comp[str(p)] = row
    summary = {
        "grid": {"nx": nx, "ny": ny, "dx_A": dx, "dy_A": grid.dy, "x0_A": x0, "Ly_A": Ly},
        "slices_per_period": n_sl_period, "dz_A": dz, "z_period_A": pz,
        "n_atoms_cell": int(len(pos)),
        "V0_parameterisation_V": V0_ms, "V0_geometric_V": V0_geo,
        "V0_check_from_potential_V": Vmean_top,
        "theta_int_mrad": cond_ms.theta_int * 1e3,
        "theta_ext_operating_mrad_(V0_param)": cond_ms.theta_ext * 1e3,
        "theta_ext_geometric_mrad_(V0_geo)": cond_geo.theta_ext * 1e3,
        "rocking": [{"offset_mrad": r["offset_mrad"], "theta_ext_mrad": r["theta_ext"] * 1e3,
                     "R_flat": r["R_flat"], "R_defect": r["R_defect"], "n_slices": r["n_steps"],
                     "length_A": r["L"], "ms_dphi_ptp_rad": float(np.ptp(unwrap_rel(r["dphi"], axis=0)))}
                    for r in results],
        "comparison_at_offset_mrad": best["offset_mrad"],
        "multislice_dphi_ptp_rad": float(np.ptp(ms_rel)),
        "geometric_vs_multislice": comp,
        "pure_path_phase_ptp_rad": float(cond_ms.q_ext * np.ptp(ux_s[:, 0])),
        "runtime_potential_s": t_pot,
        "status": "SMOKE TEST: kernel not validated against abTEM or a dynamical solver (docs/05 M2)",
    }
    np.savez_compressed(
        out / "multislice.npz", x=grid.x, y=y, offsets_mrad=offsets,
        dphi=np.array([r["dphi"] for r in results]), phase_flat=np.array([r["phase_flat"] for r in results]),
        amp_flat=np.array([r["amp_flat"] for r in results]), amp_defect=np.array([r["amp_defect"] for r in results]),
        psi_df_defect=best["psi_df_defect"].astype(np.complex64), psi_df_flat=best["psi_df_flat"].astype(np.complex64),
        psi_exit_defect=best["psi_exit_defect"].astype(np.complex64),
        exit_plane="z = L (exit plane of the cell, no back-propagation)",
        geo_phase=phi_geo_ms[:, :, 0], geo_phase_observed=phi_geo_obs, geo_phase_V0geo=phi_geo[:, :, 0],
        penetration_A=pens, surface_uy=uy_s[:, 0],
        surface_ux=ux_s[:, 0])
    _plot_multislice(out, grid, results, best, ms_rel, pens, phi_geo_obs, ux_s[:, 0], cond_ms, q_ap)
    write_manifest(out, cfg, {"mode": "multislice", "summary": summary,
                              "potential_parameterisation": "Peng et al. 1996 high-angle, via abTEM 1.0.6 data file"},
                   backend=backend)
    print(json.dumps(summary, indent=2, default=float))
    return summary


def _plot_multislice(out, grid, results, best, ms_rel, pens, phi_geo, ux_s, cond, q_ap):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    y, x = grid.y, grid.x
    fig, ax = plt.subplots(2, 3, figsize=(16, 8.5))
    I = np.abs(best["psi_exit_defect"]) ** 2
    ax[0, 0].imshow(np.log10(I + 1e-6), aspect="auto", origin="lower", extent=[y[0], y[-1], x[0], x[-1]], vmin=-4)
    ax[0, 0].axhline(0, color="w", lw=0.5)
    ax[0, 0].set(xlabel="y (A)", ylabel="x, height above surface (A)", title="log10 |exit wave|^2 (defect run)")
    S = np.fft.fftshift(best["spec"])
    qx, qy = np.fft.fftshift(grid.qx), np.fft.fftshift(grid.qy)
    ax[0, 1].imshow(np.log10(S / S.max() + 1e-9), aspect="auto", origin="lower",
                    extent=[qy[0], qy[-1], qx[0], qx[-1]], vmin=-7)
    q0 = np.sin(best["theta_ext"]) / cond.lam
    ax[0, 1].add_patch(plt.Circle((0, q0), q_ap, fill=False, color="r"))
    ax[0, 1].set(xlabel="q_y (1/A)", ylabel="q_x (1/A)", title="exit spectrum (vacuum-masked), aperture in red",
                 xlim=(-1.0, 1.0), ylim=(-1.5, 1.5))
    ph = np.angle(best["psi_df_defect"] * np.conj(best["psi_df_flat"]))
    amp = np.abs(best["psi_df_flat"])
    ph = np.where(amp > 0.1 * amp.max(), ph, np.nan)
    ax[0, 2].imshow(ph, aspect="auto", origin="lower", extent=[y[0], y[-1], x[0], x[-1]], cmap="twilight")
    ax[0, 2].set(xlabel="y (A)", ylabel="exit height x (A)", title="dark-field phase, defect minus flat (wrapped)",
                 ylim=(0, x[-1]))
    ax[1, 0].plot(y, ux_s, "k")
    ax[1, 0].set(xlabel="y (A)", ylabel="surface u_x (A)", title="surface relief (elastic model)")
    ax[1, 1].plot(y, ms_rel, "k", lw=2.5, label="multislice (defect - flat)")
    for p, g in zip(pens, phi_geo):
        ax[1, 1].plot(y, unwrap_rel(g, axis=0), lw=1, label=f"geometric, Lambda={p:g} A")
    ax[1, 1].set(xlabel="y (A)", ylabel="phase (rad, mean removed)",
                 title="specular phase (geometric: deformed coords + same aperture)")
    ax[1, 1].legend(fontsize=7)
    offs = [r["offset_mrad"] for r in results]
    ax[1, 2].plot(offs, [r["R_flat"] for r in results], "o-", label="flat")
    ax[1, 2].plot(offs, [r["R_defect"] for r in results], "s--", label="defect")
    ax[1, 2].set(xlabel="theta_ext - theta_ext(Bragg, V0 of potential) (mrad)", ylabel="fraction in aperture",
                 title="specular intensity (sheet beam)")
    ax[1, 2].legend()
    fig.tight_layout()
    fig.savefig(out / "multislice.png", dpi=100)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["geometric", "multislice"])
    ap.add_argument("--config", required=True)
    ap.add_argument("--backend", default="numpy", choices=["numpy", "cupy"])
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    cfg = Config(args.config)
    out = Path(args.out) / cfg.data["name"] / args.mode
    out.mkdir(parents=True, exist_ok=True)
    if args.mode == "geometric":
        run_geometric(cfg, out)
    else:
        run_multislice(cfg, out, args.backend)
    print(f"outputs in {out}")


if __name__ == "__main__":
    main()
