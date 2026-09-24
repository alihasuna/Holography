"""Continuum oxide: the fixes of report X6 after the re-audit A10b of report X5 (structure level).

A10b M1  A count interval over the stated item-12 uncertainties that spans ONE rounding boundary
         admits a PARITY VARIANT: the specification states consumed_layers_parity_variant (lower or
         upper, the uncertainties and their kind) and the count is the lower or upper count of the
         interval, not necessarily the nearest one; the thickness is not altered, so the layer
         overlaps or misses the kept crystal by more than a/8 (at most 1.5 a/4). Refused: no
         boundary spanned, more than two counts, another count, per-terrace overrides, a DERIVED_HERE
         count label without the qualifier (or with it and no variant).
A10b m2  item12_count_interval takes the uncertainty kind: a standard uncertainty enters as +- 2 u
         (about 95 % coverage for a normal distribution), a half-width as +- itself.
A10b m3  the a-Si thickness uncertainty enters the interval (clipped at 0).
A10b n2  zero or negative uncertainties are refused.
A10b n1  nonconformal_sublayer_acknowledged is accepted for different counts at one thickness (the
         cell refusal itself: tests/forward/test_oxide_multislice_a10b_fixes.py).

Every value standing in for PROJECT_INPUT item 12 is TEST_ONLY; the reference numbers are the saved
output of tools/review/x6/x6_oxide_numbers.py, and for the count intervals (report X7: standard
uncertainties combined in quadrature, re-audit A12 m2) that of tools/review/x7/x7_oxide_numbers.py.
"""
import dataclasses
import hashlib
import json
import re
from pathlib import Path

import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import Staircase, build_si001_terraces
from reflection_holo.structure import oxide as ox

L12 = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (continuum oxide)"
Q = A_SI_A / 4
OUT = (Path(__file__).resolve().parents[2] / "tools" / "review" / "x6"
       / "x6_oxide_numbers_output.txt")
# report X7 (re-audit A12 m2): the intervals of standard uncertainties changed (quadrature); X6's
# saved output keeps X6's box and is no longer the reference for them
OUT_X7 = (Path(__file__).resolve().parents[2] / "tools" / "review" / "x7"
          / "x7_oxide_numbers_output.txt")
UNC = dict(thickness_uncertainty_A=1.0, density_uncertainty_g_cm3=0.05,
           amorphous_si_thickness_uncertainty_A=0.1, uncertainty_kind="half_width")


def variant(parity, **kw):
    return dict(UNC, parity=parity, **kw)


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
                consumed_layers_parity_variant=None, labels=lab)
    base.update(kw)
    return ox.ContinuumOxideSpec(**base)


def stacks(s):
    return ox.terrace_stacks(s, terrace_heights_A=[0.0], a_A=A_SI_A, crystal="atomistic")


def interval(**kw):
    args = dict(thickness_A=20.0, density_g_cm3=2.20, amorphous_si_thickness_A=0.0, a_A=A_SI_A,
                **UNC)
    args.update(kw)
    return ox.item12_count_interval(**args)


def _printed(pattern: str, out: Path = OUT) -> list[str]:
    m = re.search(pattern, out.read_text())
    assert m, pattern
    return list(m.groups())


# --------------------------------------------------------------------------------------------------
# A10b m2, m3, n2: the interval of the stated item-12 uncertainties
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("t,ut,ur,ta,ua", [(20.0, 1.0, 0.05, 0.0, 0.1), (20.0, 1.0, 0.05, 0.0, 1.0),
                                           (15.0, 0.5, 0.03, 0.0, 1.0),
                                           (15.0, 0.5, 0.03, 5.0, 0.5)])
@pytest.mark.parametrize("kind", ["standard", "half_width"])
def test_interval_matches_the_printed_cases(t, ut, ur, ta, ua, kind):
    # report X7: the reference is X7's saved output (standard: quadrature, re-audit A12 m2)
    lo, hi, counts = _printed(
        rf"t {t} \+- {ut} A, rho 2.20 \+- {ur} g/cm\^3, a-Si {ta} \+- {ua} A, {kind}: "
        r"(\d\.\d{3})-(\d\.\d{3}) layers .*-> counts (\[[\d, ]+\])", OUT_X7)
    ci = interval(thickness_A=t, thickness_uncertainty_A=ut, density_uncertainty_g_cm3=ur,
                  amorphous_si_thickness_A=ta, amorphous_si_thickness_uncertainty_A=ua,
                  uncertainty_kind=kind)
    assert f"{ci['continuum_layers_min']:.3f}" == lo and f"{ci['continuum_layers_max']:.3f}" == hi
    assert str(ci["counts"]) == counts


def test_the_amorphous_si_uncertainty_enters_the_interval():
    """A10b m3: 1 A of a-Si moves the depth by 1 A = 0.7365 layer (printed), 2.26 times the oxide's
    0.3252 layer per A; the upper corner carries + k u_a, the lower one is clipped at 0."""
    per_asi, per_t = _printed(r"= (\d\.\d{4}) layer per A\n.*= (\d\.\d{4}) layer per A")
    assert f"{1 / Q:.4f}" == per_asi
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    assert f"{f / Q:.4f}" == per_t
    a = interval(amorphous_si_thickness_uncertainty_A=0.1)
    b = interval(amorphous_si_thickness_uncertainty_A=1.0)
    assert b["continuum_layers_max"] - a["continuum_layers_max"] == pytest.approx(0.9 / Q, rel=1e-9)
    assert b["continuum_layers_min"] == a["continuum_layers_min"]           # clipped at 0
    assert a["counts"] == [6, 7] and b["counts"] == [6, 7, 8]
    assert b["box"]["amorphous_si_thickness_A"] == [0.0, 1.0]
    c = interval(amorphous_si_thickness_A=5.0, amorphous_si_thickness_uncertainty_A=0.5)
    assert c["box"]["amorphous_si_thickness_A"] == [4.5, 5.5]


def test_the_uncertainty_kind_sets_the_coverage():
    """A10b m2: a standard uncertainty enters with k = 2 (about 95 % coverage for a normal
    distribution: 95.45 %, printed), a half-width as itself. Report X7 (re-audit A12 m2): standard
    uncertainties are combined in quadrature, so 1 A, 0.05 g/cm^3 and 0.1 A as standard
    uncertainties no longer equal the box of their doubled half-widths (X6's rule, [6, 7, 8]): the
    interval is 5.789-7.233 layers, counts [6, 7] (printed by tools/review/x7)."""
    (cov,) = _printed(r"= (\d\d\.\d\d) % \(about 95 %\)")
    assert cov == "95.45" and ox.STANDARD_COVERAGE_FACTOR == 2.0
    assert "about 95 % coverage" in ox.COVERAGE_STATEMENT["standard"]
    assert "quadrature" in ox.COVERAGE_STATEMENT["standard"]
    assert "worst case" in ox.COVERAGE_STATEMENT["half_width"]
    s = interval(uncertainty_kind="standard")
    h = interval(uncertainty_kind="half_width", thickness_uncertainty_A=2.0,
                 density_uncertainty_g_cm3=0.10, amorphous_si_thickness_uncertainty_A=0.2)
    before, after = _printed(r"before \(report X6: .*: (\d\.\d{3}-\d\.\d{3}) layers .*\n"
                             r"  after \(report X7: .*\): (\d\.\d{3}-\d\.\d{3}) layers", OUT_X7)
    assert f"{h['continuum_layers_min']:.3f}-{h['continuum_layers_max']:.3f}" == before
    assert f"{s['continuum_layers_min']:.3f}-{s['continuum_layers_max']:.3f}" == after
    assert s["box"] == h["box"]                   # the per-quantity ranges +- k u are those of X6
    assert s["coverage_factor"] == 2.0 and h["coverage_factor"] == 1.0
    assert s["counts"] == [6, 7] and h["counts"] == [6, 7, 8] and interval()["counts"] == [6, 7]
    for bad in ("sigma", None, "Standard", ""):
        with pytest.raises(ox.OxideSpecError, match="uncertainty_kind must be one of"):
            interval(uncertainty_kind=bad)


@pytest.mark.parametrize("key", ["thickness_uncertainty_A", "density_uncertainty_g_cm3",
                                 "amorphous_si_thickness_uncertainty_A"])
@pytest.mark.parametrize("bad", [0.0, -0.1, -1e-12])
def test_zero_or_negative_uncertainties_are_refused(key, bad):
    with pytest.raises(ox.OxideSpecError, match=rf"{key} .*zero or negative refused.* must be > 0"):
        interval(**{key: bad})


@pytest.mark.parametrize("kw,match", [
    (dict(thickness_uncertainty_A=10.0, uncertainty_kind="standard"), "thickness interval"),
    (dict(density_uncertainty_g_cm3=1.1, uncertainty_kind="standard"), "density interval"),
    (dict(thickness_uncertainty_A="1.0"), "number"),
])
def test_interval_half_widths_must_stay_below_the_values(kw, match):
    with pytest.raises(ox.OxideSpecError, match=match):
        interval(**kw)


# --------------------------------------------------------------------------------------------------
# A10b M1: parity variants
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("parity,n,other,sign", [("lower", 6, 7, +1), ("upper", 7, 6, -1)])
def test_parity_variant_builds_the_lower_or_upper_count(parity, n, other, sign):
    lab = f"DERIVED_HERE ({ox.parity_variant_qualifier(parity)}; TEST)"
    s = spec(consumed_layers=n, consumed_layers_parity_variant=variant(parity),
             labels=dict(consumed_layers=lab))
    st = stacks(s)
    rec, p = st["record"], st["per_terrace"][0]
    assert s.thickness_A == 20.0 and p["thickness_A"] == 20.0          # no thickness altered
    assert p["consumed_layers"] == n and p["consumed_layers_nearest"] == 7
    assert p["parity_variant"] == parity
    v = rec["consumed_layers_parity_record"]
    assert v["parity"] == parity and v["count"] == n
    assert v["count_parity"] == ("even" if n % 2 == 0 else "odd")
    assert v["other_variant"] == dict(parity=("upper" if parity == "lower" else "lower"),
                                      count=other,
                                      count_parity=("even" if other % 2 == 0 else "odd"))
    assert v["interval"]["counts"] == [6, 7] and v["nearest_count"] == 7
    assert v["is_nearest_count"] is (n == 7)
    assert "is a SEPARATE run, not built here" in v["note"]
    assert v["qualifier"] == f"parity variant {parity} of an interval spanning a boundary"
    # the overlap (lower) or gap (upper) printed by tools/review/x6 (thickness not altered)
    (ov,) = _printed(rf"{parity} variant, count {n} .*= ([+-]\d\.\d{{4}}) A = ")
    assert f"{p['interface_overlap_A']:+.4f}" == ov and sign * p["interface_overlap_A"] > 0
    assert p["interface_overlap_bound_A"] == pytest.approx(1.5 * Q, rel=1e-12)
    # the rounding guard is judged on the nearest count (7: 0.0036 layer from its boundary)
    assert rec["near_rounding_boundary"] is True
    with pytest.raises(ox.OxideSpecError, match="rounding_boundary_acknowledged"):
        stacks(dataclasses.replace(s, rounding_boundary_acknowledged=False))


def test_parity_variant_builds_the_structure_with_that_count():
    """The atomistic builder removes exactly the variant's count (assertions (o1), (o2))."""
    st = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(3, 3, 3),
                   boundary_step_layers=-1)
    lab = f"DERIVED_HERE ({ox.parity_variant_qualifier('lower')}; TEST)"
    s = build_si001_terraces(
        azimuth_uvw=(1, 0, 0), azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
        staircase=st, edge_periods=2, substrate_layers=14, first_terrace_backbond_uvw=(1, 1, 0),
        termination="bulk", overlayer=spec(consumed_layers=6,
                                           consumed_layers_parity_variant=variant("lower"),
                                           labels=dict(consumed_layers=lab)),
        vacuum_above_A=20.0, lattice_parameter_A=A_SI_A, lattice_parameter_label="ASSUMPTION B2")
    ov = s.metadata["options"]["overlayer"]
    assert [p["consumed_layers"] for p in ov["per_terrace"]] == [6, 6, 6]
    tops = [t["top_layer_index"] for t in s.metadata["terrace_map"]]
    assert [p["kept_top_layer_index"] for p in ov["per_terrace"]] == [t - 6 for t in tops]
    assert ov["conformal"] is True
    assert ov["consumed_layers_parity_record"]["count"] == 6


@pytest.mark.parametrize("kw,match", [
    (dict(consumed_layers=7, consumed_layers_parity_variant=variant("lower")),
     "consumed_layers = 7 is not the lower count 6 of the interval"),
    (dict(consumed_layers=6, consumed_layers_parity_variant=variant("upper")),
     "consumed_layers = 6 is not the upper count 7 of the interval"),
    # report X7: with quadrature (re-audit A12 m2) the a-Si standard uncertainty 0.5 A gives
    # [6, 7, 8] (printed by tools/review/x7); X6's 0.1 A now gives [6, 7]
    (dict(consumed_layers=8, consumed_layers_parity_variant=variant(
        "upper", **dict(UNC, uncertainty_kind="standard",
                        amorphous_si_thickness_uncertainty_A=0.5))),
     "spans 2 rounding boundaries"),
    (dict(thickness_A=15.0, consumed_layers=5, rounding_boundary_acknowledged=False,
          consumed_layers_parity_variant=dict(variant("lower"), thickness_uncertainty_A=0.5,
                                              density_uncertainty_g_cm3=0.03)),
     "spans no rounding boundary, so the count is the nearest count"),
])
def test_parity_variant_interval_refusals(kw, match):
    with pytest.raises(ox.OxideSpecError, match=match):
        stacks(spec(**kw))


@pytest.mark.parametrize("kw,match", [
    (dict(consumed_layers_parity_variant=variant("both")), "parity must be one of"),
    (dict(consumed_layers_parity_variant=variant("odd")), "parity must be one of"),
    (dict(consumed_layers_parity_variant=variant(None)), "parity must be one of"),
    (dict(consumed_layers_parity_variant=dict(parity="lower")), "exactly the keys"),
    (dict(consumed_layers_parity_variant="lower"), "exactly the keys"),
    (dict(consumed_layers_parity_variant=variant("lower", uncertainty_kind="sigma")),
     "uncertainty_kind must be one of"),
    (dict(consumed_layers_parity_variant=dict(variant("lower"), thickness_uncertainty_A=0.0)),
     "must be > 0"),
    (dict(consumed_layers_parity_variant=variant("lower"), terrace_thickness_A=(20.0, 20.0),
          terrace_consumed_layers=(6, 6)), "overrides are refused"),
    (dict(consumed_layers_parity_variant=variant("lower"),
          labels=dict(consumed_layers="DERIVED_HERE (nearest count; TEST)")),
     "must carry the qualifier 'parity variant lower of an interval spanning a boundary'"),
    (dict(labels=dict(consumed_layers="DERIVED_HERE (parity variant lower of an interval spanning "
                                      "a boundary; TEST)")),
     "names a parity variant, but consumed_layers_parity_variant is None"),
])
def test_parity_variant_form_refusals(kw, match):
    with pytest.raises(ox.OxideSpecError, match=re.escape(match) if "'" in match else match):
        ox.validate_spec(spec(**kw))


def test_spec_hash_without_a_variant_is_unchanged():
    """The hash of a specification without a parity variant is the pre-X6 hash (the field left
    out), so recorded hashes stay comparable; the two variants hash differently."""
    s = spec()
    d = dataclasses.asdict(s)
    d.pop("consumed_layers_parity_variant")
    d["labels"] = dict(s.labels)
    want = hashlib.sha256(json.dumps(d, sort_keys=True, default=float).encode()).hexdigest()
    assert ox.spec_sha256(s) == want
    lo = spec(consumed_layers=6, consumed_layers_parity_variant=variant("lower"))
    up = spec(consumed_layers=7, consumed_layers_parity_variant=variant("upper"))
    assert len({ox.spec_sha256(x) for x in (s, lo, up)}) == 3


# --------------------------------------------------------------------------------------------------
# A10b n1: the acknowledgement covers different counts at one thickness
# --------------------------------------------------------------------------------------------------
def test_nonconformal_acknowledgement_for_counts_at_one_thickness():
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    t_tie = 6.5 * Q / f
    lab = dict(overrides="TEST_ONLY: two counts at the tie")
    rec = ox.validate_spec(spec(thickness_A=t_tie, terrace_consumed_layers=(6, 7),
                                nonconformal_sublayer_acknowledged=True, labels=lab))
    assert rec["nonconformal_sublayer_acknowledged"] is True
    with pytest.raises(ox.OxideSpecError, match="one consumed-layer count: the acknowledgement is "
                                                "not needed"):
        ox.validate_spec(spec(terrace_thickness_A=(20.0, 20.0), terrace_consumed_layers=(7, 7),
                              nonconformal_sublayer_acknowledged=True, labels=lab))
