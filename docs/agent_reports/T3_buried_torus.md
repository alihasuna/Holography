# T3: buried torus void under an intact cap in Si(001), detectability by reflection multislice

Agent T3 (Ali's request, confirmed 2026-09-24). Branch claude/electron-holography-orchestration-nakd7r;
nothing committed or pushed by this agent. Beam energy 200 keV throughout (300 keV never used).
DEMO (stand-in B42, not comparable to experiment). Every multislice number below is UNVALIDATED and
measures DETECTABILITY only (phase and amplitude contrast of the specular beam against a flat
reference computed in the identical cell). The engine is not validated for step heights (the
atomistic fixed-beam null test has not passed). The reflection has not converged along z in a
1499 A crystal. The absorption is a TEST_ONLY stand-in or absent (B30).

## 0. Log (UTC)

- 08:12: read T1 report, shapes.py, features.py, feature_cell.py, the T1 runner and figure script,
  model_assumptions B20/B30/B32/B33/B34, P2 (2.4, 5.2, 6.5), E7 (M3, 3.7), H2 (2.4, 2.5, 3),
  physics_conventions. Machine idle at the start (load 0.1).
- 08:13: measured the builder at the needed depth: flat 74-layer full-size cell 1 102 896 atoms,
  26.8 s, peak RSS 2.66 GB (below the 3 GB limit; the peak is the builder's own checks).
- 08:15-08:22: BuriedTorus (shapes.py), builder branch and assertions (h), (i) (features.py),
  cell record and depth rule F5 (feature_cell.py), runner kinds "buried" and "buried_flat".
  Full-size cap-30 build: 1 095 865 atoms (7 031 removed), 27.1 s, peak RSS 2.63 GB. An
  estimate-only run passed every engine and feature check (section 3).
- 08:23: T1 tests still pass after the edits (36 passed). Runs started in two lanes (at most two
  engine processes, 2 FFT workers each).
- 08:25-08:40: registry B42, tests (structure 19, forward 14), analysis script.
- 08:40: CAUSALITY FINDING (section 4.1), derived before any run finished and then confirmed by the
  runs: in this cell most of the void's signal cannot reach the vacuum before the exit plane.
- 09:04: all 7 runs finished (rc = 0). 09:05-09:20: analysis, figures, full test suite.

## 1. Design

### 1.1 Shape (reflection_holo/structure/shapes.py, `BuriedTorus`)

A FULL torus-shaped empty cavity. Required fields, no defaults: center_y_A, center_z_A,
major_radius_A R, minor_radius_A r (0 < r < R), cap_A (> 0, finite, not bool), label, source. The
ring axis is along the surface normal. The ring centre (y_c, z_c) is as in the T1 half-torus demos:
(73.317, 1000.0) A. The tube centre line is the circle rho = R at x_rel = -(cap + r) below the top
atomic plane of the flat surface (x_rel = 0). Removed: lattice sites with
(rho - R)^2 + (x_rel + cap + r)^2 < r^2 (strict). Every removed site therefore has x_rel < -cap, so
the cap and the surface are untouched. `layer_height_A` and `continuous_height_A` return 0
everywhere. Volume 2 pi^2 R r^2 = 142 122 A^3; surface 4 pi^2 R r = 23 687 A^2. kind = "buried_void".

### 1.2 Builder (structure/features.py) and cell (forward/feature_cell.py)

`build_si001_with_feature(feature=BuriedTorus(...), ...)` keeps its signature (all arguments
required). It removes the void sites of the ONE continuous lattice; nothing is added or moved.
`build_si001_flat_reference` gives the flat reference: same lattice, origin, window and layers.
The half-torus paths are unchanged (T1's 36 tests pass).

`build_feature_reflection_cell` records the void in cell coordinates (void top/bottom, tube centre,
cap, intact cap layers). It refuses a void that reaches the bulk absorber. `check_feature_geometry`
adds F5 for buried voids (next section). F1-F4 are unchanged (F4 shadow length 0: the top is flat).

### 1.3 Depth rule F5 (stated and asserted; `check_buried_void_depth`)

Clean crystal, measured to the top of the bulk absorber:
- >= 65 A below the flat top plane. H2 2.4 measured that the exit-plane intensity falls below 1e-4
  at 53.2 A (r = 0.1) and 60.6 A (r = 0.05). H2 section 3 sets 55 A (r = 0.1) and 65 A (r = 0.05,
  also taken for r = 0). E7 M3 adopts >= 65 A for the atomistic null-study redesign. The larger
  value is used for both absorption settings.
- >= 30 A below the void bottom (x_rel = -(cap + 2 r)). The void bottom is a crystal surface where
  the wave that crossed the void re-enters the crystal. At r = 0.1 the exit-plane intensity below a
  [100] surface falls below 1e-2 at 26.0 A (H2 2.4). This keeps the absorber below the 1e-2
  intensity level of the wave arriving at the void bottom, which is itself attenuated over cap + 2r.

For r = 0, no depth converges outside the plateau (P2 6.5, E7 3.7). Those cells stay UNVALIDATED.
All runs use ONE cell: 74 layers, the smallest depth satisfying F5 for the deepest cap (30 A). The
runner asserts this at import. Clean depth (74 - 1) a/4 - 15 = 84.114 A >= max(65, 30 + 24 + 30 =
84) A. Clean crystal below the void bottom: 55.1 / 50.1 / 40.1 / 30.1 A for caps 5 / 10 / 20 /
30 (F5 records in the run summaries).

### 1.4 Runner (scripts/torus/run_torus_multislice.py)

New kinds "buried" (requires `--cap-A`) and "buried_flat". Both require `--absorption`
(`test_only_r0.1` or `none`) and an explicit `--max-cpu-seconds`: BURIED_CASE has no CPU default.
Each misplaced option is refused (tested). Run names are buried_cap<cap>A_<r010|r000> and
buried_flat_<r010|r000>. Structure files use the schema "T3 buried torus structure/1". The T1
kinds and their outputs are unchanged.

Absorption labels:
- r = 0.1: "TEST_ONLY: proportional absorption V_imag = 0.1 V_real, a numerical stand-in for
  PROJECT_INPUT item 21 (not supplied) in the T3 buried-void demo only (the value used by H2, P2
  and S5); not a sourced property of Si, not comparable to experiment (B30-style stand-in; H2 2.5:
  amplitude 1/e path 987 A)".
- r = 0: "ASSUMPTION B30".

Other settings: static lattice (ASSUMPTION), exact [100] (B20), 16.1347 mrad (B32, MIP 13.9028 V
asserted to 5e-4 V), 200 keV, complex128, numpy, 2 FFT workers. T1 used 4 workers; 2 lets two
processes share the 4 cores, and the environment variables are set to 2 (manifest thread check
"consistent").

## 2. Assertions (inside the builder; each tested on built and on corrupted structures)

(a) on-lattice and buried rule at every site. (b) window, no duplicates, count = flat - independent
enumeration. (c) minimum distance a sqrt(3)/4; atoms farther than r + 1.05 d_nn from the tube line
are 4-coordinated; EXACT bond bookkeeping for layers 1..l_s-1: coordination + removed neighbour
sites = 4. (d) removed count vs full-torus volume x density, |N - nV| <= n (a/8) 4 pi^2 R r
(relative a/(4r) = 11.3 %). (e) FLAT SURFACE UNTOUCHED: the top-layer height map of the built atoms
is 0 at every point of the ring box + 8 A, with no exclusion band. (f) void inside the cell, >= 4
intact layers below it. (g) frame. (h) VOID EMPTY: no atom within r of the tube centre line, from
the positions; the clearance is recorded. (i) CAP INTACT: every layer with x_rel >= -cap, and every
layer below the void, holds the flat per-layer count. Removed sites lie only in layers strictly
between the void top and bottom. With (a) and (b) this makes the cap identical to the flat build
atom for atom; tests compare the sets with `build_si001_flat_reference`.

Full-size numbers (n V = 7098.0, tolerance +-803.1):

| cap | removed | deviation | intact cap layers | clearance (h) | atoms with 1 / 2 / 3 missing bonds |
|---|---|---|---|---|---|
| 5 | 7166 | +68.0 | 4 | 1.7e-3 A | 1496 / 636 / 24 |
| 10 | 7083 | -15.0 | 8 | 1.2e-4 A | 1448 / 659 / 26 |
| 20 | 7123 | +25.0 | 15 | 7.9e-4 A | 1477 / 649 / 23 |
| 30 | 7031 | -67.0 | 23 | 3.0e-5 A | 1386 / 674 / 32 |

## 3. Cell and run log

Cell as T1 in y and z: 27 x 276 periods (146.63 x 1498.93 A), ring centre z = 1000 A, 1124 slices
of a/4, sheet beam H = 22 A 1 A above the surface. DEPTH FORCED ONE CHANGE: x box 169.11 A (T1
118.88 A), so the grid is 1323 x 1134 (dx 0.1278, dy 0.1293 A; T1 945 x 1134, dx 0.1258). All
engine checks passed: item 2 margin 60.0 > 46.63 A; footprint 1363 < 1499 A; build-up 1464 > 1083
A; clean 84.1 > 20 A. F1-F3 and F5 passed (F2: ring 779 A / 212 A inside the lit core).

`--max-cpu-seconds 3600` was passed explicitly for every run (calibrated estimates 571-1167 s).

| run | atoms | estimate (x1.5) | simulate | total | peak RSS | wall, load at start |
|---|---|---|---|---|---|---|
| buried_flat_r010 | 1 102 896 | 571 s | 480.3 s | 511.1 s | 2659 MB | 512 s, 0.7 |
| buried_cap5A_r010 | 1 095 730 | 613 s | 472.7 s | 502.2 s | 2631 MB | 503 s, 0.7 |
| buried_cap10A_r010 | 1 095 813 | 661 s | 620.1 s | 644.2 s | 2631 MB | 645 s, 3.4 |
| buried_cap20A_r010 | 1 095 773 | 675 s | 620.1 s | 648.7 s | 2631 MB | 650 s, 3.5 |
| buried_cap30A_r010 | 1 095 865 | 1167 s | 697.5 s | 727.1 s | 2631 MB | 728 s, 6.8 |
| buried_flat_r000 | 1 102 896 | 892 s | 647.8 s | 678.5 s | 2660 MB | 679 s, 6.8 |
| buried_cap10A_r000 | 1 095 813 | 619 s | 485.6 s | 516.2 s | 2631 MB | 517 s, 4.0 |

The peak RSS is the builder's; the engine phase ran at about 0.73 GB. Outputs are in
<scratch>/buried/ms_<tag>/: case, structure, summary, outputs/exit_waves, outputs/manifests. The
manifests record package versions, engine commit 39b6151 + dirty, repository commit + diff hash,
complex128, seed None (static), threads 2 "consistent", input sha256, case sha256 and
configuration_sha256.

Caveat: other agents' uncommitted edits (X4: engine.py, cell.py, ...) were in the working tree. The
diff hash is taken when the manifest is written, and it differs between runs (51b28fdb, 8281446,
2aaa02bd). Far from the void, cap 30 and its flat reference agree to 2e-5 of A_ref (C_up), so the
paired runs behaved identically there.

## 4. Results (tools/plots/buried_torus.py; output <scratch>/buried/figures/analysis_output.txt)

The analysis first asserts, from the files, that each cap run and its flat reference share grid,
plane, angle, cell, absorbers and absorption, and that flat atoms = cap atoms + void sites (passed
for all 5 pairs).

### 4.1 Where the signal can appear (causality; DERIVED_HERE, confirmed below)

The wave scattered at depth t travels up along the reflected characteristic (theta_int = 18.472
mrad). It reaches the surface only t / tan(theta_int) = 54.1 t downstream. In this cell the ring
is followed by only 437-561 A of crystal. The signal therefore reaches the vacuum before the exit
plane only for t < 8.1-10.4 A; deeper signal leaves through the END FACE, which has no experimental
counterpart.

The illumination has the same limit on the upstream side. The refracted beam enters at the first
contact z = 62.0 A (cell). By the ring it can have reached only 16.7-19.0 A deep, and 27.0 A by the
exit plane. The flat reference's exit-plane intensity accordingly drops below 1e-2 at 26.5 A (H2:
26.0 A), below 1e-4 at 37.3 A (H2, a 6000 A strip: 53.2 A).

The requested projected-ring region P (x_rel 7.05-9.05 A, +2.5 A) lies upstream of every causal
path. The analysis therefore also reports V (causal vacuum region), E (end-face band) and two
controls (C_up upstream, C_y lateral).

Measured location of |psi_s - psi_s,flat| (y-integrated peak / centroid vs characteristic
prediction for the tube centre):

| cap | peak | centroid | predicted | fraction in vacuum |
|---|---|---|---|---|
| 5 | -7.08 A | -8.57 A | -7.78 A | 0.14 |
| 10 | -11.94 A | -12.95 A | -12.78 A | 0.03 |
| 20 | -21.78 A | -21.30 A | -22.78 A | 0.04 |
| 30 | at floor | - | -32.78 A | - |

Cap 10 without absorption: -11.94 / -13.11 A. The engine carries the void's signal along the Bragg
characteristic, as predicted.

### 4.2 Signal table (printed verbatim; [value / larger control of the same run])

```
        cap       region    max|dphi|     rms dphi   max|rho-1|  max|dpsi|/A  rms|dpsi|/A
          5            P    2.711e-02 [  1.9]    6.547e-03 [  2.4]    2.778e-02 [  2.6]    3.264e-02 [  8.5]    7.501e-03 [  6.5]
          5            V    1.283e-01 [  8.8]    3.231e-02 [ 12.0]    9.808e-02 [  9.3]    1.201e-01 [ 31.4]    4.759e-02 [ 41.5]
          5            E    1.292e+00 [ 88.2]    3.968e-01 [147.9]    3.954e-01 [ 37.4]    1.580e-01 [ 41.3]    7.896e-02 [ 68.8]
          5         C_up    1.465e-02           2.683e-03           1.058e-02           3.826e-03           1.147e-03
          5          C_y    5.192e-03           1.093e-03           3.649e-03           2.107e-03           8.033e-04
         10            P    1.842e-03 [  0.4]    6.151e-04 [  0.7]    2.192e-03 [  0.6]    2.308e-03 [  2.3]    7.764e-04 [  2.0]
         10            V    6.337e-03 [  1.4]    3.079e-03 [  3.4]    8.243e-03 [  2.1]    8.095e-03 [  8.1]    3.501e-03 [  9.1]
         10            E    8.892e-01 [192.5]    2.061e-01 [225.3]    4.183e-01 [108.7]    7.736e-02 [ 76.9]    2.863e-02 [ 74.3]
         10         C_up    4.619e-03           9.146e-04           3.848e-03           1.005e-03           3.853e-04
         10          C_y    1.040e-03           1.883e-04           1.770e-03           7.354e-04           2.472e-04
         20            P    2.334e-04 [  0.9]    9.235e-05 [  1.7]    2.124e-04 [  1.1]    2.324e-04 [  2.8]    1.007e-04 [  2.5]
         20            V               empty               empty               empty               empty               empty
         20            E    5.101e-02 [199.4]    6.270e-03 [114.7]    8.761e-02 [463.0]    4.804e-03 [ 57.4]    1.129e-03 [ 27.7]
         20         C_up    2.558e-04           4.848e-05           1.892e-04           5.568e-05           1.721e-05
         20          C_y    1.470e-04           5.468e-05           1.892e-04           8.376e-05           4.077e-05
         30            P    1.268e-04 [  1.7]    6.149e-05 [  1.8]    1.710e-04 [  3.5]    1.600e-04 [  2.2]    8.887e-05 [  2.6]
         30            V               empty               empty               empty               empty               empty
         30            E    2.070e-04 [  2.7]    5.814e-05 [  1.7]    4.302e-04 [  8.8]    7.745e-05 [  1.1]    2.755e-05 [  0.8]
         30         C_up    4.230e-05           1.632e-05           2.484e-05           1.965e-05           6.815e-06
         30          C_y    7.630e-05           3.409e-05           4.871e-05           7.263e-05           3.452e-05
```

A_ref = max |psi_s,flat| over x_rel 0-25 A = 0.1783 (r = 0.1). The phase and the ratio mask pixels
below 5 % amplitude, which hides x_rel < -20 A. max|dpsi|/A needs no mask.

The FLOOR is not a noise floor: these simulations are noiseless. The controls hold leakage of the
Fourier aperture and of the band-limited propagation, and it scales with the signal (C_up 3.8e-3
for cap 5 down to 2.0e-5 for cap 30). The absolute detection limit needs the dose model: NOT RUN.

Reading, vacuum side (the only part with an experimental counterpart):
- Cap 5: detected in V: max|dphi| 0.128 rad, max|rho-1| 0.098 (9-12 x floor).
- Cap 10: marginal: rms dphi 3.1e-3 rad (3.4 x), max|dpsi|/A 8.1e-3 (8.1 x), max|dphi| 6.3e-3 rad
  (1.4 x).
- Caps 20 and 30: V is empty. Their signal cannot reach the vacuum in this cell.
- P detects nothing by phase or ratio at any cap (<= 2.6 x; 3.5 x at the 1.7e-4 level for cap 30).
  Its complex difference at cap 5 (8.5 x) is the tail of V inside P's 2.5 A dilation.

### 4.3 Decay with cap; comparison with the extinction depth

The fits S0 exp(-cap/L) use caps above 3 x floor:

| region | metric | L (A) |
|---|---|---|
| E (end face) | max\|dpsi\|/A | 4.18 +- 0.58 (caps 5-20) |
| E (end face) | rms\|dpsi\|/A | 3.46 +- 0.36 (caps 5-20) |
| E (end face) | max\|dphi\| | 4.43 +- 1.03 (caps 5-20) |
| E (end face) | rms dphi | 3.49 +- 0.66 (caps 5-20) |
| E (end face) | max\|rho-1\| | 3.69 +- 1.09 (caps 5-30) |
| V (vacuum) | max\|dpsi\|/A | 1.85 (caps 5, 10 only) |
| V (vacuum) | rms dphi | 2.13 (caps 5, 10 only) |

Pairwise L values are in the output file.

Compared quantity: the signal is a first-order change of the reflected AMPLITUDE. By reciprocity it
scales as psi(t)^2, so it decays with the INTENSITY depth of the Bragg wavefield. The two-beam
prediction is therefore L = Lambda/2 = 12.23 A (P2: amplitude extinction depth Lambda = G/|U_g| =
24.47 A).

The measured L is 3-7 x shorter, and it is NOT an extinction measurement:
- V is a cell-length cut-off (section 4.1).
- E is set by the illumination reach at the ring (16.7-19.0 A) and the TEST_ONLY absorption.
- The flat reference's own exit-plane intensity has local 1/e lengths of 9.2 A (10-20 A deep) and
  2.3 A (20-30 A).
A long-cell value of L is NOT RUN (section 7).

### 4.4 Absorption dependence (cap 10 A, each against its own flat)

| quantity | r = 0 | r = 0.1 |
|---|---|---|
| V max\|dpsi\|/A | 1.22e-2 | 8.09e-3 |
| V max\|dphi\| | 8.3e-3 rad | 6.3e-3 rad |
| E max\|dpsi\|/A | 0.127 | 0.077 |
| E max\|dphi\| | 1.02 rad | 0.89 rad |
| A_ref | 0.386 | 0.178 |

Without absorption the relative contrast is about 1.5 x larger. The r = 0 cells are UNVALIDATED at
any depth.

### 4.5 Geometric engine, and why the multislice sees below the surface

The geometric engine uses only the top-layer height. For the buried void, `layer_height_A` = 0 at
every exit-plane source point, so its prediction is phase 0 and amplitude ratio 1 (printed for all
5 runs).

The multislice sees the void for a different reason: the dynamical Bragg wavefield penetrates the
crystal. It is evanescent in the plateau (two-beam extinction depth 24.5 A), and the refracted
components are absorbed. The void removes potential and absorption where that field is non-zero.
The scattered wave travels along the reflected characteristic and leaves the surface t /
tan(theta_int) downstream of the void. In the exit plane that is a shift of about -0.87 t in
height.

## 5. Figures (<scratch>/buried/figures/)

- supercell_buried.png: y and z sections through the ring centre for all four caps (1:1). Shows
  removed sites, void outline, top plane, void top and the bulk-absorber top.
- signal_maps_r010.png: dphi, ratio - 1 and log |dpsi|/A_ref for each cap, with P, V, E and C_up
  outlined.
- signal_maps_cap10_absorption.png: cap 10 with r = 0.1 and r = 0.
- signal_vs_cap.png: metrics vs cap per region, 3 x floor, fits.
- depth_profile_flat_r010.png: exit-plane depth profile of the flat reference.

## 6. Registry B42 (proposed row for docs/model_assumptions.md, to be written by the orchestrator)

| B42 | Demo buried torus VOID (Ali's buried-cavity study, confirmed 2026-09-24): a full torus-shaped empty cavity inside Si(001), ring axis along the surface normal, major radius R = 50 A, tube radius r = 12 A, tube centre line at depth cap + r below the top atomic plane of the flat surface; every lattice site closer than r to the tube centre line is removed (`structure.shapes.BuriedTorus`, kind "buried_void"); caps (intact Si between the top atomic plane and the top of the void) 5, 10, 20 and 30 A; the flat surface and the cap untouched; otherwise as B33 (flat, step-free, bulk-terminated, exact [100] azimuth B20). Atomistic multislice demo of report T3 only (no pipeline configuration; the pipeline's feature path has no buried kind). Stands in for PROJECT_INPUT item 13 in demo runs only (registry demo_only; no laboratory counterpart); not comparable to experiment. | ASSUMPTION | A feature of known shape to test whether reflection holography sees below the surface. Report T3: in the 1499 A demo cell the specular signal reaches the vacuum only for the 5 A cap (the 10 A cap marginally); the rest leaves through the end face. |

Registered in reflection_holo/io/assumption_registry.yaml as `B42: [13]` + demo_only, following
B33/B34. tests/io was updated. `test_registry_ids_exist_in_model_assumptions` FAILS until the row is
in docs/model_assumptions.md.

GATE GAP, not fixed (pipeline/config.py belongs to X4). `FEATURE_STAND_IN_SUB_KIND` lacks B42. A
scratch check loaded configs/demo_smoke_torus_trench.yaml with assumption_id B42 on the feature
and on pattern_geometry: it was ACCEPTED. Proposed fix: add `"B42": "buried_void"`, so a B42 half
torus is refused, and a test.

## 7. Limitations and NOT RUN

- NOT RUN: vacuum-side detectability and L for caps >= 10 A. It needs about 2920 A of crystal
  before and after the ring (54 A / tan theta_int), beyond H2's 2500 A run-in. That is about
  6000 A of crystal and about 4.4 M atoms, and at 2.4 kB/atom the builder would peak at about
  10 GB, over the 3 GB per-process limit. It needs a memory-lean builder or a larger node.
- NOT RUN: convergence in pixel, slice, aperture, cell length and absorption value. NOT RUN:
  dose/noise, holograms and reconstruction.
- NOT RUN: frozen phonons, reconstruction, oxide, [110].
- NOT extended: the HPC kit (TORUS_KINDS) and the pipeline.
- The P, V and E regions and the 3 x floor rule are my definitions, stated in the script.

## 8. Tests (verbatim)

```
tests/structure/test_features_buried.py: 19 passed in 4.31s
tests/forward/test_feature_cell_buried.py: 14 passed in 6.58s
tests/structure: 383 passed in 36.04s
tests/forward/test_feature_cell.py + test_feature_cell_buried.py: 20 passed in 9.52s
tests/io: FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
          (AssertionError: B42) -- 1 failed, 127 passed in 1.30s
```
