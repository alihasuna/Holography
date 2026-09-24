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


# Measured by agent T2 on this machine (4 CPUs, 2026-09-23): the height-field ray trace costs
# 7.9e-8 s per traced surface sample (192 columns x 9600 cells, 870 exit rows, 0.146 s); the
# band-limited detector resampling is a complex matrix product of n_det_along x n_y x n_det_perp
# multiply-adds (assumed 2e9 complex multiply-adds per second: an ASSUMPTION, not measured).
FEATURE_COSTS = dict(surface_sample_s=7.9e-8, complex_madd_per_s=2.0e9,
                     label="surface-sample cost MEASURED here (agent T2); matrix-product rate an "
                           "ASSUMPTION; scaled linearly")


def _dry_run_feature(cfg: PipelineConfig, out: dict) -> dict:
    """Resource estimate of the feature path (height-field engine; agent T2)."""
    theta = cfg.glancing_angle["value_rad"]
    e = cfg.value("engine", "geometric")
    f = cfg.rec("structure", "feature").value
    a, _ = cfg.cfg_b.quantity("lattice_parameter")
    layer = a / 4.0
    n_layers = math.ceil(f["minor_radius_A"] / layer)
    h_lo = -n_layers * layer if f["sub_kind"] == "trench" else 0.0
    h_hi = (n_layers - 1) * layer if f["sub_kind"] == "ridge" else 0.0
    L = e["field_length_A"]
    n_cells = int(round(L / e["surface_dz_A"]))
    dx = e["exit_plane_pixel_A"]["x"]
    nx = int(math.ceil((h_hi - h_lo + L * math.tan(theta) + 2 * e["x_margin_A"]) / dx)) + 1
    ny = e["n_y"]
    n0, n1 = cfg.value("detector", "roi_shape")
    n_det = n0 * n1
    mem_exit = nx * ny * (16 * 6 + 8 * 3 + 1)
    mem_resample = 16 * (n1 * ny + n0 * nx + n0 * ny + nx * ny)
    mem_det = n_det * 16 * 40
    mem_trace_chunk = 96 * (n_cells + 1) * 8 * 10
    t = ((ny + n1 + ny // 8) * n_cells * FEATURE_COSTS["surface_sample_s"]
         + nx * ny * SMOKE_COSTS["exit_pixel_s"] + n_det * SMOKE_COSTS["detector_pixel_s"]
         + (n0 * nx * ny + n0 * ny * n1) / FEATURE_COSTS["complex_madd_per_s"])
    out["structure"] = dict(feature=f, atomistic="not built on the feature path",
                            layer_spacing_A=layer, height_range_A=[h_lo, h_hi])
    out["geometric"] = dict(field_length_A=L, exit_plane_shape=[nx, ny], surface_cells=n_cells,
                            traced_surface_samples=(ny + n1 + ny // 8) * n_cells,
                            exit_plane_memory_bytes=mem_exit,
                            resampling_matrices_bytes=mem_resample,
                            trace_chunk_bytes=mem_trace_chunk, estimated_seconds=t,
                            cost_basis=dict(SMOKE_COSTS, feature=FEATURE_COSTS))
    out["detector"]["memory_bytes"] = mem_det
    out["detector"]["note"] = "about 40 detector-sized arrays of 16 B (feature path)"
    out["total_memory_bytes"] = mem_exit + mem_resample + mem_det + mem_trace_chunk
    return out


def dry_run(cfg: PipelineConfig, *, calibrate_cpu: bool = False) -> dict:
    """Resource estimate of a gated configuration (see module docstring)."""
    theta = cfg.glancing_angle["value_rad"]
    if "feature" in cfg.sections["structure"]:
        det = cfg.value("detector", "roi_shape")
        out = dict(run_name=cfg.run_name, variant=cfg.variant, purpose=cfg.purpose,
                   engine=cfg.value("engine", "name"), glancing_angle_mrad=theta * 1e3,
                   glancing_angle=cfg.glancing_angle, beam_energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
                   detector=dict(roi_shape=det))
        return _dry_run_feature(cfg, out)
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
    from reflection_holo.pipeline import convergence as CV
    if CV.is_convergent(cfg):
        # report E3: the declared quadrature against the computed design extent, and the band and
        # geometry assertions for EVERY member (each member is one engine run)
        from reflection_holo.forward.multislice.convergence import check_members
        q, de = CV.checked_quadrature(cfg, cell=cell)
        checks = check_members(cell, potential=o["potential"], beam=o["beam"], params=params,
                               quadrature=q)
        n = q.n_members
        out["convergence"] = dict(
            quadrature=q.as_record(), design_extent=de, n_members=n,
            members_passing_band_and_geometry_checks=len(checks),
            cost_note=f"every engine cost above is PER MEMBER: the ensemble runs {n} members "
                      f"(separately with run-member, or in one run)",
            seconds_total_cpu=(est["cpu"]["seconds_total"] * n if "cpu" in est else None),
            seconds_total_gpu_assumption=est["gpu"]["seconds_total"] * n)
    return out
