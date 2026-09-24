# A7 - Re-audit of fix rounds X1 (A5 findings) and X2 (A6 findings) at 685e434

Agent A7, 2026-09-24. Status: IN PROGRESS (written incrementally; sections 1-2 added after the checks of 3-4).

Scope: commit 685e434, detached worktree
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/a7_wt` (`<wt>`
below), a `venv` symlink to the main venv (ignored by `/venv`), Python
`/home/user/Holography/venv/bin/python` with `PYTHONPATH=<wt>`; nothing installed, no code under audit
modified, nothing committed or pushed. A7's own scripts are scratch files under
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/a7/` (`<sp7>`;
not part of the repository). A5's scripts `<sp>/a5/`, A6's scripts `<sp>/` (scratchpad root).

## 0. Log

* 04:43 UTC: worktree created at 685e434; full suite and per-directory suites started in the
  background (section 5).
* 04:45-05:05: X1 findings re-checked (section 3), A5's scripts rerun or adapted.
* 05:00-05:20: X2 findings re-checked (section 4), A6's scripts rerun (through a wrapper where X2
  made `amp_floor_rel` a required keyword).
* 05:20: sections 1-2 (verdict tables, ranked findings) and 5-8 written.

## 1. Verdict

No BLOCKER and no MAJOR. Every MAJOR of A5 (F1, F2) and of A6 (N-1, N-2) is fixed at 685e434, and
A5's and A6's original failure cases no longer reproduce. Remaining: four MINOR findings, two
of them new defects introduced by the fixes (A7-1: X1's F1 breaks a figure tool outside X1's
scope; A7-3: X2's N-2 verdict fields). A7-2 concerns the orchestrator's wording edit and A7-4 is a
residue of K-1. There is one NIT finding of substance (A7-5) and several documentation NITs. The changed assertions of both rounds are legitimate behaviour changes; none weakens a test.
All suites pass in the worktree (section 5).

### X1 (audit A5, E2/E3 code)

| A5 id | A5 severity | verdict at 685e434 | evidence (section 3) | residue |
|---|---|---|---|---|
| F1 buckling registry | MAJOR | FIXED: required, no default on any path; B4 verdict convention-free; measured relation labelled "not physics" | `<sp7>/f1_registry.py` (24 builds x 2 frame conventions), refusals, registry mutation caught by 8 tests | A7-1 (MINOR, new): tools/plots/phase4_figures.py `surface` now refused; NIT: docs B3/B4 wording |
| F2 static lattice in comparison | MAJOR | FIXED: comparison refuses `frozen_phonons: none` (item 23 named, one error); demo needs an ASSUMPTION static-lattice label | `<sp7>/f2_static.py` (A5 t6 adapted) | observation: the geometric engine has no thermal gate (phase-only model) |
| F3 n = 1.246 | MINOR | FIXED in code/configs | configs, inelastic.py, test | NIT: docs B38 "1.87", test_inelastic.py docstrings "n = 1.25" |
| F4 thin substrate | MINOR | FIXED (>= 8 layers) | `<sp7>/f4_f12_builder.py` | none |
| F5 R2 extent | MINOR | FIXED; formula re-derived; 60-digit check: odd/v = 1.000000000000, even/kappa = 1 - 7.5e-9 | `<sp7>/f5_extent_decimal.py` | the test's `4 k eps |Q|` allowance is a legitimate precision allowance, not a masked defect (NIT: could be removed) |
| F6 member assembly | MINOR | FIXED (realisations, seed, manifest SHA/member/seeds/count, package tree; commit mix recorded) | A5 t9 refused; 7 extra forgeries refused (`<sp7>/f6_members.py`) | observation: numerical environment of member jobs not compared |
| F7 R2 without shift | MINOR | FIXED | A5 t11 unchanged: MissingProjectInputError item 16 | none |
| F8 sqrt(2) | MINOR | implemented; A5's premise is wrong: the factor is not needed (bound valid but 41 % looser) | derivation in section 3 | A7-5 (NIT) |
| F9 report numbers | MINOR | corrected numbers reproduced (x1_a5_numbers.py output byte-identical) | rerun | E2/E3 reports not edited (instruction) |
| F10 V_loss on every path | MINOR | FIXED (R2 required, R1/R3 refused) | code, tests | none |
| F11 B37 needs B35 / stale rows | MINOR | FIXED in code; rows B6, B30, B35, B37, B39 updated | require_b35_frozen_phonons | NIT: docs/06 item 16 lacks the "effective separation" wording of A5 F12 |
| F12 NITs | NIT | FIXED ((r2), (r3b), float32 T, flip-flop states in the run record, D0 docstring) | A5 mutation caught by (r3b) | none |
| kit tests in a worktree | - | DONE: `/venv` ignore rule; tests/hpc 117 passed, 5 skipped in this worktree | section 5 | none |

### X2 (audit A6, E1 engine wave 2a)

| A6 id | A6 severity | verdict at 685e434 | evidence (section 4) | residue |
|---|---|---|---|---|
| N-1 short beam | MAJOR | FIXED: H, edge, gap required; study_depth100 H = L_z tan(theta) - gap - a/2 - 1 A exact for all 24 points on the built cells; run_study refuses a short beam | `<sp7>/n1_heights.py`; run_study refusals; A6's H = 8 A case now "not assessed" and refused | NIT: refusal per point inside the run loop |
| N-2 verdict | MAJOR | FIXED WITH A NEW DEFECT: amplitude floor and lit-end limit do not hide the tested failures (shifted crystal fails every bin; non-converged build-up stays visible); A6's 1.029 last bin excluded with its reason | `<sp7>/n2_probe.py` (6 cases), A6 scripts via `<sp7>/a6_wrap.py` | A7-3 (MINOR): `converged_beyond_A` is a number when NOT converged; NIT: one passing bin suffices |
| N-3 silent beam defaults | MINOR | FIXED | required keys, `_beam_inputs` | none |
| S-1 rung-3 wording | MINOR | FIXED | engine.py, run_study.py, study_depth100.yaml | NIT: README_ALLIANCE.md:15-16 still stale (declined by X2, scope) |
| S-2 rocking curve "NOT RUN" | MINOR | FIXED; the numbers the orchestrator added are partly wrong | `<sp7>/solver_angles.py` | A7-2 (MINOR) |
| B-1 memory claim | MINOR | FIXED (docstrings; behaviour unchanged) | algebra, A6 numbers | none |
| K-1 dry-run code identity | MINOR | FIXED for the engine package | tests/hpc | A7-4 (MINOR): grid/atom-count code outside the hash |
| K-2 explicit need below derived | MINOR | FIXED (refused unless flag; recorded) | tests/hpc | none |
| Z-1 vacuous sizing check | MINOR | FIXED: the check fails for a real 20-30 % under-count | `<sp7>/z1_perturb.py` | limited power (< ~19 % passes), as X2 states |
| n1, n2, n3, n4, n9 | NIT | FIXED | fingerprint (n3), R2-A rerun (n9) | none |
| n5 | NIT | FIXED except README_ALLIANCE.md:15-16 (declined) | grep | still stale |
| n6, n7, n8 | NIT | DECLINED legitimately (docs line count; kit scope; inherent) | - | n7: margin 0 still accepted |
| gpu_check.py edit (outside scope) | - | legitimate: tiny cases byte-identical at 67f3bf5 and 685e434; PASS gate still binds the engine hash (which changed, so old PASS records do not unlock 685e434) | `<sp7>/gpucheck_fp.py` | tonight's list is pinned to a1ef2a0 and unaffected |
| study.yaml byte identity | - | CONFIRMED 17/17 against a1ef2a0 (only the `check` diagnostic changed, on purpose) | A6 fingerprint script | none |

## 2. Findings, ranked (new or remaining)

### A7-1 (MINOR, new defect of X1 F1) The Phase 4 surface figure tool is refused

* Where: `tools/plots/phase4_figures.py:109-110`: `build(st, ..., termination="c(4x2)")`.
* What: since X1 F1, a bare static buckled name is refused (reconstruction.py:394-404). X1's report
  says "no caller had to change". That holds for reflection_holo/ and tests/, not for this tool
  (committed by the orchestrator in 5a1471d).
* Reproduction:
  `PYTHONPATH=<wt> venv/bin/python tools/plots/phase4_figures.py surface --repo <wt> --out <sp7>/fig`
  -> `ValueError: c(4x2) is a static BUCKLED reconstruction: its buckling registry is a required,
  explicit choice (no default) ...`. The `solver` figure still runs.
* Why it matters: the Phase 4 staircase figure (commit 5a1471d) cannot be regenerated from the
  code of record. It was drawn with the former convention, which equals registry +[100] (X1
  section 1), and that model choice is not stated on the figure.
* Fix: pass `dict(name="c(4x2)", buckling_registry=...)` and put the registry in the title, noting
  it is a model choice.

### A7-2 (MINOR) The solver-agreement numbers in VALIDATION_STATUS understate the largest phase difference and misattribute it

* Where: `reflection_holo/forward/multislice/engine.py:18-21` (module docstring) and `:63-64`
  (VALIDATION_STATUS, copied into every ExitWave); `scripts/hpc/README_HPC.md:141-142`; the same
  sentence in `docs/08_paper_readiness.md:64`.
* What: the text says "median of 0.014 rad ([100]) and 0.017 rad ([110]), up to 0.075 rad at
  weakly reflecting angles". It cites `tools/plots/phase4_figures_solver_output.txt`, whose first
  line prints `[100] ... max |d arg| 0.398 rad`.
  - The medians match (0.0142 and 0.0174 rad).
  - The [100] maximum is 0.3976 rad at 15.00 mrad (|R|^2 = 1e-5). Without the |R|^2 < 1e-3 angles
    it is 0.055 rad.
  - The 0.075 rad is the [110] maximum at 17.60 mrad, where |R|^2 = 0.0439: the 5th strongest of
    15 angles (53 % of the [110] peak). It is not a weakly reflecting angle.
  - docs/05_final_repository_specification.md:206-208 states all of this correctly.
* Reproduction: `PYTHONPATH=<wt> venv/bin/python <sp7>/solver_angles.py <wt>` prints
  `[100]: n=23 ... median |d| 0.0142; max |d| 0.3976; max |d| excluding |R|^2<1e-3: 0.0550`;
  `[110]: n=15 ... median |d| 0.0174; max |d| 0.0750`; `17.60 mrad |R|^2 0.04389 (rank 5 of 15 by
  |R|^2) d -0.0750`.
* Fix: "median 0.014 rad ([100], 23 angles) and 0.017 rad ([110], 15 angles); at most 0.055 rad
  ([100]) and 0.075 rad ([110], at 17.6 mrad) except 0.398 rad at [100] 15.0 mrad, where |R|^2 is
  about 1e-5", as docs/05 has it.

### A7-3 (MINOR, new with X2 N-2) `converged_beyond_A` carries a distance when the point is NOT converged

* Where: `tests/forward/null_test_cases.py:440-448` (`resolved_translation`).
* What: E1's contract was that None means not converged. X2 returns the end of the last failing
  included bin, also when that bin is the last one, with `converged=False`. A reader of the study
  JSON who looks at the field whose name states the result sees "converged beyond 4500 A" on a
  point that failed every bin.
* Reproduction: `<sp7>/n2_probe.py <wt> shiftB` (crystal B translated half a pixel too far):
  `fixed: converged=False converged_beyond_A=4500.0 n_bins_beyond=0 ...; verdict: NOT converged`,
  and the same for the moved beam.
* Why it matters: the HPC study's purpose is exactly this verdict (docs/05 4.4 item 3). There is no
  code consumer (grep), so the harm is a misreading, not a wrong computation.
* Fix: `converged_beyond_A = None` unless `converged`, plus a separately named field (e.g.
  `last_failing_included_bin_end_A`). Optionally require a minimum number of passing bins
  (NIT: r = 0.02 gives "converged" on one bin while the ratio is still trending, 1.011 -> 1.005).

### A7-4 (MINOR, residue of K-1) The dry-run memory need is bound to the engine package only

* Where: `reflection_holo/pipeline/__main__.py:85-110`; `scripts/hpc/alliance/kit.py:378-383`.
* What: the report is refused if the configuration SHA-256 or the SHA-256 of
  reflection_holo/forward/multislice/*.py differs. The grid and atom count behind the device peak
  are produced by forward/cell.py, structure/ and pipeline/. A change there with the same
  configuration changes the need without changing either hash that the kit compares. A6 proposed
  the commit plus dirty state. The package-tree hash of provenance.manifest (all of reflection_holo/)
  would cover it.
* Reproduction: by reading. Not run, because it needs a code edit, which this audit does not make.
* Fix: compare `package_tree_sha256` (or the commit plus dirty state) in addition to the engine
  hash, or record the grid and atom count and compare them with the submitting clone's dry run.

### A7-5 (NIT) F8's sqrt(2) is not needed

* Where: `reflection_holo/optics/coherence.py:160-176` (and the pre-existing line branch, :173).
* What: Gauss-Legendre has real nodes and weights, so its remainder functional R is real-linear.
  For complex h take phi = arg R[h]. Then |R[h]| = R[Re(e^(-i phi) h)] <= C_n max|h^(2n)|, and the
  one-point form with factor 1 already bounds complex integrands. The added sqrt(2) keeps the bound
  valid but makes it 41 % looser. X1 section 2 shows it refusing the 1 x 4 disc at 1.083e-2 against
  a 1e-2 tolerance.
* Fix: optional (safe side). Either drop the factor with this derivation or keep it and call it
  conservative rather than necessary.

### NITs

* F1 docs: model_assumptions B4 (line 30) still says reconstructions are "not modelled". B3 says
  "only the flip-flop ensemble (B37) satisfies B4", but the code has B4 hold for static p(2x1)s at
  <100> (si001.py:495-502) and says "the only ROOM-TEMPERATURE model".
* F3 residue: model_assumptions B38 "1/0.536 = 1.87" (should be 1.86 with n = 1.246);
  tests/optics/test_inelastic.py docstrings (lines 5, 149, 203-204) still say n = 1.25 and 1.87.
* A5 F12 D0 wording: docs/06 item 16 still lacks "effective separation in the unfolded geometry".
* scripts/hpc/alliance/README_ALLIANCE.md:15-16: "(docs/05 4.4 rung 2 and the abTEM cross-check NOT
  RUN)" is stale (X2 declined, scope).
* run_study.py:132-176: study-file checks run per point inside the run loop. Without `--estimate`, a
  bad late point is refused only after the earlier points have run (pre-existing pattern).
* The L0 points of study_depth100.yaml can never be assessed by the surface-resolved read-out
  (window ends at 261 A, before the 292 A contact). This is stated by X2, and their x-summed result
  remains.
* `--gpu-mem-margin 0` is still accepted (n7, declined).
* tests/pipeline/test_e3_convergence_losses.py:368: the `4 k eps |Q|` allowance is legitimate (F5
  above), but a cancellation-free or extended-precision evaluation would make it unnecessary.

## 3. X1 (A5 findings): evidence per finding (written as checked)

### F1 buckling registry: FIXED

* No default path left. `reconstruction.check_buckling_registry` (reconstruction.py:394-413) refuses
  None or any value outside the four registries for p(2x1)a, p(2x2), c(4x2), and refuses a registry
  given with p(2x1)s or the flip-flop. `si001.parse_termination` (si001.py:431-455) refuses the bare
  buckled name and a mapping with extra keys. `build_reconstruction` takes `buckling_registry` as a
  required keyword without a default (reconstruction.py:416). The pipeline gate `_check_termination`
  (config.py:903-944) calls the same parser before any engine run. The feature builder accepts
  'bulk' only (features.py:513-524). Every `termination=` call site in reflection_holo/, scripts/,
  tools/ and tests/ was grepped: none passes a registry by default. The pipeline's
  `prep.get("termination", "bulk")` (config.py:915) is the pre-existing bulk default of the gate,
  not a registry default; engines.py:89 refuses a missing termination key anyway.
* A5's case, adapted (`<sp7>/f1_registry.py`: 3 tables x 4 registries x [100]/[010], MIXED
  staircase (0, 2, 1); A5's frame swap +crystal x -> +crystal y monkeypatched in-process):
  every a/4 step at <100> now carries `B4_RECON_A4_BUCKLED` ("not guaranteed at any azimuth;
  depends on the buckling registry"), for every registry and under both frame conventions
  (`B4 strings unchanged: True` for all six table/azimuth pairs). The measured relation still swaps
  with the registry, as A5 found: p(2x1)a +-[100] maps at [100] (0.000 A), not at [010]
  (0.708 A); +-[010] the reverse. p(2x2): 0.001/0.022 A. c(4x2): 0.001/0.018 A. These numbers are
  stored only in `relation.buckling_registry_relation`, whose note says "not physics"
  (si001.py:1033-1039). The registry metadata carries the label "MODEL CHOICE (explicit, required;
  not physics)" (reconstruction.py:541-550; si001.py:470-472).
* Refusals reproduced: 'p(2x1)a', 'c(4x2)', {name: p(2x2), buckling_registry: None} and
  {..., '[100]'} all raise ValueError with the "required, explicit choice (no default)" message.
* The four registries give (table, table), (mirror, mirror), (table, mirror) and (mirror, table)
  for the two terrace types. That is every per-type orientation. Terraces of the same type are
  forced to share one orientation, which is a stated limit rather than a defect.
* Mutation (`<sp7>/mut_registry.py`: the registry ignored, every terrace carries R1's table):
  the builder does not notice, because no builder assertion checks the registry on the atoms.
  The test modules catch it: `8 failed, 99 passed` (the six +-[010] cases of
  `test_both_registry_axes_...`, `test_p2x1s_is_its_own_mirror_image...` and
  `test_static_registries_are_members_of_the_flipflop_ensemble`).
* Quantification is unaffected: quantify.py:275 withholds every a/4 height whose B4 string is not
  `B4_A4_100`, and that now includes every reconstructed string.
* New defect (MINOR, A7-1 below): `tools/plots/phase4_figures.py:109-110` (the orchestrator's
  Phase 4 figure tool, 5a1471d) still builds `termination="c(4x2)"`. At 685e434 its `surface` figure
  is refused with the new ValueError (reproduced). X1's report says "no caller had to change".
  That was true of reflection_holo/ and tests/, not of tools/.
* Docs residue (NIT): model_assumptions B4 still says reconstructions are "not modelled"
  (docs/model_assumptions.md:30). B3 says "only the flip-flop ensemble (B37) satisfies B4", while
  the code's `B4_RECON_A4_100` holds for static p(2x1)s at <100> (si001.py:495-502). The code says
  "the only room-temperature model", and B3 lacks that qualifier.

### F2 static lattice in comparison runs: FIXED

* `<sp7>/f2_static.py` (A5's t6 adapted to the new `reasons=` keyword; demo file
  `configs/demo_smoke_si001.yaml`, variant multislice_tiny_thermal):
  - purpose comparison, `frozen_phonons: none` with an ASSUMPTION label: REFUSED; the one error
    names item 23, the static lattice and the demo stand-ins (A5's last line now True).
  - the same with a PROJECT_INPUT label: REFUSED (a static lattice cannot pass as a project input).
  - fixed u (model_assumptions A7): REFUSED.
  - With the demo-stand-in gate replaced in-process by a gate that raises only the thermal
    reasons (A5's isolation), the static lattice and the fixed u are both refused by their own
    reason, and the B35 model is accepted.
  - demo purpose: no label, empty label, PROJECT_INPUT label and TEST_ONLY without allow_test_only
    are REFUSED; "ASSUMPTION (demo): ..." is ACCEPTED; a label together with B35 phonons is REFUSED
    ("null otherwise"). A bare "ASSUMPTION" is accepted. That is the repository-wide meaning of
    `qualified=True` (io/labels.py:23-50), not X1's.
* Remaining gap, recorded by X1 and not an A5 finding: purpose comparison does not refuse the
  geometric engine on thermal grounds (config.py:694: `fp = None` for non-multislice engines).
  The geometric model is phase-only, and a Debye-Waller factor common to both terraces does not
  change its phase, so this is an observation rather than a defect.

### F3 n = 1.246: FIXED in code and configs; residue in docs and E3 test docstrings (NIT)

* configs/demo_smoke_si001.yaml:517-533 and demo_hpc_si001.yaml:425-441 use 1.246 and 1/0.536 = 1.86.
  optics/inelastic.py:37-40 and the registry comment agree.
* Residue: docs/model_assumptions.md B38 (line 64) still says "1/0.536 = 1.87". The docstrings of
  tests/optics/test_inelastic.py:5, 149, 203-204 still say n = 1.25 and 1.87, while the asserted
  numbers there use 1.246. Wording only.

### F4 thin substrate: FIXED

* `<sp7>/f4_f12_builder.py`: p(2x1)s, p(2x1)a (-[010]) and the flip-flop are REFUSED at 4, 5, 6 and 7
  layers, and BUILT at 8 with 16 interior atoms checked by (r6). Bulk is still accepted at 4 layers
  (X1's test). The (r6) "not applicable" branch is now an assertion (si001.py:753).

### F5 R2 design extent: FIXED; the X1 test allowance is legitimate

* Own derivation, frame x outward, b0 = (-s, 0, c), e_a = (-c, 0, -s), e_b = y:
  - Take dk_in = k[(sqrt(1-t^2) - 1) b0 + t_a e_a + t_b e_b] and dk_out = mirror(dk_in). The flat
    mirror's member phase is dk_out.Q + 2 dk_in,x x_m, from phase continuity on the plane x = x_m.
  - With Q' = Q + (dx, s_y, 0), dx = -s_u/c, the R2 difference is
    k[t_a (s_u - 2c dh) - t_b s_y] + k (1 - sqrt(1-t^2)) s (dx + 2 dh), with dh = x_m - x_m'.
  - The linear part has |E|_max = sqrt((|s_u| + 2c h_max)^2 + s_y^2). With 1 - sqrt(1-t^2) <=
    (t^2/2)(1 + t^2), the curvature bound is kappa = k alpha^2/2 (1 + alpha^2) s (|s_u|/c + 2 h_max).
  - convergence.py:113-129 implements exactly this (R2 branch 113-125, E_max at 121). For R2,
    v_step = 2k c h_max alpha is contained in k alpha |E|_max.
* Independent 60-digit check (`<sp7>/f5_extent_decimal.py`: Python `decimal`, member directions built
  from eq. (2) without the repository's phase function; shifts (10,0), (40,0), (0,10), (-25,15),
  (0.5,0), (500,-300) A; a/2 step; 721 azimuths at |t| = alpha and alpha/2):
  - max odd part / v_design = 1.000000000000 (attained; the largest ratio is 1 + 1e-15, the float
    rounding of v_design);
  - max even part / kappa = 0.999999992500 in every case, which is the analytic
    (1 + alpha^2/4)/(1 + alpha^2) = 1 - 7.5e-9 at alpha = 1e-4.
* The allowance `4 k eps |Q|` (tests/pipeline/test_e3_convergence_losses.py:368): kappa's
  margin over the exact maximum is 7.5e-9 relative, 2.3e-15 rad in absolute terms here. The test
  forms phases of about k |Q| t = 25 rad from O(1) direction cosines in double precision, so it
  cannot resolve that margin; its failure by 6.9e-15 rad (X1 section 2) is rounding. It is a
  legitimate numerical allowance, not a masked defect: the extended-precision check shows that the
  code's kappa bounds the true even part. The allowance is 2.2e-10 rad, 7e-4 of kappa, so a kappa
  under-estimate below 0.07 % would pass the test unnoticed. That would be physically irrelevant.
  An extended-precision or cancellation-free (t^2/(1 + sqrt(1 - t^2))) evaluation would remove
  the need for the allowance (NIT).

### F6 member assembly: FIXED

* A5's own t9 job set (`<sp7>/f6_members.py`, A5's writer code executed unchanged, then the new
  `load_member_jobs(..., code_state=...)`): REFUSED "lacks 'engine_manifest_sha256' ... rerun the
  member job".
* Forgeries not in X1's test, built with X1's `_fake_member_jobs`. Each is REFUSED with the
  intended message:
  - member 0's engine manifest copied into member 1 (hash updated): "engine manifest of member 0,
    not 1";
  - manifest seeds changed: REFUSED;
  - manifest realisation count 2: REFUSED;
  - record code differing from its manifest: REFUSED;
  - record and manifest consistently claiming another package tree: "a mix is refused";
  - a record listing one wave twice ([0, 0]): REFUSED.
  The genuine set is ACCEPTED; a dirty flag with the same tree is ACCEPTED (the tree hash covers
  uncommitted package changes, provenance/manifest.py:93-106).
* Not compared, an observation beyond A5: the numerical environment across member jobs (numpy/cupy
  versions, device). The backend comes from the configuration hash.

### F7 R2 without shift: FIXED

* A5's t11 unchanged: `gate: MissingProjectInputError ... item 16 (sections.reference.shift ...)`.
  The same error also names the missing loss-electron visibility (F10), before any engine run.

### F8 sqrt(2) in the disc bound: implemented; A5's premise is wrong (the factor is safe but unnecessary)

* coherence.py:160-176 (`radial_error_bound`) multiplies the disc radial bound by sqrt(2) when
  kappa != 0. A5's t7 rerun: no violation; the disc radial part with curvature goes from actual/bound 0.270 to 0.1908
  (= 0.270/sqrt(2)).
* A7 derivation: for any complex h, choose phi = arg R[h]. Gauss-Legendre has real nodes and
  weights, so R is real-linear and |R[h]| = R[Re(e^(-i phi) h)] = C_n g^(2n)(eta) with the real
  g = Re(e^(-i phi) h), and |g^(2n)| <= |h^(2n)|. The one-point remainder with factor 1 therefore
  already bounds a complex integrand.
* So the sqrt(2) (and the pre-existing sqrt(2) of the line branch, coherence.py:173) makes the
  bound 41 % looser without making it valid where it was not. It can refuse a quadrature that
  meets the tolerance: X1 section 2 shows the 1 x 4 disc at the former R2 extent going from
  9.2e-3 to 1.083e-2 through this factor alone. NIT (safe side); recorded as A7-5.

### F9 report numbers: corrected numbers reproduced

* `tools/review/x1_a5_numbers.py` rerun at 685e434: exit 0; the output is byte-identical to the
  saved `tools/review/x1_a5_numbers_output.txt`. A5's t7 reproduces `1 x 3 = 3 members, bound
  1.154e-03` and `3 x 13 = 39, 6.212e-07`. The E2/E3 reports were not edited (instruction), so the
  corrections live in X1 section F9 only.

### F10 V_loss required on every path: FIXED

* `_check_reference` (config.py:739-758) requires the shift and V_loss for R2
  (MissingProjectInputError, item 16) and refuses V_loss for R1/R3.
* `SurfacePlasmonLoss` (inelastic.py:119-128) accepts None only where L_O L_R = 0 or a zero-loss
  filter is declared. The cross term is skipped only then (inelastic.py:219-222), and it was an
  exact zero there.

### F11 B37 needs B35 in the engine path: FIXED

* dimer_ensemble.py:66-69 calls `thermal.require_b35_frozen_phonons` (thermal.py:121-137). The label
  is written with repr(T) (thermal.py:113), so the parsed T round-trips exactly and u(T) is
  compared exactly. Run in-process: model_assumptions A7's fixed u with its own label is REFUSED
  ("requires frozen phonons of the sourced thermal model B35"); 0.076 A under a genuine B35 label at
  295.5 K is REFUSED ("carry 0.076 A, not u(T) = 0.07765..."); a genuine B35 at numpy float32
  300.25 K is ACCEPTED.

### F12 NITs: FIXED

* (r3b) catches A5's mutation (c(4x2) reduced with the p(2x2) lattice) for all four registries:
  "(r3b) c(4x2): neighbouring dimers of neighbouring rows are in phase, the table has them in
  antiphase" (`<sp7>/f4_f12_builder.py`).
* The float32 temperature, (r2) and the flip-flop states in the run record were checked by reading
  and by X1's tests, which pass (section 5).

## 4. X2 (A6 findings): evidence per finding (written as checked)

### N-1 / N-3 sheet beam: FIXED

* `translation_pair` and `step_case` take H, edge and gap without defaults (null_test_cases.py:195,
  512). `_beam_inputs` (null_test_cases.py:77-89) refuses None, bool, non-finite and <= 0.
  `LEGACY_M2_BEAM` (8, 2, 2) is explicit. Every caller in scripts/, tools/ and tests/ passes the
  beam (grep).
* Formula re-derived. The beam's bottom edge is `gap` above the UPPER surface (B, or the upper
  terrace). Its top edge x_b + H meets the lower surface, a/2 below, at
  z = (gap + a/2 + H)/tan(theta). Setting this equal to L_z - 1 A/tan(theta) gives
  H = L_z tan(theta) - gap - a/2 - 1 A (H2 2.6), as in `sheet_height_lit_to_exit_A`
  (null_test_cases.py:103-114).
* Checked on the BUILT cells (`<sp7>/n1_heights.py`: every one of the 24 points of
  study_depth100.yaml built with the tree's own `run_study._build`):
  - L_z of the built cell equals `cell_length_z_A` exactly;
  - the file's H equals an independent floor((L_z tan(theta) - gap - a/2 - 1) * 1000)/1000 computed
    from the built L_z, for every point (largest difference 0.0000 A);
  - the measured step is 2.7155 A and the measured gap 2.000 A;
  - the top edge meets the lower surface 62.0 A before the exit plane at 16.13 mrad (83.4 A at
    12 mrad, 50.0 A at 20 mrad) and the upper surface 230.3 A before it (309.6 A at 12 mrad,
    185.8 A at 20 mrad);
  - the moved-beam points give 230.3 A on both crystals;
  - `check_lit_to_exit` passes for all 18 translation points.
* `run_study.py` refusals, reproduced with modified copies of study_depth100.yaml (`--estimate
  --only tfix110_bragg_abs10_L5k`, output under `<sp7>`):
  - H = 8 A: exit 1, "the sheet beam does not light the surface up to the read-out window ... A:
    top-edge contact z = 788.0 A < L_z - exit_excl_A = 5261.2 A";
  - beam_height_A deleted: "missing keys ['beam_height_A']";
  - `beam_height_A: true`: "must be a number > 0".
  - study.yaml (no surface_resolved block) still estimates its legacy 8 A point.
  NIT: the check runs per point inside the loop (run_study.py:132-176, check at 159). Without
  `--estimate`, a bad point late in a file is refused only after the earlier points have run.
* study.yaml unchanged: A6's `study_points_fingerprint.py` was run in an export of a1ef2a0 and in
  `<wt>`. 17/17 points are identical in every build field (cells incl. atom positions and species,
  box and layout, both beams, MultisliceParams, R, absorption). The only difference is the `check`
  diagnostic, changed on purpose by n3: before `identical_sets: False` for all 11 pairs, now
  `identical_sets: True` with max distance 2.4e-13 to 3.6e-12 A.
* L0 points: with exit_excl_A = 1115.5 A, L_z - exit_excl_A = 261 A lies before the later
  bottom-edge contact (292 A), so the surface-resolved verdict of the four L0 points is always "no
  bin included: convergence not assessed". This is by design (X2 says so); the x-summed read-out
  remains.

### N-2 read-out verdict: FIXED; the exclusions do not hide the tested failures; one naming hazard (MINOR, A7-3)

* Probes (`<sp7>/n2_probe.py`; the rung-2 continuum known-answer case of X2's test, the study's
  beam and `surface_resolved` block, L_z of the [110] L5k points = 6377 A; each case runs B, A
  fixed and A moved):

| case | fixed beam | moved beam (covariant control) |
|---|---|---|
| base, r = 0.1 | converged beyond 2500 A (4 bins); last bin excluded (lit-end), amp 0.9916 | all 9 included bins pass (err <= 1.5e-3) |
| r = 0.02 (slow build-up) | amp ratio 1.40, 1.20, 1.11, 1.07, 1.04, 1.03, 1.018, 1.011, then 1.0054 (pass): "converged beyond 4000 A (1 included bin(s) beyond)" | all pass |
| B's V_008 x 1.01 (A unchanged) | amp ratio 1.0098-1.0087 in the late bins: "converged beyond 3500 A" | all pass, amp 1.0077-1.0095 |
| B shifted by R_x + 0.0125 A (half a pixel) | every bin err -0.10 rad: NOT converged | every bin err -0.10 rad: NOT converged |
| V_008 x 1.01 in both crystals (engine-wide) | as base (2500 A) | all pass |
| legacy 8 A beam, read directly | 0/10 bins included: "not assessed" (None); `check_lit_to_exit` refuses | same |

* Could the amplitude floor (0.05) or the lit-end limit exclude the bins that show
  non-convergence? Not in these cases.
  - The floor excluded no bin in any lit-strip case: the smallest bin is >= 0.29 of the largest
    at r = 0.1 and 0.14 at r = 0.02.
  - The lit-end limit excluded only the last bin (z_s > 5031.6 A).
  - The build-up transient of a fixed beam decays with the distance from the contact, so an
    exclusion at the END of the strip cannot turn a build-up failure into a pass. It only moves
    the last included bin earlier, which is the conservative direction.
  - A uniform, non-covariant error (the shifted crystal) fails every bin, excluded ones included.
  - What the end exclusion does hide is anything that appears only in the last ~20 % of z_s:
    1345 A of 6377 A at L5k and 2122 A of 11377 A at L10k, including the 1115.5 A exit margin.
    X2 isolated the only late failure observed as a beam-edge effect (A's lit end 168 A later than
    B's; "fixed_top" control 1.0004). That attribution is plausible, but it was checked at
    16.13 mrad only (X2 NOT RUN list).
* The 1e-2 criteria cannot see a 1 % V_g mismatch between the crystals (amp 1.008-1.010). This is
  a sensitivity limit of the null test's tolerance, not of X2's exclusions, and R2-A (T_A 1.5e-3)
  is the test for V_g.
* `converged` is True with a single passing included bin (r = 0.02: n_bins_beyond = 1, the ratio
  still trending 1.011 -> 1.005). By the stated criterion that is correct, but the verdict carries
  no minimum count or trend requirement. Only `n_bins_beyond` tells the reader how thin it is (NIT).
* Is converged_beyond_A plus `converged` unambiguous? Only together. `converged_beyond_A` is a
  number in the NOT-converged case too: shifted crystal, fixed and moved, gives
  `converged=False converged_beyond_A=4500.0`. E1's contract (None = not converged) was inverted
  (null_test_cases.py:440-448). There are no code consumers (grep), but the study JSON will carry a
  field named "converged beyond 4500 A" on failed points (A7-3, MINOR). Fix: None when not
  converged, plus a separately named `last_failing_bin_end_A`.

### S-1 / S-2 wording: FIXED; the orchestrator's added numbers are partly wrong (MINOR, A7-2)

* The rung-3 qualifier is present in engine.py:13-17 and 52-66, run_study.py:29-32 and
  study_depth100.yaml:64-67. No stale "rung 3 pass" or "rung 2 NOT RUN" text is left in
  reflection_holo/, scripts/, tests/ or tools/ (grep), except scripts/hpc/alliance/README_ALLIANCE.md:15-16 ("docs/05
  4.4 rung 2 and the abTEM cross-check NOT RUN"), which X2 declined (scope, n5). It is still stale,
  and it is the README the user reads for the cluster runs (NIT).
* The orchestrator's edit in 685e434 (engine.py:18-21 and 63-64, README_HPC.md:141-142, and the same
  sentence in docs/08_paper_readiness.md:64) says "median of 0.014 rad ([100]) and 0.017 rad ([110]),
  up to 0.075 rad at weakly reflecting angles". Recomputed (`<sp7>/solver_angles.py`, with the
  pairing of tools/plots/phase4_figures.py; `phase4_figures.py solver` rerun into `<sp7>/fig`
  reprints the saved output):
  - the medians 0.0142 and 0.0174 rad match;
  - "up to 0.075 rad" does NOT match [100]: its maximum is 0.3976 rad at 15.00 mrad (|R|^2 = 1e-5,
    the weakest of 23 angles). The saved output's first line prints it ("max |d arg| 0.398 rad").
    Excluding |R|^2 < 1e-3, the [100] maximum is 0.055 rad;
  - 0.075 rad is the [110] maximum, at 17.60 mrad where |R|^2 = 0.0439. That is the 5th strongest
    of 15 angles (53 % of the [110] maximum 0.0823), not a weakly reflecting angle. The four
    [100] angles above 0.04 rad other than 16.70 mrad are weak (|R|^2 <= 1.3e-3).
  - docs/05:206-208 states it correctly ("... and by 0.398 rad at 15.0 mrad where |R|^2 is about
    1e-5"). VALIDATION_STATUS, which is copied into every ExitWave, does not.

### B-1: FIXED (docstring)

* potentials.py:70-76 now says 32 m <= cb m + 32 B holds up to 2B rows for complex128 and up to
  4B/3 = 1365 rows for complex64, with up to 33 % more (32/24) at 2048 rows. That matches A6's
  measurement and the algebra. Behaviour unchanged, as instructed.

### K-1 / K-2 kit: FIXED (K-1 with a narrower binding than A6 proposed; MINOR residue A7-4)

* The dry-run report schema is /2 and carries `engine_code` = SHA-256 of the *.py files of
  reflection_holo/forward/multislice. It is computed from the IMPORTED package
  (pipeline/__main__.py:85-110), so a PYTHONPATH override is seen. The kit refuses a report whose
  hash differs from `engine_code_sha256(repo)` (kit.py:378-383), refuses schema /1, and refuses a
  report without the hash. Tests cover all three (tests/hpc/test_kit_gpu_mem_from_dry_run.py:
  123-153); equality of the two definitions is asserted (189-216).
* Residue (A7-4, MINOR): the device peak also depends on the grid and the atom count, which come
  from forward/cell.py, the structure builder and the pipeline (outside forward/multislice). A
  code change there with the same configuration and engine files changes the memory need without
  changing either hash that the kit compares. A6 had proposed the commit plus dirty state. X2's
  binding covers a memory-model change, which was A6's example, but not a change of the cell the
  model is applied to.
* K-2: an explicit need below the derived one is refused unless `--accept-need-below-dry-run` is
  given. The flag is then recorded, and it is refused without both options (kit.py:613-617,
  656-674). Covered by tests.

### gpu_check.py (outside X2's declared scope)

* The change is signature only (gpu_check.py:114, 127-128: `**LEGACY_M2_BEAM`). Its tiny cases are
  byte-identical at 67f3bf5 and 685e434 (`<sp7>/gpucheck_fp.py`: cells, beams and params of
  rung1_continuum_refraction and atomistic_a2_step_w2, complex64 and complex128; `diff` empty).
* The PASS gate still binds the engine hash (kit.py:246-262, 747-765, 938-951). gpu_check.py is
  the checker and is not part of the hash. X2's and the orchestrator's text edits in engine.py and
  potentials.py changed the engine hash (21096eda0355... at 67f3bf5, 2d982e28a859... at 685e434),
  so a PASS recorded with earlier code does not unlock GPU jobs at 685e434. That is the intended,
  conservative behaviour.
* Tonight's job list (scripts/hpc/alliance/TONIGHT.md) is pinned to a1ef2a0 and is not affected.
  At 685e434 tests/hpc passes (section 5). It covers the kit's dry-run plan of every job on every
  cluster (test_alliance_kit.py:104), the GPU gate (234), the emulated smoke, dry-run and null-study
  jobs (508, 535, 868), a gpu-check PASS record with a fake cupy (750, 1054), the gpu-check and
  gpu-sanity refusals without a GPU (556, 1197) and the torus CPU limit (1111). No cluster run
  (NOT RUN).

### Z-1 sizing self-check: FIXED (it can fail; limited power, as X2 states)

* `device_peak_ge_H5_blocked_model_*` compares the engine's device peak with
  48 px + max(E(nx), cb nx n + E(ny)) (supercell_sizing.py:610-621, 1762-1771), and a negative
  control is a self-check (1976-1992).
* A7 perturbation of the REAL model (`<sp7>/z1_perturb.py`: the tool's `memory_model` replaced
  in-process by the engine's model with the device peak scaled by f):
  - f = 1.0: 61/61 pass;
  - f = 0.8: exit 1, 1 of 11 device-peak checks FAILS (2a_a2: 6.185 < 6.285 GB), 58/61 checks
    pass overall;
  - f = 0.7: 8 of 11 fail, 51/61 checks pass overall.
  The check can fail. An under-count below about 19 % passes every row. So does any error confined
  to the exponential stage, whose term never sets the peak on these rows (X2's own observation).

### n1-n9

* n1 FIXED (docstring). n2 FIXED (the pixel-centre assertion is added to the optional R2-B, which
  was not run here). n3 FIXED (the fingerprint above shows the periodic cKDTree check, True for all
  11 pairs). n4 FIXED (test passes). n9 FIXED (reference at K = 2 pi f; R2-A perturbations rerun
  below). n5 FIXED except README_ALLIANCE.md:15-16 (declined, still stale). n6, n7 and n8 were
  DECLINED legitimately: n6 is a docs line count, n7 was outside the orchestrator's kit scope (the
  0 margin is recorded and printed), and n8 is inherent to the design.

### Tests: assertions changed on purpose (both rounds)

`git diff f4ce75e 685e434 -- tests/structure tests/pipeline tests/optics tests/io` and
`git diff 67f3bf5 685e434 -- tests/forward tests/hpc` were filtered for removed lines containing
assert, approx, raises, tolerance or skip. No test file was deleted. The only skip added is the
opt-in L10k proof. Every removed or changed assertion is one of those listed by X1 and X2:

| test | before | after | verdict |
|---|---|---|---|
| test_si001_reconstruction.py B4 statement table | p(2x1)a/p(2x2)/c(4x2): [100] `B4_RECON_A4_100`, [010] `B4_RECON_NOT` | `B4_RECON_A4_BUCKLED` for both, plus measured-relation assertions | legitimate (F1 is the point of the change); stronger |
| test_e2_thermal_reconstruction.py | bare "c(4x2)" accepted | refused; mapping accepted; registry with flip-flop refused | legitimate (F1) |
| test_e3_convergence_losses.py::test_plasmon_loss_records_are_required_and_gated | deleting V_loss from the R1 demo -> MissingProjectInputError | R1 refuses V_loss; R2 requires it (items == [16]); list_inputs rows; comparison refuses B38 and B39; n = 1.246 asserted | legitimate (F10); more assertions |
| test_e3_convergence_losses.py::test_plasmon_losses_reduce_... | exp(-1.25/2), exp(1.25/2), exp(-0.625) | exp(-1.246/2), exp(1.246/2), exp(-0.623), same rel tolerances; + round(.,3) == 0.536, V_loss None | legitimate (F3 value change); same strength |
| test_null_study_readout.py::test_unconverged_last_bin_gives_none | `converged_beyond_A is None` | `..._gives_not_converged`: every included bin fails, `converged is False`, `n_bins_beyond == 0`, value = end of the last included bin, verdict "NOT converged" | legitimate (orchestrator's N-2 decision), same strength; the new contract is A7-3 |
| test_null_study_readout.py synthetic KW / pair | no floor; beams without height | `amp_floor_rel=0.05`; beams lit to the exit plane; + lit-end assertions | legitimate (required inputs); the E1 assertions are kept |
| test_kit_gpu_mem_from_dry_run.py | `--need-gpu-mem-gb 30` below a derived 50 GB succeeds; schema /1 | refused unless `--accept-need-below-dry-run` (the success assertions kept under the flag); schema /2 + engine hash | legitimate (K-1, K-2) |
| test_smoke_atomistic.py, test_potential_blocked_exponentials.py | docstrings | docstrings (status, B-1) | text only |
| ladder_cases.py (R2-A reference) | `reflection_amplitude(asin(lambda f))` | `reflection_amplitude_K(2 pi f)` | legitimate (n9); T_A and T_PROP unchanged; perturbations still caught (section 5) |

## 5. Test suites at 685e434 (worktree, verbatim count lines)

Run by `<sp7>/run_suites.sh` from `<wt>` with `PYTHONPATH=<wt>`:
`/home/user/Holography/venv/bin/python -m pytest -q -p no:cacheprovider -rs --basetemp=<sp7>/pt_<name> [dir]`.
The machine is shared (4 cores). A7's own probes ran at the same time as the per-directory
suites. The worktree has no outputs/, and the outputs/ guard of tests/conftest.py raised no error.
`git -C <wt> status --short` was empty after every run.

| run | UTC, load | result |
|---|---|---|
| full suite | 04:43:27-04:57:08, load 0.3 -> 2.4 | `1165 passed, 8 skipped, 12 warnings in 819.28s (0:13:39)`; skips: `[2] tests/forward/test_null_readout_known_answer.py:184: L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1`, `[1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1`, `[5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed` |
| tests/forward | 04:57:08-05:04:29, load 2.4 -> 5.1 | `122 passed, 3 skipped in 439.44s (0:07:19)` (the 120 s smoke wall-time test passed in both runs) |
| tests/structure | 05:04:29-05:04:56 | `273 passed in 26.05s` |
| tests/optics | 05:04:56-05:05:00 | `75 passed in 4.12s` |
| tests/pipeline | 05:05:00-05:08:11 | `94 passed in 189.31s (0:03:09)` |
| tests/io | 05:08:11-05:08:13 | `128 passed in 1.20s` |
| tests/hpc (kit, emulated jobs, `venv` symlink in the worktree) | 05:08:13-05:11:30, load 2.8 -> 3.5 | `117 passed, 5 skipped in 195.91s (0:03:15)` (`SKIPPED [5] ... shellcheck not installed`) |
| optional: `RH_NULL_READOUT_LONG=1 RH_RUNG2_R2B=1 pytest -q -s tests/forward/test_null_readout_known_answer.py tests/forward/test_rung2_bragg.py -k "L10k or r2b"` | see section 6 | see section 6 |

A6's R2-A perturbation driver, unchanged, against the fixed code (n9 changed the reference
evaluation; `<sp>/r2a_perturb.py <name> <wt>`):
* baseline: 7/7 PASS with E1's and A6's numbers (`max |dR| = 4.557e-04`, `4.618e-04`, `5.172e-04`,
  `5.263e-04`; (b) `5.074e-05 rad`; (c) `3.05 to 6.50`).
* `vg_x1.01`: (a) x4 FAIL (`2.776e-03`, `2.737e-03`, `4.375e-03`, `4.307e-03` against T_A 1.5e-3)
  and (c) FAIL (`0.58 to 1.42`), identical to A6's table.
* `harmonic_origin_half_pixel`: (a) x4 FAIL (`3.926e-02`, `3.926e-02`, `6.289e-02`, `6.290e-02`);
  (c) passes (`2.01 to 2.03`), as in A6's table. n9 did not weaken R2-A.

## 6. Commands run (cwd `<wt>` unless stated; `PY=/home/user/Holography/venv/bin/python`, `PYTHONPATH=<wt>`)

| # | command | result |
|---|---|---|
| 1 | `git -C /home/user/Holography worktree add --detach <wt> 685e434; ln -s /home/user/Holography/venv <wt>/venv` | HEAD 685e434; `git status --short` empty (the `/venv` rule) |
| 2 | `git diff --stat f4ce75e 685e434`, `git diff 67f3bf5 685e434 -- <X2 files>`, `git diff 24a25ad 685e434` (the orchestrator's wording edit), `git log`, and the test diffs of section 3/4 (removed assert/approx/raises/tolerance/skip lines) | read; sections 3-4 |
| 3 | `<sp7>/run_suites.sh` (full suite, then tests/forward, structure, optics, pipeline, io, hpc) | section 5 |
| 4 | `$PY <sp7>/f1_registry.py <wt>` (cwd tests/structure) | F1: every a/4 <100> step `B4_RECON_A4_BUCKLED` under both frames; relation swaps; four refusals |
| 5 | `$PY <sp7>/mut_registry.py <wt> <sp7>/pt_mut` | `8 failed, 99 passed in 81.29s` (registry mutation caught by tests) |
| 6 | `$PY <sp7>/f2_static.py <wt>` (cwd tests/pipeline) | F2 table in section 3 |
| 7 | `$PY <sp7>/f4_f12_builder.py <wt>` (cwd tests/structure) | F4 refusals at 4-7 layers, built at 8; (r3b) refuses A5's c(4x2) mutation for all four registries |
| 8 | `$PY <sp7>/f5_extent_decimal.py <wt>` (cwd tests/pipeline) | `largest odd/v_design: 1.000000000000001  largest even/kappa: 0.9999999925000015` |
| 9 | `$PY <sp7>/f6_members.py <wt> <sp7>/member_jobs <sp>/a5/t9_members.py` (cwd tests/pipeline) | A5 t9 set refused; 7 forgeries refused; genuine and dirty-same-tree accepted |
| 10 | `$PY <sp>/a5/t11_r2_shift.py <wt>` (A5's script unchanged; cwd tests/pipeline) | `gate: MissingProjectInputError ... item 16 (sections.reference.shift ...` |
| 11 | `$PY <sp>/a5/t7_quadrature.py` (A5's script unchanged) | no violation; `disc radial part with curvature: max actual/bound: 0.1908`; `1 x 3 ... 0.0011540547393842618`; `3 x 13 ... 6.212094099180552e-07` |
| 12 | `$PY tools/review/x1_a5_numbers.py > <sp7>/x1_numbers_rerun.txt; diff` with the saved output | exit 0; IDENTICAL |
| 13 | `$PY tools/plots/phase4_figures.py surface --repo <wt> --out <sp7>/fig` | ValueError (A7-1) |
| 14 | `$PY tools/plots/phase4_figures.py solver --repo <wt> --out <sp7>/fig`; `$PY <sp7>/solver_angles.py <wt>` | medians 0.0142/0.0174; maxima 0.3976 ([100], 15.00 mrad) and 0.0750 ([110], 17.60 mrad, rank 5 of 15) (A7-2) |
| 15 | `git -C /home/user/Holography archive a1ef2a0 \| tar -x -C <sp7>/a1ef2a0_tree`; `$PY <sp>/study_points_fingerprint.py` (A6's script) in that export and in `<wt>`; field-wise comparison | `17/17 points identical in every field except 'check'` |
| 16 | `$PY <sp7>/n1_heights.py <wt>` (cwd tests/forward) | 24/24 H equal to the independent value; top edge 62.0 A (50.0/83.4 A) before the exit plane on the lower surface; lit-to-exit PASS for 18/18 translation points; 43 s |
| 17 | `$PY scripts/hpc/null_test_study/run_study.py --config <sp7>/s100_{short,nokey,bool}.yaml --out <sp7>/rs_out_* --estimate --only tfix110_bragg_abs10_L5k`; the same on study.yaml `--only tfix_bragg_abs10_L5k` | three refusals (exit 1); study.yaml legacy point estimated |
| 18 | `$PY <sp7>/n2_probe.py <wt> base r002` and `... vgBp1 shiftB engVgp1 legacy8` | N-2 table in section 4; logs `<sp7>/n2_probe_{1,2}.log` |
| 19 | `$PY <sp7>/a6_wrap.py <sp>/resolved_known_answer.py <wt>` and `... <sp>/resolved_beamheight.py <wt> 0.1 6000 8 2` (A6's scripts unchanged; the wrapper supplies the new required `amp_floor_rel = 0.05`) | A6's converged case: fixed beam converged beyond 2500 A (3 bins), A6's failing last bin (d 4500, amp 1.029) excluded by the lit-end limit; moved beam all 8 included bins pass. A6's 8 A beam: 0/10 bins included, `converged_beyond_A None` ("not assessed"), for fixed and moved |
| 20 | `$PY <sp>/r2a_perturb.py {baseline,vg_x1.01,harmonic_origin_half_pixel} <wt>` (A6's script unchanged; 05:08-05:15) | section 5 |
| 21 | `git archive 67f3bf5` to `<sp7>/t67f3bf5`; `$PY <sp7>/gpucheck_fp.py` in both trees; `kit.engine_code_sha256` in both | tiny cases identical; engine hash 21096eda0355... -> 2d982e28a859... |
| 22 | `$PY <sp7>/z1_perturb.py <wt> {1.0,0.8,0.7}` | 61/61; 58/61 (1 device check FAILS); 51/61 (8 FAIL) |
| 23 | `sha256sum scripts/hpc/null_test_study/study_depth100.yaml` | 17af7ca8..., equal to the estimate file's header |
| 24 | greps: `termination=` call sites; `converged_beyond_A` consumers; stale rung texts; `translation_pair(`/`step_case(` callers; docs rows B3, B4, B6, B35-B39, docs/06 item 16, docs/05 and docs/08 solver sentences | as cited |
| 25 | optional long runs (command in section 5) | section 5 |
| 26 | `rm <wt>/venv; git -C /home/user/Holography worktree remove <wt>; git worktree prune; git worktree list`; `rm -rf` of A7's scratch exports | section 8 |

## 7. NOT RUN / not checked

* Nothing on a GPU or a cluster: no gpu-check, gpu-sanity or demo-gpu on real hardware, and no
  member jobs across machines. The kit ran only as the emulated jobs of tests/hpc (117 passed).
  shellcheck is absent (5 skips).
* No atomistic point of study_depth100.yaml was run with the engine. The N-2 probes use the rung-2
  continuum (complex128, Fresnel, 16.13 mrad) like X2's tests. The verdict's behaviour on atomistic
  complex64 exit waves (exact propagator, many-beam [110], four-beam [100]) and at 12/20 mrad is
  untested (X2's NOT RUN list too).
* A7-4 was not reproduced by execution: it would need a code edit to forward/cell.py or the
  builder, which this audit does not make.
* Not rerun: X1's kit-in-worktree verification at 2038454 (superseded by this worktree's
  tests/hpc run at 685e434); `tools/hpc/review_h5_recompute.py` (report, `--rerun`, `--memtime`);
  run_study.py without `--estimate`.
* The E2/E3 reports and docs rows were read only where they touch the findings. The Ramstad tables
  were not re-checked, since X1 did not change them (git diff shows only the registry and mirror
  code).
* No physics study of the buckling registry's effect on the a/4 step phase (X1 NOT RUN as well).

## 8. Cleanup

