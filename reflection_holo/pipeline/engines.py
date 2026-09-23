"""Structure building and engine dispatch of the pipeline.

Engines (``sections.engine.name``):
* "geometric": ``reflection_holo.forward.geometric`` (docs/05 section 4.5), always available.
* "multislice": the multislice agent's ``reflection_holo.forward.multislice`` with
  ``reflection_holo.forward.cell``, imported LAZILY (abTEM, GPL-3.0-or-later, is an optional
  dependency of its atomic potential and is never imported here). The adapter calls, with every
  argument taken from the configuration (no default):

      cell = forward.cell.build_reflection_cell(structure, **sections.cell.multislice)
      pot  = multislice.AtomicPotential(cell, parameterisation, physical_absorption (item 21),
                                        frozen_phonons, static_lattice_label)
      beam = multislice.SheetBeam(height_A, edge_A, x_bottom_A, theta_in_ext_rad, theta_label)
      params = multislice.MultisliceParams(energy_keV=200, nx, ny, dz_A, propagator, band_limit,
                                           backend, precision, threads, absorber,
                                           theta_out_ext_rad, buildup_depth_A)
      waves, engine_manifest = multislice.simulate(cell, potential=pot, beam=beam, params=params,
                                                   realisations, seed, outputs_root, ...)

  The mean inner potential of the potential actually used (``potentials.
  potential_mean_inner_potential_V``) must equal the value with which the glancing angle was
  computed (``sections.engine.multislice.potential_mip``, report D3 F16) to 5e-4 V, or the run
  fails (orchestrator decision after D3). If a module or name is missing the run fails with
  EngineUnavailableError; nothing falls back to the geometric engine.
Every ExitWave is validated (optics.darkfield.validate_exit_wave): pixel sizes, origins and plane
are read from the wave and asserted, never assumed.
"""
from __future__ import annotations

import importlib
import importlib.util

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.forward.contracts import ExitWave, ReflectionCell
from reflection_holo.forward.geometric import (GeometricParams, geometric_exit_wave,
                                               terrace_model_from_structure)
from reflection_holo.forward.geometric.height_field import (HeightField, HeightFieldParams,
                                                            height_field_exit_wave,
                                                            require_b4_scope_height_field)
from reflection_holo.optics.darkfield import validate_exit_wave
from reflection_holo.pipeline.config import PipelineConfig, PipelineConfigError, Record
from reflection_holo.structure import OverlayerSpec, Staircase, build_si001_terraces
from reflection_holo.structure.shapes import HalfTorus

MULTISLICE_MODULE = "reflection_holo.forward.multislice"
CELL_MODULE = "reflection_holo.forward.cell"
MULTISLICE_NAMES = ("AtomicPotential", "PhysicalAbsorption", "FrozenPhonons", "SheetBeam",
                    "MultisliceParams", "NumericalAbsorber", "simulate")
CELL_NAMES = ("build_reflection_cell",)
MIP_FUNCTION = ("reflection_holo.forward.multislice.potentials", "potential_mean_inner_potential_V")
MIP_TOL_V = 5e-4


class EngineUnavailableError(RuntimeError):
    """The selected engine cannot be imported or lacks the integration entry point."""


def _label(p) -> str:
    """Qualified evidence label of a CFG-B parameter or a pipeline Record for labelled builders."""
    lab = p.label
    aid = getattr(p, "assumption_id", None)
    item = getattr(p, "item", None)
    if lab == "ASSUMPTION" and aid:
        return f"ASSUMPTION {aid} (stands in for PROJECT_INPUT item {item})"
    if lab == "PROJECT_INPUT":
        return f"PROJECT_INPUT item {item} ({p.source})"
    return f"{lab} ({p.source})"


def build_structure(cfg: PipelineConfig):
    """Si(001) staircase from the configuration (structure.si001.build_si001_terraces)."""
    b = cfg.cfg_b
    st_rec: Record = cfg.rec("structure", "staircase")
    st = st_rec.value
    staircase = Staircase(edges=st["edges"], terrace_layers=tuple(st["terrace_layers"]),
                          terrace_widths=tuple(st["terrace_widths_periods"]),
                          boundary_step_layers=st["boundary_step_layers"])
    prep = b.value("surface_preparation_details")
    if not isinstance(prep, dict) or "termination" not in prep or "overlayer" not in prep:
        raise PipelineConfigError("cfg_b.surface_preparation_details (item 12) must state "
                                  "{termination, overlayer} for the structure builder")
    over = prep["overlayer"]
    lab12 = _label(b.parameters["surface_preparation_details"])
    if over == "none":
        overlayer = None
    elif isinstance(over, dict):
        overlayer = OverlayerSpec(material=over["material"], thickness_A=over["thickness_A"],
                                  density_g_cm3=over["density_g_cm3"], label=lab12)
    else:
        raise PipelineConfigError("surface_preparation_details.overlayer must be 'none' or "
                                  "{material, thickness_A, density_g_cm3}")
    a_A, unit = b.quantity("lattice_parameter")
    lp = b.parameters["lattice_parameter"]
    lat_label = f"{lp.label} ({lp.source})"
    return build_si001_terraces(
        azimuth_uvw=tuple(b.value("beam_azimuth_uvw")),
        azimuth_label=_label(b.parameters["beam_azimuth_uvw"]),
        staircase=staircase, edge_periods=cfg.value("structure", "edge_periods"),
        substrate_layers=cfg.value("structure", "substrate_layers"),
        first_terrace_backbond_uvw=tuple(st["first_terrace_backbond_uvw"]),
        termination=prep["termination"], overlayer=overlayer,
        vacuum_above_A=cfg.value("structure", "vacuum_above_A"),
        lattice_parameter_A=a_A, lattice_parameter_label=lat_label)


def illumination_kind(cfg: PipelineConfig) -> str:
    conv, _ = cfg.cfg_b.quantity("convergence_semi_angle")
    return "plane_wave" if conv == 0.0 else "convergent"


def run_geometric(structure, cfg: PipelineConfig):
    """Geometric engine: returns (exit waves, terrace model, GeometricRun)."""
    g = cfg.value("engine", "geometric")
    model = terrace_model_from_structure(structure)
    params = GeometricParams(
        exit_plane_pixel_A=(g["exit_plane_pixel_A"]["x"], g["exit_plane_pixel_A"]["y"]),
        n_y=g["n_y"], x_margin_A=g["x_margin_A"],
        periods_along_beam=cfg.value("cell", "periods_along_beam"),
        reflectivity_amplitude=g["reflectivity_amplitude"],
        invisibility_tol_cycles=g["invisibility_tol_cycles"])
    ga = cfg.glancing_angle
    run = geometric_exit_wave(model, energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
                              theta_in_ext_rad=ga["value_rad"],
                              theta_label=_label(cfg.rec("illumination", "glancing_angle")),
                              params=params, illumination=illumination_kind(cfg),
                              beam=cfg.value("optics", "selected_beam"))
    validate_exit_wave(run.exit_wave, energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
                       theta_in_ext_rad=ga["value_rad"])
    return [run.exit_wave], model, run


def feature_shape(cfg: PipelineConfig) -> HalfTorus:
    """The surface feature of ``sections.structure.feature`` (PROJECT_INPUT item 13) as the shared
    shape of ``structure.shapes`` (read, not changed, by this path)."""
    rec: Record = cfg.rec("structure", "feature")
    v = rec.value
    if v["kind"] != "half_torus":
        raise PipelineConfigError(f"feature kind {v['kind']!r} is not implemented")
    return HalfTorus(center_y_A=float(v["center_y_A"]), center_z_A=float(v["center_z_A"]),
                     major_radius_A=float(v["major_radius_A"]),
                     minor_radius_A=float(v["minor_radius_A"]), kind=v["sub_kind"],
                     label=_label(rec), source=rec.source)


def feature_height_field(cfg: PipelineConfig, shape: HalfTorus) -> HeightField:
    """Top-atomic-layer height field of the feature on the flat Si(001) surface: heights
    ``shape.layer_height_A`` quantised to a/4 (a = cfg_b lattice_parameter), the flat surrounding
    surface at 0, the field [0, field_length_A] along the beam sampled every surface_dz_A."""
    b = cfg.cfg_b
    prep = b.value("surface_preparation_details")
    if not isinstance(prep, dict) or prep.get("termination") != "bulk" or prep.get("overlayer") != "none":
        raise PipelineConfigError("the feature path needs cfg_b.surface_preparation_details "
                                  "{termination: bulk, overlayer: none} (item 12)")
    a_A, unit = b.quantity("lattice_parameter")
    if unit != "A":
        raise PipelineConfigError("cfg_b.lattice_parameter must be in A")
    layer = float(a_A) / 4.0
    g = cfg.value("engine", "geometric")

    def h(y, z):
        return shape.layer_height_A(y, z, layer_spacing_A=layer)

    return HeightField(
        height_fn=h, profile="piecewise_constant", layer_spacing_A=layer, z_start_A=0.0,
        field_length_A=float(g["field_length_A"]), surface_dz_A=float(g["surface_dz_A"]),
        upstream_level_A=0.0,
        description=(f"half torus {shape.kind} (R = {shape.major_radius_A} A, r = "
                     f"{shape.minor_radius_A} A, centre (y, z) = ({shape.center_y_A}, "
                     f"{shape.center_z_A}) A) on a flat, step-free Si(001) surface: ideal top atomic "
                     f"layer HalfTorus.layer_height_A with layer spacing a/4 = {layer} A"),
        label=shape.label, source=shape.source)


def run_geometric_feature(cfg: PipelineConfig):
    """Height-field geometric engine for the surface feature: returns (exit waves, shape, height
    field, HeightFieldRun). The B4 scope check (azimuth, termination, overlayer, plane wave,
    specular beam) runs first."""
    shape = feature_shape(cfg)
    hf = feature_height_field(cfg, shape)
    b = cfg.cfg_b
    prep = b.value("surface_preparation_details")
    n_layers = int(round(shape.minor_radius_A / hf.layer_spacing_A))
    b4 = require_b4_scope_height_field(
        hf, azimuth_uvw=tuple(b.value("beam_azimuth_uvw")), termination=prep["termination"],
        overlayer=None if prep["overlayer"] == "none" else prep["overlayer"],
        illumination=illumination_kind(cfg), beam=cfg.value("optics", "selected_beam"),
        layer_index_parity="any" if n_layers >= 1 else "even")
    b4["azimuth_label"] = _label(b.parameters["beam_azimuth_uvw"])
    g = cfg.value("engine", "geometric")
    params = HeightFieldParams(
        exit_plane_pixel_A=(g["exit_plane_pixel_A"]["x"], g["exit_plane_pixel_A"]["y"]),
        n_y=g["n_y"], x_margin_A=g["x_margin_A"], reflectivity_amplitude=g["reflectivity_amplitude"])
    ga = cfg.glancing_angle
    run = height_field_exit_wave(hf, energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
                                 theta_in_ext_rad=ga["value_rad"],
                                 theta_label=_label(cfg.rec("illumination", "glancing_angle")),
                                 params=params, b4=b4)
    validate_exit_wave(run.exit_wave, energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
                       theta_in_ext_rad=ga["value_rad"])
    return [run.exit_wave], shape, hf, run


def multislice_status() -> tuple[bool, str]:
    """(available, reason): whether the multislice engine can be called by the pipeline."""
    try:
        ms = importlib.import_module(MULTISLICE_MODULE)
    except ImportError as exc:
        return False, (f"{MULTISLICE_MODULE} is not importable yet ({type(exc).__name__}: {exc}); "
                       f"the multislice engine is being written by the multislice agent")
    try:
        cellmod = importlib.import_module(CELL_MODULE)
        potmod = importlib.import_module(MIP_FUNCTION[0])
    except ImportError as exc:
        return False, f"{CELL_MODULE} or {MIP_FUNCTION[0]} not importable ({exc})"
    missing = [f"{MULTISLICE_MODULE}.{n}" for n in MULTISLICE_NAMES if not hasattr(ms, n)]
    missing += [f"{CELL_MODULE}.{n}" for n in CELL_NAMES if not hasattr(cellmod, n)]
    if not callable(getattr(potmod, MIP_FUNCTION[1], None)):
        missing.append(".".join(MIP_FUNCTION))
    if missing:
        return False, f"integration names missing: {missing}"
    if importlib.util.find_spec("abtem") is None:
        return False, ("the optional dependency abTEM 1.0.10 (GPL-3.0-or-later) is not installed; "
                       "the atomic potential needs it (report D3)")
    return True, "available"


def backend_status(backend: str) -> tuple[bool, str]:
    """(available, reason) of an array backend of the multislice engine (audit A3 m5): "numpy" is
    always available; "cupy" needs ``import cupy`` to work and at least one visible GPU."""
    if backend != "cupy":
        return True, f"{backend}: available"
    if importlib.util.find_spec("cupy") is None:
        return False, ("backend cupy requested but cupy is not installed in this Python "
                       "environment (install it with GPU support, or use the numpy variant)")
    try:
        cp = importlib.import_module("cupy")
        n = int(cp.cuda.runtime.getDeviceCount())
    except Exception as exc:                          # import or CUDA runtime failure
        return False, f"backend cupy requested but cupy/CUDA is not usable ({type(exc).__name__}: {exc})"
    if n < 1:
        return False, "backend cupy requested but no GPU is visible (getDeviceCount() = 0)"
    return True, f"cupy: available, {n} GPU(s) visible"


def require_engine(cfg: PipelineConfig) -> None:
    """Pre-flight of the selected engine BEFORE any computation (audit A3 m5): the multislice module
    and, for backend "cupy", an importable cupy with a visible GPU. EngineUnavailableError
    otherwise."""
    if cfg.value("engine", "name") != "multislice":
        return
    ok, why = multislice_status()
    if not ok:
        raise EngineUnavailableError(f"engine 'multislice' unavailable: {why}")
    ok, why = backend_status(cfg.value("engine", "multislice")["backend"])
    if not ok:
        raise EngineUnavailableError(why)


def reflection_cell(structure, cfg: PipelineConfig) -> ReflectionCell:
    cellmod = importlib.import_module(CELL_MODULE)
    cp = dict(cfg.sections["cell"]["multislice"])
    cell = cellmod.build_reflection_cell(structure, **cp)
    if not isinstance(cell, ReflectionCell):
        raise EngineUnavailableError(f"build_reflection_cell returned {type(cell).__name__}")
    return cell


def multislice_objects(structure, cfg: PipelineConfig, *, require_backend: bool) -> dict:
    """Cell, potential, beam and parameters of the multislice engine from the configuration, with
    the mean-inner-potential consistency check (module docstring). No propagation.
    ``require_backend``: True for a run (the array backend must be usable); the dry run passes False
    so that the geometry checks run on a machine without the GPU and reports the backend
    separately."""
    if require_backend:
        require_engine(cfg)
    else:
        ok, why = multislice_status()
        if not ok:
            raise EngineUnavailableError(f"engine 'multislice' unavailable: {why}")
    ms = importlib.import_module(MULTISLICE_MODULE)
    potmod = importlib.import_module(MIP_FUNCTION[0])
    m = cfg.value("engine", "multislice")
    ga = cfg.glancing_angle
    th = ga["value_rad"]
    cell = reflection_cell(structure, cfg)
    pa_rec: Record = m["physical_absorption"]
    pa = ms.PhysicalAbsorption(model=pa_rec.value["model"], ratio=pa_rec.value["ratio"],
                               label=_label(pa_rec))
    fp_cfg = m["frozen_phonons"]
    if fp_cfg == "none":
        fp, static = None, m["static_lattice_label"]
    else:
        fp = ms.FrozenPhonons(rms_displacement_A=fp_cfg["rms_displacement_A"],
                              label=fp_cfg["label"])
        static = None
    pot = ms.AtomicPotential(cell, parameterisation=m["parameterisation"], physical_absorption=pa,
                             frozen_phonons=fp, static_lattice_label=static)
    mip = float(getattr(potmod, MIP_FUNCTION[1])(pot))
    mip_cfg = float(m["potential_mip"].canonical_value)
    mip_check = dict(potential_mip_V=mip, configured_potential_mip_V=mip_cfg,
                     configured_label=m["potential_mip"].label,
                     configured_source=m["potential_mip"].source, tolerance_V=MIP_TOL_V,
                     V0_used_for_glancing_angle_V=ga.get("V0_V"),
                     V0_source=ga.get("V0_source"))
    if abs(mip - mip_cfg) > MIP_TOL_V:
        raise PipelineConfigError(
            f"the potential's mean inner potential is {mip:.6f} V but the configuration declares "
            f"{mip_cfg} V (sections.engine.multislice.potential_mip); refraction angles would be "
            f"inconsistent with the exit waves")
    if ga.get("rule") is not None and ga.get("V0_source") != "sections.engine.multislice.potential_mip":
        raise PipelineConfigError("with the multislice engine the glancing angle must be computed "
                                  "from the potential's MIP (V0_source "
                                  "'sections.engine.multislice.potential_mip'; report D3)")
    lay = cell.metadata["layout"]
    sb = m["sheet_beam"]
    beam = ms.SheetBeam(height_A=sb["height_A"], edge_A=sb["edge_A"],
                        x_bottom_A=lay["highest_surface_x_A"] + sb["x_bottom_above_highest_surface_A"],
                        theta_in_ext_rad=th, theta_label=_label(cfg.rec("illumination",
                                                                         "glancing_angle")))
    params = ms.MultisliceParams(
        energy_keV=BEAM_ENERGY_SUPPLIED_KEV, nx=m["nx"], ny=m["ny"], dz_A=m["dz_A"],
        propagator=m["propagator"], band_limit=m["band_limit"], backend=m["backend"],
        precision=m["precision"], threads=cfg.value("runtime", "threads"),
        absorber=ms.NumericalAbsorber(strength_V=m["absorber"]["strength_V"],
                                      profile=m["absorber"]["profile"]),
        theta_out_ext_rad=th, buildup_depth_A=m["buildup_depth_A"])
    return dict(ms=ms, cell=cell, potential=pot, beam=beam, params=params, mip_check=mip_check,
                engine_params=m)


def run_multislice(structure, cfg: PipelineConfig, *, outputs_root, run_name: str
                   ) -> tuple[list[ExitWave], ReflectionCell, dict]:
    """Multislice engine through the adapter of the module docstring. Returns the exit waves, the
    reflection cell and a record (engine manifest path, MIP check, parameters)."""
    o = multislice_objects(structure, cfg, require_backend=True)
    ms, cell, beam, params, m = o["ms"], o["cell"], o["beam"], o["params"], o["engine_params"]
    th = cfg.glancing_angle["value_rad"]
    src = cfg.source_path
    waves, man = ms.simulate(cell, potential=o["potential"], beam=beam, params=params,
                             realisations=m["n_realisations"], seed=m["seed"],
                             outputs_root=outputs_root, run_name=f"{run_name}_multislice",
                             save_waves=m["save_exit_waves"], config=src,
                             input_paths=[src] if src else [],
                             caller_record=dict(
                                 caller="reflection_holo.pipeline (audit A3 m1)",
                                 purpose=cfg.purpose, pipeline_run_name=cfg.run_name,
                                 variant=cfg.variant, test_only=cfg.test_only,
                                 pipeline_config_path=src,
                                 pipeline_config_sha256_file=cfg.sha256_file,
                                 pipeline_config_sha256_resolved=cfg.sha256_resolved))
    waves = list(waves)
    if not waves:
        raise EngineUnavailableError("the multislice engine returned no exit wave")
    seen = set()
    g0 = (waves[0].psi.shape, waves[0].dx_A, waves[0].dy_A, waves[0].x0_A, waves[0].y0_A,
          waves[0].plane, waves[0].z_A)
    for w in waves:
        validate_exit_wave(w, energy_keV=BEAM_ENERGY_SUPPLIED_KEV, theta_in_ext_rad=th,
                           rtol_angle=1e-12)
        if w.realisation in seen:
            raise ValueError(f"realisation {w.realisation} returned twice")
        seen.add(w.realisation)
        if (w.psi.shape, w.dx_A, w.dy_A, w.x0_A, w.y0_A, w.plane, w.z_A) != g0:
            raise ValueError("exit waves of one run must share grid, origin and plane")
    record = dict(engine_manifest=str(man), mip_check=o["mip_check"], params=params.to_dict(),
                  beam=beam.describe(waves[0].metadata["beam"]["wavelength_A"]),
                  validation_status=waves[0].metadata.get("validation_status"),
                  cell_layout=cell.metadata["layout"])
    return waves, cell, record
