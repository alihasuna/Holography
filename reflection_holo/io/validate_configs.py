"""Validate configuration files at both load levels and write a run manifest.

Usage: venv/bin/python -m reflection_holo.io.validate_configs [--outputs DIR] configs/cfg_*.yaml

For each file, prints the run-level verdict (PASS, or the refusal with the docs/06 item numbers or
the UNVERIFIED fields) and the placeholder-level summary. Writes a manifest under DIR/manifests
(DIR must be named "outputs"; the command line uses the repository's outputs/ unless --outputs is
given; main() requires outputs_root, so tests write only to a temporary directory).
Exit status 0 unless a file fails even the placeholder-level validation.
"""
from __future__ import annotations

import sys
from pathlib import Path

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.io.config import ConfigError, load_config_file
from reflection_holo.provenance.manifest import build_manifest, repository_root, write_manifest


def main(argv: list[str], *, outputs_root) -> int:
    if not argv:
        print(__doc__)
        return 2
    status = 0
    results = {}
    for arg in argv:
        path = Path(arg)
        try:
            cfg = load_config_file(path, level="placeholder")
        except ConfigError as exc:
            print(f"{path.name}: INVALID: {exc}")
            results[path.name] = dict(placeholder="INVALID", error=str(exc))
            status = 1
            continue
        try:
            load_config_file(path, level="run")
            run = "PASS"
        except ConfigError as exc:
            run = f"REFUSED ({type(exc).__name__}): {exc}"
        print(f"{path.name}: {cfg.config_id} status={cfg.status}")
        print(f"   run level        : {run}")
        print(f"   missing PROJECT_INPUT (name, docs/06 item): {cfg.missing_project_inputs}")
        print(f"   absent required parameters (name, docs/06 item): {cfg.missing_required}")
        print(f"   UNVERIFIED fields: {cfg.unverified}")
        print(f"   sha256(file)     : {cfg.sha256_file}")
        results[path.name] = dict(run_level=run, missing=cfg.missing_project_inputs,
                                  absent_required=cfg.missing_required,
                                  unverified=cfg.unverified, sha256_file=cfg.sha256_file)
    manifest = build_manifest(
        run_name="validate_configs", config=None, input_paths=[Path(a) for a in argv
                                                               if Path(a).is_file()],
        seeds={}, thread_count=1, precision={"real": "float64"}, engines={}, wave_planes={},
        beam_energy_keV=BEAM_ENERGY_SUPPLIED_KEV, extra=dict(results=results))
    out = write_manifest(manifest, outputs_root=outputs_root)
    print(f"manifest: {out}")
    return status


def _cli(args: list[str]) -> int:
    out = repository_root() / "outputs"
    if args[:1] == ["--outputs"]:
        if len(args) < 2:
            print(__doc__)
            return 2
        out, args = Path(args[1]), args[2:]
    return main(args, outputs_root=out)


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
