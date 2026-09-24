# E11: adversarial review of the supervisor brief and figure appendix

Status: FINAL. Reviewer E11, 2026-09-24. Nothing committed, no document edited.

Reviewed (as rendered for the meeting; the PDFs carry the same text as the HTML, checked by text
extraction):
- `SP/brief/brief.html` = `Si001_holography_brief.pdf` (2 pages; renders `page-1.png`, `page-2.png`)
- `SP/brief/figures.html` = `Si001_holography_figures.pdf` (9 pages; images `SP/phase4_figures/*.png`,
  `SP/buried_t5/figures/buried_compact.png`, each image viewed)

SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
Repository /home/user/Holography, branch claude/electron-holography-orchestration-nakd7r, HEAD b7dcbf0
(= c821862 plus the X6 work-in-progress snapshot). Scratch: `SP/e11/`.

Recomputation: `SP/e11/e11_recompute.py`, output `SP/e11/e11_recompute_output.txt` (written from
first principles, without reading the project's implementation of any quantity). Test count:
`pytest --collect-only` in a detached worktree of c821862 (`SP/e11/wt`, removed afterwards).

Severity: MAJOR = wrong or overstated number or claim a supervisor would rely on; minor; note.

## Verdict (short)

The brief and the appendix can be shown tomorrow **after the four MAJOR replacements below**.
The appendix figures and captions are close to right. Every number in both documents traces to a
committed output or report, and every value I recomputed agrees. The four MAJORs are about claim
strength, not arithmetic:

1. the buried-void result has no UNVALIDATED or TEST_ONLY label, and the brief states a negative
   result that the analysis does not support;
2. the 17 pixels-per-fringe requirement is conditional but reads as a general design requirement;
3. the absorption r = 0.1 is called "a stand-in" where the project labels it TEST_ONLY;
4. the brief says every result passes an independent review, but the buried-void numbers (T5) have
   not been re-audited.

The word "UNVALIDATED" does not appear anywhere in the 2-page brief (PDF text search).

The brief fills page 2 to the bottom margin. The replacements add about 5 lines, so apply the trims
listed at the end and re-render. Delete the stale `SP/brief/page-3.png` (an earlier 3-page render).

## MAJOR

### M1. Buried void (brief section 4, last paragraph): engine and absorption labels missing; negative result overstated

Quoted: "A ring-shaped void 5 Å under flat Si(001) changes the beam leaving the surface downstream
of it by 0.03–0.08 rad and 3–10 % in a 1,499 Å demo cell (the range depends on how the first 2.5 Å
above the surface is counted); at 10–30 Å this cell shows nothing attributable."

What is wrong:
- The numbers come from the multislice engine, which is UNVALIDATED for this use, with TEST_ONLY
  absorption r = 0.1. Row B42 carries both labels ("In the 1499 A demo cell (UNVALIDATED engine,
  TEST_ONLY r = 0.1; no dose model ...)", `docs/model_assumptions.md:68`). So does the T5 output,
  line 1 ("STATUS: UNVALIDATED demo ..."). The brief drops both labels. The appendix caption E1
  keeps them.
- "At 10–30 Å this cell shows nothing attributable" reads as a measured absence. That is not what
  T5 found:
  - cap 10: "NOT DEMONSTRATED in this cell". A vacuum-origin part of 0.02–0.50 % of the reference
    amplitude remains, and T5 says it "is not attributed (the cap-10 local/tails decomposition is
    NOT RUN)" (`tools/review/t5/buried_torus_analysis_output.txt:318`).
  - caps 20 and 30: the two-beam signal "surfaces 1082.6 [1623.9] A downstream, beyond the exit
    plane" (OUT:281, :284, :319-320). The residual difference is attributed to an artefact only
    "BY ANALOGY, UNVALIDATED in this cell".

  So the cell cannot show a deeper void; it does not show that there is nothing there.
- The T5 numbers have not been re-audited (see M4).

Numbers verified: 0.0274–0.0789 rad and 2.6–10.3 % over the 9 masks (OUT:23, :223, :317); these
round to 0.03–0.08 rad and 3–10 %. Two-beam surfacing at 20 and 30 Å is 1082.6 and 1623.9 Å;
recomputed as cap/tan(18.4719 mrad) = 1082.6 and 1623.9 Å.

Replacement (whole paragraph):
> **A buried void** (appendix E; unvalidated engine, TEST_ONLY absorption r = 0.1; latest analysis
> not yet re-audited). A ring-shaped void 5 Å under flat Si(001) changes the beam leaving the surface
> downstream of it by 0.03–0.08 rad and 3–10 % in a 1,499 Å demo cell (the range depends on how the
> first 2.5 Å above the surface is counted). At 10 Å no change is demonstrated in this cell; at 20
> and 30 Å the signal is expected to surface 1,083 and 1,624 Å downstream, beyond the end of the cell.
> A longer cell and a dose model are needed before any claim of detectability.

### M2. Detector (brief section 4): "at least 17 pixels per carrier fringe" overstated and mislabelled

Quoted: "With realistic plasmon losses the processing needs at least 17 pixels per carrier fringe."

What is wrong:
- The plasmon loss is not realistic. It is the demo stand-in B38: a clean-surface 1/sin(theta)
  transfer from Si(111), "not comparable to experiment" and "not the oxide-covered production
  surface" (`docs/model_assumptions.md:64`).
- "The processing" is the demo processing B29, whose minimum visibility of 0.5 is itself a demo
  stand-in (`:55`).
- 17 px/fringe is the threshold for a perfect incident contrast (mu_inc = 1).
  `tools/review/e10_recompute_output.txt:106, :108`: "V with the B38 R1 factor 0.536: 0.502 (pass)"
  at 17 px; "with the B38 factor 0.536 needs MTF >= 0.9328, i.e. p >= 16.6 px/fringe".
- Since V = mu_inc x 0.536 x MTF, any incident contrast below 0.93 fails at every sampling.
  Recomputed: `e11_recompute_output.txt`, "incident contrast 0.9: best possible V = 0.482 -> fails at
  every sampling".
- Review E10 M2 asked that the threshold be re-derived with the detector model
  (`docs/agent_reports/E10_microscope_review.md:339-352`, line 351: "V_min must be re-derived together with
  any detector MTF").

A supervisor would read the sentence as a recording requirement for the experiment.

Replacement:
> With the demo plasmon-loss stand-in (fringe factor 0.536) and a vacuum reference, the demo
> processing's minimum visibility of 0.5 is reached only at 17 or more pixels per fringe and only
> for perfect incident contrast, so that threshold must be re-derived with the detector model
> (review E10 M2).

### M3. Absorption r = 0.1 labelled "a stand-in" (brief Fig. 1 caption and section 5; appendix B1); section 5 is conditional on it

Quoted: "absorption r = 0.1 (a stand-in)" (brief, Fig. 1 caption); "Cost of a realistic run";
"absorption r = 0.1 as a stand-in" (brief, section 5); "absorption r = 0.1 (stand-in)" (appendix B1).
Also "0.569 rad off in short cells: the reflected wave needs about 3,500 Å of surface to build up"
(brief, section 3).

What is wrong:
- The project labels r = 0.1 TEST_ONLY everywhere else:
  - `reflection_holo/forward/multislice/engine.py:55` ("TEST_ONLY absorption r = 0.1 and 0.05")
    and `:62` (solver comparison "TEST_ONLY r = 0.1");
  - `tools/hpc/supercell_sizing_output.txt:368, :395, :442` ("r = 0.10 TEST_ONLY");
  - B42;
  - the title printed inside `solver_vs_engine.png` ("absorption r = 0.1 (TEST_ONLY)"), directly
    above the caption that says "a stand-in".
- r = 0.1 is not a demo stand-in for a laboratory value. The physical route is frozen-phonon TDS
  plus the 0–0.65 V electronic bracket (B6).
- The section 5 costs and the 3,500 Å depend on it:
  - 3,500 Å is the frozen-phonon ensemble phase run-in at r = 0.1, with the amplitude not
    established (sizing :262, :474).
  - At r = 0.05 the a/4 case needs 3.77 GB and 28 min with a 5,000 Å static lower bound (:480).
  - Without absorption the static run-in is at least 9,000 Å and the plateau is not established
    (:265-267, :483).
  - `docs/05_final_repository_specification.md:399` quotes a build-up scale of order 1,600 Å
    without absorption.

  "Realistic run" therefore overstates.

Replacements:
- Brief, Fig. 1 caption:
  > …200 keV, TEST_ONLY absorption r = 0.1, static lattice, the solver's Doyle–Turner potential in
  > both codes.
- Brief, section 5 heading:
  > 5. Cost of a production-size run and what comes next
- Brief, section 5 first sentence:
  > Exact [100] azimuth, 200 keV, TEST_ONLY absorption r = 0.1 (weaker absorption needs longer
  > cells: at r = 0.05 the a/4 case needs 3.8 GB and 28 min); memory from the engine's own
  > accounting, a lower bound; GPU times are a model until tonight's first GPU runs.
- Brief, section 3, last row:
  > 0.569 rad off in short cells; with TEST_ONLY absorption r = 0.1 the reflection phase settles
  > only after about 3,500 Å of surface (without absorption at least 9,000 Å)
- Appendix, B1 caption:
  > …specular beam, TEST_ONLY absorption r = 0.1, static lattice: …

### M4. "every result passes an independent adversarial review before it is used" (brief section 1)

What is wrong:
- The buried-void numbers that the brief uses were written by T5 at c821862, after re-audit A10a.
- No audit of T5 exists in `docs/agent_reports/` (A10a audited T4; T5 is the fix report,
  "Status: FINAL", self-tested by mutation).
- The headline range changed in T5. T4's reading was "up to 0.0339 rad … 0.0858"
  (`tools/review/t4/buried_torus_analysis_output.txt:235`); T5's is 0.0274–0.0789 rad, 2.6–10.3 %.
  So this headline number has had no independent check.

Replacement:
> Every physical number in the project documents is printed by a committed script, and every result
> is checked by an independent adversarial audit before it is adopted; the latest buried-void
> analysis (T5) is still awaiting its re-audit.

## minor

- **m1. Test count (brief section 1).** "about 1,170 tests" is out of date: 1,502 tests collected at
  c821862 (E11 run); X5 reports 1 failed + 1,477 passed + 8 skipped = 1,486 at 00851da
  (`docs/agent_reports/X5_a9b_fixes.md:258`); 1,165 + 8 was the count around A7/X2. Use "about 1,500
  tests".
- **m2. Solver row (brief section 3).**
  - "explained by the 0.13 Å pixel and by along-beam couplings the solver averages out" should be
    "attributed by review E8 to …". E8 calls the along-beam model difference "not validated"
    (`docs/agent_reports/E8_solver_review.md:372-374`); docs/05 says "E8 attributes it to"
    (`docs/05_final_repository_specification.md:212-217`).
  - The medians hide 5 angles above 0.05 rad (0.051–0.075 rad) and 0.398 rad at [100] 15.0 mrad,
    where |R|^2 is about 1e-5 (`tools/plots/phase4_figures_solver_output.txt:1-8`;
    `docs/08_paper_readiness.md:64`).
  - "37 of 38" is 22/23 + 15/15 (docs/05:209), and the amplitude part of that tolerance has no power
    (E8 M2).
  - Suggested: "median phase difference 0.014 rad at [100] and 0.017 rad at [110] (0.05–0.075 rad at
    five angles); … engine amplitude 3–5 % low, attributed by review E8 to the 0.13 Å pixel and to
    along-beam couplings the solver averages out".
- **m3. Section 3 never states the engine's status.** Add to the last row or below the table:
  "Until this gate passes, multislice step phases are UNVALIDATED." The engine's VALIDATION_STATUS
  (`engine.py:52-62`) and appendix A3 both say so.
- **m4. Plasmon sentence (brief section 4).**
  - Label missing: B38 is a clean-surface transfer and a demo stand-in, not comparable to experiment
    (`docs/model_assumptions.md:64`).
  - "the fringe contrast drops to 0.54" should be "is multiplied by 0.54": exp(-n/2) is a factor on
    whatever the incident contrast is.
  - Numbers correct: n = 1.2462, exp(-n) = 0.2876, exp(-n/2) = 0.5363 (recomputed).
- **m5. Oxide disagreement (brief section 4).**
  - "about 0.86 against 4.45 rad per Å" is right: 1-D 0.8455/0.8729/0.8599 vs 4.4549 rad/Å,
    `tools/review/x5/a9b_c4_nonconformal_output.txt:17-21`.
  - But 0.86 is A9b's 1-D laterally averaged estimate for a sub-layer thickness difference; "a
    propagated two-terrace multislice was not run" (B12, `docs/model_assumptions.md:38`).
  - Suggested: "for a thickness difference smaller than one consumed layer the two engines disagree
    (a 1-D estimate: about 0.86 against 4.45 rad per Å)".
- **m6. "Only an oxide of equal thickness on both terraces leaves the step phase unchanged."** Conformal
  means equal thickness and equal consumed-layer count (B41, `:67`, "Conformal = equal thickness and
  equal consumed-layer count (E9 M2)"). Add "and equal number of consumed Si layers".
- **m7. Two zero-loss numbers side by side.** "29 % of the reflected electrons loss-free" (plasmon)
  and "24–29 % … survives 2 nm" (oxide) invite multiplication. The project forbids it: B7 "never to
  be multiplied with B38"; B38 "its product with the oxide zero-loss value is not a sourced quantity
  (E9 M1)". Add "(alternative models; not to be multiplied)". The 0.236–0.289 value is verified
  (`tools/review/e9_recompute_output.txt:66`; recomputed 0.2358 and 0.2887).
- **m8. "Steps persist under such oxides".** The sources show steps at the Si/oxide interface and on a
  1 nm (thermally grown) oxide (`docs/source_map.tsv:37` SM33;
  `docs/agent_reports/E9_oxide_review.md:540-541`). Say that rather than "such" (1–3 nm plasma)
  oxides.
- **m9. Honda and Ohsawa 1988.** "has imaged monatomic steps" is stronger than the source. E9:78:
  "CONFIRMED (the step attribution is the authors' interpretation, "考えられる"; the surfaces were
  polished wafers, not ion-milled)". Suggested: "(008) reflection microscopy at 200 kV in an ordinary
  TEM showed fringe contrast that the authors attribute to monatomic steps on HF-dipped Si(001) wafers
  (Honda and Ohsawa 1988)".
- **m10. "Tanishiro's published 7π step phase on Si(111) as the benchmark".** docs/08:66 says "OPEN …
  a candidate". L7 (`L7_surface_realism.md:387-388`): "The step height, the sign convention and the
  method of establishing 7π … are not stated". Use "as a candidate benchmark".
- **m11. "Peng–Cowley reflection geometry" (brief section 1).** Peng and Cowley 1986/1988 are
  METADATA_VERIFIED, "none read" (`docs/02_literature_position.md:109-112`,
  `docs/05_final_repository_specification.md:439`). Describe the method instead: "transmission-type
  multislice applied to the Bragg (reflection) case".
- **m12. GPU memory (brief section 5).** Only the oxide figures are called a lower bound. The clean
  figures are also lower bounds: "UNVERIFIED on a GPU, lower bound: cuFFT/cuBLAS workspaces and the
  pool not included" (`tools/hpc/supercell_sizing_output.txt:372, :474`). This is covered by the M3
  replacement ("a lower bound").
- **m13. Appendix subtitle "from a run on the reviewed commit".** The runs date from several commits:
  smoke figures named a1ef2a0; solver and c(4×2) figures from 5a1471d/54de605; torus figures around
  4112842; buried void re-analysed at c821862. Say "from a committed script; the run's commit is
  given in its report".
- **m14. Appendix E1: "a numerical artefact of the atomic potential".** T5 and B42 say "of the
  non-local tails of the engine's transmission function". The caption also omits two caveats: the
  small-cell confirmation used "a criterion set after a first stage whose pre-stated criterion gave
  NOT CONFIRMED", and "the analogy is imperfect (cap-20/cap-30 ratio 1.278 here, 2.637 in the small
  cell)" (OUT:210, :319-320; B42). Suggested: "… attributed, by analogy with a smaller test cell (an
  imperfect analogy, confirmed there only on a criterion set after the first), to a numerical artefact
  of the engine's transmission function; not re-checked in this cell."
- **m15. Two (0,0,8) angles.** The 0.761 Å wrap and the 1.78 wraps per a/4 step (brief section 2,
  C1) hold at the geometric demo angle 16.474 mrad (V0 = 12 V, B1). The multislice, oxide and
  buried-void numbers use 16.1347 mrad (B32), where a wrap is 0.777 Å and a/4 is 1.75 wraps
  (recomputed; `docs/agent_reports/C_calculator_output.txt:195` gives 0.7612 Å at 16.474 mrad).
  State the demo angle once, e.g. "(geometric demo, 16.47 mrad)".

## notes

- n1. "the first GPU runs are scheduled now" should be "planned for tonight" (`docs/08_paper_readiness.md:55, :87`).
- n2. "a static lattice would overstate the (0,0,8) amplitude (factor 1.0 instead of 0.772)" should
  read "the (0,0,8) Debye–Waller factor would be 1.0 instead of 0.772": it is the factor on the
  Fourier coefficient, not on the reflected amplitude. Name the source (Heacock et al. 2021). Value
  recomputed: exp(-B s^2) = 0.7724.
- n3. "phase noise rises by 2.42× and 1.36×" should add "relative to an ideal detector at the same
  dose" (`e10_recompute_output.txt:73, :76`: 1/sqrt(DQE)).
- n4. "inner potential 10.1–11.5 V measured" is two inconsistent measurements, 10.1 ± 0.6 and
  11.5 ± 0.3 V (B7, `:33`).
- n5. Section 2 table: the "True height" column is unsigned while the recovered values are signed;
  write −1.3577 Å for the a/4 steps.
- n6. Section 5 table: "depth" is the cell's extent along the normal including 195–354 Å of vacuum
  (sizing :369, :444, :461). Call it "normal (incl. vacuum)".
- n7. Rung-2 row: r = 0.1 and 0.05 there are TEST_ONLY too (`engine.py:55`).
- n8. Appendix C1: "along the beam the ring is 0.11 resolution elements wide" means the ring's 40 Å
  cross-section. The flank terraces are narrower than the resolution except the crest or bottom
  terrace, 12.4 Å (`docs/agent_reports/T2_torus_pipeline.md:140-147`).
- n9. Appendix A3: the title printed inside `exit_wave_complex.png` shows an older, truncated status
  string ("UNVALIDATED: rung 1 … and rung 3 (continuum null tests) of the docs"). It does not match
  the current VALIDATION_STATUS; the caption is right.
- n10. `docs/08_paper_readiness.md:38` still says the oxide layer's "audit pending" (A8, A9b and A10b
  are done; A10b: "Final for the B41 demo path"). So the brief's "after three audit rounds … for the
  demos" is right and docs/08 is stale. docs/08 has no buried-void row.
- n11. Stale `SP/brief/page-3.png` (11:49) belongs to an earlier 3-page build; the current PDF has
  2 pages.

## Page fit

M1–M3 add about 5 lines to a page that is already full. Suggested trims:
- delete "Convergent illumination is an ensemble of incidence directions, each an independent
  cluster job."
- delete "Provenance manifests record the commit, seeds and versions of every run."
- shorten the "Needed from the laboratory" list to "the inputs of docs/06 (angle, azimuth,
  convergence, miscut, preparation, detector mode and sampling, biprism, EELS of the specular beam,
  temperature, a witness cross-section)".

Re-render and check that page 2 ends above the margin.

## Verified as correct (numbers traced and, where marked, recomputed)

- 200 keV throughout; HF-3300V at UVic; Merlin (Medipix3) named as the UVic detector. No 300 keV
  anywhere. No DOI or page number in either document. The years match `docs/references.bib`:
  - Tanishiro 2003 (TANISHIRO2003);
  - Honda and Ohsawa 1988 (HONDA1988);
  - Paton et al. 2021 (PATON2021);
  - Ramstad, Brocks and Kelly 1995 (RAMSTAD1995).
- Smoke demo (brief section 2, appendix A1):
  - heights +2.7156 ± 0.0165, −1.3576 ± 0.0082 and −1.3580 ± 0.0082 Å (A3b:29; S4:158-160; H3:79);
  - control −0.0037 vs 0.0123 rad (S4:160: −0.0036869, 0.012310);
  - true heights a/2 = 2.71545 and a/4 = 1.357725 Å at a = 5.4309 Å (recomputed);
  - wrap 0.7612 Å at 16.474 mrad (recomputed 0.7612).
- Rung 2: 4.6e-4 and 5.3e-4 vs 1.5e-3 (E1:106); 11 breaks caught (A6:38). Rung 3 moving beam
  1.1e-3 rad and fixed beam 0.569 rad (docs/05:233-234).
- Solver: medians 0.014/0.017 rad (`tools/plots/phase4_figures_solver_output.txt:1, :4`); 19 of 23 and
  12 of 23 (E8:163, :370; `e8_recompute_output.txt:205`); 37 of 38 = 22/23 + 15/15 (docs/05:209).
- Thermal: B = 0.4761(17) Å² at 295.5 K, neutron Pendellösung (B35 `:61`; L6:307; HEACOCK21 in the
  bib); Debye–Waller 0.772 (recomputed 0.7724).
- Plasmons: 1.44 at 200 kV Si(111) (B6 `:32`); 1.246, 0.288, 0.536 (B38); recomputed 1.2462,
  0.2876, 0.5363.
- Oxide:
  - 1–3 nm assumed, 10.1–11.5 V, 24–29 % for 2 nm (B7 `:33`; e9 output :66; recomputed 0.2358 and
    0.2887);
  - 0.53–0.58 Å per Å (B7; recomputed 0.5282–0.5826 from 4.27–4.71 rad/Å at 16.1347 mrad);
  - 0.86 vs 4.45 rad/Å (x5 C4 output);
  - "runs in both engines for the demos, after three audit rounds" (A8, A9b, A10b; A10b:433-441
    "Final for the B41 demo path").
- Detector: 30 % and 74 % (MTF 0.298/0.741 digitised, `e10_recompute_output.txt:48, :51`; Gaussian
  recomputed 0.316/0.750); 2.42× and 1.36× (`:73, :76`; recomputed 2.425/1.361); ≥ 17 px (`:106, :108`;
  recomputed p ≥ 16.3 with the Table-1 Gaussian); Paton 2021 Table 1 Si 200 keV (E10 section 2);
  imaging energy filter (Gatan Quantum) at UVic (E10:57; docs/06 item 21).
- Buried void: 0.03–0.08 rad, 3–10 %, 1,499 Å, 2.5 Å, 1,083/1,624 Å, 1/420 and 1/530 (T5 OUT:23,
  :223, :281, :284, :324; recomputed 417.1 and 533.0); void sites 7166/7083/7123/7031 in the figure
  (T5 OUT:5, :29, :53, :77). Appendix E1 carries the right labels (test-only r = 0.1, unvalidated engine,
  no dose model).
- GPU sizing, all rows (sizing :478-488):
  - 275×11×6,102, 0.23 M, 0.02 GB, 1 s;
  - 291×1,564×6,601, 36.7 M, 3.2 GB, 17 min;
  - 292×3,117×6,601, 73.8 M, 7.7 GB, 61 min;
  - 454×2,221×10,425, 105 M, 7.4 GB, 98 min;
  - oxide 3.4/8.2/7.9 GB same-grid lower bound (recomputed: clean plus one complex64 array of the
    grid = 3.380/8.163/7.918 GB);
  - 8 frozen-phonon realisations.
- Half-torus: 0.11 resolution elements (T2:140; recomputed 40/364 = 0.110); 1.78 wraps (T2:146;
  recomputed 1.7837); flat surface about 0.001 Å rms (T2:166, 0.0006–0.0011 Å); 39.8 %/18.7 %
  measurable and 0 on the ring (T2:130-131 and figure).
- Atom counts: A2 27,000 atoms and box 85 × 10.9 × 1,487 Å (figure title; X3:85 `n_atoms 27000`,
  grid 432 × 0.1961 = 84.7 Å, 48 × 0.2263 = 10.86 Å). C2 547,662 (3,786 removed) and C3 554,721
  (3,273 added) (T1:19; both give the same flat cell of 551,448).
- Appendix D1: c(4×2) from Ramstad, Brocks and Kelly 1995; the figure shows the 90° rotation across
  the a/4 step and none across the a/2 step. Appendix C4: 16.1347 mrad, no absorption, static
  lattice (figure title; T1:122).
- Structure claims: screw and glide relations (S1b:83, :113); h = n·a/4 joint branch rule (B29);
  Kirkland potential for the engine (B32); numerical absorbers (M2).
