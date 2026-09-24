#!/usr/bin/env python3
"""A9b C2 (audit A9b of report X4, docs/agent_reports/A9b_X4_audit.md section 4; script by agent A9b,
committed by agent X5 for audit finding A9b-m3 with the QUOTE lines added at the end).

Exact 1-D reflectivity of the erf-graded vacuum edge of the continuum oxide, computed two
independent ways (no package import):
  (i)  ODE integration of psi'' + K(x)^2 psi = 0 with scipy's DOP853 (rtol 1e-12), and
  (ii) a piecewise-constant transfer matrix (A9b's own implementation, midpoint sampling),
plus the Born factor exp(-(q w)^2) with q = k1 + k2 (E9 out:241 convention) and the sharp Fresnel
value. Edge: V(x) = V_ox E(x), E = erfc(x/(sqrt2 w))/2, vacuum at x > 0 side, layer at x < 0.
V_ox = 10.34 V (B41; E9 out:166); 200 keV (PROJECT_INPUT item 1); 16.1347 mrad (B32) and the
multislice engine's central incident bin 16.1751 mrad (report E4 section 4(a)).

The QUOTE lines print, at the precision quoted by structure.oxide.EDGE_W05_REFLECTIVITY, the module
docstrings of structure.oxide and forward.geometric.model and the proposed row B41, the numbers of
A9b-m3: the exact |r|^2 at 16.1347 mrad, |r| relative to the sharp edge, the ratio exact/Born and
the central-bin value. (The engine's own value, 1.8350e-09, is printed by the committed test
tests/forward/test_oxide_multislice.py::test_graded_edge_of_0p5_A_suppresses_the_layer_reflection.)

Run:  venv/bin/python tools/review/x5/a9b_c2_edge.py
      (saved: tools/review/x5/a9b_c2_edge_output.txt)
"""
import math
import sys

import numpy as np
from scipy.integrate import solve_ivp

HC = 6.62607015e-34 * 299792458.0 / 1.602176634e-19 * 1e10      # eV A
MC2 = 510998.95
T = 200e3
pc = math.sqrt(T * (T + 2 * MC2))
k = 2 * math.pi * pc / HC


def dK2(V):
    """k_int^2 - k^2 (exact relativistic, (E+V)(E+V+2mc^2) - E(E+2mc^2) over (hbar c)^2)."""
    return ((T + V) * (T + V + 2 * MC2) - T * (T + 2 * MC2)) * (2 * math.pi / HC) ** 2


def E(x, w):
    return 0.5 * math.erfc(x / (math.sqrt(2) * w))


def r_ode(theta, V, w, span=10.0):
    k1 = k * math.sin(theta)
    d2 = dK2(V)
    k2 = math.sqrt(k1 ** 2 + d2)
    x0, x1 = -span * w, span * w

    def rhs(x, y):
        K2 = k1 ** 2 + d2 * E(x, w)
        return [y[1], -K2 * y[0]]
    # transmitted wave travelling to -x: psi = exp(-i k2 x) at x0 (complex split into re/im)
    p0 = np.exp(-1j * k2 * x0)
    dp0 = -1j * k2 * p0
    sol = solve_ivp(lambda x, y: np.concatenate([rhs(x, y[:2]), rhs(x, y[2:])]), (x0, x1),
                    [p0.real, dp0.real, p0.imag, dp0.imag], method="DOP853", rtol=1e-12,
                    atol=1e-14)
    ps = sol.y[0, -1] + 1j * sol.y[2, -1]
    dps = sol.y[1, -1] + 1j * sol.y[3, -1]
    # psi = A e^{-i k1 x} + B e^{+i k1 x}
    A = 0.5 * (ps - dps / (1j * k1)) * np.exp(1j * k1 * x1)
    B = 0.5 * (ps + dps / (1j * k1)) * np.exp(-1j * k1 * x1)
    return B / A


def r_tm(theta, V, w, step, span=10.0):
    k1 = k * math.sin(theta)
    d2 = dK2(V)
    k2 = math.sqrt(k1 ** 2 + d2)
    n = int(round(2 * span * w / step))
    xs = np.linspace(-span * w, span * w, n + 1)
    h = xs[1] - xs[0]
    ps = np.exp(-1j * k2 * xs[0])
    dps = -1j * k2 * ps
    for xm in 0.5 * (xs[1:] + xs[:-1]):
        K = math.sqrt(k1 ** 2 + d2 * E(xm, w))
        c, s = math.cos(K * h), math.sin(K * h)
        ps, dps = ps * c + dps * s / K, -ps * K * s + dps * c
    x1 = xs[-1]
    A = 0.5 * (ps - dps / (1j * k1)) * np.exp(1j * k1 * x1)
    B = 0.5 * (ps + dps / (1j * k1)) * np.exp(-1j * k1 * x1)
    return B / A


V = 10.34
print(f"k = {k:.4f} 1/A, lambda = {2 * math.pi / k:.8f} A")
quote = {}
for th_mrad in (16.1347, 16.1751):
    th = th_mrad * 1e-3
    k1 = k * math.sin(th)
    k2 = math.sqrt(k1 ** 2 + dK2(V))
    rF = (k1 - k2) / (k1 + k2)
    print(f"--- theta {th_mrad} mrad: k1 {k1:.6f}, k2 {k2:.6f}, sharp Fresnel |r|^2 {rF ** 2:.6e}")
    for w in (0.1, 0.5):
        born = rF ** 2 * math.exp(-((k1 + k2) * w) ** 2)
        ro = r_ode(th, V, w)
        ro12 = r_ode(th, V, w, span=12.0)
        out = [f"w {w}: ODE |r|^2 {abs(ro) ** 2:.5e} (span 12: {abs(ro12) ** 2:.5e})"]
        for step in (0.004, 0.002, 0.001):
            rt = r_tm(th, V, w, step)
            out.append(f"TM step {step}: {abs(rt) ** 2:.5e}")
        out.append(f"|r|/|r_sharp| {abs(ro) / abs(rF):.4e}; Born {born:.4e}; exact/Born "
                   f"{abs(ro) ** 2 / born:.2f}")
        print("  " + "; ".join(out))
        sys.stdout.flush()
        quote[(th_mrad, w)] = (abs(ro) ** 2, abs(ro) / abs(rF), born, abs(ro) ** 2 / born,
                               rF ** 2)

# X5 (A9b-m3): the digits quoted by the code strings and the proposed row B41
r2, rel, born, ratio, sharp = quote[(16.1347, 0.5)]
print(f"QUOTE w 0.5 A at 16.1347 mrad: exact |r|^2 = {r2:.4e}; |r|/|r_sharp| = {rel:.3e} (sharp "
      f"edge |r|^2 {sharp:.3e}); Born factor |r|^2 = {born:.2e}; exact/Born = {ratio:.1f}")
r2c, relc, bornc, ratioc, sharpc = quote[(16.1751, 0.5)]
print(f"QUOTE w 0.5 A at the central bin 16.1751 mrad: exact |r|^2 = {r2c:.4e}; exact/Born = "
      f"{ratioc:.1f}")
