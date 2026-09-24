# T4: fixes of audit A9a (T3 buried torus void)

Agent T4, 2026-09-24. Branch claude/electron-holography-orchestration-nakd7r. HEAD dc4eb7f at start.
Nothing committed by this agent. Scratch outputs: SP/buried_t4/, SP =
/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad. Beam energy 200
keV throughout. Status: FINAL (section 10).

## 0. Log (UTC)

- 10:00: read T3's report, A9a's audit (all findings, notes, section 3), A9a's scripts and outputs
  (SP/a9a/), T3's run outputs (SP/buried/), row B42. Machine idle (load 0.03).
- 10:04: fix m-1 rerun of buried_flat_r010 started on a clean clone of HEAD dc4eb7f
  (SP/buried_t4/clone_HEAD, `git status` clean), 2 FFT workers, `--max-cpu-seconds 3600`, load at
  start 0.01.
- 10:12: m-1 rerun finished (rc 0, simulate 447.2 s, wall 478 s). Exit wave bitwise equal to T3's
  (section 3).
- 10:15: tools/plots/buried_torus.py revised (M-2, m-2, m-6); debug run on T3's exit waves (30 s).
- 10:21: M-1 test stage 1 started (small TEST_ONLY cell, T3's pixel rule, caps 20 and 30), load at
  start 1.92 (another agent's processes), 2 FFT workers, `--max-cpu-seconds 3000`.
- 10:22-10:30: tests for m-4 (tests/structure/test_buried_assertion_f_layers.py) and m-5
  (tests/forward/test_buried_torus_analysis.py); mutation script tools/review/t4/mutate_t4.py
  (scratch copies, each its own scratch git repository; control passes).
- 10:29: M-1 stage 1 finished (rc 0, 442 s wall, propagation of 7 waves 400.0 s). Pre-stated
  criterion (TOTAL specular difference at P): cap 30 CONFIRMED, cap 20 NOT CONFIRMED (local/full
  0.548 at the P maximum), so the pre-stated overall verdict is NOT CONFIRMED. Diagnosis from the
  same run: the local part at P is end-face signal carried by the sharp aperture (its vacuum-origin
  part at P is 3.4e-7 of A_ref against a total of 5.3e-5), i.e. the M-2 mechanism; the criterion
  should have used the vacuum-origin part. Section 2 gives the numbers.
- 10:30: PRE-REGISTRATION of stage 2, written before it ran (file saved 10:30:06; stage 2
  started 10:32:53): an independent run at a finer pixel
  rule (max 0.09 A), caps 20 and 30, same cell. Criterion on the VACUUM-ORIGIN part at P: for every
  cap, tails/full in [0.8, 1.25] and local/full < 0.2, for the maximum and the rms over P.
  CONFIRMED if this holds for every cap; NOT CONFIRMED if local/full >= 0.5 or tails/full < 0.5 for
  any cap; INCONCLUSIVE otherwise. The pixel scaling (P value and tail components at 0.09 A over
  0.13 A) is reported descriptively, without a pass/fail rule.
- 10:32: stage-1 analysis rerun from the saved waves with the final script (`--reuse-waves
  --criterion total`): identical numbers, plus the vacuum-origin ratios and the tail Fourier
  components (tools/review/t4/m1_stage1_px0.13_output.txt).
- 10:32:53: M-1 stage 2 started (0.09 A pixel rule, caps 20 and 30, `--criterion vacuum_origin`,
  `--max-cpu-seconds 6000`), load at start 4.41 (X5's test suite).
- 10:47:50: stage 2 finished (rc 0, 897 s wall, propagation of 7 waves 782.3 s): CONFIRMED on the
  pre-registered criterion (section 2).
- 10:48-10:51: analysis wording for caps 20/30 fixed from the M-1 result; final analysis output and
  figures regenerated into SP/buried_t4/figures/.
- 10:51: LAST edit of shared code, pipeline/config.py (m-3), re-read immediately before; the test
  was added together with the fix. After it, only T4's own files changed: the analysis script's
  M-1 wording (a string constant) and this report; mutations M0-M6 rerun on the final files (all
  as expected).
- 10:52-10:57: tests/structure, the feature-cell tests, tests/pipeline, tests/io and the new tests
  (section 8).

## 1. Fixes at a glance

| finding | fix | test that fails when the fix is reverted (tools/review/t4/mutate_t4_output.txt) |
|---|---|---|
| M-2 | tools/plots/buried_torus.py: "x floor" rule, "detected/marginal" and the fitted-L table removed; apodised vacuum mask BEFORE the aperture; absolute values, total / vacuum-origin / end-face parts per cap; compact supervisor figure | tests/forward/test_buried_torus_analysis.py (M2: T3's script restored, 11 of 14 fail; M3: mask after the aperture, 1 fails; M4: sharp mask, 1 fails) |
| M-1 | small-cell TEST_ONLY decomposition of the void's change of the transmission function into local and far (numerical) parts, two pixel sizes (section 2): CONFIRMED (stage 2, criterion fixed before the run) | not a code fix (a test run) |
| m-1 | buried_flat_r010 rerun on a clean clone of HEAD dc4eb7f: bitwise equal (section 3) | not a code fix |
| m-2 | geometric zero worded "zero by construction of the surface-height model; not a geometric-engine run" | test_geometric_zero_statement (M5, 1 fails) |
| m-3 | pipeline/config.py no-feature branch refuses B33/B34/B42 on pattern_geometry (section 6) | test_no_feature_route_refuses_a_feature_stand_in (M6: check removed, 2 fail) |
| m-4 | tests/structure/test_buried_assertion_f_layers.py | M1: the buried branch of (f) disabled, 4 of 5 fail |
| m-5 | tests/forward/test_buried_torus_analysis.py (14 tests) | M2-M5 |
| m-6 | fits removed (no `fit_decay`, no fit lines, no table) | test_no_detection_rule_and_no_fitted_lengths (M2) |
| m-7 | proposed row text, section 10 | - |

Control M0 (no change): 30 passed.

## 2. M-1: the vacuum difference at the ring's projection (tools/review/t4/m1_nonlocal_tail_test.py)

Design (the cheapest decisive test found; TEST_ONLY, no production code changed). The engine
multiplies the wave in slice i by t_i = BL[exp(i sigma V_i) a(x)]. The void changes this by d_i =
t_i,void - t_i,flat. The physical potential of a removed Si atom is 1.9e-3 V A at 5 A and 3.8e-5 V A
at 7 A (Kirkland, abTEM function; sigma V = 1.4e-6 and 2.8e-8 rad). So beyond 5-7 A from the void,
d is numerical: the Fourier synthesis of off-grid atoms and the sharp 2/3 band limit. One pass
propagates, with the same flat potential:
- flat: t_flat;
- full: t_flat + d, which is the engine's void run;
- local: t_flat + d (1 - M), the change within 5 A of the void's x range;
- tails: t_flat + d M, the change farther away (sin^2 ramp of 2 A), numerical by construction.

The loop repeats engine.propagate_slices operation by operation. It is checked bit for bit against it
on two 12-slice windows, one of them through the void slices ("bitwise equal ... True", both runs).
The non-void slices of the void cells are bitwise equal to the flat cell's (checked). Cell: 13 x 276
periods (70.60 x 1498.93 A), the same z geometry, beam, angle, absorption and band as T3, 66 layers
(F5 for cap 30 with r = 6), and a smaller void (R 20 A, r 6 A: 709 and 678 sites removed). All engine
assertions and F1-F5 passed. As in T3's cell, P lies at x_rel 7.63-8.47 A (+2.5 A). The steepest
in-band path from the void top reaches x_rel <= 2.66 A (cap 20); from cap 30 it reaches nothing
(-0.25 A).

Stage 1 (0.13 A rule as T3, grid 1225 x 560, dx 0.1292 A; criterion "total", stated in the script
before the run; output tools/review/t4/m1_stage1_px0.13_output.txt):

| cap | part at P | full | local | tails | tails/full | local/full |
|---|---|---|---|---|---|---|
| 20 | total, max | 9.69e-5 | 5.31e-5 | 7.16e-5 | 0.738 | 0.548 |
| 20 | total, rms | 5.23e-5 | 2.21e-5 | 4.89e-5 | 0.935 | 0.422 |
| 20 | vacuum-origin, max | 7.21e-5 | 3.4e-7 | 7.21e-5 | 1.000 | 0.005 |
| 30 | total, max | 2.63e-5 | 1.19e-6 | 2.66e-5 | 1.010 | 0.045 |
| 30 | total, rms | 1.78e-5 | 6.7e-7 | 1.78e-5 | 1.000 | 0.038 |
| 30 | vacuum-origin, max | 2.73e-5 | 6.8e-9 | 2.73e-5 | 1.000 | 0.000 |

(|F(D)|/A_ref, A_ref = 0.1761; linearity residual at P <= 3.6e-9.)

- Pre-stated verdict of stage 1: cap 30 CONFIRMED; cap 20 NOT CONFIRMED (local/full 0.548 >= 0.5 at
  the P maximum). Overall, as pre-stated: NOT CONFIRMED.
- Diagnosis (same run, post hoc). The local part's value at P is end-face signal carried by the
  sharp aperture: its vacuum-origin part at P is 3.4e-7 against a total of 5.3e-5. The cap-20
  end-face signal in this cell is 2.6e-3 of A_ref, and P (x_rel 7.63-8.47 A) is dilated by 2.5 A
  towards the surface. This is the M-2 mechanism. The pre-stated criterion should have been on
  the vacuum-origin part. On that part, both caps give tails/full = 1.000 and local/full <= 0.005. Stage 2 re-tests this with the
  criterion fixed beforehand.
- The tails-only run puts the difference's peak at P (cap 20: x_rel +7.99 A, 77 % in vacuum). The
  local-only run puts it in the end face (-20.43 A).
- Scaling with the cap (descriptive). P vacuum-origin, cap 20 over cap 30: 2.64 (max) and 2.75
  (rms). End-face signal E: 77.9. Tail measures in the vacuum above the ring (x_rel 0.5-20 A, void
  slices): max |d| 1.29, rms 1.27, and Fourier components of d along x at g = 0, (0,0,4), (0,0,8):
  1.31, 1.32, 1.24. So the P value falls with the cap far more slowly than the physical end-face
  signal. But it does not follow these simple tail measures in proportion (2.6-2.8 against
  1.2-1.3). "Scales with the tail amplitude" is NOT supported quantitatively by these measures. The
  decisive result is the tails-only run reproducing P (vacuum-origin tails/full 1.000).

Stage 2 (0.09 A rule, grid 1764 x 800, dx 0.0897 A; criterion "vacuum_origin" pre-registered at
10:30, section 0; output tools/review/t4/m1_stage2_px0.09_output.txt):

| cap | part at P | full | local | tails | tails/full | local/full |
|---|---|---|---|---|---|---|
| 20 | vacuum-origin, max | 2.92e-6 | 1.1e-7 | 2.95e-6 | 1.012 | 0.039 |
| 20 | vacuum-origin, rms | - | - | - | 1.012 | 0.029 |
| 20 | total, max | 5.51e-5 | 5.48e-5 | 3.09e-6 | 0.056 | 0.995 |
| 30 | vacuum-origin, max | 3.50e-6 | 1.4e-8 | 3.49e-6 | 0.998 | 0.004 |
| 30 | vacuum-origin, rms | - | - | - | 0.997 | 0.005 |
| 30 | total, max | 3.41e-6 | 1.09e-6 | 3.53e-6 | 1.033 | 0.320 |

(A_ref = 0.1829; linearity residual at P <= 1.6e-9.) Verdict on the pre-registered criterion:
CONFIRMED for both caps, so CONFIRMED overall. The total at P for cap 20 is now almost all local,
i.e. end-face signal carried by the aperture. This is the stage-1 effect, larger here because the
numerical part shrank.

Pixel dependence, 0.09 A rule over 0.13 A rule (descriptive):
- P vacuum-origin maximum: x 0.040 (cap 20) and x 0.128 (cap 30); rms x 0.033 and x 0.090.
- End-face signal E: x 1.008 and x 0.918.
- Tail measures: max |d| x 0.578, rms |d| x 0.50, Fourier components of d at g = 0 x 0.28-0.29,
  (0,0,4) x 0.57-0.58, (0,0,8) x 0.11-0.12.
- Cap 20 over cap 30 at the finer pixel: P vacuum-origin 0.83 (max) and 1.01 (rms), against 85.6
  for the end-face signal. The artefact does not follow the cap depth.
- A_ref of the flat reference changes from 0.1761 to 0.1829. The flat reflection itself is not
  converged in the pixel (known: T3 section 7, pixel convergence NOT RUN).

Conclusion (label: CONFIRMED, in the TEST_ONLY small cell).
- The vacuum-origin difference at the ring's projection for voids 20 and 30 A deep is produced by
  the void's change of the transmission function MORE THAN 5-7 A away from the void. That change
  alone reproduces it (tails/full 0.998-1.012), and the change near the void contributes at most
  0.039 of it.
- Physically that far change is zero (sigma V <= 1.4e-6 rad at 5 A per atom). It is not
  converged in the pixel size: from dx 0.129 to 0.090 A it falls to 0.040 (cap 20) and 0.128
  (cap 30) of its value, while the physical end-face signal changes by factors of 1.008 and 0.918.
- It is therefore a numerical artefact of the non-local tails of the engine's transmission function
  (Fourier synthesis of off-grid atoms and the sharp 2/3 band limit).
- The prediction "scales with the tail amplitude" is NOT supported quantitatively by the simple tail
  measures above: the artefact falls faster than max |d| or rms |d|, and faster than the (0,0,8)
  component for cap 20. The prediction "not with the cap depth" is supported.
- Stage 1's pre-stated total criterion gave NOT CONFIRMED at cap 20 for the reason diagnosed
  above. Both stages are reported.

Application to T3's full-size runs (inference, UNVALIDATED). T3's cell has the same engine, pixel
rule (dx 0.1278 A), z geometry, beam and absorption, but a larger void (R 50 A, r 12 A) and a
wider cell. Its P values (vacuum-origin 2.03e-4 and 1.59e-4 of A_ref for caps 20 and 30, out of
totals 2.32e-4 and 1.60e-4) are therefore attributed to the same artefact. A full-size rerun (finer
pixel, or the local/tails split) was NOT RUN. The small-cell evidence was judged sufficient, so the
rerun was not indispensable. For the engine owner (A9a n-8): at T3's pixel this artefact sets a
floor of about 1e-4 to 2e-4 of A_ref on specular differences in the vacuum (T3 cell). In the small
cell it falls to about 3e-6 at dx 0.090 A.

## 3. m-1: provenance of the paired runs (tools/review/t4/flat_rerun_compare.py, output beside it)

T4 reran buried_flat_r010 once, with T3's runner and arguments unchanged (`--kind buried_flat
--absorption test_only_r0.1 --max-cpu-seconds 3600`, 2 FFT workers), from a clean clone of HEAD
dc4eb7f (manifest: commit dc4eb7f, dirty False). The compare script prints:

```
exit waves bitwise equal: True; max |psi_T3 - psi_T4| = 0.000e+00 (max |psi| 1.2415)
structure positions bitwise identical: True (1102896 atoms)
package tree of 39b6151 (T3's recorded engine commit): 520735b2... (79 files)
package tree of 4c4a78b (snapshot committing T3 + X4 edits): dd87f256... (79 files)
package tree of dc4eb7f (commit of the T4 rerun (clean clone)): 7f3b2851... (79 files)
propagation-path files changed between 4c4a78b and dc4eb7f: none
  all package files changed between 4c4a78b and dc4eb7f: ['reflection_holo/pipeline/config.py']
```

T3's flat r010 manifest records package tree e63b9a40 (commit 39b6151, dirty, diff 51b28fdb): a
working tree that was never committed. Between 4c4a78b and dc4eb7f the whole package differs only in
pipeline/config.py, which the runner does not execute. Between 39b6151 and dc4eb7f,
eight of those files changed (T3's and X4's committed edits). The bitwise-equal exit wave shows that
the code that ran for T3's flat reference computes exactly what the committed tree computes
(DERIVED_HERE). The cap runs were not rerun: for them the evidence stays A9a's (C5, C13, C14), and
the transient-edit residual A9a states for 08:24-08:55 is closed for the flat run only.

## 4. M-2: the revised analysis (tools/plots/buried_torus.py; output SP/buried_t4/figures/analysis_output.txt, copy tools/review/t4/buried_torus_analysis_output.txt)

Method (DERIVED_HERE, stated in the script's docstring). The specular selection F (T1's sharp 0.2
1/A aperture) is linear. With D = psi_cap - psi_flat, F(D) = F(D m) + F(D (1 - m)) exactly, and the
script asserts it. The mask m(x_rel) is 0 at and below the top atomic plane, rises as sin^2 to 1 at
x_rel = 2.5 A (the resolution of the selection), and is applied to D BEFORE the aperture. So
nothing from x_rel <= 0 enters the VACUUM-ORIGIN part F(D m). The END-FACE part F(D (1 - m)) holds
the end face plus the first 2.5 A above the top plane. Every value below is absolute. No detection
rule is applied, and C_up and C_y are printed as leakage references, not a noise floor. The fits and
the fitted-L table are gone. A sensitivity line gives the vacuum-origin part with a 1.0 A ramp.
All values: UNVALIDATED engine, DEMO B42, TEST_ONLY r = 0.1, this 1499 A cell. No dose model.

Vacuum side, r = 0.1 (A = A_ref = 0.1783; region V for caps 5 and 10, P for caps 20 and 30):

| cap | region | part | max\|dphi\| (rad) | max\|rho-1\| | max\|dpsi\|/A |
|---|---|---|---|---|---|
| 5 | V | total | 0.128 | 0.098 | 0.120 |
| 5 | V | vacuum-origin, 2.5 A ramp | 0.0339 | 0.0858 | 0.0848 |
| 5 | V | vacuum-origin, 1.0 A ramp | 0.0522 | 0.0987 | 0.0990 |
| 5 | V | end-face part | - | - | 0.107 |
| 10 | V | total | 6.34e-3 | 8.24e-3 | 8.09e-3 |
| 10 | V | vacuum-origin, 2.5 A ramp | 8.7e-4 | 1.78e-3 | 1.70e-3 |
| 10 | V | vacuum-origin, 1.0 A ramp | 2.71e-3 | 3.28e-3 | 3.54e-3 |
| 10 | V | end-face part | - | - | 8.52e-3 |
| 20 | P | total | 2.33e-4 | 2.12e-4 | 2.32e-4 |
| 20 | P | vacuum-origin | 2.06e-4 | 1.74e-4 | 2.03e-4 |
| 20 | P | end-face part | - | - | 4.95e-5 |
| 30 | P | total | 1.27e-4 | 1.71e-4 | 1.60e-4 |
| 30 | P | vacuum-origin | 1.23e-4 | 1.71e-4 | 1.59e-4 |
| 30 | P | end-face part | - | - | 5.6e-6 |

Statements (printed by the script's "reading" block; wording chosen so that no statement rests on a
signal threshold):
- Cap 5: in this cell the void changes the vacuum-side specular beam. The vacuum-origin part reaches
  0.034-0.052 rad in phase and 0.086-0.099 in amplitude ratio (2.5 A and 1.0 A ramps). The total over
  V (0.128 rad, 0.098) includes end-face signal carried by the aperture (end-face part up to 0.107
  of A_ref in V). Experimental detectability was not assessed (no dose model: NOT RUN). Correction to
  A9a section 3 item 1: its "0.13 rad" is the total. The phase change of vacuum origin is 0.03-0.05
  rad; the amplitude change (0.086-0.099 in ratio, against 0.098 in total) is robust to the split.
- Cap 10: NOT DEMONSTRATED in this cell. The two-beam causal vacuum layer is 0.317 A thick, below
  the 2.5 A resolution. The total over V (6.3 mrad, 0.8 %) is mostly the end-face part (8.5e-3 of
  A_ref). The vacuum-origin part is 1.7e-3 to 3.5e-3 of A_ref (ramps 2.5 and 1.0 A). It is not
  attributed: the steepest in-band systematic beam (below) could carry signal from 10 A to x_rel <=
  6.1 A, and the numerical tails of section 2 also act. The cap-10 decomposition was NOT RUN.
- Caps 20 and 30: by the two-beam characteristic (DERIVED_HERE) the (0,0,8) signal from the void
  top surfaces 1082.6 and 1623.9 A downstream, beyond the exit plane. A vacuum-side change is NOT
  DEMONSTRATED. The engine shows a vacuum difference at the ring's projection P: 2.32e-4 and
  1.60e-4 of A_ref (vacuum-origin 2.03e-4 and 1.59e-4). It is common to both caps: as complex
  fields in P, |corr| 0.942 (rms 1.007e-4 and 8.89e-5). Section 2 attributes it.
- Cap-30 location row (A9a M-1 fix 1), printed: peak x_rel +7.88 A, centroid -11.41 A, fraction in
  vacuum 0.46. The two-beam prediction for the tube centre is -32.78 A. Caps 5/10/20: peaks -7.08,
  -11.94, -21.78 A (T3's values, unchanged).
- New information (DERIVED_HERE): the engine's band (2/3 rule, dx 0.1278 A) carries the systematic
  beams up to (0,0,16), at 55.4 mrad inside the crystal (band edge 65.4 mrad). This beam is steeper
  than the two-beam characteristic (18.5 mrad), so V is not a strict causal bound of the engine.
  Along (0,0,16) the void top surfaces 90.1/180.2/360.4/540.5 A downstream (caps 5/10/20/30), which
  reaches x_rel <= 7.60/6.14/3.24/0.33 A in the exit plane. Its amplitude is not computed. P (x_rel
  7.05-9.05 A) lies beyond the cap-20 and cap-30 values: no in-band path from those voids reaches P.
- Geometric (surface-height) model, all five runs: "zero by construction of the surface-height
  model (a buried void has no surface height); not a geometric-engine run" (m-2).
- The flat reference's local 1/e lengths are kept, but labelled "a property of this finite cell,
  not an extinction length".

Figures (SP/buried_t4/figures/; T3's figures in SP/buried/figures/ are untouched):
supercell_buried_t4.png (the legend no longer names one cap), signal_maps_r010_t4.png (per cap:
total phase change, vacuum-origin phase change, and log10 of |F(D)| and |F(D m)|, with P, V, E and
C_up outlined), signal_maps_cap10_absorption_t4.png, signal_vs_cap_t4.png (absolute values, total and
vacuum-origin, no fit and no floor line), depth_profile_flat_r010_t4.png, and buried_compact.png
(15 x 7 in: the four y-sections through the ring centre on top; below them, the vacuum-origin phase
change on the vacuum side per cap, in mrad with a per-panel scale, P and V outlined, and the
classification in the title).

## 5. m-2 and m-6

- m-2: the script now prints, for each of the five runs, "zero by construction of the
  surface-height model (a buried void has no surface height); not a geometric-engine run".
- m-6: `fit_decay`, the decay fits, the fit lines of signal_vs_cap and the fitted-L table are
  removed. The flat reference's local 1/e lengths remain, labelled "a property of this finite cell,
  not an extinction length". T3's report section 4.3 still lists the fitted values (T3's report is
  not edited here); row B42 already calls them cell artefacts.

## 6. m-3: the no-feature route of the item-13 gate (reflection_holo/pipeline/config.py)

Before the fix, all three no-feature demo configurations (demo_hpc_si001, demo_smoke_si001,
demo_convergence_si001) were ACCEPTED with pattern_geometry {features: none} labelled B33, B34 or
B42 (T4 in-memory probe, reproducing A9a C15). Fix (my only hunk in config.py; X5's oxide hunks in
the same file are theirs): in the no-feature branch of `_refuse_unused_physical_inputs`, an
ASSUMPTION id on pattern_geometry whose FEATURE_STAND_IN_SUB_KIND entry is not None is refused:

```
cfg_b.pattern_geometry = {features: none} under stand-in B42: its model_assumptions row states a
buried_void, not the absence of a feature (... no feature is stand-in B27; audit A9a m-3)
```

Tests (tests/pipeline/test_pipeline_feature.py):
- test_no_feature_route_refuses_a_feature_stand_in, on demo_hpc and demo_convergence. The demo
  passes with B27, and B33, B34 and B42 are refused. When the check is removed (M6), both cases fail.
- test_no_demo_configuration_labels_no_feature_with_a_feature_stand_in: every demo_*.yaml without a
  feature declares {features: none} with B27. So no demo configuration relies on the old behaviour
  (3 found). tests/pipeline: 200 passed.

## 7. m-4, m-5 and the mutations

- m-4, tests/structure/test_buried_assertion_f_layers.py (5 tests): assert_feature_inside with
  valid buried layers (recorded counts), with a removed site in layer 3 or 0 (< 4), and with one in
  the top layer 23 or above. Disabling the buried branch (M1, A9a's M6) fails 4 of 5.
- m-5, tests/forward/test_buried_torus_analysis.py (14 tests). The script is imported with
  importlib (precedent: tests/structure/conftest.py, tests/forward/test_feature_cell_buried.py; no
  earlier test of tools/plots). The tests cover:
  - the vacuum mask and the split, which is linear, exact, and shows the A9a M-2 leakage in the
    total but exactly zero in the vacuum-origin part;
  - the region definitions against their formulas, and V empty for a deep cap;
  - vacuum_class and steepest_row_beam;
  - assert_same_cell, passing and five refusals;
  - x_centroid and cross_cap;
  - the absence of the floor rule and the fits, the reading lines, and the geometric-zero wording.
  Nothing is written to disk.
- Mutations (tools/review/t4/mutate_t4.py; scratch copies, each committed to its own scratch git
  repository; output tools/review/t4/mutate_t4_output.txt): M0 control 30 passed; M1 4 failed; M2
  (T3's script restored) 11 failed; M3 (mask after the aperture) 1 failed; M4 (sharp mask) 1
  failed; M5 (geometric wording) 1 failed; M6 (config check removed) 2 failed. All as expected.

## 8. Tests run (verbatim last lines; 10:52-10:57 UTC, load 3.55 at start, X5's suite running)

```
tests/structure: 409 passed in 30.96s
tests/forward/test_feature_cell.py tests/forward/test_feature_cell_buried.py: 20 passed in 7.73s
tests/pipeline: 200 passed in 175.76s (0:02:55)
tests/io: FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
          (AssertionError: B43) -- 1 failed, 127 passed in 1.36s
new tests (test_buried_assertion_f_layers.py, test_buried_torus_analysis.py): 19 passed in 0.61s
```

The tests/io failure is not from T4. B43 was added to reflection_holo/io/assumption_registry.yaml by
the concurrent X5 work (uncommitted), and its row is not yet in docs/model_assumptions.md; T4 did
not touch the registry. The full suite is the orchestrator's (NOT RUN by T4).

## 9. NOT RUN

- A full-size rerun of any cap run: the M-1 attribution for T3's cell is by analogy (section 2).
  The cap runs' provenance also rests on A9a's evidence (m-1 closed for the flat run only).
- The local/tails decomposition for caps 5 and 10, so the cap-10 vacuum-origin part is not
  attributed.
- A dose/noise model, so there is no statement on experimental detectability. Also holograms and
  reconstruction.
- Convergence of the flat reflection in pixel, slice, aperture and cell length (A_ref 0.1761 and
  0.1829 at the two pixel rules in the small cell). A long cell for caps >= 10.
- The amplitude of the (0,0,16) systematic-row path, and an apodised-aperture variant of the split.
- The full test suite. Archiving A9a's scratch scripts: none of their numbers is quoted from their
  output; the needed quantities are reprinted by T4's committed scripts.

## 10. Proposed row B42 and a summary for the supervisor

Proposed text for the "why" column of B42 (the first column's gate sentence becomes: "its gate
refuses B42 on the half-torus routes and, since T4 (A9a m-3), on the no-feature route"):

> A feature of known shape to test whether reflection holography sees below the surface. Report T3,
> analysis revised by T4 (audit A9a M-1, M-2, m-7). In the 1499 A demo cell (UNVALIDATED engine,
> TEST_ONLY r = 0.1):
> - Cap 5 A: the void changes the vacuum-side specular beam. The part originating in the vacuum
>   (end face masked before the aperture) reaches 0.034-0.052 rad in phase and 0.086-0.099 in
>   amplitude ratio. The total 0.128 rad includes end-face signal carried by the aperture.
>   Experimental detectability not assessed (no dose model).
> - Cap 10 A: a vacuum-side change is NOT DEMONSTRATED. The two-beam causal vacuum layer is 0.32 A,
>   below the 2.5 A resolution; the total over V (6.3 mrad, 0.8 %) is mostly end-face signal.
> - Caps 20 and 30 A: by the two-beam characteristic (DERIVED_HERE) the signal from the void top
>   surfaces 1082.6 and 1623.9 A downstream, beyond the exit plane. The engine's vacuum difference
>   at the ring's projection (2.3e-4 and 1.6e-4 of the reference amplitude, common to both caps) is
>   attributed to a numerical artefact of the non-local tails of the transmission function. This
>   is CONFIRMED in a TEST_ONLY small cell (tools/review/t4/m1_nonlocal_tail_test.py: reproduced by
>   the far change alone; it falls to 0.04-0.13 of its value from dx 0.129 to 0.090 A), with no
>   full-size rerun.
> - The fitted decay lengths of T3 section 4.3 are withdrawn (cell artefacts). The engine's band
>   also carries the steeper (0,0,16) beam, so the two-beam region is not a strict causal bound.

Supervisor summary (for Dr Arthur Blackburn; numbers from tools/review/t4/*_output.txt):

1. Demo: a ring-shaped void buried 5, 10, 20 or 30 A under flat Si(001), reflection multislice at
   200 keV, unvalidated engine, test-only absorption, 1499 A long cell.
2. A void 5 A down changes the beam leaving the surface above it: 0.03-0.05 rad in phase and
   8.6-9.9 % in amplitude, counting only what leaves through the vacuum.
3. At 10 A this cell cannot show it: the signal reaches the vacuum in a layer only 0.3 A thick at the
   exit plane, below the 2.5 A resolution.
4. At 20 and 30 A the signal would surface 1080-1620 A downstream, beyond the cell. The small
   difference above the ring (about 2e-4) is a numerical artefact (confirmed in a smaller test cell).
5. Not shown: experimental detectability (no noise or dose model), any decay length, convergence.

## 10b. Final status

FINAL. Every A9a finding assigned to T4 is addressed:
- M-1: CONFIRMED in a small TEST_ONLY cell; full-size rerun NOT RUN.
- M-2, m-2 and m-6: the analysis is revised and regenerated.
- m-1: the flat run is bitwise reproduced on dc4eb7f.
- m-3: the gate is closed and tested.
- m-4 and m-5: tests added.
- m-7: row text proposed.
Each code fix has a test that fails when the fix is reverted (section 7). Files written:
- tools/plots/buried_torus.py;
- reflection_holo/pipeline/config.py (one hunk);
- tests/structure/test_buried_assertion_f_layers.py, tests/forward/test_buried_torus_analysis.py,
  tests/pipeline/test_pipeline_feature.py (two tests added);
- tools/review/t4/ (scripts and saved outputs);
- this report.
Scratch: SP/buried_t4/ (figures/, ms_flat_r010_rerun_HEAD/, m1_px013/, m1_px009/, mut/, logs/).
Nothing is committed.
