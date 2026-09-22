# A2b: re-audit of the fixes for the A2 findings

Status: COMPLETE, 2026-09-22. Agent A2 (code auditor). Only this file was written;
`docs/agent_reports/A2_phase2_code_audit.md` is left unedited. No code, test or config was modified.

Audited state: HEAD `d35b751`. The scope files (`reflection_holo`, `tests`, `configs`, `tools`) are
identical to `ab8031e` (`git diff --quiet ab8031e HEAD -- ...` is clean). The fixes are in `bd654c2` (S3,
report `docs/agent_reports/S3_audit_fixes.md`) and `ab8031e` (CFG-B stand-ins relabelled ASSUMPTION with
B17/B18; B16 added). On HEAD: `venv/bin/pytest -q` -> `527 passed in 11.98s`; the calculator gives
`25/25 checks pass`; `tools/phase1_numbers.py` gives `17/17 checks pass`.

Scratch scripts live in `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/audit/`:
the originals are `e*.py` (unchanged); the copies adapted to the new API (arguments only) and the new
probes are `r*.py`.

## Verdicts

| A2 finding | Verdict | Evidence (this re-audit) |
|---|---|---|
| B1 rocking branch | FIXED, with new problems (N2, N3, N4) | the original `e10` now fails at the removed argument (`TypeError: ... 'max_intercept_offset_cycles'`). With declared sigmas, `r10`: 0 wrong heights in the accepted regime; at the criterion boundary 35 wrong of 19 968 accepted = 1.75e-3, below the reported bound 2.5e-3; std(err)/sigma_h = 1.01. All five A2 regimes are refused (S3's test, re-run in the suite) |
| M1 conjugate sideband | FIXED | `r4_conjugate.py`: radius 0.06 gives +0.500 rad for all five carrier directions; radii 0.3 and inf are REFUSED ("not confined to one side of a line through the origin"). A disc of radius < \|guess\| cannot contain 0, hence no ±q pair; the Nyquist-alias pair is refused; CONJUGATE raises; the trap needs `trap_demonstration=True`. B15 and the code now agree |
| M2 configuration gate | FIXED, with a new bypass (N1) | original `e5`: CFG-B with the 8 null entries deleted -> `MissingProjectInputError ... item 3 (convergence_semi_angle, absent) ...`. Unlinked ASSUMPTION refused; duplicate keys refused; aliases under new names refused (`r5`) |
| m1 validity / NaN | FIXED, with new problems (N5, N6) | `r7`: exact zeros give NaN with a RuntimeWarning; `valid_mask` present; R2 mask kept through ensemble, noise and reconstruction (`r9` block) |
| m2 zero uncertainties | FIXED, residual gap (N7) | `r8`: zeros, sigma_phi >= pi, -pi and a negative wavelength refused. Honest sigma_phi with a vanishing angle sigma gives sigma_h = 5.99e+04 A (honest) |
| m3 B4 metadata | FIXED | `r12`: <100> a/4: "B4 applies for bulk-terminated terraces (d-glide in the incidence plane; SM...)"; <110> a/4: "does not apply (dynamical residual delta; open question 3)"; sweep 144/144 built, `independent-check mismatches: none` |
| m4 CFG-A labels | FIXED | CFG-A geometry labelled ASSUMPTION; a PROJECT_INPUT without an item is refused (`config.py:415-427`, S3 test) |
| m5 units | FIXED | spot check: 16.5 mrad -> (0.0165, 'rad'); 0.05 um -> 500.0 A; 5.4309 A, 200 keV, 12 V unchanged |
| m6 lattice parameter | FIXED | the builder requires `lattice_parameter_A` + label; the original `e2` fails with `missing 2 required keyword-only arguments`; with them, the adapted `r2` reproduces the A2 sign results exactly (9e-8 rad) |
| m7 silent acceptances | FIXED | `r9`: mis-paired None ensemble REFUSED; trap carrier REFUSED; R3 `aperture_passage` required. The R1/R3 passage is still inert and 2 theta_ext is not modelled (declared NOT IMPLEMENTED) |
| m8 provenance | FIXED | `r16`: `diff_head_sha256`, `untracked_files`, `untracked_sha256` recorded; git unavailable -> RuntimeError; thread check recorded ("not enforced", stated) |
| m9 test gaps | FIXED (remaining gaps declared) | new tests are independent (explicit Born sum; measured 10-90 % widths against independent constants; ensemble convergence) and mutation-checked by S3. V0/convergence sensitivity and loader tests still absent (no model or loader) |
| m10 material spelling | FIXED | original `e5b`: "silicon" and "Si " -> "must be a canonical element symbol" |
| NIT -pi | FIXED | `r8`: refused |
| NIT clipping beyond backscattering | FIXED | `r8`: order 300 -> ValueError "beyond backscattering" |
| NIT accessibility `>=` vs `>` | NOT FIXED | `r8`: `accessibility at G.n = 2 dK exactly: True`, whereas SpecularCondition has `K_int > dK`; S3 left it (docs conflict) |
| NIT boundary step int | FIXED | `r12b`: -1.5 -> ValueError |
| NIT bare assert | FIXED | S3 static test; not re-run under `python -O` |
| NIT shallow metadata copy | FIXED | R2 mask survives noise and ensemble (`r9`) |
| NIT wavelength validation | FIXED | `r8`: "wavelength_A must be finite and > 0" |

T1-T25 re-run (`e3_tvalues.py`, unchanged script): every value is identical to A2 (T24 2.35969848, T25
0.000274080549, ...), with the same reference values and tolerances.

## New defects, ranked

### MAJOR

#### N1. The PROJECT_INPUT gate is bypassed by labelling a stand-in with anything except ASSUMPTION, and `assumption_id` is only checked for existence

* Where: `reflection_holo/io/config.py:433` (the stand-in rule applies only when `label == "ASSUMPTION"`)
  and `:452` (`aid not in model_assumption_ids()`, i.e. any existing row is accepted).
* What is wrong. All eight blocking CFG-B inputs (items 3, 4, 5, 7, 8, 12, 13, 15) can be filled with
  non-laboratory values labelled DERIVED_HERE, SECTION_READ, REPRODUCED or METADATA_VERIFIED, with the right
  `item` and nothing else, and the run-level load PASSES. An ASSUMPTION stand-in passes with any existing
  row, including A3 ("(6,-6,6) is a usable reflection", marked False), B2 (lattice parameter) or B17
  (working reflection).
* Why it matters. This is acceptance criterion 5 again. A glancing angle computed from V0 = 12 V (the case
  that docs/06 items 7 and 20 warn about) or a zero convergence passes as DERIVED_HERE with no model-assumption
  row. S3 used exactly this route for (008) before ab8031e (S3 report, "Label decision").
* Reproduction: `r5_gate_bypass.py` (the shipped CFG-B; each null entry filled with the source "audit: not a
  laboratory value"):
  ```
    DERIVED_HERE                                                  : run level PASS; labels ['DERIVED_HERE']; glancing angle quantity (0.01647, 'rad')
    SECTION_READ                                                  : run level PASS; labels ['SECTION_READ']; glancing angle quantity (0.01647, 'rad')
    REPRODUCED                                                    : run level PASS; ...
    METADATA_VERIFIED                                             : run level PASS; ...
    ASSUMPTION without stands_in/assumption_id                    : refused -> ConfigError: CFG-B: ASSUMPTION beam_azimuth_uvw stands in for PROJECT_INPUT item 8: ...
    ASSUMPTION with an unrelated assumption_id 'A3'                        : run level PASS
    ASSUMPTION with an unrelated assumption_id 'B2'                        : run level PASS
    ASSUMPTION with an unrelated assumption_id 'B17'                        : run level PASS
  ```
* Fix: for a parameter whose schema item is a docs/06 laboratory input (CFG-B), accept only three states:
  null PROJECT_INPUT; a PROJECT_INPUT value; or an ASSUMPTION stand-in whose row names that item. Refuse every
  other label, or require `stands_in_for_item` + `assumption_id` for any label other than PROJECT_INPUT. Tie
  each `assumption_id` to its items, either through a table (B1 -> 20, B17 -> 9, B18 -> 14, ...) or by requiring
  the row to state "item N". Add these cases to `tests/io/test_io_config_gate.py`.

### MINOR

#### N2. B16 `sigma_h` excludes intercept systematics that the B16 checks accept: heights biased by 9 to 46 sigma_h

* Where: `reflection_holo/quantification/rocking.py:233` (an intercept offset up to 3 sigma_c is accepted)
  and `:241-245` (h is refit with c fixed at 2 pi n; `sigma_h = 1/(k sqrt(sum s^2/sigma^2))`).
* What is wrong. A constant phase residual delta (the dynamical residual near risers, whose acceptance
  threshold docs/05 criterion 3 proposes at 0.1 rad; a reference-phase offset between terraces; a common
  angle-calibration offset, since `d Delta_phi = -2 k h cos(theta) d theta` is nearly constant over the
  series) passes whenever `|delta| <= 3 sigma_c`. The constrained refit then shifts h by about
  `delta/(k s_mean)`, while `sigma_h` is conditional on an intercept of exactly 2 pi n. `h_free_A` and
  `sigma_h_free_A` (the robust pair) are reported but are not the headline result.
* Reproduction: `r10_b16_adversarial.py` (21 tilts, 20-25 mrad, sigma 0.05 rad declared correctly, h = 10 A;
  4000 trials each):
  ```
  A. accepted regime, 21 tilts, sigma 0.05 (correctly declared), h 10 A: accepted 3987 (correct 3987, WRONG 0 ...); reported sigma_h 0.0010 A ...; mean err +0.0000 A = +0.0 sigma_h; std(err)/sigma_h 1.01
  E. accepted regime + constant residual delta = 0.1 rad: accepted 3958 ...; reported sigma_h 0.0010 A ...; mean err -0.0088 A = -9.2 sigma_h
  E. accepted regime + constant residual delta = 0.3 rad: accepted 3506 ...; mean err -0.0265 A = -27.4 sigma_h
  E. accepted regime + constant residual delta = 0.45 rad: accepted 2374 ...; mean err -0.0398 A = -41.2 sigma_h
  F. accepted regime + common angle offset 0.1 mrad (h 10 A): accepted 1807 ...; mean err +0.0443 A = +45.8 sigma_h
  ```
* Fix: report a systematic term with `sigma_h`, for example `|d|/(k s_mean)` or its 3 sigma_c bound, or make
  the free-intercept pair the headline when the intercept is not tested against an independent zero. State in
  B16 that `sigma_h` assumes zero intercept residual. Add a test with a sub-threshold residual.

#### N3. The B16 wrong-branch bound holds only for correctly declared noise; 31 % under-declaration gives 7x the reported rate

* Where: `reflection_holo/quantification/rocking.py:250` with `CHI2_P_MIN = 1e-3` (`:53`). The bound reported
  in `wrong_branch_probability_bound` is computed from the declared sigmas.
* Reproduction: `r10` (21 tilts, 20-25 mrad, h 3 A, h_max 5 A, 20 000 trials):
  ```
  B. boundary, 21 tilts, sigma 0.32 (sigma_c 1.04 < pi/3), h 3 A: accepted 19968 (correct 19933, WRONG 35 = 1.75e-03 of accepted), ...; wrong-branch bound 2.5e-03; ... std(err)/sigma_h 1.01
  C. as B but TRUE sigma 0.42, declared 0.32 (31 % under): accepted 16903 (correct 16607, WRONG 296 = 1.75e-02 of accepted), refused branch 3097 ...; wrong-branch bound 2.5e-03; ... std(err)/sigma_h 1.32
  D. accepted regime but TRUE sigma 0.07, declared 0.05: accepted 2836 (...WRONG 0...), refused branch 1164; ... std(err)/sigma_h 1.39
  ```
  The chi-square check at p = 1e-3 lets 85 % of the 31 %-under-declared series through. The new test
  `test_underdeclared_noise_is_refused` covers only a 10x under-declaration.
* Why it matters. The declared phase sigma comes from the shot-noise formula (SM12). Drift, charging
  (B8) and reference instability add to the real noise, so under-declaration by tens of percent is the
  expected case, not an edge case.
* Fix: estimate the noise from the residuals and use `max(declared, estimated)` in the branch
  criterion, or require an independent flat-region sigma measurement per hologram. Tighten or document
  the chi-square level. Add a 30 % under-declaration test.

#### N4. |h| > h_max with a commensurate tilt grid: wrong heights are accepted in essentially every trial

* Where: `reflection_holo/quantification/rocking.py:200-210`. The guard uses the declared `h_max`; B16 says
  aliasing is "not detectable".
* Reproduction: `r10b_alias.py` (21 tilts, 0.25 mrad steps from 20 mrad, h_max = 10.5 A):
  ```
  G. |h| = 26.0 A > h_max = 10.5 A (true increment 3.26 rad/step): accepted 622 (correct 0, WRONG 622 = 1.00e+00 of accepted), refused branch 1378, guard 0
  G. |h| = 30.0 A > h_max = 10.5 A (true increment 3.76 rad/step): accepted 1981 (correct 0, WRONG 1981 = 1.00e+00 of accepted), refused branch 19, guard 0
  ```
  The mechanism (DERIVED_HERE): for uniform steps with `s_min/Delta s` close to an integer (here 80), the
  aliased series is exactly linear with an intercept near 2 pi n', so every B16 check passes.
* Why it matters. `h_max` is a prior. For the nm patterned features (item 13) a wrong prior gives a
  confident wrong height. Aliasing IS detectable with incommensurate (non-uniform) tilt spacing, so "not
  detectable" is a property of the grid, not of the method.
* Fix: require, or at least test, a non-uniform tilt set and refuse uniform grids whose aliased solutions
  pass. At minimum, report the aliased alternatives `h +- 2 pi/(k Delta s)`, and correct the B16 wording.

#### N5. The validity-aware Itoh unwrapper stops at the first invalid pixel of column 0 and never restarts

* Where: `reflection_holo/reconstruction/sideband.py:350` (`stop` = first invalid pixel after the start)
  and `:354` (each row stops at its first invalid pixel).
* What is wrong. Any invalid band that crosses column 0 turns everything below it to NaN, including
  fully valid regions. An invalid block at the left edge (for example R2 with a shift towards -axis 1)
  gives no unwrapped pixel at all. No value is invented, but the declared unwrapping returns almost
  nothing, silently apart from the amplitude warning.
* Reproduction: `r7_divide_empty.py` (invalid rows 4-11 of 128):
  `unwrapped NaN count total 15872 ; NaN count rows 40..119: 10240` (of 16 384; the valid rows 12-127 are all
  NaN). `r7b_threshold_unwrap.py`:
  `R2 shift (0.0, -16.0): valid pixels 14336 of 16384; unwrapped finite pixels 0`
  (with shift +16: 14336 of 14336).
* Fix: restart the column path at the next valid pixel (each connected valid segment gets its own offset,
  recorded as ambiguous), or start from the largest valid connected region. Add tests with invalid left
  columns and with an invalid band that crosses column 0.

#### N6. The empty-amplitude threshold is relative to the MEDIAN, which fails once the fringe-free area approaches half the field

* Where: `reflection_holo/reconstruction/sideband.py:560` (`cut = thr * median(|w_empty|)`).
* Reproduction: `r7c_threshold_noise.py` (dose 100 e/px, threshold 0.1, fringes only in the first fraction of
  the rows):
  ```
  overlap 80%: median|w_e| 49.4; inside-overlap rms err 0.011 rad; outside: 256 of 256 flagged VALID, their rms phase error 0.07 rad
  overlap 45%: median|w_e| 13.7; inside-overlap rms err 0.012 rad; outside: 4755 of 5888 flagged VALID, their rms phase error 0.33 rad
  overlap 30%: median|w_e| 3.78; inside-overlap rms err 0.012 rad; outside: 8236 of 8448 flagged VALID, their rms phase error 0.67 rad
  ```
* Why it matters. The biprism overlap is often a band narrower than the recorded field (PROJECT_INPUT
  item 17). Pixels outside it then pass as valid with phase errors 30 to 60 times the in-overlap noise.
* Fix: a threshold against a declared reference level (the carrier amplitude from the empty hologram's
  peak bin, or the median over a declared overlap region), or a noise-based criterion (amplitude against
  the expected sideband noise for the dose). Test it with an overlap of < 50 %.

### NIT

* N7. `reflection_holo/quantification/height.py:66-69`: any positive uncertainty passes, so 1e-300
  still defeats the small-denominator refusal. `r8_edges.py`:
  `sigmas 1e-300, theta 1e-9: ACCEPTED h = -9.979e+05 A, sigma_h = 2e-294 A`. With a realistic sigma_phi the
  returned sigma_h is honest (`5.99e+04 A`). A plausibility floor (for example sigma_theta >= 1 urad), or
  refusing theta_ext below a stated minimum, would close it.
* N8. `reflection_holo/io/config.py:329-330`: "positive" accepts inf and 1e300 (`r5`:
  `glancing_angle_ext = inf mrad: run level PASS, quantity (inf, 'rad')`). Require finite values; a range
  per parameter (angles below pi/2) would also catch unit slips.
* N9. `reflection_holo/io/config.py:89, 288-293`: assumption IDs are read from
  `<package>/../../docs/model_assumptions.md` and cached. This works only in the editable checkout;
  elsewhere every configuration with an `assumption_id` fails, explicitly (ConfigError), not silently.
  Rows added during a session are not seen.

## Adversarial checks requested

* B16 in my regimes: all five A2 regimes are refused, with no wrong height. The wrong-branch bound holds at
  the criterion boundary (1.75e-3 against 2.5e-3) and sigma_h is calibrated for pure, correctly declared
  noise (std/sigma_h 1.01). It does not hold for under-declared noise (N3), for sub-threshold intercept
  residuals (N2) or for |h| > h_max on uniform grids (N4).
* Tolerances and tautology: no tolerance in an existing test changed. Every removed or added assertion line
  in the modified test files is a rename, an added argument or a new refusal. One input changed:
  `test_small_denominator_boundary` now passes `sigma_wavelength_rel` 0 -> 1e-6, with its assertions
  unchanged. T1-T25 values are identical to A2. The new tests are not tautological: Monte Carlo against the
  stated bounds, an explicit Born sum, independent step-response constants, and S3's mutation checks. Coverage
  gaps: no test of a sub-threshold intercept residual, of 30 % noise under-declaration, of aliasing, or of the
  N5/N6 cases.
* New gate bypass: yes (N1). Omission, unlinked ASSUMPTION, duplicate keys, aliases, material spelling and
  TEST_ONLY from files are now refused.

## Commands run (HEAD d35b751; scratch = the audit directory above)

1. `git log --oneline -8; git status --porcelain; git diff --stat fa33ed3 ab8031e -- reflection_holo tests configs tools`
2. `git diff --stat ab8031e HEAD -- <scope>; git show --stat HEAD; cat docs/agent_reports/S3_audit_fixes.md`
3. `git diff --quiet ab8031e HEAD -- <scope>` (clean); `cat -n reflection_holo/quantification/rocking.py`
4. `git diff fa33ed3 ab8031e -- reflection_holo/reconstruction/sideband.py`; `sed -n 1,720p reflection_holo/io/config.py`
5. `git diff fa33ed3 ab8031e -- configs/cfg_b_si001_patterned.yaml`; `grep -n "^| B1[5-8]" docs/model_assumptions.md`
6. `venv/bin/python e5_config_gate.py` and `e5b_material_bypass.py` (originals); `venv/bin/python r5_gate_bypass.py`
7. `venv/bin/python e10_rocking_branch.py` (original: TypeError); `venv/bin/python r10_b16_adversarial.py`; `r10b_alias.py`
8. originals re-run: `e1_independent_values e2_sign_chain e3_tvalues e4_conjugate_sideband e7_divide_empty e8_edges e9_ensemble_pairing e12b_builder_inputs e16_manifest`
   (e3 unchanged values; the others stop at new required arguments or refusals, as quoted)
9. adapted copies: `r1_values.py` (stops at the m2 refusal, expected), `r2_sign_chain.py`, `r4_conjugate.py`, `r7_divide_empty.py` (twice, with DEBUG2 lines), `r12b_builder_inputs.py`
10. `r7b_threshold_unwrap.py`, `r7c_threshold_noise.py`, `r8_edges.py`, an inline e9-derived probe (m7), `r12_structure_sweep.py` plus an inline B4 listing, `r13_shadow_bruteforce.py` (0 mismatches in 159 676 points), `r16_manifest.py`
11. `git diff fa33ed3 ab8031e -- <each modified test file> | grep` (assertion and tolerance lines); `git diff ... test_quant_rocking.py test_carrier_trap.py`; read `tests/quantification/test_quant_rocking_noise.py`
12. inline unit-conversion check (`load_config_dict` + `quantity`); `grep` on `tests/quantification/test_kinematic_sign.py`
13. `venv/bin/pytest -q` -> 527 passed; calculator 25/25; `tools/phase1_numbers.py` 17/17; `grep -n` for line numbers

## NOT RUN

* `python -O` (bare-assert NIT; S3's static test only); `validate_configs` CLI (writes into the repository's
  outputs/); `tools/physics_checks/*`; any engine or dynamical calculation; experimental data (none).
* The adapted `r1_values.py` inversion loop was not rerun with positive sigmas; the A2 inversion check
  is covered by `r2` (full chain, 8 of 8 signed heights).
