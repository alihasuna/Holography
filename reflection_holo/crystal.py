"""Silicon surface cells, terminations, terraces and steps in the slab frame.

Slab frame (docs/physics_conventions.md): x = outward surface normal, y = in-plane
transverse, z = beam azimuth; active rotation r_slab = R r_cubic with the rows of R
the unit vectors x_hat, y_hat, z_hat in cubic coordinates.

Terraces are truncations of ONE continuous lattice (specification section 4.2): a
terrace at level L keeps every atom below the cut c_L = c_0 + L h_unit, where the
cut lies in the gap above a termination unit (a Si(111) bilayer, cut through the
wide 3d/4 gap; or a Si(001) single layer).  An up-step between levels L and L+1 is
then automatically stacking-correct: a lattice translation for Si(111) bilayers and
Si(001) double layers, the diamond 4_1 screw relation for Si(001) single layers.

Frozen phonons: independent Gaussian displacements of every atom in x and y with
the per-axis RMS u_rms (Einstein model, ASSUMPTION, value from the configuration).
Displacements along the beam (z) are not applied because each atom is projected
onto its nominal plane (projection approximation, ASSUMPTION A-proj in
docs/08_fir_simulation_campaign.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd
from typing import Callable

import numpy as np

DIAMOND_BASIS = np.array([
    [0.00, 0.00, 0.00], [0.50, 0.50, 0.00],
    [0.50, 0.00, 0.50], [0.00, 0.50, 0.50],
    [0.25, 0.25, 0.25], [0.75, 0.75, 0.25],
    [0.75, 0.25, 0.75], [0.25, 0.75, 0.75],
])

# Surface frames: (x_hat, y_hat, z_hat) as integer cubic directions.
FRAMES = {
    # CFG-A: (1,-1,1) surface, beam azimuth [110] (docs/physics_conventions.md)
    "si111_110": ((1, -1, 1), (1, -1, -2), (1, 1, 0)),
    # CFG-B: (001) surface, beam azimuth [110]
    "si001_110": ((0, 0, 1), (1, -1, 0), (1, 1, 0)),
    # CFG-B: (001) surface, beam azimuth [100]
    "si001_100": ((0, 0, 1), (0, -1, 0), (1, 0, 0)),
}


def fcc_period(direction, a):
    """Shortest fcc lattice vector length along an integer direction [u,v,w].

    (a/2)(h,k,l) is an fcc translation iff h,k,l are integers with h+k+l even.
    """
    u, v, w = (int(c) for c in direction)
    g = gcd(gcd(abs(u), abs(v)), abs(w))
    u, v, w = u // g, v // g, w // g
    t = 1 if (u + v + w) % 2 == 0 else 2
    return t * 0.5 * a * float(np.sqrt(u * u + v * v + w * w))


@dataclass
class SurfaceCell:
    """Orthorhombic periodic cell of bulk Si in the slab frame."""

    frame: str
    a: float
    R: np.ndarray = field(init=False)
    periods: np.ndarray = field(init=False)
    atoms: np.ndarray = field(init=False)         # (n, 3) slab-frame positions in the cell

    def __post_init__(self):
        dirs = FRAMES[self.frame]
        rows = [np.asarray(d, float) / np.linalg.norm(d) for d in dirs]
        R = np.vstack(rows)
        if not np.allclose(R @ R.T, np.eye(3), atol=1e-12):
            raise ValueError("frame axes are not orthonormal")
        if not np.allclose(np.cross(R[0], R[1]), R[2], atol=1e-12):
            raise ValueError("frame is not right-handed (x_hat x y_hat != z_hat)")
        self.R = R
        self.periods = np.array([fcc_period(d, self.a) for d in dirs])
        self.atoms = self._cell_atoms()

    def _cell_atoms(self):
        P = self.periods
        # cubic cells needed to cover the box: bound by the box diagonal
        nmax = int(np.ceil(np.linalg.norm(P) / self.a)) + 2
        rng = np.arange(-nmax, nmax + 1)
        cells = np.array(np.meshgrid(rng, rng, rng, indexing="ij")).reshape(3, -1).T
        cubic = (cells[:, None, :] + DIAMOND_BASIS[None, :, :]).reshape(-1, 3) * self.a
        slab = cubic @ self.R.T
        tol = 1e-6
        inside = np.all((slab >= -tol) & (slab < P - tol), axis=1)
        pos = slab[inside]
        pos[np.abs(pos) < tol] = 0.0
        expected = 8.0 * np.prod(P) / self.a**3
        if abs(len(pos) - expected) > 1e-6:
            raise RuntimeError(f"cell holds {len(pos)} atoms, expected {expected}")
        order = np.lexsort((pos[:, 1], pos[:, 0], pos[:, 2]))
        return pos[order]

    # ---- planes perpendicular to the beam ---------------------------------
    def plane_z(self, tol=1e-6):
        """Distinct atomic-plane positions along the beam within one period."""
        z = np.sort(self.atoms[:, 2])
        uniq = [z[0]]
        for v in z[1:]:
            if v - uniq[-1] > tol:
                uniq.append(v)
        return np.array(uniq)

    # ---- sheets and termination units along the normal --------------------
    def sheets_x(self, tol=1e-6):
        x = np.sort(self.atoms[:, 0])
        uniq = [x[0]]
        for v in x[1:]:
            if v - uniq[-1] > tol:
                uniq.append(v)
        return np.array(uniq)

    def termination_units(self):
        """Group atomic sheets into termination units.

        Returns (units, h_unit) where units is a list of arrays of sheet heights and
        h_unit the unit repeat along x.  Sheets closer than the largest gap belong to
        one unit (Si(111): bilayers cut through the 3d/4 gap; Si(001): single
        layers, all gaps equal).
        """
        s = self.sheets_x()
        Px = self.periods[0]
        gaps = np.diff(np.concatenate([s, [s[0] + Px]]))
        big = gaps.max()
        if np.allclose(gaps, big, rtol=1e-9):
            units = [np.array([v]) for v in s]
        else:
            cut_after = np.isclose(gaps, big, rtol=1e-6)
            units, cur = [], []
            for v, c in zip(s, cut_after):
                cur.append(v)
                if c:
                    units.append(np.array(cur))
                    cur = []
            if cur:   # wrap-around remainder belongs to the first unit of the next period
                units[0] = np.concatenate([np.array(cur) - Px, units[0]])
        h_unit = Px / len(units)
        return units, h_unit


@dataclass
class TerraceStructure:
    """A semi-infinite Si crystal with terraces, positioned on the simulation grid.

    The level-0 termination has its outermost atomic sheet at x = 0; the vacuum is
    x > 0.  ``level(y, z)`` returns the integer terrace level (in termination
    units) at each atom's (y, z); the atom is kept iff x < cut_0 + level * h_unit.
    Atoms exist down to ``x_bottom`` (inside the bulk-side absorber).
    """

    cell: SurfaceCell
    Ly: float
    x_bottom: float
    level: Callable[[np.ndarray, float], np.ndarray]
    max_level: int = 0
    y_offset: float = 0.0

    def __post_init__(self):
        Py = self.cell.periods[1]
        ny = self.Ly / Py
        if abs(ny - round(ny)) > 1e-6:
            raise ValueError(f"Ly={self.Ly} is not a multiple of the y period {Py}")
        self.n_y = int(round(ny))
        units, h_unit = self.cell.termination_units()
        self.h_unit = h_unit
        Px = self.cell.periods[0]
        # Put the top sheet of one termination unit at x = 0.
        top_sheet = units[-1].max()
        sheets = self.cell.sheets_x()
        # gap above that unit: distance to the next sheet (periodic)
        nxt = sheets[sheets > top_sheet + 1e-6]
        next_sheet = nxt.min() if len(nxt) else sheets.min() + Px
        self.shift_x = -top_sheet
        self.cut0 = 0.5 * (next_sheet - top_sheet)         # mid-gap above x = 0
        self.top_sheet_x = 0.0
        self.plane_z = self.cell.plane_z()
        self.Pz = self.cell.periods[2]
        # Column of atoms per plane type, covering x_bottom .. top of max_level
        x_top = self.cut0 + max(self.max_level, 0) * h_unit + Px
        n_lo = int(np.floor((self.x_bottom - self.shift_x) / Px)) - 1
        n_hi = int(np.ceil((x_top - self.shift_x) / Px)) + 1
        self.columns = []
        A = self.cell.atoms
        for zt in self.plane_z:
            sel = A[np.isclose(A[:, 2], zt, atol=1e-6)]
            xs, ys = [], []
            for i in range(n_lo, n_hi + 1):
                for j in range(self.n_y):
                    xs.append(sel[:, 0] + i * Px + self.shift_x)
                    ys.append(sel[:, 1] + j * Py)
            xs = np.concatenate(xs)
            ys = (np.concatenate(ys) + self.y_offset) % self.Ly
            keep = xs >= self.x_bottom
            self.columns.append((xs[keep], ys[keep]))

    def cut(self, lev):
        return self.cut0 + np.asarray(lev) * self.h_unit

    def plane_atoms(self, plane_index_global, z_plane, rng=None, u_rms=0.0):
        """(x, y) of the atoms of the plane at z_plane (global plane index p).

        Plane type = p mod n_types.  If ``rng`` is given, frozen-phonon x/y
        displacements with per-axis RMS ``u_rms`` are added AFTER truncation (the
        truncation acts on equilibrium positions).
        """
        t = plane_index_global % len(self.plane_z)
        xs, ys = self.columns[t]
        lev = self.level(ys, z_plane)
        keep = xs < self.cut(lev)
        x, y = xs[keep], ys[keep]
        if rng is not None and u_rms > 0:
            x = x + rng.normal(0.0, u_rms, size=x.shape)
            y = y + rng.normal(0.0, u_rms, size=y.shape)
        return x, y

    def plane_positions(self, z_start, z_end, z_offset=0.0):
        """Global plane indices and z positions of all planes in [z_start, z_end)."""
        n_t = len(self.plane_z)
        zt = self.plane_z - self.plane_z[0]
        p0 = int(np.floor((z_start - z_offset) / self.Pz)) - 1
        p1 = int(np.ceil((z_end - z_offset) / self.Pz)) + 1
        idx, zz = [], []
        for m in range(p0, p1 + 1):
            for t in range(n_t):
                z = z_offset + m * self.Pz + zt[t]
                if z_start <= z < z_end:
                    idx.append(m * n_t + t)
                    zz.append(z)
        return np.array(idx, dtype=np.int64), np.array(zz)

    def slice_thickness(self):
        """Thickness associated with each plane (uniform plane spacing assumed)."""
        zt = np.diff(np.concatenate([self.plane_z, [self.plane_z[0] + self.Pz]]))
        if not np.allclose(zt, zt[0], rtol=1e-9):
            raise ValueError("non-uniform plane spacing is not supported")
        return float(zt[0])


# ---- terrace maps ----------------------------------------------------------

def flat(level=0):
    return lambda y, z: np.full(np.shape(y), level, dtype=np.int64)


def steps_parallel(Ly, levels):
    """Terraces side by side across y (step edges parallel to the beam), periodic.

    ``levels`` lists the level of each of len(levels) equal-width strips.
    """
    n = len(levels)
    lev = np.asarray(levels, dtype=np.int64)

    def f(y, z):
        k = np.floor(np.asarray(y) / (Ly / n)).astype(np.int64) % n
        return lev[k]
    return f


def steps_transverse(edges_z, levels):
    """Terraces along the beam (step edges along y): level levels[i] for
    edges_z[i-1] <= z < edges_z[i]; len(levels) = len(edges_z) + 1."""
    edges = np.asarray(edges_z, float)
    lev = np.asarray(levels, dtype=np.int64)

    def f(y, z):
        k = int(np.searchsorted(edges, z, side="right"))
        return np.full(np.shape(y), lev[k], dtype=np.int64)
    return f
