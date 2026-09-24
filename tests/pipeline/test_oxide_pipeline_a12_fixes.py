"""Pipeline gate of the continuum oxide: the fixes of report X7 after the re-audit A12 (item 12).

A12 M1  The measurement record of a PROJECT_INPUT model parameter: the method must name an id of the
        ALLOWLIST MEASUREMENT_METHODS that measures that parameter ("<id>" or "<id>: <details>";
        other_measurement only with a description of at least MEASUREMENT_OTHER_MIN_WORDS distinct
        words; ellipsometry is not a width method). Second layer: every text field is
        NFKC-normalised and must be printable ASCII, and the broadened refusal list (negations,
        placeholders, origin words of unmeasured values, row, report and repository references;
        case- and whitespace-insensitive) refuses the texts that re-audit A12 found accepted.
A12 m1  The reference needs a token beyond a scheme or prefix (a DOI with its suffix, a URL with a
        host) and must not point into this repository; the date lies between 1990-01-01 and the
        item-12 supply date. Every error states that the gate cannot verify a record, only require
        one.
A12 m2  Standard uncertainties are combined in quadrature: A12's example (1 A, 0.05 g/cm^3, 0.1 A)
        gives [6, 7] and runs as a parity variant (X6's box gave [6, 7, 8] and refused it).
A12 n1  An absurd uncertainty is a configuration error naming the bound, never an uncaught
        OverflowError or MemoryError.
A12 m3  The item-12 record names the parity variant whose count is the nearest; in the geometric
        engine the two variants give byte-identical arrays (the multislice comparison is printed by
        tools/review/x7/x7_parity_variants.py).

Fabricated values that exercise the gate are TEST values of in-memory dictionaries only; the shipped
configuration file is read, never written. The gate cannot verify a record: a fabricated but
well-formed record passes (the TEST records below).
"""
import copy
import datetime as dt

import numpy as np
import pytest

from reflection_holo.io.config import MissingProjectInputError
from reflection_holo.pipeline import PipelineConfigError, load_pipeline_dict, read_pipeline_file, run
from reflection_holo.pipeline import config as pc
from reflection_holo.pipeline.config import (MEASUREMENT_METHODS, MEASUREMENT_OTHER_MIN_WORDS,
                                             allowed_measurement_methods, oxide_item12_record,
                                             oxide_spec_from_config)
from reflection_holo.structure import oxide as ox

from conftest_pipeline import REPO, SMOKE

SUPPLY = dict(label="PROJECT_INPUT", supplied_by="Auditor", supplied_on="2026-09-24",
              source="TEST: fabricated supply to exercise the gate")
MEASURED = dict(thickness="PROJECT_INPUT", density="PROJECT_INPUT", amorphous_si="PROJECT_INPUT",
                consumed_layers="DERIVED_HERE")
B43 = {k: "ASSUMPTION B43" for k in ("V_real", "V_imag", "vacuum_edge", "interface")}
UNC = dict(thickness_uncertainty_A=1.0, density_uncertainty_g_cm3=0.05,
           amorphous_si_thickness_uncertainty_A=0.1, uncertainty_kind="half_width")
REC = dict(method="offaxis_holography_wedge: TEST: fabricated holography of a witness wedge",
           instrument="TEST: fabricated microscope", date="2026-09-20",
           reference="TEST: fabricated laboratory record 1")
CANNOT_VERIFY = "the gate cannot verify a measurement record, only require one"
OTHER_DETAILS = ("TEST: fabricated phase shift across a cleaved witness corner of known angle and "
                 "thickness")
PARAMETERS = ("V_real", "V_imag", "vacuum_edge", "interface", "amorphous_si_potential")


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


def _with_record(smoke, parameter, rec):
    """One PROJECT_INPUT parameter with the record ``rec``; the others under B43. For the a-Si
    potentials: 2.0 nm oxide over 5 A of a-Si (TEST), count 10."""
    if parameter == "amorphous_si_potential":
        return _measured(smoke, amorphous_si_thickness_A=5.0, amorphous_si_V_real_V=12.0,
                         amorphous_si_V_imag_V=0.5, consumed_layers=10,
                         rounding_boundary_acknowledged=False,
                         labels=dict(amorphous_si_potential="PROJECT_INPUT"),
                         measurements=dict(amorphous_si_potential=rec))
    return _measured(smoke, labels={parameter: "PROJECT_INPUT"}, measurements={parameter: rec})


def _refusal(d, variant="oxide_2p0nm", **kw):
    with pytest.raises((PipelineConfigError, MissingProjectInputError)) as exc:
        load_pipeline_dict(d, variant=variant, **kw)
    return str(exc.value)


def _method(mid):
    return f"{mid}: {OTHER_DETAILS}" if mid == pc.MEASUREMENT_OTHER else f"{mid}: TEST: fabricated"


# --------------------------------------------------------------------------------------------------
# A12 M1: the allowlist
# --------------------------------------------------------------------------------------------------
def test_the_allowlist_is_the_decided_table():
    table = {k: set(v[0]) for k, v in MEASUREMENT_METHODS.items()}
    mean_inner = {"V_real", "amorphous_si_potential"}
    assert table == {
        "offaxis_holography_wedge": mean_inner, "other_measurement": mean_inner,
        "eels_inelastic_mean_free_path": {"V_imag"}, "eftem_log_ratio_oxide_film": {"V_imag"},
        "xrr_fit": {"vacuum_edge", "interface"},
        "cross_section_tem_profile": {"vacuum_edge", "interface"}, "afm_surface": {"vacuum_edge"}}
    doc = " ".join(allowed_measurement_methods.__doc__.split())
    assert all(mid in doc for mid in MEASUREMENT_METHODS)
    assert "ellipsometry is NOT a width method" in doc and "cannot verify a record" in doc
    assert not any(any(s in m for s in pc.MEASUREMENT_NOT_A_WIDTH_METHOD) for m in MEASUREMENT_METHODS)
    assert allowed_measurement_methods("interface") == ["cross_section_tem_profile", "xrr_fit"]
    # re-audit A13 M1: no rocking-curve id (they measure the crystal's potential, not an amorphous
    # layer's) and no reflection or whole-stack intensity ratio for the oxide's absorption
    assert not any("rocking" in m for m in MEASUREMENT_METHODS)
    assert allowed_measurement_methods("V_real") == ["offaxis_holography_wedge", "other_measurement"]
    assert allowed_measurement_methods("V_imag") == ["eels_inelastic_mean_free_path",
                                                     "eftem_log_ratio_oxide_film"]
    assert "not a reflection ratio" in MEASUREMENT_METHODS["eftem_log_ratio_oxide_film"][1]


@pytest.mark.parametrize("parameter", PARAMETERS)
@pytest.mark.parametrize("mid", sorted(MEASUREMENT_METHODS))
def test_each_method_id_measures_only_its_parameters(smoke, mid, parameter):
    d = _with_record(smoke, parameter, dict(REC, method=_method(mid)))
    if parameter in MEASUREMENT_METHODS[mid][0]:
        cfg = load_pipeline_dict(d, variant="oxide_2p0nm")
        rec = oxide_item12_record(cfg.cfg_b)["measurements"][parameter]
        assert rec["method"] == _method(mid)
        assert oxide_spec_from_config(cfg.cfg_b).labels[parameter].startswith(
            f"PROJECT_INPUT item 12 (TEST: fabricated supply to exercise the gate; measured: "
            f"method {_method(mid)}; instrument")
    else:
        msg = _refusal(d)
        assert f"with an id of the allowlist MEASUREMENT_METHODS that measures {parameter}: " \
               f"{allowed_measurement_methods(parameter)}" in msg
        assert f"{mid} ({MEASUREMENT_METHODS[mid][1]}) measures only" in msg
        assert CANNOT_VERIFY in msg


@pytest.mark.parametrize("method", [
    "estimated", "TEST: fabricated off-axis electron holography of a witness wedge", "XRR",
    "xrr fit", "XRR_FIT", "xrr_fit2", "holography", "offaxis_holography", "abc", "test",
    "Doyle-Turner scattering factors", "fitted", "offaxis_holography_wedge; TEST: fabricated",
    "other"])
def test_the_method_must_name_an_id(smoke, method):
    msg = _refusal(_with_record(smoke, "V_real", dict(REC, method=method)))
    assert f".V_real.method = {method!r}: must state the method of a measurement" in msg
    assert CANNOT_VERIFY in msg


def test_other_measurement_needs_a_description(smoke):
    ok = _with_record(smoke, "V_real", dict(REC, method=f"other_measurement: {OTHER_DETAILS}"))
    load_pipeline_dict(ok, variant="oxide_2p0nm")
    words = "phase shift across cleaved witness corner known"                # 7 distinct words
    for details in ("", words, words + " " + words, "a b c d e f g h i j k l",
                    "phase phase phase phase phase phase phase phase"):
        msg = _refusal(_with_record(smoke, "V_real", dict(REC, method=f"other_measurement: "
                                                                        f"{details}")))
        assert (f"needs a description of the measurement after the id of at least "
                f"{MEASUREMENT_OTHER_MIN_WORDS} distinct words" in msg), details
    load_pipeline_dict(_with_record(smoke, "V_real", dict(REC, method="other_measurement: "
                                                          + words + " of a wedge")),     # 8
                       variant="oxide_2p0nm")
    # the description passes the refusal list as well
    msg = _refusal(_with_record(smoke, "V_real", dict(
        REC, method=f"other_measurement: {OTHER_DETAILS}, estimated from a model")))
    assert "it contains 'estimat'" in msg


def test_ellipsometry_is_not_a_width_method(smoke):
    for parameter, mid in (("vacuum_edge", "xrr_fit"), ("interface", "cross_section_tem_profile"),
                           ("vacuum_edge", "afm_surface")):
        msg = _refusal(_with_record(smoke, parameter, dict(
            REC, method=f"{mid}: TEST: fabricated, combined with spectroscopic ellipsometry")))
        assert "ellipsometry is not a width method" in msg and CANNOT_VERIFY in msg
    # ellipsometry may enter the description of a mean-inner-potential measurement (the thickness)
    load_pipeline_dict(_with_record(smoke, "V_real", dict(
        REC, method="offaxis_holography_wedge: TEST: wedge thickness by ellipsometry")),
        variant="oxide_2p0nm")


# --------------------------------------------------------------------------------------------------
# A12 M1, m1: the second layer (the texts re-audit A12 found accepted, D1)
# --------------------------------------------------------------------------------------------------
A12_REFUSED_EVERYWHERE = [
    # other spellings and phrasings of a non-measurement
    "not yet been measured", "has not yet been measured", "no measurements", "no measurements made",
    "no measurements available", "wasn't measured", "was not actually measured", "not_measured",
    "not-measured", "notmeasured", "un-measured", "non-measured", "never been measured",
    "measured: no", "measured - no", "missing", "absent", "undefined", "NaN", "nan value", "blank",
    "empty", "anything", "whatever", "FIXME", "fill in later", "later", "aaa", "zzz",
    "lorem ipsum", "sample text",
    # the origin of an unmeasured value stated plainly
    "estimated", "estimate", "guess", "educated guess", "typical value", "textbook value",
    "handbook value (CRC)", "Wikipedia", "taken from a paper", "value from Ref. 12", "extrapolated",
    "interpolated", "fitted", "DFT", "density functional theory", "ab initio", "first principles",
    "computed", "derived", "DERIVED_HERE", "ESTIMATE", "TEST_ONLY",
    "Doyle-Turner scattering factors", "Weickenmeier-Kohl", "Lobato parametrisation",
    "tools/review/e9_recompute_output.txt line 166", "E9 out:166", "row B-43", "row B 43",
    "same as B7", "B1234", "copied from the demo configuration", "demo value",
    # the orchestrator's list (re-audit A12 M1 decision)
    "calculated", "simulated", "scattering factors", "literature", "assumed", "model",
    # other languages
    "nicht gemessen", "non mesure", "non mesuré", "no medido", "non misurato", "niet gemeten",
    "未測定", "не измерено", "не измерено (n/m)", "sans mesure",
    # look-alikes and invisible characters (NFKC, then printable ASCII only)
    "nоt measured", "not mеasured", "not​measured", "not­measured", "not measured",
    "not measured", "ТBD later", "ＴＢＤ", "Β43 value", "unmeasur3d",
    # case and whitespace
    "NOT   MEASURED", "Not\tMeasured", "nOt_MeAsUrEd", "  measured  ", "\tTBD\n", " not measured ",
    "m e a s u r e d", "   ?   ",
]


@pytest.mark.parametrize("field", ["method", "instrument", "reference"])
@pytest.mark.parametrize("text", A12_REFUSED_EVERYWHERE)
def test_a12_texts_are_refused_in_every_field(smoke, field, text):
    value = f"offaxis_holography_wedge: {text}" if field == "method" else text
    msg = _refusal(_with_record(smoke, "V_real", dict(REC, **{field: value})))
    assert f".V_real.{field} = {value!r}: must state the {field} of a measurement" in msg
    assert CANNOT_VERIFY in msg


@pytest.mark.parametrize("field", ["instrument", "reference"])
@pytest.mark.parametrize("text", ["method", "Instrument", "reference", "record", "date", "value",
                                  "fit", "internal", "notebook", "report", "sample text"])
def test_field_name_echoes_are_refused(smoke, field, text):
    """re-audit A12 m1: echoes of the field names (and similar words) are placeholders."""
    msg = _refusal(_with_record(smoke, "V_real", dict(REC, **{field: text})))
    assert f".V_real.{field} = {text!r}: must state" in msg
    assert "(a placeholder)" in msg


@pytest.mark.parametrize("text,char", [
    ("nоt measured", "U+043E CYRILLIC SMALL LETTER O"), ("not​measured", "U+200B ZERO WIDTH SPACE"),
    ("not­measured", "U+00AD SOFT HYPHEN"), ("Β43 value", "U+0392 GREEK CAPITAL LETTER BETA"),
    ("non mesuré", "U+00E9 LATIN SMALL LETTER E WITH ACUTE")])
def test_non_ascii_after_nfkc_is_refused_by_name(smoke, text, char):
    msg = _refusal(_with_record(smoke, "V_real", dict(REC, instrument=text)))
    assert "after NFKC normalisation it contains characters that are not printable ASCII" in msg
    assert char in msg


def test_nfkc_and_whitespace_normalise_a_genuine_record(smoke):
    """NFKC maps compatibility characters (no-break space, fullwidth letters, ligatures) to ASCII,
    so a genuine record written with them is accepted and stored normalised; runs of whitespace are
    collapsed."""
    rec = dict(REC, instrument="  TEST: fabricated   ＴＥＭ\tmicroscope  ",
               reference="TEST: fabricated laboratory record 1 (ﬁle 7)")
    cfg = load_pipeline_dict(_with_record(smoke, "V_real", rec), variant="oxide_2p0nm")
    got = oxide_item12_record(cfg.cfg_b)["measurements"]["V_real"]
    assert got["instrument"] == "TEST: fabricated TEM microscope"
    assert got["reference"] == "TEST: fabricated laboratory record 1 (file 7)"


@pytest.mark.parametrize("ref", [
    "ref:", "Ref. ", "doi:", "doi:10.", "doi:10.1234", "https://doi.org/", "http://", "file:///",
    "http://localhost/x", "No. 1", "ref [1]", "lab book p.", "internal", "record", "reference",
    "method", "instrument", "see notebook", "same as above", "as above", "cf. method",
    "tools/review/e9_recompute_output.txt line 166", "docs/model_assumptions.md row B43",
    "reflection_holo/pipeline/config.py", "/home/user/Holography/docs/06_project_inputs_required.md",
    "see ./tools/review/x6/x6_oxide_numbers_output.txt", "configs/demo_smoke_si001.yaml",
    "outputs/run1/manifest.json", "Holography/tests/pipeline"])
def test_empty_or_repository_references_are_refused(smoke, ref):
    msg = _refusal(_with_record(smoke, "V_real", dict(REC, reference=ref)))
    assert f".V_real.reference = {ref!r}: must state" in msg and CANNOT_VERIFY in msg


@pytest.mark.parametrize("ref", [
    "doi:10.1016/j.ultramic.2020.113096", "https://doi.org/10.1016/j.ultramic.2020.113096",
    "https://lab.example.org/xrr/witness-2026", "#123", "lab notebook LN-17 p. 34",
    "Phys. Rev. B 45, 1234 (1992)", "TEST: fabricated laboratory record 1"])
def test_locating_references_are_accepted(smoke, ref):
    cfg = load_pipeline_dict(_with_record(smoke, "V_real", dict(REC, reference=ref)),
                             variant="oxide_2p0nm")
    assert oxide_item12_record(cfg.cfg_b)["measurements"]["V_real"]["reference"] == ref


@pytest.mark.parametrize("date,match", [
    ("0001-01-01", "before the stated floor 1990-01-01"),
    (dt.date(1, 1, 1), "before the stated floor 1990-01-01"),
    ("1900-01-01", "before the stated floor 1990-01-01"),
    ("1989-12-31", "before the stated floor 1990-01-01"),
    ("2026-09-25", "after the item-12 supply date supplied_on = 2026-09-24"),
    ("2999-01-01", "is in the future relative to the run"),
])
def test_record_date_between_the_floor_and_the_supply_date(smoke, date, match):
    msg = _refusal(_with_record(smoke, "V_real", dict(REC, date=date)))
    assert match in msg and CANNOT_VERIFY in msg


@pytest.mark.parametrize("date", ["1990-01-01", "2026-09-24", dt.date(2026, 9, 24)])
def test_record_dates_at_the_bounds_are_accepted(smoke, date):
    cfg = load_pipeline_dict(_with_record(smoke, "V_real", dict(REC, date=date)),
                             variant="oxide_2p0nm")
    assert oxide_item12_record(cfg.cfg_b)["measurements"]["V_real"]["date"] == str(date)


def test_every_record_error_states_that_the_gate_cannot_verify(smoke):
    cases = [dict(REC, method="xrr_fit"), dict(REC, method="abc"), dict(REC, instrument="DFT"),
             dict(REC, reference="doi:"), dict(REC, date="1989-01-01"),
             dict(REC, date="2026-09-25"), dict(REC, date="20/09/2026"),
             dict(REC, date=dt.datetime(2026, 9, 20, 12, 0)), dict(REC, date="2026-02-30"),
             {k: v for k, v in REC.items() if k != "date"}, dict(REC, instrument="nоt")]
    for rec in cases:
        assert CANNOT_VERIFY in _refusal(_with_record(smoke, "V_real", rec)), rec
    assert CANNOT_VERIFY in _refusal(_measured(smoke, labels=dict(V_real="PROJECT_INPUT")))
    assert CANNOT_VERIFY in _refusal(_measured(smoke, labels=dict(V_real="PROJECT_INPUT"),
                                               measurements=dict(V_real=REC, V_imag=REC)))


def test_the_record_rule_names_the_allowlist(smoke):
    cfg = load_pipeline_dict(_measured(smoke), variant="oxide_2p0nm")
    rule = oxide_item12_record(cfg.cfg_b)["measurement_rule"]
    for k in PARAMETERS:
        assert f"{k}: {allowed_measurement_methods(k)}" in rule
    assert CANNOT_VERIFY in rule


# --------------------------------------------------------------------------------------------------
# A12 m2: quadrature; A12 n1: bounds
# --------------------------------------------------------------------------------------------------
A12_EXAMPLE = dict(thickness_uncertainty_A=1.0, density_uncertainty_g_cm3=0.05,
                   amorphous_si_thickness_uncertainty_A=0.1, uncertainty_kind="standard")


def test_a12_example_runs_as_a_parity_variant(smoke):
    """1 A, 0.05 g/cm^3, 0.1 A as standard uncertainties: X6's box gave [6, 7, 8] and refused the
    record; in quadrature the interval is 5.789-7.233 layers, [6, 7] (printed by tools/review/x7)."""
    out = (REPO / "tools" / "review" / "x7" / "x7_oxide_numbers_output.txt").read_text()
    assert "5.587-7.626 layers -> counts [6, 7, 8] (refused: more than two counts)" in out
    assert "5.789-7.233 layers (half-widths -0.7144 / +0.7294 layer) -> counts [6, 7]" in out
    for parity, n in (("lower", 6), ("upper", 7)):
        cfg = load_pipeline_dict(_measured(smoke, consumed_layers=n, consumed_layers_parity=parity,
                                           **A12_EXAMPLE), variant="oxide_2p0nm")
        ci = oxide_item12_record(cfg.cfg_b)["uncertainties"]["count_interval"]
        assert ci["counts"] == [6, 7] and ci["combination"].startswith("quadrature")
        assert f"{ci['continuum_layers_min']:.3f}-{ci['continuum_layers_max']:.3f}" == "5.789-7.233"
        spec = oxide_spec_from_config(cfg.cfg_b)
        assert spec.consumed_layers == n
        assert spec.consumed_layers_parity_variant["uncertainty_kind"] == "standard"
    d = _measured(smoke, consumed_layers=7, consumed_layers_parity="upper", **A12_EXAMPLE)
    d["purpose"] = "comparison"
    msg = _refusal(d)                   # refused for the demo's OTHER stand-ins only
    assert "purpose 'comparison' refuses every demo stand-in" in msg and "overlayer" not in msg


@pytest.mark.parametrize("key,value,unit,bound", [
    ("amorphous_si_thickness_uncertainty_A", 5.0, "A", "2.715 A"),
    ("amorphous_si_thickness_uncertainty_A", 1e9, "A", "2.715 A"),
    ("amorphous_si_thickness_uncertainty_A", 1e300, "A", "2.715 A"),
    ("amorphous_si_thickness_uncertainty_A", 1.7e308, "A", "2.715 A"),
    ("thickness_uncertainty_A", 7.0, "A", "6.15 A"),
    ("density_uncertainty_g_cm3", 0.7, "g/cm^3", "0.6765 g/cm^3")])
def test_absurd_uncertainties_are_configuration_errors_naming_the_bound(smoke, key, value, unit,
                                                                         bound):
    msg = _refusal(_measured(smoke, consumed_layers_parity="upper", **dict(UNC, **{key: value})))
    assert f"{key} = {value} {unit} (half_width): its interval half-width moves the continuum " \
           f"depth by" in msg
    assert f"the upper bound of this uncertainty here is {bound}" in msg
    assert ox.UNCERTAINTY_BOUND_STATEMENT in msg


@pytest.mark.parametrize("exc", [OverflowError, MemoryError])
def test_overflow_and_memory_errors_become_configuration_errors(smoke, monkeypatch, exc):
    def boom(**kw):
        raise exc("TEST")
    monkeypatch.setattr(ox, "item12_count_interval", boom)
    msg = _refusal(_measured(smoke, consumed_layers_parity="upper", **UNC))
    assert f"too large to form a count interval ({exc.__name__})" in msg
    assert ox.UNCERTAINTY_BOUND_STATEMENT in msg


# --------------------------------------------------------------------------------------------------
# A12 m3: the nearest variant; the geometric engine does not distinguish the variants
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("parity,n", [("lower", 6), ("upper", 7)])
def test_record_names_the_nearest_count_variant(smoke, parity, n):
    cfg = load_pipeline_dict(_measured(smoke, consumed_layers=n, consumed_layers_parity=parity,
                                       **UNC), variant="oxide_2p0nm")
    cl = oxide_item12_record(cfg.cfg_b)["consumed_layers"]
    pv = cl["parity_variant"]
    assert pv["nearest_count"] == 7 and pv["nearest_count_variant"] == "upper"
    assert pv["is_nearest_count"] is (parity == "upper")
    assert "Only the multislice engine distinguishes the variants" in cl["note"]
    assert "at most 1.5 a/4" in cl["note"] and "an effect not computed" in cl["note"]


def test_geometric_engine_gives_byte_identical_variants(tmp_path, smoke):
    """re-audit A12 D6, reproduced: the geometric engine's layer phase uses the continuum
    boundaries, so the lower (6) and upper (7) variants of the 2.0 nm record give the same arrays
    byte for byte (the multislice arrays differ: tools/review/x7/x7_parity_variants_output.txt)."""
    arrays = {}
    for parity, n in (("lower", 6), ("upper", 7)):
        cfg = load_pipeline_dict(_measured(smoke, consumed_layers=n, consumed_layers_parity=parity,
                                           **UNC), variant="oxide_2p0nm")
        s = run(cfg, tmp_path / parity)
        ov = s["structure"]["options"]["overlayer"]
        assert {p["consumed_layers"] for p in ov["per_terrace"]} == {n}
        arrays[parity] = np.load(tmp_path / parity / "arrays.npz")
    a, b = arrays["lower"], arrays["upper"]
    assert sorted(a.files) == sorted(b.files) and len(a.files) == 26
    for k in a.files:
        assert a[k].dtype == b[k].dtype and a[k].shape == b[k].shape, k
        assert a[k].tobytes() == b[k].tobytes(), k
    out = (REPO / "tools" / "review" / "x7" / "x7_parity_variants_output.txt").read_text()
    assert "geometric oxide_2p0nm lower (6) vs upper (7): 26 arrays; byte-identical 26" in out

