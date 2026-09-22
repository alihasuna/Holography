"""Structure factor, selection rule, d-spacing, reciprocal vectors, forbidden-reflection guard
(source map SM02). T7-T9 use exactly the calculator's reference values and tolerances (lines
1027-1031)."""
import itertools

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.geometry.crystal import (FORBIDDEN_ON_CFG_A_ROD, FORBIDDEN_ON_CFG_B_ROD,
                                              d_spacing_A, diamond_allowed,
                                              reciprocal_lattice_cycles, reciprocal_vector_cycles,
                                              reciprocal_vector_rad, require_allowed_target,
                                              rod_decomposition, rod_reflections,
                                              structure_factor_over_f)
from reflection_holo.geometry.errors import ForbiddenReflectionError


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def test_T7_F666_is_zero():
    """T7: |F(666)|/f = 0 +/- 1e-9 (calculator evaluates (6,6,6); (6,-6,6) has the same |F|)."""
    check(abs(structure_factor_over_f((6, 6, 6))), 0.0, 1e-9)
    check(abs(structure_factor_over_f((6, -6, 6))), 0.0, 1e-9)


def test_T8_F444():
    """T8: |F(444)|/f = 8 +/- 1e-9."""
    check(abs(structure_factor_over_f((4, 4, 4))), 8.0, 1e-9)


def test_T9_F555():
    """T9: |F(555)|/f = 4 sqrt(2) +/- 1e-9."""
    check(abs(structure_factor_over_f((5, 5, 5))), 4 * np.sqrt(2), 1e-9)


def test_selection_rule_matches_explicit_sum():
    """diamond_allowed agrees with |F| > 0 of the explicit 8-atom sum, and with the closed form
    4 [same parity] |1 + i^(h+k+l)| (calculator section 2), for all |h|,|k|,|l| <= 6."""
    for hkl in itertools.product(range(-6, 7), repeat=3):
        if hkl == (0, 0, 0):
            continue
        F = abs(structure_factor_over_f(hkl))
        h, k, l = hkl
        same = (h % 2 == k % 2 == l % 2)
        closed = 4.0 * abs(1 + 1j ** ((h + k + l) % 4)) if same else 0.0
        assert abs(F - closed) < 1e-9, hkl
        assert diamond_allowed(hkl) == (F > 1e-9), hkl


def test_forbidden_rod_lists_follow_from_the_rule():
    """Within orders 1..12 the forbidden EVEN orders of the (1,-1,1) rod are exactly (2,-2,2),
    (6,-6,6), (10,-10,10); the forbidden even orders of (001) are (002), (006), (0,0,10)."""
    a_forb = [r["hkl"] for r in rod_reflections((1, -1, 1), 12)
              if not r["allowed"] and r["hkl"][0] % 2 == 0]
    assert tuple(a_forb) == FORBIDDEN_ON_CFG_A_ROD
    b_forb = [r["hkl"] for r in rod_reflections((0, 0, 1), 12)
              if not r["allowed"] and r["hkl"][2] % 2 == 0]
    assert tuple(b_forb) == FORBIDDEN_ON_CFG_B_ROD
    # every odd order of (001) is forbidden (mixed parity); every odd order of (1,-1,1) is allowed
    assert all(not r["allowed"] for r in rod_reflections((0, 0, 1), 12) if r["hkl"][2] % 2)
    assert all(r["allowed"] for r in rod_reflections((1, -1, 1), 12) if r["hkl"][0] % 2)


def test_guard_refuses_666_as_target():
    """Forbidden-reflection guard: (6,-6,6) is refused as a TARGET with a clear error."""
    with pytest.raises(ForbiddenReflectionError, match=r"\(6, -6, 6\).*forbidden"):
        require_allowed_target((6, -6, 6))


@pytest.mark.parametrize("hkl", FORBIDDEN_ON_CFG_A_ROD + FORBIDDEN_ON_CFG_B_ROD)
def test_guard_refuses_every_listed_forbidden_target(hkl):
    with pytest.raises(ForbiddenReflectionError):
        require_allowed_target(hkl)


@pytest.mark.parametrize("hkl", [(4, -4, 4), (5, -5, 5), (7, -7, 7), (8, -8, 8), (3, -3, 3),
                                 (0, 0, 4), (0, 0, 8), (0, 0, 12)])
def test_guard_accepts_allowed_targets(hkl):
    assert require_allowed_target(hkl) == hkl


def test_guard_explicit_override_for_legacy_checks():
    assert require_allowed_target((6, -6, 6), allow_forbidden=True) == (6, -6, 6)


def test_d_spacing_and_reciprocal_vectors():
    d111 = d_spacing_A((1, -1, 1), A_SI_A)
    check(d111, A_SI_A / np.sqrt(3), 1e-15)
    check(d111, 3.1355, 5e-5)                      # docs/03 section 2: h = d_111 = 3.1355 A
    g = reciprocal_vector_cycles((6, -6, 6), A_SI_A)
    check(np.linalg.norm(g), 1.0 / d_spacing_A((6, -6, 6), A_SI_A), 1e-14)
    G = reciprocal_vector_rad((2, -2, 0), A_SI_A)
    check(np.linalg.norm(G), 2 * np.pi / d_spacing_A((2, -2, 0), A_SI_A), 1e-14)


def test_reciprocal_lattice_of_fcc_primitive_basis():
    a = A_SI_A
    A = 0.5 * a * np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
    B = reciprocal_lattice_cycles(A)
    assert np.allclose(A @ B.T, np.eye(3), atol=1e-14)
    # bcc reciprocal: b1 = (-1, 1, 1)/a
    assert np.allclose(B[0], np.array([-1, 1, 1]) / a, atol=1e-14)


def test_rod_decomposition():
    assert rod_decomposition((6, -6, 6)) == ((1, -1, 1), 6)
    assert rod_decomposition((0, 0, 8)) == ((0, 0, 1), 8)


def test_d_spacing_requires_lattice_parameter():
    with pytest.raises(TypeError):
        d_spacing_A((1, 1, 1))  # no default lattice parameter
