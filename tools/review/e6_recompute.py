#!/usr/bin/env python3
"""E6: independent recomputation of the derived numbers in L6 and L7.

Written by review agent E6 (2026-09-23/24) WITHOUT reading L6's `l6/calc/si_tds_absorption.py` or any
L7 script. Formulas are derived from the physics (docs/physics_conventions.md) and from the equations as
printed in the sources (Thomas, Cleverley, Beanland 2024 Eqs. (1)-(2), read as images; Horio et al.
2022 Eq. (1); R1 Table III/IV coordinates as printed). Every printed line is quoted in
docs/agent_reports/E6_literature_review.md; the saved output is tools/review/e6_recompute_output.txt.

Run:  venv/bin/python tools/review/e6_recompute.py [path/to/main_scattering_function.py]

The optional argument is the published supplementary module of Thomas et al. (2024) (CC BY, not in the
repository); if given, it is imported unmodified and called as a black box (section D3). Without it
that section is skipped. Scattering factors for the independent Bird-King integral come from abTEM
1.0.10 (Lobato and Kirkland parameterisations; optional dependency of this repository).
"""
from __future__ import annotations

import importlib.util
import math
import sys

import numpy as np

# ----------------------------------------------------------------------------------------------
# A. constants (CODATA 2018 / SI 2019, as docs/physics_conventions.md) and the 200 keV beam
# ----------------------------------------------------------------------------------------------
H = 6.62607015e-34          # J s
C = 299792458.0             # m/s
E = 1.602176634e-19         # C
ME = 9.1093837015e-31       # kg
MEC2_EV = 510998.950        # eV
ALPHA = 7.2973525693e-3
HBAR = H / (2 * math.pi)
AMU_G = 1.66053906660e-24   # g
A_B2 = 5.4309               # A, ASSUMPTION B2 (repository)
A_R1 = 5.431                # A, value printed by R1 and used by L7


def beam(T_eV):
    gam = 1 + T_eV / MEC2_EV
    beta = math.sqrt(1 - 1 / gam**2)
    lam_A = H * C / math.sqrt(T_eV * (T_eV + 2 * MEC2_EV)) / E * 1e10
    k = 2 * math.pi / lam_A                                      # rad/A
    sigma = (2 * math.pi / (lam_A * T_eV)) * (MEC2_EV + T_eV) / (2 * MEC2_EV + T_eV)  # rad/(V A)
    return dict(gamma=gam, beta=beta, lam=lam_A, k=k, sigma=sigma)


def delta_rel(V0, T_eV):
    """(k_int^2 - k_ext^2)/k_ext^2, exact relativistic form of docs/physics_conventions.md."""
    return V0 * (2 * (T_eV + MEC2_EV) + V0) / (T_eV * (T_eV + 2 * MEC2_EV))


def ext_angle_from_internal_bragg(d_A, V0, T_eV):
    b = beam(T_eV)
    s2 = (b["lam"] / (2 * d_A)) ** 2 - delta_rel(V0, T_eV)
    return math.asin(math.sqrt(s2))


def pr(label, value, fmt="{:.6g}", note=""):
    v = fmt.format(value) if isinstance(value, (int, float, np.floating)) else str(value)
    print(f"{label:<74s} {v}" + (f"   [{note}]" if note else ""))


B200 = beam(200e3)
B100 = beam(100e3)
B10 = beam(10e3)
KCONST = H**2 / (2 * math.pi * ME * E) * 1e20                    # V A^2
TH008 = 16.1347e-3                                               # rad, repository (0,0,8) angle (B32)

print("=" * 110)
print("A. beam and constants")
pr("lambda(200 keV) (A)", B200["lam"], "{:.8f}")
pr("k(200 keV) (rad/A)", B200["k"], "{:.4f}")
pr("sigma(200 keV) (rad/(V A))  [L6: 7.288401e-4]", B200["sigma"], "{:.7e}")
pr("beta(200 keV), beta(100 keV), beta(10 keV)",
   f"{B200['beta']:.5f}, {B100['beta']:.5f}, {B10['beta']:.5f}")
pr("gamma(200 keV)", B200["gamma"], "{:.6f}")
pr("K = h^2/(2 pi m0 e) (V A^2)  [L6: 47.87765]", KCONST, "{:.5f}")
th_check = ext_angle_from_internal_bragg(A_B2 / 8, 13.903, 200e3)
pr("(0,0,8) external angle, V0 = 13.903 V (mrad)  [B32: 16.1347]", th_check * 1e3, "{:.4f}")
for V0 in (12.0, 12.48, 12.53):
    pr(f"(0,0,8) external angle, V0 = {V0} V (mrad)", ext_angle_from_internal_bragg(A_B2 / 8, V0, 200e3) * 1e3, "{:.4f}")

# ----------------------------------------------------------------------------------------------
# B. Debye-Waller factor, A7
# ----------------------------------------------------------------------------------------------
print("=" * 110)
print("B. Debye-Waller factor (B = 8 pi^2 <u_x^2>, per-axis rms u)")
EP = 8 * math.pi**2
B_heacock, dB_heacock = 0.4761, 0.0017
B_bvk295 = 0.4725
u2_fs293 = 0.005941
u_A7 = 0.076
u_h = math.sqrt(B_heacock / EP)
pr("u(Heacock 0.4761 A^2) (A)", u_h, "{:.5f}")
pr("  +- from +-0.0017 A^2 (A)", 0.5 * u_h * dB_heacock / B_heacock, "{:.5f}")
B_A7 = EP * u_A7**2
pr("B(A7 u = 0.076 A) (A^2)", B_A7, "{:.5f}")
pr("A7 B below Heacock B (%)", 100 * (1 - B_A7 / B_heacock), "{:.2f}")
pr("A7 u below Heacock u (%)", 100 * (1 - u_A7 / u_h), "{:.2f}")
B_fs293 = EP * u2_fs293
pr("B(Flensburg-Stewart <u^2> = 0.005941 A^2, 293 K) (A^2)", B_fs293, "{:.5f}")
pr("  + 2.5 K x 0.0014 A^2/K -> B(295.5 K) (A^2)  [Heacock quotes 0.4725(17)]", B_fs293 + 2.5 * 0.0014, "{:.5f}")
u_fs293 = math.sqrt(u2_fs293)
u_bvk295 = math.sqrt(B_bvk295 / EP)
pr("u(BvK, 293 K) (A)", u_fs293, "{:.5f}")
pr("u(BvK, 295.5 K, B = 0.4725) (A)", u_bvk295, "{:.5f}")
pr("A7 u below u(BvK 293 K) (%)   [L6 says 1.5 %]", 100 * (1 - u_A7 / u_fs293), "{:.2f}")
pr("A7 u below u(BvK 295.5 K) (%)", 100 * (1 - u_A7 / u_bvk295), "{:.2f}")
pr("BvK(295.5) vs Heacock B difference (%)", 100 * (B_heacock - B_bvk295) / B_heacock, "{:.2f}")
pr("dB for 10 K at 0.0014 A^2/K relative to 0.4761 (%)", 100 * 10 * 0.0014 / B_heacock, "{:.2f}")
s008 = 8 / (2 * A_B2)
for lab, B in (("A7", B_A7), ("BvK 295.5 K", B_bvk295), ("Heacock", B_heacock)):
    pr(f"(008) DW amplitude factor exp(-B s^2), {lab}", math.exp(-B * s008**2), "{:.4f}")
pr("(008) DW amplitude, A7 -> Heacock change (%)", 100 * (math.exp(-B_heacock * s008**2) / math.exp(-B_A7 * s008**2) - 1), "{:.2f}")
pr("Mendis convention 2 pi^2 u^2 for u = 0.078 A (A^2)", 2 * math.pi**2 * 0.078**2, "{:.4f}")
pr("crystallographic 8 pi^2 u^2 for u = 0.078 A (A^2)", EP * 0.078**2, "{:.4f}")
pr("Voss B = 0.4613 A^2 -> u (A)", math.sqrt(0.4613 / EP), "{:.5f}")

# ----------------------------------------------------------------------------------------------
# C. electronic absorption from mean free paths
# ----------------------------------------------------------------------------------------------
print("=" * 110)
print("C. uniform imaginary potential from an intensity mean free path: |T|^2 = exp(-2 sigma V' dz)")
sig = B200["sigma"]
for Lam in (1050.0, 830.0):
    pr(f"V' = 1/(2 sigma Lambda), Lambda = {Lam:.0f} A (V)", 1 / (2 * sig * Lam), "{:.4f}")
pr("proportional ratio with the same mean, 0.653 V / 13.903 V", (1 / (2 * sig * 1050)) / 13.903, "{:.4f}")
pr("mean of TEST_ONLY r = 0.05 on Kirkland 13.903 V (V)", 0.05 * 13.903, "{:.4f}")
pr("theta_E = dE/(2E) for 17 eV at 200 keV (mrad; non-relativistic form, as Mendis)", 17 / 400e3 * 1e3, "{:.4f}")
pr("theta_E = dE/(p v) for 17 eV at 200 keV (mrad; relativistic)",
   17 / (200e3 * (200e3 + 2 * MEC2_EV) / (200e3 + MEC2_EV)) * 1e3, "{:.4f}")
rho2 = 9.3749e-4        # H2 fp_100_r010: variance/coherent intensity in the 3 mrad aperture
for N in (8, 50):
    pr(f"finite-N frozen phonons: coherent-intensity bias rho^2/N, N = {N}", rho2 / N, "{:.2e}")
    pr(f"finite-N frozen phonons: phase noise sqrt(rho^2/(2N)) (rad), N = {N}", math.sqrt(rho2 / (2 * N)), "{:.4f}")

# ----------------------------------------------------------------------------------------------
# D. TDS absorptive factor: own Bird-King integral (Thomas et al. 2024 Eq. (2) as printed)
# ----------------------------------------------------------------------------------------------
print("=" * 110)
print("D. TDS absorptive factor f'(s,B) = (2h/(beta m0 c)) Int d^2s' f(|s/2+s'|) f(|s/2-s'|) {1-exp[-2B(s'^2-s^2/4)]}")
try:
    from abtem import parametrizations as ap
    have_abtem = True
except Exception as exc:                                         # pragma: no cover
    have_abtem = False
    print("abTEM not importable; section D skipped:", exc)

S_G = {"000": 0.0, "111": math.sqrt(3) / (2 * A_B2), "022": math.sqrt(8) / (2 * A_B2),
       "004": 4 / (2 * A_B2), "044": math.sqrt(32) / (2 * A_B2), "008": 8 / (2 * A_B2)}
B_LIST = [("A7", B_A7), ("F-S 293 K", B_fs293), ("BvK 295.5 K", 0.4725), ("Heacock", 0.4761),
          ("u = 0.078 A", EP * 0.078**2)]


def gl_nodes(n, a, b):
    x, w = np.polynomial.legendre.leggauss(n)
    return 0.5 * (b - a) * x + 0.5 * (b + a), 0.5 * (b - a) * w


if have_abtem:
    fam = {"Lobato": ap.LobatoParametrization().scattering_factor("Si"),
           "Kirkland": ap.KirklandParametrization().scattering_factor("Si")}

    def f_of_s(name, s):
        g = 2.0 * np.asarray(s)                                  # abTEM: argument is |g|^2, g = 2 s
        return np.asarray(fam[name](g**2), dtype=float)

    # radial grid in s' (1/A): piecewise Gauss-Legendre, tail to 60 1/A (f^2 ~ s^-4)
    edges = [0, 0.05, 0.1, 0.2, 0.4, 0.8, 1.5, 3, 6, 12, 25, 60]
    rr, wr = [], []
    for a0, a1 in zip(edges[:-1], edges[1:]):
        x, w = gl_nodes(48, a0, a1)
        rr.append(x); wr.append(w)
    rr = np.concatenate(rr); wr = np.concatenate(wr)
    ph, wph = gl_nodes(96, 0.0, 0.5 * math.pi)                  # symmetry: 4 x quadrant
    R, PH = np.meshgrid(rr, ph, indexing="ij")
    W = (wr[:, None] * wph[None, :]) * R * 4.0
    SX, SY = R * np.cos(PH), R * np.sin(PH)

    def fprime(name, s, B):
        pref = 2 * H / (B200["beta"] * ME * C) * 1e10              # A
        fa = f_of_s(name, np.hypot(0.5 * s + SX, SY))
        fb = f_of_s(name, np.hypot(0.5 * s - SX, SY))
        integ = fa * fb * (1.0 - np.exp(-2.0 * B * (R**2 - 0.25 * s**2)))
        return pref * float(np.sum(W * integ))

    omega = A_B2**3
    pr("Lobato f_Si(0) (A)", float(f_of_s("Lobato", 0.0)), "{:.5f}")
    pr("independent-atom MIP 8 K f(0)/a^3, Lobato (V)  [D3: 13.955]",
       KCONST * 8 * float(f_of_s("Lobato", 0.0)) / omega, "{:.4f}")
    pr("independent-atom MIP 8 K f(0)/a^3, Kirkland (V)  [D3: 13.903]",
       KCONST * 8 * float(f_of_s("Kirkland", 0.0)) / omega, "{:.4f}")
    results = {}
    for name in ("Lobato", "Kirkland"):
        print(f"-- {name} scattering factors (abTEM 1.0.10), 200 keV")
        for lab, B in B_LIST:
            rat = []
            for g, s in S_G.items():
                fp = fprime(name, s, B)
                rat.append(fp / float(f_of_s(name, s)))
            fp0 = fprime(name, 0.0, B)
            V0p = KCONST * 8 * fp0 / omega
            results[(name, lab)] = (rat, V0p)
            pr(f"   B = {B:.4f} ({lab}): f'/f at 000,111,022,004,044,008",
               ", ".join(f"{r:.5f}" for r in rat))
            pr(f"   B = {B:.4f} ({lab}): V0'(TDS) (V); 1/(2 sigma V0') (A)",
               f"{V0p:.4f}; {1 / (2 * sig * V0p):.0f}")
    # optical-theorem cross-check of the bookkeeping (Lobato, Heacock B)
    Bh = 0.4761
    ss, ws = [], []
    for a0, a1 in zip(edges[:-1], edges[1:]):
        x, w = gl_nodes(64, a0, a1)
        ss.append(x); ws.append(w)
    ss = np.concatenate(ss); ws = np.concatenate(ws)
    fs = f_of_s("Lobato", ss)
    # sigma_TDS = gamma^2 lambda^2 * 4 * 2 pi Int s ds f(s)^2 (1 - exp(-2 B s^2))  (small-angle d Omega)
    sig_tds = B200["gamma"]**2 * B200["lam"]**2 * 4 * 2 * math.pi * float(np.sum(ws * ss * fs**2 * (1 - np.exp(-2 * Bh * ss**2))))
    mu0 = 8 / omega * sig_tds
    pr("optical-theorem route: 1/mu0 = 1/(N sigma_TDS) (A), Lobato, B = 0.4761", 1 / mu0, "{:.0f}")
    pr("potential route:  1/(2 sigma V0') (A), same inputs", 1 / (2 * sig * results[("Lobato", "Heacock")][1]), "{:.0f}")

# D3. black-box run of the published module of Thomas et al. (2024), if its path is given
if len(sys.argv) > 1:
    path = sys.argv[1]
    spec = importlib.util.spec_from_file_location("thomas2024", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print(f"-- black box: {path} (module V = {getattr(mod, 'V', '?')} V)")
    for lab, B in B_LIST:
        vals = [complex(mod.main(s, B, 14)) for s in S_G.values()]
        rat = [v.imag / v.real for v in vals]
        V0p = KCONST * 8 * (vals[0].imag / B200["gamma"]) / A_B2**3
        pr(f"   B = {B:.4f} ({lab}): f'/f at 000,111,022,004,044,008",
           ", ".join(f"{r:.5f}" for r in rat))
        pr(f"   B = {B:.4f} ({lab}): V0'(TDS) (V) from Im(main)/gamma; 1/(2 sigma V0') (A)",
           f"{V0p:.4f}; {1 / (2 * sig * V0p):.0f}")
else:
    print("-- black-box run of Thomas et al. module: no path given, skipped")

# ----------------------------------------------------------------------------------------------
# E. energy scaling and measured anomalous-absorption ratios
# ----------------------------------------------------------------------------------------------
print("=" * 110)
print("E. energy scaling (TDS f' ~ 1/beta) and measured ratios")
r200_100 = B200["beta"] / B100["beta"]
pr("beta(200)/beta(100)  [L6: 1.268]", r200_100, "{:.4f}")
pr("V0'(TDS) 0.089 V at 200 keV scaled to 10 keV (V)  [L6: 0.32; Minami U_TDS 0.37]", 0.089 * B200["beta"] / B10["beta"], "{:.3f}")
pr("TDS ratio (111) 0.0110 scaled to 100 keV  [L6: 0.0139]", 0.0110 * r200_100, "{:.4f}")
pr("V0'(TDS) 0.089 V scaled to 100 keV (V)  [L6: 0.113]", 0.089 * r200_100, "{:.4f}")
pr("Voss V'000 0.61 V / scaled TDS 0.113 V  [L6: 5.4]", 0.61 / (0.089 * r200_100), "{:.2f}")
for g, Vp, Vr in (("111", 0.031, 5.12), ("220", 0.039, 4.40), ("311", 0.025, 2.50), ("004", 0.027, 2.60)):
    pr(f"Voss 1980 V'_{g}/|V_{g}| at 100 keV", Vp / Vr, "{:.4f}")
pr("Radi (via Voss Table 5) V'_111/|V_111|", 0.1 / 5.12, "{:.4f}")
pr("TDS(100 keV) / Voss at (111)  [L6: 2.3]", 0.0110 * r200_100 / (0.031 / 5.12), "{:.2f}")
for lab, up, u in (("PyExtal 200 kV", 0.00079, 0.04735), ("Extal 200 kV", 0.00086, 0.04731),
                   ("IAM 300 kV", 0.00047, 0.05749), ("CBED 300 kV", 0.00091, 0.05430),
                   ("LARBED 300 kV", 0.00067, 0.05449), ("Table 3 mean 300 kV", 0.00084, 0.05418)):
    pr(f"Ni et al. 2026 U'_111/U_111, {lab}", up / u, "{:.4f}")
pr("Ni (200 kV) / TDS ratio 0.0110", f"{0.00079 / 0.04735 / 0.0110:.2f} - {0.00086 / 0.04731 / 0.0110:.2f}")
pr("Ni (200 kV) / Voss (100 keV), unscaled", f"{(0.00079 / 0.04735) / (0.031 / 5.12):.2f} - {(0.00086 / 0.04731) / (0.031 / 5.12):.2f}")
pr("Ni scaled to 100 keV by beta ratio / Voss", f"{r200_100 * (0.00079 / 0.04735) / (0.031 / 5.12):.2f} - {r200_100 * (0.00086 / 0.04731) / (0.031 / 5.12):.2f}")

# ----------------------------------------------------------------------------------------------
# F. surface plasmons
# ----------------------------------------------------------------------------------------------
print("=" * 110)
print("F. surface-plasmon excitations per specular reflection, Lucas form n = beta_c e^2/(8 eps0 hbar v sin th)")
lucas_pref = 0.5 * math.pi * ALPHA / B200["beta"]
pr("e^2/(8 eps0 hbar v) at 200 keV = (pi/2) alpha/beta  [L6: 0.01649]", lucas_pref, "{:.5f}")
pr("same at 10 keV, relativistic v  [Horio 2022 Eq. (1): 5.79e-2]", 0.5 * math.pi * ALPHA / B10["beta"], "{:.4f}")
pr("same at 10 keV, non-relativistic v = c sqrt(2T/mc^2)", 0.5 * math.pi * ALPHA / math.sqrt(2 * 10e3 / MEC2_EV), "{:.4f}")
nL = lucas_pref / math.sin(TH008)
pr("Lucas n at 16.1347 mrad (beta_c = 1)", nL, "{:.4f}")
for bc in (0.66, 0.71):
    n = bc * nL
    pr(f"  beta_c = {bc}: n; zero-loss fraction exp(-n); elastic amplitude exp(-n/2)",
       f"{n:.3f}; {math.exp(-n):.3f}; {math.exp(-n / 2):.3f}")
th_tan = math.radians(0.8)
nL_tan = lucas_pref / math.sin(th_tan)
pr("Lucas n at 0.8 deg = 13.9626 mrad (Tanishiro 2003 conditions)", nL_tan, "{:.4f}")
pr("Tanishiro 2003 measured 1.44 / Lucas at 0.8 deg", 1.44 / nL_tan, "{:.3f}")
n_tan_scaled = 1.44 * math.sin(th_tan) / math.sin(TH008)
pr("Tanishiro 1.44 scaled by 1/sin(theta) to 16.1347 mrad", n_tan_scaled, "{:.3f}")
pr("  zero-loss fraction exp(-n); elastic amplitude exp(-n/2)", f"{math.exp(-n_tan_scaled):.3f}; {math.exp(-n_tan_scaled / 2):.3f}")
pr("  sideband factor for an R2 (both waves reflected) hologram exp(-n)", math.exp(-n_tan_scaled), "{:.3f}")
v200 = B200["beta"] * C
w_s = 11.3 * E / HBAR
pr("v/(2 omega_s), 200 keV, hbar omega_s = 11.3 eV (nm)  [Tanishiro p. 170: about 6 nm]", v200 / (2 * w_s) * 1e9, "{:.2f}")
pr("  path along the surface over that height at 14 mrad (um)  [Tanishiro: 0.4 um]", v200 / (2 * w_s) / 0.014 * 1e6, "{:.2f}")
pr("  same at the repository's 16.1347 mrad (um)", v200 / (2 * w_s) / math.sin(TH008) * 1e6, "{:.2f}")
pr("v/(2 omega_s) at 10 keV (nm)", B10["beta"] * C / (2 * w_s) * 1e9, "{:.2f}")
pr("theta_E = dE/(2E), 11.3 eV at 200 keV (rad)  [Tanishiro p. 171: 3e-5]", 11.3 / 400e3, "{:.2e}")

# ----------------------------------------------------------------------------------------------
# G. mean inner potential arithmetic
# ----------------------------------------------------------------------------------------------
print("=" * 110)
print("G. mean inner potential")
iam = {"pro-crystal 13.70": 13.70, "Doyle-Turner 13.9": 13.9, "Kirkland 13.903": 13.903,
       "HF 13.91": 13.91, "Lobato 13.955": 13.955}
bonded = {"B1/RHEED 12.0": 12.0, "Wu-Spiecker 12.48": 12.48, "DFT slab 12.53": 12.53,
          "holography low 11.5": 11.5, "holography high 12.5": 12.5}
diffs = [a - b for a in iam.values() for b in bonded.values()]
pr("IAM minus bonded/measured: min, max (V)  [L6: 1.2-1.9]", f"{min(diffs):.3f}, {max(diffs):.3f}")
diffs2 = [a - b for a in iam.values() for b in (12.0, 12.48, 12.53)]
pr("  same against 12.0-12.53 only: min, max (V)", f"{min(diffs2):.3f}, {max(diffs2):.3f}")
pr("Kirkland 13.903 minus 12.53 / 12.0 (V)  [L6 7.3: 1.4-1.9]", f"{13.903 - 12.53:.3f} / {13.903 - 12.0:.3f}")
pr("Wu-Spiecker minus B1; minus DFT (V)", f"{12.48 - 12.0:.2f}; {12.48 - 12.53:.2f}")
pr("0.5 V x (-0.34 rad/V) at (4,-4,4) (rad)", 0.5 * -0.34, "{:.3f}")
pr("0.48 V x 1.07 %/V at (0,0,8) (%)", 0.48 * 1.07, "{:.2f}")
pr("TDS V0' 0.0889 V as % of Lobato MIP 13.955 V", 100 * 0.0889 / 13.955, "{:.3f}")
pr("TEST_ONLY r = 0.05 mean / TDS mean 0.089", 0.05 * 13.903 / 0.089, "{:.2f}")

# ----------------------------------------------------------------------------------------------
# H. L7 geometry: overlayer phase, step phases, Tanishiro check, dimers, terraces, densities
# ----------------------------------------------------------------------------------------------
print("=" * 110)
print("H. L7 numbers")
k = B200["k"]
st = math.sin(TH008)
kp = k * st
pr("k_perp = k sin(theta) at 16.1347 mrad (1/A)", kp, "{:.5f}")
pr("path factor 2/sin(theta) (in + out)  [L7: 124]", 2 / st, "{:.2f}")
pr("projected overlayer phase 2 sigma/sin(theta) (rad/(A V))  [L7: 0.0903]", 2 * sig / st, "{:.5f}")
for Vov in (10.0, 12.0):
    kpo = math.sqrt(kp**2 + 2 * k * sig * Vov)
    pr(f"V_ov = {Vov:.0f} V: projected 2 sigma V/sin(th) (rad/A)", 2 * sig * Vov / st, "{:.4f}")
    pr(f"V_ov = {Vov:.0f} V: refraction 2 (k'_perp - k_perp) (rad/A)  [L7 (10 V): 0.86]", 2 * (kpo - kp), "{:.4f}")
    pr(f"V_ov = {Vov:.0f} V: k'_perp/k_perp", kpo / kp, "{:.4f}")
    pr(f"V_ov = {Vov:.0f} V: height error per A of top-surface variation (A/A)", (kpo - kp) / kp, "{:.4f}")
    for lab, h in (("a/4", A_B2 / 4), ("a/2", A_B2 / 2)):
        pr(f"V_ov = {Vov:.0f} V: buried {lab} step under a flat-topped overlayer 2 k'_perp h (rad)",
           2 * kpo * h, "{:.3f}")
for lab, h in (("a/4", A_B2 / 4), ("a/2", A_B2 / 2)):
    pr(f"geometric step phase 2 k sin(theta) h, {lab} (rad)  [L7: 10.98 / 21.95]", 2 * kp * h, "{:.3f}")
pr("wrap period lambda/(2 sin theta) (A)", B200["lam"] / (2 * st), "{:.4f}")
# Tanishiro 2003 consistency
h111 = A_R1 / math.sqrt(3)
pr("Si(111) bilayer step a/sqrt(3), a = 5.431 (A)", h111, "{:.4f}")
pr("2 k sin(0.8 deg) h / pi  [L7: 6.98]", 2 * k * math.sin(th_tan) * h111 / math.pi, "{:.3f}")
th444 = ext_angle_from_internal_bragg(A_R1 / (4 * math.sqrt(3)), 12.0, 200e3)
pr("(444) external angle at the internal Bragg condition, V0 = 12 V (mrad)  [L7: 13.64]", th444 * 1e3, "{:.3f}")
osak = math.sqrt((2 * math.pi * 4) ** 2 - (2 * k * h111) ** 2 * delta_rel(12.0, 200e3))
pr("Osakabe sqrt((2 pi n)^2 - (2 k d)^2 Delta)/pi, n = 4  [L7: 6.82]", osak / math.pi, "{:.3f}")
pr("0.8 deg +- 0.05 deg -> phase/pi range", f"{2 * k * math.sin(math.radians(0.75)) * h111 / math.pi:.2f} - {2 * k * math.sin(math.radians(0.85)) * h111 / math.pi:.2f}")
pr("GaAs d_880 = a/(8 sqrt 2), a = 5.653 (A)  [L7: 0.4997]", 5.653 / (8 * math.sqrt(2)), "{:.4f}")
# dimers from R1 tables (Delta x, Delta z of layer-1 atoms (0,l,0) and (2,l,0); ideal x = k sqrt2 a/4)
x2 = 2 * math.sqrt(2) * A_R1 / 4
for lab, (dx0, dz0, dx2, dz2) in {"p(2x1)s": (0.805, -0.524, -0.805, -0.524),
                                   "p(2x1)a": (1.162, -0.921, -0.534, -0.213),
                                   "p(2x2) row l=0": (0.992, -0.832, -0.688, -0.094),
                                   "p(2x2) row l=2": (0.675, -0.076, -1.010, -0.829),
                                   "c(4x2) row l=0": (0.989, -0.789, -0.685, -0.055),
                                   "c(4x2) row l=2": (0.675, -0.045, -1.001, -0.788)}.items():
    dxh = (x2 + dx2) - dx0
    dzh = dz0 - dz2
    pr(f"R1 {lab}: dimer bond (A); buckling (deg)",
       f"{math.hypot(dxh, dzh):.3f}; {math.degrees(math.atan2(abs(dzh), dxh)):.2f}")
pr("Horio 2014: asin((a_z - b_z)/r_AB) = asin(0.71/2.28) (deg)  [printed 18.1]", math.degrees(math.asin(0.71 / 2.28)), "{:.2f}")
pr("Horio 2014 Table I: a_z - b_z = 1.38 - 0.67 (A)", 1.38 - 0.67, "{:.2f}")
d4 = A_R1 / 4
for th_deg in (0.05, 0.1, 0.25, 0.5, 1.0):
    pr(f"terrace width L = d/tan(theta), d = a/4 (a = 5.431), theta = {th_deg} deg (A)", d4 / math.tan(math.radians(th_deg)), "{:.1f}")
pr("L for a/2 steps at 4 deg (A)  [L7: 38.8]", 2 * d4 / math.tan(math.radians(4.0)), "{:.2f}")
pr("a/4 with a = 5.431 (L7) and 5.4309 (B2) (A)  [L7 table prints 1.3575]", f"{A_R1 / 4:.5f}, {A_B2 / 4:.5f}")
rho_c = 8 * 28.0855 * AMU_G / (A_R1 * 1e-8) ** 3
pr("rho(c-Si), a = 5.431 A (g/cm^3)", rho_c, "{:.4f}")
pr("c-Si atom density (1/cm^3)", 8 / (A_R1 * 1e-8) ** 3, "{:.4e}")
pr("a-Si 4.90e22 /cm^3 -> g/cm^3; deficit vs c-Si (%)", f"{4.90e22 * 28.0855 * AMU_G:.4f}; {100 * (1 - 4.90e22 / (8 / (A_R1 * 1e-8) ** 3)):.2f}")
pr("a-Si at 1.7 / 1.8 / 1.9 % below c-Si (g/cm^3)", ", ".join(f"{rho_c * (1 - p):.4f}" for p in (0.017, 0.018, 0.019)))
pr("a-Si at 1 / 2 % below c-Si (g/cm^3)", ", ".join(f"{rho_c * (1 - p):.4f}" for p in (0.01, 0.02)))
print("=" * 110)
print("end")
