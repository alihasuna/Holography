# E2 - Si(001) reconstructions, reconstructed steps and the sourced thermal displacement

Agent E2, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`. Status: IN PROGRESS
(written incrementally; sections 1-4 final, section 5 filled as the runs finish). Nothing committed
or pushed by E2 (the orchestrator's snapshot commits 7e80d33 and 9c9613d picked up in-progress
copies). No file under docs/ other than this report is edited;
`reflection_holo/forward/multislice/potentials.py` (agent E1) is read only.

Inputs read: L7 sections 1.1-1.4, 5, 6 (Ramstad, Brocks and Kelly 1995 [R1] Tables III-IV as
transcribed in 1.4; Zandvliet 2000 [R2]; Horio 2014 [R3]; Shirasawa et al. 2006 [R4]); L6 sections 2
and 7.1 (Heacock et al. 2021); E6 in full (sections 8 and 9, minor findings m2 and m3);
`reflection_holo/structure/` (si001.py, lattice.py, checks.py, features.py),
`reflection_holo/forward/multislice/potentials.py` (FrozenPhonons, AtomicPotential, _RealisedAtomic),
`reflection_holo/pipeline/config.py` and `engines.py`, `reflection_holo/io/assumption_registry.yaml`,
`docs/model_assumptions.md` (A7, B3, B4), docs/05 section 4.2, tests/structure, tests/io.

## 0. Log

* 2026-09-24: design (section 1) fixed before coding.
* 2026-09-24: implemented `reflection_holo/structure/reconstruction.py` (R1 tables, frame, dimer
  cells, flip-flop states, measurements), wired into `si001.py` (options, assertions (r1)-(r6));
  `structure/thermal.py` (B35); `forward/dimer_ensemble.py` (B37 wrapper, potentials.py
  untouched); pipeline gate and engines (item 23, terminations); registry B35-B37; feature builder
  refusal. First scan over 560 staircase builds (5 terminations x 7 staircases x 2 edge
  orientations x 4 azimuths x 2 terrace types): all build except c(4x2) on joined terraces whose
  period is not a c(4x2) lattice vector (refused with ReconstructionError, by design). Terrace
  interiors reproduce the source geometry exactly (minimum distance = the table's dimer bond);
  bonds across risers are compressed by at most 5.5 % of d_nn (2.176 A, p(2x2)), an artefact of
  "step-riser relaxation none" (section 1.4).
* 2026-09-24: measured B4 relation for reconstructed steps added (`reconstruction.
  reconstruction_relation`, `si001._b4_reconstructed`); new tests
  `tests/structure/test_si001_reconstruction.py`, `tests/structure/test_thermal.py`,
  `tests/pipeline/test_e2_thermal_reconstruction.py`. Concurrent edits by E3 to
  `pipeline/config.py`, `pipeline/run.py`, the registry and the demo configs were made on disk on top
  of mine (E3 added B38-B40 after B36 in the registry and in tests/io); one E2 test run failed
  transiently while E3's config keys and code were half-written (section 5).

## 1. Task 1: Si(001) reconstructions (R1 Tables III-IV)

Code: `reflection_holo/structure/reconstruction.py` (new), `reflection_holo/structure/si001.py`
(`_termination_option` l. 432, `_assert_reconstruction` l. 536, builder hook l. 835).

* Tables: `_TABLE_III` (l. 100) and `_TABLE_IV` (l. 113) are L7 1.4 verbatim (160 entries);
  `test_tables_equal_the_L7_transcription_entry_by_entry` re-parses L7 1.4 and compares every entry.
* Frame (DERIVED_HERE, module docstring): R1's layer-2 atoms sit one R1 unit along y from the top
  atoms, so R1 y (dimer row) = the top layer's back-bond axis and R1 x (dimer bond) = the other
  <110>; sign convention: R1 x has a positive crystal-x component on every terrace (so terraces of
  one orientation have the same buckling orientation); R1 y = [001] x R1 x. Every R1 (k, l, m) is a
  diamond site in this map for both layer parities (test). The frame is verified on the atoms: a
  swapped frame makes the builder fail (`test_builder_assertions_catch_a_wrong_frame`).
* Options (`TERMINATIONS`): `bulk` (ASSUMPTION B3), `p(2x1)s`, `p(2x1)a`, `p(2x2)`, `c(4x2)`
  (SECTION_READ geometry; T = 0 LDA, its use for the specimen is an ASSUMPTION under B3), and
  `p(2x1)a flip-flop ensemble` (ASSUMPTION B37, "a MODEL CHOICE and not a source" in the label and
  docstrings). `dimer_2x1` is refused as ambiguous (NotImplementedError; the existing test's four
  required phrases are kept true). Under a declared overlayer a reconstruction is refused.
* Dimer cells and edges: each terrace is cut into R1's p(2x1) cells (one dimer + the 8 atoms of
  layers 2-5 of Table III). A cell is complete if both dimer atoms are top-layer atoms of the
  terrace (searched through the periodic boundaries; terraces 0 and n-1 of equal height are one
  terrace). Atoms of incomplete cells keep bulk sites: ASSUMPTION, an extension of "step-riser
  relaxation none" (R1 has no geometry for an unpaired edge atom). At <110> with even widths all
  cells are complete; at <100> every step edge cuts dimer rows and the unpaired count is recorded
  per terrace (`unpaired_top_atoms_at_bulk_sites`). A cell length that is not a lattice vector of
  the pattern ((4,0),(0,2) p(2x1); (4,0),(0,4) p(2x2); (4,2),(0,4) c(4x2), R1 units) is refused.
* Assertions: (a)-(g) run unchanged on the ideal sites; then (r1) displacements only in the five
  tabulated layers of complete cells; (r2) composition and count unchanged; (r3) every dimer found
  geometrically on the atoms has the table's bond length and buckling (1e-6 A, 1e-6 deg), also in
  the all-reversed flip-flop state; (r4) one dimer axis per terrace, normal to its back-bond axis,
  rotated across every a/4 and not across a/2 steps; (r5) collisions (1.4); (r6) bulk interior
  below the reconstructed layers 4-coordinated at d_nn.

### 1.1 Dimer bond length and buckling recomputed from the built atoms (a = 5.4309 A)

Brute-force minimum-image search on the positions (test helper `dimers_from_atoms`, independent of
the builder's records), flat periodic terrace, [110]:

| termination | built: bond (A), buckling (deg) | R1 printed | E6 recomputed (a = 5.431) |
|---|---|---|---|
| p(2x1)s | 2.230226, 0.0 | 2.23 | 2.230 |
| p(2x1)a | 2.258090, 18.2727 | 2.26, 18.3 | 2.258, 18.27 |
| p(2x2) | 2.282810, 18.8618; 2.282982, 19.2586 | 2.28, 18.9 and 19.3 | 2.283/18.86, 2.283/19.26 |
| c(4x2) | 2.287202, 18.7183; 2.288214, 18.9478 | 2.29, 18.7 and 18.9 | 2.287/18.72, 2.288/18.95 |

Test tolerances (not chosen to pass; derived from the printed precisions): against R1, half a
printed unit (0.005 A, 0.05 deg) plus the first-order effect of R1's 0.001 A rounding of the four
tabulated displacements and of a = 5.4309 vs 5.431 A (`rounding_bound`: 0.0011-0.0013 A,
0.026-0.033 deg); against E6, half of E6's printed unit (0.0005 A, 0.005 deg) plus the lattice-
parameter effect (7.1e-5 A). The c(4x2) second dimer (18.9478 deg vs printed 18.9) is inside half a
printed unit on its own. The values quoted in the task (c(4x2) 2.287 A, 18.72 deg) are asserted
after rounding. c(4x2) rows are in antiphase and p(2x2) rows in phase, buckling alternating along
every row (test).

### 1.2 Room temperature: the flip-flop ensemble (ASSUMPTION B37, model choice)

Each complete cell takes the p(2x1)a state of Table III or its mirror image through the cell's
dimer-bond-normal mid-plane, d'(k, l, m) = diag(-1, 1, 1) d((2 - k) mod 4, l, m), with probability
1/2, independently (`ReconstructionRecord.positions_for`). The structure's positions are the
all-Table-III member (identical to the static p(2x1)a build, asserted); a run must draw every
realisation: `reflection_holo/forward/dimer_ensemble.py::DimerFlipFlopPotential` wraps the
unchanged AtomicPotential, draws the states from the engine's generator seeded with
[seed, realisation] BEFORE the frozen-phonon displacements, builds that realisation's cell and
calls `AtomicPotential.realise` on a view of it; the states (packed hex), their SHA-256, the
count reversed and the configuration hash are written to
`ExitWave.metadata["potential"]["realised"]["dimer_flip_flop"]`; the provenance carries the B37
label. It requires frozen phonons (the engine seeds a generator only then; room-temperature model).
Averages are taken after squaring by the pipeline's hologram stage, as for frozen phonons. Not
modelled: inter-dimer correlation (R4: 2-D Ising transition), relaxation of mixed neighbourhoods
(each subsurface atom follows its own cell), flip-flop time scale; R3's superposed-potential
alternative (L7 1.3 (b)) is not implemented.

### 1.3 B4 on reconstructed steps, measured (`reconstruction_relation`, `si001._b4_reconstructed`)

For every step, the operations of assertion (f) that fix the beam (identity for a/2 steps, the
incidence-plane mirrors for a/4 steps at <100>) are applied to the displaced atoms of one terrace
and compared with the other terrace's atoms of the same pattern class, allowing an in-plane shift
of the pattern (irrelevant for the specular beam); holds if the largest difference is <= 0.001 A
(R1's printed precision). Result (MIXED staircase, 4 edge periods):

| termination | a/2 step | a/4 step at [100] ((010) mirror) | a/4 step at [010] ((100) mirror) |
|---|---|---|---|
| p(2x1)s | holds (0.000 A) | holds (0.000) | holds (0.000) |
| p(2x1)a | holds (0.000) | holds (0.000) | FAILS (0.708 A = full buckling height) |
| p(2x2) | holds (0.000) | holds (0.001) | FAILS (0.022 A) |
| c(4x2) | holds (0.000) | holds (0.001) | FAILS (0.018 A) |
| flip-flop | ensemble only | ensemble only (0 -> 0, 1 -> 1) | ensemble only (0 -> 1, 1 -> 0) |

The [100]/[010] difference for the static buckled tables is a consequence of the fixed buckling
orientation (the sign convention above), i.e. of representing a buckled surface by one domain; the
flip-flop ensemble is mirror-invariant at both. At <110> the ideal-site statement (B4 does not
apply, open question 3) is kept. The geometric engine still refuses every non-bulk termination
(`forward/geometric/model.py::require_b4_scope`, unchanged); these statements are metadata for the
multislice runs (`steps[i].relation.model_assumption_B4`, `reconstruction_relations`).

### 1.4 Collisions at step edges

Rule (`reconstruction.assert_no_collision`): pairs with both atoms in complete cells of one terrace
reproduce R1's periodic geometry, so their minimum must equal the table's shortest distance (the
dimer bond; asserted exactly); every pair, in every configuration of the flip-flop ensemble (exact:
a pair distance depends only on the states of its two cells), must stay >= 0.9 d_nn = 2.1165 A, a
stated NUMERICAL criterion (a bond compressed by more than 10 %, 0.11 A below the shortest Si-Si
bond in R1's geometries, is refused as a collision); the repository's existing duplicate check
(assertion (b), 0.5 A) is also run on the displaced atoms. Measured over the 560-build scan: interior
minima = 2.230226 / 2.258090 / 2.282810 / 2.287202 A (the dimer bonds); riser/edge minima 2.2314
(p(2x1)s), 2.2086 (p(2x1)a), 2.1759 (p(2x2)), 2.1993 (c(4x2)), 2.2019 A (flip-flop, all
configurations), i.e. bonds across a riser compressed by up to 5.5 % of d_nn. These are compressed
bonds, not overlaps; they arise because each terrace carries its own table and the riser is not
relaxed (ASSUMPTION "step-riser relaxation none"), and are recorded per structure
(`riser_edge_pairs_shorter_than_table_shortest`, `riser_edge_largest_compression_of_dnn`).

## 2. Task 2: steps with reconstruction

* Staircase builder: done. The dimer-row direction follows each terrace's top-layer parity, so it
  rotates by 90 deg across every a/4 step (SA/SB) and not across a/2 steps (DB), measured on the
  atoms by (r4) and by `test_dimer_rows_rotate_across_a4_and_not_across_a2` (5 terminations x
  [110], [100]). Steps are labelled per Zandvliet (R2 p. 594) from the UPPER terrace's rows:
  SA/SB (a/4) and DA/DB (a/2) at <110>; at <100> the edge is 45 deg to the rows ("neither").
* Half-torus terraces (`structure/features.py`): REFUSED, not implemented now.
  `feature_termination_option` raises NotImplementedError for every reconstruction name with
  `FEATURE_RECONSTRUCTION_REFUSAL`: every terrace edge of the ring is a circle through all
  azimuths, so dimer cells are cut along every edge and in annuli narrower than a cell, and R1 has
  no geometry for unpaired edge atoms. The feature builder has no termination argument (its
  signature and tests unchanged); the pipeline's feature path refuses a non-bulk termination with
  the same text (`pipeline/engines.py::feature_height_field`, `config._check_termination`).

## 3. Task 3: sourced thermal displacement (B35) and specimen temperature (item 23)

`reflection_holo/structure/thermal.py`: B(T) = 0.4761 A^2 + 0.0014 A^2/K (T - 295.5 K) (Heacock et
al. 2021, arXiv:2103.05428v3 PDF p. 6 and p. 25, SECTION_READ in L6 2.2, confirmed by E6),
u = sqrt(B/(8 pi^2)) per axis (p. 3); u(295.5 K) = 0.077652 A, sigma 0.000139 A from the +-0.0017 A^2.
Validity range 273.15-323.15 K (0-50 deg C), refused outside: the curvature of B(T) is not in the
source; Einstein (Theta_E = 275.1 K) and Debye (Theta_D = 482.1 K) models matched to B and dB/dT at
295.5 K (model forms unsourced, used only to size the curvature) depart from the linear form by
<= 2.4e-4 A^2 in the range (one seventh of the stated 0.0017 A^2) and reach ~0.0017 A^2 only near
225 K and 375 K (reproduced in `test_validity_range_justification_numbers`). The specimen
temperature has no default: `frozen_phonon_arguments` refuses None, an unlabelled value and an
out-of-range value; the returned FrozenPhonons label starts "ASSUMPTION B35" and carries the
temperature's label. A7 is unchanged: `FrozenPhonons(rms_displacement_A=0.076, label="ASSUMPTION
A7 ...")` is accepted (test), and the pipeline's existing fixed-u form `{rms_displacement_A,
label}` still works for demo runs.

Pipeline (`pipeline/config.py`): `frozen_phonons` is `none`, `{model: si_heacock2021_linear_B}`
(B35; then `sections.engine.multislice.specimen_temperature`, a record with item 23 and unit K, is
REQUIRED: absent or null -> MissingProjectInputError naming item 23; out of range ->
PipelineConfigError), or the fixed-u form. A temperature given with `none` or fixed u is refused
rather than ignored; purpose "comparison" refuses the fixed-u form (item 23 not represented) and
the demo stand-in B36. `list_inputs` shows item 23 (used, or NOT USED with the reason).
`reflection_holo/io/config.py::N_PROJECT_INPUT_ITEMS` = 23. `pipeline/engines.py::
multislice_objects` builds FrozenPhonons from B35 and wraps the potential for the flip-flop
termination; the run record carries `thermal_model` and `termination`. Reconstructed terminations
are accepted only with the multislice engine on the staircase path; the flip-flop only with B35;
the stand-in B26 (bulk) cannot carry a reconstruction. New demo variant
`configs/demo_smoke_si001.yaml::multislice_tiny_thermal` (B35 at B36 = 295.5 K, 2 realisations,
seed 20260924, bulk termination).

## 4. Task 4: registry rows and proposed model_assumptions text

`reflection_holo/io/assumption_registry.yaml`: `stand_ins: B36: [23]`, B36 in `demo_only`; new key
`model_rows: {B35: ..., B37: ...}` (rows cited by code that stand in for NO docs/06 item; never
accepted as an assumption_id). Loader: `io/config.py::_registry_cached` accepts and validates
`model_rows`; `model_assumption_rows()`. tests/io: the expected registry has `"B36": (23,)` and
`model_assumption_rows() == {B35, B37}`; `test_registry_ids_exist_in_model_assumptions` now checks
the model rows too and FAILS until docs/model_assumptions.md has rows B35, B36 and B37 (it checks
that every registry id is the first cell of a `| ` row of that file; B36 is the first missing one
it reports). It is not weakened.

Proposed rows (orchestrator to paste into docs/model_assumptions.md section 2):

| B35 | Si thermal displacement of the frozen-phonon (Einstein) model: B(T) = 0.4761 A^2 + 0.0014 A^2/K (T - 295.5 K), u = sqrt(B/(8 pi^2)) per axis, u = 0.07765(14) A at 295.5 K. Heacock et al. 2021, arXiv:2103.05428v3: B = 0.4761(17) A^2 at 295.5 K (PDF p. 6), dB/dT = 0.0014 A^2/K at 295.5 K (PDF p. 25), <u^2> = B/(8 pi^2) (PDF p. 3); SECTION_READ (L6 section 2.2, confirmed by E6). The linear extrapolation is an ASSUMPTION accepted only for 273.15 K <= T <= 323.15 K (Einstein and Debye models matched to B and dB/dT at 295.5 K depart from it by <= 2.4e-4 A^2 there; report E2); other temperatures are refused. T is PROJECT_INPUT item 23 (no default). Code: `reflection_holo/structure/thermal.py`; pipeline `frozen_phonons: {model: si_heacock2021_linear_B}` with `specimen_temperature`. A7 (0.076 A, inherited) is unchanged. | SECTION_READ (B, dB/dT, convention); ASSUMPTION (linear extrapolation, Einstein model) | 10 K changes B by 2.94 % (u by 1.46 %). A7 is 4.2 % low in B (2.1 % in u); (008) Debye-Waller amplitude 0.7724 vs 0.7808 with A7 (L6 7.1). The Einstein model misses phonon correlations (Hajek and Rusz 2026: about 1e-3 I0 for diamond in transmission). |
| B36 | Demo specimen temperature 295.5 K (the reference temperature of B35's source). Stands in for PROJECT_INPUT item 23 in the demo configurations only (`configs/demo_smoke_si001.yaml`, variant `multislice_tiny_thermal`, purpose demo; a run with purpose "comparison" refuses it); not comparable to experiment. | ASSUMPTION | dB/dT = 0.0014 A^2/K: 10 K = 2.94 % in B, 1.46 % in u. |
| B37 | Room-temperature Si(001) represented as a p(2x1)a dimer flip-flop ensemble (MODEL CHOICE, NOT A SOURCE): every complete dimer cell of Ramstad et al. 1995 Table III [RAMSTAD1995] takes the p(2x1)a displacements or their mirror image (buckling reversed) with probability 1/2, independently, drawn per realisation from the engine's generator seeded with [seed, realisation] before the frozen-phonon displacements; intensities averaged after squaring. Motivation: the dimers flip-flop at room temperature and c(4x2) order appears only below 205 +- 3 K (Shirasawa et al. 2006 p. 865; L7 section 1.2). Not modelled: inter-dimer correlations (2-D Ising), relaxation of mixed neighbourhoods, flip-flop time scale. Requires frozen phonons (B35) and PROJECT_INPUT item 23. Code: `structure/reconstruction.py`, `forward/dimer_ensemble.py`. | ASSUMPTION | Unknown; a sensitivity test against the static p(2x1)a and c(4x2) options is NOT RUN. B4 holds for the ensemble average only (report E2 section 1.3). |

Suggested edits for the orchestrator (not made by E2): B3 "Implementation: report E2 (in
progress); until then every cell is bulk-terminated" -> "Implemented (report E2): options p(2x1)s,
p(2x1)a, p(2x2), c(4x2) and the flip-flop ensemble (B37) on the staircase builder; bulk remains the
default of every configuration; refused on the half-torus feature". B4: add the measured table of
section 1.3 (static buckled tables break the (100)-mirror relation at [010] by the fixed buckling
orientation; hold at [100]). docs/05:347-348: replace "The 2x1 reconstruction raises
NotImplementedError (no source read)" by "Si(001) reconstructions from R1 Tables III-IV are
options of the staircase builder (report E2); refused on the half-torus". docs/06: new item 23
"Specimen temperature during holography (K), with the method of measurement or estimate, including
beam heating; required by the frozen-phonon model B35 (valid 273.15-323.15 K)". An item-12
stand-in stating a clean reconstructed surface (for a demo file running the flip-flop through
`pipeline.run`) does not exist; B26 states bulk.

## 5. Tests and results

(filled below as the runs finish)
