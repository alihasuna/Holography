#!/usr/bin/env python3
"""X5: numbers behind the fixes of audit A9b (docs/agent_reports/X5_a9b_fixes.md), printed from the
code (reflection_holo.structure.oxide) with a first-principles cross-check of f.

* A9b m2: what the 0.05-layer rounding guard (structure.oxide.MIN_ROUNDING_MARGIN_LAYERS) means in
  thickness and density at t_ox = 2 nm, 2.20 g/cm^3 (0.1538 A, 0.769 %, 0.0169 g/cm^3), how far a
  witness uncertainty moves the continuum depth (+-0.325 layer per +-1 A, +-0.148 layer per
  +-0.05 g/cm^3 at 2 nm), the B41 2.0 nm boundary (2.19877 g/cm^3, -0.056 %), and the consumed-layer
  count intervals (structure.oxide.consumed_count_interval) for illustrative uncertainties (not
  item-12 values; none exists yet);
* A9b n3: the height of the layer top above the top atomic planes, (1 - f) t + a/8, for the B41
  2.0 nm and 1.5 nm variants (the comments of configs/demo_smoke_si001.yaml);
* A9b M2: the consumed-layer counts DERIVED by the code for the B41 variants.

Run:  PYTHONPATH=. venv/bin/python tools/review/x5/x5_oxide_numbers.py
      (saved: tools/review/x5/x5_oxide_numbers_output.txt)
Values standing in for PROJECT_INPUT item 12 are the B41 demo values (ASSUMPTION B41); the
uncertainties below are illustrative inputs of this script (TEST values), not item-12 values.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from reflection_holo.constants import (A_SI_A, AVOGADRO_PER_MOL, M_O_G_PER_MOL,  # noqa: E402
                                       M_SI_G_PER_MOL)
from reflection_holo.structure import oxide as ox                                   # noqa: E402

a = A_SI_A
q = a / 4
f = ox.consumed_si_fraction(2.20, a)
# first-principles cross-check of f (Si atoms conserved; E9 section 3)
rho_si = 8 * M_SI_G_PER_MOL / AVOGADRO_PER_MOL / (a * 1e-8) ** 3
f_fp = (2.20 / (M_SI_G_PER_MOL + 2 * M_O_G_PER_MOL)) / (rho_si / M_SI_G_PER_MOL)
print(f"a = {a} A (B2), a/4 = {q:.6f} A, a/8 = {q / 2:.6f} A; rho_Si = {rho_si:.6f} g/cm^3; "
      f"f(2.20) = {f:.6f} (code), {f_fp:.6f} (first principles)")

print("\n== A9b m2: the 0.05-layer guard (MIN_ROUNDING_MARGIN_LAYERS = "
      f"{ox.MIN_ROUNDING_MARGIN_LAYERS}) at t_ox = 20 A, 2.20 g/cm^3")
m = ox.MIN_ROUNDING_MARGIN_LAYERS
dd = m * q
print(f"  {m} layer = {dd:.4f} A (= {dd:.3f} A) of consumed depth = {dd / f:.4f} A of thickness at "
      f"f(2.20) = {100 * dd / (f * 20.0):.3f} % of the density = {2.20 * dd / (f * 20.0):.4f} g/cm^3")
for dt in (0.5, 1.0, 2.0):
    print(f"  thickness +-{dt} A -> continuum depth +-{f * dt:.3f} A = +-{f * dt / q:.3f} layer")
for dr in (0.03, 0.05, 0.10):
    print(f"  density +-{dr} g/cm^3 at 20 A -> +-{f * 20.0 * dr / 2.20 / q:.3f} layer")

print("\n== A9b m2: the B41 counts and their rounding boundaries (structure.oxide.rounding_margin)")
for t, N in ((20.0, 7), (15.0, 5)):
    rm = ox.rounding_margin(thickness_A=t, density_g_cm3=2.20, amorphous_si_thickness_A=0.0,
                            consumed_layers=N, a_A=a)
    rho_b = rm["count_changes_at_density_g_cm3"]
    print(f"  t {t} A, N {N}: continuum {rm['continuum_layers']:.4f} layers, margin "
          f"{rm['margin_layers']:.4f} layer ({rm['margin_A']:.4f} A); the count becomes "
          f"{rm['count_changes_to']} at {rho_b:.5f} g/cm^3 ({100 * (rho_b / 2.20 - 1):+.3f} %) or "
          f"{rm['count_changes_at_thickness_A']:.4f} A; near the boundary: {rm['near_boundary']}")

print("\n== A9b m2: consumed-layer count over an uncertainty box (structure.oxide."
      "consumed_count_interval; illustrative uncertainties, TEST values)")
for t in (20.0, 15.0):
    for ut, ur in ((0.1, 0.01), (0.5, 0.03), (1.0, 0.05), (2.0, 0.10)):
        ci = ox.consumed_count_interval(thickness_A=t, thickness_uncertainty_A=ut,
                                        density_g_cm3=2.20, density_uncertainty_g_cm3=ur,
                                        amorphous_si_thickness_A=0.0, a_A=a)
        print(f"  t {t} +- {ut} A, rho 2.20 +- {ur} g/cm^3: {ci['continuum_layers_min']:.3f}-"
              f"{ci['continuum_layers_max']:.3f} layers -> counts {ci['counts']} "
              f"({', '.join(ci['parities'])}); spans a boundary: {ci['spans_boundary']}")

print("\n== A9b M2: consumed-layer counts DERIVED by the code (structure.oxide.nearest_consumed_layers)")
for t in (20.0, 15.0):
    print(f"  t {t} A, 2.20 g/cm^3, no a-Si: {ox.nearest_consumed_layers(thickness_A=t, density_g_cm3=2.20, amorphous_si_thickness_A=0.0, a_A=a)}")

print("\n== A9b n3: the top of the layer above the top atomic planes, (1 - f) t + a/8")
for t in (20.0, 15.0):
    print(f"  t {t} A: (1 - {f:.6f}) x {t} + {q / 2:.6f} = {(1 - f) * t + q / 2:.4f} A "
          f"(= {(1 - f) * t + q / 2:.2f} A)")
