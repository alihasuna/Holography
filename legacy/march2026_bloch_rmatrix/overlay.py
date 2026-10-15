"""
overlay.py
==========
Overlay kinematical spot predictions on experimental diffraction patterns.
Matches predicted spots to experimental detections using Hungarian algorithm.
"""

import sys
import numpy as np
import csv
from pathlib import Path
from scipy.optimize import linear_sum_assignment

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation.constants import (
    ANGULAR_SCALE, DETECTOR_SHAPE, K_200KV,
    ZA_Z, ZA_X, ZA_Y, SURFACE_NORMAL,
)
from simulation.kinematical import predict_spots, generate_reciprocal_lattice
from simulation.calibration import (
    btx_bty_to_tilt_mrad, compute_incident_wavevector,
    compute_grazing_angle,
)


def load_experimental_spots(csv_path):
    """Load spot detection results from process_diffraction.py CSV."""
    spots = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            spots.append({
                "y_px": float(row["y_px"]),
                "x_px": float(row["x_px"]),
                "intensity": float(row["intensity"]),
                "dist_px": float(row["dist_px"]),
                "two_theta_mrad": float(row["2theta_mrad"]),
            })
    return spots


def load_hm_frame(hm_path):
    """Load summed diffraction frame from .hm file."""
    import h5py
    import json
    with h5py.File(hm_path, "r") as f:
        data = f["micrograph"][:]
    if data.ndim == 3:
        frame = np.sum(data, axis=0).astype(np.float64)
    else:
        frame = data.astype(np.float64)
    return np.clip(frame, 0, None)


def predict_all_spots(theta_x_mrad, theta_y_mrad, direct_beam_yx=(128, 128),
                      max_index=10, excitation_error_tol=2.0):
    """Predict all spots and shift to match the direct beam position.

    In the experiment, the direct beam (000) appears at a specific position
    on the detector (near the bright central spot). This function shifts
    the predicted pattern so 000 lands at direct_beam_yx.
    """
    k_i = compute_incident_wavevector(theta_x_mrad, theta_y_mrad)
    spots = predict_spots(theta_x_mrad, theta_y_mrad,
                          max_index=max_index,
                          excitation_error_tol=excitation_error_tol)

    # shift so 000 (direct beam) lands at direct_beam_yx
    # currently, spots are computed with 000 at detector center (128, 128)
    dy = direct_beam_yx[0] - DETECTOR_SHAPE[0] / 2
    dx = direct_beam_yx[1] - DETECTOR_SHAPE[1] / 2
    for s in spots:
        s["y_px"] += dy
        s["x_px"] += dx

    # flag reflection vs transmission geometry
    for s in spots:
        h, k, l = s["hkl"]
        recip = 2 * np.pi / 5.43102
        g = recip * np.array([h, k, l], dtype=float)
        k_f = k_i + g
        s["is_reflection"] = np.dot(k_f, SURFACE_NORMAL) > 0

    return spots


def match_spots_hungarian(predicted, experimental, max_distance_px=15.0):
    """Match predicted to experimental spots using Hungarian algorithm.

    Returns list of matched pairs and unmatched spots on both sides.
    """
    if not predicted or not experimental:
        return [], predicted, experimental

    pred_pos = np.array([[s["y_px"], s["x_px"]] for s in predicted])
    exp_pos = np.array([[s["y_px"], s["x_px"]] for s in experimental])

    # pairwise distance matrix
    diff = pred_pos[:, None, :] - exp_pos[None, :, :]
    dist_matrix = np.sqrt(np.sum(diff**2, axis=2))

    # hungarian assignment (minimise total distance)
    row_idx, col_idx = linear_sum_assignment(dist_matrix)

    matched = []
    matched_pred_idx = set()
    matched_exp_idx = set()

    for r, c in zip(row_idx, col_idx):
        if dist_matrix[r, c] <= max_distance_px:
            matched.append({
                "hkl": predicted[r]["hkl"],
                "pred_y": predicted[r]["y_px"],
                "pred_x": predicted[r]["x_px"],
                "exp_y": experimental[c]["y_px"],
                "exp_x": experimental[c]["x_px"],
                "distance_px": dist_matrix[r, c],
                "s_g": predicted[r]["s_g"],
                "F_sq": predicted[r]["F_sq"],
                "exp_intensity": experimental[c]["intensity"],
                "is_reflection": predicted[r].get("is_reflection", None),
            })
            matched_pred_idx.add(r)
            matched_exp_idx.add(c)

    unmatched_pred = [predicted[i] for i in range(len(predicted))
                      if i not in matched_pred_idx]
    unmatched_exp = [experimental[i] for i in range(len(experimental))
                     if i not in matched_exp_idx]

    return matched, unmatched_pred, unmatched_exp


def plot_overlay(frame, predicted_spots, experimental_spots, matched,
                 unmatched_pred, unmatched_exp,
                 title="", outpath="overlay.tiff",
                 gamma=0.3, clip_hi=99.5):
    """Plot experimental pattern with overlaid predictions.

    - Red circles + hkl labels: predicted spots
    - Green circles: experimental detections
    - Yellow lines: matched pairs
    - Cyan cross: direct beam (000)
    """
    vmax = np.percentile(frame, clip_hi)

    fig, ax = plt.subplots(1, 1, figsize=(12, 12), dpi=200)
    ax.imshow(frame, cmap="gray",
              norm=PowerNorm(gamma=gamma, vmin=0, vmax=vmax),
              origin="upper")

    # matched pairs: yellow connecting lines
    for m in matched:
        ax.plot([m["pred_x"], m["exp_x"]], [m["pred_y"], m["exp_y"]],
                "-", color="yellow", linewidth=0.8, alpha=0.6)

    # experimental spots: green circles
    for s in experimental_spots:
        ax.plot(s["x_px"], s["y_px"], "o", markerfacecolor="none",
                markeredgecolor="lime", markersize=10, markeredgewidth=1.0)

    # predicted spots on detector: red circles with hkl labels
    for s in predicted_spots:
        y, x = s["y_px"], s["x_px"]
        if not (0 <= y <= frame.shape[0] and 0 <= x <= frame.shape[1]):
            continue
        color = "red" if s.get("is_reflection", True) else "deepskyblue"
        ax.plot(x, y, "s", markerfacecolor="none",
                markeredgecolor=color, markersize=8, markeredgewidth=1.2)

        h, k, l = s["hkl"]
        label = f"({h}{k}{l})"
        ax.annotate(label, (x, y), xytext=(x + 6, y - 6),
                    fontsize=5.5, color=color, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.1", fc="black",
                              alpha=0.5, ec="none"))

    # matched spots: show hkl in yellow
    for m in matched:
        h, k, l = m["hkl"]
        label = f"({h}{k}{l})"
        ax.annotate(label, (m["exp_x"], m["exp_y"]),
                    xytext=(m["exp_x"] - 30, m["exp_y"] + 12),
                    fontsize=6, color="yellow", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.15", fc="black",
                              alpha=0.7, ec="yellow", linewidth=0.5))

    # legend
    legend_text = (
        f"Red squares: predicted (reflection)\n"
        f"Blue squares: predicted (transmission)\n"
        f"Green circles: experimental detections\n"
        f"Yellow lines: matched pairs ({len(matched)} matches)\n"
        f"Predicted on det: {sum(1 for s in predicted_spots if 0<=s['y_px']<=256 and 0<=s['x_px']<=256)}\n"
        f"Experimental: {len(experimental_spots)}\n"
        f"Unmatched pred: {len(unmatched_pred)}, exp: {len(unmatched_exp)}"
    )
    ax.text(0.02, 0.02, legend_text, transform=ax.transAxes, fontsize=7,
            verticalalignment="bottom", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="black", alpha=0.8),
            color="white")

    ax.set_xlim(-0.5, frame.shape[1] - 0.5)
    ax.set_ylim(frame.shape[0] - 0.5, -0.5)
    ax.set_xlabel("x (px)", fontsize=10)
    ax.set_ylabel("y (px)", fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)

    plt.tight_layout()
    plt.savefig(outpath, dpi=200, bbox_inches="tight", format="tiff")
    plt.close()
    print(f"  Saved: {outpath}")


def run_overlay_single(hm_path, csv_path, outpath,
                       btx=-814.0, bty=135.0,
                       direct_beam_yx=None,
                       max_index=10,
                       excitation_error_tol=2.0,
                       match_tolerance_px=15.0):
    """Run full overlay pipeline for a single pattern.

    Parameters
    ----------
    hm_path : str
        Path to .hm file.
    csv_path : str
        Path to spot detection CSV.
    outpath : str
        Output TIFF path.
    btx, bty : float
        CL3 beam tilt DAC values.
    direct_beam_yx : (float, float) or None
        Position of direct beam on detector. If None, auto-detect as brightest.
    """
    from scipy.ndimage import gaussian_filter

    frame = load_hm_frame(hm_path)
    exp_spots = load_experimental_spots(csv_path)

    # auto-detect direct beam as brightest spot
    if direct_beam_yx is None:
        smooth = gaussian_filter(frame, sigma=3.0)
        cy, cx = np.unravel_index(np.argmax(smooth), smooth.shape)
        direct_beam_yx = (float(cy), float(cx))

    tx, ty = btx_bty_to_tilt_mrad(btx, bty)
    grazing = compute_grazing_angle(tx, ty)

    pred_spots = predict_all_spots(tx, ty, direct_beam_yx=direct_beam_yx,
                                   max_index=max_index,
                                   excitation_error_tol=excitation_error_tol)

    # filter to on-detector
    on_det = [s for s in pred_spots
              if -20 <= s["y_px"] <= 276 and -20 <= s["x_px"] <= 276]

    matched, unmatched_pred, unmatched_exp = match_spots_hungarian(
        on_det, exp_spots, max_distance_px=match_tolerance_px)

    title = (f"{Path(hm_path).stem}\n"
             f"grazing={grazing:.1f} mrad ({grazing/1e3*180/np.pi:.2f} deg)  "
             f"direct beam=({direct_beam_yx[0]:.0f},{direct_beam_yx[1]:.0f})")

    plot_overlay(frame, on_det, exp_spots, matched,
                 unmatched_pred, unmatched_exp,
                 title=title, outpath=outpath)

    return {
        "n_predicted": len(on_det),
        "n_experimental": len(exp_spots),
        "n_matched": len(matched),
        "matched": matched,
        "grazing_mrad": grazing,
    }


def run_overlay_all(data_dir, btx=-814.0, bty=135.0):
    """Run overlay on all patterns in the diffraction series."""
    import glob as gl

    data_dir = Path(data_dir)
    tiff_dir = data_dir / "tiff_exports"
    out_dir = data_dir / "simulation_overlays"
    out_dir.mkdir(exist_ok=True)

    hm_files = sorted(gl.glob(str(data_dir / "*.hm")))
    print(f"Processing {len(hm_files)} patterns...")

    results = []
    for hm_path in hm_files:
        stem = Path(hm_path).stem
        csv_path = tiff_dir / f"{stem}_spots.csv"
        if not csv_path.exists():
            print(f"  Skipping {stem}: no spots CSV")
            continue

        outpath = out_dir / f"{stem}_overlay.tiff"
        result = run_overlay_single(
            str(hm_path), str(csv_path), str(outpath),
            btx=btx, bty=bty,
        )
        result["filename"] = stem
        results.append(result)
        print(f"  {stem}: {result['n_matched']}/{result['n_experimental']} matched")

    # summary
    print(f"\nOverlay complete. Results in {out_dir}/")
    for r in results:
        print(f"  {r['filename']}: {r['n_matched']}/{r['n_experimental']} matched, "
              f"{r['n_predicted']} predicted on detector")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str,
                        default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--file", type=str, default=None,
                        help="Single .hm file to process")
    parser.add_argument("--btx", type=float, default=-814.0)
    parser.add_argument("--bty", type=float, default=135.0)
    args = parser.parse_args()

    if args.file:
        data_dir = Path(args.dir)
        stem = Path(args.file).stem
        csv_path = data_dir / "tiff_exports" / f"{stem}_spots.csv"
        out_dir = data_dir / "simulation_overlays"
        out_dir.mkdir(exist_ok=True)
        outpath = out_dir / f"{stem}_overlay.tiff"
        run_overlay_single(args.file, str(csv_path), str(outpath),
                           btx=args.btx, bty=args.bty)
    else:
        run_overlay_all(args.dir, btx=args.btx, bty=args.bty)
