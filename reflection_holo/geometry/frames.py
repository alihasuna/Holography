"""Surface frames for cubic crystals (docs/physics_conventions.md, "Crystallographic frame").

Convention (DERIVED_HERE; identical to the calculator and to docs/physics_conventions.md):
    x_hat = outward surface normal (into vacuum), the direction [h,k,l] of the plane (hkl)
    z_hat = beam azimuth [u,v,w] (in the surface plane; the beam is then tilted out of the surface
            by the glancing angle)
    y_hat = z_hat x x_hat, so that x_hat x y_hat = z_hat (right-handed)
The active rotation R has rows (x_hat, y_hat, z_hat): r_slab = R @ r_crystal (cubic axes).
In the cubic system [hkl] is normal to (hkl), so the plane indices give the normal direction.

Example (CFG-A): normal (1,-1,1), azimuth [1,1,0] gives y_hat = [1,-1,-2]/sqrt(6).
Example (CFG-B): normal (0,0,1), azimuth [1,1,0] or [1,0,0] (PROJECT_INPUT item 8: not defaulted).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_TOL = 1e-12


@dataclass(frozen=True)
class SurfaceFrame:
    normal_hkl: tuple[int, int, int]
    azimuth_uvw: tuple[int, int, int]
    R: np.ndarray  # rows x_hat, y_hat, z_hat in cubic crystal coordinates

    @property
    def x_hat(self) -> np.ndarray:
        return self.R[0]

    @property
    def y_hat(self) -> np.ndarray:
        return self.R[1]

    @property
    def z_hat(self) -> np.ndarray:
        return self.R[2]

    def to_slab(self, r_crystal: np.ndarray) -> np.ndarray:
        """Crystal (cubic) coordinates -> slab frame; accepts (3,) or (N, 3)."""
        return np.asarray(r_crystal, float) @ self.R.T

    def to_crystal(self, r_slab: np.ndarray) -> np.ndarray:
        return np.asarray(r_slab, float) @ self.R


def surface_frame(normal_hkl, azimuth_uvw) -> SurfaceFrame:
    """Build the right-handed surface frame; both arguments are required (no defaults).

    Raises ValueError if the azimuth is not perpendicular to the normal (a beam azimuth must lie in
    the surface plane; the inspected repository's "(1,1,-1) facet" with a [110] beam fails here).
    """
    n = np.asarray(normal_hkl, dtype=float)
    b = np.asarray(azimuth_uvw, dtype=float)
    if n.shape != (3,) or b.shape != (3,):
        raise ValueError("normal_hkl and azimuth_uvw must be 3-vectors")
    if not np.any(n) or not np.any(b):
        raise ValueError("normal and azimuth must be non-zero")
    if abs(float(n @ b)) > _TOL:
        raise ValueError(f"azimuth {tuple(azimuth_uvw)} is not in the surface plane of "
                         f"{tuple(normal_hkl)}: normal.azimuth = {float(n @ b):g}")
    x = n / np.linalg.norm(n)
    z = b / np.linalg.norm(b)
    y = np.cross(z, x)
    R = np.vstack([x, y, z])
    if not np.allclose(R @ R.T, np.eye(3), atol=1e-12):      # explicit raises survive python -O
        raise RuntimeError("frame not orthonormal")
    if not abs(np.linalg.det(R) - 1.0) < 1e-12:
        raise RuntimeError("frame not right-handed")
    return SurfaceFrame(tuple(int(v) for v in normal_hkl), tuple(int(v) for v in azimuth_uvw), R)
