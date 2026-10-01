# Figure captions

All figures are smoke-test results of this repository's simulation (status in docs/08 and docs/11).
The multislice kernel has not yet been validated against abTEM or a dynamical reflection solver.
Figures are in Nature format (89 mm single column, 183 mm double column), as vector PDF and
450 dpi PNG. Source data and scripts are named under each caption.

---

**fig_sample_si001 | Simulated Si(001) sample with three strips.** **a**, Simulation cell viewed
along the electron beam ([110]), showing all atoms of one 0.384 nm repeat. Strip 1 is the
reference terrace. Strip 2 is raised by four atomic layers (0.543 nm, one lattice constant).
Strip 3 is at the reference height and contains a Lomer edge dislocation (Burgers vector
a/2[-110], 0.384 nm; line along the beam) 2.5 nm below the surface. Dashed lines mark the
strip boundaries, and the extra half-plane of the dislocation is red. **b**, The step between
strips 1 and 2, with bonds drawn. **c**, The dislocation core (⊥) and the extra half-plane (two
(220) atomic columns, red) running up to the surface. Atoms are displaced with the
isotropic-elasticity field of a dislocation below a free surface. Linear elasticity is not valid
within about 0.3 nm of the core. Script: `scripts/figures_structure.py`.

**fig_hologram_si001_008 | Simulated reflection hologram and reconstruction, (008) reflection.**
Si(001), 200 keV, glancing angle 16.9 mrad (maximum of the rocking curve). **a**, Off-axis hologram
with fringes 0.5 nm apart and Poisson noise of 400 counts per pixel. Strip labels are as in
fig_sample_si001. The vertical axis is the image coordinate along the beam, drawn stretched: the
real image is foreshortened along the beam by 1/sin(theta) = 59 and is uniform in that
direction. The box marks the region shown in **d**, and the triangle marks the dislocation
line. The faint horizontal banding is the variation of the reflected intensity along the
illuminated footprint of the finite simulation beam; the phase is not affected (**b**). **b**, Reconstructed phase, unwrapped, relative to the reference strip (sideband
reconstruction with the carrier located on an empty hologram and a linear ramp fitted on strip 1).
Negative phase (blue) means the surface is higher. **c**, Reconstructed amplitude relative to
the reference strip. **d**, Hologram over the dislocation (object, bottom) under the empty,
reference-only hologram (top). The fringes bend by up to 1.8 fringes. **e**, **f**,
Phase and amplitude profiles averaged along the beam. Multislice is the full dynamical
simulation. The geometric model is the column (kinematic) model with the same displacement
field, passed through the same hologram chain. Values: step phase -2.61 rad (geometric
-2.56 rad, which includes the tilt of strip 2 by the dislocation's far field; the bare step term
is -2.09 rad); dislocation -11.1 rad at the core, FWHM 5.4 nm. The scale bar in **a** applies to
**a** to **c**. Scripts: `scripts/run_sections.py`, `scripts/figures_holography.py`.

**fig_hologram_si001_0012 | Same as fig_hologram_si001_008 for the (0,0,12) reflection.** Glancing
angle 25.6 mrad, foreshortening 39. The dislocation phase (-16.6 rad at the core, -13.0 rad
relative to the flanks of strip 3; geometric model -13.3 rad) is converged. The step phase of
strip 2 (-2.2 rad) is **not converged** in this simulation cell, because it depends on the image
row (fig_step_rows_0012). It must not be read as a prediction.

**fig_rocking_si001 | Flat-surface rocking curves.** Fraction of the incident sheet beam
reflected into the 1.5 mrad objective aperture against the glancing angle, for the (008)
reflection (**a**) and the (0,0,12) reflection (**b**) of Si(001) at 200 keV. The dashed line is
the Bragg angle corrected for refraction with the mean inner potential of the simulation
potential (13.9 V). The triangle is the operating angle used for the holograms, at the
reflectivity maximum. Absorption is a placeholder (imaginary potential 5% of the real one), so the
absolute reflectivity is not quantitative. Data: `docs/figures/data/rocking_001_*.json`;
script: `scripts/rocking_flat.py`.

**fig_reflections_si001 | Reconstructed phase and amplitude of the three-strip sample by
reflection.** **a**, Phase and **b**, amplitude profiles across the beam, relative to strip 1, for
(008) and (0,0,12) (multislice: solid; geometric model: dashed) and for (004) (geometric model
only, glancing angle 2.1 mrad). Numbers 1 to 3 mark the strips. The dislocation signal scales with
the momentum transfer (about -1.3, -11 and -16 rad for (004), (008) and (0,0,12)). The (0,0,12)
step phase is not converged (fig_step_rows_0012). Data:
`outputs/si001_three_sections_cpu/reconstruction/results.npz`.

**fig_convergence | Numerical convergence of the simulation.** **a**, Specular reflectivity at the
Bragg angle against the lateral pixel size of the multislice grid, for Si(111) (4,-4,4) and
Si(001) (008) and (0,0,12). Results converge for pixels of 0.13 Å or smaller (shaded; used for
all Si(001) results). **b**, Error of the simulated step phase (strip 2 minus strip 1, two-strip
test without a dislocation) relative to the exact translation result -(k_out - k_in)·R, against
the length of the illuminated footprint along the beam. The weak (0,0,12) reflection needs
about 0.3 µm or more. Data: `docs/figures/data/convergence_dy.json`, `step_buildup_check.json`;
script: `scripts/step_buildup_check.py`.

**fig_step_rows_0012 | Why the (0,0,12) step phase is not converged.** **a**, Reflected intensity
along the image coordinate (along the beam) for strip 1 and strip 2 in the three-strip run. The
raised strip's pattern is displaced, because its reflection builds up at a different position along the
footprint. **b**, Step phase (strip 2 minus strip 1) evaluated row by row. It varies between -0.3
and -2.1 rad. The geometric-model value (dashed) lies within this range. A footprint of several
micrometres is needed for a converged value.
