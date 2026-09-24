"""Reflection cell: the box of the grazing-incidence multislice (docs/05 section 4.3 items 1 to 4).

Box layout along the surface normal x (cell frame; x = 0 at the bottom of the box):

    x = 0 .......................... bottom of the box = bottom of the crystal (NO vacuum below:
                                     semi-infinite emulation, docs/05 4.3 item 1)
    [0, bulk_absorber_A] ........... numerical bulk-side absorber, INSIDE the crystal (the crystal
                                     potential continues through it, so its upper edge is not a
                                     crystal/vacuum interface)
    lowest terrace surface ......... x = depth_below_A
    highest terrace surface
    vacuum_above_A of free vacuum .. above the HIGHEST terrace surface
    [extent_x - top_absorber_A, extent_x]  numerical top absorber; across the periodic seam of the
                                     FFT grid it is contiguous with the bulk absorber, so nothing
                                     leaving the box through the bottom re-enters at the top
                                     without crossing both.

Along the beam z: the illumination is launched at z = 0 (entrance plane) and the crystal occupies
[crystal_start_z_A, length_z_A) with crystal_start_z_A = entrance_vacuum_z_A > 0; the exit plane is
z = length_z_A (the downstream end face). The crystal is not periodic along z (two end faces);
y is periodic (the structure builder's in-plane period).

Frame: the slab frame of reflection_holo.geometry.frames (x = outward normal, y = z x x,
z = beam azimuth), translated so that x = 0 is the bottom of the box and z = 0 the entrance plane.

``check_reflection_geometry`` asserts the spec 4.3 geometry that needs the illumination (vacuum
margin, footprint, build-up length); the engine calls it before every run.
Numbers and rules: source map SM16, DERIVED_HERE.
"""
from __future__ import annotations

import hashlib

import numpy as np

from reflection_holo.forward.contracts import ReflectionCell
from reflection_holo.geometry.errors import GeometryError

_Z_OF = {"Si": 14, "O": 8}
BUILDUP_DEPTH_RANGE_A = (20.0, 100.0)   # docs/05 4.3 item 4: 2 to 10 nm normal penetration depth


class ReflectionGeometryError(GeometryError):
    """The reflection cell or the illumination violates docs/05 section 4.3 items 1 to 4 (SM16)."""


def _pos(v, name, *, strictly=True) -> float:
    if v is None:
        raise ValueError(f"{name} is required")
    v = float(v)
    if not np.isfinite(v) or (v <= 0.0 if strictly else v < 0.0):
        raise ValueError(f"{name} must be finite and {'>' if strictly else '>='} 0, got {v!r}")
    return v


def _layout_checks(vacuum_above_A, depth_below_A, bulk_absorber_A, top_absorber_A,
                   entrance_vacuum_z_A):
    vac = _pos(vacuum_above_A, "vacuum_above_A")
    dep = _pos(depth_below_A, "depth_below_A")
    bab = _pos(bulk_absorber_A, "bulk_absorber_A")
    tab = _pos(top_absorber_A, "top_absorber_A")
    ent = _pos(entrance_vacuum_z_A, "entrance_vacuum_z_A")
    if not bab < dep:
        raise ReflectionGeometryError(
            f"bulk_absorber_A = {bab} A must be smaller than depth_below_A = {dep} A: the bulk-side "
            f"absorber lies inside the crystal (docs/05 4.3 item 1)")
    return vac, dep, bab, tab, ent


def _hash_atoms(xyz, Z) -> str:
    h = hashlib.sha256(np.ascontiguousarray(xyz, dtype="<f8").tobytes())
    h.update(np.ascontiguousarray(Z, dtype="<i8").tobytes())
    return h.hexdigest()


def build_reflection_cell(structure, *, vacuum_above_A: float, depth_below_A: float,
                          bulk_absorber_A: float, top_absorber_A: float,
                          entrance_vacuum_z_A: float) -> ReflectionCell:
    """ReflectionCell from a structure-builder result (reflection_holo.structure.Si001Structure).

    Every argument is required (keyword-only, no defaults):
      vacuum_above_A       free vacuum between the HIGHEST terrace top layer and the top absorber
      depth_below_A        crystal kept below the LOWEST terrace top layer (atoms deeper are cut;
                           the structure must be at least this deep)
      bulk_absorber_A      thickness of the bulk-side absorber (inside the crystal, < depth_below_A)
      top_absorber_A       thickness of the top absorber
      entrance_vacuum_z_A  vacuum along the beam between the entrance plane z = 0 and the crystal
    Absorber strength and profile are engine parameters (multislice.NumericalAbsorber).
    """
    vac, dep, bab, tab, ent = _layout_checks(vacuum_above_A, depth_below_A, bulk_absorber_A,
                                             top_absorber_A, entrance_vacuum_z_A)
    md = structure.metadata
    if tuple(structure.pbc) != (False, True, True):
        raise ValueError(f"expected a structure periodic in (y, z) and open in x, got pbc "
                         f"{structure.pbc}")
    L = np.diag(np.asarray(structure.cell_A, float))
    over = ((md.get("options") or {}).get("overlayer") or {})
    oxide = over.get("value") == "continuum_oxide"
    if oxide:
        # continuum oxide (report E4): depth below the lowest KEPT crystal top layer, vacuum above
        # the highest TOP of the layer; the layer stack is recorded in the cell frame
        stacks = over["per_terrace"]
        tops = np.array([p["atomistic_crystal_top_x_A"] for p in stacks], float)
        layer_tops = np.array([p["top_x_A"] for p in stacks], float)
        nonconformal = _nonconformal_sublayer(over)         # audit A9b M1 (refuses or records)
    else:
        tops = np.array([t["top_height_A"] for t in md["terrace_map"]], float)
    lowest, highest = float(tops.min()), float(tops.max())
    bottom = lowest - dep
    tol = 1e-6
    xs = np.asarray(structure.positions_A, float)
    if bottom < xs[:, 0].min() - tol:
        raise ReflectionGeometryError(
            f"structure too thin: depth_below_A = {dep} A reaches x = {bottom:.4f} A below its "
            f"bottom layer at x = {xs[:, 0].min():.4f} A; build more substrate_layers")
    keep = xs[:, 0] >= bottom - tol
    xyz = xs[keep].copy()
    xyz[:, 0] -= bottom
    xyz[:, 2] += ent
    species = np.asarray(structure.species)[keep]
    try:
        Z = np.array([_Z_OF[s] for s in species], dtype=np.int64)
    except KeyError as exc:
        raise ValueError(f"unknown species {exc}") from None
    extent_x = ((float(layer_tops.max()) if oxide else highest) - bottom) + vac + tab
    staircase = md["staircase"]
    s_axis = staircase["staircase_axis"]
    terraces = []
    for t in md["terrace_map"]:
        rng = list(t["s_range_A"])
        if s_axis == "z":
            rng = [rng[0] + ent, rng[1] + ent]
        terraces.append(dict(index=t["index"], axis=s_axis, range_A=rng,
                             surface_x_A=float((tops[t["index"]] if oxide else t["top_height_A"])
                                               - bottom),
                             top_layer_relative=t["top_layer_relative"]))
        if oxide:
            terraces[-1]["oxide"] = _oxide_stack_in_cell(stacks[t["index"]], -bottom)
    layer = float(md["lattice"]["layer_spacing_A"])
    layout = dict(
        frame="slab frame (x = outward normal, y = z x x, z = beam azimuth); x = 0 at the bottom "
              "of the box, z = 0 at the entrance plane",
        box_bottom_x_A=0.0,
        crystal_bottom_x_A=float(xyz[:, 0].min()),
        crystal_bottom_tolerance_A=layer,
        bulk_absorber_x_A=[0.0, bab],
        lowest_surface_x_A=float(lowest - bottom),
        highest_surface_x_A=float(highest - bottom),
        top_absorber_x_A=[extent_x - tab, extent_x],
        vacuum_above_A=vac, depth_below_A=dep, bulk_absorber_A=bab, top_absorber_A=tab,
        entrance_vacuum_z_A=ent, crystal_length_z_A=float(L[2]),
        z_period_A=float(md["lattice"]["in_plane_period_A"]),
        y_period_A=float(L[1]),
        semi_infinite_emulation="no vacuum below the crystal; bulk-side absorber inside the crystal",
        end_faces="the crystal ends at z = crystal_start_z_A and z = length_z_A (not periodic in z)",
        periodic_boundary_step_note=(
            "the builder's step at the periodic z edge is not present in the reflection cell "
            "(z is open)" if s_axis == "z" else "staircase along y: the boundary step at the "
            "periodic y edge is physical (y periodic)"),
        label="DERIVED_HERE (docs/05 4.3 items 1 to 4; SM16)",
    )
    if oxide:
        layout.update(
            lowest_surface_x_A=float(layer_tops.min() - bottom),
            highest_surface_x_A=float(layer_tops.max() - bottom),
            overlayer=_oxide_layout(over, [tt["oxide"] for tt in terraces], terraces, s_axis,
                                    vac=vac, dep=dep))
        if nonconformal is not None:
            layout["overlayer"]["nonconformal_sublayer"] = nonconformal
    meta = dict(schema="reflection_holo.forward.cell/1",
                builder="reflection_holo.forward.cell.build_reflection_cell",
                kind="atomic",
                layout=layout, terraces=terraces,
                structure=dict(md), structure_positions_sha256=md.get("positions_sha256"),
                atoms_sha256=_hash_atoms(xyz, Z), n_atoms=int(len(Z)))
    return ReflectionCell(atoms_xyz_A=xyz, Z=Z, extent_x_A=float(extent_x),
                          extent_y_A=float(L[1]), length_z_A=float(ent + L[2]),
                          surface_x_A=float(terraces[0]["surface_x_A"]),
                          crystal_start_z_A=float(ent), metadata=meta)


def build_continuum_cell(*, extent_y_A: float, terrace_y_bounds_A, terrace_heights_A,
                         crystal_length_z_A: float, vacuum_above_A: float, depth_below_A: float,
                         bulk_absorber_A: float, top_absorber_A: float,
                         entrance_vacuum_z_A: float) -> ReflectionCell:
    """Structureless reflection cell (no atoms) for the refraction-only rungs of the validation
    ladder (docs/05 4.4 rungs 1 and 3): terraces of constant potential with step edges PARALLEL to
    the beam (terrace k occupies y in [bounds[k], bounds[k+1]) with its surface at
    x = depth_below_A + (height_k - min(heights))). The potential value is given to
    multislice.ContinuumTerracePotential. All arguments required."""
    vac, dep, bab, tab, ent = _layout_checks(vacuum_above_A, depth_below_A, bulk_absorber_A,
                                             top_absorber_A, entrance_vacuum_z_A)
    Ly = _pos(extent_y_A, "extent_y_A")
    Lc = _pos(crystal_length_z_A, "crystal_length_z_A")
    b = np.asarray(terrace_y_bounds_A, float)
    h = np.asarray(terrace_heights_A, float)
    if b.ndim != 1 or len(b) != len(h) + 1 or len(h) < 1:
        raise ValueError("terrace_y_bounds_A needs one more entry than terrace_heights_A")
    if abs(b[0]) > 1e-12 or abs(b[-1] - Ly) > 1e-9 or np.any(np.diff(b) <= 0):
        raise ValueError("terrace_y_bounds_A must increase from 0 to extent_y_A")
    hmin, hmax = float(h.min()), float(h.max())
    surf = dep + (h - hmin)
    extent_x = dep + (hmax - hmin) + vac + tab
    terraces = [dict(index=k, axis="y", range_A=[float(b[k]), float(b[k + 1])],
                     surface_x_A=float(surf[k]), height_A=float(h[k]))
                for k in range(len(h))]
    layout = dict(
        frame="cell frame (x = outward normal, y transverse, z = beam); x = 0 at the box bottom",
        box_bottom_x_A=0.0, crystal_bottom_x_A=0.0, crystal_bottom_tolerance_A=0.0,
        bulk_absorber_x_A=[0.0, bab], lowest_surface_x_A=float(dep),
        highest_surface_x_A=float(dep + hmax - hmin),
        top_absorber_x_A=[extent_x - tab, extent_x],
        vacuum_above_A=vac, depth_below_A=dep, bulk_absorber_A=bab, top_absorber_A=tab,
        entrance_vacuum_z_A=ent, crystal_length_z_A=Lc, z_period_A=None, y_period_A=Ly,
        semi_infinite_emulation="no vacuum below the crystal; bulk-side absorber inside the crystal",
        end_faces="front face at z = crystal_start_z_A; exit plane z = length_z_A",
        label="DERIVED_HERE (docs/05 4.3 items 1 to 4; SM16)")
    meta = dict(schema="reflection_holo.forward.cell/1",
                builder="reflection_holo.forward.cell.build_continuum_cell",
                kind="continuum", layout=layout, terraces=terraces,
                atoms_sha256=_hash_atoms(np.zeros((0, 3)), np.zeros(0, np.int64)), n_atoms=0,
                note="structureless constant-potential terraces (validation ladder rungs 1, 3)")
    return ReflectionCell(atoms_xyz_A=np.zeros((0, 3)), Z=np.zeros(0, np.int64),
                          extent_x_A=float(extent_x), extent_y_A=Ly, length_z_A=float(ent + Lc),
                          surface_x_A=float(surf[0]), crystal_start_z_A=float(ent), metadata=meta)


_OXIDE_X_KEYS = ("pre_oxidation_plane_x_A", "pre_oxidation_surface_x_A", "interface_x_A", "top_x_A",
                 "crystal_boundary_x_A", "atomistic_crystal_top_x_A",
                 "crystal_equivalent_boundary_x_A")
OXIDE_SURFACE_SEMANTICS = (
    "continuum oxide (report E4): terraces[k].surface_x_A is the CRYSTAL surface (kept top atomic "
    "layer, or the continuum crystal boundary); layout lowest/highest_surface_x_A are the TOPS of "
    "the layer (where the beam first meets matter), used by the docs/05 4.3 assertions; "
    "depth_below_A is measured below the lowest crystal surface; vacuum_above_A above the highest "
    "top of the layer")


def _nonconformal_sublayer(record: dict) -> dict | None:
    """Audit A9b M1: an ATOMISTIC multislice cell whose terraces carry different oxide thicknesses
    (or different consumed-layer counts) does not represent the grown-oxide term of the sub-layer
    part of the thickness differences (the
    crystal loses whole layers only), while the geometric engine applies it
    (structure.oxide.NONCONFORMAL_SUBLAYER). Refused unless the specification states
    nonconformal_sublayer_acknowledged = True (TEST_ONLY overrides label, checked by
    structure.oxide.validate_spec); then the statement and its size are recorded. Also refused:
    ONE thickness with different consumed-layer counts (possible at the rounding tie; re-audit A10b
    n1). None for one thickness and one count on every terrace."""
    from reflection_holo.structure import oxide as ox
    per = record["per_terrace"]
    thick = sorted({round(float(p["thickness_A"]), 12) for p in per})
    counts = sorted({int(p["consumed_layers"]) for p in per})
    if len(thick) < 2 and len(counts) < 2:
        return None
    f = float(record["consumed_si_fraction_f"])
    quant = [float(p["interface_quantisation_A"]) for p in per]
    sub = (max(quant) - min(quant)) / f          # largest sub-layer thickness difference (A)
    lo, hi = ox.SUBLAYER_RATE_DIFFERENCE_RAD_PER_A
    size = (f"terrace thicknesses {thick} A, consumed-layer counts {counts}; largest sub-layer "
            f"thickness difference {sub:.4f} A, i.e. about {lo * sub:.2f}-{hi * sub:.2f} rad "
            f"(mod 2 pi) between the engines at the B41 values")
    if record["nonconformal_sublayer_acknowledged"] is not True:
        raise ox.OxideSpecError(
            f"atomistic multislice cell with a NON-CONFORMAL continuum oxide ({size}): "
            f"{ox.NONCONFORMAL_SUBLAYER}. Refused unless the specification states "
            f"nonconformal_sublayer_acknowledged = True with a TEST_ONLY overrides label (audit A9b "
            f"M1)")
    return dict(acknowledged=True, label=record["labels"]["overrides"], size=size,
                largest_sublayer_thickness_difference_A=float(sub),
                statement=ox.NONCONFORMAL_SUBLAYER)


def _oxide_stack_in_cell(stack: dict, shift: float) -> dict:
    out = dict(stack)
    for k in _OXIDE_X_KEYS:
        if out.get(k) is not None:                 # None: no atoms (continuum crystal)
            out[k] = float(out[k] + shift)
    for k in ("measured_crystal_top_x_A",):
        if k in out:
            out[k] = float(out[k] + shift)
    return out


def _oxide_layout(record: dict, stacks: list, terraces: list, s_axis: str, *, vac: float,
                  dep: float) -> dict:
    # the stack a ray crosses: from the top of the layer to the lower of the continuum crystal
    # boundary and the kept top atomic plane (atomistic crystal: the plane lies a/8 below the kept
    # crystal's equivalent boundary, which the layer overlaps or misses by at most a/8 for the
    # nearest count and by up to 1.5 a/4 for a parity variant whose count is not the nearest one,
    # so the continuum boundary can then lie below the kept top atomic plane; re-audit A12 m3)
    thick = [float(st["top_x_A"] - min(v for v in (st["crystal_boundary_x_A"],
                                                   st.get("atomistic_crystal_top_x_A"))
                                       if v is not None)) for st in stacks]
    return dict(
        model="continuum_oxide", spec_sha256=record["spec_sha256"],
        conformal=bool(record["conformal"]), staircase_axis=s_axis,
        terrace_ranges_A=[list(t["range_A"]) for t in terraces],
        per_terrace=stacks, V_real_V=float(record["V_real_V"]),
        V_imag_V=float(record["V_imag_V"]), vacuum_edge_width_A=float(record["vacuum_edge_width_A"]),
        interface_width_A=float(record["interface_width_A"]),
        amorphous_si_thickness_A=float(record["amorphous_si_thickness_A"]),
        stack_thickness_max_A=float(max(thick)),
        vacuum_above_layer_top_A=vac, depth_below_crystal_A=dep,
        record={k: v for k, v in record.items() if k != "per_terrace"},
        surface_semantics=OXIDE_SURFACE_SEMANTICS)


def build_continuum_oxide_cell(*, extent_y_A: float, terrace_y_bounds_A, terrace_heights_A,
                               crystal_length_z_A: float, vacuum_above_A: float,
                               depth_below_A: float, bulk_absorber_A: float, top_absorber_A: float,
                               entrance_vacuum_z_A: float, oxide, lattice_parameter_A: float,
                               lattice_parameter_label: str) -> ReflectionCell:
    """Structureless reflection cell with a continuum oxide (report E4): terraces of a continuum
    crystal with step edges PARALLEL to the beam (as build_continuum_cell), whose PRE-OXIDATION
    surfaces are ``terrace_heights_A``; the oxide (structure.oxide.ContinuumOxideSpec) moves every
    crystal boundary down to x_c = H - f t - t_a and its top to H + (1 - f) t. terraces[k].
    surface_x_A is the crystal boundary x_c (so ContinuumTerracePotential fills exactly the crystal);
    depth_below_A is measured below the lowest crystal boundary, vacuum_above_A above the highest
    top of the layer; layout lowest/highest_surface_x_A are the tops of the layer
    (OXIDE_SURFACE_SEMANTICS). lattice_parameter_A (with its label) sets f and a/4. All arguments
    required."""
    from reflection_holo.io.labels import require_evidence_label
    from reflection_holo.structure import oxide as ox
    require_evidence_label(lattice_parameter_label, "lattice parameter (model_assumptions B2)",
                           accepted=("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY"), qualified=True)
    vac, dep, bab, tab, ent = _layout_checks(vacuum_above_A, depth_below_A, bulk_absorber_A,
                                             top_absorber_A, entrance_vacuum_z_A)
    Ly = _pos(extent_y_A, "extent_y_A")
    Lc = _pos(crystal_length_z_A, "crystal_length_z_A")
    b = np.asarray(terrace_y_bounds_A, float)
    h = np.asarray(terrace_heights_A, float)
    if b.ndim != 1 or len(b) != len(h) + 1 or len(h) < 1:
        raise ValueError("terrace_y_bounds_A needs one more entry than terrace_heights_A")
    if abs(b[0]) > 1e-12 or abs(b[-1] - Ly) > 1e-9 or np.any(np.diff(b) <= 0):
        raise ValueError("terrace_y_bounds_A must increase from 0 to extent_y_A")
    st = ox.terrace_stacks(oxide, terrace_heights_A=h, a_A=lattice_parameter_A,
                           crystal=ox.CRYSTAL_CONTINUUM)
    xc = np.array([p["crystal_boundary_x_A"] for p in st["per_terrace"]])
    xt = np.array([p["top_x_A"] for p in st["per_terrace"]])
    shift = dep - float(xc.min())                        # structure x -> cell x
    extent_x = float(xt.max() + shift) + vac + tab
    stacks = [_oxide_stack_in_cell(p, shift) for p in st["per_terrace"]]
    terraces = [dict(index=k, axis="y", range_A=[float(b[k]), float(b[k + 1])],
                     surface_x_A=float(xc[k] + shift), height_A=float(h[k]), oxide=stacks[k])
                for k in range(len(h))]
    layout = dict(
        frame="cell frame (x = outward normal, y transverse, z = beam); x = 0 at the box bottom",
        box_bottom_x_A=0.0, crystal_bottom_x_A=0.0, crystal_bottom_tolerance_A=0.0,
        bulk_absorber_x_A=[0.0, bab], lowest_surface_x_A=float(xt.min() + shift),
        highest_surface_x_A=float(xt.max() + shift),
        top_absorber_x_A=[extent_x - tab, extent_x],
        vacuum_above_A=vac, depth_below_A=dep, bulk_absorber_A=bab, top_absorber_A=tab,
        entrance_vacuum_z_A=ent, crystal_length_z_A=Lc, z_period_A=None, y_period_A=Ly,
        semi_infinite_emulation="no vacuum below the crystal; bulk-side absorber inside the crystal",
        end_faces="front face at z = crystal_start_z_A; exit plane z = length_z_A",
        label="DERIVED_HERE (docs/05 4.3 items 1 to 4; SM16)")
    rec = dict(st["record"], per_terrace=st["per_terrace"])
    layout["overlayer"] = _oxide_layout(rec, stacks, terraces, "y", vac=vac, dep=dep)
    meta = dict(schema="reflection_holo.forward.cell/1",
                builder="reflection_holo.forward.cell.build_continuum_oxide_cell",
                kind="continuum", layout=layout, terraces=terraces,
                lattice=dict(a_A=float(lattice_parameter_A), a_label=lattice_parameter_label),
                atoms_sha256=_hash_atoms(np.zeros((0, 3)), np.zeros(0, np.int64)), n_atoms=0,
                note="structureless continuum crystal under a continuum oxide (report E4)")
    return ReflectionCell(atoms_xyz_A=np.zeros((0, 3)), Z=np.zeros(0, np.int64),
                          extent_x_A=float(extent_x), extent_y_A=Ly, length_z_A=float(ent + Lc),
                          surface_x_A=float(terraces[0]["surface_x_A"]),
                          crystal_start_z_A=float(ent), metadata=meta)


def check_reflection_geometry(cell: ReflectionCell, *, beam_height_A: float,
                              beam_x_bottom_A: float, theta_in_ext_rad: float,
                              theta_out_ext_rad: float, theta_int_rad: float,
                              buildup_depth_A: float) -> dict:
    """Assert docs/05 section 4.3 items 1 to 4 for a cell and a sheet-beam illumination; return
    the numbers (stored in ExitWave.metadata["geometry_checks"]). Raises ReflectionGeometryError.

    beam_height_A      full height H of the sheet beam at the entrance plane (incl. apodisation)
    beam_x_bottom_A    x of its lower edge at z = 0
    theta_in_ext_rad, theta_out_ext_rad   external glancing angles (PROJECT_INPUT item 7; the
                       outgoing one equals the incident one for the specular beam)
    theta_int_rad      internal (refracted) glancing angle of the incident beam (SM04, computed by
                       the engine from the potential's mean inner potential)
    buildup_depth_A    normal penetration depth D the refracted ray must reach: 20 to 100 A
                       (docs/05 4.3 item 4, "2 to 10 nm"); a value outside is refused.
    """
    lay = cell.metadata["layout"]
    H = _pos(beam_height_A, "beam_height_A")
    xb = float(beam_x_bottom_A)
    th_in = _pos(theta_in_ext_rad, "theta_in_ext_rad")
    th_out = _pos(theta_out_ext_rad, "theta_out_ext_rad")
    th_int = _pos(theta_int_rad, "theta_int_rad")
    D = _pos(buildup_depth_A, "buildup_depth_A")
    lo, hi = BUILDUP_DEPTH_RANGE_A
    if not lo <= D <= hi:
        raise ReflectionGeometryError(f"buildup_depth_A = {D} A outside the 20 to 100 A range of "
                                      f"docs/05 4.3 item 4 (2 to 10 nm)")
    Lz, zc = float(cell.length_z_A), float(cell.crystal_start_z_A)
    s_lo, s_hi = lay["lowest_surface_x_A"], lay["highest_surface_x_A"]
    top_abs = lay["top_absorber_x_A"][0]
    th_max = max(th_in, th_out)
    out = {}

    def need(ok, key, msg, **nums):
        out[key] = dict(passed=bool(ok), **nums)
        if not ok:
            raise ReflectionGeometryError(f"{key}: {msg} " + ", ".join(
                f"{k} = {v:.6g}" for k, v in nums.items()))

    # item 1: semi-infinite emulation
    need(lay["crystal_bottom_x_A"] <= lay["crystal_bottom_tolerance_A"] + 1e-9,
         "item1_no_vacuum_below", "the crystal must reach the bottom of the box",
         crystal_bottom_x_A=lay["crystal_bottom_x_A"],
         tolerance_A=lay["crystal_bottom_tolerance_A"])
    need(0 < lay["bulk_absorber_A"] < lay["depth_below_A"], "item1_bulk_absorber_inside_crystal",
         "the bulk absorber must lie inside the crystal", bulk_absorber_A=lay["bulk_absorber_A"],
         depth_below_A=lay["depth_below_A"])
    need(lay["top_absorber_A"] > 0, "item1_top_absorber", "a top absorber is required",
         top_absorber_A=lay["top_absorber_A"])
    # item 2: vacuum margin
    margin = top_abs - s_hi
    need_margin = H + Lz * np.tan(th_max)
    need(margin > need_margin, "item2_vacuum_margin",
         "vacuum margin above the highest surface must exceed H + L_z tan(theta)",
         margin_A=margin, required_A=need_margin, H_A=H, L_z_A=Lz, theta_mrad=th_max * 1e3)
    # item 3: illumination confined to the vacuum band, launched upstream, footprint
    need(zc > 0, "item3_launched_upstream", "the crystal must start downstream of z = 0",
         crystal_start_z_A=zc)
    need(xb >= s_hi and xb + H <= top_abs, "item3_beam_in_vacuum_band_at_launch",
         "the beam must lie in the vacuum band at z = 0", beam_bottom_A=xb, beam_top_A=xb + H,
         highest_surface_A=s_hi, top_absorber_start_A=top_abs)
    xb_front = xb - zc * np.tan(th_in)
    need(xb_front >= s_hi, "item3_no_end_face_illumination",
         "at the front face the whole beam must still be above the highest surface",
         beam_bottom_at_front_face_A=xb_front, highest_surface_A=s_hi)
    foot = H / np.tan(th_in)
    z_top_contact = (xb + H - s_lo) / np.tan(th_in)
    need(Lz - zc >= foot and z_top_contact <= Lz, "item3_footprint",
         "the crystal must be longer than the footprint H/tan(theta) and the top edge of the beam "
         "must reach the lowest surface before the exit plane",
         footprint_A=foot, crystal_length_A=Lz - zc, z_top_edge_contact_A=z_top_contact,
         L_z_A=Lz)
    # item 4: dynamical build-up length
    z_first_low = (xb - s_lo) / np.tan(th_in)
    build = D / np.tan(th_int)
    need(Lz - z_first_low >= build, "item4_buildup_length",
         "downstream of the first contact with the lowest surface the refracted ray must reach "
         "the depth D before the exit plane", available_A=Lz - z_first_low, required_A=build,
         D_A=D, theta_int_mrad=th_int * 1e3)
    need(lay["depth_below_A"] - lay["bulk_absorber_A"] >= D, "item4_depth_above_absorber",
         "the crystal between the lowest surface and the bulk absorber must be at least D thick",
         clean_depth_A=lay["depth_below_A"] - lay["bulk_absorber_A"], D_A=D)
    ov = lay.get("overlayer")
    if ov is not None:
        # continuum oxide (report E4): the refracted ray must first cross the whole layer stack
        # (thickest terrace; bounded with the EXTERNAL angle, which is smaller than the angle in
        # any layer of positive potential, so the requirement is conservative) and then reach D
        # in the crystal before the exit plane
        stack = float(ov["stack_thickness_max_A"])
        build_ov = stack / np.tan(th_in) + D / np.tan(th_int)
        need(Lz - z_first_low >= build_ov, "item4_buildup_length_through_overlayer",
             "downstream of the first contact with the lowest top of the layer the ray must cross "
             "the layer stack and reach the depth D in the crystal before the exit plane",
             available_A=Lz - z_first_low, required_A=build_ov, stack_A=stack, D_A=D)
    out["label"] = "DERIVED_HERE (SM16; docs/05 4.3 items 1 to 4)"
    return out
