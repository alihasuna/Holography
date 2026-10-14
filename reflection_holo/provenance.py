"""Run manifests (specification section 6)."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def git_state():
    try:
        commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                                text=True, timeout=20).stdout.strip()
        dirty = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--",
                                "reflection_holo", "configs", "fir"], capture_output=True,
                               text=True, timeout=20).stdout.strip()
        return dict(commit=commit or "unknown", dirty=bool(dirty))
    except Exception as exc:  # noqa: BLE001
        return dict(commit="unknown", dirty=None, error=str(exc))


def package_versions():
    out = dict(python=sys.version.split()[0], platform=platform.platform())
    for name in ("numpy", "scipy", "h5py", "cupy", "yaml"):
        try:
            mod = __import__(name)
            out[name] = getattr(mod, "__version__", "unknown")
        except Exception:  # noqa: BLE001
            out[name] = None
    return out


def job_environment():
    keys = ("SLURM_JOB_ID", "SLURM_JOB_NAME", "SLURM_ARRAY_TASK_ID", "SLURM_NODELIST",
            "SLURM_CPUS_PER_TASK", "CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS",
            "CUPY_CACHE_DIR")
    env = {k: os.environ.get(k) for k in keys}
    env["hostname"] = socket.gethostname()
    return env


def pip_freeze():
    try:
        return subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True,
                              text=True, timeout=120).stdout.splitlines()
    except Exception as exc:  # noqa: BLE001
        return [f"pip freeze failed: {exc}"]


def task_manifest(task, backend_info, started, finished):
    data = os.path.join(ROOT, "reflection_holo", "data", "si_parametrizations.json")
    return dict(
        task_sha256=sha256_json(task),
        seed=task.get("seed"),
        precision=task["numerics"].get("precision"),
        started=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(started)),
        finished=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(finished)),
        wall_seconds=finished - started,
        git=git_state(),
        packages=package_versions(),
        backend=backend_info,
        environment=job_environment(),
        input_hashes={"reflection_holo/data/si_parametrizations.json": sha256_file(data)},
        licences=dict(reflection_holo="undecided (docs/05 section 6)", numpy="BSD-3-Clause",
                      cupy="MIT", h5py="BSD-3-Clause",
                      parametrisation_values="copied from abTEM 1.0.10 (GPL-3.0-or-later); "
                                             "numerical values originate from Kirkland 2010 "
                                             "and Lobato and Van Dyck 2014"),
    )
