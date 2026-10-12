#!/usr/bin/env python3
"""Off-axis hologram and matching vacuum reference hologram from an image wave (new stage; audit M1).

Runs in: em-holography (CPU; numpy, scipy for Fresnel edges).

    gemicro run --kind process --name hologram --input derived/image-wave/image_wave.npy \
        --params params/hologram.yaml --output derived/hologram -- /opt/envs/em-holography/bin/python \
        code/hologram_formation.py --params params/hologram.yaml --image-wave derived/image-wave \
        --output derived/hologram

Model (holo_optics): I = |O|² + |R|² + 2μ Re(O R*), O = a_o ψ_img E_o, R = a_r exp(-2πi q_c·r + iφ_d) E_r,
averaged over phonon configurations after squaring; then pixel integration (binning), detector MTF, dose and
Poisson noise. The reference hologram is the same with ψ_img = 1 (vacuum), the same biprism, distortion,
detector and gain map, and an independent noise realisation. μ = degree of coherence × |sinc(q_c·drift)|.

Writes: hologram.npy / hologram_clean.npy, reference_hologram.npy / reference_hologram_clean.npy (counts,
float32), image_wave_detector.npy (the image wave at the detector pixel centres: what an ideal reconstruction
returns before its aperture; the validation truth), reference_distortion_phase.npy (φ_d, injected), overlap
mask, hologram.json (carrier, contrast budget, dose, seeds), PNGs.
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402
import holo_optics as ho  # noqa: E402
import holo_sideband as hs  # noqa: E402


def load_image_waves(stage):
    w = stage.array("image_wave")
    axes = stage.entry("image_wave")["axes"]
    if axes == ["x", "y"]:
        w = w[None]
    elif axes != ["config", "x", "y"]:
        raise SystemExit(f"unexpected image_wave axes {axes}")
    return w, stage.sampling("image_wave")


def binning_transfer(q, sampling, b):
    """Transfer of b×b pixel averaging at frequency q (discrete Dirichlet kernel), product over both axes."""
    t = 1.0
    for qi, d in zip(q, sampling):
        x = math.pi * qi * d
        t *= 1.0 if abs(math.sin(x)) < 1e-15 else math.sin(b * x) / (b * math.sin(x))
    return t


def read(P):
    p = {"seed": P.integer("seed", lo=0)}
    B = P.sub("biprism")
    p["spacing"] = B.num("fringe_spacing_A", lo=0.0, lo_open=True)
    p["orientation"] = B.num("fringe_orientation_deg", lo=-180.0, hi=180.0)
    p["overlap"] = B.num("overlap_width_A", lo=0.0, lo_open=True, allow_none=True)
    p["fresnel"] = B.num("fresnel_edge_width_A", lo=0.0)
    if p["overlap"] is None and p["fresnel"] > 0:
        raise hc.ParamError("biprism.fresnel_edge_width_A > 0 needs an overlap_width_A (the edges of the overlap)")
    R = P.sub("reference_wave")
    p["model"] = R.choice("model", ("R1_plane", "R3_distorted"))
    p["ratio"] = R.num("intensity_ratio", lo=0.0, lo_open=True)
    if p["model"] == "R3_distorted":
        p["curvature"] = R.num("curvature_rad")
        p["ramp"] = R.vec("ramp_rad", 2)
    else:
        p["curvature"], p["ramp"] = 0.0, [0.0, 0.0]
    C = P.sub("coherence")
    p["gamma"] = C.num("degree_of_coherence", lo=0.0, hi=1.0)
    p["drift"] = C.num("fringe_drift_A", lo=0.0)
    D = P.sub("detector")
    p["binning"] = D.integer("binning", lo=1, hi=16)
    M = D.sub("mtf")
    p["mtf_model"] = M.choice("model", ("none", "gaussian", "table"))
    p["mtf_sigma"] = M.num("sigma_px", lo=0.0) if p["mtf_model"] == "gaussian" else None
    p["mtf_table"] = M.req("table") if p["mtf_model"] == "table" else None
    p["dose"] = D.num("dose_e_per_A2", lo=0.0, lo_open=True)
    p["dose_ref"] = D.num("reference_dose_e_per_A2", lo=0.0, lo_open=True)
    p["cpe"] = D.num("counts_per_electron", lo=0.0, lo_open=True)
    p["gain_rms"] = D.num("gain_rms", lo=0.0, hi=0.5)
    return p


def run(P, image_dir, out):
    p = read(P)
    P.finish()
    stage = hc.Stage(image_dir, "image_wave")
    waves, samp = load_image_waves(stage)
    phys_in = stage.meta["physics"]
    b = p["binning"]
    nx, ny = (waves.shape[-2] // b) * b, (waves.shape[-1] // b) * b
    cropped = [int(waves.shape[-2] - nx), int(waves.shape[-1] - ny)]
    waves = waves[..., :nx, :ny]
    pix = (samp[0] * b, samp[1] * b)
    q_c = ho.carrier_vector(p["spacing"], p["orientation"])
    qn = float(np.linalg.norm(q_c))
    B = float(phys_in["band_limit_inv_A"])
    nyq_det = 0.5 / max(pix)
    nyq_fine = 0.5 / max(samp)
    ppf = p["spacing"] / max(pix)
    warnings = []
    if ppf < 3.0:
        raise SystemExit(f"{ppf:.2f} detector pixels per fringe: at least 3 are needed (fringes need 3-4 pixels); "
                         f"increase the fringe spacing or reduce the binning")
    if ppf < 4.0:
        warnings.append(f"{ppf:.2f} pixels per fringe (< 4): the sideband sits close to the detector Nyquist")
    if qn + B > nyq_det:
        raise SystemExit(f"sideband edge |q_c| + B = {qn + B:.3f} 1/Å exceeds the detector Nyquist {nyq_det:.3f} 1/Å "
                         f"(aliasing); increase the fringe spacing or narrow the objective aperture")
    if qn + B > nyq_fine:
        raise SystemExit(f"sideband edge {qn + B:.3f} 1/Å exceeds the simulation grid's Nyquist {nyq_fine:.3f} 1/Å")
    if qn < 3.0 * B:
        warnings.append(f"|q_c| = {qn:.3f} < 3 × object band limit {B:.3f} 1/Å: the sideband overlaps the "
                        f"autocorrelation |O|² of the centre band; the reconstruction will contain cross-talk")

    a_o = math.sqrt(1.0 / (1.0 + p["ratio"]))
    a_r = math.sqrt(p["ratio"] / (1.0 + p["ratio"]))
    mu = ho.coherence_factor(p["gamma"], p["drift"], q_c)
    shape = (nx, ny)
    phi_d = ho.reference_distortion(shape, samp, p["curvature"], p["ramp"])
    E_o, E_r = ho.biprism_edges(shape, samp, q_c, p["overlap"], p["fresnel"])
    I_obj = ho.hologram_intensity(waves, samp, q_c, a_o, a_r, mu, phi_d, E_o, E_r)
    I_ref = ho.hologram_intensity(np.ones((1,) + shape, complex), samp, q_c, a_o, a_r, mu, phi_d, E_o, E_r)

    det_shape = (nx // b, ny // b)
    mtf = ho.mtf_curve(det_shape, p["mtf_model"], p["mtf_sigma"], p["mtf_table"])
    I_obj_d = ho.apply_mtf(ho.bin_pixels(I_obj, b), mtf)
    I_ref_d = ho.apply_mtf(ho.bin_pixels(I_ref, b), mtf)
    rng_gain = np.random.default_rng([p["seed"], 3])
    gain = np.clip(1.0 + p["gain_rms"] * rng_gain.standard_normal(det_shape), 0.05, None)
    clean_o, noisy_o = ho.record(I_obj_d, p["dose"], pix, p["cpe"], gain, np.random.default_rng([p["seed"], 1]))
    clean_r, noisy_r = ho.record(I_ref_d, p["dose_ref"], pix, p["cpe"], gain, np.random.default_rng([p["seed"], 2]))

    psi_det = ho.resample_to_pixel_centres(waves.mean(axis=0), b)
    phi_d_det = ho.bin_pixels(phi_d, b)
    overlap = ho.bin_pixels(np.abs(E_o * E_r), b) > 0.5

    # contrast budget: predicted from the model, measured on the clean reference hologram
    f_cpx = [q_c[0] * pix[0], q_c[1] * pix[1]]
    mtf_qc = float(ho.mtf_value(math.hypot(*f_cpx), p["mtf_model"], p["mtf_sigma"], p["mtf_table"]))
    t_bin = binning_transfer(q_c, samp, b)
    mu_pred = mu * 2 * a_o * a_r / (a_o ** 2 + a_r ** 2) * mtf_qc * abs(t_bin)
    car = hs.locate_carrier(clean_r, pix, q_c / qn, 0.5 * qn)
    ap = hs.aperture_at_origin(det_shape, pix, 0.25 * qn, "hard", 0.0)
    cmap = hs.fringe_contrast_map(clean_r, car["index"], ap)
    mu_meas = float(np.median(cmap[overlap])) if overlap.any() else float("nan")

    units = f"counts ({p['cpe']} per electron)"
    out.save_array("hologram", noisy_o, units=units, axes=["x", "y"], sampling_A=pix,
                   description="object hologram with Poisson noise")
    out.save_array("hologram_clean", clean_o, units=units, axes=["x", "y"], sampling_A=pix,
                   description="object hologram, expected counts (no noise)")
    out.save_array("reference_hologram", noisy_r, units=units, axes=["x", "y"], sampling_A=pix,
                   description="vacuum reference hologram with Poisson noise (same biprism, detector, gain)")
    out.save_array("reference_hologram_clean", clean_r, units=units, axes=["x", "y"], sampling_A=pix,
                   description="vacuum reference hologram, expected counts")
    out.save_array("image_wave_detector", psi_det, units="dimensionless", axes=["x", "y"], sampling_A=pix,
                   description="phonon-averaged image wave at the detector pixel centres (validation truth "
                               "before the reconstruction aperture; never read by the reconstruction)")
    out.save_array("reference_distortion_phase", phi_d_det, units="rad", axes=["x", "y"], sampling_A=pix,
                   description="phase φ_d injected on the reference wave (model R3), pixel-averaged")
    out.save_array("overlap_mask", overlap, units="bool", axes=["x", "y"], sampling_A=pix,
                   description="pixels inside the biprism overlap (|E_o E_r| > 0.5)")

    zx, zy = min(det_shape[0], 96), min(det_shape[1], 96)
    plots = [hc.plot_map(out, "hologram_zoom.png", noisy_o[:zx, :zy], f"object hologram (corner {zx}×{zy} px)",
                         pix, units, cmap="gray"),
             hc.plot_map(out, "hologram.png", noisy_o, "object hologram", pix, units, cmap="gray"),
             hc.plot_map(out, "reference_hologram.png", noisy_r, "vacuum reference hologram", pix, units,
                         cmap="gray"),
             hc.plot_spectrum(out, "hologram_spectrum.png", noisy_o, pix, "object hologram |FFT|: carrier ± q_c",
                              circles=[(q_c[0], q_c[1], B, "c"), (-q_c[0], -q_c[1], B, "c"), (0, 0, 2 * B, "w")])]
    physics = {
        "carrier_inv_A": q_c.tolist(), "fringe_spacing_A": p["spacing"], "fringe_orientation_deg": p["orientation"],
        "sideband_convention": "the sideband at +q_c (numpy FFT) carries psi_img · exp(-i phi_d): +object phase",
        "pixels_per_fringe": ppf, "detector_pixel_A": list(pix), "binning": b, "cropped_fine_pixels": cropped,
        "detector_shape": list(det_shape), "detector_nyquist_inv_A": nyq_det,
        "object_band_limit_inv_A": B, "carrier_over_band_limit": qn / B if B > 0 else None,
        "biprism": {"overlap_width_A": p["overlap"], "fresnel_edge_width_A": p["fresnel"],
                    "overlap_fraction": float(overlap.mean())},
        "reference_wave": {"model": p["model"], "intensity_ratio": p["ratio"], "amp_obj": a_o, "amp_ref": a_r,
                           "curvature_rad": p["curvature"], "ramp_rad": p["ramp"]},
        "contrast": {"degree_of_coherence": p["gamma"], "fringe_drift_A": p["drift"],
                     "drift_factor": abs(float(np.sinc(qn * p["drift"]))), "mu_interference": mu,
                     "beam_ratio_factor": 2 * a_o * a_r / (a_o ** 2 + a_r ** 2), "mtf_at_carrier": mtf_qc,
                     "pixel_integration_at_carrier": t_bin, "predicted_vacuum_contrast": mu_pred,
                     "measured_vacuum_contrast_clean_reference": mu_meas},
        "detector": {"mtf_model": p["mtf_model"], "mtf_sigma_px": p["mtf_sigma"], "mtf_table": p["mtf_table"],
                     "dose_e_per_A2": p["dose"], "reference_dose_e_per_A2": p["dose_ref"],
                     "counts_per_electron": p["cpe"], "gain_rms": p["gain_rms"],
                     "vacuum_counts_per_pixel": p["dose"] * pix[0] * pix[1] * p["cpe"],
                     "noise_order": "pixel integration -> MTF on the expected intensity -> Poisson (white noise)"},
        "seeds": {"object_noise": [p["seed"], 1], "reference_noise": [p["seed"], 2], "gain_map": [p["seed"], 3]},
        "energy_keV": phys_in["energy_keV"], "wavelength_A": phys_in["wavelength_A"],
        "image_wave_sidecar": str(stage.sidecar_path), "n_configs_averaged": int(waves.shape[0]),
        "image_wave": {"spot": phys_in["spot"], "tilt_mrad": phys_in["tilt_mrad"]},  # carried to recon/step height
        "warnings": warnings}
    summary = {"detector_shape": list(det_shape), "pixel_A": [round(v, 5) for v in pix],
               "fringe_spacing_A": p["spacing"], "pixels_per_fringe": round(ppf, 3),
               "carrier_over_band_limit": round(qn / B, 3) if B > 0 else None,
               "vacuum_counts_per_pixel": round(physics["detector"]["vacuum_counts_per_pixel"], 2),
               "contrast_predicted": round(mu_pred, 4), "contrast_measured_clean_ref": round(mu_meas, 4),
               "reference_model": p["model"], "plots": [x for x in plots if x], "warnings": warnings}
    return physics, summary, stage


def main(argv=None):
    ap = hc.common_cli("Off-axis object + reference holograms (env: em-holography)",
                       [("--image-wave", "output folder of specular_filter.py")])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    with hc.Output(a.output, a.overwrite) as out:
        physics, summary, stage = run(hc.Section(raw), a.image_wave, out)
        prov = hc.provenance(sys.argv, a.params, {"image_wave_sidecar": stage.sidecar_path},
                             seeds=physics["seeds"])
        hc.write_sidecar(out, "hologram", raw, prov, physics, summary)
        out.publish()
    hc.print_summary("holograms", summary, out.final, out.files)


if __name__ == "__main__":
    main()
