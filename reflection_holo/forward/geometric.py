"""Geometric-phase forward model for strained or displaced surfaces ("geometry mode").

Model (DERIVED_HERE; premises in docs/08_buried_defects.md section 2):

    A(r_par) = sum_l w_l exp(-i (q_int - G).(R_l - R_0)) exp(-i G.u(R_l, r_par))
    phi(r_par) = arg A(r_par) - (q_ext - G).u(R_0, r_par)

* l runs over the lattice layers below the surface position r_par (R_0 = outermost layer),
  w_l = exp(-depth_l / Lambda) is the penetration weight with an effective depth Lambda (ASSUMPTION;
  in the dynamical theory it is set by extinction and absorption and depends on the angle).
* The first factor is a column (kinematic) sum over the probed depth; exp(-i G.u) is unchanged
  across a Volterra cut because G.b is a multiple of 2 pi for a perfect dislocation.
* The second term is the vacuum path difference of the displaced surface, with the refraction-
  corrected external momentum transfer.
* For a rigid translation u = R the model returns exactly -q_ext.R, the translation-covariance step
  phase of docs/physics_conventions.md, independently of Lambda (tested).

Limitations: no dynamical scattering (valid as a small-strain kinematic approximation inside the
extinction depth), no shadowing (the relief of a buried dislocation is smooth, slopes << theta),
no lateral propagation blur, specular or single-reflection only. Agreement with the multislice is a
consistency check, not an independent validation (docs/05 section 4.4).
"""

from __future__ import annotations

import numpy as np


def column_phase(u_layers: np.ndarray, layer_depth: np.ndarray, G_vec, q_int_vec, q_ext_vec,
                 penetration_A: float):
    """Phase and relative amplitude for columns.

    u_layers : (L, ..., 3) displacement at each layer (index 0 = outermost layer) and position.
    layer_depth : (L,) depth of each layer below the outermost one (>= 0), A.
    G_vec, q_int_vec, q_ext_vec : rad/A, slab frame.
    """
    G = np.asarray(G_vec, float)
    qi = np.asarray(q_int_vec, float)
    qe = np.asarray(q_ext_vec, float)
    depth = np.asarray(layer_depth, float)
    if np.any(depth < 0):
        raise ValueError("layer depths must be >= 0")
    if not penetration_A > 0:
        raise ValueError("penetration depth must be positive")
    n_hat = np.array([1.0, 0.0, 0.0])
    w = np.exp(-depth / penetration_A)
    # (q_int - G).(R_l - R_0): the layer offset is along -n (depth)
    off = np.exp(-1j * ((qi - G) @ n_hat) * (-depth))
    shape = (len(depth),) + (1,) * (u_layers.ndim - 2)
    lattice = np.exp(-1j * (u_layers @ G))
    A = np.sum((w * off).reshape(shape) * lattice, axis=0) / np.sum(w)
    phase = np.angle(A) - u_layers[0] @ (qe - G)
    return phase, np.abs(A)


def specular_vectors(cond):
    """(G, q_int, q_ext) vectors along the outward normal x for a SpecularCondition."""
    n = np.array([1.0, 0.0, 0.0])
    return cond.G * n, cond.q_int * n, cond.q_ext * n


def rigid_step_phase(cond, R_vec) -> float:
    """Reference: -q_ext.R for a lattice-translation step (docs/physics_conventions.md)."""
    return float(-cond.q_ext * np.asarray(R_vec, float)[0])


def to_deformed_coordinates(field, y, u_y, period):
    """Resample a complex field given at undeformed positions y (Lagrangian) onto the lab grid y,
    where the material point y sits at y + u_y (Eulerian). Periodic along y with `period`.

    The beam sees atoms at their displaced positions, so a relief computed as u(y) appears at
    y + u_y(y). The map must be monotonic (|du_y/dy| < 1), which holds away from dislocation cores.
    """
    y_def = y + u_y
    if np.any(np.diff(y_def) <= 0):
        raise ValueError("deformed coordinates are not monotonic (core region inside the window)")
    ye = np.concatenate([y_def - period, y_def, y_def + period])
    fe = np.concatenate([field, field, field])
    return np.interp(y, ye, fe.real) + 1j * np.interp(y, ye, fe.imag)


def band_limit_1d(field, dy, q_max):
    """Ideal low-pass |q| < q_max (cycles/A) along the last axis: the objective aperture acting on a
    field that varies only perpendicular to the beam."""
    F = np.fft.fft(field, axis=-1)
    q = np.fft.fftfreq(field.shape[-1], dy)
    return np.fft.ifft(F * (np.abs(q) < q_max), axis=-1)
