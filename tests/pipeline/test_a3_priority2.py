"""Regression tests of the priority-2 pipeline fixes (audit A3 M1, M2, M6; A2c G3 and residual R1
in the pipeline; report docs/agent_reports/S4_pipeline_fixes.md). Each test reproduces the
auditor's case (scratch scripts repro_r2.py, repro_comparison_leak.py, repro_convergence.py,
repro_ignored_inputs.py, repro_item9.py; A2c r5b). Fabricated "supplied" values are TEST values
that exercise the gate; they never appear in configs/.
"""
import copy
import importlib
import json

import pytest

from reflection_holo.io import config as IOC
from reflection_holo.pipeline import (PipelineConfigError, list_inputs, load_pipeline_dict,
                                      read_pipeline_file, run)
from reflection_holo.pipeline.__main__ import main as cli_main

from conftest_pipeline import SMOKE

R = importlib.import_module("reflection_holo.pipeline.run")
# The structured supply fields exist only after the A2c G2 fix; on the pre-fix code the helper
# writes the free-text form the old gate required, so that the auditor's case is reproduced there.
STRUCTURED = hasattr(IOC, "SUPPLY_KEYS")
BLOCKING = (3, 4, 5, 7, 8, 11, 12, 15)


def _supply(rec, item, who="Auditor", when="2026-09-23"):
    rec["label"] = "PROJECT_INPUT"
    rec["source"] = f"supplied by {who} {when} (TEST: fabricated to exercise the gate)"
    rec["item"] = item
    rec.pop("stands_in_for_item", None)
    rec.pop("assumption_id", None)
    if STRUCTURED:
        rec.update(supplied_by=who, supplied_on=when)


def _test_only(rec, value):
    rec.update(value=value, label="TEST_ONLY", source="TEST_ONLY: fabricated to exercise the gate")
    rec.pop("stands_in_for_item", None)
    rec.pop("assumption_id", None)


# --------------------------------------------------------------------------------------------------
# M1: R2 heights near 0 "resolved"
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("shift", [{"along_beam": 0.0, "perpendicular": 10.0},
                                   {"along_beam": 20.0, "perpendicular": 0.0}],
                         ids=["perp", "along"])
def test_r2_differential_phase_returns_no_height(tmp_path, shift):
    """A3 M1 (repro_r2.py): R2 with reference_trajectory reflected_flat_area returned h = -0.0001
    +- 0.0004 A and +0.0002 +- 0.0004 A 'resolved' for steps built at +2.7155 and -1.3577 A."""
    d = read_pipeline_file(SMOKE)
    P = d["cfg_b"]["parameters"]
    P["reference_model"]["value"] = "R2"
    P["reference_trajectory"]["value"] = "reflected_flat_area"
    d["sections"]["reference"]["shift"] = dict(value=shift, unit="A", label="ASSUMPTION", item=16,
                                               stands_in_for_item=16, assumption_id="B28",
                                               source="TEST (A3 repro_r2.py): R2 shift")
    s = run(load_pipeline_dict(d, variant=None), tmp_path / "r2")
    for st in s["quantification"]["steps"]:
        assert st.get("height") is None, (st["built_height_A"], st.get("height"))
        assert "differential" in st["reason"].lower(), st["reason"]
    assert s["height_verdict"]["withheld"]
    assert "R2" in s["height_verdict"]["line"]


# --------------------------------------------------------------------------------------------------
# M2: the comparison gate
# --------------------------------------------------------------------------------------------------
def _comparison_with_blocking_supplied():
    """repro_comparison_leak.py: purpose comparison, every blocking stand-in replaced by a
    fabricated PROJECT_INPUT; the glancing angle supplied as a measured NUMBER (a rule-form angle
    labelled PROJECT_INPUT is a separate refusal, tested below)."""
    d = read_pipeline_file(SMOKE)
    d["purpose"] = "comparison"
    for p in d["cfg_b"]["parameters"].values():
        if p.get("label") == "ASSUMPTION" and p.get("item") in BLOCKING:
            _supply(p, p["item"])
    for sec in d["sections"].values():
        for r in sec.values():
            if isinstance(r, dict) and r.get("label") == "ASSUMPTION" and r.get("item") in BLOCKING:
                _supply(r, r["item"])
    ga = d["sections"]["illumination"]["glancing_angle"]
    ga.update(value=16.474333, unit="mrad")
    return d


def test_comparison_refuses_every_demo_stand_in():
    """A3 M2 (a): with the blocking items supplied, the gate PASSED although B24 (item 6), B28
    (item 16), B29 (item 19), B31 (item 1) and B27 (item 13) remained."""
    d = _comparison_with_blocking_supplied()
    with pytest.raises(PipelineConfigError, match="comparison") as exc:
        load_pipeline_dict(d, variant=None)
    msg = str(exc.value)
    for aid in ("B24", "B27", "B28", "B29", "B31"):
        assert aid in msg, (aid, msg)


def test_comparison_passes_without_demo_stand_ins_and_lists_the_remaining_assumptions():
    d = _comparison_with_blocking_supplied()
    for sec in d["sections"].values():
        for r in sec.values():
            if isinstance(r, dict) and r.get("label") == "ASSUMPTION":
                _supply(r, r["item"])
    for p in d["cfg_b"]["parameters"].values():
        if p.get("label") == "ASSUMPTION" and p.get("assumption_id") in {f"B{i}" for i in
                                                                         range(19, 33)}:
            _supply(p, p["item"])
    cfg = load_pipeline_dict(d, variant=None)
    from reflection_holo.pipeline.config import assumptions_in_use
    ids = {a["assumption_id"] for a in assumptions_in_use(cfg)}
    assert {"B1", "B17", "B18"} <= ids and not any(a["demo_only"] for a in assumptions_in_use(cfg))


def test_rule_form_angle_from_an_assumed_v0_cannot_be_labelled_project_input():
    """A3 M2 (b): the rule form labelled PROJECT_INPUT computed the angle from V0 = 12.0 V
    (ASSUMPTION B1) and recorded it as PROJECT_INPUT (any purpose)."""
    d = read_pipeline_file(SMOKE)
    _supply(d["sections"]["illumination"]["glancing_angle"], 7)
    with pytest.raises(PipelineConfigError, match="cannot carry the label PROJECT_INPUT"):
        load_pipeline_dict(d, variant=None)
    _supply(d["cfg_b"]["parameters"]["mean_inner_potential_V"], 20)   # V0 supplied: allowed
    cfg = load_pipeline_dict(d, variant=None)
    assert cfg.glancing_angle["V0_record"]["label"] == "PROJECT_INPUT"


# --------------------------------------------------------------------------------------------------
# M6: supplied inputs that no path represents are refused
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("variant", [None, "multislice_tiny"])
def test_nonzero_convergence_is_refused_on_every_engine_path(variant):
    """repro_convergence.py: 0.5 mrad was refused by the geometric engine at run time but the
    multislice path RAN it as a plane wave, listing item 3 as SUPPLIED."""
    d = read_pipeline_file(SMOKE)
    _test_only(d["cfg_b"]["parameters"]["convergence_semi_angle"], 0.5)
    with pytest.raises(PipelineConfigError, match="convergen"):
        load_pipeline_dict(d, variant=variant, allow_test_only=True)


@pytest.mark.parametrize("variant", [None, "multislice_tiny"])
def test_pattern_features_are_refused(variant):
    """repro_ignored_inputs.py: pattern_geometry {features: [mesa]} RAN (heights returned)."""
    d = read_pipeline_file(SMOKE)
    _test_only(d["cfg_b"]["parameters"]["pattern_geometry"],
               {"features": [{"type": "mesa", "height_nm": 10.0, "width_nm": 200.0}]})
    with pytest.raises(PipelineConfigError, match="pattern_geometry"):
        load_pipeline_dict(d, variant=variant, allow_test_only=True)


@pytest.mark.parametrize("variant", [None, "multislice_tiny"])
def test_overlayer_is_refused(variant):
    """repro_ignored_inputs.py: overlayer SiO2 10 A RAN on the multislice path."""
    d = read_pipeline_file(SMOKE)
    _test_only(d["cfg_b"]["parameters"]["surface_preparation_details"],
               {"termination": "bulk", "overlayer": {"material": "SiO2", "thickness_A": 10.0,
                                                     "density_g_cm3": 2.2}})
    with pytest.raises(PipelineConfigError, match="overlayer"):
        load_pipeline_dict(d, variant=variant, allow_test_only=True)


def test_rule_reflection_must_equal_the_target_reflection():
    """repro_item9.py: target (0,0,12) supplied, the angle computed for (0,0,8): gate PASSED."""
    d = read_pipeline_file(SMOKE)
    _test_only(d["cfg_b"]["parameters"]["target_reflection_hkl"], [0, 0, 12])
    with pytest.raises(PipelineConfigError, match="target reflection"):
        load_pipeline_dict(d, variant=None, allow_test_only=True)


def test_list_inputs_marks_unused_inputs_and_shows_the_engine_v0():
    """A3 M6 listing and m2: an input accepted but not used on the path is 'NOT USED on this path';
    for the multislice engine item 20 shows the potential's MIP 13.903 V that is actually used and
    the CFG-B V0 12.0 V as not used."""
    d = read_pipeline_file(SMOKE)
    rows = {r["parameter"]: r for r in list_inputs(d, variant=None)}
    assert rows["cfg_b.step_types"]["status"].endswith("NOT USED on this path")
    assert rows["cfg_b.surface_preparation_method"]["status"] == "SUPPLIED, NOT USED on this path"
    assert rows["cfg_b.mean_inner_potential_V"]["used"] is True
    ms = {r["parameter"]: r for r in list_inputs(d, variant="multislice_tiny")}
    assert ms["cfg_b.mean_inner_potential_V"]["status"].endswith("NOT USED on this path")
    mip = ms["sections.engine.multislice.potential_mip"]
    assert mip["item"] == 20 and mip["value"] == 13.903 and "USED" in mip["status"]


# --------------------------------------------------------------------------------------------------
# A2c G3: TEST_ONLY never reaches a pipeline run; the manifest records it
# --------------------------------------------------------------------------------------------------
def test_run_refuses_a_test_only_configuration(tmp_path):
    """A2c G3: a configuration built in memory with allow_test_only=True ran Ali's experiment on
    TEST_ONLY values."""
    d = read_pipeline_file(SMOKE)
    _test_only(d["sections"]["detector"]["dose"], 500.0)
    cfg = load_pipeline_dict(d, variant=None, allow_test_only=True)
    assert cfg.test_only
    out = tmp_path / "test_only"
    with pytest.raises(PipelineConfigError, match="TEST_ONLY"):
        run(cfg, out)
    assert not out.exists() or not any(out.iterdir())


def test_manifest_records_test_only(tmp_path):
    run(SMOKE, tmp_path / "m")
    m = json.loads((tmp_path / "m" / "manifest.json").read_text())
    assert m["extra"]["test_only"] is False


def test_cli_offers_no_test_only_switch(capsys):
    with pytest.raises(SystemExit):
        cli_main(["run", "--config", str(SMOKE), "--out", "x", "--allow-test-only"])


# --------------------------------------------------------------------------------------------------
# A2c residual R1 in the pipeline: reference_correction "none" needs an object visibility minimum
# --------------------------------------------------------------------------------------------------
def test_pipeline_none_correction_requires_object_min_visibility():
    d = read_pipeline_file(SMOKE)
    proc = d["sections"]["reconstruction"]["processing"]["value"]
    proc["reference_correction"] = "none"
    with pytest.raises(PipelineConfigError, match="object_min_visibility"):
        load_pipeline_dict(copy.deepcopy(d), variant=None)
    proc["object_min_visibility"] = 0.3
    load_pipeline_dict(d, variant=None)
