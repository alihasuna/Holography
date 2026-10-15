"""
structure_factors.py
====================
Electron scattering factors, diamond cubic selection rules,
and crystal potential Fourier components for Si.

Parameterization: Peng, Ren, Dudarev, Whelan, Acta Cryst. A52, 257 (1996).
"""

import numpy as np
from simulation.constants import (
    SI_LATTICE_PARAM, SI_UNIT_CELL_VOLUME, SI_ATOM_POSITIONS,
    SI_SCATTERING_A, SI_SCATTERING_B, SI_DEBYE_WALLER_B,
    RELATIVISTIC_GAMMA, M_E, E_CHARGE, HBAR,
    VOLTAGE_V, K_200KV,
)


def is_allowed_diamond_cubic(h, k, l):
    """Check if reflection (hkl) is allowed for diamond cubic (Fd-3m).

    Returns (is_allowed, relative_structure_factor_squared).

    Selection rules:
        1. h,k,l must be all odd or all even (FCC condition)
        2. If all odd: allowed, |F|^2 proportional to 32*f^2
        3. If all even and (h+k+l) % 4 == 0: allowed, |F|^2 ~ 64*f^2
        4. If all even and (h+k+l) % 4 == 2: forbidden (diamond basis)
    """
    parities = (h % 2, k % 2, l % 2)
    if len(set(parities)) > 1:  # mixed parity -> forbidden by FCC
        return False, 0.0
    if all(p % 2 == 1 for p in parities):  # all odd
        return True, 32.0
    # all even
    if (h + k + l) % 4 == 0:
        return True, 64.0
    return False, 0.0  # (h+k+l) % 4 == 2


def electron_scattering_factor(s):
    """Electron scattering factor for Si at scattering parameter s.

    Parameters
    ----------
    s : float or array
        s = |G| / (4*pi) = sin(theta) / lambda  [A^-1]

    Returns
    -------
    f_e : float or array
        Electron scattering factor in Angstroms.
    """
    s2 = np.asarray(s, dtype=float)**2
    f = np.sum(SI_SCATTERING_A * np.exp(-SI_SCATTERING_B * s2[..., None]), axis=-1)
    return f


def debye_waller_factor(s, b_factor=SI_DEBYE_WALLER_B):
    """Debye-Waller temperature factor exp(-B * s^2).

    Parameters
    ----------
    s : float or array
        s = |G| / (4*pi) [A^-1]
    b_factor : float
        B-factor in A^2.
    """
    return np.exp(-b_factor * np.asarray(s)**2)


def structure_factor(h, k, l, a=SI_LATTICE_PARAM, include_dw=True):
    """Compute the electron structure factor F_G for Si diamond cubic.

    F_G = sum_j f_e(s) * T_j(s) * exp(-2*pi*i*(h*x_j + k*y_j + l*z_j))

    All 8 atoms in the conventional cell are Si, so f_e factors out.

    Parameters
    ----------
    h, k, l : int
        Miller indices.
    a : float
        Lattice parameter in Angstroms.
    include_dw : bool
        Whether to include Debye-Waller factor.

    Returns
    -------
    F : complex
        Structure factor (units of Angstroms, since f_e is in Angstroms).
    """
    g_mag = 2 * np.pi / a * np.sqrt(h**2 + k**2 + l**2)
    s = g_mag / (4 * np.pi)

    f_e = electron_scattering_factor(s)
    dw = debye_waller_factor(s) if include_dw else 1.0

    # geometric structure factor: sum over 8 atom positions
    hkl = np.array([h, k, l], dtype=float)
    phase_sum = np.sum(np.exp(-2j * np.pi * SI_ATOM_POSITIONS @ hkl))

    return f_e * dw * phase_sum


def fourier_potential(h, k, l, a=SI_LATTICE_PARAM, voltage_kv=200.0):
    """Compute the Fourier component of the crystal potential U_G.

    U_G = (2*m*e / hbar^2) * V_G
    V_G = (hbar^2 / (2*pi*m*e)) * (1/V_c) * F_G   [using natural units]

    In practical units for the eigenvalue equation (A^-2):
        U_G = (4*pi / V_c) * F_G

    With relativistic mass correction: m -> m* = m_0 * gamma_rel
    This is already embedded in the scattering factors (Peng parameterization
    is for the relativistic case at given voltage).

    For the Bloch wave eigenvalue equation (Peng et al. Eq. 5.45),
    U_G appears as:
        U_G / (2*K)   [dimensionless, in units of A^-1]

    Parameters
    ----------
    h, k, l : int
        Miller indices.
    a : float
        Lattice parameter.
    voltage_kv : float
        Accelerating voltage.

    Returns
    -------
    U_G : complex
        Fourier potential in A^-2.
    """
    vc = a**3
    F = structure_factor(h, k, l, a=a)
    # U_G = (4*pi / V_c) * F_G
    # This follows from: V_G = (h^2/(2*pi*m*e*V_c)) * F_G (CGS)
    # and U_G = (2*m*e/hbar^2) * V_G = (4*pi/V_c) * F_G
    return (4 * np.pi / vc) * F


def generate_allowed_reflections(max_index=12, a=SI_LATTICE_PARAM):
    """Generate all allowed Si reflections up to max Miller index.

    Returns
    -------
    reflections : list of dict
        Each dict has: hkl, g_vec (A^-1), g_mag (A^-1), d_spacing (A),
        F (complex), F_sq (float), allowed (bool).
    """
    recip = 2 * np.pi / a  # reciprocal lattice unit in A^-1
    reflections = []

    for h in range(-max_index, max_index + 1):
        for k in range(-max_index, max_index + 1):
            for l in range(-max_index, max_index + 1):
                if h == 0 and k == 0 and l == 0:
                    continue
                allowed, f_sq_rel = is_allowed_diamond_cubic(h, k, l)
                if not allowed:
                    continue

                g_vec = recip * np.array([h, k, l], dtype=float)
                g_mag = np.linalg.norm(g_vec)
                d_spacing = 2 * np.pi / g_mag if g_mag > 0 else np.inf

                F = structure_factor(h, k, l, a=a)

                reflections.append({
                    "hkl": (h, k, l),
                    "g_vec": g_vec,
                    "g_mag": g_mag,
                    "d_spacing": d_spacing,
                    "F": F,
                    "F_sq": abs(F)**2,
                })

    # sort by |G|
    reflections.sort(key=lambda r: r["g_mag"])
    return reflections


def validate_selection_rules():
    """Quick validation of diamond cubic selection rules for Si."""
    tests = [
        # (hkl, expected_allowed, description)
        ((1, 1, 1), True, "all odd -> allowed"),
        ((2, 2, 0), True, "all even, h+k+l=4 -> allowed"),
        ((4, 0, 0), True, "all even, h+k+l=4 -> allowed"),
        ((2, 2, 2), False, "all even, h+k+l=6, 6%4=2 -> forbidden"),
        ((4, 4, 2), False, "all even, h+k+l=10, 10%4=2 -> forbidden"),
        ((3, 1, 1), True, "all odd -> allowed"),
        ((2, 1, 0), False, "mixed parity -> forbidden"),
        ((6, 6, 6), False, "all even, h+k+l=18, 18%4=2 -> forbidden"),
        ((4, 4, 4), True, "all even, h+k+l=12, 12%4=0 -> allowed"),
        ((8, 8, 0), True, "all even, h+k+l=16, 16%4=0 -> allowed"),
    ]

    print("Diamond cubic selection rule validation:")
    all_pass = True
    for (h, k, l), expected, desc in tests:
        result, _ = is_allowed_diamond_cubic(h, k, l)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  ({h:2d},{k:2d},{l:2d}): {status}  [{desc}]")

    # check structure factors
    print("\nStructure factor magnitudes for key reflections:")
    for hkl in [(1,1,1), (2,2,0), (3,1,1), (2,2,2), (4,0,0), (3,3,1),
                (4,2,2), (3,3,3), (4,4,0), (6,6,6)]:
        F = structure_factor(*hkl)
        allowed, _ = is_allowed_diamond_cubic(*hkl)
        tag = "allowed" if allowed else "FORBIDDEN"
        print(f"  {hkl}: |F| = {abs(F):.4f} A  ({tag})")

    return all_pass


if __name__ == "__main__":
    validate_selection_rules()
