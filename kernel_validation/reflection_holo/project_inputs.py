"""reflection_holo.project_inputs -- the PROJECT_INPUT register.

Every laboratory quantity (repo:06_project_inputs_required.md) has an entry with
status 'SUPPLIED' (value given by the lab or stated by an HF-3300 card that applies) or 'MISSING'.
get(id) returns a SUPPLIED value; for a MISSING id it raises MissingProjectInput unless the caller
passes accept_assumptions=True, in which case the labelled placeholder (or the caller's default) is
returned, recorded in USED_ASSUMPTIONS and announced with 'ASSUMPTION used: <id> = <value>'.
No result can silently depend on a missing input.
"""
from __future__ import annotations


class MissingProjectInput(Exception):
    """Raised when a MISSING project input is requested without accept_assumptions=True."""


USED_ASSUMPTIONS: list = []


def _item(name, status, value, unit, source, repo_item, placeholder=None, placeholder_source=None):
    return {"name": name, "status": status, "value": value, "unit": unit, "source": source,
            "repo_item": repo_item, "placeholder": placeholder,
            "placeholder_source": placeholder_source}


_ITEMS = "06_project_inputs_required.md"

REGISTER: dict[str, dict] = {
    # ---- supplied -------------------------------------------------------------------------
    "E0": _item("beam kinetic energy", "SUPPLIED", 200e3, "eV",
                "PROJECT_INPUT, Ali, 2026-09-22 (repo:physics_conventions.md; 300 keV never used)",
                _ITEMS + " item 1"),
    "gun_type": _item("electron source", "SUPPLIED", "W(310) cold field-emission gun", "-",
                      "card:hf3300_lenses p.3; card:hf3300_column_overview p.1", "context"),
    "standard_holder_tilt_deg": _item(
        "specimen tilt range of the standard single-tilt holder (+/-)", "SUPPLIED", 15.0, "deg",
        "card:hf3300_lenses p.3 (alpha +/-15 deg); no reflection holder is described on any card",
        "context"),
    # ---- missing, with labelled placeholders ------------------------------------------------
    "energy_spread_eV": _item(
        "energy spread FWHM", "MISSING", None, "eV", "not supplied by the lab", _ITEMS + " item 2",
        0.45, "card:hf3300_column_overview p.1 (0.45 eV at 10 uA emission, voltage not stated); "
              "card:hf3300_structure p.5 ties it to 300 kV -> value at 200 kV UNVERIFIED"),
    "convergence_semiangle_rad": _item(
        "illumination convergence semi-angle at the specimen", "MISSING", None, "rad",
        "HF-3300 cards: TEM illumination 'nearly parallel', no number [hf3300_column_overview p.2]",
        _ITEMS + " item 3 (blocking)",
        1.0e-6, "card:shindo_tomita_ch04-06 p.31/pr.45 (alpha_i ~ 1e-6 rad in conventional "
                "diffraction, 200 kV thermal FEG: a different instrument)"),
    "objective_aperture": _item("objective-aperture semi-angle and selected beam", "MISSING", None,
                                "mrad", "not supplied", _ITEMS + " item 4 (blocking)"),
    "pixel_size_nm": _item("image pixel size at the detector", "MISSING", None, "nm/px",
                           "not supplied", _ITEMS + " item 5 (blocking)"),
    "dose_e_per_px": _item("dose per hologram", "MISSING", None, "e/px", "not supplied",
                           _ITEMS + " item 6", 100.0, "ASSUMPTION (order of magnitude; no card)"),
    "camera_mtf_at_carrier": _item(
        "camera MTF at the carrier frequency", "MISSING", None, "-",
        "MTF NOT IN any card; camera model differs between cards (Gatan OneView 4k "
        "[hf3300_structure p.3]; 2k/4k CCD or OneView [hf3300_column_overview p.8]; film "
        "[hf3300_lenses p.5])", _ITEMS + " item 6", 0.5, "ASSUMPTION"),
    "drift_rms_over_fringe": _item(
        "rms fringe drift during the exposure / fringe spacing", "MISSING", None, "-",
        "card:hf3300_lenses p.3 specifies stage drift <= 1 nm/min, but exposure time and fringe "
        "spacing at the specimen are unknown", _ITEMS + " item 6", 0.05, "ASSUMPTION"),
    "fringe_contrast": _item("fringe contrast on an empty/flat hologram", "MISSING", None, "-",
                             "no card gives a visibility", _ITEMS + " item 16", 0.3, "ASSUMPTION"),
    "n_px_per_terrace": _item("pixels averaged per terrace in the analysis", "MISSING", None, "px",
                              "analysis choice", _ITEMS + " item 19", 1000, "ASSUMPTION"),
    "theta_ext_rad": _item("external glancing angle", "MISSING", None, "rad", "not supplied",
                           _ITEMS + " item 7 (blocking)"),
    "azimuth": _item("beam azimuth", "MISSING", None, "[uvw]", "not supplied",
                     _ITEMS + " item 8 (blocking)"),
    "surface_orientation": _item("surface orientation, miscut", "MISSING", None, "(hkl)",
                                 "not supplied", _ITEMS + " item 11 (blocking)"),
    "overlayer_thickness_A": _item("oxide/amorphous overlayer thickness", "MISSING", None, "A",
                                   "not supplied", _ITEMS + " item 12 (blocking)"),
    "overlayer_potential_fraction": _item(
        "overlayer mean potential as a fraction of V0 (reduced-density layer)", "MISSING", None, "-",
        "no card gives an oxide or damage-layer potential", _ITEMS + " item 12",
        0.8, "ASSUMPTION: reduced-density layer V_layer = f V0 (task R0(c))"),
    "reference_trajectory": _item(
        "reference-beam trajectory at the specimen", "MISSING", None, "-", "not supplied",
        _ITEMS + " item 15 (blocking)", "vacuum",
        "ASSUMPTION; note Osakabe used a diffracted beam from a perfect area [osakabe1993 p.5]"),
    "V0_SI": _item("Si mean inner potential V0", "MISSING", None, "V",
                   "no card gives a Si value", _ITEMS + " item 20",
                   12.0, "repo:physics_conventions.md (ASSUMPTION)"),
    "absorptive_params_Si": _item("Si absorptive potential parameters", "MISSING", None, "-",
                                  "card:peng_ch13 p.20: not tabulated", _ITEMS + " item 21"),
    "specimen_temperature_K": _item("specimen temperature", "MISSING", None, "K", "not supplied",
                                    "context (Debye-Waller)", 300.0, "ASSUMPTION (room temperature)"),
}


def get(id: str, accept_assumptions: bool = False, default=None):
    """Return the value of project input `id`.

    SUPPLIED -> value. MISSING -> raise MissingProjectInput unless accept_assumptions, then return
    `default` (or the register placeholder if default is None), record it in USED_ASSUMPTIONS and
    print 'ASSUMPTION used: <id> = <value>'. A MISSING item without any placeholder always raises.
    """
    if id not in REGISTER:
        raise KeyError(f"unknown project input {id!r}")
    e = REGISTER[id]
    if e["status"] == "SUPPLIED":
        return e["value"]
    if not accept_assumptions:
        raise MissingProjectInput(
            f"'{id}' ({e['name']}; {e['repo_item']}) is MISSING. Supply it in "
            f"project_inputs.REGISTER, or call with accept_assumptions=True to use the labelled "
            f"placeholder {e['placeholder']!r}.")
    value = default if default is not None else e["placeholder"]
    if value is None:
        raise MissingProjectInput(f"'{id}' ({e['name']}; {e['repo_item']}) is MISSING and has no "
                                  f"placeholder; it must be supplied by the laboratory.")
    USED_ASSUMPTIONS.append((id, value, e["placeholder_source"] if default is None else "caller default"))
    print(f"ASSUMPTION used: {id} = {value}")
    return value


def missing() -> list[str]:
    """Ids of all MISSING items."""
    return [k for k, v in REGISTER.items() if v["status"] == "MISSING"]


def reset_assumptions() -> None:
    USED_ASSUMPTIONS.clear()
