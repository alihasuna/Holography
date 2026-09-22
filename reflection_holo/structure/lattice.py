"""Diamond-lattice primitives for the structure builders (pure numpy, no engine dependency).

Evidence: the 8-atom conventional basis is ``reflection_holo.constants.DIAMOND_BASIS`` (source map
SM02); the lattice parameter is ``reflection_holo.constants.A_SI_A`` (ASSUMPTION B2). The following are
DERIVED_HERE from that basis:

* every diamond site, in units of a/4 on the cubic axes, is an integer vector ``n`` that is either
  all even with ``n1 + n2 + n3 = 0 (mod 4)`` (fcc sublattice) or all odd with
  ``n1 + n2 + n3 = 3 (mod 4)`` (the sublattice shifted by a(1/4,1/4,1/4));
* the nearest-neighbour distance is ``a sqrt(3) / 4``;
* the (001) atomic layers lie at ``z = n3 a/4``; a layer with even ``n3`` belongs to the fcc sublattice
  and its bonds to the layer below project on the ``[1,-1,0]`` axis; a layer with odd ``n3`` has
  back-bonds projecting on ``[1,1,0]``.
"""
from __future__ import annotations

import itertools

import numpy as np

from reflection_holo.constants import DIAMOND_BASIS

# Basis in units of a/4: exact small integers.
BASIS_QUARTER = np.rint(4.0 * DIAMOND_BASIS).astype(np.int64)
if not np.allclose(BASIS_QUARTER, 4.0 * DIAMOND_BASIS, atol=0.0):  # pragma: no cover - guard
    raise RuntimeError("DIAMOND_BASIS is not on the a/4 grid")


def nearest_neighbour_distance_A(a_A: float) -> float:
    """Bulk nearest-neighbour distance a*sqrt(3)/4 (DERIVED_HERE from DIAMOND_BASIS)."""
    return float(a_A) * np.sqrt(3.0) / 4.0


def is_diamond_site_quarter(n: np.ndarray) -> np.ndarray:
    """Site rule on integer a/4 coordinates, shape (..., 3) -> bool (...)."""
    n = np.asarray(n, dtype=np.int64)
    par = n % 2
    s = n.sum(axis=-1) % 4
    all_even = np.all(par == 0, axis=-1)
    all_odd = np.all(par == 1, axis=-1)
    return (all_even & (s == 0)) | (all_odd & (s == 3))


def diamond_sites_quarter(lo_crystal_A: np.ndarray, hi_crystal_A: np.ndarray,
                          a_A: float) -> np.ndarray:
    """Integer a/4 coordinates of all sites of ONE diamond lattice covering a crystal-frame box.

    The lattice is the conventional cubic cell (DIAMOND_BASIS) repeated over the integer cell range
    that covers ``[lo, hi]`` with a one-cell margin; each site is generated exactly once.
    """
    lo = np.floor(np.asarray(lo_crystal_A, float) / a_A).astype(np.int64) - 1
    hi = np.ceil(np.asarray(hi_crystal_A, float) / a_A).astype(np.int64) + 1
    axes = [np.arange(lo[k], hi[k] + 1, dtype=np.int64) for k in range(3)]
    cells = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    n = (4 * cells[:, None, :] + BASIS_QUARTER[None, :, :]).reshape(-1, 3)
    return n


def lattice_site_residuals(positions_crystal_A: np.ndarray, a_A: float):
    """Distance of each position to the nearest a/4 grid point and whether that point is a site.

    Returns ``(residual_A, n_int, is_site)``.
    """
    q = np.asarray(positions_crystal_A, float) * (4.0 / a_A)
    n_int = np.rint(q).astype(np.int64)
    residual_A = np.linalg.norm(q - n_int, axis=-1) * (a_A / 4.0)
    return residual_A, n_int, is_diamond_site_quarter(n_int)


def is_fcc_translation(t_crystal_A: np.ndarray, a_A: float, tol_A: float) -> bool:
    """True if t is a lattice translation of the diamond (fcc) lattice: (a/2)(i,j,k), i+j+k even.

    Same test as ``is_fcc_lattice_vector`` in the calculator, section 2b.
    """
    m = 2.0 * np.asarray(t_crystal_A, float) / a_A
    mi = np.rint(m)
    if np.max(np.abs(m - mi)) * a_A / 2.0 > tol_A:
        return False
    return int(mi.sum()) % 2 == 0


def neighbour_pairs(positions_A: np.ndarray, periodic_lengths_A, cutoff_A: float):
    """All ordered neighbour pairs within ``cutoff_A`` under the given periodic boundaries.

    ``periodic_lengths_A`` is a 3-sequence with ``None`` for a non-periodic axis. Periodic images are
    generated explicitly (as many as the cutoff requires, so periods shorter than twice the cutoff
    are handled), and a cell list with bin size ``cutoff_A`` is searched.

    Returns ``(i, j, d, vec)``: for each ordered pair, the index of the query atom ``i``, the index
    of the partner atom ``j`` (whose periodic image is at ``r_i + vec``), the distance ``d`` and the
    displacement ``vec``. A pair of distinct atoms at the same position appears with ``d = 0``; an
    atom's own periodic image within the cutoff appears with ``i == j``.
    """
    pos = np.asarray(positions_A, dtype=float)
    n_atoms = pos.shape[0]
    if n_atoms == 0:
        e = np.zeros(0, dtype=np.int64)
        return e, e, np.zeros(0), np.zeros((0, 3))
    ranges = []
    lengths = np.zeros(3)
    for ax in range(3):
        L = periodic_lengths_A[ax]
        if L is None:
            ranges.append([0])
        else:
            L = float(L)
            if L <= 0.0:
                raise ValueError("periodic lengths must be positive")
            lengths[ax] = L
            k = int(np.ceil(cutoff_A / L))
            ranges.append(list(range(-k, k + 1)))
    shifts = np.array(list(itertools.product(*ranges)), dtype=float) * lengths
    is_zero = np.all(shifts == 0.0, axis=1)
    img = (pos[None, :, :] + shifts[:, None, :]).reshape(-1, 3)
    img_atom = np.tile(np.arange(n_atoms), len(shifts))
    img_self = np.repeat(is_zero, n_atoms)
    lo = pos.min(axis=0) - cutoff_A
    hi = pos.max(axis=0) + cutoff_A
    keep = np.all((img >= lo) & (img <= hi), axis=1)
    img, img_atom, img_self = img[keep], img_atom[keep], img_self[keep]

    origin = img.min(axis=0)
    b = np.floor((img - origin) / cutoff_A).astype(np.int64)
    nb = b.max(axis=0) + 1
    key = (b[:, 0] * nb[1] + b[:, 1]) * nb[2] + b[:, 2]
    order = np.argsort(key, kind="stable")
    skey = key[order]

    q_img = np.nonzero(img_self)[0]          # one self image per atom, in atom order
    qb = b[q_img]
    I_parts, J_parts = [], []
    for off in itertools.product((-1, 0, 1), repeat=3):
        nbb = qb + np.asarray(off)
        valid = np.all((nbb >= 0) & (nbb < nb), axis=1)
        nkey = (nbb[:, 0] * nb[1] + nbb[:, 1]) * nb[2] + nbb[:, 2]
        start = np.searchsorted(skey, nkey, side="left")
        end = np.searchsorted(skey, nkey, side="right")
        cnt = np.where(valid, end - start, 0)
        tot = int(cnt.sum())
        if tot == 0:
            continue
        qi = np.repeat(np.arange(len(q_img)), cnt)
        offs = np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        cj = order[np.repeat(start, cnt) + offs]
        I_parts.append(qi)
        J_parts.append(cj)
    if not I_parts:
        e = np.zeros(0, dtype=np.int64)
        return e, e, np.zeros(0), np.zeros((0, 3))
    qi = np.concatenate(I_parts)
    cj = np.concatenate(J_parts)
    qimg = q_img[qi]
    vec = img[cj] - img[qimg]
    d = np.linalg.norm(vec, axis=1)
    m = (d < cutoff_A) & (cj != qimg)
    return img_atom[qimg][m], img_atom[cj][m], d[m], vec[m]
