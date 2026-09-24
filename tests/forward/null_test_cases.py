"""Atomistic null-test diagnosis cases (not a test module): whole-crystal translation of a flat
Si(001) terrace by the builder's a/2 translation vector R, and the step-phase convergence study.
TEST_ONLY stand-ins are labelled as in smoke_case.py.

Required cell inputs (no defaults; E1 wave 2a):
* clean_depth_A: crystal between the lowest surface and the 15 A bulk absorber. The M2 study cells
  used buildup + 1 = 21 A, which is SHALLOWER than the 24.5 A (0,0,8) extinction depth (P2 section
  6.5, H2 section 3, H5 D.8): LEGACY_M2_CLEAN_DEPTH_A = 21.0 is kept only to reproduce M2
  (scripts/hpc/null_test_study/study.yaml, tests/forward/test_atomistic_translation.py). For the
  null-test criteria (1e-2 rad, 1e-2 in amplitude) >= 65 A with r >= 0.05 is the reviewed minimum
  (E7 M3, from P2's 1D model; H2 2.4 and 3); study_depth100.yaml uses 100 A as a margin. At r = 0
  no clean depth converges the absolute reflection (P2 6.5).
* azimuth: "110" (the M2 azimuth) or "100" (exact [100]: the (0,0,8) condition is at least a
  four-beam case there, H2 section 2.2); TEST_ONLY stand-ins for PROJECT_INPUT item 8. The in-plane
  period along the beam is a/sqrt(2) ([110]) or a ([100]); dz = period/4 (as M2 and H2).
* H, edge, gap: the sheet beam (full height H incl. the two sin^2 edges of width `edge`, bottom edge
  `gap` above the highest surface at the entrance plane; illumination.SheetBeam). Required (audit
  A6 N-1/N-3, X2): the M2 cells used H = 8, edge 2, gap 2 A (LEGACY_M2_BEAM), which lights only
  H/tan(theta) ~ 500 A of surface; the surface-position-resolved read-out needs the surface lit up
  to the exit plane (H2 2.4 and 2.6): `sheet_height_lit_to_exit_A` gives
  H = L_z tan(theta) - gap - step - 1 A (H2 2.6) with L_z from `cell_length_z_A`.
The surface-position-resolved read-out (H2 section 2.4, finding N12) is H2's own
`specular_column` (tools/hpc/supercell_sizing.py, imported, not re-implemented); the pairing of the
two crystals by surface point is `resolved_translation` below."""
from __future__ import annotations

import dataclasses

import numpy as np

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_reflection_cell
from reflection_holo.forward.multislice import (AtomicPotential, MultisliceParams,
                                                NumericalAbsorber, PhysicalAbsorption, SheetBeam,
                                                fft_friendly, run_realisation, select_beam,
                                                terrace_step_phase, wrap)
from reflection_holo.geometry.refraction import theta_int_from_ext_rad
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.structure import Staircase, build_si001_terraces

from smoke_case import AZ_LABEL, NO_ABS, STATIC, THETA_LABEL, _kirkland_F0

P = A_SI_A / np.sqrt(2)          # in-plane period for the [110] azimuth
Q = A_SI_A / 4                   # (001) layer spacing
V0_MIP = 8.0 / A_SI_A**3 * _kirkland_F0()
LEGACY_M2_CLEAN_DEPTH_A = 21.0   # LEGACY (M2 study cells: buildup 20 A + 1 A); shallower than the
#                                  24.5 A extinction depth (P2 6.5): for reproducing M2 only
AZIMUTHS = {"110": dict(uvw=(1, 1, 0), period_A=A_SI_A / np.sqrt(2), label=AZ_LABEL),
            "100": dict(uvw=(1, 0, 0), period_A=A_SI_A,
                        label="TEST_ONLY: stands in for PROJECT_INPUT item 8 (beam azimuth exact "
                              "[100]; (0,0,8) is at least four-beam there, H2 section 2.2)")}
TILE_ABOVE_PERIODS_M2 = 400      # M2's threshold for building one period and tiling (exact)
LEGACY_M2_BEAM = dict(H=8.0, edge=2.0, gap=2.0)   # LEGACY (M2 study cells): an 8 A sheet beam
#                                     lights ~500 A of surface; for reproducing M2 only (A6 N-1)
ENTRANCE_SLICES = 10             # entrance vacuum of the null-test cells: 10 slices of period/4
BUILDUP_A = 20.0                 # buildup_depth_A of the null-test cells (M2)
LIT_TO_EXIT_MARGIN_A = 1.0       # H2 2.6: the top edge lands 1 A (in height) before the exit plane


def _azimuth(azimuth):
    if azimuth not in AZIMUTHS:
        raise ValueError(f"azimuth must be one of {tuple(AZIMUTHS)} (TEST_ONLY stand-ins for "
                         f"PROJECT_INPUT item 8), got {azimuth!r}")
    return AZIMUTHS[azimuth]


def _clean_depth(clean_depth_A):
    if clean_depth_A is None:
        raise ValueError("clean_depth_A is required (LEGACY_M2_CLEAN_DEPTH_A = 21.0 reproduces M2; "
                         ">= 65 A is the reviewed minimum for the null-test criteria, E7 M3)")
    c = float(clean_depth_A)
    if not (np.isfinite(c) and c > 0):
        raise ValueError(f"clean_depth_A must be finite and > 0, got {clean_depth_A!r}")
    return c


def _beam_inputs(H, edge, gap):
    """The sheet-beam inputs of a null-test cell: required, finite, > 0 (SheetBeam asserts
    2 edge <= H)."""
    out = []
    for name, v in (("H", H), ("edge", edge), ("gap", gap)):
        if v is None or isinstance(v, bool):
            raise ValueError(f"{name} (sheet beam) is required: LEGACY_M2_BEAM = "
                             f"{LEGACY_M2_BEAM} reproduces M2; the surface-resolved read-out "
                             f"needs a beam lit to the exit plane (sheet_height_lit_to_exit_A)")
        f = float(v)
        if not (np.isfinite(f) and f > 0):
            raise ValueError(f"{name} must be finite and > 0, got {v!r}")
        out.append(f)
    return out


def cell_length_z_A(*, theta, azimuth, gap, extra_A, buildup=BUILDUP_A) -> float:
    """L_z of a translation_pair / parallel step_case cell (entrance vacuum 10 dz + whole periods
    along the beam, `_length_periods`); independent of H."""
    Pz = _azimuth(azimuth)["period_A"]
    ent = ENTRANCE_SLICES * (Pz / 4)                 # as translation_pair / step_case
    periods = _length_periods(theta, gap=gap, h_total=2 * Q, buildup=buildup, extra_A=extra_A,
                              ent=ent, period_A=Pz)
    return float(ent + periods * Pz)


def sheet_height_lit_to_exit_A(*, L_z_A, theta, gap, step_A=2 * Q,
                               margin_A=LIT_TO_EXIT_MARGIN_A) -> float:
    """H2 2.6 (DERIVED there): H = L_z tan(theta) - gap - step - 1 A, so that the top edge of a
    sheet beam whose bottom edge is `gap` above the HIGHEST surface reaches the LOWEST surface
    (step_A lower: a/2 for the translated pair in the fixed-beam case and for the a/2 step)
    margin_A in height, i.e. margin_A/tan(theta) along z, before the exit plane (engine item 3
    asserts the contact before the exit plane). Rounded DOWN to 1e-3 A (the study files carry the
    number)."""
    h = L_z_A * np.tan(theta) - gap - step_A - margin_A
    return float(np.floor(h * 1000.0) / 1000.0)


def theta_0008() -> float:
    """External angle of the (0,0,8) internal Bragg condition with the potential's own MIP."""
    return float(specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=200.0, V0_V=V0_MIP,
                                        a_A=A_SI_A).theta_ext)


def _build(staircase, periods, sub, azimuth):
    az = _azimuth(azimuth)
    return build_si001_terraces(azimuth_uvw=az["uvw"], azimuth_label=az["label"],
                                staircase=staircase, edge_periods=periods, substrate_layers=sub,
                                first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                                overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                                lattice_parameter_label="ASSUMPTION B2")


def _structure(staircase, periods, sub, *, tile_above, azimuth):
    """Builder result; for edges parallel to the beam and more than tile_above periods, ONE period
    along z is built (all builder assertions run on it) and tiled along z: exact, because such a
    crystal is periodic along z with the in-plane period (the builder's own z periodicity). This
    avoids the builder's ~55 kB per atom peak memory (4.7 GB for 84 000 atoms)."""
    if staircase.edges != "parallel" or periods <= tile_above:
        return _build(staircase, periods, sub, azimuth)
    import hashlib
    Pz = _azimuth(azimuth)["period_A"]
    one = _build(staircase, 1, sub, azimuth)
    n = one.n_atoms
    shift = np.repeat(np.arange(periods), n) * Pz
    pos = np.tile(one.positions_A, (periods, 1))
    pos[:, 2] += shift
    cell = one.cell_A.copy()
    cell[2, 2] = periods * Pz
    md = dict(one.metadata)
    md["edge_periods"] = periods
    md["atom_count"] = int(n * periods)
    md["positions_sha256"] = hashlib.sha256(np.ascontiguousarray(pos, "<f8").tobytes()).hexdigest()
    md["tiled_along_z"] = dict(periods=periods, from_verified_build_of_periods=1,
                               note="exact: the crystal is periodic along z (edges parallel)")
    return dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, periods),
                               cell_A=cell, layer_index=np.tile(one.layer_index, periods),
                               terrace_index=np.tile(one.terrace_index, periods), metadata=md)


def _params(cell, theta, *, dz, max_pixel=0.13, precision="complex64", buildup=20.0):
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / max_pixel)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / max_pixel)))
    return MultisliceParams(energy_keV=200.0, nx=nx, ny=ny, dz_A=dz, propagator="exact",
                            band_limit="2/3", backend="numpy", precision=precision, threads=4,
                            absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                            theta_out_ext_rad=theta, buildup_depth_A=buildup,
                            working_reflections_hkl=((0, 0, 8),))   # B17 stand-in (item 9)


def _length_periods(theta, *, gap, h_total, buildup, extra_A, ent, period_A):
    th_int = theta_int_from_ext_rad(theta, 200.0, V0_MIP)
    L_need = (gap + h_total) / np.tan(theta) + buildup / np.tan(th_int) + extra_A
    return int(np.ceil((L_need - ent) / period_A))


def _translation_check(sA, sB, R):
    """B's atoms above A's cut against wrap(A's atoms + R): nearest-neighbour distances with a
    KD-tree periodic in y and z (the builder's periodic directions; z periodic also at [100], where
    R has a z component; A6 n3/n4). Replaces a rounded-coordinate set comparison that was False for
    every pair (wrap rounding at the cell faces), including the verified legacy M2 pair."""
    from scipy.spatial import cKDTree
    L = np.diag(sA.cell_A)
    bs = np.array([1e6, L[1], L[2]])                 # x not periodic (1e6 A box)

    def wrap(p):
        w = np.mod(p, bs)
        w[w >= bs] = 0.0                             # np.mod may return the box length itself
        return w
    moved = wrap(sA.positions_A + R)
    b = sB.positions_A[sB.positions_A[:, 0] >= 2 * Q - 1e-6]
    d, _ = cKDTree(wrap(b), boxsize=bs).query(moved)
    dmax = float(d.max()) if len(d) else float("inf")
    return dict(n_translated=int(len(moved)), n_B_above=int(len(b)), max_distance_A=dmax,
                identical_sets=bool(len(b) == len(moved) and dmax < 1e-6),
                method="cKDTree periodic in y and z (A6 n3)")


def translation_pair(*, theta, clean_depth_A, azimuth, H, edge, gap, width_periods=2,
                     buildup=BUILDUP_A, extra_A=0.0, absorption=NO_ABS, precision="complex64",
                     move_beam: bool = False, tile_above_periods=TILE_ABOVE_PERIODS_M2):
    """Flat terrace A and the same crystal translated by the builder's a/2 translation R
    (normal component a/2), in identical boxes, with the identical beam and grid.

    clean_depth_A (required): crystal between A's surface and the 15 A bulk absorber (B has a/2
    more); azimuth (required): "110" or "100"; H, edge, gap (required): the sheet beam, bottom edge
    gap above B's surface (module docstring; LEGACY_M2_BEAM reproduces M2).
    Returns dict(A=(cell, pot), B=(cell, pot), beam, params, R_slab_A, check) where check holds the
    maximum distance between B's atoms above A's cut and wrap(A's atoms + R), periodic in y and z
    (must be ~0; A6 n3)."""
    H, edge, gap = _beam_inputs(H, edge, gap)
    Pz = _azimuth(azimuth)["period_A"]
    dz = Pz / 4
    ent = ENTRANCE_SLICES * dz
    absorber, clean = 15.0, _clean_depth(clean_depth_A)
    depth = absorber + clean
    sub = int(np.ceil(depth / Q)) + 2
    periods = _length_periods(theta, gap=gap, h_total=2 * Q, buildup=buildup, extra_A=extra_A,
                              ent=ent, period_A=Pz)
    flat = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(width_periods,),
                     boundary_step_layers=0)
    sA = _structure(flat, periods, sub, tile_above=tile_above_periods, azimuth=azimuth)
    sB = _structure(flat, periods, sub + 2, tile_above=tile_above_periods,
                    azimuth=azimuth)                           # top layer a/2 higher
    # the builder's a/2 translation vector R (slab frame), from a stepped build of the same lattice
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(1, 1),
                   boundary_step_layers=-2)
    R = np.array(_build(st, 2, 6, azimuth).metadata["steps"][0]["relation"]["t_slab_A"])
    assert abs(R[0] - 2 * Q) < 1e-9
    check = _translation_check(sA, sB, R)
    vac = float(np.ceil(H + gap + (ent + periods * Pz) * np.tan(theta) + 1.0)) + 2 * Q
    cA = build_reflection_cell(sA, vacuum_above_A=vac, depth_below_A=depth,
                               bulk_absorber_A=absorber, top_absorber_A=10.0,
                               entrance_vacuum_z_A=ent)
    cB = build_reflection_cell(sB, vacuum_above_A=vac - 2 * Q, depth_below_A=depth + 2 * Q,
                               bulk_absorber_A=absorber, top_absorber_A=10.0,
                               entrance_vacuum_z_A=ent)
    assert abs(cA.extent_x_A - cB.extent_x_A) < 1e-9 and abs(cA.length_z_A - cB.length_z_A) < 1e-9
    xbB = cB.metadata["layout"]["highest_surface_x_A"] + gap
    beamB = SheetBeam(height_A=H, edge_A=edge, x_bottom_A=xbB, theta_in_ext_rad=theta,
                      theta_label=THETA_LABEL)
    # move_beam: the envelope of A's beam is a/2 lower, so the WHOLE configuration (crystal and
    # illumination envelope) is translated; the carrier phase stays referenced to x = 0, which
    # leaves the expected specular phase difference -(k_out - k_in).R unchanged (report).
    beamA = dataclasses.replace(beamB, x_bottom_A=xbB - R[0]) if move_beam else beamB
    params = _params(cA, theta, precision=precision, buildup=buildup, dz=dz)
    pots = [AtomicPotential(c, parameterisation="kirkland", physical_absorption=absorption,
                            frozen_phonons=None, static_lattice_label=STATIC) for c in (cA, cB)]
    return dict(A=(cA, pots[0]), B=(cB, pots[1]), beam=beamB, beams=dict(A=beamA, B=beamB),
                params=params, R_slab_A=R, check=check, clean_depth_A=clean, azimuth=azimuth)


def specular_component(ew, theta, aperture, y_range=None):
    """Fourier component of the specular beam at f_c = sin(theta)/lambda over a y range."""
    lam = ew.metadata["beam"]["wavelength_A"]
    fc = np.sin(theta) / lam
    sel = select_beam(ew, fx_centre_per_A=fc, fy_centre_per_A=0.0, radius_per_A=aperture)
    x = ew.x0_A + np.arange(ew.psi.shape[0]) * ew.dx_A
    y = ew.y0_A + np.arange(ew.psi.shape[1]) * ew.dy_A
    m = np.ones_like(y, bool) if y_range is None else (y >= y_range[0]) & (y < y_range[1])
    return complex((sel * np.exp(-2j * np.pi * fc * x)[:, None])[:, m].sum() * ew.dx_A * ew.dy_A
                   / (m.sum() * ew.dy_A))


def vacuum_component(ew, theta, x_min_A, x_max_A):
    """Fourier component at f_c of the field in the vacuum window x_min <= x < x_max (all y),
    without a k-space aperture (the window excludes the crystal)."""
    lam = ew.metadata["beam"]["wavelength_A"]
    fc = np.sin(theta) / lam
    x = ew.x0_A + np.arange(ew.psi.shape[0]) * ew.dx_A
    w = (x >= x_min_A) & (x < x_max_A)
    col = ew.psi.astype(np.complex128).mean(axis=1)[w]
    return complex((col * np.exp(-2j * np.pi * fc * x[w])).sum() * ew.dx_A)


def _h2_specular_column():
    """H2's surface-position-resolved read-out (H2 section 2.4; H5 A10 reproduced it):
    tools/hpc/supercell_sizing.py specular_column, imported (not re-implemented)."""
    import importlib.util
    import sys
    from pathlib import Path
    name = "supercell_sizing_h2"
    if name not in sys.modules:
        path = Path(__file__).resolve().parents[2] / "tools" / "hpc" / "supercell_sizing.py"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name].specular_column


RESOLVED_KEYS = ("radius_per_A", "x_cut_A", "taper_A", "min_height_A", "bin_A", "exit_excl_A",
                 "tol_phase_rad", "tol_amp", "amp_floor_rel")


def lit_strip(pair, *, L_z_A, wavelength_A, radius_per_A):
    """Where each crystal of a pair is lit, in the surface coordinate z_s (along the beam from the
    entrance plane; contact of a ray descending at theta from height h above the surface: h/tan):
    bottom-edge contact, top-edge contact, end of the fully lit core (top edge minus the sin^2
    edge), and the LIT-END LIMIT of the surface-resolved read-out:

        lit_limit = min over A, B of (end of the lit core) - radius_per_A lambda L_z / tan(theta).

    The margin (DERIVED_HERE, X2; checked on A6's continuum case, see resolved_translation) is the
    z_s extent of the Fresnel fringes of the beam's top edge that pass the read-out band: a fringe a
    height dx below the geometric edge has, after a path L_z, the local frequency offset
    dx/(lambda L_z) from the carrier; |f - f_c| <= radius_per_A keeps dx <= radius lambda L_z, i.e.
    radius lambda L_z / tan(theta) of surface (933 A for L_z = 6000 A, 0.1 1/A, 16.13 mrad). In the
    fixed-beam case these fringes sit (x_sB - x_sA)/tan(theta) apart on A and B and do not cancel in
    the ratio."""
    th = float(pair["params"].theta_out_ext_rad)
    t = np.tan(th)
    rec = {}
    for key in ("A", "B"):
        xs = float(pair[key][0].metadata["layout"]["highest_surface_x_A"])
        b = pair["beams"][key]
        xb, H, e = float(b.x_bottom_A), float(b.height_A), float(b.edge_A)
        rec[key] = dict(x_surface_A=xs, z_bottom_contact_A=(xb - xs) / t,
                        z_top_contact_A=(xb + H - xs) / t, z_core_end_A=(xb + H - e - xs) / t)
    margin = float(radius_per_A) * float(wavelength_A) * float(L_z_A) / t
    first = min(("A", "B"), key=lambda k: rec[k]["z_core_end_A"])
    rec.update(top_edge_fringe_margin_A=margin, lit_limit_A=rec[first]["z_core_end_A"] - margin,
               lit_limit_set_by=first, L_z_A=float(L_z_A),
               rule="lit_limit = min(end of the fully lit core of A, B) - radius lambda L_z / "
                    "tan(theta) (top-edge Fresnel fringes inside the read-out band; X2, "
                    "DERIVED_HERE)")
    return rec


def check_lit_to_exit(pair, *, exit_excl_A):
    """A6 N-1: the surface-resolved read-out presumes the surface is lit up to the exit plane (H2
    2.4, 2.6). Refuse (ValueError) a pair whose sheet beam's top edge meets either crystal before
    L_z - exit_excl_A (the end of the read-out window): the bins beyond it would read the decaying
    tail of an unlit strip, whose ratio is not the null-test quantity. The engine itself asserts
    the contact before the exit plane (item 3)."""
    Lz = float(pair["A"][0].length_z_A)
    th = float(pair["params"].theta_out_ext_rad)
    bad = []
    for key in ("A", "B"):
        xs = float(pair[key][0].metadata["layout"]["highest_surface_x_A"])
        b = pair["beams"][key]
        zt = (float(b.x_bottom_A) + float(b.height_A) - xs) / np.tan(th)
        if zt < Lz - float(exit_excl_A):
            bad.append(f"{key}: top-edge contact z = {zt:.1f} A < L_z - exit_excl_A = "
                       f"{Lz - float(exit_excl_A):.1f} A (H {float(b.height_A):g} A)")
    if bad:
        raise ValueError("the sheet beam does not light the surface up to the read-out window "
                         "(A6 N-1; use H = sheet_height_lit_to_exit_A(...)): " + "; ".join(bad))


def resolved_translation(ewA, ewB, pair, *, expected_rad, radius_per_A, x_cut_A, taper_A,
                         min_height_A, bin_A, exit_excl_A, tol_phase_rad, tol_amp, amp_floor_rel):
    """Surface-position-resolved comparison of the translated crystal B with A (H2 N12).

    Each exit wave is read with H2's specular_column (y average, sin^2 vacuum window from
    x_cut_A above its OWN surface x_s over taper_A, band pass |f - f_c| <= radius_per_A,
    demodulation by exp(-2 pi i f_c x)) and mapped to the surface point z_s = L_z - (x - x_s) /
    tan(theta) (the ray reflected at z_s reaches the exit plane at that height; H2 2.4); pixels less
    than min_height_A above x_s are dropped. The two envelopes are averaged in the SAME bins of z_s
    (bin_A wide, from the later of the two bottom-edge contact points to L_z - exit_excl_A) and
    compared bin by bin (a final partial bin shorter than bin_A/2 is dropped): c = <E_B>/<E_A>,
    err = wrap(arg c - expected_rad), amp = |c|. For a
    translation R, E_B(z_s) = E_A(z_s - R_z) exp(-i (k_out - k_in).R) wherever the reflected field
    has converged (DERIVED_HERE; the beam envelope is not translated in the fixed-beam case, so B
    has been lit (x_sB - x_sA)/tan(theta) longer at the same z_s).

    Every bin is reported (`rows`, with `status` and `excluded_because`). A bin is EXCLUDED from the
    verdict (A6 N-2, X2) when
      * it ends beyond lit_strip()'s lit-end limit (the end of the fully lit core of A or B minus
        the top-edge fringe margin radius lambda L_z / tan(theta)); checked on A6's continuum case:
        the last bin of the fixed-beam comparison, 254 A before the end of B's lit core, reads
        |B|/|A| = 1.029 with the beams as run and 1.0004 when A's top edge is moved to meet the
        surface where B's does (X2 report); or
      * |E_A| or |E_B| is below amp_floor_rel times the largest bin amplitude of the same exit wave
        (REQUIRED; an unlit or decaying tail near the noise floor has no meaningful ratio).
    Verdict over the included bins, each passing when |err| <= tol_phase_rad and
    |amp - 1| <= tol_amp. Let d be the end of the last failing included bin, or the start of the
    first included bin if none fails (distances from the later contact):
      converged           at least one included bin starts at or after d (all of them pass); False
                          when the last included bin fails, or when no bin is included;
      converged_beyond_A  d when converged, else None (E1's contract, restored after audit A7-3:
                          a number in this field always means "converged beyond it");
      n_bins_beyond       included bins starting at or after d (all pass; 0 unless converged);
      last_examined_A     the end of the last INCLUDED bin (the farthest distance the verdict
                          examined; the excluded bins, wherever they lie, are listed in `excluded`
                          with their reason), whether converged or not; None when no bin is
                          included. When NOT converged, the last included bin fails and this is
                          its end (the value X2 had put in converged_beyond_A)."""
    spec = _h2_specular_column()
    th = float(pair["params"].theta_out_ext_rad)
    L = float(ewA.z_A)
    if float(ewB.z_A) != L:
        raise ValueError("A and B exit planes differ")
    floor = float(amp_floor_rel)
    if not (np.isfinite(floor) and 0.0 <= floor < 1.0):
        raise ValueError(f"amp_floor_rel must be a fraction in [0, 1), got {amp_floor_rel!r}")
    lam = float(ewA.metadata["beam"]["wavelength_A"])
    lit = lit_strip(pair, L_z_A=L, wavelength_A=lam, radius_per_A=radius_per_A)
    out = {}
    for key, ew in (("A", ewA), ("B", ewB)):
        cell = pair[key][0]
        xs = float(cell.metadata["layout"]["highest_surface_x_A"])
        x, e = spec(ew, xs=xs, th=th, radius=radius_per_A, x_cut=x_cut_A, taper=taper_A)
        zs = L - (x - xs) / np.tan(th)
        zc = (pair["beams"][key].x_bottom_A - xs) / np.tan(th)
        ok = (x >= xs + min_height_A) & (x < cell.metadata["layout"]["top_absorber_x_A"][0])
        out[key] = dict(zs=zs[ok], e=e[ok], xs=xs, z_contact_A=float(zc))
    z0 = max(out["A"]["z_contact_A"], out["B"]["z_contact_A"])
    z_end = L - exit_excl_A
    rows = []
    b = z0
    while b + 1e-9 < z_end:
        hi = min(b + bin_A, z_end)
        if hi - b < 0.5 * bin_A and rows:          # a final sliver of < half a bin is dropped
            break
        mA = (out["A"]["zs"] >= b) & (out["A"]["zs"] < hi)
        mB = (out["B"]["zs"] >= b) & (out["B"]["zs"] < hi)
        if np.any(mA) and np.any(mB):
            eA, eB = complex(out["A"]["e"][mA].mean()), complex(out["B"]["e"][mB].mean())
            c = eB / eA
            rows.append(dict(z_start_A=float(b), z_end_A=float(hi), d_start_A=float(b - z0),
                             d_end_A=float(hi - z0), E_A_abs=abs(eA), E_A_arg=float(np.angle(eA)),
                             E_B_abs=abs(eB), err_rad=float(wrap(np.angle(c) - expected_rad)),
                             amp_ratio=float(abs(c)), n_px_A=int(mA.sum()), n_px_B=int(mB.sum())))
        b = hi
    maxA = max((q["E_A_abs"] for q in rows), default=0.0)
    maxB = max((q["E_B_abs"] for q in rows), default=0.0)
    for q in rows:
        why = []
        if q["z_end_A"] > lit["lit_limit_A"] + 1e-9:
            why.append(f"beyond the lit-end limit z_s = {lit['lit_limit_A']:.1f} A (end of the lit "
                       f"core of {lit['lit_limit_set_by']} minus the top-edge fringe margin "
                       f"{lit['top_edge_fringe_margin_A']:.1f} A)")
        for k, amax in (("A", maxA), ("B", maxB)):
            v = q[f"E_{k}_abs"]
            if v < floor * amax:
                why.append(f"|E_{k}| = {v:.3e} below the amplitude floor {floor:g} x max |E_{k}| = "
                           f"{floor * amax:.3e}")
        q["passes"] = bool(abs(q["err_rad"]) <= tol_phase_rad
                           and abs(q["amp_ratio"] - 1.0) <= tol_amp)
        q["included"] = not why
        q["excluded_because"] = why
        q["status"] = "excluded" if why else ("pass" if q["passes"] else "fail")
    inc = [q for q in rows if q["included"]]
    if not inc:
        conv, n_after, last_examined = None, 0, None
        verdict = ("no bin included (none under the lit core above the amplitude floor): "
                   "convergence not assessed")
    else:
        fails = [q for q in inc if not q["passes"]]
        d = fails[-1]["d_end_A"] if fails else inc[0]["d_start_A"]
        n_after = sum(1 for q in inc if q["d_start_A"] >= d - 1e-9)
        last_examined = inc[-1]["d_end_A"]
        conv = d if n_after >= 1 else None           # A7-3: None unless converged (E1's contract)
        verdict = (f"converged beyond {d:.1f} A from the later contact ({n_after} included "
                   f"bin(s) beyond, all within tolerance)" if n_after else
                   f"NOT converged: the last included bin (ending {last_examined:.1f} A from the "
                   f"later contact, last_examined_A) fails")
    return dict(rows=rows, converged_beyond_A=conv, converged=bool(n_after >= 1),
                n_bins_beyond=n_after, last_examined_A=last_examined, n_bins=len(rows),
                n_included=len(inc), verdict=verdict,
                excluded=[dict(z_start_A=q["z_start_A"], z_end_A=q["z_end_A"],
                               because=q["excluded_because"]) for q in rows if not q["included"]],
                last_bin=(rows[-1] if rows else None), lit_strip=lit,
                z_contact_A=dict(A=out["A"]["z_contact_A"], B=out["B"]["z_contact_A"]),
                x_surface_A=dict(A=out["A"]["xs"], B=out["B"]["xs"]),
                params=dict(radius_per_A=radius_per_A, x_cut_A=x_cut_A, taper_A=taper_A,
                            min_height_A=min_height_A, bin_A=bin_A, exit_excl_A=exit_excl_A,
                            tol_phase_rad=tol_phase_rad, tol_amp=tol_amp,
                            amp_floor_rel=amp_floor_rel),
                readout="H2 section 2.4 specular_column (tools/hpc/supercell_sizing.py), bins of "
                        "the surface coordinate z_s shared by A and B; distances from the later "
                        "bottom-edge contact; verdict over the included bins (X2: lit-end limit "
                        "and amplitude floor)")


def run_translation(pair, *, aperture=0.2, vacuum_margins_A=(), surface_resolved=None):
    """Specular components of A and B: over all x after a k-space aperture (the engine's
    terrace_step_phase measurement) and, for each margin m, over the vacuum window
    [highest surface of B + m, top absorber) (the same window for A and B). surface_resolved: None
    (not computed) or a dict with every key of RESOLVED_KEYS: the surface-position-resolved
    comparison of resolved_translation from the same two runs."""
    if surface_resolved is not None:
        miss = [k for k in RESOLVED_KEYS if k not in surface_resolved]
        extra = [k for k in surface_resolved if k not in RESOLVED_KEYS]
        if miss or extra:
            raise ValueError(f"surface_resolved: missing {miss}, unknown {extra}")
    theta = pair["beam"].theta_in_ext_rad
    out = {}
    ews = {}
    layB = pair["B"][0].metadata["layout"]
    for key in ("A", "B"):
        cell, pot = pair[key]
        ew = run_realisation(cell, potential=pot, beam=pair["beams"][key],
                             params=pair["params"], realisation=0, seed=None)
        out[key] = specular_component(ew, theta, aperture)
        for m in vacuum_margins_A:
            out[(key, m)] = vacuum_component(ew, theta, layB["highest_surface_x_A"] + m,
                                             layB["top_absorber_x_A"][0])
        out[key + "_time"] = ew.metadata["timing_s"]["total"]
        if surface_resolved is not None:
            ews[key] = ew
    k = 2 * np.pi / ew.metadata["beam"]["wavelength_A"]
    th_out = pair["params"].theta_out_ext_rad
    k_in = np.array([-k * np.sin(theta), 0.0, k * np.cos(theta)])
    k_out = np.array([k * np.sin(th_out), 0.0, k * np.cos(th_out)])
    expected = float(-(k_out - k_in) @ pair["R_slab_A"])
    meas = float(np.angle(out["B"] / out["A"]))
    vac = {m: dict(err_rad=float(wrap(np.angle(out[("B", m)] / out[("A", m)]) - expected)),
                   amp_ratio=float(abs(out[("B", m)]) / abs(out[("A", m)])),
                   amp_A=abs(out[("A", m)])) for m in vacuum_margins_A}
    res = dict(delta_phi_rad=meas, expected_rad=expected, expected_wrapped=float(wrap(expected)),
               vacuum=vac,
               err_rad=float(wrap(meas - expected)),
               amp_ratio=float(abs(out["B"]) / abs(out["A"])), amp_A=abs(out["A"]),
               time_s=out["A_time"] + out["B_time"], grid=(pair["params"].nx, pair["params"].ny),
               n_slices=int(round(pair["A"][0].length_z_A / pair["params"].dz_A)))
    if surface_resolved is not None:
        res["surface_resolved"] = resolved_translation(ews["A"], ews["B"], pair,
                                                       expected_rad=expected, **surface_resolved)
    return res


def step_case(*, theta, width_periods, clean_depth_A, azimuth, H, edge, gap, edges="parallel",
              buildup=BUILDUP_A, extra_A=0.0, absorption=NO_ABS, precision="complex64",
              tile_above_periods=TILE_ABOVE_PERIODS_M2):
    """a/2 step between two terraces of width_periods each (edges parallel or transverse);
    clean_depth_A, azimuth and the sheet beam H, edge, gap (bottom edge gap above the upper
    terrace) required (module docstring)."""
    H, edge, gap = _beam_inputs(H, edge, gap)
    Pz = _azimuth(azimuth)["period_A"]
    dz = Pz / 4
    ent = ENTRANCE_SLICES * dz
    absorber, clean = 15.0, _clean_depth(clean_depth_A)
    depth = absorber + clean
    sub = int(np.ceil(depth / Q)) + 2
    st = Staircase(edges=edges, terrace_layers=(0, 2), terrace_widths=(width_periods,) * 2,
                   boundary_step_layers=-2)
    if edges == "parallel":
        periods = _length_periods(theta, gap=gap, h_total=2 * Q, buildup=buildup,
                                  extra_A=extra_A, ent=ent, period_A=Pz)
    else:
        periods = 2
    s = _structure(st, periods, sub, tile_above=tile_above_periods, azimuth=azimuth)
    L = ent + np.diag(s.cell_A)[2]
    vac = float(np.ceil(H + gap + L * np.tan(theta) + 1.0))
    cell = build_reflection_cell(s, vacuum_above_A=vac, depth_below_A=depth,
                                 bulk_absorber_A=absorber, top_absorber_A=10.0,
                                 entrance_vacuum_z_A=ent)
    beam = SheetBeam(height_A=H, edge_A=edge,
                     x_bottom_A=cell.metadata["layout"]["highest_surface_x_A"] + gap,
                     theta_in_ext_rad=theta, theta_label=THETA_LABEL)
    pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=absorption,
                          frozen_phonons=None, static_lattice_label=STATIC)
    return cell, pot, beam, _params(cell, theta, precision=precision, buildup=buildup, dz=dz)


def step_phase_rows(ew, cell, theta, *, apertures, window_offsets_A, window_width_A):
    """Step phase phi(upper) - phi(lower) for windows of fixed width centred at a distance d
    from the step edge at y = W (upper terrace y in [W, 2W), lower in [0, W); the other edge of
    each terrace is the periodic boundary step at y = 0 = 2W)."""
    lam = ew.metadata["beam"]["wavelength_A"]
    W = cell.extent_y_A / 2
    geo = -4 * np.pi / lam * (A_SI_A / 2) * np.sin(theta)
    rows = []
    for ap in apertures:
        for d in window_offsets_A:
            lo = (W - d - window_width_A / 2, W - d + window_width_A / 2)
            up = (W + d - window_width_A / 2, W + d + window_width_A / 2)
            r = terrace_step_phase(ew, theta_out_ext_rad=theta, aperture_radius_per_A=ap,
                                   upper_y_range_A=up, lower_y_range_A=lo)
            rows.append(dict(aperture=ap, d_A=d, delta_phi=r["delta_phi_rad"],
                             residual=float(wrap(r["delta_phi_rad"] - geo)),
                             amp_ratio=r["amplitude_upper"] / r["amplitude_lower"]))
    return geo, rows


def replace_absorption(pot, absorption):
    c = pot.cell
    return AtomicPotential(c, parameterisation="kirkland", physical_absorption=absorption,
                           frozen_phonons=None, static_lattice_label=STATIC)


__all__ = ["translation_pair", "run_translation", "step_case", "step_phase_rows", "theta_0008",
           "specular_component", "P", "Q", "V0_MIP", "replace_absorption", "dataclasses",
           "LEGACY_M2_CLEAN_DEPTH_A", "AZIMUTHS", "TILE_ABOVE_PERIODS_M2", "RESOLVED_KEYS",
           "resolved_translation", "LEGACY_M2_BEAM", "cell_length_z_A",
           "sheet_height_lit_to_exit_A", "lit_strip", "check_lit_to_exit"]
