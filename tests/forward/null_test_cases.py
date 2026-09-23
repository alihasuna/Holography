"""Atomistic null-test diagnosis cases (not a test module): whole-crystal translation of a flat
Si(001) terrace by the builder's a/2 translation vector R, and the step-phase convergence study.
TEST_ONLY stand-ins are labelled as in smoke_case.py."""
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


def theta_0008() -> float:
    """External angle of the (0,0,8) internal Bragg condition with the potential's own MIP."""
    return float(specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=200.0, V0_V=V0_MIP,
                                        a_A=A_SI_A).theta_ext)


def _build(staircase, periods, sub):
    return build_si001_terraces(azimuth_uvw=(1, 1, 0), azimuth_label=AZ_LABEL,
                                staircase=staircase, edge_periods=periods, substrate_layers=sub,
                                first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                                overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                                lattice_parameter_label="ASSUMPTION B2")


def _structure(staircase, periods, sub, *, tile_above=400):
    """Builder result; for edges parallel to the beam and more than tile_above periods, ONE period
    along z is built (all builder assertions run on it) and tiled along z: exact, because such a
    crystal is periodic along z with the in-plane period (the builder's own z periodicity). This
    avoids the builder's ~55 kB per atom peak memory (4.7 GB for 84 000 atoms)."""
    if staircase.edges != "parallel" or periods <= tile_above:
        return _build(staircase, periods, sub)
    import hashlib
    one = _build(staircase, 1, sub)
    n = one.n_atoms
    shift = np.repeat(np.arange(periods), n) * P
    pos = np.tile(one.positions_A, (periods, 1))
    pos[:, 2] += shift
    cell = one.cell_A.copy()
    cell[2, 2] = periods * P
    md = dict(one.metadata)
    md["edge_periods"] = periods
    md["atom_count"] = int(n * periods)
    md["positions_sha256"] = hashlib.sha256(np.ascontiguousarray(pos, "<f8").tobytes()).hexdigest()
    md["tiled_along_z"] = dict(periods=periods, from_verified_build_of_periods=1,
                               note="exact: the crystal is periodic along z (edges parallel)")
    return dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, periods),
                               cell_A=cell, layer_index=np.tile(one.layer_index, periods),
                               terrace_index=np.tile(one.terrace_index, periods), metadata=md)


def _params(cell, theta, *, max_pixel=0.13, precision="complex64", buildup=20.0, dz=P / 4):
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / max_pixel)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / max_pixel)))
    return MultisliceParams(energy_keV=200.0, nx=nx, ny=ny, dz_A=dz, propagator="exact",
                            band_limit="2/3", backend="numpy", precision=precision, threads=4,
                            absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                            theta_out_ext_rad=theta, buildup_depth_A=buildup,
                            working_reflections_hkl=((0, 0, 8),))   # B17 stand-in (item 9)


def _length_periods(theta, *, gap, h_total, buildup, extra_A, ent):
    th_int = theta_int_from_ext_rad(theta, 200.0, V0_MIP)
    L_need = (gap + h_total) / np.tan(theta) + buildup / np.tan(th_int) + extra_A
    return int(np.ceil((L_need - ent) / P))


def translation_pair(*, theta, width_periods=2, H=8.0, edge=2.0, gap=2.0, buildup=20.0,
                     extra_A=0.0, absorption=NO_ABS, precision="complex64",
                     move_beam: bool = False):
    """Flat terrace A and the same crystal translated by the builder's a/2 translation R
    (normal component a/2), in identical boxes, with the identical beam and grid.

    Returns dict(A=(cell, pot), B=(cell, pot), beam, params, R_slab_A, check) where check is the
    maximum distance between B's atoms above A's cut and wrap(A's atoms + R) (must be ~0)."""
    dz = P / 4
    ent = 10 * dz
    absorber, clean = 15.0, buildup + 1.0
    depth = absorber + clean
    sub = int(np.ceil(depth / Q)) + 2
    periods = _length_periods(theta, gap=gap, h_total=2 * Q, buildup=buildup, extra_A=extra_A,
                              ent=ent)
    flat = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(width_periods,),
                     boundary_step_layers=0)
    sA = _structure(flat, periods, sub)
    sB = _structure(flat, periods, sub + 2)                   # top layer a/2 higher
    # the builder's a/2 translation vector R (slab frame), from a stepped build of the same lattice
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(1, 1),
                   boundary_step_layers=-2)
    R = np.array(_build(st, 2, 6).metadata["steps"][0]["relation"]["t_slab_A"])
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
    vac = float(np.ceil(H + gap + (ent + periods * P) * np.tan(theta) + 1.0)) + 2 * Q
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
    params = _params(cA, theta, precision=precision, buildup=buildup)
    pots = [AtomicPotential(c, parameterisation="kirkland", physical_absorption=absorption,
                            frozen_phonons=None, static_lattice_label=STATIC) for c in (cA, cB)]
    return dict(A=(cA, pots[0]), B=(cB, pots[1]), beam=beamB, beams=dict(A=beamA, B=beamB),
                params=params, R_slab_A=R, check=check)


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


def run_translation(pair, *, aperture=0.2, vacuum_margins_A=()):
    """Specular components of A and B: over all x after a k-space aperture (the engine's
    terrace_step_phase measurement) and, for each margin m, over the vacuum window
    [highest surface of B + m, top absorber) (the same window for A and B)."""
    theta = pair["beam"].theta_in_ext_rad
    out = {}
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
    k = 2 * np.pi / ew.metadata["beam"]["wavelength_A"]
    th_out = pair["params"].theta_out_ext_rad
    k_in = np.array([-k * np.sin(theta), 0.0, k * np.cos(theta)])
    k_out = np.array([k * np.sin(th_out), 0.0, k * np.cos(th_out)])
    expected = float(-(k_out - k_in) @ pair["R_slab_A"])
    meas = float(np.angle(out["B"] / out["A"]))
    vac = {m: dict(err_rad=float(wrap(np.angle(out[("B", m)] / out[("A", m)]) - expected)),
                   amp_ratio=float(abs(out[("B", m)]) / abs(out[("A", m)])),
                   amp_A=abs(out[("A", m)])) for m in vacuum_margins_A}
    return dict(delta_phi_rad=meas, expected_rad=expected, expected_wrapped=float(wrap(expected)),
                vacuum=vac,
                err_rad=float(wrap(meas - expected)),
                amp_ratio=float(abs(out["B"]) / abs(out["A"])), amp_A=abs(out["A"]),
                time_s=out["A_time"] + out["B_time"], grid=(pair["params"].nx, pair["params"].ny),
                n_slices=int(round(pair["A"][0].length_z_A / pair["params"].dz_A)))


def step_case(*, theta, width_periods, edges="parallel", H=8.0, edge=2.0, gap=2.0, buildup=20.0,
              extra_A=0.0, absorption=NO_ABS, precision="complex64"):
    """a/2 step between two terraces of width_periods each (edges parallel or transverse)."""
    dz = P / 4
    ent = 10 * dz
    absorber, clean = 15.0, buildup + 1.0
    depth = absorber + clean
    sub = int(np.ceil(depth / Q)) + 2
    st = Staircase(edges=edges, terrace_layers=(0, 2), terrace_widths=(width_periods,) * 2,
                   boundary_step_layers=-2)
    if edges == "parallel":
        periods = _length_periods(theta, gap=gap, h_total=2 * Q, buildup=buildup,
                                  extra_A=extra_A, ent=ent)
    else:
        periods = 2
    s = _structure(st, periods, sub)
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
    return cell, pot, beam, _params(cell, theta, precision=precision, buildup=buildup)


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
           "specular_component", "P", "Q", "V0_MIP", "replace_absorption", "dataclasses"]
