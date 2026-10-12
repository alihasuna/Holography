#!/usr/bin/env python3
"""Validation of a reconstruction against the known truth, with pass/fail criteria and expected-failure controls.

Runs in: em-holography (CPU; numpy, scikit-image).

    gemicro run --kind analysis --name holo-validate --input derived/holo-recon/phase_unwrapped.npy \
        --input derived/hologram/image_wave_detector.npy --input sims/exit-wave/ground_truth_phase.npy \
        --params params/validate.yaml --output derived/holo-validate -- /opt/envs/em-holography/bin/python \
        code/holo_validate.py --params params/validate.yaml --recon derived/holo-recon \
        --hologram derived/hologram --exit-wave sims/exit-wave --slab sims/slab --output derived/holo-validate

Truths (both band-limited with the reconstruction's own aperture, offset to its reference region):
  T_holo  arg of the image wave at the detector pixel centres: what an ideal reconstruction of these holograms
          returns. Primary truth: tests the hologram chain (formation, sideband, normalisation, unwrapping).
  T_proj  σ·V_proj of the static structure (projection approximation). Secondary: shows how far the measured
          phase is from the thin-object interpretation (dynamical scattering, aperture, propagation).

Metrics: NCC and phase-scale slope (as gemicro's recon scoring), residual map and RMS against the predicted
shot-noise phase error, registration shift, the residual's correlation with the injected reference distortion
(the known failure mode without reference normalisation), the resolution set by the aperture, and, with --slab,
the surface-edge position of every terrace (a d_111 = 3.14 Å step must be recovered with its sign).

Exit status: 0 when the verdict matches `expected_outcome` (a control that fails as expected is a success),
3 when it does not.
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402
import holo_metrics as hm  # noqa: E402
import holo_optics as ho  # noqa: E402
import holo_sideband as hs  # noqa: E402


def read(P):
    p = {"expected": P.choice("expected_outcome", ("pass", "fail"))}
    p["region"] = P.vec("analysis_region", 4)
    p["margin"] = P.num("edge_margin_A", lo=0.0)
    C = P.sub("criteria")
    p["min_ncc"] = C.num("min_ncc", lo=-1.0, hi=1.0)
    p["max_slope_err"] = C.num("max_abs_slope_error", lo=0.0)
    p["max_noise_ratio"] = C.num("max_residual_rms_over_noise", lo=0.0, lo_open=True)
    E = P.sub("profile_edges")
    p["edges"] = E.boolean("enabled")
    if p["edges"]:
        p["plateau_window"] = E.num("plateau_window_A", lo=0.0, lo_open=True)
        p["edge_gap"] = E.num("gap_A", lo=0.0)
        p["max_step_error"] = E.num("max_step_error_A", lo=0.0, lo_open=True)
    return p


def truth_phase(psi_or_phase, aperture, region, ramp_mode, pix, seed, is_wave, amp_out=None):
    """Band-limit a truth with the reconstruction aperture and give it the reconstruction's offset/ramp."""
    if is_wave:
        w = np.fft.ifft2(np.fft.fft2(psi_or_phase) * aperture)
        if region is not None:
            w = w * np.exp(-1j * np.angle(w[region].mean()))
        t = hs.unwrap(np.angle(w), seed)
        if amp_out is not None:
            amp_out.append(np.abs(w))
    else:
        t = hm.band_limit_real(psi_or_phase, aperture)
    if region is not None:
        t = t - t[region].mean()
    if ramp_mode == "plane_in_reference_region":
        plane, _ = hs.fit_plane(t, region, pix)
        t = t - plane
    return t


def compare(rec, truth, mask):
    s, c = hm.slope_fit(rec, truth, mask)
    r = hm.residual(rec, truth, mask)
    return {"ncc": hm.ncc(rec, truth, mask), "slope": s, "intercept": c,
            "residual_rms_rad": float(r[mask].std()), "truth_std_rad": float(truth[mask].std())}, r


def terrace_edges(rec, truths, pix, slab, p, res_A, binning):
    """Surface edge (50 % crossing) of every terrace on y-averaged x profiles, for rec and each truth."""
    g = slab["physics"]["geometry"]
    x = hc.pixel_centres(rec.shape[0], pix[0], binning)
    y = hc.pixel_centres(rec.shape[1], pix[1], binning)
    edges_y = g["terrace_y_edges_A"]
    tops = g["x_top_atom_A"]
    rows = []
    for i in range(len(tops)):
        sel = (y > edges_y[i] + res_A) & (y < edges_y[i + 1] - res_A)
        if sel.sum() < 2:
            rows.append({"terrace": i, "error": "terrace narrower than 2 × resolution"})
            continue
        row = {"terrace": i, "x_top_atom_A": tops[i], "pixels_averaged_y": int(sel.sum())}
        for name, img in [("rec", rec)] + list(truths.items()):
            e = hm.edge_analysis(x, img[:, sel].mean(axis=1), tops[i], p["plateau_window"], p["edge_gap"])
            row[name] = e
        rows.append(row)
    steps = []
    n = len(tops)
    for i in range(n):
        j = (i + 1) % n
        a, b = rows[i], rows[j]
        if "rec" not in a or "rec" not in b or not a["rec"] or not b["rec"] or a["rec"]["x50_A"] is None \
                or b["rec"]["x50_A"] is None:
            steps.append({"from": i, "to": j, "error": "edge not found"})
            continue
        st = {"from": i, "to": j, "true_step_A": tops[j] - tops[i],
              "rec_step_A": b["rec"]["x50_A"] - a["rec"]["x50_A"]}
        for k in ("T_holo", "T_proj"):
            if a.get(k) and b.get(k) and a[k]["x50_A"] is not None and b[k]["x50_A"] is not None:
                st[f"{k}_step_A"] = b[k]["x50_A"] - a[k]["x50_A"]
        st["rec_minus_true_A"] = st["rec_step_A"] - st["true_step_A"]
        steps.append(st)
    return rows, steps


def run(P, recon_dir, holo_dir, exit_dir, slab_dir, out):
    p = read(P)
    P.finish()
    rs = hc.Stage(recon_dir, "recon")
    hs_ = hc.Stage(holo_dir, "hologram")
    rec = rs.array("phase_unwrapped").astype(np.float64)
    pix = rs.sampling("phase_unwrapped")
    if tuple(hs_.sampling("image_wave_detector")) != tuple(pix):
        raise SystemExit("reconstruction and hologram pixel sizes differ")
    rphys = rs.meta["physics"]
    hphys = hs_.meta["physics"]
    seed = rs.meta["params"]["seed"]
    A = rs.array("aperture").astype(np.float64)
    region = hc.region_mask(rec.shape, rphys["phase_reference_region"]) if rphys["phase_reference_region"] else None
    ramp_mode = rphys["ramp_removal"]

    psi = hs_.array("image_wave_detector").astype(np.complex128)
    amp_box = []
    truths = {"T_holo": truth_phase(psi, A, region, ramp_mode, pix, seed, True, amp_box)}
    if exit_dir is not None:
        es = hc.Stage(exit_dir, "exit_wave")
        gt = es.array("ground_truth_phase").astype(np.float64)
        b = hphys["binning"]
        cx, cy = hphys["cropped_fine_pixels"]
        gt = gt[:gt.shape[0] - cx, :gt.shape[1] - cy]
        truths["T_proj"] = truth_phase(ho.bin_pixels(gt, b), A, region, ramp_mode, pix, seed, False)

    ov = hs_.array("overlap_mask")
    mask = ov & hc.region_mask(rec.shape, p["region"]) & hm.edge_mask(rec.shape, pix, p["margin"])
    if mask.sum() < 16:
        raise SystemExit("fewer than 16 pixels in the analysis mask")
    results = {}
    resid = None
    for k, t in truths.items():
        results[k], r = compare(rec, t, mask)
        if k == "T_holo":
            resid = r
    results["registration_shift_px_vs_T_holo"] = hm.registration_shift(rec, truths["T_holo"])
    phi_d = hs_.array("reference_distortion_phase").astype(np.float64)
    # Without reference normalisation the residual is -φ_d plus a plane (the uncancelled sub-pixel carrier):
    # compare after removing a best-fit plane from both, so ≈ 1 identifies that failure, ≈ 0 means noise.
    if phi_d[mask].std() > 1e-9:
        r_flat = resid - hs.fit_plane(resid, mask, pix)[0]
        d_flat = -phi_d - hs.fit_plane(-phi_d, mask, pix)[0]
        results["residual_vs_injected_distortion_ncc"] = hm.ncc(r_flat, d_flat, mask) \
            if d_flat[mask].std() > 1e-9 else None
    else:
        results["residual_vs_injected_distortion_ncc"] = None
    noise_pred = rphys["predicted_vacuum_phase_noise_rad"]
    vac_std = float(rec[region & ov].std()) if region is not None else None
    radius = rphys["aperture"]["radius_inv_A"]
    res_A = 1.0 / radius
    resolution = {"aperture_radius_inv_A": radius, "aperture_radius_mrad": rphys["aperture"]["radius_mrad"],
                  "resolution_A": res_A, "resolution_in_fringe_spacings": rphys["aperture"][
                      "resolution_in_fringe_spacings"],
                  "object_band_limit_inv_A": hphys["object_band_limit_inv_A"],
                  "note": "the reconstruction cannot represent spatial frequencies above the aperture radius; "
                          "T_holo and T_proj are band-limited with the same aperture before comparison"}

    edges = None
    if p["edges"]:
        if slab_dir is None:
            raise hc.ParamError("profile_edges.enabled needs --slab")
        slab = hc.Stage(slab_dir, "slab").meta
        rows, steps = terrace_edges(rec, truths, pix, slab, p, res_A, hphys["binning"])
        widths = [r["rec"]["width_10_90_A"] for r in rows if r.get("rec") and r["rec"]["width_10_90_A"]]
        resolution["measured_edge_width_10_90_A_rec"] = float(np.median(widths)) if widths else None
        tw = [r["T_holo"]["width_10_90_A"] for r in rows if r.get("T_holo") and r["T_holo"]["width_10_90_A"]]
        resolution["measured_edge_width_10_90_A_T_holo"] = float(np.median(tw)) if tw else None
        edges = {"terraces": rows, "steps": steps}

    # mask sensitivity (spec / gemicro /holography skill): ±20 % aperture radius
    sens = []
    stack = rs.array("phase_mask_sensitivity")
    for s, img in zip(rphys["mask_sensitivity_scales"], stack):
        d = img.astype(np.float64) - rec
        row = {"scale": s, "rms_change_rad": float((d[mask] - d[mask].mean()).std()),
               "ncc_vs_T_holo_nominal_aperture": hm.ncc(img, truths["T_holo"], mask)}
        if edges is not None:
            _, st2 = terrace_edges(img.astype(np.float64), {}, pix, slab, p, res_A, hphys["binning"])
            row["steps_rec_A"] = [x.get("rec_step_A") for x in st2]
        sens.append(row)

    # local shot-noise prediction: the object sideband scales with |ψ| while its noise scales with the local
    # intensity a_o²|ψ|² + a_r² (vacuum = 1), so σ² = σ_obj² (a_o²|ψ|² + a_r²)/|ψ|² + σ_ref²
    comp = rphys["predicted_noise_components_rad"]
    rw = hphys["reference_wave"]
    a_amp = np.maximum(amp_box[0], 0.05)
    sig_loc = np.sqrt(comp["object_hologram"] ** 2 * (rw["amp_obj"] ** 2 * a_amp ** 2 + rw["amp_ref"] ** 2)
                      / a_amp ** 2 + comp["reference_hologram"] ** 2)
    z = resid[mask] / sig_loc[mask]
    th = results["T_holo"]
    th["residual_rms_over_local_noise"] = float(z.std())
    th["ncc_expected_from_noise"] = 1.0 / math.sqrt(1.0 + (noise_pred / th["truth_std_rad"]) ** 2) \
        if th["truth_std_rad"] > 0 else None
    ratio_vac = th["residual_rms_rad"] / noise_pred if noise_pred > 0 else float("inf")
    ratio = th["residual_rms_over_local_noise"]
    checks = {"ncc": th["ncc"] >= p["min_ncc"], "slope": abs(th["slope"] - 1.0) <= p["max_slope_err"],
              "residual_vs_noise": ratio <= p["max_noise_ratio"]}
    if edges is not None:
        errs = [abs(s["rec_minus_true_A"]) for s in edges["steps"] if "rec_minus_true_A" in s]
        checks["terrace_steps"] = bool(errs) and len(errs) == len(edges["steps"]) and max(errs) <= p["max_step_error"]
    verdict = "pass" if all(checks.values()) else "fail"
    matched = verdict == p["expected"]

    plots = []
    t = truths["T_holo"]
    lim = (float(min(rec[mask].min(), t[mask].min())), float(max(rec[mask].max(), t[mask].max())))
    plots.append(hc.plot_map(out, "truth_T_holo.png", np.where(mask, t, np.nan), "T_holo (band-limited truth)",
                             pix, "rad", vlim=lim))
    plots.append(hc.plot_map(out, "reconstructed_phase.png", np.where(mask, rec, np.nan), "reconstructed phase",
                             pix, "rad", vlim=lim))
    rl = 4 * max(noise_pred, float(resid[mask].std()))
    plots.append(hc.plot_map(out, "residual_map.png", np.where(mask, resid, np.nan),
                             f"residual rec - T_holo (RMS {th['residual_rms_rad']:.4f} rad)", pix, "rad",
                             cmap="RdBu_r", vlim=(-rl, rl)))
    plt = hc._plt()
    if plt is not None:
        fig, ax = plt.subplots(figsize=(5, 4.5))
        sel = np.flatnonzero(mask.ravel())
        sel = sel[:: max(1, len(sel) // 20000)]
        ax.plot(t.ravel()[sel], rec.ravel()[sel], ",", alpha=0.4)
        xx = np.array(lim)
        ax.plot(xx, th["slope"] * xx + th["intercept"], "r-", label=f"slope {th['slope']:.3f}")
        ax.plot(xx, xx, "k--", lw=0.8, label="1:1")
        ax.set_xlabel("T_holo (rad)")
        ax.set_ylabel("reconstructed (rad)")
        ax.set_title(f"NCC {th['ncc']:.4f}", fontsize=9)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out.path("phase_scale.png"), dpi=140)
        plt.close(fig)
        plots.append("phase_scale.png")
        if edges is not None:
            x = hc.pixel_centres(rec.shape[0], pix[0], hphys["binning"])
            y = hc.pixel_centres(rec.shape[1], pix[1], hphys["binning"])
            g = slab["physics"]["geometry"]
            fig, ax = plt.subplots(figsize=(7, 4.2))
            for i, top in enumerate(g["x_top_atom_A"]):
                sel_y = (y > g["terrace_y_edges_A"][i] + res_A) & (y < g["terrace_y_edges_A"][i + 1] - res_A)
                if sel_y.sum() < 2:
                    continue
                ln, = ax.plot(x, rec[:, sel_y].mean(axis=1), "-", lw=1, label=f"terrace {i} rec")
                ax.plot(x, t[:, sel_y].mean(axis=1), ":", color=ln.get_color(), lw=1)
                ax.axvline(top, color=ln.get_color(), lw=0.6, ls="--")
            lo_x, hi_x = min(g["x_top_atom_A"]) - 25, max(g["x_top_atom_A"]) + 25
            ax.set_xlim(lo_x, hi_x)
            vis = rec[(x > lo_x) & (x < hi_x)][:, 1:-1]
            ax.set_ylim(float(np.percentile(vis, 0.5)) - 0.2, float(np.percentile(vis, 99.5)) + 0.2)
            ax.set_xlabel("x (Å), surface normal")
            ax.set_ylabel("phase (rad)")
            ax.set_title("surface profiles per terrace: solid rec, dotted T_holo, dashed top atom", fontsize=9)
            if ax.get_legend_handles_labels()[0]:
                ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(out.path("terrace_profiles.png"), dpi=140)
            plt.close(fig)
            plots.append("terrace_profiles.png")

    out.save_array("residual", np.where(mask, resid, 0.0), units="rad", axes=["x", "y"], sampling_A=pix,
                   description="rec - T_holo, mean removed, zero outside the analysis mask")
    out.save_array("truth_T_holo", t, units="rad", axes=["x", "y"], sampling_A=pix,
                   description="band-limited image-wave phase with the reconstruction's offset")
    if "T_proj" in truths:
        out.save_array("truth_T_proj", truths["T_proj"], units="rad", axes=["x", "y"], sampling_A=pix,
                       description="band-limited σ·V_proj with the reconstruction's offset")
    out.save_array("analysis_mask", mask, units="bool", axes=["x", "y"], sampling_A=pix,
                   description="pixels used for every metric")

    physics = {"comparisons": results, "noise": {"predicted_rad": noise_pred,
                                                 "reference_region_std_rad": vac_std,
                                                 "residual_rms_over_vacuum_prediction": ratio_vac,
                                                 "residual_rms_over_local_prediction": ratio,
                                                 "local_prediction": "σ² = σ_obj² (a_o²|ψ|² + a_r²)/|ψ|² + σ_ref², "
                                                                     "|ψ| from T_holo's band-limited wave"},
               "resolution": resolution, "terrace_edges": edges, "mask_sensitivity": sens,
               "criteria": {k: p[k] for k in ("min_ncc", "max_slope_err", "max_noise_ratio")},
               "checks": checks, "verdict": verdict, "expected_outcome": p["expected"],
               "outcome_matches_expectation": matched,
               "reconstruction": {"engine": rphys["engine"], "reference_normalization":
                                  rphys["reference_normalization"], "carrier": rphys["carrier"]["q_refined_inv_A"]},
               "analysis_pixels": int(mask.sum())}
    summary = {"verdict": verdict, "expected": p["expected"], "matches_expectation": matched,
               "ncc_T_holo": round(th["ncc"], 5),
               "ncc_expected_from_noise": None if th["ncc_expected_from_noise"] is None
               else round(th["ncc_expected_from_noise"], 5), "slope_T_holo": round(th["slope"], 5),
               "residual_rms_rad": round(th["residual_rms_rad"], 5), "predicted_noise_rad": round(noise_pred, 5),
               "residual_over_noise": round(ratio, 3), "residual_over_vacuum_noise": round(ratio_vac, 3),
               "residual_vs_distortion_ncc": None if results["residual_vs_injected_distortion_ncc"] is None
               else round(results["residual_vs_injected_distortion_ncc"], 4),
               "registration_shift_px": results["registration_shift_px_vs_T_holo"],
               "resolution_A": round(res_A, 3)}
    if "T_proj" in results:
        summary["ncc_T_proj"] = round(results["T_proj"]["ncc"], 5)
        summary["slope_T_proj"] = round(results["T_proj"]["slope"], 5)
    if edges is not None:
        summary["terrace_steps_true_A"] = [round(s.get("true_step_A", float("nan")), 4) for s in edges["steps"]]
        summary["terrace_steps_rec_A"] = [None if "rec_step_A" not in s else round(s["rec_step_A"], 4)
                                          for s in edges["steps"]]
        summary["edge_width_10_90_A"] = resolution.get("measured_edge_width_10_90_A_rec")
    summary["checks"] = {k: bool(v) for k, v in checks.items()}
    summary["plots"] = [x for x in plots if x]
    return physics, summary, matched, {"recon_sidecar": rs.sidecar_path, "hologram_sidecar": hs_.sidecar_path}


def main(argv=None):
    ap = hc.common_cli("Validate a reconstruction against the truth (env: em-holography)",
                       [("--recon", "output folder of holo_recon.py"),
                        ("--hologram", "output folder of hologram_formation.py (truth, distortion, overlap)")])
    ap.add_argument("--exit-wave", default=None, help="exit-wave folder (σ·V_proj truth; optional)")
    ap.add_argument("--slab", default=None, help="slab folder (terrace edges; needed with profile_edges)")
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    with hc.Output(a.output, a.overwrite) as out:
        physics, summary, matched, inputs = run(hc.Section(raw), a.recon, a.hologram, a.exit_wave, a.slab, out)
        hc.write_sidecar(out, "validate", raw, hc.provenance(sys.argv, a.params, inputs), physics, summary)
        out.publish()
    hc.print_summary("validation", summary, out.final, out.files)
    if matched:
        print(f"   OUTCOME: {summary['verdict'].upper()} as expected"
              + (" (control: the metrics detect the deliberate error)" if summary["expected"] == "fail" else ""))
        return 0
    print(f"   OUTCOME: {summary['verdict'].upper()} but {summary['expected'].upper()} was expected", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
