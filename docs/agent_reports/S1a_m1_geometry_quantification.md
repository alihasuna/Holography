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
3. Implemented geometry/ (errors, wavelength, crystal, refraction, specular, accessibility,
   projection, sampling, plate_cell), quantification/ (errors, height, noise, invisibility, rocking,
   controls, shadow), io/ (config loader, validate_configs CLI), provenance/ (manifest) and the
   three configs. Smoke check against the calculator: theta_B_vac(666) 23.997603 mrad, theta_ext
   22.495315 mrad, mod2pi 3.923572 rad, h_2pi 0.557482 A (identical to the calculator output).
4. Ran `venv/bin/python -m reflection_holo.io.validate_configs configs/cfg_*.yaml`: CFG-A loads at
   run level; CFG-B refused at run level naming items 3, 4, 5, 7, 8, 12, 13, 15; CFG-O refused as
   a placeholder (UNVERIFIED: azimuth, energy, glancing angle, reflection order). A manifest was
   written under outputs/manifests/.
