# S1c: hologram formation and sideband reconstruction (Phase 2, part C)

Status: IN PROGRESS, 2026-09-22. Written incrementally; the final sections are filled in when the
tests have been run.

Scope (orchestrator task S1c): `reflection_holo/optics/`, `reflection_holo/reconstruction/`,
`tests/optics/`, `tests/reconstruction/`. Height conversion is NOT done here (it belongs to
`quantification/`); the reconstruction returns phases only.

Inputs read: docs/05 sections 5 and 8; docs/03 section 6; docs/physics_conventions.md;
docs/model_assumptions.md B5, B8; docs/06 items 3, 6, 15-19, 22; source map SM12, SM13, SM21, SM22;
tools/reflection_step_phase_calculator.py section 12 and checks T24/T25 (lines 1062-1068);
docs/agent_reports/A_code_audit.md C3 (find_peak) and M5 (default plane detrend).

## Log

1. Calculator trap reproduced before any code was written (scratch script, calculator functions
   only): on the T24 object hologram (n = 512, fringe 8 px, 50/50 tanh step of 2.3596 rad) the
   brightest bin outside the calculator's r < 0.05 cycles/px exclusion disc is fftshifted bin
   (255, 320), whereas the empty hologram gives (256, 192). Recentring on the object's brightest bin
   gives 0.7820 rad (noiseless) and 0.7815 rad (dose 1e4, seed 12345) instead of 2.3596 rad.
   Mechanism (DERIVED_HERE from these numbers): the bin is (i) on the CONJUGATE side (+q_c, which
   carries -(phi_o - phi_r)) and (ii) one row off, which adds a ramp of 2 pi/512 per row, i.e. pi
   over the 256-row separation of the two terrace medians: -2.3596 + pi = 0.7820. The calculator's
   0.78 rad is therefore a sign error plus a ramp, not a ramp alone. If the object and the empty
   hologram are both demodulated at the object's brightest bin and divided, the ramp cancels and the
   result is -2.3596 rad (still wrong: conjugate sideband).
