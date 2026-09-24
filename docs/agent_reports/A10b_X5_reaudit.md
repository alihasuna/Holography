# A10b - Re-audit of X5 (fixes of audit A9b on the continuum-oxide overlayer)

Auditor: agent A10b, 2026-09-24. Status: FINAL (written incrementally).

Scope: repository /home/user/Holography, branch claude/electron-holography-orchestration-nakd7r,
commit 00851da. During the audit the orchestrator committed b4177ce ("Snapshot: re-audit A10b
(X5) report in progress, DRAFT"). It changes only this report:
`git diff --stat 00851da HEAD -- reflection_holo tests configs tools scripts` is empty.

Read in full:
* docs/agent_reports/A9b_X4_audit.md and docs/agent_reports/X5_a9b_fixes.md;
* `git diff 62ced11..00851da` of `structure/oxide.py`, `structure/si001.py`, `forward/cell.py`,
  `forward/geometric/model.py`, `pipeline/config.py`, `pipeline/run.py`,
  `io/assumption_registry.yaml`, `configs/demo_smoke_si001.yaml`, `tools/hpc/supercell_sizing.py`
  and its output;
* the three new a9b test files and the diffs of the changed oxide tests;
* `tools/review/x5/` (four scripts, four outputs);
* rows B7, B12, B41 and B43 of docs/model_assumptions.md, and docs/06 item 12;
* the current `oxide.py` (700 lines), and the item-12 part of `pipeline/config.py` (lines 40-82,
  692-800, 935-960, 1000-1600) with its callers in `engines.py`, `estimates.py`, `run.py`,
  `__main__.py`, `feature_cell.py`, `forward/multislice/overlayer.py`, `scripts/hpc/alliance/kit.py`
  and `scripts/torus/run_torus_multislice.py`.

Rules kept:
* This report is the only repository file written. The code under audit was not modified;
  mutations were made in scratch copies only.
* Nothing was committed by me.
* Nothing was written under outputs/: `git status --short outputs/` and
  `find outputs -newer SP/a10b/d1_probes.py -type f` were both empty after the last run.
* Scratch files are in SP/a10b/, where SP =
  /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
* Every run was single-threaded (OMP_NUM_THREADS=1), because a full suite ran concurrently.

Grades: MAJOR (must be resolved before the affected item is adopted; a reproduction is given),
minor, note.

## Verdict table (question 1)

| A9b finding | X5 status | A10b verdict | reverting the fix makes a test fail? (D5, own mutations) |
|---|---|---|---|
| M1 non-conformal engines disagree | FIXED (stated with size; atomistic cell refused unless TEST_ONLY acknowledged; C4 committed) | FIXED as decided. The statement, its size and the per-step record are correct and printed by a committed script. The guard checks thickness only, so a cell with ONE thickness and two counts passes it (A10b-n1; tie window 2e-9 A, engine level only) | yes: guard not called (A1) 3 failed; guard sees one thickness (A2) 3 failed; size without 1/f (A3) 2 failed |
| M2 label policy | FIXED (DERIVED_HERE count, B43 or measurement record, thickness/density PROJECT_INPUT, mixed headline) | PARTLY FIXED. (a) DERIVED_HERE count, (c) B43 refused on thickness/density/a-Si/count and (d) headline: correct. (b) The measurement-record requirement passes '?', 'measured.' and 'not measured: ...' (**A10b-M2**). The a-Si potentials stay PROJECT_INPUT-only without any record (A10b-m1, stated by X5 and in B43) | yes: derived check (A4) 1; pipeline label rule (A5) 3; record required (A7) 1; placeholder filter (A8) 1; statement in the label (A9) 1; B43 values (A14) 4; nominal only (A15) 4; B43 on thickness (A16) 2; gate refuses B43 (A17) 1; `used` field (A19) 4 |
| m1 B26 per parameter | FIXED | FIXED | yes: A6 3 failed |
| m2 0.05-layer rationale | FIXED (arbitrary guard stated; uncertainties required; both parities acknowledged) | PARTLY FIXED. The rationale is removed and the uncertainties are required. But "both parities" is only an acknowledgement, and the other parity cannot be run under honest labels (**A10b-M1**). The uncertainty convention cannot be stated (A10b-m2). The a-Si thickness uncertainty is ignored (A10b-m3) | yes: both-parities gate (A10) 1; uncertainties required (A11) 1; stand-in uncertainties (A12) 1; wrong box corner (A13) 1 |
| m3 numbers not printed | FIXED (C2 committed) | FIXED. The four scripts reproduce their saved outputs byte for byte (D6). The digits in code and rows match the prints. The engine's 1.8350e-9 is printed by the committed test (D8), but only its presence as a string is asserted (A10b-n3) | X5 X22 (not repeated) |
| m4 gap dip | FIXED (text, C3 committed) | FIXED (digits match `a9b_c3_gap_output.txt`) | X5 X23 (not repeated) |
| m5 X4 report | not X5's; values in X5 section 6 | X4's report is still DRAFT with its four placeholders (lines 140, 184, 196, 229). The values in X5 section 6 match A9b's saved outputs (checked) | n/a |
| m6 sizing "with oxide" column | FIXED (text only) | PARTLY FIXED. The column is now labelled a same-grid lower bound. No oxide cell is laid out and the geometry terms are not printed (A10b-n6). The clean-surface numbers are unchanged (D10) | X5 X26 (not repeated) |
| n1 headline | FIXED | FIXED. The headline is never PROJECT_INPUT alone; in the pipeline it is always "mixed (...)" because the count is DERIVED_HERE | yes: A18 1 |
| n2 B41 variant tie | FIXED | FIXED (D11) | X5 X24 (not repeated) |
| n3 copied comment | FIXED | FIXED (9.0563 A, D7) | X5 X25 (not repeated) |
| n4, n5 | not in brief | unchanged | n/a |
| n6 B12 wording | taken into B12 | done: B12 now says "partial-layer mismatch f t + t_a - N a/4" | n/a |

D5 control: 119 passed, 1 deselected. Every mutated copy imported its own package (the printed
`reflection_holo/__init__.py` lies in `SP/a10b/mut/<name>/`). The deselected test,
`test_run_records_the_model_row_bracket`, writes a manifest and needs git; X5's X14 covers it.

The five checks the orchestrator asked for were reproduced by mutation:
* the M1 guard (A1, A2);
* the DERIVED_HERE count check (A4, A5);
* the B26 refusal (A6);
* the measurement-record requirement (A7, A8, A9);
* the both-parities gate (A10).

Each one makes at least one test fail. No existing assertion was weakened (X5 section 3 diffs
read).

## Findings

### MAJOR

**A10b-M1. "Both parities" is only acknowledged, never run. The other parity cannot be produced
without mislabelling a measured value as PROJECT_INPUT. docs/06 tells Ali the opposite.**

The code:
* `pipeline/config.py:1436-1449` (`_check_oxide_uncertainties`): when the count interval spans a
  rounding boundary, the run passes with `both_parities_acknowledged: true`.
* The run then builds ONE count: the derived nominal count, which the stated count must equal
  (`config.py:1368-1376`).
* Nothing runs, schedules, links or checks a run at the other parity.
* The item-12 record (`oxide_item12_record`, `config.py:1465-1508`) has no field naming the parity
  this run covers or a companion run.

The documents:
* docs/06 item 12 (line 29): "the simulation then runs both parities".
* B12: comparison runs "need both parities when the count interval spans a boundary".
* B7: "needs both parities".
* The `config.py` docstring (line 80): "(both parities must then be run)".

The other parity cannot be made with the measured values:
* `consumed_layers: 6` at the measured 20.0 A and 2.20 g/cm^3 is refused by the derived-count
  check.
* At engine level it is refused by the nearest-count rule: |6 a/4 - 8.8301 A| = 0.684 A > a/8.
* The pipeline refuses per-terrace overrides.

The only route is to move a PROJECT_INPUT value inside the uncertainty box, for example a
thickness of 19.5 or 19.0 A. The gate accepts this with the label "PROJECT_INPUT item 12 (...)",
although the value is not the measured one. No admissible label exists for such a value: B43 is
refused on the thickness, and B41 is refused in comparison runs and off its (t, N) pairs.

Reproduction (D2: `SP/a10b/d2_parity.py`, output `d2_parity.out`; fabricated TEST supply,
in-memory). Here and below, "OXIDE ENTRIES PASS" means the comparison gate refuses only the demo's
other stand-ins and names no oxide entry:

    [REFUSED (comparison gate, other items only; OXIDE ENTRIES PASS)] acknowledged True -> oxide entries pass the comparison gate
    [ACCEPTED] same, demo purpose (to read the record)
          recorded count interval: {'counts': [6, 7], 'parities': ['even', 'odd'], 'spans_boundary': True, 'continuum_layers_min': 6.0380342751098555, 'continuum_layers_max': 6.984017613193163}
          the run's spec: consumed_layers = 7 ; terrace overrides: None None
          keys of the item-12 record naming the parity actually run or the companion run: []
    [REFUSED] consumed_layers 6 at t 20.0 A (measured)
    [REFUSED] engine-level spec: count 6 at 20.0 A / 2.20 (TEST_ONLY labels): terrace 0: consumed_layers = 6 (8.1463 A) is not the whole-layer count nearest to the continuum depth ...
    [REFUSED (comparison gate, other items only; OXIDE ENTRIES PASS)] thickness_A 19.5 (inside the box, NOT the measured 20.0) labelled PROJECT_INPUT, count 6, comparison
    [ACCEPTED]    same, demo purpose: its thickness label
          thickness label: PROJECT_INPUT item 12 (TEST: fabricated supply to exercise the gate (audit A10b))
    [REFUSED] thickness 19.5 labelled ASSUMPTION B41 (the only ASSUMPTION a thickness can carry), comparison
          ... stand-in B41 ... states (thickness_A, consumed_layers) in [(20.0, 7), (15.0, 5)], got (19.5, 6)

Why it matters:
* At <110> the parity decides the terrace type at every buried a/4 step (E9 section 3 item 2),
  and so the sign of the residual delta.
* At 2 nm any realistic witness uncertainty spans the boundary. The committed
  `x5_oxide_numbers_output.txt` already gives counts [6, 7] for +-0.1 A and +-0.01 g/cm^3.
* A comparison result would carry one parity while docs/06 tells Ali both were run.
* The second run is possible only by labelling an unmeasured thickness PROJECT_INPUT. That breaks
  the decision's rule that a label must not read PROJECT_INPUT when the value is not one.

Fix needed, one of:
* (a) Make the pipeline run both parities. For example, allow a consumed-layer count override
  labelled DERIVED_HERE ("other count of the item-12 interval"), admitted only when the interval
  spans a boundary, and link the pair in both manifests.
* (b) Refuse comparison runs whose interval spans a boundary.
* (c) At minimum, record in `oxide_item12` the count and parity this run covers and that the other
  parity was NOT run, and correct docs/06 item 12, B7, B12 and the `config.py` docstring. For
  example, replace "runs both parities" with "records that only one parity was computed; the
  other must be run and compared before a result is quoted".

**A10b-M2. The measurement-record requirement passes one-character, punctuated and explicit
"not measured" records. A comparison run can still carry an unmeasured model value labelled
PROJECT_INPUT.**

`pipeline/config.py:1017, 1197-1202`: the text is lower-cased and its whitespace folded. It is
then refused only if it EQUALS one of seven words (`_MEASUREMENT_PLACEHOLDERS`) or a
`NON_SUPPLIERS` entry. Punctuation, single characters and statements that say the value was not
measured all pass.

D1 (`SP/a10b/d1_probes.py`, `d1_probes.out`): V_real is labelled PROJECT_INPUT, the other model
parameters carry B43, the uncertainties are stated and the purpose is "comparison".

    [... OXIDE ENTRIES PASS] measurements.V_real = '?'                  (also '-', '.', 'x', '...')
    [... OXIDE ENTRIES PASS] measurements.V_real = 'measured.'          (while 'measured' is refused)
    [... OXIDE ENTRIES PASS] measurements.V_real = 'not measured'
    [... OXIDE ENTRIES PASS] measurements.V_real = 'not measured: independent-atom model value, E9 out:166'
    [... OXIDE ENTRIES PASS] measurements.V_real = 'ASSUMPTION B43'     (also 'B43', 'nominal', '10.34 V')
    [... OXIDE ENTRIES PASS] measurements.V_real = 't.b.d.'             (while 'TBD' is refused)
    [... OXIDE ENTRIES PASS] measurements.V_real = 'unknown.'           (while 'unknown' is refused)
    [... OXIDE ENTRIES PASS] measurements.V_real = 'to be supplied'     (also 'pending', 'yes.', 'Measured!')
    [REFUSED] 'N/A', 'none', 'TBD', 'measured', '  '

The spec label then reads "PROJECT_INPUT item 12 (...; measured: not measured: independent-atom
model value ...)". This is the substance of A9b-M2: an unmeasured model value labelled
PROJECT_INPUT in a comparison run.
* X5 section 1 says "placeholders refused".
* The test (`test_measurement_record_for_project_input_model_parameters`) checks only 'measured',
  '  ' and 'TBD'.
* Mutation A8 (filter reduced to "not empty") is caught only through those three strings.

The gate cannot verify a statement. It can refuse what is plainly not one, and here the bypass is
easy to make by accident ("measured." with a full stop).

Fix needed:
* a structured record, e.g. {quantity, method, instrument_or_reference, value, uncertainty}, each
  field non-empty and not a placeholder after stripping punctuation;
* refusal of records that contain "not measured", "model", "assumption", "nominal" or a
  model_assumptions row id;
* optionally, a refusal or a recorded warning when a "measured" value equals the B43 nominal value
  exactly;
* tests for the punctuation variants.

### minor

**A10b-m1. The a-Si potentials are still model values that a comparison run admits only as
PROJECT_INPUT, and no measurement record can be attached to them.**

D2 (a-Si 5 A; V_a 12.0 V and V'_a 0.5 V labelled PROJECT_INPUT; no record; purpose comparison):
OXIDE ENTRIES PASS. D1 shows the other two routes are closed:
* a record for them is refused: "exactly the model parameters labelled PROJECT_INPUT ([]) carry a
  measurement record, got ['amorphous_si_potential']";
* B43 on them is refused.

So for V_a and V'_a, A9b-M2 is unchanged. This is recorded, not hidden: X5 section 9 and row B43
say "The a-Si potentials remain PROJECT_INPUT-only in comparison runs".

Fix needed: add `amorphous_si_potential` to `OXIDE_MODEL_PARAMETERS` (so it needs a measurement
record), or refuse t_a > 0 in comparison runs until a model row for a-Si exists.

**A10b-m2. docs/06 asks Ali to state which uncertainty convention he uses, but the configuration
has no field for it and the code treats every value as an interval half-width.**

docs/06 item 12 asks for "the uncertainty of each (one standard uncertainty or an interval
half-width, stated which)". But:
* `oxide_spec_from_config` refuses any extra key (D1: `uncertainty_convention` -> REFUSED as an
  unknown key);
* `consumed_count_interval` (`oxide.py:441-477`) always uses the box (t -+ u_t, rho -+ u_rho).

A one-sigma value is thereby read as a half-width. The count interval then spans only a one-sigma
box, and a count that looks robust can change within two sigma.

Fix needed: a required, enumerated `uncertainty_convention` key, with a coverage factor applied to
a standard uncertainty (or standard uncertainties refused), recorded in `oxide_item12`.

**A10b-m3. The count interval ignores the a-Si thickness uncertainty. Per angstrom it moves the
count 2.3 times more than the oxide thickness does.**

`consumed_count_interval` takes t_a at its value (`oxide.py:457, 464-465`). docs/06 asks for thickness
and density uncertainties only. D7 (independent):
* +-1 A of a-Si gives +-0.7365 layer;
* +-1 A of oxide gives +-0.3252 layer.

A "measured zero" of a-Si (the X4 route) is a detection limit, and that limit is an uncertainty
the interval treats as 0. X5 section 9 lists this as open. B12, B7 and docs/06 do not mention it.

Fix needed: an a-Si thickness uncertainty in item 12 and in the interval (for a measured zero:
the detection limit), or a sentence in B12 and docs/06 that the interval assumes an exact a-Si
thickness.

### note

* **A10b-n1. The M1 guard keys on thickness only.**
  * `forward/cell.py:249-251` returns None when all terrace thicknesses are equal. `terrace_stacks`
    calls the layer non-conformal when the COUNTS differ (`oxide.py:626-627`).
  * At the rounding tie (depth within `_TOL_A` = 1e-9 A of (N + 1/2) a/4, with the rounding
    acknowledgement) both counts pass the nearest-count assertion.
  * D3 (`SP/a10b/d3_m1_edge.py`), at t = 19.988820254914156 A with counts (6, 7): the structure is
    built with "conformal False", and its step record says the multislice does not represent a
    -3.0752 A sub-layer difference (about 11.0 rad, i.e. about 1.5 rad mod 2 pi on the 1-D model).
    Then "[CELL BUILT] nonconformal_sublayer record present: False". An acknowledgement is refused
    ("the terraces carry one thickness: ... not needed").
  * This is reachable only at engine level, inside a 2e-9 A window.
  * Fix: key the guard on `record["conformal"]`.
  * Related: `si001.py:892-893` compares thicknesses with an exact `==`, while `terrace_stacks`
    uses `round(., 12)`. In D3, 20.0 against 20.0 + 1e-13 gives `conformal True` in the record
    and `conformal_at_step False`, with a 0.0000 A sub-layer note.
* **A10b-n2. Edge cases of the interval.** D2 Q4d:
  * An upper corner exactly on a boundary counts as a span ([4, 5, 6]).
  * A lower corner exactly on 4.5 does not ([5]), although the tie admits count 4. This happens
    only at an exact floating-point tie.
  * No floor exists on the uncertainties. u_t = 1e-6 A with u_rho = 1e-6 g/cm^3 passes a 2 nm
    comparison without the both-parities acknowledgement (D2 Q4c). The gate cannot verify
    uncertainties either; a floor (e.g. 0.1 A) or a recorded plausibility note would help.
* **A10b-n3. The engine value is checked as a string only.**
  `test_edge_reflectivity_quotes_the_printed_digits` asserts that "1.8350e-9" is in the text and
  that the test source holds the format string. It does not compare against the engine's output.
  The engine value is held by X4's 1 % |r| test (2 % in |r|^2). D8 reprinted
  `w = 0.5 A: |r|^2 = 1.8350e-09` today, so the quote is currently right.
* **A10b-n4.** The `pipeline/config.py` line numbers in X5 sections 1-2 are about 12 lines low:
  1146-1153 is at 1158-1164, 1371-1451 at 1383-1449, 1453-1501 at 1465-1508, 1560 at 1570-1572.
  The `oxide.py` numbers are right (154-167, 168, 413-426).
* **A10b-n5.** B43's V_ox does not follow a measured density. D1: V_real 11.5 V under B43 at a
  measured 2.30 g/cm^3 is accepted, while the IAM value there is 10.81 V. The run record has no
  note of the mismatch. The B43 consequence column says "a B43 V_ox with a measured density is
  therefore a model choice to be stated", but no field exists to state it.
* **A10b-n6 (A9b-m6).** The sizing tool's oxide column is now labelled a same-grid lower bound.
  No oxide cell is laid out, and A9b's geometry-term estimate is not scripted. So no oxide-covered
  figure is available to quote to Ali.

## Question 2: label-policy loopholes (D1, D2, D11)

| question | answer | evidence |
|---|---|---|
| unmeasured model value labelled PROJECT_INPUT in a comparison run WITHOUT a record? | V_ox, V'_ox, w_v, w_i: no. **The a-Si potentials: yes** (A10b-m1) | D1 "needs a measurement record"; D2 |
| empty or placeholder record passes? | empty or whitespace: no. **Placeholders: yes** ('?', 'measured.', 'not measured', 'B43', ...; A10b-M2) | D1 |
| B43 vouches for a value outside nominal and bracket ends? | no. 10.2, 11.6, 0.395, 0.45 and 0.7 A are refused. 10.1, 11.5, 0.0, 0.39, 0.44 and the nominal values are accepted. Tolerance rel 1e-12 (10.100000000001 is accepted and recorded with its own value) | D1 Q2c; mutations A14, A15 |
| B43 for thickness, density, a-Si, count? | no, each refused ("covers only the model parameters"); the count takes DERIVED_HERE only | D1 Q2d; A16 |
| B43 as a record-level stand-in? | no: refused at io load ("'B43' is not mapped to PROJECT_INPUT item 12") | D11 |
| B43 inside the B41 stand-in record? | no ("every parameter carries its id") | D1 |
| count forced? | no. 6, 8, 7.0, '7' and True are refused; the labels 'DERIVED_HERE ', 'derived_here', 'DERIVED_HERE (my own count)', PROJECT_INPUT and TEST_ONLY on the count are refused, as is DERIVED_HERE on the thickness. The only lever is the PROJECT_INPUT thickness or density (A10b-M1) | D1 Q2e; A4, A5 |
| missing item-12 field silently defaulted? | labels, count, rounding acknowledgement, the three uncertainty keys (all or none) and the records: none defaulted (D1 Q2g). **Silently assumed:** the uncertainty convention (half-width; A10b-m2) and the a-Si thickness uncertainty (0; A10b-m3) | D1 Q2g |
| headline reads PROJECT_INPUT while a parameter is not? | no: "mixed (DERIVED_HERE, PROJECT_INPUT)", "mixed (ASSUMPTION B43, DERIVED_HERE, PROJECT_INPUT)", "mixed (ASSUMPTION B41, DERIVED_HERE)". Per-parameter labels can read PROJECT_INPUT for a non-measured value (A10b-M1, A10b-M2) | D1 Q2f; A18 |
| bracket ENDS under B43: consistent with the row, recorded per parameter? | yes. Row B43 says "vouches for the nominal values and the bracket ends only; every run records per parameter the value, 'nominal' or 'bracket end', and the declared bracket". `model_rows` records parameter, key, value, nominal, `used`, bracket and bracket_ends, and the note "the gate does not require the bracket ends to be run" (D1 Q2c, D4). The ends of V_ox are the two measured central values (10.1, 11.5), not their uncertainty extremes (9.5-11.8), as B7 and B43 state | D1, D4 |

## Question 3: the non-conformal guard and the unchanged geometric engine

These are all the paths that build an atomistic multislice cell. Callers found with
`grep build_reflection_cell|build_continuum_oxide_cell|build_feature_cell` over reflection_holo,
scripts and tools:
* engine level: `forward/cell.build_reflection_cell` calls `_nonconformal_sublayer` for every
  oxide structure (`cell.py:105`).
* pipeline run, run-member and dry-run (`pipeline/estimates.py:135` and
  `engines.reflection_cell`, `engines.py:275-281`) all go through `build_reflection_cell`. The
  pipeline builds conformal layers only (`nonconformal_sublayer_acknowledged=False`, no overrides,
  `config.py:1264-1267`).
* the feature path (`feature_cell.build_feature_reflection_cell`, used by
  `scripts/torus/run_torus_multislice.py`) goes through `build_reflection_cell`. Its structure
  builder fixes `overlayer=None` (`features.py:747`), and the pipeline refuses an oxide on the
  feature path.
* the HPC kit (`scripts/hpc/alliance/kit.py`) loads pipeline configurations and uses
  `pipeline dry-run` (conformal).
* `tools/hpc/supercell_sizing.py` and `review_h5_recompute.py` build clean cells only
  (`overlayer=None`).
* `build_continuum_oxide_cell` (continuum crystal) is exempt by design, since its boundary moves
  continuously; the test checks this.
* `ContinuumOxidePotential` does not re-check the guard. It asserts the spec hash against the
  cell's record, so it cannot be given a spec other than the one the guarded cell was built with.

Every path reaches the guard, subject to the thickness-only key (A10b-n1).

Geometric engine: the diff of `forward/geometric/model.py` is inside the module docstring only.
D4 at 00851da (`SP/a10b/d4_bitid.py oxide_2p0nm`, 4.8 s):

    built 2.71545 measured +2.7153 +- 0.0165 / -1.357725 -1.3578 +- 0.0082 / -1.357725 -1.3575 +- 0.0082
    vs a9b/pipe: arrays 26 vs 26; bitwise identical 26
    vs x5/pipe:  arrays 26 vs 26; bitwise identical 26
    vs a8:       arrays 26 vs 26; bitwise identical 26          (A8's run of E4's pre-fix code)
    manifest extra.oxide_item12 headline: mixed (ASSUMPTION B41, DERIVED_HERE); ... summary oxide_item12 == manifest: True

Conformal multislice demo through the guard (D12, `multislice_tiny_oxide_2p0nm`, 18.9 s): `vs
a9b/pipe: arrays 26 vs 26; bitwise identical 26`. Heights are withheld ("measured None"), as in
A8 and A9b. Against A8 20 arrays differ, as expected, because X4 moved the stack (A8-M2).

## Question 4: the count interval and the both-parities gate

Arithmetic, independently from first principles with no package import (D7,
`SP/a10b/d7_numbers.py`):

    rho_Si 2.329195 g/cm^3; a/4 1.357725 A; f(2.20) 0.441507
    +-1 A of thickness: 0.4415 A of depth = 0.3252 layer                 (quoted +-0.325)
    +-0.05 g/cm^3 at 20 A: 0.2007 A = 0.1478 layer                       (quoted +-0.148)
    +-1 A of amorphous Si (enters 1:1): 0.7365 layer                     (not in the interval, A10b-m3)
    0.05 layer = 0.06789 A depth = 0.15376 A of thickness = 0.7688 % of rho = 0.01691 g/cm^3
    t 20 A: 6.50364 layers, margin 0.00364 layer = 0.00494 A; count 6 below 2.198770 g/cm^3 (-0.0559 %) or 19.98882 A
    box t 20+-1.0, rho 2.20+-0.05: 6.038-6.984 layers -> counts [6, 7]   (x5 output identical)
    box t 15+-2.0, rho 2.20+-0.1: 4.035-5.779 layers -> counts [4, 5, 6]

* The corner rule is correct: the depth f(rho) t + t_a increases with both t and rho.
* The box adds the two contributions linearly (+-0.473 layer at 2 nm, against +-0.357 in
  quadrature), which is conservative for half-widths (but see A10b-m2).
* Boundary edge cases: A10b-n2.

Is "runs both parities" enforced? No: it is only acknowledged, and the other parity cannot be
produced under honest labels (A10b-M1). The acknowledgement itself is enforced both ways:
* A10: without it the run is refused;
* X5's X19: an unneeded acknowledgement is refused.

## Question 5: numbers in code strings and rows

The four committed scripts rerun at HEAD reproduce their saved outputs byte for byte (D6):
* `x5_oxide_numbers` 0.16 s;
* `a9b_c2_edge` 0.70 s;
* `a9b_c3_gap` 4.42 s;
* `a9b_c4_nonconformal` 5.46 s.

| quoted number (where) | printed by | verdict |
|---|---|---|
| 4.4549 rad/A, 13.6998 rad = 3.0752 A, 0.8857 (0.886), 0.8455/0.8729/0.8599 (0.85-0.87), 3.58-3.61, 2.23 vs 0.42-0.44 rad (NONCONFORMAL_SUBLAYER, B4_OXIDE_GROWN, B12, cell refusal) | c4 output (QUOTE lines) | OK. D7 recomputes 4.4549, 0.8857, 13.6998 and 3.6094/3.5820/3.5950. Labelled a 1-D laterally averaged estimate, with "a propagated two-terrace multislice was not run". The mod-2 pi use of "sub-layer difference x rate" holds on the 1-D table: over one whole layer the difference is 12.568 rad = 2.000 x 2 pi (D7) |
| 1.9545e-9, 8.513e-4, 2.697e-3, 3.44e-11, 56.8, 1.8345e-9, 58.4 (EDGE_W05_REFLECTIVITY, docstrings, B41, B43) | c2 output (QUOTE) | OK |
| engine 1.8350e-9 (B41, oxide.py) | committed test with -s (D8: "w = 0.5 A: \|r\|^2 = 1.8350e-09 ... EXACT ... 1.8346e-09 ... 58-fold") | OK. 1.8346 (coarse TM in the test) against 1.8345 (converged ODE) is explained by X5. String-only guard: A10b-n3 |
| 4.84 V at 0.96 A, 0.674 A, 1.7e-12, -0.05 %, +0.023 rad; 1.5 nm: 0.166 A, +0.01 %, +0.009 rad (INTERFACE_OVERLAP_RULE, B41) | c3 output (SUMMARY) | OK. Labelled a 1-D laterally averaged model |
| 0.068 A, 0.1538 A, 0.769 %, 0.0169, +-0.325, +-0.148, 0.0036 layer (0.0049 A), 2.19877 (-0.056 %), 19.9888 (oxide.py comment, B41, docs/06) | x5_oxide_numbers output | OK (D7) |
| 11.85 A, 9.06 A (config comments) | x5_oxide_numbers output | OK (D7: 11.8487, 9.0563) |
| B43: 10.34 V (E9 line 166), 0.4024 V for 1705 A (line 20), 4.6997 V per g/cm^3 (line 170) | tools/review/e9_recompute_output.txt lines 166, 20, 170 | OK (read) |
| docs/06: "the simulation then runs both parities" | code | **overstated** (A10b-M1) |
| B7, B12: "needs/need both parities" | code | **overstated as a requirement the code does not enforce** (A10b-M1) |
| B7, B43, X5: measurement record "what was measured and how" / "placeholders refused" | code | the gate cannot verify (stated); "placeholders refused" is **overstated** (A10b-M2) |
| B12: "an atomistic multislice cell whose terraces carry different thicknesses is refused unless acknowledged" | code | literally correct; the one-thickness, two-count case passes (A10b-n1) |

The evidence labels (DERIVED_HERE from committed scripts; ESTIMATE / 1-D model; ASSUMPTION for
B43 with REPRODUCED/SECTION_READ sources) are appropriate.

## Question 6: scripts/hpc/alliance and the sizing numbers

* `git diff --stat 62ced11..00851da -- scripts/` is empty, and `git log 62ced11..00851da --
  scripts/hpc/alliance/` is empty. b4177ce touches only this report.
* The committed sizing output differs from 62ced11 only in:
  * the git and load line;
  * the load-dependent CPU observation (753 -> 531 s);
  * the relabelled oxide texts.
* 3.162, 7.731 and 7.438 GB appear in the same six lines before and after.
* Rerun at HEAD (D10, single-threaded, 24 s): "63/63 checks pass; runtime 23 s". It differs from
  the committed output only in the git and load line and the CPU observation (1103 s at load 4.9,
  a machine-load measurement). It contains all three numbers (6 lines).

## Test runs (repository, HEAD = 00851da code)

    D9  pytest (9 files: the three a9b files, the two a8 files, tests/io/test_io_config_stand_ins.py,
        test_oxide_structure.py, test_oxide_geometric.py, test_oxide_pipeline.py): 264 passed in 17.99s
        (the io test X5 reported failing on the missing B43 row now passes: the row exists)
    D8  tests/forward/test_oxide_multislice.py::test_graded_edge_of_0p5_A_suppresses_the_layer_reflection -s: 1 passed in 7.33s
    D5  mutation control (scratch copy, 5 files): 119 passed, 1 deselected in 1.60s

The full suite was NOT RUN by me. It was running concurrently (the orchestrator's run).

## Command log

PY = `OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python` from /home/user/Holography. Scripts and
outputs are in SP/a10b/.

| # | command | purpose | result |
|---|---|---|---|
| C0 | `git status`, `git log`, `git rev-parse HEAD`, `git diff --stat 62ced11..00851da`, `git diff 62ced11..00851da -- <oxide files, docs/06, model_assumptions, sizing>`, `git diff --stat 62ced11..00851da -- scripts/`, `git log 62ced11..00851da -- scripts/hpc/alliance/`, later `git show --stat HEAD`, `git diff --stat 00851da HEAD` | scope | code at 00851da; b4177ce = this report only |
| D1 | `PY SP/a10b/d1_probes.py > d1_probes.out` | q2 probes | first attempt FAILED (my script: duplicate keyword in `dict(MEAS, **B43, V_real=...)`); fixed and rerun, exit 0 |
| D2 | `PY SP/a10b/d2_parity.py > d2_parity.out` | q2 a-Si, q4 | exit 0 |
| D3 | `PY SP/a10b/d3_m1_edge.py > d3_m1_edge.out` | q3 guard edge | first run used the default thickness (my script); fixed to the tie thickness, exit 0 |
| D4 | `PY SP/a10b/d4_bitid.py oxide_2p0nm > d4_bitid.out` (outputs in SP/a10b/pipe) | q3 bit-identity | 26/26 identical vs A9b, X5, A8 |
| D5 | `venv/bin/python SP/a10b/d5_mutate.py A0_control`, then A1-A19 -> `d5_control.out`, `d5_mutations.out` | q1 | first control printed no summary (I had passed `-q` twice); corrected, 119 passed; all 19 mutations caught |
| D6 | `PY tools/review/x5/<script>.py > SP/a10b/d6_<script>.out`; `diff` against the committed outputs | q5 | first loop FAILED (no `/usr/bin/time` here: exit 127); rerun with shell timing: 4 of 4 identical |
| D7 | `venv/bin/python SP/a10b/d7_numbers.py > d7_numbers.out` (no package import) | q4, q5 | section above |
| D8 | `PY -m pytest -q -s -p no:cacheprovider tests/forward/test_oxide_multislice.py::test_graded_edge_of_0p5_A_suppresses_the_layer_reflection > d8_edge_print.out` | q5 | 1 passed in 7.33s |
| D9 | `PY -m pytest -q -p no:cacheprovider <9 files> > d9_tests.out` | regression | 264 passed in 17.99s |
| D10 | `OMP/OPENBLAS/MKL_NUM_THREADS=1 PYTHONPATH=. venv/bin/python tools/hpc/supercell_sizing.py > SP/a10b/d10_sizing.out`; `diff` against the committed output | q6 | 63/63; three numbers present |
| D11 | `PY SP/a10b/d11_record_b43.py > d11_record_b43.out` | q2 (B43 record level), n2 | first attempt did not catch io's ConfigError (my script); fixed, exit 0 |
| D12 | `PY SP/a10b/d4_bitid.py multislice_tiny_oxide_2p0nm > d12_ms_bitid.out` | q3 (guard in the pipeline, bit-identity) | 26/26 vs A9b; 18.9 s |
| D13 | `git status --short outputs/`; `find outputs -newer SP/a10b/d1_probes.py -type f` | nothing written | empty, empty |

Read-only commands, not listed one by one: `grep`, `sed -n`, `cat`, `ls`, `wc`, `du`,
`/proc/loadavg`, `ps`. I also read `SP/a9b/*`, `SP/x5/mutate.py`, `SP/x5/mutations_final.out`,
`SP/full_suite_x4t3.txt` (other agents' files, not my runs).

## NOT RUN

* The full test suite (it was running concurrently; not my run).
* A propagated two-terrace multislice of a non-conformal oxide. The size of the engine
  disagreement still rests on A9b's 1-D laterally averaged model, which X5 labels an estimate.
* Any run at the B43 bracket ends beyond in-memory loading.
* A comparison run with a real item-12 record (none exists). All comparison probes are in-memory
  with fabricated TEST supply records, and all are refused for the demo's other stand-ins.
* X5's text-only mutations (X3, X4, X21-X23, X25, X26), and the n2 and manifest mutations (X14,
  X24). I did not repeat them; X5's saved output shows each failing a test.
* cupy/GPU; the [110] multislice with the layer; the a-Si layer in propagation.

## Verdict

**The oxide work (E4, X4, X5) cannot yet be called final without qualification.**

Final for the B41 demo path:
* the X5 code changes are correct where they apply;
* every fix I reverted makes a test fail (19 mutations);
* the geometric and the conformal multislice demo arrays are bitwise unchanged;
* the review scripts reproduce their outputs;
* every quoted number is printed by a committed script and recomputes independently;
* scripts/hpc/alliance and the clean-surface GPU figures (3.162 / 7.731 / 7.438 GB) are unchanged.

Not final for comparison runs, which is where the item-12 label policy applies. Before the first
comparison run, or before docs/06 item 12 is relied on by Ali:

1. **A10b-M1:** either implement both-parity runs with an honest (DERIVED_HERE) label for the
   other count, refuse boundary-spanning comparison runs, or record the single parity run. In
   every case correct "the simulation then runs both parities" in docs/06 item 12, and "needs
   both parities" in B7, B12 and the `config.py` docstring.
2. **A10b-M2:** make the measurement record structured, and refuse punctuation placeholders and
   "not measured" statements; test them.
3. Minor: the a-Si potentials (m1), the uncertainty convention (m2) and the a-Si thickness
   uncertainty (m3). Notes n1-n6 when convenient.
4. Bookkeeping: X4's report is still DRAFT with four placeholders. Either annotate it with a
   pointer to X5 section 6, whose values I checked against A9b's saved outputs, or accept X5
   section 6 as its completion.

Items 1 and 2 are small code changes plus text. No change is needed for the demo path.
