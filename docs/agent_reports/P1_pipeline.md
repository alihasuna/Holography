# P1: end-to-end pipeline, geometric-phase engine, dark-field optics and HPC runner (Phase 3)

Status: COMPLETE for this task, 2026-09-23. Not committed by me (the orchestrator took snapshots
while I worked).
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
2. Implemented `forward/geometric/model.py`: TerraceModel from the builder (R_k accumulated from the
   step relations measured on the atoms; checked against the terrace heights), B4-scope refusals
   (a/4 step whose builder B4 statement is not the <100> in-scope one, any overlayer, a termination
   other than bulk, non-plane-wave illumination, a non-specular beam), exact ray trace of every
   exit-plane point back along -k_out with shadow.py's `shadow_masks` for illumination (and an
   assertion that every traced source is visible), invisibility flag for translation steps,
   ExitWave on "exit plane z = L_z (no further propagation)" in the envelope convention (the
   transverse carrier exp(i k_out,x x) included, exp(i k_z z) omitted, as in the multislice
   engine). First probe (terraces 800 periods, (0,0,8) at 16.474 mrad): the a/4 down-step shows a
   shadow band of 5 px and a riser band of 6 px at dx = 0.25 A (h = 1.358 A each on the exit-plane
   axis), the a/2 up-step no dark band (its blocked-view strip is not imaged), as derived.
3. Implemented `optics/darkfield.py` (exact angular aperture disc about k_out, demodulation at the
   absolute exit-plane x, band checks, aperture record), `optics/projection.py` (z_s, u and x
   samplings stated, flip so the along-beam axis runs downstream, parallax and the neglected
   envelope propagation recorded), `optics/detector.py` (pitch / M must equal CFG-B's image pixel;
   band-limited DFT resampling inside the projected field only; Poisson at the dose, then gain;
   MTF "none" only).
4. Coordinator decision received mid-task (report D3): multislice runs compute the glancing angle
   from the MIP of the potential actually used (Kirkland IAM, 13.903 V; measured here
   13.9028 V through `forward.multislice.potentials.potential_mean_inner_potential_V`), geometric
   runs keep B1 = 12.0 V. Implemented as the `V0_source` of the glancing-angle rule; the run
   asserts the potential's MIP equals the configured value to 5e-4 V. New stand-in B32 (item 7).
   (0,0,8): 16.474 mrad at 12.0 V, 16.135 mrad at 13.903 V.
5. The multislice agent's package became importable during the task; the adapter
   (`pipeline/engines.py`) was written against its current API (`forward.cell.build_reflection_cell`,
   `AtomicPotential`, `PhysicalAbsorption`, `SheetBeam`, `MultisliceParams`, `NumericalAbsorber`,
   `simulate`), not against a guessed one. The multislice ray-trace masks use a `FieldLayout`
   (crystal from z = crystal_start_z to the exit plane, x shifted to the cell frame, vacuum upstream,
   no closing step), because the reflection cell is open along z.
6. First end-to-end runs. Smoke demo (geometric): 2.1 s wall; a/2 step h = +2.71564 +- 0.01166 A
   (built +2.71545), a/4 steps -1.35765 +- 0.00584 A and -1.35800 +- 0.00584 A (built -1.35773);
   phase differences within 1 sigma of -q.n h; no-step control delta = -0.0037 rad against a
   3-sigma tolerance of 0.0123 rad; measured per-pixel phase scatter 0.005-0.0066 rad against the
   predicted 0.0039 rad for one hologram (x sqrt 2 for the division by the empty hologram: 0.0055).
   One configuration error on the way: PyYAML reads `3.0e5` as a string (YAML 1.1 needs a sign in
   the exponent); the demo now writes 300000.0. Tiny multislice variant: 7.5 s wall, steps
   reported as not measurable (terraces of 489 A are below the dark-field resolution), as intended.
7. First full HPC-size multislice run on this machine (CPU, `--variant cpu_numpy`, 1.44 million
   atoms, 1152 x 432 x 7215 slices, 10 min wall): the a/2 step was refused ("branch inconsistent
   under the lattice constraint") and the a/4 down-step came out as h = +1.4272 +- 0.0355 A
   (built -1.3577 A): WRONG SIGN. Diagnosis from the dark-field wave: the 8 A sheet beam has a
   footprint of H/tan(theta) = 496 A, so only the first ~500 A of terrace 0 is illuminated; the
   reflected amplitude over terraces 1 and 2 is 1-3 % of terrace 0's, i.e. those "phases" are not
   the specular reflection of the incident beam from those terraces. Two changes, both made before
   the rerun and not tuned on its result: (a) the HPC demo now uses a 150 A sheet beam whose
   footprint covers the three terraces (9.3 um of the 9.8 um crystal; vacuum above 320 A; nx 1920;
   all docs/05 4.3 assertions of the engine pass in dry-run) and centres the detector on the image
   of the terraces (`alignment: field_of_view`); (b) the quantification now excludes pixels whose
   reconstructed object amplitude is below a declared fraction (0.25, B29) of the empty-hologram
   object amplitude ("no object wave, no phase"), so an unilluminated terrace is reported as not
   measurable instead of giving a height. The first run's outputs are kept only in the scratch
   directory (not in the repository).
8. Two existing io tests fail because the registry now holds B19-B32 (expected; not my files):
   `test_registry_is_package_data_mapping_ids_to_items` (expects exactly B1, B17, B18) and
   `test_registry_ids_exist_in_model_assumptions` (B19 is not yet a row of
   docs/model_assumptions.md). The orchestrator must add the rows below and update the expected
   registry in tests/io/test_io_config_stand_ins.py.

## Proposed model_assumptions rows (orchestrator adds them to docs/model_assumptions.md)

All are demo stand-ins; a run with `purpose: comparison` refuses stand-ins for blocking items.

| ID | Assumption | Stands in for | Why this value |
|---|---|---|---|
| B19 | Glancing angle = external angle of the (0,0,8) internal Bragg condition computed by geometry.specular with V0 = 12.0 V (B1): 16.474 mrad; angle-calibration uncertainty 0.1 mrad (1 sigma) | item 7 | (0,0,8) is the proposed working condition (B17); computing, not typing, the angle keeps it consistent with V0; 0.1 mrad is a typical Kikuchi/rocking-curve calibration |
| B20 | Beam azimuth exactly [100], no misalignment | item 8 | inside the B4 scope for bulk-terminated a/4 steps (SM26), so the geometric model is valid for both step types |
| B21 | Plane-wave illumination: convergence semi-angle 0, no source-size or energy-spread ensemble | item 3 (and 2) | the geometric engine computes one plane wave; the azimuthal-spread effect on a/4 steps is not analysed (B4) |
| B22 | Dark-field objective aperture 3 mrad, centred on the specular beam | item 4 | below the 4.6 mrad transverse offset of the nearest non-specular rods at [100]; gives about 370 A of surface per reconstruction resolution along the beam |
| B23 | Detector pitch 15 um, magnification 3.0e5, image pixel 0.05 nm on both axes | item 5 | 4 pixels per 2 A fringe; object band 0.12 cycles/A below the detector Nyquist frequency 1.0 cycles/A |
| B24 | Ideal detector: gain 1 count/e, 500 e/px per hologram, Poisson noise only, no MTF, no readout noise, no drift | item 6 | a typical hologram dose; gives about 0.005 rad of phase scatter per pixel |
| B25 | Periodic Si(001) staircase, edges transverse to the beam, terrace layers (0, 2, 1): an a/2 up-step and two a/4 down-steps (one at the period boundary); terrace widths per configuration (800 periods smoke, 600 HPC, 90 tiny); terrace-0 back-bond axis [110] (irrelevant at [100]) | item 11 | one a/2 and one a/4 step in the field (the builder needs a closed period); terraces several resolutions long after foreshortening |
| B26 | Clean, bulk-terminated surface, no oxide or damage overlayer (restates B3 and B7) | item 12 | the ion-milling details are not supplied; B4 and the geometric model exclude an overlayer |
| B27 | No patterned features in the field of view | item 13 | the demo images atomic steps only |
| B28 | R1 vacuum reference beside the sample, passing the dark-field aperture after a condenser-biprism pre-tilt of 2 theta_ext (recorded, no effect); carrier fringe spacing 2.0 A (after compensation) along the perpendicular detector axis; reference amplitude equal to the empty object amplitude | items 15, 16 | the patent arrangement SM21; 2.0 A keeps the 3 mrad object band inside a |q_c|/3 sideband mask |
| B29 | Processing: carrier on the EMPTY hologram in a disc of |q|/2 about -q_ref, centre band |q|/4 excluded, integer bin; Hann disc mask |q_c|/3; division by the empty hologram, minimum visibility 0.5; Itoh raster unwrapping; regions 3 resolutions from any unusable pixel; object amplitude >= 0.25 of the empty object amplitude; branch from the lattice constraint h = n a/4, |n| <= 2, refused if not exactly one candidate within 3 sigma; 3-sigma no-step control; >= 50 px per region | item 19 | the calculator's T24/T25 processing (mask |q_c|/3, three-resolution pad) plus explicit refusal rules |
| B30 | No physical absorption in the multislice demos (imaginary potential 0; B6 not represented) | item 21 | no sourced absorptive-potential parameterisation (the [B15] warning forbids a tuned one) |
| B31 | Beam-energy stability: relative wavelength uncertainty 1e-5 (1 sigma), used only in the height uncertainty | item 1 (stability part) | negligible against the angle term; a stated, not guessed-to-zero, uncertainty |
| B32 | Multislice runs: the glancing angle and every refraction angle are computed with the mean inner potential of the potential actually used (Kirkland independent-atom model, 13.903 V, report D3 F16; 16.135 mrad at (0,0,8)), asserted against the engine's value to 5e-4 V; geometric runs keep B1. The IAM value exceeds B1 (12.0 V) by 1.90 V and the DFT value 12.53 V by 1.37 V: a model systematic of the engine (neutral free atoms, no bonding), not a correction | item 7 | consistency of the incidence angle with the refraction inside the simulated crystal (orchestrator decision after D3) |
9. Second full HPC-size multislice run (CPU, `--variant cpu_numpy`, corrected configuration:
   1920 x 432 x 7215 slices, 1.44 million atoms; 18.8 min wall, 45 min CPU on 4 CPUs): the pipeline
   ran end to end and wrote every output. No height: terrace 0 has no usable region, the a/4 step
   is refused ("branch inconsistent under the lattice constraint"), and the no-step control FAILS
   (delta = 0.441 rad between the two halves of terrace 1, tolerance 3 x 0.0966 = 0.290 rad). The
   dark-field phase of the multislice exit wave varies along the beam inside a terrace (quicklook:
   a slow gradient and amplitude modulation along the beam), unlike the geometric model. Not
   investigated further here: it is the engine's physics (UNVALIDATED; rung 2 and the abTEM
   cross-check NOT RUN), and the pipeline's refusals are the intended behaviour. Outputs are in the
   scratch directory only.

## Files (all new unless stated)

* `reflection_holo/forward/geometric/{__init__,model}.py`: geometric-phase engine, ray trace,
  B4-scope refusals, `FieldLayout` (also used for multislice masks).
* `reflection_holo/optics/darkfield.py`, `projection.py`, `detector.py`.
* `reflection_holo/pipeline/{__init__,__main__,config,engines,run,quantify,estimates}.py`.
* `configs/demo_smoke_si001.yaml` (geometric; variant `multislice_tiny`),
  `configs/demo_hpc_si001.yaml` (multislice cupy/complex64; variants `cpu_numpy`,
  `geometric_same_structure`).
* `scripts/hpc/run_pipeline.slurm`, `setup_env.sh`, `README_HPC.md`.
* `tests/forward_geometric/test_geometric_model.py` (7 tests),
  `tests/forward_geometric/test_darkfield_projection_detector.py` (7),
  `tests/pipeline/test_pipeline_geometric.py` (10), `tests/pipeline/test_pipeline_multislice.py`
  (2), `tests/pipeline/conftest_pipeline.py` (constants).
* Modified: `reflection_holo/io/assumption_registry.yaml` (B19-B32 appended, as requested).

## CLI

    venv/bin/python -m reflection_holo.pipeline list-inputs --config configs/demo_smoke_si001.yaml
    venv/bin/python -m reflection_holo.pipeline dry-run --config C [--variant V] [--calibrate-cpu]
    venv/bin/python -m reflection_holo.pipeline run --config C --out D [--variant V] [--allow-no-git]

Exit status 3 = configuration refused (missing PROJECT_INPUT, unregistered stand-in), 4 = engine
unavailable, 5 = output directory not empty.

## Test results (verbatim summary of the last full run, `venv/bin/pytest -q`)

    FAILED tests/io/test_io_config_stand_ins.py::test_registry_is_package_data_mapping_ids_to_items
    FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
    2 failed, 641 passed, 6 warnings in 197.86s (0:03:17)

The two failures are the registry extension of item 8 (`E       AssertionError: assert {'B1':
(20,),...9': (7,), ...} == {'B1': (20,),... 'B18': (14,)}` and `E           AssertionError: B19`);
every test I wrote passes (26; each acceptance test passed on its first run; no tolerance changed).

## NOT RUN

* The GPU run of `demo_hpc_si001.yaml` (no GPU here; the cupy backend is untested by me) and the
  SLURM submission itself (the script was exercised locally: placeholder refusal, a fake `sbatch`
  for the submission line, and job mode with the smoke configuration).
* `setup_env.sh` on a fresh machine (abTEM and matplotlib were already in this venv).
* R2 through the pipeline (implemented, no test), parallel step edges through the pipeline (engine
  test only), frozen-phonon ensembles (`n_realisations > 1`) through the pipeline.
* Any validation of the multislice step phases: they are not flat along the beam (item 9).

## Integration steps left for the multislice engine

1. Keep the names the adapter calls stable, or update `pipeline/engines.py`
   (`build_reflection_cell`, `AtomicPotential`, `PhysicalAbsorption`, `FrozenPhonons`, `SheetBeam`,
   `MultisliceParams`, `NumericalAbsorber`, `simulate`, `potentials.potential_mean_inner_potential_V`);
   `multislice_status()` reports what is missing.
2. Export `potential_mean_inner_potential_V` from the package (it is found in `potentials`).
3. Explain or remove the along-beam phase variation inside a terrace (item 9) before any
   multislice height is reported; the no-step control is the check.
4. A declared band limit as a number (`metadata["band_limit_cycles_per_A"]`) would let the
   dark-field stage assert the aperture against it (it now checks Nyquist only).
5. The orchestrator: add rows B19-B32 to docs/model_assumptions.md, update the expected registry
   in tests/io/test_io_config_stand_ins.py, and decide whether the three pipeline units ("e/px",
   "counts/e", "deg") move into io.config.UNITS.
