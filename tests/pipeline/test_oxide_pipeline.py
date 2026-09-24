"""Pipeline with the continuum oxide (report E4): the item-12 gate, the B41 demo variants, the
variant-level CFG-B records, refusal in comparison runs, and the geometric demo end to end.

Fabricated values that exercise the gate are TEST values of in-memory dictionaries only; the shipped
configuration files are read, never written.
"""
import copy

import pytest

from reflection_holo.io.config import MissingProjectInputError
from reflection_holo.pipeline import (PipelineConfigError, list_inputs, load_pipeline_dict,
                                      read_pipeline_file, run)
from reflection_holo.pipeline.config import OXIDE_KEYS, resolve_variant_cfg_b
from reflection_holo.structure.oxide import ContinuumOxideSpec

from conftest_pipeline import SMOKE, TOL_SIGMA

OXIDE_VARIANTS = ("oxide_2p0nm", "oxide_2p0nm_no_absorption", "oxide_1p5nm",
                  "oxide_1p5nm_no_absorption", "multislice_tiny_oxide_2p0nm")


def _oxide_rec(d, variant="oxide_2p0nm"):
    return d["variants"][variant]["cfg_b_parameters"]["surface_preparation_details"]


def _with_base_oxide(d, over, *, label="TEST_ONLY", variant="oxide_2p0nm"):
    """The base configuration (geometric) with the variant's structure settings and an overlayer
    record in cfg_b (in memory)."""
    e = copy.deepcopy(d)
    rec = copy.deepcopy(_oxide_rec(d, variant))
    rec["value"]["overlayer"] = over
    if label == "TEST_ONLY":
        rec.update(label="TEST_ONLY", source="TEST: fabricated to exercise the gate")
        for k in ("stands_in_for_item", "assumption_id"):
            rec.pop(k)
    e["cfg_b"]["parameters"]["surface_preparation_details"] = rec
    e["sections"]["structure"].update(substrate_layers=12, vacuum_above_A=20.0)
    return e


@pytest.fixture(scope="module")
def smoke():
    return read_pipeline_file(SMOKE)


@pytest.mark.parametrize("variant", OXIDE_VARIANTS)
def test_b41_variants_load_and_build_the_oxide(smoke, variant):
    cfg = load_pipeline_dict(smoke, variant=variant)
    over = cfg.cfg_b.value("surface_preparation_details")["overlayer"]
    assert over["model"] == "continuum_oxide" and set(over) == set(OXIDE_KEYS)
    p12 = cfg.cfg_b.parameters["surface_preparation_details"]
    assert (p12.label, p12.assumption_id) == ("ASSUMPTION", "B41")
    assert over["vacuum_edge_width_A"] >= 0.5 and over["amorphous_si_thickness_A"] == 0.0
    # the base stays clean (B26): demo configurations as variants, never the base
    base = load_pipeline_dict(smoke, variant=None)
    assert base.cfg_b.value("surface_preparation_details")["overlayer"] == "none"
    assert base.cfg_b.parameters["surface_preparation_details"].assumption_id == "B26"


@pytest.mark.parametrize("variant", OXIDE_VARIANTS)
def test_b41_is_refused_in_comparison_runs(smoke, variant):
    d = copy.deepcopy(smoke)
    d["purpose"] = "comparison"
    with pytest.raises((PipelineConfigError, MissingProjectInputError), match="B41"):
        load_pipeline_dict(d, variant=variant)


def test_list_inputs_shows_the_b41_stand_in(smoke):
    rows = {r["parameter"]: r for r in list_inputs(smoke, variant="oxide_1p5nm")}
    assert rows["cfg_b.surface_preparation_details"]["status"] == "ASSUMPTION B41 stand-in"
    rows0 = {r["parameter"]: r for r in list_inputs(smoke, variant=None)}
    assert rows0["cfg_b.surface_preparation_details"]["status"] == "ASSUMPTION B26 stand-in"


def test_variant_cfg_b_records_are_whole_records(smoke):
    d = copy.deepcopy(smoke)
    d["variants"]["oxide_2p0nm"]["cfg_b_parameters"]["surface_preparation_details"] = {
        "value": {"termination": "bulk", "overlayer": "none"}}
    with pytest.raises(PipelineConfigError, match="whole record"):
        resolve_variant_cfg_b(d, "oxide_2p0nm")
    d["variants"]["oxide_2p0nm"]["cfg_b_parameters"] = {}
    with pytest.raises(PipelineConfigError, match="non-empty"):
        load_pipeline_dict(d, variant="oxide_2p0nm")
    d["variants"]["oxide_2p0nm"]["other"] = 1
    with pytest.raises(PipelineConfigError, match="must be"):
        load_pipeline_dict(d, variant="oxide_2p0nm")
    # the resolved CFG-B block (with the variant's record) is what is hashed and recorded
    cfg = load_pipeline_dict(smoke, variant="oxide_2p0nm")
    assert cfg.cfg_b_raw["parameters"]["surface_preparation_details"]["assumption_id"] == "B41"


# --------------------------------------------------------------------------------------------------
# the item-12 gate: every key required; refusals
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("key", [k for k in OXIDE_KEYS if k != "model"])
def test_every_oxide_key_is_required(smoke, key):
    over = copy.deepcopy(_oxide_rec(smoke)["value"]["overlayer"])
    over.pop(key)
    with pytest.raises(PipelineConfigError, match=f"item 12.*{key}"):
        load_pipeline_dict(_with_base_oxide(smoke, over), variant=None, allow_test_only=True)


@pytest.mark.parametrize("change,match", [
    (dict(vacuum_edge_width_A=0.25), "graded over at least 0.5"),
    (dict(consumed_layers=6), "nearest whole count is 7"),
    (dict(model="atomistic"), "continuum oxide"),
    (dict(extra_key=1.0), "unknown"),
    (dict(amorphous_si_thickness_A=10.0), "amorphous_si_V_real_V"),
    (dict(thickness_A=-20.0), "thickness_A"),
    (dict(V_imag_V=-0.4), "V'_ox"),
])
def test_invalid_oxide_values_are_refused(smoke, change, match):
    over = dict(_oxide_rec(smoke)["value"]["overlayer"], **change)
    with pytest.raises(PipelineConfigError, match=match):
        load_pipeline_dict(_with_base_oxide(smoke, over), variant=None, allow_test_only=True)


def test_zero_absorption_or_a_si_under_project_input_needs_assumption(smoke):
    """V'_ox = 0 must carry an ASSUMPTION (or TEST_ONLY) label: a supplied PROJECT_INPUT stating 0
    is refused rather than taken as a measurement. Changed on purpose by report X4 (audit A8 M1):
    a-Si = 0 labelled PROJECT_INPUT (a measured zero) is now ACCEPTED, through the per-parameter
    labels; E4's docstring stated its refusal, which made a measured 'no amorphous Si' impossible
    in a comparison run."""
    over = dict(_oxide_rec(smoke)["value"]["overlayer"], V_imag_V=0.0)
    over["labels"] = dict(over["labels"], V_imag="PROJECT_INPUT")
    e = _with_base_oxide(smoke, over)
    rec = e["cfg_b"]["parameters"]["surface_preparation_details"]
    rec.update(label="PROJECT_INPUT", supplied_by="Auditor", supplied_on="2026-09-24",
               source="TEST: fabricated supply to exercise the gate")
    with pytest.raises(PipelineConfigError, match="ASSUMPTION"):
        load_pipeline_dict(e, variant=None, allow_test_only=True)
    from reflection_holo.pipeline.config import oxide_spec_from_config
    over = dict(_oxide_rec(smoke)["value"]["overlayer"])
    over["labels"] = dict(over["labels"], amorphous_si="PROJECT_INPUT")
    e = _with_base_oxide(smoke, over)
    e["cfg_b"]["parameters"]["surface_preparation_details"].update(
        label="PROJECT_INPUT", supplied_by="Auditor", supplied_on="2026-09-24",
        source="TEST: fabricated supply to exercise the gate")
    spec = oxide_spec_from_config(load_pipeline_dict(e, variant=None).cfg_b)
    assert spec.amorphous_si_thickness_A == 0.0
    assert spec.labels["amorphous_si"].startswith("PROJECT_INPUT item 12")
    assert spec.labels["thickness"] == "ASSUMPTION B41 (stands in for PROJECT_INPUT item 12)"


def test_clean_stand_in_b26_cannot_carry_an_oxide(smoke):
    e = _with_base_oxide(smoke, _oxide_rec(smoke)["value"]["overlayer"], label="keep")
    e["cfg_b"]["parameters"]["surface_preparation_details"]["assumption_id"] = "B26"
    with pytest.raises(PipelineConfigError, match="B26 states a clean surface"):
        load_pipeline_dict(e, variant=None, allow_test_only=True)


def test_reconstruction_under_the_oxide_is_refused(smoke):
    e = _with_base_oxide(smoke, _oxide_rec(smoke)["value"]["overlayer"])
    e["cfg_b"]["parameters"]["surface_preparation_details"]["value"]["termination"] = "p(2x1)s"
    with pytest.raises(PipelineConfigError, match="reconstruction under an overlayer"):
        load_pipeline_dict(e, variant="multislice_tiny", allow_test_only=True)


def test_feature_path_refuses_the_oxide():
    from conftest_pipeline import REPO
    d = read_pipeline_file(REPO / "configs" / "demo_smoke_torus_trench.yaml")
    rec = d["cfg_b"]["parameters"]["surface_preparation_details"]
    smoke = read_pipeline_file(SMOKE)
    rec.update(value={"termination": "bulk",
                      "overlayer": _oxide_rec(smoke)["value"]["overlayer"]},
               label="TEST_ONLY", source="TEST: fabricated to exercise the gate")
    rec.pop("stands_in_for_item", None)
    rec.pop("assumption_id", None)
    with pytest.raises(PipelineConfigError, match="feature path"):
        load_pipeline_dict(d, variant=None, allow_test_only=True)


def test_spec_built_by_the_pipeline_carries_the_record_label(smoke):
    from reflection_holo.pipeline.config import oxide_spec_from_config
    cfg = load_pipeline_dict(smoke, variant="oxide_1p5nm")
    spec = oxide_spec_from_config(cfg.cfg_b)
    assert isinstance(spec, ContinuumOxideSpec)
    # report X5 (audit A9b M2), changed on purpose: the consumed-layer count is DERIVED_HERE (from
    # the B41 labels of the thickness, density and a-Si), every other parameter carries B41
    labels = dict(spec.labels)
    assert labels.pop("consumed_layers").startswith("DERIVED_HERE (consumed-layer count computed")
    assert set(labels.values()) == {"ASSUMPTION B41 (stands in for PROJECT_INPUT item 12)"}
    assert spec.terrace_thickness_A is None and spec.sharp_edge_test_flag is False
    assert (spec.thickness_A, spec.consumed_layers) == (15.0, 5)


# --------------------------------------------------------------------------------------------------
# end to end (geometric) and the multislice dry run
# --------------------------------------------------------------------------------------------------
def test_geometric_demo_under_the_oxide_recovers_the_steps(tmp_path, smoke):
    """The conformal layer leaves the step phases unchanged (E9 section 3 item 1), so the built
    step heights are recovered within 3 propagated standard deviations (as the base demo)."""
    s = run(load_pipeline_dict(smoke, variant="oxide_2p0nm"), tmp_path / "out")
    over = s["structure"]["options"]["overlayer"]
    assert over["value"] == "continuum_oxide" and over["conformal"] is True
    assert s["variant"] == "oxide_2p0nm"
    steps = s["quantification"]["steps"]
    assert len(steps) == 3
    for st in steps:
        assert st["measured"], st
        h = st["height"]
        assert h is not None, st.get("reason")
        assert abs(h["h_A"] - st["built_height_A"]) <= TOL_SIGMA * h["sigma_h_A"], (st, h)


def test_multislice_oxide_variant_passes_the_engine_setup(smoke):
    pytest.importorskip("abtem")
    from reflection_holo.pipeline.estimates import dry_run
    out = dry_run(load_pipeline_dict(smoke, variant="multislice_tiny_oxide_2p0nm"))
    g = out["geometry_checks"]
    assert g["item4_buildup_length_through_overlayer"]["passed"] is True
    assert "incident_int_layer" in str(out["band_checks"])
    assert out["mip_check"]["potential_mip_V"] == pytest.approx(13.903, abs=5e-4)
