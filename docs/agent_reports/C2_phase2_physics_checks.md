# C2: Phase 2 physics checks (a/4 step symmetry on Si(001), carrier-location trap, R2 twin)

Status: IN PROGRESS, 2026-09-22. Agent C2 (physics-deriver). Owned paths: this report and
`tools/physics_checks/`. No package, test or document file was edited; nothing was committed.

## Inputs read

docs/physics_conventions.md (all); docs/03_physics_summary.md sections 2 and 6 (and 3, 7 for
context); docs/model_assumptions.md B4 and open question 3; docs/06_project_inputs_required.md
item 8; tools/reflection_step_phase_calculator.py (`screw_search`, `SpecularCondition`, section 4b,
`_sideband_wave`, `hologram_roundtrip`, checks T24/T25); docs/agent_reports/S1b (open issue 1, log
item 2); docs/agent_reports/S1c (log item 1-2, open issues 1-2); docs/agent_reports/C_physics_derivations.md
sections 2.3, 3.6 and 7 (the trap paragraph); reflection_holo/structure/si001.py and lattice.py,
reflection_holo/reconstruction/sideband.py, reflection_holo/optics/hologram.py and fields.py;
tests/reconstruction/holo_cases.py, test_carrier_trap.py, test_self_reference_R2.py.

Conventions (docs/physics_conventions.md): `exp(+i k.r)`; angular wavevectors in rad/A; glancing
angles to the surface plane; `n_hat` the outward normal; `Delta_phi = phi(upper) - phi(lower)`,
signed; numpy FFT sign (a wave `exp(+2 pi i q0.r)` appears at `+q0`). Beam energy 200 keV
(PROJECT_INPUT item 1). Crystal (cubic) axes are used for the symmetry work: outward normal
`[001]`; the package's slab frame is x = [001], z = beam azimuth, y = z x x.

No textbook passage was read for this report. Nothing below is attributed to a source; every
result is DERIVED_HERE from the stated premises and checked numerically, or REPRODUCED (an earlier
agent's number re-obtained by an independent script of this report).

## Scripts (all numpy only; `venv/bin/python tools/physics_checks/<name>.py`)

| Script | Question | Self-checks |
|---|---|---|
| (being written) | | |

(Sections for questions 1 to 3 follow as they are completed.)
