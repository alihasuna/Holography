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
