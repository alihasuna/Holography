"""Aggregation of a campaign stage: tables, verdicts and figures.

  python -m reflection_holo.aggregate --run-dir RUN --stage STAGE [--benchmarks configs/benchmarks.yaml]

Writes RUN/summary/<stage>/summary.json (all numbers and pass/fail verdicts),
CSV tables and, if matplotlib is importable, PNG figures.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np

from .constants import k_rad_per_A, wavelength_A
from .crystal import SurfaceCell
from .geometry import SpecularCondition
from .io import read_result

E_KEV = 200.0
LAM = float(wavelength_A(E_KEV))
K = float(k_rad_per_A(E_KEV))


def load_stage(run_dir, stage):
    out = []
    for f in sorted(glob.glob(os.path.join(run_dir, "results", stage, "*.h5"))):
        out.append(read_result(f))
    return out


def windows_of(res):
    return res["windows"]


def wmask(w, bm, min_abs=None, ref=None):
    m = w["weight"] >= bm["weight_min"]
    if min_abs is not None and ref is not None:
        m &= np.abs(ref) >= min_abs
    return m


def stitch(results, bm, theta_step_mrad=0.02):
    """Weighted combination of the windows of several tasks on the shared absolute
    theta grid (multiples of theta_step).  Weight = |a|^2 of each window.  Returns
    theta, r, the largest disagreement between overlapping windows, and the
    truncation bound of each point (weighted like r)."""
    pts = defaultdict(list)
    for res in results:
        for w in windows_of(res):
            m = w["weight"] >= bm["weight_min"]
            bnd = w.get("r_truncation_bound", np.zeros(len(w["theta"])))
            for th, r, wt, b in zip(w["theta"][m], w["r"][m], w["weight"][m], bnd[m]):
                key = int(round(th * 1e3 / theta_step_mrad))
                pts[key].append((r, wt**2, b))
    keys = sorted(pts)
    th = np.array(keys) * theta_step_mrad * 1e-3
    r = np.array([sum(a * c for a, c, _ in pts[k]) / sum(c for _, c, _ in pts[k]) for k in keys])
    bound = np.array([sum(b * c for _, c, b in pts[k]) / sum(c for _, c, _ in pts[k]) for k in keys])
    overlap = 0.0
    for k in keys:
        if len(pts[k]) > 1:
            rr = [a for a, _, _ in pts[k]]
            overlap = max(overlap, max(abs(x - y) for x in rr for y in rr))
    return th, r, overlap, bound


def group_key(res):
    t = res["task"]
    return (t["surface"], t["structure"].get("level"), t.get("mode", "static"),
            t.get("variant", "default"))


def ensemble(results, bm):
    """Coherent average <r> and incoherent <|r|^2> over frozen-phonon seeds, on the
    union theta grid of the windows; standard error of <r> from the seed scatter."""
    per_seed = defaultdict(list)
    for res in results:
        per_seed[res["task"]["seed"]].append(res)
    curves = []
    for seed, rs in sorted(per_seed.items()):
        th, r, _, _ = stitch(rs, bm)
        curves.append(dict(zip(np.round(th * 1e5).astype(int), r)))
    common = sorted(set.intersection(*[set(c) for c in curves])) if curves else []
    R = np.array([[c[k] for k in common] for c in curves])
    th = np.array(common) * 1e-5
    mean = R.mean(axis=0)
    se = R.std(axis=0, ddof=1) / np.sqrt(len(R)) if len(R) > 1 else np.full(len(th), np.nan)
    inc = (np.abs(R) ** 2).mean(axis=0)
    return dict(theta=th, r_mean=mean, r_se=se, I_incoherent=inc,
                I_coherent=np.abs(mean) ** 2, n=len(R))


def compare_curves(th1, r1, th2, r2, min_abs, b1=None, b2=None):
    """Differences of two curves on their common theta points with |r| >= min_abs.
    b1, b2 are truncation bounds; 'excess' quantities subtract them (amplitude) or
    their phase equivalents (b/|r|), so that a comparison fails only beyond the
    stated numerical uncertainty."""
    b1 = np.zeros(len(th1)) if b1 is None else b1
    b2 = np.zeros(len(th2)) if b2 is None else b2
    k1 = dict(zip(np.round(th1 * 1e5).astype(int), zip(r1, b1)))
    k2 = dict(zip(np.round(th2 * 1e5).astype(int), zip(r2, b2)))
    keys = sorted(set(k1) & set(k2))
    a = np.array([k1[k][0] for k in keys])
    b = np.array([k2[k][0] for k in keys])
    allow = np.array([k1[k][1] + k2[k][1] for k in keys])
    m = (np.abs(a) >= min_abs) & (np.abs(b) >= min_abs)
    if not m.any():
        return dict(n=0)
    d = np.abs(a - b)[m]
    ph = np.abs(np.angle(a[m] / b[m]))
    al = allow[m]
    return {"n": int(m.sum()), "max_abs_diff": float(d.max()), "max_phase_diff": float(ph.max()),
            "max_rel_diff": float(np.max(d / np.abs(b[m]))),
            "max_abs_excess": float(np.max(d - al)),
            "max_phase_excess": float(np.max(ph - al / np.minimum(np.abs(a[m]), np.abs(b[m])))),
            "max_truncation_bound": float(al.max()),
            "n_points_bound_above_1e-4": int(np.sum(al > 1e-4))}


def h_unit(surface, a=5.4309):
    return SurfaceCell(surface, a).termination_units()[1]


def bragg_angles(surface, V0, theta_max=0.05, a=5.4309):
    """External angles of the specular Bragg conditions on the rod (all orders,
    allowed or not, labelled)."""
    d = a / np.sqrt(3) if surface.startswith("si111") else a
    out = []
    for n in range(1, 40):
        sc = SpecularCondition(d, n, E_KEV, V0)
        if sc.accessible and sc.theta_ext <= theta_max:
            if surface.startswith("si111"):
                hkl = (n, -n, n)
                allowed = (n % 2 == 1) or (n % 4 == 0)
            else:
                hkl = (0, 0, n)
                allowed = n % 4 == 0
            out.append(dict(hkl=hkl, allowed=allowed, theta_ext_mrad=1e3 * sc.theta_ext))
    return out


def local_maxima(th, absr, min_height=0.02):
    i = np.nonzero((absr[1:-1] > absr[:-2]) & (absr[1:-1] >= absr[2:]) & (absr[1:-1] > min_height))[0] + 1
    return [dict(theta_mrad=float(th[j] * 1e3), abs_r=float(absr[j])) for j in i]


# --------------------------------------------------------------------------
# validation stage
# --------------------------------------------------------------------------

def check_reference(w, tol, bm):
    rp = w["r_parratt_multislice"]
    m = w["weight"] >= bm["weight_min"]
    bnd = w.get("r_truncation_bound", np.zeros(len(rp)))
    err = np.abs(w["r"] - rp)
    amp_ok = np.all(err[m] <= np.maximum(tol["amp_rel"] * np.abs(rp[m]), tol["amp_abs_floor"]) + bnd[m])
    mp = m & (np.abs(rp) >= tol["phase_min_abs_r"])
    ph = (np.abs(np.angle(w["r"][mp] / rp[mp])) - bnd[mp] / np.abs(rp[mp])) if mp.any() else np.array([0.0])
    rs = w["r_parratt_schroedinger"]
    return dict(theta0_mrad=float(w["theta0_mrad"]), max_abs_err=float(err[m].max()),
                max_rel_err=float((err[m] / np.abs(rp[m])).max()),
                max_phase_err_beyond_bound=float(ph.max()), pass_amp=bool(amp_ok),
                max_truncation_bound=float(bnd[m].max()),
                pass_phase=bool(ph.max() <= tol["phase_rad"]),
                multislice_vs_schroedinger_model_max_rel=float(
                    (np.abs(rp - rs)[m] / np.abs(rs[m])).max()),
                record_tail_rel=float(w["record_tail_rel"]),
                record_head_rel=float(w["record_head_rel"]))


def terrace_ratio(curves, surface, levels, min_abs):
    """arg(r_L / r_0) + 2 K_ext h L: zero for translation- or mirror-related terraces.
    curves[L] = (theta, r, truncation bound); the phase uncertainty of the ratio is
    b_0/|r_0| + b_L/|r_L|."""
    th0, r0, b0 = curves[0]
    out = {}
    h = h_unit(surface)
    for L in levels:
        if L == 0 or L not in curves:
            continue
        thL, rL, bL = curves[L]
        k0 = dict(zip(np.round(th0 * 1e5).astype(int), zip(r0, b0)))
        kL = dict(zip(np.round(thL * 1e5).astype(int), zip(rL, bL)))
        keys = sorted(set(k0) & set(kL))
        th = np.array(keys) * 1e-5
        a = np.array([k0[k][0] for k in keys])
        b = np.array([kL[k][0] for k in keys])
        unc = np.array([k0[k][1] for k in keys]) / np.maximum(np.abs(a), 1e-300) \
            + np.array([kL[k][1] for k in keys]) / np.maximum(np.abs(b), 1e-300)
        m = (np.abs(a) >= min_abs) & (np.abs(b) >= min_abs)
        geo = -2.0 * K * np.sin(th) * h * L
        resid = np.angle(b / a * np.exp(-1j * geo))
        out[L] = dict(theta=th[m], residual_rad=resid[m], amp_ratio=np.abs(b / a)[m],
                      geometric_phase=geo[m], h_A=h * L, uncertainty_rad=unc[m])
    return out


def aggregate_validation(results, bm):
    S = dict(rung1=[], rung2=[], rung3={}, beam_independence={})
    flat = defaultdict(dict)
    waists = {}
    for res in results:
        t = res["task"]
        if t["kind"] == "uniform_1d":
            for w in windows_of(res):
                d = check_reference(w, bm["rung1_uniform_step"], bm)
                d.update(width_A=t["profile"]["width_A"],
                         W_V=t["physics"]["inelastic_absorption_W_V"]["value"])
                S["rung1"].append(d)
        elif t["kind"] == "averaged_1d":
            for w in windows_of(res):
                d = check_reference(w, bm["rung2_averaged_crystal"], bm)
                d.update(surface=t["surface"], W_V=t["physics"]["inelastic_absorption_W_V"]["value"],
                         V0_parametrization_V=float(res["V0_parametrization_V"]))
                S["rung2"].append(d)
        elif t["kind"] == "flat_rocking":
            th, r, ov, bnd = stitch([res], bm)
            if t["label"].startswith("beam waist"):
                waists[t["beams"][0]["w0_A"]] = (th, r, bnd)
            else:
                flat[t["surface"]][t["structure"]["level"]] = (th, r, bnd)
    tol = bm["rung3_null"]
    for surf, curves in flat.items():
        if 0 not in curves:
            continue
        tr = terrace_ratio(curves, surf, sorted(curves), tol["min_abs_r"])
        for L, d in tr.items():
            kind = ("translation" if (surf == "si111_110" or (surf == "si001_110" and L % 2 == 0))
                    else "mirror (si001 [100])" if surf == "si001_100" else "screw: physics result")
            n = len(d["theta"])
            entry = dict(h_A=d["h_A"], relation=kind, n=int(n),
                         max_abs_residual_rad=float(np.max(np.abs(d["residual_rad"]))) if n else None,
                         max_residual_beyond_uncertainty_rad=float(np.max(np.abs(d["residual_rad"]) - d["uncertainty_rad"])) if n else None,
                         max_amp_ratio_dev=float(np.max(np.abs(d["amp_ratio"] - 1))) if n else None,
                         max_amp_dev_beyond_uncertainty=float(np.max(np.abs(d["amp_ratio"] - 1) - d["uncertainty_rad"])) if n else None,
                         max_uncertainty_rad=float(np.max(d["uncertainty_rad"])) if n else None,
                         theta_mrad=(d["theta"] * 1e3).tolist(), residual_rad=d["residual_rad"].tolist(),
                         uncertainty_rad=d["uncertainty_rad"].tolist(), amp_ratio=d["amp_ratio"].tolist())
            if kind != "screw: physics result" and n:
                entry["pass"] = bool(entry["max_residual_beyond_uncertainty_rad"] <= tol["phase_rad"]
                                     and entry["max_amp_dev_beyond_uncertainty"] <= tol["amp_rel"])
            S["rung3"][f"{surf} level {L}"] = entry
    if waists:
        ref_w0 = 10.0 if 10.0 in waists else sorted(waists)[len(waists) // 2]
        ref = waists[ref_w0]
        S["beam_independence_reference_w0_A"] = ref_w0
        for w0, (th, r, bnd) in waists.items():
            if w0 == ref_w0:
                continue
            c = compare_curves(th, r, ref[0], ref[1], bm["beam_independence"]["min_abs_r"], bnd, ref[2])
            if c.get("n"):
                c["pass"] = bool(c["max_abs_excess"] <= bm["beam_independence"]["amp_abs"]
                                 and c["max_phase_excess"] <= bm["beam_independence"]["phase_rad"])
            S["beam_independence"][str(w0)] = c
    S["all_pass"] = bool(all(d["pass_amp"] and d["pass_phase"] for d in S["rung1"] + S["rung2"])
                         and all(v.get("pass", True) for v in S["rung3"].values())
                         and all(v.get("pass", True) for v in S["beam_independence"].values()))
    return S


# --------------------------------------------------------------------------
# convergence and rocking stages
# --------------------------------------------------------------------------

def aggregate_convergence(results, bm):
    groups = defaultdict(list)
    for res in results:
        groups[(res["task"]["label"].split(" seed")[0], res["task"].get("mode"))].append(res)
    ref = None
    curves = {}
    for (label, mode), rs in groups.items():
        if mode == "frozen_phonon":
            e = ensemble(rs, bm)
            curves[label] = (e["theta"], e["r_mean"], e, np.abs(e["r_se"]))
        else:
            th, r, ov, bnd = stitch(rs, bm)
            curves[label] = (th, r, None, bnd)
    prod = [lab for lab in curves if lab.endswith("(production)")]
    ref = curves[prod[0]] if prod else None
    S = dict(reference=prod[0] if prod else None, variants={})
    tol = bm["convergence"]
    roles = {res["task"]["label"]: res["task"].get("convergence_role", "info") for res in results}
    for label, (th, r, e, bnd) in curves.items():
        if ref is None or label.startswith("phonon") or roles.get(label) == "reference":
            continue
        c = compare_curves(th, r, ref[0], ref[1], tol["min_abs_r"], bnd, ref[3])
        c["role"] = roles.get(label, "info")
        if c.get("n"):
            c["within_tolerance"] = bool(c["max_abs_excess"] <= tol["amp_abs"]
                                         and c["max_phase_excess"] <= tol["phase_rad"])
        S["variants"][label] = c
    gates = [v for v in S["variants"].values() if v["role"] == "gate"]
    S["converged"] = bool(ref is not None and gates and all(v.get("within_tolerance") for v in gates))
    ph = {lab: v for lab, v in curves.items() if lab.startswith("phonon")}
    if ph:
        best = max(ph, key=lambda s: int(s.split("Ly=")[1].split()[0]))
        S["phonon_reference"] = best
        S["phonon"] = {}
        for lab, (th, r, e, se) in ph.items():
            c = compare_curves(th, r, ph[best][0], ph[best][1], tol["min_abs_r"], se, ph[best][3])
            c["n_configs"] = e["n"]
            c["median_standard_error"] = float(np.nanmedian(np.abs(e["r_se"])))
            S["phonon"][lab] = c
    return S


def aggregate_rocking(results, bm, V0_assumed=12.0):
    groups = defaultdict(list)
    for res in results:
        groups[group_key(res)].append(res)
    S = dict(curves={}, terrace_ratios={}, peaks={})
    V0p = float(results[0]["V0_parametrization_V"]) if results else None
    default_curves = defaultdict(lambda: defaultdict(dict))     # [mode][surface][level]
    arrays = {}
    for key, rs in groups.items():
        surf, lev, mode, variant = key
        name = f"{surf}|L{lev}|{mode}|{variant}"
        if mode == "frozen_phonon":
            e = ensemble(rs, bm)
            th, r, bnd = e["theta"], e["r_mean"], np.abs(e["r_se"])
            arrays[name] = dict(theta=th, r=r, r_se=e["r_se"], I_incoherent=e["I_incoherent"])
            S["curves"][name] = dict(n_configs=e["n"], median_se=float(np.nanmedian(np.abs(e["r_se"]))),
                                     diffuse_fraction_median=float(np.median(
                                         1 - e["I_coherent"] / np.maximum(e["I_incoherent"], 1e-30))))
        else:
            th, r, ov, bnd = stitch(rs, bm)
            arrays[name] = dict(theta=th, r=r, truncation_bound=bnd)
            S["curves"][name] = {"overlap_max_abs_diff": float(ov), "n_points": int(len(th)),
                                 "max_truncation_bound": float(bnd.max()) if len(bnd) else None,
                                 "theta_mrad_bound_above_1e-3": (th[bnd > 1e-3] * 1e3).tolist()}
        if variant == "default":
            default_curves[mode][surf][lev] = (th, r, bnd)
        S["peaks"][name] = local_maxima(th, np.abs(r))
    for mode, by_surf in default_curves.items():
        for surf, curves in by_surf.items():
            if 0 not in curves:
                continue
            tr = terrace_ratio(curves, surf, sorted(curves), bm["rung3_null"]["min_abs_r"])
            for L, d in tr.items():
                S["terrace_ratios"][f"{surf}|L{L}|{mode}"] = dict(
                    h_A=d["h_A"], theta_mrad=(d["theta"] * 1e3).tolist(),
                    residual_rad=d["residual_rad"].tolist(), amp_ratio=d["amp_ratio"].tolist(),
                    uncertainty_rad=d["uncertainty_rad"].tolist(),
                    max_abs_residual_rad=float(np.max(np.abs(d["residual_rad"]))) if len(d["theta"]) else None)
    S["bragg_conditions"] = {s: dict(V0_parametrization=bragg_angles(s, V0p) if V0p else None,
                                     V0_assumed_12V=bragg_angles(s, V0_assumed))
                             for s in ("si111_110", "si001_110")}
    S["V0_parametrization_V"] = V0p
    return S, arrays


# --------------------------------------------------------------------------
# steps stage: images from the detector spectra
# --------------------------------------------------------------------------

def image_from_spectrum(w, z_s, x_ref, theta_center, aperture):
    """Image wave psi(x_ref, y, z_s) from the stored up-going detector spectrum U
    (field amplitude referred to x = 0), through a circular objective aperture of
    semi-angle `aperture` (rad) centred on the specular direction (theta_center, 0):

      psi = sum_{kappa, qy} U(kappa, qy) exp(i K_x x_ref) exp(i kappa z_s)
            exp(2 pi i qy y) dkappa / (2 pi).

    Returns (len(z_s), n_qy) coefficients of exp(2 pi i qy y) and the qy values."""
    kap = np.asarray(w["spec_kappa"])
    qy = np.asarray(w["spec_qy"])
    S = np.asarray(w["spectrum"]).astype(complex)
    dk = kap[1] - kap[0]
    kz = K + kap
    ky = 2 * np.pi * qy
    Kx2 = K**2 - kz[:, None] ** 2 - ky[None, :] ** 2
    ok = Kx2 > 0
    Kx = np.sqrt(np.where(ok, Kx2, 0.0))
    thx = np.arcsin(np.clip(Kx / K, 0, 1))
    thy = np.arcsin(np.clip(ky / K, -1, 1))[None, :]
    ap = ok & ((thx - theta_center) ** 2 + thy**2 <= aperture**2)
    T = S * ap * np.exp(1j * Kx * x_ref) * dk / (2 * np.pi)
    E = np.exp(1j * np.outer(z_s, kap))
    return E @ T, qy


def synthesize_y(psi_q, qy, Ly, Ny_out):
    y = np.arange(Ny_out) * Ly / Ny_out
    return y, psi_q @ np.exp(2j * np.pi * np.outer(qy, y))


def angle_resolved_profile(w, Ly, Ny_out, qy_max=None, y0=0.0):
    """r(y; theta) at the surface plane from the stored exact plane-wave response
    rho(theta, qy) (simulate: vdp_angle_resolved).  qy_max optionally low-passes the
    profile (below the first surface rod it shows the step-induced envelope)."""
    rho = np.asarray(w["ar_rho"]).astype(complex)
    qy = np.asarray(w["ar_qy"])
    if qy_max is not None:
        rho = rho * (np.abs(qy) <= qy_max)[None, :]
    y = y0 + np.arange(Ny_out) * Ly / Ny_out
    return np.asarray(w["ar_theta"]), y, rho @ np.exp(2j * np.pi * np.outer(qy, y))


def _strip_mean(r, y, lo, hi, Py):
    """Mean over an integer number of y periods centred in [lo, hi] (None if the
    strip is shorter than one period): a partial period would mix in the
    non-specular rods."""
    n = int(np.floor((hi - lo) / Py + 1e-9))
    if n < 1:
        return None
    c = 0.5 * (lo + hi)
    sel = (y >= c - 0.5 * n * Py) & (y < c + 0.5 * n * Py)
    return r[:, sel].mean(axis=1)


def _beam_of(res):
    from .beams import GaussianSheetBeam
    b = res["beams"][0]
    return GaussianSheetBeam(b["theta0_mrad"] * 1e-3, b["w0_A"], 0.0, b["z_hit_A"])


def aggregate_steps(results, bm):
    """Steps parallel to the beam: angle-resolved plane-wave profiles r(y; theta)
    (no smearing by the beam's angular spread), the step phase and its dynamical
    residual far from the risers versus angle, the strip-versus-flat null test, and
    the near-riser deviation profile.  Steps transverse to the beam: image waves
    through objective apertures, each side divided by the flat-terrace image of its
    own level with the same beam, so that only the riser's influence and the shadow
    remain; the flat images give the step phase at the beam's central angle."""
    from .geometry import shadow_length
    refs = {}
    steps = []
    for res in results:
        t = res["task"]
        if t["kind"] == "flat_rocking":
            key = (t["surface"], t["structure"]["level"], t["structure"].get("clearance_level"),
                   t["beams"][0]["theta0_mrad"], t["beams"][0]["w0_A"], t["numerics"]["Nx"])
            refs[key] = res
        else:
            steps.append(res)
    S = dict(parallel={}, transverse={})
    arrays = {}
    a = 5.4309
    wmin = bm["weight_min"]
    for res in steps:
        t = res["task"]
        st = t["structure"]
        lev = st["levels"]
        th0 = t["beams"][0]["theta0_mrad"] * 1e-3
        w = res["windows"][0]
        cell = SurfaceCell(t["surface"], a)
        hu = h_unit(t["surface"])
        rkey = lambda L: (t["surface"], L, max(lev), t["beams"][0]["theta0_mrad"],  # noqa: E731
                          t["beams"][0]["w0_A"], t["numerics"]["Nx"])
        name = (f"{t['surface']}|{st['kind']}|{lev}|{1e3 * th0:.1f}mrad|{t.get('mode')}"
                f"|seed{t.get('seed')}")
        if st["kind"] == "steps_parallel":
            Py = cell.periods[1]
            Ly = Py * st.get("n_y_periods", 1)
            Ny_out = int(max(64, round(Ly / 0.25)))
            theta, y, r = angle_resolved_profile(w, Ly, Ny_out)
            m = np.interp(theta, w["theta"], w["weight"]) >= wmin
            theta, r = theta[m], r[m]
            ex = min(bm["image"]["edge_exclusion_A"], Ly / 8)
            r0 = _strip_mean(r, y, ex, Ly / 2 - ex, Py)
            r1 = _strip_mean(r, y, Ly / 2 + ex, Ly - ex, Py)
            h = hu * (lev[1] - lev[0])
            geo = -2.0 * K * np.sin(theta) * h
            entry = dict(h_A=h, theta_mrad=(theta * 1e3).tolist(), edge_exclusion_A=ex,
                         geometric_phase_rad=geo.tolist())
            if r0 is not None and r1 is not None:
                resid = np.angle(r1 / r0 * np.exp(-1j * geo))
                entry.update(step_phase_rad=np.angle(r1 / r0).tolist(), residual_rad=resid.tolist(),
                             abs_r_strip0=np.abs(r0).tolist(), abs_r_strip1=np.abs(r1).tolist())
                for L, rs in ((lev[0], r0), (lev[1], r1)):
                    ref = refs.get(rkey(L))
                    if ref is None:
                        continue
                    wr = ref["windows"][0]
                    kr = dict(zip(np.round(wr["theta"] * 1e5).astype(int), wr["r"]))
                    rf = np.array([kr.get(int(k), np.nan) for k in np.round(theta * 1e5)])
                    ok = np.isfinite(rf) & (np.abs(rf) >= bm["rung3_null"]["min_abs_r"])
                    entry[f"strip_vs_flat_level{L}_max_abs_dev"] = (
                        float(np.max(np.abs(rs - rf)[ok])) if ok.any() else None)
            # step-induced envelope: profile low-passed below the first surface rod
            _, _, rl = angle_resolved_profile(w, Ly, Ny_out, qy_max=0.5 / Py)
            rl = rl[m]
            entry["y_A"] = y.tolist()
            entry["envelope_abs_mean_over_theta"] = np.abs(rl).mean(axis=0).tolist()
            S["parallel"][name] = entry
            arrays[name] = dict(theta=theta, y=y, r=r.astype(np.complex64),
                                envelope=rl.astype(np.complex64))
        else:
            b = res["beams"][0]
            zc = float(b["z_hit_A"])
            half = 4.5 * float(b["w0_A"]) / np.tan(th0) * bm["image"]["footprint_fraction"]
            z_s = np.linspace(zc - half, zc + half, 1601)
            edge = st["edges_z_A"][0]
            h = hu * (lev[1] - lev[0])
            L_sh = float(shadow_length(abs(h), th0))
            refL = [refs.get(rkey(L)) for L in lev]
            for apm in bm["image"]["aperture_semi_angles_mrad"]:
                ap = apm * 1e-3
                pq, qy = image_from_spectrum(w, z_s, 0.0, th0, ap)
                img = pq[:, int(np.argmin(np.abs(qy)))]
                entry = dict(h_A=h, edge_z_A=edge, shadow_length_geometric_A=L_sh,
                             aperture_mrad=apm, beam_w0_A=float(b["w0_A"]),
                             beam_angular_halfwidth_mrad=1e3 * LAM / (np.pi * float(b["w0_A"])),
                             step_phase_smear_per_mrad_rad=float(2 * K * abs(h) * np.cos(th0) * 1e-3),
                             z_s_A=z_s.tolist())
                if all(r_ is not None for r_ in refL):
                    flats = []
                    for r_ in refL:
                        pr, qyr = image_from_spectrum(r_["windows"][0], z_s, 0.0, th0, ap)
                        flats.append(pr[:, int(np.argmin(np.abs(qyr)))])
                    local = np.where(z_s < edge, flats[0], flats[1])
                    ratio = img / local
                    flat_step = np.angle(flats[1] / flats[0])
                    jc = int(np.argmin(np.abs(z_s - edge)))
                    entry.update(local_ratio_amplitude=np.abs(ratio).tolist(),
                                 local_ratio_phase=np.angle(ratio).tolist(),
                                 flat_image_step_phase_at_edge_rad=float(flat_step[jc]),
                                 geometric_phase_wrapped=float(np.angle(np.exp(-2j * K * np.sin(th0) * h))),
                                 riser_influence_upstream_A=_influence(z_s, ratio, edge, -1),
                                 riser_influence_downstream_A=_influence(z_s, ratio, edge, +1))
                    arrays[name + f"|ap{apm}"] = dict(z_s=z_s, ratio=ratio.astype(np.complex64),
                                                      img=img.astype(np.complex64))
                S["transverse"][name + f"|ap{apm}"] = entry
    return S, arrays


def _influence(z_s, ratio, edge, side, tol=0.05):
    """Distance from the edge over which |ratio - 1| exceeds tol on one side."""
    sel = (z_s - edge) * side > 0
    d = np.abs(z_s[sel] - edge)
    bad = np.abs(ratio[sel] - 1) > tol
    return float(d[bad].max()) if bad.any() else 0.0


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return _jsonable(o.tolist())
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, complex):
        return [o.real, o.imag]
    return o


def plots(stage, arrays, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:  # noqa: BLE001
        return []
    files = []
    if stage == "rocking":
        surfaces = sorted({k.split("|")[0] for k in arrays})
        for s in surfaces:
            fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
            for name, d in sorted(arrays.items()):
                if not name.startswith(s) or not name.endswith("|default"):
                    continue
                lab = "|".join(name.split("|")[1:3])
                ax[0].plot(d["theta"] * 1e3, np.abs(d["r"]), lw=0.8, label=lab)
                ax[1].plot(d["theta"] * 1e3, np.angle(d["r"]), ".", ms=1, label=lab)
            ax[0].set_ylabel("|r|")
            ax[1].set_ylabel("arg r (rad)")
            ax[1].set_xlabel("external glancing angle (mrad)")
            ax[0].legend(fontsize=7)
            ax[0].set_title(f"{s}: specular reflection coefficient, 200 keV")
            f = os.path.join(out_dir, f"rocking_{s}.png")
            fig.savefig(f, dpi=130)
            plt.close(fig)
            files.append(f)
    if stage == "steps":
        for name, d in arrays.items():
            fig, ax = plt.subplots(1, 2, figsize=(11, 4))
            if "r" in d:          # parallel steps: angle-resolved profiles
                ext = [d["y"][0], d["y"][-1], d["theta"][0] * 1e3, d["theta"][-1] * 1e3]
                ax[0].imshow(np.abs(d["r"]), aspect="auto", origin="lower", extent=ext)
                ax[0].set_title("|r(y; theta)|")
                ax[1].imshow(np.angle(d["r"]), aspect="auto", origin="lower", extent=ext, cmap="twilight")
                ax[1].set_title("arg r(y; theta)")
                for a_ in ax:
                    a_.set_xlabel("y across the steps (A)")
                    a_.set_ylabel("glancing angle (mrad)")
            else:                 # transverse steps: image divided by the local flat image
                zs = d["z_s"]
                ax[0].plot(zs, np.abs(d["ratio"]))
                ax[0].set_title("|image / flat image of the local terrace|")
                ax[1].plot(zs, np.angle(d["ratio"]))
                ax[1].set_title("phase (rad)")
                for a_ in ax:
                    a_.set_xlabel("z_s along the beam (A)")
            fig.suptitle(name, fontsize=8)
            f = os.path.join(out_dir, "step_" + name.replace("|", "_").replace(" ", "").replace(",", "") + ".png")
            fig.savefig(f, dpi=110)
            plt.close(fig)
            files.append(f)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--stage", required=True, choices=("validation", "convergence", "rocking", "steps"))
    ap.add_argument("--benchmarks", default=os.path.join(os.path.dirname(__file__), "..", "configs", "benchmarks.yaml"))
    args = ap.parse_args(argv)
    import yaml
    bm = yaml.safe_load(open(args.benchmarks))
    results = load_stage(args.run_dir, args.stage)
    out_dir = os.path.join(args.run_dir, "summary", args.stage)
    os.makedirs(out_dir, exist_ok=True)
    arrays = {}
    if args.stage == "validation":
        S = aggregate_validation(results, bm)
    elif args.stage == "convergence":
        S = aggregate_convergence(results, bm)
    elif args.stage == "rocking":
        S, arrays = aggregate_rocking(results, bm)
    else:
        S, arrays = aggregate_steps(results, bm)
    S["n_results"] = len(results)
    with open(os.path.join(out_dir, "summary.json"), "w") as fh:
        json.dump(_jsonable(S), fh, indent=1)
    if arrays:
        np.savez_compressed(os.path.join(out_dir, "arrays.npz"),
                            **{f"{k}::{kk}": vv for k, v in arrays.items() for kk, vv in v.items()})
    files = plots(args.stage, arrays, out_dir)
    print(f"{args.stage}: {len(results)} results -> {out_dir}/summary.json; {len(files)} figures")
    if "all_pass" in S:
        print("validation all_pass =", S["all_pass"])


if __name__ == "__main__":
    main()
