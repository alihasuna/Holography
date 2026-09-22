"""Assertion-based loader of the named configurations (CFG-A, CFG-B, CFG-O).

docs/05_final_repository_specification.md sections 0 (criterion 5), 2 and 3 (io/); source policy of
docs/06_project_inputs_required.md. Every parameter is a mapping with the keys
    value   the value (null allowed only for a PROJECT_INPUT or an UNVERIFIED field)
    label   one of the seven evidence labels
            METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE,
            UNVERIFIED
            (TEST_ONLY is accepted only for in-memory test fixtures, never from a file)
    source  where the value comes from (file, section, item, sentence)
and optionally unit, item (the docs/06 item number; REQUIRED when a PROJECT_INPUT value is null)
and note. Unknown keys and unknown parameter names are refused.

Two load levels, stated by the caller (no default):
  * level="run": any PROJECT_INPUT whose value is null FAILS (MissingProjectInputError naming the
    docs/06 item numbers); any UNVERIFIED field FAILS (UnverifiedParameterError); a configuration
    whose status is "placeholder" FAILS. No default ever replaces a missing input.
  * level="placeholder": the configuration is validated and returned with the missing and
    unverified fields listed; value() still refuses to return a null.

Energy rule: the beam energy is 200 keV for every configuration (PROJECT_INPUT item 1, Ali,
2026-09-22; reflection_holo.constants.BEAM_ENERGY_SUPPLIED_KEV). Any other stated energy fails at
every level; CFG-A and CFG-B must state it (null fails at every level). CFG-O's energy is UNVERIFIED
(null) until the body of P01 is read.
Crystallographic cross-checks for silicon configurations: the azimuth must lie in the surface plane
(reflection_holo.geometry.frames.surface_frame); a target reflection must be on the specular rod,
allowed (forbidden-reflection guard, SM02) and accessible (SM04, SM06); every reflection listed as
forbidden must indeed have F = 0.
"""
from __future__ import annotations

import copy
import hashlib
import json
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

EVIDENCE_LABELS = ("METADATA_VERIFIED", "SECTION_READ", "REPRODUCED", "PROJECT_INPUT",
                   "ASSUMPTION", "DERIVED_HERE", "UNVERIFIED")
TEST_ONLY_LABEL = "TEST_ONLY"
LEVELS = ("run", "placeholder")
STATUSES = ("benchmark", "experiment", "placeholder")
CONFIG_IDS = {"CFG-A": "si111_cleaved_110azimuth", "CFG-B": "si001_patterned",
              "CFG-O": "osakabe_1988_reproduction"}
N_PROJECT_INPUT_ITEMS = 22
PARAM_KEYS_REQUIRED = ("value", "label", "source")
PARAM_KEYS_OPTIONAL = ("unit", "item", "note")
TOP_KEYS = ("schema_version", "config_id", "name", "status", "description", "parameters")
REFERENCE_TRAJECTORIES = ("vacuum_beside_sample", "reflected_flat_area",
                          "transmitted_thin_region")        # docs/06 item 15
REFERENCE_MODELS = ("R1", "R2", "R3")                       # docs/05 section 5 item 3
STEP_EDGE_ORIENTATIONS = ("parallel_to_beam", "transverse_to_beam")

# name -> (kind, unit or None, docs/06 item expected when the label is PROJECT_INPUT, or None)
PARAMETERS: dict[str, tuple[str, str | None, int | None]] = {
    "surface_material": ("str", None, 11),
    "surface_normal_hkl": ("int3", None, 11),
    "beam_azimuth_uvw": ("int3", None, 8),
    "beam_energy_keV": ("positive", "keV", 1),
    "lattice_parameter_A": ("positive", "A", None),
    "mean_inner_potential_V": ("positive", "V", 20),
    "target_reflection_hkl": ("int3", None, 9),
    "second_reflection_hkl": ("int3", None, 9),
    "recommended_reflections_hkl": ("int3_list", None, 9),
    "not_recommended_reflections_hkl": ("int3_list", None, None),
    "forbidden_rod_reflections_hkl": ("int3_list", None, None),
    "step_types": ("str_list", None, 14),
    "step_translations": ("mapping", None, None),
    "step_edge_orientations": ("edge_orientations", None, None),
    "glancing_angle_ext_mrad": ("positive", "mrad", 7),
    "convergence_semi_angle_mrad": ("nonnegative", "mrad", 3),
    "objective_aperture_semi_angle_mrad": ("positive", "mrad", 4),
    "image_pixel_size_nm": ("pixel_size", "nm", 5),
    "reference_trajectory": ("reference_trajectory", None, 15),
    "reference_model": ("reference_model", None, None),
    "pattern_geometry": ("mapping", None, 13),
    "surface_preparation_method": ("str", None, 12),
    "surface_preparation_details": ("mapping", None, 12),
    "reflection_order": ("str", None, None),
    "height_sensitivity_nm": ("positive", "nm", None),
    "reconstruction_method": ("str", None, 19),
    "literature_source": ("str", None, None),
}


class ConfigError(ValueError):
    """Invalid configuration (schema, label, unit, value or crystallographic cross-check)."""


class MissingProjectInputError(ConfigError):
    """A PROJECT_INPUT is null at run level. .items holds the docs/06 item numbers."""

    def __init__(self, message: str, items: list[int], names: list[str]):
        super().__init__(message)
        self.items = items
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
    unit: str | None = None
    item: int | None = None
    note: str | None = None


@dataclass
class LoadedConfig:
    config_id: str
    name: str
    status: str
    description: str
    schema_version: int
    level: str
    parameters: dict[str, Parameter]
    missing_project_inputs: list[tuple[str, int]]
    unverified: list[str]
    test_only: bool
    sha256_canonical: str
    source_path: str | None = None
    sha256_file: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    def value(self, name: str):
        """Return a parameter value; refuses a null (naming the docs/06 item) or an unknown name.
        Source map: no row; evidence label: not applicable (no physical claim)."""
        if name not in self.parameters:
            raise ConfigError(f"{self.config_id}: parameter {name!r} is not defined")
        p = self.parameters[name]
        if p.value is None:
            if p.label == "PROJECT_INPUT":
                raise MissingProjectInputError(
                    f"{self.config_id}: {name} is a missing PROJECT_INPUT "
                    f"(docs/06_project_inputs_required.md item {p.item})", [p.item], [name])
            raise UnverifiedParameterError(f"{self.config_id}: {name} is UNVERIFIED (null)",
                                           [name])
        return copy.deepcopy(p.value)

    def label(self, name: str) -> str:
        return self.parameters[name].label


def canonical_sha256(data: dict) -> str:
    """SHA-256 of the canonical JSON form (sorted keys, no whitespace) of a configuration.
    Source map: no row (software requirement, docs/05 sections 0 and 3); evidence label: not
    applicable (no physical claim)."""
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_kind(cid: str, name: str, kind: str, v) -> None:
    def bad(what):
        raise ConfigError(f"{cid}: parameter {name} must be {what}, got {v!r}")
    if kind == "str":
        if not isinstance(v, str) or not v.strip():
            bad("a non-empty string")
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
            bad("a positive number")
    elif kind == "nonnegative":
        if not (_is_num(v) and v >= 0):
            bad("a number >= 0")
    elif kind == "mapping":
        if not (isinstance(v, dict) and v):
            bad("a non-empty mapping")
    elif kind == "pixel_size":
        if not (isinstance(v, dict) and set(v) == {"along_beam", "perpendicular"}
                and all(_is_num(x) and x > 0 for x in v.values())):
            bad("a mapping {along_beam: >0, perpendicular: >0} (both axes stated)")
    elif kind == "reference_trajectory":
        if v not in REFERENCE_TRAJECTORIES:
            bad(f"one of {REFERENCE_TRAJECTORIES}")
    elif kind == "reference_model":
        if v not in REFERENCE_MODELS:
            bad(f"one of {REFERENCE_MODELS}")
    elif kind == "edge_orientations":
        if not (isinstance(v, list) and v and all(x in STEP_EDGE_ORIENTATIONS for x in v)):
            bad(f"a non-empty list drawn from {STEP_EDGE_ORIENTATIONS}")
    else:  # pragma: no cover - registry error
        raise AssertionError(kind)


def _parse_parameter(cid: str, name: str, spec, allow_test_only: bool) -> Parameter:
    if name not in PARAMETERS:
        raise ConfigError(f"{cid}: unknown parameter {name!r}")
    if not isinstance(spec, dict):
        raise ConfigError(f"{cid}: parameter {name} must be a mapping {{value, label, source}}")
    missing = [k for k in PARAM_KEYS_REQUIRED if k not in spec]
    if missing:
        raise ConfigError(f"{cid}: parameter {name} lacks {missing}")
    extra = sorted(set(spec) - set(PARAM_KEYS_REQUIRED) - set(PARAM_KEYS_OPTIONAL))
    if extra:
        raise ConfigError(f"{cid}: parameter {name} has unknown keys {extra}")
    label = spec["label"]
    if label == TEST_ONLY_LABEL:
        if not allow_test_only:
            raise ConfigError(f"{cid}: parameter {name} is labelled TEST_ONLY; TEST_ONLY values "
                              f"are accepted only from in-memory test fixtures")
    elif label not in EVIDENCE_LABELS:
        raise ConfigError(f"{cid}: parameter {name} has label {label!r}, not one of "
                          f"{EVIDENCE_LABELS}")
    source = spec["source"]
    if not isinstance(source, str) or not source.strip():
        raise ConfigError(f"{cid}: parameter {name} must state a non-empty source")
    kind, unit_expected, item_expected = PARAMETERS[name]
    unit = spec.get("unit")
    if unit_expected is not None and unit != unit_expected:
        raise ConfigError(f"{cid}: parameter {name} must state unit {unit_expected!r}, "
                          f"got {unit!r}")
    if unit_expected is None and unit is not None:
        raise ConfigError(f"{cid}: parameter {name} is dimensionless; unit {unit!r} not allowed")
    item = spec.get("item")
    if item is not None:
        if not _is_int(item) or not 1 <= item <= N_PROJECT_INPUT_ITEMS:
            raise ConfigError(f"{cid}: parameter {name}: item must be a docs/06 item number "
                              f"1..{N_PROJECT_INPUT_ITEMS}, got {item!r}")
        if item_expected is not None and item != item_expected:
            raise ConfigError(f"{cid}: parameter {name} belongs to docs/06 item "
                              f"{item_expected}, not {item}")
    value = spec["value"]
    if value is None:
        if label not in ("PROJECT_INPUT", "UNVERIFIED"):
            raise ConfigError(f"{cid}: parameter {name} is null with label {label}; only a "
                              f"PROJECT_INPUT or an UNVERIFIED field may be null")
        if label == "PROJECT_INPUT" and item is None:
            raise ConfigError(f"{cid}: null PROJECT_INPUT {name} must name its docs/06 item")
    else:
        _check_kind(cid, name, kind, value)
    note = spec.get("note")
    if note is not None and not isinstance(note, str):
        raise ConfigError(f"{cid}: parameter {name}: note must be a string")
    return Parameter(name=name, value=value, label=label, source=source, unit=unit, item=item,
                     note=note)


def _cross_checks(cid: str, params: dict[str, Parameter]) -> None:
    def val(n):
        return params[n].value if n in params else None

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

    if val("surface_material") != "Si":
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
    a = val("lattice_parameter_A")
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

    missing_pi = sorted(((p.name, p.item) for p in params.values()
                         if p.value is None and p.label == "PROJECT_INPUT"), key=lambda t: t[1])
    unverified = sorted(p.name for p in params.values() if p.label == "UNVERIFIED")
    test_only = any(p.label == TEST_ONLY_LABEL for p in params.values())

    if level == "run":
        if status == "placeholder":
            raise PlaceholderConfigError(
                f"{cid} is a placeholder configuration and cannot be loaded at run level "
                f"(unverified fields: {', '.join(unverified) or 'none'})")
        if missing_pi:
            items = [i for _, i in missing_pi]
            listing = "; ".join(f"item {i} ({n})" for n, i in missing_pi)
            raise MissingProjectInputError(
                f"{cid}: run-level load refused, missing PROJECT_INPUT "
                f"(docs/06_project_inputs_required.md): {listing}",
                items, [n for n, _ in missing_pi])
        if unverified:
            raise UnverifiedParameterError(
                f"{cid}: run-level load refused, UNVERIFIED fields: {', '.join(unverified)}",
                unverified)

    return LoadedConfig(config_id=cid, name=data["name"], status=status,
                        description=data["description"], schema_version=1, level=level,
                        parameters=params, missing_project_inputs=missing_pi,
                        unverified=unverified, test_only=test_only,
                        sha256_canonical=canonical_sha256(data), source_path=source_path,
                        sha256_file=sha256_file, raw=copy.deepcopy(data))


_FILE_RE = re.compile(r"^cfg_([a-z])_([a-z0-9_]+)\.yaml$")


def load_config_file(path, *, level: str) -> LoadedConfig:
    """Load a configuration YAML file (TEST_ONLY labels refused). The file name must be
    cfg_<letter>_<name>.yaml and agree with config_id and name. level is required.
    Source map: no row (software requirement, docs/05 sections 0 and 3); evidence label: not
    applicable (no physical claim)."""
    p = Path(path)
    m = _FILE_RE.match(p.name)
    if not m:
        raise ConfigError(f"configuration file name {p.name!r} must match cfg_<x>_<name>.yaml")
    blob = p.read_bytes()
    data = yaml.safe_load(blob)
    if not isinstance(data, dict):
        raise ConfigError(f"{p}: not a YAML mapping")
    expected_id = f"CFG-{m.group(1).upper()}"
    if data.get("config_id") != expected_id or data.get("name") != m.group(2):
        raise ConfigError(f"{p.name}: config_id/name {data.get('config_id')!r}/"
                          f"{data.get('name')!r} do not match the file name")
    return load_config_dict(data, level=level, allow_test_only=False, source_path=str(p),
                            sha256_file=hashlib.sha256(blob).hexdigest())
