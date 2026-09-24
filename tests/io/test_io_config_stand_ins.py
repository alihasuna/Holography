"""PROJECT_INPUT stand-ins and the assumption registry (re-audit A2b findings N1, N8, N9).

The re-auditor's case (A2b N1, scratch script r5_gate_bypass.py): the eight null blocking inputs of
the shipped CFG-B (items 3, 4, 5, 7, 8, 12, 13, 15) filled with non-laboratory values labelled
DERIVED_HERE, SECTION_READ, REPRODUCED or METADATA_VERIFIED, or ASSUMPTION with an unrelated but
existing row (A3, B2, B17), passed the run-level gate. Now a parameter whose schema names a docs/06
item accepts only
  * PROJECT_INPUT: null (missing; fails at run level), or a value with the structured supply
    fields supplied_by (a name) and supplied_on (an ISO date, not in the future); A2c G2 replaced
    the former free-text rule "supplied by <name> <YYYY-MM-DD>" in the source;
  * ASSUMPTION with stands_in_for_item equal to that item and an assumption_id that the package
    registry reflection_holo/io/assumption_registry.yaml maps to that item (B1 -> 20, B17 -> 9,
    B18 -> 14);
  * TEST_ONLY, in in-memory test fixtures only (never from a file).
Any other label fails. N8: non-finite numbers fail. N9: the registry is package data, not docs/.
Shipped files under configs/ are read, never written.
"""
import copy
import importlib.resources
from pathlib import Path

import pytest
import yaml

from reflection_holo.io import config as C
from reflection_holo.io.config import ConfigError, load_config_dict, load_config_file

REPO = Path(__file__).resolve().parents[2]
CFG_A = REPO / "configs" / "cfg_a_si111_cleaved_110azimuth.yaml"
CFG_B = REPO / "configs" / "cfg_b_si001_patterned.yaml"
FILL = {"beam_azimuth_uvw": [1, 1, 0], "glancing_angle_ext": 16.47, "convergence_semi_angle": 0.0,
        "objective_aperture_semi_angle": 1.0,
        "image_pixel_size": {"along_beam": 0.5, "perpendicular": 0.5},
        "reference_trajectory": "vacuum_beside_sample", "pattern_geometry": {"mesa_height": 10.0},
        "surface_preparation_details": {"oxide": "none"}}


def raw(path):
    return yaml.safe_load(path.read_text())


def filled(label, source="audit: not a laboratory value", **extra):
    d = raw(CFG_B)
    for k, v in FILL.items():
        d["parameters"][k].update(value=v, label=label, source=source, **extra)
    return d


@pytest.mark.parametrize("label", ["DERIVED_HERE", "SECTION_READ", "REPRODUCED", "METADATA_VERIFIED",
                                   "UNVERIFIED"])
def test_other_labels_cannot_fill_a_project_input_item(label):
    with pytest.raises(ConfigError, match="PROJECT_INPUT item"):
        load_config_dict(filled(label), level="placeholder")


@pytest.mark.parametrize("aid", ["A3", "B2", "B17", "B99", "B1"])
def test_assumption_id_must_map_to_the_item_it_stands_in_for(aid):
    """B17 maps to item 9 and B1 to item 20; none of these maps to items 3-15 filled here."""
    d = raw(CFG_B)
    for k, v in FILL.items():
        p = d["parameters"][k]
        p.update(value=v, label="ASSUMPTION", source="audit", stands_in_for_item=p["item"],
                 assumption_id=aid)
    with pytest.raises(ConfigError, match="registry"):
        load_config_dict(d, level="placeholder")


def test_registered_stand_ins_of_the_shipped_configs_pass():
    b = load_config_file(CFG_B, level="placeholder")
    got = {n: (p.assumption_id, p.stands_in_for_item) for n, p in b.parameters.items()
           if p.label == "ASSUMPTION" and p.stands_in_for_item is not None}
    assert got == {"mean_inner_potential_V": ("B1", 20), "target_reflection_hkl": ("B17", 9),
                   "second_reflection_hkl": ("B17", 9), "step_types": ("B18", 14)}
    load_config_file(CFG_A, level="run")


@pytest.mark.parametrize("supply,ok", [
    ({}, False),                                              # no supply record
    ({"supplied_by": "Ali"}, False),                          # no date
    ({"supplied_by": "Ali", "supplied_on": "2026-13-40"}, False),   # not a date
    ({"supplied_on": "2026-09-23"}, False),                   # no supplier
    ({"supplied_by": "Ali", "supplied_on": "2026-09-23"}, True),
])
def test_project_input_value_names_supplier_and_date(supply, ok):
    """The same cases as before A2c G2, in the structured form that replaced the free-text rule
    (the free-text sentences themselves are tested in test_a2c_gate_fixes.py)."""
    d = filled("PROJECT_INPUT", source="docs/06 logbook", **supply)
    if ok:
        cfg = load_config_dict(d, level="run")
        assert cfg.missing_project_inputs == []
    else:
        with pytest.raises(ConfigError, match="supplied_by|supplied_on|date"):
            load_config_dict(d, level="placeholder")


def test_registry_is_package_data_mapping_ids_to_items():
    res = importlib.resources.files("reflection_holo.io").joinpath("assumption_registry.yaml")
    assert res.is_file()
    reg = C.assumption_registry()
    assert reg == {"B1": (20,), "B17": (9,), "B18": (14,),
                   # Phase 3 demo stand-ins (docs/model_assumptions.md B19-B32)
                   "B19": (7,), "B20": (8,), "B21": (3,), "B22": (4,), "B23": (5,), "B24": (6,),
                   "B25": (11,), "B26": (12,), "B27": (13,), "B28": (15, 16), "B29": (19,),
                   "B30": (21,), "B31": (1,), "B32": (7,),
                   "B33": (13,), "B34": (13,),
                   # report E2: demo stand-in specimen temperature (docs/06 item 23)
                   "B36": (23,),
                   # report E3: demo stand-ins of the surface-plasmon excitation number (item 21),
                   # the loss-electron visibility (item 16) and a convergent illumination with the
                   # R1 object-reference separation (items 3 and 16)
                   "B38": (21,), "B39": (16,), "B40": (3, 16),
                   # report E4: demo continuum oxide (docs/06 item 12; L8 section 8 with E9)
                   "B41": (12,)}
    assert "B36" in C.demo_only_stand_ins()
    assert {"B38", "B39", "B40"} <= C.demo_only_stand_ins()
    assert "B41" in C.demo_only_stand_ins()
    # report E2: rows cited by code that stand in for no docs/06 item (never an assumption_id)
    assert set(C.model_assumption_rows()) == {"B35", "B37"}
    assert not set(C.model_assumption_rows()) & set(reg)
    assert not any(k.startswith("A") for k in reg)            # inherited A-rows never stand in
    assert "B2" not in reg                                    # the lattice parameter is no stand-in
    assert all(C.SCHEMAS[c][kind].get("lattice_parameter") is None      # no docs/06 item anywhere
               for c in C.SCHEMAS for kind in ("required", "optional"))
    assert not hasattr(C, "MODEL_ASSUMPTIONS_PATH")           # nothing is read from docs/


def test_registry_ids_exist_in_model_assumptions():
    path = REPO / "docs" / "model_assumptions.md"
    if not path.is_file():
        pytest.skip("docs/model_assumptions.md is absent (installed package without docs/)")
    rows = {line.split("|")[1].strip() for line in path.read_text().splitlines()
            if line.startswith("| ") and len(line.split("|")) > 2}
    for aid in list(C.assumption_registry()) + list(C.model_assumption_rows()):
        assert aid in rows, aid


def test_assumption_id_on_a_parameter_without_item_is_refused():
    d = raw(CFG_A)
    d["parameters"]["lattice_parameter"]["assumption_id"] = "B2"
    with pytest.raises(ConfigError, match="assumption_id"):
        load_config_dict(d, level="placeholder")


@pytest.mark.parametrize("name,value", [
    ("glancing_angle_ext", float("inf")), ("glancing_angle_ext", float("nan")),
    ("lattice_parameter", float("inf")), ("convergence_semi_angle", float("-inf")),
    ("image_pixel_size", {"along_beam": float("nan"), "perpendicular": 0.5})])
def test_non_finite_values_are_refused(name, value):
    d = filled("PROJECT_INPUT", source="docs/06 logbook", supplied_by="Ali",
               supplied_on="2026-09-23")
    d["parameters"][name]["value"] = value
    with pytest.raises(ConfigError, match="finite"):
        load_config_dict(copy.deepcopy(d), level="placeholder")
