#!/usr/bin/env python3
"""X6: revert each fix of report X6 (re-audit A10b) in a SCRATCH copy of the repository parts (never
the repository itself) and run the tests that should catch it; every reversion must make at least
one test fail. Each copy is a throw-away git repository (the pipeline run test writes a manifest,
which needs a clean git state) and is deleted after its run; the imported package is printed to
show that it is the copy's.

Usage:  PYTHONPATH=. venv/bin/python tools/review/x6/mutate_x6.py --work DIR [--check] [NAME ...]
        DIR: a scratch directory for the copies (required, no default; it must not lie inside the
        repository). --check: only verify that every replacement applies once (no test run).
Saved:  tools/review/x6/mutate_x6_output.txt (the full run, all mutations, in order)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PY = sys.executable
OX = "reflection_holo/structure/oxide.py"
CF = "reflection_holo/pipeline/config.py"
CE = "reflection_holo/forward/cell.py"
TESTS = ["tests/structure/test_oxide_structure_a10b_fixes.py",
         "tests/forward/test_oxide_multislice_a10b_fixes.py",
         "tests/pipeline/test_oxide_pipeline_a10b_fixes.py",
         "tests/structure/test_oxide_structure_a9b_fixes.py",
         "tests/forward/test_oxide_multislice_a9b_fixes.py",
         "tests/pipeline/test_oxide_pipeline_a9b_fixes.py",
         "tests/pipeline/test_oxide_pipeline_a8_fixes.py",
         "tests/structure/test_oxide_structure.py"]

M: dict[str, list[tuple[str, str, str]]] = {
    "Y0_control": [(OX, 'MODEL_NAME = "continuum_oxide"', 'MODEL_NAME = "continuum_oxide"')],
    # ---- A10b M1: parity variants ----------------------------------------------------------------
    "Y1_M1_key_not_required": [(
        CF, "    if OXIDE_PARITY_KEY not in over or parity not in ox.PARITY_VARIANTS:\n",
        "    if OXIDE_PARITY_KEY not in over:\n        return None\n"
        "    if parity not in ox.PARITY_VARIANTS:\n")],
    "Y2_M1_key_ignored_without_a_span": [(
        CF, "    if not ci[\"spans_boundary\"]:\n        if OXIDE_PARITY_KEY in over:\n",
        "    if not ci[\"spans_boundary\"]:\n        if False:\n")],
    "Y3_M1_any_value_is_upper": [
        (CF, "    if OXIDE_PARITY_KEY not in over or parity not in ox.PARITY_VARIANTS:\n",
         "    if OXIDE_PARITY_KEY not in over:\n"),
        (CF, "    idx = ox.PARITY_VARIANTS.index(parity)\n    other = ox.PARITY_VARIANTS[1 - idx]\n",
         "    idx = 0 if parity == \"lower\" else 1\n    other = ox.PARITY_VARIANTS[1 - idx]\n"
         "    parity = ox.PARITY_VARIANTS[idx]\n")],
    "Y4_M1_nearest_count_always": [(CF, "    if count_variant is None:\n        derived = ",
                                    "    if True:\n        derived = ")],
    "Y5_M1_label_without_qualifier": [(
        CF, "        how = (f\"{ox.parity_variant_qualifier(variant['parity'])}: the "
            "{variant['parity']} count \"",
        "        how = (f\"the {variant['parity']} count \"")],
    "Y6_M1_structure_qualifier_unchecked": [(
        OX, "    if derived and parity_variant_qualifier(parity) not in count_label:",
        "    if False:")],
    "Y7_M1_record_without_the_variant": [(
        CF, "    cv = _oxide_count_variant(cfg_b, over)\n    if cv is None:",
        "    cv = None\n    if cv is None:")],
    "Y8_M1_more_than_two_counts_accepted": [
        (CF, "    if len(ci[\"counts\"]) != 2:\n        raise PipelineConfigError(",
         "    if False:\n        raise PipelineConfigError("),
        (OX, "    if len(ci[\"counts\"]) != 2:\n        raise OxideSpecError(",
         "    if False:\n        raise OxideSpecError(")],
    "Y31_M1_more_than_two_counts_asks_for_the_key_first": [(
        CF, "    if len(ci[\"counts\"]) != 2:\n        raise PipelineConfigError(\n"
            "            f\"{where}: {span}: more than one",
        "    if len(ci[\"counts\"]) != 2 and parity in ox.PARITY_VARIANTS:\n"
        "        raise PipelineConfigError(\n            f\"{where}: {span}: more than one")],
    "Y9_M1_structure_count_unchecked": [(OX, "    if rec[\"consumed_layers\"] != want:",
                                         "    if False:")],
    "Y10_M1_structure_span_unchecked": [(
        OX, "    if not ci[\"spans_boundary\"]:\n        raise OxideSpecError(",
        "    if False:\n        raise OxideSpecError(")],
    "Y11_M1_retired_key_not_named": [(CF, "    if retired:\n        raise PipelineConfigError(",
                                      "    if False:\n        raise PipelineConfigError(")],
    "Y12_M1_hash_of_specs_without_variant_changed": [(      # None hashed like any value
        OX, "    if d[\"consumed_layers_parity_variant\"] is None:\n"
            "        del d[\"consumed_layers_parity_variant\"]\n    else:\n",
        "    if d[\"consumed_layers_parity_variant\"] is not None:\n")],
    "Y13_M1_overlap_bound_a8": [(OX, "interface_overlap_bound_A=((0.5 if variant is None else 1.5)",
                                 "interface_overlap_bound_A=((0.5 if True else 1.5)")],
    # ---- A10b M2: structured measurement records -------------------------------------------------
    "Y14_M2_free_text_accepted": [(
        CF, "        if not isinstance(rec, dict) or set(rec) != set(MEASUREMENT_RECORD_KEYS):\n",
        "        if isinstance(rec, str) and rec.strip():\n            out[k] = rec\n"
        "            continue\n"
        "        if not isinstance(rec, dict) or set(rec) != set(MEASUREMENT_RECORD_KEYS):\n")],
    "Y15_M2_patterns_off": [(CF, "    for pat in _MEASUREMENT_REFUSED:", "    for pat in ():")],
    "Y16_M2_placeholder_words_off": [(
        CF, "    if low in _MEASUREMENT_PLACEHOLDERS or words in NON_SUPPLIERS or low in {",
        "    if False and low in _MEASUREMENT_PLACEHOLDERS or False and words in NON_SUPPLIERS "
        "or False and low in {")],
    "Y17_M2_min_alnum_off": [(CF, "    if len(alnum) < MEASUREMENT_MIN_ALNUM:", "    if False:")],
    "Y18_M2_bare_value_accepted": [(CF, "    if _MEASUREMENT_BARE_VALUE.fullmatch(v):",
                                    "    if False:")],
    "Y19_M2_future_date_accepted": [(CF, "    if day > latest_today():\n        raise "
                                         "PipelineConfigError(f\"{where}.date",
                                     "    if False:\n        raise PipelineConfigError(f\"{where}.date")],
    "Y20_M2_date_format_free": [(
        CF, "    elif isinstance(v, str) and re.fullmatch(r\"\\d{4}-\\d{2}-\\d{2}\", v):\n"
            "        try:\n            day = _dt.date.fromisoformat(v)\n"
            "        except ValueError:\n            raise PipelineConfigError(f\"{where}.date",
        "    elif isinstance(v, str) and v:\n"
        "        try:\n            day = _dt.date.fromisoformat(v)\n"
        "        except ValueError:\n            raise PipelineConfigError(f\"{where}.date")],
    # ---- A10b m1: the a-Si potentials need a record ----------------------------------------------
    "Y21_m1_asi_potential_without_record": [(
        CF, "OXIDE_RECORDED_PARAMETERS = OXIDE_MODEL_PARAMETERS + (\"amorphous_si_potential\",)",
        "OXIDE_RECORDED_PARAMETERS = OXIDE_MODEL_PARAMETERS")],
    # ---- A10b m2: the uncertainty kind -----------------------------------------------------------
    "Y22_m2_standard_read_as_half_width": [(OX, "STANDARD_COVERAGE_FACTOR = 2.0",
                                            "STANDARD_COVERAGE_FACTOR = 1.0")],
    "Y23_m2_kind_defaulted": [(                              # an unstated kind read as half_width
        CF, "    got = [k for k in OXIDE_UNCERTAINTY_KEYS if k in over]\n",
        "    if any(k in over for k in OXIDE_UNCERTAINTY_KEYS[:3]):\n"
        "        over.setdefault(\"uncertainty_kind\", \"half_width\")\n"
        "    got = [k for k in OXIDE_UNCERTAINTY_KEYS if k in over]\n")],
    # ---- A10b m3: the a-Si thickness uncertainty in the interval ---------------------------------
    "Y24_m3_asi_uncertainty_ignored": [(
        OX, "    lo, hi, counts = _depth_counts(t - ht, t + ht, rho - hr, rho + hr, ta_lo, t_a + ha, a)",
        "    lo, hi, counts = _depth_counts(t - ht, t + ht, rho - hr, rho + hr, t_a, t_a, a)")],
    "Y30_m3_asi_stand_in_uncertainty_accepted": [(
        CF, "    stand = [k for k in (\"thickness\", \"density\", \"amorphous_si\")",
        "    stand = [k for k in (\"thickness\", \"density\")")],
    "Y25_m3_comparison_names_two_keys": [(CF, "{list(OXIDE_UNCERTAINTY_KEYS[:3])} of the witness",
                                          "{list(OXIDE_UNCERTAINTY_KEYS[:2])} of the witness")],
    # ---- A10b n2: zero uncertainties ------------------------------------------------------------
    "Y26_n2_zero_accepted": [(OX, "        u[name] = _num(v, f\"{name} (item 12; zero or negative "
                                  "refused, re-audit A10b n2)\",\n                       positive=True)",
                              "        u[name] = _num(v, f\"{name} (item 12; zero or negative "
                              "refused, re-audit A10b n2)\",\n                       nonneg=True)")],
    # ---- A10b n1: the non-conformal guard --------------------------------------------------------
    "Y27_n1_guard_on_thickness_only": [(CE, "    if len(thick) < 2 and len(counts) < 2:",
                                        "    if len(thick) < 2:")],
    "Y28_n1_ack_on_thickness_only": [(
        OX, "        if (tt is None or len({round(v, 12) for v in tt}) < 2) and (tn is None or "
            "len(set(tn)) < 2):",
        "        if tt is None or len({round(v, 12) for v in tt}) < 2:")],
    # ---- decision 6: "both parities" in a code string --------------------------------------------
    "Y29_d6_both_parities_text": [(
        CF, "is refused (lower and upper would not cover the counts between them).",
        "is refused (both parities must then be run).")],
}


def _apply(work: Path, name: str) -> None:
    for rel, old, new in M[name]:
        p = work / rel
        s = p.read_text()
        n = s.count(old)
        if n != 1:
            raise SystemExit(f"{name}: {rel}: the text to replace occurs {n} times (expected 1)")
        p.write_text(s.replace(old, new))


def run(name: str, root: Path, check: bool) -> None:
    work = root / name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    ign = shutil.ignore_patterns("__pycache__", "*.pyc")
    for d in ("reflection_holo", "tests", "configs", "tools"):
        shutil.copytree(REPO / d, work / d, ignore=ign)
    shutil.copy(REPO / "pyproject.toml", work / "pyproject.toml")
    _apply(work, name)
    if check:
        print(f"{name}: applies", flush=True)
        shutil.rmtree(work)
        return
    git = ["git", "-c", "user.name=x6", "-c", "user.email=x6@scratch.invalid"]
    subprocess.run(git + ["init", "-q"], cwd=work, check=True)
    subprocess.run(git + ["add", "-A"], cwd=work, check=True)
    subprocess.run(git + ["commit", "-qm", f"scratch {name}"], cwd=work, check=True)
    env = {"PYTHONPATH": str(work), "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "HOME": os.environ.get("HOME", "/root"), "OMP_NUM_THREADS": "2",
           "OPENBLAS_NUM_THREADS": "2", "MKL_NUM_THREADS": "2"}
    t0 = time.time()
    r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", *TESTS],
                       cwd=work, env=env, capture_output=True, text=True)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    failed = [ln.split(" - ")[0] for ln in lines if ln.startswith("FAILED")]
    probe = subprocess.run([PY, "-c", "import reflection_holo; print(reflection_holo.__file__)"],
                           cwd=work, env=env, capture_output=True, text=True).stdout.strip()
    ok = probe.startswith(str(work))
    print(f"{name}: package in the copy: {ok}; {lines[-1] if lines else r.stderr[-300:]} "
          f"[{time.time() - t0:.0f} s]", flush=True)
    for f in failed[:10]:
        print(f"    {f}", flush=True)
    if len(failed) > 10:
        print(f"    ... {len(failed) - 10} more", flush=True)
    shutil.rmtree(work)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    root = a.work.resolve()
    if root == REPO or REPO in root.parents:
        raise SystemExit("--work must lie outside the repository")
    names = a.names or list(M)
    unknown = [n for n in names if n not in M]
    if unknown:
        raise SystemExit(f"unknown mutations {unknown}")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                          text=True).stdout.strip()
    print(f"X6 mutations: repository HEAD {head} plus the working tree; tests: {', '.join(TESTS)}",
          flush=True)
    for n in names:
        run(n, root, a.check)


if __name__ == "__main__":
    main()
