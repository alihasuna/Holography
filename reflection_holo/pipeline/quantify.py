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
an integer multiple of the layer spacing) or from a rocking series"). The steps of one run share ONE
angle calibration and one wavelength, so the sensitivity error is a common scale of every step
(audit A3 M3): s_true = s (1 + eps). The rule is joint over the K measured steps of the run
(``lattice_branch``):
  * model: unwrapped phase of step i, phi_i + 2 pi m_i = -s (1 + eps) n_i a/4 + r_i, with the
    lattice index n_i in {+-1, ..., +-n_max} (n = 0 is excluded: the two regions straddle a step of
    the ray-traced geometry, audit A3 M1), |r_i| <= n_sigma sigma_phi_i (the MEASURED phase
    uncertainty) and |eps| <= E = n_sigma sigma_s / s (sigma_s the propagated, correlated
    sensitivity uncertainty);
  * an assignment {(n_i, m_i)} is consistent if one eps satisfies every step. None: "inconsistent";
    several: "ambiguous"; exactly one: "resolved" only if the lattice constraint is SIGNIFICANT;
  * significance (audit A3 B1: a phase that carries no height information must be refused): P_chance
    is an upper bound on the probability that K phases uniform on the circle (no height
    information) are accepted by the rule, the zonotope volume of every assignment over (2 pi)^K,
        P_chance = prod_i (2 n_max 2 w_i / 2 pi) [1 + sum_i E s (a/4) (n_max + 1) / (2 w_i)],
    w_i = n_sigma sigma_phi_i. The branch is "resolved" only if P_chance <= alpha = P(|Z| > n_sigma)
    (2.70e-3 for n_sigma = 3), the false-acceptance rate the n_sigma criterion implies; otherwise
    "not significant" and no height. A single step at the demo angle calibration (0.1 mrad) is
    never significant (P_chance ~ 0.4); the three demo steps together are (P_chance ~ 1e-4).
    For true lattice steps with Gaussian errors the rule accepts the right assignment with
    probability >= (1 - alpha)^(K+1).
The returned height is the MEASURED -(phi_i + 2 pi m_i)/s of the chosen branch
(quantification.height.height_from_phase with angle_errors="common": the specular beam's incidence
and exit angles share one calibration error, sigma_s = 2 k cos(theta) sigma_theta), not the lattice
value. An a/4 step outside the B4 scope gets its phase difference reported and no height.

Heights are WITHHELD for the whole run (``withhold_reason``, audit A3 B1) when the no-step control
failed or could not be performed, or when the phase is differential (R2 self-reference, audit A3
M1): every measured step keeps its phase difference, carries ``height: None`` and the reason.
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


def chance_level(n_sigma: float) -> float:
    """alpha = P(|Z| > n_sigma) for a standard normal Z: the false-acceptance rate that an n_sigma
    criterion implies (2.6998e-3 for n_sigma = 3)."""
    return math.erfc(float(n_sigma) / math.sqrt(2.0))


def chance_probability_bound(sigma_phi_rad, *, s_rad_per_A: float, sigma_s_rad_per_A: float,
                             layer_A: float, n_max: int, n_sigma: float) -> float:
    """Upper bound on the probability that K phases uniform on the circle (no height information)
    are accepted by ``lattice_branch`` (module docstring): the sum over the (2 n_max)^K assignments
    of the volume of {box of half-widths w_i} + {segment eps in [-E, E]}, over (2 pi)^K; capped
    at 1."""
    w = n_sigma * np.atleast_1d(np.asarray(sigma_phi_rad, dtype=float))
    E = n_sigma * sigma_s_rad_per_A / s_rad_per_A
    base = float(np.prod(2 * n_max * 2 * w / TWO_PI))
    extra = float(np.sum(E * s_rad_per_A * layer_A * (n_max + 1) / (2 * w)))
    return min(1.0, base * (1.0 + extra))


MAX_JOINT_SURVIVORS = 100_000


def lattice_branch(wrapped_rad, *, s_rad_per_A: float, sigma_s_rad_per_A: float, sigma_phi_rad,
                   layer_A: float, n_max: int, n_sigma: float) -> dict:
    """Joint lattice-constraint branch of the steps of one run (module docstring).

    ``wrapped_rad`` and ``sigma_phi_rad``: one value (one step) or equal-length sequences (the K
    steps sharing one angle calibration). ``sigma_s_rad_per_A``: the propagated, CORRELATED
    uncertainty of the sensitivity s (a common scale of every step). Returns the decision
    ("resolved", "not significant", "ambiguous", "inconsistent"), the assignment
    [{lattice_n, branch_index, h_A, lattice_h_A}] per step (for "resolved" and "not significant"),
    the eps interval, the chance bound and alpha. For one step, "chosen" is its assignment."""
    phis = np.atleast_1d(np.asarray(wrapped_rad, dtype=float))
    sig = np.atleast_1d(np.asarray(sigma_phi_rad, dtype=float))
    if phis.ndim != 1 or sig.shape != phis.shape or phis.size == 0:
        raise ValueError("wrapped_rad and sigma_phi_rad must be one value or equal-length sequences")
    if not (np.all(np.isfinite(phis)) and np.all(phis > -math.pi) and np.all(phis <= math.pi)):
        raise ValueError(f"wrapped phases must lie in (-pi, pi], got {phis.tolist()}")
    if not (np.all(np.isfinite(sig)) and np.all(sig > 0)):
        raise ValueError(f"phase uncertainties must be finite and > 0, got {sig.tolist()}")
    for name, v in (("s_rad_per_A", s_rad_per_A), ("sigma_s_rad_per_A", sigma_s_rad_per_A),
                    ("layer_A", layer_A), ("n_sigma", n_sigma)):
        if not (math.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be finite and > 0, got {v!r}")
    if not (isinstance(n_max, int) and n_max >= 1):
        raise ValueError(f"n_max must be an integer >= 1, got {n_max!r}")
    K = int(phis.size)
    s = float(s_rad_per_A)
    E = n_sigma * sigma_s_rad_per_A / s
    w = n_sigma * sig
    alpha = chance_level(n_sigma)
    p_chance = chance_probability_bound(sig, s_rad_per_A=s, sigma_s_rad_per_A=sigma_s_rad_per_A,
                                        layer_A=layer_A, n_max=n_max, n_sigma=n_sigma)
    allowed = [n for n in range(-n_max, n_max + 1) if n != 0]
    out = dict(n_steps=K, n_sigma=n_sigma, n_max=n_max, layer_A=layer_A,
               lattice_n_allowed=allowed, wrap_period_A=TWO_PI / s,
               relative_sensitivity_sigma=sigma_s_rad_per_A / s, epsilon_bound=E,
               chance_probability_bound=p_chance, chance_level=alpha,
               rule=("joint lattice constraint over the steps of the run: phi_i + 2 pi m_i = "
                     "-s (1 + eps) n_i a/4 + r_i, |r_i| <= n_sigma sigma_phi_i, |eps| <= n_sigma "
                     "sigma_s/s (one common angle calibration), n_i != 0; resolved only if the "
                     "chance-acceptance bound of uniform phases <= P(|Z| > n_sigma) (audit A3 B1)"))
    if E >= 1.0:
        out.update(decision="not significant", assignment=None, epsilon_interval=None,
                   chosen=None, reason=f"the sensitivity is not larger than n_sigma times its "
                                       f"uncertainty (E = {E:.3g} >= 1)")
        return out
    per_step = []
    for i in range(K):
        opts = []
        for n in allowed:
            A = s * n * layer_A
            c = -phis[i] - A
            mlo = math.floor((c - abs(A) * E - w[i]) / TWO_PI)
            mhi = math.ceil((c + abs(A) * E + w[i]) / TWO_PI)
            for m in range(mlo, mhi + 1):
                lo = (-w[i] - phis[i] - TWO_PI * m - A) / A
                hi = (w[i] - phis[i] - TWO_PI * m - A) / A
                lo, hi = min(lo, hi), max(lo, hi)
                lo, hi = max(lo, -E), min(hi, E)
                if lo <= hi:
                    opts.append((lo, hi, n, m))
        per_step.append(opts)
    surv = [(-E, E, ())]
    overflow = False
    for opts in per_step:
        new = []
        for lo, hi, asg in surv:
            for l2, h2, n, m in opts:
                lo2, hi2 = max(lo, l2), min(hi, h2)
                if lo2 <= hi2:
                    new.append((lo2, hi2, asg + ((n, m),)))
        surv = new
        if len(surv) > MAX_JOINT_SURVIVORS:
            overflow = True
            break
    assignments = sorted({a for _, _, a in surv}) if not overflow else None
    out["per_step_options"] = [[dict(lattice_n=n, branch_index=m, h_A=-(phis[i] + TWO_PI * m) / s,
                                     epsilon_interval=[lo, hi]) for lo, hi, n, m in opts]
                               for i, opts in enumerate(per_step)]
    if overflow or (assignments is not None and len(assignments) > 1):
        out.update(decision="ambiguous", assignment=None, epsilon_interval=None, chosen=None,
                   n_consistent_assignments=(None if overflow else len(assignments)),
                   reason="several lattice assignments are consistent with one common eps")
        return out
    if not assignments:
        out.update(decision="inconsistent", assignment=None, epsilon_interval=None, chosen=None,
                   n_consistent_assignments=0,
                   reason="no lattice assignment is consistent with one common eps")
        return out
    asg = assignments[0]
    ivs = [(lo, hi) for lo, hi, a in surv if a == asg]
    assignment = [dict(lattice_n=n, branch_index=m, h_A=-(phis[i] + TWO_PI * m) / s,
                       lattice_h_A=n * layer_A) for i, (n, m) in enumerate(asg)]
    significant = p_chance <= alpha
    out.update(decision="resolved" if significant else "not significant", assignment=assignment,
               epsilon_interval=[min(lo for lo, _ in ivs), max(hi for _, hi in ivs)],
               n_consistent_assignments=1,
               chosen=assignment[0] if K == 1 else None,
               reason=("one lattice assignment, significant" if significant else
                       f"the lattice constraint cannot distinguish these {K} phase(s) from phases "
                       f"carrying no height information: chance-acceptance bound "
                       f"{p_chance:.3g} > alpha {alpha:.3g} (P(|Z| > {n_sigma:g}))"))
    return out


def measure_steps(*, phase: np.ndarray, regions: dict, a_eff_px: float, field_steps: list,
                  wavelength_A: float, theta_rad: float, sigma_theta_rad: float,
                  sigma_wavelength_rel: float, layer_A: float, n_max: int, n_sigma: float,
                  branch_source: str, withhold_reason: str | None) -> tuple[list[dict], dict]:
    """Signed height of every step between two measurable regions (module docstring). Returns the
    step records and the joint branch record. ``withhold_reason`` (required; None when heights may
    be returned) withholds every height of the run with that reason (control failed or not
    performed, differential phase)."""
    s = sensitivity_rad_per_A(wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad,
                              theta_out_ext_rad=theta_rad)
    sig_s = sensitivity_uncertainty_rad_per_A(
        wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad, theta_out_ext_rad=theta_rad,
        sigma_theta_in_rad=sigma_theta_rad, sigma_theta_out_rad=sigma_theta_rad,
        sigma_wavelength_rel=sigma_wavelength_rel, angle_errors="common")
    h2pi = wrap_period_A(wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad,
                         theta_out_ext_rad=theta_rad)
    out = []
    eligible = []
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
                   sensitivity_rad_per_A=s, sigma_sensitivity_rad_per_A=sig_s,
                   sigma_sensitivity_note="angle errors common to incidence and exit (specular "
                                          "beam, one calibration; audit A3 M3)",
                   wrap_period_A=h2pi)
        out.append(rec)
        if withhold_reason is not None:
            rec.update(height=None, reason=withhold_reason, heights_withheld=True)
            continue
        if st["type"] == "screw" and st["model_assumption_B4"] != B4_A4_100:
            rec.update(height=None, reason=f"a/4 step outside the B4 scope ({st['model_assumption_B4']}): "
                                           f"the phase difference is reported, not a height")
            continue
        if not (sphi > 0.0):
            rec.update(height=None, reason="zero measured phase scatter: the uncertainty is not "
                                           "measurable (noise-free data); no height")
            continue
        eligible.append(rec)
    if withhold_reason is not None:
        return out, dict(decision="withheld", reason=withhold_reason, steps=[])
    if not eligible:
        return out, dict(decision="no eligible step", steps=[])
    br = lattice_branch([r["delta_phi_wrapped_rad"] for r in eligible], s_rad_per_A=s,
                        sigma_s_rad_per_A=sig_s,
                        sigma_phi_rad=[r["sigma_delta_phi_rad"] for r in eligible],
                        layer_A=layer_A, n_max=n_max, n_sigma=n_sigma)
    br["steps"] = [[r["from_field_terrace"], r["to_field_terrace"]] for r in eligible]
    for i, rec in enumerate(eligible):
        asg = br["assignment"][i] if br["assignment"] is not None else None
        rec["branch"] = dict(decision=br["decision"], joint_over_steps=br["steps"],
                             chance_probability_bound=br["chance_probability_bound"],
                             chance_level=br["chance_level"], assignment=asg,
                             epsilon_interval=br["epsilon_interval"],
                             per_step_options=br["per_step_options"][i]
                             if "per_step_options" in br else None)
        if br["decision"] != "resolved":
            rec.update(height=None, reason=f"branch {br['decision']} under the joint lattice "
                                           f"constraint: {br['reason']}; height refused")
            continue
        try:
            est = height_from_phase(rec["delta_phi_wrapped_rad"], branch_index=asg["branch_index"],
                                    branch_source=branch_source, wavelength_A=wavelength_A,
                                    theta_in_ext_rad=theta_rad, theta_out_ext_rad=theta_rad,
                                    sigma_phi_rad=rec["sigma_delta_phi_rad"],
                                    sigma_theta_in_rad=sigma_theta_rad,
                                    sigma_theta_out_rad=sigma_theta_rad,
                                    sigma_wavelength_rel=sigma_wavelength_rel,
                                    angle_errors="common")
        except (QuantificationError, ValueError) as exc:
            rec.update(height=None, reason=f"height refused: {exc}")
            continue
        rec["height"] = dict(h_A=est.h_A, sigma_h_A=est.sigma_h_A, branch_index=est.branch_index,
                             branch_source=est.branch_source,
                             unwrapped_phase_rad=est.unwrapped_phase_rad,
                             h_principal_A=est.h_principal_A, wrap_period_A=est.wrap_period_A,
                             angle_errors=est.angle_errors, convention=est.convention)
    return out, br


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
