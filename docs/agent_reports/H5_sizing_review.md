# H5: adversarial review of H2's supercell sizing

Agent H5, 2026-09-23. Reviewed: `docs/agent_reports/H2_realistic_supercell_sizing.md` (H2 report),
`tools/hpc/supercell_sizing.py` (H2 tool), `tools/hpc/supercell_sizing_cpu_calibration.json`,
`tools/hpc/supercell_sizing_measurements.json`, at HEAD 661762e. Written incrementally; the verdict table and
the list of confirmed numbers are at the end. Nothing here is committed by H5.

Method. Every number below is printed by `tools/hpc/review_h5_recompute.py` (my script; it was written
without reading H2's implementation of any quantity; it calls only the repository's engine, builders,
constants and abTEM's Kirkland table). Modes: report (default), `--rerun` (engine rerun of H2's
`bu_100_r010` strip and a frozen-phonon strip, output `tools/hpc/review_h5_rerun.json`), `--memtime`
(tracemalloc and timing probes of the engine, output `tools/hpc/review_h5_memtime.json`). H2's tool was
opened only after my own numbers existed, to locate the cause of a disagreement; where that happened it
is said.

Labels: DERIVED_HERE (formula recomputed here), REPRODUCED (engine executed here, output saved in the
JSON named), SECTION_READ (text or code read), UNVERIFIED.

Severity: BLOCKER (must not reach a summary or a cluster run as is), MAJOR (a number or claim that is
wrong, unsupported or mislabelled and that matters for the runs or for what Ali is told), MINOR (wrong
or inconsistent but without consequence for the runs), NIT.

## Log

- 21:50 UTC: read the H2 report (all), engine (engine, grid, potentials, propagator, illumination,
  backend, physics), forward/cell.py, feature_cell.py, geometry/sampling.py, null_test_cases.py,
  study.yaml, run_study.py, M2 (all), T2 (resolution, torus), T1 (memory), model_assumptions,
  physics_conventions, docs/03 section 5, docs/05 (sections 2 and 9), docs/06, L2 C14/E17, D3 F16.
- 22:05 UTC: sections 1-7 of my script (analytic numbers) run: they agree with H2 (F-list below).
- 22:15 UTC: scenario rows rebuilt from H2's stated rules: they agree with H2's table.
- 22:20 UTC: engine rerun of `bu_100_r010` started (my own cell construction and read-out).

## A. Recomputed and confirmed (analytic part)

A1. Beam and potential (DERIVED_HERE, script section 1-2). lambda = 0.02507934 A, k = 250.5323 rad/A,
sigma = 7.288401e-4 rad/(V A). Mean inner potential of the engine's Kirkland potential 13.902843 V by
two routes (abTEM `projected_scattering_factor` as the engine uses it, and the raw Kirkland table with
h^2/(2 pi m0 e) = 47.8776 V A^2; they agree to 1.5e-9). V(0,0,8) = 1.0357 V by both routes (4.4e-8).
The (0,0,8) internal Bragg condition with V0 = 13.9028 V gives theta_ext = 16.1347 mrad,
theta_int = 18.4719 mrad; with V0 = 12.0 V (B1) it gives 16.4743 mrad (the B19 angle; docs/05 and B17
round it to 16.5 mrad). CONFIRMED.

A2. M2's "~1600 A" (question 1). M2 10.2 used V_g ~ 0.84 V from an estimated Kirkland f_e ~ 0.35 A at
s = 0.74 1/A. The Kirkland table gives f_e = 0.4332 A at q = |g_008| = 1.4731 1/A (s = 0.7365 1/A);
0.84 V corresponds to f_e = 0.3513 A. So M2's number is the same two-beam formula with an f_e read 19 %
low: 1/(sigma 0.84 V) = 1633 A (M2's "~1600 A", xi_g = 5131 A, penetration 30.2 A), against
1/(sigma 1.0357 V) = 1324.7 A with the engine's static coefficient. For the static lattice that every
engine measurement here uses, 1325 A is right. A nuance H2 does not state: with the Debye-Waller factor
of u = 0.076 A (0.7808, ASSUMPTION A7) the coherent coefficient of a frozen-phonon ensemble is 0.8087 V
and the same formula gives 1697 A, close to M2's number by coincidence (see finding M3).

A3. Two-beam Bragg case (DERIVED_HERE, script section 3, my own derivation: z-evolution
`d psi/dz = (i/2k) d2psi/dx2 + i sigma V psi`, two beams, first order in eta/G). u_g = 0.37825 rad^2/A^2,
b = c = 0.040868 rad/A, Lambda = 24.47 A, xi_g = 4161.7 A, L_b = 1324.5 A (= 0.99987/(sigma V_g)),
Darwin full width 0.3263 mrad internal, 0.3736 mrad external; at the Bragg angle |X| = 1.0000 (r = 0),
0.5339 (r = 0.05), 0.3334 (r = 0.1), depth 1/|Im q| = 24.47, 20.32, 14.64 A. CONFIRMED to all digits
printed by H2, including eta0 = -5.363e-6 rad/A at r = 0.

A4. Leading-edge transient (DERIVED_HERE, script section 4). The closed form
g(s) = i J1(c s) exp(i eta0 s)/s equals my numerical transform of X(eta0 - p) to 7.7e-4 of |c|/2 and
vanishes upstream to 1.8e-4. Last distance with |E| > 1e-2 / 3e-3 / 1e-3 on a 25 A grid (50 A above
20 000 A): r = 0: 22 550 / 51 550 / 113 500 A (H2: 22 572 / 51 572 / 113 552); r = 0.05: 3700 / 6700 /
7525 A (H2: 3721 / 6712 / 7538); r = 0.1: 3175 / 3750 / 4275 A (H2: 3194 / 3762 / 4290). The pure
envelope sqrt(2/pi)(L/L_b)^-1.5 reaches 1e-2 only at 24 548 A; H2's 22 572 A is the actual last crossing,
which lies 8 % inside the envelope. CONFIRMED (to my grid).

A5. Absorption lengths (DERIVED_HERE, script section 5): mean imaginary potential 0.695 / 1.390 V;
1/(sigma r V0) = 1974 / 987 A (intensity 987 / 493 A); slow transient 1/(sigma r (V0 - V_g)) = 2133 /
1066 A; depth sin(theta_int)/(sigma r V0) = 36.5 / 18.2 A for r = 0.05 / 0.1. CONFIRMED.

A6. Four-beam claim (question 2; DERIVED_HERE, script section 6). At the exact [100] azimuth, with
kappa0 = G_008/2 inside the crystal, the (0,+-4,4) beams have zeta = 1.4e-17 rad/A (exactly on the
sphere), k_x = 0 inside (surface-parallel, evanescent in vacuum since k_x,vac^2 = -2 k sigma V0 < 0),
in-plane angle 18.47 mrad, sigma|V_044| = 1.222e-3 rad/A > sigma V_008 = 7.549e-4 rad/A. The
coincidence is exact in the full Ewald construction (|K + 2 pi h| = K for h = (0,+-4,4) whenever
2 kappa0 = G), so it holds with refraction: refraction enters only through kappa0, and every beam of the
multislice has a propagation constant that depends on |q| alone. Even with the multislice's own
kappa0 (exact propagator: kappa0^2 = k^2 sin^2 theta + 2 k sigma V0 cos theta - (sigma V0)^2, which is
1.9e-5 below G/2 in relative terms) the residual zeta(0,+-4,4) = 1.6e-6 rad/A is 1.3e-3 of the coupling.
Admixtures: (0,+-2,2), (0,+-2,6) 0.201 at 9.24 mrad; (0,0,4) 0.093; (0,+-4,0), (0,+-4,8) 0.062.
[110]: no exact beam; (+-1,-+1,1), (+-1,-+1,7) 0.348 at 6.53 mrad; (+-3,-+3,3), (+-3,-+3,5) 0.209 at
19.59 mrad; also (+-2,-+2,8) 0.184 at 13.06 mrad (not listed by H2, no consequence). CONFIRMED.

A7. Sampling (question 3; DERIVED_HERE and REPRODUCED by calling the engine, script section 7). With
f_max = 1/(3 dx): external beam 0.6433 1/A (dx <= 0.5181 A), wave inside 0.7365 1/A (0.4526 A),
(0,0,8) coupling 1.4731 1/A (0.2263 A = a/24), (0,+-4,4) 1.0416 1/A (0.3200 A), (0,0,12) 2.2096 1/A
(0.1509 A), (0,0,16) 2.9461 1/A (0.1131 A). The engine's `check_band` (grid.py:135-166, called by
`reflection_setup` with the incident and outgoing external and internal angles only, engine.py:149-151)
passes for dx up to 0.450 A and fails first at 0.455 A when called here: CONFIRMED that a grid between
0.2263 and 0.4526 A passes while the transmission function loses its (0,0,8) Fourier component
(reflection then proceeds only through second-order paths such as (0,0,4) twice). F(f_max^2)/F(0) =
0.0303 (0.13 A) and 0.0186 (0.10 A). dz = a/4 = 1.357725 A at [100], p/4 = 0.960057 A at [110].

A8. Scenario rows (question 6; DERIVED_HERE, script section 8). I rebuilt every row of H2's table from
the rules stated in the H2 report alone (entrance 10 slices; contact 2/tan(theta); run-in; field =
3 + 2 resolution elements, or the transverse / torus fields of section 2.6; exit margin 3 elements;
whole z-periods of a; H = L_z tan(theta) - 2 - h - 1; vacuum = ceil(H + L_z tan(theta) + 1) (+19.008 A
for the ridge); depth 15 + 55/65 (+20.366 for the torus); y = whole periods; 7-smooth grids at
<= 0.13 A; (001) layers counted from the depth; 1 atom per y-period per same-parity layer in each
[100] slice). Result, identical to H2 in every printed digit: atoms 31,116,960 / 6,266,610 /
51,031,008 / 62,608,476 / 5,618,340 / 69,983,424 / 2,710,784 / 2,666,624 / 93,496,543 / 136,189,483 /
214,032; grids, slices, x-y-z extents, the 4.096 / 0.705 / 5.824 / 9.625 / 0.631 / 7.444 / 0.278 /
0.275 / 0.023 GB of engine arrays, GPU-model times (13 min, 56 s, 28 min, 46 min, 48 s, 49 min, 22 s,
22 s, 82 min, 2.4 h, 1 s) and CPU x1.5 times (17.2 h, 72 min, 33.6 h, 2.6 d, 62 min, 2.3 d, 28 min,
27 min, 3.8 d, 6.5 d, 75 s) with my own median fit of the RAW calibration entries (FFT 2.786e-10
s/(px log2 px), element-wise 1.803e-9 s/px, exp 4.463e-8 s/element, GEMM 362 GFLOP/s), totals over
8 realisations (5.7 d / 103 min ... 52.1 d / 19.4 h) and host memory at 240 B/atom (7.5, 12.2, 22.4,
32.7 GB). The torus memory (10.852, 14.361 GB) needs H2's bound of 595 extra atoms per slice on top of
my flat-slice maximum (13 668, 15 503): 10.756 + 0.096 and 14.258 + 0.103 GB. Also confirmed: W =
777.9 A (0.1 deg, a/4), 1555.8 A (a/2), rounded up to 782.0 / 1558.7 A of whole y-periods; strips
84.1 / 168.3 / 1178.0 / 1262.1 A; dlat 64.2 / 110.4 / 165.8 A; W_min 140.4 / 232.7 / 343.6 A; torus
gaps 143.2 / 235.5 A; overlayer paths 1240 / 2479 / 3719 A; 8 resolution elements 2975 A; ring volume
197 167 atoms.

A9. Built cells against the engine itself (REPRODUCED, script section 11). Three study.yaml points
(tfix_bragg_abs0_L0, tfix_off20_abs10_L5k, step_w32_bragg_abs10_L5k) built with the M2 case code: the
engine's `estimate_resources` gives 3,844,352 / 10,701,408 / 340,405,248 B and 0.314 / 1.722 /
22.750 GPU-model seconds, equal to my replica and to the M2 printout (grid, slices, atoms). Two H2 rows
built for real with the repository builder (one z-period, tiled): row V (214,032 atoms, 2000 x 84, 4126
slices, 23,236,480 B) and row 2a_a4_Wmin_r0.10 (5,618,340 atoms, 2000 x 2187, 4126 slices, n_max 1378,
630,765,808 B = 0.631 GB, GPU model 47.8 s). With H2's beam (H from the stated rule, 2 A above the
highest top layer) all ten geometry assertions of the engine's `reflection_setup` pass for both. The
cost model is therefore a faithful copy of the engine's accounting; whether that accounting is right is
finding M4.

A10. Engine rerun of `bu_100_r010` (question 4; REPRODUCED, `--rerun`, `tools/hpc/review_h5_rerun.json`).
My own cell construction (repository builder, one period tiled, same layout: 382 840 atoms, 2500 x 84,
4514 slices, L_z 6128.77 A, H 95.89 A, vacuum 196 A) and my own read-out (y-average, sin^2 vacuum mask
from 2 A above the top layer, pass band 0.1 1/A about f_c, demodulation, ray mapping
z_s = L_z - (x - x_s)/tan(theta_ext), 500 A bins from the contact point, reference = last 2500 A before
the last 750 A). Plateau |R| = 0.2707, arg = -1.5394 rad: identical to H2. Every 500 A bin agrees with
H2 to <= 2e-3 in |R| and <= 4e-3 rad in phase (largest differences in the exit bin). Converged beyond:
phase 1e-2 rad 1500 A, 3e-3 rad 3000 A; amplitude 3e-2 2500 A, 1e-2 3000 A (H2: same). Exit-plane
intensity deeper than 1e-2 / 1e-4 / 1e-6: 26.0 / 53.2 / 94.2 A (H2: same); 2.0e-1 at 10 A, 1.9e-2 at
20 A. The result does not depend on the mask edge (2-4, 2-6, 2-10 A: plateau 0.2707-0.2712, same
convergence distances). The run took 192 s here (load 5.5 after the run). H2's r = 0.05, r = 0 and
[110] strips were not rerun; they rest on the same, now reproduced, method.

## B. Findings

### M1 (MAJOR). "MEASURED" is not an evidence label of this project and overstates simulation output

Quoted (brief, line 52): "the run-in after the illumination edge until the reflected wave has settled,
MEASURED with the engine: 2500 A for the TEST_ONLY absorption r = 0.1, ..."; (line 56) "15 A absorber
plus 55-65 A of clean crystal (MEASURED; ...)"; (section 1) "MEASURED_HERE marks a number measured in
this container with the repository's UNVALIDATED engine ... (a REPRODUCED-type number whose premises are
those inputs)"; the calibration JSON is labelled "MEASURED_HERE".

Evidence. The label set of the instruction file is METADATA_VERIFIED, SECTION_READ, REPRODUCED,
PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED (plus TEST_ONLY and NUMERICAL in code). H2's own
definition says the numbers are REPRODUCED-type. They are reproducible: my independent rerun of
`bu_100_r010` gives the same plateau (0.2707, -1.5394 rad), bins, convergence distances and depths (A10).
In the brief, where Ali reads it, capitalised "MEASURED" next to a length reads as a laboratory
measurement; these are outputs of an UNVALIDATED engine on TEST_ONLY absorption, a TEST_ONLY azimuth and
an ASSUMPTION angle.

Required correction. Replace MEASURED_HERE by REPRODUCED everywhere, with the qualifier once per section:
"REPRODUCED: output of the UNVALIDATED engine on the TEST_ONLY/ASSUMPTION inputs stated, saved in
`tools/hpc/supercell_sizing_measurements.json` (bu_100_r010 independently rerun by H5)". Brief:
"the run-in ..., computed with the (UNVALIDATED) engine on flat strips: 2500 A ...". The CPU calibration
is a timing on this container; label it "timed here (4 shared cores, load 0.36)" rather than a new label.

### M2 (MAJOR). The design run-in rests on an unlabelled amplitude tolerance (3e-2) that is looser than the repository's criterion (1e-2)

Quoted (2.4): "The design run-in is 2500 A (phase 1e-2 AND amplitude 3e-2)"; (section 1 table) only
"phase tolerance for every convergence length | 1e-2 rad | the M2 fixed-beam translation criterion".
The 3e-2 is hard-coded in `supercell_sizing.py` (lines 306, 1082) and appears in no input table.

Evidence. The repository's convergence criterion for the same quantity is `|err_rad| <= 1e-2` AND
`|amp_ratio - 1| <= 1e-2` (`scripts/hpc/null_test_study/README.md`, M2 10.4). With 1e-2 on the amplitude,
H2's own data and my rerun give run-ins of 3000 A (r = 0.1; my rerun: amplitude within 1e-2 beyond
3000 A), 5000 A (r = 0.05, unchanged: H2 amplitude 1e-2 at 4500 A) and 9000 A (r = 0, H2 amplitude 1e-2
at 9000 A). Consequence (script section 12): row 2a_a4_miscut0.1_r0.10 becomes z = 6101.6 A instead of
5602.0 A, 33,899,040 atoms (+8.9 %), grid 2160 x 12096, 4.379 GB, GPU model 15 min, CPU x1.5 19.7 h;
row r = 0 z = 12 102.8 A (+9.0 % atoms, 8.023 GB); the torus r = 0.1 row z = 9919.5 A, 99,185,647 atoms
(+6.1 %), 11.140 GB. The 1116 A reconstruction margin after the run-in partly absorbs the difference,
which is why this is MAJOR and not BLOCKER, but the brief presents 2500 A as "not a free choice".

Required correction. Either adopt the repository's 1e-2 amplitude criterion (run-in 3000 / 5000 /
9000 A and the rows recomputed), or state 3e-2 in the section 1 input table as an ASSUMPTION with its
reason (for example: the amplitude enters only the B29 amplitude mask and the fringe contrast) and quote
both run-ins in the brief: "2500 A (phase 1e-2, amplitude 3e-2, ASSUMPTION) or 3000 A (amplitude 1e-2,
the null-test criterion)".

### m1 (MINOR). Same quantity, different values inside H2 (terrace width, resolution element)

Quoted (brief): "two terraces of the miscut width for steps parallel to the beam (0.1 deg: 782 A each
for a/4 steps)"; (section 4) "0.1 deg: 777.9 / 1555.8 A". Evidence: h/tan(0.1 deg) = 777.9 A; 782.0 A
is that width rounded up to 144 whole y-periods of a (script section 8). Proposed: "0.1 deg: 777.9 A
(a/4), built as 144 periods = 782.0 A".

Quoted (2.6): "one image resolution element is 371.8 A of surface (6.0 A in the image plane,
foreshortening 1/sin(theta_ext) = 61.98)". Evidence: 6.0/sin(16.1347 mrad) = 371.884 A (3 elements
1115.7 A); H2's tool computes 6.0/tan(theta) = 371.836 A (1115.5 A; `supercell_sizing.py` line 729,
seen after my number existed); likewise the T2 check prints 364.17 (tan) where T2's 1/sin gives
364.22 A. No row changes (the whole-period rounding absorbs 0.2 A). Proposed: use 6.0/sin(theta_ext)
= 371.9 A as stated, or say "6.0/tan(theta_ext) (the exit-plane mapping)"; and in any summary state
both angles: 371.9 A at 16.1347 mrad (MIP, B32) and 364.2 A at 16.4743 mrad (V0 = 12 V, B19, T2).

### m2 (MINOR). The Bethe "missing-band" fractions are not converged in the beam set

Quoted (section 5): "the perturbative Bethe correction of V(0,0,8) from couplings outside its band is
2.8e-2 V_g at [100] and 3.0e-2 V_g at [110]; at dx = dy = 0.10 A it is 4.5e-3 and 8.2e-3".
Evidence (script section 6 and the cut-off scan printed there): with |h|,|k|,|l| <= 12 / 16 / 20 the
missing part at 0.13 A is 1.75e-2 / 2.85e-2 / 3.12e-2 V_g ([100]) and at 0.10 A 1.7e-3 / 3.1e-3 /
5.8e-3 V_g; it grows with the cut-off. The effective-coupling ratio 0.479 / 0.490 / 0.493 and the
admixtures are stable. Proposed: "at least 3e-2 V_g at 0.13 A and 6e-3 V_g at 0.10 A (perturbative,
not converged in the beam set); the 0.13/0.10 A convergence run (run order 2c) decides".

### m3 (MINOR). "None of them is a free choice" overstates

Quoted (brief): "Four lengths set the cell, and none of them is a free choice". Evidence: the run-in
depends on the TEST_ONLY absorption (item 21) and on the unlabelled 3e-2 tolerance (M2 above); the
margins on B28/B29 (6.0 A resolution from the demo carrier and mask); y on the miscut scenarios (item 11,
ASSUMPTION); the vacuum on the engine's conservative item-2 rule (H2 itself shows 92 A would do instead
of 178 A). Proposed: "Four lengths set the cell; each follows from a stated stand-in, tolerance or engine
rule (section 1), none from a free choice made in this sizing."

### m4 (MINOR). The r = 0 run-in is quoted without its caveat in the brief

Quoted (brief): "8000 A without absorption (where the two-beam tail predicts 22 572 A)". Evidence:
section 2.4 of H2 says "tested only to 11 251 A": the reference window (8751-11 251 A) itself lies inside
the two-beam tail (|E| = 0.035 at 10 000 A, script section 4), so "within 1e-2 of the plateau beyond
8000 A" is relative to a plateau that is not established. Proposed: "8000 A without absorption relative
to a 8751-11 251 A reference window only (not established; the two-beam tail needs 22 572 A)".

### m5 (MINOR). The thermal displacement is labelled with the inspected repository's inert row A7

Quoted (section 1): "thermal displacement | 0.076 A rms per axis | ASSUMPTION A7 (the inspected
repository's value, also the value in Prismatic's example input SI100.XYZ, L2 C14; ...)". Evidence:
model_assumptions A7 is an assumption "inherited from the inspected repository", status "Inert: thermal
effects are never enabled". L2 C14 and E17 (SECTION_READ of the Prismatic input documentation) support
that 0.076 A is the per-axis sigma of Prismatic's example file, not a Si Debye-Waller value. The value now
drives the frozen-phonon counts and the "1/0.72" statement. Proposed: add a row B35 to
model_assumptions ("u = 0.076 A per axis, stand-in for a sourced Si Debye-Waller value; not a
PROJECT_INPUT item yet") and cite B35, not A7; add the sourced value to docs/06 section F.

### m6 (MINOR). The torus cell has no margin-eroded flat reference along the beam

Evidence (script section 8, torus rows): after the run-in the flat surface upstream of the 1262 A strip
is exactly the 3-element margin (1115.5 A), and downstream of the second strip comes the exit margin;
across the beam the gap between periodic images is 143.2 A (r = 0.1). T2's phase-map zero is "the
median over the flat surface outside the feature, eroded by the three-resolution margin" (T2, B29); T2's
own field had about 3800 A of flat surface up- and downstream and 132 A each side. H2 says the row "shows
contrast, not heights", which remains true; a phase map with a zero would need about 2 resolution
elements (744 A) of flat measured surface upstream of the strip. Proposed: say so in row 3.

### m7 (MINOR). "Six times weaker" at [110]: amplitude, not intensity

Quoted (brief): "At [110], the M2 study azimuth, the same angle reflects six times more weakly".
Evidence: plateau amplitudes 0.2707 / 0.0432 = 6.3 (intensity 39). Proposed: "the specular amplitude is
6.3 times smaller (intensity 39 times)".

### m8 (MINOR). The x1.5 CPU factor is not labelled and is untested where the time goes

Quoted (brief table header): "CPU (4 cores here, x1.5)". Evidence: the factor comes from one M2 smoke
run (38.6 s against an estimate of 26.6 s, load 6 to 9; M2 section 7) and is supported by H2's five
strips (1.26-1.89 after dividing by load/4). All six runs have ny = 60 to 480, where FFT and element-wise
passes dominate; in every production row the model attributes 86-93 % of the CPU time to the potential
construction (script section 8), which none of those runs exercised. Proposed: label the factor
ASSUMPTION (empirical, narrow cells only) and see M4 for the measured wide-slice cost.

### m9 (MINOR). The lateral buffer premise may be short

Quoted (section 4): "for as long as the field remembers it, i.e. the run-in length. dlat = L_run
tan(alpha_y) + 3 x 6 A ... = 64.2 A (r = 0.1)". Evidence (DERIVED_HERE): a surface-parallel wave
damped only by the proportional absorption falls to 1e-2 in amplitude after ln(100)/(sigma r V0) =
4545 A at r = 0.1 (5168 A for the slow two-beam-like mode sigma r (V0 - V_044)), i.e. 84-95 A of
lateral travel at 18.47 mrad, dlat 102-113 A and W_min 216-238 A instead of 140 A. Coupling may damp
it faster; H2 labels the premise and the terrace-width study (run order 5, W = 50-400 A) decides.
Proposed: quote "W_min about 140-240 A (estimate; run order step 5 decides)".

## C. Section 10 of H2 (what the engine lacks), checked in the code (question 9)

Every file and line reference in H2's table N1-N14 was opened (SECTION_READ of the code at 661762e):
N1 potentials.py:101-122 (proportional model only), N2 potentials.py:125-141 and 256-259 (independent
Gaussian displacements on all three axes, seeded), N3 pipeline/config.py:673-680 (non-zero convergence
refused) and illumination.py:27-58 (SheetBeam uniform in y, tilt in x-z only), N4 si001.py:418-425
(dimer_2x1 raises NotImplementedError), N5 si001.py:430-457, pipeline/config.py:681-688,
potentials.py:228-234 (MIP for Si only) called from engine.py:145, N6 si001.py:175-196 (net height
change refused), N7 engine.py:43-47 and no `forward/dynamical/` module, `ContinuumTerracePotential`
constant, N8 grid.py:135-166 (beam angles only; REPRODUCED in A7), N10 potentials.py:289-309 (one GEMM
per slice, `slice_key` caches only empty slices), N12 null_test_cases.py:140-149 (sum over all x). All
accurate. Two qualifications: N9 quotes T1's 2.4 kB/atom, which is peak RSS including about 0.8 GB of
process overhead (M2 section 7), so the feature builder's own cost is closer to 1 kB/atom (upper bound
as stated is fine); and the list omits what finding M4 below measures: the engine's own resource
accounting leaves out the float64/complex128 intermediates of the structure-factor exponentials
(potentials.py:302-303) and times a complex64 proxy for them (engine.py:394-402).

## D. Places in the repository that carry a different value for the same quantity (question 8)

The summary documents must correct or qualify these (none is H2's file; I edited none):

1. docs/05 section 9 (line 372): "build-up scale of order 1600 A along the beam at the (0,0,8) Bragg
   peak without absorption". The engine's static V(0,0,8) is 1.0357 V, so the two-beam scale is
   1/(sigma V_g) = 1325 A; the no-absorption two-beam field settles to 1e-2 only after 22 550 A; the
   engine strips settle (1e-2 rad, 3e-2 amplitude) after 2500 / 5000 / 8000 A for r = 0.1 / 0.05 / 0
   (static lattice). Source of the 1600 A: M2 section 10.2 (0.84 V from an f_e read 19 % low, A2).
2. M2 section 10.2 (report, not edited): "V_g(008) ~ 0.84 V ..., xi_g ~ 5100 A, penetration ~ 30 A,
   ~1600 A along z per e-fold" -> 1.0357 V, 4161.7 A, 24.5 A (two-beam 1/b), 1325 A. Summaries must
   quote H2/H5, not M2, for these.
3. docs/05 section 4.3 item 4, docs/03 section 5 (line 206), docs/00 item 2 (line 25), source map SM16:
   "0.08 to 0.42 um" of cell length "for penetration depths of 2 to 10 nm" (at theta_int = 24 mrad, the
   CFG-A geometry). This is the geometric reach of the refracted ray, necessary but not sufficient (M2
   10.4); at the (0,0,8) condition the reflection needs 2500-8000 A of run-in after first contact, and
   the realistic [100] cells are 5602-11 924 A long. docs/05 item 4's "grids of order 1500 x 600 pixels
   ... thousands of 1 A slices" becomes 2000-3969 x 84-24 000 pixels and 4126-8782 slices of 1.3577 A.
4. docs/05 section 4.3 item 5 and docs/03 section 5 (line 207): the sampling rule names only the
   outgoing beam angle ("2/3 rule at 0.13 A gives 64 mrad ... adequate"). Add: the working reflection's
   Fourier coefficient must lie inside the band, f_max = 1/(3 dx) >= |g_008| = 1.4731 1/A, i.e.
   dx <= a/24 = 0.2263 A; the engine's check_band accepts up to 0.450 A (A7; H2 N8).
5. The (0,0,8) glancing angle: 16.1347 mrad (multislice runs, V0 = 13.903 V of the Kirkland potential,
   B32; M2, T1, H2) and 16.4743 mrad (geometric runs, V0 = 12.0 V, B19; T2), printed as "16.5 mrad" in
   docs/05 CFG-B, B17 and configs/cfg_b_si001_patterned.yaml. Not a contradiction, but every summary
   number derived from the angle must name its V0: foreshortening 61.98 vs 60.70, wrap period
   0.7772 A vs 0.7612 A ("0.76 A" in docs/05 CFG-B), resolution element 371.9 A vs 364.2 A (T2's 364 A).
6. model_assumptions A7 ("Inert: thermal effects are never enabled") is now the source cited for the
   production frozen-phonon displacement (m5): a new B-row is needed.
7. M2 section 7 "HPC-size cell" (80.0 x 38.4 x 1000.4 A, 72 240 atoms) and README_HPC section 5 are
   engine-timing examples, not converged cells; a summary must not present them as the realistic size.
8. scripts/hpc/null_test_study/README.md (pass criterion |err| <= 1e-2, |amp - 1| <= 1e-2) with the
   study cells' 21 A clean depth (null_test_cases.py: clean = buildup + 1): H2's stored depth profiles
   put the bulk absorber where the exit-plane intensity is still 1.9e-2 ([100]) and 4.2e-2 ([110]),
   amplitude 0.14 / 0.20 (script section 12). An absorber reflection of a few percent then enters the
   specular amplitude at the 1e-3 to 1e-2 level, the size of the pass criterion (DERIVED_HERE estimate;
   the absorber reflectivity is not measured, UNVERIFIED). H2 says the study "tests the engine, not the
   production convergence"; the README should say it too before Ali runs it.
9. scripts/hpc/alliance/README_ALLIANCE.md section 4.6 chooses the GPU instance with
   `--need-gpu-mem-gb <from dry-run>`, i.e. from the engine's `estimate_resources`; see M4 for how far
   below the real device peak that estimate lies for the wide production cells.

