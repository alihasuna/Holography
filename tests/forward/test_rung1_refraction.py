"""Ladder rung 1 (docs/05 section 4.4): refraction-only analytic limit.

Flat half-space of constant V0 (sharp, cell-averaged step, no atoms). The specular reflection
coefficient (amplitude AND phase) is compared with the Fresnel coefficient of the 1D step barrier
r = (q1 - q2)/(q1 + q2), q2 = sqrt(q1^2 + dK^2), dK from SM04; the refracted angle with SM04.

Tolerances come from the convergence study in docs/agent_reports/M2_multislice_engine.md section 2
(dx 0.05/0.025/0.0125 A, dz 2/1/0.5 A, 10/16.47/30 mrad, exact and Fresnel propagators):
  |r|:      | err - model | <= 3.5e-3, model = -((q1+q2) dx)^2/12 (measured second-order law;
            largest residual 0.176 %)
  phase:    |arg(r/r_analytic)| <= 1.0e-3 rad (largest at dz = 1 A: 4.75e-4 rad)
  angle:    |theta_int - SM04| <= 5e-3 mrad (largest: 1.5e-3 mrad)
  order:    observed dx order >= 1.8 at 16.47 mrad (observed 1.99)
"""
import numpy as np
import pytest

from ladder_cases import THETA_0008, V0, rung1_measure
from reflection_holo.geometry.refraction import delta_K_per_A

DX, DZ = 0.025, 1.0
AMP_TOL, PHASE_TOL, ANGLE_TOL_MRAD = 3.5e-3, 1.0e-3, 5e-3


def _model(res, dx):
    dK = delta_K_per_A(200.0, V0)
    q1 = res["q1_centre"]
    return -((q1 + np.sqrt(q1**2 + dK**2)) * dx) ** 2 / 12


@pytest.mark.parametrize("theta", [10e-3, THETA_0008, 30e-3])
def test_rung1_reflection_amplitude_phase_and_refraction_exact(theta):
    res = rung1_measure(theta, dx=DX, dz=DZ, propagator="exact")
    print(f"theta={theta * 1e3:.2f} mrad |r|={abs(res['r']):.5f} analytic={abs(res['r_analytic']):.5f}"
          f" err={res['amp_rel_err']:+.4%} phase_err={res['phase_err_rad']:+.2e} rad "
          f"theta_int={res['theta_int_meas_mrad']:.4f} (SM04 {res['theta_int_sm04_mrad']:.4f}) mrad")
    assert abs(res["amp_rel_err"] - _model(res, DX)) <= AMP_TOL
    assert abs(res["phase_err_rad"]) <= PHASE_TOL
    assert abs(abs(res["phase_rad"]) - np.pi) <= PHASE_TOL        # r is real and negative
    assert abs(res["theta_int_err_mrad"]) <= ANGLE_TOL_MRAD


def test_rung1_fresnel_propagator_16p47_mrad():
    res = rung1_measure(THETA_0008, dx=DX, dz=DZ, propagator="fresnel")
    assert abs(res["amp_rel_err"] - _model(res, DX)) <= AMP_TOL
    assert abs(res["phase_err_rad"]) <= PHASE_TOL
    assert abs(res["theta_int_err_mrad"]) <= ANGLE_TOL_MRAD


def test_rung1_second_order_convergence_in_dx():
    e1 = rung1_measure(THETA_0008, dx=0.05, dz=DZ, propagator="exact")["amp_rel_err"]
    e2 = rung1_measure(THETA_0008, dx=0.025, dz=DZ, propagator="exact")["amp_rel_err"]
    order = np.log2(abs(e1) / abs(e2))
    print(f"amplitude error {e1:+.4%} (dx 0.05) -> {e2:+.4%} (dx 0.025): order {order:.2f}")
    assert order >= 1.8
