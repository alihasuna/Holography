# E4 - Continuum oxide overlayer in the multislice and geometric engines

Agent E4, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r` (HEAD 54de605 when
work started). Status: FINAL (written incrementally). Nothing committed or pushed by E4.

PROJECT_INPUT (Ali, 2026-09-24; docs/06 item 12): the ion-milled Si(001) samples were air-exposed
and only O2/Ar plasma-cleaned (about 10 min); holograms at 200 keV, specular (0,0,8), 16.1347 mrad
(B32), are recorded through an oxide. Literature basis: `docs/agent_reports/L8_oxide_plasma.md`
section 8 as corrected by the adversarial review `docs/agent_reports/E9_oxide_review.md` (M1-M5,
section 3, section 8, section 9). Every number quoted from E9 is a line of
`tools/review/e9_recompute_output.txt` ("out:N"); no value is re-derived into this report.

## 1. Design (labels in brackets)

Model (`reflection_holo/structure/oxide.py` module docstring; every physical parameter a REQUIRED
field of `ContinuumOxideSpec` with its own label, no defaults):

* Layer of complex potential V_ox + i V'_ox on every terrace, following the surface (one layer per
  terrace, never a function of x alone: E6 m12, E9 m5) [PROJECT_INPUT item 12, or a registered
  ASSUMPTION; V'_ox = 0 only with ASSUMPTION/TEST_ONLY]. V'_ox is a model value, not a bound
  (E9 M1).
* Grown from the crystal (E9 M2): f = (rho_ox/M_SiO2)/(rho_Si/M_Si), rho_Si = 8 M_Si/(N_A a^3)
  [DERIVED_HERE; molar masses and N_A added to `constants.py` as constants, the density is the
  input]; interface at x_i = H - f t, top at x_t = H + (1 - f) t, H the terrace's pre-oxidation top
  atomic-layer plane [convention; a common shift does not change a conformal step phase].
* Optional amorphous Si between x_c = x_i - t_a and x_i (E9 M5) [t_a required; 0 only with
  ASSUMPTION/TEST_ONLY; potentials required when t_a > 0; a-Si density = crystal's, ASSUMPTION].
* Consumed-layer count N (integer, REQUIRED): the atomistic crystal loses its top N whole (001)
  layers; asserted |N a/4 - (f t + t_a)| <= a/8 (nearest whole count; no silent rounding, the error
  names the nearest count). Conformal = equal t AND equal N on every terrace (E9 M2); per-terrace
  overrides of t and N (label "overrides") give non-conformal cells for the grown-oxide sensitivity.
* Vacuum edge graded with E(x; x0, w) = erfc((x - x0)/(sqrt(2) w))/2 (Gaussian gradient of s.d. w:
  E9's definition, out:236-243); w_v >= 0.5 A (E9 M4), smaller refused unless
  `sharp_edge_test_flag` with a TEST_ONLY label. Interface: graded (w_i > 0) or sharp (w_i = 0,
  cell-averaged like ContinuumTerracePotential) [option with label; E9 M4 recommends 0.5 A].
* Multislice (`forward/multislice/overlayer.py`): `ContinuumOxidePotential(base, oxide=spec)` wraps
  AtomicPotential, ContinuumTerracePotential or ContinuumPeriodicPotential; per slice the projected
  potential is base + sum over terraces of the layer profile x overlap (terraces along y: cell-
  averaged y fraction; along z: the terrace containing the slice); only the crystal's z range
  carries the layer. Point-sampled at pixel centres for w > 0 with dx <= w asserted (first alias
  exp(-2 pi^2 (w/dx)^2) <= 2.7e-9) [DERIVED_HERE]. The spec's hash is asserted against the cell's
  record; a cell with a layer refuses a plain potential and vice versa.
* Inner potential: `mean_inner_potential_V` stays the CRYSTAL's (B32; the pipeline's MIP check and
  the glancing angle are unchanged). Recorded per ExitWave (`metadata["overlayer"]`): the internal
  angle in the layer (added to the band assertion), the layer's phase and zero-loss attenuation
  terms, and the independent-atom SiO2 value n_SiO2 (F_Si + 2 F_O) at the declared density for
  comparison (not used).
* Geometric engine: phi_k = -(k_out - k_in).R_k + Re[T_k + I_k], T_k = 2 (k'_ox - k)(x_t - H)
  (top-surface term), I_k = 2 k'_ox (H - x_i) + 2 k'_a (x_i - x_c) (grown-oxide/interface term);
  amplitude x exp(-Im[T_k + I_k]); complex k'_perp from the exact relativistic Delta with U = V + iV'
  (E9's form) [DERIVED_HERE, E6 M4 formalism]; multiple reflections neglected (graded edges). B4 is
  judged on the BURIED crystal step measured on the kept atoms (at <110> the parity of N decides,
  E9 section 3 item 2). The ray trace uses the tops of the layer.
* Cell geometry: `depth_below_A` below the lowest crystal surface, `vacuum_above_A` above the
  highest top of the layer; new docs/05 4.3 item-4 assertion
  `item4_buildup_length_through_overlayer`: the ray must cross the stack (bounded with the external
  angle, conservative) and reach D before the exit plane.
* Pipeline: `cfg_b.surface_preparation_details.overlayer` = "none" or a COMPLETE continuum oxide
  (every key required; conformal only; staircase path; bulk termination; not under B26). A variant
  may now replace whole CFG-B records (`cfg_b_parameters`, gated as any record, hashed), so the B41
  demo is variants of `configs/demo_smoke_si001.yaml`, never the base.

Not represented (stated in the code): elastic diffuse scattering of the amorphous network, charging
(item 22), carbon, the Hattori transition layer, TDS absorption in the layer, surface/interface
plasmons beyond the uniform V'_ox (E9 M1: not to be multiplied with B38).

## 2. Files (file:line)

* `reflection_holo/constants.py:38-44` AVOGADRO_PER_MOL, M_SI_G_PER_MOL, M_O_G_PER_MOL.
* `reflection_holo/structure/oxide.py` (new): ContinuumOxideSpec :84, validate_spec :149,
  spec_sha256 :238, consumed_si_fraction :255, terrace_stacks :273, stack_phase_terms :341.
* `reflection_holo/structure/si001.py`: ContinuumOxideSpec accepted :781; B4 overlayer statements
  :811-825; `_apply_oxide` (assertions (o1)-(o4)) :827; call :1180.
* `reflection_holo/geometry/refraction.py:145, :159` refraction_delta_complex, k_perp_in_layer_per_A.
* `reflection_holo/forward/cell.py`: build_reflection_cell oxide branch :98; OXIDE_SURFACE_SEMANTICS
  :227; `_oxide_layout` :246; build_continuum_oxide_cell :264; overlayer build-up check :416.
* `reflection_holo/forward/multislice/overlayer.py` (new): edge_profile :62, ContinuumOxidePotential
  :86, _RealisedOxide :274; exported in `multislice/__init__.py`.
* `reflection_holo/forward/multislice/engine.py:229-247, :371` layer check, band angles, record.
* `reflection_holo/forward/geometric/model.py`: docstring; _require_b4_scope_oxide :249;
  oxide_phase_rates :280; _oxide_terms :304; exit wave :537-571; exported in `geometric/__init__.py`.
* `reflection_holo/pipeline/config.py`: resolve_variant_cfg_b :550; overlayer gate call :911;
  OXIDE_KEYS :946; qualified_label :952; oxide_spec_from_config :963; _check_overlayer :1007.
* `reflection_holo/pipeline/engines.py:99, :327` structure and potential adapters.
* `reflection_holo/pipeline/run.py:83-85` the summary's not-implemented list (overlayer part).
* `reflection_holo/io/assumption_registry.yaml:52, :56` B41 -> item 12, demo_only.
* `configs/demo_smoke_si001.yaml:534-` variants oxide_2p0nm, oxide_2p0nm_no_absorption, oxide_1p5nm,
  oxide_1p5nm_no_absorption (geometric) and multislice_tiny_oxide_2p0nm (base unchanged, B26).
* Tests (new): `tests/structure/test_oxide_structure.py`, `tests/forward/oxide_cases.py` (helpers),
  `tests/forward/test_oxide_multislice.py`, `tests/forward_geometric/test_oxide_geometric.py`,
  `tests/pipeline/test_oxide_pipeline.py`; changed: `tests/io/test_io_config_stand_ins.py` (expected
  registry + B41).

## 3. Tests and their a priori tolerances

Tolerances were fixed before the runs; none was changed after a run.

* (a) oxide-only control (`tests/forward/test_oxide_multislice.py`, helpers
  `tests/forward/oxide_cases.py`): the layer on a substrate at the SAME potential (TEST_ONLY), so the
  only step is the vacuum edge; rung-1 geometry and read-out (`flat_reflection_coefficient`,
  central bin). Fresnel value at 16.1347 mrad vs E9 out:234 (r = -0.05193, +-5e-6) and out:284
  (|r|^2 = 2.6972e-3, +-5e-8). Sharp edge (TEST_ONLY flag), dx 0.025 A, dz 1 A: the rung-1
  tolerances of the M2 convergence study (|err - model| <= 3.5e-3 with model = -((q1+q2) dx)^2/12;
  phase <= 1e-3 rad; r real negative). w = 0.1 A (flag): |r| within 1 % of |r_F| exp(-(q w)^2/2)
  (E9's formula out:236/285; 1 % = 2 x (0.35 % rung-1 + 0.05 % Nevot-Croce difference + 0.12 %
  E9 1-D deviation)). w = 0.5 A: |r|^2 <= 1e-3 |r_F|^2 (E9 M4's factor).
* potential construction: the upper terrace's layer equals the lower one shifted by the step (not a
  planar mask; E6 m12), V_ox and V'_ox inside, 0 above, crystal below (rtol 1e-9/1e-12); no layer in
  the entrance vacuum; sharp interface = the crystal base bit for bit; recorded internal angle in
  the layer 17.902 mrad (+-5e-7 rad, out:36) and k'_perp 4.48493 (+-5e-6, out:36).
* (b) geometric engine (`tests/forward_geometric/test_oxide_geometric.py`): conformal a/4 and a/2
  step phases 10.9761 / 21.9522 rad (+-5e-5, out:91) and equal to the bare phases (1e-9), in the
  metadata and in the exit wave; grown-oxide rate for the nine (f, V) pairs of out:109-117 (+-5e-6),
  top-surface rate out:96/98/102 (+-5e-5), one consumed layer 3.0753 A / 13.6998 rad (out:123,
  +-5e-5); the engine's finite difference (0.5 A thicker grown oxide on one terrace) equals the rate
  with the density's f to 1e-9 and E9's 4.45486 within 5e-6 + 2 k_perp x 5e-5 (E9 rounds f to 4
  decimals); one extra consumed layer 13.6998 rad within 5e-5 + the f-rounding bound; zero-loss
  intensity 0.2850 for Lambda = 1780 A (out:57, +-5e-5; V' = 0.3854 V, out:19); <110> scope
  (conformal a/4 refused with the parity note, a/2 accepted, a/4 with one extra consumed layer = a
  buried a/2 translation accepted); the legacy declared-region overlayer still refused.
* (c) flat Si(001) [100], TEST_ONLY r = 0.1, (0,0,8) at the IAM MIP, with and without a 2 nm oxide
  (V'_ox 0.40 V and 0 V), one box and grid for the three runs, r(f) at the central bin read in the
  vacuum above the layer: the ratios are PRINTED against E9's zero-loss model value (E9 M1: no
  pass/fail); asserted only the recorded internal angle (out:36), IAM 10.3394 V (out:166) and the
  crystal MIP 13.9028 V (out:171) at printed precision.
* (d) conformal a/4 step (parallel edges, [100]) under the 2 nm oxide on a short cell: smoke only
  (finite wave, conformal record, buried screw relations with the <100> B4 statement); the step
  phase is printed, not asserted (fixed-beam gate not passed).
* (e) refusals: every spec field required (TypeError), 23 invalid or missing values (thickness,
  density, consumed layers incl. the nearest-count message, V, V', zero V' or zero a-Si without
  ASSUMPTION, edge < 0.5 A, flag without TEST_ONLY, flag not needed, labels missing or of the wrong
  kind, a-Si potentials missing or given for 0 nm, overrides without label or of the wrong length),
  builder (vacuum too small, too few substrate layers, reconstruction under the oxide, a dict instead
  of a spec), engine (plain potential on an oxide cell, oxide potential on a clean cell, spec hash
  mismatch, dx > w), pipeline (each of the nine oxide keys missing, seven invalid values, zero V'
  under a PROJECT_INPUT record, B26 with an oxide, reconstruction, feature path, malformed variant
  records, B41 in comparison runs).
* pipeline (`tests/pipeline/test_oxide_pipeline.py`): the five B41 variants load (base stays B26),
  list-inputs shows the B41 stand-in, the geometric demo under 2 nm recovers the three built steps
  within 3 propagated sigma, the multislice oxide variant passes the engine setup (dry run).
* no overlayer = bit-identical: no new metadata without a layer (tests), and outputs compared
  bitwise with the HEAD tree (section 4).
* amorphous Si (E9 M5 option): the potential between x_c and x_i is V_a + iV'_a (TEST_ONLY 13.6 +
  0.47i V), the oxide above V_ox + iV'_ox, the crystal below (rtol 1e-9).

## 4. Results (printed by the tests and scripts; verbatim where quoted)

(a) `tests/forward/test_oxide_multislice.py -s` (dx 0.025 A, dz 1 A, exact propagator):

    sharp edge: |r|^2 = 2.65300e-03 (analytic 2.67299e-03 at the central bin), amplitude error -0.37456% (model -0.38041%), phase +6.19e-05 rad
    w = 0.1 A: |r|^2 = 1.29044e-03, E9 formula 1.28764e-03 (E9 1-D multislice at 16.1347 mrad: 1.3067e-3, out:285)
    w = 0.5 A: |r|^2 = 1.835e-09, suppression 6.92e-07 (analytic exp(-(q w)^2) = 1.17e-08)

The engine reproduces the Fresnel term of a sharp layer edge (|err - model| = 5.9e-5, phase 6e-5
rad) and its roughness factor at w = 0.1 A (+0.22 % in |r|^2); at the required 0.5 A the reflected
intensity is at the numerical floor (1.8e-9; E9 M4's control criterion, below 1e-3 of the crystal's,
is met: the crystal's |r|^2 in (c) is about 0.018).

(b) geometric engine: all 21 tests pass; conformal a/4 and a/2 step phases 10.97609 / 21.95218 rad,
equal to the bare ones to 1e-9; rates 4.454855 rad/A (f 0.4415, 10.34 V; out:113 4.45486), 0.885691
rad/A (out:98 0.8857), 13.699815 rad per consumed layer (out:123 13.6998); the engine's zero-loss
amplitude of 2 nm at V'_ox = 0.40 V is 0.5213 (intensity 0.2718; E9 prints 0.2697 for V' = 0.4024 V,
out:56, and 0.2850 for 0.3854 V, out:57, which the test reproduces).

(c) flat Si(001) [100], r = 0.1, 2 nm oxide (test output at +6000 A):

    (c) flat Si(001) [100], r = 0.1, bin 16.0895 mrad: |r| clean 0.1333, 2 nm oxide 0.0830, same without layer absorption 0.1581; ratio oxide/clean 0.6228 (phase -1.1374 rad), absorption only 0.5250 (phase -0.0546 rad); E9 zero-loss MODEL value exp(-2 Im k' t) = 0.5213 (E9 M1: a model value, not a bound; reported, not pass/fail)

Cell-length series (scratch script `exp_c4.py`, same read-out; one grid per length, so the central
bin moves: 16.1545 / 16.0945 / 16.0895 mrad):

    RESULT extra 3000.0 raw 0.37236178926960656 nonabs 0.7000377949160391 abs_only 0.5319166936040458 model 0.5213040185350547 dphi_abs 0.014742264693577648
    RESULT extra 4500.0 raw 0.5385674803693753 nonabs 1.0402175005485879 abs_only 0.5177450678202844 model 0.5213040185350547 dphi_abs 0.015219852611117777
    RESULT extra 6000.0 raw 0.6228031720704242 nonabs 1.1862110718714167 abs_only 0.5250357097812818 model 0.5213040185350547 dphi_abs -0.05461793265219863

Reading: the absorption-only factor of the layer (V'_ox 0.40 V against 0 V, same cell) is
0.518-0.532, within 2 % of the zero-loss model value exp(-2 Im k'_perp t) = 0.5213 that the test
evaluates for 0.40 V with E9's complex-k form (out:49-60; E9 prints 0.2697 in intensity for
0.4024 V, out:56) at every length. The raw oxide/clean
ratio is NOT converged in cell length (0.37, 0.54, 0.62): its non-absorbing part (0.70, 1.04, 1.19)
carries the change of the crystal's own surface step (vacuum/Si 13.9 V replaced by oxide/Si 3.6 V,
whose Fresnel term interferes with the Bragg reflection, the effect of E9 M4 seen from the crystal
side) and a read-out that has not converged along z (the reflected beam re-crosses the layer). An
earlier read-out over all x (not in the tests) gave 0.34 at +1500 A; it includes the internal wave
and is not usable. No bound is claimed (E9 M1).

(d) smoke (conformal a/4 step, parallel edges, [100], r = 0.1, 2 nm oxide, 2577 A cell):

    (d) SMOKE (not a physics claim; fixed-beam gate not passed): a/4 step under a conformal 2 nm oxide, Delta_phi = +1.8784 rad, geometric +1.5902 rad (10.9761 rad unwrapped, E9 out:91); amplitudes 0.1243 / 0.1004

The engine runs with the layer on an atomistic step; the 0.288 rad difference is not interpreted
(short cell, fixed-beam gate not passed, as without a layer).

Pipeline demo runs (outputs in the session scratchpad, not in outputs/):
* geometric base and the four B41 variants: every run returns the three built steps, e.g.
  oxide_2p0nm: `h = +2.7153 +- 0.0165 A`, `-1.3578 +- 0.0082 A`, `-1.3575 +- 0.0082 A`, no-step
  control PASS (base: +2.7156, -1.3576, -1.3580).
* multislice_tiny_oxide_2p0nm: runs end to end in 57 s, peak RSS 392 MB (2175 slices, 576 x 48,
  54000 atoms); heights withheld ("a terrace region is empty or below the minimum size after the
  margin"), as for multislice_tiny (terraces far below the dark-field resolution). Rerun after the
  (nx, 1) broadcast change: every array of arrays.npz bitwise identical.

No overlayer = bit-identical (scratch script `bitid.py` run on a clone of HEAD 54de605 and on the
working tree): rung-1 and rung-3 continuum exit waves, the atomistic smoke case (Kirkland, [110],
a/2 step) exit wave and metadata keys, the builder's positions and metadata hashes at [100] and
[110], and the geometric exit waves and metadata: all `np.array_equal` True. The only change without a
layer is the pipeline summary's text list "not_implemented" (run.py:83), which now states what of the
overlayer remains not implemented.

(test counts: section 5)

## 5. Test runs (verbatim last lines; `venv/bin/python -m pytest -q`, 4 cores shared)

    tests/forward:   133 passed, 3 skipped in 885.33s (0:14:45)
    tests/structure: 332 passed in 27.42s
    tests/pipeline:  129 passed in 247.97s (0:04:07)
    tests/io:        FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
                     1 failed, 127 passed in 1.28s
    full suite:      FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
                     1 failed, 1290 passed, 8 skipped, 12 warnings in 1374.10s (0:22:54)

The one failure is the expected doc-consistency test (`AssertionError: B41`: the registry has B41,
docs/model_assumptions.md has no B41 row yet). The outputs/ guard passed. Baseline (a clean clone of
HEAD 54de605 with the working-tree docs, same venv): every test passed (1071 passed + 8 skipped, and
the 94 hpc/slurm tests that need `venv/` at the clone's root: 147 passed, 5 skipped when rerun with
it linked), so no existing test changed outcome; 126 new tests (structure 59, geometric 21,
multislice 11, pipeline 35). One more test, `test_amorphous_si_layer_between_oxide_and_crystal`,
was added after these runs started and was run alone: `1 passed, 11 deselected in 0.08s`.
Existing tests changed: only the expected registry in `tests/io/test_io_config_stand_ins.py`
(B41 added, as instructed); no tolerance was changed.

## 6. Proposed B41 row (for the orchestrator; E4 does not edit docs/)

| B41 | Demo continuum oxide overlayer (report E4; L8 section 8 as corrected by E9): a conformal continuum layer grown from the crystal on the bulk-terminated demo staircase; t_ox = 2.0 nm (variants `oxide_2p0nm`, `oxide_2p0nm_no_absorption`, `multislice_tiny_oxide_2p0nm`) or 1.5 nm (`oxide_1p5nm`, `oxide_1p5nm_no_absorption`), thermal-oxide equivalent at 2.20 g/cm^3 (E9 M3: 1.5 nm is the midpoint of the route that matches a milled surface, 2.0 nm the midpoint of the union 0.9-2.9 nm; a choice, not a sourced centre); f = 0.4415 (`tools/review/e9_recompute_output.txt` line 143), consumed layers 7 (5) = the nearest whole count of 6.50 (4.88) a/4 layers (lines 125-127); V_ox = 10.34 V (independent-atom value at 2.20 g/cm^3, line 166, consistent with a later atomistic layer; measured span 10.1-11.5 V); V'_ox = 0.40 V (L8's nominal; 1/(2 sigma Lambda) = 0.4024 V for Lambda = 1705 A, line 20; a model value, not a bound, E9 M1) or 0 V; vacuum edge and oxide/Si interface graded 0.5 A (erf, Gaussian gradient of s.d. 0.5 A; E9 M4, line 241); no amorphous Si under the oxide (0 nm, the optimistic bound, E9 M5). Stands in for PROJECT_INPUT item 12 (witness measurement of oxide thickness with its convention, a-Si, roughness) in the variants of `configs/demo_smoke_si001.yaml` only (the base keeps B26; purpose demo; a run with purpose "comparison" refuses it); not comparable to experiment. Code: `reflection_holo/structure/oxide.py`, `forward/multislice/overlayer.py`, `forward/geometric/model.py` (report E4). | ASSUMPTION (values SECTION_READ/REPRODUCED via E9; the choices are ASSUMPTION) | Conformal = equal thickness and equal consumed-layer count (E9 M2): every step phase unchanged (10.9761 rad a/4, 21.9522 rad a/2 at 16.1347 mrad, line 91); a grown thickness difference changes it by 4.27-4.71 rad/A (lines 109-117), a top-surface-only difference by 0.87-0.98 rad/A (lines 96-103), one extra consumed layer by 13.70 rad (line 123); at <110> the terrace type at a buried a/4 step depends on the parity of the consumed-layer count (E9 section 3 item 2). Not represented: elastic diffuse scattering of the amorphous network, charging (item 22), carbon, the transition layer, TDS in the layer. |

Rows the orchestrator may want to update (E9 section 6 lists the texts): B7 and B12 (the continuum
oxide is now implemented in both engines with consumption and a graded edge; the atomistic content
is still NOT IMPLEMENTED), B4/B18 and docs/05:38, :126 (conformal continuum layer preserves B4 at
<100>; parity at <110>), docs/08 row 2.6 (implemented as a continuum; pipeline gate lifted only with
the complete item-12 record), docs/05 (variants may replace whole CFG-B records, `cfg_b_parameters`),
and a line for the new assertion `item4_buildup_length_through_overlayer`.

## 7. NOT RUN / not implemented

* The atomistic amorphous SiO2 layer (L8 section 5, Zenodo ACE model): NOT IMPLEMENTED; the
  continuum layer produces no elastic diffuse scattering and no speckle.
* The [110] configuration with the layer in the multislice (E9 M4: to be compared with the atomistic
  layer, not with the continuum alone): NOT RUN.
* Any independent check of the multislice with a layer (e.g. the sim-trhepd-rheed solver with a
  surface layer), the fixed-beam translation gate with a layer, and dx/dz convergence of (c) and (d):
  NOT RUN. The raw ratio of (c) is not converged in cell length (section 4).
* Non-conformal (grown-oxide) cases and the a-Si layer in multislice PROPAGATION: NOT RUN (only the
  geometric engine and the potential construction are tested); per-terrace overrides are refused by
  the pipeline.
* cupy/GPU backend with the layer: NOT RUN (no GPU); `engine.memory_model` does not include the layer
  arrays (one complex nx x ny array for terraces along y, n_terraces x nx along z, plus the transient
  of the sum).
* The oxide on the feature (half-torus) path and under a reconstruction: refused, not implemented.
* A demo_hpc oxide variant and HPC runs: not added, NOT RUN.
* Manifest: the oxide specification's hash enters the engine manifest through the configuration
  hash (potential provenance, cell terrace records), not as a separate `input_hashes` entry (not
  added, to keep the tested engine code unchanged after the suite runs).
* Docs: B41 row and the rows of section 6 are NOT written (orchestrator);
  `tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions` fails until
  the B41 row exists (expected).
