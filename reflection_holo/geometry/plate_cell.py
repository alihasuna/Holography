"""Illumination fractions of a free-standing plate cell (the inspected repository's default
multislice cell), behind the calculator's checks T17 to T19.

Source map SM09: geometry DERIVED_HERE; the cell parameters are the inspected repository's defaults
(PROJECT_INPUT (repository defaults), commit 6694959, si110_cleave_slab_generator.py). They are not
stored here: every parameter is a required argument, and the caller states them. Ported from
tools/reflection_step_phase_calculator.py section 8.

Frame (CFG-A, reflection_holo.geometry.frames): x along the outward normal (1,-1,1) with period
a sqrt(3); y along [1,-1,-2] with period a sqrt(1.5); z along the beam azimuth [110] with period
a / sqrt(2). The plate has x_vac of vacuum on each side along x and z_vac on each side along z.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PlateCellGeometry:
    """Result of plate_cell_geometry (source map SM09, evidence DERIVED_HERE)."""
    Lx_si_A: float          # plate thickness along the normal
    Ly_A: float
    Lz_si_A: float          # crystal length along the beam
    Lx_A: float             # supercell along the normal (Lx_si + 2 x_vac)
    Lz_A: float             # supercell along the beam (Lz_si + 2 z_vac)
    theta_ext_rad: float
    top_gap_fraction: float     # Lz_si tan(theta) / x_vac: part of the top gap reaching the surface
    end_face_fraction: float    # Lx_si / Lx: incident wave entering the front end face
    rise_over_cell_A: float     # Lz tan(theta): reflected-beam rise over the whole cell
    no_wraparound: bool         # rise_over_cell < x_vac (the wrap-around assertion)


def plate_cell_geometry(*, a_A: float, n_x_si: int, n_y: int, n_z_si: int, x_vac_A: float,
                        z_vac_A: float, theta_ext_rad: float) -> PlateCellGeometry:
    """Fractions of T17 (top-gap illumination reaching the surface), T18 (end-face entry) and T19
    (reflected-beam rise over the cell) for a plate cell at glancing angle theta_ext.

    All arguments are required keywords. Source map SM09, evidence DERIVED_HERE (geometry).
    """
    for name, v in (("a_A", a_A), ("x_vac_A", x_vac_A), ("theta_ext_rad", theta_ext_rad)):
        if not v > 0:
            raise ValueError(f"{name} must be positive, got {v!r}")
    px = a_A * np.sqrt(3.0)
    py = a_A * np.sqrt(1.5)
    pz = a_A / np.sqrt(2.0)
    Lx_si, Ly, Lz_si = n_x_si * px, n_y * py, n_z_si * pz
    Lx, Lz = Lx_si + 2.0 * x_vac_A, Lz_si + 2.0 * z_vac_A
    tn = np.tan(theta_ext_rad)
    rise = Lz * tn
    return PlateCellGeometry(
        Lx_si_A=float(Lx_si), Ly_A=float(Ly), Lz_si_A=float(Lz_si), Lx_A=float(Lx),
        Lz_A=float(Lz), theta_ext_rad=float(theta_ext_rad),
        top_gap_fraction=float(Lz_si * tn / x_vac_A), end_face_fraction=float(Lx_si / Lx),
        rise_over_cell_A=float(rise), no_wraparound=bool(rise < x_vac_A))
