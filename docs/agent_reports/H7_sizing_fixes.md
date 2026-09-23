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
