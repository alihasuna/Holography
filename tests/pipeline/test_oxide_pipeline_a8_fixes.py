"""Pipeline gate of the continuum oxide: the fixes of report X4 after the audit A8 (item 12).

A8 M1  one label PER PARAMETER in the item-12 record (overlayer.labels): a measured a-Si = 0 is a
       PROJECT_INPUT inside a supplied record while other values remain ASSUMPTIONs; the labels are
       gated like records; purpose "comparison" refuses every per-parameter demo stand-in (and, item
       12 being blocking, every per-parameter ASSUMPTION).
A8 m2  a stand-in vouches only for the values its row states: B41 with overlayer "none" or with
       values outside its row is refused.
A8 m4  the rounding-boundary acknowledgement is required at 2.0 nm (B41) and refused at 1.5 nm.
A8 m5  a sharp interface is refused (the pipeline never sets the TEST_ONLY flags).
A8 n1  numbers as strings are refused; n3: {termination, overlayer} are both required at load.

Fabricated values that exercise the gate are TEST values of in-memory dictionaries only; the shipped
configuration file is read, never written.
"""
import copy

import pytest

from reflection_holo.io.config import ConfigError, MissingProjectInputError
from reflection_holo.pipeline import PipelineConfigError, list_inputs, load_pipeline_dict
from reflection_holo.pipeline import read_pipeline_file
from reflection_holo.pipeline.config import (OXIDE_STAND_IN_ROWS, assumptions_in_use,
                                             oxide_spec_from_config)
from reflection_holo.structure import oxide as ox

from conftest_pipeline import SMOKE

SUPPLY = dict(label="PROJECT_INPUT", supplied_by="Auditor", supplied_on="2026-09-24",
              source="TEST: fabricated supply to exercise the gate")


@pytest.fixture(scope="module")
def smoke():
    return read_pipeline_file(SMOKE)


def _rec(d, variant="oxide_2p0nm"):
    return d["variants"][variant]["cfg_b_parameters"]["surface_preparation_details"]


def _variant(smoke, variant="oxide_2p0nm", *, record=None, **over):
    """The smoke configuration with the variant's item-12 record modified in memory: record keys
    (label, supply, ...) and overlayer values (labels merged)."""
    d = copy.deepcopy(smoke)
    rec = _rec(d, variant)
    labels = over.pop("labels", None)
    rec["value"]["overlayer"].update(over)
    if labels:
        rec["value"]["overlayer"]["labels"].update(labels)
    if record:
        if record.get("label") in ("PROJECT_INPUT", "TEST_ONLY"):
            for k in ("stands_in_for_item", "assumption_id"):
                rec.pop(k, None)
        rec.update(record)
    return d


# --------------------------------------------------------------------------------------------------
# A8 M1: per-parameter labels
# --------------------------------------------------------------------------------------------------
def test_measured_zero_a_si_in_a_supplied_record():
    smoke = read_pipeline_file(SMOKE)
    d = _variant(smoke, record=SUPPLY, labels=dict(amorphous_si="PROJECT_INPUT",
                                                    thickness="PROJECT_INPUT"))
    cfg = load_pipeline_dict(d, variant="oxide_2p0nm")
    spec = oxide_spec_from_config(cfg.cfg_b)
    assert spec.labels["amorphous_si"] == (
        "PROJECT_INPUT item 12 (TEST: fabricated supply to exercise the gate)")
    assert spec.labels["V_real"] == "ASSUMPTION B41 (stands in for PROJECT_INPUT item 12)"
    rows = [a for a in assumptions_in_use(cfg) if a["parameter"].startswith(
        "cfg_b.surface_preparation_details.overlayer.")]
    assert {a["parameter"].rsplit(".", 1)[1] for a in rows} == set(ox.LABEL_KEYS) - {
        "amorphous_si", "thickness"}
    assert all(a["assumption_id"] == "B41" and a["demo_only"] for a in rows)


def test_comparison_refuses_per_parameter_stand_ins(smoke):
    d = _variant(smoke, record=SUPPLY, labels={k: "PROJECT_INPUT" for k in ox.LABEL_KEYS
                                               if k != "V_real"})
    d["purpose"] = "comparison"
    with pytest.raises((PipelineConfigError, MissingProjectInputError),
                       match=r"overlayer\.V_real \(item 12, B41\)"):
        load_pipeline_dict(d, variant="oxide_2p0nm")


@pytest.mark.parametrize("record,labels,match", [
    (None, {"amorphous_si": "PROJECT_INPUT"}, "shares the supply record"),
    (None, {"density": "TEST_ONLY"}, "only inside a TEST_ONLY record"),
    (None, {"density": "ASSUMPTION B26"}, "every parameter carries its id"),
    (SUPPLY, {"density": "ASSUMPTION B20"}, "not mapped to PROJECT_INPUT item 12"),
    (SUPPLY, {"density": "assumed"}, "must be 'PROJECT_INPUT'"),
    (SUPPLY, {"density": None}, "must be 'PROJECT_INPUT'"),
])
def test_invalid_per_parameter_labels_are_refused(smoke, record, labels, match):
    d = _variant(smoke, record=record, labels=labels)
    with pytest.raises(PipelineConfigError, match=match):
        load_pipeline_dict(d, variant="oxide_2p0nm", allow_test_only=True)


@pytest.mark.parametrize("change", ["drop", "extra", "not a mapping"])
def test_label_keys_must_be_exact(smoke, change):
    d = copy.deepcopy(smoke)
    over = _rec(d)["value"]["overlayer"]
    if change == "drop":
        over["labels"].pop("interface")
    elif change == "extra":
        over["labels"]["overrides"] = "ASSUMPTION B41"
    else:
        over["labels"] = "ASSUMPTION B41"
    with pytest.raises(PipelineConfigError, match="one label per physical parameter"):
        load_pipeline_dict(d, variant="oxide_2p0nm")


def test_per_parameter_test_only_needs_an_in_memory_test_only_record(smoke):
    d = _variant(smoke, record=dict(label="TEST_ONLY", source="TEST: fabricated"),
                 labels={k: "TEST_ONLY" for k in ox.LABEL_KEYS})
    cfg = load_pipeline_dict(d, variant="oxide_2p0nm", allow_test_only=True)
    assert cfg.test_only is True
    with pytest.raises(ConfigError, match="TEST_ONLY"):
        load_pipeline_dict(d, variant="oxide_2p0nm")


def test_list_inputs_shows_one_row_per_parameter(smoke):
    rows = {r["parameter"]: r for r in list_inputs(smoke, variant="oxide_2p0nm")}
    for k in ox.LABEL_KEYS:
        r = rows[f"cfg_b.surface_preparation_details.overlayer.{k}"]
        assert r["item"] == 12 and r["status"] == "ASSUMPTION B41"
    assert rows["cfg_b.surface_preparation_details.overlayer.thickness"]["value"] == 20.0


# --------------------------------------------------------------------------------------------------
# A8 m2: a stand-in vouches only for its row
# --------------------------------------------------------------------------------------------------
def test_b41_with_no_overlayer_is_refused(smoke):
    d = copy.deepcopy(smoke)
    _rec(d)["value"]["overlayer"] = "none"
    with pytest.raises(PipelineConfigError, match="under stand-in B41"):
        load_pipeline_dict(d, variant="oxide_2p0nm")


@pytest.mark.parametrize("over,match", [
    (dict(thickness_A=50.0, consumed_layers=16, V_imag_V=0.1,          # A8's probe (C10)
          rounding_boundary_acknowledged=False), "V_imag_V"),
    (dict(thickness_A=50.0, consumed_layers=16, rounding_boundary_acknowledged=False),
     "consumed_layers"),
    (dict(thickness_A=20.5, rounding_boundary_acknowledged=False), "thickness_A"),
    (dict(V_imag_V=0.1), "V_imag_V"),
    (dict(V_real_V=11.5), "V_real_V"),
    (dict(density_g_cm3=2.27, consumed_layers=7, rounding_boundary_acknowledged=False),
     "density_g_cm3"),
    (dict(vacuum_edge_width_A=0.6), "vacuum_edge_width_A"),
    (dict(interface_width_A=0.8), "interface_width_A"),
    (dict(material="amorphous Si"), "material"),
    (dict(thickness_A=15.0, consumed_layers=5, rounding_boundary_acknowledged=False,
          V_real_V=10.34), None),
])
def test_b41_values_outside_its_row_are_refused(smoke, over, match):
    d = _variant(smoke, **over)
    if match is None:                              # the row's other pair (1.5 nm, 5): accepted
        load_pipeline_dict(d, variant="oxide_2p0nm")
        return
    with pytest.raises(PipelineConfigError, match=f"stand-in B41.*{match}"):
        load_pipeline_dict(d, variant="oxide_2p0nm")


def test_b41_row_table_matches_the_shipped_variants(smoke):
    row = OXIDE_STAND_IN_ROWS["B41"]
    for v in ("oxide_2p0nm", "oxide_2p0nm_no_absorption", "oxide_1p5nm",
              "oxide_1p5nm_no_absorption", "multislice_tiny_oxide_2p0nm"):
        over = _rec(smoke, v)["value"]["overlayer"]
        assert (over["thickness_A"], over["consumed_layers"]) in row["thickness_and_count"]
        assert over["V_imag_V"] in row["V_imag_V"] and over["density_g_cm3"] in row["density_g_cm3"]
        assert set(over["labels"].values()) == {"ASSUMPTION B41"}


# --------------------------------------------------------------------------------------------------
# A8 m4, m5, n1, n3
# --------------------------------------------------------------------------------------------------
def test_rounding_boundary_acknowledgement_in_the_variants(smoke):
    for v, ack in (("oxide_2p0nm", True), ("oxide_1p5nm", False),
                   ("multislice_tiny_oxide_2p0nm", True)):
        assert _rec(smoke, v)["value"]["overlayer"]["rounding_boundary_acknowledged"] is ack
    with pytest.raises(PipelineConfigError, match="rounding_boundary_acknowledged = True"):
        load_pipeline_dict(_variant(smoke, rounding_boundary_acknowledged=False),
                           variant="oxide_2p0nm")
    with pytest.raises(PipelineConfigError, match="not needed"):
        load_pipeline_dict(_variant(smoke, "oxide_1p5nm", rounding_boundary_acknowledged=True),
                           variant="oxide_1p5nm")
    with pytest.raises(PipelineConfigError, match="True or False"):
        load_pipeline_dict(_variant(smoke, rounding_boundary_acknowledged="yes"),
                           variant="oxide_2p0nm")


@pytest.mark.parametrize("w_i", [0.0, 0.3])
def test_sharp_interface_is_refused(smoke, w_i):
    d = _variant(smoke, record=dict(label="TEST_ONLY", source="TEST: fabricated"),
                 labels={k: "TEST_ONLY" for k in ox.LABEL_KEYS}, interface_width_A=w_i)
    with pytest.raises(PipelineConfigError, match="graded over at least 0.5"):
        load_pipeline_dict(d, variant="oxide_2p0nm", allow_test_only=True)


def test_numbers_as_strings_are_refused(smoke):
    with pytest.raises(PipelineConfigError, match="number"):
        load_pipeline_dict(_variant(smoke, V_imag_V="0.4"), variant="oxide_2p0nm")


@pytest.mark.parametrize("missing", ["overlayer", "termination"])
def test_item12_value_needs_both_keys_at_load(smoke, missing):
    d = copy.deepcopy(smoke)
    d["cfg_b"]["parameters"]["surface_preparation_details"]["value"].pop(missing)
    with pytest.raises(PipelineConfigError, match=f"must state both.*{missing}"):
        load_pipeline_dict(d, variant=None)
