"""Structure building and engine dispatch of the pipeline.

Engines (``sections.engine.name``):
* "geometric": ``reflection_holo.forward.geometric`` (docs/05 section 4.5), always available.
* "multislice": imported LAZILY from ``reflection_holo.forward.multislice`` (the multislice agent's
  package) and ``reflection_holo.forward.cell``. Integration contract proposed to that agent
  (the only two names the pipeline calls; the types are the fixed ones of forward/contracts.py):

      reflection_holo.forward.cell.reflection_cell_from_structure(structure, *, cell_params)
          -> ReflectionCell
      reflection_holo.forward.multislice.simulate_exit_waves(cell, *, energy_keV,
          theta_in_ext_rad, engine_params) -> list[ExitWave]     (one per realisation)

  ``cell_params`` is ``sections.cell.multislice`` and ``engine_params`` is
  ``sections.engine.multislice`` (with ``absorptive_potential`` as its gated record value, and
  ``n_realisations`` and ``seed``), both handed over unchanged. If either module is absent, or
  lacks the entry point, the run fails with EngineUnavailableError naming what is missing; nothing
  falls back to the geometric engine.
Every ExitWave is validated (optics.darkfield.validate_exit_wave): pixel sizes, origins and plane
are read from the wave and asserted, never assumed.
"""
from __future__ import annotations

import importlib
from typing import Any

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.forward.contracts import ExitWave, ReflectionCell
from reflection_holo.forward.geometric import (GeometricParams, geometric_exit_wave,
                                               terrace_model_from_structure)
from reflection_holo.optics.darkfield import validate_exit_wave
from reflection_holo.pipeline.config import PipelineConfig, PipelineConfigError, Record
from reflection_holo.structure import OverlayerSpec, Staircase, build_si001_terraces

MULTISLICE_MODULE = "reflection_holo.forward.multislice"
CELL_MODULE = "reflection_holo.forward.cell"
MULTISLICE_ENTRY = "simulate_exit_waves"
CELL_ENTRY = "reflection_cell_from_structure"


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


def multislice_status() -> tuple[bool, str]:
    """(available, reason): whether the multislice engine can be called by the pipeline."""
    try:
        ms = importlib.import_module(MULTISLICE_MODULE)
    except ImportError as exc:
        return False, (f"{MULTISLICE_MODULE} is not importable yet ({type(exc).__name__}: {exc}); "
                       f"the multislice engine is being written by the multislice agent")
    try:
        cellmod = importlib.import_module(CELL_MODULE)
    except ImportError as exc:
        return False, f"{CELL_MODULE} is not importable ({type(exc).__name__}: {exc})"
    missing = []
    if not callable(getattr(ms, MULTISLICE_ENTRY, None)):
        missing.append(f"{MULTISLICE_MODULE}.{MULTISLICE_ENTRY}")
    if not callable(getattr(cellmod, CELL_ENTRY, None)):
        missing.append(f"{CELL_MODULE}.{CELL_ENTRY}")
    if missing:
        return False, (f"integration entry points missing: {missing} (see "
                       f"reflection_holo/pipeline/engines.py for the proposed signatures)")
    return True, "available"


def run_multislice(structure, cfg: PipelineConfig) -> tuple[list[ExitWave], ReflectionCell]:
    """Multislice engine through the integration contract of the module docstring."""
    ok, why = multislice_status()
    if not ok:
        raise EngineUnavailableError(f"engine 'multislice' unavailable: {why}")
    ms = importlib.import_module(MULTISLICE_MODULE)
    cellmod = importlib.import_module(CELL_MODULE)
    cell_params = cfg.sections["cell"].get("multislice")
    if cell_params is None:
        raise PipelineConfigError("sections.cell.multislice is required with the multislice engine")
    cell = getattr(cellmod, CELL_ENTRY)(structure, cell_params=dict(cell_params))
    if not isinstance(cell, ReflectionCell):
        raise EngineUnavailableError(f"{CELL_ENTRY} returned {type(cell).__name__}, not a "
                                     f"ReflectionCell")
    eng: dict[str, Any] = dict(cfg.value("engine", "multislice"))
    ap = eng["absorptive_potential"]
    eng["absorptive_potential"] = ap.value if isinstance(ap, Record) else ap
    eng["absorptive_potential_label"] = _label(ap) if isinstance(ap, Record) else None
    ga = cfg.glancing_angle
    waves = getattr(ms, MULTISLICE_ENTRY)(cell, energy_keV=BEAM_ENERGY_SUPPLIED_KEV,
                                         theta_in_ext_rad=ga["value_rad"], engine_params=eng)
    waves = list(waves)
    if not waves:
        raise EngineUnavailableError("the multislice engine returned no exit wave")
    seen = set()
    for w in waves:
        validate_exit_wave(w, energy_keV=BEAM_ENERGY_SUPPLIED_KEV, theta_in_ext_rad=ga["value_rad"],
                           rtol_angle=1e-12)
        if w.realisation in seen:
            raise ValueError(f"realisation {w.realisation} returned twice")
        seen.add(w.realisation)
        g0 = (waves[0].psi.shape, waves[0].dx_A, waves[0].dy_A, waves[0].x0_A, waves[0].y0_A,
              waves[0].plane, waves[0].z_A)
        if (w.psi.shape, w.dx_A, w.dy_A, w.x0_A, w.y0_A, w.plane, w.z_A) != g0:
            raise ValueError("exit waves of one run must share grid, origin and plane")
    return waves, cell
