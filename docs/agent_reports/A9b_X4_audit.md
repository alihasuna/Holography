# A9b - Audit of X4 (fixes of audit A8 on E4's continuum oxide overlayer)

Auditor: agent A9b, 2026-09-24. Status: FINAL (written incrementally).

Scope: `docs/agent_reports/X4_a8_fixes.md` (read in full), checked against
`docs/agent_reports/A8_e4_oxide_audit.md` (read in full). X4 had not finished its report: it is
still marked DRAFT and contains the placeholders `(FULL_SUITE_RESULT)`, `(M1_PRINT)`,
`(MULTISLICE_RUN)` and `(C_PRINT)`. X4's code is in snapshot 4c4a78b (b96bc6e changed only X3's
report). During this audit the orchestrator committed ebb9ec7, which holds T3's B42 gate and the
amended rows B7, B12 and B41. I checked that these rows are byte-identical to the working-tree
text I audited.

Code read in full: `structure/oxide.py` (544 lines) and `forward/multislice/overlayer.py`. I read
X4's diffs, with their surrounding code, in `forward/cell.py`, `forward/multislice/engine.py`
(`memory_model`, `overlayer_memory_arguments`, `estimate_resources`), `forward/geometric/model.py`
(module docstring, `_require_b4_scope_oxide`, `oxide_phase_rates`, `_oxide_terms`),
`structure/si001.py` (`_apply_oxide`), `pipeline/config.py`, `pipeline/engines.py`
(`build_structure`), `io/assumption_registry.yaml`, `configs/demo_smoke_si001.yaml` (the five B41
variants), `tools/hpc/supercell_sizing.py` and its output. I also read every test X4 added or
changed (section 9) and the scratch directories `SP/x4/` and `SP/a8/`.

Rules kept:
* This report is the only repository file written. The code under audit was never modified;
  mutations were made in scratch copies only.
* Nothing was committed or pushed.
* Nothing was written under outputs/. After the last run, `git status --short outputs/` and a
  `find outputs -newer` both returned nothing.
* Scratch files are in `SP/a9b/`, where SP =
  `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`.
* All runs used at most 2 threads (the full suite was running concurrently).

Grades: MAJOR (must be resolved before the affected item is adopted; a reproduction is given),
minor, note.

## Verdict table

| A8 finding | X4 status | A9b verdict | reverting the fix makes a test fail? |
|---|---|---|---|
| M1 a-Si = 0 cannot be a PROJECT_INPUT | FIXED (per-parameter labels) | FIXED for a-Si = 0. V'_ox = 0 and V'_a = 0 are never accepted as measurements. Comparison runs refuse every per-parameter ASSUMPTION and demo stand-in. No silent default. But see **A9b-M2** (model and derived parameters can only be labelled PROJECT_INPUT) and A9b-m1 (a B26 per-parameter label is accepted) | yes: A3 4, A4 3, A5 1, A6 1 failures (C6) |
| M2 the continuum layer overlaps the atomistic crystal | FIXED | PARTLY FIXED. Placement, recorded overlap/gap, bound and measurement are correct (0.674 / 0.166 A reproduced). The second half of M2 (the two engines describe different interfaces for a non-conformal layer) is not fixed and not stated: **A9b-M1**. The gap is a potential dip that no document mentions (A9b-m4) | yes: A1 14, A2 8 (C6) |
| m1 Born figure quoted for the 0.5 A edge | FIXED | FIXED. 1.95e-9, 1.8345e-9, 8.5e-4 and 57x reproduced by an independent ODE solution. The engine gives 1.8350e-9. Several of these numbers are printed by no committed script (A9b-m3) | yes: A16 2, A17 1 (C6) |
| m2 B41 vouches for values its row does not state | FIXED | FIXED on the variant path and the base path (B41 with "none", t 50 A / N 16, other values, material). The per-parameter analogue with B26 remains (A9b-m1) | yes: A7 1, A8 1 (C6) |
| m3 memory model omits the layer | FIXED | FIXED: tracemalloc agrees within 0.13 %. The clean-surface sizes and GPU figures given to Ali are unchanged. For the oxide-covered production surface they are lower bounds (A9b-m6) | yes: A15 2 (C6) |
| m4 2.0 nm sits on the rounding boundary | FIXED (0.05-layer gate plus an acknowledgement flag) | FIXED as specified: 6.5036 layers, 0.0036 layer, 2.19877 g/cm^3 reproduced. The gate is enforced on every path, overrides included. Its rationale is unsupported and much tighter than any realistic item-12 uncertainty (A9b-m2) | yes: A9 4, A10 19 (C6) |
| m5 interface grading not enforced | FIXED | FIXED | yes: A11 5 (C6) |
| m6 build-up assertion untested | FIXED (test) | FIXED | yes: A14 1 (C6) |
| m7 reading of the (c) series | RECORDED (comment) | RECORDED as stated. E4's report itself is unchanged (docs are the orchestrator's) | n/a |
| n1 numbers as strings | FIXED | FIXED | yes: A12 7 (C6) |
| n2 B4 text next to the overlayer statement | FIXED (note) | FIXED | not mutated (C6) |
| n3 item-12 value without overlayer/termination | FIXED | FIXED at load | yes: A13 2 (C6) |

Overall: X4's code changes are correct and every fix has a test that fails when the fix is
reverted. The conformal B41 demo is unaffected: the geometric `oxide_2p0nm` arrays are bitwise
identical to A8's run of the pre-fix code, and `multislice_tiny_oxide_2p0nm` runs end to end.

There are two MAJOR findings. Both are adoption problems, not bugs in the demo path:
* A9b-M1: for a non-conformal oxide the two engines give phase rates that differ by a factor of
  about 5, and nothing says so.
* A9b-M2: in a comparison run the per-parameter label scheme leaves model and derived oxide
  parameters no correct label.

There are also six minor findings and six notes. See the final verdict at the end.

## Findings

### MAJOR

**A9b-M1. A8-M2 is only partly fixed. For a non-conformal (grown) oxide the atomistic multislice
and the geometric engine describe different interfaces. The geometric engine applies E9's
continuum grown-oxide rate of 4.45 rad/A to any thickness difference. The multislice keeps the
crystal fixed while the thickness changes by less than one consumed layer and gives about
0.86 rad/A. Nothing in the code, the records or rows B12/B41 states this.**

Where it happens:
* `structure/oxide.py:420-438` places the continuum stack continuously
  (x_i = H + a/8 - f t, x_t = H + a/8 + (1 - f) t).
* The atomistic crystal loses whole layers only (`si001.py:840-859`).
* The geometric engine adds T_k + I_k = [2 k'_ox - 2 k (1 - f)] t_k per terrace
  (`forward/geometric/model.py:312-341`; `oxide_phase_rates`).

So when two terraces differ in thickness but keep the same consumed-layer count, the multislice
crystal does not move. Only the layer top and the layer/crystal gap move.

X4 section 2 (line 71) says the chosen placement "keeps one continuum geometry for both engines
and states the atomistic crystal's unavoidable partial-layer error explicitly". What is stated is
only the geometric bound "<= a/8": `NOT_REPRESENTED`, oxide.py:121-125, and `INTERFACE_OVERLAP_RULE`.
The phase consequence is not stated anywhere. `B4_OXIDE_GROWN` (`si001.py:821-823`) records for
every non-conformal step that "the step phase carries the grown-oxide and top-surface terms of the
continuum layer ..., added by the geometric engine". A multislice run of the same structure does
not carry them. The engines accept per-terrace overrides (only the pipeline refuses them). The
grown-oxide sensitivity is the physics of E9 M2 that B7 quotes ("0.18 A of oxide difference gives
a 0.1 A height error").

Reproduction (C4, `SP/a9b/c4_nonconformal.py`). This is a 1-D laterally averaged model (my own
derivation, not an engine output; it drops the lateral Fourier components). It uses the engine's
own laterally averaged static Kirkland crystal (X4's helper `_flat_terrace_profiles`), the top N
layers removed below a fixed pre-oxidation plane, X4's placement of the layer (erf 0.5 A,
V' = 0), crystal absorption ratio 0.1, and a transfer matrix at 16.1347 mrad referenced to a fixed
plane:

    geometric grown-oxide rate 4.4549 rad/A; one consumed layer 13.6998 rad = 3.0752 A of oxide
    slope at t 19.0 A (N 6 fixed): X4 placement 0.8455 rad/A; x_c pinned to the kept crystal 0.8852 rad/A; geometric 4.4549 rad/A
    slope at t 20.5 A (N 7 fixed): X4 placement 0.8729 rad/A; x_c pinned to the kept crystal 0.8863 rad/A; geometric 4.4549 rad/A
    slope at t 21.5 A (N 7 fixed): X4 placement 0.8599 rad/A; x_c pinned to the kept crystal 0.8856 rad/A; geometric 4.4549 rad/A

The phase advances about 2.6 rad over one consumed-layer period (3.075 A of oxide) and then
jumps when the count changes. The geometric engine advances 13.70 rad linearly over the same
period. For two terraces with the same count and a thickness difference Dt, the engines therefore
differ by about 3.6 Dt rad (mod 2 pi). For example, Dt = 0.5 A gives 2.23 rad in the geometric
engine and about 0.43 rad in this model. The slope at fixed count is close to the top-surface rate
2 (k'_ox - k) = 0.886 rad/A, because moving x_c only replaces the gap potential with oxide
potential.

Neither placement option (X4's, or x_c pinned to the crystal) removes the disagreement. It is
inherent to whole-layer consumption. A propagated two-terrace multislice run was NOT RUN (A8 and
E4 did not run non-conformal cells either).

Fix needed:
* State the disagreement with its size in `NOT_REPRESENTED`, `B4_OXIDE_GROWN` and rows B12 and
  B41.
* Record, per non-conformal step of an atomistic cell, that the grown-oxide term of a sub-layer
  thickness difference is not represented by the multislice (the crystal does not move). Either
  refuse such cells for engine comparisons, or add an explicit TEST_ONLY/acknowledgement path.
* Correct X4 section 2.

**A9b-M2. A comparison run can only be made by labelling model and derived oxide parameters
PROJECT_INPUT.** `pipeline/config.py:1012-1062` accepts three per-parameter labels: PROJECT_INPUT,
"ASSUMPTION <id>" and TEST_ONLY. Item 12 is blocking, so the comparison gate (`config.py:1265-1268`)
refuses every per-parameter ASSUMPTION, and a comparison run needs all eight parameters labelled
PROJECT_INPUT.

docs/06 item 12 (line 29) asks Ali for the oxide thickness with its convention, any a-Si,
interface roughness and carbon. It does not ask for:
* V_ox (E9: an independent-atom value, 10.34 V);
* V'_ox (a model value from an inelastic mean free path, E9 M1);
* the two edge widths (E9 M4: a numerical requirement of at least 0.5 A, not a measured roughness);
* consumed_layers (derived by the code's own rule from t, rho and a, and asserted to be the nearest
  count).

The gate accepts all of these as PROJECT_INPUT and cannot tell a measurement from a model value
typed in as one. The code offers no correct label for them in a comparison run. X4 section 2 and
the amended B7 name only V_ox and V'_ox ("need a policy decision"). They omit consumed_layers (a
derived quantity: labelling it PROJECT_INPUT is a mislabel whatever the policy) and the two widths.

Reproduction (C5, `SP/a9b/c5_gate.py`; in-memory fabricated TEST supply record):

    [REFUSED ] comparison, every oxide parameter PROJECT_INPUT (PipelineConfigError); oxide entries in the refusal: NONE
       spec labels (all PROJECT_INPUT): {'V_imag': 'PROJECT_INPUT item 12 (TEST: fabricated ', ... 'consumed_layers': 'PROJECT_INPUT item 12 (TEST: fabricated ', ... 'interface': ..., 'vacuum_edge': ...}

The run is refused only for other blocking items. The oxide entries all pass, and the spec
carries "PROJECT_INPUT item 12" on V'_ox, the widths and the derived count.

Fix needed, before any comparison run:
* a label class for model and derived item-12 parameters, for example:
  * consumed_layers computed by the code and labelled DERIVED_HERE from the thickness and density
    labels;
  * V_ox, V'_ox, w_v and w_i admitted in a comparison run only under a registered non-demo model
    row;
* or, at minimum, B7 names all five parameters and the orchestrator records the policy decision.

### minor

**A9b-m1. The clean-surface stand-in B26 is accepted as a per-parameter label for oxide values.**
`config.py:1137` skips value checks for ids outside `OXIDE_STAND_IN_ROWS`. The record-level refusal
of B26 with an oxide (`config.py:1171`, `OXIDE_STAND_INS_CLEAN`) is not applied per parameter.

Result (C5):
* `[ACCEPTED] PROJECT_INPUT record, V_imag labelled ASSUMPTION B26 (clean-surface row)`, with the
  spec label "ASSUMPTION B26 (stands in for PROJECT_INPUT item 12)";
* `[ACCEPTED] PROJECT_INPUT record, every parameter ASSUMPTION B26, thickness 30 A, N 10`;
* `[ACCEPTED] TEST_ONLY record, V_imag labelled ASSUMPTION B26`.

This is the per-parameter form of A8-m2. A row that states "no oxide" vouches for oxide values in
demo runs. Comparison runs refuse it (B26 is demo-only and blocking).

Fix needed: refuse per-parameter ids listed in `OXIDE_STAND_INS_CLEAN`, or require every
per-parameter id to be a key of `OXIDE_STAND_IN_ROWS`.

**A9b-m2. The m4 threshold and its rationale.** `oxide.py:87-93` justifies
MIN_ROUNDING_MARGIN_LAYERS = 0.05 as "the precision to which item-12 values are stated". No item-12
value, and no precision for one, exists yet: docs/06 item 12 says "still to be supplied". The
supporting numbers "0.15 A", "0.8 %" and "0.017 g/cm^3" (reproduced in C1: 0.1538 A, 0.769 %,
0.0169 g/cm^3) are printed by no committed script.

C1 shows how tight the threshold is:

    thickness +-1.0 A -> consumed depth +-0.442 A = +-0.325 layer
    density +-0.05 g/cm^3 at 2 nm -> +-0.148 layer

So the gate refuses only counts closer than 0.15 A of thickness to a boundary. Any realistic
uncertainty of a witness measurement spans a count change far more often, and at <110> the parity
(the terrace type at a buried a/4 step) is then decided by the nominal value without comment. The
gate itself works on every path (question 5).

Fix needed: tie the margin to a stated uncertainty of the item-12 thickness and density (a docs/06
field). Either refuse when the uncertainty interval crosses a boundary or require both-parity
runs. Otherwise, state 0.05 as an arbitrary numerical guard and say in B41/B12 that it does not
make the parity robust.

**A9b-m3. Numbers in row B41 and in code strings that no committed script prints.**
* "1.95e-9 at 16.1347 mrad", "|r| x 8.5e-4" and "57 times lower" (B41; `oxide.py:47-51, 94-99,
  257`; `geometric/model.py:50-52`) exist only in A8's scratch (`SP/a8/a8_exact1d.py`). The
  values are right (C2).
* The committed test prints the central-bin values: "EXACT 1-D ... 1.8346e-09", "58-fold"
  (C9).
* B41 quotes "1.8345e-9" (A8's converged value), which differs from the committed print in the
  last digit.
* "-0.056 %" (B41) is printed nowhere.

Fix needed: let `test_graded_edge_of_0p5_A_suppresses_the_layer_reflection` (or a
`tools/review` script) also print `exact_graded_edge_r` at 16.1347 mrad and the ratio to the Born
factor there, and quote the printed digits.

**A9b-m4. The 2.0 nm "gap" is a real dip in the potential inside the stack, and this is not
stated.** On the engine's own laterally averaged potential (C3), the 0.674 A gap lowers the
potential to 4.85 V about 0.94 A above the kept top atomic plane. The same stack joined to the
equivalent boundary (x_c = x_eq) gives 9.9-10.6 V there, and the crystal's own minimum between
planes is 9.8 V. Relative to the joined stack the deficit has a minimum of -5.17 V and an integral
of -6.98 V A. It is a partial vacuum sliver inside the stack.

Its own reflection is negligible:
* Born reflectivity at q = 2 k'_ox: |r|^2 = 1.7e-12, below the 1.95e-9 of the graded edge,
  because the dip is smooth on the scale 1/q.
* In the 1-D dynamical (0,0,8) reflection it changes |r| by -0.05 % and the phase by +0.023 rad
  (common to every terrace of a conformal layer). At 1.5 nm (gap 0.166 A) the changes are
  +0.01 % and +0.009 rad.

For non-conformal layers the gap differs per terrace (A9b-M1). B41 calls it "a gap" without
saying what the potential does there.

Fix needed: one sentence in `INTERFACE_OVERLAP_RULE`/B41 with these numbers, printed by a
committed script.

**A9b-m5. X4's report is not final and some of its evidence is not saved.**
* The four placeholders are listed above.
* The mutation counts for X0, X2, X4 and X5 (69 passed; 7, 4 and 5 failed) are not in
  `SP/x4/mutations.out`, which holds only the collection errors of the first batch.
* X4's own full-suite log `SP/x4/pytest_full.txt` stops at 46 % after one F.

The orchestrator's full suite at 4c4a78b plus the B42 fix (`SP/full_suite_x4t3.txt`, not my run)
ended "1399 passed, 8 skipped". My targeted runs all pass (section 10). The values X4 left open
are printed in C9, C10, C12 and C14 below.

**A9b-m6. The GPU figures quoted to Ali hold for a clean surface only. The sizing tool's "with
oxide" column is a same-grid lower bound.** Question 7 in full is in section 7.

### note

* **A9b-n1.** The oxide record's headline `label` is the thickness label only
  (`oxide.py:478`). With mixed per-parameter labels it can read PROJECT_INPUT while V_ox is an
  ASSUMPTION (C5: "record headline label: PROJECT_INPUT item 12 ...").
* **A9b-n2.** `OXIDE_STAND_IN_ROWS` does not tie a thickness to a variant. B41 with 15 A / N 5
  is accepted in `multislice_tiny_oxide_2p0nm` (C5), while the row assigns 2.0 nm to that variant.
* **A9b-n3.** `configs/demo_smoke_si001.yaml:625, 666`: the comment "11.85 A above the top
  atomic planes" is copied into the two 1.5 nm variants. There the layer top lies
  (1 - f) 15 + a/8 = 9.06 A above the planes (C1 constants).
* **A9b-n4.** For a continuum crystal with the layer, `memory_model` overestimates the measured
  peak by 16.6-17.2 % (C13; the model is written for AtomicPotential). This is conservative.
* **A9b-n5.** `list-inputs` shows B41 with `overlayer: none` without comment. It is a view: load
  refuses it (C5).
* **A9b-n6.** B12 says "whole-layer overlap or gap". It is the partial-layer mismatch
  f t + t_a - N a/4.

## 0. Command log

PY = `PYTHONPATH=. venv/bin/python` from `/home/user/Holography`. Scripts and outputs are in
`SP/a9b/`.

| # | command | purpose | result |
|---|---|---|---|
| C0 | `git status`, `git log`, `git diff 36d2250 4c4a78b -- <files>`, `git diff HEAD`, `git show --stat b96bc6e ebb9ec7 db376ce` | scope | X4 = 4c4a78b; b96bc6e = X3 report only; rows committed in ebb9ec7, identical to the text I audited |
| C1 | `PY SP/a9b/c1_analytic.py` -> `c1_analytic.out` | q3, q5 numbers | section 3 |
| C2 | `venv/bin/python SP/a9b/c2_edge.py` -> `c2_edge.out` (no package import: DOP853 ODE plus my own transfer matrix) | q4 | section 4 |
| C3 | `OMP_NUM_THREADS=1 PY SP/a9b/c3_gap.py` -> `c3_gap.out` | q3: gap potential and 1-D reflection | section 3 |
| C4 | `OMP_NUM_THREADS=1 PY SP/a9b/c4_nonconformal.py` -> `c4_nonconformal.out` | A9b-M1 | above |
| C5 | `PY SP/a9b/c5_gate.py` -> `c5_gate.out` (in-memory probes) | q2, q6 | section 2 |
| C6 | `venv/bin/python SP/a9b/c6_mutate.py A0_control`, then 13 mutations, then A14-A17 -> `c6_control.out`, `c6_mutations.out`, `c6_mutations2.out` | q1 | section 1. The first control attempt passed `-q` twice and printed no summary (my script); corrected and rerun |
| C7 | `OMP_NUM_THREADS=2 ... PY tools/hpc/supercell_sizing.py > SP/a9b/c7_sizing.out`; `diff tools/hpc/supercell_sizing_output.txt SP/a9b/c7_sizing.out` | q7 | section 7 |
| C8 | `PY SP/a9b/c8_oxide_cell.py` -> `c8_oxide_cell.out` (scaling estimate) | q7 | section 7 |
| C9 | `OMP_NUM_THREADS=2 PY -m pytest -q -s -p no:cacheprovider tests/forward/test_oxide_multislice.py::test_graded_edge_of_0p5_A_suppresses_the_layer_reflection ...::test_graded_edge_of_0p1_A_follows_the_roughness_factor tests/forward/test_oxide_multislice_a8_fixes.py` -> `c9_forward_prints.out` | q3, q4, X4's (M1_PRINT) | 6 passed in 13.73s |
| C10 | `OMP_NUM_THREADS=2 PY -m pytest -q -s -p no:cacheprovider tests/forward/test_memory_model.py::test_oxide_layer_arrays_in_the_memory_model ...::test_memory_model_contract` -> `c10_memory.out` | q7 | 4 passed in 9.13s |
| C11 | `PY SP/a9b/c11_pipe.py oxide_2p0nm` (outputs `SP/a9b/pipe/`) -> `c11_pipe.out` | bit-identity of the geometric engine | 26 of 26 arrays bitwise identical to A8's pre-fix run |
| C12 | `PY SP/a9b/c12_dry.py` -> `c12_dry.out` | dry run with the layer | section 7 |
| C13 | `OMP_NUM_THREADS=1 PY SP/a9b/c13_mem_continuum.py` -> `c13_mem_continuum.out`. The first attempt FAILED because my script gave working reflections to a continuum cell; fixed | A9b-n4 | -16.6 % to -17.2 % |
| C14 | `PY SP/a9b/c11_pipe.py multislice_tiny_oxide_2p0nm` -> `c14_pipe_ms.out` | X4's (MULTISLICE_RUN) | runs end to end in 18 s; heights withheld ("a terrace region is empty or below the minimum size after the margin") as in A8 |
| C15 | `OMP_NUM_THREADS=2 PY -m pytest -q -p no:cacheprovider tests/io tests/pipeline/test_oxide_pipeline.py` | regression | 165 passed in 10.83s |
| C16 | `git status --short outputs/`; `find outputs -newer SP/a9b/c1_analytic.py -type f` | nothing written | empty, empty |

Read-only commands, not listed one by one: `grep`, `sed -n`, `cat`, `ls`, `awk`, `wc`,
`/proc/loadavg`, `ps`, `pgrep`, `md5sum` of the three rows, and reading
`SP/full_suite_x4t3.txt` (the orchestrator's run, not mine).

## 1. Each A8 finding, with reversion tests (question 1; C6)

Each fix was reverted in a scratch copy of `reflection_holo/`, `tests/` and `configs/` (without
git), and the relevant X4 and E4 oxide test files were run. Control run: 146 passed in 7.71s.

| mutation (reverts) | result | caught by |
|---|---|---|
| A1 E4's placement, `shift = 0.0` (M2) | 14 failed, 101 passed | X4 structure tests; `test_two_nm_stack_equals_e9`; six geometric oxide tests (the reference-plane check); the overlap test |
| A2 recorded overlap biased by +a/8 (M2) | 8 failed | structure a8 tests; all three overlap cases |
| A3 E4's refusal of a PROJECT_INPUT a-Si zero (M1) | 4 failed | structure and pipeline a8 tests, `test_zero_absorption_or_a_si...` |
| A4 V'_ox = 0 accepted as a measurement (M1) | 3 failed | three tests |
| A5 per-parameter PROJECT_INPUT outside a PROJECT_INPUT record (M1) | 1 failed | `test_invalid_per_parameter_labels_are_refused` |
| A6 comparison gate blind to per-parameter labels (M1) | 1 failed | `test_comparison_refuses_per_parameter_stand_ins` |
| A7 B41 with `none` accepted (m2) | 1 failed | `test_b41_with_no_overlayer_is_refused` |
| A8 material of a B41 record not checked (m2) | 1 failed | `...values_outside_its_row...[material]` |
| A9 no margin gate (m4) | 4 failed | near-boundary tests, overrides, variants |
| A10 threshold 0.003 instead of 0.05 (m4) | 19 failed | many (the acknowledgement becomes "not needed") |
| A11 no interface minimum (m5) | 5 failed | structure and pipeline |
| A12 strings accepted (n1) | 7 failed | structure and pipeline |
| A13 termination/overlayer default restored at load (n3) | 2 failed | `test_item12_value_needs_both_keys_at_load` |
| A14 build-up assertion ignores the stack (m6) | 1 failed | the m6 test |
| A15 layer dropped from `memory_model` (m3) | 2 failed | both terraces-along-y cases (along z is untouched, as X4 says) |
| A16 erfc(x/w) width convention (m1) | 2 failed | the 0.5 A exact-value assertion and the 0.1 A test |
| A17 Born figure restored in the recorded text (m1) | 1 failed | `test_edge_reflectivity_text_is_the_exact_value` |

No existing assertion or tolerance was weakened. The changed expectations are the two a-Si = 0
cases (inverted on purpose by A8-M1) and the fixtures stating the new required fields. The
fixtures compute the acknowledgement exactly when it is needed (`_near_rounding_boundary`), which
is acceptable in tests.

## 2. Per-parameter labels and the item-12 gate (questions 2 and 6; C5)

    [REFUSED ] PROJECT_INPUT record, V_imag 0 labelled PROJECT_INPUT: ... must carry the label ASSUMPTION (or TEST_ONLY in tests)
    [REFUSED ] PROJECT_INPUT record, a-Si 5 A with V'_a 0 labelled PROJECT_INPUT: amorphous_si_V_imag_V = 0 must carry the label ASSUMPTION ...
    [REFUSED ] comparison, every oxide parameter PROJECT_INPUT (PipelineConfigError); oxide entries in the refusal: NONE      (A9b-M2)
    [REFUSED ] comparison, V_imag ASSUMPTION B41: refused (demo stand-in and blocking item)
    [ACCEPTED] PROJECT_INPUT record, V_imag labelled ASSUMPTION B26 (clean-surface row)                                      (A9b-m1)
    [ACCEPTED] PROJECT_INPUT record, every parameter ASSUMPTION B26, thickness 30 A, N 10                                     (A9b-m1)
    [ACCEPTED] TEST_ONLY record, V_imag labelled ASSUMPTION B26                                                               (A9b-m1)
    [REFUSED ] variant: B41 with overlayer none: ... under stand-in B41: its model_assumptions row states a continuum oxide ...
    [REFUSED ] base: B41 with overlayer none: (same)
    [list-inputs] base with B41 + none: 2 item-12 rows (view only)                                                            (A9b-n5)
    [REFUSED ] base: B41 with t 50 A / N 16: stand-in B41 ... states consumed_layers in [7, 5], got 16
    [ACCEPTED] multislice variant: B41 t 15 A N 5                                                                             (A9b-n2)
    [REFUSED ] variant without overlayer.rounding_boundary_acknowledged / without labels / without termination (no default)
    [REFUSED ] ack given as the string 'true'
    [REFUSED ] PROJECT_INPUT record, consumed_layers 6 at 2.0 nm (not nearest)
    [ACCEPTED] PROJECT_INPUT record, thickness 20.3 A PROJECT_INPUT, consumed_layers 7 B41

Answers:
* V'_ox = 0 (and V'_a = 0) is never accepted as a measurement.
* A comparison run refuses every per-parameter ASSUMPTION and demo stand-in (A6 mutation, C5).
* No default fills a missing item-12 field. `rounding_boundary_acknowledged`, `labels`,
  `termination` and `overlayer` are all required at load. The pipeline's fixed choices (no
  overrides, both TEST_ONLY sharp flags False) are stated policy, not filled-in inputs
  (`config.py` module docstring).
* Unmeasured parameters can reach a comparison run labelled PROJECT_INPUT, and they must, because
  no other label passes: A9b-M2.
* B41 with `none` or with values outside its row is refused on the variant path and the base path.
  The engines never see B41, since labels exist only in the pipeline.

## 3. A8-M2: placement, overlap and the gap (question 3; C1, C3, C9)

Recomputed from the code's constants (C1; the code's `rounding_margin` agrees to every digit):

    rho_Si = 2.329195 g/cm^3, a/4 = 1.357725 A, a/8 = 0.678863 A
    t 20.0 A N 7 rho 2.2: f 0.441507 f t 8.83015 A = 6.50364 layers; margin 0.00364 layer (0.00494 A); X4 overlap -0.67393 A; E4-placement overlap +0.00494 A; count -> 6 at rho 2.198770 g/cm^3 or t 19.98882 A
    t 15.0 A N 5 rho 2.2: ... X4 overlap -0.16601 A; E4-placement overlap +0.51285 A
    t 20.0 A N 6 rho 2.198: ... X4 overlap +0.67577 A; E4-placement overlap +1.35463 A

On the engine's potential (C9, X4's test, printed):

    t 20.0 A, N 7: overlap measured -0.6749 A, recorded -0.6739 A
    t 15.0 A, N 5: overlap measured -0.1660 A, recorded -0.1660 A
    t 20.0 A, N 6, 2.198: overlap measured +0.6756 A, recorded +0.6758 A

Confirmed:
* The stack starts at the Si equivalent boundary (top plane + a/8; `oxide.py:420, 434-438`).
* The recorded overlap equals f t + t_a - N a/4 and is bounded by a/8 (`oxide.py:445-447`).
* It matches the engine's potential to 0.001 A.
* The continuum crystal (bitwise unchanged) has zero overlap.
* The geometric engine's output is bitwise unchanged (C11).

Is the gap a reflecting vacuum sliver? Laterally averaged potential near the interface
(C3, V; x measured from the kept top plane):

    x - top (A):            0.04  0.24  0.44  0.64  0.84  0.94  1.04  1.24  1.44  1.64  2.04
    X4 (gap 0.674 A):      21.48 12.56  8.44  6.11  5.00  4.85  4.92  5.61  6.74  7.94  9.66
    joined (x_c = x_eq):   22.48 14.41 11.38 10.18  9.91  9.97 10.09 10.35 10.53 10.58 10.50
    crystal alone:         21.43 12.43  8.09  5.31  3.42  2.73  2.16  1.35  0.84  0.52  0.19
    crystal, 5 deep layers: mean 13.921 V, minimum between planes 9.795 V

So yes, it is a partial vacuum sliver: about 5 V deep and 0.7 A wide inside the stack. Its
reflection, however, is negligible:
* Born |r|^2 = 1.7e-12 at q = 2 k'_ox, 6.7e-13 at g_008. Both are below the 1.95e-9 edge.
* In the 1-D dynamical (0,0,8) reflection:

      |r_X4/r_joined| 0.9995, arg +0.0234 rad (2.0 nm);  1.0001, +0.0087 rad (1.5 nm)

This is not stated anywhere: A9b-m4. The part that matters, per-terrace differences of the gap
for non-conformal layers, is A9b-M1.

## 4. C6: the 0.5 A graded edge (question 4; C2, C9)

Independent solution: the ODE psi'' + K(x)^2 psi = 0 integrated with scipy DOP853
(rtol 1e-12), cross-checked by my own piecewise-constant transfer matrix. No package import;
exact relativistic dK^2.

    theta 16.1347 mrad: sharp Fresnel |r|^2 2.697179e-03
      w 0.5: ODE |r|^2 1.95454e-09 (span 12: 1.95454e-09); TM step 0.004/0.002/0.001: 1.95444e-09/1.95451e-09/1.95453e-09; |r|/|r_sharp| 8.5127e-04; Born 3.4396e-11; exact/Born 56.82
      w 0.1: ODE 1.30644e-03; Born 1.3036e-03
    theta 16.1751 mrad (the engine's central bin): w 0.5: ODE 1.83454e-09; exact/Born 58.43
    engine (C9, committed test print): w = 0.5 A: |r|^2 = 1.8350e-09 ...; EXACT 1-D ... 1.8346e-09 at the central bin 16.1751 mrad (... underestimates it 58-fold)

Confirmed:
* 1.95e-9 (1.9545e-9) at 16.1347 mrad; |r| x 8.5e-4; the Born factor is 57 times lower
  (56.8x at 16.1347 mrad, 58.4x at the bin).
* The engine's 1.8350e-9 equals the exact 1.8345e-9 to 0.03 % in |r|^2. The new test asserts
  this to 1 % in |r|, and the A16 mutation breaks it (15.9 in |r|, X4).

Only 1.8346e-9 and 58 are printed by committed code (A9b-m3).

## 5. m4 rounding boundary (question 5; C1, C5, C6)

Confirmed: 6.50364 layers at 2.0 nm, 0.00364 layer (0.0049 A) from the boundary; the count
becomes 6 below 2.198770 g/cm^3, which is -0.0559 % (C1).

The 0.05-layer refusal is in `terrace_stacks` (`oxide.py:455-474`), evaluated per terrace from
the per-terrace thickness and count (`oxide.py:432-433`). Every construction path calls it:
* the atomistic builder (`si001.py:840`), for the geometric and atomistic multislice engines;
* `build_continuum_oxide_cell` (`cell.py:297`), for the continuum multislice;
* the pipeline gate (`config.py:1187`, and again through the builder).

The multislice potential re-validates the spec and its hash. The geometric engine reads the
builder's stack and checks its reference.

Overrides: `test_overrides_acknowledge_per_terrace` passes, and the A9 mutation (no gate) makes it
fail. The rationale for 0.05 is A9b-m2.

## 6. m2: B41 with none or other values (question 6)

Refused on the variant path and the base path (section 2). List-inputs shows the declaration
without refusal (A9b-n5). The per-parameter B26 route stays open for demo runs (A9b-m1).

## 7. Memory model, sizes and the figures given to Ali (question 7; C7, C8, C10, C12)

X4 made the `overlayer` argument of `engine.memory_model` required (`engine.py:524-563`). With
`overlayer=None` every term is unchanged (layer terms 0, no extra phase). `estimate_resources`
passes `overlayer_memory_arguments(cell)` (`engine.py:678-681`), so the kit's GPU figure, which is
the dry run's `device_peak_cupy` (`kit.py:434`), includes the layer automatically. C12 confirms
this: the `multislice_tiny_oxide_2p0nm` dry run shows device 4,937,738 B with overlayer
resident_B 27,648 B, and the overlayer build-up check passes with available 2722.8 A against
required 2405.9 A at stack 21.353 A, which is X4's claim.

The tracemalloc check (C10) agrees with the model within 0.13 % in all three cases (8.00 / 16.00 /
0.05 B/px).

`tools/hpc/supercell_sizing.py` rerun (C7): "63/63 checks pass". It differs from the committed
output only in the git line, the load and the timing-dependent CPU observation (533 s against
753 s; a machine-load measurement, not a model number). The three rows quoted to Ali are
reproduced exactly and are unchanged by X4:

| row | atoms | grid | clean device peak | same grid with layer arrays (tool) | + stack in extent_x (C8 estimate) |
|---|---|---|---|---|---|
| 2a_a4_miscut0.1_r0.10 (a/4 step) | 36,681,120 | 2250x12096 | 3.162 GB | 3.380 GB | 3.591 GB (+13.6 %) |
| 2a_a2_miscut0.1_r0.10 (a/2 step) | 73,803,772 | 2250x24000 | 7.731 GB | 8.163 GB | 8.582 GB (+11.0 %) |
| 3_torus_R1000_r20_r0.10 | 105,260,269 | 3500x17150 | 7.438 GB | 7.918 GB | 8.215 GB (+10.4 %) |

So for a clean surface, 36.7 M atoms at 3.2 GB, 73.8 M at 7.7 GB and 105 M at 7.4 GB still hold.
The samples are oxide-covered (PROJECT_INPUT), and for that case these figures are lower bounds.

The tool's own column (layer arrays on the same grid) is printed and labelled "the cell's
geometry change ... not included". Two effects are missing from it. Both are my scaling estimate
(C8; not a layout run):
* **x extent.** The vacuum is measured above the layer top and the depth below the kept crystal,
  so the box grows by the 21.353 A stack (nx 2250 -> 2430 in the a/4 and a/2 rows; 3500 -> 3675
  for the torus). This gives the last column.
* **z length.** The beam crosses the stack over 1193 A (the oxide internal angle; 1323 A with the
  external-angle bound of `cell.py`) before reaching the crystal. If the run-in is counted in the
  crystal, the atoms grow x1.18 (43.3 M, 87.1 M) and x1.11 for the torus (117.3 M).

The same trend is visible in the demo: the oxide multislice variant is 2953 A long against 1487 A
for the clean one (C12). All device peaks stay below 10 GB. This is A9b-m6. Fix needed: lay out
at least one oxide cell in the tool, or print the two geometry terms, and quote oxide figures to
Ali.

## 8. Rows B7, B12, B41 against script outputs (question 8)

| statement (row) | printed by | verdict |
|---|---|---|
| B41 "1.95e-9 at 16.1347 mrad", "|r| x 8.5e-4", "57 times lower" | no committed script (A8 scratch; C2 confirms) | numbers right, not scripted (A9b-m3) |
| B41 "1.835e-9 against 1.8345e-9" | committed test: 1.8350e-09 and 1.8346e-09 | last digit of the exact value differs (A9b-m3) |
| B41 "0.0036 layer (0.005 A)", "2.19877 g/cm^3" | pipeline summary.json (C11: `rounding_margin_layers` 0.0036354, note "2.19877 g/cm^3"); tests assert them | OK |
| B41 "-0.056 %" | nowhere | not scripted (A9b-m3); value right (-0.0559 %, C1) |
| B41 "0.674 A ... (a gap; 0.166 A at 1.5 nm)", "measured on the engine's potential" | committed test print (C9), summary.json | OK; measured on a [100] single-terrace test cell (the overlap does not depend on azimuth). "Gap" without its potential dip: A9b-m4 |
| B41 "Every parameter carries ASSUMPTION B41; B41 with none or any other value is refused" | C5 | OK (variant pairing: A9b-n2) |
| B12 "at most a/8", "at least 0.5 A", "0.05 layer", per-parameter labels | code constants, tests | OK. Missing: the non-conformal engine disagreement (A9b-M1); wording (A9b-n6) |
| B7 "a measured absence of amorphous Si (a zero) is a PROJECT_INPUT", "V'_ox = 0 is never a measurement", "a comparison run refuses every per-parameter demo stand-in and ... every per-parameter ASSUMPTION" | C5, C6 | OK |
| B7 "(so V_ox and V'_ox ... need a policy decision before a comparison run)" | C5 | incomplete: consumed_layers (derived) and both edge widths are in the same position (A9b-M2) |

## 9. Tests X4 changed or added (read)

New files: `tests/structure/test_oxide_structure_a8_fixes.py`,
`tests/forward/test_oxide_multislice_a8_fixes.py` and `tests/pipeline/test_oxide_pipeline_a8_fixes.py`.

Changed:
* `tests/structure/test_oxide_structure.py`,
  `tests/forward_geometric/test_oxide_geometric.py`, `tests/forward/oxide_cases.py`,
  `tests/forward/test_oxide_multislice.py`, `tests/forward/test_memory_model.py` and
  `tests/pipeline/test_oxide_pipeline.py`: diffs read (`git diff 36d2250 HEAD`).
* `tests/io/test_io_config_stand_ins.py` is T3's change (B42), not X4's.

The overlap test measures x_c from the layer array and the top plane from the crystal array
independently, so it is not a tautology: the A1 and A2 mutations fail it. The memory test checks
only the slice-loop peak. The host-build phase (32 B/px) is not exercised as a peak (see A9b-n4
for continuum bases).

## 10. Test runs of this audit

    C6 control (X4 and E4 oxide files, scratch copy):  146 passed in 7.71s
    C9  6 passed in 13.73s     C10  4 passed in 9.13s     C15  165 passed in 10.83s
    orchestrator's full suite (not my run, SP/full_suite_x4t3.txt): 1399 passed, 8 skipped, 12 warnings in 1015.20s

## 11. NOT RUN

* The full suite. It was run by the orchestrator concurrently; I only read its last lines.
* The heavy parts of `tests/forward/test_oxide_multislice.py` ((c) flat runs, (d) smoke).
* A propagated multislice run of a non-conformal (per-terrace override) oxide cell; A9b-M1 rests
  on the 1-D laterally averaged model and the engines' formulas.
* A laid-out oxide cell in the sizing tool (C8 is a scaling estimate).
* cupy/GPU.
* The [110] multislice with the layer.
* The a-Si layer in propagation.
* An independent solver with the layer.

## Verdict

X4 cannot be called final yet. Its code fixes of A8-M1 (a-Si zero), m1-m6 and n1-n3 are correct,
they are tested (every reversion fails a test), and they leave the B41 demo path intact. Before X4
can be closed:

1. **A9b-M1 (A8-M2, second half):** state the non-conformal disagreement between the engines
   with its size (about 0.86 against 4.45 rad/A at a fixed count) in `NOT_REPRESENTED`,
   `B4_OXIDE_GROWN`, B12 and B41. Flag or refuse atomistic multislice cells whose terraces differ
   by less than a whole consumed layer when they are used for engine comparisons. Correct the
   "one continuum geometry for both engines" claim in X4 section 2.
2. **A9b-M2:** before any comparison run, either give consumed_layers a derived label and give
   model parameters (V_ox, V'_ox, w_v, w_i) an admissible model label, or at least amend B7 to name
   all five and record the orchestrator's policy decision.
3. Finish X4's report: fill the four placeholders with the printed values (C9, C10, C12, C14 give
   them), and save or rerun the missing mutation outputs.
4. Minor fixes when adopting: A9b-m1 (B26 per parameter), m2 (the m4 rationale), m3 (script the
   quoted numbers), m4 (state the gap's potential dip), m6 (oxide sizes to Ali).

Items 1 and 2 are documentation plus a guard. No change is needed for the conformal B41 demo.
