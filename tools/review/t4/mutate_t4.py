#!/usr/bin/env python3
"""T4: does each fix of audit A9a have a test that FAILS when the fix is reverted?

Each mutation is applied to a SCRATCH copy of the working tree (never the repository itself): the
directories reflection_holo, tests, tools, scripts, configs, docs and pyproject.toml are copied and
committed to a scratch git repository inside the copy (the pipeline tests' manifests need one), one
string replacement (or a whole-file restore from a commit) is applied and asserted to match exactly
once, and the named test files are run there with PYTHONPATH pointing at the copy (the imported
package path is printed as proof). Mutation "M0_control" changes nothing: its tests must pass.

Usage: PYTHONPATH=. venv/bin/python tools/review/t4/mutate_t4.py --work <scratch dir> [NAME ...]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PY = str(REPO / "venv/bin/python")
T_F = "tests/structure/test_buried_assertion_f_layers.py"
T_BT = "tests/forward/test_buried_torus_analysis.py"
T_CFG = "tests/pipeline/test_pipeline_feature.py"
F = "reflection_holo/structure/features.py"
BT = "tools/plots/buried_torus.py"
CFG = "reflection_holo/pipeline/config.py"

MUTATIONS = {
    "M0_control": ("replace", F, "MIN_LAYERS_BELOW_FEATURE = 4 ", "MIN_LAYERS_BELOW_FEATURE = 4 ",
                   [T_F, T_BT, T_CFG]),
    # m-4: the buried branch of assertion (f) disabled (A9a mutation M6)
    "M1_f_buried_branch_disabled": (
        "replace", F, "        if lay.min() < MIN_LAYERS_BELOW_FEATURE or lay.max() >= l_s:",
        "        if False:", [T_F]),
    # M-2 / m-2 / m-5 / m-6: T3's analysis script restored (floor rule, fits, no split)
    "M2_analysis_script_reverted_to_T3": ("restore", BT, "4c4a78b", None, [T_BT]),
    # M-2: the vacuum mask applied AFTER the aperture instead of before it
    "M3_mask_after_the_aperture": (
        "replace", BT, "    vac = specular_of(D * m, ew)\n    end = specular_of(D * (1.0 - m), ew)",
        "    vac = specular_of(D, ew) * m\n    end = specular_of(D, ew) * (1.0 - m)", [T_BT]),
    # M-2: a sharp (unapodised) vacuum mask
    "M4_sharp_vacuum_mask": (
        "replace", BT, "    return np.where(x <= 0.0, 0.0, np.sin(0.5 * np.pi * s) ** 2)",
        "    return np.where(x <= 0.0, 0.0, 1.0)", [T_BT]),
    # m-2: the geometric zero worded as an engine result again
    "M5_geometric_zero_wording": (
        "replace", BT, "height); not a geometric-engine run\")",
        "height); geometric engine: zero signal\")", [T_BT]),
    # m-3: the no-feature stand-in check removed
    "M6_no_feature_stand_in_check_removed": (
        "replace", CFG,
        "        if (p13.label == \"ASSUMPTION\" and aid in FEATURE_STAND_IN_SUB_KIND\n"
        "                and FEATURE_STAND_IN_SUB_KIND[aid] is not None):",
        "        if False:", [T_CFG]),
}


def copy_tree(dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    for d in ("reflection_holo", "tests", "tools", "scripts", "configs", "docs"):
        shutil.copytree(REPO / d, dest / d, ignore=ign)
    shutil.copy2(REPO / "pyproject.toml", dest / "pyproject.toml")
    # the copy is its own scratch git repository (the manifests of the pipeline tests need a git
    # state); this never touches the repository's .git
    for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "T4 mutation scratch copy"]):
        subprocess.run(["git", "-c", "user.name=t4", "-c", "user.email=t4@scratch.invalid", *cmd],
                       cwd=dest, check=True, capture_output=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("names", nargs="*")
    a = ap.parse_args(argv)
    names = a.names or list(MUTATIONS)
    rc_all = 0
    for name in names:
        kind, path, old, new, tests = MUTATIONS[name]
        dest = a.work / name
        copy_tree(dest)
        target = dest / path
        if kind == "restore":
            text = subprocess.run(["git", "show", f"{old}:{path}"], cwd=REPO, check=True,
                                  capture_output=True, text=True).stdout
            target.write_text(text)
            what = f"restored {path} from {old}"
        else:
            src = target.read_text()
            n = src.count(old)
            if n != 1:
                print(f"{name}: pattern found {n} times in {path}: NOT APPLIED")
                rc_all = 1
                continue
            target.write_text(src.replace(old, new))
            what = f"1 replacement in {path}"
        env = dict(PYTHONPATH=str(dest), PATH="/usr/bin:/bin", HOME="/root",
                   OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                   NUMEXPR_NUM_THREADS="1")
        who = subprocess.run([PY, "-c", "import reflection_holo; print(reflection_holo.__file__)"],
                             cwd=dest, env=env, capture_output=True, text=True).stdout.strip()
        r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests], cwd=dest,
                           env=env, capture_output=True, text=True)
        last = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1]
        failed = [ln for ln in r.stdout.splitlines() if ln.startswith("FAILED")]
        expect = "pass" if name == "M0_control" else "fail"
        ok = (r.returncode == 0) if expect == "pass" else (r.returncode != 0)
        rc_all |= 0 if ok else 1
        print(f"{name}: {what}; package {who}; tests {' '.join(tests)}")
        print(f"    result: {last}  -> expected to {expect}: {'OK' if ok else 'NOT AS EXPECTED'}")
        for ln in failed:
            print(f"    {ln}")
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
