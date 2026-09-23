"""Test gaps of docs/05 section 8 named by audit A2 finding m9: measured reconstruction resolution
versus mask radius, and ensemble convergence with the number of realisations.

1. Resolution. A small phase step (0.05 rad, so the phase is linear in the wave to 2.5e-3 relative)
   along axis 0, R1 reference with carrier (0, 1/8) cycles/px, 1024 x 64 px, pixel 1 A (TEST_ONLY),
   no noise. The 10-90 % width of the reconstructed step is MEASURED for mask radii R = |q|/3, /4, /6
   and /8 and both apodisations, and compared with an INDEPENDENT prediction: for a function of r0
   only, the disc mask acts as its 1-D profile W(q0) (DERIVED_HERE), so the step response is
   1/2 + (1/pi) int_0^R W(f) sin(2 pi f y)/f df: width = c/R with c = 2 x/(2 pi), Si(x) = 0.4 pi, for
   the top-hat (c = 0.44582) and c = 0.97027 for the Hann window (both computed here by numpy
   quadrature). Tolerance, stated a priori: the top-hat cutoff is quantised by one frequency bin
   1/n, so |width R / c - 1| <= 1/(n R - 1) + 2.5e-3 (the bound is applied to both windows).
   The reported resolution 1/R is at least the measured width for both windows.
2. Ensemble convergence. K realisations of a reference phase jitter delta_k ~ N(0, s^2), s = 0.8
   rad, plus a phase psi_k ~ U(0, 2 pi) COMMON to object and reference (as a source-position
   ensemble gives), object and reference sharing each realisation (SM13), averaged after squaring;
   one generator, seed 20260922. The common phase cancels in each |u_o + u_r|^2; an average of
   complex waves would instead multiply the sideband by |<exp(i psi)>|^2 -> 0. The sideband of the
   average is |<exp(-i delta)>_K| exp(i (phi_o - phi_r + arg<exp(-i delta)>_K)); its contrast must
   approach exp(-s^2/2) and its phase phi_o - phi_r = 0.5 rad as K grows: at K = 4, 16, 64, 256
   and 1024 the contrast error is within 4 standard errors (1 - exp(-s^2))/sqrt(2K) plus the bias
   (1 - exp(-2 s^2))/(4 K exp(-s^2/2)), and the phase error within
   4 sqrt((1 - exp(-2 s^2))/(2K)) / exp(-s^2/2) (DERIVED_HERE, delta method).
"""
import math

import numpy as np
import pytest

from holo_cases import SIM_SIDEBAND
from reflection_holo.optics import (ArtefactOptions, Grid, Wave, ensemble_hologram_intensity,
                                    hologram_intensity, reference_r1_vacuum_plane_wave,
                                    vacuum_object_wave)
from reflection_holo.reconstruction import CarrierSearch, MaskSpec, locate_carrier, reconstruct_sideband

NA = ArtefactOptions(None, None, None)
Q = (0.0, 0.125)


def _step_response_constant(window: str) -> float:
    """10-90 % width x R of the 1-D step response of W(f/R) (numpy quadrature and bisection)."""
    f = np.linspace(1e-9, 1.0, 200001)
    W = np.ones_like(f) if window == "none" else 0.5 * (1.0 + np.cos(np.pi * f))

    def s(y):
        return 0.5 + np.trapezoid(W * np.sin(2 * np.pi * f * y) / f, f) / np.pi

    def solve(level, a, b):
        for _ in range(80):
            m = 0.5 * (a + b)
            a, b = (m, b) if s(m) < level else (a, m)
        return 0.5 * (a + b)
    return solve(0.9, 0.0, 3.0) - solve(0.1, -3.0, 0.0)


def _width(profile: np.ndarray, n: int) -> float:
    lo = np.median(profile[n // 4 - 50:n // 4 + 50])
    hi = np.median(profile[3 * n // 4 - 50:3 * n // 4 + 50])
    f = (profile - lo) / (hi - lo)
    x = np.arange(n)

    def cross(level):
        i = np.flatnonzero((f[:-1] < level) & (f[1:] >= level))
        i = i[np.argmin(np.abs(i - n // 2))]
        return x[i] + (level - f[i]) / (f[i + 1] - f[i])
    return cross(0.9) - cross(0.1)


def test_measured_resolution_versus_mask_radius():
    n, phi0 = 1024, 0.05
    g = Grid((n, 64), (1.0, 1.0), ("y", "x"), "image plane (TEST_ONLY resolution test)")
    y = np.arange(n)[:, None] * np.ones((1, 64))
    u_r = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=Q, amplitude=1.0,
                                         relative_phase_rad=0.0, aperture_passage="no_aperture",
                                         realisation=None)
    H = hologram_intensity(Wave(np.exp(1j * phi0 * (y >= n // 2)), g, "step", None), u_r,
                           artefacts=NA, content="object")
    E = hologram_intensity(vacuum_object_wave(g, amplitude=1.0, realisation=None), u_r,
                           artefacts=NA, content="empty")
    c = locate_carrier(E, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    for apod in ("none", "hann"):
        const = _step_response_constant(apod)
        widths = []
        for R in (0.125 / 3, 0.125 / 4, 0.125 / 6, 0.125 / 8):
            res = reconstruct_sideband(H, carrier=c, mask=MaskSpec(R, "disc", apod),
                                       empty_hologram=None, reference_correction="none", object_min_visibility=0.05,
                                       unwrapping="none")
            w = _width(res.wrapped_phase[:, 32], n)
            bound = 1.0 / (n * R - 1.0) + phi0 ** 2
            print(f"{apod}: R = {R:.5f} cycles/A ({n * R:.2f} bins): 10-90 width {w:.4f} A, "
                  f"width x R = {w * R:.5f}, predicted {const:.5f}, |ratio - 1| = "
                  f"{abs(w * R / const - 1):.4f} <= {bound:.4f}; reported resolution "
                  f"{res.resolution_A:.1f} A")
            assert abs(w * R / const - 1.0) <= bound
            assert w <= res.resolution_A
            widths.append(w)
        assert all(a < b for a, b in zip(widths, widths[1:]))       # smaller R, coarser
    assert abs(_step_response_constant("none") - 0.44582) <= 5e-5


def test_ensemble_converges_with_the_number_of_realisations():
    s, phi = 0.8, 0.5
    g = Grid((32, 64), (1.0, 1.0), ("y", "x"), "image plane (TEST_ONLY ensemble test)")
    rng = np.random.default_rng(20260922)
    mu_inf = math.exp(-s * s / 2)
    empty = hologram_intensity(vacuum_object_wave(g, amplitude=1.0, realisation=None),
                               reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=Q,
                                                              amplitude=1.0, relative_phase_rad=0.0,
                                                              aperture_passage="no_aperture",
                                                              realisation=None),
                               artefacts=NA, content="empty")
    c = locate_carrier(empty, CarrierSearch((0.0, -0.125), 0.06, 0.03, "none", SIM_SIDEBAND))
    mask = MaskSpec(0.04, "disc", "none")
    ref_amp = np.median(reconstruct_sideband(empty, carrier=c, mask=mask, empty_hologram=None,
                                             reference_correction="none", object_min_visibility=0.05,
                                             unwrapping="none").amplitude)
    for K in (4, 16, 64, 256, 1024):
        delta = rng.normal(0.0, s, K)
        psi = rng.uniform(0.0, 2 * np.pi, K)
        pairs = []
        for k in range(K):
            u_o = Wave(np.full(g.shape, np.exp(1j * (phi + psi[k]))), g, "flat object", k)
            u_r = reference_r1_vacuum_plane_wave(g, carrier_cycles_per_A=Q, amplitude=1.0,
                                                 relative_phase_rad=float(psi[k] + delta[k]),
                                                 aperture_passage="no_aperture", realisation=k)
            pairs.append((u_o, u_r))
        H = ensemble_hologram_intensity(pairs, artefacts=NA, content="object")
        res = reconstruct_sideband(H, carrier=c, mask=mask, empty_hologram=None,
                                   reference_correction="none", object_min_visibility=0.05, unwrapping="none")
        mu = float(np.median(res.amplitude)) / ref_amp
        ph = float(np.median(res.wrapped_phase))
        exact = np.mean(np.exp(-1j * delta))
        assert mu == pytest.approx(abs(exact), abs=1e-9)                 # after squaring, exactly
        tol_mu = 4 * (1 - math.exp(-s * s)) / math.sqrt(2 * K) \
            + (1 - math.exp(-2 * s * s)) / (4 * K * mu_inf)
        tol_ph = 4 * math.sqrt((1 - math.exp(-2 * s * s)) / (2 * K)) / mu_inf
        print(f"K = {K:5d}: contrast {mu:.5f} (limit {mu_inf:.5f}, |err| {abs(mu - mu_inf):.5f} "
              f"<= {tol_mu:.5f}); phase {ph:+.5f} rad (limit {phi:+.5f}, |err| "
              f"{abs(ph - phi):.5f} <= {tol_ph:.5f}); seed 20260922")
        assert abs(mu - mu_inf) <= tol_mu
        assert abs(ph - phi) <= tol_ph
