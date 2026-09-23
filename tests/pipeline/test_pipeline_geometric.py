"""End-to-end pipeline with the geometric engine on configs/demo_smoke_si001.yaml (read, never
written). Outputs go to pytest's tmp_path only.

Acceptance criteria, fixed before the first run (report P1):
* every measured step: |h - h_built| <= 3 sigma_h (sigma_h the propagated uncertainty returned by
  quantification.height.height_from_phase, with the MEASURED phase scatter) and
  |Delta_phi - wrap(-q.n h_built)| <= 3 sigma_Delta_phi; the a/2 step and both a/4 steps (inside
  the B4 scope at [100]) must be measured;
* the no-step control passes (|delta| <= 3 correlated standard errors);
* shadow exclusion: no region pixel is anything but a lit terrace top; the recorded strips have the
  lengths h/tan(theta) at the operating angle; shadowed and riser pixels are excluded;
* a missing PROJECT_INPUT without a registered stand-in fails.
"""
import copy
import json
import math

import numpy as np
import pytest

from reflection_holo.geometry.specular import wrap_to_pi
from reflection_holo.io.config import MissingProjectInputError
from reflection_holo.pipeline import (OutputDirectoryError, PipelineConfigError, load_pipeline_dict,
                                      read_pipeline_file, run)
from reflection_holo.pipeline.__main__ import main as cli_main
from reflection_holo.pipeline.quantify import STATUS
from reflection_holo.provenance.manifest import REQUIRED_KEYS

from conftest_pipeline import SMOKE, TOL_SIGMA


@pytest.fixture(scope="module")
def smoke(tmp_path_factory):
    out = tmp_path_factory.mktemp("smoke") / "run"
    summary = run(SMOKE, out)
    return out, summary


def _steps(summary):
    return summary["quantification"]["steps"]


def test_signed_heights_within_propagated_uncertainty(smoke):
    _, s = smoke
    steps = _steps(s)
    kinds = sorted((st["type"], round(st["built_height_A"], 6)) for st in steps)
    assert kinds == [("screw", -1.357725), ("screw", -1.357725), ("translation", 2.71545)]
    lam, th = s["wavelength_A"], s["glancing_angle"]["value_rad"]
    sens = 4 * math.pi * math.sin(th) / lam
    for st in steps:
        assert st["measured"], st
        h = st["height"]
        assert h is not None, st.get("reason")
        assert abs(h["h_A"] - st["built_height_A"]) <= TOL_SIGMA * h["sigma_h_A"], (st, h)
        want = float(wrap_to_pi(-sens * st["built_height_A"]))
        got = st["delta_phi_wrapped_rad"]
        assert abs(float(wrap_to_pi(got - want))) <= TOL_SIGMA * st["sigma_delta_phi_rad"], st
        assert st["branch"]["decision"] == "resolved"
        assert h["wrap_period_A"] == pytest.approx(lam / (2 * math.sin(th)), rel=1e-12)
        if st["type"] == "screw":
            assert st["model_assumption_B4"].startswith("B4 applies")


def test_no_step_control_passes(smoke):
    _, s = smoke
    c = s["quantification"]["no_step_control"]
    assert c["performed"] and c["passed"], c
    assert abs(c["delta_rad"]) <= c["tolerance_rad"]


def test_shadow_exclusion(smoke):
    out, s = smoke
    a = np.load(out / "arrays.npz")
    status, regions, usable = a["trace_status"], a["region_map"], a["usable_mask"]
    assert np.all(status[regions >= 0] == STATUS["lit"])
    assert not np.any(usable & (status != STATUS["lit"]))
    assert np.any(status == STATUS["illumination_shadow"]) and np.any(status == STATUS["riser"])
    th = s["glancing_angle"]["value_rad"]
    sh = s["quantification"]["shadow_exclusion"]
    for rec in sh["surface_strips"]["per_step"]:
        L = rec["nominal_shadow_length_A"] or rec["nominal_blocked_view_length_A"]
        assert L == pytest.approx(abs(rec["height_A"]) / math.tan(th), rel=1e-12)
    # the a/2 step has its upper terrace downstream: blocked-view strip, not an illumination shadow
    kinds = {round(r["height_A"], 6): r["strip"] for r in sh["surface_strips"]["per_step"]}
    assert kinds[2.71545] == "blocked_view" and kinds[1.357725] == "illumination_shadow"


def test_outputs_manifest_and_array_index(smoke):
    out, s = smoke
    for name in ("summary.json", "manifest.json", "arrays.npz"):
        assert (out / name).is_file()
    m = json.loads((out / "manifest.json").read_text())
    assert all(k in m for k in REQUIRED_KEYS)
    assert m["beam_energy_keV"] == 200.0 and m["seeds"]["detector_noise"] == 20260922
    assert m["threads"]["requested"] == 4 and m["repository"]["commit"]
    assert m["extra"]["pipeline_config_sha256_file"] and m["config"]["config_id"] == "CFG-B"
    j = json.loads((out / "summary.json").read_text())
    assert j["purpose"] == "demo; not comparable to experiment"
    assert j["engine"]["label"] == "geometric model, no dynamical amplitude, B4 scope applies"
    a = np.load(out / "arrays.npz")
    assert set(a.files) == set(j["arrays"])
    for k, meta in j["arrays"].items():
        assert meta["axes"] and meta["units"] and list(a[k].shape) == meta["shape"]
    assert j["glancing_angle"]["rule"] == "internal_bragg_external_angle"
    assert j["glancing_angle"]["V0_V"] == 12.0


def test_down_steps_reverse_the_sign(tmp_path):
    """The mirrored staircase (a/2 down, a/4 up, a/4 up) gives the opposite signed heights."""
    d = read_pipeline_file(SMOKE)
    st = d["sections"]["structure"]["staircase"]["value"]
    st["terrace_layers"] = [2, 0, 1]
    st["boundary_step_layers"] = 1
    cfg = load_pipeline_dict(d, variant=None)
    s = run(cfg, tmp_path / "mirror")
    got = sorted((round(x["built_height_A"], 6), x["height"]["h_A"], x["height"]["sigma_h_A"])
                 for x in _steps(s))
    assert [g[0] for g in got] == [-2.71545, 1.357725, 1.357725]
    for built, h, sig in got:
        assert abs(h - built) <= TOL_SIGMA * sig


def test_missing_project_input_without_stand_in_fails():
    d = read_pipeline_file(SMOKE)
    load_pipeline_dict(copy.deepcopy(d), variant=None)                   # the demo passes
    e = copy.deepcopy(d)
    del e["sections"]["detector"]["dose"]
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(e, variant=None)
    assert 6 in exc.value.items
    e = copy.deepcopy(d)
    e["sections"]["detector"]["dose"].update(value=None, label="PROJECT_INPUT")
    del e["sections"]["detector"]["dose"]["stands_in_for_item"]
    del e["sections"]["detector"]["dose"]["assumption_id"]
    with pytest.raises(MissingProjectInputError):
        load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    e["sections"]["detector"]["dose"]["assumption_id"] = "B99"             # not registered
    with pytest.raises(PipelineConfigError, match="registry"):
        load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    e["sections"]["detector"]["dose"]["assumption_id"] = "B19"             # registered, item 7
    with pytest.raises(PipelineConfigError, match="not mapped to PROJECT_INPUT item 6"):
        load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    del e["cfg_b"]["parameters"]["beam_azimuth_uvw"]                       # CFG-B gate, item 8
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(e, variant=None)
    assert 8 in exc.value.items
    e = copy.deepcopy(d)
    e["sections"]["illumination"]["glancing_angle"]["label"] = "TEST_ONLY"
    with pytest.raises(PipelineConfigError, match="TEST_ONLY"):
        load_pipeline_dict(e, variant=None)                                 # never from a file
    e = copy.deepcopy(d)
    e["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="blocking"):
        load_pipeline_dict(e, variant=None)


def test_typed_glancing_angle_is_refused_in_cfg_b():
    d = read_pipeline_file(SMOKE)
    d["cfg_b"]["parameters"]["glancing_angle_ext"] = dict(
        value=16.47, unit="mrad", label="ASSUMPTION", item=7, stands_in_for_item=7,
        assumption_id="B19", source="typed")
    with pytest.raises(PipelineConfigError, match="declared once"):
        load_pipeline_dict(d, variant=None)


def test_outside_b4_scope_is_refused(tmp_path):
    d = read_pipeline_file(SMOKE)
    d["cfg_b"]["parameters"]["beam_azimuth_uvw"].update(
        value=[1, 1, 0], label="TEST_ONLY", source="TEST_ONLY: stands in for item 8")
    d["cfg_b"]["parameters"]["beam_azimuth_uvw"].pop("stands_in_for_item")
    d["cfg_b"]["parameters"]["beam_azimuth_uvw"].pop("assumption_id")
    d["sections"]["structure"]["staircase"]["value"]["terrace_widths_periods"] = [20, 20, 20]
    cfg = load_pipeline_dict(d, variant=None, allow_test_only=True)
    from reflection_holo.forward.geometric import OutsideB4ScopeError
    from reflection_holo.pipeline.engines import build_structure, run_geometric
    # a pipeline run refuses TEST_ONLY values (A2c G3), so the engine refusal is checked on the
    # engine adapter the run calls
    with pytest.raises(PipelineConfigError, match="TEST_ONLY"):
        run(cfg, tmp_path / "b4")
    with pytest.raises(OutsideB4ScopeError, match="B4"):
        run_geometric(build_structure(cfg), cfg)


def test_output_directory_is_never_overwritten(smoke):
    out, _ = smoke
    with pytest.raises(OutputDirectoryError):
        run(SMOKE, out)


def test_cli_list_inputs_and_dry_run(capsys):
    assert cli_main(["list-inputs", "--config", str(SMOKE)]) == 0
    txt = capsys.readouterr().out
    assert "run-level gate: PASS" in txt and "ASSUMPTION B24 stand-in" in txt
    assert cli_main(["dry-run", "--config", str(SMOKE)]) == 0
    assert "exit plane [1031, 128] px" in capsys.readouterr().out
