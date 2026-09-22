# S1b: Si(001) structure builder (spec section 4.2)

Status: in progress, 2026-09-22. Agent S1b (Phase 2, part B). Owned paths: `reflection_holo/structure/`,
`tests/structure/`, this report. No other file is edited; nothing is committed by this agent.

## Inputs read

docs/05 sections 2 (CFG-B), 4.2, 4.5, 8; docs/physics_conventions.md; docs/03 sections 2 and 4;
docs/model_assumptions.md B3, B4, B7, B9; docs/06 items 8, 11, 12, 13; docs/01 section 3.3 (A-M7);
`tools/reflection_step_phase_calculator.py` (`screw_search`, `d_spacing_A`, section 4b).
Shared modules imported, not modified: `reflection_holo/constants.py` (`A_SI_A`, `DIAMOND_BASIS`),
`reflection_holo/geometry/frames.py` (`surface_frame`).

## Log

1. Calculator `screw_search()` re-run: `Rz(+90)` and `Rz(-90)` with `t = a(1/4,1/4,1/4)` and
   `a(3/4,3/4,1/4)` map the diamond basis onto itself (4 operations), as printed in section 2b.
2. Extra probe (DERIVED_HERE, same enumeration with mirrors instead of rotations): the mirror
   `(010)` (and `(100)`) combined with `t = a(1/4,1/4,1/4)` also maps the basis onto itself (a d-glide
   of Fd-3m), while the `(1-10)` and `(110)` mirrors need `t_z = a/2`. The `(010)` mirror plane contains
   the `[100]` beam azimuth and the normal; see open issues.
3. Modules written under `reflection_holo/structure/`: `lattice.py` (one diamond lattice from the
   conventional cell, a/4 site rule, periodic neighbour search), `checks.py` (assertions a, b, c, g),
   `si001.py` (staircase request checks d, e; builder; relation finder for f), `shadows.py`
   (ray-traced shadowed strips, patterned features), `xyz.py` (extended-XYZ writer and reader,
   metadata JSON).
4. Bug found in the first smoke run and fixed: the crystal-origin shift was built from
   `frame.x_hat` (crystal coordinates) instead of the slab normal (1,0,0); assertion (d) caught it
   (measured terrace tops one layer above the requested ones).
5. Smoke runs: [110], [1-10], [100] with parallel and transverse edges, mixed a/4 and a/2 steps: all
   assertions pass; 49,200 atoms built and checked in about 1 s; the a/4 shadow at 22.5 mrad is
   60.333 A.
