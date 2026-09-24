#!/usr/bin/env python
"""The `dry-run` job of the Alliance kit (H4 F2): `python -m reflection_holo.pipeline dry-run` of a
configuration inside a CPU job (never on a login node for production-size cells), with the peak
resident memory of that process, so that the memory of a later CPU job can be requested knowingly.

The dry run builds the whole structure and the reflection cell and prints the engine's estimates
without propagating. Its "memory per realisation" counts the engine's arrays of one realisation
only; the peak RSS measured here is the host memory of the structure build and the estimate (a run
holds these plus the engine arrays of every concurrent realisation).

Writes into --out: dry_run.txt (the dry run's output), dry_run_report.json (the dry run's full
report with the configuration's path and SHA-256: `kit.py plan --gpu-mem-from-dry-run` reads the
engine's GPU device peak from it), dry_run_resources.json (status, wall time, peak RSS, atoms if
printed), and a run manifest under outputs/manifests/. Exit status: the dry run's
(0 ok; 3 configuration refused; 4 for a cupy configuration on this GPU-less node AFTER the estimates
were printed, which is expected).
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--variant", required=True, help="'' for none")
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--threads", required=True, type=int)
    ap.add_argument("--backend", required=True, help="backend of the configuration (recorded)")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=False)
    cfg = Path(a.config) if os.path.isabs(a.config) else a.repo / a.config
    cmd = [sys.executable, "-m", "reflection_holo.pipeline", "dry-run", "--config", str(cfg),
           "--report-json", str((a.out / "dry_run_report.json").resolve())]
    if a.variant:
        cmd += ["--variant", a.variant]
    print("== " + " ".join(cmd), flush=True)
    t0 = time.time()
    with open(a.out / "dry_run.txt", "w") as fh:
        p = subprocess.Popen(cmd, cwd=a.repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
        for line in p.stdout:
            fh.write(line)
            sys.stdout.write(line)
        st = p.wait()
    wall = time.time() - t0
    peak_kb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss      # Linux: kB
    rec = dict(schema="reflholo_alliance_dry_run/1", config=str(cfg), variant=a.variant or None,
               backend=a.backend, exit_status=st, wall_s=wall, peak_rss_MB=peak_kb / 1024.0,
               peak_rss_counts="the dry-run process (structure build, reflection cell, estimate); "
                               "a run holds these plus the engine arrays of each concurrent "
                               "realisation",
               threads=a.threads, host=os.uname().nodename,
               report_json=(str(a.out / "dry_run_report.json")
                            if (a.out / "dry_run_report.json").is_file() else None),
               slurm_job_id=os.environ.get("SLURM_JOB_ID"))
    (a.out / "dry_run_resources.json").write_text(json.dumps(rec, indent=1))
    print(f"== dry run: exit status {st}, wall {wall:.1f} s, peak RSS {peak_kb / 1024.0:.0f} MB "
          f"(the structure build and the estimate; the engine's 'memory per realisation' above "
          f"counts the engine arrays only)", flush=True)
    if st == 4 and a.backend == "cupy":
        print("NOTE: status 4 = the cupy backend is not available on this CPU node; the estimates "
              "above were printed before that check (expected for a cupy configuration)",
              flush=True)
    from reflection_holo.provenance.manifest import build_manifest, write_manifest
    m = build_manifest(run_name="alliance_dry_run", config=cfg, input_paths=[cfg],
                       seeds={}, thread_count=a.threads,
                       precision={"complex": "not applicable (dry run: no propagation)"},
                       engines={}, wave_planes={}, beam_energy_keV=200.0,
                       extra=dict(purpose="sizing dry run of the Alliance kit; not a result",
                                  resources=rec))
    print(f"manifest {write_manifest(m, outputs_root=a.out / 'outputs')}", flush=True)
    return st


if __name__ == "__main__":
    sys.exit(main())
