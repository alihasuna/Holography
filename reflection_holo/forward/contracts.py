"""Interface contract between the reflection forward model and the pipeline (orchestrator, Phase 3).

Frame: the slab frame of reflection_holo.geometry.frames (x = outward surface normal, y = in-plane
direction perpendicular to the beam azimuth, z = beam azimuth). Slices are perpendicular to z; the
wave is sampled on an (x, y) grid; the beam enters at z = 0 travelling towards +z and descending
towards the surface (k_x < 0 on entry). Lengths in A, angles in rad, energy in keV.
Convention: exp(+i k.r), numpy FFT sign (docs/physics_conventions.md).

Nothing here may default a PROJECT_INPUT; every such argument is required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ReflectionCell:
    """Atoms and box of a reflection calculation, in the slab frame.

    atoms_xyz_A: (N, 3) positions; Z: (N,) atomic numbers.
    extent_x_A: box height along the normal (vacuum above + crystal + bulk-side absorber).
    extent_y_A: periodic width perpendicular to the beam.
    length_z_A: length along the beam from the entrance plane (z = 0) to the exit plane.
    surface_x_A: x of the top surface of the first (upstream) terrace.
    crystal_start_z_A: z where the crystal begins (vacuum entrance region before it).
    metadata: builder metadata (terraces, steps with their type and b4_statement, labels).
    """
    atoms_xyz_A: np.ndarray
    Z: np.ndarray
    extent_x_A: float
    extent_y_A: float
    length_z_A: float
    surface_x_A: float
    crystal_start_z_A: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExitWave:
    """Complex wave on a DECLARED plane, per realisation (docs/05 section 4.3 item 8).

    psi: complex array, axes (x, y) = (surface normal, in-plane transverse), shape (nx, ny).
    dx_A, dy_A: pixel sizes; x0_A: x of row 0 (so x = x0_A + i dx_A); y0_A likewise.
    plane: text naming the plane, e.g. "exit plane z = L_z (no further propagation)".
    z_A: z of that plane. energy_keV, theta_in_ext_rad: as used.
    realisation: index of the static or frozen-phonon configuration; seed if random.
    metadata: engine parameters, band limit, propagator, absorber, potential source, labels.
    """
    psi: np.ndarray
    dx_A: float
    dy_A: float
    x0_A: float
    y0_A: float
    plane: str
    z_A: float
    energy_keV: float
    theta_in_ext_rad: float
    realisation: int
    seed: int | None
    metadata: dict[str, Any] = field(default_factory=dict)
