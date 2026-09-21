# Executive summary for Ali

Date: 2026-09-21. Subject: the simulation repository `hussienba/si110-reflection-holography`
(commit 6694959) and what a final theoretical simulation repository must look like to be contrasted
with the real reflection-mode dark-field electron holography experiment, taking Osakabe's reflection
holography as the starting point. Four delegated audits (code, literature, physics, software
provenance) were run and cross-checked, and an adversarial review of the summary documents was applied;
their full reports are under `docs/agent_reports/`.

## Headline findings

1. The current repository does not simulate reflection holography. It is a transmission multislice
   of an 8.5 nm silicon plate viewed edge-on, followed by Fourier selection of one spot of the
   simulated complex wave. There is no reference wave, no intensity hologram and no reconstruction;
   the reported "phase" is the argument of a filtered simulated field (instruction section 9.1 fails).
2. With its default cell, 81 to 85 percent of the incident wave enters the crystal through the front
   end face; only 1 to 3 percent reaches the surface from the vacuum side; the declared 10 A vacuum is
   a 16 to 20 A periodic channel between plate images; the Laue-transmitted beam is collinear with the
   specular beam; and no Bragg-case reflection can develop over a slab that the refracted ray crosses
   by one bilayer. A reflection cell needs a semi-infinite emulation with an absorbing bulk-side
   region, illumination confined to the vacuum band and a length along the beam of order 0.1 to 0.4 um.
3. The physics targets are inconsistent: the "(666) specular condition" (correctly written (6,-6,6) for this surface) is a
   kinematically forbidden reflection; at the vacuum Bragg angle of any allowed order a bilayer step is
   invisible (phase 2 pi n), so at a bulk Bragg point the visible step signal is the refraction shift of
   the peak (mean inner potential), while at truncation-rod or resonance conditions it is the ordinary
   geometric path difference; the
   default target (2,-2,0) cannot connect two vacuum-propagating beams at all; and the phase-to-height
   formula ignores the 2 pi branch (wrap period 0.4 to 1.5 A), the sign, and the in-plane part of the
   step translation.
4. The software does not do what the scripts say: the saved wave is Fresnel back-propagated to the
   supercell mid-plane, not an exit wave; the tilt runner writes no wavefunction at all (two nonexistent
   keyword arguments make it fall back to "save nothing"); the reconstruction reads the wrong tilt
   index and uses a pixel size that is off by a factor of two; the absorber and the thermal settings
   are silently inert; the intensity file is NaN. All of this was reproduced against the pinned
   prismatique 0.0.1 API and the Prismatic source, without running the engine.
5. The reconstruction locks onto a sideband instead of the carrier for phase steps above 2.0 rad
   (the repository's own case is 2.09 rad), and its default plane detrend removes a quarter of a
   single step and nearly all of a staircase; the quantification has no uncertainty, no sign, no
   no-step control and silent defaults. The best end-to-end result on ideal synthetic data with
   the defaults is 0.12 A for a 3.14 A step.

## What the final version must look like

The specification is `docs/05_final_repository_specification.md`. In short: a geometry module with
refraction, structure factors and guards (forbidden and inaccessible reflections, invisibility
condition); stacking-correct step builders and named configurations (Si(111) benchmark kept separate
from the Si(001) patterned experiment); a reflection forward model with a validated reflection cell
(custom multislice kernel for the absorbing boundary, validated against abTEM before use, a surface-parallel
dynamical RHEED solver for flat-surface rocking curves, and a phase-validation ladder because the
measurand is a phase); an optics and holography chain
(dark-field aperture, projection with foreshortening and shadow masks, explicit reference-wave models
R1/R2/R3, illumination-convergence and drift envelopes, ensemble averaging after squaring, detector noise); one reconstruction code path shared with the experimental
data; a quantification module with the refraction-corrected relation, branch resolution by rocking
series or lattice constraint, and propagated uncertainties; and a provenance system (references,
source map, conventions, assumptions, run manifests) with the test suite of the instruction file.
The physics that the model must reproduce, with numbers, is in `docs/03_physics_summary.md`; the
reference calculator `tools/reflection_step_phase_calculator.py` passes 25 self-checks.

## Osakabe as the starting point

Osakabe's own 1992 summary (P08, abstract level) states the method: the phase shift of a
Bragg-reflected electron wave measured by holographic interferometry, where geometrical path
differences of the surface topography are measured in units of the wavelength. That is the kinematic
translation-covariance phase `Delta_phi = -(k_out - k_in).R` used here, with the external angles and
the vacuum wavelength. The 1988 paper itself (P01) could not be read in this environment: its surface,
energy, reflection, reference-wave arrangement and measured values are UNVERIFIED, and the reproduction
configuration (CFG-O) stays a placeholder until it is read. The Hitachi patent record suggests, at
second hand, a vacuum ("direct") reference wave passing beside the specimen; this is UNVERIFIED and
must not be stated as fact.

## What is needed from the laboratory

`docs/06_project_inputs_required.md` lists 22 items. The blocking ones: accelerating voltage, the
selected reflection and objective-aperture angle, the external glancing angle and its calibration
(a measured rocking curve is the single most valuable input, because it fixes the angle scale and the
mean inner potential), the beam azimuth, the sample orientation and surface state (oxide and
ion-milling damage can suppress the Bragg-reflected object wave entirely at grazing incidence), the
pattern heights, the reference-wave trajectory, and the measured carrier fringe spacing and overlap.

## Limitations of this analysis

* Every scholarly host was blocked by the analysis environment's network policy; no paper or book
  chapter was read. Literature evidence is index-level only and is labelled as such. The "no reflection
  electron holography since 1993" impression is a search failure, not a result.
* No multislice or dynamical reflection simulation was executed; software facts come from reading the
  version-matched source and exercising the Python API without the compiled engine.
* The physics is derived from stated premises and reproduced numerically; before publication it must
  be checked against the dynamical RHEED chapters of Ichimiya and Cohen (B07) and Peng, Dudarev and
  Whelan (B08), and the mean inner potential of silicon must be sourced (assumed 12.0 V here;
  a 1 V change moves the bilayer step phase by 0.34 rad at the (4,-4,4) condition).

## Recommended next steps

1. Read P01, P08, P07 (open access) and the B07/B08 chapters; fill CFG-O; upgrade the evidence labels.
2. Supply the PROJECT_INPUT items; record a rocking curve of the selected reflection.
3. Build milestone M1 (geometry and quantification core, tests T1 to T23) from the calculator.
4. Build the reflection cell (M2), validate flat-surface rocking curves against a dynamical solver and the
   reflection phase against the analytic and two-beam rungs of the validation ladder, before any step or
   pattern is simulated.
5. Only then simulate holograms of Si(111) bilayer steps (Osakabe-type benchmark) and of the Si(001)
   patterned samples, process them with the experimental reconstruction code, and compare blind.
