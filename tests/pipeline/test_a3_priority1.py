"""Regression tests of the priority-1 fixes of audit A3 (docs/agent_reports/A3_pipeline_audit.md;
report docs/agent_reports/S4_pipeline_fixes.md). Each test reproduces the auditor's case.

* B1 (a): a failed or not-performed no-step control withholds EVERY height of the run; the summary
  and the CLI say so first ("NO HEIGHT: no-step control failed or not performed").
* B1 (a): the lattice-constraint branch refuses phases that carry no height information at the
  rate the 3-sigma criterion implies: accepted with probability <= alpha = P(|Z| > 3) = 2.70e-3.
  Monte Carlo, seeds recorded below; the acceptance counts are judged with exact binomial
  quantiles at the same 3-sigma level (one-sided 1 - alpha).
* M3 (b): the incidence and exit angles of the specular beam share one calibration error:
  sigma_s = 2 k cos(theta) sigma_theta (not sqrt(2) k cos(theta) sigma_theta), so the smoke demo's
  a/2 step has sigma_h = 0.0165 A (A3: 0.0117 A reported, 0.0165 A expected).
* M5 (c): without a git state the run is refused BEFORE any computation (no arrays written), with
  exit status 6 from the CLI, unless --allow-no-git.

Acceptance criteria were fixed before the fixes were written.
"""
import dataclasses
import importlib
import json
import math
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest

import reflection_holo.pipeline.quantify as Q
import reflection_holo.provenance.manifest as MAN
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.pipeline import run
from reflection_holo.pipeline.__main__ import main as cli_main

from conftest_pipeline import REPO, SMOKE

R = importlib.import_module("reflection_holo.pipeline.run")   # the package exports run(), a function

LAM = wavelength_A(200.0)
K_VAC = 2 * math.pi / LAM
A_SI = 5.4309
LAYER = A_SI / 4
TH_B19 = 16.47433279927e-3          # smoke demo angle (B19, V0 = 12.0 V; A3 "Verified correct" 1)
TH_B32 = 16.13472004381e-3          # HPC demo angle (B32, V0 = 13.903 V)
SIG_THETA = 1.0e-4                  # demo angle-calibration sigma (B19), rad
SIG_LAMBDA = 1.0e-5                 # demo relative wavelength sigma (B31)
ALPHA = math.erfc(3 / math.sqrt(2))  # P(|Z| > 3) = 2.6998e-3
SEED_SINGLE = 1                     # the auditor's seed (branch_power.py)
SEED_JOINT = 20260923
SEED_POWER = 20260924
SEED_ANGLE = 20260925


def _binom_quantile(n: int, p: float, q: float) -> int:
    """Smallest k with P(X <= k) >= q for X ~ Binomial(n, p) (exact, log-space pmf)."""
    if p <= 0.0:
        return 0
    if p >= 1.0:
        return n
    lp, lq = math.log(p), math.log1p(-p)
    cdf = 0.0
    for k in range(n + 1):
        cdf += math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                        + k * lp + (n - k) * lq)
        if cdf >= q:
            return k
    return n


def _s(th):
    return 2 * K_VAC * math.sin(th)


def _sig_s_common(th):
    return math.hypot(2 * K_VAC * math.cos(th) * SIG_THETA, _s(th) * SIG_LAMBDA)


# --------------------------------------------------------------------------------------------------
# B1: the no-step control gates every height
# --------------------------------------------------------------------------------------------------
def _slope_engine(monkeypatch, slope_rad_per_A):
    """The auditor's repro_nostep.py: a slow phase exp(i g x) (the signature of charging, B8) on
    the geometric exit wave."""
    orig = R.run_geometric

    def patched(structure, cfg):
        waves, model, grun = orig(structure, cfg)
        ew = waves[0]
        x = ew.x0_A + ew.dx_A * np.arange(ew.psi.shape[0])
        ew2 = dataclasses.replace(ew, psi=ew.psi * np.exp(1j * slope_rad_per_A * x)[:, None])
        return [ew2], model, grun
    monkeypatch.setattr(R, "run_geometric", patched)


def test_failed_no_step_control_withholds_every_height(tmp_path, monkeypatch):
    """A3 B1 reproduction 1 (slope 0.001 rad/A): the control fails (delta -0.0191 rad, tolerance
    0.0169 rad in A3), so no step may carry a height."""
    _slope_engine(monkeypatch, 0.001)
    s = run(SMOKE, tmp_path / "nostep")
    c = s["quantification"]["no_step_control"]
    assert c["performed"] and not c["passed"], c
    measured = [st for st in s["quantification"]["steps"] if st["measured"]]
    assert len(measured) == 3
    for st in measured:
        assert st.get("height") is None, st.get("height")
        assert st["reason"].startswith("no-step control failed or not performed"), st["reason"]
        assert f"{c['tolerance_rad']:.4f}" in st["reason"]
    v = s["height_verdict"]
    assert v["withheld"] and v["heights_returned"] == 0
    assert v["line"].startswith("NO HEIGHT: no-step control failed or not performed")


def test_cli_prints_the_withheld_verdict_before_the_steps(tmp_path, monkeypatch, capsys):
    _slope_engine(monkeypatch, 0.001)
    assert cli_main(["run", "--config", str(SMOKE), "--out", str(tmp_path / "cli")]) == 0
    lines = capsys.readouterr().out.splitlines()
    first_step = next(i for i, ln in enumerate(lines) if ln.startswith("step field terraces"))
    verdict = [i for i, ln in enumerate(lines)
               if ln.startswith("NO HEIGHT: no-step control failed or not performed")]
    assert verdict and verdict[0] < first_step, lines
    for ln in lines[first_step:first_step + 3]:
        assert "no height: no-step control failed or not performed" in ln, ln


def test_control_not_performed_withholds_every_height(tmp_path, monkeypatch):
    monkeypatch.setattr(Q, "no_step", lambda *a, **k: dict(performed=False,
                                                           reason="TEST: forced not performed"))
    s = run(SMOKE, tmp_path / "notperf")
    for st in s["quantification"]["steps"]:
        assert st.get("height") is None
        assert "no-step control failed or not performed" in st["reason"]
        assert "TEST: forced not performed" in st["reason"]
    assert s["height_verdict"]["withheld"]


# --------------------------------------------------------------------------------------------------
# B1: pure noise is refused at the 3-sigma rate
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("th", [TH_B19, TH_B32], ids=["smoke_B19", "hpc_B32"])
@pytest.mark.parametrize("sphi", [0.003, 0.1, 0.29])
def test_single_random_phase_is_refused_at_the_three_sigma_rate(th, sphi):
    """A3 B1 reproduction 2 (branch_power.py, seed 1, 4000 draws): uniform wrapped phases (no
    height information) resolved 11.6-65.5 % of the time. Required: accepted at most at the rate
    alpha that the 3-sigma criterion implies (count <= the 1 - alpha binomial quantile at alpha)."""
    rng = np.random.default_rng(SEED_SINGLE)
    N = 4000
    kw = dict(s_rad_per_A=_s(th), sigma_s_rad_per_A=_sig_s_common(th), sigma_phi_rad=sphi,
              layer_A=LAYER, n_max=2, n_sigma=3.0)
    resolved = sum(Q.lattice_branch(float(d), **kw)["decision"] == "resolved"
                   for d in rng.uniform(-math.pi, math.pi, N))
    assert resolved <= _binom_quantile(N, ALPHA, 1 - ALPHA), (resolved, N)


def test_three_random_phases_are_refused_at_the_three_sigma_rate():
    """The demo's three steps judged jointly (one common angle calibration), with the smoke
    run's measured phase uncertainties (A3 smoke_run1): uniform random triples must be accepted
    at most at alpha; the analytic chance bound is below alpha and bounds the observed rate."""
    sig = np.array([0.00269, 0.00282, 0.00247])
    kw = dict(s_rad_per_A=_s(TH_B19), sigma_s_rad_per_A=_sig_s_common(TH_B19),
              sigma_phi_rad=sig, layer_A=LAYER, n_max=2, n_sigma=3.0)
    p_bound = Q.chance_probability_bound(sig, s_rad_per_A=kw["s_rad_per_A"],
                                         sigma_s_rad_per_A=kw["sigma_s_rad_per_A"],
                                         layer_A=LAYER, n_max=2, n_sigma=3.0)
    assert p_bound <= ALPHA
    rng = np.random.default_rng(SEED_JOINT)
    N = 20000
    phis = rng.uniform(-math.pi, math.pi, (N, 3))
    resolved = sum(Q.lattice_branch(p, **kw)["decision"] == "resolved" for p in phis)
    assert resolved <= _binom_quantile(N, p_bound, 1 - ALPHA), (resolved, N, p_bound)
    assert resolved <= _binom_quantile(N, ALPHA, 1 - ALPHA)


def test_true_lattice_steps_are_resolved_with_the_implied_power():
    """True a/2 up, a/4 down, a/4 down steps with Gaussian phase noise and ONE common angle error
    eps ~ N(0, sigma_s/s): the right assignment must be accepted with probability >=
    (1 - alpha)^(K+1) (box criterion, K = 3), judged at the lower alpha binomial quantile, and a
    wrong assignment accepted at most at alpha."""
    sig = np.array([0.00269, 0.00282, 0.00247])
    s, sig_s = _s(TH_B19), _sig_s_common(TH_B19)
    n_true = [2, -1, -1]
    rng = np.random.default_rng(SEED_POWER)
    N = 4000
    ok = wrong = 0
    for _ in range(N):
        eps = rng.normal(0.0, sig_s / s)
        phi = [-(s * (1 + eps)) * n * LAYER + rng.normal(0.0, g) for n, g in zip(n_true, sig)]
        phi = [float(np.angle(np.exp(1j * p))) for p in phi]
        br = Q.lattice_branch(phi, s_rad_per_A=s, sigma_s_rad_per_A=sig_s, sigma_phi_rad=sig,
                              layer_A=LAYER, n_max=2, n_sigma=3.0)
        if br["decision"] == "resolved":
            if [a["lattice_n"] for a in br["assignment"]] == n_true:
                ok += 1
            else:
                wrong += 1
    p_min = (1 - ALPHA) ** 4
    assert ok >= _binom_quantile(N, p_min, ALPHA), (ok, N, p_min)
    assert wrong <= _binom_quantile(N, ALPHA, 1 - ALPHA), wrong


# --------------------------------------------------------------------------------------------------
# M3: one common angle-calibration error
# --------------------------------------------------------------------------------------------------
def test_common_angle_error_sensitivity_uncertainty_formula():
    """Derivation: for the specular beam theta_out = theta_in = theta + delta with ONE calibration
    error delta, s = 2 k sin(theta + delta), so ds/d(delta) = 2 k cos(theta) and
    sigma_s = 2 k cos(theta) sigma_theta (plus the common wavelength scale s sigma_lambda/lambda).
    Monte Carlo of the height error with one common delta (seed recorded) must match it."""
    from reflection_holo.quantification.height import sensitivity_uncertainty_rad_per_A
    kw = dict(wavelength_A=LAM, theta_in_ext_rad=TH_B19, theta_out_ext_rad=TH_B19,
              sigma_theta_in_rad=SIG_THETA, sigma_theta_out_rad=SIG_THETA,
              sigma_wavelength_rel=SIG_LAMBDA)
    common = sensitivity_uncertainty_rad_per_A(**kw, angle_errors="common")
    indep = sensitivity_uncertainty_rad_per_A(**kw, angle_errors="independent")
    assert common == pytest.approx(_sig_s_common(TH_B19), rel=1e-12)
    assert indep == pytest.approx(math.hypot(math.sqrt(2) * K_VAC * math.cos(TH_B19) * SIG_THETA,
                                             _s(TH_B19) * SIG_LAMBDA), rel=1e-12)
    rng = np.random.default_rng(SEED_ANGLE)
    N = 20000
    h = 2.71545
    delta = rng.normal(0.0, SIG_THETA, N)
    s_true = 2 * K_VAC * np.sin(TH_B19 + delta)
    h_est = s_true * h / _s(TH_B19)                     # phase -s_true h inverted with nominal s
    ratio = np.std(h_est) / (h * math.hypot(2 * K_VAC * math.cos(TH_B19) * SIG_THETA, 0.0)
                             / _s(TH_B19))
    assert abs(ratio - 1) <= 3 / math.sqrt(2 * N), ratio      # std of a std estimate, 3 sigma


@pytest.fixture(scope="module")
def smoke_summary(tmp_path_factory):
    return run(SMOKE, tmp_path_factory.mktemp("p1") / "smoke")


def test_smoke_sigma_h_uses_the_common_angle_error(smoke_summary):
    """A3 M3: +2.7156 +- 0.0117 A should read +- 0.0165 A; the a/4 steps +- 0.0082 A."""
    s = smoke_summary
    th = s["glancing_angle"]["value_rad"]
    sens = _s(th)
    sig_s = _sig_s_common(th)
    got = {}
    for st in s["quantification"]["steps"]:
        h = st["height"]
        assert h is not None, st.get("reason")
        want = math.hypot(st["sigma_delta_phi_rad"] / sens, h["h_A"] * sig_s / sens)
        assert h["sigma_h_A"] == pytest.approx(want, rel=1e-9)
        assert st["sigma_sensitivity_rad_per_A"] == pytest.approx(sig_s, rel=1e-12)
        got[round(st["built_height_A"], 4)] = round(h["sigma_h_A"], 4)
    assert got == {2.7155: 0.0165, -1.3577: 0.0082}, got


# --------------------------------------------------------------------------------------------------
# M5: the git state is checked before the simulation
# --------------------------------------------------------------------------------------------------
def _no_git(monkeypatch):
    def fake(root=None):
        return dict(commit=None, dirty=None, branch=None, diff_head_sha256=None,
                    untracked_files=None, untracked_sha256=None,
                    error="CalledProcessError: TEST: git rev-parse HEAD failed (no .git)")
    monkeypatch.setattr(MAN, "git_state", fake)


def test_missing_git_is_refused_before_any_computation(tmp_path, monkeypatch):
    """A3 M5: without .git the whole simulation ran, then the manifest refused, leaving arrays.npz
    and quicklooks and no summary. Required: refused before anything is written."""
    _no_git(monkeypatch)
    out = tmp_path / "nogit"
    with pytest.raises(RuntimeError, match="git"):
        run(SMOKE, out)
    assert not out.exists() or not any(out.iterdir()), sorted(p.name for p in out.iterdir())


def test_cli_maps_missing_git_to_exit_6(tmp_path, monkeypatch, capsys):
    _no_git(monkeypatch)
    out = tmp_path / "nogit_cli"
    assert cli_main(["run", "--config", str(SMOKE), "--out", str(out)]) == 6
    assert "before any computation" in capsys.readouterr().err
    assert not out.exists() or not any(out.iterdir())


def test_allow_no_git_records_the_package_tree(tmp_path, monkeypatch):
    _no_git(monkeypatch)
    run(SMOKE, tmp_path / "nogit_allowed", allow_no_git=True)
    m = json.loads((tmp_path / "nogit_allowed" / "manifest.json").read_text())
    assert m["repository"]["allowed_without_git"] is True
    assert "TEST: git rev-parse" in m["repository"]["error"]
    assert len(m["repository"]["package_tree"]["sha256"]) == 64
    assert m["extra"]["git_preflight"]["allowed_without_git"] is True


def test_slurm_submission_refuses_a_tree_without_git(tmp_path):
    """The SLURM runner checks the git state before it submits (A3 M5): a repository copy
    without .git and a fake sbatch; the job must not be submitted."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "venv").symlink_to(REPO / "venv")
    (repo / "configs").symlink_to(REPO / "configs")
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    marker = tmp_path / "submitted"
    (fakebin / "sbatch").write_text(f"#!/bin/bash\necho \"$@\" > {marker}\n")
    (fakebin / "sbatch").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RH_", "SLURM_"))}
    env.update(PATH=f"{fakebin}:{env['PATH']}", RH_ACCOUNT="a", RH_PARTITION="p",
               RH_TIME_LIMIT="00:10:00", RH_GPU="none", RH_MODE="smoke", RH_REPO=str(repo),
               GIT_CEILING_DIRECTORIES=str(tmp_path))
    r = subprocess.run(["bash", str(REPO / "scripts" / "hpc" / "run_pipeline.slurm")], cwd=repo,
                       env=env, capture_output=True, text=True, timeout=300)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "git" in r.stderr and not marker.exists(), r.stderr
