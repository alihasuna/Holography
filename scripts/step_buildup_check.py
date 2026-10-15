#!/usr/bin/env python3
"""Diagnostic: does the multislice step phase converge to -q_ext h as the illuminated footprint
grows? A finite sheet beam of height H illuminates a footprint H/tan(theta) along the beam; if that
is not much longer than the dynamical build-up length, a raised strip (illuminated h/tan(theta)
earlier) is compared with the reference at a different stage of the build-up.

Two strips (reference, +4 layers), no defect, narrow cell. Usage:
  python scripts/step_buildup_check.py [--heights 30 80] [--hkl 0 0 12]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import geometry as geo  # noqa: E402
from reflection_holo.forward import multislice as ms  # noqa: E402
from reflection_holo.structure.sections import build_sections  # noqa: E402

OFFSETS = {(0, 0, 8): 0.8, (0, 0, 12): -0.6}  # rocking-curve maxima (scripts/rocking_flat.py)


def run(hkl, H, periods=(12, 12), a=5.4309, E=200.0, dx=0.1, dy_target=0.128, q_ap=0.06):
    s = build_sections(geo.SI001_FRAME, a, list(periods), [0, 4], 56.0)
    xc = H / 2 + 11.0
    top = xc + H / 2 + 2 * s.heights[1] + 12.0
    x0 = -58.0
    nx = int(np.ceil((top - x0) / dx / 32) * 32)
    ny = int(round(s.Ly / dy_target / 8) * 8)
    grid = ms.Grid(nx=nx, ny=ny, dx=dx, dy=s.Ly / ny, x0=x0)
    lam, sigma = geo.wavelength_A(E), geo.interaction_constant(E)
    V0 = ms.mean_inner_potential(8 / a**3)
    c = geo.SpecularCondition(E, V0, a, hkl)
    theta = c.theta_ext + OFFSETS[hkl] * 1e-3
    V, dz = ms.slice_potentials(s.positions, s.Lz, 2, grid, 0.46, 0.05)
    band = grid.band_mask()
    T = [ms.transmission(v, sigma, ms.absorber_profile(grid, -38.0, 14.0, 60.0), dz, band) for v in V]
    n = int(np.ceil(2 * xc / np.tan(theta) / dz))
    psi = ms.run(ms.illumination(grid, theta, lam, xc, H, 4.0), T, ms.propagator(grid, dz, lam), n)
    df, _ = ms.dark_field(psi, grid, theta, lam, q_ap, 8.0, 3.0)
    y = grid.y
    cols = [(y > s.boundaries[k] + 12) & (y < s.boundaries[k + 1] - 12) for k in range(2)]
    roi = np.ones(nx, bool)
    for cl in cols:
        rI = np.mean(np.abs(df[:, cl]) ** 2, axis=1)
        roi &= rI > 0.5 * rI.max()
    z = [np.mean(df[roi][:, cl]) for cl in cols]
    step = float(np.angle(z[1] / z[0]))
    return {"hkl": list(hkl), "H_A": H, "footprint_A": H / np.tan(theta), "n_slices": n,
            "rows": int(roi.sum()), "step_ms_rad": step, "amp_ratio_2_over_1": float(abs(z[1] / z[0])),
            "step_minus_q_ext_h_rad": float(np.angle(np.exp(-1j * 2 * geo.k_rad_per_A(E) * np.sin(theta) * s.heights[1])))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heights", type=float, nargs="+", default=[30.0, 80.0])
    ap.add_argument("--hkl", type=int, nargs=3, action="append")
    args = ap.parse_args()
    hkls = [tuple(h) for h in (args.hkl or [[0, 0, 8], [0, 0, 12]])]
    res = []
    for hkl in hkls:
        for H in args.heights:
            t = time.time()
            r = run(hkl, H)
            r["runtime_s"] = time.time() - t
            res.append(r)
            print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
    out = Path("outputs/rocking")
    out.mkdir(parents=True, exist_ok=True)
    (out / "step_buildup_check.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
