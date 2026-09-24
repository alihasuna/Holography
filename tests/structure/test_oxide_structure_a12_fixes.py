"""Continuum oxide: the fixes of report X7 after the re-audit A12 of report X6 (structure level).

A12 m2  item12_count_interval: STANDARD uncertainties are combined in quadrature (the nominal depth
        +- 2 combined standard uncertainties, about 95 % coverage for a normally distributed depth;
        the a-Si term one-sided at its lower end); HALF-WIDTHS keep the worst case (the corners of
        the box, the linear sum), unchanged from report X6.
A12 n1  each uncertainty is bounded (its depth contribution below two layers of a/4, besides the
        existing bounds by the thickness and the density): an absurd value is an OxideSpecError
        naming the bound, never a MemoryError or an OverflowError; the list of counts is never
        built beyond _MAX_COUNTS_BUILT.
A12 n4  the parity-variant qualifier of a DERIVED_HERE count label is checked as an exact token.
A12 m3  the structure record names the variant whose count is the nearest; the stale comment in
        forward/cell.py ("at most a/8") is corrected.

Every value standing in for PROJECT_INPUT item 12 is TEST_ONLY; the reference numbers are the saved
output of tools/review/x7/x7_oxide_numbers.py (and of tools/review/x6 for the unchanged half-width
cases).
"""
import dataclasses
import math
import re
from pathlib import Path

import pytest

from reflection_holo.constants import A_SI_A, AVOGADRO_PER_MOL, M_O_G_PER_MOL, M_SI_G_PER_MOL
from reflection_holo.structure import oxide as ox

L12 = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (continuum oxide)"
Q = A_SI_A / 4
REVIEW = Path(__file__).resolve().parents[2] / "tools" / "review"
OUT_X6 = REVIEW / "x6" / "x6_oxide_numbers_output.txt"
OUT_X7 = REVIEW / "x7" / "x7_oxide_numbers_output.txt"
UNC = dict(thickness_uncertainty_A=1.0, density_uncertainty_g_cm3=0.05,
           amorphous_si_thickness_uncertainty_A=0.1, uncertainty_kind="half_width")
LINE = (r"t {t} \+- {ut} A, rho 2.20 \+- {ur} g/cm\^3, a-Si {ta} \+- {ua} A, {kind}: "
        r"(\d\.\d{{3}})-(\d\.\d{{3}}) layers .*?-> counts (\[[\d, ]+\])")
CASES = [(20.0, 1.0, 0.05, 0.0, 0.1), (20.0, 0.1, 0.01, 0.0, 0.1), (20.0, 1.0, 0.05, 0.0, 1.0),
         (20.0, 1.0, 0.05, 0.0, 0.5), (15.0, 0.5, 0.03, 0.0, 0.1), (15.0, 1.0, 0.05, 0.0, 0.1),
         (15.0, 0.5, 0.03, 0.0, 1.0), (15.0, 0.5, 0.03, 5.0, 0.5)]


def interval(**kw):
    args = dict(thickness_A=20.0, density_g_cm3=2.20, amorphous_si_thickness_A=0.0, a_A=A_SI_A,
                **UNC)
    args.update(kw)
    return ox.item12_count_interval(**args)


def _f(rho):
    """f from first principles (Si atoms conserved), independent of the package function."""
    rho_si = 8 * M_SI_G_PER_MOL / AVOGADRO_PER_MOL / (A_SI_A * 1e-8) ** 3
    return (rho / (M_SI_G_PER_MOL + 2 * M_O_G_PER_MOL)) / (rho_si / M_SI_G_PER_MOL)


def _independent(t, ut, ur, ta, ua, kind, rho=2.20):
    """The rule of the decision, written out: quadrature (standard, k = 2, a-Si one-sided below) or
    the corners of the box (half-width). Returns (lo, hi) in layers and the counts."""
    k = 2.0 if kind == "standard" else 1.0
    ht, hr, ha = k * ut, k * ur, k * ua
    d0 = _f(rho) * t + ta
    if kind == "standard":
        ct, cr = _f(rho) * ht, _f(rho) * t * hr / rho
        lo = d0 - math.sqrt(ct ** 2 + cr ** 2 + min(ha, ta) ** 2)
        hi = d0 + math.sqrt(ct ** 2 + cr ** 2 + ha ** 2)
    else:
        lo = _f(rho - hr) * (t - ht) + max(0.0, ta - ha)
        hi = _f(rho + hr) * (t + ht) + ta + ha
    n_lo, n_hi = math.floor(lo / Q + 0.5), math.floor(hi / Q + 0.5)
    return lo / Q, hi / Q, list(range(n_lo, n_hi + 1))


# --------------------------------------------------------------------------------------------------
# A12 m2: quadrature for standard uncertainties, the box for half-widths
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("t,ut,ur,ta,ua", CASES)
@pytest.mark.parametrize("kind", ["standard", "half_width"])
def test_interval_follows_the_decided_rule(t, ut, ur, ta, ua, kind):
    ci = interval(thickness_A=t, thickness_uncertainty_A=ut, density_uncertainty_g_cm3=ur,
                  amorphous_si_thickness_A=ta, amorphous_si_thickness_uncertainty_A=ua,
                  uncertainty_kind=kind)
    lo, hi, counts = _independent(t, ut, ur, ta, ua, kind)
    assert ci["continuum_layers_min"] == pytest.approx(lo, abs=1e-12)
    assert ci["continuum_layers_max"] == pytest.approx(hi, abs=1e-12)
    assert ci["counts"] == counts
    m = re.search(LINE.format(t=t, ut=ut, ur=ur, ta=ta, ua=ua, kind=kind), OUT_X7.read_text())
    assert m and m.groups() == (f"{lo:.3f}", f"{hi:.3f}", str(counts))
    assert ci["combination"].startswith("quadrature" if kind == "standard" else "linear")
    cl = ci["combined_half_width_layers"]
    assert cl["lower"] == pytest.approx(ci["continuum_layers_nominal"] - lo, abs=1e-12)
    assert cl["upper"] == pytest.approx(hi - ci["continuum_layers_nominal"], abs=1e-12)


@pytest.mark.parametrize("t,ut,ur,ta,ua", [c for c in CASES if c != (20.0, 1.0, 0.05, 0.0, 0.5)])
def test_half_width_intervals_are_unchanged_from_x6(t, ut, ur, ta, ua):
    """The worst case (box corners) is kept for half-widths: X7 prints X6's numbers."""
    pat = LINE.format(t=t, ut=ut, ur=ur, ta=ta, ua=ua, kind="half_width")
    x6, x7 = re.search(pat, OUT_X6.read_text()), re.search(pat, OUT_X7.read_text())
    assert x6 and x7 and x6.groups() == x7.groups()


def test_a12_example_before_and_after():
    """1 A, 0.05 g/cm^3, 0.1 A as standard uncertainties at 2.0 nm: X6's box 5.587-7.626 layers,
    [6, 7, 8] (refused); in quadrature 5.789-7.233, [6, 7] (printed)."""
    out = OUT_X7.read_text()
    assert ("before (report X6: each quantity at +- 2u, depth at the box corners, linear sum): "
            "5.587-7.626 layers -> counts [6, 7, 8] (refused: more than two counts); equals X6's "
            "printed standard line ('5.587', '7.626', '[6, 7, 8]'): True") in out
    assert ("5.789-7.233 layers (half-widths -0.7144 / +0.7294 layer) -> counts [6, 7]; first "
            "principles 5.789-7.233") in out
    s = interval(uncertainty_kind="standard")
    assert f"{s['continuum_layers_min']:.3f}-{s['continuum_layers_max']:.3f}" == "5.789-7.233"
    assert s["counts"] == [6, 7]
    old = interval(thickness_uncertainty_A=2.0, density_uncertainty_g_cm3=0.10,
                   amorphous_si_thickness_uncertainty_A=0.2)
    assert f"{old['continuum_layers_min']:.3f}-{old['continuum_layers_max']:.3f}" == "5.587-7.626"
    assert old["counts"] == [6, 7, 8]


def test_the_asi_term_is_one_sided_below():
    """At t_a = 0 the lower half-width holds the thickness and density terms only; with t_a well
    above k u_a the interval is symmetric."""
    s = interval(uncertainty_kind="standard")
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    ct, cr = f * 2.0 / Q, f * 20 * 0.10 / 2.20 / Q
    assert s["combined_half_width_layers"]["lower"] == pytest.approx(math.hypot(ct, cr), rel=1e-12)
    assert s["combined_half_width_layers"]["upper"] == pytest.approx(
        math.sqrt(ct ** 2 + cr ** 2 + (0.2 / Q) ** 2), rel=1e-12)
    c = interval(uncertainty_kind="standard", amorphous_si_thickness_A=5.0,
                 amorphous_si_thickness_uncertainty_A=0.5)
    assert c["combined_half_width_layers"]["lower"] == pytest.approx(
        c["combined_half_width_layers"]["upper"], rel=1e-12)


def test_the_coverage_check_is_printed():
    """The coverage statement: 95.45 % analytically for a normally distributed depth; the seeded
    Monte Carlo of the exact depth f(rho) t + t_a (no clipping) agrees within 0.1 %."""
    out = OUT_X7.read_text()
    assert "erf(2/sqrt(2)) = 95.45 % for a normally distributed depth" in out
    m = re.search(r"a-Si 5\.0 \+- 0\.5 A normal \(no clipping\)\): quadrature [\d.-]+: depth inside "
                  r"(\d\d\.\d\d) %", out)
    assert m and abs(float(m.group(1)) - 95.45) < 0.1
    m = re.search(r"exactly 0 \(true absence; u_a the detection limit\)\): quadrature 5\.789-7\.233: "
                  r"depth inside (\d\d\.\d\d) %.*X6 box 5\.587-7\.626: depth inside (\d\d\.\d\d) %", out)
    assert m and 95.0 < float(m.group(1)) < 96.0 and float(m.group(2)) > 99.0
    assert "quadrature" in ox.COVERAGE_STATEMENT["standard"]
    assert "one-sided" in ox.COVERAGE_STATEMENT["standard"]


# --------------------------------------------------------------------------------------------------
# A12 n1: bounds on each uncertainty
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["standard", "half_width"])
@pytest.mark.parametrize("key,sens", [("thickness_uncertainty_A", "t"),
                                      ("density_uncertainty_g_cm3", "rho"),
                                      ("amorphous_si_thickness_uncertainty_A", "a")])
def test_each_uncertainty_is_bounded(kind, key, sens):
    k = 2.0 if kind == "standard" else 1.0
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    s = {"t": f, "rho": f * 20.0 / 2.20, "a": 1.0}[sens]
    u_max = 2 * Q / (k * s)
    base = dict(UNC, uncertainty_kind=kind)
    below = interval(**dict(base, **{key: u_max * (1 - 1e-9)}))
    assert len(below["counts"]) >= 2
    u = u_max * (1 + 1e-9)
    with pytest.raises(ox.OxideSpecError) as exc:
        interval(**dict(base, **{key: u}))
    msg = str(exc.value)
    assert f"{key} = {u}" in msg and ox.UNCERTAINTY_BOUND_STATEMENT in msg
    assert f"the upper bound of this uncertainty here is {u_max:.4g}" in msg
    for u in (10 * u_max, 1e9, 1e300, 1.7e308):         # never MemoryError or OverflowError
        with pytest.raises(ox.OxideSpecError) as exc:
            interval(**dict(base, **{key: u}))
        assert ox.UNCERTAINTY_BOUND_STATEMENT in str(exc.value)


@pytest.mark.parametrize("ta", [0.0, 0.3, 0.6789, 1.0, 5.0])
@pytest.mark.parametrize("kind", ["standard", "half_width"])
def test_the_bound_refuses_only_intervals_of_three_or_more_counts(ta, kind):
    """At the bound (a depth contribution of exactly two layers) the unbounded interval, computed
    independently, already holds at least three counts, which the ruling refuses: the bound refuses
    no record that would otherwise run."""
    k = 2.0 if kind == "standard" else 1.0
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    for ut, ur, ua in ((2 * Q / (k * f), 0.01, 0.01), (0.01, 2 * Q * 2.20 / (k * f * 20), 0.01),
                       (0.01, 0.01, 2 * Q / k)):
        assert len(_independent(20.0, ut, ur, ta, ua, kind)[2]) >= 3


def test_absurd_values_never_build_a_list():
    with pytest.raises(ox.OxideSpecError, match="refused before the list is built"):
        ox._counts_between(0.0, 100 * Q, Q)
    with pytest.raises(ox.OxideSpecError, match="is not finite"):
        ox._counts_between(0.0, math.inf, Q)
    # X5's consumed_count_interval (no depth bound) at an absurd thickness
    with pytest.raises(ox.OxideSpecError, match="refused before the list is built"):
        ox.consumed_count_interval(thickness_A=1e300, thickness_uncertainty_A=1e299,
                                   density_g_cm3=2.20, density_uncertainty_g_cm3=0.05,
                                   amorphous_si_thickness_A=0.0, a_A=A_SI_A)
    assert ox._counts_between(5.6 * Q, 7.4 * Q, Q) == [6, 7]


@pytest.mark.parametrize("exc", [OverflowError, MemoryError])
def test_overflow_and_memory_errors_become_spec_errors(monkeypatch, exc):
    def boom(lo, hi, q):
        raise exc("TEST")
    monkeypatch.setattr(ox, "_counts_between", boom)
    for kind in ("standard", "half_width"):
        with pytest.raises(ox.OxideSpecError, match=f"too large to form a count interval "
                                                    f"\\({exc.__name__}\\)"):
            interval(uncertainty_kind=kind)


# --------------------------------------------------------------------------------------------------
# A12 n4: exact-token qualifier; A12 m3: the nearest variant
# --------------------------------------------------------------------------------------------------
def spec(*, labels=None, **kw):
    lab = {k: L12 for k in ox.LABEL_KEYS}
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


QL, QU = ox.parity_variant_qualifier("lower"), ox.parity_variant_qualifier("upper")


@pytest.mark.parametrize("parity,label", [
    ("upper", f"DERIVED_HERE ({QU}; TEST) {QL}"),                    # A12 D2b: both qualifiers
    ("lower", f"DERIVED_HERE ({QL}; {QU}; TEST)"),
    ("upper", f"DERIVED_HERE ({QU}; {QU}; TEST)"),                   # the qualifier twice
    ("upper", f"DERIVED_HERE ({QU}; also a parity variant; TEST)"),  # other parity-variant text
    ("upper", f"DERIVED_HERE ({QL}; TEST)"),                         # the other parity
    ("upper", "DERIVED_HERE (parity variant upperx of an interval spanning a boundary; TEST)"),
])
def test_qualifier_is_an_exact_token(parity, label):
    n = 7 if parity == "upper" else 6
    s = spec(consumed_layers=n, consumed_layers_parity_variant=dict(UNC, parity=parity),
             labels=dict(consumed_layers=label))
    with pytest.raises(ox.OxideSpecError, match="exactly once and name no other parity variant"):
        ox.validate_spec(s)


@pytest.mark.parametrize("parity,n", [("lower", 6), ("upper", 7)])
def test_structure_record_names_the_nearest_count_variant(parity, n):
    lab = f"DERIVED_HERE ({ox.parity_variant_qualifier(parity)}; TEST)"
    s = spec(consumed_layers=n, consumed_layers_parity_variant=dict(UNC, parity=parity),
             labels=dict(consumed_layers=lab))
    rec = ox.terrace_stacks(s, terrace_heights_A=[0.0], a_A=A_SI_A,
                            crystal="atomistic")["record"]["consumed_layers_parity_record"]
    assert rec["nearest_count"] == 7 and rec["nearest_count_variant"] == "upper"
    assert rec["is_nearest_count"] is (parity == "upper")
    assert ox.nearest_count_variant(interval(thickness_A=15.0, thickness_uncertainty_A=0.5,
                                             density_uncertainty_g_cm3=0.03)) is None    # [5]
    assert ox.nearest_count_variant(interval(amorphous_si_thickness_uncertainty_A=1.0)) is None
    lo = dataclasses.replace(s, labels=dict(s.labels))
    assert ox.validate_spec(lo)["consumed_layers_parity_variant"]["parity"] == parity


def test_cell_comment_states_the_variant_overlap():
    text = " ".join((Path(ox.__file__).resolve().parents[1] / "forward" / "cell.py")
                    .read_text().replace("#", " ").split())
    assert "which the layer overlaps or misses by at most a/8)" not in text
    assert ("overlaps or misses by at most a/8 for the nearest count and by up to 1.5 a/4 for a "
            "parity variant whose count is not the nearest one") in text
