# E3 - Partial coherence from illumination convergence and surface-plasmon (inelastic) losses in hologram formation

Agent E3, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`. Status: IN PROGRESS
(written incrementally).

Scope (orchestrator task): (A) partial coherence from the illumination convergence (PROJECT_INPUT
item 3): an azimuthally tilted sheet beam, an ensemble generator with a stated, recorded quadrature,
incoherent summation of hologram intensities, the pipeline gate lifted only when item 3 is supplied,
an interface for running ensemble members as separate jobs; (B) surface-plasmon losses in hologram
formation (zero-loss factor, loss-electron fringes, R1 and R2 separately, noise from the reduced
visibility). Inputs read: H2 section 10 (N3), E6 (M1, M2, sections 8, 9), L6 section 1.6 with E6's
correction, `tools/review/e6_recompute.py` section F and its saved output, docs/03 sections 4 and 6,
docs/05 sections 4-6, docs/06 items 2, 3, 15, 16, 21, `docs/physics_conventions.md`,
`docs/model_assumptions.md` (B5, B6, B10, B21, B28), the illumination, engine, grid, propagator,
optics, reconstruction, pipeline and registry code.

Not edited (other agents): `reflection_holo/forward/multislice/potentials.py` (E1),
`reflection_holo/structure/` (E2), `scripts/hpc/alliance/`, every file under `docs/` except this
report. Nothing committed or pushed.

## 0. Log

* 2026-09-24: read the inputs above; baseline full test suite started before any edit (section 9).
