#!/usr/bin/env python3
"""A9b C3 (audit A9b of report X4, docs/agent_reports/A9b_X4_audit.md section 3, finding A9b-m4;
script by agent A9b, committed by agent X5 with repository-relative imports and the SUMMARY lines
added at the end of each case).

What the X4 placement puts between the kept crystal and the continuum oxide, on the engine's own
laterally averaged potential (X4's test helper _flat_terrace_profiles of
tests/forward/test_oxide_multislice_a8_fixes.py: AtomicPotential, Kirkland, static, [100],
dx 0.02 A; ContinuumOxidePotential.layer_arrays), and its effect on the 1-D specular reflection at
16.1347 mrad (transfer matrix of the laterally averaged profile; crystal absorption ratio 0.1 as in
E4's (c) runs, oxide V' = 0 so that only the placement differs).

1-D laterally averaged model: DERIVED_HERE, an estimate (lateral Fourier components of the crystal
potential are dropped; the multislice keeps them). Values standing in for PROJECT_INPUT item 12 are
the B41 demo values (TEST_ONLY labels of tests/forward/oxide_cases.oxide_spec).

Run:  OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python tools/review/x5/a9b_c3_gap.py
      (saved: tools/review/x5/a9b_c3_gap_output.txt)
"""
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tests" / "forward"))
sys.path.insert(0, str(REPO))
from oxide_cases import oxide_spec                                   # noqa: E402
from test_oxide_multislice_a8_fixes import _flat_terrace_profiles, _top_plane_peak  # noqa: E402
from reflection_holo.constants import A_SI_A                         # noqa: E402

Q = A_SI_A / 4
HC = 6.62607015e-34 * 299792458.0 / 1.602176634e-19 * 1e10
MC2, T = 510998.95, 200e3
k = 2 * math.pi * math.sqrt(T * (T + 2 * MC2)) / HC
C_U = (2 * math.pi / HC) ** 2          # dK2(V) ~ C_U * (2 V (T + mc2) + V^2)


def U_of(V):
    """k_int^2 - k^2 for a complex potential V (exact relativistic form, V complex)."""
    return C_U * (2 * V * (T + MC2) + V * V)


def layer_profile(x, x_i, x_t, V, w):
    E = lambda x0: 0.5 * np.array([math.erfc((xx - x0) / (math.sqrt(2) * w)) for xx in x])
    return V * (E(x_t) - E(x_i))


def reflect(x, Vc, theta):
    """r of the 1-D profile Vc(x) (complex V, x increasing upward, vacuum above x[-1], the
    profile continued as the bottom value below x[0]); reference plane x = 0."""
    k1 = k * math.sin(theta)
    h = x[1] - x[0]
    Kb = np.sqrt(k1 ** 2 + U_of(Vc[0]) + 0j)
    ps = np.exp(-1j * Kb * (x[0] - 0.5 * h))
    dps = -1j * Kb * ps
    K = np.sqrt(k1 ** 2 + U_of(Vc) + 0j)
    for KK in K:
        c, s = np.cos(KK * h), np.sin(KK * h)
        ps, dps = ps * c + dps * s / KK, -ps * KK * s + dps * c
    x1 = x[-1] + 0.5 * h
    A = 0.5 * (ps - dps / (1j * k1)) * np.exp(1j * k1 * x1)
    B = 0.5 * (ps + dps / (1j * k1)) * np.exp(-1j * k1 * x1)
    return B / A


def main():
    th = 16.1347e-3
    out = {}
    for t, N, rho in ((20.0, 7, 2.20), (15.0, 5, 2.20)):
        spec = oxide_spec(t_A=t, N=N, rho=rho, Vi=0.0,
                          labels=dict(V_imag="TEST_ONLY: no absorption (profile check)"))
        r = _flat_terrace_profiles(spec)
        x, dx, vc, vl, st = r["x"], r["dx"], r["v_crystal"], r["v_layer"], r["stack"]
        top = _top_plane_peak(x, vc, dx)
        x_eq = top + Q / 2
        x_c, x_t = st["crystal_boundary_x_A"], st["top_x_A"]
        print(f"=== t {t} A, N {N}: kept top plane {top:.4f}, equivalent boundary {x_eq:.4f}, "
              f"x_c {x_c:.4f} (recorded overlap {st['interface_overlap_A']:+.4f}), x_t {x_t:.4f}")
        # bulk statistics of the laterally averaged crystal potential (between planes)
        deep = (x > top - 8 * Q) & (x < top - 3 * Q)
        print(f"  crystal (deep, 5 layers): mean {vc[deep].mean():.3f} V, min between planes "
              f"{vc[deep].min():.3f} V, max {vc[deep].max():.2f} V")
        # profiles around the interface for three placements of the same layer
        cases = {"X4 (gap)": 0.0, "E4 (from top plane)": -Q / 2,
                 "joined (x_c = x_eq)": st["interface_overlap_A"]}
        # shift s moves the whole stack by s (x_i, x_t); 'joined' moves x_c onto x_eq
        xs = np.arange(top - Q, x_c + 2.0 + 1e-9, 0.1)
        print("  x - top plane (A): " + " ".join(f"{v - top:5.2f}" for v in xs))
        prof = {}
        for name, s in cases.items():
            s_ = s if name != "joined (x_c = x_eq)" else x_eq - x_c
            vl_s = layer_profile(x, st["interface_x_A"] + s_, x_t + s_, 10.34, 0.5)
            prof[name] = (s_, vl_s)
            vt = vc + vl_s
            print(f"  {name:22s} V: " + " ".join(f"{np.interp(v, x, vt):5.2f}" for v in xs))
        print("  crystal alone          V: " + " ".join(f"{np.interp(v, x, vc):5.2f}" for v in xs))
        # potential deficit of the gap relative to the joined stack, and its Born reflectivity
        s_j, vl_j = prof["joined (x_c = x_eq)"]
        d = (vc + prof["X4 (gap)"][1]) - (vc + vl_j)
        win = (x > top - Q) & (x < x_c + 3.0)
        dV = d[win]
        xw = x[win]
        print(f"  gap deficit X4 - joined: integral {dV.sum() * dx:+.4f} V A, min {dV.min():+.3f} V")
        born = {}
        for name, kk in (("2 k'_ox", 2 * math.sqrt((k * math.sin(th)) ** 2 + U_of(10.34))),
                         ("2 k'_Si(13.903 V)", 2 * math.sqrt((k * math.sin(th)) ** 2
                                                              + U_of(13.903))),
                         ("g_008 = 2 pi/(a/8)", 2 * math.pi / (Q / 2))):
            amp = abs(np.sum(U_of(dV) * np.exp(1j * kk * xw)) * dx) / kk
            born[name] = amp ** 2
            print(f"  Born |r| of the deficit at q = {name} ({kk:.4f} 1/A): {amp:.3e}, "
                  f"|r|^2 {amp ** 2:.3e}")
        # 1-D reflection of the full laterally averaged profile, crystal continued periodically
        # build a deep extension: repeat the laterally averaged crystal over one lattice period a
        # (4 layers), taken 6-10 layers below the top plane (resampled to dx exactly)
        xp = np.arange(0, 4 * Q, dx / 2)
        seg_x = top - 10 * Q + xp
        seg_v = np.interp(seg_x, x, vc)
        n_rep = int(np.ceil(250.0 / (4 * Q)))
        ext_x = np.concatenate([seg_x - (n_rep - m) * 4 * Q for m in range(n_rep)])
        ext_v = np.tile(seg_v, n_rep)
        xf = np.arange(top - 10 * Q, x_t + 6.0, dx / 2)
        vcf = np.interp(xf, x, vc)
        X = np.concatenate([ext_x, xf])
        Vc_cr = np.concatenate([ext_v, vcf])
        crystal_abs = 0.1                                                  # ratio, as E4 (c)
        results = {}
        for name, (s_, _) in list(prof.items()) + [("no layer", (None, None))]:
            if s_ is None:
                Vl = np.zeros_like(X)
            else:
                Vl = layer_profile(X, st["interface_x_A"] + s_, x_t + s_, 10.34, 0.5)
            Vt = Vc_cr * (1 + 1j * crystal_abs) + Vl
            rr = reflect(X - X[-1], Vt, th)                          # reference: box top
            results[name] = rr
            print(f"  1-D specular r ({name:22s}): |r| {abs(rr):.5f}, arg {np.angle(rr):+.4f} rad")
        a, b = results["X4 (gap)"], results["joined (x_c = x_eq)"]
        e = results["E4 (from top plane)"]
        print(f"  |r_X4/r_joined| {abs(a / b):.4f}, arg {np.angle(a / b):+.4f} rad; "
              f"|r_X4/r_E4| {abs(a / e):.4f}, arg {np.angle(a / e):+.4f} rad")
        # X5 (A9b-m4): the numbers of the sentence in structure.oxide.INTERFACE_OVERLAP_RULE and
        # the proposed row B41: the minimum of the laterally averaged potential (X4 placement)
        # between the kept top plane + a/8 and x_c + 1 A, the gap width, the Born reflectivity of
        # the deficit at q = 2 k'_ox and the 1-D changes of |r| and arg r against the joined stack
        sel = (x > x_eq) & (x < x_c + 1.0)
        vt = vc + prof["X4 (gap)"][1]
        j = int(np.argmin(vt[sel]))
        born_ox = born["2 k'_ox"]
        print(f"  SUMMARY t {t} A: laterally averaged potential minimum {vt[sel][j]:.2f} V at "
              f"{x[sel][j] - top:.2f} A above the kept top plane; gap {-st['interface_overlap_A']:.3f}"
              f" A; Born |r|^2 of the deficit at q = 2 k'_ox {born_ox:.1e}; "
              f"1-D against the joined stack: |r| {100 * (abs(a / b) - 1):+.2f} %, arg "
              f"{np.angle(a / b):+.3f} rad")
        out[t] = results
    return out


if __name__ == "__main__":
    main()
