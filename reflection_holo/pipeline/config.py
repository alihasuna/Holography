"""Pipeline configuration: a schema extending CFG-B, gated like every configuration of the package.

docs/05 section 0 criterion 5 (no result may depend on a default silently substituted for a missing
PROJECT_INPUT: such runs fail), sections 4.5 and 5; docs/06 (PROJECT_INPUT items 1-22, and item 23
"specimen temperature during holography", proposed by report E2).

File layout (YAML; duplicate keys refused anywhere, ``io.config.load_yaml_unique``):

    pipeline_schema: 1
    run_name: <name>
    purpose: "demo; not comparable to experiment" | "comparison"
    description: <text>
    cfg_b: {schema_version, config_id: CFG-B, name: si001_patterned, status, description,
            parameters: {...}}                         # a CFG-B configuration (io.config schema)
    sections: {structure, cell, engine, illumination, optics, reference, detector,
               reconstruction, quantification, runtime, outputs}
    variants: {<name>: {description, sections: {...partial overrides...},
                        cfg_b_parameters: {<name>: <whole CFG-B record>}}}      # optional

The ``cfg_b`` block is validated by ``reflection_holo.io.config.load_config_dict(level="run")``,
after the pipeline has inserted the glancing angle it computes (``illumination.glancing_angle``,
item 7; the angle is never typed when the rule form is used). CFG-B's own gate therefore applies
to items 3, 4, 5, 7, 8, 9, 11, 12, 13, 14, 15, 20.

Pipeline parameters that are docs/06 items are RECORDS with the CFG-B keys {value, unit, label,
source, item, stands_in_for_item, assumption_id, note} and the same rules (``_gate_record``): a
PROJECT_INPUT is null (missing: the run FAILS naming the item) or has a value whose source says
"supplied by <name> <YYYY-MM-DD>"; an ASSUMPTION must stand in for exactly that item with an
assumption_id that ``reflection_holo/io/assumption_registry.yaml`` maps to it; TEST_ONLY is accepted
from in-memory test dictionaries only (never from a file); any other label fails. A missing record
fails like a null one. Settings that are no docs/06 item (grid sizes, seeds, thread count, ROI) are
plain values, all REQUIRED: nothing has a default.

Units: io.config.UNITS plus three pipeline units (``PIPELINE_UNITS``): "e/px" (dose), "counts/e"
(gain) and "deg" (angle). Values are converted to A, rad, keV, V.

Variants (``--variant``) deep-merge a partial ``sections`` mapping over the base; a variant is an
explicit choice of the caller, recorded in every output. A variant may also REPLACE whole CFG-B
parameter records (``cfg_b_parameters``, report E4: e.g. the continuum-oxide stand-in B41 of item
12 on top of a clean base); every replaced record passes the same CFG-B gate, and the resolved
CFG-B block is hashed and recorded.

Overlayer (docs/06 item 12; report E4): cfg_b.surface_preparation_details.overlayer is "none" or a
complete continuum oxide {model: continuum_oxide, material, thickness_A, density_g_cm3,
consumed_layers, V_real_V, V_imag_V, vacuum_edge_width_A, interface_width_A,
amorphous_si_thickness_A (+ amorphous_si_V_real_V, amorphous_si_V_imag_V when > 0)}, every key
REQUIRED and carrying the record's label (``OXIDE_KEYS``; structure.oxide.ContinuumOxideSpec);
anything else is refused (audit A3 M6). The pipeline builds conformal layers only (no per-terrace
overrides), on the staircase path, with the bulk termination.
"""
from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reflection_holo.geometry.errors import GeometryError
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.io.config import (SUPPLY_KEYS, UNITS, ConfigError, LoadedConfig,
                                       MissingProjectInputError, assumption_registry,
                                       canonical_sha256, check_supply, demo_only_stand_ins,
                                       load_config_dict, load_yaml_unique)
from reflection_holo.io.labels import EVIDENCE_LABELS, TEST_ONLY_LABEL, require_evidence_label

PIPELINE_SCHEMA = 1
PURPOSES = ("demo; not comparable to experiment", "comparison")
BLOCKING_ITEMS = (3, 4, 5, 7, 8, 11, 12, 15)                 # docs/06 "(blocking)"
PIPELINE_UNITS: dict[str, tuple[str, float | None]] = dict(UNITS)
PIPELINE_UNITS.update({"e/px": ("dose_per_pixel", 1.0), "counts/e": ("gain", 1.0),
                       "deg": ("angle", math.pi / 180.0), "K": ("temperature", 1.0)})
CANONICAL = {"length": "A", "angle": "rad", "energy": "keV", "potential": "V", "none": "none",
             "dose_per_pixel": "e/px", "gain": "counts/e", "temperature": "K"}
RECORD_KEYS_REQUIRED = ("value", "label", "source", "unit")
RECORD_KEYS_OPTIONAL = ("item", "stands_in_for_item", "assumption_id", "note") + SUPPLY_KEYS
TOP_KEYS_REQUIRED = ("pipeline_schema", "run_name", "purpose", "description", "cfg_b", "sections")
TOP_KEYS_OPTIONAL = ("variants",)
ENGINES = ("geometric", "multislice")
PROJECTION_REFERENCES = ("lowest_terrace_top", "flat_surface")   # staircase / feature path
GLANCING_RULES = ("internal_bragg_external_angle",)
V0_SOURCES = ("cfg_b.mean_inner_potential_V", "sections.engine.multislice.potential_mip")
MS_KEYS = ("parameterisation", "physical_absorption", "frozen_phonons", "static_lattice_label",
           "potential_mip", "sheet_beam", "nx", "ny", "dz_A", "propagator", "band_limit",
           "backend", "precision", "absorber", "buildup_depth_A", "n_realisations", "seed",
           "save_exit_waves")
MS_CELL_KEYS = ("vacuum_above_A", "depth_below_A", "bulk_absorber_A", "top_absorber_A",
                "entrance_vacuum_z_A")
# Frozen phonons (report E2): "none" (static lattice, labelled by static_lattice_label); the sourced
# thermal model {model: THERMAL_MODEL_B35} with the specimen temperature (PROJECT_INPUT item 23, key
# sections.engine.multislice.specimen_temperature, REQUIRED with this model: no default); or the
# fixed per-axis u {rms_displacement_A, label} (the form used for model_assumptions A7 of the
# inspected repository; kept working, refused by purpose "comparison" because item 23 is then
# not represented).
THERMAL_MODEL_B35 = "si_heacock2021_linear_B"
MS_KEYS_OPTIONAL = ("specimen_temperature",)
FIXED_U_KEYS = {"rms_displacement_A", "label"}


class PipelineConfigError(ConfigError):
    """Invalid pipeline configuration."""


# --------------------------------------------------------------------------------------------------
# Schema: section -> name -> spec. Record specs: ("record", item or None, dimension, kind).
# Plain specs: ("plain", kind, extra). Everything listed is REQUIRED unless marked optional.
# --------------------------------------------------------------------------------------------------
def _rec(item, dimension, kind, optional=False):
    return dict(type="record", item=item, dimension=dimension, kind=kind, optional=optional)


def _plain(kind, optional=False, **extra):
    return dict(type="plain", kind=kind, optional=optional, **extra)


SECTIONS: dict[str, dict[str, dict]] = {
    "structure": {
        # exactly one of staircase (item 11) and feature (item 13) is given (``_check_structure``);
        # the three plain settings belong to the staircase path (atomistic builder) only
        "staircase": _rec(11, "none", "staircase", optional=True),
        "feature": _rec(13, "none", "feature", optional=True),
        "edge_periods": _plain("int_pos", optional=True),
        "substrate_layers": _plain("int_ge4", optional=True),
        "vacuum_above_A": _plain("float_pos", optional=True),
    },
    "cell": {
        "periods_along_beam": _plain("int_pos"),
        "multislice": _plain("mapping", optional=True),
    },
    "engine": {
        "name": _plain("enum", choices=ENGINES),
        "geometric": _plain("mapping", optional=True),
        "multislice": _plain("mapping", optional=True),
    },
    "illumination": {
        "glancing_angle": _rec(7, "angle_or_rule", "glancing"),
        "angle_calibration_sigma": _rec(7, "angle", "positive"),
        "wavelength_sigma_rel": _rec(1, "none", "positive"),
        # report E3: the declared quadrature of a convergence ensemble; REQUIRED with a non-zero
        # cfg_b.convergence_semi_angle (item 3), refused with a zero one (CONVERGENCE_KEYS)
        "convergence_quadrature": _plain("mapping", optional=True),
    },
    "optics": {
        "selected_beam": _rec(4, "none", "beam"),
        "projection_reference": _plain("enum", choices=PROJECTION_REFERENCES),
        "lens_transfer": _plain("enum", choices=("none",)),
        # report E3 (E6 M1, M2): surface-plasmon losses in hologram formation: the mean
        # excitation number of the object path per reflection (item 21: an energy-filtered EELS of
        # the specular beam at the working angle; stand-in B38), REQUIRED; the mutual visibility
        # of the loss electrons of the two arms (item 16; stand-in B39), REQUIRED with an R2
        # reference and refused with R1/R3, where it has no effect (``_check_reference``; A5 F10)
        "surface_plasmon_excitations": _rec(21, "none", "nonnegative"),
        "loss_electron_visibility": _rec(16, "none", "unit_interval", optional=True),
    },
    "reference": {
        "carrier_fringe_spacing": _rec(16, "length", "positive"),
        "carrier_direction": _rec(16, "angle", "finite"),
        "amplitude_ratio": _rec(16, "none", "positive"),
        "aperture_passage": _rec(15, "none", "aperture_passage"),
        # the self-reference shift: REQUIRED with an R2 reference (``_check_reference``; A5 F7)
        "shift": _rec(16, "length", "pixel_pair", optional=True),
        # report E3: separation D0 (x, y, z; cell frame, A) from the reference-arm point to the
        # object-arm exit-plane point superposed by the biprism; required by an R1 convergence
        # ensemble only (refused otherwise)
        "separation": _rec(16, "length", "vector3", optional=True),
        "relative_phase_rad": _plain("float"),
    },
    "detector": {
        "pixel_pitch": _rec(5, "length", "pixel_size"),
        "magnification": _rec(5, "none", "positive"),
        "dose": _rec(6, "dose_per_pixel", "positive"),
        "gain": _rec(6, "gain", "positive"),
        "mtf": _rec(6, "none", "mtf"),
        "roi_shape": _plain("int_pair"),
        "alignment": _plain("enum", choices=("centre", "field_of_view")),
        "noise_seed": _plain("seed"),
    },
    "reconstruction": {
        "processing": _rec(19, "none", "reconstruction"),
    },
    "quantification": {
        "processing": _rec(19, "none", "quantification"),
        "feature_processing": _rec(19, "none", "feature_processing", optional=True),
    },
    "runtime": {
        "threads": _plain("int_pos"),
    },
    "outputs": {
        "quicklooks": _plain("bool"),
    },
}

RECON_KEYS = {"search_radius_fraction": "fraction", "exclusion_radius_fraction": "fraction",
              "subpixel": ("none", "dft_ratio"), "mask_radius_fraction": "fraction",
              "apodisation": ("none", "hann"), "reference_correction": ("none", "divide_empty"),
              "empty_min_visibility": "fraction", "unwrapping": ("none", "itoh_raster")}
QUANT_KEYS = {"edge_margin_resolutions": "positive", "branch_rule": ("lattice_constraint",),
              "max_layers": "int_pos", "n_sigma": "positive", "min_region_px": "int_pos",
              "min_relative_amplitude": "fraction"}
STAIRCASE_KEYS = ("edges", "terrace_layers", "terrace_widths_periods", "boundary_step_layers",
                  "first_terrace_backbond_uvw")
GEOMETRIC_KEYS = {"exit_plane_pixel_A": "xy_pos", "n_y": "int_pos", "x_margin_A": "float_pos",
                  "reflectivity_amplitude": "float_pos", "invisibility_tol_cycles": "float_nonneg"}
# feature path (agent T2): the height-field engine needs the field along the beam and its sampling
GEOMETRIC_FEATURE_KEYS = {"field_length_A": "float_pos", "surface_dz_A": "float_pos"}
FEATURE_KINDS = ("half_torus",)
FEATURE_SUB_KINDS = ("trench", "ridge")
FEATURE_KEYS = ("kind", "sub_kind", "center_y_A", "center_z_A", "major_radius_A", "minor_radius_A")
FEATURE_QUANT_KEYS = {"max_phase_step_rad": "positive"}
PATTERN_FROM_FEATURE = "sections.structure.feature"
# The registry maps stand-in ids to docs/06 items only. Item-13 stand-ins whose model_assumptions
# row states something else than the declared feature are refused here (agent T2): B27 states that
# there is NO feature; B33 is the demo trench, B34 the demo ridge (proposed rows, report T2).
FEATURE_STAND_IN_SUB_KIND = {"B27": None, "B33": "trench", "B34": "ridge"}
APERTURE_PASSAGES = ("second_aperture_hole", "condenser_biprism_pretilt", "no_aperture")


# --------------------------------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Record:
    section: str
    name: str
    value: Any
    canonical_value: Any
    canonical_unit: str
    unit: str
    label: str
    source: str
    item: int | None
    stands_in_for_item: int | None
    assumption_id: str | None
    note: str | None
    supply: dict | None = None            # {supplied_by, supplied_on} of a supplied PROJECT_INPUT


@dataclass
class PipelineConfig:
    run_name: str
    purpose: str
    description: str
    variant: str | None
    sections: dict                        # plain values and Record objects
    cfg_b: LoadedConfig
    cfg_b_raw: dict
    glancing_angle: dict                  # value_rad, rule, label, assumption_id, ...
    source_path: str | None
    sha256_file: str | None
    sha256_resolved: str                  # canonical hash of the resolved (variant-merged) config
    test_only: bool
    raw: dict = field(default_factory=dict, repr=False)

    def rec(self, section: str, name: str) -> Record:
        r = self.sections[section][name]
        if not isinstance(r, Record):
            raise PipelineConfigError(f"{section}.{name} is not a record")
        return r

    def value(self, section: str, name: str):
        v = self.sections[section][name]
        return v.canonical_value if isinstance(v, Record) else v

    def records(self) -> list[Record]:
        """Every Record of the sections, including those nested in engine parameter mappings
        (sections.engine.multislice.physical_absorption, potential_mip)."""
        return _all_records(self.sections)


def _all_records(sections: dict) -> list[Record]:
    out = []
    for sec in sections.values():
        for v in sec.values():
            if isinstance(v, Record):
                out.append(v)
            elif isinstance(v, dict):
                out.extend(w for w in v.values() if isinstance(w, Record))
    return out


# --------------------------------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------------------------------
def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _fail(where: str, msg: str):
    raise PipelineConfigError(f"{where}: {msg}")


def _check_plain(where: str, spec: dict, v):
    k = spec["kind"]
    ok = {
        "int_pos": lambda: _is_int(v) and v >= 1,
        "int_ge4": lambda: _is_int(v) and v >= 4,
        "float_pos": lambda: _is_num(v) and v > 0,
        "float": lambda: _is_num(v),
        "bool": lambda: isinstance(v, bool),
        "seed": lambda: _is_int(v) and v >= 0,
        "mapping": lambda: isinstance(v, dict) and bool(v),
        "enum": lambda: v in spec["choices"],
        "int_pair": lambda: isinstance(v, list) and len(v) == 2 and all(_is_int(a) and a >= 2
                                                                         for a in v),
    }[k]()
    if not ok:
        extra = f" one of {spec['choices']}" if k == "enum" else f" ({k})"
        _fail(where, f"must be{extra}, got {v!r}")
    return copy.deepcopy(v)


def _unit(where: str, dimension: str, unit):
    if not isinstance(unit, str) or unit not in PIPELINE_UNITS:
        _fail(where, f"unknown unit {unit!r} (units: {sorted(PIPELINE_UNITS)})")
    dim, factor = PIPELINE_UNITS[unit]
    if dimension == "angle_or_rule":
        if dim not in ("angle", "none"):
            _fail(where, f"unit must be an angle unit, or 'none' for the rule form; got {unit!r}")
        return dim, factor
    if dim != dimension:
        _fail(where, f"needs a unit of {dimension}; {unit!r} is {dim}")
    return dim, factor


def _check_record_kind(where: str, kind: str, v, dim: str):
    def bad(what):
        _fail(where, f"value must be {what}, got {v!r}")
    if kind == "positive":
        if not (_is_num(v) and v > 0):
            bad("a finite positive number")
    elif kind == "finite":
        if not _is_num(v):
            bad("a finite number")
    elif kind == "nonnegative":
        if not (_is_num(v) and v >= 0):
            bad("a finite number >= 0")
    elif kind == "unit_interval":
        if not (_is_num(v) and 0 <= v <= 1):
            bad("a finite number in [0, 1]")
    elif kind == "vector3":
        if not (isinstance(v, dict) and set(v) == {"x", "y", "z"}
                and all(_is_num(a) for a in v.values())):
            bad("{x, y, z} (finite; cell frame)")
    elif kind == "glancing":
        if dim == "angle":
            if not (_is_num(v) and v > 0):
                bad("a positive angle")
        elif not (isinstance(v, dict) and set(v) == {"rule", "reflection_hkl", "V0_source"}
                  and v["rule"] in GLANCING_RULES and isinstance(v["reflection_hkl"], list)
                  and len(v["reflection_hkl"]) == 3 and all(_is_int(a) for a in v["reflection_hkl"])
                  and v["V0_source"] in V0_SOURCES):
            bad(f"a positive angle, or {{rule: one of {GLANCING_RULES}, reflection_hkl: [h,k,l], "
                f"V0_source: one of {V0_SOURCES}}}")
    elif kind == "beam":
        if v != "specular":
            bad("'specular' (the only beam the pipeline selects)")
    elif kind == "aperture_passage":
        if v not in APERTURE_PASSAGES:
            bad(f"one of {APERTURE_PASSAGES}")
    elif kind == "mtf":
        if v != "none":
            bad("'none' (an ideal detector; MTF NOT IMPLEMENTED)")
    elif kind == "pixel_size":
        if not (isinstance(v, dict) and set(v) == {"along_beam", "perpendicular"}
                and all(_is_num(a) and a > 0 for a in v.values())):
            bad("{along_beam: >0, perpendicular: >0}")
    elif kind == "pixel_pair":
        if not (isinstance(v, dict) and set(v) == {"along_beam", "perpendicular"}
                and all(_is_num(a) for a in v.values()) and any(v.values())):
            bad("{along_beam, perpendicular} (finite, not both zero)")
    elif kind == "staircase":
        if not (isinstance(v, dict) and set(v) == set(STAIRCASE_KEYS)):
            bad(f"a mapping with exactly the keys {STAIRCASE_KEYS}")
        if v["edges"] not in ("transverse", "parallel"):
            bad("edges 'transverse' or 'parallel'")
        for key in ("terrace_layers", "terrace_widths_periods", "first_terrace_backbond_uvw"):
            if not (isinstance(v[key], list) and v[key] and all(_is_int(a) for a in v[key])):
                bad(f"{key} a list of integers")
        if not _is_int(v["boundary_step_layers"]):
            bad("boundary_step_layers an integer")
    elif kind == "mapping":
        if not (isinstance(v, dict) and v):
            bad("a non-empty mapping (handed to the engine)")
    elif kind == "temperature":
        if not (_is_num(v) and v > 0):
            bad("a finite positive absolute temperature")
    elif kind == "reconstruction":
        if not isinstance(v, dict):
            bad("a mapping")
        none = v.get("reference_correction") == "none"
        if none and "object_min_visibility" not in v:
            _fail(where, "reference_correction 'none' requires object_min_visibility (the minimum "
                         "local fringe visibility of the OBJECT hologram, (0, 1]; A2c residual R1)")
        if not none and "object_min_visibility" in v:
            _fail(where, "object_min_visibility applies only to reference_correction 'none'")
        keys = dict(RECON_KEYS, object_min_visibility="fraction") if none else RECON_KEYS
        _check_mapping(where, v, keys)
    elif kind == "quantification":
        _check_mapping(where, v, QUANT_KEYS)
    elif kind == "feature_processing":
        _check_mapping(where, v, FEATURE_QUANT_KEYS)
        if not v["max_phase_step_rad"] < math.pi:
            bad("max_phase_step_rad below pi (Itoh unwrapping needs |true phase step| < pi per "
                "pixel; the wrapped difference itself never exceeds pi)")
    elif kind == "feature":
        if not (isinstance(v, dict) and set(v) == set(FEATURE_KEYS)):
            bad(f"a mapping with exactly the keys {FEATURE_KEYS} (all required, lengths in A)")
        if v["kind"] not in FEATURE_KINDS:
            bad(f"kind one of {FEATURE_KINDS}")
        if v["sub_kind"] not in FEATURE_SUB_KINDS:
            bad(f"sub_kind one of {FEATURE_SUB_KINDS}")
        for key in FEATURE_KEYS[2:]:
            if not _is_num(v[key]):
                bad(f"{key} a finite number (A)")
        if not 0.0 < v["minor_radius_A"] < v["major_radius_A"]:
            bad("0 < minor_radius_A < major_radius_A")
    else:  # pragma: no cover
        raise PipelineConfigError(f"schema error: unknown record kind {kind!r}")


def _check_mapping(where: str, v, keys: dict):
    if not isinstance(v, dict) or set(v) != set(keys):
        _fail(where, f"value must be a mapping with exactly the keys {sorted(keys)}, got "
                     f"{sorted(v) if isinstance(v, dict) else v!r}")
    for k, rule in keys.items():
        x = v[k]
        if isinstance(rule, tuple):
            if x not in rule:
                _fail(where, f"{k} must be one of {rule}, got {x!r}")
        elif rule == "fraction":
            if not (_is_num(x) and 0 < x <= 1):
                _fail(where, f"{k} must lie in (0, 1], got {x!r}")
        elif rule == "positive":
            if not (_is_num(x) and x > 0):
                _fail(where, f"{k} must be > 0, got {x!r}")
        elif rule == "int_pos":
            if not (_is_int(x) and x >= 1):
                _fail(where, f"{k} must be a positive integer, got {x!r}")


def _gate_record(section: str, name: str, spec: dict, rec, *, allow_test_only: bool) -> Record:
    where = f"sections.{section}.{name}"
    if not isinstance(rec, dict):
        _fail(where, "must be a record {value, unit, label, source, ...}")
    missing = [k for k in RECORD_KEYS_REQUIRED if k not in rec]
    if missing:
        _fail(where, f"lacks {missing}")
    extra = sorted(set(rec) - set(RECORD_KEYS_REQUIRED) - set(RECORD_KEYS_OPTIONAL))
    if extra:
        _fail(where, f"unknown keys {extra}")
    label = rec["label"]
    if label == TEST_ONLY_LABEL and not allow_test_only:
        _fail(where, "is labelled TEST_ONLY; TEST_ONLY values are accepted only from in-memory "
                     "test fixtures, never from a file")
    accepted = EVIDENCE_LABELS + ((TEST_ONLY_LABEL,) if allow_test_only else ())
    require_evidence_label(label, where, accepted=accepted, qualified=False,
                           error=PipelineConfigError)
    source = rec["source"]
    if not isinstance(source, str) or not source.strip():
        _fail(where, "must state a non-empty source")
    item = rec.get("item")
    want = spec["item"]
    sfi = rec.get("stands_in_for_item")
    aid = rec.get("assumption_id")
    value = rec["value"]
    if want is None:
        if label == "PROJECT_INPUT" or item is not None or sfi is not None or aid is not None:
            _fail(where, "is no docs/06 item: PROJECT_INPUT, item, stands_in_for_item and "
                         "assumption_id are not allowed")
    else:
        if item != want:
            _fail(where, f"must name its docs/06 item ('item: {want}'), got {item!r}")
        if label == "PROJECT_INPUT":
            pass                                  # supply record checked below (A2c G2)
        elif label == "ASSUMPTION":
            if sfi != want:
                _fail(where, f"an ASSUMPTION standing in for PROJECT_INPUT item {want} must carry "
                             f"'stands_in_for_item: {want}'")
            if not isinstance(aid, str) or want not in assumption_registry().get(aid, ()):
                _fail(where, f"assumption_id {aid!r} is not mapped to PROJECT_INPUT item {want} by "
                             f"reflection_holo/io/assumption_registry.yaml")
        elif label != TEST_ONLY_LABEL:
            _fail(where, f"is PROJECT_INPUT item {want}: label {label} is not accepted (use "
                         f"PROJECT_INPUT, a registered ASSUMPTION, or TEST_ONLY in memory)")
    supply = check_supply(where, label, value, rec, error=PipelineConfigError)
    dim, factor = _unit(where, spec["dimension"], rec["unit"])
    if value is None:
        if label not in ("PROJECT_INPUT", "UNVERIFIED"):
            _fail(where, f"is null with label {label}; only a PROJECT_INPUT or UNVERIFIED may be null")
        canonical = None
    else:
        _check_record_kind(where, spec["kind"], value, dim)
        if factor is None or (isinstance(value, dict) and "rule" in value):
            canonical = copy.deepcopy(value)
        elif isinstance(value, dict):
            canonical = {k: float(a) * factor for k, a in value.items()}
        else:
            canonical = float(value) * factor
    note = rec.get("note")
    if note is not None and not isinstance(note, str):
        _fail(where, "note must be a string")
    return Record(section=section, name=name, value=copy.deepcopy(value), canonical_value=canonical,
                  canonical_unit=CANONICAL.get(dim, "none"), unit=rec["unit"], label=label,
                  source=source, item=want, stands_in_for_item=sfi, assumption_id=aid, note=note,
                  supply=supply)


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and not (
                {"value", "label"} <= set(v)):          # records are replaced whole
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


VARIANT_KEYS = {"description", "sections"}
VARIANT_KEYS_OPTIONAL = {"cfg_b_parameters"}


def _variant(data: dict, variant: str) -> dict:
    variants = data.get("variants") or {}
    if variant not in variants:
        raise PipelineConfigError(f"unknown variant {variant!r}; defined: {sorted(variants)}")
    v = variants[variant]
    if not isinstance(v, dict) or not VARIANT_KEYS <= set(v) or \
            set(v) - VARIANT_KEYS - VARIANT_KEYS_OPTIONAL:
        raise PipelineConfigError(f"variant {variant!r} must be {{description, sections}} "
                                  f"(optionally cfg_b_parameters)")
    return v


def resolve_variant(data: dict, variant: str | None) -> dict:
    """Base sections, or the base deep-merged with ``variants[variant].sections``."""
    if variant is None:
        return copy.deepcopy(data["sections"])
    v = _variant(data, variant)
    return _deep_merge(data["sections"], v["sections"])


def resolve_variant_cfg_b(data: dict, variant: str | None) -> dict:
    """The CFG-B block of the base, with the whole parameter records of
    ``variants[variant].cfg_b_parameters`` replacing the base's (report E4). Each replacement must
    be a record mapping; it passes the CFG-B gate like any other."""
    cfg_b = copy.deepcopy(data["cfg_b"])
    if variant is None:
        return cfg_b
    over = _variant(data, variant).get("cfg_b_parameters")
    if over is None:
        return cfg_b
    if not isinstance(over, dict) or not over:
        raise PipelineConfigError(f"variant {variant!r}: cfg_b_parameters must be a non-empty "
                                  f"mapping of whole CFG-B records")
    if not isinstance(cfg_b, dict) or not isinstance(cfg_b.get("parameters"), dict):
        raise PipelineConfigError("cfg_b.parameters must be a mapping")
    for name, rec in over.items():
        if not isinstance(rec, dict) or not {"value", "label"} <= set(rec):
            raise PipelineConfigError(f"variant {variant!r}: cfg_b_parameters.{name} must be a "
                                      f"whole record {{value, unit, label, source, ...}}")
        cfg_b["parameters"][name] = copy.deepcopy(rec)
    return cfg_b


def _glancing_angle(rec: Record, cfg_b_params: dict, sections: dict) -> dict:
    """Value of the glancing angle: supplied/assumed number, or computed by the declared rule with
    the declared mean inner potential (B1 for the geometric engine; the MIP of the potential
    actually used for the multislice engine, orchestrator decision after report D3)."""
    if rec.value is None:
        raise MissingProjectInputError(
            "sections.illumination.glancing_angle is a missing PROJECT_INPUT "
            "(docs/06_project_inputs_required.md item 7)", [7], ["glancing_angle"])
    if isinstance(rec.value, dict):
        hkl = rec.value["reflection_hkl"]
        need = ("surface_normal_hkl", "beam_energy_keV", "mean_inner_potential_V",
                "lattice_parameter")
        vals = {}
        for n in need:
            p = cfg_b_params.get(n)
            if p is None or p.get("value") is None:
                raise PipelineConfigError(f"glancing-angle rule needs cfg_b.parameters.{n}")
            vals[n] = p["value"]
        if cfg_b_params["lattice_parameter"]["unit"] != "A":
            raise PipelineConfigError("glancing-angle rule: lattice_parameter must be in A")
        src = rec.value["V0_source"]
        if src == "cfg_b.mean_inner_potential_V":
            if cfg_b_params["mean_inner_potential_V"].get("unit") != "V":
                raise PipelineConfigError("cfg_b mean_inner_potential_V must be in V")
            V0 = float(vals["mean_inner_potential_V"])
            v0_rec = dict(value_V=V0, label=cfg_b_params["mean_inner_potential_V"].get("label"),
                          assumption_id=cfg_b_params["mean_inner_potential_V"].get("assumption_id"),
                          source=cfg_b_params["mean_inner_potential_V"].get("source"),
                          parameter="cfg_b.mean_inner_potential_V")
        else:
            eng = sections["engine"]
            if eng["name"] != "multislice":
                raise PipelineConfigError("V0_source 'sections.engine.multislice.potential_mip' "
                                          "is only for the multislice engine")
            mip = eng["multislice"]["potential_mip"]
            V0 = float(mip.canonical_value)
            v0_rec = dict(value_V=V0, label=mip.label, assumption_id=None, source=mip.source,
                          parameter="sections.engine.multislice.potential_mip")
        if rec.label == "PROJECT_INPUT" and v0_rec["label"] != "PROJECT_INPUT":
            raise PipelineConfigError(
                f"sections.illumination.glancing_angle: the rule form computes the angle from V0 = "
                f"{V0} V ({v0_rec['parameter']}, label {v0_rec['label']}"
                f"{' ' + v0_rec['assumption_id'] if v0_rec['assumption_id'] else ''}), so the "
                f"computed angle cannot carry the label PROJECT_INPUT (docs/06 items 7 and 20: an "
                f"angle computed from an assumed V0 biases h by about 1 %/V); supply the measured "
                f"angle as a number, or label the rule by the stand-in it is (audit A3 M2)")
        try:
            sc = specular_condition_for(tuple(hkl), tuple(vals["surface_normal_hkl"]),
                                        E_keV=float(vals["beam_energy_keV"]), V0_V=V0,
                                        a_A=float(vals["lattice_parameter"]))
        except GeometryError as exc:
            raise PipelineConfigError(f"glancing-angle rule: {exc}") from exc
        return dict(value_rad=float(sc.theta_ext), rule=rec.value["rule"], reflection_hkl=list(hkl),
                    theta_int_rad=float(sc.theta_int), h_2pi_A=float(sc.h_2pi_A),
                    computed_by="reflection_holo.geometry.specular.specular_condition_for",
                    V0_V=V0, V0_source=src, V0_record=v0_rec,
                    cfg_b_mean_inner_potential_V=float(vals["mean_inner_potential_V"]),
                    label=rec.label, assumption_id=rec.assumption_id, source=rec.source)
    return dict(value_rad=float(rec.canonical_value), rule=None, label=rec.label,
                assumption_id=rec.assumption_id, source=rec.source)


def _cfg_b_with_angle(cfg_b: dict, ga: dict, rec: Record) -> dict:
    out = copy.deepcopy(cfg_b)
    params = out.get("parameters")
    if not isinstance(params, dict):
        raise PipelineConfigError("cfg_b.parameters must be a mapping")
    if "glancing_angle_ext" in params:
        raise PipelineConfigError("cfg_b.parameters.glancing_angle_ext must not be given: the "
                                  "glancing angle is declared once, in "
                                  "sections.illumination.glancing_angle (item 7)")
    entry = dict(value=ga["value_rad"] * 1.0e3, unit="mrad", label=rec.label, item=7)
    if rec.label == "ASSUMPTION":
        entry.update(stands_in_for_item=7, assumption_id=rec.assumption_id)
    if rec.supply is not None:                     # the supply record travels with the value
        entry.update(rec.supply)
    src = rec.source
    if ga["rule"] is not None:
        src = (f"{rec.source}; computed by the pipeline: {ga['computed_by']}"
               f"({tuple(ga['reflection_hkl'])}) at V0 = {ga['V0_V']} V from {ga['V0_source']} "
               f"(not typed)")
    entry["source"] = src
    params["glancing_angle_ext"] = entry
    return out


def load_pipeline_dict(data: dict, *, variant: str | None, allow_test_only: bool = False,
                       source_path: str | None = None, sha256_file: str | None = None
                       ) -> PipelineConfig:
    """Validate a pipeline configuration mapping at RUN level (missing PROJECT_INPUT fails).

    allow_test_only=True only for in-memory test fixtures; ``load_pipeline_file`` never sets it.
    """
    if not isinstance(data, dict):
        raise PipelineConfigError("configuration must be a mapping")
    miss = [k for k in TOP_KEYS_REQUIRED if k not in data]
    if miss:
        raise PipelineConfigError(f"configuration lacks top-level keys {miss}")
    extra = sorted(set(data) - set(TOP_KEYS_REQUIRED) - set(TOP_KEYS_OPTIONAL))
    if extra:
        raise PipelineConfigError(f"configuration has unknown top-level keys {extra}")
    if data["pipeline_schema"] != PIPELINE_SCHEMA:
        raise PipelineConfigError(f"unsupported pipeline_schema {data['pipeline_schema']!r}")
    if data["purpose"] not in PURPOSES:
        raise PipelineConfigError(f"purpose must be one of {PURPOSES}, got {data['purpose']!r}")
    for k in ("run_name", "description"):
        if not isinstance(data[k], str) or not data[k].strip():
            raise PipelineConfigError(f"{k} must be a non-empty string")
    sections_raw = resolve_variant(data, variant)
    if not isinstance(sections_raw, dict):
        raise PipelineConfigError("sections must be a mapping")
    unknown = sorted(set(sections_raw) - set(SECTIONS))
    if unknown:
        raise PipelineConfigError(f"unknown sections {unknown}")
    sections: dict[str, dict] = {}
    missing_items: list[tuple[str, int]] = []
    for sec, schema in SECTIONS.items():
        got = sections_raw.get(sec)
        if not isinstance(got, dict):
            raise PipelineConfigError(f"section {sec!r} is required (a mapping)")
        unk = sorted(set(got) - set(schema))
        if unk:
            raise PipelineConfigError(f"sections.{sec}: unknown keys {unk}")
        out = {}
        for name, spec in schema.items():
            if name not in got:
                if spec["optional"]:
                    continue
                if spec["type"] == "record" and spec["item"] is not None:
                    missing_items.append((f"{sec}.{name}", spec["item"]))
                    continue
                raise PipelineConfigError(f"sections.{sec}.{name} is required (no default)")
            if spec["type"] == "record":
                r = _gate_record(sec, name, spec, got[name], allow_test_only=allow_test_only)
                if r.value is None and r.label == "PROJECT_INPUT":
                    missing_items.append((f"{sec}.{name}", r.item))
                if r.label == "UNVERIFIED":
                    raise PipelineConfigError(f"sections.{sec}.{name} is UNVERIFIED: refused at "
                                              f"run level")
                out[name] = r
            else:
                out[name] = _check_plain(f"sections.{sec}.{name}", spec, got[name])
        sections[sec] = out
    st_raw = sections_raw["structure"]
    if "staircase" not in st_raw and "feature" not in st_raw:
        missing_items.append(("structure.staircase", 11))      # the staircase path (no feature)
    if missing_items:
        listing = "; ".join(f"item {i} ({n})" for n, i in sorted(missing_items, key=lambda t: t[1]))
        raise MissingProjectInputError(
            f"pipeline run refused, missing PROJECT_INPUT (docs/06_project_inputs_required.md): "
            f"{listing}", [i for _, i in missing_items], [n for n, _ in missing_items])
    _check_structure(sections)
    _check_engine(sections, allow_test_only=allow_test_only)
    ga_rec = sections["illumination"]["glancing_angle"]
    if not isinstance(data["cfg_b"], dict):
        raise PipelineConfigError("cfg_b must be a CFG-B configuration mapping")
    cfg_b_raw = resolve_variant_cfg_b(data, variant)
    ga = _glancing_angle(ga_rec, cfg_b_raw.get("parameters") or {}, sections)
    cfg_b_full = _cfg_b_with_angle(cfg_b_raw, ga, ga_rec)
    cfg_b = load_config_dict(cfg_b_full, level="run", allow_test_only=allow_test_only)
    if cfg_b.config_id != "CFG-B":
        raise PipelineConfigError("cfg_b must be a CFG-B configuration")
    records = _all_records(sections)
    test_only = cfg_b.test_only or any(r.label == TEST_ONLY_LABEL for r in records)
    _refuse_unused_physical_inputs(cfg_b, sections, ga)
    if data["purpose"] == "comparison":
        eng = sections["engine"]
        fp = eng["multislice"]["frozen_phonons"] if eng["name"] == "multislice" else None
        thermal_reasons = []
        if isinstance(fp, dict) and set(fp) == FIXED_U_KEYS:
            thermal_reasons.append(
                "purpose 'comparison' refuses frozen phonons given as a fixed u (e.g. "
                "model_assumptions A7, inherited, unsourced): the specimen temperature "
                f"(PROJECT_INPUT item 23) must enter through {{model: {THERMAL_MODEL_B35}}} "
                "(report E2)")
        if fp == "none":
            thermal_reasons.append(
                "purpose 'comparison' refuses frozen_phonons 'none' (a static lattice, whatever "
                "its label): the specimen temperature (PROJECT_INPUT item 23) and the thermal "
                "model are then not represented at all; a static lattice has no Debye-Waller "
                "factor (amplitude 1.0 instead of exp(-B s^2) = 0.772 at (0,0,8) with B35 at "
                "295.5 K). Use frozen_phonons {model: " + THERMAL_MODEL_B35 + "} with "
                "sections.engine.multislice.specimen_temperature (item 23; audit A5 F2)")
        _comparison_gate(cfg_b, records, test_only, reasons=thermal_reasons)
    resolved = {k: v for k, v in data.items() if k != "variants"}
    resolved["sections"] = sections_raw
    resolved["cfg_b"] = cfg_b_full
    resolved["variant"] = variant
    return PipelineConfig(run_name=data["run_name"], purpose=data["purpose"],
                          description=data["description"], variant=variant, sections=sections,
                          cfg_b=cfg_b, cfg_b_raw=cfg_b_full, glancing_angle=ga,
                          source_path=source_path, sha256_file=sha256_file,
                          sha256_resolved=canonical_sha256(resolved), test_only=test_only,
                          raw=copy.deepcopy(data))


# the design phase extent of the quadrature is COMPUTED by the pipeline from the geometry
# (pipeline.convergence.design_extent), not declared
CONVERGENCE_KEYS = ("source_profile", "n_radial", "n_azimuthal", "line_azimuth_rad", "tolerance")
# item-3 stand-ins whose model_assumptions row states a plane wave (B21) or a convergent
# illumination (B40, report E3): a stand-in whose row contradicts the value is refused
CONVERGENCE_STAND_IN_ZERO = {"B21": True, "B40": False}
R1_PASSAGES_UNDER_CONVERGENCE = ("condenser_biprism_pretilt",)


# records that are required or refused according to the reference model (audit A5 F7, F10)
R2_ONLY_RECORDS = {("reference", "shift"): "the self-reference shift of an R2 reference",
                   ("optics", "loss_electron_visibility"): (
                       "the mutual visibility of the surface-plasmon-loss electrons of the two "
                       "reflected arms of an R2 reference")}


def _check_reference(cfg_b: LoadedConfig, sections: dict) -> None:
    """Item-16 records that depend on the reference model: with R2 the shift and the loss-electron
    visibility are REQUIRED (missing: MissingProjectInputError naming item 16, before any engine
    run; A5 F7, F10); with a vacuum reference (R1, R3) the loss-electron visibility has no effect
    (the reference arm carries no loss electron, optics.inelastic) and is refused rather than
    ignored (the shift of an R1 run is listed as NOT USED, as before)."""
    ref = cfg_b.value("reference_model")
    if ref == "R2":
        miss = [(sec, name) for (sec, name) in R2_ONLY_RECORDS if name not in sections[sec]]
        if miss:
            raise MissingProjectInputError(
                "pipeline run refused, missing PROJECT_INPUT (docs/06_project_inputs_required.md): "
                + "; ".join(f"item 16 (sections.{sec}.{name}: {R2_ONLY_RECORDS[(sec, name)]}, "
                            f"required by an R2 reference)" for sec, name in miss),
                [16] * len(miss), [f"{sec}.{name}" for sec, name in miss])
    elif "loss_electron_visibility" in sections["optics"]:
        raise PipelineConfigError(
            f"sections.optics.loss_electron_visibility: with the vacuum reference {ref} the "
            f"reference arm carries no surface-plasmon loss electron, so the value has no effect "
            f"(optics.inelastic): refused rather than ignored (it is required for R2 only; A5 F10)")


def _check_convergence(cfg_b: LoadedConfig, sections: dict, ga: dict) -> None:
    """Gate of the illumination convergence (PROJECT_INPUT item 3; report E3; H2 N3). A zero
    convergence is a plane wave: the quadrature block and the R1 separation are refused rather than
    ignored. A non-zero convergence is accepted only (i) as a supplied PROJECT_INPUT or a registered
    stand-in whose row states a convergence (the CFG-B gate and CONVERGENCE_STAND_IN_ZERO), (ii) with
    the multislice engine (each member is an engine run; the geometric engine is plane-wave only),
    (iii) with a declared quadrature (sections.illumination.convergence_quadrature, every key
    required) that meets its own error bound, and (iv) with R1 only through the condenser-biprism
    pre-tilt and with the separation D0 (item 16), or with R2 (no separation)."""
    conv, _ = cfg_b.quantity("convergence_semi_angle")
    p3 = cfg_b.parameters["convergence_semi_angle"]
    aid = getattr(p3, "assumption_id", None)
    cq = sections["illumination"].get("convergence_quadrature")
    sep = sections["reference"].get("separation")
    if p3.label == "ASSUMPTION" and aid in CONVERGENCE_STAND_IN_ZERO:
        if CONVERGENCE_STAND_IN_ZERO[aid] != (conv == 0.0):
            raise PipelineConfigError(
                f"cfg_b.convergence_semi_angle: stand-in {aid} states "
                f"{'a plane wave (zero convergence)' if CONVERGENCE_STAND_IN_ZERO[aid] else 'a non-zero convergence'}"
                f", not {cfg_b.value('convergence_semi_angle')} "
                f"{p3.unit}: refused")
    if conv == 0.0:
        if cq is not None:
            raise PipelineConfigError(
                "sections.illumination.convergence_quadrature is given but "
                "cfg_b.convergence_semi_angle is 0 (a plane wave): refused rather than ignored")
        if sep is not None:
            raise PipelineConfigError(
                "sections.reference.separation is used only by a convergence ensemble with an R1 "
                "reference: refused rather than ignored with a zero convergence")
        return
    if sections["engine"]["name"] != "multislice":
        raise PipelineConfigError(
            f"cfg_b.convergence_semi_angle = {cfg_b.value('convergence_semi_angle')} {p3.unit} "
            f"(docs/06 item 3): the convergence ensemble runs one multislice engine run per "
            f"incidence direction (report E3); the geometric engine is plane-wave only: refused")
    if cq is None:
        raise PipelineConfigError(
            "a non-zero cfg_b.convergence_semi_angle (docs/06 item 3) needs "
            f"sections.illumination.convergence_quadrature with the keys {CONVERGENCE_KEYS} (the "
            "number of incidence directions is a declared, recorded choice; no default)")
    if not (isinstance(cq, dict) and set(cq) == set(CONVERGENCE_KEYS)):
        raise PipelineConfigError(f"sections.illumination.convergence_quadrature must have exactly "
                                  f"the keys {CONVERGENCE_KEYS}, got "
                                  f"{sorted(cq) if isinstance(cq, dict) else cq!r}")
    try:                                   # types and ranges (the error bound is checked at run time)
        convergence_quadrature_from(cfg_b, cq, design_phase_extent_rad=0.0,
                                    design_curvature_rad=0.0)
    except ValueError as exc:
        raise PipelineConfigError(f"sections.illumination.convergence_quadrature: {exc}") from exc
    ref_model = cfg_b.value("reference_model")
    if ref_model == "R1":
        passage = sections["reference"]["aperture_passage"].value
        if passage not in R1_PASSAGES_UNDER_CONVERGENCE:
            raise PipelineConfigError(
                f"R1 reference with aperture passage {passage!r} under convergence: only "
                f"{R1_PASSAGES_UNDER_CONVERGENCE} is implemented (a reference inclined to the "
                f"imaging axis needs the conjugate plane of the imaging; report E3)")
        if sep is None or sep.value is None:
            raise MissingProjectInputError(
                "sections.reference.separation is a missing PROJECT_INPUT (docs/06 item 16: the "
                "object-reference separation at the specimen), required by an R1 convergence "
                "ensemble", [16], ["reference.separation"])
    elif ref_model == "R2":
        if sep is not None:
            raise PipelineConfigError("sections.reference.separation: an R2 reference is the "
                                      "shifted object (sections.reference.shift); refused rather "
                                      "than ignored")
    else:
        raise PipelineConfigError(f"reference model {ref_model!r} under convergence: R1 and R2 "
                                  f"only")


def convergence_quadrature_from(cfg_b: LoadedConfig, cq: dict, *, design_phase_extent_rad: float,
                                design_curvature_rad: float):
    """The optics.coherence.ConvergenceQuadrature of a gated configuration (semi-angle from
    cfg_b.convergence_semi_angle, item 3; profile, nodes and tolerance from sections.illumination.
    convergence_quadrature; the design phase extent and curvature computed by the caller from the
    geometry, pipeline.convergence.design_extent). Raises ValueError if the declared quadrature is
    invalid or its error bound exceeds its tolerance."""
    from reflection_holo.optics.coherence import ConvergenceQuadrature
    conv, _ = cfg_b.quantity("convergence_semi_angle")
    p3 = cfg_b.parameters["convergence_semi_angle"]
    aid = getattr(p3, "assumption_id", None)
    lab = (f"ASSUMPTION {aid} (stands in for PROJECT_INPUT item 3)" if p3.label == "ASSUMPTION"
           else f"{p3.label} item 3 ({p3.source})")
    return ConvergenceQuadrature(
        semi_angle_rad=float(conv), semi_angle_label=lab, source_profile=cq["source_profile"],
        n_radial=cq["n_radial"], n_azimuthal=cq["n_azimuthal"],
        line_azimuth_rad=cq["line_azimuth_rad"],
        design_phase_extent_rad=float(design_phase_extent_rad),
        design_curvature_rad=float(design_curvature_rad), tolerance=cq["tolerance"])


def _refuse_unused_physical_inputs(cfg_b: LoadedConfig, sections: dict, ga: dict) -> None:
    """Inputs that matter physically but that no engine path of the pipeline represents are
    REFUSED rather than accepted and ignored (audit A3 M6; docs/05 criterion 5; docs/06 item 12
    "must be modelled rather than ignored"). Items that do not change the simulated physics and are
    not used on a path are listed by ``list_inputs`` as "SUPPLIED, NOT USED on this path"."""
    _check_reference(cfg_b, sections)
    _check_convergence(cfg_b, sections, ga)
    prep = cfg_b.value("surface_preparation_details")
    if isinstance(prep, dict):
        if prep.get("overlayer", "none") != "none":
            _check_overlayer(cfg_b, prep, sections)
        _check_termination(cfg_b, prep, sections)
    pat = cfg_b.value("pattern_geometry")
    feat = sections["structure"].get("feature")
    if feat is None:
        if pat != {"features": "none"}:
            raise PipelineConfigError(
                f"cfg_b.pattern_geometry = {pat!r} (docs/06 item 13): without "
                f"sections.structure.feature the pipeline's structure and engines build atomic "
                f"steps only, no patterned mesa or trench; only {{features: none}} is accepted, "
                f"anything else would be ignored: refused (audit A3 M6)")
    else:
        want = {"features": feat.value["kind"], "geometry": PATTERN_FROM_FEATURE}
        p13 = cfg_b.parameters["pattern_geometry"]
        if pat != want:
            raise PipelineConfigError(
                f"cfg_b.pattern_geometry = {pat!r} (docs/06 item 13) contradicts "
                f"sections.structure.feature: with a feature it must be {want!r} (the numbers are "
                f"declared once, in the feature record)")
        if (p13.label, getattr(p13, "assumption_id", None)) != (feat.label, feat.assumption_id):
            raise PipelineConfigError(
                f"cfg_b.pattern_geometry ({p13.label} {getattr(p13, 'assumption_id', None)}) and "
                f"sections.structure.feature ({feat.label} {feat.assumption_id}) must carry the same "
                f"label and assumption_id (one item-13 declaration)")
    if ga.get("rule") is not None:
        target = cfg_b.value("target_reflection_hkl")
        if list(target) != list(ga["reflection_hkl"]):
            raise PipelineConfigError(
                f"the glancing-angle rule uses reflection {tuple(ga['reflection_hkl'])} but the "
                f"target reflection (docs/06 item 9, cfg_b.target_reflection_hkl) is "
                f"{tuple(target)}: the angle would be computed for a reflection other than the "
                f"declared working condition: refused (audit A3 M6)")


OXIDE_MODEL = "continuum_oxide"
OXIDE_KEYS = ("model", "material", "thickness_A", "density_g_cm3", "consumed_layers", "V_real_V",
              "V_imag_V", "vacuum_edge_width_A", "interface_width_A", "amorphous_si_thickness_A")
OXIDE_KEYS_AMORPHOUS = ("amorphous_si_V_real_V", "amorphous_si_V_imag_V")
OXIDE_STAND_INS_CLEAN = ("B26",)          # item-12 stand-ins whose row states NO overlayer


def qualified_label(p, item: int | None) -> str:
    """Qualified evidence label of a CFG-B parameter or a Record (as pipeline.engines._label)."""
    lab = p.label
    aid = getattr(p, "assumption_id", None)
    if lab == "ASSUMPTION" and aid:
        return f"ASSUMPTION {aid} (stands in for PROJECT_INPUT item {item})"
    if lab == "PROJECT_INPUT":
        return f"PROJECT_INPUT item {item} ({p.source})"
    return f"{lab} ({p.source})"


def oxide_spec_from_config(cfg_b: LoadedConfig):
    """structure.oxide.ContinuumOxideSpec of cfg_b.surface_preparation_details.overlayer (item 12;
    report E4), every parameter carrying the record's qualified label; conformal (no per-terrace
    overrides), sharp_edge_test_flag False. Raises PipelineConfigError naming item 12."""
    from reflection_holo.structure import oxide as ox
    prep = cfg_b.value("surface_preparation_details")
    over = prep.get("overlayer") if isinstance(prep, dict) else None
    where = "cfg_b.surface_preparation_details.overlayer (docs/06 item 12)"
    if not isinstance(over, dict) or over.get("model") != OXIDE_MODEL:
        raise PipelineConfigError(
            f"{where} = {over!r}: only 'none' or a complete continuum oxide {{model: "
            f"{OXIDE_MODEL}, ...}} is represented by the engines (report E4); refused rather than "
            f"ignored (audit A3 M6)")
    t_a = over.get("amorphous_si_thickness_A")
    want = set(OXIDE_KEYS) | (set(OXIDE_KEYS_AMORPHOUS)
                              if isinstance(t_a, (int, float)) and t_a > 0 else set())
    if set(over) != want:
        raise PipelineConfigError(
            f"{where}: the continuum oxide needs exactly the keys {sorted(want)} (every physical "
            f"parameter REQUIRED; no default), got {sorted(over)}; missing "
            f"{sorted(want - set(over))}, unknown {sorted(set(over) - want)}")
    p12 = cfg_b.parameters["surface_preparation_details"]
    lab = qualified_label(p12, 12)
    labels = {k: lab for k in ox.LABEL_KEYS}
    if t_a is not None and t_a > 0:
        labels["amorphous_si_potential"] = lab
    try:
        spec = ox.ContinuumOxideSpec(
            material=over["material"], thickness_A=over["thickness_A"],
            density_g_cm3=over["density_g_cm3"], consumed_layers=over["consumed_layers"],
            V_real_V=over["V_real_V"], V_imag_V=over["V_imag_V"],
            vacuum_edge_width_A=over["vacuum_edge_width_A"],
            interface_width_A=over["interface_width_A"],
            amorphous_si_thickness_A=over["amorphous_si_thickness_A"],
            amorphous_si_V_real_V=over.get("amorphous_si_V_real_V"),
            amorphous_si_V_imag_V=over.get("amorphous_si_V_imag_V"),
            terrace_thickness_A=None, terrace_consumed_layers=None, sharp_edge_test_flag=False,
            labels=labels)
        ox.validate_spec(spec)
    except (ValueError, TypeError) as exc:
        raise PipelineConfigError(f"{where}: {exc}") from exc
    return spec


def _check_overlayer(cfg_b: LoadedConfig, prep: dict, sections: dict) -> None:
    """Gate of a declared overlayer (item 12; report E4): a complete continuum oxide
    (oxide_spec_from_config), not under a stand-in whose row states a clean surface (B26), on the
    staircase path (the feature path builds clean bulk-terminated surfaces only) with the bulk
    termination (a reconstruction under an overlayer is NOT IMPLEMENTED). The consumed-layer count
    is checked against the lattice parameter here (structure.oxide.terrace_stacks)."""
    from reflection_holo.structure import oxide as ox
    where = f"cfg_b.surface_preparation_details.overlayer = {prep.get('overlayer')!r}"
    p12 = cfg_b.parameters["surface_preparation_details"]
    if p12.label == "ASSUMPTION" and getattr(p12, "assumption_id", None) in OXIDE_STAND_INS_CLEAN:
        raise PipelineConfigError(f"{where} (docs/06 item 12): stand-in "
                                  f"{p12.assumption_id} states a clean surface without oxide; an "
                                  f"overlayer needs its own declaration (e.g. B41)")
    spec = oxide_spec_from_config(cfg_b)
    if "feature" in sections["structure"]:
        raise PipelineConfigError(f"{where}: the feature path builds clean, bulk-terminated "
                                  f"surfaces only; the continuum oxide is built on the staircase "
                                  f"path (report E4): refused rather than ignored")
    if prep.get("termination", "bulk") != "bulk":
        raise PipelineConfigError(f"{where}: a reconstruction under an overlayer is NOT "
                                  f"IMPLEMENTED (a buried interface is not a clean surface)")
    a_A, unit = cfg_b.quantity("lattice_parameter")
    if unit != "A":
        raise PipelineConfigError("cfg_b.lattice_parameter must be in A")
    try:
        ox.terrace_stacks(spec, terrace_heights_A=[0.0], a_A=float(a_A))
    except ValueError as exc:
        raise PipelineConfigError(f"{where}: {exc}") from exc


def _check_termination(cfg_b: LoadedConfig, prep: dict, sections: dict) -> None:
    """cfg_b.surface_preparation_details.termination (item 12; report E2): 'bulk' on every path;
    a static buckled reconstruction as {name, buckling_registry} (the registry is a required model
    choice, structure.si001.parse_termination; audit A5 F1);
    a sourced reconstruction (structure.reconstruction) only where it is represented, i.e. the
    multislice engine on the staircase path (the geometric engine has no atoms and refuses it, B4;
    the feature builder refuses it, structure.features.FEATURE_RECONSTRUCTION_REFUSAL); the
    flip-flop ensemble only with the sourced thermal model (its configurations are drawn from the
    frozen-phonon generator at the specimen temperature, item 23). A stand-in whose row states a
    bulk termination (B26) cannot carry a reconstruction."""
    from reflection_holo.structure.reconstruction import FLIPFLOP
    from reflection_holo.structure.si001 import TERMINATIONS, parse_termination
    raw = prep.get("termination", "bulk")
    where = f"cfg_b.surface_preparation_details.termination = {raw!r}"
    try:
        # a static BUCKLED reconstruction needs {name, buckling_registry} (audit A5 F1)
        term, _registry = parse_termination(raw)
    except ValueError as exc:
        raise PipelineConfigError(f"{where}: {exc}") from exc
    if term == "bulk":
        return
    if term not in TERMINATIONS:
        raise PipelineConfigError(f"{where}: not one of {TERMINATIONS}: refused (audit A3 M6)")
    eng = sections["engine"]["name"]
    if "feature" in sections["structure"]:
        raise PipelineConfigError(f"{where}: the feature path builds bulk-terminated structures "
                                  f"only (reconstruction refused on the half-torus, report E2)")
    if eng != "multislice":
        raise PipelineConfigError(
            f"{where}: engine {eng!r} has no atoms and represents bulk-terminated terraces only "
            f"(B3, B4); a reconstruction is represented by the multislice engine only: refused "
            f"rather than ignored (audit A3 M6)")
    fp = sections["engine"]["multislice"]["frozen_phonons"]
    if term == FLIPFLOP and not (isinstance(fp, dict) and fp.get("model") == THERMAL_MODEL_B35):
        raise PipelineConfigError(
            f"{where} (ASSUMPTION B37) needs frozen_phonons {{model: {THERMAL_MODEL_B35}}} with the "
            f"specimen temperature (PROJECT_INPUT item 23): its configurations are drawn per "
            f"realisation from the frozen-phonon generator of a room-temperature model")
    p12 = cfg_b.parameters["surface_preparation_details"]
    if p12.label == "ASSUMPTION" and getattr(p12, "assumption_id", None) == "B26":
        raise PipelineConfigError(f"{where}: stand-in B26 states a clean, BULK-terminated surface; "
                                  f"a reconstruction needs its own declaration")


def _comparison_gate(cfg_b: LoadedConfig, records: list[Record], test_only: bool, *,
                     reasons: list[str]) -> None:
    """purpose 'comparison' refuses (audit A3 M2): every registered DEMO stand-in (registry
    demo_only, B19-B32) whatever its docs/06 item; any ASSUMPTION standing in for a blocking item;
    TEST_ONLY values; and the thermal forms that do not represent item 23 (``reasons``, computed by
    the caller: a fixed u or a static lattice; audit A5 F2). Every reason is named in ONE error.
    The remaining ASSUMPTIONs are listed in the run summary."""
    demo = demo_only_stand_ins()
    bad = [f"sections.{r.section}.{r.name} (item {r.item}, {r.assumption_id})" for r in records
           if r.label == "ASSUMPTION" and (r.assumption_id in demo or r.item in BLOCKING_ITEMS)]
    bad += [f"cfg_b.{p.name} (item {p.item}, {p.assumption_id})" for p in cfg_b.parameters.values()
            if p.label == "ASSUMPTION" and (p.assumption_id in demo or p.item in BLOCKING_ITEMS)]
    msgs = list(reasons)
    if bad or test_only:
        msgs.append(
            f"purpose 'comparison' refuses every demo stand-in ({', '.join(sorted(demo))}), every "
            f"ASSUMPTION standing in for a blocking PROJECT_INPUT item and TEST_ONLY values: "
            f"{bad or 'TEST_ONLY present'} (audit A3 M2)")
    if msgs:
        raise PipelineConfigError("; AND ".join(msgs))


def assumptions_in_use(cfg: "PipelineConfig") -> list[dict]:
    """Every ASSUMPTION-labelled value of the run (CFG-B parameters and pipeline records) with its
    model_assumptions row, for the run summary (audit A3 M2)."""
    demo = demo_only_stand_ins()
    out = [dict(parameter=f"cfg_b.{p.name}", item=p.item, assumption_id=p.assumption_id,
                demo_only=p.assumption_id in demo, source=p.source)
           for p in cfg.cfg_b.parameters.values() if p.label == "ASSUMPTION"]
    out += [dict(parameter=f"sections.{r.section}.{r.name}", item=r.item,
                 assumption_id=r.assumption_id, demo_only=r.assumption_id in demo, source=r.source)
            for r in cfg.records() if r.label == "ASSUMPTION"]
    return out


def _check_structure(sections: dict) -> None:
    """The structure is EITHER a staircase (item 11; atomistic builder, both engines) OR a surface
    feature on a flat, step-free surface (item 13; agent T2, geometric engine only). Settings that the
    chosen path does not use are refused rather than ignored."""
    st = sections["structure"]
    feature = "feature" in st
    if feature and "staircase" in st:
        raise PipelineConfigError("sections.structure: give either staircase (item 11) or feature "
                                  "(item 13), not both (a feature on a staircase is NOT IMPLEMENTED)")
    plain = ("edge_periods", "substrate_layers", "vacuum_above_A")
    if feature:
        f = st["feature"]
        if f.label == "ASSUMPTION" and f.assumption_id in FEATURE_STAND_IN_SUB_KIND:
            want = FEATURE_STAND_IN_SUB_KIND[f.assumption_id]
            if want != f.value["sub_kind"]:
                raise PipelineConfigError(
                    f"sections.structure.feature: stand-in {f.assumption_id} states "
                    f"{'that there is no feature' if want is None else 'a ' + want}, not a "
                    f"{f.value['sub_kind']}: refused")
        extra = [k for k in plain if k in st]
        if extra:
            raise PipelineConfigError(f"sections.structure.{extra[0]}: not used on the feature path "
                                      f"(no atomistic structure is built there): refused rather than "
                                      f"ignored")
        if "feature_processing" not in sections["quantification"]:
            raise PipelineConfigError("sections.quantification.feature_processing (item 19) is "
                                      "required with a feature (no default)")
        if sections["cell"]["periods_along_beam"] != 1:
            raise PipelineConfigError("sections.cell.periods_along_beam must be 1 on the feature "
                                      "path (one field of view, sections.engine.geometric."
                                      "field_length_A)")
        if sections["optics"]["projection_reference"] != "flat_surface":
            raise PipelineConfigError("sections.optics.projection_reference must be 'flat_surface' "
                                      "on the feature path (the image is referred to the flat "
                                      "surrounding surface)")
    else:
        for k in plain:
            if k not in st:
                raise PipelineConfigError(f"sections.structure.{k} is required (no default)")
        if "feature_processing" in sections["quantification"]:
            raise PipelineConfigError("sections.quantification.feature_processing applies to the "
                                      "feature path only: refused rather than ignored")
        if sections["optics"]["projection_reference"] != "lowest_terrace_top":
            raise PipelineConfigError("sections.optics.projection_reference must be "
                                      "'lowest_terrace_top' on the staircase path")


def _check_engine(sections: dict, *, allow_test_only: bool) -> None:
    eng = sections["engine"]
    name = eng["name"]
    if name not in eng:
        raise PipelineConfigError(f"sections.engine.{name} (the parameters of the selected engine) "
                                  f"is required")
    feature = "feature" in sections["structure"]
    if feature and name != "geometric":
        raise PipelineConfigError(
            f"sections.structure.feature: the feature path of the pipeline is implemented for the "
            f"geometric engine only (engine {name!r} refused; the atomistic feature structure and "
            f"its multislice runs are not connected to the pipeline)")
    if name == "geometric":
        g = eng["geometric"]
        want = dict(GEOMETRIC_KEYS, **GEOMETRIC_FEATURE_KEYS) if feature else GEOMETRIC_KEYS
        if set(g) != set(want):
            raise PipelineConfigError(f"sections.engine.geometric must have exactly the keys "
                                      f"{sorted(want)}{' (feature path)' if feature else ''}, got "
                                      f"{sorted(g)}")
        if feature:
            for k in GEOMETRIC_FEATURE_KEYS:
                if not (_is_num(g[k]) and g[k] > 0):
                    raise PipelineConfigError(f"sections.engine.geometric.{k} must be > 0")
            n = g["field_length_A"] / g["surface_dz_A"]
            if abs(n - round(n)) > 1e-9 * max(1.0, n) or round(n) < 2:
                raise PipelineConfigError("sections.engine.geometric.surface_dz_A must divide "
                                          "field_length_A into at least 2 cells")
        px = g["exit_plane_pixel_A"]
        if not (isinstance(px, dict) and set(px) == {"x", "y"}
                and all(_is_num(v) and v > 0 for v in px.values())):
            raise PipelineConfigError("sections.engine.geometric.exit_plane_pixel_A must be "
                                      "{x: >0, y: >0}")
        for k in ("n_y",):
            if not (_is_int(g[k]) and g[k] >= 2):
                raise PipelineConfigError(f"sections.engine.geometric.{k} must be an integer >= 2")
        for k in ("x_margin_A", "reflectivity_amplitude"):
            if not (_is_num(g[k]) and g[k] > 0):
                raise PipelineConfigError(f"sections.engine.geometric.{k} must be > 0")
        if not (_is_num(g["invisibility_tol_cycles"]) and g["invisibility_tol_cycles"] >= 0):
            raise PipelineConfigError("sections.engine.geometric.invisibility_tol_cycles >= 0")
    else:
        m = eng["multislice"]
        if "physical_absorption" not in m:
            raise MissingProjectInputError(
                "sections.engine.multislice.physical_absorption is a missing PROJECT_INPUT "
                "(docs/06_project_inputs_required.md item 21)", [21], ["physical_absorption"])
        miss = [k for k in MS_KEYS if k not in m]
        extra = sorted(set(m) - set(MS_KEYS) - set(MS_KEYS_OPTIONAL))
        if miss or extra:
            raise PipelineConfigError(f"sections.engine.multislice: missing keys {miss}, unknown "
                                      f"keys {extra} (every key required, no default)")
        r = _gate_record("engine.multislice", "physical_absorption", _rec(21, "none", "mapping"),
                         m["physical_absorption"], allow_test_only=allow_test_only)
        if r.value is None:
            raise MissingProjectInputError(
                "sections.engine.multislice.physical_absorption is a missing PROJECT_INPUT "
                "(docs/06_project_inputs_required.md item 21)", [21], ["physical_absorption"])
        m["physical_absorption"] = r
        m["potential_mip"] = _gate_record("engine.multislice", "potential_mip",
                                          _rec(None, "potential", "positive"), m["potential_mip"],
                                          allow_test_only=allow_test_only)
        if not (_is_int(m["n_realisations"]) and m["n_realisations"] >= 1):
            raise PipelineConfigError("sections.engine.multislice.n_realisations must be >= 1")
        if not (m["seed"] is None or (_is_int(m["seed"]) and m["seed"] >= 0)):
            raise PipelineConfigError("sections.engine.multislice.seed must be null (static "
                                      "lattice) or an integer >= 0 (frozen phonons)")
        if (m["frozen_phonons"] == "none") != (m["seed"] is None):
            raise PipelineConfigError("sections.engine.multislice: seed must be null exactly when "
                                      "frozen_phonons is 'none' (a static lattice has no seed)")
        _check_frozen_phonons(m, allow_test_only=allow_test_only)
        sb = m["sheet_beam"]
        if not (isinstance(sb, dict) and set(sb) == {"height_A", "edge_A",
                                                      "x_bottom_above_highest_surface_A"}):
            raise PipelineConfigError("sections.engine.multislice.sheet_beam must be {height_A, "
                                      "edge_A, x_bottom_above_highest_surface_A}")
        ab = m["absorber"]
        if not (isinstance(ab, dict) and set(ab) == {"strength_V", "profile"}):
            raise PipelineConfigError("sections.engine.multislice.absorber must be "
                                      "{strength_V, profile}")
        c = sections["cell"].get("multislice")
        if not (isinstance(c, dict) and set(c) == set(MS_CELL_KEYS)):
            raise PipelineConfigError(f"sections.cell.multislice must have exactly the keys "
                                      f"{MS_CELL_KEYS} (forward.cell.build_reflection_cell)")


def _check_frozen_phonons(m: dict, *, allow_test_only: bool) -> None:
    """The three forms of sections.engine.multislice.frozen_phonons (see THERMAL_MODEL_B35). The
    specimen temperature (PROJECT_INPUT item 23) is required with the sourced model and refused
    (not ignored) with the others."""
    from reflection_holo.structure import thermal
    fp = m["frozen_phonons"]
    where = "sections.engine.multislice.specimen_temperature"
    lab = m["static_lattice_label"]
    if fp == "none" or (isinstance(fp, dict) and set(fp) == FIXED_U_KEYS):
        if "specimen_temperature" in m:
            raise PipelineConfigError(
                f"{where}: not used with frozen_phonons "
                f"{'none (static lattice)' if fp == 'none' else 'given as a fixed u'}: refused "
                f"rather than ignored (use frozen_phonons: {{model: {THERMAL_MODEL_B35}}})")
    if fp == "none":
        # a static lattice is an explicit ASSUMPTION (audit A5 F2; refused altogether by purpose
        # "comparison", load_pipeline_dict)
        require_evidence_label(
            lab, "sections.engine.multislice.static_lattice_label (frozen_phonons 'none': a "
                 "static lattice, no Debye-Waller factor, item 23 not represented)",
            accepted=("ASSUMPTION",) + ((TEST_ONLY_LABEL,) if allow_test_only else ()),
            qualified=True, error=PipelineConfigError)
        return
    if lab is not None:
        raise PipelineConfigError(
            "sections.engine.multislice.static_lattice_label applies to frozen_phonons 'none' "
            "only (null otherwise): refused rather than ignored")
    if isinstance(fp, dict) and set(fp) == FIXED_U_KEYS:
        return
    if not (isinstance(fp, dict) and set(fp) == {"model"} and fp["model"] == THERMAL_MODEL_B35):
        raise PipelineConfigError(
            f"sections.engine.multislice.frozen_phonons must be 'none', {{model: "
            f"{THERMAL_MODEL_B35}}} (Si B(T) of Heacock et al. 2021, model_assumptions B35, with "
            f"{where}, PROJECT_INPUT item 23) or {{rms_displacement_A, label}} (a fixed u, e.g. "
            f"model_assumptions A7); got {fp!r}")
    if "specimen_temperature" not in m:
        raise MissingProjectInputError(
            f"{where} is a missing PROJECT_INPUT (item 23, specimen temperature during "
            f"holography): the thermal model {THERMAL_MODEL_B35} has no default temperature",
            [23], ["specimen_temperature"])
    r = _gate_record("engine.multislice", "specimen_temperature",
                     _rec(23, "temperature", "temperature"), m["specimen_temperature"],
                     allow_test_only=allow_test_only)
    if r.value is None:
        raise MissingProjectInputError(
            f"{where} is a missing PROJECT_INPUT (item 23, specimen temperature during "
            f"holography)", [23], ["specimen_temperature"])
    try:
        thermal.si_debye_waller_B_A2(r.canonical_value)
    except ValueError as exc:
        raise PipelineConfigError(f"{where}: {exc}") from exc
    m["specimen_temperature"] = r


def load_pipeline_file(path, *, variant: str | None) -> PipelineConfig:
    """Load and gate a pipeline configuration file (TEST_ONLY and duplicate keys refused)."""
    p = Path(path)
    blob = p.read_bytes()
    data = load_yaml_unique(blob)
    return load_pipeline_dict(data, variant=variant, allow_test_only=False, source_path=str(p),
                              sha256_file=hashlib.sha256(blob).hexdigest())


def read_pipeline_file(path) -> dict:
    """Parse (not gate) a pipeline configuration file; duplicate keys refused."""
    data = load_yaml_unique(Path(path).read_bytes())
    if not isinstance(data, dict):
        raise PipelineConfigError(f"{path}: not a YAML mapping")
    return data


# --------------------------------------------------------------------------------------------------
# list-inputs
# --------------------------------------------------------------------------------------------------
NOT_USED = {
    2: "not an input of this pipeline: energy spread and source size are not modelled (single "
       "plane-wave realisation; partial-coherence generators NOT IMPLEMENTED)",
    10: "not an input of a simulated run (the simulation defines its own axes and signs); "
        "required for experimental holograms",
    17: "not modelled: empty-hologram residual phase, biprism Fresnel fringes and overlap width "
        "(NOT IMPLEMENTED; divide_empty removes a static reference residual)",
    18: "not needed (the measured carrier, item 16, is used instead of biprism voltages)",
    21: "not an input of the geometric engine (no potential); required by the multislice engine "
        "(sections.engine.multislice.physical_absorption)",
    22: "not modelled: no charging phase (ASSUMPTION B8)",
    23: "not an input of this path: no thermal model (static lattice, geometric engine, or a fixed "
        "u such as model_assumptions A7); used by frozen_phonons {model: si_heacock2021_linear_B}",
}


def _path_usage(parameter: str, data: dict, sections: dict) -> str | None:
    """None if the parameter is used on the selected path, else the reason it is NOT USED there
    (audit A3 M6, m2). Physically relevant inputs that no path represents (convergence, overlayer,
    pattern geometry, a rule reflection other than item 9) are refused by the gate instead."""
    eng = (sections.get("engine") or {}).get("name")
    ga = ((sections.get("illumination") or {}).get("glancing_angle") or {}).get("value")
    rule = isinstance(ga, dict)
    v0_src = ga.get("V0_source") if rule else None
    params = (data.get("cfg_b") or {}).get("parameters") or {}
    ref_model = (params.get("reference_model") or {}).get("value")
    reasons = {
        "cfg_b.mean_inner_potential_V": (
            None if rule and v0_src == "cfg_b.mean_inner_potential_V" else
            "the glancing angle is typed, so V0 is not used" if not rule else
            "the glancing angle and the engine potential use "
            "sections.engine.multislice.potential_mip (listed below), not this V0"),
        "cfg_b.target_reflection_hkl": (
            None if rule else "the glancing angle is typed; the target reflection is not used"),
        "cfg_b.second_reflection_hkl": "one working condition is simulated per run",
        "cfg_b.recommended_reflections_hkl": "one working condition is simulated per run",
        "cfg_b.step_types": ("the steps are those of sections.structure.staircase (item 11); the "
                             "list of observables is not used"),
        "cfg_b.surface_preparation_method": ("the structure uses surface_preparation_details "
                                             "(termination, overlayer), not the method"),
        "cfg_b.reconstruction_method": ("the reconstruction uses "
                                        "sections.reconstruction.processing"),
        "sections.reference.aperture_passage": ("recorded only: the intrinsic 2 theta_ext "
                                                "inclination of an R1 reference and its "
                                                "compensation are NOT IMPLEMENTED"),
        "sections.reference.shift": (None if ref_model == "R2" else
                                     "the shift belongs to an R2 reference; this run uses "
                                     f"{ref_model}"),
        "sections.optics.loss_electron_visibility": _loss_visibility_usage(ref_model, sections),
    }
    if parameter == "sections.engine.multislice.potential_mip":
        return None
    return reasons.get(parameter)


def _r2_only_absent(parameter: str, data: dict, sections: dict) -> str | None:
    """Why an R2-only record is absent on a non-R2 path, or None (A5 F7, F10)."""
    params = (data.get("cfg_b") or {}).get("parameters") or {}
    ref = (params.get("reference_model") or {}).get("value")
    if ref == "R2":
        return None
    for (sec, name), what in R2_ONLY_RECORDS.items():
        if parameter == f"sections.{sec}.{name}":
            return f"{what}; this run uses {ref} (required with R2 only)"
    return None


def _loss_visibility_usage(ref_model, sections: dict) -> str | None:
    """Why the loss-electron visibility has no effect on this path, or None (report E3)."""
    if ref_model in ("R1", "R3"):
        return ("with a vacuum reference (R1) the reference arm carries no surface-plasmon loss "
                "electron, so the loss electrons of the object arm carry no fringes: the value has "
                "no effect (optics.inelastic)")
    n = ((sections.get("optics") or {}).get("surface_plasmon_excitations") or {})
    if isinstance(n, dict) and n.get("value") == 0:
        return "no loss electrons (surface_plasmon_excitations = 0): the value has no effect"
    return None


def _absent_reason(parameter: str, sections: dict) -> str | None:
    """Why an optional record that the selected path does not use is absent (agent T2), or None."""
    feature = "feature" in (sections.get("structure") or {})
    if parameter == "sections.structure.staircase" and feature:
        return ("the feature path has no staircase: the surface around the feature is flat and "
                "step-free, as stated by the feature stand-in (the miscut and terrace part of item 11 "
                "is not represented on this path)")
    if parameter == "sections.structure.feature" and not feature:
        return "no surface feature on this path (cfg_b.pattern_geometry {features: none})"
    if parameter == "sections.quantification.feature_processing" and not feature:
        return "staircase path: the feature height map is not computed"
    return None


def list_inputs(data: dict, *, variant: str | None) -> list[dict]:
    """Every PROJECT_INPUT item 1-23 with the parameters that carry it, their status and whether
    the selected path uses them, WITHOUT failing on a missing one (placeholder-level view;
    ``load_pipeline_dict`` is the run gate). A supplied value or stand-in that the path does not use
    is shown as "..., NOT USED on this path" with the reason (audit A3 M6); for the multislice
    engine the V0 actually used (sections.engine.multislice.potential_mip) is listed under item 20
    (audit A3 m2)."""
    sections = resolve_variant(data, variant)
    if isinstance(data.get("cfg_b"), dict):              # variant CFG-B records (report E4)
        data = dict(data, cfg_b=resolve_variant_cfg_b(data, variant))
    rows = []
    cfg_params = (data.get("cfg_b") or {}).get("parameters") or {}
    from reflection_holo.io.config import SCHEMAS
    schema_b = {**SCHEMAS["CFG-B"]["required"], **SCHEMAS["CFG-B"]["optional"]}
    for name, item in schema_b.items():
        if item is None:
            continue
        p = cfg_params.get(name)
        if name == "glancing_angle_ext":
            continue
        where = f"cfg_b.{name}"
        rows.append(_row(item, where, p, required=name in SCHEMAS["CFG-B"]["required"],
                         unused=_path_usage(where, data, sections)))
    for sec, schema in SECTIONS.items():
        for name, spec in schema.items():
            if spec["type"] != "record" or spec["item"] is None:
                continue
            p = (sections.get(sec) or {}).get(name)
            where = f"sections.{sec}.{name}"
            why = (_absent_reason(where, sections) or _r2_only_absent(where, data, sections)
                   if p is None else None)
            if why is not None:
                rows.append(dict(item=spec["item"], parameter=where, status="NOT USED on this path",
                                 value=None, detail=f"NOT USED on this path: {why}", used=False))
                continue
            ref = (((data.get("cfg_b") or {}).get("parameters") or {}).get("reference_model")
                   or {}).get("value")
            required = not spec["optional"] or (ref == "R2" and (sec, name) in R2_ONLY_RECORDS)
            rows.append(_row(spec["item"], where, p, required=required,
                             unused=_path_usage(where, data, sections)))
    eng = (sections.get("engine") or {})
    if eng.get("name") == "multislice":
        m = eng.get("multislice") or {}
        rows.append(_row(21, "sections.engine.multislice.physical_absorption",
                         m.get("physical_absorption"), required=True, unused=None))
        fpv = m.get("frozen_phonons")
        if isinstance(fpv, dict) and fpv.get("model") == THERMAL_MODEL_B35:
            rows.append(_row(23, "sections.engine.multislice.specimen_temperature",
                             m.get("specimen_temperature"), required=True, unused=None))
        mip = m.get("potential_mip")
        if isinstance(mip, dict):
            rows.append(dict(item=20, parameter="sections.engine.multislice.potential_mip",
                             status=f"{mip.get('label')}, USED (V0 of the engine potential and of "
                                    f"the glancing angle)",
                             value=mip.get("value"), detail=mip.get("source"), used=True))
    items_seen = {r["item"] for r in rows}
    for item, why in NOT_USED.items():
        if item not in items_seen:
            rows.append(dict(item=item, parameter="-", status="NOT USED", value=None, detail=why,
                             used=False))
    return sorted(rows, key=lambda r: (r["item"], r["parameter"]))


def _row(item: int, where: str, p, *, required: bool, unused: str | None) -> dict:
    if p is None:
        return dict(item=item, parameter=where, status="MISSING" if required else "absent (optional)",
                    value=None, detail="absent", used=False)
    label = p.get("label")
    v = p.get("value")
    if v is None:
        st = "MISSING" if label == "PROJECT_INPUT" else f"null ({label})"
        return dict(item=item, parameter=where, status=st, value=None, detail=p.get("source"),
                    used=False)
    if label == "PROJECT_INPUT":
        try:
            sup = check_supply(where, label, v, p)
            st = f"SUPPLIED ({sup['supplied_by']} {sup['supplied_on']})"
        except ConfigError:
            st = "INVALID (no valid supplied_by/supplied_on)"
    elif label == "ASSUMPTION":
        reg = assumption_registry()
        ok = item in reg.get(str(p.get("assumption_id")), ())
        st = (f"ASSUMPTION {p.get('assumption_id')} stand-in" if ok
              else f"INVALID (assumption_id {p.get('assumption_id')!r} not registered for item {item})")
    else:
        st = f"{label}"
    detail = p.get("source")
    if unused is not None:
        st = ("SUPPLIED, NOT USED on this path" if st.startswith("SUPPLIED") else
              f"{st}, NOT USED on this path")
        detail = f"NOT USED on this path: {unused}"
    return dict(item=item, parameter=where, status=st, value=v, detail=detail,
                used=unused is None)


def format_inputs(rows: list[dict]) -> str:
    lines = [f"{'item':>4}  {'status':<50} {'parameter':<46} value"]
    for r in rows:
        val = json.dumps(r["value"], sort_keys=True, default=str) if r["value"] is not None else "-"
        if len(val) > 60:
            val = val[:57] + "..."
        lines.append(f"{r['item']:>4}  {r['status']:<50} {r['parameter']:<46} {val}")
        if not r.get("used", True) and str(r.get("detail", "")).startswith("NOT USED"):
            lines.append(f"{'':>4}  -> {r['detail']}")
    return "\n".join(lines)

