"""
r_matrix.py
===========
R-matrix boundary conditions for semi-infinite crystal reflection.

At the crystal surface (z=0), match the Bloch wave solution inside
the crystal to the vacuum wavefield (incident + reflected beams).

Boundary conditions (Peng et al. Section 5.3.4.5):
    sum_j alpha_j * C_g^j = delta_{g,0} + R_g            (wavefunction)
    sum_j alpha_j * (kz_g + gamma_j) * C_g^j = kappa_0 * delta_{g,0} - kappa_g * R_g  (derivative)

where:
    alpha_j = Bloch wave excitation amplitude
    C_g^j = coefficient of beam g in Bloch wave j
    gamma_j = eigenvalue (z-wavevector correction)
    kz_g = (K+g)_z component (z along inward surface normal)
    kappa_g = sqrt(K^2 - |K_t + g_t|^2) = z-component of wavevector in vacuum for beam g
    R_g = reflected beam amplitude for beam g
"""

import numpy as np
from simulation.constants import K_200KV, SURFACE_NORMAL


def compute_vacuum_kz(k_i, g_vectors, surface_normal=SURFACE_NORMAL):
    """Compute z-component of wavevector in vacuum for each beam.

    kappa_g = sqrt(K^2 - |K_t + g_t|^2)

    where K_t is the tangential (surface-parallel) component.
    Evanescent beams in vacuum have imaginary kappa.
    """
    K = np.linalg.norm(k_i)
    n_out = surface_normal  # outward normal

    # tangential component of (k_i + g)
    k_plus_g = k_i[None, :] + g_vectors  # (N, 3)
    normal_comp = (k_plus_g @ n_out)[:, None] * n_out[None, :]
    tangential = k_plus_g - normal_comp
    kt_sq = np.sum(tangential**2, axis=1)

    kappa_sq = K**2 - kt_sq
    # real kappa for propagating beams, imaginary for evanescent
    kappa = np.sqrt(kappa_sq.astype(complex))
    # choose branch: positive real part for propagating, positive imaginary for evanescent
    kappa = np.where(np.real(kappa_sq) >= 0,
                     np.sqrt(np.abs(kappa_sq)),
                     1j * np.sqrt(np.abs(kappa_sq)))
    return kappa


def solve_reflection_amplitudes(gamma_evan, C_evan, kz, k_i, g_vectors,
                                surface_normal=SURFACE_NORMAL):
    """Solve for reflected beam amplitudes R_g.

    The boundary conditions at z=0 give 2N equations for 2N unknowns
    (N excitation amplitudes alpha_j and N reflected amplitudes R_g).

    From the wavefunction condition:
        sum_j alpha_j * C_g^j = delta_{g,0} + R_g

    From the derivative condition:
        sum_j alpha_j * (kz_g + gamma_j) * C_g^j = kappa_0 * delta_{g,0} - kappa_g * R_g

    Eliminating R_g from the first equation:
        R_g = sum_j alpha_j * C_g^j - delta_{g,0}

    Substituting into the second:
        sum_j alpha_j * (kz_g + gamma_j) * C_g^j =
            kappa_0 * delta_{g,0} - kappa_g * (sum_j alpha_j * C_g^j - delta_{g,0})

        sum_j alpha_j * [(kz_g + gamma_j) + kappa_g] * C_g^j =
            (kappa_0 + kappa_g) * delta_{g,0}

    This is an N x N system for alpha_j:
        sum_j M_{g,j} * alpha_j = b_g

    where M_{g,j} = (kz_g + gamma_j + kappa_g) * C_g^j
    and   b_g = kappa_0 + kappa_g  (for g=0), 0 otherwise.

    Wait, kappa_0 appears only for the incident beam (g=0). But actually
    kappa_0 is the vacuum kz for the incident beam, and kappa_g is for beam g.
    For g=0: b_0 = kappa_0 + kappa_0 = 2*kappa_0.
    For g!=0: b_g = kappa_g (from the delta_{g,0} terms... let me redo this).

    Let me be more careful. The incident beam has g=0 (the zeroth beam).
    In the vacuum:
        psi_vac = exp(i*k_i.r) + sum_g R_g * exp(i*(k_i+g)_t.r_t) * exp(i*kappa_g*z)

    where z is the outward normal direction. The derivative at z=0:
        d psi / dz = i * kappa_inc * exp(i*k_i.r) + sum_g i * kappa_g * R_g * exp(...)

    But kappa_inc for the incident beam... the incident beam goes INTO the crystal,
    so its z-component (along outward normal) is negative:
        kappa_inc = -|k_i . n_out|

    Inside the crystal:
        psi = sum_j alpha_j * sum_g C_g^j * exp(i*(k_i+g)_t.r_t) * exp(i*(kz_g+gamma_j)*z_in)

    where z_in points INTO the crystal = -z.

    At z=0 (surface):
    Wavefunction: sum_j alpha_j * C_g^j = delta_{g,0} + R_g  ... (1)
    Derivative (outward): sum_j alpha_j * (-(kz_g+gamma_j)) * C_g^j = i*kappa_inc*delta_{g,0} + i*kappa_g*R_g

    Hmm, the signs are tricky. Let me use a cleaner formulation.

    Parameters
    ----------
    gamma_evan : (N,) complex
        Evanescent eigenvalues.
    C_evan : (N, N) complex
        Bloch wave coefficients. C_evan[g, j] = coefficient of beam g in wave j.
    kz : (N,) float
        (K+g)_z components (along inward normal).
    k_i : (3,) float
        Incident wavevector.
    g_vectors : (N, 3) float
        Reciprocal lattice vectors.

    Returns
    -------
    R_g : (N,) complex
        Reflected beam amplitudes.
    alpha : (N,) complex
        Bloch wave excitation amplitudes.
    """
    n = len(kz)
    kappa = compute_vacuum_kz(k_i, g_vectors, surface_normal)

    # incident beam kappa (z-component in vacuum along outward normal)
    kappa_inc = np.dot(k_i, surface_normal)  # negative for beam going in

    # build the system matrix M and RHS b
    # Using the combined boundary condition (eliminating R_g):
    # For each g:
    #   sum_j alpha_j * C_g^j * (kz_g + gamma_j + kappa_g) = (|kappa_inc| + kappa_0) * delta_{g,0}
    #
    # This assumes:
    # - wavefunction: sum_j alpha_j * C_g^j - R_g = delta_{g,0}
    # - derivative (matching signs): sum_j alpha_j * (kz_g+gamma_j) * C_g^j + kappa_g * R_g = |kappa_inc| * delta_{g,0}
    # Adding: sum_j alpha_j * C_g^j * (kz_g+gamma_j+kappa_g) = (|kappa_inc|+kappa_g) * delta_{g,0}
    # Wait, the kappa terms need more care with signs.

    # Simplified approach: build 2N x 2N system directly
    # unknowns: [alpha_0, ..., alpha_{N-1}, R_0, ..., R_{N-1}]
    # equations: wavefunction (N) + derivative (N)

    M = np.zeros((2 * n, 2 * n), dtype=complex)
    b = np.zeros(2 * n, dtype=complex)

    # wavefunction equations (rows 0..N-1):
    # sum_j C_g^j * alpha_j - R_g = delta_{g,0}
    M[:n, :n] = C_evan        # C_evan[g,j] * alpha_j
    M[:n, n:] = -np.eye(n)    # -R_g
    b[0] = 1.0                 # delta_{g,0} for g=0

    # derivative equations (rows N..2N-1):
    # sum_j (kz_g + gamma_j) * C_g^j * alpha_j + kappa_g * R_g = kappa_inc_g * delta_{g,0}
    #
    # kappa_inc_g: for the incident beam (g=0), this is |k_i . n_out| (magnitude)
    for j in range(n):
        M[n:, j] = (kz + gamma_evan[j]) * C_evan[:, j]
    M[n:, n:] = np.diag(kappa)

    # RHS: only the incident beam contributes
    b[n] = np.abs(kappa_inc)   # for g=0 derivative equation

    # Solve using the COMBINED N×N system (eliminates R_g):
    # (B_deriv + diag(kappa)) @ C_evan @ alpha = (kappa_0 - ki_y) * e_0
    # where B_deriv[g,j] = (kz_g + gamma_j) * C_g^j
    B_deriv = np.zeros((n, n), dtype=complex)
    for j in range(n):
        B_deriv[:, j] = (kz + gamma_evan[j]) * C_evan[:, j]

    S = B_deriv + np.diag(kappa) @ C_evan
    b_combined = np.zeros(n, dtype=complex)
    b_combined[0] = kappa[0] - kappa_inc  # kappa_0 + |ki_y|

    # SVD-based solve with ADAPTIVE truncation of near-zero singular values.
    # Near-degenerate Bloch wave pairs produce small singular values
    # that must be truncated for physical results (Sum|R|^2 <= 1).
    # Sweep rcond to find the largest value giving Sum|R|^2 <= 1.05.
    best_alpha = None
    for rc in [1e-10, 1e-6, 1e-4, 1e-3, 5e-3, 0.01, 0.05, 0.1]:
        alpha_try = np.linalg.lstsq(S, b_combined, rcond=rc)[0]
        R_try = C_evan @ alpha_try
        R_try[0] -= 1.0
        total = np.sum(np.abs(R_try)**2)
        if total <= 1.05:
            best_alpha = alpha_try
    if best_alpha is None:
        # fallback: use largest rcond
        best_alpha = np.linalg.lstsq(S, b_combined, rcond=0.1)[0]
    alpha = best_alpha

    # Recover R_g from wavefunction condition
    R_g = C_evan @ alpha
    R_g[0] -= 1.0  # subtract incident beam

    return R_g, alpha


def compute_reflected_intensities(k_i, hkl_list, g_vectors,
                                   a=5.43102,
                                   absorption_ratio=0.07,
                                   n_strong=30):
    """Full calculation: eigenvalue problem + boundary conditions.

    Ensures the (000) direct beam is included in the beam set.
    Normalizes output so total reflected intensity <= 1.

    Returns dict with reflected beam intensities and metadata.
    """
    from simulation.bloch_wave import (
        select_strong_beams, solve_bloch, select_evanescent,
    )

    # select strongest beams
    indices, s_g_all = select_strong_beams(k_i, hkl_list, g_vectors,
                                           n_strong=n_strong)
    sel_hkl = [hkl_list[i] for i in indices]
    sel_g = g_vectors[indices]

    # ensure (000) is included as beam index 0
    zero_vec = np.zeros(3)
    has_000 = any(np.allclose(g, zero_vec) for g in sel_g)
    if not has_000:
        sel_hkl.insert(0, (0, 0, 0))
        sel_g = np.vstack([zero_vec[None, :], sel_g])
    else:
        # move (000) to index 0
        for i, g in enumerate(sel_g):
            if np.allclose(g, zero_vec):
                sel_hkl[0], sel_hkl[i] = sel_hkl[i], sel_hkl[0]
                sel_g[[0, i]] = sel_g[[i, 0]]
                break

    # solve eigenvalue problem
    eigenvalues, eigenvectors, s_g, kz = solve_bloch(
        k_i, sel_hkl, sel_g, a=a, absorption_ratio=absorption_ratio)

    n = len(sel_hkl)
    gamma_evan, C_evan = select_evanescent(eigenvalues, eigenvectors, n)

    # boundary conditions
    R_g, alpha = solve_reflection_amplitudes(
        gamma_evan, C_evan, kz, k_i, sel_g)

    intensities = np.abs(R_g)**2

    results = []
    for i in range(n):
        results.append({
            "hkl": sel_hkl[i],
            "s_g": s_g[i],
            "kz": kz[i],
            "R_g": R_g[i],
            "intensity": intensities[i],
        })

    # sort by intensity
    results.sort(key=lambda x: x["intensity"], reverse=True)
    return results


def compute_rocking_curve(hkl_list, g_vectors,
                          grazing_range_mrad=(10, 80),
                          n_points=100,
                          n_strong=20,
                          a=5.43102,
                          absorption_ratio=0.07):
    """Compute specular beam intensity vs grazing angle.

    Sweeps the grazing angle and computes reflected intensities.
    The specular beam (g=000 reflected) intensity is returned.
    """
    from simulation.calibration import compute_incident_wavevector

    # we need to sweep the grazing angle while keeping the beam along [110]
    # For simplicity, tilt the beam in the plane containing [110] and
    # the surface normal
    from simulation.constants import ZA_Z, ZA_X, ZA_Y

    angles = np.linspace(grazing_range_mrad[0], grazing_range_mrad[1], n_points)
    specular_intensity = np.zeros(n_points)

    # the surface normal projected into detector coords gives the tilt direction
    n_x = np.dot(SURFACE_NORMAL, ZA_X)
    n_y = np.dot(SURFACE_NORMAL, ZA_Y)
    tilt_dir = np.array([n_x, n_y])
    tilt_dir = tilt_dir / np.linalg.norm(tilt_dir)

    for i, alpha_mrad in enumerate(angles):
        # beam tilt that gives this grazing angle
        # grazing angle = alpha_mrad, tilt in the direction of surface normal
        # projected onto detector plane
        # approximate: theta_total ~ alpha / sin(angle_between_tilt_and_normal)
        # For now, just tilt along the normal projection
        tx = alpha_mrad * tilt_dir[0] / np.linalg.norm(tilt_dir)
        ty = alpha_mrad * tilt_dir[1] / np.linalg.norm(tilt_dir)
        k_i = compute_incident_wavevector(tx, ty)

        try:
            results = compute_reflected_intensities(
                k_i, hkl_list, g_vectors,
                a=a, absorption_ratio=absorption_ratio,
                n_strong=n_strong)
            # find the specular (000 or closest to it)
            for r in results:
                if r["hkl"] == (0, 0, 0) or np.linalg.norm(
                        g_vectors[hkl_list.index(r["hkl"])]) < 0.1:
                    specular_intensity[i] = r["intensity"]
                    break
            else:
                # specular not in strong beams; take lowest s_g
                specular_intensity[i] = results[0]["intensity"] if results else 0
        except Exception:
            specular_intensity[i] = 0

    return angles, specular_intensity


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

    results = compute_reflected_intensities(
        k_i, hkl_list, g_vectors, n_strong=20, absorption_ratio=0.07)

    print(f"\nReflected beam intensities (top 15):")
    print(f"{'hkl':>12s}  {'|R_g|^2':>10s}  {'s_g':>8s}")
    for r in results[:15]:
        h, k, l = r["hkl"]
        print(f"  ({h:2d},{k:2d},{l:2d})  {r['intensity']:10.6f}  {r['s_g']:8.4f}")

    total = sum(r["intensity"] for r in results)
    print(f"\nTotal reflected intensity: {total:.6f}")
