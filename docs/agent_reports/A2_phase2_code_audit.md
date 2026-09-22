# A2: Phase 2 code audit of `reflection_holo` (package, tests, configs, tools/phase1_numbers.py)

Status: IN PROGRESS (written incrementally), 2026-09-22. Agent A2 (code auditor). Only this file
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
  bulk-termination and exact-azimuth caveats. This waits on the docs decision proposed in C2 section 1.6.

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
