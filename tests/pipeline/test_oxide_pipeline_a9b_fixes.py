"""Pipeline gate of the continuum oxide: the fixes of report X5 after the audit A9b (item 12).

A9b M2  (a) consumed_layers is computed by the code and labelled DERIVED_HERE (from the thickness,
        density and a-Si labels); a stated value must equal the derived count; never PROJECT_INPUT.
        (b) V_ox, V'_ox and the two edge widths are MODEL parameters: PROJECT_INPUT only with a
        measurement record, or the registered NON-DEMO model row B43 (not a stand-in), which a
        comparison run admits; B43 vouches for its nominal values and declared bracket ends only;
        the run records the bracket (oxide_item12_record, manifest and summary).
        (c) thickness and density stay PROJECT_INPUT in comparison runs.
        (d) the headline label is "mixed (...)" for mixed labels (A9b n1).
A9b m1  per-parameter ids outside OXIDE_STAND_IN_ROWS / OXIDE_MODEL_ROWS (B26 in particular) refused.
A9b m2  comparison runs need the item-12 uncertainties of thickness and density; a count interval
        that spans a rounding boundary is refused unless both parities are acknowledged; an unneeded
        acknowledgement is refused.
A9b n2  the B41 thickness is tied to its variant. n3, m6: the texts of the demo configuration and
        of the sizing tool.

Fabricated values that exercise the gate are TEST values of in-memory dictionaries only; the shipped
configuration file is read, never written.
"""
import copy
import json

import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.io.config import MissingProjectInputError
from reflection_holo.pipeline import PipelineConfigError, load_pipeline_dict, read_pipeline_file, run
from reflection_holo.pipeline.config import (OXIDE_MODEL_ROWS, assumptions_in_use,
                                             oxide_item12_record, oxide_spec_from_config)
from reflection_holo.structure import oxide as ox

from conftest_pipeline import REPO, SMOKE

SUPPLY = dict(label="PROJECT_INPUT", supplied_by="Auditor", supplied_on="2026-09-24",
              source="TEST: fabricated supply to exercise the gate")
TEST_REC = dict(label="TEST_ONLY", source="TEST: fabricated")
MEASURED = dict(thickness="PROJECT_INPUT", density="PROJECT_INPUT", amorphous_si="PROJECT_INPUT",
                consumed_layers="DERIVED_HERE")
B43 = {k: "ASSUMPTION B43" for k in ("V_real", "V_imag", "vacuum_edge", "interface")}
TEST_ONLY_LABELS = dict({k: "TEST_ONLY" for k in ox.LABEL_KEYS}, consumed_layers="DERIVED_HERE")
UNC_2NM = dict(thickness_uncertainty_A=1.0, density_uncertainty_g_cm3=0.05)


@pytest.fixture(scope="module")
def smoke():
    return read_pipeline_file(SMOKE)


def _rec(d, variant):
    return d["variants"][variant]["cfg_b_parameters"]["surface_preparation_details"]


def _variant(smoke, variant="oxide_2p0nm", *, record=None, labels=None, **over):
    """The smoke configuration with the variant's item-12 record modified in memory."""
    d = copy.deepcopy(smoke)
    rec = _rec(d, variant)
    rec["value"]["overlayer"].update(over)
    if labels is not None:
        rec["value"]["overlayer"]["labels"] = dict(rec["value"]["overlayer"]["labels"], **labels)
    if record:
        for k in ("stands_in_for_item", "assumption_id"):
            rec.pop(k, None)
        rec.update(record)
    return d


def _measured_b43(smoke, variant="oxide_2p0nm", **over):
    return _variant(smoke, variant, record=SUPPLY, labels=dict(MEASURED, **B43), **over)


def _refusal(d, variant="oxide_2p0nm", **kw):
    with pytest.raises((PipelineConfigError, MissingProjectInputError)) as exc:
        load_pipeline_dict(d, variant=variant, **kw)
    return str(exc.value)


# --------------------------------------------------------------------------------------------------
# A9b M2 (a): the consumed-layer count is DERIVED_HERE
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("record,label", [(SUPPLY, "PROJECT_INPUT"), (None, "ASSUMPTION B41"),
                                          (TEST_REC, "TEST_ONLY")])
def test_consumed_layers_is_never_supplied(smoke, record, label):
    d = _variant(smoke, record=record, labels=dict(consumed_layers=label))
    assert "never a PROJECT_INPUT (audit A9b M2)" in _refusal(d, allow_test_only=True)


def test_derived_label_only_on_the_count(smoke):
    d = _variant(smoke, record=TEST_REC, labels=dict(TEST_ONLY_LABELS, density="DERIVED_HERE"))
    assert "only ['consumed_layers'] carries 'DERIVED_HERE'" in _refusal(d, allow_test_only=True)


def test_derived_count_label_names_its_inputs(smoke):
    cfg = load_pipeline_dict(_measured_b43(smoke), variant="oxide_2p0nm")
    lab = oxide_spec_from_config(cfg.cfg_b).labels["consumed_layers"]
    assert lab.startswith("DERIVED_HERE (consumed-layer count computed by the code")
    assert "from thickness: PROJECT_INPUT item 12 (TEST: fabricated" in lab
    assert "density: PROJECT_INPUT item 12" in lab and "amorphous_si: PROJECT_INPUT" in lab


def test_stated_count_must_equal_the_derived_count(smoke):
    """At an exact tie (continuum depth 6.5 layers) both counts pass the |N a/4 - depth| <= a/8 rule
    of structure.oxide; the stated count must still be the one the code derives."""
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    t = 6.5 * (A_SI_A / 4) / f
    derived = ox.nearest_consumed_layers(thickness_A=t, density_g_cm3=2.20,
                                         amorphous_si_thickness_A=0.0, a_A=A_SI_A)
    other = 13 - derived
    d = _variant(smoke, record=TEST_REC, labels=TEST_ONLY_LABELS, thickness_A=t,
                 consumed_layers=other, rounding_boundary_acknowledged=True)
    msg = _refusal(d, allow_test_only=True)
    assert f"is not the count derived by the code ({derived}" in msg
    d = _variant(smoke, record=TEST_REC, labels=TEST_ONLY_LABELS, thickness_A=t,
                 consumed_layers=derived, rounding_boundary_acknowledged=True)
    load_pipeline_dict(d, variant="oxide_2p0nm", allow_test_only=True)


# --------------------------------------------------------------------------------------------------
# A9b M2 (b): model parameters: B43 or a measurement record
# --------------------------------------------------------------------------------------------------
def test_b43_model_row_in_a_supplied_record(smoke):
    cfg = load_pipeline_dict(_measured_b43(smoke), variant="oxide_2p0nm")
    spec = oxide_spec_from_config(cfg.cfg_b)
    assert spec.labels["V_real"] == ("ASSUMPTION B43 (model row, not a stand-in for a "
                                     "PROJECT_INPUT; audit A9b M2)")
    rows = [a for a in assumptions_in_use(cfg) if a["assumption_id"] == "B43"]
    assert len(rows) == 4 and not any(a["demo_only"] for a in rows)
    assert all("a model row, not a stand-in" in a["source"] for a in rows)
    rec = oxide_item12_record(cfg.cfg_b)
    assert rec["headline_label"] == ("mixed (ASSUMPTION B43, DERIVED_HERE, PROJECT_INPUT); "
                                     "per-parameter labels in 'labels'")
    got = {r["key"]: r for r in rec["model_rows"]}
    assert set(got) == {"V_real_V", "V_imag_V", "vacuum_edge_width_A", "interface_width_A"}
    assert got["V_real_V"]["used"] == "nominal" and got["V_real_V"]["bracket"].startswith(
        "10.1-11.5 V")
    assert got["V_imag_V"]["bracket"].startswith("0 or 0.39-0.44 V")
    assert "numerical requirement" in got["interface_width_A"]["bracket"]
    assert all("does not require the bracket ends to be run" in r["note"] for r in got.values())


@pytest.mark.parametrize("over,used", [(dict(V_real_V=11.5), "bracket end"),
                                       (dict(V_real_V=10.1), "bracket end"),
                                       (dict(V_imag_V=0.0), "bracket end"),
                                       (dict(V_imag_V=0.44), "bracket end"),
                                       (dict(V_real_V=10.5), None),
                                       (dict(V_imag_V=0.3), None),
                                       (dict(vacuum_edge_width_A=0.6), None),
                                       (dict(interface_width_A=1.0), None)])
def test_b43_vouches_for_its_nominal_values_and_bracket_ends_only(smoke, over, used):
    d = _measured_b43(smoke, **over)
    if used is None:
        assert "model row B43" in _refusal(d)
        return
    cfg = load_pipeline_dict(d, variant="oxide_2p0nm")
    (key, value), = over.items()
    row = {r["key"]: r for r in oxide_item12_record(cfg.cfg_b)["model_rows"]}[key]
    assert row["used"] == used and row["value"] == value


@pytest.mark.parametrize("record,labels,match", [
    (SUPPLY, dict(MEASURED, thickness="ASSUMPTION B43"), "covers only the model parameters"),
    (SUPPLY, dict(MEASURED, density="ASSUMPTION B43"), "covers only the model parameters"),
    (None, dict(V_real="ASSUMPTION B43"), "every parameter carries its id"),
])
def test_b43_is_refused_outside_its_parameters(smoke, record, labels, match):
    assert match in _refusal(_variant(smoke, record=record, labels=labels))


def test_measurement_record_for_project_input_model_parameters(smoke):
    labels = dict(MEASURED, **B43)
    labels["V_real"] = "PROJECT_INPUT"
    d = _variant(smoke, record=SUPPLY, labels=labels)
    assert "needs a measurement record" in _refusal(d)
    for bad in ("measured", "  ", "TBD"):
        d = _variant(smoke, record=SUPPLY, labels=labels, measurements=dict(V_real=bad))
        assert "must state what was measured and how" in _refusal(d)
    d = _variant(smoke, record=SUPPLY, labels=labels,
                 measurements=dict(V_real="TEST: fabricated", V_imag="TEST: fabricated"))
    assert "exactly the model parameters labelled PROJECT_INPUT" in _refusal(d)
    text = "TEST: fabricated off-axis electron holography of the witness oxide"
    cfg = load_pipeline_dict(_variant(smoke, record=SUPPLY, labels=labels,
                                      measurements=dict(V_real=text)), variant="oxide_2p0nm")
    assert oxide_spec_from_config(cfg.cfg_b).labels["V_real"].endswith(f"measured: {text})")
    assert oxide_item12_record(cfg.cfg_b)["measurements"] == dict(V_real=text)


def test_comparison_admits_the_model_row(smoke):
    """In a comparison run the oxide entries pass when thickness, density and a-Si are
    PROJECT_INPUT, the model parameters carry B43 and the uncertainties are stated; the run is
    still refused by the comparison gate for the demo's OTHER stand-ins, and no oxide entry is
    named. Control: V_real under the demo stand-in B41 is named."""
    d = _measured_b43(smoke, both_parities_acknowledged=True, **UNC_2NM)
    d["purpose"] = "comparison"
    msg = _refusal(d)
    assert "purpose 'comparison' refuses every demo stand-in" in msg
    assert "overlayer" not in msg and "uncertainties" not in msg
    d["variants"]["oxide_2p0nm"]["cfg_b_parameters"]["surface_preparation_details"]["value"][
        "overlayer"]["labels"]["V_real"] = "ASSUMPTION B41"
    assert "overlayer.V_real (item 12, B41)" in _refusal(d)


# --------------------------------------------------------------------------------------------------
# A9b m1: per-parameter ids must state continuum-oxide values
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("record,labels", [
    (SUPPLY, dict(MEASURED, **dict(B43, V_imag="ASSUMPTION B26"))),
    (SUPPLY, {k: "ASSUMPTION B26" for k in ox.LABEL_KEYS if k != "consumed_layers"}),
    (TEST_REC, dict(TEST_ONLY_LABELS, V_imag="ASSUMPTION B26")),
])
def test_clean_surface_row_is_refused_per_parameter(smoke, record, labels):
    msg = _refusal(_variant(smoke, record=record, labels=labels), allow_test_only=True)
    assert "B26 is not a row that states continuum-oxide values" in msg
    assert "B26 states a clean surface (audit A9b m1)" in msg


# --------------------------------------------------------------------------------------------------
# A9b m2: item-12 uncertainties and the count interval
# --------------------------------------------------------------------------------------------------
def test_comparison_needs_the_uncertainties(smoke):
    d = _measured_b43(smoke)
    d["purpose"] = "comparison"
    assert "needs the item-12 uncertainties" in _refusal(d)


def test_interval_across_a_boundary_needs_both_parities(smoke):
    d = _variant(smoke, record=TEST_REC, labels=TEST_ONLY_LABELS, both_parities_acknowledged=False,
                 **UNC_2NM)
    msg = _refusal(d, allow_test_only=True)
    assert "may be any of [6, 7] (even and odd parity" in msg and "both parities" in msg
    d = _variant(smoke, record=TEST_REC, labels=TEST_ONLY_LABELS, both_parities_acknowledged=True,
                 **UNC_2NM)
    cfg = load_pipeline_dict(d, variant="oxide_2p0nm", allow_test_only=True)
    ci = oxide_item12_record(cfg.cfg_b)["uncertainties"]["count_interval"]
    assert ci["counts"] == [6, 7] and ci["spans_boundary"] is True


def test_unneeded_both_parities_acknowledgement_is_refused(smoke):
    unc = dict(thickness_uncertainty_A=0.5, density_uncertainty_g_cm3=0.03)
    d = _variant(smoke, "oxide_1p5nm", record=TEST_REC, labels=TEST_ONLY_LABELS,
                 both_parities_acknowledged=True, **unc)
    assert "not needed" in _refusal(d, "oxide_1p5nm", allow_test_only=True)
    d = _variant(smoke, "oxide_1p5nm", record=TEST_REC, labels=TEST_ONLY_LABELS,
                 both_parities_acknowledged=False, **unc)
    load_pipeline_dict(d, variant="oxide_1p5nm", allow_test_only=True)


@pytest.mark.parametrize("over,labels,match", [
    (dict(thickness_uncertainty_A=1.0), TEST_ONLY_LABELS, "state all of"),
    (dict(UNC_2NM, both_parities_acknowledged="yes"), TEST_ONLY_LABELS, "True or False"),
    (dict(UNC_2NM, thickness_uncertainty_A=0.0, both_parities_acknowledged=True),
     TEST_ONLY_LABELS, "thickness_uncertainty_A"),
    (dict(UNC_2NM, density_uncertainty_g_cm3="0.05", both_parities_acknowledged=True),
     TEST_ONLY_LABELS, "number"),
    (dict(UNC_2NM, both_parities_acknowledged=True), None, "rows state no uncertainty"),
])
def test_uncertainty_refusals(smoke, over, labels, match):
    d = _variant(smoke, record=TEST_REC if labels else None, labels=labels, **over)
    assert match in _refusal(d, allow_test_only=True)


# --------------------------------------------------------------------------------------------------
# A9b n2: the B41 thickness is tied to its variant
# --------------------------------------------------------------------------------------------------
def test_b41_thickness_is_tied_to_its_variant(smoke):
    d = _variant(smoke, "oxide_1p5nm", thickness_A=20.0, consumed_layers=7,
                 rounding_boundary_acknowledged=True)
    assert "for variant 'oxide_1p5nm'" in _refusal(d, "oxide_1p5nm")
    d = _variant(smoke, "multislice_tiny_oxide_2p0nm", thickness_A=15.0, consumed_layers=5,
                 rounding_boundary_acknowledged=False)
    assert "for variant 'multislice_tiny_oxide_2p0nm'" in _refusal(d, "multislice_tiny_oxide_2p0nm")
    # at the base (no variant) the row's other pair is still accepted
    e = copy.deepcopy(smoke)
    rec = copy.deepcopy(_rec(smoke, "oxide_1p5nm"))
    rec.update(TEST_REC)
    for k in ("stands_in_for_item", "assumption_id"):
        rec.pop(k)
    e["cfg_b"]["parameters"]["surface_preparation_details"] = rec
    e["sections"]["structure"].update(substrate_layers=12, vacuum_above_A=20.0)
    cfg = load_pipeline_dict(e, variant=None, allow_test_only=True)
    assert oxide_spec_from_config(cfg.cfg_b).thickness_A == 15.0


# --------------------------------------------------------------------------------------------------
# The run records item 12 (manifest and summary; audit A9b M2)
# --------------------------------------------------------------------------------------------------
def test_run_records_the_model_row_bracket(tmp_path, smoke):
    cfg = load_pipeline_dict(_measured_b43(smoke, V_real_V=11.5), variant="oxide_2p0nm")
    s = run(cfg, tmp_path / "out")
    man = json.loads((tmp_path / "out" / "manifest.json").read_text())
    for rec in (man["extra"]["oxide_item12"], s["oxide_item12"]):
        rows = {r["key"]: r for r in rec["model_rows"]}
        assert rows["V_real_V"]["used"] == "bracket end" and rows["V_real_V"]["value"] == 11.5
        assert rows["V_real_V"]["nominal"] == OXIDE_MODEL_ROWS["B43"]["nominal"]["V_real_V"]
        assert rows["V_imag_V"]["bracket"] == OXIDE_MODEL_ROWS["B43"]["bracket"]["V_imag_V"]
        assert rec["headline_label"].startswith("mixed (")


# --------------------------------------------------------------------------------------------------
# A9b n3, m6: texts
# --------------------------------------------------------------------------------------------------
def test_layer_top_comments_of_the_demo_variants():
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    text = SMOKE.read_text()
    current = None
    seen = {}
    for line in text.splitlines():
        if line.startswith("  ") and not line.startswith("   ") and line.strip().endswith(":"):
            current = line.strip()[:-1]
        if "holds the top of the layer" in line:
            seen[current] = line
    for v, t in (("oxide_2p0nm", 20.0), ("oxide_2p0nm_no_absorption", 20.0),
                 ("oxide_1p5nm", 15.0), ("oxide_1p5nm_no_absorption", 15.0)):
        want = f"{(1 - f) * t + A_SI_A / 8:.2f} A above the top atomic planes"
        assert want in seen[v], (v, seen[v])
    out = (REPO / "tools" / "review" / "x5" / "x5_oxide_numbers_output.txt").read_text()
    assert "= 9.0563 A (= 9.06 A)" in out and "= 11.8487 A (= 11.85 A)" in out


def test_sizing_tool_labels_the_oxide_column_a_same_grid_lower_bound():
    for p in ("supercell_sizing.py", "supercell_sizing_output.txt"):
        text = (REPO / "tools" / "hpc" / p).read_text()
        assert "with oxide, same-grid lower bound: GPU device / CPU job peak (GB)" in text, p
        assert "SAME-GRID LOWER BOUND" in text and "audit A9b m6" in text, p
