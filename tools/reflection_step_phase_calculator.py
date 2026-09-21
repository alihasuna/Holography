#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
reflection_step_phase_calculator.py
===================================================================
Reference calculator for reflection-mode dark-field electron holography of
silicon surfaces.  Reproduces every number quoted in the companion report
    reports/C_physics_derivations.md

Dependencies: numpy only (tested with numpy 2.4.6, CPython 3.11).
Run:  python3 reflection_step_phase_calculator.py

-------------------------------------------------------------------
CONVENTIONS  (fixed once, used everywhere; see report section 0)
-------------------------------------------------------------------
* Lengths in angstrom (A); angles in radians internally, printed in mrad/deg;
  energies in keV (beam) or eV/V (potentials).
* Electron wave:      Psi(r,t) = exp(+i(k.r - omega t)).
  With the opposite convention exp(-i(k.r - omega t)) every phase below
  changes sign.  Amplitudes/|F| are unaffected.
* ANGULAR wavevector  k = (2*pi/lambda) * khat,   |k| in rad/A.
  Crystallographic reciprocal vector g (cycles/A): |g_hkl| = 1/d_hkl.
  G = 2*pi*g  (rad/A),  |G_hkl| = 2*pi/d_hkl.
* Glancing angle theta = angle between the beam and the SURFACE (not the
  normal).  n_hat = outward surface normal (into vacuum).
* Structure factor  F_hkl = sum_j f_j exp(+2*pi*i (h x_j + k y_j + l z_j)).
* Step phase:  Delta_phi == phi(upper terrace) - phi(lower terrace)
                          = -(k_out - k_in).R          [exp(+ik.r) convention]
  where R is the lattice translation (or screw translation part) that maps the
  lower-terrace truncated crystal onto the upper-terrace one, and R.n_hat = h.

-------------------------------------------------------------------
CONSTANTS AND THEIR PROVENANCE
-------------------------------------------------------------------
h, c, e are EXACT by the 2019 SI redefinition (they are definitions, not
measurements).  m_e c^2 is the CODATA 2018 recommended value.  Both sets are
reproduced here from the standard SI/CODATA definitions; label in the report:
  h, c, e                      : SI-2019 exact definitions
  m_e c^2 = 0.510 998 950 00 MeV : CODATA_2018 (value used; the CODATA web
                                   page itself was NOT reachable from this
                                   session -- see report section 1)
No other physical constant is used.  The Si mean inner potential is NOT a
constant of nature and is treated as an explicit, labelled ASSUMPTION.
"""

from __future__ import annotations

import numpy as np

# ===================================================================
# 0.  CONSTANTS
# ===================================================================

PLANCK_J_S = 6.626_070_15e-34          # J s        (SI-2019, exact)
C_M_S = 299_792_458.0                  # m/s        (SI-2019, exact)
ELEM_CHARGE_C = 1.602_176_634e-19      # C          (SI-2019, exact)
M_E_C2_EV = 510_998.950_00             # eV         (CODATA 2018)

# hc expressed in eV*m, from the three exact SI constants above:
HC_EV_M = PLANCK_J_S * C_M_S / ELEM_CHARGE_C     # = 1.239841984...e-6 eV m

TWO_PI = 2.0 * np.pi

# ---- Silicon ------------------------------------------------------
# a_Si: the repository generator default (`--a-A`, si110_cleave_slab_generator.py)
A_SI_A = 5.4309          # A   PROJECT_INPUT (repository default)
A_SI_META_A = 5.431      # A   value used in pipeline/meta_tilt_examples.json

# Mean inner potential of Si.  ASSUMPTION -- see report section 3.2.
V0_SI_V = 12.0           # V
V0_SI_SENS_V = 1.0       # V   +/- sensitivity requested


# ===================================================================
# 1.  RELATIVISTIC ELECTRON WAVELENGTH
# ===================================================================

def wavelength_A(E_keV: float | np.ndarray) -> float | np.ndarray:
    """Relativistic de Broglie wavelength in A for kinetic energy E_keV.

    lambda = h c / sqrt(T (T + 2 m_e c^2)),  T = e*U = kinetic energy.
    Exact (no expansion).  DERIVED_HERE from (pc)^2 = T(T + 2 m c^2).
    """
    T = np.asarray(E_keV, dtype=float) * 1.0e3          # eV
    pc = np.sqrt(T * (T + 2.0 * M_E_C2_EV))             # eV
    return HC_EV_M / pc * 1.0e10                        # A


def k_ang_per_A(E_keV):
    """Angular wavevector magnitude |k| = 2 pi / lambda, in rad/A."""
    return TWO_PI / wavelength_A(E_keV)


def gamma_lorentz(E_keV):
    return 1.0 + (np.asarray(E_keV, float) * 1.0e3) / M_E_C2_EV


def beta_v_over_c(E_keV):
    g = gamma_lorentz(E_keV)
    return np.sqrt(1.0 - 1.0 / g**2)


# ===================================================================
# 2.  DIAMOND-CUBIC STRUCTURE FACTOR (8-atom conventional cell)
# ===================================================================

DIAMOND_BASIS = np.array([
    [0.00, 0.00, 0.00], [0.50, 0.50, 0.00],
    [0.50, 0.00, 0.50], [0.00, 0.50, 0.50],
    [0.25, 0.25, 0.25], [0.75, 0.75, 0.25],
    [0.75, 0.25, 0.75], [0.25, 0.75, 0.75],
])


def structure_factor_over_f(hkl) -> complex:
    """F_hkl / f for the 8-atom diamond conventional cell (equal f, no DWF).

    F = f * sum_j exp(2 pi i g.r_j).  DERIVED_HERE (direct sum; the closed
    form F = f * F_fcc * (1 + i^(h+k+l)) is verified against it in main()).
    """
    g = np.asarray(hkl, dtype=float)
    return complex(np.sum(np.exp(2j * np.pi * (DIAMOND_BASIS @ g))))


def diamond_allowed(hkl) -> bool:
    """Kinematic selection rule for diamond cubic.

    Allowed iff (h,k,l all odd) or (all even AND h+k+l == 4n).
    DERIVED_HERE from the closed form |F| = 4 f |1 + i^(h+k+l)| * [all same
    parity]; cross-checked numerically against structure_factor_over_f().
    """
    h, k, l = (int(v) for v in hkl)
    par = (h % 2, k % 2, l % 2)
    if par == (1, 1, 1):
        return True
    if par == (0, 0, 0):
        return (h + k + l) % 4 == 0
    return False


def d_spacing_A(hkl, a_A: float = A_SI_A) -> float:
    h, k, l = (int(v) for v in hkl)
    return a_A / np.sqrt(h * h + k * k + l * l)


def screw_search(grid: int = 8):
    """Brute force: which (90 deg rotation about [001]) + (translation with
    t_z = a/4) map the 8-atom diamond basis onto itself, modulo 1?

    Used to show that the Si(001) a/4 step is a SCREW relation, not a pure
    translation.  DERIVED_HERE (numerical enumeration).
    """
    Rp = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    Rm = np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    base = np.round(DIAMOND_BASIS % 1.0, 9)
    out = []
    for nm, Rmat in (("Rz(+90)", Rp), ("Rz(-90)", Rm)):
        for i in range(grid):
            for j in range(grid):
                t = np.array([i / grid, j / grid, 0.25])
                img = np.round((DIAMOND_BASIS @ Rmat.T + t) % 1.0, 9)
                if all(any(np.allclose(p, q, atol=1e-9) for q in base) for p in img):
                    out.append((nm, t))
    return out


# ===================================================================
# 3.  REFRACTION BY THE MEAN INNER POTENTIAL
# ===================================================================

def E_eff_V(E_keV: float, V0_V: float) -> float:
    """'Effective energy' E_eff [volts] defined by  (k_int^2 - k^2)/k^2 = V0/E_eff.

    DERIVED_HERE.  With T = kinetic energy [eV], U = e*V0 [eV], E0 = m c^2:
        k_int^2/k^2 = (T+U)(T+U+2E0) / (T(T+2E0))
        =>  k_int^2 - k^2 = k^2 * U(2T + U + 2E0) / (T(T+2E0))
        =>  E_eff = T(T+2E0) / (2T + U + 2E0).
    Non-relativistic limit E_eff -> T.  Setting U -> 0 gives the familiar
    E_eff = T(1 + T/2E0)/(1 + T/E0).
    """
    T = E_keV * 1.0e3
    U = V0_V
    return T * (T + 2.0 * M_E_C2_EV) / (2.0 * T + U + 2.0 * M_E_C2_EV)


def delta_K_per_A(E_keV: float, V0_V: float) -> float:
    """dK = sqrt(k_int^2 - k^2)  [rad/A].  The surface-normal wavevector
    'boost' on entering the crystal.  Exactly: K_int^2 = K_ext^2 + dK^2."""
    k = k_ang_per_A(E_keV)
    return float(k * np.sqrt(V0_V / E_eff_V(E_keV, V0_V)))


def theta_critical_rad(E_keV: float, V0_V: float) -> float:
    """External critical glancing angle for total external reflection:
    sin(theta_c) = dK/k = sqrt(V0/E_eff).  DERIVED_HERE."""
    return float(np.arcsin(delta_K_per_A(E_keV, V0_V) / k_ang_per_A(E_keV)))


def theta_int_from_ext_rad(theta_ext, E_keV, V0_V):
    """Internal glancing angle from the external one (k_parallel conserved).

    K_int = sqrt((k sin th_ext)^2 + dK^2);  sin th_int = K_int / k_int.
    """
    k = k_ang_per_A(E_keV)
    dK = delta_K_per_A(E_keV, V0_V)
    k_int = np.sqrt(k**2 + dK**2)
    K_int = np.sqrt((k * np.sin(theta_ext))**2 + dK**2)
    return np.arcsin(np.clip(K_int / k_int, -1.0, 1.0))


# ===================================================================
# 4.  SPECULAR BRAGG CONDITION SATISFIED *INSIDE* THE CRYSTAL
# ===================================================================

class SpecularCondition:
    """Order-n specular Bragg condition on a rod of spacing d, with refraction.

    Premises (all DERIVED_HERE from them):
      P1  The surface-averaged potential is a step of depth V0 (volts), so the
          surface-parallel wavevector is conserved and only the normal
          component changes:  K_int^2 = K_ext^2 + dK^2.
      P2  The Bragg condition is satisfied by the INTERNAL wavevectors:
          2 K_int = |G| = 2 pi n / d   =>  K_int = pi n / d.
      P3  The two terraces are rigid copies of one another, related by a
          lattice translation R with R.n_hat = h  (exact for the specular beam
          even when R is the translation part of a screw operation -- see
          report 2.3).
      P4  Vacuum step phase:  Delta_phi = -(k_out - k_in).R = -2 h K_ext.

    Nothing here is kinematic: P3/P4 follow from the translation covariance of
    the scattering problem and hold in full dynamical theory.  Only the
    *amplitude* is dynamical.
    """

    def __init__(self, d_A: float, order_n: int, E_keV: float, V0_V: float):
        self.d_A = float(d_A)
        self.n = int(order_n)
        self.E_keV = float(E_keV)
        self.V0_V = float(V0_V)

        self.lam_A = float(wavelength_A(E_keV))
        self.k = float(k_ang_per_A(E_keV))
        self.dK = delta_K_per_A(E_keV, V0_V)
        self.k_int = float(np.sqrt(self.k**2 + self.dK**2))

        # Vacuum ("nominal") Bragg angle -- what the repository currently uses
        s = self.n * self.lam_A / (2.0 * self.d_A)
        self.theta_B_vac = float(np.arcsin(s)) if s <= 1.0 else np.nan

        # Internal normal wavevector demanded by the Bragg condition
        self.K_int = np.pi * self.n / self.d_A                 # rad/A
        self.theta_int = float(np.arcsin(np.clip(self.K_int / self.k_int, -1, 1)))

        # External normal wavevector (real only above the critical angle)
        arg = self.K_int**2 - self.dK**2
        self.accessible = arg > 0.0
        self.K_ext = float(np.sqrt(arg)) if self.accessible else np.nan
        self.theta_ext = (float(np.arcsin(np.clip(self.K_ext / self.k, -1, 1)))
                          if self.accessible else np.nan)

        # rho = K_ext/K_int -- the factor by which refraction detunes the
        # vacuum momentum transfer away from the reciprocal lattice vector.
        self.rho = self.K_ext / self.K_int if self.accessible else np.nan

        # Height that costs exactly one 2*pi of step phase
        self.h_2pi_A = (self.lam_A / (2.0 * np.sin(self.theta_ext))
                        if self.accessible else np.nan)

    # -- step phase -------------------------------------------------
    def step_phase(self, h_A: float) -> dict:
        """Signed and wrapped step phase for an up-step of height h_A."""
        if not self.accessible:
            return dict(total=np.nan, abstotal=np.nan, over2pi=np.nan,
                        frac2pi=np.nan, mod2pi=np.nan, wrapped=np.nan)
        signed = -2.0 * h_A * self.K_ext            # rad, phi_up - phi_low
        absval = abs(signed)
        over = absval / TWO_PI
        frac = over - np.floor(over)
        return dict(total=signed, abstotal=absval, over2pi=over,
                    frac2pi=frac, mod2pi=frac * TWO_PI,
                    wrapped=wrap_to_pi(signed))

    def dphi_dtheta(self, h_A: float) -> float:
        """d(|Delta_phi|)/d(theta_ext) = (4 pi h/lambda) cos(theta_ext) [rad/rad]."""
        return 4.0 * np.pi * h_A / self.lam_A * np.cos(self.theta_ext)


def wrap_to_pi(x):
    """Wrap to (-pi, +pi]."""
    return -((-np.asarray(x, float) + np.pi) % TWO_PI - np.pi)


# ===================================================================
# 5.  SMALL PRINTING HELPERS
# ===================================================================

def rule(title: str = "", ch: str = "=", width: int = 100):
    if title:
        print("\n" + ch * width)
        print(title)
        print(ch * width)
    else:
        print(ch * width)


def fnum(x, fmt="{:.4f}"):
    return "   --   " if (x is None or (isinstance(x, float) and np.isnan(x))) else fmt.format(x)


# ===================================================================
# MAIN
# ===================================================================

def main() -> None:
    np.set_printoptions(precision=6, suppress=True)

    rule("reflection_step_phase_calculator.py  --  all numbers used in "
         "C_physics_derivations.md")
    print(f"numpy {np.__version__}")
    print("Conventions: exp(+i(k.r - wt)); |k| = 2pi/lambda [rad/A]; "
          "theta = GLANCING angle to the surface.")
    print("Delta_phi = phi(upper terrace) - phi(lower terrace) = -(k_out-k_in).R .")

    # ---------------------------------------------------------------
    rule("1.  RELATIVISTIC ELECTRON WAVELENGTH  (DERIVED_HERE from "
         "lambda = hc/sqrt(T(T+2mc^2)))")
    print("Constants: h = 6.62607015e-34 J s (SI-2019 exact), "
          "c = 299792458 m/s (exact),")
    print("           e = 1.602176634e-19 C (exact), "
          "m_e c^2 = 510998.95000 eV (CODATA 2018).")
    print(f"           hc = {HC_EV_M:.12e} eV m  (derived from the three exact values)")
    print()
    print(f"{'E (keV)':>9} {'lambda (A)':>14} {'lambda (pm)':>13} "
          f"{'k=2pi/lam (rad/A)':>19} {'gamma':>9} {'beta':>9}")
    for E in (100.0, 200.0, 300.0):
        lam = wavelength_A(E)
        print(f"{E:9.1f} {lam:14.8f} {lam*100:13.6f} {k_ang_per_A(E):19.4f} "
              f"{gamma_lorentz(E):9.6f} {beta_v_over_c(E):9.6f}")
    print()
    print("Cross-check of the repository's own wavelength helpers at 200 keV:")
    T = 200e3
    lam_gen = (4.135667696e-15 * 2.99792458e8 /
               np.sqrt(T * (T + 2 * 510.99895e3))) * 1e10     # generator form
    m0 = 9.10938356e-31
    V = 200e3 * 1.602176634e-19
    p = np.sqrt(2 * m0 * V * (1 + V / (2 * m0 * 299792458.0**2)))
    lam_pipe = (6.62607015e-34 / p) * 1e10                    # pipeline form
    lam_ref = float(wavelength_A(200.0))
    print(f"   this script                      : {lam_ref:.8f} A")
    print(f"   si110_cleave_slab_generator.py   : {lam_gen:.8f} A  "
          f"(rel. diff {abs(lam_gen/lam_ref-1):.2e})")
    print(f"   step_height_reflection_formula.py: {lam_pipe:.8f} A  "
          f"(rel. diff {abs(lam_pipe/lam_ref-1):.2e})")
    print("   -> both repository helpers agree with the exact relativistic "
          "formula to <3e-7 relative;")
    print("      the m0 = 9.10938356e-31 kg used in the pipeline is the "
          "pre-2019 CODATA value (harmless here).")

    # ---------------------------------------------------------------
    rule("2.  DIAMOND-CUBIC STRUCTURE FACTOR AND THE (nnn) / (n,-n,n) RODS")
    print("F_hkl/f from the explicit 8-atom basis vs the closed form "
          "4*[same parity]*|1+i^(h+k+l)| :")
    print(f"{'hkl':>12} {'|F|/f (8-atom sum)':>20} {'|F|/f (closed form)':>21} "
          f"{'h+k+l':>7} {'allowed?':>10}")
    test_set = [(n, n, n) for n in range(1, 13)] + \
               [(n, -n, n) for n in (1, 2, 4, 6, 8)] + \
               [(0, 0, l) for l in (2, 4, 8, 12, 16)] + [(2, -2, 0), (2, 2, 0)]
    for hkl in test_set:
        Fsum = abs(structure_factor_over_f(hkl))
        h, k, l = hkl
        same_par = (h % 2 == k % 2 == l % 2)
        Fclosed = 4.0 * abs(1 + 1j**((h + k + l) % 4)) if same_par else 0.0
        ok = "ALLOWED" if diamond_allowed(hkl) else "forbidden"
        print(f"{str(hkl):>12} {Fsum:20.6f} {Fclosed:21.6f} {h+k+l:7d} {ok:>10}")
    maxerr = max(abs(abs(structure_factor_over_f(hkl)) -
                     (4.0 * abs(1 + 1j**((sum(hkl)) % 4))
                      if (hkl[0] % 2 == hkl[1] % 2 == hkl[2] % 2) else 0.0))
                 for hkl in test_set)
    print(f"\n   max |explicit sum - closed form| over the test set = {maxerr:.2e}  -> "
          f"selection rule confirmed numerically.")
    print("   Rule: all-odd ALLOWED (|F|=4*sqrt(2)*f); all-even ALLOWED only if "
          "h+k+l = 4n (|F|=8f); otherwise F = 0.")
    print("   => 222, 666, (10,10,10) and their (n,-n,n) partners are FORBIDDEN.")

    # ---------------------------------------------------------------
    rule("2b.  STEP VECTORS: IS THE UPPER TERRACE A RIGID TRANSLATE OF THE LOWER?")
    a = A_SI_A
    n111 = np.array([1.0, -1.0, 1.0]) / np.sqrt(3.0)   # repo surface normal
    n111_std = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
    R_bilayer = 0.5 * a * np.array([1.0, 0.0, 1.0])    # (a/2)[1,0,1]

    def is_fcc_lattice_vector(R, a_A=a, tol=1e-9):
        n = 2.0 * np.asarray(R) / a_A
        return (np.allclose(n, np.round(n), atol=tol)
                and int(round(n.sum())) % 2 == 0)

    d111 = a / np.sqrt(3.0)
    print(f"a(Si) = {a} A   d_111 = a/sqrt(3) = {d111:.6f} A "
          f"(bilayer repeat along <111>)")
    print(f"   intra-bilayer gap  = d_111/4  = {d111/4:.4f} A;  "
          f"inter-bilayer gap = 3 d_111/4 = {3*d111/4:.4f} A")
    print(f"   (matches the 0.78 / 2.35 A gaps quoted in "
          f"si110_cleave_slab_generator.py)")
    print()
    print("Si(111)/(1,-1,1) single-BILAYER step, h = d_111:")
    for nm, nvec in (("n = [1,1,1]/sqrt3", n111_std), ("n = [1,-1,1]/sqrt3 (repo)", n111)):
        h_proj = float(R_bilayer @ nvec)
        Rpar = R_bilayer - h_proj * nvec
        print(f"   R = (a/2)[1,0,1] = {R_bilayer}  with {nm}")
        print(f"      is an fcc lattice vector : {is_fcc_lattice_vector(R_bilayer)}")
        print(f"      R.n_hat = {h_proj:.6f} A   (= d_111? "
              f"{abs(h_proj-d111) < 1e-12})")
        print(f"      in-plane part |R_par|   = {np.linalg.norm(Rpar):.6f} A "
              f"= a/sqrt(6) = {a/np.sqrt(6):.6f} A")
    print("   -> the two terraces of a d_111 step ARE exact rigid translates; "
          "the phase factor is the ONLY difference (far from the step edge).")
    print()
    print("Si(001) steps (n_hat = [0,0,1]):")
    for lbl, Rtry in (("(a/4)[0,0,1] single layer", 0.25 * a * np.array([0, 0, 1.0])),
                      ("(a/2)[0,0,1]", 0.5 * a * np.array([0, 0, 1.0])),
                      ("(a/2)[1,0,1] double layer", 0.5 * a * np.array([1.0, 0, 1.0]))):
        print(f"   R = {lbl:26s} -> fcc lattice vector? "
              f"{is_fcc_lattice_vector(Rtry)}   R.n = {Rtry[2]:.6f} A")
    print("   Any fcc lattice vector has R.z_hat = (a/2)*integer, so h = a/4 is")
    print("   UNREACHABLE by a pure translation.  Brute-force search over the 90 deg")
    print("   rotations about [001] and translations on an a/8 grid, for operations")
    print("   S(r) = R r + t with t.z_hat = a/4 that map the 8-atom basis onto itself:")
    found = screw_search()
    for nm, t in found:
        print(f"      S = {nm} + t = a*{np.round(t,4)}   -> maps diamond onto itself")
    print(f"      ({len(found)} such operations found; these are the diamond 4_1 screws.)")
    print("   Consequence (report 2.3):")
    print("    * KINEMATICALLY the specular amplitude obeys Vt'(q) = exp(-i q.t) Vt(R^T q),")
    print("      and R^T q = q for q || n_hat, so the a/4 step gives EXACTLY exp(-i q h).")
    print("    * DYNAMICALLY the two terraces are 90 deg-rotated crystals, so terrace B at")
    print("      azimuth phi behaves like terrace A at azimuth phi-90 deg: the reflection")
    print("      coefficients (moduli AND dynamical phases) differ.  Only the a/2 double")
    print("      step, a PURE translation, is exact to all orders.")

    # ---------------------------------------------------------------
    rule("3.  REFRACTION BY THE MEAN INNER POTENTIAL  (V0 = "
         f"{V0_SI_V:.1f} V, ASSUMPTION)")
    print(f"{'E (keV)':>9} {'E_eff (V)':>13} {'V0/E_eff':>12} {'dK (rad/A)':>13} "
          f"{'theta_c (mrad)':>15} {'k_int/k - 1':>13} {'V0/T (nonrel)':>14}")
    kint_over_k_200 = np.sqrt(1.0 + V0_SI_V / E_eff_V(200.0, V0_SI_V))
    for E in (100.0, 200.0, 300.0):
        Ee = E_eff_V(E, V0_SI_V)
        dK = delta_K_per_A(E, V0_SI_V)
        tc = theta_critical_rad(E, V0_SI_V)
        kint_over_k = np.sqrt(1.0 + V0_SI_V / Ee)
        print(f"{E:9.1f} {Ee:13.1f} {V0_SI_V/Ee:12.6e} {dK:13.6f} {tc*1e3:15.4f} "
              f"{kint_over_k-1:13.3e} {V0_SI_V/(E*1e3):14.6e}")
    kint_over_k = kint_over_k_200
    print("\n   E_eff = T(T+2mc^2)/(2T + eV0 + 2mc^2)  (DERIVED_HERE, exact).")
    print("   The relativistic E_eff is ~14% BELOW T at 200 keV, so the "
          "non-relativistic V0/T")
    print("   underestimates the refraction by ~16% in sin^2(theta).")
    print("   sin^2(theta_int) = sin^2(theta_ext) + V0/E_eff holds exactly for "
          "the NORMAL")
    print("   wavevector components: (k_int sin th_int)^2 = (k sin th_ext)^2 + "
          "k^2 V0/E_eff.")
    print("   Writing it as sin^2 th_int = sin^2 th_ext + V0/E_eff additionally "
          "assumes k_int ~ k,")
    print(f"   an error of only {kint_over_k-1:.2e} in amplitude at 200 keV "
          "(negligible) -- see report 3.3.")

    # ---------------------------------------------------------------
    rule("4.  Si(111) SPECULAR ROD (n,-n,n) == (nnn):  REFRACTION-SHIFTED "
         "ANGLES AND STEP PHASES")
    print(f"h1 = d_111 = {d111:.4f} A (single bilayer);  "
          f"h2 = 2 d_111 = {2*d111:.4f} A (double bilayer)")
    print(f"V0 = {V0_SI_V:.1f} V (ASSUMPTION).  'B_vac' = vacuum Bragg angle "
          "(what the repository uses).")
    print("'th_int' = internal glancing angle at the Bragg condition; "
          "'th_ext' = the angle you must actually set.")
    print("frac = (|Delta_phi| mod 2pi).  wrap = Delta_phi wrapped into "
          "(-pi,pi] (signed, exp(+ik.r)).")
    for E in (100.0, 200.0, 300.0):
        lam = float(wavelength_A(E))
        tc = theta_critical_rad(E, V0_SI_V) * 1e3
        print(f"\n--- E = {E:.0f} keV  (lambda = {lam:.6f} A, "
              f"theta_c = {tc:.3f} mrad) ---")
        hdr = (f"{'(nnn)':>10} {'F?':>9} {'d_nnn(A)':>9} {'B_vac':>8} {'th_int':>8} "
               f"{'th_ext':>8} {'rho':>7} {'h_2pi(A)':>9} | "
               f"{'|dphi|1':>9} {'/2pi':>8} {'frac1':>8} {'f1/2pi':>7} {'wrap1':>8} | "
               f"{'frac2':>8} {'f2/2pi':>7} {'wrap2':>8}")
        print(hdr)
        print("-" * len(hdr))
        for n in range(1, 13):
            hkl = (n, n, n)
            sc = SpecularCondition(d111, n, E, V0_SI_V)
            ph1 = sc.step_phase(d111)
            ph2 = sc.step_phase(2 * d111)
            tag = "ALLOWED" if diamond_allowed(hkl) else "FORBIDDEN"
            if not sc.accessible:
                print(f"{str(hkl):>10} {tag:>9} {d111/n:9.4f} {sc.theta_B_vac*1e3:8.3f} "
                      f"{sc.theta_int*1e3:8.3f} {'--':>8} {'--':>7} {'--':>9} | "
                      f"INACCESSIBLE: internal Bragg angle is below the critical angle "
                      f"(total external reflection)")
                continue
            print(f"{str(hkl):>10} {tag:>9} {d111/n:9.4f} {sc.theta_B_vac*1e3:8.3f} "
                  f"{sc.theta_int*1e3:8.3f} {sc.theta_ext*1e3:8.3f} {sc.rho:7.4f} "
                  f"{sc.h_2pi_A:9.4f} | {ph1['abstotal']:9.4f} {ph1['over2pi']:8.4f} "
                  f"{ph1['mod2pi']:8.4f} {ph1['frac2pi']:7.4f} {ph1['wrapped']:8.4f} | "
                  f"{ph2['mod2pi']:8.4f} {ph2['frac2pi']:7.4f} {ph2['wrapped']:8.4f}")
    print("\n   Accessibility rule (DERIVED_HERE): a reflection can be excited in "
          "TRUE reflection")
    print("   (Bragg-case) geometry only if  G.n_hat > 2 dK,  i.e. "
          "|G| cos(angle(G,n)) > 2 k sqrt(V0/E_eff).")
    print("   For the (nnn) rod this means n >= 3 at 100-300 keV with V0 = 12 V.")

    # ---------------------------------------------------------------
    rule("4b.  Si(001) SPECULAR ROD (0,0,L):  a/4 AND a/2 STEPS")
    h_quarter, h_half = a / 4.0, a / 2.0
    print(f"single-layer step a/4 = {h_quarter:.4f} A;  "
          f"double-layer step a/2 = {h_half:.4f} A")
    print("The (0,0,L) rod has K_int = pi L / a at the Bragg condition; "
          "equivalently order n = L/4 of d = a/4.")
    for E in (100.0, 200.0, 300.0):
        print(f"\n--- E = {E:.0f} keV "
              f"(theta_c = {theta_critical_rad(E, V0_SI_V)*1e3:.3f} mrad) ---")
        hdr = (f"{'(00L)':>10} {'F?':>9} {'d_00L(A)':>9} {'B_vac':>8} {'th_int':>8} "
               f"{'th_ext':>8} {'rho':>7} {'h_2pi(A)':>9} | "
               f"{'frac(a/4)':>10} {'/2pi':>7} {'wrap':>8} | "
               f"{'frac(a/2)':>10} {'/2pi':>7} {'wrap':>8}")
        print(hdr)
        print("-" * len(hdr))
        for L in (4, 8, 12, 16):
            sc = SpecularCondition(h_quarter, L // 4, E, V0_SI_V)
            p1 = sc.step_phase(h_quarter)
            p2 = sc.step_phase(h_half)
            tag = "ALLOWED" if diamond_allowed((0, 0, L)) else "FORBIDDEN"
            print(f"{str((0,0,L)):>10} {tag:>9} {a/L:9.4f} {sc.theta_B_vac*1e3:8.3f} "
                  f"{sc.theta_int*1e3:8.3f} {sc.theta_ext*1e3:8.3f} {sc.rho:7.4f} "
                  f"{sc.h_2pi_A:9.4f} | {p1['mod2pi']:10.4f} {p1['frac2pi']:7.4f} "
                  f"{p1['wrapped']:8.4f} | {p2['mod2pi']:10.4f} {p2['frac2pi']:7.4f} "
                  f"{p2['wrapped']:8.4f}")

    # ---------------------------------------------------------------
    rule("5.  SENSITIVITY OF THE (nnn) RESULTS TO V0  (+/- 1 V, 200 keV)")
    hdr = (f"{'(nnn)':>10} | {'th_ext(mrad)':>28} | {'frac(d_111) [rad]':>30} | "
           f"{'dth/dV0':>9} {'dfrac/dV0':>10}")
    print(hdr)
    print(f"{'':>10} | {'11 V':>9} {'12 V':>9} {'13 V':>9} | "
          f"{'11 V':>9} {'12 V':>9} {'13 V':>9}    | {'mrad/V':>9} {'rad/V':>10}")
    print("-" * len(hdr))
    for n in (3, 4, 5, 6, 7, 8):
        row = []
        for V0 in (V0_SI_V - V0_SI_SENS_V, V0_SI_V, V0_SI_V + V0_SI_SENS_V):
            sc = SpecularCondition(d111, n, 200.0, V0)
            row.append((sc.theta_ext * 1e3, sc.step_phase(d111)['mod2pi']))
        dth = (row[2][0] - row[0][0]) / (2 * V0_SI_SENS_V)
        dfr = (row[2][1] - row[0][1]) / (2 * V0_SI_SENS_V)
        print(f"{str((n,n,n)):>10} | {row[0][0]:9.4f} {row[1][0]:9.4f} {row[2][0]:9.4f} | "
              f"{row[0][1]:9.4f} {row[1][1]:9.4f} {row[2][1]:9.4f}    | "
              f"{dth:9.4f} {dfr:10.4f}")
    print("\n   (dfrac/dV0 is a central difference of the fractional phase; where the")
    print("    phase wraps between 11 and 13 V the difference is meaningless and the")
    print("    unwrapped derivative d|dphi|/dV0 = 2 h dK_ext/dV0 should be used:)")
    for n in (4, 5, 6, 8):
        scs = [SpecularCondition(d111, n, 200.0, V) for V in (11.0, 12.0, 13.0)]
        dabs = (scs[2].step_phase(d111)['abstotal'] -
                scs[0].step_phase(d111)['abstotal']) / 2.0
        print(f"      (nnn) = ({n}{n}{n}): d|Delta_phi|/dV0 = {dabs:+.4f} rad/V")

    # ---------------------------------------------------------------
    rule("6.  THE REPOSITORY (666) CHOICE, AND THE REPOSITORY FORMULA "
         "h = dphi*lam/(4 pi sin(th_B) (g.n))")
    E = 200.0
    lam = float(wavelength_A(E))
    sc666 = SpecularCondition(d111, 6, E, V0_SI_V)
    print(f"Repository meta (pipeline/meta_tilt_examples.json): alpha_deg = 1.375 "
          f"-> {np.radians(1.375)*1e3:.4f} mrad")
    for aa, nm in ((A_SI_A, "a = 5.4309 A (generator default)"),
                   (A_SI_META_A, "a = 5.431  A (meta_tilt_examples)")):
        d666 = d_spacing_A((6, 6, 6), aa)
        thB = np.arcsin(lam / (2 * d666))
        print(f"   vacuum Bragg angle of (666) with {nm:34s}: "
              f"{thB*1e3:.4f} mrad = {np.degrees(thB):.5f} deg   "
              f"(d_666 = {d666:.6f} A)")
    print("   -> 1.375 deg = 23.997 mrad IS the VACUUM (666) Bragg angle. "
          "It ignores refraction.")
    print()
    print(f"With refraction (V0 = {V0_SI_V} V):")
    print(f"   internal Bragg glancing angle       = {sc666.theta_int*1e3:.4f} mrad")
    print(f"   REQUIRED EXTERNAL glancing angle    = {sc666.theta_ext*1e3:.4f} mrad")
    print(f"   offset from the repository setting  = "
          f"{(sc666.theta_ext - np.radians(1.375))*1e3:+.4f} mrad "
          f"({(sc666.theta_ext/np.radians(1.375)-1)*100:+.2f} %)")
    ph = sc666.step_phase(d111)
    print(f"   |Delta_phi| for h = d_111           = {ph['abstotal']:.4f} rad "
          f"= {ph['over2pi']:.4f} x 2pi")
    print(f"   fractional (mod 2pi)                = {ph['mod2pi']:.4f} rad "
          f"= {ph['frac2pi']:.4f} x 2pi   (signed, wrapped: {ph['wrapped']:+.4f} rad)")
    print(f"   height per 2pi  h_2pi               = {sc666.h_2pi_A:.4f} A")
    print("   WITHOUT refraction the vacuum momentum transfer would equal G_666 "
          "exactly and")
    print("   Delta_phi = -G.R = -2pi*integer == 0 : a d_111 step would be "
          "INVISIBLE.  The whole")
    print("   measurable signal at a specular Bragg condition is a refraction "
          "effect.")
    print()
    print("*** What the repository actually simulates: the beam is set to the "
          "EXTERNAL angle 1.375 deg. ***")
    k200 = float(k_ang_per_A(200.0))
    dK200 = delta_K_per_A(200.0, V0_SI_V)
    for lbl, th_e in (("1.375 deg (meta alpha_deg)", np.radians(1.375)),
                      ("23.9976 mrad (exact vacuum Bragg of 666)", sc666.theta_B_vac),
                      (f"{sc666.theta_ext*1e3:.4f} mrad (refraction-corrected)",
                       sc666.theta_ext)):
        Kx = k200 * np.sin(th_e)
        Kin = np.sqrt(Kx**2 + dK200**2)
        n_eff = Kin * d111 / np.pi
        tot = 2 * d111 * Kx
        print(f"   theta_ext = {lbl:42s}")
        print(f"      K_ext = {Kx:.6f} rad/A,  K_int = {Kin:.6f} rad/A  -> "
              f"effective rod order n_eff = K_int d_111/pi = {n_eff:.4f}")
        print(f"      |Delta_phi| for h = d_111 = {tot:.6f} rad = "
              f"{tot/TWO_PI:.6f} x 2pi  ->  mod 2pi = "
              f"{(tot/TWO_PI - np.floor(tot/TWO_PI))*TWO_PI:.6f} rad")
    print("   => AT THE REPOSITORY'S OWN SETTING A SINGLE-BILAYER STEP IS "
          "PHASE-INVISIBLE to ~3e-3 rad.")
    print("   The setting is 0.35 rod orders away from the true (666) condition, "
          "and it is exactly")
    print("   the angle at which q_vacuum = G_666 and the geometric phase is a "
          "multiple of 2pi.")
    print()
    print("Rocking curve of the d_111 step phase (h = d_111) vs EXTERNAL angle, "
          "200 keV:")
    print(f"{'th_ext(mrad)':>13} {'th_int(mrad)':>13} {'n_eff':>8} "
          f"{'|dphi| (rad)':>13} {'/2pi':>9} {'mod 2pi (rad)':>14} "
          f"{'wrapped (rad)':>14}")
    for th_mrad in (18.0, 20.0, 21.0, 22.0, 22.4953, 23.0, 23.9976, 25.0, 26.0,
                    26.7216):
        th_e = th_mrad * 1e-3
        Kx = k200 * np.sin(th_e)
        Kin = np.sqrt(Kx**2 + dK200**2)
        tot = 2 * d111 * Kx
        frac = (tot / TWO_PI - np.floor(tot / TWO_PI)) * TWO_PI
        print(f"{th_mrad:13.4f} "
              f"{theta_int_from_ext_rad(th_e,200.,V0_SI_V)*1e3:13.4f} "
              f"{Kin*d111/np.pi:8.4f} {tot:13.4f} {tot/TWO_PI:9.4f} "
              f"{frac:14.4f} {wrap_to_pi(-tot):14.4f}")

    print()
    print(f"Sweep over the ASSUMED mean inner potential (200 keV, h = d_111):")
    print(f"{'V0 (V)':>8} {'th_c(mrad)':>11} | "
          + " | ".join(f"{'(%d%d%d) th_ext / frac' % (n,n,n):>24}"
                       for n in (4, 5, 6, 8)))
    for V0 in (9.0, 10.0, 11.0, 12.0, 13.0, 14.0):
        cells = []
        for n in (4, 5, 6, 8):
            s = SpecularCondition(d111, n, 200.0, V0)
            cells.append(f"{s.theta_ext*1e3:10.4f} /{s.step_phase(d111)['mod2pi']:11.4f}")
        print(f"{V0:8.1f} {theta_critical_rad(200.0,V0)*1e3:11.4f} | "
              + " | ".join(cells))
    print()
    print("Error of the repository read-out h = Delta_phi*lambda/(4 pi sin(th_B)(g.n)):")
    g_dot_n = 1.0
    h_repo_scale = np.sin(sc666.theta_ext) / np.sin(np.radians(1.375))
    print(f"   (i)  wrong angle only (using th_B = 23.997 mrad instead of "
          f"th_ext = {sc666.theta_ext*1e3:.3f} mrad):")
    print(f"        h_reported / h_true = sin(th_ext)/sin(th_B) = "
          f"{h_repo_scale:.5f}  -> {100*(h_repo_scale-1):+.2f} %")
    print(f"        for a true h = d_111 = {d111:.4f} A this is an error of "
          f"{d111*(h_repo_scale-1):+.4f} A")
    h_from_wrapped_B = ph['mod2pi'] * lam / (4 * np.pi * np.sin(np.radians(1.375)) * g_dot_n)
    h_from_wrapped_E = ph['mod2pi'] * lam / (4 * np.pi * np.sin(sc666.theta_ext) * g_dot_n)
    print(f"   (ii) with the WRAPPED phase actually measured "
          f"({ph['mod2pi']:.4f} rad) fed into the formula:")
    print(f"        with th_B  = 23.997 mrad -> h = {h_from_wrapped_B:.4f} A "
          f"(true {d111:.4f} A, factor {d111/h_from_wrapped_B:.2f} low)")
    print(f"        with th_ext= {sc666.theta_ext*1e3:.3f} mrad -> h = "
          f"{h_from_wrapped_E:.4f} A  (= h_2pi * frac = "
          f"{sc666.h_2pi_A*ph['frac2pi']:.4f} A)")
    print("        -> the 2pi ambiguity, NOT the angle error, dominates.")

    # -- the repository's default target reflection (2,-2,0) ---------
    print()
    print("Repository DEFAULT target reflection (2,-2,0) off the (1,-1,1) facet:")
    g220 = np.array([2.0, -2.0, 0.0])
    d220 = d_spacing_A((2, -2, 0), A_SI_A)
    G220 = TWO_PI / d220
    ghat_dot_n = float(abs(g220 @ n111) / np.linalg.norm(g220))
    thB220 = np.arcsin(lam / (2 * d220))
    k200 = k_ang_per_A(200.0)
    dK200 = delta_K_per_A(200.0, V0_SI_V)
    Gdotn = G220 * ghat_dot_n
    print(f"   d_220 = {d220:.6f} A, |G| = {G220:.6f} rad/A, "
          f"g_hat.n_hat = {ghat_dot_n:.6f} (repo prints 0.8165)")
    print(f"   vacuum Bragg angle = {thB220*1e3:.4f} mrad "
          f"(repo meta target_theta_B_mrad)")
    print(f"   G.n_hat = {Gdotn:.6f} rad/A     2*dK = {2*dK200:.6f} rad/A")
    print(f"   ACCESSIBLE IN REFLECTION GEOMETRY?  G.n > 2 dK  ->  "
          f"{Gdotn > 2*dK200}")
    print(f"   sin(th_in)+sin(th_out) available in vacuum = "
          f"{Gdotn/k200:.6e}  -> th_in+th_out = {Gdotn/k200*1e3:.3f} mrad,")
    print(f"   but BOTH beams need > theta_c = "
          f"{theta_critical_rad(200.0, V0_SI_V)*1e3:.3f} mrad, i.e. a sum > "
          f"{2*theta_critical_rad(200.0, V0_SI_V)*1e3:.3f} mrad.")
    print("   -> (2,-2,0) CANNOT be excited in Bragg (reflection) geometry from "
          "this surface at 200 keV.")
    print()
    R = R_bilayer
    GvecA = TWO_PI / A_SI_A * g220                     # rad/A, cartesian
    print("   Vacuum-Bragg phase of a d_111 step for a NON-specular g "
          "(the repository formula vs the exact answer):")
    print(f"      repository:   (4 pi/lam) h sin(th_B) (g.n) = "
          f"{4*np.pi*d111*np.sin(thB220)*ghat_dot_n/lam:.6f} rad "
          f"= {4*np.pi*d111*np.sin(thB220)*ghat_dot_n/lam/TWO_PI:.6f} x 2pi")
    print(f"      exact:        G.R with R = (a/2)[1,0,1] = "
          f"{float(GvecA @ R):.6f} rad = {float(GvecA @ R)/TWO_PI:.6f} x 2pi")
    print("      The repository formula keeps only the NORMAL component of R "
          "(h n_hat) and drops")
    print("      G_par . R_par, which for (2,-2,0) contributes "
          f"{float(GvecA @ R) - 4*np.pi*d111*np.sin(thB220)*ghat_dot_n/lam:.6f} rad "
          f"= 2pi/3.")
    print("      Exact answer on the vacuum Bragg condition: G.R = 2pi x integer "
          "-> the step is INVISIBLE.")
    print("      The repository's predicted 2pi/3-per-bilayer staircase is an "
          "artefact of dropping R_par.")

    # ---------------------------------------------------------------
    rule("7.  2*pi AMBIGUITY AND THE ROCKING-SERIES REQUIREMENT")
    print(f"h_2pi = lambda / (2 sin theta_ext).  At 200 keV, (666) condition, "
          f"h_2pi = {sc666.h_2pi_A:.4f} A")
    print(f"{'h':>10} {'h (A)':>9} {'|dphi| (rad)':>13} {'/2pi wraps':>11} "
          f"{'dphi/dtheta (rad/mrad)':>23} {'max dtheta for <pi (mrad)':>26}")
    for lbl, h_A in (("3 A", 3.0), ("d_111", d111), ("1 nm", 10.0), ("10 nm", 100.0)):
        p = sc666.step_phase(h_A)
        slope = sc666.dphi_dtheta(h_A) * 1e-3          # rad per mrad
        dtheta_max = np.pi / sc666.dphi_dtheta(h_A) * 1e3
        print(f"{lbl:>10} {h_A:9.4f} {p['abstotal']:13.4f} {p['over2pi']:11.4f} "
              f"{slope:23.4f} {dtheta_max:26.4f}")
    print("\n   Rule of thumb (DERIVED_HERE): d(|dphi|)/d(theta) = "
          "(4 pi h/lambda) cos(theta)")
    print("   => the tilt step must satisfy  dtheta < lambda / (4 h cos theta).")
    print(f"   The repository's default tilt step (0.15 mrad, "
          f"si110_cleave_slab_generator.py) is")
    print(f"   adequate only for h < lambda/(4*0.15e-3) = "
          f"{lam/(4*0.15e-3):.1f} A = {lam/(4*0.15e-3)/10:.2f} nm.")

    # ---------------------------------------------------------------
    rule("8.  MULTISLICE GEOMETRY WITH THE REPOSITORY DEFAULT SLAB")
    n_x_si, n_y, n_z_si = 9, 12, 36
    x_vac, z_vac = 10.0, 30.0
    px = A_SI_A * np.sqrt(3.0)
    py = A_SI_A * np.sqrt(1.5)
    pz = A_SI_A / np.sqrt(2.0)
    Lx_si, Ly, Lz_si = n_x_si * px, n_y * py, n_z_si * pz
    Lx, Lz = Lx_si + 2 * x_vac, Lz_si + 2 * z_vac
    print("Defaults read from sample_generators/si110_cleave_slab_generator.py:")
    print(f"   periods: x {px:.4f} A (a sqrt3), y {py:.4f} A (a sqrt1.5), "
          f"z {pz:.4f} A (a/sqrt2)")
    print(f"   n_x_si=9, n_y=12, n_z_si=36, x_vac=10 A/side, z_vac=30 A/side")
    print(f"   Si plate : t_x = Lx_si = {Lx_si:.3f} A, Ly = {Ly:.3f} A, "
          f"Lz_si = {Lz_si:.3f} A")
    print(f"   supercell: Lx = {Lx:.3f} A, Ly = {Ly:.3f} A, Lz = {Lz:.3f} A")
    print(f"   4 terraces of Ly/4 = {Ly/4:.3f} A across y (step edges || beam)")
    print()
    for lbl, th in (("repository 23.997 mrad", np.radians(1.375)),
                    (f"refraction-corrected {sc666.theta_ext*1e3:.3f} mrad",
                     sc666.theta_ext)):
        tn = np.tan(th)
        rise_cell = Lz * tn
        rise_si = Lz_si * tn
        print(f"-- at theta = {lbl} (tan = {tn:.6f}) --")
        print(f"   rise of the reflected beam over the full cell   : "
              f"{rise_cell:.4f} A   (x_vac = 10 A -> no re-entry: {rise_cell < x_vac})")
        print(f"   rise over the Si length only                    : {rise_si:.4f} A")
        print(f"   z needed for a ray to fall the whole 10 A gap   : "
              f"{x_vac/tn:.1f} A   (Si is only {Lz_si:.1f} A long)")
        frac_nominal = rise_si / x_vac
        frac_channel = rise_si / (2 * x_vac)
        print(f"   fraction of the NOMINAL 10 A top gap that reaches the surface "
              f"within the slab : {frac_nominal*100:.2f} %")
        print(f"   fraction of the TRUE 20 A inter-plate vacuum channel "
              f"(PBC in x)                 : {frac_channel*100:.2f} %")
        band_lo = z_vac * tn
        band_hi = (z_vac + Lz_si) * tn
        print(f"   entrance-plane heights above the surface that land on the "
              f"crystal: {band_lo:.3f} .. {band_hi:.3f} A")
        frac_end = Lx_si / Lx
        frac_end_ref = (Lx_si + band_lo) / Lx
        print(f"   fraction of the incident plane wave entering through the FRONT "
              f"END FACE     : {frac_end*100:.2f} % "
              f"({frac_end_ref*100:.2f} % counting the rays that descend into it)")
        print(f"   ratio (end-face transmission)/(useful surface reflection) "
              f"= {frac_end/ (rise_si/Lx):.1f} : 1")
        print(f"   useful surface-reflection fraction of the whole incident wave "
              f"= {rise_si/Lx*100:.2f} %")
        print()
    print("Interaction length available to the surface reflection "
          "(DERIVED_HERE, geometric):")
    th_i = sc666.theta_int
    pen = Lz_si * np.tan(th_i)
    print(f"   internal glancing angle at the (666) condition: "
          f"{th_i*1e3:.4f} mrad")
    print(f"   a refracted ray entering at the top surface descends only "
          f"Lz_si*tan(th_int) = {pen:.3f} A")
    print(f"   over the whole {Lz_si:.1f} A of crystal, i.e. it crosses "
          f"{pen/d111:.3f} (1,-1,1) bilayers.")
    print(f"   -> the beam barely enters the crystal: no Bragg-case dynamical "
          f"reflection can build up.")
    print(f"   Lz_si required for a normal penetration depth delta_x "
          f"(= delta_x / tan(th_int)):")
    for dx_nm in (0.5, 1.0, 2.0, 5.0, 10.0):
        print(f"      delta_x = {dx_nm:5.1f} nm -> Lz_si >= "
              f"{dx_nm*10/np.tan(th_i)/10:9.1f} nm "
              f"({dx_nm*10/np.tan(th_i):9.0f} A)")
    print(f"   Also needed just to use the vacuum illumination: "
          f"Lz_si >= x_vac/tan(th_ext) = "
          f"{x_vac/np.tan(sc666.theta_ext):.0f} A. The default is "
          f"{Lz_si:.0f} A.")
    print(f"   Plate thickness t_x = Lx_si = {Lx_si:.1f} A = "
          f"{Lx_si/d111:.1f} bilayers = {Lx_si/10:.2f} nm.")
    print()
    print("Foreshortening / image sampling:")
    for lbl, th in (("23.997 mrad", np.radians(1.375)),
                    (f"{sc666.theta_ext*1e3:.3f} mrad", sc666.theta_ext),
                    ("50 mrad", 0.050)):
        print(f"   theta = {lbl:14s}: sin(theta) = {np.sin(th):.6f}  -> "
              f"foreshortening 1/sin = {1/np.sin(th):7.2f} x ;  "
              f"surface length per 0.13 A exit-plane pixel = "
              f"{0.13/np.tan(th):8.3f} A")
    print(f"   the whole {Lz_si:.1f} A Si surface maps onto "
          f"{Lz_si*np.tan(sc666.theta_ext):.3f} A of exit-plane height = "
          f"{Lz_si*np.tan(sc666.theta_ext)/0.13:.1f} pixels at 0.13 A.")

    # ---------------------------------------------------------------
    rule("9.  SAMPLING / BANDWIDTH / SLICE THICKNESS")
    for px_A in (0.13, 0.5):
        for E in (100.0, 200.0, 300.0):
            lamE = float(wavelength_A(E))
            q_nyq = 1.0 / (2 * px_A)              # cycles/A
            q_max = (2.0 / 3.0) * q_nyq           # 2/3 antialias rule
            a_nyq = lamE * q_nyq * 1e3            # mrad
            a_max = lamE * q_max * 1e3            # mrad
            print(f"   px = {px_A:.2f} A, E = {E:5.1f} keV: "
                  f"q_Nyq = {q_nyq:.4f} 1/A ({a_nyq:7.2f} mrad), "
                  f"q_max(2/3) = {q_max:.4f} 1/A ({a_max:7.2f} mrad)")
    print()
    print("   The reflected beam sits at +theta and the incident at -theta, so "
          "the grid must")
    print("   carry at least |k_x| = k sin(theta): 2*theta = "
          f"{2*sc666.theta_ext*1e3:.2f} mrad of angular span (specular) plus "
          "the crystal's own beams.")
    print(f"   px = 0.50 A (generator default advisory_pixel_size_A) gives "
          f"q_max = {2/3/(2*0.5):.4f} 1/A = "
          f"{float(wavelength_A(200.))*2/3/(2*0.5)*1e3:.2f} mrad at 200 keV")
    print("   -> CANNOT represent a 24 mrad tilt at all.  px = 0.13 A "
          "(meta_tilt_examples.json) gives")
    print(f"      {float(wavelength_A(200.))*(2/3)/(2*0.13)*1e3:.2f} mrad, "
          "which is adequate.")
    print()
    g666 = TWO_PI / d_spacing_A((6, 6, 6), A_SI_A) / TWO_PI   # cycles/A
    print(f"   |g_666| = {g666:.5f} 1/A must be inside q_max: "
          f"0.13 A -> {g666 < 2/3/(2*0.13)}, 0.50 A -> {g666 < 2/3/(2*0.5)}")
    print()
    print("   Paraxial (Fresnel) propagator error over the cell, "
          "|phase_exact - phase_paraxial|:")
    kk = k_ang_per_A(200.0)
    for alpha_mrad in (24.0, 45.0, 48.0, 64.3):
        al = alpha_mrad * 1e-3
        exact = kk * Lz * np.sqrt(max(1 - np.sin(al)**2, 0.0))
        parax = kk * Lz * (1 - al**2 / 2)
        print(f"      alpha = {alpha_mrad:5.1f} mrad over Lz = {Lz:.1f} A: "
              f"|Dphi| = {abs(exact-parax):.5f} rad  "
              f"(~k L alpha^4/8 = {kk*Lz*al**4/8:.5f} rad)")
    print("   -> the paraxial propagator is NOT the limiting approximation here.")
    print()
    dz_default = 1.0
    print(f"   Slice thickness: default dz = {dz_default:.2f} A; "
          f"crystal z-period a/sqrt2 = {pz:.4f} A")
    print(f"      slices per z-period = {pz/dz_default:.4f} (NOT an integer -> "
          "incommensurate slicing)")
    for nsl in (2, 4, 8):
        print(f"      commensurate alternative: {nsl} slices/period -> dz = "
              f"{pz/nsl:.5f} A")
    num_slices = int(np.ceil(Lz / dz_default))
    print(f"      num_slices = ceil(Lz/dz) = {num_slices} -> actual dz = "
          f"{Lz/num_slices:.5f} A")
    print(f"      transverse walk of the beam per slice = dz*tan(theta) = "
          f"{dz_default*np.tan(sc666.theta_ext):.5f} A "
          f"({dz_default*np.tan(sc666.theta_ext)/0.13:.4f} px) -> "
          "sub-pixel, not a limitation")

    # ---------------------------------------------------------------
    rule("10.  OFF-AXIS HOLOGRAPHY: CARRIER, RESOLUTION, NOISE")
    print("I = |u_o + u_r|^2 = |u_o|^2 + |u_r|^2 + "
          "2|u_o||u_r| cos(2 pi q_c.r + phi_o - phi_r)")
    print("Sideband isolation returns arg(u_o u_r*) = phi_o - phi_r.")
    print()
    print("Carrier requirement (DERIVED_HERE): if the object phase/amplitude is "
          "band-limited to |q| < B,")
    print("the autocorrelation centre band occupies |q| < 2B and the sidebands "
          "sit at +/- q_c with")
    print("radius B, so clean separation needs q_c > 3B, i.e. "
          "fringe spacing s = 1/q_c < 1/(3B).")
    print("Equivalently: reconstructed resolution ~ 1/B = 3 s  -> "
          "'3 fringes per resolved feature'.")
    print()
    print(f"{'fringe s (A)':>13} {'q_c (1/A)':>11} {'B_max=q_c/3':>12} "
          f"{'resolution 1/B (A)':>19} {'px for 4/fringe (A)':>20}")
    for s in (0.5, 1.0, 2.0, 5.0):
        print(f"{s:13.3f} {1/s:11.4f} {1/(3*s):12.4f} {3*s:19.3f} {s/4:20.4f}")
    print()
    print("Phase noise (DERIVED_HERE, see report 7.4): for a reconstruction "
          "aperture collecting")
    print("N detected electrons with fringe contrast mu, "
          "sigma_phi = sqrt(2)/(mu sqrt(N)).")
    print(f"{'mu':>6} {'N=1e2':>9} {'N=1e3':>9} {'N=1e4':>9} {'N=1e6':>9}   [rad]")
    for mu in (1.0, 0.5, 0.2, 0.1):
        vals = [np.sqrt(2) / (mu * np.sqrt(N)) for N in (1e2, 1e3, 1e4, 1e6)]
        print(f"{mu:6.2f} " + " ".join(f"{v:9.4f}" for v in vals))
    print()
    print("Height precision implied by the phase precision at the (666) "
          "condition (200 keV):")
    for sigma in (0.01, 0.05, 0.1, 0.5):
        print(f"   sigma_phi = {sigma:5.3f} rad -> sigma_h = "
              f"h_2pi*sigma/2pi = {sc666.h_2pi_A*sigma/TWO_PI:.5f} A")

    # ---------------------------------------------------------------
    rule("11.  NUMERICAL SELF-CHECKS")
    # (a) translation theorem for a truncated stack of (111) bilayers
    q = 2.0 * sc666.K_ext                       # rad/A, |k_out - k_in|
    mu_damp = 1.0 / 200.0                       # 1/A, attenuation with DEPTH
    depths = np.arange(0, 4000) * d111          # bilayer repeat
    sub = np.array([0.0, -0.25 * d111])         # two sublayers per bilayer
    dep = (depths[:, None] + sub[None, :]).ravel()
    dep = dep[dep <= 0.0] if False else dep
    # amplitude of a truncated stack whose surface is at x = x_s:
    def stack_amp(x_s):
        x = x_s - dep                          # atom heights (below surface)
        return np.sum(np.exp(-1j * q * x) * np.exp(-mu_damp * (x_s - x)))
    A_low = stack_amp(0.0)
    A_up = stack_amp(d111)
    ratio = A_up / A_low
    print("(a) Translation theorem for the specular beam, truncated (111) stack")
    print(f"    (q = 2 K_ext = {q:.6f} rad/A, depth attenuation 1/{1/mu_damp:.0f} A,"
          f" 4000 bilayers):")
    print(f"    arg(A_upper/A_lower) = {np.angle(ratio):+.9f} rad")
    print(f"    predicted -q*h mod 2pi = {wrap_to_pi(-q*d111):+.9f} rad")
    print(f"    |A_upper/A_lower|    = {abs(ratio):.12f}  (must be 1)")
    print(f"    agreement: {abs(wrap_to_pi(np.angle(ratio) + q*d111)):.2e} rad")
    # (b) closed-form vs direct dot product for the general Bragg phase
    print()
    print("(b) Equivalence of the two forms of the vacuum step phase,")
    print("    (2 pi/lam) h (sin th_in + sin th_out)  ==  (4 pi/lam) h sin(th_B)(g.n),")
    print("    i.e.  q.n_hat = G.n_hat  when the Bragg condition holds in VACUUM:")
    for hkl in [(6, 6, 6), (4, 4, 4), (2, -2, 0), (2, 2, 0), (3, 3, 1)]:
        gv = np.array(hkl, float)
        Gv = TWO_PI / A_SI_A * gv                    # rad/A
        nrm = np.linalg.norm(Gv)
        ghn = abs(float(gv @ n111) / np.linalg.norm(gv))
        thB = np.arcsin(nrm / (2 * k_ang_per_A(200.0)))
        lhs = abs(float(Gv @ n111))                  # = q.n_hat on the Bragg cond.
        rhs = 2 * k_ang_per_A(200.0) * np.sin(thB) * ghn
        print(f"    {str(hkl):>11}: g.n = {ghn:.6f}, th_B = {thB*1e3:7.3f} mrad, "
              f"|G.n| = {lhs:.8f}, 2k sin(th_B)(g.n) = {rhs:.8f}, "
              f"diff = {abs(lhs-rhs):.2e} rad/A")
    # (c) exact vs approximate refraction formula
    print()
    print("(c) exact  sin^2(th_int) = [ (k sin th_ext)^2 + dK^2 ] / k_int^2   vs")
    print("    approx sin^2(th_int) = sin^2(th_ext) + V0/E_eff :")
    for th_e_mrad in (10.0, 20.0, sc666.theta_ext * 1e3, 40.0):
        th_e = th_e_mrad * 1e-3
        th_i_exact = theta_int_from_ext_rad(th_e, 200.0, V0_SI_V)
        s2 = np.sin(th_e)**2 + V0_SI_V / E_eff_V(200.0, V0_SI_V)
        th_i_appr = np.arcsin(np.sqrt(s2))
        print(f"    th_ext = {th_e_mrad:7.3f} mrad -> th_int exact "
              f"{th_i_exact*1e3:8.4f} mrad, approx {th_i_appr*1e3:8.4f} mrad, "
              f"diff {(th_i_exact-th_i_appr)*1e6:+.2f} urad")

    # ---------------------------------------------------------------
    rule("12.  SYNTHETIC INTENSITY-HOLOGRAM RECONSTRUCTION "
         "(no ground truth passed to the reconstruction)")
    print("Object: two terraces, phase step dphi_true, unit amplitude. "
          "Reference: unit plane wave with")
    print("carrier of 'fringe' pixels.  Reconstruction: carrier located on an "
          "EMPTY hologram, Hann")
    print("sideband aperture of radius q_c/3, reference-hologram division, "
          "medians of terrace interiors.")
    print(f"\n{'dphi_true':>10} {'fringe(px)':>11} {'dose(e/px)':>11} "
          f"{'recovered':>10} {'error':>9} {'sigma_terr':>11} {'res(px)':>8}")
    ph666 = sc666.step_phase(d111)
    cases = [(ph666['wrapped'], 8.0, 0.0),
             (ph666['wrapped'], 8.0, 1.0e4),
             (ph666['wrapped'], 8.0, 1.0e2),
             (ph666['wrapped'], 4.0, 1.0e4),
             (ph666['wrapped'], 16.0, 1.0e4),
             (ph666['mod2pi'], 8.0, 1.0e4),
             (0.0, 8.0, 1.0e4),
             (-1.5640, 8.0, 1.0e4)]
    for dphi_true, fr, dose in cases:
        res = hologram_roundtrip(dphi_true, fringe_px=fr, dose_per_px=dose, seed=12345)
        print(f"{dphi_true:10.4f} {fr:11.1f} {dose:11.0f} {res['recovered']:10.4f} "
              f"{res['err']:+9.4f} {res['sigma']:11.4f} {res['res_px']:8.1f}")
    print(f"\n   Row 6 uses dphi_true = {ph666['mod2pi']:.4f} rad (> pi): the "
          f"reconstruction returns")
    print(f"   {wrap_to_pi(ph666['mod2pi']):+.4f} rad, i.e. exactly the same number as a "
          f"{wrap_to_pi(ph666['mod2pi']):+.4f} rad step.")
    print("   A single hologram cannot resolve the branch; a tilt series can "
          "(section 7).")
    print("   Row 7 is the no-step control; row 8 is the (666) double-bilayer "
          "value.")

    # ---------------------------------------------------------------
    rule("13.  TEST PLAN: NUMBERS A CORRECTED REPOSITORY MUST REPRODUCE "
         "(200 keV, a = 5.4309 A, V0 = 12 V)")
    checks = []

    def chk(name, got, want, tol, unit=""):
        ok = abs(got - want) <= tol
        checks.append(ok)
        print(f"   [{'PASS' if ok else 'FAIL'}] {name:<58s} "
              f"got {got:14.6f} {unit:<6s} want {want:12.6f} +/- {tol:g}")

    chk("T1  lambda(200 keV)", float(wavelength_A(200.0)), 0.0250793, 1e-6, "A")
    chk("T2  lambda(100 keV)", float(wavelength_A(100.0)), 0.0370144, 1e-6, "A")
    chk("T3  lambda(300 keV)", float(wavelength_A(300.0)), 0.0196875, 1e-6, "A")
    chk("T4  vacuum Bragg angle (666)", sc666.theta_B_vac * 1e3, 23.9976, 1e-3, "mrad")
    chk("T5  critical angle (V0=12 V)", theta_critical_rad(200.0, 12.0) * 1e3,
        8.3560, 1e-3, "mrad")
    chk("T6  external angle at the (666) internal condition",
        sc666.theta_ext * 1e3, 22.4953, 1e-3, "mrad")
    chk("T7  |F(666)|/f  (must be 0)", abs(structure_factor_over_f((6, 6, 6))),
        0.0, 1e-9)
    chk("T8  |F(444)|/f", abs(structure_factor_over_f((4, 4, 4))), 8.0, 1e-9)
    chk("T9  |F(555)|/f", abs(structure_factor_over_f((5, 5, 5))),
        4 * np.sqrt(2), 1e-9)
    chk("T10 step phase (666), h = d_111, mod 2pi",
        sc666.step_phase(d111)['mod2pi'], 3.9236, 2e-3, "rad")
    chk("T11 step phase (444), h = d_111, mod 2pi",
        SpecularCondition(d111, 4, 200.0, 12.0).step_phase(d111)['mod2pi'],
        2.5820, 2e-3, "rad")
    chk("T12 step phase (555), h = d_111, mod 2pi",
        SpecularCondition(d111, 5, 200.0, 12.0).step_phase(d111)['mod2pi'],
        3.4088, 2e-3, "rad")
    chk("T13 step phase (888), h = d_111, mod 2pi",
        SpecularCondition(d111, 8, 200.0, 12.0).step_phase(d111)['mod2pi'],
        4.5386, 2e-3, "rad")
    chk("T14 h_2pi at the (666) condition", sc666.h_2pi_A, 0.5575, 1e-3, "A")
    chk("T15 (2,-2,0) reflection-geometry accessibility  (0=no, 1=yes)",
        float(Gdotn > 2 * dK200), 0.0, 0.5)
    chk("T16 exact G.R / 2pi for (2,-2,0) and a d_111 step (integer!)",
        float(GvecA @ R) / TWO_PI, 1.0, 1e-9)
    chk("T17 top-gap illumination reaching the surface (theta_ext)",
        Lz_si * np.tan(sc666.theta_ext) / x_vac * 100, 31.10, 0.05, "%")
    chk("T18 incident wave entering the front end face",
        Lx_si / Lx * 100, 80.89, 0.05, "%")
    chk("T19 reflected-beam rise over the cell (must stay < x_vac)",
        Lz * np.tan(sc666.theta_ext), 4.4604, 1e-3, "A")
    chk("T20 foreshortening 1/sin(theta_ext)", 1 / np.sin(sc666.theta_ext),
        44.46, 0.02)
    chk("T21 antialiased max angle at 0.13 A, 200 keV",
        float(wavelength_A(200.0)) * (2 / 3) / (2 * 0.13) * 1e3, 64.31, 0.02, "mrad")
    chk("T22 antialiased max angle at 0.50 A, 200 keV (too small for 24 mrad)",
        float(wavelength_A(200.0)) * (2 / 3) / (2 * 0.50) * 1e3, 16.72, 0.02, "mrad")
    chk("T23 max tilt step for h = 1 nm (phase increment < pi)",
        float(wavelength_A(200.0)) / (4 * 10.0) * 1e3, 0.6270, 1e-3, "mrad")
    hr = hologram_roundtrip(sc666.step_phase(d111)['wrapped'],
                            dose_per_px=1e4, seed=12345)
    chk("T24 hologram round trip recovers the (666) single-step phase",
        hr['recovered'], sc666.step_phase(d111)['wrapped'], 5e-3, "rad")
    hr0 = hologram_roundtrip(0.0, dose_per_px=1e4, seed=12345)
    chk("T25 hologram round trip, no-step control", hr0['recovered'], 0.0,
        5e-3, "rad")
    print(f"\n   {sum(checks)}/{len(checks)} checks pass in this script itself.")

    rule("END OF OUTPUT")


# ===================================================================
# 12.  SYNTHETIC HOLOGRAM ROUND TRIP
# ===================================================================

def _sideband_wave(I: np.ndarray, peak_idx=None, ap_frac: float = 1.0 / 3.0):
    """Isolate one sideband of an intensity hologram and return the complex
    reconstructed wave plus the sideband index that was used.

    If `peak_idx` is given it is used as the carrier position; otherwise the
    brightest bin outside a central exclusion disc is used.  Nothing about the
    object is assumed.
    """
    n = I.shape[0]
    F = np.fft.fftshift(np.fft.fft2(I))
    f = np.fft.fftshift(np.fft.fftfreq(n))
    FX, FY = np.meshgrid(f, f)
    if peak_idx is None:
        mag = np.abs(F).copy()
        rr = np.hypot(FX, FY)
        mag[rr < 0.05] = 0.0                    # exclude the centre band
        peak_idx = np.unravel_index(np.argmax(mag), mag.shape)
    iy, ix = peak_idx
    qcy, qcx = FY[iy, ix], FX[iy, ix]
    R_ap = np.hypot(qcx, qcy) * ap_frac
    r = np.hypot(FX - qcx, FY - qcy)
    ap = np.where(r < R_ap, 0.5 * (1 + np.cos(np.pi * r / R_ap)), 0.0)
    side = np.roll(F * ap, (-(iy - n // 2), -(ix - n // 2)), axis=(0, 1))
    return np.fft.ifft2(np.fft.ifftshift(side)), (iy, ix), float(R_ap)


def hologram_roundtrip(dphi_true_rad: float,
                       n: int = 512,
                       fringe_px: float = 8.0,
                       dose_per_px: float = 0.0,
                       seed: int = 0) -> dict:
    """Synthetic off-axis hologram round trip; the reconstruction NEVER sees
    dphi_true_rad.

    Procedure (this is what an experiment does, [B09]/[C01] in spirit):
      1. object hologram   I_obj = |u_o + u_r|^2
      2. EMPTY hologram    I_ref = |1   + u_r|^2   (same carrier, no object)
      3. locate the carrier on the EMPTY hologram (a clean single bin);
      4. apply the same sideband aperture + recentring to both;
      5. phase = arg( rec_obj / rec_ref )  -- the standard reference-hologram
         division, which removes the residual carrier and the aperture's own
         transfer function;
      6. step = median(upper terrace) - median(lower terrace).

    NOTE on why step 2/3 matter: the brightest bin of the OBJECT hologram is
    generally NOT the carrier (for a 50/50 phase step it sits one bin off, on
    the square-wave fundamental), and recentring on it injects a spurious phase
    ramp.  This is a real processing trap, not a numerical detail.
    """
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n]

    edge = n // 2
    soft = 0.5 * (1.0 + np.tanh((y - edge) / 2.0))     # soft terrace boundary
    u_o = np.exp(1j * dphi_true_rad * soft)

    q_c = 1.0 / fringe_px                              # cycles/pixel
    u_r = np.exp(2j * np.pi * q_c * x)

    I_obj = np.abs(u_o + u_r) ** 2
    I_ref = np.abs(1.0 + u_r) ** 2
    contrast_ideal = 2.0 * 1.0 * 1.0 / (1.0 + 1.0)

    if dose_per_px > 0:
        I_obj = rng.poisson(I_obj / I_obj.mean() * dose_per_px).astype(float)
        I_ref = rng.poisson(I_ref / I_ref.mean() * dose_per_px).astype(float)

    rec_ref, pk, R_ap = _sideband_wave(I_ref)          # carrier from the empty hologram
    rec_obj, _, _ = _sideband_wave(I_obj, peak_idx=pk)

    phase = np.angle(rec_obj / rec_ref)

    res_px = 1.0 / max(R_ap, 1e-12)                    # reconstruction resolution
    pad = int(min(max(3.0 * res_px, 8), n // 4 - 1))
    lo = phase[pad:edge - pad, pad:n - pad]
    hi = phase[edge + pad:n - pad, pad:n - pad]
    recovered = wrap_to_pi(np.median(hi) - np.median(lo))
    sigma = 0.5 * (np.std(wrap_to_pi(lo - np.median(lo)))
                   + np.std(wrap_to_pi(hi - np.median(hi))))

    return dict(recovered=float(recovered),
                err=float(wrap_to_pi(recovered - wrap_to_pi(dphi_true_rad))),
                sigma=float(sigma),
                contrast=float(contrast_ideal),
                q_c=float(q_c),
                aperture=float(R_ap),
                res_px=float(res_px))


if __name__ == "__main__":
    main()
