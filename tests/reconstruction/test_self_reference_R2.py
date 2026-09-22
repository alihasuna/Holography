"""R2 self-reference: the documented twin (docs/03 section 6; SM22, the R2 reading is DERIVED_HERE).

Model: u_r(r) = u_o(r + s) exp(2 pi i q_c.r). The reconstruction returns phi(r) - phi(r + s), so every
object feature appears at its own position and, sign-inverted, displaced by -s (the twin of the
reference region). The twin is TRANSLATED, not spatially inverted: an asymmetric pair of bumps keeps
its order in the twin. Synthetic case (TEST_ONLY): n = 512, pixel 1 A, carrier (0, 1/8) cycles/A,
shift (0, 128) A, Gaussian phase bumps (sigma 16 A) of 0.8 and 0.4 rad, Hann mask |q_c|/3.

Tolerance 1e-3 rad for the comparison with the mask-filtered ideal phi(r) - phi(r + s) inside the
region at least three resolution lengths (72 px) from the field edge and from the edge of the
reference's valid region (the residual is leakage of the centre band; 1e-4 rad was measured).
"""
import numpy as np
import pytest

from holo_cases import NO_ARTEFACTS, SIM_SIDEBAND, make_grid
from reflection_holo.optics import Wave, hologram_intensity, reference_r2_self_reference
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier, reconstruct_sideband,
                                            wrap_to_pi)

N = 512
SHIFT = (0.0, 128.0)
Q = (0.0, 1.0 / 8.0)
P1 = (256.0, 240.0)
P2 = (256.0, 270.0)
TOL = 1e-3


def _bumps(grid):
    r0, r1 = grid.coordinates_A()
    g = lambda p, a: a * np.exp(-((r0 - p[0]) ** 2 + (r1 - p[1]) ** 2) / (2 * 16.0 ** 2))  # noqa: E731
    return g(P1, 0.8) + g(P2, 0.4)


def _reconstruct():
    grid = make_grid(N)
    phi = _bumps(grid)
    u_o = Wave(np.exp(1j * phi), grid, "object with two bumps", None)
    u_flat = Wave(np.ones(grid.shape), grid, "flat region", None)
    kw = dict(shift_A=SHIFT, carrier_cycles_per_A=Q, amplitude_scale=1.0, relative_phase_rad=0.0)
    ref = reference_r2_self_reference(u_o, **kw)
    ref_flat = reference_r2_self_reference(u_flat, **kw)
    H = hologram_intensity(u_o, ref, artefacts=NO_ARTEFACTS, content="object")
    H_flat = hologram_intensity(u_flat, ref_flat, artefacts=NO_ARTEFACTS, content="flat_region")
    carrier = locate_carrier(H_flat, CarrierSearch((-Q[0], -Q[1]), 0.5 * Q[1], 0.05, "none", SIM_SIDEBAND))
    mask = MaskSpec(carrier.carrier_magnitude_cycles_per_A / 3.0, "disc", "hann")
    res = reconstruct_sideband(H, carrier=carrier, mask=mask, empty_hologram=None,
                               reference_correction="none", unwrapping="none")
    return grid, phi, ref, res


def test_r2_result_is_phi_r_minus_phi_r_plus_s():
    grid, phi, ref, res = _reconstruct()
    valid = ref.metadata["valid_mask"]
    assert valid[:, :N - 128].all() and not valid[:, N - 128:].any()
    shifted = np.zeros_like(phi)
    shifted[:, :N - 128] = phi[:, 128:]
    ideal = np.where(valid, np.exp(1j * (phi - shifted)), 0.0)
    W_dc = np.roll(res.mask, (0, 64), axis=(0, 1))           # the same mask centred on q = 0
    band_limited = np.angle(np.fft.ifft2(np.fft.fft2(ideal) * W_dc))
    interior = np.zeros(grid.shape, bool)
    interior[72:N - 72, 72:N - 128 - 72] = True
    assert np.max(np.abs(wrap_to_pi(res.wrapped_phase - band_limited))[interior]) <= TOL


def test_r2_twin_is_sign_inverted_and_translated_by_minus_shift():
    grid, phi, ref, res = _reconstruct()
    ph = res.wrapped_phase
    i = int(P1[0])
    a1, a2 = int(P1[1]), int(P2[1])
    t1, t2 = a1 - int(SHIFT[1]), a2 - int(SHIFT[1])
    # the features themselves (band-limited by the Hann mask) are clearly visible
    assert ph[i, a1] > 0.5 and ph[i, a2] > 0.2
    # the twin: same pattern, opposite sign, displaced by -s, same order (not mirrored in space)
    assert abs(ph[i, t1] + ph[i, a1]) <= TOL
    assert abs(ph[i, t2] + ph[i, a2]) <= TOL
    # window +-20 px beyond the bumps: there the model's twin + feature = phi(r - s) - phi(r + s) is
    # below 1e-5 rad (Gaussian tails at >= 78 px), so the sum must vanish to the stated tolerance
    profile = ph[i, a1 - 20:a2 + 21]
    twin = ph[i, t1 - 20:t2 + 21]
    assert np.max(np.abs(twin + profile)) <= TOL
    assert np.max(np.abs(twin + profile[::-1])) > 0.1       # a spatial mirror would not match
    # away from features and twins the phase is flat (common-mode phases cancel)
    assert abs(ph[100, 250]) <= TOL


STEP = 1.2               # Delta = phi(upper) - phi(lower), rad (E4 M3 used +1.2 rad)
STEP_ROW = 256           # rows >= 256 are the upper terrace: step normal n = +axis 0


@pytest.mark.parametrize("shift", [(96.0, 0.0), (-96.0, 0.0), (96.0, 40.0), (-96.0, 40.0)])
def test_r2_step_strip_sign_and_width(shift):
    """Review E4 M3: with phi = Delta H(n.r - c), the R2 result phi(r) - phi(r + s) shows the step as
    a strip of width |n.s| and phase -sign(n.s) Delta: -Delta when s points towards the upper
    terrace, +Delta when it points towards the lower one (the documented "-Delta" held for one sign
    only). A shift component along the edge does not change the strip. Tolerances: the plateau is
    compared with the mask-filtered ideal phi(r) - phi(r + s) within this module's TOL (1e-3 rad) at
    least 30 px (1.25 resolution lengths) inside the strip; the strip width is the distance between
    the half-level crossings of the profile, equal to |n.s| within 1 px (both edges are blurred by the
    same filter)."""
    grid = make_grid(N)
    r0, _ = grid.coordinates_A()
    phi = STEP * (r0 >= STEP_ROW)
    u_o = Wave(np.exp(1j * phi), grid, "one step, upper terrace at rows >= 256", None)
    u_f = Wave(np.ones(grid.shape), grid, "flat region", None)
    kw = dict(shift_A=shift, carrier_cycles_per_A=Q, amplitude_scale=1.0, relative_phase_rad=0.0)
    H = hologram_intensity(u_o, reference_r2_self_reference(u_o, **kw), artefacts=NO_ARTEFACTS,
                           content="object")
    H_f = hologram_intensity(u_f, reference_r2_self_reference(u_f, **kw), artefacts=NO_ARTEFACTS,
                             content="flat_region")
    carrier = locate_carrier(H_f, CarrierSearch((-Q[0], -Q[1]), 0.5 * Q[1], 0.05, "none", SIM_SIDEBAND))
    res = reconstruct_sideband(H, carrier=carrier, mask=MaskSpec(Q[1] / 3.0, "disc", "hann"),
                               empty_hologram=None, reference_correction="none", unwrapping="none")
    s_n = int(shift[0])                                     # n.s, n = +axis 0 (towards the upper terrace)
    lo, hi = (STEP_ROW - s_n, STEP_ROW) if s_n > 0 else (STEP_ROW, STEP_ROW - s_n)
    want = -np.sign(s_n) * STEP
    cols = slice(150, 350)
    plateau = res.wrapped_phase[lo + 30:hi - 30, cols]
    assert np.max(np.abs(plateau - want)) <= 0.05            # sign and size of the strip
    # the band-limited ideal: mask-filtered exp(i (phi(r) - phi(r + s))) on the valid region
    valid = res.valid_mask
    shifted = np.zeros_like(phi)
    s0, s1 = int(shift[0]), int(shift[1])
    d0 = slice(max(0, -s0), min(N, N - s0))
    d1 = slice(max(0, -s1), min(N, N - s1))
    shifted[d0, d1] = phi[d0.start + s0:d0.stop + s0, d1.start + s1:d1.stop + s1]
    ideal = np.where(valid, np.exp(1j * (phi - shifted)), 0.0)
    c = res.carrier.integer_bin
    W_dc = np.roll(res.mask, (-c[0], -c[1]), axis=(0, 1))
    band_limited = np.angle(np.fft.ifft2(np.fft.fft2(ideal) * W_dc))
    assert np.max(np.abs(wrap_to_pi(res.wrapped_phase - band_limited)[lo + 30:hi - 30, cols])) <= TOL
    # width from the half-level crossings of the column-averaged profile
    prof = np.median(res.wrapped_phase[:, cols], axis=1) / want
    x = np.arange(N)
    up = np.flatnonzero((prof[:-1] < 0.5) & (prof[1:] >= 0.5))
    dn = np.flatnonzero((prof[:-1] >= 0.5) & (prof[1:] < 0.5))
    a = up[np.argmin(np.abs(up - lo))]
    b = dn[np.argmin(np.abs(dn - hi))]
    xa = x[a] + (0.5 - prof[a]) / (prof[a + 1] - prof[a])
    xb = x[b] + (0.5 - prof[b]) / (prof[b + 1] - prof[b])
    assert abs((xb - xa) - abs(s_n)) <= 1.0
