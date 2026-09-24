"""Shared TEST_ONLY cases for the continuum-oxide tests (report E4; not a test module).

Every value standing in for a PROJECT_INPUT is labelled TEST_ONLY; the oxide parameters are the
L8/E9 demo values (t_ox 20 A, 2.20 g/cm^3, V_ox 10.34 V, V'_ox 0.40 V, graded 0.5 A edge) cited
from tools/review/e9_recompute_output.txt ("out:N")."""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_continuum_oxide_cell
from reflection_holo.forward.multislice import (ContinuumOxidePotential, ContinuumTerracePotential,
                                                MultisliceParams, NumericalAbsorber,
                                                PhysicalAbsorption, SheetBeam,
                                                analytic_step_reflection,
                                                flat_reflection_coefficient, make_grid,
                                                run_realisation, sheet_beam_wave)
from reflection_holo.geometry.refraction import delta_K_per_A, theta_int_from_ext_rad
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.structure.oxide import ContinuumOxideSpec

E_KEV = 200.0
L12 = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (continuum oxide; L8/E9 demo values)"
LATTICE_LABEL = "ASSUMPTION B2"
THETA_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7 (external glancing angle)"
THETA_B32 = 16.1347e-3            # rad, (0,0,8) external angle at the IAM MIP (B32; E9 out:10)
V_OX = 10.34                      # V, IAM at 2.20 g/cm^3 (E9 out:166)
LABEL_KEYS = ("thickness", "density", "consumed_layers", "V_real", "V_imag", "vacuum_edge",
              "interface", "amorphous_si")
NO_ABS = PhysicalAbsorption(model="proportional", ratio=0.0,
                            label="TEST_ONLY: no physical absorption of the substrate")


def near_rounding_boundary(*, t_A, N, rho, t_a, tt=None, tn=None) -> bool:
    """TEST helper (audit A8 m4): True when some terrace's consumed-layer count lies within
    MIN_ROUNDING_MARGIN_LAYERS of its rounding boundary, so that the fixtures state the
    acknowledgement exactly when it is needed (the gate: tests/structure/test_oxide_structure_a8_fixes.py)."""
    from reflection_holo.structure.oxide import rounding_margin
    return any(rounding_margin(thickness_A=t, density_g_cm3=rho, amorphous_si_thickness_A=t_a,
                               consumed_layers=n, a_A=A_SI_A)["near_boundary"]
               for t, n in zip(tt or (t_A,), tn or (N,)))


def oxide_spec(*, t_A=20.0, N=7, V=V_OX, Vi=0.40, w_v=0.5, w_i=0.5, rho=2.20, t_a=0.0,
               Va=None, Vai=None, tt=None, tn=None, flag=False, iflag=False, ack=None,
               nc_ack=False, labels=None) -> ContinuumOxideSpec:
    """flag / iflag: the TEST_ONLY sharp vacuum-edge / interface flags (stated by the caller);
    ack: rounding_boundary_acknowledged, by default stated exactly when needed
    (near_rounding_boundary); nc_ack: nonconformal_sublayer_acknowledged (audit A9b M1; stated by
    the caller)."""
    lab = {k: L12 for k in LABEL_KEYS}
    if t_a > 0:
        lab["amorphous_si_potential"] = L12
    if tt is not None or tn is not None:
        lab["overrides"] = L12
    if labels:
        lab.update(labels)
    if ack is None:
        ack = near_rounding_boundary(t_A=t_A, N=N, rho=rho, t_a=t_a, tt=tt, tn=tn)
    return ContinuumOxideSpec(material="amorphous SiO2", thickness_A=t_A, density_g_cm3=rho,
                              consumed_layers=N, V_real_V=V, V_imag_V=Vi, vacuum_edge_width_A=w_v,
                              interface_width_A=w_i, amorphous_si_thickness_A=t_a,
                              amorphous_si_V_real_V=Va, amorphous_si_V_imag_V=Vai,
                              terrace_thickness_A=tt, terrace_consumed_layers=tn,
                              sharp_edge_test_flag=flag, sharp_interface_test_flag=iflag,
                              rounding_boundary_acknowledged=ack,
                              nonconformal_sublayer_acknowledged=nc_ack, labels=lab)


def oxide_only_case(*, w_v, dx, dz=1.0, propagator="exact", H=48.0, edge=8.0, gap=2.0,
                    absorber_A=15.0, clean_A=110.0, top_A=10.0, W0=100.0, depth_top_ray_A=20.0,
                    buildup_A=20.0, entrance_A=10.0, t_A=20.0, N=7):
    """Oxide-only control cell (E9 M4): the continuum oxide on a substrate that carries the SAME
    potential V_OX (TEST_ONLY), so the only potential step is the layer's vacuum edge (sharp with
    the TEST_ONLY flag, or graded). Geometry as tests/forward/ladder_cases.rung1_case (the surface
    is the top of the layer); L also satisfies the overlayer build-up assertion."""
    theta = THETA_B32
    th_int = theta_int_from_ext_rad(theta, E_KEV, V_OX)
    flag = w_v < 0.5
    # the substrate carries V_OX, so the interface is no potential step: sharp with the TEST_ONLY
    # interface flag (audit A8 m5 made the flag necessary; the fixture is unchanged)
    spec = oxide_spec(t_A=t_A, N=N, Vi=0.0, w_v=w_v, w_i=0.0, flag=flag, iflag=True,
                      labels=dict(vacuum_edge="TEST_ONLY: sharp or narrow edge for the Fresnel "
                                              "validation (E9 M4)") if flag else None)
    dep = clean_A + absorber_A
    z_top = (gap + H) / np.tan(theta)
    z_bot = gap / np.tan(theta)
    L_need = max(z_top + depth_top_ray_A / np.tan(th_int),
                 z_bot + (t_A + 1.0) / np.tan(theta) + buildup_A / np.tan(th_int))
    L = float(np.ceil((L_need + 1.0) / dz) * dz)
    vac = float(np.ceil(H + gap + L * np.tan(theta) + 2.0))
    cell0 = build_continuum_oxide_cell(
        extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0], terrace_heights_A=[0.0],
        crystal_length_z_A=L - entrance_A, vacuum_above_A=vac, depth_below_A=dep,
        bulk_absorber_A=absorber_A, top_absorber_A=top_A, entrance_vacuum_z_A=entrance_A,
        oxide=spec, lattice_parameter_A=A_SI_A, lattice_parameter_label=LATTICE_LABEL)
    nx = int(np.ceil(cell0.extent_x_A / dx))
    top = top_A + nx * dx - cell0.extent_x_A          # the top absorber absorbs the rounding
    cell = build_continuum_oxide_cell(
        extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0], terrace_heights_A=[0.0],
        crystal_length_z_A=L - entrance_A, vacuum_above_A=vac, depth_below_A=dep,
        bulk_absorber_A=absorber_A, top_absorber_A=top, entrance_vacuum_z_A=entrance_A,
        oxide=spec, lattice_parameter_A=A_SI_A, lattice_parameter_label=LATTICE_LABEL)
    sub = ContinuumTerracePotential(cell, V0_V=V_OX,
                                    V0_label="TEST_ONLY: substrate at the oxide potential "
                                             "(oxide-only control, E9 M4)",
                                    physical_absorption=NO_ABS, surface_profile="sharp")
    pot = ContinuumOxidePotential(sub, oxide=spec)
    x_top = cell.metadata["terraces"][0]["oxide"]["top_x_A"]
    beam = SheetBeam(height_A=H, edge_A=edge, x_bottom_A=x_top + gap, theta_in_ext_rad=theta,
                     theta_label=THETA_LABEL)
    params = MultisliceParams(energy_keV=E_KEV, nx=nx, ny=1, dz_A=dz, propagator=propagator,
                              band_limit="2/3", backend="numpy", precision="complex128",
                              threads=4, absorber=NumericalAbsorber(strength_V=W0, profile="sin2"),
                              theta_out_ext_rad=theta, buildup_depth_A=buildup_A,
                              working_reflections_hkl=())
    return cell, pot, beam, params, x_top


def exact_graded_edge_r(theta_ext_rad: float, U_V: float, w_A: float, *, step_A: float = 0.002,
                        span: float = 8.0) -> complex:
    """Exact 1-D reflection coefficient of the erf-graded vacuum edge (DERIVED_HERE; the transfer
    matrix of audit A8 C6, SP/a8/a8_analytic.py): the normal-component equation
    psi'' + kx(x)^2 psi = 0 with kx^2 = k1^2 + dK^2 E(x), E(x) = erfc(x/(sqrt(2) w))/2, in
    piecewise-constant layers of step_A from -span w to +span w; r at x = 0. A8: converged to
    1e-4 relative in |r|^2 at step 0.004-0.001 A and span 8-12 (1.9545e-9 at 16.1347 mrad,
    1.8345e-9 at 16.1751 mrad, w = 0.5 A)."""
    import math
    k1 = 2 * np.pi / wavelength_A(E_KEV) * np.sin(theta_ext_rad)
    dK2 = delta_K_per_A(E_KEV, U_V) ** 2
    edges = np.arange(-span * w_A, span * w_A + step_A, step_A)
    xm = 0.5 * (edges[1:] + edges[:-1])
    E = np.array([0.5 * math.erfc(x / (math.sqrt(2) * w_A)) for x in xm])
    kx = np.sqrt(k1 ** 2 + dK2 * E + 0j)
    k_sub = np.sqrt(k1 ** 2 + dK2 + 0j)
    psi = np.exp(-1j * k_sub * edges[0])
    dpsi = -1j * k_sub * psi
    for kk in kx:
        c, sn = np.cos(kk * step_A), np.sin(kk * step_A)
        psi, dpsi = psi * c + dpsi * sn / kk, -psi * kk * sn + dpsi * c
    x1 = edges[-1]
    a_in = 0.5 * (psi - dpsi / (1j * k1)) * np.exp(1j * k1 * x1)
    b_out = 0.5 * (psi + dpsi / (1j * k1)) * np.exp(-1j * k1 * x1)
    return complex(b_out / a_in)


def oxide_only_measure(**kw) -> dict:
    """r at the central incident bin (flat_reflection_coefficient, reference plane = the top of
    the layer) against the single-edge Fresnel coefficient for V_OX."""
    cell, pot, beam, params, xs = oxide_only_case(**kw)
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    lam = wavelength_A(E_KEV)
    grid = make_grid(cell, nx=params.nx, ny=1)
    psi0 = sheet_beam_wave(beam, grid, lam)
    res = flat_reflection_coefficient(ew, psi0, x_surface_A=xs, propagator=params.propagator,
                                      rel_threshold=0.5)
    q1 = 2 * np.pi * res["f_per_A"]
    dK = delta_K_per_A(E_KEV, V_OX)
    ra = analytic_step_reflection(q1, dK)
    j = int(np.argmax(res["weight"]))
    q2 = np.sqrt(q1[j] ** 2 + dK ** 2)
    return dict(r=complex(res["r"][j]), r_analytic=float(ra[j]), q1=float(q1[j]), q2=float(q2),
                theta_bin_rad=float(np.arcsin(res["f_per_A"][j] * lam)),
                dx=cell.extent_x_A / params.nx, nx=params.nx, ew=ew,
                n_slices=int(round(cell.length_z_A / params.dz_A)),
                time_s=ew.metadata["timing_s"]["total"])


# -------------------------------------------------------------------------------------------------
# Atomistic Si(001) cells with the continuum oxide (tests (c) and (d) of report E4)
# -------------------------------------------------------------------------------------------------
AZ100_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 8 (beam azimuth [100])"
STATIC = "TEST_ONLY: static lattice (no frozen phonons)"


def kirkland_theta_0008() -> tuple[float, float]:
    """(theta_ext, V0_mip): the (0,0,8) specular condition with the Kirkland IAM MIP (B32)."""
    from abtem.parametrizations import KirklandParametrization

    from reflection_holo.geometry.specular import specular_condition_for
    F0 = float(KirklandParametrization().projected_scattering_factor("Si")(np.array([0.0]))[0])
    V0 = 8.0 / A_SI_A ** 3 * F0
    sc = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E_KEV, V0_V=V0, a_A=A_SI_A)
    return float(sc.theta_ext), float(V0)


def atomistic_case(*, oxide, r, edges="transverse", layers=(0,), widths=None, boundary=0,
                   edge_periods=1, extra_length_A=0.0, H=8.0, edge=2.0, gap=2.0, buildup=20.0,
                   absorber=15.0, top=10.0, max_pixel=0.2263, precision="complex128",
                   length_for_oxide=None):
    """Si(001) at [100] (B4 in scope for a/4 at the specular beam), Kirkland static lattice with
    TEST_ONLY proportional absorption r, (0,0,8) condition, optional continuum oxide (spec or None).
    The cell length is the one the OVERLAYER build-up assertion needs for `length_for_oxide` (a
    spec; so that runs with and without the layer share the same length) plus extra_length_A."""
    from reflection_holo.forward.cell import build_reflection_cell
    from reflection_holo.forward.multislice import AtomicPotential, fft_friendly
    from reflection_holo.structure import Staircase, build_si001_terraces
    from reflection_holo.structure.oxide import consumed_si_fraction
    theta, V0 = kirkland_theta_0008()
    th_int = theta_int_from_ext_rad(theta, E_KEV, V0)
    q = A_SI_A / 4
    p = A_SI_A                                           # in-plane period along the beam at [100]
    dz = p / 4
    depth = absorber + buildup + 1.0
    ref = length_for_oxide if length_for_oxide is not None else oxide
    f = consumed_si_fraction(2.20, A_SI_A)
    # layer top above the kept top atomic plane: (1 - f) t + N a/4 + a/8 (the stack is placed from
    # the Si equivalent boundary a/8 above the pre-oxidation top plane; audit A8 M2)
    stack = 0.0 if ref is None else (1.0 - f) * ref.thickness_A + ref.consumed_layers * q + q / 2
    N = 0 if oxide is None else oxide.consumed_layers
    span = (max(layers) - min(layers)) * q
    sub = int(np.ceil(depth / q)) + 2 + N
    ent = 10 * dz
    z_first = (gap + span) / np.tan(theta)
    L_need = z_first + stack / np.tan(theta) + buildup / np.tan(th_int) + extra_length_A + 2 * dz
    if widths is None:
        periods_z = int(np.ceil((L_need - ent) / p))
        widths_ = (periods_z,)
        edge_p = edge_periods
    else:
        widths_ = tuple(widths)
        edge_p = int(np.ceil((L_need - ent) / p)) if edges == "parallel" else edge_periods
    st = Staircase(edges=edges, terrace_layers=tuple(layers), terrace_widths=widths_,
                   boundary_step_layers=boundary)
    s = build_si001_terraces(azimuth_uvw=(1, 0, 0), azimuth_label=AZ100_LABEL, staircase=st,
                             edge_periods=edge_p, substrate_layers=sub,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=oxide, vacuum_above_A=20.0, lattice_parameter_A=A_SI_A,
                             lattice_parameter_label=LATTICE_LABEL)
    Lz = ent + (s.cell_A[2, 2])
    # runs with and without the layer share the box: the vacuum above the highest surface is
    # larger by the reference stack where the layer is absent (same extent_x, same grid)
    stack_this = 0.0 if oxide is None else (1.0 - f) * oxide.thickness_A + N * q + q / 2
    vac = float(np.ceil(H + gap + Lz * np.tan(theta) + 2.0)) + (stack - stack_this)
    cell = build_reflection_cell(s, vacuum_above_A=vac, depth_below_A=depth,
                                 bulk_absorber_A=absorber, top_absorber_A=top,
                                 entrance_vacuum_z_A=ent)
    pa = PhysicalAbsorption(model="proportional", ratio=float(r),
                            label="TEST_ONLY: stands in for PROJECT_INPUT item 21 (r, as S5/E8)")
    pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=pa,
                          frozen_phonons=None, static_lattice_label=STATIC)
    if oxide is not None:
        pot = ContinuumOxidePotential(pot, oxide=oxide)
    xs_hi = cell.metadata["layout"]["highest_surface_x_A"]
    beam = SheetBeam(height_A=H, edge_A=edge, x_bottom_A=xs_hi + gap, theta_in_ext_rad=theta,
                     theta_label=THETA_LABEL)
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / max_pixel)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / max_pixel)))
    params = MultisliceParams(energy_keV=E_KEV, nx=nx, ny=ny, dz_A=dz, propagator="exact",
                              band_limit="2/3", backend="numpy", precision=precision, threads=4,
                              absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                              theta_out_ext_rad=theta, buildup_depth_A=buildup,
                              working_reflections_hkl=((0, 0, 8),))
    return dict(cell=cell, potential=pot, beam=beam, params=params, theta=theta, V0=V0,
                structure=s, stack_A=stack)


def specular_component(ew, theta, *, y_range=None, aperture_per_A=0.1) -> complex:
    """Fourier component of the specular beam at f_c = sin(theta)/lambda (k-space aperture of
    radius aperture_per_A, demodulated, summed over x and the y range; analysis.
    terrace_step_phase's read-out)."""
    from reflection_holo.forward.multislice import select_beam
    lam = ew.metadata["beam"]["wavelength_A"]
    fc = np.sin(theta) / lam
    sel = select_beam(ew, fx_centre_per_A=fc, fy_centre_per_A=0.0, radius_per_A=aperture_per_A)
    nx, ny = ew.psi.shape
    x = ew.x0_A + np.arange(nx) * ew.dx_A
    y = ew.y0_A + np.arange(ny) * ew.dy_A
    m = np.ones(ny, bool) if y_range is None else (y >= y_range[0]) & (y < y_range[1])
    return complex((sel * np.exp(-2j * np.pi * fc * x)[:, None])[:, m].sum() * ew.dx_A * ew.dy_A)


def windowed_reflection(ew, c, *, x_window_A, window_ramp_A=40.0, rel_threshold=0.5):
    """Reflection coefficient r(f) of the specular beam per incident bin (analysis.
    flat_reflection_coefficient, reference plane x_window_A) read in the VACUUM only: the exit
    wave is first multiplied by sin^2(pi/2 clip((x - x_window)/ramp, 0, 1)) (the vacuum-only
    read-out of rung 2 R2-B, tests/forward/ladder_cases.rung2_measure). Returns the central bin."""
    import dataclasses
    grid = make_grid(c["cell"], nx=c["params"].nx, ny=c["params"].ny)
    lam = wavelength_A(E_KEV)
    psi0 = sheet_beam_wave(c["beam"], grid, lam)
    x = grid.x_A()
    w = np.sin(0.5 * np.pi * np.clip((x - x_window_A) / window_ramp_A, 0.0, 1.0)) ** 2
    ew_w = dataclasses.replace(ew, psi=ew.psi * w[:, None])
    res = flat_reflection_coefficient(ew_w, psi0, x_surface_A=x_window_A,
                                      propagator=c["params"].propagator,
                                      rel_threshold=rel_threshold)
    j = int(np.argmax(res["weight"]))
    return dict(r=complex(res["r"][j]), f_per_A=float(res["f_per_A"][j]),
                theta_bin_rad=float(np.arcsin(lam * res["f_per_A"][j])), bins=res)
