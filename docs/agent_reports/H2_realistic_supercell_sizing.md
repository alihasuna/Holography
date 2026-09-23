# H2: supercell for a physically realistic reflection multislice run (Si(001), 200 keV, (0,0,8))

Agent H2, 2026-09-23. Written incrementally; the final state is the table and run order at the end.
Branch `claude/electron-holography-orchestration-nakd7r` (HEAD 44c5a4a at start of the
measurements). Nothing committed or pushed by H2. Beam energy 200 keV throughout (PROJECT_INPUT item 1;
300 keV is never used).

Question (Ali): "The idea is to have all ready to ssh connect and run the simulation as more
physically correct and realistic. What will be the super cell size in this case?"

Tool: `tools/hpc/supercell_sizing.py` (prints every number below; self-checks; exit status 1 on any
failure). Stored inputs it reads: `tools/hpc/supercell_sizing_cpu_calibration.json` (its
`--calibrate` mode) and `tools/hpc/supercell_sizing_measurements.json` (its `--measure` mode: engine
runs on flat strips in this container).

## 0. Log

- 20:35 UTC: read README, physics_conventions, 03 physics summary, model_assumptions (B1-B34), 05
  (sections 0-4, 9), 06, M2 (all, section 10 in detail), T1, T2, the null-test study
  (README, study.yaml, run_study.py, tests/forward/null_test_cases.py), constants.py, the engine
  (engine, grid, potentials, illumination, physics, propagator, backend), forward/cell.py,
  feature_cell.py, structure/si001.py, features.py (header), shapes.py, demo_hpc_si001.yaml,
  scripts/hpc/README_HPC.md, the pipeline's NOT_IMPLEMENTED lists.
- 20:45 UTC: first numbers (scratch): the engine's Kirkland Fourier coefficient V(0,0,8) = 1.036 V,
  not the 0.84 V estimate of M2 section 10.2. At the exact [100] azimuth the (0,+-4,4) beams lie
  exactly on the Ewald sphere at the (0,0,8) condition (surface-parallel inside the crystal), so
  that condition is at least four-beam; a many-beam complex-band-structure prototype gave
  penetration depths very different from the two-beam value at both azimuths. Decision: measure
  the build-up length and the depth profile with the engine itself on flat strips (the exit-plane
  height maps back onto the surface point where the reflected ray left it), instead of relying on a
  two-beam estimate.
- 20:50 UTC: a scratch prototype on a flat [100] strip showed that the build-up curve and the depth
  profile can be read from ONE exit wave; its numbers are superseded by the tool's run `bu_100_r010`
  (section 2.4) and are not quoted.
- 20:58 UTC: CPU calibration written (load average 0.3); engine measurements started in the
  background (5 runs, about 1 h).
- 21:08 UTC: first full test of the report mode: the replica of `estimate_resources` equals the
  engine's accounting byte for byte on all 17 study.yaml points and reproduces the M2 printout
  (grid, slices, atoms, MB, GPU s). The engine rejected my first layout (item 4) because I had passed
  the clean depth as `buildup_depth_A`; that parameter is the engine's minimum-penetration assertion
  (20-100 A) and is now 20 A, separate from the clean depth derived below.
- 21:34 UTC: all five engine measurements written (the frozen-phonon run last). Final run of the
  tool at HEAD 7ab6210 (the orchestrator's snapshot commits of this work; engine, forward tests and
  the null-test study unchanged since 44c5a4a): 41/41 checks pass, exit status 0 (section 11).

## Answer in brief

Condition: Si(001), exact [100] azimuth (B20), (0,0,8) at 16.1347 mrad, 200 keV, the engine's
Kirkland potential, dx = dy <= 0.13 A, dz = a/4, complex64. Four lengths set the cell, and none of
them is a free choice:
* along the beam: the run-in after the illumination edge until the reflected wave has settled,
  MEASURED with the engine: 2500 A for the TEST_ONLY absorption r = 0.1, 5000 A for r = 0.05 and
  8000 A without absorption (where the two-beam tail predicts 22 572 A). To that add 3 resolution
  elements of reconstruction margin (1116 A), the field to be measured, and 3 elements of exit
  margin (1116 A);
* depth: 15 A absorber plus 55-65 A of clean crystal (MEASURED; the current study cells have 21 A);
* vacuum: the engine's rule H + L_z tan(theta), about 2 L_z tan(theta): 178-402 A (about half of it
  would do physically);
* across the beam: two terraces of the miscut width for steps parallel to the beam (0.1 deg:
  782 A each for a/4 steps), or the ring plus a 143-236 A gap between its periodic images.

| run (r = 0.1 unless stated) | x by y by z (A) | atoms | grid, slices | engine arrays per realisation | per realisation GPU (ASSUMPTION model) / CPU (4 cores here, x1.5) | total with 8 phonon realisations |
|---|---|---|---|---|---|---|
| single a/4 step parallel to the beam, 0.1 deg miscut | 259 x 1564 x 5602 | 31.1 M | 2000 x 12096, 4126 | 4.1 GB (7.5 GB host peak, code reading) | 13 min / 17.2 h | 103 min GPU |
| same, r = 0.05 | 350 x 1564 x 8100 | 51.0 M | 2700 x 12096, 5966 | 5.8 GB (12.2 GB host peak, code reading) | 28 min / 33.6 h | 3.7 h GPU |
| half-torus R = 1000 A, r = 20 A | 422 x 2183 x 9420 | 93.5 M | 3360 x 16800, 6938 | 10.9 GB (22.4 GB host peak, code reading) | 82 min / 3.8 d | 10.9 h GPU |
| half-torus, r = 0.05 | 512 x 2276 x 11924 | 136.2 M | 3969 x 17640, 8782 | 14.4 GB (32.7 GB host peak, code reading) | 2.4 h / 6.5 d | 19.4 h GPU |

The complete table (study.yaml reference, a/2 steps, steps transverse to the beam, the narrowest
converged terrace, no absorption, the validation rocking curve, and the blocked patterned case)
and the run order are at the end. These are cell sizes for runs that would be converged in the
engine's own physics. They are not yet physically validated results. The engine is UNVALIDATED
(rung 2, the abTEM cross-check and a dynamical rocking curve not run). The absorption that sets
z is a TEST_ONLY stand-in, since PROJECT_INPUT item 21 is missing. At exact [100] the (0,0,8)
condition turns out to be a four-beam surface-resonance case (section 2.2). At [110], the M2 study
azimuth, the same angle reflects six times more weakly (section 2.4). The static lattice
overestimates the specular amplitude by 1/0.72 and shifts its phase by 0.046 rad, so phonons are
needed (section 6).

## 1. Premises, conventions, labels

Conventions of `docs/physics_conventions.md`: `exp(+i k.r)`; angular wavevectors (k, K, G, q, eta,
b, c) in rad/A; reciprocal vectors g and spatial frequencies f in cycles/A (G = 2 pi g); theta is the
glancing angle to the surface (external or internal as written); x is the outward normal (crystal at
smaller x); the step phase is signed as in the conventions (not needed for sizing). Evidence labels
as in the instruction file; MEASURED_HERE marks a number measured in this container with the
repository's UNVALIDATED engine on the stated TEST_ONLY/ASSUMPTION inputs (a REPRODUCED-type
number whose premises are those inputs).

Fixed inputs of every number below (labels in brackets):

| Input | Value | Label |
|---|---|---|
| beam energy | 200 keV | PROJECT_INPUT item 1 (Ali, 2026-09-22) |
| surface, preparation | Si(001), ion-milled | PROJECT_INPUT items 11, 12 (partly supplied) |
| lattice parameter | 5.4309 A (`constants.A_SI_A`) | ASSUMPTION B2 |
| potential | Kirkland IAM via abTEM 1.0.10, infinite projection per slice, exact structure factors (the engine's `AtomicPotential`) | SECTION_READ of abTEM source (D3); parameterisation UNVERIFIED (SM17) |
| mean inner potential of that potential | 13.902843 V | REPRODUCED (D3 F16) |
| working reflection | (0,0,8) | ASSUMPTION B17 (item 9) |
| glancing angle | external angle of the (0,0,8) internal Bragg condition with V0 = 13.9028 V: 16.1347 mrad (internal 18.4719 mrad) | ASSUMPTION B32 (item 7) |
| azimuth | exact [100] for production (B20); [110] only to compare with the M2 study | ASSUMPTION B20 / TEST_ONLY (item 8) |
| absorption | proportional V' = r V with r = 0.05 or 0.1 | TEST_ONLY (item 21 missing); r = 0 is ASSUMPTION B30 |
| thermal displacement | 0.076 A rms per axis | ASSUMPTION A7 (the inspected repository's value, also the value in Prismatic's example input SI100.XYZ, L2 C14; no Debye-Waller measurement or calculation for Si has been read) |
| image resolution | 6.0 A in the image plane (T2) = 371.8 A of surface along the beam at 16.1347 mrad (T2 quotes 364 A at the B19 angle 16.4743 mrad) | ASSUMPTION chain B28/B29 (items 16, 19) |
| reconstruction margin | 3 resolution elements around every unusable region | ASSUMPTION B29 (item 19) |
| dark-field aperture | 3 mrad = 0.1196 1/A | ASSUMPTION B22 (item 4) |
| numerical absorbers | 100 V, sin^2, bulk 15 A, top 10 A | NUMERICAL (engine practice of M2, T1, demo_hpc; effectiveness untested, M2 section 9) |
| sheet beam | gap 2 A above the highest surface, sin^2 edges 2 A | NUMERICAL (M2 practice) |
| phase tolerance for every convergence length | 1e-2 rad | the M2 fixed-beam translation criterion (docs/05 4.4 rung 3); not a PROJECT_INPUT |

## 2. z (along the beam): build-up, run-in, field of view, exit margin

### 2.1 Two-beam Bragg case from the engine's own Fourier coefficient (DERIVED_HERE)

Premises. P1: two beams only, the refracted incident beam and the specular (0,0,8) beam. P2: the
engine's physics: the transmission `exp(+i sigma V_p)` with the exact propagator reproduces
`K^2 = k^2 + 2 k sigma V` for the mean potential, so a Fourier coefficient V_g couples beams with
`u_g = 2 k sigma V_g` (rad^2/A^2); the internal Bragg condition from the exact SM04 refraction
agrees with this dispersion to 4e-10 (check `bragg_internal`). P3: symmetric Bragg case (reflecting
planes parallel to the surface), semi-infinite bulk-terminated crystal, plane-wave components.
P4: absorption, when present, is the engine's proportional model `V' = r V` (so `V0' = r V0`,
`V_g' = r V_g`). P5: first order in eta/G (|eta| < 0.06 rad/A against G = 9.26 rad/A); the exact
two-beam quartic gives |Im q| = 0.040867 rad/A against b = 0.040868 rad/A (check `two_beam_exact_root`).

With `kappa0` the normal component of the refracted incident wave, `eta = kappa0 - G/2`, the two
Bloch solutions have normal wavevectors `q - G/2` and `q + G/2` with `q^2 = eta^2 - c^2`,
`c = u_g/G`, and the internal reflection ratio `X = -(eta + q)/c`, physical branch
`q = -sqrt(eta - c) sqrt(eta + c)` (principal roots; |X| <= 1, Im q < 0 into the crystal).

Numbers (script section 2, 3):
* V(0,0,8) = 1.0357 V (|S| = 8, Kirkland F at |g| = 1.4731 1/A). M2 section 10.2 estimated
  0.84 V; the engine's own coefficient is 23 % larger.
* b = u_g/G = 0.04087 rad/A: amplitude penetration at the stop-band centre Lambda = 1/b = 24.47 A.
* Extinction distance xi_g = pi/(sigma V_g) = 4161.7 A. Along the surface the build-up scale is
  L_b = 1/(b tan theta_int) = 1324.5 A = xi_g/pi to 1.3e-4 (the depth Lambda is reached along the
  internal ray over Lambda/tan theta_int).
* Comparison with M2's "~1600 A": 1/(sigma x 0.84 V) = 1633 A; with the engine's V_g the two-beam
  scale is 1325 A (-19 %). The M2 number was the same formula with a low V_g, not a different model.
* Darwin full width (two-beam): 0.3263 mrad internal, 0.3736 mrad external.
* At the Bragg angle: r = 0: |X| = 1.0000 (total reflection), depth 24.47 A; r = 0.05: |X| = 0.534,
  depth 20.3 A; r = 0.1: |X| = 0.333, depth 14.6 A.

### 2.2 The two-beam picture does not hold at this condition (DERIVED_HERE, many-beam bookkeeping)

Premise: forward scattering along z, so a beam h = (g_x, g_y) of the transverse reciprocal plane
(zero component along the beam) has excitation error
`zeta_h = (kappa0^2 - (2 pi g_x - kappa0)^2 - (2 pi g_y)^2)/(2K)`; admixture `sigma(|V_h| + |V_g-h|)/|zeta_h|`
(second-order perturbation, Bethe), with all Fourier coefficients from the engine's potential.

* Exact [100] azimuth: the (0,+-4,4) beams have zeta = 0 exactly (|g_044 - g_008/2| = |g_008|/2, a
  Thales-circle coincidence independent of energy and V0). They travel parallel to the surface inside
  the crystal (k_x = 0), deflected by +-18.47 mrad in y, cannot leave into vacuum, and couple with
  sigma|V_044| = 1.22e-3 rad/A, larger than sigma V_008 = 7.55e-4 rad/A. The (0,0,8) condition at
  exact [100] is therefore at least a four-beam (surface-resonance-like) case, where perturbation
  theory fails. In addition (0,+-2,2) and (0,+-2,6) have admixture 0.20 each (9.24 mrad in y), and
  the perturbative Bethe terms alone would change the effective coupling to 0.49 V_g and move the
  stop-band centre by 0.62 half-widths.
* [110] (the M2 study azimuth): no exactly excited beam, but (+-1,-+1,1) and (+-1,-+1,7) have
  admixture 0.35 (6.53 mrad in y) and (+-3,-+3,3), (+-3,-+3,5) 0.21 (19.59 mrad).

Consequence: the two-beam L_b, Lambda and Darwin width are order-of-magnitude guides only. The
build-up length and the penetration depth used for sizing are MEASURED with the engine (section 2.4),
which carries these beams (at dx = 0.13 A all of the above lie inside the 2/3 band).

### 2.3 Leading-edge transient (DERIVED_HERE)

Premises P1-P5 plus: the illumination on the surface switches on at the bottom-edge contact point
(a sharp edge; the 2 A sin^2 edge smooths it over 124 A, far below the transient scale) and is uniform
downstream. The tangential deviation p of the incident wavevector changes eta by -p cot(theta_int);
Fourier-transforming X over p gives the surface Green's function

    g(s) = i J1(c s) exp(i eta0 s) / s,     s = z tan(theta_int) >= 0 (zero upstream),

which integrates to X (steady state). Checks: the closed form equals a direct numerical transform of
X(eta0 - p) to 1.5e-4 (r = 0) and 5.9e-5 (r = 0.1) of |c|/2, and vanishes upstream to 2e-4 (checks
`green_closed_vs_numeric_*`, `green_causal_*`). The relative error of the reflected field at a
distance L downstream of the edge is `E = 1 - (1/X) i integral_0^s J1(c s') exp(i eta0 s')/s' ds'`.
Without absorption its envelope decays only algebraically, `sqrt(2/pi) (b s)^(-3/2)` (checked to 5 %
at b s = 20 and 50); absorption adds `exp(-sigma r (V0 - V_g) L)` (slow component) and
`exp(-sigma r (V0 + V_g) L)`.

Two-beam run-in lengths (envelope of |E| below the tolerance beyond L; script section 6):

| r | |E| at 1000 / 2000 / 3000 / 5000 / 10000 A | L for 1e-2 | L for 3e-3 | L for 1e-3 |
|---|---|---|---|---|
| 0 (B30) | 0.63 / 0.31 / 0.080 / 0.092 / 0.035 | 22 572 A | 51 572 A | 113 552 A |
| 0.05 (TEST_ONLY) | 0.46 / 0.17 / 0.045 / 7.9e-3 / 3.6e-4 | 3721 A | 6712 A | 7538 A |
| 0.1 (TEST_ONLY) | 0.30 / 0.074 / 0.014 / 6.7e-4 / 1.5e-5 | 3194 A | 3762 A | 4290 A |

This is consistent with M2's observation that without absorption the null-test error "oscillates in
sign up to 6600 A": the two-beam field needs 2.3 um to settle to 1e-2 rad and 11 um to 1e-3 rad.

### 2.4 Build-up and depth measured with the engine (MEASURED_HERE; script `--measure`, section 7)

Method (DERIVED_HERE). Flat bulk-terminated Si(001) strips, (0,0,8) at 16.1347 mrad, Kirkland
potential, static lattice, exact propagator, 2/3 band, complex64, dx = dy <= 0.13 A, 100 V sin^2
absorbers (bulk 15 A, top 10 A), clean depth 100 A, entrance vacuum 10 slices, sheet beam 2 A above
the surface whose top edge lands 1 A before the exit plane (H = L tan(theta) - 3 A). One period of
the crystal along the beam is built with every builder assertion and tiled (exact for a flat
terrace). In the exit plane the vacuum above the surface contains only the reflected wave, and the
ray found at height x left the surface at `z_s = L_z - (x - x_s)/tan(theta_ext)`. So the y-averaged
exit wave, masked to the vacuum (sin^2 taper from 2 A above the top layer), band-passed within
0.1 1/A of f_c = sin(theta)/lambda and demodulated, gives the local specular amplitude R(z_s)
at every surface point of the strip from ONE run. Resolution: 5 A in x, 310 A in z_s. The 0.1 1/A pass band
excludes the internal Bragg wave (0.093 1/A from f_c) and the steeper (0,0,l) exit beams. Bins of
500 A from the bottom-edge contact point; the reference is the mean over the last 2500 A before
the last 750 A. The strip is converged beyond L when every later bin up to the end of the reference
window is within the tolerance and the reference window itself is flat to 1e-2 rad and 3e-2. The distances are bin edges: resolution 500 A, and the
read-out is blurred by the pass band (5 A in x, 310 A of surface) and by free-space diffraction
between the surface and the exit plane (sqrt(lambda D)/tan(theta_ext): 310 A for D = 1000 A, 760 A
for D = 6000 A).

| run | azimuth, r | strip after contact | plateau |R| | reference window flat to (phase / amplitude) | phase within 1e-2 rad beyond | amplitude within 3e-2 beyond | last 500 A before exit | depth where exit-plane I > 1e-2 / 1e-4 |
|---|---|---|---|---|---|---|---|---|
| bu_100_r010 | [100], 0.1 | 6000 A | 0.271 | 0.0025 rad / 0.005 | 1500 A | 2500 A | -0.037 rad | 26.0 / 53.2 A |
| bu_100_r005 | [100], 0.05 | 9000 A | 0.457 | 0.0012 rad / 0.009 | 5000 A | 2500 A | -0.045 rad | 30.2 / 60.6 A |
| bu_100_r000 | [100], 0 | 12000 A | 0.891 | 0.0038 rad / 0.010 | 8000 A | 7000 A | -0.047 rad | floor ~1e-2 down to the absorber |
| bu_110_r010 | [110], 0.1 | 6000 A | 0.043 | 0.036 rad / 0.021 (NOT flat) | (5000 A) | (3000 A) | +0.36 rad | 30.8 / 64.2 A |

Reading:
* [100], r = 0.1: the phase settles within 1e-2 rad after 1500 A and the amplitude within 3 % after
  2500 A; the two-beam estimate (3194 A for 1e-2 rad) is conservative here. The design run-in is
  2500 A (phase 1e-2 AND amplitude 3e-2).
* [100], r = 0.05: the phase overshoots by -0.027 rad around 3000-4000 A and settles after 5000 A;
  the two-beam estimate (3721 A) is too short here. Design run-in 5000 A.
* [100], r = 0: the amplitude reaches 0.89 by 3000 A, then amplitude and phase oscillate (phase
  -0.067 rad at 3000-3500 A, +0.086 rad at 6000-6500 A) and settle within 1e-2 rad after 8000 A in
  this strip (tested only to 11 251 A). The two-beam tail predicts 22 572 A. Without absorption 0.207
  of the incident intensity is not reflected into the specular beam (|R|^2 = 0.793); the exit-plane
  intensity stays near 1e-2 down to the bulk absorber, which therefore carries the transmitted wave
  and must not reflect it.
* [110], r = 0.1 (the M2 study azimuth): at the two-beam Bragg angle the specular amplitude is only
  0.043 (six times weaker than at [100]) and its phase beats by +-0.036 rad over the whole strip, in
  a strongly many-beam regime (section 2.2). Where the [110] reflection maximum lies is for the
  rocking curve (run order step 2); the M2 study's convergence lengths at this angle do not transfer
  to [100].
* Exit margin: the last 500 A before the exit plane are off by 0.037-0.047 rad in every [100] run
  (0.36 rad at [110]); the reflected ray is then less than 500 tan(theta_ext) = 8 A above the
  surface, where the pass band mixes it with the crystal. The 3-resolution-element exit margin of
  1115.5 A (section 2.6) covers this.
* Two-beam against engine plateau amplitude: 0.333/0.271 (r = 0.1), 0.534/0.457 (r = 0.05), 1.000/0.891
  (r = 0): the engine reflects less than the two-beam model, consistent with the many-beam losses of
  section 2.2.

### 2.5 Absorption lengths of the TEST_ONLY stand-ins (DERIVED_HERE; script section 5)

With the proportional model the mean imaginary potential is r V0 (0.695 V for r = 0.05, 1.390 V for
r = 0.1). Amplitude 1/e length along the path 1/(sigma r V0): 1974 A (r = 0.05) and 987 A (r = 0.1);
intensity lengths half of that (987, 493 A). The slow two-beam transient decays over
1/(sigma r (V0 - V_g)) = 2133 A and 1066 A (the standing wave has its nodes on the (008) planes and
absorbs less than the mean). A refracted wave outside the Darwin band loses 1/e of its amplitude
over sin(theta_int)/(sigma r V0) = 36.5 A and 18.2 A of depth. These numbers say how strong the
stand-ins are at glancing incidence. They are not a statement about real Si: item 21 is missing.

### 2.6 Field of view, margins and the z layout (DERIVED_HERE)

Along the beam one image resolution element is 371.8 A of surface (6.0 A in the image plane,
foreshortening 1/sin(theta_ext) = 61.98). Rules:
* entrance vacuum 10 slices (13.6 A at [100]); the sheet beam's bottom edge reaches the surface at
  z_contact = gap/tan(theta_ext) = 124 A;
* run-in L_run after contact: 2500 A (r = 0.1), 5000 A (r = 0.05), 8000 A (r = 0, B30), section 2.4;
* the reconstruction margin upstream of the first measured region: 3 elements = 1115.5 A (B29);
* measured regions: 2 resolution elements (743.6 A) along the beam per terrace region (ASSUMPTION);
  a step transverse to the beam adds a margin, the shadow or blocked-view strip (84.1 A for a/4,
  168.3 A for a/2), a margin and the second region; the half-torus adds its strips
  (h/tan(theta_ext): 1178 A for the 19.01 A crest, 1262 A for the 20.37 A floor) around its 2040 A;
* exit margin 3 elements = 1115.5 A (covers the measured 500 A of exit contamination);
* L_z = z_contact + L_run + field + exit margin, rounded up to whole periods along the beam; the
  sheet beam height H = L_z tan(theta_ext) - gap - step height - 1 A so that the footprint reaches
  the exit plane (engine item 3) and the whole field is in the fully lit core.

## 3. x (surface normal): depth, vacuum, absorbers, features, overlayer (DERIVED_HERE)

* Bulk side: numerical absorber 15 A (inside the crystal) + clean depth D_clean. D_clean is the
  depth at which the measured exit-plane intensity is below 1e-4 (amplitude 1e-2), so the absorber
  perturbs the reflected wave at about the round-trip level 1e-4: 55 A (r = 0.1), 65 A (r = 0.05);
  for r = 0 the transmitted floor reaches the absorber and the evanescent part is taken as for
  r = 0.05 (65 A). The engine's own build-up assertion depth `buildup_depth_A` is set to its minimum
  20 A (at [100], r = 0.1, the measured exit-plane intensity already falls from 2.1e-1 at 10 A to
  1.9e-2 at 20 A); the clean depth is the physical requirement. The current study cells use a clean depth of 21 A (null_test_cases.py); at 20 A the
  measured exit-plane intensity is still 1.9e-2 at [100] and 4.2e-2 at [110] (r = 0.1).
* A trench adds its depth below the flat surface (20.37 A for the half-torus floor).
* Vacuum above the highest top layer: the engine rule (item 2) requires more than H + L_z tan(theta);
  with H close to L_z tan(theta) this is about 2 L_z tan(theta) (the reflected ray from the first
  contact rises L_z tan(theta) by the exit plane, and the incident sheet occupies H at the entrance).
  A ridge adds its height (19.01 A), an overlayer its thickness.
* Top absorber 10 A.
* Overlayer (item 12, ASSUMPTION thicknesses): 10, 20, 30 A add that much to x and are crossed over
  2 t/sin(theta_ext) = 1240, 2479, 3719 A of glancing path (in and out). No overlayer run is possible
  with the engine as it stands (N5).

## 4. y (across the beam, periodic) (DERIVED_HERE)

* Terrace width from the miscut (ASSUMPTION scenarios for item 11), W = h/tan(miscut):
  0.05 deg (0.873 mrad): 1555.8 A (a/4 steps), 3111.7 A (a/2 steps); 0.1 deg: 777.9 / 1555.8 A;
  0.25 deg: 311.2 / 622.3 A; 0.5 deg: 155.6 / 311.2 A.
* With edges parallel to the beam the only periodic staircase the builder accepts is up-down (N6):
  the y period is 2W (two terraces, one up-step and one down-step).
* Lateral buffer from a step edge parallel to the beam: the disturbance travels sideways with the
  exactly or strongly excited in-plane beams, at most alpha_y = 18.47 mrad at [100] (the
  surface-parallel (0,+-4,4) beams; 19.59 mrad at [110]), for as long as the field remembers it,
  i.e. the run-in length. dlat = L_run tan(alpha_y) + 3 x 6 A (B29 margin across the beam, not
  foreshortened) = 64.2 A (r = 0.1), 110.4 A (r = 0.05), 165.8 A (r = 0). Minimum terrace
  W_min = 2 dlat + 2 x 6 A = 140.4, 232.7, 343.6 A. This is an estimate with a stated premise (the
  memory length equals the run-in); the terrace-width study (run order step 5) decides it.
* Periodic images of an isolated feature (half-torus): gap between the ring and its image
  2 dlat + 12 A (143.2 A at r = 0.1, 235.5 A at r = 0.05), with the builder's ring margin (one
  period) included.
* Transverse steps: the structure is uniform in y; 16 periods (86.9 A, 14 resolution elements, the
  demo_hpc width) give the phase statistics.

## 5. Sampling: dx, dy, dz (DERIVED_HERE; 2/3 band limit f_max = 1/(3 dx), label of the rule UNVERIFIED, SM15)

What must be carried, and the pixel it needs (script section 9):

| Must be carried | f (1/A) | dx needed (A) |
|---|---|---|
| incident beam, external | 0.6433 | <= 0.5181 |
| specular Bragg wave inside the crystal | 0.7365 | <= 0.4526 |
| the (0,0,8) coupling itself (transmission function) | 1.4731 | <= 0.2263 |
| (0,+-4,4) coupling at [100] (exactly excited beams) | 1.0416 | <= 0.3200 |
| (0,0,12) coupling, and the (0,0,16)-row beam's f_x | 2.2096 | <= 0.1509 |
| (0,0,16) coupling | 2.9461 | <= 0.1131 |

* The engine's `check_band` asserts only the beam angles, i.e. dx <= 0.4526 A; a grid between
  0.2263 and 0.4526 A would pass and silently drop the (0,0,8) Fourier coefficient from the
  transmission function (N8).
* dx = dy = 0.13 A (the M2/T1 practice) carries every exactly or strongly excited beam of section 2.2
  and the systematic row to (0,0,12); the perturbative Bethe correction of V(0,0,8) from couplings
  outside its band is 2.8e-2 V_g at [100] and 3.0e-2 V_g at [110]; at dx = dy = 0.10 A it is 4.5e-3
  and 8.2e-3. The Kirkland scattering factor at the band edge is 3.0 % (0.13 A) and 1.9 % (0.10 A) of
  its forward value. Recommendation: production at 0.13 A, with one convergence run at 0.10 A on the
  flat strip (run order step 2).
* dy = dx: the in-plane beams that carry the physics at [100] ((0,+-2,l), (0,+-4,l)) need f_y up to
  4/a = 0.7365 1/A, and the atoms' in-plane shape the same band as in x; a coarser dy would cut the
  non-specular channels that section 2.2 shows are strongly excited.
* dz: [100] dz = a/4 = 1.357725 A (every slice holds exactly one atomic plane; commensurate with the
  period a); [110] dz = p/4 = 0.960057 A (half the slices empty). The atoms of a plane act at the
  slice centre (a uniform shift along z, which does not change a specular phase, M2 section 4).

## 6. Frozen phonons (script sections 2, 7, 10)

* Thermal displacement u = 0.076 A rms per axis: ASSUMPTION A7 (see section 1; not sourced). With
  it the Debye-Waller amplitude factor of (0,0,8) is 0.7808 (intensity 0.6097), so the thermally
  averaged coefficient is 0.8087 V instead of 1.0357 V; for (0,4,4) 0.8836, for (0,2,2) 0.9695.
* Measured (run `fp_100_r010`, MEASURED_HERE): flat [100] strip, y = 3 periods (16.3 A), 3000 A after
  contact, r = 0.1 (TEST_ONLY), clean depth 60 A; one static run and 8 frozen-phonon realisations
  (engine `FrozenPhonons`, seed 20260923); dark-field selection with the B22 aperture (3 mrad =
  0.1196 1/A) on the vacuum part of the exit wave; region 1500-2252 A after contact, >= 5 A above
  the surface, 95 x-rows x 126 y-columns = 11 970 pixels. Ratio of the ensemble variance to the
  coherent intensity rho^2 = 9.37e-4 (rho = 0.031); by distance from the edge it falls from 5.7e-3
  (0-500 A) to 6.2e-4 (2500-3000 A).
* Realisations for a phase precision dphi per resolution element: N = rho^2/(2 dphi^2) = 4.69 for
  dphi = 1e-2 rad, so 5; a terrace mean over hundreds of elements needs fewer. Every production row
  uses N = 8 (ASSUMPTION: the fewest that still estimate the ensemble variance itself), which also
  covers the 1e-2 rad phase map of the torus.
* The ensemble matters for realism beyond the noise. The ensemble-mean specular amplitude is 0.721
  of the static-lattice one, and its phase differs by -0.0457 rad. A static-lattice run therefore
  overestimates the dark-field amplitude by about 39 % and misplaces its absolute phase by more than
  the 1e-2 rad tolerance. Both are common-mode for a step between identical terraces
  (translation-related, or glide-related within B4), but not for absolute phases, amplitudes,
  fringe contrast or the amplitude-based reliability masks of B29.
* Caveats: 8 realisations on a 16 A-wide, 3000 A-long strip; rho^2 still falls with distance, so the
  converged-region value is at most the one measured; a TDS-derived absorptive potential (N1) must
  not be added on top of explicit phonons.

## 7. Rocking angles (script section 11)

* Atomic steps (a/4, a/2) at a fixed angle: the branch comes from the lattice constraint (B29), so
  1 angle per step run.
* Validation rocking curve on the flat strip (docs/05 4.4, and to find the actual reflectivity
  maximum, N11): +-1.5 two-beam Darwin widths (+-0.560 mrad) at 1/6 of the width (0.0623 mrad):
  19 angles (ASSUMPTION design; the many-beam curve may be wider, so extend the range if the edges
  are not reached).
* B16 series for the half-torus (h_max = 20.37 A, per-hologram phase uncertainty 0.028 rad, the
  docs/03 example): tilt step at most 0.2963 mrad; 4 equally spaced angles over 0.889 mrad give a
  slope standard error of 0.084 A (<= 0.1 A, ASSUMPTION target). T2 showed the ring is not resolved
  at this condition, so this multiplier is listed, not included in the totals.

## 8. Cost model and its verification (script section 12)

* Memory and GPU time: `replica_memory` and `replica_gpu_s` in the script copy
  `engine.estimate_resources` line by line. On all 17 study.yaml points, built here with the M2 case
  code, the replica equals the engine's accounting to the byte and to 1e-12 in GPU seconds, and
  grid, slices, atoms, MB and GPU s equal the M2 printout (check
  `replica_equals_engine_and_M2_on_17_study_points`).
* GPU time: the engine's `GPU_ASSUMED` model (about 1 TB/s, cuFFT at 1/3 of it, 10 TFLOP/s complex64
  GEMM, 10 us per launch): ASSUMPTION, not measured; the cupy backend has never run (N13).
* CPU time: component costs measured here with the operations `estimate_resources` times
  (`--calibrate`, 4 threads, complex64, load average 0.36 at 20:57 UTC): FFT 2.786e-10 s per
  (pixel log2 pixel), element-wise pass 1.803e-9 s per pixel, complex exponential 4.463e-8 s per
  element, GEMM 362 GFLOP/s (medians; FFT and element-wise from grids >= 1e6 pixels). The CPU times
  quoted include the x1.5 factor of `run_study.py` (the estimator under-read M2's measured smoke run
  by that factor). On the 17 study points the replica x1.5 is within 0.75 to 1.41 of the CPU numbers
  M2 printed (measured under a different load).
* The CPU replica is also checked as a formula: composing the engine's own measured components
  (estimate_resources with calibrate_cpu=True on a production-layout [100] cell of 1 080 450 atoms,
  2000 x 420, 4126 slices) gives exactly the engine's 286.293 s (check
  `cpu_formula_replica_equals_engine`); at that moment (load 0.48) the engine's components were
  1.23 (FFT), 0.51 (element-wise) and 1.01 (potential slice) times my calibration, total 286 s against
  the calibrated replica's 294 s (these timing lines change from run to run with the load).
* Measured engine runs here took 1.67 to 3.07 times the replica (1-min loads 4.74 to 6.92 on the
  4 shared cores); divided by max(1, load/4) this is 1.26 to 1.89. The x1.5 factor lies inside that
  range; the replica is a lower bound of every measured run (check
  `cpu_replica_is_lower_bound_of_measured_runs`).
* The layout formulas of the tool reproduce a built production-layout cell exactly (1 080 450 atoms,
  4126 slices, 4116 non-empty, largest slice 265 atoms, extent_x 259.358 A), and that cell passes all
  ten of the engine's own geometry assertions in `reflection_setup` (checks
  `layout_formulas_vs_built_100_cell`, `engine_reflection_setup_passes_layout`).
* Memory: the engine's accounting is per concurrent realisation and counts 48 B per atom for the
  positions; the host side is larger (N9: about 120 B/atom persistent, 192 B/atom (static) or
  240 B/atom (frozen phonons) while realising, from reading the code, not measured).

## 9. Scenarios (script section 13; every cell passes the replicated engine assertions)

All at [100] (B20), (0,0,8) at 16.1347 mrad, dx = dy <= 0.13 A (FFT-friendly grids), dz = a/4,
complex64, 100 V sin^2 absorbers (bulk 15 A, top 10 A), sheet beam 2 A above the highest surface
with 2 A edges and H = L_z tan(theta) - 2 A - step height - 1 A.

1. Reference: the 17 points of `scripts/hpc/null_test_study/study.yaml` ([110], TEST_ONLY), built
   here with the M2 case code: 83-405 A x 7.7-245.8 A x 1377-21 377 A, 19 224 to 2 971 136 atoms,
   1434 to 22 266 slices, at most 0.340 GB of engine arrays; 119 min CPU (x1.5) or 114 s GPU
   (model) for all points together. They run at the weakly reflecting [110] condition with a
   21 A clean depth (sections 2.4, 3), so they test the engine, not the production convergence.
2. Production single steps.
   * 2a, edges parallel to the beam (periodic up-down staircase, y period 2W). a/4 steps at 0.1 deg
     miscut, r = 0.1: 259.4 x 1564.1 x 5602.0 A, 31 116 960 atoms, 2000 x 12096, 4126 slices,
     4.096 GB (device part 2.602 GB), 13 min GPU and 17.2 h CPU per realisation. The measuring
     window is 653.7 A wide (218 resolution elements). Variants: 0.5 deg miscut (W = 157.5 A, only
     29.1 A of window beyond the lateral buffers); r = 0.05 (z 8100 A, 51.0 M atoms); a/2 steps at
     0.1 deg (W = 1558.7 A, y 3117 A, 62.6 M atoms, 9.6 GB); the narrowest converged terrace
     W_min = 141.2 A (5.6 M atoms, 0.63 GB, 48 s GPU); no absorption (z 11 104 A, 70.0 M atoms).
   * 2b, one step transverse to the beam (y = 16 a = 86.9 A): a/2 up-step 360.7 x 86.9 x 8746.5 A,
     2.71 M atoms, 2800 x 672, 6442 slices, 0.278 GB, 22 s GPU per realisation; a/4 almost the same.
     The terraces along the beam must be >= 8 resolution elements (2975 A; 2976 A in whole periods)
     each; a vicinal surface gives that only for a miscut <= 0.0262 deg (a/4 steps) or 0.0523 deg
     (a/2 steps). Steeper vicinal surfaces put several steps into one resolution element along the
     beam.
3. Half-torus R = 1000 A, r = 20 A (B33/B34), one cell size for ridge and trench (depth + 20.37 A,
   vacuum + 19.01 A, strips 1262 A on both sides of the 2040 A ring): r = 0.1: 422.4 x 2183.2 x
   9419.9 A, 93 496 543 atoms, 3360 x 16800, 6938 slices, 10.852 GB (device part 6.365 GB),
   82 min GPU and 3.8 d CPU per realisation; r = 0.05: 512.4 x 2275.5 x 11 923.5 A, 136 189 483
   atoms, 14.361 GB, 2.4 h GPU. At most 595 extra atoms per slice (8765 A^2 largest ring
   cross-section in one slice). The builders cannot produce 10^8 atoms in memory (N9). T2 found
   the ring's height not measurable at this condition, so this run shows contrast, not heights.
4. Patterned CFG-B feature: BLOCKED on PROJECT_INPUT item 13 (docs/05 gives no lateral size). With
   docs/05's illustrative 10 nm height, the two strips alone are 2 x 6197 A = 12 395 A along the beam,
   the lower bound on z is 17 249 A plus the feature length, and x grows by >= 100 A.
5. V, validation: flat strip 259.0 x 10.9 x 5602.0 A, 214 032 atoms, 2000 x 84, 19 angles of the
   rocking curve: 24 min CPU or 22 s GPU in total.

Where the time goes: for every wide cell (y >= 1500 A) the potential construction (the exact
structure-factor product, N10) takes 78-87 % of the GPU model time and 86-93 % of the CPU time. The
FFTs dominate only for the narrow cells. The vacuum is set by the engine's item-2 rule (H + L_z
tan(theta)); max(gap + H, L_z tan(theta)) + edge would suffice (92 instead of 178 A for 2a,
154 instead of 322 A for the torus; DERIVED_HERE, diffraction spread not included). Relaxing that
rule would shrink extent_x, and nx with it, by 33 to 39 % in these cells.

## 10. What a physically realistic run needs that the engine lacks or that is unsourced (code checked)

Each line was checked in the code at HEAD 44c5a4a (file and line where it matters).

| # | Need | State in the code | Consequence for the runs sized here |
|---|---|---|---|
| N1 | A sourced absorptive (imaginary) potential for Si at 200 keV (PROJECT_INPUT item 21) | only `PhysicalAbsorption(model="proportional")` (potentials.py:101-122); no named parameterisation; B30 sets 0 in the demos | The run-in length depends on it more than on anything else: 2500 A (r = 0.1), 5000 A (r = 0.05), 8000 A without absorption in the engine (tested only to 11 251 A; the two-beam tail needs 2.3 um), section 2.4; every production number here is for the TEST_ONLY r = 0.05 and 0.1 stand-ins |
| N2 | Thermal displacement of Si (Debye-Waller) from a source | `FrozenPhonons` (independent Gaussian, Einstein model, seeded per realisation) is implemented (potentials.py:125-141, 256-259); the value 0.076 A is ASSUMPTION A7 | Frozen-phonon counts in section 6 rest on that value; if a TDS-derived absorptive potential is adopted for N1, its TDS part must not be added on top of explicit frozen phonons (double counting) |
| N3 | Partial coherence: convergence (item 3, blocking), source size, energy spread | pipeline refuses a non-zero convergence (pipeline/config.py:673-680); `SheetBeam` is uniform in y and tilted only in the x-z plane (illumination.py:28-58), so an azimuthal (y) tilt cannot be launched; no ensemble generator | A convergence ensemble multiplies every production cost by the number of incidence directions; directions out of the incidence plane need a y-tilted sheet beam (not implemented). Energy spread is negligible (docs/03 section 4) |
| N4 | Si(001) 2x1 reconstruction | `termination="dimer_2x1"` raises NotImplementedError (si001.py:414-425): no geometry source read | bulk termination (B3) in every cell; B4 at [100] holds only for bulk-terminated terraces |
| N5 | Oxide / amorphous overlayer of an ion-milled surface (item 12) | region declared only, no atoms (si001.py:430-457); the pipeline refuses an overlayer (pipeline/config.py:681-688); an O-containing cell would also stop at `AtomicPotential.mean_inner_potential_V`, which raises NotImplementedError for any species other than Si (potentials.py:228-234), called by `reflection_setup` (engine.py:145) | x-extent and atom counts for 10-30 A overlayers are given as scenarios (section 3); an overlayer run needs a sourced amorphous structure, a multi-species mean inner potential and the pipeline gate lifted |
| N6 | Vicinal (monotonic) staircase | a net height change across the period is refused (si001.py:175-196) | only up-down staircases (a/4 up, a/4 down) can be periodic in y; that is what scenario 2a uses |
| N7 | Validation rungs | engine status UNVALIDATED: rung 2 (Bragg-case two-beam phase sweep), abTEM cross-check and the flat-surface rocking curve against a dynamical solver NOT RUN (engine.py:43-47); no `forward/dynamical/` module exists | rung 2 can now be built from sections 2.1 and 2.3: a continuum crystal whose potential is V0 + 2 V_008 cos(2 pi 8 x/a) must reproduce X(eta) (amplitude AND phase across the Darwin plateau) and the transient g(s); this needs a sinusoidal continuum potential class (the existing `ContinuumTerracePotential` is constant) |
| N8 | Band assertion that covers the working reflection | `check_band` asserts only the beam angles (grid.py:135-166): dx <= 0.4526 A passes, but the (0,0,8) coupling needs dx <= 0.2263 A (section 5) | add an assertion f_max >= |g| of the working reflection (and of the strongest couplings); 0.13 A satisfies it |
| N9 | Memory-lean structure input for 10^7 to 10^8 atoms | the builders keep every atom with its assertions (M2: ~56 kB/atom for the si001 builder on its cells; T1: 2.4 kB/atom for the feature builder); the engine keeps every atom in host memory (about 120 B/atom persistent, 192-240 B/atom while realising, code reading) | tiling one verified period (as `tests/forward/null_test_cases.py` does) is exact only for edges parallel to the beam; the transverse-step and torus cells need a slice-streaming lattice generator or a large-memory node for the build |
| N10 | Potential construction that scales for wide cells | exact structure factors by a (nx x n_slice) @ (n_slice x ny) product per slice (potentials.py:289-309): cost 8 nx ny n per slice; identical static slices are not cached (only empty slices are, `slice_key`) | for the wide cells (y >= 1500 A) the potential construction dominates the time (section 9); caching the four distinct slices of a static flat crystal at [100], or an O(n_px log n_px) construction, would remove most of it (not done here) |
| N11 | Operating point at the reflectivity maximum | the angle is the two-beam internal Bragg condition with the IAM mean inner potential (B32) | at [110] this angle gives a specular amplitude of only 0.043 (r = 0.1, section 2.4) and at exact [100] the condition is four-beam; a rocking curve per azimuth must locate the working point before production (section 7) |
| N12 | Spatially resolved null test | the study measures the specular component summed over all x at the exit plane (`specular_component`, tests/forward/null_test_cases.py:140-149), which mixes every surface position | use the surface-position-resolved read-out of section 2.4 (exit-plane height mapped to the surface point) for the convergence criteria |
| N13 | GPU backend | cupy path implemented, never executed (M2 section 9); GPU times are the engine's ASSUMPTION model | first GPU job must reproduce a CPU number (README_HPC) |
| N14 | Sourced mean inner potential (item 20) | the engine uses the IAM value 13.903 V (B32), no bonding | sets the angle and the refraction of every run; not a size driver |

## 11. Script output (verbatim)

Command, from the repository root (about 25 s; builds the 17 study cells and one production-layout
check cell; reads the two JSON files written by the `--calibrate` and `--measure` modes):

    venv/bin/python tools/hpc/supercell_sizing.py            # report mode: exit status 0, 41/41 checks
    venv/bin/python tools/hpc/supercell_sizing.py --calibrate tools/hpc/supercell_sizing_cpu_calibration.json
    venv/bin/python tools/hpc/supercell_sizing.py --measure tools/hpc/supercell_sizing_measurements.json
    venv/bin/python tools/hpc/supercell_sizing.py --measure gpu.json --only bu_100_r010 --backend cupy   # GPU sanity run

File hashes (SHA-256) at the final run: `supercell_sizing.py` bf59a0fd...324e8e78,
`supercell_sizing_cpu_calibration.json` af847fc4...37fa6da, `supercell_sizing_measurements.json`
e852de94...341d90a.

```

====================================================================================================
0. Run record
====================================================================================================
git {'commit': '7ab62104b4f656839f2052800cb5903f0ea2864d', 'dirty': True}; loadavg [0.28, 1.26, 3.65]; numpy 2.4.6; nproc 4
calibration file /home/user/Holography/tools/hpc/supercell_sizing_cpu_calibration.json (sha256 af847fc425e5d9b3)
measurement file /home/user/Holography/tools/hpc/supercell_sizing_measurements.json (sha256 e852de940e8e070e)

====================================================================================================
1. Beam, potential, (0,0,8) geometry
====================================================================================================
200 keV (PROJECT_INPUT item 1): lambda = 0.02507934 A, k = 250.5323 rad/A, sigma = 7.288401e-04 rad/(V A) (DERIVED_HERE, engine physics.py)
  CHECK PASS lambda: 0.02507934 vs 0.02507934 A (conventions)
  CHECK PASS k: 250.5323 vs 250.5323 rad/A (conventions)
  CHECK PASS sigma: 7.288401e-04 vs 7.28840e-4 (M2 section 4)
mean inner potential of the engine's potential (Kirkland IAM, 8 F(0)/a^3): V0 = 13.902843 V (REPRODUCED: D3 F16 13.902842 V)
  CHECK PASS MIP: 13.902843 V vs D3 13.902842 V
(0,0,8) with V0 = MIP: theta_ext = 16.1347 mrad, theta_int = 18.4719 mrad (B32); G_008 = 2 pi 8/a = 9.25546 rad/A; K sin(theta_int) = 4.62773 rad/A
  CHECK PASS theta_T1: 16.1347/18.4719 mrad vs T1 16.1347/18.4719
  CHECK PASS bragg_internal: 2 K sin(theta_int)/G - 1 = -3.95e-10 (engine dispersion vs exact SM04 refraction)
foreshortening 1/sin(theta_ext) = 61.98; one image resolution element (6.0 A, T2) = 371.8 A of surface along the beam at this angle (T2: 364.2 A at the B19 angle 16.4743 mrad)
  CHECK PASS T2_res_element: 364.17 A vs T2 364 A
shadow / blocked-view strip of an a/4 step: h/tan(theta_ext) = 84.1 A
shadow / blocked-view strip of an a/2 step: h/tan(theta_ext) = 168.3 A

====================================================================================================
2. Fourier coefficients of the engine's potential (Kirkland via abTEM, exact S_hkl)
====================================================================================================
  CHECK PASS forbidden_(0, 0, 2): |S(0, 0, 2)| = 4.9e-16
  CHECK PASS forbidden_(0, 0, 6): |S(0, 0, 6)| = 1.5e-15
  CHECK PASS forbidden_(0, 0, 10): |S(0, 0, 10)| = 9.6e-15
  CHECK PASS S_008: S(0,0,8) = 8
  V(0, 0, 0)    |g| = 0.0000 1/A  |V| = 13.9028 V  arg +0.0000  sigma|V| = 1.0133e-02 rad/A  DW(u=0.076 A) = 1.0000
  V(0, 0, 4)    |g| = 0.7365 1/A  |V| = 2.7401 V  arg -0.0000  sigma|V| = 1.9971e-03 rad/A  DW(u=0.076 A) = 0.9400
  V(0, 0, 8)    |g| = 1.4731 1/A  |V| = 1.0357 V  arg -0.0000  sigma|V| = 7.5489e-04 rad/A  DW(u=0.076 A) = 0.7808
  V(0, 0, 12)   |g| = 2.2096 1/A  |V| = 0.5467 V  arg -0.0000  sigma|V| = 3.9846e-04 rad/A  DW(u=0.076 A) = 0.5731
  V(0, 0, 16)   |g| = 2.9461 1/A  |V| = 0.3265 V  arg -0.0000  sigma|V| = 2.3798e-04 rad/A  DW(u=0.076 A) = 0.3717
  V(0, 0, 20)   |g| = 3.6826 1/A  |V| = 0.2136 V  arg -0.0000  sigma|V| = 1.5571e-04 rad/A  DW(u=0.076 A) = 0.2131
  V(0, 4, 4)    |g| = 1.0416 1/A  |V| = 1.6773 V  arg -0.0000  sigma|V| = 1.2225e-03 rad/A  DW(u=0.076 A) = 0.8836
  V(0, 2, 2)    |g| = 0.5208 1/A  |V| = 4.4526 V  arg -0.0000  sigma|V| = 3.2452e-03 rad/A  DW(u=0.076 A) = 0.9695
  V(0, 2, 6)    |g| = 1.1646 1/A  |V| = 1.4385 V  arg -0.0000  sigma|V| = 1.0485e-03 rad/A  DW(u=0.076 A) = 0.8567
  V(0, 4, 0)    |g| = 0.7365 1/A  |V| = 2.7401 V  arg -0.0000  sigma|V| = 1.9971e-03 rad/A  DW(u=0.076 A) = 0.9400
  V(0, 4, 8)    |g| = 1.6469 1/A  |V| = 0.8782 V  arg -0.0000  sigma|V| = 6.4004e-04 rad/A  DW(u=0.076 A) = 0.7340
  V(1, -1, 1)   |g| = 0.3189 1/A  |V| = 5.5151 V  arg +0.7854  sigma|V| = 4.0197e-03 rad/A  DW(u=0.076 A) = 0.9885
  V(1, -1, 3)   |g| = 0.6107 1/A  |V| = 2.5288 V  arg -0.7854  sigma|V| = 1.8431e-03 rad/A  DW(u=0.076 A) = 0.9584
  V(1, -1, 5)   |g| = 0.9568 1/A  |V| = 1.3350 V  arg +0.7854  sigma|V| = 9.7300e-04 rad/A  DW(u=0.076 A) = 0.9009
  V(1, -1, 7)   |g| = 1.3150 1/A  |V| = 0.8602 V  arg -0.7854  sigma|V| = 6.2698e-04 rad/A  DW(u=0.076 A) = 0.8211
  V(2, -2, 0)   |g| = 0.5208 1/A  |V| = 4.4526 V  arg +0.0000  sigma|V| = 3.2452e-03 rad/A  DW(u=0.076 A) = 0.9695
  V(2, -2, 4)   |g| = 0.9021 1/A  |V| = 2.0514 V  arg -0.0000  sigma|V| = 1.4951e-03 rad/A  DW(u=0.076 A) = 0.9114
  V(2, -2, 8)   |g| = 1.5624 1/A  |V| = 0.9503 V  arg -0.0000  sigma|V| = 6.9258e-04 rad/A  DW(u=0.076 A) = 0.7571
V(0,0,8) = 1.0357 V; with u = 0.076 A per axis (ASSUMPTION A7) the thermally averaged coefficient is 0.8087 V (factor 0.7808, intensity 0.6097)
  CHECK PASS V008_vs_M2: engine V(0,0,8) = 1.0357 V exceeds the M2 estimate 0.84 V by 23 %

====================================================================================================
3. Two-beam Bragg case (DERIVED_HERE; premises P1-P5 in the report)
====================================================================================================
u_g = 2 k sigma V_g = 0.37825 rad^2/A^2; b = u_g/G = 0.04087 rad/A
penetration (amplitude 1/e depth at the stop-band centre, no absorption) Lambda = 1/b = 24.47 A
extinction distance xi_g = pi/(sigma V_g) = 4161.7 A; along-surface build-up scale L_b = 1/(b tan theta_int) = 1324.5 A (= xi_g/pi x 0.99987)
M2 section 10.2 used V_g ~ 0.84 V: 1/(sigma 0.84 V) = 1633 A ('~1600 A'); with the engine's own coefficient the two-beam scale is 1325 A (-19 %)
  CHECK PASS Lb_identity: L_b sigma V_g - 1 = -1.30e-04 (k/K and cos(theta) factors)
  CHECK PASS two_beam_exact_root: exact |Im q| = 0.040867 vs b = 0.040868
Darwin (total-reflection) full width, two-beam: 0.3263 mrad internal, 0.3736 mrad external (Delta = 8.0892e-05)
  r = 0.00: eta0 = -5.363e-06+0.000e+00j rad/A, c = 4.0868e-02+0.0000e+00j, |X| = 1.0000, arg X = +1.5707 rad, depth 1/|Im q| = 24.47 A
  r = 0.05: eta0 = 7.592e-05+2.743e-02j rad/A, c = 4.0868e-02+2.0434e-03j, |X| = 0.5339, arg X = +1.6002 rad, depth 1/|Im q| = 20.32 A
  r = 0.10: eta0 = 3.197e-04+5.485e-02j rad/A, c = 4.0868e-02+4.0868e-03j, |X| = 0.3334, arg X = +1.6553 rad, depth 1/|Im q| = 14.64 A
  CHECK PASS two_beam_total_reflection: |X| = 1.000000 at the centre without absorption

====================================================================================================
4. Many-beam bookkeeping at the (0,0,8) condition (transverse reciprocal plane, g_z = 0)
====================================================================================================
[100] 161 beams with a coupling; exactly on the Ewald sphere: [(0, -4, 4), (0, 4, 4)]
   EXACT (0, -4, 4): k_x(beam) = +1.83e-09 rad/A (surface-parallel inside), in-plane angle 18.47 mrad, |V_h| = 1.6773 V, |V_g-h| = 1.6773 V (sigma|V| 1.222e-03 vs sigma V_008 7.549e-04 rad/A)
   EXACT (0, 4, 4): k_x(beam) = +1.83e-09 rad/A (surface-parallel inside), in-plane angle 18.47 mrad, |V_h| = 1.6773 V, |V_g-h| = 1.6773 V (sigma|V| 1.222e-03 vs sigma V_008 7.549e-04 rad/A)
   (0, -2, 6)     zeta = +2.1370e-02 rad/A  admixture 0.201  k_x = +2.314 rad/A  angle_y =  9.24 mrad  Bethe off-diag +0.2185 V
   (0, 2, 6)      zeta = +2.1370e-02 rad/A  admixture 0.201  k_x = +2.314 rad/A  angle_y =  9.24 mrad  Bethe off-diag +0.2185 V
   (0, -2, 2)     zeta = +2.1370e-02 rad/A  admixture 0.201  k_x = -2.314 rad/A  angle_y =  9.24 mrad  Bethe off-diag +0.2185 V
   (0, 2, 2)      zeta = +2.1370e-02 rad/A  admixture 0.201  k_x = -2.314 rad/A  angle_y =  9.24 mrad  Bethe off-diag +0.2185 V
   (0, 0, 4)      zeta = +4.2739e-02 rad/A  admixture 0.093  k_x = +0.000 rad/A  angle_y =  0.00 mrad  Bethe off-diag +0.1280 V
   (0, -4, 0)     zeta = -4.2739e-02 rad/A  admixture 0.062  k_x = -4.628 rad/A  angle_y = 18.47 mrad  Bethe off-diag -0.0410 V
   (0, 4, 0)      zeta = -4.2739e-02 rad/A  admixture 0.062  k_x = -4.628 rad/A  angle_y = 18.47 mrad  Bethe off-diag -0.0410 V
   (0, -4, 8)     zeta = -4.2739e-02 rad/A  admixture 0.062  k_x = +4.628 rad/A  angle_y = 18.47 mrad  Bethe off-diag -0.0410 V
   sum of perturbative Bethe terms (exact beams excluded): V_eff = V_g - +0.5287 V -> |V_eff|/V_g = 0.490; centre shift +2.5424e-02 rad/A = +0.62 half-widths b
   dx = 0.13 A (2/3 band 2.564 1/A): Bethe correction carried +0.55764 of +0.52871 V (missing 2.79e-02 V_g)
   dx = 0.1 A (2/3 band 3.333 1/A): Bethe correction carried +0.53335 of +0.52871 V (missing 4.48e-03 V_g)
   largest in-plane angle of an exactly or strongly (admixture >= 0.05) excited beam: alpha_y = 18.47 mrad
[110] 455 beams with a coupling; exactly on the Ewald sphere: []
   (-1, 1, 7)     zeta = +1.3356e-02 rad/A  admixture 0.348  k_x = +3.471 rad/A  angle_y =  6.53 mrad  Bethe off-diag +0.2589 V
   (1, -1, 7)     zeta = +1.3356e-02 rad/A  admixture 0.348  k_x = +3.471 rad/A  angle_y =  6.53 mrad  Bethe off-diag +0.2589 V
   (-1, 1, 1)     zeta = +1.3356e-02 rad/A  admixture 0.348  k_x = -3.471 rad/A  angle_y =  6.53 mrad  Bethe off-diag +0.2589 V
   (1, -1, 1)     zeta = +1.3356e-02 rad/A  admixture 0.348  k_x = -3.471 rad/A  angle_y =  6.53 mrad  Bethe off-diag +0.2589 V
   (-3, 3, 3)     zeta = -8.0136e-03 rad/A  admixture 0.209  k_x = -1.157 rad/A  angle_y = 19.59 mrad  Bethe off-diag -0.1175 V
   (3, -3, 3)     zeta = -8.0136e-03 rad/A  admixture 0.209  k_x = -1.157 rad/A  angle_y = 19.59 mrad  Bethe off-diag -0.1175 V
   (-3, 3, 5)     zeta = -8.0136e-03 rad/A  admixture 0.209  k_x = +1.157 rad/A  angle_y = 19.59 mrad  Bethe off-diag -0.1175 V
   (3, -3, 5)     zeta = -8.0136e-03 rad/A  admixture 0.209  k_x = +1.157 rad/A  angle_y = 19.59 mrad  Bethe off-diag -0.1175 V
   sum of perturbative Bethe terms (exact beams excluded): V_eff = V_g - -0.0970 V -> |V_eff|/V_g = 1.094; centre shift +6.0430e-04 rad/A = +0.01 half-widths b
   dx = 0.13 A (2/3 band 2.564 1/A): Bethe correction carried -0.06573 of -0.09701 V (missing 3.02e-02 V_g)
   dx = 0.1 A (2/3 band 3.333 1/A): Bethe correction carried -0.08847 of -0.09701 V (missing 8.24e-03 V_g)
   largest in-plane angle of an exactly or strongly (admixture >= 0.05) excited beam: alpha_y = 19.59 mrad
  CHECK PASS four_beam_100: exactly excited at [100]: [(0, -4, 4), (0, 4, 4)]
  CHECK PASS no_exact_110: exactly excited at [110]: []

====================================================================================================
5. Absorption lengths of the TEST_ONLY proportional stand-ins (PROJECT_INPUT item 21)
====================================================================================================
  r = 0.05: V' = r V: mean imaginary potential 0.695 V; amplitude 1/e length along the path 1/(sigma r V0) = 1974 A (intensity 987 A); slow (anomalous) two-beam transient 1/(sigma r (V0 - V_g)) = 2133 A; depth 1/e of a refracted non-Bragg wave sin(theta_int)/(sigma r V0) = 36.5 A
  r = 0.10: V' = r V: mean imaginary potential 1.390 V; amplitude 1/e length along the path 1/(sigma r V0) = 987 A (intensity 493 A); slow (anomalous) two-beam transient 1/(sigma r (V0 - V_g)) = 1066 A; depth 1/e of a refracted non-Bragg wave sin(theta_int)/(sigma r V0) = 18.2 A

====================================================================================================
6. Two-beam leading-edge transient (Green's function along the surface, DERIVED_HERE)
====================================================================================================
  CHECK PASS green_closed_vs_numeric_r0.0: max |g_num - g_closed| = 1.54e-04 of |c|/2; max |X(p)| = 1.000000
  CHECK PASS green_causal_r0.0: |g_num(s < 0)| = 2.12e-04 of |c|/2
  CHECK PASS green_closed_vs_numeric_r0.1: max |g_num - g_closed| = 5.85e-05 of |c|/2; max |X(p)| = 0.333631
  CHECK PASS green_causal_r0.1: |g_num(s < 0)| = 4.79e-05 of |c|/2
Relative error E of the reflected field at distance L downstream of a sharp illumination edge (two-beam, V_g = V(0,0,8)):
  r = 0.00: |E| at L (A) = 1000: 6.3e-01  2000: 3.1e-01  3000: 8.0e-02  5000: 9.2e-02  10000: 3.5e-02  20000: 1.4e-03  50000: 2.5e-03
          envelope below 1e-2 / 3e-3 / 1e-3 beyond L = 22572 / 51572 / 113552 A
  CHECK PASS tail_asymptote_T20: max |E| over one period at b s = 20.0: 8.438e-03 vs sqrt(2/pi) T^-1.5 = 8.921e-03
  CHECK PASS tail_asymptote_T50: max |E| over one period at b s = 50.0: 2.185e-03 vs sqrt(2/pi) T^-1.5 = 2.257e-03
  r = 0.05: |E| at L (A) = 1000: 4.6e-01  2000: 1.7e-01  3000: 4.5e-02  5000: 7.9e-03  10000: 3.6e-04  20000: 5.1e-06  50000: 5.5e-06
          envelope below 1e-2 / 3e-3 / 1e-3 beyond L = 3721 / 6712 / 7538 A
  r = 0.10: |E| at L (A) = 1000: 3.0e-01  2000: 7.4e-02  3000: 1.4e-02  5000: 6.7e-04  10000: 1.5e-05  20000: 1.8e-05  50000: 1.8e-05
          envelope below 1e-2 / 3e-3 / 1e-3 beyond L = 3194 / 3762 / 4290 A

====================================================================================================
7. Engine measurements on flat strips (MEASURED_HERE, UNVALIDATED engine, TEST_ONLY inputs)
====================================================================================================
measurement file: created 2026-09-23T20:57:46Z, git {'commit': '44c5a4a24e5a41f8e1f602deaabd922f9c1633a2', 'dirty': True}, loadavg start [0.3, 2.3, 1.89] end [6.8, 7.23, 6.73]
read-out resolution: pass band 0.1 1/A -> 1/(2 x 0.1) = 5 A in x = 310 A of surface; free-space diffraction between surface and exit plane sqrt(lambda D)/tan = 310 A (D = 1000 A) to 760 A (D = 6000 A); bins 500 A
  CHECK PASS measurements_present: runs present: ['bu_100_r000', 'bu_100_r005', 'bu_100_r010', 'bu_110_r010', 'fp_100_r010']; required: ['bu_100_r010', 'bu_100_r005', 'bu_110_r010', 'bu_100_r000', 'fp_100_r010']
[bu_100_r010] azimuth [100], r = 0.1, crystal 6129 A long (6000 A after first contact), y 10.86 A, clean depth 100.0 A; 382840 atoms, grid 2500x84, 4514 slices; run 144 s (loadavg after [4.74, 3.45, 2.39])
         0-   500 A: |R| 0.0483  arg -1.1286  |R|/|R_pl| - 1 = -0.8216  phase - phase_pl = +0.4107
       500-  1000 A: |R| 0.1151  arg -1.4452  |R|/|R_pl| - 1 = -0.5747  phase - phase_pl = +0.0942
      1000-  1500 A: |R| 0.1845  arg -1.5259  |R|/|R_pl| - 1 = -0.3185  phase - phase_pl = +0.0135
      1500-  2000 A: |R| 0.2304  arg -1.5296  |R|/|R_pl| - 1 = -0.1488  phase - phase_pl = +0.0097
      2000-  2500 A: |R| 0.2562  arg -1.5318  |R|/|R_pl| - 1 = -0.0535  phase - phase_pl = +0.0075
      2500-  3000 A: |R| 0.2676  arg -1.5363  |R|/|R_pl| - 1 = -0.0115  phase - phase_pl = +0.0031
      3000-  3500 A: |R| 0.2712  arg -1.5402  |R|/|R_pl| - 1 = +0.0020  phase - phase_pl = -0.0009
      3500-  4000 A: |R| 0.2720  arg -1.5418  |R|/|R_pl| - 1 = +0.0047  phase - phase_pl = -0.0025
      4000-  4500 A: |R| 0.2720  arg -1.5410  |R|/|R_pl| - 1 = +0.0050  phase - phase_pl = -0.0017
      4500-  5000 A: |R| 0.2714  arg -1.5401  |R|/|R_pl| - 1 = +0.0027  phase - phase_pl = -0.0008
      5000-  5500 A: |R| 0.2740  arg -1.5393  |R|/|R_pl| - 1 = +0.0121  phase - phase_pl = +0.0000
      5500-  6000 A: |R| 0.2624  arg -1.5758  |R|/|R_pl| - 1 = -0.0307  phase - phase_pl = -0.0365
    plateau 2755-5255 A: |R| 0.2707 (|R|^2 = 0.073, not reflected 0.927), arg -1.5394; largest bin deviation inside the plateau: phase 0.0025 rad, amplitude 0.0050
    converged (every later bin up to the plateau end within the tolerance) beyond: phase 1e-2 rad 1500 A, 3e-3 rad 3000 A; amplitude 1e-2 3000 A, 3e-2 2500 A
    exit-plane intensity versus depth below the top layer (A: I): 0: 1.7e-01, 10: 2.1e-01, 20: 1.9e-02, 30: 3.9e-03, 40: 2.1e-04, 50: 1.2e-04, 60: 2.2e-05, 70: 1.3e-06, 80: 1.4e-06, 90: 3.1e-06, 100: 5.3e-07
    deepest point with I > 1e-2 / 1e-4 / 1e-6: 26.0 / 53.2 / 94.2 A
[bu_100_r005] azimuth [100], r = 0.05, crystal 9127 A long (9000 A after first contact), y 10.86 A, clean depth 100.0 A; 570520 atoms, grid 3240x84, 6722 slices; run 282 s (loadavg after [5.36, 4.6, 3.17])
         0-   500 A: |R| 0.0630  arg +1.6768  |R|/|R_pl| - 1 = -0.8620  phase - phase_pl = +0.4705
       500-  1000 A: |R| 0.1508  arg +1.3067  |R|/|R_pl| - 1 = -0.6696  phase - phase_pl = +0.1004
      1000-  1500 A: |R| 0.2555  arg +1.1986  |R|/|R_pl| - 1 = -0.4403  phase - phase_pl = -0.0077
      1500-  2000 A: |R| 0.3486  arg +1.1947  |R|/|R_pl| - 1 = -0.2363  phase - phase_pl = -0.0117
      2000-  2500 A: |R| 0.4149  arg +1.1895  |R|/|R_pl| - 1 = -0.0912  phase - phase_pl = -0.0169
      2500-  3000 A: |R| 0.4519  arg +1.1839  |R|/|R_pl| - 1 = -0.0101  phase - phase_pl = -0.0225
      3000-  3500 A: |R| 0.4657  arg +1.1797  |R|/|R_pl| - 1 = +0.0200  phase - phase_pl = -0.0266
      3500-  4000 A: |R| 0.4661  arg +1.1796  |R|/|R_pl| - 1 = +0.0209  phase - phase_pl = -0.0268
      4000-  4500 A: |R| 0.4617  arg +1.1841  |R|/|R_pl| - 1 = +0.0113  phase - phase_pl = -0.0223
      4500-  5000 A: |R| 0.4573  arg +1.1914  |R|/|R_pl| - 1 = +0.0017  phase - phase_pl = -0.0150
      5000-  5500 A: |R| 0.4543  arg +1.1989  |R|/|R_pl| - 1 = -0.0050  phase - phase_pl = -0.0075
      5500-  6000 A: |R| 0.4529  arg +1.2044  |R|/|R_pl| - 1 = -0.0080  phase - phase_pl = -0.0019
      6000-  6500 A: |R| 0.4534  arg +1.2070  |R|/|R_pl| - 1 = -0.0068  phase - phase_pl = +0.0007
      6500-  7000 A: |R| 0.4562  arg +1.2068  |R|/|R_pl| - 1 = -0.0007  phase - phase_pl = +0.0004
      7000-  7500 A: |R| 0.4601  arg +1.2052  |R|/|R_pl| - 1 = +0.0079  phase - phase_pl = -0.0012
      7500-  8000 A: |R| 0.4608  arg +1.2052  |R|/|R_pl| - 1 = +0.0093  phase - phase_pl = -0.0011
      8000-  8500 A: |R| 0.4671  arg +1.1994  |R|/|R_pl| - 1 = +0.0231  phase - phase_pl = -0.0070
      8500-  9000 A: |R| 0.4479  arg +1.1617  |R|/|R_pl| - 1 = -0.0189  phase - phase_pl = -0.0447
    plateau 5753-8253 A: |R| 0.4565 (|R|^2 = 0.208, not reflected 0.792), arg +1.2064; largest bin deviation inside the plateau: phase 0.0012 rad, amplitude 0.0093
    converged (every later bin up to the plateau end within the tolerance) beyond: phase 1e-2 rad 5000 A, 3e-3 rad 5500 A; amplitude 1e-2 4500 A, 3e-2 2500 A
    exit-plane intensity versus depth below the top layer (A: I): 0: 4.3e-01, 10: 3.6e-01, 20: 5.9e-02, 30: 1.4e-02, 40: 6.9e-04, 50: 3.9e-04, 60: 1.1e-04, 70: 4.2e-05, 80: 2.6e-05, 90: 4.4e-06, 100: 3.8e-06
    deepest point with I > 1e-2 / 1e-4 / 1e-6: 30.2 / 60.6 / 103.0 A
[bu_110_r010] azimuth [110], r = 0.1, crystal 6127 A long (6000 A after first contact), y 7.68 A, clean depth 100.0 A; 270810 atoms, grid 2500x60, 6382 slices; run 164 s (loadavg after [5.8, 5.2, 3.64])
         0-   500 A: |R| 0.0334  arg +0.0727  |R|/|R_pl| - 1 = -0.2264  phase - phase_pl = -2.1681
       500-  1000 A: |R| 0.0744  arg +1.1752  |R|/|R_pl| - 1 = +0.7232  phase - phase_pl = -1.0656
      1000-  1500 A: |R| 0.0664  arg +1.7588  |R|/|R_pl| - 1 = +0.5379  phase - phase_pl = -0.4820
      1500-  2000 A: |R| 0.0442  arg +2.1292  |R|/|R_pl| - 1 = +0.0224  phase - phase_pl = -0.1116
      2000-  2500 A: |R| 0.0420  arg +2.0385  |R|/|R_pl| - 1 = -0.0277  phase - phase_pl = -0.2023
      2500-  3000 A: |R| 0.0403  arg +2.1828  |R|/|R_pl| - 1 = -0.0667  phase - phase_pl = -0.0580
      3000-  3500 A: |R| 0.0423  arg +2.2052  |R|/|R_pl| - 1 = -0.0213  phase - phase_pl = -0.0356
      3500-  4000 A: |R| 0.0431  arg +2.2543  |R|/|R_pl| - 1 = -0.0025  phase - phase_pl = +0.0135
      4000-  4500 A: |R| 0.0439  arg +2.2652  |R|/|R_pl| - 1 = +0.0162  phase - phase_pl = +0.0244
      4500-  5000 A: |R| 0.0436  arg +2.2754  |R|/|R_pl| - 1 = +0.0087  phase - phase_pl = +0.0346
      5000-  5500 A: |R| 0.0423  arg +2.1834  |R|/|R_pl| - 1 = -0.0194  phase - phase_pl = -0.0574
      5500-  6000 A: |R| 0.0309  arg +2.6022  |R|/|R_pl| - 1 = -0.2840  phase - phase_pl = +0.3614
    plateau 2753-5253 A: |R| 0.0432 (|R|^2 = 0.002, not reflected 0.998), arg +2.2408; largest bin deviation inside the plateau: phase 0.0356 rad, amplitude 0.0213
    converged (every later bin up to the plateau end within the tolerance) beyond: phase 1e-2 rad 5000 A, 3e-3 rad 5000 A; amplitude 1e-2 4500 A, 3e-2 3000 A
    exit-plane intensity versus depth below the top layer (A: I): 0: 1.9e-01, 10: 1.5e-01, 20: 4.2e-02, 30: 8.8e-03, 40: 1.4e-03, 50: 4.8e-04, 60: 1.4e-04, 70: 3.9e-05, 80: 1.1e-05, 90: 7.0e-06, 100: 2.3e-07
    deepest point with I > 1e-2 / 1e-4 / 1e-6: 30.8 / 64.2 / 96.9 A
[bu_100_r000] azimuth [100], r = 0.0, crystal 12124 A long (12000 A after first contact), y 10.86 A, clean depth 100.0 A; 758200 atoms, grid 3969x84, 8930 slices; run 699 s (loadavg after [6.92, 6.93, 5.54])
         0-   500 A: |R| 0.0835  arg -1.7867  |R|/|R_pl| - 1 = -0.9062  phase - phase_pl = +0.5211
       500-  1000 A: |R| 0.1998  arg -2.2063  |R|/|R_pl| - 1 = -0.7757  phase - phase_pl = +0.1014
      1000-  1500 A: |R| 0.3646  arg -2.3316  |R|/|R_pl| - 1 = -0.5906  phase - phase_pl = -0.0239
      1500-  2000 A: |R| 0.5535  arg -2.3542  |R|/|R_pl| - 1 = -0.3786  phase - phase_pl = -0.0465
      2000-  2500 A: |R| 0.7167  arg -2.3651  |R|/|R_pl| - 1 = -0.1953  phase - phase_pl = -0.0574
      2500-  3000 A: |R| 0.8324  arg -2.3718  |R|/|R_pl| - 1 = -0.0655  phase - phase_pl = -0.0641
      3000-  3500 A: |R| 0.8890  arg -2.3746  |R|/|R_pl| - 1 = -0.0019  phase - phase_pl = -0.0669
      3500-  4000 A: |R| 0.8918  arg -2.3693  |R|/|R_pl| - 1 = +0.0012  phase - phase_pl = -0.0616
      4000-  4500 A: |R| 0.8607  arg -2.3502  |R|/|R_pl| - 1 = -0.0337  phase - phase_pl = -0.0425
      4500-  5000 A: |R| 0.8205  arg -2.3158  |R|/|R_pl| - 1 = -0.0788  phase - phase_pl = -0.0080
      5000-  5500 A: |R| 0.7941  arg -2.2732  |R|/|R_pl| - 1 = -0.1084  phase - phase_pl = +0.0345
      5500-  6000 A: |R| 0.7924  arg -2.2374  |R|/|R_pl| - 1 = -0.1104  phase - phase_pl = +0.0704
      6000-  6500 A: |R| 0.8134  arg -2.2218  |R|/|R_pl| - 1 = -0.0868  phase - phase_pl = +0.0859
      6500-  7000 A: |R| 0.8481  arg -2.2291  |R|/|R_pl| - 1 = -0.0479  phase - phase_pl = +0.0786
      7000-  7500 A: |R| 0.8835  arg -2.2514  |R|/|R_pl| - 1 = -0.0081  phase - phase_pl = +0.0563
      7500-  8000 A: |R| 0.9083  arg -2.2775  |R|/|R_pl| - 1 = +0.0197  phase - phase_pl = +0.0302
      8000-  8500 A: |R| 0.9166  arg -2.2982  |R|/|R_pl| - 1 = +0.0290  phase - phase_pl = +0.0095
      8500-  9000 A: |R| 0.9108  arg -2.3094  |R|/|R_pl| - 1 = +0.0225  phase - phase_pl = -0.0017
      9000-  9500 A: |R| 0.8994  arg -2.3115  |R|/|R_pl| - 1 = +0.0097  phase - phase_pl = -0.0038
      9500- 10000 A: |R| 0.8906  arg -2.3084  |R|/|R_pl| - 1 = -0.0002  phase - phase_pl = -0.0007
     10000- 10500 A: |R| 0.8875  arg -2.3060  |R|/|R_pl| - 1 = -0.0036  phase - phase_pl = +0.0017
     10500- 11000 A: |R| 0.8878  arg -2.3050  |R|/|R_pl| - 1 = -0.0033  phase - phase_pl = +0.0027
     11000- 11500 A: |R| 0.8998  arg -2.3172  |R|/|R_pl| - 1 = +0.0102  phase - phase_pl = -0.0095
     11500- 12000 A: |R| 0.8534  arg -2.3546  |R|/|R_pl| - 1 = -0.0420  phase - phase_pl = -0.0469
    plateau 8751-11251 A: |R| 0.8907 (|R|^2 = 0.793, not reflected 0.207), arg -2.3077; largest bin deviation inside the plateau: phase 0.0038 rad, amplitude 0.0097
    converged (every later bin up to the plateau end within the tolerance) beyond: phase 1e-2 rad 8000 A, 3e-3 rad 9500 A; amplitude 1e-2 9000 A, 3e-2 7000 A
    exit-plane intensity versus depth below the top layer (A: I): 0: 8.9e-01, 10: 8.6e-01, 20: 8.8e-02, 30: 7.4e-02, 40: 9.1e-02, 50: 6.3e-02, 60: 4.3e-02, 70: 3.1e-02, 80: 1.9e-02, 90: 9.9e-03, 100: 7.5e-03
    deepest point with I > 1e-2 / 1e-4 / 1e-6: 99.7 / 104.6 / 107.0 A
[fp_100_r010] region: surface distance 1500-2252 A after contact, >= 5 A above the surface: 95 x-rows x 126 y-columns = 11970 pixels
[fp_100_r010] 8 frozen-phonon realisations, u = 0.076 A per axis (ASSUMPTION A7 (not sourced)), seed 20260923, aperture 3.0 mrad = 0.1196 1/A (B22): variance/coherent intensity rho^2 = 9.3749e-04 (rho = 0.0306); arg(mean) - arg(static) = -0.0457 rad; |mean|/|static| = 0.7213; 98 s per realisation
         0-   500 A: rho^2 5.709e-03, |mean|/|static| 0.6964
       500-  1000 A: rho^2 2.372e-03, |mean|/|static| 0.6930
      1000-  1500 A: rho^2 1.159e-03, |mean|/|static| 0.6985
      1500-  2000 A: rho^2 1.033e-03, |mean|/|static| 0.7170
      2000-  2500 A: rho^2 8.033e-04, |mean|/|static| 0.7314
      2500-  3000 A: rho^2 6.173e-04, |mean|/|static| 0.7410
r = 0.10 [100]: two-beam run-in for 1e-2 rad 3194 A; engine phase converged within 1e-2 rad beyond 1500 A (plateau drift 0.002 rad); engine plateau |R| 0.271 vs two-beam |X| 0.333
r = 0.05 [100]: two-beam run-in for 1e-2 rad 3721 A; engine phase converged within 1e-2 rad beyond 5000 A (plateau drift 0.001 rad); engine plateau |R| 0.457 vs two-beam |X| 0.534
r = 0.00 [100]: two-beam run-in for 1e-2 rad 22572 A; engine phase converged within 1e-2 rad beyond 8000 A (plateau drift 0.004 rad); engine plateau |R| 0.891 vs two-beam |X| 1.000

====================================================================================================
8. Sizing rules (DERIVED_HERE from sections 3-7 and the labelled stand-ins)
====================================================================================================
image resolution element 6.0 A = 371.8 A of surface along the beam; B29 margin 3 elements = 1115.5 A upstream of every measured region; exit margin L_exit = 1115.5 A
r = 0.10: run-in L_run = 2500 A (engine measurement: phase within 1e-2 rad AND amplitude within 3e-2 of the plateau, tested to 5255 A; two-beam phase estimate 3194 A); clean depth D_clean = 55 A (exit-plane intensity below 1e-4 (amplitude 1e-2), measured); exit bins beyond the plateau worse than 1e-2 rad: [(5500.0, -0.036)]
r = 0.05: run-in L_run = 5000 A (engine measurement: phase within 1e-2 rad AND amplitude within 3e-2 of the plateau, tested to 8253 A; two-beam phase estimate 3721 A); clean depth D_clean = 65 A (exit-plane intensity below 1e-4 (amplitude 1e-2), measured); exit bins beyond the plateau worse than 1e-2 rad: [(8500.0, -0.045)]
r = 0.00: run-in L_run = 8000 A (engine measurement: phase within 1e-2 rad AND amplitude within 3e-2 of the plateau, tested to 11251 A; two-beam phase estimate 22572 A); clean depth D_clean = 65 A (floor of transmitted waves (I > 1e-4 down to 105 A, the absorber); evanescent part as for r = 0.05); exit bins beyond the plateau worse than 1e-2 rad: [(11500.0, -0.047)]
lateral spread angle at [100]: alpha_y = 18.47 mrad (section 4)
r = 0.10: lateral buffer from a step edge parallel to the beam dlat = L_run tan(alpha_y) + 3 x 6.0 A = 64.2 A; minimum terrace width W_min = 2 dlat + 2 x 6.0 A = 140.4 A
r = 0.05: lateral buffer from a step edge parallel to the beam dlat = L_run tan(alpha_y) + 3 x 6.0 A = 110.4 A; minimum terrace width W_min = 2 dlat + 2 x 6.0 A = 232.7 A
r = 0.00: lateral buffer from a step edge parallel to the beam dlat = L_run tan(alpha_y) + 3 x 6.0 A = 165.8 A; minimum terrace width W_min = 2 dlat + 2 x 6.0 A = 343.6 A
terrace widths from the miscut (ASSUMPTION scenarios for PROJECT_INPUT item 11): W = h/tan(miscut)
  miscut 0.05 deg = 0.873 mrad: single-layer (a/4) W =  1555.8 A; double-layer (a/2) W =  3111.7 A
  miscut 0.10 deg = 1.745 mrad: single-layer (a/4) W =   777.9 A; double-layer (a/2) W =  1555.8 A
  miscut 0.25 deg = 4.363 mrad: single-layer (a/4) W =   311.2 A; double-layer (a/2) W =   622.3 A
  miscut 0.50 deg = 8.727 mrad: single-layer (a/4) W =   155.6 A; double-layer (a/2) W =   311.2 A
overlayer scenarios (PROJECT_INPUT item 12; ASSUMPTION thicknesses; 0 = B26):
  t =  0.0 A: adds 0.0 A to x; glancing path through it 2 t/sin(theta_ext) =       0 A (in and out)
  t = 10.0 A: adds 10.0 A to x; glancing path through it 2 t/sin(theta_ext) =    1240 A (in and out)
  t = 20.0 A: adds 20.0 A to x; glancing path through it 2 t/sin(theta_ext) =    2479 A (in and out)
  t = 30.0 A: adds 30.0 A to x; glancing path through it 2 t/sin(theta_ext) =    3719 A (in and out)
half-torus ridge (R = 1000 A, r = 20 A): layer-quantised extreme +19.008 A; strip h/tan(theta_ext) = 1178 A
half-torus trench (R = 1000 A, r = 20 A): layer-quantised extreme -20.366 A; strip h/tan(theta_ext) = 1262 A
  CHECK PASS torus_extremes_T2: crest 19.008 A, floor -20.366 A (T2: 19.01, -20.37)
half-torus volume x density n V = 197167 atoms

====================================================================================================
9. Sampling (2/3 band limit f_max = 1/(3 dx); DERIVED_HERE)
====================================================================================================
  incident beam, external                              f = 0.6433 1/A -> dx <= 0.5181 A
  specular beam inside (internal Bragg wave)           f = 0.7365 1/A -> dx <= 0.4526 A
  (0,0,8) coupling g_008 (transmission function)       f = 1.4731 1/A -> dx <= 0.2263 A
  (0,+-4,4) coupling at [100] (exact beam)             f = 1.0416 1/A -> dx <= 0.3200 A
  (0,0,12) coupling / beam (0,0,16) f_x                f = 2.2096 1/A -> dx <= 0.1509 A
  (0,0,16) coupling                                    f = 2.9461 1/A -> dx <= 0.1131 A
  engine check_band asserts only the beam angles: dx <= 0.4526 A passes although it drops the (0,0,8) coupling (needs dx <= 0.2263 A)
  dx = dy = 0.13 A: f_max = 2.5641 1/A; F(f_max^2)/F(0) = 0.0303; Bethe correction of V(0,0,8) outside the band: [100] 2.8e-02, [110] 3.0e-02 of V_g
  dx = dy = 0.1 A: f_max = 3.3333 1/A; F(f_max^2)/F(0) = 0.0186; Bethe correction of V(0,0,8) outside the band: [100] 4.5e-03, [110] 8.2e-03 of V_g
  slice thickness: [100] dz = a/4 = 1.357725 A (one atomic plane per slice), [110] dz = p/4 = 0.960057 A (half the slices empty); both commensurate

====================================================================================================
10. Frozen phonons (u = 0.076 A per axis: ASSUMPTION A7)
====================================================================================================
measured rho^2 = 9.3749e-04: realisations for 0.01 rad per resolution element N = rho^2/(2 dphi^2) = 4.69 -> 5; the static-lattice phase differs from the ensemble-mean phase by -0.0457 rad (a systematic, not noise)

====================================================================================================
11. Rocking angles
====================================================================================================
validation rocking curve (flat strip): range +-1.5 two-beam Darwin widths (+-0.560 mrad) at steps of 1/6 width (0.0623 mrad): 19 angles (ASSUMPTION design)
B16 for the half-torus (h_max = 20.37 A, sigma_phi = 0.028 rad per hologram, docs/03 example): largest tilt step 0.2963 mrad; 4 equally spaced angles (0.889 mrad) give sigma_h <= 0.1 A (slope standard error 0.084 A)
atomic steps (a/4, a/2): branch from the lattice constraint (B29): 1 angle

====================================================================================================
12. Cost model: replica of engine.estimate_resources, checked against the engine
====================================================================================================
CPU calibration 2026-09-23T20:57:36Z (loadavg [0.36, 2.38, 1.91], 4 threads, complex64): c_fft = 2.786e-10 s/(px log2 px), element-wise 1.803e-09 s/px, exp 4.463e-08 s/element, GEMM 362 GFLOP/s (medians; FFT and element-wise from grids >= 1e6 px)
GPU model: engine.GPU_ASSUMED = ASSUMPTION (not measured: no GPU on the build machine): a data-centre GPU with ~1 TB/s effective memory bandwidth, cuFFT at 1/3 of that for 2D complex64 FFTs, ~10 TFLOP/s effective complex64 GEMM and ~10 us per kernel launch
  tfix_bragg_abs0_L0         grid 640x60, 1434 slices, 19224 atoms, 3.8 MB, GPU 0.31 s (engine 0.31), CPU x1.5 6 s (M2 printed 8 s); replica==engine True, ==M2 True
  tfix_bragg_abs0_L10k       grid 1875x60, 11850 slices, 159840 atoms, 16.2 MB, GPU 3.66 s (engine 3.66), CPU x1.5 158 s (M2 printed 173 s); replica==engine True, ==M2 True
  tfix_bragg_abs0_L20k       grid 3125x60, 22266 slices, 300456 atoms, 28.6 MB, GPU 9.48 s (engine 9.48), CPU x1.5 504 s (M2 printed 606 s); replica==engine True, ==M2 True
  tfix_bragg_abs05_L0        grid 640x60, 1434 slices, 19224 atoms, 3.8 MB, GPU 0.31 s (engine 0.31), CPU x1.5 6 s (M2 printed 7 s); replica==engine True, ==M2 True
  tfix_bragg_abs05_L5k       grid 1260x60, 6642 slices, 89532 atoms, 10.0 MB, GPU 1.68 s (engine 1.68), CPU x1.5 59 s (M2 printed 58 s); replica==engine True, ==M2 True
  tfix_bragg_abs05_L10k      grid 1875x60, 11850 slices, 159840 atoms, 16.2 MB, GPU 3.66 s (engine 3.66), CPU x1.5 158 s (M2 printed 178 s); replica==engine True, ==M2 True
  tfix_bragg_abs10_L5k       grid 1260x60, 6642 slices, 89532 atoms, 10.0 MB, GPU 1.68 s (engine 1.68), CPU x1.5 59 s (M2 printed 53 s); replica==engine True, ==M2 True
  tfix_bragg_abs10_L10k      grid 1875x60, 11850 slices, 159840 atoms, 16.2 MB, GPU 3.66 s (engine 3.66), CPU x1.5 158 s (M2 printed 150 s); replica==engine True, ==M2 True
  tfix_off12_abs10_L5k       grid 1120x60, 7010 slices, 94500 atoms, 9.6 MB, GPU 1.68 s (engine 1.68), CPU x1.5 55 s (M2 printed 52 s); replica==engine True, ==M2 True
  tfix_off20_abs10_L5k       grid 1440x60, 6406 slices, 86346 atoms, 10.7 MB, GPU 1.72 s (engine 1.72), CPU x1.5 65 s (M2 printed 67 s); replica==engine True, ==M2 True
  tmov_bragg_abs10_L10k      grid 1875x60, 11850 slices, 159840 atoms, 16.2 MB, GPU 3.66 s (engine 3.66), CPU x1.5 158 s (M2 printed 210 s); replica==engine True, ==M2 True
  step_w8_bragg_abs10_L5k    grid 1260x480, 6642 slices, 742784 atoms, 82.4 MB, GPU 4.27 s (engine 4.27), CPU x1.5 290 s (M2 printed 216 s); replica==engine True, ==M2 True
  step_w16_bragg_abs10_L5k   grid 1260x960, 6642 slices, 1485568 atoms, 166.6 MB, GPU 9.60 s (engine 9.60), CPU x1.5 670 s (M2 printed 517 s); replica==engine True, ==M2 True
  step_w32_bragg_abs10_L5k   grid 1260x1920, 6642 slices, 2971136 atoms, 340.4 MB, GPU 22.75 s (engine 22.75), CPU x1.5 1672 s (M2 printed 1319 s); replica==engine True, ==M2 True
  step_w16_bragg_abs0_L5k    grid 1260x960, 6642 slices, 1485568 atoms, 166.6 MB, GPU 9.60 s (engine 9.60), CPU x1.5 670 s (M2 printed 479 s); replica==engine True, ==M2 True
  step_w16_off20_abs10_L5k   grid 1440x960, 6406 slices, 1432704 atoms, 177.2 MB, GPU 10.65 s (engine 10.65), CPU x1.5 727 s (M2 printed 531 s); replica==engine True, ==M2 True
  step_w16_bragg_abs10_L10k  grid 1875x960, 11850 slices, 2652160 atoms, 267.4 MB, GPU 26.01 s (engine 26.01), CPU x1.5 1713 s (M2 printed 1213 s); replica==engine True, ==M2 True
  CHECK PASS replica_equals_engine_and_M2_on_17_study_points: memory bytes and GPU seconds identical to estimate_resources; grid, slices, atoms, MB and GPU s identical to the M2 printout
  replica CPU (x1.5) / M2 printed CPU on the 17 points: 0.75 to 1.41
  study.yaml total: CPU (x1.5) 119 min on 4 cores, GPU (ASSUMPTION model) 114 s; largest engine arrays 340 MB
  CHECK PASS layout_formulas_vs_built_100_cell: built: 1080450 atoms, 4126 slices (4116 non-empty), n_max 265, extent_x 259.358 A; formulas: 1080450, 4126 (4116), 265, 259.358 A
  CHECK PASS engine_reflection_setup_passes_layout: engine geometry checks ['item1_no_vacuum_below', 'item1_bulk_absorber_inside_crystal', 'item1_top_absorber', 'item2_vacuum_margin', 'item3_launched_upstream', 'item3_beam_in_vacuum_band_at_launch', 'item3_no_end_face_illumination', 'item3_footprint', 'item4_buildup_length', 'item4_depth_above_absorber'] all passed; replicated rules {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
  CHECK PASS cpu_formula_replica_equals_engine: the replica's composition of the engine's own measured components gives 286.293 s = estimate_resources 286.293 s
  observation (grid 2000x420, 4126 slices, loadavg now [0.48, 1.24, 3.59]): engine-measured / calibrated component: FFT 1.23, element-wise 0.51, potential slice 1.01; total 286 s vs calibrated replica 294 s (both without x1.5)
  measured run bu_100_r010: 144 s per realisation vs replica 86 s (ratio measured/replica 1.67; 1-min load after the run 4.74; ratio divided by max(1, load/4) = 1.41); x1.5 replica 129 s
  measured run bu_100_r005: 282 s per realisation vs replica 167 s (ratio measured/replica 1.69; 1-min load after the run 5.36; ratio divided by max(1, load/4) = 1.26); x1.5 replica 250 s
  measured run bu_110_r010: 164 s per realisation vs replica 60 s (ratio measured/replica 2.74; 1-min load after the run 5.80; ratio divided by max(1, load/4) = 1.89); x1.5 replica 90 s
  measured run bu_100_r000: 699 s per realisation vs replica 272 s (ratio measured/replica 2.57; 1-min load after the run 6.92; ratio divided by max(1, load/4) = 1.48); x1.5 replica 409 s
  measured run fp_100_r010: 98 s per realisation vs replica 32 s (ratio measured/replica 3.07; 1-min load after the run 6.80; ratio divided by max(1, load/4) = 1.81); x1.5 replica 48 s
  CHECK PASS cpu_replica_is_lower_bound_of_measured_runs: measured/replica 1.67 to 3.07: the replica counts only FFT, element-wise and potential-slice operations and was calibrated at load 0.36, so no measured run may be faster (tolerance 0.9)
  observation: measured/replica 1.67 to 3.07 under 1-min loads of 4.74 to 6.92 on 4 cores; divided by max(1, load/4): 1.26 to 1.89. The x1.5 factor of run_study.py (used in every CPU time below) lies inside that range
host memory per atom (code reading, DERIVED_HERE, not measured): persistent 120 B (structure 48, cell 32, realised potential 40); peak while realising 192 B (static) / 240 B (frozen phonons); the engine's own accounting (estimate_resources) counts 48 B per atom
structure builders (reports M2, T1): si001 builder ~4.7 GB per 84 000 atoms = 56 kB/atom (M2 10.5); feature builder 1.33 GB for 547 662 atoms = 2.4 kB/atom (T1 section 4); tiling one verified z period is exact only for a crystal periodic along the beam (edges parallel)

====================================================================================================
13. Scenarios ([100] azimuth B20, (0,0,8) at the MIP angle, complex64, dx = dy <= 0.13 A)
====================================================================================================
  CHECK PASS engine_rules_2a_a4_miscut0.1_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2a_a4_miscut0.1_r0.10] a/4 steps parallel to the beam, miscut 0.1 deg (ASSUMPTION), r = 0.10 TEST_ONLY; W = 782.0 A vs W_min 140.4 A; measuring window 653.7 A x 744 A = 218 resolution elements
    extents x 259.4 A (depth below the lowest top layer 70.0, vacuum 178, sheet beam H 86.0), y 1564.1 A (288 periods), z 5602.0 A (1029 periods; contact 124 + run-in 2500 + field 1859 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 178 A; physical need max(gap + H, L_z tan(theta)) + edge = 92 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 174 A instead of 259 A (-33 %)
    atoms 31,116,960; grid 2000 x 12096 (dx 0.1297, dy 0.1293 A); slices 4126 (non-empty 4116, atoms per slice max 7632, mean 7560)
    engine arrays 4.096 GB per realisation (device part 2.602 GB, atom positions 1.494 GB); exit wave 0.194 GB
    per realisation: CPU 17.2 h (4 cores, replica x1.5; FFT+element-wise 13 %, potential construction 87 %), GPU 13 min (ASSUMPTION model; potential construction 78 %); x 8 realisations x 1 angles = CPU 5.7 d, GPU 103 min; exit waves 1.5 GB; host memory (code reading) 7.5 GB peak with frozen phonons
  CHECK PASS engine_rules_2a_a4_miscut0.5_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2a_a4_miscut0.5_r0.10] a/4 steps parallel to the beam, miscut 0.5 deg (ASSUMPTION), r = 0.10 TEST_ONLY; W = 157.5 A vs W_min 140.4 A; measuring window 29.1 A x 744 A = 10 resolution elements
    extents x 259.4 A (depth below the lowest top layer 70.0, vacuum 178, sheet beam H 86.0), y 315.0 A (58 periods), z 5602.0 A (1029 periods; contact 124 + run-in 2500 + field 1859 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 178 A; physical need max(gap + H, L_z tan(theta)) + edge = 92 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 174 A instead of 259 A (-33 %)
    atoms 6,266,610; grid 2000 x 2430 (dx 0.1297, dy 0.1296 A); slices 4126 (non-empty 4116, atoms per slice max 1537, mean 1522)
    engine arrays 0.705 GB per realisation (device part 0.404 GB, atom positions 0.301 GB); exit wave 0.039 GB
    per realisation: CPU 72 min (4 cores, replica x1.5; FFT+element-wise 34 %, potential construction 66 %), GPU 56 s (ASSUMPTION model; potential construction 44 %); x 8 realisations x 1 angles = CPU 9.6 h, GPU 7 min; exit waves 0.3 GB; host memory (code reading) 1.5 GB peak with frozen phonons
  CHECK PASS engine_rules_2a_a4_miscut0.1_r0.05: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2a_a4_miscut0.1_r0.05] a/4 steps parallel to the beam, miscut 0.1 deg (ASSUMPTION), r = 0.05 TEST_ONLY; W = 782.0 A vs W_min 232.7 A; measuring window 561.3 A x 744 A = 187 resolution elements
    extents x 350.4 A (depth below the lowest top layer 80.0, vacuum 259, sheet beam H 126.3), y 1564.1 A (288 periods), z 8100.2 A (1489 periods; contact 124 + run-in 5000 + field 1859 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 259 A; physical need max(gap + H, L_z tan(theta)) + edge = 133 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 224 A instead of 350 A (-36 %)
    atoms 51,031,008; grid 2700 x 12096 (dx 0.1298, dy 0.1293 A); slices 5966 (non-empty 5956, atoms per slice max 8640, mean 8568)
    engine arrays 5.824 GB per realisation (device part 3.374 GB, atom positions 2.449 GB); exit wave 0.261 GB
    per realisation: CPU 33.6 h (4 cores, replica x1.5; FFT+element-wise 13 %, potential construction 87 %), GPU 28 min (ASSUMPTION model; potential construction 80 %); x 8 realisations x 1 angles = CPU 11.2 d, GPU 3.7 h; exit waves 2.1 GB; host memory (code reading) 12.2 GB peak with frozen phonons
  CHECK PASS engine_rules_2a_a2_miscut0.1_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2a_a2_miscut0.1_r0.10] a/2 steps parallel to the beam, miscut 0.1 deg (ASSUMPTION), r = 0.10 TEST_ONLY; W = 1558.7 A vs W_min 140.4 A; measuring window 1430.3 A x 744 A = 477 resolution elements
    extents x 259.7 A (depth below the lowest top layer 70.0, vacuum 177, sheet beam H 84.7), y 3117.3 A (574 periods), z 5602.0 A (1029 periods; contact 124 + run-in 2500 + field 1859 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 177 A; physical need max(gap + H, L_z tan(theta)) + edge = 92 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 175 A instead of 260 A (-33 %)
    atoms 62,608,476; grid 2000 x 24000 (dx 0.1299, dy 0.1299 A); slices 4126 (non-empty 4116, atoms per slice max 15211, mean 15211)
    engine arrays 9.625 GB per realisation (device part 6.620 GB, atom positions 3.005 GB); exit wave 0.384 GB
    per realisation: CPU 2.6 d (4 cores, replica x1.5; FFT+element-wise 7 %, potential construction 93 %), GPU 46 min (ASSUMPTION model; potential construction 87 %); x 8 realisations x 1 angles = CPU 20.8 d, GPU 6.1 h; exit waves 3.1 GB; host memory (code reading) 15.0 GB peak with frozen phonons
  CHECK PASS engine_rules_2a_a4_Wmin_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2a_a4_Wmin_r0.10] a/4 steps parallel to the beam, narrowest converged terrace W_min, r = 0.10 TEST_ONLY; W = 141.2 A vs W_min 140.4 A; measuring window 12.8 A x 744 A = 4 resolution elements
    extents x 259.4 A (depth below the lowest top layer 70.0, vacuum 178, sheet beam H 86.0), y 282.4 A (52 periods), z 5602.0 A (1029 periods; contact 124 + run-in 2500 + field 1859 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 178 A; physical need max(gap + H, L_z tan(theta)) + edge = 92 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 174 A instead of 259 A (-33 %)
    atoms 5,618,340; grid 2000 x 2187 (dx 0.1297, dy 0.1291 A); slices 4126 (non-empty 4116, atoms per slice max 1378, mean 1365)
    engine arrays 0.631 GB per realisation (device part 0.361 GB, atom positions 0.270 GB); exit wave 0.035 GB
    per realisation: CPU 62 min (4 cores, replica x1.5; FFT+element-wise 36 %, potential construction 64 %), GPU 48 s (ASSUMPTION model; potential construction 41 %); x 8 realisations x 1 angles = CPU 8.2 h, GPU 6 min; exit waves 0.3 GB; host memory (code reading) 1.3 GB peak with frozen phonons
  CHECK PASS engine_rules_2a_a4_miscut0.1_r0.00: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2a_a4_miscut0.1_r0.00] a/4 steps parallel to the beam, miscut 0.1 deg, NO absorption (B30 ASSUMPTION); run-in 8000 A from the engine measurement (two-beam tail 22572 A); W = 782.0 A vs W_min 343.6 A; measuring window 450.5 A x 744 A = 150 resolution elements
    extents x 446.4 A (depth below the lowest top layer 80.0, vacuum 355, sheet beam H 174.8), y 1564.1 A (288 periods), z 11103.5 A (2042 periods; contact 124 + run-in 8000 + field 1859 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 355 A; physical need max(gap + H, L_z tan(theta)) + edge = 181 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 273 A instead of 446 A (-39 %)
    atoms 69,983,424; grid 3456 x 12096 (dx 0.1292, dy 0.1293 A); slices 8178 (non-empty 8168, atoms per slice max 8640, mean 8568)
    engine arrays 7.444 GB per realisation (device part 4.085 GB, atom positions 3.359 GB); exit wave 0.334 GB
    per realisation: CPU 2.3 d (4 cores, replica x1.5; FFT+element-wise 14 %, potential construction 86 %), GPU 49 min (ASSUMPTION model; potential construction 80 %); x 8 realisations x 1 angles = CPU 18.2 d, GPU 6.5 h; exit waves 2.7 GB; host memory (code reading) 16.8 GB peak with frozen phonons
steps transverse to the beam: each terrace >= 8 resolution elements = 2975 A along the beam; a vicinal surface gives that only for miscut <= 0.0262 deg (a/4 steps) or 0.0523 deg (a/2 steps)
  CHECK PASS engine_rules_2b_a2_transverse_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2b_a2_transverse_r0.10] one a/2 up-step transverse to the beam, terraces 5757 A and 2976 A along the beam (>= 8 resolution elements each), y = 16 a, r = 0.10 TEST_ONLY; strip 168 A; 29 resolution elements per measuring region
    extents x 360.7 A (depth below the lowest top layer 70.0, vacuum 278, sheet beam H 135.4), y 86.9 A (16 periods), z 8746.5 A (1608 periods; contact 124 + run-in 2500 + field 5002 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 278 A; physical need max(gap + H, L_z tan(theta)) + edge = 143 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 226 A instead of 361 A (-37 %)
    atoms 2,710,784; grid 2800 x 672 (dx 0.1288, dy 0.1293 A); slices 6442 (non-empty 6432, atoms per slice max 432, mean 421)
    engine arrays 0.278 GB per realisation (device part 0.147 GB, atom positions 0.130 GB); exit wave 0.015 GB
    per realisation: CPU 28 min (4 cores, replica x1.5; FFT+element-wise 52 %, potential construction 48 %), GPU 22 s (ASSUMPTION model; potential construction 18 %); x 8 realisations x 1 angles = CPU 3.7 h, GPU 3 min; exit waves 0.1 GB; host memory (code reading) 0.7 GB peak with frozen phonons
  CHECK PASS engine_rules_2b_a4_transverse_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[2b_a4_transverse_r0.10] one a/4 up-step transverse to the beam, terraces 5670 A and 2976 A along the beam (>= 8 resolution elements each), y = 16 a, r = 0.10 TEST_ONLY; strip 84 A; 29 resolution elements per measuring region
    extents x 358.4 A (depth below the lowest top layer 70.0, vacuum 277, sheet beam H 135.4), y 86.9 A (16 periods), z 8659.6 A (1592 periods; contact 124 + run-in 2500 + field 4918 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 277 A; physical need max(gap + H, L_z tan(theta)) + edge = 142 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 223 A instead of 358 A (-38 %)
    atoms 2,666,624; grid 2800 x 672 (dx 0.1280, dy 0.1293 A); slices 6378 (non-empty 6368, atoms per slice max 432, mean 419)
    engine arrays 0.275 GB per realisation (device part 0.147 GB, atom positions 0.128 GB); exit wave 0.015 GB
    per realisation: CPU 27 min (4 cores, replica x1.5; FFT+element-wise 52 %, potential construction 48 %), GPU 22 s (ASSUMPTION model; potential construction 18 %); x 8 realisations x 1 angles = CPU 3.6 h, GPU 3 min; exit waves 0.1 GB; host memory (code reading) 0.6 GB peak with frozen phonons
half-torus: largest cross-section in one slice 8765 A^2 -> at most 595 extra atoms per slice (ridge)
  CHECK PASS engine_rules_3_torus_R1000_r20_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[3_torus_R1000_r20_r0.10] half-torus ridge or trench (B33/B34), one cell size for both (depth + 20.37 A, vacuum + 19.01 A), r = 0.10 TEST_ONLY; y gap between periodic images 143.2 A; strips 1262 A; phase MAP -> N = max(8, 5) realisations per resolution element; a B16 rocking series would multiply by 4 angles but T2 shows the ring is not resolved
    extents x 422.4 A (depth below the lowest top layer 90.4, vacuum 322, sheet beam H 149.0), y 2183.2 A (402 periods), z 9419.9 A (1732 periods; contact 124 + run-in 2500 + field 5680 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 322 A; physical need max(gap + H, L_z tan(theta)) + edge = 154 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 273 A instead of 422 A (-35 %)
    atoms 93,496,543; grid 3360 x 16800 (dx 0.1257, dy 0.1300 A); slices 6938 (non-empty 6928, atoms per slice max 14263, mean 13495)
    engine arrays 10.852 GB per realisation (device part 6.365 GB, atom positions 4.488 GB); exit wave 0.452 GB
    per realisation: CPU 3.8 d (4 cores, replica x1.5; FFT+element-wise 10 %, potential construction 90 %), GPU 82 min (ASSUMPTION model; potential construction 86 %); x 8 realisations x 1 angles = CPU 30.8 d, GPU 10.9 h; exit waves 3.6 GB; host memory (code reading) 22.4 GB peak with frozen phonons
  CHECK PASS engine_rules_3_torus_R1000_r20_r0.05: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[3_torus_R1000_r20_r0.05] half-torus ridge or trench (B33/B34), one cell size for both (depth + 20.37 A, vacuum + 19.01 A), r = 0.05 TEST_ONLY; y gap between periodic images 235.5 A; strips 1262 A; phase MAP -> N = max(8, 5) realisations per resolution element; a B16 rocking series would multiply by 4 angles but T2 shows the ring is not resolved
    extents x 512.4 A (depth below the lowest top layer 100.4, vacuum 402, sheet beam H 189.4), y 2275.5 A (419 periods), z 11923.5 A (2193 periods; contact 124 + run-in 5000 + field 5680 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 402 A; physical need max(gap + H, L_z tan(theta)) + edge = 194 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 324 A instead of 512 A (-37 %)
    atoms 136,189,483; grid 3969 x 17640 (dx 0.1291, dy 0.1290 A); slices 8782 (non-empty 8772, atoms per slice max 16098, mean 15525)
    engine arrays 14.361 GB per realisation (device part 7.824 GB, atom positions 6.537 GB); exit wave 0.560 GB
    per realisation: CPU 6.5 d (4 cores, replica x1.5; FFT+element-wise 9 %, potential construction 91 %), GPU 2.4 h (ASSUMPTION model; potential construction 87 %); x 8 realisations x 1 angles = CPU 52.1 d, GPU 19.4 h; exit waves 4.5 GB; host memory (code reading) 32.7 GB peak with frozen phonons
  CHECK PASS engine_rules_V_rocking_flat_strip_r0.10: {'item2_vacuum_margin': np.True_, 'item3_beam_in_band': np.True_, 'item3_no_end_face': np.True_, 'item3_footprint': np.True_, 'item4_buildup': np.True_, 'item4_depth': True, 'fov_lit': np.True_}
[V_rocking_flat_strip_r0.10] flat strip for the rocking-curve benchmark (docs/05 4.4) and the run-in check, static lattice, 19 angles
    extents x 259.0 A (depth below the lowest top layer 70.0, vacuum 179, sheet beam H 87.4), y 10.9 A (2 periods), z 5602.0 A (1029 periods; contact 124 + run-in 2500 + field 1859 + exit 1116)
    vacuum: engine rule (item 2) H + L_z tan(theta) -> 179 A; physical need max(gap + H, L_z tan(theta)) + edge = 92 A (DERIVED_HERE: incident sheet at the entrance, reflected sheet at the exit plane; diffraction spread not included); extent_x would be 172 A instead of 259 A (-33 %)
    atoms 214,032; grid 2000 x 84 (dx 0.1295, dy 0.1293 A); slices 4126 (non-empty 4116, atoms per slice max 52, mean 52)
    engine arrays 0.023 GB per realisation (device part 0.013 GB, atom positions 0.010 GB); exit wave 0.001 GB
    per realisation: CPU 75 s (4 cores, replica x1.5; FFT+element-wise 59 %, potential construction 41 %), GPU 1 s (ASSUMPTION model; potential construction 4 %); x 1 realisations x 19 angles = CPU 24 min, GPU 22 s; exit waves 0.0 GB; host memory (code reading) 0.1 GB peak with frozen phonons
[4_patterned] BLOCKED on PROJECT_INPUT item 13 (docs/05 gives no lateral size). With docs/05's illustrative 10 nm height the two strips alone are 2 x 6197 A = 12395 A along the beam and the cell needs >= 100 A more vacuum or depth; lower bound on z: 17249 A plus the feature length

====================================================================================================
14. Table (paste into the report)
====================================================================================================
| scenario | extents x, y, z (A) | atoms | grid | slices | memory per realisation (GB) | CPU time per realisation (4 cores, x1.5) | GPU time per realisation (ASSUMPTION model) | realisations x angles | total CPU / GPU |
|---|---|---|---|---|---|---|---|---|---|
| 1 study.yaml, 17 points ([110], reference) | 83-405 x 7.7-245.8 x 1377-21377 | 19,224 to 2,971,136 | see section 8 | 1434 to 22266 | <= 0.340 | 119 min (sum) | 114 s (sum) | 1 x 1 (translation points 2 runs) | 119 min / 114 s |
| 2a_a4_miscut0.1_r0.10 | 259 x 1564 x 5602 | 31,116,960 | 2000x12096 | 4126 | 4.10 | 17.2 h | 13 min | 8 x 1 | 5.7 d / 103 min |
| 2a_a4_miscut0.5_r0.10 | 259 x 315 x 5602 | 6,266,610 | 2000x2430 | 4126 | 0.71 | 72 min | 56 s | 8 x 1 | 9.6 h / 7 min |
| 2a_a4_miscut0.1_r0.05 | 350 x 1564 x 8100 | 51,031,008 | 2700x12096 | 5966 | 5.82 | 33.6 h | 28 min | 8 x 1 | 11.2 d / 3.7 h |
| 2a_a2_miscut0.1_r0.10 | 260 x 3117 x 5602 | 62,608,476 | 2000x24000 | 4126 | 9.63 | 2.6 d | 46 min | 8 x 1 | 20.8 d / 6.1 h |
| 2a_a4_Wmin_r0.10 | 259 x 282 x 5602 | 5,618,340 | 2000x2187 | 4126 | 0.63 | 62 min | 48 s | 8 x 1 | 8.2 h / 6 min |
| 2a_a4_miscut0.1_r0.00 | 446 x 1564 x 11103 | 69,983,424 | 3456x12096 | 8178 | 7.44 | 2.3 d | 49 min | 8 x 1 | 18.2 d / 6.5 h |
| 2b_a2_transverse_r0.10 | 361 x 87 x 8746 | 2,710,784 | 2800x672 | 6442 | 0.28 | 28 min | 22 s | 8 x 1 | 3.7 h / 3 min |
| 2b_a4_transverse_r0.10 | 358 x 87 x 8660 | 2,666,624 | 2800x672 | 6378 | 0.28 | 27 min | 22 s | 8 x 1 | 3.6 h / 3 min |
| 3_torus_R1000_r20_r0.10 | 422 x 2183 x 9420 | 93,496,543 | 3360x16800 | 6938 | 10.85 | 3.8 d | 82 min | 8 x 1 | 30.8 d / 10.9 h |
| 3_torus_R1000_r20_r0.05 | 512 x 2276 x 11924 | 136,189,483 | 3969x17640 | 8782 | 14.36 | 6.5 d | 2.4 h | 8 x 1 | 52.1 d / 19.4 h |
| V_rocking_flat_strip_r0.10 | 259 x 11 x 5602 | 214,032 | 2000x84 | 4126 | 0.02 | 75 s | 1 s | 1 x 19 | 24 min / 22 s |
| 4 patterned CFG-B feature | BLOCKED on PROJECT_INPUT item 13 | | | | | | | | |

====================================================================================================
15. Self-checks
====================================================================================================
41/41 checks pass; runtime 25 s
exit status 0
```

## 12. Table and recommended run order

Memory is the engine's own accounting per concurrent realisation (`estimate_resources`, replicated
exactly). The GPU holds everything except the atom positions (the "device part" of section 9). The
host needs about 192-240 B per atom while realising (code reading), plus the structure build (N9).
CPU times are for the 4 cores of this container and include the x1.5 factor of `run_study.py`;
measured runs here took 1.26-1.89 times the replica after dividing by the load. GPU times come
from the engine's `GPU_ASSUMED` model: ASSUMPTION, never measured, and the cupy backend has never
run. Realisations and angles are independent jobs. Phonon realisations: 8 (ASSUMPTION floor; 5 would
give 1e-2 rad per resolution element with the measured rho^2). All rows use the TEST_ONLY
absorption stated in their names, because PROJECT_INPUT item 21 is missing.

| scenario | extents x, y, z (A) | atoms | grid | slices | memory per realisation (GB) | CPU time per realisation (4 cores, x1.5) | GPU time per realisation (ASSUMPTION model) | realisations x angles | total CPU / GPU |
|---|---|---|---|---|---|---|---|---|---|
| 1 study.yaml, 17 points ([110], reference) | 83-405 x 7.7-245.8 x 1377-21377 | 19,224 to 2,971,136 | see section 8 | 1434 to 22266 | <= 0.340 | 119 min (sum) | 114 s (sum) | 1 x 1 (translation points 2 runs) | 119 min / 114 s |
| 2a_a4_miscut0.1_r0.10 | 259 x 1564 x 5602 | 31,116,960 | 2000x12096 | 4126 | 4.10 | 17.2 h | 13 min | 8 x 1 | 5.7 d / 103 min |
| 2a_a4_miscut0.5_r0.10 | 259 x 315 x 5602 | 6,266,610 | 2000x2430 | 4126 | 0.71 | 72 min | 56 s | 8 x 1 | 9.6 h / 7 min |
| 2a_a4_miscut0.1_r0.05 | 350 x 1564 x 8100 | 51,031,008 | 2700x12096 | 5966 | 5.82 | 33.6 h | 28 min | 8 x 1 | 11.2 d / 3.7 h |
| 2a_a2_miscut0.1_r0.10 | 260 x 3117 x 5602 | 62,608,476 | 2000x24000 | 4126 | 9.63 | 2.6 d | 46 min | 8 x 1 | 20.8 d / 6.1 h |
| 2a_a4_Wmin_r0.10 | 259 x 282 x 5602 | 5,618,340 | 2000x2187 | 4126 | 0.63 | 62 min | 48 s | 8 x 1 | 8.2 h / 6 min |
| 2a_a4_miscut0.1_r0.00 | 446 x 1564 x 11103 | 69,983,424 | 3456x12096 | 8178 | 7.44 | 2.3 d | 49 min | 8 x 1 | 18.2 d / 6.5 h |
| 2b_a2_transverse_r0.10 | 361 x 87 x 8746 | 2,710,784 | 2800x672 | 6442 | 0.28 | 28 min | 22 s | 8 x 1 | 3.7 h / 3 min |
| 2b_a4_transverse_r0.10 | 358 x 87 x 8660 | 2,666,624 | 2800x672 | 6378 | 0.28 | 27 min | 22 s | 8 x 1 | 3.6 h / 3 min |
| 3_torus_R1000_r20_r0.10 | 422 x 2183 x 9420 | 93,496,543 | 3360x16800 | 6938 | 10.85 | 3.8 d | 82 min | 8 x 1 | 30.8 d / 10.9 h |
| 3_torus_R1000_r20_r0.05 | 512 x 2276 x 11924 | 136,189,483 | 3969x17640 | 8782 | 14.36 | 6.5 d | 2.4 h | 8 x 1 | 52.1 d / 19.4 h |
| V_rocking_flat_strip_r0.10 | 259 x 11 x 5602 | 214,032 | 2000x84 | 4126 | 0.02 | 75 s | 1 s | 1 x 19 | 24 min / 22 s |
| 4 patterned CFG-B feature | BLOCKED on PROJECT_INPUT item 13 | | | | | | | | |

Recommended run order (convergence before production; a step is passed only if its criterion holds):

0. GPU sanity (minutes): `run_study.py --only tfix_bragg_abs0_L0` on the GPU must give the CPU value
   (+0.569 rad, M2), and `supercell_sizing.py --measure gpu.json --only bu_100_r010 --backend cupy`
   must reproduce the stored plateau (|R| 0.2707, arg -1.5394) within 1e-2 rad and 1e-2.
1. Engine prerequisites (code, not size): rung 2 with a sinusoidal continuum potential against
   X(eta) and g(s) of sections 2.1 and 2.3 (amplitude and phase across the Darwin plateau, and the
   build-up); an absorber-effectiveness test (reflection of the 100 V sin^2 absorbers for the
   transmitted wave, which matters most without absorption); a band assertion for the (0,0,8)
   coupling (N8).
2. Flat-strip convergence at [100] (row V; about 1 GPU-minute each). (a) Rocking curve, 19 angles, for
   r = 0.1 and 0.05: it locates the reflectivity maximum, which differs from the two-beam angle
   (four-beam case, N11), and the same at [110]. (b) Run-in: repeat the four strips of section 2.4
   at twice the length (r = 0 to 25 000 A, to test the two-beam tail of 22 572 A). (c) dx 0.13 against
   0.10 A. (d) Clean depth 55/65 against 100 A and bulk absorber 15 against 30 A. (e) dz a/4 against
   a/8. Pass: plateau phase unchanged within 1e-2 rad.
3. The M2 study (17 points, 114 GPU-seconds in total) as it is, plus the same fixed-beam
   translation points at [100], with the clean depth of section 3 and the surface-resolved read-out
   of section 2.4 (N12).
4. Frozen phonons on the flat strip: 8, then 16 realisations. rho^2 (9.4e-4 here) and the
   mean-against-static phase (-0.046 rad here) must be stable.
5. Terrace-width study at [100]: a/4 up-down staircase, edges parallel to the beam, W = 50, 100, 150,
   200, 400 A, r = 0.1 (each well under 1 GPU-minute to a few minutes). It confirms or replaces
   W_min = 140 A (lateral buffer 64 A).
6. Production single steps: 2b (minutes of GPU), then 2a at W_min, then 2a at the miscut width once
   item 11 gives the miscut. Choose r = 0.1 or 0.05 only as a bracket until item 21 is supplied.
7. Half-torus (row 3) last: only after steps 1-6 pass and with a slice-streaming builder (N9). T2
   says it will show contrast, not heights.
8. Patterned CFG-B feature: blocked on item 13.

