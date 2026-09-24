#!/usr/bin/env python3
"""X6: numbers behind the fixes of re-audit A10b (docs/agent_reports/X6_a10b_fixes.md), printed from
the code (reflection_holo.structure.oxide) with first-principles cross-checks.

* A10b m3: how far the item-12 thickness, density and a-Si thickness move the continuum depth
  f(rho) t + t_a, in layers of a/4 (a-Si 0.7365 layer per A, 2.3 times the oxide's 0.3252);
* A10b m2: the coverage of the factor k = 2 applied to a standard uncertainty (95.45 % for a
  normally distributed quantity), and the count intervals of structure.oxide.item12_count_interval
  for illustrative uncertainties (TEST values, not item-12 values; none exists yet), for both
  uncertainty kinds;
* A10b M1: the two parity variants of the 2.0 nm interval [6, 7]: the interface overlap or gap of
  the continuum layer against the kept atomistic crystal when the thickness is not altered (more
  than a/8 for the variant that is not the nearest count; at most 1.5 a/4);
* A10b n1: the one-thickness, two-count case at the rounding tie (t = 6.5 (a/4)/f) and the size the
  refusal states for it.

Run:  PYTHONPATH=. venv/bin/python tools/review/x6/x6_oxide_numbers.py
      (saved: tools/review/x6/x6_oxide_numbers_output.txt)
The oxide values are the B41 demo values (ASSUMPTION B41: 2.20 g/cm^3; 20 A or 15 A); the
uncertainties are illustrative inputs of this script (TEST values).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from reflection_holo.constants import (A_SI_A, AVOGADRO_PER_MOL, M_O_G_PER_MOL,  # noqa: E402
                                       M_SI_G_PER_MOL)
from reflection_holo.structure import oxide as ox                                   # noqa: E402

a = A_SI_A
q = a / 4
f = ox.consumed_si_fraction(2.20, a)
rho_si = 8 * M_SI_G_PER_MOL / AVOGADRO_PER_MOL / (a * 1e-8) ** 3
f_fp = (2.20 / (M_SI_G_PER_MOL + 2 * M_O_G_PER_MOL)) / (rho_si / M_SI_G_PER_MOL)
print(f"a = {a} A (B2), a/4 = {q:.6f} A, a/8 = {q / 2:.6f} A, 1.5 a/4 = {1.5 * q:.4f} A; "
      f"f(2.20) = {f:.6f} (code), {f_fp:.6f} (first principles)")

print("\n== A10b m3: depth per unit of each item-12 quantity (layers of a/4), at 20 A, 2.20 g/cm^3")
per_asi = 1.0 / q
per_t = f / q
per_rho = f * 20.0 / 2.20 / q * 0.05                 # f is proportional to rho
print(f"  a-Si thickness: 1 A of a-Si = 1 A of depth = {per_asi:.4f} layer per A")
print(f"  oxide thickness: f(2.20) = {f:.4f} A of depth per A = {per_t:.4f} layer per A")
print(f"  density: +-0.05 g/cm^3 at 20 A = +-{per_rho:.4f} layer")
print(f"  ratio a-Si / oxide thickness per A: {per_asi / per_t:.2f}")

print("\n== A10b m2: coverage of the factor k = STANDARD_COVERAGE_FACTOR = "
      f"{ox.STANDARD_COVERAGE_FACTOR} for a normally distributed quantity")
k = ox.STANDARD_COVERAGE_FACTOR
print(f"  P(|x - mu| <= {k} sigma) = erf({k}/sqrt(2)) = {100 * math.erf(k / math.sqrt(2)):.2f} % "
      f"(about 95 %)")
for kind in ox.UNCERTAINTY_KINDS:
    print(f"  {kind}: {ox.COVERAGE_STATEMENT[kind]}")

print("\n== A10b m2, m3: item12_count_interval for illustrative uncertainties (TEST values)")
CASES = ((20.0, 1.0, 0.05, 0.0, 0.1), (20.0, 0.1, 0.01, 0.0, 0.1), (20.0, 1.0, 0.05, 0.0, 1.0),
         (15.0, 0.5, 0.03, 0.0, 0.1), (15.0, 1.0, 0.05, 0.0, 0.1), (15.0, 0.5, 0.03, 0.0, 1.0),
         (15.0, 0.5, 0.03, 5.0, 0.5))
for t, ut, ur, ta, ua in CASES:
    for kind in ox.UNCERTAINTY_KINDS:
        ci = ox.item12_count_interval(thickness_A=t, thickness_uncertainty_A=ut, density_g_cm3=2.20,
                                      density_uncertainty_g_cm3=ur, amorphous_si_thickness_A=ta,
                                      amorphous_si_thickness_uncertainty_A=ua,
                                      uncertainty_kind=kind, a_A=a)
        hw = ci["depth_half_width_layers"]
        print(f"  t {t} +- {ut} A, rho 2.20 +- {ur} g/cm^3, a-Si {ta} +- {ua} A, {kind}: "
              f"{ci['continuum_layers_min']:.3f}-{ci['continuum_layers_max']:.3f} layers "
              f"(nominal {ci['continuum_layers_nominal']:.4f}, nearest {ci['nearest_count']}) -> "
              f"counts {ci['counts']}; depth half-ranges: thickness {hw['thickness']:.4f}, "
              f"density {hw['density']:.4f}, a-Si {hw['amorphous_si']:.4f} layer (clipped at 0); "
              f"parity variant "
              + ("not needed" if len(ci["counts"]) == 1 else
                 f"lower {ci['counts'][0]} / upper {ci['counts'][1]}" if len(ci["counts"]) == 2
                 else "REFUSED (more than one boundary)"))

print("\n== A10b M1: parity variants of the 2.0 nm interval (thickness not altered)")
depth = f * 20.0
for parity, n in zip(ox.PARITY_VARIANTS, (6, 7)):
    ov = depth - n * q
    print(f"  {parity} variant, count {n} ({ox.count_parity(n)}): f t - N a/4 = {depth:.4f} - "
          f"{n * q:.4f} = {ov:+.4f} A = {ov / q:+.4f} layer ({'overlap' if ov > 0 else 'gap'}; "
          f"|value| {'>' if abs(ov) > q / 2 else '<='} a/8 = {q / 2:.4f} A)")

print("\n== A10b n1: one thickness, two counts at the rounding tie")
t_tie = 6.5 * q / f
sub = q / f                                           # Dt - DN (a/4)/f with Dt = 0, DN = 1
lo, hi = ox.SUBLAYER_RATE_DIFFERENCE_RAD_PER_A
print(f"  t = 6.5 (a/4)/f = {t_tie:.6f} A: counts 6 and 7 both pass |N a/4 - f t| <= a/8 + "
      f"1e-9 A; sub-layer thickness difference (a/4)/f = {sub:.4f} A, i.e. about "
      f"{lo * sub:.2f}-{hi * sub:.2f} rad between the engines (the 1-D estimate of A9b C4)")
