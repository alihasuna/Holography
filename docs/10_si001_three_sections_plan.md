# Plan: Si(001) three-section sample (reference, raised terrace, buried edge dislocation)

Status: 2026-09-30, PROPOSAL. The sample is built and rendered; no simulation has been run on it
yet. Config: `configs/si001_three_sections_cpu.yaml`. Renders:
`docs/figures/si001_three_sections_endon.png` (the simulation cell) and
`docs/figures/si001_three_sections_block3d.png` (a reduced-size 3D illustration).

## 1. The sample

| Strip | Width | Surface | Purpose |
|---|---|---|---|
| 1 reference | 153.6 A (40 x 3.84 A) | x = 0, bulk-terminated Si(001) | phase reference in the same image (R2-type self-reference) |
| 2 raised | 153.6 A | +4 atomic layers, h = a = 5.431 A (a lattice translation) | known step: tests the step phase, sign, refraction and V0 |
| 3 dislocation | 153.6 A | same height as strip 1 | Lomer edge dislocation 25 A deep (below), as in the textbook picture |

* Beam azimuth [110] (PROJECT_INPUT item 8 still open), strips and step edges parallel to the
  beam, so there is no shadowing and all three strips appear side by side in one image. The
  y axis is [1-10] and is not foreshortened.
* Dislocation: `b = a/2[-1,1,0]` (3.84 A, in the surface plane, perpendicular to the line), line
  along [110], pure edge. This is the Lomer dislocation, the usual misfit dislocation at (001)
  SiGe/Si interfaces. The sign puts the extra half-plane above the core, from 25 A deep up to the
  surface, as in the picture. Viewed along [110] the extra half-plane is two (220) atomic columns
  (red in the render).
* Construction: all strips are cut from one continuous lattice. The extra half-plane is inserted
  explicitly, adding 20 atoms per 3.84 A period (19 layers above the core plus one at the core).
  Isotropic half-space elasticity (docs/08) moves the atoms. The periodic seam lies in the middle of
  strip 1, away from the steps. Checks, all tested in `tests/test_sections.py`: terrace heights,
  +1 half-plane, surface bulge over the core of about `b/pi` = 1.2 A, reference strip flat to
  0.05 A, step edges undisturbed, and only 2 atoms (at the core) closer than 2.0 A.

## 2. What the simulation will measure

At (008) and 200 keV (theta_ext 16.5 mrad at V0 = 12 V, wrap period 0.76 A):

| Observable | Expected, geometric model | Why it matters |
|---|---|---|
| phase(strip 2) - phase(strip 1) | -44.8 rad, wrapped -0.85 rad at V0 = 12 V; wrapped 0.08 rad with the potential's V0 = 13.9 V | At a bulk Bragg condition a whole-layer step is nearly invisible: 4 x 2 pi from the lattice cancels. The measured step phase is the refraction residual, so strip 2 is a sensitive test of V0 and the angle calibration. |
| phase(strip 3) - phase(strip 1) | a bump of about 10 rad (b/pi = 1.22 A of relief, 1.6 phase wraps), FWHM about 2 x 25 A = 50 A | the buried-dislocation signal: depth from the width, Burgers component from the height |
| amplitude in strip 3 | dip above the core, deepening as the probed depth approaches 25 A | the only direct signature of the strain at depth |
| residual tilt | 0.19 rad across the 461 A cell | an artefact of the periodic seam, removed by the usual ramp fit and recorded |

## 3. Steps (after approval)

1. Geometry mode on the three-section cell: phase and amplitude maps, and strip differences
   against the table above.
2. Multislice on the CPU (numpy): the (001) cell is periodic along the beam with 2 slices per
   3.84 A, exactly as for Si(111). There is one run per sample, because strip 1 is the in-image
   reference, plus a perfect-crystal control. The strip differences are compared with step 1.
3. GPU run on Arbutus (`--backend cupy`, full sampling 0.05 x 0.13 A, rocking scan of +-0.6 mrad
   around (008)) following docs/09.
4. Sign test (strip 2 lowered instead of raised), depth scan of the dislocation (15, 25, 50 A), and
   a report in docs/08.

## 4. Choices to confirm

1. Strip 3 at the height of strip 1 (as proposed) or of strip 2?
2. Step height: 4 layers (lattice translation, the default). Odd layer counts (1 or 3) give
   terraces related by the 4_1 screw, with rotated dimer rows once a reconstruction is added;
   they have a genuinely dynamical phase difference and are an interesting second case.
3. Dislocation depth 25 A and type (Lomer, pure edge, extra half-plane up). A 60 degree
   dislocation on an inclined {111} plane is the other common type; its line is also along [110].
4. Reflection (008), or (0,0,12) (26.4 mrad, wrap period 0.48 A).
5. Unreconstructed surface for now, with the 2x1 dimer reconstruction later.
