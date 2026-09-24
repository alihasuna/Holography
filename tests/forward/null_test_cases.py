"""Atomistic null-test diagnosis cases (not a test module): whole-crystal translation of a flat
Si(001) terrace by the builder's a/2 translation vector R, and the step-phase convergence study.
TEST_ONLY stand-ins are labelled as in smoke_case.py.

Required cell inputs (no defaults; E1 wave 2a):
* clean_depth_A: crystal between the lowest surface and the 15 A bulk absorber. The M2 study cells
  used buildup + 1 = 21 A, which is SHALLOWER than the 24.5 A (0,0,8) extinction depth (P2 section
  6.5, H2 section 3, H5 D.8): LEGACY_M2_CLEAN_DEPTH_A = 21.0 is kept only to reproduce M2
  (scripts/hpc/null_test_study/study.yaml, tests/forward/test_atomistic_translation.py); P2
  recommends >= 100 A with r >= 0.05 (study_depth100.yaml).
* azimuth: "110" (the M2 azimuth) or "100" (exact [100]: the (0,0,8) condition is at least a
  four-beam case there, H2 section 2.2); TEST_ONLY stand-ins for PROJECT_INPUT item 8. The in-plane
  period along the beam is a/sqrt(2) ([110]) or a ([100]); dz = period/4 (as M2 and H2).
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


def _azimuth(azimuth):
    if azimuth not in AZIMUTHS:
        raise ValueError(f"azimuth must be one of {tuple(AZIMUTHS)} (TEST_ONLY stand-ins for "
                         f"PROJECT_INPUT item 8), got {azimuth!r}")
    return AZIMUTHS[azimuth]


def _clean_depth(clean_depth_A):
    if clean_depth_A is None:
        raise ValueError("clean_depth_A is required (LEGACY_M2_CLEAN_DEPTH_A = 21.0 reproduces M2; "
                         "P2 recommends >= 100 A)")
    c = float(clean_depth_A)
    if not (np.isfinite(c) and c > 0):
        raise ValueError(f"clean_depth_A must be finite and > 0, got {clean_depth_A!r}")
    return c


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


def translation_pair(*, theta, clean_depth_A, azimuth, width_periods=2, H=8.0, edge=2.0, gap=2.0,
                     buildup=20.0, extra_A=0.0, absorption=NO_ABS, precision="complex64",
                     move_beam: bool = False, tile_above_periods=TILE_ABOVE_PERIODS_M2):
    """Flat terrace A and the same crystal translated by the builder's a/2 translation R
    (normal component a/2), in identical boxes, with the identical beam and grid.

    clean_depth_A (required): crystal between A's surface and the 15 A bulk absorber (B has a/2
    more); azimuth (required): "110" or "100" (module docstring).
    Returns dict(A=(cell, pot), B=(cell, pot), beam, params, R_slab_A, check) where check is the
    maximum distance between B's atoms above A's cut and wrap(A's atoms + R) (must be ~0)."""
    Pz = _azimuth(azimuth)["period_A"]
    dz = Pz / 4
    ent = 10 * dz
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
    L = np.diag(sA.cell_A)
    moved = sA.positions_A + R
    moved[:, 1] %= L[1]
    moved[:, 2] %= L[2]
    for ax in (1, 2):
        moved[np.abs(moved[:, ax] - L[ax]) < 1e-6, ax] = 0.0
    keyB = np.round(sB.positions_A[sB.positions_A[:, 0] >= 2 * Q - 1e-6], 5)
    keyM = np.round(moved, 5)
    sB_set = {tuple(v) for v in keyB}
    sM_set = {tuple(v) for v in keyM}
    check = dict(n_translated=len(sM_set), n_B_above=len(sB_set),
                 identical_sets=bool(sB_set == sM_set))
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
                 "tol_phase_rad", "tol_amp")


def resolved_translation(ewA, ewB, pair, *, expected_rad, radius_per_A, x_cut_A, taper_A,
                         min_height_A, bin_A, exit_excl_A, tol_phase_rad, tol_amp):
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
    has been lit (x_sB - x_sA)/tan(theta) longer at the same z_s). converged_beyond_A: end of the
    last bin (distance from the later contact) with |err| > tol_phase_rad or |amp - 1| > tol_amp;
    0 if none; None if the LAST bin fails (not converged in this cell)."""
    spec = _h2_specular_column()
    th = float(pair["params"].theta_out_ext_rad)
    L = float(ewA.z_A)
    if float(ewB.z_A) != L:
        raise ValueError("A and B exit planes differ")
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
    bad = [q for q in rows if abs(q["err_rad"]) > tol_phase_rad or abs(q["amp_ratio"] - 1.0) >
           tol_amp]
    if not rows:
        conv = None
    elif bad and bad[-1] is rows[-1]:
        conv = None
    else:
        conv = bad[-1]["d_end_A"] if bad else 0.0
    return dict(rows=rows, converged_beyond_A=conv, n_bins=len(rows),
                last_bin=(rows[-1] if rows else None),
                z_contact_A=dict(A=out["A"]["z_contact_A"], B=out["B"]["z_contact_A"]),
                x_surface_A=dict(A=out["A"]["xs"], B=out["B"]["xs"]),
                params=dict(radius_per_A=radius_per_A, x_cut_A=x_cut_A, taper_A=taper_A,
                            min_height_A=min_height_A, bin_A=bin_A, exit_excl_A=exit_excl_A,
                            tol_phase_rad=tol_phase_rad, tol_amp=tol_amp),
                readout="H2 section 2.4 specular_column (tools/hpc/supercell_sizing.py), bins of "
                        "the surface coordinate z_s shared by A and B; distances from the later "
                        "bottom-edge contact")


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


def step_case(*, theta, width_periods, clean_depth_A, azimuth, edges="parallel", H=8.0, edge=2.0,
              gap=2.0, buildup=20.0, extra_A=0.0, absorption=NO_ABS, precision="complex64",
              tile_above_periods=TILE_ABOVE_PERIODS_M2):
    """a/2 step between two terraces of width_periods each (edges parallel or transverse);
    clean_depth_A and azimuth required (module docstring)."""
    Pz = _azimuth(azimuth)["period_A"]
    dz = Pz / 4
    ent = 10 * dz
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
           "resolved_translation"]
