# A11: re-audit of T5 (fixes of re-audit A10a on the buried-torus-void analysis)

Auditor A11, 2026-09-24. Branch claude/electron-holography-orchestration-nakd7r. T5's commit is c821862;
HEAD is b7dcbf0 (an X6 snapshot that does not touch any T5 file: `git diff c821862 HEAD --
tools/plots/buried_torus.py tests/forward/test_buried_torus_analysis.py` is empty). A11 writes only
this file. It edits no code, test or document, commits nothing and writes nothing under outputs/.
Scratch: SP/a11/, with SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
Status: FINAL (section 5).

## 0. Command log (anything not listed here was NOT RUN)

- R1. `git status`, `git log --oneline`, `git show --stat c821862`, `git show --stat b7dcbf0`,
  `git diff c821862 HEAD --stat -- <T5 files>` (empty), `wc -l` of the files in scope.
- R2. Read in full: docs/agent_reports/A10a_T4_reaudit.md, T5_a10a_fixes.md, tools/plots/buried_torus.py
  (c821862 = working tree), tests/forward/test_buried_torus_analysis.py, tools/review/t5/* (script and
  three outputs), row B42 (docs/model_assumptions.md:68) and its diff in c821862; T4's
  test_reading_lines and reading_line (`git show c821862^:...`); the small-cell outputs
  tools/review/t4/m1_stage1_px0.13_output.txt:35-47 and m1_stage2_px0.09_output.txt (grep).
- R3. Text of SP/brief/brief.html and SP/brief/figures.html (12:10 UTC versions), extracted with an
  inline python HTML-to-text filter.
- R4. `SP/a11/recompute.py` (`OMP_NUM_THREADS=1 venv/bin/python`, no repository import; 18 s, rc 0),
  output `SP/a11/recompute.out`. Own numpy-FFT aperture (circle 0.2 1/A about sin(theta_out)/lambda),
  own regions V and P, own masks (A10a's nine plus eight extra members), own metrics, on T3's saved
  exit waves SP/buried/ms_*_test_only_r0.1. It also computes the peak and centroid of the main mask's
  profile, the raw first-layer fraction (in |D|^2 and in |D|), the band edge against the metadata,
  the causal reaches, the compact-figure maxima and where they sit.
- R5. `SP/a11/mutate_a11.py` (1 thread), output `SP/a11/mutate_a11.out` and `SP/a11/mutate_a11_T4a.out`.
  Each mutation is applied to a fresh `git archive c821862` copy under SP/a11/mut/<name> (never the
  repository); the imported package path is printed; only tests/forward/test_buried_torus_analysis.py
  runs. There are 14 mutations plus a control.
- R6. `OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python tools/plots/buried_torus.py --runs SP/buried --out
  SP/a11/figs_rerun` (52 s, rc 0), output SP/a11/analysis_rerun.out. `diff` against
  tools/review/t5/buried_torus_analysis_output.txt, with the figure directory substituted, gives
  `IDENTICAL apart from the figure directory`. `cmp` of buried_compact.png against T5's gives
  `byte-identical`.
- R7. Read the PNG SP/buried_t5/figures/buried_compact.png.
- R8. Code reading: reflection_holo/forward/multislice/analysis.py select_beam,
  propagator.py propagator_phase, grid.py:185-200 (angle_ceiling_x_mrad); the exit-wave metadata keys
  `propagator` and `band_limit`.
- R9. Inline python: the per-mask ratios of the cap-5 family rows to the cap-20 and cap-30 family rows
  (OUT:214-222, 244-252, 258-266).

NOT RUN:
- any multislice run;
- the full pytest suite, and the three other buried test files (T5's "65 passed" is not re-checked;
  A11's control of the analysis test file gives `27 passed`);
- T5's mutate_t5.py itself (A11 reran A4 and A6 literally and A5 in its own form, R5);
- a visual check of any figure other than buried_compact.png;
- the docx/pdf builds of the brief.

"OUT:n" means line n of tools/review/t5/buried_torus_analysis_output.txt.

## 1. Verdict

T5's code fixes hold, and every number T5 printed reproduces from the exit waves with an independent
implementation (R4). The committed output comes from the committed script (R6). A10a's surviving
mutations A4, A5 and A6 now fail (R5).

The figure can be shown tomorrow. buried_compact.png uses one shared log scale (-5 to -1). The deep-cap
blobs sit at about -3.7, dark purple, and are no longer the most prominent feature. The cap-5 title
gives the range.

Row B42 can be shown. Every number traces to OUT or to T4's small-cell outputs with the right label.
Four wording points are minor (A11-m1, m2, m5, m6).

The brief's section-4 buried-void paragraph cannot be shown as written (A11-M1, MAJOR). It turns the
two-beam estimate back into the expected behaviour of the simulation ("the signal is expected to
surface 1,083 and 1,624 A downstream, beyond the end of the cell"). This is the wording A10a-M2
already rejected, and T5's own printed band-edge path contradicts it. The corrected sentence is in
section 3. Appendix E1 has the two-beam qualifier; it needs only minor changes (A11-m4).

## 2. Findings, ranked

### A11-M1 (MAJOR): the brief's buried-void paragraph states the two-beam estimate as the expected behaviour of the simulation

**Where.** SP/brief/brief.html, section 4, the paragraph "A buried void (appendix E; ...)". The
sentence reads: "At 10 Å no change is demonstrated in this cell; at 20 and 30 Å the signal is
expected to surface 1,083 and 1,624 Å downstream, beyond the end of the cell."

**What is wrong.**
- 1,083 and 1,624 A are the TWO-BEAM surfacing distances: (0,0,8) at 18.47 mrad, OUT:281 and 284,
  labelled DERIVED_HERE.
- The engine's band also carries steeper waves. T5's own output prints the band-edge path (65.45 mrad)
  surfacing 305.2 and 457.7 A downstream of the void top (OUT:283, 286). Both lie inside the cell:
  the void's upstream edge is at z 965.15 A and the exit plane at 1526.08 A, so 560.9 A of crystal
  lie downstream.
- A10a-M2 (MAJOR) rejected this same sentence in T4's supervisor summary, item 4 ("That is again
  two-beam"). T5's proposed summary (T5 report section 9, item 4) words it correctly: "the two-beam
  estimate puts the signal ... Steeper beams in the simulation surface sooner (305.2 and 457.7 A)".
  The brief did not carry that wording over.
- Appendix E1 of figures.html keeps the qualifier ("by the two-beam estimate") but also drops the
  steeper beams (A11-m4).

**Why it matters.** This paragraph is the buried-void text in the body of the brief, which the supervisor reads first.
It makes a definite physical prediction, "the signal is expected to surface beyond the end of the
cell". The project's own analysis does not support it: in-band paths surface inside the cell. Those
that the aperture accepts stop below the ring's projection. This does not change the conclusion that
a longer cell is needed, but it states that conclusion's reason wrongly.

**Reproduction (R4).** `band_edge 65.446 mrad: surfaces 305.16 A; reach +4.127 (theta_out) +5.411
(21.15 mrad)` for cap 20 and `surfaces 457.74 A; reach +1.665 ... +2.183` for cap 30. The two-beam
values are `surfaces 1082.60 A` and `1623.90 A`.

**Fix.** Section 4 gives the exact sentence.

### A11-m1 (minor): "the range comes from how the first 2.5 Å above the surface is counted" is imprecise; the low end of the amplitude range depends on 2.5-5 A and on the ramp width

**Where.** OUT:317 (reading line), OUT:325 (compact-figure title), B42 (docs/model_assumptions.md:68),
brief section 4, appendix E1.

**Verified.**
- Every member of the family is 0 at and below the top atomic plane. The code (buried_torus.py:242-255)
  refuses start < 0; A11's independent masks assert it for all 17 masks (R4).
- The family is A10a's nine masks verbatim. The test asserts this
  (test_mask_family_is_a10a_nine_...), so T5 neither added nor dropped members.
- The range reproduces to all printed digits (R4): phase 0.027357-0.078905 rad, |rho-1|
  0.026022-0.10335, |dpsi|/A_ref 0.030362-0.10527. The total over V is 0.12826 rad and 0.098081.

**Is the family fair?** On the whole, yes. Eight extra masks run by A11 (R4) fall inside the range:
- step at 0.3 A: 0.0651 rad, 10.1 %;
- ramp 0-0.5 A: 0.0662 rad, 10.1 %;
- step at 1.0 A: 0.0352 rad, 9.2 %;
- step at a/4: 0.0350 rad, 8.6 %;
- step at 2.5 A: 0.0340 rad, 6.2 %;
- ramp 0.5-3.0 A: 0.0343 rad, 7.6 %.

Masks that also discount x_rel > 5 A fall below, as they must, since they remove signal that is
plainly on the vacuum side: ramp 0-10 A gives 0.0141 rad and 1.9 %; ramp 5-7.5 A gives 0.0049 rad and
0.6 %. The family is neither widened nor narrowed on purpose.

**What is imprecise.**
- The lowest amplitude, 2.6 %, comes from the sin^2 ramp 2.5-5.0 A. That mask also down-weights
  2.5-5 A, which is twice the resolution.
- The ramp width alone moves the value 2-fold at the same start: step at 0 gives 10.3 %, ramp 0-5 A
  gives 5.5 %.
- Restricted to masks that are 1 for x_rel >= 2.5 A (the stated "first 2.5 A"), the range is
  0.034-0.079 rad and 6.2-10.3 %. These masks are: step at 0; ramps 0-1, 0-2.5 and 1-2; steps at a/8,
  1.0, a/4 and 2.5.
- The top of the phase range, 0.0789 rad, is specific to a sharp step at the plane. Moving the step
  0.3 A out (2.3 pixels) gives 0.065 rad. A sharp mask before a sharp aperture rings.

**Fix.** Say "depends on how the first 2.5-5 A above the top atomic plane is counted (where the mask
starts within the first 2.5 A and how gradually it rises)". The numbers can stay.

### A11-m2 (minor): the location evidence cited for "the change sits within the first 2.5 A" does not show it; "0.52 of the raw vacuum-side change" is a power fraction

**Where.** OUT:317; T5 report section 2 ("Reason, printed"); B42 ("0.52 of the raw vacuum-side change
lies in that layer").

**Reproduced (R4).** The peak is at +2.636 A, the centroid over x_rel -60..25 A at +0.323 A, and the
fraction in vacuum is 0.820. These are T5's +2.64, +0.32 and 0.82. The raw fraction is 0.5209 (T5: 0.521).

**What the numbers mean.**
- The centroid +0.32 A includes the 18 % of the main mask's |F(D m)| that the aperture spreads BELOW
  the top atomic plane. Over the vacuum side only, the centroid is +4.17 A and the median +3.15 A (R4).
- The peak +2.64 A sits where the main mask reaches 1 (2.5 A). The mask shapes it.
- After the aperture, therefore, the vacuum-origin change lies mostly ABOVE 2.5 A.
- The direct support for the claim is the raw fraction. 0.52 is a fraction of sum |D|^2 (power,
  before the aperture, ring's y band). In |D| the fraction is 0.31 (R4). Of the raw power in 0-2.5 A,
  the aperture passes 36 %; of that in 2.5-25 A, it passes 15 % (R4, over the whole y range).
- "Sits within the first 2.5 A" therefore overstates a 52 % power fraction.

**Fix.**
- Reading line: "about half (0.52) of the raw vacuum-side |D|^2 lies in the first 2.5 A". Drop the
  centroid, or print the vacuum-side centroid (+4.17 A).
- B42: "0.52 of the raw vacuum-side |D|^2 (before the aperture) lies in that layer".

### A11-m3 (minor): the analyse_pair -> reading_for wiring is tested for cap 5 only; eight wiring mutations survive

A10a's survivors now fail (R5, `mutate_a11.out`):
- control: `27 passed`;
- A4 (literal): `2 failed, 25 passed`;
- A6 (literal): `1 failed, 26 passed`;
- A5 in A11's own form (the cap-5 reading quotes the main mask's value as both ends of the range):
  `1 failed, 26 passed`.

Also caught: W5 (the raw fraction taken after the aperture), `2 failed`, and W7 (family rows from the
total), `2 failed`.

These SURVIVE, each with `27 passed`:

| id | mutation | supervisor-facing effect |
|---|---|---|
| W1 | loc_vac from the TOTAL F(D) (buried_torus.py:994) | the reading's peak/centroid would print -7.08/-8.57 A (OUT:24) instead of +2.64/+0.32 A |
| W2 | downstream fraction measured from the void's upstream end (line 591) | the "0.99 of V's z_s range lies downstream" (T5 summary item 2) changes silently |
| W3 | reading_for passes met["P"] as P_vac (line 1021) | the deep-cap reading prints the total as the "vacuum-origin part" |
| W4 | reading_for passes end_face_max["P"] instead of ["V"] (line 1021) | cap 10: end-face max of P is 0.00200 (OUT:46), below the family maximum 0.00497, so the reading would say "the vacuum-origin part reaches or exceeds the end-face part"; B42's "mostly end-face signal in amplitude" would be contradicted by the output with no test failing |
| W6 | compact window -20..20 A (line 125) | changes the basis of the "1/420, 1/530" ratios |
| W8 | ring y band = all y (line 992) | changes the raw fraction 0.52 and the location |
| W9 | cap-10 phase fraction inverted (line 619) | "0.86 of the total's max \|dphi\|" becomes 1.16 |
| W10 | family region always V (line 956) | the deep-cap family ranges become nan |

The synthetic pairs run only on cap-5 geometry with differences that do not depend on y, and
reading_for is called only for cap 5.

**Fix.**
- Run the synthetic pair also on cap-10 and cap-20 geometries, with end-face > vacuum-origin in V.
- Assert through reading_for: the end-face number, P_vac, the downstream fraction against its formula,
  and loc_vac against a known vacuum-only bump.
- Use a y-dependent synthetic difference.

### A11-m4 (minor): "about 1/420 and 1/530 of the 5 Å level" is the ratio for the mask shown; the 5 Å level is itself a range

**What is compared (R4, code lines 836-865).** Both levels are the maximum of the main mask's
|F(D m)|/A_ref over x_rel 0-20 A and ALL y:
- cap 5: 8.4802e-2 at x_rel +2.76 A, y 118.3 A. This point is in V, not in P; the maximum over P is
  3.333e-2.
- caps 20 and 30: 2.0331e-4 and 1.5907e-4 at x_rel +7.88 A, in P.

The ratios are 417.1 and 533.1, which reproduce OUT:324.

**Is it fair?** For the panels drawn, yes: same mask, window and quantity. The colour limits are shared,
by code (`_compact_bottom` uses info vmin/vmax; the clim test fails under the per-panel mutation M4a)
and visually (R7).

But the cap-5 title of the same figure gives the cap-5 change as a mask range. Pairing each family
member (R9), cap 5 / cap 20 in |dpsi| is 145-515 and cap 5 / cap 30 is 185-659. In phase the ratios
are 127-377 and 208-629; for the main mask they are 164 and 276.

**Fix.** Title and appendix E1: "(about 2e-4 of the reference amplitude; 1/420 of the 5 A maximum
for the mask shown, 1/150-1/520 over the mask family)", or simply "about 2e-4 of the reference
amplitude, against 3-10 % at 5 A".

### A11-m5 (minor): "reaches at most 5.41 and 2.18 A above the surface" holds only for waves that leave within the aperture's acceptance

**Verified (R4, R8).**
- The metadata f_x,max 2.6077095662 equals 1/(3 dx) (relative difference 0).
- asin(lambda f_x,max) = 65.446 mrad.
- The aperture accepts exit angles 11.118-21.151 mrad.
- Surfacing distances: 76.29 / 152.58 / 305.16 / 457.74 A.
- Reaches: +7.820/+10.252, +6.589/+8.638, +4.127/+5.411 and +1.665/+2.183 A. T5's 76.3/152.6/305.2/
  457.7, 7.82/10.25, 6.59/8.64, 4.13/5.41 and 1.67/2.18 reproduce.
- Cap-10 reach 6.59-8.64 A: reproduced.

**What the bound covers.** k_z is conserved at the surface. A wave at the band edge inside the crystal
(65.45 mrad) therefore leaves at sqrt(65.45^2 - 8.99^2) = 64.83 mrad. That is far outside the
aperture, whose steepest accepted exit (21.15 mrad) corresponds to 22.98 mrad inside (R4). The formula
combines band-edge travel inside with an exit inside the acceptance. That needs a re-scattering, and
it bounds only what the aperture passes directly.

In the RAW exit field, a band-edge wave that keeps its angle reaches x_rel +16.76 A (cap 20) and
+6.76 A (cap 30). Both are inside P (4.68-11.46 A). Such a wave reaches the filtered image only
through the sharp aperture's tails. The reading line says so ("not a hard edge"); B42 does not.

The deep-cap attribution does not rest on this bound: A10a's argument that the small cell's local
run holds every physical path stands.

**Fix.** B42: "... reaches at most 5.41 and 2.18 A above the surface for waves leaving within the
aperture's acceptance (steeper exits reach P only through the aperture's tails)".

### A11-m6 (minor): maxima are quoted as "the change"; the brief paragraph drops "counting only what leaves through the vacuum"

B42 says the cap-5 part "is 0.0274-0.0789 rad in phase and 2.6-10.3 %". These are max |dphi| and
max |rho-1| over V. The main mask's rms over V is 0.0164 rad against a maximum of 0.0339 (OUT:17).

The brief paragraph says "changes the beam ... by 0.03-0.08 rad and 3-10 %" without "counting only
what leaves through the vacuum". Appendix E1 has that qualifier. Without it, the reader cannot tell
that the full vacuum-side change is 0.13 rad and 10 %.

**Fix.** Write "by up to" and add the qualifier (section 4).

### Notes

- n1 (reproduction). Every T5 number used for the supervisor reproduces independently (R4) to its
  printed digits:
  - cap 5: family, total, 0.52, 0.99 (0.9916), peak/centroid;
  - cap 10: family 0.00016955-0.0049688 in |dpsi| and 0.00013037-0.0054408 rad; total 0.0063372 rad,
    0.0082427;
  - caps 20/30: P totals 2.3244e-4 and 1.600e-4; vacuum-origin 2.033e-4 and 1.591e-4;
  - the causal paths and the compact-figure maxima.

  The committed output reproduces line for line from the committed script, and buried_compact.png is
  byte-identical (R6).
- n2 (65.45 against 65.40 mrad). The metadata's `angle_ceiling_x_mrad` 65.3996 is the paraxial
  lambda f_x. T5's 65.446 mrad is asin(lambda f_x). The runs use the EXACT propagator (metadata
  `propagator.kind: exact`, kz = sqrt(k^2 - q^2), propagator.py:34-38), whose group slope is
  tan(asin(lambda f)), so T5's value is the right one. With the paraxial value, the cap-20 surfacing
  distance is 305.4 A instead of 305.2 A, and every reach changes by < 0.01 A. B42's "65.4 mrad" is
  consistent with both.
- n3 (T4's test_reading_lines). The seven assertion conditions and the three-word loop are textually
  unchanged. The new inputs (family, a geometry from regions(), loc_vac, raw fraction) do not weaken
  them. Check: making the deep-cap line quote P_vac as the total (mutation T4a) fails
  test_reading_lines (`1 failed, 26 passed`, SP/a11/mutate_a11_T4a.out). The "0.00016" assertion
  still bites, and none of the new numbers in the line contains that substring.
- n4 ("0.99 of V's z_s range"). This is a property of region V's construction (V is the two-beam
  downstream region), not a measurement. It is consistent with the data: the cap-5 vacuum-origin
  maximum lies at x_rel +2.76 A, so z_s = 1526.08 - 2.76/tan(16.13 mrad) = 1355 A. That is 266 A
  downstream of the void's end (1089.2 A).
- n5 (appendix E1 caption). "removed sites in red": the markers are orange (#eb6834).
- n6 (brief section 1). "the latest buried-void analysis is still awaiting its re-audit" must be
  updated after this report.
- n7 (small-cell constants). M1_ATTRIBUTION's 0.040, 0.128, 1.008, 0.918 and tails/full 0.998-1.012,
  and SMALL_CELL_P_VAC_RATIO_20_30 = 2.637, trace to tools/review/t4/m1_stage2_px0.09_output.txt:23,
  37, 46, 47, 49, 50 and m1_stage1_px0.13_output.txt:44. They are constants in the script, not
  recomputed by it; B42 cites the T4 files, correctly.

## 3. The orchestrator's five checks, item by item

1. **Nine-mask family.**
   - Every mask admits nothing at or below the top atomic plane. The code refuses start < 0, and
     every A11 mask asserts m = 0 for x_rel <= max(0, start) (R4). The top plane is
     surface_x_A = 99.113925 A. The first pixel above it is at x_rel +0.079 A.
   - Cap-5 range, recomputed: 0.02736-0.07890 rad; 2.60-10.33 % amplitude (0.026022-0.10335);
     |dpsi|/A_ref 0.03036-0.1053. The total is 0.12826 rad and 9.81 % (0.098081). The raw fraction is
     0.5209. All match OUT:223-225 and the rounding in B42 and the brief (0.03-0.08 rad, 3-10 %,
     0.128 rad, 9.8 %, 0.52).
   - Fair spread: yes, it is A10a's family verbatim, and extra masks fall inside it (A11-m1). The
     stated REASON for the spread ("the first 2.5 A") is imprecise, because the amplitude's low end
     depends on 2.5-5 A (A11-m1).
   - Peak and centroid (+2.64 and +0.32 A) reproduce, but they do not locate the vacuum-side change.
     The vacuum-side centroid is +4.17 A (A11-m2).
2. **Band-edge causal path.**
   - 65.446 mrad = asin(lambda f_x,max). f_x,max from the metadata equals 1/(3 dx) exactly.
     asin, not the metadata's paraxial 65.40, is right for the exact propagator (n2).
   - Surfacing 305.16 / 457.74 A.
   - Reach 4.127 / 1.665 A at theta_out and 5.411 / 2.183 A at 21.151 mrad.
   - Cap-10 reach 6.589-8.638 A.
   - All reproduce (R4). The bound covers only waves that exit within the aperture's acceptance
     (A11-m5).
3. **Shared log scale and 1/420, 1/530.**
   - One range [-5, -1] for all four panels, from the code, the clim test and the PNG.
   - The ratios compare the main mask's maximum |F(D m)|/A_ref over x_rel 0-20 A and all y. For cap 5
     that maximum lies in V, at +2.76 A; for caps 20 and 30 it lies in P, at +7.88 A. The values are
     417.1 and 533.1 (R4).
   - The titles are fair for the mask shown, but the cap-5 level is a mask range: 1/145-1/515 and
     1/185-1/659 over the family (A11-m4).
   - The deep-cap title says "numerical artefact by analogy". The caption adds "not re-checked in this
     cell", which is acceptable.
4. **Tests.**
   - A10a's A4, A5 and A6 now fail (A4 and A6 literal, A5 in A11's own form; R5).
   - T4's test_reading_lines is not weakened (n3).
   - The reading wiring for caps 10/20/30 and several derived numbers are still unguarded: eight
     surviving mutations (A11-m3).
5. **Row B42 and the brief/appendix.**
   - B42 traces:
     - cap 5: 0.0274-0.0789 rad, 2.6-10.3 %, nine masks, 0.52, 0.128 rad, 9.8 % (OUT:317);
     - cap 10: 0.317 A, 65.4 mrad, 6.59-8.64 A, 0.00634 rad, 0.8 %, 0.02-0.50 % (OUT:318);
     - caps 20/30: 1082.6/1623.9, 305.2/457.7, 5.41/2.18, 7.05-9.05, 4.68 and 0.000232/0.00016
       (OUT:319-320, 274); 1.278 (OUT:210); 2.637 and 0.040/0.128 (T4 small-cell outputs, n7).
   - Labels in B42: UNVALIDATED engine, TEST_ONLY r = 0.1, NOT DEMONSTRATED (cap 10), BY ANALOGY and
     UNVALIDATED in this cell (caps 20/30), CONFIRMED only in the small cell with the stage history,
     DERIVED_HERE on the two-beam values. All present and right.
   - Brief: the numbers trace to OUT:316, 317 and 325 (rounded), and 281/284 for 1,083/1,624. The
     two-beam label is missing (A11-M1).
   - Appendix E1: every number traces to OUT:7, 316, 317, 324, 325 and 281/284, with the labels (two-beam
     estimate, by analogy, not re-checked in this cell, not demonstrated, unvalidated engine,
     test-only absorption). The ratio and steeper-beam points are in A11-m4 and A11-M1.

## 4. Corrected text

**A11-M1: exact replacement for the brief, section 4, second and third sentences of the buried-void
paragraph** (currently "At 10 Å no change is demonstrated in this cell; at 20 and 30 Å the signal is
expected to surface 1,083 and 1,624 Å downstream, beyond the end of the cell."):

> At 10 Å no change is demonstrated in this cell. At 20 and 30 Å the simple two-beam estimate puts
> the signal 1,083 and 1,624 Å downstream, beyond the end of the cell; steeper beams in the
> simulation surface sooner (305 and 458 Å) but, among those the specular aperture accepts, reach
> at most 5.4 and 2.2 Å above the surface, below the ring's projection (7.1–9.1 Å).

(Sources: OUT:281, 284, 283, 286 and 274. "At most" is qualified by "among those the specular
aperture accepts", A11-m5.)

**A11-m6: first sentence of the same paragraph (recommended):**

> A ring-shaped void 5 Å under flat Si(001) changes the beam leaving the surface downstream of it by
> up to 0.03–0.08 rad and 3–10 % in a 1,499 Å demo cell, counting only what leaves through the
> vacuum (the range depends on how the first 2.5–5 Å above the surface is counted).

**A11-m4 / M1: appendix E1, the "20 and 30 Å" sentence (recommended):**

> 20 and 30 Å: by the two-beam estimate the signal surfaces 1,083 and 1,624 Å downstream, beyond
> the cell; steeper beams in the simulation surface sooner (305 and 458 Å) but, among those the
> aperture accepts, stay below the ring's projection. The faint pattern above the ring (about
> 2×10⁻⁴ of the reference amplitude: 1/420 and 1/530 of the 5 Å maximum for the mask shown,
> 1/150–1/520 and 1/190–1/660 over the mask family) is attributed, by analogy with a smaller test
> cell (an imperfect analogy, confirmed there only on a criterion set after a first stage), to a
> numerical artefact of the engine's transmission function; not re-checked in this cell.

**Row B42 (optional minor edits; the row may be shown as committed):**
- "is 0.0274-0.0789 rad in phase and 2.6-10.3 % in amplitude over nine masks" -> "is up to
  0.0274-0.0789 rad in phase and 2.6-10.3 % in amplitude (maxima over the vacuum region) over nine
  masks".
- "the spread comes from how the first 2.5 A above the top atomic plane is assigned (2.5 A is the
  resolution of the specular selection, and 0.52 of the raw vacuum-side change lies in that layer)"
  -> "the spread comes from how the first 2.5-5 A above the top atomic plane is assigned (where the
  mask starts within the first 2.5 A, the resolution of the specular selection, and how gradually it
  rises; 0.52 of the raw vacuum-side |D|^2, before the aperture, lies in the first 2.5 A)".
- "reaches at most 5.41 and 2.18 A above the surface" -> "reaches at most 5.41 and 2.18 A above the
  surface for waves leaving within the aperture's acceptance (steeper exits reach P only through the
  aperture's tails)".

**Brief, section 1 (n6):** once this report is final, "the latest buried-void analysis is still
awaiting its re-audit" -> "the latest buried-void analysis has been re-audited (A11)".

## 5. Can the buried-void figure and numbers be shown tomorrow?

- **Figure buried_compact.png:** YES. It uses one shared log scale, the cap-5 range is in the title,
  and the deep caps are labelled "numerical artefact by analogy". The "1/420, 1/530" ratios are for
  the mask shown (A11-m4, minor).
- **Row B42:** YES as committed. The numbers are exact and the labels right; the minor wording edits
  are optional.
- **Appendix E1:** YES, preferably with the replacement sentence above.
- **Brief section 4 paragraph:** NOT AS WRITTEN. Replace its second and third sentences with the
  A11-M1 text above.

Status: FINAL.
