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

This explains M2's observation that without absorption the null-test error "oscillates in sign up
to 6600 A": the two-beam field needs 2.3 um to settle to 1e-2 rad and 11 um to 1e-3 rad.

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
at every surface point of the strip from ONE run. Resolution: about 5 A in x, 300 A in z_s. The 0.1 1/A pass band
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
* [100], r = 0: the amplitude reaches 0.89 by 3000 A, then amplitude and phase oscillate
  (phase +-0.086 rad, period about 5000-6000 A) and settle within 1e-2 rad after 8000 A in this
  strip (tested only to 11 251 A). The two-beam tail predicts 22 572 A. Without absorption 0.207
  of the incident intensity is not reflected into the specular beam (|R|^2 = 0.793); the exit-plane
  intensity stays near 1e-2 down to the bulk absorber, which therefore carries the transmitted wave
  and must not reflect it.
* [110], r = 0.1 (the M2 study azimuth): at the two-beam Bragg angle the specular amplitude is only
  0.043 (six times weaker than at [100]) and its phase beats by +-0.036 rad over the whole strip, in
  a strongly many-beam regime (section 2.2). Where the [110] reflection maximum lies is for the
  rocking curve (run order step 2); the M2 study's convergence lengths at this angle do not transfer
  to [100].
* Exit margin: the last 500 A before the exit plane are off by 0.04-0.05 rad in every run (the
  reflected ray is then less than 8 A above the surface, where the pass band mixes it with the
  crystal). The 3-resolution-element exit margin of 1115.5 A (section 2.6) covers this.
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
  20 A (the measured amplitude 1/e depth at [100] is about 10 A); the clean depth is the physical
  requirement. The current study cells use a clean depth of 21 A (null_test_cases.py); at 20 A the
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
* Memory: the engine's accounting is per concurrent realisation and counts 48 B per atom for the
  positions; the host side is larger (N9: about 120 B/atom persistent, 192 B/atom (static) or
  240 B/atom (frozen phonons) while realising, from reading the code, not measured).

## 10. What a physically realistic run needs that the engine lacks or that is unsourced (code checked)

Each line was checked in the code at HEAD 44c5a4a (file and line where it matters).

| # | Need | State in the code | Consequence for the runs sized here |
|---|---|---|---|
| N1 | A sourced absorptive (imaginary) potential for Si at 200 keV (PROJECT_INPUT item 21) | only `PhysicalAbsorption(model="proportional")` (potentials.py:101-122); no named parameterisation; B30 sets 0 in the demos | The run-in length depends on it more than on anything else: without absorption the field needs 2.3 um (two-beam) to settle to 1e-2 rad and the engine does not settle within 12 000 A (section 2.4); every production number here is for the TEST_ONLY r = 0.05 and 0.1 stand-ins |
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
