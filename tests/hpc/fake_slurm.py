"""Fake Slurm and Lmod commands for the Alliance-kit tests (tests/hpc). Not a test module.

* `module` (tests/hpc/bin/fake_module): records its calls; `module -t list` prints MODULES (to
  stderr, as Lmod does).
* `sbatch` (tests/hpc/bin/fake_sbatch) in record mode: writes its argv (one per line) and prints
  "Submitted batch job N".
* `sbatch` in execute mode (FAKE_SBATCH_EXECUTE=1): a minimal emulation of a batch job: parses
  --export=ALL,K=V,..., --output (%j, %A, %a), --chdir, --cpus-per-task and --array (runs the tasks
  listed in FAKE_SBATCH_TASKS, default the first index only), sets SLURM_JOB_ID,
  SLURM_CPUS_PER_TASK, SLURM_ARRAY_JOB_ID and SLURM_ARRAY_TASK_ID and runs the script with bash,
  stdout and stderr to the output file. No GPU, no scontrol, no nvidia-smi.

Hermetic against the login shell (H4 F1):
* clean_environ removes BASH_ENV, ENV and exported shell functions (BASH_FUNC_*), so that a site
  profile defining Lmod's `module` function cannot replace the fake in a child bash;
* the fakes are tracked executables in tests/hpc/bin/ (the repository must be executable anyway:
  its venv runs from it). make_fakebin(root) puts SYMLINKS named `module` and `sbatch` into
  <root>/bin: a symlink in a noexec temporary directory to an executable on another mount runs
  (also through `exec sbatch` in run_pipeline.slurm), and the fakes write their records next to the
  symlink (<root>), never into the repository (tests/conftest.py guards outputs/).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

MODULES = ["StdEnv/2023", "python/3.11.5", "cuda/12.6"]
REPO = Path(__file__).resolve().parents[2]
FAKES = Path(__file__).resolve().parent / "bin"
assert " ".join(MODULES) in (FAKES / "fake_module").read_text().replace("\\n", "")


def make_fakebin(root: Path) -> Path:
    """<root>/bin with `module` and `sbatch` (symlinks to the tracked fakes); records in <root>."""
    b = Path(root) / "bin"
    b.mkdir(parents=True, exist_ok=True)
    for name in ("module", "sbatch"):
        link = b / name
        if not link.is_symlink():
            link.symlink_to(FAKES / f"fake_{name}")
    return b


def make_env_dir(root: Path, cluster: str, env_id: str | None = None) -> Path:
    e = root / "env"
    e.mkdir(parents=True, exist_ok=True)
    (e / "modules.sh").write_text("module purge\n" + "".join(f"module load {m}\n" for m in MODULES))
    (e / "module_list.txt").write_text("\n".join(MODULES) + "\n")
    env_id = env_id or f"{cluster}-20260923T000000Z-0123456789ab"
    (e / "env.json").write_text(
        '{"schema": "reflholo_alliance_env/1", "cluster": "%s", "env_id": "%s", '
        '"setup_complete": true}' % (cluster, env_id))
    return e


def write_gpu_pass(run_root: Path, cluster: str, env_id: str, *, name: str | None = None,
                   fields: dict | None = None) -> Path:
    """A gpu-check PASS record as gpu_check.py writes it (schema, cluster, environment, the engine
    code hash of this repository); `fields` replaces fields (to make an invalid one)."""
    sys.path.insert(0, str(REPO / "scripts" / "hpc" / "alliance"))
    import kit
    rec = dict(schema=kit.PASS_SCHEMA, passed=True, cluster=cluster, env_id=env_id,
               engine_code_sha256=kit.engine_code_sha256(REPO)["sha256"], job_id="1",
               commit="0" * 40)
    rec.update(fields or {})
    d = Path(run_root) / "gpu_check"
    d.mkdir(parents=True, exist_ok=True)
    p = d / (name or f"PASS_{cluster}_{env_id}_1.json")
    p.write_text(json.dumps(rec))
    return p


def clean_environ(**extra) -> dict:
    """os.environ without Slurm/kit variables and without the login shell's hooks: an inherited
    Lmod `module` function (BASH_FUNC_*) and the files a non-interactive bash or sh would source
    (BASH_ENV, ENV), which could define `module` in every child bash (H4 F1)."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("RH_", "SLURM_", "SBATCH_", "SALLOC_", "BASH_FUNC_", "FAKE_"))
           and k not in ("BASH_ENV", "ENV")}
    env.update(extra)
    return env
