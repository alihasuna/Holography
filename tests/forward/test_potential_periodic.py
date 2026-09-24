"""ContinuumPeriodicPotential (rung-2 potential class, docs/agent_reports/P2_rung2_reference.md 8.1):
required inputs, point sampling of the harmonics, bit-for-bit identity with the rung-1 class when
every V_g is zero (potential, slices and a full run), the realised harmonics record, and the band
assertion of the harmonics."""
import numpy as np
import pytest

from ladder_cases import NO_ABS, THETA_0008, V0, V0_LABEL, rung1_case
from reflection_holo.forward.cell import build_continuum_cell
from reflection_holo.forward.multislice import (ContinuumPeriodicPotential,
                                                ContinuumTerracePotential, PhysicalAbsorption,
                                                make_grid, reflection_setup, run_realisation)
from reflection_holo.geometry.errors import SamplingError

G = 8.0 / 5.4309
H_LABEL = "TEST_ONLY: harmonic stand-in (unit test)"
ABS10 = PhysicalAbsorption(model="proportional", ratio=0.1, label="TEST_ONLY: r = 0.1 (unit test)")


def _cell(terraces=1):
    if terraces == 1:
        yb, h = [0.0, 10.0], [0.0]
    else:
        yb, h = [0.0, 5.0, 10.0], [0.0, 1.0]
    return build_continuum_cell(extent_y_A=10.0, terrace_y_bounds_A=yb, terrace_heights_A=h,
                                crystal_length_z_A=40.0, vacuum_above_A=30.0, depth_below_A=35.0,
                                bulk_absorber_A=15.0, top_absorber_A=10.0,
                                entrance_vacuum_z_A=10.0)


def _pot(cell, harmonics, absorption=NO_ABS, **over):
    kw = dict(V0_V=V0, V0_label=V0_LABEL, harmonics=harmonics, harmonics_label=H_LABEL,
              physical_absorption=absorption, surface_profile="sharp")
    kw.update(over)
    return ContinuumPeriodicPotential(cell, **kw)


@pytest.mark.parametrize("absorption", [NO_ABS, ABS10])
@pytest.mark.parametrize("harmonics", [(), ((G, 0.0, 0.0),), ((G, 0.0, 0.3), (2 * G, 0.0, 0.0))])
def test_zero_harmonics_reproduce_the_rung1_class_bit_for_bit(absorption, harmonics):
    cell = _cell()
    grid = make_grid(cell, nx=1001, ny=1)                   # surface inside a pixel
    per = _pot(cell, harmonics, absorption)
    ter = ContinuumTerracePotential(cell, V0_V=V0, V0_label=V0_LABEL,
                                    physical_absorption=absorption, surface_profile="sharp")
    a, b = per.complex_potential(grid), ter.complex_potential(grid)
    assert a.dtype == b.dtype and a.tobytes() == b.tobytes()
    from reflection_holo.forward.multislice.backend import get_backend
    for prec in ("complex64", "complex128"):
        be = get_backend("numpy", prec, 1)
        ra = per.realise(grid=grid, dz_A=1.5, n_slices=34, backend=be, rng=None)
        rb = ter.realise(grid=grid, dz_A=1.5, n_slices=34, backend=be, rng=None)
        for i in (0, 6, 7, 8, 20, 33):                     # slice 6 straddles the front face
            assert ra.slice_key(i) == rb.slice_key(i)
            assert ra.projected(i).tobytes() == rb.projected(i).tobytes()


def test_zero_harmonic_full_run_is_bit_identical_to_rung1():
    cell, ter, beam, params, _ = rung1_case(THETA_0008, dx=0.1, dz=4.0, propagator="exact",
                                            precision="complex64")
    per = _pot(cell, ((G, 0.0, 0.0),))
    e1 = run_realisation(cell, potential=ter, beam=beam, params=params, realisation=0, seed=None)
    e2 = run_realisation(cell, potential=per, beam=beam, params=params, realisation=0, seed=None)
    assert e1.psi.tobytes() == e2.psi.tobytes()


def test_harmonics_are_point_sampled_and_recorded():
    cell = _cell()
    grid = make_grid(cell, nx=2400, ny=1)                   # dx = 0.025 A
    t = 0.1
    pot = _pot(cell, ((G, 1.035742, t),), ABS10)
    x = grid.x_A()
    xs = cell.metadata["terraces"][0]["surface_x_A"]
    V = pot.complex_potential(grid)[:, 0]
    inside = x < xs - grid.dx_A
    want = V0 + 2 * 1.035742 * np.cos(2 * np.pi * G * (x - xs + t))
    assert np.max(np.abs(V.real[inside] - want[inside])) < 1e-12
    assert np.max(np.abs(V.imag[inside] - 0.1 * want[inside])) < 1e-12
    assert np.all(V[x > xs + grid.dx_A] == 0)
    rh = pot.realised_harmonics(grid)
    assert abs(rh["V0_V"] - V0) < 1e-10 and rh["rms_residual_V"] < 1e-12
    (h,) = rh["harmonics"]
    assert abs(h["V_g_cos_V"] - 1.035742) < 1e-10 and abs(h["V_g_sin_V"]) < 1e-10
    assert rh["imag_over_real_max_dev_from_r"] < 1e-14
    pv = pot.provenance()
    assert pv["harmonics"] == [dict(g_per_A=G, V_g_V=1.035742, plane_offset_A=t)]
    assert pv["V0_label"] == V0_LABEL and pv["harmonics_label"] == H_LABEL


def test_required_inputs_and_refusals():
    cell = _cell()
    with pytest.raises(TypeError, match="harmonics"):
        _pot(cell, None)
    with pytest.raises(ValueError, match="triple"):
        _pot(cell, ((G, 1.0),))
    with pytest.raises(ValueError, match="g_per_A"):
        _pot(cell, ((0.0, 1.0, 0.0),))
    with pytest.raises(ValueError, match="same g_per_A"):
        _pot(cell, ((G, 1.0, 0.0), (G, 0.5, 0.0)))
    with pytest.raises(ValueError, match="finite"):
        _pot(cell, ((G, np.nan, 0.0),))
    with pytest.raises(ValueError, match="label"):
        _pot(cell, ((G, 1.0, 0.0),), harmonics_label="")
    with pytest.raises(ValueError, match="label"):
        _pot(cell, ((G, 1.0, 0.0),), V0_label="from a paper")
    with pytest.raises(ValueError, match="sharp"):
        _pot(cell, ((G, 1.0, 0.0),), surface_profile="smooth")
    with pytest.raises(TypeError, match="PhysicalAbsorption"):
        _pot(cell, ((G, 1.0, 0.0),), physical_absorption=0.1)
    with pytest.raises(ValueError, match="single terrace"):
        _pot(_cell(terraces=2), ((G, 1.0, 0.0),))
    with pytest.raises(TypeError):
        ContinuumPeriodicPotential(cell, V0_V=V0, V0_label=V0_LABEL, harmonics=(),
                                   physical_absorption=NO_ABS, surface_profile="sharp")


def test_harmonics_are_asserted_inside_the_band():
    cell, _, beam, params, _ = rung1_case(THETA_0008, dx=0.1, dz=4.0, propagator="exact",
                                          precision="complex64")
    # dx = 0.1 A: 2/3 band fx_max = 3.333 1/A
    ok = _pot(cell, ((G, 1.0, 0.0),))
    s = reflection_setup(cell, potential=ok, beam=beam, params=params)
    (name,) = s["band"]["working_reflections"]
    assert "continuum harmonic" in name
    assert s["band"]["working_reflections"][name]["g_x_per_A"] == pytest.approx(G)
    bad = _pot(cell, ((G, 1.0, 0.0), (3.4, 0.1, 0.0)))
    with pytest.raises(SamplingError, match="continuum harmonic g = 3.400000"):
        reflection_setup(cell, potential=bad, beam=beam, params=params)
