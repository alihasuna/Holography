"""Validation ladder (docs/05 section 4.4) at reduced size on the CPU.

Marked slow (minutes each).  Uses the smoke configuration's numerics (strong
absorption, coarse 0.1 A sampling) and the tolerances of configs/benchmarks.yaml.
The same checks run at production sampling on Fir in stage `validation`.
"""
import os

import numpy as np
import pytest
import yaml

from reflection_holo.campaign import load_config, make_task, numerics, physics, windows
from reflection_holo.constants import k_rad_per_A
from reflection_holo.simulate import run_task

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CFG = load_config(os.path.join(ROOT, "configs", "smoke_cpu.yaml"))
BM = yaml.safe_load(open(os.path.join(ROOT, "configs", "benchmarks.yaml")))
K = float(k_rad_per_A(200.0))
pytestmark = pytest.mark.slow


def _run(t):
    t["backend"] = "numpy"
    return run_task(t, log=lambda s: None)


def _check_ref(w, tol):
    rp = w["r_parratt_multislice"]
    m = w["weight"] >= BM["weight_min"]
    err = np.abs(w["r"] - rp)
    assert np.all(err[m] <= np.maximum(tol["amp_rel"] * np.abs(rp[m]), tol["amp_abs_floor"]))
    mp = m & (np.abs(rp) >= tol["phase_min_abs_r"])
    assert np.max(np.abs(np.angle(w["r"][mp] / rp[mp]))) <= tol["phase_rad"]
    assert w["record_tail_rel"] < 1e-3 and w["record_head_rel"] < 1e-3


@pytest.mark.parametrize("theta,W", [(13.0, 0.0), (25.0, 2.0)])
def test_rung1_fermi_step(theta, W):
    t = make_task(CFG, "test", "uniform_1d", None, dict(kind="uniform"), windows([theta], 6.0),
                  numerics(CFG), phys=physics(CFG, inelastic_absorption_W_V=W),
                  extra=dict(profile=dict(V0_V=13.9, width_A=0.2, clearance_ref_A=2.0)))
    _check_ref(_run(t)["windows"][0], BM["rung1_uniform_step"])


def test_rung2_laterally_averaged_si111():
    t = make_task(CFG, "test", "averaged_1d", "si111_110", dict(kind="flat", level=0),
                  windows([13.3], 6.0), numerics(CFG))
    _check_ref(_run(t)["windows"][0], BM["rung2_averaged_crystal"])


def _ratio(surface, levels, theta):
    out = {}
    for L in (0, levels):
        t = make_task(CFG, "test", "flat_rocking", surface, dict(kind="flat", level=L),
                      windows([theta], 6.0), numerics(CFG))
        w = _run(t)["windows"][0]
        out[L] = w
    w0, w1 = out[0], out[levels]
    assert np.allclose(w0["theta"], w1["theta"])
    return w0, w1


@pytest.mark.parametrize("surface,levels,theta,h", [
    ("si111_110", 1, 20.0, 5.4309 / np.sqrt(3)),     # bilayer: lattice translation
    ("si001_100", 1, 16.2, 5.4309 / 4),              # a/4 at [100]: mirror-related terraces
])
def test_rung3_null(surface, levels, theta, h):
    tol = BM["rung3_null"]
    w0, w1 = _ratio(surface, levels, theta)
    m = (w0["weight"] >= BM["weight_min"]) & (np.abs(w0["r"]) >= tol["min_abs_r"]) \
        & (np.abs(w1["r"]) >= tol["min_abs_r"])
    geo = -2.0 * K * np.sin(w0["theta"]) * h
    resid = np.angle(w1["r"] / w0["r"] * np.exp(-1j * geo))
    assert m.sum() > 10
    assert np.max(np.abs(resid[m])) <= tol["phase_rad"]
    assert np.max(np.abs(np.abs(w1["r"] / w0["r"])[m] - 1)) <= tol["amp_rel"]
