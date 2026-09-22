"""Projection of the dark-field wave along k_out onto the surface and image coordinates
(docs/05 section 5 item 2; source map SM07; docs/03 section 6; DERIVED_HERE).

A surface feature at coordinate z_s along the beam appears on the exit plane at height
x = x0 - z_s tan(theta) (``reflection_holo.geometry.projection``), x0 being the exit-plane height of
a feature at z_s = 0 ON A DECLARED REFERENCE HEIGHT; inversely z_s = (x0 - x)/tan(theta). Three
samplings of the same rows are stated and kept:

* exit-plane height x, pixel dx (the engine's grid);
* surface coordinate along the beam z_s = (x0 - x)/tan(theta), pixel dx/tan(theta) (the
  1/tan(theta) magnification of the exit-plane height axis);
* image-plane coordinate u = z_s sin(theta) = (x0 - x) cos(theta) on the plane perpendicular to
  k_out through the exit-plane point x0, pixel dx cos(theta): the surface is foreshortened by
  sin(theta) along the beam (factor 1/sin(theta) = ``geometry.projection.foreshortening``), not
  across it; the perpendicular axis y keeps its pixel dy.

The array is flipped along x so that the along-beam image axis increases DOWNSTREAM (increasing
z_s). The wave values are not interpolated. A feature at height H != H_ref appears displaced by
(H - H_ref)/tan(theta) in the nominal z_s (the parallax of the projection; recorded), so masks that
depend on the true source point must be ray traced (forward.geometric.trace_exit_points), not read
from the nominal z_s. Moving the wave from the exit plane to the image plane is a propagation of
the demodulated envelope over at most |x - x0| sin(theta); it is neglected and its Fresnel phase
bound pi lambda s B^2 (B the aperture band, s the largest distance) is recorded.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from reflection_holo.geometry import projection as geo_projection
from reflection_holo.optics.darkfield import DarkFieldResult
from reflection_holo.optics.fields import Grid, Wave

IMAGE_AXES = ("along_beam", "perpendicular")


@dataclass(frozen=True, eq=False)
class ProjectedImage:
    """Dark-field wave on image-plane axes (along_beam, perpendicular).

    wave            Wave on a Grid with pixel sizes (du, dy) in image-plane A (specimen-referred)
    exit_x_A        exit-plane height x of each row (A)
    surface_z_A     nominal surface coordinate z_s of each row (A), reference-height mapping
    image_u_A       image-plane coordinate u = z_s sin(theta) of each row (A)
    y_A             perpendicular coordinate of each column (A)
    sampling        the three samplings of the along-beam rows and the perpendicular one
    """
    wave: Wave
    exit_x_A: np.ndarray
    surface_z_A: np.ndarray
    image_u_A: np.ndarray
    y_A: np.ndarray
    x0_A: float
    theta_out_ext_rad: float
    sampling: dict
    record: dict = field(default_factory=dict)


def project_along_k_out(df: DarkFieldResult, *, x0_A: float, x0_definition: str,
                        aperture_semi_angle_rad: float) -> ProjectedImage:
    """Relabel the rows of the demodulated dark-field wave with z_s and u (module docstring).

    x0_A            exit-plane height of a feature at z_s = 0 on the reference height (required)
    x0_definition   what the reference height is (e.g. "lowest terrace top, H = 4.07 A,
                    z_s = 0 at the upstream end of the field of view"); required, recorded
    aperture_semi_angle_rad  used only for the recorded Fresnel bound of the neglected propagation
    """
    if not isinstance(df, DarkFieldResult):
        raise TypeError("df must be a DarkFieldResult (select_dark_field)")
    if not isinstance(x0_definition, str) or not x0_definition.strip():
        raise ValueError("x0_definition must state the reference height of the projection")
    x0 = float(x0_A)
    if not np.isfinite(x0):
        raise ValueError("x0_A must be finite")
    th = float(df.theta_out_ext_rad)
    t, c, s = math.tan(th), math.cos(th), math.sin(th)
    g = df.wave.grid
    if g.axes != ("x", "y"):
        raise ValueError(f"dark-field wave axes must be ('x', 'y'), got {g.axes}")
    dx, dy = g.pixel_size_A
    nx, ny = g.shape
    x = df.x0_A + dx * np.arange(nx)
    x_rows = x[::-1].copy()                                   # downstream first after the flip
    z_s = geo_projection.surface_coordinate_A(x_rows, x0, th)
    u = z_s * s
    y = df.y0_A + dy * np.arange(ny)
    data = np.asarray(df.wave.data)[::-1, :]
    grid = Grid(shape=(nx, ny), pixel_size_A=(dx * c, dy), axes=IMAGE_AXES,
                plane="image plane perpendicular to k_out (projection along k_out of the "
                      "dark-field exit-plane wave), specimen-referred A")
    lam = df.record["wavelength_A"]
    B = math.sin(float(aperture_semi_angle_rad)) / lam
    s_max = float(np.max(np.abs(x - x0))) * s
    sampling = dict(
        exit_plane_dx_A=dx, surface_dz_s_A=dx / t, image_du_A=dx * c, perpendicular_dy_A=dy,
        foreshortening_1_over_sin_theta=geo_projection.foreshortening(th),
        exit_to_surface_magnification_1_over_tan_theta=1.0 / t,
        along_beam_axis="increasing downstream (increasing z_s); rows are exit-plane x reversed")
    record = dict(
        mapping="z_s = (x0 - x)/tan(theta) (SM07); u = z_s sin(theta)", x0_A=x0,
        x0_definition=x0_definition, theta_out_ext_rad=th,
        parallax="a surface point at height H maps to z_s + (H - H_ref)/tan(theta); masks are "
                 "ray traced from the true source points",
        neglected_propagation=dict(max_distance_A=s_max, aperture_band_cycles_per_A=B,
                                   fresnel_phase_bound_rad=math.pi * lam * s_max * B * B),
        interpolation="none (relabelling and flip only)")
    wave = Wave(data, grid, df.wave.label.replace("dark-field wave", "projected dark-field image"),
                df.wave.realisation, {"projection": record, "sampling": sampling,
                                      "dark_field": df.record})
    return ProjectedImage(wave=wave, exit_x_A=x_rows, surface_z_A=z_s, image_u_A=u, y_A=y,
                          x0_A=x0, theta_out_ext_rad=th, sampling=sampling, record=record)
