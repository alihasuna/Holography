"""Band assertion of the working reflection (H2 N8, confirmed by H5 A7; report H7).

The transmission function is band-limited like the wave; the (0,0,8) Fourier coefficient of the
Si(001) potential, |g| = 8/a = 1.4731 1/A along the surface normal x, survives the 2/3 aperture only
for dx <= 1/(3 |g|) = a/24 = 0.2263 A, whereas the beam angles alone pass up to dx = 0.45 A.
0.13 A (the M2/T1/H2 practice) must pass, 0.25 A must be refused, with the declared reflection
(MultisliceParams.working_reflections_hkl, PROJECT_INPUT item 9) as a required input."""
import dataclasses

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_continuum_cell, build_reflection_cell
from reflection_holo.forward.multislice import (AtomicPotential, ContinuumTerracePotential,
                                                MultisliceParams, NumericalAbsorber,
                                                PhysicalAbsorption, SheetBeam, check_band,
                                                fft_friendly, reflection_setup,
                                                working_reflection_vectors)
from reflection_holo.forward.multislice.grid import Grid
from reflection_holo.geometry.errors import SamplingError
from reflection_holo.structure import Staircase, build_si001_terraces

LAM = 0.02507934                 # 200 keV (docs/physics_conventions.md)
G008 = 8 / A_SI_A                # 1.4731 cycles/A
TH = 16.1347e-3                  # TEST_ONLY: (0,0,8) angle with the potential's MIP (B32)


def _grid(d):
    return Grid(nx=400, ny=100, dx_A=d, dy_A=d, x0_A=0.0, y0_A=0.0)


def _check(grid, refl):
    return check_band(grid, rule="2/3", wavelength_A=LAM,
                      angles_rad={"incident_ext": TH, "outgoing_ext": TH},
                      reflections_per_A=refl)


def test_0p13_A_carries_0_0_8():
    rec = _check(_grid(0.13), {"(0, 0, 8)": (G008, 0.0)})
    row = rec["working_reflections"]["(0, 0, 8)"]
    assert row["g_x_per_A"] == pytest.approx(1.4731, abs=1e-4)
    assert row["fraction_of_band"] == pytest.approx(G008 * 3 * 0.13, rel=1e-12)   # 0.5745


def test_0p25_A_refused_for_0_0_8_although_the_beams_pass():
    _check(_grid(0.25), {})                                  # the beam angles alone pass
    with pytest.raises(SamplingError, match=r"working reflection '\(0, 0, 8\)'.*dx <= 0\.2263"):
        _check(_grid(0.25), {"(0, 0, 8)": (G008, 0.0)})


def test_band_edge_is_a_over_24():
    _check(_grid(A_SI_A / 24 * (1 - 1e-9)), {"(0, 0, 8)": (G008, 0.0)})
    with pytest.raises(SamplingError):
        _check(_grid(A_SI_A / 24 * (1 + 1e-6)), {"(0, 0, 8)": (G008, 0.0)})


def test_elliptic_aperture_uses_both_axes():
    # (0, +-4, 4) at [100]: g = (4, -+4)/a, |g| = 1.0416 1/A, inside at 0.30 A, outside at 0.33 A
    g = (4 / A_SI_A, -4 / A_SI_A)
    _check(_grid(0.30), {"(0, 4, 4)": g})
    with pytest.raises(SamplingError):
        _check(_grid(0.33), {"(0, 4, 4)": g})


def test_reflections_argument_is_required():
    with pytest.raises(TypeError):
        check_band(_grid(0.13), rule="2/3", wavelength_A=LAM, angles_rad={"out": TH})
    with pytest.raises(ValueError):
        check_band(_grid(0.13), rule="2/3", wavelength_A=LAM, angles_rad={"out": TH},
                   reflections_per_A=None)


# ---------------------------------------------------------------------------------------------
# engine level: the declaration, the crystal frame, reflection_setup
# ---------------------------------------------------------------------------------------------
def _structure(azimuth, z_periods):
    one = build_si001_terraces(
        azimuth_uvw=azimuth, azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
        staircase=Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(1, 1),
                            boundary_step_layers=-2),
        edge_periods=z_periods, substrate_layers=29, first_terrace_backbond_uvw=(1, 1, 0),
        termination="bulk", overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
        lattice_parameter_label="ASSUMPTION B2")
    return one


@pytest.fixture(scope="module")
def atomic_case():
    """The engine-contract geometry (30 mrad TEST_ONLY angle, [110]), which passes every geometry
    assertion at 0.13 A."""
    p = A_SI_A / np.sqrt(2)
    dz = p / 4
    cell = build_reflection_cell(_structure((1, 1, 0), 215), vacuum_above_A=38.0,
                                 depth_below_A=36.0, bulk_absorber_A=15.0, top_absorber_A=8.0,
                                 entrance_vacuum_z_A=10 * dz)
    th = 30e-3
    beam = SheetBeam(height_A=8.0, edge_A=2.0,
                     x_bottom_A=cell.metadata["layout"]["highest_surface_x_A"] + 2.0,
                     theta_in_ext_rad=th, theta_label="TEST_ONLY: item 7")
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(model="proportional", ratio=0.0,
                                                                 label="ASSUMPTION: none"),
                          frozen_phonons=None, static_lattice_label="ASSUMPTION: static")

    def params(pixel, refl):
        return MultisliceParams(
            energy_keV=200.0, nx=fft_friendly(int(np.ceil(cell.extent_x_A / pixel))),
            ny=fft_friendly(int(np.ceil(cell.extent_y_A / pixel))), dz_A=dz, propagator="exact",
            band_limit="2/3", backend="numpy", precision="complex64", threads=2,
            absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"), theta_out_ext_rad=th,
            buildup_depth_A=20.0, working_reflections_hkl=refl)
    return cell, pot, beam, params


def test_reflection_setup_passes_at_0p13_and_records_the_reflection(atomic_case):
    cell, pot, beam, params = atomic_case
    s = reflection_setup(cell, potential=pot, beam=beam, params=params(0.13, ((0, 0, 8),)))
    row = s["band"]["working_reflections"]["(0, 0, 8)"]
    assert row["g_x_per_A"] == pytest.approx(G008, rel=1e-12)
    assert row["g_y_per_A"] == pytest.approx(0.0, abs=1e-12)
    assert row["g_z_per_A"] == pytest.approx(0.0, abs=1e-12)
    assert "PROJECT_INPUT item 9" in s["band"]["working_reflections_source"]


def test_reflection_setup_refuses_0p25_for_0_0_8(atomic_case):
    cell, pot, beam, params = atomic_case
    p = params(0.25, ((0, 0, 8),))
    assert cell.extent_x_A / p.nx > A_SI_A / 24
    with pytest.raises(SamplingError, match="working reflection"):
        reflection_setup(cell, potential=pot, beam=beam, params=p)


def test_declaration_is_required_and_never_defaulted(atomic_case):
    cell, pot, beam, params = atomic_case
    p = params(0.13, ((0, 0, 8),))
    kw = {f.name: getattr(p, f.name) for f in dataclasses.fields(p)}
    del kw["working_reflections_hkl"]
    with pytest.raises(TypeError):
        MultisliceParams(**kw)
    with pytest.raises(ValueError, match="PROJECT_INPUT item 9"):
        reflection_setup(cell, potential=pot, beam=beam, params=params(0.13, ()))
    for bad in (None, "008", ((0, 0, 8.5),), ((0, 0),), ((0, 0, 0),)):
        with pytest.raises((TypeError, ValueError)):
            reflection_setup(cell, potential=pot, beam=beam, params=params(0.13, bad))


def test_crystal_frame_mapping(atomic_case):
    cell = atomic_case[0]                                         # [110] azimuth
    v = working_reflection_vectors(cell, ((0, 0, 8), (1, -1, 1), (2, -2, 0), (1, 1, 1)))
    a = A_SI_A
    assert v["(0, 0, 8)"] == pytest.approx((8 / a, 0.0, 0.0), abs=1e-12)
    # y = z x x = [1,-1,0]/sqrt(2) at the [110] azimuth, z = [110]/sqrt(2)
    assert v["(1, -1, 1)"] == pytest.approx((1 / a, np.sqrt(2) / a, 0.0), abs=1e-12)
    assert v["(2, -2, 0)"] == pytest.approx((0.0, 2 * np.sqrt(2) / a, 0.0), abs=1e-12)
    assert v["(1, 1, 1)"] == pytest.approx((1 / a, 0.0, np.sqrt(2) / a), abs=1e-12)


def test_continuum_cell_takes_no_reflection():
    cell = build_continuum_cell(extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0],
                                terrace_heights_A=[0.0], crystal_length_z_A=1000.0,
                                vacuum_above_A=40.0, depth_below_A=30.0, bulk_absorber_A=15.0,
                                top_absorber_A=10.0, entrance_vacuum_z_A=10.0)
    assert working_reflection_vectors(cell, ()) == {}
    with pytest.raises(ValueError, match="no reciprocal lattice"):
        working_reflection_vectors(cell, ((0, 0, 8),))
    ContinuumTerracePotential(cell, V0_V=12.0, V0_label="TEST_ONLY: V0",
                              physical_absorption=PhysicalAbsorption(
                                  model="proportional", ratio=0.0, label="ASSUMPTION: none"),
                              surface_profile="sharp")
