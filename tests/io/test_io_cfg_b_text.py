"""CFG-B step-type name, scope clause and header; CFG-A benchmark reflections (review E4 m8, M1, m5,
n10). The shipped files are read, never written."""
import copy
import re
from pathlib import Path

import pytest
import yaml

from reflection_holo.io.config import ConfigError, load_config_dict, load_config_file

REPO = Path(__file__).resolve().parents[2]
CFG_A = REPO / "configs" / "cfg_a_si111_cleaved_110azimuth.yaml"
CFG_B = REPO / "configs" / "cfg_b_si001_patterned.yaml"
SCOPE = ("For the specular beam (and, with the in-plane glide term, for other beams in the incidence "
         "plane) of a plane wave at the exact <100> azimuth, bulk-terminated a/4 terraces reflect "
         "identically up to exp(-i (k_out - k_in).t) (C2 section 1.3; SM26). Not for beams leaving the "
         "incidence plane (item 4), a 2x1 reconstruction, or an overlayer; azimuthal spread (item 3) "
         "not analysed; at <110> the residual is not forced to vanish (value unknown, open question 3).")


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def test_step_type_is_single_layer_a4_and_names_are_a_vocabulary():
    """E4 m8: the type name no longer says "screw-related" (at <100> the terraces are also glide
    related); the relation stays in step_translations. Unknown names, including the old one, fail."""
    from reflection_holo.io.config import STEP_TYPES
    b = load_config_file(CFG_B, level="placeholder")
    assert b.value("step_types") == ["single_layer_a4", "double_layer_a2_translation",
                                     "patterned_mesa_trench"]
    assert "single_layer_a4" in STEP_TYPES and "single_layer_a4_screw_related" not in STEP_TYPES
    d = yaml.safe_load(CFG_B.read_text())
    for bad in ("single_layer_a4_screw_related", "a4 step", "single_layer_a4 "):
        e = copy.deepcopy(d)
        e["parameters"]["step_types"]["value"] = [bad]
        with pytest.raises(ConfigError, match="step_types"):
            load_config_dict(e, level="placeholder")


def test_single_layer_scope_clause_in_description_and_relation():
    """E4 M1: the <100> a/4 result is carried with its scope conditions."""
    d = yaml.safe_load(CFG_B.read_text())
    assert SCOPE in squash(d["description"])
    rel = d["parameters"]["step_translations"]["value"]["single_layer"]["relation"]
    assert SCOPE in squash(rel)
    assert "4_1 and 4_3 screws" in rel and "<100> d-glides" in rel


def test_cfg_b_header_names_the_items_correctly():
    """E4 m5: item 13 is not blocking but required here; item 11's unsupplied parts have no field."""
    header = squash(" ".join(line.lstrip("# ") for line in CFG_B.read_text().splitlines()
                             if line.startswith("#")))
    assert "names items 3, 4, 5, 7, 8, 12, 13 (not blocking, required here) and 15" in header
    assert ("the unsupplied parts of item 11 (miscut, terrace widths, terrace types) have no field "
            "yet") in header


def test_cfg_a_benchmark_reflections_carry_no_docs06_item():
    """E4 n10 (done with A2b N1): benchmark definitions, DERIVED_HERE, no docs/06 item."""
    d = yaml.safe_load(CFG_A.read_text())
    for name in ("target_reflection_hkl", "recommended_reflections_hkl"):
        spec = d["parameters"][name]
        assert spec["label"] == "DERIVED_HERE" and "item" not in spec, name
    load_config_file(CFG_A, level="run")
