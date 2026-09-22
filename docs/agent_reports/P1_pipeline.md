# P1: end-to-end pipeline, geometric-phase engine, dark-field optics and HPC runner (Phase 3)

Status: IN PROGRESS, 2026-09-22. Written incrementally. Not committed (the orchestrator commits).
Code not audited or reviewed by another agent.

Scope (orchestrator task P1): `reflection_holo/pipeline/`, `reflection_holo/forward/geometric/`,
`reflection_holo/optics/{darkfield,projection,detector}.py`, `configs/demo_*.yaml`, `scripts/hpc/`,
`tests/pipeline/`, `tests/forward_geometric/`, new stand-in IDs in
`reflection_holo/io/assumption_registry.yaml` (explicitly requested). Not touched: `forward/multislice`,
`forward/cell.py` (multislice agent), docs other than this report.

Inputs read: docs/05 sections 0 (criterion 5), 3, 4.5, 5, 9.1; docs/03 sections 1, 4, 6;
docs/physics_conventions.md; docs/06 items 1-22; docs/model_assumptions.md; forward/contracts.py;
the APIs of structure/ (si001, shadows), optics/ (fields, hologram), reconstruction/sideband,
quantification/ (height, shadow, controls, noise, invisibility), io/ (config gate, registry, labels),
provenance/manifest, geometry/ (specular, refraction, projection, wavelength, frames).

Baseline before any change: `venv/bin/pytest -q`: 580 passed, 6 warnings in 19.08 s.

## Log

1. Design decisions (before code).
   * The pipeline configuration embeds a complete CFG-B parameter block that is validated by the
     existing gate `reflection_holo.io.config.load_config_dict(level="run")`; the pipeline sections
     (structure, cell, engine, illumination, optics, reference, detector, reconstruction,
     quantification) use the same parameter record {value, unit, label, source, item,
     stands_in_for_item, assumption_id} and the same rules (supplied with supplier and date, or an
     ASSUMPTION registered for that docs/06 item; TEST_ONLY never from a file). Numerical settings
     that are no docs/06 item (grid sizes, seeds, thread count) are plain values, all required.
   * The glancing angle is not typed: the configuration names the rule (external angle of the
     (0,0,8) internal Bragg condition) and the pipeline computes it with
     `geometry.specular.specular_condition_for`, then inserts it into the CFG-B block as an
     ASSUMPTION stand-in for item 7 before the gate runs.
   * Adding stand-in IDs B19+ to the registry makes two existing io tests fail until the
     orchestrator adds the model_assumptions rows and updates the expected registry in
     tests/io/test_io_config_stand_ins.py (both files are not mine; not edited).
