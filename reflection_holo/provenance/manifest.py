"""Run manifest writer (docs/05_final_repository_specification.md section 6; acceptance criterion 4).

Every run writes a JSON manifest with: installed package versions (importlib.metadata, the pip-freeze
equivalent), Python and numpy versions, the git commit and dirty flag of this repository, the
engines used (name, version, commit, licence), numeric precision, random seeds, thread count,
SHA-256 of the configuration and of every input file, the declared plane of every wave, and a UTC
timestamp. Manifests are written under an `outputs/` directory (gitignored).

No field is defaulted: seeds, thread count, precision, engines, configuration and wave planes are
required arguments; an empty mapping is an explicit statement (e.g. "no engine used").
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.metadata as _md
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV

MANIFEST_SCHEMA = 1
REQUIRED_KEYS = ("manifest_schema", "run_name", "timestamp_utc", "repository", "python",
                 "numpy_version", "packages", "engines", "precision", "seeds", "threads",
                 "config", "inputs", "wave_planes", "beam_energy_keV")
THREAD_ENV_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                   "NUMEXPR_NUM_THREADS")


def repository_root() -> Path:
    """Root of the repository containing this package (the parent of reflection_holo/)."""
    return Path(__file__).resolve().parents[2]


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_state(root: Path | None = None) -> dict:
    """Commit hash and dirty flag of the repository (None with the error if git is unavailable).
    Source map: no row (software requirement, docs/05 section 6); evidence label: not
    applicable (no physical claim)."""
    root = Path(root) if root is not None else repository_root()
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                                capture_output=True, text=True).stdout.strip()
        status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], check=True,
                                capture_output=True, text=True).stdout
        branch = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                                check=True, capture_output=True, text=True).stdout.strip()
        return dict(commit=commit, dirty=bool(status.strip()), branch=branch, error=None)
    except (OSError, subprocess.CalledProcessError) as exc:
        return dict(commit=None, dirty=None, branch=None, error=f"{type(exc).__name__}: {exc}")


def installed_packages() -> dict[str, str]:
    """Name -> version of every installed distribution (importlib.metadata).
    Source map: no row (software requirement, docs/05 section 6); evidence label: not
    applicable (no physical claim)."""
    out = {}
    for dist in _md.distributions():
        name = dist.metadata["Name"]
        if name:
            out[name] = dist.version
    return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))


def _json_safe(x):
    if isinstance(x, Mapping):
        return {str(k): _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, Path):
        return str(x)
    return x


def build_manifest(*, run_name: str, config, input_paths, seeds: Mapping[str, Any],
                   thread_count: int, precision: Mapping[str, str],
                   engines: Mapping[str, Mapping[str, Any]], wave_planes: Mapping[str, str],
                   beam_energy_keV: float | None, extra: Mapping[str, Any] | None = None) -> dict:
    """Assemble the manifest dictionary (all keywords required; see module docstring).

    config: a reflection_holo.io.config.LoadedConfig, a path to a configuration file, or None
    (explicitly: no configuration). input_paths: iterable of input files to hash (may be empty).
    seeds: name -> seed. thread_count: threads requested by the run. precision: e.g.
    {"real": "float64", "complex": "complex128"}. engines: name -> {version, commit, licence}.
    wave_planes: wave name -> declared plane (non-empty strings). beam_energy_keV: the energy of the
    run (200 keV for every configuration; None only for runs without a beam).
    Source map: no row (software requirement, docs/05 section 6); evidence label: not
    applicable (no physical claim).
    """
    if not isinstance(run_name, str) or not run_name.strip():
        raise ValueError("run_name must be a non-empty string")
    if int(thread_count) != thread_count or thread_count < 1:
        raise ValueError("thread_count must be a positive integer")
    if not isinstance(precision, Mapping) or not precision:
        raise ValueError("precision must be a non-empty mapping, e.g. {'real': 'float64'}")
    for name, arg in (("seeds", seeds), ("engines", engines), ("wave_planes", wave_planes)):
        if not isinstance(arg, Mapping):
            raise ValueError(f"{name} must be a mapping (an empty mapping is an explicit 'none')")
    for wave, plane in wave_planes.items():
        if not isinstance(plane, str) or not plane.strip():
            raise ValueError(f"wave {wave!r} must declare its plane as a non-empty string")
    if beam_energy_keV is not None and float(beam_energy_keV) != BEAM_ENERGY_SUPPLIED_KEV:
        raise ValueError(f"beam energy {beam_energy_keV} keV refused: the beam energy is "
                         f"{BEAM_ENERGY_SUPPLIED_KEV:g} keV (PROJECT_INPUT item 1)")

    if config is None:
        cfg = dict(path=None, sha256_file=None, sha256_canonical=None, config_id=None,
                   note="no configuration file (stated explicitly by the caller)")
    elif hasattr(config, "sha256_canonical"):
        cfg = dict(path=config.source_path, sha256_file=config.sha256_file,
                   sha256_canonical=config.sha256_canonical, config_id=config.config_id,
                   level=config.level, test_only=config.test_only,
                   missing_project_inputs=[list(t) for t in config.missing_project_inputs],
                   unverified=list(config.unverified))
    else:
        p = Path(config)
        cfg = dict(path=str(p), sha256_file=sha256_file(p), sha256_canonical=None,
                   config_id=None)

    inputs = []
    for ip in input_paths:
        p = Path(ip)
        inputs.append(dict(path=str(p), sha256=sha256_file(p), bytes=p.stat().st_size))

    manifest = dict(
        manifest_schema=MANIFEST_SCHEMA,
        run_name=run_name,
        timestamp_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        repository=git_state(),
        python=dict(version=sys.version, implementation=platform.python_implementation(),
                    executable=sys.executable, platform=platform.platform()),
        numpy_version=np.__version__,
        packages=installed_packages(),
        engines=_json_safe(engines),
        precision=_json_safe(precision),
        seeds=_json_safe(seeds),
        threads=dict(requested=int(thread_count), os_cpu_count=os.cpu_count(),
                     environment={v: os.environ.get(v) for v in THREAD_ENV_VARS}),
        config=cfg,
        inputs=inputs,
        wave_planes=_json_safe(wave_planes),
        beam_energy_keV=beam_energy_keV,
    )
    if extra:
        manifest["extra"] = _json_safe(extra)
    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    assert not missing, missing
    return manifest


def write_manifest(manifest: Mapping[str, Any], *, outputs_root) -> Path:
    """Write the manifest to <outputs_root>/manifests/<run_name>_<UTC stamp>.json and return the path.

    outputs_root must be a directory named `outputs` (the gitignored output tree); it is created if
    absent. Refuses to overwrite an existing file.
    Source map: no row (software requirement, docs/05 section 6); evidence label: not
    applicable (no physical claim).
    """
    root = Path(outputs_root)
    if root.name != "outputs":
        raise ValueError(f"manifests are written under an 'outputs' directory, got {root}")
    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    if missing:
        raise ValueError(f"manifest lacks required keys {missing}")
    stamp = manifest["timestamp_utc"].replace(":", "").replace("-", "").replace("+0000", "Z")
    stamp = stamp.replace("+00:00", "Z")
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in manifest["run_name"])
    out_dir = root / "manifests"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe}_{stamp}.json"
    n = 1
    while path.exists():
        path = out_dir / f"{safe}_{stamp}_{n}.json"
        n += 1
    with open(path, "x", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return path
