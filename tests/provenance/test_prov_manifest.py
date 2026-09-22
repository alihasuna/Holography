"""Run manifest (docs/05 section 6): required keys present, hashes correct, written under an
outputs/ directory. Uses tmp_path/outputs so that tests do not write into the repository."""
import datetime as dt
import hashlib
import json

import numpy as np
import pytest

from pathlib import Path

from reflection_holo.io.config import load_config_file
from reflection_holo.provenance.manifest import (REQUIRED_KEYS, build_manifest, git_state,
                                                 write_manifest)

REPO = Path(__file__).resolve().parents[2]


def _config():
    """The shipped CFG-A, loaded at run level (read only). The former three-parameter fixture no
    longer loads at run level (audit A2 M2 (d): required parameters absent)."""
    return load_config_file(REPO / "configs" / "cfg_a_si111_cleaved_110azimuth.yaml", level="run")


def _manifest(tmp_path, **over):
    inp = tmp_path / "wave.bin"
    inp.write_bytes(b"\x00\x01test-input")
    kw = dict(run_name="unit test", config=_config(), input_paths=[inp],
              seeds={"phonon": 12345}, thread_count=4,
              precision={"real": "float64", "complex": "complex128"},
              engines={"none": {"version": None, "commit": None, "licence": None}},
              wave_planes={"object_wave": "exit plane of the cell (z = L_z)",
                           "reference_wave": "detector plane"},
              beam_energy_keV=200.0)
    kw.update(over)
    return build_manifest(**kw), inp


def test_required_keys_present_and_values(tmp_path):
    m, inp = _manifest(tmp_path)
    for k in REQUIRED_KEYS:
        assert k in m, k
    for k in ("commit", "dirty", "branch", "error"):
        assert k in m["repository"]
    assert m["numpy_version"] == np.__version__
    assert "version" in m["python"]
    assert "numpy" in m["packages"] and "reflection_holo" in m["packages"]
    assert m["seeds"] == {"phonon": 12345}
    assert m["threads"]["requested"] == 4 and "OMP_NUM_THREADS" in m["threads"]["environment"]
    assert m["precision"]["complex"] == "complex128"
    assert m["inputs"][0]["sha256"] == hashlib.sha256(inp.read_bytes()).hexdigest()
    assert len(m["config"]["sha256_canonical"]) == 64 and m["config"]["config_id"] == "CFG-A"
    assert m["wave_planes"]["object_wave"].startswith("exit plane")
    assert m["beam_energy_keV"] == 200.0
    ts = dt.datetime.fromisoformat(m["timestamp_utc"])
    assert ts.utcoffset() == dt.timedelta(0)


def test_git_commit_recorded():
    g = git_state()
    assert g["error"] is None and len(g["commit"]) == 40 and isinstance(g["dirty"], bool)


def test_write_under_outputs_and_round_trip(tmp_path):
    m, _ = _manifest(tmp_path)
    path = write_manifest(m, outputs_root=tmp_path / "outputs")
    assert path.parent == tmp_path / "outputs" / "manifests"
    back = json.loads(path.read_text())
    assert set(REQUIRED_KEYS) <= set(back)
    path2 = write_manifest(m, outputs_root=tmp_path / "outputs")
    assert path2 != path                                        # never overwritten
    with pytest.raises(ValueError, match="outputs"):
        write_manifest(m, outputs_root=tmp_path / "results")


def test_no_silent_defaults(tmp_path):
    with pytest.raises(TypeError):
        build_manifest(run_name="x", config=None, input_paths=[])      # seeds etc. required
    with pytest.raises(ValueError):
        _manifest(tmp_path, wave_planes={"object_wave": ""})       # plane must be declared
    with pytest.raises(ValueError):
        _manifest(tmp_path, thread_count=0)
    with pytest.raises(ValueError):
        _manifest(tmp_path, precision={})
    with pytest.raises(ValueError, match="200 keV"):
        _manifest(tmp_path, beam_energy_keV=300.0)
    m, _ = _manifest(tmp_path, config=None)
    assert m["config"]["path"] is None and "explicitly" in m["config"]["note"]
