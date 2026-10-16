"""R1 geometry tests. Each docstring names the external fact (calculator check, card,
repository document, or invariant) and the tolerance."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from reflection_holo import constants as C  # noqa: E402
from reflection_holo import geometry as G  # noqa: E402
from reflection_holo import project_inputs as P  # noqa: E402

E = 200e3
V0 = 12.0
A = C.A_SI.value
D111 = A / math.sqrt(3.0)
S111 = G.Surface((1, -1, 1), (1, 1, 0))
S001 = G.Surface((0, 0, 1), (1, 1, 0))
TWO_PI = 2 * math.pi


def test_reciprocal_convention():
    """card:peng_ch13 [p.8]: a_i . b_j = 2 pi delta_ij; tol 1e-12."""
    assert np.allclose(G.lattice_vectors() @ G.reciprocal_vectors().T, TWO_PI * np.eye(3), atol=1e-12)


def test_frames_orthonormal_right_handed():
    """Invariant: frame rows orthonormal, det = +1, z = outward normal; tol 1e-12."""
    for s in (S111, S001):
        F = G.frame(s)
        assert np.allclose(F @ F.T, np.eye(3), atol=1e-12)
        assert abs(np.linalg.det(F) - 1) < 1e-12
        n = np.array(s.hkl, float)
        assert np.allclose(F[2], n / np.linalg.norm(n), atol=1e-12)


def test_frame_rejects_readme_facet():
    """repo:physics_conventions.md: '(1,1,-1) facet' is inconsistent with a [110] beam."""
    with pytest.raises(G.GeometryError):
        G.frame(G.Surface((1, 1, -1), (1, 1, 0)))


def test_frame_matches_conventions_doc():
    """repo:physics_conventions.md frame (x=[1,-1,1]/sqrt3, y=[1,-1,-2]/sqrt6, z=[1,1,0]/sqrt2)
    maps to the contract frame as x=z_conv, y=-y_conv, z=x_conv; tol 1e-12."""
    F = G.frame(S111)
    assert np.allclose(F[0], np.array([1, 1, 0]) / math.sqrt(2), atol=1e-12)
    assert np.allclose(F[1], -np.array([1, -1, -2]) / math.sqrt(6), atol=1e-12)
    assert np.allclose(F[2], np.array([1, -1, 1]) / math.sqrt(3), atol=1e-12)


TEST_SET = ([(n, n, n) for n in range(1, 13)] + [(n, -n, n) for n in (1, 2, 4, 6, 8)]
            + [(0, 0, l) for l in (2, 4, 8, 12, 16)] + [(2, -2, 0), (2, 2, 0)])


def test_structure_factor_closed_vs_direct():
    """repo:calculator_output.txt sec.2: max |explicit sum - closed form| = 2.16e-14; tol 1e-12."""
    for hkl in TEST_SET:
        assert abs(G.structure_factor_si(*hkl) - G.structure_factor_si_direct(*hkl)) <= 1e-12


def test_forbidden_exactly_zero():
    """Task R1 / spec 4.1: forbidden reflections return EXACTLY zero (==0, no tolerance)."""
    for hkl in [(2, 2, 2), (6, 6, 6), (10, 10, 10), (2, -2, 2), (6, -6, 6), (10, -10, 10),
                (0, 0, 2), (0, 0, 6), (0, 0, 10), (0, 0, 1), (1, 0, 0)]:
        assert G.structure_factor_si(*hkl) == 0
        assert G.is_forbidden(*hkl)


def test_T7_T8_T9():
    """Calculator T7-T9: |F(666)|/f = 0, |F(444)|/f = 8, |F(555)|/f = 4 sqrt2; tol 1e-9."""
    assert abs(G.structure_factor_si(6, 6, 6)) <= 1e-9
    assert abs(abs(G.structure_factor_si(4, 4, 4)) - 8) <= 1e-9
    assert abs(abs(G.structure_factor_si(5, 5, 5)) - 4 * math.sqrt(2)) <= 1e-9


def test_T4_vacuum_bragg_666():
    """Calculator T4: vacuum Bragg angle (666) = 23.9976 mrad +/- 1e-3."""
    c = G.rod_condition(S111, 6, E, V0, allow_forbidden=True)
    assert abs(c["theta_B_vac"] * 1e3 - 23.9976) <= 1e-3


def test_T5_critical_angle():
    """Calculator T5: theta_c(12 V) = 8.3560 mrad +/- 1e-3 (both sin = dK/k_int and dK/k)."""
    assert abs(G.critical_angle(E, V0) * 1e3 - 8.3560) <= 1e-3
    assert abs(math.asin(G.delta_K(E, V0) / C.wavenumber(E)) * 1e3 - 8.3560) <= 1e-3


def test_T6_external_angle_666():
    """Calculator T6: external angle at the (666) internal condition = 22.4953 mrad +/- 1e-3."""
    c = G.rod_condition(S111, 6, E, V0, allow_forbidden=True)
    assert abs(c["theta_ext"] * 1e3 - 22.4953) <= 1e-3


def test_T10_to_T13_step_phases():
    """Calculator T10-T13: d_111 step phase mod 2pi at (666) 3.9236, (444) 2.5820,
    (555) 3.4088, (888) 4.5386 rad; tol 2e-3."""
    for n, want, allow in ((6, 3.9236, True), (4, 2.5820, False), (5, 3.4088, False),
                           (8, 4.5386, False)):
        c = G.rod_condition(S111, n, E, V0, allow_forbidden=allow)
        ph = abs(G.specular_step_phase(D111, c["theta_ext"], E)) % TWO_PI
        assert abs(ph - want) <= 2e-3


def test_T14_h2pi():
    """Calculator T14: h_2pi at the (666) condition = 0.5575 A +/- 1e-3."""
    c = G.rod_condition(S111, 6, E, V0, allow_forbidden=True)
    assert abs(c["h_2pi"] - 0.5575) <= 1e-3
    assert abs(G.wrap_period(c["theta_ext"], E) - 0.5575) <= 1e-3


def test_T15_accessibility_220():
    """Calculator T15 / sec.6: (2,-2,0) off (1,-1,1): G.n = 2.671821 < 2dK = 4.186831 rad/A,
    inaccessible; tol 1e-4 on both numbers."""
    r = G.reflection_accessibility((2, -2, 0), S111, E, V0)
    assert not r["accessible"]
    assert abs(r["G_dot_n"] - 2.671821) <= 1e-4 and abs(r["two_dK"] - 4.186831) <= 1e-4


def test_T16_GR_integer():
    """Calculator T16: G.R/2pi = 1 for (2,-2,0) and R = (a/2)[1,0,1]; tol 1e-9."""
    R = 0.5 * A * np.array([1.0, 0.0, 1.0])
    assert abs(float(G.reciprocal_vector((2, -2, 0)) @ R) / TWO_PI - 1.0) <= 1e-9


def test_T20_foreshortening():
    """Calculator T20: 1/sin(theta_ext) at (666) = 44.46 +/- 0.02."""
    c = G.rod_condition(S111, 6, E, V0, allow_forbidden=True)
    assert abs(G.foreshortening(c["theta_ext"]) - 44.46) <= 0.02


def test_T23_max_tilt_step():
    """Calculator T23: max tilt step for h = 1 nm = 0.6270 mrad +/- 1e-3 (calculator omits cos)."""
    c = G.rod_condition(S111, 6, E, V0, allow_forbidden=True)
    assert abs(G.max_tilt_step(10.0, c["theta_ext"], E) * 1e3 - 0.6270) <= 1e-3


def test_guard_refuses_forbidden():
    """Spec 4.1: the guard refuses (2,-2,2), (6,-6,6), (10,-10,10), (002), (006), (0,0,10)."""
    for s, n in ((S111, 2), (S111, 6), (S111, 10), (S001, 2), (S001, 6), (S001, 10)):
        with pytest.raises(G.ForbiddenReflectionError):
            G.rod_condition(s, n, E, V0)
    hkls = [o["hkl"] for o in G.specular_orders(S111, E, nmax=16, V0=V0)]
    assert (6, -6, 6) not in hkls and (2, -2, 2) not in hkls


def test_specular_orders_si111_calculator_table():
    """repo:calculator_output.txt sec.4/sec.5 (200 keV, 12 V): theta_ext of the allowed (nnn)
    orders; tol 1e-3 mrad (T6 tolerance). (1,-1,1) inaccessible."""
    want = {1: None, 3: 8.6096, 4: 13.6415, 5: 18.1675, 7: 26.7216, 8: 30.8882, 9: 35.017,
            11: 43.204, 12: 47.275}
    got = {o["n"]: o for o in G.specular_orders(S111, E, nmax=12, V0=V0)}
    assert set(got) == set(want)
    assert not got[1]["accessible"]
    for n, w in want.items():
        if w is not None:
            assert abs(got[n]["theta_ext"] * 1e3 - w) <= 1e-3


def test_specular_orders_si001_calculator_table():
    """repo:calculator_output.txt sec.4b (200 keV): (00L) theta_ext 3.934, 16.474, 26.420,
    35.994 mrad (tol 1e-3) and h_2pi 3.1872, 0.7612, 0.4747, 0.3485 A (tol 1e-3)."""
    want = {4: (3.934, 3.1872), 8: (16.474, 0.7612), 12: (26.420, 0.4747), 16: (35.994, 0.3485)}
    got = {o["n"]: o for o in G.specular_orders(S001, E, nmax=16, V0=V0)}
    assert set(got) == set(want)
    for L, (th, h2) in want.items():
        assert abs(got[L]["theta_ext"] * 1e3 - th) <= 1e-3
        assert abs(got[L]["h_2pi"] - h2) <= 1e-3


def test_theta_c_relativistic_relation():
    """repo:physics_conventions.md: sin^2 theta_c = Delta/(1+Delta) with the relativistic Delta
    (theta_c^2 ~ 2 e V0 gamma m0 / (hbar^2 k^2)); tol 1e-12 relative."""
    D = G.delta_refraction(E, V0)
    s = math.sin(G.critical_angle(E, V0))
    assert abs(s ** 2 / (D / (1 + D)) - 1) <= 1e-12


def test_delta_value_and_relativistic_ratio():
    """repo:physics_conventions.md: Delta(200 keV, 12 V) = 6.98e-5 (tol 5e-8); relativistic value
    16 % larger than V0/T, V0/T 14 % too small (tol 0.005)."""
    D = G.delta_refraction(E, V0)
    assert abs(D - 6.98e-5) <= 5e-8
    assert abs(D / (V0 / E) - 1 - 0.16) <= 0.005
    assert abs(1 - (V0 / E) / D - 0.14) <= 0.005


def test_dK_equals_convention_form():
    """Invariant: dK^2 = 2 gamma m0 e V0/hbar^2 equals k^2 Delta; tol 1e-12 relative."""
    assert abs(G.delta_K(E, V0) ** 2 / (C.wavenumber(E) ** 2 * G.delta_refraction(E, V0)) - 1) <= 1e-12


def test_refraction_calculator_and_roundtrip():
    """Calculator sec.11(c) exact theta_int: 13.0313, 21.6751, 23.9968, 40.8629 mrad at
    theta_ext 10, 20, 22.495, 40 mrad (tol 1e-3); inverse roundtrip tol 1e-12 rad;
    no total external reflection: refraction(0) = theta_c."""
    for te, ti in ((10.0, 13.0313), (20.0, 21.6751), (22.495315, 23.9968), (40.0, 40.8629)):
        t_int = G.refraction(te * 1e-3, E, V0)
        assert abs(t_int * 1e3 - ti) <= 1e-3
        assert abs(G.external_angle(t_int, E, V0) - te * 1e-3) <= 1e-12
    assert abs(G.refraction(0.0, E, V0) - G.critical_angle(E, V0)) <= 1e-12
    assert math.isnan(G.external_angle(0.5 * G.critical_angle(E, V0), E, V0))


def test_step_phase_sign_and_specular_form():
    """repo:physics_conventions.md: Delta_phi = -(k_out - k_in).R = -(4 pi/lambda) h sin(theta)
    for the specular beam; in-plane R irrelevant; reversing R reverses the sign; tol 1e-10."""
    th = 0.0165
    k = C.wavenumber(E)
    kin = k * np.array([math.cos(th), 0, -math.sin(th)])
    kout = k * np.array([math.cos(th), 0, math.sin(th)])
    R = np.array([1.7, -0.3, 2.0])
    assert abs(G.step_phase(R, kin, kout) - G.specular_step_phase(2.0, th, E)) <= 1e-10
    assert abs(G.step_phase(-R, kin, kout) + G.step_phase(R, kin, kout)) <= 1e-10
    assert G.specular_step_phase(2.0, th, E) < 0


def test_step_invisibility_all_orders():
    """Geometry-only T-step-invisibility (repo calculator sec.6): at the VACUUM Bragg angle of
    every allowed rod order, a lattice-translation step gives Delta_phi = 2 pi * integer;
    tol 1e-9 on Delta_phi/2pi."""
    for s, hs in ((S111, (D111, 2 * D111)), (S001, (A / 4, A / 2))):
        for o in G.specular_orders(s, E, nmax=16, V0=V0):
            for h in hs:
                x = G.specular_step_phase(h, o["theta_B_vac"], E) / TWO_PI
                assert abs(x - round(x)) <= 1e-9


def test_repository_angle_invisible():
    """Calculator sec.6: at 1.375 deg a d_111 step gives |dphi| mod 2pi = 0.001058 rad; tol 2e-6."""
    ph = abs(G.specular_step_phase(D111, math.radians(1.375), E)) % TWO_PI
    assert abs(ph - 0.001058) <= 2e-6


def test_shadow_lengths_spec():
    """repo:06 item 13: 10 nm shadows 444 nm at 22.5 mrad and 733 nm at the (4,-4,4) angle
    (tol 1 nm); spec sec.2 CFG-A: 230 A per bilayer at (4,-4,4), 102 A at (8,-8,8) (tol 0.6 A)."""
    c4 = G.rod_condition(S111, 4, E, V0)
    c8 = G.rod_condition(S111, 8, E, V0)
    assert abs(G.shadow_length(100.0, 22.5e-3) / 10 - 444) <= 1
    assert abs(G.shadow_length(100.0, c4["theta_ext"]) / 10 - 733) <= 1
    assert abs(G.shadow_length(D111, c4["theta_ext"]) - 230) <= 0.6
    assert abs(G.shadow_length(D111, c8["theta_ext"]) - 102) <= 0.6


def test_cfgB_008_spec_numbers():
    """Spec sec.2 CFG-B: (008) theta_int 18.5, theta_ext 16.5 mrad (tol 0.05), wrap period
    0.76 A (tol 0.005), foreshortening 61x (tol 0.5)."""
    c = G.rod_condition(S001, 8, E, V0)
    assert abs(c["theta_int"] * 1e3 - 18.5) <= 0.05
    assert abs(c["theta_ext"] * 1e3 - 16.5) <= 0.05
    assert abs(c["h_2pi"] - 0.76) <= 0.005
    assert abs(c["foreshortening"] - 61) <= 0.5


def test_wrap_period_is_pi_over_Kext():
    """Invariant: h_2pi = lambda/(2 sin theta_ext) = pi/K_ext; tol 1e-12 relative."""
    c = G.rod_condition(S001, 8, E, V0)
    assert abs(G.wrap_period(c["theta_ext"], E) / c["h_2pi"] - 1) <= 1e-12


def test_specular_orders_requires_V0():
    """repo:06 item 20 / task: a MISSING V0 must raise unless accept_assumptions=True."""
    with pytest.raises(P.MissingProjectInput):
        G.specular_orders(S111, E)
