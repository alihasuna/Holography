"""Image-geometry relations of reflection electron microscopy: foreshortening, exit-plane mapping and
the shadow length of a step transverse to the beam.

Source map SM07, evidence DERIVED_HERE (C report section 6; E review M6). Conventions
(docs/physics_conventions.md): glancing angle theta to the surface plane, lengths in A.

  * foreshortening: the image of the surface is compressed along the beam by sin(theta_ext);
    directions perpendicular to the beam are not foreshortened. foreshortening() returns the
    magnitude 1/sin(theta_ext) (44.46x at the (6,-6,6) setting, check T20; 61x at (0,0,8)).
  * exit-plane mapping: a feature at surface coordinate z_s along the beam appears at exit-plane
    height x = x_0 - z_s tan(theta); inversely z_s = (x_0 - x)/tan(theta).
  * shadow length: a step of height h transverse to the beam shadows h / tan(theta_ext) of the
    surface (139 A per Si(111) bilayer at 22.5 mrad, 230 A at (4,-4,4)). Shadow masks are computed
    at the actual operating angle by reflection_holo.quantification.shadow, never hard-coded.
"""
from __future__ import annotations

import numpy as np


def _check_theta(theta_rad) -> np.ndarray:
    th = np.asarray(theta_rad, dtype=float)
    if np.any(~np.isfinite(th)) or np.any(th <= 0.0) or np.any(th >= np.pi / 2):
        raise ValueError(f"glancing angle must lie in (0, pi/2) rad, got {theta_rad!r}")
    return th


def _out(x):
    return float(x) if np.ndim(x) == 0 else x


def image_compression(theta_ext_rad):
    """sin(theta_ext): image length along the beam per unit surface length (SM07, DERIVED_HERE)."""
    return _out(np.sin(_check_theta(theta_ext_rad)))


def foreshortening(theta_ext_rad):
    """Foreshortening magnitude 1/sin(theta_ext) along the beam (SM07, DERIVED_HERE; check T20)."""
    return _out(1.0 / np.sin(_check_theta(theta_ext_rad)))


def exit_plane_height_A(z_s_A, x0_A: float, theta_rad):
    """Exit-plane height x = x_0 - z_s tan(theta) of a surface feature at z_s (SM07, DERIVED_HERE)."""
    return _out(x0_A - np.asarray(z_s_A, dtype=float) * np.tan(_check_theta(theta_rad)))


def surface_coordinate_A(x_A, x0_A: float, theta_rad):
    """Surface coordinate z_s = (x_0 - x)/tan(theta) from an exit-plane height x (SM07,
    DERIVED_HERE); the inverse of exit_plane_height_A."""
    return _out((x0_A - np.asarray(x_A, dtype=float)) / np.tan(_check_theta(theta_rad)))


def shadow_length_A(h_A, theta_ext_rad):
    """Length of surface shadowed by a step of height |h| transverse to the beam: |h| / tan(theta).

    Evaluate at the actual operating angle (the incidence angle for the illumination shadow, the
    exit angle for the blocked-view strip; equal for the specular beam). Source map SM07, evidence
    DERIVED_HERE.
    """
    return _out(np.abs(np.asarray(h_A, dtype=float)) / np.tan(_check_theta(theta_ext_rad)))
