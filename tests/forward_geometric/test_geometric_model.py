"""Geometric-phase engine (docs/05 section 4.5): phases, ray-traced shadows, B4 refusals,
invisibility flag. TEST_ONLY values stand in for PROJECT_INPUT items 7 and 8 and never appear in
configs/. Tolerances are stated per test and chosen before running (floating-point level for
exact identities; one exit-plane pixel for ray-traced strip widths)."""
import math

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.geometric import (STATUS, GeometricParams, OutsideB4ScopeError,
                                               geometric_exit_wave, terrace_model_from_structure)
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A
from reflection_holo.structure import OverlayerSpec, Staircase, build_si001_terraces
from reflection_holo.structure.shadows import terrace_shadow_strips

AZ_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 8 (beam azimuth)"
TH_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7 (glancing angle)"
THETA = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=200.0, V0_V=12.0, a_A=A_SI_A).theta_ext
PARAMS = GeometricParams(exit_plane_pixel_A=(0.05, 0.5), n_y=4, x_margin_A=5.0,
                         periods_along_beam=1, reflectivity_amplitude=1.0,
                         invisibility_tol_cycles=0.01)


def build(layers=(0, 2, 1), widths=(60, 60, 60), boundary=-1, azimuth=(1, 0, 0), edges="transverse",
          overlayer=None):
    st = Staircase(edges=edges, terrace_layers=layers, terrace_widths=widths,
                   boundary_step_layers=boundary)
    return build_si001_terraces(azimuth_uvw=azimuth, azimuth_label=AZ_LABEL, staircase=st,
                                edge_periods=1, substrate_layers=4,
                                first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                                overlayer=overlayer, vacuum_above_A=10.0,
                                lattice_parameter_A=A_SI_A,
                                lattice_parameter_label="ASSUMPTION B2")


def run(structure, theta=THETA, params=PARAMS, illumination="plane_wave", energy=200.0):
    return geometric_exit_wave(terrace_model_from_structure(structure), energy_keV=energy,
                               theta_in_ext_rad=theta, theta_label=TH_LABEL, params=params,
                               illumination=illumination, beam="specular")


def test_terrace_phase_is_minus_q_dot_R_exactly():
    """On every lit exit-plane pixel, psi exp(-i k_out,x x) = |A| exp(-i q.R_k), with R_k from the
    relations measured on the atoms (tolerance 1e-9 rad: floating point)."""
    s = build()
    r = run(s)
    ew = r.exit_wave
    k = k_ang_per_A(200.0)
    q_x = 2 * k * math.sin(THETA)
    x = ew.x0_A + ew.dx_A * np.arange(ew.psi.shape[0])
    env = ew.psi * np.exp(-1j * k * math.sin(THETA) * x)[:, None]
    lit = r.trace["status"] == STATUS["lit"]
    H = np.array([t["top_height_A"] for t in s.metadata["terrace_map"]])
    want = -q_x * H[r.trace["source_terrace"][lit]]
    assert np.max(np.abs(np.angle(env[lit] * np.exp(-1j * want)))) <= 1e-9
    assert np.allclose(np.abs(env[lit]), 1.0, atol=1e-12)
    assert np.all(ew.psi[~lit] == 0)
    assert ew.metadata["label"] == "geometric model, no dynamical amplitude, B4 scope applies"
    assert ew.plane == "exit plane z = L_z (no further propagation)"
    # the recorded step phases are -(k_out - k_in).t of the measured relations
    for st in ew.metadata["steps"]:
        assert st["step_phase_rad"] == pytest.approx(-q_x * st["height_A"], abs=1e-9)


def test_shadow_and_riser_bands_at_a_down_step_and_none_at_an_up_step():
    """Down-step a/4 (upper terrace upstream): illumination shadow h/tan(theta) on the surface,
    i.e. h on the exit-plane x axis, plus a riser band of height h; up-step a/2: no dark band
    (the blocked-view strip is not imaged). Tolerance: one exit-plane pixel (0.05 A)."""
    s = build()
    r = run(s)
    col = r.trace["status"][:, 0]
    dx = r.exit_wave.dx_A
    h4 = A_SI_A / 4
    n_shadow = int((col == STATUS["illumination_shadow"]).sum())
    n_riser = int((col == STATUS["riser"]).sum())
    # two a/4 down-steps (one inside, one at the upstream end of the field): shadow on both
    assert abs(n_shadow * dx - 2 * h4) <= 2 * dx
    assert abs(n_riser * dx - h4) <= dx                      # only the inner down-step has a riser
    # sources of shadowed pixels lie in the illumination intervals of structure.shadows
    strips = terrace_shadow_strips(s, THETA, TH_LABEL, theta_out_ext_rad=THETA,
                                   theta_out_label=TH_LABEL)
    zs = r.trace["source_z_A"][r.trace["status"] == STATUS["illumination_shadow"]]
    assert zs.size > 0 and np.all(strips.illumination_mask(zs))
    # nominal strip lengths recorded at the operating angle
    for st in r.exit_wave.metadata["steps"]:
        assert st["nominal_strip_length_A"] == pytest.approx(abs(st["height_A"]) / math.tan(THETA),
                                                             rel=1e-12)
    # no lit source inside a blocked-view strip
    zl = r.trace["source_z_A"][r.trace["status"] == STATUS["lit"]]
    assert not np.any(strips.blocked_view_mask(zl))


def test_a4_step_outside_b4_scope_is_refused():
    with pytest.raises(OutsideB4ScopeError, match="B4"):
        run(build(azimuth=(1, 1, 0), widths=(60, 60, 60)))
    run(build(layers=(0, 2), widths=(60, 60), boundary=-2, azimuth=(1, 1, 0)))   # a/2 only: OK


def test_overlayer_and_convergent_illumination_are_refused():
    ov = OverlayerSpec(material="SiO2", thickness_A=5.0, density_g_cm3=2.2,
                       label="TEST_ONLY: stands in for PROJECT_INPUT item 12")
    with pytest.raises(OutsideB4ScopeError, match="overlayer"):
        run(build(overlayer=ov))
    with pytest.raises(OutsideB4ScopeError, match="plane"):
        run(build(), illumination="convergent")


def test_energy_other_than_200_keV_is_refused():
    with pytest.raises(ValueError, match="200"):
        run(build(), energy=300.0)


def test_invisibility_of_the_a2_step_at_the_vacuum_bragg_angle_is_flagged():
    """At sin(theta) = 4 lambda / a (vacuum Bragg angle of (0,0,8)) the a/2 translation step has
    g.R = 4 (invisible); at the internal-Bragg external angle it is not."""
    th_B = math.asin(4 * wavelength_A(200.0) / A_SI_A)
    s = build()
    inv = [st for st in run(s, theta=th_B).exit_wave.metadata["steps"]
           if st["type"] == "translation"][0]["invisibility"]
    assert inv["invisible"] and inv["nearest_integer"] == 4
    vis = [st for st in run(s).exit_wave.metadata["steps"]
           if st["type"] == "translation"][0]["invisibility"]
    assert not vis["invisible"]


def test_parallel_edges_have_no_shadow_and_per_strip_phases():
    s = build(layers=(0, 2), widths=(3, 3), boundary=-2, edges="parallel")
    params = GeometricParams(exit_plane_pixel_A=(0.05, 0.25), n_y=int(6 * A_SI_A / 0.25),
                             x_margin_A=5.0, periods_along_beam=40, reflectivity_amplitude=1.0,
                             invisibility_tol_cycles=0.01)
    r = run(s, params=params)
    st = r.trace["status"]
    assert not np.any(st == STATUS["illumination_shadow"]) and not np.any(st == STATUS["riser"])
    assert set(np.unique(r.trace["source_terrace"][st == STATUS["lit"]])) == {0, 1}
