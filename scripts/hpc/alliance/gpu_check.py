#!/usr/bin/env python
"""GPU check of the Alliance kit: proves (or disproves) that the cupy path of the multislice engine
works on this node before any other GPU job is accepted (the cupy backend has never been executed:
README_HPC.md, M2 report). Run inside a GPU job by job.sbatch (`submit.sh <cluster> gpu-check`).

Steps: (1) cupy import, CUDA runtime/driver versions, device name and memory; (2) cupy FFT against
numpy on a seeded random array, complex128 and complex64; (3) two tiny multislice runs from the test
suite (a continuum refraction case, rung 1; and a small atomistic Si(001) a/2 step with the Kirkland
potential) with the numpy backend in complex128 as reference and the cupy backend in complex128 and
complex64. Every comparison uses a tolerance fixed below BEFORE the first GPU run (none has been
run); a failure is reported, never loosened. On success a PASS record is written to --pass-dir,
which submit.sh requires before it accepts the other GPU jobs.

Outputs in --out: gpu_check.json (every number), outputs/manifests/gpu_check_<UTC>.json (the run
manifest: package versions, commit, precision, threads, input hashes, 200 keV).
Exit status: 0 PASS; 1 a comparison failed; 4 cupy not importable or no GPU visible.
Status of the engine: UNVALIDATED (this check tests numerical agreement of the backends, not the
physics).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tests" / "forward"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import PASS_SCHEMA, engine_code_sha256  # noqa: E402  (the gate reads what is written here)

# ---- tolerances, fixed before any GPU run (max |a - b| / max |reference|) ----------------------
# FFT, complex128: double-precision FFT round-off is ~1e-16 x log2(N) (N = 65536 points -> ~2e-15);
# 1e-10 leaves five orders of magnitude and still catches any single-precision path (>= 1e-7).
TOL_FFT_C128 = 1e-10
# FFT, complex64: single-precision round-off ~6e-8 x log2(N) ~ 1e-6; 1e-4 leaves two orders.
TOL_FFT_C64 = 1e-4
# Multislice exit wave, cupy complex128 vs numpy complex128: the same algorithm in double
# precision; accumulated round-off over ~1400 slices stays far below 1e-9 (numpy vs numpy with
# different thread counts is bitwise or ~1e-15 close); a different result means a different path.
TOL_MS_C128 = 1e-9
# Multislice exit wave, cupy complex64 vs numpy complex128. Measured here (numpy complex64 vs numpy
# complex128, same cases, 2026-09-23): 1.8e-5 (rung 1 case) and 9.2e-5 (atomistic step case).
# cuFFT and pocketfft round differently; 1e-3 is about ten times the measured single-precision
# deviation, while a wrong propagator, sign or axis gives deviations of order 1.
TOL_MS_C64 = 1e-3

STATUS = ("UNVALIDATED engine (M2 report): this check compares the cupy and numpy backends of the "
          "same engine; it says nothing about the physics")


def _rel(a, ref) -> float:
    a = np.asarray(a, dtype=np.complex128)
    ref = np.asarray(ref, dtype=np.complex128)
    return float(np.abs(a - ref).max() / np.abs(ref).max())


def device_info():
    """Import cupy and describe the device; raises RuntimeError when unusable."""
    try:
        import cupy as cp
    except Exception as exc:                         # ImportError or a CUDA library error
        raise RuntimeError(f"cupy is not importable: {type(exc).__name__}: {exc}") from exc
    try:
        n = cp.cuda.runtime.getDeviceCount()
    except Exception as exc:                         # e.g. CUDARuntimeError without a driver
        raise RuntimeError(f"cupy cannot query a GPU: {type(exc).__name__}: {exc}") from exc
    if n < 1:
        raise RuntimeError("cupy sees no GPU (getDeviceCount() == 0)")
    try:
        dev = cp.cuda.Device(0)
        props = cp.cuda.runtime.getDeviceProperties(0)
        free, total = dev.mem_info
        name = props["name"].decode() if isinstance(props["name"], bytes) else str(props["name"])
        return dict(cupy_version=cp.__version__, device_count=int(n), device_name=name,
                    compute_capability=str(dev.compute_capability),
                    memory_total_bytes=int(total), memory_free_bytes=int(free),
                    cuda_runtime_version=int(cp.cuda.runtime.runtimeGetVersion()),
                    cuda_driver_version=int(cp.cuda.runtime.driverGetVersion()),
                    cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"))
    except Exception as exc:
        raise RuntimeError(f"cupy cannot describe GPU 0: {type(exc).__name__}: {exc}") from exc


def fft_check(seed: int):
    import cupy as cp
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((256, 256)) + 1j * rng.standard_normal((256, 256))
    out = {}
    for dtype, tol in ((np.complex128, TOL_FFT_C128), (np.complex64, TOL_FFT_C64)):
        xd = x.astype(dtype)
        ref = np.fft.fft2(x)                         # double-precision reference
        t0 = time.perf_counter()
        g = cp.fft.fft2(cp.asarray(xd))
        back = cp.fft.ifft2(g)
        cp.cuda.Device(0).synchronize()
        dt = time.perf_counter() - t0
        e_fwd = _rel(cp.asnumpy(g), ref)
        e_rt = _rel(cp.asnumpy(back), x)
        name = np.dtype(dtype).name
        out[name] = dict(forward_rel_err=e_fwd, roundtrip_rel_err=e_rt, tolerance=tol,
                         seconds=dt, passed=bool(e_fwd <= tol and e_rt <= tol))
    return out


def tiny_cases():
    """(name, builder(precision) -> (cell, pot, beam, params)) from the test suite's own cases."""
    from ladder_cases import THETA_0008, rung1_case
    from null_test_cases import LEGACY_M2_BEAM, LEGACY_M2_CLEAN_DEPTH_A, step_case, theta_0008
    from reflection_holo.forward.multislice import PhysicalAbsorption

    def rung1(prec):
        cell, pot, beam, params, _ = rung1_case(THETA_0008, dx=0.1, dz=4.0, propagator="exact",
                                                precision=prec)
        return cell, pot, beam, params

    ab = PhysicalAbsorption(model="proportional", ratio=0.0,
                            label="ASSUMPTION: no absorption (gpu-check test case)")

    def step(prec):
        return step_case(theta=theta_0008(), width_periods=2, extra_A=0.0, absorption=ab,
                         precision=prec, clean_depth_A=LEGACY_M2_CLEAN_DEPTH_A, azimuth="110",
                         **LEGACY_M2_BEAM)

    return [("rung1_continuum_refraction", rung1), ("atomistic_a2_step_w2", step)]


def run_case(builder, backend, precision, threads):
    from reflection_holo.forward.multislice import run_realisation
    cell, pot, beam, params = builder(precision)
    params = dataclasses.replace(params, backend=backend, threads=int(threads))
    t0 = time.perf_counter()
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    dt = time.perf_counter() - t0
    psi = np.asarray(ew.psi)
    return psi, dict(backend=backend, precision=precision, seconds=dt, nx=params.nx, ny=params.ny,
                     n_slices=ew.metadata["slices"]["n_slices"], plane=ew.plane,
                     dx_A=ew.dx_A, dy_A=ew.dy_A, finite=bool(np.isfinite(psi).all()))


def multislice_check(threads, backends=("cupy",), cases=None):
    """numpy complex128 reference against each backend in complex128 and complex64."""
    out = {}
    for name, builder in (cases or tiny_cases()):
        ref, rinfo = run_case(builder, "numpy", "complex128", threads)
        rec = dict(reference=rinfo, runs=[])
        for be in backends:
            for prec, tol in (("complex128", TOL_MS_C128), ("complex64", TOL_MS_C64)):
                psi, info = run_case(builder, be, prec, threads)
                same_grid = psi.shape == ref.shape and info["plane"] == rinfo["plane"]
                err = _rel(psi, ref) if same_grid else float("inf")
                info.update(rel_err_vs_numpy_complex128=err, tolerance=tol,
                            passed=bool(same_grid and info["finite"] and rinfo["finite"]
                                        and err <= tol))
                rec["runs"].append(info)
        out[name] = rec
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--threads", required=True, type=int)
    ap.add_argument("--pass-dir", required=True, type=Path)
    ap.add_argument("--cluster", required=True)
    ap.add_argument("--env-id", required=True)
    ap.add_argument("--seed", type=int, required=True)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=False)
    # the engine code this check exercises (F9: a PASS unlocks GPU jobs only for this code)
    engine = engine_code_sha256(REPO)
    print(f"engine code {engine['sha256']} ({len(engine['files'])} files under "
          f"{', '.join(engine['dirs'])})", flush=True)
    res = dict(schema="reflholo_gpu_check/1", status=STATUS, cluster=a.cluster, env_id=a.env_id,
               engine_code=engine,
               job_id=os.environ.get("SLURM_JOB_ID"), threads=a.threads, seed=a.seed,
               tolerances=dict(fft_complex128=TOL_FFT_C128, fft_complex64=TOL_FFT_C64,
                               multislice_complex128=TOL_MS_C128,
                               multislice_complex64=TOL_MS_C64))
    rc = 0
    try:
        res["device"] = device_info()
        print(f"cupy {res['device']['cupy_version']}: {res['device']['device_count']} device(s), "
              f"{res['device']['device_name']}, CC {res['device']['compute_capability']}, "
              f"{res['device']['memory_total_bytes'] / 2**30:.1f} GiB, CUDA runtime "
              f"{res['device']['cuda_runtime_version']}, driver "
              f"{res['device']['cuda_driver_version']}", flush=True)
    except RuntimeError as exc:
        res["device"] = dict(error=str(exc))
        print(f"GPU CHECK: FAIL (exit 4): {exc}", flush=True)
        rc = 4
    if rc == 0:
        try:
            res["fft"] = fft_check(a.seed)
            for k, v in res["fft"].items():
                print(f"FFT {k}: forward {v['forward_rel_err']:.2e}, round trip "
                      f"{v['roundtrip_rel_err']:.2e} (tol {v['tolerance']:.0e}) "
                      f"{'PASS' if v['passed'] else 'FAIL'}", flush=True)
            res["multislice"] = multislice_check(a.threads)
            for name, rec in res["multislice"].items():
                r = rec["reference"]
                print(f"{name}: grid {r['nx']} x {r['ny']}, {r['n_slices']} slices; numpy "
                      f"complex128 {r['seconds']:.2f} s", flush=True)
                for run in rec["runs"]:
                    print(f"  {run['backend']} {run['precision']}: {run['seconds']:.2f} s, rel. "
                          f"dev. {run['rel_err_vs_numpy_complex128']:.2e} (tol "
                          f"{run['tolerance']:.0e}) {'PASS' if run['passed'] else 'FAIL'}",
                          flush=True)
            ok = (all(v["passed"] for v in res["fft"].values())
                  and all(r["passed"] for rec in res["multislice"].values() for r in rec["runs"]))
            rc = 0 if ok else 1
        except Exception as exc:                     # a cupy/CUDA error in the middle: recorded
            import traceback
            res["error"] = traceback.format_exc()
            print(f"GPU CHECK: FAIL: {type(exc).__name__}: {exc}", flush=True)
            rc = 1
    res["passed"] = rc == 0
    rpath = a.out / "gpu_check.json"
    rpath.write_text(json.dumps(res, indent=1))
    from reflection_holo.provenance.manifest import build_manifest, write_manifest
    m = build_manifest(run_name="gpu_check", config=None, input_paths=[rpath], seeds={"fft": a.seed},
                       thread_count=a.threads,
                       precision={"complex": "complex128 (reference and cupy) and complex64 (cupy)"},
                       engines={"reflection_holo.forward.multislice": dict(
                           status="UNVALIDATED (M2 report)")},
                       wave_planes={"exit_wave": "exit plane z = L_z (no further propagation)"},
                       beam_energy_keV=200.0,
                       extra=dict(purpose="GPU backend check of the Alliance kit; not a result",
                                  passed=res["passed"]))
    mpath = write_manifest(m, outputs_root=a.out / "outputs")
    if rc == 0:
        a.pass_dir.mkdir(parents=True, exist_ok=True)
        rec = dict(schema=PASS_SCHEMA, passed=True, cluster=a.cluster, env_id=a.env_id,
                   engine_code_sha256=engine["sha256"], engine_files=engine["files"],
                   job_id=res["job_id"], result=str(rpath), manifest=str(mpath),
                   device=res["device"], commit=m["repository"]["commit"],
                   tolerances=res["tolerances"])
        base = f"PASS_{a.cluster}_{a.env_id}_{res['job_id']}"
        ppath = None
        for k in range(100):              # F13: a requeued job (same id) adds a record
            cand = a.pass_dir / (f"{base}.json" if k == 0 else f"{base}_requeue{k}.json")
            try:
                with open(cand, "x", encoding="utf-8") as fh:        # never overwritten
                    json.dump(rec, fh, indent=1)
                ppath = cand
                break
            except FileExistsError:
                continue
        if ppath is None:
            print(f"GPU CHECK: PASS, but no free record name {base}_requeue<k>.json", flush=True)
            return 1
        print(f"GPU CHECK: PASS (record {ppath}; valid for cluster {a.cluster}, environment "
              f"{a.env_id} and engine code {engine['sha256'][:12]})", flush=True)
    elif rc == 1:
        print("GPU CHECK: FAIL (a comparison exceeded its tolerance or the GPU path raised; see "
              "gpu_check.json); do not run other GPU jobs on this environment", flush=True)
    print(f"result {rpath}, manifest {mpath}", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
