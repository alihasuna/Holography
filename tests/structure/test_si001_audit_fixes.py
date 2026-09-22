"""Si(001) builder: B4 metadata by azimuth, explicit lattice parameter, integer boundary step
(audit A2 findings m3, m6 and a NIT; scratch scripts e12 and e12b).

m3: the unfixed builder recorded "B4 does NOT apply (4_1 screw-related terraces)" for every a/4 step,
also at an exact <100> azimuth where it found the incidence-plane glide itself (92 steps of the
auditor's sweep). C2 section 1 derives that at <100> the bulk-terminated terraces are related by the
(010)/(100) d-glide that fixes k_in and k_out, so B4 applies there (model_assumptions B4; SM26).
m6: the builder used constants.A_SI_A hard-coded, whatever the configuration said.
NIT: validate_staircase truncated a non-integer boundary step (-1.5 -> -1).
"""
import inspect
from pathlib import Path

import numpy as np
import pytest
import yaml

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import Staircase, build_si001_terraces, validate_staircase
from reflection_holo.structure import si001
from si001_test_inputs import AZIMUTH_LABEL, LATTICE_LABEL, build

B4_100 = "B4 applies for bulk-terminated terraces (d-glide in the incidence plane; SM26, C2)"
B4_110 = "does not apply (dynamical residual delta; open question 3)"
B4_A2 = "applies far from the riser (pure translation)"
MIXED = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(3, 3, 3),
                  boundary_step_layers=-1)                  # a/2 up, a/4 down, a/4 down at the edge


@pytest.mark.parametrize("az", [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)])
def test_b4_applies_to_a4_steps_at_an_exact_100_azimuth(az):
    s = build(MIXED, azimuth=az)
    kinds = [(x["type"], x["relation"]["model_assumption_B4"],
              x["relation"]["incidence_plane_mirror_operations"]) for x in s.metadata["steps"]]
    assert [k for k, _, _ in kinds] == ["translation", "screw", "screw"]
    for kind, b4, ops in kinds:
        if kind == "screw":
            assert ops and b4 == B4_100
        else:
            assert b4 == B4_A2


@pytest.mark.parametrize("az", [(1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0)])
def test_b4_does_not_apply_to_a4_steps_at_110(az):
    s = build(MIXED, azimuth=az)
    for x in s.metadata["steps"]:
        want = B4_110 if x["type"] == "screw" else B4_A2
        assert x["relation"]["model_assumption_B4"] == want
        if x["type"] == "screw":
            assert x["relation"]["incidence_plane_mirror_operations"] == []


def test_b4_statement_for_other_azimuths_and_missing_glide():
    assert si001.b4_statement("screw", (2, 1, 0), ["mirror(010)"]) == "does not apply"
    assert si001.b4_statement("screw", (1, 0, 0), []) == "does not apply"   # no glide measured
    assert si001.b4_statement("translation", (2, 1, 0), []) == B4_A2


def test_cfg_b_relation_comment_matches_b4():
    path = Path(__file__).resolve().parents[2] / "configs" / "cfg_b_si001_patterned.yaml"
    rel = yaml.safe_load(path.read_text())["parameters"]["step_translations"]["value"][
        "single_layer"]["relation"]
    # round 2 (review E4 M1): the relation carries the scope clause of the <100> result
    assert ("of a plane wave at the exact <100> azimuth, bulk-terminated a/4 terraces reflect "
            "identically up to exp(-i (k_out - k_in).t) (C2 section 1.3; SM26)") in rel
    assert "at <110> the residual is not forced to vanish (value unknown, open question 3)" in rel
    assert "screw-related terraces, dynamical difference expected" not in path.read_text()


def test_lattice_parameter_is_an_explicit_labelled_argument():
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(2, 2),
                   boundary_step_layers=-1)
    a = 5.431                                   # the inspected repository's meta_tilt value
    s = build(st, lattice_parameter_A=a, lattice_parameter_label="TEST_ONLY: 5.431 A")
    assert s.metadata["lattice"]["a_A"] == a
    assert s.metadata["lattice"]["a_label"] == "TEST_ONLY: 5.431 A"
    tops = [t["top_height_A"] for t in s.metadata["terrace_map"]]
    assert tops[1] - tops[0] == pytest.approx(a / 4, abs=1e-12)
    assert np.max(s.positions_A[:, 0]) == pytest.approx(max(tops), abs=1e-12)
    s0 = build(st)
    assert s0.metadata["lattice"]["a_A"] == A_SI_A and s0.metadata["lattice"]["a_label"] == LATTICE_LABEL
    sig = inspect.signature(build_si001_terraces).parameters
    assert "lattice_parameter_A" in sig and "lattice_parameter_label" in sig
    for fn in (si001.validate_staircase, si001.assert_step_heights, si001.is_diamond_symmetry,
               si001.find_terrace_relations, si001.classify_relation):
        assert inspect.signature(fn).parameters["a_A"].default is inspect.Parameter.empty, fn
    assert not hasattr(si001, "A_SI_A")          # the builder module does not bind the constant
    for bad_label in ("", "5.431", None):
        with pytest.raises(ValueError, match="label"):
            build(st, lattice_parameter_A=a, lattice_parameter_label=bad_label)
    for bad in (0.0, -5.4, np.nan):
        with pytest.raises(ValueError, match="lattice_parameter_A"):
            build(st, lattice_parameter_A=bad, lattice_parameter_label="TEST_ONLY: bad")


@pytest.mark.parametrize("b", [-1.5, 0.5, True])
def test_boundary_step_must_be_an_integer(b):
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(3, 3),
                   boundary_step_layers=b)
    with pytest.raises(ValueError, match="integer"):
        validate_staircase(st, A_SI_A)
    assert AZIMUTH_LABEL                          # the helper module is the one used above
