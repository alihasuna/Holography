#!/usr/bin/env python3
"""X7 (re-audit A12 M1, m1): what the measurement-record gate refuses and what it still accepts,
printed from the code (reflection_holo.pipeline.config) on in-memory copies of the shipped smoke
configuration (never written). V_real is labelled PROJECT_INPUT with a FABRICATED TEST supply and a
record whose one field is varied; the other model parameters are under B43; purpose demo (the
record rule is the same in a comparison run).

Printed: the allowlist and its constants; for each field the status of A12's D1 texts that remain
ACCEPTED (well-formed nonsense and ASCII digit-for-letter substitutions: the gate cannot verify a
record, only require one) and of genuine-looking texts that the refusal list refuses (it fails
closed, so such a record must be rephrased).

Run:  PYTHONPATH=. venv/bin/python tools/review/x7/x7_record_probe.py
Saved: tools/review/x7/x7_record_probe_output.txt
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from reflection_holo.pipeline import PipelineConfigError, load_pipeline_dict, read_pipeline_file  # noqa
from reflection_holo.pipeline import config as pc                                  # noqa: E402

SUPPLY = dict(label="PROJECT_INPUT", supplied_by="Agent X7", supplied_on="2026-09-24",
              source="TEST: fabricated supply (report X7)")
LABELS = dict(thickness="PROJECT_INPUT", density="PROJECT_INPUT", amorphous_si="PROJECT_INPUT",
              consumed_layers="DERIVED_HERE", V_real="PROJECT_INPUT", V_imag="ASSUMPTION B43",
              vacuum_edge="ASSUMPTION B43", interface="ASSUMPTION B43")
REC = dict(method="offaxis_holography_wedge: TEST: fabricated holography of a witness wedge",
           instrument="TEST: fabricated microscope", date="2026-09-20",
           reference="TEST: fabricated laboratory record 1")
BASE = read_pipeline_file(REPO / "configs" / "demo_smoke_si001.yaml")


def status(parameter: str, **field) -> str:
    d = copy.deepcopy(BASE)
    rec = d["variants"]["oxide_2p0nm"]["cfg_b_parameters"]["surface_preparation_details"]
    for k in ("stands_in_for_item", "assumption_id"):
        rec.pop(k, None)
    rec.update(SUPPLY)
    over = rec["value"]["overlayer"]
    labels = dict(LABELS)
    if parameter != "V_real":
        labels.update(V_real="ASSUMPTION B43", **{parameter: "PROJECT_INPUT"})
    over["labels"] = dict(over["labels"], **labels)
    over["measurements"] = {parameter: dict(REC, **field)}
    try:
        load_pipeline_dict(d, variant="oxide_2p0nm")
        return "ACCEPTED"
    except PipelineConfigError as exc:
        msg = str(exc)
        why = msg[msg.rfind("("):][:110] if "(" in msg else msg[-110:]
        return f"refused {why}"


print("== the allowlist (MEASUREMENT_METHODS: id -> parameters)")
for mid, (params, what) in pc.MEASUREMENT_METHODS.items():
    print(f"  {mid}: {list(params)} ({what})")
print(f"  MEASUREMENT_OTHER_MIN_WORDS = {pc.MEASUREMENT_OTHER_MIN_WORDS}; MEASUREMENT_MIN_ALNUM = "
      f"{pc.MEASUREMENT_MIN_ALNUM}; MEASUREMENT_DATE_FLOOR = {pc.MEASUREMENT_DATE_FLOOR}; not a "
      f"width method: {list(pc.MEASUREMENT_NOT_A_WIDTH_METHOD)}")

print("\n== residuals: A12 D1 texts that remain ACCEPTED (well-formed; the gate cannot verify)")
for field in ("instrument", "reference"):
    for text in ("abc", "test", "Doe", "#123", "n0t measured", "m0del value",
                 "   TEST: fabricated method A12   "):
        print(f"  {field} {text!r}: {status('V_real', **{field: text})}")
for text in ("offaxis_holography_wedge", "offaxis_holography_wedge: n0t measured",
             "offaxis_holography_wedge: abc"):
    print(f"  method {text!r}: {status('V_real', method=text)}")

print("\n== fail closed: genuine-looking texts that are refused (rephrase them)")
for parameter, field, text in (
        ("V_real", "instrument", "JEOL model JEM-2100F"),
        ("V_real", "instrument", "Titan, not aberration corrected"),
        ("V_real", "reference", "lab book No. 5, p. 12"),
        ("V_real", "method", "offaxis_holography_wedge: V0 derived from the phase slope"),
        ("V_real", "method", "rheed_rocking_curve_fit: estimated uncertainty 0.2 V"),
        ("vacuum_edge", "method", "xrr_fit: two-layer model fit"),
        ("V_real", "reference", "Kirkland group report 2026-17"),
        ("V_real", "reference", "Why the oxide is not uniform, Surf. Sci. 700 (2020) 1")):
    print(f"  {parameter} {field} {text!r}: {status(parameter, **{field: text})}")

print("\n== accepted genuine-looking texts")
for parameter, field, text in (
        ("vacuum_edge", "method", "afm_surface: non-contact mode, 5 um scan of the witness"),
        ("interface", "method", "cross_section_tem_profile: HAADF-STEM, erf fit of the profile"),
        ("V_imag", "method", "eels_inelastic_mean_free_path: log-ratio t/lambda on a wedge"),
        ("V_real", "method", "other_measurement: electron holography phase across a cleaved "
                             "witness corner of known angle"),
        ("V_real", "reference", "Phys. Rev. B 45, 1234 (1992)"),
        ("V_real", "reference", "doi:10.1016/j.ultramic.2020.113096"),
        ("V_real", "reference", "lab notebook LN-17 p. 34")):
    print(f"  {parameter} {field} {text!r}: {status(parameter, **{field: text})}")
