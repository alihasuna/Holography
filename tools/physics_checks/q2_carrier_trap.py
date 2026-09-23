#!/usr/bin/env python3
r"""
C2 question 2: the carrier-location trap of docs/03 section 6 (0.78 rad instead of 2.36 rad).

Run:  venv/bin/python tools/physics_checks/q2_carrier_trap.py
Exit status 0 only if every self-check passes.  Report: docs/agent_reports/C2_phase2_physics_checks.md

Setup: the calculator's hologram_roundtrip (tools/reflection_step_phase_calculator.py, section 12,
check T24): n = 512 px, fringe 8 px along axis 1 (u_r = exp(2 pi i x/8)), object
u_o = exp(i Delta s(y)) with s(y) = 0.5 (1 + tanh((y - 256)/2)), Delta = sc666.step_phase(d111)
['wrapped'] = 2.3596 rad, Hann sideband aperture of radius q_c/3, terrace medians with
pad = 3 resolutions. The calculator's own functions are imported (never re-typed); the package
chain (reflection_holo.optics / reconstruction) is run on the same holograms.

Conventions: numpy FFT (kernel exp(-2 pi i q.r)); a wave exp(+2 pi i q0.r) appears at +q0. With
u_r = exp(+2 pi i q_c x), I = 2 + u_o u_r^* + u_o^* u_r: the sideband at -q_c holds u_o u_r^*
(phase phi_o - phi_r, the correct one); the sideband at +q_c holds u_o^* u_r (phi_r - phi_o, the
conjugate). Bins are quoted as (k_y, k_x) in cycles per field (k_x = +-64 is the carrier) and as
fftshifted array indices (256 + k_y, 256 + k_x), the calculator's layout.

Premise of the analytic part (DERIVED_HERE): for a sharp 50/50 step (s in {0, 1}),
exp(i Delta s) = (1 + e^{i Delta})/2 + (e^{i Delta} - 1)/2 sq(y) with sq = 2 s - 1 = +-1, whose
Fourier coefficients are 0 at k = 0 and 2/(pi |k|) in modulus at odd k. The carrier bin therefore
has modulus |cos(Delta/2)| and the first harmonic (k_y = +-1) (2/pi)|sin(Delta/2)|: the harmonic is
brighter when |tan(Delta/2)| > pi/2, i.e. |Delta| > 2 arctan(pi/2) = 2.0078 rad (mod 2 pi).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reflection_holo.optics import (ArtefactOptions, Grid, Wave, hologram_intensity,  # noqa: E402
                                    reference_r1_vacuum_plane_wave, vacuum_object_wave)
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier,  # noqa: E402
                                            reconstruct_sideband)

_spec = importlib.util.spec_from_file_location(
    "c2_calc", REPO / "tools" / "reflection_step_phase_calculator.py")
calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calc)

N = 512
FRINGE = 8.0
CHECKS: list[tuple[str, bool]] = []


def rule(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(ok)))
    print(f"   [{'PASS' if ok else 'FAIL'}] {name}" + (f"   ({detail})" if detail else ""))


def delta_T24() -> float:
    d111 = calc.A_SI_A / np.sqrt(3.0)
    return float(calc.SpecularCondition(d111, 6, 200.0, calc.V0_SI_V).step_phase(d111)["wrapped"])


def holograms(dphi: float, dose: float = 0.0, seed: int = 12345, sharp: bool = False):
    """Object and empty holograms exactly as calculator.hologram_roundtrip builds them."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:N, 0:N]
    if sharp:
        soft = (y >= N // 2).astype(float)
    else:
        soft = 0.5 * (1.0 + np.tanh((y - N // 2) / 2.0))
    u_o = np.exp(1j * dphi * soft)
    u_r = np.exp(2j * np.pi * (1.0 / FRINGE) * x)
    I_obj = np.abs(u_o + u_r) ** 2
    I_ref = np.abs(1.0 + u_r) ** 2
    if dose > 0:
        I_obj = rng.poisson(I_obj / I_obj.mean() * dose).astype(float)
        I_ref = rng.poisson(I_ref / I_ref.mean() * dose).astype(float)
    return I_obj, I_ref


def measure(phase: np.ndarray, R_ap: float) -> float:
    """The calculator's step estimate (median of terrace interiors, pad = 3 resolutions)."""
    edge = N // 2
    res_px = 1.0 / max(R_ap, 1e-12)
    pad = int(min(max(3.0 * res_px, 8), N // 4 - 1))
    lo = phase[pad:edge - pad, pad:N - pad]
    hi = phase[edge + pad:N - pad, pad:N - pad]
    return float(calc.wrap_to_pi(np.median(hi) - np.median(lo)))


def demod_step(I_obj, pk, I_ref=None):
    """Demodulate at fftshifted bin pk (calculator _sideband_wave), optionally divide by the empty
    hologram demodulated at the SAME bin, and measure the step."""
    rec, _, R_ap = calc._sideband_wave(I_obj, peak_idx=pk)
    if I_ref is not None:
        rec_ref, _, _ = calc._sideband_wave(I_ref, peak_idx=pk)
        rec = rec / rec_ref
    return measure(np.angle(rec), R_ap)


def section_A(D: float):
    rule("A. THE CALCULATOR'S OWN PEAK SEARCH ON THE T24 OBJECT HOLOGRAM (calculator functions)")
    out = {}
    for dose in (0.0, 1.0e4):
        I_obj, I_ref = holograms(D, dose)
        F = np.fft.fftshift(np.fft.fft2(I_obj))
        mag = np.abs(F)
        c = N // 2

        def m(ky, kx):
            return float(mag[c + ky, c + kx])

        _, pk, _ = calc._sideband_wave(I_obj)
        _, pk_ref, _ = calc._sideband_wave(I_ref)
        ky, kx = int(pk[0]) - c, int(pk[1]) - c
        print(f"\n   dose = {dose:g} e/px (seed 12345 when > 0)")
        print(f"   |F| at the carrier bins (k_y, k_x) = (0, -64): {m(0, -64):.6e}   (0, +64): {m(0, 64):.6e}")
        for (a, b) in ((-1, 64), (1, -64), (1, 64), (-1, -64)):
            print(f"   |F| at first-harmonic bin ({a:+d}, {b:+d}) [fftshifted ({c + a}, {c + b})]: "
                  f"{m(a, b):.9e}")
        herm1 = abs(m(-1, 64) - m(1, -64)) / m(-1, 64)
        herm2 = abs(m(1, 64) - m(-1, -64)) / m(1, 64)
        within = (m(-1, 64) - m(1, 64)) / m(-1, 64)
        print(f"   Hermitian pairs: rel. |F(-1,+64)| - |F(+1,-64)| = {herm1:.1e};  "
              f"|F(+1,+64)| - |F(-1,-64)| = {herm2:.1e}")
        print(f"   within-sideband asymmetry (|F(-1,+64)| - |F(+1,+64)|)/|F(-1,+64)| = {within:+.3e}")
        print(f"   calculator brightest object bin (fftshifted): {tuple(int(v) for v in pk)} -> "
              f"(k_y, k_x) = ({ky:+d}, {kx:+d}): {'CONJUGATE sideband (+q_c)' if kx > 0 else 'correct sideband (-q_c)'}"
              f", {abs(ky)} row(s) off the carrier")
        print(f"   calculator brightest EMPTY-hologram bin: {tuple(int(v) for v in pk_ref)}")
        wrong = demod_step(I_obj, pk)
        partner = demod_step(I_obj, (c - ky, c - kx))
        wrong_div = demod_step(I_obj, pk, I_ref)
        conj_carrier = demod_step(I_obj, (c, c + 64), I_ref)
        right = demod_step(I_obj, (c, c - 64), I_ref)
        ramp_only = demod_step(I_obj, (c + 1, c - 64), None)
        ramp_only2 = demod_step(I_obj, (c - 1, c - 64), None)
        print(f"   recentre on the brightest object bin, no division (the first version):  step = {wrong:+.4f} rad")
        print(f"   its Hermitian partner ({c - ky}, {c - kx}), no division:                   step = {partner:+.4f} rad")
        print(f"   brightest object bin, object/empty both demodulated there:           step = {wrong_div:+.4f} rad")
        print(f"   conjugate sideband at the true carrier (256, 320), divided:          step = {conj_carrier:+.4f} rad")
        print(f"   correct sideband one row off, (257, 192) / (255, 192), no division:  step = {ramp_only:+.4f} / "
              f"{ramp_only2:+.4f} rad")
        print(f"   correct path: carrier (256, 192) from the empty hologram, divided:   step = {right:+.4f} rad")
        print(f"   -Delta + pi = {calc.wrap_to_pi(-D + np.pi):+.4f} rad;  Delta - pi = "
              f"{calc.wrap_to_pi(D - np.pi):+.4f} rad;  Delta = {D:+.4f} rad")
        out[dose] = dict(pk=tuple(int(v) for v in pk), pk_ref=tuple(int(v) for v in pk_ref),
                         herm=max(herm1, herm2), within=within, wrong=wrong, partner=partner,
                         wrong_div=wrong_div, conj=conj_carrier, right=right, ramp=(ramp_only, ramp_only2),
                         ratio=m(-1, 64) / m(0, 64))
    r0 = out[0.0]
    check("Q2-A1 calculator brightest object bin is fftshifted (255, 320) = (k_y, k_x) = (-1, +64): "
          "conjugate sideband, one row off (noiseless and dose 1e4)",
          out[0.0]["pk"] == (255, 320) and out[1.0e4]["pk"] == (255, 320))
    check("Q2-A2 empty hologram gives the true carrier of the correct sideband, (256, 192)",
          out[0.0]["pk_ref"] == (256, 192) and out[1.0e4]["pk_ref"] == (256, 192))
    check("Q2-A3 the brightest bin and its Hermitian partner have equal |F| (rel. 1e-12), for the "
          "noiseless and the noisy hologram", out[0.0]["herm"] < 1e-12 and out[1.0e4]["herm"] < 1e-12,
          f"{out[0.0]['herm']:.1e}, {out[1.0e4]['herm']:.1e}")
    check("Q2-A4 recentring on it without division gives +0.78 (printed digits, tol 0.005) = -Delta + pi "
          "(tol 1e-3)", abs(r0["wrong"] - 0.78) <= 0.005
          and abs(r0["wrong"] - calc.wrap_to_pi(-D + np.pi)) <= 1e-3, f"{r0['wrong']:+.4f}")
    check("Q2-A5 the same with dose 1e4, seed 12345 (tol 1e-3 to -Delta + pi)",
          abs(out[1.0e4]["wrong"] - calc.wrap_to_pi(-D + np.pi)) <= 1e-3, f"{out[1.0e4]['wrong']:+.4f}")
    check("Q2-A6 the Hermitian partner gives -0.78 = Delta - pi (tol 1e-3)",
          abs(r0["partner"] - calc.wrap_to_pi(D - np.pi)) <= 1e-3, f"{r0['partner']:+.4f}")
    check("Q2-A7 dividing by the empty hologram demodulated at the same wrong bin removes the ramp and "
          "leaves the conjugate sign: -Delta (T24 tol 5e-3)", abs(r0["wrong_div"] + D) <= 5e-3,
          f"{r0['wrong_div']:+.4f}")
    check("Q2-A8 the ramp alone (correct sideband, one row off, either direction) gives Delta - pi = -0.78: "
          "the + sign of the printed 0.78 identifies the conjugate sideband",
          all(abs(v - calc.wrap_to_pi(D - np.pi)) <= 1e-3 for v in r0["ramp"]),
          f"{r0['ramp'][0]:+.4f}, {r0['ramp'][1]:+.4f}")
    check("Q2-A9 correct path (carrier from the empty hologram, division) recovers Delta (T24 tol 5e-3)",
          abs(r0["right"] - D) <= 5e-3 and abs(out[1.0e4]["right"] - D) <= 5e-3)
    # the ramp term: a one-bin offset along axis 0 multiplies the demodulated wave by exp(+-2 pi i y/N);
    # the step estimate compares the medians of the two terrace interiors
    R_ap = (1.0 / FRINGE) / 3.0
    pad = int(min(max(3.0 / R_ap, 8), N // 4 - 1))
    rows_lo = np.arange(pad, N // 2 - pad)
    rows_hi = np.arange(N // 2 + pad, N - pad)
    sep = float(np.median(rows_hi) - np.median(rows_lo))
    ramp = 2.0 * np.pi * sep / N
    print(f"\n   ramp term: pad = {pad} px; median rows of the terrace interiors {np.median(rows_lo):.1f} and "
          f"{np.median(rows_hi):.1f} (separation {sep:.0f} rows); one-bin ramp 2 pi/{N} rad per row -> "
          f"{ramp:.6f} rad between the medians (pi = {np.pi:.6f})")
    check("Q2-A10 the one-bin ramp is worth exactly pi between the terrace medians (1e-12)",
          abs(ramp - np.pi) < 1e-12)
    return out


def section_B(D: float, outA):
    rule("B. WHY THAT BIN: HARMONIC VERSUS CARRIER, AND WHICH PAIR WINS")
    ratio_an = (2.0 / np.pi) * abs(np.tan(D / 2.0))
    print(f"   sharp 50/50 model: |first harmonic| / |carrier| = (2/pi) |tan(Delta/2)| = {ratio_an:.4f}; "
          f"calculator hologram (tanh edge): {outA[0.0]['ratio']:.4f}")
    check("Q2-B1 the first harmonic outshines the carrier; ratio within 1 % of (2/pi)|tan(Delta/2)|",
          outA[0.0]["ratio"] > 1.0 and abs(outA[0.0]["ratio"] / ratio_an - 1.0) < 0.01)
    # the four first-harmonic bins tie for a sharp step; the tanh edge splits them into two pairs
    I_sharp, _ = holograms(D, sharp=True)
    F = np.abs(np.fft.fftshift(np.fft.fft2(I_sharp)))
    c = N // 2
    four = np.array([F[c - 1, c + 64], F[c + 1, c - 64], F[c + 1, c + 64], F[c - 1, c - 64]])
    spread = float((four.max() - four.min()) / four.max())
    _, pk_sharp, _ = calc._sideband_wave(I_sharp)
    print(f"   sharp step: the four first-harmonic |F| = {four.tolist()}; relative spread {spread:.1e}; "
          f"calculator picks {tuple(int(v) for v in pk_sharp)}")
    print(f"   tanh edge: within-sideband asymmetry {outA[0.0]['within']:+.3e} decides WHICH Hermitian pair is "
          f"brightest; argmax order then decides WHICH MEMBER of that exactly tied pair is returned")
    check("Q2-B2 sharp 50/50 step: the four first-harmonic bins tie to 1e-9 (relative)", spread < 1e-9,
          f"{spread:.1e}")
    check("Q2-B3 tanh edge: the pair {(-1,+64), (+1,-64)} is brighter than {(+1,+64), (-1,-64)}",
          outA[0.0]["within"] > 0)
    # tie-break: fftshift (centred) order versus numpy's unshifted order
    I_obj, _ = holograms(D)
    Fu = np.abs(np.fft.fft2(I_obj))
    Fu[np.hypot(*np.meshgrid(np.fft.fftfreq(N), np.fft.fftfreq(N), indexing="ij")) < 0.05] = 0.0
    ku = np.unravel_index(int(np.argmax(Fu)), Fu.shape)
    print(f"   argmax in numpy's unshifted order picks unshifted bin {tuple(int(v) for v in ku)} = (k_y, k_x) = "
          f"({int(ku[0]) if ku[0] < N // 2 else int(ku[0]) - N:+d}, {int(ku[1]) if ku[1] < N // 2 else int(ku[1]) - N:+d}); "
          f"the calculator (fftshifted order) picks (255, 320) = (-1, +64)")
    check("Q2-B4 unshifted-order argmax returns the other member (1, 448) = (+1, -64): the sign of the "
          "0.78 is a tie-break outcome", tuple(int(v) for v in ku) == (1, 448))


def section_C():
    rule("C. THRESHOLD: FOR WHICH 50/50 STEPS IS THE BRIGHTEST OBJECT BIN NOT THE CARRIER?")
    thr = 2.0 * np.arctan(np.pi / 2.0)
    print(f"   sharp-step prediction: |Delta| > 2 arctan(pi/2) = {thr:.4f} rad (and < 2 pi - that = "
          f"{2 * np.pi - thr:.4f} rad)")
    ok = True
    ok_model = True
    R_ap = (1.0 / FRINGE) / 3.0
    pad = int(min(max(3.0 / R_ap, 8), N // 4 - 1))
    y_lo = np.arange(pad, N // 2 - pad).astype(float)
    y_hi = np.arange(N // 2 + pad, N - pad).astype(float)
    for D in (1.0, 1.9, 1.98, 2.04, 2.1, 2.3596, 3.0, 3.9236, -1.5640, -2.3596):
        I_obj, _ = holograms(D)
        _, pk, _ = calc._sideband_wave(I_obj)
        ky, kx = int(pk[0]) - N // 2, int(pk[1]) - N // 2
        Dw = float(calc.wrap_to_pi(D))
        predicted_off = abs(Dw) > thr
        is_off = ky != 0
        step = demod_step(I_obj, pk)
        # interior model: sigma * D * s + rho * 2 pi y / N (sigma = -1 on the conjugate sideband,
        # rho = -k_y), valid when neither terrace window wraps
        sig = -1.0 if kx > 0 else 1.0
        rho = -float(ky)
        lo = rho * 2 * np.pi * y_lo / N
        hi = sig * D + rho * 2 * np.pi * y_hi / N
        wraps = bool(np.any(np.abs(calc.wrap_to_pi(lo) - lo) > 1e-12) or
                     np.any(np.abs(calc.wrap_to_pi(hi) - hi) > 1e-12) or
                     np.ptp(calc.wrap_to_pi(hi)) > np.pi or np.ptp(calc.wrap_to_pi(lo)) > np.pi)
        pred = float(calc.wrap_to_pi(sig * D + rho * np.pi))
        note = ("model sigma*Delta + rho*pi = %+.4f" % pred) if not wraps else \
            "ramp wraps inside a terrace window: the median is corrupted"
        print(f"   Delta = {D:+.4f} (wrapped {Dw:+.4f}): brightest bin (k_y, k_x) = ({ky:+d}, {kx:+d}) "
              f"{'OFF carrier' if is_off else 'carrier'} (predicted {'OFF' if predicted_off else 'carrier'}); "
              f"naive step {step:+.4f} rad; {note if is_off else 'no ramp'}")
        ok &= (predicted_off == is_off)
        if is_off and not wraps:
            ok_model &= abs(step - pred) <= 1e-3
    check("Q2-C1 the brightest object bin leaves the carrier exactly when |Delta| > 2 arctan(pi/2) "
          "(values 0.03 rad or more from the threshold)", ok)
    check("Q2-C2 off-carrier cases without wrapping follow sigma*Delta + rho*pi (sideband sign sigma, "
          "ramp sign rho) to 1e-3", ok_model)


def section_D(D: float):
    rule("D. THE PACKAGE CHAIN (reflection_holo.optics + reconstruction) ON THE SAME HOLOGRAMS")
    grid = Grid(shape=(N, N), pixel_size_A=(1.0, 1.0), axes=("y", "x"),
                plane="image plane, specimen coordinates (TEST_ONLY synthetic, C2)")
    y = np.arange(N, dtype=float)[:, None] * np.ones((1, N))
    soft = 0.5 * (1.0 + np.tanh((y - N // 2) / 2.0))
    obj = Wave(np.exp(1j * D * soft), grid, "two terraces (calculator section 12)", None)
    art = ArtefactOptions(biprism_fresnel_fringes=None, drift=None, charging_phase_rad=None)
    ref = reference_r1_vacuum_plane_wave(grid, carrier_cycles_per_A=(0.0, 1.0 / FRINGE), amplitude=1.0,
                                         relative_phase_rad=0.0, aperture_passage="no_aperture",
                                         realisation=None)
    H_obj = hologram_intensity(obj, ref, artefacts=art, content="object")
    H_emp = hologram_intensity(vacuum_object_wave(grid, amplitude=1.0, realisation=None), ref,
                               artefacts=art, content="empty")
    I_obj_calc, _ = holograms(D)
    same = float(np.max(np.abs(H_obj.intensity - I_obj_calc)))
    print(f"   package object hologram vs calculator's: max |difference| = {same:.1e}")
    check("Q2-D1 the package forms the calculator's hologram (1e-12)", same < 1e-12)
    # S3 (audit A2 M1): the package refuses a search region holding both sidebands, so the trap bin is
    # reached by declaring the conjugate half plane (+q_c) on purpose; it is the whole-plane brightest
    # bin, as the comparison with the calculator's own whole-plane search (255, 320) below shows.
    conj_side = CarrierSearch(sideband_guess_cycles_per_A=(0.0, 1.0 / FRINGE), search_radius_cycles_per_A=0.0625,
                              exclusion_radius_cycles_per_A=0.05, subpixel="none",
                              sideband_declaration="demonstration: the conjugate sideband (+q_c) declared on purpose")
    car0 = locate_carrier(H_obj, conj_side, allow_object_hologram=True)
    m0 = MaskSpec(radius_cycles_per_A=car0.carrier_magnitude_cycles_per_A / 3.0, shape="disc", apodisation="hann")
    r0 = reconstruct_sideband(H_obj, carrier=car0, mask=m0, empty_hologram=None, reference_correction="none",
                              unwrapping="none", trap_demonstration=True, object_min_visibility=0.05)
    rec_c, _, R_c = calc._sideband_wave(I_obj_calc, peak_idx=(255, 320))
    dmax = float(np.max(np.abs(np.angle(np.exp(1j * (r0.wrapped_phase - np.angle(rec_c)))))))
    print(f"   package phase map at bin (511, 64) vs calculator _sideband_wave at (255, 320): max |difference| = "
          f"{dmax:.1e} rad (mask radius {m0.radius_cycles_per_A:.6f} vs {R_c:.6f} cycles/px)")
    check("Q2-D1b package demodulation at the trap bin equals the calculator's (1e-12 rad)", dmax < 1e-12)

    def run(search, empty=None, allow=False):
        car = locate_carrier(H_obj if empty is None or allow else H_emp, search, allow_object_hologram=allow)
        mask = MaskSpec(radius_cycles_per_A=car.carrier_magnitude_cycles_per_A / 3.0, shape="disc",
                        apodisation="hann")
        res = reconstruct_sideband(H_obj, carrier=car, mask=mask,
                                   empty_hologram=H_emp if empty == "divide" else None,
                                   reference_correction="divide_empty" if empty == "divide" else "none",
                                   unwrapping="none", trap_demonstration=allow,
                                   empty_min_visibility=0.5 if empty == "divide" else None,
                                   object_min_visibility=None if empty == "divide" else 0.05)
        return car, res, measure(res.wrapped_phase, mask.radius_cycles_per_A)   # R in cycles/px (1 A px)

    try:
        CarrierSearch(sideband_guess_cycles_per_A=(0.0, -1.0 / FRINGE), search_radius_cycles_per_A=np.inf,
                      exclusion_radius_cycles_per_A=0.05, subpixel="none",
                      sideband_declaration="whole plane (refused)")
        whole_refused = False
    except ValueError:
        whole_refused = True
    print(f"   the package refuses a whole-plane search (both sidebands, audit A2 M1): {whole_refused}")
    car, res, st = run(conj_side, allow=True)
    print(f"   conjugate half plane declared on purpose, on the OBJECT hologram (demonstration only): bin "
          f"{car.integer_bin}, {res.sideband_sign_check}; step {st:+.4f} rad")
    ok1 = car.integer_bin == (511, 64) and abs(st - calc.wrap_to_pi(-D + np.pi)) <= 1e-3
    right_side = CarrierSearch(sideband_guess_cycles_per_A=(0.0, -1.0 / FRINGE), search_radius_cycles_per_A=0.0625,
                               exclusion_radius_cycles_per_A=0.05, subpixel="none",
                               sideband_declaration="simulation: -q_c of the declared R1 reference")
    car2, res2, st2 = run(right_side, allow=True)
    print(f"   search restricted to the correct sideband, on the OBJECT hologram: bin {car2.integer_bin}, "
          f"{res2.sideband_sign_check}; step {st2:+.4f} rad")
    ok2 = car2.integer_bin == (1, 448) and abs(st2 - calc.wrap_to_pi(D - np.pi)) <= 1e-3
    car3 = locate_carrier(H_emp, right_side)
    mask3 = MaskSpec(radius_cycles_per_A=car3.carrier_magnitude_cycles_per_A / 3.0, shape="disc",
                     apodisation="hann")
    res3 = reconstruct_sideband(H_obj, carrier=car3, mask=mask3, empty_hologram=H_emp,
                                reference_correction="divide_empty", unwrapping="none",
                                empty_min_visibility=0.5)   # S3: declared (A2 m1, A2b N6)
    st3 = measure(res3.wrapped_phase, mask3.radius_cycles_per_A)
    print(f"   carrier located on the EMPTY hologram (correct sideband), divided: bin {car3.integer_bin}, "
          f"{res3.sideband_sign_check}; step {st3:+.4f} rad")
    try:
        locate_carrier(H_obj, conj_side)
        refused = False
    except ValueError:
        refused = True
    print(f"   the package refuses an object hologram by default: {refused}")
    check("Q2-D2 package: whole-plane search refused; the conjugate half plane on the object hologram gives "
          "unshifted bin (511, 64) = fftshifted (255, 320), flagged CONJUGATE, step -Delta + pi",
          whole_refused and ok1 and res.sideband_sign_check.startswith("CONJUGATE"))
    check("Q2-D3 package search restricted to the correct sideband still fails on the object hologram: "
          "(1, 448), step Delta - pi", ok2)
    check("Q2-D4 package correct path recovers Delta (T24 tol 5e-3) and refuses object holograms by default",
          abs(st3 - D) <= 5e-3 and refused)


def main() -> int:
    D = delta_T24()
    print(f"Delta (T24) = sc666.step_phase(d111)['wrapped'] = {D:.6f} rad")
    outA = section_A(D)
    section_B(D, outA)
    section_C()
    section_D(D)
    rule("SUMMARY")
    n_ok = sum(ok for _, ok in CHECKS)
    print(f"   {n_ok}/{len(CHECKS)} self-checks pass")
    for name, ok in CHECKS:
        if not ok:
            print(f"   FAILED: {name}")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
