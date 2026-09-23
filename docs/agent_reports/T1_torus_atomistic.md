# T1: half-torus surface feature on Si(001), atomistic structure and small multislice runs

Agent T1 (second smoke test requested by Ali). Branch claude/electron-holography-orchestration-nakd7r;
nothing committed or pushed by this agent. Beam energy 200 keV throughout (300 keV never used).
Status of every multislice output below: UNVALIDATED (finite-cell build-up not converged, no
physical absorption, report M2 section 10).

## 0. Log

- 02:08 UTC: read shapes.py (fixed shared definition, not modified), structure/ (si001, lattice,
  checks), forward/contracts.py, forward/cell.py, forward/multislice/, M2 report sections 5, 7, 10,
  docs/05 section 4.2. Angle from the engine's MIP (B32): V0 = 13.9028 V (Kirkland independent
  atom), (0,0,8) external angle 16.1347 mrad, internal 18.4719 mrad; build-up length for
  D = 20 A: 1082.6 A along z.
