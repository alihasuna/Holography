"""Provenance gaps (audit A2 finding m8; scratch script e16).

* a dirty working tree was recorded only as dirty=True; now the SHA-256 of `git diff HEAD --binary`
  and the untracked files (list and content hash) are recorded with the flag;
* a git failure was swallowed (commit None) and the manifest built anyway; now it is refused unless
  the caller states allow_no_git=True, and the failure is recorded;
* only the configuration validator wrote a manifest; now every public entry point that writes
  output (validate_configs.main, structure.write_xyz, structure.write_metadata_json) writes one;
* the thread count was declared but not checked against the BLAS/OpenMP environment; it is checked
  and the result recorded.
Everything is written under pytest's tmp_path; the repository's outputs/ must not change.
"""
import hashlib
import json
import subprocess

import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.io import validate_configs
from reflection_holo.provenance import manifest as M
from reflection_holo.structure import Staircase, build_si001_terraces, write_metadata_json, write_xyz

REPO = M.repository_root()


@pytest.fixture(scope="module")
def mixed_110():
    """[110] azimuth, a/2 up, a/4 down, a/4 down at the cell edge (TEST_ONLY azimuth label)."""
    st = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(4, 3, 3),
                   boundary_step_layers=-1)
    return build_si001_terraces(azimuth_uvw=(1, 1, 0),
                                azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
                                staircase=st, edge_periods=3, substrate_layers=5,
                                first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                                overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                                lattice_parameter_label="ASSUMPTION B2")


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=S3 test",
                           "-c", "user.email=s3@example.invalid", *args],
                          check=True, capture_output=True).stdout


@pytest.fixture()
def dirty_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    (root / "a.txt").write_text("one\n")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-q", "-m", "first")
    (root / "a.txt").write_text("two\n")                   # tracked change
    (root / "new.txt").write_text("untracked\n")           # untracked file
    return root


def test_dirty_tree_records_the_diff_hash(dirty_repo):
    g = M.git_state(dirty_repo)
    assert g["dirty"] is True and g["error"] is None
    want = hashlib.sha256(_git(dirty_repo, "diff", "HEAD", "--binary")).hexdigest()
    assert g["diff_head_sha256"] == want
    assert g["untracked_files"] == ["new.txt"]
    h = hashlib.sha256()
    h.update(b"new.txt\0")
    h.update(hashlib.sha256(b"untracked\n").digest())
    assert g["untracked_sha256"] == h.hexdigest()
    _git(dirty_repo, "checkout", "--", "a.txt")
    (dirty_repo / "new.txt").unlink()
    clean = M.git_state(dirty_repo)
    assert clean["dirty"] is False and clean["diff_head_sha256"] is None
    assert clean["untracked_files"] == []


def _kw(tmp_path):
    return dict(run_name="unit test", config=None, input_paths=[], seeds={}, thread_count=1,
                precision={"real": "float64"}, engines={}, wave_planes={}, beam_energy_keV=None)


def test_git_unavailable_is_refused_unless_stated(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "git_state", lambda root=None: dict(
        commit=None, dirty=None, branch=None, diff_head_sha256=None, untracked_files=None,
        untracked_sha256=None, error="OSError: git not found"))
    with pytest.raises(RuntimeError, match="git"):
        M.build_manifest(**_kw(tmp_path))
    m = M.build_manifest(**_kw(tmp_path), allow_no_git=True)
    assert m["repository"]["error"].startswith("OSError") and m["repository"]["allowed_without_git"]


def test_thread_environment_is_checked(tmp_path, monkeypatch):
    for v in M.THREAD_ENV_VARS:
        monkeypatch.delenv(v, raising=False)
    m = M.build_manifest(**_kw(tmp_path))
    assert m["threads"]["check"].startswith("not set")
    monkeypatch.setenv("OMP_NUM_THREADS", "4")
    m = M.build_manifest(**_kw(tmp_path))
    assert m["threads"]["check"].startswith("MISMATCH") and "OMP_NUM_THREADS=4" in m["threads"]["check"]
    m = M.build_manifest(**{**_kw(tmp_path), "thread_count": 4})
    assert m["threads"]["check"].startswith("consistent")


def _manifests(root):
    return sorted((root / "manifests").glob("*.json"))


def test_structure_writers_write_a_manifest(mixed_110, tmp_path):
    out = tmp_path / "outputs"
    p = write_xyz(mixed_110, tmp_path / "s.xyz", outputs_root=out)
    q = write_metadata_json(mixed_110, tmp_path / "s.json", outputs_root=out)
    ms = [json.loads(f.read_text()) for f in _manifests(out)]
    assert len(ms) == 2
    recorded = {o["path"]: o["sha256"] for m in ms for o in m["extra"]["outputs"]}
    for f in (p, q):
        assert recorded[str(f)] == hashlib.sha256(f.read_bytes()).hexdigest()
    for m in ms:
        assert m["extra"]["structure"]["positions_sha256"] == mixed_110.metadata["positions_sha256"]
        assert m["extra"]["structure"]["lattice"]["a_label"] == "ASSUMPTION B2"
    with pytest.raises(TypeError):
        write_xyz(mixed_110, tmp_path / "t.xyz")                    # outputs_root is required


def test_validate_configs_writes_its_manifest_where_told(tmp_path, capsys):
    before = sorted(p.name for p in (REPO / "outputs").rglob("*")) if (REPO / "outputs").exists() else []
    cfgs = sorted(str(p) for p in (REPO / "configs").glob("cfg_*.yaml"))
    assert validate_configs.main(cfgs, outputs_root=tmp_path / "outputs") == 0
    printed = capsys.readouterr().out
    assert "cfg_b_si001_patterned.yaml: CFG-B" in printed and "REFUSED" in printed
    (m,) = [json.loads(f.read_text()) for f in _manifests(tmp_path / "outputs")]
    assert set(m["extra"]["results"]) == {p.split("/")[-1] for p in cfgs}
    after = sorted(p.name for p in (REPO / "outputs").rglob("*")) if (REPO / "outputs").exists() else []
    assert after == before
