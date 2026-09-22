# M2: reflection multislice engine (custom numpy/cupy kernel), build report

Prepared: 2026-09-22 (Phase 3, agent M2). Written incrementally; the final state is section 9.
Scope (orchestrator task): `reflection_holo/forward/cell.py`, `reflection_holo/forward/multislice/`,
`tests/forward/`, this report. Interface: `reflection_holo/forward/contracts.py` (ReflectionCell,
ExitWave), unchanged; only metadata keys are added.

Status label of the engine: UNVALIDATED for atomistic reflection. Rung 1 (refraction-only analytic
limit) and rung 3 (continuum null tests) of the docs/05 section 4.4 ladder are run below; rung 2
(Bragg-case two-beam phase sweep), the abTEM cross-check (transmission and reflection-like
configurations, docs/05 section 4.3 engine plan) and the flat-surface rocking curve against a
dynamical solver are NOT RUN.

## 0. Log

* started: read docs/05 4.3, 4.4, 9.1; docs/03 3, 5; physics_conventions; model_assumptions A1, A2,
  B6, B7; 06 items 3, 12, 21; contracts.py; structure/si001.py; constants; geometry/.
* abTEM 1.0.10 was already installed in the venv (D3 section 0.3); its parameterisation functions
  were read in `abtem/parametrizations/__init__.py` and `abtem/parametrizations/functions/lobato.py`,
  `kirkland.py`; `projected_scattering_factor(symbol)(k2)` returns the 2D Fourier transform of the
  infinite projected potential in V A^3 (checked here by a Hankel transform against
  `projected_potential(r)`: 222.45 vs 222.80 V A at r = 0.2 A, 19.73 vs 19.76 at 1.0 A with the
  transform truncated at k = 60 1/A).
