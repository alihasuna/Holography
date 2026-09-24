# X7 - Fixes after the re-audit A12 of X6 (item-12 oxide label policy of comparison runs)

Agent X7, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`, HEAD c8f2d1a when
work started. Status: FINAL (written incrementally; final status at the end).

Input, read in full: `docs/agent_reports/A12_X6_reaudit.md` with its scratch (`SP/a12/`, SP =
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`),
`docs/agent_reports/X6_a10b_fixes.md`, rows B7, B12, B43 of `docs/model_assumptions.md`, item 12 of
`docs/06_project_inputs_required.md`, and the orchestrator's four decisions.

Rules kept: no docs/ file edited except this report; no other report edited; nothing committed;
nothing written under outputs/; `scripts/hpc/alliance/` and the buried-torus files untouched;
scratch in `SP/x7/`.

Baseline before any change (7 oxide files: the three a10b files, the a9b structure and pipeline
files, `tests/pipeline/test_oxide_pipeline_a8_fixes.py`, `tests/structure/test_oxide_structure.py`):
`381 passed in 10.13s` (`SP/x7/baseline_oxide.txt`).

## Progress log

* (12:43) reading done; baseline run; design follows.
* (13:05) code changed: `pipeline/config.py` (allowlist `MEASUREMENT_METHODS` with
  `allowed_measurement_methods`, NFKC/ASCII rule, broadened refusal list, reference form, date floor
  and supply-date bound, overflow catch, `nearest_count_variant` and the variant note in the item-12
  record), `structure/oxide.py` (quadrature for standard uncertainties, bounds on each uncertainty,
  `_counts_between` guard, `nearest_count_variant`, exact-token qualifier check), `forward/cell.py`
  (comment). Fixtures of X4, X5 and X6 migrated (section 3). `tools/review/x7/x7_oxide_numbers.py`
  written and run (output saved). The 7 oxide files: `381 passed in 10.61s`.
* (13:10) new tests written: `tests/pipeline/test_oxide_pipeline_a12_fixes.py` (448),
  `tests/structure/test_oxide_structure_a12_fixes.py` (54); `tools/review/x7/x7_parity_variants.py`,
  `x7_record_probe.py` written and run; the B41 demo bit-identity rerun with X6's script (26/26 in both
  engines); `tools/review/x7/mutate_x7.py` started (39 reversions and a control).
* (13:22) last code change (a comment of `_MAX_COUNTS_BUILT`; its bound is now printed); final
  mutation run, forward directory run; then the structure, io and pipeline directories, the
  bit-identity and the scripts rerun on the final code (sections 5-7).

## 1. Findings: what was done

Line numbers refer to the working tree at the end of X7. Each fix is guarded by a test that fails
when the fix is reverted (section 5).

| A12 finding (decision) | status | code | tests |
|---|---|---|---|
| M1 allowlist (decision 1) | FIXED as decided. The method field must be `<id>` or `<id>: <details>` with an id of the table `MEASUREMENT_METHODS` (id -> parameters it can measure, what it is) that measures the parameter; `allowed_measurement_methods` states the table in its docstring. V_ox and the a-Si potentials: `offaxis_holography_wedge`, `rheed_rocking_curve_fit`, `cbed_rocking_curve_fit`, `reflection_rocking_curve_fit`, `other_measurement` (details of at least `MEASUREMENT_OTHER_MIN_WORDS` = 8 distinct words of three or more letters, which also pass the refusal list); V'_ox: `eels_inelastic_mean_free_path`, `energy_filtered_intensity_ratio`; w_v: `xrr_fit`, `cross_section_tem_profile`, `afm_surface`; w_i: `xrr_fit`, `cross_section_tem_profile`. A method text naming ellipsometry is refused for w_v and w_i. Stated details must themselves have the form of a field (not a placeholder or bare value) | `pipeline/config.py:1050-1095` (comment, table, constants), `:1312-1338` (`allowed_measurement_methods`), `:1402-1433` (`_measurement_method`) | pipeline a12 file: allowlist table, 50 (id, parameter) cases, 14 non-id methods, `other_measurement`, ellipsometry |
| M1 second layer (decision 1) | FIXED. Every text field is NFKC-normalised; any character that is then not printable ASCII is refused and named (code point and Unicode name). The refusal list `_MEASUREMENT_REFUSED` runs on the lower-case words (every run of characters other than a-z, 0-9 replaced by one space, so `not_measured`, `not-measured`, `NOT   MEASURED` read alike): negations anywhere (not, never, no, none, nothing, without, cannot, n't forms, un-/non- before measur and similar stems, notmeasured, six foreign negations), placeholders (missing, absent, NaN, null, TBD, FIXME, fill in, later, repeated letters, ...), origin words of unmeasured values (estimat*, guess*, calculat*, computed, simulat*, DFT, density functional, ab initio, first principles, scattering factor*, Doyle-Turner, Weickenmeier, Lobato, Kirkland, independent atom, IAM, assum*, model*, theor*, nominal, literature, textbook, handbook, Wikipedia, typical, extrapolat*, interpolat*, deriv*, demo, stand-in, TEST_ONLY, copied, taken from, value from), row ids (`B43`, `B 43`, `B-43`; not "Phys. Rev. B 45"), report ids (`E9`) and "out:NNN"; `_MEASUREMENT_REFUSED_RAW` refuses "?", "n/a" and paths into this repository. Runs of whitespace are collapsed in the stored text. Field-name echoes (method, instrument, reference, record, date, value, fit, internal, notebook, report, sample text) are placeholders. The list fails closed | `:1096-1142` (lists), `:1347-1399` (`_measurement_form`, `_measurement_text`) | pipeline a12 file: 98 texts (A12 D1 and the decision's list) x 3 fields, 5 look-alikes by name, NFKC normalisation of a genuine record, field-name echoes |
| m1 reference, dates (decision 1) | FIXED. Reference: a DOI must carry prefix and suffix (`10.NNNN/...`), a URL a host with a dot, and besides schemes, prefixes and filler words (`_REFERENCE_FILLER`) at least 3 letters or digits remain; a path into the repository is refused. Date: not before `MEASUREMENT_DATE_FLOOR` = 1990-01-01, not after the item-12 `supplied_on` (the run date bound is kept and checked first). Every refusal of a record states "the gate cannot verify a measurement record, only require one" | `:1144-1151`, `:1436-1455` (`_measurement_reference`), `:1458-1490` (`_measurement_date`), `:1493-1541` (`_oxide_measurements`, now given the item-12 record for its supply date) | pipeline a12 file: 29 refused and 7 accepted references, 6 refused and 3 accepted dates, the statement in 13 kinds of refusal |
| m2 quadrature (decision 2) | FIXED as decided. `uncertainty_kind: standard`: the nominal depth -+ sqrt(c_t^2 + c_rho^2 + c_a^2) with c_i = sensitivity x 2 u_i (first-order propagation; the a-Si term one-sided below: min(2 u_a, t_a)); `half_width`: the box corners as before (their width is exactly the linear sum; bitwise the X6 arithmetic). The interval records `combination` and `combined_half_width_layers`. A12's example (1 A, 0.05 g/cm^3, 0.1 A, standard): before 5.587-7.626 layers, [6, 7, 8], refused; after 5.789-7.233, [6, 7]. Coverage check printed: 95.45 % analytic; Monte Carlo of the exact depth 95.44 % (a-Si 5.0 +- 0.5 A, no clipping), 95.64 % (a-Si exactly 0), 95.27 % (a-Si half-normal below the detection limit); X6's box covered 99.89, 99.45 and 99.53 % | `structure/oxide.py:132-149` (comment, `COVERAGE_STATEMENT`), `:632-739` (`item12_count_interval`) | structure a12 file (16 cases against an independent formula and the printed output; half-widths equal X6's printed lines; the example; one-sided a-Si; coverage) |
| n1 bounds, overflow (decision 4) | FIXED. Each uncertainty is bounded (`UNCERTAINTY_BOUND_STATEMENT`): its interval half-width below the thickness or density it belongs to (as before) and its depth contribution below 2 layers of a/4 (a/2 = 2.7155 A): at 2.0 nm, 2.20 g/cm^3, standard: u_t < 3.0752 A, u_rho < 0.3383 g/cm^3, u_a < 1.3577 A; half-widths twice these. Why: a contribution of two layers or more always gives at least three counts, which the ruling refuses, so the bound refuses no record that would otherwise run (tested at the bound against an independent formula); it keeps an absurd value from building the list (A12's 1e9 and 1e300 A are now OxideSpecError / PipelineConfigError naming the bound). Also: `_counts_between` refuses a non-finite depth or more than 16 counts before any list is built (covers X5's `consumed_count_interval`); `OverflowError`/`MemoryError` are caught in `item12_count_interval` and in the pipeline and become configuration errors with the bound statement | `oxide.py:150-161`, `:606-629` (`_counts_between`), `:632-739`; `config.py:1695-1701` | structure a12 file (bounds for 3 quantities x 2 kinds, 10 phases at the bound, list guard, monkeypatched errors); pipeline a12 file (6 absurd values, monkeypatched errors) |
| m3 variants (decision 3) | FIXED as decided. `forward/cell.py` comment corrected. The item-12 record's `parity_variant` and the structure's `consumed_layers_parity_record` carry `nearest_count_variant` (`oxide.nearest_count_variant`); the record's note adds "at most 1.5 a/4 ..., an effect not computed. Only the multislice engine distinguishes the variants". A12 D6/D7 reproduced by a committed script: geometric 26 of 26 arrays byte-identical; multislice 5 of 26 byte-identical, exit_psi_r0 max difference 0.795 (max 0.619), exit_x_A shifted by 1.355 A. The physical effect of the overlap was NOT computed | `cell.py:286-290`; `oxide.py:172-186`, `:851`; `config.py:1944`, `:1953-1959`; `tools/review/x7/x7_parity_variants.py` | pipeline a12 file (record, note; geometric byte-identity run test); structure a12 file (record, comment text) |
| n4 exact token (decision 4) | FIXED. A DERIVED_HERE count label of a variant must contain the qualifier of its parity exactly once and no other "parity variant" text (regex tokens `_PARITY_VARIANT_WORDS`, `_PARITY_VARIANT_QUALIFIER`); the no-variant check uses the same token | `oxide.py:501-542` | structure a12 file (6 labels, A12's D2b label first) |
| n2 test gap (A12 O3) | FIXED: `test_standard_uncertainty_enters_twice` asserts the kind handed to the structure | test only | the test |
| n3, n5 | not in the decisions; unchanged | | |
| n6, n7 | in the proposed texts (section 8) | | |

## 2. Design notes and choices for the orchestrator

* **Format of the method field.** "Name an id" is implemented as: the text before the first colon,
  stripped, equals an id exactly (lower case, underscores); details after the colon are optional
  except for `other_measurement`. `XRR`, `xrr fit`, `XRR_FIT` are refused (tested). The record
  keys stay {method, instrument, date, reference}; the stored method keeps the id and the details.
* **`other_measurement` is offered for V_ox and the a-Si potentials only**, as the decision lists
  it under V_ox. V'_ox and the widths have no free-text escape.
* **ASCII after NFKC.** NFKC maps compatibility forms (no-break and thin spaces, fullwidth letters,
  ligatures) to ASCII, which are then accepted and stored normalised; everything else outside
  printable ASCII is refused, including accented letters in author names ("Muller" must be written
  without the umlaut). This closes A12's look-alike and invisible-character cases and the
  other-language texts that use accents or other scripts.
* **Fail closed.** `tools/review/x7/x7_record_probe_output.txt` lists genuine-looking texts that are
  refused and must be rephrased: "JEOL model JEM-2100F", "Titan, not aberration corrected", "lab
  book No. 5, p. 12", "V0 derived from the phase slope", "estimated uncertainty 0.2 V", "two-layer
  model fit", "Kirkland group report", a paper title containing "not". "non-contact" AFM, "HAADF-STEM,
  erf fit", "Phys. Rev. B 45, 1234 (1992)" are accepted.
* **Residuals (the gate cannot verify a record).** Printed in the same output as ACCEPTED:
  well-formed nonsense in the instrument and reference ("abc", "test", "Doe", "#123"), the id alone
  or with nonsense details ("offaxis_holography_wedge: abc"), and ASCII digit-for-letter
  substitutions ("n0t measured", "m0del value"; a deliberate evasion, not in the decision). A
  reference rule requiring a digit, or an instrument allowlist, would narrow the first group; not
  implemented.
* **Quadrature is first order.** The product term of f(rho) t, f u_t u_rho / rho = 0.0100 A =
  0.0074 layer at u_t = 1 A, u_rho = 0.05 g/cm^3 (u_c = 0.3647 layer), is omitted (printed). The
  Monte Carlo of the exact depth shows the effect on the coverage is within its standard error
  (0.015 %).
* **A detection limit as a standard uncertainty** enters the upper side as 2 u_a in quadrature
  (A12-n6); stated in the proposed docs/06 text.
* **Bounds.** Depth contributions below two layers are a consequence of the ruling that refuses
  more than two counts, not a new physical limit. X5's `consumed_count_interval` (kept for X5's
  script) has no depth bound but is guarded by `_counts_between`.
* **Demo manifests.** The B41 arrays are bitwise unchanged (section 6). The item-12 record of the
  demo manifests differs from X6's in one value only: `measurement_rule` now names the allowlist
  (`SP/x7/item12_record_diff.txt`).
* **X6's committed script.** `tools/review/x6/x6_oxide_numbers.py` now prints the quadrature
  intervals for its standard cases and the new coverage statements; its saved output keeps X6's
  box and is no longer the reference for them (X7's output is; section 3). Its half-width lines
  and every other number are reproduced. `tools/review/x6/mutate_x6.py`'s replacement for Y24 no
  longer applies to the rewritten interval code (X6's record, not rerun).

## 3. Existing tests changed on purpose (none weakened; no tolerance changed; none skipped)

After the code change and before the migration, `111 failed, 270 passed in 11.90s` on the 7 oxide
files, as expected (the list was printed in the session, not saved): 103 tests whose record
fixture named no method id (every instrument, reference and date case then fails at the method
first), and 8 that asserted X6's box for standard uncertainties. Migrated as follows.

* Record fixtures now name an id of the allowlist (decision 1):
  * `tests/pipeline/test_oxide_pipeline_a10b_fixes.py`: `REC.method` =
    "offaxis_holography_wedge: TEST: fabricated off-axis electron holography of a witness wedge".
    `test_every_project_input_model_parameter_needs_a_record` gives each of the four parameters a
    record of its own allowlist (`REC_BY_PARAMETER`: EELS, XRR, cross-section STEM) and asserts
    each label in full (the V_real label as a literal).
  * `tests/pipeline/test_oxide_pipeline_a9b_fixes.py`: `MEAS_REC.method` the same id prefix.
  * `tests/pipeline/test_oxide_pipeline_a8_fixes.py::test_comparison_refuses_per_parameter_stand_ins`:
    per-parameter records (EELS for V_imag, XRR for the widths). The assertion (V_real B41 named) is
    unchanged.
* Standard uncertainties in quadrature (decision 2):
  * `tests/structure/test_oxide_structure_a10b_fixes.py::test_interval_matches_the_printed_cases`
    parses X7's saved output instead of X6's (same regular expression, same cases; the half-width
    lines of the two outputs are equal, asserted by a new test).
  * `test_the_uncertainty_kind_sets_the_coverage` asserted that 1 A, 0.05 g/cm^3, 0.1 A as standard
    uncertainties equal the box of the doubled half-widths ([6, 7, 8]). It now asserts the printed
    before (5.587-7.626, [6, 7, 8]) and after (5.789-7.233, [6, 7]) values, equal boxes, and that
    the coverage statements name quadrature and the worst case.
  * `test_parity_variant_interval_refusals`, the "spans 2 rounding boundaries" case, and
    `tests/pipeline/test_oxide_pipeline_a10b_fixes.py::test_interval_of_more_than_two_counts_is_refused`:
    the standard case of three counts is now a-Si 0 +- 0.5 A (printed [6, 7, 8]); X6's 0.1 A gives
    [6, 7]. The half-width case and every assertion are unchanged.
  * `test_standard_uncertainty_enters_twice`: "6.380-6.776" became the printed "6.416-6.675"; it
    also asserts both printed lines and, for A12-n2, that the structure receives the kind
    "standard".

## 4. Numbers and the committed scripts that print them

All numbers of this report and of the proposed texts come from these saved outputs (DERIVED_HERE
from the code, with first-principles checks; the uncertainties are illustrative TEST values):

| number | printed in |
|---|---|
| a/4 = 1.357725 A, a/8 = 0.6789 A, a/2 = 2.7155 A, 1.5 a/4 = 2.0366 A; 0.3252, 0.1478, 0.7365 layer per unit | `tools/review/x7/x7_oxide_numbers_output.txt`, first two sections |
| A12's example: before 5.587-7.626 layers, [6, 7, 8] (equal to X6's printed line); after 5.789-7.233, half-widths -0.7144 / +0.7294 layer, [6, 7]; symmetric 5.774-7.233 (A12's value) | same, section "the example of re-audit A12" |
| 95.45 %; Monte Carlo 95.44 / 95.64 / 95.27 % against the box's 99.89 / 99.45 / 99.53 %; standard error 0.015 %; product term 0.0100 A = 0.0074 layer, u_c = 0.3647 layer | same, section "coverage check" (2 000 000 draws, seed 20260924) |
| the 16 interval lines (both kinds, 8 cases), e.g. 6.416-6.675 for 0.1 A, 0.01 g/cm^3, 0.1 A standard; the a-Si 0.5 A standard case [6, 7, 8] | same, section "item12_count_interval" |
| bounds u_t < 3.0752 A, u_rho < 0.3383 g/cm^3, u_a < 1.3577 A (standard), 6.1504 A, 0.6765 g/cm^3, 2.7155 A (half-width); the refusals of 1e9, 1e300, 1e308 A | same, section "A12 n1" |
| nearest_count_variant 'upper'; +0.6838 A (lower, 6), -0.6739 A (upper, 7) | same, section "A12 m3" |
| geometric 26 of 26 byte-identical; multislice 5 of 26, exit_psi_r0 0.795 (max 0.619), exit_x_A 1.355 A | `tools/review/x7/x7_parity_variants_output.txt` (runs in `SP/x7/pv/`) |
| the allowlist, 8 words, 3 letters or digits, 1990-01-01; residual and fail-closed texts | `tools/review/x7/x7_record_probe_output.txt` |

## 5. Reverting each fix makes a test fail (mutations)

`tools/review/x7/mutate_x7.py --work SP/x7/mut` (adapted from X6's script) reverts each fix in a
scratch copy of `reflection_holo/`, `tests/`, `configs/`, `tools/` and `pyproject.toml`, a throw-away
git repository deleted after its run, and runs 9 files: the two a12 files, the three a10b files,
X5's a9b pipeline and structure files, `tests/pipeline/test_oxide_pipeline_a8_fixes.py` and
`tests/structure/test_oxide_structure.py`. Every copy imported its own package ("package in the
copy: True", 40 of 40). Saved output of the final run on the final code:
`tools/review/x7/mutate_x7_output.txt`. A preliminary run on the code before the last comment
change (`_MAX_COUNTS_BUILT`) gave the same counts for every reversion (`SP/x7/mutate_run_preliminary.txt`).

| mutation (reverts) | result (final run) |
|---|---|
| W0 control | 883 passed in 18.89s |
| W1 M1: allowlist off (any method text accepted) | 11 failed |
| W2 M1: per-parameter check off | 34 failed |
| W3 M1: ellipsometry accepted for widths | 1 failed |
| W4 M1: other_measurement word minimum off | 1 failed |
| W5 M1: details after the id not checked | 4 failed |
| W6 M1: word patterns off | 276 failed |
| W7 M1: negations back to X6's forms | 34 failed |
| W8 M1: origin words estimat*, guess*, comput* removed | 19 failed |
| W9 M1: row ids without separator only (X6) | 9 failed |
| W10 M1: "Phys. Rev. B 45" refused (lookbehind removed) | 1 failed |
| W11 M1: ASCII rule off | 11 failed |
| W12 M1: no NFKC | 1 failed |
| W13 M1: whitespace not collapsed | 1 failed |
| W14 M1: allowlist error without "cannot verify" | 49 failed |
| W15 M1: record rule without the allowlist | 1 failed |
| W16 m1: repository paths accepted | 5 failed |
| W17 m1: DOI form off | 1 failed |
| W18 m1: URL form off | 1 failed |
| W19 m1: token beyond prefix off | 6 failed |
| W20 m1: date floor off | 5 failed |
| W21 m1: supply-date bound off | 2 failed |
| W22 m1: supply date not passed to the check | 2 failed |
| W23 m1: field-name echoes accepted | 8 failed |
| W24 m2: box for standard uncertainties (X6) | 17 failed |
| W25 m2: a-Si term symmetric below | 17 failed |
| W26 m2: linear sum inside the root | 17 failed |
| W27 m2: X6's coverage statement | 2 failed |
| W28 n1: depth bound off | 12 failed |
| W29 n1: list guard off | 1 failed |
| W30 n1: non-finite guard off | 1 failed |
| W31 n1: structure catch of OverflowError/MemoryError off | 2 failed |
| W32 n1: pipeline catch off | 2 failed |
| W33 n1: thickness bound message without the bound statement | 2 failed |
| W34 m3: item-12 record without nearest_count_variant | 2 failed |
| W35 m3: structure record without nearest_count_variant | 2 failed |
| W36 m3: record note without the engine statement | 2 failed |
| W37 m3: cell.py comment restored | 1 failed |
| W38 n4: substring qualifier check (X6) | 4 failed |
| W39 n2: kind forced to half_width in the spec (A12's O3) | 2 failed |

The names of the failing tests are in the saved output.

## 6. The B41 demo path is bitwise unchanged

`tools/review/x6/x6_demo_bitid.py` (X6's script, unchanged) ran on the final code for both demo
variants; its output with the commands is saved as `tools/review/x7/x7_demo_bitid_output.txt`. Run
outputs are in `SP/x7/pipe/`, not under outputs/; the references are X6's, A10b's and A9b's saved
runs in the session scratchpad.

* Geometric `oxide_2p0nm` (3.9 s): +2.7153 +- 0.0165, -1.3578 +- 0.0082, -1.3575 +- 0.0082 A;
  arrays 26 of 26 bitwise identical to X6's, A10b's and A9b's runs; labels, headline and
  spec_sha256 (094102ed...) equal to X6's; the item-12 record has X6's keys.
* `multislice_tiny_oxide_2p0nm` (16.3 s): 26 of 26 arrays bitwise identical to X6's, A10b's and
  A9b's runs.
* The item-12 record of both manifests differs from X6's in `measurement_rule` only (text:
  it now names the allowlist; `SP/x7/item12_record_diff.txt`).
* `git status --short outputs/` is empty.

## 7. Test runs (verbatim last lines)

Command: `OMP_NUM_THREADS=2 PYTHONPATH=. venv/bin/python -m pytest -q -p no:cacheprovider -rfs
<target>`, on the final code (logs `SP/x7/run_*_final.txt`, `SP/x7/run_forward*.txt`).

    oxide files (the 14 test_oxide_* files of structure, forward_geometric, pipeline and forward
      except the heavy tests/forward/test_oxide_multislice.py, which runs in the forward directory,
      plus tests/io/test_io_config_stand_ins.py):
                     1003 passed in 31.49s
    tests/structure: 505 passed in 33.56s
    tests/io:        128 passed in 1.37s
    tests/pipeline:  835 passed in 188.70s (0:03:08)
    tests/forward:   SKIPPED [2] tests/forward/test_null_readout_known_answer.py:225: L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1
                     SKIPPED [1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1
                     191 passed, 3 skipped in 588.76s (0:09:48)

The forward run (13:22-13:32 UTC) ran concurrently with the final mutation run; it collected T5's
buried-torus test file as it is, not mine and not touched. Earlier runs on intermediate code:
baseline 381 passed; after the change, before the migration, 111 failed, 270 passed (section 3);
tests/pipeline 835 passed in 186.97s and tests/structure 505 passed (before the last comment
change).

The committed scripts reproduce their saved outputs on the final code:
`x7_oxide_numbers.py` and `x7_record_probe.py` (rerun and diffed, identical);
`x7_parity_variants.py` (rerun, identical except the run times); `tools/review/x5/x5_oxide_numbers.py`
(rerun, identical: X5's function is unchanged). `tools/review/x6/x6_oxide_numbers.py` differs from
its saved output in the standard-uncertainty lines and the coverage statements only, by decision
(section 2).

## 8. Proposed text for docs/06 item 12 and rows B7, B12, B43 (for the orchestrator)

Base: the wording at HEAD c8f2d1a (A12's interim wording in B7 and B43 included). Numbers:
`tools/review/x6/x6_oxide_numbers_output.txt` (per-unit rates), `tools/review/x7/x7_oxide_numbers_output.txt`,
`x7_parity_variants_output.txt`, `x7_record_probe_output.txt`. B41 needs no change.

**docs/06 item 12.** Replace the passage from "for the oxide thickness, its density and the
thickness of any amorphous Si under it" up to "a comparison run with amorphous Si needs its record
(re-audit A10b M2, m1)." with:

"for the oxide thickness, its density and the thickness of any amorphous Si under it (for a
measured absence: the detection limit), the uncertainty of each and whether the three are standard
uncertainties or interval half-widths (one kind for all). The simulation combines standard
uncertainties in quadrature (to first order the consumed depth is linear in the three quantities)
and takes the nominal depth +- 2 combined standard uncertainties (about 95 % coverage for a normally
distributed depth; the amorphous-Si term is one-sided below, since its thickness cannot fall below
zero, so for a measured absence only the upper side carries it, and a detection limit given as a
standard uncertainty enters there as twice its value); half-widths are taken as their worst case
(the linear sum). At 2 nm the consumed-layer count moves by 0.3252 layer per A of oxide thickness, 0.1478 layer per 0.05 g/cm^3 of density and 0.7365 layer per A of
amorphous Si (`tools/review/x6/x6_oxide_numbers_output.txt`); for example 1 A, 0.05 g/cm^3 and
0.1 A as standard uncertainties admit the counts 6 and 7 (`tools/review/x7/x7_oxide_numbers_output.txt`).
Each uncertainty must move the consumed depth by less than two layers (a/2 = 2.7155 A); a larger one
would admit more than two counts, which is refused anyway. So the count, and at <110> the terrace
type at a buried a/4 step, can change within the uncertainty. When the uncertainties admit two
counts, each simulation run builds one of them (its lower or upper count, a stated choice), records
which of the two is the nearest count at the stated values and that the other count is a separate
run, and leaves the thickness unaltered. The code does not check that the other run was made; a
result is not quoted before both runs are compared. Only the multislice engine distinguishes the two
runs; the geometric engine gave identical results for both runs of the 2.0 nm demo record, since its
layer phase does not depend on the count. When the uncertainties admit more than
two counts, the run is refused (audit A9b m2; re-audit A10b M1, m2, m3; re-audit A12 m2, m3, n1;
reports X6, X7). If the mean inner potential or the electronic absorption of the oxide, the width of
its surface or interface grading, or the potential of the amorphous Si is measured, state for each
the method, the instrument, the date (YYYY-MM-DD, not before 1990-01-01 and not after the date of
this supply) and where the result is recorded (a DOI with its suffix, a URL, or a record id; not a
file of the simulation repository). The method is one of the following ids, optionally followed by
': ' and details:
  - mean inner potential of the oxide, and potential of the amorphous Si: `offaxis_holography_wedge`
    (off-axis electron holography of a wedge or cleaved edge of known thickness),
    `rheed_rocking_curve_fit`, `cbed_rocking_curve_fit` (convergent-beam), `reflection_rocking_curve_fit`,
    or `other_measurement` followed by a description of at least eight distinct words;
  - electronic absorption of the oxide: `eels_inelastic_mean_free_path`,
    `energy_filtered_intensity_ratio` (energy-filtered transmission or reflection intensity ratio);
  - width of the surface (vacuum-edge) grading: `xrr_fit`, `cross_section_tem_profile` (HRTEM or
    STEM), `afm_surface`;
  - width of the oxide/Si interface grading: `xrr_fit`, `cross_section_tem_profile`.
  Ellipsometry is not accepted for a grading width. Write the record in ASCII. Words that state a
  non-measurement or a model origin (for example not, no, never, estimated, calculated, derived,
  model, literature) are refused even inside a genuine description, which must then be rephrased.
The simulation requires such a record but cannot verify it. Otherwise the model values of row B43
are used for the oxide and their bracket is recorded (audit A9b M2). The amorphous-Si potential has
no model row, so a comparison run with amorphous Si needs its record (re-audit A10b M2, m1;
re-audit A12 M1, m1; report X7)."

**B7.** Two replacements:
* "(a structured record: method, instrument, date, reference; the gate refuses a fixed English list
  of placeholders, negations, model and row references and future dates, which common
  non-measurement wording still passes (re-audit A12 M1, fix in progress); it cannot verify a
  record, only require one; re-audit A10b M2)" -> "(a structured record: method, instrument, date,
  reference; the method must name an id of an allowlist of measurement methods for that parameter;
  every field must be ASCII after NFKC normalisation and is refused when it contains a listed
  placeholder, negation, origin word of a model value, row id or path into this repository; the
  reference must locate a record, and the date lies between 1990-01-01 and the item-12 supply date;
  the gate cannot verify a record, only require one, and a fabricated but well-formed record passes;
  re-audit A10b M2, A12 M1, m1; report X7)".
* "(standard uncertainties, taken as +- 2 u, about 95 % coverage, or half-widths). When the
  resulting consumed-layer count interval spans one rounding boundary, the run states which of its
  two counts it builds (`consumed_layers_parity`: lower or upper; DERIVED_HERE, 'parity variant
  <lower|upper> of an interval spanning a boundary'; no thickness altered). It records that the
  other count is a separate run, which the gate does not check." -> "(standard uncertainties,
  combined in quadrature and taken as the nominal consumed depth +- 2 combined standard
  uncertainties, about 95 % coverage for a normally distributed depth; or half-widths, taken as their
  worst case; each uncertainty must move the depth by less than two layers; re-audit A12 m2, n1).
  When the resulting consumed-layer count interval spans one rounding boundary, the run states which
  of its two counts it builds (`consumed_layers_parity`: lower or upper; DERIVED_HERE, 'parity
  variant <lower|upper> of an interval spanning a boundary'; no thickness altered) and records which
  of the two is the nearest count. It records that the other count is a separate run, which the gate
  does not check; only the multislice engine distinguishes the two (re-audit A12 m3)." In the
  closing reference list add "re-audit A12; report X7".

**B12.** One replacement: "comparison runs state the item-12 uncertainties of thickness, density
and a-Si thickness with their kind. When the count interval spans one boundary, they build its lower
or upper count as a stated parity variant; the other count is a separate run that the gate does not
check. No thickness is altered, so the layer then overlaps or misses the kept crystal by more than
a/8, at most 1.5 a/4 = 2.0366 A (2.0 nm, lower variant: +0.6838 A), an effect not computed.
Intervals of more than two counts are refused (re-audit A10b M1, m2, m3; report X6)" -> "comparison
runs state the item-12 uncertainties of thickness, density and a-Si thickness with their kind
(standard uncertainties combined in quadrature, re-audit A12 m2). When the count interval spans one
boundary, they build its lower or upper count as a stated parity variant and record which variant
builds the nearest count; the other count is a separate run that the gate does not check. No
thickness is altered, so for the variant that is not the nearest count the layer overlaps (lower)
or misses (upper) the kept crystal by more than a/8, at most 1.5 a/4 = 2.0366 A (2.0 nm, lower
variant: +0.6838 A), an effect not computed; the nearest-count variant stays within a/8 (2.0 nm,
upper: -0.6739 A; re-audit A12 n7). Only the multislice engine distinguishes the variants: for the
2.0 nm demo record the geometric engine gave byte-identical arrays for both (26 of 26; its layer
phase uses the continuum boundaries, which do not depend on the count), while in the multislice only
5 of 26 arrays were identical (exit wave: largest pointwise difference 0.795 against a largest
|psi| of 0.619; the kept crystal one layer lower, exit_x_A shifted by 1.355 A). That difference
mixes the parity with the overlap of the non-nearest variant and is not a size of the parity effect
(`tools/review/x7/x7_parity_variants_output.txt`; re-audit A12 m3). Intervals of more than two counts
are refused (re-audit A10b M1, m2, m3; re-audit A12; reports X6, X7)".

**B43.** Two replacements:
* "The gate refuses a fixed English list of placeholders, negations ('not measured'), 'model',
  'assumption', 'independent-atom', row ids, bare values and future dates; common non-measurement
  wording ('never been measured', 'estimated', 'DFT') still passes (re-audit A12 M1, fix in
  progress); it cannot verify a record, only require one (re-audit A10b M2; report X6)." -> "The
  method must name an id of the allowlist for the parameter (V_ox: off-axis electron holography of
  a wedge or cleaved edge of known thickness, RHEED, convergent-beam or reflection rocking-curve
  fit, or 'other_measurement' with a description of at least eight distinct words; V'_ox: EELS
  inelastic mean free path, energy-filtered transmission or reflection intensity ratio; w_v: XRR,
  cross-section HRTEM/STEM, AFM; w_i: XRR, cross-section HRTEM/STEM; ellipsometry is not a width
  method). As a second layer every field is NFKC-normalised and must be ASCII, and a listed
  placeholder, negation (not, never, no, n't, un-/non-measured, ...), origin word of a model value
  (estimate, guess, calculated, computed, simulated, DFT, scattering factors, literature, assumed,
  model, ...), row id or path into this repository refuses the field; the list fails closed, so a
  genuine record containing such a word must be rephrased. The reference must locate a record (a
  DOI with its suffix, a URL with a host, or a record id), and the date lies between 1990-01-01 and
  the item-12 supply date. The gate cannot verify a record, only require one: a fabricated but
  well-formed record passes (re-audit A10b M2, A12 M1, m1; reports X6, X7)."
* "B43 does not cover the a-Si potentials: in a comparison run they are PROJECT_INPUT with the same
  measurement record (re-audit A10b m1; report X6)." -> "B43 does not cover the a-Si potentials: in
  a comparison run they are PROJECT_INPUT with the same measurement record, whose method ids are
  those of V_ox (re-audit A10b m1, A12 M1; reports X6, X7)."

## 9. NOT RUN, and what remains open

NOT RUN:
* The full test suite (the orchestrator runs it). Only the oxide files and the structure, io,
  pipeline and forward directories were run (section 7).
* The physical effect of the overlap of the parity variant that is not the nearest count
  (+0.6838 A at 2.0 nm; bound 1.5 a/4 = 2.0366 A) on |r| or on the phase: no 1-D or multislice
  estimate (decision 3). The multislice comparison of `x7_parity_variants_output.txt` is pointwise
  only and is not a size of the parity effect.
* A multislice run of a parity variant under standard uncertainties, and any propagated
  comparison beyond the 2.0 nm half-width record; the [110] multislice with the layer; the a-Si
  layer in propagation; cupy/GPU.
* A comparison run with a real item-12 record: none exists. All comparison probes are in-memory
  with fabricated TEST supply and records; they are refused for the demo's other stand-ins, and
  the tests assert that no oxide entry is named.
* A check of each allowlisted method against the literature (whether, for example, a RHEED
  rocking-curve fit on the witness gives the mean inner potential of amorphous SiO2): the table is
  the orchestrator's decision, implemented as stated.
* `tools/review/x6/mutate_x6.py` (X6's record; its Y24 replacement no longer applies) and the
  regeneration of X6's saved outputs (not mine to edit).

Open, for the orchestrator:
1. Residuals of the record gate (the gate cannot verify a record): well-formed nonsense in the
   instrument and reference ("abc", "test", "Doe", "#123"), an id with nonsense details, and ASCII
   digit-for-letter substitutions ("n0t measured") pass (`x7_record_probe_output.txt`). A digit
   requirement for references or an instrument vocabulary would narrow them; neither was decided.
2. The refusal list fails closed: genuine records containing "not", "No.", "model" (JEOL model
   names, XRR layer models), "derived", "estimated uncertainty", or the surnames Kirkland and
   Lobato must be rephrased (`x7_record_probe_output.txt`). docs/06 (proposed) says so.
3. Unchanged, not in the decisions: A12-n3 (exact floating-point ties at the interval ends),
   A12-n5 (no floor on uncertainties; 1e-12 accepted), A10b-n5 (B43's V_ox at another measured
   density), A10b-n6 (no oxide cell in the sizing tool), the exact `==` of `si001.py` step
   thicknesses.
4. The texts of docs/06 item 12 and rows B7, B12, B43 (section 8) are the orchestrator's; the status
   line of docs/model_assumptions.md and the row list of docs/08 are not touched.

## Final status

FINAL. Working tree on HEAD c8f2d1a, not committed. All four decisions are implemented:

* **A12-M1 (decision 1).** The method must name an id of the per-parameter allowlist
  `MEASUREMENT_METHODS` (table and docstring `allowed_measurement_methods`); `other_measurement`
  only with a description of at least 8 distinct words; ellipsometry refused for the widths. Second
  layer: NFKC, then printable ASCII only; a broadened, case- and whitespace-insensitive refusal list
  (negations, placeholders, origin words, row, report and repository references). Every text A12
  listed as accepted is refused except the well-formed residuals of section 9. References need a
  token beyond a scheme or prefix and must not point into the repository; dates lie between
  1990-01-01 and the item-12 supply date. Every error states that the gate cannot verify a record,
  only require one.
* **A12-m2 (decision 2).** Standard uncertainties in quadrature (+- 2 combined standard
  uncertainties, the a-Si term one-sided below); half-widths keep the worst case. A12's example:
  before 5.587-7.626 layers, [6, 7, 8], refused; after 5.789-7.233, [6, 7]. Coverage check: 95.45 %
  analytic, 95.27-95.64 % Monte Carlo (the box: 99.45-99.89 %).
* **A12-m3 (decision 3).** Comment corrected; the nearest variant recorded; the committed script
  reproduces A12's D6/D7: geometric 26 of 26 arrays byte-identical, multislice 5 of 26 (exit wave
  0.795 against 0.619). The overlap's physical effect is NOT RUN.
* **Notes (decision 4).** Each uncertainty bounded (depth contribution below 2 layers, besides the
  value bounds; the bound and why in every such error); OverflowError and MemoryError become
  configuration errors; the qualifier check is exact-token. A12-n2's test gap closed.

Evidence: 39 reversions each make at least one test fail (control 883 passed); the B41 demo arrays
are bitwise identical to X6's, A10b's and A9b's in both engines; oxide files 1003, structure 505,
io 128, pipeline 835 passed; forward 191 passed, 3 skipped.

Rules kept: nothing committed; nothing written under outputs/; docs/ unchanged except this report;
no other report edited; `scripts/hpc/alliance/` and the buried-torus files untouched.
