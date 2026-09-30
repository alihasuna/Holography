# Buried defects: a dislocation below the surface in reflection dark-field holography

Status: 2026-09-30, first implementation and smoke tests. Scope: straight perfect dislocations
buried parallel to the surface of Si(1,-1,1) (CFG-A frame, beam azimuth [110], specular (4,-4,4),
200 keV). The physics is DERIVED_HERE and checked numerically. The multislice kernel is
SMOKE-TESTED ONLY and has not been validated against abTEM or a dynamical solver (milestone M2).
Nothing here is a result to compare with experiment yet.

## 1. Why buried defects are visible in reflection at all

The reflected wave probes only the top few nanometres (the extinction and absorption depth
`Lambda`). A dislocation deeper than `Lambda` still acts on the hologram in two ways:

1. **Surface relaxation.** The traction-free surface moves by the elastic displacement field of the
   buried line. The reflected wave picks up the vacuum path difference `-(k_out - k_in).u_s` (the
   same translation-covariance phase as a step, docs/physics_conventions.md). For a line at depth
   `d`, the normal surface displacement is, exactly for an isotropic half-space and independently
   of Poisson's ratio (tested):

   `u_n(s) = (b1/pi) d^2/(s^2 + d^2) + (b2/pi) [atan2(d, s) - s d/(s^2 + d^2)] + const`

   Here `s` is the in-plane distance from the line, `b1` is the Burgers component in the surface
   plane perpendicular to the line (edge, glide-type), and `b2` is the component along the normal
   (edge, climb-type). The screw component `b3` moves the surface only along the line, as
   `u3 = (b3/pi) atan2(d, s)`. **The bump height `b1/pi` does not depend on depth; only its width
   (FWHM `2d`) does.** For a 60 degree dislocation `b = a/2[011]` on the (1,-1,1) glide plane:
   `b1 = 3.33 A`, bump 1.06 A, phase `q_ext b1/pi = 7.2 rad` at (4,-4,4) (0.919 A wrap period,
   so 1.15 wraps), for any depth.
2. **Strain inside the probed depth.** Where `d` is comparable to `Lambda`, the lattice phase
   `-G.u(depth)` varies over the probed column. This reduces the coherent column amplitude
   (strain contrast) and adds a small phase correction.

Consequences for the experiment:

* A buried dislocation appears in the reconstructed phase mainly as a smooth surface bump or
  step of width about `2d`. Its **depth is read from the width**, and its Burgers components from
  the height and shape.
* A pure screw dislocation parallel to the surface, or any dislocation with `b1 = b2 = 0`, is
  invisible in the specular beam (`q parallel to n`, `q.u = 0`). This is the reflection analogue of
  `g.b = 0` and is tested. A non-specular reflection with an in-plane `g` is needed to see it.
* Osakabe et al. 1989 (P02, abstract level only, not read) observed the spiral surface deformation
  of a screw dislocation EMERGING at GaAs(110). That is a different geometry (line crossing the
  surface) and is not implemented yet.

## 2. Models implemented

| Module | What it computes | Premises (labels) |
|---|---|---|
| `reflection_holo/defects/dislocation.py` | Full displacement field `u(r)` of a straight dislocation parallel to a traction-free surface, at depth `d`, arbitrary Burgers vector (edge in-plane, edge normal, screw). Superposition of several lines and periodic images. | Isotropic linear elasticity (D1, ASSUMPTION; Si has Zener ratio about 1.56). Volterra cut parallel to the surface on the side `-e1`. Perfect dislocations only: a non-lattice (partial) `b` is refused. Burgers convention: `b` = counter-clockwise circuit integral of `du` in the (s, h) plane, right-handed about the line direction `xi`. |
| `reflection_holo/forward/geometric.py` ("geometry mode") | `phi = arg sum_l w_l exp(-i(q_int - G).(R_l - R_0)) exp(-i G.u_l) - (q_ext - G).u_s` with `w_l = exp(-depth_l/Lambda)`; 2D maps on the surface and in foreshortened image coordinates; mapping to deformed (Eulerian) coordinates; the aperture as an ideal low-pass. | Kinematic column approximation over the probed depth, with `Lambda` scanned as an ASSUMPTION (D3). Refraction-corrected external angles. Reduces exactly to `-q_ext.R` for a rigid translation (tested). No dynamical scattering, no lateral propagation, no shadowing (relief slopes are below 0.05 rad, while shadows need slopes above theta). |
| `reflection_holo/forward/multislice.py` ("multislice mode") | Grazing-incidence multislice with slices perpendicular to the beam. Potential: Peng et al. 1996 high-angle parameterisation, exact structure factors, Debye-Waller damping. Absorbing bulk side. Sheet beam in the vacuum band tilted by theta_ext. Exact propagator with the 2/3 band limit. Declared exit plane. Dark-field aperture and demodulation. numpy or cupy. | Projection approximation per slice. Absorption `V_i = 0.05 V_r` (ASSUMPTION placeholder, not sourced; PROJECT_INPUT item 21). Crystal periodic along the beam, which is exact for lines along the beam; inclined lines would need z-dependent slices (not implemented). |

The mean inner potential of the parameterisation is 13.91 V. The same value is recovered from
the grid potential to 0.2 percent (tested). It differs from the 12.0 V ASSUMPTION B1, so the
multislice runs at its own internal Bragg condition (theta_ext 13.23 mrad instead of 13.64 mrad)
and reports both values. This is requirement 6 of docs/05 section 4.3 (source-map row SM17).

## 3. Verification of the elastic solution (tests/test_dislocation.py)

The field is checked numerically, not assumed: the surface traction is zero to 1e-5 of the bulk
stress scale; the Burgers circuit closes to `b` to 2e-3 A; finite-difference `div sigma` is zero;
the surface relief matches the closed forms above for Poisson ratio 0, 0.22 and 0.45; the line
sits where requested; partial Burgers vectors are refused.

## 4. Smoke test, geometry mode

Commands: `python scripts/run_buried_dislocation.py geometric --config <cfg>`. Each run takes under
25 s on a CPU.

| Config | Defect | Result |
|---|---|---|
| `configs/smoke/buried_dislocation_single_geometric.yaml` | One 60 degree dislocation, `b = a/2[110]`, line [011] at 60 degrees to the beam, 40 A deep | Surface depression of 1.06 A (`b1/pi`, with this sign of `b`); specular phase peak-to-peak 7.19 to 7.33 rad along the beam for `Lambda` = 3 to 40 A (path term alone: 7.21 rad). In the image the 1200 A surface window along the beam is compressed to 16 A (`sin theta_ext` foreshortening), so the line appears almost perpendicular to the beam. |
| `configs/smoke/buried_dislocation_cpu.yaml` | Dipole of 60 degree dislocations, `b = +-a/2[011]`, lines along the beam, 20 A deep, 100 A apart, periodic cell 199.5 A | Surface relief +-0.99 A; phase peak-to-peak 13.6 to 13.9 rad for `Lambda` = 3 to 25 A (path term alone: 13.56 rad). Column amplitude minimum above the cores 0.98, 0.91, 0.73 and 0.50 for `Lambda` = 3, 6, 12 and 25 A. |

## 5. Smoke test, multislice mode (CPU, numpy)

Command: `python scripts/run_buried_dislocation.py multislice --config configs/smoke/buried_dislocation_cpu.yaml`.
Grid 1024 x 512 (0.1 A x 0.39 A), 1733 slices of 1.92 A, cell length 3326 A, one flat-surface control
run and one defect run. Total time 65 s on 4 CPU cores.

| Quantity | Value |
|---|---|
| Operating angle (internal Bragg, V0 of the potential) | theta_ext 13.227 mrad |
| Specular intensity in a 1.5 mrad aperture, flat / defect | 0.1925 / 0.1391 of the incident flux |
| Multislice phase change, peak-to-peak (defect minus flat) | 12.54 rad |
| Geometric model, same observable (deformed coordinates + same aperture), peak-to-peak | 13.16 / 13.12 / 12.93 / 12.55 rad for Lambda = 3 / 6 / 12 / 25 A |
| RMS residual multislice minus geometric (intensity-weighted) | 0.24 / 0.32 / 0.45 / 0.57 rad for Lambda = 3 / 6 / 12 / 25 A (0.34 to 0.63 rad without the deformed-coordinate mapping and aperture) |

Reading:

* The two models agree in shape, sign and magnitude. The profile is set by the surface relief, as
  argued in section 1. The residual is smallest for small `Lambda`. This is a **consistency check,
  not a validation**: both rest on the same translation-covariance identity (docs/05 section 4.4).
  The best-matching `Lambda` is not a measured penetration depth, because the absorption is a
  placeholder.
* The remaining residual of about 0.2 rad has two visible parts. The peaks are blunted by the
  17 A aperture resolution, and there is a lateral offset of about 2 A. The local surface tilt
  deflects the reflected beam by `2 alpha sin(theta)`, about 1.3 mrad, over the roughly 1600 A
  from reflection to the exit plane. The geometric model contains no propagation, so it cannot
  show this offset. This is expected physics, not tuned away.
* The defect reduces the specular intensity by 28 percent. Part of this is intensity scattered
  outside the aperture by the phase gradients (up to 0.5 rad/A), and part is strain contrast.

NOT RUN: the cupy backend (no GPU in this environment; see docs/09); the GPU-sized config with its
rocking scan; abTEM cross-validation and the phase-validation ladder (M2); hologram formation and
reconstruction of these waves (M3); inclined or emerging lines; anisotropic elasticity; Si(001).

## 6. What is needed to turn this into a prediction for the real sample

The questions in docs/06 section G (items 23 to 27): defect type and origin, Burgers vector and
line direction, depth, spacing, and independent characterisation. Also the reflection and angle
actually used (items 4, 7 and 9), and a sourced absorptive potential (item 21), which fixes
`Lambda` and therefore the strain-contrast amplitude.

## 7. Figures

* `docs/figures/buried_dipole_geometric.png`: surface relief, specular phase and column amplitude (dipole, geometry mode).
* `docs/figures/buried_single_line60_geometric.png`: single line at 60 degrees to the beam, surface map, foreshortened wrapped phase, profile along the beam.
* `docs/figures/buried_dipole_multislice_cpu.png`: exit wave, exit spectrum with the aperture, dark-field phase map (defect minus flat), multislice-versus-geometric profiles, specular intensity.

## 8. Atomic coordinates

`python scripts/export_atoms.py --config <cfg>` writes the exact positions that the multislice
uses, as extended XYZ (readable by OVITO, ASE and VESTA via ASE). The files are in the slab frame:
x is the outward normal [1,-1,1] with the surface at 0, y is [1,-1,-2], z is the beam [110], in A.
The cell is periodic along y and z and open along x. The dislocated file also carries the
displacement `disp` per atom. For the CPU smoke config, the files
`docs/structures/si111_dipole_cpu_{perfect,dislocated}.xyz` hold 2160 atoms in a
199.544 x 3.840 A cell, 56 A deep.

* The field includes a near-uniform rigid shift (u_y about -1.1 to -2.0 A and u_z about 0.3 to 1.5 A
  everywhere), which comes from the cut convention and the summed periodic images. A rigid
  translation adds only a constant phase and a lateral shift. The comparison with the geometric
  model accounts for it by using the same displacement field.
* Linear elasticity is not valid at the cores: 3 atoms come closer than 2.0 A to a neighbour
  (minimum 1.82 A, against the 2.35 A Si bond). No atom is closer than 1.8 A. A relaxed core (from an
  interatomic potential or DFT) is not modelled.
* `docs/figures/buried_dipole_atoms_cross_section.png`: the cell viewed along the beam, coloured by
  u_x, and a zoom on one core with the window-mean displacement removed for display.
