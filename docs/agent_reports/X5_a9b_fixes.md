# X5 - Fixes after the audit A9b of X4's continuum-oxide work

Agent X5, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r` (HEAD dc4eb7f when
work started; still dc4eb7f at the end). Status: FINAL (written incrementally).

Input, read in full: `docs/agent_reports/A9b_X4_audit.md` with its scratch scripts and outputs
(`SP/a9b/`, SP = the session scratchpad
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`),
`docs/agent_reports/X4_a8_fixes.md`, `docs/agent_reports/A8_e4_oxide_audit.md`, rows B7, B12, B26,
B41 of `docs/model_assumptions.md` and item 12 of `docs/06_project_inputs_required.md`; the
orchestrator's decisions for A9b-M1, M2, m1-m4, m6, n1-n3.

Rules kept: no docs/ file edited except this report; X4's report unchanged; nothing committed;
nothing written under outputs/; `scripts/hpc/alliance/` untouched; the T3 files (A9a/T4: shapes.py
BuriedTorus, features.py, feature_cell.py, scripts/torus/, tools/plots/buried_torus.py) untouched
(no oxide fix required them); scratch in `SP/x5/`. Evidence labels: the numbers below are
DERIVED_HERE by the named committed scripts unless marked otherwise; the 1-D laterally averaged
model of A9b C3/C4 is an ESTIMATE (it drops the lateral Fourier components of the crystal).

## 1. Findings: what was done

| A9b finding | status | code (file:line, working tree at the end of X5) | tests |
|---|---|---|---|
| M1 non-conformal oxide: engines disagree | FIXED as decided: (a) stated with its size in `NOT_REPRESENTED` (via `NONCONFORMAL_SUBLAYER`), in `B4_OXIDE_GROWN`, in the geometric model docstring, and per non-conformal step (`thickness_difference_A`, `consumed_layer_difference`, `sublayer_thickness_difference_A`, `multislice_sublayer_note` with this step's size); (b) `build_reflection_cell` REFUSES an atomistic cell whose terraces carry different thicknesses, naming the size, unless the new required spec field `nonconformal_sublayer_acknowledged` is True, which the spec accepts only with differing thicknesses and a TEST_ONLY overrides label; then the statement and size are recorded in the cell layout; geometric engine unchanged; continuum-crystal cells unaffected; (c) A9b's C4 committed | `structure/oxide.py:154-167` (`SUBLAYER_RATE_DIFFERENCE_RAD_PER_A`, `NONCONFORMAL_SUBLAYER`), `:168` (`NOT_REPRESENTED`), `:239, 386-397` (field and check); `structure/si001.py:821-827` (`B4_OXIDE_GROWN`), `:922-941` (per-step record); `forward/cell.py:105, 239-267` (`_nonconformal_sublayer`); `forward/geometric/model.py:49-56` (docstring only); `tools/review/x5/a9b_c4_nonconformal.py` | `tests/forward/test_oxide_multislice_a9b_fixes.py` (4); `tests/structure/test_oxide_structure_a9b_fixes.py` (M1 block) |
| M2 label policy | FIXED as decided: (a) consumed_layers labelled DERIVED_HERE (pipeline: exactly "DERIVED_HERE", qualified by the code from the thickness, density and a-Si labels; structure: DERIVED_HERE or TEST_ONLY, never PROJECT_INPUT or ASSUMPTION); a stated value must equal the derived count; (b) V_ox, V'_ox, w_v, w_i: PROJECT_INPUT only with `measurements.<key>` (what was measured and how; placeholders refused), or `ASSUMPTION B43`, a registered NON-DEMO model row (registry `model_rows`), admitted by the comparison gate, vouching for its nominal values and its bracket ends only; the run writes `oxide_item12` (labels, headline, model-row values with nominal/bracket-end and the declared bracket, uncertainties with the count interval, measurement records) to manifest.json (`extra`) and summary.json; (c) thickness, density and a-Si thickness stay PROJECT_INPUT in comparison runs (B43 refused on them); (d) headline label `mixed (...)` | `pipeline/config.py:64-83` (docstring), `:1000-1063` (`OXIDE_UNCERTAINTY_KEYS`, `OXIDE_KEYS_OPTIONAL`, `OXIDE_MODEL_PARAMETERS`, `OXIDE_STAND_IN_ROWS`, `OXIDE_MODEL_ROWS`), `:1094-1127` (labels), `:1162-1215` (`_oxide_measurements`, `_derived_count_label`), `:1360-1365` (derived count), `:1453-1501` (`oxide_item12_record`), `:1560` (gate); `pipeline/run.py:739, 750, 825`; `io/assumption_registry.yaml:11-15, 76`; `structure/oxide.py:101-102, 286-299, 413-438` (`headline_label`, `nearest_consumed_layers`); `configs/demo_smoke_si001.yaml` (five `consumed_layers: DERIVED_HERE`) | `tests/pipeline/test_oxide_pipeline_a9b_fixes.py` (M2 blocks), structure M2/n1 blocks |
| m1 B26 per parameter | FIXED: a per-parameter `ASSUMPTION <id>` must name a key of `OXIDE_STAND_IN_ROWS` (B41) or `OXIDE_MODEL_ROWS` (B43); B26 is refused with "B26 states a clean surface" | `pipeline/config.py:1146-1153` | `test_clean_surface_row_is_refused_per_parameter` (A9b's three C5 probes) |
| m2 rounding-margin rationale | FIXED: rationale removed; 0.05 layer stated as an arbitrary numerical guard that does not make the parity robust (constant comment, module docstring, new record field `rounding_margin_rule`); new `consumed_count_interval`; comparison runs require `thickness_uncertainty_A`, `density_uncertainty_g_cm3` and `both_parities_acknowledged` (optional, all or none, elsewhere; refused under a stand-in); an interval spanning a count boundary is refused unless both_parities_acknowledged is True; an unneeded acknowledgement is refused; supporting numbers printed | `structure/oxide.py:105-116, 441-477, 659-663`; `pipeline/config.py:1371-1451` (`oxide_comparison_reasons`, `_check_oxide_uncertainties`), `:790`; `tools/review/x5/x5_oxide_numbers.py` | structure m2 block; pipeline m2 block |
| m3 quoted numbers not printed | FIXED: A9b's C2 committed with QUOTE lines; `EDGE_W05_REFLECTIVITY`, the vacuum-edge refusal, the oxide and geometric docstrings quote the printed digits (1.9545e-9, 8.513e-4, 3.44e-11, 56.8, 1.8345e-9, 58.4; engine 1.8350e-9 from the committed test print) | `structure/oxide.py:58-64, 117-123, 323-329, 689`; `forward/geometric/model.py:49-52`; `tools/review/x5/a9b_c2_edge.py` | `test_edge_reflectivity_quotes_the_printed_digits` (parses the saved output) |
| m4 gap is a potential dip | FIXED: one sentence in `INTERFACE_OVERLAP_RULE` with the digits of A9b's C3 (committed with SUMMARY lines) | `structure/oxide.py:139-152`; `tools/review/x5/a9b_c3_gap.py` | `test_interface_gap_dip_quotes_the_printed_digits` |
| m6 sizing "with oxide" column | FIXED (text only): column header and per-scenario lines say "same-grid lower bound"; tool rerun, 63/63 checks pass, clean-surface numbers unchanged | `tools/hpc/supercell_sizing.py:1818-1826, 1993-2006`; `tools/hpc/supercell_sizing_output.txt` | `test_sizing_tool_labels_the_oxide_column_a_same_grid_lower_bound` |
| n1 headline label | FIXED (with M2 (d)): `headline_label` in `terrace_stacks` and in the builder's `_overlayer_option` | `structure/oxide.py:413-426`; `structure/si001.py:786` | `test_headline_label_lists_mixed_labels`; pipeline B43 test |
| n2 B41 thickness per variant | FIXED: `OXIDE_STAND_IN_ROWS["B41"]["variants"]`; the variant name reaches the gate | `pipeline/config.py:1018-1027, 1301-1315` | `test_b41_thickness_is_tied_to_its_variant`; one case of X4's test inverted (section 3) |
| n3 copied comment | FIXED: the two 1.5 nm variants say "(1 - f) 15 + a/8 = 9.06 A" | `configs/demo_smoke_si001.yaml:625, 666` | `test_layer_top_comments_of_the_demo_variants` |
| m5 X4's report | not X5's to edit; the values its four placeholders lacked are recorded in section 6 | - | - |
| n4, n5, n6 | not in X5's brief; n6 (B12 wording) is taken into the proposed B12 text (section 8) | - | - |

## 2. Design notes

### Item-12 record in the pipeline (configuration format after X5)

    overlayer: {model: continuum_oxide, material, thickness_A, density_g_cm3, consumed_layers,
                V_real_V, V_imag_V, vacuum_edge_width_A, interface_width_A,
                amorphous_si_thickness_A, rounding_boundary_acknowledged,
                labels: {thickness, density, consumed_layers: DERIVED_HERE, V_real, V_imag,
                         vacuum_edge, interface, amorphous_si[, amorphous_si_potential]},
                [measurements: {<model parameter labelled PROJECT_INPUT>: "<what, how>"}],
                [thickness_uncertainty_A, density_uncertainty_g_cm3, both_parities_acknowledged]}

* Required keys are unchanged (`OXIDE_KEYS`); the new keys are optional as keys and required in
  the stated cases: `measurements` exactly for the model parameters (V_real, V_imag, vacuum_edge,
  interface) labelled PROJECT_INPUT; the three uncertainty keys all or none, and all three in a
  comparison run (the absence is one more reason in the comparison gate's single error, so a
  B41 run in comparison still names B41). No default fills any of them.
* consumed_layers stays a required value key: the stated value must equal the count the code
  derives (`nearest_consumed_layers`); only its label changed. I read "a supplied value is
  accepted only if it equals the derived count" as "the stated value is checked", which keeps
  every oxide key explicit.
* B43 is a registry `model_rows` entry (not in `stand_ins`, not in `demo_only`), so the io gate
  never accepts it as the assumption_id of a configuration record; the pipeline accepts
  "ASSUMPTION B43" only as a per-parameter label of V_real, V_imag, vacuum_edge, interface,
  inside a PROJECT_INPUT or TEST_ONLY record (inside a stand-in record every parameter carries the
  record's id, as before). B43 vouches for its nominal values (10.34 V, 0.40 V, 0.5 A, 0.5 A) and
  for the declared bracket ends (V_ox 10.1 and 11.5 V; V'_ox 0, 0.39 and 0.44 V); the widths have
  no bracket (a numerical requirement). The gate does NOT require the bracket ends to be run: a
  comparison run at the nominal values passes and records, per parameter, "nominal" or "bracket
  end" with the declared bracket (manifest `extra.oxide_item12.model_rows`, summary
  `oxide_item12`). Whether bracket-end runs are required before a result is quoted is left to the
  orchestrator. Accepting the bracket ENDS under B43 is my choice (the decision names the bracket as
  declared and recorded; accepting its ends lets a sensitivity run be made under the same row); if
  only the nominal values should be admitted, empty `OXIDE_MODEL_ROWS["B43"]["bracket_ends"]`
  (the tests of the bracket-end cases would then have to be inverted, which the orchestrator
  should decide).
* The per-parameter spec labels are: "ASSUMPTION B43 (model row, not a stand-in for a
  PROJECT_INPUT; audit A9b M2)"; "PROJECT_INPUT item 12 (<source>; measured: <statement>)";
  "DERIVED_HERE (consumed-layer count computed by the code: ...; from thickness: <label>; density:
  <label>; amorphous_si: <label>)". The spec (and its hash) therefore carries the measurement
  statements.
* Headline label (`headline_label`): the common label when all parameters carry one, otherwise
  "mixed (<classes>); per-parameter labels in 'labels'", e.g. "mixed (ASSUMPTION B41,
  DERIVED_HERE)" for the B41 variants, which since consumed_layers is DERIVED_HERE are always
  mixed.
* Count interval (`consumed_count_interval`): the continuum depth f(rho) t + t_a increases with t
  and rho, so its extremes lie at the corners (t - u_t, rho - u_rho) and (t + u_t, rho + u_rho);
  the counts between the nearest counts at the two corners are listed with their parities. The
  a-Si thickness enters at its value (no uncertainty field for it was requested). Uncertainties
  must be > 0 and below the value. Under a stand-in thickness or density (B41) the uncertainty keys
  are refused (the row states none). The 0.05-layer guard stays as it was (X4) and is stated as
  arbitrary.

### A9b-M1: where the refusal sits

The refusal is in `forward.cell.build_reflection_cell`, the one constructor of atomistic multislice
cells; it fires when the builder's per-terrace stacks carry more than one thickness and the spec's
`nonconformal_sublayer_acknowledged` is not True. The flag is a required field of
`ContinuumOxideSpec` (every field is required; the pipeline, which builds conformal layers only,
states False), accepted as True only with per-terrace thicknesses that differ and a TEST_ONLY
`overrides` label, and refused when not needed. The geometric engine and the si001 builder accept
non-conformal specs as before (the builder now records the size per step). The continuum-crystal
cell (`build_continuum_oxide_cell`) is not refused: its crystal boundary moves continuously with
f t, so it has no whole-layer quantisation. The decision refuses ANY different thicknesses, so a
cell whose thicknesses differ by exactly whole consumed layers is refused too; its recorded
sub-layer difference is then 0.0000 A. The size is given in the refusal and in the step record as
the sub-layer thickness difference Dt - DN (a/4)/f times the printed range 3.58-3.61 rad/A (at the
B41 values, 16.1347 mrad), labelled an estimate of the 1-D model.

## 3. Existing tests changed on purpose (none weakened; no tolerance changed; none skipped)

* New required spec field `nonconformal_sublayer_acknowledged`: stated (False) by the spec helpers of
  `tests/structure/test_oxide_structure.py`, `tests/structure/test_oxide_structure_a8_fixes.py`,
  `tests/forward_geometric/test_oxide_geometric.py` and `tests/forward/oxide_cases.py`
  (`oxide_spec(..., nc_ack=False)`). `test_every_field_is_required` now also covers the new field.
* `tests/structure/test_oxide_structure_a8_fixes.py::test_edge_reflectivity_text_is_the_exact_value`:
  the asserted substring "1.95e-9" became "1.9545e-9" (the printed digits the text now quotes; a
  stricter string, A9b m3). The Born-figure check ("1.1e-4" absent) is unchanged.
* `tests/pipeline/test_oxide_pipeline_a8_fixes.py`:
  * fixtures state `consumed_layers: DERIVED_HERE` (A9b M2 (a)) instead of TEST_ONLY/PROJECT_INPUT;
  * `test_measured_zero_a_si_in_a_supplied_record`: consumed_layers left the set of per-parameter
    ASSUMPTIONs (it is DERIVED_HERE) and its derived label is asserted;
  * `test_comparison_refuses_per_parameter_stand_ins`: the fixture states the new required fields
    of a comparison run (measurement records of the PROJECT_INPUT model parameters, the
    uncertainties and both_parities_acknowledged); the assertion (V_real B41 named) is unchanged;
  * `test_list_inputs_shows_one_row_per_parameter`, `test_b41_row_table_matches_the_shipped_variants`:
    the count's label is DERIVED_HERE, all others B41 (the latter now also asserts the variant pair);
  * `test_b41_values_outside_its_row_are_refused`: the case (15 A, 5) in the 2.0 nm variant was
    ACCEPTED ("the row's other pair") and is now REFUSED (A9b n2: the row ties 2.0 nm to that
    variant); acceptance of that pair at the base is asserted in the new file.
* `tests/pipeline/test_oxide_pipeline.py::test_spec_built_by_the_pipeline_carries_the_record_label`:
  the count's label is DERIVED_HERE, every other label B41.
* `tests/io/test_io_config_stand_ins.py::test_registry_is_package_data_mapping_ids_to_items`: the
  expected model rows are {B35, B37, B43} (was {B35, B37}) and B43 is asserted not demo-only.

New test files: `tests/structure/test_oxide_structure_a9b_fixes.py` (20 tests),
`tests/forward/test_oxide_multislice_a9b_fixes.py` (4), `tests/pipeline/test_oxide_pipeline_a9b_fixes.py`
(35). The tests of m3, m4, M1 (a) and m2 parse the SAVED outputs of the committed scripts in
`tools/review/x5/` and assert that the code strings quote those digits, so a code string and its
print cannot diverge silently.

## 4. Numbers and the committed scripts that print them

| number (where quoted) | script (saved output) | printed line |
|---|---|---|
| 4.4549 rad/A, 13.6998 rad = 3.0752 A, 0.8857 (= 0.886) rad/A, slopes 0.8455, 0.8729, 0.8599 rad/A (range 0.85-0.87), differences 3.6094, 3.5820, 3.5950 rad/A (range 3.58-3.61), Dt = 0.5 A: 2.23 rad against 0.42-0.44 rad (NONCONFORMAL_SUBLAYER, B4_OXIDE_GROWN, cell refusal, proposed B12/B41) | `tools/review/x5/a9b_c4_nonconformal.py` (A9b's C4; `..._output.txt`) | "geometric grown-oxide rate 4.4549 rad/A; one consumed layer 13.6998 rad = 3.0752 A of oxide"; the three "slope at t ..." lines; three QUOTE lines |
| 1.9545e-9, 8.513e-4 (sharp 2.697e-3), 3.44e-11, 56.8, 1.8345e-9, 58.4 (EDGE_W05_REFLECTIVITY, oxide and geometric docstrings, refusal message, proposed B41) | `tools/review/x5/a9b_c2_edge.py` (A9b's C2) | "QUOTE w 0.5 A at 16.1347 mrad: exact \|r\|^2 = 1.9545e-09; \|r\|/\|r_sharp\| = 8.513e-04 (sharp edge \|r\|^2 2.697e-03); Born factor \|r\|^2 = 3.44e-11; exact/Born = 56.8"; "QUOTE w 0.5 A at the central bin 16.1751 mrad: exact \|r\|^2 = 1.8345e-09; exact/Born = 58.4" |
| engine 1.8350e-9 | committed test `test_graded_edge_of_0p5_A_suppresses_the_layer_reflection` (`-s`; A9b C9) | "w = 0.5 A: \|r\|^2 = 1.8350e-09, ..." |
| 4.84 V at 0.96 A, gap 0.674 A, Born \|r\|^2 1.7e-12, -0.05 %, +0.023 rad; 1.5 nm: gap 0.166 A, +0.01 %, +0.009 rad (INTERFACE_OVERLAP_RULE, proposed B41) | `tools/review/x5/a9b_c3_gap.py` (A9b's C3) | "SUMMARY t 20.0 A: laterally averaged potential minimum 4.84 V at 0.96 A above the kept top plane; gap 0.674 A; Born \|r\|^2 of the deficit at q = 2 k'_ox 1.7e-12; 1-D against the joined stack: \|r\| -0.05 %, arg +0.023 rad"; "SUMMARY t 15.0 A: ... gap 0.166 A; ... \|r\| +0.01 %, arg +0.009 rad" |
| 0.068 A, 0.1538 A, 0.769 %, 0.0169 g/cm^3, +-0.325 layer per +-1 A, +-0.148 layer per +-0.05 g/cm^3, 0.0036 layer (0.0049 A), 2.19877 g/cm^3 (-0.056 %), 19.9888 A (oxide.py comment, proposed B41, docs/06) | `tools/review/x5/x5_oxide_numbers.py` | "0.05 layer = 0.0679 A (= 0.068 A) of consumed depth = 0.1538 A of thickness at f(2.20) = 0.769 % of the density = 0.0169 g/cm^3"; "thickness +-1.0 A -> continuum depth +-0.442 A = +-0.325 layer"; "density +-0.05 g/cm^3 at 20 A -> +-0.148 layer"; "t 20.0 A, N 7: continuum 6.5036 layers, margin 0.0036 layer (0.0049 A); the count becomes 6 at 2.19877 g/cm^3 (-0.056 %) or 19.9888 A" |
| 11.85 A, 9.06 A (config comments) | same | "t 20.0 A: ... = 11.8487 A (= 11.85 A)"; "t 15.0 A: ... = 9.0563 A (= 9.06 A)" |
| count intervals (e.g. 2.0 nm +-1 A, +-0.05 g/cm^3: 6.038-6.984 layers, counts [6, 7]; 1.5 nm +-0.5 A, +-0.03: [5]) | same | "consumed-layer count over an uncertainty box" block (illustrative TEST uncertainties, not item-12 values) |

The committed C2 and C3/C4 reproduce A9b's saved outputs line for line (`diff` against
`SP/a9b/c2_edge.out`, `c3_gap.out`, `c4_nonconformal.out`: identical apart from the added
QUOTE/SUMMARY lines). C3 prints the minimum of the laterally averaged potential on the 0.02 A grid,
4.84 V at 0.96 A; A9b's 0.1 A-sampled table shows 4.85 V at 0.94 A; the code quotes the printed
minimum.

## 5. Reverting each fix makes a test fail (mutations)

Each fix was reverted in a scratch copy of `reflection_holo/`, `tests/`, `configs/`, `tools/` (a
throw-away git repository per copy, never the repository), and the five test files
`tests/structure/test_oxide_structure_a9b_fixes.py`, `tests/forward/test_oxide_multislice_a9b_fixes.py`,
`tests/pipeline/test_oxide_pipeline_a9b_fixes.py`, `tests/structure/test_oxide_structure_a8_fixes.py`,
`tests/pipeline/test_oxide_pipeline_a8_fixes.py` were run (`SP/x5/mutate.py`; output saved in
`SP/x5/mutations_final.out`, run on the final code; the first batch, `SP/x5/mutations.out`, ran
before a refactor that removed an unused parameter and stopped at X25 on my runner's
one-occurrence assertion, since the n3 comment occurs twice). Every copy imported its own package
(the printed `reflection_holo/__init__.py` path lies in the copy).

| mutation (reverts) | result |
|---|---|
| X0 control (no change) | 120 passed in 5.10s |
| X1 M1: no refusal of an atomistic non-conformal cell | 2 failed, 118 passed (both refusal tests) |
| X2 M1: the acknowledgement flag not checked by the spec | 1 failed (`test_nonconformal_acknowledgement_is_checked`) |
| X3 M1: `NOT_REPRESENTED` without the sub-layer statement | 1 failed (`test_nonconformal_disagreement_is_stated_with_the_printed_numbers`) |
| X4 M1: `B4_OXIDE_GROWN` restored to X4's text | 1 failed (same test) |
| X5 M1: no per-step record of the sub-layer size | 1 failed (`test_every_nonconformal_step_records_the_sublayer_size`) |
| X6 M2 (a): the structure-level DERIVED_HERE rule removed | 44 failed, 76 passed (the pipeline's DERIVED_HERE labels are then refused, and PROJECT_INPUT/ASSUMPTION counts accepted) |
| X7 M2 (a): the pipeline accepts any label on consumed_layers | 3 failed (`test_consumed_layers_is_never_supplied`, all three) |
| X8 M2 (a): a stated count different from the derived one accepted | 1 failed (`test_stated_count_must_equal_the_derived_count`) |
| X9 M2 (b): the comparison gate refuses the model row | 1 failed (`test_comparison_admits_the_model_row`) |
| X10 M2 (b): no measurement record required | 1 failed (`test_measurement_record_for_project_input_model_parameters`) |
| X11 M2 (b): B43 values not checked | 4 failed (the four out-of-row cases) |
| X12 M2 (c): B43 accepted on thickness and density | 2 failed |
| X13 M2 (b): the record without the bracket | 2 failed (record test, run test) |
| X14 M2 (b): the manifest without the item-12 record | 1 failed (`test_run_records_the_model_row_bracket`) |
| X15 n1/M2 (d): headline = the thickness label (both places) | 1 failed (`test_headline_label_lists_mixed_labels`) |
| X16 m1: per-parameter ids outside the oxide rows accepted | 3 failed (A9b's three B26 probes) |
| X17 m2: comparison without uncertainties accepted | 1 failed (`test_comparison_needs_the_uncertainties`) |
| X18 m2: interval across a boundary accepted without acknowledgement | 1 failed |
| X19 m2: unneeded acknowledgement accepted | 1 failed |
| X20 m2: interval taken at the nominal values only | 7 failed (structure interval cases, pipeline interval tests, X4's comparison test with its new fixture) |
| X21 m2: X4's rationale comment restored | 1 failed (`test_rounding_margin_is_stated_as_an_arbitrary_guard`) |
| X22 m3: "1.95e-9" restored in the recorded statement | 2 failed (the new digits test and X4's A8-m1 test) |
| X23 m4: the dip value dropped from the gap sentence | 1 failed (`test_interface_gap_dip_quotes_the_printed_digits`) |
| X24 n2: variant tie removed | 2 failed (new test; the inverted X4 case) |
| X25 n3: the copied "11.85 A" comment restored in both 1.5 nm variants | 1 failed (`test_layer_top_comments_of_the_demo_variants`) |
| X26 m6: the sizing tool's column header restored | 1 failed (`test_sizing_tool_labels_the_oxide_column_a_same_grid_lower_bound`) |

The text-only fixes (M1 (a), m3, m4, m6, n3) are guarded by tests that compare the text with the
saved script outputs or the tool source; those are string checks, not physics checks.

Bit-identity of the conformal demo (`SP/x5/pipe_bitid.py`, output `SP/x5/pipe_bitid.out`, outputs in
`SP/x5/pipe/`, not under outputs/): the geometric `oxide_2p0nm` run returns +2.7153 +- 0.0165,
-1.3578 +- 0.0082, -1.3575 +- 0.0082 A, and "arrays 26 vs A9b 26; bitwise identical 26;
differing []" against A9b's run of X4's code (which A9b found bitwise identical to A8's run of E4's
pre-fix code). Its manifest carries `extra.oxide_item12` with the headline "mixed (ASSUMPTION B41,
DERIVED_HERE); per-parameter labels in 'labels'", no model rows and no uncertainties (B41 demo).

## 6. X4's report: the values its placeholders lacked, and one correction

X4's report stays as it is (orchestrator's instruction). The values its four placeholders lacked,
from A9b's saved outputs (`SP/a9b/`; A9b-m5):

* `(M1_PRINT)` (X4 section 5, A8-m1): A9b C9 (`c9_forward_prints.out`, the committed test with
  `-s`): "w = 0.5 A: |r|^2 = 1.8350e-09, suppression 6.92e-07; EXACT 1-D (transfer matrix, audit
  A8 C6) 1.8346e-09 at the central bin 16.1751 mrad (E9's Born factor exp(-(q w)^2) = 1.17e-08 of
  the sharp edge underestimates it 58-fold)"; also "w = 0.1 A: |r|^2 = 1.29044e-03, E9 formula
  1.28764e-03". The converged exact value at that bin is 1.8345e-9 (section 4; the test's coarser
  transfer matrix prints 1.8346e-09).
* `(MULTISLICE_RUN)` (X4 section 5): A9b C14 (`c14_pipe_ms.out`): `multislice_tiny_oxide_2p0nm`
  runs end to end (real 0m18.158s); both steps "measured None" (heights withheld: "a terrace region
  is empty or below the minimum size after the margin", as in A8); `interface_overlap_A`
  -0.6739265595682866, `rounding_margin_layers` 0.0036354493227346296. A9b C12 (`c12_dry.out`, the
  dry run): cell extent_x 126.068 A, length_z 2953.052 A, 54000 atoms; item-4 through the overlayer
  passed, available 2722.8 A, required 2405.9 A, stack 21.353 A; device 4937738 B, overlayer
  resident 27648 B, host build 55296 B.
* `(C_PRINT)` (X4 section 6, A8-m7): no A9b print exists; A9b did not run the (c) flat series
  (A9b section 11, NOT RUN). The numbers of that reading are A8's (A8 section 4 table, C17/C20).
  A9b C10 (`c10_memory.out`) re-printed X4's memory-model check: measured 41.304 / 82.062 / 25.248
  MB against the model 41.273 / 82.029 / 25.217 MB (+0.075 %, +0.041 %, +0.125 %).
* `(FULL_SUITE_RESULT)`: not X4's run and not printed by A9b; the orchestrator's full suite at
  4c4a78b plus the B42 fix (`SP/full_suite_x4t3.txt`) ends "1399 passed, 8 skipped, 12 warnings in
  1015.20s (0:16:55)".

Correction to X4 section 2 (A9b-M1): "the chosen form keeps one continuum geometry for both
engines" holds for the placement of the layer, not for the phase of a non-conformal layer on an
atomistic crystal: the multislice crystal loses whole layers only, so a sub-layer thickness
difference carries about 0.85-0.87 rad/A there (1-D estimate) against 4.4549 rad/A in the geometric
engine (section 4). This is now stated in the code and refused for atomistic multislice cells
unless acknowledged.

## 7. Test runs (verbatim last lines; `venv/bin/python -m pytest -q -p no:cacheprovider`, 4 shared cores, run one after the other; logs in `SP/x5/`)

    oxide files (the 9 test_oxide_* files of structure, forward_geometric, pipeline, forward,
      except the heavy tests/forward/test_oxide_multislice.py, which runs in the forward directory):
                     244 passed in 17.92s
    tests/structure: 409 passed in 32.72s
    tests/io:        FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
                     1 failed, 127 passed in 1.23s
    tests/pipeline:  197 passed in 238.17s (0:03:58)
    tests/forward:   SKIPPED [2] tests/forward/test_null_readout_known_answer.py:225: L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1
                     SKIPPED [1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1
                     174 passed, 3 skipped in 702.35s (0:11:42)
    full suite (SP/x5/full_suite.txt, 10:40-10:59 UTC, load 5.3 at the start):
                     SKIPPED [2] tests/forward/test_null_readout_known_answer.py:225: L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1
                     SKIPPED [1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1
                     SKIPPED [5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed
                     FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
                     1 failed, 1477 passed, 8 skipped, 12 warnings in 1174.07s (0:19:34)

The full suite collected the working tree as it was, including agent T4's uncommitted files
(`tools/plots/buried_torus.py`, `tests/forward/test_buried_torus_analysis.py`,
`tests/structure/test_buried_assertion_f_layers.py`), which are not X5's. Its one failure is the
same as in the io run. The io failure is, verbatim:

    >           assert aid in rows, aid
    E           AssertionError: B43
    E           assert 'B43' in {'#', 'A1', 'A2', 'A3', 'A4', 'A5', ...}
    tests/io/test_io_config_stand_ins.py:140: AssertionError

It is expected: B43 is registered in `reflection_holo/io/assumption_registry.yaml` (model_rows),
and the row in `docs/model_assumptions.md` is the orchestrator's to write (text in section 8). The
test is not changed or skipped; it passes once the row exists.

Other runs: the four committed review scripts (`tools/review/x5/*_output.txt`; C2 0.7 s; C3 4.3 s and
C4 5.0 s in the scratch pre-run, whose outputs the committed runs reproduce); `tools/hpc/supercell_sizing.py` ("63/63 checks pass; runtime 24 s"); the mutation batch
(section 5); the geometric `oxide_2p0nm` bit-identity run (section 5).

## 8. Proposed text for rows B7, B12, B41, B43 and docs/06 item 12 (for the orchestrator)

**B7** (replace the last sentence, "A comparison run refuses every per-parameter demo stand-in and,
item 12 being blocking, every per-parameter ASSUMPTION (so V_ox and V'_ox, model values in E9, need
a policy decision before a comparison run).", by): "A comparison run refuses every per-parameter
demo stand-in. Since report X5 (audit A9b M2, orchestrator's decision) the consumed-layer count is
DERIVED_HERE (computed by the code from the thickness, density and a-Si values; never a
PROJECT_INPUT); V_ox, V'_ox and the vacuum-edge and interface widths are model parameters, admitted
in a comparison run either as PROJECT_INPUT with a measurement record (what was measured and how;
the gate requires it but cannot verify it) or under the model row B43 (not a stand-in), whose
declared sensitivity bracket every run records; the thickness, the density and the a-Si thickness
remain PROJECT_INPUT item 12, and a comparison run states the thickness and density uncertainties
(a consumed-layer count interval across a rounding boundary needs both parities, audit A9b m2)."

**B12** (replace the parenthesis after "represented as a continuum layer in both engines" and the
end of the first cell by): "(Si consumption f t_ox from the stated densities, the stack placed from
the Si equivalent boundary a/8 above the top atomic plane, with the atomistic crystal's
partial-layer mismatch f t + t_a - N a/4 recorded as an overlap or gap of at most a/8, a gap being
a dip of the laterally averaged potential (B41); vacuum edge AND oxide/Si transition graded over
at least 0.5 A (sharp only with TEST_ONLY flags); consumed-layer counts DERIVED by the
nearest-count rule, refused within 0.05 layer of their rounding boundary unless acknowledged (an
arbitrary numerical guard that does not make the parity robust; comparison runs state the item-12
thickness and density uncertainties and need both parities when the count interval spans a
boundary); optional amorphous-Si layer; per-terrace overrides in the engines but refused by the
pipeline; one evidence label per parameter in the item-12 record; reports E4, X4, X5). For a
NON-CONFORMAL layer on an atomistic crystal the engines disagree: the crystal loses whole layers
only, so the multislice gives about 0.85-0.87 rad/A for a sub-layer thickness difference (A9b's
1-D laterally averaged estimate: 0.8455, 0.8729, 0.8599 rad/A, near the top-surface rate 0.886
rad/A) where the geometric engine applies the continuum grown-oxide rate 4.4549 rad/A (B41 values,
16.1347 mrad; one consumed layer 13.6998 rad), a difference of 3.58-3.61 rad per A of sub-layer
thickness difference (`tools/review/x5/a9b_c4_nonconformal_output.txt`); an atomistic multislice
cell whose terraces carry different thicknesses is refused unless acknowledged (TEST_ONLY; audit
A9b M1); a propagated two-terrace multislice was not run. Its atomistic content is NOT
IMPLEMENTED."

**B41** (replace the parts named; everything else stays):
* "the exact 1-D reflectivity of the 0.5 A vacuum edge is 1.95e-9 at 16.1347 mrad (|r| x 8.5e-4 of
  the sharp edge; transfer matrix, audit A8 C6), which the multislice engine reproduces (1.835e-9
  against 1.8345e-9 at its central bin); line 241's Born factor exp(-(q w)^2) is 57 times lower
  (an underestimate)" -> "the exact 1-D reflectivity of the 0.5 A vacuum edge is 1.9545e-9 at
  16.1347 mrad (|r| x 8.513e-4 of the sharp edge; ODE and transfer matrix, audits A8 C6 and A9b C2,
  `tools/review/x5/a9b_c2_edge_output.txt`), which the multislice engine reproduces at its central
  bin 16.1751 mrad (1.8350e-9 against 1.8345e-9); line 241's Born factor exp(-(q w)^2) gives
  3.44e-11, 56.8 times lower (an underestimate)".
* "consumed layers 7 (5) = the nearest whole count of 6.50 (4.88) a/4 layers (lines 125-127); at
  2.0 nm the count lies 0.0036 layer (0.005 A) from its rounding boundary: it is 6 below 2.19877
  g/cm^3 (-0.056 %), ... (a count closer than 0.05 layer to its boundary is refused without it,
  audit A8 m4)" -> "consumed layers 7 (5) = the nearest whole count of 6.50 (4.88) a/4 layers
  (lines 125-127), DERIVED_HERE by the code from the B41 thickness and density (audit A9b M2); at
  2.0 nm the count lies 0.0036 layer (0.0049 A) from its rounding boundary: it is 6 below 2.19877
  g/cm^3 (-0.056 %; `tools/review/x5/x5_oxide_numbers_output.txt`), so at <110> the terrace type
  at a buried a/4 step is set by the fourth significant digit of an assumed density; the 2.0 nm
  variants therefore state rounding_boundary_acknowledged: true (a count closer than 0.05 layer to
  its boundary is refused without it, audit A8 m4; 0.05 layer is an arbitrary numerical guard,
  audit A9b m2)".
* after "(a gap; 0.166 A at 1.5 nm), recorded as interface_overlap_A and measured on the engine's
  potential (audit A8 M2, report X4)" add: "; the gap is a dip of the laterally averaged potential
  inside the stack, to 4.84 V at 0.96 A above the kept top atomic plane, whose own Born reflectivity
  at q = 2 k'_ox is |r|^2 = 1.7e-12 and which changes the 1-D (0,0,8) reflection at 16.1347 mrad by
  -0.05 % in |r| and +0.023 rad in phase against a stack joined to the crystal, common to every
  terrace of a conformal layer (1.5 nm, gap 0.166 A: +0.01 %, +0.009 rad; audit A9b C3, a 1-D
  laterally averaged estimate, `tools/review/x5/a9b_c3_gap_output.txt`)".
* "Every parameter carries the label ASSUMPTION B41 (per-parameter labels, audit A8 M1); B41
  vouches for these values only: B41 with overlayer none or with any other value is refused (audit
  A8 m2)." -> "Every parameter carries the label ASSUMPTION B41 (per-parameter labels, audit A8 M1)
  except the consumed-layer count, which is DERIVED_HERE (audit A9b M2); B41 vouches for these
  values only, and in each variant named above for that variant's thickness only: B41 with
  overlayer none, with any other value, or with the other thickness in a named variant is refused
  (audits A8 m2, A9b n2)."
* column "consequence", after "TDS in the layer" add: "; for a non-conformal layer on the atomistic
  crystal, the grown-oxide term of a sub-layer thickness difference in the multislice (B12; audit
  A9b M1)".

**B43** (new row):

| B43 | Continuum-oxide MODEL parameters (report X5 after audit A9b M2; E9 M1, M4): a model row, NOT a stand-in for any PROJECT_INPUT and not demo-only. V_ox = 10.34 V, the independent-atom value of SiO2 at 2.20 g/cm^3 (`tools/review/e9_recompute_output.txt` line 166), with the declared sensitivity bracket 10.1-11.5 V (the two inconsistent measurements, B7); V'_ox = 0.40 V (1/(2 sigma Lambda) = 0.4024 V for Lambda = 1705 A, line 20; a model value from measured inelastic mean free paths, not a bound, E9 M1), declared bracket 0 or 0.39-0.44 V (B7); vacuum-edge width w_v and oxide/Si interface width w_i 0.5 A each: a numerical requirement (E9 M4, audit A8 m5: the grading that suppresses the layer's own edge reflections, 1.9545e-9 at 16.1347 mrad for the vacuum edge), NOT a measured roughness, no bracket. Admitted as the per-parameter label "ASSUMPTION B43" of V_ox, V'_ox, w_v and w_i inside a PROJECT_INPUT (or TEST_ONLY) item-12 record, comparison runs included; it vouches for the nominal values and the bracket ends only; every run records per parameter the value, "nominal" or "bracket end", and the declared bracket (manifest `extra.oxide_item12`, summary `oxide_item12`); the gate does not require the bracket ends to be run. A value measured on the witness piece replaces a B43 value only as PROJECT_INPUT with a measurement record (what was measured and how). Code: `reflection_holo/pipeline/config.py` (`OXIDE_MODEL_ROWS`), `reflection_holo/io/assumption_registry.yaml` (model_rows) (report X5). | ASSUMPTION (nominal values REPRODUCED via E9; brackets SECTION_READ via L8/E9; the choice of nominal value is ASSUMPTION) | V_ox is the IAM value at 2.20 g/cm^3; at another supplied density the IAM value changes by 4.6997 V per g/cm^3 (E9 line 170), which B43 does not follow (a B43 V_ox with a measured density is therefore a model choice to be stated); V'_ox is not to be multiplied with B38 (E9 M1). |

**docs/06 item 12** (append to the list "from a witness piece prepared identically, the oxide
thickness with its convention (XPS thermal-oxide equivalent or XRR), any amorphous Si under it,
interface roughness and carbon"): "; for the oxide thickness AND its density, the uncertainty of
each (one standard uncertainty or an interval half-width, stated which): at 2 nm the consumed-layer
count moves by +-0.325 layer per +-1 A of thickness and +-0.148 layer per +-0.05 g/cm^3 of density
(`tools/review/x5/x5_oxide_numbers_output.txt`), so the count, and at <110> the terrace type at a
buried a/4 step, can change within the uncertainty; the simulation then runs both parities (audit
A9b m2). If the mean inner potential or the electronic absorption of the oxide, or the width of
its surface or interface grading, is measured, state what was measured and how (method,
instrument, reference); otherwise the model values of row B43 are used and their bracket is
recorded (audit A9b M2)."

## 9. NOT RUN, and what remains open

NOT RUN:
* A propagated two-terrace multislice of a non-conformal oxide (as instructed). The size of the
  disagreement rests on A9b's 1-D laterally averaged model (an estimate) and on the engines'
  formulas; the new refusal is a cell-construction check.
* Any run at the B43 bracket ends (the gate does not require them; only in-memory configuration
  tests load bracket-end values, and one geometric demo run at V_ox = 11.5 V inside
  `test_run_records_the_model_row_bracket` checks the record, not the physics).
* A comparison run with a real item-12 record (none exists); the comparison gate was exercised only
  with fabricated TEST records in memory, and those runs are refused anyway for the demo's other
  stand-ins.
* A laid-out oxide cell in the sizing tool: the "with oxide" column is only relabelled a same-grid
  lower bound (A9b C8's scaling estimate of the geometry terms is not scripted by X5).
* cupy/GPU; the [110] multislice with the layer; the a-Si layer in propagation; an independent
  solver with the layer (as A8, A9b).

Open (not in the decisions; for the orchestrator):
* The a-Si potentials V_a, V'_a (label `amorphous_si_potential`, only when t_a > 0) are model values
  like V_ox and V'_ox, but the decision keeps "a-Si as before": in a comparison run they can still
  only be PROJECT_INPUT, without a measurement record. B43 does not cover them.
* B43's V_ox (10.34 V) is the independent-atom value at 2.20 g/cm^3; with a measured density that
  differs, the IAM value moves by 4.6997 V per g/cm^3 (E9 line 170), which B43 does not follow.
* The a-Si thickness has no uncertainty field; the count interval takes it at its value.
* list-inputs shows the per-parameter labels (consumed_layers now "DERIVED_HERE") but no rows for
  the optional measurement and uncertainty keys.
* A9b n4 (memory model of a continuum crystal with the layer, conservative) and n5 (list-inputs
  view of B41 with none) were not in X5's brief and are unchanged.
* The rows B7, B12, B41, B43 and docs/06 item 12 (section 8) are the orchestrator's; until B43 is a
  row, `test_registry_ids_exist_in_model_assumptions` fails (section 7).

## Final status

FINAL. All fixes asked for are implemented as decided: A9b-M1 (a) stated with its size in
`NOT_REPRESENTED`, `B4_OXIDE_GROWN` and every non-conformal step record, (b) atomistic multislice
cells with different terrace thicknesses refused unless `nonconformal_sublayer_acknowledged`
(TEST_ONLY), (c) A9b's C4 committed; A9b-M2 (a)-(d) (DERIVED_HERE count, B43 model row or a
PROJECT_INPUT with a measurement record for the model parameters, the bracket in the manifest,
thickness and density PROJECT_INPUT, mixed headline); m1; m2 (arbitrary guard stated, item-12
uncertainties required in comparison runs, both parities acknowledged across a boundary); m3 and m4
(the code quotes digits printed by committed scripts); n2; n3; m6 (text only). Every reversion
fails at least one test (section 5, 26 mutations and a control). The geometric B41 demo arrays are
bitwise unchanged. Test runs: structure 409 passed; pipeline 197 passed; forward 174 passed, 3
skipped; io and the full suite fail only on the missing B43 row of docs/model_assumptions.md (1
failed, 1477 passed, 8 skipped), which the orchestrator adds with the text of section 8.
Nothing committed; nothing written under outputs/ (`git status --short outputs/` and
`find outputs -newer` empty after the last run); docs/ unchanged except this report.
