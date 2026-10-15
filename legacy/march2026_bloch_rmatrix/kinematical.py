"""
kinematical.py
==============
Kinematical Ewald sphere construction for bulk Bragg reflection
diffraction from Si[110] with beam tilt (grazing incidence on (1-11)).

Predicts spot positions on the 256x256 Merlin detector.
"""

import numpy as np
from simulation.constants import (
    SI_LATTICE_PARAM, K_200KV,
    ZA_Z, ZA_X, ZA_Y, SURFACE_NORMAL,
    ANGULAR_SCALE, DETECTOR_SHAPE,
)
from simulation.structure_factors import (
    is_allowed_diamond_cubic, structure_factor,
)
from simulation.calibration import (
    compute_incident_wavevector, compute_grazing_angle,
    btx_bty_to_tilt_mrad,
)


def generate_reciprocal_lattice(max_index=12, a=SI_LATTICE_PARAM):
    """Generate allowed Si reciprocal lattice vectors.

    Returns arrays of hkl indices and g-vectors (A^-1) for allowed reflections.
    """
    recip = 2 * np.pi / a
    hkl_list = []
    g_list = []
    f_sq_list = []

    for h in range(-max_index, max_index + 1):
        for k in range(-max_index, max_index + 1):
            for l in range(-max_index, max_index + 1):
                if h == 0 and k == 0 and l == 0:
                    continue
                allowed, _ = is_allowed_diamond_cubic(h, k, l)
                if not allowed:
                    continue

                g_vec = recip * np.array([h, k, l], dtype=float)
                F = structure_factor(h, k, l, a=a)

                hkl_list.append((h, k, l))
                g_list.append(g_vec)
                f_sq_list.append(abs(F)**2)

    return hkl_list, np.array(g_list), np.array(f_sq_list)


def compute_excitation_errors(k_i, g_vectors):
    """Compute excitation error s_g for each reciprocal lattice vector.

    s_g = (|k_i|^2 - |k_i + g|^2) / (2 * |k_i|)

    Negative s_g means the reciprocal lattice point is outside the Ewald sphere.
    s_g = 0 means exact Bragg condition.
    """
    k_mag = np.linalg.norm(k_i)
    k_f_vectors = k_i[None, :] + g_vectors  # (N, 3)
    k_f_mag_sq = np.sum(k_f_vectors**2, axis=1)
    s_g = (k_mag**2 - k_f_mag_sq) / (2.0 * k_mag)
    return s_g


def filter_reflection_geometry(k_i, g_vectors, surface_normal=SURFACE_NORMAL):
    """Identify which diffracted beams exit on the reflection side.

    In reflection geometry, the diffracted beam k_f = k_i + g must have a
    component along the outward surface normal (i.e., exit the crystal
    on the same side the beam entered).

    Returns boolean mask: True for reflections exiting on the vacuum side.
    """
    k_f_vectors = k_i[None, :] + g_vectors  # (N, 3)
    # the incident beam enters the crystal: k_i . n < 0 (going into crystal)
    # the reflected beam exits: k_f . n > 0 (going out of crystal)
    # but sign depends on convention. For grazing incidence, the incident beam
    # has a small negative component along n (entering), and reflected beams
    # have positive component (exiting).
    exit_component = k_f_vectors @ surface_normal
    return exit_component > 0


def diffracted_beam_to_detector(k_i, k_f, angular_scale=ANGULAR_SCALE,
                                 specular_yx=None):
    """Map a diffracted beam k_f to detector pixel coordinates.

    The angular deviation of k_f from k_i determines the position.
    We project onto the detector plane (perpendicular to the nominal beam axis).

    Parameters
    ----------
    k_i : (3,) array
        Incident wavevector.
    k_f : (3,) or (N,3) array
        Diffracted wavevector(s).
    angular_scale : float
        mrad per pixel.
    specular_yx : (float, float) or None
        If given, positions are relative to the specular beam position.
        If None, positions are relative to the direct beam (detector center).

    Returns
    -------
    positions : (N, 2) array
        (y, x) pixel positions on detector.
    """
    k_f = np.atleast_2d(k_f)
    k_mag = np.linalg.norm(k_i)

    # angular deviation from incident beam direction
    # in the detector plane (x_hat, y_hat coordinates)
    # delta_theta_x = (k_f . x_hat - k_i . x_hat) / k_mag
    # delta_theta_y = (k_f . y_hat - k_i . y_hat) / k_mag
    delta_kx = k_f @ ZA_X - np.dot(k_i, ZA_X)
    delta_ky = k_f @ ZA_Y - np.dot(k_i, ZA_Y)

    # convert to mrad
    delta_theta_x = delta_kx / k_mag * 1e3  # mrad
    delta_theta_y = delta_ky / k_mag * 1e3  # mrad

    # convert to pixels from center
    px_x = delta_theta_x / angular_scale
    px_y = delta_theta_y / angular_scale

    # absolute pixel positions
    if specular_yx is not None:
        # compute specular beam position first
        # specular = k_i reflected about surface normal
        k_spec = k_i - 2 * np.dot(k_i, SURFACE_NORMAL) * SURFACE_NORMAL
        spec_dx = (np.dot(k_spec, ZA_X) - np.dot(k_i, ZA_X)) / k_mag * 1e3
        spec_dy = (np.dot(k_spec, ZA_Y) - np.dot(k_i, ZA_Y)) / k_mag * 1e3
        spec_px_x = spec_dx / angular_scale
        spec_px_y = spec_dy / angular_scale

        # offset so specular lands at specular_yx
        cy, cx = specular_yx
        y_positions = cy + (px_y - spec_px_y)
        x_positions = cx + (px_x - spec_px_x)
    else:
        cy, cx = DETECTOR_SHAPE[0] / 2, DETECTOR_SHAPE[1] / 2
        y_positions = cy + px_y
        x_positions = cx + px_x

    return np.column_stack([y_positions, x_positions])


def predict_spots(theta_x_mrad, theta_y_mrad,
                  max_index=12,
                  excitation_error_tol=0.5,
                  specular_yx=None):
    """Predict diffraction spot positions for given beam tilt.

    Parameters
    ----------
    theta_x_mrad, theta_y_mrad : float
        Physical beam tilt from CL3 in mrad.
    max_index : int
        Maximum Miller index to consider.
    excitation_error_tol : float
        Maximum |s_g| in A^-1 to include a reflection.
    specular_yx : (float, float) or None
        Specular beam position on detector. If given, predicted positions
        are anchored to this point.

    Returns
    -------
    spots : list of dict
        Each dict: hkl, y_px, x_px, s_g, F_sq, g_mag, d_spacing.
    """
    k_i = compute_incident_wavevector(theta_x_mrad, theta_y_mrad)
    hkl_list, g_vectors, f_sq = generate_reciprocal_lattice(max_index)

    # excitation errors
    s_g = compute_excitation_errors(k_i, g_vectors)

    # filter by excitation error
    near_ewald = np.abs(s_g) < excitation_error_tol

    # filter for reflection geometry
    exits_reflection = filter_reflection_geometry(k_i, g_vectors)

    # combined mask
    mask = near_ewald & exits_reflection

    # compute diffracted wavevectors for selected reflections
    selected_g = g_vectors[mask]
    selected_hkl = [hkl_list[i] for i in range(len(hkl_list)) if mask[i]]
    selected_sg = s_g[mask]
    selected_fsq = f_sq[mask]

    k_f_vectors = k_i + selected_g

    # map to detector
    positions = diffracted_beam_to_detector(k_i, k_f_vectors,
                                             specular_yx=specular_yx)

    # build output
    spots = []
    for i, (hkl, sg, fsq) in enumerate(zip(selected_hkl, selected_sg,
                                             selected_fsq)):
        g_mag = np.linalg.norm(selected_g[i])
        d = 2 * np.pi / g_mag if g_mag > 0 else np.inf
        spots.append({
            "hkl": hkl,
            "y_px": positions[i, 0],
            "x_px": positions[i, 1],
            "s_g": sg,
            "F_sq": fsq,
            "g_mag": g_mag,
            "d_spacing": d,
        })

    # sort by |s_g| (closest to Bragg condition first)
    spots.sort(key=lambda s: abs(s["s_g"]))
    return spots


def predict_specular_position(theta_x_mrad, theta_y_mrad):
    """Predict where the specular (mirror-reflected) beam lands on the detector.

    The specular beam is the incident beam reflected about the surface normal.
    """
    k_i = compute_incident_wavevector(theta_x_mrad, theta_y_mrad)
    k_spec = k_i - 2 * np.dot(k_i, SURFACE_NORMAL) * SURFACE_NORMAL
    k_mag = np.linalg.norm(k_i)

    # angular position relative to incident beam
    spec_dx = (np.dot(k_spec, ZA_X) - np.dot(k_i, ZA_X)) / k_mag * 1e3
    spec_dy = (np.dot(k_spec, ZA_Y) - np.dot(k_i, ZA_Y)) / k_mag * 1e3

    cy, cx = DETECTOR_SHAPE[0] / 2, DETECTOR_SHAPE[1] / 2
    y = cy + spec_dy / ANGULAR_SCALE
    x = cx + spec_dx / ANGULAR_SCALE
    return y, x


if __name__ == "__main__":
    # test with experimental beam tilt
    tx, ty = btx_bty_to_tilt_mrad(-814.0, 135.0)
    grazing = compute_grazing_angle(tx, ty)
    print(f"Beam tilt: theta_x={tx:.1f}, theta_y={ty:.1f} mrad")
    print(f"Grazing angle: {grazing:.1f} mrad ({grazing/1e3*180/np.pi:.2f} deg)")

    # specular position
    spec_y, spec_x = predict_specular_position(tx, ty)
    print(f"\nSpecular beam position: y={spec_y:.1f}, x={spec_x:.1f} px")

    # predict spots
    spots = predict_spots(tx, ty, max_index=10, excitation_error_tol=1.0)
    print(f"\nPredicted {len(spots)} reflections (|s_g| < 1.0 A^-1):")
    print(f"{'hkl':>12s}  {'y_px':>6s}  {'x_px':>6s}  {'s_g':>8s}  "
          f"{'|F|^2':>8s}  {'d(A)':>6s}")
    for s in spots[:30]:
        h, k, l = s["hkl"]
        print(f"  ({h:2d},{k:2d},{l:2d})  {s['y_px']:6.1f}  {s['x_px']:6.1f}  "
              f"{s['s_g']:8.4f}  {s['F_sq']:8.2f}  {s['d_spacing']:6.3f}")
