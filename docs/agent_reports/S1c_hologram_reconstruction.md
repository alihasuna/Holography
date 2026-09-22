# S1c: hologram formation and sideband reconstruction (Phase 2, part C)

Status: COMPLETE for this task, 2026-09-22. Not committed (the orchestrator commits). Code not
audited or reviewed by another agent.

Scope (orchestrator task S1c): `reflection_holo/optics/`, `reflection_holo/reconstruction/`,
`tests/optics/`, `tests/reconstruction/`. Height conversion is NOT done here (it belongs to
`quantification/`); the reconstruction returns phases only.

Inputs read: docs/05 sections 5 and 8; docs/03 section 6; docs/physics_conventions.md;
docs/model_assumptions.md B5, B8; docs/06 items 3, 6, 15-19, 22; source map SM12, SM13, SM21, SM22;
tools/reflection_step_phase_calculator.py section 12 and checks T24/T25 (lines 1062-1068);
docs/agent_reports/A_code_audit.md C3 (find_peak) and M5 (default plane detrend).

## Log

1. Calculator trap reproduced before any code was written (scratch script, calculator functions
   only): on the T24 object hologram (n = 512, fringe 8 px, 50/50 tanh step of 2.3596 rad) the
   brightest bin outside the calculator's r < 0.05 cycles/px exclusion disc is fftshifted bin
   (255, 320), whereas the empty hologram gives (256, 192). Recentring on the object's brightest bin
   gives 0.7820 rad (noiseless) and 0.7815 rad (dose 1e4, seed 12345) instead of 2.3596 rad.
   Mechanism (DERIVED_HERE from these numbers): the bin is (i) on the CONJUGATE side (+q_c, which
   carries -(phi_o - phi_r)) and (ii) one row off, which adds a ramp of 2 pi/512 per row, i.e. pi
   over the 256-row separation of the two terrace medians: -2.3596 + pi = 0.7820. The calculator's
   0.78 rad is therefore a sign error plus a ramp, not a ramp alone. If the object and the empty
   hologram are both demodulated at the object's brightest bin and divided, the ramp cancels and the
   result is -2.3596 rad (still wrong: conjugate sideband).
2. Implemented `reflection_holo/optics/fields.py`, `optics/hologram.py`,
   `reconstruction/sideband.py`. First comparison: the package chain reproduces the calculator's
   `hologram_roundtrip` bit for bit (difference 0.00e+00 in recovered step and sigma) on all eight
   rows of calculator section 12. The global brightest-bin search initially picked the Hermitian
   partner (unshifted (1, 448)) of the calculator's bin, because |F(q)| = |F(-q)| exactly for a real
   hologram and argmax breaks the tie by array order; this gave -0.78 rad instead of +0.78 rad. The
   locator now takes the argmax in centred (fftshift) order, the calculator's tie-break, and gives
   (511, 64) = fftshifted (255, 320) and +0.7820 / +0.7815 rad. The sign of the calculator's
   printed 0.78 is therefore a tie-break artefact; its magnitude is not.
3. Test failures while writing the tests (both in my first draft of the R2 twin test; tolerance
   1e-3 rad unchanged). Verbatim:
   - `E       AssertionError: assert np.float64(0.023102807929132628) <= 0.001`
     (test_r2_twin_is_sign_inverted_and_translated_by_minus_shift, line 78). Cause: the profile
     window reached column 370, 14 px from the edge of the reference's valid region (column 384),
     outside the documented >= 72 px interior. Fix: features moved to columns 240 and 270.
   - `E       AssertionError: assert np.float64(0.0035016960328715617) <= 0.001` (same test).
     Cause: the assertion `twin + feature = 0` was wrong for the window used. The model predicts
     twin + feature = phi(r - s) - phi(r + s), which at the window ends is about 1e-3 rad from the
     Gaussian tails. Fix: the window was narrowed to +-20 px beyond the bumps, where the model's
     prediction is below 1e-5 rad.
4. Further failures in my first draft of tests/reconstruction/test_sideband_processing.py (test-case
   design errors; tolerances unchanged). Verbatim:
   - `E       Failed: DID NOT RAISE ValueError` (test_required_processing_inputs, "mask crosses
     Nyquist"): my case had |q| + R = 0.125 + 0.124 = 0.249 cycles/A, not beyond Nyquist
     (0.5). Replaced by q = 0.375, R = 0.13 (0.505 > 0.5), which raises.
   - `E       Failed: DID NOT RAISE ValueError` (test_no_implicit_detrend_and_explicit_plane_fit):
     with gradients 0.02 / -0.01 rad/A the fitting region never wraps, so there was nothing to
     refuse. Gradient changed so that the region wraps.
   - `E       assert (0.0500001818...8337691730055) == approx((0.05 ...01 ± 1.0e-06))` with
     `Max absolute difference: 1.6623082699455255e-06` (same test, tolerance 1e-6 rad/A): a
     NON-periodic object ramp (12.8 rad across the field) leaks at the FFT boundary and biases the
     fitted gradient by 1.7e-6 rad/A (1.6e-4 rad over the 96 px region). The test now uses a
     field-periodic ramp (2 and -1 cycles), which isolates the property under test (no implicit
     detrend; the explicit fit recovers the ramp). The boundary leakage is real and is listed under
     open issues (no real-space window implemented).
5. Failure in my first draft of tests/optics/test_hologram_formation.py. Verbatim:
   `E       AssertionError: assert np.float64(0.1559487341735335) <= 1e-12`
   (test_phase_common_to_both_branches_cancels_in_each_realisation). Cause: a test-helper bug. With
   `common_phase=False` the helper skipped the random draw of psi_k, so the delta_k sequence came
   from a different generator state and the two ensembles did not share delta_k. Fix: psi_k is
   always drawn and then zeroed. Tolerance unchanged.

## Files (all new or owned by S1c)

* `reflection_holo/optics/fields.py`: `Grid`, `Wave`, `Hologram`, `sha256_array`
* `reflection_holo/optics/hologram.py`: reference models, formation, ensemble, noise
* `reflection_holo/optics/__init__.py`, `reflection_holo/reconstruction/__init__.py`: exports
* `reflection_holo/reconstruction/sideband.py`: carrier location, mask, demodulation, unwrapping,
  explicit plane fit, noise prediction
* `tests/reconstruction/holo_cases.py` (helpers; imports the calculator by path),
  `tests/reconstruction/test_roundtrip_T24_T25.py`, `test_carrier_trap.py`,
  `test_self_reference_R2.py`, `test_phase_noise.py`, `test_sideband_processing.py`
* `tests/optics/test_hologram_formation.py`

## Functions, sources and labels

| Function / class | Source map | Label |
|---|---|---|
| `Grid`, `Wave`, `Hologram` (declared pixel sizes on both axes, axes, plane, content) | physics_conventions (units, Fourier sign) | convention; pixel size PROJECT_INPUT 5 |
| `hologram_intensity` (I = \|u_o + u_r\|^2) | SM12 | SECTION_READ (P07) |
| `reference_r1_vacuum_plane_wave` (carrier required; aperture passage declared) | SM21, B5 | ASSUMPTION B5; carrier PROJECT_INPUT 16 |
| `reference_r2_self_reference` (integer-pixel shift, no wrap, valid mask) | SM22, B5 | R2 reading DERIVED_HERE |
| `reference_r3_curved_tilted` (explicit tilt, quadratic phase) | B5 | ASSUMPTION (no source); PROJECT_INPUT 17 |
| `make_reference` (by name) | B5 | - |
| `ArtefactOptions` (Fresnel fringes and drift raise NotImplementedError; charging = static phase map) | docs/05 5.5, B8 | charging PROJECT_INPUT 22 |
| `ensemble_hologram_intensity` (mean after squaring, pairs share realisation index) | SM13 | METADATA_VERIFIED/SECTION_READ |
| `apply_poisson_noise` (dose and seed required, one generator, draw order recorded) | docs/05 5.6 | dose PROJECT_INPUT 6 |
| `locate_carrier` (empty/flat-region only; centred-order argmax; `none` or `dft_ratio` sub-pixel) | SM12; audit C3 | DERIVED_HERE (dft_ratio) |
| `MaskSpec`, `sideband_mask` (disc, `none`/`hann`; refuses DC or Nyquist crossing) | SM12 | PROJECT_INPUT 19 |
| `reconstruct_sideband` (phi_o - phi_r; raw, corrected, unwrapped, amplitude, mask, carrier, resolution 1/R) | SM12 (P07 para 56) | SECTION_READ |
| `unwrap_itoh_raster` | none (standard 1-D Itoh) | needs a source-map row |
| `fit_phase_plane`, `subtract_phase_plane` (explicit region; inputs untouched) | audit M5 | - |
| `sideband_phase_noise` (N = counts in n_pix / sum W^2 pixels) | SM12 | DERIVED_HERE |

## Tests (57)

| File | Tests | T number / spec item |
|---|---|---|
| test_roundtrip_T24_T25.py | guard on the calculator's T24/T25 lines; T24 (want = calculator `sc666.step_phase(d111)['wrapped']`, tol 5e-3); T25 (0, tol 5e-3); bit equality with calculator `hologram_roundtrip` (1e-9); calculator section-12 table, 8 rows (5e-5); sign test with both carrier directions (5e-3); T24 with `dft_ratio` | T24, T25; docs/05 section 8 Holography; C section 8 sign test |
| test_carrier_trap.py | brightest object bin (511, 64) = fftshifted (255, 320) gives 0.782 / 0.781 rad (printed 0.78, tol 0.005); empty hologram gives 2.3596 (T24 tol); division at the wrong bin gives -2.3596; correct-side object search gives -0.78 | carrier-location trap; docs/03 section 6; audit C3 |
| test_self_reference_R2.py | result = mask-filtered phi(r) - phi(r+s) (1e-3); twin sign-inverted, translated by -s, not spatially mirrored | docs/03 section 6; docs/05 5.3 |
| test_phase_noise.py | 4 (mu, counts) cases x {top-hat, Hann}; K = 16, seed 20260922; tol 4 standard errors (0.94 % top-hat, 1.66 % Hann) | SM12 noise formula |
| test_sideband_processing.py | phi_o - phi_r for 4 carrier directions (1e-9); resolution = 3 fringe spacings; sub-pixel (1e-3 bins, flat 5e-3); R3 entangled/removed; no implicit detrend + explicit fit; Itoh unwrap; flat-region crop carrier; required inputs | docs/05 5.7; PROJECT_INPUT 19; audit M5 |
| test_hologram_formation.py | intensity identity; R1 on anisotropic grid and FFT sign; R2 shift; R3 phase; ensemble after squaring (contrast = \|<exp(i delta)>\|); common phase cancels; mis-pairing refused; seeded Poisson; Fresnel/drift NotImplementedError; charging = topography; missing pixel size, carrier, dose, seed raise | docs/05 5.3-5.6, section 8 Ensembles; SM13; B8 |

Noise results (pytest -s): top-hat ratios 0.9948, 1.0003, 1.0019, 1.0095 and Hann 1.0029, 1.0210,
1.0127, 1.0171 (sigma_meas/sigma_pred), all within 4 standard errors.

## Verbatim output of `venv/bin/pytest -q tests/optics tests/reconstruction`

```
.........................................................                [100%]
57 passed in 4.88s
```

## NOT IMPLEMENTED

Biprism Fresnel fringes and overlap width, and drift: these raise NotImplementedError. Also not
implemented: drifting charging (possible only as an ensemble); detector MTF; gain other than 1;
partial-coherence realisation generators (only the averaging exists); dark-field aperture
selection; projection along k_out; lens transfer; the R1 2 theta_ext inclination and its
compensation (the aperture passage is declared only); sub-pixel R2 shifts; non-disc masks; zero
padding; real-space windows; residue-aware unwrapping; validity masking when dividing by a
near-zero empty amplitude (gives NaN); a measured resolution-versus-mask-radius test.

## NOT RUN

Full repository test suite (collection only: 301 tests, no name collisions). No manifest-writing
run (no production run was made; results carry seeds, hashes and parameters; the provenance/
integration is not done). The calculator script was not re-run as a whole (its functions were
imported). No experimental hologram was processed.

## Open issues

1. The calculator's 0.78 rad is a conjugate-sideband sign error plus a one-row ramp (-2.3596 + pi).
   Its sign depends on the argmax tie-break within an exactly Hermitian pair. docs/03 section 6
   describes only the ramp.
2. docs/03 section 6 says "mirrored twin". The model gives a sign-inverted, translated twin, not a
   spatial mirror. The wording needs clarifying.
3. Which sideband holds phi_o - phi_r in an experiment is an input (PROJECT_INPUT items 10, 16).
   The sign check works only for simulated holograms.
4. N in sigma_phi: quantification/noise.py (other agent) takes N as given ("counts in the
   reconstruction aperture area"). Here N is defined from the mask and verified numerically. The
   two should be unified.
5. FFT boundary leakage for non-periodic phase (1.7e-6 rad/A gradient bias observed).
6. io/ loaders must build `Hologram` objects (the interface still has to be agreed). The source map
   needs updating: SM12/SM13 tests, and a row for the Itoh algorithm.
