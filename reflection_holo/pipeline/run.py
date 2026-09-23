"""End-to-end pipeline run (docs/05 sections 0, 4.5, 5; docs/03 sections 1, 4, 6).

Order of the chain (each stage is the package's own implementation):

 1. configuration gate (pipeline.config): every PROJECT_INPUT supplied or a registered ASSUMPTION;
    the glancing angle computed by geometry/ from the declared rule;
 2. structure (structure.build_si001_terraces), with the step relations measured on the atoms;
 3. engine: forward.geometric (fast; "geometric model, no dynamical amplitude, B4 scope applies")
    or forward.multislice (lazy import; its validation status is copied into the outputs);
 4. dark-field selection in k-space around k_out with the declared aperture (optics.darkfield);
 5. projection along k_out onto surface and image coordinates (optics.projection);
 6. detector: magnification and pixel mapping (optics.detector);
 7. reference R1 or R2 on the detector grid and the hologram I = |u_o + u_r|^2, averaged over the
    realisations AFTER squaring (optics.hologram.ensemble_hologram_intensity);
 8. an EMPTY hologram with the same reference, detector, dose and gain: its object branch is the
    vacuum plane wave along k_out, which the aperture centred on k_out passes unchanged and the
    demodulation makes uniform, so it is formed directly as a uniform wave on the detector grid
    (optics.hologram.vacuum_object_wave; the FFT of a truncated exit-plane plane wave would add a
    boundary artefact that the optics does not have);
 9. Poisson counting at the declared dose, then the gain, object first then empty, one seeded
    generator (optics.detector.record_holograms);
10. sideband reconstruction with the carrier located on the EMPTY hologram
    (reconstruction.sideband);
11. quantification (pipeline.quantify): terrace regions from the ray-traced geometry, shadow and
    blocked-view exclusion, signed step heights with wrap period and branch, no-step control;
12. outputs: arrays.npz (every array with axes and units in summary.json["arrays"]),
    summary.json, manifest.json (provenance.manifest.build_manifest) and optional PNG quicklooks
    (only if matplotlib is importable and outputs.quicklooks is true).
"""
from __future__ import annotations

import json
import math
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np

import reflection_holo
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.forward.geometric import FieldLayout, terrace_model_from_structure
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.optics.darkfield import DarkFieldAperture, select_dark_field
from reflection_holo.optics.detector import DetectorSpec, record_holograms, resample_to_detector
from reflection_holo.optics.fields import Wave
from reflection_holo.optics.hologram import (ArtefactOptions, ensemble_hologram_intensity,
                                             fringe_contrast, hologram_intensity,
                                             reference_r1_vacuum_plane_wave,
                                             reference_r2_self_reference, vacuum_object_wave)
from reflection_holo.optics.projection import project_along_k_out
from reflection_holo.pipeline import quantify as Q
from reflection_holo.pipeline.config import (PipelineConfig, PipelineConfigError, Record,
                                             assumptions_in_use, list_inputs, load_pipeline_file)
from reflection_holo.pipeline.engines import (_label, build_structure, require_engine,
                                              run_geometric, run_multislice)
from reflection_holo.provenance.manifest import build_manifest, require_git_state
from reflection_holo.reconstruction.sideband import (CarrierSearch, MaskSpec, locate_carrier,
                                                     reconstruct_sideband, sideband_phase_noise)
from reflection_holo.structure import terrace_shadow_strips

NOT_IMPLEMENTED = [
    "lens transfer (defocus, Cs, chromatic envelope)",
    "partial-coherence ensembles (source size, convergence, energy spread); the geometric engine "
    "refuses non-plane-wave illumination",
    "biprism Fresnel fringes and overlap width, specimen drift, charging (B8)",
    "detector MTF, pixel integration and readout noise",
    "the intrinsic 2 theta_ext inclination of an R1 vacuum reference and its compensation (the "
    "declared carrier is the post-compensation value; the aperture passage is recorded only)",
    "R3 reference in the pipeline",
    "terrace segmentation from the data (regions come from the ray-traced simulated geometry)",
    "rocking-series branch resolution in the pipeline (the joint lattice constraint is used)",
    "quantification of an R2 (differential) phase: R2 runs form and reconstruct the holograms, "
    "every height is withheld (audit A3 M1)",
    "patterned mesas/trenches and overlayers in the engines",
]
PURPOSE_BANNER = "purpose: {purpose}"


class OutputDirectoryError(FileExistsError):
    """The output directory exists and is not empty (outputs are never overwritten)."""


def _prepare_out(out_dir) -> Path:
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise OutputDirectoryError(f"output directory {out} exists and is not empty; outputs are "
                                   f"never overwritten")
    out.mkdir(parents=True, exist_ok=True)
    return out


def _carrier(cfg: PipelineConfig) -> tuple[float, float]:
    s = cfg.rec("reference", "carrier_fringe_spacing").canonical_value
    phi = cfg.rec("reference", "carrier_direction").canonical_value
    q = [math.cos(phi) / s, math.sin(phi) / s]
    qm = 1.0 / s
    return tuple(0.0 if abs(v) < 1e-12 * qm else v for v in q)


def _detector_spec(cfg: PipelineConfig) -> DetectorSpec:
    b = cfg.cfg_b
    img, _ = b.quantity("image_pixel_size")
    pitch = cfg.rec("detector", "pixel_pitch")
    return DetectorSpec(
        pixel_pitch_um=(pitch.value["along_beam"], pitch.value["perpendicular"])
        if pitch.unit == "um" else (pitch.canonical_value["along_beam"] * 1e-4,
                                    pitch.canonical_value["perpendicular"] * 1e-4),
        magnification=cfg.rec("detector", "magnification").canonical_value,
        image_pixel_size_A=(img["along_beam"], img["perpendicular"]),
        roi_shape=tuple(cfg.value("detector", "roi_shape")),
        alignment=cfg.value("detector", "alignment"),
        dose_e_per_px=cfg.rec("detector", "dose").canonical_value,
        gain_counts_per_e=cfg.rec("detector", "gain").canonical_value,
        mtf=cfg.rec("detector", "mtf").value,
        label_item5=_label(cfg.rec("detector", "pixel_pitch")),
        label_item6=_label(cfg.rec("detector", "dose")))


def _field_steps(model, layout: FieldLayout, reference_model: str) -> list[dict]:
    """Steps between consecutive terraces of the field (and, for a periodic upstream with a global
    R1 phase, the step at the field start measured between its two ends)."""
    n = model.n_terraces
    F = layout.periods * n if model.edges == "transverse" else n
    by_from = {s["from_terrace"]: s for s in model.steps}
    H = model.heights_A
    out = []
    pairs = [(f, f + 1, "adjacent") for f in range(F - 1)]
    if (model.edges == "transverse" and layout.upstream == "periodic" and reference_model == "R1"
            and F > 1 and H[(F - 1) % n] != H[0]):
        pairs.append((F - 1, 0, "non-adjacent: the step at the upstream end of the field, measured "
                                "between the terraces at the two ends of the field (global R1 "
                                "phase)"))
    for a, b, adj in pairs:
        ka, kb = a % n, b % n
        s = by_from.get(ka)
        if s is None or s["to_terrace"] != kb:
            continue
        out.append(dict(from_field_terrace=a, to_field_terrace=b, builder_step_index=s["index"],
                        type=s["type"], model_assumption_B4=s["relation"]["model_assumption_B4"],
                        at_periodic_boundary=s["at_periodic_boundary"],
                        upper_terrace_upstream=s.get("upper_terrace_upstream"),
                        built_height_A=float(H[kb] - H[ka]),
                        built_height_note="structure input, for comparison only (not used by the "
                                          "quantification)",
                        adjacency=adj))
    return out


NO_HEIGHT_CONTROL = "no-step control failed or not performed"
R2_DIFFERENTIAL = (
    "R2 self-reference: the reconstructed phase is the DIFFERENTIAL phi(r) - phi(r + s) of the "
    "object and its copy shifted by s (docs/03 section 6; model_assumptions B5), not a terrace "
    "phase; wherever r and r + s lie on one terrace it is 0, so region medians of it are not "
    "terrace phases. Quantification of a differential phase is NOT IMPLEMENTED (it needs the "
    "reference region traced through the same ray trace, audit A3 M1); every height of this run "
    "is withheld")


def _withhold_reason(control: dict) -> str | None:
    """Reason to withhold every height of the run, or None (audit A3 B1). The no-step control is
    the only in-pipeline check that the phase is flat within a terrace; without a passed control no
    height is returned."""
    if not control.get("performed"):
        return (f"{NO_HEIGHT_CONTROL} (not performed: {control.get('reason')}); every height of "
                f"this run is withheld")
    if not control.get("passed"):
        return (f"{NO_HEIGHT_CONTROL} (failed: delta = {control['delta_rad']:+.4f} rad, tolerance "
                f"{control['tolerance_rad']:.4f} rad = {control['n_sigma']:g} correlated standard "
                f"errors); every height of this run is withheld")
    return None


def _height_verdict(steps: list[dict], withhold: str | None, joint: dict) -> dict:
    n_h = sum(1 for s in steps if s.get("height"))
    if withhold is not None:
        line = f"NO HEIGHT: {withhold}"
    elif n_h:
        line = (f"{n_h} of {len(steps)} step heights returned (joint lattice branch "
                f"{joint.get('decision')}, chance-acceptance bound "
                f"{joint.get('chance_probability_bound', float('nan')):.3g} <= alpha "
                f"{joint.get('chance_level', float('nan')):.3g})")
    else:
        line = (f"NO HEIGHT: 0 of {len(steps)} step heights returned (joint lattice branch "
                f"{joint.get('decision')}: {joint.get('reason', '-')})")
    return dict(heights_returned=n_h, n_steps=len(steps), withheld=withhold is not None,
                withhold_reason=withhold, line=line)


def _sign_degeneracy(steps: list[dict], *, lam: float, theta: float, layer_A: float, n_max: int,
                     n_sigma: float) -> dict:
    """At the run's angle, the wrapped phases of +n a/4 and -n a/4 differ by
    |wrap(2 s n a/4)|; when that is below the single-step window 2 (n_sigma sigma_phi + n_sigma
    (sigma_s/s) s n a/4), one step alone cannot tell +n a/4 from -n a/4 (audit A3 m4: at the B32
    angle +a/2 and -a/2 differ by 0.078 rad). The joint rule can still separate them when the other
    steps pin the common angle error."""
    from reflection_holo.geometry.specular import wrap_to_pi
    measured = [st for st in steps if st.get("measured")]
    if not measured:
        return dict(note="no measured step", pairs=[])
    s = measured[0]["sensitivity_rad_per_A"]
    rel = measured[0]["sigma_sensitivity_rad_per_A"] / s
    sphi = max(st["sigma_delta_phi_rad"] for st in measured)
    pairs = []
    for n in range(1, n_max + 1):
        sep = abs(float(wrap_to_pi(2 * s * n * layer_A)))
        window = 2 * (n_sigma * sphi + n_sigma * rel * s * n * layer_A)
        pairs.append(dict(n=n, height_A=n * layer_A, wrapped_separation_rad=sep,
                          single_step_window_rad=window, degenerate_single_step=sep < window))
    bad = [f"+-{p['n']} a/4 ({p['wrapped_separation_rad']:.3f} rad < "
           f"{p['single_step_window_rad']:.3f} rad)" for p in pairs if p["degenerate_single_step"]]
    note = (f"at theta = {theta * 1e3:.6f} mrad the sign of {', '.join(bad)} cannot be decided from "
            f"one step (the wrapped phases of +n a/4 and -n a/4 are closer than the branch window); "
            f"only the joint rule with steps that pin the angle error can separate them" if bad else
            f"at theta = {theta * 1e3:.6f} mrad every +-n a/4 pair (n <= {n_max}) is separated by "
            f"more than the single-step branch window")
    return dict(note=note, pairs=pairs)


def run(config, out_dir, *, variant: str | None = None, allow_no_git: bool = False) -> dict:
    """Run the pipeline for ``config`` (a path, or a PipelineConfig already gated) into
    ``out_dir`` (created; must be empty). Returns the summary dictionary (also written)."""
    t0 = time.perf_counter()
    timing: dict[str, float] = {}
    if isinstance(config, PipelineConfig):
        cfg = config
        if variant is not None and variant != cfg.variant:
            raise PipelineConfigError("variant given twice with different values")
    else:
        cfg = load_pipeline_file(config, variant=variant)
    if cfg.test_only:
        # A2c G3: TEST_ONLY values (accepted by the loader only with allow_test_only=True, for
        # gate tests) never reach a pipeline run; the CLI never sets allow_test_only
        raise PipelineConfigError("the configuration contains TEST_ONLY values: a pipeline run "
                                  "refuses them (they exist for in-memory gate tests only; A2c G3)")
    # the manifest must identify the code: check the git state BEFORE any computation (A3 M5)
    git_preflight = require_git_state(allow_no_git=allow_no_git)
    require_engine(cfg)                     # multislice module and cupy/GPU, before computing (m5)
    out = _prepare_out(out_dir)
    notes: list[str] = []
    theta = float(cfg.glancing_angle["value_rad"])
    lam = wavelength_A(BEAM_ENERGY_SUPPLIED_KEV)
    b = cfg.cfg_b

    # 2. structure ---------------------------------------------------------------------------
    t = time.perf_counter()
    structure = build_structure(cfg)
    model = terrace_model_from_structure(structure)
    timing["structure_s"] = time.perf_counter() - t

    # 3. engine -------------------------------------------------------------------------------
    t = time.perf_counter()
    engine = cfg.value("engine", "name")
    engine_record: dict[str, Any] = dict(name=engine)
    if engine == "geometric":
        waves, model, grun = run_geometric(structure, cfg)
        layout = grun.layout
        engine_record.update(label=waves[0].metadata["label"], counts=grun.record,
                             steps=waves[0].metadata["steps"], b4=waves[0].metadata["b4"])
        engines_manifest = {"reflection_holo.forward.geometric": dict(
            version=reflection_holo.__version__, commit="this repository (see repository.commit)",
            licence="this repository", label=waves[0].metadata["label"])}
        cell = None
    else:
        if cfg.value("cell", "periods_along_beam") != 1:
            raise PipelineConfigError("the multislice reflection cell holds one structure period "
                                      "along the beam: cell.periods_along_beam must be 1")
        waves, cell, rec = run_multislice(structure, cfg, outputs_root=out / "outputs",
                                          run_name=cfg.run_name)
        lay = cell.metadata["layout"]
        layout = FieldLayout(field_length_A=float(cell.length_z_A),
                             z_start_A=float(cell.crystal_start_z_A),
                             x_offset_A=float(lay["lowest_surface_x_A"] - min(model.heights_A)),
                             periods=1, upstream="none")
        engine_record.update(label=f"multislice: {rec['validation_status']}", **rec)
        engines_manifest = {"reflection_holo.forward.multislice": dict(
            version=reflection_holo.__version__, commit="this repository (see repository.commit)",
            licence="this repository", status=rec["validation_status"],
            engine_manifest=rec["engine_manifest"])}
        notes.append("multislice engine status: " + str(rec["validation_status"]))
    timing["engine_s"] = time.perf_counter() - t

    # 4-6. dark field, projection, detector ----------------------------------------------------
    t = time.perf_counter()
    alpha, _ = b.quantity("objective_aperture_semi_angle")
    aperture = DarkFieldAperture(semi_angle_rad=alpha, beam=cfg.value("optics", "selected_beam"),
                                 label=_label(b.parameters["objective_aperture_semi_angle"]))
    spec = _detector_spec(cfg)
    H_ref = min(model.heights_A) + layout.x_offset_A
    x0 = H_ref + (layout.field_length_A - layout.z_start_A) * math.tan(theta)
    x0_def = (f"lowest terrace top (x = {H_ref:.6f} A in the exit-wave frame); z_s = 0 at the "
              f"upstream end of the terraces (z = {layout.z_start_A:.6f} A); exit plane "
              f"z = {layout.field_length_A:.6f} A")
    band = math.sin(alpha) / lam
    fov_u = (0.0, (layout.field_length_A - layout.z_start_A) * math.sin(theta))
    obj_waves, dfs, imgs = [], [], []
    placement = None
    for ew in waves:
        df = select_dark_field(ew, aperture, energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
                               theta_out_ext_rad=theta)
        img = project_along_k_out(df, x0_A=x0, x0_definition=x0_def, aperture_semi_angle_rad=alpha)
        det, placement = resample_to_detector(
            img, spec, band_cycles_per_A=band,
            field_of_view_u_A=fov_u if spec.alignment == "field_of_view" else None)
        obj_waves.append(det)
        if not dfs:
            dfs.append(df)
            imgs.append(img)
    timing["optics_s"] = time.perf_counter() - t

    # 7-9. references, holograms, detector noise ------------------------------------------------
    t = time.perf_counter()
    grid = spec.grid()
    # ray trace of every detector pixel to the built surface (also used by the quantification)
    tr = Q.detector_trace(model, placement.u_A, placement.y_A, x0_A=x0, theta_rad=theta,
                          layout=layout)
    a_all = np.abs(np.stack([w.data for w in obj_waves]))
    lit_px = np.broadcast_to(tr["status"] == Q.STATUS["lit"], a_all.shape)
    if not lit_px.any():
        raise RuntimeError("no detector pixel traces to a lit terrace top: the empty-object "
                           "amplitude is undefined")
    # A3 m3: the empty-object amplitude from LIT terrace-top pixels only (the multislice exit plane
    # also carries the field inside the crystal, which traces to no surface)
    bright = lit_px & (a_all >= 0.5 * a_all[lit_px].max())
    A_emp = float(np.sqrt(np.mean(a_all[bright] ** 2)))
    amp_by_status = {name: dict(n_px=int((tr["status"] == c).sum()),
                                mean_abs=(float(a_all[:, tr["status"] == c].mean())
                                          if (tr["status"] == c).any() else None))
                     for name, c in Q.STATUS.items()}
    ratio = cfg.rec("reference", "amplitude_ratio").canonical_value
    q_ref = _carrier(cfg)
    ref_model = b.value("reference_model")
    trajectory = b.value("reference_trajectory")
    expected_traj = {"R1": "vacuum_beside_sample", "R2": "reflected_flat_area"}
    if ref_model not in expected_traj:
        raise PipelineConfigError(f"reference model {ref_model!r}: the pipeline implements R1 "
                                  f"and R2 (R3 NOT IMPLEMENTED here)")
    if trajectory != expected_traj[ref_model]:
        raise PipelineConfigError(f"reference model {ref_model} needs reference_trajectory "
                                  f"{expected_traj[ref_model]!r} (item 15), got {trajectory!r}")
    rel_phase = cfg.value("reference", "relative_phase_rad")
    passage = cfg.rec("reference", "aperture_passage").value
    vac = vacuum_object_wave(grid, amplitude=A_emp, realisation=0)

    def reference_for(obj: Wave) -> Wave:
        if ref_model == "R1":
            return reference_r1_vacuum_plane_wave(grid, carrier_cycles_per_A=q_ref,
                                                  amplitude=ratio * A_emp,
                                                  relative_phase_rad=rel_phase,
                                                  aperture_passage=passage,
                                                  realisation=obj.realisation)
        shift_rec = cfg.sections["reference"].get("shift")
        if shift_rec is None:
            raise PipelineConfigError("R2 needs sections.reference.shift (item 16)")
        sh = shift_rec.canonical_value
        return reference_r2_self_reference(obj, shift_A=(sh["along_beam"], sh["perpendicular"]),
                                           carrier_cycles_per_A=q_ref, amplitude_scale=ratio,
                                           relative_phase_rad=rel_phase)

    artefacts = ArtefactOptions(biprism_fresnel_fringes=None, drift=None, charging_phase_rad=None)
    refs = [reference_for(o) for o in obj_waves]
    H_obj = ensemble_hologram_intensity(list(zip(obj_waves, refs)), artefacts=artefacts,
                                        content="object")
    ref_emp = reference_for(vac)
    H_emp = hologram_intensity(vac, ref_emp, artefacts=artefacts, content="empty")
    seed = cfg.value("detector", "noise_seed")
    H_obj_n, H_emp_n = record_holograms([H_obj, H_emp], spec, seed=seed)
    timing["holography_s"] = time.perf_counter() - t

    # 10. reconstruction ---------------------------------------------------------------------------
    t = time.perf_counter()
    proc = cfg.rec("reconstruction", "processing").value
    qm = math.hypot(*q_ref)
    search = CarrierSearch(
        sideband_guess_cycles_per_A=(-q_ref[0], -q_ref[1]),
        search_radius_cycles_per_A=proc["search_radius_fraction"] * qm,
        exclusion_radius_cycles_per_A=proc["exclusion_radius_fraction"] * qm,
        subpixel=proc["subpixel"],
        sideband_declaration="simulation: -q_ref of the declared reference (the phi_o - phi_r "
                             "sideband; model_assumptions B15)")
    loc = locate_carrier(H_emp_n, search)
    mask = MaskSpec(radius_cycles_per_A=proc["mask_radius_fraction"]
                    * loc.carrier_magnitude_cycles_per_A, shape="disc",
                    apodisation=proc["apodisation"])
    divide = proc["reference_correction"] == "divide_empty"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        recon = reconstruct_sideband(
            H_obj_n, carrier=loc, mask=mask, empty_hologram=H_emp_n if divide else None,
            reference_correction=proc["reference_correction"], unwrapping=proc["unwrapping"],
            empty_min_visibility=proc["empty_min_visibility"] if divide else None,
            object_min_visibility=None if divide else proc["object_min_visibility"])
    recon_warnings = [str(w.message) for w in caught]
    timing["reconstruction_s"] = time.perf_counter() - t

    # 11. quantification ---------------------------------------------------------------------------
    t = time.perf_counter()
    qp = cfg.rec("quantification", "processing").value
    phase = np.asarray(recon.wrapped_phase)
    amp_rel = np.asarray(recon.amplitude, dtype=float)       # |u_o| / A_emp with divide_empty
    if not divide:                                           # relative to the median lit amplitude
        lit_amp = amp_rel[(tr["status"] == Q.STATUS["lit"]) & np.isfinite(amp_rel)]
        amp_rel = amp_rel / float(np.median(lit_amp)) if lit_amp.size else amp_rel * np.nan
    strong = np.isfinite(amp_rel) & (amp_rel >= qp["min_relative_amplitude"])
    usable = ((tr["status"] == Q.STATUS["lit"]) & recon.valid_mask & np.isfinite(phase)
              & strong)
    res_A = float(recon.resolution_A)
    p_A = spec.pixel_A
    m0 = int(math.ceil(qp["edge_margin_resolutions"] * res_A / p_A[0]))
    m1 = int(math.ceil(qp["edge_margin_resolutions"] * res_A / p_A[1]))
    W = np.asarray(recon.mask)
    a_eff = float(W.size / np.sum(W ** 2))
    regions: dict[int, dict] = {}
    region_map = np.full(grid.shape, -1, dtype=np.int64)
    for f in sorted(int(v) for v in np.unique(tr["field_terrace"]) if v >= 0):
        good = usable & (tr["field_terrace"] == f)
        reg = Q.box_erode(good, m0, m1)
        n_px = int(reg.sum())
        rec_f: dict[str, Any] = dict(field_terrace=f, terrace=f % model.n_terraces,
                                     n_usable_px=int(good.sum()), n_region_px=n_px,
                                     measurable=n_px >= qp["min_region_px"])
        if n_px > 0:
            if np.any(tr["status"][reg] != Q.STATUS["lit"]):
                raise RuntimeError("a quantification region contains a pixel that is not a lit "
                                   "terrace top (shadow exclusion failed)")
            rec_f["phase"] = Q.region_phase(phase, reg, a_eff)
            region_map[reg] = f
        regions[f] = rec_f
    theta_sigma = cfg.rec("illumination", "angle_calibration_sigma").canonical_value
    wl_sigma = cfg.rec("illumination", "wavelength_sigma_rel").canonical_value
    a_lat, _ = b.quantity("lattice_parameter")
    # the no-step control FIRST: its verdict decides whether any height may be returned (A3 B1)
    measurable = [r for r in regions.values() if r["measurable"]]
    if measurable:
        big = max(measurable, key=lambda r: r["n_region_px"])
        control = Q.no_step(phase, region_map == big["field_terrace"], a_eff, qp["n_sigma"],
                            recon.valid_mask)
        control["field_terrace"] = big["field_terrace"]
    else:
        control = dict(performed=False, reason="no measurable flat region")
    withhold = _withhold_reason(control)
    if ref_model == "R2":
        withhold = R2_DIFFERENTIAL
    steps, joint_branch = Q.measure_steps(
        phase=phase, regions=regions, a_eff_px=a_eff,
        field_steps=_field_steps(model, layout, ref_model), wavelength_A=lam, theta_rad=theta,
        sigma_theta_rad=theta_sigma, sigma_wavelength_rel=wl_sigma, layer_A=a_lat / 4.0,
        n_max=qp["max_layers"], n_sigma=qp["n_sigma"],
        branch_source=(f"joint lattice constraint: h = n a/4 with 1 <= |n| <= "
                       f"{qp['max_layers']} over the steps of the run, one common angle "
                       f"calibration (stand-in "
                       f"{cfg.rec('quantification', 'processing').assumption_id}); not a rocking "
                       f"series"),
        withhold_reason=withhold)
    height_verdict = _height_verdict(steps, withhold, joint_branch)
    degeneracy = _sign_degeneracy(steps, lam=lam, theta=theta, layer_A=a_lat / 4.0,
                                  n_max=qp["max_layers"], n_sigma=qp["n_sigma"])
    strips = terrace_shadow_strips(structure, theta, _label(cfg.rec("illumination",
                                                                    "glancing_angle")),
                                   theta_out_ext_rad=theta,
                                   theta_out_label=_label(cfg.rec("illumination",
                                                                  "glancing_angle")))
    status_counts = {name: int((tr["status"] == c).sum()) for name, c in Q.STATUS.items()}
    shadow = dict(
        rule="docs/03 section 4; B9: illumination shadow h/tan(theta_in) behind a riser whose "
             "upper terrace is upstream, blocked-view strip h/tan(theta_out) in front of one whose "
             "upper terrace is downstream; computed at the operating angle "
             f"{theta * 1e3:.6f} mrad",
        surface_strips=dict(illumination_intervals_A=[list(v) for v in
                                                      strips.illumination_intervals_A],
                            blocked_view_intervals_A=[list(v) for v in
                                                      strips.blocked_view_intervals_A],
                            per_step=[dict(v) for v in strips.per_step], note=strips.note),
        detector_status_counts=status_counts,
        excluded_px=int((~usable).sum()), usable_px=int(usable.sum()),
        blocked_view_note="blocked-view strips are not imaged: the backward ray from the exit "
                          "plane meets the upper terrace first (their surface intervals are "
                          "listed above)",
        regions_contain_only_lit_pixels=True,
        margin_px=[m0, m1], margin_resolutions=qp["edge_margin_resolutions"],
        weak_object_px=int(((tr["status"] == Q.STATUS["lit"]) & ~strong).sum()),
        min_relative_amplitude=qp["min_relative_amplitude"],
        amplitude_rule="usable only where the reconstructed object amplitude relative to the "
                       "empty-hologram object amplitude is at least min_relative_amplitude "
                       "(no object wave, no phase)")
    contrast_empty = fringe_contrast(A_emp, ratio * A_emp)
    noise_pred = sideband_phase_noise(contrast_empty, spec.dose_e_per_px, W)
    timing["quantification_s"] = time.perf_counter() - t

    # 12. outputs ------------------------------------------------------------------------------------
    t = time.perf_counter()
    ew0, df0, img0 = waves[0], dfs[0], imgs[0]
    arrays = {
        "exit_psi_r0": (np.asarray(ew0.psi), ["x", "y"], "arbitrary amplitude", ew0.plane),
        "exit_x_A": (float(ew0.x0_A) + ew0.dx_A * np.arange(ew0.psi.shape[0]), ["x"], "A",
                     ew0.plane),
        "exit_y_A": (float(ew0.y0_A) + ew0.dy_A * np.arange(ew0.psi.shape[1]), ["y"], "A",
                     ew0.plane),
        "darkfield_r0": (np.asarray(df0.wave.data), ["x", "y"], "arbitrary amplitude",
                         df0.wave.grid.plane),
        "projected_r0": (np.asarray(img0.wave.data), ["along_beam", "perpendicular"],
                         "arbitrary amplitude", img0.wave.grid.plane),
        "projected_surface_z_A": (img0.surface_z_A, ["along_beam"], "A (nominal z_s)",
                                  img0.wave.grid.plane),
        "projected_image_u_A": (img0.image_u_A, ["along_beam"], "A (image plane)",
                                img0.wave.grid.plane),
        "detector_object_r0": (np.asarray(obj_waves[0].data), ["along_beam", "perpendicular"],
                               "arbitrary amplitude", grid.plane),
        "detector_reference_r0": (np.asarray(refs[0].data), ["along_beam", "perpendicular"],
                                  "arbitrary amplitude", grid.plane),
        "detector_u_A": (placement.u_A, ["along_beam"], "A (image plane)", grid.plane),
        "detector_y_A": (placement.y_A, ["perpendicular"], "A (image plane)", grid.plane),
        "hologram_object_noiseless": (np.asarray(H_obj.intensity), ["along_beam", "perpendicular"],
                                      "relative intensity", grid.plane),
        "hologram_object_counts": (np.asarray(H_obj_n.intensity), ["along_beam", "perpendicular"],
                                   "counts", grid.plane),
        "hologram_empty_noiseless": (np.asarray(H_emp.intensity), ["along_beam", "perpendicular"],
                                     "relative intensity", grid.plane),
        "hologram_empty_counts": (np.asarray(H_emp_n.intensity), ["along_beam", "perpendicular"],
                                  "counts", grid.plane),
        "phase_wrapped_raw": (np.asarray(recon.wrapped_phase_raw), ["along_beam", "perpendicular"],
                              "rad", grid.plane),
        "phase_wrapped": (phase, ["along_beam", "perpendicular"], "rad", grid.plane),
        "phase_unwrapped": (np.asarray(recon.unwrapped_phase) if recon.unwrapped_phase is not None
                            else np.full(grid.shape, np.nan), ["along_beam", "perpendicular"],
                            "rad", grid.plane),
        "amplitude": (np.asarray(recon.amplitude), ["along_beam", "perpendicular"], "relative",
                      grid.plane),
        "valid_mask": (np.asarray(recon.valid_mask), ["along_beam", "perpendicular"], "bool",
                       grid.plane),
        "trace_status": (tr["status"], ["along_beam", "perpendicular"],
                         f"code {Q.STATUS}", grid.plane),
        "trace_field_terrace": (tr["field_terrace"], ["along_beam", "perpendicular"],
                                "index (-1 none)", grid.plane),
        "trace_source_z_A": (tr["source_z_A"], ["along_beam", "perpendicular"],
                             "A (surface z of the traced source; NaN none)", grid.plane),
        "usable_mask": (usable, ["along_beam", "perpendicular"], "bool", grid.plane),
        "region_map": (region_map, ["along_beam", "perpendicular"], "field terrace (-1 none)",
                       grid.plane),
    }
    arrays["purpose"] = (np.array(cfg.purpose), ["none (0-d scalar)"], "text (run purpose)",
                         "not a wave: run metadata (audit A3 m1)")
    with open(out / "arrays.npz", "xb") as fh:          # never overwrite (A3 n3)
        np.savez_compressed(fh, **{k: v[0] for k, v in arrays.items()})
    array_index = {k: dict(axes=v[1], units=v[2], plane=v[3], shape=list(np.shape(v[0])),
                           dtype=str(np.asarray(v[0]).dtype)) for k, v in arrays.items()}
    ga = dict(cfg.glancing_angle)
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
            used_for_glancing_angle_V=ga.get("V0_V"), V0_source=ga.get("V0_source"),
            engine_potential=engine_record.get("mip_check")),
        structure=dict(positions_sha256=structure.metadata["positions_sha256"],
                       n_atoms=structure.n_atoms, staircase=structure.metadata["staircase"],
                       terrace_map=[{k: v for k, v in tmap.items()}
                                    for tmap in structure.metadata["terrace_map"]],
                       azimuth=structure.metadata["azimuth"],
                       options=structure.metadata["options"]),
        engine={k: v for k, v in engine_record.items()},
        exit_wave=dict(plane=ew0.plane, z_A=ew0.z_A, dx_A=ew0.dx_A, dy_A=ew0.dy_A, x0_A=ew0.x0_A,
                       y0_A=ew0.y0_A, shape=list(ew0.psi.shape), dtype=str(ew0.psi.dtype),
                       n_realisations=len(waves), realisations=[w.realisation for w in waves],
                       seeds=[w.seed for w in waves]),
        dark_field=df0.record, projection=dict(img0.record, sampling=img0.sampling),
        detector=dict(spec.as_record(theta), placement=placement.record,
                      empty_object_amplitude=A_emp,
                      empty_object_amplitude_rule="RMS of the detector object amplitude over the "
                                                  "LIT terrace-top pixels >= half their maximum "
                                                  "(audit A3 m3)",
                      object_amplitude_by_trace_status=amp_by_status),
        reference=dict(model=ref_model, trajectory=trajectory, carrier_cycles_per_A=list(q_ref),
                       amplitude=ratio * A_emp, amplitude_ratio=ratio, relative_phase_rad=rel_phase,
                       aperture_passage=passage, empty_hologram_fringe_contrast=contrast_empty,
                       noise_seed=seed),
        hologram=dict(object={k: v for k, v in H_obj.metadata.items() if k != "valid_mask"},
                      empty_formation=H_emp.metadata.get("formation"),
                      ensemble_rule="intensities averaged over realisations AFTER squaring"),
        reconstruction=dict(parameters=recon.parameters, resolution_A=res_A,
                            resolution_fringe_spacings=recon.resolution_fringe_spacings,
                            sideband_sign_check=recon.sideband_sign_check,
                            warnings=recon_warnings,
                            predicted_phase_noise_per_px=noise_pred),
        quantification=dict(height_verdict=height_verdict, steps=steps,
                            joint_branch=joint_branch, sign_degeneracy=degeneracy,
                            regions={str(k): v for k, v in regions.items()},
                            no_step_control=control, shadow_exclusion=shadow,
                            a_eff_px=a_eff, sigma_source="measured phase scatter (B16: measured, "
                                                         "not guessed)",
                            region_source="ray-traced geometry of the built structure"),
        not_implemented=NOT_IMPLEMENTED, notes=notes, arrays=array_index,
        timing_s=timing,
    )
    summary["timing_s"]["outputs_s"] = time.perf_counter() - t
    summary["timing_s"]["total_s"] = time.perf_counter() - t0
    quick = []
    if cfg.value("outputs", "quicklooks"):
        quick = _quicklooks(out, arrays, cfg)
    summary["quicklooks"] = quick
    manifest = build_manifest(
        run_name=f"{cfg.run_name}{'_' + cfg.variant if cfg.variant else ''}", config=cfg.cfg_b,
        input_paths=[cfg.source_path] if cfg.source_path else [],
        seeds=dict(detector_noise=seed, engine=[w.seed for w in waves]),
        thread_count=cfg.value("runtime", "threads"),
        precision=dict(pipeline_complex="complex128", pipeline_real="float64",
                       exit_wave=str(ew0.psi.dtype)),
        engines=engines_manifest,
        wave_planes={"exit_wave": ew0.plane, "dark_field": df0.wave.grid.plane,
                     "projected": img0.wave.grid.plane, "detector": grid.plane},
        beam_energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
        extra=dict(purpose=cfg.purpose, variant=cfg.variant, test_only=cfg.test_only,
                   allow_test_only="never set by a pipeline run or the CLI (A2c G3)",
                   pipeline_config_sha256_file=cfg.sha256_file,
                   pipeline_config_sha256_resolved=cfg.sha256_resolved,
                   structure_positions_sha256=structure.metadata["positions_sha256"],
                   glancing_angle=ga, engine_label=engine_record.get("label"),
                   git_preflight=git_preflight, height_verdict=height_verdict),
        allow_no_git=allow_no_git)
    with open(out / "manifest.json", "x", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    with open(out / "summary.json", "x", encoding="utf-8") as fh:
        json.dump(_jsonable(summary), fh, indent=2)
        fh.write("\n")
    return summary


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, Record):
        return dict(value=x.value, unit=x.unit, label=x.label, source=x.source, item=x.item,
                    assumption_id=x.assumption_id)
    if isinstance(x, np.ndarray):
        return dict(array_shape=list(x.shape), dtype=str(x.dtype),
                    note="array not stored in the summary")
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, float) and not math.isfinite(x):
        return str(x)
    if isinstance(x, Path):
        return str(x)
    return x


def _quicklooks(out: Path, arrays: dict, cfg: PipelineConfig) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return ["skipped: matplotlib is not importable"]
    files = []
    banner = f"{cfg.run_name}: {cfg.purpose}"
    fig, ax = plt.subplots(1, 4, figsize=(16, 4.5))
    panels = [("hologram_object_counts", "object hologram (counts)", "gray"),
              ("phase_wrapped", "reconstructed phase (rad)", "twilight"),
              ("amplitude", "reconstructed amplitude", "gray"),
              ("region_map", "quantification regions", "tab10")]
    for a, (key, title, cmap) in zip(ax, panels):
        im = a.imshow(np.asarray(arrays[key][0], float), cmap=cmap, aspect="auto",
                      interpolation="nearest")
        a.set_title(title, fontsize=9)
        a.set_xlabel("perpendicular (px)")
        a.set_ylabel("along beam (px, downstream)")
        fig.colorbar(im, ax=a, shrink=0.8)
    fig.suptitle(banner, fontsize=9)
    fig.tight_layout()
    p = out / "quicklook_detector.png"
    fig.savefig(p, dpi=90)
    plt.close(fig)
    files.append(p.name)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    psi = np.asarray(arrays["exit_psi_r0"][0])
    ax[0].imshow(np.abs(psi).T, aspect="auto", cmap="gray", origin="lower")
    ax[0].set_title("|exit wave| (x horizontal, y vertical)", fontsize=9)
    col = psi[:, psi.shape[1] // 2]
    ax[1].plot(arrays["exit_x_A"][0], np.abs(col))
    ax[1].set_xlabel("exit-plane x (A)")
    ax[1].set_title("|exit wave| on one column", fontsize=9)
    fig.suptitle(banner, fontsize=9)
    fig.tight_layout()
    p = out / "quicklook_exit_wave.png"
    fig.savefig(p, dpi=90)
    plt.close(fig)
    files.append(p.name)
    return files
