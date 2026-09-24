# A8 - Audit of E4 (continuum oxide overlayer) at commit 83fa75f

Auditor: agent A8, 2026-09-24. Status: FINAL (written incrementally; this is the reorganised final
state).

Scope: report E4 (`docs/agent_reports/E4_oxide_overlayer.md`) and its code at commit 83fa75f,
against L8 (`docs/agent_reports/L8_oxide_plasma.md`, read in full), its review E9
(`docs/agent_reports/E9_oxide_review.md`, read in full) with `tools/review/e9_recompute_output.txt`
("out:N"), `docs/model_assumptions.md` (B4, B7, B12, B26, B41) and `docs/physics_conventions.md`.
Code read completely: `reflection_holo/structure/oxide.py`, the E4 parts of `structure/si001.py`,
`forward/cell.py`, `forward/multislice/overlayer.py`, the E4 parts of `forward/multislice/engine.py`
(and `potentials.py`, `analysis.py` as used), `forward/geometric/model.py` (E4 parts),
`geometry/refraction.py` (E4 part), `pipeline/config.py` (E4 parts and the comparison gate),
`pipeline/engines.py`, `pipeline/run.py` (E4 part), `configs/demo_smoke_si001.yaml` (five oxide
variants), `io/assumption_registry.yaml`, and the five new test files plus the changed
`tests/io/test_io_config_stand_ins.py`.

Context: PROJECT_INPUT (Ali, 2026-09-24): air-exposed, O2/Ar plasma-cleaned, ion-milled Si(001);
holograms recorded through an oxide; 200 keV, specular (0,0,8), 16.1347 mrad.

Rules kept: audited in a detached worktree (`venv` symlinked, gitignored; PYTHONPATH at the
worktree; nothing installed); the code under audit was never modified (mutations were applied to
scratch copies only); nothing committed or pushed; nothing written under the repository's
outputs/ (checked, section 12); the only repository file written is this report; no personal data.

Severity scale: BLOCKER (wrong physics or a gate that lets a stand-in into a comparison), MAJOR
(must be fixed before the affected item is adopted), MINOR (fix when adopting), NIT.

## Verdict table

| item | verdict | findings |
|---|---|---|
| (1) physics of the layer: V + iV' on the layer only, following the surface, erf edge, sampling, band; sign and magnitude of V', 1/(2 sigma Lambda) | CONFIRMED (absorption, not gain; equivalence exact; surface-following; point sampling and band assertion correct) | A8-m5 (interface grading not enforced) |
| (2) geometry: f, consumed layers, conformal, buried step and parity, a-Si, overrides | CONFIRMED for f = 0.441507, the count rule, the conformal definition, (o1)-(o4) and parity, a-Si placement, overrides | A8-M2 (continuum layer overlaps the atomistic crystal by 0 to a/4), A8-m4 (2 nm sits on the rounding boundary) |
| (3) analytic checks; tolerances; deliberate breakage | every number CONFIRMED to printed precision; tolerances a priori; the four named breakages each fail a test | A8-m1 (E9's Born edge suppression quoted as exact; the engine is right), A8-m6 (overlayer build-up assertion untested) |
| (4) multislice (c) | absorption-only comparison set up correctly (0.505-0.532 vs 0.521); the raw-ratio drift is a read-out-window artefact, not a bug and not build-up | A8-m7 (report interpretation) |
| (5) smoke (d) +1.878 vs +1.590 rad | build-up (cell length) and narrow-terrace artefact shared with the layer-free crystal; at 5575 A the layer changes the a/4 phase by <= 0.05 rad | none (E4 did not interpret it) |
| (6) bit-identity without a layer | CONFIRMED: 76 arrays and 26 metadata records identical to 54de605, incl. the null-test cases and two pipeline runs | none |
| (7) pipeline gate | no silent default reaches an engine; comparison runs refuse B41; no smuggling path through variant CFG-B records | A8-M1 (a measured item-12 record cannot say "no a-Si"), A8-m2 (B41 id accepted with values its row does not state), A8-n1, A8-n3 |
| (8) B41 row and registry vs code | AGREE on every value and label | A8-n2 (contradictory B4 texts in the metadata) |
| (9) tests weakened? | NO: one existing file changed, additions only | none |
| (10) memory model | omission measured: exactly one complex array per pixel for terraces along y (+0.19-0.26 GB, +4.5-7.4 % for the H2 production cells), negligible along z | A8-m3 |
| test runs | structure 332 passed; io 128 passed; pipeline 129 passed; forward 133 passed, 3 skipped, 1 failed; full 1291 passed, 8 skipped, 1 failed. The failure is the wall-time assertion of `test_smoke_atomistic_a2_step_0008` (186 s > 120 s at load 15 on 4 shared cores); it passes in 83.5 s (WT) and 84.2 s (54de605) at load 6-7, and its exit wave is bitwise identical to 54de605 (section 6): environmental | none |

Overall: no BLOCKER. The layer's physics (sign, magnitude, geometry, phase terms, surface
following, grading) is right and E4's reported numbers reproduce to every printed digit; the
engine even reproduces the exact reflectivity of a 0.5 A erf edge that E4 dismissed as a numerical
floor. Two MAJOR findings concern the adoption path (the item-12 gate for real inputs, and the
registry of the continuum layer on an atomistic crystal), seven MINOR and three NIT concern
documentation, test coverage, the memory model and stand-in checking.

## Findings

### BLOCKER

None.

### MAJOR

**A8-M1. A PROJECT_INPUT item-12 record cannot state "no amorphous Si" (comparison runs).**
`pipeline/config.py:985-988` gives every oxide parameter the ONE qualified label of the item-12
record; `structure/oxide.py:199-202` refuses `amorphous_si_thickness_A = 0` unless its label starts
with ASSUMPTION or TEST_ONLY. Item 12 is blocking (`config.py:72`), so a comparison run needs a
PROJECT_INPUT record, and then a-Si = 0 is always refused. Why it matters: E9 M5 allows 0 nm when
the final milling step was a low-energy polish, so Ali's witness measurement may well report no
a-Si; the only way through is to invent an a-Si layer (thickness, V_a, V'_a, and a different
consumed-layer count), i.e. to falsify the input. Reproduction (C10, `SP/a8/a8_gate.py` probe 8):

    [REFUSED ] PROJECT_INPUT oxide, a-Si 0 (measured), V' 0.40, purpose comparison:
      PipelineConfigError: cfg_b.surface_preparation_details.overlayer (docs/06 item 12):
      amorphous_si_thickness_A = 0 (the optimistic bound, E9 M5) must carry the label ASSUMPTION
      (or TEST_ONLY in tests)

E4's test `test_zero_absorption_or_a_si_under_project_input_needs_assumption`
(`tests/pipeline/test_oxide_pipeline.py:119-127`) states this as intended in its docstring (its
body exercises only V' = 0, which is refused first). Fix: per-parameter labels in the item-12
record (the spec already carries one label per parameter), or accept a PROJECT_INPUT zero that
states its detection limit; keep the refusal for V'_ox = 0 (not a measurement).

**A8-M2. On an atomistic crystal the continuum layer overlaps the kept crystal by 0 to a/4, and the
recorded "interface quantisation" misstates the registry.**
`structure/oxide.py:40-43, 295-314`: the pre-oxidation surface H is the top ATOMIC plane, so
x_i = H - f t and x_t = H + (1 - f) t, and the count rule is |N a/4 - (f t + t_a)| <= a/8. An
atomistic crystal whose top N layers are removed ends at its equivalent boundary H - N a/4 + a/8
(half a layer above its top atomic plane; Si atoms are conserved, the rule E4 itself uses for f).
The layer therefore overlaps the kept crystal by f t + t_a - N a/4 + a/8, which the rule bounds to
[0, a/4] (not [-a/8, a/8], as `interface_quantisation_A` suggests); the whole stack sits on
average a/8 = 0.68 A too low relative to the atoms. Reproduction (C9, `SP/a8/a8_registry.py`: the
engine's own AtomicPotential + ContinuumOxidePotential, laterally averaged):

    t 20 A, N 7, 2.200 g/cm^3: overlap +0.005 A; max V near the top atom 25.2 V
    t 15 A, N 5, 2.200 g/cm^3: overlap +0.513 A; max V 28.1 V
    t 20 A, N 6, 2.198 g/cm^3: overlap +1.355 A; max V 33.7 V

Why it matters: a conformal step phase is unaffected (common to all terraces) and the B41
multislice variant (2 nm) happens to sit at 0.005 A, but for any other thickness (Ali's measured
one) the top Si layer is immersed in up to 10 V of oxide potential, the vacuum edge is up to one
layer spacing too low, and the geometric engine (continuum interface at x_i, consumption f t) and
the multislice (atoms ending at H - N a/4, layer added on top of them) describe different
interfaces; for a grown-oxide thickness difference below one layer the multislice keeps the Si and
adds oxide where the geometric engine removes Si (non-conformal multislice runs are NOT RUN by E4).
Fix: place the stack from the kept crystal's equivalent boundary (take the pre-oxidation surface of
an atomistic terrace at H + a/8, or tie x_i to H - N a/4 + a/8 and quantise the consumed depth in
both engines), and record the true overlap/gap and its bound.

### MINOR

**A8-m1. The 0.5 A erf-edge suppression quoted in the code is E9's Born estimate; the exact value is
7.5 times larger in |r|, and the engine reproduces the exact value.** C6 (exact 1-D transfer
matrix, converged in step size 0.004-0.001 A and span): abs r^2 = 1.9545e-9 at 16.1347 mrad and
1.8345e-9 at E4's central bin (16.1751 mrad), against the Born factor exp(-(q w)^2) giving
3.44e-11 (E9 out:241); at w = 0.1 A exact 1.3064e-3 vs Born 1.3036e-3 (0.2 %). E4's engine value at
w = 0.5 A, 1.835e-9, equals the exact 1.8345e-9 to four digits, so it is not "the numerical floor"
(E4 section 4(a), line 156) but a validation. The Born figure is quoted as fact in
`structure/oxide.py:31-33`, in the refusal message `oxide.py:196` ("0.5 A suppresses |r| by
1.1e-4"), in `forward/geometric/model.py:50` and in the print of
`tests/forward/test_oxide_multislice.py:85-86`. The M4 conclusion is unaffected (2e-9 is about 1e-7
of the crystal's reflectivity). Fix: quote the exact value or call it a Born estimate.

**A8-m2. A stand-in id vouches for values its row does not state.** C10: B41 with `overlayer: none`,
with t = 50 A / N = 16 / V' = 0.1 V, or with `interface_width_A: 0` is accepted; only B26 with an
oxide is refused (`config.py:1016-1020`). The convergence gate refuses a contradicting stand-in in
both directions (`CONVERGENCE_STAND_IN_ZERO`). Fix: refuse B41 with "none" and check the B41 values
against its row (or let the row say "any demo values").

**A8-m3. `engine.memory_model` omits the layer (C11, measured).** One working-precision complex
array per pixel for terraces along y (+8.1 B/px complex64, +16.1 B/px complex128; +0.1 B/px without
a layer), negligible along z. H2 production cells (complex64): a/4 step parallel to the beam, 0.1
deg miscut, 2000 x 12096 px: +0.194 GB on a modelled 4.096 GB (+4.7 %; +7.4 % of the 2.602 GB cupy
device part); r = 0.05, 2700 x 12096: +0.26 GB on 5.8 GB. On cupy the layer is also built on the
host in complex128 (`overlayer.py:240-247`), about 32 B/px of host transient (0.77 GB for the 0.1
deg cell; code reading, no GPU). The HPC kit inherits the omission.

**A8-m4. The 2.0 nm stand-in sits on the rounding boundary of the consumed-layer count.** f t/(a/4)
= 6.5036 layers, 0.0036 layer (0.005 A) from 6.5; N flips from 7 to 6 at 2.19877 g/cm^3 (-5.6e-4
relative; C5). The parity of N decides the terrace type at a buried a/4 step at <110> (E9 section 3
item 2; C12 on the atoms: N = 7 swaps both terraces, N = 6 keeps them), so for B41 at 2 nm that
parity is set by the fourth significant digit of an assumed density. The B41 row should say so.

**A8-m5. The oxide/Si transition is not required to be graded.** E9 M4's required addition covers
"the vacuum edge and oxide/Si transition"; the code enforces >= 0.5 A only for the vacuum edge
(`oxide.py:180-197`); `interface_width_A` accepts 0 or any value in (0, 0.5) with any label
(`oxide.py:198`), and the pipeline accepts 0 under B41 (C10). A sharp 10.34/13.90 V step reflects
abs r^2 = 2.5e-4 (r = -0.01567, C5; E9 out:234): common-mode for a conformal layer, but it would
dominate the attenuated crystal reflectivity at [110] (about 9e-5, E9 out:247), and on an atomistic
crystal it sits up to a/4 away from the atoms (A8-M2).

**A8-m6. The new docs/05 4.3 assertion `item4_buildup_length_through_overlayer`
(`forward/cell.py:408-419`) has no refusal test.** Mutation M13 (the assertion ignores the stack)
passes the whole oxide suite (section 3.3). The check itself is correct and conservative (external
angle in the stack).

**A8-m7. E4's reading of the (c) length series (report section 4(c)).** The drift 0.37 -> 0.54 ->
0.62 is the read-out window, not the surface-step Fresnel term: at 3000 A 95 % of the oxide runs'
specular beam lies inside the window ramp or below it, 55 % of the clean run's (section 4). The
3000/4500 A values should be marked read-out-truncated; "within 2 % at every length" becomes 3.1 %
at 9000 A.

### NIT

* **A8-n1.** Oxide numbers given as strings are accepted (`oxide.py:126-139` uses float();
  C10: `V_imag_V: "0.4"` accepted); the spec then carries and hashes the string.
* **A8-n2.** At <100> every buried step under the oxide records `buried_b4 = B4_A4_100`
  (`si001.py:382-386`), whose text says B4 "does not apply to ... an overlayer", next to
  `model_assumption_B4_overlayer` saying the conformal layer preserves it (C12); the geometric
  engine accepts the step on the first string.
* **A8-n3.** An item-12 value without `overlayer` (or `termination`) passes the load gate
  (`config.py:910`, `:1049` default to "none"/"bulk", pre-existing) and is refused only by
  `engines.build_structure` (`engines.py:91`); no silent default reaches an engine, but
  list-inputs and the load report nothing.

## 0. Command log

Abbreviations: WT = the audit worktree (83fa75f); SP = the session scratchpad
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`; PY =
`/home/user/Holography/venv/bin/python`; every Python run with `PYTHONPATH=<tree>`. Scripts and
outputs are in `SP/a8/` (not in the repository).

| # | command | purpose | result |
|---|---|---|---|
| C1 | `git -C /home/user/Holography worktree add --detach SP/a8_wt 83fa75f`; `ln -s /home/user/Holography/venv SP/a8_wt/venv` | audit tree | HEAD 83fa75f, clean |
| C2 | `git diff --stat 685e434 83fa75f`; `git diff --stat 54de605 83fa75f`; `git log 685e434..83fa75f`; `git diff --diff-filter=M --name-only 685e434 83fa75f -- tests/` | scope (E4's own change is 54de605..83fa75f, 24 files) | section 9 |
| C3 | `git diff 685e434 83fa75f -- <each code file in scope>`; reads of the files above | code reading | - |
| C4 | `SP/a8/run_dirs.sh`: WT, `PY -m pytest -q tests/<d> -p no:cacheprovider`, d = structure, io, pipeline, forward -> `pytest_<d>.txt` | directory runs | section 11 |
| C5 | `PY SP/a8/a8_analytic.py` -> `a8_analytic.out` (first principles, no package import) | item (3), f, N | sections 2, 3 |
| C6 | `PY SP/a8/a8_exact1d.py` -> `a8_exact1d.out` (exact 1-D reflectivity of the erf edge) | item (3) | section 3 |
| C7 | `git -C /home/user/Holography archive 54de605 \| tar -x -C SP/a8/base_54de605` (and 685e434) | baselines outside the repository | - |
| C8 | `SP/a8/run_bitid.sh` (`PY a8_bitid.py <tree> <npz>`, base and WT). First two attempts FAILED (my script: a 20 A cell depth on a 10-layer structure; then the base archive has no git, which the pipeline refuses); third attempt saved sections 1-7 for both trees and all sections for WT | item (6) | section 6 |
| C9 | `PY SP/a8/a8_registry.py` -> `a8_registry.out`, `profile_t*.txt` | item (2), A8-M2 | section 2 |
| C10 | `PY SP/a8/a8_gate.py`, `PY SP/a8/a8_gate2.py` -> `a8_gate.out`, `a8_gate2.out` (in-memory configuration probes) | item (7) | section 7 |
| C11 | `PY SP/a8/a8_memory.py` -> `a8_memory.out` (tracemalloc vs `memory_model`) | item (10) | section 10 |
| C12 | `PY SP/a8/a8_b4text.py` -> `a8_b4text.out` | item (2) parity, A8-n2 | section 2 |
| C13 | `PY SP/a8/a8_mutate.py --files=<structure, geometric, pipeline oxide tests> M0 M2 M3 M4c M6 M9 M10 M11` -> `mut_batch1.out`, `mut/*.log` (copies without git: the pipeline end-to-end test failed on the git preflight in every copy, control included) | item (3) | section 3.3 |
| C14 | `SP/a8/run_mut2.sh`: `a8_mutate.py M0 M6` (all oxide files) and `a8_mutate.py --files=tests/forward/test_oxide_multislice.py M1 M4 M4b M5 M5b M7 M8 M12 M13`, copies made throw-away git repositories -> `mut_batch2a.out`, `mut_batch2b.out` | item (3) | section 3.3 |
| C15 | `git -C SP/a8/base_54de605 init` + commit (throw-away, scratch only); `PY a8_bitid_pipe.py <base> <npz>`; `PY a8_bitid_compare.py bitid_base_merged.npz bitid_wt.npz` -> `a8_bitid_compare.out` | item (6) | section 6 |
| C16 | `PY SP/a8/a8_smoke_d.py 0 3000` -> `a8_smoke_d.out` | item (5) | section 5 |
| C17 | `PY SP/a8/a8_flat_c.py 3000 6000` -> `a8_flat_c.out` | item (4) | section 4 |
| C18 | `PY SP/a8/a8_smoke_d2.py 0` -> `a8_smoke_d2.out`, `smoke2_*.npz` | item (5), read-out | section 5 |
| C19 | WT: `PY -m pytest -q -p no:cacheprovider` (full suite) -> `pytest_full.txt` | full suite | section 11 |
| C20 | `PY SP/a8/a8_flat_c.py 9000` -> `a8_flat_c9000.out`; `PY a8_smoke_regions.py`, `PY a8_smoke_regions2.py` -> `a8_smoke_regions*.out` | items (4), (5) | sections 4, 5 |
| C21 | `PY SP/a8/a8_pipe_oxide.py multislice_tiny_oxide_2p0nm oxide_2p0nm` (WT; outputs in `SP/a8/pipe_*`) -> `a8_pipe_oxide.out` | E4's pipeline demo claims | section 11 |
| C22 | `PY -m pytest -q -s tests/forward/test_smoke_atomistic.py` in WT and in the 54de605 archive -> `smoke_timing.out` | the one failing test | section 11 |
| C23 | `git -C SP/a8_wt status --short`; `find /home/user/Holography/outputs -newer SP/a8/a8_analytic.py -type f` | nothing written into WT or outputs/ | empty, empty |
| C24 | `git -C /home/user/Holography worktree remove SP/a8_wt`; `git worktree prune`; `git worktree list` | cleanup | section 12 |

Read-only inspection commands (not listed one by one): `git status/log/show/diff`, `grep`/`rg`,
`sed -n`, `cat`, `ls`, `ps`, `/proc/loadavg`, `nproc`, `free`.

## 1. Physics of the layer (item 1)

* Profile. `overlayer.py:194-204` builds `(V_ox + i V'_ox) [E(x; x_t, w_v) - E(x; x_i, w_i)]` (+ the
  a-Si term) for each terrace from its own recorded stack (`t["oxide"]`, cell frame,
  `cell.py:137`, `cell.py:303`). x is the outward normal (x_t > x_i): the bracket is 1 inside the
  layer, 0 above and below. CONFIRMED.
* Region. Terraces along y: each terrace's profile times its cell-averaged y fraction
  (`overlayer.py:239-247`); along z: one (nx, 1) profile per terrace times the slice overlap with
  the terrace, clipped to the crystal's z range (`overlayer.py:234-265`); nothing in the entrance
  vacuum. Follows the surface, not a planar mask: CONFIRMED (test and mutations M4b, M7).
* Edge and sampling. `edge_profile` (`overlayer.py:62-69`) = erfc((x - x0)/(sqrt(2) w))/2, an erf
  whose gradient is a Gaussian of s.d. w (E9's definition), point-sampled at pixel centres; w = 0
  is the cell-averaged pixel fraction. w_v >= 0.5 A enforced (`oxide.py:180-197`) except with the
  TEST_ONLY flag; dx <= w asserted before any run (`overlayer.py:149-153`); first alias
  exp(-2 pi^2) = 2.67e-9 at dx = w, as stated. The layer's internal angles join the band assertion
  (`engine.py:239-242`; mutation M12). CONFIRMED (A8-m5 for the interface).
* Sign and magnitude of V'. The engine transmits exp(i sigma V_proj) (`engine.py:199`) with
  V_proj = sum_g (V + iV') w_g: amplitude exp(-sigma V' path), absorption. Intensity
  exp(-2 sigma V' L) = exp(-L/Lambda) gives V' = 1/(2 sigma Lambda); C5: sigma = 7.2884010e-4
  rad/(V A), Lambda 1780 / 1705 A -> 0.3854 / 0.4024 V (E9 out:19-20). Geometric engine: Im k'_perp
  from the complex relativistic Delta (`refraction.py:145-169`); C5: exp(-2 Im k' t) = 0.52130
  (0.40 V, 2 nm) = refracted-path form exp(-sigma V' 2t/sin theta_in) = 0.52131. CONFIRMED.
* Mean inner potential stays the crystal's (`overlayer.py:121-122`); B32 unchanged. CONFIRMED.

## 2. Geometry (item 2)

* f: rho_Si = 2.32919 g/cm^3 (a = 5.4309 A), f(2.20) = 0.441507 (C5) from the stated molar masses
  (`constants.py:38-44`); `oxide.py:255-264` is the same formula; f t = 8.8301 / 6.6226 A for 2.0 /
  1.5 nm (E9 out:143). CONFIRMED.
* Consumed-layer rule (`oxide.py:295-303`): |N a/4 - (f t + t_a)| <= a/8, refused otherwise naming
  the nearest count. CONFIRMED; the 2 nm case sits 0.0036 layer from the boundary (A8-m4).
* Conformal = equal thickness AND equal count (`oxide.py:315-316`; per step `si001.py:878-879`).
  CONFIRMED. With the count rule, equal thickness already implies equal count except at an exact
  tie, so the count half is untestable in practice (mutation M6, benign).
* Buried step and terrace type: (o1)-(o4) measured on the kept atoms (`si001.py:827-918`). C12: a/4
  step, N = 7 at [100] and [110]: buried screw, both back-bond axes swapped; N = 6: not swapped;
  at [110] the buried a/4 step records B4 "does not apply" and the geometric engine refuses it.
  CONFIRMED (A8-n2 on the <100> text).
* a-Si: x_c = x_i - t_a at the crystal's density, included in the count rule
  (`oxide.py:296-307`). CONFIRMED for the potential construction (test); propagation NOT RUN.
* Per-terrace overrides: honoured by `terrace_stacks`, refused by the pipeline. CONFIRMED.
* Registry on an atomistic crystal: A8-M2 (C9 profiles above).

## 3. Analytic checks, tolerances and deliberate breakage (item 3)

### 3.1 Independent recomputation (C5, C6)

| quantity | A8 | E9 / E4 | verdict |
|---|---|---|---|
| lambda, k, sigma, k_perp at 16.1347 mrad | 0.02507934 A, 250.5323, 7.2884010e-4, 4.04209 | out:6-11 | CONFIRMED |
| k'_perp(10.34 V) | 4.484934 | out:36 4.48493 | CONFIRMED |
| conformal a/4, a/2 | 10.97609, 21.95218 rad | out:91 | CONFIRMED |
| top-surface rate 2(k' - k) | 0.88569 rad/A | out:98 0.8857 | CONFIRMED |
| grown rate 2k' - 2k(1 - f) | 4.454915 (f exact), 4.454855 (f = 0.4415) | out:113 4.45486 | CONFIRMED |
| one consumed layer | q/f = 3.07520 A, 13.69977 rad (also by direct construction -2k dx_t + 2k'(dx_t - dx_i)) | out:123 3.0753, 13.6998 | CONFIRMED |
| zero-loss 2 nm, 0.40 V | amplitude 0.52130 (intensity 0.2718) | E4 0.5213 | CONFIRMED |
| same, 0.3854 V | intensity 0.2850 | out:57 | CONFIRMED |
| Fresnel vacuum/10.34 V | r = -0.051934, abs r^2 = 2.69718e-3 | out:234, 284 | CONFIRMED |
| E4 "analytic 2.67299e-3 at the central bin" | the Fresnel value at 16.1751 mrad, the grid's central incident bin | E4 4(a) | CONFIRMED |
| E4 sharp-edge multislice 2.65300e-3 | 2.67297e-3 x (1 - 2 x 0.0038): the rung-1 cell-averaging bias -((q1 + q2) dx)^2/12; residual 5.9e-5 in amplitude | E4 4(a) | CONFIRMED |
| w = 0.1 A, exact 1-D | 1.3064e-3 (16.1347 mrad); 1.2905e-3 (16.1751) | Born 1.3036e-3; E9 1-D multislice 1.3067e-3 (out:285); E4 engine 1.29044e-3 | engine = exact to 5e-5 relative |
| w = 0.5 A, exact 1-D | 1.9545e-9 (16.1347); 1.8345e-9 (16.1751); abs r suppressed by 8.5e-4 | Born 3.44e-11 (out:241, 1.13e-4 in abs r); E4 engine 1.835e-9 | engine = exact; Born 57x low (A8-m1) |

### 3.2 Are the tolerances a priori and meaningful?

* Structure and geometric tests: E9 lines at printed precision plus the stated f-rounding bound;
  the engine's own terms are pinned by finite differences at 1e-9 against `oxide_phase_rates`,
  itself pinned to E9. A priori and meaningful.
* Multislice (a): sharp edge |err - model| <= 3.5e-3 and phase <= 1e-3 rad (rung-1, a priori;
  measured 5.9e-5 and 6e-5 rad). w = 0.1 A within 1 % of the Born factor (engine 0.11 % from Born,
  0.005 % from exact: budget holds by a factor 9). w = 0.5 A ratio <= 1e-3 (measured 6.9e-7; the
  test alone cannot tell w = 0.35 A from 0.5 A, the w = 0.1 A test pins the width convention, M5b).
* (c) and (d) assert no physics (E9 M1; smoke). The layer's absorption magnitude is pinned only by
  the potential-construction test (imaginary part 0.40 V at rtol 1e-9), not by a propagated run.

### 3.3 Mutations (C13, C14; each applied to a scratch copy, never to WT; (c) and (d) deselected;
control M0: 125 passed)

| mutation | what | failed tests | caught by |
|---|---|---|---|
| M1 | V'_ox sign flipped in the multislice layer (gain) | 2 | surface-following, a-Si potential tests |
| M2 | V'_ox sign flipped in k'_perp (geometric) | 3 | conformal a/4 and a/2 (amplitude > 1), zero loss (3.51 instead of 0.2850) |
| M3 | f = 0 in the stack (non-consuming layer) | 12 | E9 stack/count tests, builder, engine differentials, multislice dry run |
| M4 | layer mirrored below the interface | 5 | all three edge tests, surface-following, a-Si |
| M4b | planar mask (terrace 0's layer everywhere) | 1 | surface-following test |
| M4c | sign of the top-surface term | 5 | conformal (amplitude), differentials, zero loss |
| M5 | edges never graded | 2 | w = 0.1 A and w = 0.5 A tests |
| M5b | erfc(x/w)/2 instead of erfc(x/(sqrt2 w))/2 | 1 | w = 0.1 A test |
| M6 | conformal = equal thickness only | 0 | none (benign, section 2) |
| M7 | layer in the entrance vacuum | 1 | surface-following test |
| M8 | V'_ox dropped in the multislice | 2 | potential-construction tests |
| M9 | count rule relaxed to +-1.5 layers | 2 | refusal tests |
| M10 | B41 removed from `demo_only` | 0 | none (benign: item 12 is blocking, any ASSUMPTION for it is refused and the message still names B41) |
| M11 | variant CFG-B records ignored | 8 | every B41 variant test |
| M12 | layer angles not in the band assertion | 1 | setup-record test |
| M13 | overlayer build-up assertion ignores the stack | 0 | none (A8-m6) |

(Batch C13 counts exclude the git-preflight failure of the pipeline end-to-end test, which failed
in every copy without git including the control; batch C14, with git, confirms the control.) The
four named breakages (wrong sign of V'_ox, f = 0, layer on the wrong side, edge not graded) each
fail at least one test: CONFIRMED.

## 4. The flat multislice result (c) (item 4; C17, C20)

E4's helpers (`atomistic_case`, `windowed_reflection`; [100], r = 0.1, (0,0,8) at the IAM MIP, one
box and grid per length), plus a clean run launched at the SAME absolute height as the oxide runs
(22.67 A instead of 2 A above the crystal) and the fraction of the specular beam (aperture 0.02
1/A) lying below the full-weight part of the read-out window (start + 40 A ramp) at the exit plane.
E4's numbers reproduce to every printed digit (3000 A: 0.3724 / 0.7000 / 0.5319; 6000 A: 0.6228 /
1.1862 / 0.5250).

| extra (Lz) | bin | abs r: clean / clean same launch / oxide / oxide V'=0 | beam below window (same order) | oxide/clean (E4) | oxide/clean same launch | V'=0/clean (E4), same launch | absorption only (model 0.5213) |
|---|---|---|---|---|---|---|---|
| 3000 A (5493 A) | 16.1545 mrad | 0.1592 / 0.0800 / 0.0593 / 0.1114 | 0.55 / 0.98 / 0.95 / 0.95 | 0.3724 | 0.7412 | 0.7000, 1.3934 | 0.5319 |
| 6000 A (8491 A) | 16.0895 mrad | 0.1333 / 0.1318 / 0.0830 / 0.1581 | 0.016 / 0.044 / 0.017 / 0.022 | 0.6228 | 0.6301 | 1.1862, 1.2000 | 0.5250 |
| 9000 A (11494 A) | 16.1092 mrad | 0.1363 / 0.1355 / 0.0798 / 0.1580 | 0.008 / 0.007 / 0.010 / 0.008 | 0.5856 | 0.5886 | 1.1598, 1.1659 | 0.5049 |

* The absorption-only comparison (0.40 V against 0 V) shares structure, cell, grid, beam, bin and
  read-out, and exp(-2 Im k'_perp t) is the correct in+out zero-loss factor (section 1): set up
  correctly, CONFIRMED; the engine gives 0.505-0.532 over 3000-9000 A (within 3.1 %).
* The raw-ratio drift is a read-out problem, not a bug and not build-up: at 3000 A 95-98 % of the
  oxide runs' specular beam (and of the clean run launched at the same height) is still in the
  window ramp or below at the exit plane, 55 % for E4's clean run, whose beam reaches the crystal
  about 1150 A earlier (the oxide runs start 2 A above the layer top and cross 20.67 A of layer at
  17.9 mrad). With the same launch height the 3000 A ratio is 0.74, not 0.37. Once the read-out
  is complete (>= 6000 A, < 5 % below) the ratio no longer depends on the launch (0.623 vs 0.630;
  0.586 vs 0.589) and the clean coefficient agrees between launches to 1.2 % and 0.5 %.
* What remains at complete read-out: oxide/clean 0.59-0.63 and a non-absorbing ratio of 1.16-1.20
  (the V' = 0 layer raises the (0,0,8) reflection by 16-20 %), consistent with E4's reading (the
  vacuum/Si surface step, r = -0.068 (C5), replaced by the smooth oxide/Si transition). The 6 %
  change between 6000 and 9000 A coincides with a 0.020 mrad bin shift and is not separated from it
  (a common-bin study: NOT RUN). A8-m7 on E4's wording.

## 5. The smoke result (d): +1.878 rad against the geometric +1.590 rad (item 5; C16, C18, C20)

E4's case ([100], a/4 step, parallel edges, two terraces 4 periods = 21.7 A wide, Kirkland,
r = 0.1), all runs in the same box and grid (`length_for_oxide`), E4's read-out (aperture 0.5 1/A,
central halves). Deviation = Delta_phi - (+1.5902 rad):

| cell length | layer 0.40 V | layer 0 V | clean, beam 2 A above the crystal | clean, launched at the oxide runs' height |
|---|---|---|---|---|
| 2577 A (E4's) | +0.2881 (amp 0.124/0.100) | +0.1900 (0.227/0.207) | -0.7350 (0.557/0.671) | -0.3760 (0.209/0.238) |
| 5575 A (+3000) | -0.5081 (0.500/0.571) | -0.5475 (0.958/1.063) | -0.5010 (0.843/0.961) | -0.5396 (0.865/0.975) |

* E4's +1.8784 rad (+0.2881) reproduces exactly.
* Decisive test: at E4's length the clean crystal in the same box deviates by -0.74 rad (-0.38 rad
  with the same launch) and the layered value moves by 0.8 rad when the cell grows by 3000 A; at
  5575 A all four runs agree within 0.05 rad (-0.50 to -0.55): the conformal layer changes the a/4
  step phase by at most about 0.05 rad, as E9 section 3 item 1 predicts. The common -0.5 rad is the
  layer-free crystal's own finite-cell / narrow-terrace deviation (fixed-beam gate not passed).
* The read-out at 2577 A is ill-conditioned (`a8_smoke_regions*.out`): within the central half of
  one 21.7 A terrace the per-column specular component varies by a factor 3-9 in amplitude and by
  104-234 deg in phase; one more pixel column in the region moves the deviation from +0.2881 to
  +0.2538 rad; region margins 0.20-0.40 W give +0.17 to +0.31 rad (layer) and -0.09 to -0.63 rad
  (clean); aperture 0.03 1/A gives +0.90 rad.
* Ruled out: the layer's own reflection (abs r = 4.4e-5 at w = 0.5 A against a crystal amplitude of
  0.1-1: at most 5e-4 rad) and the moved interface (common to both terraces; buried relations
  asserted on the atoms, C12).
* Absorption-only amplitude ratio at 5575 A: 0.522 and 0.537 (model 0.521).

Verdict: build-up (cell length) plus the narrow-terrace read-out, shared with the layer-free
crystal; not the layer. E4 rightly did not interpret it; its report should show the layer-free
value in the same box (-0.74 rad) next to it.

## 6. Bit-identity without an overlayer (item 6; C8, C15)

`a8_bitid.py` on the 54de605 archive (E4's starting commit) and on WT, nothing with a layer: rung 1
(continuum, flat), rung 3 (continuum a/4 step), rung 2 (periodic continuum, r = 0.1), the atomistic
smoke ([110], a/2, Kirkland), the null-test translation pair A and B (M2 cell, [110]) and the
null-test [100] step case, builder positions and metadata plus reflection cells for [100]/[110] x
parallel/transverse x bulk/p(2x1)s, the geometric engine at [100], and the pipeline arrays of the
base demo (geometric) and `multislice_tiny` (54de605's pipeline part from a throw-away git
repository of the archive, because the multislice manifest refuses a tree without git):

    arrays: 76 vs 76; same keys: True
    arrays bitwise identical: 74 of 76 (the other two, trace_source_z_A of both pipeline runs,
                                        contain NaN; their bytes are identical)
    metadata entries equal: 26 of 26 (timing and package_version removed)

CONFIRMED.

## 7. Pipeline gate (item 7; C10)

    [REFUSED ] comparison + oxide_2p0nm: ... demo stand-in (..., B41) ...
    [REFUSED ] comparison + multislice_tiny_oxide_2p0nm: frozen_phonons 'none' ... (and the demo list incl. B41)
    [REFUSED ] variant replaces lattice_parameter with a TEST_ONLY record: ConfigError ... TEST_ONLY values are accepted only from in-memory test fixtures
    [ACCEPTED] same with allow_test_only=True -> cfg.test_only = True (then refused by any comparison run)
    [REFUSED ] variant adds an unknown CFG-B parameter: ConfigError: CFG-B: unknown parameter 'made_up_parameter'
    [REFUSED ] variant sets cfg_b.glancing_angle_ext: ... declared once, in sections.illumination.glancing_angle (item 7)
    [REFUSED ] B41 as the assumption_id of mean_inner_potential_V: ... not mapped to PROJECT_INPUT item 20
    [ACCEPTED] B41 with overlayer 'none'                                  (A8-m2)
    [ACCEPTED] B41 with t 50 A, N 16, V' 0.1 V                             (A8-m2)
    [ACCEPTED] interface_width_A = 0 under B41                           (A8-m5)
    [ACCEPTED] V_imag_V given as the string '0.4'                        (A8-n1)
    [REFUSED ] PROJECT_INPUT oxide, a-Si 0 (measured), purpose comparison (A8-M1)
    item-12 value without 'overlayer' or 'termination': load ACCEPTED, build_structure REFUSED (A8-n3)
    sha256_resolved differs between oxide_2p0nm and oxide_1p5nm: True

* No silent default reaches an engine: every oxide key required (`config.py:976-983`), the fixed
  choices (no overrides, no sharp-edge flag) stated, missing top-level keys refused at build.
* Comparison runs refuse B41 (registry `demo_only` and item 12 in `BLOCKING_ITEMS`; either alone
  suffices, M10).
* Variant CFG-B records pass the same gate (`resolve_variant_cfg_b` then `load_config_dict`,
  `config.py:729-732`) and are hashed (`sha256_resolved`): no smuggling path found.

## 8. B41 row, registry and code (item 8)

`docs/model_assumptions.md:67` against `configs/demo_smoke_si001.yaml:534-755`,
`io/assumption_registry.yaml:52, 56` and the code:

| B41 statement | code / configuration | verdict |
|---|---|---|
| 2.0 nm in oxide_2p0nm, oxide_2p0nm_no_absorption, multislice_tiny_oxide_2p0nm; 1.5 nm in oxide_1p5nm(_no_absorption) | thickness_A 20.0 / 15.0 in exactly those variants | AGREE |
| 2.20 g/cm^3, f = 0.4415 | 2.20; f 0.441507 | AGREE |
| consumed layers 7 (5), nearest counts of 6.50 (4.88) | 7 / 5, asserted | AGREE (A8-m4) |
| V_ox 10.34 V; V'_ox 0.40 or 0 V | 10.34; 0.4 / 0.0 | AGREE |
| vacuum edge and interface graded 0.5 A | 0.5 / 0.5, erfc(x/(sqrt2 w))/2 | AGREE (the cited line 241 is the Born value, A8-m1) |
| a-Si 0 nm with its label | 0.0 under "ASSUMPTION B41 (stands in for PROJECT_INPUT item 12)" | AGREE |
| variants only; base B26; comparison refuses | base B26 `overlayer: none`; `B41: [12]`, in `demo_only` | AGREE |
| conformal phases; 4.27-4.71, 0.87-0.98 rad/A; 13.70 rad per layer | geometric engine; C5 | AGREE |
| not represented: diffuse, charging, carbon, transition layer, TDS | `oxide.py:73-76` | AGREE |

B4 (`model_assumptions.md:30`), B7 (:33), B12 (:38) agree with the code (A8-n2 on the metadata
text).

## 9. Tests changed between 685e434 and 83fa75f (item 9)

Five new files (oxide_cases.py, test_oxide_multislice.py, test_oxide_geometric.py,
test_oxide_pipeline.py, test_oxide_structure.py) and one modified file,
`tests/io/test_io_config_stand_ins.py` (+5/-1: B41 added to the expected registry and to
`demo_only`); no conftest changed. No existing test or tolerance weakened: CONFIRMED.

## 10. Memory model (item 10; C11)

tracemalloc peak of `run_realisation` (numpy backend; geometry assertions bypassed as
`tests/forward/test_memory_model.py` does; after a warm-up) minus `engine.memory_model`:

    terraces along y, complex64,  no layer: 672 x 504, +0.1 B/px
    terraces along y, complex64,  layer:    840 x 504, +8.1 B/px  (+1.01 cb)
    terraces along y, complex128, layer:    840 x 504, +16.1 B/px (+1.00 cb)
    terraces along z, complex64 / complex128, layer: +0.1 / +0.2 B/px

E4's statement (`overlayer.py:226-229`) is accurate; the size for production cells is in A8-m3.

## 11. Test runs and E4's pipeline claims (C4, C19, C21, C22)

    tests/structure: 332 passed in 28.21s
    tests/io:        128 passed in 1.26s
    tests/pipeline:  129 passed in 354.64s (0:05:54)
    tests/forward:   1 failed, 133 passed, 3 skipped in 1685.82s (0:28:05)
    full suite:      1 failed, 1291 passed, 8 skipped, 12 warnings in 2141.11s (0:35:41)
    FAILED tests/forward/test_smoke_atomistic.py::test_smoke_atomistic_a2_step_0008
        assert t_total < 120.0  ->  assert 186.14443448400561 < 120.0   (load 14-17 on 4 cores)
    rerun alone at load 5.8 (WT):  total 83.5 s, 1 passed
    rerun alone at load 7.4 (54de605 archive): total 84.2 s, 1 passed

The failure is a wall-time assertion under a shared, overloaded CPU; the test's exit wave is
bitwise identical to 54de605 (section 6). tests/io passes at 83fa75f (E4's run failed only because
the B41 row did not exist yet; it does now). Totals agree with E4's plus its later a-Si test.

E4's pipeline demo claims (C21): `multislice_tiny_oxide_2p0nm` runs end to end (88 s under load,
peak RSS 402 MB; E4: 57 s, 392 MB), heights withheld ("a terrace region is empty or below the
minimum size after the margin"); `oxide_2p0nm` returns +2.7153 +- 0.0165, -1.3578 +- 0.0082,
-1.3575 +- 0.0082 A, identical to E4. CONFIRMED.

## 12. NOT RUN and cleanup

NOT RUN: cupy/GPU with the layer (no GPU; the cupy host transient of A8-m3 is code reading); the
[110] configuration with the layer in the multislice; non-conformal (grown) and a-Si cases in
multislice propagation; the atomistic fixed-beam translation gate with the layer; dx/dz
convergence of (c) and (d); a common-bin cell-length study of (c); the amplitude consequence of
the A8-M2 overlap in a propagated run (only the potential profile, C9); an independent solver with
a layer; a demo_hpc oxide variant. The pipeline end-to-end test inside the first mutation batch did
not run meaningfully (no git in those copies; C13).

Nothing was written into WT (C23: `git status --short` empty) or into the repository's outputs/
(C23: no file newer than the start of the audit). Scratch files remain in `SP/a8/` (outside the
repository). Worktree removal (C24): `git worktree remove` succeeded; `git worktree list` now
shows only `/home/user/Holography`; the shared `venv` (symlink target) is intact.
