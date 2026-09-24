"""Continuum oxide in the multislice engine (report E4; tests (a), (c), (d), (e)).

(a) Oxide-only control (E9 M4): the layer on a substrate at the same potential, so the only step is
    the layer's vacuum edge. Sharp edge (TEST_ONLY flag) against the single-edge Fresnel value with
    the rung-1 tolerances fixed by the M2 convergence study (tests/forward/test_rung1_refraction.py:
    |err - model| <= 3.5e-3 with model = -((q1 + q2) dx)^2/12 for a cell-averaged step, phase
    <= 1e-3 rad); the Fresnel value itself against E9 out:234 and out:284 (printed precision). Graded
    edges: w = 0.1 A (TEST_ONLY flag) against |r_F| exp(-(q w)^2/2) (E9's formula, out:236, 285)
    within 1 % in |r| (a priori: 0.35 % rung-1 amplitude tolerance + 0.05 % between that factor
    and the Nevot-Croce factor exp(-2 k1 k2 w^2) + E9's own 1-D multislice deviation 0.12 % in |r|,
    out:285, doubled); w = 0.5 A (the required minimum) suppresses |r|^2 by at least 1e3 (the
    factor E9 M4 asks of an oxide-only control), and equals the EXACT 1-D reflectivity of the
    graded edge (transfer matrix, audit A8 C6: 1.8345e-9 at the central bin 16.1751 mrad; E9's
    Born factor exp(-(q w)^2), out:241, underestimates it 58-fold) within the same 1 % in |r|
    (added by report X4 after audit A8 m1; the Born-based tolerances of E4 had nothing to test
    here, the budget of the w = 0.1 A case without its Born-related terms is conservative).
(c) Flat Si(001) [100] with and without a 2 nm oxide (V'_ox 0.40 V, and 0 V), TEST_ONLY crystal
    absorption r = 0.1: the specular reflection-coefficient ratios are REPORTED against E9's
    zero-loss model value exp(-2 Im k'_perp t) (E9 M1: a model value, not a bound; no pass/fail on
    it). Asserted: the recorded layer quantities (internal angle out:36, IAM out:166, crystal MIP
    out:171) at their printed precision.
(d) A conformal a/4 step under the oxide on a short cell: a SMOKE test (the atomistic fixed-beam
    translation gate has not passed; not a physics claim). The step phase is printed, not asserted.
(e) Refusals of the engine (missing or inconsistent overlayer inputs).
"""
import dataclasses

import numpy as np
import pytest

from oxide_cases import (E_KEV, THETA_B32, V_OX, atomistic_case, exact_graded_edge_r,
                         oxide_only_case, oxide_only_measure, oxide_spec, windowed_reflection)
from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_continuum_cell, build_continuum_oxide_cell
from reflection_holo.forward.multislice import (ContinuumOxidePotential, ContinuumTerracePotential,
                                                PhysicalAbsorption, analytic_step_reflection,
                                                make_grid, reflection_setup, run_realisation,
                                                terrace_step_phase)
from reflection_holo.geometry.refraction import delta_K_per_A, k_perp_in_layer_per_A
from reflection_holo.geometry.wavelength import k_ang_per_A

AMP_TOL, PHASE_TOL = 3.5e-3, 1.0e-3            # rung 1 (M2 convergence study)
GRADED_TOL = 1e-2                              # |r| relative, w = 0.1 A (module docstring)
SUPPRESSION = 1e-3                             # |r|^2 ratio, w = 0.5 A (E9 M4)
NO_ABS = PhysicalAbsorption(model="proportional", ratio=0.0, label="TEST_ONLY: no absorption")


# --------------------------------------------------------------------------------------------------
# (a) oxide-only control: Fresnel term of the layer edge and its suppression
# --------------------------------------------------------------------------------------------------
def test_fresnel_value_of_the_edge_equals_e9():
    k1 = k_ang_per_A(E_KEV) * np.sin(THETA_B32)
    r = float(analytic_step_reflection(k1, delta_K_per_A(E_KEV, V_OX)))
    assert r == pytest.approx(-0.05193, abs=5e-6)                          # out:234
    assert r ** 2 == pytest.approx(2.6972e-3, abs=5e-8)                     # out:284 (analytic)


@pytest.fixture(scope="module")
def sharp():
    return oxide_only_measure(w_v=0.0, dx=0.025)


def test_sharp_edge_reflects_the_fresnel_value(sharp):
    err = abs(sharp["r"]) / abs(sharp["r_analytic"]) - 1
    model = -((sharp["q1"] + sharp["q2"]) * sharp["dx"]) ** 2 / 12
    phase = np.angle(sharp["r"] / sharp["r_analytic"])
    print(f"sharp edge: |r|^2 = {abs(sharp['r']) ** 2:.5e} (analytic {sharp['r_analytic'] ** 2:.5e}"
          f" at the central bin), amplitude error {err:+.5%} (model {model:+.5%}), phase "
          f"{phase:+.2e} rad")
    assert abs(err - model) <= AMP_TOL
    assert abs(phase) <= PHASE_TOL
    assert abs(abs(np.angle(sharp["r"])) - np.pi) <= PHASE_TOL              # r real, negative
    md = sharp["ew"].metadata["overlayer"]
    assert md["edge_widths_A"]["vacuum_edge_width_A"] == 0.0


def test_graded_edge_of_0p1_A_follows_the_roughness_factor(sharp):
    g = oxide_only_measure(w_v=0.1, dx=0.025)
    q = g["q1"] + g["q2"]
    want = abs(g["r_analytic"]) * np.exp(-(q * 0.1) ** 2 / 2)
    print(f"w = 0.1 A: |r|^2 = {abs(g['r']) ** 2:.5e}, E9 formula {want ** 2:.5e} (E9 1-D "
          f"multislice at 16.1347 mrad: 1.3067e-3, out:285)")
    assert abs(g["r"]) / want - 1 == pytest.approx(0, abs=GRADED_TOL)


def test_graded_edge_of_0p5_A_suppresses_the_layer_reflection(sharp):
    g = oxide_only_measure(w_v=0.5, dx=0.025)
    ratio = abs(g["r"]) ** 2 / abs(sharp["r"]) ** 2
    r_exact = exact_graded_edge_r(g["theta_bin_rad"], V_OX, 0.5)
    print(f"w = 0.5 A: |r|^2 = {abs(g['r']) ** 2:.4e}, suppression {ratio:.2e}; EXACT 1-D "
          f"(transfer matrix, audit A8 C6) {abs(r_exact) ** 2:.4e} at the central bin "
          f"{g['theta_bin_rad'] * 1e3:.4f} mrad (E9's Born factor exp(-(q w)^2) = "
          f"{np.exp(-((g['q1'] + g['q2']) * 0.5) ** 2):.2e} of the sharp edge underestimates it "
          f"{abs(r_exact) ** 2 / (g['r_analytic'] ** 2 * np.exp(-((g['q1'] + g['q2']) * 0.5) ** 2)):.0f}"
          f"-fold)")
    assert ratio <= SUPPRESSION
    assert abs(g["r"]) / abs(r_exact) - 1 == pytest.approx(0, abs=GRADED_TOL)


# --------------------------------------------------------------------------------------------------
# potential construction: following the surface, sampling, bit-identity without the layer
# --------------------------------------------------------------------------------------------------
def _two_terrace_cell(spec, h, dx=None):
    def cell(top):
        return build_continuum_oxide_cell(
            extent_y_A=20.0, terrace_y_bounds_A=[0.0, 10.0, 20.0], terrace_heights_A=[0.0, h],
            crystal_length_z_A=100.0, vacuum_above_A=40.0, depth_below_A=30.0,
            bulk_absorber_A=10.0, top_absorber_A=top, entrance_vacuum_z_A=10.0, oxide=spec,
            lattice_parameter_A=A_SI_A, lattice_parameter_label="ASSUMPTION B2")
    c = cell(10.0)
    if dx is None:
        return c
    n = int(np.ceil(c.extent_x_A / dx))                   # the top absorber takes the rounding
    return cell(10.0 + n * dx - c.extent_x_A)


def test_layer_follows_the_surface_not_a_planar_mask():
    """The layer of the upper terrace is the lower one shifted by the step (E6 m12, E9 m5)."""
    h = 2 * A_SI_A / 4
    spec = oxide_spec()
    dx = h / 16                                           # the step is a whole number of pixels
    cell = _two_terrace_cell(spec, h, dx)
    base = ContinuumTerracePotential(cell, V0_V=13.903, V0_label="TEST_ONLY: substrate V0",
                                     physical_absorption=NO_ABS, surface_profile="sharp")
    pot = ContinuumOxidePotential(base, oxide=spec)
    grid = make_grid(cell, nx=int(round(cell.extent_x_A / dx)), ny=40)
    assert grid.dx_A == pytest.approx(dx, rel=1e-12)
    (arr,), W = pot.layer_arrays(grid, dz_A=1.0, n_slices=int(round(cell.length_z_A)))
    lo, hi = arr[:, 10], arr[:, 30]                       # pixel columns inside terrace 0 and 1
    np.testing.assert_allclose(hi[16:], lo[:-16], atol=1e-9)
    ox0 = cell.metadata["terraces"][0]["oxide"]
    x = grid.x_A()
    inside = (x > ox0["interface_x_A"] + 4) & (x < ox0["top_x_A"] - 4)
    np.testing.assert_allclose(lo[inside].real, V_OX, rtol=1e-9)
    np.testing.assert_allclose(lo[inside].imag, 0.40, rtol=1e-9)
    assert np.all(np.abs(lo[x > ox0["top_x_A"] + 5]) < 1e-12)
    np.testing.assert_allclose(lo[x < ox0["crystal_boundary_x_A"] - 5].real, 13.903, rtol=1e-12)
    assert W[:10].sum() == 0 and np.all(W[10:, 0] == 1.0)  # entrance vacuum carries no layer


def test_sharp_interface_uses_the_crystal_base_bit_for_bit():
    spec = oxide_spec(w_i=0.0, iflag=True)          # TEST_ONLY sharp interface (audit A8 m5)
    cell = _two_terrace_cell(spec, A_SI_A / 4)
    base = ContinuumTerracePotential(cell, V0_V=13.903, V0_label="TEST_ONLY: substrate V0",
                                     physical_absorption=NO_ABS, surface_profile="sharp")
    pot = ContinuumOxidePotential(base, oxide=spec)
    grid = make_grid(cell, nx=600, ny=20)
    assert np.array_equal(pot._continuum_crystal(grid), base.complex_potential(grid))


def test_setup_records_what_the_layer_changes():
    cell, pot, beam, params, _ = oxide_only_case(w_v=0.5, dx=0.1)
    s = reflection_setup(cell, potential=pot, beam=beam, params=params)
    ov = s["overlayer"]
    assert ov["internal_angle_in_layer_in_rad"] == pytest.approx(17.902e-3, abs=5e-7)   # out:36
    assert "incident_int_layer" in str(s["band"])
    assert "B32" in ov["mean_inner_potential_treatment"]
    assert s["V0_potential_V"] == pytest.approx(V_OX)      # the substrate's (the crystal's) MIP
    assert s["geometry"]["item4_buildup_length_through_overlayer"]["passed"] is True
    kp = k_perp_in_layer_per_A(THETA_B32, E_KEV, V_OX, 0.0)
    assert kp.real == pytest.approx(4.48493, abs=5e-6)                                   # out:36


# --------------------------------------------------------------------------------------------------
# (e) refusals
# --------------------------------------------------------------------------------------------------
def test_refusals_of_the_engine():
    cell, pot, beam, params, _ = oxide_only_case(w_v=0.5, dx=0.1)
    with pytest.raises(ValueError, match="must be multislice.ContinuumOxidePotential"):
        reflection_setup(cell, potential=pot.base, beam=beam, params=params)
    with pytest.raises(ValueError, match="spec_sha256"):
        ContinuumOxidePotential(pot.base, oxide=oxide_spec(Vi=0.0, w_v=0.5, w_i=0.0, iflag=True,
                                                           t_A=20.0, N=7, V=10.5))
    with pytest.raises(ValueError, match="not resolved"):              # dx = 0.6 A > w = 0.5 A
        reflection_setup(cell, potential=pot, beam=beam,
                         params=dataclasses.replace(params, nx=int(cell.extent_x_A / 0.6)))
    plain = build_continuum_cell(extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0],
                                 terrace_heights_A=[0.0], crystal_length_z_A=100.0,
                                 vacuum_above_A=40.0, depth_below_A=30.0, bulk_absorber_A=10.0,
                                 top_absorber_A=10.0, entrance_vacuum_z_A=10.0)
    base = ContinuumTerracePotential(plain, V0_V=13.903, V0_label="TEST_ONLY: substrate V0",
                                     physical_absorption=NO_ABS, surface_profile="sharp")
    with pytest.raises(ValueError, match="carries no continuum oxide"):
        ContinuumOxidePotential(base, oxide=oxide_spec())
    with pytest.raises(ValueError, match="graded over at least 0.5"):
        _two_terrace_cell(oxide_spec(w_v=0.2), 0.0)


def test_no_overlayer_no_record():
    from ladder_cases import rung1_case
    cell, pot, beam, params, _ = rung1_case(16.47e-3, dx=0.1, dz=2.0, propagator="exact")
    s = reflection_setup(cell, potential=pot, beam=beam, params=params)
    assert "overlayer" not in s and "overlayer" not in cell.metadata["layout"]
    assert "incident_int_layer" not in str(s["band"])


# --------------------------------------------------------------------------------------------------
# (c) flat Si(001) + 2 nm oxide: comparison with the zero-loss model value (not pass/fail)
# --------------------------------------------------------------------------------------------------
C_EXTRA_LENGTH_A = 6000.0          # set from the cell-length series of report E4 section 4
# audit A8 m7 (section 4): the drift of the raw ratio with cell length (0.37 / 0.54 / 0.62 at
# +3000 / 4500 / 6000 A) is the read-out window (at +3000 A 95 % of the oxide runs' specular beam
# is still in the window ramp or below it), not the surface-step Fresnel term; +3000 and +4500 A
# are read-out-truncated; the absorption-only ratio is 0.505-0.532 over 3000-9000 A (3.1 % from
# the model value 0.5213); nothing asserted on it (E9 M1)


@pytest.fixture(scope="module")
def flat_runs():
    """Flat Si(001) [100], r = 0.1: clean, 2 nm oxide with V'_ox = 0.40 V and with V'_ox = 0 (the
    last separates the layer's absorption from the change of the crystal's surface step, E9 M4);
    one box and one grid for the three runs; r(f) at the central bin read in the vacuum above the
    top of the layer (windowed_reflection)."""
    pytest.importorskip("abtem")
    ref = oxide_spec()
    out = {}
    for name, ox_ in (("clean", None), ("oxide", ref), ("oxide_no_absorption",
                                                        oxide_spec(Vi=0.0))):
        c = atomistic_case(oxide=ox_, r=0.1, extra_length_A=C_EXTRA_LENGTH_A,
                           length_for_oxide=ref)
        ew = run_realisation(c["cell"], potential=c["potential"], beam=c["beam"],
                             params=c["params"], realisation=0, seed=None)
        # top of the reference layer above the box bottom (the same window for the three runs):
        # depth below the kept top plane + (1 - f) t + N a/4 + a/8 (audit A8 M2; E4 used 20.67)
        top = c["cell"].metadata["layout"]["depth_below_A"] + c["stack_A"]
        out[name] = dict(c=c, ew=ew, R=windowed_reflection(ew, c, x_window_A=top + 5.0))
    return out


def test_flat_oxide_amplitude_ratio_is_reported(flat_runs):
    c = flat_runs["oxide"]["c"]
    r0, r1, r2 = (flat_runs[k]["R"]["r"] for k in ("clean", "oxide", "oxide_no_absorption"))
    assert flat_runs["clean"]["R"]["f_per_A"] == flat_runs["oxide"]["R"]["f_per_A"]  # same bin
    ko = k_perp_in_layer_per_A(c["theta"], E_KEV, V_OX, 0.40)
    model = float(np.exp(-2 * ko.imag * 20.0))
    print(f"(c) flat Si(001) [100], r = 0.1, bin {flat_runs['clean']['R']['theta_bin_rad'] * 1e3:.4f}"
          f" mrad: |r| clean {abs(r0):.4f}, 2 nm oxide {abs(r1):.4f}, same without layer "
          f"absorption {abs(r2):.4f}; ratio oxide/clean {abs(r1 / r0):.4f} (phase "
          f"{np.angle(r1 / r0):+.4f} rad), absorption only {abs(r1 / r2):.4f} (phase "
          f"{np.angle(r1 / r2):+.4f} rad); E9 zero-loss MODEL value exp(-2 Im k' t) = {model:.4f} "
          f"(E9 M1: a model value, not a bound; reported, not pass/fail)")
    assert all(np.isfinite(x) and abs(x) > 0 for x in (r0, r1, r2))
    md = flat_runs["oxide"]["ew"].metadata["overlayer"]
    assert md["internal_angle_in_layer_in_rad"] == pytest.approx(17.902e-3, abs=5e-7)   # out:36
    assert md["iam_sio2_at_declared_density_V"] == pytest.approx(10.3394, abs=5e-5)     # out:166
    assert md["crystal_mean_inner_potential_V"] == pytest.approx(13.9028, abs=5e-5)     # out:171


# --------------------------------------------------------------------------------------------------
# (d) conformal a/4 step under the oxide: smoke test only
# --------------------------------------------------------------------------------------------------
def test_conformal_a4_step_under_the_oxide_smoke():
    pytest.importorskip("abtem")
    c = atomistic_case(oxide=oxide_spec(), r=0.1, edges="parallel", layers=(0, 1), widths=(4, 4),
                       boundary=-1)
    ew = run_realisation(c["cell"], potential=c["potential"], beam=c["beam"], params=c["params"],
                         realisation=0, seed=None)
    assert np.all(np.isfinite(ew.psi))
    ov = ew.metadata["overlayer"]
    assert ov["conformal"] is True
    steps = c["structure"].metadata["steps"]
    assert [s["overlayer"]["buried_relation"] for s in steps] == ["screw", "screw"]
    assert all(s["overlayer"]["buried_b4"].startswith("B4 applies") for s in steps)
    terr = c["cell"].metadata["terraces"]

    def central(t):
        y0, y1 = t["range_A"]
        return (y0 + 0.25 * (y1 - y0), y1 - 0.25 * (y1 - y0))
    res = terrace_step_phase(ew, theta_out_ext_rad=c["theta"], aperture_radius_per_A=0.5,
                             upper_y_range_A=central(terr[1]), lower_y_range_A=central(terr[0]))
    expect = -4 * np.pi / ew.metadata["beam"]["wavelength_A"] * (A_SI_A / 4) * np.sin(c["theta"])
    print(f"(d) SMOKE (not a physics claim; fixed-beam gate not passed): a/4 step under a conformal "
          f"2 nm oxide, Delta_phi = {res['delta_phi_rad']:+.4f} rad, geometric "
          f"{(expect + np.pi) % (2 * np.pi) - np.pi:+.4f} rad (10.9761 rad unwrapped, E9 out:91); "
          f"amplitudes {res['amplitude_lower']:.4f} / {res['amplitude_upper']:.4f}")


def test_amorphous_si_layer_between_oxide_and_crystal():
    """E9 M5 option: a-Si (TEST_ONLY V_a 13.6 V, V'_a 0.47 V) of 10 A between the crystal boundary
    and the oxide; each region carries its own complex potential."""
    spec = oxide_spec(t_a=10.0, N=14, Va=13.6, Vai=0.47)
    cell = _two_terrace_cell(spec, 0.0, 0.05)
    base = ContinuumTerracePotential(cell, V0_V=13.903, V0_label="TEST_ONLY: substrate V0",
                                     physical_absorption=NO_ABS, surface_profile="sharp")
    pot = ContinuumOxidePotential(base, oxide=spec)
    grid = make_grid(cell, nx=int(round(cell.extent_x_A / 0.05)), ny=40)
    (arr,), _ = pot.layer_arrays(grid, dz_A=1.0, n_slices=int(round(cell.length_z_A)))
    st = cell.metadata["terraces"][0]["oxide"]
    assert st["interface_x_A"] - st["crystal_boundary_x_A"] == pytest.approx(10.0)
    x = grid.x_A()
    a_si = (x > st["crystal_boundary_x_A"] + 4) & (x < st["interface_x_A"] - 4)
    oxl = (x > st["interface_x_A"] + 4) & (x < st["top_x_A"] - 4)
    np.testing.assert_allclose(arr[a_si, 10], 13.6 + 0.47j, rtol=1e-9)
    np.testing.assert_allclose(arr[oxl, 10], V_OX + 0.40j, rtol=1e-9)
    np.testing.assert_allclose(arr[x < st["crystal_boundary_x_A"] - 4, 10].real, 13.903,
                               rtol=1e-9)
    assert cell.metadata["layout"]["overlayer"]["amorphous_si_thickness_A"] == 10.0
