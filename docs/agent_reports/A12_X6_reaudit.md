# A12 - Re-audit of X6 (fixes of re-audit A10b on the item-12 oxide label policy of comparison runs)

Auditor: agent A12, 2026-09-24. Status: FINAL (written incrementally).

Scope: repository /home/user/Holography, branch claude/electron-holography-orchestration-nakd7r,
commit 33fd484. The code, tests and tools are those of f009be8: 33fd484 changes only docs/ and
reports (`git show --stat 33fd484`). During the audit the orchestrator committed b7ba812 (A11) and
874c5cc (a snapshot of this report). `git diff --stat 33fd484 HEAD -- reflection_holo tests tools
configs scripts` is empty, and rows B7, B12 and B43 are unchanged (only B42 and the status line of
docs/model_assumptions.md changed).

Read in full:
* docs/agent_reports/A10b_X5_reaudit.md and docs/agent_reports/X6_a10b_fixes.md;
* `git diff b7dcbf0^..33fd484` (the X6 diffs b7dcbf0^..f009be8 plus 33fd484) of
  `structure/oxide.py`, `pipeline/config.py`, `forward/cell.py`, the oxide tests and the docs;
* the three new a10b test files and the migrated tests of X4 and X5;
* `tools/review/x6/`: `x6_oxide_numbers.py` with its output, `x6_demo_bitid.py` with its output, and
  `mutate_x6.py` with its output;
* rows B7, B12, B41 and B43 of docs/model_assumptions.md, and item 12 of
  docs/06_project_inputs_required.md;
* the item-12 part of `pipeline/config.py` (lines 1020-1735); `oxide.py` lines 100-940; the
  oxide use of `forward/geometric/model.py` (lines 240-360); and `forward/cell.py` lines 238-300.

Rules kept:
* This report is the only repository file I wrote. The code under audit was not modified;
  mutations were made in scratch copies only.
* Nothing was committed by me.
* Nothing was written under outputs/: `git status --short outputs/` and
  `find outputs -newer SP/a12/common.py -type f` were both empty after the last run.
* Scratch files are in SP/a12/, where SP =
  /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad.
* Every run was single-threaded (OMP_NUM_THREADS=1), because a full suite ran concurrently.

Grades:
* MAJOR: must be resolved before the policy is called final for comparison runs; a
  reproduction is given.
* minor.
* note.

## Verdict table (question 1)

| A10b finding (decision) | A12 verdict | reverting the fix makes a test fail? (A12 D4, own replacement texts) |
|---|---|---|
| M1 parity (lower/upper, DERIVED_HERE, thickness unaltered, other count a separate run) | FIXED as decided. A count outside the interval is refused, and so is a thickness override. The parity key is refused without uncertainties, off a boundary, and with a value other than lower or upper (D2). The count label carries the qualifier and the item-12 record carries the variant, the other variant and "SEPARATE run". Residual: the non-nearest variant's overlap, and the geometric engine gives the two variants byte-identical arrays (**A12-m3**) | yes: key missing builds the nearest count (Z1 = X6 Y1) 4 failed; pipeline accepts three counts (Z2 = Y8, config half only) 1 failed |
| ruling: intervals of more than two counts refused | IMPLEMENTED in the pipeline (`config.py:1482-1488`) and the structure (`oxide.py:728-735` in `_check_parity_variant`); the refusal comes before the key check | Z2 1 failed; X6 Y8, Y31 (not repeated) |
| M2 structured record with placeholder and negation refusal | PARTLY FIXED. The record is structured. Every text A10b listed is refused, as are invalid and future dates. But the next most natural negations, and plain statements that the value was not measured, pass. B7 and B43 overstate this as "refuses ... negations" (**A12-M1**). The dates and references can be empty in substance (**A12-m1**) | yes: negation patterns off (Z3 = Y15) 49 failed; "yet" dropped from the pattern (O4, own) 3 failed |
| m1 a-Si potentials | FIXED: `amorphous_si_potential` labelled PROJECT_INPUT needs the record (`config.py:1038`, `1281-1282`). In a comparison run no other label is admissible (B41 is a demo stand-in, B43 does not cover the a-Si potentials, TEST_ONLY is refused) | X6 Y21 (not repeated) |
| m2 uncertainty kind (standard as +-2u) | FIXED as decided (`oxide.py:128-137`, `593`; `config.py:1451-1457`). Residual: the corner box of k u per quantity is not a 95 % interval of the depth (**A12-m2**). The kind handed to the structure is not tested (**A12-n2**) | yes: k = 1 (Z4 = Y22) 10 failed; spec kind forced to half_width (O3, own): **0 failed** |
| m3 a-Si thickness uncertainty in the interval | FIXED: t_a -+ k u_a, with the lower end clipped at 0. Residual: no upper bound (**A12-n1**) | yes: a-Si uncertainty ignored (Z5 = Y24) 13 failed; lower end not clipped (O1, own) 11 failed |
| n2 zero or negative uncertainties refused | FIXED (both `item12_count_interval` and `_parity_variant`). No floor, as before (not in the decisions) | yes: nonneg instead of positive (Z6 = Y26) 17 failed |
| n1 cell guard also on different counts at one thickness | FIXED (`cell.py:251-254`, `oxide.py:428-440`) | yes: guard counts ignored (Z7 = Y27) 2 failed |
| decision 6 texts | Code: FIXED; a test scans `reflection_holo/**/*.py`. Docs: see question 5 | X6 Y29 (not repeated) |
| (own) spec hash covers the variant mapping | the lower and upper specs hash differently | yes: hash drops the variant (O2, own) 1 failed |

D4 control: 318 passed (6 test files: the three a10b files, X5's pipeline and structure a9b files,
and `test_oxide_pipeline_a8_fixes.py`). Every mutated copy imported its own package: the printed
`reflection_holo/__init__.py` lies in `SP/a12/mut/<name>/`. I reproduced 7 of X6's 31 reversions
with my own replacement texts (Z1-Z7), and added 4 of my own (O1-O4). Every one except O3 makes a
test fail.

X6's saved `mutate_x6_output.txt` lists 31 reversions and a control, and every reversion fails at
least one test (read). I did not rerun `mutate_x6.py` itself.

## Findings

### MAJOR

**A12-M1. The measurement record still passes the most natural negations after "not measured",
and plain statements that the value was not measured. So a comparison run can still label an
unmeasured model value PROJECT_INPUT. Rows B7 and B43 say that the gate "refuses ... negations".**

`pipeline/config.py:1046-1055` (`_MEASUREMENT_REFUSED`) is an English denylist of fixed phrases:
* "not" + at most ONE of "yet"/"been" + a participle;
* "never measured" (adjacent words only);
* "no" + a singular noun;
* the prefix "un" + six stems.

`_measurement_text` (`config.py:1222-1248`) applies it after an ASCII-only alphanumeric count.

D1 (`SP/a12/d1_records.py`, output `d1_records.out`): V_real is labelled PROJECT_INPUT, the other
model parameters B43, and one field of an otherwise valid record is varied. Each text below is
ACCEPTED in the method field and in the reference field:

    not yet been measured | has not yet been measured | never been measured | no measurements |
    no measurements available | no measurements made | wasn't measured | was not actually measured |
    not-measured | not_measured | notmeasured | un-measured | non-measured | measured: no |
    measured - no | missing | absent | undefined | NaN | FIXME | fill in later | later | abc | test
    estimated | estimate | guess | educated guess | typical value | textbook value |
    handbook value (CRC) | Wikipedia | taken from a paper | extrapolated | fitted | DFT |
    density functional theory | ab initio | first principles | computed | derived | DERIVED_HERE |
    ESTIMATE | TEST_ONLY | Doyle-Turner scattering factors | Weickenmeier-Kohl |
    tools/review/e9_recompute_output.txt line 166 | E9 out:166 | row B-43 | row B 43 |
    copied from the demo configuration | demo value

With purpose "comparison" (D1 section C: item-12 uncertainties as half-widths, parity upper, count
7), the gate refuses only the demo's OTHER stand-ins and names no oxide entry. The records
checked were:
* {estimated, the usual one, 2026-09-20, "ref:"};
* {guess, abc, 0001-01-01, "doi:"};
* {"not yet been measured", "nicht gemessen", 1900-01-01, "n<Cyrillic o>t measured"};
* {"Doyle-Turner scattering factors", DFT, 2026-09-01, "tools/review/e9_recompute_output.txt
  line 166"}.

In the same configuration with purpose demo, the spec label reads:

    PROJECT_INPUT item 12 (TEST: fabricated supply (audit A12); measured: method not yet been measured;
    instrument nicht gemessen; date 1900-01-01; reference nоt measured)

Negative control (D2): 'not measured' in a comparison run is refused, and the error names
`overlayer.measurements ... V_real.method`.

Why it matters:
* A10b-M2 was graded MAJOR because an honest non-measurement statement ("not measured: ...")
  became a PROJECT_INPUT label in a comparison run. The same class still passes with the phrases
  a user is most likely to write next: "never been measured", "not yet been measured", "no
  measurements", or the method "estimated", "DFT" or "Doyle-Turner scattering factors" (the last
  is the origin of the B43 IAM value itself).
* The words "model", "IAM" and "independent-atom" are refused, but the scattering-factor names,
  "DFT", "ab initio", "computed", "derived" and a path to the review output that holds the IAM
  value are not.
* B7: "the gate refuses placeholders, negations, model and row references and future dates". B43:
  "The gate refuses placeholders, negations ('not measured'), 'model', 'assumption',
  'independent-atom', row ids, bare values and future dates". Both overstate the negation and row
  refusal: 'row B-43' and 'row B 43' pass. X6 section 2 says the patterns "fail closed"; they fail
  closed only for the listed phrases.
* "The simulation requires such a record but cannot verify it" (docs/06) is TRUE. The record is
  required whenever the label is PROJECT_INPUT, whatever the purpose, and in a comparison run
  PROJECT_INPUT is the only admissible label for a measured value.

The gate cannot verify a record, and a determined user can defeat any list. The finding concerns
accidental, honest text, which is what A10b-M2 was about.

Fix needed (small):
* (a) Replace the denylist for `method` with an allowlist: the method must name a measurement
  technique from an enumerated list (for example XRR, XPS, TEM/STEM, EELS, ellipsometry, off-axis
  electron holography, RHEED, AFM), or be refused. Keep the negation refusal as a second line,
  generalised: refuse any negation token (not, never, no, non-, n't, un-, without) within a few
  words of "measur", in any word order.
* (b) Refuse the origin words of model values in every field: estimat*, guess, typical, textbook,
  handbook, DFT, ab initio, first principles, comput*, deriv*, scattering factor*, Doyle-Turner,
  Weickenmeier, Lobato, Kirkland, tools/review, E<digits> report ids, and "B[-\s]?\d".
* (c) Test the texts above.
* (d) In B7 and B43, say "refuses the listed placeholder and negation phrases" rather than
  "negations".

### minor

**A12-m1. Dates, references and other languages: a record that is empty in substance passes.**

D1 sections A and B, all ACCEPTED:
* dates: 0001-01-01 (as a string and as a YAML date), 1000-01-01, 1900-01-01 and 1970-01-01.
  `_measurement_date` (`config.py:1251-1270`) has an upper bound only.
* a measurement date after the item-12 record's own `supplied_on`: 2026-09-25 against 2026-09-24.
  The supply cannot contain a later measurement.
* references that look real but are empty: "ref:", "Ref. ", "doi:", "doi:10.", "http://",
  "file:///", "#123", "No. 1", "ref [1]", "lab book p.", "internal", "see notebook", "same as
  above", "as above".
* echoes of the field names: "method", "instrument", "reference", "record". The three-character
  minimum admits all of these.
* other languages: "nicht gemessen", "non mesuré", "no medido", "non misurato", "niet gemeten" and
  "sans mesure". Text written wholly in a non-Latin script is refused, but only because the minimum
  counts ASCII letters and digits ('未測定', 'не измерено').

Fix needed:
* a lower date bound (for example not before the witness piece was prepared, or a stated floor)
  and not after the item-12 `supplied_on`;
* a reference form (a DOI with a suffix, a URL with a host, or a record id with at least N
  characters besides "ref"/"doi"/"http");
* refusal of the field names as values;
* either an ASCII/English-only rule stated in docs/06, or the allowlist of A12-M1 (a), which
  covers the languages as well.

**A12-m2. For standard uncertainties the count interval is not the "about 95 %" interval its
record states. Together with the ruling that refuses more than two counts, it refuses records
that a 95 % interval of the depth would admit.**

`item12_count_interval` (`oxide.py:573-634`) takes each quantity at +- k u, with k = 2, and the
depth at the two box corners. So the half-widths add linearly. The record's `coverage` field, the
docstrings and docs/06 attach "about 95 % coverage for a normally distributed quantity" to the
interval. That holds per quantity, but not for the depth (and hence the count) whose interval
this is.

D3 part 3 (`SP/a12/d3_interval.py`, no package import) assumes independent normal errors:

    t 20.0 +- 1.0, rho +- 0.05, a-Si 0 +- 0.1 (standard): box 5.587-7.626 -> [6, 7, 8];
        nominal +- 2 sigma_RSS 5.774-7.233 -> [6, 7]; box half-range / sigma_RSS = 2.80 (99.48 %)
    t 20.0 +- 0.1, rho +- 0.01, a-Si 0 +- 0.1 (standard): box half-range = 2.31 sigma (97.89 %)
    t 15.0 +- 1.0, rho +- 0.05, a-Si 0 +- 0.1 (standard): 2.69 sigma (99.29 %)

In the first case, the most plausible witness record in X6's own list, the box gives three counts
and the run is refused. A 95 % interval of the depth gives [6, 7], two parity variants.

For half-widths the linear box is the exact range and is correct.

Fix needed, an orchestrator decision: for "standard", either combine in quadrature (U = 2 sqrt(sum
(c_i u_i)^2), with the a-Si term one-sided), or keep the box and state in the record, docs/06 and B7
that the count interval is a conservative box, 97.9-99.6 % for these cases, not a 95 % interval.

**A12-m3. The parity variant that is not the nearest count builds an unphysical double occupancy
of up to 1.5 a/4 = 2.0366 A, whose effect is not computed. In the geometric engine the two
variants give byte-identical arrays.**

What the code does:
* The thickness is not altered (the decision), so the lower variant at 2.0 nm leaves the
  continuum oxide overlapping the kept crystal by +0.6838 A. The continuum interface then lies
  0.0049 A below the kept top atomic plane (+0.6838 - a/8 = +0.6838 - 0.6789), so the graded
  SiO2 potential and the top Si layer occupy the same region.
* At the bound (depth close to N + 1.5 layers), a whole Si layer lies inside the oxide.
* X6 (section 9) and B12 ("an effect not computed") state this. A9b's C3 estimate covers only the
  0.674 A GAP of the nearest variant.

D6 and D7 (`SP/a12/d6_variants.py`, `d7_ms_variants.py`; measured labels, fabricated TEST supply,
half-width uncertainties giving [6, 7], purpose demo, outputs in `SP/a12/pipe/`):

    geometric oxide_2p0nm      lower (6) vs upper (7): 26 arrays; byte-identical 26
                               (steps +2.7153 / -1.3578 / -1.3575 A in both)
    multislice_tiny_oxide_2p0nm lower vs upper: byte-identical 5 of 26; exit_psi_r0 max |diff|
                               0.795 (max |psi| 0.619); exit_x_A shifted by 1.355 A
                               (the kept crystal is one layer lower)

So:
* In the geometric engine the variant changes only the labels. The phase terms use the
  continuum boundaries (`oxide.stack_phase_terms`, `oxide.py:914-938`), and the geometric engine
  refuses buried a/4 steps at <110> anyway (`model.py:271-281`). There, docs/06's "a result is not
  quoted before both runs are compared" is satisfied trivially.
* In the multislice engine the variants differ. The difference mixes the parity effect with the
  uncomputed overlap artefact of the lower variant: +0.68 A here, up to 2.04 A in general.
* I compared the pointwise arrays only. The multislice arrays are shifted by one layer, so these
  differences are not a size of the parity effect.

Fix needed:
* before a variant result is quoted, a 1-D estimate like A9b C3 of the overlap at +0.6838 A and
  at 2.0366 A (or cap the admissible overlap of a non-nearest variant);
* one sentence in docs/06 and B12 that only the multislice engine distinguishes the variants;
* the stale comment at `forward/cell.py:286-288` ("which the layer overlaps or misses by at most
  a/8") also needs correcting.

### note

* **A12-n1. The a-Si thickness uncertainty has no upper bound.**
  * The thickness and density half-widths must stay below their values, but the a-Si half-width
    is limited only to finite values. `_depth_counts` then builds `list(range(n_lo, n_hi + 1))`.
  * D2 (e), in a subprocess with a 1.5 GB address-space limit: u_a = 1e9 A gives MemoryError, and
    1e300 gives OverflowError.
  * Neither is a ValueError, so at pipeline level 1e300 escapes as an UNCAUGHT OverflowError
    (D2b), not a PipelineConfigError.
  * Without a limit, u_a near 1e9 A asks for a list of about 7.4e8 integers (several GB) on a
    shared machine.
  * Fix: refuse k u_a above a stated bound (for example the oxide thickness), or refuse as soon
    as n_hi - n_lo > 2, without building the range.
* **A12-n2. Test gap: the kind handed to the structure is not tied to the stated kind.**
  * Mutation O3 forces `uncertainty_kind="half_width"` into the spec's parity-variant mapping
    (`config.py:1401-1404`), and all 318 tests pass.
  * With a standard kind, the structure's recorded interval (`consumed_layers_parity_record`) and
    the spec hash would then silently use k = 1, while the item-12 record states k = 2.
  * The code is correct today.
  * Fix: assert `spec.consumed_layers_parity_variant["uncertainty_kind"] == "standard"` in
    `test_standard_uncertainty_enters_twice`.
* **A12-n3. The exact-tie asymmetry (A10b-n2) is unchanged.** It is not in the decisions.
  * A lower corner exactly on 6.5 layers excludes 6. D3: t = 21.453676539912163 A with half-widths
    1 A, 0.05 g/cm^3 and 0.1 A gives min 6.5 and counts [7, 8], although the engine's tie rule
    admits 6.
  * An upper corner on N + 1/2 includes N + 1, because of floor(x + 0.5).
  * Both happen only at floating-point ties.
* **A12-n4. The engine-level qualifier check is a substring test.** A DERIVED_HERE count label
  that names BOTH qualifiers passes for the upper variant (D2b). The pipeline writes the label
  itself, so this is reachable at engine level only.
* **A12-n5. No floor on uncertainties** (A10b-n2, unchanged; not in the decisions). D2: 1e-12 for
  all three is accepted, and no variant is needed.
* **A12-n6. A detection limit is doubled when the kind is "standard".** docs/06 asks for the a-Si
  detection limit as its uncertainty, with "one kind for all". With "standard" the code doubles it
  (k = 2). This is conservative; state it in docs/06.
* **A12-n7. B12 overstates the overlap for both variants.** B12 says "No thickness is altered, so
  the layer then overlaps or misses the kept crystal by more than a/8". That holds for the
  non-nearest variant only. The nearest variant stays within a/8 (2.0 nm upper: -0.6739 A against
  a/8 = 0.6789 A).

## Question 2: loopholes (D1, D2, D2b)

| probe | result |
|---|---|
| comparison run builds a count outside the stated interval [6, 7] (5 lower, 8 upper, 6 upper, 7 lower, 8 or 6 without the key) | all REFUSED |
| thickness altered: `terrace_thickness_A`, `terrace_consumed_layers` | REFUSED (unknown keys). Thickness 19.5 with count 6 and parity lower: REFUSED (at 19.5 A the rounding acknowledgement is not needed). The gate cannot know the measured value; stating another one is a false supply, not a loophole of this gate |
| parity key without uncertainties (comparison; B41 record) | REFUSED ("without the item-12 uncertainties") |
| parity key or uncertainties under the B41 stand-ins | REFUSED ("stand-ins whose rows state no uncertainty") |
| parity null, 'Lower', ' lower', True, 6 | REFUSED (X6 tests; null in D2) |
| uncertainty True, '1.0', NaN, inf, 0, negative | REFUSED; 1e-12 accepted (A12-n5); a very large a-Si value crashes (A12-n1) |
| record placeholders in another spelling or language | many ACCEPTED (A12-M1, A12-m1) |
| Unicode look-alikes and invisible characters | ACCEPTED: 'n<Cyrillic o>t measured', 'not m<Cyrillic e>asured', 'not<U+200B>measured', 'not<U+00AD>measured', '<Cyrillic Te>BD later', '<Greek Beta>43 value', 'n0t measured', 'm0del value'. REFUSED: no-break and thin spaces (Python `\s` matches them) and fullwidth 'ＴＢＤ' (no ASCII letters). A deliberate evasion; NFKC normalisation, removal of Cf characters and refusal of mixed-script words would close it (part of the A12-M1 fix) |
| whitespace padding | '  measured  ', '\tTBD\n', ' not measured ', 'm e a s u r e d', '   ?   ' REFUSED; a padded genuine text is accepted and stored stripped |
| a real-looking but empty reference | ACCEPTED (A12-m1) |
| date 0001-01-01 | ACCEPTED (A12-m1); 0000-01-01 and 2026-02-29 refused |
| demo run affected by the new keys | No. The B41 variants state none of them. Uncertainties or the parity key under B41 are refused, and so is a record for a B41 parameter. `measurements: {}` is accepted and changes nothing. The arrays are byte-identical (question 4). The manifest's item-12 record gains `consumed_layers` and `measurement_rule`, and every earlier key is equal |

## Question 3: the interval arithmetic

D3 part 1 works from first principles, with no package import: f = (rho N_A / M_SiO2)(a^3/8),
a = 5.4309 A.

    f(2.20) = 0.441507; a/4 = 1.357725 A
    layer per A of oxide = 0.3252; per A of a-Si = 0.7365; +-0.05 g/cm^3 at 20 A = 0.1478 layer; ratio 2.26
    erf(2/sqrt2) = 95.45 %
    2.0 nm: lower (6) +0.6838 A = +0.5036 layer; upper (7) -0.6739 A; a/8 = 0.6789; 1.5 a/4 = 2.0366
    tie thickness 19.988820 A; (a/4)/f = 3.0752 A; x 3.58, 3.61 rad/A = 11.01-11.10 rad

* All 14 printed interval cases, computed independently, give the same counts as the code. The
  largest difference in layers is 1.78e-15. The layer ranges equal the committed output to the
  printed digits.
* Signs and corners are correct: the depth increases with t, rho and t_a, the a-Si lower end is
  clipped at 0, and "standard" doubles each u (box [19.8, 20.2] A and a-Si [0.0, 0.2] A, asserted
  by X6's test).
* Boundaries exactly at a half-integer: A12-n3. The lower tie was reproduced through the public
  function; the upper tie follows from floor(x + 0.5) (`_depth_counts` at 7.500000000000001 ->
  [6, 7, 8], D3c).
* The refusal of more than two counts:
  * it is applied in both layers, before the parity key is examined;
  * it names the depth half-width of each quantity;
  * it is refused with and without the key (X6 test; Z2).
* The 1.5 a/4 bound of the overlap for two counts is correct:
  * If the nearest count is N + 1, the nominal depth d satisfies (N + 1/2) q <= d <= hi, and
    hi < (N + 3/2) q, so d - N q < 1.5 q.
  * The upper variant is symmetric.
* The coverage of the combined box: A12-m2.

## Question 4: the B41 demo path is bitwise unchanged

D5 (`SP/a12/d5_bitid.py oxide_2p0nm`; my own script, not X6's; output in `SP/a12/pipe/`, 4.0 s):

    vs A10b: 26 vs 26 arrays; byte-identical 26      (A10b's run of the code at 00851da)
       example array 'exit_psi_r0': shape (1031, 128) dtype complex128; max |diff| 0.0
    vs X6:   26 vs 26 arrays; byte-identical 26
    vs A9b:  26 vs 26 arrays; byte-identical 26
    item-12 labels equal A10b: True; headline: mixed (ASSUMPTION B41, DERIVED_HERE); ...
    keys added: ['consumed_layers', 'measurement_rule']; removed: []; every earlier key equal: True
    consumed_layers: {'count': 7, ..., 'parity_variant': None, 'note': 'no parity variant: no item-12 uncertainties stated'}
    spec_sha256 equal A10b: True 094102edc907

The multislice demo was not rerun by me (X6's saved output: 26/26 against A10b and A9b).

## Question 5: rows B7, B12, B43 and docs/06 item 12

Rerunning `tools/review/x6/x6_oxide_numbers.py` at HEAD reproduces its committed output byte for
byte (D8).

| quoted (where) | printed by | verdict |
|---|---|---|
| 0.3252 layer per A of oxide, 0.1478 layer per 0.05 g/cm^3, 0.7365 layer per A of a-Si (docs/06) | x6 output, section "A10b m3" | OK (D3 recomputes them) |
| "+- 2 standard uncertainties (about 95 % coverage for a normally distributed quantity)" (docs/06, B7) | x6 output: 95.45 % | OK per quantity. The count interval is not a 95 % interval (A12-m2) |
| 1.5 a/4 = 2.0366 A, lower variant +0.6838 A (B12) | x6 output, first line and section "A10b M1" | OK. "overlaps or misses ... by more than a/8" holds for the non-nearest variant only (A12-n7) |
| (a/4)/f = 3.0752 A (B12) | x6 output, section "A10b n1" | OK |
| "each simulation run builds one of them ... records that the other count is a separate run, and leaves the thickness unaltered. The code does not check that the other run was made" (docs/06; also B7, B12) | code (D2 section g: `other_variant_run`, `thickness_altered: False`) | OK, not overstated. In the geometric engine the two runs are identical (A12-m3) |
| "When the uncertainties admit more than two counts, the run is refused" (docs/06, B7, B12) | code | OK |
| "The simulation requires such a record but cannot verify it" (docs/06) | code | TRUE everywhere: required for every PROJECT_INPUT label of V_ox, V'_ox, w_v, w_i and the a-Si potentials in any run; in a comparison run no other label is admissible for a measured value |
| "the gate refuses placeholders, negations, model and row references and future dates, but cannot verify a record" (B7); "refuses placeholders, negations ('not measured'), 'model', 'assumption', 'independent-atom', row ids, bare values and future dates" (B43) | code | **overstated** for negations and row ids (A12-M1). The rest holds for the listed forms |
| "B43 does not cover the a-Si potentials: in a comparison run they are PROJECT_INPUT with the same measurement record" (B43); "a comparison run with amorphous Si needs its record" (docs/06) | code | OK |
| "(for a measured absence: the detection limit)" with "one kind for all" (docs/06) | code | OK. Doubled when the kind is standard (A12-n6) |

## Test runs

    D4 control (scratch copy, 6 files: three a10b files, X5's pipeline and structure a9b files,
       test_oxide_pipeline_a8_fixes.py): 318 passed in 9.68s

The full suite was NOT RUN by me; it was running concurrently (the orchestrator's run).

## Command log

PY = `OMP_NUM_THREADS=1 PYTHONPATH=. venv/bin/python` from /home/user/Holography. Scripts and
outputs are in SP/a12/.

| # | command | purpose | result |
|---|---|---|---|
| C0 | `git log`, `git status`, `git rev-parse HEAD`, `git show --stat 33fd484 f009be8 b7dcbf0`, `git diff --stat b7dcbf0^..33fd484`, `git diff b7dcbf0^..33fd484 -- <oxide.py, cell.py, config.py, docs>`, later `git diff --stat 33fd484 HEAD`, `git diff 33fd484 HEAD -- docs/model_assumptions.md`, `git log -- docs/agent_reports/A12_X6_reaudit.md` | scope | code unchanged since f009be8; 874c5cc = the orchestrator's snapshot of this report |
| D1 | `PY SP/a12/d1_records.py > d1_records.out` | record loopholes | exit 0, 1.3 s |
| D2 | `PY SP/a12/d2_parity.py > d2_parity.out` | parity and uncertainty loopholes; the 1.5 GB-limited subprocess | exit 0 |
| D2b | `PY SP/a12/d2b_extra.py > d2b_extra.out` | follow-ups (19.5 A, OverflowError, label with both qualifiers) | exit 0 |
| D3 | `OMP_NUM_THREADS=1 venv/bin/python SP/a12/d3_interval.py > d3_interval.out` | interval arithmetic | exit 0. The upper-tie search printed "not found", so I wrote two further scripts |
| D3b | `venv/bin/python SP/a12/d3b_uppertie.py` (two versions) | exact upper tie through the public function | both FAILED (my scripts: no float input reaches 7.5 exactly; TypeError on None). Replaced by D3c |
| D3c | `PY -c "... ox._depth_counts(...)" > d3c_ties.out` | the ties through the private helper | exit 0 |
| D4 | `venv/bin/python SP/a12/d4_mutate.py > d4_mutate.out` (background) | mutations Z0-Z7, O1-O4 | control 318 passed; all caught except O3 |
| D5 | `OMP/OPENBLAS=1 PY SP/a12/d5_bitid.py oxide_2p0nm > d5_bitid.out` | B41 bit-identity | 26/26 vs A10b, X6, A9b |
| D6 | `PY SP/a12/d6_variants.py > d6_variants.out` | both variants, geometric | 26/26 identical |
| D7 | `PY SP/a12/d7_ms_variants.py > d7_ms_variants.out` (background) | both variants, multislice tiny | 5/26 identical; 17.0 s and 13.9 s |
| D8 | `PY tools/review/x6/x6_oxide_numbers.py > SP/a12/d8_x6_numbers.out; diff` against the committed output | numbers | IDENTICAL |
| D9 | `git status --short outputs/`; `find outputs -newer SP/a12/common.py -type f` | nothing written | empty, empty |

Read-only commands, not listed one by one: `grep`, `sed -n`, `cat`, `ls`, `/proc/loadavg`.

## NOT RUN

* The full test suite (it was running concurrently; not my run).
* `tools/review/x6/mutate_x6.py` and `x6_demo_bitid.py` themselves. I read their saved outputs and
  reproduced 7 reversions and one bit-identity comparison with my own scripts. X6's other 24
  reversions were not repeated.
* The multislice demo bit-identity (`multislice_tiny_oxide_2p0nm` against A10b); only the
  geometric demo was compared.
* Any estimate of the physical effect of the lower variant's overlap (+0.6838 A; bound 2.0366 A)
  on |r| or the phase. D7 shows only that the multislice arrays differ.
* A comparison run with a real item-12 record (none exists). All comparison probes are in-memory
  with fabricated TEST supply and records, and each is refused for the demo's other stand-ins.
* The [110] multislice with the layer; the a-Si layer in propagation; cupy/GPU.

## Verdict

**The oxide label policy cannot yet be called final for comparison runs, because of one MAJOR
residual of A10b-M2 (A12-M1).**

Final and correct:
* The parity-variant mechanism (A10b-M1) as decided, including the ruling that refuses more than
  two counts. No count outside the interval, no thickness change and no parity key without
  uncertainties can pass.
* The uncertainty kind (m2) with k = 2; the a-Si uncertainty in the interval (m3); the refusal of
  zero and negative uncertainties (n2); the cell guard on counts (n1); the record requirement for
  the a-Si potentials (m1).
* Each fix is guarded by tests. Seven X6 reversions reproduced with my own texts fail tests, and
  so do three of my own four mutations.
* The B41 demo path is byte-identical (26/26); the committed numbers reproduce, and each quoted
  number recomputes independently.

Before the policy is called final for comparison runs:
1. **A12-M1:**
   * tighten the measurement record: an allowlist of methods; a generalised negation refusal; the
     origin words of model values;
   * test the texts in A12-M1;
   * correct "refuses ... negations" in B7 and B43.
2. Minor, to be decided or fixed:
   * A12-m1: date floor and supply-date bound, reference form, field-name echoes, languages;
   * A12-m2: quadrature, or a coverage statement for the standard-uncertainty box, since it
     decides which realistic records are refused;
   * A12-m3: estimate the non-nearest variant's overlap before a variant result is quoted; state
     that only the multislice engine distinguishes the variants; correct the stale comment in
     `forward/cell.py`.
3. Notes n1-n7 when convenient. n1 (an uncaught OverflowError, and a memory hazard for a huge
   a-Si uncertainty) and n2 (the test gap found by O3) are one-line fixes.
