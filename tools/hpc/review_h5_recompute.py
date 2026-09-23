#!/usr/bin/env python
"""H5: adversarial review of agent H2's supercell sizing (docs/agent_reports/H2_realistic_supercell_sizing.md,
tools/hpc/supercell_sizing.py). Independent recomputation: written WITHOUT reading H2's implementation of
any quantity; it calls only the repository's engine, builders and constants (and abTEM's Kirkland table).

Every number cited in docs/agent_reports/H5_sizing_review.md is printed by this script.

Modes (run from the repository root):
    venv/bin/python tools/hpc/review_h5_recompute.py                    # report mode (reads the JSONs below)
    venv/bin/python tools/hpc/review_h5_recompute.py --rerun  OUT.json  # engine rerun of H2's bu_100_r010 strip
    venv/bin/python tools/hpc/review_h5_recompute.py --memtime OUT.json # memory (tracemalloc) and timing probes
Stored outputs read by the report mode: tools/hpc/review_h5_rerun.json, tools/hpc/review_h5_memtime.json.

Conventions: docs/physics_conventions.md (exp(+i k.r); angular k, K, G, q, eta, c in rad/A; g, f in cycles/A;
theta = glancing angle; x = outward normal). Labels: DERIVED_HERE (formula recomputed here), REPRODUCED
(engine executed here, output saved), UNVERIFIED as stated.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import integrate, special

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from reflection_holo.constants import (A_SI_A, C_M_S, DIAMOND_BASIS, ELEM_CHARGE_C,  # noqa: E402
                                       HC_EV_M, M_E_C2_EV, PLANCK_J_S)

H2_MEAS = REPO / "tools" / "hpc" / "supercell_sizing_measurements.json"
H2_CAL = REPO / "tools" / "hpc" / "supercell_sizing_cpu_calibration.json"
RERUN_JSON = REPO / "tools" / "hpc" / "review_h5_rerun.json"
MEMTIME_JSON = REPO / "tools" / "hpc" / "review_h5_memtime.json"

E_KEV = 200.0
a = A_SI_A
OMEGA = a ** 3
Q = a / 4.0                      # (001) layer spacing = [100] slice thickness
CHECKS = []


def hdr(t):
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)


def check(name, ok, msg):
    CHECKS.append((name, bool(ok)))
    print(f"  CHECK {'PASS' if ok else 'FAIL'} {name}: {msg}")


# ------------------------------------------------------------------------------------------------
# 1. Beam constants (own formulas from the constants module)
# ------------------------------------------------------------------------------------------------
T = E_KEV * 1e3                                        # eV
HC_EV_A = HC_EV_M * 1e10
LAM = HC_EV_A / np.sqrt(T * (T + 2 * M_E_C2_EV))       # A
K = 2 * np.pi / LAM                                    # rad/A
SIGMA = 2 * np.pi * (T + M_E_C2_EV) * LAM / HC_EV_A ** 2   # rad/(V A)  (m_rel e lambda / hbar^2 form)
# h^2/(2 pi m0 e) in V A^2 (converts an electron scattering factor f_e (A) into V A^3)
M0_KG = M_E_C2_EV * ELEM_CHARGE_C / C_M_S ** 2
C_FE = PLANCK_J_S ** 2 / (2 * np.pi * M0_KG * ELEM_CHARGE_C) * 1e20


def delta_exact(V0):
    """(k_int^2 - k^2)/k^2, exact relativistic (physics_conventions)."""
    return V0 * (2 * (T + M_E_C2_EV) + V0) / (T * (T + 2 * M_E_C2_EV))


def theta_ext_for_internal_bragg(g_normal_cyc, V0):
    """External glancing angle whose refracted wave satisfies 2 K sin(theta_int) = G (own solve)."""
    D = delta_exact(V0)
    Kin = K * np.sqrt(1 + D)
    s_int = 2 * np.pi * g_normal_cyc / (2 * Kin)
    s_ext2 = s_int ** 2 * (1 + D) - D
    return float(np.arcsin(np.sqrt(s_ext2))), float(np.arcsin(s_int))


# ------------------------------------------------------------------------------------------------
# 2. Kirkland Fourier coefficients: two independent routes
# ------------------------------------------------------------------------------------------------
def kirkland_params_si():
    from abtem import parametrizations as ap
    base = os.path.dirname(ap.__file__)
    p = np.array(json.load(open(os.path.join(base, "data", "kirkland.json")))["Si"], float)
    return p            # rows a_i, b_i, c_i, d_i (Kirkland's f_e(q) = sum a/(q^2+b) + c exp(-d q^2))


P_SI = kirkland_params_si()


def fe_kirkland(q2):
    """Kirkland electron scattering factor f_e (A) at q^2 (q in cycles/A), from the raw table."""
    q2 = np.asarray(q2, float)
    a_, b_, c_, d_ = P_SI
    return sum(a_[i] / (q2 + b_[i]) + c_[i] * np.exp(-d_[i] * q2) for i in range(3))


def abtem_F(q2):
    """The engine's route: abTEM KirklandParametrization().projected_scattering_factor('Si')(f^2), V A^3."""
    from abtem import parametrizations as ap
    fn = ap.KirklandParametrization().projected_scattering_factor("Si")
    return np.asarray(fn(np.asarray(q2, np.float64)), np.float64)


def S_cubic(hkl):
    """Structure factor of the 8-atom diamond cell, convention exp(+2 pi i h.r) (physics_conventions)."""
    h = np.asarray(hkl, float)
    return complex(np.sum(np.exp(2j * np.pi * DIAMOND_BASIS @ h)))


def V_h(hkl, route="abtem"):
    h = np.asarray(hkl, float)
    g2 = float(h @ h) / a ** 2
    if route == "abtem":
        F = float(abtem_F(np.array([g2]))[0])
    else:
        F = C_FE * float(fe_kirkland(g2))
    return S_cubic(hkl) * F / OMEGA


# ------------------------------------------------------------------------------------------------
# 3. Two-beam Bragg case (own derivation, paraxial z-evolution; see the review, section F1)
# ------------------------------------------------------------------------------------------------
def two_beam(Vg, V0, r, theta_ext):
    """Return eta0, c (complex, rad/A) and X at eta0 for proportional absorption V' = (1 + i r) V.

    z-evolution d psi/dz = (i/2k) d2psi/dx2 + i sigma V psi; two beams p, p + G; with eta = kappa0 - G/2,
    q = p + G/2: q^2 = eta^2 - c^2 (first order in eta/G), c = 2 k sigma V_g / G; B/A = X = -(eta + q)/c
    with Im q < 0 (decay into the crystal at x < 0); |X| <= 1."""
    G = 2 * np.pi * 8 / a
    kap_vac = K * np.sin(theta_ext)
    kap0 = np.sqrt(kap_vac ** 2 + 2 * K * SIGMA * V0 * (1 + 1j * r) + 0j)
    eta = kap0 - G / 2
    c = 2 * K * SIGMA * Vg * (1 + 1j * r) / G
    X = X_of_eta(eta, c)
    return eta, c, X


def X_of_eta(eta, c):
    q1 = np.sqrt(eta - c + 0j) * np.sqrt(eta + c + 0j)
    q = np.where(np.imag(q1) < 0, q1, -q1)
    # on the real axis outside the band (Im q = 0) pick |X| <= 1
    X1 = -(eta + q) / c
    X2 = -(eta - q) / c
    return np.where(np.abs(X1) <= np.abs(X2) + 1e-15, X1, X2)


def transient_E(Ls, eta0, c, theta_int, X):
    """Relative error E(L) = 1 - (1/X) int_0^s i J1(c s') exp(i eta0 s')/s' ds', s = L tan(theta_int)."""
    tt = np.tan(theta_int)
    out = []
    s_prev, acc = 0.0, 0.0 + 0j
    f = lambda s: (1j * special.jv(1, c * s) * np.exp(1j * eta0 * s) / s) if s > 0 else 0.5j * c
    for L in Ls:
        s = L * tt
        re = integrate.quad(lambda u: np.real(f(u)), s_prev, s, limit=400)[0]
        im = integrate.quad(lambda u: np.imag(f(u)), s_prev, s, limit=400)[0]
        acc += re + 1j * im
        s_prev = s
        out.append(1 - acc / X)
    return np.array(out)



# ------------------------------------------------------------------------------------------------
# 6. Many-beam bookkeeping in the transverse reciprocal plane (g component along the beam = 0)
# ------------------------------------------------------------------------------------------------
def frame_vectors(azimuth):
    """Slab frame rows in cubic coordinates: x = [001] outward normal, z = azimuth, y = z x x."""
    xh = np.array([0.0, 0.0, 1.0])
    zh = np.asarray(azimuth, float) / np.linalg.norm(azimuth)
    yh = np.cross(zh, xh)
    return xh, yh, zh


def many_beam(azimuth, V0, th_e, hmax=12):
    """Return rows (hkl, zeta, admixture, k_x, angle_y, bethe_offdiag_V) for every allowed hkl with zero
    component along the beam, using K = paraxial internal wavenumber and kappa0 = G_008/2 exactly."""
    xh, yh, zh = frame_vectors(azimuth)
    G = 2 * np.pi * 8 / a
    Kin = np.sqrt(K ** 2 + 2 * K * SIGMA * V0)
    kap0 = G / 2
    g008 = np.array([0, 0, 8])
    rows = []
    rng = range(-hmax, hmax + 1)
    for h in rng:
        for k_ in rng:
            for l in rng:
                hkl = np.array([h, k_, l])
                if abs(hkl @ zh) > 1e-9 or (h == 0 and k_ == 0 and l in (0, 8)):
                    continue
                S = S_cubic(hkl)
                if abs(S) < 1e-9:
                    continue
                gx, gy = (hkl @ xh) / a, (hkl @ yh) / a
                kx = -kap0 + 2 * np.pi * gx
                ky = 2 * np.pi * gy
                zeta = (kap0 ** 2 - kx ** 2 - ky ** 2) / (2 * Kin)
                Vh = V_h(tuple(hkl))
                Vgh = V_h(tuple(g008 - hkl))
                if abs(Vgh) < 1e-12 and abs(Vh) < 1e-12:
                    continue
                adm = SIGMA * (abs(Vh) + abs(Vgh)) / abs(zeta) if abs(zeta) > 1e-12 else np.inf
                bethe = (SIGMA * Vgh * Vh / zeta).real if abs(zeta) > 1e-12 else np.nan
                rows.append((tuple(int(v) for v in hkl), zeta, adm, kx, ky / Kin, bethe, Vh, Vgh, gx, gy))
    return rows


def bethe_missing(rows, fmax):
    """Bethe sum over beams whose coupling to 0 (|h|) or to g (|g - h|) lies outside the band fmax."""
    tot, carried = 0.0, 0.0
    for (hkl, zeta, adm, kx, ang, bethe, Vh, Vgh, gx, gy) in rows:
        if not np.isfinite(bethe):
            continue
        h = np.array(hkl, float)
        g_h = np.sqrt(h @ h) / a
        g_gh = np.sqrt((np.array([0, 0, 8]) - h) @ (np.array([0, 0, 8]) - h)) / a
        tot += bethe
        # the beam itself (transverse frequency of its wave) and both couplings must be carried
        fbeam = np.hypot(kx / (2 * np.pi), gy)
        if g_h <= fmax and g_gh <= fmax and fbeam <= fmax:
            carried += bethe
    return tot, carried



# ------------------------------------------------------------------------------------------------
# 8. Layout of H2's scenario rows, rebuilt from the RULES stated in the H2 report (sections 2.6, 3, 4, 9)
# ------------------------------------------------------------------------------------------------
def smooth7(n):
    m = int(np.ceil(n))
    while True:
        k = m
        for pr in (2, 3, 5, 7):
            while k % pr == 0:
                k //= pr
        if k == 1:
            return m
        m += 1


def layout(name, *, th, res_el, L_run, D_clean, y_mode, step_h=0.0, field=None, torus=False,
           W=None, edges="parallel", n_real=8, n_ang=1, extra_depth=0.0, ridge=0.0, ring_V=0.0):
    """Cell of one scenario from the stated rules. Returns a dict of every derived number."""
    tt = np.tan(th)
    ent = 10 * Q
    gap = 2.0
    z_contact = gap / tt
    exit_m = 3 * res_el
    Lneed = z_contact + L_run + field + exit_m
    periods = int(np.ceil((Lneed - ent) / a - 1e-12))
    Lz = ent + periods * a
    H = Lz * tt - gap - step_h - 1.0
    vac = float(np.ceil(H + Lz * tt + 1.0 + ridge))
    depth = 15.0 + D_clean + extra_depth
    ext_x = depth + step_h + vac + 10.0
    if y_mode == "staircase":
        nW = int(np.ceil(W / a - 1e-12))
        Wc = nW * a
        y = 2 * Wc
        yper = 2 * nW
    elif y_mode == "transverse":
        yper = 16
        y = 16 * a
    elif y_mode == "torus":
        yper = int(np.ceil(W / a - 1e-12))
        y = yper * a
    else:
        yper = int(y_mode)
        y = yper * a
    nx = smooth7(np.ceil(ext_x / 0.13 - 1e-9))
    ny = smooth7(np.ceil(y / 0.13 - 1e-9))
    N = int(round(Lz / Q))
    n_low = int(np.floor(depth / Q + 1e-9)) + 1           # (001) layers from the bottom to the lowest top layer
    dl = int(round(step_h / Q))                           # extra layers of the upper terrace
    per_layer_period = 2                                  # atoms per (001) layer per a x a at [100]
    if y_mode == "staircase":
        atoms = per_layer_period * periods * (yper * n_low + nW * dl)
        # atoms per slice: one (100) plane holds the layers of one parity, 1 atom per y-period per layer
        par = [(n_low + 1) // 2, n_low // 2]              # layers of each parity (0 = even from the bottom)
        up_extra = [0, 0]
        for j in range(dl):
            up_extra[(n_low + j) % 2] += 1
        slice_counts = [nW * par[pp] + nW * (par[pp] + up_extra[pp]) for pp in (0, 1)]
    elif y_mode == "transverse":
        atoms = per_layer_period * yper * periods * n_low      # patched by the caller (two terraces)
        par = [(n_low + 1) // 2, n_low // 2]
        slice_counts = [yper * par[pp] for pp in (0, 1)]
    else:
        atoms = per_layer_period * yper * periods * n_low
        par = [(n_low + 1) // 2, n_low // 2]
        slice_counts = [yper * par[pp] for pp in (0, 1)]
    ring_atoms = 0
    if torus:
        ring_atoms = int(round(ring_V * 8 / a ** 3))
        atoms += ring_atoms
    nonempty = 4 * periods
    n_mean = atoms / nonempty
    n_max = max(slice_counts) + (int(np.ceil(8765.0 * 8 / a ** 3 * Q / Q * 0)) if False else 0)
    return dict(name=name, periods=periods, Lz=Lz, H=H, vac=vac, depth=depth, ext_x=ext_x, y=y, yper=yper,
                nx=nx, ny=ny, N=N, nonempty=nonempty, atoms=int(atoms), n_mean=n_mean, n_max=int(n_max),
                n_low=n_low, z_contact=z_contact, n_real=n_real, n_ang=n_ang, ring_atoms=ring_atoms)


def engine_memory(nx, ny, n_max, n_atoms, n_species=1, cb=8):
    """Replica of estimate_resources' memory accounting, written from engine.py:361-368."""
    npx = nx * ny
    rb = cb // 2
    arrays = cb * npx * (1 + 1 + 2) + rb * npx + rb * npx * n_species + 3 * cb * npx + cb * (nx + ny) * n_max \
        + cb * npx + 48 * n_atoms
    return arrays, 48 * n_atoms


def engine_gpu_s(nx, ny, N, nonempty, n_mean, cb=8):
    """Replica of estimate_resources' GPU model (engine.py:411-418, GPU_ASSUMED constants)."""
    npx = nx * ny
    lg = np.log2(max(npx, 2))
    t_fft = max(1e-5, 2 * cb * npx * lg / 4 / (1e12 / 3))
    t_el = max(1e-5, 3 * cb * npx / 1e12)
    t_pot = max(1e-5, 8.0 * npx * n_mean / 1e13)
    per_e = 2 * t_fft + 4 * t_el
    per_f = per_e + 3 * t_fft + 6 * t_el + t_pot
    tot = (N - nonempty) * per_e + nonempty * per_f
    return tot, nonempty * t_pot / tot


def cpu_constants_from_raw():
    """Own fit of the per-operation CPU costs from the RAW entries of H2's calibration file."""
    cal = json.load(open(H2_CAL))
    big = [e for e in cal["fft"] if e["npx"] >= 1_000_000]
    c_fft = float(np.median([e["fft_s"] / (e["npx"] * np.log2(e["npx"])) for e in big]))
    c_el = float(np.median([e["elementwise_pass_s"] / e["npx"] for e in big]))
    c_exp = float(np.median([e["exp_s"] / ((e["nx"] + e["ny"]) * e["m"]) for e in cal["potential"]]))
    gemm = float(np.median([e["gemm_flops"] for e in cal["potential"]]))
    return dict(c_fft=c_fft, c_el=c_el, c_exp=c_exp, gemm=gemm, load=cal["loadavg"], created=cal["created_utc"])


def cpu_model_s(nx, ny, N, nonempty, n_mean, cc):
    """The engine's CPU composition (engine.py:394-405) with my fitted per-operation costs."""
    npx = nx * ny
    t_fft = cc["c_fft"] * npx * np.log2(npx)
    t_el = cc["c_el"] * npx
    t_pot = cc["c_exp"] * (nx + ny) * n_mean + 8.0 * npx * n_mean / cc["gemm"]
    per_e = 2 * t_fft + 4 * t_el
    per_f = per_e + 3 * t_fft + 6 * t_el + t_pot
    tot = (N - nonempty) * per_e + nonempty * per_f
    return tot, nonempty * t_pot / tot


def fmt_t(sec):
    if sec < 120:
        return f"{sec:.0f} s"
    if sec < 2 * 3600:
        return f"{sec/60:.0f} min"
    if sec < 48 * 3600:
        return f"{sec/3600:.1f} h"
    return f"{sec/86400:.1f} d"



# ------------------------------------------------------------------------------------------------
# 9. Engine rerun of a flat [100] strip with an independent surface-resolved read-out (--rerun)
# ------------------------------------------------------------------------------------------------
TEST_ABS = "TEST_ONLY: stands in for PROJECT_INPUT item 21 (H5 review rerun)"
AZ100 = "TEST_ONLY: stands in for PROJECT_INPUT item 8 (exact [100], B20) (H5 review rerun)"
TH_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7; (0,0,8) internal Bragg with the potential's MIP (H5)"


def build_flat_100(*, y_periods, z_periods, depth_below, vac, ent):
    """Flat bulk-terminated Si(001) terrace at the exact [100] azimuth: ONE z-period built by the repository
    builder (all its assertions), tiled along z (exact for a flat terrace), then build_reflection_cell."""
    import dataclasses
    import hashlib
    from reflection_holo.forward.cell import build_reflection_cell
    from reflection_holo.structure import Staircase, build_si001_terraces
    sub = int(np.ceil(depth_below / Q)) + 2
    st = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(int(y_periods),), boundary_step_layers=0)
    one = build_si001_terraces(azimuth_uvw=(1, 0, 0), azimuth_label=AZ100, staircase=st, edge_periods=1,
                               substrate_layers=sub, first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                               overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=a,
                               lattice_parameter_label="ASSUMPTION B2")
    n = one.n_atoms
    pos = np.tile(one.positions_A, (z_periods, 1))
    pos[:, 2] += np.repeat(np.arange(z_periods), n) * a
    cellA = one.cell_A.copy()
    cellA[2, 2] = z_periods * a
    md = dict(one.metadata)
    md["edge_periods"] = z_periods
    md["positions_sha256"] = hashlib.sha256(np.ascontiguousarray(pos, "<f8").tobytes()).hexdigest()
    s_ = dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, z_periods), cell_A=cellA,
                             layer_index=np.tile(one.layer_index, z_periods),
                             terrace_index=np.tile(one.terrace_index, z_periods), metadata=md)
    return build_reflection_cell(s_, vacuum_above_A=vac, depth_below_A=depth_below, bulk_absorber_A=15.0,
                                 top_absorber_A=10.0, entrance_vacuum_z_A=ent)


def strip_setup(*, r, L_after, y_periods, clean_depth, th):
    tt = np.tan(th)
    ent = 10 * Q
    gap = 2.0
    zc = gap / tt
    periods = int(np.ceil((zc + L_after - ent) / a))
    Lz = ent + periods * a
    H = Lz * tt - 3.0
    vac = float(np.ceil(H + Lz * tt + 1.0))
    depth = 15.0 + clean_depth
    cell = build_flat_100(y_periods=y_periods, z_periods=periods, depth_below=depth, vac=vac, ent=ent)
    nx = smooth7(np.ceil(cell.extent_x_A / 0.13 - 1e-9))
    ny = smooth7(np.ceil(cell.extent_y_A / 0.13 - 1e-9))
    return dict(cell=cell, Lz=Lz, H=H, vac=vac, depth=depth, periods=periods, nx=nx, ny=ny, zc=zc,
                xs=float(cell.metadata["layout"]["highest_surface_x_A"]))


def run_strip(su, *, r, th, u_rms=None, seed=None, realisation=0):
    from reflection_holo.forward.multislice import (AtomicPotential, FrozenPhonons, MultisliceParams,
                                                    NumericalAbsorber, PhysicalAbsorption, SheetBeam,
                                                    run_realisation)
    cell = su["cell"]
    ab = PhysicalAbsorption(model="proportional", ratio=float(r),
                            label=(TEST_ABS if r else "ASSUMPTION: no absorption (B30), H5 review rerun"))
    fp = None if u_rms is None else FrozenPhonons(rms_displacement_A=u_rms,
                                                   label="ASSUMPTION A7: 0.076 A per axis (H5 review rerun)")
    pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=ab, frozen_phonons=fp,
                          static_lattice_label=(None if fp else "ASSUMPTION: static lattice (H5 review rerun)"))
    beam = SheetBeam(height_A=su["H"], edge_A=2.0, x_bottom_A=su["xs"] + 2.0, theta_in_ext_rad=th,
                     theta_label=TH_LABEL)
    params = MultisliceParams(energy_keV=200.0, nx=su["nx"], ny=su["ny"], dz_A=Q, propagator="exact",
                              band_limit="2/3", backend="numpy", precision="complex64", threads=4,
                              absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                              theta_out_ext_rad=th, buildup_depth_A=20.0)
    t0 = time.time()
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=realisation,
                         seed=(None if fp is None else seed))
    return ew, time.time() - t0


def readout(ew, su, th, *, taper=(2.0, 6.0), band=0.1, bin_A=500.0):
    """Surface-resolved specular amplitude R(d), d = distance after the bottom-edge contact point:
    y-average, vacuum mask (sin^2 from xs + taper[0] to xs + taper[1]), pass band |f - f_c| <= band,
    demodulation by exp(-2 pi i f_c x); ray mapping z_s = L_z - (x - xs)/tan(theta_ext)."""
    psi = ew.psi.astype(np.complex128)
    nx = psi.shape[0]
    x = ew.x0_A + np.arange(nx) * ew.dx_A
    xs = su["xs"]
    col = psi.mean(axis=1)
    u = np.clip((x - xs - taper[0]) / (taper[1] - taper[0]), 0, 1)
    m = np.sin(0.5 * np.pi * u) ** 2
    fc = np.sin(th) / LAM
    F = np.fft.fft(col * m)
    f = np.fft.fftfreq(nx, ew.dx_A)
    F[np.abs(f - fc) > band] = 0
    R = np.fft.ifft(F) * np.exp(-2j * np.pi * fc * x)
    zs = su["Lz"] - (x - xs) / np.tan(th)
    d = zs - su["zc"]
    top = float(ew.metadata["absorbers"]["top_absorber_x_A"][0])
    ok = (x > xs + taper[1]) & (x < top - 1.0) & (d >= 0)
    d, R = d[ok], R[ok]
    d_end = su["Lz"] - su["zc"]
    edges = np.arange(0.0, d_end + 1e-9, bin_A)
    bins = []
    for lo in edges:
        sel = (d >= lo) & (d < lo + bin_A)
        if np.count_nonzero(sel) >= 3:
            bins.append((float(lo), complex(R[sel].mean())))
    pl = (d >= d_end - 750 - 2500) & (d < d_end - 750)
    Rpl = complex(R[pl].mean())
    # depth profile of the exit-plane intensity below the top layer
    I = np.mean(np.abs(psi) ** 2, axis=1)
    depth = xs - x
    prof = {}
    for dd in range(0, 101, 10):
        prof[dd] = float(np.interp(dd, depth[::-1], I[::-1]))
    deepest = {}
    absorber_top = float(ew.metadata["absorbers"]["bulk_absorber_x_A"][1])
    for thr in (1e-2, 1e-4, 1e-6):
        sel = (depth >= 0) & (x > absorber_top) & (I > thr)
        deepest[thr] = float(depth[sel].max()) if np.any(sel) else 0.0
    return dict(bins=bins, R_plateau=Rpl, d_end=d_end, profile=prof, deepest=deepest,
                d_fine=d.tolist()[::5], R_fine=[[float(v.real), float(v.imag)] for v in R[::5]])


def converged_beyond(bins, Rpl, d_end, tol_ph, tol_amp):
    """Smallest bin start L such that every bin starting at >= L and ending before the plateau end is
    within the tolerance (phase in rad, amplitude relative)."""
    end = d_end - 750
    rows = [(lo, R) for lo, R in bins if lo + 500 <= end + 1e-6]
    Lph = Lam = None
    for i, (lo, _) in enumerate(rows):
        later = rows[i:]
        if Lph is None and all(abs(np.angle(R / Rpl)) <= tol_ph for _, R in later):
            Lph = lo
        if Lam is None and all(abs(abs(R) / abs(Rpl) - 1) <= tol_amp for _, R in later):
            Lam = lo
    return Lph, Lam


def rerun_mode(out_path, which):
    th_e, th_i = theta_ext_for_internal_bragg(8 / a, 8 * float(abtem_F(np.array([0.0]))[0]) / OMEGA)
    res = dict(schema="H5/rerun/1", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               loadavg_start=list(os.getloadavg()), runs={})
    if Path(out_path).exists():
        res = json.load(open(out_path))
    if "static" in which:
        su = strip_setup(r=0.1, L_after=6000.0, y_periods=2, clean_depth=100.0, th=th_e)
        ew, dt = run_strip(su, r=0.1, th=th_e)
        ro = {}
        for tp in ((2.0, 6.0), (2.0, 4.0), (2.0, 10.0)):
            o = readout(ew, su, th_e, taper=tp)
            ro[f"{tp[0]}-{tp[1]}"] = dict(bins=[[lo, R.real, R.imag] for lo, R in o["bins"]],
                                          R_plateau=[o["R_plateau"].real, o["R_plateau"].imag], d_end=o["d_end"],
                                          profile=o["profile"], deepest={str(k): v for k, v in o["deepest"].items()},
                                          d_fine=o["d_fine"], R_fine=o["R_fine"])
        res["runs"]["bu_100_r010_h5"] = dict(n_atoms=int(len(su["cell"].Z)), nx=su["nx"], ny=su["ny"],
                                             Lz=su["Lz"], H=su["H"], vac=su["vac"], periods=su["periods"],
                                             n_slices=int(round(su["Lz"] / Q)), run_s=dt,
                                             loadavg_after=list(os.getloadavg()), readouts=ro,
                                             validation_status=ew.metadata["validation_status"])
        json.dump(res, open(out_path, "w"), indent=1)
        print(f"static run done in {dt:.0f} s")
    if "fp" in which:
        # frozen phonons on the same 6000 A strip (H2's fp run was 3000 A long): static + 8 realisations
        su = strip_setup(r=0.1, L_after=6000.0, y_periods=2, clean_depth=60.0, th=th_e)
        runs = []
        ew0, dt0 = run_strip(su, r=0.1, th=th_e)
        o0 = readout(ew0, su, th_e)
        for k in range(8):
            ew, dt = run_strip(su, r=0.1, th=th_e, u_rms=0.076, seed=20260923, realisation=k)
            o = readout(ew, su, th_e)
            runs.append(dict(bins=[[lo, R.real, R.imag] for lo, R in o["bins"]], R_fine=o["R_fine"], run_s=dt))
            print(f"fp realisation {k} done in {dt:.0f} s", flush=True)
        res["runs"]["fp_100_r010_6000_h5"] = dict(
            n_atoms=int(len(su["cell"].Z)), nx=su["nx"], ny=su["ny"], Lz=su["Lz"], d_end=o0["d_end"],
            static=dict(bins=[[lo, R.real, R.imag] for lo, R in o0["bins"]], R_fine=o0["R_fine"], run_s=dt0),
            d_fine=o0["d_fine"], realisations=runs, u_rms_A=0.076, seed=20260923, loadavg_after=list(os.getloadavg()))
        json.dump(res, open(out_path, "w"), indent=1)



# ------------------------------------------------------------------------------------------------
# 10. Memory (tracemalloc) and timing probes of the engine (--memtime)
# ------------------------------------------------------------------------------------------------
def memtime_mode(out_path):
    import tracemalloc
    from reflection_holo.forward.multislice import (AtomicPotential, FrozenPhonons, MultisliceParams,
                                                    NumericalAbsorber, PhysicalAbsorption, estimate_resources)
    from reflection_holo.forward.multislice.backend import get_backend
    from reflection_holo.forward.multislice.engine import propagate_slices
    from reflection_holo.forward.multislice.grid import band_limit_mask, make_grid
    from reflection_holo.forward.multislice.potentials import absorber_profile_V
    from reflection_holo.forward.multislice.propagator import propagator_kernel
    out = dict(schema="H5/memtime/1", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               loadavg_start=list(os.getloadavg()))
    ab = PhysicalAbsorption(model="proportional", ratio=0.1, label=TEST_ABS)
    be = get_backend("numpy", "complex64", 4)
    ent = 10 * Q

    def params_for(cell):
        nx = smooth7(np.ceil(cell.extent_x_A / 0.13 - 1e-9))
        ny = smooth7(np.ceil(cell.extent_y_A / 0.13 - 1e-9))
        return MultisliceParams(energy_keV=200.0, nx=nx, ny=ny, dz_A=Q, propagator="exact", band_limit="2/3",
                                backend="numpy", precision="complex64", threads=4,
                                absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                                theta_out_ext_rad=0.0161347, buildup_depth_A=20.0)

    # (a) host bytes per atom while realising: atom-heavy, pixel-light cell
    cell = build_flat_100(y_periods=2, z_periods=2000, depth_below=140.0, vac=40.0, ent=ent)
    prm = params_for(cell)
    grid = make_grid(cell, nx=prm.nx, ny=prm.ny)
    N = int(round(cell.length_z_A / Q))
    nat = int(len(cell.Z))
    rec = {}
    for tag, fp in (("static", None), ("frozen", FrozenPhonons(rms_displacement_A=0.076, label="ASSUMPTION A7 (H5)"))):
        pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=ab, frozen_phonons=fp,
                              static_lattice_label=(None if fp else "ASSUMPTION: static lattice (H5)"))
        npx_bytes = 4 * prm.nx * prm.ny + 8 * (prm.nx + prm.ny)       # F (float32) and fx64, fy64
        tracemalloc.start()
        base = tracemalloc.get_traced_memory()[0]
        rl = pot.realise(grid=grid, dz_A=Q, n_slices=N, backend=be,
                         rng=(np.random.default_rng([20260923, 0]) if fp else None))
        cur, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rec[tag] = dict(n_atoms=nat, peak_B_per_atom=(peak - base - npx_bytes) / nat,
                        persistent_B_per_atom=(cur - base - npx_bytes) / nat)
        del rl
    cell_B = (cell.atoms_xyz_A.nbytes + cell.Z.nbytes) / nat
    out["host_per_atom"] = dict(rec, cell_arrays_B_per_atom=cell_B, n_atoms=nat)
    del cell

    # (b) one wide slice: memory transients of projected(i) and its time, against estimate_resources
    cell = build_flat_100(y_periods=96, z_periods=2, depth_below=140.0, vac=40.0, ent=ent)
    prm = params_for(cell)
    grid = make_grid(cell, nx=prm.nx, ny=prm.ny)
    N = int(round(cell.length_z_A / Q))
    pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=ab, frozen_phonons=None,
                          static_lattice_label="ASSUMPTION: static lattice (H5)")
    rl = pot.realise(grid=grid, dz_A=Q, n_slices=N, backend=be, rng=None)
    counts = np.diff(rl.starts)
    i_max = int(np.argmax(counts))
    n_max = int(counts[i_max])
    est = estimate_resources(cell, prm, realisations=1, calibrate_cpu=True)
    V = rl.projected(i_max)                                   # warm-up
    del V
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    V = rl.projected(i_max)
    cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del V
    ts = []
    for _ in range(3):
        t0 = time.perf_counter()
        V = rl.projected(i_max)
        ts.append(time.perf_counter() - t0)
        del V
    t_proj = float(np.median(ts))
    # the full slice loop of the engine on this cell (N slices, 8 of them non-empty)
    lam = LAM
    mask = band_limit_mask(grid, "2/3")
    P_full, _ = propagator_kernel(grid, dz_A=Q, wavelength_A=lam, kind="exact", band_mask=mask)
    P_half, _ = propagator_kernel(grid, dz_A=0.5 * Q, wavelength_A=lam, kind="exact", band_mask=mask)
    P_full = be.asarray(P_full, dtype=be.complex_dtype)
    P_half = be.asarray(P_half, dtype=be.complex_dtype)
    maskb = be.asarray(mask, dtype=be.real_dtype)
    W = absorber_profile_V(grid, cell, prm.absorber)
    absfac = be.asarray(np.exp(-SIGMA * W * Q)[:, None], dtype=be.real_dtype)
    psi = be.asarray(np.ones(grid.shape), dtype=be.complex_dtype)
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    t0 = time.perf_counter()
    psi, nb = propagate_slices(psi, realised=rl, n_slices=N, backend=be, P_full=P_full, P_half=P_half,
                               band_mask=maskb, sigma=be.real_dtype(SIGMA), absorber_factor=absfac)
    t_loop = time.perf_counter() - t0
    cur2, peak2 = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    nonempty = int(np.count_nonzero(counts))
    out["wide_slice"] = dict(nx=prm.nx, ny=prm.ny, n_atoms=int(len(cell.Z)), n_max=n_max, N=N, nonempty=nonempty,
                             projected_peak_B=peak - base, projected_s_median=t_proj, projected_s_all=ts,
                             loop_s=t_loop, loop_peak_B=peak2 - base, transmission_built=int(nb),
                             estimate_memory=est["memory_bytes"], estimate_cpu=est["cpu"],
                             loadavg=list(os.getloadavg()))
    json.dump(out, open(out_path, "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float)[:3000])



# ------------------------------------------------------------------------------------------------
# 11. Built cells: the engine's own estimate_resources and reflection_setup against H2's table
# ------------------------------------------------------------------------------------------------
def build_staircase_100(*, nW, dl_layers, z_periods, depth_below, vac, ent):
    """a/4 (dl = 1) or a/2 (dl = 2) up-down staircase at [100], edges parallel to the beam, two terraces of
    nW periods; one z-period built by the repository builder, tiled along z (exact: uniform along z)."""
    import dataclasses
    from reflection_holo.forward.cell import build_reflection_cell
    from reflection_holo.structure import Staircase, build_si001_terraces
    sub = int(np.ceil(depth_below / Q)) + 2
    st = Staircase(edges="parallel", terrace_layers=(0, dl_layers), terrace_widths=(nW, nW),
                   boundary_step_layers=-dl_layers)
    one = build_si001_terraces(azimuth_uvw=(1, 0, 0), azimuth_label=AZ100, staircase=st, edge_periods=1,
                               substrate_layers=sub, first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                               overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=a,
                               lattice_parameter_label="ASSUMPTION B2")
    n = one.n_atoms
    pos = np.tile(one.positions_A, (z_periods, 1))
    pos[:, 2] += np.repeat(np.arange(z_periods), n) * a
    cellA = one.cell_A.copy()
    cellA[2, 2] = z_periods * a
    md = dict(one.metadata)
    md["edge_periods"] = z_periods
    s_ = dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, z_periods), cell_A=cellA,
                             layer_index=np.tile(one.layer_index, z_periods),
                             terrace_index=np.tile(one.terrace_index, z_periods), metadata=md)
    return build_reflection_cell(s_, vacuum_above_A=vac, depth_below_A=depth_below, bulk_absorber_A=15.0,
                                 top_absorber_A=10.0, entrance_vacuum_z_A=ent)


def engine_check_cell(cell, *, th, H, n_real, label):
    from reflection_holo.forward.multislice import (AtomicPotential, MultisliceParams, NumericalAbsorber,
                                                    PhysicalAbsorption, SheetBeam, estimate_resources)
    from reflection_holo.forward.multislice.engine import reflection_setup
    nx = smooth7(np.ceil(cell.extent_x_A / 0.13 - 1e-9))
    ny = smooth7(np.ceil(cell.extent_y_A / 0.13 - 1e-9))
    prm = MultisliceParams(energy_keV=200.0, nx=nx, ny=ny, dz_A=Q, propagator="exact", band_limit="2/3",
                           backend="numpy", precision="complex64", threads=4,
                           absorber=NumericalAbsorber(strength_V=100.0, profile="sin2"),
                           theta_out_ext_rad=th, buildup_depth_A=20.0)
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(model="proportional", ratio=0.1, label=TEST_ABS),
                          frozen_phonons=None, static_lattice_label="ASSUMPTION: static lattice (H5)")
    lay = cell.metadata["layout"]
    beam = SheetBeam(height_A=H, edge_A=2.0, x_bottom_A=lay["highest_surface_x_A"] + 2.0, theta_in_ext_rad=th,
                     theta_label=TH_LABEL)
    setup = reflection_setup(cell, potential=pot, beam=beam, params=prm)
    est = estimate_resources(cell, prm, realisations=n_real, calibrate_cpu=False)
    counts = np.bincount(np.clip(np.floor((cell.atoms_xyz_A[:, 2] + 1e-9) / Q).astype(int), 0, None),
                         minlength=int(round(cell.length_z_A / Q)))
    ne = int(np.count_nonzero(counts))
    mem, _ = engine_memory(nx, ny, int(counts.max()), int(len(cell.Z)))
    g, _ = engine_gpu_s(nx, ny, int(round(cell.length_z_A / Q)), ne, float(counts[counts > 0].mean()))
    passed = [k for k, v in setup["geometry"].items() if isinstance(v, dict) and v.get("passed")]
    print(f"  [{label}] built: {len(cell.Z):,} atoms, extent_x {cell.extent_x_A:.3f} A, y {cell.extent_y_A:.2f} A, "
          f"L_z {cell.length_z_A:.2f} A, grid {nx}x{ny}, slices {est['n_slices']} (non-empty {est['nonempty_slices']}), "
          f"n_max {est['atoms_per_slice_max']}, n_mean {est['atoms_per_nonempty_slice_mean']:.1f}")
    print(f"      engine estimate_resources: {est['memory_bytes']['total']:,} B, GPU {est['gpu']['seconds_per_realisation']:.4f} s "
          f"per realisation; my replica: {mem:,} B, GPU {g:.4f} s; engine geometry assertions passed: {len(passed)} "
          f"({', '.join(passed)})")
    return est, mem, g, setup


def study_point_checks():
    sys.path.insert(0, str(REPO / "tests" / "forward"))
    from null_test_cases import step_case, theta_0008, translation_pair
    from reflection_holo.forward.multislice import PhysicalAbsorption, estimate_resources
    th = theta_0008()
    m2 = {"tfix_bragg_abs0_L0": (640, 60, 1434, 19224, 4, 0.3), "tfix_off20_abs10_L5k": (1440, 60, 6406, 86346, 11, 1.7),
          "step_w32_bragg_abs10_L5k": (1260, 1920, 6642, 2971136, 340, 22.8)}
    rows = []
    for name, kind, theta, extra, wp, r in (("tfix_bragg_abs0_L0", "t", th, 0.0, 2, 0.0),
                                            ("tfix_off20_abs10_L5k", "t", 20e-3, 5000.0, 2, 0.1),
                                            ("step_w32_bragg_abs10_L5k", "s", th, 5000.0, 32, 0.1)):
        ab = PhysicalAbsorption(model="proportional", ratio=r,
                                label=("ASSUMPTION: no absorption" if r == 0 else TEST_ABS))
        if kind == "t":
            pair = translation_pair(theta=theta, width_periods=wp, extra_A=extra, absorption=ab, precision="complex64")
            cell, prm, nrun = pair["A"][0], pair["params"], 2
        else:
            cell, _, _, prm = step_case(theta=theta, width_periods=wp, extra_A=extra, absorption=ab,
                                        precision="complex64")
            nrun = 1
        est = estimate_resources(cell, prm, realisations=nrun, calibrate_cpu=False)
        dzs = prm.dz_A
        N = int(round(cell.length_z_A / dzs))
        counts = np.bincount(np.clip(np.floor((cell.atoms_xyz_A[:, 2] + 1e-9) / dzs).astype(int), 0, N - 1), minlength=N)
        ne = int(np.count_nonzero(counts))
        mem, _ = engine_memory(prm.nx, prm.ny, int(counts.max()), int(len(cell.Z)))
        g, _ = engine_gpu_s(prm.nx, prm.ny, N, ne, float(counts[counts > 0].mean()))
        mm = m2[name]
        ok = (est["memory_bytes"]["total"] == mem and abs(est["gpu"]["seconds_per_realisation"] - g) < 1e-9 * max(g, 1)
              and (prm.nx, prm.ny, N, len(cell.Z)) == mm[:4])
        print(f"  study point {name}: grid {prm.nx}x{prm.ny}, {N} slices, {len(cell.Z):,} atoms; engine {est['memory_bytes']['total']:,} B "
              f"/ GPU {est['gpu']['seconds_total']:.3f} s total ({nrun} runs); my replica {mem:,} B / {g*nrun:.3f} s; "
              f"M2 printout {mm[0]}x{mm[1]}, {mm[2]} slices, {mm[3]} atoms, {mm[4]} MB, {mm[5]} s")
        rows.append(ok)
        check(f"replica_vs_engine_{name}", ok, "memory bytes, GPU seconds, grid, slices, atoms")
    return rows


def main_report():
    t0 = time.time()
    hdr("0. Run record")
    try:
        commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                                text=True).stdout.strip()
    except Exception:                                   # pragma: no cover
        commit = "?"
    print(f"git HEAD {commit}; loadavg {os.getloadavg()}; numpy {np.__version__}")

    hdr("1. Beam constants, refraction, (0,0,8) angle (DERIVED_HERE)")
    print(f"lambda = {LAM:.8f} A, k = {K:.4f} rad/A, sigma = {SIGMA:.6e} rad/(V A), h^2/(2 pi m0 e) = {C_FE:.4f} V A^2")
    F0_ab = float(abtem_F(np.array([0.0]))[0])
    V0 = 8 * F0_ab / OMEGA
    V0_fe = 8 * C_FE * float(fe_kirkland(0.0)) / OMEGA
    print(f"MIP: abTEM route 8 F(0)/a^3 = {V0:.6f} V; raw-table route 8 (h^2/2pi m0 e) f_e(0)/a^3 = {V0_fe:.6f} V "
          f"(f_e(0) = {float(fe_kirkland(0.0)):.6f} A)")
    check("MIP_13.903", abs(V0 - 13.902843) < 5e-6, f"{V0:.6f} V vs H2/D3 13.902843 V")
    th_e, th_i = theta_ext_for_internal_bragg(8 / a, V0)
    th_e12, th_i12 = theta_ext_for_internal_bragg(8 / a, 12.0)
    print(f"(0,0,8) internal Bragg with V0 = MIP: theta_ext = {th_e*1e3:.4f} mrad, theta_int = {th_i*1e3:.4f} mrad; "
          f"with V0 = 12.0 V (B1): theta_ext = {th_e12*1e3:.4f} mrad, theta_int = {th_i12*1e3:.4f} mrad")
    check("theta_0008", abs(th_e * 1e3 - 16.1347) < 5e-5 and abs(th_i * 1e3 - 18.4719) < 5e-5,
          f"{th_e*1e3:.5f}/{th_i*1e3:.5f} mrad vs H2 16.1347/18.4719")
    G = 2 * np.pi * 8 / a
    Kin_exact = K * np.sqrt(1 + delta_exact(V0))
    Kin_par = np.sqrt(K ** 2 + 2 * K * SIGMA * V0)
    kap_ms = np.sqrt((K * np.sin(th_e)) ** 2 + 2 * K * SIGMA * V0 * np.cos(th_e) - (SIGMA * V0) ** 2)
    print(f"internal K: exact relativistic {Kin_exact:.6f}, paraxial k^2 + 2 k sigma V0 {Kin_par:.6f} rad/A; "
          f"2 kappa0/G - 1 with the paraxial dispersion {2*np.sqrt((K*np.sin(th_e))**2 + 2*K*SIGMA*V0)/G - 1:+.2e}; "
          f"with the multislice's exact-propagator dispersion (sqrt(k^2-q^2) - k + sigma V0) {2*kap_ms/G - 1:+.2e} "
          f"(eta shift {kap_ms - G/2:+.2e} rad/A)")
    res_el = 6.0 / np.sin(th_e)
    print(f"resolution element 6.0 A (T2) / sin(theta_ext) = {res_el:.3f} A (x3 = {3*res_el:.1f} A); "
          f"6.0/tan(theta_ext) = {6.0/np.tan(th_e):.3f} A (x3 = {18.0/np.tan(th_e):.1f}); at the B19 angle "
          f"{th_e12*1e3:.4f} mrad: 6.0/sin = {6.0/np.sin(th_e12):.2f} A, 6.0/tan = {6.0/np.tan(th_e12):.2f} A; "
          f"1/sin = {1/np.sin(th_e):.3f}, 1/sin at 16.4743 = {1/np.sin(th_e12):.3f}")

    print(f"wrap period lambda/(2 sin theta_ext): {LAM/(2*np.sin(th_e)):.4f} A at {th_e*1e3:.4f} mrad (MIP, B32); "
          f"{LAM/(2*np.sin(th_e12)):.4f} A at {th_e12*1e3:.4f} mrad (V0 = 12 V, B19)")
    hdr("2. Fourier coefficients of the engine's potential (static lattice)")
    beams = [(0, 0, 0), (0, 0, 4), (0, 0, 8), (0, 0, 12), (0, 0, 16), (0, 4, 4), (0, 2, 2), (0, 2, 6), (0, 4, 0),
             (1, -1, 1), (1, -1, 7), (3, -3, 3), (3, -3, 5)]
    u = 0.076
    for hkl in beams:
        va, vf = V_h(hkl, "abtem"), V_h(hkl, "fe")
        g2 = np.dot(hkl, hkl) / a ** 2
        dw = np.exp(-2 * np.pi ** 2 * u ** 2 * g2)
        print(f"  V{str(hkl):12s} |g| = {np.sqrt(g2):.4f} 1/A  |V| abTEM {abs(va):.4f} V, raw table {abs(vf):.4f} V "
              f"(rel. diff {abs(vf)/max(abs(va),1e-30)-1:+.1e})  sigma|V| = {SIGMA*abs(va):.4e} rad/A  "
              f"DW(0.076 A) = {dw:.4f}")
    Vg = V_h((0, 0, 8)).real
    check("V008", abs(Vg - 1.0357) < 5e-5, f"V(0,0,8) = {Vg:.5f} V vs H2 1.0357 V")
    g008 = 8 / a
    fe008 = float(fe_kirkland(g008 ** 2))
    print(f"f_e(Kirkland) at q = |g_008| = {g008:.4f} 1/A (s = q/2 = {g008/2:.4f} 1/A): {fe008:.4f} A; "
          f"M2's 0.84 V corresponds to f_e = {0.84*OMEGA/(8*C_FE):.4f} A")
    dw008 = np.exp(-2 * np.pi ** 2 * u ** 2 * g008 ** 2)
    print(f"DW (u = 0.076 A per axis, ASSUMPTION A7) of (0,0,8): amplitude {dw008:.4f}, intensity {dw008**2:.4f}; "
          f"thermally averaged V_008 = {Vg*dw008:.4f} V")

    hdr("3. Two-beam Bragg case (DERIVED_HERE; premises in the review F1)")
    ug = 2 * K * SIGMA * Vg
    c0 = ug / G
    print(f"u_g = 2 k sigma V_g = {ug:.5f} rad^2/A^2; c = b = u_g/G = {c0:.6f} rad/A; Lambda = 1/b = {1/c0:.2f} A")
    xi = np.pi / (SIGMA * Vg)
    Lb = 1 / (c0 * np.tan(th_i))
    print(f"xi_g = pi/(sigma V_g) = {xi:.1f} A; L_b = 1/(b tan theta_int) = {Lb:.1f} A; 1/(sigma V_g) = {1/(SIGMA*Vg):.1f} A;"
          f" L_b sigma V_g = {Lb*SIGMA*Vg:.5f}")
    print(f"M2 10.2 formula with V_g = 0.84 V: 1/(sigma 0.84) = {1/(SIGMA*0.84):.0f} A, xi = {np.pi/(SIGMA*0.84):.0f} A, "
          f"penetration xi sin(theta_int)/pi = {np.sin(th_i)/(SIGMA*0.84):.1f} A; with the DW-averaged V_g "
          f"{Vg*dw008:.4f} V: 1/(sigma V_g) = {1/(SIGMA*Vg*dw008):.0f} A; engine static V_g: "
          f"{(1/(SIGMA*Vg))/(1/(SIGMA*0.84)) - 1:+.3f} relative to M2")
    dth_int = 2 * c0 / (Kin_par * np.cos(th_i))
    D = delta_exact(V0)
    dth_ext = dth_int * (1 + D) * np.sin(th_i) * np.cos(th_i) / (np.sin(th_e) * np.cos(th_e))
    print(f"Darwin full width (two-beam): internal {dth_int*1e3:.4f} mrad, external {dth_ext*1e3:.4f} mrad")
    tb = {}
    for r in (0.0, 0.05, 0.1):
        eta0, c, X = two_beam(Vg, V0, r, th_e)
        q1 = np.sqrt(eta0 - c) * np.sqrt(eta0 + c)
        q = q1 if np.imag(q1) < 0 else -q1
        tb[r] = (eta0, c, complex(X))
        print(f"  r = {r:.2f}: eta0 = {eta0.real:+.3e}{eta0.imag:+.3e}j rad/A, c = {c.real:.5e}{c.imag:+.4e}j, |X| = "
              f"{abs(X):.4f}, arg X = {np.angle(X):+.4f} rad, depth 1/|Im q| = {1/abs(q.imag):.2f} A")

    hdr("4. Two-beam leading-edge transient: run-in lengths (DERIVED_HERE)")
    # closed form of the Green's function checked against a direct transform of X(eta0 - p)
    for r in (0.0, 0.1):
        eta0, c, X = tb[r]
        s = np.array([5.0, 20.0, 60.0])
        pp = np.linspace(-40, 40, 400001)
        Xp = X_of_eta(eta0 - pp, c)
        dp = pp[1] - pp[0]
        g_num = np.array([np.sum(Xp * np.exp(1j * pp * si)) * dp / (2 * np.pi) for si in s])
        g_cl = 1j * special.jv(1, c * s) * np.exp(1j * eta0 * s) / s
        g_up = np.sum(Xp * np.exp(-1j * pp * 20.0)) * dp / (2 * np.pi)
        print(f"  r = {r}: g closed vs numeric transform at s = 5, 20, 60 A: max |diff| / (|c|/2) = "
              f"{np.max(np.abs(g_num-g_cl))/(abs(c)/2):.1e}; upstream |g(-20 A)|/(|c|/2) = {abs(g_up)/(abs(c)/2):.1e}")
    Ls = np.concatenate([np.arange(50.0, 20000.0, 25.0), np.arange(20000.0, 130000.0, 50.0)])
    for r in (0.0, 0.05, 0.1):
        eta0, c, X = tb[r]
        E = np.abs(transient_E(Ls, eta0, c, th_i, X))
        sel = [1000, 2000, 3000, 5000, 10000]
        vals = "  ".join(f"{L:.0f}: {E[np.argmin(np.abs(Ls-L))]:.2g}" for L in sel)
        runin = []
        for tol in (1e-2, 3e-3, 1e-3):
            above = np.nonzero(E > tol)[0]
            runin.append(Ls[above[-1]] if len(above) else 0.0)
        print(f"  r = {r:.2f}: |E| at {vals}; last L with |E| > 1e-2 / 3e-3 / 1e-3: "
              f"{runin[0]:.0f} / {runin[1]:.0f} / {runin[2]:.0f} A (grid 25 A below 20 000 A, 50 A above)")
        if r == 0.0:
            T20 = 20.0
            Lsub = np.linspace(T20, T20 + 2 * np.pi, 400) / (c0 * np.tan(th_i))
            Emax = np.max(np.abs(transient_E(Lsub, eta0, c, th_i, X)))
            print(f"         asymptote: max |E| over one period at b s = 20: {Emax:.3e} vs sqrt(2/pi) 20^-1.5 = "
                  f"{np.sqrt(2/np.pi)*20**-1.5:.3e}; envelope sqrt(2/pi)(L/L_b)^-1.5 = 1e-2 at L = "
                  f"{(np.sqrt(2/np.pi)/1e-2)**(2/3)*Lb:.0f} A")
    print(f"  slow and fast absorption lengths along the surface: 1/(sigma r (V0 -+ V_g)): r = 0.05: "
          f"{1/(SIGMA*0.05*(V0-Vg)):.0f} / {1/(SIGMA*0.05*(V0+Vg)):.0f} A; r = 0.1: {1/(SIGMA*0.1*(V0-Vg)):.0f} / "
          f"{1/(SIGMA*0.1*(V0+Vg)):.0f} A")

    hdr("5. Absorption lengths of the proportional stand-ins (DERIVED_HERE)")
    for r in (0.05, 0.1):
        la = 1 / (SIGMA * r * V0)
        print(f"  r = {r}: mean imaginary potential {r*V0:.3f} V; amplitude 1/e length along the path {la:.0f} A "
              f"(intensity {la/2:.0f} A); depth of a refracted non-Bragg wave sin(theta_int)/(sigma r V0) = "
              f"{np.sin(th_i)*la:.1f} A")


    hdr("6. Many-beam bookkeeping at the (0,0,8) condition (DERIVED_HERE)")
    for az in ((1, 0, 0), (1, 1, 0)):
        rows = many_beam(az, V0, th_e)
        exact = [r_ for r_ in rows if abs(r_[1]) < 1e-9]
        print(f"azimuth {az}: {len(rows)} coupled beams; exactly excited (|zeta| < 1e-9 rad/A): {[r_[0] for r_ in exact]}")
        for r_ in exact:
            print(f"   EXACT {r_[0]}: zeta = {r_[1]:+.2e}, k_x = {r_[3]:+.2e} rad/A (surface-parallel), in-plane "
                  f"angle {abs(r_[4])*1e3:.2f} mrad, |V_h| = {abs(r_[6]):.4f} V, |V_g-h| = {abs(r_[7]):.4f} V, "
                  f"sigma|V_h| = {SIGMA*abs(r_[6]):.3e} rad/A")
            # evanescent in vacuum: kx_int = 0 -> kx_vac^2 = -2 k sigma V0 < 0
        strong = sorted([r_ for r_ in rows if np.isfinite(r_[2]) and r_[2] >= 0.05], key=lambda r_: -r_[2])
        for r_ in strong[:10]:
            print(f"   {str(r_[0]):12s} zeta = {r_[1]:+.4e} admixture {r_[2]:.3f} k_x = {r_[3]:+.3f} angle_y = "
                  f"{abs(r_[4])*1e3:5.2f} mrad Bethe off-diag {r_[5]:+.4f} V")
        tot, _ = bethe_missing(rows, np.inf)
        print(f"   Bethe sum (exact beams excluded): {tot:+.4f} V -> |V_g - sum|/V_g = {abs(Vg - tot)/Vg:.3f}; "
              f"centre shift estimate (sum of sigma|V_h|^2/zeta over 0-coupled beams) not recomputed")
        for dx in (0.13, 0.10):
            fmax = 1 / (3 * dx)
            tot, car = bethe_missing(rows, fmax)
            print(f"   dx = {dx}: band {fmax:.3f} 1/A: Bethe carried {car:+.5f} of {tot:+.5f} V -> missing "
                  f"{abs(tot-car)/Vg:.2e} V_g")
        if az == (1, 0, 0):
            check("four_beam_100", sorted(r_[0] for r_ in exact) == [(0, -4, 4), (0, 4, 4)],
                  f"exactly excited at [100]: {[r_[0] for r_ in exact]}")
            # exactness with the multislice dispersion: every beam's gamma depends on |q| only, so the
            # degeneracy of 0 and (0,+-4,4) holds for any kappa0 = G/2; with the engine's own kappa0:
            kap_ms = np.sqrt((K * np.sin(th_e)) ** 2 + 2 * K * SIGMA * V0 * np.cos(th_e) - (SIGMA * V0) ** 2)
            dz_ = G * (G / 2 - kap_ms) / (2 * Kin_par)
            print(f"   with the multislice's own kappa0 ({kap_ms:.6f} vs G/2 {G/2:.6f}): zeta(0,+-4,4) = {dz_:.2e} rad/A "
                  f"= {dz_/(SIGMA*abs(V_h((0,4,4)))):.1e} of sigma|V_044|")
        else:
            check("no_exact_110", len(exact) == 0, f"exactly excited at [110]: {[r_[0] for r_ in exact]}")

    hdr("7. Sampling (2/3 band f_max = 1/(3 dx)) and the engine's check_band (REPRODUCED by calling it)")
    items = [("incident beam, external", np.sin(th_e) / LAM), ("specular/incident wave inside", np.sin(th_i) / LAM),
             ("(0,0,8) coupling", 8 / a), ("(0,+-4,4) coupling", np.sqrt(32) / a), ("(0,0,12) coupling", 12 / a),
             ("(0,0,16) coupling", 16 / a)]
    for name, f in items:
        print(f"  {name:32s} f = {f:.4f} 1/A -> dx <= {1/(3*f):.4f} A")
    print(f"  a/24 = {a/24:.4f} A")
    from reflection_holo.forward.multislice.grid import Grid, check_band
    from reflection_holo.geometry.errors import SamplingError
    th_int_eng = th_i
    passed = []
    for dx in np.arange(0.20, 0.50, 0.005):
        g_ = Grid(nx=1000, ny=10, dx_A=float(dx), dy_A=float(dx), x0_A=0.0, y0_A=0.0)
        try:
            check_band(g_, rule="2/3", wavelength_A=LAM, angles_rad=dict(incident_ext=th_e, outgoing_ext=th_e,
                                                                         incident_int=th_int_eng,
                                                                         outgoing_int=th_int_eng))
            passed.append(float(dx))
        except SamplingError:
            pass
    print(f"  engine check_band (grid.py) with the four declared angles passes for dx up to {max(passed):.3f} A "
          f"(tested 0.200-0.495 A in 0.005 A steps); it fails first at {min(set(np.round(np.arange(0.20,0.50,0.005),3))-set(np.round(passed,3))):.3f} A")
    check("band_check_threshold", 0.45 <= max(passed) < 0.4526 + 1e-9, f"largest passing dx {max(passed):.3f} A (bound 0.4526 A)")
    for dx in (0.13, 0.10):
        from reflection_holo.forward.multislice.potentials import AtomicPotential  # noqa: F401 (import check)
        fm = 1 / (3 * dx)
        print(f"  dx = {dx}: f_max = {fm:.4f} 1/A; F(f_max^2)/F(0) = {abtem_F(np.array([fm**2]))[0]/F0_ab:.4f}")
    print(f"  dz: [100] a/4 = {a/4:.6f} A; [110] p/4 = {a/np.sqrt(2)/4:.6f} A")


    hdr("8. Sizing rules and scenario rows rebuilt from the stated rules (DERIVED_HERE)")
    tt = np.tan(th_e)
    alpha_y = np.sin(th_i)          # in-plane angle of the surface-parallel (0,+-4,4) beams: kappa0/K
    print(f"alpha_y = {alpha_y*1e3:.2f} mrad (tan {np.tan(alpha_y):.6f})")
    dl = {}
    for r, Lr in ((0.1, 2500.0), (0.05, 5000.0), (0.0, 8000.0)):
        dl[r] = Lr * np.tan(alpha_y) + 3 * 6.0
        print(f"  r = {r}: dlat = {Lr:.0f} tan(alpha_y) + 18 = {dl[r]:.1f} A; W_min = 2 dlat + 12 = {2*dl[r]+12:.1f} A; "
              f"torus y: ceil((2040 + 2 dlat + 12)/a) a - 2040 = {np.ceil((2040+2*dl[r]+12)/a)*a - 2040:.1f} A")
    for mis in (0.05, 0.1, 0.25, 0.5):
        m = np.deg2rad(mis)
        print(f"  miscut {mis} deg: W = h/tan = {Q/np.tan(m):.1f} A (a/4), {2*Q/np.tan(m):.1f} A (a/2); "
              f"whole y-periods: {np.ceil(Q/np.tan(m)/a)*a:.1f} A (a/4)")
    for h in (Q, 2 * Q, 19.008, 20.366, 100.0):
        print(f"  strip h/tan(theta_ext) for h = {h:.4f} A: {h/tt:.1f} A")
    for t_ in (10.0, 20.0, 30.0):
        print(f"  overlayer {t_:.0f} A: 2 t/sin(theta_ext) = {2*t_/np.sin(th_e):.0f} A")
    print(f"  8 resolution elements = {8*res_el:.1f} A; miscut giving that terrace: a/4 {np.rad2deg(np.arctan(Q/(8*res_el))):.4f} deg, "
          f"a/2 {np.rad2deg(np.arctan(2*Q/(8*res_el))):.4f} deg")
    print(f"  half-torus volume pi^2 R r^2 x 8/a^3 = {np.pi**2*1000*400*8/a**3:.0f} atoms")
    re_ = res_el
    tor_field = 3 * re_ + 1262.0 + 2040.0 + 1262.0
    rows = []
    rows.append(layout("2a_a4_miscut0.1_r0.10", th=th_e, res_el=re_, L_run=2500, D_clean=55, y_mode="staircase",
                       step_h=Q, field=5 * re_, W=Q / np.tan(np.deg2rad(0.1))))
    rows.append(layout("2a_a4_miscut0.5_r0.10", th=th_e, res_el=re_, L_run=2500, D_clean=55, y_mode="staircase",
                       step_h=Q, field=5 * re_, W=Q / np.tan(np.deg2rad(0.5))))
    rows.append(layout("2a_a4_miscut0.1_r0.05", th=th_e, res_el=re_, L_run=5000, D_clean=65, y_mode="staircase",
                       step_h=Q, field=5 * re_, W=Q / np.tan(np.deg2rad(0.1))))
    rows.append(layout("2a_a2_miscut0.1_r0.10", th=th_e, res_el=re_, L_run=2500, D_clean=55, y_mode="staircase",
                       step_h=2 * Q, field=5 * re_, W=2 * Q / np.tan(np.deg2rad(0.1))))
    rows.append(layout("2a_a4_Wmin_r0.10", th=th_e, res_el=re_, L_run=2500, D_clean=55, y_mode="staircase",
                       step_h=Q, field=5 * re_, W=2 * dl[0.1] + 12))
    rows.append(layout("2a_a4_miscut0.1_r0.00", th=th_e, res_el=re_, L_run=8000, D_clean=65, y_mode="staircase",
                       step_h=Q, field=5 * re_, W=Q / np.tan(np.deg2rad(0.1))))
    for hstep, nm in ((2 * Q, "2b_a2_transverse_r0.10"), (Q, "2b_a4_transverse_r0.10")):
        fld = 3 * re_ + 2 * re_ + 3 * re_ + hstep / tt + 3 * re_ + 2 * re_
        z_step = 2.0 / tt + 2500 + 3 * re_ + 2 * re_ + 3 * re_ + hstep / tt - 10 * Q
        rows.append(layout(nm, th=th_e, res_el=re_, L_run=2500, D_clean=55, y_mode="transverse", step_h=hstep,
                           field=fld, W=None))
        # patch the atom count with the two terraces (lower upstream, upper = + step downstream)
        r_ = rows[-1]
        z1 = int(np.ceil(z_step / a - 1e-9))
        z2 = r_["periods"] - z1
        dlay = int(round(hstep / Q))
        r_["atoms"] = 2 * 16 * (z1 * r_["n_low"] + z2 * (r_["n_low"] + dlay))
        r_["n_mean"] = r_["atoms"] / r_["nonempty"]
        r_["n_max"] = 16 * ((r_["n_low"] + dlay + 1) // 2)
        r_["terraces_A"] = (z1 * a, z2 * a)
    for r, Lr, Dc in ((0.1, 2500.0, 55.0), (0.05, 5000.0, 65.0)):
        rows.append(layout(f"3_torus_R1000_r20_r{r:.2f}", th=th_e, res_el=re_, L_run=Lr, D_clean=Dc, y_mode="torus",
                           field=tor_field, torus=True, W=2040 + 2 * dl[r] + 12, extra_depth=20.366, ridge=19.008,
                           ring_V=np.pi ** 2 * 1000 * 400))
    rows.append(layout("V_rocking_flat_strip_r0.10", th=th_e, res_el=re_, L_run=2500, D_clean=55, y_mode=2,
                       field=5 * re_, n_real=1, n_ang=19))
    cc = cpu_constants_from_raw()
    print(f"CPU constants fitted here from the RAW calibration entries ({cc['created']}, load {cc['load']}): "
          f"FFT {cc['c_fft']:.3e} s/(px log2 px), element-wise {cc['c_el']:.3e} s/px, exp {cc['c_exp']:.3e} s/element, "
          f"GEMM {cc['gemm']/1e9:.0f} GFLOP/s")
    print("| scenario | x, y, z (A) | atoms | grid | slices (non-empty) | n_max / n_mean | engine arrays GB (device) | "
          "GPU model per real. | CPU x1.5 per real. | pot. share GPU/CPU | x real x ang | total CPU / GPU | host 120/192/240 B/atom GB |")
    table = {}
    for r_ in rows:
        mem, atomsB = engine_memory(r_["nx"], r_["ny"], r_["n_max"], r_["atoms"])
        g, gpf = engine_gpu_s(r_["nx"], r_["ny"], r_["N"], r_["nonempty"], r_["n_mean"])
        c, cpf = cpu_model_s(r_["nx"], r_["ny"], r_["N"], r_["nonempty"], r_["n_mean"], cc)
        c15 = 1.5 * c
        nr = r_["n_real"] * r_["n_ang"]
        table[r_["name"]] = dict(r_, mem=mem, gpu=g, cpu15=c15)
        print(f"| {r_['name']} | {r_['ext_x']:.1f} x {r_['y']:.1f} x {r_['Lz']:.1f} | {r_['atoms']:,} | {r_['nx']}x{r_['ny']} | "
              f"{r_['N']} ({r_['nonempty']}) | {r_['n_max']} / {r_['n_mean']:.0f} | {mem/1e9:.3f} ({(mem-atomsB)/1e9:.3f}) | "
              f"{fmt_t(g)} | {fmt_t(c15)} | {gpf*100:.0f} % / {cpf*100:.0f} % | {r_['n_real']} x {r_['n_ang']} | "
              f"{fmt_t(c15*nr)} / {fmt_t(g*nr)} | {r_['atoms']*120/1e9:.1f} / {r_['atoms']*192/1e9:.1f} / {r_['atoms']*240/1e9:.1f} |")
        print(f"      detail: periods {r_['periods']}, H {r_['H']:.1f} A, vacuum {r_['vac']:.0f} A, depth {r_['depth']:.2f} A "
              f"({r_['n_low']} layers), y periods {r_['yper']}" + (f", terraces {r_['terraces_A'][0]:.0f} / {r_['terraces_A'][1]:.0f} A"
                                                                     if 'terraces_A' in r_ else "")
              + (f", ring atoms {r_['ring_atoms']}" if r_['ring_atoms'] else ""))


    hdr("9. Engine rerun of H2's bu_100_r010 strip with my own read-out (REPRODUCED; UNVALIDATED engine)")
    if RERUN_JSON.exists():
        rr = json.load(open(RERUN_JSON))
        h2 = json.load(open(H2_MEAS))["runs"]["bu_100_r010"]
        run = rr["runs"].get("bu_100_r010_h5")
        if run:
            print(f"cell: {run['n_atoms']} atoms, grid {run['nx']}x{run['ny']}, {run['n_slices']} slices, L_z {run['Lz']:.2f} A, "
                  f"H {run['H']:.2f} A, vacuum {run['vac']:.0f} A; run {run['run_s']:.0f} s (load after {run['loadavg_after']}); "
                  f"H2: {h2['info']['n_atoms']} atoms, {h2['info']['nx']}x{h2['info']['ny']}, {h2['info']['n_slices']} slices, "
                  f"L_z {h2['info']['L_z_A']:.2f}, H {h2['info']['H_A']:.2f}, vacuum {h2['info']['vacuum_above_A']:.0f}")
            check("rerun_cell_equals_H2", run['n_atoms'] == h2['info']['n_atoms'] and run['nx'] == h2['info']['nx']
                  and run['n_slices'] == h2['info']['n_slices'], "atoms, nx, slices identical")
            h2b = {b_['start_A']: complex(b_['R_abs'] * np.exp(1j * b_['R_arg'])) for b_ in h2['buildup']['bins']}
            for key in ("2.0-6.0", "2.0-4.0", "2.0-10.0"):
                ro = run["readouts"][key]
                Rpl = complex(*ro["R_plateau"])
                bins = [(lo, complex(re_, im_)) for lo, re_, im_ in ro["bins"]]
                print(f"  read-out with vacuum taper {key} A above the top layer: plateau |R| = {abs(Rpl):.4f}, arg = "
                      f"{np.angle(Rpl):+.4f} (H2: {h2['buildup']['R_plateau_abs']:.4f}, {h2['buildup']['R_plateau_arg']:+.4f})")
                if key == "2.0-6.0":
                    for lo, R in bins:
                        hb = h2b.get(lo)
                        print(f"     {lo:6.0f}-{lo+500:6.0f} A: |R| {abs(R):.4f} arg {np.angle(R):+.4f}  dphase "
                              f"{np.angle(R/Rpl):+.4f} damp {abs(R)/abs(Rpl)-1:+.4f}" +
                              (f"   | H2 |R| {abs(hb):.4f} arg {np.angle(hb):+.4f}" if hb is not None else ""))
                for tp, ta in ((1e-2, 3e-2), (1e-2, 1e-2), (3e-3, 1e-2)):
                    Lph, Lam = converged_beyond(bins, Rpl, ro["d_end"], tp, ta)
                    print(f"     converged beyond: phase {tp:g} rad -> {Lph} A; amplitude {ta:g} -> {Lam} A")
                if key == "2.0-6.0":
                    Rpl6 = Rpl
                    prof = ro["profile"]
                    print("     exit-plane intensity vs depth below the top layer: " +
                          ", ".join(f"{k}: {v:.1e}" for k, v in prof.items()))
                    print(f"     deepest point with I > 1e-2 / 1e-4 / 1e-6: {ro['deepest']['0.01']:.1f} / "
                          f"{ro['deepest']['0.0001']:.1f} / {ro['deepest']['1e-06']:.1f} A (H2: "
                          f"{h2['depth']['depth_I_below_1e-02_A']:.1f} / {h2['depth']['depth_I_below_1e-04_A']:.1f} / "
                          f"{h2['depth']['depth_I_below_1e-06_A']:.1f})")
            check("rerun_plateau", abs(abs(Rpl6) - h2['buildup']['R_plateau_abs']) < 5e-3 and
                  abs(np.angle(Rpl6) - h2['buildup']['R_plateau_arg']) < 1e-2,
                  f"|R| {abs(Rpl6):.4f} vs 0.2707, arg {np.angle(Rpl6):+.4f} vs -1.5394")
        fpr = rr["runs"].get("fp_100_r010_6000_h5")
        if fpr:
            print("  frozen-phonon strip (6000 A after contact, y = 2 periods, clean depth 60 A, r = 0.1, u = 0.076 A, "
                  f"seed 20260923, {len(fpr['realisations'])} realisations; static reference in the same cell)")
            st = {lo: complex(re_, im_) for lo, re_, im_ in fpr["static"]["bins"]}
            reals = [{lo: complex(re_, im_) for lo, re_, im_ in rz["bins"]} for rz in fpr["realisations"]]
            d_end = fpr["d_end"]
            mean = {lo: np.mean([rz[lo] for rz in reals]) for lo in st}
            pl = [lo for lo in st if lo >= d_end - 750 - 2500 and lo + 500 <= d_end - 750 + 1e-6]
            Rst = np.mean([st[lo] for lo in pl])
            Rmn = np.mean([mean[lo] for lo in pl])
            for lo in sorted(st):
                print(f"     {lo:6.0f}-{lo+500:6.0f} A: static |R| {abs(st[lo]):.4f} arg {np.angle(st[lo]):+.4f} | mean |R| "
                      f"{abs(mean[lo]):.4f} arg {np.angle(mean[lo]):+.4f} | |mean|/|static| {abs(mean[lo])/abs(st[lo]):.4f} "
                      f"arg diff {np.angle(mean[lo]/st[lo]):+.4f} | mean vs its plateau: dphase {np.angle(mean[lo]/Rmn):+.4f} "
                      f"damp {abs(mean[lo])/abs(Rmn)-1:+.4f}")
            print(f"     plateau bins {min(pl):.0f}-{max(pl)+500:.0f} A: static |R| {abs(Rst):.4f}; ensemble mean |R| {abs(Rmn):.4f}; "
                  f"ratio {abs(Rmn)/abs(Rst):.4f}; arg(mean) - arg(static) {np.angle(Rmn/Rst):+.4f} rad")
            bins_m = [(lo, mean[lo]) for lo in sorted(mean)]
            bins_s = [(lo, st[lo]) for lo in sorted(st)]
            for tp, ta in ((1e-2, 3e-2), (1e-2, 1e-2)):
                print(f"     converged beyond (phase {tp:g} rad / amplitude {ta:g}): static {converged_beyond(bins_s, Rst, d_end, tp, ta)}; "
                      f"ensemble mean {converged_beyond(bins_m, Rmn, d_end, tp, ta)}")
            # H2-style region 1500-2252 A: ratio of the ensemble mean to static in the transient region
            reg = [lo for lo in (1500.0, 2000.0)]
            print(f"     in H2's region (1500-2500 A bins): |mean|/|static| {abs(np.mean([mean[l] for l in reg]))/abs(np.mean([st[l] for l in reg])):.4f}, "
                  f"arg diff {np.angle(np.mean([mean[l] for l in reg])/np.mean([st[l] for l in reg])):+.4f} rad")
    else:
        print("  (no rerun JSON)")



    hdr("12. Phonons, rocking angles, B16, vacuum rule, tolerance sensitivity (DERIVED_HERE)")
    fp = json.load(open(H2_MEAS))["runs"]["fp_100_r010"]
    rho2 = fp["rho2"]
    print(f"H2 stored rho^2 = {rho2:.4e}: N = rho^2/(2 dphi^2) for dphi = 1e-2 rad: {rho2/(2*1e-4):.2f}; "
          f"|mean|/|static| = {fp['amp_mean_over_static']:.4f} (1/x = {1/fp['amp_mean_over_static']:.3f}, "
          f"+{(1/fp['amp_mean_over_static']-1)*100:.1f} %), arg diff {fp['phase_mean_minus_static_rad']:+.4f} rad")
    rows_fp = fp["rows"]
    print("  H2 per-bin |mean|/|static|: " + ", ".join(f"{r_.get('start_A', r_.get('d0', '?'))}: {r_.get('amp_mean_over_static', r_.get('ratio', float('nan'))):.4f}"
                                                  for r_ in rows_fp))
    w = dth_ext
    n_rock = int(round(2 * 1.5 * w / (w / 6))) + 1
    print(f"rocking: +-1.5 Darwin widths = +-{1.5*w*1e3:.4f} mrad, step w/6 = {w/6*1e3:.4f} mrad -> {n_rock} angles")
    hmax, sig = 20.366, 0.028
    dth_max = (np.pi - 3 * np.sqrt(2) * sig) / ((2 * np.pi / LAM) * hmax * 2 * np.cos(th_e))
    s_off = np.array([-1.5, -0.5, 0.5, 1.5]) * 2 * np.cos(th_e) * dth_max
    sig_h = sig / ((2 * np.pi / LAM) * np.sqrt(np.sum(s_off ** 2)))
    print(f"B16 (h_max 20.366 A, sigma 0.028 rad): largest tilt step {dth_max*1e3:.4f} mrad; 4 angles over "
          f"{3*dth_max*1e3:.3f} mrad: slope standard error {sig_h:.4f} A")
    for nm in ("2a_a4_miscut0.1_r0.10", "3_torus_R1000_r20_r0.10", "2a_a4_miscut0.1_r0.05"):
        t_ = table[nm]
        need = max(2.0 + t_["H"], t_["Lz"] * np.tan(th_e)) + 2.0
        print(f"  vacuum {nm}: engine rule H + L_z tan = {t_['H'] + t_['Lz']*np.tan(th_e):.1f} A (cell {t_['vac']:.0f} A); "
              f"max(gap + H, L_z tan) + edge = {need:.1f} A")
    print("tolerance sensitivity: design run-in with the M2/README amplitude criterion |B/A - 1| <= 1e-2 instead of 3e-2:")
    for nm, Lr_new, Dc, r in (("2a_a4_miscut0.1_r0.10", 3000.0, 55.0, 0.1), ("2a_a4_miscut0.1_r0.00", 9000.0, 65.0, 0.0),
                              ("3_torus_R1000_r20_r0.10", 3000.0, 55.0, 0.1)):
        t_ = table[nm]
        if nm.startswith("3_"):
            alt = layout(nm, th=th_e, res_el=re_, L_run=Lr_new, D_clean=Dc, y_mode="torus", field=tor_field, torus=True,
                         W=2040 + 2 * (Lr_new * np.tan(alpha_y) + 18) + 12, extra_depth=20.366, ridge=19.008,
                         ring_V=np.pi ** 2 * 1000 * 400)
        else:
            alt = layout(nm, th=th_e, res_el=re_, L_run=Lr_new, D_clean=Dc, y_mode="staircase", step_h=Q,
                         field=5 * re_, W=Q / np.tan(np.deg2rad(0.1)))
        mem, _ = engine_memory(alt["nx"], alt["ny"], alt["n_max"], alt["atoms"])
        g, _ = engine_gpu_s(alt["nx"], alt["ny"], alt["N"], alt["nonempty"], alt["n_mean"])
        c, _ = cpu_model_s(alt["nx"], alt["ny"], alt["N"], alt["nonempty"], alt["n_mean"], cc)
        print(f"  {nm}: run-in {Lr_new:.0f} A -> z {alt['Lz']:.1f} A (was {t_['Lz']:.1f}), x {alt['ext_x']:.1f}, y {alt['y']:.1f}, "
              f"atoms {alt['atoms']:,} ({alt['atoms']/t_['atoms']-1:+.1%}), grid {alt['nx']}x{alt['ny']}, "
              f"memory {mem/1e9:.3f} GB, GPU {fmt_t(g)}, CPU x1.5 {fmt_t(1.5*c)}")


    print("lateral buffer bounds from absorption alone (r = 0.1): ")
    for tag, Vabs in (("mean V0", V0), ("V0 - V_044", V0 - abs(V_h((0, 4, 4))))):
        Ldec = np.log(100) / (SIGMA * 0.1 * Vabs)
        lat = Ldec * np.tan(alpha_y)
        print(f"  {tag}: 1e-2 decay length {Ldec:.0f} A -> lateral {lat:.1f} A, dlat {lat+18:.1f} A, W_min {2*(lat+18)+12:.1f} A")
    h2m = json.load(open(H2_MEAS))["runs"]
    for nm in ("bu_100_r010", "bu_110_r010"):
        prof = {round(p_["depth_A"]): p_["I"] for p_ in h2m[nm]["depth"]["profile"]}
        print(f"  H2 {nm}: exit-plane intensity at 20 A depth {prof.get(20, float('nan')):.2e} (study cells: clean depth 21 A; "
              f"amplitude {np.sqrt(prof.get(20, float('nan'))):.2f}); plateau |R| {h2m[nm]['buildup']['R_plateau_abs']:.4f}")
    print(f"  [100]/[110] plateau amplitude ratio {h2m['bu_100_r010']['buildup']['R_plateau_abs']/h2m['bu_110_r010']['buildup']['R_plateau_abs']:.2f} "
          f"(intensity {(h2m['bu_100_r010']['buildup']['R_plateau_abs']/h2m['bu_110_r010']['buildup']['R_plateau_abs'])**2:.0f})")

    hdr("11. Built cells: engine estimate_resources and geometry assertions vs H2's table (REPRODUCED)")
    study_point_checks()
    # the validation strip (row V) and the narrowest converged terrace (row 2a_a4_Wmin), built for real
    tV = table["V_rocking_flat_strip_r0.10"]
    cellV = build_flat_100(y_periods=2, z_periods=tV["periods"], depth_below=tV["depth"], vac=tV["vac"], ent=10 * Q)
    estV, memV, gV, _ = engine_check_cell(cellV, th=th_e, H=tV["H"], n_real=19, label="V_rocking_flat_strip_r0.10")
    check("V_row_built", len(cellV.Z) == 214032 and estV["grid"]["nx"] == 2000 and estV["grid"]["ny"] == 84
          and estV["n_slices"] == 4126 and abs(estV["memory_bytes"]["total"] / 1e9 - 0.023) < 5e-4,
          f"214,032 atoms, 2000x84, 4126 slices, {estV['memory_bytes']['total']/1e9:.4f} GB (H2 0.023 GB)")
    del cellV
    tW = table["2a_a4_Wmin_r0.10"]
    nW = tW["yper"] // 2
    cellW = build_staircase_100(nW=nW, dl_layers=1, z_periods=tW["periods"], depth_below=tW["depth"], vac=tW["vac"],
                                ent=10 * Q)
    estW, memW, gW, setW = engine_check_cell(cellW, th=th_e, H=tW["H"], n_real=8, label="2a_a4_Wmin_r0.10")
    check("Wmin_row_built", len(cellW.Z) == 5618340 and (estW["grid"]["nx"], estW["grid"]["ny"]) == (2000, 2187)
          and estW["n_slices"] == 4126 and abs(estW["memory_bytes"]["total"] / 1e9 - 0.631) < 5e-4
          and abs(estW["gpu"]["seconds_per_realisation"] - 48) < 1.0,
          f"5,618,340 atoms, 2000x2187, 4126 slices, {estW['memory_bytes']['total']/1e9:.4f} GB (H2 0.631), "
          f"GPU {estW['gpu']['seconds_per_realisation']:.1f} s (H2 48 s)")
    del cellW

    return dict(V0=V0, Vg=Vg, th_e=th_e, th_i=th_i, G=G, c0=c0, Lb=Lb, dth_ext=dth_ext, dth_int=dth_int,
                res_el=res_el, t0=t0, tb=tb)


if __name__ == "__main__":
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--rerun", default=None)
    ap_.add_argument("--memtime", default=None)
    ap_.add_argument("--which", default="static")
    args = ap_.parse_args()
    if args.rerun:
        rerun_mode(args.rerun, args.which.split(","))
        sys.exit(0)
    if args.memtime:
        memtime_mode(args.memtime)
        sys.exit(0)
    ctx = main_report()
