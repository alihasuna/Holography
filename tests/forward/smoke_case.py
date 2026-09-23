"""Atomistic smoke case (not a test module): Si(001), [110] azimuth, a/2 (double-layer) step with
edges PARALLEL to the beam, specular (0,0,8) condition at 200 keV, Kirkland independent-atom
potential, static lattice. UNVALIDATED: rung 2 and the abTEM cross-check were not run.

TEST_ONLY stand-ins: azimuth (item 8), terrace widths (item 11), incidence angle (item 7; taken as
the external angle of the (0,0,8) internal Bragg condition computed with the mean inner potential
of the potential actually used, 13.903 V, orchestrator decision 5), absorption (item 21: zero,
ASSUMPTION), static lattice (ASSUMPTION)."""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_reflection_cell
from reflection_holo.forward.multislice import (AtomicPotential, MultisliceParams,
                                                NumericalAbsorber, PhysicalAbsorption, SheetBeam,
                                                fft_friendly, potential_mean_inner_potential_V)
from reflection_holo.geometry.refraction import theta_int_from_ext_rad
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.structure import Staircase, build_si001_terraces

AZ_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 8 (beam azimuth [110])"
THETA_LABEL = ("TEST_ONLY: stands in for PROJECT_INPUT item 7; external angle of the (0,0,8) "
               "internal Bragg condition with the potential's own mean inner potential")
NO_ABS = PhysicalAbsorption(model="proportional", ratio=0.0,
                            label="ASSUMPTION: no physical absorption (PROJECT_INPUT item 21 not "
                                  "supplied)")
STATIC = "ASSUMPTION: static lattice (no frozen phonons) for the smoke run"


def smoke_setup(*, widths=(6, 6), H=8.0, edge=2.0, gap=2.0, buildup=20.0, absorber=15.0,
                top=10.0, max_pixel=0.13, slices_per_period=4, precision="complex64",
                threads=4):
    p = A_SI_A / np.sqrt(2)
    dz = p / slices_per_period
    q = A_SI_A / 4
    clean = buildup + 1.0
    depth = absorber + clean
    sub = int(np.ceil(depth / q)) + 2
    # angle: (0,0,8) specular condition with the MIP of the Kirkland potential (13.903 V)
    V0_mip = 8.0 / A_SI_A**3 * _kirkland_F0()
    sc = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=200.0, V0_V=V0_mip, a_A=A_SI_A)
    theta = float(sc.theta_ext)
    th_int = theta_int_from_ext_rad(theta, 200.0, V0_mip)
    h = A_SI_A / 2
    ent = 10 * dz
    z_first_low = (gap + h) / np.tan(theta)
    L_need = z_first_low + buildup / np.tan(th_int) + 2 * dz
    periods = int(np.ceil((L_need - ent) / p))
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=tuple(widths),
                   boundary_step_layers=-2)
    s = build_si001_terraces(azimuth_uvw=(1, 1, 0), azimuth_label=AZ_LABEL, staircase=st,
                             edge_periods=periods, substrate_layers=sub,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                             lattice_parameter_label="ASSUMPTION B2")
    L = ent + periods * p
    vac = float(np.ceil(H + gap + L * np.tan(theta) + 1.0))
    cell = build_reflection_cell(s, vacuum_above_A=vac, depth_below_A=depth,
                                 bulk_absorber_A=absorber, top_absorber_A=top,
                                 entrance_vacuum_z_A=ent)
    pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=NO_ABS,
                          frozen_phonons=None, static_lattice_label=STATIC)
    assert abs(potential_mean_inner_potential_V(pot) - V0_mip) < 1e-9
    xs_hi = cell.metadata["layout"]["highest_surface_x_A"]
    beam = SheetBeam(height_A=H, edge_A=edge, x_bottom_A=xs_hi + gap, theta_in_ext_rad=theta,
                     theta_label=THETA_LABEL)
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / max_pixel)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / max_pixel)))
    params = MultisliceParams(energy_keV=200.0, nx=nx, ny=ny, dz_A=dz, propagator="exact",
                              band_limit="2/3", backend="numpy", precision=precision,
                              threads=threads,
                              absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                              theta_out_ext_rad=theta, buildup_depth_A=buildup)
    return dict(cell=cell, potential=pot, beam=beam, params=params, theta=theta, h=h,
                V0_mip=V0_mip, structure=s)


def _kirkland_F0() -> float:
    from abtem.parametrizations import KirklandParametrization
    return float(KirklandParametrization().projected_scattering_factor("Si")(np.array([0.0]))[0])


def terrace_regions(cell, fraction):
    """Central `fraction` of each terrace strip in y: (lower, upper) = (terrace 0, terrace 1)."""
    out = []
    for t in cell.metadata["terraces"]:
        y0, y1 = t["range_A"]
        m = 0.5 * (1 - fraction) * (y1 - y0)
        out.append((y0 + m, y1 - m))
    return out[0], out[1]
