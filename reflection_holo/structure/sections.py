"""Multi-section samples: side-by-side strips of different terrace heights and buried defects.

The strips run parallel to the beam (along z), so every strip is imaged side by side in the same
dark-field image and step edges cast no shadow. All strips are truncations of ONE continuous
lattice (docs/05 section 4.2); a strip raised by n atomic layers differs from the reference by the
lattice translation n * (layer spacing) along the normal only when n * spacing is a lattice
translation (for Si(001): n a multiple of 2; n = 1 or 3 gives 4_1-screw-related terraces).

Dislocations with a net Burgers vector in a y-periodic cell (for example ONE edge dislocation with
its extra half-plane reaching the surface) cannot conserve the atom count: the half-plane adds a
plane of atoms. The builder follows the Atomsk-type construction: lattice sites are generated over
the cell plus a margin on both sides, displaced by the non-periodic half-space field, corrected by a
small linear ramp so that the mismatch across the periodic seam is exactly a lattice vector, then
wrapped into the cell with coincident atoms merged. The missing or surplus plane is thereby inserted
or removed at the seam, where the crystal is perfect again. The ramp strain is reported.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from ..crystal import build_slab, lattice_period


@dataclass
class SectionSample:
    positions: np.ndarray  # (N, 3) A, slab frame
    section: np.ndarray  # (N,) section index of each atom (by its final y)
    displacement: np.ndarray  # (N, 3) A, elastic displacement applied (zero without defects)
    Ly: float
    Lz: float
    boundaries: np.ndarray  # y of the section boundaries, A (len n_sections + 1)
    heights: np.ndarray  # terrace height of each section, A
    info: dict
    u_func: object = None  # r (..., 3) -> elastic displacement applied to the atoms (same field)


def build_sections(frame, a_A, periods, raise_layers, depth_A, defects=None, margin_periods=3,
                   merge_tol_A=0.5, seam_y=None):
    """Side-by-side strips along y.

    periods : number of y lattice periods in each section.
    raise_layers : atomic layers added on top of each section (0 = reference height).
    depth_A : crystal depth below the reference surface (x = 0).
    defects : object with .displacement(r) and .items (BuriedDislocation) or None.
    seam_y : y where the periodic seam is anchored (plane insertion and ramp). Default: the point
        opposite the first dislocation line (Ly/2 away), where the normal component of the seam
        mismatch vanishes by symmetry, so the ramp does not tilt the surface.
    """
    periods = list(periods)
    raise_layers = list(raise_layers)
    py = lattice_period(frame, frame.y_uvw, a_A)
    n_tot = sum(periods)
    Ly = n_tot * py
    boundaries = np.concatenate([[0.0], np.cumsum(periods) * py])

    # layer spacing along the normal
    probe, _, _ = build_slab(frame, a_A, 1, 3 * a_A)
    lev = np.unique(np.round(probe[:, 0], 4))
    gaps = np.diff(lev)
    if np.ptp(gaps) > 1e-3:
        raise ValueError("sections are implemented for equally spaced layers (e.g. Si(001))")
    d_layer = float(gaps.mean())
    heights = np.array(raise_layers) * d_layer
    h_max = float(heights.max())

    m = int(margin_periods)
    if seam_y is None:
        seam_y = 0.0
        if defects is not None and len(defects.items):
            d0 = defects.items[0]
            y_line = -d0.offset if d0.e1[1] < 0 else d0.offset  # lines along the beam: e1 = -+y
            seam_y = np.mod(y_line + Ly / 2, Ly)
    Y0 = float(np.round(seam_y / py) * py)  # sites must stay on the lattice
    sites, _, Lz = build_slab(frame, a_A, n_tot + 2 * m, depth_A + h_max)
    sites[:, 0] += h_max
    sites[:, 1] += Y0 - m * py
    y_in = np.mod(sites[:, 1], Ly)
    sec = np.clip(np.searchsorted(boundaries, y_in, side="right") - 1, 0, len(periods) - 1)
    keep = (sites[:, 0] <= heights[sec] + 1e-3) & (sites[:, 0] >= -depth_A - 1e-3)
    sites = sites[keep]

    info = {"layer_spacing_A": d_layer, "margin_periods": m}
    u = np.zeros_like(sites)
    if defects is not None and len(defects.items):
        u = defects.displacement(sites)
        B = np.sum([d.burgers for d in defects.items], axis=0)
        layers = np.unique(np.round(sites[:, 0], 3))
        r0 = np.stack([layers, np.full_like(layers, Y0), np.zeros_like(layers)], -1)
        r1 = r0 + np.array([0.0, Ly, 0.0])
        mism = defects.displacement(r0) - defects.displacement(r1)
        if np.linalg.norm(B) > 1e-9:
            k = np.round(mism @ B / (B @ B))
            resid = mism - k[:, None] * B
        else:
            resid = mism
        idx = np.searchsorted(layers, np.round(sites[:, 0], 3))
        u = u + resid[idx] * ((sites[:, 1] - Y0) / Ly)[:, None]
        # remove the rigid translation so the middle of section 0 (the reference) sits at its
        # undisplaced position; a rigid shift changes no observable phase difference
        r_ref = np.array([[0.0, 0.5 * (boundaries[0] + boundaries[1]), 0.0]])
        y_ref = Y0 + np.mod(r_ref[0, 1] - Y0, Ly)
        u_ref = defects.displacement(r_ref)[0] + resid[np.argmin(np.abs(layers))] * (y_ref - Y0) / Ly
        if y_ref != r_ref[0, 1]:
            u_ref = defects.displacement(r_ref + [0, y_ref - r_ref[0, 1], 0])[0] + \
                resid[np.argmin(np.abs(layers))] * (y_ref - Y0) / Ly
        if np.linalg.norm(B) > 1e-9:  # a shift by a lattice vector is not a rigid shift to remove
            u_ref = u_ref - B * np.round(u_ref @ B / (B @ B))
        u = u - u_ref
        info["rigid_shift_removed_A"] = u_ref.tolist()
        info["net_burgers_A"] = B.tolist()
        info["seam_y_A"] = Y0
        info["seam_ramp_residual_surface_A"] = resid[np.argmin(np.abs(layers))].tolist()
        info["seam_ramp_max_strain"] = float(np.abs(resid).max() / Ly)

        def u_func(r, _d=defects, _L=layers, _R=resid, _Y0=Y0, _u0=u_ref):
            r = np.array(r, float)
            r[..., 1] = _Y0 + np.mod(r[..., 1] - _Y0, Ly)
            ramp = np.stack([np.interp(r[..., 0], _L, _R[:, k]) for k in range(3)], -1)
            return _d.displacement(r) + ramp * ((r[..., 1] - _Y0) / Ly)[..., None] - _u0
    else:
        def u_func(r):
            return np.zeros(np.shape(r))

    pos = sites + u
    pos[:, 1] = np.mod(pos[:, 1], Ly)
    pos[:, 2] = np.mod(pos[:, 2], Lz)
    pos[pos[:, 1] >= Ly - 1e-9, 1] = 0.0
    pos[pos[:, 2] >= Lz - 1e-9, 2] = 0.0

    # merge coincident atoms (periodic in y and z)
    shift = pos[:, 0].min() - 1.0
    tree = cKDTree(pos - np.array([shift, 0, 0]), boxsize=[1e9, Ly, Lz])
    pairs = tree.query_pairs(merge_tol_A, output_type="ndarray")
    drop = np.zeros(len(pos), bool)
    for i, j in pairs:
        if not drop[i]:
            drop[j] = True
    pos, u = pos[~drop], u[~drop]
    info["merged_atoms"] = int(drop.sum())
    section = np.clip(np.searchsorted(boundaries, pos[:, 1], side="right") - 1, 0, len(periods) - 1)
    return SectionSample(pos, section, u, Ly, Lz, boundaries, heights, info, u_func)


def nearest_neighbour_distances(sample: SectionSample):
    shift = sample.positions[:, 0].min() - 1.0
    tree = cKDTree(sample.positions - np.array([shift, 0, 0]), boxsize=[1e9, sample.Ly, sample.Lz])
    d, _ = tree.query(sample.positions - np.array([shift, 0, 0]), k=5)
    return d[:, 1:]
