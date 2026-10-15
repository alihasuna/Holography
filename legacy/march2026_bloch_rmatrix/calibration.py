"""
calibration.py
==============
Convert CL3 beam tilt DAC values (BTX, BTY) to physical tilt angles
and compute the effective grazing angle on the (111) surface.

Calibration source: beam_tilt_calibration_formulas.pdf, Eqs. 21-26.
"""

import sys
import numpy as np
from pathlib import Path

# allow importing from parent dir (process_diffraction.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation.constants import (
    BT_REFERENCE, BT_CALIBRATION_MATRIX, BT_CALIBRATION_OFFSET,
    ZA_Z, ZA_X, ZA_Y, SURFACE_NORMAL, ANGULAR_SCALE,
    LAMBDA_200KV, K_200KV,
)


def relativistic_wavelength(voltage_kv):
    """Relativistic electron wavelength in Angstroms."""
    v = voltage_kv * 1e3
    return 12.2643 / np.sqrt(v * (1.0 + 0.978476e-6 * v))


def btx_bty_to_tilt_mrad(btx, bty):
    """Convert BTX/BTY DAC values to physical beam tilt (theta_x, theta_y) in mrad.

    Uses the affine calibration:
        theta = A @ (BT - BT_ref) + b
    """
    delta = np.array([btx, bty]) - BT_REFERENCE
    theta = BT_CALIBRATION_MATRIX @ delta + BT_CALIBRATION_OFFSET
    return theta[0], theta[1]


def total_tilt_mrad(theta_x_mrad, theta_y_mrad):
    """Magnitude of beam tilt in mrad."""
    return np.sqrt(theta_x_mrad**2 + theta_y_mrad**2)


def compute_grazing_angle(theta_x_mrad, theta_y_mrad):
    """Compute the effective grazing angle on the (111) surface.

    The crystal is on the [110] zone axis (beam along [110]).
    CL3 tilts the beam by (theta_x, theta_y) in the detector plane.
    The grazing angle is the complement of the angle between the
    tilted beam direction and the (111) surface plane.

    Returns grazing angle in mrad.
    """
    # beam tilt in radians
    tx = theta_x_mrad * 1e-3
    ty = theta_y_mrad * 1e-3

    # tilted beam direction in crystal Cartesian coordinates:
    # z_hat = [110]/sqrt(2) = beam axis (on zone)
    # x_hat = [1-10]/sqrt(2) = detector horizontal
    # y_hat = [001] = detector vertical
    k_dir = ZA_Z + tx * ZA_X + ty * ZA_Y
    k_dir = k_dir / np.linalg.norm(k_dir)

    # grazing angle = angle between tilted beam and the surface PLANE
    # = arcsin(|k_dir . surface_normal|)
    # When beam is in the surface plane (no tilt component along normal),
    # grazing angle = 0. CL3 tilt pushes beam out of the plane.
    sin_grazing = np.abs(np.dot(k_dir, SURFACE_NORMAL))
    grazing_rad = np.arcsin(np.clip(sin_grazing, -1, 1))
    return grazing_rad * 1e3  # mrad


def compute_tilted_beam_direction(theta_x_mrad, theta_y_mrad):
    """Return the unit vector of the tilted beam in Cartesian crystal coords.

    Crystal frame: standard cubic axes [100], [010], [001].
    """
    tx = theta_x_mrad * 1e-3
    ty = theta_y_mrad * 1e-3
    k_dir = ZA_Z + tx * ZA_X + ty * ZA_Y
    return k_dir / np.linalg.norm(k_dir)


def compute_incident_wavevector(theta_x_mrad, theta_y_mrad):
    """Return the full incident wavevector k_i in A^-1 (crystal Cartesian)."""
    k_dir = compute_tilted_beam_direction(theta_x_mrad, theta_y_mrad)
    return K_200KV * k_dir


def estimate_grazing_from_specular_shift(specular_yx, direct_beam_yx=None,
                                          angular_scale=ANGULAR_SCALE):
    """Estimate grazing angle from the specular beam displacement on the detector.

    In reflection geometry, the specular beam exits at angle 2*alpha from
    the incident direction. The displacement on the detector encodes this.

    Parameters
    ----------
    specular_yx : (float, float)
        Specular beam position (y, x) in pixels.
    direct_beam_yx : (float, float) or None
        Direct beam position. If None, assumes detector centre (128, 128).
    angular_scale : float
        mrad per pixel.

    Returns
    -------
    grazing_mrad : float
        Estimated grazing angle in mrad.
    """
    if direct_beam_yx is None:
        direct_beam_yx = (128.0, 128.0)
    dy = specular_yx[0] - direct_beam_yx[0]
    dx = specular_yx[1] - direct_beam_yx[1]
    shift_px = np.sqrt(dy**2 + dx**2)
    two_alpha_mrad = shift_px * angular_scale
    return two_alpha_mrad / 2.0


def load_metadata_from_hm(hm_path):
    """Load BTX/BTY and other metadata from an .hm file.

    Reuses the load_hm / extract_metadata pattern from process_diffraction.py.
    """
    import h5py
    import json
    import base64

    with h5py.File(hm_path, "r") as f:
        meta = json.loads(f["meta"][()])

    mic = meta.get("microscope", {})

    def _dac(key):
        v = mic.get(key, {})
        if isinstance(v, dict):
            raw = base64.b64decode(v["data"])
            return np.frombuffer(raw, dtype=v["dtype"]).tolist()
        return [0, 0]

    return {
        "n_frames": meta.get("n_frames", 1),
        "voltage_kv": mic.get("Gun.HighVoltage", 200),
        "cl_mm": mic.get("Mag", 500),
        "alpha_deg": mic.get("Tilt.Angle", 0),
        "btx": _dac("BTX"),
        "bty": _dac("BTY"),
    }


def calibrate_all_patterns(data_dir):
    """Compute beam tilt and grazing angle for all .hm files in a directory.

    Returns list of dicts with filename, BTX/BTY, theta_x/y, grazing angle.
    """
    import glob as gl
    results = []
    for path in sorted(gl.glob(str(Path(data_dir) / "*.hm"))):
        meta = load_metadata_from_hm(path)
        # use element [1] of BTX/BTY arrays (fine DAC value)
        btx = meta["btx"][1] if len(meta["btx"]) > 1 else meta["btx"][0]
        bty = meta["bty"][1] if len(meta["bty"]) > 1 else meta["bty"][0]

        tx, ty = btx_bty_to_tilt_mrad(btx, bty)
        grazing = compute_grazing_angle(tx, ty)

        results.append({
            "filename": Path(path).stem,
            "btx_dac": btx,
            "bty_dac": bty,
            "theta_x_mrad": tx,
            "theta_y_mrad": ty,
            "total_tilt_mrad": total_tilt_mrad(tx, ty),
            "grazing_angle_mrad": grazing,
            "grazing_angle_deg": grazing / 1000.0 * (180.0 / np.pi),
            "n_frames": meta["n_frames"],
            "alpha_deg": meta["alpha_deg"],
        })

    return results


if __name__ == "__main__":
    # quick test with the known experimental values
    tx, ty = btx_bty_to_tilt_mrad(-814.0, 135.0)
    print(f"CL3 beam tilt: theta_x = {tx:.2f} mrad, theta_y = {ty:.2f} mrad")
    print(f"Total tilt magnitude: {total_tilt_mrad(tx, ty):.2f} mrad "
          f"({total_tilt_mrad(tx, ty) / 1000 * 180 / np.pi:.2f} deg)")

    grazing = compute_grazing_angle(tx, ty)
    print(f"Grazing angle on (111): {grazing:.2f} mrad "
          f"({grazing / 1000 * 180 / np.pi:.2f} deg)")

    k_i = compute_incident_wavevector(tx, ty)
    print(f"k_i = {k_i} A^-1, |k_i| = {np.linalg.norm(k_i):.2f} A^-1")
