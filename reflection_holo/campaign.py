"""Expansion of the campaign configuration into task lists, one list per stage.

Usage:
  python -m reflection_holo.campaign plan  --config configs/fir_m2_campaign.yaml --stage rocking --out RUN_DIR
  python -m reflection_holo.campaign check --config ... --stage all     (dry geometric check)

Every task is a self-contained dict (physics with labels, numerics, structure, beams);
task_id is a hash of its content, so re-planning an unchanged task reproduces the id
and finished results are reused.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys

import numpy as np

from .beams import plan_beam
from .constants import wavelength_A
from .crystal import SurfaceCell
from .grid import _fft_friendly

STAGES = ("validation", "convergence", "rocking", "steps")


def load_config(path):
    import yaml
    with open(path) as fh:
        return yaml.safe_load(fh)


def task_id(task):
    body = {k: v for k, v in task.items() if k not in ("task_id", "backend", "stage", "label", "cost")}
    return hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def numerics(cfg, preset="production", **over):
    num = copy.deepcopy(cfg["numerics"]["production"])
    num.update(copy.deepcopy(cfg["numerics"].get(preset, {})))
    num.update(over)
    return num


def ny_for(Ly, dy_target, tol=0.10):
    """FFT-friendly Ny (prime factors <= 7) whose dy = Ly/Ny is closest to dy_target
    (within tol relative)."""
    n0 = max(1, int(round(Ly / dy_target)))
    cands = [n for n in range(max(1, int(n0 * (1 - 2 * tol))), int(n0 * (1 + 2 * tol)) + 2)
             if _fft_friendly(n)]
    best = min(cands, key=lambda n: abs(Ly / n - dy_target)) if cands else None
    if best is None or abs(Ly / best - dy_target) > tol * dy_target:
        raise ValueError(f"no FFT-friendly Ny for Ly={Ly}")
    return best


def periods_for(surface, Ly_target, a):
    Py = SurfaceCell(surface, a).periods[1]
    return max(1, int(round(Ly_target / Py))), Py


def physics(cfg, **over):
    ph = copy.deepcopy(cfg["physics"])
    for k, v in over.items():
        ph[k] = dict(ph[k], value=v, label=ph[k]["label"] + " (scan value)")
    return ph


def make_task(cfg, stage, kind, surface, structure, beams, num, mode="static", seed=None,
              phys=None, label="", extra=None, variant="default"):
    """variant: "default" for the campaign's physics, otherwise the name of the
    sensitivity scan the task belongs to (used to group results)."""
    a = cfg["physics"]["lattice_parameter_A"]["value"]
    t = dict(stage=stage, kind=kind, backend=cfg["backend"], surface=surface,
             physics=phys if phys is not None else physics(cfg),
             numerics=dict(num), structure=dict(structure), mode=mode,
             beams=[dict(b) for b in beams], label=label, variant=variant)
    if seed is not None:
        t["seed"] = int(seed)
    if surface is not None:
        nyp = structure.get("n_y_periods", 1)
        Ly = SurfaceCell(surface, a).periods[1] * nyp
        t["numerics"]["Ny"] = ny_for(Ly, cfg["dy_target_A"])
    else:
        t["numerics"]["Ny"] = 1
    if extra:
        t.update(extra)
    t["task_id"] = task_id(t)
    return t


def windows(th_list, w0):
    return [dict(theta0_mrad=float(t), w0_A=float(w0)) for t in th_list]


def rocking_windows(sc):
    th = np.arange(sc["theta_min_mrad"], sc["theta_max_mrad"] + 1e-9, sc["theta_spacing_mrad"])
    n = sc["windows_per_task"]
    return [windows(th[i:i + n], sc["w0_A"]) for i in range(0, len(th), n)]


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------

def stage_validation(cfg):
    sc = cfg["stages"]["validation"]
    tasks = []
    num = numerics(cfg)
    # rung 1: refraction-only Fermi step versus Parratt
    for w in sc["rung1_widths_A"]:
        for W in sc["rung1_W_V"]:
            for th in sc["rung1_angles_mrad"]:
                tasks.append(make_task(
                    cfg, "validation", "uniform_1d", None, dict(kind="uniform"),
                    windows([th], sc["w0_A"]), num, phys=physics(cfg, inelastic_absorption_W_V=W),
                    label=f"rung1 Fermi step width {w} A, W {W} V, {th} mrad",
                    extra=dict(profile=dict(V0_V=sc["rung1_V0_V"], width_A=w,
                                            clearance_ref_A=2.0))))
    # rung 2: laterally averaged crystal versus Parratt, windows on the null-test angles
    for surf, angs in sc["null_test_angles_mrad"].items():
        for W in sc["rung2_W_V"]:
            tasks.append(make_task(
                cfg, "validation", "averaged_1d", surf, dict(kind="flat", level=0),
                windows(angs, sc["w0_A"]), num, phys=physics(cfg, inelastic_absorption_W_V=W),
                label=f"rung2 laterally averaged {surf}, W {W} V"))
    # rung 3: null tests (terrace ratios) and the a/4 residual, static lattice
    for surf, angs in sc["null_test_angles_mrad"].items():
        for lev in cfg["surfaces"][surf]["levels"]:
            tasks.append(make_task(
                cfg, "validation", "flat_rocking", surf, dict(kind="flat", level=lev),
                windows(angs, sc["w0_A"]), num, label=f"rung3 terrace level {lev} of {surf}"))
    # beam independence: same structure, different waists (taller cell)
    for w0 in sc["beam_waists_A"]:
        tasks.append(make_task(
            cfg, "validation", "flat_rocking", "si111_110", dict(kind="flat", level=0),
            windows([13.3], w0), numerics(cfg, "tall"), label=f"beam waist {w0} A"))
    return tasks


def stage_convergence(cfg):
    """Variants of the production numerics on the same structure and windows.

    role "gate": a refinement of the production numerics (finer sampling, longer
    delay, wider or stronger absorber, larger phonon cell); its disagreement with
    production beyond the tolerance blocks the production stages.  role "info": a
    comparison that is expected to differ (coarser sampling, single precision,
    Fresnel propagator, weaker absorber) and is reported only."""
    sc = cfg["stages"]["convergence"]
    tasks = []
    base_w = windows(sc["angles_mrad"], sc["w0_A"])
    st = dict(kind="flat", level=0)
    prod = numerics(cfg)

    def add(num, label, role, c=None):
        tasks.append(make_task(c or cfg, "convergence", "flat_rocking", "si111_110", st, base_w,
                               num, label=label, extra=dict(convergence_role=role)))
    Lx = prod["Nx"] * prod["dx_A"]
    for Nx in sc["Nx_list"]:
        dx = Lx / int(Nx)                      # same cell height: geometry unchanged
        num = numerics(cfg, Nx=int(Nx), dx_A=float(dx))
        c = copy.deepcopy(cfg)
        c["dy_target_A"] = cfg["dy_target_A"] * dx / prod["dx_A"]
        is_prod = int(Nx) == prod["Nx"]
        role = "reference" if is_prod else ("gate" if dx < prod["dx_A"] else "info")
        add(num, f"sampling dx={dx:.4f} A" + (" (production)" if is_prod else ""), role, c)
    add(numerics(cfg, precision="complex64"), "precision complex64", "info")
    add(numerics(cfg, propagator="fresnel"), "Fresnel propagator", "info")
    for n in sc["delay_decay_lengths"]:
        if float(n) == prod["delay_decay_lengths"]:
            continue
        add(numerics(cfg, delay_decay_lengths=float(n)), f"delay {n} decay lengths",
            "gate" if n > prod["delay_decay_lengths"] else "info")
    for tol in sc.get("tail_tol", []):
        add(numerics(cfg, tail_tol=float(tol)), f"tail tolerance {tol}",
            "gate" if tol < prod["tail_tol"] else "info")
    for width, Wmax in sc["absorber"]:
        stronger = (width >= prod["absorber_bottom_width_A"] and Wmax >= prod["absorber_W_max_V"])
        add(numerics(cfg, absorber_bottom_width_A=float(width), absorber_W_max_V=float(Wmax)),
            f"absorber {width} A, {Wmax} V", "gate" if stronger else "info")
    for nyp in sc["phonon_Ly_periods"]:
        for seed in range(sc["phonon_configs"]):
            tasks.append(make_task(cfg, "convergence", "flat_rocking", "si111_110",
                                   dict(kind="flat", level=0, n_y_periods=int(nyp)),
                                   windows(sc["phonon_angles_mrad"], sc["w0_A"]), numerics(cfg),
                                   mode="frozen_phonon", seed=1000 * nyp + seed,
                                   label=f"phonon Ly={nyp} periods seed {seed}",
                                   extra=dict(convergence_role="info")))
    return tasks


def stage_rocking(cfg):
    sc = cfg["stages"]["rocking"]
    a = cfg["physics"]["lattice_parameter_A"]["value"]
    tasks = []
    groups = rocking_windows(sc)
    num = numerics(cfg)
    for surf, info in cfg["surfaces"].items():
        for lev in info["levels"]:
            flat_st = dict(kind="flat", level=lev)
            for g in groups:
                tasks.append(make_task(cfg, "rocking", "flat_rocking", surf, flat_st, g, num,
                                       label=f"{surf} level {lev} static"))
                if lev == 0:
                    tasks.append(make_task(cfg, "rocking", "flat_rocking", surf, flat_st, g, num,
                                           mode="debye_waller", variant="debye_waller",
                                           label=f"{surf} level 0 Debye-Waller"))
                    for W in sc["W_scan_V"]:
                        tasks.append(make_task(cfg, "rocking", "flat_rocking", surf, flat_st, g, num,
                                               phys=physics(cfg, inelastic_absorption_W_V=W),
                                               variant=f"W={W}", label=f"{surf} level 0 W {W} V"))
                    for w in sc["onset_scan_A"]:
                        tasks.append(make_task(cfg, "rocking", "flat_rocking", surf, flat_st, g, num,
                                               phys=physics(cfg, absorption_onset_width_A=w),
                                               variant=f"onset={w}", label=f"{surf} level 0 onset {w} A"))
                    tasks.append(make_task(cfg, "rocking", "flat_rocking", surf, flat_st, g, num,
                                           phys=physics(cfg, parametrization="lobato"),
                                           variant="lobato", label=f"{surf} level 0 Lobato"))
                nyp, _ = periods_for(surf, sc["phonon_Ly_target_A"], a)
                for seed in range(sc["phonon_configs"]):
                    tasks.append(make_task(cfg, "rocking", "flat_rocking", surf,
                                           dict(kind="flat", level=lev, n_y_periods=nyp), g, num,
                                           mode="frozen_phonon", seed=seed,
                                           label=f"{surf} level {lev} phonon {seed}"))
    return tasks


def auto_Nx(cfg, num, surface, max_level, theta_mrad, w0):
    """Smallest FFT-friendly Nx (same dx and x0) whose cell holds the detector line of
    a beam of waist w0 above a structure of the given top level."""
    a = cfg["physics"]["lattice_parameter_A"]["value"]
    from .crystal import TerraceStructure, flat
    lam = float(wavelength_A(cfg["physics"]["beam_energy_keV"]["value"]))
    cell = SurfaceCell(surface, a)
    ts = TerraceStructure(cell, Ly=cell.periods[1], x_bottom=-10.0, level=flat(0),
                          max_level=max_level)
    beam, z_hit = plan_beam(theta_mrad * 1e-3, w0, lam, num["clearance_sigmas"],
                            num["clearance_margin_A"], float(ts.cut(max_level)))
    top_in = beam.axis_height(0.0) + num["clearance_sigmas"] * beam.width_at(z_hit, lam)
    x_need = (top_in + num["detector_margin_A"] + num["detector_spacing_A"]
              + num["detector_top_margin_A"] + num["absorber_top_width_A"] + 1.0)
    n = int(np.ceil((x_need - num["x0_A"]) / num["dx_A"]))
    while not _fft_friendly(n):
        n += 1
    return max(n, num["Nx"])


def _hit_point(cfg, num, surface, max_level, theta_mrad, w0):
    a = cfg["physics"]["lattice_parameter_A"]["value"]
    from .crystal import TerraceStructure, flat
    lam = float(wavelength_A(cfg["physics"]["beam_energy_keV"]["value"]))
    cell = SurfaceCell(surface, a)
    ts = TerraceStructure(cell, Ly=cell.periods[1], x_bottom=-10.0, level=flat(0),
                          max_level=max_level)
    _, z_hit = plan_beam(theta_mrad * 1e-3, w0, lam, num["clearance_sigmas"],
                         num["clearance_margin_A"], float(ts.cut(max_level)))
    return z_hit


def stage_steps(cfg):
    """Explicit step runs.  Each item may set its own beam waist w0_A (default the
    stage's) and a list of waists w0_list_A (beam-dependence study); the cell height
    is chosen automatically (auto_Nx) unless the item names a preset."""
    sc = cfg["stages"]["steps"]
    a = cfg["physics"]["lattice_parameter_A"]["value"]
    tasks = []

    def item_numerics(item, surf, lev, th, w0):
        if "preset" in item:
            num = numerics(cfg, item["preset"], spectrum_qy_max_mrad=15.0)
        else:
            num = numerics(cfg, spectrum_qy_max_mrad=15.0)
            num["Nx"] = auto_Nx(cfg, num, surf, max(lev), th, w0)
        return num

    for item in sc["parallel"]:
        surf, lev = item["surface"], list(item["levels"])
        nyp, _ = periods_for(surf, item.get("Ly_target_A", sc["Ly_target_A"]), a)
        st = dict(kind="steps_parallel", levels=lev, n_y_periods=nyp)
        w0 = item.get("w0_A", sc["w0_A"])
        for th in item["angles_mrad"]:
            num = item_numerics(item, surf, lev, th, w0)
            w = windows([th], w0)
            tasks.append(make_task(cfg, "steps", "step_image", surf, st, w, num,
                                   label=f"parallel steps {surf} {lev} {th} mrad"))
            for L in sorted(set(lev)):    # flat references, one y period, same beam
                tasks.append(make_task(cfg, "steps", "flat_rocking", surf,
                                       dict(kind="flat", level=L, clearance_level=max(lev)), w, num,
                                       extra=dict(save_spectrum=True),
                                       label=f"reference flat {surf} level {L} {th} mrad"))
        for th in item.get("phonon_angles_mrad", []):
            num = item_numerics(item, surf, lev, th, w0)
            for seed in range(sc["phonon_configs"]):
                tasks.append(make_task(cfg, "steps", "step_image", surf, st, windows([th], w0),
                                       num, mode="frozen_phonon", seed=seed,
                                       label=f"parallel steps {surf} {lev} {th} mrad phonon {seed}"))
    for item in sc["transverse"]:
        surf, lev = item["surface"], list(item["levels"])
        for w0 in item.get("w0_list_A", [item.get("w0_A", sc["w0_A"])]):
            for th in item["angles_mrad"]:
                num = item_numerics(item, surf, lev, th, w0)
                z_edge = _hit_point(cfg, num, surf, max(lev), th, w0)
                st = dict(kind="steps_transverse", levels=lev, edges_z_A=[float(z_edge)],
                          n_y_periods=1)
                w = windows([th], w0)
                tasks.append(make_task(cfg, "steps", "step_image", surf, st, w, num,
                                       label=item.get("label", f"transverse step {surf} {lev} {th} mrad")
                                       + f" w0 {w0} A"))
                for L in sorted(set(lev)):
                    tasks.append(make_task(cfg, "steps", "flat_rocking", surf,
                                           dict(kind="flat", level=L, clearance_level=max(lev)), w, num,
                                           extra=dict(save_spectrum=True),
                                           label=f"reference flat {surf} level {L} {th} mrad w0 {w0} A"))
    return tasks


BUILDERS = dict(validation=stage_validation, convergence=stage_convergence,
                rocking=stage_rocking, steps=stage_steps)


def build(cfg, stage):
    stages = STAGES if stage == "all" else (stage,)
    tasks = []
    for s in stages:
        tasks.extend(BUILDERS[s](cfg))
    ids = [t["task_id"] for t in tasks]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        # identical tasks requested twice (e.g. a flat reference shared by two step
        # items): keep one
        seen, uniq = set(), []
        for t in tasks:
            if t["task_id"] not in seen:
                uniq.append(t)
                seen.add(t["task_id"])
        tasks = uniq
    return tasks


# --------------------------------------------------------------------------
# dry geometric planning and cost model
# --------------------------------------------------------------------------

def dry_plan(task):
    """Geometry of a task without running it: grid, windows, detector lines, plane
    count, memory estimate.  Raises on any planning error (window outside the band,
    detector line above the top absorber, ...)."""
    from .simulate import (delay_allowance_A, make_grid, physics_value, plan_windows,
                           _max_level)
    from .constants import interaction_constant
    from .crystal import TerraceStructure, flat
    num = task["numerics"]
    E = float(physics_value(task, "beam_energy_keV"))
    lam = float(wavelength_A(E))
    sigma = interaction_constant(E)
    a = physics_value(task, "lattice_parameter_A")
    if task["kind"] == "uniform_1d":
        Ly = num["dx_A"]
        x_top = task["profile"]["clearance_ref_A"]
        dzp = num["uniform_dz_A"]
    else:
        cell = SurfaceCell(task["surface"], a)
        Ly = cell.periods[1] * task["structure"].get("n_y_periods", 1)
        ts = TerraceStructure(cell, Ly=cell.periods[1], x_bottom=-10.0, level=flat(0),
                              max_level=max(0, _max_level(task)))
        x_top = float(ts.cut(_max_level(task)))
        if task["kind"] == "averaged_1d":
            x_top = float(ts.cut0)
        dzp = ts.slice_thickness()
    grid = make_grid(num, Ly)
    delay, _ = delay_allowance_A(task, sigma)
    beams, z_end, x_det, info = plan_windows(task, grid, lam, x_top, delay)
    n_planes = int(np.ceil(z_end.max() / dzp))                  # planned (minimum)
    n_cap = int(np.ceil(num["cell_cap_factor"] * z_end.max() / dzp))   # adaptive cap
    Ny = 1 if task["kind"] == "averaged_1d" else grid.Ny
    B = len(beams)
    itemsize = 16 if num["precision"] == "complex128" else 8
    mem = itemsize * (3 * B * grid.Nx * Ny + 2 * B * n_cap * Ny + 4 * grid.Nx * Ny)
    # cost unit: complex grid points times planes (FFT work) plus GEMM work for phonons
    fft_work = B * grid.Nx * Ny * n_planes
    gemm_work = 0.0
    if task.get("mode") == "frozen_phonon" or task["kind"] == "step_image":
        atoms_per_plane = 8.0 / a**3 * dzp * (-num["x0_A"] - num["atoms_bottom_margin_A"]) * Ly
        gemm_work = (2 / 3) ** 2 * grid.Nx * Ny * atoms_per_plane * n_planes
        if task.get("mode") != "frozen_phonon":
            gemm_work = 0.0
        else:
            fft_work += grid.Nx * Ny * n_planes      # transmission function of every plane
    return dict(Nx=grid.Nx, Ny=Ny, B=B, n_planes=n_planes, n_planes_cap=n_cap,
                z_end_max_A=float(z_end.max()),
                memory_GB=mem / 1e9, fft_work=float(fft_work), gemm_work=float(gemm_work),
                windows=info)


def write_tasks(tasks, out_dir, stage):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"tasks_{stage}.jsonl")
    with open(path, "w") as fh:
        for t in tasks:
            fh.write(json.dumps(t, sort_keys=True) + "\n")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("plan", "check"))
    ap.add_argument("--config", required=True)
    ap.add_argument("--stage", required=True, choices=STAGES + ("all",))
    ap.add_argument("--out", default=None)
    ap.add_argument("--backend", default=None, help="override the backend (numpy for CPU tests)")
    ap.add_argument("--benchmark", default=None, help="benchmark.json from the GPU self-test")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    if args.backend:
        cfg["backend"] = args.backend
    stages = STAGES if args.stage == "all" else (args.stage,)
    bench = None
    if args.benchmark:
        with open(args.benchmark) as fh:
            bench = json.load(fh)
    grand = 0.0
    for s in stages:
        tasks = build(cfg, s)
        costs = []
        for t in tasks:
            p = dry_plan(t)
            t["cost"] = dict(fft_work=p["fft_work"], gemm_work=p["gemm_work"],
                             n_planes=p["n_planes"], memory_GB=p["memory_GB"])
            if p["memory_GB"] > 70.0:
                raise ValueError(f"task {t['task_id']} needs {p['memory_GB']:.1f} GB")
            costs.append(p)
        line = (f"stage {s}: {len(tasks)} tasks, max planes {max(c['n_planes'] for c in costs)}, "
                f"max memory {max(c['memory_GB'] for c in costs):.2f} GB")
        if bench:
            secs = sum(c["fft_work"] / bench["fft_points_per_s"] + c["gemm_work"] / bench["gemm_points_per_s"]
                       for c in costs)
            grand += secs
            line += f", estimated {secs / 3600:.2f} GPU-hours ({secs / 3600 / 4:.2f} h on 4 GPUs)"
        print(line)
        if args.action == "plan":
            if not args.out:
                sys.exit("--out is required for plan")
            path = write_tasks(tasks, args.out, s)
            print(f"  wrote {path}")
    if bench:
        print(f"total estimate {grand / 3600:.2f} GPU-hours")


if __name__ == "__main__":
    main()
