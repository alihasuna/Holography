#!/usr/bin/env python3
"""Parameters, derived quantities and key results of every smoke test S1-S9 (agent R1).

Usage (repository root; the saved output is tools/report/smoke_parameters_output.txt):
    PYTHONPATH=. venv/bin/python tools/report/smoke_parameters.py --runs SP/report_smoke \
        --t1-runs SP/torus --t1-rerun SP/torus_ms --buried SP/buried \
        --t5-output tools/review/t5/buried_torus_analysis_output.txt

Every value comes from a file or from the package's own code:
  * the configuration of S1-S6 and S9 through the package's loader
    reflection_holo.pipeline.config.load_pipeline_file(path, variant=...), grouped by stage, each
    value with its unit and its label exactly as the configuration states it (label, assumption id,
    the docs/06 item it stands in for; plain numerical settings carry no label and are marked so);
  * the values the code computed for each run and the key results from that run's summary.json,
    manifest.json and engine manifest (runs of tools/report/run_smoke_campaign.py, campaign log
    ROOT/campaign_log.json);
  * S7 (atomistic half torus, report T1) and S8 (buried torus void, reports T3/T5) are NOT rerun:
    their parameters are printed from the saved case_*.json and summary_*.json files, their results
    from the saved summaries and (S8) verbatim lines of the T5 analysis output;
  * derived quantities (wavelength, k, (0,0,8) angles, step phases, height per phase wrap) from
    reflection_holo.geometry and reflection_holo.quantification.height, cross-checked against the
    reference calculator tools/reflection_step_phase_calculator.py (docs/agent_reports/
    C_calculator_output.txt).
DEMO runs: not comparable to experiment. The multislice engine is UNVALIDATED for step heights
(engine VALIDATION_STATUS, printed once below). Beam energy 200 keV (300 keV never used).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from reflection_holo.geometry.specular import (specular_condition_for,  # noqa: E402
                                               specular_step_phase, wrap_to_pi)
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A  # noqa: E402
from reflection_holo.pipeline.config import Record, load_pipeline_file  # noqa: E402
from reflection_holo.quantification.height import wrap_period_A  # noqa: E402


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CAMPAIGN = _load_module("run_smoke_campaign", REPO / "tools" / "report" / "run_smoke_campaign.py")

ENERGY_KEV = 200.0                     # PROJECT_INPUT item 1 (supplied by Ali 2026-09-22)
A_SI = 5.4309                          # ASSUMPTION (model_assumptions B2), as in every config
STAGES = ["specimen/structure", "cell", "engine", "illumination", "optics", "reference", "detector",
          "reconstruction", "quantification", "runtime/outputs", "other"]
SECTION_STAGE = {"structure": "specimen/structure", "cell": "cell", "engine": "engine",
                 "illumination": "illumination", "optics": "optics", "reference": "reference",
                 "detector": "detector", "reconstruction": "reconstruction",
                 "quantification": "quantification", "runtime": "runtime/outputs",
                 "outputs": "runtime/outputs"}
CFGB_STAGE = {
    "surface_material": "specimen/structure", "surface_normal_hkl": "specimen/structure",
    "lattice_parameter": "specimen/structure", "mean_inner_potential_V": "specimen/structure",
    "step_types": "specimen/structure", "step_translations": "specimen/structure",
    "pattern_geometry": "specimen/structure", "surface_preparation_method": "specimen/structure",
    "surface_preparation_details": "specimen/structure",
    "beam_energy_keV": "illumination", "beam_azimuth_uvw": "illumination",
    "target_reflection_hkl": "illumination", "forbidden_rod_reflections_hkl": "illumination",
    "convergence_semi_angle": "illumination", "glancing_angle_ext": "illumination",
    "objective_aperture_semi_angle": "optics",
    "reference_trajectory": "reference", "reference_model": "reference",
    "image_pixel_size": "detector"}
CELL_KEYS = {"geometric": {"exit_plane_pixel_A", "n_y", "x_margin_A", "field_length_A",
                           "surface_dz_A"},
             "multislice": {"nx", "ny", "dz_A", "absorber", "buildup_depth_A"}}
ILLUM_KEYS = {"multislice": {"sheet_beam"}}
PLAIN = "plain setting (no label; not a docs/06 item)"
OXIDE_LABEL_KEYS = {"thickness_A": "thickness", "density_g_cm3": "density",
                    "consumed_layers": "consumed_layers", "V_real_V": "V_real",
                    "V_imag_V": "V_imag", "vacuum_edge_width_A": "vacuum_edge",
                    "interface_width_A": "interface", "amorphous_si_thickness_A": "amorphous_si"}


# ------------------------------------------------------------------------------------------------
# formatting
# ------------------------------------------------------------------------------------------------
def fmt(v) -> str:
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v, default=str)
    return str(v)


def label_of(r) -> str:
    """Label exactly as the configuration states it: label, assumption id, item stood in for;
    for a supplied PROJECT_INPUT the item and the supplier/date."""
    lab = r.label
    aid = getattr(r, "assumption_id", None)
    out = lab + (f" {aid}" if aid else "")
    item = getattr(r, "item", None)
    sif = getattr(r, "stands_in_for_item", None)
    if lab == "PROJECT_INPUT":
        sup = getattr(r, "supply", None) or {}
        out += f" item {item}"
        if sup:
            out += f" (supplied by {sup.get('supplied_by')} {sup.get('supplied_on')})"
    elif sif is not None:
        out += f" (stands in for PROJECT_INPUT item {sif})"
    if lab in ("ASSUMPTION", "REPRODUCED", "DERIVED_HERE") and not aid:
        src = " ".join(str(getattr(r, "source", "") or "").split())
        out += f" [no assumption_id field; source: {src[:90]}{'...' if len(src) > 90 else ''}]"
    return out


def rows_of_config(cfg) -> list[tuple]:
    """(stage, name, value, unit, label) for every CFG-B parameter and every pipeline section
    entry of the loaded configuration; nothing is dropped (unmapped entries go to 'other')."""
    rows = []
    for name, p in cfg.cfg_b.parameters.items():
        stage = CFGB_STAGE.get(name, "other")
        lab = label_of(p)
        if name == "surface_preparation_details" and isinstance(p.value, dict):
            for k, v in p.value.items():
                if k == "overlayer" and isinstance(v, dict):
                    labels = v.get("labels", {})
                    for kk, vv in v.items():
                        if kk == "labels":
                            continue
                        lk = OXIDE_LABEL_KEYS.get(kk)
                        l2 = (labels[lk] + " (per-parameter label of the config)"
                              if lk in labels else lab)
                        unit = ("A" if kk.endswith("_A") else "V" if kk.endswith("_V") else
                                "g/cm^3" if kk.endswith("_g_cm3") else "none")
                        rows.append((stage, f"cfg_b.{name}.overlayer.{kk}", fmt(vv), unit, l2))
                else:
                    rows.append((stage, f"cfg_b.{name}.{k}", fmt(v), p.unit, lab))
            continue
        rows.append((stage, f"cfg_b.{name}", fmt(p.value), p.unit, lab))
    engine_name = cfg.sections["engine"]["name"]
    for sec, d in cfg.sections.items():
        stage0 = SECTION_STAGE.get(sec, "other")
        for name, v in d.items():
            full = f"sections.{sec}.{name}"
            if isinstance(v, Record):
                if isinstance(v.value, dict) and name in ("staircase", "processing",
                                                          "feature_processing", "feature"):
                    for k, vv in v.value.items():
                        rows.append((stage0, f"{full}.{k}", fmt(vv), v.unit, label_of(v)))
                else:
                    rows.append((stage0, full, fmt(v.value), v.unit, label_of(v)))
                continue
            if sec == "engine" and isinstance(v, dict) and name in ("geometric", "multislice"):
                if name != engine_name:
                    rows.append(("engine", full, "(block present in the resolved configuration; "
                                 f"NOT USED: the engine is {engine_name})", "", PLAIN))
                    continue
                for k, vv in v.items():
                    stage = ("cell" if k in CELL_KEYS.get(name, ()) else
                             "illumination" if k in ILLUM_KEYS.get(name, ()) else "engine")
                    if isinstance(vv, Record):
                        rows.append((stage, f"{full}.{k}", fmt(vv.value), vv.unit, label_of(vv)))
                    else:
                        lab = PLAIN
                        if k == "static_lattice_label" and vv:
                            lab = "label text of the config (the value itself)"
                        rows.append((stage, f"{full}.{k}", fmt(vv), "", lab))
                continue
            if isinstance(v, dict):
                for k, vv in v.items():
                    if isinstance(vv, Record):
                        rows.append((stage0, f"{full}.{k}", fmt(vv.value), vv.unit, label_of(vv)))
                    else:
                        rows.append((stage0, f"{full}.{k}", fmt(vv), "", PLAIN))
                continue
            rows.append((stage0, full, fmt(v), "", PLAIN))
    return rows


def print_rows(rows):
    for stage in STAGES:
        sel = [r for r in rows if r[0] == stage]
        if not sel:
            continue
        print(f"  [{stage}]")
        for _, name, val, unit, lab in sel:
            u = f" [{unit}]" if unit and unit != "none" else (" [none]" if unit == "none" else "")
            print(f"    {name} = {val}{u}  | {lab}")


def diff_rows(rows, base_rows) -> list[str]:
    b = {(r[1]): r for r in base_rows}
    c = {(r[1]): r for r in rows}
    out = []
    for k in sorted(set(b) | set(c)):
        if k not in b:
            out.append(f"    + {k} = {c[k][2]} [{c[k][3]}] | {c[k][4]}  (not in S1)")
        elif k not in c:
            out.append(f"    - {k} (in S1 = {b[k][2]}; absent here)")
        elif b[k][2:] != c[k][2:]:
            out.append(f"    ~ {k}: S1 {b[k][2]} [{b[k][3]}] | {b[k][4]}  ->  {c[k][2]} [{c[k][3]}]"
                       f" | {c[k][4]}")
    return out


# ------------------------------------------------------------------------------------------------
# derived quantities
# ------------------------------------------------------------------------------------------------
def derived_block(c_calc_path: Path) -> None:
    print("=" * 100)
    print("D. DERIVED QUANTITIES (DERIVED_HERE by this script with the package's functions; "
          "200 keV = PROJECT_INPUT item 1)")
    print("=" * 100)
    calc = _load_module("reflection_step_phase_calculator",
                        REPO / "tools" / "reflection_step_phase_calculator.py")
    lam = float(wavelength_A(ENERGY_KEV))
    lam_c = float(calc.wavelength_A(ENERGY_KEV))
    k = float(k_ang_per_A(ENERGY_KEV))
    print(f"  wavelength lambda(200 keV) = {lam:.8f} A (reflection_holo.geometry.wavelength); "
          f"reference calculator {lam_c:.8f} A; relative difference {abs(lam - lam_c) / lam:.2e}")
    print(f"  k = 2 pi / lambda = {k:.4f} rad/A")
    d008 = A_SI / 8.0
    thB = math.asin(lam / (2.0 * d008))
    print(f"  a = {A_SI} A (ASSUMPTION, model_assumptions B2); d_008 = a/8 = {d008:.5f} A; vacuum "
          f"Bragg angle of (0,0,8) asin(lambda/(2 d_008)) = {thB * 1e3:.4f} mrad")
    lines = c_calc_path.read_text().splitlines()
    for i, ln in enumerate(lines, 1):
        if ln.strip().startswith("200.0") and "0.0250793" in ln:
            print(f"  C calculator ({c_calc_path.relative_to(REPO)} line {i}, verbatim): {ln.strip()}")
            break
    cases = [(12.0, "V0 = 12.0 V (ASSUMPTION B1): geometric demos S1, S4, S5 geometric, S6 "
                    "(glancing-angle rule B19)"),
             (13.903, "V0 = 13.903 V (REPRODUCED: Kirkland IAM MIP, report D3 F16): multislice demos "
                      "S2, S3, S5 multislice, S7, S8, S9 (glancing-angle rule B32)")]
    for V0, what in cases:
        sc = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=ENERGY_KEV, V0_V=V0, a_A=A_SI)
        th = float(sc.theta_ext)
        s = 4.0 * math.pi * math.sin(th) / lam
        h2pi = lam / (2.0 * math.sin(th))
        h2pi_pkg = wrap_period_A(wavelength_A=lam, theta_in_ext_rad=th, theta_out_ext_rad=th)
        print(f"  --- (0,0,8) specular condition, {what}")
        print(f"      internal angle {float(sc.theta_int) * 1e3:.4f} mrad; EXTERNAL glancing angle "
              f"{th * 1e3:.4f} mrad (geometry.specular.specular_condition_for)")
        print(f"      height sensitivity s = 4 pi sin(theta)/lambda = {s:.4f} rad/A; height per 2 pi "
              f"phase wrap h_2pi = lambda/(2 sin theta) = {h2pi:.4f} A "
              f"(quantification.height.wrap_period_A: {h2pi_pkg:.4f} A)")
        for name, h in (("a/4 up-step (+1.357725 A)", A_SI / 4), ("a/2 up-step (+2.71545 A)", A_SI / 2)):
            ph = float(specular_step_phase(h, th, lam))
            w = float(wrap_to_pi(ph))
            print(f"      {name}: step phase -(4 pi/lambda) h sin(theta) = {ph:+.4f} rad = "
                  f"{ph / (2 * math.pi):+.4f} x 2 pi; wrapped to (-pi, pi]: {w:+.4f} rad, the phase "
                  f"of an apparent step of {-w / s:+.4f} A")
    for i, ln in enumerate(lines, 1):
        if ln.strip().startswith("(0, 0, 8)") and "16.474" in ln:
            print(f"  C calculator (0,0,8) at 200 keV, V0 = 12 V (line {i}, verbatim; columns: "
                  f"th_int, th_ext mrad, h_2pi A, |dphi| mod 2pi, /2pi, wrapped, for a/4 and a/2):")
            print(f"      {ln.strip()}")
    print("  Sign convention: exp(+i(k.r - omega t)); Delta_phi = phi(upper) - phi(lower) = "
          "-(k_out - k_in).R, external angles, vacuum wavelength (docs/physics_conventions.md).")


# ------------------------------------------------------------------------------------------------
# per run: values computed by the code and results
# ------------------------------------------------------------------------------------------------
def _engine_manifest(s: dict, run_dir: Path) -> dict | None:
    eng = s.get("engine", {})
    p = eng.get("engine_manifest")
    if p is None and isinstance(eng.get("engine_manifests"), dict):   # convergence: per member
        p = eng["engine_manifests"].get("0")
    if not p:
        return None
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def computed_block(s: dict, run_dir: Path) -> None:
    ga = s["glancing_angle"]
    print("  values computed by the code for this run (summary.json / engine manifest):")
    print(f"    beam energy {s['beam_energy_keV']} keV; wavelength {s['wavelength_A']:.8f} A")
    print(f"    glancing angle (external) {ga['value_mrad']:.4f} mrad = rule {ga.get('rule')} for "
          f"{ga.get('reflection_hkl')} with V0 = {ga.get('V0_V')} V from {ga.get('V0_source')}; "
          f"internal {ga['theta_int_rad'] * 1e3:.4f} mrad; h_2pi {ga['h_2pi_A']:.4f} A | "
          f"{ga.get('label')} {ga.get('assumption_id')}")
    ew = s["exit_wave"]
    print(f"    exit wave: {ew['plane']}; shape {ew['shape']} (x, y), dx {ew['dx_A']:.4f} A, dy "
          f"{ew['dy_A']:.4f} A, z {ew['z_A']:.3f} A; realisations {ew['n_realisations']}, seeds "
          f"{ew['seeds']}")
    st = s["structure"]
    if "terrace_map" in st and st["terrace_map"]:
        tm = st["terrace_map"]
        lens = [t["s_range_A"][1] - t["s_range_A"][0] for t in tm]
        tops = [t.get("top_height_A") for t in tm]
        print(f"    structure: {st['n_atoms']} atoms; terrace lengths along the beam "
              f"{[round(v, 3) for v in lens]} A; terrace top heights {tops} A; top layers relative "
              f"{[t['top_layer_relative'] for t in tm]} x a/4")
    elif "feature" in s:
        f = s["feature"]
        hf = f.get("height_field", {})
        print(f"    structure: height field of {f['shape']['kind']} {f['shape']['sub_kind']} (R "
              f"{f['shape']['major_radius_A']} A, r {f['shape']['minor_radius_A']} A, centre y "
              f"{f['shape']['center_y_A']} A, z {f['shape']['center_z_A']} A) | {f['shape']['label']}; "
              f"{hf.get('profile')} profile, layer spacing {hf.get('layer_spacing_A')} A, field "
              f"{hf.get('field_length_A')} A along the beam in {hf.get('n_cells')} cells of "
              f"{hf.get('surface_dz_A')} A; base surface: {f.get('base_surface')}")
    else:
        print(f"    structure: {st.get('n_atoms')} atoms")
    eng = s["engine"]
    if eng.get("name") == "multislice":
        m = _engine_manifest(s, run_dir)
        rc = (m or {}).get("extra", {}).get("run_configuration", {})
        cell, prm = rc.get("cell", {}), rc.get("params", {})
        if cell:
            nsl = cell["length_z_A"] / prm["dz_A"]
            assert abs(nsl - round(nsl)) < 1e-6, nsl
            print(f"    multislice cell (engine manifest): {cell['n_atoms']} atoms; box x {cell['extent_x_A']:.4f}"
                  f" x y {cell['extent_y_A']:.4f} x z {cell['length_z_A']:.4f} A; grid nx {prm['nx']} x ny "
                  f"{prm['ny']} (dx {cell['extent_x_A'] / prm['nx']:.4f}, dy "
                  f"{cell['extent_y_A'] / prm['ny']:.4f} A); dz {prm['dz_A']} A; slices "
                  f"{int(round(nsl))} (= L_z/dz, DERIVED_HERE); crystal starts at z "
                  f"{cell['crystal_start_z_A']:.4f} A; surface x {cell['surface_x_A']} A")
            pot = rc.get("potential", {})
            print(f"    potential: {pot.get('kind')}; parameterisation {pot.get('parameterisation')} "
                  f"(abTEM {pot.get('abtem_version')}); MIP of the potential "
                  f"{pot.get('mean_inner_potential_V'):.4f} V; physical absorption "
                  f"{json.dumps(pot.get('physical_absorption', {}).get('ratio'))} "
                  f"({pot.get('physical_absorption', {}).get('label')})")
            fp = pot.get("frozen_phonons")
            if fp and fp.get("rms_displacement_per_axis_A") is not None:
                print(f"    frozen phonons: {fp.get('model')}; u = {fp.get('rms_displacement_per_axis_A'):.6f} A "
                      f"per axis | {fp.get('label')}; ensemble rule: {fp.get('ensemble_rule')}")
            else:
                print(f"    frozen phonons: none; engine record {fmt(fp)}")
            ov = rc.get("overlayer_setup") or (pot.get("overlayer") if isinstance(pot, dict) else None)
            if ov:
                print(f"    overlayer in the engine: {fmt(ov)[:400]}")
        bm = eng.get("beam") or eng.get("central_beam") or {}
        print(f"    engine beam{' (central member)' if 'central_beam' in eng else ''}: "
              f"{bm.get('kind')}, height {bm.get('height_A')} A, edge {bm.get('edge_A')} A")
    df = s["dark_field"]
    print(f"    dark-field aperture: {df['beam']} beam, semi-angle {df['semi_angle_rad'] * 1e3:.3f} mrad "
          f"| {df['label']}; fraction of exit-wave power passed {df['fraction_of_power_passed']:.4f}")
    d = s["detector"]
    roi = d["roi_shape"]
    print(f"    detector: pixel {d['pixel_A']} A (specimen-referred image plane) = pitch "
          f"{d['pixel_pitch_um']} um / M {d['magnification']:.0f}; ROI {roi} px = "
          f"{roi[0] * d['pixel_A'][0]:.1f} x {roi[1] * d['pixel_A'][1]:.1f} A; one detector row = "
          f"{d['surface_pixel_along_beam_A']:.3f} A of surface along the beam; dose "
          f"{d['dose_e_per_px']} e/px; gain {d['gain_counts_per_e']} counts/e; MTF {d['mtf']}; readout "
          f"noise {d['readout_noise']}; pixel integration: {d['pixel_integration']}")
    ref = s["reference"]
    fc = ref["fringe_contrast"]
    print(f"    reference: {ref['model']} ({ref['trajectory']}), carrier {ref['carrier_cycles_per_A']} "
          f"cycles/A, amplitude ratio {ref['amplitude_ratio']}; empty-hologram fringe contrast "
          f"{ref['empty_hologram_fringe_contrast']:.4f} (lossless {fc['lossless']}, with plasmon losses "
          f"{fc['with_surface_plasmon_losses']:.4f}, convergence coherence "
          f"{fmt(fc['convergence_coherence'])})")
    lo = s["surface_plasmon_losses"]
    print(f"    surface-plasmon losses: n = {lo['mean_excitations_object']} per reflection "
          f"({lo['object_label']}); zero-loss amplitude {lo['zero_loss_amplitude_object']:.4f}; loss "
          f"fraction {lo['loss_fraction_object']:.4f}; fringe factor {lo['fringe_factor']:.4f}")
    rec = s["reconstruction"]
    th = ga["value_rad"]
    pn = rec["predicted_phase_noise_per_px"]
    print(f"    reconstruction: resolution {rec['resolution_A']} A in the image plane "
          f"({rec['resolution_fringe_spacings']} fringe spacings) = {rec['resolution_A'] / math.sin(th):.1f} A "
          f"of surface along the beam (/ sin theta, DERIVED_HERE); mask radius "
          f"{rec['parameters']['mask']['radius_cycles_per_A']:.4f} cycles/A "
          f"({rec['parameters']['mask']['apodisation']}); unwrapping {rec['parameters']['unwrapping']}; "
          f"carrier located on the {rec['parameters']['carrier']['located_on']}")
    print(f"    predicted phase noise per pixel {pn['sigma_phi_rad']:.5f} rad (fringe contrast "
          f"{pn['fringe_contrast']:.4f}, {pn['counts_per_px']} counts/px)")
    print(f"    detector object amplitude (RMS over lit terrace tops) {d['empty_object_amplitude']:.4f}")
    if s.get("oxide_item12"):
        ox = s["oxide_item12"]
        print(f"    oxide (item 12 record): headline label {ox['headline_label']}; consumed layers "
              f"{ox['consumed_layers']['count']} ({ox['consumed_layers']['derived_by']})")
        for t in st.get("terrace_map", []):
            o = t.get("oxide")
            if o:
                print(f"      terrace {t['index']}: consumed depth {o['consumed_depth_A']:.4f} A; "
                      f"interface x {o['interface_x_A']:.4f} A; layer top x {o['top_x_A']:.4f} A; "
                      f"pre-oxidation plane x {o['pre_oxidation_plane_x_A']:.4f} A; top rise "
                      f"{o['top_rise_A']:.4f} A; removed atoms {o['removed_atoms']}; rounding "
                      f"margin {o['rounding_margin_layers']:.4f} layer")
        for stp in eng.get("steps", []):
            if "step_phase_with_overlayer_rad" in stp:
                print(f"      step {stp['index']} ({stp['type']}, {stp['height_A']:+.6f} A): step phase "
                      f"with overlayer {stp['step_phase_with_overlayer_rad']:+.6f} rad, bare "
                      f"{stp['step_phase_rad']:+.6f} rad")


def results_block(s: dict, camp: dict | None) -> None:
    print("  RESULTS:")
    hv = s["height_verdict"]
    print(f"    verdict: {hv['line']}")
    q = s["quantification"]
    for st in q.get("steps", []):
        h = st.get("height")
        built = st.get("built_height_A")
        if h:
            dev = (h["h_A"] - built) / h["sigma_h_A"]
            print(f"    step field terraces {st['from_field_terrace']}->{st['to_field_terrace']} "
                  f"({st['type']}): h = {h['h_A']:+.5f} +- {h['sigma_h_A']:.5f} A (1 sigma) vs built "
                  f"{built:+.5f} A: (h - built)/sigma = {dev:+.2f}; wrapped phase "
                  f"{st['delta_phi_wrapped_rad']:+.4f} +- {st['sigma_delta_phi_rad']:.4f} rad; branch "
                  f"{h['branch_index']} (lattice n = {st['branch']['assignment']['lattice_n']}); wrap "
                  f"period {h['wrap_period_A']:.4f} A")
        else:
            print(f"    step field terraces {st['from_field_terrace']}->{st['to_field_terrace']} "
                  f"({st['type']}, built {fmt(built)} A): no height: {st.get('reason')}")
    jb = q.get("joint_branch")
    if isinstance(jb, dict) and jb.get("decision"):
        print(f"    joint branch decision: {jb.get('decision')}; chance-acceptance bound "
              f"{fmt(jb.get('chance_probability_bound'))} vs alpha {fmt(jb.get('chance_level'))}")
    c = q["no_step_control"]
    if c.get("performed"):
        print(f"    no-step control: delta {c['delta_rad']:+.6f} rad vs tolerance {c['tolerance_rad']:.6f} "
              f"rad ({c['n_sigma']} x {c['se_correlated_rad']:.6f} rad); passed {c['passed']}; "
              f"n = {c['n_a']} / {c['n_b']} px")
    else:
        print(f"    no-step control: NOT performed ({c.get('reason')})")
    if "regions" in q:
        regs = q["regions"]
        meas = [r for r in regs.values() if r["measurable"]]
        print(f"    terrace regions measurable: {len(meas)} of {len(regs)}; per region (usable px, region "
              f"px, phase scatter rad): " + "; ".join(
                  f"T{k}: {r['n_usable_px']}, {r['n_region_px']}, "
                  f"{fmt(round(r['phase']['scatter_rad'], 5)) if 'phase' in r else '-'}"
                  for k, r in regs.items()))
        sh = q["shadow_exclusion"]
        tot = sh["usable_px"] + sh["excluded_px"]
        print(f"    usable detector pixels {sh['usable_px']} of {tot} ({100 * sh['usable_px'] / tot:.1f} %); "
              f"status counts {sh['detector_status_counts']}")
    if "measurable" in q:
        m = q["measurable"]
        print(f"    height map: measurable {m['measurable_px']} of {m['detector_px']} detector px "
              f"({100 * m['measurable_fraction_of_detector']:.1f} %); flat-source fraction "
              f"{m['measurable_fraction_of_flat_source']:.4f}; ring footprint {m['measurable_footprint_px']} "
              f"of {m['footprint_source_px']} lit footprint px; reason counts {m['reason_counts']}")
        for name, cut in q["profile_cuts"].items():
            print(f"    profile {name}: {cut['n_measurable']} of {cut['n_px']} px measurable "
                  f"({cut['n_measurable_on_footprint']} of {cut['n_on_footprint']} on the footprint); "
                  f"rms vs layer {fmt(cut['rms_vs_layer_A'])} A; median sigma_h "
                  f"{fmt(cut['median_sigma_h_A'])} A")
        r = q["resolution"]
        print(f"    resolution: image {r['reconstruction_resolution_image_A']} A; surface along the beam "
              f"{r['surface_resolution_along_beam_A']:.1f} A, across {r['surface_resolution_across_beam_A']} "
              f"A; ring cross-section {r['ring_cross_section_A']} A = "
              f"{r['ring_cross_section_in_resolution_elements']}")
    t = s["timing_s"]
    print(f"    pipeline timing (summary.json): total {t['total_s']:.2f} s; " + ", ".join(
        f"{k} {v:.2f}" for k, v in t.items() if k != "total_s"))
    if camp:
        print(f"    campaign: status {camp['status']}; wall {camp['wall_s']:.1f} s; child CPU "
              f"{camp['cpu_user_plus_sys_s']:.1f} s")
    eng = s["engine"]
    print(f"    engine label: {eng.get('label', '')[:130]}{'...' if len(eng.get('label', '')) > 130 else ''}")


def smoke_block(sid: str, name: str, config: str, variant, runs: Path, camp_by_name: dict,
                base_rows) -> list:
    cfg = load_pipeline_file(REPO / config, variant=variant)
    print("=" * 100)
    print(f"{sid}  {name}: config {config}, variant {variant}")
    print("=" * 100)
    print(f"  run_name {cfg.run_name}; purpose \"{cfg.purpose}\"; test_only {cfg.test_only}")
    print(f"  config sha256 (file) {cfg.sha256_file}; resolved (variant merged) {cfg.sha256_resolved}")
    print(f"  description (base): {' '.join(str(cfg.description).split())}")
    vdesc = ((cfg.raw.get("variants") or {}).get(variant) or {}).get("description") if variant else None
    if vdesc:
        print(f"  description (variant {variant}): {' '.join(str(vdesc).split())}")
    rows = rows_of_config(cfg)
    print(f"  PARAMETERS ({len(rows)} rows; loader reflection_holo.pipeline.config.load_pipeline_file):")
    print_rows(rows)
    if base_rows is not None:
        d = diff_rows(rows, base_rows)
        print(f"  DIFFERENCES FROM S1 (S1_base) ({len(d)}):")
        print("\n".join(d) if d else "    none")
    run_dir = runs / name
    s = json.loads((run_dir / "summary.json").read_text())
    man = json.loads((run_dir / "manifest.json").read_text())
    repo = man.get("repository", {})
    print(f"  run directory {run_dir}; manifest: commit {repo.get('commit')}, dirty {repo.get('dirty')}, "
          f"untracked {repo.get('untracked_files')}, package tree "
          f"{(repo.get('package_tree') or {}).get('sha256')}; threads "
          f"{(man.get('threads') or {}).get('check')}")
    assert s["beam_energy_keV"] == ENERGY_KEV
    assert s["config"]["sha256_resolved"] == cfg.sha256_resolved, "run was made with another config"
    computed_block(s, run_dir)
    results_block(s, camp_by_name.get(name))
    return rows


# ------------------------------------------------------------------------------------------------
# comparisons across runs and the summary table
# ------------------------------------------------------------------------------------------------
def _S(runs: Path, name: str) -> dict:
    return json.loads((runs / name / "summary.json").read_text())


def _steps(s: dict) -> list:
    return [st for st in s["quantification"].get("steps", []) if st.get("height")]


def comparisons_block(runs: Path, camp: dict) -> None:
    from reflection_holo.geometry.refraction import k_perp_in_layer_per_A
    print("=" * 100)
    print("C. COMPARISONS ACROSS RUNS (from the summaries above; ratios DERIVED_HERE)")
    print("=" * 100)
    names = {r["name"] for r in camp["runs"]}
    s1 = _S(runs, "S1_base")
    a1 = s1["detector"]["empty_object_amplitude"]
    sc1 = [r["phase"]["scatter_rad"] for r in s1["quantification"]["regions"].values() if "phase" in r]
    if "S4_plasmon_losses" in names:
        s4 = _S(runs, "S4_plasmon_losses")
        sc4 = [r["phase"]["scatter_rad"] for r in s4["quantification"]["regions"].values() if "phase" in r]
        n1, n4 = (x["reconstruction"]["predicted_phase_noise_per_px"]["sigma_phi_rad"] for x in (s1, s4))
        t1, t4 = (x["quantification"]["no_step_control"]["tolerance_rad"] for x in (s1, s4))
        print("  S4 (plasmon loss n = 1.246, B38) vs S1 (n = 0, B30):")
        print(f"    empty-hologram fringe contrast {s1['reference']['empty_hologram_fringe_contrast']:.4f} -> "
              f"{s4['reference']['empty_hologram_fringe_contrast']:.4f}; zero-loss object amplitude "
              f"exp(-n/2) = {s4['surface_plasmon_losses']['zero_loss_amplitude_object']:.4f}; loss fraction "
              f"1 - exp(-n) = {s4['surface_plasmon_losses']['loss_fraction_object']:.4f}")
        print(f"    predicted phase noise per px {n1:.5f} -> {n4:.5f} rad (ratio {n4 / n1:.3f}); measured "
              f"terrace phase scatter {[round(v, 5) for v in sc1]} -> {[round(v, 5) for v in sc4]} rad "
              f"(ratio of means {np.mean(sc4) / np.mean(sc1):.3f}); no-step tolerance {t1:.5f} -> {t4:.5f} rad")
        for a, b in zip(_steps(s1), _steps(s4)):
            print(f"    step {a['from_field_terrace']}->{a['to_field_terrace']}: S1 {a['height']['h_A']:+.5f} "
                  f"+- {a['height']['sigma_h_A']:.5f} A, S4 {b['height']['h_A']:+.5f} +- "
                  f"{b['height']['sigma_h_A']:.5f} A (built {a['built_height_A']:+.5f} A)")
    ox = [n for n in ("S5_oxide_2p0nm", "S5_oxide_2p0nm_no_absorption", "S5_oxide_1p5nm",
                      "S5_oxide_1p5nm_no_absorption") if n in names]
    if ox:
        print("  S5 continuum oxide (B41, geometric engine) vs S1 (no overlayer):")
    for n in ox:
        s = _S(runs, n)
        o = s["structure"]["options"]["overlayer"]
        th = s["glancing_angle"]["value_rad"]
        kp = k_perp_in_layer_per_A(th, ENERGY_KEV, o["V_real_V"], o["V_imag_V"])
        model = math.exp(-2.0 * kp.imag * o["thickness_A"])
        a = s["detector"]["empty_object_amplitude"]
        r1 = s1["quantification"]["regions"]
        r = s["quantification"]["regions"]
        off = [float(wrap_to_pi(r[k]["phase"]["median_rad"] - r1[k]["phase"]["median_rad"]))
               for k in r if "phase" in r[k] and "phase" in r1[k]]
        print(f"    {n}: t {o['thickness_A']} A, V {o['V_real_V']} + i {o['V_imag_V']} V; detector object "
              f"amplitude {a:.4f} vs S1 {a1:.4f}: ratio {a / a1:.4f}; zero-loss model exp(-2 Im k'_perp t) "
              f"= {model:.4f} (k'_perp = {kp.real:.5f} + {kp.imag:.3e} i rad/A, "
              f"geometry.refraction.k_perp_in_layer_per_A)")
        print(f"      terrace phase offset vs S1 (median, wrapped) per terrace {[round(v, 4) for v in off]} rad "
              f"(spread {max(off) - min(off):.4f} rad); no-step delta "
              f"{s['quantification']['no_step_control']['delta_rad']:+.5f} vs tolerance "
              f"{s['quantification']['no_step_control']['tolerance_rad']:.5f} rad")
        for a_, b_ in zip(_steps(s1), _steps(s)):
            print(f"      step {a_['from_field_terrace']}->{a_['to_field_terrace']}: h {b_['height']['h_A']:+.5f} +- "
                  f"{b_['height']['sigma_h_A']:.5f} A (S1 {a_['height']['h_A']:+.5f}; built "
                  f"{b_['built_height_A']:+.5f} A)")
    ms = [n for n in ("S2_multislice_tiny", "S3_multislice_tiny_thermal",
                      "S5_multislice_tiny_oxide_2p0nm", "S9_convergence") if n in names]
    if ms:
        print("  tiny multislice runs (UNVALIDATED engine; no height in any of them):")
        base = _S(runs, ms[0])["detector"]["empty_object_amplitude"]
        for n in ms:
            s = _S(runs, n)
            a = s["detector"]["empty_object_amplitude"]
            print(f"    {n}: detector object amplitude (RMS over lit) {a:.4f} (ratio to S2 {a / base:.4f}); "
                  f"dark-field fraction of exit-wave power passed {s['dark_field']['fraction_of_power_passed']:.4f}; "
                  f"realisations/members {s['exit_wave']['n_realisations']}; engine time "
                  f"{s['timing_s'].get('engine_s', float('nan')):.2f} s")
    tor = [n for n in ("S6_torus_trench", "S6_torus_ridge") if n in names]
    for n in tor:
        m = _S(runs, n)["quantification"]["measurable"]
        print(f"  {n}: measurable {100 * m['measurable_fraction_of_detector']:.1f} % of the detector; ring "
              f"footprint {m['measurable_footprint_px']} of {m['footprint_source_px']} lit footprint px")
    print("=" * 100)
    print("T. SUMMARY TABLE (commit and package tree from each run's manifest.json; times from the campaign log)")
    print("=" * 100)
    print("  id  run                               commit   dirty  package-tree  wall s  CPU s  verdict")
    for r in camp["runs"]:
        man = json.loads((runs / r["name"] / "manifest.json").read_text())
        rp = man.get("repository", {})
        v = r["verdict"]
        print(f"  {r['smoke_test']:<3} {r['name']:<33} {str(rp.get('commit'))[:7]}  {str(rp.get('dirty')):<5}  "
              f"{(rp.get('package_tree') or {}).get('sha256', '')[:12]}  {r['wall_s']:6.1f} "
              f"{r['cpu_user_plus_sys_s']:6.1f}  {v[:110]}{'...' if len(v) > 110 else ''}")


# ------------------------------------------------------------------------------------------------
# S7 and S8 (not rerun)
# ------------------------------------------------------------------------------------------------
def _flat(d, p=""):
    out = []
    if isinstance(d, dict):
        for k, v in d.items():
            out += _flat(v, f"{p}.{k}" if p else k)
    else:
        out.append((p, d))
    return out


def _manifest_of(summary: dict) -> dict | None:
    mp = (summary.get("run") or {}).get("manifest")
    return json.loads(Path(mp).read_text()) if mp and Path(mp).exists() else None


def s7_block(t1: Path, rerun: Path) -> None:
    print("=" * 100)
    print("S7  atomistic half torus, trench / ridge / flat reference, multislice (report T1): NOT RERUN")
    print("=" * 100)
    print("  Source: saved case_<kind>.json and summary_<kind>.json of T1's runs (these are the runs "
          "behind the figures in SP/torus/figures, tools/plots/torus_atomistic.py). Script: "
          "scripts/torus/run_torus_multislice.py.")
    base_case = None
    for kind in ("trench", "ridge", "flat"):
        d = t1 / f"ms_{kind}"
        case = json.loads((d / f"case_{kind}.json").read_text())
        s = json.loads((d / f"summary_{kind}.json").read_text())
        m = _manifest_of(s)
        print(f"  --- {kind}: {d}")
        if base_case is None:
            print("  CASE parameters (as saved; labels as stated in the file):")
            for k, v in _flat(case["CASE"]):
                print(f"    {k} = {fmt(v)}")
            base_case = case["CASE"]
        else:
            diffs = [(k, v) for k, v in _flat(case["CASE"]) if dict(_flat(base_case)).get(k) != v]
            print(f"  CASE parameters: identical to trench ({len(diffs)} differences)"
                  + ("; ".join(f"{k} = {fmt(v)}" for k, v in diffs)))
        print(f"    status: {case['status'][:160]}...")
        print(f"    atoms {s['n_atoms']}; grid {s['grid']['nx']} x {s['grid']['ny']} (dx {s['grid']['dx_A']:.4f}, "
              f"dy {s['grid']['dy_A']:.4f} A); slices {s['n_slices']}; box {s['cell']['extent_x_A']:.2f} x "
              f"{s['cell']['extent_y_A']:.2f} x {s['cell']['length_z_A']:.2f} A; MIP "
              f"{s['mean_inner_potential_V']:.4f} V; theta_ext {s['theta_ext_rad'] * 1e3:.4f} mrad, "
              f"theta_int {s['theta_int_rad'] * 1e3:.4f} mrad; band angle ceiling "
              f"{s['band']['angle_ceiling_x_mrad']:.2f} mrad")
        if "feature" in s and kind != "flat":
            f = s["feature"]
            print(f"    feature: {f['kind']}, R {f['major_radius_A']} A, r {f['minor_radius_A']} A, removed "
                  f"{f['n_removed']}, added {f['n_added']}, layers changed {f['max_layers_changed']} | "
                  f"{f['label']} ({f['source']})")
        checks = {**s.get("engine_geometry_checks", {}), **(s.get("feature_geometry_checks") or {})}
        failed = [k for k, v in checks.items() if isinstance(v, dict) and v.get("passed") is False]
        print(f"    geometry checks: {len(checks)} recorded, failed: {failed or 'none'}")
        r = s["run"]
        print(f"    run: simulate {r['simulate_s']:.1f} s, total {r['total_s']:.1f} s, peak RSS "
              f"{r['peak_rss_MB']:.0f} MB; structure build {s['structure_build_s']:.1f} s")
        if m:
            rp = m["repository"]
            print(f"    manifest {r['manifest']}: commit {rp['commit']}, dirty {rp['dirty']}, precision "
                  f"{fmt(m.get('precision'))}, threads {(m.get('threads') or {}).get('check')}")
    print("  --- later clean rerun of the same three cases (SP/torus_ms, not used for the figures):")
    for kind in ("trench", "ridge", "flat"):
        case = json.loads((rerun / f"case_{kind}.json").read_text())
        s = json.loads((rerun / f"summary_{kind}.json").read_text())
        m = _manifest_of(s)
        t1case = json.loads((t1 / f"ms_{kind}" / f"case_{kind}.json").read_text())
        a, b = dict(_flat(t1case["CASE"])), dict(_flat(case["CASE"]))
        dif = [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
        r = s["run"]
        print(f"    {kind}: commit {m['repository']['commit'] if m else '?'} dirty "
              f"{m['repository']['dirty'] if m else '?'}; simulate {r['simulate_s']:.1f} s; atoms "
              f"{s['n_atoms']}; grid {s['grid']['nx']} x {s['grid']['ny']}; slices {s['n_slices']}; CASE keys "
              f"differing from T1: {len(dif)}: " + "; ".join(f"{k}: {fmt(a.get(k))} -> {fmt(b.get(k))}"
                                                             for k in dif))
    print("  RESULTS: none to quote. The exit waves are UNVALIDATED (finite-cell build-up not "
          "converged, no physical absorption B30; T1 section 8): no phase or height may be read from "
          "them; the figures show the complex exit waves only.")


def s8_block(buried: Path, t5_out: Path) -> None:
    print("=" * 100)
    print("S8  buried torus void (report T3 runs, T5 analysis): NOT RERUN")
    print("=" * 100)
    dirs = sorted(p for p in buried.glob("ms_*") if p.is_dir())
    base = None
    for d in dirs:
        case_f = sorted(d.glob("case_*.json"))[0]
        sum_f = sorted(d.glob("summary_*.json"))[0]
        case, s = json.loads(case_f.read_text()), json.loads(sum_f.read_text())
        m = _manifest_of(s)
        print(f"  --- {d.name}: {case_f.name}")
        if base is None:
            print("  CASE parameters (as saved; labels as stated in the file):")
            for k, v in _flat(case["CASE"]):
                print(f"    {k} = {fmt(v)}")
            base = dict(_flat(case["CASE"]))
        else:
            diffs = [(k, v) for k, v in _flat(case["CASE"]) if base.get(k) != v]
            print(f"    CASE identical to the first except: "
                  + ("; ".join(f"{k} = {fmt(v)}" for k, v in diffs) or "none"))
        print(f"    name {case.get('name')}; cap {fmt(case.get('cap_A'))} A; absorption "
              f"{case.get('absorption')}: {s.get('physical_absorption', {}).get('label', '')[:110]}")
        print(f"    atoms {s['n_atoms']}; grid {s['grid']['nx']} x {s['grid']['ny']} (dx {s['grid']['dx_A']:.4f}, "
              f"dy {s['grid']['dy_A']:.4f} A); slices {s['n_slices']}; box {s['cell']['extent_x_A']:.2f} x "
              f"{s['cell']['extent_y_A']:.2f} x {s['cell']['length_z_A']:.2f} A; theta_ext "
              f"{s['theta_ext_rad'] * 1e3:.4f} mrad")
        r = s["run"]
        lu = s.get("limits_used") or {}
        print(f"    limits used: CPU {fmt(lu.get('cpu_seconds'))} s ({lu.get('cpu_seconds_source')}), memory "
              f"{fmt(lu.get('memory_bytes'))} B")
        print(f"    run: simulate {r['simulate_s']:.1f} s, total {r['total_s']:.1f} s, peak RSS "
              f"{r['peak_rss_MB']:.0f} MB" + (f"; manifest commit {m['repository']['commit']}, dirty "
                                              f"{m['repository']['dirty']}" if m else ""))
    print(f"  RESULTS (verbatim lines of {t5_out}, 'OUT:n' = line n):")
    lines = t5_out.read_text().splitlines()
    print(f"    OUT:1: {lines[0]}")
    for i, ln in enumerate(lines, 1):
        if ln.startswith("=== reading"):
            j = i
            while j < len(lines) and lines[j].startswith("  cap "):
                print(f"    OUT:{j + 1}: {lines[j].strip()}")
                j += 1
        if ln.startswith("compact figure") or ln.strip().startswith("panel title"):
            print(f"    OUT:{i}: {ln.strip()}")


# ------------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", required=True, type=Path, help="campaign root (run_smoke_campaign.py --out)")
    ap.add_argument("--t1-runs", required=True, type=Path, help="T1 run root (ms_trench, ms_ridge, ms_flat)")
    ap.add_argument("--t1-rerun", required=True, type=Path, help="later rerun of the T1 cases (torus_ms)")
    ap.add_argument("--buried", required=True, type=Path, help="T3 run root (ms_*)")
    ap.add_argument("--t5-output", required=True, type=Path, help="T5 analysis output text")
    args = ap.parse_args(argv)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True,
                          check=True).stdout.strip()
    camp = json.loads((args.runs / "campaign_log.json").read_text())
    print("R1 smoke-test parameters, derived quantities and results "
          f"(tools/report/smoke_parameters.py; printed {_dt.datetime.now(_dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ})")
    print(f"repository HEAD {head}; campaign commit {camp['commit']} (started {camp['started_utc']}, "
          f"finished {camp.get('finished_utc')}); git status at campaign start "
          f"{camp['git_status_porcelain']}; tracked files identical to HEAD {camp['tracked_diff_vs_head_empty']}")
    print("Labels: PROJECT_INPUT (supplied by Ali), ASSUMPTION Bxx (demo stand-in registered in "
          "reflection_holo/io/assumption_registry.yaml; 'stands in for' names the docs/06 item), "
          "DERIVED_HERE, REPRODUCED, TEST_ONLY; 'plain setting' = numerical setting without a label. "
          "DEMO: not comparable to experiment.")
    derived_block(REPO / "docs" / "agent_reports" / "C_calculator_output.txt")
    from reflection_holo.optics import detector as _det
    noise = [ln.strip() for ln in (_det.__doc__ or "").splitlines() if ln.startswith("Noise:")]
    print(f"  detector noise model (reflection_holo/optics/detector.py docstring, verbatim): "
          f"{noise[0] if noise else '(not found)'} ...")
    camp_by_name = {r["name"]: r for r in camp["runs"]}
    base_rows = None
    status_printed = False
    for sid, name, config, variant in CAMPAIGN.RUNS:
        if name not in camp_by_name:
            print(f"{sid} {name}: NOT RUN in the campaign")
            continue
        rows = smoke_block(sid, name, config, variant, args.runs, camp_by_name,
                           None if base_rows is None else base_rows)
        if base_rows is None:
            base_rows = rows
        s = json.loads((args.runs / name / "summary.json").read_text())
        if s["engine"].get("name") == "multislice" and not status_printed:
            print(f"  ENGINE VALIDATION_STATUS (verbatim, same for every multislice run): "
                  f"{s['engine']['validation_status']}")
            status_printed = True
        if name == "S9_convergence":
            cv = s["engine"].get("convergence", {})
            qd = cv.get("quadrature", {})
            print(f"  convergence ensemble: {qd.get('n_members')} members, semi-angle "
                  f"{qd.get('semi_angle_rad', 0) * 1e3} mrad ({qd.get('semi_angle_label')}), profile "
                  f"{qd.get('source_profile')}, {qd.get('n_radial')} x {qd.get('n_azimuthal')} product "
                  f"rule; design phase extent {fmt(qd.get('design_phase_extent_rad'))} rad; error bound "
                  f"{fmt(qd.get('error_bound'))} <= tolerance {fmt(qd.get('tolerance'))}; R1 separation "
                  f"{fmt(cv.get('design_extent', {}).get('geometry', {}).get('separation_A'))} A")
            fc = s["reference"]["fringe_contrast"]["convergence_coherence"]
            print(f"  convergence coherence of the empty ensemble over lit pixels: median "
                  f"{fc['median_over_lit_pixels']:.5f}, min {fc['min_over_lit_pixels']:.5f}, max "
                  f"{fc['max_over_lit_pixels']:.5f}")
    comparisons_block(args.runs, camp)
    s7_block(args.t1_runs, args.t1_rerun)
    s8_block(args.buried, args.t5_output)
    print("=" * 100)
    print("END")
    return 0


if __name__ == "__main__":
    sys.exit(main())
