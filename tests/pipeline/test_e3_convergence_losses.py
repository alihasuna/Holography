"""Pipeline: the convergence gate and ensemble, member jobs, and the surface-plasmon loss records
(report E3; PROJECT_INPUT items 3, 16, 21; registry rows B38, B39, B40).

The convergence cases are in-memory copies of configs/demo_smoke_si001.yaml (variant
multislice_tiny) with the demo stand-in B40 (a 10 urad uniform disc or line and, for R1, the
object-reference separation D0 = (0, 20, 0) A); B40 is demo-only, so these copies can run (a
pipeline run refuses TEST_ONLY values). The engine is UNVALIDATED for atomistic reflection: the
end-to-end test checks the member bookkeeping and the assembly, not the physics of the exit wave.
Exact equalities only (the assembly of saved member jobs performs the same operations on the same
exit waves as the in-process ensemble).
"""
import copy
import json

import numpy as np
import pytest
import yaml

from reflection_holo.io.config import MissingProjectInputError
from reflection_holo.pipeline import PipelineConfigError, load_pipeline_dict, run
from reflection_holo.pipeline.__main__ import main as cli_main
from reflection_holo.pipeline.config import read_pipeline_file
from reflection_holo.pipeline.engines import multislice_status

from conftest_pipeline import SMOKE

MS_OK, MS_WHY = multislice_status()
B40_CONV = dict(unit="mrad", label="ASSUMPTION", item=3, stands_in_for_item=3, assumption_id="B40",
                source="E3 test: demo convergent illumination (stand-in B40)")
B40_SEP = dict(value={"x": 0.0, "y": 20.0, "z": 0.0}, unit="A", label="ASSUMPTION", item=16,
               stands_in_for_item=16, assumption_id="B40",
               source="E3 test: R1 object-reference separation D0 (stand-in B40)")
DISC4 = dict(source_profile="uniform_disc", n_radial=1, n_azimuthal=4, line_azimuth_rad=None,
             tolerance=1e-2)
LINE2_Y = dict(source_profile="uniform_line", n_radial=2, n_azimuthal=None,
               line_azimuth_rad=float(np.pi / 2), tolerance=1e-2)     # two pure y (azimuthal) tilts


def conv_dict(alpha_mrad=0.01, quad=DISC4, sep=True):
    d = read_pipeline_file(SMOKE)
    d["cfg_b"]["parameters"]["convergence_semi_angle"] = dict(B40_CONV, value=alpha_mrad)
    d["sections"]["illumination"]["convergence_quadrature"] = copy.deepcopy(quad)
    if sep:
        d["sections"]["reference"]["separation"] = copy.deepcopy(B40_SEP)
    return d


# ---------------------------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------------------------
def test_gate_lifted_only_with_every_convergence_declaration():
    cfg = load_pipeline_dict(conv_dict(), variant="multislice_tiny")
    assert cfg.value("illumination", "convergence_quadrature")["n_azimuthal"] == 4
    with pytest.raises(PipelineConfigError, match="geometric engine is plane-wave only"):
        load_pipeline_dict(conv_dict(), variant=None)
    d = conv_dict()
    del d["sections"]["illumination"]["convergence_quadrature"]
    with pytest.raises(PipelineConfigError, match="convergence_quadrature"):
        load_pipeline_dict(d, variant="multislice_tiny")
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(conv_dict(sep=False), variant="multislice_tiny")
    assert 16 in exc.value.items
    d = conv_dict()
    d["cfg_b"]["parameters"]["convergence_semi_angle"]["assumption_id"] = "B21"   # plane wave row
    with pytest.raises(PipelineConfigError, match="B21"):
        load_pipeline_dict(d, variant="multislice_tiny")
    d = conv_dict(alpha_mrad=0.0)
    with pytest.raises(PipelineConfigError, match="B40"):                        # zero, B40 row
        load_pipeline_dict(d, variant="multislice_tiny")
    d = read_pipeline_file(SMOKE)                                                 # B21 plane wave
    d["sections"]["illumination"]["convergence_quadrature"] = dict(DISC4)
    with pytest.raises(PipelineConfigError, match="refused rather than ignored"):
        load_pipeline_dict(d, variant="multislice_tiny")
    d = read_pipeline_file(SMOKE)
    d["sections"]["reference"]["separation"] = dict(B40_SEP)
    with pytest.raises(PipelineConfigError, match="refused rather than ignored"):
        load_pipeline_dict(d, variant="multislice_tiny")
    d = conv_dict()
    d["sections"]["reference"]["aperture_passage"]["value"] = "second_aperture_hole"
    with pytest.raises(PipelineConfigError, match="condenser_biprism_pretilt"):
        load_pipeline_dict(d, variant="multislice_tiny")
    for bad in (dict(DISC4, n_radial=0), dict(DISC4, extra=1), dict(DISC4, source_profile="gauss"),
                {k: v for k, v in DISC4.items() if k != "tolerance"}):
        with pytest.raises(PipelineConfigError, match="convergence_quadrature"):
            load_pipeline_dict(conv_dict(quad=bad), variant="multislice_tiny")
    d = conv_dict()
    d["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="B40"):
        load_pipeline_dict(d, variant="multislice_tiny")


def test_supplied_convergence_passes_and_a_missing_one_fails():
    d = conv_dict()
    p = d["cfg_b"]["parameters"]["convergence_semi_angle"]
    for k in ("stands_in_for_item", "assumption_id"):
        p.pop(k)
    p.update(label="PROJECT_INPUT", supplied_by="Ali", supplied_on="2026-09-24",
             source="E3 test: fabricated supply record")
    cfg = load_pipeline_dict(copy.deepcopy(d), variant="multislice_tiny")
    assert cfg.cfg_b.parameters["convergence_semi_angle"].label == "PROJECT_INPUT"
    p.update(value=None)
    for k in ("supplied_by", "supplied_on"):
        p.pop(k)
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(d, variant="multislice_tiny")
    assert 3 in exc.value.items


def test_plasmon_loss_records_are_required_and_gated():
    d = read_pipeline_file(SMOKE)
    load_pipeline_dict(copy.deepcopy(d), variant=None)
    for name, item in (("surface_plasmon_excitations", 21), ("loss_electron_visibility", 16)):
        e = copy.deepcopy(d)
        del e["sections"]["optics"][name]
        with pytest.raises(MissingProjectInputError) as exc:
            load_pipeline_dict(e, variant=None)
        assert item in exc.value.items
    e = copy.deepcopy(d)
    e["sections"]["optics"]["loss_electron_visibility"]["assumption_id"] = "B38"   # item 21 row
    with pytest.raises(PipelineConfigError, match="not mapped to PROJECT_INPUT item 16"):
        load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    e["sections"]["optics"]["surface_plasmon_excitations"]["assumption_id"] = "B39"  # item 16 row
    with pytest.raises(PipelineConfigError, match="not mapped to PROJECT_INPUT item 21"):
        load_pipeline_dict(e, variant=None)
    for name, v in (("surface_plasmon_excitations", -0.1), ("loss_electron_visibility", 1.5),
                    ("surface_plasmon_excitations", float("nan"))):
        e = copy.deepcopy(d)
        e["sections"]["optics"][name]["value"] = v
        with pytest.raises(PipelineConfigError):
            load_pipeline_dict(e, variant=None)
    cfg = load_pipeline_dict(copy.deepcopy(d), variant="plasmon_losses")
    assert cfg.rec("optics", "surface_plasmon_excitations").assumption_id == "B38"
    e = copy.deepcopy(d)
    e["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="B39"):
        load_pipeline_dict(e, variant="plasmon_losses")


def test_plasmon_losses_reduce_the_contrast_used_by_the_noise_model(tmp_path):
    """Geometric smoke demo, R1: base (n = 0, B30) and variant plasmon_losses (n = 1.25, B38).
    The empty-hologram contrast drops from 1 to exp(-1.25/2) (R1: V_loss has no effect) and the
    predicted phase noise rises by exactly its inverse."""
    a = run(SMOKE, tmp_path / "base")
    b = run(SMOKE, tmp_path / "loss", variant="plasmon_losses")
    ca, cb = a["reference"]["fringe_contrast"], b["reference"]["fringe_contrast"]
    assert ca["used_by_the_noise_model"] == ca["lossless"] == 1.0
    assert cb["used_by_the_noise_model"] == pytest.approx(np.exp(-1.25 / 2), rel=1e-12)
    na = a["reconstruction"]["predicted_phase_noise_per_px"]["sigma_phi_rad"]
    nb = b["reconstruction"]["predicted_phase_noise_per_px"]["sigma_phi_rad"]
    assert nb / na == pytest.approx(np.exp(1.25 / 2), rel=1e-9)
    assert b["surface_plasmon_losses"]["mean_excitations_reference"] == 0.0
    assert b["surface_plasmon_losses"]["fringe_factor"] == pytest.approx(np.exp(-0.625), rel=1e-15)
    arr = np.load(tmp_path / "loss" / "arrays.npz")
    Ha, Hb = (np.load(tmp_path / p / "arrays.npz")["hologram_empty_noiseless"]
              for p in ("base", "loss"))
    assert Ha.mean() == pytest.approx(Hb.mean(), rel=1e-12)       # unfiltered: DC unchanged
    assert "hologram_object_counts" in arr.files


# ---------------------------------------------------------------------------------------------
# members and the job interface
# ---------------------------------------------------------------------------------------------
def test_members_cli_prints_the_job_list(tmp_path, capsys):
    p = tmp_path / "conv.yaml"
    p.write_text(yaml.safe_dump(conv_dict(), sort_keys=False))
    assert cli_main(["members", "--config", str(p), "--variant", "multislice_tiny"]) == 0
    t = json.loads(capsys.readouterr().out)
    assert t["n_members"] == 4 and len(t["quadrature"]["members"]) == 4
    assert abs(sum(m["weight"] for m in t["quadrature"]["members"]) - 1.0) <= 1e-15
    assert cli_main(["members", "--config", str(SMOKE)]) == 3             # plane wave: no members
    assert "no convergence ensemble" in capsys.readouterr().err


@pytest.mark.skipif(not MS_OK, reason=f"multislice engine unavailable: {MS_WHY}")
def test_quadrature_refused_against_the_computed_design_extent(capsys, tmp_path):
    """alpha = 0.1 mrad over the tiny cell: v = k alpha |E|_max = 2.98 rad; a 1 x 4 disc cannot
    reach 1e-6, the dry run refuses and names the smallest quadrature that would."""
    p = tmp_path / "conv.yaml"
    p.write_text(yaml.safe_dump(conv_dict(alpha_mrad=0.1, quad=dict(DISC4, tolerance=1e-6)),
                                sort_keys=False))
    rc = cli_main(["dry-run", "--config", str(p), "--variant", "multislice_tiny"])
    err = capsys.readouterr().err
    assert rc == 3 and "smallest quadrature" in err, err


@pytest.mark.skipif(not MS_OK, reason=f"multislice engine unavailable: {MS_WHY}")
def test_member_jobs_assemble_to_the_in_process_ensemble(tmp_path, capsys):
    """Two members (a uniform line of y tilts, the Bloch path end to end): each member run as a
    separate job (CLI run-member), assembled with run --members-dir, equals the in-process ensemble
    bit for bit; tampered or incomplete job sets are refused."""
    d = conv_dict(quad=LINE2_Y)
    p = tmp_path / "conv.yaml"
    p.write_text(yaml.safe_dump(d, sort_keys=False))
    jobs = tmp_path / "jobs"
    for k in (1, 0):
        rc = cli_main(["run-member", "--config", str(p), "--variant", "multislice_tiny",
                       "--member", str(k), "--out", str(jobs / f"m{k}")])
        assert rc == 0, capsys.readouterr().err
        rec = json.loads((jobs / f"m{k}" / "member.json").read_text())
        assert rec["member"]["index"] == k and rec["member"]["t_a_rad"] == pytest.approx(0.0,
                                                                                          abs=1e-20)
        assert abs(rec["member"]["direction_cosine_y"]) > 0                  # y tilt (Bloch)
        man = json.loads((jobs / f"m{k}" / rec["engine_manifest"]).read_text())
        assert man["extra"]["caller"]["convergence"]["member"]["index"] == k
    assert cli_main(["run-member", "--config", str(p), "--variant", "multislice_tiny",
                     "--member", "2", "--out", str(tmp_path / "bad")]) == 3   # no member 2
    capsys.readouterr()
    a = run(p, tmp_path / "assembled", variant="multislice_tiny", members_dir=jobs)
    b = run(p, tmp_path / "inprocess", variant="multislice_tiny")
    conv = a["engine"]["convergence"]
    assert conv["quadrature"]["n_members"] == 2 and "loaded from member jobs" in conv["member_origin"]
    assert b["engine"]["convergence"]["member_origin"] == "computed in this process"
    A, B = (np.load(tmp_path / q / "arrays.npz") for q in ("assembled", "inprocess"))
    for key in ("hologram_object_noiseless", "hologram_empty_noiseless", "hologram_object_counts",
                "phase_wrapped_raw"):
        assert np.array_equal(A[key], B[key], equal_nan=True), key
    cr = a["reference"]["fringe_contrast"]["convergence_coherence"]
    assert 0.9 < cr["median_over_lit_pixels"] <= 1.0
    assert a["hologram"]["object"]["n_members"] == 2
    # tampering: a member computed with another configuration, or a missing member
    rec_p = jobs / "m0" / "member.json"
    rec = json.loads(rec_p.read_text())
    rec["pipeline_config_sha256_resolved"] = "0" * 64
    rec_p.write_text(json.dumps(rec))
    with pytest.raises(PipelineConfigError, match="another configuration"):
        run(p, tmp_path / "t1", variant="multislice_tiny", members_dir=jobs)
    import shutil
    shutil.rmtree(jobs / "m0")
    with pytest.raises(PipelineConfigError, match="every member"):
        run(p, tmp_path / "t3", variant="multislice_tiny", members_dir=jobs)
    with pytest.raises(PipelineConfigError, match="no convergence ensemble|convergence 0"):
        run(SMOKE, tmp_path / "t4", members_dir=jobs)


@pytest.mark.skipif(not MS_OK, reason=f"multislice engine unavailable: {MS_WHY}")
def test_convergence_demo_config_passes_the_gate_and_every_member_check():
    """configs/demo_convergence_si001.yaml (stand-in B40): the dry run checks the declared 1 x 4
    quadrature against the design extent computed from the cell and runs the band and geometry
    assertions of all four members (no propagation)."""
    from reflection_holo.pipeline.config import load_pipeline_file
    from reflection_holo.pipeline.estimates import dry_run
    cfg = load_pipeline_file(SMOKE.parent / "demo_convergence_si001.yaml", variant=None)
    rep = dry_run(cfg)
    c = rep["convergence"]
    assert c["n_members"] == 4 and c["members_passing_band_and_geometry_checks"] == 4
    q = c["quadrature"]
    assert q["error_bound"] <= q["tolerance"] == 1e-2
    assert q["design_phase_extent_rad"] == pytest.approx(c["design_extent"]["v_design_rad"])
    assert c["design_extent"]["geometry"]["reference"] == "R1"
