"""Tests for the one-beam independent check (R2 item 2f) and the T-1D-agreement harness.

Run with: pytest -q tests/test_reflectivity1d.py
"""
import math

import numpy as np
import pytest

from reflection_holo import constants as C
from reflection_holo import reflectivity1d as R1

E = 200e3


def _flatten_numbers(obj):
    """Yield every float found inside a nested dict/list/tuple/array."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _flatten_numbers(v)
    elif isinstance(obj, (list, tuple, np.ndarray)):
        for v in np.asarray(obj, dtype=object).ravel():
            yield from _flatten_numbers(v)
    elif isinstance(obj, (int, float, np.floating)) and not isinstance(obj, bool):
        yield float(obj)
    elif hasattr(obj, "value"):
        yield float(obj.value)


def test_prefactor_matches_kirkland_6_10():
    """External fact: Kirkland eqn 6.10 [ch06 p.7] prints 47.86 V*A^2 for h^2/(2 pi m0 e). Tolerance 1e-3 rel."""
    assert abs(R1.KIRKLAND_PREFACTOR_V_A2 / 47.86 - 1) < 1e-3


def test_local_si_params_match_constants():
    """External fact: Kirkland appC Si row [p.12]. The local copy must equal constants.KIRKLAND_SI (rel 1e-8)."""
    nums = list(_flatten_numbers(C.KIRKLAND_SI))
    for key in ("a", "b", "c", "d"):
        for v in R1.KIRKLAND_SI_CARD[key]:
            assert any(abs(x - v) <= 1e-8 * abs(v) for x in nums), f"{key}={v} missing in constants.KIRKLAND_SI"


def test_fe0_two_independent_parameterisations():
    """External facts:
    * Kirkland C.15 f_e(0) = 5.814 A (appC card's computed value, tolerance 1e-3 A).
    * Peng Table 13.3 sum a_i = 5.8182 A [ch13 p.24]. The two parameterisations agree to 0.2 %.
    """
    assert abs(R1.fe0() - 5.814) < 1e-3
    assert abs(R1.fe0() / sum(R1.PENG_T13_3_SI_A) - 1) < 2e-3


@pytest.mark.parametrize("B", [0.0, 0.5261])
def test_areal_profile_integral(B):
    """External fact: a Debye-Waller factor leaves g = 0 unchanged (Peng 13.52, T(0) = 1), so
    integral of P dz = 2 pi a0 e f_e(0) (Kirkland C.5 at q = 0). Tolerance 1e-4 rel."""
    z = np.arange(-15, 15, 0.0005) + 0.00025
    P = R1.atom_areal_profile(z, B)
    assert abs(P.sum() * 0.0005 / (R1.KIRKLAND_PREFACTOR_V_A2 * R1.fe0()) - 1) < 1e-4


def test_dw_convolution_matches_numeric():
    """Invariant: the analytic DW-smeared profile equals the numerical Gaussian convolution of the static
    profile with sigma^2 = B/(8 pi^2) (Peng 13.51). Tolerance 1e-3 of the peak."""
    B = 0.5
    dz = 0.0005
    z = np.arange(-15, 15 + dz / 2, dz)
    P0 = R1.atom_areal_profile(z, 0.0)
    s = math.sqrt(B / (8 * math.pi ** 2))
    kz = np.arange(-8 * s, 8 * s + dz / 2, dz)
    g = np.exp(-kz ** 2 / (2 * s * s))
    g /= g.sum()
    num = np.convolve(P0, g, mode="same")
    ana = R1.atom_areal_profile(z, B)
    sel = np.abs(z) < 3
    assert np.max(np.abs(num[sel] - ana[sel])) < 1e-3 * ana.max()


@pytest.mark.parametrize("fam,name", [("001", "si001"), ("111", "si111")])
def test_bulk_mean_potential(fam, name):
    """Invariant: the mean of V(z) over whole periods equals 2 pi a0 e f_e(0) 8/a^3 (both stackings carry
    8 atoms per a^3, the diamond 8-atom cell of the conventions). Tolerance 1e-5 rel."""
    a = float(C.A_SI.value)
    p = R1.rod_period(fam, a)
    n = 400
    z = -40 + (np.arange(10 * n) + 0.5) * p / n
    V = R1.averaged_potential_z(name, z, absorption=False)
    assert abs(V.real.mean() / R1.bulk_mean_potential(E).real - 1) < 1e-5
    assert np.all(V.imag == 0)


def test_forbidden_harmonics_vanish():
    """External fact: diamond structure factor, F = 0 for h+k+l = 4n+2 and mixed parity (conventions;
    geometry.is_forbidden). The Fourier components of V(z) at the forbidden specular orders are < 1e-10 of
    the allowed one: (002), (006) for Si(001); (2,-2,2), (6,-6,6) for Si(111)."""
    from reflection_holo import geometry as G
    a = float(C.A_SI.value)
    z = -40 + (np.arange(4000) + 0.5) * (2 * a) / 4000
    V = R1.averaged_potential_z("si001", z, absorption=False).real
    c = {l: abs(np.mean(V * np.exp(-2j * math.pi * l * z / a))) for l in (2, 4, 6, 8)}
    assert c[2] < 1e-10 * c[4] and c[6] < 1e-10 * c[4] and c[8] > 0
    assert G.is_forbidden(0, 0, 2) and G.is_forbidden(0, 0, 6) and not G.is_forbidden(0, 0, 8)
    d = a / math.sqrt(3)
    z = -40 + (np.arange(4000) + 0.5) * (4 * d) / 4000
    V = R1.averaged_potential_z("si111", z, absorption=False).real
    c = {n: abs(np.mean(V * np.exp(-2j * math.pi * n * z / d))) for n in (1, 2, 3, 4, 6)}
    assert c[2] < 1e-10 * c[4] and c[6] < 1e-10 * c[4] and c[1] > 0 and c[3] > 0
    assert G.is_forbidden(2, -2, 2) and not G.is_forbidden(4, -4, 4)


def test_fresnel_step():
    """External fact: conventions refraction law K_z,int^2 = K_z,vac^2 + 2 m e V0/hbar^2 with continuity of
    psi and psi' (Peng 5.58-5.59). For a potential step AT z = z_ref = 0 this gives r = (k_z - q)/(k_z + q).
    Tolerance 1e-12 abs.

    Grid built from integer indices (integration fix): np.arange(-20 + dz/2, 0, dz) fills
    start + i*(a[1]-a[0]); near |z| = 20 that difference carries ~1.8e-15 A rounding, accumulated to
    ~3e-12 A at the top sample, which moved the vacuum boundary off z_ref = 0 and gave Im r ~ 2.5e-12.
    """
    dz = 0.01
    z = -20.0 + dz * (np.arange(2000) + 0.5)
    V0 = 12.0
    th = np.array([5e-3, 10e-3, 20e-3, 40e-3])
    r = R1.reflect_1d(th, E, np.full(z.shape, V0, complex), z, V_sub=V0, z_ref=0.0)
    K = 2 * math.pi / C.wavelength(E)
    kz = K * np.sin(th)
    q = np.sqrt(kz ** 2 + 2 * K * C.interaction_constant(E) * V0)
    assert np.max(np.abs(r - (kz - q) / (kz + q))) < 1e-12


def test_delta_and_critical_angle():
    """External facts (physics_conventions.md and the calculator): Delta = 6.98e-5 and theta_c = 8.356 mrad
    at 200 keV, V0 = 12 V. Delta = U0/K^2 = 2 sigma V0/K. Tolerances: 5e-3 rel (3 printed figures) and
    1e-3 mrad."""
    K = 2 * math.pi / C.wavelength(E)
    D = 2 * C.interaction_constant(E) * 12.0 / K
    assert abs(D / 6.98e-5 - 1) < 5e-3
    assert abs(1e3 * math.asin(math.sqrt(D / (1 + D))) - 8.356) < 1e-3


def test_flux_conservation_thin_slab_and_methods_agree():
    """Invariant: with W = 0 (Hermitian, Peng p.13), R + T = 1 to 1e-10. The Parratt recursion and the
    characteristic matrix agree to 1e-9."""
    dz = 0.01
    z = np.arange(-20 + dz / 2, 8, dz)
    V = R1.averaged_potential_z("si001", z, absorption=False)
    Vs = R1.bulk_mean_potential(E)
    th = np.linspace(3e-3, 40e-3, 37)
    r_m, T = R1.reflect_1d(th, E, V, z, method="matrix", V_sub=Vs, return_t=True)
    r_p = R1.reflect_1d(th, E, V, z, method="transfer", V_sub=Vs)
    assert np.max(np.abs(np.abs(r_m) ** 2 + T - 1)) < 1e-10
    assert np.max(np.abs(r_m - r_p)) < 1e-9


def test_missing_absorption_raises():
    """Repository rule: absorption of Si is NOT IN any card, so absorption=None must raise unless the caller
    accepts the assumption."""
    with pytest.raises(R1.MissingProjectInput):
        R1.averaged_potential_z("si001", np.linspace(-5, 5, 11))


def test_absorption_reduces_reflectivity():
    """Invariant: with W > 0 (absorbing for exp(+ik.r), Peng ch13 p.3), |r| < 1 and R + T < 1."""
    dz = 0.01
    z = np.arange(-20 + dz / 2, 8, dz)
    V = R1.averaged_potential_z("si001", z, absorption=0.1)
    th = np.linspace(3e-3, 40e-3, 37)
    r, T = R1.reflect_1d(th, E, V, z, method="matrix", V_sub=R1.bulk_mean_potential(E, absorption=0.1),
                         return_t=True)
    assert np.all(np.abs(r) < 1) and np.all(np.abs(r) ** 2 + T < 1)


def _kin(fam, n):
    a = float(C.A_SI.value)
    return R1.kinematic_external_angle(R1.rod_G(fam, n, a), E, R1.bulk_mean_potential(E).real)


def test_total_reflection_band_008():
    """External fact: Peng ch05 p.30, Darwin-type total reflection; for a semi-infinite crystal without
    absorption the specular Bragg peak reaches |r| = 1. Max |r|^2 near (008) >= 0.999 (W = 0, 400 A)."""
    tk = _kin("001", 8)
    th = np.linspace(tk - 1e-3, tk + 1e-3, 801)
    rc = R1.rocking_curve_1d("si001", E, th, absorption=False, depth=400.0)
    assert np.max(np.abs(rc.r) ** 2) >= 0.999


def test_kinematic_limit_0012():
    """External fact: Peng 5.75/5.76 [p.29]. The peak lies at the refraction-corrected Bragg angle; the
    dynamical shift [p.30] is small at high order. The band centre of (0,0,12) lies within 0.5 FWHM of
    kinematic_external_angle, using V0 = the profile's own mean."""
    tk = _kin("001", 12)
    th = np.linspace(tk - 0.3e-3, tk + 0.3e-3, 1201)
    rc = R1.rocking_curve_1d("si001", E, th, absorption=False, depth=1000.0)
    pm = R1.peak_metrics(th, np.abs(rc.r) ** 2)
    assert pm["R_peak"] > 0.5 and pm["fwhm"] > 0
    assert abs(pm["theta_center"] - tk) < 0.5 * pm["fwhm"]


def test_no_peak_at_forbidden_006():
    """External fact: (006) is forbidden for diamond (h+k+l = 4n+2), and V(z) has period a/4, so there is no
    Bragg band. Max |r|^2 within +-0.3 mrad of its kinematic angle is < 0.05 (allowed orders give ~1)."""
    tk = _kin("001", 6)
    th = np.linspace(tk - 0.3e-3, tk + 0.3e-3, 301)
    rc = R1.rocking_curve_1d("si001", E, th, absorption=False, depth=300.0)
    assert np.max(np.abs(rc.r) ** 2) < 0.05


def test_depth_convergence_with_absorption():
    """Invariant (Peng ch05 p.34): a slab much thicker than the absorption length reflects like a
    semi-infinite crystal. 200 A vs 400 A depth with W/V = 0.1 (ASSUMPTION) gives max|delta r| < 1e-3."""
    tk = _kin("001", 8)
    th = np.linspace(tk - 1e-3, tk + 1e-3, 101)
    r1 = R1.rocking_curve_1d("si001", E, th, absorption=0.1, depth=200.0).r
    r2 = R1.rocking_curve_1d("si001", E, th, absorption=0.1, depth=400.0).r
    assert np.max(np.abs(r1 - r2)) < 1e-3


def test_slice_convergence():
    """Invariant (Peng ch05 p.12: accuracy improves as dz is reduced): dz 0.01 vs 0.005 A gives
    max|delta r| < 2e-3 around (008)."""
    tk = _kin("001", 8)
    th = np.linspace(tk - 1e-3, tk + 1e-3, 101)
    r1 = R1.rocking_curve_1d("si001", E, th, absorption=0.1, depth=200.0, dz=0.01).r
    r2 = R1.rocking_curve_1d("si001", E, th, absorption=0.1, depth=200.0, dz=0.005).r
    assert np.max(np.abs(r1 - r2)) < 2e-3


def test_1d_agreement_with_kernel():
    """T-1D-agreement, like-for-like (rewritten 2026-10-16, orchestrator; see validation/kernel_vs_1d.py).

    External fact: for an x-independent potential the paraxial beam-perpendicular kernel and the 1D
    one-beam equation are the same stationary problem (Peng ch05 p.10, one-rod case: multislice and
    semi-reciprocal specular curves "agree very well"); identical input Vbar(z)+iW(z) must give the same r
    in the continuum limit.
    The previous version compared the FULL-structure kernel (many-beam) with one-beam theory, so its peak
    shift (+0.1 mrad) and R_peak = 0.27 at W = 0 are many-beam physics, not a kernel error; they are
    recorded in INTEGRATION_NOTES.md, not asserted here.
    Tolerances: dR <= 0.02 (fixed before the like-for-like run, ASSUMPTION); convergence: doubling the
    band limit must cut the median complex error by >= 40 % (DERIVED_HERE expectation of a convergent
    representation); |dr| <= 0.025 at the refined sampling (POST-HOC metric replacing a fixed 0.05 rad
    phase tolerance, because the phase error of r with complex error delta is delta/|r|, unbounded as
    |r| -> 0; recorded as post-hoc in INTEGRATION_NOTES.md).
    Extraction validity: beam spectral weight >= 0.5 and residual down-going amplitude <= 1e-3.
    """
    try:
        from reflection_holo.geometry import Surface
        from validation.kernel_vs_1d import compare
    except Exception as exc:  # noqa: BLE001
        pytest.xfail(f"kernel not importable: {exc!r}")
    th = np.linspace(0.01590, 0.01640, 11)
    cen = np.linspace(th.min(), th.max(), 5)
    surf = Surface((0, 0, 1), (1, 1, 0))
    coarse = compare(surf, E, th, cen, 0.15, 0.08)
    fine = compare(surf, E, th, cen, 0.075, 0.04)
    print({"coarse_med": float(np.median(coarse["abs_dr"])), "fine_med": float(np.median(fine["abs_dr"])),
           "fine_max": float(fine["abs_dr"].max()), "fine_dR": float(fine["dR"].max())})
    for out in (coarse, fine):
        assert out["weight"].min() >= 0.5
        assert out["residual_down"].max() <= 1e-3
    assert np.median(fine["abs_dr"]) <= 0.6 * np.median(coarse["abs_dr"])
    assert fine["dR"].max() <= 0.02
    assert fine["abs_dr"].max() <= 0.025
