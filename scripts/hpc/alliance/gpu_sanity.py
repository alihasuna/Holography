#!/usr/bin/env python
"""gpu-sanity job of the Alliance kit: step 0 of the H2 report's "Recommended run order"
(docs/agent_reports/H2_realistic_supercell_sizing.md §12; H2 is under review) on one GPU.

1. `scripts/hpc/null_test_study/run_study.py --only tfix_bragg_abs0_L0` on the given study copy
   (runtime.backend must equal --backend: cupy in the job) against the stored CPU value of the same
   fixed-beam translation point, read from the repository at run time:
   docs/agent_reports/M2_multislice_engine.md, row "beam fixed (as in any step geometry)"
   (error vs -(k_out - k_in).R and amplitude ratio B/A).
2. `tools/hpc/supercell_sizing.py --measure <new file> --only bu_100_r010 --backend <backend>`
   against the plateau stored in tools/hpc/supercell_sizing_measurements.json (runs.bu_100_r010.
   buildup.R_plateau_abs and R_plateau_arg), which H2 measured with the numpy backend.

The tolerances below were fixed on 2026-09-23 by agent H6 BEFORE any GPU run (none has run) and are
printed at the start of the job output and recorded in gpu_sanity.json; they cannot be changed from
the command line. Exit status: 0 PASS (every comparison); 1 a comparison failed; 2 refused (inputs);
5 a sub-run failed or wrote no result. Status of the engine: UNVALIDATED (this compares backends of
the same engine against stored CPU numbers; it says nothing about the physics).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SANITY_POINT = "tfix_bragg_abs0_L0"
BU_RUN = "bu_100_r010"
M2_REPORT = REPO / "docs" / "agent_reports" / "M2_multislice_engine.md"
M2_ROW_PREFIX = "| beam fixed (as in any step geometry) |"
H2_MEASUREMENTS = REPO / "tools" / "hpc" / "supercell_sizing_measurements.json"
RUN_STUDY = REPO / "scripts" / "hpc" / "null_test_study" / "run_study.py"
SIZING = REPO / "tools" / "hpc" / "supercell_sizing.py"

# ---- tolerances, fixed before any GPU run ------------------------------------------------------
# 1. study point: |err_rad(this run) - err_rad(M2)| and |amp_ratio(this run) - amp_ratio(M2)|.
#    1e-2 rad is the study's own convergence criterion (|err_rad| <= 1e-2, null_test_study/README)
#    and the rung-3 tolerance; the stored value is rounded to 1e-3 (+0.569); the numpy complex64
#    run of the same point on this machine gave 0.568589 (H4 audit §2.3), 4e-4 from it. A wrong
#    propagator, sign or axis on the GPU changes these numbers by order 1.
TOL_STUDY_ERR_RAD = 1e-2
TOL_STUDY_AMP = 1e-2
# 2. build-up strip: |wrap(arg R - arg R_stored)| <= 1e-2 rad and ||R| / |R_stored| - 1| <= 1e-2
#    (H2 §12 step 0: "within 1e-2 rad and 1e-2"; the amplitude is read as RELATIVE, the stricter
#    of the two readings for |R| = 0.27).
TOL_BU_ARG_RAD = 1e-2
TOL_BU_AMP_REL = 1e-2

STATUS = ("UNVALIDATED engine (M2 report): this compares the backend of this run with stored CPU "
          "numbers of the same engine; it says nothing about the physics")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


def study_reference(path: Path = M2_REPORT) -> dict:
    """The stored CPU value of the fixed-beam point, parsed from the M2 report row (exactly as
    stored: the error and the amplitude ratio columns)."""
    lines = Path(path).read_text().splitlines()
    rows = [(i + 1, s) for i, s in enumerate(lines) if s.startswith(M2_ROW_PREFIX)]
    if len(rows) != 1:
        raise RuntimeError(f"{path}: expected exactly one row starting with {M2_ROW_PREFIX!r}, "
                           f"found {len(rows)}")
    lineno, line = rows[0]
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != 4:
        raise RuntimeError(f"{path}:{lineno}: expected 4 columns, got {cells}")
    return dict(point=SANITY_POINT, delta_phi_rad=float(cells[1]), err_rad=float(cells[2]),
                amp_ratio=float(cells[3]), source=f"{_rel(Path(path))}:{lineno}",
                row=line.strip(), file_sha256=_sha256(path),
                note="M2 section 10.1, numpy backend, complex64 (translation_pair default)")


def buildup_reference(path: Path = H2_MEASUREMENTS) -> dict:
    d = json.loads(Path(path).read_text())
    r = d["runs"][BU_RUN]
    b, info = r["buildup"], r["info"]
    return dict(run=BU_RUN, R_plateau_abs=float(b["R_plateau_abs"]),
                R_plateau_arg=float(b["R_plateau_arg"]),
                cell=dict((k, info[k]) for k in ("nx", "ny", "n_slices", "n_atoms", "precision")),
                backend=info.get("backend") or "numpy (not recorded in the file: the stored run "
                                               "predates the tool's --backend option; H2 §2.4)",
                source=f"{_rel(Path(path))} runs.{BU_RUN}.buildup",
                file_sha256=_sha256(path), git=d.get("git"))


def _finite(*xs) -> bool:
    return all(isinstance(x, (int, float)) and math.isfinite(x) for x in xs)


def _wrap(x: float) -> float:
    return (x + math.pi) % (2 * math.pi) - math.pi


def compare_study(res: dict, ref: dict) -> dict:
    out = dict(reference=ref, tolerances=dict(err_rad=TOL_STUDY_ERR_RAD, amp_ratio=TOL_STUDY_AMP))
    problems = []
    if (res.get("point") or {}).get("name") != SANITY_POINT:
        problems.append(f"result is for point {(res.get('point') or {}).get('name')!r}")
    err, amp = res.get("err_rad"), res.get("amp_ratio")
    if not _finite(err, amp):
        problems.append(f"err_rad {err!r} or amp_ratio {amp!r} is not a finite number")
        out.update(passed=False, problems=problems)
        return out
    d_err = abs(err - ref["err_rad"])
    d_amp = abs(amp - ref["amp_ratio"])
    out.update(err_rad=err, amp_ratio=amp, dev_err_rad=d_err, dev_amp_ratio=d_amp,
               wall_s=res.get("wall_s"),
               gpu_model_s=((res.get("estimate") or {}).get("gpu") or {}).get("seconds_total"))
    if d_err > TOL_STUDY_ERR_RAD:
        problems.append(f"err_rad deviates by {d_err:.3e} rad > {TOL_STUDY_ERR_RAD:g}")
    if d_amp > TOL_STUDY_AMP:
        problems.append(f"amp_ratio deviates by {d_amp:.3e} > {TOL_STUDY_AMP:g}")
    out.update(passed=not problems, problems=problems)
    return out


def compare_buildup(meas: dict, ref: dict, backend: str) -> dict:
    out = dict(reference=ref, tolerances=dict(arg_rad=TOL_BU_ARG_RAD, amp_rel=TOL_BU_AMP_REL))
    problems = []
    r = (meas.get("runs") or {}).get(BU_RUN)
    if not r:
        out.update(passed=False, problems=[f"no run {BU_RUN} in the measurement file"])
        return out
    info = r.get("info") or {}
    if info.get("backend") != backend:
        problems.append(f"the strip ran with backend {info.get('backend')!r}, not {backend!r}")
    for k, v in ref["cell"].items():
        if info.get(k) != v:
            problems.append(f"cell differs from the stored run: {k} {info.get(k)!r} != {v!r}")
    b = r.get("buildup") or {}
    a_abs, a_arg = b.get("R_plateau_abs"), b.get("R_plateau_arg")
    if not _finite(a_abs, a_arg):
        problems.append(f"plateau |R| {a_abs!r} or arg {a_arg!r} is not a finite number")
        out.update(passed=False, problems=problems)
        return out
    d_arg = abs(_wrap(a_arg - ref["R_plateau_arg"]))
    d_amp = abs(a_abs / ref["R_plateau_abs"] - 1.0)
    out.update(R_plateau_abs=a_abs, R_plateau_arg=a_arg, dev_arg_rad=d_arg, dev_amp_rel=d_amp,
               run_s=r.get("run_s"), build_s=r.get("build_s"))
    if d_arg > TOL_BU_ARG_RAD:
        problems.append(f"plateau phase deviates by {d_arg:.3e} rad > {TOL_BU_ARG_RAD:g}")
    if d_amp > TOL_BU_AMP_REL:
        problems.append(f"plateau amplitude deviates by {d_amp:.3e} (relative) > "
                        f"{TOL_BU_AMP_REL:g}")
    out.update(passed=not problems, problems=problems)
    return out


def _run(cmd, log: Path) -> int:
    print("== " + " ".join(str(c) for c in cmd), flush=True)
    with open(log, "w") as fh:
        p = subprocess.Popen([str(c) for c in cmd], cwd=REPO, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            fh.write(line)
            sys.stdout.write(line)
        return p.wait()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--study", required=True, type=Path, help="the job's study copy")
    ap.add_argument("--backend", required=True, choices=("cupy", "numpy"),
                    help="cupy in the job; numpy only to test this script on a CPU")
    ap.add_argument("--threads", required=True, type=int)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=False)
    from reflection_holo.io.config import load_yaml_unique
    study = load_yaml_unique(a.study.read_bytes())
    if (study.get("runtime") or {}).get("backend") != a.backend:
        print(f"REFUSED: {a.study} has runtime.backend {(study.get('runtime') or {}).get('backend')!r}, "
              f"not {a.backend!r}", flush=True)
        return 2
    ref_s, ref_b = study_reference(), buildup_reference()
    res = dict(schema="reflholo_gpu_sanity/1", status=STATUS, backend=a.backend,
               threads=a.threads, job_id=os.environ.get("SLURM_JOB_ID"),
               tolerances=dict(study_err_rad=TOL_STUDY_ERR_RAD, study_amp_ratio=TOL_STUDY_AMP,
                               buildup_arg_rad=TOL_BU_ARG_RAD, buildup_amp_rel=TOL_BU_AMP_REL,
                               fixed="2026-09-23 by agent H6, before any GPU run"),
               references=dict(study=ref_s, buildup=ref_b),
               study_file=dict(path=str(a.study), sha256=_sha256(a.study)))
    print(f"GPU SANITY ({a.backend}); tolerances fixed before any GPU run: study point "
          f"|d err| <= {TOL_STUDY_ERR_RAD:g} rad, |d amp| <= {TOL_STUDY_AMP:g}; strip "
          f"|d arg R| <= {TOL_BU_ARG_RAD:g} rad, |d |R|| / |R| <= {TOL_BU_AMP_REL:g}", flush=True)
    print(f"reference 1: {SANITY_POINT} err {ref_s['err_rad']:+.3f} rad, amplitude ratio "
          f"{ref_s['amp_ratio']:.3f} ({ref_s['source']})", flush=True)
    print(f"reference 2: {BU_RUN} plateau |R| {ref_b['R_plateau_abs']:.6f}, arg "
          f"{ref_b['R_plateau_arg']:+.6f} rad ({ref_b['source']}, backend {ref_b['backend']})",
          flush=True)
    rc = 0
    # 1. study point
    t0 = time.time()
    st1 = _run([sys.executable, RUN_STUDY, "--config", a.study, "--out", a.out / "study",
                "--only", SANITY_POINT], a.out / "study.log")
    rpath = a.out / "study" / "outputs" / "null_test_study" / f"{SANITY_POINT}.json"
    if st1 != 0 or not rpath.is_file():
        res["study"] = dict(passed=False, problems=[f"run_study.py status {st1}, result "
                                                    f"{'present' if rpath.is_file() else 'missing'}"])
        rc = 5
    else:
        res["study"] = compare_study(json.loads(rpath.read_text()), ref_s)
        res["study"]["result_file"] = str(rpath)
    res["study"]["job_wall_s"] = time.time() - t0
    # 2. build-up strip
    t0 = time.time()
    mpath = a.out / "buildup_measure.json"
    st2 = _run([sys.executable, SIZING, "--measure", mpath, "--only", BU_RUN, "--backend",
                a.backend, "--threads", str(a.threads)], a.out / "buildup.log")
    if st2 != 0 or not mpath.is_file():
        res["buildup"] = dict(passed=False, problems=[f"supercell_sizing.py status {st2}, file "
                                                      f"{'present' if mpath.is_file() else 'missing'}"])
        rc = 5
    else:
        res["buildup"] = compare_buildup(json.loads(mpath.read_text()), ref_b, a.backend)
        res["buildup"]["result_file"] = str(mpath)
    res["buildup"]["job_wall_s"] = time.time() - t0
    ok = res["study"]["passed"] and res["buildup"]["passed"]
    if rc == 0:
        rc = 0 if ok else 1
    res["passed"] = rc == 0
    def _s(x):
        return f"{x:.1f} s" if _finite(x) else "? s"

    for key, label in (("study", SANITY_POINT), ("buildup", BU_RUN)):
        r = res[key]
        if "dev_err_rad" in r:
            print(f"{label}: err {r['err_rad']:+.6f} rad (dev {r['dev_err_rad']:.2e}), amplitude "
                  f"ratio {r['amp_ratio']:.6f} (dev {r['dev_amp_ratio']:.2e}); {_s(r['wall_s'])} "
                  f"(GPU_ASSUMED model {_s(r['gpu_model_s'])}) -> "
                  f"{'PASS' if r['passed'] else 'FAIL'}", flush=True)
        elif "dev_arg_rad" in r:
            print(f"{label}: plateau |R| {r['R_plateau_abs']:.6f} (rel dev {r['dev_amp_rel']:.2e}), "
                  f"arg {r['R_plateau_arg']:+.6f} rad (dev {r['dev_arg_rad']:.2e}); run "
                  f"{_s(r['run_s'])} -> {'PASS' if r['passed'] else 'FAIL'}", flush=True)
        else:
            print(f"{label}: FAIL", flush=True)
        for p in r.get("problems", []):
            print(f"  {label}: {p}", flush=True)
    rfile = a.out / "gpu_sanity.json"
    rfile.write_text(json.dumps(res, indent=1, default=str))
    from reflection_holo.provenance.manifest import build_manifest, write_manifest
    inputs = [a.study, M2_REPORT, H2_MEASUREMENTS, rfile] + [
        Path(res[k]["result_file"]) for k in ("study", "buildup") if "result_file" in res[k]]
    m = build_manifest(run_name="gpu_sanity", config=a.study, input_paths=inputs, seeds={},
                       thread_count=a.threads,
                       precision={"complex": "complex64 (study point and strip)"},
                       engines={"reflection_holo.forward.multislice": dict(
                           status="UNVALIDATED (M2 report)", backend=a.backend)},
                       wave_planes={"exit_wave": "exit plane z = L_z (no further propagation)"},
                       beam_energy_keV=200.0,
                       extra=dict(purpose="GPU sanity of the Alliance kit (H2 run order step 0); "
                                          "not a result", passed=res["passed"]))
    mpath_m = write_manifest(m, outputs_root=a.out / "outputs")
    verdict = {0: "PASS", 1: "FAIL (a comparison exceeded its tolerance)",
               5: "FAIL (a sub-run failed or wrote no result)"}[rc]
    print(f"GPU SANITY: {verdict}; result {rfile}, manifest {mpath_m}", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
