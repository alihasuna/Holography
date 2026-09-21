# Laboratory inputs the simulation cannot supply (PROJECT_INPUT list)

Status: revision 2, 2026-09-21. Each item is a quantity that no physics derivation and no repository
file can provide. Until it is supplied by the laboratory, the corresponding model parameter is an
ASSUMPTION and every result that depends on it must carry that label (instruction file
sections 1.4, 2, 9.4). Items marked (blocking) prevent a quantitative comparison with experiment.

## A. Microscope and beam

1. (blocking) Accelerating voltage used for the reflection holograms and its stability.
2. Energy spread (FWHM, eV) and effective source size or measured spatial-coherence width at the specimen. (Energy spread is a minor effect: below 0.003 rad of step phase even for a 10 nm step at 0.7 eV.)
3. (blocking) Illumination convergence semi-angle at the specimen (mrad) for holography and for REM imaging. The step phase changes by `(4 pi h/lambda) cos(theta)` per radian of incidence angle, so the convergence produces an irreducible phase spread: 1 rad of spread at 0.64 mrad for a 3.1 A bilayer, 0.20 mrad for a 1 nm step, 0.020 mrad for a 10 nm step (200 keV). This decides whether nanometre-scale features can show any phase contrast at all.
4. (blocking) Objective-aperture semi-angle (mrad) and which reflected beam it selects: the specular (00) rod at which Bragg order, a surface-resonance condition, or a non-specular rod/bulk reflection.
5. (blocking) Image pixel size at the detector (nm/pixel, both axes) and the magnification for holograms.
6. Detector: type, MTF or its published parameters, gain, dose per hologram (electrons/pixel), exposure time, drift during exposure (drift enters the model as a coherent envelope loss, not as noise).

## B. Reflection geometry, per experiment

7. (blocking) External glancing angle of incidence (mrad) and how it was set and calibrated (RHEED pattern, rocking curve, Kikuchi lines).
8. (blocking) Beam azimuth relative to the surface net (for Si(001): [110] or [100]; for Si(111): [1-10] or [11-2]).
9. Which specular Bragg order or resonance condition the hologram was recorded at, and a measured rocking curve (intensity of the selected beam vs glancing angle) if one exists. The rocking curve is also what calibrates the mean inner potential and the angle scale.
10. Sign conventions: which tilt-coil direction moves the beam toward the surface, which image axis is the beam direction (the foreshortened one), and on which side of a step the shadow appears.

## C. Sample

11. (blocking) Surface orientation actually used (Si(001) vs Si(111)), miscut angle and direction, typical terrace widths.
12. (blocking) Surface preparation state: native oxide, HF-last, UHV flash, ion-milling parameters, expected amorphous damage-layer thickness, any annealing. At 20 mrad glancing incidence a 1 nm amorphous overlayer is crossed over about 50 nm of path on the way in and again on the way out (about 100 nm in total), so this dominates the reflected amplitude and must be modelled rather than ignored.
13. Pattern geometry for the patterned samples: lateral dimensions, nominal step or trench heights (nm) from AFM or SEM, edge profile, orientation relative to the beam. A feature of height h transverse to the beam shadows `h/tan(theta)` of surface behind it (444 nm for 10 nm at 22.5 mrad).
14. Whether the intended observable is atomic steps (heights 1.36 A, 2.72 A or 3.14 A) or nanometre-scale patterned steps. The two regimes need different quantification strategies because the height wrap period is only 0.4 to 1.5 A and because of items 3 and 13.

## D. Reference wave (do not infer from the biprism's intended function)

15. (blocking) Trajectory of the reference beam at the specimen plane: vacuum beside the sample, reflected from a flat area of the same surface, or transmitted through a thin region.
16. Separation between object and reference regions at the specimen; measured carrier fringe spacing (in image pixels and in specimen nanometres, stating which axis) and fringe contrast on an empty or flat-surface hologram.
17. Residual phase of an empty hologram (curvature, distortion), the biprism's Fresnel-fringe pattern and overlap width, and whether a reference hologram is recorded with every object hologram.
18. Biprism voltage(s) only if the laboratory intends to publish them; otherwise the measured carrier and overlap width are what the simulation needs.

## E. Processing applied to the experimental holograms

19. Sideband mask shape and radius, apodization window, zero-padding, carrier-location method, unwrapping algorithm, reference-hologram correction, ramp fitting region. The simulated holograms must be processed by the identical code path.

## F. Material and specimen-state parameters to be sourced or measured

20. Silicon mean inner potential `V0` with a citable measured or calculated value and uncertainty. The value 12.0 V used in this repository is an ASSUMPTION; a change of 1 V shifts the single-bilayer step phase at the (4,-4,4) condition by about 0.34 rad and biases a height inferred from a fixed measured phase by about 0.05 A.
21. Absorptive (imaginary) potential parameters for Si at the working energy, from a named parameterisation, for the dynamical reflection calculations.
22. Specimen charging: evidence (phase drift versus dose or time on a flat region) that the oxide-covered surface does not charge under the grazing-incidence illumination footprint, or the measured drift if it does.
