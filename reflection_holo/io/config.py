"""Assertion-based loader of the named configurations (CFG-A, CFG-B, CFG-O).

docs/05_final_repository_specification.md sections 0 (criterion 5), 2 and 3 (io/); source policy of
docs/06_project_inputs_required.md. Every parameter is a mapping with the keys
    value   the value (null allowed only for a PROJECT_INPUT or an UNVERIFIED field)
    label   one of the seven evidence labels
            METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE,
            UNVERIFIED
            (TEST_ONLY is accepted only for in-memory test fixtures, never from a file)
    source  where the value comes from (file, section, item, sentence)
    unit    REQUIRED for every parameter: a unit of the one unit table UNITS whose dimension matches
            the parameter, or "none" for a parameter that is not a physical quantity (strings,
            Miller indices, mappings of labels). An unknown unit fails.
and optionally
    item                the docs/06 item number. REQUIRED, whatever the label, when the
                        configuration's schema (SCHEMAS) gives the parameter a docs/06 item, and
                        refused otherwise; a PROJECT_INPUT without a docs/06 item fails.
    stands_in_for_item  REQUIRED (equal to item) for an ASSUMPTION value standing in for a docs/06
                        item, together with
    assumption_id       the model_assumptions row that states the assumption (e.g. "B1"); it must be
                        mapped to that item by the package registry assumption_registry.yaml
                        (loaded with importlib.resources; A2b N1, N9). Refused on any parameter
                        without a docs/06 item.
    note

Labels on a parameter whose schema names a docs/06 item (re-audit A2b N1). Only three states:
  * PROJECT_INPUT, null (the input is missing: listed at placeholder level, fails at run level), or
    with a value and the two STRUCTURED fields (A2c G2; they replace the former free-text rule
    "supplied by <name> <YYYY-MM-DD>" in the source)
        supplied_by  the person who supplied the value (a non-empty name; placeholders such as
                     "nobody", "unknown", "the simulation" and negations "not ..." are refused)
        supplied_on  the ISO date "YYYY-MM-DD" (a YAML date is accepted) of the supply, a valid date
                     not in the future (compared with the current date at UTC+14, the latest
                     calendar date anywhere);
    both fields are refused on any other parameter;
  * ASSUMPTION with stands_in_for_item = item and an assumption_id registered for that item;
  * TEST_ONLY, accepted only from in-memory test fixtures (allow_test_only=True; never from a file,
    and recorded as test_only).
Any other label (DERIVED_HERE, SECTION_READ, REPRODUCED, METADATA_VERIFIED, UNVERIFIED) fails.
Numbers must be finite (A2b N8).
Unknown keys, unknown parameter names, parameters outside the configuration's schema and duplicate
YAML keys (anywhere in the file) are refused.

Schemas (SCHEMAS, audit A2 M2): each configuration type lists its REQUIRED parameters with their
docs/06 item numbers (None: not a laboratory input of that configuration, e.g. a CFG-A benchmark
definition) and its optional parameters. A required parameter that is ABSENT counts exactly like a
null one: it is listed at placeholder level and fails at run level, naming its item.

Two load levels, stated by the caller (no default):
  * level="run": a PROJECT_INPUT that is null or absent FAILS (MissingProjectInputError naming the
    docs/06 item numbers); any UNVERIFIED field FAILS (UnverifiedParameterError); an absent
    required parameter without a docs/06 item FAILS (MissingRequiredParameterError); a
    configuration whose status is "placeholder" FAILS. No default ever replaces a missing input.
  * level="placeholder": the configuration is validated and returned with the missing, absent and
    unverified fields listed; value() still refuses to return a null or an absent parameter.

Units (audit A2 m5): parameters are stored as declared (value(), e.g. 16.5 with unit "mrad") and
converted through UNITS to the canonical units of the code, A, rad, keV and V (quantity(), e.g.
(0.0165, "rad")); docs/physics_conventions.md, "Angstrom everywhere in code", angles "stored in
radians". A parameter name carries a unit suffix only when that is the one unit it accepts
(beam_energy_keV, mean_inner_potential_V).

Energy rule: the beam energy is 200 keV for every configuration (PROJECT_INPUT item 1, Ali,
2026-09-22; reflection_holo.constants.BEAM_ENERGY_SUPPLIED_KEV). Any other stated energy fails at
every level; CFG-A and CFG-B must state it (null fails at every level). CFG-O's energy is UNVERIFIED
(null) until the body of P01 is read.
Materials (audit A2 m10): surface_material must be a canonical element symbol, and the one of its
configuration: "Si" for CFG-A and CFG-B, "Pt" for CFG-O; any other spelling fails, so the silicon
cross-checks cannot be skipped. Defining values (A2c G1, PINNED): a configuration is identified by
its geometry (docs/05 section 2), so CFG-A must have surface (1,-1,1), azimuth [1,1,0] and material
Si, and CFG-B surface (0,0,1); any other value is refused (an experiment cannot be declared as the
CFG-A benchmark to skip the CFG-B gate). The imaging inputs of CFG-A (glancing angle, convergence,
aperture, pixel size, reference trajectory, reconstruction method) carry their docs/06 items as in
CFG-B, so they pass the same PROJECT_INPUT gate. Crystallographic cross-checks for silicon configurations: the
azimuth must lie in the surface plane (reflection_holo.geometry.frames.surface_frame); a target
reflection must be on the specular rod, allowed (forbidden-reflection guard, SM02) and accessible
(SM04, SM06); every reflection listed as forbidden must indeed have F = 0.
"""
from __future__ import annotations

import copy
import datetime as _dt
import functools
import hashlib
import importlib.resources
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.geometry.crystal import diamond_allowed, rod_decomposition
from reflection_holo.geometry.errors import GeometryError
from reflection_holo.geometry.frames import surface_frame
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.io.labels import EVIDENCE_LABELS, TEST_ONLY_LABEL, require_evidence_label
from reflection_holo.optics.hologram import REFERENCE_MODELS  # docs/05 section 5 item 3

LEVELS = ("run", "placeholder")
STATUSES = ("benchmark", "experiment", "placeholder")
CONFIG_IDS = {"CFG-A": "si111_cleaved_110azimuth", "CFG-B": "si001_patterned",
              "CFG-O": "osakabe_1988_reproduction"}
N_PROJECT_INPUT_ITEMS = 23      # item 23: specimen temperature during holography (report E2;
                                # docs/06 row to be added by the orchestrator)
PARAM_KEYS_REQUIRED = ("value", "label", "source", "unit")
SUPPLY_KEYS = ("supplied_by", "supplied_on")                 # A2c G2: structured supply record
PARAM_KEYS_OPTIONAL = ("item", "stands_in_for_item", "assumption_id", "note") + SUPPLY_KEYS
NON_SUPPLIERS = ("nobody", "no one", "noone", "none", "unknown", "anonymous", "n/a", "na", "tbd",
                 "todo", "simulation", "the simulation", "pipeline", "the pipeline", "code",
                 "the code", "default", "assumption", "not supplied", "auto", "automatic")
TOP_KEYS = ("schema_version", "config_id", "name", "status", "description", "parameters")
REFERENCE_TRAJECTORIES = ("vacuum_beside_sample", "reflected_flat_area",
                          "transmitted_thin_region")        # docs/06 item 15
STEP_EDGE_ORIENTATIONS = ("parallel_to_beam", "transverse_to_beam")
# step-type names (a vocabulary, so a misspelt or retired name fails). The relation of each step
# (translation, screw, glide) is stated in step_translations, not in the name (review E4 m8).
STEP_TYPES = ("lattice_translation_bilayer", "single_layer_a4", "double_layer_a2_translation",
              "patterned_mesa_trench", "monatomic_height_steps")
MATERIALS = ("Si", "Pt")                                    # canonical element symbols only
REGISTRY_RESOURCE = "assumption_registry.yaml"              # package data of reflection_holo.io
SUPPLIER_DATE_RE = re.compile(r"supplied by (?P<who>[A-Za-z][^,;:()]*?) (?P<date>\d{4}-\d{2}-\d{2})\b")

# The one unit table: unit -> (dimension, factor to the canonical unit of that dimension).
UNITS: dict[str, tuple[str, float | None]] = {
    "A": ("length", 1.0), "nm": ("length", 10.0), "um": ("length", 1.0e4),
    "rad": ("angle", 1.0), "mrad": ("angle", 1.0e-3),
    "keV": ("energy", 1.0),
    "V": ("potential", 1.0),
    "none": ("none", None),
}
CANONICAL_UNITS = {"length": "A", "angle": "rad", "energy": "keV", "potential": "V", "none": "none"}

# name -> (kind, dimension)
PARAMETERS: dict[str, tuple[str, str]] = {
    "surface_material": ("material", "none"),
    "surface_normal_hkl": ("int3", "none"),
    "beam_azimuth_uvw": ("int3", "none"),
    "beam_energy_keV": ("positive", "energy"),
    "lattice_parameter": ("positive", "length"),
    "mean_inner_potential_V": ("positive", "potential"),
    "target_reflection_hkl": ("int3", "none"),
    "second_reflection_hkl": ("int3", "none"),
    "recommended_reflections_hkl": ("int3_list", "none"),
    "not_recommended_reflections_hkl": ("int3_list", "none"),
    "forbidden_rod_reflections_hkl": ("int3_list", "none"),
    "step_types": ("step_types", "none"),
    "step_translations": ("mapping", "none"),
    "step_edge_orientations": ("edge_orientations", "none"),
    "glancing_angle_ext": ("positive", "angle"),
    "convergence_semi_angle": ("nonnegative", "angle"),
    "objective_aperture_semi_angle": ("positive", "angle"),
    "image_pixel_size": ("pixel_size", "length"),
    "reference_trajectory": ("reference_trajectory", "none"),
    "reference_model": ("reference_model", "none"),
    "pattern_geometry": ("mapping", "none"),
    "surface_preparation_method": ("str", "none"),
    "surface_preparation_details": ("mapping", "none"),
    "reflection_order": ("str", "none"),
    "height_sensitivity": ("positive", "length"),
    "reconstruction_method": ("str", "none"),
    "literature_source": ("str", "none"),
}

# Per configuration type: the material, the REQUIRED parameters and the optional ones, each with its
# docs/06 item number (None: not a laboratory input of this configuration). CFG-A is a benchmark
# defined by docs/05 section 2: its geometry, target reflection and imaging choices are benchmark
# definitions, not laboratory inputs; only the beam energy (item 1, supplied) and V0 (item 20) are
# docs/06 items there. Its imaging inputs are optional (a hologram simulation of CFG-A must declare
# them, and value() refuses an absent one). CFG-B is Ali's experiment (docs/06). CFG-O reproduces
# P01; its values come from the literature, not from docs/06. The lattice parameter is no docs/06
# item in any schema, so model_assumptions B2 is not a PROJECT_INPUT stand-in.
SCHEMAS: dict[str, dict[str, Any]] = {
    "CFG-A": dict(
        material="Si",
        required={"surface_material": None, "surface_normal_hkl": None, "beam_azimuth_uvw": None,
                  "beam_energy_keV": 1, "lattice_parameter": None, "mean_inner_potential_V": 20,
                  "target_reflection_hkl": None, "recommended_reflections_hkl": None,
                  "forbidden_rod_reflections_hkl": None, "step_types": None,
                  "step_translations": None, "step_edge_orientations": None},
        # imaging inputs of a CFG-A hologram simulation: the same docs/06 items as CFG-B, so they
        # pass the same PROJECT_INPUT gate (A2c G1)
        optional={"second_reflection_hkl": None, "not_recommended_reflections_hkl": None,
                  "glancing_angle_ext": 7, "convergence_semi_angle": 3,
                  "objective_aperture_semi_angle": 4, "image_pixel_size": 5,
                  "reference_trajectory": 15, "reference_model": None,
                  "reconstruction_method": 19}),
    "CFG-B": dict(
        material="Si",
        required={"surface_material": 11, "surface_normal_hkl": 11, "beam_azimuth_uvw": 8,
                  "beam_energy_keV": 1, "lattice_parameter": None, "mean_inner_potential_V": 20,
                  "target_reflection_hkl": 9, "forbidden_rod_reflections_hkl": None,
                  "step_types": 14, "step_translations": None, "glancing_angle_ext": 7,
                  "convergence_semi_angle": 3, "objective_aperture_semi_angle": 4,
                  "image_pixel_size": 5, "reference_trajectory": 15, "pattern_geometry": 13,
                  "surface_preparation_method": 12, "surface_preparation_details": 12},
        optional={"second_reflection_hkl": 9, "recommended_reflections_hkl": 9,
                  "not_recommended_reflections_hkl": None, "step_edge_orientations": None,
                  "reference_model": None, "reconstruction_method": 19}),
    "CFG-O": dict(
        material="Pt",
        required={"literature_source": None, "surface_material": None, "surface_normal_hkl": None,
                  "beam_azimuth_uvw": None, "beam_energy_keV": None, "reflection_order": None,
                  "glancing_angle_ext": None, "step_types": None, "height_sensitivity": None,
                  "reference_model": None, "reconstruction_method": None},
        optional={}),
}


# Defining values of each configuration (A2c G1): any other value is refused.
PINNED: dict[str, dict[str, Any]] = {
    "CFG-A": {"surface_material": "Si", "surface_normal_hkl": [1, -1, 1],
              "beam_azimuth_uvw": [1, 1, 0]},
    "CFG-B": {"surface_material": "Si", "surface_normal_hkl": [0, 0, 1]},
    "CFG-O": {"surface_material": "Pt"},
}


class ConfigError(ValueError):
    """Invalid configuration (schema, label, unit, value or crystallographic cross-check)."""


class MissingProjectInputError(ConfigError):
    """A PROJECT_INPUT is null or absent at run level. .items holds the docs/06 item numbers."""

    def __init__(self, message: str, items: list[int], names: list[str]):
        super().__init__(message)
        self.items = items
        self.names = names


class MissingRequiredParameterError(ConfigError):
    """A required parameter without a docs/06 item is absent at run level. .names holds them."""

    def __init__(self, message: str, names: list[str]):
        super().__init__(message)
        self.names = names


class UnverifiedParameterError(ConfigError):
    """An UNVERIFIED field was requested at run level. .names holds the parameter names."""

    def __init__(self, message: str, names: list[str]):
        super().__init__(message)
        self.names = names


class PlaceholderConfigError(ConfigError):
    """A placeholder configuration was requested at run level."""


@dataclass(frozen=True)
class Parameter:
    name: str
    value: Any
    label: str
    source: str
    unit: str
    item: int | None = None
    note: str | None = None
    stands_in_for_item: int | None = None
    assumption_id: str | None = None
    canonical_value: Any = None           # value converted through UNITS (None when null)
    canonical_unit: str = "none"
    supply: dict | None = None            # {supplied_by, supplied_on} of a supplied PROJECT_INPUT


@dataclass
class LoadedConfig:
    config_id: str
    name: str
    status: str
    description: str
    schema_version: int
    level: str
    parameters: dict[str, Parameter]
    missing_project_inputs: list[tuple[str, int]]      # null or absent, with docs/06 item
    unverified: list[str]
    test_only: bool
    sha256_canonical: str
    source_path: str | None = None
    sha256_file: str | None = None
    missing_required: list[tuple[str, int | None]] = field(default_factory=list)   # absent
    raw: dict = field(default_factory=dict, repr=False)

    def _absent(self, name: str):
        req = SCHEMAS[self.config_id]["required"]
        if name in req:
            item = req[name]
            if item is not None:
                raise MissingProjectInputError(
                    f"{self.config_id}: {name} is a missing PROJECT_INPUT (absent from the "
                    f"configuration; docs/06_project_inputs_required.md item {item})", [item], [name])
            raise MissingRequiredParameterError(
                f"{self.config_id}: required parameter {name} is absent", [name])
        raise ConfigError(f"{self.config_id}: parameter {name!r} is not defined")

    def value(self, name: str):
        """Return a parameter value as declared; refuses a null or absent one (naming the docs/06
        item) and an unknown name. Source map: no row; evidence label: not applicable."""
        if name not in self.parameters:
            self._absent(name)
        p = self.parameters[name]
        if p.value is None:
            if p.label == "PROJECT_INPUT":
                raise MissingProjectInputError(
                    f"{self.config_id}: {name} is a missing PROJECT_INPUT "
                    f"(docs/06_project_inputs_required.md item {p.item})", [p.item], [name])
            raise UnverifiedParameterError(f"{self.config_id}: {name} is UNVERIFIED (null)",
                                           [name])
        return copy.deepcopy(p.value)

    def quantity(self, name: str) -> tuple[Any, str]:
        """(value in the canonical unit, canonical unit): A, rad, keV or V, converted through the
        one unit table UNITS. Refuses nulls, absent names and parameters without a physical unit.
        Source map: no row; evidence label: not applicable (unit conversion)."""
        self.value(name)
        p = self.parameters[name]
        if p.canonical_unit == "none":
            raise ConfigError(f"{self.config_id}: {name} has no physical unit; use value()")
        return copy.deepcopy(p.canonical_value), p.canonical_unit

    def label(self, name: str) -> str:
        return self.parameters[name].label


def canonical_sha256(data: dict) -> str:
    """SHA-256 of the canonical JSON form (sorted keys, no whitespace) of a configuration.
    Source map: no row (software requirement, docs/05 sections 0 and 3); evidence label: not
    applicable (no physical claim)."""
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      default=_json_date)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _json_date(x):
    if isinstance(x, _dt.date):                    # a YAML date (supplied_on)
        return x.isoformat()
    raise TypeError(f"not JSON serialisable: {type(x).__name__}")


def latest_today() -> _dt.date:
    """The latest calendar date anywhere on Earth now (UTC+14): a supply date after it is in the
    future everywhere."""
    return (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=14)).date()


def check_supply(where: str, label: str, value, spec: dict, *, error=None) -> dict | None:
    """Structured supply record of a PROJECT_INPUT with a value (A2c G2): returns
    {supplied_by, supplied_on (ISO string)}; refuses missing, empty, placeholder or negated
    suppliers, invalid dates and dates in the future; refuses the fields on anything else.
    Source map: no row; evidence label: not applicable (configuration policy)."""
    err = error or ConfigError
    present = [k for k in SUPPLY_KEYS if k in spec]
    if not (label == "PROJECT_INPUT" and value is not None):
        if present:
            raise err(f"{where}: {present} are only for a PROJECT_INPUT with a value (label "
                      f"{label}{', value null' if value is None else ''}; A2c G2)")
        return None
    missing = [k for k in SUPPLY_KEYS if k not in spec]
    if missing:
        raise err(f"{where}: a PROJECT_INPUT with a value must state who supplied it and when, in "
                  f"the structured fields 'supplied_by: <name>' and 'supplied_on: <YYYY-MM-DD>' "
                  f"(missing {missing}; the free-text 'supplied by' rule is retired, A2c G2)")
    who = spec["supplied_by"]
    if not isinstance(who, str) or not who.strip():
        raise err(f"{where}: supplied_by must be a non-empty name, got {who!r}")
    low = " ".join(who.strip().lower().split())
    if low in NON_SUPPLIERS or low.startswith(("not ", "no ", "nobody")):
        raise err(f"{where}: supplied_by {who!r} does not name a person who supplied the value "
                  f"(A2c G2)")
    when = spec["supplied_on"]
    if isinstance(when, _dt.datetime):
        raise err(f"{where}: supplied_on must be a date 'YYYY-MM-DD', not a date-time")
    if isinstance(when, _dt.date):
        day = when
    elif isinstance(when, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
        try:
            day = _dt.date.fromisoformat(when)
        except ValueError:
            raise err(f"{where}: supplied_on {when!r} is not a valid date") from None
    else:
        raise err(f"{where}: supplied_on must be an ISO date 'YYYY-MM-DD', got {when!r}")
    if day > latest_today():
        raise err(f"{where}: supplied_on {day.isoformat()} is in the future (A2c G2)")
    return dict(supplied_by=who.strip(), supplied_on=day.isoformat())


@functools.lru_cache(maxsize=1)
def _registry_cached() -> tuple:
    try:
        text = importlib.resources.files("reflection_holo.io").joinpath(REGISTRY_RESOURCE).read_text(
            encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"assumption registry {REGISTRY_RESOURCE} unreadable ({exc})") from exc
    data = load_yaml_unique(text)
    if not isinstance(data, dict) or data.get("schema_version") != 1 \
            or not isinstance(data.get("stand_ins"), dict) \
            or set(data) != {"schema_version", "stand_ins", "demo_only", "model_rows"}:
        raise ConfigError(f"{REGISTRY_RESOURCE}: expected {{schema_version: 1, stand_ins: {{...}}, "
                          f"demo_only: [...], model_rows: {{...}}}}")
    out = []
    for aid, items in data["stand_ins"].items():
        if not (isinstance(aid, str) and re.fullmatch(r"B\d+", aid)):
            raise ConfigError(f"{REGISTRY_RESOURCE}: {aid!r} is not a model_assumptions B-row id")
        if not (isinstance(items, list) and items
                and all(_is_int(i) and 1 <= i <= N_PROJECT_INPUT_ITEMS for i in items)):
            raise ConfigError(f"{REGISTRY_RESOURCE}: {aid} must map to docs/06 item numbers")
        out.append((aid, tuple(items)))
    demo = data["demo_only"]
    if not (isinstance(demo, list) and all(isinstance(a, str) and a in data["stand_ins"]
                                           for a in demo) and len(set(demo)) == len(demo)):
        raise ConfigError(f"{REGISTRY_RESOURCE}: demo_only must list distinct ids of stand_ins")
    rows = data["model_rows"]
    if not (isinstance(rows, dict) and all(
            isinstance(a, str) and re.fullmatch(r"B\d+", a) and a not in data["stand_ins"]
            and isinstance(t, str) and t.strip() for a, t in rows.items())):
        raise ConfigError(f"{REGISTRY_RESOURCE}: model_rows must map B-row ids that are not "
                          f"stand-ins to a non-empty description")
    return tuple(out), tuple(demo), tuple(rows.items())


def assumption_registry() -> dict[str, tuple[int, ...]]:
    """model_assumptions row id -> the docs/06 items it may stand in for (package data
    reflection_holo/io/assumption_registry.yaml). Source map: no row; evidence label: not
    applicable (configuration policy, A2b N1)."""
    return dict(_registry_cached()[0])


def demo_only_stand_ins() -> frozenset[str]:
    """The registered stand-ins that only demonstration runs may use (registry key demo_only):
    a pipeline run with purpose "comparison" refuses each of them, whatever the docs/06 item
    (audit A3 M2)."""
    return frozenset(_registry_cached()[1])


def model_assumption_rows() -> dict[str, str]:
    """model_assumptions B-rows that the code cites as MODEL assumptions or sourced models, not as
    stand-ins for a docs/06 item (registry key model_rows; report E2): row id -> description."""
    return dict(_registry_cached()[2])


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v) -> bool:
    """A finite real number (bools excluded; inf and nan refused, A2b N8)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _check_kind(cid: str, name: str, kind: str, v) -> None:
    def bad(what):
        raise ConfigError(f"{cid}: parameter {name} must be {what}, got {v!r}")
    if kind == "str":
        if not isinstance(v, str) or not v.strip():
            bad("a non-empty string")
    elif kind == "material":
        if v not in MATERIALS:
            bad(f"a canonical element symbol, one of {MATERIALS} (exact spelling)")
        if v != SCHEMAS[cid]["material"]:
            bad(f"{SCHEMAS[cid]['material']!r} for {cid}")
    elif kind == "int3":
        if not (isinstance(v, list) and len(v) == 3 and all(_is_int(x) for x in v)) \
                or not any(v):
            bad("a non-zero list of three integers")
    elif kind == "int3_list":
        if not (isinstance(v, list) and v and all(isinstance(t, list) and len(t) == 3
                                                  and all(_is_int(x) for x in t) for t in v)):
            bad("a non-empty list of integer triples")
    elif kind == "str_list":
        if not (isinstance(v, list) and v and all(isinstance(s, str) and s for s in v)):
            bad("a non-empty list of strings")
    elif kind == "positive":
        if not (_is_num(v) and v > 0):
            bad("a finite positive number")
    elif kind == "nonnegative":
        if not (_is_num(v) and v >= 0):
            bad("a finite number >= 0")
    elif kind == "mapping":
        if not (isinstance(v, dict) and v):
            bad("a non-empty mapping")
    elif kind == "pixel_size":
        if not (isinstance(v, dict) and set(v) == {"along_beam", "perpendicular"}
                and all(_is_num(x) and x > 0 for x in v.values())):
            bad("a mapping {along_beam: >0, perpendicular: >0} of finite numbers (both axes stated)")
    elif kind == "reference_trajectory":
        if v not in REFERENCE_TRAJECTORIES:
            bad(f"one of {REFERENCE_TRAJECTORIES}")
    elif kind == "reference_model":
        if v not in REFERENCE_MODELS:
            bad(f"one of {REFERENCE_MODELS}")
    elif kind == "step_types":
        if not (isinstance(v, list) and v and all(x in STEP_TYPES for x in v)):
            bad(f"a non-empty list drawn from {STEP_TYPES}")
    elif kind == "edge_orientations":
        if not (isinstance(v, list) and v and all(x in STEP_EDGE_ORIENTATIONS for x in v)):
            bad(f"a non-empty list drawn from {STEP_EDGE_ORIENTATIONS}")
    else:  # pragma: no cover - registry error
        raise ConfigError(f"registry error: unknown kind {kind!r}")


def _check_unit(cid: str, name: str, dimension: str, unit) -> tuple[str, float | None]:
    if not isinstance(unit, str) or unit not in UNITS:
        raise ConfigError(f"{cid}: parameter {name}: unknown unit {unit!r} (unit table: "
                          f"{sorted(UNITS)})")
    dim, factor = UNITS[unit]
    if dim != dimension:
        if dimension == "none":
            raise ConfigError(f"{cid}: parameter {name} is not a physical quantity; its unit must "
                              f"be 'none', got {unit!r}")
        ok = sorted(u for u, (d, _) in UNITS.items() if d == dimension)
        raise ConfigError(f"{cid}: parameter {name} needs a unit of {dimension} ({ok}); {unit!r} "
                          f"is {'not a physical unit' if dim == 'none' else 'a unit of ' + dim}")
    return CANONICAL_UNITS[dimension], factor


def _convert(kind: str, value, factor):
    if value is None or factor is None:
        return copy.deepcopy(value)
    if kind == "pixel_size":
        return {k: float(v) * factor for k, v in value.items()}
    return float(value) * factor


def _parse_parameter(cid: str, name: str, spec, allow_test_only: bool) -> Parameter:
    if name not in PARAMETERS:
        raise ConfigError(f"{cid}: unknown parameter {name!r}")
    schema = SCHEMAS[cid]
    if name in schema["required"]:
        schema_item = schema["required"][name]
    elif name in schema["optional"]:
        schema_item = schema["optional"][name]
    else:
        raise ConfigError(f"{cid}: parameter {name} is not part of the {cid} schema")
    if not isinstance(spec, dict):
        raise ConfigError(f"{cid}: parameter {name} must be a mapping {{value, label, source, unit}}")
    missing = [k for k in PARAM_KEYS_REQUIRED if k not in spec]
    if missing:
        raise ConfigError(f"{cid}: parameter {name} lacks {missing} (every parameter states its "
                          f"unit, 'none' if it is not a physical quantity)")
    extra = sorted(set(spec) - set(PARAM_KEYS_REQUIRED) - set(PARAM_KEYS_OPTIONAL))
    if extra:
        raise ConfigError(f"{cid}: parameter {name} has unknown keys {extra}")
    label = spec["label"]
    if label == TEST_ONLY_LABEL and not allow_test_only:
        raise ConfigError(f"{cid}: parameter {name} is labelled TEST_ONLY; TEST_ONLY values "
                          f"are accepted only from in-memory test fixtures")
    accepted = EVIDENCE_LABELS + ((TEST_ONLY_LABEL,) if allow_test_only else ())
    require_evidence_label(label, f"{cid}: parameter {name}", accepted=accepted, qualified=False,
                           error=ConfigError)
    source = spec["source"]
    if not isinstance(source, str) or not source.strip():
        raise ConfigError(f"{cid}: parameter {name} must state a non-empty source")
    kind, dimension = PARAMETERS[name]
    unit = spec["unit"]
    canonical_unit, factor = _check_unit(cid, name, dimension, unit)

    item = spec.get("item")
    if item is not None and (not _is_int(item) or not 1 <= item <= N_PROJECT_INPUT_ITEMS):
        raise ConfigError(f"{cid}: parameter {name}: item must be a docs/06 item number "
                          f"1..{N_PROJECT_INPUT_ITEMS}, got {item!r}")
    if schema_item is None:
        if label == "PROJECT_INPUT":
            raise ConfigError(f"{cid}: parameter {name} is labelled PROJECT_INPUT but has no docs/06 "
                              f"item in the {cid} schema: a PROJECT_INPUT must name its docs/06 "
                              f"item (audit A2 m4)")
        if item is not None:
            raise ConfigError(f"{cid}: parameter {name} has no docs/06 item in the {cid} schema; "
                              f"'item: {item}' is not allowed")
    else:
        if item is None:
            raise ConfigError(f"{cid}: parameter {name} must name its docs/06 item {schema_item} "
                              f"('item: {schema_item}'), whatever its label (audit A2 M2)")
        if item != schema_item:
            raise ConfigError(f"{cid}: parameter {name} belongs to docs/06 item {schema_item}, "
                              f"not {item}")

    sfi = spec.get("stands_in_for_item")
    aid = spec.get("assumption_id")
    value = spec["value"]
    supply = check_supply(f"{cid}: parameter {name}", label, value, spec)
    if schema_item is not None:
        if label == "PROJECT_INPUT":
            pass                                  # supply record checked above (A2c G2)
        elif label == "ASSUMPTION":
            if sfi is None:
                raise ConfigError(
                    f"{cid}: ASSUMPTION {name} stands in for PROJECT_INPUT item {schema_item}: it "
                    f"must carry 'stands_in_for_item: {schema_item}' and an 'assumption_id' that the "
                    f"registry {REGISTRY_RESOURCE} maps to item {schema_item}")
            if sfi != schema_item:
                raise ConfigError(f"{cid}: parameter {name}: stands_in_for_item {sfi!r} must equal "
                                  f"its docs/06 item {schema_item}")
            if aid is None:
                raise ConfigError(f"{cid}: ASSUMPTION {name} stands in for PROJECT_INPUT item "
                                  f"{schema_item}: it must name its assumption_id (registered in "
                                  f"{REGISTRY_RESOURCE})")
            if not isinstance(aid, str) or schema_item not in assumption_registry().get(aid, ()):
                raise ConfigError(
                    f"{cid}: parameter {name}: assumption_id {aid!r} is not mapped to PROJECT_INPUT "
                    f"item {schema_item} by the registry {REGISTRY_RESOURCE} (A2b N1)")
        elif label != TEST_ONLY_LABEL:
            raise ConfigError(
                f"{cid}: parameter {name} is PROJECT_INPUT item {schema_item}: label {label} is not "
                f"accepted. Use PROJECT_INPUT (null, or a value whose source names the supplier and "
                f"the date), an ASSUMPTION registered for item {schema_item}, or TEST_ONLY in "
                f"in-memory fixtures (A2b N1)")
    else:
        if sfi is not None:
            raise ConfigError(f"{cid}: parameter {name}: stands_in_for_item is only for an "
                              f"ASSUMPTION standing in for a docs/06 item")
        if aid is not None:
            raise ConfigError(f"{cid}: parameter {name} has no docs/06 item in the {cid} schema: "
                              f"assumption_id is only for an ASSUMPTION standing in for a docs/06 "
                              f"item (cite the model_assumptions row in the source)")

    if value is None:
        if label not in ("PROJECT_INPUT", "UNVERIFIED"):
            raise ConfigError(f"{cid}: parameter {name} is null with label {label}; only a "
                              f"PROJECT_INPUT or an UNVERIFIED field may be null")
    else:
        _check_kind(cid, name, kind, value)
        pinned = PINNED.get(cid, {})
        if name in pinned and value != pinned[name]:
            raise ConfigError(
                f"{cid}: parameter {name} is {value!r}, but {cid} is defined by {name} = "
                f"{pinned[name]!r} (docs/05 section 2): a configuration with another geometry is "
                f"not {cid} and cannot use its gate (A2c G1)")
    note = spec.get("note")
    if note is not None and not isinstance(note, str):
        raise ConfigError(f"{cid}: parameter {name}: note must be a string")
    return Parameter(name=name, value=value, label=label, source=source, unit=unit, item=item,
                     note=note, stands_in_for_item=sfi, assumption_id=aid,
                     canonical_value=_convert(kind, value, factor), canonical_unit=canonical_unit,
                     supply=supply)


def _cross_checks(cid: str, params: dict[str, Parameter]) -> None:
    def val(n):
        return params[n].canonical_value if n in params else None

    energy = val("beam_energy_keV")
    if energy is not None and float(energy) != BEAM_ENERGY_SUPPLIED_KEV:
        raise ConfigError(f"{cid}: beam energy {energy} keV refused; the beam energy is "
                          f"{BEAM_ENERGY_SUPPLIED_KEV:g} keV for every configuration "
                          f"(PROJECT_INPUT item 1, Ali, 2026-09-22; 300 keV is never used)")
    if cid in ("CFG-A", "CFG-B") and energy is None:
        raise ConfigError(f"{cid} must state the beam energy, {BEAM_ENERGY_SUPPLIED_KEV:g} keV "
                          f"(PROJECT_INPUT item 1)")

    normal = val("surface_normal_hkl")
    azimuth = val("beam_azimuth_uvw")
    if normal is not None and azimuth is not None:
        try:
            surface_frame(tuple(normal), tuple(azimuth))
        except ValueError as exc:
            raise ConfigError(f"{cid}: {exc}") from exc

    if SCHEMAS[cid]["material"] != "Si":
        return                                   # no Si structure factor or V0 may be reused
    for hkl in val("forbidden_rod_reflections_hkl") or []:
        if diamond_allowed(hkl):
            raise ConfigError(f"{cid}: {tuple(hkl)} is listed as forbidden but F != 0")
    targets = [n for n in ("target_reflection_hkl", "second_reflection_hkl") if val(n)]
    targets_list = [(f"recommended_reflections_hkl[{i}]", t)
                    for i, t in enumerate(val("recommended_reflections_hkl") or [])]
    to_check = [(n, val(n)) for n in targets] + targets_list
    if to_check and normal is None:
        raise ConfigError(f"{cid}: target reflections need surface_normal_hkl")
    a = val("lattice_parameter")                 # canonical: A
    V0 = val("mean_inner_potential_V")
    for name, hkl in to_check:
        if a is None or V0 is None or energy is None:
            # the rod and the selection rule can still be checked
            if rod_decomposition(hkl)[0] != rod_decomposition(normal)[0]:
                raise ConfigError(f"{cid}: {name} {tuple(hkl)} is not on the specular rod")
            if not diamond_allowed(hkl):
                raise ConfigError(f"{cid}: {name} {tuple(hkl)} is a forbidden reflection")
            continue
        try:
            specular_condition_for(tuple(hkl), tuple(normal), E_keV=float(energy),
                                   V0_V=float(V0), a_A=float(a))
        except GeometryError as exc:
            raise ConfigError(f"{cid}: {name}: {exc}") from exc


def load_config_dict(data: dict, *, level: str, allow_test_only: bool = False,
                     source_path: str | None = None, sha256_file: str | None = None
                     ) -> LoadedConfig:
    """Validate an in-memory configuration mapping and return a LoadedConfig.

    level ("run" or "placeholder") is required. allow_test_only=True is for in-memory test
    fixtures only; load_config_file never sets it.
    Source map: no row (software requirement, docs/05 sections 0 and 3); evidence label: not
    applicable (no physical claim).
    """
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
    if not isinstance(data, dict):
        raise ConfigError("configuration must be a mapping")
    missing = [k for k in TOP_KEYS if k not in data]
    if missing:
        raise ConfigError(f"configuration lacks top-level keys {missing}")
    extra = sorted(set(data) - set(TOP_KEYS))
    if extra:
        raise ConfigError(f"configuration has unknown top-level keys {extra}")
    if data["schema_version"] != 1:
        raise ConfigError(f"unsupported schema_version {data['schema_version']!r}")
    cid = data["config_id"]
    if cid not in CONFIG_IDS:
        raise ConfigError(f"unknown config_id {cid!r}; expected one of {sorted(CONFIG_IDS)}")
    if data["name"] != CONFIG_IDS[cid]:
        raise ConfigError(f"{cid}: name must be {CONFIG_IDS[cid]!r}, got {data['name']!r}")
    status = data["status"]
    if status not in STATUSES:
        raise ConfigError(f"{cid}: status must be one of {STATUSES}, got {status!r}")
    if not isinstance(data["description"], str) or not data["description"].strip():
        raise ConfigError(f"{cid}: description must be a non-empty string")
    if not isinstance(data["parameters"], dict) or not data["parameters"]:
        raise ConfigError(f"{cid}: parameters must be a non-empty mapping")

    params = {n: _parse_parameter(cid, n, s, allow_test_only)
              for n, s in data["parameters"].items()}
    _cross_checks(cid, params)

    required = SCHEMAS[cid]["required"]
    missing_required = [(n, required[n]) for n in required if n not in params]
    absent_pi = [(n, i) for n, i in missing_required if i is not None]
    null_pi = [(p.name, p.item) for p in params.values()
               if p.value is None and p.label == "PROJECT_INPUT"]
    missing_pi = sorted(null_pi + absent_pi, key=lambda t: (t[1], t[0]))
    unverified = sorted(p.name for p in params.values() if p.label == "UNVERIFIED")
    test_only = any(p.label == TEST_ONLY_LABEL for p in params.values())

    if level == "run":
        if status == "placeholder":
            raise PlaceholderConfigError(
                f"{cid} is a placeholder configuration and cannot be loaded at run level "
                f"(unverified fields: {', '.join(unverified) or 'none'})")
        if missing_pi:
            absent = {n for n, _ in absent_pi}
            items = [i for _, i in missing_pi]
            listing = "; ".join(f"item {i} ({n}{', absent' if n in absent else ''})"
                                for n, i in missing_pi)
            raise MissingProjectInputError(
                f"{cid}: run-level load refused, missing PROJECT_INPUT "
                f"(docs/06_project_inputs_required.md): {listing}",
                items, [n for n, _ in missing_pi])
        if unverified:
            raise UnverifiedParameterError(
                f"{cid}: run-level load refused, UNVERIFIED fields: {', '.join(unverified)}",
                unverified)
        absent_other = [n for n, i in missing_required if i is None]
        if absent_other:
            raise MissingRequiredParameterError(
                f"{cid}: run-level load refused, required parameters absent: "
                f"{', '.join(absent_other)} (schema {cid})", absent_other)

    return LoadedConfig(config_id=cid, name=data["name"], status=status,
                        description=data["description"], schema_version=1, level=level,
                        parameters=params, missing_project_inputs=missing_pi,
                        unverified=unverified, test_only=test_only,
                        sha256_canonical=canonical_sha256(data), source_path=source_path,
                        sha256_file=sha256_file, missing_required=missing_required,
                        raw=copy.deepcopy(data))


class _UniqueKeyLoader(yaml.SafeLoader):
    """yaml.SafeLoader that refuses duplicate mapping keys (PyYAML keeps the last one silently)."""


def _construct_unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    seen = {}
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise ConfigError(f"duplicate key {key!r} at line {key_node.start_mark.line + 1} "
                              f"(first at line {seen[key]}): a duplicate key would silently "
                              f"override the earlier value (audit A2 M2)")
        seen[key] = key_node.start_mark.line + 1
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                                 _construct_unique_mapping)


def load_yaml_unique(text: str | bytes):
    """Parse YAML refusing duplicate keys anywhere (ConfigError)."""
    return yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506 - SafeLoader subclass


_FILE_RE = re.compile(r"^cfg_([a-z])_([a-z0-9_]+)\.yaml$")


def load_config_file(path, *, level: str) -> LoadedConfig:
    """Load a configuration YAML file (TEST_ONLY labels and duplicate keys refused). The file name
    must be cfg_<letter>_<name>.yaml and agree with config_id and name. level is required.
    Source map: no row (software requirement, docs/05 sections 0 and 3); evidence label: not
    applicable (no physical claim)."""
    p = Path(path)
    m = _FILE_RE.match(p.name)
    if not m:
        raise ConfigError(f"configuration file name {p.name!r} must match cfg_<x>_<name>.yaml")
    blob = p.read_bytes()
    data = load_yaml_unique(blob)
    if not isinstance(data, dict):
        raise ConfigError(f"{p}: not a YAML mapping")
    expected_id = f"CFG-{m.group(1).upper()}"
    if data.get("config_id") != expected_id or data.get("name") != m.group(2):
        raise ConfigError(f"{p.name}: config_id/name {data.get('config_id')!r}/"
                          f"{data.get('name')!r} do not match the file name")
    return load_config_dict(data, level=level, allow_test_only=False, source_path=str(p),
                            sha256_file=hashlib.sha256(blob).hexdigest())
