# Specification: what the final theoretical simulation repository must look like

Status: 2026-09-21, version 0.1 (orchestrator synthesis of reports A to D and independent checks).
Purpose: define the repository that will produce simulated observables to be contrasted with the
real reflection-mode dark-field electron holography experiment on silicon surfaces (Osakabe-type
measurement), starting from the inspected repository `hussienba/si110-reflection-holography`
(commit 6694959) and its instruction file. Everything here follows the source policy of that
instruction file; unresolved items are labelled PROJECT_INPUT, ASSUMPTION or UNVERIFIED.

## 0. Acceptance criteria (definition of "final")

The repository is final when all of the following hold:

1. It produces, for a named configuration, the full observable chain: reflectivity amplitude and phase
   versus glancing angle (rocking curve), dark-field image wave with correct foreshortening, reference
   wave under a declared model, ensemble-averaged hologram intensity with detector effects, reconstructed
   phase produced by the same code used on the experimental holograms, and quantified heights with
   uncertainties and branch information.
2. The forward model reproduces the physics test plan (`docs/03_physics_summary.md` section 7; checks
   T1 to T25 and the qualitative checks) and a flat-surface rocking-curve benchmark against an
   independent dynamical reflection solver, within stated tolerances.
3. The Osakabe-type benchmark (monatomic steps on Si(111), phase step versus glancing angle) is
   reproduced with the refraction-corrected geometric phase plus a quantified dynamical residual.
4. Every physical claim, material parameter and algorithm has a `docs/source_map.tsv` record with an
   evidence label, and every run writes a provenance manifest.
5. No result depends on a default silently substituted for a missing PROJECT_INPUT; such runs fail.

## 1. What the current repository is, in one paragraph

The inspected repository is a transmission HRTEM multislice (Prismatic through prismatique 0.0.1) run on
a free-standing 8.5 nm Si plate whose (1,-1,1) face is parallel to a [110] beam tilted by up to 24 mrad,
followed by Fourier selection of one spot of the resulting complex wave and a kinematic phase-to-height
formula. It contains no reference wave, forms no intensity hologram and performs no reconstruction; the
wave it reads is the supercell mid-plane wave, not an exit wave; its default vacuum, slab length and
sampling make end-face Laue transmission, not surface reflection, the dominant channel; its named
specular condition (666) is a forbidden reflection; its default target (2,-2,0) is inaccessible in
reflection geometry; and its phase-to-height step cannot resolve the 2 pi branch. The itemised audit is
in `docs/01_repository_audit.md` and the agent reports under `docs/agent_reports/`.

## 2. Named configurations (kept separate; instruction file section 2)

| ID | Name | Surface, azimuth | Steps and features | Specular conditions | Status |
|---|---|---|---|---|---|
| CFG-A | `si111_cleaved_110azimuth` | (1,-1,1) surface, beam azimuth [110] | lattice-translation bilayer steps `h = m d_111`, `R = m (a/2)[1,0,1]` (stacking-correct in-plane shift) | (444), (555), (777), (888); never (666) or (222) | benchmark inherited from the inspected repository; geometry consistent (normal.beam = 0) |
| CFG-B | `si001_patterned` | (001) surface, azimuth [110] or [100] (PROJECT_INPUT item 8) | single-layer `a/4` steps (screw-related terraces, dynamical difference expected), double-layer `a/2` steps, patterned mesas/trenches of nm height (PROJECT_INPUT item 13), optional oxide/amorphous overlayer (item 12) | (004), (008), (0,0,12); (002), (006) forbidden | Ali's experiment; all unknowns listed in `docs/06_project_inputs_required.md` |
| CFG-O | `osakabe_1988_reproduction` | UNVERIFIED (P01 not readable here) | monatomic steps | UNVERIFIED | placeholder until P01 (and P08, Osakabe 1992) are read |

Each configuration is a versioned YAML/JSON file with every parameter labelled by evidence level.

## 3. Architecture

```
reflection_holo/
  geometry/       crystal, surface, rotations, reciprocal lattice, structure factors, Bragg/rod
                  conditions, refraction, accessibility, foreshortening   (pure numpy, fully tested)
  structure/      slab and terrace builders (stacking-correct steps, Si(001) screw-related terraces,
                  patterned features, optional amorphous overlayer), writers for each engine
  forward/
    geometric/    refraction-corrected geometric-phase model (fast, large fields of view)
    multislice/   grazing-incidence multislice with reflection-specific box (engine adapter layer:
                  custom numpy/cupy kernel as reference; abTEM and Prismatic adapters for cross-checks)
    dynamical/    interface to a surface-parallel dynamical reflection solver (sim-trhepd-rheed, GPL
                  Fortran, Ichimiya-type) and/or a Bragg-case Bloch-wave solver, for rocking curves
  optics/         dark-field selection (objective aperture in k-space), projection along k_out,
                  magnification and pixel mapping, reference-wave models R1/R2/R3, carrier, partial
                  coherence (source size, energy spread), hologram intensity, detector MTF and noise
  reconstruction/ sideband reconstruction shared with the experimental pipeline (carrier location on an
                  empty hologram, mask, apodisation, unwrapping, reference correction, ramp fitting with
                  preserved raw outputs)
  quantification/ phase-to-height with the refraction-corrected relation, wrap period and branch logic,
                  rocking-series inversion, terrace segmentation with uncertainties, no-step controls
  provenance/     manifest writer (versions, commits, seeds, precision, thread count, input hashes),
                  source-map validation, evidence labels in docstrings
  io/             assertion-based loaders (dataset names, axis order, units, plane of the wave)
configs/          CFG-A, CFG-B, CFG-O and per-experiment comparison configs
docs/             references.bib, source_map.tsv, physics_conventions.md, model_assumptions.md, ...
tests/            see section 8
```

## 4. Forward-model requirements

### 4.1 Geometry module (must exist before any simulation is run)

* Explicit `(hkl)` surface, `[uvw]` azimuth, outward normal, active rotation matrices, handedness and
  orthogonality assertions, reciprocal lattice, diamond structure factor with a forbidden-reflection guard
  (`F_hkl = 0` refuses (222), (666), (10,10,10), (002), (006) and so on).
* Relativistic wavelength from a named constants source; refraction with the relativistic `Delta`;
  critical angle; internal and external angles for every order of the specular rod; the accessibility
  guard `G.n_hat >= 2 k sin(theta_c)` for non-specular reflections; foreshortening; wrap period `h_2pi`.
* Reference implementation and numbers: `tools/reflection_step_phase_calculator.py` (25 checks).

### 4.2 Structure module

* Terraces built as truncations of one continuous lattice with stacking-correct lattice-translation steps;
  a Si(001) single-layer step implemented as the `4_1` screw relation (rotated dimer rows if a
  reconstruction is enabled). Terrace staircases must be continuous under the periodic boundary
  perpendicular to the beam (the inspected default 0,1,2,3 bilayers is not: there is a hidden 3-bilayer
  down-step at the cell edge).
* Options, each an explicit ASSUMPTION with a source: bulk termination; 2x1 dimer reconstruction of Si(001);
  amorphous SiO2/damage overlayer of given thickness and density; step-riser relaxation none.
* Patterned features: mesas/trenches with heights and edge profiles from PROJECT_INPUT item 13.

### 4.3 Grazing-incidence multislice (the finite-feature engine)

Requirements independent of the engine:

1. Semi-infinite emulation along the surface normal: no vacuum below the crystal; a smooth absorbing
   (imaginary potential) or apodising region on the bulk side and at the end faces, so that nothing
   escaping the crystal re-enters through the periodic boundary. Prismatic has no such primitive and its
   `absorbing_layers` keyword does not exist in prismatique (report D); this alone rules Prismatic out as
   the reference engine.
2. Vacuum margin above the surface larger than the illumination height plus `L_z tan(theta)`.
3. Illumination confined to a vacuum band (apodised sheet beam of height `H`, tilted by `theta_ext`),
   launched upstream of the crystal; the crystal starts downstream of the entrance plane. The footprint
   `H/tan(theta)` sets a minimum cell length along the beam (890 A for `H = 20 A` at 22.5 mrad).
4. Cell length along the beam also larger than the dynamical build-up length (refracted ray must reach a
   penetration depth of several nm: of order 0.1 to 0.4 um). Expect grids of order 1500 x 600 pixels and
   thousands of 1 A slices; GPU execution is required but routine.
5. Sampling: the OUTGOING beam angle must lie inside the anti-aliasing band (2/3 rule at 0.13 A gives
   64 mrad at 200 keV; Prismatic's half-Nyquist rule gives 48 mrad); the pixel size is a derived quantity,
   never an advisory constant; slice thickness commensurate with the crystal period along the beam.
6. Refraction is included automatically by the projected potential; the mean inner potential of the
   potential parameterisation actually used must be reported and compared with the sourced `V0`.
7. Absorption via a sourced optical potential (instruction file B15 warning: never a tuned parameter);
   frozen phonons optional, with intensity averaging after hologram formation and recorded seeds.
8. Output: the wave on a DECLARED plane (exit plane of the cell, no hidden propagation), per realisation,
   complex64 or complex128 stated, with axes, pixel sizes and tilt actually used stored in the file.
9. Exact propagator preferred (abTEM provides one; the paraxial error here is small but must be reported).

Engine plan: a small custom numpy/cupy multislice as the reference implementation (about 200 lines;
explicit absorber, band limit, tilt and output plane), benchmarked in a transmission configuration against
abTEM 1.1 and Prismatic, then used in reflection. abTEM is the preferred packaged cross-check (exact
propagator, 2/3 band limit, explicit exit wave, ensemble control); Prismatic is kept only as a documented
legacy benchmark with its true semantics (mid-plane wave, half-Nyquist band, static lattice, quantised
tilt list; upstream unmaintained since January 2026).

### 4.4 Dynamical reflection reference (the flat-surface truth)

A surface-parallel-slicing dynamical RHEED solver (Ichimiya-type; the open-source `sim-trhepd-rheed`
implements it) or a Bragg-case Bloch-wave solver provides rocking curves `|A(theta)|^2` and, where the
code exposes it, the reflection phase for the flat surface of each configuration. It is the benchmark for
the multislice engine in the flat-surface limit (peak positions calibrate refraction and the angle scale;
widths and resonance features test absorption and boundary handling). Which quantities the chosen solver
exposes must be verified from its documentation (UNVERIFIED here: only its README was readable).

### 4.5 Geometric-phase model

Fast model for large fields of view: `Delta_phi = -(k_out - k_in).R(r)` with refraction-corrected external
angles, an optional dynamical residual taken from the multislice engine near step risers, and explicit
detection of the invisibility condition (`g.R` integer) and of screw-related terraces where the model is
not valid. Used for experiment planning and for the rocking-series inversion.

## 5. Optics, hologram formation and reconstruction requirements

1. Dark-field selection: an objective aperture of semi-angle from PROJECT_INPUT item 4 applied in k-space
   around `k_out`; the aperture position and radius are recorded with the run.
2. Image formation: projection along `k_out` (surface coordinate `z_s = (x_0 - x)/tan(theta)`), then
   magnification and detector pixel mapping (anisotropic sampling stated on both axes); optional lens
   transfer (defocus, spherical aberration, chromatic envelope) applied ONCE, at a declared plane.
3. Reference-wave models R1, R2, R3 selectable by name; the intrinsic inclination `2 theta` between a vacuum
   reference and the specular object beam and its compensation are explicit inputs derived from the measured
   carrier fringe spacing and overlap width (PROJECT_INPUT item 16). A freely adjustable relative phase is a
   simulation parameter, not evidence of hardware phase control.
4. Partial coherence by intensity averaging over source-size, energy-spread (defocus) and phonon ensembles
   with the object and reference branches sharing each realisation; never averaging complex waves.
5. Detector: MTF, gain and Poisson noise at the recorded dose; raw and noisy holograms both saved.
6. Reconstruction: one code path for simulation and experiment; carrier located on an empty hologram;
   mask radius and apodisation recorded; raw wrapped phase, unwrapped phase, masks and fitted ramps all
   preserved; the resolution of the reconstruction (about three fringe spacings) reported.
7. Quantification: `h = Delta_phi lambda/(2 pi (sin theta_in,ext + sin theta_out,ext))` for the specular
   beam, with the wrap period and branch stated; rocking-series inversion for absolute heights; terrace
   segmentation with uncertainties from the measured fringe contrast and dose; refusal (not division) when
   the sensitivity `|q.n_hat|` is below the propagated uncertainty; no-step control on every dataset.

## 6. Provenance requirements

* `docs/references.bib` (verified entries separated from unverified candidates), `docs/source_map.tsv`
  (claim, source, locator, evidence, implementation, test, status), `docs/physics_conventions.md`,
  `docs/model_assumptions.md`, all kept current.
* Every run writes a manifest: package versions (`pip freeze`), engine commit and build flags, numeric
  precision, random seeds and thread count (Prismatic's phonon seeding depends on the thread index),
  SHA-256 of inputs and configuration, git commit of the repository, and the declared plane of every wave.
* Docstrings cite source IDs; evidence labels appear next to every physical constant.

## 7. Comparison protocol with the experiment

1. Calibration first: compare the measured rocking curve (PROJECT_INPUT item 9) with the dynamical
   reflection benchmark to fix the external angle scale and `V0`; report the residual.
2. Flat-region holograms: compare fringe contrast versus dose and the reference-corrected phase flatness
   with the simulated hologram under the declared reference model.
3. Steps: compare reconstructed phase steps versus glancing angle (rocking series) with the simulation;
   fit the height with the branch resolved; report the dynamical residual near risers.
4. Foreshortened geometry: compare feature positions along the beam after the `1/tan(theta)` mapping.
5. Blind protocol: processing parameters are frozen before the comparison; no tuning of the simulation
   to recover a known answer (instruction file section 9.8).
6. Uncertainty budget: `V0`, angle calibration, energy, fringe contrast, dose, mask radius, unwrapping.

## 8. Test suite (selected per change, instruction file section 10)

* Geometry: handedness, orthogonality, reciprocal vectors, forbidden reflections, Bragg and refracted
  angles, accessibility, foreshortening (T1 to T9, T15, T20).
* Propagation: vacuum plane-wave phase advance, inverse propagation, sampling and slice convergence, norm
  preservation for lossless stages, paraxial-versus-exact comparison.
* Boundaries: footprint and wrap-around assertions (T17 to T19), absorber effectiveness, no periodic-image
  contamination in the measurement band.
* Data handling: assertion-based loading (dataset names, axis order, units, plane, pixel size from file,
  tilt selection by value), round-trip for the supported schema.
* Holography: intensity-only recovery of independently specified object and reference fields with a
  known carrier and a non-ideal reference (T24, T25), carrier-location trap, resolution versus mask radius.
* Quantification: no-step control, positive and negative steps, near-invisibility condition, rocking-series
  branch recovery, small-denominator policy, sensitivity to angle and `V0` uncertainty.
* Ensembles: single realisation versus intensity average; convergence with the number of configurations.
* Inversion (later, ptychography): independent forward-model benchmarks, held-out conditions, gradient
  and adjoint checks.

## 9. Migration plan from the inspected repository

| Milestone | Deliverable | Depends on |
|---|---|---|
| M0 Honesty and provenance | Correct the inspected repository's documentation (mid-plane wave, forbidden (666), inaccessible (2,-2,0), inert absorber and thermal settings, tilt-index and pixel-size defects); pin versions; add loader assertions; keep CFG-A as a documented legacy benchmark | report D section 5.2 |
| M1 Physics core | `geometry/` and `quantification/` from the calculator; tests T1 to T23; source map entries | nothing |
| M2 Reflection forward model | Custom kernel with absorber and confined illumination; flat-surface rocking curves validated against the dynamical solver; convergence studies | M1, solver access |
| M3 Holography chain | R1/R2/R3, hologram formation, shared reconstruction, T24/T25 and the carrier trap | M1 |
| M4 Benchmarks | CFG-A bilayer steps (phase versus angle; double-contour contrast check), CFG-B a/4 and a/2 steps, patterned features, overlayer sensitivity | M2, M3 |
| M5 Experimental comparison | Calibration, blind comparison, uncertainty budget, paper figures | M4 and PROJECT_INPUT items 1 to 19 |
| M6 Reflection ptychography (optional) | Differentiable dynamical forward model; multiplicative-object algorithms explicitly not assumed valid | M2 |

## 10. Literature position (from `docs/agent_reports/B_literature.md`, index-level evidence only)

* Starting point: Osakabe et al. 1988 (P01) and 1989 (P02, GaAs(110), dislocation surface undulation,
  0.01 A precision claimed at abstract level), Osakabe 1992 review (P08, "phase shift of a Bragg-reflected
  electron wave", "geometrical path differences measured in units of wavelengths"), Banzhof and Herrmann
  1993 (P03), Banzhof, Herrmann and Lichte 1992 (P09: pi and 0.9 pi steps on Au(111) and Pt(111) with an
  image-side biprism). The content of P01 itself could not be read here.
* Theory to read before implementing: Peng and Cowley 1986/1988 (transmission-type multislice applied to
  the Bragg case), Ichimiya 1983 (surface-parallel slicing), Ma and Marks 1989 to 1992 (Bloch-wave Bragg
  case, multislice-versus-Bloch consistency in reflection), Yao and Cowley 1990 (Bragg-Bragg and
  Bragg-channelling resonances, double-contour step contrast), B07 and B08 chapters on dynamical RHEED.
* Methodological analogues: dark-field electron holography (Hytch et al. 2008, 2011; Lubk et al. 2014;
  Meissner et al. 2019 show that dynamical effects must be included even in transmission); X-ray CTR and
  Bragg ptychography (Zhu et al. 2015 on Pt(111) steps is the closest analogue); split-illumination
  holography (Tanigaki et al. 2012, 2014) for condenser-side biprisms; Blackburn and McLeod 2021 and
  Herring 2021/2022 for the group's public holography and diffracted-beam interferometry work.
* No published electron reflection-mode ptychography and no post-2015 reflection electron holography
  experiment was found, but the citation-graph search could not be run (blocked), so this is a search
  failure, not evidence of absence.

## 11. What this specification does not settle

* The content of Osakabe 1988 and of the Hitachi reflection-holography patent (reference-wave arrangement).
* The exact relativistic refraction and Bragg-case expressions as printed in B07/B08 (derived here, not read).
* Whether abTEM accepts a complex (absorptive) potential and tilts of 20 to 50 mrad with adequate accuracy
  (its docstring recommends below one degree; UNVERIFIED).
* Which quantities `sim-trhepd-rheed` exposes (phase of the reflected beams or intensities only).
* All PROJECT_INPUT items in `docs/06_project_inputs_required.md`.
