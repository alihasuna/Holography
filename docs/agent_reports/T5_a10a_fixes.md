# T5: fixes of re-audit A10a (T4's buried-torus analysis)

Agent T5, 2026-09-24. Branch claude/electron-holography-orchestration-nakd7r, HEAD 8d277e1 at start.
Nothing committed by this agent. Scratch: SP/buried_t5/ with
SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
No multislice run: every number comes from T3's saved exit waves SP/buried/ms_*/. Beam energy 200
keV (asserted from every exit-wave file). Status: FINAL (section 10).

"OUT:n" below means line n of tools/review/t5/buried_torus_analysis_output.txt, the committed copy
of SP/buried_t5/figures/analysis_output.txt.

## 0. Log (UTC)

- Read in full: docs/agent_reports/A10a_T4_reaudit.md, T4_a9a_fixes.md, tools/plots/buried_torus.py,
  tests/forward/test_buried_torus_analysis.py, SP/a10a/split_family.{py,out},
  SP/a10a/mutate_a10a.{sh,out}, SP/a10a/kirkland_range.out, tools/review/t4/mutate_t4.py and outputs.
- 11:25: baseline of the four named test files before any change: `52 passed in 10.37s`.
- 11:27: probe (SP/buried_t5/probe.py, scratch only; none of its numbers is quoted) of the raw
  vacuum-side difference. It guided the wording; the quoted numbers come from the committed script.
- 11:30-11:40: tools/plots/buried_torus.py revised (fixes 1, 2, 4). Dev run on T3's exit waves into
  SP/buried_t5/figures_dev/ (47 s, rc 0). The family values agree with A10a's independent R4 table
  to all printed digits.
- 11:38-11:42: tests written (fix 3), 27 passed.
- 11:42:06-11:42:55: FINAL run, `OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python
  tools/plots/buried_torus.py --runs SP/buried --out SP/buried_t5/figures` (rc 0). Output copied to
  tools/review/t5/buried_torus_analysis_output.txt (330 lines). Second run into
  SP/buried_t5/figures_rerun: `identical apart from the figure directory`, and buried_compact.png is
  byte-identical.
- 11:44:06-11:44:59: mutations, tools/review/t5/mutate_t5.py, output
  tools/review/t5/mutate_t5_output.txt: all 16 as expected. Then T4's analysis-script mutations
  M2-M5 were rerun on the revised script (tools/review/t5/mutate_t4_rerun_output.txt): all 4 still
  fail, as expected.
- 11:45: the four named test files (section 7).
- Working tree: while T5 worked, other agents left uncommitted edits in reflection_holo/forward/cell.py,
  reflection_holo/pipeline/config.py, reflection_holo/structure/oxide.py and oxide tests, plus
  tools/review/x6/. The orchestrator also committed snapshot cff596d of this report. T5 did not
  touch any of these files. T5's files are tools/plots/buried_torus.py,
  tests/forward/test_buried_torus_analysis.py, tools/review/t5/ and this report. The mutation copies
  and the test runs include the other agents' edits, as found at 11:44-11:45.

## 1. Fixes at a glance

| finding | fix (tools/plots/buried_torus.py) | test that fails when it is reverted (mutate_t5_output.txt) |
|---|---|---|
| A10a-M1 | `mask_family(a)` (A10a's nine masks; a/8 and a/4 use a from the structure file). `family_mask` refuses start < 0. `family_metrics` gives, per member, V (or P) metrics, P, peak and centroid. It also gives the min-max range, the total over V, the raw first-layer fraction and V's source points (family block OUT:212-270). The cap-5 reading quotes the range, gives the reason and does not claim robustness (OUT:317). | M1a (family reduced to the main mask): 3 fail. M1b (start < 0 admitted): 1 fails. M1c (every member uses the main mask): 1 fails. M1d (raw fraction of a wrong layer): 1 fails. A5 (reading quotes the total): 1 fails. |
| A10a-m2 | `causal_paths`: two-beam, (0,0,16) and band edge; surfacing distance; reach at theta_out and at the aperture's steepest accepted angle. The band edge is read from the exit-wave metadata and asserted equal to 1/(3 dx) (2/3 rule). `band_edge_vs_P` words the comparison from the numbers. M1_ATTRIBUTION is reworded (below). The phrase "outside every in-band causal path" is removed. | M2a (band edge = row angle): 2 fail. M2b (aperture angle = theta_out): 2 fail. M2c (metadata not asserted): 1 fails. M2d (P called beyond on the specular angle only): 1 fails. M2e (old "CONFIRMED there" wording): 1 fails. A6 (V16 at the two-beam angle): 1 fails. |
| A10a-m3 | `analyse` split into loading plus `analyse_pair`; `reading_for` is the wiring main() uses | A4 (vacuum-origin metrics from the total): 2 fail. A5, A6: above. |
| A10a-m4 | `compact_panel_info` and `_compact_bottom`: log10 \|F(D m)\|/A_ref on ONE shared range with one colour bar; plain titles, N printed (OUT:324-328) | M4a (per-panel scale): 1 fails. M4b (deep-cap title without "by analogy" and N): 1 fails. |
| m-1 / M-2 wording | M1_ATTRIBUTION carries "BY ANALOGY, UNVALIDATED in this cell; CONFIRMED in a TEST_ONLY small cell on a criterion set after a first stage whose pre-stated criterion gave NOT CONFIRMED (aperture leakage)" | M2e |

Control T0 (no change; all four named files): `65 passed in 11.45s`.

## 2. A10a-M1: the cap-5 vacuum-origin part over the mask family

- Every member is 0 at and below the top atomic plane. The members are:
  - the sharp step at 0;
  - sin^2 ramps 0-1.0, 0-2.5 (main), 0-5.0, 1.0-2.0 and 2.5-5.0 A;
  - the sharp step at a/8 = 0.679 A;
  - ramps 0.679-3.179 and 1.358-3.858 A.

  Rows at OUT:214-222.
- Cap 5, region V, RANGE (OUT:223): max|dphi| 0.02736-0.0789 rad; max|rho-1| 0.02602-0.1033
  (2.6-10.3 %); max|dpsi|/A_ref 0.03036-0.1053. TOTAL over V (OUT:224): 0.1283 rad, 0.09808 (9.81 %),
  0.1201.
- Reason, printed (OUT:225-226):
  - 0.521 of the raw vacuum-side |D|^2 (0 < x_rel <= 25 A, ring's y band) lies at
    0 < x_rel <= 2.5 A;
  - the main mask's |F(D m)| peaks at x_rel +2.64 A, centroid +0.32 A.
- V's surface source points are z_s 1085.5-1521.2 A; the void spans z 965.2-1089.2 A (OUT:227). The
  reading line gives "0.99 of V's z_s range lies downstream of the void's downstream end" (OUT:317).
  This answers A10a-M2 item 2 ("above it").
- Cap 10, RANGE (OUT:238): max|dpsi|/A_ref 0.0001696-0.004969 (0.017-0.497 %), max|dphi|
  0.0001304-0.005441 rad; total (OUT:239) 0.006337 rad.
- Caps 20/30: the family changes P little: max|dpsi|/A_ref 0.0002025-0.0002097 and
  0.0001584-0.0001637 (OUT:253, 267). This confirms A10a n-7.
- T4's separate "1.0 A ramp" sensitivity line is removed. That ramp is member 2 of the family.

## 3. A10a-m2: causal paths and wording

- Internal angles (OUT:273): two-beam 18.47, (0,0,16) 55.44, band edge 65.45 mrad (f_x,max
  2.6077 1/A from the metadata). The aperture accepts exit angles 16.13-21.15 mrad.
- Region P spans x_rel 4.68-11.46 A; the ring's projection is 7.05-9.05 A (OUT:274).

The band-edge path, recomputed (not copied from A10a); it agrees with A10a R4:

| cap | surfaces downstream | reach at theta_out | reach at 21.15 mrad | line |
|---|---|---|---|---|
| 5 | 76.3 A | +7.82 A | +10.25 A | OUT:277 |
| 10 | 152.6 A | +6.59 A | +8.64 A | OUT:280 |
| 20 | 305.2 A | +4.13 A | +5.41 A | OUT:283 |
| 30 | 457.7 A | +1.67 A | +2.18 A | OUT:286 |

The two-beam and (0,0,16) values are printed beside it (OUT:275-285). Readings:
- Cap 10 (OUT:318): "That layer is not a bound of the engine" plus the band-edge reach, and
  "mostly end-face signal in amplitude". In phase the vacuum-origin part reaches up to 0.86 of the
  total (A10a n-4).
- Cap 20 (OUT:319): the reach stays below P at the specular angle. At the aperture's steepest angle
  it enters P but stays below the ring's undilated projection.
- Cap 30 (OUT:320): "both reaches lie below region P".
- Both deep caps: the point-spread-function caveat and the full attribution history.
- OUT:210 adds the imperfect analogy: cap-20/cap-30 ratio of P vacuum-origin 1.278 here, against
  2.637 in the small cell (m1_stage1_px0.13_output.txt:44).

vacuum_class is kept on the two-beam layer. With the band edge it would call caps 10 and 20 "shown"
(reach 6.59 and 4.13 A >= 2.5 A). A reach bounds where signal could go; it demonstrates nothing, and
A10a keeps cap 10 NOT DEMONSTRATED.

## 4. A10a-m3: tests (tests/forward/test_buried_torus_analysis.py, 14 -> 27 tests)

New tests:
- the mask family and its refusals;
- the causal paths against their formulas, and against A10a's independent values on T3's geometry;
- band_edge_vs_P (three branches);
- the raw-fraction known answer, and x_centroid of a zero profile;
- geometry reading and asserting the metadata band edge.

Synthetic pairs through `analyse_pair`, on a TEST_ONLY grid where the flat wave sits on an FFT bin:
- END-FACE-ONLY: the total over V > 1e-2 (leakage). The vacuum-origin |dpsi| and |rho-1| are exactly
  0 for the main mask and all nine members. The phase is <= 1e-15 rad: arg(pf conj(pf)) of an
  unchanged wave came out at 2.75e-17, the rounding of the complex product.
- VACUUM-ONLY: vacuum-origin = total, end-face part exactly 0. Known answer 0.05 and atan(0.05) to
  1 %; peak at x_rel 10-14 A.
- MIXED: the main member equals metrics_vac, and the range is the min/max of the rows. The cap-5 line
  from `reading_for` quotes the range before the total, with "not a bound" and "depends on how that
  layer is assigned", and not "robust".

Plus: deep and cap-10 readings (band-edge numbers, the attribution phrase, no "outside every
in-band causal path"); compact_panel_info and the shared clim.

T4's `test_reading_lines`: its seven assertions are unchanged. Its three calls now pass the inputs
the revised `reading_line` requires: `family=`, a geom from regions() and, for cap 5, `loc_vac` and
`raw_frac_first_res`. A missing family raises ValueError, and that is tested.

A10a's survivors now fail (mutate_t5_output.txt):
- A4 `2 failed, 25 passed`;
- A5 `1 failed, 26 passed`;
- A6 `1 failed, 26 passed`.

A4 and A6 use A10a's literal strings. A10a's literal A5 pattern no longer exists, because the line
was rewritten; the mutation applies the same fault to the new line (the total's phase quoted as the
vacuum-origin phase).

## 5. A10a-m4: buried_compact.png (SP/buried_t5/figures/)

- Top row: supercell sections (unchanged).
- Bottom row: log10 |F(D m)|/A_ref (main mask), x_rel 0-20 A, ONE range [-5, -1] and one colour bar.
- Titles (OUT:325-328):
  - "cap 5 A: 0.03-0.08 rad in phase, 3-10 % in amplitude (vacuum part; the range comes from how the
    first 2.5 A above the surface is counted)";
  - "cap 10 A: not demonstrated in this cell";
  - caps 20/30: "numerical artefact by analogy (about 1/420 | 1/530 of the cap-5 level)".
- N is printed (OUT:324): 417.1 and 533.1 (panel maxima 2.033e-04 and 1.591e-04 against 8.480e-02).

Other figures: same content as T4, renamed *_t5.png. Only buried_compact.png was inspected visually.

## 6. Outputs

- tools/review/t5/buried_torus_analysis_output.txt (sha256 5d5beaed...);
- tools/review/t5/mutate_t5.py and mutate_t5_output.txt;
- tools/review/t5/mutate_t4_rerun_output.txt;
- figures in SP/buried_t5/figures/: buried_compact.png, supercell_buried_t5.png,
  signal_maps_r010_t5.png, signal_maps_cap10_absorption_t5.png, signal_vs_cap_t5.png and
  depth_profile_flat_r010_t5.png.

T3's figures (SP/buried/figures) and T4's (SP/buried_t4/figures) are untouched.

## 7. Tests run (11:45 UTC, verbatim last lines, OMP_NUM_THREADS=1)

```
all four together: 65 passed in 11.17s
tests/forward/test_buried_torus_analysis.py: 27 passed in 1.15s
tests/structure/test_buried_assertion_f_layers.py: 5 passed in 0.02s
tests/structure/test_features_buried.py: 19 passed in 4.07s
tests/forward/test_feature_cell_buried.py: 14 passed in 5.33s
```

## 8. NOT RUN

- Any multislice run: none was needed, and there was no full-size rerun or finer-pixel run of T3's
  cell.
- The local/tails decomposition for caps 5 and 10 (cap 10 stays unattributed), and for T3's caps
  20/30 (the attribution stays by analogy).
- A dose model; convergence in pixel, slice, aperture and cell length; holograms.
- The apodised-aperture variant inside the committed script: A10a ran it in scratch; it was not
  added here.
- The full pytest suite; tests/pipeline; T4's M0/M1/M6 mutations.
- Edits to docs/model_assumptions.md row B42, T4's report or docs/: not permitted. The proposed text
  is in section 9.
- Visual inspection of figures other than buried_compact.png.

## 9. Proposed row B42 "why" text and supervisor summary (numbers from OUT)

**Row B42, "why" column:**

> A feature of known shape to test whether reflection holography sees below the surface. Report T3,
> analysis revised by T4 and T5 (audits A9a, A10a). In the 1499 A demo cell (OUT:316; UNVALIDATED
> engine, TEST_ONLY r = 0.1, OUT:1; no dose model, so experimental detectability is not assessed):
> - Cap 5 A: the void changes the vacuum-side specular beam. The part that leaves through the vacuum
>   (end face masked before the aperture) is 0.0274-0.0789 rad in phase and 2.6-10.3 % in amplitude
>   over nine masks (OUT:317). The spread comes from how the first 2.5 A above the top atomic plane is
>   assigned. 2.5 A is the resolution of the specular selection, and 0.52 of the raw vacuum-side
>   change lies in that layer (OUT:317). The total over the vacuum region, 0.128 rad and 9.8 %,
>   includes end-face signal carried by the aperture (OUT:317).
> - Cap 10 A: a vacuum-side change is NOT DEMONSTRATED. The two-beam causal vacuum layer is 0.317 A
>   (DERIVED_HERE), below the 2.5 A resolution. Beams inside the engine's band (band edge 65.4 mrad)
>   could carry signal up to 6.59-8.64 A above the surface. The total over the vacuum region
>   (0.00634 rad, 0.8 %) is mostly end-face signal in amplitude. The vacuum-origin part (0.02-0.50 %
>   of the reference amplitude, depending on the mask) is not attributed (all OUT:318).
> - Caps 20 and 30 A: by the two-beam characteristic (DERIVED_HERE) the signal from the void top
>   surfaces 1082.6 and 1623.9 A downstream, beyond the exit plane. The steepest in-band path
>   surfaces 305.2 and 457.7 A downstream. It reaches at most 5.41 and 2.18 A above the surface,
>   below the ring's projection at 7.05-9.05 A; for cap 20 it enters the 2.5 A-dilated region P
>   (from 4.68 A) at the aperture's steepest angle (OUT:319, 320).
>
>   The engine's vacuum difference at the ring's projection (0.000232 and 0.00016 of the reference
>   amplitude, OUT:319, 320) is attributed to a numerical artefact of the non-local tails of the
>   transmission function. The attribution is BY ANALOGY and UNVALIDATED in this cell. In a
>   TEST_ONLY small cell (same engine, pixel rule and z geometry, smaller void R 20 A, r 6 A;
>   tools/review/t4/m1_stage1_px0.13_output.txt and m1_stage2_px0.09_output.txt), the same kind of
>   difference was reproduced by the far change of the transmission function alone. From dx 0.129
>   to 0.090 A it fell to 0.040 and 0.128 of its value (OUT:319). That is CONFIRMED there, on a
>   criterion set after a first stage whose pre-stated criterion gave NOT CONFIRMED (aperture
>   leakage). The analogy is imperfect: the cap-20/cap-30 ratio is 1.278 here and 2.637 in the small
>   cell (OUT:210). No full-size rerun.
> - The fitted decay lengths of T3 section 4.3 are withdrawn (cell artefacts). Numbers:
>   tools/review/t5/buried_torus_analysis_output.txt.

**Supervisor summary:**

> 1. Demo: a ring-shaped void (R 50 A, r 12 A; OUT:7) buried 5, 10, 20 or 30 A under flat Si(001).
>    Reflection multislice at 200 keV (OUT:7), unvalidated engine, test-only absorption, 1499 A long
>    cell (OUT:316).
> 2. A void 5 A down changes the reflected beam that leaves the surface downstream of it (0.99 of that
>    region's source points lie beyond the void; OUT:317). The change is 0.03-0.08 rad in phase and
>    3-10 % in amplitude, counting only what leaves through the vacuum (OUT:325). The spread comes
>    from how the first 2.5 A above the surface is counted; this simulation cannot decide that
>    (OUT:317).
> 3. At 10 A this cell does not demonstrate it. By the simple two-beam estimate, the signal would
>    reach the vacuum only in a 0.317 A layer at the end of the cell, below the 2.5 A resolution.
>    Steeper beams in the simulation could carry some of it 6.59-8.64 A out. The small vacuum-side
>    change seen (at most 0.50 % of the reference amplitude) has not been attributed (all OUT:318).
> 4. At 20 and 30 A the two-beam estimate puts the signal 1082.6 and 1623.9 A downstream, beyond the
>    cell. Steeper beams in the simulation surface sooner (305.2 and 457.7 A) but reach at most 5.41
>    and 2.18 A above the surface, below where the ring projects (7.05-9.05 A) (OUT:319, 320). The
>    small difference seen above the ring (2.324e-04 and 1.600e-04 of the reference amplitude;
>    OUT:208, 209) is most likely a numerical artefact of the simulation. In a smaller test cell the
>    same kind of difference was traced to numerical tails of the atomic potential, and it fell to
>    0.040 and 0.128 of its value at a finer pixel (OUT:319). It was not re-checked in this cell.
> 5. Not shown: experimental detectability (no noise or dose model), any decay length, convergence
>    (pixel, slice, cell length), holograms and reconstruction.

Figure: SP/buried_t5/figures/buried_compact.png.

## 10. Final status

FINAL. A10a-M1 and m-2, m-3 and m-4 are fixed in code. Each fix has a test that fails when it is
reverted (16 of 16 mutations as expected). A10a-M2, m-1 and m-5 are covered by the printed wording
and by the proposed text in section 9. Nothing is committed.
