#!/usr/bin/env python3
"""Off-axis hologram reconstruction: sideband selection, reference normalisation, amplitude, phase, unwrapping.

Runs in: em-holography (CPU; numpy, scikit-image, HoloSpy 0.3). No GPU needed: a 2048² hologram takes seconds.

    gemicro run --kind analysis --name holo-recon --input derived/hologram/hologram.npy \
        --input derived/hologram/reference_hologram.npy --params params/holo.yaml --output derived/holo-recon \
        -- /opt/envs/em-holography/bin/python code/holo_recon.py --params params/holo.yaml \
        --hologram derived/hologram --output derived/holo-recon

The reconstruction never reads the truth (image_wave_detector.npy); it reads hologram.npy and
reference_hologram.npy (and, for the noise prediction only, the dose bookkeeping in hologram.json).
Experimental holograms go through the same code after import_experimental_holograms.py.

Writes: wave.npy (complex64, normalised), amplitude.npy, phase_wrapped_raw.npy (no offset, no ramp),
phase_unwrapped.npy (offset to the reference region, optional ramp removed), phase_ramp.npy (zeros unless
ramp_removal is used), aperture.npy, phase_mask_sensitivity.npy, recon.json, PNGs.
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


def read(P):
    p = {"engine": P.choice("engine", ("holospy", "numpy")), "seed": P.integer("seed", lo=0)}
    S = P.sub("sideband")
    p["half_plane_deg"] = S.num("half_plane_deg", lo=-360.0, hi=360.0)
    p["exclude"] = S.num("exclude_radius_inv_A", lo=0.0)
    p["expected"] = S.vec("expected_carrier_inv_A", 2, allow_none=True)
    p["tol"] = S.num("tolerance_inv_A", lo=0.0, lo_open=True) if p["expected"] is not None else None
    A = P.sub("aperture")
    p["radius"] = A.num("radius_inv_A", lo=0.0, lo_open=True, allow_none=True)
    p["radius_frac"] = A.num("radius_fraction_of_carrier", lo=0.0, lo_open=True, hi=0.5, allow_none=True)
    if (p["radius"] is None) == (p["radius_frac"] is None):
        raise hc.ParamError("set exactly one of aperture.radius_inv_A and aperture.radius_fraction_of_carrier")
    p["edge"] = A.choice("edge", ("hard", "hann", "hamming", "tanh"))
    p["taper"] = A.num("taper_inv_A", lo=0.0)
    if p["engine"] == "holospy" and (p["edge"] != "tanh" or p["taper"] <= 0):
        raise hc.ParamError("engine: holospy uses HoloSpy's tanh aperture: set aperture.edge: tanh and "
                            "taper_inv_A > 0, or engine: numpy for hard/hann/hamming apertures")
    p["tukey"] = P.num("apodization_tukey_alpha", lo=0.0, hi=1.0)
    p["normalize"] = P.boolean("reference_normalization")
    p["region"] = P.vec("phase_reference_region", 4, allow_none=True)
    p["ramp"] = P.choice("ramp_removal", ("none", "plane_in_reference_region"))
    if p["ramp"] != "none" and p["region"] is None:
        raise hc.ParamError("ramp_removal needs a phase_reference_region (the plane is fitted there only)")
    p["scales"] = P.vec("mask_sensitivity_scales")
    return p


def reconstruct(holo, ref, pix, index, radius, edge, taper, engine, normalize):
    """Normalised complex wave from object (and reference) holograms with one sideband choice."""
    A = hs.aperture_at_origin(holo.shape, pix, radius, edge, taper)
    if engine == "holospy":
        sb_o = hs.sideband_holospy(holo, pix, index, radius, taper)
        sb_r = hs.sideband_holospy(ref, pix, index, radius, taper)
    else:
        sb_o = hs.sideband_numpy(holo, index, A)
        sb_r = hs.sideband_numpy(ref, index, A)
    if normalize:
        floor = 1e-6 * np.abs(sb_r).max()
        wave = sb_o / np.where(np.abs(sb_r) > floor, sb_r, floor)
    else:
        wave = sb_o / np.median(np.abs(sb_r))  # amplitude scale only; the reference phase is NOT removed
    return wave, A


def finish_phase(wave, region_mask, ramp_mode, pix, seed):
    """Offset (and optional ramp) referred to the reference region; returns unwrapped, raw wrapped, ramp."""
    raw = np.angle(wave)
    if region_mask is not None:
        wave = wave * np.exp(-1j * np.angle(wave[region_mask].mean()))
    unw = hs.unwrap(np.angle(wave), seed)
    if region_mask is not None:
        unw = unw - unw[region_mask].mean()
    ramp = np.zeros_like(unw)
    coef = None
    if ramp_mode == "plane_in_reference_region":
        ramp, coef = hs.fit_plane(unw, region_mask, pix)
        unw = unw - ramp
    return unw, raw, ramp, coef


def run(P, holo_dir, out):
    p = read(P)
    P.finish()
    st = hc.Stage(holo_dir, "hologram")
    holo = st.array("hologram").astype(np.float64)
    ref = st.array("reference_hologram").astype(np.float64)
    pix = st.sampling("hologram")
    if st.sampling("reference_hologram") != pix or holo.shape != ref.shape:
        raise SystemExit("object and reference holograms differ in shape or pixel size")
    meta = st.meta["physics"]
    energy = meta["energy_keV"]
    lam = hc.wavelength_A(energy)
    hp = math.radians(p["half_plane_deg"])
    car = hs.locate_carrier(ref, pix, (math.cos(hp), math.sin(hp)), p["exclude"], p["expected"], p["tol"])
    qn = math.hypot(*car["q_refined_inv_A"])
    radius = p["radius"] if p["radius"] is not None else p["radius_frac"] * qn
    if radius + 0.5 * p["taper"] > 0.5 * qn:
        raise SystemExit(f"aperture radius {radius:.3f} (+taper/2) exceeds half the carrier frequency {qn:.3f} 1/Å: "
                         f"it would include the centre band")
    region = hc.region_mask(holo.shape, p["region"]) if p["region"] is not None else None
    if region is not None and st.has("overlap_mask") and not st.array("overlap_mask")[region].all():
        raise SystemExit("the phase reference region extends outside the biprism overlap (pixels without fringes); "
                         "move phase_reference_region inside it")
    win = hs.tukey_window(holo.shape, p["tukey"])
    if region is not None and win[region].min() < 0.999:
        raise SystemExit("the phase reference region lies inside the apodisation taper; move it inwards or "
                         "reduce apodization_tukey_alpha")
    holo_raw, ref_raw = holo, ref
    holo, ref = holo * win, ref * win  # identical window on both: it cancels in the normalised wave

    wave, A = reconstruct(holo, ref, pix, car["index"], radius, p["edge"], p["taper"], p["engine"], p["normalize"])
    unw, raw, ramp, coef = finish_phase(wave, region, p["ramp"], pix, p["seed"])
    if region is not None:
        wave = wave * np.exp(-1j * np.angle(wave[region].mean()))
    amp = np.abs(wave)

    cross = None
    if p["engine"] == "holospy":
        w2, _ = reconstruct(holo, ref, pix, car["index"], radius, "tanh", p["taper"], "numpy", p["normalize"])
        d = np.angle(w2 * np.conj(wave))
        d = hs.wrap(d - np.angle(np.mean(np.exp(1j * d))))  # the two differ by the region offset only
        cross = float(np.abs(d).max())

    sens = []
    for s in p["scales"]:
        if (radius * s) + 0.5 * p["taper"] > 0.5 * qn:
            raise SystemExit(f"mask sensitivity scale {s}: radius {radius * s:.3f} 1/Å reaches the centre band")
        ws, _ = reconstruct(holo, ref, pix, car["index"], radius * s, p["edge"], p["taper"], "numpy",
                            p["normalize"])
        us, *_ = finish_phase(ws, region, p["ramp"], pix, p["seed"])
        sens.append(us)

    # contrast and noise budget, measured on the holograms themselves
    Ah = hs.aperture_at_origin(holo.shape, pix, 0.25 * qn, "hard", 0.0)
    cmap_r = hs.fringe_contrast_map(ref_raw, car["index"], Ah)
    ov = st.array("overlap_mask") if st.has("overlap_mask") else np.ones(holo.shape, bool)
    vac = region if region is not None else ov
    mu_ref = float(np.median(cmap_r[ov]))
    cpe = meta.get("detector", {}).get("counts_per_electron", 1.0)
    area = ho.aperture_area(A, holo.shape, pix)
    dose_o = float(holo_raw[vac & ov].mean()) / (cpe * pix[0] * pix[1])
    dose_r = float(ref_raw[ov].mean()) / (cpe * pix[0] * pix[1])
    sigma_pred = ho.predicted_phase_noise(mu_ref, dose_o, dose_r if p["normalize"] else None, area)
    sigma_obj = ho.predicted_phase_noise(mu_ref, dose_o, None, area)  # object-hologram part (vacuum)
    sigma_ref = ho.predicted_phase_noise(mu_ref, dose_r, None, area) if p["normalize"] else 0.0
    warnings = []
    vac_std = float(unw[vac].std()) if vac is not None else None
    if vac_std is not None and vac_std > 2.0 * sigma_pred:
        warnings.append(f"reference-region phase std {vac_std:.4f} rad is {vac_std / sigma_pred:.1f} × the shot-noise "
                        f"prediction: not a flat vacuum region, residues, or a reconstruction problem")
    resid = hs.count_residues(np.where(ov & (win > 0.5), np.angle(wave), 0.0))  # not where the window ~ 0
    try:
        hstat = hs.holospy_statistics(ref_raw, pix, car["q_refined_inv_A"], energy)
    except Exception as e:  # report HoloSpy problems, do not hide them; the numpy numbers stand on their own
        hstat = {"error": repr(e)}

    out.save_array("wave", wave, units="dimensionless (object/reference)", axes=["x", "y"], sampling_A=pix,
                   description="reconstructed complex wave, phase offset to the reference region")
    out.save_array("amplitude", amp, units="relative to vacuum", axes=["x", "y"], sampling_A=pix,
                   description="|wave|")
    out.save_array("phase_wrapped_raw", raw, units="rad", axes=["x", "y"], sampling_A=pix,
                   description="arg of the normalised sideband wave: no offset, no ramp, no unwrapping")
    out.save_array("phase_unwrapped", unw, units="rad", axes=["x", "y"], sampling_A=pix,
                   description="2-D unwrapped phase (skimage Herráez), mean of the reference region = 0, "
                               "minus phase_ramp")
    out.save_array("phase_ramp", ramp, units="rad", axes=["x", "y"], sampling_A=pix,
                   description="fitted plane removed from phase_unwrapped (zeros when ramp_removal: none)")
    out.save_array("aperture", A, units="transmission", axes=["qx", "qy"],
                   sampling_A=[1.0 / (A.shape[0] * pix[0]), 1.0 / (A.shape[1] * pix[1])],
                   description="sideband aperture, unshifted FFT layout centred at q = 0 (sampling in 1/Å)")
    out.save_array("phase_mask_sensitivity", np.asarray(sens) if sens else np.zeros((0,) + unw.shape),
                   units="rad", axes=["scale", "x", "y"], sampling_A=pix,
                   description=f"phase_unwrapped repeated with the aperture radius × {p['scales']} (numpy engine)")

    qc = np.asarray(car["q_refined_inv_A"])
    plots = [hc.plot_map(out, "phase.png", unw, "reconstructed phase (unwrapped)", pix, "rad", robust=True),
             hc.plot_map(out, "phase_wrapped_raw.png", raw, "raw wrapped phase", pix, "rad", cmap="twilight",
                         vlim=(-np.pi, np.pi)),
             hc.plot_map(out, "amplitude.png", amp, "reconstructed amplitude", pix, "|ψ|/|ψ_vac|", robust=True),
             hc.plot_spectrum(out, "sideband_selection.png", holo_raw, pix,
                              f"hologram |FFT|, selected sideband (r = {radius:.3f} 1/Å)",
                              circles=[(qc[0], qc[1], radius, "c"), (0, 0, p["exclude"], "w")])]
    physics = {"engine": p["engine"], "carrier": car, "aperture": {
        "radius_inv_A": radius, "radius_mrad": 1e3 * lam * radius, "edge": p["edge"], "taper_inv_A": p["taper"],
        "noise_equivalent_area_inv_A2": area, "resolution_A": 1.0 / radius,
        "resolution_in_fringe_spacings": (1.0 / radius) * qn},
        "reference_normalization": p["normalize"], "phase_reference_region": p["region"],
        "apodization_tukey_alpha": p["tukey"],
        "ramp_removal": p["ramp"], "ramp_coefficients": coef, "unwrapping": "skimage.restoration.unwrap_phase "
        "(Herráez et al. 2002), wrap_around False", "residues_in_overlap": resid,
        "residues_counted_where": "overlap and apodisation window > 0.5",
        "contrast_reference_median": mu_ref, "dose_object_e_per_A2": dose_o, "dose_reference_e_per_A2": dose_r,
        "predicted_vacuum_phase_noise_rad": sigma_pred,
        "predicted_noise_components_rad": {"object_hologram": sigma_obj, "reference_hologram": sigma_ref},
        "warnings": warnings,
        "measured_reference_region_phase_std_rad": float(unw[vac].std()) if vac is not None else None,
        "holospy_statistics_reference": hstat,
        "holospy_vs_numpy_max_abs_phase_diff_rad": cross, "mask_sensitivity_scales": p["scales"],
        "energy_keV": energy, "wavelength_A": lam, "hologram_sidecar": str(st.sidecar_path),
        "image_wave": meta.get("image_wave"), "detector_binning": meta.get("binning", 1)}
    summary = {"carrier_inv_A": [round(float(v), 5) for v in qc], "fringe_spacing_A": round(car["spacing_A"], 5),
               "aperture_radius_inv_A": round(radius, 5), "resolution_A": round(1.0 / radius, 3),
               "reference_normalization": p["normalize"], "contrast_ref": round(mu_ref, 4),
               "phase_range_rad": [round(float(unw.min()), 4), round(float(unw.max()), 4)],
               "reference_region_std_rad": None if vac is None else round(float(unw[vac].std()), 5),
               "predicted_noise_rad": round(sigma_pred, 5), "residues": resid,
               "holospy_vs_numpy_rad": cross, "plots": [x for x in plots if x], "warnings": warnings}
    return physics, summary, st


def main(argv=None):
    ap = hc.common_cli("Off-axis hologram reconstruction (env: em-holography)",
                       [("--hologram", "output folder of hologram_formation.py or import_experimental_holograms.py")])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    with hc.Output(a.output, a.overwrite) as out:
        physics, summary, st = run(hc.Section(raw), a.hologram, out)
        inputs = {"hologram": st.folder / st.entry("hologram")["file"],
                  "reference_hologram": st.folder / st.entry("reference_hologram")["file"],
                  "hologram_sidecar": st.sidecar_path}
        hc.write_sidecar(out, "recon", raw, hc.provenance(sys.argv, a.params, inputs), physics, summary)
        out.publish()
    hc.print_summary("reconstruction", summary, out.final, out.files)


if __name__ == "__main__":
    main()
