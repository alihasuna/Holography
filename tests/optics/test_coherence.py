"""Convergence ensembles in hologram formation (report E3 section 2; optics.coherence;
PROJECT_INPUT item 3; docs/05 section 5 item 4; SM13: intensities averaged after squaring).

TEST_ONLY values: semi-angles, separations, grid, carriers, amplitudes (items 3, 5, 16).

Tolerances (fixed before running; DERIVED_HERE):
* single member of weight 1: bit-for-bit equality (the same float operations: 0 + 1.0 x);
* visibility of a synthetic hologram against the analytic factor: the DERIVED_HERE quadrature bound
  of the declared quadrature (optics.coherence, recorded with it) plus 1e-13 for the FFT of an
  O(1) real image of 4096 samples (a few eps log2(N) relative);
* the R1 inclined-surface coherence: the quadrature bound plus kappa_max, since the exact
  member phase is k t.E_perp - kappa_s with 0 <= kappa_s <= kappa_max
  (|exp(-i kappa s) - 1| <= kappa);
* Bessel J0, J1 against scipy.special: 1e-14 absolute.
"""
import math

import numpy as np
import pytest

from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A
from reflection_holo.optics import (ArtefactOptions, Grid, MemberPairs, SurfacePlasmonLoss, Wave,
                                    ensemble_hologram_intensity, hologram_intensity,
                                    partially_coherent_hologram, reference_r1_vacuum_plane_wave,
                                    reference_r2_self_reference)
from reflection_holo.optics import coherence as C

NONE = ArtefactOptions(biprism_fresnel_fringes=None, drift=None, charging_phase_rad=None)
LAB = "TEST_ONLY: stands in for PROJECT_INPUT item 3"
LAM = wavelength_A(200.0)
K = k_ang_per_A(200.0)
TH0 = 16.47e-3
FFT_TOL = 1e-13


def no_loss():
    return SurfacePlasmonLoss(mean_excitations_object=0.0, object_label="TEST_ONLY: n = 0",
                              mean_excitations_reference=0.0, reference_label="TEST_ONLY: n = 0",
                              loss_visibility=0.1, visibility_label="TEST_ONLY: V_loss",
                              energy_filter="none", energy_filter_label="TEST_ONLY: unfiltered")


def grid(shape=(64, 64), px=(0.5, 0.5)):
    return Grid(shape=shape, pixel_size_A=px, axes=("along_beam", "perpendicular"),
                plane="image plane (TEST_ONLY)")


def quad(profile, alpha, v, tol, psi=None):
    mq = C.minimal_quadrature(profile, phase_extent_rad=v, curvature_rad=0.0, tolerance=tol)
    return C.ConvergenceQuadrature(semi_angle_rad=alpha, semi_angle_label=LAB,
                                   source_profile=profile, n_radial=mq["n_radial"],
                                   n_azimuthal=mq["n_azimuthal"],
                                   line_azimuth_rad=psi, design_phase_extent_rad=v,
                                   design_curvature_rad=0.0, tolerance=tol)


def synthetic_visibility(q, E):
    """Hologram of a uniform object and an R1 plane-wave reference of equal amplitude (mu_0 = 1);
    member s multiplies the object by exp(i dk_s.E). Returns the complex degree of coherence
    measured on the hologram: 2 F(q_c) / F(0) (conjugated to the object-minus-reference phase)."""
    g = grid()
    qc = (0.0, 0.25)                                      # on-grid carrier (16 px/fringe)
    ref = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=qc, amplitude=1.0,
                                         relative_phase_rad=0.0, aperture_passage="no_aperture",
                                         realisation=0)
    members = []
    for m in q.members():
        ph = float(m.dk_in(K, TH0) @ np.asarray(E, float))
        obj = Wave(np.full(g.shape, np.exp(1j * ph)), g, "uniform object (TEST_ONLY)", 0)
        members.append(MemberPairs(index=m.index, weight=m.weight, pairs=((obj, ref),)))
    H = partially_coherent_hologram(members, loss=no_loss(), artefacts=NONE, content="object")
    F = np.fft.fft2(H.intensity)
    k1 = int(round(-qc[1] * g.shape[1] * g.pixel_size_A[1])) % g.shape[1]
    # I = 2 + 2 Re(mu exp(-2 pi i q_c.r)): the component at -q_c is mu, at +q_c conj(mu)
    return 2.0 * F[0, k1] / F[0, 0] / 1.0 * 1.0, H


def e_perp(v, alpha, direction):
    """Separation E (A) perpendicular to b0 with k alpha |E| = v along the transverse unit vector
    cos(direction) e_a + sin(direction) e_b."""
    ea, eb = C.transverse_basis(TH0)
    return (v / (K * alpha)) * (math.cos(direction) * ea + math.sin(direction) * eb)


# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("v", [0.5, 2.0, 3.8317059702075125, 5.0])
def test_visibility_follows_2J1v_over_v_for_a_uniform_disc(v):
    """DERIVED_HERE (van Cittert-Zernike, flat incoherent source). Member s illuminates the object
    and the reference points with the phase difference dk_s.E; its hologram is
    I_s = |A e^(i dk_s.E) + A e^(i 2 pi q_c.r)|^2 = 2A^2 [1 + cos(2 pi q_c.r - dk_s.E)]. The ensemble
    after squaring is I = 2A^2 [1 + Re(mu e^(-2 pi i q_c.r))] with mu = sum_s w_s e^(i dk_s.E): the
    visibility is |mu| and the fringe shift arg(mu). For E perpendicular to b0, dk_s.E = k t_s.E
    exactly (the (sqrt(1 - t^2) - 1) b0 part of dk is orthogonal to E), and for the continuous
    uniform disc |t| <= alpha, with t = alpha rho (cos phi, sin phi):
        mu = (1/pi) int_0^1 rho d rho int_0^2pi e^(i v rho cos(phi - psi)) d phi
           = 2 int_0^1 J0(v rho) rho d rho = 2 J1(v)/v,   v = k alpha |E|,
    using int_0^2pi e^(i x cos phi) d phi = 2 pi J0(x) and d(x J1(x))/dx = x J0(x). The fringe
    visibility therefore falls with the convergence as |2 J1(v)/v| (zero at v = 3.8317, the first
    zero of J1) and the fringes reverse (arg mu = pi) between the first and second zeros."""
    alpha = 2e-5
    q = quad("uniform_disc", alpha, v, 1e-10)
    mu, H = synthetic_visibility(q, e_perp(v, alpha, 0.7))
    want = float(C.disc_coherence_factor(v))
    assert abs(mu - want) <= q.error_bound() + FFT_TOL
    if v == 5.0:
        assert want < 0 and abs(np.angle(mu)) == pytest.approx(np.pi, abs=1e-9)
    assert H.metadata["n_members"] == q.n_members and "after squaring" in H.metadata["formation"]


def test_visibility_falls_with_convergence_for_a_fixed_separation():
    E = e_perp(1.0, 1e-5, 0.0)                           # |E| with k alpha |E| = 1 at 10 urad
    last = 1.0
    for alpha in (2e-6, 5e-6, 1e-5, 2e-5, 3e-5):
        v = K * alpha * np.linalg.norm(E)
        q = quad("uniform_disc", alpha, v, 1e-10)
        mu, _ = synthetic_visibility(q, E)
        want = float(C.disc_coherence_factor(v))
        assert abs(mu - want) <= q.error_bound() + FFT_TOL
        assert abs(mu) < last
        last = abs(mu)


@pytest.mark.parametrize("v", [0.7, 3.0, np.pi])
def test_visibility_follows_sinc_for_a_uniform_line_source(v):
    """DERIVED_HERE: a uniform line (top hat) t = alpha xi l, xi in [-1, 1], with E along the line
    direction l: mu = (1/2) int_-1^1 e^(i v xi) d xi = sin(v)/v, v = k alpha E.l (zero at v = pi)."""
    alpha, psi = 1.5e-5, 0.3
    q = quad("uniform_line", alpha, v, 1e-10, psi=psi)
    mu, _ = synthetic_visibility(q, e_perp(v, alpha, psi))
    assert abs(mu - float(C.line_coherence_factor(v))) <= q.error_bound() + FFT_TOL


def test_single_member_reproduces_the_existing_hologram_bit_for_bit():
    """One direction (the central one, weight 1) and no loss: partially_coherent_hologram equals
    hologram_intensity (one realisation) and ensemble_hologram_intensity (several) exactly."""
    g = grid()
    rng = np.random.default_rng(3)
    ref = lambda r: reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.125, 0.25),  # noqa
                                                   amplitude=0.8, relative_phase_rad=0.3,
                                                   aperture_passage="no_aperture", realisation=r)
    objs = [Wave((0.5 + rng.random(g.shape)) * np.exp(1j * rng.uniform(-3, 3, g.shape)), g,
                 "object", r) for r in range(3)]
    one = partially_coherent_hologram([MemberPairs(index=0, weight=1.0,
                                                   pairs=((objs[0], ref(0)),))],
                                      loss=no_loss(), artefacts=NONE, content="object")
    assert np.array_equal(one.intensity,
                          hologram_intensity(objs[0], ref(0), artefacts=NONE,
                                             content="object").intensity)
    many = partially_coherent_hologram([MemberPairs(index=0, weight=1.0,
                                                    pairs=tuple((o, ref(o.realisation))
                                                                for o in objs))],
                                       loss=no_loss(), artefacts=NONE, content="object")
    assert np.array_equal(many.intensity, ensemble_hologram_intensity(
        [(o, ref(o.realisation)) for o in objs], artefacts=NONE, content="object").intensity)


def test_ensemble_rules_weights_indices_and_pairing():
    g = grid()
    ref = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=(0.0, 0.25), amplitude=1.0,
                                         relative_phase_rad=0.0, aperture_passage="no_aperture",
                                         realisation=0)
    obj = Wave(np.ones(g.shape), g, "o", 0)
    p = ((obj, ref),)
    for bad in ([MemberPairs(0, 0.5, p), MemberPairs(1, 0.4, p)],        # weights sum 0.9
                [MemberPairs(0, 0.5, p), MemberPairs(0, 0.5, p)],        # duplicate index
                [MemberPairs(0, -0.5, p), MemberPairs(1, 1.5, p)]):      # negative weight
        with pytest.raises(ValueError):
            partially_coherent_hologram(bad, loss=no_loss(), artefacts=NONE, content="object")
    with pytest.raises(TypeError):
        partially_coherent_hologram([MemberPairs(0, 1.0, p)], loss=None, artefacts=NONE,
                                    content="object")
    with pytest.raises(ValueError, match="realisation"):
        partially_coherent_hologram([MemberPairs(0, 1.0, ((obj, ref), (obj, ref)))],
                                    loss=no_loss(), artefacts=NONE, content="object")


# ---------------------------------------------------------------------------------------------
# quadrature: exactness, error bound, refusal
# ---------------------------------------------------------------------------------------------
def disc_monomial_mean(i, j, alpha):
    """Exact mean of t_a^i t_b^j over the uniform disc |t| <= alpha."""
    if i % 2 or j % 2:
        return 0.0
    ang = 2 * math.gamma((i + 1) / 2) * math.gamma((j + 1) / 2) / math.gamma((i + j) / 2 + 1)
    return alpha ** (i + j) * ang / (math.pi * (i + j + 2))


@pytest.mark.parametrize("n_r,n_az", [(1, 4), (2, 5), (3, 16), (4, 9)])
def test_disc_rule_is_exact_to_the_stated_degree_and_no_further(n_r, n_az):
    alpha = 1.0                                             # scale-free check
    q = C.ConvergenceQuadrature(semi_angle_rad=0.01, semi_angle_label=LAB,
                                source_profile="uniform_disc", n_radial=n_r, n_azimuthal=n_az,
                                line_azimuth_rad=None, design_phase_extent_rad=0.0,
                                design_curvature_rad=0.0, tolerance=0.5)
    D = q.polynomial_degree_exact()
    assert D == min(n_az - 1, 4 * n_r - 1)
    nodes = np.array(q.nodes())
    ta, tb, w = nodes[:, 0] / 0.01 * alpha, nodes[:, 1] / 0.01 * alpha, nodes[:, 2]
    assert w.sum() == pytest.approx(1.0, abs=1e-15)
    for d in range(D + 1):
        for i in range(d + 1):
            got = float(np.sum(w * ta ** i * tb ** (d - i)))
            assert got == pytest.approx(disc_monomial_mean(i, d - i, alpha), abs=1e-14), (i, d - i)
    # degree D + 1 is not integrated exactly by at least one monomial
    d = D + 1
    errs = [abs(float(np.sum(w * ta ** i * tb ** (d - i))) - disc_monomial_mean(i, d - i, alpha))
            for i in range(d + 1)]
    assert max(errs) > 1e-6


@pytest.mark.parametrize("n_r,n_az,v", [(1, 3, 1.0), (2, 6, 3.0), (3, 8, 3.0), (2, 12, 6.0),
                                        (5, 20, 6.0)])
def test_disc_error_bound_holds(n_r, n_az, v):
    b = C.quadrature_error_bound("uniform_disc", n_r, n_az, phase_extent_rad=v, curvature_rad=0.0)
    x, w = np.polynomial.legendre.leggauss(n_r)
    for psi in (0.0, 0.4, 1.3):
        got = sum(wj / (2 * n_az) * np.exp(1j * v * math.sqrt(0.5 * (1 + xj))
                                             * math.cos(2 * math.pi * m / n_az - psi))
                  for xj, wj in zip(x, w) for m in range(n_az))
        assert abs(got - float(C.disc_coherence_factor(v))) <= b


def test_disc_error_bound_holds_with_curvature():
    """kappa > 0: the exact mean int_0^1 J0(v sqrt(s)) exp(-i kappa s) ds from a converged
    reference rule (n_radial 30, n_azimuthal 40; its own bound, rounding floor included, < 1e-10)."""
    v, kap = 2.5, 0.8
    ref_b = C.quadrature_error_bound("uniform_disc", 30, 40, phase_extent_rad=v, curvature_rad=kap)
    assert ref_b < 1e-10

    def rule(n_r, n_az):
        x, w = np.polynomial.legendre.leggauss(n_r)
        return sum(wj / (2 * n_az) * np.exp(1j * v * math.sqrt(0.5 * (1 + xj))
                                              * math.cos(2 * math.pi * m / n_az - 0.2)
                                              - 1j * kap * 0.5 * (1 + xj))
                   for xj, wj in zip(x, w) for m in range(n_az))
    exact = rule(30, 40)
    for n_r, n_az in ((1, 4), (2, 6), (4, 10)):
        b = C.quadrature_error_bound("uniform_disc", n_r, n_az, phase_extent_rad=v,
                                     curvature_rad=kap)
        assert abs(rule(n_r, n_az) - exact) <= b + ref_b


@pytest.mark.parametrize("n,v", [(1, 0.5), (2, 2.0), (4, 3.0), (8, 6.0)])
def test_line_error_bound_holds(n, v):
    b = C.quadrature_error_bound("uniform_line", n, None, phase_extent_rad=v, curvature_rad=0.0)
    x, w = np.polynomial.legendre.leggauss(n)
    got = np.sum(w / 2 * np.exp(1j * v * x))
    assert abs(got - float(C.line_coherence_factor(v))) <= b


def test_declared_quadrature_refused_above_its_tolerance_and_inputs_required():
    kw = dict(semi_angle_rad=1e-5, semi_angle_label=LAB, source_profile="uniform_disc",
              n_radial=1, n_azimuthal=2, line_azimuth_rad=None, design_phase_extent_rad=3.0,
              design_curvature_rad=0.0, tolerance=1e-6)
    with pytest.raises(ValueError, match="smallest quadrature"):
        C.ConvergenceQuadrature(**kw)
    ok = dict(kw, n_radial=3, n_azimuthal=13)
    q = C.ConvergenceQuadrature(**ok)
    rec = q.as_record(TH0)
    assert rec["error_bound"] <= 1e-6 and rec["n_members"] == 39 == len(rec["members"])
    assert rec["minimal_quadrature_for_the_design"]["members"] <= 39
    assert "justification" in rec and rec["analytic_limit"] == "2 J1(v)/v"
    for bad in (dict(semi_angle_rad=0.0), dict(semi_angle_rad=float("nan")),
                dict(semi_angle_label="convergence 0.1 mrad"), dict(source_profile="gaussian"),
                dict(n_radial=0), dict(n_azimuthal=None), dict(line_azimuth_rad=0.1),
                dict(tolerance=0.0), dict(design_phase_extent_rad=-1.0)):
        with pytest.raises((ValueError, TypeError)):
            C.ConvergenceQuadrature(**dict(ok, **bad))
    with pytest.raises(ValueError, match="line_azimuth_rad"):
        C.ConvergenceQuadrature(**dict(ok, source_profile="uniform_line", n_azimuthal=None))


def test_bessel_functions_against_scipy():
    special = pytest.importorskip("scipy.special")
    v = np.linspace(0.0, 60.0, 601)
    assert np.max(np.abs(C.bessel_j(0, v) - special.j0(v))) <= 1e-14
    assert np.max(np.abs(C.bessel_j(1, v) - special.j1(v))) <= 1e-14
    x = np.array([1e-9, 1e-3, 1.0, 3.8317059702075125, 7.0])
    assert np.max(np.abs(C.disc_coherence_factor(x) - 2 * special.j1(x) / x)) <= 1e-14


# ---------------------------------------------------------------------------------------------
# member geometry and the reflection-specific illumination phases
# ---------------------------------------------------------------------------------------------
def test_rotation_and_mirror_frame():
    b0 = C.central_direction(TH0)
    R = C.rotation_2theta(TH0)
    assert np.allclose(R @ b0, C.mirror_x(b0), atol=1e-16)
    ea, eb = C.transverse_basis(TH0)
    assert abs(ea @ b0) < 1e-17 and np.allclose(R @ ea, [-math.cos(TH0), 0, math.sin(TH0)],
                                                  atol=1e-16)
    assert np.allclose(R.T @ R, np.eye(3), atol=1e-15)


def test_r1_vacuum_reference_coherence_is_confined_near_the_zero_path_difference_line():
    """DERIVED_HERE (report E3 section 2.3). Flat surface (mirror at x_m) imaged with the specular
    beam; R1 reference split from the same source point and pre-tilted by 2 theta (condenser
    biprism, B28), so dk_ref = R_y(2 th0) dk_in. With dk_in = k[(sqrt(1-t^2) - 1) b0 + t_a e_a +
    t_b e_b], mirror(e_a) = (c, 0, -s), R e_a = (-c, 0, s) and R b0 = mirror(b0), the member phase
    between object (dk_out.Q + 2 dk_in,x x_m) and reference (dk_ref.(Q - D0)) at the exit-plane
    point Q is exactly
        phi_s(Q) = k [t_a E_a(Q) + t_b E_b] - kappa_s,
        E_a = 2c (Q_x - x_m) - 2s Q_z - c D0_x + s D0_z,   E_b = D0_y,
        kappa_s = k (1 - sqrt(1 - t_s^2)) (mirror(b0).D0 - 2 s x_m)    (Q-independent),
    so for a uniform disc the coherence is 2 J1(v)/v with v(Q) = k alpha |(E_a, E_b)| up to
    kappa_max. Along the exit plane Q_x - x_m = x_m-relative height of the ray from the surface
    point z_s, i.e. E_a = -2 sin(theta) z_s + const = -2 u + const (u = z_s sin theta, the image
    coordinate): the fringes are coherent only within |u - u*| ~ 1/(2 k alpha) of the line where
    object and reference coincide (a Lloyd's-mirror geometry), whatever the separation."""
    alpha, x_m, Lz = 1e-5, 40.0, 3000.0
    D0 = np.array([12.0, 30.0, -50.0])
    x = np.linspace(x_m, x_m + 900.0, 181)
    X, Y, Z = x, np.zeros_like(x), np.full_like(x, Lz)
    c, s = math.cos(TH0), math.sin(TH0)
    Ea = 2 * c * (X - x_m) - 2 * s * Z - c * D0[0] + s * D0[2]
    v = K * alpha * np.hypot(Ea, D0[1])
    kappa_max = K * alpha ** 2 / 2 * 1.0001 * abs(C.mirror_x(C.central_direction(TH0)) @ D0
                                                  - 2 * s * x_m)
    q = quad("uniform_disc", alpha, float(v.max()), 1e-9)
    ms = q.members()
    ph = [C.flat_mirror_member_phase(m, k_rad_per_A=K, theta0_rad=TH0, exit_points_A=(X, Y, Z),
                                     mirror_height_A=x_m)
          - C.r1_reference_member_phase(m, k_rad_per_A=K, theta0_rad=TH0,
                                        exit_points_A=(X, Y, Z), separation_A=D0,
                                        aperture_passage="condenser_biprism_pretilt")
          for m in ms]
    mu = C.ensemble_coherence(ms, ph)
    tol = C.quadrature_error_bound("uniform_disc", q.n_radial, q.n_azimuthal,
                                   phase_extent_rad=float(v.max()), curvature_rad=kappa_max) \
        + kappa_max
    assert np.max(np.abs(mu - C.disc_coherence_factor(v))) <= tol
    # a linear phase ramp of slope 2c per A of exit-plane height, i.e. -2 per A of image u
    assert np.abs(mu).max() > 0.99 and np.abs(mu).min() < 0.2
    with pytest.raises(NotImplementedError):
        C.r1_reference_member_phase(ms[0], k_rad_per_A=K, theta0_rad=TH0, exit_points_A=(X, Y, Z),
                                    separation_A=D0, aperture_passage="second_aperture_hole")


def test_r2_self_reference_coherence_depends_on_the_shift_only():
    """R2: both arms are the specular wave of the same flat surface, the reference taken at the
    shifted exit-plane point Q + s: phi_s = dk_out,s.(Q - (Q + s)) = -dk_out,s.s (constant). With
    mirror(e_a) = (c, 0, -s') the effective separation is (-c s_x, -s_y) (s_z = 0 on the exit
    plane), so the disc coherence is 2 J1(v)/v, v = k alpha sqrt((c s_x)^2 + s_y^2), everywhere
    in the overlap (no Lloyd's-mirror confinement)."""
    alpha = 1e-5
    g = Grid(shape=(48, 40), pixel_size_A=(2.0, 3.0), axes=("x", "y"), plane="exit plane (TEST)")
    X, Y = g.coordinates_A()
    Z = np.full(g.shape, 2500.0)
    shift = (10.0, 36.0)                                   # 5 and 12 pixels
    c = math.cos(TH0)
    v = K * alpha * math.hypot(c * shift[0], shift[1])
    q = quad("uniform_disc", alpha, v, 1e-10)
    members = []
    for m in q.members():
        ph = C.flat_mirror_member_phase(m, k_rad_per_A=K, theta0_rad=TH0, exit_points_A=(X, Y, Z),
                                        mirror_height_A=0.0)
        obj = Wave(np.exp(1j * ph), g, "flat surface (TEST_ONLY)", 0)
        ref = reference_r2_self_reference(obj, shift_A=shift, carrier_cycles_per_A=(0.0, 1 / 12),
                                          amplitude_scale=1.0, relative_phase_rad=0.0)
        members.append(MemberPairs(index=m.index, weight=m.weight, pairs=((obj, ref),)))
    H = partially_coherent_hologram(members, loss=no_loss(), artefacts=NONE, content="object")
    valid = H.metadata["valid_mask"]
    # visibility per pixel from the member phases directly (the hologram is 2 + 2 Re(...)):
    mu = C.ensemble_coherence(q.members(), [-(m.dk_out_specular(K, TH0) @ np.array([shift[0],
                                                                                   shift[1], 0.0]))
                                            for m in q.members()])
    # the quadratic part of dk_out along mirror(b0) = (s', 0, c) adds kappa_s <= k alpha^2/2 s' s_x
    kappa_max = K * alpha ** 2 / 2 * 1.0001 * math.sin(TH0) * abs(shift[0])
    assert abs(mu - float(C.disc_coherence_factor(v))) <= q.error_bound() + kappa_max
    Icheck = 2 + 2 * np.real(mu * np.exp(-2j * np.pi * Y / 12))
    assert np.max(np.abs(H.intensity[valid] - Icheck[valid])) <= 1e-12
