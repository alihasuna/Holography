# A10b - Re-audit of X5 (fixes of audit A9b on the continuum-oxide overlayer)

Auditor: agent A10b, 2026-09-24. Status: DRAFT (written incrementally; not final).

Scope: repository /home/user/Holography, branch claude/electron-holography-orchestration-nakd7r,
commit 00851da (working tree clean). Read in full: docs/agent_reports/A9b_X4_audit.md,
docs/agent_reports/X5_a9b_fixes.md, `git diff 62ced11..00851da` of `structure/oxide.py`,
`structure/si001.py`, `forward/cell.py`, `forward/geometric/model.py`, `pipeline/config.py`,
`pipeline/run.py`, `io/assumption_registry.yaml`, `configs/demo_smoke_si001.yaml`,
`tools/hpc/supercell_sizing.py` and its output, the three new a9b test files and the changed oxide
tests; `tools/review/x5/` (4 scripts, 4 outputs); rows B7, B12, B41, B43 of
docs/model_assumptions.md; docs/06 item 12. Current `oxide.py` (700 lines) and the item-12 part
of `pipeline/config.py` (lines 40-82, 692-800, 935-960, 1000-1600) read in full.

Rules kept: this report is the only repository file written; the code under audit was not
modified (mutations in scratch copies only); nothing committed; nothing under outputs/. Scratch:
SP/a10b/, SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
All runs single-threaded (OMP_NUM_THREADS=1) while a full suite ran concurrently.

Grades: MAJOR (must be resolved before the affected item is adopted; reproduction given), minor,
note.

## Findings so far (in progress)

### A10b-M1 (MAJOR). "Both parities" is only acknowledged, and the other parity cannot be run under honest labels

`pipeline/config.py:1436-1449` (`_check_oxide_uncertainties`): when the item-12 count interval
spans a rounding boundary, the run passes with `both_parities_acknowledged: true`. The run then
computes ONE count, the derived nominal one (`config.py:1372`, stated count must equal
`nearest_consumed_layers`). Nothing runs, schedules, links or checks a run at the other parity,
and the item-12 record (`oxide_item12_record`, `config.py:1465-1508`) has no field naming the
parity actually run or a companion run. docs/06 item 12 (line 29) tells Ali "the simulation then
runs both parities"; B12 says comparison runs "need both parities"; B7 "needs both parities".

The other parity also cannot be produced with the measured values:
* `consumed_layers: 6` at the measured 20.0 A / 2.20 g/cm^3 is refused by the derived-count check
  and, at engine level, by the nearest-count rule (|6 a/4 - 8.8301| = 0.684 A > a/8);
* per-terrace overrides are refused by the pipeline;
* the only route is to change a PROJECT_INPUT value to a point inside the uncertainty box
  (thickness 19.5 or 19.0 A), which the gate accepts with the label
  "PROJECT_INPUT item 12 (...)" although it is not the measured value. No admissible label exists
  for such a value (B43 is refused on thickness; B41 is refused in comparison runs and off its
  pairs).

Reproduction (D2, `SP/a10b/d2_parity.py`, output `d2_parity.out`; fabricated TEST supply,
in-memory):

    [REFUSED (comparison gate, other items only; OXIDE ENTRIES PASS)] acknowledged True -> oxide entries pass the comparison gate
    [ACCEPTED] same, demo purpose (to read the record)
          recorded count interval: {'counts': [6, 7], 'parities': ['even', 'odd'], 'spans_boundary': True, ...}
          the run's spec: consumed_layers = 7 ; terrace overrides: None None
          keys of the item-12 record naming the parity actually run or the companion run: []
    [REFUSED] consumed_layers 6 at t 20.0 A (measured)
    [REFUSED] engine-level spec: count 6 at 20.0 A / 2.20 (TEST_ONLY labels): terrace 0: consumed_layers = 6 (8.1463 A) is not the whole-layer count nearest ...
    [REFUSED (comparison gate, other items only; OXIDE ENTRIES PASS)] thickness_A 19.5 (inside the box, NOT the measured 20.0) labelled PROJECT_INPUT, count 6, comparison
    [ACCEPTED]    same, demo purpose: its thickness label
          thickness label: PROJECT_INPUT item 12 (TEST: fabricated supply to exercise the gate (audit A10b))
    [REFUSED] thickness 19.5 labelled ASSUMPTION B41 (the only ASSUMPTION a thickness can carry), comparison
          ... stand-in B41 ... states (thickness_A, consumed_layers) in [(20.0, 7), (15.0, 5)], got (19.5, 6)

Why it matters: at <110> the parity decides the terrace type at every buried a/4 step (E9
section 3 item 2), i.e. the sign of the residual delta. With realistic witness uncertainties
every 2 nm case spans the boundary (x5_oxide_numbers_output: +-0.1 A / +-0.01 g/cm^3 already
gives [6, 7]). A comparison result would then carry one parity, with docs/06 telling Ali that
both were run, and the second run is only possible by mislabelling a thickness as PROJECT_INPUT,
which the decision forbids in spirit ("the headline label must not read PROJECT_INPUT when a
parameter is not").

Fix needed: either (a) make the pipeline run both parities (e.g. a derived per-run consumed-layer
count override labelled DERIVED_HERE "count interval of item 12, other parity", admitted only when
the interval spans the boundary, with the pair linked in the manifest), or (b) refuse a
comparison run whose interval spans a boundary, or (c) at minimum record in `oxide_item12` which
parity this run covers and that the other is NOT run, and correct docs/06 item 12, B7 and B12
("runs both parities" -> "the run records that only one parity was computed").

### A10b-M2 (MAJOR). The measurement-record requirement is defeated by one-character or explicit "not measured" records

`pipeline/config.py:1017, 1197-1202`: a record is refused only if, after lower-casing and
whitespace folding, it EQUALS one of seven words or a NON_SUPPLIERS entry. Punctuation,
single characters and explicit non-measurement statements pass. Every probe below was made with
purpose "comparison"; "OXIDE ENTRIES PASS" means the run is refused only for the demo's other
stand-ins and no oxide entry is named (D1, `SP/a10b/d1_probes.py`, `d1_probes.out`):

    [... OXIDE ENTRIES PASS] measurements.V_real = '?'
    [... OXIDE ENTRIES PASS] measurements.V_real = '.'      (also '-', 'x', '...')
    [... OXIDE ENTRIES PASS] measurements.V_real = 'measured.'   (while 'measured' is refused)
    [... OXIDE ENTRIES PASS] measurements.V_real = 'not measured'
    [... OXIDE ENTRIES PASS] measurements.V_real = 'not measured: independent-atom model value, E9 out:166'
    [... OXIDE ENTRIES PASS] measurements.V_real = 'ASSUMPTION B43'      (also 'B43', 'nominal', '10.34 V')
    [... OXIDE ENTRIES PASS] measurements.V_real = 't.b.d.'     (while 'TBD' is refused)
    [... OXIDE ENTRIES PASS] measurements.V_real = 'unknown.'   (while 'unknown' is refused)
    [... OXIDE ENTRIES PASS] measurements.V_real = 'to be supplied'   (also 'pending', 'yes.')
    [REFUSED] 'N/A', 'none', 'TBD', 'measured', '  '

So a comparison run can still carry an unmeasured model value (the IAM V_ox, stated as such in
the record itself) labelled "PROJECT_INPUT item 12 (...; measured: not measured: ...)". This is
the substance of A9b-M2. X5 section 1 claims "placeholders refused"; the test
(`test_measurement_record_for_project_input_model_parameters`) checks only 'measured', '  ' and
'TBD'. The gate cannot verify a statement, but it can refuse what is obviously not one.

Fix needed: a structured measurement record (e.g. {quantity, method, instrument_or_reference,
value, uncertainty}, each non-empty and not a placeholder after stripping punctuation), refusal
of records containing "not measured"/"model"/"assumption"/a row id, and tests of the
punctuation variants.

### A10b-m1 (minor). The a-Si potentials remain model values that a comparison run admits only as PROJECT_INPUT, without any measurement record

D2: `a-Si 5 A, V_a 12.0 V / V'_a 0.5 V labelled PROJECT_INPUT, no measurement record,
comparison` -> OXIDE ENTRIES PASS. A measurement record for them is refused
(`exactly the model parameters labelled PROJECT_INPUT ([]) carry a measurement record, got
['amorphous_si_potential']`), and B43 is refused on them (D1). So for V_a and V'_a the A9b-M2
loophole is unchanged: the only admissible label in a comparison run is PROJECT_INPUT, with no
way even to attach a statement. X5 section 9 and row B43 ("The a-Si potentials remain
PROJECT_INPUT-only in comparison runs") state it, so it is recorded, not hidden. Fix: extend
OXIDE_MODEL_PARAMETERS (measurement record) to `amorphous_si_potential`, or refuse t_a > 0 in
comparison runs until a model row for a-Si exists.

### A10b-m2 (minor). docs/06 asks Ali to state the uncertainty convention; the configuration has no field for it and the code silently treats every value as an interval half-width

docs/06 item 12: "the uncertainty of each (one standard uncertainty or an interval half-width,
stated which)". `oxide_spec_from_config` refuses any extra key (D1: `uncertainty_convention`
-> REFUSED, unknown key), and `consumed_count_interval` (`oxide.py:441-477`) always uses the box
(t -+ u_t, rho -+ u_rho). A one-sigma value is thereby read as a half-width: the count interval
then covers roughly a one-sigma box only, and a count that looks robust can flip within two
sigma. Fix: a required `uncertainty_convention` key (enumerated), with a coverage factor applied
for a standard uncertainty (or refuse standard uncertainties), recorded in `oxide_item12`.

### A10b-n1 (note). The A9b-M1 cell guard keys on thickness only: a non-conformal atomistic cell with one thickness and two counts is built without refusal or record

`forward/cell.py:249-252` returns None when all per-terrace thicknesses are equal, although
`terrace_stacks` calls the layer non-conformal when the COUNTS differ (`oxide.py:626-627`). At the
rounding tie (depth within 1e-9 A, `_TOL_A`, of (N + 1/2) a/4, with the rounding acknowledgement)
both counts pass the nearest-count assertion. D3 (`SP/a10b/d3_m1_edge.py`):

    t at the 6.5-layer tie: 19.988820254914156 A
    [structure built] one thickness (tie), counts (6, 7): conformal False; ... sublayer -3.0752031161406395 ...
          note: sub-layer thickness difference Dt - DN (a/4)/f = +0.0000 - (+1) x 3.0752 = -3.0752 A: its grown-oxide term is applied by the geometric engine but not represented by a multislice ...
       [CELL BUILT] nonconformal_sublayer record present: False; layout conformal: False
    [REFUSED at spec/structure] ... nonconformal ack True: ... the terraces carry one thickness: the acknowledgement is not needed

The builder's step record states a disagreement (about 11.0 rad, i.e. about 1.5 rad mod 2 pi on
the 1-D model), the cell is built unrefused and unrecorded, and the acknowledgement is refused.
Reachable only at engine level (the pipeline refuses overrides) inside a 2e-9 A thickness
window, so a note. Fix: key the guard on `record["conformal"]` (thickness OR count), and let the
spec accept the acknowledgement for differing counts. Related: `si001.py:900-901` compares
thicknesses with exact `==`, `terrace_stacks` with `round(., 12)` (D3: 20.0 vs 20.0 + 1e-13 gives
`conformal True` in the record and `conformal_at_step False` with a 0.0000 A sub-layer note).

### Confirmed so far

* Geometric engine unchanged: `forward/geometric/model.py` differs only inside the module
  docstring (diff read); D4 (`SP/a10b/d4_bitid.py oxide_2p0nm`, 4.8 s) at 00851da: `vs a9b/pipe:
  arrays 26 vs 26; bitwise identical 26`; `vs x5/pipe: ... 26`; `vs a8: ... 26` (A8's run of
  E4's pre-fix code). Heights +2.7153 +- 0.0165, -1.3578 +- 0.0082, -1.3575 +- 0.0082 A. The
  manifest and summary carry the same `oxide_item12` (headline "mixed (ASSUMPTION B41,
  DERIVED_HERE)", no model rows, no uncertainties).
* `scripts/` unchanged in 62ced11..00851da (`git diff --stat` empty; `git log` of
  scripts/hpc/alliance empty in the range).
* Sizing tool: committed output differs from 62ced11 only in the git/load line, the
  load-dependent CPU observation (753 -> 531 s) and the relabelled oxide texts; 3.162, 7.731 and
  7.438 GB present in the same 6 lines before and after.
