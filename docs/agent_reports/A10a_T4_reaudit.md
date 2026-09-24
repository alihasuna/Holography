# A10a: re-audit of T4 (fixes of audit A9a on the buried-torus-void study T3)

Auditor A10a, 2026-09-24. Branch claude/electron-holography-orchestration-nakd7r, HEAD 00851da.
A10a edits only this file; no code, test, configuration or other document is changed; nothing is
committed; nothing is written under outputs/. Scratch: SP/a10a/ with
SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
Status: FINAL.

## Verdict

T4's code fixes hold.
- The split is exact. It is placed at the top atomic plane, the same origin as the regions.
- The committed analysis output reproduces line for line from the committed script (R11).
- The M-1 slice loop equals the production engine bit for bit over the whole small cell, for flat
  and cap 30.
- The flat rerun is bitwise equal to T3's run.
- Every new test that guards a fix fails when that fix is reverted (R8). Three wiring mutations of
  the analysis script do survive (A10a-m3).

The problems are in what is claimed for the supervisor:
- A10a-M1 (MAJOR): the cap-5 vacuum-origin numbers (0.034-0.052 rad, 0.086-0.099, "robust to the
  split") are two samples of a mask choice. Reasonable masks give 0.027-0.079 rad and 0.026-0.103;
  the amplitude varies 4-fold.
- A10a-M2 (MAJOR): the supervisor summary (T4 section 10, items 2-4) turns two-beam estimates and
  a small-cell result back into facts about T3's cell. This is the pattern A9a M-1 objected to.
- Minor:
  - "CONFIRMED" travels without its history (stage-2 criterion chosen after stage 1);
  - the causal-path statement uses (0,0,16) instead of the band edge;
  - the test gaps above;
  - the compact figure's per-panel scale makes the numerical artefact look like the strongest
    signal;
  - row B42 needs three corrections.

Can the demo be shown with the B42 / section 10 wording? NOT AS WRITTEN. With the section 3 wording
below, yes, as a demo. Figure: buried_compact.png is the right figure, once its bottom row uses one
colour scale (or a common log scale) and its cap-5 title gives the range. Until then, show its top
row and cap-5 panel only, or signal_maps_r010_t4.png (column 4, common log scale) as technical
backup. Do not show the per-panel-scaled cap-20/30 panels without saying that they are a numerical
artefact about 1/200 of the cap-5 scale.

## 0. Command log (every command A10a ran; anything not listed was NOT RUN)

- R1. `git status`, `git log --oneline`, `git show --stat HEAD`; `wc -l` of the files in scope.
- R2. Read in full: docs/agent_reports/A9a_T3_audit.md, T4_a9a_fixes.md, T3_buried_torus.md,
  tools/plots/buried_torus.py, tools/review/t4/m1_nonlocal_tail_test.py and every
  tools/review/t4/*_output.txt / run log; engine.py propagate_slices and run_realisation;
  analysis.select_beam; feature_cell.build_feature_reflection_cell.
- R3. `ls -la --time-style=full-iso` of SP/buried_t4/**, tools/review/t4/; `find -newermt` for files
  written 10:28:30-10:34:00; `cat` of SP/buried_t4/logs/*.log, run_m1.sh, run_m1_stage2.sh;
  `diff` of the committed run logs against the scratch logs.
- R4. `SP/a10a/split_family.py` (`OMP_NUM_THREADS=1 venv/bin/python`, no repository import), output
  `SP/a10a/split_family.out`. Own aperture (numpy FFT, circle 0.2 1/A about sin(theta_out)/lambda),
  own V and P regions, own mask; T3's saved exit waves SP/buried/ms_*_test_only_r0.1. Recomputes
  T4's cap 5/10/20/30 numbers, the linearity of the split, the top-plane position, a family of ten
  masks and a cos^2-apodised aperture (T4: NOT RUN), and the (0,0,16) / band-edge causal reach.
- R5. `SP/a10a/loop_vs_engine.py` (`OMP_NUM_THREADS=2 PYTHONPATH=. venv/bin/python ... 30`,
  background, 216 s + 219 s per run, rc 0), output `SP/a10a/loop_vs_engine.out`. Builds T4's small
  TEST_ONLY cell (0.13 A rule) with T4's own builder functions and runs the PRODUCTION kernel engine.run_realisation on the flat
  cell and on the cap-30 cell over all 1124 slices; bitwise comparison with T4's saved `flat` and
  `full_30` waves (SP/buried_t4/m1_px013/waves_px0.13_caps20-30.npz).
- R6. Inline python: bitwise comparison of T3's and T4's buried_flat_r010 exit waves (array and
  bytes), diff of their metadata_json, the rerun manifest's repository record; `git -C
  SP/buried_t4/clone_HEAD log -1` and `status`; `cat` of run_flat_rerun.sh and its log.
- R7. Code reading: pipeline/config.py (gate, _check_structure, load_pipeline_dict), io/config.py
  (registry/item check), the registry's item-13 ids, scripts/torus/run_torus_multislice.py labels,
  the three new test files, tools/review/t4/mutate_t4.py and its output.
- R8. `SP/a10a/mutate_a10a.sh`, output `SP/a10a/mutate_a10a.out`: a control and six mutations, each on
  a `git archive HEAD` copy under SP/a10a/mut/ (never the repository), with the imported package path
  printed; only the named test files/functions run, 1 thread.
- R9. Read the PNGs SP/buried_t4/figures/buried_compact.png and signal_maps_r010_t4.png.
- R10. Inline `venv/bin/python -c` evaluating abtem KirklandParametrization().projected_potential('Si')
  at 0.5-7 A, output SP/a10a/kirkland_range.out.
- R11. `OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python tools/plots/buried_torus.py --runs SP/buried
  --out SP/a10a/figs_rerun`, output SP/a10a/analysis_rerun.out, then `diff` against
  tools/review/t4/buried_torus_analysis_output.txt with the figure directory substituted:
  `identical apart from the figure directory` (the committed output comes from the committed script).

NOT RUN: any full-size multislice run; the full pytest suite (the orchestrator's run is in
progress); T4's test files other than through the R8 control; a dose model; the local/tails
decomposition for caps 5 and 10; a finer-pixel run of T3's cell.

## 1. Findings, ranked

### A10a-M1 (MAJOR): the cap-5 "vacuum-origin" range is two samples of the mask choice, not a bound; "robust to the split" is false

**Where.** T4 report section 4 (table rows "cap 5 vacuum-origin, 2.5 A / 1.0 A ramp" and the
statement "the amplitude change (0.086-0.099 in ratio, against 0.098 in total) is robust to the
split"), section 10 (row text and supervisor item 2 "0.03-0.05 rad in phase and 8.6-9.9 % in
amplitude"), docs/model_assumptions.md:68 (row B42, "0.034-0.052 rad in phase and 0.086-0.099 in
amplitude ratio (ramps 2.5 and 1.0 A)"), tools/plots/buried_torus.py:669-670 (compact-figure title
"up to 34 mrad in V").

**What is right (R4).** The split is exact as implemented: F is a linear FFT-mask-IFFT
(analysis.py:35-42), and |F(Dm) + F(D(1-m)) - F(D)| / max|F(D)| = 5e-16 to 9e-16 for every mask
tried. x_rel = 0 is the top atomic plane: `highest atom x in cell coordinates: 99.113925 A
(surface_x_A 99.113925)`, the same origin as the regions (P and V use X > 0). T4's numbers reproduce
to all printed digits with an independent implementation: cap 5, 2.5 A ramp `max|dphi| 0.03388 rad,
max|rho-1| 0.08579, max|dpsi|/A 0.0848`; 1.0 A ramp `0.05216 rad, 0.09866, 0.09897`; total
`0.1283 rad, 0.09808, 0.1201`; cap 10 `0.0008715 rad, 0.00178, 0.001696` and `0.002715, 0.00328,
0.00354`; caps 20/30 P vacuum-origin `0.0002033` and `0.0001591`. An apodised (cos^2) aperture,
listed by T4 as NOT RUN, changes the cap-5 values by less than 1 %.

**What is wrong.** The two ramps sample a strong dependence; they do not bracket it. Masks that
admit nothing at or below the top atomic plane (the stated design) give, for cap 5 over V (R4,
`split_family.out`):

| mask m(x_rel) | max\|dphi\| (rad) | max\|rho-1\| | max\|dpsi\|/A_ref |
|---|---|---|---|
| sharp step at 0 | 0.0789 | 0.1033 | 0.1053 |
| sin^2 ramp 0 to 1.0 A (T4) | 0.0522 | 0.0987 | 0.0990 |
| sharp step at a/8 = 0.679 A (equivalent boundary) | 0.0435 | 0.0974 | 0.0974 |
| sin^2 ramp 1.0 to 2.0 A | 0.0349 | 0.0837 | 0.0823 |
| sin^2 ramp 0 to 2.5 A (T4) | 0.0339 | 0.0858 | 0.0848 |
| sin^2 ramp 0.679 to 3.179 A | 0.0343 | 0.0723 | 0.0710 |
| sin^2 ramp 1.358 to 3.858 A | 0.0329 | 0.0554 | 0.0553 |
| sin^2 ramp 0 to 5.0 A | 0.0308 | 0.0546 | 0.0541 |
| sin^2 ramp 2.5 to 5.0 A | 0.0274 | 0.0260 | 0.0304 |

(A ramp centred on the top plane, -1.25 to +1.25 A, gives 0.0739 / 0.1007 but admits x_rel <= 0 and
is excluded.) The phase spans 0.027-0.079 rad (T4: 0.034-0.052) and the amplitude ratio 0.026-0.103
(T4: 0.086-0.099, "robust"). The amplitude is the MOST mask-sensitive quantity, a factor of 4.

**Why.** T4's own output locates the cap-5 vacuum-origin part at the surface: `x-location of the
vacuum-origin |F(D m)|: {"peak_x_rel_A": 2.6356..., "centroid_x_rel_A": 0.3234...}`
(buried_torus_analysis_output.txt:24). The change sits within the first 2.5 A above the top plane,
which is the aperture's resolution and also the range of the top layer's potential (Kirkland
projected potential of one Si atom: 19.6 V A at 1 A, 1.27 V A at 2 A, 0.34 V A at 2.5 A, i.e.
sigma V = 14, 0.93 and 0.24 mrad per atom and slice; R10). How that layer is assigned (vacuum or
crystal) is a convention the cell cannot decide, and the answer follows the convention. This is
the one positive result of the study, and the supervisor would be given a range that looks like a
bound and a robustness claim that fails.

**Fix.** Report the cap-5 vacuum-side change as a mask-dependent range with the family stated, for
example "0.03-0.08 rad in phase and 3-10 % in amplitude, depending on how the first 2.5 A above the
top atomic plane (the resolution) are assigned; the total over V is 0.13 rad and 10 %". Delete
"robust to the split". Apply the same wording in B42, section 10 item 2 and the compact-figure
title. Optionally, print the family in the analysis script.

### A10a-M2 (MAJOR): the supervisor summary (T4 section 10, items 2-4) states two-beam estimates and a small-cell result as facts about T3's cell

A9a M-1 objected that T3 "presents a two-beam argument (section 4.1) as a fact about the engine".
Row B42 now carries the qualifiers. The supervisor summary, the text meant for Dr Blackburn, drops
them again.

- Item 2 says "changes the beam leaving the surface above it". Region V (x_rel 0-7.18 A) maps to
  surface source points z_s = L_z - x_rel / tan(theta_out) = 1081-1526 A (cell). The void spans z
  965-1089 A, so V lies DOWNSTREAM of the void, up to 445 A. That is where the two-beam
  characteristic puts it (surfacing 270.7 A downstream). Over the ring itself (P), the vacuum-origin
  change is smaller: 0.029 rad and |dpsi|/A_ref 0.033 (output lines 15, 153).
- Item 3: "At 10 A this cell cannot show it: the signal reaches the vacuum in a layer only 0.3 A
  thick at the exit plane". The 0.317 A is the TWO-BEAM layer. T4's own section 4 says the engine's
  band carries (0,0,16) at 55.4 mrad, and that this path reaches x_rel <= 6.14 A for cap 10. The band
  edge, 65.4 mrad, reaches 6.59 A. A localised void scatters into every in-band k_x, not only the
  systematic row. With vacuum travel at the aperture's steepest accepted angle (21.15 mrad) these
  become 8.05 and 8.64 A (R4). So "cannot show it" and "reaches the vacuum in a layer only 0.3 A
  thick" are not established. What the data show is that cap 10 is NOT DEMONSTRATED: the
  vacuum-origin part (0.17e-3 to 5.0e-3 of A_ref across the R4 mask family) is not attributed.
- Item 4: "At 20 and 30 A the signal would surface 1080-1620 A downstream, beyond the cell". That is
  again two-beam. Along (0,0,16) the void top surfaces 360.4 and 540.5 A downstream (T4's own
  numbers). Both lie inside the 560.9 A of crystal downstream of the ring's upstream edge. At the
  band edge the distances are 305.2 and 457.7 A (R4).
- Item 4: "The small difference above the ring (about 2e-4) is a numerical artefact (confirmed in a
  smaller test cell)". What was CONFIRMED is that a 2.7e-5 to 7.2e-5 difference, from a different
  void (R 20 A, r 6 A, 709/678 sites) in a 70.6 A wide cell, is numerical. For T3's 2.3e-4 and
  1.6e-4 the attribution is an inference by analogy. T4's section 2 says so ("inference,
  UNVALIDATED"); the summary does not. The analogy is also imperfect. At T3's pixel the small cell
  gives a cap-20/cap-30 ratio of P vacuum-origin of 2.64 (stage 1); T3's cell gives 2.03e-4 /
  1.59e-4 = 1.28.

**Why it matters.** This is the wording the supervisor reads. Items 2-4 would tell him three
things: that the cap-5 signal leaves the surface above the void; that a 10 A void is invisible in
principle in this cell; and that the deep-cap signal is a proven artefact. None of the three is
established, and the geometry contradicts the first.

**Fix.** Section 3 of this report gives exact replacement wording.

### A10a-m1 (minor): M-1 "CONFIRMED" rests on a criterion chosen after stage 1 had passed it; the label travels without that history

**Timeline, verified from the files (R3).**
- The stage-1 propagation ran 10:21:40-10:29:02 (runs_log.txt) with an EARLIER revision of the
  script. Its log (m1_stage1_px0.13_run_log.txt; identical to the scratch log apart from a 4-line
  header that says so) already printed the vacuum-origin values: `local: ... vacuum-origin P max
  3.412e-07` against `full: ... vacuum-origin P max 7.208e-05`. It also printed `verdict (prediction
  stated in the docstring): NOT CONFIRMED`.
- The committed script, whose docstring and `--criterion` fix the stage-2 criterion, has mtime
  10:31:06. run_m1_stage2.sh (10:32:48) passes `--criterion vacuum_origin`. Stage 2 started at
  10:32:53. So the criterion WAS fixed before stage 2 ran.
- T4's "file saved 10:30:06" cannot be checked: the report file was overwritten later. The comment
  in run_m1_stage2.sh ("report section 0 at 10:35") names a time after the run started.
- T4's report discloses all of this in section 2: the stage-1 NOT CONFIRMED on its pre-stated total
  criterion, the post-hoc diagnosis, and "Stage 2 re-tests this".

**Assessment.** Stage 2 is a replication, at a finer pixel, of a criterion already known to pass at
stage 1. Its pass/fail rule therefore adds little. The discriminating new evidence is the pixel
dependence, which had no pre-stated rule. The P vacuum-origin maximum falls to x 0.040 and x 0.128,
while the physical end-face signal changes by x 1.008 and x 0.918. I nevertheless find the small-cell
conclusion (numerical, not physical) supported by three independent lines:
1. The far change alone reproduces P (tails/full 0.998-1.012 at both pixels).
2. The far change is non-physical by construction. The Kirkland potential gives sigma V <= 1.4e-6
   rad per atom at 5 A. The measured |d| in the tails region is 8.5e-4 (stage 1) and 4.5e-4
   (stage 2).
3. The pixel dependence above.

The decomposition does isolate the numerical part. M depends on x only, so "local" is the void's
depth band +-5 A over the whole slice. It contains the physical change plus some numerical
near-field. "tails" contains only numerical content: Fourier-synthesis tails, and band-limit ringing
of the physical change.

The loop is the engine, bit for bit, over the WHOLE cell and not only the two 12-slice windows (R5):
`flat: engine.run_realisation vs T4 loop wave: bitwise equal True; max|diff| 0.000e+00` and
`full_30: engine.run_realisation vs T4 loop wave: bitwise equal True; max|diff| 0.000e+00`. The
full_30 result also covers T4's sampled check (5 slices) that the void cell's other slices equal
the flat cell's. T4 rightly says "scales with the tail amplitude" is NOT supported.

**What must change.** The label "CONFIRMED" is used without this history in row B42
("CONFIRMED in a TEST_ONLY small cell only") and in buried_torus.py:88-92 M1_ATTRIBUTION
("CONFIRMED there"). Use "CONFIRMED in a TEST_ONLY small cell on a criterion set after stage 1
(stage 1 on its pre-stated total criterion: NOT CONFIRMED at cap 20, explained by aperture leakage
of end-face signal)". For T3's cell: "attributed by analogy (UNVALIDATED)".

### A10a-m2 (minor): the causal-path statement uses the steepest SYSTEMATIC beam and the specular exit angle; the engine's bound is the band edge and the aperture's acceptance

**Verified (R4).**
- Band limit: `fx_max_per_A 2.6077`, `angle_ceiling_x_mrad 65.40` (exit-wave metadata).
- (0,0,16): f_x = 12/a = 2.2096 1/A, 55.44 mrad; (0,0,20) at 16/a = 2.946 1/A lies outside the
  band.
- Surfacing distances 90.1 / 180.2 / 360.4 / 540.5 A and exit-plane reach +7.60 / +6.14 / +3.24 /
  +0.33 A: reproduced.

**What is incomplete.** The void is not periodic. It scatters into every in-band k_x, so the engine's
steepest path is the band edge (65.4 mrad), not the systematic (0,0,16) beam. The specular aperture
(radius 0.2 1/A about 0.643 1/A) also accepts vacuum waves up to 21.15 mrad, not only theta_out
(R4):

| cap | band edge: surfaces downstream | reach at theta_out | reach at 21.15 mrad |
|---|---|---|---|
| 5 | 76.3 A | +7.82 A | +10.25 A |
| 10 | 152.6 A | +6.59 A | +8.64 A |
| 20 | 305.2 A | +4.13 A | +5.41 A |
| 30 | 457.7 A | +1.67 A | +2.18 A |

T4 section 4 says "P (x_rel 7.05-9.05 A) lies beyond the cap-20 and cap-30 values: no in-band path
from those voids reaches P", and the reading line (buried_torus.py:441-442) says "outside every in-band
causal path". Both hold for the undilated projection only. The P region on which every number is
taken is dilated to 4.55-11.55 A, and it is reached for cap 20 (5.41 A). The sharp aperture's
point-spread function also has long tails, so "reach" in the filtered image is not a hard edge.

**Does it weaken the attributions?**
- Caps 20/30: no. The small cell's "local" run contains every physical path, whatever its angle, and
  its vacuum-origin value at P is 3.4e-7 (stage 1) and 1.1e-7 (stage 2) of A_ref for cap 20, against
  full values of 7.2e-5 and 2.9e-6.
- Cap 5: no. More paths only add physical vacuum signal. Numerical tails at cap 5 were not
  decomposed (NOT RUN). By size they are unlikely to matter (the deep-cap artefact is 2e-4 against
  8.5e-2).
- Cap 10: the NOT DEMONSTRATED verdict stands, but its stated reason (the 0.317 A two-beam layer) is
  not a bound of the engine. T4's reading line and row B42 say so ("V is not a strict causal
  bound"); the supervisor summary does not (A10a-M2).

**Fix.** Use the band edge (65.4 mrad) for V16 and vacuum_class. Mention the aperture's angular
acceptance. Change "no in-band path ... reaches P" / "outside every in-band causal path" to "the
steepest in-band path (band edge) reaches x_rel <= 4.1 A (cap 20) and 1.7 A (cap 30) at the specular
angle, 5.4 and 2.2 A at the aperture's steepest accepted angle; the ring's projection (7.05-9.05 A)
lies beyond".

### A10a-m3 (minor): the m-5 tests do not guard the wiring that produces the supervisor-facing numbers

Mutations on scratch copies (R8, `mutate_a10a.out`):
- The control passes: `21 passed`.
- These are caught: m-3 check removed (`2 failed`); m-3 check narrowed to B42 only (`2 failed`);
  buried branch of (f) disabled (`4 failed, 1 passed`). This reproduces T4's M6 and M1.
- These SURVIVE:
  - A4: in analyse(), the "vacuum-origin" metrics computed from the TOTAL F(D) (`met_vac =
    metrics(pf + parts["total"], ...)`) gives `14 passed`. Every vacuum-origin number in the output,
    the table, row B42 and the compact figure comes from this line.
  - A5: the cap-5 reading line quoting the TOTAL phase as the vacuum-origin phase gives `14 passed`.
  - A6: V16 computed with the two-beam angle instead of the (0,0,16) angle gives `14 passed`.

T4's claim that the m-5 tests cover "the vacuum mask and the split" is true for split_parts(). It is
not true for analyse(), metrics() (5 % mask, A_ref window) or main().

**Fix.** Add a test that runs analyse() (or metrics() plus the analyse wiring) on a synthetic pair of
exit waves with a known vacuum-only and a known end-face-only difference. Add tests of reading_line
for the cap-5 numbers and of V16.

### A10a-m4 (minor): buried_compact.png uses a per-panel colour scale, which makes the numerical artefact the most prominent "signal" in the figure

Bottom row, from the figure:
- cap 5: +-34 mrad;
- cap 10: +-0.9 mrad;
- cap 20: +-0.2 mrad;
- cap 30: +-0.12 mrad.

On its own scale, each deep-cap panel shows two saturated blobs sitting exactly inside the blue P
outline. That is the cleanest, most "detected-looking" pattern in the figure, and it is the artefact
(A9a M-1). The titles say "attributed to a numerical artefact (T4 M-1)", but the eye reads the
colour. The cap-5 title "up to 34 mrad" carries only one mask (A10a-M1).

signal_maps_r010_t4.png is honest: its log10 |F(D m)|/A_ref column uses a common -8..0 scale, on
which caps 20/30 are about 3.5 decades below cap 5. But it has 16 panels at 25 x 18 in, a technical
figure rather than a supervisor figure.

**Fix.** In buried_compact.png:
- use one colour scale for the bottom row, or replace it by log10 |F(D m)|/A_ref on a common scale;
- or overprint the cap-20/30 panels "numerical artefact (about 1/200 of the cap-5 scale)";
- give the cap-5 title as a range (A10a-M1).

### A10a-m5 (minor): row B42 (docs/model_assumptions.md:68) needs three corrections

Every number in the row traces to a committed output (section 2, item 6). Three corrections:
1. Cap 5: the range "0.034-0.052 rad ... 0.086-0.099 ... (ramps 2.5 and 1.0 A)" (A10a-M1).
2. "CONFIRMED in a TEST_ONLY small cell only" is attached to T3's values. It needs the stage history
   and the analogy qualifier (A10a-m1).
3. "(0,0,16) beam" should be "steeper in-band beams (band edge 65.4 mrad)" (A10a-m2).

The gate sentence ("refuses B42 on the half-torus routes and, since T4 (A9a m-3), on the no-feature
route") is correct (R8, section 2, item 5). Section 3 gives the text.

### Notes

- n-1 (m-1 verified). T3's and T4's buried_flat_r010 exit waves are bitwise equal (R6):
  - `array_equal True bytes equal True sha a199ef5ca699665a a199ef5ca699665a`;
  - the metadata differ only in `/timing_s/{propagation,setup,total}`;
  - the rerun manifest records commit dc4eb7f4..., `dirty: False`, `untracked_files: []`, package
    tree 7f3b2851;
  - the clone is at dc4eb7f and clean;
  - run_flat_rerun.sh ran from the clone with `PYTHONPATH=.`.

  T4's committed comparison output matches. The residual A9a stated is closed for the flat run only,
  as T4 says.
- n-2 (the stage-1 waves). The stage-1 propagation used an earlier, uncommitted revision of
  m1_nonlocal_tail_test.py. This is disclosed in the header of m1_stage1_px0.13_run_log.txt. R5 shows
  that its `flat` and `full_30` waves equal the production kernel bit for bit. The revision
  therefore does not matter for those waves. `full_20` was not rerun (NOT RUN).
- n-3 (gate, future-proofing). No route is open today: the registry's item-13 ids are B27, B33, B34
  and B42, and all four are in FEATURE_STAND_IN_SUB_KIND (registry lines 35, 43, 44, 58;
  config.py:250). The no-feature check (config.py:975-976) refuses only ids that ARE in the map with a
  non-None value. A future item-13 feature id added to the registry but not to the map would pass.
  Whitelist B27 on the no-feature route, or test that the registry's item-13 ids are a subset of the
  map. The second new test (test_no_demo_configuration_labels_no_feature_with_a_feature_stand_in)
  reads configuration files, so it cannot fail when the fix is reverted. That is by design. The
  refusal test uses two of the three no-feature demos (demo_smoke_si001 is not used).
- n-4 (cap-10 "mostly end-face signal"). This holds in amplitude for every mask in R4: vacuum-origin
  max|dpsi|/A_ref <= 5.0e-3, end-face part 8.5e-3 to 9.1e-3 (T4 output line 180; A9a C7). In phase it
  does not hold for a sharp mask at the top plane: vacuum-origin max|dphi| 5.4 mrad out of a 6.3 mrad
  total (R4). Write "mostly end-face signal in amplitude".
- n-5 ("sets a floor of about 1e-4 to 2e-4", T4 section 2, for the engine owner). This is the
  artefact of THIS void at THIS pixel. It depends on the removed-atom count and position, so it is
  not a general floor. Say "in T3's cell the artefact is 1.6-2.3e-4 of A_ref".
- n-6 (apodised aperture, T4 NOT RUN). Run here (R4, cos^2 tapers of 0.05 and 0.1 1/A).
  - It changes every VACUUM-ORIGIN value (caps 5, 10, 20, 30) by less than 1 %.
  - It changes the TOTALS by up to 10 % (cap 20 at P: 2.10e-4 against 2.32e-4) and 18 % (cap 10
    phase in V: 5.2 against 6.3 mrad), because less end-face signal leaks.

  The mask, not the aperture shape, carries the uncertainty of the vacuum-origin part (A10a-M1).
- n-7 (caps 20/30 are insensitive to the mask). P vacuum-origin values are 2.02e-4 to 2.10e-4 (cap 20)
  and 1.58e-4 to 1.64e-4 (cap 30) over the whole R4 family. The deep-cap difference sits well above
  the surface (at P), as the numerical-tail picture predicts.

## 2. Item-by-item record (the orchestrator's six checks)

1. **Vacuum-origin split.**
   - F(Dm) + F(D(1-m)) = F(D) is exact as implemented: 5e-16 to 9e-16 relative (R4). The script
     asserts it at 1e-9 (buried_torus.py:215).
   - The ramp starts at the top atomic plane (surface_x_A = highest atom x = 99.113925 A). That is
     the same origin and convention as the regions, which use X > 0.
   - The 2.5 A / 1.0 A choice SAMPLES the answer and does not bound it. The cap-5 claim is not a fair
     range: other reasonable masks give 0.027-0.079 rad and 0.026-0.103 in amplitude ratio, and the
     amplitude is not robust (A10a-M1).
   - Recomputed independently from T3's exit waves: caps 5, 10, 20 and 30 reproduce T4's numbers to
     all printed digits (R4). The committed analysis output reproduces line for line from the
     committed script (R11).
2. **M-1 test.**
   - The far part isolates the numerical tail (A10a-m1).
   - The loop is the engine's, bit for bit over the whole cell, for flat and cap 30 (R5).
   - The stage-2 criterion was fixed before stage 2 (script mtime 10:31:06 < start 10:32:53). It was
     chosen after the stage-1 vacuum-origin values were printed, and "file saved 10:30:06" cannot be
     verified.
   - CONFIRMED is justified for the small cell, but only with that history (A10a-m1).
   - T4 itself reports "scales with the tail amplitude" as NOT supported.
   - The transfer to T3's values is stated as an inference in T4 section 2. It is not stated as such
     in section 10 item 4 (A10a-M2) or in row B42 (A10a-m5).
3. **(0,0,16) statement.**
   - Band limit, 55.4 mrad, 65.4 mrad band edge, 90.1/180.2/360.4/540.5 A and 7.60/6.14/3.24/0.33 A:
     reproduced (R4).
   - The engine's causal bound is the band edge, with the aperture's acceptance up to 21.15 mrad. Cap
     20 then reaches the dilated P (A10a-m2).
   - It does not weaken the cap-5 vacuum-origin attribution, nor the cap-20/30 artefact attribution
     (the small cell's local run contains every physical path).
   - It removes the stated REASON for cap-10 NOT DEMONSTRATED ("0.3 A layer"), but not the verdict.
   - It contradicts summary items 3 and 4 as worded (A10a-M2).
4. **m-1.** Verified: bitwise equal exit waves, clean dc4eb7f clone, metadata differ in timing only
   (n-1).
5. **m-3 and tests.**
   - Each test that guards a fix fails when that fix is reverted: m-3 check removed or narrowed,
     `2 failed`; (f) buried branch off, `4 failed` (R8). The configuration-reading test cannot fail
     on a revert (n-3).
   - The m-5 tests miss the analyse() wiring, the cap-5 reading line and the V16 angle (A10a-m3).
   - No route for a feature stand-in on a no-feature run is open today; a future item-13 id could open
     one (n-3).
6. **Row B42 and T4 section 10.** Every number traces to a committed output:
   - buried_torus_analysis_output.txt: lines 235-238 (0.0339/0.0522 rad, 0.0858/0.0987, 0.128 rad,
     0.317 A, 6.34 mrad, 0.00824, 1082.6/1623.9 A); lines 203-204 (2.324e-4, 1.600e-4); line 191
     (|corr| 0.942, "common to both caps");
   - m1_stage2_px0.09_output.txt: "vacuum-origin P max ratio 0.040" / "0.128", dx 0.1292 / 0.0897;
     row B42 cites the script rather than this output file.

   The rounding in section 10 is correct (0.03-0.05 rad, 8.6-9.9 %, 0.3 A, 1080-1620 A, about 2e-4).
   Overstated or mislabelled:
   - the cap-5 range and "robust" (A10a-M1);
   - summary items 2-4 (A10a-M2);
   - "CONFIRMED" without history or analogy qualifier (A10a-m1, m5);
   - "(0,0,16)" as the steepest path (A10a-m2);
   - "changes the beam leaving the surface above it" (A10a-M2: V is downstream);
   - "sets a floor" (n-5).

## 3. Proposed wording

The numbers marked (A10a R4) come from this audit's scratch output, not from a committed file. Before
they go into the row, the analysis script should print the mask family, so that they trace to
tools/review/.

**Row B42, "why" column (replaces T4's text):**

> A feature of known shape to test whether reflection holography sees below the surface. Report T3,
> analysis revised by T4 (audits A9a, A10a). In the 1499 A demo cell (UNVALIDATED engine, TEST_ONLY
> r = 0.1; no dose model, so experimental detectability is not assessed):
> - Cap 5 A: the void changes the vacuum-side specular beam. The part that leaves through the vacuum
>   (end face masked before the aperture) is 0.03-0.08 rad in phase and 3-10 % in amplitude. The
>   spread comes from how the first 2.5 A above the top atomic plane is assigned; 2.5 A is the
>   resolution of the specular selection (A10a R4). The total over the vacuum region, 0.13 rad and
>   10 %, includes end-face signal carried by the aperture.
> - Cap 10 A: a vacuum-side change is NOT DEMONSTRATED. The two-beam causal vacuum layer is 0.32 A
>   (DERIVED_HERE), below the 2.5 A resolution. Beams inside the engine's band (up to 65.4 mrad)
>   could carry signal up to 6.6-8.6 A above the surface. The total over the vacuum region
>   (6.3 mrad, 0.8 %) is mostly end-face signal in amplitude. The vacuum-origin part (0.02-0.5 % of
>   the reference amplitude, depending on the mask) is not attributed.
> - Caps 20 and 30 A: by the two-beam characteristic (DERIVED_HERE) the signal from the void top
>   surfaces 1082.6 and 1623.9 A downstream, beyond the exit plane. The steepest in-band path
>   surfaces 305 and 458 A downstream and does not reach the ring's projection (A10a R4). The
>   engine's vacuum difference at that projection (2.3e-4 and 1.6e-4 of the reference amplitude) is
>   attributed to a numerical artefact of the non-local tails of the transmission function. The
>   attribution is BY ANALOGY and UNVALIDATED in this cell. In a TEST_ONLY small cell (same engine,
>   pixel rule and z geometry, smaller void; tools/review/t4/m1_stage1_px0.13_output.txt and
>   m1_stage2_px0.09_output.txt), the same kind of difference was reproduced by the far change of the
>   transmission function alone, and it fell to 0.04-0.13 of its value from dx 0.129 to 0.090 A. That
>   is CONFIRMED there, on a criterion set after a first stage whose pre-stated criterion gave NOT
>   CONFIRMED (aperture leakage). No full-size rerun.
> - The fitted decay lengths of T3 section 4.3 are withdrawn (cell artefacts). Numbers:
>   tools/review/t4/buried_torus_analysis_output.txt.

The first column's gate sentence can stay as committed.

**Supervisor summary (replaces T4 section 10 items 2-5):**

> 2. A void 5 A down changes the specular beam that leaves the surface downstream of it by
>    0.03-0.08 rad in phase and 3-10 % in amplitude, counting only what leaves through the vacuum.
>    The spread comes from how the first 2.5 A above the surface is counted; this simulation cannot
>    decide that.
> 3. At 10 A this cell does not demonstrate it. By the simple two-beam estimate, the signal would
>    reach the vacuum only in a 0.3 A layer at the end of the cell, below the 2.5 A resolution.
>    Steeper beams in the simulation could carry some of it further out. The small vacuum-side
>    change seen (at most 0.5 % of the reference amplitude) has not been attributed.
> 4. At 20 and 30 A the two-beam estimate puts the signal 1080-1620 A downstream, beyond the cell.
>    Steeper beams in the simulation surface sooner (about 300-460 A) but do not reach the vacuum
>    above the ring. The small difference seen above the ring (about 2e-4 of the reference amplitude) is most likely
>    a numerical artefact of the simulation. In a smaller test cell the same kind of difference was
>    traced to numerical tails of the atomic potential, and it shrank 8- to 25-fold at a finer
>    pixel. It was not re-checked in this cell.
> 5. Not shown: experimental detectability (no noise or dose model), any decay length, convergence
>    (pixel, slice, cell length), holograms and reconstruction.

Item 1 can stay as written.

**Other text.** Wherever T4's section 2/4 wording, M1_ATTRIBUTION (buried_torus.py:88-92) or the
reading line (buried_torus.py:441-442, "outside every in-band causal path") is quoted, apply A10a-m1 and
A10a-m2.
