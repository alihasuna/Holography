#!/usr/bin/env python
"""Helper of the Alliance kit (scripts/hpc/alliance/): reads clusters.yaml and the environment record
written by setup_alliance.sh, validates a submission and builds the sbatch command. Called by
submit.sh and job.sbatch; not meant to be run by hand (but `plan` is harmless: it only prints).

    kit.py plan --cluster C --job J --account A --time T --repo R --env-dir E --run-root D
                --record F --argv-out F [...]
    kit.py study-point --study S --index I          # name of point I of a study file
    kit.py modules-diff --recorded F --current G    # compare two `module -t list` outputs
    kit.py job-record --out F [--extra KEY=VALUE ...]
    kit.py copy-study --src S --dst D --sha256 H    # submission: the study copy the job reads (F6)
    kit.py verify-study --study S --sha256 H --copy-to D   # job start: hash check, copy (F6)
    kit.py env-check --env-dir E --env-id I         # job start: still the submitted environment (F9)
    kit.py gate-check --run-root D --cluster C --env-id I --repo R   # job start: gpu-check PASS (F9)
    kit.py engine-hash --repo R                     # SHA-256 of the engine code the PASS is tied to

Rules (docs/05, docs/agent_reports/H1): no default replaces a required input (account and time
limit are required; memory is required for CPU jobs); every cluster value comes from clusters.yaml
with its wiki locator; a value the wiki does not state (NOT_FOUND) is never invented.
Exit status: 0 ok; 2 refused (usage, a missing or invalid input, a policy limit); 3 configuration
refused by the pipeline gate.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
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
# gpu-sanity (H2 report, "Recommended run order" step 0; H2 is under review): the first point of the
# null study on the GPU against its stored CPU value; the point name is fixed by that step
SANITY_POINT = "tfix_bragg_abs0_L0"
# Job definitions of this repository. "config" is part of the job's definition (which run it is),
# not a stand-in for a PROJECT_INPUT; the `pipeline` and `dry-run` jobs take any configuration.
JOBS = {
    "gpu-check": dict(kind="gpu_check"),
    "gpu-sanity": dict(kind="gpu_sanity"),
    "smoke": dict(kind="pipeline", config="configs/demo_smoke_si001.yaml"),
    "demo-gpu": dict(kind="pipeline", config="configs/demo_hpc_si001.yaml", backend="cupy"),
    "pipeline": dict(kind="pipeline", config=None),
    "dry-run": dict(kind="dry_run"),
    "torus": dict(kind="torus"),
    "null-study": dict(kind="null_study"),
}
TORUS_KINDS = ("trench", "ridge", "flat")
# scripts/torus/run_torus_multislice.py fixes CASE["threads"] = 4 and backend numpy (T1 runner)
TORUS_THREADS = 4
# F11: the torus runner refuses a kind whose calibrated CPU estimate exceeds its limit (600 s by
# default, set for the build machine). The kit passes a limit derived from the requested walltime:
# this fraction of the walltime, shared by the kinds that run one after the other in the job.
TORUS_WALLTIME_FRACTION = 0.8

# Hints printed when --mem is missing for a CPU job. They say what each number counts and where it
# was measured; none of them is used as a value (--mem stays required).
CPU_MEM_HINTS = {
    "smoke": ("the geometric smoke demo measured 3.4 s wall and a peak RSS of 132 MB here "
              "(H3, 4 CPUs, 2026-09-23); 2G is ample"),
    "torus": ("T1 report measured a peak RSS of 1.33-1.35 GB per kind (4 CPUs); 4G is ample; "
              "the runner refuses cases above 10 GB of engine arrays (CASE limits)"),
    "pipeline": ("the 'memory per realisation' printed by `pipeline dry-run` counts only the engine's "
                 "arrays of one realisation (wave, propagator, potential slices); it is NOT the memory "
                 "of the job. The host also holds the structure and the reflection cell (the dry run of "
                 "configs/demo_hpc_si001.yaml, 1.44 M atoms, printed ~127 MiB per realisation and "
                 "peaked at 3.6 GB RSS: H4 audit, command 18) and, while realising, about 192-240 B "
                 "per atom (H2 §8 and §12, from reading the code, not measured; H2 is under review). "
                 "Measure the peak with the `dry-run` job (it prints the peak RSS of the structure "
                 "build) and pass --mem explicitly"),
    "dry-run": ("the dry run builds the whole structure and reflection cell: peak RSS 3.6 GB for "
                "configs/demo_hpc_si001.yaml (1.44 M atoms; H4 audit, command 18); larger cells "
                "need more (not measured here)"),
    "null-study": ("run_study.py --estimate prints the engine's arrays only (at most 340 MB for "
                   "study.yaml); the host also holds the structures of each point (up to 2.97 M atoms "
                   "in study.yaml; host memory not measured here)"),
}


# GPU memory need from a dry run (E1 wave 2a; H7 sections 1 and 4): the engine's cupy device peak
# (engine.memory_model: UNVERIFIED on a GPU and a LOWER BOUND, cuFFT/cuBLAS workspaces and the cupy
# memory pool are not modelled) times (1 + a margin the user states with --gpu-mem-margin; no
# default), and the host memory of that GPU run: the model's cupy host peak (cell 32 B/atom +
# realisation 112 B/atom + pixel arrays) plus the builder structure the pipeline keeps while it
# realises, 48 B/atom (192 B/atom in total, H7 section 4; H5 measured 193).
DRY_RUN_REPORT_SCHEMA = "reflholo_pipeline_dry_run_report/1"
STRUCTURE_B_PER_ATOM = 48
_SLURM_MEM_UNIT_B = {"": 2**20, "K": 2**10, "M": 2**20, "G": 2**30, "T": 2**40}  # Slurm: MB default


def slurm_mem_bytes(mem: str) -> int:
    m = re.match(r"^(\d+)([KMGT]?)$", str(mem))
    if not m:
        raise Refused(f"--mem {mem!r} is not a Slurm memory size (e.g. 16G, 128000M)")
    return int(m[1]) * _SLURM_MEM_UNIT_B[m[2]]


class Refused(Exception):
    def __init__(self, msg, status=2):
        super().__init__(msg)
        self.status = status


def _load_yaml(path: Path):
    from reflection_holo.io.config import load_yaml_unique      # duplicate keys refused
    return load_yaml_unique(Path(path).read_bytes())


def _load_yaml_bytes(data: bytes):
    from reflection_holo.io.config import load_yaml_unique
    return load_yaml_unique(data)


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
# time limit (Running_jobs § Use sbatch to submit jobs: "The acceptable time formats include
# "minutes", "minutes:seconds", "hours:minutes:seconds", "days-hours", "days-hours:minutes" and
# "days-hours:minutes:seconds"", Running_jobs.wiki:47)
# ------------------------------------------------------------------------------------------------
_TIME_FORMS = [
    ("minutes", re.compile(r"^(\d+)$"), lambda m: int(m[1])),
    ("minutes:seconds", re.compile(r"^(\d+):(\d{1,2})$"), lambda m: int(m[1]) + int(m[2]) / 60),
    ("hours:minutes:seconds", re.compile(r"^(\d+):(\d{1,2}):(\d{1,2})$"),
     lambda m: 60 * int(m[1]) + int(m[2]) + int(m[3]) / 60),
    ("days-hours", re.compile(r"^(\d+)-(\d+)$"), lambda m: 1440 * int(m[1]) + 60 * int(m[2])),
    ("days-hours:minutes", re.compile(r"^(\d+)-(\d+):(\d{1,2})$"),
     lambda m: 1440 * int(m[1]) + 60 * int(m[2]) + int(m[3])),
    ("days-hours:minutes:seconds", re.compile(r"^(\d+)-(\d+):(\d{1,2}):(\d{1,2})$"),
     lambda m: 1440 * int(m[1]) + 60 * int(m[2]) + int(m[3]) + int(m[4]) / 60),
]
# F7: the two forms without hours are refused by the kit: "01:00" is ONE MINUTE to Slurm
# (minutes:seconds) and "2" is two minutes; both are easily meant as hours. The others name the
# hours explicitly (a day prefix or three fields).
AMBIGUOUS_TIME_FORMS = ("minutes", "minutes:seconds")


def parse_time(t: str):
    """(form, minutes) of a Slurm time limit; every form of the wiki is recognised."""
    s = (t or "").strip()
    for name, rx, f in _TIME_FORMS:
        m = rx.match(s)
        if m:
            v = float(f(m))
            if v <= 0:
                raise Refused(f"time limit {t!r} is zero")
            return name, v
    raise Refused(f"time limit {t!r} is not a Slurm time (minutes, minutes:seconds, "
                  f"hours:minutes:seconds, days-hours, days-hours:minutes, "
                  f"days-hours:minutes:seconds; Running_jobs § Use sbatch to submit jobs)")


def time_minutes(t: str) -> float:
    return parse_time(t)[1]


def hms(minutes: float) -> str:
    s = int(round(minutes * 60))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def checked_time(t: str):
    """The kit's time policy: a Slurm form that names the hours (F7). Returns (form, minutes)."""
    form, minutes = parse_time(t)
    if form in AMBIGUOUS_TIME_FORMS:
        raise Refused(f"--time {t!r} is ambiguous and refused: Slurm reads it as {form} "
                      f"(= {minutes:g} min, i.e. {hms(minutes)}), which is easily meant as hours. "
                      f"Write HH:MM:SS or D-HH:MM:SS, e.g. {hms(minutes)} for {minutes:g} min or "
                      f"01:00:00 for one hour")
    n_sub_hour = {"hours:minutes:seconds": 2, "days-hours:minutes": 1,
                  "days-hours:minutes:seconds": 2}.get(form, 0)
    fields = re.split(r"[-:]", t.strip())
    if n_sub_hour and any(int(x) >= 60 for x in fields[-n_sub_hour:]):
        raise Refused(f"--time {t!r}: minutes and seconds must be below 60 ({form})")
    return form, minutes


_MEM_RX = re.compile(r"^\d+[KMGT]?$")
_SAFE_RX = re.compile(r"^[A-Za-z0-9_./+:@%=~-]+$")          # no comma, no whitespace (--export)


def _safe(name: str, v: str) -> str:
    if not _SAFE_RX.match(v):
        raise Refused(f"{name} {v!r} contains a character the kit cannot pass through "
                      f"sbatch --export (comma, space or quote); use another path")
    return v


# ------------------------------------------------------------------------------------------------
# engine code identity (F9): the gpu-check PASS is valid only for the engine code it checked
# ------------------------------------------------------------------------------------------------
ENGINE_CODE_DIRS = ("reflection_holo/forward/multislice",)
ENGINE_BACKEND_FILE = "reflection_holo/forward/multislice/backend.py"
PASS_SCHEMA = "reflholo_gpu_check_pass/2"


def engine_code_sha256(repo) -> dict:
    """SHA-256 over every *.py file (relative path, size, content; sorted) of the multislice engine
    package, which contains the array backend (backend.py). A PASS carries this hash; a PASS of
    other engine code does not unlock GPU jobs."""
    repo = Path(repo).resolve()
    files = []
    for d in ENGINE_CODE_DIRS:
        base = repo / d
        if not base.is_dir():
            raise Refused(f"engine code directory {base} not found")
        files += sorted(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    rels = [p.relative_to(repo).as_posix() for p in files]
    if ENGINE_BACKEND_FILE not in rels:
        raise Refused(f"{ENGINE_BACKEND_FILE} not found under {repo}")
    h = hashlib.sha256()
    for rel, p in zip(rels, files):
        data = p.read_bytes()
        h.update(f"{rel}\0{len(data)}\0".encode())
        h.update(data)
    return dict(sha256=h.hexdigest(), files=rels, dirs=list(ENGINE_CODE_DIRS))


def pass_problems(rec, *, cluster, env_id, engine_sha) -> list[str]:
    if not isinstance(rec, dict):
        return ["not a JSON object"]
    why = []
    if rec.get("schema") != PASS_SCHEMA:
        why.append(f"schema {rec.get('schema')!r} is not {PASS_SCHEMA} (not written by this "
                   f"gpu_check.py)")
    if rec.get("passed") is not True:
        why.append("not a pass")
    if rec.get("cluster") != cluster:
        why.append(f"cluster {rec.get('cluster')!r} != {cluster!r}")
    if rec.get("env_id") != env_id:
        why.append(f"environment {rec.get('env_id')!r} != {env_id!r}")
    if rec.get("engine_code_sha256") != engine_sha:
        why.append(f"engine code {str(rec.get('engine_code_sha256'))[:12]} != current "
                   f"{engine_sha[:12]}")
    return why


def find_gate_pass(run_root, cluster, env_id, engine_sha):
    """(valid, rejected): PASS files under <run root>/gpu_check whose CONTENT matches the cluster,
    the environment id and the engine code hash (the file name is not trusted)."""
    ok, rejected = [], []
    for p in sorted((Path(run_root) / "gpu_check").glob("PASS_*.json")):
        try:
            rec = json.loads(p.read_text())
        except (OSError, ValueError) as exc:
            rejected.append((p, [f"unreadable: {exc}"]))
            continue
        why = pass_problems(rec, cluster=cluster, env_id=env_id, engine_sha=engine_sha)
        (rejected if why else ok).append((p, why))
    return ok, rejected


def _gate_refusal(run_root, cluster, env_id, engine_sha, rejected) -> str:
    msg = (f"no gpu-check PASS record for cluster {cluster}, environment {env_id} and engine code "
           f"{engine_sha[:12]} under {run_root}/gpu_check")
    if rejected:
        msg += "; PASS files that do not qualify: " + "; ".join(
            f"{p.name}: {', '.join(w)}" for p, w in rejected[-5:])
    return msg


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


def study_from_bytes(data: bytes, label):
    d = _load_yaml_bytes(data)
    rt = d.get("runtime") or {}
    for k in ("backend", "threads"):
        if k not in rt:
            raise Refused(f"{label}: runtime.{k} is required")
    names = [p.get("name") for p in d.get("points") or []]
    if not names or any(not n for n in names):
        raise Refused(f"{label}: every point needs a name (and there must be at least one)")
    if len(set(names)) != len(names):
        raise Refused(f"{label}: duplicate point names")
    return rt["backend"], int(rt["threads"]), names


def study_points(study: Path):
    return study_from_bytes(Path(study).read_bytes(), study)


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


def gpu_need_from_dry_run(path: str, *, margin, config_path: Path, variant: str):
    """(record, NOTE lines): the GPU memory need derived from a `pipeline dry-run --report-json`
    file (or a directory holding dry_run_report.json, e.g. the dry-run job's dry_run/ directory)
    of THIS configuration and variant (SHA-256 checked). Every step is printed."""
    p = Path(path)
    if p.is_dir():
        cands = [p / "dry_run_report.json", p / "dry_run" / "dry_run_report.json"]
        found = [c for c in cands if c.is_file()]
        if not found:
            raise Refused(f"--gpu-mem-from-dry-run {path}: no dry_run_report.json in it (the "
                          f"`dry-run` job writes <job dir>/dry_run/dry_run_report.json)")
        p = found[0]
    if not p.is_file():
        raise Refused(f"--gpu-mem-from-dry-run {path}: file not found")
    if margin is None:
        raise Refused("--gpu-mem-margin is required with --gpu-mem-from-dry-run (no default): the "
                      "fraction added to the engine's device peak for the cuFFT/cuBLAS workspaces "
                      "and the cupy memory pool, which the model does not contain (e.g. 0.5 = "
                      "+50 %; state it, it is recorded)")
    if not (margin == margin and 0.0 <= margin < 100.0):
        raise Refused(f"--gpu-mem-margin {margin!r} must be a fraction >= 0 (e.g. 0.5 = +50 %)")
    raw = p.read_bytes()
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise Refused(f"{p}: not a JSON dry-run report ({exc})") from None
    if data.get("schema") != DRY_RUN_REPORT_SCHEMA:
        raise Refused(f"{p}: schema {data.get('schema')!r}, expected {DRY_RUN_REPORT_SCHEMA!r} "
                      f"(written by `python -m reflection_holo.pipeline dry-run --report-json`)")
    want = hashlib.sha256(config_path.read_bytes()).hexdigest()
    if data.get("config_sha256") != want:
        raise Refused(f"{p} was made for configuration {data.get('config_path')} (SHA-256 "
                      f"{str(data.get('config_sha256'))[:12]}...), not for {config_path} "
                      f"({want[:12]}...): run the `dry-run` job of this configuration first")
    if (data.get("variant") or "") != (variant or ""):
        raise Refused(f"{p} was made for variant {data.get('variant')!r}, not {variant or None!r}")
    rep = data.get("report") or {}
    ms = rep.get("multislice")
    if not isinstance(ms, dict) or "memory_bytes" not in ms:
        raise Refused(f"{p}: the dry run has no multislice estimate (engine {rep.get('engine')!r}, "
                      f"status {rep.get('multislice_status')!r}): no GPU memory to derive")
    backend = (rep.get("backend") or {}).get("name")
    if backend != "cupy":
        raise Refused(f"{p}: the configuration's multislice backend is {backend!r}; the device "
                      f"peak applies to a cupy run only")
    mb = ms["memory_bytes"]
    dev = int(mb["device_peak_cupy"])
    host = int(mb["host_peak_cupy"])
    n_atoms = int(ms["n_atoms"])
    need_B = dev * (1.0 + float(margin))
    host_B = host + STRUCTURE_B_PER_ATOM * n_atoms
    rec = dict(source=str(p), source_sha256=hashlib.sha256(raw).hexdigest(),
               config_sha256=want, device_peak_cupy_B=dev, margin=float(margin),
               need_gb=need_B / 1e9, host_peak_cupy_B=host, n_atoms=n_atoms,
               structure_B_per_atom=STRUCTURE_B_PER_ATOM, host_need_B=host_B,
               label="engine.memory_model (UNVERIFIED on a GPU; device peak is a lower bound) + "
                     "stated margin; host + 48 B/atom builder structure (H7)")
    lines = [
        f"GPU memory from the dry run {p} (SHA-256 {rec['source_sha256'][:12]}..., configuration "
        f"SHA-256 {want[:12]}... matches): grid {ms.get('grid')}, {n_atoms} atoms, precision "
        f"{ms.get('precision')}",
        f"  device peak of the cupy backend (engine.memory_model; UNVERIFIED on a GPU, a LOWER "
        f"BOUND: cuFFT/cuBLAS workspaces and the cupy pool are not modelled) = {dev} B = "
        f"{dev / 1e9:.3f} GB",
        f"  x (1 + margin {float(margin):g}, stated with --gpu-mem-margin) = {need_B / 1e9:.3f} GB "
        f"(1 GB = 1e9 B) = the GPU memory needed",
        f"  host memory of that GPU run: cupy host peak {host} B (cell 32 B/atom + realisation "
        f"112 B/atom + pixel arrays) + builder structure {STRUCTURE_B_PER_ATOM} B/atom x {n_atoms} "
        f"= {host_B / 2**30:.2f} GiB (192 B/atom in total, H7 section 4)"]
    return rec, lines


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
    notes: list[str] = []
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

    # --- time limit (required, no default; a form that names the hours: F7) ------------------
    if not a.time:
        raise Refused("--time is required (no default; Running_jobs § Use sbatch to submit jobs)")
    _form, minutes = checked_time(a.time)
    notes.append(f"time limit {a.time} = {hms(minutes)} ({minutes:g} min)")
    tmax = val(prof["walltime_max_hours"])
    if minutes > 60 * tmax:
        raise Refused(f"time limit {a.time} exceeds the {a.cluster} maximum of {tmax} h "
                      f"({loc(prof['walltime_max_hours'])})")
    tmin = val(prof["walltime_min_minutes_test"])
    if tmin != NOT_FOUND and minutes < tmin:
        raise Refused(f"time limit {a.time} is below the {a.cluster} minimum of {tmin} min "
                      f"({loc(prof['walltime_min_minutes_test'])})")
    if tmin == NOT_FOUND and minutes < 5:
        _warn(warnings, f"time limit {a.time} is {minutes:g} min; {a.cluster} states no minimum "
                        f"for test jobs (NOT_FOUND), the other clusters ask for at least 5 min")
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
    study_rec = None
    if a.config and job["kind"] not in ("pipeline", "dry_run") or (
            a.config and a.job in ("smoke", "demo-gpu")):
        raise Refused("--config is accepted by the `pipeline` and `dry-run` jobs only (smoke and "
                      "demo-gpu run their fixed demo configurations; use `pipeline --config ...` "
                      "otherwise)")
    if a.variant and job["kind"] not in ("pipeline", "dry_run"):
        raise Refused("--variant applies to the pipeline jobs (smoke, demo-gpu, pipeline) and "
                      "dry-run only")
    for opt, kinds in (("study", ("null_study",)), ("only", ("null_study",)),
                       ("serial", ("null_study",)), ("array", ("null_study",)),
                       ("array_throttle", ("null_study",)), ("kinds", ("torus",))):
        v = getattr(a, opt)
        if (v is not None and v is not False) and job["kind"] not in kinds:
            raise Refused(f"--{opt.replace('_', '-')} applies to the {kinds[0].replace('_', '-')} "
                          f"job only")

    def study_setup(study, fixed_backend=None):
        spath = Path(study) if os.path.isabs(study) else repo / study
        if not spath.is_file():
            raise Refused(f"study file {study} not found")
        data = spath.read_bytes()                        # read once: parsed, hashed and copied
        sha = hashlib.sha256(data).hexdigest()
        backend, threads, names = study_from_bytes(data, study)
        if backend not in ("cupy", "numpy"):
            raise Refused(f"{study}: runtime.backend must be cupy or numpy, got {backend!r}")
        if fixed_backend and backend != fixed_backend:
            raise Refused(f"{a.job} needs a study with runtime.backend {fixed_backend}; "
                          f"{study} has {backend}")
        if not a.record or not a.record.endswith(".json"):
            raise Refused("internal: plan needs --record <submission record>.json (submit.sh "
                          "passes it)")
        copy = a.record[:-len(".json")] + ".study.yaml"
        rec = dict(source=str(spath), copy=copy, sha256=sha)
        # F6: every task reads this copy (written by submit.sh after planning, hash-checked by the
        # job), never the repository file, which a `git pull` may change while tasks wait
        export.update(RH_STUDY=_safe("study copy", copy), RH_STUDY_SHA256=sha,
                      RH_STUDY_SOURCE=_safe("study", str(spath)))
        return backend, threads, names, rec

    config_path = None
    if job["kind"] in ("pipeline", "dry_run"):
        config = a.config or job.get("config")
        if not config:
            raise Refused(f"the `{a.job}` job needs --config PATH (any pipeline configuration, "
                          f"e.g. a production configuration from agent H2)")
        cpath = Path(config) if os.path.isabs(config) else repo / config
        if not cpath.is_file():
            raise Refused(f"configuration {config} not found (relative paths are relative to "
                          f"{repo})")
        config_path = cpath
        variant = a.variant or ""
        eng, backend, declared_threads = pipeline_backend_threads(repo, config, variant)
        if job.get("backend") and backend != job["backend"]:
            raise Refused(f"{a.job} is the {job['backend']} demo; {config} variant "
                          f"{variant or 'none'} uses backend {backend}: use the `pipeline` job")
        if job["kind"] == "pipeline":
            needs_gpu = backend == "cupy"
        else:
            # a sizing job on a CPU node: the dry run builds the structure and the cell and prints
            # the estimates; for a cupy configuration it then exits 4 (no GPU on a CPU node)
            needs_gpu = False
            if backend == "cupy":
                notes.append("dry-run of a cupy configuration on a CPU node: the estimates and the "
                             "peak RSS are printed, then the dry run exits 4 (no GPU here); that "
                             "status is expected")
        export.update(RH_CONFIG=_safe("config", config), RH_VARIANT=variant,
                      RH_PIPE_ENGINE=eng, RH_PIPE_BACKEND=backend)
    elif job["kind"] == "torus":
        kinds = (a.kinds or "trench,ridge").split(",")
        bad = [k for k in kinds if k not in TORUS_KINDS]
        if bad or not kinds:
            raise Refused(f"--kinds must be a comma list of {TORUS_KINDS}, got {a.kinds!r}")
        declared_threads = TORUS_THREADS
        # F11: the runner's CPU guard, derived from the walltime (recorded by the runner)
        max_cpu = int(TORUS_WALLTIME_FRACTION * minutes * 60 / len(kinds))
        notes.append(f"torus: the runner accepts a calibrated CPU estimate up to {max_cpu} s per "
                     f"kind ({TORUS_WALLTIME_FRACTION:g} x {hms(minutes)} / {len(kinds)} kinds; "
                     f"its own default for local use is 600 s)")
        export.update(RH_TORUS_KINDS=":".join(kinds), RH_TORUS_MAX_CPU_S=str(max_cpu))
    elif job["kind"] == "null_study":
        study = a.study or DEFAULT_STUDY
        backend, declared_threads, names, study_rec = study_setup(study)
        needs_gpu = backend == "cupy"
        if a.array_throttle is not None:
            a.array = True                               # an explicit request of the array mode
        if sum(bool(x) for x in (a.only, a.serial, a.array)) > 1:
            if a.array_throttle is not None and (a.only or a.serial):
                raise Refused("--array-throttle applies to the array mode only (not --only/--serial)")
            raise Refused("--only, --serial and --array are exclusive")
        if a.only:
            if a.only not in names:
                raise Refused(f"--only {a.only!r} is not a point of {study}: {names}")
            mode = "only"
        elif a.array:
            mode = "array"
            array = f"0-{len(names) - 1}"
            n_tasks = len(names)
            if a.array_throttle is not None:
                if a.array_throttle < 1:
                    raise Refused("--array-throttle must be >= 1")
                array += f"%{a.array_throttle}"
            _warn(warnings, "array mode: each array task is one study point. The wiki: \"You should "
                            "not use a job array to submit tasks with very short run times, e.g. "
                            "much less than an hour. Tasks with run times of only a few minutes "
                            "should be grouped into longer jobs\" (Job_arrays § A simple example); "
                            "the default --serial runs every point in one job")
        else:
            mode = "serial"                              # F4: the default (Job_arrays § A simple example)
        export.update(RH_STUDY_MODE=mode, RH_STUDY_ONLY=a.only or "", RH_STUDY_N=str(len(names)))
    elif job["kind"] == "gpu_sanity":
        backend, declared_threads, names, study_rec = study_setup(DEFAULT_STUDY,
                                                                  fixed_backend="cupy")
        if SANITY_POINT not in names:
            raise Refused(f"{DEFAULT_STUDY} has no point {SANITY_POINT}")
        needs_gpu = True
        export.update(RH_SANITY_POINT=SANITY_POINT)
    else:                                                              # gpu_check
        needs_gpu = True

    # --- GPU memory need derived from a dry run (option; --need-gpu-mem-gb overrides it) -------
    gpu_need = None
    if a.gpu_mem_margin is not None and a.gpu_mem_from_dry_run is None:
        raise Refused("--gpu-mem-margin applies with --gpu-mem-from-dry-run only")
    if a.gpu_mem_from_dry_run is not None:
        if job["kind"] != "pipeline" or not needs_gpu:
            raise Refused("--gpu-mem-from-dry-run applies to a pipeline job of a cupy "
                          "configuration (pipeline, demo-gpu) only")
        gpu_need, lines = gpu_need_from_dry_run(a.gpu_mem_from_dry_run, margin=a.gpu_mem_margin,
                                                config_path=config_path, variant=variant)
        notes.extend(lines)

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
        if inst_name == "unpinned" and "unpinned" in gpu:
            # F5: the Trillium site pages request a GPU without a model; offered only on request
            inst = dict(insts["full"], request=gpu["unpinned"]["request"])
            _warn(warnings, f"{val(gpu['unpinned']['warning'])} ({loc(gpu['unpinned']['warning'])})")
        elif inst_name not in insts:
            extra = ["unpinned"] if "unpinned" in gpu else []
            raise Refused(f"GPU instance {inst_name!r} not offered on {a.cluster}: "
                          f"{sorted(insts) + extra} ({loc(gpu['mig_availability'])})")
        else:
            inst = insts[inst_name]
        need = a.need_gpu_mem_gb
        if gpu_need is not None:
            if need is None:
                need = gpu_need["need_gb"]
                gpu_need["used"] = "derived (no --need-gpu-mem-gb)"
                notes.append(f"GPU memory needed: {need:.3f} GB, derived from the dry run (above); "
                             f"{a.cluster} {inst_name} has {val(inst['gpu_mem_gb'])} GB")
            else:
                gpu_need["used"] = f"overridden by --need-gpu-mem-gb {need:g}"
                notes.append(f"--need-gpu-mem-gb {need:g} given explicitly: it overrides the "
                             f"{gpu_need['need_gb']:.3f} GB derived from the dry run")
        if need is not None and val(inst["gpu_mem_gb"]) < need:
            how = ("" if a.need_gpu_mem_gb is not None else
                   " (derived from the dry run: device peak x (1 + margin), see the NOTE lines)")
            shown = f"{need}" if a.need_gpu_mem_gb is not None else f"{need:.3f}"
            raise Refused(f"{a.cluster} {inst_name} has {val(inst['gpu_mem_gb'])} GB of GPU memory "
                          f"< the {shown} GB you need{how} ({loc(inst['gpu_mem_gb'])})")
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
        if gpu_need is not None:
            if mem is not None:
                gpu_need["host_mem_requested_B"] = slurm_mem_bytes(mem)
                if slurm_mem_bytes(mem) < gpu_need["host_need_B"]:
                    _warn(warnings, f"--mem {mem} is below the host memory derived from the dry run "
                                    f"({gpu_need['host_need_B'] / 2**30:.2f} GiB, NOTE lines); pass "
                                    f"a larger --mem")
            else:
                notes.append(f"host memory per GPU is not requested on {a.cluster} "
                             f"({loc(gpu['pass_mem'])}); derived host need "
                             f"{gpu_need['host_need_B'] / 2**30:.2f} GiB")
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

    # --- GPU gate: gpu-check must have passed for this cluster, environment and engine code (F9) --
    run_root = Path(a.run_root)
    engine = engine_code_sha256(repo)
    gate = None
    gate_mode = "none"
    if needs_gpu and a.job != "gpu-check":
        ok, rejected = find_gate_pass(run_root, a.cluster, env["env_id"], engine["sha256"])
        if ok:
            gate = dict(status="PASS", record=str(ok[-1][0]), engine_code_sha256=engine["sha256"])
            gate_mode = "pass"
        elif a.skip_gpu_check_gate:
            gate = dict(status="SKIPPED by --skip-gpu-check-gate",
                        engine_code_sha256=engine["sha256"])
            gate_mode = "skipped"
            _warn(warnings, "no valid gpu-check PASS record for this cluster, environment and "
                            "engine code: the GPU path is UNVERIFIED (--skip-gpu-check-gate)")
        else:
            raise Refused(_gate_refusal(run_root, a.cluster, env["env_id"], engine["sha256"],
                                        rejected)
                          + f": run `submit.sh {a.cluster} gpu-check ...` first and check its "
                            f"log (the job re-checks this record when it starts). Override: "
                            f"--skip-gpu-check-gate")

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
                  RH_GPU_GATE=gate_mode, RH_ENGINE_SHA256=engine["sha256"],
                  RH_SUBMISSION_RECORD=_safe("record", a.record or ""))
    for k, v in export.items():
        _safe(k, v) if v else None
    argv.append("--export=ALL," + ",".join(f"{k}={v}" for k, v in export.items()))
    argv.append(str(JOB_SCRIPT))
    return dict(schema="reflholo_alliance_submission/2",
                created_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                cluster=a.cluster, job=a.job, argv=argv, warnings=warnings, notes=notes,
                gpu=gpu_rec, gpu_memory_need=gpu_need, cpus_per_task=cpus, threads=threads, mem=mem, time=a.time,
                time_minutes=minutes, array=array, gate=gate, config=config, variant=variant,
                study=study_rec, engine_code=engine,
                run_root=str(run_root), log_dir=str(logdir), env=env, repo=str(repo),
                commit=a.commit, record=a.record, profile_locators=dict(
                    walltime_max=loc(prof["walltime_max_hours"]),
                    job_limit=loc(prof["job_limit_queued_running"]),
                    gpu=gpu_rec["locator"] if gpu_rec else None))


def cmd_plan(a) -> int:
    try:
        plan = make_plan(a)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return exc.status
    for n in plan["notes"]:
        print(f"NOTE: {n}", file=sys.stderr)
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
            "SLURM_RESTART_COUNT", "CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "CUPY_CACHE_DIR",
            "NUMBA_CACHE_DIR", "MPLCONFIGDIR", "PYTHONNOUSERSITE", "VIRTUAL_ENV")
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


def cmd_copy_study(a) -> int:
    """Submission (F6): write the copy of the study file that every task will read."""
    data = Path(a.src).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != a.sha256:
        print(f"REFUSED: {a.src} changed after the plan was made (SHA-256 {sha}, planned "
              f"{a.sha256}); submit again", file=sys.stderr)
        return 2
    try:
        with open(a.dst, "xb") as fh:                    # never overwritten
            fh.write(data)
    except FileExistsError:
        print(f"REFUSED: {a.dst} exists; submission copies are never overwritten", file=sys.stderr)
        return 2
    print(f"study copy {a.dst} (SHA-256 {sha}); the job reads this copy")
    return 0


def cmd_verify_study(a) -> int:
    """Job start (F6): the study copy must still have the submitted hash; the job copies it into its
    own directory and reads only that copy."""
    try:
        data = Path(a.study).read_bytes()
    except OSError as exc:
        print(f"REFUSED: study copy {a.study} unreadable: {exc}; nothing was computed",
              file=sys.stderr)
        return 2
    sha = hashlib.sha256(data).hexdigest()
    if sha != a.sha256:
        print(f"REFUSED: study copy {a.study} has SHA-256 {sha}, the submission recorded "
              f"{a.sha256}: it was modified after submission; nothing was computed",
              file=sys.stderr)
        return 2
    if a.copy_to:
        with open(a.copy_to, "xb") as fh:
            fh.write(data)
    print(f"study: {a.study} SHA-256 {sha} as submitted"
          + (f"; job copy {a.copy_to}" if a.copy_to else ""))
    return 0


def cmd_env_check(a) -> int:
    """Job start (F9): the environment must be the one the job was submitted against."""
    envf = Path(a.env_dir) / "env.json"
    try:
        env = json.loads(envf.read_text())
    except (OSError, ValueError) as exc:
        print(f"REFUSED: {envf} unreadable ({exc}): the environment is being rebuilt or is "
              f"gone; nothing was computed", file=sys.stderr)
        return 2
    if env.get("setup_complete") is not True:
        print(f"REFUSED: {envf} is not a complete setup; nothing was computed", file=sys.stderr)
        return 2
    if env.get("env_id") != a.env_id:
        print(f"REFUSED: the environment was rebuilt after submission (submitted against "
              f"{a.env_id}, now {env.get('env_id')}); nothing was computed. Resubmit (GPU jobs "
              f"need a gpu-check PASS of the new environment)", file=sys.stderr)
        return 2
    print(f"environment: {a.env_id} (as submitted)")
    return 0


def cmd_gate_check(a) -> int:
    """Job start (F9): a PASS for this cluster, environment and the engine code as it is NOW."""
    try:
        engine = engine_code_sha256(Path(a.repo))
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    ok, rejected = find_gate_pass(Path(a.run_root), a.cluster, a.env_id, engine["sha256"])
    if not ok:
        print(f"REFUSED: {_gate_refusal(a.run_root, a.cluster, a.env_id, engine['sha256'], rejected)}"
              f"; checked when the job started, nothing was computed", file=sys.stderr)
        return 2
    print(f"gpu-check gate: {ok[-1][0].name} matches cluster {a.cluster}, environment {a.env_id} "
          f"and engine code {engine['sha256'][:12]}")
    return 0


def cmd_engine_hash(a) -> int:
    try:
        e = engine_code_sha256(Path(a.repo))
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(e["sha256"])
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
    p.add_argument("--array", action="store_true")
    p.add_argument("--array-throttle", type=int, default=None)
    p.add_argument("--kinds", default=None)
    p.add_argument("--gpu-instance", default=None)
    p.add_argument("--need-gpu-mem-gb", type=float, default=None)
    p.add_argument("--gpu-mem-from-dry-run", default=None)
    p.add_argument("--gpu-mem-margin", type=float, default=None)
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
    c = sub.add_parser("copy-study")
    c.add_argument("--src", required=True)
    c.add_argument("--dst", required=True)
    c.add_argument("--sha256", required=True)
    v = sub.add_parser("verify-study")
    v.add_argument("--study", required=True)
    v.add_argument("--sha256", required=True)
    v.add_argument("--copy-to", default=None)
    e = sub.add_parser("env-check")
    e.add_argument("--env-dir", required=True)
    e.add_argument("--env-id", required=True)
    g = sub.add_parser("gate-check")
    g.add_argument("--run-root", required=True)
    g.add_argument("--cluster", required=True)
    g.add_argument("--env-id", required=True)
    g.add_argument("--repo", required=True)
    h = sub.add_parser("engine-hash")
    h.add_argument("--repo", required=True)
    a = ap.parse_args(argv)
    return {"plan": cmd_plan, "study-point": cmd_study_point, "modules-diff": cmd_modules_diff,
            "job-record": cmd_job_record, "copy-study": cmd_copy_study,
            "verify-study": cmd_verify_study, "env-check": cmd_env_check,
            "gate-check": cmd_gate_check, "engine-hash": cmd_engine_hash}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
