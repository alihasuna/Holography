#!/usr/bin/env python3
"""Flat-surface rocking curve of the multislice kernel (specular intensity in the aperture vs angle).

Cheap: a flat surface is uniform in y, so a narrow cell (a few lattice periods) is enough.
Usage: python scripts/rocking_flat.py --surface 001 --hkl 0 0 8 [--span 2.0 --step 0.1]
Writes outputs/rocking/rocking_<surface>_<hkl>.{png,json}. Smoke-test kernel (docs/08).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflection_holo import geometry as geo  # noqa: E402
from reflection_holo.crystal import build_slab  # noqa: E402
from reflection_holo.forward import multislice as ms  # noqa: E402


def rocking(frame, hkl, offsets_mrad, a=5.4309, E=200.0, n_y=4, ny=120, nx=1024, dx=0.1, x0=-60.0,
            depth=56.0, B=0.46, absr=0.05, xc=22.0, H=20.0, edge=4.0, q_ap=0.06, backend="numpy"):
    xp = ms.get_xp(backend)
    pos, Ly, Lz = build_slab(frame, a, n_y, depth)
    grid = ms.Grid(nx=nx, ny=ny, dx=dx, dy=Ly / ny, x0=x0)
    lam, sigma = geo.wavelength_A(E), geo.interaction_constant(E)
    V0 = ms.mean_inner_potential(8 / a**3)
    cond = geo.SpecularCondition(E, V0, a, tuple(hkl))
    V, dz = ms.slice_potentials(pos, Lz, 2, grid, B, absr, xp=xp)
    band = xp.asarray(grid.band_mask())
    T = [ms.transmission(v, sigma, ms.absorber_profile(grid, -38.0, 14.0, 60.0), dz, band, xp=xp) for v in V]
    R, ph = [], []
    for off in offsets_mrad:
        th = cond.theta_ext + off * 1e-3
        n = int(np.ceil(2 * xc / np.tan(th) / dz))
        psi0 = ms.illumination(grid, th, lam, xc, H, edge)
        psi = ms.to_numpy(ms.run(psi0, T, ms.propagator(grid, dz, lam, xp=xp), n, xp=xp))
        df, _ = ms.dark_field(psi, grid, th, lam, q_ap, 8.0, 3.0)
        R.append(float(np.sum(np.abs(df) ** 2) / np.sum(np.abs(psi0) ** 2)))
        ph.append(float(np.angle(np.sum(df))))
    return cond, np.array(R), np.array(ph)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", choices=["001", "111"], default="001")
    ap.add_argument("--hkl", type=int, nargs=3, required=True)
    ap.add_argument("--span", type=float, default=2.0)
    ap.add_argument("--step", type=float, default=0.1)
    ap.add_argument("--backend", default="numpy")
    ap.add_argument("--ny", type=int, default=120, help="lateral pixels over 4 periods (dy 0.128 A for Si(001))")
    args = ap.parse_args()
    frame = geo.SI001_FRAME if args.surface == "001" else geo.SI111_FRAME
    offs = np.arange(-args.span, args.span + 1e-9, args.step)
    cond, R, ph = rocking(frame, args.hkl, offs, backend=args.backend, ny=args.ny)
    i = int(np.argmax(R))
    res = {"surface": args.surface, "hkl": args.hkl, "theta_ext_bragg_mrad_V0potential": cond.theta_ext * 1e3,
           "offsets_mrad": offs.tolist(), "R": R.tolist(), "peak_offset_mrad": float(offs[i]), "R_peak": float(R[i]),
           "R_at_zero_offset": float(R[np.argmin(np.abs(offs))])}
    out = Path("outputs/rocking")
    out.mkdir(parents=True, exist_ok=True)
    tag = f"{args.surface}_{''.join(str(h) for h in args.hkl)}"
    (out / f"rocking_{tag}.json").write_text(json.dumps(res, indent=1))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(cond.theta_ext * 1e3 + offs, R, "o-")
    ax.axvline(cond.theta_ext * 1e3, color="k", ls=":", label="refraction-corrected Bragg angle")
    ax.set(xlabel="theta_ext (mrad)", ylabel="specular fraction in aperture",
           title=f"Si({args.surface}) {tuple(args.hkl)} flat-surface rocking curve (smoke-test kernel)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / f"rocking_{tag}.png", dpi=110)
    print(json.dumps({k: v for k, v in res.items() if k not in ("offsets_mrad", "R")}))


if __name__ == "__main__":
    main()
