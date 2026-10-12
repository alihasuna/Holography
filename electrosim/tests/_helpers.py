"""Shared test helpers: locate code/ and params/, skip cleanly when an optional package is missing, and build
small synthetic stage folders. Works under pytest and under tests/run_tests.py (no pytest needed)."""

import importlib
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find(name, marker):
    for d in (HERE.parent, HERE.parent / name, HERE.parent.parent / name):
        if (d / marker).exists():
            return d
    raise RuntimeError(f"cannot find the {name}/ folder next to {HERE}")


CODE = _find("code", "holo_common.py")
PARAMS = _find("params", "holo.yaml")
if str(CODE) not in sys.path:
    sys.path.append(str(CODE))


def need(module):
    """Import a module or skip the test (unittest.SkipTest is a skip for pytest and for run_tests.py)."""
    try:
        return importlib.import_module(module)
    except ImportError as e:
        raise unittest.SkipTest(f"{module} not importable: {e}")


def load_yaml(name):
    yaml = need("yaml")
    return yaml.safe_load((PARAMS / name).read_text())


def write_yaml(path, data):
    yaml = need("yaml")
    Path(path).write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def run_script(script, *args, cwd=None):
    """Run a pipeline script with this interpreter; returns CompletedProcess (never raises on failure)."""
    env = dict(os.environ)
    env.setdefault("MPLBACKEND", "Agg")
    return subprocess.run([sys.executable, str(CODE / script)] + [str(a) for a in args], cwd=cwd,
                          capture_output=True, text=True, env=env)


def write_exit_wave_stage(folder, psi, sampling, energy_keV=200.0, gt=None):
    """A minimal exit_wave stage folder (as written by multislice_forward_model.py) from an array."""
    import numpy as np
    import holo_common as hc
    out = hc.Output(folder)
    out.save_array("exit_wave", psi.astype(np.complex64), units="dimensionless", axes=["x", "y"],
                   sampling_A=sampling, description="synthetic test wave")
    out.save_array("ground_truth_phase", (np.angle(psi) if gt is None else gt).astype(np.float32), units="rad",
                   axes=["x", "y"], sampling_A=sampling, description="synthetic truth")
    lam = hc.wavelength_A(energy_keV)
    physics = {"energy_keV": energy_keV, "wavelength_A": lam, "tilts_mrad": [[0.0, 0.0]],
               "antialias_cutoff_inv_A": (2.0 / 3.0) / (2.0 * max(sampling)),
               "wave_plane": "synthetic", "frozen_phonons": {"seeds": []}}
    hc.write_sidecar(out, "exit_wave", {}, {"synthetic": True}, physics, {"plots": []})
    out.publish()
    return Path(folder)


def smooth_step(n, sampling, x0_A, width_A, height):
    """Phase map with a tanh step along x (axis 0): 0 for x < x0, `height` beyond (periodic-safe if x0 central)."""
    import numpy as np
    x = (np.arange(n[0]) * sampling[0])[:, None] * np.ones(n)
    return height * 0.5 * (1 + np.tanh((x - x0_A) / width_A))
