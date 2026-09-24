#!/usr/bin/env python3
"""Figure manifest of the R1 smoke report: for each figure its file, SHA-256, pixel size and dpi, the
script and command that made it, the run directories and their commits (from the runs' manifests),
and a one-sentence caption with the evidence labels. Numbers in captions are read here from the runs'
summary.json files (nothing is typed).

Usage: PYTHONPATH=. venv/bin/python tools/report/figure_manifest.py --sp SP > tools/report/figure_manifest.txt
(called by tools/report/make_report_figures.sh after the figures are built).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]


def _s(runs: Path, name: str) -> dict:
    return json.loads((runs / name / "summary.json").read_text())


def _commit(man_path: Path) -> str:
    m = json.loads(man_path.read_text())
    r = m.get("repository", {})
    return f"{str(r.get('commit'))[:7]} (dirty {r.get('dirty')})"


def _run_commit(runs: Path, name: str) -> str:
    return f"{name}: {_commit(runs / name / 'manifest.json')}"


def _steps(s: dict) -> str:
    return "; ".join(f"{st['from_field_terrace']}->{st['to_field_terrace']} {st['height']['h_A']:+.4f} +- "
                     f"{st['height']['sigma_h_A']:.4f} A (built {st['built_height_A']:+.4f})"
                     for st in s["quantification"]["steps"] if st.get("height"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sp", required=True, type=Path)
    a = ap.parse_args(argv)
    sp = a.sp
    runs = sp / "report_smoke"
    fig = runs / "figures"
    rf = ("PYTHONPATH=. venv/bin/python tools/report/report_figures.py --runs SP/report_smoke --out "
          "SP/report_smoke/figures --t1-figures SP/torus/figures --t5-figures SP/buried_t5/figures")
    s1, s2, s3, s4 = (_s(runs, n) for n in ("S1_base", "S2_multislice_tiny", "S3_multislice_tiny_thermal",
                                            "S4_plasmon_losses"))
    ox = {n: _s(runs, n) for n in ("S5_oxide_2p0nm", "S5_oxide_1p5nm", "S5_oxide_2p0nm_no_absorption",
                                   "S5_oxide_1p5nm_no_absorption")}
    t6 = {n: _s(runs, n)["quantification"]["measurable"] for n in ("S6_torus_trench", "S6_torus_ridge")}
    c1 = s1["quantification"]["no_step_control"]
    a1 = s1["detector"]["empty_object_amplitude"]
    t1m = {k: next((sp / "torus" / f"ms_{k}" / "outputs" / "manifests").glob("*.json"))
           for k in ("trench", "ridge", "flat")}
    b_man = sorted((sp / "buried").glob("ms_*/outputs/manifests/*.json"))
    n_atoms_s2 = json.loads(Path(s2["engine"]["engine_manifest"]).read_text())["extra"]["run_configuration"][
        "cell"]["n_atoms"]
    mip = s2["engine"]["mip_check"]
    ap = s2["dark_field"]
    th3 = s3["engine"]["thermal_model"]
    lo4 = s4["surface_plasmon_losses"]
    o20, o15 = (ox[n]["structure"]["options"]["overlayer"] for n in ("S5_oxide_2p0nm", "S5_oxide_1p5nm"))
    f6 = _s(runs, "S6_torus_trench")["feature"]["shape"]
    t1s = {k: json.loads((sp / "torus" / f"ms_{k}" / f"summary_{k}.json").read_text())
           for k in ("trench", "ridge")}
    bcase = json.loads(next((sp / "buried").glob("ms_cap5A_*/case_*.json")).read_text())["CASE"]
    b_commits = sorted({_commit(p) for p in b_man})
    entries = [
        ("f0_pipeline_overview.png", "tools/report/report_figures.py (fig_overview)", rf, "none (schematic)", "-",
         "Flow of `python -m reflection_holo.pipeline run` (stages of reflection_holo/pipeline/run.py, module "
         "names in each box) with its refusal gates (exit codes of pipeline/__main__.py; thresholds of stand-in "
         "B29 in the demo configs); a schematic, no data."),
        ("s1_staircase_geometric.png", "tools/report/report_figures.py (fig_s1)", rf, "SP/report_smoke/S1_base",
         _run_commit(runs, "S1_base"),
         "S1, configs/demo_smoke_si001.yaml base, geometric engine (no dynamical amplitude), every unsupplied "
         "input an ASSUMPTION stand-in (B19-B31): object-hologram crop across the a/2 step, reconstructed "
         "wrapped phase, amplitude, quantification regions, wrapped phase along the beam and terrace heights "
         f"built vs recovered ({_steps(s1)}); no-step control {c1['delta_rad']:+.4f} rad vs tolerance "
         f"{c1['tolerance_rad']:.4f} rad; DEMO, not comparable to experiment."),
        ("s2_multislice_tiny_supercell_exitwave.png", "tools/report/report_figures.py (fig_s2)", rf,
         "SP/report_smoke/S2_multislice_tiny", _run_commit(runs, "S2_multislice_tiny"),
         f"S2, variant multislice_tiny: side view of the {n_atoms_s2:,}-atom supercell with the numerical "
         "absorbers and the sheet beam, and the complex exit wave (|psi|, arg psi, amplitude profiles of all "
         f"beams and of the specular beam selected by the {ap['semi_angle_rad'] * 1e3:g} mrad aperture, "
         f"{ap['label'].split(' (')[0]}); Kirkland IAM potential ({mip['configured_label']} MIP "
         f"{mip['configured_potential_mip_V']} V), no absorption (B30), static lattice, glancing angle "
         f"{s2['glancing_angle']['value_mrad']:.4f} mrad (B32); multislice engine UNVALIDATED for step "
         "heights; the run returns NO HEIGHT (terraces shorter than the 3-resolution margin)."),
        ("s2_detail/supercell.png", "tools/plots/smoke_figures.py (supercell_figure; reused, unchanged)",
         "PYTHONPATH=. venv/bin/python tools/plots/smoke_figures.py --config configs/demo_smoke_si001.yaml "
         "--variant multislice_tiny --run-dir SP/report_smoke/S2_multislice_tiny --geometric-run-dir "
         "SP/report_smoke/S1_base --out SP/report_smoke/figures/s2_detail",
         "configs/demo_smoke_si001.yaml variant multislice_tiny (rebuilt by the script)",
         "rebuilt from the configuration by the code at the HEAD above (figures are built just before this "
         "manifest by tools/report/make_report_figures.sh)",
         "S2 supplementary (15 in wide, for a full landscape page): the same supercell with zooms on the a/2 "
         "translation step and the a/4 screw/glide step and a top view of the back-bond rotation across the "
         "a/4 step; bulk-terminated (B26) DEMO structure."),
        ("s2_detail/exit_wave_complex.png", "tools/plots/smoke_figures.py (exitwave_figure; reused, unchanged)",
         "same command as s2_detail/supercell.png", "SP/report_smoke/S2_multislice_tiny and S1_base",
         f"{_run_commit(runs, 'S2_multislice_tiny')}; {_run_commit(runs, 'S1_base')}",
         "S2 supplementary, NOT recommended for the report: its lower-right panel is the S1 geometric-engine "
         "wave and labels as 'unwrapped' a numpy.unwrap of the row-mean phase, which cannot recover whole "
         "wraps across a sharp a/4 or a/2 step; the other three panels repeat s2_multislice_tiny_*.png."),
        ("s3_thermal_vs_static.png", "tools/report/report_figures.py (fig_s3)", rf,
         "SP/report_smoke/S2_multislice_tiny, S3_multislice_tiny_thermal",
         f"{_run_commit(runs, 'S2_multislice_tiny')}; {_run_commit(runs, 'S3_multislice_tiny_thermal')}",
         f"S3, variant multislice_tiny_thermal (frozen phonons, {th3['model']} at "
         f"{th3['specimen_temperature_K']} K {th3['temperature_assumption_id']}, "
         f"{s3['exit_wave']['n_realisations']} realisations averaged after squaring) vs the static S2: specular beam at the exit plane and object amplitude on the "
         "detector for realisation 0; the thermal/static ratio is printed in the figure and in "
         "tools/report/report_figures_output.txt; one realisation of a tiny cell with the UNVALIDATED "
         "engine, indicative only."),
        ("s4_plasmon_fringe_contrast.png", "tools/report/report_figures.py (fig_s4)", rf,
         "SP/report_smoke/S1_base, S4_plasmon_losses",
         f"{_run_commit(runs, 'S1_base')}; {_run_commit(runs, 'S4_plasmon_losses')}",
         f"S4, variant plasmon_losses ({lo4['object_label'].split(' (')[0]}, n = "
         f"{lo4['mean_excitations_object']:g} per reflection) vs S1 (n = 0, B30), geometric engine, same dose "
         f"{s4['detector']['dose_e_per_px']:g} e/px (B24): empty-hologram fringe contrast "
         f"{s1['reference']['empty_hologram_fringe_contrast']:.4f} -> "
         f"{s4['reference']['empty_hologram_fringe_contrast']:.4f}, hologram crops on one grey scale, and the "
         "phase noise inside the terrace-1 region; the step heights stay within 1 sigma (S4 "
         f"{_steps(s4)}); DEMO."),
        ("s5_oxide_stack_heights.png", "tools/report/report_figures.py (fig_s5)", rf,
         "SP/report_smoke/S1_base and the four geometric S5_oxide_* runs",
         "; ".join(_run_commit(runs, n) for n in ("S1_base", *ox)),
         "S5, continuum oxide (stand-in B41, conformal; consumed-layer count DERIVED_HERE) on the geometric "
         "demo: schematic of the built stack across the a/2 step (kept and consumed atomic planes, "
         f"pre-oxidation surface, oxide with {o20['vacuum_edge_width_A']:g} A erfc edges; the riser is not "
         f"modelled), the layer potential for {o20['thickness_A'] / 10:.1f} and {o15['thickness_A'] / 10:.1f} nm, "
         "the recovered - built step heights without and with the oxide, with and without V' (all within 1 "
         "sigma), and the reflected amplitude (RMS "
         f"{a1:.4f} without oxide; " + ", ".join(
             f"{n.replace('S5_oxide_', '')} {s['detector']['empty_object_amplitude']:.4f}" for n, s in ox.items())
         + "); DEMO."),
        ("s6_torus_compact.png", "tools/plots/torus_compact.py (reused, unchanged)",
         "PYTHONPATH=. venv/bin/python tools/plots/torus_compact.py --trench SP/report_smoke/S6_torus_trench "
         "--ridge SP/report_smoke/S6_torus_ridge --out SP/report_smoke/figures/s6_torus_compact.png",
         "SP/report_smoke/S6_torus_trench, S6_torus_ridge",
         f"{_run_commit(runs, 'S6_torus_trench')}; {_run_commit(runs, 'S6_torus_ridge')}",
         f"S6, configs/demo_smoke_torus_{{trench,ridge}}.yaml (half torus R {f6['major_radius_A']:g} A, r "
         f"{f6['minor_radius_A']:g} A, stand-ins B33/B34; "
         "geometric engine): object hologram, wrapped phase, measurable pixels and the profile across the ring; "
         f"measurable {100 * t6['S6_torus_trench']['measurable_fraction_of_detector']:.1f} % (trench) and "
         f"{100 * t6['S6_torus_ridge']['measurable_fraction_of_detector']:.1f} % (ridge) of the detector, "
         f"{t6['S6_torus_trench']['measurable_footprint_px']} and {t6['S6_torus_ridge']['measurable_footprint_px']} "
         "pixels on the ring footprint: the flat surface reconstructs, the ring does not (15 in wide at 130 dpi; "
         "made for a landscape page)."),
        ("s7_supercell_trench_T1.png", "tools/plots/torus_atomistic.py (report T1; copied unchanged)",
         "PYTHONPATH=. venv/bin/python tools/plots/torus_atomistic.py --runs SP/torus --out SP/torus/figures "
         "(inferred from the script's usage line and the file locations; T1 does not record the exact line)",
         "SP/torus/ms_trench", f"trench {_commit(t1m['trench'])}",
         f"S7 (report T1, not rerun): atomistic half-torus trench (R {t1s['trench']['feature']['major_radius_A']:g}"
         f" A, r {t1s['trench']['feature']['minor_radius_A']:g} A, B33) in the {t1s['trench']['n_atoms']:,}-atom "
         "Si(001) cell: top-layer height map, cross-sections and built vs ideal a/4 terraces; DEMO structure."),
        ("s7_exitwave_trench_T1.png", "tools/plots/torus_atomistic.py (report T1; copied unchanged)",
         "as s7_supercell_trench_T1.png", "SP/torus/ms_trench and ms_flat",
         f"trench {_commit(t1m['trench'])}; flat {_commit(t1m['flat'])}",
         "S7 (T1, not rerun): complex exit wave of the trench and its difference to the flat reference "
         f"(Kirkland IAM, no absorption B30, static lattice, {t1s['trench']['theta_ext_rad'] * 1e3:.4f} mrad "
         "B32): UNVALIDATED (finite-cell "
         "build-up not converged); no phase or height may be read from it."),
        ("s7_exitwave_ridge_T1.png", "tools/plots/torus_atomistic.py (report T1; copied unchanged)",
         "as s7_supercell_trench_T1.png", "SP/torus/ms_ridge and ms_flat",
         f"ridge {_commit(t1m['ridge'])}; flat {_commit(t1m['flat'])}",
         "S7 (T1, not rerun): as the trench figure for the ridge (B34); UNVALIDATED, no phase or height may be "
         "read from it."),
        ("s8_buried_compact_T5.png", "tools/plots/buried_torus.py (report T5; copied unchanged)",
         "OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python tools/plots/buried_torus.py --runs SP/buried --out "
         "SP/buried_t5/figures (T5 report section 0)", "SP/buried/ms_* (report T3)",
         "runs: " + ", ".join(b_commits),
         f"S8 (T3 runs, T5 analysis, not rerun): buried torus void (R {bcase['feature']['major_radius_A']:g} A, "
         f"r {bcase['feature']['minor_radius_A']:g} A, caps {bcase['study_caps_A']} A, B42) under flat Si(001), "
         f"TEST_ONLY absorption r = {bcase['physical_absorption']['test_only_r0.1']['ratio']:g} (the r = 0 pair "
         "of cap 10, B30, is not in this figure), UNVALIDATED engine, no dose model: supercell sections "
         "and the vacuum-origin part of the specular-beam difference on one shared log scale; the panel "
         "titles are the T5 readings (tools/review/t5/buried_torus_analysis_output.txt lines 324-328)."),
    ]
    import subprocess
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    st = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout
    print("R1 figure manifest (tools/report/figure_manifest.py). SP = " + str(sp))
    print(f"written at repository HEAD {head}; git status --porcelain: {st.split() and st.strip().splitlines() or 'clean'}")
    print("All figures: DEMO runs, not comparable to experiment; 200 keV; multislice engine UNVALIDATED "
          "for step heights. Figures made by tools/report/report_figures.py are 7.5 in wide at 150 dpi.")
    print("Figure stdout (every annotated number): tools/report/report_figures_output.txt; run parameters and "
          "results: tools/report/smoke_parameters_output.txt; campaign log: SP/report_smoke/campaign_log.txt.")
    for f, script, cmd, rundir, commit, cap in entries:
        p = fig / f
        im = Image.open(p)
        dpi = im.info.get("dpi")
        print("")
        print(f"file:     SP/report_smoke/figures/{f}")
        print(f"sha256:   {hashlib.sha256(p.read_bytes()).hexdigest()}; {im.size[0]} x {im.size[1]} px; dpi "
              f"{round(dpi[0]) if dpi else 'not recorded'}"
              + (f"; {im.size[0] / dpi[0]:.2f} x {im.size[1] / dpi[1]:.2f} in" if dpi else ""))
        print(f"script:   {script}")
        print(f"command:  {cmd}")
        print(f"runs:     {rundir}")
        print(f"commits:  {commit}")
        print(f"caption:  {cap}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
