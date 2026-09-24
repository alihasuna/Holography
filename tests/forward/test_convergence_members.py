"""Convergence members on the multislice engine: the azimuthally tilted sheet beam (Bloch form),
the member runs and the band assertion for every tilted direction (report E3 sections 2 and 5;
H2 N3; PROJECT_INPUT item 3).

TEST_ONLY values: glancing angle (item 7), convergence semi-angle and quadrature (item 3), cell
sizes, grids. V0 is the repository's ASSUMPTION B1 value passed explicitly (ladder_cases).

Tolerances (fixed before running, DERIVED_HERE):
* identical code paths: bit-for-bit equality (np.array_equal);
* the analytic Bloch phase of a y-uniform cell with the Fresnel propagator: the tilted and
  untilted envelopes differ ONLY by exp(-i pi lambda f_y^2 L_z) (the kernels factorise, and every
  transmission function is y-independent), so the residual is rounding: 1e-11 relative in
  complex128 over ~10^3 slices (a few ulp per FFT pass, 4 passes per slice);
* the y-mirror symmetry of a mirror-symmetric cell: the +u_y and -u_y runs are exact mirror images
  in exact arithmetic (the kernel, the band mask and the potential are all even in f_y and y), so
  1e-11 relative again;
* the explicit Fourier-component launch of a commensurate tilt with the band mask rolled onto the
  same physical passband performs the same arithmetic in another order: 1e-11 relative.
"""
import dataclasses

import numpy as np
import pytest

from ladder_cases import E_KEV, NO_ABS, THETA_LABEL, V0, V0_LABEL
from reflection_holo.forward.cell import build_continuum_cell
from reflection_holo.forward.multislice import (ContinuumTerracePotential, MultisliceParams,
                                                NumericalAbsorber, SheetBeam, make_grid,
                                                run_realisation, sheet_beam_wave)
from reflection_holo.forward.multislice.backend import get_backend
from reflection_holo.forward.multislice.convergence import (check_members, member_beam,
                                                            member_params, quadrature_sha256,
                                                            simulate_member)
from reflection_holo.forward.multislice.engine import propagate_slices, reflection_setup
from reflection_holo.forward.multislice.grid import band_limit_mask
from reflection_holo.forward.multislice.illumination import (BlochShiftedGrid, TiltedSheetBeam,
                                                             bloch_fy_per_A)
from reflection_holo.forward.multislice.potentials import absorber_profile_V
from reflection_holo.forward.multislice.propagator import propagator_kernel
from reflection_holo.geometry.errors import SamplingError
from reflection_holo.geometry.refraction import theta_int_from_ext_rad
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.optics.coherence import ConvergenceMember, ConvergenceQuadrature

TH0 = 16.47e-3                                    # TEST_ONLY: (0,0,8) condition at V0 = 12 V
LAM = wavelength_A(E_KEV)
TILT_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 3 (convergence member)"
REL = 1e-11


def small_case(*, ny, y_bounds, heights, dx=0.2, dz=8.0, propagator="exact",
               theta_span=(TH0, TH0), H=8.0, edge=2.0, gap=2.0, buildup=20.0,
               precision="complex128", Ly=None):
    """Continuum cell sized for every glancing angle in theta_span (docs/05 4.3 items 1-4 hold
    for each): terraces along y (edges parallel to the beam), sheet beam of height H."""
    th_lo, th_hi = theta_span
    th_int_lo = theta_int_from_ext_rad(th_lo, E_KEV, V0)
    hmax = max(heights) - min(heights)
    absorber, clean, top = 10.0, buildup + 5.0, 10.0
    dep = absorber + clean
    ent = 2 * dz
    xb_rel = hmax + gap                          # beam bottom above the lowest surface
    z_top = (xb_rel + H) / np.tan(th_lo)
    z_first = xb_rel / np.tan(th_lo)
    L_need = max(z_top, z_first + buildup / np.tan(th_int_lo)) + 2 * dz
    L = float(np.ceil(L_need / dz) * dz)
    vac = float(np.ceil(hmax + H + gap + L * np.tan(th_hi) + 2.0))
    ext = dep + hmax + vac + top
    nx = int(np.ceil(ext / dx))
    top = nx * dx - dep - hmax - vac
    Ly = Ly if Ly is not None else float(y_bounds[-1])
    cell = build_continuum_cell(extent_y_A=Ly, terrace_y_bounds_A=list(y_bounds),
                                terrace_heights_A=list(heights), crystal_length_z_A=L - ent,
                                vacuum_above_A=vac, depth_below_A=dep, bulk_absorber_A=absorber,
                                top_absorber_A=top, entrance_vacuum_z_A=ent)
    pot = ContinuumTerracePotential(cell, V0_V=V0, V0_label=V0_LABEL, physical_absorption=NO_ABS,
                                    surface_profile="sharp")
    beam = SheetBeam(height_A=H, edge_A=edge, x_bottom_A=cell.metadata["layout"]
                     ["highest_surface_x_A"] + gap, theta_in_ext_rad=TH0, theta_label=THETA_LABEL)
    params = MultisliceParams(energy_keV=E_KEV, nx=nx, ny=ny, dz_A=dz, propagator=propagator,
                              band_limit="2/3", backend="numpy", precision=precision, threads=2,
                              absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                              theta_out_ext_rad=TH0, buildup_depth_A=buildup,
                              working_reflections_hkl=())
    return cell, pot, beam, params


def tilted(beam, uy, theta=None):
    return TiltedSheetBeam(height_A=beam.height_A, edge_A=beam.edge_A, x_bottom_A=beam.x_bottom_A,
                           theta_in_ext_rad=beam.theta_in_ext_rad if theta is None else theta,
                           theta_label=beam.theta_label, direction_cosine_y=uy,
                           tilt_label=TILT_LABEL)


def rel_err(a, b):
    return float(np.max(np.abs(a - b)) / np.max(np.abs(b)))


# ---------------------------------------------------------------------------------------------
# the tilted beam and the Bloch form
# ---------------------------------------------------------------------------------------------
def test_zero_tilt_reproduces_the_untilted_exit_wave_bit_for_bit():
    """A TiltedSheetBeam with u_y = 0 (one direction, the central one) takes the untilted code path:
    the exit wave equals the SheetBeam run exactly (single-direction reproduction)."""
    cell, pot, beam, params = small_case(ny=4, y_bounds=[0.0, 5.0, 10.0], heights=[0.0, 1.3575])
    a = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    b = run_realisation(cell, potential=pot, beam=tilted(beam, 0.0), params=params, realisation=0,
                        seed=None)
    assert np.array_equal(a.psi, b.psi)
    assert b.metadata["bloch"]["fy_per_A"] == 0.0 and "bloch" not in a.metadata
    # the same through the member interface: a member with zero offsets
    q = ConvergenceQuadrature(semi_angle_rad=1e-5, semi_angle_label=TILT_LABEL,
                              source_profile="uniform_line", n_radial=1, n_azimuthal=None,
                              line_azimuth_rad=0.0, design_phase_extent_rad=0.0,
                              design_curvature_rad=0.0, tolerance=1e-9)
    m = q.member(0)                                       # the single Gauss node xi = 0
    assert (m.t_a_rad, m.t_b_rad, m.weight) == (0.0, 0.0, 1.0)
    c = run_realisation(cell, potential=pot, beam=member_beam(beam, m, q),
                        params=member_params(params, m, TH0), realisation=0, seed=None)
    assert np.array_equal(a.psi, c.psi)


def test_bloch_phase_of_a_y_uniform_cell_is_analytic_with_the_fresnel_propagator():
    """y-uniform cell, Fresnel kernel exp(-i pi lambda dz (f_x^2 + f_y^2)): with the y tilt carried
    at f_y (non-commensurate on purpose) the envelope is the untilted one times
    exp(-i pi lambda f_y^2 L_z) exactly (DERIVED_HERE, module docstring)."""
    cell, pot, beam, params = small_case(ny=4, y_bounds=[0.0, 10.0], heights=[0.0],
                                         propagator="fresnel")
    uy = 0.37 * LAM / cell.extent_y_A                     # 0.37 of a grid step: incommensurate
    a = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    b = run_realisation(cell, potential=pot, beam=tilted(beam, uy), params=params, realisation=0,
                        seed=None)
    fy = uy / LAM
    want = a.psi * np.exp(-1j * np.pi * LAM * fy ** 2 * cell.length_z_A)
    assert rel_err(b.psi, want) <= REL
    assert b.metadata["bloch"]["fy_per_A"] == pytest.approx(fy, rel=1e-15)
    assert b.metadata["band_limit"]["azimuthal_tilt"]["native_fy_of_every_beam_per_A"] == 0.0


def test_opposite_y_tilts_are_mirror_images_on_a_mirror_symmetric_cell():
    """Terraces symmetric under y -> -y (mod L_y): the +u_y and -u_y runs are mirror images,
    u_-(x, y) = u_+(x, -y), with the exact propagator and a y-structured potential."""
    Ly, ny = 12.0, 12
    cell, pot, beam, params = small_case(ny=ny, y_bounds=[0.0, 3.0, 9.0, Ly],
                                         heights=[0.0, 1.3575, 0.0])
    # pixel centres y_j = j dy; the terrace [3, 9) is symmetric about y = 6 = L_y/2, i.e. under
    # j -> -j mod ny composed with the half-period shift: mirror about y = 0 maps [3, 9) onto
    # [-9, -3) = [3, 9) mod 12
    uy = 0.61 * LAM / Ly
    p = run_realisation(cell, potential=pot, beam=tilted(beam, uy), params=params,
                        realisation=0, seed=None).psi
    m = run_realisation(cell, potential=pot, beam=tilted(beam, -uy), params=params,
                        realisation=0, seed=None).psi
    idx = (-np.arange(ny)) % ny
    assert rel_err(m, p[:, idx]) <= REL
    assert rel_err(m, p) > 1e-6                           # the tilt does act on this cell


def test_commensurate_tilt_equals_an_explicit_fourier_component_launch():
    """For f_y = m/L_y the Bloch run equals launching exp(2 pi i m y/L_y) u_0 explicitly with the
    native kernels and the band mask rolled onto the same physical passband (the explicit launch of
    a tilted plane wave on the periodic grid): psi_explicit = exp(2 pi i f_y y) u_Bloch."""
    Ly, ny, mfy = 12.0, 12, 1
    cell, pot, beam, params = small_case(ny=ny, y_bounds=[0.0, 3.0, 9.0, Ly],
                                         heights=[0.0, 1.3575, 0.0])
    uy = mfy * LAM / Ly
    bl = run_realisation(cell, potential=pot, beam=tilted(beam, uy), params=params,
                         realisation=0, seed=None)
    s = reflection_setup(cell, potential=pot, beam=beam, params=params)
    grid, N = s["grid"], s["n_slices"]
    be = get_backend("numpy", "complex128", 2)
    mask = band_limit_mask(grid, params.band_limit)
    rolled = np.roll(mask, mfy, axis=1)                   # passband centred on f_y = m/L_y
    P_full, _ = propagator_kernel(grid, dz_A=params.dz_A, wavelength_A=LAM,
                                  kind=params.propagator, band_mask=rolled)
    P_half, _ = propagator_kernel(grid, dz_A=0.5 * params.dz_A, wavelength_A=LAM,
                                  kind=params.propagator, band_mask=rolled)
    sig = s["bc"]["sigma_rad_per_VA"]
    W = absorber_profile_V(grid, cell, params.absorber)
    absfac = np.exp(-sig * W * params.dz_A)[:, None]
    y = grid.y_A()
    psi0 = sheet_beam_wave(beam, grid, LAM) * np.exp(2j * np.pi * mfy * y / Ly)[None, :]
    realised = pot.realise(grid=grid, dz_A=params.dz_A, n_slices=N, backend=be, rng=None)
    ex, _ = propagate_slices(psi0, realised=realised, n_slices=N, backend=be, P_full=P_full,
                             P_half=P_half, band_mask=mask.astype(float), sigma=sig,
                             absorber_factor=absfac)
    want = ex * np.exp(-2j * np.pi * mfy * y / Ly)[None, :]
    assert rel_err(bl.psi, want) <= REL


def test_bloch_grid_shifts_only_the_propagator_frequencies():
    cell, pot, beam, params = small_case(ny=4, y_bounds=[0.0, 10.0], heights=[0.0])
    g = make_grid(cell, nx=params.nx, ny=params.ny)
    bg = BlochShiftedGrid(g, 0.0123)
    assert np.array_equal(bg.fx(), g.fx()) and np.allclose(bg.fy() - g.fy(), 0.0123, rtol=0,
                                                          atol=1e-15)
    assert bg.nx == g.nx and bg.dy_A == g.dy_A
    assert bloch_fy_per_A(beam, LAM) == 0.0
    with pytest.raises(TypeError):
        bloch_fy_per_A("beam", LAM)
    for bad in (float("nan"), 0.25, True, None):
        with pytest.raises((ValueError, TypeError)):
            tilted(beam, bad)
    with pytest.raises(ValueError, match="label"):
        TiltedSheetBeam(height_A=8.0, edge_A=2.0, x_bottom_A=40.0, theta_in_ext_rad=TH0,
                        theta_label=THETA_LABEL, direction_cosine_y=1e-4, tilt_label="convergence")


# ---------------------------------------------------------------------------------------------
# members: band assertion for every tilted direction, independent runs
# ---------------------------------------------------------------------------------------------
def disc(alpha, n_r=2, n_az=6):
    return ConvergenceQuadrature(semi_angle_rad=alpha, semi_angle_label=TILT_LABEL,
                                 source_profile="uniform_disc", n_radial=n_r, n_azimuthal=n_az,
                                 line_azimuth_rad=None, design_phase_extent_rad=0.1,
                                 design_curvature_rad=0.0, tolerance=1e-3)


def test_band_assertion_holds_for_every_member_of_a_disc_quadrature():
    alpha = 0.5e-3
    cell, pot, beam, params = small_case(ny=4, y_bounds=[0.0, 5.0, 10.0], heights=[0.0, 1.3575],
                                         theta_span=(TH0 - alpha, TH0 + alpha))
    q = disc(alpha)
    recs = check_members(cell, potential=pot, beam=beam, params=params, quadrature=q)
    assert len(recs) == q.n_members == 12
    for r in recs:
        th = r["member"]["glancing_angle_rad"]
        rows = r["band"]["beams"]
        assert rows["incident_ext"]["theta_mrad"] == pytest.approx(th * 1e3, rel=1e-12)
        assert rows["outgoing_ext"]["theta_mrad"] == pytest.approx(th * 1e3, rel=1e-12)
        assert all(v["fraction_of_band"] <= 1.0 for v in rows.values())
        assert r["band"]["azimuthal_tilt"]["direction_cosine_y"] == r["member"]["t_b_rad"]
        assert r["geometry_passed"]
    ths = [r["member"]["glancing_angle_rad"] for r in recs]
    assert min(ths) < TH0 < max(ths) and max(ths) - min(ths) <= 2 * alpha * (1 + 1e-9)


def test_a_member_outside_the_band_is_refused_by_name():
    """dx = 0.45 A: the 2/3 band ends at lambda/(3 dx) = 18.6 mrad; the central 16.47 mrad passes,
    members of a 5 mrad disc reach 21.4 mrad and are refused (SamplingError naming the member)."""
    alpha = 5e-3
    cell, pot, beam, params = small_case(ny=4, y_bounds=[0.0, 10.0], heights=[0.0], dx=0.45,
                                         theta_span=(TH0 - alpha, TH0 + alpha))
    reflection_setup(cell, potential=pot, beam=beam, params=params)       # central passes
    with pytest.raises(SamplingError, match="convergence member"):
        check_members(cell, potential=pot, beam=beam, params=params, quadrature=disc(alpha))


def test_member_runs_are_independent_jobs_with_their_own_manifest(tmp_path):
    import json
    alpha = 0.5e-3
    cell, pot, beam, params = small_case(ny=4, y_bounds=[0.0, 5.0, 10.0], heights=[0.0, 1.3575],
                                         theta_span=(TH0 - alpha, TH0 + alpha), dx=0.25, dz=16.0)
    q = disc(alpha, n_r=1, n_az=3)
    waves_all = {}
    for k in (2, 0):                                      # any order: no shared state
        waves, man = simulate_member(cell, potential=pot, beam=beam, params=params, quadrature=q,
                                     member_index=k, realisations=1, seed=None,
                                     outputs_root=tmp_path / "outputs", run_name="conv",
                                     save_waves=True, config=None, input_paths=[],
                                     caller_record=dict(job="test"))
        m = json.loads(man.read_text())
        conv = m["extra"]["caller"]["convergence"]
        assert conv["member"]["index"] == k and conv["quadrature"]["n_members"] == 3
        assert conv["quadrature_sha256"] == quadrature_sha256(q, TH0)
        assert m["extra"]["caller"]["job"] == "test"
        assert m["seeds"] and m["threads"]["requested"] == 2 and m["repository"]["commit"]
        assert (tmp_path / "outputs" / "exit_waves" / f"conv_m{k:04d}_r0000.npz").is_file()
        waves_all[k] = waves[0]
        mem = q.member(k)
        assert waves[0].theta_in_ext_rad == mem.glancing_angle_rad(TH0)
        assert waves[0].metadata["bloch"]["direction_cosine_y"] == mem.t_b_rad
    # the same member run again in-process gives the same wave (deterministic, static lattice)
    b = run_realisation(cell, potential=pot, beam=member_beam(beam, q.member(2), q),
                        params=member_params(params, q.member(2), TH0), realisation=0, seed=None)
    assert np.array_equal(b.psi, waves_all[2].psi)
    with pytest.raises(ValueError, match="member index"):
        q.member(3)
    with pytest.raises(ValueError, match="theta_out"):
        check_members(cell, potential=pot, beam=beam,
                      params=dataclasses.replace(params, theta_out_ext_rad=TH0 * 1.01),
                      quadrature=q)
    with pytest.raises(TypeError):
        check_members(cell, potential=pot, beam=tilted(beam, 1e-5), params=params, quadrature=q)


def test_member_geometry_follows_the_stated_frame():
    m = ConvergenceMember(index=0, t_a_rad=2e-4, t_b_rad=-3e-4, weight=1.0)
    u = m.direction(TH0)
    assert np.linalg.norm(u) == pytest.approx(1.0, abs=1e-15)
    ta, tb = 2e-4, -3e-4
    exact = np.arcsin(np.sqrt(1 - ta ** 2 - tb ** 2) * np.sin(TH0) + ta * np.cos(TH0))
    assert m.glancing_angle_rad(TH0) == pytest.approx(exact, abs=1e-15)
    # t_a raises the glancing angle to first order; the second-order remainder is
    # sin(th0) (sqrt(1 - t^2) - cos t_a) + cos(th0) (t_a - sin t_a), |.| <= sin(th0) t_b^2/2 + t_a^3
    assert abs(m.glancing_angle_rad(TH0) - (TH0 + ta)) <= np.sin(TH0) * tb ** 2 / 2 + ta ** 3
    assert m.direction_cosine_y() == -3e-4
    tx, ty = m.tilt_simulation_frame(TH0)
    # theta = lambda (q - q0): q_x = u_x / lambda, so theta_x = u_x + sin(th0) < 0 for t_a > 0
    want_tx = -ta * np.cos(TH0) + np.sin(TH0) * (1 - np.sqrt(1 - ta ** 2 - tb ** 2))
    # u_x + sin(th0) cancels two numbers of size sin(th0): rounding of a few eps sin(th0) < 1e-16
    assert tx == pytest.approx(want_tx, abs=1e-16) and ty == -3e-4
