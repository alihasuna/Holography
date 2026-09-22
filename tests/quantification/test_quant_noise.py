"""sigma_phi = sqrt(2)/(mu sqrt(N)) (source map SM12). Values from the calculator output section
10 table and docs/03 section 4, tolerances matching the printed digits."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.quantification.noise import (height_sigma_from_phase_sigma_A,
                                                  phase_noise_sigma_rad)


def check(got, want, tol):
    assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"


# calculator output section 10 (C_calculator_output.txt lines 428-432), 4 decimals
TABLE = [(1.0, 1e2, 0.1414), (1.0, 1e4, 0.0141), (0.5, 1e2, 0.2828), (0.5, 1e4, 0.0283),
         (0.2, 1e3, 0.2236), (0.1, 1e6, 0.0141)]


@pytest.mark.parametrize("mu,N,want", TABLE)
def test_sigma_phi_table(mu, N, want):
    check(phase_noise_sigma_rad(contrast_mu=mu, counts_N=N), want, 5e-5)


def test_docs03_precision_example():
    """docs/03 section 4: mu = 0.5, 1e4 counts -> sigma_phi = 0.028 rad, i.e. 0.004 A at (4,-4,4)
    (h_2pi = 0.919 A)."""
    s = phase_noise_sigma_rad(contrast_mu=0.5, counts_N=1e4)
    check(s, 0.028, 5e-4)
    sc = specular_condition_for((4, -4, 4), (1, -1, 1), E_keV=E, V0_V=V0, a_A=A_SI_A)
    check(sc.h_2pi_A, 0.919, 5e-4)
    check(height_sigma_from_phase_sigma_A(s, sc.h_2pi_A), 0.004, 5e-4)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        phase_noise_sigma_rad(contrast_mu=0.0, counts_N=100)
    with pytest.raises(ValueError):
        phase_noise_sigma_rad(contrast_mu=0.5, counts_N=0)
    assert np.allclose(phase_noise_sigma_rad(contrast_mu=np.array([1.0, 0.5]), counts_N=100),
                       [0.1414213562, 0.2828427125])
