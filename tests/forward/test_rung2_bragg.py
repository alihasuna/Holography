"""Ladder rung 2 (docs/05 section 4.4): Bragg-case (0,0,8) reflection of a laterally uniform
periodic continuum potential V(x) = V0 + 2 V_g cos(2 pi g (x - x_s)) (1 + i r), g = 8/a, against
the EXACT semi-infinite reference of docs/agent_reports/P2_rung2_reference.md (tool
tools/physics_checks/rung2_reference.py, imported by ladder_cases.rung2_measure; not re-derived).

Test R2-A exactly as P2 section 8 proposes (cell, sheet beam, angle, r = 0.1 and 0.05, dx 0.025 A,
dz 1 A, both propagators, read-out with flat_reflection_coefficient at x_s, no fitted phase or
angle offset). The pass criteria were set by P2 BEFORE any engine run (P2 8.4) and are copied here
unchanged; they are never loosened:
  (a) max over the bins with |eta| <= 3 of |r_engine - R_ref| <= T_A = 1.5e-3 (complex difference),
      for r = 0.1 (clean depth 100 A, exit 5000 A after the top-edge contact) and r = 0.05 (150 A,
      10000 A), with the Fresnel propagator against model "exact" and the exact propagator against
      model "engine_exact_propagator" (P2 4.1, 4.2);
  (b) r = 0.1, |eta| <= 0.9: |arg(r_exact-prop/r_Fresnel) - arg(R_engine_exact_propagator/R_exact)|
      <= 2e-4 rad (same grid, same bins);
  (c) r = 0.1, Fresnel: max |dR| at dx = 0.05 A over that at dx = 0.025 A >= 2^1.5 (order >= 1.5).
Guards against a vacuous test (not tolerances): each run has bins on both sides of the plateau and
inside it.

R2-B (r = 0, Darwin sweep, clean depth 250 A, exit 30000 A, vacuum-only read-out, |eta| <= 0.5,
T_B = 3e-2) is OPTIONAL and QUALITATIVE (P2 8.4): it runs only with RH_RUNG2_R2B=1 and is not part
of the engine's rung-2 status.
"""
import functools
import os

import numpy as np
import pytest

from ladder_cases import V008_R2, V0_R2, rung2_g_per_A, rung2_measure, rung2_reference

T_A = 1.5e-3            # P2 8.4 (a)
ETA_A = 3.0
T_PROP = 2e-4           # P2 8.4 (b), rad
ETA_PROP = 0.9
ORDER_MIN = 1.5         # P2 8.4 (c)
T_B = 3e-2              # P2 8.4, R2-B (optional, qualitative)
ETA_B = 0.5

COMMON = dict(dz=1.0, H=24.0, edge=4.0, gap=2.0, absorber_A=15.0, top_A=10.0, W0=100.0,
              entrance_A=10.0, extra_vacuum_A=150.0, buildup_A=20.0, precision="complex128")
R2A = {0.1: dict(clean_A=100.0, exit_after_top_contact_A=5000.0),
       0.05: dict(clean_A=150.0, exit_after_top_contact_A=10000.0)}
R2B = dict(clean_A=250.0, exit_after_top_contact_A=30000.0)


@functools.lru_cache(maxsize=None)
def _run(r, propagator, dx):
    return rung2_measure(r, dx=dx, propagator=propagator, **R2A[r], **COMMON)


def _table(res, sel):
    lines = [f"  {res['propagator']} r-model {res['model']}, dx {res['dx']:.5f} A, nx {res['nx']}, "
             f"{res['n_slices']} slices, x_s {res['x_s']:.3f} A, run {res['time_s']:.1f} s"]
    for e, r_, R_ in zip(res["eta"][sel], res["r"][sel], res["R_ref"][sel]):
        lines.append(f"    eta {e:+7.3f}: engine {abs(r_):.5f} exp({np.angle(r_):+.5f} i), ref "
                     f"{abs(R_):.5f} exp({np.angle(R_):+.5f} i), |dR| {abs(r_ - R_):.2e}")
    return "\n".join(lines)


def _guard(res, lim):
    e = res["eta"][np.abs(res["eta"]) <= lim]
    assert len(e) >= 10 and e.min() < -1.0 and e.max() > 1.0
    assert np.count_nonzero(np.abs(e) <= 0.9) >= 4


@pytest.mark.parametrize("propagator", ["fresnel", "exact"])
@pytest.mark.parametrize("r", [0.1, 0.05])
def test_r2a_reflection_amplitude_and_phase_across_the_plateau(r, propagator):
    res = _run(r, propagator, 0.025)
    sel = np.abs(res["eta"]) <= ETA_A
    d = np.abs(res["r"][sel] - res["R_ref"][sel])
    print(f"\nR2-A r = {r}, {propagator}: {sel.sum()} bins |eta| <= {ETA_A}, max |dR| = "
          f"{d.max():.3e} (T_A = {T_A}), max |d arg| = "
          f"{np.max(np.abs(np.angle(res['r'][sel] / res['R_ref'][sel]))):.3e} rad\n"
          + _table(res, sel))
    _guard(res, ETA_A)
    assert d.max() <= T_A


def test_r2a_exact_minus_fresnel_propagator_matches_the_oneway_model():
    F, X = _run(0.1, "fresnel", 0.025), _run(0.1, "exact", 0.025)
    assert np.array_equal(F["f_per_A"], X["f_per_A"])            # same grid, same bins
    sel = np.abs(F["eta"]) <= ETA_PROP
    meas = np.angle(X["r"][sel] / F["r"][sel])
    pred = np.angle(X["R_ref"][sel] / F["R_ref"][sel])
    dev = np.abs(meas - pred)
    print(f"\nR2-A (b), r = 0.1, |eta| <= {ETA_PROP} ({sel.sum()} bins): measured arg(r_X/r_F) in "
          f"[{meas.min():+.3e}, {meas.max():+.3e}] rad, predicted [{pred.min():+.3e}, "
          f"{pred.max():+.3e}] rad, max |measured - predicted| = {dev.max():.3e} rad "
          f"(T = {T_PROP})")
    assert sel.sum() >= 4
    assert dev.max() <= T_PROP


def test_r2a_dx_convergence_order():
    e = {}
    for dx in (0.05, 0.025):
        res = _run(0.1, "fresnel", dx)
        sel = np.abs(res["eta"]) <= ETA_A
        e[dx] = float(np.max(np.abs(res["r"][sel] - res["R_ref"][sel])))
    order = np.log2(e[0.05] / e[0.025])
    print(f"\nR2-A (c), r = 0.1, Fresnel: max |dR| {e[0.05]:.3e} (dx 0.05) -> {e[0.025]:.3e} "
          f"(dx 0.025): order {order:.2f} (>= {ORDER_MIN})")
    assert order >= ORDER_MIN


def test_r2a_realised_potential_and_band_record():
    res = _run(0.1, "fresnel", 0.025)
    rh = res["realised"]["realised_harmonics"]
    assert abs(rh["V0_V"] - V0_R2) < 1e-9
    (h,) = rh["harmonics"]
    assert h["g_per_A"] == rung2_g_per_A() and h["plane_offset_A"] == 0.0
    assert abs(h["V_g_cos_V"] - V008_R2) < 1e-9 and abs(h["V_g_sin_V"]) < 1e-9
    wr = res["band"]["working_reflections"]
    assert len(wr) == 1 and list(wr.values())[0]["g_x_per_A"] == pytest.approx(rung2_g_per_A())
    th = rung2_reference().darwin_plateau(200.0, V0_R2, V008_R2, rung2_g_per_A())["theta_centre"]
    assert res["theta_in_rad"] == th and abs(th - 16.13477e-3) < 5e-9


@pytest.mark.skipif(os.environ.get("RH_RUNG2_R2B") != "1",
                    reason="R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1")
def test_r2b_optional_qualitative_darwin_sweep_vacuum_readout():
    res = rung2_measure(0.0, dx=0.025, propagator="fresnel", readout_window_above_A=60.0, **R2B,
                        **COMMON)
    sel = np.abs(res["eta"]) <= ETA_B
    d = np.abs(res["r"][sel] - res["R_ref"][sel])
    print(f"\nR2-B (optional, qualitative) r = 0: {sel.sum()} bins |eta| <= {ETA_B}, max |dR| = "
          f"{d.max():.3e} (T_B = {T_B}); arg R_ref from {np.angle(res['R_ref'][sel]).min():+.4f} "
          f"to {np.angle(res['R_ref'][sel]).max():+.4f} rad\n" + _table(res, np.abs(res["eta"]) <= 1.2))
    assert sel.sum() >= 3
    assert d.max() <= T_B
