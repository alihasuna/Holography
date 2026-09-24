# A7 - Re-audit of fix rounds X1 (A5 findings) and X2 (A6 findings) at 685e434

Agent A7, 2026-09-24. Status: IN PROGRESS (written incrementally).

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
  - fixed u (A7): REFUSED.
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
  - convergence.py:113-125 implements exactly this. For R2, v_step = 2k c h_max alpha is contained
    in k alpha |E|_max.
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

* coherence.py:156-170 multiplies the disc radial bound by sqrt(2) when kappa != 0. A5's t7 rerun:
  no violation; the disc radial part with curvature goes from actual/bound 0.270 to 0.1908
  (= 0.270/sqrt(2)).
* A7 derivation: for any complex h, choose phi = arg R[h]. Gauss-Legendre has real nodes and
  weights, so R is real-linear and |R[h]| = R[Re(e^(-i phi) h)] = C_n g^(2n)(eta) with the real
  g = Re(e^(-i phi) h), and |g^(2n)| <= |h^(2n)|. The one-point remainder with factor 1 therefore
  already bounds a complex integrand.
* So the sqrt(2) (and the pre-existing sqrt(2) of the line branch, coherence.py:167) makes the
  bound 41 % looser without making it valid where it was not. It can refuse a quadrature that
  meets the tolerance: X1 section 2 shows the 1 x 4 disc at the former R2 extent going from
  9.2e-3 to 1.083e-2 through this factor alone. MINOR at most (safe side); recorded as A7-5.

### F9 report numbers: corrected numbers reproduced

* `tools/review/x1_a5_numbers.py` rerun at 685e434: exit 0; the output is byte-identical to the
  saved `tools/review/x1_a5_numbers_output.txt`. A5's t7 reproduces `1 x 3 = 3 members, bound
  1.154e-03` and `3 x 13 = 39, 6.212e-07`. The E2/E3 reports were not edited (instruction), so the
  corrections live in X1 section F9 only.

### F10 V_loss required on every path: FIXED

* `_check_reference` (config.py:739-758) requires the shift and V_loss for R2
  (MissingProjectInputError, item 16) and refuses V_loss for R1/R3.
* `SurfacePlasmonLoss` (inelastic.py:119-136) accepts None only where L_O L_R = 0 or a zero-loss
  filter is declared. The cross term is skipped only then (inelastic.py:219-222), and it was an
  exact zero there.

### F11 B37 needs B35 in the engine path: FIXED

* dimer_ensemble.py:66-69 calls `thermal.require_b35_frozen_phonons` (thermal.py:118-137). The label
  is written with repr(T) (thermal.py:112), so the parsed T round-trips exactly and u(T) is
  compared exactly. A7's fixed u (0.076 A with a B35-looking label at 295.5 K) is refused, because
  u(295.5) = 0.07765 A.

### F12 NITs: FIXED

* (r3b) catches A5's mutation (c(4x2) reduced with the p(2x2) lattice) for all four registries:
  "(r3b) c(4x2): neighbouring dimers of neighbouring rows are in phase, the table has them in
  antiphase" (`<sp7>/f4_f12_builder.py`).
* The float32 temperature, (r2) and the flip-flop states in the run record were checked by reading
  and by X1's tests, which pass (section 5).

