"""Reflection cell for a Si(001) slab carrying a surface feature (reflection_holo.structure.features)
and the feature-aware checks that complement forward.cell.check_reflection_geometry.

The cell is built by forward.cell.build_reflection_cell unchanged: the structure presents ONE flat
terrace (the surface that carries the feature), so the layout's lowest_surface_x_A and
highest_surface_x_A are the FLAT surface, and the engine's docs/05 4.3 assertions (items 1 to 4:
vacuum margin, beam in the vacuum band, no end-face illumination, footprint, build-up length, clean
depth) are made for that surface. The feature's own extremes (the ridge top above it, the trench
floor below it) are recorded in cell.metadata["feature"] and checked by
:func:`check_feature_geometry` (DERIVED_HERE, the same rules applied to the feature):

  F1  vacuum margin above the HIGHEST ATOM (ridge top) > H + L_z tan(theta)   (item 2 rule)
  F2  the ring's z-range lies inside the fully lit core of the sheet beam's footprint on the flat
      surface, [z(bottom edge + e), z(top edge - e)], with the stated margin on both sides
  F3  clean crystal between the LOWEST top layer (trench floor) and the bulk absorber >= D
      (item 4 depth rule)
  F4  (recorded, not asserted) the crystal length that the engine's assertions would demand if the
      feature's extremes were read as terrace surfaces (a conservative reading: the ridge top as
      the highest surface forces the beam above it at the front face, the trench floor as the
      lowest surface moves the "first contact" downstream), and the shadow / blocked-view lengths
      h / tan(theta) of the feature.
Frame: slab frame (x = outward normal, y = z x x, z = beam azimuth), x = 0 at the box bottom, z = 0
at the entrance plane (forward.cell).
"""
from __future__ import annotations

import numpy as np

from reflection_holo.forward.cell import ReflectionGeometryError, build_reflection_cell
from reflection_holo.forward.contracts import ReflectionCell

SURFACE_SEMANTICS = (
    "feature cell: lowest_surface_x_A and highest_surface_x_A are the FLAT surface carrying the "
    "feature (the only terrace); the feature's top-layer range is metadata['feature'], checked by "
    "forward.feature_cell.check_feature_geometry")


def build_feature_reflection_cell(structure, *, vacuum_above_flat_surface_A: float,
                                  depth_below_A: float, bulk_absorber_A: float,
                                  top_absorber_A: float,
                                  entrance_vacuum_z_A: float) -> ReflectionCell:
    """ReflectionCell of a structure.features result (feature or flat reference). All arguments
    required; vacuum_above_flat_surface_A is measured from the FLAT top layer (the ridge stands in
    it; F1 checks the margin above the ridge top). Other arguments as forward.cell."""
    md = structure.metadata
    if md.get("schema") != "reflection_holo.structure.features/1":
        raise ValueError("expected a reflection_holo.structure.features structure")
    cell = build_reflection_cell(structure, vacuum_above_A=vacuum_above_flat_surface_A,
                                 depth_below_A=depth_below_A, bulk_absorber_A=bulk_absorber_A,
                                 top_absorber_A=top_absorber_A,
                                 entrance_vacuum_z_A=entrance_vacuum_z_A)
    lay = cell.metadata["layout"]
    x_flat_struct = float(md["terrace_map"][0]["top_height_A"])
    shift = x_flat_struct - float(depth_below_A)              # structure x -> cell x: x - shift
    ent = float(entrance_vacuum_z_A)
    x_hi_atom = float(np.max(cell.atoms_xyz_A[:, 0]))
    if x_hi_atom >= lay["top_absorber_x_A"][0]:
        raise ReflectionGeometryError(f"the highest atom (x = {x_hi_atom:.4f} A) reaches the top "
                                      f"absorber at x = {lay['top_absorber_x_A'][0]:.4f} A")
    f = md.get("feature")
    fc = None
    if f is not None:
        R, r = float(f["major_radius_A"]), float(f["minor_radius_A"])
        cz = float(f["center_z_A"]) + ent
        cy = float(f["center_y_A"])
        fc = dict(kind=f["kind"], label=f["label"], source=f["source"], project_input="item 13",
                  center_y_A=cy, center_z_A=cz, major_radius_A=R, minor_radius_A=r,
                  y_range_A=[cy - R - r, cy + R + r], z_range_A=[cz - R - r, cz + R + r],
                  flat_surface_x_A=float(lay["lowest_surface_x_A"]),
                  top_layer_x_range_A=[float(v) - shift for v in f["top_layer_x_range_A"]],
                  highest_atom_x_A=x_hi_atom,
                  n_removed=f["n_removed"], n_added=f["n_added"])
    cell.metadata["feature"] = fc
    lay["surface_semantics"] = SURFACE_SEMANTICS
    lay["highest_atom_x_A"] = x_hi_atom
    return cell


def check_feature_geometry(cell: ReflectionCell, *, beam, theta_out_ext_rad: float,
                           theta_int_rad: float, buildup_depth_A: float,
                           footprint_margin_A: float) -> dict:
    """Assert F1 to F3 of the module docstring and record F4; raises ReflectionGeometryError.
    beam: multislice.SheetBeam; all arguments required."""
    f = cell.metadata.get("feature")
    if f is None:
        raise ValueError("cell carries no feature (flat reference): nothing to check")
    lay = cell.metadata["layout"]
    th_in = float(beam.theta_in_ext_rad)
    th = max(th_in, float(theta_out_ext_rad))
    t_in, t_int = np.tan(th_in), np.tan(float(theta_int_rad))
    D = float(buildup_depth_A)
    m = float(footprint_margin_A)
    if not (np.isfinite(m) and m >= 0):
        raise ValueError("footprint_margin_A must be >= 0")
    s = float(lay["highest_surface_x_A"])
    lo_top, hi_top = f["top_layer_x_range_A"]
    out = {}

    def need(ok, key, msg, **nums):
        out[key] = dict(passed=bool(ok), **{k: float(v) for k, v in nums.items()})
        if not ok:
            raise ReflectionGeometryError(f"{key}: {msg} " + ", ".join(
                f"{k} = {v:.6g}" for k, v in nums.items()))

    top_abs = lay["top_absorber_x_A"][0]
    need(top_abs - hi_top > beam.height_A + cell.length_z_A * np.tan(th), "F1_vacuum_above_feature",
         "vacuum margin above the highest top layer of the feature must exceed H + L_z tan(theta)",
         margin_A=top_abs - hi_top, required_A=beam.height_A + cell.length_z_A * np.tan(th),
         feature_top_x_A=hi_top)
    z_core0 = (beam.x_bottom_A + beam.edge_A - s) / t_in
    z_core1 = (beam.x_bottom_A + beam.height_A - beam.edge_A - s) / t_in
    z0, z1 = f["z_range_A"]
    need(z0 - z_core0 >= m and z_core1 - z1 >= m, "F2_ring_inside_lit_footprint",
         "the ring must lie inside the fully lit footprint core on the flat surface with the margin",
         ring_z0_A=z0, ring_z1_A=z1, core_z0_A=z_core0, core_z1_A=z_core1, margin_A=m,
         upstream_clearance_A=z0 - z_core0, downstream_clearance_A=z_core1 - z1)
    clean = lo_top - lay["bulk_absorber_x_A"][1]
    need(clean >= D, "F3_depth_below_feature",
         "the crystal between the lowest top layer and the bulk absorber must be at least D thick",
         clean_depth_A=clean, D_A=D, lowest_top_layer_x_A=lo_top)
    Lc = cell.length_z_A - cell.crystal_start_z_A
    s_hi, s_lo = max(hi_top, s), min(lo_top, s)
    out["F4_conservative_reading"] = dict(
        passed=None,
        crystal_length_A=Lc,
        crystal_length_required_if_feature_extremes_were_terraces_A=float(
            (s_hi - s_lo) / t_in + D / t_int),
        crystal_length_required_flat_surface_A=float(D / t_int),
        shadow_or_blocked_view_length_A=float(max(hi_top - s, s - lo_top) / t_in),
        ring_start_fraction_of_crystal=float((z0 - cell.crystal_start_z_A) / Lc),
        ring_end_fraction_of_crystal=float((z1 - cell.crystal_start_z_A) / Lc),
        note="recorded only: the engine's assertions are made for the flat surface (module "
             "docstring F4)")
    out["label"] = "DERIVED_HERE (docs/05 4.3 items 2 to 4 applied to the feature)"
    return out
