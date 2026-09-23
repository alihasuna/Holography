# T2: half-torus surface feature (trench and ridge) through the pipeline, geometric engine

Status: IN PROGRESS, 2026-09-23. Agent T2. Written incrementally. Nothing committed or pushed.
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
     (`layer_height_A`, a/4 terraces) has 14 terraces on each flank (top/bottom terrace n = +-14,
     |h| = 19.01 A);
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
