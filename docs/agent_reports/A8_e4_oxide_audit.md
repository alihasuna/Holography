# A8 - Audit of E4 (continuum oxide overlayer) at commit 83fa75f

Auditor: agent A8, 2026-09-24. Status: IN PROGRESS (written incrementally).

Scope: the continuum oxide overlayer of report E4 at commit 83fa75f, audited in a detached worktree
(`git worktree add --detach <scratchpad>/a8_wt 83fa75f`; `venv` symlinked into it, gitignored;
PYTHONPATH at the worktree; nothing installed). Base for diffs: 685e434. Context: PROJECT_INPUT
(Ali, 2026-09-24): air-exposed, O2/Ar plasma-cleaned ion-milled Si(001); holograms through an oxide;
200 keV, specular (0,0,8), 16.1347 mrad.

Nothing in the code under audit was modified; nothing committed or pushed; nothing written under
the repository's outputs/. Scratch scripts and their outputs live in the session scratchpad
(`<scratchpad>/a8/`), not in the repository.

## 0. Command log

(appended as the audit proceeds)

Abbreviations: WT = the audit worktree at 83fa75f; SP = the session scratchpad
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`; PY =
`/home/user/Holography/venv/bin/python`; every run below with `PYTHONPATH=<tree>`.

| # | command (cwd) | purpose | result |
|---|---|---|---|
| C1 | `git -C /home/user/Holography worktree add --detach SP/a8_wt 83fa75f`; `ln -s /home/user/Holography/venv SP/a8_wt/venv` | audit tree | HEAD 83fa75f, clean |
| C2 | `git diff --stat 685e434 83fa75f`; `git diff --stat 54de605 83fa75f`; `git log 685e434..83fa75f` | scope; E4's own change is 54de605..83fa75f (24 files) | see section 9 |
| C3 | `git diff 685e434 83fa75f -- <every code file in scope>` | read the change | - |
| C4 | `SP/a8/run_dirs.sh` (WT; `PY -m pytest -q tests/<d> -p no:cacheprovider` for d = structure, io, pipeline, forward) | directory runs | section 11 |
| C5 | `PY SP/a8/a8_analytic.py` (first-principles recomputation, no package import) -> `SP/a8/a8_analytic.out` | item (3) | section 3 |
| C6 | `PY SP/a8/a8_exact1d.py` (exact 1-D transfer-matrix reflectivity of the erf-graded edge) -> `SP/a8/a8_exact1d.out` | item (3) | section 3 |
| C7 | `git -C /home/user/Holography archive 54de605 \| tar -x -C SP/a8/base_54de605` (same for 685e434) | bit-identity baselines (outside the repository) | - |
| C8 | `SP/a8/run_bitid.sh` (`PY SP/a8/a8_bitid.py <tree> <npz>` for base_54de605 and WT) | item (6) | section 6 |
| C9 | `PY SP/a8/a8_registry.py` -> `a8_registry.out`, `profile_t*.txt` (laterally averaged V(x) of the engine's AtomicPotential + ContinuumOxidePotential) | item (2) registry | section 2 |
| C10 | `PY SP/a8/a8_gate.py`, `PY SP/a8/a8_gate2.py` -> `a8_gate*.out` (in-memory configuration probes) | item (7) | section 7 |
| C11 | `PY SP/a8/a8_memory.py` -> `a8_memory.out` (tracemalloc vs engine.memory_model, with and without the layer) | item (10) | section 10 |
| C12 | `PY SP/a8/a8_b4text.py` -> `a8_b4text.out` (buried relations, parity at [100]/[110]) | item (2) | section 2 |
| C13 | `PY SP/a8/a8_mutate.py --files=<structure, geometric, pipeline oxide tests> M0 M2 M3 M4c M6 M9 M10 M11` -> `mut_batch1.out`, `mut/*.log` | item (3) mutations (copies without git) | section 3.3 |
| C14 | `SP/a8/run_mut2.sh` (`a8_mutate.py M0 M6` on all oxide files; `a8_mutate.py --files=tests/forward/test_oxide_multislice.py M1 M4 M4b M5 M5b M7 M8 M12 M13`; copies made throw-away git repositories) -> `mut_batch2a.out`, `mut_batch2b.out` | item (3) | section 3.3 |
| C15 | `git -C SP/a8/base_54de605 init` + commit (throw-away, scratch only); `PY SP/a8/a8_bitid_pipe.py <base> <npz>`; `PY SP/a8/a8_bitid_compare.py bitid_base_merged.npz bitid_wt.npz` -> `a8_bitid_compare.out` | item (6) | section 6 |
| C16 | `PY SP/a8/a8_smoke_d.py 0 3000` -> `a8_smoke_d.out` | item (5) | section 5 |
| C17 | `PY SP/a8/a8_flat_c.py 3000 6000` -> `a8_flat_c.out` | item (4) | section 4 |
| C18 | `PY SP/a8/a8_smoke_d2.py 0` -> `a8_smoke_d2.out`, `smoke2_*.npz` | item (5), read-out | section 5 |
| C19 | WT: `PY -m pytest -q -p no:cacheprovider` (full suite) -> `SP/a8/pytest_full.txt` | full suite | section 11 |

## 1. Physics of the layer (item 1)

Traced in code (not in comments):

* Profile. `overlayer.py:194-204` builds `(V_ox + i V'_ox) [E(x; x_t, w_v) - E(x; x_i, w_i)]` (+ the
  a-Si term) per terrace from that terrace's own recorded stack (`t["oxide"]`, cell frame, written by
  `cell.py:137` / `cell.py:303`). x is the outward normal (x_t > x_i), so the bracket is 1 inside the
  layer and 0 above and below it. CONFIRMED.
* Region. Terraces along y: each terrace's profile weighted by its cell-averaged y fraction
  (`overlayer.py:239-247`); along z: one (nx, 1) profile per terrace weighted by the slice overlap
  with the terrace's z range, clipped to the crystal's z range (`overlayer.py:234-265`); the
  entrance vacuum carries nothing. Follows the surface (not a planar mask): CONFIRMED by the test
  `test_layer_follows_the_surface_not_a_planar_mask` and by mutation M4b (section 3.4).
* Edge. `edge_profile` (`overlayer.py:62-69`) = `erfc((x - x0)/(sqrt(2) w))/2`, i.e. an erf whose
  gradient is a Gaussian of s.d. w (E9's definition); point-sampled at pixel centres; w = 0 is the
  cell-averaged pixel fraction (ContinuumTerracePotential's convention). w_v >= 0.5 A enforced
  (`oxide.py:183-197`); smaller only with the TEST_ONLY flag. dx <= w asserted before any run
  (`overlayer.py:149-153`); the claimed first alias exp(-2 pi^2 (w/dx)^2) = 2.67e-9 at dx = w is
  correct. The layer's internal angles enter the band assertion (`engine.py:239-242`; mutation M12
  in section 3.4). CONFIRMED.
* Sign and magnitude of V'. The engine transmits `exp(i sigma V_proj)` (`engine.py:199`) with
  `V_proj = sum_g (V + iV') w_g`, so the amplitude decays as exp(-sigma V' path): absorption, not
  gain. Intensity exp(-2 sigma V' L) = exp(-L/Lambda) gives V' = 1/(2 sigma Lambda): with
  sigma = 7.2884010e-4 rad/(V A) (C5), Lambda = 1780 / 1705 A -> 0.3854 / 0.4024 V (E9 out:19-20
  reproduced). The geometric engine uses Im k'_perp from the complex relativistic Delta
  (`refraction.py:145-169`); C5: exp(-2 Im k' t) = 0.52130 for 0.40 V, 2 nm, identical to the
  refracted-path form exp(-sigma V' 2t/sin theta_in) = 0.52131. CONFIRMED.
* Mean inner potential. `mean_inner_potential_V` stays the crystal's (`overlayer.py:121-122`); the
  pipeline's MIP check and the glancing angle are unchanged (B32). CONFIRMED.

## 2. Geometry (item 2)

* f. C5 recomputes rho_Si = 2.32919 g/cm^3 (a = 5.4309 A) and f(2.20) = 0.441507 from the stated
  molar masses (`constants.py:38-44`); code `oxide.py:255-264` implements the same formula. f t for
  2.0 / 1.5 nm = 8.8301 / 6.6226 A (E9 out:143) CONFIRMED.
* Consumed-layer rule. `oxide.py:295-303`: |N a/4 - (f t + t_a)| <= a/8, refused otherwise with the
  nearest count named. CONFIRMED. BUT the 2.0 nm stand-in sits on the rounding boundary: f t/(a/4) =
  6.5036 layers, 0.0036 layers (0.005 A) from 6.5; N flips from 7 to 6 at rho = 2.19877 g/cm^3
  (-5.6e-4 relative; C5). The parity of N is exactly what decides the <110> terrace type at a buried
  a/4 step (E9 section 3 item 2; verified on the atoms: N = 7 swaps both terraces, N = 6 keeps them,
  C12), so for the B41 2 nm case that parity is set by the fourth significant digit of an assumed
  density (finding A8-m4).
* Conformal definition: equal thickness AND equal count (`oxide.py:315-316`; `si001.py:878-879` per
  step). CONFIRMED (mutation M6 shows no test pins the count half; section 3.4).
* Buried step and terrace type: (o1)-(o4) measured on the kept atoms (`si001.py:827-918`); a/4 step,
  N = 7 at [100] and [110]: buried screw, both terraces' back-bond axes swapped; N = 6: not swapped
  (C12). One extra consumed layer turns an a/2 step into a buried a/4 and an a/4 step into a flat
  interface (test). CONFIRMED.
* a-Si placement: x_c = x_i - t_a, with the crystal density (`oxide.py:304-307`); the count rule
  includes t_a. CONFIRMED (potential construction tested; propagation NOT RUN by E4 or A8).
* Per-terrace overrides: honoured by `terrace_stacks`, refused by the pipeline. CONFIRMED.
* Registry of the continuum layer against the ATOMISTIC crystal (finding A8-M2): the reference
  plane H is the top ATOMIC plane (`oxide.py:40-43`), so x_i = H - f t, while an atomistic crystal
  whose top N layers are removed extends to its equivalent boundary H - N a/4 + a/8 (half a layer
  above its top atomic plane; measured +0.74 A for the Kirkland IAM, C9). The layer therefore
  OVERLAPS the kept crystal by f t + t_a - N a/4 + a/8, which the count rule bounds to [0, a/4]
  (not to [-a/8, a/8], as the recorded `interface_quantisation_A` suggests). C9, engine potential,
  laterally averaged:

      t 20 A, N 7, 2.200 g/cm^3: overlap +0.005 A; max V near the top atom 25.2 V
      t 15 A, N 5, 2.200 g/cm^3: overlap +0.513 A; max V 28.1 V
      t 20 A, N 6, 2.198 g/cm^3: overlap +1.355 A; max V 33.7 V

  The overlap does not change a conformal step phase (common to every terrace) and the B41
  multislice variant (2 nm) happens to have 0.005 A, but for any other thickness the layer and its
  vacuum edge sit up to one layer spacing too low relative to the crystal, the top Si layer is
  immersed in the oxide potential, and the geometric engine (interface at x_i) and the multislice
  (atoms end at H - N a/4) describe different interfaces. Fix: take the pre-oxidation surface of an
  atomistic terrace at H + a/8 (or assert the overlap, not |N a/4 - f t|, against a stated bound)
  and record the true registry.

## 3. Analytic checks and test tolerances (item 3)

### 3.1 Independent recomputation (C5, C6; first principles, CODATA 2018)

| quantity | A8 | E9 line / E4 | verdict |
|---|---|---|---|
| lambda, k, sigma, k_perp (16.1347 mrad) | 0.02507934 A, 250.5323, 7.2884010e-4, 4.04209 | out:6-11 | CONFIRMED |
| k'_perp(10.34 V) | 4.484934 | out:36 4.48493 | CONFIRMED |
| conformal a/4, a/2 | 10.97609, 21.95218 rad | out:91 10.9761, 21.9522 | CONFIRMED |
| top-surface rate 2(k' - k) | 0.88569 rad/A | out:98 0.8857 | CONFIRMED |
| grown rate 2k' - 2k(1 - f) | 4.454915 (f exact), 4.454855 (f = 0.4415) rad/A | out:113 4.45486 | CONFIRMED |
| one consumed layer | q/f = 3.07520 A; 13.69977 rad (also by direct construction -2k dx_t + 2k'(dx_t - dx_i)) | out:123 3.0753, 13.6998 | CONFIRMED |
| zero-loss amplitude, 2 nm, 0.40 V | 0.52130 (intensity 0.2718) | E4 0.5213 | CONFIRMED |
| same, 0.3854 V (1780 A) | intensity 0.2850 | out:57 | CONFIRMED |
| Fresnel r, vacuum/10.34 V, 16.1347 mrad | -0.051934, abs r^2 2.69718e-3 | out:234, 284 | CONFIRMED |
| E4's "analytic 2.67299e-3 at the central bin" | is the Fresnel value at 16.1751 mrad (the grid's central incident bin), not a discrepancy | E4 4(a) | CONFIRMED |
| E4's sharp-edge multislice 2.65300e-3 | = 2.67297e-3 x (1 - 2 x 0.0038): the cell-averaging bias -((q1 + q2) dx)^2/12 of the rung-1 model; residual 5.9e-5 in amplitude | E4 4(a) | CONFIRMED |
| graded w = 0.1 A (exact 1-D transfer matrix, C6, converged in step 0.004-0.001 A and span) | abs r^2 1.3064e-3 at 16.1347 mrad; 1.2905e-3 at 16.1751 mrad | E9 Born formula 1.3036e-3; E9 1-D multislice 1.3067e-3 (out:285); E4 engine 1.29044e-3 | engine = exact to 5e-5 relative |
| graded w = 0.5 A (C6) | abs r^2 1.9545e-9 at 16.1347 mrad; 1.8345e-9 at 16.1751 mrad; suppression of abs r 8.5e-4 | E9 out:241 Born 1.129e-4 (abs r^2 3.44e-11); E4 engine 1.835e-9, called "the numerical floor" | E9's factor is 57x too small in intensity; the engine is RIGHT (finding A8-m1) |

Finding A8-m1 (MINOR, documentation and interpretation): the erf-edge suppression exp(-(q w)^2/2)
(E9 out:236-241) is the first Born approximation. It is accurate at w = 0.1 A (0.2 %) but not at
0.5 A, where the exact 1-D reflectivity of the same profile is 57-58 times larger in intensity
(abs r = 4.4e-5, a suppression of 8.5e-4 rather than 1.1e-4). E4's multislice value at w = 0.5 A
(1.835e-9 at its central bin) agrees with the exact value (1.8345e-9) to four digits, so it is not
"the numerical floor" (E4 section 4(a)) but a validation of the engine that E4 did not claim. The
1.1e-4 figure is quoted as fact in `oxide.py:31-33`, in the refusal message `oxide.py:196`
("0.5 A suppresses |r| by 1.1e-4"), in `forward/geometric/model.py:50` ("w >= 0.5 A: |r|
suppressed by 1.1e-4") and in the test print (`test_oxide_multislice.py:85-86`, "analytic
exp(-(q w)^2) = 1.17e-08"). The M4 conclusion stands (abs r^2 ~ 2e-9 is ~1e-7 of the crystal's
reflectivity), and the test threshold (1e-3) is met by a factor 1400. Fix: quote the exact value
or state "Born estimate".

## 7. Pipeline gate (item 7; C10, in-memory copies of `configs/demo_smoke_si001.yaml`)

    [REFUSED ] comparison + oxide_2p0nm: ... demo stand-in (..., B41) ...
    [REFUSED ] comparison + multislice_tiny_oxide_2p0nm: frozen_phonons 'none' ...; the demo list incl. B41 (E4 test)
    [REFUSED ] variant replaces lattice_parameter with a TEST_ONLY record (allow_test_only False): ConfigError ... TEST_ONLY values are accepted only from in-memory test fixtures
    [ACCEPTED] same, allow_test_only=True -> cfg.test_only = True (then refused by any comparison run)
    [REFUSED ] variant adds an unknown CFG-B parameter: ConfigError: CFG-B: unknown parameter 'made_up_parameter'
    [REFUSED ] variant sets cfg_b.glancing_angle_ext: ... declared once, in sections.illumination.glancing_angle (item 7)
    [REFUSED ] B41 as the assumption_id of mean_inner_potential_V: ... 'B41' is not mapped to PROJECT_INPUT item 20
    [ACCEPTED] B41 with overlayer 'none'
    [ACCEPTED] B41 with t 50 A, N 16, V' 0.1 V (not the B41 row's values)
    [ACCEPTED] interface_width_A = 0 (sharp interface) under B41
    [ACCEPTED] V_imag_V given as the string '0.4'
    [REFUSED ] PROJECT_INPUT oxide, a-Si 0 (measured), V' 0.40, purpose comparison: ... amorphous_si_thickness_A = 0 (the optimistic bound, E9 M5) must carry the label ASSUMPTION (or TEST_ONLY in tests)
    without 'overlayer' (or 'termination') in the item-12 value: load ACCEPTED, build_structure REFUSED ("must state {termination, overlayer}")
    sha256_resolved differs between oxide_2p0nm and oxide_1p5nm: True

* No silent default reaches an engine: every oxide key is required (`config.py:976-983`), the fixed
  choices (no overrides, no sharp-edge flag) are stated, and a missing `overlayer`/`termination` key
  passes the load-level gate (`config.py:910` and `:1049` use `.get(..., "none"/"bulk")`,
  pre-existing) but is refused by `engines.build_structure` (`engines.py:91`) before any
  engine. CONFIRMED (NIT: the refusal comes after load).
* Comparison runs refuse B41 (registry `demo_only`, and item 12 is in `BLOCKING_ITEMS`,
  `config.py:72`). CONFIRMED; mutation M10 shows the refusal test fails without the registry entry.
* Variant CFG-B records pass the same CFG-B gate (`load_config_dict` after
  `resolve_variant_cfg_b`, `config.py:729-732`): TEST_ONLY, unknown parameters, a second glancing
  angle and a stand-in id on the wrong item are refused; the resolved record is hashed
  (`sha256_resolved`). No smuggling path found. CONFIRMED.
* Finding A8-M1 (MAJOR): a measured item-12 record cannot state "no amorphous Si".
  `oxide_spec_from_config` gives every oxide parameter the ONE qualified label of the record
  (`config.py:985-988`), and `validate_spec` refuses t_a = 0 unless its label starts with
  ASSUMPTION/TEST_ONLY (`oxide.py:199-202`). Item 12 is blocking, so a comparison run needs a
  PROJECT_INPUT record, and then t_a = 0 is always refused (probe above). E9 M5 explicitly allows
  0 nm when the final milling step was a low-energy polish, i.e. a witness measurement may well
  report none; the only way through would be to invent a non-zero a-Si layer (with invented
  potentials and a different consumed-layer count). E4's test
  `test_zero_absorption_or_a_si_under_project_input_needs_assumption` pins this behaviour (its
  body only exercises V' = 0). Fix: per-parameter labels in the item-12 record (as the spec
  already supports), or accept a PROJECT_INPUT zero that states its detection limit.
* Finding A8-m2 (MINOR): a stand-in id vouches for values its row does not state. B41 with
  `overlayer: none`, with t = 50 A / V' = 0.1 V, or with a sharp oxide/Si interface is accepted
  (probes above); only the reverse contradiction (B26 with an oxide, `config.py:1016-1020`) is
  refused. Compare the convergence gate, which refuses a stand-in whose row contradicts the value
  in both directions (`CONVERGENCE_STAND_IN_ZERO`). Fix: refuse B41 with "none", and check the B41
  values against the row (or make the row say "any values; demo").
* Finding A8-n1 (NIT): numeric oxide values given as strings ("0.4") are accepted (`oxide.py:126-139`
  converts with float()); the spec then carries the string (and hashes it).

## 8. B41 row, registry and code (item 8)

`docs/model_assumptions.md:67` (B41) against `configs/demo_smoke_si001.yaml:534-755`,
`io/assumption_registry.yaml:52,56` and the code:

| B41 statement | code / configuration | verdict |
|---|---|---|
| t_ox 2.0 nm in oxide_2p0nm, oxide_2p0nm_no_absorption, multislice_tiny_oxide_2p0nm; 1.5 nm in oxide_1p5nm(_no_absorption) | thickness_A 20.0 / 15.0 in exactly those variants | AGREE |
| 2.20 g/cm^3, f = 0.4415 | density_g_cm3 2.20; f computed 0.441507 | AGREE |
| consumed layers 7 (5), nearest count of 6.50 (4.88) | consumed_layers 7 / 5; asserted by oxide.py:295-303 | AGREE (6.504 is 0.004 layer from the rounding boundary: A8-m4) |
| V_ox 10.34 V; V'_ox 0.40 V or 0 V | V_real_V 10.34; V_imag_V 0.4 / 0.0 | AGREE |
| vacuum edge and interface graded 0.5 A (erf, Gaussian gradient s.d. 0.5 A) | vacuum_edge_width_A 0.5, interface_width_A 0.5; erfc(x/(sqrt2 w))/2 | AGREE (the cited line 241 is E9's Born value; A8-m1) |
| a-Si 0 nm, optimistic bound, with its label | amorphous_si_thickness_A 0.0 under "ASSUMPTION B41 (stands in for PROJECT_INPUT item 12)"; validate_spec requires an ASSUMPTION/TEST_ONLY label for 0 | AGREE |
| variants only, base keeps B26; comparison refuses it | base record B26 `overlayer: none`; registry `B41: [12]`, B41 in `demo_only` | AGREE (C10) |
| conformal: step phases unchanged; 4.27-4.71 / 0.87-0.98 rad/A; 13.70 rad per layer | geometric engine terms; C5 | AGREE |
| "Not represented: elastic diffuse scattering, charging, carbon, transition layer, TDS in the layer" | `oxide.py:73-76` NOT_REPRESENTED | AGREE |

B4 row (`model_assumptions.md:30`), B7 (:33), B12 (:38) agree with the code (conformal a/4 at <100>
accepted, at <110> refused with the parity note; per-terrace overrides in the engines, refused by
the pipeline). NIT A8-n2: the buried-step record at <100> carries `buried_b4 = B4_A4_100`
(`si001.py:382-386`), whose text says B4 "does not apply to ... an overlayer", next to
`model_assumption_B4_overlayer` saying the conformal layer preserves it (C12 output); the geometric
engine accepts the step on the first string. The two texts contradict each other in every
oxide run's metadata.

## 9. Tests changed between 685e434 and 83fa75f (item 9)

`git diff --stat 685e434 83fa75f -- tests/`: five new files (oxide_cases.py, test_oxide_multislice.py,
test_oxide_geometric.py, test_oxide_pipeline.py, test_oxide_structure.py) and one modified file,
`tests/io/test_io_config_stand_ins.py` (+5/-1: B41 added to the expected registry and to
`demo_only`; nothing removed or loosened). `git diff --diff-filter=M --name-only` lists only that
file; no conftest changed. No existing test or tolerance weakened: CONFIRMED.

## 10. Memory model and the layer arrays (item 10; C11)

tracemalloc peak of `run_realisation` (numpy backend, geometry assertions bypassed exactly as
`tests/forward/test_memory_model.py` does, after a warm-up) against `engine.memory_model`:

    terraces along y, complex64,  no layer: 672 x 504, measured - model = +0.1 B/px
    terraces along y, complex64,  layer:    840 x 504, measured - model = +8.1 B/px  (+1.01 cb)
    terraces along y, complex128, layer:    840 x 504, measured - model = +16.1 B/px (+1.00 cb)
    terraces along z, complex64 / complex128, layer: +0.1 / +0.2 B/px (the (nx, 1) arrays)

So the omission is exactly one working-precision complex array per pixel for terraces along y
(steps parallel to the beam) and negligible for terraces along z, as E4 states
(`overlayer.py:226-229`). Scaled to the H2 production cells
(`docs/agent_reports/H2_realistic_supercell_sizing.md:64-65`), complex64: single a/4 step parallel
to the beam, 0.1 deg miscut, 2000 x 12096 px: +0.194 GB against a modelled 4.096 GB (+4.7 %; +7.4 %
of the 2.602 GB device part on cupy); r = 0.05, 2700 x 12096: +0.26 GB against 5.8 GB (+4.5 %).
The half-torus cells (feature path) refuse the oxide. On cupy the layer is built on the host in
complex128 (`overlayer.py:240-247`: one 16 B/px array plus one 16 B/px product temporary) before
the transfer, a host transient of about 32 B/px (0.77 GB for the 0.1 deg cell) that the cupy host
model does not include either (code reading; not measured, no GPU). Finding A8-m3 (MINOR): add
cb px (terraces along y) to `memory_model` when the potential is a ContinuumOxidePotential and
32 B/px to the cupy host realise phase; the HPC kit's memory requests inherit the omission.

### Finding A8-m5 (MINOR): the oxide/Si transition is not required to be graded

E9 M4's required addition reads "the continuum layer's vacuum edge AND oxide/Si transition are
graded over at least 0.5 A". The code enforces the minimum only for the vacuum edge
(`oxide.py:180-197`); `interface_width_A` accepts 0 (sharp, cell-averaged) or any value in (0, 0.5)
with any label (`oxide.py:198`), and the pipeline accepts `interface_width_A: 0.0` under B41 (C10).
A sharp oxide/Si step at 10.34/13.90 V reflects abs r^2 = 2.5e-4 (E9 out:234, C5 r = -0.01567),
which is common-mode for a conformal layer but, at [110] where the attenuated crystal reflectivity
is about 9e-5 (E9 out:247), would dominate the specular beam; with an atomistic crystal the sharp
step sits at x_i, up to a/4 away from the atoms (section 2). Fix: enforce >= 0.5 A for the interface
too (flag + TEST_ONLY below), or record why a sharp interface is acceptable.

### 3.2 Are the tolerances a priori and meaningful?

* Structure and geometric tests compare with E9 lines at their printed precision (plus the stated
  f-rounding bound); the geometric engine's own terms are pinned by the finite-difference tests at
  1e-9 against `oxide_phase_rates`, which is pinned to E9. A priori and meaningful.
* Multislice (a): sharp edge |err - model| <= 3.5e-3 and phase <= 1e-3 rad are the rung-1
  tolerances (a priori); measured 5.9e-5 and 6e-5 rad. w = 0.1 A within 1 % of the Born factor:
  the engine is within 0.11 % of Born and 0.005 % of the exact 1-D value (C6), so the budget holds
  with a factor 9. w = 0.5 A: ratio <= 1e-3; measured 6.9e-7 (a factor 1400 margin); the test
  cannot distinguish w = 0.35 A from 0.5 A, but the w = 0.1 A test pins the width convention
  (mutation M5b).
* Multislice (c) and (d) assert no physics (E9 M1; smoke). The absorption magnitude in the layer is
  pinned only by the potential-construction test (imaginary part = 0.40 V at rtol 1e-9), not by any
  propagated run.

### 3.3 Mutation tests (C13, C14: `PY SP/a8/a8_mutate.py [--files=...] <names>`; each mutation
applied to a scratch copy of WT made into a throw-away git repository, never to WT; the flat (c)
and smoke (d) tests deselected; control M0 = no mutation: 125 passed)

| mutation | what | result | caught by |
|---|---|---|---|
| M1 | V'_ox sign flipped in the multislice layer (gain) | 2 failed | test_layer_follows_the_surface..., test_amorphous_si_layer... |
| M2 | V'_ox sign flipped in k'_perp (geometric) | 3 failed | conformal a/4, a/2 (amplitude > 1), zero-loss 0.2850 (got 3.51) |
| M3 | f = 0 in the stack (non-consuming layer) | 12 failed | E9 stack/count tests, builder, engine differentials, multislice dry run |
| M4 | layer mirrored below the interface | 5 failed | all three edge tests, surface-following, a-Si |
| M4b | planar mask (terrace 0's layer everywhere) | 1 failed | test_layer_follows_the_surface_not_a_planar_mask |
| M4c | sign of the top-surface term | 5 failed | conformal (amplitude), differentials, zero loss |
| M5 | edges never graded | 2 failed | w = 0.1 A and w = 0.5 A tests |
| M5b | erfc(x/w)/2 instead of erfc(x/(sqrt2 w))/2 | 1 failed | w = 0.1 A test only |
| M6 | conformal = equal thickness only | 0 failed | none (benign: with the nearest-count rule equal thickness implies equal count except at an exact tie) |
| M7 | layer in the entrance vacuum | 1 failed | surface-following test (W[:10] = 0) |
| M8 | V'_ox dropped in the multislice | 2 failed | potential-construction tests |
| M9 | count rule relaxed to +-1.5 layers | 2 failed | refusal tests (structure, pipeline) |
| M10 | B41 removed from `demo_only` | 0 failed | none (benign: item 12 is blocking, so any ASSUMPTION for it is refused in comparison runs and the message still names B41) |
| M11 | variant CFG-B records ignored | 8 failed | every B41 variant test |
| M12 | layer angles not in the band assertion | 1 failed | test_setup_records_what_the_layer_changes |
| M13 | overlayer build-up assertion ignores the stack | 0 failed | none: no test builds a cell that is too short for the layer (finding A8-m6, MINOR) |

(The first batch ran in copies without git; the pipeline end-to-end test then failed on the git
preflight in every copy including the control. Those rows count only the other failures; the
second batch, with git, confirms the control and M6.)

The four breakages the task names (wrong sign of V'_ox, f = 0, layer on the wrong side, edge not
graded) each fail at least one test: CONFIRMED. Finding A8-m6 (MINOR): the new docs/05 4.3
assertion `item4_buildup_length_through_overlayer` (`cell.py:408-419`) has no refusal test; a
version that ignores the stack passes the whole oxide suite.

## 6. Bit-identity without an overlayer (item 6; C8, C15)

`SP/a8/a8_bitid.py` run on a `git archive` of 54de605 (E4's starting commit) and on WT, every case
without an overlayer: rung 1 (continuum, flat), rung 3 (continuum a/4 step), rung 2 (periodic
continuum, r = 0.1), the atomistic smoke ([110], a/2, Kirkland), the null-test translation pair A
and B (M2 cell, [110]) and the null-test [100] step case, the builder positions and metadata and
the reflection cells for [100]/[110] x parallel/transverse x bulk/p(2x1)s, the geometric engine at
[100], and the pipeline arrays (arrays.npz) of the base demo (geometric) and `multislice_tiny`
(the pipeline part for 54de605 run from a throw-away git repository of the archive, because the
multislice manifest refuses a tree without git; C15 `a8_bitid_pipe.py`). Result
(`SP/a8/a8_bitid_compare.out`):

    arrays: 76 vs 76; same keys: True
    arrays bitwise identical: 74 of 76  (the other two, trace_source_z_A of both pipeline runs,
                                         contain NaN; their bytes are identical)
    metadata entries equal: 26 of 26  (exit-wave, builder and cell metadata, timing and
                                       package_version removed)

CONFIRMED: without a layer nothing changes, including the null-test cases.

## 5. The smoke result (d): +1.878 rad against the geometric +1.590 rad (item 5; C16, C18)

Same helpers as E4 (`tests/forward/oxide_cases.atomistic_case`: [100], a/4 step, parallel edges, two
terraces 4 periods = 21.7 A wide, Kirkland, r = 0.1; `length_for_oxide` so that every run has the
SAME box, grid and length), read-out as the E4 test (aperture 0.5 1/A, central halves). Deviation
= Delta_phi - (-2 k_perp a/4, wrapped = +1.5902 rad):

| cell length | layer 0.40 V | layer 0 V | clean, beam 2 A above the crystal | clean, beam launched at the oxide runs' height |
|---|---|---|---|---|
| 2577 A (E4's) | +0.2881 (amp 0.124/0.100) | +0.1900 (0.227/0.207) | -0.7350 (0.557/0.671) | -0.3760 (0.209/0.238) |
| 5575 A (+3000) | -0.5081 (0.500/0.571) | -0.5475 (0.958/1.063) | -0.5010 (0.843/0.961) | -0.5396 (0.865/0.975) |

* E4's number is reproduced exactly (+1.8784 rad, +0.2881).
* At E4's length the result is not a property of the layer: the clean crystal in the same box
  deviates by -0.74 rad (-0.38 rad with the same launch height), and the value moves by 0.8 rad
  when the cell is 3000 A longer. At 5575 A all four runs agree within 0.05 rad (-0.50 to
  -0.55 rad): the conformal layer changes the a/4 step phase by at most about 0.05 rad there,
  consistent with E9 section 3 item 1. The common -0.5 rad is the clean crystal's own
  finite-cell / narrow-terrace deviation (the atomistic fixed-beam gate has not passed; "as
  without a layer", as E4 says).
* The read-out at 2577 A is also ill-conditioned (C18, `a8_smoke_regions*.out`): inside the
  central half of one 21.7 A terrace the per-column specular component varies in amplitude by a
  factor 3-9 and in phase by 104-234 deg (layer: 155 and 234 deg; clean: 104 and 134 deg); moving the region boundary by one pixel column changes the deviation from
  +0.2881 to +0.2538 rad, margins 0.20-0.40 W give +0.17 to +0.31 rad (layer) and -0.09 to
  -0.63 rad (clean); aperture 0.03 1/A gives +0.90 rad.
* Ruled out as causes: the layer's own reflection (|r| = 4.4e-5 at w = 0.5 A, section 3.1, against
  a crystal amplitude of 0.1-1: at most 5e-4 rad) and the moved interface (common to both
  terraces for a conformal layer; the buried relations are asserted on the atoms, C12).
* The absorption-only amplitude ratio at 5575 A is 0.500/0.958 = 0.522 and 0.571/1.063 = 0.537
  (model 0.521).

Verdict: the 0.288 rad is a build-up (cell-length) and narrow-terrace artefact of the short cell,
shared with the layer-free crystal, not an effect of the layer. E4 was right not to interpret it;
its report should state the layer-free deviation in the same box (-0.74 rad) next to it.
