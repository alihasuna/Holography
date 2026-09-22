"""Invisibility condition g.R integer (source map SM03). T16 uses exactly the calculator's
reference value and tolerance (line 1046)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.geometry.crystal import reciprocal_vector_cycles
from reflection_holo.geometry.frames import surface_frame
from reflection_holo.geometry.specular import SpecularCondition, beam_wavevectors_slab
from reflection_holo.quantification.invisibility import detect_invisibility

R_BILAYER = 0.5 * A_SI_A * np.array([1.0, 0.0, 1.0])       # (a/2)[1,0,1], R.n_hat = d_111
D111 = A_SI_A / np.sqrt(3.0)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def test_T16_220_bilayer_is_invisible():
    """T16: exact G.R/2pi for (2,-2,0) and a d_111 step = 1.0 +/- 1e-9 (integer: invisible)."""
    rep = detect_invisibility(reciprocal_vector_cycles((2, -2, 0), A_SI_A), R_BILAYER,
                              tol_cycles=1e-9)
    check(rep.g_dot_R, 1.0, 1e-9)
    assert rep.invisible and rep.nearest_integer == 1


def test_repository_formula_would_give_4_thirds():
    """docs/03 section 2: dropping g_par.R_par gives 4/3 (the 2 pi/3 staircase artefact)."""
    g = reciprocal_vector_cycles((2, -2, 0), A_SI_A)
    n = np.array([1.0, -1.0, 1.0]) / np.sqrt(3)
    normal_only = float(g @ n) * float(R_BILAYER @ n)
    check(normal_only, 4.0 / 3.0, 1e-12)
    assert not detect_invisibility(g, (R_BILAYER @ n) * n, tol_cycles=1e-6).invisible


def test_vacuum_bragg_setting_of_666_is_invisible_refraction_setting_is_not():
    """At the vacuum Bragg angle of (6,-6,6) (the inspected repository's 1.375 deg) q = G_666 and
    a bilayer step is invisible; at the refraction-corrected angle it is not (docs/03 section 2)."""
    f = surface_frame((1, -1, 1), (1, 1, 0))
    sc = SpecularCondition(D111, 6, 200.0, 12.0)
    for th, expect in ((sc.theta_B_vac, True), (sc.theta_ext, False)):
        k_in, k_out = beam_wavevectors_slab(th, th, sc.k)
        g = f.to_crystal(k_out - k_in) / (2 * np.pi)
        rep = detect_invisibility(g, R_BILAYER, tol_cycles=1e-6)
        assert rep.invisible is expect, (th, rep)
    k_in, k_out = beam_wavevectors_slab(sc.theta_B_vac, sc.theta_B_vac, sc.k)
    check(detect_invisibility(f.to_crystal(k_out - k_in) / (2 * np.pi), R_BILAYER,
                              tol_cycles=1e-9).g_dot_R, 6.0, 1e-9)


def test_tolerance_required():
    with pytest.raises(TypeError):
        detect_invisibility([1, 0, 0], [1, 0, 0])
