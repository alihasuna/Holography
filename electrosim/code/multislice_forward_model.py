#!/usr/bin/env python3
"""Plane-wave multislice exit wave with abTEM (replaces the prismatique 0.0.1 wrapper of the si110 pipeline).

Runs in: em-abtem (abTEM 1.0.10, ase, numpy; CuPy when device: gpu). GPU step of the pipeline.

    gemicro gpu
    gemicro run --kind sim --name exit-wave --input sims/slab/si110_slab.extxyz --params params/exit_wave.yaml \
        --output sims/exit-wave -- /opt/envs/em-abtem/bin/python code/multislice_forward_model.py \
        --params params/exit_wave.yaml --structure sims/slab/si110_slab.extxyz --output sims/exit-wave

Writes (all arrays [ix, iy], axis 0 = x):
  exit_wave.npy           complex64 (nx, ny), or (config, nx, ny) with frozen phonons; vacuum amplitude 1
  ground_truth_phase.npy  float32 σ·V_proj of the static structure (rad): the thin-object phase
  exit_wave.json          sampling, energy, λ, σ, tilt and its convention, the plane of the wave, abTEM band
                          limit, measured mean inner potential of the parametrisation, device and GPU memory
  exit_wave_phase.png, exit_wave_amplitude.png, ground_truth_phase.png

The plane of the saved wave (audit M4; the prismatique wave was the cell MID-plane): abTEM transmits and then
propagates each slice, so the wave is at the exit face of the potential box (z = box length along the beam).
Columns shorter than the box include the vacuum propagation to that plane.

Tilt convention: abTEM applies a plane-wave tilt by shearing the Fresnel propagator; the saved array is in the
frame of the incident beam (the direct beam is at q = 0, a reflection g at q = g_xy). abTEM recommends tilts
below about 1° (17 mrad) for this method; larger tilts are run with a warning (spec §4.3, milestone M2 test).
With device: gpu every array is copied to the host with .get() before numpy, np.save or plotting
(the "Implicit conversion to a NumPy array is not allowed" bug fixed in gemicro 0.5.6), and the CuPy memory
pools are released at the end.
"""

import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402

FFT_PRIMES = (2, 3, 5, 7)
SHEAR_TILT_LIMIT_MRAD = 17.0


def nice_size(n):
    """Smallest m >= n whose prime factors are 2, 3, 5, 7 (fast FFTs on CPU and GPU)."""
    m = max(int(n), 1)
    while True:
        k = m
        for p in FFT_PRIMES:
            while k % p == 0:
                k //= p
        if k == 1:
            return m
        m += 1


def read_settings(P):
    """All forward-model settings from the parameter file (shared with the tilt-series runner)."""
    s = {"energy_keV": P.num("energy_keV", lo=1.0), "device": P.choice("device", ("cpu", "gpu")),
         "seed": P.integer("seed", lo=0)}
    pot = P.sub("potential")
    s["sampling_A"] = pot.num("sampling_A", lo=0.005, hi=1.0)
    s["slice_thickness_A"] = pot.num("slice_thickness_A", lo=0.05, hi=20.0)
    s["parametrization"] = pot.choice("parametrization", ("lobato", "kirkland", "peng"))
    s["projection"] = pot.choice("projection", ("infinite", "finite"))
    fp = P.sub("frozen_phonons")
    s["num_configs"] = fp.integer("num_configs", lo=0)
    s["sigma_A"] = fp.num("sigma_A", lo=0.0)
    if s["num_configs"] > 0 and s["sigma_A"] == 0:
        raise hc.ParamError("frozen_phonons.num_configs > 0 needs sigma_A > 0 (or set num_configs: 0)")
    if s["num_configs"] == 0 and s["sigma_A"] != 0:
        raise hc.ParamError("frozen_phonons.sigma_A is set but num_configs is 0")
    lim = P.sub("limits")
    s["max_device_memory_GB"] = lim.num("max_device_memory_GB", lo=0.1)
    return s


def grid_for(atoms, sampling):
    L = np.diag(atoms.cell.array)
    if not np.allclose(atoms.cell.array, np.diag(L), atol=1e-8):
        raise SystemExit("the structure's cell must be orthogonal with the beam along z")
    gpts = [nice_size(math.ceil(L[i] / sampling)) for i in (0, 1)]
    return gpts, L


def memory_estimate_GB(gpts, n_slices):
    """Device bytes: wave, transmission function, propagator and FFT work arrays (complex64, ~6 copies) plus
    the potential slices (float32) if abTEM materialises them all."""
    n = gpts[0] * gpts[1]
    return (n * 8 * 6 + n * 4 * n_slices) / 1e9


def setup_device(device):
    import abtem
    abtem.config.set({"device": device, "precision": "float32"})
    info = {"device": device}
    if device == "gpu":
        try:
            import cupy as cp
        except ImportError as e:
            raise SystemExit(f"device: gpu but CuPy is not importable in this interpreter ({e}); run with "
                             f"/opt/envs/em-abtem/bin/python or set device: cpu")
        try:
            dev = cp.cuda.Device()
            free, total = dev.mem_info
            props = cp.cuda.runtime.getDeviceProperties(dev.id)
            info.update({"gpu_name": props["name"].decode() if isinstance(props["name"], bytes) else props["name"],
                         "gpu_total_GB": total / 1e9, "gpu_free_GB_at_start": free / 1e9})
        except Exception as e:  # report, do not hide: the run will fail visibly below if the GPU is unusable
            info["gpu_query_error"] = repr(e)
    return info


def release_device(device):
    if device != "gpu":
        return {}
    import cupy as cp
    pool = cp.get_default_memory_pool()
    rec = {"cupy_pool_total_GB_before_release": pool.total_bytes() / 1e9}
    pool.free_all_blocks()
    cp.get_default_pinned_memory_pool().free_all_blocks()
    rec["cupy_pool_total_GB_after_release"] = pool.total_bytes() / 1e9
    return rec


def displaced(atoms, sigma, seed):
    a = atoms.copy()
    rng = np.random.default_rng(seed)
    a.positions = a.positions + rng.normal(0.0, sigma, a.positions.shape)
    return a


def simulate(atoms, s, tilts_mrad):
    """Exit waves for every tilt and phonon configuration: complex64 host array (n_tilt, n_cfg, nx, ny)."""
    import abtem

    gpts, L = grid_for(atoms, s["sampling_A"])
    n_slices = math.ceil(L[2] / s["slice_thickness_A"])
    est = memory_estimate_GB(gpts, n_slices)
    if s["device"] == "gpu" and est > s["max_device_memory_GB"]:
        raise SystemExit(f"estimated device memory {est:.2f} GB > limits.max_device_memory_GB "
                         f"{s['max_device_memory_GB']} (grid {gpts}, {n_slices} slices): coarsen the sampling or "
                         f"reduce the cell; the H100 MIG slice (~12 GB) is shared")
    n_cfg = max(s["num_configs"], 1)
    out = np.empty((len(tilts_mrad), n_cfg, gpts[0], gpts[1]), np.complex64)
    energy = s["energy_keV"] * 1e3
    for c in range(n_cfg):
        at = atoms if s["num_configs"] == 0 else displaced(atoms, s["sigma_A"], s["seed"] + 1000 + c)
        pot = abtem.Potential(at, gpts=tuple(gpts), slice_thickness=s["slice_thickness_A"],
                              parametrization=s["parametrization"], projection=s["projection"])
        for t, tilt in enumerate(tilts_mrad):
            wave = abtem.PlaneWave(energy=energy, tilt=tuple(tilt)).multislice(pot)
            wave = wave.compute(progress_bar=False, scheduler="synchronous")
            out[t, c] = hc.to_host(wave.array)  # .get() for CuPy: never np.asarray on a device array
            del wave
    grid = {"gpts": gpts, "extent_A": [float(L[0]), float(L[1])], "box_length_along_beam_A": float(L[2]),
            "sampling_A": [float(L[0] / gpts[0]), float(L[1] / gpts[1])], "n_slices": n_slices,
            "device_memory_estimate_GB": est}
    return out, grid


def ground_truth(atoms, s, gpts):
    """σ·V_proj (rad) of the static structure, and V_proj itself (V·Å), both on the host."""
    import abtem
    from abtem.core.energy import energy2sigma
    pot = abtem.Potential(atoms, gpts=tuple(gpts), slice_thickness=s["slice_thickness_A"],
                          parametrization=s["parametrization"], projection=s["projection"])
    vproj = hc.to_host(pot.project().compute(progress_bar=False, scheduler="synchronous").array).astype(np.float64)
    sigma_abtem = float(energy2sigma(s["energy_keV"] * 1e3))
    return sigma_abtem * vproj, vproj, sigma_abtem


def mean_inner_potential(vproj, sampling, slab_meta):
    """V0 of the parametrisation: mean V_proj over the slab interior / thickness along the beam (needs slab.json)."""
    if slab_meta is None:
        return None
    g = slab_meta["physics"]["geometry"]
    t = g["z_last_atom_A"] - g["z_first_atom_A"] + 0.5 * g["period_z_A"]  # (220) planes every period_z/2
    margin = 2.0 * g["d_111_A"]
    x = (np.arange(vproj.shape[0]) + 0.5) * sampling[0]
    rows = (x > g["x_back_atom_A"] + margin) & (x < min(g["x_top_atom_A"]) - margin)
    if rows.sum() < 3:
        return None
    v0 = float(vproj[rows].mean() / t)
    return {"V0_parametrisation_V": v0, "thickness_along_beam_A": t, "region": "slab interior below the lowest "
            "terrace, 2 d_111 from the faces", "note": "compare with the sourced V0 (ASSUMPTION B1: 12.0 V; "
            "instrument file 12.5 V OPEN)"}


def load_structure(path):
    import ase.io
    atoms = ase.io.read(path)
    slab_json = Path(path).parent / "slab.json"
    slab_meta = json.loads(slab_json.read_text()) if slab_json.is_file() else None
    return atoms, slab_meta, (slab_json if slab_meta else None)


def write_outputs(out, waves, tilts, grid, s, atoms, slab_meta, gt, vproj, sigma_abtem, dev_info, series):
    lam = hc.wavelength_A(s["energy_keV"])
    sig = hc.interaction_constant(s["energy_keV"])
    samp = grid["sampling_A"]
    n_cfg = waves.shape[1]
    if series:
        arr, axes, name = waves, ["tilt", "config", "x", "y"], "exit_waves"
    elif n_cfg == 1 and s["num_configs"] == 0:
        arr, axes, name = waves[0, 0], ["x", "y"], "exit_wave"
    else:
        arr, axes, name = waves[0], ["config", "x", "y"], "exit_wave"
    out.save_array(name, arr, units="dimensionless (incident plane wave amplitude 1)", axes=axes, sampling_A=samp,
                   description="complex exit wave at the exit face of the potential box (abTEM plane-wave "
                               "multislice), in the incident-beam frame")
    if series:
        out.save_array("tilts_mrad", np.asarray(tilts, np.float32), units="mrad", axes=["tilt", "component"],
                       description="beam tilt (θx, θy) of each exit wave, abTEM PlaneWave(tilt=...)")
    out.save_array("ground_truth_phase", gt, units="rad", axes=["x", "y"], sampling_A=samp,
                   description="σ·V_proj of the static structure (projection approximation)")
    w0 = waves[0, 0]
    plots = [hc.plot_map(out, "exit_wave_phase.png", np.angle(w0), f"exit wave phase (tilt {tilts[0]} mrad)",
                         samp, "phase (rad)", cmap="twilight", vlim=(-np.pi, np.pi)),
             hc.plot_map(out, "exit_wave_amplitude.png", np.abs(w0), "exit wave amplitude", samp, "|ψ|"),
             hc.plot_map(out, "ground_truth_phase.png", gt, "ground truth σ·V_proj", samp, "phase (rad)")]
    mip = mean_inner_potential(vproj, samp, slab_meta)
    max_tilt = max(math.hypot(*t) for t in tilts)
    warnings = []
    if max_tilt > SHEAR_TILT_LIMIT_MRAD:
        warnings.append(f"tilt {max_tilt:.1f} mrad exceeds abTEM's recommended ~17 mrad for propagator-shear tilt; "
                        f"the spec's milestone M2 convergence test (shear vs Fourier-component tilt) applies")
    cutoff_mrad = 1e3 * lam * (2.0 / 3.0) / (2.0 * max(samp))
    physics = {"energy_keV": s["energy_keV"], "wavelength_A": lam, "sigma_rad_per_V_A": sig,
               "sigma_abtem_rad_per_V_A": sigma_abtem, "grid": grid, "tilts_mrad": [list(t) for t in tilts],
               "tilt_convention": "abTEM propagator-shear tilt; array in the incident-beam frame (direct beam at "
                                  "q = 0, reflection g at q = g_xy)",
               "wave_plane": "exit face of the potential box, z = box_length_along_beam_A (no propagation after)",
               "antialias_cutoff_mrad": cutoff_mrad,
               "antialias_cutoff_inv_A": cutoff_mrad / 1e3 / lam,
               "potential": {k: s[k] for k in ("slice_thickness_A", "parametrization", "projection")},
               "frozen_phonons": {"num_configs": s["num_configs"], "sigma_A": s["sigma_A"],
                                  "seeds": [s["seed"] + 1000 + c for c in range(s["num_configs"])]},
               "n_atoms": len(atoms), "mean_inner_potential": mip, "device": dev_info, "warnings": warnings}
    vac = None
    if slab_meta is not None:
        g = slab_meta["physics"]["geometry"]
        x = (np.arange(w0.shape[0]) + 0.5) * samp[0]
        rows = x > max(g["x_top_atom_A"]) + 10.0
        if rows.any():
            vac = float(np.abs(w0[rows]).std())
    summary = {"grid": grid["gpts"], "sampling_A": [round(v, 5) for v in samp], "slices": grid["n_slices"],
               "tilts_mrad": [list(t) for t in tilts], "configs": n_cfg, "device": s["device"],
               "phase_range_rad": [round(float(np.angle(w0).min()), 4), round(float(np.angle(w0).max()), 4)],
               "ground_truth_max_rad": round(float(gt.max()), 4),
               "V0_parametrisation_V": None if mip is None else round(mip["V0_parametrisation_V"], 3),
               "vacuum_amplitude_std": vac, "plots": [p for p in plots if p], "warnings": warnings}
    return physics, summary


def run(raw, structure, out, tilts=None, series=False, P=None):
    P = P or hc.Section(raw)
    s = read_settings(P)
    if tilts is None:
        tilts = [P.sub("illumination").vec("tilt_mrad", 2)]
    P.finish()
    atoms, slab_meta, slab_json = load_structure(structure)
    dev_info = setup_device(s["device"])
    t0 = time.time()
    waves, grid = simulate(atoms, s, tilts)
    gt, vproj, sigma_abtem = ground_truth(atoms, s, grid["gpts"])
    dev_info["simulation_time_s"] = round(time.time() - t0, 2)
    dev_info.update(release_device(s["device"]))
    physics, summary = write_outputs(out, waves, tilts, grid, s, atoms, slab_meta, gt, vproj, sigma_abtem,
                                     dev_info, series)
    summary["simulation_time_s"] = dev_info["simulation_time_s"]
    return physics, summary, {"structure": structure, "slab_json": slab_json}, s


def main(argv=None):
    ap = hc.common_cli("abTEM plane-wave exit wave (env: em-abtem, GPU)",
                       [("--structure", "structure file with an orthogonal cell (extxyz/CIF), beam along z")])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    out = hc.Output(a.output, a.overwrite)
    physics, summary, inputs, s = run(raw, a.structure, out)
    prov = hc.provenance(sys.argv, a.params, inputs, seeds={"phonons": physics["frozen_phonons"]["seeds"]})
    hc.write_sidecar(out, "exit_wave", raw, prov, physics, summary)
    out.publish()
    hc.print_summary("exit wave", summary, out.final, out.files)


if __name__ == "__main__":
    main()
