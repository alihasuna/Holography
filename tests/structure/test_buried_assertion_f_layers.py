"""Assertion (f) of the buried-void builder, its BURIED branch (structure.features.assert_feature_inside,
audit A9a m-4; agent T4): removed sites must lie strictly below the flat top layer l_s and leave at
least MIN_LAYERS_BELOW_FEATURE intact layers below the void. Before this file no test reached the
branch (A9a mutation M6: disabling it left every structure test passing).

TEST_ONLY inputs: the feature geometry (item 13); lattice parameter ASSUMPTION B2. Synthetic feature
sites on (001) layers x = layer * a/4 inside the ring's bounding box, so that only the layer rule can
fire.
"""
import numpy as np
import pytest

from si001_test_inputs import FEATURE_LABEL
from reflection_holo.constants import A_SI_A
from reflection_holo.structure.checks import StructureAssertionError
from reflection_holo.structure.features import MIN_LAYERS_BELOW_FEATURE, assert_feature_inside
from reflection_holo.structure.shapes import BuriedTorus

A = A_SI_A
Q = A / 4.0
SRC = "TEST_ONLY geometry (tests/structure/test_buried_assertion_f_layers.py)"
L_S = 23                                  # flat top layer index
L = np.array([30.0 * Q, 30.0 * A, 30.0 * A])  # box (x, y, z); ring well inside, margin A
YC = ZC = 15.0 * A
FEATURE = BuriedTorus(center_y_A=YC, center_z_A=ZC, major_radius_A=20.0, minor_radius_A=6.0,
                      cap_A=5.0, label=FEATURE_LABEL, source=SRC)


def sites(layers):
    """One site per layer, on the tube circle (y = y_c + R, z = z_c): inside the ring box."""
    lay = np.asarray(layers, float)
    return np.column_stack([lay * Q, np.full_like(lay, YC + 20.0), np.full_like(lay, ZC)])


def test_valid_buried_layers_pass_and_are_recorded():
    rec = assert_feature_inside(sites([MIN_LAYERS_BELOW_FEATURE, 12, L_S - 1]), FEATURE, L_S, Q,
                                L, A)
    assert rec["feature_site_layers"] == [MIN_LAYERS_BELOW_FEATURE, L_S - 1]
    assert rec["intact_layers_below_void"] == MIN_LAYERS_BELOW_FEATURE
    assert rec["intact_layers_above_void"] == 1


@pytest.mark.parametrize("bad_layer", [MIN_LAYERS_BELOW_FEATURE - 1, 0])
def test_removed_site_too_deep_is_refused(bad_layer):
    with pytest.raises(StructureAssertionError, match=r"\(f\) the buried void removes layers"):
        assert_feature_inside(sites([bad_layer, 12, 20]), FEATURE, L_S, Q, L, A)


@pytest.mark.parametrize("bad_layer", [L_S, L_S + 1])
def test_removed_site_in_or_above_the_top_layer_is_refused(bad_layer):
    with pytest.raises(StructureAssertionError, match=r"must stay below the flat top layer"):
        assert_feature_inside(sites([8, 12, bad_layer]), FEATURE, L_S, Q, L, A)

