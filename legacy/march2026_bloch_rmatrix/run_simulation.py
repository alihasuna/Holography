#!/usr/bin/env python3
"""
run_simulation.py
=================
Full simulation pipeline for bulk reflection electron diffraction from Si[110].

Combines:
1. CL3 beam tilt calibration -> grazing angle
2. Kinematical Ewald construction -> spot positions
3. Dynamical Bloch wave + R-matrix -> intensities
4. Comparison with experimental data -> spot indexing and R-factor

Usage:
    python -m simulation.run_simulation                    # process all patterns
    python -m simulation.run_simulation --file pattern.hm  # single file
    python -m simulation.run_simulation --rocking-curve    # compute rocking curve
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation.constants import (
    ANGULAR_SCALE, DETECTOR_SHAPE, K_200KV, SURFACE_NORMAL,
    ZA_X, ZA_Y, ZA_Z,
)
from simulation.calibration import (
    btx_bty_to_tilt_mrad, compute_incident_wavevector,
    compute_grazing_angle,
)
from simulation.kinematical import (
    generate_reciprocal_lattice, predict_spots, predict_specular_position,
)
from simulation.r_matrix import compute_reflected_intensities
from simulation.overlay import (
    load_hm_frame, load_experimental_spots, predict_all_spots,
    match_spots_hungarian, plot_overlay,
)


def run_single_pattern(hm_path, csv_path, outdir,
                       btx=-814.0, bty=135.0,
                       n_strong=20, max_index=10):
    """Full analysis pipeline for one experimental pattern.

    1. Load experimental data
    2. Kinematical prediction (spot positions)
    3. Dynamical calculation (intensities)
    4. Match and index spots
    5. Generate overlay and comparison plots
    """
    from scipy.ndimage import gaussian_filter

    stem = Path(hm_path).stem
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # load experimental data
    frame = load_hm_frame(hm_path)
    exp_spots = load_experimental_spots(csv_path) if Path(csv_path).exists() else []

    # auto-detect direct beam as brightest spot
    smooth = gaussian_filter(frame, sigma=3.0)
    cy, cx = np.unravel_index(np.argmax(smooth), smooth.shape)
    direct_beam_yx = (float(cy), float(cx))

    # calibration
    tx, ty = btx_bty_to_tilt_mrad(btx, bty)
    k_i = compute_incident_wavevector(tx, ty)
    grazing = compute_grazing_angle(tx, ty)

    # kinematical prediction
    pred_spots = predict_all_spots(tx, ty, direct_beam_yx=direct_beam_yx,
                                   max_index=max_index,
                                   excitation_error_tol=2.0)
    on_det = [s for s in pred_spots
              if -20 <= s["y_px"] <= 276 and -20 <= s["x_px"] <= 276]

    # dynamical intensities
    hkl_list, g_vectors, f_sq = generate_reciprocal_lattice(max_index=8)
    dyn_results = compute_reflected_intensities(
        k_i, hkl_list, g_vectors, n_strong=n_strong, absorption_ratio=0.07)

    # add dynamical intensities to predicted spots
    dyn_dict = {r["hkl"]: r["intensity"] for r in dyn_results}
    for s in on_det:
        s["dyn_intensity"] = dyn_dict.get(s["hkl"], 0.0)

    # match predicted to experimental
    matched, unmatched_pred, unmatched_exp = match_spots_hungarian(
        on_det, exp_spots, max_distance_px=15.0)

    # overlay plot
    overlay_path = outdir / f"{stem}_full_overlay.tiff"
    title = (f"{stem}\n"
             f"grazing={grazing:.1f} mrad ({grazing/1e3*180/np.pi:.2f} deg)  "
             f"direct beam=({direct_beam_yx[0]:.0f},{direct_beam_yx[1]:.0f})  "
             f"matched={len(matched)}/{len(exp_spots)}")
    plot_overlay(frame, on_det, exp_spots, matched,
                 unmatched_pred, unmatched_exp,
                 title=title, outpath=str(overlay_path))

    # save indexed spots CSV
    csv_out = outdir / f"{stem}_indexed.csv"
    with open(csv_out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hkl", "pred_y", "pred_x", "exp_y", "exp_x",
                         "distance_px", "s_g", "F_sq", "dyn_intensity",
                         "exp_intensity", "is_reflection"])
        for m in matched:
            writer.writerow([
                f"({m['hkl'][0]},{m['hkl'][1]},{m['hkl'][2]})",
                f"{m['pred_y']:.1f}", f"{m['pred_x']:.1f}",
                f"{m['exp_y']:.1f}", f"{m['exp_x']:.1f}",
                f"{m['distance_px']:.2f}", f"{m['s_g']:.4f}",
                f"{m['F_sq']:.2f}",
                f"{dyn_dict.get(m['hkl'], 0):.6f}",
                f"{m['exp_intensity']:.1f}",
                str(m.get("is_reflection", "")),
            ])

    # intensity comparison for matched spots
    if matched:
        _plot_intensity_comparison(matched, dyn_dict, outdir, stem)

    return {
        "filename": stem,
        "n_predicted": len(on_det),
        "n_experimental": len(exp_spots),
        "n_matched": len(matched),
        "grazing_mrad": grazing,
        "direct_beam": direct_beam_yx,
        "matched": matched,
        "dyn_results": dyn_results[:10],
    }


def _plot_intensity_comparison(matched, dyn_dict, outdir, stem):
    """Scatter plot of predicted vs experimental intensities."""
    exp_int = []
    sim_int = []
    labels = []
    for m in matched:
        dyn = dyn_dict.get(m["hkl"], 0.0)
        if dyn > 0 and m["exp_intensity"] > 0:
            exp_int.append(m["exp_intensity"])
            sim_int.append(dyn)
            labels.append(f"({m['hkl'][0]},{m['hkl'][1]},{m['hkl'][2]})")

    if len(exp_int) < 2:
        return

    fig, ax = plt.subplots(1, 1, figsize=(6, 6), dpi=150)
    ax.scatter(exp_int, sim_int, c="royalblue", s=50, zorder=5)
    for i, lab in enumerate(labels):
        ax.annotate(lab, (exp_int[i], sim_int[i]),
                    fontsize=7, xytext=(5, 5), textcoords="offset points")

    ax.set_xlabel("Experimental intensity (arb.)")
    ax.set_ylabel("Simulated intensity (normalized)")
    ax.set_title(f"Intensity comparison: {stem}")
    ax.set_xscale("log")
    ax.set_yscale("log")

    # R-factor
    exp_arr = np.array(exp_int)
    sim_arr = np.array(sim_int)
    scale = np.sum(exp_arr * sim_arr) / np.sum(sim_arr**2)
    r_factor = np.sum(np.abs(exp_arr - scale * sim_arr)) / np.sum(exp_arr)
    corr = np.corrcoef(np.log(exp_arr), np.log(sim_arr))[0, 1]
    ax.text(0.05, 0.95, f"R = {r_factor:.3f}\ncorr = {corr:.3f}",
            transform=ax.transAxes, fontsize=10, verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    plt.tight_layout()
    plt.savefig(str(outdir / f"{stem}_intensity.tiff"), dpi=150, format="tiff")
    plt.close()


def run_all_patterns(data_dir, btx=-814.0, bty=135.0):
    """Run full pipeline on all .hm files."""
    import glob as gl

    data_dir = Path(data_dir)
    tiff_dir = data_dir / "tiff_exports"
    out_dir = data_dir / "simulation_results"
    out_dir.mkdir(exist_ok=True)

    hm_files = sorted(gl.glob(str(data_dir / "*.hm")))
    print(f"Running full simulation pipeline on {len(hm_files)} patterns...")
    print(f"Output: {out_dir}/\n")

    all_results = []
    for hm_path in hm_files:
        stem = Path(hm_path).stem
        csv_path = tiff_dir / f"{stem}_spots.csv"
        if not csv_path.exists():
            print(f"  Skipping {stem}: no spots CSV")
            continue

        result = run_single_pattern(
            str(hm_path), str(csv_path), str(out_dir),
            btx=btx, bty=bty)
        all_results.append(result)
        print(f"  {stem}: {result['n_matched']}/{result['n_experimental']} matched, "
              f"grazing={result['grazing_mrad']:.1f} mrad")

    # summary table
    _write_summary(all_results, out_dir)
    _print_dynamical_summary(all_results)

    return all_results


def _write_summary(results, outdir):
    """Write summary CSV."""
    csv_path = Path(outdir) / "_simulation_summary.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "n_predicted", "n_experimental",
                         "n_matched", "grazing_mrad", "direct_beam_y",
                         "direct_beam_x"])
        for r in results:
            writer.writerow([
                r["filename"], r["n_predicted"], r["n_experimental"],
                r["n_matched"], f"{r['grazing_mrad']:.2f}",
                f"{r['direct_beam'][0]:.0f}", f"{r['direct_beam'][1]:.0f}",
            ])
    print(f"\nSummary saved: {csv_path}")


def _print_dynamical_summary(results):
    """Print strongest reflections from dynamical calculation."""
    if not results:
        return
    # use first result's dynamical data
    dyn = results[0].get("dyn_results", [])
    if not dyn:
        return

    print("\nDynamical reflected intensities (first pattern):")
    print(f"  {'hkl':>12s}  {'intensity':>10s}  {'s_g':>8s}")
    for r in dyn[:10]:
        h, k, l = r["hkl"]
        print(f"  ({h:2d},{k:2d},{l:2d})  {r['intensity']:10.6f}  {r['s_g']:8.4f}")


def run_rocking_curve(outdir, n_strong=20, n_points=100):
    """Compute and plot the specular rocking curve."""
    from simulation.r_matrix import compute_rocking_curve

    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)

    hkl_list, g_vectors, f_sq = generate_reciprocal_lattice(max_index=6)

    print("Computing rocking curve...")
    angles, intensity = compute_rocking_curve(
        hkl_list, g_vectors,
        grazing_range_mrad=(5, 80),
        n_points=n_points,
        n_strong=n_strong,
        absorption_ratio=0.07)

    # mark the experimental angle
    tx, ty = btx_bty_to_tilt_mrad(-814.0, 135.0)
    exp_grazing = compute_grazing_angle(tx, ty)

    fig, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=150)
    ax.plot(angles, intensity, "b-", linewidth=1.5)
    ax.axvline(exp_grazing, color="red", linestyle="--", linewidth=1,
               label=f"Experimental: {exp_grazing:.1f} mrad")
    ax.set_xlabel("Grazing angle (mrad)")
    ax.set_ylabel("Specular intensity (normalized)")
    ax.set_title("Si[110] Rocking Curve - Specular Beam (200 kV)")
    ax.legend()
    ax.set_xlim(5, 80)

    plt.tight_layout()
    outpath = outdir / "rocking_curve.tiff"
    plt.savefig(str(outpath), dpi=150, format="tiff")
    plt.close()
    print(f"Rocking curve saved: {outpath}")

    return angles, intensity


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Full reflection diffraction simulation pipeline")
    parser.add_argument("--dir", type=str,
                        default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--file", type=str, default=None,
                        help="Single .hm file")
    parser.add_argument("--btx", type=float, default=-814.0)
    parser.add_argument("--bty", type=float, default=135.0)
    parser.add_argument("--rocking-curve", action="store_true",
                        help="Compute specular rocking curve")
    parser.add_argument("--n-strong", type=int, default=20,
                        help="Number of strong beams in dynamical calculation")
    args = parser.parse_args()

    data_dir = Path(args.dir)
    out_dir = data_dir / "simulation_results"

    if args.rocking_curve:
        run_rocking_curve(str(out_dir), n_strong=args.n_strong)
    elif args.file:
        stem = Path(args.file).stem
        csv_path = data_dir / "tiff_exports" / f"{stem}_spots.csv"
        run_single_pattern(args.file, str(csv_path), str(out_dir),
                           btx=args.btx, bty=args.bty, n_strong=args.n_strong)
    else:
        run_all_patterns(str(data_dir), btx=args.btx, bty=args.bty)
