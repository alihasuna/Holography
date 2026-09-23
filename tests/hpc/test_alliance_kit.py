"""Tests of the Alliance kit (scripts/hpc/alliance/): the sbatch command that submit.sh builds for
every cluster and job (fake sbatch and module on PATH, --dry-run), the refusals (no account, no
time, limits, GPU gate, CPU jobs on Trillium), setup_alliance.sh without the module command, the
cluster profiles against H1's table, emulated batch jobs (smoke, null-study array task, gpu-check
without a GPU) end to end with a fake Slurm, and collect_results.sh.

Nothing here touches a real cluster; the GPU path itself is NOT exercised (no GPU here)."""
from __future__ import annotations

import csv
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fake_slurm import MODULES, clean_environ, make_env_dir, make_fakebin  # noqa: E402

REPO = HERE.parents[1]
KIT = REPO / "scripts" / "hpc" / "alliance"
SUBMIT = KIT / "submit.sh"
JOB_SCRIPT = KIT / "job.sbatch"
CLUSTERS = ("fir", "nibi", "rorqual", "narval", "trillium")
JOBS = ("gpu-check", "smoke", "demo-gpu", "pipeline", "torus", "null-study")
GPU_FLAGS = {"fir": ["--gpus=h100:1"], "nibi": ["--gpus=h100:1"], "rorqual": ["--gpus=h100:1"],
             "narval": ["--gpus=a100:1"], "trillium": ["--nodes=1", "--gpus-per-node=1"]}
RECOMMENDED = {"fir": ("12", "280G"), "nibi": ("14", "250G"), "rorqual": ("16", "124G"),
               "narval": ("12", "124G")}
N_STUDY_POINTS = 17


def _yaml(path):
    from reflection_holo.io.config import load_yaml_unique
    return load_yaml_unique(Path(path).read_bytes())


class Kit:
    """A fake login node: fake module and sbatch on PATH, an environment record, a scratch."""

    def __init__(self, root: Path, cluster: str):
        self.root = root
        self.cluster = cluster
        self.bin = make_fakebin(root)
        self.env_dir = make_env_dir(root, cluster)
        self.env_id = json.loads((self.env_dir / "env.json").read_text())["env_id"]
        self.scratch = root / "scratch"
        self.scratch.mkdir(exist_ok=True)
        self.run_root = self.scratch.resolve() / "reflholo"

    def environ(self, **extra):
        return clean_environ(PATH=f"{self.bin}:{os.environ['PATH']}", SCRATCH=str(self.scratch),
                             RH_ALLIANCE_ENV_DIR=str(self.env_dir), **extra)

    def gpu_pass(self):
        d = self.run_root / "gpu_check"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"PASS_{self.cluster}_{self.env_id}_1.json").write_text("{}")

    def submit(self, job, *args, dry=True, env=None, timeout=600):
        cmd = ["bash", str(SUBMIT), self.cluster, job, *args] + (["--dry-run"] if dry else [])
        return subprocess.run(cmd, cwd=self.root, env=env or self.environ(), capture_output=True,
                              text=True, timeout=timeout)


def sbatch_argv(stdout: str) -> list[str]:
    lines = stdout.splitlines()
    i = lines.index("sbatch command:")
    return shlex.split(lines[i + 1])


def export_vars(argv) -> dict:
    exp = [a for a in argv if a.startswith("--export=")]
    assert len(exp) == 1
    items = exp[0][len("--export="):].split(",")
    assert items[0] == "ALL"
    return dict(i.split("=", 1) for i in items[1:])


def job_args(cluster, job, tmp_path):
    """Minimal complete argument list of each job (a CPU job needs --mem)."""
    base = ["--account", "def-testpi", "--time", "01:00:00"]
    if job in ("smoke", "torus"):
        base += ["--mem", "4G"]
    if job == "pipeline":
        base += ["--config", "configs/demo_hpc_si001.yaml"]
    return base


# --------------------------------------------------------------------------------------------------
# dry runs: every cluster x every job
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("cluster", CLUSTERS)
@pytest.mark.parametrize("job", JOBS)
def test_dry_run_command_every_cluster_and_job(tmp_path, cluster, job):
    kit = Kit(tmp_path, cluster)
    kit.gpu_pass()
    r = kit.submit(job, *job_args(cluster, job, tmp_path))
    cpu_job = job in ("smoke", "torus")
    if cluster == "trillium" and cpu_job:
        assert r.returncode == 2, (r.stdout, r.stderr)
        assert "192-core" in r.stderr and "sbatch command" not in r.stdout
        return
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "DRY RUN: nothing submitted" in r.stdout
    assert not (kit.root / "sbatch_args.txt").exists(), "dry run called sbatch"
    assert not (kit.run_root / "logs").exists(), "dry run created directories"
    argv = sbatch_argv(r.stdout)
    assert argv[0] == "sbatch" and argv[-1] == str(JOB_SCRIPT)
    assert "--account=def-testpi" in argv and "--time=01:00:00" in argv
    assert not any(a.startswith(("--partition", "-p", "--gres")) for a in argv)
    # outputs and log under $SCRATCH, job-id stamped
    out = [a for a in argv if a.startswith("--output=")][0]
    assert out.startswith(f"--output={kit.run_root}/logs/{job}_")
    assert f"--chdir={kit.run_root}" in argv
    ex = export_vars(argv)
    assert ex["RH_RUN_ROOT"] == str(kit.run_root) and ex["RH_KIT_JOB"] == job
    assert ex["RH_KIT_CLUSTER"] == cluster and ex["RH_ACCOUNT"] == "def-testpi"
    assert len(ex["RH_SUBMIT_COMMIT"]) == 40
    if job == "null-study":
        assert "--array=0-16" in argv and out.endswith(f"{job}_%A_%a.log")
        assert ex["RH_STUDY_MODE"] == "array" and ex["RH_STUDY_N"] == str(N_STUDY_POINTS)
    else:
        assert not any(a.startswith("--array") for a in argv) and out.endswith(f"{job}_%j.log")
    if cpu_job:
        assert ex["RH_KIT_GPU"] == "none"
        assert "--cpus-per-task=4" in argv and "--mem=4G" in argv
        assert not any(a.startswith(("--gpus", "--gpus-per-node")) for a in argv)
        return
    # GPU jobs: the GPU model is named in the request (mandatory on Fir, Nibi, Rorqual)
    for flag in GPU_FLAGS[cluster]:
        assert flag in argv, (cluster, argv)
    if cluster == "trillium":
        assert not any(a.startswith(("--mem", "--cpus-per-task")) for a in argv)
    else:
        cpus, mem = RECOMMENDED[cluster]
        assert f"--cpus-per-task={cpus}" in argv and f"--mem={mem}" in argv
    assert ex["RH_KIT_GPU"] == "full"


def test_null_study_array_range_is_read_from_the_study_file(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    kit.gpu_pass()
    study = _yaml(REPO / "scripts" / "hpc" / "null_test_study" / "study.yaml")
    assert len(study["points"]) == N_STUDY_POINTS
    r = kit.submit("null-study", "--account", "rrg-testpi-ab", "--time", "02:00:00",
                   "--array-throttle", "4")
    assert r.returncode == 0, r.stderr
    assert "--array=0-16%4" in sbatch_argv(r.stdout)
    r = kit.submit("null-study", "--account", "rrg-testpi-ab", "--time", "02:00:00", "--serial")
    argv = sbatch_argv(r.stdout)
    assert not any(a.startswith("--array") for a in argv)
    assert export_vars(argv)["RH_STUDY_MODE"] == "serial"
    r = kit.submit("null-study", "--account", "rrg-testpi-ab", "--time", "02:00:00", "--only",
                   "no_such_point")
    assert r.returncode == 2 and "not a point" in r.stderr


# --------------------------------------------------------------------------------------------------
# required inputs and refusals
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("dry", [True, False])
def test_account_is_required(tmp_path, dry):
    kit = Kit(tmp_path, "fir")
    r = kit.submit("smoke", "--time", "01:00:00", "--mem", "4G", dry=dry)
    assert r.returncode == 2 and "--account is required" in r.stderr, r.stderr
    assert not (kit.root / "sbatch_args.txt").exists()


@pytest.mark.parametrize("dry", [True, False])
def test_time_is_required_and_never_defaulted(tmp_path, dry):
    kit = Kit(tmp_path, "narval")
    r = kit.submit("smoke", "--account", "def-testpi", "--mem", "4G", dry=dry)
    assert r.returncode == 2 and "--time is required" in r.stderr, r.stderr
    assert "--time=" not in r.stdout
    assert not (kit.root / "sbatch_args.txt").exists()


def test_account_prefix_checked(tmp_path):
    kit = Kit(tmp_path, "fir")
    r = kit.submit("smoke", "--account", "someone", "--time", "01:00:00", "--mem", "4G")
    assert r.returncode == 2 and "def-" in r.stderr
    r = kit.submit("smoke", "--account", "someone", "--time", "01:00:00", "--mem", "4G",
                   "--any-account-prefix")
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("cluster,time,why", [
    ("trillium", "25:00:00", "maximum of 24 h"),
    ("trillium", "00:10:00", "minimum of 15 min"),
    ("fir", "8-00:00:00", "maximum of 168 h"),
    ("rorqual", "3", "minimum of 5 min"),
    ("nibi", "01:00", None),          # minutes:seconds = 1 min; Nibi states no test minimum
])
def test_time_limits(tmp_path, cluster, time, why):
    kit = Kit(tmp_path, cluster)
    kit.gpu_pass()
    r = kit.submit("gpu-check", "--account", "def-testpi", "--time", time)
    if cluster == "nibi":
        # Nibi states no test-job minimum (NOT_FOUND): accepted with the production warning
        assert r.returncode == 0 and "production jobs should last at least 60 min" in r.stderr
        return
    assert r.returncode == 2 and why in r.stderr, r.stderr


def test_bad_time_format_refused(tmp_path):
    kit = Kit(tmp_path, "fir")
    r = kit.submit("gpu-check", "--account", "def-testpi", "--time", "1h")
    assert r.returncode == 2 and "not a Slurm time" in r.stderr


def test_cpu_job_needs_memory(tmp_path):
    kit = Kit(tmp_path, "fir")
    r = kit.submit("torus", "--account", "def-testpi", "--time", "01:00:00")
    assert r.returncode == 2 and "--mem is required" in r.stderr and "1.3" in r.stderr


def test_gpu_gate_requires_a_gpu_check_pass(tmp_path):
    kit = Kit(tmp_path, "fir")
    r = kit.submit("demo-gpu", "--account", "def-testpi", "--time", "01:00:00")
    assert r.returncode == 2 and "gpu-check" in r.stderr
    r = kit.submit("gpu-check", "--account", "def-testpi", "--time", "00:10:00")
    assert r.returncode == 0, r.stderr                  # gpu-check itself is never gated
    r = kit.submit("demo-gpu", "--account", "def-testpi", "--time", "01:00:00",
                   "--skip-gpu-check-gate")
    assert r.returncode == 0 and "UNVERIFIED" in r.stderr
    # a PASS of another environment does not count
    other = kit.run_root / "gpu_check"
    other.mkdir(parents=True)
    (other / "PASS_fir_fir-other-env_7.json").write_text("{}")
    r = kit.submit("demo-gpu", "--account", "def-testpi", "--time", "01:00:00")
    assert r.returncode == 2
    kit.gpu_pass()
    assert kit.submit("demo-gpu", "--account", "def-testpi", "--time", "01:00:00").returncode == 0


def test_mig_instances_and_gpu_memory(tmp_path):
    kit = Kit(tmp_path, "fir")
    kit.gpu_pass()
    a = ["--account", "def-testpi", "--time", "01:00:00"]
    r = kit.submit("demo-gpu", *a, "--gpu-instance", "3g.40gb")
    assert r.returncode == 2 and "cpus-per-task 6 < the 8 threads" in r.stderr, r.stderr
    r = kit.submit("demo-gpu", *a, "--gpu-instance", "3g.40gb", "--cpus", "8")
    assert r.returncode == 0, r.stderr
    argv = sbatch_argv(r.stdout)
    assert "--gpus=nvidia_h100_80gb_hbm3_3g.40gb:1" in argv and "--mem=140G" in argv
    assert "--cpus-per-task=8" in argv and "exceeds the recommended 6" in r.stderr
    r = kit.submit("gpu-check", *a, "--gpu-instance", "1g.10gb")
    assert r.returncode == 0 and "--gpus=nvidia_h100_80gb_hbm3_1g.10gb:1" in sbatch_argv(r.stdout)
    r = kit.submit("gpu-check", *a, "--gpu-instance", "4g.20gb")
    assert r.returncode == 2 and "not offered" in r.stderr
    r = kit.submit("gpu-check", *a, "--gpu-instance", "2g.20gb", "--need-gpu-mem-gb", "30")
    assert r.returncode == 2 and "20 GB of GPU memory" in r.stderr
    # Nibi/Rorqual short MIG names, Narval A100 MIG
    for cl, inst, flag in (("nibi", "2g.20gb", "--gpus=h100_2g.20gb:1"),
                           ("rorqual", "1g.10gb", "--gpus=h100_1g.10gb:1"),
                           ("narval", "3g.20gb", "--gpus=a100_3g.20gb:1")):
        k = Kit(tmp_path / cl, cl)
        r = k.submit("gpu-check", *a, "--gpu-instance", inst)
        assert r.returncode == 0 and flag in sbatch_argv(r.stdout), (cl, r.stderr)
    t = Kit(tmp_path / "tri", "trillium")
    r = t.submit("gpu-check", *a, "--gpu-instance", "1g.10gb")
    assert r.returncode == 2 and "not offered" in r.stderr
    r = t.submit("gpu-check", *a, "--mem", "100G")
    assert r.returncode == 2 and "--mem is not accepted" in r.stderr
    r = t.submit("gpu-check", *a, "--cpus", "8")
    assert r.returncode == 2 and "--cpus is not accepted" in r.stderr


def test_pipeline_job_takes_any_config(tmp_path):
    kit = Kit(tmp_path, "nibi")
    a = ["--account", "def-testpi", "--time", "03:00:00"]
    r = kit.submit("pipeline", *a)
    assert r.returncode == 2 and "--config" in r.stderr
    r = kit.submit("pipeline", *a, "--config", "configs/demo_hpc_si001.yaml", "--variant",
                   "cpu_numpy")
    assert r.returncode == 2 and "--mem is required" in r.stderr     # numpy variant: a CPU job
    r = kit.submit("pipeline", *a, "--config", "configs/demo_hpc_si001.yaml", "--variant",
                   "cpu_numpy", "--mem", "32G")
    assert r.returncode == 0, r.stderr
    argv = sbatch_argv(r.stdout)
    assert "--cpus-per-task=8" in argv and not any(x.startswith("--gpus") for x in argv)
    ex = export_vars(argv)
    assert ex["RH_CONFIG"] == "configs/demo_hpc_si001.yaml" and ex["RH_VARIANT"] == "cpu_numpy"
    r = kit.submit("pipeline", *a, "--config", "configs/no_such.yaml", "--mem", "1G")
    assert r.returncode == 2 and "not found" in r.stderr
    r = kit.submit("smoke", *a, "--config", "configs/demo_hpc_si001.yaml", "--mem", "1G")
    assert r.returncode == 2 and "pipeline" in r.stderr
    r = kit.submit("demo-gpu", *a, "--variant", "cpu_numpy", "--skip-gpu-check-gate")
    assert r.returncode == 2 and "use the `pipeline` job" in r.stderr


def test_scratch_required(tmp_path):
    kit = Kit(tmp_path, "fir")
    env = kit.environ()
    env.pop("SCRATCH")
    r = kit.submit("smoke", "--account", "def-testpi", "--time", "01:00:00", "--mem", "4G",
                   env=env)
    assert r.returncode == 2 and "SCRATCH" in r.stderr
    r = kit.submit("smoke", "--account", "def-testpi", "--time", "01:00:00", "--mem", "4G",
                   "--scratch", str(kit.scratch), env=env)
    assert r.returncode == 0, r.stderr


def test_environment_of_another_cluster_refused(tmp_path):
    kit = Kit(tmp_path, "fir")
    make_env_dir(tmp_path, "narval")                   # overwrite the record: built on Narval
    r = kit.submit("smoke", "--account", "def-testpi", "--time", "01:00:00", "--mem", "4G")
    assert r.returncode == 2 and "built for 'narval'" in r.stderr


def test_unknown_cluster_and_job(tmp_path):
    kit = Kit(tmp_path, "fir")
    kit.cluster = "cedar"
    r = kit.submit("smoke", "--account", "def-testpi", "--time", "01:00:00", "--mem", "4G")
    assert r.returncode == 2 and "retired" in r.stderr
    kit.cluster = "fir"
    r = kit.submit("bogus", "--account", "def-testpi", "--time", "01:00:00")
    assert r.returncode == 2 and "unknown job" in r.stderr


def test_real_submission_matches_dry_run_and_is_recorded(tmp_path):
    kit = Kit(tmp_path, "rorqual")
    a = ["--account", "def-testpi", "--time", "01:00:00", "--mem", "4G"]
    dry = sbatch_argv(kit.submit("smoke", *a).stdout)
    r = kit.submit("smoke", *a, dry=False)
    assert r.returncode == 0, r.stderr
    sent = (kit.root / "sbatch_args.txt").read_text().splitlines()
    assert sent[-1] == str(JOB_SCRIPT)

    def strip(v):                                      # the record name carries a time stamp
        return [",".join(i for i in x.split(",") if not i.startswith("RH_SUBMISSION_RECORD="))
                for x in v]
    assert strip(sent) == strip(dry[1:])
    rec = export_vars(["sbatch"] + sent)["RH_SUBMISSION_RECORD"]
    plan = json.loads(Path(rec).read_text())
    assert plan["cluster"] == "rorqual" and plan["argv"][1:] == sent
    assert "Submitted batch job 900001" in Path(rec + ".sbatch_output").read_text()
    assert (kit.run_root / "logs").is_dir()


# --------------------------------------------------------------------------------------------------
# setup_alliance.sh and the scripts themselves
# --------------------------------------------------------------------------------------------------
def test_setup_refuses_without_module_command(tmp_path):
    env = clean_environ(PATH="/usr/bin:/bin")
    # (on a cluster, the running setup's own log already exists: compare before and after)
    before = set(REPO.glob("alliance_setup_*.log"))
    r = subprocess.run(["bash", str(KIT / "setup_alliance.sh"), "fir"], cwd=REPO, env=env,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 2, (r.stdout, r.stderr)
    assert "'module' command is not available" in r.stderr
    assert set(REPO.glob("alliance_setup_*.log")) == before, "setup started logging"


def test_setup_refuses_unknown_cluster_and_wrong_directory(tmp_path):
    b = make_fakebin(tmp_path)
    env = clean_environ(PATH=f"{b}:/usr/bin:/bin")
    r = subprocess.run(["bash", str(KIT / "setup_alliance.sh"), "cedar"], cwd=REPO, env=env,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 2 and "unknown cluster" in r.stderr
    r = subprocess.run(["bash", str(KIT / "setup_alliance.sh"), "fir"], cwd=tmp_path, env=env,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 2 and "repository root" in r.stderr


SCRIPTS = [KIT / "setup_alliance.sh", KIT / "submit.sh", KIT / "job.sbatch",
           KIT / "collect_results.sh", REPO / "scripts" / "hpc" / "run_pipeline.slurm"]


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_bash_syntax(script):
    r = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck not installed")
@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_shellcheck(script):
    r = subprocess.run(["shellcheck", "-s", "bash", str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


# --------------------------------------------------------------------------------------------------
# cluster profiles: locators on every value, agreement with H1's table
# --------------------------------------------------------------------------------------------------
def _leaves(node, path=()):
    if isinstance(node, dict) and "value" in node:
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _leaves(v, path + (k,))


def test_every_profile_value_has_a_locator():
    d = _yaml(KIT / "clusters.yaml")
    n = 0
    for sect in ("common", "clusters"):
        for path, leaf in _leaves(d[sect]):
            assert isinstance(leaf.get("locator"), str) and len(leaf["locator"].strip()) > 5, path
            n += 1
    assert n > 150
    for c in CLUSTERS:
        assert set(d["clusters"][c]["gpu"]["instances"]) >= {"full"}


def test_profiles_agree_with_h1_table():
    d = _yaml(KIT / "clusters.yaml")["clusters"]
    rows = list(csv.DictReader(open(REPO / "docs" / "agent_reports" / "H1_alliance_clusters.tsv"),
                               delimiter="\t"))
    gpu_rows = {r["cluster"].lower(): r for r in rows
                if r["node_type"] in ("gpu", "gpu_h100") and r["cluster"].lower() in CLUSTERS}
    assert set(gpu_rows) == set(CLUSTERS)
    for c, r in gpu_rows.items():
        p = d[c]
        assert r["login_host"].split()[0] in (p["login_hosts"]["value"] + [p["gpu_login_host"]["value"]])
        assert int(r["max_walltime_h"].split()[0]) == p["walltime_max_hours"]["value"]
        assert int(r["gpus_per_node"]) == p["gpu"]["gpus_per_node"]["value"]
        assert int(r["gpu_mem_GB"]) == p["gpu"]["instances"]["full"]["gpu_mem_gb"]["value"]
        assert (r["compute_node_internet"] == "yes") == p["compute_internet"]["value"]
        for inst in p["gpu"]["instances"]:
            if inst != "full":
                assert inst in r["mig_instances"], (c, inst)
    assert d["trillium"]["gpu"]["mig_availability"]["value"] == "none"
    assert d["nibi"]["walltime_min_minutes_test"]["value"] == "NOT_FOUND"


def test_time_parser():
    sys.path.insert(0, str(KIT))
    import kit
    assert kit.time_minutes("90") == 90
    assert kit.time_minutes("10:30") == 10.5
    assert kit.time_minutes("01:00:00") == 60
    assert kit.time_minutes("2-3") == 2 * 1440 + 180
    assert kit.time_minutes("1-00:30") == 1470
    assert kit.time_minutes("1-00:00:30") == 1440.5
    for bad in ("", "1h", "00:00:00", "1:2:3:4"):
        with pytest.raises(kit.Refused):
            kit.time_minutes(bad)


# --------------------------------------------------------------------------------------------------
# gpu_check.py without a GPU; its comparison plumbing with numpy standing in for cupy
# --------------------------------------------------------------------------------------------------
def _gpu_check():
    sys.path.insert(0, str(KIT))
    import gpu_check
    return gpu_check


@pytest.mark.skipif(shutil.which("nvidia-smi") is not None, reason="a GPU may be present")
def test_gpu_check_fails_without_cupy_or_gpu(tmp_path):
    env = clean_environ()
    r = subprocess.run([sys.executable, str(KIT / "gpu_check.py"), "--out", str(tmp_path / "gc"),
                        "--threads", "1", "--pass-dir", str(tmp_path / "pass"), "--cluster", "fir",
                        "--env-id", "e", "--seed", "1"], env=env, capture_output=True, text=True,
                       timeout=300)
    assert r.returncode == 4, (r.stdout, r.stderr)
    assert "GPU CHECK: FAIL" in r.stdout
    res = json.loads((tmp_path / "gc" / "gpu_check.json").read_text())
    assert res["passed"] is False and "error" in res["device"]
    assert list((tmp_path / "gc" / "outputs" / "manifests").glob("gpu_check_*.json"))
    assert not (tmp_path / "pass").exists()


def test_gpu_check_comparison_plumbing_with_numpy():
    """numpy stands in for cupy: complex128 must agree to TOL_MS_C128 and complex64 to TOL_MS_C64
    on the rung-1 case (this tests the comparison code, not the GPU)."""
    gc = _gpu_check()
    rung1 = gc.tiny_cases()[0]
    out = gc.multislice_check(2, backends=("numpy",), cases=[rung1])
    runs = out[rung1[0]]["runs"]
    assert [r["precision"] for r in runs] == ["complex128", "complex64"]
    assert runs[0]["rel_err_vs_numpy_complex128"] == 0.0
    assert 0 < runs[1]["rel_err_vs_numpy_complex128"] < gc.TOL_MS_C64
    assert all(r["passed"] for r in runs)
    assert gc.TOL_MS_C128 == 1e-9 and gc.TOL_MS_C64 == 1e-3      # fixed before any GPU run


# --------------------------------------------------------------------------------------------------
# emulated batch jobs (fake sbatch runs job.sbatch; CPU only)
# --------------------------------------------------------------------------------------------------
def _run_emulated(kit, job, *args, tasks=None):
    env = kit.environ(FAKE_SBATCH_EXECUTE="1", **({"FAKE_SBATCH_TASKS": tasks} if tasks else {}))
    return kit.submit(job, *args, dry=False, env=env, timeout=1200)


def _jobdirs(kit, pattern):
    return sorted((kit.run_root / "runs").glob(pattern))


def test_emulated_smoke_job_end_to_end(tmp_path):
    kit = Kit(tmp_path, "fir")
    before = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"], capture_output=True,
                            text=True).stdout
    r = _run_emulated(kit, "smoke", "--account", "def-testpi", "--time", "00:30:00", "--mem", "4G")
    assert r.returncode == 0, (r.stdout, r.stderr)
    (jd,) = _jobdirs(kit, "smoke_900001_*")
    log = (kit.run_root / "logs" / "smoke_900001.log").read_text()
    assert (tmp_path / "job_900001.status").read_text() == "0", log[-3000:]
    assert (jd / "job_status.txt").read_text().startswith("exit_status 0")
    for f in ("pipeline/summary.json", "pipeline/manifest.json", "manifests/pipeline__manifest.json",
              "slurm.log", "job_info.json", "module_list.txt", "submission.json",
              f"reflholo_900001_dryrun.txt"):
        assert (jd / f).is_file(), f
    m = json.loads((jd / "pipeline" / "manifest.json").read_text())
    assert m["beam_energy_keV"] == 200.0 and m["repository"]["commit"]
    assert "MISMATCH" not in m["threads"]["check"] and not m["threads"]["check"].startswith("not set")
    info = json.loads((jd / "job_info.json").read_text())
    assert info["slurm"]["OMP_NUM_THREADS"] == "4" and info["kit"]["RH_KIT_JOB"] == "smoke"
    assert "module purge" in (tmp_path / "module_calls.txt").read_text()
    assert "modules: identical to the setup record" in log
    assert "h = " in log                              # the geometric smoke demo returns heights
    after = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"], capture_output=True,
                           text=True).stdout
    assert after == before, "the job wrote into the repository"


def test_emulated_null_study_array_task(tmp_path):
    kit = Kit(tmp_path, "narval")
    study = tmp_path / "study_numpy.yaml"
    txt = (REPO / "scripts" / "hpc" / "null_test_study" / "study.yaml").read_text()
    txt = txt.replace("  backend: cupy          # numpy on CPU nodes (then set threads to "
                      "cpus-per-task)\n  threads: 8\n", "  backend: numpy\n  threads: 2\n")
    assert "backend: numpy" in txt
    study.write_text(txt)
    r = _run_emulated(kit, "null-study", "--account", "def-testpi", "--time", "01:00:00",
                      "--study", str(study), "--mem", "8G", tasks="0")
    assert r.returncode == 0, (r.stdout, r.stderr)
    argv = shlex.split(r.stdout.splitlines()[1])
    assert "--array=0-16" in argv and "--cpus-per-task=2" in argv
    (jd,) = _jobdirs(kit, "null-study_900001/task000_900002_*")
    log = (kit.run_root / "logs" / "null-study_900001_0.log").read_text()
    assert (tmp_path / "job_900002.status").read_text() == "0", log[-3000:]
    res = json.loads((jd / "study/outputs/null_test_study/tfix_bragg_abs0_L0.json").read_text())
    assert res["test_only"] is True and res["point"]["name"] == "tfix_bragg_abs0_L0"
    assert list((jd / "manifests").glob("study__outputs__manifests__null_test_*.json"))


def test_emulated_gpu_check_refuses_without_gpu(tmp_path):
    if shutil.which("nvidia-smi"):
        pytest.skip("nvidia-smi present")
    kit = Kit(tmp_path, "rorqual")
    r = _run_emulated(kit, "gpu-check", "--account", "def-testpi", "--time", "00:10:00")
    assert r.returncode == 0, r.stderr                 # sbatch itself succeeded
    assert (tmp_path / "job_900001.status").read_text() == "4"
    (jd,) = _jobdirs(kit, "gpu-check_900001_*")
    assert (jd / "job_status.txt").read_text().startswith("exit_status 4")
    assert "nvidia-smi not found" in (kit.run_root / "logs" / "gpu-check_900001.log").read_text()
    assert not (kit.run_root / "gpu_check").exists()   # no PASS record


# --------------------------------------------------------------------------------------------------
# collect_results.sh
# --------------------------------------------------------------------------------------------------
def test_collect_results(tmp_path):
    root = tmp_path / "reflholo"
    run = root / "runs" / "smoke_123_20260923T000000Z"
    (run / "pipeline").mkdir(parents=True)
    (run / "pipeline" / "summary.json").write_text('{"a": 1}')
    (run / "pipeline" / "arrays.npz").write_bytes(b"x" * 3_000_000)
    (run / "small.npz").write_bytes(b"y" * 1000)
    (run / "quicklook.png").write_bytes(b"png")
    other = root / "runs" / "torus_456_20260923T000000Z"
    other.mkdir(parents=True)
    (other / "summary_trench.json").write_text("{}")
    (root / "logs").mkdir()
    (root / "logs" / "smoke_123.log").write_text("log")
    (root / "logs" / "torus_456.log").write_text("log")
    (root / "submissions").mkdir()
    (root / "submissions" / "s1.json").write_text("{}")
    (root / "submissions" / "s1.json.sbatch_output").write_text("Submitted batch job 123\n")
    (root / "submissions" / "s2.json").write_text("{}")
    (root / "submissions" / "s2.json.sbatch_output").write_text("Submitted batch job 456\n")
    env = clean_environ(PATH=os.environ["PATH"])
    r = subprocess.run(["bash", str(KIT / "collect_results.sh"), "--run-root", str(root)],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 2 and "--max-array-mb is required" in r.stderr
    r = subprocess.run(["bash", str(KIT / "collect_results.sh"), "--run-root", str(root),
                        "--max-array-mb", "1", "--jobs", "123", "--out", str(tmp_path / "c")],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    (tar,) = list((tmp_path / "c").glob("reflholo_results_*.tar.gz"))
    assert (tmp_path / "c" / (tar.name + ".sha256")).is_file()
    ex = tmp_path / "x"
    with tarfile.open(tar) as t:
        names = set(t.getnames())
        t.extractall(ex)
    rel = "runs/smoke_123_20260923T000000Z"
    assert {f"{rel}/pipeline/summary.json", f"{rel}/small.npz", f"{rel}/quicklook.png",
            "logs/smoke_123.log", "submissions/s1.json", "submissions/s1.json.sbatch_output",
            "MANIFEST.sha256", "SKIPPED_ARRAYS.tsv", "COLLECT_INFO.txt"} <= names
    assert f"{rel}/pipeline/arrays.npz" not in names                # 3 MB > 1 MB cap
    assert not any("torus_456" in n or n.startswith("submissions/s2") for n in names)
    assert f"{rel}/pipeline/arrays.npz\t3000000" in (ex / "SKIPPED_ARRAYS.tsv").read_text()
    chk = subprocess.run(["sha256sum", "-c", "MANIFEST.sha256"], cwd=ex, capture_output=True,
                         text=True)
    assert chk.returncode == 0, chk.stdout + chk.stderr


# --------------------------------------------------------------------------------------------------
# run_pipeline.slurm: the two additions used by the kit (no regression of its own submission mode)
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("partition,expected", [("none", None), ("gpu_p", "--partition=gpu_p")])
def test_run_pipeline_partition_none(tmp_path, partition, expected):
    b = make_fakebin(tmp_path)
    env = clean_environ(PATH=f"{b}:{os.environ['PATH']}", RH_ACCOUNT="def-testpi",
                        RH_PARTITION=partition, RH_TIME_LIMIT="00:10:00", RH_GPU="none",
                        RH_MODE="smoke", RH_REPO=str(REPO))
    r = subprocess.run(["bash", str(REPO / "scripts" / "hpc" / "run_pipeline.slurm")],
                       cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, (r.stdout, r.stderr)
    args = (tmp_path / "sbatch_args.txt").read_text().splitlines()
    parts = [a for a in args if a.startswith("--partition")]
    assert parts == ([expected] if expected else [])
    assert "--account=def-testpi" in args and "--time=00:10:00" in args
    assert not any(a.startswith("--gres") for a in args)            # RH_GPU=none
    exp = [a for a in args if a.startswith("--export=")][0]
    assert "RH_WORKDIR=" in exp


def test_run_pipeline_placeholders_still_required(tmp_path):
    b = make_fakebin(tmp_path)
    env = clean_environ(PATH=f"{b}:{os.environ['PATH']}", RH_ACCOUNT="def-testpi",
                        RH_TIME_LIMIT="00:10:00", RH_GPU="none", RH_MODE="smoke",
                        RH_REPO=str(REPO))
    r = subprocess.run(["bash", str(REPO / "scripts" / "hpc" / "run_pipeline.slurm")],
                       cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300)
    assert r.returncode == 2 and "PARTITION" in r.stderr
    assert not (tmp_path / "sbatch_args.txt").exists()


def test_submit_refuses_when_recorded_modules_do_not_load(tmp_path):
    kit = Kit(tmp_path, "fir")
    (kit.env_dir / "module_list.txt").write_text("\n".join(MODULES + ["scipy-stack/2026a"]) + "\n")
    r = kit.submit("smoke", "--account", "def-testpi", "--time", "01:00:00", "--mem", "2G")
    assert r.returncode == 2 and "could not be loaded as recorded" in r.stderr
    assert "scipy-stack/2026a" in r.stderr


def test_null_study_option_combinations(tmp_path):
    kit = Kit(tmp_path, "fir")
    kit.gpu_pass()
    a = ["--account", "def-testpi", "--time", "01:00:00"]
    r = kit.submit("null-study", *a, "--only", "tfix_bragg_abs0_L0", "--array-throttle", "2")
    assert r.returncode == 2 and "array mode only" in r.stderr
    r = kit.submit("null-study", *a, "--only", "tfix_bragg_abs0_L0", "--serial")
    assert r.returncode == 2 and "exclusive" in r.stderr
    r = kit.submit("smoke", *a, "--mem", "2G", "--only", "x")
    assert r.returncode == 2 and "null-study job only" in r.stderr


# --------------------------------------------------------------------------------------------------
# gpu_check.py end to end with numpy IMPERSONATING cupy (plumbing of the PASS record; not a GPU test)
# --------------------------------------------------------------------------------------------------
FAKE_CUPY = '''"""numpy impersonating cupy for tests/hpc: NOT a GPU."""
import sys as _sys
import numpy as _np
from numpy import *  # noqa: F401,F403
import numpy.fft as _nfft
__version__ = "0.0+numpy-impersonation"
MODE = "{mode}"


class _FFT:
    def __getattr__(self, n):
        return getattr(_nfft, n)

    def fft2(self, a, **kw):
        if MODE == "raise":
            raise RuntimeError("fake cuFFT failure")
        return _nfft.fft2(a, **kw)


fft = _FFT()
_sys.modules["cupy.fft"] = fft


def asnumpy(a):
    return _np.asarray(a)


class _Runtime:
    getDeviceCount = staticmethod(lambda: 1)
    getDeviceProperties = staticmethod(lambda i: dict(name=b"FAKE numpy impersonation"))
    runtimeGetVersion = staticmethod(lambda: 0)
    driverGetVersion = staticmethod(lambda: 0)


class _Device:
    def __init__(self, i=0):
        self.mem_info = (0, 0)
        self.compute_capability = "00"

    def synchronize(self):
        pass


class cuda:
    runtime = _Runtime
    Device = _Device


class ElementwiseKernel:          # abTEM builds kernels at import time (abtem/core/complex.py)
    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        raise RuntimeError("fake cupy: no kernels")


def fuse(*a, **k):                # abtem/bloch/matrix_exponential.py decorates with cp.fuse
    if a and callable(a[0]) and not k:
        return a[0]
    return lambda f: f
'''


def _fake_cupy(tmp_path, mode):
    d = tmp_path / f"fakecupy_{mode}" / "cupy"
    d.mkdir(parents=True)
    (d / "__init__.py").write_text(FAKE_CUPY.replace("{mode}", mode))
    # abTEM imports cupyx and cupyx.scipy.ndimage whenever cupy imports (abtem/core/backend.py)
    x = d.parent / "cupyx" / "scipy"
    x.mkdir(parents=True)
    (d.parent / "cupyx" / "__init__.py").write_text('"""fake cupyx (tests/hpc)"""\n')
    (x / "__init__.py").write_text('"""fake cupyx.scipy (tests/hpc)"""\n')
    (x / "ndimage.py").write_text("from scipy.ndimage import *  # noqa: F401,F403\n")
    return d.parent


@pytest.mark.parametrize("mode", ["raise", "pass"])
def test_gpu_check_pass_record_with_fake_cupy(tmp_path, mode):
    fake = _fake_cupy(tmp_path, mode)
    env = clean_environ(PYTHONPATH=str(fake), SLURM_JOB_ID="77", OMP_NUM_THREADS="2")
    r = subprocess.run([sys.executable, str(KIT / "gpu_check.py"), "--out", str(tmp_path / "gc"),
                        "--threads", "2", "--pass-dir", str(tmp_path / "pass"), "--cluster",
                        "fir", "--env-id", "e1", "--seed", "3"], env=env, capture_output=True,
                       text=True, timeout=1200)
    res = json.loads((tmp_path / "gc" / "gpu_check.json").read_text())
    assert res["device"]["device_name"] == "FAKE numpy impersonation"
    if mode == "raise":
        assert r.returncode == 1 and "fake cuFFT failure" in res["error"], r.stdout
        assert not (tmp_path / "pass").exists()
        return
    assert r.returncode == 0, (r.stdout[-3000:], r.stderr[-3000:])
    assert "GPU CHECK: PASS" in r.stdout and res["passed"] is True
    (rec,) = (tmp_path / "pass").glob("PASS_fir_e1_77.json")
    assert json.loads(rec.read_text())["commit"]
    names = set(res["multislice"])
    assert names == {"rung1_continuum_refraction", "atomistic_a2_step_w2"}
