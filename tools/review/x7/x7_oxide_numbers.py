#!/usr/bin/env python3
"""X7: numbers behind the fixes of re-audit A12 (docs/agent_reports/X7_a12_fixes.md), printed from
the code (reflection_holo.structure.oxide) with first-principles cross-checks.

* A12 m2: the consumed-layer count interval of STANDARD item-12 uncertainties is now the nominal
  continuum depth +- 2 combined standard uncertainties (the three contributions in quadrature; the
  a-Si term one-sided at its lower end); half-widths keep the worst case (the corners of the box,
  i.e. the linear sum). Printed: the example of A12 (1 A, 0.05 g/cm^3, 0.1 A) before (X6's box)
  and after, a coverage check (the analytic 95.45 % and a seeded Monte Carlo of the exact depth
  f(rho) t + t_a), and the illustrative cases of report X6 with the new rule (same line format as
  tools/review/x6/x6_oxide_numbers_output.txt, plus one case of three counts);
* A12 n1: the upper bound of each uncertainty (UNCERTAINTY_BOUND_STATEMENT) at the 2.0 nm values,
  and the refusal of A12's absurd a-Si uncertainties (1e9 A, 1e300 A);
* A12 m3: which parity variant of the 2.0 nm interval [6, 7] builds the nearest count, with the
  overlap or gap of each variant (thickness not altered).

Run:  PYTHONPATH=. venv/bin/python tools/review/x7/x7_oxide_numbers.py
      (saved: tools/review/x7/x7_oxide_numbers_output.txt)
The oxide values are the B41 demo values (ASSUMPTION B41: 2.20 g/cm^3; 20 A or 15 A); the
uncertainties are illustrative inputs of this script (TEST values, not item-12 values; none exists).
The Monte Carlo draws independent normal errors (an assumption of the check, stated per line) with
numpy.random.default_rng(SEED).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from reflection_holo.constants import (A_SI_A, AVOGADRO_PER_MOL, M_O_G_PER_MOL,  # noqa: E402
                                       M_SI_G_PER_MOL)
from reflection_holo.structure import oxide as ox                                   # noqa: E402

SEED = 20260924
N_MC = 2_000_000
a = A_SI_A
q = a / 4
rho0 = 2.20
f = ox.consumed_si_fraction(rho0, a)
rho_si = 8 * M_SI_G_PER_MOL / AVOGADRO_PER_MOL / (a * 1e-8) ** 3
f_fp = (rho0 / (M_SI_G_PER_MOL + 2 * M_O_G_PER_MOL)) / (rho_si / M_SI_G_PER_MOL)
print(f"a = {a} A (B2), a/4 = {q:.6f} A, a/8 = {q / 2:.6f} A, a/2 = {2 * q:.4f} A, "
      f"1.5 a/4 = {1.5 * q:.4f} A; f(2.20) = {f:.6f} (code), {f_fp:.6f} (first principles)")


def interval(t, ut, ur, ta, ua, kind, rho=rho0):
    return ox.item12_count_interval(thickness_A=t, thickness_uncertainty_A=ut, density_g_cm3=rho,
                                    density_uncertainty_g_cm3=ur, amorphous_si_thickness_A=ta,
                                    amorphous_si_thickness_uncertainty_A=ua,
                                    uncertainty_kind=kind, a_A=a)


def quadrature_fp(t, ut, ur, ta, ua, k=2.0, rho=rho0):
    """First principles (no package call except f): nominal +- k u_c, a-Si one-sided below."""
    ff = (rho / (M_SI_G_PER_MOL + 2 * M_O_G_PER_MOL)) / (rho_si / M_SI_G_PER_MOL)
    d0 = ff * t + ta
    ct, cr = ff * k * ut, ff * t * k * ur / rho
    lo = d0 - math.sqrt(ct ** 2 + cr ** 2 + min(k * ua, ta) ** 2)
    hi = d0 + math.sqrt(ct ** 2 + cr ** 2 + (k * ua) ** 2)
    return lo / q, hi / q


print("\n== A12 m2: depth sensitivities (layers of a/4 per unit), at 20 A, 2.20 g/cm^3")
print(f"  thickness: f / (a/4) = {f / q:.4f} layer per A; density: f t / rho / (a/4) = "
      f"{f * 20 / rho0 / q:.4f} layer per g/cm^3 ({f * 20 / rho0 / q * 0.05:.4f} per 0.05); a-Si: "
      f"1 / (a/4) = {1 / q:.4f} layer per A")

print("\n== A12 m2: the example of re-audit A12 (standard uncertainties t 20.0 +- 1.0 A, rho 2.20 "
      "+- 0.05 g/cm^3, a-Si 0.0 +- 0.1 A)")
before = interval(20.0, 2.0, 0.10, 0.0, 0.2, "half_width")   # X6's rule: the box of +- 2u
after = interval(20.0, 1.0, 0.05, 0.0, 0.1, "standard")
x6 = (REPO / "tools" / "review" / "x6" / "x6_oxide_numbers_output.txt").read_text()
m = re.search(r"t 20\.0 \+- 1\.0 A, rho 2\.20 \+- 0\.05 g/cm\^3, a-Si 0\.0 \+- 0\.1 A, standard: "
              r"(\d\.\d{3})-(\d\.\d{3}) layers .*-> counts (\[[\d, ]+\])", x6)
b_lo, b_hi = f"{before['continuum_layers_min']:.3f}", f"{before['continuum_layers_max']:.3f}"
same = bool(m) and m.groups() == (b_lo, b_hi, str(before["counts"]))
print(f"  before (report X6: each quantity at +- 2u, depth at the box corners, linear sum): "
      f"{b_lo}-{b_hi} layers -> counts {before['counts']} (refused: more than two counts); equals "
      f"X6's printed standard line {m.groups() if m else None}: {same}")
lo_fp, hi_fp = quadrature_fp(20.0, 1.0, 0.05, 0.0, 0.1)
cl = after["combined_half_width_layers"]
print(f"  after (report X7: nominal {after['continuum_layers_nominal']:.4f} +- 2 u_c in quadrature, "
      f"a-Si one-sided below): {after['continuum_layers_min']:.3f}-"
      f"{after['continuum_layers_max']:.3f} layers (half-widths -{cl['lower']:.4f} / "
      f"+{cl['upper']:.4f} layer) -> counts {after['counts']}; first principles "
      f"{lo_fp:.3f}-{hi_fp:.3f}")
sym = after["continuum_layers_nominal"] + np.array([-1, 1]) * 2 * math.sqrt(
    (f * 1.0 / q) ** 2 + (f * 20 * 0.05 / rho0 / q) ** 2 + (0.1 / q) ** 2)
print(f"  (symmetric quadrature, a-Si also below: {sym[0]:.3f}-{sym[1]:.3f}, A12's 5.774-7.233)")

print("\n== A12 m2: coverage check (k = 2)")
print(f"  analytic: P(|x - mu| <= 2 sigma) = erf(2/sqrt(2)) = {100 * math.erf(2 / math.sqrt(2)):.2f} "
      f"% for a normally distributed depth (the depth is linear in t, rho and t_a to first order)")
rng = np.random.default_rng(SEED)


def mc(t, ut, ur, ta, ua, asi, label):
    tt = rng.normal(t, ut, N_MC)
    rr = rng.normal(rho0, ur, N_MC)
    if asi == "normal":
        aa = rng.normal(ta, ua, N_MC)
    elif asi == "zero":
        aa = np.zeros(N_MC)
    else:                                              # half-normal: |N(0, u_a)|
        aa = np.abs(rng.normal(0.0, ua, N_MC))
    ff = rr / (M_SI_G_PER_MOL + 2 * M_O_G_PER_MOL) / (rho_si / M_SI_G_PER_MOL)
    d = (ff * tt + aa) / q
    n = np.floor(d + 0.5)
    new = interval(t, ut, ur, ta, ua, "standard")
    box = interval(t, 2 * ut, 2 * ur, ta, 2 * ua, "half_width")
    out = []
    for name, ci in (("quadrature", new), ("X6 box", box)):
        inside = np.mean((d >= ci["continuum_layers_min"]) & (d <= ci["continuum_layers_max"]))
        cnt = np.mean(np.isin(n, ci["counts"]))
        out.append(f"{name} {ci['continuum_layers_min']:.3f}-{ci['continuum_layers_max']:.3f}: "
                   f"depth inside {100 * inside:.2f} %, count in {ci['counts']} {100 * cnt:.2f} %")
    print(f"  Monte Carlo ({N_MC} draws, seed {SEED}; t, rho normal; a-Si {label}): "
          + "; ".join(out))


mc(20.0, 1.0, 0.05, 5.0, 0.5, "normal", "5.0 +- 0.5 A normal (no clipping)")
mc(20.0, 1.0, 0.05, 0.0, 0.1, "zero", "exactly 0 (true absence; u_a the detection limit)")
mc(20.0, 1.0, 0.05, 0.0, 0.1, "halfnormal", "|N(0, 0.1 A)| (half-normal below the detection limit)")
mc(20.0, 0.1, 0.01, 0.0, 0.1, "zero", "exactly 0")
se = math.sqrt(0.9545 * 0.0455 / N_MC)
print(f"  Monte Carlo standard error at 95.45 %: {100 * se:.3f} %")
print(f"  second-order (product) term of f(rho) t, omitted by the first-order propagation: "
      f"f u_t u_rho / rho = {f * 1.0 * 0.05 / rho0:.4f} A = {f * 0.05 / rho0 / q:.4f} layer for "
      f"u_t = 1 A, u_rho = 0.05 g/cm^3 (u_c = {math.sqrt((f / q) ** 2 + (f * 20 * 0.05 / rho0 / q) ** 2 + (0.1 / q) ** 2):.4f} layer)")

print("\n== A12 m2: item12_count_interval for illustrative uncertainties (TEST values; standard: "
      "quadrature, half_width: box corners)")
CASES = ((20.0, 1.0, 0.05, 0.0, 0.1), (20.0, 0.1, 0.01, 0.0, 0.1), (20.0, 1.0, 0.05, 0.0, 1.0),
         (20.0, 1.0, 0.05, 0.0, 0.5),
         (15.0, 0.5, 0.03, 0.0, 0.1), (15.0, 1.0, 0.05, 0.0, 0.1), (15.0, 0.5, 0.03, 0.0, 1.0),
         (15.0, 0.5, 0.03, 5.0, 0.5))
for t, ut, ur, ta, ua in CASES:
    for kind in ox.UNCERTAINTY_KINDS:
        ci = interval(t, ut, ur, ta, ua, kind)
        hw = ci["depth_half_width_layers"]
        extra = ""
        if kind == "standard":
            b = interval(t, 2 * ut, 2 * ur, ta, 2 * ua, "half_width")
            lo_fp, hi_fp = quadrature_fp(t, ut, ur, ta, ua)
            extra = (f"; first principles {lo_fp:.3f}-{hi_fp:.3f}; before (X6 box) "
                     f"{b['continuum_layers_min']:.3f}-{b['continuum_layers_max']:.3f} -> "
                     f"{b['counts']}")
        print(f"  t {t} +- {ut} A, rho 2.20 +- {ur} g/cm^3, a-Si {ta} +- {ua} A, {kind}: "
              f"{ci['continuum_layers_min']:.3f}-{ci['continuum_layers_max']:.3f} layers "
              f"(nominal {ci['continuum_layers_nominal']:.4f}, nearest {ci['nearest_count']}) -> "
              f"counts {ci['counts']}; depth half-ranges: thickness {hw['thickness']:.4f}, "
              f"density {hw['density']:.4f}, a-Si {hw['amorphous_si']:.4f} layer (clipped at 0); "
              f"parity variant "
              + ("not needed" if len(ci["counts"]) == 1 else
                 f"lower {ci['counts'][0]} / upper {ci['counts'][1]}" if len(ci["counts"]) == 2
                 else "REFUSED (more than one boundary)") + extra)

print("\n== A12 n1: upper bound of each uncertainty (UNCERTAINTY_BOUND_STATEMENT) at t = 20 A, "
      "2.20 g/cm^3")
bd = ox.UNCERTAINTY_DEPTH_BOUND_LAYERS * q
for kind in ox.UNCERTAINTY_KINDS:
    k = ox.STANDARD_COVERAGE_FACTOR if kind == "standard" else 1.0
    print(f"  {kind} (h = {k:g} u): u_t < min(t, a/2 / f) / {k:g} = "
          f"{min(20.0, bd / f) / k:.4f} A; u_rho < min(rho, a/2 rho / (f t)) / {k:g} = "
          f"{min(rho0, bd * rho0 / (f * 20.0)) / k:.4f} g/cm^3; u_a < (a/2) / {k:g} = "
          f"{bd / k:.4f} A")
# the widest interval the bounds admit (each depth contribution c_i < 2 layers): half-widths, box
# width 2 c_t + 2 c_rho + h_a + min(h_a, t_a) < 12 layers; standard, U- + U+ < 2 sqrt(3 x 2^2)
w_box = 2 * 2 + 2 * 2 + 2 + 2
w_std = 2 * math.sqrt(3 * 2.0 ** 2)
print(f"  widest interval the bounds admit: half_width below {w_box} layers -> at most "
      f"{math.ceil(w_box) + 1} counts; standard below {w_std:.2f} layers -> at most "
      f"{math.ceil(w_std) + 1} counts (a width below w holds at most ceil(w) + 1 counts); "
      f"_MAX_COUNTS_BUILT = {ox._MAX_COUNTS_BUILT} (refused above, before the list is built)")
for ua in (1.0e9, 1.0e300, 1.0e308):
    try:
        interval(20.0, 1.0, 0.05, 0.0, ua, "standard")
        print(f"  a-Si uncertainty {ua:g} A (standard): ACCEPTED")
    except ox.OxideSpecError as exc:
        print(f"  a-Si uncertainty {ua:g} A (standard): refused: {str(exc)[:150]}...")

print("\n== A12 m3: the parity variants of the 2.0 nm interval [6, 7] (half-widths 1 A, 0.05, 0.1 A)")
ci = interval(20.0, 1.0, 0.05, 0.0, 0.1, "half_width")
print(f"  counts {ci['counts']}, nearest count {ci['nearest_count']}: nearest_count_variant = "
      f"{ox.nearest_count_variant(ci)!r}")
depth = f * 20.0
for parity, n in zip(ox.PARITY_VARIANTS, ci["counts"]):
    ov = depth - n * q
    print(f"  {parity} variant, count {n} ({ox.count_parity(n)}): f t - N a/4 = {ov:+.4f} A "
          f"({'overlap' if ov > 0 else 'gap'}; |value| {'>' if abs(ov) > q / 2 else '<='} a/8 = "
          f"{q / 2:.4f} A; bound for a variant 1.5 a/4 = {1.5 * q:.4f} A)")
