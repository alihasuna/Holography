# S3: fixes for the Phase 2 code audit A2 (`reflection_holo`)

Status: COMPLETE, 2026-09-22 (written incrementally). Agent S3. Scope: the findings of
`docs/agent_reports/A2_phase2_code_audit.md` (1 Blocker, 2 Major, 10 Minor, 7 Nit), following the
orchestrator's decisions. No commit or push. `docs/` is not edited except this file.

Baseline (HEAD `fa33ed3`, clean tree), before any change:

```
$ venv/bin/pytest -q | tail -1
374 passed in 6.44s
$ venv/bin/python tools/reflection_step_phase_calculator.py | grep "checks pass"
   25/25 checks pass in this script itself.
$ venv/bin/python tools/phase1_numbers.py | tail -1
   17/17 checks pass
$ venv/bin/python tools/physics_checks/q2_carrier_trap.py | tail -1
   21/21 self-checks pass
$ venv/bin/python tools/physics_checks/q3_r2_twin.py | tail -1
   7/7 self-checks pass
```

Method: for every finding the regression test is written first and run against the unfixed code
(outcome recorded verbatim, trimmed where marked), then the fix is made and the test re-run.

## Log

(entries are appended below as each finding is fixed)

### B1 (Blocker): rocking-series inversion (`reflection_holo/quantification/rocking.py`)

Fix: `resolve_rocking_series(..., sigma_phi_rad, wavelength_A, h_max_A)`; `sigma_phi_rad` (one
per tilt, > 0) is required; `max_intercept_offset_cycles` is removed. Noise-aware unwrap guard,
weighted fit with free intercept, B16 branch criterion (sigma_c < pi/3 and |c - 2 pi n| < pi),
model checks (|c - 2 pi n| <= 3 sigma_c; chi-square p >= 1e-3), sigma_h from the WLS covariance
given the branch, plus the branch statistics (sigma_c, P(|Z| > pi/sigma_c), flat-prior branch
probability, heights of branches n -+ 1). `chi2_sf` added (checked against scipy).
Tests: `tests/quantification/test_quant_rocking_noise.py` (new, 9 tests);
`tests/quantification/test_quant_rocking.py` call signatures updated (tolerances unchanged).

Before (unfixed code): the new tests fail (8 of 8 then written), verbatim causes:
```
      4 E               TypeError: resolve_rocking_series() got an unexpected keyword argument 'sigma_phi_rad'
      2 E           TypeError: resolve_rocking_series() got an unexpected keyword argument 'sigma_phi_rad'
      1 E       ImportError: cannot import name 'chi2_sf' from 'reflection_holo.quantification.rocking' (/home/user/Holography/reflection_holo/quantification/rocking.py)
      1 E       TypeError: resolve_rocking_series() got an unexpected keyword argument 'sigma_phi_rad'
```
and the auditor's case on the unfixed code (`audit/e10_rocking_branch.py`, re-run here, verbatim):
```
tilts 20.0-21.0 mrad step 0.25 (5), noise 0.05 rad: intercept s.e. 0.21 cycles -> correct 1552, WRONG h accepted 1, refused 447 (of 2000); wrong h values e.g. [10.6] A with reported sigma_h median 0.002 A
tilts 20.0-21.0 mrad step 0.25 (5), noise 0.1 rad: intercept s.e. 0.41 cycles -> correct 889, WRONG h accepted 136, refused 975 (of 2000); wrong h values e.g. [ 9.4 10.6] A with reported sigma_h median 0.004 A
tilts 20.0-21.0 mrad step 0.25 (5), noise 0.2 rad: intercept s.e. 0.83 cycles -> correct 468, WRONG h accepted 567, refused 965 (of 2000); wrong h values e.g. [ 8.2  8.8  9.4 10.6 11.2 11.8] A with reported sigma_h median 0.007 A
tilts 20.0-25.0 mrad step 0.5 (11), noise 0.2 rad: intercept s.e. 0.14 cycles -> correct 1642, WRONG h accepted 133, refused 225 (of 2000); wrong h values e.g. [3.4 3.8 4.  4.4 4.7 5.8] A with reported sigma_h median 0.045 A
tilts 16.0-17.0 mrad step 0.25 (5), noise 0.1 rad: intercept s.e. 0.33 cycles -> correct 1068, WRONG h accepted 54, refused 878 (of 2000); wrong h values e.g. [ 9.2 10.7 10.8] A with reported sigma_h median 0.005 A
```
After (`venv/bin/pytest -q -s tests/quantification/test_quant_rocking_noise.py`, 9 passed):
```
tilts 20.0-21.0 mrad step 0.25 (5), noise 0.05 rad: intercept s.e. 1.297 rad (0.21 cycles) -> correct 0, WRONG 0, refused branch 2000, refused guard 0 (of 2000; seed 20260922)
tilts 20.0-21.0 mrad step 0.25 (5), noise 0.1 rad: intercept s.e. 2.594 rad (0.41 cycles) -> correct 0, WRONG 0, refused branch 2000, refused guard 0 (of 2000; seed 20260922)
tilts 20.0-21.0 mrad step 0.25 (5), noise 0.2 rad: intercept s.e. 5.188 rad (0.83 cycles) -> correct 0, WRONG 0, refused branch 2000, refused guard 0 (of 2000; seed 20260922)
tilts 20.0-25.0 mrad step 0.5 (11), noise 0.2 rad: intercept s.e. 0.860 rad (0.14 cycles) -> correct 0, WRONG 0, refused branch 0, refused guard 2000 (of 2000; seed 20260922)
tilts 16.0-17.0 mrad step 0.25 (5), noise 0.1 rad: intercept s.e. 2.088 rad (0.33 cycles) -> correct 0, WRONG 0, refused branch 2000, refused guard 0 (of 2000; seed 20260922)
tilts 20.0-25.0 mrad step 0.25 (21), noise 0.05 rad, h 10.0 A: intercept s.e. 0.163 rad; accepted 1993 (correct 1993, WRONG 0, allowed <= 16 at p3 = 2.700e-03, alpha 0.0001), refused branch 7, guard 0; std(h err)/sigma_h = 1.0256 (bound 1 +- 0.0634, K = 1993); mean err +3.65e-05 A; seed 20260922, 2000 trials
tilts 20.0-25.0 mrad step 0.5 (11), noise 0.21 rad, h 3.0 A: intercept s.e. 0.903 rad; accepted 1994 (correct 1994, WRONG 0, allowed <= 16 at p3 = 2.700e-03, alpha 0.0001), refused branch 6, guard 0; std(h err)/sigma_h = 0.9802 (bound 1 +- 0.0634, K = 1994); mean err +1.75e-04 A; seed 20260922, 2000 trials
```
Consequence: in all five auditor regimes the branch is not resolvable at 3 sigma (sigma_c >= pi/3)
or the noisy increments can slip, so no height is returned. Absolute heights need a wider tilt
range, more tilts or lower noise (the 21-tilt, 0.05 rad regime is accepted).

### M1 (Major): carrier search picks the conjugate (`reflection_holo/reconstruction/sideband.py`)

Fix: `CarrierSearch` gains the required field `sideband_declaration` (which sideband, on what
evidence); the guess must be non-zero and the search radius finite and < |guess| (disc confined
to one side of a line through the origin), else ValueError. `locate_carrier` refuses a region
that holds a Hermitian pair of bins on the grid (Nyquist aliasing); exact ties go to the bin
closest to the guess. `reconstruct_sideband` raises on a CONJUGATE sign check and on a carrier
located on an object hologram (m7) unless `trap_demonstration=True` (recorded in `parameters`).
Tests: `tests/reconstruction/test_sideband_selection.py` (new, 43 cases: radii 0.3, inf, |guess|
and 0.2 for eight carrier directions in all four quadrants; half-plane search gives +0.500 rad;
Nyquist-aliased pair; declaration required; conjugate refused).
Existing tests changed (signature only, no tolerance): `CarrierSearch(...)` calls in
`holo_cases.py`, `test_sideband_processing.py`, `test_phase_noise.py`, `test_self_reference_R2.py`
gain the declaration; in `test_required_processing_inputs` the search disc for q = 0.375 is 0.1
(the old 0.1875 disc reached the Nyquist line, now refused) so that the mask-crosses-Nyquist
refusal is still what the test exercises. `test_carrier_trap.py`: the whole-plane search is now
asserted REFUSED; the trap bin (511, 64) is reached by a deliberately declared conjugate half-plane
search on the object hologram with `trap_demonstration=True`; every asserted value (bin, 0.78 +-
0.005 rad, CONJUGATE, calculator bin (255, 320), 2.36 rad, -Delta within 5e-3) is unchanged.
C2 scripts adapted to the API (tools/physics_checks/q2, q3): q3 output identical to C2's run;
q2 21/21, only the D2 line differs (it also asserts the refusal of the whole-plane search).

Before (unfixed code): `43 failed`, causes `TypeError: CarrierSearch.__init__() got an unexpected
keyword argument 'sideband_declaration'` (32), `... takes 5 positional arguments but 6 were given`
(10), `Failed: DID NOT RAISE TypeError` (1). The auditor's case on the unfixed code
(`audit/e4_conjugate_sideband.py`, re-run, excerpt verbatim):
```
q_ref=(0.0, -0.125), guess=(-0.0, 0.125), search radius=0.3: located sideband (0.0, -0.125), median phase -0.500 rad (want +0.500); experiment sign check: 'unknown: '; simulated sign check: 'CONJUGATE: p'
q_ref=(-0.125, 0.0), guess=(0.125, -0.0), search radius=inf: located sideband (-0.125, 0.0), median phase -0.500 rad (want +0.500); experiment sign check: 'unknown: '; simulated sign check: 'CONJUGATE: p'
q_ref=(0.0625, -0.125), guess=(-0.0625, 0.125), search radius=0.3: located sideband (0.0625, -0.125), median phase -0.500 rad (want +0.500); experiment sign check: 'unknown: '; simulated sign check: 'CONJUGATE: p'
```
After: `43 passed`; full suite `426 passed`.

### M2 (Major), m4, m5, m10: configuration gate, labels, units, materials (`reflection_holo/io/config.py`, `configs/*.yaml`)

Fix (config.py rewritten):
* `SCHEMAS` per configuration type (CFG-A, CFG-B, CFG-O): required and optional parameters, each with
  its docs/06 item (None where the parameter is not a laboratory input of that configuration; all
  CFG-O values come from P01, CFG-A geometry is the benchmark definition). A parameter outside the
  schema fails. An ABSENT required parameter is listed (`LoadedConfig.missing_required`) and fails at
  run level exactly like a null one: `MissingProjectInputError` naming the item ("item 7
  (glancing_angle_ext, absent)"), or the new `MissingRequiredParameterError` when it has no item.
  `value()` of an absent required parameter raises the same errors.
* `item` is required, whatever the label, when the schema gives one, and refused otherwise; a
  PROJECT_INPUT without a docs/06 item fails (m4). An ASSUMPTION standing in for a docs/06 item must
  carry `stands_in_for_item` (= item) and `assumption_id`, verified against the rows of
  docs/model_assumptions.md (A1-A8, B1-B15 today).
* Duplicate YAML keys fail anywhere in a file (`_UniqueKeyLoader`, `load_yaml_unique`).
* m5: `unit` is required for every parameter; one table `UNITS` (A, nm, um; rad, mrad; keV; V;
  "none"); unknown units and wrong dimensions fail; `LoadedConfig.quantity()` returns the value in
  A, rad, keV or V (value() keeps the declared value). Length and angle parameters lose their unit
  suffix (`glancing_angle_ext`, `convergence_semi_angle`, `objective_aperture_semi_angle`,
  `image_pixel_size`, `height_sensitivity`, `lattice_parameter`); `beam_energy_keV` and
  `mean_inner_potential_V` keep theirs (their only accepted unit).
* m10: `surface_material` must be a canonical symbol and the one of the configuration ("Si" for
  CFG-A and CFG-B, "Pt" for CFG-O); the silicon cross-checks are keyed on the schema, not on the
  string.
Configs: CFG-A `surface_material`, `surface_normal_hkl`, `beam_azimuth_uvw` relabelled ASSUMPTION
with source "inspected repository default ...; benchmark definition, docs/05 section 2 CFG-A" (m4).
V0 in CFG-A and CFG-B: `stands_in_for_item: 20`, `assumption_id: B1`; lattice parameter
`assumption_id: B2`. **Label decision to confirm:** CFG-B `target_reflection_hkl` (0,0,8),
`second_reflection_hkl` (0,0,12) and `step_types` were ASSUMPTION with items 9, 9, 14, but no
model_assumptions row states them, so they could not pass the new rule. They are relabelled
DERIVED_HERE (docs/05 section 2 derives (008) and (0,0,12) as the recommended conditions, as CFG-A's
(4,-4,4) already is; step_types lists the three step types CFG-B covers), with sources that say
items 9 and 14 are not supplied. If the orchestrator prefers ASSUMPTION, rows must first be added to
model_assumptions (proposed: "B17 the working condition is (008), second (0,0,12)"; "B18 the
observables are a/4, a/2 and patterned steps").
Tests: `tests/io/test_io_config_gate.py` (new, 28 cases): (a) omission, (b) five unlinked-ASSUMPTION
variants plus convergence 0.0, (c) duplicate `value:` and appended duplicate parameter, (d) the
three-parameter CFG-A; schema membership; m4 labels; m5 nm->A (0.5 nm -> 5.0 A), mrad->rad
(16.5 -> 0.0165), 0.54309 nm lattice parameter, unknown/wrong/missing units; m10 "silicon", "Si ",
"si", "SI", "Pt" and CFG-O "Si". Existing `tests/io/test_io_config.py` and
`tests/provenance/test_prov_manifest.py`: renamed keys, explicit units, fixtures completed to the
schema (the manifest test now loads the shipped CFG-A); no expectation relaxed.

Before (unfixed code): the module does not collect:
```
E   ImportError: cannot import name 'MissingRequiredParameterError' from 'reflection_holo.io.config' (/home/user/Holography/reflection_holo/io/config.py)
```
and the auditor's scripts on the unfixed code (re-run, verbatim excerpt):
```
CFG-B with the null PROJECT_INPUT entries DELETED: ['beam_azimuth_uvw', 'glancing_angle_ext_mrad', 'convergence_semi_angle_mrad', 'objective_aperture_semi_angle_mrad', 'image_pixel_size_nm', 'reference_trajectory', 'pattern_geometry', 'surface_preparation_details']
   run level -> PASS; missing_project_inputs = [] ; status = experiment
CFG-B with glancing angle 16.47 mrad and convergence 0.0 mrad as ASSUMPTION, no 'item' key -> run level PASS; item recorded: None None
duplicate 'value:' key in one parameter mapping -> [1, 1, 0] (no error; label still PROJECT_INPUT , item 8 )
duplicate parameter name appended at the end of CFG-A -> run level PASS, V0 = 14.0
   labels of repository defaults: {'surface_material': 'PROJECT_INPUT', 'surface_normal_hkl': 'PROJECT_INPUT', 'beam_azimuth_uvw': 'PROJECT_INPUT'}
surface_material='silicon': forbidden target (6,-6,6) and a false 'forbidden' list ACCEPTED at run level
surface_material='Si ': forbidden target (6,-6,6) and a false 'forbidden' list ACCEPTED at run level
```
After: `28 passed`; full suite `454 passed`.
Not done: the registry still has no fields for docs/06 items 2, 6, 10, 16, 17, 19, 21, 22 (dose,
carrier, sign conventions, processing choices); CFG-A's imaging inputs (items 3, 4, 5, 7, 15) are
optional in its schema because the CFG-A benchmark does not use them (a hologram simulation of
CFG-A must declare them; `value()` refuses an absent one); `pattern_geometry` is a free mapping
whose inner units are not checked.

### m1: zero empty-hologram sideband, validity mask (`reconstruction/sideband.py`, `optics/hologram.py`)

Fix: `reconstruct_sideband(..., empty_amplitude_threshold=...)` must be declared (0 <= t < 1,
relative to the median |empty sideband|) with `divide_empty` and refused otherwise. Pixels with
|w_empty| <= t x median (exact zeros always) get NaN phase and amplitude; with "none", exact zeros
of the object sideband likewise; a RuntimeWarning states the count. `SidebandResult.valid_mask`
(read-only) = amplitude validity AND the R2 `valid_mask` of the object/empty hologram metadata;
`parameters["validity"]` records threshold and counts. `unwrap_itoh_raster(phase, valid)` starts at
the first valid pixel of column 0 and returns NaN where its path meets an invalid pixel (identical
to the old result for all-valid input, asserted); `fit_phase_plane` refuses non-finite pixels in
its region. `ensemble_hologram_intensity` carries the AND of the realisations' `valid_mask`;
`apply_poisson_noise` deep-copies metadata (also the NIT on shared state). The S1c statement
"(gives NaN)" is now what the code does.
Existing call sites with `divide_empty` declare `EMPTY_THRESHOLD = 0.1` (TEST_ONLY, holo_cases.py;
no synthetic empty hologram comes near it; T24/T25 still match the calculator to 1e-9 rad) and the
q2 script declares 0.1 (output unchanged).
Tests: `tests/reconstruction/test_validity_mask.py` (new, 7 tests).
Before: `7 failed` (`DID NOT WARN` x3, `DID NOT RAISE ValueError` x2, `TypeError: reconstruct_sideband()
got an unexpected keyword argument 'empty_amplitude_threshold'` x2, the ensemble mask assertion);
auditor's e7/e9 on the unfixed code (verbatim excerpt):
```
fringe-free 'empty' hologram: |empty sideband| max 0, corrected phase finite fraction 1.00, NaN fraction of unwrapped 0.00, no warning raised
DEBUG: corrected w sample:  wrapped_phase sample [0.78539816 0.78539816 0.78539816] amplitude sample [inf inf inf]
R2 valid_mask kept in: single hologram True | ensemble False | noisy copy True
   carries the R2 valid mask: False
```
After: `7 passed`; full suite `461 passed`.

### m7: remaining silent acceptances in the hologram chain (`optics/hologram.py`, `reconstruction/sideband.py`)

Fix: `ensemble_hologram_intensity` requires an integer realisation index on every wave when more
than one pair is given; `reconstruct_sideband` refuses a carrier located on an object hologram
unless `trap_demonstration=True` (done with M1); `reference_r3_curved_tilted` requires and records
`aperture_passage` (same choices as R1). Callers of R3 in two tests updated (argument only).
Tests: `tests/optics/test_m7_acceptances.py` (new, 3 tests).
Before: `2 failed, 1 passed` (`Failed: DID NOT RAISE ValueError` for the mis-paired ensemble,
`Failed: DID NOT RAISE TypeError` for R3); the trap test already passed because the refusal was
added with M1; on the fully unfixed code e9 printed `mis-paired ensemble with realisation=None
accepted: n_realisations = 2` and `reconstruct_sideband with a carrier located on the OBJECT
hologram: accepted`. After: `3 passed`; full suite `464 passed`.
Not fixed (NOT IMPLEMENTED, as the audit states): the R1/R3 aperture passage is recorded but does
not change the field, and the intrinsic 2 theta_ext inclination of a vacuum reference and its
compensation are not modelled (docs/05 5.3; needs PROJECT_INPUT items 15, 16).

### m2: zero uncertainties bypass the small-denominator refusal (`quantification/height.py`)

Fix: `height_from_phase` refuses a zero sensitivity first (SmallDenominatorError), then requires
every uncertainty (sigma_phi, sigma_theta_in, sigma_theta_out, sigma_wavelength_rel) finite and > 0
and sigma_phi < pi (ValueError); `sensitivity_uncertainty_rad_per_A` requires > 0 too. Also the
NITs on the wrapped range (now strictly (-pi, pi]) and on the wavelength (finite, > 0, in every
height function). Not adopted: the audit's example "refuse when sigma_h >= h_2pi/2", because with
an externally resolved branch a large height has a legitimately large sigma_h (1 % angle
calibration at h = 10 nm gives 1 A > h_2pi/2); sigma_h is reported instead.
Existing test changed (input only): `test_quant_height.py::test_small_denominator_boundary` used
`sigma_wavelength_rel=0.0`, now 1e-6 (the module's TEST_ONLY value; its assertions unchanged).
Tests: `tests/quantification/test_quant_height_refusals.py` (new, 29 cases).
Before: `15 failed, 14 passed` (`Failed: DID NOT RAISE ValueError` x12, a `ZeroDivisionError: float
division by zero`, and the negative wavelength reported as `sensitivity |q.n_hat| = -10.0206 rad/A is
not larger than its propagated uncertainty ...`); e8 on the unfixed code: `theta = 1e-09 rad, all
sigmas 0: h = -9.979e+05 A, sigma_h = 0, wrap period 1.25e+07 A (no refusal)`, `sigma_phi = 5 rad
(> pi) accepted: h = -0.0499 +- 0.4990 A`, `wrapped phase -3.141592653589793 accepted`.
After: `29 passed`; full suite `493 passed`.

### m3: B4 metadata at <100>; m6: hard-coded lattice parameter; NIT boundary step (`structure/si001.py`)

Fix m3: `b4_statement(kind, azimuth_uvw, incidence_plane_operations)` sets
`relation.model_assumption_B4` from the measured relation: a/2 "applies far from the riser (pure
translation)"; a/4 at an exact <100> azimuth with the incidence-plane glide measured "B4 applies for
bulk-terminated terraces (d-glide in the incidence plane; SM26, C2)"; at <110> "does not apply
(dynamical residual delta; open question 3)"; any other azimuth, or <100> without the measured glide,
"does not apply". Module docstring and `incidence_plane_mirror_note` updated. CFG-B `description` and
`step_translations.single_layer.relation` now say the same (4_1/4_3 screws and <100> d-glides; B4 at
<100> for bulk-terminated terraces; not at <110>).
Fix m6: `build_si001_terraces` requires `lattice_parameter_A` and `lattice_parameter_label`
(evidence label checked; recorded as `metadata.lattice.a_A/a_label`); `A_SI_A` is no longer
imported by si001.py and the `a_A=A_SI_A` defaults of `validate_staircase`, `assert_step_heights`,
`is_diamond_symmetry`, `find_terrace_relations`, `classify_relation` are removed.
NIT: `validate_staircase` refuses a non-integer (or bool) `boundary_step_layers`.
Callers updated (arguments only): `tests/structure/si001_test_inputs.py::build` passes
`A_SI_A, "ASSUMPTION B2"`; `test_si001_options.py::_kwargs` (so the "every argument is required"
test now also covers the two new arguments); `test_si001_assertions.py` passes `A_SI_A`;
`tools/physics_checks/q1_si001_quarter_step_symmetry.py` passes them (output identical to C2's run,
41/41).
Tests: `tests/structure/test_si001_audit_fixes.py` (new, 14 cases).
Before: collection error `ImportError: cannot import name 'LATTICE_LABEL' from 'si001_test_inputs'`;
the auditor's scripts on the unfixed code: `92 x [100]-family a/4 step recorded as 'B4 does NOT
apply' although an incidence-plane glide exists`; `validate_staircase with boundary_step_layers =
-1.5 -> [(1, False), (-1, True)]` then `builder then fails late with: (e) measured step at the
periodic cell edge -1.357725000 A != declared -2.036587500 A`; `build_si001_terraces takes a_A? ->
False ; validate_staircase default a_A = 5.4309`. After: `14 passed`; full suite `509 passed`.

### m8: provenance (`provenance/manifest.py`, `structure/xyz.py`, `io/validate_configs.py`, `tests/conftest.py`)

Fix: `git_state` records, when the tree is dirty, `diff_head_sha256` (SHA-256 of `git diff HEAD
--binary`) with the dirty flag, and `untracked_files` plus `untracked_sha256` (path + NUL +
SHA-256(content) of each). `build_manifest` refuses (RuntimeError) when git cannot be run, unless
`allow_no_git=True`, which is recorded; the thread count is checked against OMP/OPENBLAS/MKL/
NUMEXPR variables and the result recorded (`threads.check`: "not set ...", "consistent ...",
"MISMATCH ..."; recorded, not enforced, since numpy's BLAS is initialised at import); the bare
`assert` became an explicit raise (NIT). Every public entry point that writes output writes a
manifest: `write_xyz(structure, path, *, outputs_root)` and `write_metadata_json(...)` (new required
`outputs_root`; manifest records the file's SHA-256, builder, lattice parameter and labels) and
`validate_configs.main(argv, *, outputs_root)` (the command line keeps the repository's outputs/
unless `--outputs DIR`). `tests/conftest.py` gains a session guard that fails the session if
the repository's outputs/ changes.
Tests: `tests/provenance/test_prov_manifest_audit.py` (new, 5 tests: a throw-away git repository in
tmp_path with a tracked change and an untracked file; git unavailable; thread check; both structure
writers; validate_configs into tmp_path with outputs/ compared before and after);
`tests/structure/test_structure_xyz.py` passes `outputs_root=tmp_path/"outputs"`.
Before: `4 failed, 1 error` then, with the fixture moved, `5 failed`: `KeyError: 'diff_head_sha256'`,
`Failed: DID NOT RAISE RuntimeError`, `KeyError: 'check'`, `TypeError: write_xyz() got an unexpected
keyword argument 'outputs_root'`, `TypeError: main() got an unexpected keyword argument
'outputs_root'`. After: `5 passed`; full suite `514 passed`.

### m9: test gaps of docs/05 section 8

New tests (the finding is missing tests, so the "before" state is shown by running each new test
against a deliberately mutated package, restored afterwards; md5 of the three files checked):
* `tests/quantification/test_kinematic_sign.py` (8 cases): step phase from an explicit first-Born
  sum over atoms of `build_si001_terraces` (120 layers, attenuation 10 A, wavevectors written out in
  the test) against the signed relation `-|q.n_hat| h` of `quantification.height` and its inversion
  (branch from the a/4 lattice constraint); a/2 and a/4, up and down, [110] and [100]; tolerance
  1e-6 rad from the 8e-8 truncation tail; the opposite sign is asserted to differ by > 0.1 rad.
  Mutant `h = phi / s` in height.py: `8 failed`.
* `tests/reconstruction/test_resolution_and_ensemble.py::test_measured_resolution_versus_mask_radius`:
  measured 10-90 % width of a 0.05 rad step for R = |q|/3, /4, /6, /8, top-hat and Hann, against the
  independent 1-D step-response constants c = 0.44582 (top-hat) and 0.97027 (Hann); bound
  |wR/c - 1| <= 1/(nR - 1) + 2.5e-3 (bin quantisation). Measured wR: top-hat 0.4529, 0.4473, 0.4341,
  0.4532; Hann 0.9704, 0.9700, 0.9702, 0.9701; 1/R (reported resolution) is at least the measured
  width for both windows. Mutant "mask uses 2R": `1 failed, 1 passed`.
* `...::test_ensemble_converges_with_the_number_of_realisations`: K = 4 ... 1024 realisations with a
  reference jitter N(0, 0.8^2) and a phase common to both branches, seed 20260922; contrast -> 0.72615
  and phase -> 0.5 rad within 4 standard errors (K = 1024: 0.72875 and 0.52446 rad). Mutant "average
  the complex waves, then square": fails (contrast 0.18498 instead of 0.37757 at K = 4). A first
  version without the common phase did NOT catch that mutant (the sideband is linear in the
  reference), so the common phase was added before recording.
Full suite after m9: `526 passed`.
Not added (reason): sensitivity of the height to convergence and V0 (no convergence model exists;
the V0 sensitivity is in tools/phase1_numbers.py); data-handling loader tests (no data loader
exists); Fresnel-fringe and drift options (NotImplementedError, asserted by an existing test).

### NIT findings

| NIT | Fix / reason | Test | Before -> after |
|---|---|---|---|
| -pi accepted in height.py and rocking.py | range now strictly (-pi, pi] (height.py, rocking.py) | `test_quant_height_refusals.py::test_wrapped_phase_range_is_minus_pi_exclusive_to_pi` | DID NOT RAISE -> pass |
| SpecularCondition clips n lambda/2d > 1 | refuses when K_int > k_int (specular.py) | `tests/geometry/test_geom_nits.py::test_order_beyond_backscattering_is_refused` | DID NOT RAISE -> pass |
| accessibility `>=` vs SpecularCondition `>` at equality | NOT FIXED: docs/physics_conventions.md states `G.n_hat >= 2 dK`; making both strict (theta_ext = 0 is no vacuum beam) needs that line changed first (orchestrator) | none | - |
| `int(boundary_step_layers)` truncates -1.5 | integrality checked (si001.py) | `test_si001_audit_fixes.py::test_boundary_step_must_be_an_integer` | collection error / e12b truncation -> pass |
| bare `assert` in frames.py, manifest.py | explicit raises | `test_geom_nits.py::test_no_bare_assert_in_the_package` | `['reflection_holo/geometry/frames.py:68', ...]` -> pass |
| shallow metadata copy in apply_poisson_noise | deep copy (with m1) | `test_validity_mask.py::test_r2_valid_mask_reaches_the_result_through_ensemble_and_noise` | failed -> pass |
| wavelength not validated in quantification | finite and > 0 required (height.py, rocking.py) | `test_quant_height_refusals.py::test_wavelength_is_validated` | wrong error type -> pass |

## Summary table (finding, fix, regression test, before -> after)

| Finding | Fix (file:line at the end of this work) | Regression test | Before -> after |
|---|---|---|---|
| B1 rocking branch | `quantification/rocking.py:152` `resolve_rocking_series` (noise guard :202, WLS :217, B16 :225-237, sigma_h :245, chi-square :250) | `tests/quantification/test_quant_rocking_noise.py` | TypeError; e10: 891 wrong heights accepted -> 0 wrong, all auditor regimes refused |
| M1 conjugate sideband | `reconstruction/sideband.py:88` `CarrierSearch` (half-plane :118), Hermitian pairs :239, trap :513, CONJUGATE :538 | `tests/reconstruction/test_sideband_selection.py` | 43 failed; e4: -0.500 rad -> 43 passed |
| M2 config gate | `io/config.py:138` `SCHEMAS`, item rule :425, stands-in rule :433, absent = null :560, duplicate keys :601 | `tests/io/test_io_config_gate.py` | ImportError; e5: 5 bypasses PASS -> 28 passed |
| m1 NaN + validity mask | `reconstruction/sideband.py:518-580` (threshold :561), unwrapper :330, plane fit :397; `optics/hologram.py:339` ensemble mask, :374 deep copy | `tests/reconstruction/test_validity_mask.py` | 7 failed -> 7 passed |
| m2 zero uncertainties | `quantification/height.py:59-72`, zero sensitivity :163, sigma_phi < pi :168 | `tests/quantification/test_quant_height_refusals.py` | 15 failed -> 29 passed |
| m3 B4 metadata | `structure/si001.py:359` `b4_statement`; `configs/cfg_b_si001_patterned.yaml:91` | `tests/structure/test_si001_audit_fixes.py` | e12: 92 wrong labels -> 14 passed |
| m4 CFG-A labels | `configs/cfg_a_si111_cleaved_110azimuth.yaml:20-36`; `io/config.py:417` | `test_io_config_gate.py::test_cfg_a_repository_defaults_are_labelled_assumption` | PROJECT_INPUT -> ASSUMPTION |
| m5 units | `io/config.py:92` `UNITS`, :355 `_check_unit`, :266 `quantity()` | `test_io_config_gate.py::test_units_*`, `test_unknown_or_wrong_unit_fails` | no conversion -> nm->A, mrad->rad |
| m6 lattice parameter | `structure/si001.py:452` (label check :480) | `test_si001_audit_fixes.py::test_lattice_parameter_is_an_explicit_labelled_argument` | hard-coded -> explicit, labelled |
| m7 acceptances | `optics/hologram.py:311` pairing, :164 R3 aperture; `sideband.py:513` trap carrier | `tests/optics/test_m7_acceptances.py` | 2 failed (trap fixed with M1) -> 3 passed |
| m8 manifests | `provenance/manifest.py:59` `git_state`, :89 thread check, :179 git refusal; `structure/xyz.py:34`; `io/validate_configs.py:21`; `tests/conftest.py` | `tests/provenance/test_prov_manifest_audit.py` | 5 failed -> 5 passed |
| m9 test gaps | tests only | `test_kinematic_sign.py`, `test_resolution_and_ensemble.py` | mutants: 8 failed, 1 failed, failed |
| m10 material names | `io/config.py:313` canonical symbol per schema | `test_io_config_gate.py::test_non_canonical_*`, `test_cfg_o_material_must_be_pt` | e5b accepted -> refused |
| NITs | see the NIT table | see the NIT table | 6 fixed, 1 not (docs conflict) |

## Proposed model assumption B16 (for the orchestrator to add to docs/model_assumptions.md)

| B16 | A rocking series gives the absolute 2 pi branch of a lattice-translation step only when the branch is resolved at 3 sigma: (i) for every consecutive pair of tilts, `(2 pi/lambda) h_max |s_(i+1) - s_i| + 3 sqrt(sigma_i^2 + sigma_(i+1)^2) < pi` (`s = sin theta_in,ext + sin theta_out,ext`, `sigma_i` the declared phase uncertainty of each hologram, `h_max` the prior bound on `|h|`); (ii) the weighted least-squares fit `Delta_phi = -(2 pi/lambda) h s + c` with a free intercept gives `sigma_c < pi/3` and `n = round(c/2 pi)` with `|c - 2 pi n| < pi`; (iii) model checks `|c - 2 pi n| <= 3 sigma_c` and chi-square `p >= 1e-3` with the declared `sigma_i`. Otherwise the branch is reported as unresolved and no absolute height is returned; `sigma_h` is the fit covariance given the branch, reported with `sigma_c` and `P(|Z| > pi/sigma_c)`. | ASSUMPTION (Gaussian, independent phase errors with correctly declared `sigma_i`; a single lattice-translation height; `|h| <= h_max`); the criterion and its error rate are DERIVED_HERE (S3) | Wrong-branch probability among accepted results below `P(|Z| > 3) = 2.7e-3` (Monte Carlo, seed 20260922: 0 wrong of 3987 accepted in two regimes). Narrow tilt ranges (a few mrad near 20 mrad) are refused at 0.05 rad noise (`sigma_c` = 1.3 rad for 5 tilts over 1 mrad). Violated by non-Gaussian or underestimated errors (partly caught by the chi-square check), by a dynamical residual or a screw-related a/4 step at <110> (caught by the intercept check only if larger than `3 sigma_c`), and by `|h| > h_max` (aliasing, not detectable). |

## Left unfixed, with reason

* NIT accessibility equality (`>=` in `geometry/accessibility.py`, `>` in `SpecularCondition`): the
  fix needs docs/physics_conventions.md ("G.n_hat >= 2 dK") changed first.
* m7: R1/R3 aperture passage recorded but inert; intrinsic 2 theta_ext inclination and its
  compensation not modelled (NOT IMPLEMENTED; PROJECT_INPUT items 15, 16).
* m8: thread count is checked and recorded, not enforced.
* m9: V0/convergence sensitivity tests, data-loader tests (no loader), Fresnel and drift options.
* M2: no configuration fields yet for docs/06 items 2, 6, 10, 16, 17, 19, 21, 22; CFG-A imaging
  inputs optional; `pattern_geometry` inner units unchecked. CFG-B label decision (DERIVED_HERE for
  (008), (0,0,12), step_types) awaits confirmation, or rows B17/B18.
* docs/agent_reports/S1c (says validity masking is NOT IMPLEMENTED) and C2's appendix A.2 (the D2
  line of q2) are now out of date; not edited (docs/ restriction).

## Final runs (verbatim)

```
$ venv/bin/pytest -q
........................................................................ [ 95%]
.......................                                                  [100%]
527 passed in 12.04s
$ venv/bin/python tools/reflection_step_phase_calculator.py | tail -3
====================================================================================================
END OF OUTPUT
====================================================================================================
$ venv/bin/python tools/reflection_step_phase_calculator.py | grep "checks pass"
   25/25 checks pass in this script itself.
$ venv/bin/python tools/phase1_numbers.py | tail -1
   17/17 checks pass
$ venv/bin/python tools/physics_checks/q1_si001_quarter_step_symmetry.py | tail -1   (q2, q3 likewise)
   41/41 self-checks pass
   21/21 self-checks pass
   7/7 self-checks pass
```
Not committed, not pushed. NOT RUN: `python -O` (no `assert` statements remain; asserted by a test);
any multislice, dynamical or engine run (none exists); experimental data (none available).
