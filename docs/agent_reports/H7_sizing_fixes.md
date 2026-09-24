# H7: code fixes after the H5 review of the H2 supercell sizing

Agent H7, 2026-09-23. Scope: apply `docs/agent_reports/H5_sizing_review.md` (H5) to the code: the
multislice engine (`reflection_holo/forward/multislice/`) and H2's sizing tool
(`tools/hpc/supercell_sizing.py`). H2's report stays unedited as the record; the corrected numbers
are printed by the corrected tool (`tools/hpc/supercell_sizing_output.txt`). Written incrementally:
finding -> fixed / declined -> file:line -> test. Nothing is committed or pushed by H7.

## Log

- start: read H5 (all), engine.py, grid.py, potentials.py, backend.py, propagator.py,
  illumination.py, forward/cell.py, pipeline/engines.py, pipeline/estimates.py, the sizing tool (all),
  H5's recompute script sections 8-12. Baselines before any edit (both in the scratchpad, not in
  the repository): `review_h5_recompute.py` report mode 13/13 checks, exit 0 (load 12-16 from
  other agents); `supercell_sizing.py` report mode 41/41 checks, exit 0.
- memory probes (scratchpad scripts, numpy backend, tracemalloc, run_realisation on short [100]
  strips of 576 x 84 and 576 x 2520 px, complex64 and complex128, r = 0 and 0.1, static and frozen
  phonons): the whole-run peak is reproduced by a phase model written from the code (below) to
  0.02-0.9 % once a warm-up run has absorbed first-call allocations (lazy imports; 4-7 MB on the
  first run in a process). realise() alone: 112 B/atom from the code plus the f2 grid (8 B/px) and
  F still alive, 71,319 k vs 71,333 k B measured (624 000 atoms). H5's 118 B/atom (static) was
  measured on the first call in its process; the frozen value (113) and my warm static and frozen
  values (113.5 including the f2 grid) agree: static and frozen are the same.

## 1. M4: estimate_resources and the complex128 temporaries (FIXED)

Finding (H5 M4): `estimate_resources` counted Ex, Ey as 8 (nx + ny) n and no temporaries; the
structure-factor exponentials of `_RealisedAtomic.projected` (potentials.py:302-303) are formed in
complex128 (argument 16 B + result 16 B per element) before the cast.

Fix: `reflection_holo/forward/multislice/engine.py:403-521` `memory_model(...)` (new, public,
exported) and `estimate_resources` (engine.py:524-) now use it. The model follows the engine's
statements phase by phase (numpy semantics: a binary operator reuses a temporary operand of the
result dtype, ufunc calls and `astype` allocate) and takes the maximum:

* setup: propagator kernels computed in complex128 on the host (58 B/px while P(dz/2) is built);
  entrance wave in complex128 before the cast;
* realise: scattering factors (f2 grid + F in float64, 16 B/px) and the atom sorting and records
  (112 B/atom from the code: sorted copy 40 + unsorted copy 24 + idx, order, offsets 24 + three
  float64 temporaries of the boundary count 24; the f2 grid is still alive);
* slice loop, largest slice: residents 3 cb + rb + rb n_species B/px (+1 B/px boolean mask on the
  host) + max(5 cb px, 3 cb px + max(32 nx n, cb nx n + 32 ny n, cb (nx + ny) n + (3 cb + rb) px))
  (psi, t_bl and t of the previous slice stay alive while the next potential is built; the
  potential construction itself: the two exponential stages of H5, and the pixel stage of acc,
  ifft, V, V (1 + i r) and its astype copy);
* after the loop: the exit-wave copy.

`memory_bytes["total"]` (the key every caller reads) is now the numpy-backend peak of one
realisation including the cell's own atom arrays (32 B/atom); new keys `device_peak_cupy`,
`host_peak_cupy` and the full `model` (phases, residents, largest-slice terms, per-atom bytes);
`gpu.memory_bytes` is the cupy device peak (same statements; UNVERIFIED on a GPU and a lower bound:
cuFFT/cuBLAS workspaces and the cupy pool are not included). The physical absorption is assumed
non-zero (the larger code path; r = 0 needs one complex array less), stated in the model.
The numerics of the potential are unchanged (potentials.py not edited).

Test: `tests/forward/test_memory_model.py` (8 tests, pass). tracemalloc peak of a real
`run_realisation` (numpy backend, after a warm-up run in the process) against the estimate minus
the pre-existing cell arrays; stated tolerance 2 % of the model (the size of the O(nx + ny +
n_slices) arrays and Python objects the model leaves out). The reflection-geometry assertions are
bypassed with monkeypatch in this file only, explicitly (the cells are 2-3 periods long); the band
assertion runs. Measured / model:

| cell | grid | n per slice | measured B | model B | ratio | engine before H7 |
|---|---|---|---|---|---|---|
| narrow, complex64, r = 0.1 | 576 x 84 | 28 | 4,295,096 | 4,279,540 | 1.0036 | 3,647,040 (x1.18 under) |
| narrow, complex128, r = 0.1 | 576 x 84 | 28 | 8,509,336 | 8,491,636 | 1.0021 | |
| narrow, complex64, frozen phonons | 576 x 84 | 28 | 4,339,157 | 4,279,540 | 1.0139 | |
| wide, complex64, r = 0.1 (exponentials dominate) | 432 x 2520 | 840 | 133,010,481 | 132,997,024 | 1.0001 | 98,530,560 (x1.35 under) |
| narrow, complex64, r = 0 | 576 x 84 | 28 | 3,908,856 | 4,279,540 | 0.9134 = model minus one complex array (tested) | |

Also tested: realise() alone on 53 k atoms (peak and kept bytes, 2 %), the memory_model contract.

Cheap memory reduction without numerical change (PROPOSED, NOT APPLIED): in
`_RealisedAtomic.projected`, build Ex and Ey in blocks of rows into a preallocated array of the
working precision, `Ey[j0:j1] = xp.exp(-2j*np.pi*(fy64[j0:j1, None]*pos[None, :, 1])).astype(c)`.
Every element is computed by the same float64/complex128 operations, so the result is bit-identical;
the transient falls from 32 ny n (+8 nx n) to 32 B x block x n. For the 2a_a2 row (ny = 24 000,
n = 15 211) that is 11.7 GB -> 0.5 GB at 1024 rows per block. Chunking over atoms instead would
change the GEMM summation order (not bit-identical). The `astype` copy in `projected` for r > 0
(`(V * (1 + 1j r)).astype(c)` where the product already has dtype c) could be `astype(c, copy=False)`,
also bit-identical, saving cb B/px.

For the Alliance kit (H6, not edited by me): `--need-gpu-mem-gb` must be taken from
`memory_bytes["device_peak_cupy"]` (or `gpu.memory_bytes`) of the dry run after this change, with a
margin for cuFFT/cuBLAS workspaces and the pool (not modelled, no GPU here); `total` is the
numpy/CPU host peak.

## 2. N8: the band limit must carry the working reflection (FIXED)

Finding (H2 N8, H5 A7): `check_band` asserted the beam angles only and passed pixels up to 0.450 A,
while the (0,0,8) coupling needs f_max = 1/(3 dx) >= |g_008| = 8/a = 1.4731 1/A, dx <= a/24 =
0.2263 A.

Fix:
* `reflection_holo/forward/multislice/grid.py:141-204` `check_band(..., reflections_per_A)`: new
  REQUIRED argument (name -> (g_x, g_y) in cycles/A; an empty mapping only for a structureless
  cell); asserts (g_x/fx_max)^2 + (g_y/fy_max)^2 <= 1 for each (the elliptic aperture applied to
  the transmission function) and raises `SamplingError` naming the reflection, its vector, the
  band, the derived pixels and the pixel needed along each axis ("dx <= 0.2263 A" for (0,0,8));
  records `working_reflections` in the band record (ExitWave metadata). Module docstring updated.
* `engine.py:89` `MultisliceParams.working_reflections_hkl` (new required field, no default):
  PROJECT_INPUT item 9, integer (h, k, l) of the cubic crystal frame; required non-empty for an
  atomic cell, `()` for a continuum cell (no reciprocal lattice; a non-empty value is refused).
  `engine.py:119-164` `working_reflection_vectors(cell, hkls)` maps g = hkl/a onto the cell axes
  with the frame the structure builder records (`metadata["structure"]["frame"]`, both
  `si001` and `features` builders); `reflection_setup` (engine.py:201-210) passes (g_x, g_y) to
  `check_band` and records g_z. Exported from the package.
* `reflection_holo/pipeline/engines.py:328-331`: the adapter passes the configuration's declared
  target reflection, `cfg.cfg_b.value("target_reflection_hkl")` (item 9; `value()` already refuses
  an absent or null one), so a pipeline run can never fall back to a default.
* `reflection_holo/pipeline/__main__.py`: the dry run also prints the cupy device and host peaks.

Tests: `tests/forward/test_band_working_reflection.py` (10 tests, pass): 0.13 A passes and records
fraction 0.5745; 0.25 A is refused for (0,0,8) while the beam angles alone pass; edge exactly at
a/24; elliptic aperture with (0,+-4,4); argument required; engine level (`reflection_setup` on an
atomic [110] cell): 0.13 A passes and records g = (8/a, 0, 0), 0.25 A raises `SamplingError`,
missing field -> TypeError, `()` for an atomic cell -> ValueError naming item 9, malformed
declarations refused; crystal-frame mapping at [110] ((1,-1,1) -> (1/a, sqrt2/a, 0), (2,-2,0) ->
(0, 2 sqrt2/a, 0), (1,1,1) -> g_z = sqrt2/a); continuum cell takes `()` only.

Audit of every grid against the new assertion (no assertion loosened):

| where | grid | result |
|---|---|---|
| configs/demo_hpc_si001.yaml (multislice) | dx 0.1900, dy 0.2011 A | passes, (0,0,8) at 0.84 of the band (pipeline dry-run run here: geometry and band checks pass; exit 4 only because cupy is absent, as before) |
| configs/demo_smoke_si001.yaml, variant multislice_tiny | dx 0.1961, dy 0.2263 A | passes, 0.87 of the band (dry-run exit 0) |
| other configs (cfg_a/b/o, demo_smoke_si001 default, torus demos) | geometric engine or CFG definitions | not applicable |
| scripts/hpc/null_test_study/study.yaml (17 points, via null_test_cases._params) | dx, dy <= 0.13 A by construction | passes; declares ((0,0,8),) (B17) |
| scripts/torus/run_torus_multislice.py | <= 0.13 A | passes; the CASE now declares `working_reflection_hkl` (0,0,8) once, labelled ASSUMPTION B17, used for the angle and the assertion |
| tests/forward smoke_case, null_test_cases, test_engine_contract phonon case, test_memory_model | <= 0.13 A (0.1324 A for the contract case) | pass; declare ((0,0,8),) |
| tests/forward ladder_cases (rungs 1, 3), test_engine_contract `_fast` | continuum cells | declare `()` (no lattice) |
| tests/forward/test_vacuum_propagation (check_band direct) | vacuum, no crystal | `reflections_per_A={}` stated in the test |
| tests/forward/test_potential_atomic | builds Grid objects for the potential only (no check_band, no run) | unaffected |

No existing test or physics grid is too coarse; no test needed an explicit coarse-grid exemption.
Other agents' files that construct `MultisliceParams` (not edited by me): S5 has meanwhile adapted
`tools/validation/rheed_solver_compare.py:535-540` (passes ((0,0,8),) when the field exists; its grid
is 0.13 A, so the assertion passes). `tools/hpc/review_h5_recompute.py` (H5's record script) now
stops with `TypeError: missing ... 'working_reflections_hkl'` in report-mode section 12 and in the
--rerun/--memtime modes, and its section-12 checks compare against the pre-H7 memory accounting:
it is a record of commit 47256f3 and needs its own update before it is run again (finding for the
orchestrator; its baseline run before my edits was 13/13, exit 0).
`tools/physics_checks/rung2_reference.py` (P2) builds grids only and is unaffected; the Alliance
kit's `gpu_check.py` takes its cases from ladder_cases/null_test_cases and is covered.

## 3. The sizing tool (`tools/hpc/supercell_sizing.py`)

Every change is labelled in the tool's docstring and output; H2's JSON data files
(`supercell_sizing_measurements.json`, `supercell_sizing_cpu_calibration.json`) are records and
were not edited (their labels are read and relabelled in the output).

| H5 finding | status | where (tool) | self-check (new or changed) |
|---|---|---|---|
| M1 "MEASURED_HERE" | FIXED: engine outputs labelled "REPRODUCED: computed with the UNVALIDATED engine"; calibration "timed here (4 shared cores)"; writers of new files use the new labels | docstring; section 7 header and file-label note; section 12 calibration line; `measure()`, `calibrate()` | (output text) |
| M2 amplitude tolerance 3e-2 unlabelled | FIXED: `RUNIN_AMP_TOL = 1e-2` with label (null-test criterion) printed in section 8; H2's 3e-2 value still printed for comparison | constants; section 8 | `runin_static_null_test_criterion` (3000 / 5000 / 9000 A), `H5_tolerance_row_2a_a4_miscut0.1_r0.10` (z 6101.6 A, 33,899,040 atoms, 2160 x 12096, H5's numbers) |
| M3 static-lattice run-ins | FIXED: `h5_fp_analysis` reads H5's 6000 A frozen-phonon strip (`review_h5_rerun.json`, sha256 printed); r = 0.1 production run-in 3500 A (ensemble phase), flagged "ensemble amplitude within 1e-2 not established on the strip (lower bound)"; r = 0.05 and r = 0 production rows flagged "static-lattice LOWER BOUND, phonon run-in to be computed on the cluster"; the static V row keeps the static 3000 A; section 10 quotes 0.766 / -0.083 rad (H2's 0.721 / -0.046 marked transient) | sections 7, 8, 10, 13, 14 | `h5_fp_ratio_phase`, `h5_fp_runin`, `runin_phonon_r010` |
| M4 memory | FIXED: `memory_row` calls `engine.memory_model` (no replica); per row GPU device peak (cupy), host of a GPU run and CPU-job peak, both with the 48 B/atom builder structure; host bytes per atom 32 + 112 + 48 = 192 B from the model, H5's measured 193 / 198 printed | sections 12-14 | `tool_equals_engine_and_M2_on_17_study_points` (memory and device peak equal estimate_resources; grid, slices, atoms, GPU s equal M2), `layout_formulas_vs_built_100_cell` (+ device peak), `host_per_atom_vs_H5`, `device_peak_ge_H5_model_<row>` (11 rows) |
| m1 resolution element, terrace widths | FIXED: 6.0/sin(theta_ext) = 371.884 A (1/tan 371.836 printed as the exit-plane mapping; both angles: 364.22 A at the B19 angle); "built as N periods" printed per miscut | sections 1, 8 | `res_element_H5`; `T2_res_element` now with 1/sin (364.22 vs 364) |
| m2 Bethe fractions | FIXED: cut-off scan c = 12/16/20/24; section 9 quotes "at least" the largest (3.2e-2 V_g at 0.13 A, 6.7e-3 / 1.0e-2 V_g at 0.10 A) | sections 4, 9 | `bethe_not_converged_H5_m2` |
| m4 r = 0 caveat | FIXED: printed with the r = 0 run-in and in the row note | sections 8, 13 | |
| m5 u label | FIXED: `U_RMS_LABEL` (Prismatic example value, not sourced, no model_assumptions row yet); the proposed B35 row is a docs/ change for the orchestrator | constants, sections 2, 7, 10 | |
| m6 torus flat reference | FIXED (note in row 3, as H5 proposed) | section 13 | |
| m7 [110] six times | FIXED: amplitude ratio 6.27, intensity 39 printed | section 7 | |
| m8 x1.5 unlabelled | FIXED: `CPU_FACTOR` with its ASSUMPTION label in every row and the table | constants, sections 12-14 | |
| m9 lateral buffer | FIXED: absorption-only bounds printed; "W_min about 177-239 A at r = 0.1 (estimate; run order step 5 decides)" | section 8 | |
| m3, n1-n5 | DECLINED for the tool: wording of H2's report (not edited, it is the record) or no tool output involved; n1 (vacuum 177-402 A) is printed per row | | |
| H2 N8 text in section 9 | updated: the engine now asserts the declared working reflection | section 9 | |

New consequence printed by the tool (finding for the orchestrator): with the phonon run-in
3500 A, W_min becomes 177.3 A, so the 0.5 deg miscut row (a/4 terraces of 157.5 A) has NO converged
measuring window (flagged in the row and the table); the W_min row itself becomes 179.2 A wide.

Run: `venv/bin/python tools/hpc/supercell_sizing.py` (report mode; the --measure mode was not
needed: the phonon data are H5's) -> 60/60 checks pass, exit 0, 58 s, full output saved to
`tools/hpc/supercell_sizing_output.txt` (sha256 at this run: tool fb9103d7...aafc190d, output
dd0b839c...ad68a6720c; the output contains the load average and git state of the run).

Corrected scenario table printed by the tool (section 14 of the output):

Run-in per row: r = 0.10 rows with phonons 3500 A (frozen-phonon ensemble phase run-in, amplitude not established); r = 0.05 and r = 0 rows: static-lattice LOWER BOUNDS (phonon run-in to be computed on the cluster); V row: static run-in. Memory: engine.memory_model; GPU device peak UNVERIFIED on a GPU (lower bound); host and CPU-job figures include the 48 B/atom builder structure. CPU: CPU x1.5 (ASSUMPTION: empirical factor, M2 and H2 strips, H5 wide-slice probe; for an unloaded node, H5 m8).
| scenario | extents x, y, z (A) | atoms | grid | slices | run-in (A) | GPU device peak (GB) | host, GPU run (GB) | CPU job peak (GB) | CPU time per realisation (4 cores, x1.5) | GPU time per realisation (ASSUMPTION model) | realisations x angles | total CPU / GPU |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 study.yaml, 17 points ([110], reference) | 83-405 x 7.7-245.8 x 1377-21377 | 19,224 to 2,971,136 | see section 12 | 1434 to 22266 | per point | <= 0.227 | | <= 0.527 | 119 min (sum) | 114 s (sum) | 1 x 1 (translation points 2 runs) | 119 min / 114 s |
| 2a_a4_miscut0.1_r0.10 | 291 x 1564 x 6601 | 36,681,120 | 2250x12096 | 4862 | 3500 (phonon phase; amplitude not established) | 4.62 | 7.3 | 9.0 | 21.9 h | 17 min | 8 x 1 | 7.3 d / 2.3 h |
| 2a_a4_miscut0.5_r0.10 (W < W_min: no converged window) | 291 x 315 x 6601 | 7,387,170 | 2250x2430 | 4862 | 3500 (phonon phase; amplitude not established) | 0.52 | 1.5 | 1.6 | 94 min | 74 s | 8 x 1 | 12.5 h / 10 min |
| 2a_a4_miscut0.1_r0.05 | 350 x 1564 x 8100 | 51,031,008 | 2700x12096 | 5966 | 5000 (static lower bound) | 5.36 | 10.1 | 11.5 | 33.6 h | 28 min | 8 x 1 | 11.2 d / 3.7 h |
| 2a_a2_miscut0.1_r0.10 | 292 x 3117 x 6601 | 73,803,772 | 2250x24000 | 4862 | 3500 (phonon phase; amplitude not established) | 14.98 | 14.7 | 23.9 | 3.3 d | 61 min | 8 x 1 | 26.2 d / 8.1 h |
| 2a_a4_Wmin_r0.10 | 291 x 358 x 6601 | 8,406,090 | 2250x2800 | 4862 | 3500 (phonon phase; amplitude not established) | 0.60 | 1.7 | 1.9 | 114 min | 91 s | 8 x 1 | 15.3 h / 12 min |
| 2a_a4_miscut0.1_r0.00 | 479 x 1564 x 12103 | 76,289,472 | 3750x12096 | 8914 | 9000 (static lower bound) | 6.14 | 15.1 | 16.5 | 2.6 d | 58 min | 8 x 1 | 21.1 d / 7.7 h |
| 2b_a2_transverse_r0.10 | 393 x 87 x 9746 | 3,016,960 | 3024x672 | 7178 | 3500 (phonon phase; amplitude not established) | 0.18 | 0.6 | 0.7 | 33 min | 27 s | 8 x 1 | 4.4 h / 4 min |
| 2b_a4_transverse_r0.10 | 390 x 87 x 9659 | 2,972,768 | 3024x672 | 7114 | 3500 (phonon phase; amplitude not established) | 0.18 | 0.6 | 0.7 | 33 min | 26 s | 8 x 1 | 4.4 h / 4 min |
| 3_torus_R1000_r20_r0.10 | 454 x 2221 x 10425 | 105,260,269 | 3500x17150 | 7678 | 3500 (phonon phase; amplitude not established) | 11.73 | 20.8 | 24.4 | 4.5 d | 98 min | 8 x 1 | 36.3 d / 13.1 h |
| 3_torus_R1000_r20_r0.05 | 512 x 2276 x 11924 | 136,189,483 | 3969x17640 | 8782 | 5000 (static lower bound) | 13.52 | 26.8 | 29.9 | 6.5 d | 2.4 h | 8 x 1 | 52.1 d / 19.4 h |
| V_rocking_flat_strip_r0.10 | 275 x 11 x 6102 | 233,168 | 2160x84 | 4494 | 3000 | 0.02 | 0.0 | 0.1 | 88 s | 1 s | 1 x 19 | 28 min / 26 s |
| 4 patterned CFG-B feature | BLOCKED on PROJECT_INPUT item 13 | | | | | | | | | | | |
GPU instances: rows whose device peak exceeds 10 GB (a 1g.10gb / 2g.10gb MIG instance is too small even before the library workspaces): ['2a_a2_miscut0.1_r0.10', '3_torus_R1000_r20_r0.10', '3_torus_R1000_r20_r0.05']


Self-checks: 41 before, 60 after. One check was replaced, not weakened:
`replica_equals_engine_and_M2_on_17_study_points` compared the tool's memory with M2's printed MB,
which used the pre-H7 accounting that M4 corrects; `tool_equals_engine_and_M2_on_17_study_points`
still requires grid, slices, atoms and GPU seconds equal to M2's printout and the memory (numpy peak
and device peak) equal to the engine's `estimate_resources`. `T2_res_element` now uses 1/sin
(364.22 A vs T2's 364 A, same 0.5 A tolerance).

## 4. Other H5 items and what they need from others

* H5 D.9 / M4 consequence for the Alliance kit (H6's files, not edited): `--need-gpu-mem-gb` should
  come from `memory_bytes["device_peak_cupy"]` of the dry run (now printed by the pipeline's
  dry-run and by `run_study.py --estimate`) plus a margin for cuFFT/cuBLAS workspaces and the cupy
  pool; README_ALLIANCE's "192-240 B per atom" becomes 192 B/atom (32 cell + 112 realise + 48
  builder structure; H5 measured 193). By the tool's table the 2a_a2 row (15.0 GB) and both torus
  rows (11.7, 13.5 GB) need more than a 10 GB MIG instance.
* H5 m5 (a model_assumptions row for u = 0.076 A), D.1-D.8 (docs/05, docs/03, M2 wording), m3 and
  the nits: documentation, outside my scope (docs/ not edited); the tool prints the corrected
  numbers they need.
* `scripts/hpc/null_test_study/run_study.py`: its `--estimate` line said "engine arrays"; it now
  prints the numpy peak and the GPU device peak (lower bound).

## 5. Tests run (verbatim counts)

Machine shared with other agents throughout (1-min load 14-22 on 4 cores: S5 engine runs, P2
rung-2 run, H6's gpu_sanity with this tool's --measure mode).

* `venv/bin/python -m pytest -q tests/forward/test_memory_model.py` -> `8 passed in 27.02s`
* `venv/bin/python -m pytest -q tests/forward/test_band_working_reflection.py` -> `10 passed in 5.40s`
* `venv/bin/python -m pytest -q tests/forward` -> `1 failed, 63 passed in 589.81s (0:09:49)`;
  the failure: `FAILED tests/forward/test_smoke_atomistic.py::test_smoke_atomistic_a2_step_0008`,
  `E       assert 155.22981277600047 < 120.0` (the test's wall-clock limit; "SMOKE: build 11.4 s,
  propagation 143.5 s, total 155.2 s, peak RSS 828 MB"; the geometry, band, finiteness and manifest
  assertions come after the timing assertion and were therefore not reached in this run).
* `venv/bin/python -m pytest -q tests/hpc` -> `109 passed, 5 skipped in 396.44s (0:06:36)`
  (`SKIPPED [5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed`)
* `venv/bin/python -m pytest -q` (full suite) -> `1 failed, 905 passed, 5 skipped, 12 warnings in
  1541.86s (0:25:41)`; the same single failure: `FAILED
  tests/forward/test_smoke_atomistic.py::test_smoke_atomistic_a2_step_0008`, `E       assert
  202.92326317900006 < 120.0` ("SMOKE: build 13.9 s, propagation 188.6 s, total 202.9 s, peak RSS
  836 MB"). The 120 s limit was not changed. My edits do not touch the propagation path
  (`propagate_slices`, the potential and the propagators are unchanged; the band assertion adds a
  loop over one reflection); see the timing comparison below.
* `venv/bin/python tools/hpc/supercell_sizing.py` -> 60/60 checks, exit 0 (section 3).
* Pipeline dry runs (section 2): demo_hpc_si001 exit 4 (cupy absent; geometry and band checks
  passed), demo_smoke_si001 --variant multislice_tiny exit 0.
* `run_study.py --estimate --only step_w32_bragg_abs10_L5k` -> "memory peak 527 MB (numpy/CPU; GPU
  device 227 MB, lower bound)" (the pre-H7 accounting printed 340 MB).
