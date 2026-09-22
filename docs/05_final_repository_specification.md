# Specification: what the final theoretical simulation repository must look like

Status: 2026-09-21, version 0.2 (orchestrator synthesis of reports A to D, independent checks, and
the corrections required by the adversarial review `docs/agent_reports/E_review.md`); version 0.3,
2026-09-22 (Phase 1 literature pass with network access: reports B3 and L1 to L5 under
`docs/agent_reports/`).
Purpose: define the repository that will produce simulated observables to be contrasted with the
real reflection-mode dark-field electron holography experiment on silicon surfaces (Osakabe-type
measurement), starting from the inspected repository `hussienba/si110-reflection-holography`
(commit 6694959) and its instruction file. Everything here follows the source policy of that
instruction file; unresolved items are labelled PROJECT_INPUT, ASSUMPTION or UNVERIFIED.
Reflection indices are written with their signs: the specular rod of the (1,-1,1) surface is
`(n,-n,n)`, not `(n,n,n)` (see `docs/physics_conventions.md`).

## 0. Acceptance criteria (definition of "final")

The repository is final when all of the following hold:

1. It produces, for a named configuration, the full observable chain: reflectivity amplitude and phase
   versus glancing angle (rocking curve), dark-field image wave with correct foreshortening and shadow
   masks, reference wave under a declared model, ensemble-averaged hologram intensity with detector
   effects, reconstructed phase produced by the same code used on the experimental holograms, and
   quantified heights with uncertainties and branch information.
2. The forward model passes the physics test plan (`docs/03_physics_summary.md` section 7; checks
   T1 to T25 with the tolerances stated in the calculator, plus the qualitative checks), the
   phase-validation ladder of section 4.4 (each rung with a tolerance recorded in
   `configs/benchmarks.yaml` when the rung is implemented), and a flat-surface rocking-curve benchmark
   against an independent dynamical reflection solver. If that solver exposes only intensities, the
   rocking-curve criterion is restricted to peak positions and widths and that restriction is recorded;
   the phase is then validated by rungs 1 to 3 of the ladder.
3. A step benchmark on the translation-related steps (the CFG-B a/2 double-layer step on Ali's Si(001),
   and the CFG-A bilayer as the validation case) reproduces the refraction-corrected geometric phase
   versus glancing angle with a dynamical residual below a threshold recorded in
   `configs/benchmarks.yaml` (proposed initial value 0.1 rad, ASSUMPTION). For the CFG-B a/4
   single-layer step, whose terraces are screw-related (section 2 of `docs/03_physics_summary.md`,
   assumption B4), the geometric phase does not hold: the dynamical phase difference between the two
   terraces is computed and reported, not compared with the geometric phase.
   Comparison with Osakabe 1988 is deferred until the body of P01 is read. Its abstract (read on the
   publisher page) gives a Pt(111) surface, so CFG-O is not a silicon benchmark; its energy,
   reflection, glancing angle and measured values are still UNVERIFIED.
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
specular condition (6,-6,6) is a forbidden reflection; its default target (2,-2,0) is inaccessible in
reflection geometry; and its phase-to-height step cannot resolve the 2 pi branch. The itemised audit is
in `docs/01_repository_audit.md` and the agent reports under `docs/agent_reports/`.

## 2. Named configurations (kept separate; instruction file section 2)

| ID | Name | Surface, azimuth | Steps and features | Specular conditions | Status |
|---|---|---|---|---|---|
| CFG-A | `si111_cleaved_110azimuth` | (1,-1,1) surface, beam azimuth [110] | lattice-translation bilayer steps `h = m d_111`, `R = m (a/2)[1,0,1]` (stacking-correct in-plane shift); step edges parallel or transverse to the beam (transverse edges shadow 230 A per bilayer at (4,-4,4), 102 A at (8,-8,8)) | (4,-4,4), (5,-5,5), (7,-7,7), (8,-8,8); (3,-3,3) is allowed but exits at 8.6 mrad, barely above `theta_c`, with 116x foreshortening, so it is not recommended; never (6,-6,6) or (2,-2,2) | benchmark inherited from the inspected repository; geometry consistent (normal.beam = 0) |
| CFG-B | `si001_patterned` | (001) surface, 200 keV (PROJECT_INPUT, supplied), azimuth [110] or [100] (PROJECT_INPUT item 8) | single-layer `a/4` steps (screw-related terraces, dynamical difference expected), double-layer `a/2` steps, patterned mesas/trenches of nm height (PROJECT_INPUT item 13; a 10 nm mesa shadows 444 nm at 22.5 mrad and 733 nm at the (4,-4,4) angle), optional oxide/amorphous overlayer (item 12) | (008) as the proposed working condition (PROJECT_INPUT item 9) (theta_int 18.5 mrad, theta_ext 16.5 mrad at V0 = 12 V, wrap period 0.76 A, foreshortening 61x); (0,0,12) as the second condition; (004) exits at 3.9 mrad and is not usable on an overlayer-covered surface; (002), (006), (0,0,10) forbidden | Ali's experiment; remaining unknowns listed in `docs/06_project_inputs_required.md` |
| CFG-O | `osakabe_1988_reproduction` | Pt(111) at glancing incidence (P01 abstract, sentence 2, `+ABSTRACT(publisher)`; not silicon, so no Si structure, `V0` or structure factor may be reused); azimuth UNVERIFIED | monatomic-height steps, sensitivity of the order of 0.01 nm (P01 abstract, sentence 4) | energy, reflection order and glancing angle UNVERIFIED; reference: two regions of the reflection image overlapped by an electron biprism, i.e. a self-reference of type R2 (the R2 reading is DERIVED_HERE); optical reconstruction (abstract, sentence 3) | placeholder: every field not listed here fails on load until the body of P01 (upload 1) and P08 (upload 2) are read; source map SM22 |

Each configuration is a versioned YAML/JSON file with every parameter labelled by evidence level.

## 3. Architecture

```
reflection_holo/
  geometry/       crystal, surface, rotations, reciprocal lattice, structure factors, Bragg/rod
                  conditions, refraction, accessibility, foreshortening, shadow lengths (pure numpy)
  structure/      slab and terrace builders (stacking-correct steps, Si(001) screw-related terraces,
                  patterned features, optional amorphous overlayer), writers for each engine
  forward/
    geometric/    refraction-corrected geometric-phase model with visibility ray-tracing (fast)
    multislice/   grazing-incidence multislice with reflection-specific box (engine adapter layer:
                  custom numpy/cupy kernel; abTEM and Prismatic adapters for cross-checks)
    dynamical/    interface to a surface-parallel dynamical reflection solver (sim-trhepd-rheed, GPL
                  Fortran, Ichimiya-type) and a Bragg-case Bloch-wave two-beam solver (for phases)
  optics/         dark-field selection (objective aperture in k-space), projection along k_out with
                  shadow masks, magnification and pixel mapping, reference-wave models R1/R2/R3,
                  carrier, biprism Fresnel fringes and overlap width, partial coherence (source size,
                  convergence, energy spread), drift envelope, charging phase option, hologram intensity,
                  detector MTF and noise
  reconstruction/ sideband reconstruction shared with the experimental pipeline (carrier location on an
                  empty hologram, mask, apodisation, unwrapping, reference correction, ramp fitting with
                  preserved raw outputs)
  quantification/ signed phase-to-height with the refraction-corrected relation, wrap period and branch
                  logic, rocking-series inversion, terrace segmentation with uncertainties, shadow
                  exclusion, no-step controls
  provenance/     manifest writer (versions, commits, licences, seeds, precision, thread count, input
                  hashes), source-map validation, evidence labels in docstrings
  io/             assertion-based loaders (dataset names, axis order, units, plane of the wave)
configs/          CFG-A, CFG-B, CFG-O, benchmarks.yaml (tolerances), per-experiment comparison configs
docs/             references.bib, source_map.tsv, physics_conventions.md, model_assumptions.md, ...
tests/            see section 8
```

## 4. Forward-model requirements

### 4.1 Geometry module (must exist before any simulation is run)

* Explicit `(hkl)` surface, `[uvw]` azimuth, outward normal, active rotation matrices, handedness and
  orthogonality assertions, reciprocal lattice, diamond structure factor with a forbidden-reflection guard
  (`F_hkl = 0` refuses (2,-2,2), (6,-6,6), (10,-10,10) on the CFG-A rod and (002), (006), (0,0,10) on the CFG-B rod).
* Relativistic wavelength from a named constants source; refraction with the relativistic `Delta`
  (`T` in eV); the internal escape angle `theta_c`; internal and external angles for every order of the
  specular rod; the accessibility guard `G.n_hat >= 2 dK` for non-specular reflections; foreshortening;
  wrap period `h_2pi`; shadow length `h/tan(theta_ext)`.
* Reference implementation and numbers: `tools/reflection_step_phase_calculator.py` (25 checks).

### 4.2 Structure module

* Terraces built as truncations of one continuous lattice with stacking-correct lattice-translation steps;
  a Si(001) single-layer step implemented as the `4_1` screw relation (rotated dimer rows if a
  reconstruction is enabled). Terrace staircases must be continuous under the periodic boundary
  perpendicular to the beam (the inspected default 0,1,2,3 bilayers is not: there is a hidden 3-bilayer
  down-step at the cell edge).
* Options, each an explicit ASSUMPTION with a source: bulk termination; 2x1 dimer reconstruction of Si(001);
  amorphous SiO2/damage overlayer of given thickness and density; step-riser relaxation none.
* Patterned features: mesas/trenches with heights and edge profiles from PROJECT_INPUT item 13, with the
  shadowed strips computed from the geometry for every incidence angle.

### 4.3 Grazing-incidence multislice (the finite-feature engine)

Requirements independent of the engine (numbers DERIVED_HERE, source-map rows SM15 and SM16):

1. Semi-infinite emulation along the surface normal: no vacuum below the crystal; a smooth absorbing
   (imaginary potential) or apodising region on the bulk side and at the end faces, so that nothing
   escaping the crystal re-enters through the periodic boundary. Prismatic has no such primitive and its
   `absorbing_layers` keyword does not exist in prismatique (report D); this alone rules Prismatic out as
   the reference engine.
2. Vacuum margin above the surface larger than the illumination height plus `L_z tan(theta)`.
3. Illumination confined to a vacuum band (apodised sheet beam of height `H`, tilted by `theta_ext`),
   launched upstream of the crystal; the crystal starts downstream of the entrance plane. The footprint
   `H/tan(theta)` sets a minimum cell length along the beam (889 A for `H = 20 A` at 22.5 mrad).
4. Cell length along the beam also larger than the dynamical build-up length: the refracted ray must
   reach a normal penetration depth of 2 to 10 nm, i.e. 0.08 to 0.42 um at `theta_int = 24 mrad`.
   Expect grids of order 1500 x 600 pixels (0.13 A over 200 A by 80 A) and thousands of 1 A slices;
   GPU execution is required but routine.
5. Sampling: the OUTGOING beam angle must lie inside the anti-aliasing band (2/3 rule at 0.13 A gives
   64 mrad at 200 keV; Prismatic's half-Nyquist rule gives 48 mrad); the pixel size is a derived quantity,
   never an advisory constant; slice thickness commensurate with the crystal period along the beam.
6. Refraction is included automatically by the projected potential; the mean inner potential of the
   potential parameterisation actually used must be computed, reported and compared with the sourced
   `V0` (source-map row SM17). The projected atomic potential (a Kirkland- or Peng-type
   parameterisation, its Fourier-space construction and sub-slice sampling) is a sourced physical input
   and the largest part of any custom kernel, not boilerplate.
7. Absorption via a sourced optical potential (the warning attached to [B15] in the instruction file:
   never a tuned parameter); frozen phonons optional, with intensity averaging after hologram formation
   and recorded seeds.
8. Output: the wave on a DECLARED plane (exit plane of the cell, no hidden propagation), per realisation,
   complex64 or complex128 stated, with axes, pixel sizes and tilt actually used stored in the file.
9. Exact propagator preferred (abTEM provides one). The paraxial Fresnel error `k dz sin^4(alpha)/8`
   over a 198 A cell is 0.026 rad at the 45 mrad specular scattering angle and 0.106 rad at the
   64 mrad band edge; it is common-mode between terraces but not negligible for absolute phases, and
   must be reported for whichever engine is used.

Engine plan. A custom numpy/cupy multislice kernel provides the controls no packaged code exposes
(explicit absorber, band limit, tilt as an entrance-plane Fourier component or as a propagator shear,
declared output plane, per-realisation output). Because it is the least-scrutinised code in the stack,
it is not trusted until it agrees with abTEM 1.1 to a stated tolerance in both a transmission
configuration and a reflection-like configuration that abTEM can still run (crystal thick enough that
the absorber is inert); only then is the absorber enabled. abTEM is the preferred packaged cross-check
(exact propagator with evanescent handling, 2/3 band limit, explicit exit wave, ensemble control), but
its propagator-shear tilt is documented as "should generally not exceed one degree" (about 17 mrad)
while 24 to 48 mrad are needed here: a convergence test comparing the shear tilt against an
entrance-plane Fourier-component tilt at 24 and 48 mrad is part of milestone M2, and if abTEM fails it
the cross-check engine changes. Prismatic is kept only as a documented legacy benchmark with its true
semantics (mid-plane wave, half-Nyquist band, static lattice, quantised tilt list; upstream
unmaintained since January 2026).

### 4.4 Dynamical reflection reference and the phase-validation ladder

A surface-parallel-slicing dynamical RHEED solver (Ichimiya-type; the open-source `sim-trhepd-rheed`
implements it) or a Bragg-case Bloch-wave solver provides rocking curves `|A(theta)|^2` for the flat
surface of each configuration: peak positions calibrate refraction and the angle scale; widths and
resonance features test absorption and boundary handling. `sim-trhepd-rheed`, as vendored for the P49
benchmark, and its P49 fork `trhepd-opt` (GPL-3.0) compute the complex reflection amplitudes but write
only intensities (SECTION_READ of the code, L2 rows D19, D19b; the current upstream release was not
checked); exposing `arg A` is a small output change. P49 (Kudo, Yamamoto and Hoshi) recasts the
boundary-value problem as a matrix initial-value problem for the full (non-paraxial) Schroedinger
equation and returns the complex amplitude `rho(0)` (preprint Eq. (36)); it validates intensities
only, and its notation implies an `exp(+i omega t)` time factor, so its phases must be conjugated
before comparison with this repository's convention (DERIVED_HERE, UNVERIFIED until rung 1 below is
run). Source map SM19.

Because the measurand is a phase, intensity agreement is not sufficient. The reflection PHASE of the
multislice engine is validated by a ladder that needs no new reading:

1. Refraction-only analytic limit: a structureless slab whose potential is the constant `V0` reflects
   with an analytically known amplitude and phase (one-dimensional step barrier in the surface-normal
   momentum); this isolates the propagator and the boundary treatment from the lattice.
2. Bragg-case Bloch-wave two-beam solution for one allowed reflection, which gives `arg A` in closed
   form across the Darwin plateau; the multislice must reproduce the phase sweep, not only the width.
3. Null tests with an exact expected phase: a step of exactly `h_2pi` gives zero phase step; a
   lattice-translation step at an exact vacuum Bragg angle gives zero; reversing the step reverses the sign.

Agreement between the geometric-phase model and the multislice near a step is a consistency check
(both rest on the same translation-covariance identity), not an independent validation.

### 4.5 Geometric-phase model

Fast model for large fields of view: `Delta_phi = -(k_out - k_in).R(r)` with refraction-corrected external
angles, visibility ray-tracing (shadowed strips of length `h/tan(theta)` behind transverse up-steps are
masked, computed at the actual operating angle), an optional dynamical residual taken from the multislice engine near step risers, and explicit
detection of the invisibility condition (`g.R` integer) and of screw-related terraces where the model is
not valid. Used for experiment planning and for the rocking-series inversion.

## 5. Optics, hologram formation and reconstruction requirements

1. Dark-field selection: an objective aperture of semi-angle from PROJECT_INPUT item 4 applied in k-space
   around `k_out`; the aperture position and radius are recorded with the run.
2. Image formation: projection along `k_out` (surface coordinate `z_s = (x_0 - x)/tan(theta)` with
   `x_0` the exit-plane height of a feature at `z_s = 0`), shadow masks, then magnification and detector
   pixel mapping (anisotropic sampling stated on both axes); optional lens transfer (defocus, spherical
   aberration, chromatic envelope) applied ONCE, at a declared plane.
3. Reference-wave models R1, R2, R3 selectable by name; the intrinsic inclination `2 theta_ext` between a
   vacuum reference and the specular object beam and its compensation are explicit inputs derived from
   the measured carrier fringe spacing and overlap width (PROJECT_INPUT item 16). A freely adjustable
   relative phase is a simulation parameter, not evidence of hardware phase control. Published
   arrangements (source map SM21, SM22): R1 is the Hitachi patent arrangement US 4,998,788 (a direct
   wave that does not illuminate the specimen, compensated either by objective over-focus with one
   diverging image-side biprism and a two-hole aperture, with image offset `d = Cs alpha^3 -
   Delta f alpha`, or by a condenser-side biprism that pre-tilts the reference by the sum of the
   incidence and reflection angles); R2 is how the P01 abstract is read here (two regions of the
   reflection image overlapped by a biprism; the R2 reading is DERIVED_HERE). An R1 reference must pass the dark-field objective
   aperture: the model must declare whether it uses a second aperture hole, a condenser-biprism
   pre-tilt of `2 theta_ext`, or no aperture, because an aperture centred on `k_out` blocks an
   untilted vacuum reference (DERIVED_HERE, L1 inference I6).
4. Partial coherence by intensity averaging over source-size, illumination-convergence, energy-spread
   (defocus) and phonon ensembles with the object and reference branches sharing each realisation; never
   averaging complex waves. The convergence semi-angle is a first-order contrast limit for tall features
   (1 rad of phase spread at 0.64 mrad for a bilayer, 0.20 mrad for 1 nm, 0.020 mrad for 10 nm).
5. Instrument artefacts that the experiment will contain and the hologram model must offer as declared
   options: the biprism's own Fresnel fringes and finite overlap width; specimen drift during the exposure
   as a coherent envelope loss; specimen charging as an added, slowly varying phase (ASSUMPTION B8 and
   PROJECT_INPUT item 22).
6. Detector: MTF, gain and Poisson noise at the recorded dose; raw and noisy holograms both saved.
7. Reconstruction: one code path for simulation and experiment; carrier located on an empty hologram;
   mask radius and apodisation recorded; raw wrapped phase, unwrapped phase, masks and fitted ramps all
   preserved; the resolution of the reconstruction (about three fringe spacings) reported.
8. Quantification: `h = -Delta_phi lambda/(2 pi (sin theta_in,ext + sin theta_out,ext))` for the
   specular beam in the `exp(+ik.r)` convention of `docs/physics_conventions.md` (a down-step must
   reverse the sign; this is a required unit test), with the wrap period and branch stated; rocking-series
   inversion for absolute heights; terrace segmentation with uncertainties from the measured fringe
   contrast and dose; shadowed strips excluded; refusal (not division) when the sensitivity `|q.n_hat|`
   is below the propagated uncertainty; no-step control on every dataset.

## 6. Provenance requirements

* `docs/references.bib` (verified entries separated from unverified candidates), `docs/source_map.tsv`
  (claim, source, locator, evidence, implementation, test, status), `docs/physics_conventions.md`,
  `docs/model_assumptions.md`, all kept current.
* Every run writes a manifest: package versions (`pip freeze`), engine commit and build flags and
  licence (Prismatic and prismatique are GPL; `sim-trhepd-rheed` is GPL; the distribution licence of this
  repository must be decided against them), numeric precision, random seeds and thread count (Prismatic's
  phonon seeding depends on the thread index), SHA-256 of inputs and configuration, git commit of the
  repository, and the declared plane of every wave.
* Docstrings cite source IDs; evidence labels appear next to every physical constant.

## 7. Comparison protocol with the experiment

1. Calibration first: compare the measured rocking curve (PROJECT_INPUT item 9) with the dynamical
   reflection benchmark to fix the external angle scale and `V0`; report the residual.
2. Flat-region holograms: compare fringe contrast versus dose and the reference-corrected phase flatness
   with the simulated hologram under the declared reference model; test for charging drift (item 22).
3. Steps: compare reconstructed phase steps versus glancing angle (rocking series) with the simulation;
   fit the height with the branch resolved; report the dynamical residual near risers; exclude shadows.
4. Foreshortened geometry: compare feature positions and shadow lengths along the beam after the
   `1/tan(theta)` mapping.
5. Blind protocol: processing parameters are frozen before the comparison; no tuning of the simulation
   to recover a known answer (instruction file section 9.8).
6. Uncertainty budget: `V0`, angle calibration, illumination convergence, energy, fringe contrast, dose,
   mask radius, unwrapping, drift, charging.

## 8. Test suite (selected per change, instruction file section 10)

* Geometry: handedness, orthogonality, reciprocal vectors, forbidden reflections (T7 to T9), Bragg and
  refracted angles (T4 to T6), accessibility (T15), wrap period (T14), foreshortening (T20),
  wavelength (T1 to T3), shadow length equals `h/tan(theta)` at the operating angle.
* Propagation: vacuum plane-wave phase advance, inverse propagation, sampling and slice convergence, norm
  preservation for lossless stages, paraxial-versus-exact comparison (expected 0.026 rad at 45 mrad
  over 198 A), shear-tilt versus Fourier-component tilt at 24 and 48 mrad.
* Boundaries: footprint and wrap-around assertions (T17 to T19), sampling ceilings (T21, T22), absorber
  effectiveness, no periodic-image contamination in the measurement band.
* Phase validation ladder (section 4.4): refraction-only slab, two-beam Bragg-case phase sweep, null tests.
* Data handling: assertion-based loading (dataset names, axis order, units, plane, pixel size from file,
  tilt selection by value), round-trip for the supported schema.
* Holography: intensity-only recovery of independently specified object and reference fields with a
  known carrier and a non-ideal reference (T24, T25), carrier-location trap, resolution versus mask radius,
  Fresnel-fringe and drift options.
* Quantification: step phases (T10 to T13), no-step control, positive and negative steps (sign test),
  near-invisibility condition (T16), rocking-series branch recovery (T23), small-denominator policy, sensitivity
  to angle, convergence and `V0` uncertainty, shadow exclusion.
* Ensembles: single realisation versus intensity average; convergence with the number of configurations.
* Inversion (later, ptychography): independent forward-model benchmarks, held-out conditions, gradient
  and adjoint checks.

## 9. Migration plan from the inspected repository

| Milestone | Deliverable | Depends on |
|---|---|---|
| M0 Honesty and provenance | Correct the inspected repository's documentation (mid-plane wave, forbidden (6,-6,6), inaccessible (2,-2,0), inert absorber and thermal settings, tilt-index and pixel-size defects, runner writing no output); pin versions; add loader assertions; keep CFG-A as a documented legacy benchmark | report D section 5.2, report A section 7 |
| M1 Physics core | `geometry/` and `quantification/` from the calculator; tests T1 to T25 and the shadow-length test (Ali's Phase 2 specification, PROJECT_INPUT, Ali, 2026-09-22; T24 and T25 are re-run in M3 with the full holography chain); source map entries | nothing |
| M2 Reflection forward model | Custom kernel with absorber and confined illumination, validated against abTEM before the absorber is enabled; abTEM tilt-range test at 24 and 48 mrad; flat-surface rocking curves against the dynamical solver; phase-validation ladder; convergence studies | M1, solver access |
| M3 Holography chain | R1/R2/R3, hologram formation with Fresnel-fringe, drift and charging options, shared reconstruction, T24/T25 and the carrier trap | M1 |
| M4 Benchmarks | CFG-A bilayer steps (phase versus angle; double-contour contrast check; transverse steps with shadows), CFG-B a/4 and a/2 steps, patterned features, overlayer sensitivity | M2, M3 |
| M5 Experimental comparison | Calibration, blind comparison, uncertainty budget, paper figures | M4 and PROJECT_INPUT items 1 to 22 |
| M6 Reflection ptychography (optional) | Differentiable dynamical forward model; multiplicative-object algorithms explicitly not assumed valid | M2 |

## 10. Literature position (revision 3: `docs/02_literature_position.md`)

* Starting point: P01 is known from its abstract only (Pt(111), two regions of the reflection image
  overlapped by a biprism, optical reconstruction, sensitivity of the order of 0.01 nm); P02 and P03
  from their metadata only (P02E, read, gives GaAs(110) and the (880) reflection for P02); P08 and P09
  from their PubMed abstracts (P08: the phase shift of a Bragg-reflected wave measured by holographic
  interferometry, path differences in units of the wavelength; P09: pi and 0.9 pi steps on Au(111) and
  Pt(111) with an image-side biprism, interpreted in terms of refraction).
* Theory to read before implementing (identities Crossref-verified, none read): Peng and Cowley 1986/1988 (transmission-type multislice applied to
  the Bragg case), Ichimiya 1983 (surface-parallel slicing), Ma and Marks 1989 to 1992 (Bloch-wave Bragg
  case, multislice-versus-Bloch consistency in reflection), Yao and Cowley 1990 (Bragg-Bragg and
  Bragg-channelling resonances, double-contour step contrast), B07 and B08 chapters on dynamical RHEED.
* Methodological analogues: dark-field electron holography (Hÿtch et al. 2008 and 2011, not read; their
  2010 companion, read in sections 1-2; Lubk et al. 2014 and Meißner et al. 2019, not read, are recorded at index level in
  report B as showing that dynamical effects must be included even in transmission); X-ray CTR and
  Bragg ptychography (Zhu et al. 2015 on Pt(111) steps is the closest analogue); split-illumination
  holography (Tanigaki et al. 2012, 2014) for condenser-side biprisms; Blackburn and McLeod 2021 and
  Herring 2021/2022 for the group's public holography and diffracted-beam interferometry work.
* After 1993 the citation graph and the searches of report L4 found reflection interferometry only by
  the Tokyo Institute of Technology group (Si(111)7x7, 2001 to 2003) and no electron reflection-mode
  ptychography; this is an absence in the databases searched, not a proof of absence.

## 11. What this specification does not settle

* The body of Osakabe 1988 (energy, reflection, glancing angle, phase relation and sign, measured
  values); the patent is now read (SM21) and the P01 abstract gives the surface and the biprism overlap of two
  image regions, read here as a self-reference (DERIVED_HERE; SM22).
* The exact relativistic refraction and Bragg-case expressions as printed in B07/B08 (derived here, not read).
* Whether abTEM accepts a complex (absorptive) potential and tilts of 24 to 48 mrad with adequate accuracy
  (its docstring recommends below one degree; UNVERIFIED; tested in M2).
* Whether the current upstream `sim-trhepd-rheed` release writes complex amplitudes (the vendored copy
  and the P49 fork compute them and write intensities only), and the sign convention of P49's phases.
* The dynamical residual threshold of acceptance criterion 3 (0.1 rad proposed, ASSUMPTION).
* All PROJECT_INPUT items in `docs/06_project_inputs_required.md`.
