# A5 - Audit of the E2 (surface, thermal) and E3 (coherence, inelastic) physics code at f4ce75e

Agent A5, 2026-09-24. Status: FINAL (written incrementally).

Scope: commit f4ce75e, checked out as a detached worktree
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/a5_wt` (`<wt>`
below; removed at the end). Python: `/home/user/Holography/venv/bin/python` with `PYTHONPATH=<wt>`;
nothing installed. No code under audit was modified; nothing committed or pushed. E1's in-progress
files in the main tree were ignored. A5's own check scripts are scratch files in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/a5/` (`<sp>`
below; not part of the repository). Every reproduction below ran on synthetic data.

Reports audited: docs/agent_reports/E2_surface_thermal.md, docs/agent_reports/E3_coherence_inelastic.md.
Read in full: both reports; L7 section 1.4; E6 sections 1, 8 and m2; docs/model_assumptions.md rows A7,
B3, B4, B6, B10, B21, B30, B35-B40; docs/physics_conventions.md (frame, tilts); docs/06 items 3, 16,
21, 23; the registry; structure/{reconstruction,si001,thermal}.py and the features.py diff;
forward/dimer_ensemble.py; forward/multislice/{illumination,convergence,engine}.py (and the
propagator, grid band functions, potentials `_RealisedAtomic`); optics/{coherence,inelastic,hologram,
darkfield}.py (and projection, detector resampling); pipeline/{config,run,convergence,__main__}.py,
the engines/estimates/feature diffs and quantify.py:255-295; configs/demo_*.yaml diffs and
demo_convergence_si001.yaml; the tests diff 1ef0900..f4ce75e and the new test modules.

## 1. Verdict

No BLOCKER. Two MAJOR, nine MINOR, one group of NITs. The core physics of both reports holds up
under independent checks: the 160 Ramstad entries, the parity/axis map, the 90-degree rotation,
the collision checks, B(T), the Bloch y tilt, the quadrature and its bound, the R1/R2 loss factors and
the reduced-contrast noise model. The defects are in what the code and the docs claim around them:
a B4 verdict that depends on a sign convention, a gate asymmetry for item 23, and bookkeeping and
number errors.

| task item | verdict | findings |
|---|---|---|
| (1) Ramstad transcription (160 entries), units, axes per terrace parity, handedness, step-edge dimers, 90 deg rotation, min-distance checks | PASS (independent parse and 30 builds); B4 verdict for static buckled tables is convention-dependent | F1 MAJOR; F4, F9 MINOR; F12 NIT |
| (2) flip-flop ensemble: [seed, realisation] seeding, drawn before the phonons, recorded states, averaging after squaring | PASS | F12 NIT (states of realisations >= 1 not persisted unless waves are saved) |
| (3) thermal.py: B(T), 273.15-323.15 K, refusal outside, no default, A7 refused in comparison | PASS for thermal.py; gate: static lattice accepted in comparison | F2 MAJOR |
| (4) y-tilt Bloch shift: kernels at f_y' + f_y, periodicity, band assertion, energy conservation, bit identity at u_y = 0 | PASS (independent exact-propagator factorisation check) | none |
| (5) quadrature bound and its use, member hashing/assembly, weights, aperture on the central k_out | PASS with reservations | F5, F6, F8, F9 MINOR |
| (6) inelastic: R1/R2 formulas, arms, noise with reduced contrast, phase unchanged | PASS (derived independently; ratio 1.0047 reproduced, independent 1.0148) | F3 MINOR |
| (7) pipeline gates items 3, 16, 21, 23; demo stand-ins in comparison; plasmon_losses variants | PASS for 3, 21, 23 (B35 path), demo refusals and variants | F2 MAJOR; F7, F10 MINOR |
| (8) E2's changed assertion; other tests/tolerances | PASS: legitimate, same strength; the only removed assertion line in tests/ over 1ef0900..f4ce75e | none |
| (9) registry and docs rows B35-B40 vs code | items and demo-only flags PASS; numbers/claims partly wrong | F1, F3, F11 |

## 2. Findings, ranked

### F1 (MAJOR) The B4 verdict for STATIC buckled reconstructions is an artefact of an arbitrary sign convention, recorded as physics

* Where: `reflection_holo/structure/reconstruction.py:25-27, 303-309` (`dimer_frame`: R1 x "sign
  convention: positive crystal-x component, the same for every terrace"); `si001.py:462-467`
  (`B4_RECON_A4_100`: "B4 applies ... on these STATIC reconstructed terraces") and `si001.py:479-506`;
  docs/model_assumptions.md row B3 ("At the exact [100] azimuth B4 holds on reconstructed terraces;
  for static buckled tables it fails at [010]"); E2 section 1.3 table.
* What is wrong: the ideal slab is symmetric under the {110} mirrors, so which of the two buckling
  orientations a single-domain static terrace carries is not fixed by R1 or any source read. E2 fixes
  it by a convention; the [100]/[010] asymmetry of the B4 verdict follows from that convention. With
  the equally valid convention "positive crystal-y component" the verdicts swap exactly.
* Reproduction (`<sp>/t4_b4_convention.py`; only `dimer_frame` is monkeypatched, in-process):

      code: +crystal x           p(2x1)a  az=(1, 0, 0): a/4 steps -> HOLDS (B4_RECON_A4_100) (max dev 0.000 A) x2
      code: +crystal x           p(2x1)a  az=(0, 1, 0): a/4 steps -> DOES NOT APPLY (max dev 0.708 A) x2
      code: +crystal x           c(4x2)   az=(1, 0, 0): HOLDS (0.001 A);  az=(0, 1, 0): DOES NOT APPLY (0.018 A)
      alternative: +crystal y    p(2x1)a  az=(1, 0, 0): DOES NOT APPLY (0.708 A);  az=(0, 1, 0): HOLDS (0.000 A)
      alternative: +crystal y    c(4x2)   az=(1, 0, 0): DOES NOT APPLY (0.018 A);  az=(0, 1, 0): HOLDS (0.001 A)

* Why it matters: B3 now tells the reader that [100] is safe for reconstructed a/4 steps and [010]
  is not; physically the two azimuths are equivalent (a 4_1 screw maps the staircase onto itself with
  the terrace types swapped, and both buckling orientations are degenerate: a static buckled surface
  has domains). The step metadata `relation.model_assumption_B4` repeats the claim. Heights are NOT
  affected: `pipeline/quantify.py:275` withholds every a/4 height whose B4 string differs from
  `B4_A4_100`, which excludes all reconstructed strings. The flip-flop verdict ("ensemble only") is
  convention-independent and correct.
* Fix: for static buckled tables say that B4 holds at a <100> azimuth only for the single-domain
  orientation chosen by the convention (not established for a real surface), or evaluate both
  orientations and report "does not apply"; correct B3 and E2 1.3.

### F2 (MAJOR) A static lattice passes a "comparison" run, although the fixed-u form is refused because item 23 is not represented

* Where: `reflection_holo/pipeline/config.py:690-698` (the only item-23 check under purpose
  "comparison": refuses `frozen_phonons` equal to `{rms_displacement_A, label}`); `config.py:1067-1073`
  (`frozen_phonons: none` without a temperature is accepted for every purpose); the static-lattice label
  is free text, checked only as a qualified evidence label, not against the registry.
* What is wrong: E2 refuses the fixed u (A7) in comparison runs because "item 23 is then not
  represented" (E2 section 3; B35 row "A7 ... refused in comparison runs"). A static lattice
  represents item 23 even less, yet it passes the same gate. At (0,0,8) the Debye-Waller amplitude
  factor is exp(-B s^2) = 0.7724 with B35, 0.7808 with A7 and 1.0 with a static lattice
  (`<sp>/t12_thermal.py`).
* Reproduction (`<sp>/t6_comparison_static.py`; to isolate the item-23 check, the generic
  demo-stand-in gate `_comparison_gate` is replaced by a no-op in that process only):

      B35 model + item 23 (B36)   : ACCEPTED with purpose comparison; item-23 rows: [('sections.engine.multislice.specimen_temperature', 'ASSUMPTION B36 stand-in', True)]
      fixed u (A7)                : REFUSED PipelineConfigError: purpose 'comparison' refuses frozen phonons given as a fixed u (e.g. model_assumptions A7, ...
      static lattice (none)       : ACCEPTED with purpose comparison; item-23 rows: [('-', 'NOT USED', False)]
      real gate, static lattice: False | mentions static: False | B36 in msg: True

  (Line 1 passes only because the no-op hides B36; the real gate refuses B36, as E2's test shows. The
  last line: with the real gate, the static-lattice refusal message does not name item 23. It is
  refused only for the file's other demo stand-ins.)
* Why it matters: docs/05 criterion 5 and the purpose of the comparison gate. A comparison run can
  drop the specimen temperature (item 23) and the whole thermal model by declaring
  `frozen_phonons: none`. That changes the (0,0,8) Fourier coefficient by 23 %, against the 1 % A7
  offset that is refused.
* Fix: under "comparison", refuse `frozen_phonons: none` as well. Alternatively, require a registered
  row saying why a static lattice represents the specimen (for example a Debye-Waller-smeared static
  potential at the B35 B, which is not implemented). State the rule in B35.

### F3 (MINOR) exp(-n/2) = 0.536 is quoted for n = 1.25; it is 0.5353 (0.536 belongs to n = 1.246)

* Where: docs/model_assumptions.md B38 ("n = 1.25 ... zero-loss amplitude exp(-n/2) = 0.536");
  descriptions of the `plasmon_losses` variants in `configs/demo_smoke_si001.yaml` and
  `configs/demo_hpc_si001.yaml` ("exp(-n/2) = 0.536 ... drops from 1 to 0.536"); E3 section 1 ("F =
  0.536 at E6's n = 1.25").
* Reproduction (`<sp>/t5_noise.py`): `n=1.25: mu=0.53526 (exp(-n/2)=0.53526)`. 1.44 sin(0.8 deg)/
  sin(16.1347 mrad) = 1.2465 and exp(-0.6233) = 0.5362. The E3 test that prints 0.5363 uses 1.246.
  The code is consistent; E3's pipeline test asserts exp(-0.625).
* Fix: quote 0.535 with n = 1.25, or use 1.246 in the variants.

### F4 (MINOR) A reconstruction is built on a substrate thinner than its tabulated depth

* Where: `si001.py:716-718` (substrate_layers >= 4 only); `reconstruction.py:414` (5 layers).
* Reproduction (`<sp>/t3_depth.py`): `substrate_layers=4: BUILT; layers present [0, 1, 2, 3],
  displaced layers [0, 1, 2, 3]; bottom layer 0 displaced: True; (r6) interior_atoms_checked=0 ...
  not applicable`. The same happens with 5 layers. R1 relaxes 5 layers over bulk; here the bottom
  layer of the slab is displaced as R1 layer 4 and there is no bulk under it.
* Why it matters: the builder accepts a physically meaningless structure, and (r6) is silently "not
  applicable". Pipeline impact is small (the demo substrate has 26 layers, and
  `DimerFlipFlopPotential` refuses reconstructed atoms within 1 A of the cell cut).
* Fix: refuse a reconstruction unless substrate_layers >= RECONSTRUCTED_DEPTH + 1 (R1: + 2).

### F5 (MINOR) The R2 design phase extent is not conservative: the shift phase and the step phase add, but the code takes their maximum

* Where: `reflection_holo/pipeline/convergence.py:105-117` (`E_max = hypot(su, sy)`,
  `v_design = max(v_coh, v_step)`). The docstring (l. 77-87) and E3 2.4 call the extent
  "conservative over the whole exit plane".
* What is wrong: for R2 the member phase at a pixel is the object's member phase at Q minus that at
  Q' = Q + s. When Q and Q' lie on terraces of different height, the shift term k t.E and the height
  term 2 k cos(theta) t_a (x_m - x_m') add. R1 is correct: its corner evaluation of E_a over x_m
  already contains the height term.
* Reproduction (`<sp>/t10_r2_extent.py`; member phases from `optics.coherence.
  flat_mirror_member_phase`, alpha = 0.1 mrad, a/2 step):

      shift (10, 0) A: actual extent 0.3866 rad; code v_design = max(v_coh 0.2505, v_step 0.1360) = 0.2505 rad (ratio 1.543)
      shift (40, 0) A: actual extent 1.1382 rad; code 1.0021 rad (ratio 1.136)
          tol 0.01: minimal quadrature for the code's extent 1x4 (bound 9.20e-03); its bound at the actual extent 1.55e-02

* Why it matters: for R2 ensembles over steps, the gate can accept a quadrature whose own bound
  exceeds the declared tolerance. The impact is limited: every R2 height is withheld, and the Cauchy
  bound is loose (F8).
* Fix: v_design(R2) = k alpha sqrt((|s_u| + 2 cos(theta) h_max)^2 + s_y^2), or evaluate |E| over the
  height combinations as for R1.

### F6 (MINOR) Member-job assembly checks neither the realisation set of a member nor the code commit of the jobs

* Where: `pipeline/convergence.py:300-340` (`load_member_jobs`) and 156-165
  (`_validate_member_waves` checks only the glancing angle and the y direction cosine).
  `git_preflight` is written to member.json (l. 293) but never read back. The `engine_manifest` path
  is not checked.
* Reproduction (`<sp>/t9_members.py`; synthetic member jobs written with the repository's
  `save_exit_wave`, configuration with `n_realisations = 1`):

      configured n_realisations: 1
      assembled: {0: [0, 1], 1: [0]} (member 0 has 2 realisations, member 1 has 1; jobs claim commits 'aaaa' and 'cccc', dirty): ACCEPTED
      _validate_member_waves: passed for both members

* Why it matters: the interface exists so that jobs can run on different machines and dates. Members
  computed at different commits, or with realisations added to or dropped from member.json, are
  assembled silently. E3's "tampered or incomplete job sets refused" covers only the configuration
  hash and missing members. The genuine path works: E3's bit-identity test passes (section 3).
* Fix: require realisations {0..n_realisations-1} and the configured seed for every member. Require
  one commit (clean, or record the mix) across the members and the assembling run. Check and hash the
  engine manifest.

### F7 (MINOR) An R2 convergence ensemble without `sections.reference.shift` (item 16) passes the gate and fails with a bare KeyError

* Where: `pipeline/config.py:150` (shift optional); `_check_convergence` l. 783-788 (the R2 branch
  does not require the shift); `pipeline/convergence.py:106`.
* Reproduction (`<sp>/t11_r2_shift.py`): `gate: ACCEPTED (R2 convergence ensemble without shift)`,
  then `design_extent: KeyError 'shift'`. Run, run-member and dry-run all reach this before any engine
  run, but the CLI maps only ConfigError to exit 3. The plane-wave R2 path has the same gap, and it
  predates E3 (`run.py:317-319`, raised after the engine run).
* Fix: raise MissingProjectInputError for item 16 when an R2 run has no shift.

### F8 (MINOR) The disc radial error bound omits the sqrt(2) needed for a complex integrand when kappa > 0

* Where: `optics/coherence.py:60-64, 156-170`. The disc branch has `extra = 0.0`; the line branch
  carries sqrt(2) (`0.5 * log(2)`) for the same reason.
* What is wrong: the Gauss-Legendre remainder with a single intermediate point applies to real
  functions. h(s) = J0(v sqrt s) exp(-i kappa s) is complex when kappa > 0, so the bound needs
  sqrt(2). The pipeline does pass kappa > 0 (`design_extent`, l. 116).
* Reproduction (`<sp>/t7_quadrature.py`): no violation found. Max actual/bound = 0.398 (disc, 960
  cases), 0.270 (disc radial part with curvature), 0.191 (line). The Cauchy estimate is loose enough.
* Fix: multiply the disc radial bound by sqrt(2) when kappa > 0.

### F9 (MINOR) Report numbers that do not match the code

* E3 section 2.4 says "v = 0.3, tolerance 1e-2 needs 1 x 4". `minimal_quadrature` gives
  `{'n_radial': 1, 'n_azimuthal': 3, 'members': 3, 'bound': 0.00115}`. The other example (v = 3,
  1e-6 gives 3 x 13 = 39) reproduces (`<sp>/t7_quadrature.py`).
* E2 sections 0 and 1.4 say bonds across a riser are "compressed by at most 5.5 % of d_nn (2.176 A,
  p(2x2))". By the code's own measure, 1 - min/d_nn gives 7.5 % for 2.176 A. The recorded
  `riser_edge_largest_compression_of_dnn` is 0.0724 for p(2x2) at [010] and 0.0721 at [100]; 0.0551
  is p(2x1)a (`<sp>/t14_compression.py`).

### F10 (MINOR) The loss-electron visibility (item 16) is required on every path, including R1 where it has no effect

* Where: `pipeline/config.py:143` (not optional). `config.py:1174-1183` itself says the value "has no
  effect" with R1/R3. docs/06 item 16 (revision 5) asks for it only "for a self-reference R2 ... if
  known".
* Why it matters: B39 is demo-only, so every R1 comparison run is refused until someone supplies a
  PROJECT_INPUT for a quantity that cannot be measured in R1 and cannot affect the result. A made-up
  value would then be recorded as a supplied input. This is an over-requirement, not a silent default.
* Fix: make the record optional for R1/R3 (refused rather than ignored if given, as the code already
  does for the separation) and required for R2.

### F11 (MINOR) Documentation rows stale or inconsistent with the code

* The B6 row still ends "Implementation of (iii) in hologram formation: report E3 (in progress)".
  E3's proposed B6/B10/B21 notes (E3 section 6) were not applied.
* The registry comment for B30 (`assumption_registry.yaml:34`, "absorptive potential of the
  multislice demos (none)") does not mention its new use for `surface_plasmon_excitations` n = 0 on
  every demo, geometric ones included. The B30 row does.
* The B37 row says "Requires frozen phonons (B35) and PROJECT_INPUT item 23". Only the pipeline gate
  enforces this (`config.py:888-892`); `forward/dimer_ensemble.py:57-62` accepts any FrozenPhonons,
  the A7 fixed u included.
* B3 (F1) and B38 (F3).

### F12 (NIT)

* `si001.py:849` lists "(r2) composition and atom count unchanged" as passed, but the only count check
  (l. 602, `assert_no_duplicates_and_count(pos, per, len(pos))`) compares the count with itself. (r2)
  holds by construction; it is not asserted.
* The builder's own assertions (r1)-(r6) do not catch a c(4x2) built with the p(2x2) registry (the
  (4,2) shift dropped). Mutation run `<sp>/t13_mutation.py c4x2_as_p2x2`: the builder passes, and only
  `test_c4x2_rows_in_antiphase_and_p2x2_rows_in_phase` fails. The mutation `dimer_along_backbond` is
  caught (the builder raises and `test_dimer_bond_and_buckling_..._match_R1_printed[p(2x1)s]` fails).
* Flip-flop states are recorded in `ExitWave.metadata` per realisation, and in the .npz only with
  `save_exit_waves`. The manifest's `run_configuration.potential` holds realisation 0 only
  (`engine.py:380-383`). The other realisations can be reproduced from [seed, realisation] but are not
  saved in a demo run.
* `thermal._temperature` refuses numpy float32 (TypeError). float64 and Python numbers pass.
* D0 (`optics/coherence.py:503-516`, E3 2.3) is defined as "the separation at the specimen that the
  biprism superposes", and the model anchors the condenser-biprism deflection at the cell origin.
  A5 derivation: anchoring at P_d is equivalent to D0 -> D0 + (P_d - R_y(2 th0) P_d). The item-16
  value is therefore the effective separation in the unfolded geometry, not a distance measured
  between two specimen points. docs/06 item 16 should say so.

## 3. Checks that passed (evidence)

* **Transcription** (`<sp>/t1_transcription.py`): my own regex parse of L7 1.4 found 10 Table III
  rows (40 entries) and 20 Table IV rows (120 entries); `mismatches: []` against
  `_TABLE_III`/`_TABLE_IV` (160 code entries). Dimers recomputed from the parsed L7 numbers at
  a = 5.431 A:
  - p(2x1)s 2.230297 A; p(2x1)a 2.258157 A / 18.2721 deg;
  - p(2x2) 2.282877/18.8612 and 2.283049/19.2580; c(4x2) 2.287269/18.7178 and 2.288281/18.9473.
  - These match R1 as printed (2.23; 2.26/18.3; 2.28/18.9, 19.3; 2.29/18.7, 18.9) and E6 (2.287/18.72).
    At a = 5.4309 A they equal `reference_dimers` and E2's table 1.1.
* **Parity and axes** (`<sp>/t2_frame.py`, computed from `DIAMOND_BASIS` directly):
  - n3 = 0 and 2 have back-bonds along (1,-1); n3 = 1 and 3 along (1,1). The code's dimer axis is the
    other <110> in every case.
  - On built atoms (back-bonds from ideal sites, dimers found by brute force on displaced positions),
    30 builds: 5 terminations x [110], [100], [010] x transverse/parallel edges.
  - Every build: one dimer axis per terrace, perpendicular to that terrace's back-bond axis; rows
    rotated across both a/4 steps and not across the a/2 step.
  - At <100>, 4 unpaired top atoms per terrace sit at bulk sites (recorded); at <110> there are none.
  - E6 m2 does not apply to the code: no <110> is transcribed from a source.
* **Handedness**: Table IV is symmetric under y -> -y about the dimer line to 0.0010 A (the table
  precision) for p(2x2) and c(4x2). The frame's handedness therefore cannot change a structure beyond
  R1's rounding. The code's frame is right-handed.
* **Minimum distances** (same 30 builds, brute force, flip-flop in both uniform states):
  - Minima: 2.2302 (p(2x1)s), 2.2220 (p(2x1)a), 2.1814 (p(2x2)), 2.2097 (c(4x2)), 2.2086 A
    (flip-flop). All are >= 0.9 d_nn = 2.1165 A.
  - `structure/checks.py` is unchanged since 1ef0900. (a)-(g) still run on the ideal sites. (r5)
    replaces (c) for displaced atoms: it is exact for interior pairs and stricter than the 0.5 A
    duplicate test.
  - Not weakened.
* **Flip-flop** (code read and E2's test, which passed):
  - `rng.integers(0, 2, n_cells)` is drawn from `default_rng([seed, realisation])` before
    `rng.normal` of the phonons (`dimer_ensemble.py:135`, `potentials.py:282`).
  - `_RealisedAtomic` reads the per-realisation cell through the view (`potentials.py:277-278`), so
    the drawn configuration is what gets propagated.
  - States, their SHA-256 and the configuration hash are recorded; realisations are reproducible and
    differ.
  - Holograms are averaged after squaring (`hologram.partially_coherent_hologram`).
* **Thermal** (`<sp>/t12_thermal.py`):
  - Values: B(273.15) 0.444810, B(295.5) 0.476100, B(323.15) 0.514810 A^2; u(295.5) = 0.077652 A,
    sigma 0.000139 A (independent formula identical).
  - Range: 273.149 K and 323.151 K refused; nan, bool and str refused. The temperature has no default:
    omitting it raises TypeError (keyword-only argument); None and an empty label raise ValueError.
  - Percentages: 2.941 % in B per 10 K; 1.46 % in u. A7 is 4.21 % low in B and 2.13 % in u.
  - A7's `FrozenPhonons(0.076, "ASSUMPTION A7 ...")` is still accepted, and the pipeline refuses the
    fixed u in comparison runs (but see F2).
* **Bloch y tilt** (`<sp>/t8_bloch_exact.py`, exact propagator, y-uniform continuum cell, my own
  factorisation argument):
  - u_y = 0 gives a bit-identical exit wave (True).
  - Tilted runs differ from exp(-i k u_y^2 L/2) x (untilted run) by 1.01e-06, 2.52e-05 and 6.54e-04
    for u_y = 2e-4, 1e-3 and 5e-3, against the expected order (u_y^2/4)(q_x^2/k)L = 8.3e-07, 2.1e-05,
    5.2e-04.
  - The envelope stays y-uniform to 3e-15.
  - The band mask stays on native frequencies (products t u), the kernels use physical frequencies,
    and member angles are used for both the x-band and geometry checks. The dark-field aperture acts on
    physical directions around the central k_out; the Bloch factor is restored at absolute exit-plane
    y after exact trigonometric resampling (`detector.py:207`, `projection.py:88`).
* **Coherence algebra**:
  - The R1 member phase, rederived: E_a = 2c(Q_x - x_m) - 2s Q_z - c D0_x + s D0_z, E_b = D0_y,
    kappa_s = k(1 - sqrt(1 - t^2))(mirror(b0).D0 - 2 s x_m). This matches E3 2.3 and
    `r1_reference_member_phase`.
  - 2J1(v)/v = 0.5 at v = 2.215 gives 0.176 lambda/alpha = 442 A at 10 urad.
  - The flat-mirror phase dk_out.Q + 2 dk_in,x x_m is correct.
  - Quadrature: exactness degree min(n_az - 1, 4 n_r - 1) is correct; weights sum to 1 - 1.1e-16.
    The v = 3, 1e-6 example reproduces 3 x 13.
  - Bound vs actual error (F8): never exceeded.
* **Inelastic model**, derived independently from coherent-state bookkeeping:
  - F = e^{-(n_O+n_R)/2} + V sqrt(L_O L_R) (the second term is the Cauchy-Schwarz maximum of the
    loss-channel overlap). R1 (n_R = 0): F = e^{-n/2}. R2 (n_O = n_R): F = e^{-n} + V(1 - e^{-n}).
    The unfiltered DC is unchanged; the phase is unchanged (F is real and positive).
  - The code applies n to the object arm and 0 (R1) or n (R2) to the reference arm, including the
    empty hologram.
  - E3's noise test reproduced verbatim: `mu=0.5363 ... sigma_meas=0.00812 ratio=1.0047
    ratio_to_mu0=1.8735 rel_se=0.0135`.
  - Independent check (own FFT top-hat demodulation, seed 424242, K = 16, 100 e/px, n = 1.25;
    `<sp>/t5_noise.py`): `mu=0.53526 sigma_meas=0.01979 pred(mu)=0.01950 ratio=1.0148
    ratio_to_mu0=1.8959`; lossless control ratio 0.9885; mean phase offset 1e-4 rad.
* **Gates**:
  - Item 3: a non-zero value needs multislice, a quadrature, the B40 or PROJECT_INPUT label, and for
    R1 the condenser-biprism passage plus D0 (item 16).
  - Item 21: `surface_plasmon_excitations` is required. Item 23 is required with the B35 model, and
    refused rather than ignored otherwise.
  - Registry: B36 [23], B38 [21], B39 [16], B40 [3, 16], all demo_only; comparison runs refuse them.
  - The `plasmon_losses` variants use B38 = 1.25; the base demos keep n = 0 under B30.
  - These points come from the code and from E2/E3's gate tests, which passed.
* **Tests (task 8)**:
  - In `git diff 1ef0900 f4ce75e -- tests/`, the only removed assertion or tolerance line is
    `startswith("NOT IMPLEMENTED")` in `test_option_labels_recorded_bulk_clean`. It was replaced by
    three assertions (value "not enabled", status prefix "NOT ENABLED: bulk termination", all five
    option names): a new fact at the same strength, and legitimate.
  - E1's changes (`test_memory_model.py` selects the unblocked path through `EXP_BLOCK_ROWS`;
    `test_atomistic_translation.py` passes the legacy 21 A depth explicitly) keep every tolerance.
  - Every skip that was added belongs to a new test.
  - No test file was deleted.

## 4. Commands run (cwd `<wt>`, `PY=/home/user/Holography/venv/bin/python`, `PYTHONPATH=<wt>` unless stated)

| # | command | result |
|---|---|---|
| 1 | `git -C /home/user/Holography worktree add --detach <wt> f4ce75e` | HEAD f4ce75e |
| 2 | `git diff --stat/--name-status 1ef0900 f4ce75e` (main repo), diffs of code, configs, docs, tests | 82 files; tests: 19 files, A/M only |
| 3 | `$PY -m pytest -q -p no:cacheprovider --basetemp=<sp>/../pt_full` (full suite) | `93 failed, 1037 passed, 6 skipped, 12 warnings in 843.44s (0:14:03)`; load 5-7 on 4 cores |
| 4 | the 93 failures | 84 `tests/hpc/test_alliance_kit.py`, 6 `tests/hpc/test_kit_gpu_mem_from_dry_run.py`, 3 SLURM tests in `tests/pipeline/test_a3_priority{1,3}.py`; all `<wt>/venv/bin/python not found: run setup_alliance.sh first` (the worktree has no venv); none are E2/E3 files |
| 5 | same 124 tests with an ignored `<wt>/venv/` directory of symlinks to the main venv (nothing installed; removed with the worktree) | `9 failed, 110 passed, 5 skipped in 184.60s`; the 9 stop at `python is not the venv of <wt>` (`scripts/hpc/alliance/job.sbatch:90-92` compares realpath(sys.prefix) with `<wt>/venv`). A first attempt with a plain `venv` symlink made the tree dirty (4 git-state failures) and was replaced |
| 6 | `$PY -m pytest -q --durations=8` on tests/structure/{test_si001_reconstruction,test_thermal,test_si001_options}.py, tests/pipeline/test_e2_thermal_reconstruction.py, tests/forward/test_convergence_members.py, tests/optics/{test_coherence,test_inelastic,test_darkfield_bloch}.py, tests/pipeline/test_e3_convergence_losses.py, tests/io | `336 passed in 177.38s`; slowest: member-job assembly 74.08 s, flip-flop 45.94 s, thermal end-to-end 32.53 s |
| 7 | `$PY -m pytest -q -s tests/forward/test_smoke_atomistic.py::test_smoke_atomistic_a2_step_0008` (alone) | `SMOKE: build 11.1 s, propagation 93.8 s, total 105.1 s, peak RSS 806 MB`; `1 passed in 105.11s` (it also passed within the full suite) |
| 8 | `$PY -m pytest -q -s tests/optics/test_inelastic.py::test_phase_unchanged_within_noise_... ::test_E6_transfer_numbers_are_reproduced` | E3's printed line reproduced verbatim (section 3); `2 passed` |
| 9 | `$PY <sp>/t1_transcription.py <wt>` | section 3 |
| 10 | `$PY <sp>/t2_frame.py <wt>` | section 3 |
| 11 | `$PY <sp>/t3_depth.py <wt>` | F4 |
| 12 | `$PY <sp>/t4_b4_convention.py <wt>` | F1 |
| 13 | `$PY <sp>/t5_noise.py` | F3, section 3 |
| 14 | `$PY <sp>/t6_comparison_static.py <wt>` (cwd tests/pipeline) | F2 |
| 15 | `$PY <sp>/t7_quadrature.py` (scipy reference integrals) | F8, F9, section 3 |
| 16 | `$PY <sp>/t8_bloch_exact.py <wt>` | section 3 |
| 17 | `$PY <sp>/t9_members.py <wt> <sp>/member_jobs` (cwd tests/pipeline) | F6 |
| 18 | `$PY <sp>/t10_r2_extent.py` | F5 |
| 19 | `$PY <sp>/t11_r2_shift.py <wt>` (cwd tests/pipeline) | F7 |
| 20 | `$PY <sp>/t12_thermal.py` | section 3, F2 numbers |
| 21 | `$PY <sp>/t13_mutation.py {c4x2_as_p2x2,dimer_along_backbond} <wt> ...` (cwd tests/structure) | F12 |
| 22 | `$PY <sp>/t14_compression.py <wt>` | F9 |
| 23 | `git diff 1ef0900 f4ce75e -- tests/ \| grep` removed assert/tolerance lines, added skips | section 3 |
| 24 | `git -C /home/user/Holography worktree remove` of `<wt>` (after removing the venv symlink directory), `git worktree prune`, `git worktree list` | worktree removed (section 5) |

## 5. NOT RUN / not checked

* The 9 kit tests listed in command 5 were NOT RUN in a valid environment: they require the
  repository's own venv inside the worktree, and installing one is outside this task. They exercise
  `scripts/hpc/alliance/`, which neither E2 nor E3 edited.
* No GPU/cupy run and no SLURM job array. The member-job interface was exercised only through E3's
  CPU test (2 members) and A5's synthetic assembly.
* No physics study: the flip-flop or static reconstructions against bulk on the step phase, the
  convergence of the flip-flop plus phonon average, and the a/4 azimuthal residual under convergence
  are all NOT RUN (by E2/E3 either).
* The Ramstad tables were checked against the L7 transcription only, not against the paper's pages.
  E6 checked the pages.
* Heacock's and Tanishiro's values were not re-read at the source; they were taken as confirmed by E6.
* E1's potentials.py was read only where E2/E3 depend on it (`_RealisedAtomic`, `FrozenPhonons`).
