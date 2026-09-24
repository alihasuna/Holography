# X4 - Fixes after the audit A8 of E4's continuum oxide overlayer

Agent X4, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r` (HEAD 36d2250 when
work started; X3's 39b6151 and a snapshot b96bc6e arrived meanwhile). Status: DRAFT (written
incrementally). Nothing committed or pushed by X4; nothing written under outputs/.

Input: `docs/agent_reports/A8_e4_oxide_audit.md` (read in full) with its scratch scripts and outputs
(`SP/a8/`, SP = the session scratchpad), E4's report and code, and the orchestrator's decisions for
A8-M1, A8-M2 and m1-m7. X4's scratch scripts and outputs are in `SP/x4/` (not in the repository).
Other agents editing the tree at the same time: X3 (null-test files, HPC kit, dry-run report; not
touched by X4) and T3 (buried torus: `structure/features.py`, `structure/shapes.py`,
`forward/feature_cell.py`, registry row B42, `tests/io/test_io_config_stand_ins.py`; not touched
by X4).

## 1. Findings: fixed or declined

Line numbers are those of the working tree at the end of X4's work.

| finding | status | code (file:line) | tests |
|---|---|---|---|
| A8-M1 a-Si = 0 cannot be a PROJECT_INPUT | FIXED: one label PER PARAMETER in the item-12 record (`overlayer.labels`, keys = `structure.oxide.LABEL_KEYS`); oxide.py accepts a-Si = 0 with any evidence label (PROJECT_INPUT = a measured zero, recorded as such) and refuses a missing/blank label; V'_ox = 0 still needs ASSUMPTION/TEST_ONLY; the comparison gate applies the record rule to every per-parameter ASSUMPTION | `structure/oxide.py:280-284, 319-323`; `pipeline/config.py:971-1112` (`OXIDE_KEYS`, `oxide_parameter_labels`, `oxide_spec_from_config`), `:1196-1206` (`oxide_parameter_assumptions`), `:1265-1268` (comparison gate), `:1288-1291` (run summary), `:1619, 1692-1711` (list-inputs); `configs/demo_smoke_si001.yaml:559-568` (and the four other B41 variants) | `tests/structure/test_oxide_structure_a8_fixes.py` (M1 block); `tests/pipeline/test_oxide_pipeline_a8_fixes.py` (M1 block); changed on purpose: `tests/pipeline/test_oxide_pipeline.py::test_zero_absorption_or_a_si_under_project_input_needs_assumption`, one case of `tests/structure/test_oxide_structure.py::test_invalid_or_missing_inputs_are_refused` (section 3) |
| A8-M2 continuum layer overlaps the atomistic crystal by 0 to a/4; recorded quantisation misstates it | FIXED (orchestrator's second option, with the reference corrected): the pre-oxidation SURFACE of an atomistic terrace is its Si equivalent boundary, a/8 above its top atomic plane (`terrace_stacks(..., crystal="atomistic")`, a new REQUIRED keyword; "continuum": the boundary itself); the recorded `interface_overlap_A` (= `interface_quantisation_A`) = f t + t_a - N a/4 is the true overlap (+) or gap (-) of the continuum layer with the kept crystal's equivalent boundary, bounded by a/8; measured on the engine's own potential | `structure/oxide.py:108-120, 362-517` (`REFERENCE_PLANE`, `INTERFACE_OVERLAP_RULE`, `rounding_margin`, `terrace_stacks`), `:535` (`stack_phase_terms` from the surface); `structure/si001.py:840`; `forward/cell.py:225-257, 297-298`; `forward/geometric/model.py:320-341, 351-352` (checks the reference; ray trace unchanged) | `tests/forward/test_oxide_multislice_a8_fixes.py::test_recorded_overlap_is_what_the_engine_potential_contains` (A8's three cases); `tests/structure/test_oxide_structure_a8_fixes.py` (M2 block) |
| A8-m1 Born estimate quoted for the 0.5 A edge | FIXED: the exact 1-D value (A8 C6: 1.95e-9 at 16.1347 mrad, 1.8345e-9 at the central bin; engine 1.835e-9) replaces the Born figure in the oxide docstring and refusal message, `EDGE_W05_REFLECTIVITY` (recorded), the geometric model docstring and record, the overlayer docstring; the test prints the exact value (transfer matrix ported to `tests/forward/oxide_cases.exact_graded_edge_r`) and now ASSERTS the engine against it (1 % in abs r) | `structure/oxide.py:44-51, 94-99, 252-257` (refusal message); `forward/geometric/model.py:49-60, 362-363`; `forward/multislice/overlayer.py` docstring | `tests/forward/test_oxide_multislice.py::test_graded_edge_of_0p5_A_suppresses_the_layer_reflection` (added assertion; section 3) |
| A8-m2 B41 vouches for values its row does not state | FIXED: `OXIDE_STAND_IN_ROWS["B41"]` = the row's values ((20 A, 7) or (15 A, 5); 2.20 g/cm^3; 10.34 V; 0.40 or 0 V; 0.5/0.5 A; a-Si 0; amorphous SiO2; bulk); every parameter labelled B41 and the material/termination of a B41 record must take a row value; `overlayer: none` under B41 refused | `pipeline/config.py:987-993, 1119-1157, 928-937` | `tests/pipeline/test_oxide_pipeline_a8_fixes.py` (m2 block, incl. A8's probes: none; t 50 A/N 16/V' 0.1 V; interface 0 is refused by m5 first) |
| A8-m3 memory model omits the layer | FIXED: `memory_model(..., overlayer)` REQUIRED (None or dict(staircase_axis, n_terraces), from `overlayer_memory_arguments(cell)` in `estimate_resources`): one working-precision complex array per pixel resident in the slice loop (terraces along y or one terrace), n_terraces x nx along z; the complex128 host build (32 B/px) as a realise phase (numpy) and a host phase (cupy) | `forward/multislice/engine.py:496-498, 515-563, 575-576, 605-608, 623-626, 635-638, 681`; `overlayer.py:228-232`; `tools/hpc/supercell_sizing.py:599-608` (`memory_row(..., overlayer)`), `:1135-1137` (layout), per-scenario oxide line, checks `:1958-1990`, table column `:2001` | `tests/forward/test_memory_model.py::test_oxide_layer_arrays_in_the_memory_model` (3 cases, tracemalloc, TOL 2 % unchanged); `test_memory_model_contract` (overlayer=None added, refusals added); sizing tool 63/63 checks |
| A8-m4 2.0 nm sits on the rounding boundary | FIXED: `rounding_margin` records per terrace the distance (layers, A) and where the count changes (density, thickness); closer than `MIN_ROUNDING_MARGIN_LAYERS = 0.05` layer (0.068 A of consumed depth; stated rule) the spec is refused unless the new REQUIRED field `rounding_boundary_acknowledged` is True, and an unneeded acknowledgement is refused; loud note in the record; B41 2.0 nm variants acknowledge (0.0036 layer; count 6 below 2.19877 g/cm^3) | `structure/oxide.py:86-93, 362-386, 455-495`; `configs/demo_smoke_si001.yaml:559, 600, 641, 682, 790` | `tests/structure/test_oxide_structure_a8_fixes.py` (m4 block); `tests/pipeline/test_oxide_pipeline_a8_fixes.py::test_rounding_boundary_acknowledgement_in_the_variants` |
| A8-m5 interface grading not enforced | FIXED: `interface_width_A >= MIN_INTERFACE_WIDTH_A = 0.5` A unless the new REQUIRED field `sharp_interface_test_flag` is True with a TEST_ONLY interface label; an unneeded flag is refused; the pipeline never sets it | `structure/oxide.py:86, 259-276`; `pipeline/config.py` (`sharp_interface_test_flag=False`) | `tests/structure/test_oxide_structure_a8_fixes.py` (m5 block); `tests/pipeline/test_oxide_pipeline_a8_fixes.py::test_sharp_interface_is_refused`; existing TEST_ONLY sharp-interface fixtures now state the flag (section 3) |
| A8-m6 build-up assertion through the overlayer untested | FIXED (test only): a continuum oxide cell long enough for the plain item-4 length but not for the stack refuses with `item4_buildup_length_through_overlayer`; the long cell passes | none (`forward/cell.py` assertion unchanged) | `tests/forward/test_oxide_multislice_a8_fixes.py::test_buildup_assertion_through_the_overlayer_refuses` (fails under A8's M13, section 5) |
| A8-m7 reading of the (c) length series | RECORDED (no code change beyond a comment): A8's reading in section 6 and in a comment at `C_EXTRA_LENGTH_A` | `tests/forward/test_oxide_multislice.py:200-205` | - |
| A8-n1 numbers as strings | FIXED: `_num` accepts only numbers.Real (numpy scalars included) | `structure/oxide.py:188` | structure and pipeline n1 tests |
| A8-n2 B4_A4_100 text next to the overlayer statement | FIXED (note): every buried step with a relation records `buried_b4_note` (the bare-step statement's "overlayer" clause refers to a layer ON that step; `model_assumption_B4_overlayer` states how the continuum layer enters); the strings themselves unchanged (the geometric engine keys on them) | `structure/si001.py:827-830, 907` | `test_buried_b4_statement_carries_its_note` |
| A8-n3 item-12 value without `overlayer`/`termination` passes the load | FIXED: both keys required at load (no default) | `pipeline/config.py:921-926` | `test_item12_value_needs_both_keys_at_load` |

Declined: none. Partly: A8-M1's alternative "a PROJECT_INPUT zero that states its detection
limit" is not enforced as a number (the record says "a measured zero (below the detection limit of
the witness measurement)"; the limit itself would be a new item-12 field, docs/06, not X4's).

## 2. Design notes

### A8-M1: per-parameter labels (configuration format)

    overlayer: {model: continuum_oxide, material, thickness_A, density_g_cm3, consumed_layers,
                V_real_V, V_imag_V, vacuum_edge_width_A, interface_width_A,
                amorphous_si_thickness_A, rounding_boundary_acknowledged,
                labels: {thickness, density, consumed_layers, V_real, V_imag, vacuum_edge,
                         interface, amorphous_si[, amorphous_si_potential]}}

Each label is "PROJECT_INPUT" (only inside a supplied PROJECT_INPUT record, whose supplied_by /
supplied_on / source it shares), "ASSUMPTION <id>" (registered for item 12; inside a stand-in
record, that record's id) or "TEST_ONLY" (inside a TEST_ONLY record, in-memory only). The spec gets
the qualified label of each (e.g. "PROJECT_INPUT item 12 (<source>)", "ASSUMPTION B41 (stands in
for PROJECT_INPUT item 12)"). purpose "comparison" refuses a per-parameter ASSUMPTION exactly when a
record would be refused (a demo id, or any ASSUMPTION for a blocking item). Consequence to note for
the orchestrator: item 12 is blocking (`BLOCKING_ITEMS`), so under the present rule a comparison
run needs EVERY oxide parameter labelled PROJECT_INPUT, V_ox and V'_ox included, although E9 calls
V'_ox a model value; admitting model values would need a policy decision (e.g. a non-blocking model
row), not taken here. list-inputs shows one row per parameter; the run summary lists the
per-parameter ASSUMPTIONs.

### A8-M2: which option, and what the potential contains

Chosen: the orchestrator's second option ("record the true overlap measured on the engine's own
potential"), after correcting the reference. The stack of an atomistic terrace starts from its Si
equivalent boundary (top atomic plane + a/8: each (001) layer occupies a/4 centred on its plane, Si
atoms conserved), so x_i = H + a/8 - f t and x_t = H + a/8 + (1 - f) t in BOTH engines, and the
kept crystal (top plane H - N a/4, equivalent boundary H - N a/4 + a/8) meets the layer's lower
boundary x_c with overlap f t + t_a - N a/4 in [-a/8, a/8] (was [0, a/4], biased by a/8). Not
chosen: pinning x_c to the kept crystal's boundary (zero overlap by construction). It moves the
same quantisation error to the top of the layer and, in the geometric engine, would either
disagree with the multislice on x_i or quantise the grown-oxide sensitivity (E9's 4.27-4.71 rad/A
are laterally averaged continuum rates); the chosen form keeps one continuum geometry for both
engines and states the atomistic crystal's unavoidable partial-layer error explicitly. The geometric
engine's output is unchanged bit for bit (its layer terms are differences; its ray trace keeps its
bare-surface convention, heights + (1 - f) t; section 5).

(measurements: section 5)

### A8-m4: the stated margin

MIN_ROUNDING_MARGIN_LAYERS = 0.05 layer = 0.068 A of consumed depth: at 2 nm and 2.20 g/cm^3 the
count then survives a thickness change of 0.15 A or a density change of 0.8 % (0.017 g/cm^3), the
precision at which item-12 values are stated (DERIVED_HERE, a stated rule). Below it the spec is
REFUSED unless acknowledged (the orchestrator allowed either refusal or an acknowledged flag; the
acknowledgement is required, recorded with the density and thickness at which the count changes,
and refused when not needed).

## 3. Existing tests changed on purpose (none weakened; no tolerance changed)

New REQUIRED spec fields (`sharp_interface_test_flag`, `rounding_boundary_acknowledged`) and the
REQUIRED `crystal` keyword of `terrace_stacks` and `overlayer` argument of `memory_model` had to be
stated by the existing fixtures and calls; assertions changed only where the fixed behaviour
contradicts the old expectation:

* `tests/structure/test_oxide_structure.py`: `spec()` states the two new fields (the
  acknowledgement exactly when needed, computed by `oxide.rounding_margin`); `crystal="atomistic"`
  added to four `terrace_stacks` calls. `test_two_nm_stack_equals_e9`: E9's 8.8301/11.1699 A are
  now asserted from the pre-oxidation SURFACE for a continuum crystal (as before, where it equals
  the input height) AND for an atomistic one (surface = plane + a/8; the kept top plane 5 - 7 a/4
  still asserted); the continuum call asserts no atoms (None) and zero overlap (A8-M2).
  `test_invalid_or_missing_inputs_are_refused`: the case "a-Si = 0 labelled PROJECT_INPUT is
  refused" is replaced by "a-Si = 0 with a blank label is refused" (A8-M1 decision: a measured
  zero is accepted; acceptance tested in the new file).
* `tests/forward_geometric/test_oxide_geometric.py`: `spec()` states the two new fields; no
  assertion changed (x_offset 11.1699 A and every phase still hold: the geometric engine's output is
  bitwise unchanged).
* `tests/forward/oxide_cases.py`: `oxide_spec` gains `iflag` and `ack` (acknowledgement stated
  exactly when needed); `oxide_only_case` states `iflag=True` (its interface joins two regions of
  the same potential, no step; the TEST_ONLY flag is now required for w_i = 0);
  `atomistic_case`'s stack (layer top above the kept top plane) is (1 - f) t + N a/4 + a/8 (was
  without a/8) and is returned as `stack_A`; new `exact_graded_edge_r` (A8's transfer matrix).
* `tests/forward/test_oxide_multislice.py`: `iflag=True` in
  `test_sharp_interface_uses_the_crystal_base_bit_for_bit` and in the spec-hash case of
  `test_refusals_of_the_engine` (otherwise refused by m5 before the hash check);
  `test_graded_edge_of_0p5_A_suppresses_the_layer_reflection` prints the exact value and ADDS the
  assertion |r_engine|/|r_exact| - 1 within GRADED_TOL (1 %; the SUPPRESSION assertion unchanged);
  (c) `flat_runs`: the vacuum read-out window starts 5 A above the reference layer top taken from
  the geometry (`depth + stack_A`, was the hard-coded 20.67 A, now 21.35 A); nothing asserted on
  the ratios (E9 M1), the recorded-quantity assertions unchanged.
* `tests/forward/test_memory_model.py`: `test_memory_model_contract` passes `overlayer=None` and
  asserts two new refusals; tolerance TOL = 2 % unchanged.
* `tests/pipeline/test_oxide_pipeline.py::test_zero_absorption_or_a_si_under_project_input_needs_assumption`:
  the V'_ox = 0 refusal is kept, stated through the per-parameter label (V_imag: PROJECT_INPUT in a
  supplied record); the a-Si = 0 half of E4's docstring (refusal) is inverted to acceptance with a
  PROJECT_INPUT a-Si label (A8-M1).

New test files: `tests/structure/test_oxide_structure_a8_fixes.py`, `tests/forward/test_oxide_multislice_a8_fixes.py`,
`tests/pipeline/test_oxide_pipeline_a8_fixes.py`; new tolerance: the overlap on the engine's potential within
dx/2 = 0.01 A (a priori: the atomic-plane peak lies within half a pixel of the sampled maximum; the
layer integral is exact to exp(-2 pi^2 (w/dx)^2) = 0; E4's placement is off by a/8 = 0.679 A).

## 4. Test runs (verbatim last lines; `venv/bin/python -m pytest -q -p no:cacheprovider`, 4 shared cores)

    tests/structure: 383 passed in 32.58s
    tests/io:        FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
                     1 failed, 127 passed in 1.31s
    tests/pipeline:  162 passed in 292.92s (0:04:52)
    tests/forward:   SKIPPED [2] tests/forward/test_null_readout_known_answer.py:225: L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1
                     SKIPPED [1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1
                     156 passed, 3 skipped in 927.18s (0:15:27)
    full suite:      (FULL_SUITE_RESULT)

The io failure is `AssertionError: B42` (`assert aid in rows, aid`): agent T3's new registry id B42
has no row in docs/model_assumptions.md yet; it is not caused by X4's changes (X4 did not touch the
registry or that test). The directory runs of structure and io used the code before two final
edits (the rise of the layer top computed as (1 - f) t again, for bit-identity, and the renaming
of the three new test files to unique basenames, `*_a8_fixes.py` -> `test_oxide_{structure,
multislice,pipeline}_a8_fixes.py`, needed because pytest cannot collect one basename in several
test directories without `__init__.py`); the full suite ran on the final tree.

## 5. Results of the fixes (printed by the tests and scripts)

A8-M2, the overlap on the engine's own potential (`test_recorded_overlap_is_what_the_engine_potential_contains`, `-s`):

    t 20.0 A, N 7, 2.2 g/cm^3: layer plateau 10.3400 V, lower boundary 21.352789 A (recorded 21.352789), kept top plane 19.9991 A (recorded 20.0000); overlap measured -0.6749 A, recorded -0.6739 A (E4's placement: A8 measured +0.005 A)
    t 15.0 A, N 5, 2.2 g/cm^3: layer plateau 10.3400 V, lower boundary 20.844876 A (recorded 20.844876), kept top plane 20.0000 A (recorded 20.0000); overlap measured -0.1660 A, recorded -0.1660 A (E4's placement: A8 measured +0.513 A)
    t 20.0 A, N 6, 2.198 g/cm^3: layer plateau 10.3400 V, lower boundary 20.003091 A (recorded 20.003091), kept top plane 19.9998 A (recorded 20.0000); overlap measured +0.6756 A, recorded +0.6758 A (E4's placement: A8 measured +1.355 A)

Before the fix the same measurement (`SP/x4/explore_m2.py`, E4's placement) gave +0.00407, +0.51294,
+1.35456 A against a recorded -0.67393, -0.16601, +0.67577 A: A8's C9 numbers, off by a/8. After it
the recorded value is what the potential contains to 0.001 A, and the bound is a/8 (was [0, a/4]).
For the B41 2.0 nm stand-in the layer now leaves a 0.674 A gap above the kept crystal's equivalent
boundary (it overlapped by 0.005 A); the gap is the honest consequence of consuming 7 whole layers
for 6.504.

A8-m3, the layer in the memory model (`test_oxide_layer_arrays_in_the_memory_model`, `-s`):

    oxide, terraces along y, complex64, 840 x 504: measured 41.305 MB, model 41.273 MB (+0.076%); layer term 8.00 B/px
    oxide, terraces along y, complex128, 840 x 504: measured 82.063 MB, model 82.029 MB (+0.042%); layer term 16.00 B/px
    oxide, terraces along z, complex64, 840 x 336: measured 25.248 MB, model 25.217 MB (+0.123%); layer term 0.05 B/px

Before the fix these deviated by +8.1 / +16.1 / +0.1 B/px (A8 C11). `tools/hpc/supercell_sizing.py`
rerun, output saved to `tools/hpc/supercell_sizing_output.txt`, last line `63/63 checks pass;
runtime 26 s`; the two new checks:

    CHECK PASS oxide_layer_memory_A8_m3_2a_a4_miscut0.1_r0.10: layer arrays add 0.2177 GB to the device peak and to the numpy slice loop = 8 B x 2250 x 12096 px (complex64; CPU-job peak +0.0000 GB, numpy peak phase 'realise: atom sorting and records'); on A8's grid 2000 x 12096: 0.1935 GB (A8 m3: +0.194 GB)
    CHECK PASS oxide_layer_memory_A8_m3_2a_a4_miscut0.1_r0.05: layer arrays add 0.2613 GB to the device peak and to the numpy slice loop = 8 B x 2700 x 12096 px (complex64; CPU-job peak +0.0000 GB, numpy peak phase 'realise: atom sorting and records'); on A8's grid 2700 x 12096: 0.2613 GB (A8 m3: +0.26 GB)

Correction to A8-m3's percentages: A8 scaled to H2's original grid (2000 x 12096, 4.096 GB); the
tool's current 0.1 deg row is 2250 x 12096 (H7's run-in), where the layer adds 0.218 GB to the
3.162 GB device peak (+6.9 %) and nothing to the CPU-job peak, whose phase is the atom sorting of
realise(), before the layer exists. Table 14 now carries a column "with oxide: GPU device / CPU job
peak" (e.g. 3.38 / 8.2 GB for that row).

A8-m1 (`test_graded_edge_of_0p5_A_suppresses_the_layer_reflection`, `-s`): (M1_PRINT)

Pipeline demo, geometric `oxide_2p0nm` (`SP/x4/pipe_oxide.py`, outputs in `SP/x4/pipe/`):

    oxide_2p0nm 5 s, peak RSS 196 MB
       built 2.71545 measured +2.7153 +- 0.0165
       built -1.357725 measured -1.3578 +- 0.0082
       built -1.357725 measured -1.3575 +- 0.0082
       arrays: 26 vs A8's 26; bitwise identical to A8's pre-fix run: 26; differing: []

The dry run of `multislice_tiny_oxide_2p0nm` passes the overlayer build-up assertion with the
thicker stack (21.353 A above the kept top plane, was 20.67): available 2722.8 A, required 2405.9 A.
(MULTISLICE_RUN)

Deliberate breaks of the fixed code, each on a scratch copy of the package (never the repository;
`SP/x4/mutate.py`, output `SP/x4/mutations.out`); control first:

| break | targets | result |
|---|---|---|
| X0 control (no change) | the five targets below | 69 passed |
| X13 overlayer build-up ignores the stack (A8's M13) | m6 test | 1 failed |
| X2 E4's placement (no a/8) | M2 potential test + structure file | 7 failed, 26 passed |
| X4 no rounding-margin refusal | structure + pipeline files | 4 failed, 57 passed |
| X5 no interface minimum | structure + pipeline files | 5 failed, 56 passed |
| X1 comparison gate ignores per-parameter labels | pipeline file | 1 failed, 30 passed |
| X6 no B41 row check | pipeline file | 9 failed, 22 passed |
| X3 memory model without the layer (terraces along y) | memory test | 2 failed, 1 passed (the along-z case is not touched by this break) |
| X7 erfc(x/w) instead of erfc(x/(sqrt2 w)) (A8's M5b) | w = 0.5 A test | 1 failed: the new exact-value assertion (15.9 in abs r); the old suppression bound passes (1.98e-4 <= 1e-3) |

(A first batch collected X2, X4 and X5 with an error: two new files had the same basename; renamed,
section 4.)

## 6. A8-m7: A8's reading of the (c) length series (recorded; no code change)

A8 section 4: the drift of E4's raw oxide/clean ratio (0.37 -> 0.54 -> 0.62 at +3000/+4500/+6000 A)
is the read-out window, not the surface-step Fresnel term: at +3000 A 95 % of the oxide runs'
specular beam (and of a clean run launched at the same height) is still in the window ramp or below
it at the exit plane, 55 % of E4's clean run, whose beam reaches the crystal about 1150 A earlier;
with the same launch height the +3000 A ratio is 0.74, not 0.37; once the read-out is complete
(>= +6000 A, < 5 % below) the ratio no longer depends on the launch (0.623 vs 0.630; 0.586 vs
0.589). The +3000 and +4500 A values are therefore read-out-truncated; E4's "within 2 % at every
length" for the absorption-only ratio becomes 3.1 % at +9000 A (0.505-0.532 over 3000-9000 A
against the model value 0.5213); the remaining 6 % change between 6000 and 9000 A coincides with a
0.020 mrad bin shift and is not separated from it (a common-bin study: NOT RUN). Recorded as a
comment at `C_EXTRA_LENGTH_A` (`tests/forward/test_oxide_multislice.py:200-205`); nothing is
asserted on it (E9 M1). E4's report itself (docs) is not X4's to edit. (C_PRINT)

## 7. NOT RUN

* cupy/GPU with the layer (no GPU): the cupy device and host terms of the layer are code reading
  plus the numpy tracemalloc check.
* The [110] configuration with the layer in the multislice; non-conformal (grown) cells and the
  a-Si layer in multislice PROPAGATION; the propagated-amplitude consequence of the A8-M2 change
  (only the potential is measured; (c) and (d) run with it but assert no physics); the atomistic
  fixed-beam gate with the layer; dx/dz convergence of (c) and (d); a common-bin cell-length study
  of (c); an independent solver with a layer; a demo_hpc oxide variant.
* A comparison run with a supplied item-12 record (no real item-12 values exist; only in-memory
  TEST fixtures exercise the gate).
* The atomistic amorphous SiO2 layer (still NOT IMPLEMENTED).
* The A8-M1 detection limit of a measured zero as a number (would need a new item-12 field).
* Docs rows: section 8 (orchestrator).

## 8. Proposed changes of docs/model_assumptions.md rows (for the orchestrator; X4 does not edit docs/)

**B41** (replace the parts named; everything else of the row stays):
* after "vacuum edge and oxide/Si interface graded 0.5 A (erf, Gaussian gradient of s.d. 0.5 A;
  E9 M4, line 241)": "; the exact 1-D reflectivity of the 0.5 A vacuum edge is 1.95e-9 at 16.1347
  mrad (|r| x 8.5e-4 of the sharp edge; transfer matrix, audit A8 C6), which the multislice engine
  reproduces (1.835e-9 against 1.8345e-9 at its central bin); line 241's Born factor exp(-(q w)^2)
  is 57 times lower (an underestimate)".
* after "consumed layers 7 (5) = the nearest whole count of 6.50 (4.88) a/4 layers (lines
  125-127)": "; at 2.0 nm the count lies 0.0036 layer (0.005 A) from its rounding boundary: it is 6
  below 2.19877 g/cm^3 (-0.056 %), so at <110> the terrace type at a buried a/4 step is set by the
  fourth significant digit of an assumed density; the 2.0 nm variants therefore state
  rounding_boundary_acknowledged: true (a count closer than 0.05 layer to its boundary is refused
  without it, audit A8 m4)".
* new sentence before "Stands in for": "The stack is placed from each terrace's Si equivalent
  boundary, a/8 above its top atomic plane; on the atomistic crystal of the multislice variant the
  layer's lower boundary lies 0.674 A above the kept crystal's equivalent boundary (a gap; 0.166 A
  at 1.5 nm), recorded as interface_overlap_A and measured on the engine's potential (audit A8 M2,
  report X4). Every parameter carries the label ASSUMPTION B41 (per-parameter labels, audit A8 M1);
  B41 vouches for these values only: B41 with overlayer none or with any other value is refused
  (audit A8 m2)."

**B12** (replace "(Si consumption f t_ox from the stated densities, graded vacuum edge of at least
0.5 A, optional amorphous-Si layer, per-terrace overrides in the engines but refused by the
pipeline)" by): "(Si consumption f t_ox from the stated densities, the stack placed from the Si
equivalent boundary a/8 above the top atomic plane with the atomistic crystal's whole-layer overlap
or gap (at most a/8) recorded, vacuum edge AND oxide/Si transition graded over at least 0.5 A
(sharp only with TEST_ONLY flags), consumed-layer counts within 0.05 layer of their rounding
boundary refused unless acknowledged, optional amorphous-Si layer, per-terrace overrides in the
engines but refused by the pipeline, one evidence label per parameter in the item-12 record;
reports E4, X4)".

**B7** (append to the Revision-5 part): "Since report X4 (audit A8 M1) the item-12 record carries
one evidence label per oxide parameter: a measured value, including a measured absence of amorphous
Si (a zero), is a PROJECT_INPUT while unmeasured values remain ASSUMPTIONs; V'_ox = 0 is never a
measurement. A comparison run refuses every per-parameter demo stand-in and, item 12 being blocking,
every per-parameter ASSUMPTION (so V_ox and V'_ox, model values in E9, need a policy decision before
a comparison run)."
