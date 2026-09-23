"""Shared TEST_ONLY cases for the validation ladder (docs/05 section 4.4), used by the tests in
tests/forward and by the convergence study quoted in docs/agent_reports/M2_multislice_engine.md.
Not a test module. Every value standing in for a PROJECT_INPUT is labelled TEST_ONLY; the mean inner
potential of the continuum rungs is the repository's ASSUMPTION B1 value passed explicitly."""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import V0_SI_ASSUMPTION_V
from reflection_holo.forward.cell import build_continuum_cell
from reflection_holo.forward.multislice import (ContinuumTerracePotential, MultisliceParams,
                                                NumericalAbsorber, PhysicalAbsorption, SheetBeam,
                                                analytic_step_reflection,
                                                flat_reflection_coefficient, make_grid,
                                                run_realisation, sheet_beam_wave,
                                                terrace_step_phase)
from reflection_holo.geometry.refraction import (delta_K_per_A, k_internal_per_A,
                                                 theta_int_from_ext_rad)
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A

E_KEV = 200.0
V0 = V0_SI_ASSUMPTION_V                       # ASSUMPTION B1 (12.0 V), passed explicitly
V0_LABEL = "ASSUMPTION B1 (V0 = 12.0 V; PROJECT_INPUT item 20 not supplied)"
THETA_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7 (external glancing angle)"
NO_ABS = PhysicalAbsorption(model="proportional", ratio=0.0,
                            label="ASSUMPTION: no physical absorption in the refraction-only rungs "
                                  "(PROJECT_INPUT item 21 not supplied)")
THETA_0008 = 16.47e-3                         # docs/05: (0,0,8) specular condition at V0 = 12 V


def rung1_case(theta, *, dx, dz, propagator, precision="complex128", H=48.0, edge=8.0, gap=2.0,
               absorber_A=15.0, clean_A=110.0, top_A=10.0, W0=100.0, depth_top_ray_A=20.0,
               buildup_A=20.0, entrance_A=10.0):
    """Flat half-space of constant V0 below x_s = clean + absorber; sheet beam of height H.

    L is chosen so that at the exit plane the refracted ray of the TOP edge of the beam is
    depth_top_ray_A below the surface (whole refracted sheet inside the clean crystal) and the
    build-up assertion (docs/05 4.3 item 4) holds; the vacuum margin satisfies item 2."""
    th_int = theta_int_from_ext_rad(theta, E_KEV, V0)
    dep = clean_A + absorber_A
    z_top = (gap + H) / np.tan(theta)
    z_bot = gap / np.tan(theta)
    L_need = max(z_top + depth_top_ray_A / np.tan(th_int), z_bot + buildup_A / np.tan(th_int))
    L = float(np.ceil((L_need + 1.0) / dz) * dz)
    vac = float(np.ceil(H + gap + L * np.tan(theta) + 2.0))
    ext = dep + vac + top_A
    nx = int(np.ceil(ext / dx))
    top = nx * dx - dep - vac                   # top absorber absorbs the rounding
    cell = build_continuum_cell(extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0],
                                terrace_heights_A=[0.0], crystal_length_z_A=L - entrance_A,
                                vacuum_above_A=vac, depth_below_A=dep, bulk_absorber_A=absorber_A,
                                top_absorber_A=top, entrance_vacuum_z_A=entrance_A)
    pot = ContinuumTerracePotential(cell, V0_V=V0, V0_label=V0_LABEL, physical_absorption=NO_ABS,
                                    surface_profile="sharp")
    beam = SheetBeam(height_A=H, edge_A=edge, x_bottom_A=dep + gap, theta_in_ext_rad=theta,
                     theta_label=THETA_LABEL)
    params = MultisliceParams(energy_keV=E_KEV, nx=nx, ny=1, dz_A=dz, propagator=propagator,
                              band_limit="2/3", backend="numpy", precision=precision, threads=4,
                              absorber=NumericalAbsorber(strength_V=W0, profile="sin2"),
                              theta_out_ext_rad=theta, buildup_depth_A=buildup_A,
                              working_reflections_hkl=())       # continuum cell: no lattice
    return cell, pot, beam, params, dep


def rung1_measure(theta, **kw):
    """Run rung 1 and return the reflection coefficient at the central incident bin versus the
    analytic step barrier, and the refracted angle versus SM04."""
    cell, pot, beam, params, xs = rung1_case(theta, **kw)
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    lam = wavelength_A(E_KEV)
    k = k_ang_per_A(E_KEV)
    dK = delta_K_per_A(E_KEV, V0)
    grid = make_grid(cell, nx=params.nx, ny=1)
    psi0 = sheet_beam_wave(beam, grid, lam)
    res = flat_reflection_coefficient(ew, psi0, x_surface_A=xs, propagator=params.propagator,
                                      rel_threshold=0.5)
    q1 = 2 * np.pi * res["f_per_A"]
    ra = analytic_step_reflection(q1, dK)
    j = int(np.argmax(res["weight"]))
    r_c, ra_c = res["r"][j], ra[j]
    # refracted angle: local wavenumber at the centre of the refracted sheet (wide beam, locally a
    # plane wave): |psi|^2-weighted phase gradient over the central third of the sheet
    x = grid.x_A()
    psi = ew.psi[:, 0].astype(np.complex128)
    inside = (x > cell.metadata["layout"]["bulk_absorber_x_A"][1] + 2.0) & (x < xs - 2.0)
    amp = np.abs(psi) * inside
    core = amp > 0.9 * amp.max()
    xc = x[core]
    sel = inside & (x > xc.min() + (xc.max() - xc.min()) / 3) & (x < xc.max() - (xc.max() - xc.min()) / 3)
    grad = np.gradient(np.unwrap(np.angle(psi)), grid.dx_A)
    w = np.abs(psi) ** 2 * sel
    q2_meas = -float(np.sum(w * grad) / np.sum(w))
    q1_c = k * np.sin(theta)
    q2_ana = float(np.sqrt(q1_c**2 + dK**2))
    kint = k_internal_per_A(E_KEV, V0)
    th_int_meas = float(np.arcsin(q2_meas / kint))
    th_int_sm04 = float(theta_int_from_ext_rad(theta, E_KEV, V0))
    return dict(theta_mrad=theta * 1e3, dx=params.nx and cell.extent_x_A / params.nx,
                dz=params.dz_A, nx=params.nx, n_slices=int(round(cell.length_z_A / params.dz_A)),
                q1_centre=float(q1[j]), r=complex(r_c), r_analytic=float(ra_c),
                amp_rel_err=float(abs(r_c) / abs(ra_c) - 1.0),
                phase_err_rad=float(np.angle(r_c / ra_c)), phase_rad=float(np.angle(r_c)),
                bins_amp_rel_err_max=float(np.max(np.abs(np.abs(res["r"]) / np.abs(ra) - 1))),
                bins_phase_err_max=float(np.max(np.abs(np.angle(res["r"] / ra)))),
                q2_meas=q2_meas, q2_analytic=q2_ana,
                theta_int_meas_mrad=th_int_meas * 1e3, theta_int_sm04_mrad=th_int_sm04 * 1e3,
                theta_int_err_mrad=(th_int_meas - th_int_sm04) * 1e3,
                time_s=ew.metadata["timing_s"]["total"], ew=ew)


def rung3_case(theta, h, *, dx, dy, dz, propagator="exact", precision="complex128",
               terrace_width_A=40.0, H=8.0, edge=2.0, gap=2.0, absorber_A=15.0, clean_A=25.0,
               top_A=10.0, W0=100.0, buildup_A=20.0, depth_top_ray_A=20.0, entrance_A=10.0):
    """Two constant-potential terraces with step edges PARALLEL to the beam: terrace A (y in
    [0, W)) at height 0, terrace B (y in [W, 2W)) at height h (h < 0 reverses the step). The exit
    plane is where the refracted ray of the top edge of the beam is depth_top_ray_A below the LOWER
    surface (complete scattering of the reflected packet on both terraces)."""
    th_int = theta_int_from_ext_rad(theta, E_KEV, V0)
    dep = clean_A + absorber_A
    s_lo = dep
    s_hi = dep + abs(h)
    xb = s_hi + gap
    z_top = (xb + H - s_lo) / np.tan(theta)
    z_first_low = (xb - s_lo) / np.tan(theta)
    L_need = max(z_top + depth_top_ray_A / np.tan(th_int),
                 z_first_low + buildup_A / np.tan(th_int))
    L = float(np.ceil((L_need + 1.0) / dz) * dz)
    vac = float(np.ceil(H + gap + L * np.tan(theta) + 2.0))
    ext = s_hi + vac + top_A
    nx = int(np.ceil(ext / dx))
    top = nx * dx - s_hi - vac
    Ly = 2 * terrace_width_A
    ny = int(round(Ly / dy))
    cell = build_continuum_cell(extent_y_A=Ly, terrace_y_bounds_A=[0.0, terrace_width_A, Ly],
                                terrace_heights_A=[0.0, h], crystal_length_z_A=L - entrance_A,
                                vacuum_above_A=vac, depth_below_A=dep, bulk_absorber_A=absorber_A,
                                top_absorber_A=top, entrance_vacuum_z_A=entrance_A)
    pot = ContinuumTerracePotential(cell, V0_V=V0, V0_label=V0_LABEL, physical_absorption=NO_ABS,
                                    surface_profile="sharp")
    beam = SheetBeam(height_A=H, edge_A=edge, x_bottom_A=xb, theta_in_ext_rad=theta,
                     theta_label=THETA_LABEL)
    params = MultisliceParams(energy_keV=E_KEV, nx=nx, ny=ny, dz_A=dz, propagator=propagator,
                              band_limit="2/3", backend="numpy", precision=precision, threads=4,
                              absorber=NumericalAbsorber(strength_V=W0, profile="sin2"),
                              theta_out_ext_rad=theta, buildup_depth_A=buildup_A,
                              working_reflections_hkl=())       # continuum cell: no lattice
    return cell, pot, beam, params


def rung3_measure(theta, h, *, region_fraction=0.5, aperture_per_A=0.5, **kw):
    """Step phase phi(B) - phi(A) of the specular beam selected in k-space (circular aperture of
    radius aperture_per_A about (+sin(theta)/lambda, 0)) on the central region_fraction of each
    terrace (B at height h relative to A)."""
    cell, pot, beam, params = rung3_case(theta, h, **kw)
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    W = cell.extent_y_A / 2
    m = 0.5 * (1 - region_fraction) * W
    res = terrace_step_phase(ew, theta_out_ext_rad=theta, aperture_radius_per_A=aperture_per_A,
                             upper_y_range_A=(W + m, 2 * W - m), lower_y_range_A=(m, W - m))
    lam = wavelength_A(E_KEV)
    expected = -4 * np.pi / lam * h * np.sin(theta)
    res.update(h_A=h, expected_rad=float(expected),
               expected_wrapped_rad=float((expected + np.pi) % (2 * np.pi) - np.pi),
               err_rad=float((res["delta_phi_rad"] - expected + np.pi) % (2 * np.pi) - np.pi),
               nx=params.nx, ny=params.ny, dx=cell.extent_x_A / params.nx,
               dy=cell.extent_y_A / params.ny, dz=params.dz_A, n_slices=int(round(
                   cell.length_z_A / params.dz_A)), time_s=ew.metadata["timing_s"]["total"],
               ew=ew)
    return res
