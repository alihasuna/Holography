# E4b: verification that review E4 was applied

Status: FINAL, 2026-09-22. Reviewer E4 (adversarial scientific reviewer). This is the only file
written; no reviewed file was edited.

Scope: `git diff 296d0ee 017761d -- README.md docs configs tools/phase1_numbers.py
reflection_holo/structure/si001.py tests/reconstruction/test_self_reference_R2.py`. It covers commits
682c4ba (documents), 9d7a087 and 017761d (code and config items) and 0f0304d (B16, docs/05 section
9.1, the accessibility note). I also checked fc8e949, a B16 edit from A2c committed after 017761d.
`reflection_holo/forward/` and `pipeline/` are out of scope. HEAD at the time of writing is ba22e29.
Since 017761d the only change to the documents under review is fc8e949 (B16); the other changes are
new reports and out-of-scope code. Line numbers refer to HEAD.

Method:
* I recomputed the numbers with my own script (appendix; it uses no package, calculator or test code).
* I ran the suite and the checks in temporary worktrees of 9d7a087 and 017761d, removed afterwards,
  and saved the output below.
* REPRODUCED means executed by me, with the output in the appendix.

## Verdicts

| E4 item | Verdict | Evidence (file:line at HEAD) |
|---|---|---|
| M1 <100> a/4 scope | APPLIED correctly | See note 1 |
| M2 docs/05 section 9.1 | APPLIED with a new problem (Major) | See new problem P1 |
| M3 R2 strip sign | APPLIED correctly | See note 2 |
| m1 four-way tie | APPLIED correctly | docs/03:252-255; source_map.tsv:31 (SM27) |
| m2 carrier rule | APPLIED correctly | docs/03:258-259; docs/05:249 (section 5 item 7) and :342-343 (section 9.1); B15 and SM27 already agreed |
| m3 docs/05 section 4.5, docs/03 section 3 | APPLIED correctly | docs/05:214-217; docs/03:137-138 |
| m4 B16 | APPLIED with a new problem (Minor) | See new problem P2 |
| m5 CFG-B header | APPLIED correctly | cfg_b:4-7 ("13 (not blocking, required here)"; item 11 has no fields); docs/05:363 lists item 11 |
| m6 "see below" | APPLIED correctly | docs/03:95-96 |
| m7 shadow wording | APPLIED correctly | docs/06:28 (item 13: falling and rising edges); docs/05:128 |
| m8 type name | APPLIED correctly | See note 3 |
| m9 source-map test columns | APPLIED with a new problem (Minor) | See new problem P3 |
| n1 102 A provenance | APPLIED correctly | docs/03:164 ("Phase 2 commit 5d59c41"); README.md:28; tests/geometry/test_geom_projection.py:69-71 |
| n2 status lines | APPLIED correctly | docs/03:3-4; docs/05:6-7; docs/06:3; model_assumptions.md:3-4. Nit: "reviews E4" is plural in docs/03:4 and model_assumptions.md:4 |
| n3 B17 external angle | APPLIED correctly | model_assumptions.md:42 |
| n4 B1 item 20 | APPLIED correctly | model_assumptions.md:26 ("Stands in for PROJECT_INPUT item 20") |
| n5 item 11 wording | APPLIED with a new problem (Nit) | See new problem P5 |
| n6 CFG-B mask lengths | APPLIED correctly | See note 4 |
| n7 "must vanish" | APPLIED correctly | docs/05:40-42 (tolerance in configs/benchmarks.yaml; the grid must respect the glide) |
| n8 "monotonic" | APPLIED with a new problem (Nit) | See new problem P6 |
| n9 Delta conditions | APPLIED correctly | physics_conventions.md:50-52. REPRODUCED: 1.0e-4 rad at 2 mrad, 2.0e-4 rad at 1 mrad, 5.09e-5 rad at (004) |
| n10 CFG-A item 9, SM27 status | APPLIED correctly | cfg_a:60, :65 carry no `item` and cite "benchmark definition"; SM27 status (source_map.tsv:31) |

Notes to the table:

1. M1 is applied in every place:
   * docs/03:45-53: every `k_out` in the incidence plane; specular beam; plane wave; off-plane beams
     obey no relation; convergence not analysed; "not forced to vanish by symmetry ... (its value is
     unknown)".
   * docs/06:20 (item 8); model_assumptions.md:29 (B4) and :43 (B18).
   * docs/05:37-42 (criterion 3) and :67 (CFG-B row); source_map.tsv:30 (SM26, claim and validity
     columns).
   * cfg_b:20-25 (description) and :103 (relation).
   * reflection_holo/structure/si001.py:354-360 (`B4_A4_100`, `B4_A4_110`).

   Residual Nit: the SM03 validity column (source_map.tsv:4) still reads "Si(001) a/4 steps only at
   an exact <100> azimuth for bulk-terminated terraces (SM26)", without "specular beam". It defers to
   SM26, so the practical effect is small.
2. M3 is applied: docs/03:238-241 gives the strip as `-Delta` for `s` towards the upper terrace and
   `+Delta` towards the lower one. `tests/reconstruction/test_self_reference_R2.py:91-92` covers
   shifts (+-96, 0) and (+-96, 40) and passes (580 passed at 017761d). No addendum was added to C2.
   That is acceptable: the reports are kept unedited as the record, and docs/03:240-241 says C2
   tested only the first case.
3. m8 is applied: cfg_b:93 now has `single_layer_a4`. The old name fails in the loader
   (tests/io/test_io_cfg_b_text.py). The docs/05:67 row no longer calls the terraces
   "screw-related".
4. n6 is applied: docs/05:67 gives 607 nm and 378 nm. REPRODUCED: 606.95 and 378.41 nm, and
   tools/phase1_numbers.py passes 19/19 at 017761d.

## New problems

P1 (Major; M2). docs/05:323-326, "580 passed at commit 9d7a087 ... the round-2 fixes of S3, verified
by A2c". A2c was written after 0f0304d; it was committed as 90f1423. A2c verifies the round-2 fixes but
also finds new problems:
* G1 (MAJOR): Ali's experiment loads as CFG-A, whose schema pins neither its geometry nor its imaging
  inputs, so the CFG-B gate is avoided altogether.
* G2: the supplier/date rule is a substring match. "not supplied by Ali 2026-09-22" passes.
* G3: TEST_ONLY stand-ins pass at run level for in-memory configurations.
* R1: no validity criterion with `reference_correction="none"`.
* R2 and R3: two Nits.

None of these is in "Open after the fixes" (:352-354). The io/ bullet (:345-349), "a PROJECT_INPUT
item accepts only a supplied value naming the supplier and date or an ASSUMPTION mapped to that
item", is contradicted by G1 to G3. Two smaller points:
* "(no `forward/` package exists)" (:356-357) is false at HEAD: a4f607f adds
  `reflection_holo/forward/contracts.py`.
* 9d7a087 is a snapshot commit. The final round-2 state 017761d also gives 580 passed (REPRODUCED;
  580 also at 9d7a087), so cite 017761d.

Proposed wording: "... 580 passed at 017761d. Verification: A2 (7874c85), A2b (d35b751), A2c
(017761d). Open after A2c: G1 (Major, a Si(001) experiment can be declared as the CFG-A benchmark
and bypass the CFG-B gate), G2 and G3 (the supplier rule is a free-text match; TEST_ONLY stand-ins
from memory pass at run level), R1 (no validity criterion without an empty hologram), and the B16
noise declaration (A2b N3)". Qualify the io/ bullet the same way, and write "no forward engine exists
(`forward/` holds only the interface contract)".

P2 (Minor; m4). B16 (model_assumptions.md:41). The verified parts are:
* the P(|Z| > 3) bound: 2.6998e-3;
* 1.75e-3 and 1.75e-2 from A2b;
* "0 wrong in 3987 accepted": REPRODUCED at 017761d (1993 + 1994);
* "at most about 0.85 sigma_h" for offsets up to 3 sigma_c: own Monte Carlo gives 0.80 at 3.0 sigma_c
  and 0.83 at 3.08 sigma_c, and the prediction |rho| E[z | accepted] agrees within 0.03;
* fc8e949's 0.76, which is exactly 0.32/0.42 = 0.762;
* fc8e949's Gaussian tails: own 3.2e-3 beyond 3 true sigma_h (Gaussian 2.7e-3) and 0 beyond 5.

Two statements are wrong:
* "a dynamical residual ... larger than `3 sigma_c` is refused by the intercept check". It is refused
  only with probability Phi(u - 3), with u = delta/sigma_c. My own implementation of the criterion
  accepts 31 % of series at 3.5 sigma_c (mean height shift 1.14 sigma_h), 16 % at 4 sigma_c
  (1.54 sigma_h) and 2.3 % at 5 sigma_c (2.40 sigma_h). The package's own test output
  (test_quant_rocking_offsets, angle case, u = 3.08) accepts 1817 of 4000.
* "an angle-calibration offset biases it only in second order". This is true before selection: own
  result -2.3e-5 A, or -0.0016 sigma_h, for 0.1 mrad at h = 10 A. But the offset moves the intercept
  by -0.50 rad (-3.08 sigma_c). Then 53 % of series are refused, and the accepted heights shift by
  +0.84 sigma_h (own) or +0.832 sigma_h (S3 test).

Proposed: "... is refused with probability Phi(|delta|/sigma_c - 3) (50 % at 3 sigma_c, 84 % at 4,
99.9 % at 6). The accepted series are shifted by up to 1.5 sigma_h at 4 sigma_c. An angle offset
d theta acts, after selection, as an intercept offset of about -2 k h d theta."

P3 (Minor; m9). The m9 items are applied:
* SM01-SM09 "reference: calculator (25/25)" (source_map.tsv:2-10);
* the SM01 E-review note;
* SM13 split status (:17);
* SM15 tilt_test (:19).

The round-2 rewrite is not recorded. SM05 (:6) lists neither test_quant_rocking_offsets.py nor
test_quant_rocking_alias.py. SM05, SM12 (:16) and SM27 (:31) still report "527 passed, commit
bd654c2", which tested the round-1 rocking.py and sideband.py. Proposed: add the round-2 tests
(including test_validity_round2.py for SM12) and "580 passed at 017761d".

P4 (Nit; accessibility note, physics_conventions.md:67-69). "At equality the exit is exactly grazing
(`theta_out` = 0)". REPRODUCED: at G.n = 2 dK both K_int equal dK, so the incidence and the exit are
both exactly grazing (0, 0). At 1.000001 x 2 dK the largest external angle is 0.017 mrad. The reason
given ("not usable") argues for `>`, as A2c D2 also notes. The decision itself is harmless because
equality is measure zero. The relation 2 dK = 2 k sin(theta_c) holds to 3.491e-5 relative, which
agrees with the note's figure. Proposed: "At equality both beams are exactly grazing (theta_in =
theta_out = 0): propagating, not evanescent, but unusable. The guard keeps `>=` (existence of
propagating beams); `SpecularCondition` uses `>`; the difference is a measure-zero case."

P5 (Nit; n5). docs/06:26: "at an exact <100> azimuth both types are at 45 degrees and the clause is
not needed". Add "for the specular beam of bulk-terminated terraces". For off-plane beams or a
reconstruction the terrace types still matter (M1).

P6 (Nit; n8). docs/03:54-55 has "monotonic". B4 (model_assumptions.md:29) and SM26
(source_map.tsv:30) still say "alternating in sign along a staircase".

P7 (Nit). docs/05:67: the pasted scope clause gives "...never by a translation; For the specular
beam ... (open question 3).)". It has a capital letter after a semicolon and several sentences
inside a parenthesis in a table cell.

## Verified as correct

* The suite passes, REPRODUCED in worktrees: 580 passed with 6 warnings at 9d7a087 and at 017761d.
  The warnings are the intended aliasing warnings.
* At 017761d:
  * calculator 25/25; phase1_numbers 19/19 (README.md:63);
  * q1 41/41, q2 21/21, q3 7/7;
  * rocking noise, offset and alias tests: 21 passed. On the designed series, the aliases at 26, 30
    and 40 A are refused in 2000 of 2000 trials each.
* The fc8e949 wording of B16 (phase-branch-index rate; sigma_h 0.76; Gaussian tails) is consistent
  with my Monte Carlo.

## Appendix: script and output

Script: `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/e4b/e4b_checks.py`
(run with `venv/bin/python`).

```
(1) CFG-B 10 nm mask lengths h/tan(theta_ext):
    (0,0,8): theta_ext = 16.4743 mrad, 10 nm -> 606.95 nm
    (0,0,12): theta_ext = 26.4205 mrad, 10 nm -> 378.41 nm
(2) accessibility G.n >= 2 dK:
    G.n = 2 dK x 1.000000: (theta_in, theta_out) ext at the ends and the symmetric point [mrad] = (0.000, 0.000), (0.000, 0.000), (0.000, 0.000)
    G.n = 2 dK x 1.000001: (theta_in, theta_out) ext at the ends and the symmetric point [mrad] = (0.000, 0.017), (0.012, 0.012), (0.017, 0.000)
    G.n = 2 dK x 1.010000: (theta_in, theta_out) ext at the ends and the symmetric point [mrad] = (0.000, 1.680), (1.185, 1.185), (1.680, 0.000)
    2 dK vs 2 k sin(theta_c) (sin theta_c = dK/k_int): relative difference 3.491e-05
(3) B16 regime: 21 tilts 20-25 mrad, sigma 0.05 rad: sigma_c = 0.1626 rad, sigma_h = 0.01439 A, corr(c, slope) = -0.9977
    u = 0.000 | 3985 of 4000 accepted | mean(h err)/sigma_h -0.015 | prediction 0.000 | P(accept) 0.997
    u = 1.000 | 3904 | -0.051 | -0.055 | 0.977
    u = 2.000 | 3364 | -0.298 | -0.287 | 0.841
    u = 2.768 | 2406 | -0.652 | -0.655 | 0.592
    u = 3.000 | 1985 | -0.804 | -0.796 | 0.500
    u = 3.083 | 1838 | -0.833 | -0.850 | 0.467
    u = 3.500 | 1233 | -1.140 | -1.139 | 0.309
    u = 4.000 |  636 | -1.540 | -1.522 | 0.159
    u = 5.000 |   93 | -2.398 | -2.368 | 0.023
    angle offset 0.1 mrad (h = 10 A): accepted 1870 of 4000, mean(h err)/sigma_h = +0.843
    angle offset 0.1 mrad, noise-free free fit: h error = -2.255e-05 A (-0.0016 sigma_h; second order), intercept shift -0.5012 rad = -3.083 sigma_c
(3b) under-declared noise (true 0.42, declared 0.32): accepted 16931 of 20000; reported sigma_h = 0.0921 A, true sigma_h of the free slope = 0.1209 A (ratio 0.762); scatter of the accepted h = 0.1167 A; fraction |err| > 3 true sigma_h = 3.25e-03 (Gaussian 2.70e-03), > 5 true sigma_h = 0.0e+00
```
(Rows of (3) condensed from the verbatim output; the refusal reasons, mostly the intercept check, are
in `e4b_checks_output.txt`.)

Runs (temporary worktrees, package imported from the worktree, removed afterwards):
* `pytest -q` at 9d7a087 and at 017761d: `580 passed, 6 warnings`.
* At 017761d:
  * `tools/phase1_numbers.py`: 19/19, printing `10 nm, (0,0,8) 606.95` and `(0,0,12) 378.41`;
  * calculator 25/25; q1 41/41, q2 21/21, q3 7/7;
  * `pytest -q -s` on the three rocking test files: 21 passed. Noise regimes accepted 1993 and 1994
    with 0 wrong. The offsets test, angle case: `u = -3.083 sigma_c; accepted 1817 of 4000 ... mean err
    +0.832 sigma_h`.
