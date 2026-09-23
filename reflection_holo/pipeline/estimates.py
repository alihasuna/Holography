"""Dry run: validate a pipeline configuration and estimate its resources (no simulation).

Geometric engine: grid sizes from the staircase, the glancing angle and the engine sampling, memory
of the arrays the pipeline holds, and a time estimate scaled from the per-pixel and per-atom costs
MEASURED on the smoke demo on the build machine (4 CPUs; ``SMOKE_COSTS``; an estimate, not a
guarantee). Multislice engine: the structure and reflection cell are built and the engine's own
``forward.multislice.estimate_resources`` is called (memory from the arrays it allocates; GPU time
from its labelled ASSUMPTION model; CPU time measured on this machine only when
``calibrate_cpu`` is set).
"""
from __future__ import annotations

import math

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.pipeline.config import PipelineConfig

# Measured on the smoke demo (configs/demo_smoke_si001.yaml, 4 CPUs, 2026-09-22; report P1):
# structure 0.85 s for 28,800 atoms; engine + optics 0.06 s for 1031 x 128 exit-plane pixels.
SMOKE_COSTS = dict(structure_s_per_atom=3.0e-5, exit_pixel_s=5.0e-7, detector_pixel_s=2.0e-6,
                   label="MEASURED on the smoke demo, build machine (4 CPUs); scaled linearly")


def _geometry_numbers(cfg: PipelineConfig) -> dict:
    b = cfg.cfg_b
    a, _ = b.quantity("lattice_parameter")
    az = tuple(b.value("beam_azimuth_uvw"))
    p = a if sorted(abs(v) for v in az) == [0, 0, 1] else a / math.sqrt(2.0)
    st = cfg.rec("structure", "staircase").value
    widths = st["terrace_widths_periods"]
    layers = st["terrace_layers"]
    period = sum(widths) * p
    sub = cfg.value("structure", "substrate_layers")
    tops = [lv - min(layers) + sub - 1 for lv in layers]
    edge_periods = cfg.value("structure", "edge_periods")
    atoms_per_layer_period = 1 if p != a else 2
    n_atoms = sum(w * edge_periods * atoms_per_layer_period * (t + 1) for w, t in zip(widths, tops))
    span = (max(layers) - min(layers)) * a / 4.0
    return dict(in_plane_period_A=p, staircase_period_A=period, n_atoms_structure=n_atoms,
                height_span_A=span, edges=st["edges"])


def dry_run(cfg: PipelineConfig, *, calibrate_cpu: bool = False) -> dict:
    """Resource estimate of a gated configuration (see module docstring)."""
    theta = cfg.glancing_angle["value_rad"]
    g = _geometry_numbers(cfg)
    det = cfg.value("detector", "roi_shape")
    n_det = det[0] * det[1]
    out = dict(run_name=cfg.run_name, variant=cfg.variant, purpose=cfg.purpose,
               engine=cfg.value("engine", "name"),
               glancing_angle_mrad=theta * 1e3, glancing_angle=cfg.glancing_angle,
               beam_energy_keV=BEAM_ENERGY_SUPPLIED_KEV, structure=g,
               detector=dict(roi_shape=det, memory_bytes=n_det * 16 * 24,
                             note="about 24 detector-sized arrays of 16 B"))
    if out["engine"] == "geometric":
        e = cfg.value("engine", "geometric")
        periods = cfg.value("cell", "periods_along_beam")
        L = periods * g["staircase_period_A"] if g["edges"] == "transverse" else \
            periods * cfg.value("structure", "edge_periods") * g["in_plane_period_A"]
        dx, dy = e["exit_plane_pixel_A"]["x"], e["exit_plane_pixel_A"]["y"]
        nx = int(math.ceil((g["height_span_A"] + L * math.tan(theta) + 2 * e["x_margin_A"]) / dx)) + 1
        ny = e["n_y"]
        mem = nx * ny * (16 * 6 + 8 * 3 + 1)
        t = (g["n_atoms_structure"] * SMOKE_COSTS["structure_s_per_atom"]
             + nx * ny * SMOKE_COSTS["exit_pixel_s"] + n_det * SMOKE_COSTS["detector_pixel_s"])
        out["geometric"] = dict(field_length_A=L, exit_plane_shape=[nx, ny],
                                exit_plane_memory_bytes=mem, estimated_seconds=t,
                                cost_basis=SMOKE_COSTS)
        out["total_memory_bytes"] = mem + out["detector"]["memory_bytes"]
        return out
    from reflection_holo.pipeline.engines import build_structure, multislice_status
    ok, why = multislice_status()
    out["multislice_available"] = ok
    out["multislice_status"] = why
    if not ok:
        return out
    from reflection_holo.pipeline.engines import backend_status, multislice_objects
    backend = cfg.value("engine", "multislice")["backend"]
    b_ok, b_why = backend_status(backend)
    out["backend"] = dict(name=backend, available=b_ok, status=b_why)
    structure = build_structure(cfg)
    o = multislice_objects(structure, cfg, require_backend=False)
    ms, cell, params = o["ms"], o["cell"], o["params"]
    setup = ms.reflection_setup(cell, potential=o["potential"], beam=o["beam"], params=params)
    m = cfg.value("engine", "multislice")
    est = ms.estimate_resources(cell, params, realisations=m["n_realisations"],
                                calibrate_cpu=calibrate_cpu)
    out["multislice"] = est
    out["mip_check"] = o["mip_check"]
    out["geometry_checks"] = setup["geometry"]
    out["band_checks"] = setup["band"]
    out["cell"] = dict(extent_x_A=cell.extent_x_A, extent_y_A=cell.extent_y_A,
                       length_z_A=cell.length_z_A, n_atoms=int(len(cell.Z)),
                       crystal_start_z_A=cell.crystal_start_z_A)
    return out
