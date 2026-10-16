"""R2 driver: kernel rocking curves for Si(001) (008), (0,0,12) and Si(111) (4,-4,4) at 200 keV.

Usage:
    python scripts/run_R2.py --accept-assumptions --absorption off [--n 41] [--quick]
    python scripts/run_R2.py --accept-assumptions --absorption proportional --w-over-v 0.1

* V0_SI (item 20) is MISSING: the kinematic reference angles need --accept-assumptions (12.0 V,
  printed as an ASSUMPTION). Without it the script exits with code 2.
* Absorption (item 21) is MISSING: --absorption is required; 'proportional' is an ASSUMPTION
  (Peng ch.13 contradiction 2) and needs --accept-assumptions. The same choice is used by the 1D check.
--quick uses dz = 0.1, dy = 0.15 (dy must keep the (0,0,12) rod inside the 2/3 band).
Writes outputs/R2_rocking_curves.csv and .svg; prints the peak, convergence and timing tables.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from reflection_holo import project_inputs as P  # noqa: E402
from reflection_holo.geometry import Surface, specular_orders  # noqa: E402
from reflection_holo.multislice.reflectivity import rocking_curve, peak_table  # noqa: E402

E = 200e3
TARGETS = [("Si(001)", Surface((0, 0, 1), (1, 1, 0)), (0, 0, 8)),
           ("Si(001)", Surface((0, 0, 1), (1, 1, 0)), (0, 0, 12)),
           ("Si(111)", Surface((1, -1, 1), (1, 1, 0)), (4, -4, 4))]


def kin_angle(surface, hkl, V0):
    for d in specular_orders(surface, E, V0=V0):
        if tuple(d["hkl"]) == tuple(hkl):
            return d["theta_ext"]
    raise KeyError(hkl)


def svg(path, curves):
    W, H = 900, 300 * len(curves)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">']
    for k, (name, th, Rk, R1) in enumerate(curves):
        y0 = 300 * k
        x = lambda t: 60 + 800 * (t - th.min()) / (th.max() - th.min())  # noqa: E731
        y = lambda r: y0 + 260 - 230 * r  # noqa: E731
        for R, col in ((Rk, "black"), (R1, "red")):
            if np.all(np.isfinite(R)):
                pts = " ".join(f"{x(t):.1f},{y(r):.1f}" for t, r in zip(th, R))
                out.append(f'<polyline fill="none" stroke="{col}" points="{pts}"/>')
        out.append(f'<text x="60" y="{y0+20}">{name}: |r|^2 kernel (black), 1D (red); '
                   f'{th.min()*1e3:.2f}-{th.max()*1e3:.2f} mrad</text>')
    out.append("</svg>")
    open(path, "w").write("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=41)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--accept-assumptions", action="store_true")
    ap.add_argument("--absorption", choices=("off", "proportional"), required=True)
    ap.add_argument("--w-over-v", type=float, default=0.1)
    a = ap.parse_args()
    try:
        V0 = float(P.get("V0_SI", accept_assumptions=a.accept_assumptions))
    except P.MissingProjectInput as e:
        print(f"R2 ABORTED: MissingProjectInput: {e}")
        return 2
    if a.absorption == "off":
        ab = dict(absorption=False)
        ab1d = False
        print("absorption: OFF (explicit switch; W = 0 in kernel and 1D)")
    else:
        if not a.accept_assumptions:
            print("R2 ABORTED: --absorption proportional is an ASSUMPTION; add --accept-assumptions")
            return 2
        model = {"name": "proportional", "parameters": {"fraction": a.w_over_v}, "label": "ASSUMPTION",
                 "source": "run_R2 --absorption proportional; contradicted by card:peng_ch13 p.17, p.21"}
        ab = dict(absorption=True, absorption_model=model, accept_assumptions=True)
        ab1d = a.w_over_v
        print(f"ASSUMPTION used: W/V = {a.w_over_v} in kernel and 1D")
    kw = dict(dz=0.1, dy=0.15, absorber_thickness=20.0) if a.quick else {}
    os.makedirs("outputs", exist_ok=True)
    rows, curves, peaks = [], [], []
    t_all = time.perf_counter()
    from reflection_holo.reflectivity1d import rocking_curve_1d
    for name, surf, hkl in TARGETS:
        th0 = kin_angle(surf, hkl, V0)
        th = np.linspace(th0 - 1.5e-3, th0 + 1.5e-3, a.n)
        rc = rocking_curve(surf, E, th, **ab, **kw)
        r1 = rocking_curve_1d(surf, E, th, absorption=ab1d).r
        pk = peak_table(rc)
        tpa = rc.meta["t_per_angle_s"].mean()
        peaks.append((name, hkl, th0, pk, rc.meta["t_setup_s"], tpa))
        curves.append((f"{name} {hkl}", th, np.abs(rc.r) ** 2, np.abs(r1) ** 2))
        for t, rk, rr in zip(th, rc.r, r1):
            rows.append(f"{name},{hkl},{t*1e3:.4f},{abs(rk)**2:.6e},{np.angle(rk):.6f},"
                        f"{abs(rr)**2:.6e},{np.angle(rr):.6f}")
        print(f"{name} {hkl}: V0_meas={rc.meta['V0_meas']:.3f} V  W0_meas={rc.meta['W0_meas']:.4f} V  "
              f"grid={rc.meta['grid']} dx={rc.meta['dx']:.4f} A  depth={rc.meta['depth']:.1f} A  "
              f"vacuum={rc.meta['vacuum']:.1f} A  L(peak)={rc.meta['angles'][a.n//2]['L']:.0f} A")
    with open("outputs/R2_rocking_curves.csv", "w") as f:
        f.write("surface,hkl,theta_ext_mrad,R_kernel,arg_kernel,R_1d,arg_1d\n" + "\n".join(rows) + "\n")
    svg("outputs/R2_rocking_curves.svg", curves)

    print("\nPEAK TABLE (200 keV)")
    print(f"{'target':22s} {'th_kin(R1)':>10s} {'th_peak':>9s} {'shift':>8s} {'R_peak':>7s} "
          f"{'FWHM':>7s} {'arg r':>7s} {'s/angle':>8s} {'100-angle min':>13s}")
    for name, hkl, th0, pk, ts, tpa in peaks:
        print(f"{name+' '+str(hkl):22s} {th0*1e3:10.3f} {pk['theta_peak']*1e3:9.3f} "
              f"{(pk['theta_peak']-th0)*1e3:8.3f} {pk['R_peak']:7.4f} {pk['fwhm']*1e3:7.3f} "
              f"{pk['arg_peak']:7.3f} {tpa:8.2f} {(ts+100*tpa)/60:13.1f}")

    print("\nCONVERGENCE TABLE: Si(001) (008) at the kernel peak angle")
    name, hkl, th0, pk, _, _ = peaks[0]
    th = [pk["theta_peak"]]
    base = rocking_curve(TARGETS[0][1], E, th, **ab, **kw)
    L0, Vv = base.meta["angles"][0]["L"], base.meta["vacuum"]
    var = [("base", {}), ("dx/2", {"dx": 0.96}),
           ("dz/2,dy/2", {"dz": kw.get("dz", 0.08) / 2, "dy": kw.get("dy", 0.15) / 2}),
           ("2x vacuum", {"vacuum": 2 * Vv}), ("2x length", {"length_x": 2 * L0, "vacuum": 2 * Vv})]
    print(f"{'variant':12s} {'|r|^2':>9s} {'d|r|^2':>9s} {'arg r':>8s} {'d arg':>8s}")
    for lab, v in var:
        r = base.r[0] if lab == "base" else rocking_curve(TARGETS[0][1], E, th, **ab, **(kw | v)).r[0]
        print(f"{lab:12s} {abs(r)**2:9.5f} {abs(r)**2-abs(base.r[0])**2:9.5f} {np.angle(r):8.4f} "
              f"{np.angle(r/base.r[0]):8.4f}")
    print(f"\ntotal wall time {time.perf_counter()-t_all:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
