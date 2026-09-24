# X6 - Fixes after the re-audit A10b of X5 (item-12 label policy of comparison runs)

Agent X6, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`, HEAD cff596d when
work started. Status: FINAL (written incrementally; final status at the end).

Input, read in full: `docs/agent_reports/A10b_X5_reaudit.md` with its scratch
(`SP/a10b/`, SP = `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`),
`docs/agent_reports/X5_a9b_fixes.md`, rows B7, B12, B41, B43 of `docs/model_assumptions.md`, item 12
of `docs/06_project_inputs_required.md` (with the orchestrator's interim wording of 477fad5), and the
orchestrator's six decisions.

Rules kept: no docs/ file edited except this report; no other report edited; nothing committed;
nothing written under outputs/; `scripts/hpc/alliance/` untouched; T5's files
(`tools/plots/buried_torus.py`, `tests/forward/test_buried_torus_analysis.py`) untouched; scratch in
`SP/x6/`.

Baseline before any change (oxide files and `tests/io/test_io_config_stand_ins.py`, 10 files):
`268 passed in 16.91s` (`SP/x6/baseline_oxide.txt`).

## Progress log

* (started) reading done; design in section 1.
* code changed: `structure/oxide.py` (item12_count_interval, parity-variant spec field and check),
  `pipeline/config.py` (parity key, structured records, uncertainty keys, item-12 record),
  `forward/cell.py` (n1 guard); X5's and X4's tests migrated to the new keys (section 3);
  `tools/review/x6/x6_oxide_numbers.py` written and run (output saved). Tests of the new behaviour
  and the mutation run follow.
* new tests written: `tests/structure/test_oxide_structure_a10b_fixes.py` (41),
  `tests/forward/test_oxide_multislice_a10b_fixes.py` (4), `tests/pipeline/test_oxide_pipeline_a10b_fixes.py`
  (187); the 13 oxide files together: `501 passed in 21.71s`.
* B41 demo bit-identity (`SP/x6/d_bitid.py`, outputs in `SP/x6/pipe/`): geometric `oxide_2p0nm`
  26/26 arrays bitwise identical to A10b's, X5's and A9b's runs; `multislice_tiny_oxide_2p0nm` 26/26
  identical to A10b's and A9b's; spec_sha256 equal to A10b's (094102ed...); per-parameter labels
  and headline unchanged; the item-12 record gains `consumed_layers` and `measurement_rule`.

## 1. Findings: what was done

Line numbers refer to the working tree at the end of X6. Each fix is guarded by a test that fails
when the fix is reverted (section 5).

| A10b finding (decision) | status | code | tests |
|---|---|---|---|
| M1 parity (decision 1) | FIXED as decided. `both_parities_acknowledged` retired: stating it is refused with a message naming its replacement. When the count interval spans a rounding boundary the record must state `consumed_layers_parity: lower \| upper` (no default). The run builds that count of the interval, not necessarily the nearest one; the thickness, density and a-Si values are not altered. The count carries "DERIVED_HERE (consumed-layer count computed by the code: parity variant <lower\|upper> of an interval spanning a boundary: the <v> count N of the item-12 count interval [..] (...); the nearest count at the stated values is ..; the other variant (.., count ..) is a separate run; the thickness is not altered; ...)". The item-12 record (manifest `extra.oxide_item12`, summary `oxide_item12`) gains `consumed_layers` = {count, derived_by, parity_variant: {variant, count, count_parity, qualifier, interval_counts, nearest_count, is_nearest_count, other_variant, other_variant_run: "the other variant is a SEPARATE run: this run builds only the count above; the gate does not check that the other variant was run, ...", thickness_altered: false}, note}. The key is refused when the interval spans no boundary, with any value outside {lower, upper}, and without uncertainties. Demo runs are unchanged (no uncertainties, `rounding_boundary_acknowledged` as before). Structure level: new required spec field `consumed_layers_parity_variant` (None, or {parity, the three uncertainties, kind}). `terrace_stacks` then checks the interval and the count, judges the 0.05-layer guard on the nearest count, and records the variant | `structure/oxide.py:35-45` (docstring), `:139-146`, `:281` (field), `:441-442` (call), `:461-498` (`_parity_variant`), `:637-651` (`spec_sha256`), `:704-755` (`count_parity`, `_check_parity_variant`), `:758-911` (`terrace_stacks`); `pipeline/config.py:64-96` (docstring), `:1027-1034`, `:1336-1353` (`_derived_count_label`), `:1356-1416` (`oxide_spec_from_config`), `:1419-1501` (`_oxide_count_variant`), `:1564-1614` (`_check_overlayer`), `:1651-1731` (`oxide_item12_record`) | pipeline a10b file (M1 block, run test); structure a10b file (M1 block); forward a10b file (variant cell); X5's two tests migrated (section 3) |
| M1: interval of more than two counts | REFUSED (my reading; decision needed, section 2) | `oxide.py:_check_parity_variant`; `config.py:_oxide_count_variant` | `test_interval_of_more_than_two_counts_is_refused`, structure refusal case |
| M2 measurement record (decision 2) | FIXED as decided. `measurements.<key>` is the mapping {method, instrument, date, reference}, every key required and no other. method, instrument, reference: a string with at least `MEASUREMENT_MIN_ALNUM` = 3 letters or digits. Refused: a placeholder word (after removing punctuation: "measured", "yes", "witness", ... and `NON_SUPPLIERS`); a bare number or value ("10.34 V", "2026"); or a field that contains, case-insensitively, a negation or placeholder pattern: not measured, never measured, no measurement, unmeasured, unknown, unspecified, tbd/t.b.d./tba/tbc, n/a, none, nil, null, todo/to do, "to be ...", pending, placeholder, default, assum*, model*, independent-atom, IAM, a model_assumptions row id (B + 1-3 digits), nominal, simulat*, calculat*, theoret*, literature, see above, ditto, idem, dummy, xxx, "?". date: ISO YYYY-MM-DD (or a YAML date), valid, not after the run's date (`io.config.latest_today`, as for `supplied_on`), not a date-time. Every refusal and the item-12 record say: "the gate cannot verify a measurement record, only require one". The spec label reads "PROJECT_INPUT item 12 (<source>; measured: method ...; instrument ...; date ...; reference ...)" | `config.py:1038-1061` (constants), `:1218-1315` (`_measurement_text`, `_measurement_date`, `_oxide_measurements`), `:1318-1333` (label) | `test_placeholder_record_fields_are_refused` (44 texts x 3 fields, A10b's D1 list included), date, structure and record tests; X5's record test migrated |
| m1 a-Si potentials (decision 2) | FIXED: `amorphous_si_potential` labelled PROJECT_INPUT needs the same record (`OXIDE_RECORDED_PARAMETERS`); no model row covers it, so in a comparison run the a-Si potentials need a record | `config.py:1038` | `test_amorphous_si_potentials_need_a_record`, `test_comparison_with_a_si_potentials_needs_the_record` |
| m2 uncertainty kind (decision 3) | FIXED: `uncertainty_kind: standard \| half_width`, required with the uncertainties (all four keys or none; all four in a comparison run). The count interval uses +- 2 u for "standard" (coverage factor k = 2: about 95 % coverage for a normally distributed quantity, 95.45 % printed) and +- u for "half_width". The kind, the factor and the coverage statement are recorded in the interval | `oxide.py:128-137` (`UNCERTAINTY_KINDS`, `STANDARD_COVERAGE_FACTOR`, `COVERAGE_STATEMENT`), `:573-634` (`item12_count_interval`); `config.py:1027-1028`, `:1419-1501` | structure and pipeline m2 tests |
| n2 zero or negative uncertainties (decision 3) | FIXED: refused for each of the three, with "zero or negative refused". Also refused: an interval half-width (k u) not below the thickness or the density | `oxide.py:item12_count_interval`, `_parity_variant` | structure and pipeline n2 tests |
| m3 a-Si thickness uncertainty (decision 4) | FIXED: `amorphous_si_thickness_uncertainty_A` required with the others and in the interval: t_a +- k u_a, the lower end clipped at 0 (for a measured zero the uncertainty is its detection limit). 1 A of a-Si moves the depth by 0.7365 layer, 2.26 times the oxide's 0.3252 layer per A (printed). Stand-in a-Si (B41) with uncertainties is refused, like thickness and density | `oxide.py:573-634`; `config.py:1419-1501` | structure and pipeline m3 tests |
| n1 guard (decision 5) | FIXED: `_nonconformal_sublayer` also refuses different consumed-layer counts at one thickness (the rounding tie), naming the size: (a/4)/f = 3.0752 A of sub-layer thickness difference, about 11.01-11.10 rad (the 1-D estimate of A9b C4, printed). The acknowledgement (`nonconformal_sublayer_acknowledged`, TEST_ONLY overrides label) is now accepted for differing counts as well as differing thicknesses; refused when neither differs | `forward/cell.py:239-270`; `oxide.py:428-440` | forward a10b file (2 tests); structure n1 test |
| decision 6 texts | FIXED in code: `config.py` module docstring, `oxide.py` docstring, `MIN_ROUNDING_MARGIN_LAYERS` comment, `rounding_margin_rule` and the `consumed_count_interval` docstring no longer say that both parities are run. A test scans every `reflection_holo/**/*.py` for "runs both parities", "both parities must then be run", "both parities are acknowledged" and "unless both parities". Proposed texts for docs/06 item 12, B7, B12 and B43 are in section 8 | as listed | `test_no_code_string_claims_both_parities_are_run` |

## 2. Design notes and choices for the orchestrator

Configuration format of the item-12 overlayer after X6 (additions to X5's):

    overlayer: {..., labels: {...},
                [measurements: {<PROJECT_INPUT model parameter or amorphous_si_potential>:
                                {method, instrument, date: YYYY-MM-DD, reference}}],
                [thickness_uncertainty_A, density_uncertainty_g_cm3,
                 amorphous_si_thickness_uncertainty_A, uncertainty_kind: standard | half_width],
                [consumed_layers_parity: lower | upper]}      # both_parities_acknowledged: retired

* **Intervals of more than two counts are refused.** This is my choice and needs a decision.
  "lower | upper" covers two counts. For an interval [6, 7, 8] the lower and upper counts (6, 8)
  have the same parity, and neither variant builds the nearest count 7. So "parity variant" would
  mislabel them. The run is refused, and the error gives the depth half-range of each quantity.
  Consequence (printed): with the a-Si uncertainty included, the 2.0 nm B41 values give three
  counts for +-1 A thickness, +-0.05 g/cm^3 and a-Si 0 +- 1 A as half-widths ([6, 7, 8]). They
  also give three counts for +-1 A and +-0.05 g/cm^3 as standard uncertainties with a-Si +-0.1 A.
  Realistic witness uncertainties may therefore be refused until the orchestrator extends the
  enumeration (for example, a stated count of the interval).
* **The layer overlap of the variant that is not the nearest count exceeds a/8.** No thickness is
  altered, and the kept crystal loses the variant's whole layers. So the continuum layer overlaps
  the kept crystal (lower variant) or leaves a gap (upper variant) of more than a/8, at most
  1.5 a/4 = 2.0366 A. At 2.0 nm: lower (6) +0.6838 A = +0.5036 layer (an overlap above
  a/8 = 0.6789 A); upper (7, the nearest) -0.6739 A (printed). This is recorded per terrace
  (`interface_overlap_A`, `interface_overlap_bound_A` = 1.5 a/4, `consumed_layers_nearest`,
  `parity_variant`) and in the record's note. Its effect on the reflection is NOT computed. A9b's
  C3 estimate covers a 0.674 A gap only (-0.05 % in |r|, +0.023 rad, common to all terraces of a
  conformal layer).
* The 0.05-layer rounding guard (`rounding_boundary_acknowledged`) is judged on the nearest count
  in a variant, so both variants of one record need the same acknowledgement. For demo runs
  nothing changes.
* The parity key is checked whenever uncertainties are stated, whatever the purpose (as X5's
  acknowledgement was). A comparison run must state the uncertainties
  (`oxide_comparison_reasons`), so every comparison run is covered.
* X5's `consumed_count_interval` (thickness and density half-widths at a fixed a-Si thickness) is
  kept unchanged. Its committed script `tools/review/x5/x5_oxide_numbers.py` calls it, and that
  script's output is quoted and parsed by X5's tests. The pipeline and the structure use the new
  `item12_count_interval` only, and the old function's docstring says so.
* `spec_sha256` leaves the new field out when it is None. The hash of every specification without
  a variant is therefore the pre-X6 hash: the demo's 094102ed... equals A10b's.
* Measurement records: the patterns are deliberately broad and fail closed. A genuine record that
  contains a refused word is refused and must be rephrased, for example "model" in "XRR two-layer
  model fit" or "to be" in "found to be". The gate cannot verify a record, only require one: a
  fabricated but well-formed record passes (the tests use "TEST: fabricated ..." records).
  A10b's optional check (a "measured" value equal to the B43 nominal value) was not asked for and
  is not implemented.
* A10b-n1 related: `si001.py` compares step thicknesses with an exact `==`, while `terrace_stacks`
  rounds to 12 digits (A10b D3: 20.0 against 20.0 + 1e-13). This is not in the decisions and is
  unchanged. The guard uses the rounded thickness, so such a cell is built as conformal.

## 3. Existing tests changed on purpose (none weakened; no tolerance changed; none skipped)

Before the migration, the eight tests of the retired mechanisms failed on the new code, as
expected: `8 failed, 58 passed in 4.44s` (`SP/x6/pre_migration_failures.txt`). They were
migrated as follows.

* New required spec field `consumed_layers_parity_variant`, stated `None` in the spec helpers of
  `tests/structure/test_oxide_structure.py`, `tests/structure/test_oxide_structure_a8_fixes.py`,
  `tests/structure/test_oxide_structure_a9b_fixes.py` and
  `tests/forward_geometric/test_oxide_geometric.py`. In `tests/forward/oxide_cases.py` it is a new
  keyword `parity_variant=None` of the TEST helper, which already defaults `nc_ack=False`.
  `test_every_field_is_required` now also covers the new field (one more case).
* `tests/pipeline/test_oxide_pipeline_a9b_fixes.py` (X5):
  * `UNC_2NM` gains `amorphous_si_thickness_uncertainty_A=0.1` and `uncertainty_kind="half_width"`
    (decisions 3, 4). The counts stay [6, 7] (printed).
  * `test_measurement_record_for_project_input_model_parameters`: X5's three placeholders
    ("measured", "  ", "TBD") are now tested in each of the three text fields of the structured
    record (9 cases instead of 3). X5's free-text form is refused as a whole. The accepted case
    uses a structured record, and its label and item-12 entry are asserted in full.
  * `test_comparison_admits_the_model_row`: `both_parities_acknowledged=True` replaced by
    `consumed_layers_parity="upper"`. The assertions are unchanged.
  * `test_interval_across_a_boundary_needs_both_parities` became
    `test_interval_across_a_boundary_needs_a_parity_variant`. It still asserts "may be any of
    [6, 7] (even and odd parity". It now also asserts the missing-key message, the refusal of the
    retired flag, acceptance with "upper", and the recorded interval.
  * `test_unneeded_both_parities_acknowledgement_is_refused` became
    `test_unneeded_parity_variant_is_refused`: both values are refused when no boundary is
    spanned, and the run without the key is accepted.
  * `test_uncertainty_refusals`: the flag's "True or False" case became the parity-value case
    ("got consumed_layers_parity = 'yes'"). The other cases state `consumed_layers_parity="upper"`
    instead of the flag, with the same match strings. Before the migration, the case with the
    zero uncertainty passed only because the unknown-key error lists `thickness_uncertainty_A`.
    The retired key is now refused first, by name.
* `tests/pipeline/test_oxide_pipeline_a8_fixes.py::test_comparison_refuses_per_parameter_stand_ins`
  (X4/X5): the fixture states structured TEST records, the a-Si uncertainty, the kind and
  `consumed_layers_parity="upper"` instead of the free-text records and the flag. The assertion
  (V_real B41 named) is unchanged.

New test files:
* `tests/structure/test_oxide_structure_a10b_fixes.py` (41 tests);
* `tests/forward/test_oxide_multislice_a10b_fixes.py` (4);
* `tests/pipeline/test_oxide_pipeline_a10b_fixes.py` (187, with 132 placeholder cases).

The tests of quoted numbers parse the saved output of `tools/review/x6/x6_oxide_numbers.py`: the
interval cases, 0.7365 and 0.3252 layer per A, 95.45 %, the overlaps +0.6838 and -0.6739 A, the
tie thickness, 3.0752 A and 11.01-11.10 rad.

## 4. Numbers and the committed script that prints them

All come from `tools/review/x6/x6_oxide_numbers.py` (saved: `x6_oxide_numbers_output.txt`). They
are DERIVED_HERE from the code with a first-principles check of f. The uncertainties are
illustrative TEST values, not item-12 values.

| number (where quoted) | printed line |
|---|---|
| 0.7365 layer per A of a-Si, 0.3252 layer per A of oxide, 0.1478 layer per +-0.05 g/cm^3, ratio 2.26 (this report, proposed docs/06 and B12) | "a-Si thickness: 1 A of a-Si = 1 A of depth = 0.7365 layer per A"; "oxide thickness: f(2.20) = 0.4415 A of depth per A = 0.3252 layer per A"; "density: +-0.05 g/cm^3 at 20 A = +-0.1478 layer"; "ratio a-Si / oxide thickness per A: 2.26" |
| k = 2, 95.45 % / "about 95 %" (`oxide.py` comment, `COVERAGE_STATEMENT`, `config.py` docstring, proposed docs) | "P(\|x - mu\| <= 2.0 sigma) = erf(2.0/sqrt(2)) = 95.45 % (about 95 %)" |
| intervals [6, 7] (2.0 nm, +-1 A, +-0.05, a-Si +-0.1 A half-widths), [6, 7, 8] (same as standard, or a-Si +-1 A half-width), [5] (1.5 nm, +-0.5 A, +-0.03, +-0.1 A half-widths), 6.380-6.776 (2.0 nm, +-0.1, +-0.01, +-0.1 standard) (tests, section 2) | the 14 lines of "item12_count_interval for illustrative uncertainties" |
| overlap +0.6838 A = +0.5036 layer (lower, 6), gap -0.6739 A (upper, 7), a/8 = 0.6789 A, 1.5 a/4 = 2.0366 A (section 2, `oxide.py` docstring "at most 1.5 a/4") | "lower variant, count 6 (even): ... = +0.6838 A = +0.5036 layer (overlap; \|value\| > a/8 = 0.6789 A)"; "upper variant ... -0.6739 A"; first line |
| tie t = 19.988820 A, (a/4)/f = 3.0752 A, 11.01-11.10 rad (n1 refusal, tests) | "t = 6.5 (a/4)/f = 19.988820 A: ... 3.0752 A, i.e. about 11.01-11.10 rad ..." |

The "about 11.01-11.10 rad" in the n1 refusal message is formatted at run time from
`SUBLAYER_RATE_DIFFERENCE_RAD_PER_A` (3.58, 3.61; A9b C4, `tools/review/x5/a9b_c4_nonconformal.py`)
times the sub-layer difference. It is not a constant.

## 5. Reverting each fix makes a test fail (mutations)

`tools/review/x6/mutate_x6.py --work SP/x6/mut` reverts each fix in a scratch copy of
`reflection_holo/`, `tests/`, `configs/`, `tools/` and `pyproject.toml`. Each copy is a throw-away
git repository (never the repository) and is deleted after its run. The script runs 8 files: the
three a10b files, X5's three a9b files, `tests/pipeline/test_oxide_pipeline_a8_fixes.py` and
`tests/structure/test_oxide_structure.py`. Every copy imported its own package ("package in the
copy: True"). The saved output of the final run on the final code is
`tools/review/x6/mutate_x6_output.txt`: 31 reversions and a control.

A preliminary batch (`SP/x6/mutate_run.txt`) caught all its 29 reversions. Two of them were not
faithful, and I rewrote them before the final run:
* Y12 crashed on `dict(None)` instead of only changing the hash;
* Y23 made a stated kind an unknown key instead of defaulting it.

A second batch was stopped when I moved the more-than-two-counts refusal before the key check.
Y31 guards that move. My `pkill` of that batch also killed my own shell once (exit 144); the edit
was then re-applied and checked.

| mutation (reverts) | result (final run) |
|---|---|
| Y0 control | 385 passed in 10.33s |
| Y1 M1: the parity key not required across a boundary (nearest count built) | 2 failed |
| Y2 M1: the key ignored when no boundary is spanned | 2 failed |
| Y3 M1: any value read as "upper" | 11 failed |
| Y4 M1: the nearest count always derived | 2 failed |
| Y5 M1: the count label without the qualifier | 8 failed |
| Y6 M1: the structure does not check the qualifier | 1 failed |
| Y7 M1: the item-12 record without the variant | 3 failed |
| Y8 M1: intervals of more than two counts accepted | 2 failed |
| Y31 M1: more than two counts: the key asked for first | 1 failed |
| Y9 M1: the structure does not check the variant's count | 3 failed |
| Y10 M1: the structure does not check that a boundary is spanned | 1 failed |
| Y11 M1: the retired flag not named | 2 failed |
| Y12 M1: None hashed (the pre-X6 hashes change) | 1 failed |
| Y13 M1: overlap bound a/8 for a variant | 2 failed |
| Y14 M2: X5's free-text record accepted | 2 failed |
| Y15 M2: no pattern refusals | 49 failed |
| Y16 M2: no placeholder words | 16 failed |
| Y17 M2: no minimum of 3 letters or digits | 19 failed |
| Y18 M2: bare values accepted | 9 failed |
| Y19 M2: future dates accepted | 2 failed |
| Y20 M2: any date string parsed | 3 failed |
| Y21 m1: a-Si potentials without a record | 2 failed |
| Y22 m2: a standard uncertainty read as a half-width (k = 1) | 10 failed |
| Y23 m2: an unstated kind defaulted to half_width | 1 failed |
| Y24 m3: the a-Si uncertainty ignored in the interval | 13 failed |
| Y30 m3: an uncertainty on a stand-in a-Si thickness accepted | 1 failed |
| Y25 m3: the comparison reason names two keys | 2 failed |
| Y26 n2: zero uncertainties accepted | 12 failed |
| Y27 n1: the cell guard keyed on thickness only (A10b's finding) | 2 failed |
| Y28 n1: the acknowledgement keyed on thickness only | 2 failed |
| Y29 decision 6: "(both parities must then be run)" restored in a docstring | 1 failed |

The names of the failing tests are in the saved output.

## 6. The B41 demo path is bitwise unchanged

`tools/review/x6/x6_demo_bitid.py` ran on the final code; its saved output is
`tools/review/x6/x6_demo_bitid_output.txt`. The run outputs are in `SP/x6/pipe2/`, not under
outputs/, and the references are the saved runs in `SP/a10b/pipe`, `SP/x5/pipe` and `SP/a9b/pipe`.

* Geometric `oxide_2p0nm` (3.9 s): +2.7153 +- 0.0165, -1.3578 +- 0.0082, -1.3575 +- 0.0082 A.
  * Arrays 26 of 26 bitwise identical to A10b's, X5's and A9b's runs.
  * Per-parameter labels and headline equal to A10b's and X5's.
  * The item-12 record gains `consumed_layers` (count 7, "no parity variant: no item-12
    uncertainties stated") and `measurement_rule`.
  * spec_sha256 094102ed... is equal to A10b's and X5's. It differs from A9b's, which ran X4's
    code, before X5's new field and label.
* `multislice_tiny_oxide_2p0nm` (16.1 s): 26 of 26 arrays identical to A10b's and A9b's (X5 has no
  such run); heights withheld ("measured None"), as in A9b and A10b.

The same check on the code before the last reorder (`SP/x6/d_bitid*.out`) gave the same result.
`git status --short outputs/` was empty.

## 7. Test runs (verbatim last lines)

Command: `OMP_NUM_THREADS=2 PYTHONPATH=. venv/bin/python -m pytest -q -p no:cacheprovider -rfs`,
run one after the other on the final code from 12:05:55 to 12:19:15 UTC. Logs are in `SP/x6/run_*.txt`.

    oxide files (the 12 test_oxide_* files of structure, forward_geometric, pipeline and forward,
      except the heavy tests/forward/test_oxide_multislice.py, which runs in the forward directory):
                     477 passed in 22.08s
    tests/structure: 451 passed in 32.22s
    tests/io:        128 passed in 1.24s
    tests/pipeline:  387 passed in 177.76s (0:02:57)
    tests/forward:   SKIPPED [2] tests/forward/test_null_readout_known_answer.py:225: L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1
                     SKIPPED [1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1
                     191 passed, 3 skipped in 561.50s (0:09:21)

The forward run collected T5's buried-torus test file as it was at that time. It is not mine and
was not touched.

Earlier runs, all on intermediate code:
* baseline: 268 passed;
* the 13 oxide files: 501 passed in 21.71s;
* pre-migration: 8 failed, as intended (section 3);
* the pipeline oxide files after the reorder: 253 passed in 8.77s.

The committed scripts reproduce their saved outputs:
* `x6_oxide_numbers.py`: rerun on the final code and diffed, identical;
* `tools/review/x5/x5_oxide_numbers.py`: rerun and diffed, identical (X5's function is unchanged);
* `mutate_x6.py`: run once on the final code (section 5);
* `x6_demo_bitid.py`: run once on the final code (section 6).

## 8. Proposed text for docs/06 item 12 and rows B7, B12, B43 (for the orchestrator)

Base: the wording at HEAD, including the interim wording of 477fad5. B41 needs no change: the demo
variants keep `rounding_boundary_acknowledged` and carry no uncertainties. Numbers:
`tools/review/x6/x6_oxide_numbers_output.txt`.

**docs/06 item 12.** Replace the passage from "for the oxide thickness AND its density, the
uncertainty of each" up to "their bracket is recorded (audit A9b M2)." with:

"for the oxide thickness, its density and the thickness of any amorphous Si under it (for a
measured absence: the detection limit), the uncertainty of each and whether the three are standard
uncertainties or interval half-widths (one kind for all). The simulation takes +- 2 standard
uncertainties (about 95 % coverage for a normally distributed quantity) or +- the half-widths. At
2 nm the consumed-layer count moves by 0.3252 layer per A of oxide thickness, 0.1478 layer per
0.05 g/cm^3 of density and 0.7365 layer per A of amorphous Si
(`tools/review/x6/x6_oxide_numbers_output.txt`). So the count, and at <110> the terrace type at a
buried a/4 step, can change within the uncertainty. When the uncertainties admit two counts, each
simulation run builds one of them (its lower or upper count, a stated choice), records that the
other count is a separate run, and leaves the thickness unaltered. The code does not check that the
other run was made; a result is not quoted before both runs are compared. When the uncertainties
admit more than two counts, the run is refused (audit A9b m2; re-audit A10b M1, m2, m3; report X6).
If the mean inner potential or the electronic absorption of the oxide, the width of its surface or
interface grading, or the potential of the amorphous Si is measured, state for each the method, the
instrument, the date (YYYY-MM-DD) and where the result is recorded. The simulation requires such a
record but cannot verify it. Otherwise the model values of row B43 are used for the oxide and their
bracket is recorded (audit A9b M2). The amorphous-Si potential has no model row, so a comparison
run with amorphous Si needs its record (re-audit A10b M2, m1)."

**B7.** Two replacements in the last sentences:
* "(what was measured and how; the gate requires it but cannot verify it)" -> "(a structured
  record: method, instrument, date, reference; the gate refuses placeholders, negations, model
  and row references and future dates, but cannot verify a record, only require one; re-audit
  A10b M2)".
* "and a comparison run states the thickness and density uncertainties (a consumed-layer count
  interval across a rounding boundary needs both parities, audit A9b m2; at 00851da this is only
  acknowledged, not run, re-audit A10b M1, fix in progress)." -> "and a comparison run states the
  uncertainties of the thickness, the density and the a-Si thickness and their kind (standard
  uncertainties, taken as +- 2 u, about 95 % coverage, or half-widths). When the resulting
  consumed-layer count interval spans one rounding boundary, the run states which of its two
  counts it builds (`consumed_layers_parity`: lower or upper; DERIVED_HERE, 'parity variant
  <lower|upper> of an interval spanning a boundary'; no thickness altered). It records that the
  other count is a separate run, which the gate does not check. Intervals of more than two counts
  are refused (audit A9b m2; re-audit A10b M1, m2, m3; report X6)."

**B12.** Two replacements:
* "comparison runs state the item-12 thickness and density uncertainties and need both parities
  when the count interval spans a boundary, at 00851da acknowledged but not run, re-audit A10b
  M1" -> "comparison runs state the item-12 uncertainties of thickness, density and a-Si thickness
  with their kind. When the count interval spans one boundary, they build its lower or upper
  count as a stated parity variant; the other count is a separate run that the gate does not
  check. No thickness is altered, so the layer then overlaps or misses the kept crystal by more
  than a/8, at most 1.5 a/4 = 2.0366 A (2.0 nm, lower variant: +0.6838 A), an effect not
  computed. Intervals of more than two counts are refused (re-audit A10b M1, m2, m3; report X6)".
* "an atomistic multislice cell whose terraces carry different thicknesses is refused unless
  acknowledged (TEST_ONLY; audit A9b M1)" -> "an atomistic multislice cell whose terraces carry
  different thicknesses, or different consumed-layer counts at one thickness (the rounding tie,
  a sub-layer difference of (a/4)/f = 3.0752 A; re-audit A10b n1), is refused unless
  acknowledged (TEST_ONLY; audit A9b M1)".

**B43.** Two replacements:
* "A value measured on the witness piece replaces a B43 value only as PROJECT_INPUT with a
  measurement record (what was measured and how)." -> "A value measured on the witness piece
  replaces a B43 value only as PROJECT_INPUT with a structured measurement record {method,
  instrument, date YYYY-MM-DD, reference where the result is recorded}. The gate refuses
  placeholders, negations ('not measured'), 'model', 'assumption', 'independent-atom', row ids,
  bare values and future dates, but cannot verify a record, only require one (re-audit A10b M2;
  report X6)."
* "The a-Si potentials remain PROJECT_INPUT-only in comparison runs (report X5 section 9)." -> "B43
  does not cover the a-Si potentials: in a comparison run they are PROJECT_INPUT with the same
  measurement record (re-audit A10b m1; report X6)."

## 9. NOT RUN, and what remains open

NOT RUN:
* The full test suite (the orchestrator runs it).
* A pipeline run of the OTHER parity variant next to its partner, or any comparison of two variant
  runs. The pipeline builds and records one variant per run. The run test builds only the lower
  variant (geometric engine), and the gate does not check that the other variant was run.
* The physics of a variant whose count is not the nearest one. Its overlap or gap exceeds a/8
  (+0.6838 A for 2.0 nm, lower) and is recorded but not evaluated: no 1-D or multislice estimate
  of its effect on |r| or the phase was made. A9b's C3 covers a 0.674 A gap only.
* A multislice run of a parity variant (cell construction only, forward a10b tests); the [110]
  multislice with the layer; the a-Si layer in propagation; cupy/GPU.
* A comparison run with a real item-12 record: none exists. All comparison probes are in-memory
  with fabricated TEST supply and measurement records. They are refused anyway for the demo's other
  stand-ins, and the tests assert that no oxide entry is named.
* A propagated two-terrace multislice of a non-conformal or two-count oxide. The n1 size
  (11.01-11.10 rad) rests on A9b's 1-D estimate of 3.58-3.61 rad per A.

Open, for the orchestrator:
1. **Intervals of more than two counts are refused** (section 2). With the a-Si uncertainty
   included this will be common: for example 2.0 nm with a-Si 0 +- 1 A as a half-width, or +-1 A
   and +-0.05 g/cm^3 as standard uncertainties. Deciding how such a record is simulated (for
   example a stated count of the interval, with each count a separate run) is needed before a
   realistic item-12 record can be run.
2. Whether a comparison result may be quoted from one variant. The record says "a result is not
   quoted before both variants are compared", but nothing enforces or links the pair (A10b's
   option (a) "link the pair in both manifests" was not in the decision).
3. The measurement-record patterns fail closed and can refuse a genuine record ("model fit",
   "found to be", an instrument named with "model"). The gate cannot verify a record, only require
   one.
4. Not in the decisions and unchanged:
   * A10b-n2's exact-tie edge cases of the interval corners;
   * a floor on uncertainties (only zero and negative values are refused);
   * A10b-n3 (the engine value checked as a string);
   * A10b-n5 (B43's V_ox at another measured density);
   * A10b-n6 (no oxide cell in the sizing tool);
   * the exact `==` of `si001.py` step thicknesses (section 2).
5. The texts of docs/06 item 12 and rows B7, B12, B43 (section 8) are the orchestrator's.

## Final status

FINAL. HEAD f009be8, the orchestrator's snapshot, which includes this working tree. All six
decisions are implemented:

* **M1.** `both_parities_acknowledged` is retired. `consumed_layers_parity: lower | upper` is
  required across a boundary and refused otherwise. The variant's count is labelled DERIVED_HERE
  with "parity variant <lower|upper> of an interval spanning a boundary". The item-12 record,
  manifest and summary give the interval, the variant and "the other variant is a SEPARATE run".
  No thickness is altered. Intervals of more than two counts are refused, which is my addition
  and needs a decision.
* **M2 and m1.** The measurement record is structured {method, instrument, date, reference} for
  V_ox, V'_ox, w_v, w_i and the a-Si potentials. Placeholders, negations, model and row
  references, bare values and future dates are refused. Every error states that the gate cannot
  verify a measurement record, only require one.
* **m2 and n2.** `uncertainty_kind` is required: a standard uncertainty enters as +- 2 u (k = 2,
  about 95 % coverage for a normally distributed quantity), a half-width as +- itself. Zero and
  negative uncertainties are refused.
* **m3.** The a-Si thickness uncertainty is in the interval: 0.7365 layer per A, printed.
* **n1.** The cell guard also refuses different counts at one thickness.
* **Decision 6.** The code strings are corrected, and texts are proposed for docs/06 item 12, B7,
  B12 and B43.

Evidence:
* Each of the 31 reversions makes at least one test fail.
* The B41 geometric and multislice demo arrays are bitwise identical to A10b's runs.
* Tests: oxide files 477, structure 451, io 128 and pipeline 387 passed; forward 191 passed and
  3 skipped.

Rules kept: nothing committed by me; nothing written under outputs/; docs/ unchanged except this
report; `scripts/hpc/alliance/` and T5's files untouched.
