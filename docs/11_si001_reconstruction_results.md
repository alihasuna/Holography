# Si(001) three-strip sample: simulated holograms and reconstructed phase and amplitude

Status: 2026-09-30, smoke-test results. The multislice kernel is not validated against abTEM or a
dynamical solver (docs/08). The sample is the one proposed in docs/10: strip 1 is the reference,
strip 2 is raised by 4 layers (5.431 A), and strip 3 is at reference height with a Lomer edge
dislocation 25 A deep. Command:
`python scripts/run_sections.py --config configs/si001_three_sections_cpu.yaml`.

## 1. Which Bragg reflection

The specular rod of Si(001) has the allowed reflections (004), (008) and (0,0,12). (002), (006) and
(0,0,10) are forbidden (F = 0). With the potential's own mean inner potential (13.91 V; 12 V is the
geometric ASSUMPTION):

| Reflection | theta_int (mrad) | theta_ext at Bragg (mrad) | Rocking maximum of this kernel (mrad) | Peak specular fraction | Wrap period (A) | Status |
|---|---|---|---|---|---|---|
| (004) | 9.24 | 2.09 | not computed | n/a | 6.0 | too grazing (exits barely above theta_c); geometry mode only |
| (008) | 18.47 | 16.13 | 16.93 (+0.8) | 0.019 | 0.74 | **working reflection** |
| (0,0,12) | 27.71 | 26.21 | 25.61 (-0.6) | 0.0011 | 0.49 | about 18 times weaker; about 1.5 times more phase per A of height |

Rocking curves: `docs/figures/rocking_si001_008.png`, `docs/figures/rocking_si001_0012.png`
(flat surface, dy = 0.128 A). The operating angle is the rocking-curve maximum, as an
experimenter would set it.

## 2. Hologram and reconstruction chain

The dark-field wave comes from the multislice exit plane, through the 1.5 mrad objective
aperture and demodulation. A tilted plane-wave reference (R1) with fringes 5 A apart along y at
the specimen is added. The hologram is recorded as `I = |psi + R|^2`, both noiseless and with
Poisson noise at 400 counts per pixel. The sideband is reconstructed with the carrier located on
an empty hologram, a mask radius of 0.06 A^-1 and division by the empty hologram. The phase is
unwrapped along y and a linear ramp is fitted on the reference strip only. Geometry mode (docs/08
column model, same displacement field as the atoms, same terrace heights) goes through the
identical hologram and reconstruction code. `tests/test_holography.py` checks that the chain is
exact (1e-9) for a band-limited object when the carrier exceeds 3 x the aperture radius.

## 3. Results

Converged sampling: dy = 0.128 A, dx = 0.1 A, sheet H = 80 A (see section 4). Figures:
`docs/figures/si001_three_sections_recon_008.png`, `..._recon_0012.png`, `..._overview.png`.
Each figure shows the hologram (zoom), the reconstructed phase map (noiseless and noisy), the
amplitude map and the profiles, with multislice and geometry mode through the same code. The
recon figure titles print the wrap period at the Bragg angle (0.777 A for (008)); at the
operating angle it is 0.741 A, and the script now prints that value.

| Quantity | (008) multislice | (008) geometry mode (Lambda 3 / 12 A) | (0,0,12) multislice | (0,0,12) geometry mode |
|---|---|---|---|---|
| operating angle (rocking maximum) | 16.93 mrad (effective 16.95) | same | 25.61 mrad (effective 25.75) | same |
| specular fraction in the aperture | 0.014 | n/a | 0.0044 | n/a |
| step, strip 2 - strip 1 | **-2.61 rad** | -2.56 / -2.56 | -2.23 rad, **not converged** (-0.3 to -1.5 rad depending on the image row) | -1.23 / -1.22 |
| -q_ext h alone, without the dislocation tail | n/a | -2.09 | n/a | -0.57 |
| dislocation, core minus strip 1 | **-11.17 rad** | -10.89 / -11.16 | -16.72 rad | -16.17 / -16.40 |
| dislocation, core minus strip-3 flanks (local reference) | **-8.99 rad** | -8.91 | -13.0 rad (spread over rows 0.45 rad) | -13.27 |
| dislocation FWHM | 54 A | 51 / 51 A | 57 A | 53 / 53 A |
| noisy hologram (400 counts per pixel) | identical to 0.01 rad after averaging over the image rows | n/a | identical | n/a |
| (004), geometry mode only | n/a | step +0.56 rad, dislocation -1.3 rad | n/a | n/a |

Reading:

* **(008) is converged and consistent.** The multislice reconstruction agrees with geometry mode
  to 0.05 rad on the step and to 1 to 3 percent on the dislocation. The step contains -0.47 rad
  from the dislocation's far field, which tilts strip 2 in both models. The bare -q_ext h is
  -2.09 rad.
* **(0,0,12): the dislocation agrees (2 percent against the local reference), but the step does not
  converge in this cell.** The reflected intensity along the band still oscillates over the 80 A
  sheet, and the raised strip's pattern is displaced by about 2h (figure
  `docs/figures/si001_0012_step_phase_per_row.png`). The per-row step phase spans -0.3 to -1.5
  rad, and geometry mode's -1.23 lies inside that range. A converged (0,0,12) step needs a
  footprint of micrometres (a GPU job).
* **(004)** exits at 2.1 mrad. It is 8 times less sensitive to height than (008) (1.05 against 8.48 rad/A), and the
  dislocation gives only -1.3 rad. It is not useful here.

## 4. Two numerical requirements found on the way

1. **Lateral sampling.** The specular reflectivity converges only for dy <= 0.13 A (docs/08,
   correction). The CPU runs here use dy = 0.128 A over the 460.8 A cell (3600 pixels).
2. **Illuminated footprint.** A finite sheet beam of height H illuminates a footprint of
   H/tan(theta) along the beam. A strip raised by h is illuminated h/tan(theta) earlier, so at a
   given image row the two strips are at different stages of the dynamical build-up of the
   reflected wave. A narrow two-strip test (`scripts/step_buildup_check.py`, no dislocation)
   against the exact -q_ext h:

   | Reflection | -q_ext h | Footprint 1.2-1.8 kA (H = 30 A) | 3-5 kA (H = 80 A) | 6-9 kA (H = 160 A) |
   |---|---|---|---|---|
   | (008) | -2.09 | -2.11 | -2.01 | -1.97 |
   | (0,0,12) | -0.57 | -1.34 | -0.42 | -0.44 |

   The weak (0,0,12) reflection needs a footprint of at least 3000 A. The runs in section 3 use
   H = 80 A. This is a property of the simulation cell only: in the experiment the footprint is
   micrometres long. The residual of about 0.1 rad at convergence is not yet explained; a strip
   width of 46 A in the narrow test is one candidate.

## 5. Physics read-out for the experiment

* **The dislocation is the robust signal.** A buried Lomer dislocation 25 A deep gives a phase
  bump of about 11 rad at (008) and 16 rad at (0,0,12), with FWHM of about 2 x depth, in agreement
  with geometry mode to a few percent at both reflections.
* **The step is a refraction and angle test, not a height measurement.** At a Bragg condition
  a 4-layer step returns only the residual of -q_ext h modulo 2 pi, which depends on the angle
  at 2.7 rad/mrad for h = 5.43 A. It is therefore very sensitive to angle calibration and to the
  illumination convergence (PROJECT_INPUT items 3 and 7).
* **Aperture limit.** Near the core the phase gradient of the (0,0,12) image exceeds what a
  0.06 A^-1 aperture passes (about 16 rad over 25 A needs about 0.1 A^-1). The amplitude drops to
  about 0.3 at +-15 A in both models and the peak is blunted. A larger objective aperture, or
  (008), images the core more faithfully (PROJECT_INPUT item 4).
* **Strain contrast.** At (008) the amplitude in strip 3 falls to about 0.8 over the core region
  in both models. An earlier +20 percent spike at the core came from the short 30 A sheet and
  disappears when the footprint is converged. At the current accuracy the amplitude does not yet
  separate buried strain from surface relief.
