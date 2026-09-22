"""Structure assertions (spec section 4.2), run inside the builders and tested one by one.

Each check raises :class:`StructureAssertionError` (an ``AssertionError`` subclass raised explicitly,
so the checks survive ``python -O``). Tolerances are stated here and recorded in the structure
metadata; they are never loosened to make a structure pass.

(a) ``assert_on_lattice_sites``: every atom on a bulk diamond site of ONE lattice.
(b) ``assert_half_open_window`` and ``assert_no_duplicates_and_count``: half-open periodic window
    with tolerance ``WINDOW_TOL_A``, no two atoms closer than ``DUPLICATE_DIST_A`` under the periodic
    boundaries, and the atom count equal to the count expected for the occupied volume (the fix for
    defect A-M7 of docs/01_repository_audit.md section 3.3).
(c) ``assert_min_distance_and_coordination``: minimum interatomic distance equals a*sqrt(3)/4
    within ``POSITION_TOL_A``, and atoms of the bulk interior are 4-coordinated across the
    periodic boundaries.
(d), (e) live with the staircase in ``si001.py`` (``validate_staircase``, ``assert_step_heights``)
(f) ``si001.find_terrace_relations`` / ``assert_terrace_relation``.
(g) ``assert_frame``: right-handed orthonormal frame, outward normal as x, beam azimuth in the
    surface plane.
"""
from __future__ import annotations

import numpy as np

from reflection_holo.geometry.frames import SurfaceFrame

from .lattice import lattice_site_residuals, nearest_neighbour_distance_A, neighbour_pairs

# Stated tolerances (angstrom). Positions are exact lattice sites up to float rounding (~1e-13 A at
# 1000 A), so these are far below any physical displacement (the thermal RMS is 0.076 A).
POSITION_TOL_A = 1e-6        # lattice-site residual, distances, step heights
WINDOW_TOL_A = 1e-6          # half-open window [lo - tol, hi - tol)
DUPLICATE_DIST_A = 0.5       # two atoms closer than this under the PBC are duplicates (d_nn = 2.35 A)
FRAME_TOL = 1e-12            # orthonormality / handedness of the frame


class StructureAssertionError(AssertionError):
    """A structure failed one of the spec 4.2 assertions."""


def _fail(msg: str) -> None:
    raise StructureAssertionError(msg)


# --- (g) frame ----------------------------------------------------------------------------------
def assert_frame(frame: SurfaceFrame, normal_hkl=(0, 0, 1)) -> None:
    R = np.asarray(frame.R, float)
    if not np.allclose(R @ R.T, np.eye(3), atol=FRAME_TOL):
        _fail("(g) frame rows are not orthonormal")
    det = float(np.linalg.det(R))
    if abs(det - 1.0) > FRAME_TOL:
        _fail(f"(g) frame is not right-handed: det = {det:.15g}")
    if not np.allclose(np.cross(frame.x_hat, frame.y_hat), frame.z_hat, atol=FRAME_TOL):
        _fail("(g) x_hat x y_hat != z_hat")
    n = np.asarray(normal_hkl, float)
    n = n / np.linalg.norm(n)
    if not np.allclose(frame.x_hat, n, atol=FRAME_TOL):
        _fail(f"(g) x_hat {frame.x_hat} is not the outward normal {tuple(normal_hkl)}")
    az = np.asarray(frame.azimuth_uvw, float)
    if abs(float(az @ n)) > FRAME_TOL:
        _fail(f"(g) beam azimuth {frame.azimuth_uvw} is not in the surface plane")
    if not np.allclose(frame.z_hat, az / np.linalg.norm(az), atol=FRAME_TOL):
        _fail("(g) z_hat is not the beam azimuth")
    if abs(float(frame.z_hat @ frame.x_hat)) > FRAME_TOL:
        _fail("(g) beam azimuth has a component along the normal")


# --- (a) lattice sites ---------------------------------------------------------------------------
def assert_on_lattice_sites(positions_slab_A: np.ndarray, frame: SurfaceFrame,
                            crystal_origin_slab_A: np.ndarray, a_A: float,
                            tol_A: float = POSITION_TOL_A) -> None:
    """Every atom lies on a site of the single diamond lattice whose origin sits at
    ``crystal_origin_slab_A`` in the slab frame, within ``tol_A``."""
    r_c = frame.to_crystal(np.asarray(positions_slab_A, float) - np.asarray(crystal_origin_slab_A))
    res, n_int, is_site = lattice_site_residuals(r_c, a_A)
    bad = np.nonzero(res > tol_A)[0]
    if bad.size:
        i = int(bad[0])
        _fail(f"(a) {bad.size} atom(s) off the a/4 grid of the bulk lattice; atom {i} is "
              f"{res[i]:.3e} A from the nearest grid point (tolerance {tol_A:g} A)")
    bad = np.nonzero(~is_site)[0]
    if bad.size:
        i = int(bad[0])
        _fail(f"(a) {bad.size} atom(s) on a/4 grid points that are not diamond sites; atom {i} "
              f"at a/4 x {n_int[i].tolist()}")


# --- (b) window, duplicates and count ------------------------------------------------------------
def assert_half_open_window(coord_A: np.ndarray, length_A: float, axis_name: str,
                            tol_A: float = WINDOW_TOL_A) -> None:
    u = np.asarray(coord_A, float)
    bad = (u < -tol_A) | (u >= length_A - tol_A)
    if np.any(bad):
        i = int(np.nonzero(bad)[0][0])
        _fail(f"(b) {int(bad.sum())} atom(s) outside the half-open window [0, {length_A:.6f}) "
              f"along {axis_name} (tolerance {tol_A:g} A); first at {u[i]:.9f} A")


def assert_no_duplicates_and_count(positions_A: np.ndarray, periodic_lengths_A,
                                   expected_count: int,
                                   dup_dist_A: float = DUPLICATE_DIST_A) -> None:
    pos = np.asarray(positions_A, float)
    i, j, d, _ = neighbour_pairs(pos, periodic_lengths_A, dup_dist_A)
    if d.size:
        k = int(np.argmin(d))
        kind = "its own periodic image" if i[k] == j[k] else f"atom {int(j[k])}"
        _fail(f"(b) duplicate atoms under the periodic boundaries: {d.size // 2 or 1} pair(s) "
              f"closer than {dup_dist_A} A; atom {int(i[k])} coincides with {kind} at "
              f"{d[k]:.3e} A")
    if pos.shape[0] != int(expected_count):
        _fail(f"(b) atom count {pos.shape[0]} != expected {int(expected_count)} for the occupied "
              f"volume")


# --- (c) minimum distance and coordination -------------------------------------------------------
def assert_min_distance_and_coordination(positions_A: np.ndarray, periodic_lengths_A,
                                         a_A: float, interior_mask: np.ndarray | None,
                                         tol_A: float = POSITION_TOL_A):
    """Minimum interatomic distance equals a*sqrt(3)/4 within tol_A; every atom flagged by
    ``interior_mask`` has exactly 4 neighbours at that distance under the periodic boundaries.
    Returns the neighbour pairs (i, j, d, vec) within 1.05 d_nn for reuse."""
    d_nn = nearest_neighbour_distance_A(a_A)
    pos = np.asarray(positions_A, float)
    i, j, d, vec = neighbour_pairs(pos, periodic_lengths_A, 1.05 * d_nn)
    if d.size == 0:
        _fail("(c) no interatomic distance below 1.05 d_nn: no bonded pair found")
    dmin = float(d.min())
    if abs(dmin - d_nn) > tol_A:
        _fail(f"(c) minimum interatomic distance {dmin:.9f} A != a*sqrt(3)/4 = {d_nn:.9f} A "
              f"(tolerance {tol_A:g} A)")
    off = np.abs(d - d_nn) > tol_A
    if np.any(off):
        _fail(f"(c) {int(off.sum())} pair distance(s) within 1.05 d_nn differ from d_nn")
    if interior_mask is not None:
        coord = np.bincount(i, minlength=pos.shape[0])
        bad = np.nonzero(np.asarray(interior_mask) & (coord != 4))[0]
        if bad.size:
            k = int(bad[0])
            _fail(f"(c) {bad.size} interior atom(s) not 4-coordinated under the periodic "
                  f"boundaries; atom {k} has {int(coord[k])} neighbours")
    return i, j, d, vec
