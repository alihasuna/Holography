# E12: adversarial review of the supervisor report "Simulating reflection electron holography of stepped Si(001): how the code works, and the smoke tests"

Status: FINAL. Reviewer E12, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`,
HEAD `c9b1909`. Nothing in the report, code or docs was edited; nothing committed. This file is the
only file written in the repository.

`SP` = `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`.
Under review: `SP/report_full/build.py` (text; cited below as `build:n`), `si001_smoke_report.html`,
`Si001_smoke_tests_report.pdf` (renders `pg01-22.png`), the ten figures in `SP/report_smoke/figures/`.
`PO:n` = line n of `tools/report/smoke_parameters_output.txt`; `RF:n` = `tools/report/report_figures_output.txt`.

## 0. What I did

- Read build.py completely. A fresh run of an unmodified copy of build.py in `SP/e12/bc/` produces an
  HTML that is byte-identical to `report_full/si001_smoke_report.html` (`cmp`), so the text below is
  the text of the delivered HTML. Looked at all ten figures, the contact sheet and pages 6, 13, 14, 16,
  19 and 21 of the PDF.
- Read the sources the report must agree with: PO (all sections), RF, the figure manifest, R1, R2, rows
  B1-B43 of docs/model_assumptions.md where cited, docs/08 rows 3.7 and 4.1-4.7, docs/06 items 6 and 12,
  docs/references.bib entries RAMSTAD1995, HEACOCK21 and TANISHIRO2003, the VALIDATION_STATUS in
  `reflection_holo/forward/multislice/engine.py` at HEAD, the docstrings of
  `tests/forward/test_rung1_refraction.py`, `test_rung2_bragg.py`, `test_rung3_null.py` and
  `test_atomistic_translation.py`, M2 section 10.2, docs/05:225-237 and 396-411, T2:219-240,
  `tools/review/t4/flat_rerun_compare_output.txt`, and the code where R2's locators left doubt
  (`pipeline/quantify.py`, `pipeline/run.py`, `forward/geometric/model.py`, `geometry/refraction.py`,
  `quantification/height.py`, `optics/inelastic.py`, `structure/oxide.py`).
- Recomputed independently from standard relativistic kinematics and the printed inputs (no package code
  called or transcribed; the code's docstrings were compared afterwards):
  `SP/e12/recompute.py` -> `SP/e12/recompute_output.txt` (CODATA 2018 constants; wavelength, refraction,
  angles, sensitivities, wraps, uncertainty split, Debye-Waller, plasmon numbers, oxide consumption,
  attenuation and phase, grids, ratios). From the saved run arrays: `SP/e12/s2s3_amplitudes.txt`.
- Executed: loading `configs/cfg_b_si001_patterned.yaml` at run level (`SP/e12/cfgb_run_level.txt`):
  `MissingProjectInputError` for items 3, 4, 5, 7, 8, 12, 13 and 15, as the report says.
- The scratch outputs above are not committed. Where a replacement text below needs a number that no
  committed script prints, I say so.

Severity scale of the instruction: MAJOR (a wrong or overstated number or claim the supervisor could rely
on), minor, note. No Blocker: no number in the report is fabricated; every number I checked is printed by
a committed script or document, except where stated.

## 1. MAJOR findings

### M1. The report says the code withholds multislice heights until the fixed-beam gate passes; no such gate exists

Where: section 2, last paragraph (build:282); section 5, first bullet (build:422).

Quoted: "the multislice pipeline runs end to end but returns no height until the fixed-beam gate passes";
"the multislice step phase stays UNVALIDATED until the fixed-beam test passes in long cells on the cluster".

What is wrong: the pipeline withholds heights only when the no-step control fails or is not performed,
for an R2 (differential) reference, and for an a/4 step outside B4 (`pipeline/quantify.py:43-48`,
`pipeline/run.py:171-182`, `628-630`). The multislice validation status is only copied into the outputs
(`pipeline/run.py:521-526`); nothing in `reflection_holo/pipeline/` reads it. The smoke multislice runs
return NO HEIGHT because their terraces (489 A; 978 A for the oxide variant) are shorter than the
three-resolution margin (PO:301-306, 1383-1387), not because of a gate. A multislice run with long enough
terraces would print heights labelled UNVALIDATED. Figure 1 of the report itself shows no such gate on the
engine stage. The "gate" is a project rule (docs/05:234-237; docs/08 3.7), not code.

Replacement (build:282): "Consequence: heights from the geometric engine are trustworthy within the B4
scope; the multislice pipeline runs end to end, and in these smoke cells it returns no height because the
terraces are shorter than the three-element margin. The code does not block multislice heights: a longer
cell would print heights that carry the engine's UNVALIDATED status (pipeline/run.py:521-526). By project
rule none may be used before the fixed-beam test passes (docs/05 4.4 item 3; docs/08 3.7)."

Replacement (build:422): see M2.

### M2. The fixed-beam translation failure: an interpretation is stated as fact, and "long cells" is not the known remedy

Where: summary, third bullet (build:230); section 2 table, fixed-beam row (build:279); section 5, first
bullet (build:422).

Quoted: "The test with the beam held fixed while the crystal moves still fails (+0.57 rad), because the
reflection has not built up in short cells"; "+0.57 rad: the (0,0,8) reflection has not built up by the
exit plane of short cells | open: cluster"; "until the fixed-beam test passes in long cells on the cluster".

What is wrong:
- The same test in cells 2500 and 5000 A longer gives -0.06 and -0.14 rad, still outside the 1.0e-2 rad
  tolerance (`tests/forward/test_atomistic_translation.py:11-15`). M2 section 10.2 (docs/agent_reports/
  M2_multislice_engine.md:381-392): +0.569, +0.519, -0.056, -0.136 rad at +0, +1000, +2500, +5000 A
  without absorption; "Without absorption the error does not converge (it oscillates in sign up to
  6600 A); with absorption it decays towards zero"; the build-up explanation is labelled "Interpretation
  (DERIVED_HERE, consistent with but not proven by the data)".
- docs/05:234-237 requires "a sourced absorption (item 21) and a cell several build-up lengths longer than
  the first-contact point". Item 21 is not supplied; all smoke multislice runs have no absorption (B30).
- docs/08 3.7 says "OPEN: the gate before any step-phase run; redesigned study being fixed (A6 N-1, N-2)",
  not "cluster".
- The test was run at the [110] azimuth (test docstring, line 3), not at the [100] azimuth of the demos.

Replacement (build:279, result and status cells): "fails: +0.57 rad in the M2 cell ([110], no absorption);
-0.06 and -0.14 rad in cells 2500 and 5000 A longer (tolerance 1.0x10^-2 rad; tests/forward/
test_atomistic_translation.py:11-15). Without absorption the error does not converge with cell length;
with TEST_ONLY r = 0.1 it decays (M2 report section 10.2). Attributed, not proven, to the unconverged
(0,0,8) build-up. | open: redesigned study (docs/08 3.7)".

Replacement (build:422): "No multislice height. Heights come only from the geometric engine. The
multislice runs here return none because their terraces are shorter than the margin, not because of a
code gate. By project rule no multislice step phase may be used until the fixed-beam translation test
passes, which needs a sourced absorption (item 21) and cells several build-up lengths long
(docs/05:234-237); the redesigned study is being fixed (docs/08 3.7)."

Replacement for the summary bullet: see M3 (one text covers both).

### M3. Summary bullet 3 overstates the validation evidence of the multislice engine

Where: build:230.

Quoted: "It passes the refraction and Bragg-reflection tests (rungs 1 and 2) and agrees in phase with an
independent dynamical solver (median 0.014 and 0.017 rad)."

What is wrong: the bullet drops every qualifier that the engine's own VALIDATION_STATUS
(`engine.py:52-67`) and docs/08 4.4 ("PARTIAL") attach:
- rung 2 (R2-A) passes for a laterally uniform continuum potential with TEST_ONLY absorption r = 0.1 and
  0.05; R2-B (r = 0, the regime of every smoke multislice run) is "optional and qualitative";
- the solver comparison is on flat Si(001), "with the solver's own potential" in both codes, TEST_ONLY
  r = 0.1; 0.051-0.075 rad at five angles and 0.398 rad at [100] 15.0 mrad; amplitude differences
  d|R|/|R| from -0.193 to +0.188 (`tools/plots/phase4_figures_solver_output.txt:1,4`); "not like-for-like
  along the beam ... not an amplitude validation".
The section 2 table gives most of these (not "the solver's own potential", and not the rung-2
absorption); the summary, which the supervisor reads first, gives none.

Replacement (build:230, whole bullet): "The multislice engine runs but is not validated for heights. It
passes the refraction test (rung 1) and the Bragg-case test on a laterally uniform continuum potential with
TEST_ONLY absorption r = 0.1 and 0.05 (rung 2, R2-A). Against an independent dynamical solver on flat
Si(001), with the solver's own potential in both codes and TEST_ONLY r = 0.1, the phase differs by a median
of 0.014 rad ([100]) and 0.017 rad ([110]), by 0.051-0.075 rad at five angles and by 0.398 rad at one angle
where |R|^2 is about 1e-5; the comparison is not like-for-like along the beam and is not an amplitude
validation (docs/08 4.4: PARTIAL). The atomistic test with the beam held fixed while the crystal moves
fails (+0.57 rad; -0.06 and -0.14 rad in cells 2500 and 5000 A longer; tolerance 0.01 rad); it is
attributed to the unconverged (0,0,8) build-up, and without absorption the error does not converge with
cell length (M2 section 10.2). The tiny multislice smoke cells are deliberately too short for a height;
they test the interfaces."

Also add to the rung-2 row of the section 2 table (build:276): "TEST_ONLY absorption r = 0.1 and 0.05; R2-B
(r = 0) optional and qualitative".

### M4. The quoted height uncertainties are almost entirely the angle-calibration stand-in, which the simulation never perturbs; "(h - built)/sigma", "within 0.05 sigma" and "costs precision, not accuracy" overstate what S1, S4 and S5 test

Where: S1 purpose "check that the correct heights come back with honest uncertainties" (build:289); S1
table column "(h - built)/sigma" (build:291-293); summary "the heights stay within their uncertainties"
(build:229); S4 caption "The heights stay within their uncertainties; the loss costs precision, not
accuracy" (build:341); S5 "within 0.05 sigma" (build:362).

Evidence (recomputed, `SP/e12/recompute_output.txt`): sigma_h^2 = (sigma_phi/s)^2 + (h sigma_s/s)^2
(`quantification/height.py:40, 210-211`). With the B19 calibration sigma of 0.1 mrad and the common-angle
rule, sigma_s/s = 0.00607, so h sigma_s/s = 0.01648 A (a/2) and 0.00824 A (a/4): 99.8-99.96 % of the
variance. The phase part sigma_phi/s = 0.0025-0.0028 rad / 8.2543 rad/A (PO:128-130, PO:13) is about
0.0003 A. The simulated angle is exact, so this term never acts. Hence:
- (h - built)/sigma = +0.01, +0.01, -0.03 does not test the noise model; measured against the phase part
  alone the S1 deviations are +0.6, +0.2 and -0.9, and the S4 deviations +1.5, +0.4 and -1.7 (my
  computation from PO:128-130 and PO:593-595; not printed by any committed script);
- in S4 the height sigma barely moves (0.00825 -> 0.00827 A, PO:594-595) while the phase scatter grows by
  a factor of 1.717 (PO:1855): the loss costs phase precision, but the quoted height sigma cannot show it;
- "within 0.05 sigma" (S5) and "within 0.12 sigma" (S4, R1) are statements about the calibration
  stand-in, not about the chain.

Replacement (add as a third item of the S1 "Two things to know" box, build:301): "The quoted 1 sigma
(0.0165 A for a/2, 0.00825 A for a/4) is almost entirely the angle-calibration term h sigma_s/s of stand-in
B19 (0.1 mrad), which the simulation does not perturb: its angle is exact. The shot-noise part is
sigma_phi/s, e.g. 0.0027 rad / 8.2543 rad/A for step 0->1 (PO:128, PO:13). The recovered heights differ
from the built ones by +0.00019, +0.00008 and -0.00026 A (RF:21-23). The (h - built)/sigma column therefore
does not test the noise model." If a numerical value of the phase part (about 0.0003 A) is wanted,
smoke_parameters.py must print it first.

Replacement (build:289): "... check that the correct heights and wrap branches come back."
Replacement (end of S4 caption, build:341): "The heights stay close to the built values. The loss raises
the phase noise (terrace scatter ratio of means 1.717, PO:1855); the height sigma barely changes (0.00825
-> 0.00827 A) because it is dominated by the angle-calibration stand-in B19."

### M5. S5: the step-height and amplitude "results" hold by construction of the geometric engine, and the tabulated "Common terrace phase offset" is not the oxide's phase

Where: summary bullet 2 (build:229); S5 variant table, column "Common terrace phase offset" (build:354-359);
S5 result "Absorption in the oxide reduces the reflected amplitude exactly as the continuum model predicts"
(build:362).

What is wrong:
- The geometric engine adds the same Re[T_k + I_k] to every terrace of a conformal layer and multiplies the
  amplitude by exp(-Im[T_k + I_k]) (`forward/geometric/model.py:36-47`: "For a conformal layer T_k + I_k
  is the same on every terrace and every step phase is unchanged"). Unchanged step heights and an amplitude
  ratio equal to the model are therefore inputs of the model. What the runs show is that the chain
  (projection, hologram, noise, reconstruction, quantification) preserves them.
- The offset column is the S5 terrace phase minus the S1 terrace phase (PO:1861-1876), but the S5 structures
  are built on 12 substrate layers instead of S1's 4 (PO:716), so their terrace tops are 10.8618 A higher
  (PO:118 vs PO:723). That alone adds -2 k_perp x 10.8618 A = -89.66 rad. Recomputed: the oxide term alone,
  2 Re k'_perp t - 2 k_perp (1 - f) t, is 90.27 rad (wrapped +2.307 rad) at 2.0 nm and 67.70 rad (wrapped
  -1.411 rad) at 1.5 nm. Adding the substrate term gives +0.615 and -3.104 rad (V' = 0: +0.614 and -3.104),
  which reproduces the tabulated 0.613-0.617, 0.611-0.615, -3.104 to -3.100 and -3.105 to -3.103 rad within
  the noise. A supervisor will read 0.61 rad as the phase of 2 nm of SiO2. It is not.

Replacement (column header, build:354): "Terrace phase minus S1's (wrapped; common to the three terraces)".
Add to the footnote (build:361): "The phase offsets are not the oxide's phase alone: the S5 structures are
built on 12 substrate layers instead of S1's 4 (PO:716), so their terrace tops are 10.8618 A higher (PO:118,
PO:723). The column shows only that the offset is the same on the three terraces (spread <= 0.0041 rad)."
Replacement (build:362, first two sentences): "The geometric engine adds the same oxide phase to every
terrace of a conformal layer and multiplies the amplitude by the continuum factor exp(-2 Im k'_perp t)
(forward/geometric/model.py:36-47). The runs show that the chain preserves this: the terrace phases shift by
a common amount (spread 0.0015-0.0041 rad), the step heights stay at their built values, and the reflected
amplitude equals the model factor to four digits."
Replacement (summary, build:229, second sentence onward): "A 2.0 or 1.5 nm conformal oxide adds the same
phase to every terrace, so the step heights are unchanged, as the geometric model guarantees by
construction; its absorption reduces the reflected amplitude to 0.5271 (2.0 nm) and 0.6186 (1.5 nm), the
model factor the engine applies, carried through the chain to four digits."

### M6. Summary bullet 4 gives the S8 numbers without their labels, and "deeper voids need a longer cell" is an inference that B42 does not support for the 10 A cap

Where: build:231.

Quoted: "A ring-shaped void 5 A under the surface changes the beam leaving the vacuum by 0.03-0.08 rad and
3-10 %; deeper voids need a longer cell."

What is wrong: the numbers come from an UNVALIDATED multislice cell with TEST_ONLY absorption r = 0.1 and no
dose model (B42; T5 OUT:1, PO:2076). They are maxima over the vacuum region over nine masks, "not a bound"
(OUT:317). The section-S8 text carries these labels; the summary does not. For the 10 A cap B42 does not say
the cell is too short: the change is NOT DEMONSTRATED because the two-beam causal vacuum layer (0.317 A) is
below the 2.5 A resolution, the total is mostly end-face signal in amplitude, and the vacuum-origin part is
not attributed. For 20 and 30 A the two-beam signal would surface beyond the exit plane, but no longer cell
was run, and whether one would show a signal is unknown. The rounding (0.03-0.08 rad, 3-10 %) is T5's own
(OUT:325), so it is traced.

Replacement (build:231, second sentence): "In an UNVALIDATED multislice demo with TEST_ONLY absorption
r = 0.1 and no dose model, a ring-shaped void under a 5 A cap changes the specular beam leaving through the
vacuum by at most 0.03-0.08 rad and 3-10 % (maxima over the region; the range depends on how the first
2.5-5 A above the surface are assigned and is not a bound). Under a 10 A cap no vacuum-side change is
demonstrated; under 20 and 30 A caps the two-beam signal would surface beyond the end of this 1499 A cell
(B42). Experimental detectability is not assessed."

### M7. S3: the caption attributes to "realisation 0 alone" a difference that comes from two definitions of "object amplitude" (low impact, but wrong)

Where: Figure 4 caption (build:327): "realisation 0 alone gives a ratio of 0.752"; S2 result (build:319):
"detector object amplitude 0.0948 (RMS over lit pixels)".

Evidence (own computation from the saved arrays, `SP/e12/s2s3_amplitudes.txt`): the summary's 0.0948 is the
"RMS of the detector object amplitude over the LIT terrace-top pixels >= half their maximum" (summary.json
`empty_object_amplitude_rule`; 320 of 512 px). Over all 512 lit pixels the static value is 0.07776. That is
the "static: RMS 0.0778" of Figure 4(b) and RF:15. For realisation 0 of S3 the summary's rule gives
0.7686 (0.07284/0.09476), almost the two-realisation 0.7692. The all-lit rule gives 0.7521. The difference
between 0.769 and 0.752 is therefore the pixel selection, not the number of realisations. R1 had it right
("0.7692 (summary definition), 0.7521 (all lit px, figure script)", R1:77). The report also gives the same
static S2 quantity two values: 0.0948 in the text and 0.0778 in Figure 4, both described as RMS over lit
pixels.

Replacement (build:327, panel b): "(b) Object amplitude on the detector along the beam for realisation 0
(RMS per row). Over all lit pixels the thermal/static ratio is 0.752 (RF:15); the 0.7692 of the text uses
the run summary's rule (lit terrace-top pixels at or above half their maximum), so the two ratios differ by
definition, not by the number of realisations."
Replacement (build:319): "detector object amplitude 0.0948 (RMS over the lit terrace-top pixels at or
above half their maximum; 0.0778 over all lit pixels, Figure 4)".

## 2. minor findings

m1. Citation: "Tanishiro et al. 2003" (build:330). The paper has one author: `docs/references.bib:1357-1358`
(author = {Tanishiro, Yasumasa}); docs/08 4.6 and B38 write "Tanishiro 2003". Replace with "Tanishiro 2003".

m2. S4 angle: "a transfer of Tanishiro ... to our angle" (build:330). B38 transfers 1.44 to 16.13 mrad
(the multislice angle); S4 is a geometric run at 16.4743 mrad. The same 1/sin(theta) transfer at 16.4743
mrad gives n = 1.2205 and a zero-loss amplitude of 0.5432 (recomputed; not printed by any committed script).
Wording: "a transfer of Tanishiro 2003 (Si(111), 200 kV, 0.8 deg) to the (0,0,8) condition at 16.13 mrad
(B38), used unchanged at the geometric angle 16.47 mrad".

m3. Section 2, rung 1: "tolerance fixed in advance" (build:275). The test docstring says the tolerances
"come from the convergence study in ... M2_multislice_engine.md section 2" (engine runs;
`tests/forward/test_rung1_refraction.py:7-11`; largest phase error 4.75e-4 rad). Only rung 2's criteria
were set before any engine run (`test_rung2_bragg.py:10-12`). Wording: "phase within 1.0x10^-3 rad (largest
4.75x10^-4 rad; tolerance from the M2 convergence study)". R2:176 carries the same over-claim.

m4. S1 pixels (build:298): "the rest are shadow (640), risers (384), below the surface (5,248) or outside the
field (5,632)". These sum to 11,904; the unusable total is 12,032. 128 lit pixels are unusable too (lit 53,632
vs usable 53,504, PO:134). Add "and 128 lit pixels excluded by the processing".

m5. S6 flat-surface rms (build:378, 381): only the across-beam cut is quoted (0.00061 / 0.00059 A,
PO:1522, 1657). The along-beam cut gives 0.00084 / 0.00110 A (PO:1523, 1658), 1.3-1.8 times the median
sigma_h. So "consistent with the median sigma_h" holds for one cut only; this is the same excess as in S1.
Give both cuts.

m6. S6 reading (build:381) and summary bullet 4: across the beam the ring's sides are 6.7 resolution
elements, yet still unmeasurable, because the flank a/4 terraces are narrower than the resolution (PO:1519,
1654). The flat interior enclosed by the ring is also unmeasurable (trench: 198,658 px "not_connected";
ridge: 531,930 px "not_lit", PO:1521, 1656; Figure 7, third column). The reliability map uses the built
geometry, which exists only in simulation (T2:228-229). "The flat surface around it reconstructs" should
read "the flat surface outside the ring".

m7. S6: "Heights of nanometre features need a rocking series or a larger aperture" (build:381). This is an
unsourced inference. T2:238-239 lists "rocking series, convergent illumination, other azimuths ... other
reflections or apertures" as NOT RUN, "the conditions under which the ring height might be measurable". The
364 A comes from the 6 A sideband resolution (3 fringe spacings of the 2 A carrier, B28/B29) divided by
sin(theta), not from the aperture alone. Wording: "Whether a rocking series, other reflections or other
apertures and fringe spacings would make the ring measurable was not run (T2)."

m8. S5 multislice: "its object amplitude is 0.310 of S2's" (build:362). The oxide cell differs from S2
(180-period terraces, nx 576, 60 A vacuum; PO:1309-1360) and its amplitude selection keeps 144 of 480 lit px
against 320 of 512 (own computation). The ratio is not an oxide attenuation and must not be compared with
0.5271. Add "(a different cell; not an attenuation measurement)".

m9. S5 table, "Consumed Si layers (2.0 nm): 7" (build:351). The count lies 0.0036 layer from its rounding
boundary (PO:732; recomputed 6.5036 layers) and becomes 6 below 2.19877 g/cm^3 (B41). The config states
`rounding_boundary_acknowledged: true` (PO:631). One clause is worth adding.

m10. Section 5: "Every laboratory input is a stand-in" (build:425). Items 1 and 11 are PROJECT_INPUT, and
item 12 is partly supplied: ion-milled, air-exposed, O2/Ar plasma-cleaned, so oxide-covered (docs/06:29;
PO:33-34, 40, 62). The base demos' clean bulk-terminated surface (B26) is therefore contrary to the supplied
item 12. Say so.

m11. Summary bullet 5: "Every value is labelled" (build:232). "Plain settings" carry no label (PO:3). Use
"Every value tied to a laboratory input is labelled".

m12. S8 purpose and run log (build:403, 418):
- "TEST_ONLY absorption r = 0.1; seven runs": 2 of the 7 runs (cap 10 and flat, r = 0) use B30, no absorption
  (PO:1982-2038, 2063-2068).
- "Same engine settings as S7 but ... 1499 A long": S7's crystal is also 276 periods = 1499 A long; S8's grid
  differs (1323 x 1134, dx 0.1278 A).
- "S8's flat reference was re-run on dc4eb7f and is bitwise identical": only the TEST_ONLY r = 0.1 flat
  (`tools/review/t4/flat_rerun_compare_output.txt:1-8`).

m13. S8 table (build:405-407) drops caveats that B42 and T5 state:
- cap 10: the 0.317 A layer "is not a bound" (in-band beams reach 6.59-8.64 A above the surface); in phase the
  vacuum-origin part reaches 0.86 of the total (OUT:318).
- caps 20 and 30: the artefact analogy "is imperfect" (cap-20/cap-30 ratio 1.278 here, 2.637 in the small
  cell; B42), and it was CONFIRMED only on a criterion set after a first stage gave NOT CONFIRMED (OUT:319-320).

m14. Section 1, structure and engines (build:252, 258):
- The Ramstad reconstructions are SECTION_READ and their room-temperature use is an ASSUMPTION; the flip-flop
  ensemble is B37, a model choice (R2:34-36).
- The Kirkland parameterisation is UNVERIFIED by us (SM17, R2:75).
- The B4 scope also covers a conformal continuum oxide at <100> (B4), which S5 relies on.
- These labels are missing.

m15. Parameter tables:
- S2 "Changed from S1" (build:307-318) lists 10 of the 36 differences (PO:246-282). Missing are substrate
  layers 4 -> 26, edge periods 1 -> 2, build-up depth 20 A, vacuum 40 A, depth 32 A and entrance vacuum.
  Section 3 promises "each later test lists only what it changes", so either complete the list or say
  "main changes".
- The absorber label "NUMERICAL" is the code's (engine.py:9), not the loader's "plain setting" (PO:175).
- S9 omits the R1 separation D0 = (0, 20, 0) A, ASSUMPTION B40 standing in for item 16 (PO:1745, 1816).

m16. PDF layout:
- In the S5 variant table, numbers break mid-digit ("+2.71 / 533", "-1.35 / 779", pg14), inviting misreading;
  remove `overflow-wrap:anywhere` for those cells.
- The reused wide figures (Figures 7, 9, 10) print at a size whose labels are unreadable (pg16, pg19); R1:98-100
  asked for a landscape page.
- Page 6 is almost empty.

m17. The S1 note on the chance bound (build:301) should add the true rate: "printed 1.22e-4, true rate
2.04e-3, still below alpha = 2.70e-3" (docs/05:409-410; R2:135), so the reader sees that the verdict
survives.

m18. Section 5 omits that the terrace regions and the no-step control's flat region come from the built
geometry, which exists only in simulation, and that segmentation from data is not implemented (build:266;
R2:128, 205). This is a limitation of the demonstration.

## 3. notes

n1. Section 1 defines Delta = V0/E_eff as a number, then writes k'_perp = k sqrt(sin^2 theta + Delta(V + iV')).
In the code Delta(.) is a function of the potential (`geometry/refraction.py:150-169`). Write
"(V + iV')/E_eff(V + iV')" or "Delta evaluated at V + iV'".

n2. S5 footnote "0.0082-0.0083 (a/4)": PO prints 0.00824-0.00825 (recomputed 0.008248). The built value of
step 2->0 in the oxide runs is -1.35772 A (PO:742, 889, 1036, 1183), not -1.35773.

n3. "The ridge looks alike" (build:400): same layout, but the ring signature in panel (g) has the opposite
sign and lies at a different height. Write "The ridge figure has the same layout".

n4. "detector MTF (Medipix3)" (build:424): docs/06 item 6 says "Medipix-based ... exact model, e.g.
MerlinEM, to be confirmed".

n5. The S7 exit-wave figures select the specular beam with a 0.2 1/A disc (about 5 mrad), not the 3 mrad
aperture of B22 (Figure 9, panel e).

n6. "Ichimiya method" (build:277): the docs say "Ichimiya-type" (docs/05:186).

n7. The smoke runs' saved VALIDATION_STATUS says "up to 0.05 rad" (PO:311). HEAD's says "more than"
(fd3ef33). The package tree at HEAD therefore differs from 14148875c6ba, in engine.py only.

n8. Labels in the S1 table:
- "so the steps are ... | ASSUMPTION B18 (item 14)": the sequence follows from B25; B18 names the step types.
- "Noise; MTF | ASSUMPTION B24": the seed is a plain setting (PO:93).
- D table "13.903 V (Kirkland IAM, B32)": the value is REPRODUCED (D3 F16, PO:16); B32 is the angle rule.

n9. S3 compares the thermal/static ratio with the kinematic Debye-Waller amplitude factor. That this factor
is the expected attenuation of a dynamical specular beam averaged after squaring is itself unsourced. The
"indicative only" is already there; "agreement" could read "the values are close".

## 4. Verified as correct

- Header, meta line, 200 keV only (no other energy anywhere in the text), "DEMO: not comparable to
  experiment" on every section.
- D table (build:176-183): every entry recomputed to the printed digits (lambda 0.02507934 A, k 250.5323
  rad/A, theta_int 18.4720 / 18.4719 mrad, theta_ext 16.4743 / 16.1347 mrad, s 8.2543 / 8.0842 rad/A, h_2pi
  0.7612 / 0.7772 A, a/4 and a/2 phases and wraps); the 0.76-0.78 A and 1.358 A of section 1.
- S1 parameter table: every value and label matches the loader output (PO:33-125): items 1, 3-9, 11, 12, 14,
  15, 16, 19, 20, 21 and rows B1, B2, B17-B31. Also 24,000 atoms, 0.9837, 1.0000, 364.2 A, 0.1667
  cycles/A.
- S1 results (PO:127-136): heights, sigmas, wrapped phases, branches, relations, chance bound 1.22e-4 vs
  2.70e-3 (P(|Z| > 3) = 2.6998e-3 recomputed), no-step control, pixel counts, 2.9 s. The heights recompute
  from the printed wrapped phases and branches. Figure 2 panels match its caption; panel (e) medians
  reproduce the wrapped step phases.
- S2: 27,000 atoms, box, grid, dx/dy, 1095 slices, 3.56 %, 0.0948, 489 A vs 3 x 372 A, labels B25, B30,
  B32. S3: B(T), 295.5 K, B35/B36, u = 0.077652 A (recomputed), seed 20260924, 0.0729, 0.0948, 0.7692, DW
  0.7724 (recomputed).
- S4: n = 1.246 (B38, item 21), exp(-n/2) = 0.5363, 71.2 % (0.7123), 0.00388 / 0.00723 rad, scatter ranges,
  tolerances, heights (PO:586-597, 1853-1858); Figure 5 numbers (RF:18-19).
- S5: oxide parameter values and labels (B41 per-parameter labels are correct for the demo variants; B43
  applies only inside a PROJECT_INPUT/TEST_ONLY item-12 record); f = 0.4415; consumed layers 7 and 5
  (recomputed); exp(-2 Im k'_perp t) = 0.5271 and 0.6186 (recomputed); all twelve heights; offsets as
  printed; 54,000 atoms, 2175 slices; 0.53-0.58 A per A (B7; recomputed 0.5282-0.5826 from 4.27-4.71
  rad/A at 16.1347 mrad) and 0.86 vs 4.45 rad/A (A9b, x5 C4). Figure 6 matches RF:21-44.
- S6: R, r, centre, field, 1 A cells, detector field, pi/2 (B29), 39.8 % / 18.7 %, 0 of 62 / 0 of 5110,
  no-step controls, 0.110 elements (recomputed 0.1098), 1.78 wraps, median sigma_h 0.0006-0.0007 A.
- S7: atoms (3,786 removed, 3,273 added: recomputed), box, grid, dx/dy (recomputed), 1124 slices, 16.1347 mrad,
  MIP 13.9028 V, beam, B30, simulate 188-207 s, RSS about 1.3 GB, the a1ef2a0 rerun statement, the
  status-string remark (PO:1904-1978).
- S8: every number of the table and caption against B42 and T5 (PO:2076-2086): 0.0274-0.0789 rad, 2.6-10.3 %,
  2.5-5 A (B42), 0.128 rad, 9.8 %, 0.317 A, 6.3 mrad, 0.8 %, 1082.6/1623.9 A, 305.2/457.7 A, 2.3e-4 and
  1.6e-4, 1/420 and 1/530 (recomputed 417.1 and 533.0), 74 layers, 1499 A, 502-727 s, audits A9a, A10a, A11,
  "geometry confirmed by Ali".
- S9: 0.01 mrad (B40, item 3), 1 x 4, tolerance 0.01, bound 8.1e-5, coherence 0.99925 (0.99810-0.99964),
  contrast 0.9993, 0.0948, 41.4 s (PO:1776-1849).
- Run log: all 14 rows (commits, wall times, verdicts) against PO:1888-1903, PO:1904-2074 and the figure
  manifest; the package-tree statement (14148875c6ba).
- Section 1 equations against the code: measurand and h = -Delta_phi lambda / [2 pi (sin theta_in + sin
  theta_out)] (`quantification/height.py:6-12`); sigma_h (`height.py:40`); refraction
  (`geometry/refraction.py:13-16`); oxide phase and attenuation (`forward/geometric/model.py:36-47`);
  split-step multislice (`forward/multislice/engine.py:4-10`); F = e^(-n/2) for R1 (`optics/inelastic.py:34-36`);
  lattice constraint and P(|Z| > 3) (R2:130-133); CFG-B refusal items (REPRODUCED here).
- Citations: Ramstad, Brocks and Kelly 1995 and Heacock et al. 2021 match references.bib. No DOI or page
  appears in the report.
- Figure captions 1-10 against the images: correct except m6 (Figure 7 interior), M7 (Figure 4b) and n3
  (Figure 9).

## 5. Verdict

Not ready to send as is. Seven MAJOR corrections are needed, all text-only; no rerun is needed:
- M1: the non-existent code gate;
- M2: the fixed-beam test framing;
- M3: the multislice validation summary;
- M4: the angle-dominated height sigma;
- M5: the S5 by-construction results and the confounded offset column;
- M6: the unlabelled S8 summary;
- M7: the S3 ratio attribution.

The exact replacement texts are given under each item above. Everything else is well traced: every number I
checked matches its committed source, the D table and all derived quantities reproduce independently, and
the equations match the code. The minor items m1-m18 improve precision and layout. m1 (single author),
m2 (angle of the B38 transfer), m6 and m7 (S6 reading) and m10 (item 12 is supplied and oxide-covered) are
worth fixing in the same pass.
