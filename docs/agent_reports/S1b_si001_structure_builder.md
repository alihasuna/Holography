# S1b: Si(001) structure builder (spec section 4.2)

Status: complete for the scope below, 2026-09-22. Agent S1b (Phase 2, part B). Owned paths:
`reflection_holo/structure/`, `tests/structure/`, this report. No other file was edited; nothing was
committed by this agent.

## Inputs read

docs/05 sections 2 (CFG-B), 4.2, 4.5, 8; docs/physics_conventions.md; docs/03 sections 2 and 4;
docs/model_assumptions.md B3, B4, B7, B9; docs/06 items 8, 11, 12, 13; docs/01 section 3.3 (A-M7);
`tools/reflection_step_phase_calculator.py` (`screw_search`, `d_spacing_A`, section 4b).
Shared modules imported, not modified: `reflection_holo/constants.py` (`A_SI_A`, `DIAMOND_BASIS`),
`reflection_holo/geometry/frames.py` (`surface_frame`).

## Files

| File | Content |
|---|---|
| `reflection_holo/structure/__init__.py` | public API |
| `reflection_holo/structure/lattice.py` | one diamond lattice from the conventional cell (integer a/4 coordinates), site rule, fcc-translation test, periodic neighbour search (explicit images plus cell list; numpy only) |
| `reflection_holo/structure/checks.py` | assertions (a), (b), (c), (g); stated tolerances |
| `reflection_holo/structure/si001.py` | `Staircase`, `OverlayerSpec`, `Si001Structure`, `validate_staircase` (d, e), `assert_step_heights`, `find_terrace_relations` / `classify_relation` / `is_diamond_symmetry` (f), `build_si001_terraces` |
| `reflection_holo/structure/shadows.py` | exact ray trace of piecewise-linear profiles, periodic variant, `terrace_shadow_strips`, `PatternedFeature`, `EdgeProfile`, feature shadow intervals and 2-D masks |
| `reflection_holo/structure/xyz.py` | extended-XYZ writer and reader recording the frame, metadata JSON writer |
| `tests/structure/si001_test_inputs.py`, `conftest.py` | TEST_ONLY inputs and fixtures |
| `tests/structure/test_si001_builder.py`, `test_si001_assertions.py`, `test_si001_options.py`, `test_structure_shadows.py`, `test_structure_xyz.py` | 98 tests |

## Builder interface

`build_si001_terraces(*, azimuth_uvw, azimuth_label, staircase, edge_periods, substrate_layers,
first_terrace_backbond_uvw, termination, overlayer, vacuum_above_A)`: keyword-only, no defaults
(tested by signature inspection and by dropping each argument). The azimuth must be in the [110] or
[100] family (PROJECT_INPUT item 8) and carry a label starting `PROJECT_INPUT`, `TEST_ONLY` or
`ASSUMPTION`. `Staircase(edges, terrace_layers, terrace_widths, boundary_step_layers)`: terrace
heights on the a/4 grid, widths in in-plane lattice periods (a/sqrt2 at <110>, a at <100>), step
edges `parallel` or `transverse` to the beam, and the step at the periodic cell edge DECLARED by the
caller. `first_terrace_backbond_uvw` fixes which of the two screw-related terrace types terrace 0
is (at [110]: bonds along or across the beam). Output: `Si001Structure` with positions (A, slab
frame, bottom layer at x = 0), cell, pbc (F, T, T), frame, layer and terrace index, crystal origin,
and metadata (azimuth, frame rows, terrace map with measured top-layer back-bond axis, step list
with type `translation`/`screw` and the operation found on the atoms, options with labels, atom
count, tolerances, assertions passed, positions SHA-256).

## Assertions and their tests

Tolerances: positions, distances, step heights 1e-6 A; half-open window 1e-6 A; duplicates below
0.5 A. All raise `StructureAssertionError` explicitly (survive `python -O`). The builder runs all
of them; `test_builder_refuses_duplicated_sites` and `test_builder_refuses_non_site_points`
corrupt the lattice generator and show the builder fails.

| | Assertion | Tests |
|---|---|---|
| a | every atom on a site of ONE diamond lattice (integer a/4 coordinates, parity rule) | built structures pass; one atom moved 0.01 A, one moved to a non-site a/4 point, and a terrace shifted by (a/2)[100] all fail |
| b | half-open window `[-tol, L - tol)`, per-terrace and total atom count equal to the occupied volume, no duplicates under the PBC | independent count formula for [110] and [100]; A-M7 reproduced (y = 0 plane duplicated at `L(1 - 1e-15)`) and caught by both the window and the duplicate check; count mismatch caught; window edges tested at +-0.5e-6 and 2e-6 A |
| c | minimum distance = a sqrt3/4; bulk-interior atoms 4-coordinated across the PBC | brute-force O(N^2) minimum-image cross-check; atom 1 A from another, a cell length 0.5 A off the lattice period, and a removed interior atom all fail |
| d | steps exactly a/4 or a/2 as requested, measured on the atoms | 3- and 4-layer steps and zero steps refused; measured heights equal requested to 1e-6 A; wrong built heights caught |
| e | staircase continuous under the periodic boundary; net height change refused (vicinal cell NOT IMPLEMENTED) | the inspected repository's 0,1,2,3 staircase refused in all three declarations: boundary +1 ("net height change of +4 layers ... hidden 3-layer down-step"), -3 (hidden 3-layer step, not a/4 or a/2), 0 (net +3) |
| f | a/2 terraces related by a pure lattice (fcc) translation; a/4 terraces by a 90-degree lattice screw and not by any translation; top-layer back-bond axis unchanged / rotated 90 degrees; measured on the built atoms | relation finder generalises `screw_search` (same rotations, a/8 grid, basis-mod-lattice test); its screw set equals the calculator's `screw_search()` output modulo the surface net; back-bond axes checked by an independent O(N^2) bond search; mislabelled steps, a terrace shifted by a/8 (found by the grid but flagged not a lattice symmetry) and an imperfect layer all fail |
| g | frame right-handed, orthonormal, x = [001], beam azimuth in the surface plane | all four azimuths; left-handed frame caught; [111] refused by `surface_frame`, [120] refused as not item 8 |

Shadows: `abs(L - 60) <= 0.5` A for a/4 at 22.5 mrad (docs/03 section 4 prints "60 A"), also 444 nm
(10 nm mesa) and 139 A (Si(111) bilayer); from a built single a/4 step the interval is 60.333 A and
equals `h/tan(theta)` to 1e-9 A; up-steps along the beam cast none; truncation by the next rise,
two successive down-steps, wrap across the cell edge, parallel edges (none), sloped mesa walls
steeper and gentler than the beam, trenches narrower and wider than the shadow, 2-D masks.

## pytest output (verbatim, `venv/bin/pytest -q tests/structure`)

```
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 0.95s
```

Full suite at the end of the task (`venv/bin/pytest -q`): `355 passed in 6.19s`. An earlier full
run showed `FAILED tests/geometry/test_geom_projection.py::test_shadow_bilayer_888` (geometry
agent's file, in progress; not touched; passing at the final run).

## Log

1. `screw_search()` re-run: Rz(+90) and Rz(-90) with t = a(1/4,1/4,1/4) and a(3/4,3/4,1/4).
2. Probe (DERIVED_HERE): the (010) and (100) mirrors with t = a(1/4,1/4,1/4) also map the diamond
   basis onto itself (d-glide of Fd-3m); the (1-10) and (110) mirrors need t_z = a/2.
3. Bug found by assertion (d) in the first smoke run and fixed: the crystal-origin shift used
   `frame.x_hat` (crystal coordinates) instead of the slab normal (1,0,0).
4. Test-side corrections (no tolerance changed): a wrong regex ("(b) atom" vs "(b) 30 atom(s)");
   `pytest.approx` on nested interval lists (flattened). A code defect found by a 1e-9 degree test:
   the back-bond angle used `arccos` near 1 (1.2e-6 degree error); replaced by `atan2`.
5. Timing: 49,200 atoms built and fully checked in about 1 s.

## NOT IMPLEMENTED (with reasons)

* 2x1 dimer reconstruction: raises `NotImplementedError` naming the missing source (no dimer
  geometry has been read; values must not be invented).
* Overlayer atomistic content: only the declared conformal region (thickness, density, material,
  label; per-terrace x ranges) is recorded; a random-network model needs a source. No atoms placed.
* Vicinal cell for staircases with a net height change: refused.
* Atomistic mesas and trenches: only height profiles and shadows (nm features are 1e7+ atoms; the
  engine representation is undecided). Orientations other than 0/90 degrees and edge profiles other
  than vertical/linear raise `NotImplementedError`.
* Exit-side occlusion (reflected beam blocked by a rise downstream): not in docs/03 section 4.
* Step-riser relaxation: none (ASSUMPTION). Engine-specific writers: none yet.

## NOT RUN

No simulation, engine or run manifest: this is a library plus tests (the metadata carries the
package version and positions SHA-256 for the provenance writer). No structure was passed to any
engine.

## Open issues

1. [100] azimuth (DERIVED_HERE, measured on built atoms, `incidence_plane_mirror_operations`): the
   two a/4 terrace types are also related by a glide whose mirror plane contains the beam and the
   normal; at [110] they are not (bonds along vs across the beam). If confirmed, for beams in that
   plane (the specular beam) the terraces would have equal dynamical reflectivity at [100], so
   docs/03 section 2 ("different complex reflectivities at a general azimuth"), B4 and
   model_assumptions open question 3 would apply only at [110]. This bears on PROJECT_INPUT item 8.
   Needs physics review; no document was changed.
2. Wording: SM07/B9 say "behind a transverse up-step"; docs/03 says "upper terrace upstream". The
   code implements docs/03 and records `upper_terrace_upstream` per step.
3. Exit-side occlusion strip: `geometry.projection.shadow_length_A`'s docstring mentions a
   "blocked-view strip" at the exit angle; docs/03 does not. Needs a docs decision.
4. No model_assumptions rows yet for "riser relaxation none", overlayer conformality, the riser
   position used for shadows (the terrace-boundary coordinate) and `dimensions_at` (top or base)
   of item 13 dimensions.
5. Consolidation: `structure.shadows._shadow_length_A` duplicates
   `geometry.projection.shadow_length_A` (agreement test added); the label checker is duplicated in
   `si001.py` and `shadows.py`.
6. Which terrace type lies where (`first_terrace_backbond_uvw`) is a sample property absent from
   the PROJECT_INPUT list.
