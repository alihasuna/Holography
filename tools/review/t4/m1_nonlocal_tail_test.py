#!/usr/bin/env python3
"""T4 (fix of audit A9a M-1): is the vacuum difference at the ring's projection P in T3's buried-void
runs (caps 20 and 30 A: max 2.3e-4 and 1.6e-4 of A_ref, common to both caps) a NUMERICAL artefact of
the non-local tails of the engine's transmission function, or a signal carried from the void?

TEST_ONLY diagnostic in a small cell; no production code is modified. Repository builders and engine
functions are called unchanged (reflection_setup with every engine assertion, check_feature_geometry
F1-F5, AtomicPotential.realise, band_limit_mask, propagator_kernel, absorber_profile_V,
sheet_beam_wave); the slice loop repeats engine.propagate_slices operation by operation and is
checked BIT FOR BIT against it on two slice windows (one containing void slices).

Cell (TEST_ONLY; every value below printed): Si(001) [100], 13 x 276 periods (70.60 x 1498.93 A),
the same z geometry as T3 (ring centre z = 1000 A, 1124 slices of a/4, sheet beam H = 22 A 1 A above
the surface, 16.1347 mrad, 200 keV, TEST_ONLY proportional absorption r = 0.1, exact propagator, 2/3
band limit, complex128), a smaller full-torus void (R = 20 A, r = 6 A) under caps 20 and 30 A, depth
66 layers (the smallest satisfying F5 for cap 30 A with r = 6 A), pixel rule max_pixel_A (argument;
T3: 0.13 A).

The test. The engine multiplies the wave in slice i by t_i = BL[exp(i sigma V_i) a(x)]. The void
changes it by d_i = t_i,void - t_i,flat. Physically the removed atoms change the potential only
within a few A of their sites (Kirkland projected potential of one Si atom: printed below at 5 and
7 A); farther away d_i is purely numerical (Fourier synthesis of off-grid atoms up to the grid's
Nyquist frequency, potentials.py, and the sharp 2/3 band limit BL, engine.py). One pass propagates,
with the SAME flat potential:
  flat     t_flat
  full_c   t_flat + d          = the engine's void run (bit for bit; checked)
  local_c  t_flat + d (1 - M)  only the change within 5 A of the void's x range [-(cap + 2r), -cap]
  tails_c  t_flat + d M        only the change farther than 5 A (M = 1 beyond a 2 A sin^2 ramp):
                               numerical by construction
Exit waves are analysed with tools/plots/buried_torus.py (specular aperture, regions, apodised
vacuum-origin split; imported, not re-implemented).

PREDICTION of the hypothesis (A9a M-1): at P, for every cap, tails/full lies in [0.8, 1.25] and
local/full < 0.2, for the maximum and for the rms over P. Verdict: CONFIRMED if both hold for every
cap; NOT CONFIRMED if local/full >= 0.5 or tails/full < 0.5 for any cap; INCONCLUSIVE otherwise.
The ratios are taken on the part named by --criterion, fixed before each run (report T4 section 2):
  stage 1 (0.13 A rule): 'total' F(D) at P. Its cap-20 result showed that the local (physical)
          end-face signal reaches P through the sharp aperture (the A9a M-2 mechanism);
  stage 2 (0.09 A rule, an independent run): 'vacuum_origin' F(D m) at P (end face masked before
          the aperture, tools/plots/buried_torus.py).
Both parts are always printed. Also printed: the tail amplitude |d| in the vacuum above the ring and
the Fourier components of d along x there (g = 0, (0,0,4), (0,0,8)), per cap, and with
--reference-summary the ratios between two pixel sizes (descriptive, no pass/fail rule).

Usage: OMP_NUM_THREADS=2 ... PYTHONPATH=. venv/bin/python tools/review/t4/m1_nonlocal_tail_test.py
       --max-pixel-A 0.13 --caps 20 30 --criterion total --max-cpu-seconds 3000 --out <dir>
       [--reuse-waves] [--reference-summary <summary json of an earlier run>]
Writes <out>/outputs/manifests/<run>.json (manifest), <out>/waves_<tag>.npz, <out>/summary_<tag>.json.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import reflection_holo
from reflection_holo.constants import A_SI_A as A
from reflection_holo.forward.feature_cell import (BURIED_MIN_CLEAN_BELOW_SURFACE_A,
                                                  BURIED_MIN_CLEAN_BELOW_VOID_A,
                                                  build_feature_reflection_cell,
                                                  check_feature_geometry)
from reflection_holo.forward.multislice import (PLANE_TEXT, VALIDATION_STATUS, AtomicPotential,
                                                MultisliceParams, NumericalAbsorber,
                                                PhysicalAbsorption, SheetBeam, estimate_resources,
                                                fft_friendly, potential_mean_inner_potential_V,
                                                reflection_setup)
from reflection_holo.forward.multislice.backend import get_backend
from reflection_holo.forward.multislice.engine import ENGINE_NAME, propagate_slices
from reflection_holo.forward.multislice.grid import band_limit_mask
from reflection_holo.forward.multislice.illumination import sheet_beam_wave
from reflection_holo.forward.multislice.potentials import absorber_profile_V
from reflection_holo.forward.multislice.propagator import propagator_kernel
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.provenance.manifest import build_manifest, write_manifest
from reflection_holo.structure.features import build_si001_flat_reference, build_si001_with_feature
from reflection_holo.structure.shapes import BuriedTorus

REPO = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("buried_torus", REPO / "tools/plots/buried_torus.py")
bt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bt)

TEST = "TEST_ONLY: T4 M-1 numerical diagnostic (small cell), stands in for PROJECT_INPUT item {}"
CASE = dict(
    energy_keV=200.0, lattice_parameter_A=A, lattice_label="ASSUMPTION B2", azimuth_uvw=(1, 0, 0),
    azimuth_label=TEST.format(8), periods_y=13, periods_z=276,
    feature=dict(major_radius_A=20.0, minor_radius_A=6.0, center_z_A=1000.0,
                 label=TEST.format(13), source="TEST_ONLY T4 M-1 diagnostic (not B42's geometry)"),
    ring_margin_A=A, structure_vacuum_A=10.0, vacuum_above_flat_surface_A=60.0,
    bulk_absorber_A=15.0, top_absorber_A=10.0, entrance_vacuum_slices=20,
    beam=dict(height_A=22.0, edge_A=2.0, bottom_above_flat_surface_at_launch_A=1.0),
    absorber=dict(strength_V=100.0, profile="sin2"),
    physical_absorption=dict(model="proportional", ratio=0.1,
                             label="TEST_ONLY: proportional absorption r = 0.1 as T3 (stands in "
                                   "for PROJECT_INPUT item 21 in this numerical diagnostic only)"),
    static_lattice_label="TEST_ONLY: static lattice in this numerical diagnostic",
    theta_label="ASSUMPTION B32: external angle of the (0,0,8) internal Bragg condition computed "
                "with the engine's mean inner potential (stands in for PROJECT_INPUT item 7)",
    working_reflection_hkl=(0, 0, 8), buildup_depth_A=20.0, footprint_margin_A=100.0,
    slices_per_period=4, propagator="exact", band_limit="2/3", backend="numpy",
    precision="complex128", threads=2, cpu_calibration_factor=1.5,
    local_margin_A=5.0, local_ramp_A=2.0,
    vacuum_tail_window_x_rel_A=(0.5, 20.0),
)
STATUS = ("TEST_ONLY numerical diagnostic (T4, fix of A9a M-1); small cell with a smaller void than "
          "B42; UNVALIDATED engine: " + VALIDATION_STATUS)


def _r(u, v) -> float:
    """u / v, NaN when v is not positive (a zero difference in a DEBUG run)."""
    return float(u / v) if v > 0 else float("nan")


def depth_layers_for(cap_max_A: float, r_A: float) -> int:
    need = max(BURIED_MIN_CLEAN_BELOW_SURFACE_A,
               cap_max_A + 2.0 * r_A + BURIED_MIN_CLEAN_BELOW_VOID_A) + CASE["bulk_absorber_A"]
    return int(np.ceil(need / (A / 4.0) - 1e-12)) + 1


def local_mask(x_rel, cap, r, margin, ramp):
    """M(x_rel) = 0 within `margin` of the void's x range [-(cap + 2 r), -cap], sin^2 ramp over
    `ramp`, 1 beyond (the 'tails' region)."""
    top, bot = -cap, -(cap + 2.0 * r)
    dist = np.maximum(np.maximum(bot - x_rel, x_rel - top), 0.0)
    s = np.clip((dist - margin) / ramp, 0.0, 1.0)
    return np.sin(0.5 * np.pi * s) ** 2


def build_cells(caps, max_px):
    c = CASE
    Ly, Lz = c["periods_y"] * A, c["periods_z"] * A
    depth = depth_layers_for(max(caps), c["feature"]["minor_radius_A"])
    common = dict(azimuth_uvw=c["azimuth_uvw"], azimuth_label=c["azimuth_label"], extent_y_A=Ly,
                  extent_z_A=Lz, depth_layers=depth, lattice_parameter_A=c["lattice_parameter_A"],
                  lattice_label=c["lattice_label"], vacuum_above_A=c["structure_vacuum_A"])
    q = A / 4.0
    dz = A / c["slices_per_period"]
    depth_below = (depth - 1) * q

    def cell_of(s):
        return build_feature_reflection_cell(
            s, vacuum_above_flat_surface_A=c["vacuum_above_flat_surface_A"],
            depth_below_A=depth_below, bulk_absorber_A=c["bulk_absorber_A"],
            top_absorber_A=c["top_absorber_A"], entrance_vacuum_z_A=c["entrance_vacuum_slices"] * dz)

    flat = build_si001_flat_reference(**common)
    cells = {None: (flat, cell_of(flat))}
    f = c["feature"]
    for cap in caps:
        feat = BuriedTorus(center_y_A=0.5 * Ly, center_z_A=f["center_z_A"],
                           major_radius_A=f["major_radius_A"], minor_radius_A=f["minor_radius_A"],
                           cap_A=float(cap), label=f["label"], source=f["source"])
        s = build_si001_with_feature(feature=feat, ring_margin_A=c["ring_margin_A"], **common)
        cells[cap] = (s, cell_of(s))
    return cells, depth, dz


def potential_of(cell):
    return AtomicPotential(cell, parameterisation="kirkland",
                           physical_absorption=PhysicalAbsorption(**CASE["physical_absorption"]),
                           frozen_phonons=None, static_lattice_label=CASE["static_lattice_label"])


class Window:
    """A realised potential seen from slice i0 on (to call engine.propagate_slices on a window)."""

    def __init__(self, real, i0):
        self.real, self.i0 = real, i0

    def slice_key(self, i):
        return self.real.slice_key(i + self.i0)

    def projected(self, i):
        return self.real.projected(i + self.i0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--max-pixel-A", required=True, type=float)
    ap.add_argument("--caps", required=True, type=float, nargs="+")
    ap.add_argument("--max-cpu-seconds", required=True, type=float)
    ap.add_argument("--criterion", required=True, choices=("total", "vacuum_origin"),
                    help="the part of the specular difference at P on which the verdict of THIS run "
                         "is taken (stated before the run: stage 1 'total', stage 2 "
                         "'vacuum_origin', report T4 section 2); the other is printed as well")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--reference-summary", type=Path, default=None,
                    help="summary json of an earlier run at another pixel size (optional; compared)")
    ap.add_argument("--reuse-waves", action="store_true",
                    help="load <out>/waves_<tag>.npz of an earlier identical run instead of "
                         "propagating (analysis only; the loop checks still run)")
    ap.add_argument("--debug-slices", type=int, default=None,
                    help="CODE TEST ONLY: propagate the first N slices only (the waves are not at "
                         "the exit plane; outputs tagged DEBUG, not for any conclusion)")
    a = ap.parse_args(argv)
    c = CASE
    t0 = time.perf_counter()
    tag = f"px{a.max_pixel_A:g}_caps" + "-".join(f"{x:g}" for x in a.caps)
    if a.debug_slices is not None:
        tag = "DEBUG_" + tag
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    print(f"STATUS: {STATUS}")
    cells, depth, dz = build_cells(a.caps, a.max_pixel_A)
    s_f, cell_f = cells[None]
    print(f"cells built in {time.perf_counter() - t0:.1f} s: depth {depth} layers, flat {s_f.n_atoms} "
          f"atoms; " + ", ".join(f"cap {k:g}: {cells[k][0].n_atoms} atoms "
                                  f"({s_f.n_atoms - cells[k][0].n_atoms} removed)" for k in a.caps)
          + f"; peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MB")
    for k in a.caps:
        cv = cells[k][1]
        for key in ("extent_x_A", "extent_y_A", "length_z_A", "crystal_start_z_A", "surface_x_A"):
            if getattr(cv, key) != getattr(cell_f, key):
                raise RuntimeError(f"cap {k:g} cell differs from the flat cell in {key}")
    pot_f = potential_of(cell_f)
    V0 = potential_mean_inner_potential_V(pot_f)
    sc = specular_condition_for(c["working_reflection_hkl"], (0, 0, 1), E_keV=c["energy_keV"],
                                V0_V=V0, a_A=A)
    theta = float(sc.theta_ext)
    x_flat = cell_f.metadata["layout"]["highest_surface_x_A"]
    b = c["beam"]
    beam = SheetBeam(height_A=b["height_A"], edge_A=b["edge_A"],
                     x_bottom_A=x_flat + b["bottom_above_flat_surface_at_launch_A"],
                     theta_in_ext_rad=theta, theta_label=c["theta_label"])
    nx = fft_friendly(int(np.ceil(cell_f.extent_x_A / a.max_pixel_A - 1e-9)))
    ny = fft_friendly(int(np.ceil(cell_f.extent_y_A / a.max_pixel_A - 1e-9)))
    params = MultisliceParams(energy_keV=c["energy_keV"], nx=nx, ny=ny, dz_A=dz,
                              propagator=c["propagator"], band_limit=c["band_limit"],
                              backend=c["backend"], precision=c["precision"], threads=c["threads"],
                              absorber=NumericalAbsorber(**c["absorber"]), theta_out_ext_rad=theta,
                              buildup_depth_A=c["buildup_depth_A"],
                              working_reflections_hkl=(c["working_reflection_hkl"],))
    s = reflection_setup(cell_f, potential=pot_f, beam=beam, params=params)
    pots = {None: pot_f}
    feat_checks = {}
    for k in a.caps:
        pots[k] = potential_of(cells[k][1])
        reflection_setup(cells[k][1], potential=pots[k], beam=beam, params=params)
        fc = check_feature_geometry(cells[k][1], beam=beam, theta_out_ext_rad=theta,
                                    theta_int_rad=s["theta_int_in_rad"],
                                    buildup_depth_A=c["buildup_depth_A"],
                                    footprint_margin_A=c["footprint_margin_A"])
        feat_checks[k] = fc
    grid, bc, N = s["grid"], s["bc"], s["n_slices"]
    print(f"grid {nx} x {ny} (dx {grid.dx_A:.5f}, dy {grid.dy_A:.5f} A), {N} slices of {dz:.4f} A, "
          f"theta {theta * 1e3:.4f} mrad, MIP {V0:.4f} V; engine assertions and F1-F5 passed for "
          f"every cell (F5: " + ", ".join(f"cap {k:g} {feat_checks[k]['F5_buried_void_depth']['passed']}"
                                          for k in a.caps) + ")")
    est = estimate_resources(cell_f, params, realisations=1, calibrate_cpu=True)
    n_waves = 1 + 3 * len(a.caps)
    cpu_est = est["cpu"]["seconds_per_realisation"] * c["cpu_calibration_factor"] * (1 + n_waves) / 2
    print(f"CPU estimate {cpu_est:.0f} s (engine estimate x {c['cpu_calibration_factor']} x "
          f"(1 + {n_waves} waves) / 2); limit --max-cpu-seconds {a.max_cpu_seconds:.0f} s")
    if cpu_est > a.max_cpu_seconds:
        print("REFUSED: estimate above --max-cpu-seconds")
        return 2

    # ---- engine pieces, exactly as engine.run_realisation -------------------------------------
    be = get_backend(params.backend, params.precision, params.threads)
    lam, sigma = bc["wavelength_A"], bc["sigma_rad_per_VA"]
    mask = band_limit_mask(grid, params.band_limit)
    P_full, _ = propagator_kernel(grid, dz_A=dz, wavelength_A=lam, kind=params.propagator,
                                  band_mask=mask)
    P_half, _ = propagator_kernel(grid, dz_A=0.5 * dz, wavelength_A=lam, kind=params.propagator,
                                  band_mask=mask)
    P_full = be.asarray(P_full, dtype=be.complex_dtype)
    P_half = be.asarray(P_half, dtype=be.complex_dtype)
    maskb = be.asarray(mask, dtype=be.real_dtype)
    W = absorber_profile_V(grid, cell_f, params.absorber)
    absfac = be.asarray(np.exp(-sigma * W * dz)[:, None], dtype=be.real_dtype)
    psi0 = be.asarray(sheet_beam_wave(beam, grid, lam), dtype=be.complex_dtype)
    sig = be.real_dtype(sigma)
    real = {k: pots[k].realise(grid=grid, dz_A=dz, n_slices=N, backend=be, rng=None)
            for k in pots}

    def t_pair(r, i):
        t = be.xp.exp(1j * sig * r.projected(i)) * absfac
        return t, be.ifft2(be.fft2(t) * maskb)

    counts = {k: np.diff(real[k].starts) for k in real}
    ring = {k: set(np.nonzero(counts[k] != counts[None])[0].tolist()) for k in a.caps}
    for k in a.caps:
        print(f"cap {k:g}: {len(ring[k])} slices hold removed atoms (slices {min(ring[k])}-{max(ring[k])})")
    # the void cell's other slices hold the same atoms in the same order: projected bit for bit
    for k in a.caps:
        other = [i for i in range(N) if i not in ring[k] and counts[None][i] > 0]
        pick = [other[0], other[len(other) // 2], other[-1], min(ring[k]) - 1, max(ring[k]) + 1]
        eq = all(np.array_equal(real[k].projected(i), real[None].projected(i)) for i in pick)
        print(f"cap {k:g}: projected potential of non-void slices {pick} bitwise equal to the flat "
              f"cell's: {eq}")
        if not eq:
            raise RuntimeError("non-void slices differ between the void and the flat cell")

    x_rel = grid.x_A() - cell_f.surface_x_A
    y = grid.y_A()
    fr = cells[a.caps[0]][1].metadata["feature"]
    yc, R, r = float(fr["center_y_A"]), float(fr["major_radius_A"]), float(fr["minor_radius_A"])
    Mx = {k: local_mask(x_rel, k, r, c["local_margin_A"], c["local_ramp_A"]) for k in a.caps}
    lo, hi = c["vacuum_tail_window_x_rel_A"]
    win = ((x_rel >= lo) & (x_rel <= hi))[:, None] & (np.abs(y - yc) <= R + r + bt.RES_A)[None, :]

    def loop(psis: dict, i0: int, n: int):
        """psis: name -> wave; names 'flat', 'full_<cap>', 'local_<cap>', 'tails_<cap>'. Slices
        i0 .. i0 + n - 1, as engine.propagate_slices (first P(dz/2), last P(dz/2))."""
        psis = {k: be.ifft2(be.fft2(v) * P_half) for k, v in psis.items()}
        for j in range(n):
            i = i0 + j
            tf = t_pair(real[None], i)[1]
            ts = {"flat": tf}
            for k in a.caps:
                if i in ring[k]:
                    tv = t_pair(real[k], i)[1]
                    d = tv - tf
                    ts[f"full_{k:g}"] = tv
                    ts[f"local_{k:g}"] = tf + d * (1.0 - Mx[k])[:, None]
                    ts[f"tails_{k:g}"] = tf + d * Mx[k][:, None]
                else:
                    for v in ("full", "local", "tails"):
                        ts[f"{v}_{k:g}"] = tf
            P = P_full if j < n - 1 else P_half
            for name in psis:
                psis[name] = be.ifft2(be.fft2(psis[name] * ts[name]) * P)
        return psis

    G_TAIL = {"0": 0.0, "(0,0,4)": 4.0 / A, "(0,0,8)": 8.0 / A}
    xw = (x_rel >= lo) & (x_rel <= hi)
    yb = np.abs(y - yc) <= R + r + bt.RES_A
    ph = {g: np.exp(-2j * np.pi * f * x_rel[xw])[:, None] for g, f in G_TAIL.items()}

    def tail_stats(k):
        """|d| = |t_void - t_flat| over the void slices: in the vacuum window (x_rel lo..hi, ring's
        y band), before and after the band limit, in the tails and local regions; and the Fourier
        components of d along x in the window at g = 0, (0,0,4), (0,0,8) (|mean_x d e^{-2 pi i g x}|,
        rms over y), the components that can couple vacuum waves to the specular beam."""
        st = dict(vac_max_bl=0.0, vac_sum2_bl=0.0, vac_n=0, vac_max_raw=0.0, far_max_bl=0.0,
                  near_max_bl=0.0, fourier_max={g: 0.0 for g in G_TAIL},
                  fourier_sum2={g: 0.0 for g in G_TAIL}, n_slices=0)
        for i in sorted(ring[k]):
            tf_raw, tf = t_pair(real[None], i)
            tv_raw, tv = t_pair(real[k], i)
            d = be.to_numpy(tv - tf)
            ad = np.abs(d)
            st["vac_max_bl"] = max(st["vac_max_bl"], float(ad[win].max()))
            st["vac_sum2_bl"] += float(np.sum(ad[win] ** 2))
            st["vac_n"] += int(win.sum())
            st["vac_max_raw"] = max(st["vac_max_raw"],
                                    float(np.abs(be.to_numpy(tv_raw - tf_raw))[win].max()))
            st["far_max_bl"] = max(st["far_max_bl"], float(ad[Mx[k] >= 1.0].max()))
            st["near_max_bl"] = max(st["near_max_bl"], float(ad[Mx[k] <= 0.0].max()))
            dw = d[xw][:, yb]
            for g in G_TAIL:
                comp = np.abs(np.mean(dw * ph[g], axis=0))
                v = float(np.sqrt(np.mean(comp ** 2)))
                st["fourier_max"][g] = max(st["fourier_max"][g], v)
                st["fourier_sum2"][g] += v ** 2
            st["n_slices"] += 1
        st["fourier_rms_over_slices"] = {g: float(np.sqrt(st["fourier_sum2"][g] / st["n_slices"]))
                                         for g in G_TAIL}
        return st

    # ---- bit-for-bit checks of the loop against engine.propagate_slices on two windows ---------
    checks = {}
    K = 12
    for lab, i0, key in (("first slices, flat", 0, None),
                         ("void slices, full", min(ring[a.caps[0]]) - 2, a.caps[0])):
        ref, _ = propagate_slices(psi0, realised=Window(real[key], i0), n_slices=K, backend=be,
                                  P_full=P_full, P_half=P_half, band_mask=maskb, sigma=sig,
                                  absorber_factor=absfac)
        name = "flat" if key is None else f"full_{key:g}"
        mine = loop({name: psi0}, i0, K)[name]
        eq = bool(np.array_equal(be.to_numpy(ref), be.to_numpy(mine)))
        checks[lab] = dict(i0=int(i0), n_slices=K, bitwise_equal=eq,
                           max_abs_diff=float(np.abs(be.to_numpy(ref) - be.to_numpy(mine)).max()))
        print(f"loop check ({lab}, slices {i0}-{i0 + K - 1}): bitwise equal to "
              f"engine.propagate_slices: {eq}")
        if not eq:
            raise RuntimeError("the diagnostic loop does not reproduce engine.propagate_slices")

    # ---- the pass -------------------------------------------------------------------------------
    names = ["flat"] + [f"{v}_{k:g}" for k in a.caps for v in ("full", "local", "tails")]
    t1 = time.perf_counter()
    stats = {k: tail_stats(k) for k in a.caps}
    print(f"tail statistics over the void slices: {time.perf_counter() - t1:.1f} s")
    t1 = time.perf_counter()
    wpath = out / f"waves_{tag}.npz"
    if a.reuse_waves:
        with np.load(wpath, allow_pickle=False) as f:
            if str(f["plane"]) != PLANE_TEXT or not np.array_equal(f["x_rel_A"], x_rel):
                raise ValueError(f"{wpath}: plane or grid differ from this run")
            waves = {k: np.array(f[k]) for k in names}
        t_prop = 0.0
        print(f"waves reused from {wpath} (no propagation)")
    else:
        n_run = N if a.debug_slices is None else int(a.debug_slices)
        waves = loop({n_: psi0 for n_ in names}, 0, n_run)
        t_prop = time.perf_counter() - t1
        waves = {k: be.to_numpy(v).astype(np.complex128) for k, v in waves.items()}
        print(f"propagation of {len(names)} waves over {n_run} slices: {t_prop:.1f} s")
        np.savez(wpath, x_rel_A=x_rel, y_A=y, dx_A=grid.dx_A, dy_A=grid.dy_A, plane=PLANE_TEXT,
                 **{k: v for k, v in waves.items()})

    # ---- analysis with tools/plots/buried_torus.py ------------------------------------------------
    meta = dict(beam=bc, theta_out_ext_rad=theta, theta_int_out_rad=s["theta_int_out_rad"],
                cell=dict(surface_x_A=cell_f.surface_x_A, length_z_A=cell_f.length_z_A,
                          crystal_start_z_A=cell_f.crystal_start_z_A),
                slices=dict(dz_A=dz), illumination=beam.describe(lam))

    def ew_of(psi):
        return SimpleNamespace(psi=psi, dx_A=grid.dx_A, dy_A=grid.dy_A, x0_A=grid.x0_A,
                               y0_A=grid.y0_A, z_A=float(N * dz), metadata=meta)

    ew_f = ew_of(waves["flat"])
    pf = bt.specular(ew_f)
    summary = dict(tag=tag, status=STATUS, max_pixel_A=a.max_pixel_A, grid=dict(nx=nx, ny=ny,
                   dx_A=grid.dx_A, dy_A=grid.dy_A), caps={}, loop_checks=checks,
                   prediction="tails/full in [0.8, 1.25] and local/full < 0.2 at P (max and rms), "
                              "every cap")
    kirk = pot_f._param.projected_potential("Si")
    kp = {f"{d:g}A": float(kirk(np.array([d]))[0]) for d in (0.5, 5.0, 7.0)}
    print(f"Kirkland projected potential of one Si atom (abTEM function, V A): {kp}; sigma "
          f"{sigma:.4e} rad/(V A): sigma V(5 A) = {sigma * kp['5A']:.2e} rad, sigma V(7 A) = "
          f"{sigma * kp['7A']:.2e} rad (the physical change of t beyond the local band)")
    summary["kirkland_projected_potential_V_A"] = kp
    verdicts = []
    for k in a.caps:
        g = bt.geometry(ew_of(waves[f"full_{k:g}"]),
                        dict(cell_feature=cells[k][1].metadata["feature"], lattice_a_A=A))
        reg = bt.regions(g, g["core_z0_A"])
        A_ref = float(np.abs(pf)[(g["x_rel"] >= 0) & (g["x_rel"] <= bt.VAC_BAND_A)].max())
        band = np.abs(g["y"] - g["yc"]) <= g["R"] + g["r"] + bt.RES_A
        rec = dict(A_ref=A_ref, P_x_range_A=reg["geom"]["x_projection_A"],
                   x_V_two_beam_A=reg["geom"]["x_V_two_beam_A"], x_V16_A=reg["geom"]["x_V16_A"])
        F = {}
        for v in ("full", "local", "tails"):
            D = waves[f"{v}_{k:g}"] - waves["flat"]
            parts = bt.split_parts(D, ew_f, g["x_rel"])
            F[v] = parts["total"]
            dd = np.abs(parts["total"]) / A_ref
            dv = np.abs(parts["vacuum_origin"]) / A_ref
            bands = {}
            for lo_, hi_ in ((0.5, 3.0), (3.0, 5.0), tuple(reg["geom"]["x_projection_A"]),
                             (11.0, 13.0), (14.0, 21.0)):
                m = ((g["x_rel"] >= lo_) & (g["x_rel"] <= hi_))[:, None] & band[None, :]
                bands[f"{lo_:.2f}-{hi_:.2f}"] = float(dd[m].max())
            rec[v] = dict(P_max=float(dd[reg["P"]].max()),
                          P_rms=float(np.sqrt(np.mean(dd[reg["P"]] ** 2))),
                          P_vacuum_origin_max=float(dv[reg["P"]].max()),
                          P_vacuum_origin_rms=float(np.sqrt(np.mean(dv[reg["P"]] ** 2))),
                          E_max=float(dd[reg["E"]].max()) if reg["E"].any() else None,
                          x_bands_max=bands,
                          location=bt.x_centroid(dd, g, band))
        lin = np.abs(F["full"] - F["local"] - F["tails"]) / A_ref
        rec["linearity_residual_P_max"] = float(lin[reg["P"]].max())
        st = stats[k]
        rec["tail_amplitude"] = dict(
            window=f"x_rel {lo}-{hi} A over the ring's y band, void slices",
            max_abs_d_band_limited=st["vac_max_bl"],
            rms_abs_d_band_limited=float(np.sqrt(st["vac_sum2_bl"] / max(st["vac_n"], 1))),
            max_abs_d_before_band_limit=st["vac_max_raw"],
            max_abs_d_in_tails_region=st["far_max_bl"], max_abs_d_in_local_region=st["near_max_bl"],
            fourier_components_max_over_slices=st["fourier_max"],
            fourier_components_rms_over_slices=st["fourier_rms_over_slices"])
        crit = dict(total=("P_max", "P_rms"),
                    vacuum_origin=("P_vacuum_origin_max", "P_vacuum_origin_rms"))
        ratio = {m: dict(tails=_r(rec["tails"][m], rec["full"][m]),
                         local=_r(rec["local"][m], rec["full"][m]))
                 for ms in crit.values() for m in ms}
        rec["ratios_at_P"] = ratio

        def verdict(ms):
            ok = all(0.8 <= ratio[m]["tails"] <= 1.25 and ratio[m]["local"] < 0.2 for m in ms)
            bad = any(ratio[m]["local"] >= 0.5 or ratio[m]["tails"] < 0.5 for m in ms)
            return "CONFIRMED" if ok else ("NOT CONFIRMED" if bad else "INCONCLUSIVE")

        rec["verdict_by_criterion"] = {kk: verdict(ms) for kk, ms in crit.items()}
        rec["criterion"] = a.criterion
        rec["verdict"] = rec["verdict_by_criterion"][a.criterion]
        verdicts.append(rec["verdict"])
        summary["caps"][f"{k:g}"] = rec
        print(f"\n=== cap {k:g} A (R {R:g} A, r {r:g} A), A_ref {A_ref:.4f}; P = x_rel "
              f"{rec['P_x_range_A'][0]:.2f}-{rec['P_x_range_A'][1]:.2f} A (+{bt.RES_A:g} A); two-beam "
              f"x_V {rec['x_V_two_beam_A']:.2f} A, steepest-row x_V16 {rec['x_V16_A']:.2f} A")
        for v in ("full", "local", "tails"):
            q = rec[v]
            e_txt = "none" if q["E_max"] is None else f"{q['E_max']:.3e}"
            print(f"  {v:5s}: P max |F(D)|/A_ref {q['P_max']:.3e}, rms {q['P_rms']:.3e}, vacuum-origin "
                  f"P max {q['P_vacuum_origin_max']:.3e}; E max {e_txt}; "
                  f"peak x_rel {q['location']['peak_x_rel_A']:+.2f} A, fraction in vacuum "
                  f"{q['location']['fraction_in_vacuum']:.2f}")
            print(f"         max over x_rel bands (ring y band): " + ", ".join(
                f"{kk} {vv:.2e}" for kk, vv in q["x_bands_max"].items()))
        for kk, ms in crit.items():
            print(f"  ratios at P, {kk} part: max tails/full {ratio[ms[0]]['tails']:.3f}, local/full "
                  f"{ratio[ms[0]]['local']:.3f}; rms tails/full {ratio[ms[1]]['tails']:.3f}, "
                  f"local/full {ratio[ms[1]]['local']:.3f} -> {rec['verdict_by_criterion'][kk]}"
                  + ("  [the criterion of this run]" if kk == a.criterion else
                     "  [not the criterion of this run]"))
        print(f"  linearity residual |F(D_full) - F(D_local) - F(D_tails)| / A_ref, max over P: "
              f"{rec['linearity_residual_P_max']:.2e}")
        ta = rec["tail_amplitude"]
        print(f"  tail amplitude |t_void - t_flat| ({ta['window']}): max {ta['max_abs_d_band_limited']:.3e}, "
              f"rms {ta['rms_abs_d_band_limited']:.3e} (before the band limit: max "
              f"{ta['max_abs_d_before_band_limit']:.3e}); max in the tails region "
              f"{ta['max_abs_d_in_tails_region']:.3e}, in the local band {ta['max_abs_d_in_local_region']:.3e}")
        print(f"  Fourier components of d along x in the window (rms over y), max over void slices: "
              + ", ".join(f"g = {gg}: {vv:.3e}" for gg, vv in ta["fourier_components_max_over_slices"].items())
              + "; rms over void slices: "
              + ", ".join(f"{gg}: {vv:.3e}" for gg, vv in ta["fourier_components_rms_over_slices"].items()))
        print(f"  verdict ({a.criterion} criterion of this run, stated before it ran): {rec['verdict']}")
    if len(a.caps) >= 2:
        k1, k2 = a.caps[0], a.caps[1]
        r1, r2 = summary["caps"][f"{k1:g}"], summary["caps"][f"{k2:g}"]
        print(f"\ncap {k1:g} / cap {k2:g}: P max (full) ratio {_r(r1['full']['P_max'], r2['full']['P_max']):.3f}, "
              f"P rms ratio {_r(r1['full']['P_rms'], r2['full']['P_rms']):.3f}; tail amplitude ratio max "
              f"{_r(r1['tail_amplitude']['max_abs_d_band_limited'], r2['tail_amplitude']['max_abs_d_band_limited']):.3f}, "
              f"rms {_r(r1['tail_amplitude']['rms_abs_d_band_limited'], r2['tail_amplitude']['rms_abs_d_band_limited']):.3f}; "
              f"end-face E max ratio {_r(r1['full']['E_max'], r2['full']['E_max']):.3f}")
        f1 = r1["tail_amplitude"]["fourier_components_rms_over_slices"]
        f2 = r2["tail_amplitude"]["fourier_components_rms_over_slices"]
        print(f"cap {k1:g} / cap {k2:g}: P vacuum-origin max ratio "
              f"{_r(r1['full']['P_vacuum_origin_max'], r2['full']['P_vacuum_origin_max']):.3f}, rms "
              f"{_r(r1['full']['P_vacuum_origin_rms'], r2['full']['P_vacuum_origin_rms']):.3f}; tail "
              f"Fourier components (rms over void slices) ratio: "
              + ", ".join(f"{gg} {_r(f1[gg], f2[gg]):.3f}" for gg in f1))
    if a.reference_summary is not None:
        ref = json.loads(a.reference_summary.read_text())
        for kk, rec in summary["caps"].items():
            if kk in ref["caps"]:
                rr = ref["caps"][kk]
                print(f"\npixel comparison, cap {kk} A: this run ({a.max_pixel_A:g} A rule, dx "
                      f"{grid.dx_A:.4f}) vs reference ({ref['max_pixel_A']:g} A rule, dx "
                      f"{ref['grid']['dx_A']:.4f}): P max (full) ratio "
                      f"{_r(rec['full']['P_max'], rr['full']['P_max']):.3f}, P rms ratio "
                      f"{_r(rec['full']['P_rms'], rr['full']['P_rms']):.3f}; tail amplitude ratio max "
                      f"{_r(rec['tail_amplitude']['max_abs_d_band_limited'], rr['tail_amplitude']['max_abs_d_band_limited']):.3f}, "
                      f"rms {_r(rec['tail_amplitude']['rms_abs_d_band_limited'], rr['tail_amplitude']['rms_abs_d_band_limited']):.3f}; "
                      f"end-face E max ratio {_r(rec['full']['E_max'], rr['full']['E_max']):.3f}")
                if "P_vacuum_origin_rms" in rr["full"]:
                    fa = rec["tail_amplitude"]["fourier_components_rms_over_slices"]
                    fb = rr["tail_amplitude"]["fourier_components_rms_over_slices"]
                    print(f"  vacuum-origin P max ratio "
                          f"{_r(rec['full']['P_vacuum_origin_max'], rr['full']['P_vacuum_origin_max']):.3f}, "
                          f"rms {_r(rec['full']['P_vacuum_origin_rms'], rr['full']['P_vacuum_origin_rms']):.3f}; "
                          f"tail Fourier components (rms over void slices) ratio: "
                          + ", ".join(f"{gg} {_r(fa[gg], fb[gg]):.3f}" for gg in fa))
    summary["criterion"] = a.criterion
    overall = ("CONFIRMED" if all(v == "CONFIRMED" for v in verdicts) else
               "NOT CONFIRMED" if any(v == "NOT CONFIRMED" for v in verdicts) else "INCONCLUSIVE")
    summary["verdict"] = overall
    print(f"\nOVERALL VERDICT for this run ({tag}, {a.criterion} criterion): {overall}")
    spath = out / f"summary_{tag}.json"
    spath.write_text(json.dumps(summary, indent=1))
    case_path = out / f"case_{tag}.json"
    case_path.write_text(json.dumps(dict(CASE=CASE, caps=a.caps, max_pixel_A=a.max_pixel_A,
                                         depth_layers=depth, status=STATUS), indent=1, default=str))
    cfg = dict(CASE=CASE, caps=a.caps, max_pixel_A=a.max_pixel_A, nx=nx, ny=ny)
    engines = {ENGINE_NAME: dict(version=reflection_holo.__version__, licence="this repository",
                                 status=VALIDATION_STATUS,
                                 note="engine functions called unchanged; slice loop repeated in "
                                      "this script and checked bit for bit (loop_checks)"),
               "abTEM (Kirkland parameterisation functions only)": dict(
                   version=pot_f.provenance()["abtem_version"],
                   commit=pot_f.provenance()["abtem_commit"],
                   licence="GPL-3.0-or-later (optional dependency)")}
    man = build_manifest(
        run_name=f"t4_m1_{tag}", config=case_path, input_paths=[wpath, spath],
        seeds={"frozen_phonons": None}, thread_count=params.threads,
        precision={"complex": params.precision}, engines=engines,
        wave_planes={k: PLANE_TEXT for k in names}, beam_energy_keV=params.energy_keV,
        extra=dict(configuration_sha256=hashlib.sha256(json.dumps(cfg, sort_keys=True,
                                                                  default=str).encode()).hexdigest(),
                   input_hashes={("flat" if k is None else f"cap{k:g}"):
                                 cells[k][1].metadata.get("atoms_sha256") for k in cells},
                   status=STATUS, timing_s=dict(total=time.perf_counter() - t0, propagation=t_prop),
                   ensemble_rule="static lattice: no ensemble"))
    mp = write_manifest(man, outputs_root=out / "outputs")
    print(f"manifest {mp}; waves {wpath}; summary {spath}; total {time.perf_counter() - t0:.1f} s, "
          f"peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
