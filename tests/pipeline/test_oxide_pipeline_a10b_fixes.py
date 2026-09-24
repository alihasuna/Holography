"""Pipeline gate of the continuum oxide: the fixes of report X6 after the re-audit A10b (item 12).

A10b M1  X5's both_parities_acknowledged is retired (it ran nothing). When the count interval over
         the stated item-12 uncertainties spans a rounding boundary the record states
         consumed_layers_parity: lower | upper; the run builds that count of the interval (both are
         consistent with the uncertainties; no thickness is altered), labels it DERIVED_HERE with
         the qualifier "parity variant <lower|upper> of an interval spanning a boundary", and records
         the interval, the variant and that the other variant is a separate run (item-12 record,
         manifest, summary). The key is refused when no boundary is spanned, with a value outside
         {lower, upper}, without uncertainties, and for an interval of more than two counts.
A10b M2  A PROJECT_INPUT model parameter needs a STRUCTURED measurement record {method, instrument,
         date, reference}; placeholders, negations, model and row references, bare values, fewer
         than 3 letters or digits, invalid or future dates are refused. The gate cannot verify a
         record, only require one (stated in the error).
A10b m1  The a-Si potentials, when labelled PROJECT_INPUT, need the same record.
A10b m2  uncertainty_kind: standard (+- 2 u, about 95 % coverage) | half_width (+- u), required.
A10b m3  amorphous_si_thickness_uncertainty_A is required with the other uncertainties and enters
         the interval.
A10b n2  zero or negative uncertainties are refused.
Decision 6: no code string says that the simulation runs both parities.

Fabricated values that exercise the gate are TEST values of in-memory dictionaries only; the shipped
configuration file is read, never written.
"""
import copy
import datetime as dt
import json
from pathlib import Path

import pytest

from reflection_holo.io.config import MissingProjectInputError, latest_today
from reflection_holo.pipeline import PipelineConfigError, load_pipeline_dict, read_pipeline_file, run
from reflection_holo.pipeline.config import (OXIDE_KEYS_OPTIONAL, OXIDE_RECORDED_PARAMETERS,
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
UNC = dict(thickness_uncertainty_A=1.0, density_uncertainty_g_cm3=0.05,
           amorphous_si_thickness_uncertainty_A=0.1, uncertainty_kind="half_width")
# report X7 (re-audit A12 M1): the method names an id of the allowlist for its parameter
REC = dict(method="offaxis_holography_wedge: TEST: fabricated off-axis electron holography of a "
                  "witness wedge",
           instrument="TEST: fabricated microscope", date="2026-09-20",
           reference="TEST: fabricated laboratory record 1")
REC_BY_PARAMETER = dict(
    V_real=REC,
    V_imag=dict(REC, method="eels_inelastic_mean_free_path: TEST: fabricated EELS log-ratio"),
    vacuum_edge=dict(REC, method="xrr_fit: TEST: fabricated X-ray reflectivity of the witness"),
    interface=dict(REC, method="cross_section_tem_profile: TEST: fabricated STEM profile"))
CANNOT_VERIFY = "the gate cannot verify a measurement record, only require one"


@pytest.fixture(scope="module")
def smoke():
    return read_pipeline_file(SMOKE)


def _variant(smoke, variant="oxide_2p0nm", *, record=None, labels=None, **over):
    d = copy.deepcopy(smoke)
    rec = d["variants"][variant]["cfg_b_parameters"]["surface_preparation_details"]
    rec["value"]["overlayer"].update(over)
    if labels is not None:
        rec["value"]["overlayer"]["labels"] = dict(rec["value"]["overlayer"]["labels"], **labels)
    if record:
        for k in ("stands_in_for_item", "assumption_id"):
            rec.pop(k, None)
        rec.update(record)
    return d


def _measured(smoke, variant="oxide_2p0nm", *, labels=None, **over):
    return _variant(smoke, variant, record=SUPPLY, labels={**MEASURED, **B43, **(labels or {})},
                    **over)


def _refusal(d, variant="oxide_2p0nm", **kw):
    with pytest.raises((PipelineConfigError, MissingProjectInputError)) as exc:
        load_pipeline_dict(d, variant=variant, **kw)
    return str(exc.value)


# --------------------------------------------------------------------------------------------------
# A10b M1: parity variants
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("parity,n,other", [("lower", 6, 7), ("upper", 7, 6)])
def test_each_parity_variant_is_built_and_recorded(smoke, parity, n, other):
    cfg = load_pipeline_dict(_measured(smoke, consumed_layers=n, consumed_layers_parity=parity,
                                       **UNC), variant="oxide_2p0nm")
    spec = oxide_spec_from_config(cfg.cfg_b)
    assert spec.thickness_A == 20.0 and spec.density_g_cm3 == 2.20      # nothing altered
    assert spec.consumed_layers == n
    lab = spec.labels["consumed_layers"]
    assert lab.startswith("DERIVED_HERE (consumed-layer count computed by the code: parity variant "
                          f"{parity} of an interval spanning a boundary: the {parity} count {n} of "
                          f"the item-12 count interval [6, 7]")
    assert f"the other variant ({'upper' if parity == 'lower' else 'lower'}, count {other}) is a " \
           f"separate run; the thickness is not altered" in lab
    assert spec.consumed_layers_parity_variant == dict(UNC, parity=parity)
    rec = oxide_item12_record(cfg.cfg_b)
    pv = rec["consumed_layers"]["parity_variant"]
    assert rec["consumed_layers"]["count"] == n
    assert (pv["variant"], pv["count"], pv["interval_counts"], pv["nearest_count"]) == (
        parity, n, [6, 7], 7)
    assert pv["other_variant"]["count"] == other and pv["thickness_altered"] is False
    assert pv["other_variant_run"].startswith("the other variant is a SEPARATE run")
    assert pv["qualifier"] == f"parity variant {parity} of an interval spanning a boundary"
    assert rec["uncertainties"]["count_interval"]["counts"] == [6, 7]


def test_parity_key_is_required_across_a_boundary_and_refused_otherwise(smoke):
    msg = _refusal(_measured(smoke, **UNC))
    assert "may be any of [6, 7] (even and odd parity" in msg
    assert "consumed_layers_parity is not stated (no default)" in msg
    # 1.5 nm, +-0.5 A, +-0.03 g/cm^3, a-Si +-0.1 A (half-widths): counts [5] (printed by x6)
    unc15 = dict(UNC, thickness_uncertainty_A=0.5, density_uncertainty_g_cm3=0.03)
    out = (REPO / "tools" / "review" / "x6" / "x6_oxide_numbers_output.txt").read_text()
    assert ("t 15.0 +- 0.5 A, rho 2.20 +- 0.03 g/cm^3, a-Si 0.0 +- 0.1 A, half_width: "
            "4.651-5.183 layers") in out
    for parity in ("lower", "upper"):
        msg = _refusal(_measured(smoke, "oxide_1p5nm", consumed_layers_parity=parity, **unc15),
                       "oxide_1p5nm")
        assert "the interval spans no rounding boundary, the count is the nearest count" in msg
    load_pipeline_dict(_measured(smoke, "oxide_1p5nm", **unc15), variant="oxide_1p5nm")


@pytest.mark.parametrize("bad", ["both", "odd", "even", "Lower", "LOWER", " lower", None, 6, True,
                                 ["lower"]])
def test_parity_value_outside_lower_upper_is_refused(smoke, bad):
    msg = _refusal(_measured(smoke, consumed_layers_parity=bad, **UNC))
    assert f"got consumed_layers_parity = {bad!r}" in msg
    assert "State consumed_layers_parity: one of ['lower', 'upper']" in msg


def test_parity_key_without_uncertainties_is_refused(smoke):
    msg = _refusal(_measured(smoke, consumed_layers_parity="upper"))
    assert "without the item-12 uncertainties" in msg


def test_stated_count_must_be_the_variant_count(smoke):
    msg = _refusal(_measured(smoke, consumed_layers=7, consumed_layers_parity="lower", **UNC))
    assert "consumed_layers = 7 is not the lower count 6 of the interval" in msg
    msg = _refusal(_measured(smoke, consumed_layers=6, consumed_layers_parity="upper", **UNC))
    assert "consumed_layers = 6 is not the upper count 7 of the interval" in msg


def test_interval_of_more_than_two_counts_is_refused(smoke):
    """With a-Si 0 +- 0.5 A as a standard uncertainty (report X7: quadrature, re-audit A12 m2), or
    0 +- 1 A as a half-width, the 2.0 nm interval is [6, 7, 8]: lower and upper (6 and 8) share one
    parity and would not cover 7 (printed by tools/review/x7 and x6)."""
    for unc in (dict(UNC, uncertainty_kind="standard", amorphous_si_thickness_uncertainty_A=0.5),
                dict(UNC, amorphous_si_thickness_uncertainty_A=1.0)):
        for parity in ("lower", "upper", None):          # None: the key not stated
            over = dict(unc) if parity is None else dict(unc, consumed_layers_parity=parity)
            msg = _refusal(_measured(smoke, **over))
            assert "may be any of [6, 7, 8]" in msg and "more than one rounding boundary" in msg
            assert "defined for an interval of two counts only" in msg
            assert "State consumed_layers_parity" not in msg


def test_retired_acknowledgement_is_refused(smoke):
    assert "both_parities_acknowledged" not in OXIDE_KEYS_OPTIONAL
    msg = _refusal(_measured(smoke, both_parities_acknowledged=True, consumed_layers_parity="upper",
                             **UNC))
    assert "both_parities_acknowledged is retired by report X6" in msg


def test_run_records_the_parity_variant_in_manifest_and_summary(tmp_path, smoke):
    cfg = load_pipeline_dict(_measured(smoke, consumed_layers=6, consumed_layers_parity="lower",
                                       **UNC), variant="oxide_2p0nm")
    s = run(cfg, tmp_path / "out")
    man = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert s["oxide_item12"] == man["extra"]["oxide_item12"]
    for rec in (man["extra"]["oxide_item12"], s["oxide_item12"]):
        pv = rec["consumed_layers"]["parity_variant"]
        assert (pv["variant"], pv["count"], pv["other_variant"]["count"]) == ("lower", 6, 7)
        assert "SEPARATE run" in pv["other_variant_run"]
        assert rec["uncertainties"]["uncertainty_kind"] == "half_width"
        assert rec["uncertainties"]["count_interval"]["counts"] == [6, 7]
        assert "parity variant lower of an interval spanning a boundary" in rec["labels"][
            "consumed_layers"]
    ov = s["structure"]["options"]["overlayer"]
    assert [p["consumed_layers"] for p in ov["per_terrace"]] == [6] * len(ov["per_terrace"])


# --------------------------------------------------------------------------------------------------
# A10b M2, m1: structured measurement records
# --------------------------------------------------------------------------------------------------
BAD_TEXT = ["?", "-", ".", "x", "...", "measured", "measured.", "Measured!", "measurement",
            "not measured", "not measured: independent-atom model value, E9 out:166",
            "not yet measured", "unmeasured", "unknown", "unknown.", "TBD", "t.b.d.", "tbd", "N/A",
            "n/a", "none", "None.", "todo", "TODO", "to do", "to be supplied", "pending",
            "assumption", "ASSUMPTION B43", "assumed", "model", "model value", "independent-atom",
            "B43", "B41", "nominal", "10.34 V", "0.40 V", "0.5 A", "yes.", "  ", "",
            "simulated", "literature value"]


@pytest.mark.parametrize("field", ["method", "instrument", "reference"])
@pytest.mark.parametrize("bad", BAD_TEXT)
def test_placeholder_record_fields_are_refused(smoke, field, bad):
    d = _measured(smoke, labels=dict(V_real="PROJECT_INPUT"),
                  measurements=dict(V_real=dict(REC, **{field: bad})))
    msg = _refusal(d)
    assert f".V_real.{field} = {bad!r}: must state the {field} of a measurement" in msg
    assert CANNOT_VERIFY in msg


@pytest.mark.parametrize("bad,match", [
    ("2999-01-01", "is in the future relative to the run"),
    ((latest_today() + dt.timedelta(days=1)).isoformat(), "is in the future relative to the run"),
    ("2026-13-01", "is not a valid date"), ("20/09/2026", "must be an ISO date"),
    ("2026-9-20", "must be an ISO date"), ("", "must be an ISO date"), (None, "must be an ISO date"),
    ("TBD", "must be an ISO date"), (dt.datetime(2026, 9, 20, 12, 0), "not a date-time"),
])
def test_record_date_is_an_iso_date_not_in_the_future(smoke, bad, match):
    d = _measured(smoke, labels=dict(V_real="PROJECT_INPUT"),
                  measurements=dict(V_real=dict(REC, date=bad)))
    assert match in _refusal(d)


def test_record_date_may_be_a_yaml_date(smoke):
    d = _measured(smoke, labels=dict(V_real="PROJECT_INPUT"),
                  measurements=dict(V_real=dict(REC, date=dt.date(2026, 9, 20))))
    cfg = load_pipeline_dict(d, variant="oxide_2p0nm")
    assert oxide_item12_record(cfg.cfg_b)["measurements"]["V_real"]["date"] == "2026-09-20"


@pytest.mark.parametrize("rec", [
    "TEST: fabricated off-axis electron holography",                     # X5's free text
    {k: v for k, v in REC.items() if k != "reference"},
    dict(REC, value="10.5 V"), dict(REC, method=12345), {}, None, ["method"]])
def test_record_is_the_structured_mapping(smoke, rec):
    d = _measured(smoke, labels=dict(V_real="PROJECT_INPUT"), measurements=dict(V_real=rec))
    msg = _refusal(d)
    assert ("a measurement record is the mapping {method, instrument, date, reference}" in msg
            or "(a string is required)" in msg)
    assert CANNOT_VERIFY in msg


def test_every_project_input_model_parameter_needs_a_record(smoke):
    labels = {k: "PROJECT_INPUT" for k in ("V_real", "V_imag", "vacuum_edge", "interface")}
    msg = _refusal(_measured(smoke, labels=labels))
    assert "['V_imag', 'V_real', 'interface', 'vacuum_edge'] are labelled PROJECT_INPUT" in msg
    assert CANNOT_VERIFY in msg
    # report X7 (re-audit A12 M1): each parameter's record names a method of its own allowlist
    cfg = load_pipeline_dict(_measured(smoke, labels=labels, measurements=REC_BY_PARAMETER),
                             variant="oxide_2p0nm")
    spec = oxide_spec_from_config(cfg.cfg_b)
    for k in labels:
        text = (f"measured: method {REC_BY_PARAMETER[k]['method']}; instrument TEST: fabricated "
                f"microscope; date 2026-09-20; reference TEST: fabricated laboratory record 1)")
        assert spec.labels[k].endswith(text), k
    assert spec.labels["V_real"].endswith(
        "measured: method offaxis_holography_wedge: TEST: fabricated off-axis electron holography "
        "of a witness wedge; instrument TEST: fabricated microscope; date 2026-09-20; reference "
        "TEST: fabricated laboratory record 1)")
    rec = oxide_item12_record(cfg.cfg_b)
    assert rec["measurements"] == REC_BY_PARAMETER
    assert CANNOT_VERIFY in rec["measurement_rule"]


def _asi(smoke, **over):
    """2.0 nm oxide over 5 A of a-Si (TEST): count 10 (depth 10.19 layers, margin 0.31 layer)."""
    return _measured(smoke, amorphous_si_thickness_A=5.0, amorphous_si_V_real_V=12.0,
                     amorphous_si_V_imag_V=0.5, consumed_layers=10,
                     rounding_boundary_acknowledged=False,
                     labels=dict(amorphous_si_potential="PROJECT_INPUT"), **over)


def test_amorphous_si_potentials_need_a_record(smoke):
    assert "amorphous_si_potential" in OXIDE_RECORDED_PARAMETERS
    msg = _refusal(_asi(smoke))
    assert "['amorphous_si_potential'] are labelled PROJECT_INPUT, so each needs a measurement " \
           "record" in msg
    msg = _refusal(_asi(smoke, measurements=dict(amorphous_si_potential=dict(
        REC, method="not measured: 12.0 V is the crystal's value"))))
    assert "must state the method of a measurement" in msg
    cfg = load_pipeline_dict(_asi(smoke, measurements=dict(amorphous_si_potential=REC)),
                             variant="oxide_2p0nm")
    lab = oxide_spec_from_config(cfg.cfg_b).labels["amorphous_si_potential"]
    assert lab.startswith("PROJECT_INPUT item 12 (TEST: fabricated supply to exercise the gate; "
                          "measured: method ")


def test_comparison_with_a_si_potentials_needs_the_record(smoke):
    unc = dict(UNC, thickness_uncertainty_A=0.2, density_uncertainty_g_cm3=0.01)
    d = _asi(smoke, **unc)
    d["purpose"] = "comparison"
    assert "needs a measurement record" in _refusal(d)
    d = _asi(smoke, measurements=dict(amorphous_si_potential=REC), **unc)
    d["purpose"] = "comparison"
    msg = _refusal(d)                   # refused for the demo's OTHER stand-ins only
    assert "purpose 'comparison' refuses every demo stand-in" in msg and "overlayer" not in msg


# --------------------------------------------------------------------------------------------------
# A10b m2, m3, n2: uncertainties
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("missing", ["amorphous_si_thickness_uncertainty_A", "uncertainty_kind"])
def test_new_uncertainty_keys_are_required_with_the_others(smoke, missing):
    unc = {k: v for k, v in UNC.items() if k != missing}
    assert "state all of" in _refusal(_measured(smoke, consumed_layers_parity="upper", **unc))
    d = _measured(smoke, consumed_layers_parity="upper", **unc)
    d["purpose"] = "comparison"
    assert "state all of" in _refusal(d)
    d = _measured(smoke)
    d["purpose"] = "comparison"
    msg = _refusal(d)
    assert "needs the item-12 uncertainties" in msg and "uncertainty_kind" in msg
    assert "amorphous_si_thickness_uncertainty_A" in msg


@pytest.mark.parametrize("bad", ["sigma", "Standard", "", None, 2, "95 %"])
def test_uncertainty_kind_is_enumerated(smoke, bad):
    msg = _refusal(_measured(smoke, consumed_layers_parity="upper",
                             **dict(UNC, uncertainty_kind=bad)))
    assert "uncertainty_kind must be one of ['standard', 'half_width']" in msg
    assert "about 95 % coverage" in msg


def test_standard_uncertainty_enters_twice(smoke):
    # +-0.1 A, +-0.01 g/cm^3, a-Si +-0.1 A as standard uncertainties: [6, 7]; report X7 (re-audit
    # A12 m2): combined in quadrature, 6.416-6.675 layers (X6's box: 6.380-6.776; both printed by
    # tools/review/x7)
    unc = dict(UNC, thickness_uncertainty_A=0.1, density_uncertainty_g_cm3=0.01,
               uncertainty_kind="standard")
    cfg = load_pipeline_dict(_measured(smoke, consumed_layers_parity="upper", **unc),
                             variant="oxide_2p0nm")
    ci = oxide_item12_record(cfg.cfg_b)["uncertainties"]["count_interval"]
    assert ci["coverage_factor"] == 2.0 and ci["box"]["thickness_A"] == [19.8, 20.2]
    assert ci["box"]["amorphous_si_thickness_A"] == [0.0, 0.2]
    assert f"{ci['continuum_layers_min']:.3f}-{ci['continuum_layers_max']:.3f}" == "6.416-6.675"
    out = (REPO / "tools" / "review" / "x7" / "x7_oxide_numbers_output.txt").read_text()
    assert ("t 20.0 +- 0.1 A, rho 2.20 +- 0.01 g/cm^3, a-Si 0.0 +- 0.1 A, standard: 6.416-6.675 "
            "layers") in out and "before (X6 box) 6.380-6.776 -> [6, 7]" in out
    # re-audit A12 n2: the kind handed to the structure is the stated kind (k = 2 there as well)
    spec = oxide_spec_from_config(cfg.cfg_b)
    assert spec.consumed_layers_parity_variant["uncertainty_kind"] == "standard"


@pytest.mark.parametrize("key", ["thickness_uncertainty_A", "density_uncertainty_g_cm3",
                                 "amorphous_si_thickness_uncertainty_A"])
@pytest.mark.parametrize("bad", [0.0, -0.05])
def test_zero_or_negative_uncertainty_is_refused(smoke, key, bad):
    msg = _refusal(_measured(smoke, consumed_layers_parity="upper", **dict(UNC, **{key: bad})))
    assert f"{key} (item 12; zero or negative refused, re-audit A10b n2) must be > 0" in msg


def test_amorphous_si_uncertainty_under_a_stand_in_is_refused(smoke):
    d = _variant(smoke, record=SUPPLY, labels=dict(MEASURED, **B43, amorphous_si="ASSUMPTION B41"),
                 consumed_layers_parity="upper", **UNC)
    assert "['amorphous_si'] are stand-ins whose rows state no uncertainty" in _refusal(d)


# --------------------------------------------------------------------------------------------------
# Decision 6: no code string claims that both parities are run
# --------------------------------------------------------------------------------------------------
def test_no_code_string_claims_both_parities_are_run():
    pkg = Path(ox.__file__).resolve().parents[1]
    for p in pkg.rglob("*.py"):
        text = " ".join(p.read_text().split()).lower()
        for s in ("runs both parities", "both parities must then be run",
                  "both parities are acknowledged", "unless both parities"):
            assert s not in text, (p, s)
