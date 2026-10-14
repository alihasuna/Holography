"""Every module of the package and every script imports (catches syntax errors in
code paths that the numerical tests do not exercise)."""
import importlib
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODULES = ["aggregate", "analysis", "backend", "beams", "campaign", "constants", "crystal",
           "geometry", "grid", "io", "multislice", "potential", "provenance", "reference1d",
           "simulate", "worker"]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(f"reflection_holo.{name}")


@pytest.mark.parametrize("path", ["fir/gpu_selftest.py", "validation/abtem_crosscheck.py"])
def test_scripts_compile(path):
    with open(os.path.join(ROOT, path)) as fh:
        compile(fh.read(), path, "exec")
