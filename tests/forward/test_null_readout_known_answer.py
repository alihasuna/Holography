"""Surface-resolved null-test read-out on REAL engine exit waves of an exactly translation-covariant
case (audit A6 N-1/N-2, X2).

Case (A6 section 4, `resolved_known_answer.py`): the rung-2 laterally uniform periodic continuum
(ContinuumPeriodicPotential; V0 13.902843 V, V_008 1.035742 V, TEST_ONLY r, P2's two-beam centre
16.134773 mrad, Fresnel propagator, complex128, dx 0.025 A, dz 1 A, clean depth 100 A) and the same
crystal translated by R = (a/2, 0, 0) in an identical box. Known answers (A6, DERIVED there): with
the beam envelope moved with the crystal, E_B(z_s) = E_A(z_s) exp(i expected) in every bin (up to
the sub-pixel representation of a/2 = 108.618 px, measured <= 2.4e-3 rad by A6); with the beam
fixed, the same where the reflection has built up (P2 5.3: >= 2600 A at r = 0.1).

  * A6's converged fixed-beam case (L 6000 A, H = L tan(theta) - 6 A, edge 4 A, exit exclusion
    750 A): converged beyond 2500 A. Its last bin (|B|/|A| = 1.029, 254 A before the end of B's lit
    core) is EXCLUDED by the lit-end limit and no longer decides the verdict (E1's code: None).
  * non-converged case: the study's beam and read-out in a cell shorter than the build-up
    (L 2500 A): every included bin fails, converged is False.
  * the study's beam (study_depth100.yaml: H = L_z tan(theta) - gap - a/2 - 1 A, edge 2, gap 2) and
    the study's surface_resolved block at the L_z of its L5k points, r = 0.1: the fixed-beam ratio
    converges and the moved-beam control passes in every bin. With RH_NULL_READOUT_LONG=1 also at
    the L_z of the L10k points for r = 0.1 and 0.05 (about 6 minutes; run for the X2 report).
TEST_ONLY throughout; no tolerance of the study is changed here (1e-2 rad, 1e-2)."""
import os
import time
from pathlib import Path

import numpy as np
import pytest

import null_test_cases as ntc
from ladder_cases import V008_R2, V0_R2, rung2_g_per_A, rung2_theta_centre
from reflection_holo.forward.cell import build_continuum_cell
from reflection_holo.forward.multislice import (ContinuumPeriodicPotential, MultisliceParams,
                                                NumericalAbsorber, PhysicalAbsorption, SheetBeam,
                                                run_realisation)
from reflection_holo.io.config import load_yaml_unique

TH = rung2_theta_centre()
RX = 2.71545                      # a/2 (A6: 108.618 pixels of 0.025 A)
XS_A = 115.0                      # 15 A bulk absorber + 100 A clean depth
LAB = "TEST_ONLY: X2 known-answer check of the null-study read-out (rung-2 continuum)"
STUDY = Path(__file__).resolve().parents[2] / "scripts" / "hpc" / "null_test_study"
A6_KW = dict(radius_per_A=0.1, x_cut_A=2.0, taper_A=3.0, min_height_A=5.0, bin_A=500.0,
             exit_excl_A=750.0, tol_phase_rad=1e-2, tol_amp=1e-2, amp_floor_rel=0.05)


def _study_block():
    cfg = load_yaml_unique((STUDY / "study_depth100.yaml").read_bytes())
    return {k: float(v) for k, v in cfg["surface_resolved"].items()}, cfg["points"]


def _cells(r, L, H):
    ent, dx = 10.0, 0.025
    vacA = H + 2.0 + RX + L * np.tan(TH) + 60.0
    nx = int(np.ceil((XS_A + vacA + 10.0) / dx))
    top = nx * dx - XS_A - vacA
    out = {}
    for key, xs, vac in (("A", XS_A, vacA), ("B", XS_A + RX, vacA - RX)):
        cell = build_continuum_cell(extent_y_A=10.0, terrace_y_bounds_A=[0.0, 10.0],
                                    terrace_heights_A=[0.0], crystal_length_z_A=L - ent,
                                    vacuum_above_A=vac, depth_below_A=xs, bulk_absorber_A=15.0,
                                    top_absorber_A=top, entrance_vacuum_z_A=ent)
        pot = ContinuumPeriodicPotential(
            cell, V0_V=V0_R2, V0_label=LAB, harmonics=((rung2_g_per_A(), V008_R2, 0.0),),
            harmonics_label=LAB, surface_profile="sharp",
            physical_absorption=PhysicalAbsorption(model="proportional", ratio=r, label=LAB))
        out[key] = (cell, pot)
    assert abs(out["A"][0].extent_x_A - out["B"][0].extent_x_A) < 1e-9
    params = MultisliceParams(energy_keV=200.0, nx=nx, ny=1, dz_A=1.0, propagator="fresnel",
                              band_limit="2/3", backend="numpy", precision="complex128", threads=4,
                              absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                              theta_out_ext_rad=TH, buildup_depth_A=20.0,
                              working_reflections_hkl=())
    return out, params


def run_case(*, r, L, H, edge, gap, variants=("fixed", "moved")):
    """B's beam: bottom `gap` above B's surface; A fixed: B's beam; A moved: translated by -R_x."""
    cells, params = _cells(r, L, H)
    beam = dict(height_A=H, edge_A=edge, theta_in_ext_rad=TH, theta_label=LAB)
    bB = SheetBeam(x_bottom_A=XS_A + RX + gap, **beam)
    bA = dict(fixed=bB, moved=SheetBeam(x_bottom_A=XS_A + gap, **beam))
    t0 = time.time()
    ews = dict(B=run_realisation(cells["B"][0], potential=cells["B"][1], beam=bB, params=params,
                                 realisation=0, seed=None))
    for v in variants:
        ews[v] = run_realisation(cells["A"][0], potential=cells["A"][1], beam=bA[v],
                                 params=params, realisation=0, seed=None)
    lam = ews["B"].metadata["beam"]["wavelength_A"]
    expected = -2.0 * (2 * np.pi / lam) * np.sin(TH) * RX          # -(k_out - k_in).R
    pairs = {v: dict(params=params, A=cells["A"], B=cells["B"], beams=dict(A=bA[v], B=bB))
             for v in variants}
    print(f"continuum r {r}, L {L:.1f} A, H {H:.3f} A, edge {edge}, gap {gap}, nx {params.nx}: "
          f"{len(variants) + 1} runs in {time.time() - t0:.0f} s")
    return ews, pairs, expected


def readout(ews, pairs, expected, variant, kw):
    r = ntc.resolved_translation(ews[variant], ews["B"], pairs[variant], expected_rad=expected,
                                 **kw)
    print(f"  {variant} beam: {r['verdict']}; lit-end limit {r['lit_strip']['lit_limit_A']:.1f} A "
          f"(margin {r['lit_strip']['top_edge_fringe_margin_A']:.1f} A)")
    for q in r["rows"]:
        why = f" ({q['excluded_because'][0]})" if q["excluded_because"] else ""
        print(f"    z_s {q['z_start_A']:7.1f}-{q['z_end_A']:7.1f} (d {q['d_start_A']:6.1f}): err "
              f"{q['err_rad']:+.2e} rad, |B|/|A| {q['amp_ratio']:.5f}, |E_A| {q['E_A_abs']:.4f}: "
              f"{q['status']}{why}")
    return r


def _within(q, kw):
    return abs(q["err_rad"]) <= kw["tol_phase_rad"] and abs(q["amp_ratio"] - 1) <= kw["tol_amp"]


@pytest.fixture(scope="module")
def a6_case():
    L = 6000.0
    return run_case(r=0.1, L=L, H=L * np.tan(TH) - 6.0, edge=4.0, gap=2.0)


def test_a6_converged_case_is_converged_and_its_last_bin_is_excluded(a6_case):
    ews, pairs, expected = a6_case
    r = readout(ews, pairs, expected, "fixed", A6_KW)
    assert r["converged"] and r["converged_beyond_A"] == pytest.approx(2500.0)
    assert r["n_bins_beyond"] >= 3
    last = r["last_bin"]
    assert last["status"] == "excluded" and "lit-end limit" in last["excluded_because"][0]
    assert abs(last["amp_ratio"] - 1) > A6_KW["tol_amp"]       # it WOULD fail (A6: 1.029)
    assert all(not any("amplitude floor" in w for w in q["excluded_because"]) for q in r["rows"])
    m = readout(ews, pairs, expected, "moved", A6_KW)
    assert all(_within(q, A6_KW) for q in m["rows"])           # every bin, excluded ones too
    assert m["converged"] and m["converged_beyond_A"] == 0.0


def test_short_cell_with_the_study_beam_is_not_converged():
    kw, _ = _study_block()
    L = 2500.0
    H = ntc.sheet_height_lit_to_exit_A(L_z_A=L, theta=TH, gap=2.0)
    ews, pairs, expected = run_case(r=0.1, L=L, H=H, edge=2.0, gap=2.0, variants=("fixed",))
    ntc.check_lit_to_exit(pairs["fixed"], exit_excl_A=kw["exit_excl_A"])
    r = readout(ews, pairs, expected, "fixed", kw)
    inc = [q for q in r["rows"] if q["included"]]
    assert inc and all(q["status"] == "fail" for q in inc)
    assert not r["converged"] and r["n_bins_beyond"] == 0
    assert r["converged_beyond_A"] == inc[-1]["d_end_A"]
    assert r["verdict"].startswith("NOT converged")


def _study_beam_case(r, Lz_study):
    kw, pts = _study_block()
    L = float(round(Lz_study))                    # dz = 1 A: L_z rounded to a whole slice count
    H = ntc.sheet_height_lit_to_exit_A(L_z_A=L, theta=TH, gap=2.0)
    ews, pairs, expected = run_case(r=r, L=L, H=H, edge=2.0, gap=2.0)
    for v in pairs:
        ntc.check_lit_to_exit(pairs[v], exit_excl_A=kw["exit_excl_A"])
    fixed = readout(ews, pairs, expected, "fixed", kw)
    moved = readout(ews, pairs, expected, "moved", kw)
    assert fixed["converged"], fixed["verdict"]
    assert moved["converged"] and moved["converged_beyond_A"] == 0.0
    assert all(_within(q, kw) for q in moved["rows"])            # every bin, excluded ones too
    for res in (fixed, moved):                                   # lit to the exit plane: the
        top = max(q["E_A_abs"] for q in res["rows"])             # floor removes nothing
        print(f"  smallest bin |E_A| / largest: {min(q['E_A_abs'] for q in res['rows']) / top:.3f}"
              f" (amplitude floor {kw['amp_floor_rel']})")
        assert not any(any("amplitude floor" in w for w in q["excluded_because"])
                       for q in res["rows"])
    return fixed, moved


def _study_Lz(name):
    _, pts = _study_block()
    p = next(q for q in pts if q["name"] == name)
    th = ntc.theta_0008() if p["theta"] == "bragg_0008_mip" else float(p["theta"]) * 1e-3
    return ntc.cell_length_z_A(theta=th, azimuth=p["azimuth"], gap=p["beam_gap_A"],
                               extra_A=float(p["extra_length_A"]))


def test_study_beam_L5k_fixed_converges_and_moved_passes():
    _study_beam_case(0.1, _study_Lz("tfix110_bragg_abs10_L5k"))


LONG = os.environ.get("RH_NULL_READOUT_LONG") == "1"


@pytest.mark.skipif(not LONG, reason="L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1")
@pytest.mark.parametrize("r, name", [(0.1, "tfix110_bragg_abs10_L10k"),
                                     (0.05, "tfix110_bragg_abs05_L10k")])
def test_study_beam_L10k_fixed_converges_and_moved_passes(r, name):
    _study_beam_case(r, _study_Lz(name))
