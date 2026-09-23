"""Regression tests of the priority-3 fixes (audit A3 minors m1, m3-m8; report
docs/agent_reports/S4_pipeline_fixes.md). m2 (list-inputs shows the engine's V0) is tested in
test_a3_priority2.py::test_list_inputs_marks_unused_inputs_and_shows_the_engine_v0.
"""
import importlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from reflection_holo.pipeline import run
from reflection_holo.pipeline.__main__ import main as cli_main

from conftest_pipeline import HPC, REPO, SMOKE

R = importlib.import_module("reflection_holo.pipeline.run")
ENG = importlib.import_module("reflection_holo.pipeline.engines")


def _ms_ok():
    ok, _ = ENG.multislice_status()
    return ok


def _cupy_usable():
    f = getattr(ENG, "backend_status", None)
    if f is not None:
        return f("cupy")[0]
    try:
        import cupy  # noqa: F401
        return True
    except ImportError:
        return False


# --------------------------------------------------------------------------------------------------
# m1: purpose in arrays.npz and in the engine manifest
# --------------------------------------------------------------------------------------------------
def test_arrays_npz_carries_the_purpose(tmp_path):
    s = run(SMOKE, tmp_path / "m1")
    a = np.load(tmp_path / "m1" / "arrays.npz")
    assert str(a["purpose"]) == "demo; not comparable to experiment"
    assert s["arrays"]["purpose"]["units"].startswith("text")


@pytest.fixture(scope="module")
def ms_tiny(tmp_path_factory):
    if not _ms_ok():
        pytest.skip("multislice engine unavailable")
    out = tmp_path_factory.mktemp("p3") / "ms_tiny"
    return out, run(SMOKE, out, variant="multislice_tiny")


def test_engine_manifest_carries_the_purpose_and_the_config(ms_tiny):
    """m1: the engine's own manifest said 'no configuration file (stated explicitly by the caller)',
    inputs [], and carried no purpose."""
    out, _ = ms_tiny
    mans = sorted((out / "outputs" / "manifests").glob("*.json"))
    assert len(mans) == 1
    m = json.loads(mans[0].read_text())
    assert m["extra"]["caller"]["purpose"] == "demo; not comparable to experiment"
    assert m["config"]["path"] == str(SMOKE)
    assert [i["path"] for i in m["inputs"]] == [str(SMOKE)]


# --------------------------------------------------------------------------------------------------
# m3: the empty-object amplitude comes from lit terrace-top pixels only
# --------------------------------------------------------------------------------------------------
def test_empty_object_amplitude_uses_lit_pixels_only(ms_tiny):
    """m3: in the tiny multislice run the below-surface pixels (|obj| mean 0.094) were brighter than
    the lit ones (0.069) and entered A_emp."""
    out, s = ms_tiny
    a = np.load(out / "arrays.npz")
    amp = np.abs(a["detector_object_r0"])
    lit = a["trace_status"] == 0
    bright = lit & (amp >= 0.5 * amp[lit].max())
    assert s["detector"]["empty_object_amplitude"] == pytest.approx(
        float(np.sqrt(np.mean(amp[bright] ** 2))), rel=1e-12)
    by = s["detector"]["object_amplitude_by_trace_status"]
    assert by["lit"]["n_px"] == int(lit.sum())


# --------------------------------------------------------------------------------------------------
# m4: the +-a/2 sign degeneracy at the B32 angle is stated in the summary
# --------------------------------------------------------------------------------------------------
def test_sign_degeneracy_note_at_the_b32_angle():
    """m4: at 16.1347 mrad +a/2 and -a/2 differ by 0.078 rad of wrapped phase; one a/2 step alone
    cannot be resolved. At the smoke angle (B19) the separation is 0.846 rad."""
    from reflection_holo.geometry.wavelength import wavelength_A
    lam = wavelength_A(200.0)
    L = 5.4309 / 4
    out = {}
    for th in (16.13472004381e-3, 16.47433279927e-3):
        s = 4 * math.pi * math.sin(th) / lam
        sig_s = math.hypot(2 * (2 * math.pi / lam) * math.cos(th) * 1e-4, s * 1e-5)
        steps = [dict(measured=True, sensitivity_rad_per_A=s, sigma_sensitivity_rad_per_A=sig_s,
                      sigma_delta_phi_rad=0.003)]
        out[th] = R._sign_degeneracy(steps, lam=lam, theta=th, layer_A=L, n_max=2, n_sigma=3.0)
    b32 = {p["n"]: p for p in out[16.13472004381e-3]["pairs"]}
    assert b32[2]["wrapped_separation_rad"] == pytest.approx(0.0779, abs=1e-4)
    assert b32[2]["degenerate_single_step"] and "cannot be decided" in out[16.13472004381e-3]["note"]
    b19 = {p["n"]: p for p in out[16.47433279927e-3]["pairs"]}
    assert b19[2]["wrapped_separation_rad"] == pytest.approx(0.846, abs=1e-3)
    assert not any(p["degenerate_single_step"] for p in b19.values())


def test_smoke_summary_carries_the_sign_degeneracy_note(tmp_path):
    s = run(SMOKE, tmp_path / "m4")
    assert "separated" in s["quantification"]["sign_degeneracy"]["note"]


# --------------------------------------------------------------------------------------------------
# m5: cupy is checked when a cupy variant is requested
# --------------------------------------------------------------------------------------------------
needs_no_cupy = pytest.mark.skipif(_cupy_usable() or not _ms_ok(),
                                   reason="cupy is usable here (or the multislice engine is "
                                          "unavailable): the refusal cannot be exercised")


@needs_no_cupy
def test_cupy_run_is_refused_before_any_computation(tmp_path):
    """m5: without cupy the HPC run built the 1.44M-atom structure and failed late with an uncaught
    ImportError; the dry run exited 0 reporting multislice_available true."""
    out = tmp_path / "cupy"
    with pytest.raises(ENG.EngineUnavailableError, match="cupy"):
        run(HPC, out)
    assert not out.exists() or not any(out.iterdir())


@needs_no_cupy
def test_cli_cupy_run_exits_4(tmp_path, capsys):
    assert cli_main(["run", "--config", str(HPC), "--out", str(tmp_path / "c")]) == 4
    assert "cupy" in capsys.readouterr().err


# --------------------------------------------------------------------------------------------------
# m6: SLURM runner robustness
# --------------------------------------------------------------------------------------------------
def _slurm_env(tmp_path, **extra):
    fakebin = tmp_path / "bin"
    fakebin.mkdir(exist_ok=True)
    marker = tmp_path / "sbatch_args"
    (fakebin / "sbatch").write_text(f"#!/bin/bash\necho \"$@\" > {marker}\n")
    (fakebin / "sbatch").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RH_", "SLURM_"))}
    env.update(PATH=f"{fakebin}:{env['PATH']}", RH_ACCOUNT="a", RH_PARTITION="p",
               RH_TIME_LIMIT="00:10:00", RH_GPU="none", RH_MODE="smoke", RH_REPO=str(REPO))
    env.update(extra)
    return env, marker


def test_slurm_submission_from_another_directory(tmp_path):
    """m6: a job submitted from outside the repository failed with FileNotFoundError on
    'configs/demo_smoke_si001.yaml' (the config check ran before cd "$REPO")."""
    env, marker = _slurm_env(tmp_path)
    r = subprocess.run(["bash", str(REPO / "scripts" / "hpc" / "run_pipeline.slurm")],
                       cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, (r.stdout, r.stderr)
    args = marker.read_text()
    assert "--cpus-per-task=8" in args and str(REPO / "scripts" / "hpc" / "run_pipeline.slurm") in args


def test_slurm_job_uses_slurm_cpus_per_task(tmp_path):
    """m6: RH_CPUS defaulted to 8 whatever --cpus-per-task a direct sbatch gave; with 2 CPUs and
    runtime.threads 4 the job must refuse (exit 2) before running."""
    env, _ = _slurm_env(tmp_path, SLURM_JOB_ID="4242", SLURM_CPUS_PER_TASK="2",
                        RH_OUT=str(tmp_path / "job_out"))
    r = subprocess.run(["bash", str(REPO / "scripts" / "hpc" / "run_pipeline.slurm")],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
    assert r.returncode == 2, (r.returncode, r.stdout[-2000:], r.stderr[-2000:])
    assert "cpus-per-task 2 < runtime.threads 4" in r.stderr
    assert not (tmp_path / "job_out").exists()


# --------------------------------------------------------------------------------------------------
# m7: the null-test study runner
# --------------------------------------------------------------------------------------------------
def _study():
    sys.path.insert(0, str(REPO / "scripts" / "hpc" / "null_test_study"))
    try:
        return importlib.import_module("run_study")
    finally:
        sys.path.pop(0)


def test_study_refuses_duplicate_yaml_keys(tmp_path):
    rs = _study()
    cfg = tmp_path / "dup.yaml"
    cfg.write_text("runtime: {threads: 1}\nruntime: {threads: 2}\npoints: []\n")
    from reflection_holo.io.config import ConfigError
    with pytest.raises(ConfigError, match="duplicate key"):
        rs.main(["--config", str(cfg), "--out", str(tmp_path / "o"), "--estimate"])


def test_study_never_overwrites_a_result(tmp_path, monkeypatch):
    """m7: results were written with write_text (overwrite). Now an existing result stops the point
    BEFORE any computation (the build step must not be reached)."""
    rs = _study()
    study = REPO / "scripts" / "hpc" / "null_test_study" / "study.yaml"
    from reflection_holo.io.config import load_yaml_unique
    first = load_yaml_unique(study.read_bytes())["points"][0]["name"]
    res = tmp_path / "o" / "outputs" / "null_test_study" / f"{first}.json"
    res.parent.mkdir(parents=True)
    res.write_text("{}")

    def reached(*a, **k):
        raise AssertionError("computation started although the result exists")
    monkeypatch.setattr(rs, "_build", reached)
    with pytest.raises(SystemExit, match="never overwritten"):
        rs.main(["--config", str(study), "--out", str(tmp_path / "o"), "--only", first])
    assert res.read_text() == "{}"


# --------------------------------------------------------------------------------------------------
# m8: refusals map to exit codes; a closed pipe is not an error
# --------------------------------------------------------------------------------------------------
def test_cli_maps_the_b4_refusal_to_exit_3(tmp_path, monkeypatch, capsys):
    from reflection_holo.forward.geometric import OutsideB4ScopeError

    def refuse(*a, **k):
        raise OutsideB4ScopeError("TEST: a/4 step outside the B4 scope")
    monkeypatch.setattr(R, "run", refuse)
    assert cli_main(["run", "--config", str(SMOKE), "--out", str(tmp_path / "b4")]) == 3
    assert "B4" in capsys.readouterr().err


def test_cli_survives_a_closed_pipe(tmp_path):
    """M4/m8: with PYTHONUNBUFFERED=1 a reader that closes the pipe early made the command die with
    BrokenPipeError (status 1). The read end is closed before the command writes (deterministic)."""
    r_fd, w_fd = os.pipe()
    os.close(r_fd)
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    try:
        p = subprocess.run([sys.executable, "-m", "reflection_holo.pipeline", "list-inputs",
                            "--config", str(SMOKE)], stdout=w_fd, stderr=subprocess.PIPE,
                           env=env, cwd=REPO, timeout=300)
    finally:
        os.close(w_fd)
    assert p.returncode == 0, p.stderr.decode()[-2000:]
