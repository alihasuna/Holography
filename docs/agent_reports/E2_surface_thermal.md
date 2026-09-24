# E2 - Si(001) reconstructions, reconstructed steps and the sourced thermal displacement

Agent E2, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`. Status: IN PROGRESS
(written incrementally). Nothing committed or pushed. No file under docs/ other than this report is
edited; `reflection_holo/forward/multislice/potentials.py` (agent E1) is read only.

Inputs read: L7 sections 1.1-1.4, 5, 6 (Ramstad, Brocks and Kelly 1995 [R1] Tables III-IV as
transcribed in 1.4; Zandvliet 2000 [R2]; Horio 2014 [R3]; Shirasawa 2006 [R4]); L6 sections 2 and 7.1
(Heacock et al. 2021); E6 in full (sections 8 and 9, minor findings m2 and m3);
`reflection_holo/structure/` (si001.py, lattice.py, checks.py, features.py),
`reflection_holo/forward/multislice/potentials.py` (FrozenPhonons, AtomicPotential, _RealisedAtomic),
`reflection_holo/pipeline/config.py` and `engines.py`, `reflection_holo/io/assumption_registry.yaml`,
`docs/model_assumptions.md` (A7, B3, B4), docs/05 section 4.2, tests/structure, tests/io.

## 0. Log

* 2026-09-24: design (section 1) fixed before coding.
* 2026-09-24: implemented `reflection_holo/structure/reconstruction.py` (R1 tables, frame, dimer
  cells, flip-flop states, measurements), wired into `si001.py` (options, assertions (r1)-(r6));
  `structure/thermal.py` (B35); `forward/dimer_ensemble.py` (B37 wrapper, potentials.py
  untouched); pipeline gate and engines (item 23, terminations); registry B35-B37; feature builder
  refusal. First scan over 560 staircase builds (5 terminations x 7 staircases x 2 edge
  orientations x 4 azimuths x 2 terrace types): all build except c(4x2) on joined terraces whose
  period is not a c(4x2) lattice vector (refused with ReconstructionError, by design). Terrace
  interiors reproduce the source geometry exactly (minimum distance = the table's dimer bond);
  bonds across risers are compressed by at most 5.5 % of d_nn (2.176 A, p(2x2)), an artefact of
  "step-riser relaxation none" (section 3.4).
