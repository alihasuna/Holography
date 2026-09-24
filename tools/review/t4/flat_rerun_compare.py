#!/usr/bin/env python3
"""T4 (fix of audit A9a m-1): compare the rerun of buried_flat_r010 on the committed tree with T3's run.

T3's paired runs (report T3 section 3) were made while other agents edited the working tree, and
each manifest records the package tree at the END of its run (A9a m-1). T4 reran buried_flat_r010
once, unchanged (scripts/torus/run_torus_multislice.py --kind buried_flat --absorption
test_only_r0.1 --max-cpu-seconds 3600, 2 FFT workers), from a clean clone of the committed tree.
This script compares the two exit waves (bitwise and max |difference|), the two structure files,
the grid and plane records, and prints the repository and package-tree records of both manifests,
plus the package-tree hashes of the committed trees 39b6151 (T3's recorded engine commit),
4c4a78b (the snapshot that committed T3's and X4's edits) and the clone's commit, computed with
reflection_holo.provenance.manifest.package_tree_sha256 on `git archive` extractions, and the list
of propagation-path files that differ between those commits.

Usage: PYTHONPATH=. venv/bin/python tools/review/t4/flat_rerun_compare.py --t3-run DIR --rerun DIR
       --work DIR   (DIR for the git-archive extractions; nothing is written in the repository)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
import io
from pathlib import Path

import numpy as np

from reflection_holo.forward.multislice import PLANE_TEXT, load_exit_wave
from reflection_holo.provenance.manifest import package_tree_sha256

REPO = Path(__file__).resolve().parents[3]
NAME = "buried_flat_r010"
# files whose code runs when a flat Si(001) cell is built and propagated by the runner (import
# closure of the executed functions; the pipeline and oxide modules are not executed)
PROPAGATION_PATH = [
    "reflection_holo/forward/multislice/engine.py", "reflection_holo/forward/multislice/potentials.py",
    "reflection_holo/forward/multislice/grid.py", "reflection_holo/forward/multislice/propagator.py",
    "reflection_holo/forward/multislice/illumination.py", "reflection_holo/forward/multislice/backend.py",
    "reflection_holo/forward/multislice/physics.py", "reflection_holo/forward/multislice/exitwave_io.py",
    "reflection_holo/forward/multislice/overlayer.py", "reflection_holo/forward/cell.py",
    "reflection_holo/forward/feature_cell.py", "reflection_holo/forward/contracts.py",
    "reflection_holo/structure/features.py", "reflection_holo/structure/shapes.py",
    "reflection_holo/structure/si001.py", "reflection_holo/geometry/refraction.py",
    "reflection_holo/geometry/specular.py", "reflection_holo/geometry/frames.py",
    "reflection_holo/constants.py", "scripts/torus/run_torus_multislice.py"]


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True,
                          text=True).stdout


def tree_hash(commit: str, work: Path) -> dict:
    dest = work / f"tree_{commit}"
    if not (dest / "reflection_holo").exists():
        dest.mkdir(parents=True, exist_ok=True)
        data = subprocess.run(["git", "archive", commit, "reflection_holo"], cwd=REPO, check=True,
                              capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(data)) as tf:
            tf.extractall(dest)
    return package_tree_sha256(dest)


def one(run: Path):
    ew_p = sorted(run.glob(f"outputs/exit_waves/torus_{NAME}_r0000.npz"))
    man = sorted(run.glob(f"outputs/manifests/torus_{NAME}_*.json"))
    if len(ew_p) != 1 or len(man) != 1:
        raise FileNotFoundError(f"{run}: expected one exit wave and one manifest")
    ew = load_exit_wave(ew_p[0], expected_plane=PLANE_TEXT)
    m = json.loads(man[0].read_text())
    with np.load(run / f"structure_{NAME}.npz", allow_pickle=False) as f:
        pos = np.array(f["positions_A"])
    return ew, m, pos, ew_p[0], man[0]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--t3-run", required=True, type=Path)
    ap.add_argument("--rerun", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    a = ap.parse_args(argv)
    ew3, m3, pos3, p3, man3 = one(a.t3_run)
    ew4, m4, pos4, p4, man4 = one(a.rerun)
    print(f"T3 run  : {p3}\nT4 rerun: {p4}")
    for lab, m, man in (("T3 run", m3, man3), ("T4 rerun", m4, man4)):
        r = m["repository"]
        print(f"{lab} manifest {man.name}: commit {r['commit']}, dirty {r['dirty']}, diff_head_sha256 "
              f"{r.get('diff_head_sha256')}, package_tree {r['package_tree']['sha256']} "
              f"({r['package_tree']['n_files']} files), timestamp {m['timestamp_utc']}, threads "
              f"{m['threads']['requested']} ({m['threads']['check']})")
    same_grid = all(np.isclose(getattr(ew3, k), getattr(ew4, k), rtol=0, atol=0)
                    for k in ("dx_A", "dy_A", "x0_A", "y0_A", "z_A", "energy_keV", "theta_in_ext_rad"))
    print(f"grid, plane, energy, angle identical: {same_grid and ew3.plane == ew4.plane and ew3.psi.shape == ew4.psi.shape}"
          f" ({ew3.psi.shape}, dx {ew3.dx_A:.6f} A, dy {ew3.dy_A:.6f} A, {ew3.energy_keV:g} keV)")
    print(f"structure positions bitwise identical: {np.array_equal(pos3, pos4)} ({len(pos3)} atoms)")
    b3 = np.ascontiguousarray(ew3.psi).tobytes()
    b4 = np.ascontiguousarray(ew4.psi).tobytes()
    d = np.abs(ew3.psi.astype(np.complex128) - ew4.psi.astype(np.complex128))
    print(f"exit wave dtype {ew3.psi.dtype} / {ew4.psi.dtype}; sha256 {hashlib.sha256(b3).hexdigest()[:16]} / "
          f"{hashlib.sha256(b4).hexdigest()[:16]}")
    print(f"exit waves bitwise equal: {b3 == b4}; max |psi_T3 - psi_T4| = {d.max():.3e} "
          f"(max |psi| {np.abs(ew3.psi).max():.4f})")
    commits = {"39b6151": "T3's recorded engine commit", "4c4a78b": "snapshot committing T3 + X4 edits",
               m4["repository"]["commit"][:7]: "commit of the T4 rerun (clean clone)"}
    for c, lab in commits.items():
        h = tree_hash(c, a.work)
        print(f"package tree of {c} ({lab}): {h['sha256']} ({h['n_files']} files)")
    head = m4["repository"]["commit"]
    for base in ("39b6151", "4c4a78b"):
        changed = [f for f in PROPAGATION_PATH
                   if git("diff", "--name-only", base, head, "--", f).strip()]
        print(f"propagation-path files changed between {base} and {head[:7]}: {changed if changed else 'none'}")
        allpkg = git("diff", "--name-only", base, head, "--", "reflection_holo").split()
        print(f"  all package files changed between {base} and {head[:7]}: {allpkg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
