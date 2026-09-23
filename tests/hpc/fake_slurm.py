"""Fake Slurm and Lmod commands for the Alliance-kit tests (tests/hpc). Not a test module.

* `module`: records its calls; `module -t list` prints MODULES (to stderr, as Lmod does).
* `sbatch` in record mode: writes its argv (one per line) and prints "Submitted batch job N".
* `sbatch` in execute mode (FAKE_SBATCH_EXECUTE=1): a minimal emulation of a batch job: parses
  --export=ALL,K=V,..., --output (%j, %A, %a), --chdir, --cpus-per-task and --array (runs the tasks
  listed in FAKE_SBATCH_TASKS, default the first index only), sets SLURM_JOB_ID,
  SLURM_CPUS_PER_TASK, SLURM_ARRAY_JOB_ID and SLURM_ARRAY_TASK_ID and runs the script with bash,
  stdout and stderr to the output file. No GPU, no scontrol, no nvidia-smi.
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

MODULES = ["StdEnv/2023", "python/3.11.5", "cuda/12.6"]

MODULE_SH = """#!/bin/bash
echo "module $*" >> "$(dirname "$0")/../module_calls.txt"
if [ "${1:-}" = "-t" ] && [ "${2:-}" = "list" ]; then
  printf '%s\\n' """ + " ".join(MODULES) + """ >&2
fi
exit 0
"""

SBATCH_PY = r'''
import os, re, subprocess, sys
from pathlib import Path
args = sys.argv[1:]
here = Path(__file__).resolve().parent.parent
(here / "sbatch_args.txt").write_text("\n".join(args) + "\n")
jobid = int((here / "next_jobid").read_text()) if (here / "next_jobid").exists() else 900001
(here / "next_jobid").write_text(str(jobid + 100))
if os.environ.get("FAKE_SBATCH_EXECUTE") != "1":
    print(f"Submitted batch job {jobid}")
    sys.exit(0)
opts, script = args[:-1], args[-1]
o = {}
for a in opts:
    k, _, v = a.partition("=")
    o[k] = v
env = dict(os.environ)
exp = o["--export"].split(",")
assert exp[0] == "ALL", exp
for kv in exp[1:]:
    k, _, v = kv.partition("=")
    env[k] = v
env.pop("FAKE_SBATCH_EXECUTE", None)
if "--cpus-per-task" in o:
    env["SLURM_CPUS_PER_TASK"] = o["--cpus-per-task"]
env["SLURM_CPUS_ON_NODE"] = o.get("--cpus-per-task", "24")
runs = []
if "--array" in o:
    m = re.match(r"^(\d+)-(\d+)(%\d+)?$", o["--array"])
    first = int(m[1])
    tasks = [int(t) for t in os.environ.get("FAKE_SBATCH_TASKS", str(first)).split()]
    for t in tasks:
        runs.append(dict(SLURM_JOB_ID=str(jobid + 1 + t), SLURM_ARRAY_JOB_ID=str(jobid),
                         SLURM_ARRAY_TASK_ID=str(t)))
else:
    runs.append(dict(SLURM_JOB_ID=str(jobid)))
status = 0
for r in runs:
    e = dict(env, **r)
    out = o["--output"].replace("%A", r.get("SLURM_ARRAY_JOB_ID", "")).replace(
        "%a", r.get("SLURM_ARRAY_TASK_ID", "")).replace("%j", r["SLURM_JOB_ID"])
    with open(out, "w") as fh:
        p = subprocess.run(["bash", script], cwd=o["--chdir"], env=e, stdout=fh,
                           stderr=subprocess.STDOUT)
    (here / f"job_{r['SLURM_JOB_ID']}.status").write_text(str(p.returncode))
    status = status or p.returncode
print(f"Submitted batch job {jobid}")
'''


def make_fakebin(root: Path) -> Path:
    b = root / "bin"
    b.mkdir(parents=True, exist_ok=True)
    (b / "module").write_text(MODULE_SH)
    (b / "sbatch").write_text(f"#!{sys.executable}\n" + SBATCH_PY)
    for f in ("module", "sbatch"):
        (b / f).chmod((b / f).stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return b


def make_env_dir(root: Path, cluster: str, env_id: str | None = None) -> Path:
    e = root / "env"
    e.mkdir(parents=True, exist_ok=True)
    (e / "modules.sh").write_text("module purge\n" + "".join(f"module load {m}\n" for m in MODULES))
    (e / "module_list.txt").write_text("\n".join(MODULES) + "\n")
    env_id = env_id or f"{cluster}-20260923T000000Z-0123456789ab"
    (e / "env.json").write_text(
        '{"schema": "reflholo_alliance_env/1", "cluster": "%s", "env_id": "%s", '
        '"setup_complete": true}' % (cluster, env_id))
    return e


def clean_environ(**extra) -> dict:
    """os.environ without Slurm/kit variables and without an inherited Lmod `module` function."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "SLURM_", "SBATCH_", "SALLOC_", "BASH_FUNC_", "FAKE_"))}
    env.update(extra)
    return env
