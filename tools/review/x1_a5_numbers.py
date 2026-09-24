#!/usr/bin/env python3
"""X1: numbers behind the A5 fixes (docs/agent_reports/X1_a5_fixes.md), printed from the code.

* A5 F9: the report numbers of E2 (sections 0 and 1.4: bonds across a riser "compressed by at most
  5.5 % of d_nn (2.176 A, p(2x2))") and E3 (section 2.4: "v = 0.3, tolerance 1e-2 needs 1 x 4")
  as the code gives them (the E2/E3 reports are not edited; X1 lists the corrected numbers);
* A5 F1: the measured incidence-plane relation of static buckled a/4 steps for every buckling
  registry at [100] and [010] (the B4 verdict swaps with the registry);
* A5 F3: the zero-loss factors at E6's n = 1.246 and at the rounded 1.25.

Run:  venv/bin/python tools/review/x1_a5_numbers.py      (saved: tools/review/x1_a5_numbers_output.txt)
Synthetic structures only (TEST_ONLY labels, the builder's own inputs); nothing is written.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from reflection_holo.constants import A_SI_A  # noqa: E402
from reflection_holo.optics import coherence as C  # noqa: E402
from reflection_holo.structure import Staircase, build_si001_terraces  # noqa: E402
from reflection_holo.structure import reconstruction as R  # noqa: E402

AZ_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 8 (beam azimuth)"


def build(st, az, term):
    return build_si001_terraces(azimuth_uvw=az, azimuth_label=AZ_LABEL, staircase=st,
                                edge_periods=4, substrate_layers=12,
                                first_terrace_backbond_uvw=(1, 1, 0), termination=term,
                                overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                                lattice_parameter_label="ASSUMPTION B2")


def staircase(edges):
    return Staircase(edges=edges, terrace_layers=(0, 2, 1), terrace_widths=(4, 4, 4),
                     boundary_step_layers=-1)


def main() -> None:
    print("== A5 F9, E3 section 2.4: optics.coherence.minimal_quadrature (curvature 0)")
    for v, tol in ((0.3, 1e-2), (3.0, 1e-6)):
        q = C.minimal_quadrature("uniform_disc", phase_extent_rad=v, curvature_rad=0.0,
                                 tolerance=tol)
        print(f"  v = {v}, tolerance {tol:g}: {q['n_radial']} x {q['n_azimuthal']} = "
              f"{q['members']} members, bound {q['bound']:.3e}")

    dnn = A_SI_A * math.sqrt(3.0) / 4.0
    print(f"\n== A5 F9, E2 sections 0 and 1.4: riser/edge minimum distance and the recorded "
          f"riser_edge_largest_compression_of_dnn (= 1 - min/d_nn, d_nn = {dnn:.4f} A); "
          f"staircase (0, 2, 1) x 4 periods, 4 edge periods, 12 layers")
    terms = [("p(2x1)s", None)] + [(t, r) for t in R.BUCKLED_STATIC
                                   for r in R.BUCKLING_REGISTRIES] + [(R.FLIPFLOP, None)]
    worst = {}
    for term, reg in terms:
        arg = term if reg is None else dict(name=term, buckling_registry=reg)
        for edges in ("transverse", "parallel"):
            for az in ((1, 1, 0), (1, 0, 0), (0, 1, 0)):
                try:
                    s = build(staircase(edges), az, arg)
                except R.ReconstructionError:
                    print(f"  {term:27s} {str(reg):7s} {edges:10s} {az}: refused (period)")
                    continue
                c = s.metadata["options"]["dimer_reconstruction"]["checks"]["collision"]
                comp = c["riser_edge_largest_compression_of_dnn"]
                print(f"  {term:27s} {str(reg):7s} {edges:10s} {az}: min {c['riser_edge_min_A']:.4f}"
                      f" A, recorded compression {comp:.4f}")
                if term not in worst or c["riser_edge_min_A"] < worst[term][0]:
                    worst[term] = (c["riser_edge_min_A"], comp, reg, edges, az)
    print("  smallest riser/edge distance per termination:")
    for k, (mn, comp, reg, edges, az) in worst.items():
        print(f"    {k:27s} {mn:.4f} A: 1 - min/d_nn = {100 * (1 - mn / dnn):.2f} % "
              f"(recorded {100 * comp:.2f} %; {reg}, {edges}, {az})")
    for mn in (2.1759, 2.2220):
        print(f"  E2's quoted minima: {mn} A -> 1 - min/d_nn = {100 * (1 - mn / dnn):.2f} %")

    print("\n== A5 F1: incidence-plane relation of static buckled a/4 steps per buckling registry")
    for term in R.BUCKLED_STATIC:
        for reg in R.BUCKLING_REGISTRIES:
            out = []
            for az in ((1, 0, 0), (0, 1, 0)):
                s = build(staircase("transverse"), az, dict(name=term, buckling_registry=reg))
                rel = [st["relation"]["buckling_registry_relation"] for st in s.metadata["steps"]
                       if st["type"] == "screw"]
                maps = {r["incidence_plane_glide_maps_reconstructed_layers"] for r in rel}
                dev = min(r["smallest_max_deviation_A"] for r in rel)
                out.append(f"{az}: {'maps' if maps == {True} else 'does not map'} ({dev:.3f} A)")
            print(f"  {term:7s} registry {reg}: " + "; ".join(out))

    print("\n== A5 F3: zero-loss amplitude exp(-n/2)")
    n = 1.44 * math.sin(math.radians(0.8)) / math.sin(16.1347e-3)
    for v in (n, 1.246, 1.25):
        print(f"  n = {v:.6f}: exp(-n/2) = {math.exp(-v / 2):.5f}, 1/exp(-n/2) = "
              f"{math.exp(v / 2):.4f}, R2 with V_loss = 0.1: {math.exp(-v) + 0.1 * -math.expm1(-v):.4f}")
    print(f"\nnumpy {np.__version__}")


if __name__ == "__main__":
    main()
