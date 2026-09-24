"""Pipeline wiring of report E2: the specimen temperature (PROJECT_INPUT item 23, required with the
sourced thermal model B35; demo stand-in B36), the Si(001) reconstructions (multislice engine on the
staircase path only) and the p(2x1)a flip-flop ensemble (ASSUMPTION B37, configurations drawn per
realisation from the seeded generator, averaged after squaring). The engine runs are SKIPPED when
the multislice engine (abTEM) is unavailable. TEST_ONLY values exist in memory only."""
import copy
import json
import math

import numpy as np
import pytest

from reflection_holo.io.config import MissingProjectInputError
from reflection_holo.pipeline import (PipelineConfigError, list_inputs, load_pipeline_dict,
                                      read_pipeline_file, run)
from reflection_holo.pipeline.config import assumptions_in_use
from reflection_holo.pipeline.engines import multislice_status

from conftest_pipeline import SMOKE

OK, WHY = multislice_status()
needs_engine = pytest.mark.skipif(not OK, reason=f"multislice engine unavailable: {WHY}")
THERMAL = "multislice_tiny_thermal"
FLIP = "p(2x1)a flip-flop ensemble"
U_295 = math.sqrt(0.4761 / (8 * math.pi ** 2))


def _ms(d, variant=THERMAL):
    return d["variants"][variant]["sections"]["engine"]["multislice"]


def _termination(d, term):
    rec = d["cfg_b"]["parameters"]["surface_preparation_details"]
    rec.update(value={"termination": term, "overlayer": "none"}, label="TEST_ONLY",
               source="TEST_ONLY: reconstructed clean surface (report E2 gate test)")
    rec.pop("stands_in_for_item", None)
    rec.pop("assumption_id", None)


# ---- item 23 -----------------------------------------------------------------------------------
def test_thermal_variant_uses_B35_at_the_B36_stand_in():
    cfg = load_pipeline_dict(read_pipeline_file(SMOKE), variant=THERMAL)
    T = cfg.sections["engine"]["multislice"]["specimen_temperature"]
    assert (T.item, T.assumption_id, T.canonical_value, T.canonical_unit) == (23, "B36", 295.5, "K")
    used = {a["assumption_id"]: a for a in assumptions_in_use(cfg)}
    assert used["B36"]["demo_only"] is True and used["B36"]["item"] == 23
    rows = [r for r in list_inputs(read_pipeline_file(SMOKE), variant=THERMAL) if r["item"] == 23]
    assert len(rows) == 1 and rows[0]["used"] and rows[0]["status"] == "ASSUMPTION B36 stand-in"


def test_missing_specimen_temperature_fails_the_run():
    d = read_pipeline_file(SMOKE)
    del _ms(d)["specimen_temperature"]
    with pytest.raises(MissingProjectInputError, match="item 23") as e:
        load_pipeline_dict(d, variant=THERMAL)
    assert 23 in e.value.items
    d = read_pipeline_file(SMOKE)
    _ms(d)["specimen_temperature"] = dict(value=None, unit="K", label="PROJECT_INPUT", item=23,
                                          source="docs/06 item 23, not supplied")
    with pytest.raises(MissingProjectInputError, match="item 23"):
        load_pipeline_dict(d, variant=THERMAL)


@pytest.mark.parametrize("value,unit,match", [(350.0, "K", "outside"), (1023.15, "K", "outside"),
                                              (295.5, "A", "temperature"),
                                              (-5.0, "K", "positive")])
def test_bad_specimen_temperatures_are_refused(value, unit, match):
    d = read_pipeline_file(SMOKE)
    _ms(d)["specimen_temperature"].update(value=value, unit=unit)
    with pytest.raises(PipelineConfigError, match=match):
        load_pipeline_dict(d, variant=THERMAL)


def test_temperature_with_a_static_lattice_is_refused_not_ignored():
    d = read_pipeline_file(SMOKE)
    ms = _ms(d)
    ms["frozen_phonons"] = "none"
    ms["seed"] = None
    with pytest.raises(PipelineConfigError, match="refused rather than ignored"):
        load_pipeline_dict(d, variant=THERMAL)


def test_fixed_u_A7_form_still_accepted_for_demo_and_refused_for_comparison():
    d = read_pipeline_file(SMOKE)
    ms = _ms(d)
    del ms["specimen_temperature"]
    ms["frozen_phonons"] = {"rms_displacement_A": 0.076,
                            "label": "ASSUMPTION A7: 0.076 A per axis (inspected repository)"}
    cfg = load_pipeline_dict(copy.deepcopy(d), variant=THERMAL)
    assert cfg.sections["engine"]["multislice"]["frozen_phonons"]["rms_displacement_A"] == 0.076
    d["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="item 23"):
        load_pipeline_dict(d, variant=THERMAL)


def test_comparison_refuses_the_B36_demo_temperature():
    d = read_pipeline_file(SMOKE)
    d["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="B36"):
        load_pipeline_dict(d, variant=THERMAL)


# ---- terminations ------------------------------------------------------------------------------
def test_reconstruction_accepted_only_on_the_multislice_staircase_path():
    d = read_pipeline_file(SMOKE)
    _termination(d, FLIP)
    cfg = load_pipeline_dict(copy.deepcopy(d), variant=THERMAL, allow_test_only=True)
    assert cfg.cfg_b.value("surface_preparation_details")["termination"] == FLIP
    with pytest.raises(PipelineConfigError, match="engine 'geometric'"):
        load_pipeline_dict(copy.deepcopy(d), variant=None, allow_test_only=True)
    with pytest.raises(PipelineConfigError, match="needs frozen_phonons"):
        load_pipeline_dict(copy.deepcopy(d), variant="multislice_tiny", allow_test_only=True)
    _termination(d, "c(4x2)")                                # static: any frozen-phonon setting
    load_pipeline_dict(copy.deepcopy(d), variant="multislice_tiny", allow_test_only=True)
    _termination(d, "7x7")
    with pytest.raises(PipelineConfigError, match="not one of"):
        load_pipeline_dict(d, variant=THERMAL, allow_test_only=True)


def test_B26_cannot_carry_a_reconstruction():
    d = read_pipeline_file(SMOKE)
    d["cfg_b"]["parameters"]["surface_preparation_details"]["value"] = {
        "termination": "p(2x1)s", "overlayer": "none"}
    with pytest.raises(PipelineConfigError, match="B26"):
        load_pipeline_dict(d, variant=THERMAL)


# ---- engine runs -------------------------------------------------------------------------------
@needs_engine
def test_flipflop_configurations_per_realisation(tmp_path):
    """Flip-flop ensemble through the pipeline's structure and engine adapters (TEST_ONLY item 12
    in memory; pipeline.run itself refuses TEST_ONLY): states drawn per realisation from the
    [seed, realisation] generator, reproducible, recorded; realisations differ."""
    from reflection_holo.forward.dimer_ensemble import DimerFlipFlopPotential
    from reflection_holo.forward.multislice.backend import get_backend
    from reflection_holo.forward.multislice.engine import reflection_setup, run_realisation
    from reflection_holo.pipeline.engines import build_structure, multislice_objects, run_multislice
    d = read_pipeline_file(SMOKE)
    _termination(d, FLIP)
    cfg = load_pipeline_dict(d, variant=THERMAL, allow_test_only=True)
    s = build_structure(cfg)
    assert s.reconstruction is not None and s.reconstruction.n_cells > 0
    o = multislice_objects(s, cfg, require_backend=True)
    pot = o["potential"]
    assert isinstance(pot, DimerFlipFlopPotential)
    assert pot.frozen_phonons.rms_displacement_A == pytest.approx(U_295, rel=1e-15)
    assert pot.frozen_phonons.label.startswith("ASSUMPTION B35")
    assert pot.provenance()["dimer_flip_flop"]["label"].startswith("ASSUMPTION B37")
    setup = reflection_setup(o["cell"], potential=pot, beam=o["beam"], params=o["params"])
    be = get_backend("numpy", "complex64", 1)
    seed = cfg.value("engine", "multislice")["seed"]
    rec = []
    for r in (0, 1, 1):
        rz = pot.realise(grid=setup["grid"], dz_A=o["params"].dz_A, n_slices=setup["n_slices"],
                         backend=be, rng=np.random.default_rng([seed, r]))
        rec.append(rz.metadata)
    ff = [m["dimer_flip_flop"] for m in rec]
    assert ff[1] == ff[2] and rec[1]["displaced_positions_sha256"] == \
        rec[2]["displaced_positions_sha256"]                       # reproducible from (seed, r)
    assert ff[0]["states_sha256"] != ff[1]["states_sha256"]
    for f in ff:
        bits = np.unpackbits(np.frombuffer(bytes.fromhex(f["states_packbits_hex"]), np.uint8))
        flips = bits[:pot.n_cells]
        assert int(flips.sum()) == f["n_reversed"]
        assert 0.3 < f["n_reversed"] / pot.n_cells < 0.7           # p = 1/2 per cell
        import hashlib
        assert hashlib.sha256(np.ascontiguousarray(pot.positions_for(flips), "<f8").tobytes()
                              ).hexdigest() == f["configuration_positions_sha256"]
    # full engine path with its manifest: two realisations, different exit waves
    waves, cell, record = run_multislice(s, cfg, outputs_root=tmp_path / "outputs", run_name="e2ff")
    assert [w.realisation for w in waves] == [0, 1] and waves[0].seed == seed
    assert not np.array_equal(waves[0].psi, waves[1].psi)
    st = [w.metadata["potential"]["realised"]["dimer_flip_flop"]["states_sha256"] for w in waves]
    assert st[0] == ff[0]["states_sha256"] and st[1] == ff[1]["states_sha256"]
    assert record["termination"]["value"] == FLIP
    again = run_realisation(cell, potential=pot, beam=o["beam"], params=o["params"],
                            realisation=1, seed=seed)
    assert np.array_equal(again.psi, waves[1].psi)
    man = json.loads(open(record["engine_manifest"]).read())
    assert man["seeds"] == {"frozen_phonons": seed}


@needs_engine
def test_thermal_demo_variant_end_to_end(tmp_path):
    s = run(SMOKE, tmp_path / "th", variant=THERMAL)
    th = s["engine"]["thermal_model"]
    assert th["model"] == "B35" and th["specimen_temperature_K"] == 295.5
    assert th["u_per_axis_A"] == pytest.approx(U_295, rel=1e-15)
    assert th["temperature_assumption_id"] == "B36"
    assert s["engine"]["termination"]["value"] == "bulk"
    man = json.loads(open(s["engine"]["engine_manifest"]).read())
    assert man["seeds"] == {"frozen_phonons": 20260924}
    fp = man["extra"]["run_configuration"]["potential"]["frozen_phonons"]
    assert fp["rms_displacement_per_axis_A"] == pytest.approx(U_295, rel=1e-15)
    assert fp["label"].startswith("ASSUMPTION B35")
    assert "after squaring" in man["extra"]["ensemble_rule"]
