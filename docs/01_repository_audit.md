# Audit of `hussienba/si110-reflection-holography` (commit 6694959)

Status: 2026-09-21. Orchestrator's synthesis of the full code audit
(`docs/agent_reports/A_code_audit.md`, 1413 lines, every file read, generator/filter/step-height
scripts executed on synthetic data), the software-provenance audit
(`docs/agent_reports/D_software_provenance.md`, version-matched source of prismatique 0.0.1,
embeam 0.0.1 and the Prismatic 1.2.0 tree) and the physics report
(`docs/agent_reports/C_physics_derivations.md`). File and line numbers refer to the inspected
commit. Evidence labels as in the instruction file; REPRODUCED means the behaviour was executed or
the API exercised here, SECTION_READ means the pinned source was read, DERIVED_HERE means computed
from the repository's own parameters. No prismatique simulation was executed (no compiled engine).

## 1. What the repository is

The repository is a transmission HRTEM multislice (Prismatic through the prismatique wrapper) of a
free-standing Si plate, 8.5 nm thick, whose (1,-1,1) face is parallel to a [110] beam tilted by 0 to
24 mrad, followed by Fourier selection of one spot of the resulting complex wave and a kinematic
phase-to-height formula. In the terms of instruction section 9.1 it implements only complex-wave
selection; it forms no intensity hologram and performs no hologram reconstruction, although its
README, its citations and its script docstrings describe it as off-axis holographic reconstruction.

| Aspect | Reflection-mode dark-field holography experiment | This repository |
|---|---|---|
| Specimen | semi-infinite crystal, one free surface, grazing incidence | 8.5 nm plate with two free surfaces, periodic along its own surface normal with a 16 A image gap (declared 10 A vacuum on each face; measured 7.6 A), no absorber |
| Illumination | wave arriving from vacuum at the glancing angle | plane wave filling the whole cell: 85 percent starts inside the crystal (end-face entry); 1 percent (8 mrad) to 3 percent (24 mrad) reaches the surface from the vacuum side within the 138 A slab |
| Measured beam | a Bragg-reflected beam leaving into vacuum | the (2,-2,0) zone-axis Bragg beam of a plate in transmission; (2,-2,0) is not accessible in reflection geometry at 200 keV (C section 3.5); the documented "(666) specular" target ((6,-6,6) for this surface) is kinematically forbidden |
| Recorded plane | detector plane after the imaging optics | the supercell mid-plane (the engine back-propagates the exit wave by half the cell), labelled "complex exit wave" |
| Reference wave, hologram | biprism overlap of object and reference beams; intensity fringes | none; the "phase" is `np.angle` of a band-pass-filtered copy of the simulated field |
| Quantification | signed, calibrated, branch-resolved height with uncertainty | `h = Delta_phi lambda/(4 pi sin theta_B (g_hat.n_hat))` with the sign discarded, the 2 pi branch ignored, silent defaults for energy, angle and `g_hat.n_hat`, no uncertainty |
| Ensembles | incoherent average over source, energy, phonons | one static configuration; config, defocus and tilt axes collapsed by `[0,0,0,:,:]` |

## 2. Checklist against instruction section 9

| Item | Verdict | Evidence (A section 3, D sections 2 to 4) |
|---|---|---|
| 9.1 complex wave vs hologram | FAIL | no `u_ref`, no `abs(u_o+u_r)**2`, no reconstruction; `specular_filter.py:500-601` |
| 9.2 orientation conventions | PARTIAL | rotation matrix orthonormal and right-handed (REPRODUCED); README "(1,1,-1)" incompatible with a [110] beam; examples labelled "Diamond Cubic (100)"; no outward-normal, tilt-sign or structure-factor statement |
| 9.3 propagation approximation | FAIL | nothing documented or tested; the cell is a periodic stack of plates; absorber silently dropped |
| 9.4 reference beam | FAIL (not applicable to the code, but the README claims holography) | no reference branch exists |
| 9.5 coherence and ensembles | FAIL | `[0,0,0,:,:]` discards config, defocus and tilt axes; only subset 0 read; thermal parameters written but never used |
| 9.6 data plane and axes | FAIL | no assertions on dataset, dims, dtype; fallback to "first complex dataset"; pixel size from an advisory value (factor 2); mid-plane wave called exit wave |
| 9.7 phase-to-height | FAIL | sign destroyed; wrap ignored; exact-zero-only denominator guard; silent defaults; no uncertainty |
| 9.8 units, Fourier conventions, processing bias | FAIL | units internally consistent (no stray 2 pi), but apodisation, padding, notch, aperture, unwrapping and default detrending are unquantified; raw phase not saved; constants hard-coded in four places |

## 3. Defects, grouped by consequence

### 3.1 Scripts that do not produce what they claim (REPRODUCED against the pinned API)

* A-C1: `multislice_tilt_series_runner.py:547-556` passes `save_probe_complex` and
  `wavefunction_z_planes` to `prismatique.hrtem.image.Params`; neither keyword exists in 0.0.1. The
  `TypeError` is swallowed, `image_params` becomes `None`, the defaults `save_wavefunctions=False`
  and `save_final_intensity=False` apply, and the tilt runner writes nothing but a parameter JSON
  after running the full multislice.
* A-C2: the runner sets `interpolation_factors=(4,4)` while the forward model uses `(1,1)`; the
  potential grid is 16 times larger than the grid it prints (864 x 640 at 0.121 A instead of
  216 x 160 at 0.485 A) and the tilt grid is 4 times coarser (nearest available tilt 0.66 mrad off).
* D-3.1: `absorbing_layers` is not a `sample.ModelParams` keyword; the forward model catches the
  error, retries without it, and still prints "Absorber window ... (bulk side)". Prismatic has no
  absorbing boundary at all. The configured window is also on the wrong axis (z, not the bulk-side x).
* D-3.4: with the tilt sweep the engine simulates every FFT-grid tilt inside the window (1309 plane
  waves for the 74 requested angles) and the intensity file is filled with NaN because the tilt
  weights use an exact float comparison against a snapped offset computed with a different wavelength.
* A-M10: `process_all_tilts.py` calls the renamed `specular_666_filter.py`, uses a hard-coded HPC
  path, expects a directory layout the runner does not produce, and exits with status 0 after printing an error.

### 3.2 Wrong plane, wrong slice, wrong calibration

* D-2a: `image_wavefunctions` is the exit wave Fresnel back-propagated by half the cell length to
  the supercell mid-plane (about -99 A for the default cell), unconditionally; every message in the
  pipeline calls it the exit wave.
* A-C5 / D-3.4: `specular_filter.py:61-77` takes index `[0,0,0]`; for the runner's output that is
  tilt (0, -0.94) mrad at the edge of the window, not the intended condition. A synthetic 5-tilt file
  with the step at index 3 yields a reported step of 0.000 rad with no warning.
* A-C6 / D-3.5: the pixel size comes from `meta.json`'s advisory value; the HRTEM image pixel is
  twice the achieved potential pixel (ratio 2.01 for 0.13 A), so the k axes are stretched by two and
  the filter locks onto the reflection at half the requested |g|. This error partially cancels the
  next one, so the pipeline can appear to work and fixing either bug alone breaks it.
* A-C7: the filter searches a ring of radius `1/d_target`, but the Fourier components of a tilted
  beam lie at `k_in + g`; for the runner's own tilt the correct radius is outside the +-3 percent ring.
* A-M8: `meta.json` misreports the realised geometry (vacuum 7.65 A actual vs 10.0 declared; slab
  thickness 88.6 A vs 84.7 A; asymmetric z vacuum) and never writes the true surface position.
* D-2g: Prismatic mirrors the file z coordinate (`z = L_z - z_file`); the generator ignores this. For
  this slab the mirror perpendicular to [110] is a lattice symmetry (97 percent atom match), so the
  effect is benign here but must be handled for any z-asymmetric cell.

### 3.3 The simulated geometry is not a reflection problem (DERIVED_HERE from the defaults)

* Only rays within `L_z tan(theta)` of the surface (3 to 4.5 A) reach it inside the slab; the
  illumination must travel 444 A to fall the declared 10 A gap; 81 to 85 percent of the wave enters
  through the front end face and propagates as Laue transmission through the plate.
* The Laue-transmitted (n,-n,n) beam and the specular beam leave in the same direction, so a k-space
  aperture cannot separate top-surface reflection, end-face transmission and back-face reflection.
* The refracted ray crosses about one bilayer over the whole slab; no Bragg-case reflection can build up.
* The 8 A potential extent wraps past the cell edge; 193 atoms are double-counted on the y = 0 plane
  (a strict inequality at both ends of the periodic direction), producing a line of anomalous
  projected potential along the beam, geometrically identical to a step edge (A-M7).
* The generator's default advisory pixel (0.5 A) cannot represent a 24 mrad tilt: prismatique raises
  `IndexError` (Prismatic's tilt ceiling is `lambda/(4 dx)` = 12.9 mrad there) (D-2c, REPRODUCED).

### 3.4 The physics targets are inconsistent (DERIVED_HERE, reproduced by the calculator)

* (6,-6,6), the specular reflection the docs call "666", is kinematically forbidden in diamond-cubic Si
  (F = 0); the initial commit message already acknowledged this. Allowed neighbours on the rod: (4,-4,4),
  (5,-5,5), (7,-7,7), (8,-8,8).
* At the vacuum Bragg angle of any allowed order a lattice-translation bilayer step is invisible
  (phase 2 pi n); at the reflectivity maximum the signal is the refraction shift, which places the peak at
  the external angle 22.50 mrad rather than 24.00 mrad for the (6,-6,6) spacing, where a bilayer step
  gives 3.92 rad; away from bulk Bragg points the phase is the ordinary geometric path difference.
* The default target (2,-2,0) cannot connect two vacuum-propagating beams at 200 keV
  (`G.n_hat = 2.67 rad/A < 2 k sin theta_c = 4.19 rad/A`); any (2,-2,0) intensity in the simulation
  is Laue transmission through the plate. For non-specular reflections the repository formula drops
  the in-plane part of the step translation: with it, `G.R/2 pi` is exactly 1 for a bilayer step (invisible).

### 3.5 Reconstruction defects (REPRODUCED on synthetic 5-D files in the prismatique schema)

* A-C3: `find_peak` demodulates on `argmax|Psi|`; for a two-level object the first harmonic exceeds
  the carrier when |Delta_phi| > 2.008 rad, so the repository's own 2.094 rad case locks onto a
  sideband and injects a pi/2 ramp; the measured step becomes 0.524 rad. (The physics calculator found
  the same trap independently, C section 7.5.)
* A-M5: the plane detrend is on by default and removes 27 percent of a single step and essentially all
  of a monotonic staircase.
* A-M6: the k-space aperture is specified in pixels of the padded grid; its physical radius changes
  with `--dx`, `--pad` and array size; a sweep of the inner radius gives reported heights of 0.12, 0.55,
  0.11 and 84.9 A with no warning.
* A-M13, A-M14, A-M15: circular `np.roll` demodulation; a row-then-column `np.unwrap` on an array whose
  invalid pixels are zero; raw phase never saved.

### 3.6 Quantification defects (REPRODUCED)

* A-C8: `min/max` of histogram levels destroys the sign: an imposed -2 pi/3 step is reported as +1.15 rad.
* A-C4: the branch is ignored; with the repository's own formula the one-bilayer phase at (2,-2,0) is
  8 pi/3, only 2 pi/3 is observable, and the script returns d_111/4 = 0.78 A while printing the
  theoretical 8.38 rad next to the measured value without comment.
* A-M11, A-M12: no no-step control (fewer than two histogram peaks returns the 10th/90th percentiles of
  the noise as a "step"); `step_height_A = 0.0` is treated as missing (falsy-zero) and reported as
  3.136 A; `energy_keV`, `alpha_deg`, `g_dot_n_surf`, `a_A` default silently; no uncertainty anywhere.

### 3.7 Provenance and documentation

* No tests, no CI, no lockfile; `requirements.txt` pins nothing while the README claims a 0.0.1 pin
  whose stated rationale (schema drift) is not supported: `hrtem/sim.py` is byte-identical in 0.0.1 and
  0.0.4 (D-1.3). `prismatique` does not declare `pyprismatic`; the engine build is unrecorded.
* Thermal effects are never enabled; the 0.076 A per-axis RMS displacement is inert; the README's
  claim of Debye-Waller treatments is false for this code.
* README inconsistencies: "(1,1,-1)" vs "[1,-1,1]"; author orders of B08 and B11 reversed; the initial
  commit claims to replicate "Osakabe et al. (1993)", which is the Banzhof and Herrmann paper;
  `CITATION.cff` is empty; the licence is MIT while prismatique is GPLv3 (a decision to record).

## 4. What survived scrutiny (REPRODUCED)

* The slab rotation matrix is orthonormal (2e-16) and right-handed; the facet is {111} and the beam
  is a <110> in-plane direction.
* Terrace heights are exact multiples of d_111 and every cut plane falls in the wide inter-bilayer gap;
  no half-bilayers are produced.
* The two wavelength formulas are algebraically identical (1e-6 percent difference).
* Units are consistent inside the filter (cycles per angstrom throughout) and tilts are in mrad at every
  software boundary; no factor-1000 error exists.
* With the carrier bin forced, detrending off and the true pixel size, the filter recovers an imposed
  2.094 rad step as 2.130 rad (1.7 percent), which shows the Fourier arithmetic itself is sound.

## 5. What would have to change first

In priority order (A section 7, D section 5.2): remove the invalid keywords so the runner writes output
and replace every swallowed constructor exception by a hard failure; rewrite the loader with assertions
(dataset, dims, dtype, pixel size from `/metadata/r_x`, tilt selected by value, all subsets); rewrite the
quantification (signed differences, branch handling, required metadata, small-denominator policy,
uncertainty); locate the spot from `k_in + g` with sub-pixel refinement, specify the aperture in
physical units, detrend off by default, save raw phase; make the grid and geometry explicit; add the
hologram-formation and reconstruction stages as separate tested operations; add the tests of
instruction section 10. These are the M0 and M1 milestones of `docs/05_final_repository_specification.md`.
Whether the reflection geometry can be modelled with this engine at all is a separate decision
(M2): with periodic boundaries along the surface normal and no absorber, Prismatic cannot represent a
semi-infinite surface, and the maintainers describe it as no longer actively maintained.
