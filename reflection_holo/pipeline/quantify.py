"""Quantification stage of the pipeline: terrace regions, signed step heights with wrap and branch,
shadow exclusion and the no-step control (docs/05 section 5 item 8; docs/03 section 4).

Regions. The terrace of every detector pixel and whether it is usable are obtained by ray tracing
the pixel's exit-plane point back to the surface of the BUILT structure
(``forward.geometric.trace_exit_points``; the same function for every engine), i.e. from the
simulated geometry, not segmented from the data. A pixel is usable only if its source is a lit
terrace top (not in an illumination shadow, not on a riser, inside the field of view) and the
reconstruction marks it valid. A terrace region keeps only usable pixels whose box of half-widths
m_a = ceil(n_res * resolution / pixel_a) (n_res declared, PROJECT_INPUT item 19 stand-in) lies
entirely inside the same terrace's usable set (outside the ROI counts as unusable).

Step phase. For two regions A (lower index along the field) and B, the circular median of the
wrapped reconstructed phase in each region gives Delta_phi = wrap(phi_B - phi_A). Its uncertainty
is MEASURED from the phase scatter: SE = 1.2533 sd sqrt(A_eff / n) per region (sd the circular
scatter, n the pixel count, A_eff = n_pix / sum W^2 the effective resolution area of the sideband
mask in pixels: pixels closer than a resolution element are correlated), combined in quadrature.

Branch (lattice constraint; docs/03 section 4 "the branch must come from a lattice constraint (h is
an integer multiple of the layer spacing) or from a rocking series"): the candidate heights
h_m = -(Delta_phi + 2 pi m)/|q.n_hat| are compared with the lattice heights n a/4, |n| <= n_max
(declared). The branch is accepted only if exactly one candidate lies within n_sigma sigma_h of a
lattice height; none (the phase is not a geometric lattice-height phase) or several (ambiguous) is a
refusal and no height is returned. The returned height is the MEASURED h_m of that branch
(quantification.height.height_from_phase, with the small-denominator policy and the propagated
uncertainty), not the lattice value. An a/4 step outside the B4 scope gets its phase difference
reported and no height.
"""
from __future__ import annotations

import math

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.forward.geometric import STATUS, trace_exit_points
from reflection_holo.geometry.specular import wrap_to_pi
from reflection_holo.quantification.controls import no_step_control
from reflection_holo.quantification.errors import QuantificationError
from reflection_holo.quantification.height import (height_from_phase,
                                                    sensitivity_rad_per_A,
                                                    sensitivity_uncertainty_rad_per_A,
                                                    wrap_period_A)
from reflection_holo.structure.si001 import B4_A4_100


def detector_trace(model, u_A, y_A, *, x0_A: float, theta_rad: float, layout) -> dict:
    """Ray trace of every detector pixel centre (u along the beam, y perpendicular; image-plane A)
    through its exit-plane point x = x0 - u / cos(theta)."""
    U, Y = np.meshgrid(np.asarray(u_A, float), np.asarray(y_A, float), indexing="ij")
    X = x0_A - U / math.cos(theta_rad)
    tr = trace_exit_points(model, X, Y, layout=layout, theta_in_ext_rad=theta_rad,
                           theta_out_ext_rad=theta_rad)
    n = model.n_terraces
    ft = np.where(tr["source_terrace"] >= 0, tr["source_period"] * n + tr["source_terrace"], -1)
    tr["field_terrace"] = ft.astype(np.int64)
    tr["exit_x_A"] = X
    return tr


def box_erode(mask: np.ndarray, m0: int, m1: int) -> np.ndarray:
    """True where the (2 m0 + 1) x (2 m1 + 1) box centred on the pixel is entirely True (outside
    the array counts as False)."""
    g = np.asarray(mask, dtype=bool)
    P = np.pad(g.astype(np.int64), ((m0, m0), (m1, m1)))
    S = np.zeros((P.shape[0] + 1, P.shape[1] + 1), dtype=np.int64)
    S[1:, 1:] = P.cumsum(0).cumsum(1)
    n0, n1 = g.shape
    a0, a1 = 2 * m0 + 1, 2 * m1 + 1
    win = (S[a0:a0 + n0, a1:a1 + n1] - S[:n0, a1:a1 + n1] - S[a0:a0 + n0, :n1] + S[:n0, :n1])
    return win == a0 * a1


def region_phase(phase: np.ndarray, region: np.ndarray, a_eff_px: float) -> dict:
    """Circular median, scatter and correlated standard error of the phase over a region."""
    p = np.asarray(phase, float)[region]
    if p.size == 0 or not np.all(np.isfinite(p)):
        raise QuantificationError("region empty or containing invalid pixels")
    c = float(np.angle(np.mean(np.exp(1j * p))))
    d = wrap_to_pi(p - c)
    med = float(np.median(d))
    sd = float(np.std(wrap_to_pi(d - med)))
    n = int(p.size)
    n_eff = max(1.0, n / a_eff_px)
    return dict(median_rad=float(wrap_to_pi(c + med)), scatter_rad=sd, n_px=n, n_independent=n_eff,
                se_median_rad=1.2533 * sd / math.sqrt(n_eff))


def lattice_branch(wrapped_rad: float, *, s_rad_per_A: float, sigma_s_rad_per_A: float,
                   sigma_phi_rad: float, layer_A: float, n_max: int, n_sigma: float) -> dict:
    """Branch index m from the lattice constraint (module docstring). Returns the candidates and
    the decision: "resolved" (one candidate within n_sigma sigma_h of a lattice height),
    "inconsistent" (none) or "ambiguous" (several)."""
    h2pi = TWO_PI / s_rad_per_A
    M = int(math.ceil((n_max + 0.5) * layer_A / h2pi)) + 2
    cands = []
    for m in range(-M, M + 1):
        h = -(wrapped_rad + TWO_PI * m) / s_rad_per_A
        n = int(round(h / layer_A))
        if abs(n) > n_max:
            continue
        sig = math.hypot(sigma_phi_rad / s_rad_per_A, h * sigma_s_rad_per_A / s_rad_per_A)
        dist = abs(h - n * layer_A)
        cands.append(dict(branch_index=m, h_A=h, lattice_n=n, lattice_h_A=n * layer_A,
                          distance_A=dist, sigma_h_A=sig, within=bool(dist <= n_sigma * sig)))
    cands.sort(key=lambda c: c["distance_A"])
    ok = [c for c in cands if c["within"]]
    decision = "resolved" if len(ok) == 1 else ("inconsistent" if not ok else "ambiguous")
    return dict(decision=decision, chosen=ok[0] if len(ok) == 1 else None, candidates=cands,
                n_sigma=n_sigma, n_max=n_max, layer_A=layer_A, wrap_period_A=h2pi)


def measure_steps(*, phase: np.ndarray, regions: dict, a_eff_px: float, field_steps: list,
                  wavelength_A: float, theta_rad: float, sigma_theta_rad: float,
                  sigma_wavelength_rel: float, layer_A: float, n_max: int, n_sigma: float,
                  branch_source: str) -> list[dict]:
    """Signed height of every step between two measurable regions (module docstring)."""
    s = sensitivity_rad_per_A(wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad,
                              theta_out_ext_rad=theta_rad)
    sig_s = sensitivity_uncertainty_rad_per_A(
        wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad, theta_out_ext_rad=theta_rad,
        sigma_theta_in_rad=sigma_theta_rad, sigma_theta_out_rad=sigma_theta_rad,
        sigma_wavelength_rel=sigma_wavelength_rel)
    h2pi = wrap_period_A(wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad,
                         theta_out_ext_rad=theta_rad)
    out = []
    for st in field_steps:
        rec = dict(st)
        a, b = st["from_field_terrace"], st["to_field_terrace"]
        ra, rb = regions.get(a), regions.get(b)
        if ra is None or rb is None or not ra["measurable"] or not rb["measurable"]:
            rec.update(measured=False, reason="a terrace region is empty or below the minimum size "
                                              "after the margin (not measurable)")
            out.append(rec)
            continue
        pa, pb = ra["phase"], rb["phase"]
        dphi = float(wrap_to_pi(pb["median_rad"] - pa["median_rad"]))
        sphi = float(math.hypot(pa["se_median_rad"], pb["se_median_rad"]))
        rec.update(measured=True, delta_phi_wrapped_rad=dphi, sigma_delta_phi_rad=sphi,
                   sensitivity_rad_per_A=s, sigma_sensitivity_rad_per_A=sig_s, wrap_period_A=h2pi)
        if st["type"] == "screw" and st["model_assumption_B4"] != B4_A4_100:
            rec.update(height=None, reason=f"a/4 step outside the B4 scope ({st['model_assumption_B4']}): "
                                           f"the phase difference is reported, not a height")
            out.append(rec)
            continue
        if not (sphi > 0.0):
            rec.update(height=None, reason="zero measured phase scatter: the uncertainty is not "
                                           "measurable (noise-free data); no height")
            out.append(rec)
            continue
        br = lattice_branch(dphi, s_rad_per_A=s, sigma_s_rad_per_A=sig_s, sigma_phi_rad=sphi,
                            layer_A=layer_A, n_max=n_max, n_sigma=n_sigma)
        rec["branch"] = br
        if br["decision"] != "resolved":
            rec.update(height=None, reason=f"branch {br['decision']} under the lattice constraint: "
                                           f"height refused")
            out.append(rec)
            continue
        try:
            est = height_from_phase(dphi, branch_index=br["chosen"]["branch_index"],
                                    branch_source=branch_source, wavelength_A=wavelength_A,
                                    theta_in_ext_rad=theta_rad, theta_out_ext_rad=theta_rad,
                                    sigma_phi_rad=sphi, sigma_theta_in_rad=sigma_theta_rad,
                                    sigma_theta_out_rad=sigma_theta_rad,
                                    sigma_wavelength_rel=sigma_wavelength_rel)
        except (QuantificationError, ValueError) as exc:
            rec.update(height=None, reason=f"height refused: {exc}")
            out.append(rec)
            continue
        rec["height"] = dict(h_A=est.h_A, sigma_h_A=est.sigma_h_A, branch_index=est.branch_index,
                             branch_source=est.branch_source,
                             unwrapped_phase_rad=est.unwrapped_phase_rad,
                             h_principal_A=est.h_principal_A, wrap_period_A=est.wrap_period_A,
                             convention=est.convention)
        out.append(rec)
    return out


def split_control(region: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split a region into two halves along the beam axis (rows) at its median row."""
    rows = np.nonzero(region)[0]
    cut = int(np.median(rows))
    a = region.copy()
    b = region.copy()
    a[cut:, :] = False
    b[:cut, :] = False
    return a, b


def no_step(phase: np.ndarray, region: np.ndarray, a_eff_px: float, n_sigma: float,
            valid: np.ndarray) -> dict:
    """No-step control on a flat region: its two halves must agree within n_sigma times the
    measured correlated standard error (quantification.controls.no_step_control)."""
    a, b = split_control(region)
    if not a.any() or not b.any():
        return dict(performed=False, reason="region too small to split")
    pa, pb = region_phase(phase, a, a_eff_px), region_phase(phase, b, a_eff_px)
    se = math.hypot(pa["se_median_rad"], pb["se_median_rad"])
    if not se > 0:
        return dict(performed=False, reason="zero measured scatter (noise-free): tolerance undefined")
    tol = n_sigma * se
    r = no_step_control(phase, a, b, valid_mask=valid, tolerance_rad=tol)
    return dict(performed=True, delta_rad=r.delta_rad, tolerance_rad=tol, n_sigma=n_sigma,
                se_correlated_rad=se, passed=r.passed, n_a=r.n_a, n_b=r.n_b,
                controls_sigma_uncorrelated_rad=r.sigma_rad)


STATUS_NAMES = {v: k for k, v in STATUS.items()}
