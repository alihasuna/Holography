# A9a: audit of T3 (buried torus void in Si(001), reflection multislice demo)

Auditor A9a, 2026-09-24. Branch claude/electron-holography-orchestration-nakd7r. HEAD was 4c4a78b
when the audit started. The orchestrator committed ebb9ec7 (B42 gate, row B42) and db376ce (a
snapshot of this draft) during the audit. A9a edited only this file, committed nothing and wrote
nothing under outputs/. Scratch: SP/a9a/, with
SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad. T3's run
outputs are in SP/buried/. Every number below is printed by a command in section 0; the outputs are
the SP/a9a/*.out files. Labels: DERIVED_HERE means computed by A9a.
Status: FINAL.

## Verdict

The geometry, the builder, the depth rule F5, the cell and the section 4.1 causality numbers are
correct. They were reproduced independently, bitwise where that applies. The builder assertions
fire on corrupted structures. The B42 gate works for the half-torus routes.

Two MAJOR problems are in the reading of the multislice output, which is what the supervisor would
see:
- M-1: the cap-20 and cap-30 data contradict the report's claims "cannot reach the vacuum" and
  "cap 30 at floor". There is a small vacuum signal located at the ring's projection. Its most
  likely origin is numerical.
- M-2: the "3 x floor" detection rule is unsound. The "cap 10 marginal" claim is about half
  end-face leakage through the aperture.

Provenance of the paired runs: they are comparable with high confidence (minor m-1).

Show the results as a demo only with the wording changes in section 3.

## 0. Command log (every command A9a ran; anything not listed was NOT RUN)

- C1. `git status`, `git log`, `git show --stat b96bc6e 39b6151 4c4a78b`, `git diff 39b6151 4c4a78b
  -- reflection_holo/...` (engine.py, cell.py, overlayer.py, si001.py, registry, tests/io),
  `git diff 4c4a78b ebb9ec7 -- reflection_holo/pipeline/config.py tests/pipeline/test_pipeline_feature.py`.
- C2. Manifest provenance of the 7 runs: an inline python loop over
  SP/buried/ms_*/outputs/manifests/*.json. It reads commit, dirty, diff_head_sha256,
  untracked_sha256, package_tree.sha256 and timestamp.
- C3. `git archive <c> reflection_holo | tar -x -C SP/a9a/tree_<c>` for 39b6151, 4c4a78b, ebb9ec7 and
  HEAD, then `reflection_holo.provenance.manifest.package_tree_sha256(SP/a9a/tree_<c>)`.
- C4. `venv/bin/python SP/a9a/causality.py`, output causality.out. It recomputes the refraction law
  and the section 4.1 numbers. Physical constants are hard-coded; no repository physics is imported.
- C5. `venv/bin/python SP/a9a/geometry_check.py`, output geometry_check.out. It applies an own torus
  rule to the saved structure files (37 s).
- C6. Read the 5 PNGs and analysis_output.txt in SP/buried/figures/.
- C7. `PYTHONPATH=. venv/bin/python SP/a9a/leakage_split.py`, output leakage_split.out and .json. It
  uses T3's own regions and aperture, imported unchanged, and splits the difference linearly into
  its in-crystal and vacuum parts.
- C8. `PYTHONPATH=. venv/bin/python SP/a9a/p_signal_origin.py`, output p_signal_origin.out.
- C9. `PYTHONPATH=. venv/bin/python SP/a9a/gibbs_tail.py`, output gibbs_tail.out. It uses a small
  TEST_ONLY cell and computes the transmission function of one slice. The first attempt was
  refused by reflection_setup ("buildup_depth_A = 1.0 A outside the 20 to 100 A range"). The script
  was then changed to build the grid with grid.make_grid, as engine.py:217 does. No propagation.
- C10. `PYTHONPATH=. venv/bin/python SP/a9a/single_atom_tail.py {0.0,0.5,0.3}`, output
  single_atom_tail.out. It computes the engine's projected potential of one Si atom on T3's grid.
- C11. `venv/bin/python SP/a9a/mutate_t3.py`, output mutate_t3.out: a control and 15 mutations,
  each on a scratch copy of the repository, never the repository itself.
- C12. `PYTHONPATH=. venv/bin/python SP/a9a/corrupt_saved.py`, output corrupt_saved.out. It calls
  T3's assertion functions on corrupted versions of the saved full-size cap-5 structure and of
  the run's cell record.
- C13. Inline python diff of the exit-wave metadata_json of all runs against buried_flat_r010,
  output ew_metadata_diff.out.
- C14. `PYTHONPATH=SP/a9a/tree_{4c4a78b,39b6151} venv/bin/python SP/a9a/engine_identity.py`, then a
  bitwise comparison; output engine_identity.out. One small flat cell (82 800 atoms, 1124
  slices, 35 s each, 1 thread).
- C15. `PYTHONPATH=. venv/bin/python SP/a9a/gate_probe.py` plus an inline comparison-purpose
  probe, output gate_probe.out. Configurations are read, copied in memory, never written.
- C16. `PYTHONPATH=. venv/bin/python SP/a9a/mem_scaling.py {46,92,138}`, output mem_scaling.out.
  Flat builder, depth 74, 27 x pz periods; 3.6-10.0 s each.
- C17. Inline python over the run summaries: bond histograms, (d) deviations, engine geometry
  records.
- C18. Code reading with grep/sed/Read: shapes.py, features.py, feature_cell.py, forward/cell.py,
  run_torus_multislice.py, buried_torus.py, engine.py (propagate_slices, simulate),
  potentials.py (projected), manifest.py, pipeline/config.py, pipeline/engines.py, io/labels.py,
  the registry, docs/model_assumptions.md row B42, and P2 lines 146, 211, 447, 901-903.

NOT RUN:
- Any full-size multislice run. This includes a rerun of buried_flat_r010 to close m-1, and a
  finer-pixel or apodised-potential rerun to confirm the mechanism behind M-1.
- A dose or noise model.
- The full pytest suite (the orchestrator is running it concurrently). The T3 test files and the
  orchestrator's B42 test did run, unmutated, as the C11 control: 34 passed.

## 1. Findings, ranked

### M-1 (MAJOR): the cap-20/30 vacuum data contradict the report; the cap-30 location row misreports the script output

**What is wrong.** T3 report lines 176 and 218, and the summary in row B42, say:
- cap 30 location: "at floor | - | -32.78 A | -";
- "Caps 20 and 30: V is empty. Their signal cannot reach the vacuum in this cell";
- "P detects nothing by phase or ratio at any cap (<= 2.6 x; 3.5 x at the 1.7e-4 level for cap 30)".

The script T3 cites printed, for cap 30 (analysis_output.txt, printed at buried_torus.py:569):
`"peak_x_rel_A": 7.876517346938769, "centroid_x_rel_A": -11.408001737834768,
"fraction_in_vacuum": 0.45807984822525477`. The peak of the y-integrated difference is in the
vacuum, inside P (x_rel 7.05-9.05 A), and 46 % of it lies at x_rel > 0. The cap-30 phase and ratio
maps in signal_maps_r010.png show a ring-shaped pattern inside the blue P outline.

By T3's own rule, P "detects" cap 30 in max|rho-1|: 3.5 x floor. The decay fit prints
`caps used [30.0]` for that metric. So "V is empty" is true only because V is defined from the
two-beam characteristic (buried_torus.py:207-208). It is not a measurement.

**What the signal is (C7, C8).** The specular-filtered difference F(D) was split linearly at
x_rel = 0:
- In P, the part carried out of the crystal is 5.5e-6 of the 1.6e-4 max for cap 30, and 4.8e-5 of
  2.3e-4 for cap 20. The signal therefore originates in the vacuum part of the exit plane.
- It peaks at P. For cap 30 the max over the ring's y band is 8.3e-5 at 0.5-3 A, 1.6e-4 at 7.05-9.05
  A, 5.3e-5 at 11-13 A and 2.0e-5 in C_up.
- It is almost the same complex field for caps 20 and 30: `caps 20 vs 30, P: rms 1.007e-04 vs
  8.887e-05; |corr| 0.942`. A signal that surfaces along the Bragg characteristic cannot do this:
  the end-face signal E falls 60-fold from cap 20 to cap 30.

**Probable mechanism (DERIVED_HERE, C9 and C10; consistent, not proven).**
potentials.py:316-339 synthesises each slice's projected potential in Fourier space up to the grid
Nyquist frequency. engine.py:199-200 then truncates t at the 2/3 band limit. An atom off the pixel
grid therefore has a non-local tail on T3's grid:

```
atom offset 0.5 pixel ... distance 10.0 A: |V|/peak along x 1.09e-03 ... distance 30.0 A: |V|/peak along x 3.66e-04 ...; |exp(i sigma V) - 1| along x 1.34e-04
```

In a small TEST_ONLY cell, removing the tube atoms 30 A below the surface changes the
un-band-limited transmission function in the vacuum above it by up to 1.5e-4 (0.5-3 A); at cap 20
the change is 2.4e-4 (gibbs_tail.out). Without the numerical tails this change is exactly 0. The
change sits at the same z as the void, so the reflected wave carries it to the geometric
projection P. The cap-20/cap-30 ratio of the small-cell tail (1.6) matches the observed P ratio
(max 1.45). The cap-20/30 vacuum signal is therefore most likely a numerical floor of the engine
at about 1-2e-4 A_ref, located at the projection. It is neither physics nor "at floor".

**Why it matters.**
- The report presents a two-beam argument (section 4.1) as a fact about the engine ("cannot
  reach the vacuum"). The engine shows a vacuum difference at the ring's projection for a void
  30-54 A deep.
- A supervisor shown the cap-30 map without this explanation could read it as "reflection
  holography sees 30 A deep". The report's own table hides the effect.
- The same numerical tails bound any 1e-4-level difference measurement with this engine
  (note n-8).

**Reproduction.** Commands C7, C8, C9 and C10; the outputs are quoted above.

**Fix.**
1. Report the printed cap-30 location (peak +7.88 A, 46 % in vacuum).
2. Call the section 4.1 bounds "two-beam characteristic (DERIVED_HERE)".
3. State that the engine shows a P-located vacuum difference of 1.6-2.3e-4 A_ref at caps 20 and
   30, common to both caps, and attributed provisionally to the Fourier-synthesis tails of the
   potential. Mark it UNVALIDATED until a finer-pixel or apodised-potential rerun (NOT RUN)
   confirms it.
4. Do not call cap 30 "at floor".

### M-2 (MAJOR): "3 x floor" is not a detection criterion; "cap 10 marginal" is not supported as a vacuum detection

**What is wrong.**
- The floor is the larger control of the same run (buried_torus.py:33-35, 584-585, 602-603).
  T3 says the controls "hold leakage of the Fourier aperture and of the band-limited propagation,
  and it scales with the signal" (report line 211). A value divided by its own leakage is not a
  detection statistic.
- The controls are not free of the void. At cap 10, 94 % of the C_up max (9.5e-4 of 1.0e-3) and
  all of the C_y max (7.45e-4 of 7.35e-4) come from the in-crystal (end-face) part of the
  difference, split at x_rel = 0 (C7).
- The rule is not monotonic in depth: P "detects" cap 30 (3.5 x) but not caps 5, 10 or 20
  (report table, line 200).
- Cap 10's V region is almost entirely dilation. The causal vacuum thickness is x_V = 0.317 A,
  about 2.5 pixel rows. V extends to 2.82 A, so about 89 % of V is the 2.5 A dilation beside the
  surface, next to the strong end-face band E.
- C7 split at x_rel = 0: `V ... total_max 0.008095, from_crystal_max 0.009117, from_rest_max
  0.004969, total_rms 0.003501, from_crystal_rms 0.002790, from_rest_rms 0.001932`. About half of
  cap 10's "vacuum" value is end-face signal carried through the sharp aperture.
- The absolute values (max phase 6.3 mrad, 0.8 % amplitude) are far below any holographic phase
  sensitivity; the dose model is NOT RUN.
- For comparison, cap 5 passes the same split: the vacuum part dominates V (rms 4.4e-2 of
  4.8e-2), so "cap 5 visible in the vacuum in this simulation" is supported.

**Why it matters.** Row B42 and the report summary say "reaches the vacuum only for the 5 A cap
(the 10 A cap marginally)". The cap-10 part is not supported, and "detected" suggests
experimental detectability, which was not assessed.

**Reproduction.** Command C7; the output is quoted above. T3's own table (report lines 190-194)
shows C_up and C_y rising with the signal.

**Fix.**
1. Drop "detected/marginal" based on x floor.
2. Report absolute values and the vacuum-origin part: mask D to x_rel >= 0 with an apodised edge
   before the aperture, or use an apodised aperture.
3. State cap 10 as "not demonstrated in this cell".
4. State that experimental detectability needs the dose model (NOT RUN).
5. Methodological, also for T1's tools/plots/torus_atomistic.py: the specular selection of the
   whole exit plane mixes in the end face. The aperture should act on the vacuum part only.

### m-1 (minor): provenance of the paired runs. Comparable, but the record and the argument are wrong

**Package-tree hashes (C2, C3).**

| run | recorded (end of run) | at start (inferred) |
|---|---|---|
| flat r010, cap 5 r010 | e63b9a40 | unrecorded (08:23:57-59) |
| cap 10 r010, cap 20 r010 | 5dbde117 | e63b9a40 (started 08:32:22/29, when both earlier manifests were written) |
| cap 30 r010, flat r000 | 5dbde117 | 5dbde117 (08:43:12/14) |
| cap 10 r000 | dd87f256 (= 4c4a78b, C3) | 5dbde117 (08:55:22) |

simulate() computes git_state and the package tree after the propagation (engine.py:405, then
:421-440; manifest.py:214-221). So each manifest records the tree at the END of the run, not the
code that ran. With agents editing concurrently, the manifests of caps 10 and 20 r010 and of
cap 10 r000 record trees that did not run.

**T3's argument.** "Far from the void, cap 30 and its flat reference agree to 2e-5 of A_ref (C_up)"
(report line 142). This is not evidence: C_up contains void leakage by T3's own statement, and
2e-5 is the order of the cap-30 signal.

**What could differ.**
- Between 39b6151 and 4c4a78b, no file on the propagation path changed. engine.py changed the
  memory model only; cell.py and si001.py changed only oxide functions, which are not executed for
  a non-oxide cell; overlayer.py changed its docstring only. T3's structure code is checked
  through its outputs (C5).
- The two flat structures are bitwise identical (C5).
- The exit-wave metadata of each pair differ only in atoms, timing and absorption (C13).
- A small flat cell run with both package trees gives bitwise identical exit waves: `bitwise
  equal: True max |diff| 0.0` (C14).

**Conclusion.** Paired runs are comparable with high confidence. The residual risk is transient,
later-reverted edits of the propagation path between 08:24 and 08:55, which the record cannot
exclude.

**Fix.**
1. Replace the report's argument with the evidence above.
2. List the package-tree hashes per run.
3. Optionally close the residual with one rerun of buried_flat_r010 (about 500 s) and a bitwise
   comparison (NOT RUN).
4. For the engine owner: take the repository record at the start of simulate(), or record both.

### m-2 (minor): section 4.5 "printed for all 5 runs" is not a geometric-engine run

buried_torus.py:637-646 evaluates BuriedTorus.layer_height_A. That function is identically 0 by
construction (shapes.py:173-181). The script then passes 0 to geometric_step_phase. The zero
prediction is correct as a consequence of the model's definition: the height-field engine uses only
height_fn (pipeline/engines.py:159-187). But it is a tautology, not an engine run.

No pipeline path can run the geometric engine on a buried void:
- config.py:222 allows only trench and ridge;
- engines.feature_shape (engines.py:146-156) builds a HalfTorus only.

**Fix.** Wording: "zero by construction of the geometric model (DERIVED_HERE); not run".

### m-3 (minor): the gate still accepts B42 on the no-feature route

The half-torus routes are closed (C15, all REFUSED):
- B42 on a trench or ridge;
- sub_kind buried_void;
- B42 on pattern_geometry only;
- purpose comparison.

The route that remains open: a staircase configuration's `cfg_b.pattern_geometry {features: none}`
labelled ASSUMPTION B42 is ACCEPTED, and the configuration records B42 as the item-13 stand-in:
`staircase + B42 (demo): accepted; recorded item-13 stand-in: [('pattern_geometry', 'B42')]`. The
same holds for B33, a gap that predates T3. config.py:940-946 checks only the value; the stand-in
check at :1308-1314 runs only when a feature is present.

This does not present a buried void as measurable: no void is simulated, and purpose comparison
refuses it (demo_only). It does mislabel a run.

**Fix.** In the no-feature branch, refuse an ASSUMPTION id whose FEATURE_STAND_IN_SUB_KIND entry
is not None; add a test.

### m-4 (minor): the buried branch of assertion (f) is untested

With features.py:413-417 disabled (mutation M6), all 19 structure tests pass. The "too thin"
test (test_features_buried.py:330-331) exercises the builder pre-check (features.py:793-800), not
(f). Every other T3 check is caught when disabled (C11): (h), (i) both parts, (c), (e), (d), F5,
the absorber refusal, and F5 not being called. The a/8 geometry shifts and the inclusive boundary
are also caught, as is the removal of the B42 gate entry.

**Fix.** A test that calls assert_feature_inside with removed sites in layer < 4 or in the top
layer.

### m-5 (minor): the analysis script has no tests

Nothing in tests/ imports tools/plots/buried_torus.py. That leaves untested: the region
definitions, assert_same_cell (the flat = cap + void check), fit_decay and x_centroid.

### m-6 (minor): the fitted decay lengths should not be shown as quantities

Section 4.3 states that the L values are "NOT an extinction measurement". That is adequate, but the
table still prints them with +- errors, and the fits have further problems:
- The fits use nominal caps. The first removed layer lies at 5.43, 10.86, 20.37 and 31.23 A below
  the top plane (C5), 0.4-1.2 A deeper than nominal; with L of 2-4 A, that is a 10-30 % effect
  per point.
- The E max|rho-1| fit spans a non-monotonic pair (pairwise L = -88.96 A for caps 5 to 10).
- The two V points use regions of different size (55 832 and 21 934 pixels).
- E at cap 30 uses 22 940 of 244 265 pixels (5 % mask).

**Fix.** Remove the table from the supervisor version, or label it "cell artefact, not a
physical length".

### m-7 (minor): row B42 inherits M-1 and M-2

docs/model_assumptions.md:68, "why" column. "(the 10 A cap marginally)" is not supported (M-2).
"the rest leaves through the end face" omits the numerical vacuum difference at P (M-1). The
surfacing distances 271/541/1083/1624 A match the script (270.65, 541.30, 1082.60, 1623.90), but
they are two-beam values and need a DERIVED_HERE, two-beam qualifier.

The rest of the row is correct: the geometry (C5), the label ASSUMPTION, demo_only (registry), and
"otherwise as B33". The phrase "its gate refuses B42 on a half-torus configuration" is true but
incomplete (m-3).

### Notes

- n-1: Section 7's HPC arithmetic is confirmed.
  - 2 x 27 x 1100 x 74 = 4.40 M atoms for 5970 A (2 x 2923 + 124).
  - The builder's peak RSS is linear: 473, 910 and 1349 MB at 183 816, 367 632 and 551 448 atoms,
    a slope of 2.38 MiB per 1000 atoms with the intercept at the import baseline (C16). That
    extrapolates to about 10.3 GiB, which is "about 10 GB".
  - But ~6000 A is what the void BOTTOM needs at cap 30. For cap 10 the full void needs about
    2 x 1840 + 124 = 3.8 kA; for cap 20, 2 x 2382 + 124 = 4.9 kA (C4). "caps >= 10 A need ~6000
    A" overstates caps 10 and 20.
- n-2: The reciprocity statement is correct for a converged semi-infinite crystal in first-order
  DWBA. The change of the reflected amplitude is the overlap of the incident and the time-reversed
  outgoing Bragg fields, each with envelope exp(-t/Lambda), so L = Lambda/2 = 12.23 A. It is
  psi^2, not |psi|^2; "INTENSITY depth" is loose, but the envelope is the same. P2's own converged
  1-D check supports it (P2 lines 901-902: |R_D - R_inf| follows exp(-2D/24.47 A) at D = 100 and
  200 A). It is not first order for the 5 A cap.
- n-3: C_y is the 12.6 A strip |y - y_c| >= 67 A of a periodic 146.63 A cell, 5 A from the ring's
  lateral edge. P and V overlap for cap 5 (P 4.55-11.55 A, V 0-7.18 A); T3 notes this.
- n-4: The illumination reach (16.7-19.0 A) starts from the beam's zero-amplitude bottom edge (first
  contact 62.0 A). From the full-amplitude edge (185.9 A) it is 14.4-16.7 A (C4). Both are
  two-beam values.
- n-5: The in-builder checks (a), (b) and (h) use the same BuriedTorus.contains as the
  construction, so (b)'s "independent enumeration" is independent of the chunking only. The
  geometric anchor is the test's brute-force rule (test_features_buried.py:89-113) and its
  hard-coded numbers (:130-145); mutations M10-M12 confirm both are effective. C5 confirms the
  saved runs.
- n-6: In supercell_buried.png the legend reads "void top (cap 5 A)" for all four rows.
- n-7: The runner's feature label is a bare "ASSUMPTION"; "B42" appears only in the source text
  (the same convention as T1; io/labels.py:44-46 accepts it). The registry gates the pipeline, not
  the runner.
- n-8: For the engine owner, outside T3's code. Off-grid atoms have Fourier tails decaying as 1/r:
  |V|/peak 1.1e-3 at 10 A and 3.7e-4 at 30 A (C10). This limits every difference measurement at
  the 1e-4 level, for example the step-phase null tests.

## 2. Item-by-item record

1. **Geometry: verified (C5).** Removed sites equal, bitwise, the flat sites within 12 A of the
   circle rho = 50 A, x_rel = -(cap + 12). x_rel is measured from the TOP atomic plane (x =
   99.113925 A), not the equivalent boundary.
   - No removed site lies at x_rel >= -cap.
   - All 4/8/15/23 cap layers are complete.
   - Every atom of the cap runs is a bitwise row of the flat structure. flat r010 == flat r000.
   - No site lies within 1e-6 A of the wall; the smallest margin is 3.0e-5 A.
   - Counts 7166/7083/7123/7031; deviations +68/-15/+25/-67 against the tolerance 803.1; clearances
     and bond histograms match report section 2 (C17).
   - The analysis's own check (buried_torus.py:145-153) is confirmed.
2. **Assertions fire.**
   - On T3's saved full-size cap-5 structure (C12), each corruption fires the named check: (h), (i)
     cap atom, (i) removed site in the cap, (d), (e), F5 on the surface rule, F5 on the void rule.
   - The uncorrupted data pass.
   - The tests fail when each check is removed (C11), except for (f)'s buried branch (m-4).
3. **Causality numbers: reproduced (C4).** From k cos(theta_ext) = k_in cos(theta_int), relativistic
   k, 2 k_in sin(theta_int) = 8/a, V0 = 13.903 V: theta_int 18.4719 mrad, theta_ext 16.1347 mrad,
   1/tan 54.130. Surfacing distances 270.65/541.30/1082.60/1623.90 A; crystal after the ring
   436.93-560.93 A; depth reaching the vacuum 8.072-10.363 A; illumination reach 16.685-18.976 A and
   27.048 A; P 7.050-9.051 A; tan ratio 0.8735. These are two-beam values; see M-1 for the engine.
4. **Regions.**
   - P, V, E, C_up and C_y are coded as documented (buried_torus.py:194-226). V uses
     z_min = z_c - R - r, a conservative choice (+0.19 A).
   - The controls are not free of the void (M-2, n-3).
   - The 3 x floor rule is unsound (M-2).
   - "Cap 5 detected": supported as visible in this simulation. "Cap 10 marginal": not supported.
     "Caps 20/30 cannot reach the vacuum": true in the two-beam sense only (M-1).
5. **Decay section.** The physics is right (n-2). The artefact caveat is adequate in the text, but
   the fitted-L table should not be shown (m-6).
6. **Provenance.** m-1.
7. **Geometric zero.** Correct by construction but not a run (m-2). No pipeline path presents a
   buried void as measurable (C15, m-2).
8. **Gate.**
   - B42 is refused on every half-torus route, including purpose comparison.
   - The orchestrator's test fails when the gate entry is removed (M14).
   - The buried-void sub_kind is refused at schema level.
   - Remaining gap: the no-feature route (m-3).
   - No path turns a B42 run into a comparison run: the T3 outputs live in scratch, the HPC kit's
     TORUS_KINDS was not extended, and demo_only is enforced.
9. **Row B42.** m-7.
10. **HPC.** n-1.

## 3. Wording changes needed before showing T3 to the supervisor

1. **Cap 5.** "In this 1499 A simulation cell the void changes the vacuum-side specular beam by up
   to 0.13 rad and 10 % in amplitude. Experimental detectability was not assessed (no dose model)."
2. **Cap 10.** "Not demonstrated: the vacuum-side change (6 mrad, 0.8 %) is about half end-face
   leakage through the aperture." Delete "marginal".
3. **Caps 20/30.**
   - "By the two-beam characteristic, no signal can surface before the exit plane."
   - "The engine shows a 1.6-2.3e-4 A_ref difference at the ring's projection, common to both caps
     and most likely a numerical artefact of the atomic potential's Fourier tails (UNVALIDATED)."
   - Correct the cap-30 location row.
4. Remove "x floor" detection wording and the fitted-L table from the supervisor version.
5. Section 4.5: "zero by construction of the surface-height model; not a geometric-engine run".
6. Section 3 caveat: replace the C_up argument with m-1's evidence and list the package-tree
   hashes.
7. Section 7: "~6 kA for the 30 A cap's full void (about 3.8 kA for cap 10)".
8. Row B42: the corrections of m-7.
