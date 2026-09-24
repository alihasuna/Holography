"""Continuum oxide: the fixes of report X4 after the audit A8 of report E4 (structure level).

A8 M1  a-Si = 0 labelled PROJECT_INPUT (a measured zero) is accepted; an unlabelled zero is refused;
       V'_ox = 0 still needs ASSUMPTION or TEST_ONLY.
A8 M2  the stack of an atomistic terrace is placed from its Si equivalent boundary, a/8 above the top
       atomic plane; the recorded interface overlap is f t + t_a - N a/4, bounded by a/8 (its value
       in the engine's potential: tests/forward/test_oxide_multislice_a8_fixes.py).
A8 m4  the distance of the consumed-layer count from its rounding boundary is recorded; closer than
       MIN_ROUNDING_MARGIN_LAYERS the specification is refused unless acknowledged; an unneeded
       acknowledgement is refused.
A8 m5  the oxide/Si transition is graded over >= 0.5 A unless a TEST_ONLY flag says otherwise.
A8 n1  numbers given as strings are refused; n2: the buried B4 statement carries its note.

Every value standing in for PROJECT_INPUT item 12 is TEST_ONLY; the reference numbers are A8's
(C5: f(2.20) t/(a/4) = 6.5036 layers at 2 nm, the count 7 becomes 6 at 2.19877 g/cm^3) and E9's
(tools/review/e9_recompute_output.txt, out:125-127, 143) at their printed precision.
"""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import Staircase, build_si001_terraces
from reflection_holo.structure import oxide as ox
from reflection_holo.structure.si001 import B4_BURIED_NOTE

L12 = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (continuum oxide)"
Q = A_SI_A / 4


def spec(*, labels=None, raw_labels=None, **kw):
    """labels: updates of the TEST_ONLY labels; raw_labels: the whole label mapping."""
    base = dict(material="amorphous SiO2", thickness_A=20.0, density_g_cm3=2.20, consumed_layers=7,
                V_real_V=10.34, V_imag_V=0.40, vacuum_edge_width_A=0.5, interface_width_A=0.5,
                amorphous_si_thickness_A=0.0, amorphous_si_V_real_V=None,
                amorphous_si_V_imag_V=None, terrace_thickness_A=None, terrace_consumed_layers=None,
                sharp_edge_test_flag=False, sharp_interface_test_flag=False,
                rounding_boundary_acknowledged=True,
                nonconformal_sublayer_acknowledged=False,     # audit A9b M1 (stated)
                labels=(raw_labels if raw_labels is not None else
                        dict({k: L12 for k in ox.LABEL_KEYS}, **(labels or {}))))
    base.update(kw)
    return ox.ContinuumOxideSpec(**base)


def stacks(s, heights=(0.0,), crystal="atomistic"):
    return ox.terrace_stacks(s, terrace_heights_A=list(heights), a_A=A_SI_A, crystal=crystal)


def build(s, *, az=(1, 0, 0)):
    st = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(3, 3, 3),
                   boundary_step_layers=-1)
    return build_si001_terraces(
        azimuth_uvw=az, azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8", staircase=st,
        edge_periods=2, substrate_layers=14, first_terrace_backbond_uvw=(1, 1, 0),
        termination="bulk", overlayer=s, vacuum_above_A=20.0, lattice_parameter_A=A_SI_A,
        lattice_parameter_label="ASSUMPTION B2")


# --------------------------------------------------------------------------------------------------
# A8 M1
# --------------------------------------------------------------------------------------------------
def test_measured_zero_amorphous_si_is_accepted():
    rec = ox.validate_spec(spec(labels=dict(amorphous_si="PROJECT_INPUT item 12 (witness TEM, "
                                                         "TEST fabricated)")))
    assert rec["amorphous_si_thickness_A"] == 0.0
    assert rec["amorphous_si_zero"].startswith("a measured zero")
    assert ox.validate_spec(spec())["amorphous_si_zero"].startswith("the optimistic bound")


@pytest.mark.parametrize("bad", [None, "", "  ", "measured"])
def test_unlabelled_zero_amorphous_si_is_refused(bad):
    labels = {k: L12 for k in ox.LABEL_KEYS}
    if bad is None:
        labels.pop("amorphous_si")
    else:
        labels["amorphous_si"] = bad
    with pytest.raises(ValueError, match="label"):
        ox.validate_spec(spec(raw_labels=labels))


def test_zero_absorption_is_still_not_a_measurement():
    with pytest.raises(ValueError, match="ASSUMPTION"):
        ox.validate_spec(spec(V_imag_V=0.0, labels=dict(V_imag="PROJECT_INPUT item 12")))


# --------------------------------------------------------------------------------------------------
# A8 M2
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("t,N,rho", [(20.0, 7, 2.20), (15.0, 5, 2.20), (20.0, 6, 2.198)])
def test_atomistic_reference_surface_and_overlap(t, N, rho):
    s = spec(thickness_A=t, consumed_layers=N, density_g_cm3=rho,
             rounding_boundary_acknowledged=(t == 20.0))
    p = stacks(s, heights=(5.0,))["per_terrace"][0]
    f = ox.consumed_si_fraction(rho, A_SI_A)
    assert p["pre_oxidation_plane_x_A"] == 5.0
    assert p["pre_oxidation_surface_x_A"] == pytest.approx(5.0 + Q / 2, abs=1e-12)
    assert p["atomistic_crystal_top_x_A"] == pytest.approx(5.0 - N * Q, abs=1e-12)
    assert p["crystal_equivalent_boundary_x_A"] == pytest.approx(5.0 - N * Q + Q / 2, abs=1e-12)
    assert p["interface_x_A"] == pytest.approx(5.0 + Q / 2 - f * t, abs=1e-12)
    ov = p["crystal_equivalent_boundary_x_A"] - p["crystal_boundary_x_A"]
    assert p["interface_overlap_A"] == pytest.approx(ov, abs=1e-12)
    assert p["interface_overlap_A"] == pytest.approx(f * t - N * Q, abs=1e-12)
    assert p["interface_quantisation_A"] == pytest.approx(p["interface_overlap_A"], abs=1e-12)
    assert abs(p["interface_overlap_A"]) <= Q / 2 == p["interface_overlap_bound_A"]


def test_the_three_cases_of_a8():
    """A8 C9 measured +0.005 / +0.513 / +1.355 A (E4's placement, bounded by [0, a/4]); the
    same cases placed from the equivalent boundary: -0.674 / -0.166 / +0.676 A (= A8's minus a/8,
    printed precision), bounded by a/8."""
    got = [stacks(spec(thickness_A=t, consumed_layers=N, density_g_cm3=rho,
                       rounding_boundary_acknowledged=(t == 20.0)))["per_terrace"][0][
               "interface_overlap_A"] for t, N, rho in ((20.0, 7, 2.20), (15.0, 5, 2.20),
                                                        (20.0, 6, 2.198))]
    np.testing.assert_allclose(got, [0.005 - Q / 2, 0.513 - Q / 2, 1.355 - Q / 2], atol=1.5e-3)
    np.testing.assert_allclose(got, [-0.674, -0.166, 0.676], atol=1e-3)


def test_continuum_crystal_has_no_overlap():
    p = stacks(spec(), heights=(3.0,), crystal="continuum")["per_terrace"][0]
    assert p["pre_oxidation_surface_x_A"] == 3.0 and p["atomistic_crystal_top_x_A"] is None
    assert p["crystal_equivalent_boundary_x_A"] == p["crystal_boundary_x_A"]
    assert p["interface_overlap_A"] == 0.0
    with pytest.raises(ValueError, match="crystal must be one of"):
        stacks(spec(), crystal="mixed")
    with pytest.raises(TypeError):
        ox.terrace_stacks(spec(), terrace_heights_A=[0.0], a_A=A_SI_A)


def test_builder_places_the_stack_from_the_equivalent_boundary():
    s = build(spec())
    o = s.metadata["options"]["overlayer"]
    assert o["crystal"] == "atomistic" and "a/8" in o["reference_plane"]
    for k, p in enumerate(o["per_terrace"]):
        H = s.metadata["terrace_map"][k]["top_height_A"]
        kept = s.positions_A[s.terrace_index == k, 0].max()
        assert p["pre_oxidation_plane_x_A"] == H
        assert p["pre_oxidation_surface_x_A"] == pytest.approx(H + Q / 2, abs=1e-12)
        assert kept == pytest.approx(H - 7 * Q, abs=1e-9)
        # the recorded overlap is measured on the kept atoms: top atomic plane + a/8 - x_c
        assert kept + Q / 2 - p["crystal_boundary_x_A"] == pytest.approx(p["interface_overlap_A"],
                                                                         abs=1e-9)
        assert p["top_rise_A"] == pytest.approx(11.1699, abs=5e-5)          # E9 out:143


# --------------------------------------------------------------------------------------------------
# A8 m4
# --------------------------------------------------------------------------------------------------
def test_rounding_margin_is_recorded_and_equals_a8():
    rm = ox.rounding_margin(thickness_A=20.0, density_g_cm3=2.20, amorphous_si_thickness_A=0.0,
                            consumed_layers=7, a_A=A_SI_A)
    assert rm["continuum_layers"] == pytest.approx(6.5036, abs=5e-5)                 # A8 C5
    assert rm["margin_layers"] == pytest.approx(0.0036, abs=5e-5)
    assert rm["count_changes_to"] == 6
    assert rm["count_changes_at_density_g_cm3"] == pytest.approx(2.19877, abs=5e-6)  # A8 C5
    assert rm["near_boundary"] is True
    p = stacks(spec())["per_terrace"][0]
    assert p["rounding_margin_layers"] == pytest.approx(rm["margin_layers"], abs=1e-12)
    rec = stacks(spec())["record"]
    assert rec["near_rounding_boundary"] is True and "2.19877" in rec["rounding_boundary_note"]
    far = ox.rounding_margin(thickness_A=15.0, density_g_cm3=2.20, amorphous_si_thickness_A=0.0,
                             consumed_layers=5, a_A=A_SI_A)
    assert far["margin_layers"] == pytest.approx(0.5 - (5 - 4.878), abs=5e-4)       # out:126
    assert far["near_boundary"] is False


@pytest.mark.parametrize("t,N,rho", [(20.0, 7, 2.20), (20.0, 6, 2.198)])
def test_near_the_rounding_boundary_needs_the_acknowledgement(t, N, rho):
    with pytest.raises(ValueError, match="rounding_boundary_acknowledged = True"):
        stacks(spec(thickness_A=t, consumed_layers=N, density_g_cm3=rho,
                    rounding_boundary_acknowledged=False))
    with pytest.raises(ValueError, match="rounding boundary"):
        build(spec(thickness_A=t, consumed_layers=N, density_g_cm3=rho,
                   rounding_boundary_acknowledged=False))
    stacks(spec(thickness_A=t, consumed_layers=N, density_g_cm3=rho,
                rounding_boundary_acknowledged=True))


def test_unneeded_acknowledgement_is_refused():
    with pytest.raises(ValueError, match="not needed"):
        stacks(spec(thickness_A=15.0, consumed_layers=5, rounding_boundary_acknowledged=True))
    with pytest.raises(ValueError, match="True or False"):
        ox.validate_spec(spec(rounding_boundary_acknowledged="yes"))


def test_overrides_acknowledge_per_terrace():
    """One terrace near the boundary (2 nm), one far (1.5 nm): the acknowledgement is needed."""
    lab = dict(overrides=L12)
    s = spec(terrace_thickness_A=(20.0, 15.0), terrace_consumed_layers=(7, 5), labels=lab,
             rounding_boundary_acknowledged=False)
    with pytest.raises(ValueError, match="terrace 0"):
        stacks(s, heights=(0.0, Q))


# --------------------------------------------------------------------------------------------------
# A8 m5, n1, n2
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("w_i", [0.0, 0.25, 0.49])
def test_interface_must_be_graded(w_i):
    with pytest.raises(ValueError, match="graded over at least 0.5"):
        ox.validate_spec(spec(interface_width_A=w_i))
    with pytest.raises(ValueError, match="TEST_ONLY interface label"):
        ox.validate_spec(spec(interface_width_A=w_i, sharp_interface_test_flag=True,
                              labels=dict(interface="ASSUMPTION sharp")))
    rec = ox.validate_spec(spec(interface_width_A=w_i, sharp_interface_test_flag=True))
    assert rec["sharp_interface_test_flag"] is True


def test_interface_flag_not_needed_is_refused():
    with pytest.raises(ValueError, match="not needed"):
        ox.validate_spec(spec(sharp_interface_test_flag=True))
    with pytest.raises(ValueError, match="True or False"):
        ox.validate_spec(spec(sharp_interface_test_flag=1))


@pytest.mark.parametrize("field", ["thickness_A", "density_g_cm3", "V_real_V", "V_imag_V",
                                   "vacuum_edge_width_A", "interface_width_A"])
def test_numbers_given_as_strings_are_refused(field):
    good = getattr(spec(), field)
    with pytest.raises(ValueError, match="number"):
        ox.validate_spec(spec(**{field: str(good)}))


def test_numpy_numbers_are_accepted():
    ox.validate_spec(spec(thickness_A=np.float64(20.0), V_real_V=np.float32(10.34)))


def test_buried_b4_statement_carries_its_note():
    s = build(spec())
    buried = [st["overlayer"] for st in s.metadata["steps"]
              if st["overlayer"]["buried_relation"] != "none"]
    assert buried and all(b["buried_b4_note"] == B4_BURIED_NOTE for b in buried)
    assert "model_assumption_B4_overlayer" in B4_BURIED_NOTE


def test_edge_reflectivity_text_is_the_exact_value():
    """A8 m1: the recorded statement is the exact 1-D value, not E9's Born estimate. Since report
    X5 (audit A9b m3) the text quotes the digits printed by tools/review/x5/a9b_c2_edge.py
    (1.9545e-9, formerly the rounded 1.95e-9)."""
    rec = stacks(spec())["record"]
    assert "1.9545e-9" in rec["edge_reflectivity_w05"] and "1.1e-4" not in str(rec)
    with pytest.raises(ValueError, match="1.9545e-9"):
        ox.validate_spec(spec(vacuum_edge_width_A=0.3))
