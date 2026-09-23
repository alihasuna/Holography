# P2: exact and two-beam reference for rung 2 of the phase-validation ladder

Prepared: 2026-09-23 (agent P2). Written incrementally; IN PROGRESS until section 9 says final.
Scope (orchestrator task): the reference for docs/05 section 4.4 rung 2 ("Bragg-case Bloch-wave
two-beam solution for one allowed reflection ... the multislice must reproduce the phase sweep, not
only the width"). Deliverables: `tools/physics_checks/rung2_reference.py` (importable functions and a
`__main__` that prints every number quoted here, with self-checks) and this report. No engine code,
summary document or other report was edited; nothing was committed.

## 0. Log

* read: docs/physics_conventions.md, docs/03_physics_summary.md, docs/05 section 4.4 (and 4.3),
  reflection_holo/constants.py, tools/reflection_step_phase_calculator.py (sections 0 to 4, 4b),
  docs/agent_reports/M2_multislice_engine.md (all), the engine modules physics.py, potentials.py,
  propagator.py, engine.py, analysis.py, illumination.py, grid.py, backend.py, cell.py,
  reflection_holo/geometry/{refraction,wavelength,specular}.py, tests/forward/ladder_cases.py,
  test_rung1_refraction.py, smoke_case.py, null_test_cases.py (head).
* NOT read before the derivation and code were finished (independence, orchestrator rule):
  docs/agent_reports/H2_realistic_supercell_sizing.md sections 2.1 to 2.3.
* prototype (scratchpad, later moved into the tool): laterally averaged Kirkland potential of a
  flat 41-layer Si(001) cell built by the repository's builder and realised by the engine's
  `AtomicPotential` (dx = 0.01 A): least-squares Fourier fit over 16 layer periods in the bulk gives
  V0 = 13.9028 V, V_(0,0,4) = 2.7401 V, V_(0,0,8) = 1.0357 V, V_(0,0,12) = 0.5467 V (origin at an
  atomic plane; sine terms < 1e-7 V), equal to 8 F(f^2)/a^3 from the engine's own scattering factor
  to 6e-6 V. (M2 section 10.2 used a rough estimate of 0.84 V; not used here.)
* first full run of `tools/physics_checks/rung2_reference.py` (48 self-checks, 0 failed): exact
  solvers agree to < 1e-9; the Darwin (Takagi-Taupin) form misses the refraction correction of the
  boundary condition (0.14 rad at the plateau centre); the two-beam closed form with exact matching
  is within 8e-3 of the exact solution. Side finding: with r = 0 the engine-style bulk absorber
  (15 A, sin^2, 100 V) reflects the Bragg-case Bloch waves outside the plateau strongly (|dR| up to
  0.38), and a clean depth of 21 A (the M2 null-test cells) is inside the extinction depth (24.5 A).
