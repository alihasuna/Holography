"""Rocking-series height under a constant phase offset or an angle offset (re-audit A2b N2).

The re-auditor's case (scratch script r10_b16_adversarial.py): 21 tilts 20-25 mrad, sigma 0.05 rad
declared correctly, h = 10 A, h_max 10.5 A; a constant residual delta = 0.1, 0.3, 0.45 rad, or a common
angle offset of 0.1 mrad. The earlier version refit h with the intercept fixed at 2 pi n, so an offset
that passed the B16 intercept check (|c - 2 pi n| <= 3 sigma_c) biased h by 9 to 46 of its reported
sigma_h. Now h and sigma_h come from the SLOPE of the free two-parameter weighted fit, and the
offset residual c - 2 pi n is reported with its standard error sigma_c.

Stated bounds (DERIVED_HERE, before the runs):
* Unconditionally the free slope is unbiased by a constant offset, and by an angle offset to first
  order (the offset moves the intercept; the second-order slope change, about -tan(theta) dtheta
  relative, is computed here from the noise-free perturbation and included in the prediction).
* Conditional on acceptance, B16 keeps |z + u| <= 3 (z the intercept error in sigma_c units, u the
  offset in sigma_c units) and chi2_free + (z + u)^2 <= chi2_crit(N - 1, p = 1e-3), chi2_free ~
  chi2(N - 2) independent of the estimates. The mean of accepted h is shifted by
  b_pred = dh_det + beta sigma_c E[z | accepted], beta = cov(h, c)/var(c) of the design. For these
  cases |b_pred| <= 0.85 sigma_h (asserted), so |mean error| <= sigma_h is the headline bound.
* The mean error agrees with b_pred within 4 sigma_h/sqrt(K); the scatter is at most the reported
  sigma_h (std <= sigma_h (1 + 4/sqrt(2 (K - 1)))), and the mean reported offset residual agrees
  with sigma_c (u + E[z | accepted]) within 4 sigma_c/sqrt(K).
4000 trials per case, one generator per case, seed 20260923 (the re-auditor's seed).
"""
import math
import warnings

import numpy as np
import pytest

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.geometry.specular import specular_step_phase, wrap_to_pi
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.quantification.errors import BranchAmbiguityError
from reflection_holo.quantification.rocking import CHI2_P_MIN, chi2_sf, resolve_rocking_series

LAM = wavelength_A(E)
TH = np.arange(20.0, 25.001, 0.25) * 1e-3
SIG = 0.05
H_TRUE, H_MAX = 10.0, 10.5
TRIALS = 4000


def design():
    kfac = 2 * np.pi / LAM
    s = 2 * np.sin(TH)
    A = np.column_stack([np.ones_like(s), -kfac * s])
    cov = np.linalg.inv(A.T @ A / SIG ** 2)
    return kfac, s, A, cov


def chi2_crit(dof):
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if chi2_sf(mid, dof) > CHI2_P_MIN else (lo, mid)
    return 0.5 * (lo + hi)


def selection_mean(u, n):
    """E[z | |z + u| <= 3 and chi2(n - 2) + (z + u)^2 <= chi2_crit(n - 1)], z ~ N(0, 1)."""
    z = np.linspace(-12, 12, 240001)
    crit = chi2_crit(n - 1)
    rest = crit - (z + u) ** 2
    F = np.array([1.0 - chi2_sf(r, n - 2) if r > 0 else 0.0 for r in rest[::100]])
    F = np.interp(z, z[::100], F)
    w = np.exp(-0.5 * z ** 2) * (np.abs(z + u) <= 3.0) * F
    return float(np.sum(z * w) / np.sum(w))


CASES = [("none", 0.0, 0.0), ("delta_0.1", 0.1, 0.0), ("delta_0.3", 0.3, 0.0),
         ("delta_0.45", 0.45, 0.0), ("angle_0.1mrad", 0.0, 0.1e-3)]


@pytest.mark.parametrize("name,delta,dtheta", CASES, ids=[c[0] for c in CASES])
def test_offsets_do_not_bias_the_free_slope_height(name, delta, dtheta):
    kfac, s, A, cov = design()
    sig_c, sig_h = math.sqrt(cov[0, 0]), math.sqrt(cov[1, 1])
    beta = cov[0, 1] / cov[0, 0]
    # deterministic effect of the offsets on the free fit (noise-free perturbation of the phases)
    pert = delta + (specular_step_phase(H_TRUE, TH + dtheta, LAM) - specular_step_phase(H_TRUE, TH, LAM))
    dc_det, dh_det = cov @ (A.T @ pert) / SIG ** 2
    u = dc_det / sig_c
    m = selection_mean(u, TH.size)
    b_pred = dh_det + beta * sig_c * m
    assert abs(b_pred) <= 0.85 * sig_h

    rng = np.random.default_rng(20260923)
    errs, offs, refused = [], [], 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)       # uniform grid: aliasing flag (N4)
        for _ in range(TRIALS):
            phi = specular_step_phase(H_TRUE, TH + dtheta, LAM) + delta + rng.normal(0, SIG, TH.size)
            try:
                r = resolve_rocking_series(TH, TH, wrap_to_pi(phi), sigma_phi_rad=np.full(TH.size, SIG),
                                           wavelength_A=LAM, h_max_A=H_MAX)
            except BranchAmbiguityError:
                refused += 1
                continue
            errs.append(r.h_A - H_TRUE)
            offs.append(r.offset_residual_rad)
            assert r.sigma_h_A == pytest.approx(sig_h, rel=1e-9)
            assert r.sigma_offset_residual_rad == pytest.approx(sig_c, rel=1e-9)
    e, o = np.array(errs), np.array(offs)
    K = e.size
    print(f"{name}: offset {delta} rad, angle offset {dtheta * 1e3:.2f} mrad: u = {u:+.3f} sigma_c; "
          f"accepted {K} of {TRIALS}, refused {refused}; mean err {e.mean():+.5f} A = "
          f"{e.mean() / sig_h:+.3f} sigma_h (predicted {b_pred / sig_h:+.3f}); std/sigma_h "
          f"{e.std(ddof=1) / sig_h:.3f}; mean offset residual {o.mean():+.4f} rad (predicted "
          f"{sig_c * (u + m):+.4f}); sigma_h {sig_h:.5f} A, sigma_c {sig_c:.4f} rad; seed 20260923")
    assert K > 0.4 * TRIALS
    assert abs(e.mean()) <= sig_h
    assert abs(e.mean() - b_pred) <= 4 * sig_h / math.sqrt(K)
    assert e.std(ddof=1) <= sig_h * (1 + 4 / math.sqrt(2 * (K - 1)))
    assert abs(o.mean() - sig_c * (u + m)) <= 4 * sig_c / math.sqrt(K)
