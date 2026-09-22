# A2: Phase 2 code audit of `reflection_holo` (package, tests, configs, tools/phase1_numbers.py)

Status: COMPLETE, 2026-09-22 (written incrementally). Agent A2 (code auditor). Only this file
was written; no code, test, config or document was modified. Scratch scripts live outside the
repository in `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/audit/`.

Audited state: branch `claude/electron-holography-orchestration-nakd7r`, HEAD `7874c85` (the scope
files are identical to `1c98826`; `git diff --quiet -- reflection_holo tests configs
tools/phase1_numbers.py tools/reflection_step_phase_calculator.py` is clean). Aggregate SHA-256 of
the scope files (`find ... | sort | xargs sha256sum | sha256sum`):
`997d5d5b2e8142ac5947bb02e5588572cd7e94ca2483768b09e462d66050d8ff`. Other agents (C2) were writing
under `tools/physics_checks/` and `docs/agent_reports/C2_*` during the audit; those are out of scope.

## Files read completely

Package: `reflection_holo/__init__.py`, `constants.py`, `geometry/{errors,wavelength,frames,crystal,
refraction,specular,accessibility,projection,sampling,plate_cell,__init__}.py`,
`quantification/{errors,height,noise,invisibility,rocking,controls,shadow,__init__}.py`,
`io/{config,labels,validate_configs,__init__}.py`, `provenance/{manifest,__init__}.py`,
`optics/{fields,hologram,__init__}.py`, `reconstruction/{sideband,__init__}.py`,
`structure/{lattice,checks,si001,shadows,xyz,__init__}.py`.
Configs: `configs/cfg_a_si111_cleaved_110azimuth.yaml`, `cfg_b_si001_patterned.yaml`,
`cfg_o_osakabe_1988_reproduction.yaml`.
Reference: `tools/reflection_step_phase_calculator.py` (all 1168 lines), `tools/phase1_numbers.py`.
Docs: `docs/05_final_repository_specification.md` (all), `docs/physics_conventions.md`,
`docs/model_assumptions.md`, `docs/06_project_inputs_required.md`, build reports S1a, S1b, S1c, S2,
and C2 (context only).
Tests: see section "Tolerance integrity" (every file under `tests/`).

## Summary

1 Blocker, 2 Major, 10 Minor, 7 Nit. The test suite (374 passed), the calculator (25/25) and
`tools/phase1_numbers.py` (17/17) all pass. Every T1-T25 test uses exactly the calculator's reference value and
tolerance; none is looser. The core physics was reproduced independently and is correct. That covers the
exp(+ik.r) signed step phase against an explicit Born sum over built atoms, the signed inverse through the
whole hologram chain for up- and down-steps, relativistic Delta and theta_c, the internal and external angles,
the guards, the wrap period, the shadow and blocked-view strips against a brute-force ray trace, the FFT sign,
and phi_o - phi_r. The defects are in how the code is protected against realistic inputs:

* B1: the rocking-series inversion accepts wrong 2 pi branches (wrong absolute heights by one or more h_2pi)
  with a sigma_h about 100 times too small, in up to 28 % of noisy trials (3 to 28 % across four plausible
  regimes; `audit/e10`).
* M1: a carrier search disc that contains both sidebands silently picks the conjugate by array order, flipping
  the sign of the phase and the height. docs/model_assumptions B15 now says this is refused; the code does not
  refuse it.
* M2: the run-level PROJECT_INPUT gate fails only for present-and-null entries. Omitting the entry, an
  ASSUMPTION value without an item, or a duplicate YAML key passes (acceptance criterion 5).
* Minor: silent pi/4 phase for a zero empty-hologram sideband and no validity mask (m1); the zero-uncertainty
  bypass of the small-denominator refusal (m2); "B4 does NOT apply" recorded at <100>, contrary to C2 and the
  updated docs (m3); CFG-A defaults labelled PROJECT_INPUT (m4); nm/mrad configurations against A/rad code with
  no adapter (m5); hard-coded lattice parameter (m6); pairing, trap-carrier and R3-aperture acceptances (m7);
  manifest gaps (m8); test gaps (m9); a material spelling that bypasses the Si cross-checks (m10).

(Findings follow below, ranked; the command log is at the end.)

## Findings, ranked

Scratch scripts cited as `audit/<name>.py` live in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/audit/` and were run with
`/home/user/Holography/venv/bin/python <name>.py`. Outputs are quoted verbatim (trimmed where marked).

### BLOCKER

#### B1. The rocking-series inversion returns wrong absolute heights with a confident, far too small sigma_h

* Where: `reflection_holo/quantification/rocking.py:91-92` (tilt-step guard), `:97` (`np.unwrap`), `:99-106`
  (free intercept, integer test), `:114` (sigma_h).
* What is wrong. (1) The tilt-step guard `kfac * h_max * max|Delta s| < pi` ignores the phase noise, so
  `np.unwrap` slips a 2 pi whenever increment plus noise exceeds pi. (2) The branch integer `M` is taken from a
  free intercept extrapolated from the tilt range to `s = 0`. Its standard error is
  `sigma_phi * sqrt(1/N + s_mean^2 / sum((s - s_mean)^2))`, i.e. 10 to 30 times `sigma_phi` for a range of a few
  mrad around 20 mrad. The code neither computes that error nor refuses when it is comparable to 0.5 cycle; it
  only tests `|c/2pi - M| <= max_intercept_offset_cycles`, which a random intercept passes about half the time.
  (3) `sigma_h` is computed from the residuals after `M` is fixed, so a wrong `M` or an unwrap slip still gives
  a tiny `sigma_h`. There is no `sigma_phi` input, so no chi-square check against the expected noise.
* Why it matters. docs/05 section 5 item 8 makes rocking-series inversion the route to absolute heights, and
  section 0 criterion 1 requires quantified heights with uncertainties. A wrong `M` shifts the height by a whole
  multiple of `h_2pi` (0.6 A at 20 mrad), which is larger than the Si(001) a/4 step itself. The reported
  uncertainty is about 100 times too small, so the error cannot be seen downstream.
* Reproduction: `audit/e10_rocking_branch.py`. True h = +10 A, 200 keV, specular, 2000 noise draws per row.
  ```
  tilts 20.0-21.0 mrad step 0.25 (5), noise 0.05 rad: intercept s.e. 0.21 cycles -> correct 1552, WRONG h accepted 1, refused 447 (of 2000); wrong h values e.g. [10.6] A with reported sigma_h median 0.002 A
  tilts 20.0-21.0 mrad step 0.25 (5), noise 0.1 rad: intercept s.e. 0.41 cycles -> correct 889, WRONG h accepted 136, refused 975 (of 2000); wrong h values e.g. [ 9.4 10.6] A with reported sigma_h median 0.004 A
  tilts 20.0-21.0 mrad step 0.25 (5), noise 0.2 rad: intercept s.e. 0.83 cycles -> correct 468, WRONG h accepted 567, refused 965 (of 2000); wrong h values e.g. [ 8.2  8.8  9.4 10.6 11.2 11.8] A with reported sigma_h median 0.007 A
  tilts 20.0-25.0 mrad step 0.5 (11), noise 0.2 rad: intercept s.e. 0.14 cycles -> correct 1642, WRONG h accepted 133, refused 225 (of 2000); wrong h values e.g. [3.4 3.8 4.  4.4 4.7 5.8] A with reported sigma_h median 0.045 A
  tilts 16.0-17.0 mrad step 0.25 (5), noise 0.1 rad: intercept s.e. 0.33 cycles -> correct 1068, WRONG h accepted 54, refused 878 (of 2000); wrong h values e.g. [ 9.2 10.7 10.8] A with reported sigma_h median 0.005 A
  ```
  The 11-tilt row is the unwrap-slip mode: the guard passes (2.63 rad < pi), noise pushes single increments over
  pi, and heights 4 to 6 A off are returned with sigma_h = 0.045 A. The existing test
  (`tests/quantification/test_quant_rocking.py:56`, one seed, 21 tilts over 5 mrad, 0.05 rad) never enters
  either regime.
* What a fix needs: a required `sigma_phi_rad` input. Put a noise margin in the tilt-step guard (for example
  `max_inc + k * sqrt(2) * sigma_phi < pi`). Compute the intercept standard error and refuse, raising
  BranchAmbiguityError, unless it is well below 0.5 cycle (for example 5 sigma). Refuse when the residual
  chi-square is inconsistent with `sigma_phi`. Propagate the branch uncertainty into the result, or report the
  alternative branches. Add a Monte Carlo test like the one above that asserts no silently wrong height.

### MAJOR

#### M1. The carrier locator can select the conjugate sideband, contradicting the declared guess (silent sign flip of phase and height)

* Where: `reflection_holo/reconstruction/sideband.py:92-93` (any search radius is accepted, including inf),
  `:196-197` (search disc), `:204` (argmax with fftshift tie-break), `:394-403` and `:465` (`_sign_check` only
  records a string).
* What is wrong. |F(q)| = |F(-q)| for a real hologram, so when the declared disc contains both the guess `-q_ref`
  and its conjugate `+q_ref` (radius >= 2|guess|, or inf, which the docstring advertises as "whole plane"),
  the chosen bin is decided by array order, not by the declared guess. For simulated holograms the result
  records "CONJUGATE" but nothing raises. For experimental holograms (no recorded carrier) it records
  "unknown".
* Why it matters. The sideband decides the sign of `phi_o - phi_r` and therefore the sign of the height. An
  up-step becomes a down-step: the required sign test of docs/05 5.8, defeated downstream of the test. The only
  protection is the caller's choice of radius.
* Reproduction: `audit/e4_conjugate_sideband.py`. Flat object 0.7 rad, reference 0.2 rad (so +0.500 rad is
  expected), dose 1e3, guess always the correct `-q_ref`. Excerpt:
  ```
  q_ref=(0.0, -0.125), guess=(-0.0, 0.125), search radius=0.3: located sideband (0.0, -0.125), median phase -0.500 rad (want +0.500); experiment sign check: 'unknown: '; simulated sign check: 'CONJUGATE: p'
  q_ref=(0.0, -0.125), guess=(-0.0, 0.125), search radius=inf: located sideband (0.0, -0.125), median phase -0.500 rad (want +0.500); experiment sign check: 'unknown: '; simulated sign check: 'CONJUGATE: p'
  q_ref=(-0.125, 0.0), guess=(0.125, -0.0), search radius=inf: located sideband (-0.125, 0.0), median phase -0.500 rad (want +0.500); ...
  q_ref=(0.0625, -0.125), guess=(-0.0625, 0.125), search radius=0.3: located sideband (0.0625, -0.125), median phase -0.500 rad (want +0.500); ...
  ```
  With radius 0.06 (< |guess|) all five carrier directions give +0.500. With radius 0.3 or inf, three of the
  five give -0.500.
* Documentation now disagrees with the code. `docs/model_assumptions.md:39` (row B15, added in commit a01bc19
  while this audit was running) says a brightest-bin search "over both sidebands, is refused". The package
  does not refuse it.
* What a fix needs: refuse a search region that contains the conjugate point `-guess`, or restrict the search to
  the half plane `q . guess > 0`. Break ties by distance to the guess. Make a "CONJUGATE" sign check raise
  unless the caller explicitly opts in. Add a test with a wide search radius for all four carrier quadrants.
  (The trap demonstration in `tests/reconstruction/test_carrier_trap.py:34` relies on the whole-plane search;
  it can keep an explicit opt-in.)

#### M2. The run-level PROJECT_INPUT gate is passed by omitting a parameter, or by a silent YAML override (acceptance criterion 5)

* Where: `reflection_holo/io/config.py:365-385`. The gate lists only parameters that are present with a null
  value; no per-configuration set of required parameters exists (`PARAMETERS`, `:63-91`, is a registry of
  allowed names, not required ones). `:253-260`: the docs/06 item is enforced only when `item` is given.
  `:408`: `yaml.safe_load` silently keeps the last of duplicate keys.
* What is wrong. (a) Deleting the eight null PROJECT_INPUT entries of CFG-B turns a refused run into a PASS.
  (b) A blocking input can be filled with an unlinked ASSUMPTION value (no `item`), e.g. glancing angle
  16.47 mrad or convergence 0.0 mrad, and the run PASSES with `item = None`. (c) A duplicated `value:` key, or
  a parameter repeated later in the file, overrides silently, so a null PROJECT_INPUT keeps its label and item
  but acquires a value. (d) The shipped CFG-A passes at run level although it has no glancing-angle,
  convergence, aperture, pixel-size or reference field. A CFG-A fixture with three parameters also loads at run
  level (`tests/provenance/test_prov_manifest.py:17-22`).
* Why it matters. docs/05 section 0 criterion 5 ("no default silently substitutes a missing PROJECT_INPUT;
  such runs fail") is implemented only as "present and null fails". The CFG-B header promises that the
  run-level load fails and names items 3, 4, 5, 7, 8, 12, 13 and 15. That holds only while the null lines stay
  in the file. Omitting a line is the easiest way to lose an input, and downstream code will need a value from
  somewhere.
* Reproduction: `audit/e5_config_gate.py`:
  ```
  shipped CFG-B at run level: MissingProjectInputError -> CFG-B: run-level load refused, missing PROJECT_INPUT (docs/06_project_inputs_required.md): item 3 (convergence ...
  CFG-B with the null PROJECT_INPUT entries DELETED: ['beam_azimuth_uvw', 'glancing_angle_ext_mrad', 'convergence_semi_angle_mrad', 'objective_aperture_semi_angle_mrad', 'image_pixel_size_nm', 'reference_trajectory', 'pattern_geometry', 'surface_preparation_details']
     run level -> PASS; missing_project_inputs = [] ; status = experiment
  CFG-B with glancing angle 16.47 mrad and convergence 0.0 mrad as ASSUMPTION, no 'item' key -> run level PASS; item recorded: None None
  duplicate 'value:' key in one parameter mapping -> [1, 1, 0] (no error; label still PROJECT_INPUT , item 8 )
  duplicate parameter name appended at the end of CFG-A -> run level PASS, V0 = 14.0
  ```
* What a fix needs: a required-parameter set per `config_id` (and per `status`) that fails at run level when a
  name is absent. Require `item` whenever a parameter has a docs/06 item in `PARAMETERS`, whatever the label,
  so that an ASSUMPTION standing in for a PROJECT_INPUT stays traceable. Use a YAML loader that refuses
  duplicate keys. Add tests for omission, relabelling and duplicates. Also note: the registry has no fields at
  all for items 2, 6, 10, 16, 17, 19, 21 and 22 (dose, carrier, reference residual, processing choices), so
  those cannot be declared or gated from a configuration yet.

### MINOR

#### m1. Division by the empty hologram hides zero or near-zero reference amplitude; the result carries no validity mask

* Where: `reflection_holo/reconstruction/sideband.py:444-445` (`np.errstate(divide="ignore", invalid="ignore")`),
  `:450` (Itoh unwrap over everything). The R2 `valid_mask` is kept in the hologram metadata
  (`reflection_holo/optics/hologram.py:283-284`) but is dropped by `ensemble_hologram_intensity` (`:317-322`)
  and never reaches `SidebandResult`.
* What is wrong. Where the empty sideband is exactly 0 the division gives `inf+inf j`, and `np.angle` returns a
  finite pi/4 everywhere; no NaN, no warning. S1c lists this as NOT IMPLEMENTED and says it "gives NaN", which
  is not what the code does. Near-zero regions (outside the biprism overlap, a dead detector area) give finite
  garbage phases with no flag, and the raster unwrapper walks through them.
* Reproduction: `audit/e7_divide_empty.py` (with `warnings.simplefilter("error")`):
  ```
  empty-sideband amplitude: overlap region median 1, outside-overlap rows median 0.0949
  corrected amplitude max 1; finite everywhere: True; any validity mask in the result: []
  fringe-free 'empty' hologram: |empty sideband| max 0, corrected phase finite fraction 1.00, NaN fraction of unwrapped 0.00, no warning raised
  DEBUG: corrected w sample:  wrapped_phase sample [0.78539816 0.78539816 0.78539816] amplitude sample [inf inf inf]
  ```
  `audit/e9_ensemble_pairing.py`: `R2 valid_mask kept in: single hologram True | ensemble False | noisy copy True`;
  `SidebandResult ... carries the R2 valid mask: False`.
* Fix: a declared, required amplitude threshold. Return a validity mask (amplitude threshold AND the R2 or
  shadow masks) in `SidebandResult`. Let the unwrapper and the fitters honour it. Propagate `valid_mask` through
  the ensemble and noise stages.

#### m2. The small-denominator refusal can be disabled by declaring zero uncertainties

* Where: `reflection_holo/quantification/height.py:73` and `:139` (0 accepted), `:149` (`if not s > sigma_s`).
* What is wrong. With every sigma set to 0, `sigma_s = 0`, so any `theta > 0` passes. At theta = 1e-9 rad the
  function returns h = -9.979e+05 A with sigma_h = 0. `sigma_phi` does not enter the refusal at all (the
  C report alternative `|q.n_hat|` against `sigma_phi/h` is not implemented; S1a open issue 5).
* Reproduction: `audit/e8_edges.py`:
  `theta = 1e-09 rad, all sigmas 0: h = -9.979e+05 A, sigma_h = 0, wrap period 1.25e+07 A (no refusal)`;
  `sigma_phi = 5 rad (> pi) accepted: h = -0.0499 +- 0.4990 A`.
* Fix: require strictly positive angle and phase uncertainties, or an explicit labelled "exact" flag for
  synthetic data. Include `sigma_phi` in the refusal criterion (for example refuse when `sigma_h >= h_2pi/2`).
  Refuse `sigma_phi >= pi`.

#### m3. Si(001) builder metadata states "B4 does NOT apply" for a/4 steps at the <100> azimuth, while the builder itself finds the incidence-plane glide that makes B4 apply there

* Where: `reflection_holo/structure/si001.py:562-564`. The label depends only on `kind`. The same record holds
  `incidence_plane_mirror_operations` (`:534-536`, `:557`).
* Why it matters. docs/agent_reports/C2 section 1.2-1.5 derives, and checks exhaustively on the truncated half
  crystals, that at an exact <100> azimuth the bulk-terminated a/4 terraces are related by the (010) d-glide,
  which leaves `k_in` and `k_out` invariant, so the geometric phase is exact there. The metadata that a
  downstream geometric-phase model would read to decide "screw-related terraces where the model is not valid"
  (docs/05 4.5) is therefore too pessimistic at <100>. It is correct at <110>.
* Reproduction: `audit/e12_structure_sweep.py`: `92 x [100]-family a/4 step recorded as 'B4 does NOT apply'
  although an incidence-plane glide exists` (144 of 144 valid staircases built; the other checks show no
  mismatch).
* Fix: make the B4 field depend on the measured incidence-plane operation and the azimuth, and state the
  bulk-termination and exact-azimuth caveats. Commit a01bc19 (during this audit) has since adopted C2 in
  docs/05 criterion 3 and the CFG-B row, model_assumptions B4 and docs/06 item 8, and its message records
  that "builder metadata and CFG-B config comment still say B4 does not apply at <100>". The code and
  `configs/cfg_b_si001_patterned.yaml` (description and `step_translations.single_layer.relation`) now
  disagree with the documents.

#### m4. CFG-A labels inherited repository defaults as PROJECT_INPUT

* Where: `configs/cfg_a_si111_cleaved_110azimuth.yaml:19, 23, 27` (`surface_material`,
  `surface_normal_hkl`, `beam_azimuth_uvw` carry the label `PROJECT_INPUT` and no docs/06 item).
* Why it matters. PROJECT_INPUT means supplied by the laboratory (docs/06). These are defaults of the inspected
  repository that define the CFG-A benchmark. The label propagates into manifests
  (`config.missing_project_inputs`, labels) and makes a default look like a lab-supplied input. This is the
  failure mode that criterion 5 tries to exclude, here done by the label.
* Fix: label them DERIVED_HERE, or with a benchmark-definition label, and cite docs/05 section 2 (CFG-A row).
  Together with M2, require `item` for every PROJECT_INPUT, null or not.

#### m5. Unit mix between configuration and code, with no conversion layer

* Where: `reflection_holo/io/config.py:78, 79, 81, 88` (`glancing_angle_ext_mrad`,
  `convergence_semi_angle_mrad`, `image_pixel_size_nm`, `height_sensitivity_nm`). Every library function takes
  rad and A (`Grid.pixel_size_A`, `theta_*_rad`).
* Why it matters. docs/physics_conventions.md line 21 says "Angstrom everywhere in code and metadata" and line
  17 says angles are "stored in radians". The configuration stores nm and mrad. No function converts a
  LoadedConfig into library arguments, so each future caller will convert by hand. A missed conversion factor
  of 10 in the pixel size or of 1000 in the angle can pass silently: `height_from_phase` validates only
  `[0, pi/2]`, `wavelength_A` is not range-checked, and `audit/e8_edges.py` shows a x10 wavelength with
  theta = 1.2 rad accepted (`h = -0.01071`). An angle passed in mrad (20.0) is refused, which is good.
* Fix: one tested adapter from LoadedConfig to typed, unit-converted arguments. Either amend the conventions to
  allow nm and mrad in configurations, or store A and rad there.

#### m6. The lattice parameter is hard-coded in the structure builder, and structure functions default it

* Where: `reflection_holo/structure/si001.py:435` (`a = float(A_SI_A)`), and the `a_A=A_SI_A` defaults at
  `:136, :191, :229, :267, :314`.
* Why it matters. `geometry/crystal.py` docstring lines 12-14 say the lattice parameter is "a required argument
  everywhere (no default)". The configurations carry `lattice_parameter_A` (ASSUMPTION B2), but a structure
  built for a configuration with another value (for example 5.431 A, the inspected repository's
  meta_tilt_examples value) silently uses 5.4309 A, although the metadata records it. It is not a
  PROJECT_INPUT; the impact on phases is negligible (1e-5, B2), but it is an unrecorded mismatch between the
  configuration and the built structure.
* Fix: make `a_A` a required labelled argument of the builder and remove the defaults.

#### m7. Remaining silent acceptances in the hologram chain

* `reflection_holo/optics/hologram.py:257` and `:311`: realisation pairing is enforced only when the indices are
  set. With `realisation=None` a mis-paired ensemble is accepted (`audit/e9_ensemble_pairing.py`: `mis-paired
  ensemble with realisation=None accepted: n_realisations = 2`). Fix: require integer indices when more than
  one pair is given.
* `reflection_holo/reconstruction/sideband.py:426`: `reconstruct_sideband` accepts a CarrierLocation obtained
  with `allow_object_hologram=True` (the trap). Only the record string shows it (`audit/e9`: `accepted;
  located_on = OBJECT hologram (brightest-bin trap, demonstration only)`). Fix: refuse unless an explicit
  opt-in is repeated.
* `reflection_holo/optics/hologram.py:161`: R3 is a vacuum-type reference but has no `aperture_passage`
  declaration, unlike R1 (`:103`). docs/05 5.3 requires the declaration for a reference that must pass the
  dark-field aperture.
* The R1 `aperture_passage` is recorded but does not change the field, and the intrinsic `2 theta_ext`
  inclination and its compensation are not modelled (declared in the module docstring and in S1c NOT
  IMPLEMENTED). Stated here because docs/05 5.3 calls them explicit inputs.

#### m8. Provenance: only the configuration validator writes a manifest; git failure and a dirty tree are recorded but not guarded

* Where: `reflection_holo/provenance/manifest.py:62` (`dirty` is a bool, with no diff or patch hash) and
  `:63-64` (an OSError or CalledProcessError from git is swallowed and the manifest is built with
  `commit=None`). `build_manifest`/`write_manifest` are called only from `reflection_holo/io/validate_configs.py:46,51`.
  No hologram, reconstruction or structure path writes one. The thread count is declared, not applied
  (`threads.requested`; the environment variables are all `None`).
* Why it matters. docs/05 section 6 says "every run writes a manifest ... git commit of the repository". A
  dirty-tree manifest (the state during this audit, `dirty: True`) does not identify the code that ran. The
  editable install reports `reflection_holo 0.0.1` whatever the code state.
* Reproduction: `audit/e16_manifest.py`: `repository: {'commit': '7874c85...', 'dirty': True, ...}`;
  `git unavailable -> manifest built anyway: {'commit': None, 'dirty': None, 'branch': None, 'error': 'OSError: git not found'}`.
* Fix: record `git diff HEAD` (and untracked-file list) SHA-256 when dirty. Refuse, or require an explicit
  flag, when git is unavailable. Wire the manifest into every run entry point once those exist. Set or check
  BLAS and OMP threads against `thread_count`.

#### m9. Test-suite gaps against docs/05 section 8 and tests that assert less than their names suggest

* No independent physical anchor for the sign of the step phase. `test_round_trip_recovers_signed_height`
  (`tests/quantification/test_quant_height.py:37`) inverts the package's own forward model, and
  `test_sign_down_step_reverses_the_sign` (`:45`) pins the sign against the convention formula, not against a
  scattering calculation. The calculator's translation check (section 11(a)) is not ported (S1a NOT RUN). My
  kinematic check (`audit/e2_sign_chain.py`, section "Verified correct") shows the sign is right; it should be
  a test.
* `test_resolution_reported_three_fringe_spacings` (`tests/reconstruction/test_sideband_processing.py:52-63`)
  checks that `resolution_A == 1/R` for `R = |q|/3`, which is the definition. docs/05 section 8 asks for
  "resolution versus mask radius", i.e. a measured one (for example the 10-90 % width of a reconstructed
  step against R). Not implemented (S1c lists it).
* Missing per docs/05 section 8: ensemble convergence with the number of configurations; sensitivity of the
  height to convergence and to V0 uncertainty (S1a NOT RUN); data-handling loader tests (dataset names, axis
  order, pixel size from file, tilt selection by value), because no data loader exists; Fresnel-fringe and
  drift options (NotImplementedError); the M2/M3 failure modes above (rocking noise regime, wide carrier
  search, configuration omission).
* T5 and T23 evaluate a different expression from the calculator's `chk()`. T5 uses the internal escape angle
  `dK/k_int`, T23 uses `lambda/(4 h cos theta)`. Both are documented and both pass within the unchanged
  calculator tolerance. See the tolerance table.

#### m10. A free-text `surface_material` silently disables the Si crystallographic cross-checks of a configuration

* Where: `reflection_holo/io/config.py:298` (`if val("surface_material") != "Si": return`). The kind is a free
  string (`:64`), and nothing ties CFG-A or CFG-B to silicon.
* What is wrong. Writing "silicon" or "Si " (trailing space) in CFG-A skips the forbidden-reflection guard, the
  accessibility check and the "listed as forbidden but F != 0" check. A forbidden target (6,-6,6) and a false
  forbidden list then load at run level.
* Reproduction: `audit/e5b_material_bypass.py`:
  ```
  surface_material='Si': refused -> CFG-A: (4, -4, 4) is listed as forbidden but F != 0
  surface_material='silicon': forbidden target (6,-6,6) and a false 'forbidden' list ACCEPTED at run level
  surface_material='Si ': forbidden target (6,-6,6) and a false 'forbidden' list ACCEPTED at run level
  ```
  A later `specular_condition_for` call would still refuse (6,-6,6), which limits the damage, but the
  configuration gate is the check that docs/05 4.1 and the S1a report rely on.
* Fix: an enumerated material field, with `surface_material == "Si"` required for CFG-A and CFG-B (and "Pt"
  for CFG-O).

### NIT

* `reflection_holo/quantification/height.py:132` and `reflection_holo/quantification/rocking.py:78` accept
  -pi (and |w| up to pi + 1e-12) although the documented range is (-pi, pi]. `audit/e8`:
  `wrapped phase -3.141592653589793 accepted ... h = 0.31351 A`. Harmless for the height (the branch index
  absorbs it) but inconsistent with `wrap_to_pi`, which maps -pi to +pi.
* `reflection_holo/geometry/specular.py:80, 85`: `np.clip` silently maps an order beyond backscattering
  (`n lambda/2d > 1`) to theta_int = theta_ext = pi/2 with `accessible=True` (`audit/e8`: order 300 of d_111 ->
  `theta_int 1.570796 rad (clipped to pi/2) ... accessible True`). Irrelevant at the orders used (n_max about
  250 at 200 keV), but the class should refuse rather than clip.
* `reflection_holo/geometry/accessibility.py:38` uses `>= 2 dK` while `SpecularCondition` uses `K_int > dK`
  (`specular.py:83`). The equality case (a grazing exit beam, theta_ext = 0) is accepted by one and refused by
  the other. `test_guard_agrees_with_specular_condition_on_the_rod` does not reach equality.
* `reflection_holo/structure/si001.py:150`: `int(st.boundary_step_layers)` truncates -1.5 to -1 in
  `validate_staircase`. The builder then fails late with a misleading "(e) measured step ... != declared"
  message (`audit/e12b_builder_inputs.py`). Check integrality as for the layers and widths (`:145-147`).
* `reflection_holo/geometry/frames.py:68-69` and `reflection_holo/provenance/manifest.py:165` use bare
  `assert`, which is stripped by `python -O`. The structure checks deliberately avoid this (checks.py
  docstring).
* `reflection_holo/optics/hologram.py:355`: `dict(h.metadata)` is a shallow copy, so nested records (the
  reference record, the R2 `valid_mask` array) are shared between the noiseless and noisy Hologram objects.
* Quantification functions do not validate `wavelength_A`. A negative value surfaces as a SmallDenominatorError
  with the message "sensitivity -10.02 rad/A is not larger than its propagated uncertainty 0" (`audit/e8`).

## Tolerance integrity: T1-T25 against the calculator's `chk()` calls

Calculator lines `tools/reflection_step_phase_calculator.py:1019-1068`. Package values are from
`audit/e3_tvalues.py`; margin = tol - |got - want|. Every T test uses exactly the calculator's reference value
and tolerance. None is looser.

| T | Test (file:line) | Calculator want +- tol | Package got | Same ref/tol? | Note |
|---|---|---|---|---|---|
| T1 | tests/geometry/test_geom_wavelength.py:16 | 0.0250793 +- 1e-6 | 0.0250793405 | yes | |
| T2 | same file:21 | 0.0370144 +- 1e-6 | 0.0370143661 | yes | |
| T3 | same file:26 | 0.0196875 +- 1e-6 | 0.019687489 | yes | formula check only (300 keV never used) |
| T4 | tests/geometry/test_geom_specular.py:36 | 23.9976 +- 1e-3 mrad | 23.9976034 | yes | lower-level SpecularCondition (forbidden (6,-6,6) setting, as the calculator) |
| T5 | tests/geometry/test_geom_refraction.py:21 | 8.3560 +- 1e-3 mrad | 8.35567613 | yes | different quantity: internal `asin(dK/k_int)`; the calculator's `asin(dK/k)` = 8.355968. \|d\| = 3.2e-4 vs the calculator's 3.2e-5; both pass |
| T6 | test_geom_specular.py:41 | 22.4953 +- 1e-3 mrad | 22.4953153 | yes | |
| T7 | tests/geometry/test_geom_crystal.py:23 | 0 +- 1e-9 | 6.2e-15 | yes | also asserts (6,-6,6) |
| T8 | same file:29 | 8 +- 1e-9 | 8 | yes | |
| T9 | same file:34 | 4 sqrt 2 +- 1e-9 | 5.65685425 | yes | |
| T10 | test_geom_specular.py:46 | 3.9236 +- 2e-3 rad | 3.92357236 | yes | |
| T11 | same file:51 | 2.5820 +- 2e-3 | 2.58200562 | yes | target-level call (with the guard) |
| T12 | same file:56 | 3.4088 +- 2e-3 | 3.40876519 | yes | target-level |
| T13 | same file:61 | 4.5386 +- 2e-3 | 4.53858367 | yes | target-level |
| T14 | same file:66; tests/quantification/test_quant_height.py:74 | 0.5575 +- 1e-3 A | 0.557481757 (both) | yes | evaluated twice (geometry and quantification paths) |
| T15 | tests/geometry/test_geom_accessibility.py:24 | 0 +- 0.5 | 0 | yes | also asserts the refusal message |
| T16 | tests/quantification/test_quant_invisibility.py:20 | 1 +- 1e-9 | 1 | yes | |
| T17 | tests/geometry/test_geom_plate_cell.py:26 | 31.10 +- 0.05 % | 31.1046027 | yes | |
| T18 | same file:31 | 80.89 +- 0.05 % | 80.8903844 | yes | |
| T19 | same file:36 | 4.4604 +- 1e-3 A | 4.4604069 | yes | |
| T20 | tests/geometry/test_geom_projection.py:35 | 44.46 +- 0.02 | 44.4574496 | yes | |
| T21 | tests/geometry/test_geom_sampling.py:16 | 64.31 +- 0.02 mrad | 64.3060012 | yes | |
| T22 | same file:21 | 16.72 +- 0.02 mrad | 16.7195603 | yes | also asserts refusal of 24 mrad |
| T23 | tests/quantification/test_quant_rocking.py:23 | 0.6270 +- 1e-3 mrad | 0.627142184 | yes | different expression: `lambda/(4 h cos theta)` at 22.495 mrad; the calculator uses `lambda/(4 h)` = 0.626984. Documented (S1a open issue 4) |
| T24 | tests/reconstruction/test_roundtrip_T24_T25.py:35 | `sc666.step_phase(d111)['wrapped']` = 2.35961295 +- 5e-3 | 2.35969848 | yes | full package chain; want imported from the calculator, not retyped; source-text guard at :17 |
| T25 | same file:42 | 0 +- 5e-3 | 0.000274081 | yes | |

Other tolerance observations:

* The calculator's tolerances are wide compared with the precision of the values: 2e-3 rad on T10 to T13
  corresponds to about 0.01 V of V0 (d|Delta_phi|/dV0 = -0.20 rad/V at (6,-6,6)). That is the specification
  (docs/05 criterion 2); it is not loosened here.
* Printed-digit tests use half a unit of the last printed digit. `test_shadow_bilayer_888`
  (`tests/geometry/test_geom_projection.py:68-73`) compares 101.48 A with 101.0 +- 0.5 (margin 0.02 A); the
  docstring still says "102 A ... +/- 0.5 A" while the code checks 101.0.
* No tolerance has been widened in the git history of tests/ (`git log -p -- tests`, removed assertion lines
  listed). The removed lines are API renames (`intervals_A` -> `illumination_intervals_A`, f5a2a00),
  nested-approx flattening (52b9c6e) and the converted private-helper test (36fbe25), all with unchanged
  tolerances, plus one reference value (102 -> 101 A, 5d59c41, following the docs correction).

## Answers to the audit questions

### 1. Physics against docs/physics_conventions.md (all reproduced independently)

* exp(+ik.r) sign and signed step phase: VERIFIED. An explicit kinematic (Born) sum
  `sum_j exp(-i q.r_j)` over atoms built by `build_si001_terraces` gives arg(A_upper/A_lower) equal to
  `specular_step_phase(+h)` to 9e-8 rad for a/2 and a/4 steps at [110] and [100] (`audit/e2_sign_chain.py`):
  ```
  az (1, 1, 0) a/2 up then a/2 down at cell edge : h = +2.7155 A  arg(A_up/A_low) = +2.718514936  package specular_step_phase (wrapped) = +2.718514875  |diff| = 6.1e-08
  az (1, 0, 0) a/4 up then a/4 down              : h = +1.3577 A  arg(A_up/A_low) = +1.359257524  package specular_step_phase (wrapped) = +1.359257438  |diff| = 8.7e-08
  ```
  (A first run with a 40-layer slab and a 30 A decay length gave a 0.21 rad mismatch. That was bottom
  truncation in my probe, not a package error; 120 layers and 10 A remove it.)
* Inverse height and down-step reversal: VERIFIED through the whole chain (object wave, R1 hologram, Poisson
  1e4, carrier on the empty hologram, sideband, divide_empty, `height_from_phase`) for +-a/2 and +-a/4 with both
  carrier signs (`audit/e2`): `h_true = -2.7155 A ... h_rec = -2.7154 A`, `h_true = +1.3577 A ... h_rec =
  +1.3577 A`, and so on (8 of 8). Also exact inversion for 7 conditions and both signs to 1e-9 A
  (`audit/e1_independent_values.py`).
* Relativistic Delta, theta_c, internal and external angles: VERIFIED against an independent route (kinetic
  energy inside the crystal T + eV0, K_par conserved), `audit/e1`:
  ```
  Delta                          6.98205733414109e-05       6.98205733414108e-05   7.77e-16
  theta_c_int_mrad                   8.35567612905899           8.35567612905899   4.44e-16
  (0,0,8) h=a/2         18.471996329/18.471996329       16.474332799/16.474332799     -22.414226354/-22.414226354    0.76119850/0.76119850
  (0,0,4) h=a/4          9.235604224/9.235604224         3.934389667/3.934389667       -2.676589798/-2.676589798     3.18720402/3.18720402
  ```
  The relativistic/non-relativistic ratio is 1.1637 (docs: 16 %). theta_c is the internal escape angle
  (`geometry/refraction.py:92-102`), as the conventions require.
* Accessibility guard: correct formula and sign (`geometry/accessibility.py:20-50`; (2,-2,0) refused; negative
  normal component refused). Nit on the equality boundary (see NIT).
* Forbidden-reflection guard: correct. The rule matches the explicit 8-atom sum for all |h|,|k|,|l| <= 6
  (`test_selection_rule_matches_explicit_sum`), and the six listed forbidden reflections are refused as targets
  in code and in configurations. It is kinematic by design (spherical atoms). There is no combined
  target-level guard for NON-specular reflections: `require_accessible` takes G in rad/A and cannot check
  F_hkl. No caller needs one yet.
* Wrap period and branch: `h_2pi = lambda/(sin theta_in + sin theta_out)` and `phi = wrapped + 2 pi m` are
  correct and always reported (`quantification/height.py:83-97, 119-164`); -pi edge case in NIT.
* Shadow and blocked-view strips: VERIFIED by an independent brute-force ray trace on the BUILT atoms of 40 random
  periodic staircases, both azimuth families, theta_in and theta_out drawn independently in 5-40 mrad
  (`audit/e13_shadow_bruteforce.py`): `159676 sample points compared, mismatching points = 0`. At the (0,0,8)
  operating angle the strip is 82.407 A per a/4 layer and 164.814 A per a/2 step. Side and angle assignment
  (illumination behind an upper-upstream riser at theta_in; blocked view in front of an upper-downstream riser
  at theta_out) matches docs/05 4.5. Limits (declared): the masks are on surface coordinates and are not yet
  mapped to image pixels (no foreshortening or exit-plane projection of the masks); features only at 0 or 90
  degrees.
* numpy FFT sign: VERIFIED (`tests/optics/test_hologram_formation.py:48-60`, and `audit/e4`: the correct
  sideband gives +0.500 rad for phi_o - phi_r = +0.5).
* The reconstruction returns phi_o - phi_r: VERIFIED for the correct sideband (above, and
  `test_returned_phase_is_phi_o_minus_phi_r` for four carrier directions). NOT guaranteed when the search disc
  covers both sidebands (M1).

### 2. PROJECT_INPUT and default policy

Every parameter default in the package (AST scan, `audit/defaults.py`):
`require_accessible(label='G')`, `allow_forbidden=False` (twice), `load_config_dict(allow_test_only=False,
source_path=None, sha256_file=None)`, `require_evidence_label(error=ValueError)`, `_require_2vector` and
`_require_finite` flags, `git_state(root=None)`, `build_manifest(extra=None)`, `_positive(allow_inf=False)`,
`locate_carrier(allow_object_hologram=False)`, `checks.assert_frame(normal_hkl=(0,0,1))` and the structure
tolerances, `shadows._check_theta(name, what)`, `_merge(tol)`, `intervals_to_mask(period_A=None)`,
`feature_shadow_intervals(y_A=None)` (the feature centre line), and `a_A=A_SI_A` in five structure functions
(m6). None stands in for V0, energy, azimuth, glancing angle, convergence, aperture, pixel size, dose,
carrier, reference trajectory, pattern geometry or overlayer. Each of those is a required argument where it
exists: `V0_V` (geometry), `E_keV`, `azimuth_uvw`+label, `theta_*_ext_rad`+label, `pixel_size_A`,
`dose_e_per_px`+`seed`, `carrier_cycles_per_A`, `overlayer` (explicit None = ASSUMPTION B7), and
`PatternedFeature` (all fields). `try/except` occurs only at `io/config.py:295, 322` (re-raised as ConfigError),
`io/validate_configs.py:29, 37` (reported and recorded) and `provenance/manifest.py:63` (swallowed, m8).
`.get(...)` occurs only for optional metadata or YAML keys; no default value is substituted for a physical
input. There is no "first dataset" logic (no data loader exists). The silent paths found are the configuration
gate (M2), `np.errstate` in divide_empty (m1), the zero-uncertainty refusal bypass (m2), the hard-coded
lattice parameter (m6) and the clipping in SpecularCondition (NIT).

### 3. Tolerance integrity: see the table above. Tests that assert less than their names claim: m9.

### 4. Hologram chain

* Ensemble averaging only after squaring: YES. The only accumulation is `acc += |u_o + u_r|^2`
  (`optics/hologram.py:310`); no package code averages complex arrays (grep for mean/average/sum). Pairs share
  the realisation index when indices are set; with `None` pairing is not enforced (m7). The contrast of the
  average equals |<exp(i delta)>| (test).
* Carrier located only on an empty hologram: YES by default (`sideband.py:189-191` refuses `content ==
  "object"`), but `content` is self-declared, and `reconstruct_sideband` accepts a carrier located on an object
  hologram with the opt-in flag (m7). The sideband choice is not protected (M1).
* No hidden detrend: CONFIRMED. `ramp_removal: "none (never implicit)"`; the plane fit is a separate call over a
  declared region; `divide_empty` is a declared option.
* Raw wrapped phase and masks preserved: the raw wrapped phase, raw amplitude, both complex sidebands and the
  Fourier mask are kept read-only. The real-space validity (R2 `valid_mask`, amplitude threshold) is NOT
  carried into the result (m1).
* sigma_phi N definition: CONSISTENT. One formula (`quantification/noise.py:20-43`); `sideband_phase_noise`
  supplies N = counts/px x n_pix/sum(W^2). The Monte Carlo test, re-run here with `-s`, gives
  sigma_meas/sigma_pred = 0.9948, 1.0003, 1.0019, 1.0095 (top-hat) and 1.0029, 1.0210, 1.0127, 1.0171 (Hann),
  all within 4 standard errors. The four Hann ratios all lie above 1 (mean +1.3 %, about 1.6 sigma
  combined). This is not significant with K = 16, but a larger K would show whether the Hann effective area is
  slightly optimistic.
* R1 aperture passage declared: YES, required (`hologram.py:103`), but inert, and R3 has none (m7).
* R2 twin as documented: YES, sign-inverted and translated by -s, not mirrored
  (`tests/reconstruction/test_self_reference_R2.py`, 1e-3 rad), consistent with C2 q3.

### 5. Structure

144 of 144 valid staircases built: all 8 azimuths of both families, parallel and transverse edges,
`edge_periods` 1 to 3, terrace widths down to one period, random a/4 and a/2 sequences
(`audit/e12_structure_sweep.py`). Atom count, step type, back-bond axis alternation and incidence-plane glide
(present at <100>, absent at <110>) all agree with independent expectations; `independent-check mismatches:
none`. The 16 refusals were inconsistent boundary declarations of my own, correctly refused as net height
changes. Near-boundary A-M7 duplicates are caught (existing test). Accepted when it should be refused: a
non-integer `boundary_step_layers` in `validate_staircase` (NIT; the builder catches it later). The
screw-versus-translation classification is correct, but its B4 consequence is wrong at <100> (m3). The
unlabelled inputs `first_terrace_backbond_uvw` (item 11: which terrace type is on which side) and the staircase
widths and heights (items 11, 13, 14) are required but carry no evidence label, unlike the azimuth and the
overlayer. The lattice parameter is hard-coded (m6).

### 6. Provenance

Manifest fields present: package versions (all distributions, pip-freeze equivalent), Python and numpy, git
commit, branch and dirty flag, engines, precision, seeds, thread count plus environment, configuration file and
canonical SHA-256, input SHA-256, declared wave planes, beam energy (refused unless 200 keV), UTC timestamp.
Gaps: no diff hash when dirty, git failure swallowed, only `validate_configs` writes a manifest, thread count
not applied (m8). Configurations are labelled per parameter (value, label, source, optional unit and item);
units are enforced; CFG-A mislabels repository defaults (m4).

### 7. Code quality with scientific impact

Units (m5); theta near 0 without uncertainty (m2); theta near theta_c: `theta_ext_from_int_rad` is exact down
to theta_c and refuses below it (`audit/e8`: theta_c(1 + 1e-9) -> 0.0004 mrad), and a condition just above
the accessibility limit is accepted with a huge h_2pi and foreshortening (by design; (0,0,4) at 12 V exits at
3.934 mrad with 254x); h = 0 is refused where it would divide (`max_tilt_step_rad`) and handled elsewhere;
dtypes are upcast to float64 and complex128 at the Wave and Hologram boundaries; clipping (NIT).

## Verified as correct (with the evidence used)

1. Relativistic wavelength, k, gamma and beta at 100, 200 and 300 keV: T1-T3 and the conventions values
   (0.02507934 A, 250.5323 rad/A). The independent route agrees to 0 relative (`audit/e1`).
2. Delta: the exact relativistic form (not V0/T; ratio 1.1637). The conventions' first-order form is provided
   for cross-checking and agrees to 8.4e-6 (test). theta_c = asin(dK/k_int) = 8.3557 mrad (internal escape
   angle); independent agreement 4e-16.
3. Internal and external angles, step phases and h_2pi for (4,-4,4), (6,-6,6), (8,-8,8), (0,0,4), (0,0,8),
   (0,0,12): independent agreement to 1e-9 or better (`audit/e1`). docs/05 CFG-B numbers reproduced
   (theta_int 18.472, theta_ext 16.474 mrad, h_2pi 0.7612 A; (004) exits at 3.934 mrad).
4. Signed step phase `-(k_out - k_in).R` in exp(+ik.r): confirmed by an explicit Born sum over built atoms
   (9e-8 rad), for a/2 and a/4 at [110] and [100] (`audit/e2`).
5. Signed inverse height, including down-step reversal, through the full hologram chain with both carrier signs
   (`audit/e2`, 8 of 8 cases) and exactly for 7 conditions (`audit/e1`).
6. Structure factor and selection rule against the explicit sum for |hkl| <= 6. The forbidden-target guard
   refuses (2,-2,2), (6,-6,6), (10,-10,10), (002), (006), (0,0,10) in code, and in configurations when
   `surface_material == "Si"` (m10).
7. Accessibility guard G.n_hat >= 2 dK: (2,-2,0) refused; agreement with SpecularCondition on the rod.
8. Frames: right-handed and orthonormal for CFG-A and for all four CFG-B azimuths; out-of-plane azimuths
   refused.
9. The shadow and blocked-view strips of built staircases agree with an independent brute-force ray trace
   (0 mismatches in 159 676 points over 40 random cells, `audit/e13`). The feature strips agree with the
   independent `quantification.shadow` implementation (existing test).
10. numpy FFT sign and phi_o - phi_r for the correct sideband; no implicit detrend; raw wrapped phase kept
    read-only; plane fitting only on request.
11. Ensemble averaging after squaring only; partial-coherence contrast |<exp(i delta)>|; phases common to both
    branches cancel.
12. sigma_phi = sqrt(2)/(mu sqrt(N)) with one definition of N; the Monte Carlo agreement was re-run here.
13. T24/T25 through the package chain; bit-level agreement with the calculator's `hologram_roundtrip`; the
    carrier trap (0.78 rad) reproduced and explained (conjugate sideband plus one-row ramp).
14. R2 twin: sign-inverted and translated by -s, not mirrored.
15. Si(001) builder: one continuous lattice, half-open window, A-M7 duplicates caught, counts, a/4 = screw and
    a/2 = translation measured on the atoms, back-bond axis alternation, incidence-plane glide at <100> only;
    144 of 144 valid random staircases (`audit/e12`). Continuity under the periodic boundary enforced; the
    inspected 0,1,2,3 staircase refused.
16. Function-level PROJECT_INPUT policy: no signature default stands in for any listed PROJECT_INPUT
    (AST scan). TEST_ONLY is refused from files. CFG-O is refused at run level. A present-and-null
    PROJECT_INPUT fails at run level, naming its item.
17. All 25 calculator checks and all 17 `tools/phase1_numbers.py` checks pass. The dh/dV0 sign logic in
    phase1_numbers (fixed phase, K_ext decreasing with V0, so an underestimated V0 gives too small a height) is
    consistent with its docstring and docs/06 item 20.

## Commands run (all from /home/user/Holography unless stated; scratch = the audit directory above)

1. `git status | head -20 && git log --oneline | head -15 && ls -la && find reflection_holo tests configs tools -type f | sort && wc -l ...`
2. `ls -la docs docs/agent_reports && wc -l docs/*.md docs/agent_reports/*.md && git diff --stat && mkdir -p <scratch>/audit && cat pyproject.toml README.md .gitignore`
3. `sed -n 1,400p docs/physics_conventions.md`; `cat docs/05_final_repository_specification.md`; `cat docs/model_assumptions.md docs/06_project_inputs_required.md`
4. `cat docs/agent_reports/S1a_m1_geometry_quantification.md`; `cat docs/agent_reports/S1b_... S1c_...`; `cat docs/agent_reports/S2_consolidation.md`
5. Read `tools/reflection_step_phase_calculator.py` (1-828, 829-1168)
6. `cat -n` of every package module, every test file, the three configs and `tools/phase1_numbers.py` (Read for si001.py, shadows.py, test_structure_shadows.py)
7. `cat -n reflection_holo/structure/xyz.py; cat docs/agent_reports/C2_phase2_physics_checks.md; git diff --stat`
8. `git rev-parse HEAD && git status --porcelain && git diff --quiet -- <scope> && echo "scope clean vs HEAD"; find <scope> ... | xargs sha256sum | sha256sum`
9. `git log --oneline -5 && git show --stat HEAD | head -20`
10. `venv/bin/pytest -q` -> `374 passed in 6.38s`; `venv/bin/python tools/reflection_step_phase_calculator.py > <scratch>/calc_out.txt` -> `25/25 checks pass`; `venv/bin/python tools/phase1_numbers.py` -> `17/17 checks pass`
11. `grep -n -A2 "except" ...; grep -n "\.get(" ...; grep -n "errstate|warnings|nan_to_num|np.clip" ...; grep -n "next(iter|[0]" ...`
12. `venv/bin/python <scratch>/defaults.py` (AST scan of parameter defaults)
13. `grep -n "V0_SI_ASSUMPTION_V|A_SI_A|BEAM_ENERGY_SUPPLIED_KEV|200\.0|12\.0" -r reflection_holo`
14. `venv/bin/python -c "import mpmath"` -> not installed; `venv/bin/python <scratch>/e1_independent_values.py` (first attempt failed on the missing mpmath; rewritten to numpy longdouble and re-run)
15. `venv/bin/python <scratch>/e2_sign_chain.py` (run twice; the first with a 40-layer slab showed the probe truncation noted above)
16. `venv/bin/python <scratch>/e4_conjugate_sideband.py`
17. `venv/bin/python <scratch>/e5_config_gate.py`; `venv/bin/python <scratch>/e5b_material_bypass.py`
18. `venv/bin/python <scratch>/e10_rocking_branch.py`
19. `venv/bin/python <scratch>/e8_edges.py`
20. `venv/bin/python <scratch>/e12_structure_sweep.py`; `venv/bin/python <scratch>/e12b_builder_inputs.py`
21. `venv/bin/python <scratch>/e16_manifest.py` (manifest built in memory only, not written)
22. `venv/bin/python <scratch>/e7_divide_empty.py` (twice; the second added the DEBUG lines)
23. `venv/bin/python <scratch>/e9_ensemble_pairing.py`
24. `venv/bin/python <scratch>/e13_shadow_bruteforce.py`
25. `venv/bin/python <scratch>/e3_tvalues.py`
26. `grep -n ...` for line numbers (several); `grep -n "def test_T" -r tests; grep -n 'chk("T' tools/reflection_step_phase_calculator.py`
27. `git log --format="%h %s" -- tests; git log -p --format="COMMIT %h" -- tests | grep ...` (tolerance history)
28. `git diff 7874c85 HEAD -- <scope>` (0 lines) and `git diff 7874c85 HEAD -- docs/physics_conventions.md docs/model_assumptions.md docs/06_project_inputs_required.md`; `grep -n "^| B15" docs/model_assumptions.md`
29. `venv/bin/pytest -q -s tests/reconstruction/test_phase_noise.py` -> `8 passed`
30. `grep -n "np.mean(|\.mean(|np.average|np.sum(.*data|acc +=" -r reflection_holo`

## NOT RUN

* `python -m reflection_holo.io.validate_configs configs/*.yaml`: NOT RUN, because it writes a manifest under
  the repository's `outputs/`, and this audit may write only its report. Its logic was exercised in memory
  (`audit/e5`, `audit/e16`).
* `python -O` runs (the bare-assert NIT): NOT RUN; the finding is from reading the code.
* Any multislice, dynamical or engine run: none exists in the package (M2 of the milestones), so NOT RUN.
* A dynamical check of the <100> a/4 symmetry: NOT RUN here; C2's result is cited, and only the builder's
  own glide detection was exercised.
* Scripts under `tools/physics_checks/` (C2): NOT RUN; out of scope.
* Experimental data: none available.
