"""Run manifest writer (docs/05_final_repository_specification.md section 6; acceptance criterion 4).

Every run writes a JSON manifest with: installed package versions (importlib.metadata, the pip-freeze
equivalent), Python and numpy versions, the git commit and dirty flag of this repository and, when
the tree is dirty, the SHA-256 of `git diff HEAD --binary` and the list and content hash of the
untracked files (audit A2 m8), the engines used (name, version, commit, licence), numeric precision,
random seeds, thread count with a check against the BLAS/OpenMP environment variables, SHA-256 of
the configuration and of every input file, the declared plane of every wave, and a UTC timestamp.
Manifests are written under an `outputs/` directory (gitignored). If git cannot be run the manifest
is refused unless the caller states allow_no_git=True (the failure is then recorded).

No field is defaulted: seeds, thread count, precision, engines, configuration and wave planes are
required arguments; an empty mapping is an explicit statement (e.g. "no engine used").
Every public entry point that writes output writes a manifest: io.validate_configs.main,
structure.write_xyz, structure.write_metadata_json.
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


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout


def git_state(root: Path | None = None) -> dict:
    """Commit, branch and dirty flag of the repository; when dirty, the SHA-256 of
    `git diff HEAD --binary` and the untracked files (sorted list, and a SHA-256 over
    path + NUL + SHA-256(content) of each). All None, with the error, if git fails.
    Source map: no row (software requirement, docs/05 section 6); evidence label: not
    applicable (no physical claim)."""
    root = Path(root) if root is not None else repository_root()
    try:
        commit = _git(root, "rev-parse", "HEAD").decode().strip()
        status = _git(root, "status", "--porcelain").decode()
        branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip()
        dirty = bool(status.strip())
        diff_sha = hashlib.sha256(_git(root, "diff", "HEAD", "--binary")).hexdigest() if dirty else None
        untracked = sorted(p for p in _git(root, "ls-files", "--others", "--exclude-standard",
                                           "-z").decode().split("\0") if p)
        untracked_sha = None
        if untracked:
            h = hashlib.sha256()
            for rel in untracked:
                h.update(rel.encode() + b"\0")
                h.update(bytes.fromhex(sha256_file(root / rel)))
            untracked_sha = h.hexdigest()
        return dict(commit=commit, dirty=dirty, branch=branch, diff_head_sha256=diff_sha,
                    untracked_files=untracked, untracked_sha256=untracked_sha, error=None)
    except (OSError, subprocess.CalledProcessError) as exc:
        return dict(commit=None, dirty=None, branch=None, diff_head_sha256=None,
                    untracked_files=None, untracked_sha256=None,
                    error=f"{type(exc).__name__}: {exc}")


class GitStateError(RuntimeError):
    """The git state of the repository is unavailable and the caller did not state allow_no_git."""


def package_tree_sha256(root: Path | None = None) -> dict:
    """SHA-256 over the package source tree reflection_holo/ (every *.py and *.yaml file, sorted by
    relative path; path + NUL + SHA-256(content) of each), so that a run without git still
    identifies the code that ran (audit A3 M5)."""
    pkg = (Path(root) if root is not None else repository_root()) / "reflection_holo"
    files = sorted(p for p in pkg.rglob("*") if p.is_file() and p.suffix in (".py", ".yaml")
                   and "__pycache__" not in p.parts)
    h = hashlib.sha256()
    for f in files:
        rel = f.relative_to(pkg).as_posix()
        h.update(rel.encode() + b"\0")
        h.update(bytes.fromhex(sha256_file(f)))
    return dict(sha256=h.hexdigest(), n_files=len(files), root=str(pkg),
                rule="sha256 over sorted relative path + NUL + sha256(content) of *.py, *.yaml")


def require_git_state(*, allow_no_git: bool) -> dict:
    """The git state (``git_state``) checked BEFORE a run computes anything (audit A3 M5): raises
    GitStateError when git is unavailable unless allow_no_git is True (then the error is recorded
    with the package-tree hash)."""
    repo = git_state()
    if repo["error"] is not None:
        if not allow_no_git:
            raise GitStateError(f"git state of the repository unavailable ({repo['error']}): the "
                                f"manifest could not identify the code that ran, so the run is "
                                f"refused before any computation; pass --allow-no-git "
                                f"(allow_no_git=True) to record the failure and the package-tree "
                                f"hash instead (audit A3 M5)")
        repo["allowed_without_git"] = True
    repo["package_tree"] = package_tree_sha256()
    return repo


def thread_check(thread_count: int) -> str:
    """Compare the declared thread count with the BLAS/OpenMP environment variables (audit A2 m8).
    The package does not set them: numpy's BLAS is initialised at import time."""
    env = {v: os.environ.get(v) for v in THREAD_ENV_VARS}
    set_vals = {k: v for k, v in env.items() if v is not None}
    if not set_vals:
        return (f"not set: {', '.join(THREAD_ENV_VARS)} are unset, so the BLAS/OpenMP libraries use "
                f"their defaults; the requested {thread_count} is not enforced")
    bad = [f"{k}={v}" for k, v in set_vals.items() if v.strip() != str(int(thread_count))]
    if bad:
        return f"MISMATCH: {', '.join(bad)} vs requested thread_count {thread_count}"
    return f"consistent: {', '.join(f'{k}={v}' for k, v in set_vals.items())}"


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
                   beam_energy_keV: float | None, extra: Mapping[str, Any] | None = None,
                   allow_no_git: bool = False) -> dict:
    """Assemble the manifest dictionary (all keywords required; see module docstring).

    config: a reflection_holo.io.config.LoadedConfig, a path to a configuration file, or None
    (explicitly: no configuration). input_paths: iterable of input files to hash (may be empty).
    seeds: name -> seed. thread_count: threads requested by the run. precision: e.g.
    {"real": "float64", "complex": "complex128"}. engines: name -> {version, commit, licence}.
    wave_planes: wave name -> declared plane (non-empty strings). beam_energy_keV: the energy of the
    run (200 keV for every configuration; None only for runs without a beam). allow_no_git: if git
    cannot be run the manifest is refused (RuntimeError) unless this is True.
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
                   absent_required=[list(t) for t in getattr(config, "missing_required", [])],
                   unverified=list(config.unverified))
    else:
        p = Path(config)
        cfg = dict(path=str(p), sha256_file=sha256_file(p), sha256_canonical=None,
                   config_id=None)

    repo = git_state()
    if repo["error"] is not None:
        if not allow_no_git:
            raise GitStateError(f"git state of the repository unavailable ({repo['error']}): the "
                                f"manifest cannot identify the code that ran; pass allow_no_git=True "
                                f"to record the failure explicitly (audit A2 m8)")
        repo["allowed_without_git"] = True
    repo["package_tree"] = package_tree_sha256()

    inputs = []
    for ip in input_paths:
        p = Path(ip)
        inputs.append(dict(path=str(p), sha256=sha256_file(p), bytes=p.stat().st_size))

    manifest = dict(
        manifest_schema=MANIFEST_SCHEMA,
        run_name=run_name,
        timestamp_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        repository=repo,
        python=dict(version=sys.version, implementation=platform.python_implementation(),
                    executable=sys.executable, platform=platform.platform()),
        numpy_version=np.__version__,
        packages=installed_packages(),
        engines=_json_safe(engines),
        precision=_json_safe(precision),
        seeds=_json_safe(seeds),
        threads=dict(requested=int(thread_count), os_cpu_count=os.cpu_count(),
                     environment={v: os.environ.get(v) for v in THREAD_ENV_VARS},
                     check=thread_check(int(thread_count))),
        config=cfg,
        inputs=inputs,
        wave_planes=_json_safe(wave_planes),
        beam_energy_keV=beam_energy_keV,
    )
    if extra:
        manifest["extra"] = _json_safe(extra)
    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    if missing:                                     # explicit raise: survives python -O
        raise RuntimeError(f"manifest lacks required keys {missing}")
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
