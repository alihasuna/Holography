# S4: fixes of audit A3 (pipeline) and the A2c residuals G1-G3

Status: IN PROGRESS, 2026-09-23. Agent S4. Written incrementally; nothing committed or pushed.
Branch `claude/electron-holography-orchestration-nakd7r`, HEAD `fdabd67` ("Fix the SLURM runner's
random failure under pipefail", A3 M4 already fixed there).
Scratch directory: `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/`
(written `$S` below; before/after test logs in `$S/s4/`).

## Baseline (HEAD fdabd67, unmodified)

`venv/bin/pytest -q`: `646 passed, 6 warnings in 204.78s (0:03:24)`.

Smoke CLI (`--out $S/s4_smoke_0`), exit 0:
```
purpose: demo; not comparable to experiment
engine: geometric model, no dynamical amplitude, B4 scope applies
step field terraces 0->1 (translation): h = +2.7156 +- 0.0117 A (branch -4, wrap period 0.7612 A)
step field terraces 1->2 (screw): h = -1.3576 +- 0.0058 A (branch 2, wrap period 0.7612 A)
step field terraces 2->0 (screw): h = -1.3580 +- 0.0058 A (branch 2, wrap period 0.7612 A)
no-step control: PASS {'performed': True, 'delta_rad': -0.0036868859167245027, 'tolerance_rad': 0.012310012257320535, 'n_sigma': 3.0, 'se_correlated_rad': 0.004103337419106845, 'passed': True, 'n_a': 1960, 'n_b': 2016, 'controls_sigma_uncorrelated_rad': 0.0002516205842901576, 'field_terrace': 1}
outputs in /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/s4_smoke_0: summary.json, manifest.json, arrays.npz quicklook_detector.png quicklook_exit_wave.png
```
