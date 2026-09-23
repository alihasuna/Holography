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

Height fields (``height_field_masks``, ``height_field_corner_maxima``; agent T2, DERIVED_HERE): the
same rules for a general surface h(y, z), one row per perpendicular position y (each row is an
independent profile along the beam: rays travel in planes of constant y for the specular beam). Two
declared profiles along z:
  * "piecewise_constant": n cells [z0 + j dz, z0 + (j+1) dz) with the height h_j of the cell,
    vertical risers at the cell boundaries (B13), a corner of height max(h_(j-1), h_j) at every
    boundary (a boundary between equal heights is a dominated corner and changes nothing);
    masks are evaluated at the cell centres z0 + (j + 1/2) dz;
  * "piecewise_linear": n + 1 vertices at z0 + j dz, the surface linear between them; masks are
    evaluated at the vertices (the maxima of h + z tan(theta) over a linear piece are at its ends).
Upstream of z0 the surface continues flat at a declared level (a vertical riser at z0 if it differs
from the first height); nothing exists downstream of the field end z0 + n dz (the exit plane).
The illumination test uses the running maximum W of h_c + z_c tan(theta_in) over the upstream
corners, the visibility test the running maximum V of h_c + (L - z_c) tan(theta_out) over the
downstream corners; for a profile whose edges lie on cell boundaries the masks equal
``shadow_masks`` at the cell centres (tests/forward_geometric/test_height_field.py).
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


# --------------------------------------------------------------------------------------------------
# Height fields h(y, z) (module docstring; agent T2)
# --------------------------------------------------------------------------------------------------
HEIGHT_FIELD_PROFILES = ("piecewise_constant", "piecewise_linear")


@dataclass(frozen=True)
class HeightFieldMasks:
    """Result of height_field_masks: masks at the evaluation points of each row (cell centres for
    "piecewise_constant", vertices for "piecewise_linear"). Arrays are (n_rows, n_points)."""
    z_A: np.ndarray
    height_A: np.ndarray
    illuminated: np.ndarray
    visible: np.ndarray
    usable: np.ndarray
    theta_in_ext_rad: float
    theta_out_ext_rad: float
    profile: str


def _check_height_field(heights_A, z_start_A, dz_A, profile, upstream_level_A, theta_in_ext_rad,
                        theta_out_ext_rad) -> np.ndarray:
    for th in (theta_in_ext_rad, theta_out_ext_rad):
        if not 0.0 < th < np.pi / 2:
            raise ValueError("glancing angles must lie in (0, pi/2) rad")
    if profile not in HEIGHT_FIELD_PROFILES:
        raise ValueError(f"profile must be one of {HEIGHT_FIELD_PROFILES}, got {profile!r}")
    h = np.asarray(heights_A, dtype=float)
    if h.ndim != 2 or h.shape[1] < 2:
        raise ValueError("heights_A must be 2-D (rows = perpendicular positions, columns along the "
                         "beam) with at least 2 points per row")
    if not np.all(np.isfinite(h)):
        raise ValueError("heights_A must be finite")
    for name, v in (("z_start_A", z_start_A), ("upstream_level_A", upstream_level_A)):
        if not np.isfinite(float(v)):
            raise ValueError(f"{name} must be finite")
    if not (np.isfinite(float(dz_A)) and float(dz_A) > 0):
        raise ValueError("dz_A must be finite and > 0")
    return h


def height_field_corner_maxima(heights_A, *, z_start_A: float, dz_A: float, profile: str,
                               upstream_level_A: float, theta_in_ext_rad: float,
                               theta_out_ext_rad: float) -> dict:
    """Running maxima of the corner terms (module docstring), all arguments required.

    Returns z_eval_A (evaluation points), z_end_A (field end = exit plane), and per row and
    evaluation point j:
      W_up_A[:, j]   max of h_c + z_c tan(theta_in) over the corners at or upstream of point j's
                     cell (constant: boundaries b <= j and the field start; linear: vertices
                     k <= j and the field-start corner);
      V_down_A[:, j] max of h_c + (L - z_c) tan(theta_out) over the corners strictly downstream of
                     point j (constant: internal boundaries b >= j + 1; linear: vertices k > j);
                     -inf where there is none.
    Source map SM07, evidence DERIVED_HERE."""
    h = _check_height_field(heights_A, z_start_A, dz_A, profile, upstream_level_A,
                            theta_in_ext_rad, theta_out_ext_rad)
    z0, dz = float(z_start_A), float(dz_A)
    t_in, t_out = np.tan(theta_in_ext_rad), np.tan(theta_out_ext_rad)
    rows, n_pts = h.shape
    up = np.full((rows, 1), float(upstream_level_A))
    if profile == "piecewise_constant":
        n = n_pts
        L = z0 + n * dz
        z_eval = z0 + (np.arange(n) + 0.5) * dz
        zb = z0 + np.arange(n) * dz                                  # boundary b at z0 + b dz
        left = np.concatenate([up, h[:, :-1]], axis=1)
        corner_h = np.maximum(left, h)                               # (rows, n), boundary b = 0..n-1
        W = np.maximum.accumulate(corner_h + zb[None, :] * t_in, axis=1)
        wo = corner_h + (L - zb)[None, :] * t_out                    # internal boundaries b >= 1
        V = np.full((rows, n), -np.inf)
        if n > 1:
            rev = np.maximum.accumulate(wo[:, :0:-1], axis=1)[:, ::-1]   # max over b' >= b, b >= 1
            V[:, :-1] = rev                                          # point j: boundaries >= j + 1
    else:
        n = n_pts - 1
        L = z0 + n * dz
        z_eval = z0 + np.arange(n_pts) * dz
        start = np.maximum(up, h[:, :1]) + z0 * t_in                 # corner at the field start
        W = np.maximum(np.maximum.accumulate(h + z_eval[None, :] * t_in, axis=1), start)
        xs = h + (L - z_eval)[None, :] * t_out
        V = np.full((rows, n_pts), -np.inf)
        V[:, :-1] = np.maximum.accumulate(xs[:, :0:-1], axis=1)[:, ::-1]
    return dict(z_eval_A=z_eval, z_end_A=L, W_up_A=W, V_down_A=V, heights_A=h)


def height_field_masks(heights_A, *, z_start_A: float, dz_A: float, profile: str,
                       upstream_level_A: float, theta_in_ext_rad: float,
                       theta_out_ext_rad: float) -> HeightFieldMasks:
    """Illumination, visibility and usable masks of a height field h(y, z) at the operating angles
    (module docstring; one row per perpendicular position). Same conventions and tolerance as
    ``shadow_masks``. Source map SM07, evidence DERIVED_HERE."""
    c = height_field_corner_maxima(heights_A, z_start_A=z_start_A, dz_A=dz_A, profile=profile,
                                   upstream_level_A=upstream_level_A,
                                   theta_in_ext_rad=theta_in_ext_rad,
                                   theta_out_ext_rad=theta_out_ext_rad)
    h, z, L = c["heights_A"], c["z_eval_A"], c["z_end_A"]
    t_in, t_out = np.tan(theta_in_ext_rad), np.tan(theta_out_ext_rad)
    illuminated = c["W_up_A"] <= h + z[None, :] * t_in + _EPS_A
    visible = c["V_down_A"] <= h + (L - z)[None, :] * t_out + _EPS_A
    return HeightFieldMasks(z_A=z, height_A=h, illuminated=illuminated, visible=visible,
                            usable=illuminated & visible, theta_in_ext_rad=float(theta_in_ext_rad),
                            theta_out_ext_rad=float(theta_out_ext_rad), profile=profile)
