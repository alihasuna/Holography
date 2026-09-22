# S2: consolidation of duplicated quantities and helpers in reflection_holo

Scope: remove duplicates so that each quantity and helper has one canonical implementation that the
other modules import. No physics and no test tolerance changed. Nothing committed or pushed.

Baseline: repository commit 608ce91 (branch claude/electron-holography-orchestration-nakd7r;
working tree clean). `venv/bin/pytest -q` before any change: `355 passed in 5.90s`.

"Before" line numbers refer to commit 608ce91; "after" line numbers refer to the working tree at the
end of this pass.

## Log

### 1. Shadow length (canonical: `reflection_holo.geometry.projection.shadow_length_A`)

Before:
* `reflection_holo/structure/shadows.py:44-51` private `_shadow_length_A(height_A, theta)` =
  `float(h) / math.tan(theta)` (a copy of the formula).
* `reflection_holo/structure/shadows.py:54-56` public labelled wrapper `shadow_length_A(h, theta,
  theta_label)` calling the private copy; `:183` (per-step nominal length in
  `terrace_shadow_strips`) and `:303` (ray-trace margin in `feature_shadow_intervals`) also called it.
* `tests/structure/test_structure_shadows.py:218-223` `test_private_shadow_helper_matches_geometry_module`
  compared the private copy with the geometry function (rel 1e-15).

After:
* `reflection_holo/structure/shadows.py:25` `from reflection_holo.geometry import projection`.
* `reflection_holo/structure/shadows.py:42-50` the labelled wrapper keeps its signature and its
  label and range checks (`_check_theta`) and returns `projection.shadow_length_A(h, theta)`; the
  private copy is deleted. `:177` and `:298` call `projection.shadow_length_A`.
* Test converted, not removed (count unchanged): `tests/structure/test_structure_shadows.py:217-244`
  `test_structure_shadow_lengths_use_geometry_module` asserts that `structure.shadows` has no
  `_shadow_length_A`, spies on `geometry.projection.shadow_length_A` and checks that the wrapper (12
  height/angle pairs, the same grid as the old test) and the per-step nominal length of a built
  single a/4 staircase call it and return exactly its value. Mutation check: with the wrapper
  temporarily reverted to an inline `|h|/tan(theta)`, this test failed (`1 failed`); restored.
* Behaviour difference (not physics): the canonical function uses `|h|`. The old private copy used
  the signed `h`, so the structure wrapper returned a negative "length" for a negative height. No
  caller passed a negative height: `terrace_shadow_strips` passes `abs(height)` and the features pass
  a positive height.
* `structure/shadows.py:33-39` `_check_theta` is kept: it enforces the theta evidence label and gives
  the `theta_ext_rad must be in (0, pi/2)` message that the structure tests match. The canonical
  function checks the range again.

`venv/bin/pytest -q tests/structure` after this change: `98 passed in 0.89s`.

### 2. Phase wrapping (canonical: `reflection_holo.geometry.specular.wrap_to_pi`)

Inventory (grep for `wrap`, `% TWO_PI`, `np.mod`, `np.angle(np.exp`, `np.unwrap` in
`reflection_holo/`): only two wrapping helpers existed, both the calculator's expression
`-((-x + pi) % 2pi - pi)` onto (-pi, +pi]. `np.unwrap` (Itoh unwrapping in reconstruction, rocking
series) and the circular median in `quantification/controls.py` are not wrapping helpers.

Choice: `geometry.specular.wrap_to_pi` is canonical. It was already imported by
`quantification/controls.py:16`, `quantification/height.py:40`, `quantification/rocking.py:27` and the
geometry and quantification tests, and the spec places the step phase (SM03, SM05) in geometry.

Before:
* `reflection_holo/geometry/specular.py:32-35` canonical definition.
* `reflection_holo/reconstruction/sideband.py:59-61` second definition (same expression; returned a
  0-d array for a scalar where the geometry one returns a float).

After:
* `reflection_holo/reconstruction/sideband.py:50` `from reflection_holo.geometry.specular import
  wrap_to_pi` (definition deleted). `reflection_holo/reconstruction/__init__.py:6-9` still exports the
  name, so `from reflection_holo.reconstruction import wrap_to_pi` (used by
  `tests/reconstruction/*`) now returns the geometry object (`is` identity checked).
* `reflection_holo/geometry/specular.py:33-39` docstring states that it is the package's one
  wrapping helper. Expression unchanged.
* Only behaviour difference: a scalar argument through the reconstruction name now gives a Python
  float instead of a 0-d array. The only scalar use, `tests/reconstruction/holo_cases.py:77`, wraps it
  in `float()`.

`venv/bin/pytest -q tests/reconstruction tests/geometry tests/quantification` after this change:
`181 passed in 5.07s`.

### 3. sigma_phi = sqrt(2)/(mu sqrt(N)), SM12 (canonical: `reflection_holo.quantification.noise.phase_noise_sigma_rad`)

What the two definitions were:
* `reflection_holo/quantification/noise.py:15-22` `phase_noise_sigma_rad(*, contrast_mu, counts_N)`:
  the formula, with N taken as given ("counts in the reconstruction aperture area").
* `reflection_holo/reconstruction/sideband.py:475-494` `sideband_phase_noise(fringe_contrast,
  counts_per_px, mask)`: its own copy of the formula (`:493`), with N = counts_per_px x A_eff and
  A_eff = n_pix / sum(W^2) pixels (about 1/(pi R^2) for a top-hat disc of radius R).

Reading of docs/03 section 6 ("N counts in the reconstruction aperture area"), SM12 and C report
section 7.4: eq. (7.3) derives sigma_phi for one sideband coefficient c = (1/M) sum_j I_j
exp(-2 pi i q_c.r_j) estimated over M pixels, with N = M I_bar, the counts in the real-space area
that the estimate averages. A reconstruction with a Fourier mask W averages each output pixel over
A_eff = n_pix / sum(W^2) pixels; the single-bin case (sum W^2 = 1) gives A_eff = M. The two modules
therefore use the same quantity. N is the counts in the real-space area of one reconstruction
resolution element; the reconstruction module gives it operationally for a given mask. The two
definitions are not physically different, so they are unified rather than kept under separate
names.

Changes:
* `reflection_holo/quantification/noise.py:20-43`: canonical. The docstring now defines N as "the
  number of detected electrons in the REAL-SPACE area of ONE reconstruction resolution element, the
  area over which one reconstructed pixel averages the hologram: A_eff = n_pix / sum_q W(q)^2 pixels"
  and states the relation to docs/03, SM12 and C eq. (7.3). It also states the scope: one hologram,
  no reference division, white Poisson noise, sigma_phi << 1. Module docstring `:1-12` updated. The
  code is unchanged.
* `reflection_holo/reconstruction/sideband.py:52` imports `phase_noise_sigma_rad`. In
  `sideband_phase_noise` (`:472-494`), `:493` now returns `phase_noise_sigma_rad(contrast_mu=mu,
  counts_N=N)`. The docstring says the function supplies N and defers to the canonical formula. The
  N computation, validation and returned keys are unchanged.
* Numerical identity: for 2000 random masks, contrasts and doses, old expression vs new call:
  `max |new - old| over 2000 random masks: 0`. The return type is still `float`.
* Reconstruction noise test, unchanged file and tolerance (|ratio - 1| <= 4 standard errors),
  `venv/bin/pytest -q -s tests/reconstruction/test_phase_noise.py`:
  ```
  apod=none mu=1.000 counts/px=100 N=18357 sigma_pred=0.01044 sigma_meas=0.01038 ratio=0.9948 rel_se=0.0094 K=16 seed=20260922
  apod=hann mu=1.000 counts/px=100 N=106376 sigma_pred=0.00434 sigma_meas=0.00435 ratio=1.0029 rel_se=0.0166 K=16 seed=20260922
  apod=none mu=0.500 counts/px=100 N=18357 sigma_pred=0.02088 sigma_meas=0.02088 ratio=1.0003 rel_se=0.0094 K=16 seed=20260922
  apod=hann mu=0.500 counts/px=100 N=106376 sigma_pred=0.00867 sigma_meas=0.00885 ratio=1.0210 rel_se=0.0166 K=16 seed=20260922
  apod=none mu=0.250 counts/px=100 N=18357 sigma_pred=0.04175 sigma_meas=0.04183 ratio=1.0019 rel_se=0.0094 K=16 seed=20260922
  apod=hann mu=0.250 counts/px=100 N=106376 sigma_pred=0.01734 sigma_meas=0.01757 ratio=1.0127 rel_se=0.0166 K=16 seed=20260922
  apod=none mu=0.500 counts/px=10 N=1836 sigma_pred=0.06601 sigma_meas=0.06664 ratio=1.0095 rel_se=0.0094 K=16 seed=20260922
  apod=hann mu=0.500 counts/px=10 N=10638 sigma_pred=0.02742 sigma_meas=0.02789 ratio=1.0171 rel_se=0.0166 K=16 seed=20260922
  8 passed in 1.54s
  ```
  Consistency check: top-hat, R = |q_c|/3 = 1/24 cycles/A, 1 A pixels (`holo_cases.make_grid`), so
  1/(pi R^2) = 183.3 A^2, and N/(100 counts/px) = 183.57 px (disc pixelation).
  `tests/quantification/test_quant_noise.py` (calculator table, docs/03 example): 8 passed.
* Also unchanged: dividing by an equally noisy empty hologram multiplies sigma by sqrt(2). This is
  stated in `sideband_phase_noise` and has no function of its own.

### 4. Evidence-label checker (canonical: `reflection_holo.io.labels.require_evidence_label`)

Before, three checkers:
* `reflection_holo/io/config.py:48-50` `EVIDENCE_LABELS`, `TEST_ONLY_LABEL`, and `:238-245` the
  inline check in `_parse_parameter`: the label must equal one of the seven labels, and TEST_ONLY is
  accepted only with `allow_test_only` (raises `ConfigError`).
* `reflection_holo/structure/si001.py:43` `LABEL_PREFIXES = ("PROJECT_INPUT", "TEST_ONLY",
  "ASSUMPTION")`, `:58-63` `_check_label` (a non-blank string starting with one of the prefixes;
  `ValueError`), called at `:398` (overlayer) and `:443` (azimuth).
* `reflection_holo/structure/shadows.py:26` `_LABEL_PREFIXES` (the same tuple) and `:29-33`
  `_check_label` (same rule, different message), called at `:37` (theta) and `:230` (feature).

Choice: io's version is canonical. It is moved out of `_parse_parameter` into the new module
`reflection_holo/io/labels.py`, which imports only the standard library. Importing
`reflection_holo.io.config` directly would not create a cycle (io imports geometry, never
structure), but it would make structure import yaml and the configuration loader to check a string.
The module lives in io/ as instructed; it is not a shared module outside io.

After:
* `reflection_holo/io/labels.py:17-20` `EVIDENCE_LABELS`, `TEST_ONLY_LABEL`, `KNOWN_LABELS`;
  `:23-49` `require_evidence_label(label, what, *, accepted, qualified, error=ValueError)`. With
  `qualified=False` the label must equal an accepted label (configuration files). With
  `qualified=True` it must start with one and may carry text such as "PROJECT_INPUT item 8"
  (in-memory labelled arguments). `accepted` must be a subset of the known labels.
* `reflection_holo/io/config.py:47` imports the names from `io.labels`, so
  `io.config.EVIDENCE_LABELS` still exists for `tests/io`. `:236-242`: the TEST_ONLY-from-file policy
  message stays in config (it is loader policy); the membership check calls
  `require_evidence_label(..., qualified=False, error=ConfigError)`.
* `reflection_holo/structure/si001.py:37` imports it. `:44` `LABEL_PREFIXES` is kept as structure's
  policy (which labels a caller may attach to a physical argument). `_check_label` is deleted;
  `:391-392` and `:437-438` call `require_evidence_label(..., accepted=LABEL_PREFIXES,
  qualified=True)`.
* `reflection_holo/structure/shadows.py:26,28` import the checker and `LABEL_PREFIXES` from
  `.si001`. `_LABEL_PREFIXES` and `_check_label` are deleted; `:34-35` and `:224-225` call the
  canonical checker.
* Equivalence check: the old `si001._check_label`, old `shadows._check_label` and old io inline
  logic (read from git HEAD) were compared with the new calls on 28 labels, including None, "", "  ",
  3, a list, "PROJECT_INPUTS", "ASSUMPTIONAL", " PROJECT_INPUT", lower case, all seven labels,
  qualified forms, and io with `allow_test_only` both False and True. Output:
  `prefix tuples equal: True` / `labels checked: 28 mismatches: []`.
* Message changes: every message still contains "label", which is what the tests match. The
  structure/shadows wording is now the si001 wording. The io membership message changed from
  "has label X, not one of (...)" to "label X is not one of (...)".

`venv/bin/pytest -q tests/io tests/structure` after this change: `148 passed in 1.05s`.

### 5. Other duplicates: survey, the two consolidated, and those left

Survey method: every `def` and module-level constant in `reflection_holo/*/*.py` was listed; the
package was grepped for wavelength and constants (`HC_EV_M`, `M_E_C2_EV`, `5.43`, `2 * np.pi`),
hashing, grid/frequency helpers, angle-range checks, and the shadow, noise, wrap and label helpers.
Results for wavelength, constants and grids:
* Wavelength: one implementation, `geometry/wavelength.py`. No other package module computes it;
  quantification takes `wavelength_A` as an argument. Physical constants are defined only in
  `constants.py`. The calculator in `tools/` is the reference implementation the tests compare
  against, outside the package, and was not touched.
* Grids: `optics.fields.Grid` is the only coordinate/frequency grid, and reconstruction uses its
  methods. `geometry.sampling` (anti-aliasing band limits) and `geometry.plate_cell` (cell geometry)
  compute other quantities.

Consolidated (identical in meaning and in floating-point result):
* Reference-model names R1/R2/R3 (docs/05 section 5 item 3). Before: `reflection_holo/io/config.py:61`
  and `reflection_holo/optics/hologram.py:56`, two identical tuples. After: canonical
  `optics/hologram.py:56`; `io/config.py:48` imports it and the io definition is deleted. The
  valid names are those that optics implements. `io.config.REFERENCE_MODELS is
  optics.hologram.REFERENCE_MODELS` is True.
* Foreshortening 1/sin(theta_ext) (SM07, T20). Before: `reflection_holo/geometry/specular.py:93-97`
  (`SpecularCondition.foreshortening`, its own `1.0 / np.sin(theta_ext)`) and
  `geometry/projection.py:37-39` (unchanged). After: canonical `projection.foreshortening`; `specular.py:28`
  imports it and `:97-102` (property at `:98`) returns `_foreshortening(self.theta_ext)`. Over 65 accessible conditions
  (d_111, d_001, d_110 rods, orders 1-24, 200 keV, 12 V): `max |new - old|: 0.0`.

Full suite after this step: `355 passed in 6.17s`. Each module also imports on its own in a fresh
process; importing `reflection_holo.structure` does not import yaml or `io.config`.

## Left duplicated, and why

1. Shadow masks: `quantification/shadow.py` (`shadow_masks`) and `structure/shadows.py`
   (`shadowed_intervals`, `periodic_shadowed_intervals`, `terrace_shadow_strips`,
   `feature_shadow_*`). They overlap only for the illumination shadow of piecewise-constant terraces
   with vertical risers. quantification also computes the blocked-view (exit-side) strip and the
   usable mask on sampled coordinates, without periodicity. structure computes the illumination
   shadow only, but for piecewise-linear profiles (sloped sidewalls), periodic cells and as
   intervals. They are not identical in meaning, so they were not merged. Open issue (not changed):
   since commit 8913007, docs/03 section 4 and docs/05 section 4.5 require the blocked-view strip to
   be masked as well. The `structure/shadows.py:11-13` docstring ("exit-side occlusion is not part
   of the documented model ... NOT IMPLEMENTED") is now out of date, and structure's shadows lack
   that strip.
2. Wrap period h_2pi: `geometry/specular.py:88` (`SpecularCondition.h_2pi_A = lam/(2 sin
   theta_ext)`, NaN when inaccessible), `quantification/height.py:83-91` (`wrap_period_A`, general
   theta_in != theta_out, raises `SmallDenominatorError`) and `height.py:162` (`TWO_PI / s` inside
   `height_from_phase`). They mean the same thing for the specular beam, but merging needs a
   layering decision. Spec 4.1 puts h_2pi in geometry, yet the general function and its error class
   live in quantification, and geometry must not import quantification. `height.py:162` is also a
   different arithmetic path (tested against `h_2pi_A` at 1e-12).
3. Height noise term: `quantification/noise.py:46-48` (`h_2pi sigma_phi / 2 pi`) and the
   `sigma_phi / s` term inside `height.py:158` (a quadrature sum with the sensitivity uncertainty).
   The quantity is the same, but it is inline in a larger formula, not a helper.
4. Specular step phase: `SpecularCondition.step_phase` (`-2 h K_ext`, the calculator port) and
   `specular_step_phase` (`-(4 pi/lambda) h sin theta_ext`), both in `geometry/specular.py`. The
   arithmetic paths differ (K_ext against k sin(arcsin(K_ext/k))), so merging would change the
   calculator-port values at rounding level. Related but different: `dphi_dtheta` (`specular.py:119`)
   and `quantification/rocking.py:max_tilt_step_rad` (= pi / dphi_dtheta).
5. Angle-range validators with different intervals and messages:
   `geometry/projection.py:_check_theta` (open), `structure/shadows.py:_check_theta` (open plus a
   label), `quantification/height.py:_angles` and `specular.beam_wavevectors_slab` (closed
   [0, pi/2]), `rocking.max_tilt_step_rad` ([0, pi/2)), and `quantification/shadow.shadow_masks`
   (open). Other input validators: `optics/hologram._require_finite` and `reconstruction/sideband.
   _positive`. Tests match some of these messages.
6. Hashes: `optics.fields.sha256_array` (dtype + shape + bytes); `structure/si001.py:588` (raw
   `<f8` bytes of the positions, recorded as `positions_sha256`); `io.config.canonical_sha256`
   (canonical JSON); `provenance.manifest.sha256_file` against `io/config.py` (end of
   `load_config_file`, `:416`) `hashlib.sha256(blob)`. The first three are different definitions, and
   unifying them would change recorded hashes. The last pair mean the same thing, but io hashes the
   exact bytes it parsed in one read, and `sha256_file` would read the file a second time.
7. Step-edge names: `io/config.py:60` `STEP_EDGE_ORIENTATIONS = ("parallel_to_beam",
   "transverse_to_beam")` and `structure/si001.py` `Staircase.edges in ("parallel", "transverse")`.
   Same meaning, different spellings in a configuration schema and a builder API; unifying would
   change one of those interfaces.
8. `structure/shadows.shadow_length_A(h, theta, theta_label)` and
   `geometry/projection.shadow_length_A(h, theta)` share a name. The structure one is a labelled
   wrapper with no copy of the formula (change 1).

## Final full suite (verbatim, `venv/bin/pytest -q`, after all changes)

```
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 81%]
...................................................................      [100%]
355 passed in 5.96s
```

Test count: 355 before and 355 after. No test was removed. The one test that only compared two
copies, `tests/structure/test_structure_shadows.py::test_private_shadow_helper_matches_geometry_module`,
was converted in place into `test_structure_shadow_lengths_use_geometry_module` (change 1). No
tolerance was changed, and no other test file was edited.

## Canonical choices (summary)

| quantity / helper | canonical | users now importing it |
|---|---|---|
| shadow length abs(h)/tan(theta_ext) | `geometry.projection.shadow_length_A` | `structure.shadows` (labelled wrapper, per-step lengths, feature margin) |
| phase wrap to (-pi, pi] | `geometry.specular.wrap_to_pi` | `quantification.{controls,height,rocking}`, `reconstruction.sideband` (re-exported) |
| sigma_phi = sqrt(2)/(mu sqrt(N)) | `quantification.noise.phase_noise_sigma_rad` (N defined in its docstring) | `reconstruction.sideband.sideband_phase_noise` (supplies N from the mask) |
| evidence-label check | `io.labels.require_evidence_label` (+ `EVIDENCE_LABELS`, `TEST_ONLY_LABEL`) | `io.config`, `structure.si001`, `structure.shadows` |
| reference-model names R1/R2/R3 | `optics.hologram.REFERENCE_MODELS` | `io.config` |
| foreshortening 1/sin(theta_ext) | `geometry.projection.foreshortening` | `geometry.specular.SpecularCondition.foreshortening` |

## NOT RUN

No simulation, engine, configuration validation CLI or manifest-writing run: this pass changed library
code and one test only. No commit or push.

## Follow-up: blocked-view strip

Coordinator request: `structure/shadows.py` must also return the blocked-view strip (length
h/tan(theta_out) of the lower terrace in front of a transverse riser whose upper terrace is
downstream), preferably by delegating to `quantification/shadow.py`, record per step which strip
applies, update the docstring (old lines 11-13), and add tests. Baseline for this step: 355 passed
(end of the consolidation above).

Delegation. `quantification/shadow.py` imports only numpy, so importing it from structure raises no
import problem, and the masking decisions are delegated to it. It returns boolean masks at sample
points, while `ShadowStrips` returns exact half-open intervals on a periodic cell. The new helper
therefore samples only at the midpoints between exact candidate strip ends. The candidates are every
riser and riser +- dh/tan(theta) for each riser corner and each lower terrace level, with dh/tan
from `geometry.projection.shadow_length_A`. The masks are constant between candidates, so the
intervals are exact. The illumination shadow of staircases now goes through the same path, so both
strips of a staircase come from one implementation.

Changes to `reflection_holo/structure/shadows.py` ("before" = commit 36fbe25):
* Docstring: old `:11-13` ("Only the INCIDENT-beam shadow ... exit-side occlusion ... NOT
  IMPLEMENTED") is replaced by new `:11-20`. It describes both strips, the delegation and the
  required exit angle, and says the patterned features still give the illumination shadow only.
* `:34` `from reflection_holo.quantification import shadow as quantification_shadow`; `:39`
  `_BREAK_TOL_A = 1e-6` (strip ends closer than this are merged, which matters only in degenerate
  geometry).
* `_check_theta` (old `:33`, new `:42`) takes keyword `name`/`what`, so the exit angle gets its own
  label context and the message `theta_out_ext_rad must be in (0, pi/2)`. The incidence behaviour is
  unchanged.
* `ShadowStrips` (old `:136-147`, new `:145-180`) adds `illumination_intervals_A`,
  `blocked_view_intervals_A`, `theta_out_ext_rad`, `theta_out_label`, `illumination_mask()` and
  `blocked_view_mask()`. The meaning of `intervals_A` and `mask()` changed from "illumination shadow"
  to "union of both strips (everything to mask)".
* New `_periodic_terrace_strips` (`:182-232`): unrolls the periodic profile, collects the candidate
  strip ends, and calls `quantification_shadow.shadow_masks`; `~illuminated` gives the illumination
  intervals and `~visible` the blocked-view intervals.
* `terrace_shadow_strips` (old `:150-182`, new `:235-289`) has new required keyword-only arguments
  `theta_out_ext_rad` and `theta_out_label`, with no default (they equal theta_in and its label for
  the specular beam). Each per-step record (`:266-281`) gains `strip` ("illumination_shadow" or
  "blocked_view"), `strip_side`, `strip_angle` ("theta_in" or "theta_out"), `nominal_strip_A`,
  `nominal_blocked_view_length_A` and `height_A`. `nominal_shadow_length_A` is kept (0 for a
  blocked-view step).
* Unchanged: the feature functions and the `shadowed_intervals` / `periodic_shadowed_intervals`
  primitives (the features use `shadowed_intervals`).

Changes to `tests/structure/test_structure_shadows.py`:
* Existing tests, updated for the new API (values and tolerances unchanged). `:23-26` adds the
  helper `specular_strips(s)` (theta_out = theta_in, TEST_ONLY label), which replaces the 7 calls
  `terrace_shadow_strips(s, THETA_22P5_MRAD, THETA_LABEL)` at old `:53, 73, 84, 92, 102, 115, 241`.
  `sh.intervals_A` becomes `sh.illumination_intervals_A` in the illumination assertions of
  `test_built_single_a4_step_shadow_is_60A` (`:63-64`), `test_built_a2_step_shadow_is_twice` (`:80`),
  `test_shadow_cut_short_by_next_rise` (`:91`), `test_shadow_over_two_descending_steps` (`:101`) and
  `test_shadow_wraps_across_the_periodic_boundary` (`:112-113`). `sh.mask` becomes
  `sh.illumination_mask` at `:115`, where the old expectation `False` at `z_edge + lsh - L + 0.1` is
  inside the blocked-view strip of the up-step. In the S2 guard test,
  `calls == [(Q, theta)]` becomes `(Q, theta) in calls` (`:337`), because
  `terrace_shadow_strips` now also calls `shadow_length_A` for the strip ends.
* New tests (`:126-210`):
  - `test_blocked_view_strip_in_front_of_upper_terrace_downstream_step` (`:141`). Single a/4
    staircase with theta_out = 30 mrad (TEST_ONLY), so that theta_out and theta_in can be told
    apart. The strip ends at the up-step riser (30 x P110, abs 1e-9) and has length
    Q/tan(theta_out) = 45.26 A (abs 1e-9). Checked: masks either side of both ends, the per-step
    record, and equal lengths for the specular beam.
  - `test_no_blocked_view_in_front_of_upper_terrace_upstream_step` (`:171`). For specular and
    non-specular exit angles, nothing is masked in the 100 A in front of the down-step riser at the
    cell edge. The only blocked-view strip ends at the up-step, and the down-step record says
    "illumination_shadow" with a zero blocked-view length.
  - `test_blocked_view_cut_short_by_preceding_rise` (`:190`). The lower 5-period terrace in front
    of an up-step is blocked exactly over [20, 25] x P110; the strip is cut by the higher terrace
    upstream.
  - `test_exit_angle_required_labelled_and_checked` (`:200`). A missing exit angle gives TypeError,
    an unlabelled one ValueError "label", and 0, -0.01 or pi/2 ValueError "theta_out_ext_rad".

Verification beyond the tests:
* Mutation: with `shadow_masks` temporarily given theta_in as the exit angle, the new test failed
  (`1 failed, 23 passed`). File restored (`cmp` identical).
* Independent cross-check (scratch script, not a test). For 388 random periodic staircases (2-6
  terraces, integer widths 3-80 A, heights k x 1.25 A, theta_in and theta_out drawn independently
  in 5-80 mrad), the delegated intervals were compared with structure's own ray trace:
  `periodic_shadowed_intervals` for the illumination shadow, and the same sweep on the z-mirrored
  profile for the blocked view. Output: `random periodic staircases compared: 388 | illumination
  intervals: 625 | blocked-view intervals: 630 | max endpoint difference (A): 2.5579538487363607e-13`.
* Found while doing this, pre-existing and not fixed: `periodic_shadowed_intervals` unrolls with
  `pts + k*Lp`. For a period that is not exactly representable, `k*Lp + Lp` can exceed `(k+1)*Lp` by
  one ulp and raise "profile z coordinates must be non-decreasing". It happened with random float
  widths in the cross-check. Terrace staircases no longer use it; the built cells tested here
  (multiples of P110) did not trigger it.

`venv/bin/pytest -q` (verbatim):

```
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 80%]
.......................................................................  [100%]
359 passed in 6.08s
```

The count went from 355 to 359: the 4 new tests. No test was removed and no tolerance changed.

Still open:
* Patterned features (`feature_shadow_intervals`, `feature_shadow_mask`) return the illumination
  shadow only. Adding their blocked-view strip needs an API decision: an exit-angle argument, and a
  change to the single interval list those functions return.
* The exit angle has no docs/06 item; item 7 covers the incidence angle only. For the specular beam
  it equals the incidence angle.
* Section 5, item 1 above (shadow masks left duplicated) now applies only to the patterned
  features. Staircase strips are computed by `quantification/shadow.py`.

NOT RUN: no simulation, engine or manifest-writing run. Not committed.

## Follow-up 2

Coordinator request (the orchestrator decided the API): (1) patterned mesas and trenches get the same
API as terraces: `theta_out_ext_rad` and `theta_out_label` required with no default, both strips per
edge, and a field for each strip alone. Tests for a mesa and a trench at 0 and 90 degrees; sloped
edges handled as the geometry dictates and labelled DERIVED_HERE. (2) Fix the pre-existing failure
of `periodic_shadowed_intervals` for inexact periods, with a regression test that fails before the
fix. "Before" line numbers refer to commit f5a2a00; "after" line numbers to the working tree.
`tools/physics_checks/q1_si001_quarter_step_symmetry.py` shows as modified in the working tree; it
belongs to another agent and was not touched here.

### (2) `periodic_shadowed_intervals` for inexact periods

Cause: the unrolled profile was built as `pts + k*period`. For many periods, `fl(k*period) + period`
exceeds `fl((k+1)*period)` by one ulp, so the unrolled z decreased at a period join and
`shadowed_intervals` raised "profile z coordinates must be non-decreasing". Examples: 0.2, 0.3 and
0.7 A, and 1 and 2 x P110 (a Si(001) cell of one or two [110] rows). A second trigger: an end point
accepted by the existing check |z_end - period| <= 1e-9 A but lying above the period made every join
decrease.

Fix, `reflection_holo/structure/shadows.py` (old `:106-127`, new `:123-160`):
* Offsets are accumulated, o_(k+1) = o_k + period. The end of period k, fl(period + o_k), is then
  bit-identical to the start of period k + 1, fl(0 + o_(k+1)). Rounding is monotone, so the unrolled
  z is non-decreasing by construction. No tolerance is involved.
* The end point, already accepted by the existing 1e-9 A check (`_F_TOL_A`, unchanged), is placed
  exactly at the period, and so is any point in that accepted band above the period
  (`np.minimum(z, period)`). No new tolerance is introduced. A z sequence that decreases is now
  refused explicitly, before unrolling, with the same message as before.
* Interval ends at the cell edges are returned as exactly 0 and period, instead of
  `end - last` (which could differ from the period by rounding).

Regression tests, `tests/structure/test_structure_shadows.py`:
* `:229-238` `test_periodic_ray_trace_inexact_periods_regression`, parametrised over periods 0.2,
  0.3, 0.7, P110, 2 x P110, 3 x P110, 25 x P110 and 100.1 A. The profile falls by Q at half the
  period and rises again at the cell edge; the expected shadow is
  [period/2, min(period/2 + Q/tan theta, period)) (abs 1e-9, the file's existing tolerance for
  exact interval ends).
* `:241-250` `test_periodic_ray_trace_end_point_within_accepted_tolerance_regression`. The end point
  is 5e-10 A above the period, inside the accepted band, and gives the correct [50, 100). An end
  point 2e-9 A above, outside the band, is still refused.
* Before the fix (same tests on the unfixed code), verbatim tail:
  ```
  =========================== short test summary info ============================
  FAILED tests/structure/test_structure_shadows.py::test_periodic_ray_trace_inexact_periods_regression[0.2]
  FAILED tests/structure/test_structure_shadows.py::test_periodic_ray_trace_inexact_periods_regression[0.3]
  FAILED tests/structure/test_structure_shadows.py::test_periodic_ray_trace_inexact_periods_regression[0.7]
  FAILED tests/structure/test_structure_shadows.py::test_periodic_ray_trace_inexact_periods_regression[3.8402262179460207]
  FAILED tests/structure/test_structure_shadows.py::test_periodic_ray_trace_inexact_periods_regression[7.680452435892041]
  FAILED tests/structure/test_structure_shadows.py::test_periodic_ray_trace_end_point_within_accepted_tolerance_regression
  6 failed, 3 passed, 24 deselected in 0.13s
  ```
  After the fix: `10 passed, 23 deselected in 0.03s` (regression and primitive tests).
* Wider check, not a test: 3400 periods (0.1 to 300 A in steps of 0.1 A, and 1 to 400 x P110) with
  the same profile against the analytic interval gave `max endpoint error (A):
  4.547473508864641e-13`, with no failure.

### (1) Patterned features: both strips per edge

Changes to `reflection_holo/structure/shadows.py`:
* Module docstring: new `:10-13` (definition of the blocked-view condition and of the mirror
  z -> -z) and new `:24-36`, which replace old `:19-20` ("Patterned features ... return the
  illumination shadow only; their blocked-view strip is NOT IMPLEMENTED"). The new text states the
  feature API, why features are ray-traced here rather than delegated (their sidewalls are sloped,
  and `quantification.shadow.shadow_masks` handles vertical risers only), and the sloped-edge rule
  as DERIVED_HERE.
* `:56` `_EXIT_ANGLE_WHAT`, the label context for the exit angle, now shared by
  `terrace_shadow_strips` (`:304`) and the feature functions (`:496`, `:540`).
* New primitive `blocked_view_intervals(points, tan_theta_out)` (`:163-177`, DERIVED_HERE): a point is
  blocked when a downstream surface point lies above the outgoing ray. By the mirror z -> -z this is
  `shadowed_intervals` of the mirrored profile at tan(theta_out), mapped back. It is exact for
  piecewise-linear profiles. The blocked set is open at both ends and is reported half-open like the
  illumination intervals; the difference has measure zero.
* `ShadowStrips` docstring (`:207-209`): `per_step` holds one record per step (staircases) or per
  transverse edge on the line (features); `period_A` is None for features.
* New `_feature_edge_records` (`:451-479`). One record per edge ("upstream", "downstream"):
  `rising_along_beam`, `upper_terrace_upstream`, `strip` ("blocked_view" for a rising edge,
  "illumination_shadow" for a falling edge), `strip_side`, `strip_angle`, `height_A` (local),
  `top_edge_A`, `foot_A`, `sidewall_run_A`, `casts_strip`, `sidewall_in_strip`,
  `nominal_strip_A` (measured from the top edge, None when no strip) and `nominal_length_A`.
* `feature_shadow_intervals` (old `:399-406`, new `:482-512`) now takes `theta_out_ext_rad` and
  `theta_out_label` as required keywords and returns a `ShadowStrips` with period_A None:
  `illumination_intervals_A` (sweep at tan theta_in, as before), `blocked_view_intervals_A` (mirrored
  sweep at tan theta_out), `intervals_A` (their union), the mask methods and `per_step` (the edge
  records). The flat margin of the profile is now max(h/tan theta_in, h/tan theta_out) + length + 1 A.
  The margin only extends the flat surroundings; the illumination results are unchanged.
* New `FeatureShadowMasks` (`:514-530`) and `feature_shadow_mask` (old `:409-418`, new `:533-552`):
  the exit angle is required, and the result has fields `mask` (union), `illumination_mask` and
  `blocked_view_mask`, each (ny, nz), plus the grids, angles and labels.
* `reflection_holo/structure/__init__.py:8-10, 15-16` export `FeatureShadowMasks`.

Sloped (linear) edges, DERIVED_HERE from the exact ray trace. Each wall is compared with the ray
that meets it: theta_in for a wall falling along the beam (mesa back, trench front), theta_out for
a wall rising along the beam (mesa front, trench back).
* A wall steeper than that ray (alpha > theta) lies inside its strip. The strip is measured from the
  top edge of the wall with length h/tan(theta), i.e. h/tan(theta) - h/tan(alpha) beyond the foot.
* A wall at or below that angle casts no strip (grazing counts as lit or visible, as in the existing
  sweep).
* On a line crossing a sloped side wall parallel to the beam, the local height is reduced, and the
  strips follow from the local profile.

Existing feature tests, updated for the API; values and tolerances are unchanged. `:260-265` adds
`SPECULAR_EXIT` and the helper `specular_feature(f)` (theta_out = theta_in, TEST_ONLY label).
Illumination assertions now read `.illumination_intervals_A` at old `:239, 246, 252, 264, 270`.
Old `:259` `== []` becomes `.illumination_intervals_A == ()`. Old `:279-280`: the mask call passes
the exit angle and reads `m.illumination_mask`. In `test_feature_inputs_required_and_checked` (old
`:292-308`) every call passes the exit angle. Without it these calls would raise TypeError before
reaching the error each one is meant to test.

New feature tests (`:374-479`):
* `test_feature_both_strips_per_edge_mesa_and_trench[kind, orient]` (`:374-425`), 4 cases: mesa and
  trench at 0 and 90 degrees. Vertical edges, h = 10 nm, (1000 nm, 300 nm), theta_in = 22.5 mrad,
  theta_out = 30 mrad (TEST_ONLY).
  - Mesa: blocked view [-L/2 - h/tan theta_out, -L/2) and shadow [L/2, L/2 + h/tan theta_in).
  - Trench: shadow on the floor behind the front wall and blocked view in front of the back wall,
    each cut by the other wall at 90 degrees, where the 300 nm floor is shorter than both strips.
  - Also checked: the edge records, and an independent comparison with
    `quantification.shadow.shadow_masks` on 4001 points (points within 1e-6 A of a strip end are
    excluded; that exclusion only avoids sampling exactly at an end). The 2-D mask fields (each strip
    alone, their union) are checked too, and a line outside the feature is clear.
* `test_feature_sloped_edges_compared_with_their_own_ray_angle` (`:428-465`).
  - alpha = 0.3 rad: both walls lie inside their strips, measured from the top edges.
  - alpha = 26 mrad, between theta_in and theta_out: the back wall shadows (598.4 A beyond its
    foot), and the front wall blocks nothing.
  - A trench with 26 mrad walls at the specular angle: both strips appear, measured from the
    opening edges.
  - Interval tolerance is abs 1e-6 A for sloped profiles: the sweep interpolates along the slope,
    whereas vertical risers are exact to 1e-9. This is a test tolerance, stated here; no code
    tolerance changed.
* `test_feature_exit_angle_required_labelled_and_checked` (`:468-479`): a missing exit angle gives
  TypeError for both functions, an unlabelled one ValueError "label", and 0 ValueError
  "theta_out_ext_rad".
* Mutation check: with the feature blocked view temporarily computed at theta_in, 4 tests failed
  (`4 failed, 35 passed`); trench at 90 degrees cannot see the difference, since both strips cover
  its whole floor. File restored (`cmp` identical).

### `venv/bin/pytest -q` (verbatim)

```
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 77%]
........................................................................ [ 96%]
..............                                                           [100%]
374 passed in 6.56s
```

Count: 359 before and 374 after, +15 new: 8 + 1 periodic regression, 4 mesa/trench, 1 sloped edges,
1 exit angle. No test was removed and no tolerance was changed.

Open: trench and mesa orientations other than 0 and 90 degrees, and edge profiles other than
vertical and linear, remain NOT IMPLEMENTED, as before. NOT RUN: no simulation, engine or manifest
run. Not committed.
