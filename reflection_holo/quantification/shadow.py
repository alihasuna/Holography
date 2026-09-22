"""Shadow-exclusion masks computed from the geometry at the operating angle.

Source map SM07 (shadow length h/tan(theta)), evidence DERIVED_HERE (docs/03 section 4;
model_assumptions B9; E review M6). Exact ray tracing for a piecewise-constant terrace profile with
vertical risers transverse to the beam. Coordinates: z_s along the beam azimuth on the surface
(increasing downstream), heights h along the outward normal, in A.

A surface point (z, h(z)) is
  * ILLUMINATED if no top corner (z_c, h_c) upstream (z_c <= z) lies above the incoming ray:
        h_c - (z - z_c) tan(theta_in) <= h(z);
  * VISIBLE if no top corner downstream (z_c > z) lies above the outgoing ray:
        h_c - (z_c - z) tan(theta_out) <= h(z);
  * USABLE if both. Only usable pixels may be quantified.
For a single step of height |h| this gives an illumination shadow of length |h|/tan(theta_in)
downstream of a step whose upper terrace is upstream, and a blocked-view strip of length
|h|/tan(theta_out) upstream of a step whose upper terrace is downstream. The two strips lie on
opposite sides of the riser, so the shadow position distinguishes the step sense. Angles are the
actual operating angles (never hard-coded). Step edges transverse to the beam only: a mask on an
image with an axis perpendicular to the beam is the same for every perpendicular position.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_EPS_A = 1e-9


@dataclass(frozen=True)
class ShadowMasks:
    """Result of shadow_masks (source map SM07, evidence DERIVED_HERE)."""
    z_A: np.ndarray
    height_A: np.ndarray
    illuminated: np.ndarray
    visible: np.ndarray
    usable: np.ndarray
    theta_in_ext_rad: float
    theta_out_ext_rad: float


def terrace_profile_A(z_A, *, edges_A, h_start_A: float, heights_after_A) -> np.ndarray:
    """Piecewise-constant height h(z): h_start for z < edges[0]; heights_after[i] for
    edges[i] <= z < edges[i+1]. Edges strictly increasing. Source map SM07, evidence
    DERIVED_HERE."""
    z = np.asarray(z_A, dtype=float)
    e = np.asarray(edges_A, dtype=float)
    ha = np.asarray(heights_after_A, dtype=float)
    if e.ndim != 1 or e.shape != ha.shape:
        raise ValueError("edges_A and heights_after_A must be 1-D of equal length")
    if np.any(np.diff(e) <= 0):
        raise ValueError("edges must be strictly increasing")
    levels = np.concatenate([[float(h_start_A)], ha])
    return levels[np.searchsorted(e, z, side="right")]


def shadow_masks(z_A, *, edges_A, h_start_A: float, heights_after_A, theta_in_ext_rad: float,
                 theta_out_ext_rad: float) -> ShadowMasks:
    """Illumination, visibility and usable masks along the beam for a terrace profile at the given
    operating angles (all required). Source map SM07, evidence DERIVED_HERE."""
    for th in (theta_in_ext_rad, theta_out_ext_rad):
        if not 0.0 < th < np.pi / 2:
            raise ValueError("glancing angles must lie in (0, pi/2) rad")
    z = np.asarray(z_A, dtype=float)
    if z.ndim != 1:
        raise ValueError("z_A must be 1-D (the coordinate along the beam)")
    e = np.asarray(edges_A, dtype=float)
    h = terrace_profile_A(z, edges_A=e, h_start_A=h_start_A, heights_after_A=heights_after_A)
    levels = np.concatenate([[float(h_start_A)], np.asarray(heights_after_A, dtype=float)])
    corners_h = np.maximum(levels[:-1], levels[1:])          # top corner of each riser
    t_in, t_out = np.tan(theta_in_ext_rad), np.tan(theta_out_ext_rad)

    dz = z[:, None] - e[None, :]                             # z - z_c
    up = dz >= 0.0                                           # corner upstream of (or at) z
    block_in = up & (corners_h[None, :] - dz * t_in > h[:, None] + _EPS_A)
    block_out = (~up) & (corners_h[None, :] - (-dz) * t_out > h[:, None] + _EPS_A)
    illuminated = ~block_in.any(axis=1)
    visible = ~block_out.any(axis=1)
    return ShadowMasks(z_A=z, height_A=h, illuminated=illuminated, visible=visible,
                       usable=illuminated & visible, theta_in_ext_rad=float(theta_in_ext_rad),
                       theta_out_ext_rad=float(theta_out_ext_rad))
