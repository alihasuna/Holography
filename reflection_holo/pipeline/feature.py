"""Feature path of the pipeline (agent T2): a surface feature on a flat Si(001) surface.

Chain (``pipeline.run`` dispatches here when ``sections.structure.feature`` is given):

 1. configuration gate (``pipeline.config``; the feature geometry is PROJECT_INPUT item 13, a demo
    value must be a registered stand-in; ``cfg_b.pattern_geometry`` must point at the feature);
 2. structure: the shared shape ``structure.shapes.HalfTorus`` and its ideal top atomic layer
    ``layer_height_A`` (a/4 terraces) as a height field; NO atomistic structure is built on this
    path (the atomistic builder must reproduce layer_height_A on its atoms);
 3. engine: ``forward.geometric.height_field`` (specular phase -2 k sin(theta_ext) h per surface
    point, ray-traced shadows and blocked views; B4 scope checked: exact <100> azimuth);
 4-10. the SAME dark-field, projection, detector, reference, hologram, noise and sideband stages as
    the staircase path (``pipeline.run._optics_stage``, ``_hologram_stage``,
    ``_reconstruction_stage``); the projection is referred to the flat surrounding surface
    (x0 = L tan(theta), z_s = 0 at the upstream end of the field); the empty hologram's object
    branch is the uniform reflection of the flat surface, its amplitude the RMS over lit
    flat-surface pixels;
11. quantification: the HEIGHT MAP (``quantification.height_map``: reliability map, unwrapping from
    the flat reference, h = -Delta_phi / s, masks with reason codes), the no-step control on the flat
    reference (a failed or missing control withholds every height, audit A3 B1 / S4), profile cuts
    across the ring at its sides (y cut at z = z_c) and along the beam (z cut at y = y_c) compared
    with ``continuous_height_A`` and ``layer_height_A`` at the traced source points, and the
    resolution record;
12. outputs: arrays.npz, summary.json, manifest.json, quicklooks.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

import reflection_holo
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.forward.geometric import STATUS
from reflection_holo.forward.geometric.height_field import trace_height_field
from reflection_holo.geometry.specular import wrap_to_pi
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.pipeline import quantify as Q
from reflection_holo.pipeline.config import PipelineConfig, assumptions_in_use, list_inputs
from reflection_holo.pipeline.engines import run_geometric_feature
from reflection_holo.provenance.manifest import build_manifest
from reflection_holo.quantification.height_map import REASONS, box_all, box_span, height_map
from reflection_holo.quantification.invisibility import detect_invisibility
from reflection_holo.quantification.shadow import height_field_masks
from reflection_holo.reconstruction.sideband import sideband_phase_noise

FEATURE_NOT_IMPLEMENTED = [
    "atomistic feature structure on this path (the geometric engine uses the shared shape's "
    "layer_height_A; the atomistic builder and its multislice runs are separate)",
    "dynamical amplitude and the B4 riser region: every surface point reflects with one |A|",
    "height-map unwrapping across unresolved a/4 steps (a single hologram cannot; a rocking series "
    "or a lattice constraint over resolved terraces would be needed)",
]


def detector_trace_height_field(hf, u_A, y_A, *, x0_A: float, theta_rad: float) -> dict:
    """Ray trace of every detector pixel centre (u along the beam, y perpendicular; image-plane A)
    through its exit-plane point x = x0 - u / cos(theta) (``quantify.detector_trace`` for a height
    field)."""
    X = float(x0_A) - np.asarray(u_A, float) / math.cos(theta_rad)
    tr = trace_height_field(hf, X, np.asarray(y_A, float), theta_in_ext_rad=theta_rad,
                            theta_out_ext_rad=theta_rad)
    tr["exit_x_A"] = X
    return tr


def _rms(v: np.ndarray) -> float | None:
    v = np.asarray(v, float)
    return float(np.sqrt(np.mean(v ** 2))) if v.size else None


def _cut_stats(meas, sigma, h_layer, h_cont, measurable, footprint, h_data) -> dict:
    m = measurable & np.isfinite(meas)
    fm = m & footprint
    d_ok = np.isfinite(h_data) & footprint
    return dict(
        n_px=int(meas.size), n_measurable=int(m.sum()), n_on_footprint=int(footprint.sum()),
        n_measurable_on_footprint=int(fm.sum()),
        rms_vs_layer_A=_rms(meas[m] - h_layer[m]), rms_vs_continuous_A=_rms(meas[m] - h_cont[m]),
        rms_vs_layer_on_footprint_A=_rms(meas[fm] - h_layer[fm]),
        rms_vs_continuous_on_footprint_A=_rms(meas[fm] - h_cont[fm]),
        median_sigma_h_A=float(np.median(sigma[m])) if m.any() else None,
        data_only_on_footprint=dict(
            n_px=int(d_ok.sum()),
            rms_vs_layer_A=_rms(h_data[d_ok] - h_layer[d_ok]),
            mean_A=float(np.mean(h_data[d_ok])) if d_ok.any() else None,
            mean_layer_A=float(np.mean(h_layer[d_ok])) if d_ok.any() else None,
            note="height_data_only (DATA criteria only, no model check): NOT a height; shows the "
                 "aliasing across unresolved a/4 steps"))


def _resolution_record(shape, *, theta: float, res_A: float, pixel_A, layer_A: float, s: float,
                       alpha: float) -> dict:
    R, r = shape.major_radius_A, shape.minor_radius_A
    sin_t, cos_t = math.sin(theta), math.cos(theta)
    along = res_A / sin_t
    n_max = int(math.ceil(r / layer_A)) - (1 if shape.kind == "ridge" else 0)
    h_ext = n_max * layer_A * (1 if shape.kind == "ridge" else -1)
    top_w = 2.0 * math.sqrt(max(0.0, r ** 2 - ((n_max - (0 if shape.kind == "ridge" else 1))
                                                * layer_A) ** 2))
    step = s * layer_A
    wrapped = math.remainder(-step, 2 * math.pi)
    return dict(
        reconstruction_resolution_image_A=res_A,
        detector_pixel_A=list(pixel_A),
        surface_resolution_along_beam_A=along,
        surface_resolution_across_beam_A=res_A,
        ring_cross_section_A=2 * r,
        ring_cross_section_in_resolution_elements=dict(
            along_beam_front_back_arcs=2 * r / along, across_beam_sides=2 * r / res_A),
        ring_front_back_resolved=bool(2 * r / along >= 1.0),
        ring_image_length_along_beam_A=(2 * R + 2 * r) * sin_t,
        extreme_layer=dict(n=n_max if shape.kind == "ridge" else -n_max, height_A=h_ext,
                           terrace_width_A=top_w,
                           parallax_image_A=-h_ext * cos_t,
                           parallax_rows=-h_ext * cos_t / pixel_A[0]),
        a4_step=dict(phase_rad=-step, wraps=step / (2 * math.pi), wrapped_phase_rad=wrapped,
                     apparent_height_A=-wrapped / s,
                     note="one +a/4 step changes the phase by -s a/4; its wrapped value is the phase "
                          "of a step of apparent_height_A: a sharp a/4 step cannot be unwrapped "
                          "from one hologram"),
        aperture_slope_acceptance=dict(across_beam_dh_dy=math.tan(alpha) / (2 * sin_t),
                                       along_beam_dh_dz=math.tan(alpha / 2.0),
                                       note="a facet tilted across the beam deflects the specular "
                                            "beam by 2 sin(theta) dh/dy, along the beam by 2 "
                                            "atan(dh/dz); the aperture semi-angle alpha bounds both"),
        summary=(f"along the beam the ring cross-section (2r = {2 * r:g} A) is "
                 f"{2 * r / along:.3f} resolution elements ({along:.0f} A of surface each): the "
                 f"ring front and back arcs are UNRESOLVED; across the beam at the sides it is "
                 f"{2 * r / res_A:.1f} elements; the {n_max} a/4 terraces of each flank are "
                 f"narrower than the resolution except the "
                 f"{'top' if shape.kind == 'ridge' else 'bottom'} terrace ({top_w:.1f} A); one "
                 f"a/4 step is {step / (2 * math.pi):.3f} wraps (apparent {-wrapped / s:+.3f} A)"))


def _surface_mask_map(hf, theta: float, n_y: int, dy: float, stride_y: int, stride_z: int) -> dict:
    """Shadowed / blocked map of the surface on every stride_y-th exit column, every stride_z-th
    cell (code 0 usable, 1 shadowed, 2 blocked, 3 both), from ``height_field_masks``."""
    y = dy * np.arange(0, n_y, stride_y)
    code = []
    for s0 in range(0, y.size, 64):
        H = hf.sample(y[s0:s0 + 64])
        m = height_field_masks(H, z_start_A=hf.z_start_A, dz_A=hf.surface_dz_A, profile=hf.profile,
                               upstream_level_A=hf.upstream_level_A, theta_in_ext_rad=theta,
                               theta_out_ext_rad=theta)
        c = (~m.illuminated).astype(np.int8) + 2 * (~m.visible).astype(np.int8)
        code.append(c[:, ::stride_z])
    z = hf.z_points_A()[::stride_z]
    return dict(code=np.concatenate(code, axis=0), y_A=y, z_A=z)


def run_feature(cfg: PipelineConfig, out: Path, *, t0: float, git_preflight: dict,
                allow_no_git: bool) -> dict:
    """The feature path (module docstring). ``out`` has been prepared (empty) by ``pipeline.run``."""
    from reflection_holo.pipeline.run import (NOT_IMPLEMENTED, PURPOSE_BANNER, _hologram_stage,
                                              _jsonable, _optics_stage, _reconstruction_stage,
                                              _withhold_reason)
    timing: dict[str, float] = {}
    notes: list[str] = []
    theta = float(cfg.glancing_angle["value_rad"])
    lam = wavelength_A(BEAM_ENERGY_SUPPLIED_KEV)
    b = cfg.cfg_b

    # 2-3. structure (shape and height field) and engine -------------------------------------------
    t = time.perf_counter()
    waves, shape, hf, hrun = run_geometric_feature(cfg)
    ew0 = waves[0]
    timing["engine_s"] = time.perf_counter() - t
    g = cfg.value("engine", "geometric")
    a_lat, _ = b.quantity("lattice_parameter")
    layer = a_lat / 4.0
    q_x = float(ew0.metadata["q_rad_per_A"][0])
    inv = []
    for n in range(2, int(math.ceil(shape.minor_radius_A / layer)) + 2, 2):  # translations
        r = detect_invisibility(np.asarray(ew0.metadata["q_rad_per_A"]) / (2 * math.pi),
                                np.array([n * layer, 0.0, 0.0]),
                                tol_cycles=g["invisibility_tol_cycles"])
        inv.append(dict(layers=n, g_dot_R_cycles=r.g_dot_R, distance_cycles=r.distance_cycles,
                        invisible=r.invisible))

    # 4-6. dark field, projection, detector ---------------------------------------------------------
    t = time.perf_counter()
    span = hf.z_end_A - hf.z_start_A
    x0 = hf.upstream_level_A + span * math.tan(theta)
    x0_def = (f"flat surrounding surface (x = {hf.upstream_level_A:.6f} A); z_s = 0 at the upstream "
              f"end of the field (z = {hf.z_start_A:.6f} A); exit plane z = {hf.z_end_A:.6f} A")
    fov_u = (0.0, span * math.sin(theta))
    op = _optics_stage(cfg, waves, x0=x0, x0_def=x0_def, fov_u=fov_u)
    spec, placement, obj_waves, dfs, imgs = (op["spec"], op["placement"], op["obj_waves"],
                                             op["dfs"], op["imgs"])
    timing["optics_s"] = time.perf_counter() - t

    # 7-9. detector trace, references, holograms ----------------------------------------------------
    t = time.perf_counter()
    grid = spec.grid()
    tr = detector_trace_height_field(hf, placement.u_A, placement.y_A, x0_A=x0, theta_rad=theta)
    lit = tr["status"] == STATUS["lit"]
    U, Yd = np.meshgrid(placement.u_A, placement.y_A, indexing="ij")
    zsrc = tr["source_z_A"]
    Zs = np.where(lit, zsrc, shape.center_z_A + 10 * shape.major_radius_A)   # far outside: flat
    footprint = lit & (shape.half_thickness_A(Yd, Zs) > 0.0)
    flat_source = lit & ~footprint
    h_layer = np.where(lit, shape.layer_height_A(Yd, Zs, layer_spacing_A=layer), np.nan)
    h_cont = np.where(lit, shape.continuous_height_A(Yd, Zs), np.nan)
    # the engine's cells: heights sampled at the cell centres (risers at most dz/2 from the true
    # terrace boundary, B13); assert that sampling, and count sources whose exact layer height differs
    zc_cell = hf.z_start_A + (tr["source_index"] + 0.5) * hf.surface_dz_A
    h_cell = shape.layer_height_A(Yd, np.where(lit, zc_cell, Zs), layer_spacing_A=layer)
    if np.any(np.abs(h_cell[lit] - tr["source_h_A"][lit]) > 1e-9):
        raise RuntimeError("traced source heights differ from layer_height_A at the cell centres")
    n_boundary_cells = int(np.sum(np.abs(h_layer[lit] - tr["source_h_A"][lit]) > 1e-9))
    ho = _hologram_stage(cfg, obj_waves, spec, amplitude_px=flat_source,
                         amplitude_px_description="flat-surface point")
    a_all, A_emp, refs = ho["a_all"], ho["A_emp"], ho["refs"]
    H_obj, H_emp, H_obj_n, H_emp_n = ho["H_obj"], ho["H_emp"], ho["H_obj_n"], ho["H_emp_n"]
    amp_by_status = {name: dict(n_px=int((tr["status"] == c).sum()),
                                mean_abs=(float(a_all[:, tr["status"] == c].mean())
                                          if (tr["status"] == c).any() else None))
                     for name, c in STATUS.items()}
    timing["holography_s"] = time.perf_counter() - t

    # 10. reconstruction ------------------------------------------------------------------------------
    t = time.perf_counter()
    rc = _reconstruction_stage(cfg, H_obj_n, H_emp_n, ho["q_ref"])
    recon, divide, recon_warnings = rc["recon"], rc["divide"], rc["warnings"]
    timing["reconstruction_s"] = time.perf_counter() - t

    # 11. quantification: height map, control, cuts, resolution -------------------------------------
    t = time.perf_counter()
    qp = cfg.rec("quantification", "processing").value
    fp = cfg.rec("quantification", "feature_processing").value
    phase = np.asarray(recon.wrapped_phase)
    amp_rel = np.asarray(recon.amplitude, dtype=float)
    if not divide:
        fa = amp_rel[flat_source & np.isfinite(amp_rel)]
        amp_rel = amp_rel / float(np.median(fa)) if fa.size else amp_rel * np.nan
    res_A = float(recon.resolution_A)
    p_A = spec.pixel_A
    m0 = int(math.ceil(qp["edge_margin_resolutions"] * res_A / p_A[0]))
    m1 = int(math.ceil(qp["edge_margin_resolutions"] * res_A / p_A[1]))
    W = np.asarray(recon.mask)
    a_eff = float(W.size / np.sum(W ** 2))
    theta_sigma = cfg.rec("illumination", "angle_calibration_sigma").canonical_value
    wl_sigma = cfg.rec("illumination", "wavelength_sigma_rel").canonical_value
    source_phase = np.where(lit, -q_x * tr["source_h_A"], np.nan)
    hm = height_map(phase_wrapped=phase, amplitude_rel=amp_rel, valid=recon.valid_mask, lit=lit,
                    source_phase_rad=source_phase, hidden=tr["hidden_neighbour"],
                    flat_source=flat_source, min_relative_amplitude=qp["min_relative_amplitude"],
                    max_phase_step_rad=fp["max_phase_step_rad"], margin_px=(m0, m1),
                    min_region_px=qp["min_region_px"], a_eff_px=a_eff, wavelength_A=lam,
                    theta_rad=theta, sigma_theta_rad=theta_sigma, sigma_wavelength_rel=wl_sigma)
    s_sens = hm["record"]["sensitivity_rad_per_A"]
    if abs(s_sens - q_x) > 1e-9 * q_x:
        raise RuntimeError("the engine's q.n_hat and the quantification sensitivity differ")
    flat_ref = hm["flat_reference"]
    if int(flat_ref.sum()) >= qp["min_region_px"]:
        control = Q.no_step(phase, flat_ref, a_eff, qp["n_sigma"], recon.valid_mask)
        control["region"] = "flat reference surface (outside the feature footprint)"
    else:
        control = dict(performed=False, reason="no flat reference region of the minimum size")
    withhold = _withhold_reason(control)
    height = hm["height_A"].copy()
    sigma_h = hm["sigma_h_A"].copy()
    measurable = hm["measurable"] & np.isfinite(height)
    if withhold is not None:
        height[:] = np.nan
        sigma_h[:] = np.nan
    n_meas = int(measurable.sum()) if withhold is None else 0
    # resolved map: the built phase varies by less than pi over one resolution element
    r0 = int(math.ceil(0.5 * res_A / p_A[0]))
    r1 = int(math.ceil(0.5 * res_A / p_A[1]))
    resolved = box_span(source_phase, lit, r0, r1) < math.pi
    # profile cuts ------------------------------------------------------------------------------
    dz_row = p_A[0] / math.sin(theta)
    dist = np.where(lit, np.abs(zsrc - shape.center_z_A), np.inf)
    rows = np.argmin(dist, axis=0)
    cols = np.arange(grid.shape[1])
    take = dist[rows, cols] <= dz_row
    cy = dict(y_A=placement.y_A[take], row=rows[take], z_src_A=zsrc[rows[take], cols[take]])
    col0 = int(np.argmin(np.abs(placement.y_A - shape.center_y_A)))
    cz = dict(u_A=placement.u_A.copy(), column=np.array(col0), y_A=np.array(placement.y_A[col0]),
              z_src_A=zsrc[:, col0].copy())
    for name, arr in (("h_meas_A", height), ("sigma_h_A", sigma_h), ("h_layer_A", h_layer),
                      ("h_continuous_A", h_cont), ("h_data_only_A", hm["height_data_only_A"]),
                      ("reason", hm["reason_code"]), ("status", tr["status"]),
                      ("footprint", footprint), ("measurable", measurable)):
        cy[name] = arr[rows[take], cols[take]]
        cz[name] = arr[:, col0].copy()
    if withhold is not None:
        cy["measurable"] = np.zeros_like(cy["measurable"])
        cz["measurable"] = np.zeros_like(cz["measurable"])
    stats = {}
    for key, c in (("y_cut_at_z_centre", cy), ("z_cut_at_y_centre", cz)):
        stats[key] = _cut_stats(c["h_meas_A"], c["sigma_h_A"], c["h_layer_A"], c["h_continuous_A"],
                                c["measurable"].astype(bool), c["footprint"].astype(bool),
                                c["h_data_only_A"])
    stats["y_cut_at_z_centre"].update(
        definition=f"for each detector column, the lit pixel whose traced source z is nearest the "
                   f"ring centre z_c = {shape.center_z_A:g} A (within one along-beam surface pixel, "
                   f"{dz_row:.1f} A); crosses the ring where it runs along the beam (y_c +- R)",
        n_columns=int(take.sum()))
    stats["z_cut_at_y_centre"].update(
        definition=f"the detector column nearest y_c = {shape.center_y_A:g} A (y = "
                   f"{float(cz['y_A']):.3f} A); crosses the ring front and back arcs (z_c -+ R), "
                   f"where the ring runs across the beam", column=col0)
    # measurable fractions ------------------------------------------------------------------------
    n_px = int(lit.size)
    fractions = dict(
        detector_px=n_px, lit_px=int(lit.sum()), flat_source_px=int(flat_source.sum()),
        footprint_source_px=int(footprint.sum()),
        measurable_px=n_meas,
        measurable_fraction_of_detector=n_meas / n_px,
        measurable_fraction_of_flat_source=(int((measurable & flat_source).sum()) /
                                            max(1, int(flat_source.sum())) if withhold is None
                                            else 0.0),
        measurable_fraction_of_footprint_source=(int((measurable & footprint).sum()) /
                                                 max(1, int(footprint.sum())) if withhold is None
                                                 else 0.0),
        measurable_footprint_px=int((measurable & footprint).sum()) if withhold is None else 0,
        resolved_fraction_of_footprint_source=int((resolved & footprint).sum())
                                              / max(1, int(footprint.sum())),
        reason_counts={k: int((hm["reason_code"] == v).sum()) for k, v in REASONS.items()},
        reason_counts_on_footprint={k: int(((hm["reason_code"] == v) & footprint).sum())
                                    for k, v in REASONS.items()})
    # reliable footprint pixels NOT connected to the flat reference: their height is known modulo
    # h_2pi only; check the chain there modulo 2 pi against the built phase at the source
    iso_all = hm["reliable"] & ~hm["connected"] & footprint
    iso = iso_all & box_all(hm["reliable"], r0, r1)          # half a resolution from unreliable px
    rec_iso: dict[str, Any] = dict(
        n_px=int(iso_all.sum()), n_px_half_resolution_inside=int(iso.sum()),
        note="reliable pixels on the footprint that no reliable path joins to the flat reference: "
             "height known modulo h_2pi only (not returned). Residual over those at least half a "
             "resolution element from any unreliable pixel: wrap(phi - phi_ref - (-s "
             "h_layer(source))), a check of the chain modulo 2 pi")
    if iso.any() and "phi0_rad" in hm:
        res_w = np.asarray(wrap_to_pi(phase[iso] - hm["phi0_rad"] - source_phase[iso]))
        rec_iso.update(rms_wrapped_residual_rad=_rms(res_w),
                       rms_wrapped_residual_A=_rms(res_w) / s_sens)
    fractions["isolated_reliable_on_footprint"] = rec_iso
    resolution = _resolution_record(shape, theta=theta, res_A=res_A, pixel_A=p_A, layer_A=layer,
                                    s=s_sens, alpha=op["alpha"])
    if withhold is not None:
        line = f"NO HEIGHT: {withhold}"
    else:
        line = (f"HEIGHT MAP: {n_meas} of {n_px} detector pixels measurable "
                f"({100 * n_meas / n_px:.1f} %); ring footprint: "
                f"{fractions['measurable_footprint_px']} of {fractions['footprint_source_px']} lit "
                f"footprint pixels measurable; {resolution['summary']}")
    height_verdict = dict(heights_returned=n_meas, n_steps=0, withheld=withhold is not None,
                          withhold_reason=withhold, line=line, product="height map (pixels)")
    surf = _surface_mask_map(hf, theta, g["n_y"], g["exit_plane_pixel_A"]["y"], 8, 4)
    # report E3: the noise model uses the contrast reduced by the surface-plasmon losses
    contrast_empty = ho["contrast_empty"]
    noise_pred = sideband_phase_noise(contrast_empty, spec.dose_e_per_px, W)
    timing["quantification_s"] = time.perf_counter() - t

    # 12. outputs --------------------------------------------------------------------------------------
    t = time.perf_counter()
    det_axes = ["along_beam", "perpendicular"]
    arrays = {
        "exit_psi_r0": (np.asarray(ew0.psi), ["x", "y"], "arbitrary amplitude", ew0.plane),
        "exit_x_A": (float(ew0.x0_A) + ew0.dx_A * np.arange(ew0.psi.shape[0]), ["x"], "A",
                     ew0.plane),
        "exit_y_A": (float(ew0.y0_A) + ew0.dy_A * np.arange(ew0.psi.shape[1]), ["y"], "A",
                     ew0.plane),
        "detector_object_r0": (np.asarray(obj_waves[0].data), det_axes, "arbitrary amplitude",
                               grid.plane),
        "detector_u_A": (placement.u_A, ["along_beam"], "A (image plane)", grid.plane),
        "detector_y_A": (placement.y_A, ["perpendicular"], "A (image plane)", grid.plane),
        "hologram_object_noiseless": (np.asarray(H_obj.intensity), det_axes, "relative intensity",
                                      grid.plane),
        "hologram_object_counts": (np.asarray(H_obj_n.intensity), det_axes, "counts", grid.plane),
        "hologram_empty_counts": (np.asarray(H_emp_n.intensity), det_axes, "counts", grid.plane),
        "phase_wrapped_raw": (np.asarray(recon.wrapped_phase_raw), det_axes, "rad", grid.plane),
        "phase_wrapped": (phase, det_axes, "rad", grid.plane),
        "amplitude": (np.asarray(recon.amplitude), det_axes, "relative", grid.plane),
        "valid_mask": (np.asarray(recon.valid_mask), det_axes, "bool", grid.plane),
        "trace_status": (tr["status"], det_axes, f"code {STATUS}", grid.plane),
        "trace_source_z_A": (zsrc, det_axes, "A (surface z of the traced source; NaN none)",
                             grid.plane),
        "trace_source_h_A": (tr["source_h_A"], det_axes, "A (built top-layer height at the "
                             "source; NaN none)", grid.plane),
        "trace_hidden_neighbour": (tr["hidden_neighbour"], det_axes, "bool (blocked-view strip "
                                   "between along-beam neighbours)", grid.plane),
        "built_height_layer_A": (h_layer, det_axes, "A (HalfTorus.layer_height_A at the source)",
                                 grid.plane),
        "built_height_continuous_A": (h_cont, det_axes, "A (HalfTorus.continuous_height_A at the "
                                      "source)", grid.plane),
        "footprint_source": (footprint, det_axes, "bool (source inside the ring footprint)",
                             grid.plane),
        "reliable": (hm["reliable"], det_axes, "bool", grid.plane),
        "reason_code": (hm["reason_code"], det_axes, f"code {REASONS}", grid.plane),
        "unwrapped_phase": (hm["unwrapped"], det_axes, "rad (NaN where not reliable)", grid.plane),
        "unwrap_regions": (hm["unwrap_regions"], det_axes, "label (0 not reliable)", grid.plane),
        "flat_reference": (flat_ref, det_axes, "bool", grid.plane),
        "measurable": (measurable if withhold is None else np.zeros_like(measurable), det_axes,
                       "bool", grid.plane),
        "height_A": (height, det_axes, "A (NaN not measurable or withheld)", grid.plane),
        "sigma_height_A": (sigma_h, det_axes, "A", grid.plane),
        "height_data_only_A": (hm["height_data_only_A"], det_axes, "A (DATA criteria only: NOT a "
                               "height, aliased across unresolved a/4 steps)", grid.plane),
        "geometry_resolved": (resolved, det_axes, "bool (built phase span < pi over one "
                              "resolution element)", grid.plane),
        "surface_mask_code": (surf["code"], ["y", "z"], "code 0 usable, 1 shadowed, 2 blocked, "
                              "3 both", "surface plane x_rel = h(y, z) (slab frame)"),
        "surface_mask_y_A": (surf["y_A"], ["y"], "A", "surface plane"),
        "surface_mask_z_A": (surf["z_A"], ["z"], "A", "surface plane"),
    }
    for key, c in (("cut_y", cy), ("cut_z", cz)):
        for name, v in c.items():
            if isinstance(v, np.ndarray):
                arrays[f"{key}_{name}"] = (v, ["cut"] if v.ndim else ["none (0-d scalar)"],
                                           "see summary quantification.profile_cuts", grid.plane)
    arrays["purpose"] = (np.array(cfg.purpose), ["none (0-d scalar)"], "text (run purpose)",
                         "not a wave: run metadata (audit A3 m1)")
    with open(out / "arrays.npz", "xb") as fh:
        np.savez_compressed(fh, **{k: v[0] for k, v in arrays.items()})
    array_index = {k: dict(axes=v[1], units=v[2], plane=v[3], shape=list(np.shape(v[0])),
                           dtype=str(np.asarray(v[0]).dtype)) for k, v in arrays.items()}
    array_index["_not_stored"] = dict(
        axes=[], units="-", plane="-", shape=[], dtype="-",
        note="darkfield_r0 and projected_r0 are not stored on the feature path (size); they follow "
             "from exit_psi_r0 by optics.darkfield.select_dark_field and "
             "optics.projection.project_along_k_out with the recorded parameters")
    ga = dict(cfg.glancing_angle)
    df0, img0 = dfs[0], imgs[0]
    feature_rec = dict(
        shape=dict(kind="half_torus", sub_kind=shape.kind, center_y_A=shape.center_y_A,
                   center_z_A=shape.center_z_A, major_radius_A=shape.major_radius_A,
                   minor_radius_A=shape.minor_radius_A, label=shape.label, source=shape.source,
                   definition="reflection_holo.structure.shapes.HalfTorus (fixed shared definition)"),
        base_surface="flat, step-free, bulk-terminated Si(001) at x_rel = 0 (stated by the feature "
                     "stand-in; the miscut and terrace part of item 11 is not represented)",
        height_field=hf.as_record(), layer_spacing_A=layer,
        invisibility_even_layers=inv,
        sources_in_boundary_cells=dict(
            n_px=n_boundary_cells,
            note="lit pixels whose source lies in a cell holding a terrace boundary: the engine "
                 "uses the cell-centre height (riser at the cell boundary, at most dz/2 from the "
                 "true boundary), the comparisons use layer_height_A at the exact source point"))
    summary = dict(
        purpose=cfg.purpose, banner=PURPOSE_BANNER.format(purpose=cfg.purpose),
        height_verdict=height_verdict,
        run_name=cfg.run_name, variant=cfg.variant, test_only=cfg.test_only,
        description=cfg.description,
        config=dict(path=cfg.source_path, sha256_file=cfg.sha256_file,
                    sha256_resolved=cfg.sha256_resolved,
                    cfg_b_sha256_canonical=cfg.cfg_b.sha256_canonical),
        inputs=list_inputs(cfg.raw, variant=cfg.variant),
        assumptions_in_use=assumptions_in_use(cfg),
        beam_energy_keV=BEAM_ENERGY_SUPPLIED_KEV, wavelength_A=lam,
        glancing_angle=dict(ga, value_mrad=theta * 1e3),
        mean_inner_potentials=dict(
            cfg_b_V0_V=b.quantity("mean_inner_potential_V")[0],
            cfg_b_V0_label=f"{b.label('mean_inner_potential_V')} "
                           f"{b.parameters['mean_inner_potential_V'].assumption_id}",
            used_for_glancing_angle_V=ga.get("V0_V"), V0_source=ga.get("V0_source")),
        feature=feature_rec,
        structure=dict(atomistic="not built on the feature path", feature=feature_rec["shape"]),
        engine=dict(name="geometric", label=ew0.metadata["label"], counts=hrun.record,
                    b4=ew0.metadata["b4"], height_field=ew0.metadata["height_field"],
                    phase_formula=ew0.metadata["phase_formula"]),
        exit_wave=dict(plane=ew0.plane, z_A=ew0.z_A, dx_A=ew0.dx_A, dy_A=ew0.dy_A, x0_A=ew0.x0_A,
                       y0_A=ew0.y0_A, shape=list(ew0.psi.shape), dtype=str(ew0.psi.dtype),
                       n_realisations=len(waves), realisations=[w.realisation for w in waves],
                       seeds=[w.seed for w in waves]),
        dark_field=df0.record, projection=dict(img0.record, sampling=img0.sampling),
        detector=dict(spec.as_record(theta), placement=placement.record,
                      empty_object_amplitude=A_emp,
                      empty_object_amplitude_rule="RMS of the detector object amplitude over the "
                                                  "LIT FLAT-SURFACE pixels (outside the feature "
                                                  "footprint) >= half their maximum",
                      object_amplitude_by_trace_status=amp_by_status),
        reference=dict(model=ho["ref_model"], trajectory=ho["trajectory"],
                       carrier_cycles_per_A=list(ho["q_ref"]), amplitude=ho["ratio"] * A_emp,
                       amplitude_ratio=ho["ratio"], relative_phase_rad=ho["rel_phase"],
                       aperture_passage=ho["passage"], empty_hologram_fringe_contrast=contrast_empty,
                       fringe_contrast=ho["contrast_record"],
                       noise_seed=ho["seed"],
                       empty_hologram="uniform object wave of the flat surface (amplitude above), "
                                      "same reference, detector, dose and gain; carrier located on "
                                      "it"),
        surface_plasmon_losses=ho["loss"].as_record(),
        hologram=dict(object={k: v for k, v in H_obj.metadata.items() if k != "valid_mask"},
                      empty_formation=H_emp.metadata.get("formation"),
                      ensemble_rule="intensities averaged over realisations AFTER squaring"),
        reconstruction=dict(parameters=recon.parameters, resolution_A=res_A,
                            resolution_fringe_spacings=recon.resolution_fringe_spacings,
                            sideband_sign_check=recon.sideband_sign_check,
                            warnings=recon_warnings, predicted_phase_noise_per_px=noise_pred),
        quantification=dict(
            product="height map", height_verdict=height_verdict, steps=[],
            height_map=dict(hm["record"], reason_codes=REASONS,
                            processing=dict(fp, min_relative_amplitude=qp["min_relative_amplitude"],
                                            edge_margin_resolutions=qp["edge_margin_resolutions"],
                                            min_region_px=qp["min_region_px"],
                                            n_sigma=qp["n_sigma"],
                                            stand_in=cfg.rec("quantification",
                                                             "feature_processing").assumption_id)),
            measurable=fractions, profile_cuts=stats, resolution=resolution,
            no_step_control=control, a_eff_px=a_eff,
            shadow_exclusion=dict(
                rule="docs/03 section 4; B9: a surface point is shadowed if an upstream point lies "
                     "above its incoming ray, blocked if a downstream point lies above its outgoing "
                     f"ray (height-field ray trace at {theta * 1e3:.6f} mrad)",
                detector_status_counts={k: int((tr["status"] == c).sum())
                                        for k, c in STATUS.items()},
                hidden_neighbour_px=int(tr["hidden_neighbour"].sum()),
                surface_map=dict(n_y=int(surf["code"].shape[0]), n_z=int(surf["code"].shape[1]),
                                 shadowed_fraction=float(np.mean(surf["code"] & 1 > 0)),
                                 blocked_fraction=float(np.mean(surf["code"] & 2 > 0)))),
            sigma_source="measured phase scatter on the flat reference (B16)",
            region_source="ray-traced geometry of the built height field (model criteria) and the "
                          "reconstruction (data criteria)"),
        not_implemented=NOT_IMPLEMENTED + FEATURE_NOT_IMPLEMENTED, notes=notes,
        arrays=array_index, timing_s=timing)
    summary["timing_s"]["outputs_s"] = time.perf_counter() - t
    summary["timing_s"]["total_s"] = time.perf_counter() - t0
    quick = []
    if cfg.value("outputs", "quicklooks"):
        quick = _feature_quicklooks(out, arrays, cfg)
    summary["quicklooks"] = quick
    manifest = build_manifest(
        run_name=f"{cfg.run_name}{'_' + cfg.variant if cfg.variant else ''}", config=cfg.cfg_b,
        input_paths=[cfg.source_path] if cfg.source_path else [],
        seeds=dict(detector_noise=ho["seed"], engine=[w.seed for w in waves]),
        thread_count=cfg.value("runtime", "threads"),
        precision=dict(pipeline_complex="complex128", pipeline_real="float64",
                       exit_wave=str(ew0.psi.dtype)),
        engines={"reflection_holo.forward.geometric.height_field": dict(
            version=reflection_holo.__version__, commit="this repository (see repository.commit)",
            licence="this repository", label=ew0.metadata["label"])},
        wave_planes={"exit_wave": ew0.plane, "dark_field": df0.wave.grid.plane,
                     "projected": img0.wave.grid.plane, "detector": grid.plane},
        beam_energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
        extra=dict(purpose=cfg.purpose, variant=cfg.variant, test_only=cfg.test_only,
                   allow_test_only="never set by a pipeline run or the CLI (A2c G3)",
                   pipeline_config_sha256_file=cfg.sha256_file,
                   pipeline_config_sha256_resolved=cfg.sha256_resolved,
                   feature=feature_rec["shape"], glancing_angle=ga,
                   engine_label=ew0.metadata["label"], git_preflight=git_preflight,
                   height_verdict=height_verdict),
        allow_no_git=allow_no_git)
    with open(out / "manifest.json", "x", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    with open(out / "summary.json", "x", encoding="utf-8") as fh:
        json.dump(_jsonable(summary), fh, indent=2)
        fh.write("\n")
    return summary


def _feature_quicklooks(out: Path, arrays: dict, cfg: PipelineConfig) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return ["skipped: matplotlib is not importable"]
    fig, ax = plt.subplots(4, 1, figsize=(14, 9))
    panels = [("hologram_object_counts", "object hologram (counts)", "gray", None),
              ("phase_wrapped", "reconstructed phase (rad)", "twilight", None),
              ("height_A", "height map (A), NaN masked", "RdBu_r", "sym"),
              ("reason_code", f"reason code {REASONS}", "tab10", None)]
    for a, (key, title, cmap, norm) in zip(ax, panels):
        v = np.asarray(arrays[key][0], float)
        kw = {}
        if norm == "sym" and np.isfinite(v).any():
            m = float(np.nanmax(np.abs(v))) or 1.0
            kw = dict(vmin=-m, vmax=m)
        im = a.imshow(v, cmap=cmap, aspect="auto", interpolation="nearest", **kw)
        a.set_title(title, fontsize=8)
        a.set_ylabel("along beam (px)")
        fig.colorbar(im, ax=a, shrink=0.8)
    ax[-1].set_xlabel("perpendicular (px)")
    fig.suptitle(f"{cfg.run_name}: {cfg.purpose}", fontsize=9)
    fig.tight_layout()
    p = out / "quicklook_detector.png"
    fig.savefig(p, dpi=80)
    plt.close(fig)
    return [p.name]
