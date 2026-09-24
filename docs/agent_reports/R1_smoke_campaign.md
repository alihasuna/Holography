# R1: smoke-test campaign on HEAD with parameters and figures (for the supervisor report)

Status: IN PROGRESS (written incrementally; final status at the end). Agent R1. Nothing committed
by R1 (the orchestrator commits). Branch `claude/electron-holography-orchestration-nakd7r`,
HEAD `2896522` at start. Beam energy 200 keV throughout (300 keV never used).

`SP` = `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`;
outputs (runs, figures) in `SP/report_smoke/` (never under `outputs/` of the repository).
Committed code: `tools/report/` only (new). Not touched: `reflection_holo/`, `configs/`, `tests/`,
`scripts/hpc/`.

## Log

1. Inputs read: configs/demo_smoke_si001.yaml (base and every variant), demo_smoke_torus_{trench,
   ridge}.yaml, demo_convergence_si001.yaml, pipeline CLI (`reflection_holo/pipeline/__main__.py`,
   `run.py` outputs), tools/plots/*.py, reports P1, T1, T2, T5, E3, the S7 run directories
   (`SP/torus/ms_*`, T1, and a later clean rerun `SP/torus_ms/` at a1ef2a0) and the S8 run
   directories (`SP/buried/ms_*`, T3; analysis `tools/review/t5/buried_torus_analysis_output.txt`).
   Machine load before starting: 0.14 (4 cores).
2. Wrote `tools/report/run_smoke_campaign.py` (pipeline CLI per run, thread variables = 4 =
   runtime.threads, per-command wall limit required on the command line, campaign log with commit,
   git status, package-tree hash, command, status, wall and child CPU time). Probe with S1 only
   (deleted afterwards), then the full campaign:
   `PYTHONPATH=. venv/bin/python tools/report/run_smoke_campaign.py --out SP/report_smoke --timeout-s 1200`
   19:05:40-19:08:22 UTC, exit 0, all 12 runs OK (S1, S2, S3, S4, five S5 runs, two S6 runs, S9 as
   4 member jobs plus assembly). Commit 2896522; the only differences from HEAD are the untracked
   files `tools/report/` and this report (tracked files identical to HEAD; recorded as dirty in the
   manifests, with the untracked-file hash); package-tree SHA-256 14148875...006d1 (79 files).
   Log: `SP/report_smoke/campaign_log.{txt,json}`; per-run stdout in `SP/report_smoke/logs/`.
   S9 (convergence, 4 members) took 41.4 s wall, 89.5 s CPU, so it was run (limit ~10 min CPU).
3. Correction to item 2: the orchestrator committed snapshot d022473 at 19:06:20 UTC while the
   campaign ran (docs and tools only). S1, S2, S3, S4, S5_oxide_2p0nm and S5_oxide_2p0nm_no_absorption
   ran at 2896522 (dirty: untracked tools/report files and this report only); S5_oxide_1p5nm,
   S5_oxide_1p5nm_no_absorption, S5_multislice_tiny_oxide_2p0nm, S6 and S9 ran at d022473 (clean).
   Every run's manifest records the same reflection_holo package-tree SHA-256 (14148875c6ba...), i.e.
   the same package code. Per-run commits: summary table "T." of the parameter output. Not rerun.
4. Wrote `tools/report/smoke_parameters.py`; saved output `tools/report/smoke_parameters_output.txt`
   (2087 lines, rc 0; below "PO:n" = its line n). Parameter tables come from the package's loader
   `load_pipeline_file(path, variant=...)`, grouped by stage, each value with its unit and its label as
   the configuration states it (records without an assumption_id field print their source text, e.g.
   lattice_parameter "model_assumptions B2"); a difference list against S1 for every other run; the
   values the code computed (angle, grids, cell box and slices from the engine manifest, resolution,
   noise, contrast, oxide stack); the results; cross-run comparisons (block C); a summary table
   (block T); S7 and S8 parameters from their saved case/summary files and S8 results as verbatim lines
   of the T5 output.
5. Wrote `tools/report/report_figures.py` (overview, S1-S5, copies of the reused T1/T5 figures with
   SHA-256), `tools/report/make_report_figures.sh` (runs it, `tools/plots/torus_compact.py` for S6 and
   `tools/plots/smoke_figures.py` for the S2 supplementary figures; stdout saved to
   `tools/report/report_figures_output.txt`) and `tools/report/figure_manifest.py` (writes
   `tools/report/figure_manifest.txt`: file, SHA-256, pixels, dpi, script, command, runs, commits,
   caption; the numbers in the captions are read from the runs). Every array's axes and plane are
   asserted from summary.json["arrays"], detector and exit-plane pixel sizes against the coordinate
   arrays. Figures were inspected visually and relaid out until no text overlapped.
   `bash tools/report/make_report_figures.sh SP`: rc 0, 10.8 s.

## Derived quantities (PO:7-24; package functions, cross-checked with tools/reflection_step_phase_calculator.py)

lambda(200 keV) = 0.02507934 A (calculator identical), k = 250.5323 rad/A; d_008 = a/8 = 0.67886 A,
vacuum Bragg angle of (0,0,8) 18.4726 mrad. Signs: exp(+i(k.r - wt)), Delta_phi = -(4 pi/lambda) h sin(theta).

| (0,0,8), 200 keV | V0 12.0 V (B1; geometric demos, rule B19) | V0 13.903 V (Kirkland IAM MIP; multislice, rule B32) |
|---|---|---|
| external glancing angle | 16.4743 mrad | 16.1347 mrad |
| s = 4 pi sin(theta)/lambda | 8.2543 rad/A | 8.0842 rad/A |
| height per 2 pi wrap h_2pi | 0.7612 A | 0.7772 A |
| a/4 up-step phase | -11.2071 rad = -1.7837 wraps; wrapped +1.3593 rad (apparent -0.1647 A) | -10.9761 rad = -1.7469 wraps; wrapped +1.5903 rad |
| a/2 up-step phase | -22.4142 rad = -3.5673 wraps; wrapped +2.7185 rad (apparent -0.3293 A) | -21.9522 rad = -3.4938 wraps; wrapped -3.1026 rad |

The V0 = 12 V row equals the C calculator's (0,0,8) row (C_calculator_output.txt line 195, printed at PO:21-22).

## Results (all DEMO, not comparable to experiment; wall/CPU from the campaign log)

| test | run (config, variant) | verdict | key numbers | wall / CPU s |
|---|---|---|---|---|
| S1 | demo_smoke_si001, base (geometric) | 3 of 3 heights | a/2: +2.71564 +- 0.01649 A (built +2.71545); a/4: -1.35765 +- 0.00825, -1.35799 +- 0.00825 A (built -1.35773); no-step control -0.003687 vs tolerance 0.012310 rad, passed (PO:127-132) | 2.9 / 3.8 |
| S2 | multislice_tiny | NO HEIGHT | terraces 489 A < 3-resolution margin (3 x 372 A); no-step control not performed (PO:301-305) | 9.8 / 22.0 |
| S3 | multislice_tiny_thermal | NO HEIGHT | frozen phonons B35/B36, 2 realisations; detector object amplitude ratio thermal/static 0.7692 (summary definition, PO:1882), 0.7521 (all lit px, figure script); (0,0,8) Debye-Waller amplitude exp(-B (g/2)^2) = 0.7724; one realisation of a tiny UNVALIDATED cell: indicative only | 13.0 / 35.7 |
| S4 | plasmon_losses (B38, n = 1.246) | 3 of 3 heights | empty-hologram contrast 1.0000 -> 0.5363; predicted phase noise x1.865, measured terrace scatter x1.717 (means); heights within 0.12 sigma of built; no-step control passed (PO:592-597, 1854-1858) | 2.8 / 3.8 |
| S5 | oxide_2p0nm, _no_absorption, oxide_1p5nm, _no_absorption (geometric, B41) | 3 of 3 heights each | all heights within 0.05 sigma of built; reflected amplitude ratio 0.5271 (2.0 nm) and 0.6186 (1.5 nm) = zero-loss model exp(-2 Im k'_perp t) to 4 digits, 1.0000 without V'; terrace phases shifted by a common offset (spread <= 0.0041 rad); no-step controls passed (PO:1860-1879) | 3.8-4.1 / 5.0-5.7 |
| S5 | multislice_tiny_oxide_2p0nm | NO HEIGHT | UNVALIDATED engine; no measurable region (PO:1383-1387) | 17.2 / 45.3 |
| S6 | demo_smoke_torus_trench / _ridge (geometric, B33/B34) | height map | measurable 39.8 % / 18.7 % of the detector; ring footprint 0 of 62 / 0 of 5110 lit px measurable; ring cross-section 0.110 resolution elements along the beam: UNRESOLVED; no-step control passed (PO:1519-1521, 1654-1656) | 31.4 / 32.8; 27.6 / 28.8 |
| S7 | T1 atomistic half torus (not rerun) | none quotable | 547 662 / 554 721 / 551 448 atoms, 945 x 1134 x 1124 slices, 16.1347 mrad; exit waves UNVALIDATED; runs at 2471f76 (dirty) and c544257; clean rerun at a1ef2a0 exists in SP/torus_ms (CASE differs only by the working-reflection record) | T1: 188-207 s simulate |
| S8 | T3 buried void (not rerun), T5 analysis | readings (T5 OUT:317-328) | cap 5 A: 0.0274-0.0789 rad, 2.6-10.3 %; cap 10 A: not demonstrated; caps 20/30 A: numerical artefact by analogy; TEST_ONLY r = 0.1, no dose model | T3: 473-698 s simulate |
| S9 | demo_convergence_si001 (4 members + assembly) | NO HEIGHT | quadrature error bound 8.14e-5 <= 0.01; convergence coherence median 0.99925 (min 0.99810); no measurable region (PO:1838-1849) | 41.4 / 89.5 |

The multislice engine's VALIDATION_STATUS (UNVALIDATED for step heights) is printed verbatim once in
the parameter output; it applies to S2, S3, S5 multislice, S7, S8 and S9.

## Figures (SP/report_smoke/figures/; manifest tools/report/figure_manifest.txt)

f0_pipeline_overview.png (flow with module names and refusal gates); s1_staircase_geometric.png;
s2_multislice_tiny_supercell_exitwave.png (+ s2_detail/supercell.png, 15 in wide, supplementary;
s2_detail/exit_wave_complex.png made by the reused script but NOT recommended: see manifest);
s3_thermal_vs_static.png; s4_plasmon_fringe_contrast.png; s5_oxide_stack_heights.png;
s6_torus_compact.png (reused tools/plots/torus_compact.py, 15 in wide at 130 dpi, landscape page);
s7_supercell_trench_T1.png, s7_exitwave_trench_T1.png, s7_exitwave_ridge_T1.png (T1 copies);
s8_buried_compact_T5.png (T5 copy). The T1/T5 copies keep their original size and dpi.
Sizes: my figures are 7.5 in wide at 150 dpi; the reused ones are wider (s6 15.0 in at 130 dpi, s7
supercell 13.6 in at 130 dpi, s7 exit waves 21.8 in at 120 dpi, s8 14.2 in at 130 dpi, s2_detail
14.6 / 13.0 in at 150 dpi): at 7 in their text is small; use a landscape page or an appendix.

## Files (all new, under tools/report/; nothing else in the repository changed)

run_smoke_campaign.py; smoke_parameters.py + smoke_parameters_output.txt; report_figures.py;
make_report_figures.sh; report_figures_output.txt; figure_manifest.py + figure_manifest.txt.
Reproduce: `PYTHONPATH=. venv/bin/python tools/report/run_smoke_campaign.py --out SP/report_smoke
--timeout-s 1200`, then the smoke_parameters.py command in its docstring, then
`bash tools/report/make_report_figures.sh SP`. Not touched: reflection_holo/, configs/, tests/,
scripts/hpc/, tools/plots/ (reused unchanged). No test file touched; no test run (none required).

## NOT RUN

- S7 and S8 multislice runs (instruction): parameters and results from the saved files; figures are
  copies of T1/T5 figures, not regenerated. The clean a1ef2a0 rerun of the T1 cases (SP/torus_ms)
  has no figures; only its parameters and timings are printed. The T1 figure command line is inferred
  (T1 does not record it). R1 did not inspect the copied T1/T5 figures visually.
- No new S9 figure (the run's quicklook_detector.png / quicklook_exit_wave.png exist in
  SP/report_smoke/S9_convergence/).
- A campaign on a single commit: HEAD moved to d022473 during the campaign (item 3; same package code).
- No validation of any multislice number, no convergence study, no HPC/GPU demo
  (configs/demo_hpc_si001.yaml), no pytest run.
- Outputs (about 200 MB, mostly S6) are in the scratchpad only and are not persisted by git.

## Final status

COMPLETE. All 12 smoke runs (S1-S6, S9) ran OK (exit 0) on the package tree 14148875c6ba...;
parameter tables, derived quantities, results and the figure manifest are printed by committed
scripts with saved outputs. Not committed by R1.
