"""Internal-Bragg specular condition, step phase and the surface frames used (source map SM03,
SM04, SM05). T4, T6, T10-T14 use exactly the calculator's reference values and tolerances
(lines 1022-1043). T4, T6, T10 and T14 evaluate the FORBIDDEN (6,-6,6) setting of the inspected
repository, as the calculator does, through the lower-level SpecularCondition (no target guard);
the target-level call refuses (6,-6,6) (test_target_level_refuses_666)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.errors import (ForbiddenReflectionError, InaccessibleReflectionError,
                                             NotSpecularError)
from reflection_holo.geometry.frames import surface_frame
from reflection_holo.geometry.specular import (SpecularCondition, beam_wavevectors_slab,
                                               specular_condition_for, specular_step_phase,
                                               step_phase_translation, wrap_to_pi)

D111 = A_SI_A / np.sqrt(3.0)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


@pytest.fixture(scope="module")
def sc666():
    # lower-level call, exactly the calculator's SpecularCondition(d111, 6, 200.0, 12.0)
    return SpecularCondition(D111, 6, 200.0, 12.0)


def target(hkl, normal=(1, -1, 1)):
    return specular_condition_for(hkl, normal, E_keV=E, V0_V=V0, a_A=A_SI_A)


def test_T4_vacuum_bragg_angle_666(sc666):
    """T4: vacuum Bragg angle of the (6,-6,6) setting = 23.9976 mrad +/- 1e-3."""
    check(sc666.theta_B_vac * 1e3, 23.9976, 1e-3)


def test_T6_external_angle_666(sc666):
    """T6: external angle at the (6,-6,6) internal condition = 22.4953 mrad +/- 1e-3."""
    check(sc666.theta_ext * 1e3, 22.4953, 1e-3)


def test_T10_step_phase_666(sc666):
    """T10: (6,-6,6) setting, h = d_111, |Delta_phi| mod 2 pi = 3.9236 rad +/- 2e-3."""
    check(sc666.step_phase(D111)["mod2pi"], 3.9236, 2e-3)


def test_T11_step_phase_444():
    """T11: (4,-4,4), h = d_111, mod 2 pi = 2.5820 rad +/- 2e-3 (target-level call; allowed)."""
    check(target((4, -4, 4)).step_phase(D111)["mod2pi"], 2.5820, 2e-3)


def test_T12_step_phase_555():
    """T12: (5,-5,5), h = d_111, mod 2 pi = 3.4088 rad +/- 2e-3."""
    check(target((5, -5, 5)).step_phase(D111)["mod2pi"], 3.4088, 2e-3)


def test_T13_step_phase_888():
    """T13: (8,-8,8), h = d_111, mod 2 pi = 4.5386 rad +/- 2e-3."""
    check(target((8, -8, 8)).step_phase(D111)["mod2pi"], 4.5386, 2e-3)


def test_T14_wrap_period_666(sc666):
    """T14: h_2pi at the (6,-6,6) setting = 0.5575 A +/- 1e-3."""
    check(sc666.h_2pi_A, 0.5575, 1e-3)


def test_target_level_refuses_666():
    """The forbidden-reflection guard refuses (6,-6,6) as a target."""
    with pytest.raises(ForbiddenReflectionError):
        target((6, -6, 6))
    with pytest.raises(ForbiddenReflectionError):
        target((0, 0, 6), normal=(0, 0, 1))


def test_allow_forbidden_reproduces_the_lower_level_call(sc666):
    s = specular_condition_for((6, -6, 6), (1, -1, 1), E_keV=E, V0_V=V0, a_A=A_SI_A,
                               allow_forbidden=True)
    for attr in ("theta_B_vac", "theta_int", "theta_ext", "h_2pi_A", "K_ext"):
        assert getattr(s, attr) == getattr(sc666, attr), attr


def test_signs_matter_444_is_not_specular_on_1m11():
    """(4,4,4) is inclined at 70.5 degrees to the (1,-1,1) rod (physics_conventions)."""
    with pytest.raises(NotSpecularError):
        target((4, 4, 4))
    with pytest.raises(NotSpecularError):
        target((-4, 4, -4))


def test_first_order_is_inaccessible():
    with pytest.raises(InaccessibleReflectionError):
        target((1, -1, 1))
    assert not SpecularCondition(D111, 1, E, V0).accessible


# docs/03 section 3 table (rod order, theta_int, theta_ext, step phase mod 2 pi, h_2pi,
# foreshortening), tolerances matching the printed digits. Not T-numbered.
TABLE_03 = [
    (3, 12.00, 8.61, 0.96, 1.456, 116),
    (4, 16.00, 13.64, 2.58, 0.919, 73),
    (5, 20.00, 18.17, 3.41, 0.690, 55),
    (6, 24.00, 22.50, 3.92, 0.557, 44),
    (7, 28.00, 26.72, 4.28, 0.469, 37),
    (8, 32.00, 30.89, 4.54, 0.406, 32),
]


@pytest.mark.parametrize("n,th_int,th_ext,phase,h2pi,fore", TABLE_03)
def test_docs03_section3_table(n, th_int, th_ext, phase, h2pi, fore):
    s = SpecularCondition(D111, n, E, V0)       # lower level: the table includes (6,-6,6)
    check(s.theta_int * 1e3, th_int, 0.005)
    check(s.theta_ext * 1e3, th_ext, 0.005)
    check(s.step_phase(D111)["mod2pi"], phase, 0.005)
    check(s.h_2pi_A, h2pi, 0.0005)
    check(s.foreshortening, fore, 0.5)


def test_cfg_b_008_condition_docs05():
    """docs/05 section 2 CFG-B: (008) theta_int 18.5 mrad, theta_ext 16.5 mrad at V0 = 12 V, wrap
    period 0.76 A, foreshortening 61x; (004) exits at 3.9 mrad (printed digits)."""
    s = target((0, 0, 8), normal=(0, 0, 1))
    check(s.theta_int * 1e3, 18.5, 0.05)
    check(s.theta_ext * 1e3, 16.5, 0.05)
    check(s.h_2pi_A, 0.76, 0.005)
    check(s.foreshortening, 61, 0.5)
    check(target((0, 0, 4), normal=(0, 0, 1)).theta_ext * 1e3, 3.9, 0.05)
    # identical to the calculator's parametrisation d = a/4, order L/4
    s_calc = SpecularCondition(A_SI_A / 4.0, 2, E, V0)
    check(s.theta_ext, s_calc.theta_ext, 1e-15)


def test_cfg_a_333_docs05():
    """docs/05 section 2 CFG-A: (3,-3,3) exits at 8.6 mrad with 116x foreshortening."""
    s = target((3, -3, 3))
    check(s.theta_ext * 1e3, 8.6, 0.05)
    check(s.foreshortening, 116, 0.5)


def test_step_sign_up_and_down(sc666):
    up = sc666.step_phase(+D111)
    down = sc666.step_phase(-D111)
    assert up["total"] < 0 < down["total"]
    check(up["total"], -down["total"], 0.0)
    check(up["wrapped"], -down["wrapped"], 1e-12)


def test_frames_used_cfg_a_step_phase_translation_equals_specular():
    """Frames used: CFG-A frame (1,-1,1)/[110] from reflection_holo.geometry.frames. The bilayer
    translation R = (a/2)[1,0,1] has R.n_hat = d_111 and in-plane part a/sqrt(6); the exact
    -(k_out - k_in).R equals -(4 pi/lambda) h sin(theta) for the specular beam."""
    f = surface_frame((1, -1, 1), (1, 1, 0))
    R = 0.5 * A_SI_A * np.array([1.0, 0.0, 1.0])
    R_slab = f.to_slab(R)
    check(R_slab[0], D111, 1e-12)
    check(np.hypot(R_slab[1], R_slab[2]), A_SI_A / np.sqrt(6), 1e-12)
    s = target((4, -4, 4))
    k_in, k_out = beam_wavevectors_slab(s.theta_ext, s.theta_ext, s.k)
    q_crys = f.to_crystal(k_out - k_in)
    assert np.allclose(np.cross(q_crys, [1, -1, 1]), 0.0, atol=1e-12)     # q || n_hat
    got = step_phase_translation(f.to_crystal(k_in), f.to_crystal(k_out), R)
    check(got, specular_step_phase(D111, s.theta_ext, s.lam_A), 1e-9)
    check(got, s.step_phase(D111)["total"], 1e-9)
    check(wrap_to_pi(got), s.step_phase(D111)["wrapped"], 1e-9)


@pytest.mark.parametrize("azimuth", [(1, 1, 0), (1, 0, 0)])
def test_frames_used_cfg_b_double_layer(azimuth):
    """Frames used: CFG-B frame (001) with either candidate azimuth (PROJECT_INPUT item 8, not
    defaulted: both are tested). The a/2 double-layer translation gives the specular phase for
    h = a/2 independently of the azimuth."""
    f = surface_frame((0, 0, 1), azimuth)
    R = 0.5 * A_SI_A * np.array([1.0, 0.0, 1.0])
    s = target((0, 0, 8), normal=(0, 0, 1))
    k_in, k_out = beam_wavevectors_slab(s.theta_ext, s.theta_ext, s.k)
    got = step_phase_translation(f.to_crystal(k_in), f.to_crystal(k_out), R)
    check(got, specular_step_phase(A_SI_A / 2, s.theta_ext, s.lam_A), 1e-9)
