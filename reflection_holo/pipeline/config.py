"""Pipeline configuration: a schema extending CFG-B, gated like every configuration of the package.

docs/05 section 0 criterion 5 (no result may depend on a default silently substituted for a missing
PROJECT_INPUT: such runs fail), sections 4.5 and 5; docs/06 (PROJECT_INPUT items 1-22).

File layout (YAML; duplicate keys refused anywhere, ``io.config.load_yaml_unique``):

    pipeline_schema: 1
    run_name: <name>
    purpose: "demo; not comparable to experiment" | "comparison"
    description: <text>
    cfg_b: {schema_version, config_id: CFG-B, name: si001_patterned, status, description,
            parameters: {...}}                         # a CFG-B configuration (io.config schema)
    sections: {structure, cell, engine, illumination, optics, reference, detector,
               reconstruction, quantification, runtime, outputs}
    variants: {<name>: {description, sections: {...partial overrides...}}}     # optional

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
explicit choice of the caller, recorded in every output.
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
from reflection_holo.io.config import (SUPPLIER_DATE_RE, UNITS, ConfigError, LoadedConfig,
                                       MissingProjectInputError, assumption_registry,
                                       canonical_sha256, load_config_dict, load_yaml_unique)
from reflection_holo.io.labels import EVIDENCE_LABELS, TEST_ONLY_LABEL, require_evidence_label

PIPELINE_SCHEMA = 1
PURPOSES = ("demo; not comparable to experiment", "comparison")
BLOCKING_ITEMS = (3, 4, 5, 7, 8, 11, 12, 15)                 # docs/06 "(blocking)"
PIPELINE_UNITS: dict[str, tuple[str, float | None]] = dict(UNITS)
PIPELINE_UNITS.update({"e/px": ("dose_per_pixel", 1.0), "counts/e": ("gain", 1.0),
                       "deg": ("angle", math.pi / 180.0)})
CANONICAL = {"length": "A", "angle": "rad", "energy": "keV", "potential": "V", "none": "none",
             "dose_per_pixel": "e/px", "gain": "counts/e"}
RECORD_KEYS_REQUIRED = ("value", "label", "source", "unit")
RECORD_KEYS_OPTIONAL = ("item", "stands_in_for_item", "assumption_id", "note")
TOP_KEYS_REQUIRED = ("pipeline_schema", "run_name", "purpose", "description", "cfg_b", "sections")
TOP_KEYS_OPTIONAL = ("variants",)
ENGINES = ("geometric", "multislice")
GLANCING_RULES = ("internal_bragg_external_angle",)


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
        "staircase": _rec(11, "none", "staircase"),
        "edge_periods": _plain("int_pos"),
        "substrate_layers": _plain("int_ge4"),
        "vacuum_above_A": _plain("float_pos"),
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
    },
    "optics": {
        "selected_beam": _rec(4, "none", "beam"),
        "projection_reference": _plain("enum", choices=("lowest_terrace_top",)),
        "lens_transfer": _plain("enum", choices=("none",)),
    },
    "reference": {
        "carrier_fringe_spacing": _rec(16, "length", "positive"),
        "carrier_direction": _rec(16, "angle", "finite"),
        "amplitude_ratio": _rec(16, "none", "positive"),
        "aperture_passage": _rec(15, "none", "aperture_passage"),
        "shift": _rec(16, "length", "pixel_pair", optional=True),
        "relative_phase_rad": _plain("float"),
    },
    "detector": {
        "pixel_pitch": _rec(5, "length", "pixel_size"),
        "magnification": _rec(5, "none", "positive"),
        "dose": _rec(6, "dose_per_pixel", "positive"),
        "gain": _rec(6, "gain", "positive"),
        "mtf": _rec(6, "none", "mtf"),
        "roi_shape": _plain("int_pair"),
        "alignment": _plain("enum", choices=("centre",)),
        "noise_seed": _plain("seed"),
    },
    "reconstruction": {
        "processing": _rec(19, "none", "reconstruction"),
    },
    "quantification": {
        "processing": _rec(19, "none", "quantification"),
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
              "max_layers": "int_pos", "n_sigma": "positive", "min_region_px": "int_pos"}
STAIRCASE_KEYS = ("edges", "terrace_layers", "terrace_widths_periods", "boundary_step_layers",
                  "first_terrace_backbond_uvw")
GEOMETRIC_KEYS = {"exit_plane_pixel_A": "xy_pos", "n_y": "int_pos", "x_margin_A": "float_pos",
                  "reflectivity_amplitude": "float_pos", "invisibility_tol_cycles": "float_nonneg"}
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
        return [v for sec in self.sections.values() for v in sec.values() if isinstance(v, Record)]


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
    elif kind == "glancing":
        if dim == "angle":
            if not (_is_num(v) and v > 0):
                bad("a positive angle")
        elif not (isinstance(v, dict) and set(v) == {"rule", "reflection_hkl"}
                  and v["rule"] in GLANCING_RULES and isinstance(v["reflection_hkl"], list)
                  and len(v["reflection_hkl"]) == 3 and all(_is_int(a) for a in v["reflection_hkl"])):
            bad(f"a positive angle, or {{rule: one of {GLANCING_RULES}, reflection_hkl: [h,k,l]}}")
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
    elif kind == "reconstruction":
        _check_mapping(where, v, RECON_KEYS)
    elif kind == "quantification":
        _check_mapping(where, v, QUANT_KEYS)
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
            if value is not None:
                m = SUPPLIER_DATE_RE.search(source)
                ok = m is not None
                if ok:
                    try:
                        _dt.date.fromisoformat(m.group("date"))
                    except ValueError:
                        ok = False
                if not ok:
                    _fail(where, f"PROJECT_INPUT item {want} has a value, so its source must name "
                                 f"the supplier and the date, 'supplied by <name> <YYYY-MM-DD>'")
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
                  source=source, item=want, stands_in_for_item=sfi, assumption_id=aid, note=note)


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and not (
                {"value", "label"} <= set(v)):          # records are replaced whole
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def resolve_variant(data: dict, variant: str | None) -> dict:
    """Base sections, or the base deep-merged with ``variants[variant].sections``."""
    if variant is None:
        return copy.deepcopy(data["sections"])
    variants = data.get("variants") or {}
    if variant not in variants:
        raise PipelineConfigError(f"unknown variant {variant!r}; defined: {sorted(variants)}")
    v = variants[variant]
    if not isinstance(v, dict) or set(v) != {"description", "sections"}:
        raise PipelineConfigError(f"variant {variant!r} must be {{description, sections}}")
    return _deep_merge(data["sections"], v["sections"])


def _glancing_angle(rec: Record, cfg_b_params: dict) -> dict:
    """Value of the glancing angle: supplied/assumed number, or computed by the declared rule."""
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
        try:
            sc = specular_condition_for(tuple(hkl), tuple(vals["surface_normal_hkl"]),
                                        E_keV=float(vals["beam_energy_keV"]),
                                        V0_V=float(vals["mean_inner_potential_V"]),
                                        a_A=float(vals["lattice_parameter"]))
        except GeometryError as exc:
            raise PipelineConfigError(f"glancing-angle rule: {exc}") from exc
        return dict(value_rad=float(sc.theta_ext), rule=rec.value["rule"], reflection_hkl=list(hkl),
                    theta_int_rad=float(sc.theta_int), h_2pi_A=float(sc.h_2pi_A),
                    computed_by="reflection_holo.geometry.specular.specular_condition_for",
                    V0_V=float(vals["mean_inner_potential_V"]),
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
    src = rec.source
    if ga["rule"] is not None:
        src = (f"{rec.source}; computed by the pipeline: {ga['computed_by']}"
               f"({tuple(ga['reflection_hkl'])}) at V0 = {ga['V0_V']} V (not typed)")
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
    if missing_items:
        listing = "; ".join(f"item {i} ({n})" for n, i in sorted(missing_items, key=lambda t: t[1]))
        raise MissingProjectInputError(
            f"pipeline run refused, missing PROJECT_INPUT (docs/06_project_inputs_required.md): "
            f"{listing}", [i for _, i in missing_items], [n for n, _ in missing_items])
    _check_engine(sections, allow_test_only=allow_test_only)
    ga_rec = sections["illumination"]["glancing_angle"]
    cfg_b_raw = data["cfg_b"]
    if not isinstance(cfg_b_raw, dict):
        raise PipelineConfigError("cfg_b must be a CFG-B configuration mapping")
    ga = _glancing_angle(ga_rec, cfg_b_raw.get("parameters") or {})
    cfg_b_full = _cfg_b_with_angle(cfg_b_raw, ga, ga_rec)
    cfg_b = load_config_dict(cfg_b_full, level="run", allow_test_only=allow_test_only)
    if cfg_b.config_id != "CFG-B":
        raise PipelineConfigError("cfg_b must be a CFG-B configuration")
    test_only = cfg_b.test_only or any(
        isinstance(v, Record) and v.label == TEST_ONLY_LABEL
        for s in sections.values() for v in s.values())
    if data["purpose"] == "comparison":
        stand_ins = [f"{r.section}.{r.name} (item {r.item})" for s in sections.values()
                     for r in s.values() if isinstance(r, Record) and r.label == "ASSUMPTION"
                     and r.item in BLOCKING_ITEMS]
        stand_ins += [f"cfg_b.{p.name} (item {p.item})" for p in cfg_b.parameters.values()
                      if p.label == "ASSUMPTION" and p.item in BLOCKING_ITEMS]
        if stand_ins or test_only:
            raise PipelineConfigError(
                f"purpose 'comparison' refuses ASSUMPTION stand-ins for blocking PROJECT_INPUT "
                f"items and TEST_ONLY values: {stand_ins or 'TEST_ONLY present'}")
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


def _check_engine(sections: dict, *, allow_test_only: bool) -> None:
    eng = sections["engine"]
    name = eng["name"]
    if name not in eng:
        raise PipelineConfigError(f"sections.engine.{name} (the parameters of the selected engine) "
                                  f"is required")
    if name == "geometric":
        g = eng["geometric"]
        if set(g) != set(GEOMETRIC_KEYS):
            raise PipelineConfigError(f"sections.engine.geometric must have exactly the keys "
                                      f"{sorted(GEOMETRIC_KEYS)}, got {sorted(g)}")
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
        if "absorptive_potential" not in m:
            raise MissingProjectInputError(
                "sections.engine.multislice.absorptive_potential is a missing PROJECT_INPUT "
                "(docs/06_project_inputs_required.md item 21)", [21], ["absorptive_potential"])
        r = _gate_record("engine.multislice", "absorptive_potential", _rec(21, "none", "mapping"),
                         m["absorptive_potential"], allow_test_only=allow_test_only)
        if r.value is None:
            raise MissingProjectInputError(
                "sections.engine.multislice.absorptive_potential is a missing PROJECT_INPUT "
                "(docs/06_project_inputs_required.md item 21)", [21], ["absorptive_potential"])
        m["absorptive_potential"] = r
        for k, lo in (("n_realisations", 1), ("seed", 0)):
            if not (_is_int(m.get(k)) and m[k] >= lo):
                raise PipelineConfigError(f"sections.engine.multislice.{k} must be an integer "
                                          f">= {lo} (required, no default)")


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
    22: "not modelled: no charging phase (ASSUMPTION B8)",
}


def list_inputs(data: dict, *, variant: str | None) -> list[dict]:
    """Every PROJECT_INPUT item 1-22 with the parameters that carry it and their status, WITHOUT
    failing on a missing one (placeholder-level view; ``load_pipeline_dict`` is the run gate)."""
    sections = resolve_variant(data, variant)
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
        rows.append(_row(item, f"cfg_b.{name}", p, required=name in SCHEMAS["CFG-B"]["required"]))
    for sec, schema in SECTIONS.items():
        for name, spec in schema.items():
            if spec["type"] != "record" or spec["item"] is None:
                continue
            p = (sections.get(sec) or {}).get(name)
            rows.append(_row(spec["item"], f"sections.{sec}.{name}", p,
                             required=not spec["optional"]))
    eng = (sections.get("engine") or {})
    if eng.get("name") == "multislice":
        p = (eng.get("multislice") or {}).get("absorptive_potential")
        rows.append(_row(21, "sections.engine.multislice.absorptive_potential", p, required=True))
    items_seen = {r["item"] for r in rows}
    for item, why in NOT_USED.items():
        if item not in items_seen:
            rows.append(dict(item=item, parameter="-", status="NOT USED", value=None, detail=why))
    return sorted(rows, key=lambda r: (r["item"], r["parameter"]))


def _row(item: int, where: str, p, *, required: bool) -> dict:
    if p is None:
        return dict(item=item, parameter=where, status="MISSING" if required else "absent (optional)",
                    value=None, detail="absent")
    label = p.get("label")
    v = p.get("value")
    if v is None:
        st = "MISSING" if label == "PROJECT_INPUT" else f"null ({label})"
        return dict(item=item, parameter=where, status=st, value=None, detail=p.get("source"))
    if label == "PROJECT_INPUT":
        m = SUPPLIER_DATE_RE.search(str(p.get("source", "")))
        st = f"SUPPLIED ({m.group('who')} {m.group('date')})" if m else "INVALID (no supplier/date)"
    elif label == "ASSUMPTION":
        reg = assumption_registry()
        ok = item in reg.get(str(p.get("assumption_id")), ())
        st = (f"ASSUMPTION {p.get('assumption_id')} stand-in" if ok
              else f"INVALID (assumption_id {p.get('assumption_id')!r} not registered for item {item})")
    else:
        st = f"{label}"
    return dict(item=item, parameter=where, status=st, value=v, detail=p.get("source"))


def format_inputs(rows: list[dict]) -> str:
    lines = [f"{'item':>4}  {'status':<34} {'parameter':<46} value"]
    for r in rows:
        val = json.dumps(r["value"], sort_keys=True) if r["value"] is not None else "-"
        if len(val) > 60:
            val = val[:57] + "..."
        lines.append(f"{r['item']:>4}  {r['status']:<34} {r['parameter']:<46} {val}")
    return "\n".join(lines)

