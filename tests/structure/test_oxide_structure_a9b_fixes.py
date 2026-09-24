"""Continuum oxide: the fixes of report X5 after the audit A9b of report X4 (structure level).

A9b M1  The engines disagree for a non-conformal layer on an atomistic crystal (whole-layer
        consumption: the multislice crystal does not move for a sub-layer thickness difference;
        the geometric engine applies the continuum grown-oxide rate). Stated with its size in
        oxide.NOT_REPRESENTED, si001.B4_OXIDE_GROWN and the per-step record of every non-conformal
        step; the TEST_ONLY acknowledgement nonconformal_sublayer_acknowledged is checked by the
        spec (the refusal of the cell: tests/forward/test_oxide_multislice_a9b_fixes.py).
A9b M2  consumed_layers is DERIVED_HERE (TEST_ONLY in tests), never PROJECT_INPUT or ASSUMPTION.
A9b n1  the record's headline label lists mixed labels ("mixed (...)"), never PROJECT_INPUT alone
        while some parameter is not one.
A9b m2  the 0.05-layer margin is stated as an arbitrary numerical guard; consumed_count_interval
        gives the counts over an item-12 uncertainty box.
A9b m3, m4  the quoted numbers are the digits printed by the committed scripts in tools/review/x5/
        (asserted against their saved outputs, so that code strings and prints cannot diverge).

Every value standing in for PROJECT_INPUT item 12 is TEST_ONLY; reference numbers are the saved
outputs of tools/review/x5/ (A9b's C2, C3, C4 and X5's numbers script).
"""
import re
from pathlib import Path

import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import Staircase, build_si001_terraces
from reflection_holo.structure import oxide as ox
from reflection_holo.structure.si001 import B4_OXIDE_GROWN

L12 = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (continuum oxide)"
Q = A_SI_A / 4
REVIEW = Path(__file__).resolve().parents[2] / "tools" / "review" / "x5"


def spec(*, labels=None, **kw):
    lab = {k: L12 for k in ox.LABEL_KEYS}
    if kw.get("terrace_thickness_A") is not None or kw.get("terrace_consumed_layers") is not None:
        lab["overrides"] = L12
    lab.update(labels or {})
    base = dict(material="amorphous SiO2", thickness_A=20.0, density_g_cm3=2.20, consumed_layers=7,
                V_real_V=10.34, V_imag_V=0.40, vacuum_edge_width_A=0.5, interface_width_A=0.5,
                amorphous_si_thickness_A=0.0, amorphous_si_V_real_V=None,
                amorphous_si_V_imag_V=None, terrace_thickness_A=None, terrace_consumed_layers=None,
                sharp_edge_test_flag=False, sharp_interface_test_flag=False,
                rounding_boundary_acknowledged=True, nonconformal_sublayer_acknowledged=False,
                consumed_layers_parity_variant=None,          # re-audit A10b M1 (stated)
                labels=lab)
    base.update(kw)
    return ox.ContinuumOxideSpec(**base)


def build(s):
    st = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(3, 3, 3),
                   boundary_step_layers=-1)
    return build_si001_terraces(
        azimuth_uvw=(1, 0, 0), azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
        staircase=st, edge_periods=2, substrate_layers=14, first_terrace_backbond_uvw=(1, 1, 0),
        termination="bulk", overlayer=s, vacuum_above_A=20.0, lattice_parameter_A=A_SI_A,
        lattice_parameter_label="ASSUMPTION B2")


def _quote(name: str, pattern: str) -> list[str]:
    """The groups of ``pattern`` in the saved output of a committed tools/review/x5 script."""
    text = (REVIEW / f"{name}_output.txt").read_text()
    m = re.search(pattern, text)
    assert m, (name, pattern)
    return list(m.groups())


# --------------------------------------------------------------------------------------------------
# A9b M1: the non-conformal disagreement is stated with its size
# --------------------------------------------------------------------------------------------------
def test_nonconformal_disagreement_is_stated_with_the_printed_numbers():
    g, lo, hi = _quote("a9b_c4_nonconformal",
                       r"geometric grown-oxide rate (\d\.\d{4}) rad/A.*\n(?:.*\n)*?.*range "
                       r"(\d\.\d\d)-(\d\.\d\d) rad per A of sub-layer")
    slopes = _quote("a9b_c4_nonconformal", r"slopes at a fixed consumed-layer count: "
                                           r"([\d.]+), ([\d.]+), ([\d.]+) rad/A")
    layer, top = _quote("a9b_c4_nonconformal", r"one consumed layer ([\d.]+) rad.*\n")[0], \
        _quote("a9b_c4_nonconformal", r"\(= (\d\.\d{3})\); geometric")[0]
    for text in (ox.NONCONFORMAL_SUBLAYER, ox.NOT_REPRESENTED, B4_OXIDE_GROWN):
        assert f"{g} rad/A" in text and f"{lo}-{hi} rad per A of sub-layer" in text
        assert all(s in text for s in slopes) and f"{top} rad/A" in text
        assert f"{layer} rad" in text
    assert ox.SUBLAYER_RATE_DIFFERENCE_RAD_PER_A == (float(lo), float(hi))
    assert "sub-layer thickness difference" in ox.NOT_REPRESENTED


def test_every_nonconformal_step_records_the_sublayer_size():
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    lab = dict(overrides=L12)
    # terrace 1 carries 0.5 A more oxide at the same count (7): a sub-layer difference of 0.5 A
    s = build(spec(terrace_thickness_A=(20.0, 20.5, 20.0), terrace_consumed_layers=(7, 7, 7),
                   labels=lab))
    steps = {x["index"]: x["overlayer"] for x in s.metadata["steps"]}
    lo, hi = ox.SUBLAYER_RATE_DIFFERENCE_RAD_PER_A
    for i, dt in ((0, 0.5), (1, -0.5)):
        ov = steps[i]
        assert ov["conformal_at_step"] is False
        assert ov["thickness_difference_A"] == pytest.approx(dt, abs=1e-12)
        assert ov["consumed_layer_difference"] == 0
        assert ov["sublayer_thickness_difference_A"] == pytest.approx(dt, abs=1e-12)
        assert f"about {lo * 0.5:.2f}-{hi * 0.5:.2f} rad (mod 2 pi)" in ov[
            "multislice_sublayer_note"]
        assert ov["model_assumption_B4_overlayer"].startswith(B4_OXIDE_GROWN)
    assert steps[2]["conformal_at_step"] is True and "multislice_sublayer_note" not in steps[2]
    # one whole extra consumed layer (t + (a/4)/f, count 8): the sub-layer part is zero
    s = build(spec(terrace_thickness_A=(20.0, 20.0 + Q / f, 20.0),
                   terrace_consumed_layers=(7, 8, 7), labels=lab))
    ov = {x["index"]: x["overlayer"] for x in s.metadata["steps"]}[0]
    assert ov["consumed_layer_difference"] == 1
    assert ov["sublayer_thickness_difference_A"] == pytest.approx(0.0, abs=1e-9)


def test_nonconformal_acknowledgement_is_checked():
    lab = dict(overrides="TEST_ONLY: non-conformal engine test")
    rec = ox.validate_spec(spec(terrace_thickness_A=(20.0, 20.5), terrace_consumed_layers=(7, 7),
                                nonconformal_sublayer_acknowledged=True, labels=lab))
    assert rec["nonconformal_sublayer_acknowledged"] is True
    assert ox.validate_spec(spec())["nonconformal_sublayer_acknowledged"] is False
    with pytest.raises(ox.OxideSpecError, match="not needed"):          # one thickness
        ox.validate_spec(spec(terrace_thickness_A=(20.0, 20.0), terrace_consumed_layers=(7, 7),
                              nonconformal_sublayer_acknowledged=True, labels=lab))
    with pytest.raises(ox.OxideSpecError, match="not needed"):          # no overrides
        ox.validate_spec(spec(nonconformal_sublayer_acknowledged=True))
    with pytest.raises(ox.OxideSpecError, match="TEST_ONLY overrides label"):
        ox.validate_spec(spec(terrace_thickness_A=(20.0, 20.5), terrace_consumed_layers=(7, 7),
                              nonconformal_sublayer_acknowledged=True,
                              labels=dict(overrides="ASSUMPTION B41")))
    with pytest.raises(ox.OxideSpecError, match="True or False"):
        ox.validate_spec(spec(nonconformal_sublayer_acknowledged="yes"))


# --------------------------------------------------------------------------------------------------
# A9b M2 (a): the consumed-layer count is DERIVED_HERE
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("lab", ["PROJECT_INPUT item 12 (witness, TEST fabricated)",
                                 "ASSUMPTION B41 (stands in for PROJECT_INPUT item 12)"])
def test_consumed_layers_never_carries_project_input_or_assumption(lab):
    with pytest.raises(ox.OxideSpecError, match="DERIVED_HERE"):
        ox.validate_spec(spec(labels=dict(consumed_layers=lab)))


def test_consumed_layers_derived_label_is_accepted():
    lab = "DERIVED_HERE (nearest whole count; TEST)"
    rec = ox.validate_spec(spec(labels=dict(consumed_layers=lab)))
    assert rec["labels"]["consumed_layers"] == lab
    for t, n in ((20.0, 7), (15.0, 5), (18.45, 6)):
        assert ox.nearest_consumed_layers(thickness_A=t, density_g_cm3=2.20,
                                          amorphous_si_thickness_A=0.0, a_A=A_SI_A) == n


# --------------------------------------------------------------------------------------------------
# A9b n1: the headline label
# --------------------------------------------------------------------------------------------------
def test_headline_label_lists_mixed_labels():
    pi = "PROJECT_INPUT item 12 (TEST fabricated)"
    mixed = dict({k: pi for k in ox.LABEL_KEYS}, V_real="ASSUMPTION B43 (model row)",
                 consumed_layers="DERIVED_HERE (TEST)")
    s = spec(labels=mixed)
    head = ox.headline_label(s.labels)
    assert head.startswith("mixed (") and not head.startswith("PROJECT_INPUT")
    assert "ASSUMPTION B43" in head and "DERIVED_HERE" in head and "PROJECT_INPUT" in head
    assert ox.terrace_stacks(s, terrace_heights_A=[0.0], a_A=A_SI_A,
                             crystal="atomistic")["record"]["label"] == head
    assert build(s).metadata["options"]["overlayer"]["label"] == head
    assert ox.headline_label({k: L12 for k in ox.LABEL_KEYS}) == L12       # one label: itself


# --------------------------------------------------------------------------------------------------
# A9b m2: the margin is an arbitrary guard; the count interval over an uncertainty box
# --------------------------------------------------------------------------------------------------
def test_rounding_margin_is_stated_as_an_arbitrary_guard():
    rec = ox.terrace_stacks(spec(), terrace_heights_A=[0.0], a_A=A_SI_A,
                            crystal="atomistic")["record"]
    assert "arbitrary numerical guard" in rec["rounding_margin_rule"]
    assert "does not make the count or its parity robust" in rec["rounding_margin_rule"]
    assert "stated precision" not in str(rec)
    src = Path(ox.__file__).read_text()
    assert "the precision to which item-12 values are stated" not in src
    # the numbers of the comment at MIN_ROUNDING_MARGIN_LAYERS are the printed ones
    out = (REVIEW / "x5_oxide_numbers_output.txt").read_text()
    for s in ("0.1538 A of thickness", "0.769 % of the density", "0.0169 g/cm^3",
              "+-1.0 A -> continuum depth +-0.442 A = +-0.325 layer",
              "+-0.05 g/cm^3 at 20 A -> +-0.148 layer", "2.19877 g/cm^3 (-0.056 %)"):
        assert s in out, s
    comment = src[src.index("# A8 m4, A9b m2"):src.index("MIN_ROUNDING_MARGIN_LAYERS = 0.05")]
    for s in ("0.1538 A", "0.769 %", "0.0169 g/cm^3", "+-0.325 layer", "+-0.148 layer",
              "2.19877 g/cm^3", "-0.056 %", "0.068 A"):
        assert s in comment, s


@pytest.mark.parametrize("t,ut,ur,counts", [
    (20.0, 1.0, 0.05, [6, 7]),        # 2.0 nm: any uncertainty spans the boundary (6.5036 layers)
    (20.0, 0.1, 0.01, [6, 7]),
    (15.0, 0.5, 0.03, [5]),           # 1.5 nm: 0.378 layer of margin
    (15.0, 1.0, 0.05, [4, 5]),
    (15.0, 2.0, 0.10, [4, 5, 6]),
])
def test_consumed_count_interval(t, ut, ur, counts):
    ci = ox.consumed_count_interval(thickness_A=t, thickness_uncertainty_A=ut, density_g_cm3=2.20,
                                    density_uncertainty_g_cm3=ur, amorphous_si_thickness_A=0.0,
                                    a_A=A_SI_A)
    assert ci["counts"] == counts and ci["spans_boundary"] is (len(counts) > 1)
    f_lo = ox.consumed_si_fraction(2.20 - ur, A_SI_A)
    assert ci["continuum_layers_min"] == pytest.approx(f_lo * (t - ut) / Q, rel=1e-12)


@pytest.mark.parametrize("kw,match", [
    (dict(thickness_uncertainty_A=0.0), "thickness_uncertainty_A"),
    (dict(thickness_uncertainty_A=-1.0), "thickness_uncertainty_A"),
    (dict(thickness_uncertainty_A=20.0), "smaller than the thickness"),
    (dict(density_uncertainty_g_cm3=2.2), "smaller than the density"),
    (dict(density_uncertainty_g_cm3="0.05"), "number"),
])
def test_consumed_count_interval_refusals(kw, match):
    args = dict(thickness_A=20.0, thickness_uncertainty_A=1.0, density_g_cm3=2.20,
                density_uncertainty_g_cm3=0.05, amorphous_si_thickness_A=0.0, a_A=A_SI_A)
    args.update(kw)
    with pytest.raises(ox.OxideSpecError, match=match):
        ox.consumed_count_interval(**args)


# --------------------------------------------------------------------------------------------------
# A9b m3, m4: code strings quote the printed digits
# --------------------------------------------------------------------------------------------------
def test_edge_reflectivity_quotes_the_printed_digits():
    r2, rel, born, ratio = _quote(
        "a9b_c2_edge", r"QUOTE w 0.5 A at 16.1347 mrad: exact \|r\|\^2 = (\S+); \|r\|/\|r_sharp\| = "
                       r"(\S+) \(sharp edge.*Born factor \|r\|\^2 = (\S+); exact/Born = (\S+)")
    r2c, ratioc = _quote("a9b_c2_edge", r"central bin 16.1751 mrad: exact \|r\|\^2 = (\S+); "
                                        r"exact/Born = (\S+)")

    def short(x):                     # 1.9545e-09 -> 1.9545e-9 (the form used in the strings)
        return x.replace("e-0", "e-")
    text = ox.EDGE_W05_REFLECTIVITY
    for v in (short(r2), short(rel), short(born), f"{ratio} times lower", short(r2c),
              f"{ratioc} times the Born factor"):
        assert v in text, v
    assert short(r2) in ox.__doc__ and short(r2c) in ox.__doc__
    # the engine value quoted next to it is the committed test's print (1.8350e-09)
    src = (Path(__file__).resolve().parents[1] / "forward" / "test_oxide_multislice.py").read_text()
    assert "w = 0.5 A: |r|^2 = {abs(g['r']) ** 2:.4e}" in src and "1.8350e-9" in text


def test_interface_gap_dip_quotes_the_printed_digits():
    v, x, gap, born, dr, dph = _quote(
        "a9b_c3_gap", r"SUMMARY t 20.0 A: laterally averaged potential minimum (\S+) V at (\S+) A "
                      r"above the kept top plane; gap (\S+) A; Born \|r\|\^2 of the deficit at q = "
                      r"2 k'_ox (\S+); 1-D against the joined stack: \|r\| (\S+) %, arg (\S+) rad")
    gap15, dr15, dph15 = _quote(
        "a9b_c3_gap", r"SUMMARY t 15.0 A: .*gap (\S+) A;.*\|r\| (\S+) %, arg (\S+) rad")
    text = ox.INTERFACE_OVERLAP_RULE
    for s in (f"falls to {v} V, {x} A above", f"(gap {gap} A)", f"|r|^2 = {born}",
              f"|r| by {dr} %", f"phase by {dph} rad", f"gap {gap15} A: {dr15} %, {dph15} rad"):
        assert s in text, s
