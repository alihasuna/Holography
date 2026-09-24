# X2: fixes of audit A6 (E1 engine wave 2a)

Agent X2, 2026-09-24. Written incrementally: finding -> fixed/declined -> file:line -> test ->
results verbatim -> NOT RUN. Scope: docs/agent_reports/A6_e1_audit.md applied to E1's work
(docs/agent_reports/E1_engine_wave2a.md) with the orchestrator's decisions. Nothing committed or
pushed. Base: HEAD b6e06bf (snapshot commits of X1/X2 in progress; X1 edits E2/E3 files in
parallel, which were not touched here). Machine shared (4 cores); load averages are quoted with
the runs. `<scratch>` = the session scratchpad (not in the repository).

Status: IN PROGRESS.

## Baseline taken before any edit

* A6's `study_points_fingerprint.py` (hashes of every built cell, atom set, beam, params, R and
  absorption, via the tree's own `run_study._build`) on study.yaml (17 points) and
  study_depth100.yaml (24 points) at b6e06bf: `<scratch>/x2/fp_before.txt`,
  `<scratch>/x2/fp100_before.txt` (24 s and 60 s).

## N-1 and N-3 (MAJOR): the sheet beam is a required input; study_depth100 lit to the exit plane

FIXED.

* `tests/forward/null_test_cases.py`: `translation_pair(*, theta, clean_depth_A, azimuth, H, edge,
  gap, ...)` and `step_case(..., H, edge, gap, ...)` have no default for the sheet beam any more
  (`_beam_inputs` refuses None, bool, non-finite or <= 0; SheetBeam asserts 2 edge <= H).
  `LEGACY_M2_BEAM = dict(H=8.0, edge=2.0, gap=2.0)` is the explicit legacy value.
  New `cell_length_z_A(theta, azimuth, gap, extra_A)` (the cell's L_z, independent of H) and
  `sheet_height_lit_to_exit_A(L_z_A, theta, gap)` = H2 2.6's `L_z tan(theta) - gap - a/2 - 1 A`,
  rounded down to 1e-3 A; `check_lit_to_exit(pair, exit_excl_A)` refuses a pair whose beam meets
  either crystal before `L_z - exit_excl_A`.
* `scripts/hpc/null_test_study/run_study.py`: `beam_height_A`, `beam_edge_A`, `beam_gap_A` are
  required keys of every point (POINT_KEYS; > 0 checked) and passed to both case functions; with a
  `surface_resolved` block every translation point is checked with `check_lit_to_exit` before it
  runs (also with `--estimate`); the estimate line names H and L_z. Docstring updated.
* `study.yaml`: every one of the 17 points carries `beam_height_A: 8.0, beam_edge_A: 2.0,
  beam_gap_A: 2.0` (the former silent defaults), header comment added; runtime block untouched.
  Byte identity verified with A6's `study_points_fingerprint.py` (every built cell incl. atom
  positions, species, box and layout, both beams, MultisliceParams, R, absorption) before any edit
  (b6e06bf) and after: `17/17 points identical in every build field`. The only other field of the
  fingerprint, the `check` diagnostic, changed on purpose (A6 n3 below): before `identical_sets:
  False` for all 11 pairs, after `identical_sets True, max_distance_A 2.38e-13` to `3.64e-12`.
* `study_depth100.yaml`: every point (translations AND steps) has `beam_edge_A: 2.0,
  beam_gap_A: 2.0` and `beam_height_A = L_z tan(theta) - gap - a/2 - 1 A` (16.499 A for L0,
  97.179/97.210 A for L5k, 177.860/177.833 A for L10k at [110]/[100], 75.048/75.067 A at 12 mrad,
  117.303/117.310 A at 20 mrad); the formula, L_z and why is in the header (the fixed-beam crystal A
  meets the top edge 62 A before the exit plane, the upper surface 230 A before it). The step points
  get the same beam so that their L5k/L10k lengths are lit; their read-out stays M2's x-summed one.
  Header status line: S-1 wording (below). `tests/forward/test_null_study_readout.py` recomputes
  every H of the file from the formula (exact equality).
* Callers updated with the legacy beam (signature only): `tests/forward/test_atomistic_translation.py`
  (`M2_CELL` includes `LEGACY_M2_BEAM`), `tools/hpc/review_h5_recompute.py` (H=8, edge=2, gap=2),
  `tools/hpc/supercell_sizing.py` (the study point's own three keys), and
  `scripts/hpc/alliance/gpu_check.py` (`**LEGACY_M2_BEAM`): this last edit is OUTSIDE K-1/K-2 in
  scripts/hpc/alliance/, but unavoidable once step_case has no default (the gpu-check test case
  would otherwise raise TypeError); it passes exactly the former defaults.

Proof on A6's exactly translation-covariant continuum case with the study's beam
(`tests/forward/test_null_readout_known_answer.py`, new; case = A6's `resolved_known_answer.py`:
ContinuumPeriodicPotential V0 13.902843 V, V_008 1.035742 V, 16.134773 mrad, Fresnel, complex128,
dx 0.025 A, dz 1 A, clean depth 100 A, R = (a/2, 0, 0); beam and `surface_resolved` block read from
study_depth100.yaml; L = the L_z of the study's L5k/L10k [110] points rounded to whole slices):

```
RH_NULL_READOUT_LONG=1 venv/bin/python -m pytest -q -s -p no:cacheprovider tests/forward/test_null_readout_known_answer.py -k "L10k or L5k"
continuum r 0.1, L 6377.0 A, H 97.184 A, edge 2.0, gap 2.0, nx 15592: 3 runs in 46 s
  fixed beam: converged beyond 2500.0 A from the later contact (4 included bin(s) beyond, all within tolerance); lit-end limit 5031.6 A (margin 991.1 A)
  moved beam: converged beyond 0.0 A from the later contact (9 included bin(s) beyond, all within tolerance); lit-end limit 5031.6 A (margin 991.1 A)
continuum r 0.1, L 11377.0 A, H 177.865 A, edge 2.0, gap 2.0, nx 22047: 3 runs in 117 s
  fixed beam: converged beyond 2500.0 A from the later contact (12 included bin(s) beyond, all within tolerance); lit-end limit 9254.5 A (margin 1768.2 A)
  moved beam: converged beyond 0.0 A from the later contact (18 included bin(s) beyond, all within tolerance); lit-end limit 9254.5 A (margin 1768.2 A)
  smallest bin |E_A| / largest: 0.297 (amplitude floor 0.05)
continuum r 0.05, L 11377.0 A, H 177.865 A, edge 2.0, gap 2.0, nx 22047: 3 runs in 117 s
  fixed beam: converged beyond 3000.0 A from the later contact (11 included bin(s) beyond, all within tolerance); lit-end limit 9254.5 A (margin 1768.2 A)
  moved beam: converged beyond 0.0 A from the later contact (18 included bin(s) beyond, all within tolerance); lit-end limit 9254.5 A (margin 1768.2 A)
  smallest bin |E_A| / largest: 0.206 (amplitude floor 0.05)
3 passed, 2 deselected in 284.34s (0:04:44)
```

(03:37-03:42 UTC, load ~2-3.) The moved-beam control is within 1e-2 rad and 1e-2 in EVERY bin,
the excluded ones included (asserted); the fixed-beam ratio converges (r = 0.05, L10k: bins d 3000
to 8000 A at |err| <= 1.6e-3 rad, |amp - 1| <= 9.6e-3; the bin d 9500, 761 A before the end of B's
lit core, reads +1.81e-2 rad and is excluded by the lit-end limit: the limit is needed at this
length). Full log `<scratch>/x2/known_answer_long.log`. The L5k case (r = 0.1) runs in the default
suite; the two L10k cases only with RH_NULL_READOUT_LONG=1 (about 4 min).

## N-2 (MAJOR): amplitude floor, lit-end limit and a verdict that a single last bin cannot void

FIXED. `tests/forward/null_test_cases.py` `resolved_translation(..., amp_floor_rel)` (REQUIRED;
`RESOLVED_KEYS` gains `amp_floor_rel`, so study files must state it; refused outside [0, 1)):

* Cause of A6's failing last bin, isolated first (`<scratch>/x2/lit_end_probe.py`, A6's case r 0.1,
  L 6000 A, H = L tan(theta) - 6 A, edge 4 A, E1's code): it is the END OF B'S ILLUMINATION, not the
  exit plane. With A's top edge lowered so that it meets A's surface where B's meets B's (`fixed_top`,
  bottom edges as in the fixed beam) the last bin reads `err +6.80e-04 rad, |B|/|A| 1.00041` instead
  of `err -7.40e-03 rad, |B|/|A| 1.02920`; with H 3 A lower (lit end 186 A earlier) the failure moves
  one bin up (`d 4000.0: err +1.11e-02 rad`); the moved beam (lit ends coincide) passes every bin.
  Mechanism (DERIVED_HERE): Fresnel fringes of the beam's top edge; after a path L_z a fringe dx below
  the edge has frequency offset dx/(lambda L_z), so the read-out band (radius 0.1 1/A) passes fringes
  within radius lambda L_z / tan(theta) of surface (933 A at L 6000 A) before the lit end; in the
  fixed beam they sit 168 A apart on A and B and do not cancel.
* Every bin is still reported (`rows`, same binning as E1), now with `status` (pass / fail /
  excluded), `passes`, `included` and `excluded_because`. Excluded from the verdict: bins ending
  beyond `lit_strip()`'s LIT-END LIMIT = min over A, B of the end of the fully lit core
  (top edge - edge) minus radius lambda L_z / tan(theta) (derived, no new parameter); and bins with
  |E_A| or |E_B| below `amp_floor_rel` x the largest bin amplitude of that exit wave.
* Verdict: `converged_beyond_A` = the first distance beyond which every included bin passes (end
  of the last failing included bin, or the start of the first included bin if none fails); a
  number whenever a bin is included (None only when none is); `n_bins_beyond`; `converged` =
  n_bins_beyond >= 1; `verdict` text; `excluded` list with reasons; `lit_strip` record; the last
  bin still reported separately (`last_bin`).
* `amp_floor_rel = 0.05` in study_depth100.yaml, justified in its header: on A6's covariant control
  (A6's H = 8 A moved-beam runs, 38 bins, `<scratch>/resolved_h8.log`, recounted here) the ratio
  left the 1e-2 criteria only in bins with |E_A| <= 2.1e-3 of the largest bin (1e-5 to 1.6e-4
  absolute); every bin above 2.3e-3 of it stayed within 3.4e-3 rad and 8.1e-3 in amplitude, above
  1e-2 of it within 2.0e-3 rad and 1.9e-3; 0.05 is 24 times above the highest failing bin. In a
  strip lit to the exit plane the smallest bin is 0.21 (r 0.05) to 0.29 (r 0.1) of the largest
  (runs above), so the floor removes only unlit or decayed tails.
* `exit_excl_A` 750 -> 1115.5 A in study_depth100.yaml (H2 2.6's 3-element exit margin, as A6
  recommends). This narrows the read-out window; it is not a tolerance (tol_phase_rad and tol_amp
  stay 1e-2). For L >= 5k the lit-end limit ends the verdict window earlier anyway.

Tests. Synthetic (`tests/forward/test_null_study_readout.py`): the three existing read-out tests
keep their assertions, their synthetic pair now has beams lit to the exit plane (height and edge
were needed by lit_strip); new: `test_excluded_last_bins_do_not_decide_the_verdict`,
`test_amplitude_floor_excludes_the_noise_floor_and_is_required` (with floor 0 the same data are
NOT converged), `test_case_functions_require_the_sheet_beam`,
`test_lit_to_exit_height_and_refusal_of_a_short_beam`. ONE EXISTING ASSERTION CHANGED because the
behaviour changes on purpose (orchestrator: no None from a single last bin):
`test_unconverged_last_bin_gives_none` (`converged_beyond_A is None`) became
`test_unconverged_last_bin_gives_not_converged`: every included bin fails, `converged is False`,
`n_bins_beyond == 0`, `converged_beyond_A` = end of the last included bin, verdict "NOT converged".
Real engine exit waves (`tests/forward/test_null_readout_known_answer.py`), default suite:

```
venv/bin/python -m pytest -q -s -p no:cacheprovider tests/forward/test_null_readout_known_answer.py   (03:33 UTC, load 1.8)
continuum r 0.1, L 6000.0 A, H 90.817 A, edge 4.0, gap 2.0, nx 15094: 3 runs in 53 s
  fixed beam: converged beyond 2500.0 A from the later contact (3 included bin(s) beyond, all within tolerance); lit-end limit 4571.7 A (margin 932.5 A)
    z_s  2792.2- 3292.2 (d 2500.0): err -2.04e-04 rad, |B|/|A| 1.00677, |E_A| 0.3300: pass
    z_s  3292.2- 3792.2 (d 3000.0): err +1.23e-03 rad, |B|/|A| 1.00298, |E_A| 0.3357: pass
    z_s  3792.2- 4292.2 (d 3500.0): err +2.07e-03 rad, |B|/|A| 1.00068, |E_A| 0.3373: pass
    z_s  4292.2- 4792.2 (d 4000.0): err -1.19e-03 rad, |B|/|A| 0.99547, |E_A| 0.3374: excluded (beyond the lit-end limit z_s = 4571.7 A (end of the lit core of B minus the top-edge fringe margin 932.5 A))
    z_s  4792.2- 5250.0 (d 4500.0): err -7.39e-03 rad, |B|/|A| 1.02916, |E_A| 0.3363: excluded (beyond the lit-end limit z_s = 4571.7 A (end of the lit core of B minus the top-edge fringe margin 932.5 A))
  moved beam: converged beyond 0.0 A from the later contact (8 included bin(s) beyond, all within tolerance); lit-end limit 4571.7 A (margin 932.5 A)
continuum r 0.1, L 2500.0 A, H 34.624 A, edge 2.0, gap 2.0, nx 10588: 2 runs in 12 s
  fixed beam: NOT converged: the last included bin (ending 1000.0 A from the later contact) fails; lit-end limit 1757.2 A (margin 388.6 A)
    z_s   292.2-  792.2 (d    0.0): err -1.61e-01 rad, |B|/|A| 1.39191, |E_A| 0.0952: fail
    z_s   792.2- 1292.2 (d  500.0): err -4.12e-02 rad, |B|/|A| 1.15065, |E_A| 0.1921: fail
continuum r 0.1, L 6377.0 A, H 97.184 A, edge 2.0, gap 2.0, nx 15592: 3 runs in 46 s
  fixed beam: converged beyond 2500.0 A from the later contact (4 included bin(s) beyond, all within tolerance); lit-end limit 5031.6 A (margin 991.1 A)
  moved beam: converged beyond 0.0 A from the later contact (9 included bin(s) beyond, all within tolerance); lit-end limit 5031.6 A (margin 991.1 A)
3 passed, 2 skipped in 113.73s (0:01:53)
```

(first case = A6's converged case exactly as A6 ran it, exit exclusion 750 A: converged beyond
2500 A; its last bin, amplitude 1.029, is excluded with its reason; second case = non-converged,
study beam and block in a cell shorter than the build-up.) E1's code on the same waves returned
`converged_beyond_A None` (`<scratch>/x2/lit_end_probe_dH0.log`).

## S-1 and S-2 (MINOR): status wording

FIXED (text only; no behaviour).

* S-1: rung 3 is now qualified everywhere A6 named: `reflection_holo/forward/multislice/engine.py`
  module docstring and `VALIDATION_STATUS` ("rung 3 has passed ONLY for the continuum null tests and
  the atomistic MOVED-beam translation: the atomistic FIXED-beam translation check that docs/05 4.4
  item 3 requires before any step-phase run has NOT passed"), `scripts/hpc/null_test_study/
  run_study.py` docstring and the status line of `study_depth100.yaml`.
* S-2: `VALIDATION_STATUS` and the engine docstring now say that the flat-surface rocking-curve
  comparison with an independent dynamical solver (sim-trhepd-rheed, flat Si(001), [100] and [110],
  TEST_ONLY r = 0.1; reports S5, E8) was RUN: "with the solver's own potential the phases agree
  within about 0.03 rad over the rocking range, but the comparison is not like-for-like along the
  beam and its amplitude tolerance has no power (E8 M1, M2): not an amplitude validation". The
  abTEM cross-check stays NOT RUN. (Wording follows docs/05 4.4 and E8 sections 8 and 11.)
  `tests/forward/test_engine_contract.py` asserts only `"UNVALIDATED" in VALIDATION_STATUS` and that
  the string is copied into the metadata; no test pins the old text. Stored JSON records
  (supercell_sizing_measurements.json, review_h5_rerun.json, rheed_engine_results.json) keep the
  string of the engine they were made with (records; not compared by any tool or test).

## B-1 (MINOR): the false memory claim

FIXED (claim corrected, measured; behaviour unchanged as instructed). Measured with tracemalloc
(`<scratch>/x2/b1_memory.py`, n = 2000 coordinates; blocked = the statements of the blocked branch
with blocks of 1024 rows, results byte-identical to the unblocked path):

```
EXP_BLOCK_ROWS = 1024; n = 2000 coordinates; B per output element
 dtype      rows  unblocked(default)  blocked(1024)  model: 32 | cb + 32*1024/rows   smaller
 complex64   1024              32.00          40.00   32.00 |  40.00            unblocked
 complex64   1365              32.00          32.01   32.00 |  32.01            unblocked
 complex64   1366              32.00          31.99   32.00 |  31.99            BLOCKED
 complex64   1536              32.00          29.33   32.00 |  29.33            BLOCKED
 complex64   2048              32.00          24.00   32.00 |  24.00            BLOCKED
 complex128  1365              32.00          40.01   32.00 |  40.01            unblocked
 complex128  1800              32.00          34.20   32.00 |  34.20            unblocked
 complex128  2048              32.00          32.00   32.00 |  32.00            unblocked
```

(excerpt; all 16 lines in `<scratch>/x2/b1_memory.log`.) So "up to 2 x EXP_BLOCK_ROWS rows the
unblocked form needs less memory" holds for complex128 but, for complex64, only up to 1365 rows;
from 1366 to 2048 rows the unblocked stage needs up to 33 % more (32 against 24 B per element at
2048 rows). Corrected in `potentials._phase_factors`' docstring and in the docstring of
`tests/forward/test_potential_blocked_exponentials.py::test_default_block_is_used_only_where_it_saves_memory`
(its assertions unchanged). E1's report (docs/, not edited here) carries the same statement at
lines 235-237: superseded by this section.

## K-1 and K-2 (MINOR): kit

FIXED.

* K-1: `python -m reflection_holo.pipeline dry-run --report-json` writes schema
  `reflholo_pipeline_dry_run_report/2` with `engine_code` = SHA-256 of the multislice package
  (`reflection_holo/pipeline/__main__.py` `engine_code_identity()`, the same definition as the
  kit's `engine_code_sha256`: relative path, size, content of every *.py, sorted; equality with the
  kit's function asserted in tests). `scripts/hpc/alliance/kit.py` `gpu_need_from_dry_run(...,
  repo)` refuses a report whose `engine_code.sha256` differs from `engine_code_sha256(repo)` of the
  submitting clone (also a report without it, and schema /1), and records the hash in
  `gpu_memory_need`.
* K-2: an explicit `--need-gpu-mem-gb` BELOW the need derived from the dry run is refused unless
  `--accept-need-below-dry-run` is given; then a WARNING is printed and `explicit_need_gb`,
  `explicit_below_derived`, `accept_need_below_dry_run` are recorded in the submission record's
  `gpu_memory_need`. An explicit need above the derived one overrides it as before (NOTE). The flag
  without both options is refused. `submit.sh` passes the flag (header documents it; `-h` range
  2-44), README_ALLIANCE.md 4.7 documents both rules.
* Tests `tests/hpc/test_kit_gpu_mem_from_dry_run.py`: the report fixture writes schema /2 with the
  current engine hash; new refusals (other engine code, no engine code, E1's schema /1), the below-
  need refusal, acceptance with the flag and its record (new test
  `test_accepted_override_below_the_derived_need_is_recorded`), an above-need override without the
  flag, the flag without both options. CHANGED ASSERTIONS (intentional behaviour change): E1's
  `--need-gpu-mem-gb 30` against a derived 50 GB was asserted to succeed; it now must be refused
  and succeeds only with `--accept-need-below-dry-run` (the original success assertions are kept
  under the flag); `schema == ".../1"` became `".../2"` in the two report tests, which also assert
  the engine hash.

## Z-1 (MINOR): the vacuous device-peak self-check of tools/hpc/supercell_sizing.py

FIXED. `device_peak_ge_H5_pixel_term_<row>` (`device >= 48 px`) is replaced by
`device_peak_ge_H5_blocked_model_<row>`: the engine's device peak must be >= H5's measured model with
the blocked exponential stage, `h5_blocked_device_bound(nx, ny, n, precision, EXP_BLOCK_ROWS)` =
48 px + max(E(nx), cb nx n + E(ny)), E(m) = 32 m n for m <= 2 B, cb m n + 32 B n otherwise (E1's
proposal; written in the tool independently of engine._exp_stage_B; cb nx n = H5's 8 nx n for the
complex64 rows). Negative control printed by the tool and made a self-check
(`negative_control_device_peak_check_can_fail`): the engine's device model with the
potential-construction stage removed (loop residents + 5 cb px; an omission of the kind H5 M4 found)
fails the new bound for 6 of the 11 scenario rows, while the former 48 px check passes all 11.
Tool rerun, output saved to `tools/hpc/supercell_sizing_output.txt`:

```
venv/bin/python tools/hpc/supercell_sizing.py      (03:42 UTC, load 2.0; exit 0; 27 s)
  CHECK PASS device_peak_ge_H5_blocked_model_2a_a2_miscut0.1_r0.10: model device peak 7.731 GB >= H5's measured model with the blocked exponential stage 6.285 GB (48 B/px + max(E(nx), cb nx n + E(ny)), E blocked above 2048 rows; ratio 1.23); H5's unblocked model 14.548 GB applies to the code before E1's blocked structure factors
  CHECK PASS device_peak_ge_H5_blocked_model_3_torus_R1000_r20_r0.05: model device peak 8.665 GB >= H5's measured model with the blocked exponential stage 6.671 GB (48 B/px + max(E(nx), cb nx n + E(ny)), E blocked above 2048 rows; ratio 1.30); H5's unblocked model 12.959 GB applies to the code before E1's blocked structure factors
NEGATIVE CONTROL of device_peak_ge_H5_blocked_model_* (A6 Z-1): the engine's device model with the potential-construction stage removed (loop residents + 5 cb px) fails H5's blocked bound for 6 of 11 scenario rows (e.g. 2a_a2_miscut0.1_r0.10: 3.888 GB < 6.285 GB); the former check device >= 48 px fails for 0 of them (it cannot fail: the model has >= 84 B/px for complex64)
  CHECK PASS negative_control_device_peak_check_can_fail: 6 of 11 rows fail the blocked H5 bound with the potential stage removed (must be > 0); the former 48 px check: 0 fail
61/61 checks pass; runtime 26 s
```

Observation (not a defect): for these 11 rows the engine model's device peak is set by the pixel
stage of the potential construction, not by the exponential stage (an exploratory run with the
engine's MEM_EXP_B_PER_ELEMENT set to 16, 8 and 0 left every row's model unchanged; model/bound
1.230-1.553, `<scratch>/x2/z1_explore.py`), so the new check detects an under-count of that stage
or of the residents larger than 19-35 % per row, not a 32 -> 16 B slip in the exponential transient.
The other differences of the saved output against the previous one are the run record (commit,
load) and the live CPU calibration line (426.815 s -> 594.458 s, timed under the current load).

## NITs n1-n9

| id | decision | where / how |
|---|---|---|
| n1 | FIXED (doc) | `potentials.py` ContinuumPeriodicPotential docstring: any finite t_n is accepted (the cosine is periodic, t_n and t_n + m/g_n are the same potential); "t_n >= 0" was a convention, not needed. No behaviour change. |
| n2 | FIXED | `tests/forward/test_rung2_bragg.py` R2-B: the E7 M1 pixel-centre assertion of x_s added (as in `_run`). R2-B stays optional (RH_RUNG2_R2B=1); run below. |
| n3 | FIXED | `null_test_cases._translation_check`: cKDTree periodic in y and z instead of rounded-coordinate sets; `check` = n_translated, n_B_above, max_distance_A, identical_sets. Before: `identical_sets False` for every pair; after: True with 2.4e-13 to 3.6e-12 A for the 11 study.yaml pairs; asserted in test_atomistic_translation.py and test_null_study_readout.py. |
| n4 | FIXED | `tests/forward/test_atomistic_translation.py::test_translated_crystal_is_the_builders_crystal`: the tree is periodic in z too (coordinates relative to the crystal start, box = the crystal length); assertion `d.max() < 1e-9` unchanged, plus `pair["check"]` asserted. Checked on both azimuths (`<scratch>`, not a test): `[110] ... non-periodic in z 2.602e-13 A, periodic in z 2.602e-13 A`; `[100] R = [ 2.71545  0.  -2.71545]; ... non-periodic in z 2.352e+00 A, periodic in z 2.276e-13 A` (A6's false mismatch reproduced and removed). |
| n5 | FIXED except one file | stale "rung 2 not run" texts corrected in tests/forward/smoke_case.py, tests/forward/test_smoke_atomistic.py (docstrings), scripts/torus/run_torus_multislice.py (docstring), scripts/hpc/README_HPC.md section 6 (with the S5/E8 statement). DECLINED for scripts/hpc/alliance/README_ALLIANCE.md:15: the orchestrator restricted edits in scripts/hpc/alliance/ to K-1/K-2; the line still says "docs/05 4.4 rung 2 and the abTEM cross-check NOT RUN" and should read like README_HPC.md section 6 (for the kit owner). |
| n6 | DECLINED | E1's line count of the H5 diff (8/6, not 6/5) is in docs/agent_reports/E1_engine_wave2a.md; docs/ is not mine to edit. Recorded here as the correction. |
| n7 | DECLINED | `--gpu-mem-margin 0` stays accepted: outside the orchestrator's K-1/K-2 scope for scripts/hpc/alliance/; the value is stated by the user, printed and recorded, and the NOTE says the device peak is a LOWER BOUND. |
| n8 | DECLINED | engine and P2's reference share `reflection_holo.constants` and the read-out shares `propagator_phase`: inherent to the design (P2 section 1 states it); an error common to both is out of reach of R2-A by construction. n9 removes the one avoidable coupling. |
| n9 | FIXED | `tests/forward/ladder_cases.py` `rung2_measure`: the reference is evaluated with P2's `reflection_amplitude_K(K = 2 pi f)` at each bin's own normal wavevector, so the engine's wavelength no longer enters the reference (the angle asin(lambda f) is kept for display only). R2-A rerun in tests/forward below (criteria unchanged). |
