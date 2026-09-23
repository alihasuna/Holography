#!/usr/bin/env python
"""Helper of the Alliance kit (scripts/hpc/alliance/): reads clusters.yaml and the environment record
written by setup_alliance.sh, validates a submission and builds the sbatch command. Called by
submit.sh and job.sbatch; not meant to be run by hand (but `plan` is harmless: it only prints).

    kit.py plan --cluster C --job J --account A --time T --repo R --env-dir E --argv-out F [...]
    kit.py study-point --study S --index I          # name of point I of a study file
    kit.py modules-diff --recorded F --current G    # compare two `module -t list` outputs
    kit.py job-record --out F [--extra KEY=VALUE ...]

Rules (docs/05, docs/agent_reports/H1): no default replaces a required input (account and time
limit are required; memory is required for CPU jobs); every cluster value comes from clusters.yaml
with its wiki locator; a value the wiki does not state (NOT_FOUND) is never invented.
Exit status: 0 ok; 2 refused (usage, a missing or invalid input, a policy limit); 3 configuration
refused by the pipeline gate.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import socket
import sys
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
CLUSTERS_YAML = KIT_DIR / "clusters.yaml"
JOB_SCRIPT = KIT_DIR / "job.sbatch"
NOT_FOUND = "NOT_FOUND"

DEFAULT_STUDY = "scripts/hpc/null_test_study/study.yaml"
# Job definitions of this repository. "config" is part of the job's definition (which run it is),
# not a stand-in for a PROJECT_INPUT; the `pipeline` job takes any configuration (--config).
JOBS = {
    "gpu-check": dict(kind="gpu_check"),
    "smoke": dict(kind="pipeline", config="configs/demo_smoke_si001.yaml"),
    "demo-gpu": dict(kind="pipeline", config="configs/demo_hpc_si001.yaml", backend="cupy"),
    "pipeline": dict(kind="pipeline", config=None),
    "torus": dict(kind="torus"),
    "null-study": dict(kind="null_study"),
}
TORUS_KINDS = ("trench", "ridge", "flat")
# scripts/torus/run_torus_multislice.py fixes CASE["threads"] = 4 and backend numpy (T1 runner)
TORUS_THREADS = 4

# measured memory hints printed when --mem is missing for a CPU job (sources in the message)
CPU_MEM_HINTS = {
    "smoke": ("the geometric smoke demo measured 3.4 s wall and a peak RSS of 132 MB here "
              "(H3, 4 CPUs, 2026-09-23); 2G is ample"),
    "torus": ("T1 report measured a peak RSS of 1.33-1.35 GB per kind (4 CPUs); 4G is ample; "
              "the runner refuses cases above 10 GB of engine arrays (CASE limits)"),
    "pipeline": "take the memory from `python -m reflection_holo.pipeline dry-run --config ...`",
    "null-study": "take the memory from run_study.py --estimate (engine arrays) plus the structure",
}


class Refused(Exception):
    def __init__(self, msg, status=2):
        super().__init__(msg)
        self.status = status


def _load_yaml(path: Path):
    from reflection_holo.io.config import load_yaml_unique      # duplicate keys refused
    return load_yaml_unique(Path(path).read_bytes())


def load_clusters(path: Path = CLUSTERS_YAML) -> dict:
    d = _load_yaml(path)
    if d.get("schema") != "reflholo_alliance_clusters/1":
        raise Refused(f"{path}: unknown schema {d.get('schema')!r}")
    return d


def val(entry):
    """Value of a {value, locator} entry; every entry must carry a locator."""
    if not isinstance(entry, dict) or "value" not in entry or not entry.get("locator"):
        raise Refused(f"clusters.yaml entry without value/locator: {entry!r}")
    return entry["value"]


def loc(entry) -> str:
    return " ".join(str(entry["locator"]).split())


# ------------------------------------------------------------------------------------------------
# time limit (Running_jobs § Use sbatch to submit jobs: accepted formats)
# ------------------------------------------------------------------------------------------------
_TIME_FORMS = [
    (re.compile(r"^(\d+)$"), lambda m: int(m[1])),                                  # minutes
    (re.compile(r"^(\d+):(\d{1,2})$"), lambda m: int(m[1]) + int(m[2]) / 60),      # min:sec
    (re.compile(r"^(\d+):(\d{1,2}):(\d{1,2})$"),
     lambda m: 60 * int(m[1]) + int(m[2]) + int(m[3]) / 60),                       # h:m:s
    (re.compile(r"^(\d+)-(\d+)$"), lambda m: 1440 * int(m[1]) + 60 * int(m[2])),   # d-h
    (re.compile(r"^(\d+)-(\d+):(\d{1,2})$"),
     lambda m: 1440 * int(m[1]) + 60 * int(m[2]) + int(m[3])),                     # d-h:m
    (re.compile(r"^(\d+)-(\d+):(\d{1,2}):(\d{1,2})$"),
     lambda m: 1440 * int(m[1]) + 60 * int(m[2]) + int(m[3]) + int(m[4]) / 60),    # d-h:m:s
]


def time_minutes(t: str) -> float:
    for rx, f in _TIME_FORMS:
        m = rx.match(t.strip())
        if m:
            v = float(f(m))
            if v <= 0:
                raise Refused(f"time limit {t!r} is zero")
            return v
    raise Refused(f"time limit {t!r} is not a Slurm time (minutes, minutes:seconds, "
                  f"hours:minutes:seconds, days-hours, days-hours:minutes, "
                  f"days-hours:minutes:seconds; Running_jobs § Use sbatch to submit jobs)")


_MEM_RX = re.compile(r"^\d+[KMGT]?$")
_SAFE_RX = re.compile(r"^[A-Za-z0-9_./+:@%=~-]+$")          # no comma, no whitespace (--export)


def _safe(name: str, v: str) -> str:
    if not _SAFE_RX.match(v):
        raise Refused(f"{name} {v!r} contains a character the kit cannot pass through "
                      f"sbatch --export (comma, space or quote); use another path")
    return v


# ------------------------------------------------------------------------------------------------
# run descriptions read from the repository
# ------------------------------------------------------------------------------------------------
def pipeline_backend_threads(repo: Path, config: str, variant: str | None):
    from reflection_holo.io.config import ConfigError
    from reflection_holo.pipeline.config import load_pipeline_file
    try:
        cfg = load_pipeline_file(str(repo / config) if not os.path.isabs(config) else config,
                                 variant=variant or None)
    except ConfigError as exc:
        raise Refused(f"configuration {config} (variant {variant or 'none'}) refused by the "
                      f"pipeline gate: {exc}", status=3)
    eng = cfg.value("engine", "name")
    backend = cfg.value("engine", "multislice")["backend"] if eng == "multislice" else "none"
    return eng, backend, int(cfg.value("runtime", "threads"))


def study_points(study: Path):
    d = _load_yaml(study)
    rt = d.get("runtime") or {}
    for k in ("backend", "threads"):
        if k not in rt:
            raise Refused(f"{study}: runtime.{k} is required")
    names = [p.get("name") for p in d.get("points") or []]
    if not names or any(not n for n in names):
        raise Refused(f"{study}: every point needs a name (and there must be at least one)")
    if len(set(names)) != len(names):
        raise Refused(f"{study}: duplicate point names")
    return rt["backend"], int(rt["threads"]), names


# ------------------------------------------------------------------------------------------------
# plan
# ------------------------------------------------------------------------------------------------
def _warn(msgs, m):
    msgs.append(m)


def _under(path: Path, root: str | None) -> bool:
    if not root:
        return False
    try:
        path.resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def make_plan(a) -> dict:
    clusters = load_clusters(Path(a.clusters_yaml))
    common = clusters["common"]
    if a.cluster not in clusters["clusters"]:
        raise Refused(f"unknown cluster {a.cluster!r}; clusters.yaml has "
                      f"{sorted(clusters['clusters'])} (Cedar, Graham, Beluga and Niagara are "
                      f"retired: H1 §1)")
    prof = clusters["clusters"][a.cluster]
    if a.job not in JOBS:
        raise Refused(f"unknown job {a.job!r}; jobs: {sorted(JOBS)}")
    job = JOBS[a.job]
    warnings: list[str] = []
    repo = Path(a.repo).resolve()

    # --- environment record written by setup_alliance.sh -------------------------------------
    env_dir = Path(a.env_dir)
    envf = env_dir / "env.json"
    if not envf.is_file():
        raise Refused(f"{envf} not found: run scripts/hpc/alliance/setup_alliance.sh "
                      f"{a.cluster} on a login node of {a.cluster} first")
    env = json.loads(envf.read_text())
    if env.get("setup_complete") is not True:
        raise Refused(f"{envf}: setup did not complete; rerun setup_alliance.sh")
    if env.get("cluster") != a.cluster:
        raise Refused(f"the environment in {env_dir} was built for {env.get('cluster')!r}, not "
                      f"{a.cluster!r}: each cluster needs its own clone and setup")

    # --- account (required, no default) ------------------------------------------------------
    if not a.account:
        raise Refused("--account is required (no default): your RAP, e.g. def-<pi> or "
                      "rrg-<pi>-ab (CCDB 'Group Name'; Running_jobs § Accounts and projects)")
    prefixes = val(common["account_prefixes"])
    if not any(a.account.startswith(p) for p in prefixes) and not a.any_account_prefix:
        raise Refused(f"account {a.account!r} does not start with {prefixes} "
                      f"({loc(common['account_prefixes'])}); pass --any-account-prefix if "
                      f"this really is your RAP")
    _safe("account", a.account)

    # --- time limit (required, no default) --------------------------------------------------
    if not a.time:
        raise Refused("--time is required (no default; Running_jobs § Use sbatch to submit jobs)")
    minutes = time_minutes(a.time)
    tmax = val(prof["walltime_max_hours"])
    if minutes > 60 * tmax:
        raise Refused(f"time limit {a.time} exceeds the {a.cluster} maximum of {tmax} h "
                      f"({loc(prof['walltime_max_hours'])})")
    tmin = val(prof["walltime_min_minutes_test"])
    if tmin != NOT_FOUND and minutes < tmin:
        raise Refused(f"time limit {a.time} is below the {a.cluster} minimum of {tmin} min "
                      f"({loc(prof['walltime_min_minutes_test'])})")
    pmin = val(prof["walltime_min_minutes_production"])
    if pmin != NOT_FOUND and minutes < pmin:
        _warn(warnings, f"time limit {a.time} < {pmin} min: acceptable for a test job, but "
                        f"production jobs should last at least {pmin} min "
                        f"({loc(prof['walltime_min_minutes_production'])})")

    # --- what runs ----------------------------------------------------------------------------
    export = {}
    declared_threads = None
    needs_gpu = False
    config = variant = None
    array = None
    n_tasks = 1
    if a.config and a.job != "pipeline":
        raise Refused("--config is accepted by the `pipeline` job only (smoke and demo-gpu run "
                      "their fixed demo configurations; use `pipeline --config ...` otherwise)")
    if a.variant and job["kind"] != "pipeline":
        raise Refused("--variant applies to the pipeline jobs (smoke, demo-gpu, pipeline) only")
    for opt, kinds in (("study", ("null_study",)), ("only", ("null_study",)),
                       ("serial", ("null_study",)), ("array_throttle", ("null_study",)),
                       ("kinds", ("torus",))):
        if getattr(a, opt) and job["kind"] not in kinds:
            raise Refused(f"--{opt.replace('_', '-')} applies to the {kinds[0].replace('_', '-')} "
                          f"job only")

    if job["kind"] == "pipeline":
        config = a.config or job["config"]
        if not config:
            raise Refused("the `pipeline` job needs --config PATH (any pipeline configuration, "
                          "e.g. a production configuration from agent H2)")
        cpath = Path(config) if os.path.isabs(config) else repo / config
        if not cpath.is_file():
            raise Refused(f"configuration {config} not found (relative paths are relative to "
                          f"{repo})")
        variant = a.variant or ""
        eng, backend, declared_threads = pipeline_backend_threads(repo, config, variant)
        if job.get("backend") and backend != job["backend"]:
            raise Refused(f"{a.job} is the {job['backend']} demo; {config} variant "
                          f"{variant or 'none'} uses backend {backend}: use the `pipeline` job")
        needs_gpu = backend == "cupy"
        export.update(RH_CONFIG=_safe("config", config), RH_VARIANT=variant,
                      RH_PIPE_ENGINE=eng, RH_PIPE_BACKEND=backend)
    elif job["kind"] == "torus":
        kinds = (a.kinds or "trench,ridge").split(",")
        bad = [k for k in kinds if k not in TORUS_KINDS]
        if bad or not kinds:
            raise Refused(f"--kinds must be a comma list of {TORUS_KINDS}, got {a.kinds!r}")
        declared_threads = TORUS_THREADS
        export.update(RH_TORUS_KINDS=":".join(kinds))
    elif job["kind"] == "null_study":
        study = a.study or DEFAULT_STUDY
        spath = Path(study) if os.path.isabs(study) else repo / study
        if not spath.is_file():
            raise Refused(f"study file {study} not found")
        backend, declared_threads, names = study_points(spath)
        if backend not in ("cupy", "numpy"):
            raise Refused(f"{study}: runtime.backend must be cupy or numpy, got {backend!r}")
        needs_gpu = backend == "cupy"
        if a.only and a.serial:
            raise Refused("--only and --serial are exclusive")
        if a.array_throttle is not None and (a.only or a.serial):
            raise Refused("--array-throttle applies to the array mode only (not --only/--serial)")
        if a.only:
            if a.only not in names:
                raise Refused(f"--only {a.only!r} is not a point of {study}: {names}")
            mode = "only"
        elif a.serial:
            mode = "serial"
        else:
            mode = "array"
            array = f"0-{len(names) - 1}"
            n_tasks = len(names)
            if a.array_throttle:
                if a.array_throttle < 1:
                    raise Refused("--array-throttle must be >= 1")
                array += f"%{a.array_throttle}"
            _warn(warnings, "each array task is one study point; the wiki advises against arrays "
                            "of tasks much shorter than an hour (Job_arrays § A simple example): "
                            "--serial runs every point in one job")
        export.update(RH_STUDY=_safe("study", study), RH_STUDY_MODE=mode,
                      RH_STUDY_ONLY=a.only or "", RH_STUDY_N=str(len(names)))
    else:                                                              # gpu_check
        needs_gpu = True

    limit = val(prof["job_limit_queued_running"])
    if limit != NOT_FOUND and n_tasks > int(limit):
        raise Refused(f"{n_tasks} tasks exceed the {a.cluster} limit of {limit} queued+running "
                      f"jobs ({loc(prof['job_limit_queued_running'])})")

    # --- resources ------------------------------------------------------------------------------
    argv = ["sbatch", f"--account={a.account}", f"--time={a.time}"]
    gpu_rec = None
    gpu = prof["gpu"]
    if needs_gpu:
        inst_name = a.gpu_instance or "full"
        insts = gpu["instances"]
        if inst_name not in insts:
            raise Refused(f"GPU instance {inst_name!r} not offered on {a.cluster}: "
                          f"{sorted(insts)} ({loc(gpu['mig_availability'])})")
        inst = insts[inst_name]
        if a.need_gpu_mem_gb is not None and val(inst["gpu_mem_gb"]) < a.need_gpu_mem_gb:
            raise Refused(f"{a.cluster} {inst_name} has {val(inst['gpu_mem_gb'])} GB of GPU memory "
                          f"< the {a.need_gpu_mem_gb} GB you need ({loc(inst['gpu_mem_gb'])})")
        req = list(val(inst["request"]))
        argv += req
        if val(gpu["pass_cpus_per_task"]):
            rec = int(val(inst["cpus_recommended"]))
            cpus = a.cpus if a.cpus else rec
            if cpus > rec:
                _warn(warnings, f"--cpus {cpus} exceeds the recommended {rec} per {inst_name} "
                                f"({loc(inst['cpus_recommended'])}); it may be charged")
            argv.append(f"--cpus-per-task={cpus}")
        else:
            if a.cpus:
                raise Refused(f"--cpus is not accepted on {a.cluster}: "
                              f"{loc(gpu['pass_cpus_per_task'])}")
            cpus = int(val(gpu["cpus_fixed_per_gpu"]))
        if val(gpu["pass_mem"]):
            mem = a.mem or val(inst["mem_recommended"])
            argv.append(f"--mem={mem}")
        else:
            if a.mem:
                raise Refused(f"--mem is not accepted on {a.cluster}: {loc(gpu['pass_mem'])}")
            mem = None
        gpu_rec = dict(instance=inst_name, request=req, gpu_mem_gb=val(inst["gpu_mem_gb"]),
                       model=val(gpu["model"]), locator=loc(inst["request"]))
        export.update(RH_KIT_GPU=inst_name)
        if a.cluster == "trillium":
            hn = socket.gethostname().split(".")[0]
            want = val(prof["gpu_login_internal_hostname"])
            if hn != want:
                _warn(warnings, f"this host is {hn!r}; Trillium GPU jobs must be submitted from the "
                                f"GPU login node ({want}, "
                                f"{val(prof['gpu_login_host'])}; "
                                f"{loc(prof['submit_gpu_jobs_from_gpu_login'])})")
    else:
        if val(prof["cpu_jobs"]) != "allowed":
            raise Refused(f"{a.job} is a CPU job; the kit does not run CPU jobs on {a.cluster}: "
                          f"{loc(prof['cpu_jobs'])}")
        if a.gpu_instance or a.need_gpu_mem_gb is not None:
            raise Refused(f"{a.job} uses no GPU (backend of the run); --gpu-instance and "
                          f"--need-gpu-mem-gb do not apply")
        cpus = a.cpus if a.cpus else declared_threads
        if not a.mem:
            raise Refused(f"--mem is required for the CPU job {a.job} (no default: the wiki's "
                          f"256 MB per core default is not a statement about this run, "
                          f"Running_jobs § Memory). Hint: {CPU_MEM_HINTS.get(a.job, '')}")
        mem = a.mem
        argv += [f"--cpus-per-task={cpus}", f"--mem={mem}"]
        export.update(RH_KIT_GPU="none")
    if mem is not None and not _MEM_RX.match(str(mem)):
        raise Refused(f"--mem {mem!r} is not a Slurm memory size (e.g. 16G, 128000M)")
    if declared_threads is not None and cpus < declared_threads:
        raise Refused(f"cpus-per-task {cpus} < the {declared_threads} threads the run declares "
                      f"(runtime.threads of the configuration or study, or the torus runner's 4); "
                      f"pass --cpus {declared_threads} or more")
    threads = declared_threads if declared_threads is not None else cpus

    # --- GPU gate: the GPU path has never run; gpu-check must pass first -----------------------
    run_root = Path(a.run_root)
    gate = None
    if needs_gpu and a.job != "gpu-check":
        passes = sorted((run_root / "gpu_check").glob(f"PASS_{a.cluster}_{env['env_id']}_*.json"))
        if passes:
            gate = dict(status="PASS", record=str(passes[-1]))
        elif a.skip_gpu_check_gate:
            gate = dict(status="SKIPPED by --skip-gpu-check-gate")
            _warn(warnings, "no gpu-check PASS record for this environment: the GPU path is "
                            "UNVERIFIED on this cluster (--skip-gpu-check-gate)")
        else:
            raise Refused(f"no gpu-check PASS record for this environment "
                          f"({run_root}/gpu_check/PASS_{a.cluster}_{env['env_id']}_*.json): run "
                          f"`submit.sh {a.cluster} gpu-check ...` first and check its log; the cupy "
                          f"path has never been executed. Override: --skip-gpu-check-gate")

    # --- where things go ------------------------------------------------------------------------
    if a.cluster == "trillium":
        for var in ("HOME", "PROJECT"):
            if _under(run_root, os.environ.get(var)):
                raise Refused(f"run root {run_root} is under ${var}, read-only on Trillium compute "
                              f"nodes ({loc(prof['home_writable_on_compute'])}); use $SCRATCH")
    logdir = run_root / "logs"
    stem = f"{a.job}_%A_%a" if array else f"{a.job}_%j"
    argv += [f"--job-name=reflholo-{a.job}", f"--output={logdir}/{stem}.log",
             f"--chdir={run_root}"]
    if array:
        argv.append(f"--array={array}")
    export.update(RH_KIT_JOB=a.job, RH_KIT_CLUSTER=a.cluster, RH_REPO=_safe("repo", str(repo)),
                  RH_ENV_DIR=_safe("env dir", str(env_dir.resolve())),
                  RH_RUN_ROOT=_safe("run root", str(run_root)), RH_KIT_THREADS=str(threads),
                  RH_KIT_CPUS=str(cpus), RH_TIME_LIMIT=a.time, RH_ACCOUNT=a.account,
                  RH_ENV_ID=env["env_id"], RH_SUBMIT_COMMIT=a.commit or "",
                  RH_SUBMISSION_RECORD=_safe("record", a.record or ""))
    for k, v in export.items():
        _safe(k, v) if v else None
    argv.append("--export=ALL," + ",".join(f"{k}={v}" for k, v in export.items()))
    argv.append(str(JOB_SCRIPT))
    return dict(schema="reflholo_alliance_submission/1",
                created_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                cluster=a.cluster, job=a.job, argv=argv, warnings=warnings, gpu=gpu_rec,
                cpus_per_task=cpus, threads=threads, mem=mem, time=a.time,
                time_minutes=minutes, array=array, gate=gate, config=config, variant=variant,
                run_root=str(run_root), log_dir=str(logdir), env=env, repo=str(repo),
                commit=a.commit, profile_locators=dict(
                    walltime_max=loc(prof["walltime_max_hours"]),
                    job_limit=loc(prof["job_limit_queued_running"]),
                    gpu=gpu_rec["locator"] if gpu_rec else None))


def cmd_plan(a) -> int:
    try:
        plan = make_plan(a)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return exc.status
    for w in plan["warnings"]:
        print(f"WARNING: {w}", file=sys.stderr)
    with open(a.argv_out, "wb") as fh:
        fh.write(b"\0".join(s.encode() for s in plan["argv"]) + b"\0")
    if a.plan_out:
        Path(a.plan_out).write_text(json.dumps(plan, indent=1))
    return 0


def cmd_study_point(a) -> int:
    try:
        _, _, names = study_points(Path(a.study))
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    if not 0 <= a.index < len(names):
        print(f"REFUSED: index {a.index} outside 0..{len(names) - 1} of {a.study}", file=sys.stderr)
        return 2
    print(names[a.index])
    return 0


def _module_set(path: Path) -> list[str]:
    out = []
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if not s or s.endswith(":") or s.startswith("Currently Loaded"):
            continue
        out.append(s)
    return sorted(set(out))


def cmd_modules_diff(a) -> int:
    rec, cur = _module_set(Path(a.recorded)), _module_set(Path(a.current))
    if rec == cur:
        print(f"modules: identical to the setup record ({len(rec)} modules)")
        return 0
    print("REFUSED: loaded modules differ from the setup record", file=sys.stderr)
    print(f"  only in the record : {sorted(set(rec) - set(cur))}", file=sys.stderr)
    print(f"  only in this job   : {sorted(set(cur) - set(rec))}", file=sys.stderr)
    return 2


def cmd_job_record(a) -> int:
    keys = ("SLURM_JOB_ID", "SLURM_ARRAY_JOB_ID", "SLURM_ARRAY_TASK_ID", "SLURM_CLUSTER_NAME",
            "SLURM_JOB_NODELIST", "SLURM_CPUS_PER_TASK", "SLURM_CPUS_ON_NODE", "SLURM_MEM_PER_NODE",
            "SLURM_JOB_ACCOUNT", "SLURM_JOB_PARTITION", "SLURM_GPUS", "SLURM_GPUS_ON_NODE",
            "CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS", "CUPY_CACHE_DIR", "NUMBA_CACHE_DIR", "MPLCONFIGDIR",
            "PYTHONNOUSERSITE", "VIRTUAL_ENV")
    rec = dict(schema="reflholo_alliance_job/1",
               written_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
               host=socket.gethostname(), python=sys.version, executable=sys.executable,
               slurm={k: os.environ.get(k) for k in keys},
               kit={k: v for k, v in sorted(os.environ.items()) if k.startswith("RH_")})
    for kv in a.extra or []:
        k, _, v = kv.partition("=")
        rec.setdefault("extra", {})[k] = v
    Path(a.out).write_text(json.dumps(rec, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--cluster", required=True)
    p.add_argument("--job", required=True)
    p.add_argument("--account", default=None)
    p.add_argument("--time", default=None)
    p.add_argument("--repo", required=True)
    p.add_argument("--env-dir", required=True)
    p.add_argument("--run-root", required=True)
    p.add_argument("--argv-out", required=True)
    p.add_argument("--plan-out", default=None)
    p.add_argument("--clusters-yaml", default=str(CLUSTERS_YAML))
    p.add_argument("--commit", default=None)
    p.add_argument("--record", default=None)
    p.add_argument("--config", default=None)
    p.add_argument("--variant", default=None)
    p.add_argument("--study", default=None)
    p.add_argument("--only", default=None)
    p.add_argument("--serial", action="store_true")
    p.add_argument("--array-throttle", type=int, default=None)
    p.add_argument("--kinds", default=None)
    p.add_argument("--gpu-instance", default=None)
    p.add_argument("--need-gpu-mem-gb", type=float, default=None)
    p.add_argument("--cpus", type=int, default=None)
    p.add_argument("--mem", default=None)
    p.add_argument("--any-account-prefix", action="store_true")
    p.add_argument("--skip-gpu-check-gate", action="store_true")
    s = sub.add_parser("study-point")
    s.add_argument("--study", required=True)
    s.add_argument("--index", type=int, required=True)
    m = sub.add_parser("modules-diff")
    m.add_argument("--recorded", required=True)
    m.add_argument("--current", required=True)
    j = sub.add_parser("job-record")
    j.add_argument("--out", required=True)
    j.add_argument("--extra", action="append")
    a = ap.parse_args(argv)
    return dict(plan=cmd_plan, **{"study-point": cmd_study_point,
                                  "modules-diff": cmd_modules_diff,
                                  "job-record": cmd_job_record})[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
