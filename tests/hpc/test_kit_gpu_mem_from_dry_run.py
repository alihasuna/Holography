"""kit.py `--gpu-mem-from-dry-run PATH --gpu-mem-margin F` (E1 wave 2a; H7 sections 1 and 4): the GPU
memory need of a pipeline job is taken from the dry run's `device_peak_cupy` (engine.memory_model,
a lower bound) times (1 + F), with F REQUIRED (no default); the derivation is printed (NOTE lines)
and recorded in the submission record; the host memory of the GPU run is the model's cupy host
peak plus 48 B/atom of builder structure (192 B/atom in total) and is compared with --mem;
`--need-gpu-mem-gb` stays the explicit override. The dry-run report must be the one of the
configuration and variant being submitted (SHA-256). The pipeline writes that report with
`dry-run --report-json` and the kit's dry-run job asks for it.
X2 (audit A6 K-1, K-2): the report (schema /2) carries the engine code's SHA-256 and the kit refuses
a report of other engine code; an explicit --need-gpu-mem-gb BELOW the derived need is refused
unless --accept-need-below-dry-run is given (recorded). E1's assertion that 30 GB against a derived
50 GB is accepted therefore now holds only with that flag (intentional change).

Fake login node and Slurm from test_alliance_kit (nothing touches a cluster, no GPU)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from test_alliance_kit import (REPO, Kit, _jobdirs, _run_emulated, export_vars,  # noqa: F401
                               sbatch_argv)

CFG = "configs/demo_hpc_si001.yaml"                  # a cupy multislice configuration
A = ["--account", "def-testpi", "--time", "01:00:00"]


def _engine_sha():
    sys.path.insert(0, str(REPO / "scripts" / "hpc" / "alliance"))
    import kit
    return kit.engine_code_sha256(REPO)["sha256"]


def _report(path: Path, *, dev=25e9, host=3.0e9, n_atoms=10_000_000, config=CFG, variant=None,
            backend="cupy", schema="reflholo_pipeline_dry_run_report/2", multislice=True,
            engine_sha="current"):
    cpath = (REPO / config).resolve()
    rep = dict(engine="multislice", backend=dict(name=backend, available=False, status="no GPU"))
    if multislice:
        rep["multislice"] = dict(grid=dict(nx=2250, ny=12096), n_atoms=n_atoms,
                                 precision="complex64",
                                 memory_bytes=dict(total=int(dev * 1.5), device_peak_cupy=int(dev),
                                                   host_peak_cupy=int(host)))
    d = dict(schema=schema, config_path=str(cpath),
             config_sha256=hashlib.sha256(cpath.read_bytes()).hexdigest(), variant=variant,
             report=rep)
    if engine_sha is not None:
        d["engine_code"] = dict(sha256=_engine_sha() if engine_sha == "current" else engine_sha)
    path.write_text(json.dumps(d))
    return path


def test_derived_need_is_printed_and_selects_the_refusal(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    kit.gpu_pass()
    rep = _report(tmp_path / "dry_run_report.json")
    base = ["pipeline", *A, "--config", CFG, "--gpu-instance", "3g.40gb", "--cpus", "8",
            "--gpu-mem-from-dry-run", str(rep)]
    r = kit.submit(*base, "--gpu-mem-margin", "0.5")          # 25 GB x 1.5 = 37.5 GB <= 40 GB
    assert r.returncode == 0, r.stderr
    for s in ("device peak of the cupy backend", "LOWER BOUND", "= 25.000 GB",
              "x (1 + margin 0.5, stated with --gpu-mem-margin) = 37.500 GB",
              "GPU memory needed: 37.500 GB, derived from the dry run", "192 B/atom"):
        assert s in r.stderr, (s, r.stderr)
    r = kit.submit(*base, "--gpu-mem-margin", "1.0")          # 50 GB > 40 GB: refused
    assert r.returncode == 2 and "40 GB of GPU memory < the 50.000 GB you need (derived from the " \
                                 "dry run" in r.stderr, r.stderr
    r = kit.submit(*base, "--gpu-mem-margin", "1.0", "--gpu-instance", "full")
    assert r.returncode == 0, r.stderr                         # 80 GB instance


def test_margin_is_required_and_explicit_need_overrides(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    kit.gpu_pass()
    rep = _report(tmp_path / "dry_run_report.json")
    base = ["pipeline", *A, "--config", CFG, "--gpu-instance", "3g.40gb", "--cpus", "8"]
    r = kit.submit(*base, "--gpu-mem-from-dry-run", str(rep))
    assert r.returncode == 2 and "--gpu-mem-margin is required" in r.stderr
    r = kit.submit(*base, "--gpu-mem-margin", "0.5")
    assert r.returncode == 2 and "applies with --gpu-mem-from-dry-run only" in r.stderr
    r = kit.submit(*base, "--gpu-mem-from-dry-run", str(rep), "--gpu-mem-margin", "-0.1")
    assert r.returncode == 2 and "must be a fraction >= 0" in r.stderr
    below = [*base, "--gpu-mem-from-dry-run", str(rep), "--gpu-mem-margin", "1.0",
             "--need-gpu-mem-gb", "30"]                       # 30 GB < the derived 50 GB
    r = kit.submit(*below)                                    # A6 K-2: refused without the flag
    assert r.returncode == 2 and "--need-gpu-mem-gb 30 is below the 50.000 GB derived from the " \
                                 "dry run" in r.stderr and "--accept-need-below-dry-run" in r.stderr
    r = kit.submit(*below, "--accept-need-below-dry-run")
    assert r.returncode == 0, r.stderr
    assert "--need-gpu-mem-gb 30 given explicitly: it overrides the 50.000 GB derived" in r.stderr
    assert "WARNING: --need-gpu-mem-gb 30 is BELOW the 50.000 GB derived" in r.stderr
    r = kit.submit(*base, "--gpu-mem-from-dry-run", str(rep), "--gpu-mem-margin", "0.5",
                   "--need-gpu-mem-gb", "39")                # above the derived 37.5 GB: no flag
    assert r.returncode == 0 and "overrides the 37.500 GB derived" in r.stderr, r.stderr
    assert "BELOW" not in r.stderr
    r = kit.submit(*base, "--need-gpu-mem-gb", "45")           # the override alone, as before
    assert r.returncode == 2 and "< the 45.0 GB you need (" in r.stderr
    for extra in (["--need-gpu-mem-gb", "30"],
                  ["--gpu-mem-from-dry-run", str(rep), "--gpu-mem-margin", "1.0"]):
        r = kit.submit(*base, *extra, "--accept-need-below-dry-run")
        assert r.returncode == 2 and "applies only with both" in r.stderr, r.stderr


def test_accepted_override_below_the_derived_need_is_recorded(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    kit.gpu_pass()
    rep = _report(tmp_path / "dry_run_report.json")
    r = kit.submit("pipeline", *A, "--config", CFG, "--gpu-instance", "3g.40gb", "--cpus", "8",
                   "--gpu-mem-from-dry-run", str(rep), "--gpu-mem-margin", "1.0",
                   "--need-gpu-mem-gb", "30", "--accept-need-below-dry-run", "--mem", "16G",
                   dry=False)
    assert r.returncode == 0, r.stderr
    sent = (kit.root / "sbatch_args.txt").read_text().splitlines()
    plan = json.loads(Path(export_vars(["sbatch"] + sent)["RH_SUBMISSION_RECORD"]).read_text())
    g = plan["gpu_memory_need"]
    assert g["explicit_need_gb"] == 30.0 and abs(g["need_gb"] - 50.0) < 1e-9
    assert g["explicit_below_derived"] is True and g["accept_need_below_dry_run"] is True
    assert g["used"] == "overridden by --need-gpu-mem-gb 30"


def test_report_must_belong_to_this_configuration(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    kit.gpu_pass()
    base = ["pipeline", *A, "--config", CFG, "--cpus", "16", "--gpu-mem-margin", "0.5",
            "--gpu-mem-from-dry-run"]
    other = _report(tmp_path / "other.json", config="configs/demo_smoke_si001.yaml")
    r = kit.submit(*base, str(other))
    assert r.returncode == 2 and "was made for configuration" in r.stderr
    r = kit.submit(*base, str(_report(tmp_path / "v.json", variant="multislice_tiny")))
    assert r.returncode == 2 and "was made for variant" in r.stderr
    r = kit.submit(*base, str(_report(tmp_path / "s.json", schema="something/1")))
    assert r.returncode == 2 and "schema" in r.stderr
    r = kit.submit(*base, str(_report(tmp_path / "old.json",               # E1's schema: refused
                                      schema="reflholo_pipeline_dry_run_report/1")))
    assert r.returncode == 2 and "schema" in r.stderr
    # A6 K-1: a report made with other engine code, or without the engine code's hash, is refused
    r = kit.submit(*base, str(_report(tmp_path / "e.json", engine_sha="0" * 64)))
    assert r.returncode == 2 and "was made with engine code 000000000000" in r.stderr, r.stderr
    r = kit.submit(*base, str(_report(tmp_path / "e0.json", engine_sha=None)))
    assert r.returncode == 2 and "was made with engine code None" in r.stderr, r.stderr
    r = kit.submit(*base, str(_report(tmp_path / "n.json", backend="numpy")))
    assert r.returncode == 2 and "cupy run only" in r.stderr
    r = kit.submit(*base, str(_report(tmp_path / "g.json", multislice=False)))
    assert r.returncode == 2 and "no multislice estimate" in r.stderr
    r = kit.submit(*base, str(tmp_path / "missing.json"))
    assert r.returncode == 2 and "file not found" in r.stderr
    d = tmp_path / "jobdir" / "dry_run"                       # the dry-run job's directory layout
    d.mkdir(parents=True)
    _report(d / "dry_run_report.json")
    r = kit.submit(*base, str(tmp_path / "jobdir"))
    assert r.returncode == 0, r.stderr


def test_not_for_cpu_jobs_and_other_jobs(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    kit.gpu_pass()
    rep = _report(tmp_path / "dry_run_report.json")
    opt = ["--gpu-mem-from-dry-run", str(rep), "--gpu-mem-margin", "0.5"]
    r = kit.submit("smoke", *A, "--mem", "4G", *opt)
    assert r.returncode == 2 and "applies to a pipeline job of a cupy configuration" in r.stderr
    r = kit.submit("gpu-check", *A, *opt)
    assert r.returncode == 2 and "applies to a pipeline job of a cupy configuration" in r.stderr


def test_host_memory_is_compared_with_mem_and_recorded(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    kit.gpu_pass()
    rep = _report(tmp_path / "dry_run_report.json", host=3.0e9, n_atoms=100_000_000)
    base = ["pipeline", *A, "--config", CFG, "--gpu-instance", "3g.40gb", "--cpus", "8",
            "--gpu-mem-from-dry-run", str(rep), "--gpu-mem-margin", "0.5"]
    need = 3.0e9 + 48 * 100_000_000                           # 7.8e9 B = 7.26 GiB
    r = kit.submit(*base, "--mem", "4G")
    assert r.returncode == 0 and "--mem 4G is below the host memory derived from the dry run " \
                                 f"({need / 2**30:.2f} GiB" in r.stderr, r.stderr
    r = kit.submit(*base, "--mem", "16G", dry=False)
    assert r.returncode == 0 and "is below the host memory" not in r.stderr, r.stderr
    sent = (kit.root / "sbatch_args.txt").read_text().splitlines()
    plan = json.loads(Path(export_vars(["sbatch"] + sent)["RH_SUBMISSION_RECORD"]).read_text())
    g = plan["gpu_memory_need"]
    assert g["device_peak_cupy_B"] == 25_000_000_000 and g["margin"] == 0.5
    assert abs(g["need_gb"] - 37.5) < 1e-9 and g["used"].startswith("derived")
    assert g["host_need_B"] == need and g["host_mem_requested_B"] == 16 * 2**30
    assert g["source_sha256"] == hashlib.sha256(rep.read_bytes()).hexdigest()
    assert g["engine_code_sha256"] == _engine_sha()


def test_pipeline_dry_run_writes_the_report_json(tmp_path):
    out = tmp_path / "rep.json"
    p = subprocess.run([sys.executable, "-m", "reflection_holo.pipeline", "dry-run", "--config",
                        "configs/demo_smoke_si001.yaml", "--variant", "multislice_tiny",
                        "--report-json", str(out)], cwd=REPO, capture_output=True, text=True,
                       timeout=900)
    assert p.returncode in (0, 4), p.stdout[-2000:] + p.stderr[-2000:]
    d = json.loads(out.read_text())
    cfg = (REPO / "configs" / "demo_smoke_si001.yaml").resolve()
    # schema /1 -> /2 (X2, A6 K-1: intentional change): the report carries the engine code's hash,
    # computed by the pipeline exactly as the kit computes it
    assert d["schema"] == "reflholo_pipeline_dry_run_report/2" and d["variant"] == "multislice_tiny"
    assert d["config_sha256"] == hashlib.sha256(cfg.read_bytes()).hexdigest()
    assert d["engine_code"]["sha256"] == _engine_sha()
    mb = d["report"]["multislice"]["memory_bytes"]
    assert int(mb["device_peak_cupy"]) > 0 and int(mb["host_peak_cupy"]) > 0
    assert int(d["report"]["multislice"]["n_atoms"]) > 0


def test_emulated_dry_run_job_writes_the_report(tmp_path):
    kit = Kit(tmp_path, "fir")
    r = _run_emulated(kit, "dry-run", "--account", "def-testpi", "--time", "00:30:00", "--config",
                      "configs/demo_smoke_si001.yaml", "--mem", "2G")
    assert r.returncode == 0, (r.stdout, r.stderr)
    (jd,) = _jobdirs(kit, "dry-run_900001_*")
    d = json.loads((jd / "dry_run" / "dry_run_report.json").read_text())
    assert d["schema"] == "reflholo_pipeline_dry_run_report/2"          # X2 (A6 K-1)
    assert d["engine_code"]["sha256"] == _engine_sha()
    res = json.loads((jd / "dry_run" / "dry_run_resources.json").read_text())
    assert res["report_json"].endswith("dry_run_report.json")
