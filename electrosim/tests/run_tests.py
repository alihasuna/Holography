#!/usr/bin/env python3
"""Run the test suite without pytest (ElectroSim's environments do not list pytest).

    /opt/envs/em-holography/bin/python code/tests/run_tests.py      # or tests/run_tests.py in this repository
    /opt/envs/em-abtem/bin/python code/tests/run_tests.py           # also runs the abTEM tests

Discovers test_*.py next to this file, calls every test_* function (giving a fresh temporary folder to
functions that take `tmp_path`), treats unittest.SkipTest as a skip, and exits 1 on any failure.
With pytest available, `python -m pytest -q tests` runs the same tests.
"""

import importlib.util
import inspect
import sys
import tempfile
import time
import traceback
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    sys.path.insert(0, str(HERE))
    only = sys.argv[1:]
    passed, failed, skipped = 0, [], []
    t0 = time.time()
    for f in sorted(HERE.glob("test_*.py")):
        if only and not any(o in f.name for o in only):
            continue
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except unittest.SkipTest as e:
            skipped.append((f.name, str(e)))
            continue
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if not name.startswith("test_") or fn.__module__ != mod.__name__:
                continue
            label = f"{f.name}::{name}"
            try:
                if "tmp_path" in inspect.signature(fn).parameters:
                    with tempfile.TemporaryDirectory() as d:
                        fn(tmp_path=Path(d))
                else:
                    fn()
                passed += 1
                print(f"PASS {label}")
            except unittest.SkipTest as e:
                skipped.append((label, str(e)))
                print(f"SKIP {label}: {e}")
            except Exception:
                failed.append(label)
                print(f"FAIL {label}")
                traceback.print_exc()
    print(f"\n{passed} passed, {len(failed)} failed, {len(skipped)} skipped in {time.time() - t0:.1f} s")
    for s in skipped:
        print(f"  skipped {s[0]}: {s[1]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
