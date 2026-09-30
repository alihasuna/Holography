"""Straight dislocation buried below a free surface, isotropic linear elasticity (half-space).

Premises (labels as in docs/model_assumptions.md, rows D1 to D4):

* Straight, infinitely long dislocation line parallel to the free surface at depth ``d`` below it
  (buried: the line does not meet the surface). ASSUMPTION of the defect model.
* Isotropic linear elasticity with Poisson ratio ``nu`` (silicon is cubic-anisotropic, Zener ratio
  about 1.56; the isotropic field is an approximation). ASSUMPTION.
* Traction-free planar surface, no surface stress, no reconstruction. ASSUMPTION.
* Volterra dislocation: the displacement jumps by ``b`` across a cut. The cut runs from the line
  parallel to the surface towards -s (``s`` defined below), so it never reaches the surface. For a
  perfect dislocation (``b`` an fcc lattice vector) atom positions are unchanged by the choice of cut.

Solution (DERIVED_HERE, verified numerically in tests/test_dislocation.py: traction-free surface,
Burgers-circuit closure, bulk equilibrium):

* Edge part (plane strain, Burgers components b1, b2 in the plane normal to the line): Kolosov-
  Muskhelishvili potentials of the infinite-medium dislocation, phi0 = g log(w - w0),
  psi0 = conj(g) log(w - w0) - g conj(w0)/(w - w0), g = mu b / (pi i (kappa + 1)), kappa = 3 - 4 nu,
  plus the half-plane correction obtained by analytic continuation across the free boundary,
  phi1 = -(w conj-phi0'(w) + conj-psi0(w)), psi1 = -conj-phi0(w) - w phi1'(w), where
  conj-f(w) = conj(f(conj(w))).
* Screw part (anti-plane): u3 = (b3 / 2 pi) (atan2(h + d, s - s0) - atan2(h - d, s - s0)), an image
  screw of opposite rotation sense above the surface; the surface displacement is
  (b3 / pi) atan2(d, s - s0), the Savage-Burford form.

Local frame: e2 = outward surface normal n, e3 = line direction xi (in the surface plane),
e1 = e2 x e3 (right-handed; e1, e2, e3). Coordinates s = r.e1, h = r.n - surface height (h <= 0 in
the crystal). Burgers-vector convention used throughout this repository: b = circuit integral of du
taken counter-clockwise in the (s, h) plane, i.e. right-handed about +xi. The FS/RH convention of
Hirth and Lothe may differ from this by a sign; state the convention with every result.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BuriedDislocation:
    """Straight dislocation parallel to a free surface.

    All vectors are in the slab frame (x = outward normal, y = in-plane, z = beam azimuth), A.

    Parameters
    ----------
    burgers : Burgers vector (A), slab frame.
    line : line direction (unit vector after normalisation), must lie in the surface plane.
    depth : depth of the line below the surface, A (> 0).
    offset : position of the line in the surface plane along e1 = n x xi, A.
    nu : Poisson ratio (isotropic).
    surface_height : height of the free surface on the x axis, A.
    """

    burgers: np.ndarray
    line: np.ndarray
    depth: float
    offset: float
    nu: float
    surface_height: float = 0.0
    normal: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0]))

    def __post_init__(self):
        self.burgers = np.asarray(self.burgers, float)
        self.normal = np.asarray(self.normal, float) / np.linalg.norm(self.normal)
        xi = np.asarray(self.line, float)
        self.line = xi / np.linalg.norm(xi)
        if abs(self.line @ self.normal) > 1e-9:
            raise ValueError("only lines parallel to the surface are supported (buried dislocation)")
        if not self.depth > 0:
            raise ValueError("depth must be positive (line below the surface)")
        if not 0 <= self.nu < 0.5:
            raise ValueError("Poisson ratio must be in [0, 0.5)")
        self.e2 = self.normal
        self.e3 = self.line
        self.e1 = np.cross(self.e2, self.e3)

    # -- components ---------------------------------------------------------------------------
    @property
    def b_local(self) -> np.ndarray:
        """(b1, b2, b3): edge in-plane, edge normal, screw components."""
        return np.array([self.burgers @ self.e1, self.burgers @ self.e2, self.burgers @ self.e3])

    def local_coords(self, r: np.ndarray):
        r = np.asarray(r, float)
        s = r @ self.e1
        h = r @ self.e2 - self.surface_height
        return s, h

    # -- fields -------------------------------------------------------------------------------
    def displacement_local(self, s, h):
        """(u1, u2, u3) at local coordinates; arrays broadcast."""
        s = np.asarray(s, float)
        h = np.asarray(h, float)
        b1, b2, b3 = self.b_local
        kappa = 3 - 4 * self.nu
        w = s + 1j * h
        w0 = self.offset - 1j * self.depth
        w0c = np.conj(w0)
        g = (b1 + 1j * b2) / (np.pi * 1j * (kappa + 1))  # mu = 1 (cancels in displacements)
        gc = np.conj(g)
        with np.errstate(divide="ignore", invalid="ignore"):
            L0 = np.log(w - w0)
            L1 = np.log(w - w0c)
            phi = g * L0 - (gc * (w - w0) / (w - w0c) + g * L1)
            dphi1 = -(gc * (w0 - w0c) / (w - w0c) ** 2 + g / (w - w0c))
            dphi = g / (w - w0) + dphi1
            psi = gc * L0 - g * w0c / (w - w0) - gc * L1 - w * dphi1
            U = (kappa * phi - w * np.conj(dphi) - np.conj(psi)) / 2.0
            u3 = b3 / (2 * np.pi) * (
                np.arctan2(h + self.depth, s - self.offset) - np.arctan2(h - self.depth, s - self.offset)
            )
        return U.real, U.imag, u3

    def displacement(self, r: np.ndarray) -> np.ndarray:
        """Displacement (slab frame, A) at points r of shape (..., 3)."""
        s, h = self.local_coords(r)
        u1, u2, u3 = self.displacement_local(s, h)
        return u1[..., None] * self.e1 + u2[..., None] * self.e2 + u3[..., None] * self.e3


@dataclass
class DefectSet:
    """Superposition of dislocation fields (linear elasticity; valid while the cores do not overlap)."""

    items: list

    def displacement(self, r: np.ndarray) -> np.ndarray:
        r = np.asarray(r, float)
        u = np.zeros(r.shape)
        for d in self.items:
            u = u + d.displacement(r)
        return u


def from_config(entries, nu: float, a_A: float, frame, Ly: float | None = None, n_images: int = 0) -> DefectSet:
    """Build dislocations from config entries.

    Each entry: burgers_over_a (cubic, units of a), line_uvw (cubic), depth_A, position_yz_A (a point
    of the line in the surface plane, slab frame), sign (+1 or -1). With n_images > 0, images at
    +-k Ly along y are added (lines along the beam only), for cells periodic in y. A non-lattice
    Burgers vector is refused: partial dislocations need a stacking-fault model not implemented here.
    """
    from ..geometry import is_fcc_lattice_vector

    items = []
    for e in entries:
        b_over_a = np.asarray(e["burgers_over_a"], float)
        if not is_fcc_lattice_vector(b_over_a):
            raise ValueError(f"Burgers vector {b_over_a.tolist()} a is not a lattice vector (partial?)")
        line = frame.to_slab(e["line_uvw"])
        line = line / np.linalg.norm(line)
        b = float(e["sign"]) * a_A * frame.to_slab(b_over_a)
        y, z = e["position_yz_A"]
        shifts = [0]
        if n_images:
            if abs(abs(line[2]) - 1) > 1e-9:
                raise ValueError("periodic images along y require lines along the beam (z)")
            shifts = range(-n_images, n_images + 1)
        for k in shifts:
            D = BuriedDislocation(burgers=b, line=line, depth=float(e["depth_A"]), offset=0.0, nu=nu)
            D.offset = float(np.array([0.0, y + k * (Ly or 0.0), z]) @ D.e1)
            items.append(D)
    return DefectSet(items)
