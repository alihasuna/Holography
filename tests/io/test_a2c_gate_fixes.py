"""Regression tests of the A2c gate findings G1 and G2 (docs/agent_reports/A2c_verification.md;
report docs/agent_reports/S4_pipeline_fixes.md). Scratch probe of the auditor: r5b_registry_bypass.py.

G1: Ali's Si(001)/[110]/(008) experiment loaded as the CFG-A benchmark, with its imaging inputs
labelled DERIVED_HERE, passed at run level: the CFG-B gate was avoided by the configuration name.
Now CFG-A is defined by material Si, surface (1,-1,1) and azimuth [1,1,0] (any other value refused),
and its imaging inputs carry their docs/06 items, so they pass the PROJECT_INPUT gate like CFG-B's.
G2: the PROJECT_INPUT supplier rule was a substring match on free text ("not supplied by Ali
2026-09-22", "supplied by nobody 2099-12-31" and "guess; supplied by the simulation 2026-09-22"
passed). Now a supplied value needs the structured fields supplied_by (a name) and supplied_on (an
ISO date, not in the future).
In-memory fixtures only; shipped files are read, never written.
"""
import copy
import datetime as dt
from pathlib import Path

import pytest
import yaml

from reflection_holo.io.config import ConfigError, load_config_dict, load_config_file

REPO = Path(__file__).resolve().parents[2]
CFG_A = REPO / "configs" / "cfg_a_si111_cleaved_110azimuth.yaml"
CFG_B = REPO / "configs" / "cfg_b_si001_patterned.yaml"


def raw(path):
    return yaml.safe_load(path.read_text())


def _cfg_a_as_si001_experiment(label="DERIVED_HERE"):
    """r5b: the shipped CFG-A with normal [0,0,1], azimuth [1,1,0], target (0,0,8), the Si(001)
    forbidden list, and imaging inputs (glancing angle 16.47 mrad, convergence 0, aperture 1 mrad,
    pixel 0.5 A, reference trajectory) labelled DERIVED_HERE."""
    d = raw(CFG_A)
    P = d["parameters"]
    P["surface_normal_hkl"]["value"] = [0, 0, 1]
    P["beam_azimuth_uvw"]["value"] = [1, 1, 0]
    P["target_reflection_hkl"]["value"] = [0, 0, 8]
    P["recommended_reflections_hkl"]["value"] = [[0, 0, 8]]
    P["not_recommended_reflections_hkl"]["value"] = [[0, 0, 4]]
    P["forbidden_rod_reflections_hkl"]["value"] = [[0, 0, 2], [0, 0, 6], [0, 0, 10]]
    for name, value, unit in (("glancing_angle_ext", 16.47, "mrad"),
                              ("convergence_semi_angle", 0.0, "mrad"),
                              ("objective_aperture_semi_angle", 1.0, "mrad"),
                              ("image_pixel_size", {"along_beam": 0.5, "perpendicular": 0.5}, "A"),
                              ("reference_trajectory", "vacuum_beside_sample", "none")):
        P[name] = dict(value=value, unit=unit, label=label, source="audit r5b: not a lab value")
    return d


def test_si001_experiment_declared_as_cfg_a_is_refused():
    with pytest.raises(ConfigError, match="CFG-A is defined by surface_normal_hkl"):
        load_config_dict(_cfg_a_as_si001_experiment(), level="run")


@pytest.mark.parametrize("name,value", [("surface_normal_hkl", [1, 1, 1]),
                                        ("beam_azimuth_uvw", [1, 0, -1]),
                                        ("surface_material", "Pt")])
def test_cfg_a_defining_values_are_pinned(name, value):
    d = raw(CFG_A)
    d["parameters"][name]["value"] = value
    with pytest.raises(ConfigError, match=name):
        load_config_dict(d, level="placeholder")


def test_cfg_b_surface_is_pinned_to_001():
    d = raw(CFG_B)
    d["parameters"]["surface_normal_hkl"]["value"] = [1, -1, 1]
    with pytest.raises(ConfigError, match="CFG-B is defined by surface_normal_hkl"):
        load_config_dict(d, level="placeholder")


@pytest.mark.parametrize("label", ["DERIVED_HERE", "SECTION_READ", "REPRODUCED",
                                   "METADATA_VERIFIED"])
def test_cfg_a_imaging_inputs_pass_the_project_input_gate(label):
    """CFG-A geometry correct, imaging inputs present with a non-laboratory label: refused like
    CFG-B's (items 3, 4, 5, 7, 15)."""
    d = raw(CFG_A)
    d["parameters"]["glancing_angle_ext"] = dict(value=16.47, unit="mrad", label=label,
                                                 source="audit: not a lab value")
    with pytest.raises(ConfigError, match="item"):
        load_config_dict(d, level="placeholder")
    d["parameters"]["glancing_angle_ext"].update(item=7)
    with pytest.raises(ConfigError, match="PROJECT_INPUT item 7"):
        load_config_dict(d, level="placeholder")


def test_cfg_a_imaging_input_supplied_is_accepted():
    d = raw(CFG_A)
    d["parameters"]["glancing_angle_ext"] = dict(
        value=16.47, unit="mrad", label="PROJECT_INPUT", item=7, supplied_by="Ali",
        supplied_on="2026-09-22", source="TEST fixture: fabricated supply")
    cfg = load_config_dict(d, level="run")
    assert cfg.parameters["glancing_angle_ext"].supply == {"supplied_by": "Ali",
                                                           "supplied_on": "2026-09-22"}
    load_config_file(CFG_A, level="run")                     # the shipped benchmark still loads


# --------------------------------------------------------------------------------------------------
# G2
# --------------------------------------------------------------------------------------------------
FILL = {"beam_azimuth_uvw": [1, 1, 0], "glancing_angle_ext": 16.47, "convergence_semi_angle": 0.0,
        "objective_aperture_semi_angle": 1.0,
        "image_pixel_size": {"along_beam": 0.5, "perpendicular": 0.5},
        "reference_trajectory": "vacuum_beside_sample", "pattern_geometry": {"mesa_height": 10.0},
        "surface_preparation_details": {"oxide": "none"}}


def _filled(source, **supply):
    d = raw(CFG_B)
    for k, v in FILL.items():
        d["parameters"][k].update(value=v, label="PROJECT_INPUT", source=source, **supply)
    return d


@pytest.mark.parametrize("source", ["not supplied by Ali 2026-09-22",
                                    "supplied by nobody 2099-12-31",
                                    "guess; supplied by the simulation 2026-09-22"])
def test_free_text_supplier_sentences_no_longer_pass(source):
    """A2c G2, r5b: these three sources passed the run level with the free-text rule."""
    with pytest.raises(ConfigError, match="supplied_by"):
        load_config_dict(_filled(source), level="run")


@pytest.mark.parametrize("who,when,match", [
    ("nobody", "2026-09-22", "does not name a person"),
    ("the simulation", "2026-09-22", "does not name a person"),
    ("not Ali", "2026-09-22", "does not name a person"),
    ("", "2026-09-22", "non-empty name"),
    ("Ali", "2026-02-30", "not a valid date"),
    ("Ali", "22.09.2026", "ISO date"),
    ("Ali", "FUTURE", "in the future"),
])
def test_structured_supply_fields_are_checked(who, when, match):
    if when == "FUTURE":
        from reflection_holo.io.config import latest_today
        when = (latest_today() + dt.timedelta(days=1)).isoformat()
    with pytest.raises(ConfigError, match=match):
        load_config_dict(_filled("docs/06 logbook", supplied_by=who, supplied_on=when),
                         level="run")


def test_structured_supply_accepted_and_recorded():
    d = _filled("docs/06 logbook", supplied_by="Ali", supplied_on="2026-09-23")
    cfg = load_config_dict(d, level="run")
    assert cfg.missing_project_inputs == []
    assert cfg.parameters["beam_azimuth_uvw"].supply == {"supplied_by": "Ali",
                                                         "supplied_on": "2026-09-23"}
    e = _filled("docs/06 logbook", supplied_by="Ali", supplied_on=dt.date(2026, 9, 23))
    load_config_dict(e, level="run")                         # a YAML date is accepted too


def test_supply_fields_only_on_a_supplied_project_input():
    d = raw(CFG_B)
    d["parameters"]["mean_inner_potential_V"].update(supplied_by="Ali", supplied_on="2026-09-22")
    with pytest.raises(ConfigError, match="only for a PROJECT_INPUT with a value"):
        load_config_dict(copy.deepcopy(d), level="placeholder")
    d = raw(CFG_B)
    d["parameters"]["beam_azimuth_uvw"].update(supplied_by="Ali", supplied_on="2026-09-22")
    with pytest.raises(ConfigError, match="only for a PROJECT_INPUT with a value"):
        load_config_dict(d, level="placeholder")                 # null PROJECT_INPUT
