#!/usr/bin/env python3
r"""
C2 question 3: what an R2 (object overlapped with the shifted object) reconstruction returns.

Run:  venv/bin/python tools/physics_checks/q3_r2_twin.py
Exit status 0 only if every self-check passes.  Report: docs/agent_reports/C2_phase2_physics_checks.md

Model (reflection_holo.optics.hologram.reference_r2_self_reference; ASSUMPTION B5, R2 reading
DERIVED_HERE, SM22): u_r(r) = c u_o(r + s) exp(i (2 pi q_c.r + phi_rel)), s = the package's
``shift_A`` (integer pixels, no wrap; pixels whose source r + s lies outside the field are invalid).
Conventions: exp(+i k.r); numpy FFT sign, so u_o u_r^* appears at -q_c.

Derivation (DERIVED_HERE):
    I = |u_o|^2 + |u_r|^2 + u_o u_r^* + u_o^* u_r,
    u_o u_r^* = c |u_o(r)| |u_o(r + s)| exp(i [phi(r) - phi(r + s) - phi_rel]) exp(-2 pi i q_c.r),
so the -q_c sideband, demodulated with the carrier of a flat-region hologram, returns
    Phi(r) = phi(r) - phi(r + s) - phi_rel,   amplitude c |u_o(r)| |u_o(r + s)|   (band-limited).
A feature f centred at r0 on a flat background, phi = phi_0 + f(r - r0), gives
    Phi(r) = f(r - r0) - f(r - (r0 - s)) - phi_rel:
the feature at r0 and a copy with the opposite sign at r0 - s, with the SAME orientation (a
translation, not a mirror). Equivalently, with the reference defined as u_o(r - s') (s' = -s),
Phi(r) = phi(r) - phi(r - s') and the twin sits at r0 + s'. The conjugate sideband (+q_c) returns
-Phi. Because the demodulation kernel of a real, even mask is real and even, the band-limited twin
is exactly minus the band-limited feature (up to the tails f(d -+ s)).

Synthetic cases (TEST_ONLY): 512 x 512 px, pixel 1 A on both axes, carrier (0, 1/8) cycles/A, Hann
mask |q_c|/3 (resolution 24 px); interior = at least 72 px (three resolutions) from the field edge
and from the invalid band of the reference.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reflection_holo.optics import (ArtefactOptions, Grid, Wave, hologram_intensity,  # noqa: E402
                                    reference_r2_self_reference)
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier,  # noqa: E402
                                            reconstruct_sideband, wrap_to_pi)

N = 512
Q = (0.0, 1.0 / 8.0)
PAD = 72
CHECKS: list[tuple[str, bool]] = []
ART = ArtefactOptions(biprism_fresnel_fringes=None, drift=None, charging_phase_rad=None)


def rule(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(ok)))
    print(f"   [{'PASS' if ok else 'FAIL'}] {name}" + (f"   ({detail})" if detail else ""))


GRID = Grid(shape=(N, N), pixel_size_A=(1.0, 1.0), axes=("y", "x"),
            plane="image plane, specimen coordinates (TEST_ONLY synthetic, C2)")


def gauss(r0, sig, amp):
    y, x = GRID.coordinates_A()
    return amp * np.exp(-((y - r0[0]) ** 2 + (x - r0[1]) ** 2) / (2.0 * sig ** 2))


def reconstruct(phi: np.ndarray, shift, sideband: str = "correct", phi_rel: float = 0.0):
    """Form the R2 hologram of exp(i phi) with the package and reconstruct one sideband."""
    u_o = Wave(np.exp(1j * phi), GRID, "object", None)
    u_f = Wave(np.ones(GRID.shape), GRID, "flat region", None)
    kw = dict(shift_A=shift, carrier_cycles_per_A=Q, amplitude_scale=1.0, relative_phase_rad=phi_rel)
    ref = reference_r2_self_reference(u_o, **kw)
    ref_f = reference_r2_self_reference(u_f, **kw)
    H = hologram_intensity(u_o, ref, artefacts=ART, content="object")
    H_f = hologram_intensity(u_f, ref_f, artefacts=ART, content="flat_region")
    guess = (-Q[0], -Q[1]) if sideband == "correct" else (Q[0], Q[1])
    decl = ("simulation: -q_ref of the declared R2 reference" if sideband == "correct" else
            "demonstration: the conjugate sideband (+q_ref) declared on purpose")
    car = locate_carrier(H_f, CarrierSearch(guess, 0.5 * Q[1], 0.05, "none", decl))
    mask = MaskSpec(car.carrier_magnitude_cycles_per_A / 3.0, "disc", "hann")
    res = reconstruct_sideband(H, carrier=car, mask=mask, empty_hologram=None,
                               reference_correction="none", unwrapping="none",
                               object_min_visibility=0.05,   # A2c R1: declared minimum
                               trap_demonstration=(sideband != "correct"))  # S3: explicit opt-in
    return res, ref.metadata["valid_mask"], car


def band_limited_prediction(phi: np.ndarray, shift, res, valid) -> np.ndarray:
    """arg of the mask-filtered exp(i [phi(r) - phi(r + s)]) (zero where the reference is invalid)."""
    s0, s1 = int(shift[0]), int(shift[1])
    shifted = np.zeros_like(phi)
    d0 = slice(max(0, -s0), min(N, N - s0))
    d1 = slice(max(0, -s1), min(N, N - s1))
    shifted[d0, d1] = phi[d0.start + s0:d0.stop + s0, d1.start + s1:d1.stop + s1]
    ideal = np.where(valid, np.exp(1j * (phi - shifted)), 0.0)
    c = res.carrier.integer_bin
    W_dc = np.roll(res.mask, (-c[0], -c[1]), axis=(0, 1))       # the same mask centred on q = 0
    return np.angle(np.fft.ifft2(np.fft.fft2(ideal) * W_dc))


def interior(valid: np.ndarray) -> np.ndarray:
    m = np.zeros((N, N), bool)
    m[PAD:N - PAD, PAD:N - PAD] = True
    # at least PAD px from the invalid band of the reference
    inv = ~valid
    grow = inv.copy()
    for ax in (0, 1):
        for k in range(1, PAD + 1):
            grow |= np.roll(inv, k, axis=ax) | np.roll(inv, -k, axis=ax)
    return m & ~grow


def section_A():
    rule("A. ASYMMETRIC FEATURE: RESULT = phi(r) - phi(r + s); TWIN SIGN, SHIFT AND ORIENTATION")
    shift = (40.0, 128.0)
    r0 = (230.0, 300.0)
    phi = gauss(r0, 10.0, 0.8) + gauss((r0[0] + 18.0, r0[1] + 26.0), 10.0, 0.4)   # asymmetric pair
    res, valid, car = reconstruct(phi, shift)
    pred = band_limited_prediction(phi, shift, res, valid)
    inter = interior(valid)
    err = float(np.max(np.abs(wrap_to_pi(res.wrapped_phase - pred))[inter]))
    print(f"   shift s = {shift} px (package: u_r(r) = u_o(r + s) ...); feature at r0 = {r0}; carrier bin "
          f"{car.integer_bin}; {res.sideband_sign_check}")
    print(f"   max |Phi - band-limited [phi(r) - phi(r + s)]| over the interior ({int(inter.sum())} px): "
          f"{err:.2e} rad")
    check("Q3-A1 the reconstruction equals the band-limited phi(r) - phi(r + s) to 1e-3 rad", err <= 1e-3)
    ph = res.wrapped_phase
    h = 40
    i0, j0 = int(r0[0]), int(r0[1])
    t0, t1 = i0 - int(shift[0]), j0 - int(shift[1])
    feat = ph[i0 - h:i0 + h + 1, j0 - h:j0 + h + 1]
    twin = ph[t0 - h:t0 + h + 1, t1 - h:t1 + h + 1]
    tr = float(np.max(np.abs(twin + feat)))
    flip0 = float(np.max(np.abs(twin + feat[::-1, :])))
    flip1 = float(np.max(np.abs(twin + feat[:, ::-1])))
    point = float(np.max(np.abs(twin + feat[::-1, ::-1])))
    plus = float(np.max(np.abs(twin - feat)))
    print(f"   feature peak Phi(r0) = {ph[i0, j0]:+.4f} rad; twin Phi(r0 - s) = {ph[t0, t1]:+.4f} rad at "
          f"r0 - s = ({t0}, {t1})")
    print(f"   81 x 81 px windows: max |twin + feature| (sign-inverted translate) = {tr:.2e};  mirrored "
          f"along axis 0: {flip0:.3f};  along axis 1: {flip1:.3f};  point-inverted: {point:.3f};  "
          f"same sign: {plus:.3f} rad")
    check("Q3-A2 twin = minus the feature, translated by -s (to 1e-3 rad)", tr <= 1e-3)
    check("Q3-A3 twin is NOT a spatial mirror (axis 0, axis 1 or point inversion: all > 0.1 rad) and "
          "NOT same-sign", min(flip0, flip1, point, plus) > 0.1)
    rp = (i0 + int(shift[0]), j0 + int(shift[1]))
    inside = 0 <= rp[0] < N and 0 <= rp[1] < N and bool(valid[rp])
    print(f"   r0 + s = {rp}: {'valid' if inside else 'in the invalid band (its reference source lies outside the field)'}"
          f" -- the direction of the twin is tested with valid r0 + s in section B")
    # conjugate sideband
    res_c, _, car_c = reconstruct(phi, shift, sideband="conjugate")
    dconj = float(np.max(np.abs(wrap_to_pi(res_c.wrapped_phase + res.wrapped_phase))[inter]))
    print(f"   conjugate sideband (+q_c, bin {car_c.integer_bin}, {res_c.sideband_sign_check}): "
          f"max |Phi_conj + Phi| = {dconj:.2e} rad")
    check("Q3-A4 the conjugate sideband returns -Phi = phi(r + s) - phi(r) (1e-9 rad)", dconj <= 1e-9)
    # phi_rel is a constant offset
    res_p, _, _ = reconstruct(phi, shift, phi_rel=0.7)
    doff = float(np.max(np.abs(wrap_to_pi(res_p.wrapped_phase - res.wrapped_phase + 0.7))[inter]))
    print(f"   phi_rel = 0.7 rad: max |Phi(0.7) - Phi(0) + 0.7| over the interior = {doff:.2e} rad (exact in the "
          f"sideband; the residual is centre-band leakage from the reference's valid-mask edge, which does "
          f"not rotate with phi_rel; same level as Q3-A1)")
    check("Q3-A5 the relative phase phi_rel enters as the constant -phi_rel (to the 1e-3 rad leakage "
          "tolerance of Q3-A1)", doff <= 1e-3, f"{doff:.1e}")


def section_B():
    rule("B. THE SAME WITH A DIFFERENT SHIFT (both signs of both components)")
    ok = True
    h = 30
    for shift in ((-40.0, -90.0), (-64.0, 90.0), (64.0, -90.0), (40.0, 90.0)):
        s0, s1 = int(shift[0]), int(shift[1])
        # interior of the valid region (>= PAD px from the field edge and the invalid band)
        lo0, hi0 = max(0, -s0) + PAD, min(N, N - s0) - PAD
        lo1, hi1 = max(0, -s1) + PAD, min(N, N - s1) - PAD
        c0 = (lo0 + abs(s0) + h + hi0 - abs(s0) - h) // 2
        c1 = (lo1 + abs(s1) + h + hi1 - abs(s1) - h) // 2
        r0 = (float(c0 - 9), float(c1 - 13))                 # centre of the asymmetric pair near (c0, c1)
        for q in ((c0 - abs(s0) - h, c1 - abs(s1) - h), (c0 + abs(s0) + h, c1 + abs(s1) + h)):
            assert lo0 <= q[0] < hi0 and lo1 <= q[1] < hi1, "windows leave the valid interior"
        phi = gauss(r0, 10.0, 0.8) + gauss((r0[0] + 18.0, r0[1] + 26.0), 10.0, 0.4)
        res, valid, _ = reconstruct(phi, shift)
        ph = res.wrapped_phase
        i0, j0 = c0, c1
        t0, t1 = i0 - int(shift[0]), j0 - int(shift[1])
        feat = ph[i0 - h:i0 + h + 1, j0 - h:j0 + h + 1]
        twin = ph[t0 - h:t0 + h + 1, t1 - h:t1 + h + 1]
        tr = float(np.max(np.abs(twin + feat)))
        other = ph[i0 + int(shift[0]) - h:i0 + int(shift[0]) + h + 1,
                   j0 + int(shift[1]) - h:j0 + int(shift[1]) + h + 1]
        wrong = float(np.max(np.abs(other + feat)))
        flat = float(np.max(np.abs(other)))
        print(f"   s = {shift}: windows centred on ({i0}, {j0}); twin window at -s ({t0}, {t1}): max |twin + feature| "
              f"= {tr:.2e} rad; window at +s ({i0 + s0}, {j0 + s1}) (valid interior): max |Phi| = {flat:.2e} rad, "
              f"max |Phi + feature| = {wrong:.3f} rad")
        ok &= flat <= 1e-3
        ok &= tr <= 1e-3 and wrong > 0.1
    check("Q3-B1 for every shift the twin sits at r0 - s (package convention), never at r0 + s", ok)


def section_C():
    rule("C. A TERRACE STEP INSIDE THE OVERLAP: STEP AND TWIN STEP")
    shift = (96.0, 40.0)
    Dphi = 1.0
    y, _ = GRID.coordinates_A()
    ys = 300.0
    phi = Dphi * 0.5 * (1.0 + np.tanh((y - ys) / 2.0))
    res, valid, _ = reconstruct(phi, shift)
    ph = res.wrapped_phase
    cols = slice(PAD, N - int(shift[1]) - PAD)
    strip = ph[int(ys - shift[0]) + 24:int(ys) - 24, cols]
    above = ph[PAD:int(ys - shift[0]) - 24, cols]
    below = ph[int(ys) + 24:N - int(shift[0]) - PAD, cols]
    print(f"   step of {Dphi} rad at row {ys:.0f} (phase {Dphi} rad for rows > {ys:.0f}); s = {shift} px")
    print(f"   rows {int(ys - shift[0]) + 24}..{int(ys) - 24} (between twin step and step): median Phi = "
          f"{np.median(strip):+.4f} rad; rows {PAD}..{int(ys - shift[0]) - 24}: {np.median(above):+.4f}; "
          f"rows {int(ys) + 24}..{N - int(shift[0]) - PAD}: {np.median(below):+.4f}")
    check("Q3-C1 a step Delta at y_s appears as a strip of phase -Delta between the twin step at "
          "y_s - s_y and the step at y_s (1e-3 rad); 0 outside",
          abs(np.median(strip) + Dphi) <= 1e-3 and abs(np.median(above)) <= 1e-3
          and abs(np.median(below)) <= 1e-3)


def main() -> int:
    section_A()
    section_B()
    section_C()
    rule("SUMMARY")
    n_ok = sum(ok for _, ok in CHECKS)
    print(f"   {n_ok}/{len(CHECKS)} self-checks pass")
    for name, ok in CHECKS:
        if not ok:
            print(f"   FAILED: {name}")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
