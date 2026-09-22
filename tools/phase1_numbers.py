#!/usr/bin/env python3
"""Physics numbers quoted in the Phase 1 revisions of the summary documents (2026-09-22).

Every physics number that the Phase 1 synthesis adds to docs/ is printed by this script (the
bibliography and citation counts are printed by tools/bib/crossref_check.py and
tools/lit/citation_lists.py), which reuses the
reference calculator (tools/reflection_step_phase_calculator.py) so that the same quantity carries
the same value everywhere. Conventions: docs/physics_conventions.md (exp(+ik.r), glancing angles,
signed step phase). Beam energy 200 keV (PROJECT_INPUT, Ali, 2026-09-22).

Premises (DERIVED_HERE):
  * The step phase is evaluated at the internal Bragg condition of the stated specular order
    (the reflectivity maximum), as in the calculator's SpecularCondition.
  * V0 = 12.0 V is the repository ASSUMPTION (model_assumptions B1); 12.53 V is the Si endpoint
    of the fit printed in Fig. 2c of arXiv:2607.05948v1 (DFT, bulk-terminated (110) slab; read in
    docs/agent_reports/L5_open_access_check.md section 4). No value is endorsed here.
  * Height bias (premise A): the glancing angle is NOT measured but taken as the external angle of
    the internal Bragg condition computed with the assumed V0, and the phase Delta_phi is correctly
    unwrapped; the height is inferred as h_inf = |Delta_phi| / (2 K_ext(V0_assumed)). With
    V0_true = V0_assumed + dV the bias is h_inf - h_true. If theta_ext is measured independently
    (PROJECT_INPUT item 7), V0 does not enter the height and the bias is zero.
  * dh/dV0 is the derivative of h_inf with respect to the ASSUMED V0 at 12.0 V (central difference,
    +-0.01 V) for a fixed phase; it is proportional to h, so it is also printed in percent of h.

Run:  venv/bin/python tools/phase1_numbers.py
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import numpy as np

_HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "calc", _HERE / "reflection_step_phase_calculator.py")
calc = importlib.util.module_from_spec(_spec)
sys.modules["calc"] = calc
_spec.loader.exec_module(calc)

E_KEV = 200.0
V0_ASSUMED = 12.0
V0_DFT = 12.53
A = calc.A_SI_A
D111 = A / np.sqrt(3.0)


def phase_block(label: str, d: float, n: int, h: float) -> dict:
    lo = calc.SpecularCondition(d, n, E_KEV, V0_ASSUMED)
    hi = calc.SpecularCondition(d, n, E_KEV, V0_DFT)
    p_lo = lo.step_phase(h)["abstotal"]
    p_hi = hi.step_phase(h)["abstotal"]
    # bias of the height inferred with V0_ASSUMED when the truth is V0_DFT
    h_inf = p_hi / (2.0 * lo.K_ext)
    # derivative of h_inf with respect to the assumed V0 at V0_ASSUMED, phase fixed at its 12.0 V value
    dv = 0.01
    k_m = calc.SpecularCondition(d, n, E_KEV, V0_ASSUMED - dv).K_ext
    k_p = calc.SpecularCondition(d, n, E_KEV, V0_ASSUMED + dv).K_ext
    dh_dv = (p_lo / (2.0 * k_p) - p_lo / (2.0 * k_m)) / (2.0 * dv)
    out = dict(label=label, h=h, dh_dv=dh_dv, dh_dv_pct=100.0 * dh_dv / h,
               th_ext_lo=lo.theta_ext * 1e3, th_ext_hi=hi.theta_ext * 1e3,
               phi_lo=p_lo, phi_hi=p_hi, dphi=p_hi - p_lo,
               bias=h_inf - h, bias_per_V=(h_inf - h) / (V0_DFT - V0_ASSUMED))
    print(f"{label}")
    print(f"   h = {h:.4f} A;  theta_ext = {out['th_ext_lo']:.3f} mrad (12.0 V), "
          f"{out['th_ext_hi']:.3f} mrad (12.53 V)")
    print(f"   |Delta_phi| = {p_lo:.4f} rad (12.0 V), {p_hi:.4f} rad (12.53 V); "
          f"change = {out['dphi']:+.4f} rad")
    print(f"   dh_inf/dV0(assumed) at 12.0 V = {dh_dv:+.4f} A/V = {100.0*dh_dv/h:+.3f} % of h per volt")
    print(f"   height inferred with 12.0 V when V0 is 12.53 V: bias h_inf - h = "
          f"{out['bias']:+.4f} A  ({out['bias_per_V']:+.4f} A per volt of underestimate)")
    return out


def main() -> None:
    print("=" * 96)
    print("PHASE 1 NUMBERS (200 keV; V0 12.0 V ASSUMPTION versus 12.53 V DFT endpoint)")
    print("=" * 96)
    r444 = phase_block("Si(111) (4,-4,4), single-bilayer step h = d_111", D111, 4, D111)
    r008 = phase_block("Si(001) (0,0,8), double-layer step h = a/2", A / 4.0, 2, A / 2.0)
    r0012 = phase_block("Si(001) (0,0,12), double-layer step h = a/2", A / 4.0, 3, A / 2.0)

    # Self-checks: the (4,-4,4) 12.0 V values must agree with the calculator table in docs/03.
    checks = [
        ("theta_ext (4,-4,4) at 12.0 V [mrad]", r444["th_ext_lo"], 13.64, 5e-3),
        ("theta_ext (0,0,8) at 12.0 V [mrad]", r008["th_ext_lo"], 16.5, 5e-2),
        ("sign of dphi for V0 increase (must be < 0)", float(r444["dphi"] < 0), 1.0, 0.0),
        ("sign of bias for underestimated V0 (must be < 0)", float(r444["bias"] < 0), 1.0, 0.0),
        # values quoted in docs/03, docs/06 item 20, model_assumptions B1 and source map SM04
        ("dh/dV0 (4,-4,4) bilayer [A/V]", r444["dh_dv"], 0.049, 1e-3),
        ("dh/dV0 (4,-4,4) [% of h per V]", r444["dh_dv_pct"], 1.56, 5e-3),
        ("dh/dV0 (0,0,8) a/2 step [A/V]", r008["dh_dv"], 0.029, 1e-3),
        ("dh/dV0 (0,0,8) [% of h per V]", r008["dh_dv_pct"], 1.07, 5e-3),
        ("change of |dphi| (4,-4,4), 12.0 -> 12.53 V [rad]", r444["dphi"], -0.178, 1e-3),
        ("change of |dphi| (0,0,8), 12.0 -> 12.53 V [rad]", r008["dphi"], -0.128, 1e-3),
    ]
    npass = 0
    print("-" * 96)
    for name, got, want, tol in checks:
        ok = abs(got - want) <= tol
        npass += ok
        print(f"   [{'PASS' if ok else 'FAIL'}] {name}: {got:.4f} (expected {want} +- {tol})")
    print(f"   {npass}/{len(checks)} checks pass")
    if npass != len(checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
