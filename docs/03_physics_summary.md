# Physics of reflection-mode dark-field electron holography of Si surfaces: what the simulation must reproduce

Status: 2026-09-21, revision 2 (corrected after the adversarial review in
`docs/agent_reports/E_review.md`; the review's blocker B1 and major items M1 to M9 are applied here).
This is the orchestrator's synthesis of `docs/agent_reports/C_physics_derivations.md` (full
derivations, 25 self-checked numbers reproduced by `tools/reflection_step_phase_calculator.py`) and of
independent checks made during the analysis. Conventions: `docs/physics_conventions.md`. Evidence
labels follow the instruction file. Unless stated otherwise every formula below is DERIVED_HERE from
stated premises; nothing is attributed to an unread source.

Notation: the specular rod of the (1,-1,1) surface consists of the reflections `(n,-n,n)`. They have
the same `d` and the same `|F|` as `(n,n,n)`, but only `(n,-n,n)` is specular for this surface; an
implementer must copy `(4,-4,4)`, not `(4,4,4)`. "Dark-field" here means that the image is formed from
one selected reflected rod of the RHEED pattern, chosen by the objective aperture; no transmitted beam
exists in reflection geometry, so the phrase says which reflected beam is used.

## 1. The measurement chain (what the experiment records)

1. A plane-wave-like beam of kinetic energy `T` hits the surface at an external glancing angle
   `theta_ext`.
2. Inside the crystal the beam is refracted (mean inner potential `V0`) to `theta_int` and is
   Bragg-reflected by planes parallel (specular rod) or inclined (non-specular) to the surface.
   Dynamical theory gives a complex reflectivity `A(theta) = |A| exp(i phi_R)`.
3. One reflected beam is selected by the objective aperture: this is the dark-field object wave.
   Its image of the surface is foreshortened along the beam by `sin(theta_ext)`.
4. The object wave is superposed on a reference wave with a carrier tilt; the detector records
   `I = |u_o + u_r|^2`, averaged over the incoherent ensemble (source, energy, phonons) AFTER squaring.
5. Sideband reconstruction returns `phi_o - phi_r` (plus processing artefacts), wrapped mod 2 pi.
6. A surface step of height `h` between two identical terraces produces a phase step; the height is
   inferred from it, modulo a wrap period, with the branch fixed by prior knowledge or a rocking series.

The simulation must produce every quantity in this chain, in this order, with the same processing
applied to simulated and experimental holograms. A Fourier-selected spot of a simulated complex wave
(the inspected repository's `specular_filter.py`) is step 3 only; it is not steps 4 to 6.

## 2. Geometric (truncation) phase of a step

Premise: the upper-terrace crystal is the lower-terrace crystal translated by a lattice vector `R`
with `R.n_hat = h` (true for a Si(111) single-bilayer step, `R = (a/2)[1,0,1]`, `h = d_111 = 3.1355 A`,
whose in-plane part `a/sqrt(6) = 2.217 A` is not a surface-net vector; and for a Si(001) double-layer
step `h = a/2`; NOT true for a Si(001) single-layer step `h = a/4`, whose terraces are related by the
diamond `4_1` screw operation and therefore have different complex reflectivities at a general azimuth).

Translation covariance of the scattering problem gives, exactly (not only kinematically):

```
Delta_phi = phi(upper) - phi(lower) = -(k_out - k_in) . R        (exp(+ik.r) convention)
```

* Specular beam: `k_out - k_in = (2 k sin(theta_ext)) n_hat`, so `Delta_phi = -(4 pi / lambda) h sin(theta_ext)`.
  Equivalently `-2 pi g.u` with `|g| = 2 sin(theta_ext)/lambda`: the same geometric-phase form as
  transmission dark-field holography, with the surface truncation playing the role of the displacement.
  The extra path is travelled in vacuum, so the VACUUM wavelength and the EXTERNAL angle apply.
* General reflection at in/out glancing angles:
  `Delta_phi = -[ (2 pi / lambda) h (sin theta_in + sin theta_out) + 2 pi g_par . R_par ]`.
  When the vacuum Bragg condition holds this reduces to `-(4 pi/lambda) h sin(theta_B) (g_hat.n_hat)`
  only if the in-plane term is an integer multiple of 2 pi. The inspected repository's formula drops the
  in-plane term: for its default `(2,-2,0)` reflection the full `G.R/2 pi` is exactly 1 (invisible),
  while the repository formula gives 4/3, i.e. `2 pi/3` of phase per bilayer, which is the origin of the
  `0, 2 pi/3, 4 pi/3, 2 pi` staircase claimed in the generator docstring.
* Invisibility at the vacuum Bragg condition: if `g` is a bulk reciprocal-lattice vector and `R` a lattice
  translation, `exp(2 pi i g.R) = 1`. At the vacuum Bragg angle of any allowed order, a lattice-translation
  step is invisible.
* Two operating regimes must both be supported. At an exact bulk-Bragg point of the specular rod the
  vacuum momentum transfer would be `G` and the step would be invisible; the phase actually measured
  there is the refractive departure of the vacuum momentum transfer from `G` (the reflectivity maximum
  sits at the internal Bragg condition, so the external angle is smaller). Away from a bulk Bragg point
  (a truncation-rod or surface-resonance condition, which is how REM is commonly operated, see B report
  P26) the step phase is the ordinary geometric path difference `-2 h k sin(theta_ext)` and is not a
  refraction effect. The operating point, a PROJECT_INPUT, decides which description applies.

## 3. Refraction and the step phase at the specular conditions (Si, 200 keV, `V0 = 12 V` ASSUMPTION)

Conservation of the surface-parallel wavevector with `k_int^2 - k_ext^2 = 2 m_e gamma e V0 / hbar^2`
(`T` in eV, `V0` in V):

```
sin^2(theta_int) = (sin^2(theta_ext) + Delta)/(1 + Delta),
Delta = V0 (1 + T/(m_e c^2)) / (T (1 + T/(2 m_e c^2))) = 6.98e-5 at 200 keV
theta_c = 8.356 mrad
```

`theta_c` is the internal glancing angle below which a beam inside the crystal cannot escape into
vacuum (total internal reflection at the surface barrier). Because `V0 > 0` the refractive index
exceeds 1, every externally incident beam enters the crystal with `theta_int >= theta_c`, and there is
no total external reflection for electrons.

At the n-th order internal Bragg condition for spacing `d` the vacuum step phase for `h = m d` is
`|Delta_phi| = 2 pi m n sin(theta_ext)/sin(theta_int)`: not an integer multiple of 2 pi.

| Rod order (n,-n,n) | Allowed? | theta_int (mrad) | theta_ext (mrad) | Single-bilayer step phase mod 2 pi (rad) | h_2pi = lambda/(2 sin theta_ext) (A) | Foreshortening 1/sin theta_ext |
|---|---|---|---|---|---|---|
| (3,-3,3) | yes | 12.00 | 8.61 | 0.96 | 1.456 | 116 |
| (4,-4,4) | yes | 16.00 | 13.64 | 2.58 | 0.919 | 73 |
| (5,-5,5) | yes | 20.00 | 18.17 | 3.41 | 0.690 | 55 |
| (6,-6,6) | NO (F = 0) | 24.00 | 22.50 | 3.92 | 0.557 | 44 |
| (7,-7,7) | yes | 28.00 | 26.72 | 4.28 | 0.469 | 37 |
| (8,-8,8) | yes | 32.00 | 30.89 | 4.54 | 0.406 | 32 |

(Values: `tools/reflection_step_phase_calculator.py`, checks T4 to T14 and T20; the (3,-3,3) and
(7,-7,7) rows and the `theta_int` column are tabulated by the script but not asserted. The orchestrator
reproduced the table independently, `docs/agent_reports/orchestrator_sanity_numbers.txt`, and the
adversarial reviewer confirmed every printed digit.)
A non-relativistic treatment (`Delta = V0/T`) would give 14.00 mrad and a step phase of 3.14 rad
(indistinguishable from pi) at (4,-4,4); `V0/T` is 14 percent too small (equivalently the relativistic
`Delta` is 16 percent larger) and must not be used.

Sensitivity to the mean inner potential: `d|Delta_phi|/dV0` is -0.34 rad/V at (4,-4,4) and
-0.20 rad/V at the (6,-6,6) setting; the external peak angle moves by -0.21 mrad/V and -0.13 mrad/V
respectively. If the glancing angle is not measured
but taken as the external angle of the internal Bragg condition computed with the assumed `V0`, a
height inferred from a fixed, correctly unwrapped phase, `h_inf = |Delta_phi|/(2 k sin theta_ext(V0))`,
rises by 1.56 % of h per volt of assumed `V0` at (4,-4,4) (0.049 A/V for a bilayer) and by 1.07 %/V at
(0,0,8) (0.029 A/V for an a/2 step). Underestimating `V0` therefore makes the height too small, by an amount
proportional to h. If `theta_ext` is measured
independently (item 7), `V0` does not enter the height (`tools/phase1_numbers.py`, premise in its
docstring; revision 3 corrects the sign of the earlier wording "+0.05 A per volt of underestimate"). `V0` is a first-order systematic, not a
correction, and must be a sourced input with an uncertainty (`docs/06_project_inputs_required.md`, item 20).

Si(001), single-layer step `a/4 = 1.358 A` (terraces NOT translation-related; the kinematic value is only
indicative) and double-layer `a/2 = 2.716 A`, specular orders (004), (008), (0,0,12): see the calculator
output section 4b (`docs/agent_reports/C_calculator_output.txt`).

## 4. The 2 pi branch problem, coherence and shadowing

A single hologram gives `h` modulo `h_2pi = lambda/(2 sin theta_ext)`, which is 0.4 to 1.5 A for all
usable conditions at 200 keV. A 3.1 A bilayer step is 3.4 wraps at (4,-4,4); a 10 nm patterned step is
about 110 wraps at (4,-4,4). Consequences:

* Atomic steps: the branch must come from a lattice constraint (h is an integer multiple of the layer
  spacing) or from a rocking series: `d|Delta_phi|/d(theta) = (4 pi h/lambda) cos(theta)`, which is
  1.57 rad/mrad for a bilayer, 5.0 rad/mrad for 1 nm and 50 rad/mrad for 10 nm. The phase increment per
  tilt step must stay below pi: below 0.63 mrad for `h = 1 nm` (check T23) and about 0.06 mrad for
  `h = 10 nm` (not asserted by a check). Phase precision is not the limit: with fringe contrast 0.5 and
  1e4 counts in the aperture area, `sigma_phi = 0.028 rad`, i.e. 0.004 A at (4,-4,4) (`h_2pi = 0.919 A`).
* Illumination convergence is the limit for tall features. The same derivative converts the
  illumination convergence semi-angle into an irreducible phase spread over the incoherent ensemble:
  1 rad of spread is reached at 0.64 mrad for a bilayer, 0.20 mrad for 1 nm and 0.020 mrad for 10 nm.
  A tilt step can be made finer; a convergence angle cannot, so this decides whether a 10 nm feature is
  measurable at all (`docs/06_project_inputs_required.md`, item 3, blocking). Energy spread is harmless
  by comparison: `d ln(lambda)/dT = -2.9e-6 per eV`, so a 0.7 eV spread changes the step phase by less
  than 0.004 rad over the whole allowed rod, even for a 10 nm step.
* Shadowing. A step transverse to the beam whose upper terrace is upstream casts a geometric shadow of
  length `h/tan(theta_ext)` on the surface behind it. At 22.5 mrad (a round illustrative angle; it is
  the external angle of the forbidden (6,-6,6) condition) that is 139 A per Si(111) bilayer, 60 A per
  Si(001) layer and 444 nm for a 10 nm mesa; at the first recommended condition (4,-4,4), 13.6 mrad,
  it is 230 A per bilayer and 733 nm for a 10 nm mesa; at (8,-8,8), 102 A and 324 nm. Shadow masks
  must be computed at the actual operating angle, never hard-coded. Inside the shadow there is no object wave and the
  reconstructed phase is meaningless; in the foreshortened image the shadow is `1/sin(theta)` times
  narrower than on the surface but still much wider than the riser. The shadow direction distinguishes
  an up-step from a down-step. Every configuration must compute and mask the shadowed strips before
  quantification, and the geometric-phase model must ray-trace visibility rather than evaluate `-q.R`
  alone. (The inspected repository's benchmark avoids the issue by running the step edges parallel to
  the beam.)
* Nanometre-scale ion-milled patterns: the step riser is a phase discontinuity of many wraps and the
  terrace behind it is shadowed; the hologram measures the shape of the visible terraces, and the riser
  height only through a fine rocking series with an illumination convergence far below 0.02 mrad.

## 5. What a transmission multislice can and cannot do at grazing incidence

* Propagator: specular reflection at 22 mrad changes only the transverse wavevector by `2 k sin(theta)`;
  the longitudinal component is unchanged, so the wave is forward-propagating along the beam axis. The
  paraxial Fresnel error `k dz sin^4(alpha)/8` over the 198 A default cell is 0.002 rad at the 24 mrad
  tilt, 0.026 rad at the 45 mrad specular scattering angle and 0.106 rad at the 64 mrad band edge
  (values corrected by the adversarial review; the C report's section 5.1 numbers are three times too
  small because they expand the cosine in the angle rather than in the transverse wavevector). The error
  is common-mode between two terraces reflecting into the same `k_out` and cancels in the step phase,
  but it is not negligible against the 0.028 rad phase-noise figure of section 4 for absolute phases,
  which is why an exact propagator is preferred (`docs/05_final_repository_specification.md`, section 4.3).
* Boundary conditions ARE the obstacle. With the inspected repository's defaults (10 A declared vacuum
  above and below an 85 A plate, 138 A of crystal along the beam, periodic in the surface normal):
  only rays within `L_z,si tan(theta) = 3.11 A` of the surface reach it inside the crystal (31 percent of
  the declared 10 A top gap; 19 percent of the realised 16.1 A periodic vacuum channel between plate
  images, which the generator declares as 2 x 10 A, A report section 2a); the reflected beam rises
  4.46 A over the full 198 A cell, which is what must stay below the vacuum margin; 81 percent of the
  incident plane wave on the declared geometry (85 percent on the realised atom positions) enters the
  crystal through the front end face (Laue transmission through a plate 8.5 nm thick as declared,
  8.9 nm as realised);
  the refracted ray crosses only one bilayer over the whole slab, so no Bragg-case reflection can
  develop; and the Laue-transmitted (n,-n,n) beam leaves in the same direction as the specular beam, so
  a k-space aperture cannot separate top-surface reflection, end-face transmission and back-face
  reflection. For the vacuum illumination to reach the surface at all, `L_z >= x_vac/tan(theta) = 444 A`
  for a 10 A gap; for a Bragg-case reflection to build up over a normal penetration depth of 2 to 10 nm,
  `L_z` must be 0.08 to 0.42 um at `theta_int = 24 mrad`.
* Sampling: with a 2/3 anti-aliasing rule the 0.13 A pixel supports 64 mrad at 200 keV (adequate; check
  T21); the generator's default 0.5 A advisory pixel (realised 0.4845 A) gives 17.3 mrad under the 2/3
  rule and 12.9 mrad under Prismatic's half-Nyquist rule (16.7 and 12.5 mrad at the nominal 0.5 A), so
  it cannot represent the 24 mrad tilt under either (check T22; D report section 2c reproduces the
  resulting `IndexError`). Prismatic's ceiling at 0.13 A is 48 mrad.
* Requirements for a valid reflection cell: no vacuum below the back face (semi-infinite emulation with
  an absorbing or apodising region on the bulk side of the surface normal); vacuum margin above the
  surface larger than the illumination height plus `L_z tan(theta)`; illumination confined to the vacuum
  band and launched upstream of the crystal; cell length along the beam set by the footprint
  `H/tan(theta)` (889 A for `H = 20 A` at 22.5 mrad) and by the dynamical build-up length; an allowed
  reflection; absorption from a sourced optical potential; validation against a surface-parallel
  dynamical reflection solver (Ichimiya-type, e.g. `sim-trhepd-rheed`) or a Bragg-case Bloch-wave
  solution, in the flat-surface limit, before any step is simulated.

## 6. Image geometry and hologram formation

* The simulated wave on the plane `z = L_z` is not the image. Select `k_out`, remove the carrier, and
  project along `k_out`: a surface feature at position `z_s` along the beam appears at exit-plane height
  `x = x_0 - z_s tan(theta)`, with `x_0` the exit-plane height of a feature at `z_s = 0`; the surface
  coordinate is recovered as `z_s = (x_0 - x)/tan(theta)`, a `1/tan(theta)` (about 44x at 22 mrad)
  magnification of the exit-plane height axis.
* Hologram: `I = |u_o + u_r|^2 = |u_o|^2 + |u_r|^2 + 2|u_o||u_r| cos(2 pi q_c.r + phi_o - phi_r)`.
  Sideband non-overlap requires `q_c > 3B` for an object bandwidth `B`, so the reconstructed resolution is
  about three fringe spacings; fringes need 3 to 4 pixels each.
* Reference models that must be explicitly selectable and reported: R1 vacuum plane wave (measures the
  absolute reflected phase including `phi_R`; a vacuum reference beside the specimen is inclined by
  `2 theta_ext` to the specular beam, 17 to 62 mrad over orders 3 to 8, which the optics must
  compensate to obtain a recordable fringe spacing); R2 self-reference from a flat region of the same
  surface (common-mode phases cancel; a mirrored twin of the reference region appears in the result);
  R3 reference with residual curvature and tilt (long-wavelength topography is entangled with the
  reference phase). The hologram model must also contain the biprism's own Fresnel fringes and finite
  overlap width, specimen drift as a coherent envelope loss, and the possibility of specimen charging
  (an added, drifting phase indistinguishable from topography), each as a declared option.
* Phase noise of the sideband estimate: `sigma_phi = sqrt(2)/(mu sqrt(N))` with fringe contrast `mu` and
  `N` counts in the reconstruction aperture area.
* Processing trap verified in the calculator (check T24, section 12 of its output): the brightest Fourier
  bin of an object hologram with a 50/50 phase step is not the carrier; recentring on it produced a
  plausible but wrong step (0.78 rad instead of 2.36 rad). The carrier must be located on an empty
  hologram or on the sideband envelope. The code audit found the same defect in the inspected
  repository's `find_peak` (A report, C3).

## 7. Numbers a corrected repository must reproduce

See `docs/agent_reports/C_physics_derivations.md` section 8 (checks T1 to T25) and the qualitative
checks listed there: sign test for a down-step, forbidden-reflection guard, accessibility guard
(`G.n_hat >= 2 dK`, `dK = k sqrt(Delta)`), small-denominator policy with a propagated height
uncertainty, periodic-boundary continuity of the terrace staircase, footprint and wrap-around
assertions, rocking-series branch resolution, the carrier-location test, and (added after the review)
a shadow-mask test (`h/tan(theta)`) and a phase-validation ladder for the reflection engine
(`docs/05_final_repository_specification.md`, section 4.4).
