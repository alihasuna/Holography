# Physics of reflection-mode dark-field electron holography of Si surfaces: what the simulation must reproduce

Status: 2026-09-21. This is the orchestrator's synthesis of `docs/agent_reports/C_physics_derivations.md`
(full derivations, 25 self-checked numbers, reproduced by `tools/reflection_step_phase_calculator.py`)
and of independent checks made during the analysis. Conventions: `docs/physics_conventions.md`.
Evidence labels follow the instruction file. Unless stated otherwise every formula below is
DERIVED_HERE from stated premises; nothing is attributed to an unread source.

## 1. The measurement chain (what the experiment records)

1. A plane-wave-like beam of energy `T` hits the surface at an external glancing angle `theta_ext`.
2. Inside the crystal the beam is refracted (mean inner potential `V0`) to `theta_int` and is
   Bragg-reflected by planes parallel (specular rod) or inclined (non-specular) to the surface.
   Dynamical theory gives a complex reflectivity `A(theta) = |A| exp(i phi_R)`.
3. One reflected beam is selected by the objective aperture: this is the dark-field object wave.
   Its image of the surface is foreshortened along the beam by `sin(theta_ext)`.
4. The object wave is superposed on a reference wave with a carrier tilt; the detector records
   `I = |u_o + u_r|^2`, averaged over the incoherent ensemble (source, energy, phonons) AFTER squaring.
5. Sideband reconstruction returns `phi_o - phi_r` (plus processing artefacts), wrapped mod 2 pi.
6. A surface step of height `h` between two identical terraces produces a phase step; the height
   is inferred from it, modulo a wrap period, with the branch fixed by prior knowledge or a rocking series.

The simulation must produce every quantity in this chain, in this order, with the same processing
applied to simulated and experimental holograms. A Fourier-selected spot of a simulated complex wave
(the inspected repository's `specular_filter.py`) is step 3 only; it is not steps 4 to 6.

## 2. Geometric (truncation) phase of a step

Premise: the upper-terrace crystal is the lower-terrace crystal translated by a lattice vector `R`
with `R.n_hat = h` (true for a Si(111) single-bilayer step, `R = (a/2)[1,0,1]`, `h = d_111 = 3.1355 A`,
and for a Si(001) double-layer step `h = a/2`; NOT true for a Si(001) single-layer step `h = a/4`,
whose terraces are related by the diamond `4_1` screw operation and therefore have different
complex reflectivities at a general azimuth).

Translation covariance of the scattering problem gives, exactly (not only kinematically):

```
Delta_phi = phi(upper) - phi(lower) = -(k_out - k_in) . R        (exp(+ik.r) convention)
```

* Specular beam: `k_out - k_in = (2 k sin(theta_ext)) n_hat`, so `|Delta_phi| = (4 pi / lambda) h sin(theta_ext)`.
  Equivalently `2 pi g.u` with `|g| = 2 sin(theta_ext)/lambda`: the same geometric-phase form as
  transmission dark-field holography, with the surface truncation playing the role of the displacement.
  The extra path is travelled in vacuum, so the VACUUM wavelength and the EXTERNAL angle apply.
* General reflection at in/out glancing angles: `|Delta_phi| = (2 pi / lambda) h (sin theta_in + sin theta_out) + (in-plane part) 2 pi g_par . R_par`.
  When the vacuum Bragg condition holds this reduces to `(4 pi/lambda) h sin(theta_B) (g_hat.n_hat)` only if
  the in-plane term is an integer multiple of 2 pi. The inspected repository's formula drops the in-plane
  term; for its default `(2,-2,0)` reflection the full `G.R/2pi` equals exactly 1 (invisible), not 2/3.
* Invisibility at the vacuum Bragg condition: if `g` is a bulk reciprocal-lattice vector and `R` a lattice
  translation, `exp(2 pi i g.R) = 1`. At the vacuum Bragg angle of any allowed order, a lattice-translation
  step is invisible. The step becomes visible because the Bragg condition is met INSIDE the crystal while
  the phase is accumulated OUTSIDE: refraction is the entire signal.

## 3. Refraction and the step phase at the specular conditions (Si, 200 keV, `V0 = 12 V` ASSUMPTION)

Conservation of the surface-parallel wavevector with `k_int^2 - k_ext^2 = 2 m_e gamma e V0 / hbar^2`:

```
sin^2(theta_int) = (sin^2(theta_ext) + Delta)/(1 + Delta),  Delta = V0 (1+T/m_e c^2) / (T (1+T/2 m_e c^2)) = 6.98e-5 at 200 keV
theta_c = 8.356 mrad (critical angle for total external reflection)
```

At the n-th order internal Bragg condition for spacing `d` the vacuum step phase for `h = m d` is
`Delta_phi = 2 pi m n sin(theta_ext)/sin(theta_int)`: not an integer multiple of 2 pi.

| Rod order (nnn) | Allowed? | theta_int (mrad) | theta_ext (mrad) | Single-bilayer step phase mod 2 pi (rad) | h_2pi = lambda/(2 sin theta_ext) (A) | Foreshortening 1/sin theta_ext |
|---|---|---|---|---|---|---|
| 333 | yes | 12.00 | 8.61 | 0.96 | 1.456 | 116 |
| 444 | yes | 16.00 | 13.64 | 2.58 | 0.919 | 73 |
| 555 | yes | 20.00 | 18.17 | 3.41 | 0.690 | 55 |
| 666 | NO (F = 0) | 24.00 | 22.50 | 3.92 | 0.557 | 44 |
| 777 | yes | 28.00 | 26.72 | 4.28 | 0.469 | 37 |
| 888 | yes | 32.00 | 30.89 | 4.54 | 0.406 | 32 |

(Values: `tools/reflection_step_phase_calculator.py`, checks T4 to T14; the orchestrator reproduced
them independently with a separate script, `docs/agent_reports/orchestrator_sanity_numbers.txt`.)
The instruction-file version of the same table using the non-relativistic `Delta = V0/T` gives
14.00 mrad and exactly pi at (444); that form underestimates `Delta` by 16 percent and must not be used.

Sensitivity: `dDelta_phi/dV0` is about -0.34 rad/V at (444) (about -0.05 A/V in height); the mean inner
potential is therefore a first-order systematic, not a correction, and must be a sourced input with an
uncertainty (see `docs/06_project_inputs_required.md`, item 20).

Si(001), single-layer step `a/4 = 1.358 A` (terraces NOT translation-related; the kinematic value is only
indicative) and double-layer `a/2 = 2.716 A`, specular orders (004), (008), (0,0,12): see the calculator
output section 5 (`docs/agent_reports/C_calculator_output.txt`).

## 4. The 2 pi branch problem and its resolution

A single hologram gives `h` modulo `h_2pi = lambda/(2 sin theta_ext)`, which is 0.4 to 1.5 A for all
usable conditions at 200 keV. A 3.1 A bilayer step is 3.4 wraps at (444); a 10 nm patterned step is
about 100 wraps. Consequences:

* Atomic steps: the branch must come from a lattice constraint (h is an integer multiple of the layer
  spacing) or from a rocking series: `d(Delta_phi)/d(theta) = (4 pi h/lambda) cos(theta)`; the phase
  increment per tilt step must stay below pi, which requires tilt steps below 0.63 mrad for `h = 1 nm`
  and below 0.06 mrad for `h = 10 nm` (check T23). Phase precision is not the problem: with fringe
  contrast 0.5 and 1e4 counts in the aperture area, `sigma_phi = 0.03 rad`, i.e. 0.003 A at (444).
* Nanometre-scale ion-milled patterns: the step riser is a phase discontinuity of many wraps; the
  hologram measures the shape of terraces, not the riser height, unless a fine rocking series is recorded.

## 5. What a transmission multislice can and cannot do at grazing incidence

* Propagator: specular reflection at 22 mrad changes only the transverse wavevector by `2 k sin(theta)`;
  the longitudinal component is unchanged, so the wave is forward-propagating along the beam axis and the
  paraxial Fresnel error over a 200 A cell is below 0.04 rad (C section 5.1). The propagator is not the obstacle.
* Boundary conditions ARE the obstacle. With the inspected repository's defaults (10 A vacuum above and
  below an 85 A plate, 138 A of crystal along the beam, periodic in the surface normal):
  only rays within `L_z tan(theta) = 3 to 4.5 A` of the surface reach it inside the slab (31 percent of
  the nominal 10 A gap, 16 percent of the true 20 A periodic channel); 81 percent of the incident plane
  wave enters the crystal through the front end face (Laue transmission through an 8.5 nm plate); the
  refracted ray crosses only one bilayer over the whole slab, so no Bragg-case reflection can develop;
  and the Laue-transmitted (n,-n,n) beam leaves in the same direction as the specular beam, so a k-space
  aperture cannot separate top-surface reflection, end-face transmission and back-face reflection.
  For the vacuum illumination to reach the surface at all, `L_z >= x_vac/tan(theta) = 444 A` for a 10 A
  gap; for a Bragg-case reflection to build up over a penetration depth of 5 nm, `L_z` of order 0.2 um.
* Sampling: with a 2/3 anti-aliasing rule the 0.13 A pixel supports 64 mrad at 200 keV (adequate); the
  generator's default 0.5 A pixel supports 17 mrad and cannot represent a 24 mrad tilt (check T22).
  Prismatic in particular anti-aliases at half Nyquist, ceiling `lambda/(4 dx) = 48 mrad` at 0.13 A.
* Requirements for a valid reflection cell: no vacuum below the back face (semi-infinite emulation with an
  absorbing or apodising region on the bulk side of the surface normal); vacuum margin above the surface
  larger than the illumination height plus `L_z tan(theta)`; illumination confined to the vacuum band and
  launched upstream of the crystal; cell length along the beam set by the footprint `H/tan(theta)` and by
  the dynamical build-up length; an allowed reflection; absorption from a sourced optical potential;
  validation against a surface-parallel dynamical reflection solver (Ichimiya-type, e.g. `sim-trhepd-rheed`)
  or a Bragg-case Bloch-wave solution, in the flat-surface limit, before any step is simulated.

## 6. Image geometry and hologram formation

* The simulated wave on the plane `z = L_z` is not the image. Select `k_out`, remove the carrier, and
  project along `k_out`: a surface feature at position `z_s` along the beam appears at exit-plane height
  `x = x_0 + (L_z - z_s) tan(theta)`; the surface coordinate is recovered as `z_s = (x_0 - x)/tan(theta)`,
  a 1/tan(theta) (about 44x at 22 mrad) magnification of the exit-plane height axis.
* Hologram: `I = |u_o + u_r|^2 = |u_o|^2 + |u_r|^2 + 2|u_o||u_r| cos(2 pi q_c.r + phi_o - phi_r)`.
  Sideband non-overlap requires `q_c > 3B` for an object bandwidth `B`, so the reconstructed resolution is
  about three fringe spacings; fringes need 3 to 4 pixels each.
* Reference models that must be explicitly selectable and reported: R1 vacuum plane wave (measures the
  absolute reflected phase including `phi_R`; note that a vacuum reference beside the specimen is inclined
  by `2 theta` (25 to 60 mrad) to the specular beam, which the optics must compensate to obtain a
  recordable fringe spacing); R2 self-reference from a flat region of the same surface (common-mode phases
  cancel; mirrored twin of the reference region appears in the result); R3 reference with residual
  curvature and tilt (long-wavelength topography is entangled with the reference phase).
* Phase noise of the sideband estimate: `sigma_phi = sqrt(2)/(mu sqrt(N))` with fringe contrast `mu` and
  `N` counts in the reconstruction aperture area.
* Processing trap verified in the calculator (check T24, section 12 of its output): the brightest Fourier
  bin of an object hologram with a 50/50 phase step is not the carrier; recentring on it produced a
  plausible but wrong step (0.78 rad instead of 2.36 rad). The carrier must be located on an empty
  hologram or on the sideband envelope.

## 7. Numbers a corrected repository must reproduce

See `docs/agent_reports/C_physics_derivations.md` section 8 (checks T1 to T25) and the qualitative
checks listed there: sign test for a down-step, forbidden-reflection guard, accessibility guard
(`G.n_hat >= 2 k sin theta_c`), small-denominator policy with a propagated height uncertainty,
periodic-boundary continuity of the terrace staircase, footprint and wrap-around assertions, rocking-series
branch resolution, and the carrier-location test.
