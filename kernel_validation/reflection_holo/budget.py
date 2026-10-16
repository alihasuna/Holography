"""reflection_holo.budget -- rung R0 error budget.

Comparisons (task R0), all at the Si(001) specular (0,0,8) condition, 200 keV:
 (a) a/4 vs a/2 step;  (b) V0 = 12 V vs 13 V;  (c) overlayer 0 vs 1 nm (reduced-density layer).

Required precision (DERIVED_HERE): two hypotheses whose predicted phases differ by D (circular
distance in (-pi, pi]) are separable if |D| >= SEPARATION_SIGMA * sigma (ASSUMPTION: 5 sigma,
midpoint misclassification 0.6 %), so required sigma = |D|/5.

Phases are geometric (translation covariance, repo:physics_conventions.md 'Step phase'):
 * step: Delta_phi = -2 h K_ext. The Si(001) a/4 terraces are 4_1-screw related, so the dynamical
   part of their phases differs (repo:calculator_output.txt sec.2b); that residual is NOT in this
   budget (R2).
 * V0: at a FIXED external angle the geometric step phase does not depend on V0. V0 moves the
   angle of the (0,0,8) peak; the step phase measured AT the peak then changes by
   (dphi/dtheta) * dtheta_peak. Comparison (b) is therefore one measurement viewed twice: (b1)
   locate the peak in angle, (b2) phase at the peak; (b2) needs the angle scale to the same level.
 * overlayer (ASSUMPTION model): a layer of thickness t and mean potential f*V0 added on top of an
   unchanged crystal, refraction only, no internal reflections (WKB): extra phase on the double
   pass phi_ox = 2 t (K_L - K_ext), K_L = sqrt(K_ext^2 + f dK^2). Absorption in the layer is not
   computable (absorptive parameters MISSING, item 21). A conformal layer is common to object and
   reference if the reference is reflected from the same surface -> phase-blind.

Achievable precision (each factor DERIVED_HERE unless noted):
 * shot noise per region sigma = sqrt(2)/(mu sqrt(N)) [repo:calculator_output.txt sec.10, there
   labelled DERIVED_HERE; no card states a dose-noise law: card:shindo_tomita_ch04-06 'phase noise
   vs dose: NOT IN THIS DOCUMENT' -> UNVERIFIED]; step = difference of two regions -> x sqrt(2).
 * mu = mu0 * MTF(q_c) * drift envelope exp(-2 pi^2 (sigma_d/s)^2) * convergence envelope
   exp(-(1/2)((dphi/dtheta) sigma_alpha)^2) (Gaussian averages of exp(i delta phi)).
   dphi/dtheta = 2 h k cos(theta) for a step of height h: the (4 pi h/lambda) cos(theta) of the
   task statement / repo item 3.
 * energy spread: dk/k = dE (T + E0)/(T (T + 2E0)); phase spread |Delta_phi| dk/k.
Every input above except the beam energy is MISSING and enters only via
project_inputs.get(..., accept_assumptions=True).
"""
from __future__ import annotations

import argparse
import math
import sys

from . import constants as C
from . import geometry as G
from . import project_inputs as P

SEPARATION_SIGMA = 5.0                       # ASSUMPTION
V0_HYPOTHESES = (12.0, 13.0)                 # task R0(b)
OVERLAYER_THICKNESS_A = 10.0                 # task R0(c): 0 vs 1 nm
SURFACE_001 = G.Surface((0, 0, 1), (1, 1, 0))
ORDER = 8                                    # (0,0,8), CFG-B working condition (spec sec.2)
CARD_ANCHOR_RAD = 0.03                       # card:shindo_tomita_ch04-06 p.46/pr.60

LIM_A = ("items 6, 16 (dose, fringe contrast); a/4 terraces are 4_1-screw related, "
         "dynamical residual not included (R2)")
LIM_B1 = "items 7, 9 (angle calibration, measured rocking curve)"
LIM_C = ("items 12, 15 (layer state, reference trajectory); layer absorption item 21")


def circular_distance(p: float, q: float) -> float:
    return abs(G.wrap_to_pi(p - q))


def sigma_phi_region(mu: float, N: float) -> float:
    """sqrt(2)/(mu sqrt(N)) [repo calculator sec.10; UNVERIFIED against a card]."""
    return math.sqrt(2.0) / (mu * math.sqrt(N))


def sigma_phi_step(mu: float, N: float) -> float:
    """Step phase = difference of two independent terrace means. DERIVED_HERE."""
    return math.sqrt(2.0) * sigma_phi_region(mu, N)


def n_min_for_step(mu: float, sigma: float) -> float:
    """Electrons per terrace for sigma_phi_step = sigma. DERIVED_HERE."""
    return (2.0 / (mu * sigma)) ** 2


def gaussian_phase_envelope(sigma_phase: float) -> float:
    return math.exp(-0.5 * sigma_phase ** 2)


def drift_envelope(rms_over_fringe: float) -> float:
    return math.exp(-2.0 * math.pi ** 2 * rms_over_fringe ** 2)


def relative_k_spread(E_eV: float, dE_eV: float) -> float:
    T, E0 = float(E_eV), C.MEC2_EV.value
    return dE_eV * (T + E0) / (T * (T + 2.0 * E0))


def overlayer_phase(t_A: float, theta_ext: float, E_eV: float, V0: float, fraction: float) -> float:
    """phi_ox = 2 t (K_L - K_ext) (ASSUMPTION model, see module docstring)."""
    Kx = C.wavenumber(E_eV) * math.sin(theta_ext)
    KL = math.sqrt(Kx ** 2 + fraction * G.delta_K(E_eV, V0) ** 2)
    return 2.0 * t_A * (KL - Kx)


def overlayer_phase_slope(t_A, theta_ext, E_eV, V0, fraction) -> float:
    k = C.wavenumber(E_eV)
    Kx = k * math.sin(theta_ext)
    KL = math.sqrt(Kx ** 2 + fraction * G.delta_K(E_eV, V0) ** 2)
    return 2.0 * t_A * k * math.cos(theta_ext) * (Kx / KL - 1.0)


def compute_budget(accept_assumptions: bool = False) -> dict:
    """All R0 numbers. Raises MissingProjectInput unless accept_assumptions."""
    E = float(P.get("E0"))
    V0 = float(P.get("V0_SI", accept_assumptions))
    frac = P.get("overlayer_potential_fraction", accept_assumptions)
    mu0 = P.get("fringe_contrast", accept_assumptions)
    mtf = P.get("camera_mtf_at_carrier", accept_assumptions)
    drift = P.get("drift_rms_over_fringe", accept_assumptions)
    sig_alpha = P.get("convergence_semiangle_rad", accept_assumptions)
    dose = P.get("dose_e_per_px", accept_assumptions)
    npx = P.get("n_px_per_terrace", accept_assumptions)
    dE = P.get("energy_spread_eV", accept_assumptions)
    ref = P.get("reference_trajectory", accept_assumptions)

    a = C.A_SI.value
    k = C.wavenumber(E)
    c12 = G.rod_condition(SURFACE_001, ORDER, E, V0_HYPOTHESES[0])
    c13 = G.rod_condition(SURFACE_001, ORDER, E, V0_HYPOTHESES[1])
    cV = G.rod_condition(SURFACE_001, ORDER, E, V0)
    th = cV["theta_ext"]

    # (a)
    p4 = G.wrap_to_pi(G.specular_step_phase(a / 4, th, E))
    p2 = G.wrap_to_pi(G.specular_step_phase(a / 2, th, E))
    D_a = circular_distance(p4, p2)
    # (b)
    p2_12 = G.wrap_to_pi(G.specular_step_phase(a / 2, c12["theta_ext"], E))
    p2_13 = G.wrap_to_pi(G.specular_step_phase(a / 2, c13["theta_ext"], E))
    D_b = circular_distance(p2_12, p2_13)
    dth = c13["theta_ext"] - c12["theta_ext"]
    slope_b = 2.0 * (a / 2) * k * math.cos(c12["theta_ext"])
    # (c)
    phi_ox = overlayer_phase(OVERLAYER_THICKNESS_A, th, E, V0, frac)
    D_c = circular_distance(phi_ox, 0.0)
    slope_c = overlayer_phase_slope(OVERLAYER_THICKNESS_A, th, E, V0, frac)

    req_a, req_b1, req_b2, req_c = (D_a / SEPARATION_SIGMA, abs(dth) / SEPARATION_SIGMA,
                                    D_b / SEPARATION_SIGMA, D_c / SEPARATION_SIGMA)

    N = float(dose) * float(npx)
    env_d = drift_envelope(drift)
    slope_a = 2.0 * (a / 2) * k * math.cos(th)            # worst of the two step heights
    env_a = gaussian_phase_envelope(slope_a * sig_alpha)
    env_b = gaussian_phase_envelope(slope_b * sig_alpha)
    env_c = gaussian_phase_envelope(abs(slope_c) * sig_alpha)
    mu_a, mu_b, mu_c = (mu0 * mtf * env_d * e for e in (env_a, env_b, env_c))
    sig_a, sig_b, sig_c = (sigma_phi_step(m, N) for m in (mu_a, mu_b, mu_c))
    return dict(E0=E, V0=V0, frac=frac, mu0=mu0, mtf=mtf, drift=drift, sig_alpha=sig_alpha,
                dose=dose, npx=npx, dE=dE, ref=ref, N=N, c12=c12, c13=c13, th=th,
                p4=p4, p2=p2, D_a=D_a, p2_12=p2_12, p2_13=p2_13, D_b=D_b, dth=dth,
                slope_b=slope_b, phi_ox=phi_ox, D_c=D_c,
                req_a=req_a, req_b1=req_b1, req_b2=req_b2, req_c=req_c,
                env_d=env_d, env_a=env_a, sig_alpha_half=math.sqrt(2 * math.log(2)) / slope_a,
                dE_phase=abs(G.specular_step_phase(a / 2, th, E)) * relative_k_spread(E, dE),
                sig_region=sigma_phi_region(mu_a, N),
                sig_a=sig_a, sig_b=sig_b, sig_c=sig_c,
                nmin_a=n_min_for_step(mu_a, req_a), nmin_b=n_min_for_step(mu_b, req_b2),
                nmin_c=n_min_for_step(mu_c, req_c), n_assumptions=len(P.USED_ASSUMPTIONS))


def _feas(ach, req, nmin):
    return f"YES (N_min = {nmin:.2e} e)" if ach <= req else f"NO (N_min = {nmin:.2e} e)"


def report_lines(accept_assumptions: bool = False) -> list[str]:
    r = compute_budget(accept_assumptions)
    L = [f"R0 ERROR BUDGET -- Si(001) specular (0,0,8) condition, E0 = {r['E0']:.0f} eV "
         f"(PROJECT_INPUT, SUPPLIED)",
         f"separation criterion: hypotheses distinguishable if |D| >= {SEPARATION_SIGMA:.1f} "
         f"sigma (ASSUMPTION)",
         "-- required precision (geometric phases, DERIVED_HERE) --",
         f"(0,0,8): theta_ext(V0={V0_HYPOTHESES[0]:.1f} V) = {r['c12']['theta_ext']*1e3:.4f} mrad, "
         f"theta_ext(V0={V0_HYPOTHESES[1]:.1f} V) = {r['c13']['theta_ext']*1e3:.4f} mrad, "
         f"peak shift = {r['dth']*1e3:+.3f} mrad",
         f"(a) wrapped step phase: a/4 = {r['p4']:+.3f} rad, a/2 = {r['p2']:+.3f} rad; "
         f"D = {r['D_a']:.3f} rad",
         f"(b) a/2 step phase at the (0,0,8) peak: V0={V0_HYPOTHESES[0]:.1f} V -> {r['p2_12']:+.3f} "
         f"rad, V0={V0_HYPOTHESES[1]:.1f} V -> {r['p2_13']:+.3f} rad; D = {r['D_b']:.3f} rad",
         f"(b) d(phi_a/2)/d(theta_ext) = {r['slope_b']:.1f} rad/rad; peak-shift requirement = "
         f"{r['req_b1']*1e6:.1f} urad",
         f"(c) overlayer t = {OVERLAYER_THICKNESS_A:.1f} A, V_layer = {r['frac']} x V0: phase "
         f"2t(K_L - K_ext) = {r['phi_ox']:+.3f} rad, wrapped {G.wrap_to_pi(r['phi_ox']):+.3f} rad; "
         f"D = {r['D_c']:.3f} rad",
         "-- achievable precision (placeholders; see ASSUMPTION lines) --",
         f"fringe contrast mu0 = {r['mu0']}, camera MTF at carrier = {r['mtf']}, drift envelope = "
         f"{r['env_d']:.4f}, N per terrace = {r['N']:.2e} e",
         f"convergence sigma_alpha = {r['sig_alpha']:.1e} rad: envelope for a/2 step = "
         f"{r['env_a']:.6f}; envelope falls to 0.5 at {r['sig_alpha_half']*1e3:.3f} mrad",
         f"energy spread {r['dE']} eV: a/2 step phase spread = {r['dE_phase']:.1e} rad (negligible)",
         f"sigma_phi per terrace = {r['sig_region']:.4f} rad; step (two terraces) = "
         f"{r['sig_a']:.4f} rad",
         f"card anchor (transmission, split illumination): +/-{CARD_ANCHOR_RAD} rad in a Si "
         f"substrate [shindo_tomita ch06 p.46/pr.60]",
         "",
         "| comparison | required sigma_phi | achievable sigma_phi | feasible? | limiting input |",
         "|---|---|---|---|---|",
         f"| (a) Si(001) a/4 vs a/2 step at (0,0,8) | {r['req_a']:.3f} rad | {r['sig_a']:.4f} rad | "
         f"{_feas(r['sig_a'], r['req_a'], r['nmin_a'])} | {LIM_A} |",
         f"| (b1) V0 12 vs 13 V: (0,0,8) peak shift {r['dth']*1e3:+.3f} mrad | "
         f"{r['req_b1']*1e6:.1f} urad in theta_ext (angle) | not computable from the cards | "
         f"UNDETERMINED | {LIM_B1} |",
         f"| (b2) V0 12 vs 13 V: a/2 step phase at the peak | {r['req_b2']:.4f} rad | "
         f"{r['sig_b']:.4f} rad | {_feas(r['sig_b'], r['req_b2'], r['nmin_b'])} | items 6, 16; "
         f"equivalent to locating the peak to {r['req_b1']*1e6:.1f} urad (item 7) |"]
    if r["ref"] == "vacuum" and r["sig_c"] <= r["req_c"]:
        fc = (f"YES if the reference avoids the layer (reference_trajectory = {r['ref']}) "
              f"(N_min = {r['nmin_c']:.2e} e)")
    elif r["ref"] != "vacuum":
        fc = "NO (layer common to object and reference)"
    else:
        fc = f"NO (N_min = {r['nmin_c']:.2e} e)"
    L.append(f"| (c) overlayer 0 vs 1 nm, reduced-density layer (ASSUMPTION) | {r['req_c']:.3f} rad | "
             f"{r['sig_c']:.4f} rad | {fc} | {LIM_C} |")
    L.append("")
    L.append(f"assumptions used: {r['n_assumptions']} (listed above); every achievable entry is "
             f"conditional on them.")
    return L


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Print the R0 error budget.")
    ap.add_argument("--accept-assumptions", action="store_true")
    args = ap.parse_args(argv)
    try:
        lines = report_lines(args.accept_assumptions)
    except P.MissingProjectInput as e:
        print(f"R0 ABORTED: MissingProjectInput: {e}")
        print("Re-run with --accept-assumptions to proceed on the labelled placeholders.")
        return 2
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
