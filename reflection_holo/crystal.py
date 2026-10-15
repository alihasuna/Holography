"""Silicon slab builder in the slab frame (x = outward normal, y = in-plane, z = beam azimuth).

The slab is periodic in y and z with lattice-translation periods, bulk-terminated (ASSUMPTION B3),
and truncated at a chosen depth on the bulk side (the multislice kernel places an absorber there).
"""

from __future__ import annotations

import itertools

import numpy as np

from .geometry import DIAMOND_BASIS, SlabFrame


def lattice_period(frame: SlabFrame, uvw, a_A: float) -> float:
    """Length of the shortest fcc translation along the cubic direction uvw (A)."""
    v = np.asarray(uvw, float)
    for m in (0.5, 1.0, 2.0):  # a/2 [uvw] is a lattice vector if the entries have an even sum
        t = 2 * m * v
        if np.allclose(t, np.round(t)) and int(round(t.sum())) % 2 == 0:
            return m * a_A * float(np.linalg.norm(v))
    raise ValueError(f"no short lattice translation along {uvw}")


def build_slab(frame: SlabFrame, a_A: float, n_y: int, depth_A: float, n_z: int = 1):
    """Atoms of a slab, top bilayer outermost atom at x = 0, down to x >= -depth_A.

    Returns positions (N, 3) in A in the slab frame and the periods (Ly, Lz).
    y in [0, Ly) with Ly = n_y * (y-period); z in [0, Lz) with Lz = n_z * (z-period).
    """
    py = lattice_period(frame, frame.y_uvw, a_A)
    pz = lattice_period(frame, frame.beam_uvw, a_A)
    Ly, Lz = n_y * py, n_z * pz
    R = frame.R
    # cubic-cell index range covering the slab box
    corners = np.array(list(itertools.product([-depth_A - 2 * a_A, 2 * a_A], [0, Ly], [0, Lz])))
    cub = corners @ R  # slab -> cubic (R orthonormal)
    lo = np.floor(cub.min(0) / a_A) - 1
    hi = np.ceil(cub.max(0) / a_A) + 1
    ijk = np.stack(np.meshgrid(*[np.arange(l, h + 1) for l, h in zip(lo, hi)], indexing="ij"), -1).reshape(-1, 3)
    pos_cub = (ijk[:, None, :] + DIAMOND_BASIS[None, :, :]).reshape(-1, 3) * a_A
    pos = pos_cub @ R.T
    eps = 1e-6
    keep = (pos[:, 1] >= -eps) & (pos[:, 1] < Ly - eps) & (pos[:, 2] >= -eps) & (pos[:, 2] < Lz - eps)
    pos = pos[keep]
    for ax, L in ((1, Ly), (2, Lz)):
        pos[:, ax] = np.mod(pos[:, ax], L)
        pos[pos[:, ax] > L - 1e-6, ax] = 0.0

    # bulk termination: find the top of a bilayer (pair of layers closer than half the spacing)
    levels = np.unique(np.round(pos[:, 0], 4))[::-1]
    gaps = -np.diff(levels)
    x_top = None
    if np.ptp(gaps) < 1e-3:  # equally spaced layers, e.g. Si(001): any layer is a termination
        x_top = levels[levels < 0.5 * a_A][0]
    for i in range(len(levels) - 1):
        if x_top is not None:
            break
        if levels[i] < 0.5 * a_A and gaps[i] < 0.5 * gaps.max():
            x_top = levels[i]
    if x_top is None:
        raise RuntimeError("could not identify a bilayer termination")
    pos[:, 0] -= x_top
    pos = pos[(pos[:, 0] <= 1e-3) & (pos[:, 0] >= -depth_A)]  # x_top is rounded to 1e-4 A
    pos[:, 0] -= pos[np.abs(pos[:, 0]) < 1e-3, 0].mean()  # top layer exactly at x = 0
    return pos, Ly, Lz


def layer_depths(positions: np.ndarray, decimals: int = 4) -> np.ndarray:
    """Unique atomic-layer heights (x), descending."""
    return np.unique(np.round(positions[:, 0], decimals))[::-1]
