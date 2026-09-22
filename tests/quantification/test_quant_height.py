"""Signed phase-to-height conversion, wrap period, branch index and the small-denominator policy
(docs/05 section 5 item 8; source map SM03, SM05). Includes the REQUIRED sign test (a down-step
reverses the sign), the height-level no-step control and the refusal test."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.specular import (SpecularCondition, specular_condition_for,
                                               specular_step_phase, wrap_to_pi)
from reflection_holo.quantification.errors import SmallDenominatorError
from reflection_holo.quantification.height import (branch_index_of, height_candidates_A,
                                                    height_from_phase, sensitivity_rad_per_A,
                                                    wrap_period_A)

D111 = A_SI_A / np.sqrt(3.0)
SC444 = specular_condition_for((4, -4, 4), (1, -1, 1), E_keV=E, V0_V=V0, a_A=A_SI_A)
SC008 = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E, V0_V=V0, a_A=A_SI_A)
# TEST_ONLY uncertainties (stand-ins for PROJECT_INPUT items 7 and 1; never used outside tests)
TEST_ONLY_SIGMAS = dict(sigma_phi_rad=0.03, sigma_theta_in_rad=0.05e-3,
                        sigma_theta_out_rad=0.05e-3, sigma_wavelength_rel=1e-6)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


def invert(sc, phase_total, branch_source="test: exact branch from the forward model"):
    w = wrap_to_pi(phase_total)
    m = branch_index_of(phase_total)
    return height_from_phase(w, branch_index=m, branch_source=branch_source,
                             wavelength_A=sc.lam_A, theta_in_ext_rad=sc.theta_ext,
                             theta_out_ext_rad=sc.theta_ext, **TEST_ONLY_SIGMAS)


@pytest.mark.parametrize("sc,h", [(SC444, D111), (SC444, 2 * D111), (SC008, A_SI_A / 2),
                                  (SC008, 100.0)])
def test_round_trip_recovers_signed_height(sc, h):
    est = invert(sc, sc.step_phase(h)["total"])
    check(est.h_A, h, 1e-9)
    check(est.wrap_period_A, sc.h_2pi_A, 1e-12)


def test_sign_down_step_reverses_the_sign():
    """REQUIRED sign test (docs/05 5.8): exp(+ik.r); an up-step (h > 0) has Delta_phi < 0 and a
    down-step (h < 0) the opposite phase; the inverse relation returns the sign."""
    phi_up = SC444.step_phase(+D111)["total"]
    phi_down = SC444.step_phase(-D111)["total"]
    assert phi_up < 0.0 < phi_down
    check(phi_up, -phi_down, 0.0)
    up = invert(SC444, phi_up)
    down = invert(SC444, phi_down)
    assert up.h_A > 0.0 > down.h_A
    check(up.h_A, -down.h_A, 1e-12)
    check(up.h_A, D111, 1e-9)
    # also on the principal branch of a single hologram (branch not resolved)
    assert np.sign(up.h_principal_A) == -np.sign(down.h_principal_A)
    assert up.branch_index == -down.branch_index


def test_formula_matches_spec_expression():
    """h = -Delta_phi lambda / (2 pi (sin theta_in,ext + sin theta_out,ext)) with unequal angles."""
    lam, ti, to = SC444.lam_A, 0.012, 0.016
    phi = -(2 * np.pi / lam) * 1.7 * (np.sin(ti) + np.sin(to))
    est = height_from_phase(wrap_to_pi(phi), branch_index=branch_index_of(phi),
                            branch_source="test", wavelength_A=lam, theta_in_ext_rad=ti,
                            theta_out_ext_rad=to, **TEST_ONLY_SIGMAS)
    check(est.h_A, -phi * lam / (2 * np.pi * (np.sin(ti) + np.sin(to))), 1e-12)
    check(est.h_A, 1.7, 1e-12)
    check(est.wrap_period_A, lam / (np.sin(ti) + np.sin(to)), 1e-15)


def test_T14_wrap_period_via_quantification():
    """T14 through the quantification layer: h_2pi at the (6,-6,6) setting = 0.5575 A +/- 1e-3."""
    sc = SpecularCondition(D111, 6, 200.0, 12.0)
    check(wrap_period_A(wavelength_A=sc.lam_A, theta_in_ext_rad=sc.theta_ext,
                        theta_out_ext_rad=sc.theta_ext), 0.5575, 1e-3)


def test_wrap_and_branch_always_reported():
    """A single hologram of a (4,-4,4) bilayer step: 3.41 wraps (docs/03 section 4); the
    principal branch gives h modulo h_2pi, the branch index and the period are reported."""
    phi = SC444.step_phase(D111)["total"]
    check(abs(phi) / (2 * np.pi), 3.41, 0.005)
    w = wrap_to_pi(phi)
    est = height_from_phase(w, branch_index=0, branch_source="principal branch, single "
                            "hologram: NOT resolved", wavelength_A=SC444.lam_A,
                            theta_in_ext_rad=SC444.theta_ext, theta_out_ext_rad=SC444.theta_ext,
                            **TEST_ONLY_SIGMAS)
    assert est.branch_index == 0 and "NOT resolved" in est.branch_source
    check(est.h_A, est.h_principal_A, 0.0)
    check((D111 - est.h_A) / est.wrap_period_A, round((D111 - est.h_A) / est.wrap_period_A), 1e-9)
    assert branch_index_of(phi) == -3
    cands = height_candidates_A(w, range(-5, 6), wavelength_A=SC444.lam_A,
                                theta_in_ext_rad=SC444.theta_ext,
                                theta_out_ext_rad=SC444.theta_ext)
    assert np.min(np.abs(cands - D111)) < 1e-9


def test_branch_index_definition():
    for p in (-20.0, -3.5, -np.pi, 0.0, 1.0, np.pi, 3.5, 20.0):
        m = branch_index_of(p)
        check(wrap_to_pi(p) + 2 * np.pi * m, p, 1e-12)


def test_no_step_control_at_height_level():
    """No-step control: zero phase gives zero height, branch 0, with a finite uncertainty."""
    est = height_from_phase(0.0, branch_index=0, branch_source="no-step control",
                            wavelength_A=SC444.lam_A, theta_in_ext_rad=SC444.theta_ext,
                            theta_out_ext_rad=SC444.theta_ext, **TEST_ONLY_SIGMAS)
    assert est.h_A == 0.0 and est.branch_index == 0
    check(est.sigma_h_A, 0.03 / est.sensitivity_rad_per_A, 1e-15)


def test_small_denominator_refused_never_divided():
    """Refusal: the sensitivity |q.n_hat| is below its propagated uncertainty -> error, no
    division. Grazing angles of 0.02 mrad with a 0.05 mrad angle uncertainty."""
    with pytest.raises(SmallDenominatorError, match="refused"):
        height_from_phase(0.5, branch_index=0, branch_source="test",
                          wavelength_A=SC444.lam_A, theta_in_ext_rad=0.02e-3,
                          theta_out_ext_rad=0.02e-3, **TEST_ONLY_SIGMAS)
    with pytest.raises(SmallDenominatorError):
        height_from_phase(0.5, branch_index=0, branch_source="test", wavelength_A=SC444.lam_A,
                          theta_in_ext_rad=0.0, theta_out_ext_rad=0.0, sigma_phi_rad=0.03,
                          sigma_theta_in_rad=0.0, sigma_theta_out_rad=0.0,
                          sigma_wavelength_rel=0.0)


def test_small_denominator_boundary():
    """Just above the propagated uncertainty the height is returned with a large sigma_h."""
    lam = SC444.lam_A
    sig = 1e-3
    s_sig = (2 * np.pi / lam) * np.sqrt(2) * sig          # cos ~ 1
    th = 1.5 * s_sig / (2 * (2 * np.pi / lam))            # s = 1.5 sigma_s
    # sigma_wavelength_rel 1e-6 (the TEST_ONLY value above): a zero uncertainty is refused (A2 m2);
    # it adds (1e-6 s)^2 to sigma_s^2, negligible against s = 1.5 sigma_s
    est = height_from_phase(0.1, branch_index=0, branch_source="test", wavelength_A=lam,
                            theta_in_ext_rad=th, theta_out_ext_rad=th, sigma_phi_rad=0.03,
                            sigma_theta_in_rad=sig, sigma_theta_out_rad=sig,
                            sigma_wavelength_rel=1e-6)
    assert est.sensitivity_rad_per_A > est.sigma_sensitivity_rad_per_A
    assert est.sigma_h_A > abs(est.h_A) * 0.5


def test_inputs_validated():
    kw = dict(branch_index=0, branch_source="test", wavelength_A=SC444.lam_A,
              theta_in_ext_rad=SC444.theta_ext, theta_out_ext_rad=SC444.theta_ext,
              **TEST_ONLY_SIGMAS)
    with pytest.raises(ValueError, match="wrapped"):
        height_from_phase(4.0, **kw)                      # not wrapped
    with pytest.raises(ValueError):
        height_from_phase(0.1, **{**kw, "branch_source": ""})
    with pytest.raises(TypeError):
        height_from_phase(0.1, wavelength_A=SC444.lam_A)  # branch and uncertainties required


def test_sensitivity_equals_2k_sin_theta_specular():
    s = sensitivity_rad_per_A(wavelength_A=SC444.lam_A, theta_in_ext_rad=SC444.theta_ext,
                              theta_out_ext_rad=SC444.theta_ext)
    check(s, 2 * SC444.K_ext, 1e-12)
    check(-s * D111, specular_step_phase(D111, SC444.theta_ext, SC444.lam_A), 1e-12)
