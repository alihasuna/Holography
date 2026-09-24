#!/usr/bin/env python3
"""X7: revert each fix of report X7 (re-audit A12) in a SCRATCH copy of the repository parts (never
the repository itself) and run the tests that should catch it; every reversion must make at least
one test fail. Each copy is a throw-away git repository (the pipeline run tests write a manifest,
which needs a clean git state) and is deleted after its run; the imported package is printed to
show that it is the copy's. Adapted from tools/review/x6/mutate_x6.py.

Usage:  PYTHONPATH=. venv/bin/python tools/review/x7/mutate_x7.py --work DIR [--check] [NAME ...]
        DIR: a scratch directory for the copies (required, no default; it must not lie inside the
        repository). --check: only verify that every replacement applies once (no test run).
Saved:  tools/review/x7/mutate_x7_output.txt (the full run, all mutations, in order)
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
TESTS = ["tests/pipeline/test_oxide_pipeline_a12_fixes.py",
         "tests/structure/test_oxide_structure_a12_fixes.py",
         "tests/pipeline/test_oxide_pipeline_a10b_fixes.py",
         "tests/structure/test_oxide_structure_a10b_fixes.py",
         "tests/forward/test_oxide_multislice_a10b_fixes.py",
         "tests/pipeline/test_oxide_pipeline_a9b_fixes.py",
         "tests/structure/test_oxide_structure_a9b_fixes.py",
         "tests/pipeline/test_oxide_pipeline_a8_fixes.py",
         "tests/structure/test_oxide_structure.py"]

M: dict[str, list[tuple[str, str, str]]] = {
    "W0_control": [(OX, 'MODEL_NAME = "continuum_oxide"', 'MODEL_NAME = "continuum_oxide"')],
    # ---- A12 M1: the allowlist -------------------------------------------------------------------
    "W1_M1_allowlist_off": [
        (CF, "    if mid not in MEASUREMENT_METHODS:\n        raise PipelineConfigError(",
         "    if False:\n        raise PipelineConfigError("),
        (CF, "    if parameter not in MEASUREMENT_METHODS[mid][0]:",
         "    if mid in MEASUREMENT_METHODS and parameter not in MEASUREMENT_METHODS[mid][0]:")],
    "W2_M1_per_parameter_check_off": [(CF, "    if parameter not in MEASUREMENT_METHODS[mid][0]:",
                                       "    if False:")],
    "W3_M1_ellipsometry_accepted_for_widths": [(
        CF, "    if parameter in (\"vacuum_edge\", \"interface\") and any(", "    if False and any(")],
    "W4_M1_other_measurement_word_minimum_off": [(CF, "        if n < MEASUREMENT_OTHER_MIN_WORDS:",
                                                  "        if False:")],
    "W5_M1_details_form_off": [(CF, "    if details:                                        # stated",
                                "    if False:                                          # stated")],
    # ---- A12 M1: the second layer ----------------------------------------------------------------
    "W6_M1_word_patterns_off": [(CF, "    for text, pats in ((_measurement_words(t), _MEASUREMENT_REFUSED),",
                                 "    for text, pats in ((_measurement_words(t), ()),")],
    "W7_M1_negations_back_to_x6": [(
        CF, "    r\"\\bnot\\b\", r\"\\bnot ?(?:measur|known|avail|stat|suppl|determin|record|done|appl)\",\n"
            "    r\"\\bnever\\b\", r\"\\bno\\b\", r\"\\bnone\\b\", r\"\\bnothing\\b\", r\"\\bwithout\\b\", "
            "r\"\\bcannot\\b\",\n",
        "    r\"\\bnot (?:yet |been )?measured\\b\", r\"\\bnever measured\\b\", r\"\\bnone\\b\",\n")],
    "W8_M1_origin_words_off": [(
        CF, "    r\"\\bestimat\", r\"\\bguess\", r\"\\bcalculat\", r\"\\bcomput(?:e|ed|es|ing|ation|ations)\\b\",",
        "    r\"\\bcalculat\",")],
    "W9_M1_row_id_without_separator": [(CF, "r\"(?<!rev )\\bb ?\\d{1,4}\\b\"", "r\"\\bb\\d{1,3}\\b\"")],
    "W10_M1_phys_rev_b_refused": [(CF, "r\"(?<!rev )\\bb ?\\d{1,4}\\b\"", "r\"\\bb ?\\d{1,4}\\b\"")],
    "W11_M1_ascii_rule_off": [(CF, "    if bad:\n        names = ", "    if False:\n        names = ")],
    "W12_M1_nfkc_off": [(CF, "    t = unicodedata.normalize(\"NFKC\", v)", "    t = v")],
    "W13_M1_whitespace_not_collapsed": [(
        CF, "    t = \" \".join(t.split())\n    _measurement_form(what, field_, t)",
        "    t = t.strip()\n    _measurement_form(what, field_, t)")],
    "W14_M1_method_error_without_statement": [(
        CF, "            f\"MEASUREMENT_METHODS that measures {parameter}: {allowed}; \"\n"
            "            f\"{_MEASUREMENT_CANNOT_VERIFY}\")",
        "            f\"MEASUREMENT_METHODS that measures {parameter}: {allowed}\")")],
    "W15_M1_record_rule_without_allowlist": [(
        CF, "                                  f\"{{{', '.join(MEASUREMENT_RECORD_KEYS)}}} whose method \"\n"
            "                                  f\"names an id of the allowlist for its parameter (\"\n"
            "                                  + \"; \".join(f\"{k}: {allowed_measurement_methods(k)}\"\n"
            "                                              for k in OXIDE_RECORDED_PARAMETERS)\n"
            "                                  + f\"; re-audit A12 M1); {_MEASUREMENT_CANNOT_VERIFY}\"),",
        "                                  f\"{{{', '.join(MEASUREMENT_RECORD_KEYS)}}}; \"\n"
        "                                  f\"{_MEASUREMENT_CANNOT_VERIFY}\"),")],
    # ---- A12 m1: reference form, repository references, dates, echoes ----------------------------
    "W16_m1_repository_paths_accepted": [
        (CF, "    r\"(?:^|[\\s(\\\"'=:,;]|\\./)(?:tools|docs|reflection_holo|tests|configs|scripts|outputs)/\",",
         "    r\"$^\","),
        (CF, "    r\"reflection_holo\", r\"model_assumptions\", r\"project_inputs_required\", r\"agent_reports\",",
         "    r\"$^\","),
        (CF, "    r\"holography/(?:tools|docs|tests|configs|scripts|outputs)\\b\", r\"_recompute_output\"))",
         "    r\"$^\"))")],
    "W17_m1_doi_form_off": [(
        CF, "    if (re.search(r\"\\bdoi\\b\", low) or \"doi.org\" in low) and not _REFERENCE_DOI.search(low):",
        "    if False:")],
    "W18_m1_url_form_off": [(CF, "    if \"://\" in low and not _REFERENCE_URL.search(low):",
                             "    if False:")],
    "W19_m1_token_beyond_prefix_off": [(CF, "    if len(rest) < MEASUREMENT_MIN_ALNUM:",
                                        "    if False:")],
    "W20_m1_date_floor_off": [(CF, "    if day < MEASUREMENT_DATE_FLOOR:", "    if False:")],
    "W21_m1_supply_date_bound_off": [(
        CF, "    if supplied_on is not None and day > _dt.date.fromisoformat(supplied_on):",
        "    if False:")],
    "W22_m1_supply_date_not_passed": [(
        CF, "date=_measurement_date(w, rec[\"date\"], supplied_on=supplied_on),",
        "date=_measurement_date(w, rec[\"date\"], supplied_on=None),")],
    "W23_m1_field_name_echoes_accepted": [(
        CF, "                             \"method\", \"instrument\", \"reference\", \"references\", \"record\",\n",
        "")],
    # ---- A12 m2: quadrature ---------------------------------------------------------------------
    "W24_m2_box_for_standard": [(
        OX, "        if uncertainty_kind == \"half_width\":           # worst case: the corners of the box",
        "        if True:                                       # worst case: the corners of the box")],
    "W25_m2_asi_symmetric_below": [(OX, "            lo = depth - math.sqrt(base + ha_lo ** 2)",
                                    "            lo = depth - math.sqrt(base + ha ** 2)")],
    "W26_m2_linear_sum_inside_the_root": [(
        OX, "            base = contrib[\"thickness\"] ** 2 + contrib[\"density\"] ** 2",
        "            base = (contrib[\"thickness\"] + contrib[\"density\"]) ** 2")],
    "W27_m2_coverage_statement_of_x6": [(
        OX, "    \"standard\": \"the nominal depth +- 2 combined standard uncertainties of the depth (the three \"\n"
            "                \"contributions combined in quadrature, first-order propagation; coverage factor \"\n"
            "                \"k = 2: about 95 % coverage for a normally distributed depth; the a-Si term \"\n"
            "                \"one-sided at its lower end, clipped at zero thickness)\",",
        "    \"standard\": \"+- 2 standard uncertainties (coverage factor k = 2: about 95 % coverage for a \"\n"
        "                \"normally distributed quantity)\",")],
    # ---- A12 n1: bounds --------------------------------------------------------------------------
    "W28_n1_depth_bound_off": [(OX, "            if not c < bound:                          # also inf",
                                "            if False:                                  # also inf")],
    "W29_n1_list_guard_off": [(OX, "    if n_hi - n_lo + 1 > _MAX_COUNTS_BUILT:", "    if False:")],
    "W30_n1_non_finite_guard_off": [(OX, "    if not (math.isfinite(lo) and math.isfinite(hi)):",
                                     "    if False:")],
    "W31_n1_structure_overflow_catch_off": [(
        OX, "    except (OverflowError, MemoryError) as exc:        # re-audit A12 n1",
        "    except ZeroDivisionError as exc:                   # re-audit A12 n1")],
    "W32_n1_pipeline_overflow_catch_off": [(
        CF, "    except (OverflowError, MemoryError) as exc:          # re-audit A12 n1",
        "    except ZeroDivisionError as exc:                     # re-audit A12 n1")],
    "W33_n1_value_bounds_without_statement": [(
        OX, "                             f\"thickness {t} A; {UNCERTAINTY_BOUND_STATEMENT}\")",
        "                             f\"thickness {t} A\")")],
    # ---- A12 m3: the nearest variant, the note, the comment --------------------------------------
    "W34_m3_record_without_nearest_variant": [(
        CF, "                nearest_count_variant=ox.nearest_count_variant(cv[\"interval\"]),\n", "")],
    "W35_m3_structure_without_nearest_variant": [(
        OX, "                nearest_count_variant=nearest_count_variant(ci),         # re-audit A12 m3\n",
        "")],
    "W36_m3_note_without_engine_statement": [(
        CF, "an effect not computed. Only the multislice \"\n"
            "                  \"engine distinguishes the variants: the geometric engine's layer phase uses \"\n"
            "                  \"the continuum boundaries, which do not depend on the count (re-audit A12 m3, \"\n"
            "                  \"report X7)\"))",
        "an effect not computed\"))")],
    "W37_m3_cell_comment_restored": [(
        CE, "    # crystal's equivalent boundary, which the layer overlaps or misses by at most a/8 for the\n"
            "    # nearest count and by up to 1.5 a/4 for a parity variant whose count is not the nearest one,\n"
            "    # so the continuum boundary can then lie below the kept top atomic plane; re-audit A12 m3)",
        "    # crystal's equivalent boundary, which the layer overlaps or misses by at most a/8)")],
    # ---- A12 n4, n2 ------------------------------------------------------------------------------
    "W38_n4_substring_qualifier_check": [(
        OX, "    if derived and (len(_PARITY_VARIANT_WORDS.findall(count_label)) != 1\n"
            "                    or _PARITY_VARIANT_QUALIFIER.findall(count_label) != [parity]):",
        "    if derived and parity_variant_qualifier(parity) not in count_label:")],
    "W39_n2_kind_forced_half_width": [(
        CF, "                parity=variant[\"parity\"], uncertainty_kind=over[\"uncertainty_kind\"],",
        "                parity=variant[\"parity\"], uncertainty_kind=\"half_width\",")],
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
    git = ["git", "-c", "user.name=x7", "-c", "user.email=x7@scratch.invalid"]
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
    for f in failed[:6]:
        print(f"    {f}", flush=True)
    if len(failed) > 6:
        print(f"    ... {len(failed) - 6} more", flush=True)
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
    print(f"X7 mutations: repository HEAD {head} plus the working tree; tests: {', '.join(TESTS)}",
          flush=True)
    for n in names:
        run(n, root, a.check)


if __name__ == "__main__":
    main()
