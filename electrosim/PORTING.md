# Porting map: si110-reflection-holography @ 6694959 -> electrosim/

Defect IDs refer to `docs/agent_reports/A_code_audit.md` (A), the specification
`docs/05_final_repository_specification.md` (spec) and `docs/03_physics_summary.md`.

## Files

| si110 file | electrosim file | What changed |
|---|---|---|
| `sample_generators/si110_cleave_slab_generator.py` | `code/si110_cleave_slab_generator.py` | Same slab frame and wide-gap cut planes; every setting from the parameter file (no argparse defaults); half-open periodic bounds with a rounding tolerance (M7: a duplicated plane at y = 0 and, here, a 7th (220) plane along z); exact atom-count assertion and periodic duplicate check; measured geometry written (M8); cyclic terrace sequence enforced (spec §4.2); forbidden or non-specular target reflections refused (A-C4, spec §4.1) with the refraction-corrected external angle; extxyz output (exact cell) instead of the Prismatic `.xyz`; the inert thermal options removed (thermal motion is in the forward model). |
| `pipeline/multislice_forward_model.py` (prismatique 0.0.1) | `code/multislice_forward_model.py` (abTEM 1.0.10) | Engine swap: prismatique/Prismatic are not on ElectroSim. abTEM's wave is on the exit face of the box (M4: prismatique's was the mid-plane); the grid simulated is the grid reported (C2); no `try/except` around engine calls (m15); no inert absorber (M3); memory estimate of what is allocated, with a hard limit for the shared GPU slice (M17); `.get()` before numpy for CuPy arrays and memory pools released; ground truth σ·V_proj and the parametrisation's mean inner potential written. |
| `pipeline/multislice_tilt_series_runner.py` | `code/multislice_tilt_series_runner.py` | Uses the forward model's code (m20: 250 duplicated lines); invalid keywords that disabled all output removed (C1); each tilt simulated exactly and stored with its value (C2, C5); the sample-rotation "validation" that broke periodicity removed (M9). |
| `pipeline/specular_filter.py` | `code/specular_filter.py` (spot selection) + `code/hologram_formation.py` + `code/holo_recon.py` | Split as the audit asked (M1): the objective aperture on one spot of the exit wave (spot vector from the crystal, k_in + g in abTEM's frame: C7; forbidden reflections refused; aperture in mrad: M6; tilt by value: C5; pixel size from the sidecar: C6); hologram formation from that image wave, with a vacuum reference hologram (new); reconstruction from intensities only, with the carrier located on the reference hologram (C3), the aperture in 1/Å (M6), reference normalisation, a 2-D unwrapper (M14), raw phase saved (M15), no default detrend (M5), and Hann/Hamming apertures kept from the old filter alongside HoloSpy's tanh. |
| `pipeline/step_height_reflection_formula.py` | `code/step_height_reflection_formula.py` | Signed steps in a fixed spatial order from the known terraces (C8, M11); wrap period and branch family reported (C4); external angle required, no silent defaults (M12); no-step control and refusal when the height uncertainty exceeds a fraction of the wrap period (M11, spec §5.8); `is None` instead of falsy-zero (M11). |
| `pipeline/process_all_tilts.py` | `code/process_all_tilts.py` | Runs filter -> hologram -> recon -> steps for every tilt (selected by value) into one gemicro-recorded folder (M10: a renamed script, a hard-coded HPC path, a layout the runner never wrote, exit 0 on failure). |
| `pipeline/hdf5_output_validator.py` | `code/output_validator.py` | Assertions on every stage folder: shapes and dtypes against the sidecar, axes, sampling, NaN, plots (M19). |
| (none) | `code/holo_validate.py` | New: NCC, phase-scale slope, residual map against the shot-noise prediction, registration, resolution, terrace-edge steps, mask sensitivity, expected-failure controls. |
| (none) | `code/import_experimental_holograms.py` | New: experimental holograms enter the same reconstruction (spec §5.7). |
| `requirements.txt` (unpinned) | ElectroSim's fixed environments; versions recorded by gemicro and in every sidecar (M16) |  |
| no tests | `tests/` (27 tests, runner without pytest) (M19) |  |

## Audit defects and their status

| ID | Status |
|---|---|
| C1 invalid keywords, no output | fixed (engine replaced; no swallowed exceptions) |
| C2 hidden 4 × 4 interpolation | fixed (grid reported is grid simulated; abTEM has no tilt grid) |
| C3 carrier = argmax of the object FFT | fixed (reference hologram, declared half plane, optional expected carrier with tolerance; test) |
| C4 wrap/branch ignored | fixed in the quantification (wrap period, branch family, branch matching the truth for simulations); a single hologram still cannot fix the branch: rocking-series inversion is future work |
| C5 tilt index 0 | fixed (selection by value, failure when absent; test) |
| C6 advisory pixel size | fixed (pixel sizes only from sidecars) |
| C7 search radius from |g| | fixed (spot vector from the crystal in abTEM's incident-beam frame) |
| C8 sign destroyed | fixed (signed, fixed order; test) |
| M1 no hologram | fixed (hologram + reference + reconstruction stages) |
| M2 reflection cell | **open**: needs milestone M2 (absorbing reflection cell, confined illumination, dynamical-solver validation); the reflection example is labelled exploratory |
| M3 inert absorber | removed; an absorber belongs to M2 |
| M4 mid-plane wave | fixed (abTEM exit face, declared in the sidecar) |
| M5 default detrend | fixed (none by default; optional plane fitted on the reference region only, saved) |
| M6 aperture in pixels | fixed (1/Å or mrad, resolution reported, ±20 % sensitivity) |
| M7 duplicated plane | fixed (half-open bounds + atom-count assertion + duplicate check) |
| M8 meta misreports geometry | fixed (measured geometry written) |
| M9 sample-tilt validation | removed |
| M10 batch driver | rewritten |
| M11, M12 histogram levels, silent defaults | fixed |
| M13 circular roll | integer Fourier shift kept (exact and periodic); the sub-pixel remainder cancels in the reference normalisation, and a Tukey window on both holograms removes the edge leakage |
| M14 row/column unwrap | fixed (scikit-image, residues counted) |
| M15 raw phase not saved | fixed |
| M16 nothing pinned | the ElectroSim environments are fixed; versions recorded per run |
| M17 memory estimate | fixed (estimate of what is allocated; hard limit) |
| M18 README inconsistencies | not carried over (new README) |
| M19 no tests | 27 tests |
