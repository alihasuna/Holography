# A2c: verification of the round-2 fixes (S3 "Round 2" and "Round 2, last item")

Status: COMPLETE, 2026-09-22. Agent A2 (code auditor). Only this file was written; A2 and A2b are
unedited. No code, test or config was modified.

Scope: `git diff d35b751 017761d -- reflection_holo tests configs pyproject.toml tools`. The in-scope files
at HEAD `a4f607f` are identical to `017761d` (`git diff --quiet 017761d HEAD -- reflection_holo/{io,
quantification,reconstruction,structure,optics,geometry,provenance} tests configs pyproject.toml tools`);
`reflection_holo/forward/` and `pipeline/` are out of scope and were ignored. On HEAD:
`venv/bin/pytest -q` -> `580 passed, 6 warnings in 19.73s`; the calculator gives `25/25`;
`tools/phase1_numbers.py` gives `19/19`. T1-T25 (`e3_tvalues.py`) are identical to A2 and A2b.

Scripts are in `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/audit/`:
`r*.py` from A2b re-run unchanged; `r7*_v2.py` changed only for the renamed argument
(`empty_min_visibility=0.5`, the holo_cases value); new probes `r5b_registry_bypass.py`,
`r7d_none_and_speed.py`, `r10c_alias_flag.py`, `r10d_phase_branch.py`, `e4_checks.py`.

## Verdicts

| Item | Verdict | Evidence |
|---|---|---|
| N1 gate bypass by labelling | FIXED, with new bypasses (G1-G3 below) | `r5` unchanged: DERIVED_HERE, SECTION_READ, REPRODUCED, METADATA_VERIFIED refused ("label ... is not accepted"); A3, B2 and B17 on item 8 refused ("not mapped to PROJECT_INPUT item 8 by the registry"); `r5b`: B1 and B17 on items 3-15 refused |
| N2 sigma_h excluding intercept systematics | FIXED | `r10` unchanged: sigma_h 0.0144 A (free slope). Constant residual delta 0.1/0.3/0.45 rad -> mean error -0.1/-0.2/-0.7 sigma_h; 0.1 mrad angle offset -> +0.9 sigma_h (A2b: -9.2/-27.4/-41.2 and +45.8). Unbiased case std(err)/sigma_h 0.98. The small residual shift is the selection by the intercept check, as S3 derives |
| N3 under-declared noise | NOT FIXED in code (decision); the decision holds, B16 wording imprecise (D1) | `r10d`: with 31 % under-declaration the returned PHASE branch indices are wrong in 1.75e-2 of accepted series, but the HEIGHT is no longer affected by the branch: \|err\| > 3 true sigma_h 2.6e-3 (Gaussian 2.7e-3), > 5 sigma_h 0; the reported sigma_h is 0.76 of the true one |
| N4 aliasing above h_max | FIXED (flag, not refusal, on uniform grids) | `r10b` unchanged: uniform grid still returns the aliased heights (622/1981/1979 accepted); `r10c`: 497 of 497 accepted aliases carry `aliasing_undetectable=True` and a RuntimeWarning. Designed series (13 tilts, 20.00-24.71 mrad, scan limit 99.8 A): true h 3 and 10 A accepted (400/400, 399/400; std/sigma_h 0.97, 0.95); 26, 30, 40, 89.8, 119.7, 199.5, 299.3 A accepted 0 of 400 each (up to 3x the scan limit) |
| N5 unwrapper | FIXED | `r7_v2`: unwrapped NaN count 1792 = exactly the invalid pixels; rows 40-119: 0 NaN (A2b: 15 872 and 10 240). `r7b_v2`: R2 shift (0, -16): 14336 of 14336 valid pixels unwrapped (A2b: 0). Run time `r7d`: 2048x2048 with 10 % random invalid pixels 10.0 s, 368 regions |
| N6 median-relative threshold | FIXED for divide_empty; residual on reference_correction="none" (R1 below) | `r7c_v2`: outside-overlap pixels flagged valid 0 of 256 / 5888 / 8448 at 80 / 45 / 30 % overlap (A2b: 256, 4755, 8236); inside rms 0.011-0.012 rad unchanged. `r7b_v2` noiseless: 0 of 1280/6912/9472 |
| N7 tiny positive sigmas | declined; the reason holds | a realistic sigma_phi gives an honest sigma_h (A2b r8: 5.99e+04 A for theta = 1e-9 rad); only fabricated sigmas give nonsense |
| N8 non-finite values | FIXED | inf and nan refused with a valid PROJECT_INPUT label ("must be a finite positive number"); 1e300 mrad accepted (Nit R3) |
| N9 registry location | FIXED | `reflection_holo/io/assumption_registry.yaml`, importlib.resources, declared in `pyproject.toml` package data |
| NIT accessibility `>=` | declined; decision harmless, reason inconsistent (D2) | `r8`: `is_accessible` at `G.n = 2 dK` exactly -> True |
| E4 M3 R2 strip sign | FIXED (test; no code change needed) | `e4_checks.py`, own hologram: n.s = +20 -> strip [108,128) at -0.865 rad; n.s = -20 -> [128,148) at +0.865 rad (sign as E4; magnitude band-limited, strip 20 px < resolution 24 px); `test_r2_step_strip_sign_and_width` passes |
| E4 M1 scope clause | FIXED | CFG-B description and `step_translations.single_layer.relation`, and `si001.py:354-360` (`B4_A4_100`, `B4_A4_110`), carry the beam, reconstruction/overlayer and azimuthal-spread clauses. Direct listing: all 8 <100> a/4 steps give `B4_A4_100`, all 8 <110> give `B4_A4_110` (the `r12` "92 x" line is a false positive of my probe: the new <100> text contains "does not apply to beams leaving ...") |
| E4 m8 step-type name | FIXED | CFG-B `step_types` = `single_layer_a4`, ...; the old `single_layer_a4_screw_related` and unknown names refused (`e4_checks.py`) |
| E4 m5 CFG-B header | FIXED | header names items 3, 4, 5, 7, 8, 12, 13 (not blocking, required here) and 15, and the missing item-11 fields |
| E4 n10 CFG-A item 9 | FIXED | CFG-A target/recommended reflections carry no `item` |
| E4 n1 docstring | FIXED | `tests/geometry/test_geom_projection.py:68-72` |

Test integrity: no existing tolerance was loosened (round-2 diffs of the 9 modified test files). The
changes are renames; new-parameter values (visibility 0.01/0.6 for the old relative thresholds 0.0/0.5,
with the reason in a comment); and the wrong-branch criterion of `test_quant_rocking_noise.py`, now judged
by the phase branch indices because h no longer depends on n (same binomial bound).
`test_quant_rocking.py`'s `|h - h_true| < 4 sigma_h` is wider in absolute terms because sigma_h is now the
honest free-fit value (0.0144 vs 0.0010 A), per the N2 decision. The new tests (`test_io_config_stand_ins`,
`test_quant_rocking_offsets`, `test_quant_rocking_alias`, `test_validity_round2`, `test_io_cfg_b_text`)
compare against Monte Carlo, derived predictions or explicit refusals; none compares an implementation
with itself.

## New gate bypasses (asked: adversarial against the registry)

### G1 (MAJOR). Ali's experiment can be loaded as the CFG-A benchmark, whose schema pins neither its geometry nor its imaging inputs

* Where: `reflection_holo/io/config.py:160-171` (CFG-A: every geometry and imaging parameter has item None;
  any evidence label is accepted; the defining normal (1,-1,1) and azimuth [110] are not fixed).
* Reproduction: `r5b_registry_bypass.py`. The shipped CFG-A with normal [0,0,1], azimuth [1,1,0], target
  (0,0,8), the Si(001) forbidden list, and glancing angle 16.47 mrad, convergence 0, aperture 1 mrad,
  pixel 0.5 A and reference trajectory all labelled DERIVED_HERE:
  ```
    Si(001)/[110]/(008) experiment declared as CFG-A, imaging inputs DERIVED_HERE: run level PASS; normal [0, 0, 1], glancing (0.01647, 'rad')
  ```
* Why it matters. The CFG-B gate (criterion 5) is avoided entirely by naming the configuration CFG-A. The
  benchmark's identity is its geometry (docs/05 section 2), and nothing enforces it.
* Fix: fixed values in the schema for each configuration's defining parameters (CFG-A: material Si, normal
  (1,-1,1), azimuth [1,1,0]; CFG-B: normal (0,0,1); CFG-O: Pt, (1,1,1)), refusing any other value. Consider
  requiring the CFG-A imaging parameters to carry a benchmark label or source when they are present.

### G2 (MINOR). The PROJECT_INPUT supplier rule is a substring match on free text

* Where: `reflection_holo/io/config.py:108` (`SUPPLIER_DATE_RE.search`) and `:480-491`.
* Reproduction: `r5b` (all eight blocking CFG-B items with values):
  ```
    PROJECT_INPUT, source 'not supplied by Ali 2026-09-22'                : run level PASS (test_only=False)
    PROJECT_INPUT, source 'supplied by nobody 2099-12-31' (future date)   : run level PASS (test_only=False)
    PROJECT_INPUT, source 'guess; supplied by the simulation 2026-09-22'  : run level PASS (test_only=False)
    PROJECT_INPUT, source 'supplied by Ali 2026-02-30' (invalid date)     : refused -> ...
  ```
* Why it matters. A negated sentence, a future date or a non-person supplier satisfies the check. No code
  can verify human provenance, but these three are cheap to refuse.
* Fix: anchor the pattern (for example a dedicated `supplied_by` and `supplied_on` pair of keys instead of
  free text); refuse dates after today and before the project; optionally keep a list of known suppliers.

### G3 (MINOR). TEST_ONLY stand-ins pass at run level for in-memory configurations

* Where: `reflection_holo/io/config.py:587` (`allow_test_only` is a plain keyword), `:635` (the run level does
  not refuse `test_only`).
* Reproduction: `r5b`: `TEST_ONLY in memory, allow_test_only=True, level run : run level PASS
  (test_only=True)`. It is recorded, and the manifest records `test_only`. However, any code that builds a
  configuration in memory (the pipeline now being added) can run Ali's experiment on TEST_ONLY stand-ins.
* Fix: refuse `test_only` at level "run" (add a separate level "test"), or make every run entry point
  refuse a configuration with `test_only=True`.

## Residuals and decisions

* R1 (MINOR, residual of N6). With `reference_correction="none"` (no empty hologram, e.g. R2, or an
  experiment without a reference hologram) there is no visibility criterion; only exact zeros are
  flagged. `r7d_none_and_speed.py`: `reference_correction='none', overlap 30%: outside pixels flagged VALID
  8448 of 8448, rms phase error 2.02 rad`. Fix: an optional (or required) `object_min_visibility` computed the
  same way from the object hologram.
* R2 (NIT, N4). On a flagged uniform grid the wrong height is still returned, with the flag and a warning
  (497/497 in `r10c`). This is acceptable as recorded, but a caller that ignores warnings gets an aliased
  height. A `strict` option that refuses flagged grids would close it.
* R3 (NIT, N8). There is no range check: glancing_angle_ext = 1e300 mrad is accepted with a valid label. Per-parameter
  ranges (angles below pi/2) would also catch unit slips.
* D1. N3 decision ("phase uncertainties must be measured", B16): the reason holds, because under-declared
  sigmas make the reported sigma_h too small (0.76 of the true value at 31 %) and the phase branch
  indices wrong (1.75e-2). With the round-2 free-slope height, however, the height itself is not
  affected by the branch (`r10d`: > 3 true sigma_h 2.6e-3, > 5: 0). B16 (`docs/model_assumptions.md:41`) says
  "Noise under-declared by 31 % raises the rate to 1.75e-2" right after "The wrong-branch rate per accepted
  series". It should say that this rate is of the returned phase branch indices, and that h is affected
  only through a proportionally underestimated sigma_h.
* D2. Accessibility `>=` (`docs/physics_conventions.md`, "At equality the exit is exactly grazing
  (theta_out = 0) and the beam is not usable; the guard keeps `>=` ..."). The decision is harmless: equality
  is a measure-zero floating-point event, and every usable reflection lies strictly inside. The stated
  reason argues the other way, though. If equality is unusable, a refusal guard should refuse it, i.e.
  `>`, which would also agree with `SpecularCondition` (`K_int > dK`). I judge the decision acceptable and
  its reason inconsistent. A one-character change plus the conventions line would remove the discrepancy.

## Commands run (HEAD a4f607f; scratch = the audit directory above)

1. `git log --oneline -8; git status --porcelain; git diff --stat d35b751 017761d -- <scope>; git diff --stat 017761d HEAD -- <scope>`
2. `git diff --quiet 017761d HEAD -- <in-scope package dirs> tests configs pyproject.toml tools` (identical); `sed -n 380,560p docs/agent_reports/S3_audit_fixes.md`
3. `cat reflection_holo/io/assumption_registry.yaml; git diff d35b751 017761d -- reflection_holo/io/config.py pyproject.toml`
4. `sed -n 1,80p` and `136,480p reflection_holo/quantification/rocking.py`; `git diff d35b751 017761d -- reflection_holo/reconstruction/sideband.py`
5. `venv/bin/python -W ignore r10_b16_adversarial.py`; `r10b_alias.py`; `r10c_alias_flag.py`; `r10d_phase_branch.py`
6. `grep -n "^| B16" docs/model_assumptions.md`; `git show 0f0304d -- docs/physics_conventions.md`
7. `r7_divide_empty_v2.py`, `r7b_threshold_unwrap_v2.py`, `r7c_threshold_noise_v2.py` (argument renamed only); `timeout 900 ... r7d_none_and_speed.py`
8. `r5_gate_bypass.py` (unchanged); `r5b_registry_bypass.py`; inline inf/nan/1e300 check
9. `sed` and `grep` on `docs/agent_reports/E4_review.md` (M1, M3, m5, m8, n10); config/builder text greps; `e4_checks.py`; `venv/bin/pytest -q tests/reconstruction/test_self_reference_R2.py tests/io/test_io_cfg_b_text.py tests/structure/test_si001_audit_fixes.py` -> 24 passed
10. round-2 test diffs (`git diff d35b751 017761d -- <9 test files> | grep ...`)
11. `e3_tvalues.py`; `r12_structure_sweep.py` plus a direct listing of the B4 strings; `r13_shadow_bruteforce.py` (0 mismatches in 159 676 points); `venv/bin/pytest -q` -> 580 passed; calculator 25/25; `tools/phase1_numbers.py` 19/19

## NOT RUN

`python -O`; `validate_configs` CLI (writes into outputs/); `tools/physics_checks/*`; anything under
`reflection_holo/forward/` or `pipeline/` (out of scope); engine or dynamical runs; experimental data.
