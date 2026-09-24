"""Continuum oxide overlayer: geometry, builder assertions (o1)-(o4) and refusals (report E4).

Reference numbers are lines of tools/review/e9_recompute_output.txt (E9, "out:N"); tolerances are
the printed precision of those lines (a priori). Every value standing in for PROJECT_INPUT item 12
is labelled TEST_ONLY.
"""
import dataclasses

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import Staircase, build_si001_terraces
from reflection_holo.structure import oxide as ox
from reflection_holo.structure.checks import StructureAssertionError

L12 = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (continuum oxide)"
KEYS = ox.LABEL_KEYS
Q = A_SI_A / 4


def _near_rounding_boundary(d):
    """TEST helper (audit A8 m4): True when some terrace's count lies within
    ox.MIN_ROUNDING_MARGIN_LAYERS of its rounding boundary, so that the fixtures state the
    acknowledgement exactly when it is needed (the gate itself:
    test_oxide_structure_a8_fixes.py); False for inputs the specification refuses anyway."""
    try:
        tt = d["terrace_thickness_A"] or (d["thickness_A"],)
        tn = d["terrace_consumed_layers"] or (d["consumed_layers"],)
        return any(ox.rounding_margin(thickness_A=t, density_g_cm3=d["density_g_cm3"],
                                      amorphous_si_thickness_A=d["amorphous_si_thickness_A"],
                                      consumed_layers=n, a_A=A_SI_A)["near_boundary"]
                   for t, n in zip(tt, tn))
    except (ValueError, TypeError):
        return False


def spec(**kw):
    base = dict(material="amorphous SiO2", thickness_A=20.0, density_g_cm3=2.20, consumed_layers=7,
                V_real_V=10.34, V_imag_V=0.40, vacuum_edge_width_A=0.5, interface_width_A=0.5,
                amorphous_si_thickness_A=0.0, amorphous_si_V_real_V=None,
                amorphous_si_V_imag_V=None, terrace_thickness_A=None, terrace_consumed_layers=None,
                sharp_edge_test_flag=False, sharp_interface_test_flag=False,
                labels={k: L12 for k in KEYS})
    base.update(kw)
    base.setdefault("rounding_boundary_acknowledged", _near_rounding_boundary(base))
    return ox.ContinuumOxideSpec(**base)


def build(overlayer, *, layers=(0, 2, 1), widths=(3, 3, 3), boundary=-1, az=(1, 0, 0),
          substrate_layers=14, vacuum_above_A=20.0, edges="transverse", termination="bulk"):
    st = Staircase(edges=edges, terrace_layers=layers, terrace_widths=widths,
                   boundary_step_layers=boundary)
    return build_si001_terraces(
        azimuth_uvw=az, azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
        staircase=st, edge_periods=2, substrate_layers=substrate_layers,
        first_terrace_backbond_uvw=(1, 1, 0), termination=termination, overlayer=overlayer,
        vacuum_above_A=vacuum_above_A, lattice_parameter_A=A_SI_A,
        lattice_parameter_label="ASSUMPTION B2")


# --------------------------------------------------------------------------------------------------
# E9 numbers (printed precision)
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("rho,f_e9,line", [(2.07, 0.4154, 139), (2.10, 0.4214, 140),
                                           (2.18, 0.4375, 141), (2.20, 0.4415, 143),
                                           (2.27, 0.4556, 144), (2.30, 0.4616, 146)])
def test_consumed_fraction_equals_e9(rho, f_e9, line):
    """f = (rho_ox/M_SiO2)/(rho_Si/M_Si), E9 out:139-147 (4 decimals)."""
    assert ox.consumed_si_fraction(rho, A_SI_A) == pytest.approx(f_e9, abs=5e-5), line


def test_silicon_density_and_formula_units_equal_e9():
    assert ox.silicon_density_g_cm3(A_SI_A) == pytest.approx(2.3292, abs=5e-5)       # out:138
    assert ox.sio2_formula_units_per_A3(2.20) == pytest.approx(0.02205, abs=5e-6)    # out:166


@pytest.mark.parametrize("t_nm,layers", [(1.0, 3.252), (1.5, 4.878), (2.0, 6.504), (3.0, 9.755)])
def test_consumed_layers_continuum_equal_e9(t_nm, layers):
    """f(2.20) t_ox/(a/4), E9 out:125-128 (3 decimals); the nearest whole count is required."""
    N = int(np.floor(layers + 0.5))
    st = ox.terrace_stacks(spec(thickness_A=10 * t_nm, consumed_layers=N), terrace_heights_A=[0.0],
                           a_A=A_SI_A, crystal="atomistic")
    p = st["per_terrace"][0]
    assert p["consumed_layers_continuum"] == pytest.approx(layers, abs=5e-4)
    assert abs(p["interface_quantisation_A"]) <= Q / 2


def test_two_nm_stack_equals_e9():
    """2 nm at 2.20 g/cm^3: interface 8.8301 A down, top 11.1699 A up (out:143) from the
    pre-oxidation surface: the boundary of a continuum crystal, and the Si equivalent boundary a/8
    above the top atomic plane of an atomistic one (audit A8 M2), whose kept top plane is 7 layers
    down."""
    p = ox.terrace_stacks(spec(), terrace_heights_A=[5.0], a_A=A_SI_A,
                          crystal="continuum")["per_terrace"][0]
    assert 5.0 - p["interface_x_A"] == pytest.approx(8.8301, abs=5e-5)
    assert p["top_x_A"] - 5.0 == pytest.approx(11.1699, abs=5e-5)
    assert p["crystal_boundary_x_A"] == p["interface_x_A"]                 # no amorphous Si
    assert p["atomistic_crystal_top_x_A"] is None and p["interface_overlap_A"] == 0.0
    a = ox.terrace_stacks(spec(), terrace_heights_A=[5.0], a_A=A_SI_A,
                          crystal="atomistic")["per_terrace"][0]
    assert a["pre_oxidation_plane_x_A"] == 5.0
    assert a["pre_oxidation_surface_x_A"] == pytest.approx(5.0 + Q / 2, abs=1e-12)
    assert a["pre_oxidation_surface_x_A"] - a["interface_x_A"] == pytest.approx(8.8301, abs=5e-5)
    assert a["top_x_A"] - a["pre_oxidation_surface_x_A"] == pytest.approx(11.1699, abs=5e-5)
    assert a["atomistic_crystal_top_x_A"] == pytest.approx(5.0 - 7 * Q, abs=1e-12)


def test_amorphous_si_moves_the_crystal_boundary():
    s = spec(amorphous_si_thickness_A=10.0, consumed_layers=14, amorphous_si_V_real_V=13.6,
             amorphous_si_V_imag_V=0.47, labels=dict({k: L12 for k in KEYS},
                                                     amorphous_si_potential=L12))
    p = ox.terrace_stacks(s, terrace_heights_A=[0.0], a_A=A_SI_A,
                          crystal="atomistic")["per_terrace"][0]
    assert p["interface_x_A"] - p["crystal_boundary_x_A"] == pytest.approx(10.0)
    assert abs(14 * Q - (8.8301 + 10.0)) <= Q / 2


# --------------------------------------------------------------------------------------------------
# Builder: (o1)-(o4)
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("az", [(1, 0, 0), (1, 1, 0)])
def test_conformal_oxide_on_the_staircase(az):
    s0 = build(None, az=az)
    s = build(spec(), az=az)
    o = s.metadata["options"]["overlayer"]
    assert o["value"] == "continuum_oxide" and o["conformal"] is True
    assert o["spec_sha256"] == ox.spec_sha256(spec())
    # (o1): 7 whole layers per terrace removed; the ideal count is the clean builder's
    assert s.metadata["ideal_atom_count_before_consumption"] == s0.n_atoms
    removed = sum(p["removed_atoms"] for p in o["per_terrace"])
    assert s.n_atoms == s0.n_atoms - removed and s.metadata["expected_atom_count"] == s.n_atoms
    per_layer = [np.count_nonzero((s0.terrace_index == k) & (s0.layer_index == 0))
                 for k in range(3)]
    assert [p["removed_atoms"] for p in o["per_terrace"]] == [7 * n for n in per_layer]
    # (o2): kept tops measured at tops - 7
    for k, p in enumerate(o["per_terrace"]):
        H = s.metadata["terrace_map"][k]["top_height_A"]
        assert p["pre_oxidation_plane_x_A"] == H
        assert s.positions_A[s.terrace_index == k, 0].max() == pytest.approx(H - 7 * Q, abs=1e-9)
        # (o4): an odd number of consumed layers swaps the terrace type (E9 section 3 item 2)
        assert p["buried_terrace_type_swapped"] is True
    # (o3): buried relations equal the ideal ones for a conformal layer
    for st in s.metadata["steps"]:
        ov = st["overlayer"]
        assert ov["conformal_at_step"] and ov["buried_relation"] == st["type"]
        assert ov["buried_b4"] == st["relation"]["model_assumption_B4"]
        assert ov["buried_delta_layers"] == st["delta_layers"]
    assert any(a.startswith("(o3)") for a in s.metadata["assertions_passed"])
    if az == (1, 1, 0):
        assert "parity of the consumed-layer count" in s.metadata["steps"][1]["overlayer"][
            "model_assumption_B4_overlayer"]


def test_even_consumed_layer_count_keeps_the_terrace_type():
    s = build(spec(thickness_A=18.45, consumed_layers=6))       # f t = 8.146 A = 6.0 layers
    assert all(p["buried_terrace_type_swapped"] is False
               for p in s.metadata["options"]["overlayer"]["per_terrace"])


def test_one_extra_consumed_layer_changes_the_buried_step():
    """E9 section 3 item 5: one extra consumed layer (t + (a/4)/f) on terrace 1 turns the a/2 up-
    step 0 -> 1 into an a/4 buried step and the a/4 down-step 1 -> 2 into a flat buried
    interface."""
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    t1 = 20.0 + Q / f
    s = build(spec(terrace_thickness_A=(20.0, t1, 20.0), terrace_consumed_layers=(7, 8, 7),
                   labels=dict({k: L12 for k in KEYS}, overrides=L12)))
    o = s.metadata["options"]["overlayer"]
    assert o["conformal"] is False
    st = {x["index"]: x["overlayer"] for x in s.metadata["steps"]}
    assert st[0]["buried_delta_layers"] == 1 and st[0]["buried_relation"] == "screw"
    assert st[1]["buried_delta_layers"] == 0 and st[1]["buried_relation"] == "none"
    assert not st[0]["conformal_at_step"] and st[2]["conformal_at_step"]


def test_overlayer_absent_is_the_clean_builder():
    s1, s2 = build(None), build(None)
    assert s1.metadata["positions_sha256"] == s2.metadata["positions_sha256"]
    assert "ideal_atom_count_before_consumption" not in s1.metadata
    assert all("overlayer" not in st for st in s1.metadata["steps"])
    assert all("oxide" not in t for t in s1.metadata["terrace_map"])


# --------------------------------------------------------------------------------------------------
# Refusals: every missing or inconsistent input (test (e))
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("field", [f.name for f in dataclasses.fields(ox.ContinuumOxideSpec)])
def test_every_field_is_required(field):
    kw = {f.name: getattr(spec(), f.name) for f in dataclasses.fields(ox.ContinuumOxideSpec)}
    kw.pop(field)
    with pytest.raises(TypeError):
        ox.ContinuumOxideSpec(**kw)


@pytest.mark.parametrize("kw,match", [
    (dict(thickness_A=0.0), "thickness_A"),
    (dict(thickness_A=None), "thickness_A"),
    (dict(density_g_cm3=-1.0), "density"),
    (dict(consumed_layers=6), "nearest whole count is 7"),
    (dict(consumed_layers=7.0), "integer"),
    (dict(V_real_V=0.0), "V_ox"),
    (dict(V_imag_V=-0.1), "V'_ox"),
    (dict(V_imag_V=0.0, labels=dict({k: L12 for k in KEYS},
                                    V_imag="PROJECT_INPUT item 12")), "ASSUMPTION"),
    (dict(vacuum_edge_width_A=0.3), "graded over at least 0.5"),
    (dict(vacuum_edge_width_A=0.0), "graded over at least 0.5"),
    (dict(vacuum_edge_width_A=0.0, sharp_edge_test_flag=True,
          labels=dict({k: L12 for k in KEYS}, vacuum_edge="ASSUMPTION sharp")), "TEST_ONLY"),
    (dict(sharp_edge_test_flag=True), "not needed"),
    (dict(sharp_edge_test_flag=1), "True or False"),
    (dict(interface_width_A=-0.5), "interface_width_A"),
    (dict(amorphous_si_thickness_A=-1.0), "amorphous_si_thickness_A"),
    # audit A8 M1 (changed on purpose, report X4): a-Si = 0 labelled PROJECT_INPUT (a measured
    # zero) is now ACCEPTED (tests/structure/test_oxide_structure_a8_fixes.py); an unlabelled zero is refused
    (dict(labels=dict({k: L12 for k in KEYS}, amorphous_si=" ")), "label"),
    (dict(amorphous_si_V_real_V=13.6), "must be None"),
    (dict(amorphous_si_thickness_A=10.0, consumed_layers=14,
          labels=dict({k: L12 for k in KEYS}, amorphous_si_potential=L12)),
     "amorphous_si_V_real_V"),
    (dict(labels={k: L12 for k in KEYS if k != "density"}), "exactly the keys"),
    (dict(labels=dict({k: L12 for k in KEYS}, density="guess")), "label"),
    (dict(labels=dict({k: L12 for k in KEYS}, density="DERIVED_HERE")), "label"),
    (dict(terrace_thickness_A=(20.0, 20.0, 20.0)), "exactly the keys"),
    (dict(material=" "), "material"),
])
def test_invalid_or_missing_inputs_are_refused(kw, match):
    with pytest.raises(ValueError, match=match):
        ox.terrace_stacks(spec(**kw), terrace_heights_A=[0.0], a_A=A_SI_A, crystal="atomistic")


def test_override_length_must_match_the_terraces():
    s = spec(terrace_consumed_layers=(7, 7), labels=dict({k: L12 for k in KEYS}, overrides=L12))
    with pytest.raises(ValueError, match="one entry per terrace"):
        build(s)


def test_labels_must_be_a_mapping():
    with pytest.raises(TypeError):
        ox.validate_spec(spec(labels=[L12] * len(KEYS)))


def test_builder_refusals():
    with pytest.raises(ValueError, match="cannot hold the continuum oxide"):
        build(spec(), vacuum_above_A=10.0)
    with pytest.raises(ValueError, match="substrate_layers too small"):
        build(spec(), substrate_layers=8)
    with pytest.raises(NotImplementedError, match="overlayer"):
        build(spec(), layers=(0,), widths=(4,), boundary=0, termination="p(2x1)s",
              substrate_layers=16)
    with pytest.raises(TypeError):
        build({"model": "continuum_oxide"})
