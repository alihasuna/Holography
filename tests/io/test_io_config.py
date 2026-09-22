"""Assertion-based configuration loader (docs/05 sections 0 and 2; docs/06).

Fixtures are IN-MEMORY and labelled TEST_ONLY where they stand in for a PROJECT_INPUT; no file
under configs/ is read by these tests. Includes one configuration-failure test per null
PROJECT_INPUT item of CFG-B (items 3, 4, 5, 7, 8, 12, 13, 15), the 200 keV rule, the CFG-O
placeholder rule, label and schema checks, and the crystallographic cross-checks."""
import copy

import pytest
import yaml

from reflection_holo.io.config import (EVIDENCE_LABELS, ConfigError, MissingProjectInputError,
                                       PlaceholderConfigError, UnverifiedParameterError,
                                       load_config_dict, load_config_file)


def P(value, label, source="TEST_ONLY fixture", **kw):
    d = dict(value=value, label=label, source=source)
    d.update(kw)
    return d


def cfg_b_complete():
    """A CFG-B-like configuration with every blocking input filled by a TEST_ONLY stand-in."""
    return dict(
        schema_version=1, config_id="CFG-B", name="si001_patterned", status="experiment",
        description="TEST_ONLY in-memory fixture",
        parameters=dict(
            surface_material=P("Si", "PROJECT_INPUT", item=11),
            surface_normal_hkl=P([0, 0, 1], "PROJECT_INPUT", item=11),
            beam_azimuth_uvw=P([1, 1, 0], "TEST_ONLY", item=8),
            beam_energy_keV=P(200.0, "PROJECT_INPUT", unit="keV", item=1),
            lattice_parameter_A=P(5.4309, "ASSUMPTION", unit="A"),
            mean_inner_potential_V=P(12.0, "ASSUMPTION", unit="V", item=20),
            target_reflection_hkl=P([0, 0, 8], "ASSUMPTION", item=9),
            second_reflection_hkl=P([0, 0, 12], "ASSUMPTION", item=9),
            forbidden_rod_reflections_hkl=P([[0, 0, 2], [0, 0, 6], [0, 0, 10]], "DERIVED_HERE"),
            glancing_angle_ext_mrad=P(16.5, "TEST_ONLY", unit="mrad", item=7),
            convergence_semi_angle_mrad=P(0.01, "TEST_ONLY", unit="mrad", item=3),
            objective_aperture_semi_angle_mrad=P(1.0, "TEST_ONLY", unit="mrad", item=4),
            image_pixel_size_nm=P({"along_beam": 0.5, "perpendicular": 0.5}, "TEST_ONLY",
                                  unit="nm", item=5),
            reference_trajectory=P("vacuum_beside_sample", "TEST_ONLY", item=15),
            pattern_geometry=P({"mesa_height_nm": 10.0}, "TEST_ONLY", item=13),
            surface_preparation_method=P("ion-milled", "PROJECT_INPUT", item=12),
            surface_preparation_details=P({"oxide": "TEST_ONLY"}, "TEST_ONLY", item=12),
        ))


def cfg_a_fixture():
    return dict(
        schema_version=1, config_id="CFG-A", name="si111_cleaved_110azimuth", status="benchmark",
        description="TEST_ONLY in-memory fixture",
        parameters=dict(
            surface_material=P("Si", "PROJECT_INPUT"),
            surface_normal_hkl=P([1, -1, 1], "PROJECT_INPUT"),
            beam_azimuth_uvw=P([1, 1, 0], "PROJECT_INPUT"),
            beam_energy_keV=P(200.0, "PROJECT_INPUT", unit="keV", item=1),
            lattice_parameter_A=P(5.4309, "ASSUMPTION", unit="A"),
            mean_inner_potential_V=P(12.0, "ASSUMPTION", unit="V", item=20),
            target_reflection_hkl=P([4, -4, 4], "DERIVED_HERE", item=9),
            forbidden_rod_reflections_hkl=P([[2, -2, 2], [6, -6, 6], [10, -10, 10]],
                                            "DERIVED_HERE"),
        ))


def cfg_o_fixture():
    return dict(
        schema_version=1, config_id="CFG-O", name="osakabe_1988_reproduction",
        status="placeholder", description="TEST_ONLY in-memory fixture",
        parameters=dict(
            surface_material=P("Pt", "SECTION_READ"),
            surface_normal_hkl=P([1, 1, 1], "SECTION_READ"),
            beam_energy_keV=P(None, "UNVERIFIED", unit="keV"),
            glancing_angle_ext_mrad=P(None, "UNVERIFIED", unit="mrad"),
            reflection_order=P(None, "UNVERIFIED"),
            reference_model=P("R2", "DERIVED_HERE"),
        ))


def load(d, level="run"):
    return load_config_dict(d, level=level, allow_test_only=True)


def test_seven_evidence_labels():
    assert EVIDENCE_LABELS == ("METADATA_VERIFIED", "SECTION_READ", "REPRODUCED",
                               "PROJECT_INPUT", "ASSUMPTION", "DERIVED_HERE", "UNVERIFIED")


def test_complete_test_only_fixture_loads_at_run_level():
    cfg = load(cfg_b_complete())
    assert cfg.test_only and cfg.missing_project_inputs == [] and cfg.unverified == []
    assert cfg.value("beam_energy_keV") == 200.0
    assert cfg.value("target_reflection_hkl") == [0, 0, 8]
    assert len(cfg.sha256_canonical) == 64


CFG_B_NULL_ITEMS = [("convergence_semi_angle_mrad", 3), ("objective_aperture_semi_angle_mrad", 4),
                    ("image_pixel_size_nm", 5), ("glancing_angle_ext_mrad", 7),
                    ("beam_azimuth_uvw", 8), ("surface_preparation_details", 12),
                    ("pattern_geometry", 13), ("reference_trajectory", 15)]


@pytest.mark.parametrize("name,item", CFG_B_NULL_ITEMS,
                         ids=[f"item{i}_{n}" for n, i in CFG_B_NULL_ITEMS])
def test_null_project_input_fails_run_level_naming_item(name, item):
    """Configuration-failure test, one per null PROJECT_INPUT item of CFG-B."""
    d = cfg_b_complete()
    spec = d["parameters"][name]
    spec.update(value=None, label="PROJECT_INPUT", source=f"docs/06 item {item}, not supplied")
    with pytest.raises(MissingProjectInputError, match=rf"item {item} \({name}\)") as exc:
        load(d, level="run")
    assert exc.value.items == [item] and exc.value.names == [name]
    cfg = load(d, level="placeholder")
    assert cfg.missing_project_inputs == [(name, item)]
    with pytest.raises(MissingProjectInputError, match=rf"item {item}\b"):
        cfg.value(name)


def test_all_eight_nulls_are_named_together():
    d = cfg_b_complete()
    for name, item in CFG_B_NULL_ITEMS:
        d["parameters"][name].update(value=None, label="PROJECT_INPUT")
    with pytest.raises(MissingProjectInputError) as exc:
        load(d)
    assert exc.value.items == [3, 4, 5, 7, 8, 12, 13, 15]


def test_null_project_input_must_name_its_item():
    d = cfg_b_complete()
    d["parameters"]["beam_azimuth_uvw"] = P(None, "PROJECT_INPUT")
    with pytest.raises(ConfigError, match="docs/06 item"):
        load(d, level="placeholder")


@pytest.mark.parametrize("energy", [300.0, 100.0, 199.9, 200.1])
@pytest.mark.parametrize("level", ["run", "placeholder"])
def test_cfg_b_energy_other_than_200_keV_fails(energy, level):
    d = cfg_b_complete()
    d["parameters"]["beam_energy_keV"]["value"] = energy
    with pytest.raises(ConfigError, match="200 keV"):
        load(d, level=level)


def test_cfg_b_must_state_the_energy():
    d = cfg_b_complete()
    d["parameters"]["beam_energy_keV"].update(value=None, label="PROJECT_INPUT")
    with pytest.raises(ConfigError, match="must state the beam energy"):
        load(d, level="placeholder")
    d = cfg_b_complete()
    del d["parameters"]["beam_energy_keV"]
    with pytest.raises(ConfigError, match="must state the beam energy"):
        load(d, level="placeholder")


def test_cfg_b_energy_unit_must_be_keV():
    d = cfg_b_complete()
    d["parameters"]["beam_energy_keV"]["unit"] = "eV"
    with pytest.raises(ConfigError, match="unit"):
        load(d)


def test_300_keV_refused_for_every_configuration():
    d = cfg_a_fixture()
    d["parameters"]["beam_energy_keV"]["value"] = 300.0
    with pytest.raises(ConfigError, match="300 keV is never used"):
        load(d, level="placeholder")
    o = cfg_o_fixture()
    o["parameters"]["beam_energy_keV"] = P(300.0, "SECTION_READ", unit="keV")
    with pytest.raises(ConfigError):
        load(o, level="placeholder")


def test_cfg_o_is_placeholder_only():
    cfg = load(cfg_o_fixture(), level="placeholder")
    assert cfg.unverified == ["beam_energy_keV", "glancing_angle_ext_mrad", "reflection_order"]
    with pytest.raises(UnverifiedParameterError):
        cfg.value("beam_energy_keV")
    with pytest.raises(PlaceholderConfigError):
        load(cfg_o_fixture(), level="run")


def test_unverified_fields_fail_run_level_even_if_not_placeholder():
    o = cfg_o_fixture()
    o["status"] = "experiment"
    with pytest.raises(UnverifiedParameterError) as exc:
        load(o, level="run")
    assert exc.value.names == ["beam_energy_keV", "glancing_angle_ext_mrad", "reflection_order"]
    o["parameters"]["reflection_order"] = P("(3,3,3)", "UNVERIFIED")   # non-null still fails
    o["parameters"]["beam_energy_keV"] = P(200.0, "SECTION_READ", unit="keV")
    o["parameters"]["glancing_angle_ext_mrad"] = P(20.0, "SECTION_READ", unit="mrad")
    with pytest.raises(UnverifiedParameterError, match="reflection_order"):
        load(o, level="run")


def test_cfg_a_fixture_loads_at_run_level():
    cfg = load(cfg_a_fixture())
    assert cfg.config_id == "CFG-A" and not cfg.test_only


@pytest.mark.parametrize("label", ["VERIFIED", "assumption", "", None, "+ABSTRACT(publisher)"])
def test_labels_must_be_one_of_the_seven(label):
    d = cfg_a_fixture()
    d["parameters"]["lattice_parameter_A"]["label"] = label
    with pytest.raises(ConfigError, match="label"):
        load(d)


def test_test_only_refused_without_flag_and_from_files(tmp_path):
    d = cfg_b_complete()
    with pytest.raises(ConfigError, match="TEST_ONLY"):
        load_config_dict(d, level="run")
    f = tmp_path / "cfg_b_si001_patterned.yaml"                 # not under configs/
    f.write_text(yaml.safe_dump(d))
    with pytest.raises(ConfigError, match="TEST_ONLY"):
        load_config_file(f, level="placeholder")


def test_file_loader_hashes_and_checks_the_name(tmp_path):
    d = cfg_a_fixture()
    f = tmp_path / "cfg_a_si111_cleaved_110azimuth.yaml"
    f.write_text(yaml.safe_dump(d))
    cfg = load_config_file(f, level="run")
    assert len(cfg.sha256_file) == 64 and cfg.source_path == str(f)
    g = tmp_path / "cfg_b_si001_patterned.yaml"
    g.write_text(yaml.safe_dump(d))
    with pytest.raises(ConfigError, match="file name"):
        load_config_file(g, level="run")
    with pytest.raises(TypeError):
        load_config_file(f)                                      # level is required


@pytest.mark.parametrize("mutation,match", [
    (lambda d: d["parameters"]["lattice_parameter_A"].pop("source"), "lacks"),
    (lambda d: d["parameters"]["lattice_parameter_A"].update(extra=1), "unknown keys"),
    (lambda d: d["parameters"].update(made_up=P(1, "ASSUMPTION")), "unknown parameter"),
    (lambda d: d["parameters"]["lattice_parameter_A"].update(value=None), "null"),
    (lambda d: d.update(colour="red"), "unknown top-level"),
    (lambda d: d.update(name="other"), "name must be"),
    (lambda d: d["parameters"]["surface_normal_hkl"].update(value=[1, -1]), "three integers"),
    (lambda d: d["parameters"]["mean_inner_potential_V"].update(item=7), "item 20"),
])
def test_schema_assertions(mutation, match):
    d = cfg_a_fixture()
    mutation(d)
    with pytest.raises(ConfigError, match=match):
        load(d, level="placeholder")


@pytest.mark.parametrize("target", [[6, -6, 6], [2, -2, 2], [10, -10, 10]])
def test_forbidden_target_refused_cfg_a(target):
    d = cfg_a_fixture()
    d["parameters"]["target_reflection_hkl"]["value"] = target
    with pytest.raises(ConfigError, match="forbidden"):
        load(d, level="placeholder")


@pytest.mark.parametrize("target", [[0, 0, 2], [0, 0, 6], [0, 0, 10]])
def test_forbidden_target_refused_cfg_b(target):
    d = cfg_b_complete()
    d["parameters"]["target_reflection_hkl"]["value"] = target
    with pytest.raises(ConfigError, match="forbidden"):
        load(d, level="placeholder")


def test_crystallographic_cross_checks():
    d = cfg_a_fixture()
    d["parameters"]["target_reflection_hkl"]["value"] = [4, 4, 4]      # not on the (1,-1,1) rod
    with pytest.raises(ConfigError, match="specular rod"):
        load(d)
    d = cfg_a_fixture()
    d["parameters"]["target_reflection_hkl"]["value"] = [1, -1, 1]     # inaccessible
    with pytest.raises(ConfigError, match="escape angle"):
        load(d)
    d = cfg_b_complete()
    d["parameters"]["beam_azimuth_uvw"]["value"] = [1, 1, 1]          # not in the (001) plane
    with pytest.raises(ConfigError, match="not in the surface plane"):
        load(d)
    d = cfg_b_complete()
    d["parameters"]["forbidden_rod_reflections_hkl"]["value"] = [[0, 0, 4]]
    with pytest.raises(ConfigError, match="listed as forbidden"):
        load(d)


def test_value_returns_a_copy():
    cfg = load(cfg_b_complete())
    v = cfg.value("image_pixel_size_nm")
    v["along_beam"] = 99.0
    assert cfg.value("image_pixel_size_nm")["along_beam"] == 0.5


def test_fixture_is_not_mutated_by_loading():
    d = cfg_b_complete()
    before = copy.deepcopy(d)
    load(d)
    assert d == before
