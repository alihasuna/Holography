"""Run manifests and labelled configuration loading (docs/05 section 6)."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import yaml

LABELS = {"METADATA_VERIFIED", "SECTION_READ", "REPRODUCED", "PROJECT_INPUT", "ASSUMPTION",
          "DERIVED_HERE", "UNVERIFIED", "SMOKE_TEST"}


class Config:
    """YAML config where every physical parameter is {value, label[, note]}.

    `get` refuses missing keys and missing or unknown evidence labels: no default may silently
    replace a missing input.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.text = self.path.read_text()
        self.data = yaml.safe_load(self.text)
        self.used = {}

    def raw(self, dotted):
        node = self.data
        for k in dotted.split("."):
            if not isinstance(node, dict) or k not in node:
                raise KeyError(f"{self.path.name}: required key '{dotted}' is missing")
            node = node[k]
        return node

    def get(self, dotted):
        node = self.raw(dotted)
        if not (isinstance(node, dict) and "value" in node and "label" in node):
            raise ValueError(f"{self.path.name}: '{dotted}' must be {{value, label}}")
        if node["label"] not in LABELS:
            raise ValueError(f"{self.path.name}: '{dotted}' has unknown label {node['label']!r}")
        self.used[dotted] = {"value": node["value"], "label": node["label"]}
        return node["value"]

    @property
    def sha256(self):
        return hashlib.sha256(self.text.encode()).hexdigest()


def _git(*args):
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def write_manifest(out_dir, cfg: Config, extra: dict, backend: str = "numpy"):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    import numpy
    import scipy

    m = {
        "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.node(),
        "python": sys.version,
        "packages": {"numpy": numpy.__version__, "scipy": scipy.__version__},
        "backend": backend,
        "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "cpu_count": os.cpu_count(),
        "repository_commit": _git("rev-parse", "HEAD"),
        "repository_dirty": bool(_git("status", "--porcelain")),
        "config_path": str(cfg.path),
        "config_sha256": cfg.sha256,
        "parameters_used": cfg.used,
        "random_seeds": None,
    }
    if backend == "cupy":
        try:
            import cupy

            dev = cupy.cuda.runtime.getDeviceProperties(0)
            m["packages"]["cupy"] = cupy.__version__
            m["gpu"] = {"name": dev["name"].decode(), "total_mem_GB": dev["totalGlobalMem"] / 1e9,
                        "cuda_runtime": cupy.cuda.runtime.runtimeGetVersion()}
        except Exception as e:  # pragma: no cover
            m["gpu"] = f"unavailable: {e}"
    m.update(extra)
    (out_dir / "manifest.json").write_text(json.dumps(m, indent=2, default=str))
    return m
