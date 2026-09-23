"""Run-level PROJECT_INPUT gate, units and material names (audit A2 findings M2, m4, m5, m10).

The shipped files under configs/ are READ here (never written); every modified copy is written to
pytest's tmp_path. The auditor's cases (A2 M2, scratch script e5; m10, e5b) are reproduced:
(a) the null PROJECT_INPUT entries of CFG-B deleted, (b) a blocking input filled by an unlinked
ASSUMPTION value, (c) duplicate YAML keys, (d) a three-parameter CFG-A at run level; a material
spelling that skipped the Si cross-checks; CFG-A repository defaults labelled PROJECT_INPUT; units.
"""
import copy
import math
from pathlib import Path

import pytest
import yaml

from reflection_holo.io.config import (ConfigError, MissingProjectInputError,
                                       MissingRequiredParameterError, PlaceholderConfigError,
                                       SCHEMAS, UNITS, load_config_dict, load_config_file)

REPO = Path(__file__).resolve().parents[2]
CFG_A = REPO / "configs" / "cfg_a_si111_cleaved_110azimuth.yaml"
CFG_B = REPO / "configs" / "cfg_b_si001_patterned.yaml"
CFG_O = REPO / "configs" / "cfg_o_osakabe_1988_reproduction.yaml"
CFG_B_BLOCKING = [3, 4, 5, 7, 8, 12, 13, 15]


def raw(path):
    return yaml.safe_load(path.read_text())


def write(tmp_path, path, data=None, text=None):
    out = tmp_path / path.name
    out.write_text(text if text is not None else yaml.safe_dump(data, sort_keys=False))
    return out


def test_shipped_configurations_at_both_levels():
    a = load_config_file(CFG_A, level="run")
    assert a.missing_project_inputs == [] and a.missing_required == []
    with pytest.raises(MissingProjectInputError) as exc:
        load_config_file(CFG_B, level="run")
    assert exc.value.items == CFG_B_BLOCKING
    b = load_config_file(CFG_B, level="placeholder")
    assert [i for _, i in b.missing_project_inputs] == CFG_B_BLOCKING
    with pytest.raises(PlaceholderConfigError):
        load_config_file(CFG_O, level="run")
    load_config_file(CFG_O, level="placeholder")


def test_omitted_project_inputs_fail_like_nulls(tmp_path):
    """(a) Deleting the eight null PROJECT_INPUT entries of CFG-B must not turn the refusal into a
    PASS: absent required parameters fail at run level exactly like null ones, naming the items."""
    d = raw(CFG_B)
    dropped = [k for k, v in d["parameters"].items() if v["value"] is None]
    assert len(dropped) == 8
    for k in dropped:
        del d["parameters"][k]
    f = write(tmp_path, CFG_B, d)
    with pytest.raises(MissingProjectInputError, match=r"absent") as exc:
        load_config_file(f, level="run")
    assert exc.value.items == CFG_B_BLOCKING and sorted(exc.value.names) == sorted(dropped)
    cfg = load_config_file(f, level="placeholder")
    assert [i for _, i in cfg.missing_project_inputs] == CFG_B_BLOCKING
    assert sorted(n for n, _ in cfg.missing_required) == sorted(dropped)
    with pytest.raises(MissingProjectInputError, match="item 7"):
        cfg.value("glancing_angle_ext")


@pytest.mark.parametrize("extra,match", [
    ({}, "must name its docs/06 item 7"),                                           # no item at all
    ({"item": 7}, "stands_in_for_item"),                                            # not linked
    ({"item": 7, "stands_in_for_item": 7}, "assumption_id"),                        # no row
    ({"item": 7, "stands_in_for_item": 7, "assumption_id": "B99"}, "B99"),          # not a row
    ({"item": 7, "stands_in_for_item": 8, "assumption_id": "B1"}, "stands_in_for_item"),
])
def test_assumption_standing_in_for_a_project_input_must_be_traceable(tmp_path, extra, match):
    """(b) A blocking input filled by an ASSUMPTION value (16.47 mrad) must carry its docs/06 item,
    stands_in_for_item and an existing model_assumptions row, else it fails at every level."""
    d = raw(CFG_B)
    d["parameters"]["glancing_angle_ext"] = dict(value=16.47, unit="mrad", label="ASSUMPTION",
                                                 source="guess", **extra)
    with pytest.raises(ConfigError, match=match):
        load_config_file(write(tmp_path, CFG_B, d), level="placeholder")


def test_zero_convergence_assumption_without_item_fails(tmp_path):
    d = raw(CFG_B)
    d["parameters"]["convergence_semi_angle"] = dict(value=0.0, unit="mrad", label="ASSUMPTION",
                                                     source="ideal")
    with pytest.raises(ConfigError, match="item 3"):
        load_config_file(write(tmp_path, CFG_B, d), level="placeholder")


def test_traceable_assumption_is_accepted_and_recorded():
    b = load_config_file(CFG_B, level="placeholder")
    v0 = b.parameters["mean_inner_potential_V"]
    assert (v0.label, v0.item, v0.stands_in_for_item, v0.assumption_id) == ("ASSUMPTION", 20, 20, "B1")


def test_duplicate_yaml_keys_fail(tmp_path):
    """(c) PyYAML keeps the last of duplicate keys silently; the loader refuses them."""
    txt = CFG_B.read_text()
    old = "  beam_azimuth_uvw:\n    value: null\n"
    assert txt.count(old) == 1
    bad = txt.replace(old, "  beam_azimuth_uvw:\n    value: null\n    value: [1, 1, 0]\n")
    with pytest.raises(ConfigError, match="duplicate key 'value'"):
        load_config_file(write(tmp_path, CFG_B, text=bad), level="placeholder")
    txt_a = CFG_A.read_text() + ("  mean_inner_potential_V:\n    value: 14.0\n    unit: V\n"
                                 "    label: ASSUMPTION\n    source: \"appended later\"\n")
    with pytest.raises(ConfigError, match="duplicate key 'mean_inner_potential_V'"):
        load_config_file(write(tmp_path, CFG_A, text=txt_a), level="run")


def test_three_parameter_cfg_a_fails_at_run_level():
    """(d) The manifest test's former CFG-A fixture (three parameters) loaded at run level."""
    P = lambda v, lab, **kw: dict(value=v, label=lab, **{"source": "TEST_ONLY fixture", **kw})  # noqa: E731
    d = dict(schema_version=1, config_id="CFG-A", name="si111_cleaved_110azimuth",
             status="benchmark", description="TEST_ONLY fixture",
             parameters=dict(surface_material=P("Si", "ASSUMPTION", unit="none"),
                             surface_normal_hkl=P([1, -1, 1], "ASSUMPTION", unit="none"),
                             beam_energy_keV=P(200.0, "PROJECT_INPUT", unit="keV", item=1,
                                               source="docs/06 item 1 (fixture)",
                                               supplied_by="Ali", supplied_on="2026-09-22")))
    with pytest.raises((MissingRequiredParameterError, MissingProjectInputError)):
        load_config_dict(copy.deepcopy(d), level="run", allow_test_only=True)
    cfg = load_config_dict(d, level="placeholder", allow_test_only=True)
    missing = sorted(n for n, _ in cfg.missing_required)
    assert missing == sorted(set(SCHEMAS["CFG-A"]["required"]) - set(d["parameters"]))


def test_missing_required_without_item_fails_at_run_level(tmp_path):
    d = raw(CFG_A)
    del d["parameters"]["step_translations"]
    with pytest.raises(MissingRequiredParameterError, match="step_translations"):
        load_config_file(write(tmp_path, CFG_A, d), level="run")


def test_parameter_outside_the_schema_of_its_configuration_fails():
    d = raw(CFG_O)
    d["parameters"]["surface_preparation_method"] = dict(value="ion-milled", unit="none",
                                                         label="SECTION_READ", source="x")
    with pytest.raises(ConfigError, match="not part of the CFG-O schema"):
        load_config_dict(d, level="placeholder")


# -- m4: repository defaults are not PROJECT_INPUT ----------------------------------------------

def test_cfg_a_repository_defaults_are_labelled_assumption():
    a = load_config_file(CFG_A, level="run")
    for name in ("surface_material", "surface_normal_hkl", "beam_azimuth_uvw"):
        p = a.parameters[name]
        assert p.label == "ASSUMPTION" and "inspected repository default" in p.source, name
    assert all(p.label != "PROJECT_INPUT" or p.item is not None for p in a.parameters.values())


def test_project_input_must_name_a_docs06_item():
    d = raw(CFG_A)
    d["parameters"]["beam_azimuth_uvw"]["label"] = "PROJECT_INPUT"
    with pytest.raises(ConfigError, match="PROJECT_INPUT"):
        load_config_dict(d, level="placeholder")


# -- m5: one unit table, conversion to A and rad -----------------------------------------------

def _cfg_b_with(tmp_path, **params):
    d = raw(CFG_B)
    d["parameters"].update(params)
    return d


def test_units_convert_nm_to_A_and_mrad_to_rad():
    d = raw(CFG_B)
    d["parameters"]["glancing_angle_ext"] = dict(value=16.5, unit="mrad", label="TEST_ONLY",
                                                 source="TEST_ONLY", item=7)
    d["parameters"]["image_pixel_size"] = dict(value={"along_beam": 0.5, "perpendicular": 0.25},
                                               unit="nm", label="TEST_ONLY", source="TEST_ONLY",
                                               item=5)
    cfg = load_config_dict(d, level="placeholder", allow_test_only=True)
    assert cfg.quantity("glancing_angle_ext") == (pytest.approx(0.0165, rel=1e-15), "rad")
    px, unit = cfg.quantity("image_pixel_size")
    assert unit == "A" and px == {"along_beam": pytest.approx(5.0, rel=1e-15),
                                  "perpendicular": pytest.approx(2.5, rel=1e-15)}
    assert cfg.value("glancing_angle_ext") == 16.5                  # the declared value is kept
    assert cfg.quantity("lattice_parameter") == (5.4309, "A")
    assert cfg.quantity("beam_energy_keV") == (200.0, "keV")
    assert UNITS["nm"] == ("length", 10.0) and UNITS["mrad"] == ("angle", 1e-3)
    with pytest.raises(ConfigError, match="no physical unit"):
        cfg.quantity("target_reflection_hkl")


@pytest.mark.parametrize("unit,match", [("furlong", "unknown unit"), ("nm", "angle"),
                                        (None, "unit"), ("deg", "unknown unit")])
def test_unknown_or_wrong_unit_fails(unit, match):
    d = raw(CFG_B)
    spec = dict(value=16.5, label="TEST_ONLY", source="TEST_ONLY", item=7)
    if unit is not None:
        spec["unit"] = unit
    d["parameters"]["glancing_angle_ext"] = spec
    with pytest.raises(ConfigError, match=match):
        load_config_dict(d, level="placeholder", allow_test_only=True)


def test_every_parameter_states_a_unit():
    for path in (CFG_A, CFG_B, CFG_O):
        for name, spec in raw(path)["parameters"].items():
            assert "unit" in spec, (path.name, name)
    d = raw(CFG_A)
    del d["parameters"]["surface_material"]["unit"]
    with pytest.raises(ConfigError, match="unit"):
        load_config_dict(d, level="placeholder")


def test_lattice_parameter_in_nm_is_converted():
    d = raw(CFG_A)
    d["parameters"]["lattice_parameter"].update(value=0.54309, unit="nm")
    cfg = load_config_dict(d, level="run")
    a, unit = cfg.quantity("lattice_parameter")
    assert unit == "A" and math.isclose(a, 5.4309, rel_tol=1e-14)


# -- m10: canonical material symbols only ------------------------------------------------------

@pytest.mark.parametrize("mat", ["silicon", "Si ", "si", "SI", "Pt"])
def test_non_canonical_or_wrong_material_fails_for_silicon_configs(mat):
    """The auditor's bypass: a forbidden target (6,-6,6) and a false 'forbidden' list were accepted
    at run level when surface_material was not spelled exactly 'Si'."""
    d = raw(CFG_A)
    d["parameters"]["surface_material"]["value"] = mat
    d["parameters"]["target_reflection_hkl"]["value"] = [6, -6, 6]
    d["parameters"]["forbidden_rod_reflections_hkl"]["value"] = [[4, -4, 4]]
    with pytest.raises(ConfigError, match="surface_material"):
        load_config_dict(d, level="placeholder")
    d["parameters"]["surface_material"]["value"] = "Si"
    with pytest.raises(ConfigError, match="forbidden"):
        load_config_dict(d, level="placeholder")


def test_cfg_o_material_must_be_pt():
    d = raw(CFG_O)
    d["parameters"]["surface_material"]["value"] = "Si"
    with pytest.raises(ConfigError, match="surface_material"):
        load_config_dict(d, level="placeholder")
