# S1a: milestone M1, geometry, quantification, io and provenance

Status: COMPLETE for this agent's scope (2026-09-22); not committed (the orchestrator commits).
Scope: docs/05_final_repository_specification.md sections 0, 2, 3, 4.1, 5 item 8, 8, 9 (M1).
Beam energy 200 keV everywhere; 300 keV appears only in the T3 formula check of the wavelength
function. constants.py and geometry/frames.py were imported and not modified. docs/ and tools/ were
not edited, apart from this report.

## Progress log

1. Read docs/05 (sections 0, 2, 3, 4.1, 5.8, 8, 9), physics_conventions, 03_physics_summary,
   model_assumptions, 06_project_inputs_required, source_map.tsv, the calculator (all 1168 lines),
   constants.py and geometry/frames.py.
2. Before writing any code, I checked the shadow-length reference values with the calculator's
   own SpecularCondition. The (8,-8,8) bilayer shadow is 101.48 A, not the 102 A printed in
   docs/03 section 4 (from E2 review F14). The test keeps 102 A +- 0.5 A (see open issues).
3. Implemented the modules listed below. A smoke check against the calculator gave
   theta_B_vac(666) = 23.997603 mrad, theta_ext = 22.495315 mrad, mod2pi = 3.923572 rad and
   h_2pi = 0.557482 A, identical to the calculator.
4. Ran the configuration validator (output at the end). CFG-A loads at run level. CFG-B is refused
   and the error names items 3, 4, 5, 7, 8, 12, 13 and 15. CFG-O is refused as a placeholder.
5. Ran the test suite. 193 passed and 1 failed; the failure is the (8,-8,8) reference value
   (verbatim output below).

## Files

Library (new):
- reflection_holo/geometry/: errors.py, wavelength.py, crystal.py, refraction.py, specular.py,
  accessibility.py, projection.py, sampling.py, plate_cell.py
- reflection_holo/quantification/: errors.py, height.py, noise.py, invisibility.py, rocking.py,
  controls.py, shadow.py
- reflection_holo/io/: config.py, validate_configs.py (a command-line tool that also writes a
  manifest)
- reflection_holo/provenance/: manifest.py

Configurations:
- configs/cfg_a_si111_cleaved_110azimuth.yaml
- configs/cfg_b_si001_patterned.yaml
- configs/cfg_o_osakabe_1988_reproduction.yaml

Tests:
- tests/geometry/: test_geom_wavelength.py, test_geom_crystal.py, test_geom_refraction.py,
  test_geom_specular.py, test_geom_accessibility.py, test_geom_projection.py,
  test_geom_sampling.py, test_geom_plate_cell.py
- tests/quantification/: test_quant_height.py, test_quant_invisibility.py, test_quant_rocking.py,
  test_quant_noise.py, test_quant_controls_shadow.py
- tests/io/test_io_config.py
- tests/provenance/test_prov_manifest.py

Outputs (gitignored):
- outputs/manifests/validate_configs_20260922T204649Z.json. It records commit 7e1e500, dirty=True,
  numpy 2.4.6, Python 3.11.15, the SHA-256 of the three configurations and 200 keV.

## Function to source-map table

Every public function's docstring states its SMxx ID and evidence label. io/ and provenance/ state
"no row; no physical claim".

| Module | Functions | SM | Evidence |
|---|---|---|---|
| geometry/wavelength | wavelength_A, k_ang_per_A, gamma_lorentz, beta_v_over_c | SM01 | DERIVED_HERE |
| geometry/crystal | structure_factor_over_f, diamond_allowed, require_allowed_target (forbidden-reflection guard), d_spacing_A, reciprocal_vector_cycles/_rad, reciprocal_lattice_cycles, rod_decomposition, rod_reflections | SM02 | DERIVED_HERE |
| geometry/refraction | effective_energy_V, refraction_delta (exact), refraction_delta_first_order, delta_K_per_A, k_internal_per_A, theta_c_rad, theta_int_from_ext_rad, theta_ext_from_int_rad (V0 required everywhere) | SM04 | DERIVED_HERE |
| geometry/specular | SpecularCondition (lower-level, no guard), specular_condition_for (target-level: rod, guard, accessibility) | SM02-SM05 | DERIVED_HERE |
| geometry/specular | beam_wavevectors_slab, step_phase_translation, specular_step_phase; wrap_to_pi | SM03; SM05 | DERIVED_HERE |
| geometry/accessibility | accessibility_margin, is_accessible, require_accessible | SM06 | DERIVED_HERE |
| geometry/projection | foreshortening, image_compression, exit_plane_height_A, surface_coordinate_A, shadow_length_A | SM07 | DERIVED_HERE |
| geometry/sampling | antialias_max_angle_rad, require_angle_in_band | SM15 | 2/3 rule UNVERIFIED; half-Nyquist SECTION_READ |
| geometry/plate_cell | plate_cell_geometry | SM09 | DERIVED_HERE |
| quantification/height | height_from_phase (signed height, sigma_h, wrap period, branch and branch source, small-denominator refusal), sensitivity_rad_per_A, sensitivity_uncertainty_rad_per_A, wrap_period_A, branch_index_of, height_candidates_A | SM03, SM05 | DERIVED_HERE |
| quantification/invisibility | detect_invisibility | SM03 | DERIVED_HERE |
| quantification/rocking | max_tilt_step_rad, resolve_rocking_series | SM05 | DERIVED_HERE |
| quantification/noise | phase_noise_sigma_rad, height_sigma_from_phase_sigma_A | SM12 | DERIVED_HERE |
| quantification/shadow | terrace_profile_A, shadow_masks (exact ray tracing at the operating angles) | SM07 | DERIVED_HERE |
| quantification/controls | no_step_control | no row (docs/05 5.8) | DERIVED_HERE |
| io/config | load_config_dict, load_config_file | no row | n/a |
| provenance/manifest | build_manifest, write_manifest, git_state, installed_packages | no row | n/a |

## Tests mapped to T numbers

Every check uses exactly the calculator's reference value and tolerance, compared as
|got - want| <= tol.

| T | Test | Note |
|---|---|---|
| T1, T2 | test_geom_wavelength::test_T1_wavelength_200keV, test_T2_wavelength_100keV | |
| T3 | test_geom_wavelength::test_T3_wavelength_formula_check_300keV | formula check only |
| T4, T6, T10, T14 | test_geom_specular::test_T4_…, test_T6_…, test_T10_…, test_T14_… | forbidden (6,-6,6) setting, lower-level SpecularCondition |
| T14 | test_quant_height::test_T14_wrap_period_via_quantification | second evaluation, through the quantification layer |
| T5 | test_geom_refraction::test_T5_critical_angle | |
| T7-T9 | test_geom_crystal::test_T7/T8/T9 | |
| T11-T13 | test_geom_specular::test_T11/T12/T13 | target-level call |
| T15 | test_geom_accessibility::test_T15_220_inaccessible | |
| T16 | test_quant_invisibility::test_T16_220_bilayer_is_invisible | |
| T17-T19 | test_geom_plate_cell::test_T17/T18/T19 | |
| T20 | test_geom_projection::test_T20_foreshortening_666 | |
| T21, T22 | test_geom_sampling::test_T21/T22 | |
| T23 | test_quant_rocking::test_T23_max_tilt_step_1nm | |
| none | test_geom_projection::test_shadow_* (8 tests, 11 cases) | docs/03 section 4 values, tolerance half a unit of the last printed digit |
| none | test_geom_crystal::test_guard_refuses_666_as_target; test_geom_specular::test_target_level_refuses_666 | guard tests |
| none | test_quant_height::test_sign_down_step_reverses_the_sign | sign test |
| none | test_quant_height::test_no_step_control_at_height_level; test_quant_controls_shadow::test_no_step_* | no-step control |
| none | test_quant_height::test_small_denominator_refused_never_divided | refusal |
| none | test_quant_height::test_wrap_and_branch_always_reported, test_branch_index_definition; test_quant_rocking::test_absolute_height_* | wrap and branch |
| none | test_io_config::test_null_project_input_fails_run_level_naming_item[item3…item15] | 8 configuration-failure tests, one per null item |
| none | test_io_config: CFG-B energy, CFG-O placeholder, label, schema and crystallographic tests | |
| none | test_geom_specular::test_frames_used_cfg_a_…, test_frames_used_cfg_b_…[110,100] | frames |
| none | test_geom_specular::test_docs03_section3_table[3..8] | docs/03 section 3 table, printed digits |

## Verbatim pytest output

Command: `venv/bin/pytest -q tests/geometry tests/quantification tests/io tests/provenance`
(exit status 1)

```
...........................................F............................ [ 37%]
........................................................................ [ 74%]
..................................................                       [100%]
=================================== FAILURES ===================================
___________________________ test_shadow_bilayer_888 ____________________________

    def test_shadow_bilayer_888():
        """docs/03 section 4: 102 A per bilayer at (8,-8,8) (+/- 0.5 A). Reference value kept as
        printed; the calculator's own theta_ext(8,-8,8) = 30.888 mrad gives 101.48 A (see
        docs/agent_reports/S1a_m1_geometry_quantification.md, open issues)."""
>       check(shadow_length_A(D111, theta_ext((8, -8, 8))), 102.0, 0.5)

tests/geometry/test_geom_projection.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

got = 101.47994547922607, want = 102.0, tol = 0.5

    def check(got, want, tol):
>       assert abs(got - want) <= tol, f"got {got!r}, want {want!r} +/- {tol}"
E       AssertionError: got 101.47994547922607, want 102.0 +/- 0.5
E       assert 0.5200545207739253 <= 0.5
E        +  where 0.5200545207739253 = abs((101.47994547922607 - 102.0))

tests/geometry/test_geom_projection.py:22: AssertionError
=========================== short test summary info ============================
FAILED tests/geometry/test_geom_projection.py::test_shadow_bilayer_888 - Asse...
1 failed, 193 passed in 0.43s
```

Also run: `venv/bin/pytest -q tests/test_frames.py`, 6 passed. The configuration validator,
`venv/bin/python -m reflection_holo.io.validate_configs configs/cfg_a… configs/cfg_b…
configs/cfg_o…`, printed:
- CFG-A: run level PASS.
- CFG-B: run level REFUSED (MissingProjectInputError), naming item 3
  (convergence_semi_angle_mrad), item 4 (objective_aperture_semi_angle_mrad), item 5
  (image_pixel_size_nm), item 7 (glancing_angle_ext_mrad), item 8 (beam_azimuth_uvw), item 12
  (surface_preparation_details), item 13 (pattern_geometry) and item 15 (reference_trajectory).
- CFG-O: run level REFUSED (PlaceholderConfigError); UNVERIFIED fields are beam_azimuth_uvw,
  beam_energy_keV, glancing_angle_ext_mrad and reflection_order.

## NOT RUN

- T24 and T25. They belong to the optics and reconstruction agent.
- The complete tests/ tree, including other agents' tests. Only my four directories and
  test_frames.py were run.
- Parts of spec section 8 and section 5.8 that are not implemented:
  - sensitivity of the height to convergence and to V0 uncertainty (sigma_h propagates only the
    phase, angle and wavelength uncertainties);
  - terrace segmentation with uncertainties;
  - source-map validation.
- The calculator's section 11(a) truncated-stack translation check.
- The checks of tools/phase1_numbers.py (dh/dV0).
- Any simulation. No multislice or dynamical code exists in M1.

## Proposed source_map test_status updates (proposals only)

- SM01: T1-T3 PASS 2026-09-22. Implementation reflection_holo/geometry/wavelength.py.
- SM02: T7-T9 and the guard tests PASS. Implementation geometry/crystal.py.
- SM03: T10-T13, T16 and the sign test PASS. Implementation geometry/specular.py,
  quantification/height.py and quantification/invisibility.py.
- SM04: T5 and T6 PASS. Implementation geometry/refraction.py.
- SM05: T14, T23 and the rocking-series recovery PASS. Implementation quantification/rocking.py
  and quantification/height.py.
- SM06: T15 PASS. Implementation geometry/accessibility.py.
- SM07: "T20 PASS; shadow-length test RUN: 10 of 11 cases PASS, the (8,-8,8) 102 A case FAILS
  (computed 101.48 A); shadow masks PASS". Implementation geometry/projection.py and
  quantification/shadow.py.
- SM09: T17-T19 PASS. Implementation geometry/plate_cell.py.
- SM12: sigma_phi formula PASS. Implementation quantification/noise.py.
- SM15: T21, T22 and the SM15 printed values PASS. Implementation geometry/sampling.py.
- SM22: CFG-O placeholder rule PASS (fixture test and validation of the shipped file).

## Open issues

1. Wrong reference value. docs/03 section 4 and docs/05 section 2 (CFG-A) give "102 A at
   (8,-8,8)". d_111/tan(30.888 mrad) = 101.48 A, which rounds to 101 A. The 10 nm value there
   (324 nm) is right. The test keeps 102 A and fails. The fix belongs in docs/ (orchestrator).
2. Two definitions of theta_c. The calculator's theta_critical_rad uses dK/k and its docstring
   calls it an "external critical angle for total external reflection". This contradicts
   physics_conventions revision 2. I implemented the conventions (internal escape angle,
   dK/k_int). The two differ by 3.5e-5 relative, and T5 passes either way. The calculator
   docstring should be corrected.
3. Two forms of Delta. physics_conventions prints the first-order form of Delta; I implemented
   the calculator's exact form. They differ by 8.4e-6 relative, and a test checks that.
4. T23 formula. The calculator's T23 expression omits cos(theta). I implemented
   lambda/(4 h cos theta), evaluated at the (6,-6,6) angle; it gives 0.62714 mrad, inside
   0.6270 +- 1e-3.
5. Small-denominator policy, as interpreted here. The conversion is refused when
   |q.n_hat| <= sigma(|q.n_hat|), with sigma propagated from the angle and wavelength
   uncertainties. The C report's alternative (|q.n_hat| below a multiple of sigma_phi/h_target)
   is not implemented. Please confirm which is intended.
6. Duplicated functions across agents. structure/shadows.py has its own shadow_length_A and
   shadow masks. reconstruction/sideband.py has its own wrap_to_pi and sigma_phi. The
   orchestrator should choose the canonical versions.
7. Configuration choices:
   - CFG-A's inherited defaults are labelled PROJECT_INPUT (repository default), following the
     calculator and SM09; they have no docs/06 item.
   - For CFG-B, (0,0,8) is labelled ASSUMPTION (item 9) and the step list is ASSUMPTION
     (item 14).
   - The miscut (item 11) and items 2, 6, 10 and 16-22 have no fields yet.
   - Any non-null energy other than 200 keV is refused in every configuration. If the body of
     P01 gives CFG-O another energy, this rule needs a decision.
8. Shared constants: no new constant is requested.
