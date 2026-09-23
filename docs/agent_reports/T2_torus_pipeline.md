# T2: half-torus surface feature (trench and ridge) through the pipeline, geometric engine

Status: COMPLETE, 2026-09-23. Agent T2. Written incrementally. Nothing committed or pushed by T2
(the orchestrator snapshotted work in progress as c544257 and d998030).
Branch `claude/electron-holography-orchestration-nakd7r`, HEAD `2f40c9a` at start.
Scratch directory `$S` = `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/torus`.

Scope (orchestrator task T2, second smoke test requested by Ali): the geometric engine for a general
height field h(y, z), the pipeline feature path (config `structure.feature`, height-map
quantification, profile cuts), the two demo configurations, plots, tests. Not touched:
`reflection_holo/structure/` (read only: `shapes.py` is the fixed shared definition),
`reflection_holo/forward/multislice/`, `docs/` other than this report.

Inputs read: `structure/shapes.py`; `forward/geometric/`; `pipeline/` (config, engines, run, quantify,
estimates, CLI); `quantification/shadow.py`, `height.py`, `controls.py`; `optics/` (darkfield,
projection, detector); `reconstruction/sideband.py`; `configs/demo_smoke_si001.yaml`;
`docs/agent_reports/P1_pipeline.md`, `S4_pipeline_fixes.md`; `docs/03` sections 2, 4, 6;
`docs/model_assumptions.md` B4, B9, B19-B32.

## Log

1. Physics expectations written down BEFORE any code or run (theta = 16.4743 mrad, B19;
   k = 250.53 /A; s = 2 k sin(theta) = 8.2543 rad/A; h_2pi = 0.7612 A; a/4 = 1.3577 A):
   * one a/4 step is s a/4 = 11.207 rad = 1.784 wraps; its wrapped phase is +1.359 rad, the phase of
     a -0.165 A step. A sharp a/4 step can therefore NOT be unwrapped from one hologram (docs/03
     section 4): Itoh unwrapping across it returns -0.165 A per +a/4 step. The torus top layer
     (`layer_height_A`, a/4 terraces) has 14 terraces on each ridge flank (crest n = +14, 19.01 A)
     and 15 levels on each trench flank (floor n = -15, -20.37 A: the exposed layer lies below
     -s; corrected after reading shapes.py again);
   * slopes: a facet tilted by beta across the beam deflects the specular beam by 2 sin(theta)
     tan(beta) = 0.033 tan(beta) (transverse), a tilt along the beam by 2 beta; the 3 mrad aperture
     (B22) passes |dh/dy| < 0.091 and |dh/dz| < 0.0015 only. The semicircular cross-section
     (r = 20 A) has |dh/dd| = |d|/sqrt(r^2 - d^2) < 0.091 only for |d| < 1.8 A;
   * terrace widths on the flanks: the top terrace is 12.4 A wide (|d| < 6.2 A), the next ones 3.2,
     2.2, ... A, the outermost 0.05 A: below the reconstruction resolution (~6 A image plane,
     carrier 2 A, mask |q_c|/3) everywhere except the crest/bottom terrace;
   * along the beam: the image coordinate is u = z sin(theta) - h cos(theta): the ring (2040 A of
     surface) is 33.6 A long in the image, and a point at height h is displaced by -h cos(theta)
     (-19 A for the crest), i.e. by as much as half the foreshortened ring. The ring cross-section
     (40 A) at the front and back arcs is 0.66 A in the image: UNRESOLVED (resolution ~364 A of
     surface along the beam);
   * shadows: 19 A casts h/tan(theta) = 1154 A (ridge: blocked strip in front of each arc, shadow
     behind it); a 19 A deep, 40 A wide trench crossing the beam is shadowed down to 0.66 A below the
     rim at most, i.e. almost entirely shadowed or blocked at the front and back arcs.
   Consequence expected before running: with one hologram the ring height is NOT measurable
   (aliased a/4 steps, slopes outside the aperture, unresolved terraces); the measurable height map
   is the flat surrounding surface; the ring is detected (amplitude, shadow and phase contrast) but
   not measured. The quantification must say so rather than return aliased heights.
2. Baseline before any change (HEAD 2f40c9a): `venv/bin/pytest -q`: `724 passed, 12 warnings in
   246.45s (0:04:06)`. Reference smoke run (`$S/smoke_before`, CLI exit 0): the S4 numbers
   (+2.7156 +- 0.0165, -1.3576 +- 0.0082, -1.3580 +- 0.0082 A; control delta -0.0036868859167245027
   rad), kept to check that the refactor of `pipeline/run.py` leaves the staircase path bit-identical.
3. Implemented `quantification/shadow.py` `height_field_corner_maxima` and `height_field_masks`
   (same conventions and 1e-9 A tolerance as `shadow_masks`; profiles "piecewise_constant" with
   vertical risers at cell boundaries, B13, and "piecewise_linear") and
   `forward/geometric/height_field.py` (HeightField, HeightFieldParams, the B4 scope check,
   `trace_height_field`, `height_field_exit_wave`). The exit-plane trace uses the running maxima of
   shadow.py for the illumination test and asserts visibility of every traced source. First check
   (`$S/check_tracer.py`, before any test file was written): the masks equal `shadow_masks` exactly
   for three step profiles (up, down, trench); the exit-plane trace of the built (0, 2, 1) staircase
   (60 periods, a/4 cells) equals `forward.geometric.trace_exit_points` (upstream "none") on all
   8002 exit points: identical status, source z difference 0.0.
4. Pipeline feature path implemented: `pipeline/config.py` (`structure.feature` record, item 13,
   kind "feature", exactly the keys {kind, sub_kind, center_y_A, center_z_A, major_radius_A,
   minor_radius_A}; exactly one of staircase / feature; `quantification.feature_processing`
   record, item 19, required with a feature; engine keys `field_length_A`, `surface_dz_A` on the
   feature path; `projection_reference: flat_surface`; `cfg_b.pattern_geometry` must be
   {features: half_torus, geometry: sections.structure.feature} with the SAME label and
   assumption_id; the multislice engine and the other path's settings are refused; B27, or B33 for
   a ridge / B34 for a trench, refused as the feature stand-in; list-inputs shows the absent
   staircase as "NOT USED on this path" with the reason), `pipeline/engines.py`
   (`feature_shape`, `feature_height_field`, `run_geometric_feature`), `pipeline/run.py` (stages
   4-10 factored into `_optics_stage`, `_hologram_stage`, `_reconstruction_stage`, shared by both
   paths; dispatch to `pipeline/feature.py`), `quantification/height_map.py`, `pipeline/feature.py`,
   `pipeline/estimates.py` (feature dry-run), CLI lines. Registry: B33, B34 -> item 13, demo_only.
   Refactor check: the smoke demo after the refactor gives all 26 arrays of `arrays.npz`
   bit-identical to `$S/smoke_before`; `summary.json` differs only in the two new "NOT USED on this
   path" input rows (feature, feature_processing).
5. First debug runs (`$S/debug_trench1`, `$S/debug_ridge1`; the final runs are below). One code
   error on the way: my assertion that the traced source height equals `layer_height_A` at the exact
   source point failed (`RuntimeError: traced source heights differ from layer_height_A at the
   source points`): by design the engine's cells put risers up to dz/2 from the true terrace
   boundary (B13), so a source near a boundary carries the cell-centre height. The assertion now
   checks the cell-centre sampling and the number of boundary-cell sources is recorded; comparisons
   use `layer_height_A` at the exact source point. Both debug runs matched the expectations of item
   1: trench interior essentially never imaged (62 lit footprint pixels of 1.47 M), ridge
   footprint 5110 lit pixels, none measurable.
6. Tests written (tolerances in the module docstrings, fixed before the runs):
   `tests/forward_geometric/test_height_field.py` (11), `tests/pipeline/test_pipeline_feature.py`
   (8). First run of the engine tests: `1 failed, 10 passed in 0.77s`, verbatim:
   `FAILED tests/forward_geometric/test_height_field.py::test_torus_ridge_and_trench_phases_have_opposite_signs`
   with `E           AssertionError: trench` / `E           assert np.int64(0) > 0`. Cause: my test
   geometry (ring sides at y = -50 and 250 A outside the 0-200 A exit columns, and a small trench
   fully shadowed: a floor is lit and visible only where the groove section along a column exceeds
   2 depth/tan(theta)). Fixed by the geometry (R = 20000 A, r = 3 A, side in the columns; section
   980 A against 494 A needed); no tolerance changed. Then `11 passed in 0.77s`; pipeline tests
   `8 passed in 6.05s` on the first run. Gentle bump (2 A, sigma_y 40 A, sigma_z 2500 A, 2.6
   wraps): 100 % of the 57 412 core pixels measurable, rms error 0.0023 A, max |error| 0.67 (+) and
   0.77 (-) sigma_h, peak +1.9945 / -1.9944 A against +-2.0 A, control passes.
7. Final runs through the CLI (HEAD d998030 plus this agent's uncommitted changes; the manifests
   record `dirty: true`, the diff hash and the package-tree hash):

       venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_smoke_torus_trench.yaml
       venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_smoke_torus_ridge.yaml
       venv/bin/python -m reflection_holo.pipeline run --config configs/demo_smoke_torus_trench.yaml --out $S/geo_trench
       venv/bin/python -m reflection_holo.pipeline run --config configs/demo_smoke_torus_ridge.yaml --out $S/geo_ridge
       venv/bin/python tools/plots/torus_geometric.py --run-dir $S/geo_trench --out $S/figures/geo_trench.png
       venv/bin/python tools/plots/torus_geometric.py --run-dir $S/geo_ridge --out $S/figures/geo_ridge.png

   Dry-run (0.27 s each, exit 0): exit plane [876, 4800] (trench) and [870, 4800] (ridge) px,
   9600 A along the beam, memory ~1.8 GiB, ~17 s estimated. Runs: exit 0, 25.8 s (trench) and
   22.5 s (ridge) wall; summary timings 22.6 s and 20.2 s (engine 5.9 / 4.9 s, optics 5.0 s,
   holograms 3.7 / 3.1 s, reconstruction 1.1 s, quantification 1.2 s, outputs 5.6 / 4.8 s).
   Outputs 92 MB and 83 MB. CLI output: `$S/geo_{trench,ridge}_cli.txt`.

## Results (geometric model, one plane-wave hologram, (0,0,8) at 16.4743 mrad, 200 keV)

Field: ring R = 1000 A, r = 20 A at (y, z) = (1199.75, 4800) A; detector 320 x 4608 px of 0.5 A
(160 A along the beam in the image plane = the whole 9600 A field, 2304 A across it = 2R + 2r plus
132 A each side). Reconstruction resolution 6.0 A (image plane) = 364 A of surface along the beam.
Measured per-pixel phase scatter on the flat surface 0.0055 rad (trench) and 0.0051 rad (ridge)
(predicted 0.0039 x sqrt(2) = 0.0055 rad); height noise 0.0006-0.0007 A per pixel.

| | trench | ridge |
|---|---|---|
| detector pixels imaging a lit surface point | 1 439 318 | 942 630 |
| of which on the ring footprint | 62 | 5 110 |
| ray-trace status: shadow / riser face | 32 / 16 778 | 217 560 / 295 938 |
| surface area shadowed / blocked (surface map) | 1.09 % / 1.09 % | 19.5 % / 19.5 % |
| MEASURABLE pixels (height returned) | 587 362 (39.8 %) | 275 290 (18.7 %) |
| measurable pixels on the ring footprint | **0 of 62** | **0 of 5 110** |
| footprint reasons | hidden strip 2, margin 24, not connected 36 | weak/invalid 2 217, hidden strip 2 238, model step 8, not connected 647 |
| no-step control (flat reference) | PASS, delta 4.8e-5 rad, tol 8.8e-4 rad | PASS, delta 2.4e-4 rad, tol 1.2e-3 rad |
| y cut at z_c (sides of the ring): measurable / px, on footprint | 384 / 4450, 0 of 2 | 382 / 630, 0 of 102 |
| y cut rms vs layer_height_A / continuous_height_A | 0.0006 / 0.0006 A (flat pixels only) | 0.0006 / 0.0006 A (flat only) |
| z cut at y_c (front and back arcs): measurable / px, on footprint | 104 / 320, 0 of 0 | 30 / 320, 0 of 0 |
| z cut rms vs layer / continuous | 0.0008 / 0.0008 A (flat only) | 0.0011 / 0.0011 A (flat only) |

What is resolved and what is not (summary.json `quantification.resolution`, printed by the CLI):
* along the beam the ring cross-section (40 A) is 0.110 resolution elements (364 A of surface
  each): the ring FRONT AND BACK ARCS ARE UNRESOLVED (the z cut has no footprint pixel at all:
  the trench arcs image as a 1-2 row riser line, the ridge arcs as a crest line followed by a
  1154 A shadow);
* across the beam at the sides the cross-section is 6.7 resolution elements, but every a/4
  terrace of the flanks is narrower than the resolution except the crest (ridge) or bottom
  (trench) terrace, 12.4 A; one a/4 step is 1.784 wraps (its wrapped phase is that of a -0.165 A
  step), so no path from the flat surface onto the ring can be unwrapped (docs/03 section 4);
* the aperture (B22) passes surface slopes |dh/dy| < 0.091 and |dh/dz| < 0.0015 only;
* the image coordinate is u = z sin(theta) - h cos(theta): the crest (19.0 A) is displaced 38 rows
  upstream, the trench floor (-20.4 A) 41 rows downstream, comparable to the 67-row image of the
  whole ring;
* TRENCH: the interior is almost never imaged: a floor point is lit and visible only where the
  groove section along a column exceeds 2 depth/tan(theta) (2400 A for 20 A), whereas the ring
  gives at most 4 sqrt(R r) = 566 A; backward rays over the downstream rim meet the riser faces of
  the upstream wall. The trench shows as a thin dark ellipse; the inner flat region is not
  connected to the outer one by reliable pixels (198 658 px "not connected") and lies within the
  three-resolution margin anyway;
* RIDGE: the interior of the ring is entirely shadowed or blocked (the 1154 A strips of the two
  arcs overlap, 2R = 2000 A < 2308 A); the lit footprint pixels (crest lines) are isolated from the
  flat reference; none is at least half a resolution element from an unreliable pixel, so not
  even the modulo-h_2pi check of the phase could be made there.

Conclusion: in the geometric model the half torus (R 1000 A, r 20 A) is DETECTED (shadow, riser and
amplitude contrast, footprint position across the beam) but its height is NOT MEASURABLE from one
hologram at this condition, for either version. The measurable height map is the flat surrounding
surface (rms 0.0006-0.0011 A against the built 0). The machinery measures a surface that is
resolvable: the gentle bump test (item 6) recovers 2 A (2.6 wraps) to 0.0023 A rms with both signs.

Figures: `$S/figures/geo_trench.png`, `$S/figures/geo_ridge.png` (object hologram whole and zoom;
wrapped phase, twilight; height map and unwrapped phase of every reliable region, RdBu centred on
0; reliability-map reason codes and ray-trace status; surface-plane shadow / blocked map; y cuts
whole and at the ring side, z cut, against layer_height_A and continuous_height_A).

## Files

New: `reflection_holo/forward/geometric/height_field.py` (height-field engine),
`reflection_holo/quantification/height_map.py` (reliability map, unwrapping, height map),
`reflection_holo/pipeline/feature.py` (feature path, cuts, resolution record, outputs),
`configs/demo_smoke_torus_trench.yaml`, `configs/demo_smoke_torus_ridge.yaml`,
`tools/plots/torus_geometric.py`, `tests/forward_geometric/test_height_field.py` (11 tests),
`tests/pipeline/test_pipeline_feature.py` (8 tests).
Modified: `reflection_holo/quantification/shadow.py` (height-field masks appended; `shadow_masks`
unchanged), `reflection_holo/pipeline/{config,engines,run,estimates,__main__}.py`,
`reflection_holo/io/assumption_registry.yaml` (B33, B34 -> item 13, demo_only).
Not touched: `reflection_holo/structure/` (shapes.py read only), `reflection_holo/forward/multislice/`,
docs other than this report, tests/io.

## Tests

`venv/bin/pytest -q` (full suite, after all changes; `$S/final_pytest.txt`), verbatim summary:

    FAILED tests/io/test_io_config_stand_ins.py::test_registry_is_package_data_mapping_ids_to_items
    FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
    2 failed, 777 passed, 12 warnings in 250.41s (0:04:10)

with `E         Left contains 2 more items:` / `E         {'B33': (13,), 'B34': (13,)}` and
`E           AssertionError: B33`. Both are the registry extension requested here: the orchestrator
adds rows B33 and B34 to docs/model_assumptions.md and B33, B34 to the expected registry of
tests/io/test_io_config_stand_ins.py (not my files; not edited). Every test written here passes
(19); after a last cleanup (unused import) the affected modules give `53 passed in 11.84s`.

## Proposed model_assumptions rows (the orchestrator adds them)

| ID | Assumption | Label | Status |
|---|---|---|---|
| B33 | Demo half-torus TRENCH (Ali's second smoke test): the lattice sites with x_rel <= 0 inside the lower half-torus are removed (`structure.shapes.HalfTorus`, kind "trench"); major radius, minor radius and centre per configuration (pipeline demo `configs/demo_smoke_torus_trench.yaml`: R = 1000 A, r = 20 A, centred in the field; atomistic cells of report T1: R = 50 A, r = 12 A), on an otherwise flat, step-free, bulk-terminated Si(001) surface (the miscut and terrace part of item 11 is not represented). The geometric engine uses the ideal top atomic layer `layer_height_A` (a/4 terraces), inside the B4 scope at the exact [100] azimuth (B20). Stands in for PROJECT_INPUT item 13 in the demo configurations only (purpose demo; a run with purpose "comparison" refuses every demo stand-in B19-B34, registry demo_only); not comparable to experiment. | ASSUMPTION | A feature of known shape for the second smoke test (size requested by Ali). Report T2: at the B19/B22 demo condition no height of the ring is measurable from one hologram. |
| B34 | Demo half-torus RIDGE: sites of the same continuous lattice with x_rel > 0 inside the upper half-torus are added (kind "ridge"); otherwise as B33. Stands in for PROJECT_INPUT item 13 in the demo configurations only; not comparable to experiment. | ASSUMPTION | As B33. |

B29 amendment (feature path, `sections.quantification.feature_processing`, same stand-in B29):
"Feature path (report T2): the height map is unwrapped only through pixels that pass the data
criteria (valid, relative amplitude >= 0.25, every wrapped 4-neighbour phase difference <= pi/2,
half the Itoh limit) and the model criteria of the ray-traced built geometry (lit source, built
phase difference < pi to every lit neighbour, no hidden strip between along-beam neighbours); the
zero is the median over the flat surface outside the feature, eroded by the three-resolution
margin, in the unwrap region holding most of it; a height is returned where the pixel lies in that
region and its margin box is entirely reliable; the 3-sigma no-step control on that flat reference
gates every height."

## Open points for the orchestrator

* Item 11 on the feature path: B33/B34 are registered for item 13 only, as instructed; the flat,
  step-free base surface is stated in their source text and list-inputs shows the staircase as
  "NOT USED on this path" with that reason. Registering B33/B34 for item 11 too, or a separate
  row, is your decision.
* `pipeline/config.py` refuses B27 (no feature), B33 for a ridge and B34 for a trench as the
  feature stand-in through a small table `FEATURE_STAND_IN_SUB_KIND`: the registry maps ids to
  items only. It could move into the registry.
* The model criteria of the reliability map use the built geometry (simulation-only, like the
  terrace regions of the staircase path); for experimental data a rocking series would be needed.
* Staircase path: stages 4-10 of `pipeline/run.py` were factored into shared helpers; the smoke
  demo arrays are bit-identical to those before the change.

## NOT RUN

* The feature path with the multislice engine (refused by the gate) and any comparison of these
  geometric exit waves with T1's atomistic multislice exit waves (different ring size; T1's waves
  are UNVALIDATED).
* Rocking series, convergent illumination, other azimuths (<110> a/4 terraces are refused), other
  reflections or apertures: the conditions under which the ring height might be measurable.
* The continuous (non-quantised) torus through the pipeline; a comparison-purpose run (only the
  gate refusal is tested); GPU/HPC runs.
