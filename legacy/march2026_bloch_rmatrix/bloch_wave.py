"""
bloch_wave.py
=============
Bloch wave eigenvalue problem for bulk reflection electron diffraction.

Implements the 2N x 2N eigenvalue formulation from Peng, Dudarev & Whelan
(2004) Chapter 5, Section 5.3.4 for a semi-infinite crystal.

The eigenvalue equation (Eq. 5.45):
    [gamma^2 + 2*(K+g)_z * gamma - 2*K*S_g] * C_g - sum_{h!=g} U_{g-h} * C_h = 0

Reformulated as a linear 2N x 2N problem in gamma.
"""

import numpy as np
from simulation.constants import (
    SI_LATTICE_PARAM, K_200KV, SURFACE_NORMAL,
)
from simulation.structure_factors import (
    structure_factor, is_allowed_diamond_cubic,
)


def select_strong_beams(k_i, hkl_list, g_vectors, n_strong=30,
                        surface_normal=SURFACE_NORMAL):
    """Select the N strongest beams by excitation error.

    Sorts reflections by |s_g| and returns the n_strong closest to
    the Ewald sphere.

    Returns indices into the original arrays.
    """
    k_mag = np.linalg.norm(k_i)
    k_f = k_i[None, :] + g_vectors
    k_f_mag_sq = np.sum(k_f**2, axis=1)
    s_g = (k_mag**2 - k_f_mag_sq) / (2.0 * k_mag)

    # sort by |s_g|
    order = np.argsort(np.abs(s_g))
    selected = order[:n_strong]
    return selected, s_g


def compute_kz_components(k_i, g_vectors, surface_normal=SURFACE_NORMAL):
    """Compute the z-component (along surface normal into crystal) of (K+g).

    The z-direction is along the INWARD surface normal (into the crystal).
    """
    # inward normal (into crystal) = -outward normal
    n_in = -surface_normal
    k_plus_g = k_i[None, :] + g_vectors  # (N, 3)
    kz = k_plus_g @ n_in
    return kz


def build_potential_matrix(hkl_list, a=SI_LATTICE_PARAM,
                           absorption_ratio=0.07):
    """Build the U_{g-h} matrix of Fourier potential components.

    Parameters
    ----------
    hkl_list : list of (h,k,l) tuples
        Miller indices of beams in the calculation.
    a : float
        Lattice parameter.
    absorption_ratio : float
        Ratio of imaginary to real potential (Hashimoto-Howie-Whelan).
        U_G -> U_G * (1 + i*mu)

    Returns
    -------
    U_matrix : (N, N) complex array
        U_matrix[g, h] = U_{g-h}   [units: A^-2]
        NOT divided by 2K -- kept in same units as the diagonal (2*K*s_g).
    """
    n = len(hkl_list)
    vc = a**3
    U = np.zeros((n, n), dtype=complex)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            dh = hkl_list[i][0] - hkl_list[j][0]
            dk = hkl_list[i][1] - hkl_list[j][1]
            dl = hkl_list[i][2] - hkl_list[j][2]

            F = structure_factor(dh, dk, dl, a=a)
            # U_G = (4*pi / V_c) * F_G  [A^-2]
            U_g = (4 * np.pi / vc) * F
            # add absorption
            U_g = U_g * (1.0 + 1j * absorption_ratio)
            U[i, j] = U_g

    return U


def build_eigenvalue_matrix(k_i, hkl_list, g_vectors,
                            a=SI_LATTICE_PARAM,
                            absorption_ratio=0.07,
                            surface_normal=SURFACE_NORMAL):
    """Build the 2N x 2N eigenvalue matrix for the Bloch wave problem.

    The eigenvalue equation is reformulated as:
        | 0      I   | | C   |        | C   |
        | D    -diag | | psi | = gamma | psi |

    where:
        D[g,g] = 2*K*S_g / (2*(K+g)_z)  ... wait, let me be more careful.

    Following Peng et al. Section 5.3.4, the linearized form is:

    Define psi_g = gamma * C_g. Then the second-order equation becomes:

        gamma * C_g = psi_g
        gamma * psi_g = -2*(K+g)_z * psi_g + 2*K*S_g * C_g + sum_h U_{g-h} * C_h

    In matrix form:
        | 0      I     | | C |       | C   |
        | A    -2*K_z  | |psi| = gam |psi  |

    where A[g,h] = U_{g-h}/(nothing) for g!=h, A[g,g] = 2*K*S_g

    WAIT - let me be more precise. The original equation (Peng Eq. 5.45):

        gamma^2 * C_g + 2*(K+g)_z * gamma * C_g - 2*K*S_g * C_g
            - sum_{h!=g} U_{g-h} * C_h = 0

    Let psi_g = gamma * C_g:

        gamma * psi_g + 2*(K+g)_z * psi_g = 2*K*S_g * C_g + sum_{h!=g} U_{g-h} * C_h
        gamma * psi_g = -2*(K+g)_z * psi_g + sum_h M_{g,h} * C_h

    where M[g,g] = 2*K*S_g and M[g,h] = U_{g-h} for g!=h.

    The 2N x 2N system is:
        | 0  I | |C|       |C|
        | M -D | |p| = gam |p|

    where D = diag(2*(K+g)_z).

    Returns (2N, 2N) complex matrix.
    """
    n = len(hkl_list)
    K = K_200KV
    k_mag = np.linalg.norm(k_i)

    # excitation errors
    k_f = k_i[None, :] + g_vectors
    k_f_mag_sq = np.sum(k_f**2, axis=1)
    s_g = (k_mag**2 - k_f_mag_sq) / (2.0 * k_mag)

    # z-components (along inward surface normal)
    n_in = -surface_normal
    kz = (k_i[None, :] + g_vectors) @ n_in  # (N,)

    # potential matrix
    U = build_potential_matrix(hkl_list, a=a, absorption_ratio=absorption_ratio)

    # M matrix: diagonal = 2*K*S_g, off-diagonal = U_{g-h}
    M = U.copy()
    for g in range(n):
        M[g, g] = 2.0 * k_mag * s_g[g]

    # D = diag(2*(K+g)_z)
    D = np.diag(2.0 * kz)

    # build 2N x 2N matrix
    mat = np.zeros((2 * n, 2 * n), dtype=complex)
    mat[:n, n:] = np.eye(n)       # top-right: I
    mat[n:, :n] = M               # bottom-left: M
    mat[n:, n:] = -D              # bottom-right: -D

    return mat, s_g, kz


def solve_bloch(k_i, hkl_list, g_vectors,
                a=SI_LATTICE_PARAM,
                absorption_ratio=0.07,
                surface_normal=SURFACE_NORMAL):
    """Solve the Bloch wave eigenvalue problem.

    Returns
    -------
    eigenvalues : (2N,) complex
        gamma values (perpendicular wavevector corrections).
    eigenvectors : (2N, 2N) complex
        Columns are [C_g; psi_g] for each Bloch wave.
    s_g : (N,) float
        Excitation errors.
    kz : (N,) float
        (K+g)_z components.
    """
    mat, s_g, kz = build_eigenvalue_matrix(
        k_i, hkl_list, g_vectors, a=a,
        absorption_ratio=absorption_ratio,
        surface_normal=surface_normal,
    )

    eigenvalues, eigenvectors = np.linalg.eig(mat)

    return eigenvalues, eigenvectors, s_g, kz


def select_evanescent(eigenvalues, eigenvectors, n_beams):
    """Select the N evanescent Bloch waves (decay into crystal).

    For z pointing INTO the crystal (inward normal), evanescent waves
    have Im(gamma) > 0 (they grow as e^{i*gamma*z} with z going into
    the crystal, but gamma has positive imaginary part meaning the
    wave decays in the +z direction inside the crystal).

    Returns
    -------
    gamma_evan : (N,) complex
    C_evan : (N, N) complex
        Bloch wave coefficients. C_evan[g, j] = coefficient of beam g
        in Bloch wave j.
    """
    # the eigenvectors have structure [C; psi] where psi = gamma*C
    # extract the C part (first N rows)
    C_all = eigenvectors[:n_beams, :]  # (N, 2N)

    # select evanescent: Im(gamma) > 0 for inward-decaying waves
    evan_mask = np.imag(eigenvalues) > 0

    gamma_evan = eigenvalues[evan_mask]
    C_evan = C_all[:, evan_mask]

    # we should get exactly N evanescent waves
    if len(gamma_evan) < n_beams:
        # fallback: take the N with largest Im(gamma)
        order = np.argsort(-np.imag(eigenvalues))
        gamma_evan = eigenvalues[order[:n_beams]]
        C_evan = C_all[:, order[:n_beams]]

    if len(gamma_evan) > n_beams:
        # take the N with smallest |Im(gamma)| (closest to surface)
        order = np.argsort(np.imag(gamma_evan))
        gamma_evan = gamma_evan[order[:n_beams]]
        C_evan = C_evan[:, order[:n_beams]]

    return gamma_evan, C_evan


if __name__ == "__main__":
    from simulation.calibration import (
        btx_bty_to_tilt_mrad, compute_incident_wavevector,
        compute_grazing_angle,
    )
    from simulation.kinematical import generate_reciprocal_lattice

    tx, ty = btx_bty_to_tilt_mrad(-814.0, 135.0)
    k_i = compute_incident_wavevector(tx, ty)
    grazing = compute_grazing_angle(tx, ty)
    print(f"Grazing angle: {grazing:.1f} mrad ({grazing/1e3*180/np.pi:.2f} deg)")

    hkl_list, g_vectors, f_sq = generate_reciprocal_lattice(max_index=6)

    # select strong beams
    indices, s_g_all = select_strong_beams(k_i, hkl_list, g_vectors, n_strong=20)
    sel_hkl = [hkl_list[i] for i in indices]
    sel_g = g_vectors[indices]
    print(f"\nSelected {len(sel_hkl)} strong beams:")
    for i, idx in enumerate(indices):
        print(f"  {sel_hkl[i]}  s_g={s_g_all[idx]:.4f} A^-1")

    # solve eigenvalue problem
    eigenvalues, eigenvectors, s_g, kz = solve_bloch(
        k_i, sel_hkl, sel_g, absorption_ratio=0.07)

    n = len(sel_hkl)
    gamma_evan, C_evan = select_evanescent(eigenvalues, eigenvectors, n)

    print(f"\nEigenvalue problem: {2*n}x{2*n} matrix")
    print(f"Evanescent Bloch waves: {len(gamma_evan)}")
    print(f"  gamma (first 5): {gamma_evan[:5]}")
    print(f"  Im(gamma) range: {np.min(np.imag(gamma_evan)):.4f} to "
          f"{np.max(np.imag(gamma_evan)):.4f} A^-1")
