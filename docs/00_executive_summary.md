# Executive summary for Ali

Date: 2026-09-21 (revision 2, after two adversarial review passes). Subject: the simulation
repository `hussienba/si110-reflection-holography` (commit 6694959) and what a final theoretical
simulation repository must look like to be contrasted with the real reflection-mode dark-field
electron holography experiment, taking Osakabe's reflection holography as the starting point. Four
delegated audits (code, literature, physics, software provenance) were run and cross-checked, and two
adversarial reviews of the summary documents were applied; their full reports are under
`docs/agent_reports/`.

## Headline findings

1. The current repository does not simulate reflection holography. It is a transmission multislice
   of a thin silicon plate (8.5 nm declared, 8.9 nm realised) viewed edge-on, followed by Fourier
   selection of one spot of the simulated complex wave. There is no reference wave, no intensity
   hologram and no reconstruction; the reported "phase" is the argument of a filtered simulated field
   (instruction section 9.1 fails).
2. With its default cell, 81 percent of the incident wave (on the declared geometry; 85 percent on the
   realised atom positions) enters the crystal through the front end face; only 1 to 3 percent reaches
   the surface from the vacuum side; the declared 2 x 10 A vacuum is a 16.1 A periodic channel between
   plate images; the Laue-transmitted beam is collinear with the specular beam; and no Bragg-case
   reflection can develop over a slab that the refracted ray crosses by one bilayer. A reflection cell
   needs a semi-infinite emulation with an absorbing bulk-side region, illumination confined to the
   vacuum band and a length along the beam of 0.08 to 0.42 um (for penetration depths of 2 to 10 nm).
3. The physics targets are inconsistent: the "(666) specular condition" (correctly written (6,-6,6) for
   this surface) is a kinematically forbidden reflection; at the vacuum Bragg angle of any allowed order
   a bilayer step is invisible (phase 2 pi n), so at a bulk Bragg point the visible step signal is the
   refraction shift of the peak (mean inner potential), while at truncation-rod or resonance conditions
   it is the ordinary geometric path difference; the default target (2,-2,0) cannot connect two
   vacuum-propagating beams at all; and the phase-to-height formula ignores the 2 pi branch (wrap
   period 0.4 to 1.5 A), the sign, and the in-plane part of the step translation.
4. The software does not do what the scripts say. Reproduced against the pinned prismatique 0.0.1
   API (no engine run): the absorber keyword is rejected and silently dropped, the thermal settings are
   inert, the tilt window makes the engine simulate 1309 plane waves for a 74-point sweep, the
   reconstruction reads the wrong tilt index and uses a pixel size that is off by a factor of two, and
   the intensity file is NaN. Established by reading the pinned source, not executed: the saved wave is
   Fresnel back-propagated to the supercell mid-plane rather than being an exit wave, and the tilt
   runner writes no wavefunction at all because two keyword arguments that do not exist in prismatique
   0.0.1 make it fall back to "save nothing".
5. The reconstruction locks onto a sideband instead of the carrier for phase steps above 2.0 rad (the
   repository's own case is 2.09 rad), and its default plane detrend removes a quarter of a single step
   and nearly all of a staircase; the quantification has no uncertainty, no sign, no no-step control and
   silent defaults. With the repository's own defaults the end-to-end result on ideal synthetic data is
   0.12 A for a 3.14 A step. Forcing the true carrier bin, widening the aperture and disabling the
   detrend recovers the phase to 1.7 percent (2.130 rad against 2.094) but still returns only 0.80 A,
   because the 2 pi branch is never resolved (A report, section 5.5).

## What the final version must look like

The specification is `docs/05_final_repository_specification.md`. In short: a geometry module with
refraction, structure factors and guards (forbidden and inaccessible reflections, invisibility
condition, shadow lengths); stacking-correct step builders and named configurations (Si(111) benchmark
kept separate from the Si(001) patterned experiment); a reflection forward model with a validated
reflection cell (custom multislice kernel for the absorbing boundary, validated against abTEM before
use, a surface-parallel dynamical RHEED solver for flat-surface rocking curves, and a phase-validation
ladder because the measurand is a phase); an optics and holography chain (dark-field aperture,
projection with foreshortening and shadow masks, explicit reference-wave models R1/R2/R3,
illumination-convergence and drift envelopes, biprism Fresnel fringes and charging as declared options,
ensemble averaging after squaring, detector noise); one reconstruction code path shared with the
experimental data; a quantification module with the signed refraction-corrected relation, branch
resolution by rocking series or lattice constraint, shadow exclusion and propagated uncertainties; and
a provenance system (references, source map, conventions, assumptions, run manifests with licences)
with the test suite of the instruction file. The physics that the model must reproduce, with numbers,
is in `docs/03_physics_summary.md`; the reference calculator `tools/reflection_step_phase_calculator.py`
passes 25 self-checks.

## Osakabe as the starting point

Osakabe's own 1992 summary (P08, abstract-index level) describes the method as the phase shift of a
Bragg-reflected electron wave measured by holographic interferometry, where geometrical path
differences of the surface topography are measured in units of the wavelength. That is the kinematic
translation-covariance phase `Delta_phi = -(k_out - k_in).R` used here, with the external angles and
the vacuum wavelength. The 1988 paper itself (P01) could not be read in this environment: its surface,
energy, reflection, reference-wave arrangement and measured values are UNVERIFIED, and the reproduction
configuration (CFG-O) stays a placeholder until it is read. The Hitachi patent record suggests, at
second hand, a vacuum ("direct") reference wave passing beside the specimen; this is UNVERIFIED and
must not be stated as fact.

## What is needed from the laboratory

`docs/06_project_inputs_required.md` lists 22 items, nine of them blocking: the accelerating voltage
(1); the illumination convergence semi-angle (3), which alone decides whether nanometre features can
show phase contrast (a 10 nm step reaches 1 rad of phase spread at 0.02 mrad); the objective-aperture
semi-angle and which beam it selects (4); the detector pixel size and magnification (5); the external
glancing angle and its calibration (7); the beam azimuth (8); the surface orientation (11) and
preparation state (12), because oxide and ion-milling damage can suppress the Bragg-reflected object
wave entirely; and the reference-wave trajectory (15). The most valuable non-blocking input is a
measured rocking curve (9), because it fixes the angle scale and the mean inner potential together.

## Limitations of this analysis

* Every scholarly host was blocked by the analysis environment's network policy; no paper or book
  chapter was read. Literature evidence is index-level only and is labelled as such. The "no reflection
  electron holography since 1993" impression is a search failure, not a result.
* No multislice or dynamical reflection simulation was executed; software facts come from reading the
  version-matched source and exercising the Python API without the compiled engine, and each document
  states which facts were reproduced at the API level and which were only read in the source.
* The physics is derived from stated premises and reproduced numerically; before publication it must
  be checked against the dynamical RHEED chapters of Ichimiya and Cohen (B07) and Peng, Dudarev and
  Whelan (B08), and the mean inner potential of silicon must be sourced (assumed 12.0 V here;
  a 1 V change moves the bilayer step phase by 0.34 rad at the (4,-4,4) condition).

## Recommended next steps

1. Read P01, P08, P07 (open access) and the B07/B08 chapters; fill CFG-O; upgrade the evidence labels.
2. Supply the PROJECT_INPUT items; record a rocking curve of the selected reflection.
3. Build milestone M1 (geometry and quantification core, tests T1 to T23) from the calculator.
4. Build the reflection cell (M2), validate flat-surface rocking curves against a dynamical solver and
   the reflection phase against the analytic and two-beam rungs of the validation ladder, before any
   step or pattern is simulated.
5. Only then simulate holograms of Si(111) bilayer steps (the monatomic-step benchmark CFG-A; whether it
   matches Osakabe's own configuration is UNVERIFIED until P01 is read) and of the Si(001) patterned
   samples, process them with the experimental reconstruction code, and compare blind.
