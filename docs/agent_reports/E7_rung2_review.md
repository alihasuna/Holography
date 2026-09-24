# E7: adversarial review of P2's rung-2 exact reference and of the proposed engine test R2-A

Prepared 2026-09-24 by review agent E7. Written incrementally; status at the end of the file.
Under review (not edited): `docs/agent_reports/P2_rung2_reference.md` (P2 report, final run in its
section 11) and `tools/physics_checks/rung2_reference.py` (P2 tool).
My code: `tools/review/e7_recompute.py`, written WITHOUT reading the P2 tool's implementation of any
quantity it recomputes; it imports the P2 tool only in its last section, to compare numbers. Saved
output: `tools/review/e7_recompute_output.txt` ("E7 out §n" below). Nothing committed or pushed; no
other file edited.

Severity scale: BLOCKER (the reference or the test would validate or fail the engine wrongly),
MAJOR (a number, criterion or claim that is wrong or unsupported and matters for R2-A or for the
sizing), MINOR (wording, label or traceability defect that does not change a decision), NIT.

## 0. Log

* read: P2 report (all), docs/physics_conventions.md, reflection_holo/constants.py, the engine
  modules engine.py, potentials.py, propagator.py, analysis.py (flat_reflection_coefficient),
  illumination.py, grid.py, physics.py, forward/cell.py; H2 sections 0 to 3 and 10
  (`docs/agent_reports/H2_realistic_supercell_sizing.md`), H5 (`H5_sizing_review.md`) sections A-M3,
  D-G; the run-in and clean-depth lines of the H7-corrected `tools/hpc/supercell_sizing_output.txt`;
  M2 sections 2 and 10 (`M2_multislice_engine.md`); tests/forward/null_test_cases.py (geometry
  lines); tests/forward/smoke_case.py (head).
* NOT read before my numbers were final: `tools/physics_checks/rung2_reference.py` (only imported,
  as a black box, in the comparison section of my script).
