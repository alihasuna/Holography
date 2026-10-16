#!/usr/bin/env python3
"""Rung R1: print every geometry number quoted in REPORT_R0_R1.md (200 keV only)."""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from reflection_holo import constants as C  # noqa: E402
from reflection_holo import geometry as G  # noqa: E402
from reflection_holo import project_inputs as P  # noqa: E402

S111 = G.Surface((1, -1, 1), (1, 1, 0))
S001 = G.Surface((0, 0, 1), (1, 1, 0))


def _h(t):
    return "(" + ",".join(str(int(v)) for v in t) + ")"


def _u(t):
    return "[" + ",".join(str(int(v)) for v in t) + "]"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept-assumptions", action="store_true")
    args = ap.parse_args(argv)
    E = float(P.get("E0"))
    a = C.A_SI.value
    d111 = a / math.sqrt(3.0)
    print(f"R1 GEOMETRY -- E0 = {E:.0f} eV (PROJECT_INPUT, SUPPLIED)")
    print(f"lambda = {C.wavelength(E):.8f} A (card shindo_tomita_appA p.2: 0.00250793 nm)")
    print(f"k = 2pi/lambda = {C.wavenumber(E):.4f} rad/A; gamma = {C.gamma(E):.6f}")
    print(f"sigma = {C.interaction_constant(E):.4e} rad/(V A) "
          f"(card shindo_tomita_appA p.2: 0.0072884 V^-1 nm^-1)")
    try:
        V0 = G.resolve_V0(None, args.accept_assumptions)
    except P.MissingProjectInput as e:
        print(f"R1 ABORTED: MissingProjectInput: {e}")
        print("Re-run with --accept-assumptions to proceed on the labelled placeholders.")
        return 2
    D = G.delta_refraction(E, V0)
    print(f"Delta = {D:.4e}; Delta/(V0/T) = {D/(V0/E):.3f} (relativistic / non-relativistic)")
    tck = math.asin(G.delta_K(E, V0) / C.wavenumber(E))
    print(f"theta_c (internal; sin = dK/k_int) = {G.critical_angle(E, V0)*1e3:.3f} mrad; "
          f"(sin = dK/k) = {tck*1e3:.3f} mrad")
    print("frames (rows x_beam, y, z_normal in crystal cartesian):")
    for s in (S111, S001):
        print(f"Si{_h(s.hkl)} azimuth {_u(s.azimuth)}:")
        for name, row in zip(("x_beam", "y     ", "z_norm"), G.frame(s)):
            print(f"  {name} = [{row[0]:+.6f} {row[1]:+.6f} {row[2]:+.6f}]")

    print("Si(1,-1,1) specular rod (n,-n,n), allowed orders n <= 12:")
    for o in G.specular_orders(S111, E, nmax=12, V0=V0):
        head = (f"  {o['hkl']} |F|={o['F_abs']:.3f} thB={o['theta_B_vac']*1e3:.3f} "
                f"th_int={o['theta_int']*1e3:.3f}")
        if not o["accessible"]:
            print(head + " INACCESSIBLE (K_int < dK)")
            continue
        ph = G.wrap_to_pi(G.specular_step_phase(d111, o["theta_ext"], E))
        print(head + f" th_ext={o['theta_ext']*1e3:.3f} h_2pi={o['h_2pi']:.3f} "
              f"1/sin={o['foreshortening']:.1f} shadow(d111)={G.shadow_length(d111, o['theta_ext']):.1f} "
              f"phi(d111)={ph:+.3f}")
    print("  forbidden (refused by the guard): "
          + " ".join(str(t) for t in G.forbidden_rod_orders(S111, 12)))

    print("Si(0,0,1) specular rod (0,0,L), allowed orders L <= 16:")
    for o in G.specular_orders(S001, E, nmax=16, V0=V0):
        p4 = G.wrap_to_pi(G.specular_step_phase(a / 4, o["theta_ext"], E))
        p2 = G.wrap_to_pi(G.specular_step_phase(a / 2, o["theta_ext"], E))
        print(f"  {o['hkl']} |F|={o['F_abs']:.3f} thB={o['theta_B_vac']*1e3:.3f} "
              f"th_int={o['theta_int']*1e3:.3f} th_ext={o['theta_ext']*1e3:.3f} "
              f"h_2pi={o['h_2pi']:.3f} 1/sin={o['foreshortening']:.1f} "
              f"phi(a/4)={p4:+.3f} phi(a/2)={p2:+.3f}")
    print("  forbidden (refused by the guard): "
          + " ".join(str(t) for t in G.forbidden_rod_orders(S001, 16)))

    acc = G.reflection_accessibility((2, -2, 0), S111, E, V0)
    print(f"(2, -2, 0) on Si(1,-1,1): G.n = {acc['G_dot_n']:.4f} rad/A, 2 dK = {acc['two_dK']:.4f} "
          f"rad/A, accessible = {acc['accessible']}")
    R = 0.5 * a * np.array([1.0, 0.0, 1.0])
    print(f"G.R/2pi for (2, -2, 0) and R = (a/2)[1,0,1]: "
          f"{float(G.reciprocal_vector((2, -2, 0)) @ R)/(2*math.pi):.6f}")
    try:
        G.rod_condition(S111, 6, E, V0)
    except G.ForbiddenReflectionError as e:
        print(f"rod_condition(Si(1,-1,1), n=6) -> {type(e).__name__}: {e}")
    c6 = G.rod_condition(S111, 6, E, V0, allow_forbidden=True)
    mod = abs(G.specular_step_phase(d111, c6["theta_ext"], E)) % (2 * math.pi)
    print(f"override allow_forbidden=True (calculator T4, T6, T10, T14, T20): thB = "
          f"{c6['theta_B_vac']*1e3:.4f} mrad, th_ext = {c6['theta_ext']*1e3:.4f} mrad, "
          f"phi(d111) mod 2pi = {mod:.4f} rad, h_2pi = {c6['h_2pi']:.4f} A, "
          f"1/sin = {G.foreshortening(c6['theta_ext']):.2f}")
    c4 = G.rod_condition(S111, 4, E, V0)
    print(f"(4, -4, 4) at its vacuum Bragg angle: Delta_phi(d111)/2pi = "
          f"{G.specular_step_phase(d111, c4['theta_B_vac'], E)/(2*math.pi):.6f}")
    print(f"max tilt step for h = 1 nm at the (6,-6,6) angle: "
          f"{G.max_tilt_step(10.0, c6['theta_ext'], E)*1e3:.4f} mrad")
    print(f"Peng neutral-atom Si: sum f(0) = {C.PENG_SI_F0_SUM:.4f} A per atom; hbar^2/2m0 = "
          f"{C.HBAR2_OVER_2M0_EV_A2:.5f} eV A^2; V0 (8 atoms, a = {a} A) = "
          f"{C.V0_PENG_NEUTRAL_SI.value:.2f} V (DERIVED_HERE) vs placeholder {V0} V")
    lo = sum(c * 80.0 ** i for i, c in enumerate(C.DW_SI_LOW_T))
    hi = sum(c * 80.0 ** i for i, c in enumerate(C.DW_SI_HIGH_T))
    print(f"Debye-Waller (Peng ch.14): B(300 K) = {C.debye_waller_B(300.0):.4f} A^2; B(80 K) "
          f"low-T fit {lo:.4f}, high-T fit {hi:.4f} (mismatch {(lo-hi)/hi*100:.2f} %)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
