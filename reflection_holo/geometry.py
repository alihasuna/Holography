"""Geometry core: wavelength, interaction constant, refraction, Si lattice and slab frame.

Formulas follow docs/physics_conventions.md and tools/reflection_step_phase_calculator.py
(source-map rows SM01, SM02, SM04). Angles are glancing angles in radians, lengths in A,
beam energy in keV, potentials in V.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# SI-2019 exact definitions and CODATA 2018 m_e c^2 (same values as the reference calculator).
PLANCK_J_S = 6.626_070_15e-34
C_M_S = 299_792_458.0
ELEM_CHARGE_C = 1.602_176_634e-19
M_E_C2_EV = 510_998.950_00
M_E_KG = M_E_C2_EV * ELEM_CHARGE_C / C_M_S**2
HC_EV_A = PLANCK_J_S * C_M_S / ELEM_CHARGE_C * 1e10

# h^2 / (2 pi m_e e) in V A^2: converts an electron scattering factor f_e (A) into a potential
# Fourier coefficient (V A^3). DERIVED_HERE from the constants above (Kirkland-type convention).
FE_TO_POTENTIAL_V_A2 = PLANCK_J_S**2 / (2 * np.pi * M_E_KG * ELEM_CHARGE_C) * 1e20


def wavelength_A(E_keV: float) -> float:
    """Relativistic vacuum wavelength (SM01)."""
    T = E_keV * 1e3
    return HC_EV_A / np.sqrt(T * (T + 2 * M_E_C2_EV))


def k_rad_per_A(E_keV: float) -> float:
    return 2 * np.pi / wavelength_A(E_keV)


def interaction_constant(E_keV: float) -> float:
    """sigma = 2 pi m e lambda / h^2 in rad/(V A), relativistic mass m = gamma m_e.

    Equivalent form (2 pi / (lambda V_acc)) (m c^2 + eV)/(2 m c^2 + eV); 7.29e-4 at 200 keV.
    """
    T = E_keV * 1e3
    lam = wavelength_A(E_keV)
    return 2 * np.pi / (lam * T) * (M_E_C2_EV + T) / (2 * M_E_C2_EV + T)


def refraction_delta(E_keV: float, V0_V: float) -> float:
    """Delta = (k_int^2 - k_ext^2)/k_ext^2, relativistic (SM04)."""
    T = E_keV * 1e3
    return V0_V * (1 + T / M_E_C2_EV) / (T * (1 + T / (2 * M_E_C2_EV)))


def theta_int_from_ext(theta_ext: float, E_keV: float, V0_V: float) -> float:
    D = refraction_delta(E_keV, V0_V)
    return float(np.arcsin(np.sqrt((np.sin(theta_ext) ** 2 + D) / (1 + D))))


def theta_ext_from_int(theta_int: float, E_keV: float, V0_V: float) -> float:
    D = refraction_delta(E_keV, V0_V)
    s2 = np.sin(theta_int) ** 2 * (1 + D) - D
    if s2 <= 0:
        raise ValueError("internal angle below the escape angle theta_c: beam cannot exit")
    return float(np.arcsin(np.sqrt(s2)))


# ---------------------------------------------------------------------------------------------
# Silicon, diamond cubic
# ---------------------------------------------------------------------------------------------

FCC = np.array([[0, 0, 0], [0, 0.5, 0.5], [0.5, 0, 0.5], [0.5, 0.5, 0]])
DIAMOND_BASIS = np.vstack([FCC, FCC + 0.25])  # fractional coordinates of the 8-atom cell


def diamond_structure_factor_over_f(hkl) -> complex:
    h = np.asarray(hkl, float)
    return complex(np.exp(2j * np.pi * DIAMOND_BASIS @ h).sum())


def diamond_allowed(hkl) -> bool:
    return abs(diamond_structure_factor_over_f(hkl)) > 1e-9


def is_fcc_lattice_vector(v_over_a, tol: float = 1e-9) -> bool:
    """True if v/a is a translation of the fcc (hence diamond) lattice: half-integers with even 2v sum."""
    t = 2 * np.asarray(v_over_a, float)
    if not np.allclose(t, np.round(t), atol=tol):
        return False
    return int(round(t.sum())) % 2 == 0


@dataclass(frozen=True)
class SlabFrame:
    """Rows are the slab axes in cubic coordinates: x = outward normal, y = in-plane, z = beam azimuth.

    Active rotation r_slab = R @ r_cubic (docs/physics_conventions.md).
    """

    name: str
    normal_hkl: tuple
    y_uvw: tuple
    beam_uvw: tuple

    @property
    def R(self) -> np.ndarray:
        rows = [np.asarray(v, float) / np.linalg.norm(v) for v in (self.normal_hkl, self.y_uvw, self.beam_uvw)]
        R = np.array(rows)
        assert np.allclose(R @ R.T, np.eye(3), atol=1e-12), "slab axes are not orthonormal"
        assert np.isclose(np.linalg.det(R), 1.0), "slab frame is not right-handed"
        return R

    def to_slab(self, v_cubic) -> np.ndarray:
        return self.R @ np.asarray(v_cubic, float)


# CFG-A benchmark frame (docs/physics_conventions.md): (1,-1,1) surface, beam along [110].
SI111_FRAME = SlabFrame("si111_cleaved_110azimuth", (1, -1, 1), (1, -1, -2), (1, 1, 0))

# CFG-B frame: (001) surface, beam azimuth [110] (PROJECT_INPUT item 8 still open: [110] or [100]).
SI001_FRAME = SlabFrame("si001_110azimuth", (0, 0, 1), (1, -1, 0), (1, 1, 0))


@dataclass(frozen=True)
class SpecularCondition:
    """Specular reflection of order n on the rod normal to the surface, at the INTERNAL Bragg condition."""

    E_keV: float
    V0_V: float
    a_A: float
    hkl: tuple  # e.g. (4,-4,4); must be parallel to the frame normal

    def __post_init__(self):
        if not diamond_allowed(self.hkl):
            raise ValueError(f"reflection {self.hkl} is kinematically forbidden in diamond (F = 0)")

    @property
    def d_A(self) -> float:
        return self.a_A / float(np.linalg.norm(self.hkl))

    @property
    def lam(self) -> float:
        return wavelength_A(self.E_keV)

    @property
    def theta_int(self) -> float:
        k_int = np.sqrt(1 + refraction_delta(self.E_keV, self.V0_V)) / self.lam
        return float(np.arcsin(1 / (2 * self.d_A * k_int)))

    @property
    def theta_ext(self) -> float:
        return theta_ext_from_int(self.theta_int, self.E_keV, self.V0_V)

    @property
    def G(self) -> float:
        """|G| in rad/A."""
        return 2 * np.pi / self.d_A

    @property
    def q_ext(self) -> float:
        """Vacuum momentum transfer 2 k sin(theta_ext), rad/A."""
        return 2 * k_rad_per_A(self.E_keV) * np.sin(self.theta_ext)

    @property
    def q_int(self) -> float:
        k_int = k_rad_per_A(self.E_keV) * np.sqrt(1 + refraction_delta(self.E_keV, self.V0_V))
        return 2 * k_int * np.sin(self.theta_int)


@dataclass(frozen=True)
class SpecularAtAngle:
    """Specular reflection of order hkl for an arbitrary external glancing angle (off-Bragg allowed)."""

    E_keV: float
    V0_V: float
    a_A: float
    hkl: tuple
    theta_ext: float

    @property
    def d_A(self) -> float:
        return self.a_A / float(np.linalg.norm(self.hkl))

    @property
    def lam(self) -> float:
        return wavelength_A(self.E_keV)

    @property
    def theta_int(self) -> float:
        return theta_int_from_ext(self.theta_ext, self.E_keV, self.V0_V)

    @property
    def G(self) -> float:
        return 2 * np.pi / self.d_A

    @property
    def q_ext(self) -> float:
        return 2 * k_rad_per_A(self.E_keV) * np.sin(self.theta_ext)

    @property
    def q_int(self) -> float:
        k_int = k_rad_per_A(self.E_keV) * np.sqrt(1 + refraction_delta(self.E_keV, self.V0_V))
        return 2 * k_int * np.sin(self.theta_int)
