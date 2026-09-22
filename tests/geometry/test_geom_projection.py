"""Foreshortening, exit-plane mapping and the shadow length h/tan(theta_ext) (source map SM07).
T20 uses exactly the calculator's reference value and tolerance (line 1054). The shadow-length
values are those printed in docs/03 section 4, each with a tolerance matching its printed digits
(half a unit of the last printed digit), evaluated at the operating angle."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.projection import (exit_plane_height_A, foreshortening,
                                                 image_compression, shadow_length_A,
                                                 surface_coordinate_A)
from reflection_holo.geometry.specular import SpecularCondition, specular_condition_for

D111 = A_SI_A / np.sqrt(3.0)
LAYER_001 = A_SI_A / 4.0                   # Si(001) single layer a/4
MESA_10NM_A = 100.0                        # 10 nm


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def theta_ext(hkl):
    return specular_condition_for(hkl, (1, -1, 1), E_keV=E, V0_V=V0, a_A=A_SI_A).theta_ext


# "22.5 mrad" in docs/03 section 4 is "a round illustrative angle; it is the external angle of the
# forbidden (6,-6,6) condition": both readings are tested.
ANGLE_22_5 = [pytest.param(22.5e-3, id="22.5mrad_literal"),
              pytest.param(SpecularCondition(D111, 6, E, V0).theta_ext, id="666_theta_ext")]


def test_T20_foreshortening_666():
    """T20: 1/sin(theta_ext) at the (6,-6,6) setting = 44.46 +/- 0.02 (lower-level call)."""
    check(foreshortening(SpecularCondition(D111, 6, 200.0, 12.0).theta_ext), 44.46, 0.02)


@pytest.mark.parametrize("th", ANGLE_22_5)
def test_shadow_bilayer_22_5mrad(th):
    """docs/03 section 4: 139 A per Si(111) bilayer at 22.5 mrad (+/- 0.5 A)."""
    check(shadow_length_A(D111, th), 139.0, 0.5)


@pytest.mark.parametrize("th", ANGLE_22_5)
def test_shadow_10nm_mesa_22_5mrad(th):
    """docs/03 section 4: 444 nm for a 10 nm mesa at 22.5 mrad (+/- 0.5 nm)."""
    check(shadow_length_A(MESA_10NM_A, th) / 10.0, 444.0, 0.5)


@pytest.mark.parametrize("th", ANGLE_22_5)
def test_shadow_si001_layer_22_5mrad(th):
    """docs/03 section 4: 60 A per Si(001) layer (a/4) at 22.5 mrad (+/- 0.5 A)."""
    check(shadow_length_A(LAYER_001, th), 60.0, 0.5)


def test_shadow_bilayer_444():
    """docs/03 section 4: 230 A per bilayer at the (4,-4,4) angle, 13.6 mrad (+/- 0.5 A)."""
    check(shadow_length_A(D111, theta_ext((4, -4, 4))), 230.0, 0.5)


def test_shadow_10nm_mesa_444():
    """docs/03 section 4: 733 nm for a 10 nm mesa at the (4,-4,4) angle (+/- 0.5 nm)."""
    check(shadow_length_A(MESA_10NM_A, theta_ext((4, -4, 4))) / 10.0, 733.0, 0.5)


def test_shadow_bilayer_888():
    """Shadow length per bilayer at (8,-8,8). The documents printed 102 A until commit 5d59c41
    corrected it to 101 A (101.48 A computed: the calculator's theta_ext(8,-8,8) = 30.888 mrad;
    tools/phase1_numbers.py). The test value stays 101.0 +/- 0.5 A (review E4 n1)."""
    check(shadow_length_A(D111, theta_ext((8, -8, 8))), 101.0, 0.5)


def test_shadow_10nm_mesa_888():
    """docs/03 section 4: 324 nm for a 10 nm mesa at (8,-8,8) (+/- 0.5 nm)."""
    check(shadow_length_A(MESA_10NM_A, theta_ext((8, -8, 8))) / 10.0, 324.0, 0.5)


def test_shadow_length_is_h_over_tan_theta_and_sign_free():
    th = theta_ext((5, -5, 5))
    for h in (D111, 2 * D111, 50.0):
        assert shadow_length_A(h, th) == h / np.tan(th)
        assert shadow_length_A(-h, th) == shadow_length_A(h, th)


def test_exit_plane_mapping_round_trip_and_compression():
    th = theta_ext((4, -4, 4))
    z = np.linspace(0.0, 2000.0, 11)
    x = exit_plane_height_A(z, 7.0, th)
    assert np.allclose(surface_coordinate_A(x, 7.0, th), z, rtol=0, atol=1e-9)
    check(image_compression(th) * foreshortening(th), 1.0, 1e-15)


def test_angle_must_be_positive():
    with pytest.raises(ValueError):
        shadow_length_A(1.0, 0.0)
