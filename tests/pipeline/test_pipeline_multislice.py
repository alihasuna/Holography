"""End-to-end smoke test of the pipeline with the multislice engine (variant multislice_tiny of
configs/demo_smoke_si001.yaml). SKIPPED, with the reason, when forward.multislice (or its optional
abTEM dependency) is not importable. The engine is UNVALIDATED for atomistic reflection: this test
checks the interface and the bookkeeping only, not the physics of the exit wave."""
import json

import pytest

from reflection_holo.pipeline import run
from reflection_holo.pipeline.engines import multislice_status
from reflection_holo.pipeline.__main__ import main as cli_main

from conftest_pipeline import HPC, SMOKE

OK, WHY = multislice_status()
pytestmark = pytest.mark.skipif(not OK, reason=f"multislice engine unavailable: {WHY}")


def test_multislice_tiny_end_to_end(tmp_path):
    out = tmp_path / "ms"
    s = run(SMOKE, out, variant="multislice_tiny")
    assert s["engine"]["name"] == "multislice"
    assert "UNVALIDATED" in s["engine"]["label"]
    ew = s["exit_wave"]
    assert ew["plane"] == "exit plane z = L_z (no further propagation)"
    assert ew["dx_A"] > 0 and ew["dy_A"] > 0
    mip = s["mean_inner_potentials"]
    assert mip["V0_source"] == "sections.engine.multislice.potential_mip"
    assert abs(mip["engine_potential"]["potential_mip_V"] - 13.903) <= 5e-4
    assert mip["cfg_b_V0_V"] == 12.0
    assert s["glancing_angle"]["assumption_id"] == "B32"
    # the tiny cell is far below the dark-field resolution: steps reported, not measured
    for st in s["quantification"]["steps"]:
        assert st["measured"] is False and "not measurable" in st["reason"]
    m = json.loads((out / "manifest.json").read_text())
    assert "reflection_holo.forward.multislice" in m["engines"]
    assert (out / "outputs" / "manifests").is_dir()          # the engine's own manifest


def test_hpc_config_passes_the_gate_and_the_engine_geometry_checks(capsys):
    """dry-run of the HPC demo builds its 1.44M-atom structure and cell and runs every engine
    assertion (docs/05 4.3 items 1-4, band limits) without propagating. The HPC demo requests the
    cupy backend: where cupy is not usable the checks still run and the dry run exits 4 saying so
    (audit A3 m5; before, it exited 0)."""
    from reflection_holo.pipeline.engines import backend_status
    rc = cli_main(["dry-run", "--config", str(HPC)])
    txt = capsys.readouterr().out
    assert "engine multislice" in txt and "16.134720 mrad" in txt
    ok, why = backend_status("cupy")
    if ok:
        assert rc == 0
    else:
        assert rc == 4 and "multislice backend cupy NOT available" in txt, why
