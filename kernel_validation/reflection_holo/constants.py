"""reflection_holo.constants -- physical constants and silicon parameters (rung R1).

Conventions (repo:physics_conventions.md): exp(+i k.r); angular wavevectors |k| = 2 pi / lambda
in rad/A; lengths in A; potentials in V; energies in eV inside every formula. The beam
energy of this project is 200 keV (PROJECT_INPUT, SUPPLIED; see project_inputs.REGISTER['E0']).
300 keV is never used by any configuration.

Every constant is a Const(value, unc, unit, label, source). Labels:
  SECTION_READ  traced to a card page or to a repository document that was attached
  REPRODUCED    a script/test reproduces a printed number
  ASSUMPTION    chosen value with a stated reason
  DERIVED_HERE  derived in this file from labelled premises
  UNVERIFIED    not checkable with the attached cards
An uncertainty of float('nan') means "not stated by any attached source".

Integration fix 2026-10-16 (INTEGRATION_NOTES.md):
  * KIRKLAND_SI now carries the Kirkland Eq. C.15 Si row (card:kirkland_appC p.12) in the
    {'a','b','c','d'} layout read by multislice.potential.kirkland_coefficients. The Peng
    Gaussian set stays separate as PENG_SI_ELASTIC.
  * ABSORPTION_MODEL is named 'peng_gaussian' (a form resolve_absorption_model knows) with
    parameters None, status MISSING, label UNVERIFIED; any use raises MissingProjectInput.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

LABELS = frozenset({"SECTION_READ", "REPRODUCED", "PROJECT_INPUT", "ASSUMPTION",
                    "DERIVED_HERE", "UNVERIFIED"})

NAN = float("nan")


@dataclass(frozen=True)
class Const:
    """A labelled constant. `label` must be one of LABELS (checked on construction)."""
    value: float
    unc: float
    unit: str
    label: str
    source: str

    def __post_init__(self) -> None:
        if self.label not in LABELS:
            raise ValueError(f"unknown evidence label {self.label!r}")


# ---------------------------------------------------------------------------
# Fundamental constants
# ---------------------------------------------------------------------------
_CONV = "repo:physics_conventions.md, 'Wavelength' row (h, c, e exact SI-2019; m_e c^2 CODATA 2018)"

H_PLANCK = Const(6.62607015e-34, 0.0, "J s", "SECTION_READ",
                 _CONV + "; digits as printed in repo:calculator_output.txt sec.1; "
                 "consistent with card:shindo_tomita_appA_constants p.1 (6.6261e-34 J s)")
C_LIGHT = Const(299792458.0, 0.0, "m/s", "SECTION_READ",
                _CONV + "; card:shindo_tomita_appA_constants p.1 (2.9979e8 m/s)")
E_CHARGE = Const(1.602176634e-19, 0.0, "C", "SECTION_READ",
                 _CONV + "; card:shindo_tomita_appA_constants p.1 (1.6022e-19 C)")
MEC2_EV = Const(510998.95, NAN, "eV", "SECTION_READ",
                _CONV + " (510998.950 eV); uncertainty not on any card (negligible here); "
                "card:shindo_tomita_appA_constants p.1 prints 0.51100 MeV")

# DERIVED_HERE from the three exact SI values above.
HC_EV_A: float = H_PLANCK.value * C_LIGHT.value / E_CHARGE.value * 1.0e10   # eV A
HBARC_EV_A: float = HC_EV_A / (2.0 * math.pi)                                # eV A
# hbar^2 / (2 m0) in eV A^2 = (hbar c)^2 / (2 m0 c^2). DERIVED_HERE.
HBAR2_OVER_2M0_EV_A2: float = HBARC_EV_A ** 2 / (2.0 * MEC2_EV.value)


def _check_E(E_eV: float) -> float:
    E = float(E_eV)
    if not E > 0.0:
        raise ValueError(f"kinetic energy must be positive, got {E_eV!r} eV")
    return E


def gamma(E_eV: float) -> float:
    """Lorentz factor gamma = 1 + T/(m_e c^2), T = kinetic energy in eV. DERIVED_HERE."""
    return 1.0 + _check_E(E_eV) / MEC2_EV.value


def beta(E_eV: float) -> float:
    """v/c = sqrt(1 - 1/gamma^2). DERIVED_HERE."""
    g = gamma(E_eV)
    return math.sqrt(1.0 - 1.0 / g ** 2)


def wavelength(E_eV: float) -> float:
    """Relativistic vacuum wavelength in A: lambda = h c / sqrt(T (T + 2 m_e c^2)).

    SECTION_READ: repo:physics_conventions.md 'Wavelength' row (this exact form) and
    card:hf3300_parallax p.14 (lambda = h/sqrt(2 m0 e V (1 + eV/2m0c^2)), algebraically identical).
    REPRODUCED: 200 kV -> 0.00250793 nm [card:shindo_tomita_appA_constants p.2];
    2.508 pm [card:hf3300_parallax p.14]; 0.0250793 A [calculator T1] (tests/test_constants.py).
    """
    T = _check_E(E_eV)
    return HC_EV_A / math.sqrt(T * (T + 2.0 * MEC2_EV.value))


def wavenumber(E_eV: float) -> float:
    """Angular vacuum wavenumber |k| = 2 pi / lambda in rad/A (convention). DERIVED_HERE."""
    return 2.0 * math.pi / wavelength(E_eV)


def interaction_constant(E_eV: float) -> float:
    """Relativistic interaction constant sigma in rad/(V A).

    sigma = (2 pi / (lambda V)) * (m c^2 + eV) / (2 m c^2 + eV), V = T/e numerically.
    SECTION_READ: card:shindo_tomita_ch04-06 eq.(4.3) [p.4 / pr.18]:
    sigma = e/(hbar v) = 2 pi / (lambda V (1 + sqrt(1 - (v/c)^2))). The two forms are identical
    because 1 + sqrt(1-beta^2) = (gamma+1)/gamma (DERIVED_HERE; tested numerically).
    REPRODUCED: 0.0072884 V^-1 nm^-1 at 200 kV [card:shindo_tomita_appA_constants p.2].
    """
    T = _check_E(E_eV)
    E0 = MEC2_EV.value
    return 2.0 * math.pi / (wavelength(T) * T) * (E0 + T) / (2.0 * E0 + T)


# ---------------------------------------------------------------------------
# Silicon
# ---------------------------------------------------------------------------
A_SI = Const(5.4309, 1.0e-4, "A", "ASSUMPTION",
             "No attached card prints the Si lattice parameter (card:peng_ch13 'Not in this "
             "document': Si lattice constant). 5.4309 A is the repository generator default used "
             "by repo:calculator_output.txt sec.2b ('a(Si) = 5.4309 A'), adopted so every "
             "calculator check is reproducible; unc = spread to the 5.431 A of the repository meta "
             "file (calculator sec.6). Textbook value from memory UNVERIFIED, not load-bearing.")

V0_SI = Const(12.0, 1.0, "V", "ASSUMPTION",
              "repo:physics_conventions.md refraction bullet ('V0 = 12 V (ASSUMPTION)'); "
              "repo:06_project_inputs_required.md item 20 (to be sourced); no card gives a Si "
              "value (card:peng_ch13 request 3: 'Si value: NOT IN THIS DOCUMENT'). "
              "Code never reads this directly: it goes through project_inputs.get('V0_SI').")

# Elastic 5-Gaussian electron scattering factor, f(s) = sum a_i exp(-b_i s^2), s = sin(theta)/lambda.
PENG_SI_ELASTIC: dict = {
    "Z": 14,
    "a": (0.0567, 0.3365, 0.8104, 2.4960, 2.1186),       # A
    "b": (0.0582, 0.6155, 3.2522, 16.7929, 57.6767),     # A^2
    "form": "f(s) = sum_i a_i exp(-b_i s^2), s = sin(theta)/lambda in 1/A",
    "label": "SECTION_READ",
    "source": "card:peng_ch13_scattering_factor_optical_potential Table 13.3 [p.24 / printed 450]; "
              "form eq.(13.79) [p.18]; s definition [p.1]",
}

# Kirkland Eq. C.15: f_e(q) = sum_{i=1..3} a_i/(q^2 + b_i) + sum_{i=1..3} c_i exp(-d_i q^2),
# q in 1/A (Fourier variable of exp(2 pi i q.r), Eq. C.5). Row printed order
# a1 b1 a2 b2 / a3 b3 c1 d1 / c2 d2 c3 d3 [card:kirkland_appC p.9]; values [p.12, printed p.294].
KIRKLAND_SI: dict = {
    "Z": 14,
    "a": (1.06543892e+000, 1.20143691e-001, 1.80915263e-001),   # 1/A
    "b": (1.04118455e+000, 6.87113368e+001, 8.87533926e-002),   # 1/A^2
    "c": (1.12065620e+000, 3.05452816e-002, 1.59963502e+000),   # A
    "d": (3.70062619e+000, 2.14097897e-001, 9.99096638e+000),   # A^2
    "chisq": 0.071667,
    "units": "a 1/A, b 1/A^2, c A, d A^2 [card:kirkland_appC p.9]",
    "form": "f_e(q) = sum a/(q^2+b) + sum c exp(-d q^2), q in 1/A, fit range 0 < q < 12/A [p.7-8]",
    "label": "SECTION_READ",
    "source": "card:kirkland_appC_scattering_factors Si row [p.12, printed p.294]; layout [p.9]; "
              "Eq. C.15 [p.8]",
}

ABSORPTION_MODEL: dict = {
    "name": "peng_gaussian",
    "description": "TDS absorptive potential, Einstein model (Hall-Hirsch), local form",
    "equations": "card:peng_ch13 eqs.(13.64)-(13.65) [p.13], analytic use eqs.(13.84),(13.87),(13.90) "
                 "[p.21-23]: imaginary terms i a_j^(Im) exp[-(b_j^(Im) + B/2) s^2]",
    "parameters": None,
    "status": "MISSING",
    "label": "UNVERIFIED",
    "source": "card:peng_ch13 [p.20]: no absorptive parameter table in the chunk; Appendix D absent. "
              "Si a^(Im), b^(Im) must be supplied (repo:06_project_inputs_required.md item 21).",
}

# Debye-Waller B(T) = a0 + a1 T + a2 T^2 + a3 T^3 + a4 T^4 (T in K, B in A^2), eq.(14.4).
DW_SI_LOW_T = (0.19284, 0.1670e-04, -0.7475e-06, 0.1410e-06, -0.8174e-09)   # T < 80 K, Table 14.1
DW_SI_HIGH_T = (0.14236, 0.9261e-03, 0.1623e-05, -0.1677e-08, 0.6351e-12)   # T > 80 K, Table 14.2
DW_SOURCE = ("card:peng_ch14_debye_waller eq.(14.4) [p.2/455]; Table 14.1 [p.8/461] (0-80 K), "
             "Table 14.2 [p.9/462] (T > 80 K); amplitude factor exp(-B s^2) [p.1/454]")


def debye_waller_B(T_K: float) -> float:
    """Bulk Si Debye-Waller B(T) in A^2 from the card polynomials (SECTION_READ coefficients).

    T < 80 K uses Table 14.1, T >= 80 K Table 14.2 (the card fits 'T < 80 K' and 'T > 80 K';
    the two differ by 0.93 % at 80 K, printed by scripts/run_R1.py). Bulk value only: its use for
    surface layers is an ASSUMPTION the card does not support [peng ch14 card, contradiction 5].
    Upper validity limit of the high-T fit is not stated (UNVERIFIED).
    """
    T = float(T_K)
    if T < 0.0:
        raise ValueError("temperature must be >= 0 K")
    c = DW_SI_LOW_T if T < 80.0 else DW_SI_HIGH_T
    return float(sum(ci * T ** i for i, ci in enumerate(c)))


B_SI_300K = Const(debye_waller_B(300.0), 0.005 * debye_waller_B(300.0), "A^2", "DERIVED_HERE",
                  DW_SOURCE + "; evaluated at 300 K (temperature is an ASSUMPTION, "
                  "project_inputs 'specimen_temperature_K'); unc = card's 0.5 % fit error only, "
                  "accuracy vs experiment UNVERIFIED")

PENG_SI_F0_SUM: float = float(sum(PENG_SI_ELASTIC["a"]))   # f(0) per atom, A; DERIVED_HERE


def mean_inner_potential_neutral_atoms(f0_sum_per_cell_A: float, cell_volume_A3: float) -> float:
    """Mean inner potential (V) of an isolated-neutral-atom superposition.

    DERIVED_HERE from card:peng_ch13 eq.(13.31)/(13.86) at g = 0 with T(0) = 1 [p.6, p.22]:
    the potential ENERGY coefficient is V_{g=0} = -(hbar^2/2m0)(4 pi/Omega) sum_n f_n(0) < 0;
    with the repository convention 'electron potential energy = -e V0', V0 in volts is
    +(hbar^2/2m0)(4 pi/Omega) sum f(0) with hbar^2/2m0 in eV A^2. Caveat [peng ch13 p.2]:
    bonding redistributes charge mostly in low orders, so g = 0 is the least reliable order.
    """
    return HBAR2_OVER_2M0_EV_A2 * 4.0 * math.pi * float(f0_sum_per_cell_A) / float(cell_volume_A3)


V0_PENG_NEUTRAL_SI = Const(
    mean_inner_potential_neutral_atoms(8.0 * PENG_SI_F0_SUM, A_SI.value ** 3), NAN, "V",
    "DERIVED_HERE",
    "neutral-atom V0 of the Peng Table 13.3 parameterisation, 8 atoms per a^3 cell (a = A_SI, "
    "ASSUMPTION); NOT a measured Si value; bonding correction UNVERIFIED")

ALL_CONSTS = (H_PLANCK, C_LIGHT, E_CHARGE, MEC2_EV, A_SI, V0_SI, B_SI_300K, V0_PENG_NEUTRAL_SI)
