"""Feature path of the pipeline (agent T2): half-torus configurations, the height map, the gate.

configs/demo_smoke_torus_{trench,ridge}.yaml are read, never written; the end-to-end tests shrink the
ring and the field (numbers only; labels unchanged) so that they run in seconds. Outputs go to
pytest's tmp_path only.

Acceptance criteria, fixed before the first run:
* a smooth, gentle bump (continuous TEST_ONLY surface, 2 A high, 40 A wide across the beam, 2500 A
  along it: slopes inside the 3 mrad aperture, no shadows) run through the pipeline's own optics,
  hologram, reconstruction and height-map stages: at least half of the pixels of the bump core
  (|h| > 0.5 A) measurable; every measurable core pixel within 3 sigma_h (the propagated
  uncertainty) of the built height at its traced source; rms over the core <= 0.01 A; the sign of
  the recovered heights follows the sign of the bump; the no-step control passes;
* a small torus (R = 150 A, r = 8 A) end to end: outputs complete (arrays with axes, units and
  planes; manifest), the control passes, no footprint pixel returns a height (a/4 steps are 1.78
  wraps and the flanks are unresolved), the front and back arcs are reported UNRESOLVED, and at most
  1 % of the measurable (flat) pixels lie beyond 3 sigma_h of the built height;
* the gate refuses a feature without a registered item-13 stand-in, a missing feature processing
  record, an inconsistent pattern_geometry, the multislice engine, and settings of the other path.
"""
import copy
import json
import math

import numpy as np
import pytest

from reflection_holo.forward.geometric import STATUS
from reflection_holo.forward.geometric.height_field import (HeightField, HeightFieldParams,
                                                            height_field_exit_wave,
                                                            require_b4_scope_height_field)
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.io.config import MissingProjectInputError
from reflection_holo.pipeline import PipelineConfigError, load_pipeline_dict, read_pipeline_file, run
from reflection_holo.pipeline.__main__ import main as cli_main
from reflection_holo.pipeline.feature import detector_trace_height_field
from reflection_holo.pipeline.run import _hologram_stage, _optics_stage, _reconstruction_stage
from reflection_holo.provenance.manifest import REQUIRED_KEYS
from reflection_holo.quantification.height_map import height_map

from conftest_pipeline import REPO, TOL_SIGMA

TRENCH = REPO / "configs" / "demo_smoke_torus_trench.yaml"
RIDGE = REPO / "configs" / "demo_smoke_torus_ridge.yaml"


def _small(path, *, R=150.0, r=8.0):
    """The demo configuration with a small ring and field (numbers only; labels unchanged)."""
    d = read_pipeline_file(path)
    f = d["sections"]["structure"]["feature"]["value"]
    f.update(center_y_A=255.75, center_z_A=2000.0, major_radius_A=R, minor_radius_A=r)
    g = d["sections"]["engine"]["geometric"]
    g.update(n_y=1024, field_length_A=4000.0, surface_dz_A=1.0)
    d["sections"]["detector"]["roi_shape"] = [128, 960]
    d["sections"]["outputs"]["quicklooks"] = False
    return d


# --------------------------------------------------------------------------------------------------
# gentle bump: the height map recovers it within its uncertainty
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("sign", [+1, -1])
def test_gentle_bump_height_map_within_uncertainty(sign):
    d = read_pipeline_file(TRENCH)
    d["sections"]["detector"]["roi_shape"] = [384, 960]
    cfg = load_pipeline_dict(d, variant=None)
    theta = cfg.glancing_angle["value_rad"]
    A, sy, sz, yc, zc, L = 2.0 * sign, 40.0, 2500.0, 255.75, 6000.0, 12000.0

    def bump(y, z):
        return A * np.exp(-(y - yc) ** 2 / (2 * sy ** 2) - (z - zc) ** 2 / (2 * sz ** 2))

    hf = HeightField(height_fn=bump, profile="piecewise_linear", layer_spacing_A=None,
                     z_start_A=0.0, field_length_A=L, surface_dz_A=2.0, upstream_level_A=0.0,
                     description="gentle Gaussian bump",
                     label="TEST_ONLY: stands in for PROJECT_INPUT item 13", source="test")
    b4 = require_b4_scope_height_field(hf, azimuth_uvw=(1, 0, 0), termination="bulk",
                                       overlayer=None, illumination="plane_wave", beam="specular",
                                       layer_index_parity="any")
    params = HeightFieldParams(exit_plane_pixel_A=(0.25, 0.5), n_y=1024, x_margin_A=20.0,
                               reflectivity_amplitude=1.0)
    er = height_field_exit_wave(hf, energy_keV=200.0, theta_in_ext_rad=theta,
                                theta_label="TEST_ONLY: stands in for item 7", params=params,
                                b4=b4)
    x0 = L * math.tan(theta)
    op = _optics_stage(cfg, [er.exit_wave], x0=x0, x0_def="flat surface, z_s = 0 at z = 0",
                       fov_u=(0.0, L * math.sin(theta)))
    pl = op["placement"]
    tr = detector_trace_height_field(hf, pl.u_A, pl.y_A, x0_A=x0, theta_rad=theta)
    lit = tr["status"] == STATUS["lit"]
    Y = np.broadcast_to(pl.y_A[None, :], lit.shape)
    flat = lit & (np.abs(Y - yc) > 4 * sy)
    ho = _hologram_stage(cfg, op["obj_waves"], op["spec"], amplitude_px=flat,
                         amplitude_px_description="flat-surface point")
    rc = _reconstruction_stage(cfg, ho["H_obj_n"], ho["H_emp_n"], ho["q_ref"])
    recon = rc["recon"]
    qp = cfg.rec("quantification", "processing").value
    fp = cfg.rec("quantification", "feature_processing").value
    res, p = float(recon.resolution_A), op["spec"].pixel_A
    m = (math.ceil(qp["edge_margin_resolutions"] * res / p[0]),
         math.ceil(qp["edge_margin_resolutions"] * res / p[1]))
    W = np.asarray(recon.mask)
    q_x = float(er.exit_wave.metadata["q_rad_per_A"][0])
    hm = height_map(phase_wrapped=recon.wrapped_phase, amplitude_rel=recon.amplitude,
                    valid=recon.valid_mask, lit=lit,
                    source_phase_rad=np.where(lit, -q_x * tr["source_h_A"], np.nan),
                    hidden=tr["hidden_neighbour"], flat_source=flat,
                    min_relative_amplitude=qp["min_relative_amplitude"],
                    max_phase_step_rad=fp["max_phase_step_rad"], margin_px=m,
                    min_region_px=qp["min_region_px"], a_eff_px=float(W.size / np.sum(W ** 2)),
                    wavelength_A=wavelength_A(200.0), theta_rad=theta,
                    sigma_theta_rad=cfg.rec("illumination", "angle_calibration_sigma")
                    .canonical_value,
                    sigma_wavelength_rel=cfg.rec("illumination", "wavelength_sigma_rel")
                    .canonical_value)
    from reflection_holo.pipeline import quantify as Q
    ctrl = Q.no_step(recon.wrapped_phase, hm["flat_reference"], float(W.size / np.sum(W ** 2)),
                     qp["n_sigma"], recon.valid_mask)
    assert ctrl["performed"] and ctrl["passed"], ctrl
    h_true = np.where(lit, bump(Y, np.where(lit, tr["source_z_A"], 0.0)), np.nan)
    core = lit & (np.abs(h_true) > 0.5)
    meas = hm["measurable"] & core
    assert core.sum() > 1000
    assert meas.sum() >= 0.5 * core.sum(), (int(meas.sum()), int(core.sum()))
    err = hm["height_A"][meas] - h_true[meas]
    assert np.all(np.abs(err) <= TOL_SIGMA * hm["sigma_h_A"][meas]), float(np.max(np.abs(err)))
    assert float(np.sqrt(np.mean(err ** 2))) <= 0.01
    assert np.sign(np.mean(hm["height_A"][meas])) == sign
    peak = hm["height_A"][meas][np.argmax(np.abs(h_true[meas]))]
    assert abs(peak - A) <= TOL_SIGMA * hm["sigma_h_A"][meas][np.argmax(np.abs(h_true[meas]))]


# --------------------------------------------------------------------------------------------------
# small torus end to end
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("path", [TRENCH, RIDGE], ids=["trench", "ridge"])
def test_small_torus_end_to_end(path, tmp_path):
    cfg = load_pipeline_dict(_small(path), variant=None)
    out = tmp_path / "run"
    s = run(cfg, out)
    kind = "trench" if path == TRENCH else "ridge"
    assert s["feature"]["shape"]["sub_kind"] == kind
    assert s["purpose"] == "demo; not comparable to experiment"
    assert s["engine"]["label"] == "geometric model, no dynamical amplitude, B4 scope applies"
    assert s["beam_energy_keV"] == 200.0
    q = s["quantification"]
    assert q["no_step_control"]["performed"] and q["no_step_control"]["passed"]
    assert not s["height_verdict"]["withheld"] and s["height_verdict"]["heights_returned"] > 0
    assert q["measurable"]["measurable_footprint_px"] == 0
    assert q["resolution"]["ring_front_back_resolved"] is False
    assert "UNRESOLVED" in q["resolution"]["summary"]
    a = np.load(out / "arrays.npz")
    j = json.loads((out / "summary.json").read_text())
    idx = {k: v for k, v in j["arrays"].items() if not k.startswith("_")}
    assert set(a.files) == set(idx)
    for k, meta in idx.items():
        assert meta["axes"] and meta["units"] and meta["plane"] and list(a[k].shape) == meta["shape"]
    meas = a["measurable"]
    dev = np.abs(a["height_A"][meas] - a["built_height_layer_A"][meas])
    assert np.mean(dev > TOL_SIGMA * a["sigma_height_A"][meas]) <= 0.01
    assert not np.any(meas & a["footprint_source"])
    assert np.all(a["trace_status"][meas] == STATUS["lit"])
    man = json.loads((out / "manifest.json").read_text())
    assert set(REQUIRED_KEYS) <= set(man)
    assert man["beam_energy_keV"] == 200.0 and man["extra"]["feature"]["sub_kind"] == kind
    if kind == "ridge":
        assert q["shadow_exclusion"]["detector_status_counts"]["illumination_shadow"] > 0


# --------------------------------------------------------------------------------------------------
# CLI: dry-run (memory and time) and list-inputs of the shipped configurations
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("path, aid", [(TRENCH, "B33"), (RIDGE, "B34")], ids=["trench", "ridge"])
def test_cli_dry_run_and_list_inputs(path, aid, capsys):
    assert cli_main(["dry-run", "--config", str(path)]) == 0
    txt = capsys.readouterr().out
    assert "engine geometric" in txt and "exit plane [" in txt
    rep = json.loads(txt[txt.index("{"):])                  # fails if the report were truncated
    assert rep["geometric"]["estimated_seconds"] < 180
    assert rep["total_memory_bytes"] < 4 * 2 ** 30
    assert cli_main(["list-inputs", "--config", str(path)]) == 0
    txt = capsys.readouterr().out
    assert "run-level gate: PASS" in txt and f"ASSUMPTION {aid} stand-in" in txt
    assert "sections.structure.staircase" in txt and "the feature path has no staircase" in txt


# --------------------------------------------------------------------------------------------------
# gate
# --------------------------------------------------------------------------------------------------
def test_feature_refused_without_a_registered_stand_in():
    d = read_pipeline_file(TRENCH)
    load_pipeline_dict(copy.deepcopy(d), variant=None)                    # the demo passes
    for aid, match in (("B99", "registry"), ("B19", "not mapped to PROJECT_INPUT item 13"),
                       (None, "not mapped")):
        e = copy.deepcopy(d)
        e["sections"]["structure"]["feature"]["assumption_id"] = aid
        with pytest.raises(PipelineConfigError, match=match):
            load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    e["sections"]["structure"]["feature"].update(value=None, label="PROJECT_INPUT")
    for k in ("stands_in_for_item", "assumption_id"):
        del e["sections"]["structure"]["feature"][k]
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(e, variant=None)
    assert 13 in exc.value.items
    e = copy.deepcopy(d)
    e["sections"]["structure"]["feature"]["label"] = "TEST_ONLY"
    with pytest.raises(PipelineConfigError, match="TEST_ONLY"):
        load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    del e["sections"]["structure"]["feature"]                             # nothing: item 11
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(e, variant=None)
    assert 11 in exc.value.items
    for aid, other in (("B27", "B27"), ("B34", "B34")):                   # wrong stand-in rows
        e = copy.deepcopy(d)
        e["sections"]["structure"]["feature"]["assumption_id"] = aid
        e["cfg_b"]["parameters"]["pattern_geometry"]["assumption_id"] = other
        with pytest.raises(PipelineConfigError, match="stand-in"):
            load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)                                                  # the buried-void row (T3)
    e["sections"]["structure"]["feature"]["assumption_id"] = "B42"
    e["cfg_b"]["parameters"]["pattern_geometry"]["assumption_id"] = "B42"
    with pytest.raises(PipelineConfigError, match="B42 states a buried_void"):
        load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    e["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="B33"):
        load_pipeline_dict(e, variant=None)


@pytest.mark.parametrize("name", ["demo_hpc_si001.yaml", "demo_convergence_si001.yaml"])
def test_no_feature_route_refuses_a_feature_stand_in(name):
    """Audit A9a m-3 (agent T4): a staircase configuration (no sections.structure.feature) whose
    cfg_b.pattern_geometry {features: none} carried a FEATURE stand-in (B33 trench, B34 ridge, B42
    buried void) was accepted and recorded that row as its item-13 stand-in. Refused now; B27 (no
    feature) is still accepted."""
    d = read_pipeline_file(REPO / "configs" / name)
    assert d["cfg_b"]["parameters"]["pattern_geometry"]["assumption_id"] == "B27"
    load_pipeline_dict(copy.deepcopy(d), variant=None)                    # the demo passes
    for aid in ("B33", "B34", "B42"):
        e = copy.deepcopy(d)
        e["cfg_b"]["parameters"]["pattern_geometry"]["assumption_id"] = aid
        with pytest.raises(PipelineConfigError, match=f"under stand-in {aid}"):
            load_pipeline_dict(e, variant=None)


def test_no_demo_configuration_labels_no_feature_with_a_feature_stand_in():
    """Every demo configuration without a feature declares B27 on pattern_geometry, so none relies
    on the route closed by the A9a m-3 fix (read from the files; nothing is run)."""
    seen = 0
    for path in sorted((REPO / "configs").glob("demo_*.yaml")):
        d = read_pipeline_file(path)
        p13 = d["cfg_b"]["parameters"]["pattern_geometry"]
        if "feature" not in d["sections"]["structure"]:
            seen += 1
            assert p13["value"] == {"features": "none"}, path.name
            assert p13.get("assumption_id") == "B27", path.name
    assert seen >= 3


def test_feature_path_consistency_rules():
    d = read_pipeline_file(TRENCH)
    cases = []
    e = copy.deepcopy(d)
    del e["sections"]["quantification"]["feature_processing"]
    cases.append((e, "feature_processing"))
    e = copy.deepcopy(d)
    e["cfg_b"]["parameters"]["pattern_geometry"]["value"] = {"features": "none"}
    cases.append((e, "pattern_geometry"))
    e = copy.deepcopy(d)
    e["cfg_b"]["parameters"]["pattern_geometry"]["assumption_id"] = "B27"
    cases.append((e, "same label and assumption_id"))
    e = copy.deepcopy(d)
    e["sections"]["structure"]["edge_periods"] = 1
    cases.append((e, "not used on the feature path"))
    e = copy.deepcopy(d)
    e["sections"]["optics"]["projection_reference"] = "lowest_terrace_top"
    cases.append((e, "flat_surface"))
    e = copy.deepcopy(d)
    del e["sections"]["engine"]["geometric"]["field_length_A"]
    cases.append((e, "exactly the keys"))
    e = copy.deepcopy(d)
    e["sections"]["engine"]["geometric"]["surface_dz_A"] = 7.0
    cases.append((e, "divide"))
    e = copy.deepcopy(d)
    e["sections"]["engine"]["name"] = "multislice"
    e["sections"]["engine"]["multislice"] = {"x": 1}
    cases.append((e, "geometric engine only"))
    e = copy.deepcopy(d)
    e["sections"]["quantification"]["feature_processing"]["value"]["max_phase_step_rad"] = 3.5
    cases.append((e, "below pi"))
    e = copy.deepcopy(d)
    e["sections"]["structure"]["feature"]["value"]["minor_radius_A"] = 2000.0
    cases.append((e, "minor_radius_A < major_radius_A"))
    for e, match in cases:
        with pytest.raises(PipelineConfigError, match=match):
            load_pipeline_dict(e, variant=None)
    smoke = read_pipeline_file(REPO / "configs" / "demo_smoke_si001.yaml")
    smoke["sections"]["quantification"]["feature_processing"] = copy.deepcopy(
        d["sections"]["quantification"]["feature_processing"])
    with pytest.raises(PipelineConfigError, match="feature path only"):
        load_pipeline_dict(smoke, variant=None)
