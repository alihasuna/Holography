#!/usr/bin/env python3
"""A9b C4 (audit A9b of report X4, docs/agent_reports/A9b_X4_audit.md finding A9b-M1; script by agent
A9b, committed by agent X5 with repository-relative imports and the QUOTE lines added at the end).

A grown-oxide thickness difference between terraces (non-conformal, per-terrace overrides) in the
two engines' geometries. 1-D laterally averaged model (DERIVED_HERE, an estimate; it drops the
lateral Fourier components of the crystal potential): the engine's laterally averaged static
Kirkland crystal (X4's helper _flat_terrace_profiles, [100]) with its top N layers removed from a
FIXED pre-oxidation top plane H = 0, the continuum oxide placed as X4 places it
(x_i = H + a/8 - f t, x_t = H + a/8 + (1 - f) t, erf 0.5 A, V' = 0), N the nearest count; r of the
1-D profile referenced at a fixed plane (crystal absorption ratio 0.1). Compared with the geometric
engine's continuum rate [2 k'_ox - 2 k (1 - f)] per A (forward.geometric.model.oxide_phase_rates,
E9 4.4549 rad/A). Parameters: the B41 demo values (V_ox 10.34 V, 2.20 g/cm^3, TEST_ONLY labels of
tests/forward/oxide_cases.oxide_spec) at 16.1347 mrad (B32), 200 keV (PROJECT_INPUT item 1).

The whole-layer consumption of the atomistic crystal (the multislice) keeps the crystal fixed while
the thickness changes by less than one consumed layer; the geometric engine applies the continuum
grown-oxide rate to any thickness difference. The QUOTE lines print the numbers quoted by
structure.oxide.NOT_REPRESENTED, structure.si001.B4_OXIDE_GROWN, the refusal of forward.cell and the
proposed rows B12/B41 (report X5).

Run:  OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python tools/review/x5/a9b_c4_nonconformal.py
      (saved: tools/review/x5/a9b_c4_nonconformal_output.txt)
"""
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tests" / "forward"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))
from a9b_c3_gap import layer_profile, reflect                            # noqa: E402
from oxide_cases import oxide_spec                                       # noqa: E402
from test_oxide_multislice_a8_fixes import _flat_terrace_profiles, _top_plane_peak  # noqa: E402
from reflection_holo.constants import A_SI_A                             # noqa: E402
from reflection_holo.forward.geometric.model import oxide_phase_rates    # noqa: E402
from reflection_holo.structure import oxide as ox                        # noqa: E402

Q = A_SI_A / 4
th = 16.1347e-3
spec = oxide_spec(t_A=20.0, N=7, Vi=0.0, labels=dict(V_imag="TEST_ONLY: no absorption"))
r = _flat_terrace_profiles(spec)
x, dx, vc = r["x"], r["dx"], r["v_crystal"]
top = _top_plane_peak(x, vc, dx)
f = ox.consumed_si_fraction(2.20, A_SI_A)
rates = oxide_phase_rates(theta_ext_rad=th, energy_keV=200.0, V_real_V=10.34, V_imag_V=0.0, f=f,
                          layer_spacing_A=Q)
g = rates["grown_oxide_rad_per_A"]
print(f"geometric grown-oxide rate {g:.4f} rad/A; one consumed layer {rates['one_consumed_layer_rad']:.4f} rad "
      f"= {rates['one_consumed_layer_oxide_A']:.4f} A of oxide")
# crystal: laterally averaged profile relative to its top plane, continued periodically below
seg_x = np.arange(0, 4 * Q, dx / 2)
seg_v = np.interp(top - 10 * Q + seg_x, x, vc)
xf_rel = np.arange(-10 * Q, 6.0, dx / 2)                                   # relative to top plane
vf = np.interp(top + xf_rel, x, vc, right=0.0)
n_rep = int(np.ceil(250.0 / (4 * Q)))
ext_rel = np.concatenate([-10 * Q + seg_x - (n_rep - m) * 4 * Q for m in range(n_rep)])
ext_v = np.tile(seg_v, n_rep)
X_rel = np.concatenate([ext_rel, xf_rel])
V_rel = np.concatenate([ext_v, vf])


def run(t, N, joined=False):
    H = 0.0                                              # pre-oxidation top plane (fixed)
    kept_top = H - N * Q
    Hs = H + Q / 2
    x_i, x_t = Hs - f * t, Hs + (1 - f) * t
    if joined:                                           # x_c on the kept crystal's boundary
        s = (kept_top + Q / 2) - x_i
        x_i, x_t = x_i + s, x_t + s
    Xg = np.arange(kept_top - 250.0 - 10 * Q, 30.0, dx / 2)
    Vc = np.interp(Xg - kept_top, X_rel, V_rel, left=V_rel[0], right=0.0)
    Vl = layer_profile(Xg, x_i, x_t, 10.34, 0.5)
    Vt = Vc * (1 + 0.1j) + Vl
    rr = reflect(Xg - 30.0, Vt, th)                     # reference plane x = 30 A (fixed)
    return rr


ts = np.round(np.arange(17.0, 23.01, 0.5), 3)
rows = []
for t in ts:
    N = int(math.floor(f * t / Q + 0.5))
    rr = run(t, N)
    rows.append((t, N, rr))
ph = np.unwrap([np.angle(rr) for _, _, rr in rows])
print(" t(A)  N  overlap(A)   |r|     phase(rad)  phase - geometric(rad)")
for (t, N, rr), p in zip(rows, ph):
    geo = ph[0] + g * (t - ts[0])
    print(f"{t:5.2f} {N:2d}  {f * t - N * Q:+.4f}  {abs(rr):.4f}  {p:+9.4f}  {p - geo:+8.4f}")
# local slope at fixed N (sub-layer thickness difference, the E9 grown-oxide case)
slopes = []
for t0 in (19.0, 20.5, 21.5):
    N = int(math.floor(f * t0 / Q + 0.5))
    a, b = run(t0 - 0.1, N), run(t0 + 0.1, N)
    sl = np.angle(b / a) / 0.2
    slopes.append(sl)
    aj, bj = run(t0 - 0.1, N, joined=True), run(t0 + 0.1, N, joined=True)
    print(f"slope at t {t0} A (N {N} fixed): X4 placement {sl:.4f} rad/A; x_c pinned to the kept "
          f"crystal {np.angle(bj / aj) / 0.2:.4f} rad/A; geometric {g:.4f} rad/A")
# X5 (A9b-M1): the numbers quoted by the code strings and the proposed rows
top_rate = rates["top_surface_rad_per_A"]
diffs = [g - s for s in slopes]
print(f"QUOTE top-surface rate 2 (k'_ox - k) = {top_rate:.4f} rad/A (= {top_rate:.3f}); geometric "
      f"grown-oxide rate {g:.4f} rad/A; one consumed layer {rates['one_consumed_layer_rad']:.4f} "
      f"rad = {rates['one_consumed_layer_oxide_A']:.4f} A of oxide")
print(f"QUOTE multislice (1-D model) slopes at a fixed consumed-layer count: "
      f"{', '.join(f'{s:.4f}' for s in slopes)} rad/A (range {min(slopes):.2f}-{max(slopes):.2f}); "
      f"geometric minus 1-D model: {', '.join(f'{d:.4f}' for d in diffs)} rad/A (range "
      f"{min(diffs):.2f}-{max(diffs):.2f} rad per A of sub-layer thickness difference)")
print(f"QUOTE example Dt = 0.5 A at a fixed count: geometric {g * 0.5:.2f} rad, 1-D model "
      f"{min(slopes) * 0.5:.2f}-{max(slopes) * 0.5:.2f} rad")
