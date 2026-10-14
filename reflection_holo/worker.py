"""Task-farm worker: one process per GPU, dynamic claiming, restartable.

  python -m reflection_holo.worker run   --run-dir RUN --stage STAGE --worker-index I \
          [--deadline EPOCH] [--max-failures 2]
  python -m reflection_holo.worker clean --run-dir RUN      (remove stale claims)
  python -m reflection_holo.worker status --run-dir RUN --stage STAGE

Layout of RUN: tasks_<stage>.jsonl (from reflection_holo.campaign plan),
results/<stage>/<task_id>.h5, claims/<task_id>.claim, failed/<task_id>.<n>.txt,
logs/.  A claim is created with O_CREAT|O_EXCL (atomic on Lustre); results are
written to a temporary name and renamed.  Tasks are taken longest first.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import socket
import subprocess
import sys
import time
import traceback


def _paths(run, stage):
    return dict(tasks=os.path.join(run, f"tasks_{stage}.jsonl"),
                results=os.path.join(run, "results", stage),
                claims=os.path.join(run, "claims"),
                failed=os.path.join(run, "failed"),
                logs=os.path.join(run, "logs"))


def load_tasks(path):
    with open(path) as fh:
        tasks = [json.loads(line) for line in fh if line.strip()]
    return sorted(tasks, key=lambda t: (-cost_units(t), t["task_id"]))


def cost_units(t):
    """FFT point-planes plus GEMM work converted with the assumed throughput ratio
    (5e9 point-planes/s against 3e12 multiply-adds/s on an H100)."""
    c = t.get("cost", {})
    return c.get("fft_work", 0.0) + c.get("gemm_work", 0.0) / 600.0


def n_failures(failed_dir, tid):
    return len(glob.glob(os.path.join(failed_dir, f"{tid}.*.txt")))


def claim(claims_dir, tid, info):
    path = os.path.join(claims_dir, f"{tid}.claim")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return None
    with os.fdopen(fd, "w") as fh:
        json.dump(info, fh)
    return path


def run_worker(args):
    from .backend import backend_info, get_xp
    from .io import write_result
    from .provenance import task_manifest
    from .simulate import run_task

    P = _paths(args.run_dir, args.stage)
    for d in (P["results"], P["claims"], P["failed"], P["logs"]):
        os.makedirs(d, exist_ok=True)
    job = os.environ.get("SLURM_JOB_ID", "local")
    logf = open(os.path.join(P["logs"], f"worker_{args.stage}_{job}_{args.worker_index}.log"), "a")

    def log(msg):
        logf.write(time.strftime("%H:%M:%S ") + msg + "\n")
        logf.flush()

    tasks = load_tasks(P["tasks"])
    log(f"worker {args.worker_index} on {socket.gethostname()} job {job}: {len(tasks)} tasks")
    rate = None            # measured seconds per unit of fft_work
    done = 0
    for t in tasks:
        tid = t["task_id"]
        out = os.path.join(P["results"], f"{tid}.h5")
        if os.path.exists(out) or n_failures(P["failed"], tid) >= args.max_failures:
            continue
        if args.deadline and rate is not None:
            need = rate * max(cost_units(t), 1.0) * 1.5
            if time.time() + need > args.deadline:
                log(f"deadline: not starting {tid} (needs ~{need:.0f} s)")
                continue
        c = claim(P["claims"], tid, dict(job=job, worker=args.worker_index,
                                        host=socket.gethostname(), time=time.time()))
        if c is None:
            continue
        log(f"start {tid} {t.get('label', '')}")
        t0 = time.time()
        try:
            xp = get_xp(t["backend"])
            binfo = backend_info(xp)
            res = run_task(t, log=log)
            t1 = time.time()
            write_result(out, res, t, task_manifest(t, binfo, t0, t1))
            fw = cost_units(t)
            if fw > 0:
                r = (t1 - t0) / fw
                rate = r if rate is None else max(rate, r)
            done += 1
            log(f"done  {tid} in {t1 - t0:.1f} s")
            os.remove(c)
        except Exception:  # noqa: BLE001
            n = n_failures(P["failed"], tid) + 1
            with open(os.path.join(P["failed"], f"{tid}.{n}.txt"), "w") as fh:
                fh.write(json.dumps(t, sort_keys=True) + "\n\n" + traceback.format_exc())
            log(f"FAIL  {tid}: {traceback.format_exc().splitlines()[-1]}")
            os.remove(c)
        finally:
            if t["backend"] == "cupy":
                import cupy
                cupy.get_default_memory_pool().free_all_blocks()
                cupy.get_default_pinned_memory_pool().free_all_blocks()
    log(f"worker {args.worker_index} finished: {done} tasks this session")


def running_jobs():
    try:
        out = subprocess.run(["squeue", "-h", "-o", "%i", "-u", os.environ.get("USER", "")],
                             capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return None
        return {line.strip().split("_")[0] for line in out.stdout.splitlines() if line.strip()}
    except Exception:  # noqa: BLE001
        return None


def clean(args):
    claims = glob.glob(os.path.join(args.run_dir, "claims", "*.claim"))
    jobs = running_jobs()
    me = os.environ.get("SLURM_JOB_ID")
    removed = 0
    for c in claims:
        try:
            info = json.load(open(c))
        except Exception:  # noqa: BLE001
            info = {}
        j = str(info.get("job"))
        alive = (jobs is not None and j in jobs and j != me)
        if jobs is None and not args.force:
            print("squeue unavailable: use --force to remove all claims")
            return
        if not alive:
            os.remove(c)
            removed += 1
    print(f"removed {removed} stale claims of {len(claims)}")


def status(args):
    P = _paths(args.run_dir, args.stage)
    tasks = load_tasks(P["tasks"])
    done = sum(os.path.exists(os.path.join(P["results"], f"{t['task_id']}.h5")) for t in tasks)
    failed = {os.path.basename(f).split(".")[0] for f in glob.glob(os.path.join(P["failed"], "*.txt"))}
    failed &= {t["task_id"] for t in tasks}
    print(f"stage {args.stage}: {done}/{len(tasks)} done, {len(failed)} with failures")
    for tid in sorted(failed):
        f = sorted(glob.glob(os.path.join(P["failed"], f"{tid}.*.txt")))[-1]
        print("  ", tid, open(f).read().strip().splitlines()[-1])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("run", "clean", "status"))
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--stage")
    ap.add_argument("--worker-index", type=int, default=0)
    ap.add_argument("--deadline", type=float, default=None)
    ap.add_argument("--max-failures", type=int, default=2)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    if args.action == "run":
        run_worker(args)
    elif args.action == "clean":
        clean(args)
    else:
        status(args)


if __name__ == "__main__":
    sys.exit(main())
