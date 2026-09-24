#!/usr/bin/env python3
"""T5: does each fix of re-audit A10a have a test that FAILS when the fix is reverted, and do A10a's
surviving mutations A4, A5 and A6 (SP/a10a/mutate_a10a.out: "14 passed" each) now fail?

Each mutation is applied to a SCRATCH copy of the working tree (never the repository itself): the
directories reflection_holo, tests, tools, scripts, configs, docs and pyproject.toml are copied and
committed to a scratch git repository inside the copy, one string replacement is applied and asserted
to match exactly once, and the named test files are run there with PYTHONPATH pointing at the copy
(the imported package path and the imported analysis-script path are printed as proof). Mutation
"T0_control" changes nothing: its tests must pass.

A4 and A6 are A10a's literal replacements. A10a's literal A5 pattern no longer exists (T5 rewrote the
cap-5 reading line); "A5_cap5_reading_quotes_total" is the same fault in the new line: the phase the
reading quotes as vacuum-origin is taken from the TOTAL instead of the mask family.

Usage: PYTHONPATH=. venv/bin/python tools/review/t5/mutate_t5.py --work <scratch dir> [NAME ...]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PY = str(REPO / "venv/bin/python")
T_BT = "tests/forward/test_buried_torus_analysis.py"
T_ALL = [T_BT, "tests/structure/test_buried_assertion_f_layers.py",
         "tests/structure/test_features_buried.py", "tests/forward/test_feature_cell_buried.py"]
BT = "tools/plots/buried_torus.py"

MUTATIONS = {
    "T0_control": (BT, "APERTURE_PER_A = 0.2 ", "APERTURE_PER_A = 0.2 ", T_ALL),
    # ---- A10a's surviving mutations (A10a-m3) --------------------------------------------------
    "A4_analyse_vac_is_total": (
        BT, 'met_vac = metrics(pf + parts["vacuum_origin"], pf, g, reg)',
        'met_vac = metrics(pf + parts["total"], pf, g, reg)', [T_BT]),
    "A5_cap5_reading_quotes_total": (
        BT, "f\"aperture; region {family['region']}) is {_rng(family, 'max_abs_dphi_rad')} rad in \"",
        "f\"aperture; region {family['region']}) is {tot.get('max_abs_dphi_rad', nan):.3g}-"
        "{tot.get('max_abs_dphi_rad', nan):.3g} rad in \"", [T_BT]),
    "A6_V16_uses_two_beam_angle": (BT, '    t_16 = np.tan(g["row"]["angle_rad"])',
                                   '    t_16 = t_int', [T_BT]),
    # ---- A10a-M1: the mask family ------------------------------------------------------------------
    "M1a_family_reduced_to_the_main_mask": (
        BT, '    return (("sharp step at 0", 0.0, 0.0),',
        '    return ((f"sin^2 ramp 0-{VAC_RAMP_A:g} A (main mask)", 0.0, VAC_RAMP_A),)\n'
        '    return (("sharp step at 0", 0.0, 0.0),', [T_BT]),
    "M1b_family_admits_the_top_plane": (
        BT, "    if not (np.isfinite(start_A) and start_A >= 0.0):",
        "    if not np.isfinite(start_A):", [T_BT]),
    "M1c_every_member_evaluated_with_the_main_mask": (
        BT, "parts = split_with_mask(D, ew, family_mask(g[\"x_rel\"], start, ramp))",
        "parts = split_with_mask(D, ew, vacuum_mask(g[\"x_rel\"]))", [T_BT]),
    "M1d_raw_fraction_of_a_wrong_layer": (
        BT, "    return float(p2[vac & (x <= layer_A)].sum() / tot)",
        "    return float(p2[vac & (x <= 2 * layer_A)].sum() / tot)", [T_BT]),
    # ---- A10a-m2: the band-edge path and the wording ---------------------------------------------
    "M2a_band_edge_is_the_row_angle": (
        BT, '                     ("band_edge", float(g["row"]["band_edge_angle_rad"]))):',
        '                     ("band_edge", float(g["row"]["angle_rad"]))):', [T_BT]),
    "M2b_aperture_max_angle_is_theta_out": (
        BT, "    return float(np.arcsin(np.sin(th_out_rad) + wavelength_A * APERTURE_PER_A))",
        "    return float(th_out_rad)", [T_BT]),
    "M2c_band_edge_not_asserted_against_the_metadata": (
        BT, '    if not np.isclose(float(bl["fx_max_per_A"]), row["band_edge_fx_per_A"], rtol=1e-9, '
            'atol=0.0):', '    if False:', [T_BT]),
    "M2d_P_called_beyond_the_reach_on_the_specular_angle_only": (
        BT, "    if r2 < p_lo:\n", "    if r1 < p_lo:\n", [T_BT]),
    "M2e_old_attribution_wording": (
        BT, '"transmission function BY ANALOGY, UNVALIDATED in this cell; CONFIRMED in a "',
        '"transmission function (CONFIRMED there in a "', [T_BT]),
    # ---- A10a-m4: the compact figure -----------------------------------------------------------------
    "M4a_compact_per_panel_scale": (
        BT, '                   interpolation="nearest", vmin=info["vmin"], vmax=info["vmax"])',
        '                   interpolation="nearest", vmin=float(np.nanmin(d)), '
        'vmax=float(np.nanmax(d)))', [T_BT]),
    "M4b_compact_deep_cap_title_without_analogy": (
        BT, 'f"cap {cap:g} A: numerical artefact by analogy\\n(about "',
        'f"cap {cap:g} A: attributed to a numerical artefact (T4 M-1)\\n(about "', [T_BT]),
}


def copy_tree(dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    for d in ("reflection_holo", "tests", "tools", "scripts", "configs", "docs"):
        shutil.copytree(REPO / d, dest / d, ignore=ign)
    shutil.copy2(REPO / "pyproject.toml", dest / "pyproject.toml")
    for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "T5 mutation scratch copy"]):
        subprocess.run(["git", "-c", "user.name=t5", "-c", "user.email=t5@scratch.invalid", *cmd],
                       cwd=dest, check=True, capture_output=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("names", nargs="*")
    a = ap.parse_args(argv)
    names = a.names or list(MUTATIONS)
    rc_all = 0
    for name in names:
        path, old, new, tests = MUTATIONS[name]
        dest = a.work / name
        copy_tree(dest)
        target = dest / path
        src = target.read_text()
        n = src.count(old)
        if n != 1:
            print(f"{name}: pattern found {n} times in {path}: NOT APPLIED")
            rc_all = 1
            continue
        target.write_text(src.replace(old, new))
        env = dict(PYTHONPATH=str(dest), PATH="/usr/bin:/bin", HOME="/root",
                   OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                   NUMEXPR_NUM_THREADS="1", MPLBACKEND="Agg")
        who = subprocess.run([PY, "-c", "import reflection_holo; print(reflection_holo.__file__)"],
                             cwd=dest, env=env, capture_output=True, text=True).stdout.strip()
        r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests], cwd=dest,
                           env=env, capture_output=True, text=True)
        last = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1]
        failed = [ln for ln in r.stdout.splitlines() if ln.startswith("FAILED")]
        expect = "pass" if name == "T0_control" else "fail"
        ok = (r.returncode == 0) if expect == "pass" else (r.returncode != 0)
        rc_all |= 0 if ok else 1
        print(f"{name}: 1 replacement in {path}; package {who}; analysis script {target}; "
              f"tests {' '.join(tests)}")
        print(f"    result: {last}  -> expected to {expect}: {'OK' if ok else 'NOT AS EXPECTED'}")
        for ln in failed:
            print(f"    {ln}")
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
