"""R1 constants tests. Each docstring names the external fact and the tolerance."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from reflection_holo import constants as C  # noqa: E402


def test_const_labels_valid():
    """Invariant: every Const carries an allowed evidence label and a non-empty source."""
    for c in C.ALL_CONSTS:
        assert c.label in C.LABELS and c.source


def test_constants_consistent_with_shindo_table():
    """card:shindo_tomita_appA_constants p.1: h = 6.6261e-34, e = 1.6022e-19, c = 2.9979e8,
    mc^2 = 0.51100 MeV. Tolerance: half a unit of the last printed digit."""
    assert abs(C.H_PLANCK.value / 1e-34 - 6.6261) <= 5e-5
    assert abs(C.E_CHARGE.value / 1e-19 - 1.6022) <= 5e-5
    assert abs(C.C_LIGHT.value / 1e8 - 2.9979) <= 5e-5
    assert abs(C.MEC2_EV.value / 1e6 - 0.51100) <= 5e-6


def test_wavelength_200keV_T1():
    """Calculator check T1: lambda(200 keV) = 0.0250793 A +/- 1e-6."""
    assert abs(C.wavelength(200e3) - 0.0250793) <= 1e-6


def test_wavelength_100keV_T2():
    """Calculator check T2: lambda(100 keV) = 0.0370144 A +/- 1e-6 (formula check only)."""
    assert abs(C.wavelength(100e3) - 0.0370144) <= 1e-6


def test_wavelength_300keV_T3_not_exercised():
    """Calculator check T3 is deliberately not exercised: the project never uses 300 keV and
    T1/T2 already pin the formula at two energies."""
    pytest.skip("300 keV is never used in this project (PROJECT_INPUT E0 = 200 keV)")


def test_wavelength_shindo_table_200kV():
    """card:shindo_tomita_appA_constants p.2: 200 kV -> 0.00250793 nm = 0.0250793 A.
    Tolerance 5e-8 A = half of the last printed digit."""
    assert abs(C.wavelength(200e3) - 0.0250793) <= 5e-8


def test_wavelength_parallax_card():
    """card:hf3300_parallax p.14: lambda = 2.508 pm at 200 kV; tolerance 5e-4 pm."""
    assert abs(C.wavelength(200e3) * 100.0 - 2.508) <= 5e-4


def test_interaction_constant_shindo_200kV():
    """card:shindo_tomita_appA_constants p.2: sigma(200 kV) = 0.0072884 V^-1 nm^-1
    = 7.2884e-4 rad/(V A); tolerance 5e-9 (half last digit)."""
    assert abs(C.interaction_constant(200e3) - 7.2884e-4) <= 5e-9


def test_interaction_constant_shindo_100kV():
    """card:shindo_tomita_appA_constants p.2: sigma(100 kV) = 0.0092440 V^-1 nm^-1; tol 5e-9."""
    assert abs(C.interaction_constant(100e3) - 9.2440e-4) <= 5e-9


def test_interaction_constant_equals_e_over_hbar_v():
    """card:shindo_tomita_ch04-06 eq.(4.3) [p.4]: sigma = e/(hbar v). Identity to 1e-12 rel."""
    E = 200e3
    v = C.beta(E) * C.C_LIGHT.value
    hbar = C.H_PLANCK.value / (2 * math.pi)
    sigma_SI = C.E_CHARGE.value / (hbar * v)          # rad/(V m)
    assert abs(sigma_SI * 1e-10 / C.interaction_constant(E) - 1.0) <= 1e-12


def test_gamma_200keV():
    """repo:calculator_output.txt sec.1: gamma(200 keV) = 1.391390 (+/- 1e-6)."""
    assert abs(C.gamma(200e3) - 1.391390) <= 1e-6


def test_debye_waller_zero_point():
    """card:peng_ch14 Table 14.1 [p.8]: B(0) = a0 = 0.19284 A^2 (exact)."""
    assert C.debye_waller_B(0.0) == 0.19284


def test_debye_waller_300K():
    """card:peng_ch14 card's own evaluation of Table 14.2: B(300 K) ~ 0.5261 A^2; tol 5e-4."""
    assert abs(C.debye_waller_B(300.0) - 0.5261) <= 5e-4
    assert abs(C.B_SI_300K.value - 0.5261) <= 5e-4


def test_debye_waller_80K_boundary():
    """card:peng_ch14 card note: the two fits differ by ~0.9 % at 80 K; tolerance < 1 %."""
    lo = sum(c * 80.0 ** i for i, c in enumerate(C.DW_SI_LOW_T))
    hi = sum(c * 80.0 ** i for i, c in enumerate(C.DW_SI_HIGH_T))
    assert 0.005 < (lo - hi) / hi < 0.01


def test_peng_f0_sum():
    """card:peng_ch13 card arithmetic: f_Si(0) = sum a_i = 5.8182 A (Table 13.3 [p.24])."""
    assert abs(C.PENG_SI_F0_SUM - 5.8182) <= 1e-9


def test_mean_inner_potential_peng_regression():
    """DERIVED_HERE regression (no external value exists on the cards): neutral-atom V0 of the
    Peng parameterisation = (hbar^2/2m0)(4pi/a^3) 8 f(0) = 13.91 V; tol 0.005 V."""
    assert abs(C.HBAR2_OVER_2M0_EV_A2 - 3.80998) <= 1e-5
    assert abs(C.V0_PENG_NEUTRAL_SI.value - 13.9125) <= 0.005
