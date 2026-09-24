# E8: adversarial review of S5 (independent dynamical RHEED solver against the multislice engine)

Agent E8, 2026-09-24. Written incrementally; the final state is sections 9 to 11. Branch
`claude/electron-holography-orchestration-nakd7r`; S5's work reviewed at commit `872e949`. Nothing
committed or pushed by E8; no GPL-3.0 code or input copied into the repository.

Documents under review: `docs/agent_reports/S5_independent_rheed_solver.md` (the S5 report),
`tools/validation/rheed_solver_compare.py` (the S5 tool), `tools/validation/rheed_solver_results.json`,
`tools/validation/rheed_engine_results.json`; the solver sources, builds, runs and patch in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/rheed_solver/`
(upstream sim-trhepd-rheed `d98d6252`, P49 fork trhepd-opt `dc394ba`).

Method: every number below is printed by `tools/review/e8_recompute.py` (saved run
`tools/review/e8_recompute_output.txt`, section numbers "E8-n" below refer to its sections). The script
was written WITHOUT reading the S5 tool's implementation of the recomputed quantities (reflection
coefficient at the reference plane, one-beam reference, engine read-out, tolerance test, peak and
phase-sweep analysis, plane fit); it reads only the raw solver output files (`amp.txt`, the Fortran
inputs) and the stored engine exit columns. The S5 tool was read afterwards, only to locate the source
of a discrepancy, and its report mode was re-run as a black box.

Evidence labels as in the S5 report: SECTION_READ, REPRODUCED (executed here, saved output),
DERIVED_HERE, ASSUMPTION, UNVERIFIED, MEASURED_HERE (a number from the UNVALIDATED engine).

## 0. Log

- 01:00 UTC: read the S5 report (all), the patch, the upstream Fortran listed in S5 F1-F17, the
  P49 fork's `matcomp.f90`, `surf_rk.f90`, `surflf.f90`, `surfio.f90` (head); docs/05 4.4; L2 rows
  D1-D20, D-I1 to D-I4; the engine (`engine.py`, `potentials.py`, `analysis.py`, `illumination.py`,
  `propagator.py`, `grid.py`), H2's `flat_strip`; E1 Task 1 (rung 2 R2-A results).
