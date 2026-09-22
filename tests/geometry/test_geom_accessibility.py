"""Accessibility guard G.n_hat >= 2 dK (source map SM06). T15 uses exactly the calculator's
reference value and tolerance (line 1044)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.accessibility import (accessibility_margin, is_accessible,
                                                    require_accessible)
from reflection_holo.geometry.crystal import d_spacing_A, reciprocal_vector_rad
from reflection_holo.geometry.errors import InaccessibleReflectionError
from reflection_holo.geometry.frames import surface_frame
from reflection_holo.geometry.refraction import delta_K_per_A
from reflection_holo.geometry.specular import SpecularCondition

N111 = np.array([1.0, -1.0, 1.0]) / np.sqrt(3.0)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def test_T15_220_inaccessible():
    """T15: (2,-2,0) off (1,-1,1) at 200 keV, V0 = 12 V is not accessible: 0 +/- 0.5 (0 = no)."""
    G = reciprocal_vector_rad((2, -2, 0), A_SI_A)
    check(float(is_accessible(G, N111, E_keV=200.0, V0_V=12.0)), 0.0, 0.5)
    with pytest.raises(InaccessibleReflectionError, match="SM06"):
        require_accessible(G, N111, E_keV=200.0, V0_V=12.0, label="(2,-2,0)")


def test_220_numbers_c_report():
    """C report section 4.3: G.n_hat = 2.671821 rad/A, 2 dK = 4.186831 rad/A (printed digits);
    G.n_hat taken in the CFG-A surface frame (reflection_holo.geometry.frames)."""
    f = surface_frame((1, -1, 1), (1, 1, 0))
    G_slab = f.to_slab(reciprocal_vector_rad((2, -2, 0), A_SI_A))
    check(G_slab[0], 2.671821, 5e-7)
    check(2 * delta_K_per_A(E, V0), 4.186831, 5e-7)
    check(accessibility_margin(G_slab, [1.0, 0.0, 0.0], E_keV=E, V0_V=V0),
          2.671821 - 4.186831, 1e-6)


def test_guard_agrees_with_specular_condition_on_the_rod():
    d = d_spacing_A((1, -1, 1), A_SI_A)
    for n in range(1, 13):
        G = reciprocal_vector_rad((n, -n, n), A_SI_A)
        assert is_accessible(G, N111, E_keV=E, V0_V=V0) == SpecularCondition(d, n, E, V0).accessible


def test_negative_normal_component_refused():
    G = reciprocal_vector_rad((-4, 4, -4), A_SI_A)
    assert not is_accessible(G, N111, E_keV=E, V0_V=V0)


def test_normal_must_be_unit():
    with pytest.raises(ValueError):
        is_accessible([0, 0, 10.0], [0, 0, 2.0], E_keV=E, V0_V=V0)
