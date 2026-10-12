#!/usr/bin/env python3
"""Objective-aperture selection of one spot of the exit wave: the image wave that enters the biprism.

Runs in: em-holography (CPU; numpy). Also runs in em-abtem.

    gemicro run --kind process --name image-wave --input sims/exit-wave/exit_wave.npy \
        --params params/specular_filter.yaml --output derived/image-wave -- /opt/envs/em-holography/bin/python \
        code/specular_filter.py --params params/specular_filter.yaml --exit-wave sims/exit-wave \
        --slab sims/slab --output derived/image-wave

In the si110 pipeline this script Fourier-selected a spot of the simulated complex wave and called the
argument of the result "the holographic phase" (audit M1). Here it does only what a microscope does before
the biprism: an objective aperture (bright field around the direct beam, or dark field around a reflection),
optional defocus and Cs, and recentring of the selected beam. The hologram is formed by hologram_formation.py
and reconstructed by holo_recon.py, from intensities only.

Fixes (audit A): the spot vector is computed from the crystal (g in the slab frame; abTEM's incident-beam frame
puts it at q = g_xy for any tilt: C7), forbidden reflections are refused, the tilt of a series is selected by
value (C5), the pixel size is read from the exit wave's sidecar (C6), the aperture is in mrad (M6), the
spot is moved to q = 0 by an exact phase ramp (M13), and the measured centroid of the spot is reported next
to the prediction instead of replacing it (C3).
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402
import holo_optics as ho  # noqa: E402


def load_exit_waves(stage, tilt_select, tol):
    """(waves (n_cfg, nx, ny), tilt, sampling) from an exit_wave stage; a tilt series is selected by value."""
    phys = stage.meta["physics"]
    if stage.has("exit_waves"):
        if tilt_select is None:
            raise hc.ParamError("the exit wave is a tilt series: set tilt_select_mrad to the [θx, θy] to use")
        tilts = np.asarray(stage.array("tilts_mrad"), float)
        d = np.hypot(*(tilts - np.asarray(tilt_select)).T)
        i = int(np.argmin(d))
        if d[i] > tol:
            raise SystemExit(f"no tilt within {tol} mrad of {tilt_select}; available: {tilts.tolist()}")
        w = stage.array("exit_waves")[i]
        return w, tilts[i].tolist(), stage.sampling("exit_waves")
    if tilt_select is not None:
        t = phys["tilts_mrad"][0]
        if math.hypot(t[0] - tilt_select[0], t[1] - tilt_select[1]) > tol:
            raise SystemExit(f"tilt_select_mrad {tilt_select} but the exit wave was simulated at {t}")
    w = stage.array("exit_wave")
    axes = stage.entry("exit_wave")["axes"]
    if axes == ["x", "y"]:
        w = w[None]
    elif axes != ["config", "x", "y"]:
        raise SystemExit(f"unexpected exit_wave axes {axes}")
    return w, phys["tilts_mrad"][0], stage.sampling("exit_wave")


def run(P, exit_dir, slab_dir, out):
    tilt_select = P.vec("tilt_select_mrad", 2, allow_none=True)
    tol = P.num("tilt_tolerance_mrad", lo=0.0, lo_open=True)
    S = P.sub("spot")
    mode = S.choice("mode", ("direct_beam", "hkl", "vector"))
    O = P.sub("objective")
    radius_mrad = O.num("radius_mrad", lo=0.0, lo_open=True)
    edge = O.choice("edge", ("hard", "hann", "hamming", "tanh"))
    taper_mrad = O.num("taper_mrad", lo=0.0)
    defocus = O.num("defocus_A")
    Cs = O.num("Cs_mm") * 1e7
    refine_r = S.num("refine_radius_inv_A", lo=0.0, lo_open=True, allow_none=True)

    stage = hc.Stage(exit_dir, "exit_wave")
    waves, tilt, samp = load_exit_waves(stage, tilt_select, tol)
    energy = stage.meta["physics"]["energy_keV"]
    lam = hc.wavelength_A(energy)
    spot_info = {"mode": mode}
    if mode == "direct_beam":
        q_spot = np.zeros(2)
    elif mode == "vector":
        q_spot = np.asarray(S.vec("q_inv_A", 2))
    else:
        hkl = S.vec("hkl", 3, integer=True)
        if slab_dir is None:
            raise SystemExit("spot.mode: hkl needs --slab (the slab.json frame and lattice constant)")
        slab = hc.Stage(slab_dir, "slab").meta["physics"]
        F = ho.diamond_structure_factor(hkl)
        if abs(F) < 1e-9:
            raise SystemExit(f"{hkl} is kinematically forbidden in diamond-cubic Si (F = 0)")
        g = ho.spot_vector(hkl, slab["lattice_constant_A"], slab["frame"]["rows_in_crystal_coordinates"])
        if abs(g[2]) > 1e-6:
            raise SystemExit(f"{hkl} has a component {g[2]:.4g} 1/Å along the beam: not in the zero-order Laue "
                             f"zone of this exit wave")
        q_spot = g[:2]
        spot_info.update({"hkl": hkl, "abs_F_over_f": abs(F), "g_slab_inv_A": g.tolist()})
    P.finish()

    radius_q = radius_mrad * 1e-3 / lam
    taper_q = taper_mrad * 1e-3 / lam
    cutoff = stage.meta["physics"]["antialias_cutoff_inv_A"]
    if math.hypot(*q_spot) + radius_q > cutoff:
        raise SystemExit(f"aperture edge at {math.hypot(*q_spot) + radius_q:.3f} 1/Å lies beyond the simulation's "
                         f"band limit {cutoff:.3f} 1/Å (sampling too coarse for this spot and aperture)")
    spot_info["predicted_q_inv_A"] = q_spot.tolist()
    spot_info["predicted_mrad"] = (1e3 * lam * q_spot).tolist()
    if refine_r is not None:
        q_ref, frac = ho.refine_spot(waves, samp, q_spot, refine_r)
        spot_info.update({"centroid_q_inv_A": q_ref.tolist(), "centroid_minus_predicted_inv_A":
                          (q_ref - q_spot).tolist(), "fraction_of_intensity_in_refine_radius": frac})

    T, A = ho.objective_transfer(waves.shape[-2:], samp, q_spot, radius_q, edge, taper_q, lam, defocus, Cs)
    F = np.fft.fft2(waves, axes=(-2, -1))
    selected = np.fft.ifft2(F * T, axes=(-2, -1))
    img = ho.shift_by_phase_ramp(selected, samp, q_spot)  # selected beam to q = 0 (exact, sub-pixel)
    frac_in = float((np.abs(F * A) ** 2).sum() / (np.abs(F) ** 2).sum())

    arr = img[0] if img.shape[0] == 1 else img
    axes = ["x", "y"] if img.shape[0] == 1 else ["config", "x", "y"]
    out.save_array("image_wave", arr, units="dimensionless (vacuum amplitude 1 for the direct beam)", axes=axes,
                   sampling_A=samp, description="exit wave through the objective aperture centred on the "
                                                "selected spot, recentred to q = 0 (the wave entering the biprism)")
    out.save_array("objective_aperture", np.fft.fftshift(A), units="transmission", axes=["qx", "qy"],
                   sampling_A=[1.0 / (A.shape[0] * samp[0]), 1.0 / (A.shape[1] * samp[1])],
                   description="aperture |T| in the fftshifted Fourier plane of the exit wave; sampling in 1/Å")
    w0 = arr if arr.ndim == 2 else arr[0]
    plots = [hc.plot_spectrum(out, "exit_wave_spectrum.png", waves[0], samp,
                              f"exit wave |FFT| with the objective aperture ({radius_mrad} mrad)",
                              circles=[(q_spot[0], q_spot[1], radius_q, "c")]),
             hc.plot_map(out, "image_wave_phase.png", np.angle(w0), "image wave phase (wrapped)", samp, "rad",
                         cmap="twilight", vlim=(-np.pi, np.pi)),
             hc.plot_map(out, "image_wave_amplitude.png", np.abs(w0), "image wave amplitude", samp, "|ψ|")]
    physics = {"energy_keV": energy, "wavelength_A": lam, "tilt_mrad": tilt, "spot": spot_info,
               "objective": {"radius_mrad": radius_mrad, "radius_inv_A": radius_q, "edge": edge,
                             "taper_mrad": taper_mrad, "taper_inv_A": taper_q, "defocus_A": defocus,
                             "defocus_convention": "defocus = -C10 (abTEM)", "Cs_A": Cs,
                             "aberrations_relative_to": "the selected spot (centred dark field)"},
               "band_limit_inv_A": radius_q + 0.5 * taper_q, "fraction_of_intensity_selected": frac_in,
               "wave_plane": stage.meta["physics"]["wave_plane"] + (f"; then defocus {defocus} Å" if defocus else ""),
               "exit_wave_sidecar": str(stage.sidecar_path), "n_configs": int(img.shape[0])}
    summary = {"spot": mode if mode != "hkl" else f"hkl {spot_info['hkl']}", "tilt_mrad": tilt,
               "aperture_mrad": radius_mrad, "aperture_inv_A": round(radius_q, 5),
               "fraction_selected": round(frac_in, 5), "plots": [p for p in plots if p]}
    if "centroid_minus_predicted_inv_A" in spot_info:
        summary["centroid_minus_predicted_inv_A"] = [round(v, 5) for v in spot_info["centroid_minus_predicted_inv_A"]]
    return physics, summary, stage


def main(argv=None):
    ap = hc.common_cli("Objective-aperture spot selection -> image wave (env: em-holography)",
                       [("--exit-wave", "output folder of multislice_forward_model / tilt_series_runner")])
    ap.add_argument("--slab", default=None, help="output folder of si110_cleave_slab_generator (spot.mode: hkl)")
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    out = hc.Output(a.output, a.overwrite)
    physics, summary, stage = run(hc.Section(raw), a.exit_wave, a.slab, out)
    inputs = {"exit_wave_sidecar": stage.sidecar_path}
    hc.write_sidecar(out, "image_wave", raw, hc.provenance(sys.argv, a.params, inputs), physics, summary)
    out.publish()
    hc.print_summary("image wave", summary, out.final, out.files)


if __name__ == "__main__":
    main()
