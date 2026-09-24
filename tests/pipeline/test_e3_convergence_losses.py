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
from reflection_holo.pipeline import PipelineConfigError, list_inputs, load_pipeline_dict, run
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


B39_VIS = dict(value=0.1, unit="none", label="ASSUMPTION", item=16, stands_in_for_item=16,
               assumption_id="B39", source="E3 test: demo loss-electron visibility (stand-in B39)")
B28_SHIFT = dict(value={"along_beam": 20.0, "perpendicular": 0.0}, unit="A", label="ASSUMPTION",
                 item=16, stands_in_for_item=16, assumption_id="B28",
                 source="E3 test: R2 shift (stand-in B28)")


def r2_dict(d, *, shift=True, vis=True):
    """The same configuration with an R2 self-reference (reflected flat area)."""
    P = d["cfg_b"]["parameters"]
    P["reference_model"]["value"] = "R2"
    P["reference_trajectory"]["value"] = "reflected_flat_area"
    if shift:
        d["sections"]["reference"]["shift"] = copy.deepcopy(B28_SHIFT)
    if vis:
        d["sections"]["optics"]["loss_electron_visibility"] = copy.deepcopy(B39_VIS)
    return d


def test_plasmon_loss_records_are_required_and_gated():
    """n (item 21) is required on every path; V_loss (item 16) is required with R2 and refused with
    the R1 vacuum reference, where it has no effect (audit A5 F10: before, it was required on every
    path, so every R1 comparison run needed a PROJECT_INPUT that cannot affect it)."""
    d = read_pipeline_file(SMOKE)
    load_pipeline_dict(copy.deepcopy(d), variant=None)
    assert "loss_electron_visibility" not in d["sections"]["optics"]      # R1 demo: not declared
    e = copy.deepcopy(d)
    del e["sections"]["optics"]["surface_plasmon_excitations"]
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(e, variant=None)
    assert 21 in exc.value.items
    e = copy.deepcopy(d)
    e["sections"]["optics"]["loss_electron_visibility"] = copy.deepcopy(B39_VIS)
    with pytest.raises(PipelineConfigError, match="R1.*refused rather than ignored"):
        load_pipeline_dict(e, variant=None)
    cfg = load_pipeline_dict(r2_dict(copy.deepcopy(d)), variant=None)
    assert cfg.rec("optics", "loss_electron_visibility").assumption_id == "B39"
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(r2_dict(copy.deepcopy(d), vis=False), variant=None)
    assert exc.value.items == [16] and "loss_electron_visibility" in str(exc.value)
    rows = [r for r in list_inputs(r2_dict(copy.deepcopy(d), vis=False), variant=None)
            if r["parameter"] == "sections.optics.loss_electron_visibility"]
    assert rows[0]["status"] == "MISSING"
    rows = [r for r in list_inputs(copy.deepcopy(d), variant=None)
            if r["parameter"] == "sections.optics.loss_electron_visibility"]
    assert rows[0]["status"] == "NOT USED on this path" and "R1" in rows[0]["detail"]
    e = r2_dict(copy.deepcopy(d))
    e["sections"]["optics"]["loss_electron_visibility"]["assumption_id"] = "B38"   # item 21 row
    with pytest.raises(PipelineConfigError, match="not mapped to PROJECT_INPUT item 16"):
        load_pipeline_dict(e, variant=None)
    e = copy.deepcopy(d)
    e["sections"]["optics"]["surface_plasmon_excitations"]["assumption_id"] = "B39"  # item 16 row
    with pytest.raises(PipelineConfigError, match="not mapped to PROJECT_INPUT item 21"):
        load_pipeline_dict(e, variant=None)
    for name, v in (("surface_plasmon_excitations", -0.1), ("loss_electron_visibility", 1.5),
                    ("surface_plasmon_excitations", float("nan"))):
        e = r2_dict(copy.deepcopy(d))
        e["sections"]["optics"][name]["value"] = v
        with pytest.raises(PipelineConfigError):
            load_pipeline_dict(e, variant=None)
    cfg = load_pipeline_dict(copy.deepcopy(d), variant="plasmon_losses")
    assert cfg.rec("optics", "surface_plasmon_excitations").assumption_id == "B38"
    assert cfg.rec("optics", "surface_plasmon_excitations").canonical_value == 1.246   # A5 F3
    e = copy.deepcopy(d)
    e["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="B38"):
        load_pipeline_dict(e, variant="plasmon_losses")
    e = r2_dict(copy.deepcopy(d))
    e["purpose"] = "comparison"
    with pytest.raises(PipelineConfigError, match="B39"):
        load_pipeline_dict(e, variant="plasmon_losses")


def test_r2_without_its_shift_is_a_missing_project_input_before_any_engine_run():
    """A5 F7: an R2 run (convergence ensemble or plane wave) without sections.reference.shift
    passed the gate and failed later (KeyError in design_extent, or after the engine run)."""
    d = read_pipeline_file(SMOKE)
    for variant, e in ((None, r2_dict(copy.deepcopy(d), shift=False)),
                       ("multislice_tiny", r2_dict(conv_dict(sep=False), shift=False))):
        with pytest.raises(MissingProjectInputError) as exc:
            load_pipeline_dict(e, variant=variant)
        assert exc.value.items == [16] and "sections.reference.shift" in str(exc.value)
    e = r2_dict(copy.deepcopy(d), shift=False, vis=False)                  # both named at once
    with pytest.raises(MissingProjectInputError) as exc:
        load_pipeline_dict(e, variant=None)
    assert exc.value.items == [16, 16]
    assert "shift" in str(exc.value) and "loss_electron_visibility" in str(exc.value)
    p_rows = [r for r in list_inputs(r2_dict(copy.deepcopy(d), shift=False), variant=None)
              if r["parameter"] == "sections.reference.shift"]
    assert p_rows[0]["status"] == "MISSING"


def test_plasmon_losses_reduce_the_contrast_used_by_the_noise_model(tmp_path):
    """Geometric smoke demo, R1: base (n = 0, B30) and variant plasmon_losses (n = 1.246, B38, E6's
    scripted value; A5 F3: the variant said 1.25 while quoting exp(-n/2) = 0.536). The
    empty-hologram contrast drops from 1 to exp(-1.246/2) = 0.536 (R1: V_loss has no effect and is
    not declared) and the predicted phase noise rises by exactly its inverse."""
    a = run(SMOKE, tmp_path / "base")
    b = run(SMOKE, tmp_path / "loss", variant="plasmon_losses")
    ca, cb = a["reference"]["fringe_contrast"], b["reference"]["fringe_contrast"]
    assert ca["used_by_the_noise_model"] == ca["lossless"] == 1.0
    assert cb["used_by_the_noise_model"] == pytest.approx(np.exp(-1.246 / 2), rel=1e-12)
    assert round(cb["used_by_the_noise_model"], 3) == 0.536                  # E6's printed value
    na = a["reconstruction"]["predicted_phase_noise_per_px"]["sigma_phi_rad"]
    nb = b["reconstruction"]["predicted_phase_noise_per_px"]["sigma_phi_rad"]
    assert nb / na == pytest.approx(np.exp(1.246 / 2), rel=1e-9)
    assert b["surface_plasmon_losses"]["mean_excitations_reference"] == 0.0
    assert b["surface_plasmon_losses"]["loss_visibility"] is None
    assert b["surface_plasmon_losses"]["fringe_factor"] == pytest.approx(np.exp(-0.623), rel=1e-15)
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


# ---------------------------------------------------------------------------------------------
# audit A5 F5: the R2 design extent adds the shift and the step phase
# ---------------------------------------------------------------------------------------------
def test_r2_design_extent_adds_the_shift_and_the_step_phase():
    """For R2 the member phase at a pixel is the object's flat-mirror member phase at Q minus that
    at Q' = Q + (-s_u/cos(theta), s_y, 0), each at the height of its terrace (optics.coherence.
    flat_mirror_member_phase, computed independently here for opposite members +t, -t on the
    boundary |t| = alpha): its odd part (linear in t) must reach, and not exceed, the design extent
    k alpha sqrt((|s_u| + 2 cos(theta) h_max)^2 + s_y^2), and its even part must stay below the
    design curvature. Before the fix the code took max(k alpha |s|, v_step): 0.2505 rad against the
    actual 0.3866 rad for s = (10, 0) A (A5 t10_r2_extent.py)."""
    import math
    from reflection_holo.geometry.wavelength import k_ang_per_A
    from reflection_holo.optics import coherence as C
    from reflection_holo.pipeline import convergence as CV
    from reflection_holo.pipeline.config import convergence_quadrature_from
    h = 5.4309 / 2.0                                                  # an a/2 step
    k = k_ang_per_A(200.0)
    for su, sy in ((10.0, 0.0), (40.0, 0.0), (0.0, 10.0), (-25.0, 15.0)):
        d = r2_dict(conv_dict(alpha_mrad=0.1, sep=False))
        d["sections"]["reference"]["shift"]["value"] = {"along_beam": su, "perpendicular": sy}
        cfg = load_pipeline_dict(d, variant="multislice_tiny")
        th = float(cfg.glancing_angle["value_rad"])
        alpha = 1e-4
        de = CV.design_extent(cfg, extent_x_A=100.0, length_z_A=1000.0, lowest_surface_x_A=40.0,
                              highest_surface_x_A=40.0 + h)
        X, Y, Z = np.array([30.0]), np.array([0.0]), np.array([1000.0])
        dx = -su / math.cos(th)
        odd = even = 0.0
        for phi in np.linspace(0.0, np.pi, 3601):
            p = {}
            for sgn in (1, -1):
                m = C.ConvergenceMember(index=0, t_a_rad=sgn * alpha * math.cos(phi),
                                        t_b_rad=sgn * alpha * math.sin(phi), weight=1.0)
                for xm1, xm2 in ((0.0, h), (h, 0.0), (0.0, 0.0)):
                    a = C.flat_mirror_member_phase(m, k_rad_per_A=k, theta0_rad=th,
                                                   exit_points_A=(X, Y, Z), mirror_height_A=xm1)
                    b = C.flat_mirror_member_phase(m, k_rad_per_A=k, theta0_rad=th,
                                                   exit_points_A=(X + dx, Y + sy, Z),
                                                   mirror_height_A=xm2)
                    p[(sgn, xm1, xm2)] = float((a - b)[0])
            for xm1, xm2 in ((0.0, h), (h, 0.0), (0.0, 0.0)):
                odd = max(odd, abs(p[(1, xm1, xm2)] - p[(-1, xm1, xm2)]) / 2)
                even = max(even, abs(p[(1, xm1, xm2)] + p[(-1, xm1, xm2)]) / 2)
        want = k * alpha * math.hypot(abs(su) + 2 * math.cos(th) * h, sy)
        assert de["v_design_rad"] == pytest.approx(want, rel=1e-12)
        assert de["v_design_rad"] >= de["v_coherence_rad"] and de["v_design_rad"] >= de["v_step_rad"]
        assert odd <= de["v_design_rad"] * (1 + 1e-9)                  # conservative
        assert odd >= de["v_design_rad"] * (1 - 1e-6)                  # and tight (3601 azimuths)
        # the independent phases are differences of O(1) direction cosines times k |Q|: rounding
        # of order k eps |Q| = 5.6e-11 rad, far below kappa (3e-7 rad) but above its 1e-8 margin
        assert even <= de["kappa_design_rad"] + 4 * k * np.finfo(float).eps * 1000.0
        if (su, sy) == (40.0, 0.0):
            # the gate consequence (A5): a 1 x 4 disc met 1e-2 at the old extent (bound 9.19e-3),
            # not at the sum (1.55e-2); curvature 0 in both calls isolates F5 (with kappa > 0 the
            # sqrt(2) of F8 enters the radial bound as well)
            old = max(k * alpha * math.hypot(su, sy), de["v_step_rad"])     # the former rule
            convergence_quadrature_from(cfg.cfg_b, dict(DISC4), design_phase_extent_rad=old,
                                        design_curvature_rad=0.0)
            with pytest.raises(ValueError, match="smallest quadrature"):
                convergence_quadrature_from(cfg.cfg_b, dict(DISC4),
                                            design_phase_extent_rad=de["v_design_rad"],
                                            design_curvature_rad=0.0)


# ---------------------------------------------------------------------------------------------
# audit A5 F6: member-job assembly checks realisations, seed, engine manifests and code identity
# ---------------------------------------------------------------------------------------------
REPO_CODE = dict(commit="c0ffee" * 6 + "c0ff", dirty=False, package_tree=dict(sha256="ab" * 32))


def _fake_member_jobs(root, cfg, q, *, extra_realisation=None, commit_of=None, tree_of=None,
                      wave_seed=None):
    """Synthetic member jobs (exit waves written with the repository's own writer, engine manifests
    reduced to the fields the assembly reads), as a job of this configuration would write them."""
    import hashlib
    from reflection_holo.forward.contracts import ExitWave
    from reflection_holo.forward.multislice import PLANE_TEXT
    from reflection_holo.forward.multislice.convergence import quadrature_sha256
    from reflection_holo.forward.multislice.exitwave_io import save_exit_wave
    from reflection_holo.pipeline import convergence as CV
    th0 = float(cfg.glancing_angle["value_rad"])
    m_cfg = cfg.value("engine", "multislice")
    for mem in q.members():
        d = root / f"m{mem.index}"
        (d / "outputs" / "exit_waves").mkdir(parents=True)
        (d / "outputs" / "manifests").mkdir(parents=True)
        reals = list(range(m_cfg["n_realisations"]))
        if extra_realisation is not None and mem.index == 0:
            reals.append(extra_realisation)
        files = []
        for r in reals:
            ew = ExitWave(psi=np.ones((8, 4), np.complex128), dx_A=0.1, dy_A=0.5, x0_A=0.0, y0_A=0.0,
                          plane=PLANE_TEXT, z_A=100.0, energy_keV=200.0,
                          theta_in_ext_rad=mem.glancing_angle_rad(th0), realisation=r,
                          seed=wave_seed, metadata=dict(
                              grid=dict(nx=8, ny=4, dx_A=0.1, dy_A=0.5),
                              bloch=dict(fy_per_A=0.0, direction_cosine_y=mem.direction_cosine_y())))
            p = d / "outputs" / "exit_waves" / f"x_m{mem.index:04d}_r{r:04d}.npz"
            save_exit_wave(p, ew)
            files.append(dict(path=str(p.relative_to(d)), realisation=r,
                              sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        repo = dict(REPO_CODE, commit=(commit_of or {}).get(mem.index, REPO_CODE["commit"]))
        if tree_of and mem.index in tree_of:
            repo["package_tree"] = dict(sha256=tree_of[mem.index])
        man = dict(repository=repo, seeds={"frozen_phonons": m_cfg["seed"]},
                   extra=dict(caller=dict(convergence=dict(member=dict(index=mem.index))),
                              run_configuration=dict(realisations=m_cfg["n_realisations"],
                                                     seed=m_cfg["seed"])))
        mp = d / "outputs" / "manifests" / "engine.json"
        mp.write_text(json.dumps(man))
        rec = dict(schema=CV.MEMBER_SCHEMA, member=mem.as_record(th0),
                   quadrature_member_sha256=quadrature_sha256(q, th0),
                   pipeline_config_sha256_resolved=cfg.sha256_resolved, exit_waves=files,
                   engine_manifest=str(mp.relative_to(d)),
                   engine_manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),
                   seed=m_cfg["seed"], n_realisations=m_cfg["n_realisations"],
                   code=CV.code_identity(repo), git_preflight=repo)
        (d / "member.json").write_text(json.dumps(rec))


def test_member_job_assembly_checks_realisations_seed_manifests_and_code(tmp_path):
    from reflection_holo.pipeline import convergence as CV
    cfg = load_pipeline_dict(conv_dict(quad=LINE2_Y), variant="multislice_tiny")
    q = CV.member_quadrature(cfg)
    assert cfg.value("engine", "multislice")["n_realisations"] == 1

    def load(root, code=REPO_CODE):
        return CV.load_member_jobs(cfg, root, q, code_state=code)

    ok = tmp_path / "ok"
    _fake_member_jobs(ok, cfg, q)
    waves, mans, code = load(ok)
    assert sorted(waves) == [0, 1] and code["assembling_run"]["commit"] == REPO_CODE["commit"]
    assert code["mixed_commits"] is False
    # another commit with the SAME package tree (same code): accepted, the mix is recorded
    mix = tmp_path / "mixed_commits"
    _fake_member_jobs(mix, cfg, q, commit_of={1: "deadbeef"})
    assert load(mix)[2]["mixed_commits"] is True
    cases = [("extra realisation", dict(extra_realisation=1), None, "realisations \\[0, 1\\]"),
             ("mixed code", dict(tree_of={1: "ee" * 32}), None, "different code"),
             ("wave seed", dict(wave_seed=7), None, "another seed"),
             ("assembling run", {}, dict(REPO_CODE, package_tree=dict(sha256="cd" * 32)),
              "other than the assembling run")]
    for name, kw, code, match in cases:
        root = tmp_path / name.replace(" ", "_")
        _fake_member_jobs(root, cfg, q, **kw)
        with pytest.raises(PipelineConfigError, match=match):
            load(root, code or REPO_CODE)
    # tampering with a member record or its manifest
    for name, edit, match in (
            ("manifest edited", lambda d: (d / "outputs/manifests/engine.json").write_text("{}"),
             "SHA-256 differs"),
            ("manifest missing", lambda d: (d / "outputs/manifests/engine.json").unlink(),
             "missing"),
            ("record without hash", lambda d: _edit_json(d / "member.json",
                                                         lambda r: r.pop("engine_manifest_sha256")),
             "lacks 'engine_manifest_sha256'"),
            ("record seed", lambda d: _edit_json(d / "member.json", lambda r: r.update(seed=3)),
             "ran with seed 3")):
        root = tmp_path / name.replace(" ", "_")
        _fake_member_jobs(root, cfg, q)
        edit(root / "m1")
        with pytest.raises(PipelineConfigError, match=match):
            load(root)


def _edit_json(p, fn):
    r = json.loads(p.read_text())
    fn(r)
    p.write_text(json.dumps(r))
