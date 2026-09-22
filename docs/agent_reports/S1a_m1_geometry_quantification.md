# S1a: milestone M1, geometry, quantification, io and provenance

Status: IN PROGRESS (2026-09-22). Written incrementally by the S1a build agent; the orchestrator
commits. Scope: docs/05_final_repository_specification.md sections 4.1, 5 item 8, 8 and 9 (M1).
Beam energy 200 keV everywhere; 300 keV appears only as the T3 formula check of the wavelength
function.

## Progress log

1. Read docs/05 (sections 0, 2, 3, 4.1, 5.8, 8, 9), physics_conventions, 03_physics_summary,
   model_assumptions, 06_project_inputs_required, source_map.tsv, the calculator (all 1168 lines),
   constants.py and geometry/frames.py.
2. Pre-check of the shadow-length reference values with the calculator's own SpecularCondition
   (before any code was written): the (8,-8,8) bilayer shadow is 101.48 A, not the 102 A printed in
   docs/03 section 4 (from E2 review F14). Kept as 102 A +- 0.5 A in the test (see open issues).
