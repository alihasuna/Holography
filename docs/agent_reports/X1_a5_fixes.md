# X1 - Fixes of the A5 audit findings (E2/E3 code)

Agent X1, 2026-09-24. Status: IN PROGRESS (written incrementally).

Scope: apply docs/agent_reports/A5_e2_e3_audit.md (F1-F11 and the NITs that concern code) to the
code of E2 and E3, with the orchestrator's decisions. Code under audit unchanged since f4ce75e at the
start (`git diff --stat f4ce75e HEAD -- reflection_holo tests configs scripts` empty). Nothing
committed or pushed. Not edited: `reflection_holo/forward/multislice/potentials.py`, null-test
files, `scripts/hpc/alliance/`, docs/ (except this report), the E2/E3 reports.

## 0. Log

* 2026-09-24: read A5 in full, the E2 and E3 reports, A5's scratch scripts; code read.
* 2026-09-24: F1-F11 and the code NITs implemented (section 1); new and changed tests written;
  suite runs in section 2.

## 1. Findings: fixed or declined

Line numbers are those of the working tree at the end of this task.

### F1 (MAJOR) B4 verdict of static buckled terraces from a sign convention: FIXED

* The buckling registry is an explicit, REQUIRED builder input for the static buckled tables:
  `termination={"name": "p(2x1)a" | "p(2x2)" | "c(4x2)", "buckling_registry": D}`, D one of
  `+[100]`, `-[100]`, `+[010]`, `-[010]` (`reconstruction.BUCKLING_REGISTRIES`; module docstring
  "Buckling registry"). A terrace whose dimer-bond axis d (read with a positive crystal-x
  component, now called a labelling convention) has d.D > 0 carries R1's table; the others carry
  its mirror image through each cell's mid-plane (same cells; the flip-flop's state 1). For
  p(2x1)a the up atom of every dimer lies on the D side. The bare name is refused
  (`check_buckling_registry`, `si001.parse_termination`); a registry with p(2x1)s (its own
  mirror image, tested exactly) or with the flip-flop ensemble (both states of every cell) is
  refused rather than ignored. All four orientations are offered, so the global orientation is
  no hidden convention either. The builder's signature is unchanged (no caller had to change).
* B4: static buckled a/4 steps at <100> get `B4_RECON_A4_BUCKLED` = "not guaranteed at any
  azimuth; depends on the buckling registry: ... the flip-flop ensemble (B37) is the only
  room-temperature model here for which B4 holds, and then on average only ...". The measured
  relation is recorded separately as `relation.buckling_registry_relation` (registry, maps or
  not, smallest deviation, note "not physics"). `B4_RECON_A4_100` now applies to p(2x1)s only
  (text says so); `B4_RECON_ENSEMBLE` names B37 as the only RT model. Metadata `frame_rule`,
  `buckling_registry` (label "MODEL CHOICE (explicit, required; not physics)").
* Pipeline: `cfg_b.surface_preparation_details.termination` takes the same mapping; the gate
  (`config._check_termination`) refuses a bare buckled name before any engine run.
* Measured (scratch `x1/f1_registry.py`, all 24 builds pass (a)-(g), (r1)-(r6)): p(2x1)a with
  +-[100]: [100] maps (0.000 A), [010] does not (0.708 A); with +-[010]: [100] 0.708 A, [010]
  0.000 A. p(2x2): 0.001/0.022 A and 0.022/0.000 A; c(4x2): 0.001/0.018 A and 0.018/0.000 A. The
  verdict swaps as A5 found.
* Files: `reflection_holo/structure/reconstruction.py` (docstring l. 25-29, 49-67;
  `MIN_SUBSTRATE_LAYERS` l. 112, `BUCKLED_STATIC` l. 117, `BUCKLING_REGISTRIES` l. 121-133;
  `table_displacements` l. 232; `check_buckling_registry` l. 394; `build_reconstruction` l. 416,
  registry applied l. 507, metadata l. 541); `reflection_holo/structure/si001.py`
  (`parse_termination` l. 432, `B4_RECON_A4_100` l. 495, `B4_RECON_A4_BUCKLED` l. 503,
  `_b4_reconstructed` l. 546, `buckling_registry_relation` l. 1033);
  `reflection_holo/pipeline/config.py` (`_check_termination` l. 903-921).
* Tests (tests/structure/test_si001_reconstruction.py): new
  `test_both_registry_axes_build_and_the_measured_relation_swaps` (3 tables x 4 registries x
  [100], [010]), `test_buckled_reconstruction_requires_an_explicit_registry`,
  `test_p2x1s_is_its_own_mirror_image_and_takes_no_registry`,
  `test_static_registries_are_members_of_the_flipflop_ensemble` (exact equality);
  tests/pipeline/test_e2_thermal_reconstruction.py: bare "c(4x2)" refused, mapping accepted,
  registry with the flip-flop refused.
* CHANGED assertions (behaviour intentionally changed): in
  `test_b4_statement_of_reconstructed_steps_is_measured` the expected statement for p(2x1)a,
  p(2x2), c(4x2) at [100] (was `B4_RECON_A4_100`) and at [010] (was `B4_RECON_NOT`) is now
  `B4_RECON_A4_BUCKLED` for both; the test gained the measured-relation assertions. In
  `test_reconstruction_accepted_only_on_the_multislice_staircase_path` the static "c(4x2)" string
  (accepted before) is now asserted refused, and the mapping is accepted. The helper `rbuild`
  passes the registry (TEST choice `+[100]`, the relabelled former convention, so every other
  assertion of the module is unchanged).

### F2 (MAJOR) static lattice accepted in comparison runs: FIXED

* `pipeline/config.py:697-710` (`load_pipeline_dict`, comparison branch): purpose "comparison" refuses
  `frozen_phonons: none` whatever its label; the message names item 23, the Debye-Waller factor
  (1.0 vs 0.772 at (0,0,8)) and B35. All comparison refusals (fixed u, static lattice, demo
  stand-ins, TEST_ONLY) are now reported in ONE error (`_comparison_gate(..., reasons=)`), so the
  message names item 23 even when demo stand-ins are also present (A5's last line;
  `_comparison_gate` l. 947).
* Demo runs: `static_lattice_label` must start with ASSUMPTION (TEST_ONLY in memory) when
  `frozen_phonons: none`, and must be null otherwise (refused rather than ignored)
  (`_check_frozen_phonons` l. 1114-1140). The demo files already carry "ASSUMPTION (demo): static lattice ..."
  and keep working.
* Tests: `test_comparison_refuses_a_static_lattice_naming_item_23`,
  `test_static_lattice_needs_an_assumption_label_and_a_label_needs_a_static_lattice`
  (tests/pipeline/test_e2_thermal_reconstruction.py).

### F3 (MINOR) 0.536 quoted for n = 1.25: FIXED (orchestrator decision: n = 1.246)

* `configs/demo_smoke_si001.yaml`, `configs/demo_hpc_si001.yaml` variant `plasmon_losses`:
  value 1.246, source "1.246 = 1.44 x sin(0.8 deg)/sin(16.1347 mrad) ... line 119: 1.246,
  zero-loss amplitude exp(-n/2) = 0.536"; description "1/0.536 = 1.86" (1/0.53633 = 1.8645; the
  former "1.87" was 1/0.536 rounded up). B30 texts of all five demo files: "n = 1.246".
  `optics/inelastic.py` docstring (1.246 -> 0.536; R2: 0.288 + 0.712 V_loss = 0.359 at 0.1),
  registry comment of B38.
* CHANGED assertions: `test_plasmon_losses_reduce_the_contrast_used_by_the_noise_model`
  (tests/pipeline/test_e3_convergence_losses.py) now expects exp(-1.246/2) (was exp(-1.25/2)),
  exp(1.246/2), fringe factor exp(-0.623) (was exp(-0.625)), because the stand-in value changed;
  it also asserts round(contrast, 3) == 0.536 and V_loss None. The gate test asserts the variant
  value 1.246.

### F4 (MINOR) reconstruction on a too-thin substrate: FIXED

* `reconstruction.py:112` `MIN_SUBSTRATE_LAYERS = RECONSTRUCTED_DEPTH + 3` (= 8), checked at
  `si001.py:860`: the 5 tabulated layers,
  the bulk layer bonded to them, one bulk layer that (r6) checks at d_nn, the bottom layer. The
  builder refuses a reconstruction on fewer layers (ValueError); bulk keeps its minimum 4. (r6)
  "not applicable" became an assertion error (unreachable; `si001.py:753`).
* Scratch `x1/nit_mutation.py`: 4, 5, 6, 7 layers REFUSED; 8 BUILT with 16 interior atoms
  checked. Test `test_reconstruction_needs_the_minimum_substrate`.

### F5 (MINOR) R2 design extent not conservative: FIXED (re-derived)

* Derivation (docstring of `pipeline/convergence.py::design_extent`, l. 76; code l. 113-125): with dk_in = k (t_a e_a +
  t_b e_b) - k (1 - sqrt(1 - t^2)) b0 and dk_out = mirror(dk_in) exactly, the R2 member phase
  flat_mirror(Q, x_m) - flat_mirror(Q + (dx, s_y, 0), x_m') = k [t_a (s_u - 2 c dh) - t_b s_y]
  + k (1 - sqrt(1 - t^2)) s (dx + 2 dh), dx = -s_u/c, |dh| <= h_max. Hence
  |E|_max = sqrt((|s_u| + 2 c h_max)^2 + s_y^2) (A5's formula) and the curvature bound gains the
  step term: kappa <= k alpha^2/2 s (|s_u|/c + 2 h_max) (1 + alpha^2).
* Test `test_r2_design_extent_adds_the_shift_and_the_step_phase`: the odd part of the
  independently computed member phase over 3601 boundary azimuths equals v_design to 1e-6 (tight)
  and never exceeds it (1e-9); the even part stays below kappa (+ 4 k eps |Q| rounding). Shifts
  (10, 0), (40, 0), (0, 10), (-25, 15) A, a/2 step, alpha 0.1 mrad. For (40, 0) the 1 x 4 disc
  passes the 1e-2 gate at the former extent and is refused at the corrected one (curvature 0 in
  both calls, isolating F5).

### F6 (MINOR) member assembly: FIXED

* `pipeline/convergence.py`: `run_member_job` (l. 262; record l. 307-316) writes
  `engine_manifest_sha256`, `seed`, `n_realisations`, `code` (commit,
  dirty, package-tree SHA-256; `code_identity` l. 323). `load_member_jobs(..., code_state=)`
  (l. 332) refuses: realisations other
  than exactly 0..n-1; waves or records with another seed; a missing, edited (SHA-256) or foreign
  engine manifest (member index, seeds, realisation count, commit and package tree compared with
  the record); different CODE across the members or with the assembling run (its git pre-flight,
  passed from `run.py`). The code that ran is identified by the package-tree SHA-256 (every
  `*.py`/`*.yaml` of `reflection_holo/`, committed or not), which must be one; the commits are
  recorded, and different commits with the same package tree are accepted and recorded as
  `mixed_commits` (A5's "clean, or record the mix"; comparing commits alone would refuse an
  identical tree after an unrelated commit, which happened during this task: the orchestrator's
  snapshot commits moved HEAD twice while the tests ran). A record without the new fields is
  refused (rerun the job). The assembled record keeps `member_code`.
* Test `test_member_job_assembly_checks_realisations_seed_manifests_and_code` (synthetic jobs
  written with the repository's `save_exit_wave`): refused are A5's case "member 0 has 2
  realisations", a member with another package tree, another seed in the waves or in the record,
  code other than the assembling run's, an edited or missing engine manifest, a record without
  the manifest hash; A5's "commits aaaa/cccc" with one package tree is accepted with
  `mixed_commits` True. The genuine path is E3's
  `test_member_jobs_assemble_to_the_in_process_ensemble` (section 2).

### F7 (MINOR) R2 without shift -> KeyError: FIXED

* `pipeline/config.py::_check_reference` (l. 733-757): an R2 run without `sections.reference.shift` raises
  MissingProjectInputError naming item 16 at the gate (every path: plane wave and convergence),
  CLI exit 3; `list_inputs` shows the shift MISSING for R2. `design_extent` refuses clearly too.
* Test `test_r2_without_its_shift_is_a_missing_project_input_before_any_engine_run`.

### F8 (MINOR) sqrt(2) for the complex disc integrand: FIXED

* `optics/coherence.py::radial_error_bound` (l. 169): disc branch multiplies by sqrt(2) when kappa != 0.
  Derivation (module docstring): the one-point remainder holds for real functions; for h = u + i w
  it applies to u and w separately, |R[h]| = (R[u]^2 + R[w]^2)^(1/2) <= sqrt(2) C_n max|h^(2n)|
  since |u^(2n)|, |w^(2n)| <= |h^(2n)|. kappa = 0: h = J0 real, factor 1.
* Test `test_disc_radial_bound_carries_sqrt2_for_the_complex_integrand` (tests/optics/
  test_coherence.py): against an independent scipy minimisation over R, factor sqrt(2) exactly
  where kappa > 0.

### F9 (MINOR) report numbers: corrected numbers listed (E2/E3 reports not edited)

Printed by `tools/review/x1_a5_numbers.py` (new; saved output `tools/review/x1_a5_numbers_output.txt`):

* E3 section 2.4 "v = 0.3, tolerance 1e-2 needs 1 x 4": the code gives `1 x 3 = 3 members, bound
  1.154e-03` (curvature 0; unchanged by F8). The other example reproduces: `v = 3.0, tolerance
  1e-06: 3 x 13 = 39 members, bound 6.212e-07`.
* E2 sections 0 and 1.4 "compressed by at most 5.5 % of d_nn (2.176 A, p(2x2))": by the code's
  recorded measure `riser_edge_largest_compression_of_dnn` = 1 - min/d_nn (d_nn = 2.3516 A),
  E2's own p(2x2) minimum 2.1759 A is `7.47 %`; 5.5 % belongs to 2.2220 A (`5.51 %`, p(2x1)a,
  transverse edges). On the script's staircase (0, 2, 1), [110]/[100]/[010], both edge
  orientations, every registry: largest recorded compression p(2x2) `2.1814 A: 7.24 %` (A5's
  0.0724), c(4x2) `2.2061 A: 6.19 %`, p(2x1)a and the flip-flop `2.2086 A: 6.08 %`, p(2x1)s none
  below its table bond (`2.2339 A`, recorded 0.00 %). Corrected sentence: "bonds across a riser
  are compressed by up to 7.5 % of d_nn (2.176 A, p(2x2))". The registry changes the riser minima
  slightly (p(2x1)a: 2.2086 A with -[100] or +[010], parallel edges, <100> azimuths; 2.2220 A
  otherwise); all stay above 0.9 d_nn = 2.1165 A.
* E3 section 1/3 and the B38 row: "F = 0.536 at E6's n = 1.25" -> n = 1.246 (F3); 1/0.536 =
  1.86 (not 1.87); R2 with V_loss = 0.1: 0.359 (0.358 was n = 1.25).

### F10 (MINOR) V_loss required on every path: FIXED

* `sections.optics.loss_electron_visibility` is optional in the schema (`config.py:144`); `_check_reference`
  requires it for R2 (MissingProjectInputError item 16) and refuses it for R1/R3 (no effect).
  `optics.inelastic.SurfacePlasmonLoss` (l. 119-136, 220) accepts `loss_visibility=None` only where it cannot enter
  (L_O L_R = 0 or a zero-loss filter; otherwise ValueError), and the R1 intensities stay bit for
  bit (the cross term was an exact zero). The five R1 demo files no longer declare B39.
  `list_inputs`: R1 "NOT USED on this path", R2 "MISSING" if absent.
* CHANGED assertions: `test_plasmon_loss_records_are_required_and_gated` (E3) no longer expects
  MissingProjectInputError when V_loss is deleted from the R1 demo; it asserts the R1 refusal,
  the R2 requirement, the list_inputs rows, and the comparison refusal of B38 (R1 variant) and
  B39 (R2). `tests/pipeline/test_a3_priority2.py::test_r2_differential_phase_returns_no_height`
  declares B39 for its in-memory R2 case (the demo file no longer carries it; n = 0, no effect).

### F11 (MINOR) stale rows, B37 needs B35 only in the pipeline: FIXED (code), rows for the orchestrator

* `forward/dimer_ensemble.py:68`: `DimerFlipFlopPotential` calls
  `structure.thermal.require_b35_frozen_phonons` (`thermal.py:121`): the label must be thermal's B35 label and the
  rms displacement must equal u(T) at the recorded T exactly; A7's fixed u and a forged label are
  refused. Test `test_flipflop_potential_refuses_frozen_phonons_other_than_B35`.
* Registry comments only (`reflection_holo/io/assumption_registry.yaml`): B30 (also n = 0 on
  every demo), B38 (1.246, 0.536), B39 (R2 only), B35/B37 (B37 requires B35, enforced twice;
  the only RT model for which B4 holds). The `model_rows` values are unchanged.
* For the orchestrator (docs not edited): B6 row end; B3/B4 (F1 wording); B35 (comparison refuses
  a static lattice); B37 (enforced in the engine path); B38 (1.246); B39 (R2 only); docs/06 item
  16 (D0 is an effective separation, NIT below; V_loss for R2 only).

### F12 (NITs)

* (r2) not asserted: FIXED. `_assert_reconstruction` (`si001.py:657-670`) compares the reconstruction's sites with the
  checked ideal sites and the count with assertion (b)'s expected count; the duplicate check uses
  the expected count. Test `test_builder_asserts_the_atom_count_r2` (an atom dropped: refused).
* c(4x2) with the p(2x2) registry passed the builder: FIXED. New assertion (r3b)
  `si001._assert_buckling_phases` (l. 594; neighbour search by the repository's cell list,
  linear in the number of dimers): buckling orientation of every dimer measured on the atoms,
  compared along the row and between neighbouring rows (alternating/constant; in phase/antiphase
  per table). A5's mutation is now refused by the builder: "(r3b) c(4x2): neighbouring dimers of
  neighbouring rows are in phase, the table has them in antiphase" (test
  `test_builder_catches_a_c4x2_built_with_the_p2x2_registry`).
* Flip-flop states of realisations >= 1: FIXED in the pipeline (engine.py is E1's and was not
  edited): `engines.flip_flop_states` puts the states of every realisation (and member) in the
  run record `dimer_flip_flop_states` (`engines.py:357`, 410; `convergence.py:231`); asserted in `test_flipflop_configurations_per_realisation`.
* numpy float32 temperature: FIXED (`thermal.py:67`: numbers.Real, not bool).
  Test `test_numpy_floating_temperatures_are_accepted_and_bools_refused`.
* D0 definition: FIXED in code (docstring of `optics.coherence.r1_reference_member_phase`: the
  effective separation of the unfolded geometry, D0 -> D0 + (P_d - R_y(2 th0) P_d)); the docs/06
  item 16 wording is for the orchestrator.

### Kit tests from a git worktree (A5 command 5): small change, DONE and run

* Cause: `scripts/hpc/alliance/job.sbatch:90-92` requires realpath(sys.prefix) =
  `readlink -f $RH_REPO/venv`. A `venv` SYMLINK in the worktree to the main checkout's venv
  satisfies it (readlink -f resolves the link), but `.gitignore` had only `venv/`, which matches
  directories, not a symlink, so the tree became dirty (A5's 4 git-state failures).
* Change: `.gitignore` gains `/venv` (with a comment). Nothing in `scripts/hpc/alliance/` or in
  the kit tests changed. Recipe: `git worktree add --detach WT; ln -s <main>/venv WT/venv`.
* Verified (section 2): worktree at HEAD 2038454 (which predates the `.gitignore` edit, so the rule
  was supplied by `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.excludesFile` pointing at a file with
  `/venv`), `git status --porcelain` clean with the rule and `?? venv` without it; the same 124
  tests as A5's command 5 pass. `git check-ignore -v --no-index venv` in the main tree:
  `.gitignore:7:/venv	venv`. The worktree was removed afterwards.

## 2. Test runs (verbatim counts)

Load average 2-6 on 4 cores (another agent active). Commands from the repository root with
`venv/bin/python -m pytest -q` unless stated.

Failures met while writing the new tests (verbatim; each was a defect of the new test, fixed as
stated; no existing test or tolerance was weakened):

* `test_both_registry_axes_build_and_the_measured_relation_swaps[+[100]-p(2x1)a]`:
  `E   KeyError: 'buckling_registry_relation'` / `1 failed, 73 passed in 9.07s` (the test read
  the key from the step instead of `step["relation"]`; fixed).
* `test_r2_design_extent_adds_the_shift_and_the_step_phase`:
  `E           assert 3.118920176292672e-07 <= 3.1189201077227023e-07` (even part vs kappa). The
  analytic margin of kappa is its factor (1 + alpha^2) = 1 + 1e-8 (3e-15 rad); the independent
  phases are differences of O(1) direction cosines times k |Q| with rounding of order
  k eps |Q| = 5.6e-11 rad, so the exact comparison was below the precision of the check. The
  assertion now allows 4 k eps |Q| = 2.2e-10 rad (stated in the test; 1e-3 of kappa); the odd
  part keeps its 1e-9 relative bound.
* same test, first gate demonstration: `ValueError: declared quadrature (uniform_disc, n_radial =
  1, n_azimuthal = 4) has the error bound 1.548e-02 > tolerance 1.000e-02 for the design phase
  extent v = 1.138 rad (kappa = 0 rad) ...`: the test took the "former" extent from
  `v_coherence_rad`, which after F5 already contains the step term; it now recomputes the former
  rule k alpha |s|. An earlier variant failed because the sqrt(2) of F8 raised the bound at
  kappa > 0 (1.083e-02 at the former extent); the F5 demonstration uses kappa = 0 in both calls.

Runs (final code unless stated):

| # | command | result (verbatim) |
|---|---|---|
| 1 | `pytest -q tests/structure tests/io tests/optics` (before the (r3b) cell-list rewrite) | `476 passed in 31.93s` |
| 2 | `pytest -q tests/pipeline tests/forward/test_convergence_members.py tests/optics/test_darkfield_bloch.py` (before the (r3b) rewrite) | `105 passed in 217.21s (0:03:37)` |
| 3 | kit tests in a worktree (A5's 124: tests/hpc/test_alliance_kit.py, tests/hpc/test_kit_gpu_mem_from_dry_run.py, the 3 SLURM tests of tests/pipeline/test_a3_priority{1,3}.py), `venv` symlink, `/venv` ignore rule | `119 passed, 5 skipped in 191.46s (0:03:11)`; `SKIPPED [5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed` |
| 4 | `venv/bin/python -m pytest -q` (full suite, before the F6 package-tree refinement) | `1156 passed, 6 skipped, 12 warnings in 722.90s (0:12:02)` (the 120 s smoke wall-time test passed within it) |
| 5 | `pytest -q tests/pipeline/test_e3_convergence_losses.py` (after the F6 refinement) | `11 passed in 33.56s` |
| 6 | E2/E3 modules: tests/structure/{test_si001_reconstruction,test_thermal,test_si001_options}.py, tests/pipeline/test_e2_thermal_reconstruction.py, tests/forward/test_convergence_members.py, tests/optics/{test_coherence,test_inelastic,test_darkfield_bloch}.py, tests/pipeline/test_e3_convergence_losses.py | `234 passed in 91.12s (0:01:31)` |
| 7 | `pytest -q tests/io tests/structure tests/optics tests/pipeline` | `570 passed in 193.08s (0:03:13)` |
