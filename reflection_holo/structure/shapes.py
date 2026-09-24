"""Surface feature shapes shared by the atomistic builder and the geometric engine (orchestrator).

Slab frame (reflection_holo.geometry.frames): x = outward surface normal, y = in-plane direction
perpendicular to the beam, z = beam azimuth. x_rel = x - x_surface, where x_surface is the height of
the flat surface's top atomic layer. All lengths in A. Every parameter is REQUIRED: the feature
geometry is PROJECT_INPUT item 13 (docs/06); a demo value must be a registered stand-in.

HalfTorus: a torus lying flat on the surface (symmetry axis along the normal), centred at
(y_c, z_c) in the surface plane, major radius R, minor radius r (r < R), cut by the surface plane.
  kind "trench": lattice sites with x_rel <= 0 and (rho - R)^2 + x_rel^2 < r^2 are REMOVED
                 (a circular groove of semicircular cross-section);
  kind "ridge":  sites of the SAME continuous lattice with x_rel > 0 and (rho - R)^2 + x_rel^2 < r^2
                 are ADDED above the surface (a circular ridge);
with rho = sqrt((y - y_c)^2 + (z - z_c)^2).

On the Si(001) lattice the atomic layers sit at x_rel = n a/4 (n integer, n = 0 the original top
layer), so the feature becomes a ring of a/4 terraces. layer_height_A gives the IDEAL top-layer height
per surface point from that rule (DERIVED_HERE):
  s = sqrt(r^2 - (rho - R)^2) inside the ring (|rho - R| < r), else no change;
  ridge: top layer n_top = ceil(s / (a/4)) - 1 (largest n with n a/4 < s);
  trench: layers 0 .. -m removed with m = ceil(s / (a/4)) - 1, so n_top = -ceil(s / (a/4));
  height = n_top a/4. The continuous profile is continuous_height_A.
The atomistic builder must reproduce layer_height_A on its built atoms (to be asserted there).

BuriedTorus (agent T3, Ali's buried-cavity study, 2026-09-24): a FULL torus-shaped EMPTY cavity
inside the crystal under an intact cap; the flat surface above it is untouched. The ring lies in the
surface plane's orientation (symmetry axis along the normal) centred at (y_c, z_c); its tube centre
line is the circle rho = R at the depth x_rel = x_c = -(cap + r) below the top atomic plane of the
flat surface (x_rel = 0), so the top of the void is at x_rel = -cap and its bottom at
x_rel = -(cap + 2 r). Lattice sites with distance to the tube centre line < r, i.e.
(rho - R)^2 + (x_rel - x_c)^2 < r^2, are REMOVED (kind "buried_void"); nothing is added and no site
is moved. Every removed site has x_rel < -cap strictly, so every atomic layer with x_rel >= -cap (the
cap and the flat surface) is untouched. The top atomic layer is flat everywhere:
layer_height_A = continuous_height_A = 0 (a surface-height model, such as the geometric engine,
therefore sees no feature at all). Volume 2 pi^2 R r^2, surface 4 pi^2 R r (DERIVED_HERE, Pappus).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_KINDS = ("trench", "ridge")


@dataclass(frozen=True)
class HalfTorus:
    center_y_A: float
    center_z_A: float
    major_radius_A: float
    minor_radius_A: float
    kind: str
    label: str        # evidence label of the geometry, e.g. "ASSUMPTION" (demo stand-in) or "PROJECT_INPUT"
    source: str       # where the numbers come from (assumption row, or supplier and date)

    def __post_init__(self):
        if self.kind not in _KINDS:
            raise ValueError(f"HalfTorus.kind must be one of {_KINDS}, got {self.kind!r}")
        if not (np.isfinite(self.major_radius_A) and np.isfinite(self.minor_radius_A)):
            raise ValueError("HalfTorus radii must be finite")
        if not (0.0 < self.minor_radius_A < self.major_radius_A):
            raise ValueError("HalfTorus needs 0 < minor_radius_A < major_radius_A")
        if not self.label or not self.source:
            raise ValueError("HalfTorus needs an evidence label and a source (PROJECT_INPUT item 13)")

    def _rho(self, y, z):
        return np.hypot(np.asarray(y, float) - self.center_y_A, np.asarray(z, float) - self.center_z_A)

    def half_thickness_A(self, y, z):
        """s(y, z) = sqrt(r^2 - (rho - R)^2) inside the ring footprint, 0 outside."""
        d = self._rho(y, z) - self.major_radius_A
        return np.sqrt(np.clip(self.minor_radius_A ** 2 - d ** 2, 0.0, None))

    def contains(self, x_rel, y, z):
        """True for lattice sites that the feature removes (trench) or adds (ridge)."""
        x_rel = np.asarray(x_rel, float)
        d = self._rho(y, z) - self.major_radius_A
        inside = d ** 2 + x_rel ** 2 < self.minor_radius_A ** 2
        return inside & (x_rel <= 0.0) if self.kind == "trench" else inside & (x_rel > 0.0)

    def continuous_height_A(self, y, z):
        s = self.half_thickness_A(y, z)
        return s if self.kind == "ridge" else -s

    def layer_height_A(self, y, z, *, layer_spacing_A: float):
        """Ideal top-atomic-layer height (quantised to layer_spacing_A, i.e. a/4 on Si(001))."""
        if not (layer_spacing_A > 0.0):
            raise ValueError("layer_spacing_A must be positive")
        s = self.half_thickness_A(y, z)
        k = np.ceil(s / layer_spacing_A)              # 0 outside the footprint
        n_top = np.where(s > 0.0, (k - 1.0) if self.kind == "ridge" else -k, 0.0)
        return n_top * layer_spacing_A


BURIED_KIND = "buried_void"


@dataclass(frozen=True)
class BuriedTorus:
    """A full torus-shaped empty cavity under an intact cap (module docstring). Every field is
    required (no defaults): centre (y_c, z_c) in the surface plane, major radius R, tube (minor)
    radius r < R, cap = thickness of intact crystal between the top atomic plane of the flat surface
    and the top of the void (> 0), evidence label and source (PROJECT_INPUT item 13; a demo value
    must be a registered stand-in, e.g. "ASSUMPTION B42")."""
    center_y_A: float
    center_z_A: float
    major_radius_A: float
    minor_radius_A: float
    cap_A: float
    label: str
    source: str

    def __post_init__(self):
        vals = (self.center_y_A, self.center_z_A, self.major_radius_A, self.minor_radius_A,
                self.cap_A)
        if not all(isinstance(v, (int, float, np.floating, np.integer))
                   and not isinstance(v, bool) and np.isfinite(v) for v in vals):
            raise ValueError("BuriedTorus centre, radii and cap must be finite numbers")
        if not (0.0 < self.minor_radius_A < self.major_radius_A):
            raise ValueError("BuriedTorus needs 0 < minor_radius_A < major_radius_A")
        if not (self.cap_A > 0.0):
            raise ValueError("BuriedTorus needs cap_A > 0 (intact crystal above the void; a void "
                             "reaching the surface is not a buried void)")
        if not self.label or not self.source:
            raise ValueError("BuriedTorus needs an evidence label and a source (PROJECT_INPUT "
                             "item 13)")

    @property
    def kind(self) -> str:
        return BURIED_KIND

    @property
    def tube_centre_x_rel_A(self) -> float:
        """x_rel of the tube centre line: -(cap + r)."""
        return -(float(self.cap_A) + float(self.minor_radius_A))

    @property
    def void_top_x_rel_A(self) -> float:
        return -float(self.cap_A)

    @property
    def void_bottom_x_rel_A(self) -> float:
        return -(float(self.cap_A) + 2.0 * float(self.minor_radius_A))

    @property
    def volume_A3(self) -> float:
        return float(2.0 * np.pi ** 2 * self.major_radius_A * self.minor_radius_A ** 2)

    @property
    def surface_A2(self) -> float:
        return float(4.0 * np.pi ** 2 * self.major_radius_A * self.minor_radius_A)

    def _rho(self, y, z):
        return np.hypot(np.asarray(y, float) - self.center_y_A, np.asarray(z, float) - self.center_z_A)

    def distance_to_tube_centre_line_A(self, x_rel, y, z):
        """Distance of (x_rel, y, z) from the tube centre line (the circle rho = R, x_rel = x_c)."""
        d = self._rho(y, z) - self.major_radius_A
        return np.hypot(d, np.asarray(x_rel, float) - self.tube_centre_x_rel_A)

    def contains(self, x_rel, y, z):
        """True for lattice sites inside the void (removed): distance to the tube centre line < r."""
        d = self._rho(y, z) - self.major_radius_A
        dx = np.asarray(x_rel, float) - self.tube_centre_x_rel_A
        return d ** 2 + dx ** 2 < self.minor_radius_A ** 2

    def footprint_half_width_A(self, y, z):
        """s(y, z) = sqrt(r^2 - (rho - R)^2) inside the projected annulus |rho - R| < r, else 0:
        the half height of the void's vertical section at (y, z)."""
        d = self._rho(y, z) - self.major_radius_A
        return np.sqrt(np.clip(self.minor_radius_A ** 2 - d ** 2, 0.0, None))

    def continuous_height_A(self, y, z):
        """Height of the surface relative to the flat surface: 0 everywhere (buried feature)."""
        return np.zeros(np.broadcast(np.asarray(y, float), np.asarray(z, float)).shape)

    def layer_height_A(self, y, z, *, layer_spacing_A: float):
        """Ideal top-atomic-layer height: 0 everywhere (the cap and the surface are intact)."""
        if not (layer_spacing_A > 0.0):
            raise ValueError("layer_spacing_A must be positive")
        return self.continuous_height_A(y, z)
