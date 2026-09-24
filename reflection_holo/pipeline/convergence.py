"""Convergence ensembles and surface-plasmon losses in the pipeline (report E3; H2 N3; E6 M1, M2).

* Losses (both engines, every run): ``plasmon_loss`` builds the optics.inelastic model from the
  REQUIRED records sections.optics.surface_plasmon_excitations (item 21; stand-in B38) and
  sections.optics.loss_electron_visibility (item 16; stand-in B39) and the reference model (R1: the
  reference arm carries no loss; R2: both arms carry n). The pipeline forms UNFILTERED holograms.
* Convergence (multislice engine only; gate in pipeline.config._check_convergence): the members of
  the declared quadrature (optics.coherence) are independent engine runs
  (forward.multislice.convergence.simulate_member), in this process or as separate jobs
  (``run_member_job``; CLI ``run-member``) assembled by ``load_member_jobs`` (CLI
  ``run --members-dir``). The quadrature's design phase extent is COMPUTED here from the geometry
  (``design_extent``, conservative over the whole exit plane) and the declared quadrature is refused
  if its error bound exceeds the declared tolerance.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A
from reflection_holo.optics import coherence as C
from reflection_holo.optics.inelastic import SurfacePlasmonLoss, for_reference_model
from reflection_holo.pipeline.config import (PipelineConfig, PipelineConfigError,
                                             convergence_quadrature_from)

ENERGY_FILTER_LABEL = ("ASSUMPTION: unfiltered holograms (every detected electron counts; an energy "
                       "filter is NOT IMPLEMENTED in the pipeline, report E3)")
MEMBER_SCHEMA = "reflection_holo.pipeline.convergence_member/1"


def _label(rec) -> str:
    from reflection_holo.pipeline.engines import _label as lab
    return lab(rec)


# ------------------------------------------------------------------------------------------------
# surface-plasmon losses
# ------------------------------------------------------------------------------------------------
def plasmon_loss(cfg: PipelineConfig) -> SurfacePlasmonLoss:
    """The loss model of the run (optics.inelastic.for_reference_model), all inputs from records."""
    n = cfg.rec("optics", "surface_plasmon_excitations")
    v = cfg.rec("optics", "loss_electron_visibility")
    return for_reference_model(cfg.cfg_b.value("reference_model"),
                               mean_excitations=float(n.canonical_value),
                               excitation_label=_label(n),
                               loss_visibility=float(v.canonical_value),
                               visibility_label=_label(v), energy_filter="none",
                               energy_filter_label=ENERGY_FILTER_LABEL)


# ------------------------------------------------------------------------------------------------
# convergence: quadrature, design extent, members
# ------------------------------------------------------------------------------------------------
def is_convergent(cfg: PipelineConfig) -> bool:
    conv, _ = cfg.cfg_b.quantity("convergence_semi_angle")
    return conv != 0.0


def member_quadrature(cfg: PipelineConfig) -> C.ConvergenceQuadrature:
    """The declared quadrature with a zero design extent: the MEMBER LIST only (identical to the
    checked quadrature's; the error bound is checked by ``checked_quadrature``)."""
    if not is_convergent(cfg):
        raise PipelineConfigError("the configuration has no convergence ensemble "
                                  "(cfg_b.convergence_semi_angle = 0: a plane wave)")
    cq = cfg.value("illumination", "convergence_quadrature")
    return convergence_quadrature_from(cfg.cfg_b, cq, design_phase_extent_rad=0.0,
                                       design_curvature_rad=0.0)


def design_extent(cfg: PipelineConfig, *, extent_x_A: float, length_z_A: float,
                  lowest_surface_x_A: float, highest_surface_x_A: float) -> dict:
    """Phase extent v and curvature kappa that the quadrature must integrate (optics.coherence),
    conservative over the whole exit plane x in [0, extent_x] (DERIVED_HERE, report E3 2.3-2.4):

    * R1 (condenser-biprism pre-tilt): member phase k [t_a E_a + t_b E_b] - kappa_s with
      E_a = 2c (x - x_m) - 2s L_z - c D0_x + s D0_z, E_b = D0_y, kappa_s <= k alpha^2/2
      |mirror(b0).D0 - 2 s x_m| (x_m a surface height between the lowest and highest terrace);
    * R2 (shift (s_u, s_y) on the detector, exit-plane dx = -s_u/cos(theta)): E = (-s_u, s_y),
      kappa <= k alpha^2/2 s |dx|;
    * step phase: v_step = (4 pi h_max / lambda) cos(theta) alpha, h_max the highest minus the
      lowest terrace (docs/03 section 4).
    v_design = max(k alpha |E|_max, v_step)."""
    th = float(cfg.glancing_angle["value_rad"])
    k = k_ang_per_A(BEAM_ENERGY_SUPPLIED_KEV)
    lam = wavelength_A(BEAM_ENERGY_SUPPLIED_KEV)
    alpha, _ = cfg.cfg_b.quantity("convergence_semi_angle")
    c, s = math.cos(th), math.sin(th)
    ref = cfg.cfg_b.value("reference_model")
    heights = (float(lowest_surface_x_A), float(highest_surface_x_A))
    if ref == "R1":
        d = cfg.rec("reference", "separation").canonical_value
        D0 = np.array([d["x"], d["y"], d["z"]], float)
        Ea = [2 * c * (x - xm) - 2 * s * length_z_A - c * D0[0] + s * D0[2]
              for x in (0.0, float(extent_x_A)) for xm in heights]
        E_max = max(math.hypot(e, D0[1]) for e in Ea)
        mb0 = C.mirror_x(C.central_direction(th))
        par = max(abs(float(mb0 @ D0) - 2 * s * xm) for xm in heights)
        geometry = dict(reference="R1", separation_A=D0.tolist(),
                        E_a_range_A=[min(Ea), max(Ea)], E_b_A=float(D0[1]))
    elif ref == "R2":
        sh = cfg.rec("reference", "shift").canonical_value
        su, sy = float(sh["along_beam"]), float(sh["perpendicular"])
        E_max = math.hypot(su, sy)
        par = s * abs(su / c)
        geometry = dict(reference="R2", shift_A=[su, sy])
    else:
        raise PipelineConfigError(f"reference model {ref!r} under convergence: R1 and R2 only")
    h_max = heights[1] - heights[0]
    v_coh = k * alpha * E_max
    v_step = 4 * math.pi * h_max / lam * math.cos(th) * alpha
    kappa = 0.5 * k * alpha ** 2 * par * (1.0 + alpha ** 2)
    return dict(v_design_rad=max(v_coh, v_step), kappa_design_rad=kappa,
                v_coherence_rad=v_coh, v_step_rad=v_step, E_perp_max_A=E_max,
                step_height_max_A=h_max, semi_angle_rad=alpha, theta0_rad=th, geometry=geometry,
                rule="optics.coherence module docstring; pipeline.convergence.design_extent")


def checked_quadrature(cfg: PipelineConfig, *, cell) -> tuple[C.ConvergenceQuadrature, dict]:
    """The declared quadrature with the design extent of ``design_extent`` for this cell; raises
    PipelineConfigError (with the smallest quadrature that would pass) if its error bound exceeds
    the declared tolerance."""
    lay = cell.metadata["layout"]
    de = design_extent(cfg, extent_x_A=float(cell.extent_x_A), length_z_A=float(cell.length_z_A),
                       lowest_surface_x_A=float(lay["lowest_surface_x_A"]),
                       highest_surface_x_A=float(lay["highest_surface_x_A"]))
    cq = cfg.value("illumination", "convergence_quadrature")
    try:
        q = convergence_quadrature_from(cfg.cfg_b, cq, design_phase_extent_rad=de["v_design_rad"],
                                        design_curvature_rad=de["kappa_design_rad"])
    except ValueError as exc:
        raise PipelineConfigError(f"sections.illumination.convergence_quadrature: {exc}") from exc
    return q, de


def members_table(cfg: PipelineConfig) -> dict:
    """The job list of a convergence ensemble (CLI ``members``): one engine run per member."""
    from reflection_holo.forward.multislice.convergence import quadrature_sha256
    q = member_quadrature(cfg)
    th = float(cfg.glancing_angle["value_rad"])
    return dict(n_members=q.n_members, quadrature=q.as_record(th),
                quadrature_member_sha256=quadrature_sha256(q, th),
                pipeline_config_sha256_resolved=cfg.sha256_resolved, variant=cfg.variant,
                note="run each member with `run-member --member K` (any order, any machine); "
                     "assemble with `run --members-dir DIR`; the error bound of the quadrature is "
                     "checked against the cell by run-member, run and dry-run")


# ------------------------------------------------------------------------------------------------
# engine runs of the members
# ------------------------------------------------------------------------------------------------
def _validate_member_waves(waves, member, th0, *, what: str):
    from reflection_holo.optics.darkfield import validate_exit_wave
    th = member.glancing_angle_rad(th0)
    for w in waves:
        validate_exit_wave(w, energy_keV=BEAM_ENERGY_SUPPLIED_KEV, theta_in_ext_rad=th,
                           rtol_angle=1e-12)
        b = (w.metadata or {}).get("bloch")
        if b is None or float(b["direction_cosine_y"]) != float(member.direction_cosine_y()):
            raise ValueError(f"{what}: exit wave of member {member.index} does not carry the "
                             f"member's y direction cosine {member.direction_cosine_y()!r}")


def _grid_key(w):
    return (w.psi.shape, w.dx_A, w.dy_A, w.x0_A, w.y0_A, w.plane, w.z_A)


def engine_members(structure, cfg: PipelineConfig, *, outputs_root, run_name: str,
                   members_dir) -> tuple[dict, object, dict]:
    """Exit waves of every member: computed here (members_dir None; one ``simulate_member`` per
    member, each with its own engine manifest) or loaded from member jobs (``load_member_jobs``).
    Returns ({member index: [ExitWave]}, cell, record)."""
    from reflection_holo.forward.multislice.convergence import (check_members, quadrature_sha256,
                                                                simulate_member)
    from reflection_holo.pipeline.engines import multislice_objects
    o = multislice_objects(structure, cfg, require_backend=members_dir is None)
    cell, beam, params, m = o["cell"], o["beam"], o["params"], o["engine_params"]
    q, de = checked_quadrature(cfg, cell=cell)
    th0 = float(cfg.glancing_angle["value_rad"])
    checks = check_members(cell, potential=o["potential"], beam=beam, params=params, quadrature=q)
    src = cfg.source_path
    manifests = {}
    if members_dir is None:
        waves = {}
        for mem in q.members():
            ws, man = simulate_member(
                cell, potential=o["potential"], beam=beam, params=params, quadrature=q,
                member_index=mem.index, realisations=m["n_realisations"], seed=m["seed"],
                outputs_root=outputs_root, run_name=f"{run_name}_multislice",
                save_waves=m["save_exit_waves"], config=src, input_paths=[src] if src else [],
                caller_record=_caller(cfg))
            waves[mem.index] = list(ws)
            manifests[mem.index] = str(man)
        origin = "computed in this process"
    else:
        waves, manifests = load_member_jobs(cfg, members_dir, q)
        origin = f"loaded from member jobs in {members_dir}"
    g0 = None
    for mem in q.members():
        _validate_member_waves(waves[mem.index], mem, th0, what=origin)
        for w in waves[mem.index]:
            if g0 is None:
                g0 = _grid_key(w)
            elif _grid_key(w) != g0:
                raise ValueError("exit waves of every member must share grid, origin and plane")
    w0 = waves[q.members()[0].index][0]
    record = dict(engine_manifests={str(k): v for k, v in manifests.items()},
                  mip_check=o["mip_check"], params=params.to_dict(),
                  central_beam=beam.describe(w0.metadata["beam"]["wavelength_A"]),
                  validation_status=w0.metadata.get("validation_status"),
                  cell_layout=cell.metadata["layout"],
                  convergence=dict(quadrature=q.as_record(th0),
                                   quadrature_member_sha256=quadrature_sha256(q, th0),
                                   design_extent=de, member_origin=origin,
                                   band_and_geometry_checks=[dict(member=c["member"]["index"],
                                                                  geometry_passed=c["geometry_passed"])
                                                             for c in checks]))
    return waves, cell, record


def _caller(cfg: PipelineConfig) -> dict:
    return dict(caller="reflection_holo.pipeline (convergence member; report E3)",
                purpose=cfg.purpose, pipeline_run_name=cfg.run_name, variant=cfg.variant,
                test_only=cfg.test_only, pipeline_config_path=cfg.source_path,
                pipeline_config_sha256_file=cfg.sha256_file,
                pipeline_config_sha256_resolved=cfg.sha256_resolved)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_member_job(cfg: PipelineConfig, member_index: int, out_dir, *, allow_no_git: bool) -> dict:
    """One member of the ensemble as a separate job (CLI ``run-member``): the git state and the
    engine are checked first; the structure, the cell and EVERY member's assertions are built and
    run (cheap), then the member's engine run writes its exit waves (always saved) and engine
    manifest under out_dir/outputs, and out_dir/member.json records the member, the quadrature
    identity, the configuration hash and the SHA-256 of every exit-wave file."""
    from reflection_holo.forward.multislice.convergence import (check_members, quadrature_sha256,
                                                                simulate_member)
    from reflection_holo.pipeline.engines import (build_structure, multislice_objects,
                                                  require_engine)
    from reflection_holo.pipeline.run import _prepare_out
    from reflection_holo.provenance.manifest import require_git_state
    if cfg.test_only:
        raise PipelineConfigError("the configuration contains TEST_ONLY values: a member job "
                                  "refuses them (A2c G3)")
    if not is_convergent(cfg):
        raise PipelineConfigError("run-member needs a convergence ensemble "
                                  "(cfg_b.convergence_semi_angle > 0)")
    git = require_git_state(allow_no_git=allow_no_git)
    require_engine(cfg)
    q0 = member_quadrature(cfg)
    try:
        q0.member(member_index)                            # index checked before any computation
    except ValueError as exc:
        raise PipelineConfigError(f"--member {member_index!r}: {exc}") from exc
    out = _prepare_out(out_dir)
    structure = build_structure(cfg)
    o = multislice_objects(structure, cfg, require_backend=True)
    cell, beam, params, m = o["cell"], o["beam"], o["params"], o["engine_params"]
    q, de = checked_quadrature(cfg, cell=cell)
    check_members(cell, potential=o["potential"], beam=beam, params=params, quadrature=q)
    th0 = float(cfg.glancing_angle["value_rad"])
    src = cfg.source_path
    waves, man = simulate_member(
        cell, potential=o["potential"], beam=beam, params=params, quadrature=q,
        member_index=int(member_index), realisations=m["n_realisations"], seed=m["seed"],
        outputs_root=out / "outputs", run_name=f"{cfg.run_name}_multislice", save_waves=True,
        config=src, input_paths=[src] if src else [], caller_record=_caller(cfg))
    mem = q.member(member_index)
    _validate_member_waves(waves, mem, th0, what="member job")
    files = []
    for w in waves:
        p = out / "outputs" / "exit_waves" / f"{cfg.run_name}_multislice_m{mem.index:04d}_r{w.realisation:04d}.npz"
        files.append(dict(path=str(p.relative_to(out)), sha256=_sha256_file(p),
                          realisation=int(w.realisation)))
    rec = dict(schema=MEMBER_SCHEMA, member=mem.as_record(th0),
               quadrature_member_sha256=quadrature_sha256(q, th0),
               quadrature=q.as_record(), design_extent=de,
               pipeline_config_sha256_resolved=cfg.sha256_resolved,
               pipeline_config_sha256_file=cfg.sha256_file, pipeline_config_path=src,
               variant=cfg.variant, run_name=cfg.run_name,
               engine_manifest=str(Path(man).relative_to(out)), exit_waves=files,
               git_preflight=git)
    with open(out / "member.json", "x", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, default=str)
        fh.write("\n")
    return rec


def load_member_jobs(cfg: PipelineConfig, members_dir, q: C.ConvergenceQuadrature
                     ) -> tuple[dict, dict]:
    """Load and assert the member jobs under members_dir (every */member.json): the same resolved
    configuration (SHA-256) and quadrature member identity, each member exactly once, every
    exit-wave file unchanged (SHA-256) and read with its plane asserted (exitwave_io)."""
    from reflection_holo.forward.multislice import PLANE_TEXT, load_exit_wave
    from reflection_holo.forward.multislice.convergence import quadrature_sha256
    root = Path(members_dir)
    th0 = float(cfg.glancing_angle["value_rad"])
    want_q = quadrature_sha256(q, th0)
    recs = sorted(root.glob("*/member.json"))
    if not recs:
        raise PipelineConfigError(f"no member job (*/member.json) under {root}")
    waves, manifests = {}, {}
    for rp in recs:
        r = json.loads(rp.read_text())
        where = str(rp)
        if r.get("schema") != MEMBER_SCHEMA:
            raise PipelineConfigError(f"{where}: schema {r.get('schema')!r} != {MEMBER_SCHEMA}")
        if r.get("pipeline_config_sha256_resolved") != cfg.sha256_resolved:
            raise PipelineConfigError(f"{where}: computed with another configuration or variant "
                                      f"(resolved SHA-256 {r.get('pipeline_config_sha256_resolved')}"
                                      f" != {cfg.sha256_resolved})")
        if r.get("quadrature_member_sha256") != want_q:
            raise PipelineConfigError(f"{where}: another quadrature (member identity)")
        k = int(r["member"]["index"])
        if k in waves:
            raise PipelineConfigError(f"{where}: member {k} present twice")
        ws = []
        for f in r["exit_waves"]:
            p = rp.parent / f["path"]
            if _sha256_file(p) != f["sha256"]:
                raise PipelineConfigError(f"{p}: SHA-256 differs from the member record")
            ws.append(load_exit_wave(p, expected_plane=PLANE_TEXT))
        waves[k] = sorted(ws, key=lambda w: w.realisation)
        manifests[k] = str(rp.parent / r["engine_manifest"])
    want = {m.index for m in q.members()}
    if set(waves) != want:
        raise PipelineConfigError(f"member jobs under {root}: have {sorted(waves)}, need every "
                                  f"member {sorted(want)}")
    return waves, manifests


# ------------------------------------------------------------------------------------------------
# member phases on the detector (report E3 2.3-2.4)
# ------------------------------------------------------------------------------------------------
def exit_points_of_detector(placement, *, x0_A: float, theta_rad: float, z_A: float) -> tuple:
    """Exit-plane points Q = (x, y, z) imaged at the detector pixels: u = (x0 - x) cos(theta)
    (optics.projection), y the perpendicular coordinate, z the exit plane."""
    U, Y = np.meshgrid(np.asarray(placement.u_A, float), np.asarray(placement.y_A, float),
                       indexing="ij")
    X = float(x0_A) - U / math.cos(theta_rad)
    return X, Y, np.full(X.shape, float(z_A))
