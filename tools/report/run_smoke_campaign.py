#!/usr/bin/env python3
"""Re-run the cheap smoke tests of the pipeline on the current commit and write a campaign log (R1).

Usage (from the repository root):
    PYTHONPATH=. venv/bin/python tools/report/run_smoke_campaign.py --out ROOT [--only NAME ...]
                                                                   [--timeout-s SECONDS]

Every run is the pipeline CLI ``python -m reflection_holo.pipeline`` on a committed configuration
(configs/demo_smoke_si001.yaml and its variants, configs/demo_smoke_torus_{trench,ridge}.yaml,
configs/demo_convergence_si001.yaml as member jobs plus assembly), one after the other, each into
its own new directory ROOT/<name>/ (the pipeline refuses a non-empty directory). The thread
variables OMP/OPENBLAS/MKL/NUMEXPR_NUM_THREADS are set to the configurations' runtime.threads (4)
so that the run manifests record a consistent thread check. Nothing is written under outputs/.

Campaign log: ROOT/campaign_log.json and ROOT/campaign_log.txt with the repository commit, the git
status (porcelain), the SHA-256 of the reflection_holo package tree, and per run: the command, the
exit status, the wall time, the CPU time of the child process (user + system), the output
directory and the verdict line printed by the CLI. stdout/stderr of each run: ROOT/logs/<name>.log.

A run that exceeds --timeout-s (wall; required, no default) is killed and recorded as NOT COMPLETED.
DEMO runs: purpose "demo; not comparable to experiment"; the multislice engine is UNVALIDATED for
step heights (engine VALIDATION_STATUS, copied into every run's summary).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = "configs/demo_smoke_si001.yaml"
THREADS = 4          # runtime.threads of every configuration below (asserted at start)

# (smoke-test id, run name, config, variant); order = execution order
RUNS = [
    ("S1", "S1_base", BASE, None),
    ("S2", "S2_multislice_tiny", BASE, "multislice_tiny"),
    ("S3", "S3_multislice_tiny_thermal", BASE, "multislice_tiny_thermal"),
    ("S4", "S4_plasmon_losses", BASE, "plasmon_losses"),
    ("S5", "S5_oxide_2p0nm", BASE, "oxide_2p0nm"),
    ("S5", "S5_oxide_2p0nm_no_absorption", BASE, "oxide_2p0nm_no_absorption"),
    ("S5", "S5_oxide_1p5nm", BASE, "oxide_1p5nm"),
    ("S5", "S5_oxide_1p5nm_no_absorption", BASE, "oxide_1p5nm_no_absorption"),
    ("S5", "S5_multislice_tiny_oxide_2p0nm", BASE, "multislice_tiny_oxide_2p0nm"),
    ("S6", "S6_torus_trench", "configs/demo_smoke_torus_trench.yaml", None),
    ("S6", "S6_torus_ridge", "configs/demo_smoke_torus_ridge.yaml", None),
    ("S9", "S9_convergence", "configs/demo_convergence_si001.yaml", None),   # members + assembly
]


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True,
                          text=True).stdout


def _env() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[v] = str(THREADS)
    return env


def _run_cmd(cmd: list[str], log: Path, timeout_s: float) -> dict:
    """Run one command, append its output to log; return status, wall and child CPU seconds."""
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.perf_counter()
    start = _utc()
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"$ {' '.join(cmd)}\n# start {start}\n")
        fh.flush()
        try:
            p = subprocess.run(cmd, cwd=REPO, env=_env(), stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, timeout=timeout_s)
            out, rc, status = p.stdout, p.returncode, ("OK" if p.returncode == 0 else
                                                       f"FAILED (exit {p.returncode})")
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode()
            rc, status = None, f"NOT COMPLETED (killed after the {timeout_s:.0f} s wall limit)"
        wall = time.perf_counter() - t0
        r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
        fh.write(out or "")
        fh.write(f"# end {_utc()} status {status} wall {wall:.1f} s\n\n")
    cpu = (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime)
    return dict(command=" ".join(cmd), start_utc=start, exit_status=rc, status=status,
                wall_s=round(wall, 2), cpu_user_plus_sys_s=round(cpu, 2), stdout=out or "")


def _verdict(stdout: str) -> str:
    """The CLI's first result line: 'NO HEIGHT: ...' or 'heights: ...' (verbatim)."""
    for line in stdout.splitlines():
        if line.startswith("NO HEIGHT") or line.startswith("heights:"):
            return line.strip()
    return "(no verdict line printed)"


def run_pipeline(name: str, config: str, variant: str | None, root: Path, timeout_s: float) -> dict:
    out = root / name
    cmd = [sys.executable, "-m", "reflection_holo.pipeline", "run", "--config", config,
           "--out", str(out)]
    if variant:
        cmd += ["--variant", variant]
    rec = _run_cmd(cmd, root / "logs" / f"{name}.log", timeout_s)
    rec["verdict"] = _verdict(rec.pop("stdout"))
    rec["output_dir"] = str(out)
    return rec


def run_convergence(name: str, config: str, root: Path, timeout_s: float) -> dict:
    """members -> run-member K (K = 0 .. n-1) -> run --members-dir (docs: report E3)."""
    log = root / "logs" / f"{name}.log"
    mem_dir = root / f"{name}_members"
    mem_dir.mkdir(parents=True, exist_ok=False)
    steps = []
    m = _run_cmd([sys.executable, "-m", "reflection_holo.pipeline", "members", "--config", config],
                 log, timeout_s)
    steps.append({k: v for k, v in m.items() if k != "stdout"})
    if m["exit_status"] != 0:
        return dict(status=m["status"], steps=steps, verdict="(members listing failed)",
                    output_dir=str(root / name), wall_s=m["wall_s"],
                    cpu_user_plus_sys_s=m["cpu_user_plus_sys_s"], command=m["command"])
    # stdout and stderr are merged in the log: parse the JSON object from its first "{"
    table, _ = json.JSONDecoder().raw_decode(m["stdout"][m["stdout"].index("{"):])
    (mem_dir / "members_table.json").write_text(json.dumps(table, indent=1) + "\n")
    n = int(table["n_members"])
    for k in range(n):
        s = _run_cmd([sys.executable, "-m", "reflection_holo.pipeline", "run-member", "--config",
                      config, "--member", str(k), "--out", str(mem_dir / f"m{k}")], log, timeout_s)
        steps.append({kk: v for kk, v in s.items() if kk != "stdout"})
        if s["exit_status"] != 0:
            return dict(status=f"member {k}: {s['status']}", steps=steps, verdict="(member failed)",
                        output_dir=str(root / name), n_members=n,
                        wall_s=sum(x["wall_s"] for x in steps),
                        cpu_user_plus_sys_s=sum(x["cpu_user_plus_sys_s"] for x in steps),
                        command="; ".join(x["command"] for x in steps))
    a = _run_cmd([sys.executable, "-m", "reflection_holo.pipeline", "run", "--config", config,
                  "--out", str(root / name), "--members-dir", str(mem_dir)], log, timeout_s)
    verdict = _verdict(a.pop("stdout"))
    steps.append(a)
    return dict(status=a["status"], steps=steps, verdict=verdict, output_dir=str(root / name),
                members_dir=str(mem_dir), n_members=n,
                wall_s=round(sum(x["wall_s"] for x in steps), 2),
                cpu_user_plus_sys_s=round(sum(x["cpu_user_plus_sys_s"] for x in steps), 2),
                command="; ".join(x["command"] for x in steps))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, type=Path, help="campaign root (created)")
    ap.add_argument("--only", nargs="*", default=None, help="run names to run (default: all)")
    ap.add_argument("--timeout-s", required=True, type=float,
                    help="wall-time limit per command (runs beyond it are NOT COMPLETED)")
    args = ap.parse_args(argv)
    root = args.out.resolve()
    if str(root).startswith(str(REPO / "outputs")):
        raise SystemExit("refused: campaign outputs must not go under the repository's outputs/")
    (root / "logs").mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(REPO))
    import numpy
    from reflection_holo.pipeline.config import load_pipeline_file
    from reflection_holo.provenance.manifest import package_tree_sha256
    selected = [r for r in RUNS if args.only is None or r[1] in args.only]
    for _, name, config, variant in selected:
        cfg = load_pipeline_file(REPO / config, variant=variant)
        if cfg.value("runtime", "threads") != THREADS:
            raise SystemExit(f"{name}: runtime.threads {cfg.value('runtime', 'threads')} != {THREADS}")
    head = dict(
        started_utc=_utc(), repository=str(REPO), commit=_git("rev-parse", "HEAD").strip(),
        branch=_git("rev-parse", "--abbrev-ref", "HEAD").strip(),
        git_status_porcelain=_git("status", "--porcelain").splitlines(),
        tracked_diff_vs_head_empty=(_git("diff", "HEAD", "--stat").strip() == ""),
        package_tree=package_tree_sha256(REPO), python=platform.python_version(),
        numpy=numpy.__version__, executable=sys.executable, host_cpus=os.cpu_count(),
        load_average_at_start=list(os.getloadavg()), thread_env=THREADS,
        timeout_s=args.timeout_s,
        note="demo runs; not comparable to experiment; multislice engine UNVALIDATED for step "
             "heights (engine VALIDATION_STATUS in each summary.json)")
    runs = []
    log_json = root / "campaign_log.json"
    for sid, name, config, variant in selected:
        print(f"[{_utc()}] {name} ...", flush=True)
        if sid == "S9":
            rec = run_convergence(name, config, root, args.timeout_s)
        else:
            rec = run_pipeline(name, config, variant, root, args.timeout_s)
        rec.update(smoke_test=sid, name=name, config=config, variant=variant)
        runs.append(rec)
        print(f"    {rec['status']}; wall {rec['wall_s']:.1f} s; CPU {rec['cpu_user_plus_sys_s']:.1f} s;"
              f" {rec['verdict']}", flush=True)
        log_json.write_text(json.dumps(dict(head, runs=runs), indent=1) + "\n")
    head["finished_utc"] = _utc()
    log_json.write_text(json.dumps(dict(head, runs=runs), indent=1) + "\n")
    lines = [f"R1 smoke campaign; commit {head['commit']} ({head['branch']}); started "
             f"{head['started_utc']}, finished {head['finished_utc']}",
             f"git status --porcelain at start: {head['git_status_porcelain'] or 'clean'}",
             f"tracked files identical to HEAD: {head['tracked_diff_vs_head_empty']}",
             f"reflection_holo package tree sha256 {head['package_tree']['sha256']} "
             f"({head['package_tree']['n_files']} files)",
             f"python {head['python']}, numpy {head['numpy']}, {head['host_cpus']} CPUs, load at "
             f"start {head['load_average_at_start']}, thread variables = {THREADS}", ""]
    for r in runs:
        lines += [f"{r['smoke_test']} {r['name']}: {r['status']}; wall {r['wall_s']:.1f} s; child CPU "
                  f"(user+sys) {r['cpu_user_plus_sys_s']:.1f} s",
                  f"    command: {r['command']}", f"    output: {r['output_dir']}",
                  f"    verdict: {r['verdict']}"]
    (root / "campaign_log.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if all(r["status"] == "OK" for r in runs) else 1


if __name__ == "__main__":
    sys.exit(main())
