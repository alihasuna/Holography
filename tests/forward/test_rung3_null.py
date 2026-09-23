"""Ladder rung 3 (docs/05 section 4.4): null tests on constant-potential terraces.

Two terraces of constant V0 (40 A wide in y, step edges PARALLEL to the beam, periodic in y) at
16.47 mrad; the step phase is measured from the specular beam selected in k-space (aperture radius
0.5 1/A about (+sin(theta)/lambda, 0)) on the central half of each terrace.

Tolerance 1.0e-2 rad, from the study in docs/agent_reports/M2_multislice_engine.md section 3:
largest |error| 3.6e-3 rad over h_2pi, +-a/4 and a/2 at dx = 0.05 and 0.025 A (complex64 and
complex128). The residual is diffraction from the step edges into the measured regions: it did not
decrease with dx (h_2pi: 2.3e-3 at 0.05 A, 3.6e-3 at 0.025 A) and fell from up to 1.8e-2 rad to
<= 3.6e-3 rad when the terraces were widened from 24 to 40 A. 1.0e-2 rad is 2.8x the largest value.
The reversed step (-h) is the same configuration translated by one terrace width in y, so
Delta_phi(-h) = -Delta_phi(+h) holds to round-off (asserted at 1e-9 rad in complex128).
"""
import numpy as np
import pytest

from ladder_cases import THETA_0008, rung3_measure
from reflection_holo.constants import A_SI_A
from reflection_holo.geometry.wavelength import wavelength_A

TOL = 1.0e-2
KW = dict(dx=0.05, dy=0.6, dz=1.0, precision="complex128")


def _show(tag, r):
    print(f"{tag}: h={r['h_A']:+.4f} A  Delta_phi={r['delta_phi_rad']:+.5f} rad  expected "
          f"(wrapped) {r['expected_wrapped_rad']:+.5f}  error {r['err_rad']:+.2e}  "
          f"amp ratio {r['amplitude_upper'] / r['amplitude_lower']:.4f}  {r['time_s']:.1f} s")


def test_step_of_h2pi_gives_zero_phase_step():
    lam = wavelength_A(200.0)
    h2pi = lam / (2 * np.sin(THETA_0008))
    r = rung3_measure(THETA_0008, h2pi, **KW)
    _show("h_2pi", r)
    assert r["expected_rad"] == pytest.approx(-2 * np.pi, abs=1e-12)
    assert abs(r["delta_phi_rad"]) <= TOL


@pytest.fixture(scope="module")
def a4_pair():
    return (rung3_measure(THETA_0008, A_SI_A / 4, **KW),
            rung3_measure(THETA_0008, -A_SI_A / 4, **KW))


def test_translation_step_phase_equals_geometric(a4_pair):
    for tag, r in zip(("+a/4", "-a/4"), a4_pair):
        _show(tag, r)
        assert abs(r["err_rad"]) <= TOL        # vs -(4 pi / lambda) h sin(theta_ext), wrapped


def test_reversing_the_step_reverses_the_sign(a4_pair):
    up, down = a4_pair
    assert abs(up["delta_phi_rad"]) > 1.0                    # a non-trivial phase
    assert up["delta_phi_rad"] == pytest.approx(-down["delta_phi_rad"], abs=1e-9)
