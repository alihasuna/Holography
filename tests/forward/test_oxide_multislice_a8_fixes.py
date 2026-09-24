"""Continuum oxide in the multislice engine: the fixes of report X4 after the audit A8 (forward level).

A8 M2  The interface overlap recorded by the builder (interface_overlap_A = f t + t_a - N a/4:
       positive = the continuum layer overlaps the kept atomistic crystal's top half-layer slab,
       negative = a gap) must be what the engine's potential contains. Measured on the engine's own
       arrays: the lower boundary x_c of the layer from ContinuumOxidePotential.layer_arrays
       (x_mid - integral of the laterally averaged layer potential below x_mid / its plateau: exact
       for any edge symmetric about x_c), the kept crystal's top atomic plane as the topmost peak
       of the laterally averaged AtomicPotential (3-point parabolic interpolation), whose
       equivalent boundary lies a/8 above it (the stated rule, structure.oxide.REFERENCE_PLANE).
       A priori tolerance: dx/2 = 0.01 A at dx = 0.02 A (the peak lies within half a pixel of the
       sampled maximum even without interpolation; the layer integral is exact to the alias
       exp(-2 pi^2 (w/dx)^2) = 0 at w = 0.5 A); E4's placement differs by a/8 = 0.679 A. Cases: A8's
       three (C9): 2.0 nm (7 layers), 1.5 nm (5), and 2.0 nm at 2.198 g/cm^3 (6 layers; the density
       moves the rounding); A8 measured +0.005, +0.513, +1.355 A with E4's placement.
A8 m6  The docs/05 4.3 item-4 assertion through the overlayer (forward.cell,
       item4_buildup_length_through_overlayer) refuses a cell long enough for the plain build-up
       length but not for the layer stack in addition (A8's mutation M13, the assertion ignoring
       the stack, passed every test before).
(A8 m1: the exact reflectivity of the 0.5 A edge is asserted in test_oxide_multislice.py; A8 m3:
test_memory_model.py.)
"""
import numpy as np
import pytest

from oxide_cases import LATTICE_LABEL, oxide_spec
from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import (ReflectionGeometryError, build_continuum_oxide_cell,
                                          build_reflection_cell, check_reflection_geometry)
from reflection_holo.geometry.refraction import theta_int_from_ext_rad

Q = A_SI_A / 4
DX = 0.02
OVERLAP_TOL_A = DX / 2                       # module docstring (a priori)


def _flat_terrace_profiles(spec):
    """Laterally and slice-averaged potentials (V) of the engine for one flat [100] terrace under
    the continuum oxide: the crystal (AtomicPotential, Kirkland, static, no absorption) and the
    layer (ContinuumOxidePotential.layer_arrays), on a grid of DX."""
    from reflection_holo.forward.multislice import (AtomicPotential, ContinuumOxidePotential,
                                                    PhysicalAbsorption, make_grid)
    from reflection_holo.forward.multislice.backend import get_backend
    from reflection_holo.structure import Staircase, build_si001_terraces
    st = Staircase(edges="transverse", terrace_layers=(0,), terrace_widths=(1,),
                   boundary_step_layers=0)
    s = build_si001_terraces(
        azimuth_uvw=(1, 0, 0), azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
        staircase=st, edge_periods=1, substrate_layers=24 + spec.consumed_layers,
        first_terrace_backbond_uvw=(1, 1, 0), termination="bulk", overlayer=spec,
        vacuum_above_A=25.0, lattice_parameter_A=A_SI_A, lattice_parameter_label=LATTICE_LABEL)
    cell = build_reflection_cell(s, vacuum_above_A=20.0, depth_below_A=20.0, bulk_absorber_A=5.0,
                                 top_absorber_A=5.0, entrance_vacuum_z_A=Q)
    base = AtomicPotential(cell, parameterisation="kirkland",
                           physical_absorption=PhysicalAbsorption(
                               model="proportional", ratio=0.0, label="TEST_ONLY: none"),
                           frozen_phonons=None, static_lattice_label="TEST_ONLY: static")
    pot = ContinuumOxidePotential(base, oxide=spec)
    grid = make_grid(cell, nx=int(round(cell.extent_x_A / DX)), ny=32)
    n = int(round(cell.length_z_A / Q))
    be = get_backend("numpy", "complex128", 1)
    R = base.realise(grid=grid, dz_A=Q, n_slices=n, backend=be, rng=None)
    acc = np.zeros(grid.shape, complex)
    for i in range(n):
        acc += R.projected(i)
    v_crystal = (acc / (cell.length_z_A - cell.crystal_start_z_A)).mean(axis=1).real
    (arr,), W = pot.layer_arrays(grid, dz_A=Q, n_slices=n)
    np.testing.assert_allclose(W[W > 0], Q, rtol=0, atol=1e-9)   # whole slices of the crystal
    return dict(x=grid.x_A(), dx=grid.dx_A, v_crystal=v_crystal, v_layer=arr.mean(axis=1).real,
                stack=cell.metadata["terraces"][0]["oxide"], cell=cell)


def _top_plane_peak(x, v, dx):
    """x of the topmost atomic-plane peak of the laterally averaged crystal potential."""
    j = np.where((v[1:-1] > v[:-2]) & (v[1:-1] >= v[2:]) & (v[1:-1] > 0.5 * v.max()))[0] + 1
    j = int(j.max())
    a, b, c = v[j - 1], v[j], v[j + 1]
    return float(x[j] + 0.5 * dx * (a - c) / (a - 2 * b + c))


def _layer_lower_boundary(x, v, dx, x_mid):
    """x_c of a layer profile symmetric about its lower edge: x_mid - int_{x < x_mid} v / plateau,
    with x_mid moved to the nearest pixel boundary inside the plateau."""
    jm = int(np.argmin(np.abs(x - x_mid)))
    plateau = v[jm]
    return float(x[jm] + 0.5 * dx - v[: jm + 1].sum() * dx / plateau), float(plateau)


@pytest.mark.parametrize("t,N,rho,a8_e4_placement", [(20.0, 7, 2.20, 0.005), (15.0, 5, 2.20, 0.513),
                                                     (20.0, 6, 2.198, 1.355)])
def test_recorded_overlap_is_what_the_engine_potential_contains(t, N, rho, a8_e4_placement):
    pytest.importorskip("abtem")
    spec = oxide_spec(t_A=t, N=N, rho=rho, Vi=0.0,
                      labels=dict(V_imag="TEST_ONLY: no absorption (profile check)"))
    r = _flat_terrace_profiles(spec)
    st = r["stack"]
    x, dx = r["x"], r["dx"]
    x_c, plateau = _layer_lower_boundary(x, r["v_layer"], dx,
                                         0.5 * (st["interface_x_A"] + st["top_x_A"]))
    top = _top_plane_peak(x, r["v_crystal"], dx)
    measured = top + Q / 2 - x_c
    print(f"t {t} A, N {N}, {rho} g/cm^3: layer plateau {plateau:.4f} V, lower boundary "
          f"{x_c:.6f} A (recorded {st['crystal_boundary_x_A']:.6f}), kept top plane {top:.4f} A "
          f"(recorded {st['atomistic_crystal_top_x_A']:.4f}); overlap measured {measured:+.4f} A, "
          f"recorded {st['interface_overlap_A']:+.4f} A (E4's placement: A8 measured "
          f"{a8_e4_placement:+.3f} A)")
    assert plateau == pytest.approx(10.34, rel=1e-9)
    assert x_c == pytest.approx(st["crystal_boundary_x_A"], abs=1e-6)
    assert measured == pytest.approx(st["interface_overlap_A"], abs=OVERLAP_TOL_A)
    assert abs(st["interface_overlap_A"]) <= Q / 2 + 1e-12
    # E4's placement (stack from the top atomic plane) would be a/8 further into the crystal
    assert measured + Q / 2 == pytest.approx(a8_e4_placement, abs=OVERLAP_TOL_A)


def _buildup_case(Lc):
    """Continuum crystal under the 2 nm TEST_ONLY oxide, crystal length Lc (A)."""
    spec = oxide_spec()
    cell = build_continuum_oxide_cell(
        extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0], terrace_heights_A=[0.0],
        crystal_length_z_A=Lc, vacuum_above_A=60.0, depth_below_A=40.0, bulk_absorber_A=10.0,
        top_absorber_A=10.0, entrance_vacuum_z_A=10.0, oxide=spec, lattice_parameter_A=A_SI_A,
        lattice_parameter_label=LATTICE_LABEL)
    return cell


def test_buildup_assertion_through_the_overlayer_refuses():
    th = 16.1347e-3                      # TEST_ONLY: the (0,0,8) angle (B32, E9 out:10)
    th_int = theta_int_from_ext_rad(th, 200.0, 13.903)
    H, gap, D = 4.0, 1.0, 20.0
    probe = _buildup_case(3000.0)
    lay = probe.metadata["layout"]
    stack = lay["overlayer"]["stack_thickness_max_A"]
    assert stack == pytest.approx(20.0, abs=1e-9)          # continuum crystal: t_ox + t_a
    xb = lay["highest_surface_x_A"] + gap
    z_first = (xb - lay["lowest_surface_x_A"]) / np.tan(th)
    plain, through = D / np.tan(th_int), stack / np.tan(th) + D / np.tan(th_int)

    def check(Lz):
        cell = _buildup_case(Lz - 10.0)
        return check_reflection_geometry(cell, beam_height_A=H, beam_x_bottom_A=xb,
                                         theta_in_ext_rad=th, theta_out_ext_rad=th,
                                         theta_int_rad=th_int, buildup_depth_A=D)
    # long enough for the plain build-up length, not for the stack in addition: refused by the
    # overlayer assertion (the plain item-4 assertion, checked first, passes)
    with pytest.raises(ReflectionGeometryError,
                       match=r"^item4_buildup_length_through_overlayer: .*stack_A = 20"):
        check(z_first + 0.5 * (plain + through))
    ok = check(z_first + through + 5.0)
    assert ok["item4_buildup_length"]["passed"] and \
        ok["item4_buildup_length_through_overlayer"]["passed"]
    assert ok["item4_buildup_length_through_overlayer"]["required_A"] == pytest.approx(through)
