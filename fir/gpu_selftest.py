#!/usr/bin/env python3
"""GPU self-test and throughput benchmark, run inside a 1-GPU job before the campaign.

1. CPU (numpy) and GPU (cupy) give the same reflection coefficients on a small
   static task and on a small frozen-phonon task (same seed) -> agreement to 1e-9.
2. Throughput of the production grids: multislice planes (FFT work) and the
   structure-factor GEMM of frozen-phonon planes -> RUN/benchmark.json, used by
   `reflection_holo.campaign check --benchmark` to estimate GPU-hours per stage.
3. GPU and driver description -> RUN/gpu_info.txt.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from reflection_holo.backend import backend_info, get_xp  # noqa: E402
from reflection_holo.campaign import load_config, make_task, numerics, windows  # noqa: E402
from reflection_holo.grid import Grid  # noqa: E402
from reflection_holo.multislice import Propagator, propagate  # noqa: E402
from reflection_holo.potential import PotentialBuilder  # noqa: E402
from reflection_holo.simulate import run_task  # noqa: E402


def small_task(cfg, mode, seed=None):
    """A small task on the grid of configs/smoke_cpu.yaml (strong absorption, short
    cell), with the physics of the campaign configuration except W_in."""
    smoke = load_config(os.path.join(ROOT, "configs", "smoke_cpu.yaml"))
    num = numerics(smoke)
    c = dict(cfg)
    c["dy_target_A"] = smoke["dy_target_A"]
    ph = json.loads(json.dumps(cfg["physics"]))
    ph["inelastic_absorption_W_V"] = smoke["physics"]["inelastic_absorption_W_V"]
    nyp = 2 if mode == "frozen_phonon" else 1
    return make_task(c, "selftest", "flat_rocking", "si111_110",
                     dict(kind="flat", level=0, n_y_periods=nyp), windows([16.0], 6.0), num,
                     mode=mode, seed=seed, phys=ph, label=f"selftest {mode}")


def equivalence(cfg):
    out = {}
    for mode, seed in (("static", None), ("frozen_phonon", 7)):
        t = small_task(cfg, mode, seed)
        res = {}
        for backend in ("numpy", "cupy"):
            t["backend"] = backend
            t0 = time.time()
            r = run_task(t, log=lambda s: None)
            res[backend] = (r["windows"][0]["r"], time.time() - t0)
        d = float(np.max(np.abs(res["numpy"][0] - res["cupy"][0])))
        out[mode] = dict(max_abs_diff=d, seconds_numpy=res["numpy"][1],
                         seconds_cupy=res["cupy"][1], pass_=bool(d < 1e-9))
        print(f"equivalence {mode}: max|r_numpy - r_cupy| = {d:.2e} "
              f"(numpy {res['numpy'][1]:.1f} s, cupy {res['cupy'][1]:.1f} s)")
    return out


def bench_planes(xp, Nx, Ny, B, n=60, dtype="complex128"):
    g = Grid(Nx, Ny, Nx * 0.08, Ny * 0.08, x0=-230.0)
    prop = Propagator(g, 0.0250793, xp, dtype)
    P = prop(1.92)
    psi = xp.ones((B, Nx, Ny), dtype=dtype)
    t = xp.exp(1j * xp.random.random((Nx, Ny))).astype(dtype)
    rows = xp.asarray(np.array([[100, 125]] * B))
    rec = xp.zeros((B, 2, n, Ny), dtype=dtype)
    for i in range(5):
        psi = propagate(psi, P, xp) * t
    xp.cuda.Stream.null.synchronize()
    t0 = time.time()
    ar = xp.arange(B)[:, None]
    for i in range(n):
        psi = propagate(psi, P, xp)
        psi *= t[None]
        rec[:, :, i, :] = psi[ar, rows, :]
    xp.cuda.Stream.null.synchronize()
    dt = (time.time() - t0) / n
    return B * Nx * Ny / dt, dt


def bench_gemm(xp, Nx, Ny, n_atoms, n=10, dtype="complex128"):
    g = Grid(Nx, Ny, Nx * 0.08, Ny * 0.08, x0=-230.0)
    pb = PotentialBuilder(g, xp, 200.0, dtype=dtype)
    rng = np.random.default_rng(0)
    x = rng.uniform(-225, 0, n_atoms)
    y = rng.uniform(0, g.Ly, n_atoms)
    pb.projected(x, y)
    xp.cuda.Stream.null.synchronize()
    t0 = time.time()
    for _ in range(n):
        pb.projected(x + rng.normal(0, 0.08, n_atoms), y)
    xp.cuda.Stream.null.synchronize()
    dt = (time.time() - t0) / n
    work = len(pb.ix) * len(pb.iy) * n_atoms
    return work / dt, dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "fir_m2_campaign.yaml"))
    args = ap.parse_args()
    os.makedirs(args.run_dir, exist_ok=True)
    cfg = load_config(args.config)
    xp = get_xp("cupy")
    info = backend_info(xp)
    print("GPU:", info)
    try:
        smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=60).stdout
    except Exception as exc:  # noqa: BLE001
        smi = f"nvidia-smi failed: {exc}"
    with open(os.path.join(args.run_dir, "gpu_info.txt"), "w") as fh:
        fh.write(json.dumps(info, indent=1) + "\n\n" + smi)
    eq = equivalence(cfg)
    cases = {}
    fft_rates = []
    for (Nx, Ny, B) in ((5120, 84, 4), (5120, 336, 4), (7680, 2520, 1), (7680, 48, 1)):
        rate, dt = bench_planes(xp, Nx, Ny, B)
        cases[f"planes Nx={Nx} Ny={Ny} B={B}"] = dict(points_per_s=rate, seconds_per_plane=dt)
        fft_rates.append(rate)
        print(f"planes Nx={Nx} Ny={Ny} B={B}: {dt*1e3:.2f} ms/plane, {rate:.3e} point-planes/s")
    gemm_rates = []
    for (Nx, Ny, na) in ((5120, 336, 600), (7680, 2520, 4300)):
        rate, dt = bench_gemm(xp, Nx, Ny, na)
        cases[f"gemm Nx={Nx} Ny={Ny} atoms={na}"] = dict(work_per_s=rate, seconds_per_plane=dt)
        gemm_rates.append(rate)
        print(f"potential Nx={Nx} Ny={Ny} atoms={na}: {dt*1e3:.2f} ms/plane, {rate:.3e} MAC/s")
    bench = dict(fft_points_per_s=float(min(fft_rates)), gemm_points_per_s=float(min(gemm_rates)),
                 cases=cases, equivalence=eq, gpu=info,
                 note="measured by fir/gpu_selftest.py; the minimum over the cases is used")
    with open(os.path.join(args.run_dir, "benchmark.json"), "w") as fh:
        json.dump(bench, fh, indent=1)
    ok = all(v["pass_"] for v in eq.values())
    print("SELFTEST", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
