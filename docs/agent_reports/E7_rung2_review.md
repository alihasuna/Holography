# E7: adversarial review of P2's rung-2 exact reference and of the proposed engine test R2-A

Prepared 2026-09-24 by review agent E7. Written incrementally; status at the end of the file.
Under review (not edited): `docs/agent_reports/P2_rung2_reference.md` (P2 report, final run in its
section 11) and `tools/physics_checks/rung2_reference.py` (P2 tool).
My code: `tools/review/e7_recompute.py`, written WITHOUT reading the P2 tool's implementation of any
quantity it recomputes; it imports the P2 tool only in its last section, to compare numbers. Saved
output: `tools/review/e7_recompute_output.txt` ("E7 out §n" below). Nothing committed or pushed; no
other file edited.

Severity scale: BLOCKER (the reference or the test would validate or fail the engine wrongly),
MAJOR (a number, criterion or claim that is wrong or unsupported and matters for R2-A or for the
sizing), MINOR (wording, label or traceability defect that does not change a decision), NIT.

## 0. Log

* read: P2 report (all), docs/physics_conventions.md, reflection_holo/constants.py, the engine
  modules engine.py, potentials.py, propagator.py, analysis.py (flat_reflection_coefficient),
  illumination.py, grid.py, physics.py, forward/cell.py; H2 sections 0 to 3 and 10
  (`docs/agent_reports/H2_realistic_supercell_sizing.md`), H5 (`H5_sizing_review.md`) sections A-M3,
  D-G; the run-in and clean-depth lines of the H7-corrected `tools/hpc/supercell_sizing_output.txt`;
  M2 sections 2 and 10 (`M2_multislice_engine.md`); tests/forward/null_test_cases.py (geometry
  lines); tests/forward/smoke_case.py (head).
* NOT read before my numbers were final: `tools/physics_checks/rung2_reference.py` (only imported,
  as a black box, in the comparison section of my script).
* wrote `tools/review/e7_recompute.py`: my own exact solvers (A: continued fractions of the Bloch
  recurrence plus complex Newton on kappa; B: my own 4th-order Magnus transfer matrix, Floquet
  eigenvector; C: finite crystal on an absorbing substrate), the two-beam forms derived again, the
  build-up integral, a transfer-matrix model of the engine's bulk absorber, and a review-only
  stand-in `E7PeriodicContinuum` (P2 8.1 specification, written here, not E1's class) that I ran
  through the UNMODIFIED engine (`run_realisation`, `flat_reflection_coefficient`) to test the R2-A
  protocol itself. One bug of mine found by my own convergence test (sign of the Magnus commutator;
  fixed before any number was used).
* read E1's in-progress `tests/forward/test_rung2_bragg.py` and `ladder_cases.rung2_case` (geometry
  lines only, to know where E1 puts x_s): x_s = 15 + D A with dx exact, i.e. a pixel centre.
* only after all my numbers were final: imported the P2 tool as a black box (E7 out §10).
* concurrency: engine.py, illumination.py and potentials.py were being edited by other agents in
  the working tree during my runs (a y-tilt feature and E1's class); my stand-in uses neither; the
  module hashes at the start of the saved run are listed in section 7 below.

## 1. Verdict in brief

No BLOCKER. P2's reference is right. My three solvers agree with each other to 1.4e-9 or better.
Every exact number I recomputed agrees with P2's tool to 2.3e-12 or better (r = 0), and to 1.7e-13
and 7.7e-14 at r = 0.05 and 0.1. The unmodified engine, run with a potential class built to P2's
section 8.1, reproduces P2's R(K) in every bin to 4.5e-4 (r = 0.1) and 5.1e-4 (r = 0.05) with no
fitted phase. The conventions are therefore consistent end to end: R at x_s, cosine maximum at x_s,
exp(+i k.r), x outward, and the reference plane of `flat_reflection_coefficient`.

There are three MAJOR findings. They concern the test design and a depth recommendation, not the
reference. M1: criterion (c) (dx order >= 1.5) fails a correct engine whenever x_s is not on a pixel
centre. M2: the error budget was measured on grids with dx = 0.0249995 and 0.0249988 A, not the
specified 0.025 A; at r = 0.05 the engine's error on the specified grid is 5.1e-4, not 2.8e-4. M3:
the recommendation ">= 100 A of clean crystal" for atomistic null tests contradicts H2/H7's 55-65 A,
and P2's own 1D model does not require it at the 1e-2 criteria. T_A = 1.5e-3 stays valid.

## 2. Findings

### M1 (MAJOR). Criterion (c) can fail a correct engine: the dx error depends on where x_s falls in its pixel

Quoted (P2 8.4): "Criterion (c), convergence: max |dR| at dx = 0.05 A over that at dx = 0.025 A
>= 2^1.5 (split step: 3.3, order 1.71)."; (P2 7, reading (i)) "the residual being mainly
discretisation (dx order 1.71 between 0.05 and 0.025 A ...)".

Evidence (E7 out §9). Setup: the unmodified engine with the stand-in class, r = 0.1, Fresnel,
D = 100 A, Z_e = 5000 A, dz = 1 A, dx exact. The pixel fraction of x_s is kept the same on both
grids:

| x_s in its pixel (both grids) | max abs(dR), dx 0.05 A | max abs(dR), dx 0.025 A | ratio (order) | criterion (c) |
|---|---|---|---|---|
| centre (x_s = 115 A: P2's and E1's geometry) | 1.44e-3 | 4.48e-4 | 3.21 (1.68) | passes, ratio 13 % above 2.83 |
| quarter pixel | 9.27e-4 | 3.31e-4 | 2.80 (1.49) | FAILS |
| boundary | 7.65e-4 | 2.79e-4 | 2.74 (1.45) | FAILS |

Other data points:
* From dx = 0.025 to 0.0125 A (pixel centres) the error goes 4.48e-4 -> 2.20e-4: order 1.03.
* Doubling only Z_e lowers it from 4.48e-4 to 3.52e-4, so a dx-independent part of about 1e-4 sits
  under the dx term. The ratio of two maxima is therefore not an order.
* Per bin (pixel centres, 18 bins), |e(0.05)|/|e(0.025)| ranges from 3.07 to 5.88. A p = 2
  Richardson extrapolation leaves 1.59e-4.

Consequence. With P2's exact geometry a correct engine passes. This is the only reason M1 is not a
BLOCKER. Moving x_s off a pixel centre makes (c) fail a correct engine. That happens with a change
of D, of the absorber thickness or of dx, or with a box whose extent is not a multiple of dx (the
case of P2's own split step, M2). E1's in-progress test (`test_r2a_dx_convergence_order`) uses P2's
geometry.

Correction.
* State in 8.2 that x_s lies on a pixel centre of every grid: dx exact, and x_s = 15 + D a multiple
  of 0.05 A.
* Replace (c) by one of:
  * a per-bin guard: "for every bin with |eta| <= 3, |r(0.05) - R_ref| >= 2 |r(0.025) - R_ref|,
    same pixel fraction of x_s" (observed minimum 3.07);
  * "max ratio >= 2".
* Call it a convergence guard, not an order measurement.

### M2 (MAJOR). The budget was measured on grids that are not the specified one; at r = 0.05 the engine error on the specified grid is 5.1e-4, not 2.8e-4

Quoted (P2 8.4 budget):
* "finite cell + discretisation (dx 0.025 A, dz 1 A) | 4.4e-4 (split step F; ...) | 2.8e-4 (split
  step F_r005)";
* "total | <= 4.5e-4 | <= 3.2e-4";
* "tolerance T_A | 1.5e-3 | 1.5e-3 | 3.3x and 4.7x the budget, for a different sub-pixel position of
  x_s and implementation details of the class";
* P2 7 table: runs F, X, F_dz05 and F_r005 listed with "dx (A) 0.025".

Evidence (E7 out §9, §10).
* P2's split step, called as a black box, ran with dx = 0.0249995325 A (r = 0.1; x_s/dx =
  4600.086) and 0.0249987575 A (r = 0.05; x_s/dx = 6600.328). The box extent is not a multiple of
  0.025 A.
* On exactly those grids the engine with my stand-in class reproduces the split step to 5.8e-15 and
  7.6e-14, including P2's 4.39e-4 and 2.78e-4. So P2's split step is a faithful replica of the
  engine's scheme, and P2's section 4 and 7 conclusions carry over to the engine.
* On the grid P2 specifies and E1 builds (dx exactly 0.025 A, x_s on a pixel centre), the engine
  gives 4.48e-4 at r = 0.1 and 5.14e-4 at r = 0.05. At r = 0.05 with dx = 0.0125 A: 2.44e-4.
  At r = 0.05 with Z_e = 20000 A: 4.19e-4.
* At r = 0.1 the error spans 2.79e-4 to 4.48e-4 over the pixel positions tested (M1). The
  pixel-centre case is the largest. P2's allowance "for a different sub-pixel position" was not
  tested, but it holds.
* The margin at r = 0.05 is 1.5e-3/5.14e-4 = 2.9x, not 4.7x.
* T_A = 1.5e-3 remains adequate for a correct engine.

Correction.
* Budget row r = 0.05: "5.1e-4 (engine and split step, dx = 0.025 A exact, x_s on a pixel centre;
  2.8e-4 with x_s 0.33 pixel off centre)"; total <= 5.5e-4; margin 2.9x.
* In the 7 table, print the dx actually used (0.0249995 and 0.0249988 A) or rerun with dx exact.
* State the pixel-position spread.

### M3 (MAJOR). The clean-depth recommendation for atomistic cells conflicts with H2/H7 and is not required by P2's own model at the stated criteria

Quoted:
* P2 6.5: "Recommendation for the atomistic null-test study (not an engine change): a clean depth
  of at least 100 A for r = 0.05 to 0.1".
* P2 10, recommendation (3): "for atomistic (0,0,8) null tests use >= 100 A of clean crystal above
  the absorber with r >= 0.05".
* Against: H2 brief, "depth: 15 A absorber plus 55-65 A of clean crystal"; H7-corrected
  `tools/hpc/supercell_sizing_output.txt`, "clean depth D_clean = 55 A" (r = 0.1) and "65 A"
  (r = 0.05 and r = 0), sizing rows with 70.0 and 80.0 A below the top layer.

Evidence (E7 out §8): P2's own 1D model, reproduced. Setup: full laterally averaged layer potential,
16.13477 mrad, pair A / B = A + a/2 as in `tests/forward/null_test_cases.py`. Each cell gives
arg(R_B/R_A) in rad, then abs(R_B/R_A) - 1:

| r | D = 21 A | 55 A | 65 A | 100 A |
|---|---|---|---|---|
| 0.1 | -6.0e-3, +1.3e-2 | -1.0e-4, +1.2e-4 | -3.1e-5, +3.1e-5 | -3.9e-7, +2.1e-7 |
| 0.05 | -9.5e-3, +3.2e-2 | -6.3e-4, +1.3e-3 | -2.8e-4, +4.9e-4 | -1.6e-5, +1.7e-5 |
| 0 | -8.1e-3, +6.5e-2 | -4.9e-4, +5.3e-3 | -2.3e-4, +2.5e-3 | -1.8e-5, +2.0e-4 |

* Against the null-test criterion (1e-2 rad and 1e-2 in amplitude), H2's 55 and 65 A leave a
  factor 7.7 or more for r >= 0.05 (worst case r = 0.05 at 55 A: 1.3e-3).
* The 1D model also penetrates deeper than the atomistic [100] crystal. Its stationary intensity
  falls below 1e-4 only at 101.9 A (r = 0.05) and 69.3 A (r = 0.1) (E7 out §8b), against 60.6 A
  and 53.2 A computed by H2 with the engine (H2 2.4).
* P2 read H2 only in sections 2.1 to 2.3 (P2 log) and does not mention H2's depth.
* Adopted as written, (3) would add 35 to 45 A of x to every atomistic row with no gain at the
  stated criteria.

Reconciliation (which criterion, which depth):
* Rung-2 continuum cells. The criterion is T_A = 1.5e-3, and the physics is exactly the 1D problem.
  Keep P2's 100 A (r = 0.1) and 150 A (r = 0.05): the absorber term is at most 1.8e-6 and 3.3e-5.
* Atomistic sizing and the null-study redesign. The criteria are 1e-2 rad and 1e-2 in amplitude.
  * At [100], keep H2/H7's 55 A (r = 0.1) and 65 A (r = 0.05).
  * At [110], the study azimuth, use >= 65 A: H2 2.4 found 1e-4 at 64.2 A for r = 0.1.
  * The study's current 21 A fails in the 1D model as well: abs(B/A) - 1 = 1.3e-2 to 6.5e-2.
* r = 0 (B30 rows). At the plateau centre, 65 A leaves abs(R_A - R_inf) = 1.4e-2 (full layer
  potential; 1.1e-3 at 100 A). Outside the plateau the absorber reflects 0.15 to 0.38 at any depth
  (reproduced, section 3.7). The r = 0 rows are therefore not converged at 1e-2 in absolute terms at
  any listed depth. Their translation residual (2.5e-3 at 65 A) is within the null criterion.
* P2: replace recommendation (3) by these bullets, or cite H2/H7 and name the criterion that gives
  100 A (a 1D translation residual of about 2e-5).

### MINOR

m1. Overstated sensitivity.
* Quoted (P2 8, rationale): "rung 2 therefore tests the engine's effective potential at the mV
  level".
* Evidence, engine with V0 + 5 mV in the class (E7 out §9): max abs(dR) = 8.21e-4 at r = 0.1, which
  PASSES T_A, and 1.94e-3 at r = 0.05, which fails.
* Evidence, perturbed reference (E7 out §9b):
  * V0 + 3 mV gives 5.86e-4 (r = 0.1) and 1.28e-3 (r = 0.05).
  * A relative sigma error of 1e-4 gives 2.71e-4 and 6.02e-4.
* A cell-averaged harmonic in the engine gives 8.83e-4 and passes.
* P2's own 8.4 table already shows that 5 mV is caught only at r = 0.05.
* Proposed: "R2-A tests the effective mean potential to about 4 mV (through its r = 0.05 case) and
  the phase origin to about 5e-4 A (0.001 A gives 3.1e-3 and 5.0e-3); the dx = 0.0125 A variant to
  about 2 mV."

m2. The Darwin error at the centre.
* Quoted (P2 3.2): "so the Darwin/TT phase is too small by 0.135 rad there".
* Quoted (P2 9 table): "the TT/Darwin phase is 0.135 rad too small at the centre (r = 0)".
* Evidence: exact minus Darwin at the centre is 0.137180 rad. The refraction part,
  2 atan(abs(r_F)), is 0.134890 rad (E7 out §5).
* Proposed: "too small by 0.137 rad, of which 0.135 rad (2 atan abs(r_F)) is the refraction at the
  mean-potential step".

m3. The finite cell.
* Quoted (P2 7, reading (iii)): "With Z_e = 5000 A (r = 0.1) and 10000 A (r = 0.05) the finite cell
  no longer limits the accuracy."
* Evidence, exact smooth-edge transient at the exit distance (E7 out §7): 1.1e-4 to 2.2e-4 at
  r = 0.1 and 5000 A; 6.5e-5 to 2.3e-4 at r = 0.05 and 10000 A.
* Evidence, engine (E7 out §9): doubling Z_e lowers max abs(dR) from 4.48e-4 to 3.52e-4 (r = 0.1)
  and from 5.14e-4 to 4.19e-4 (r = 0.05).
* Proposed: "the finite cell contributes about 1e-4, a fifth of the residual; it does not limit the
  test at T_A = 1.5e-3."

m4. The comparison with M2.
* Quoted (P2 6.5): "M2 measured B/A = 1.014 at +5000 A with r = 0.1 (M2 section 10.2, SECTION_READ),
  close to the 1.013 predicted here".
* Evidence: M2's cells are at the [110] azimuth (`null_test_cases.py`: azimuth (1, 1, 0),
  P = a/sqrt(2)).
* At [110] and this angle, H2 2.4 found a specular amplitude of 0.043 (r = 0.1). The 1D model gives
  0.3137 (E7 out §8). The 1D model does not describe those cells, so the closeness of 1.013 and
  1.014 is not evidence for it (an inference stated as support).
* Proposed: "M2 measured 1.014; at [110] the specular amplitude is 0.043 (H2 2.4), far from the
  1D value 0.31, so the closeness is not a confirmation."

### NIT

n1. P2 6.1 table, column "V_l fit, dx = 0.01 A" (1.035737 and 13.902837 V).
* These are about 5e-6 V low: the fit basis of 60 harmonics (up to 44.2 1/A) does not span the
  50 1/A band at that pixel.
* An exact DFT of the engine's realised potential over 20 layer periods gives 1.0357425 V and
  13.9028426 V at both dx = a/256 and a/512 (E7 out §2).
* The values P2 used are unaffected.

n2. kc = 7.548907e-4 rad/A (P2 out §3) uses the unrounded V_g = 1.0357425 V.
* P2's printed "USED: ... V_008 = 1.035742 V" gives 7.548903e-4 (E7 out §3).
* Same quantity, two values in the 7th digit, no consequence.

n3. Grid-limited plateau numbers (P2 6.4, 7); none is used by R2-A (E7 out §4):
* Maxima: 16.18140 and 16.21117 mrad become 16.18180 and 16.21110 mrad on a 0.1 urad grid.
* FWHM of abs(R)^2: 395.94, 454.53 and 642.82 urad become 396.96, 455.30 and 643.78 urad by root
  finding.
* FWHM centres: 16.13633, 16.17823 and 16.24484 mrad.
* Phase sweeps across the FWHM: 1.7872 and 1.5363 rad.

n4. Names without a source.
* P2 states "No textbook passage was read for any formula below; none is cited", but names the form
  "Darwin (Takagi-Taupin)".
* Proposed: "two-beam form without the step reflection (called Darwin/TT here as a label; no source
  read)".
* No DOI, page or year appears in P2's report (checked).

## 3. The seven questions, one by one

### 3.1 Exact R(theta) and the phase-origin convention (question 1)

Methods (all mine):
* A: continued fractions of the three-term Bloch recurrence, with complex Newton iteration on kappa.
* B: my own 4th-order Magnus monodromy and its Floquet eigenvector with abs(mu) < 1 (flux criterion
  on the unit circle).
* C: 3000 periods on an absorbing substrate.

Agreement between them (E7 out §4):
* r = 0: 1.4e-9 over 301 angles from 15.4 to 16.9 mrad; the largest differences are at the band
  edges.
* r = 0.05: 2.0e-11. r = 0.1: 1.3e-11.
* Magnus convergence is 4th order: error ratios 16.0 per halving of the step. B agrees with A at
  the centre to 2.35e-12 (r = 0), 1.38e-11 (r = 0.05) and 1.24e-11 (r = 0.1) at 512 steps per
  period.
* A plane-wave eigenproblem (P2's Bloch method) was deliberately not used.

Numbers (E7 out §3, §4):
* The 39 entries (abs(R), arg R) of P2 6.3 "ex" at eta = -3 ... 3 for r = 0, 0.05 and 0.1 are
  reproduced to the printed digits (largest deviation 4.9e-5, rounding).
* Centre (two-beam, 16.13477 mrad): r = 0: arg R = 1.707976 rad; r = 0.05: 0.53532 exp(1.7627 i);
  r = 0.1: 0.33836 exp(1.8755 i).
* Exact midpoint: arg R = 1.700074 rad.
* Exact gap: 15.94648 to 16.32008 mrad (my own tr M = -2 root), width 373.595 urad, midpoint
  16.13328 mrad.
* Both edges lie 0.416 and 0.409 urad below the two-beam edges (15.94690 to 16.32049 mrad).
  Mathieu second order, -U_g^2/(2 G^2), gives -0.412 urad for both.
* Cosine maximum t below x_s: t = d/4 gives -3.13195 rad; t = d/2 gives -1.70360 rad.
* Full layer potential (V_004 ... V_048): gap 15.98286 to 16.31535 mrad, width 332.492 urad
  (-11.0 %), midpoint +15.83 urad; arg R = 1.67006 rad at 16.13477 mrad.

Convention check:
* physics_conventions.md: exp(+i k.r), x the outward normal, theta the external glancing angle,
  numpy FFT sign.
* `flat_reflection_coefficient` returns r(f) = Psi_exit(+f) exp(+i 4 pi f (x_s - x0)) /
  (Psi_0(-f) P_L(f)). Derived again from analysis.py: this is exactly R at x_s with incident
  exp(-iK(x - x_s)) and reflected R exp(+iK(x - x_s)), which is P2's definition.
* The engine's transmission exp(+i sigma V_p) gives U = +2 k sigma V, the sign P2 uses.
* The cosine maximum at x_s (t = 0) is the class's t_n = 0; the maximum sits at x = x_s - t,
  consistent with E1's class docstring.
* Decisive check: the unmodified engine, with a class built to P2 8.1, reproduces the reference in
  every bin to at most 4.5e-4 (r = 0.1) and 5.1e-4 (r = 0.05) with no fitted phase (E7 out §9). By
  contrast, a reference plane or cosine origin off by dx/2 = 0.0125 A changes R by 3.9e-2 to 6.2e-2,
  or arg R by about 0.1 rad (E7 out §9b).

### 3.2 V0 and V_008 from the engine's own potential (question 2)

(E7 out §2)
* Own Kirkland formula: f_e(q) = sum a_i/(q^2 + b_i) + sum c_i exp(-d_i q^2), and V_l = 8 (h^2/(2 pi
  m0 e)) f_e(l/a)/a^3. The Si parameters are read from abTEM's kirkland.json; the formula and
  h^2/(2 pi m0 e) = 47.877647 V A^2 are written here.
  * Result: V0 = 13.9028426 V, V_008 = 1.0357425 V.
  * The engine's 8 F/a^3 agrees to 2e-8 V and 5e-8 V.
* Engine-realised lateral average:
  * Setup: a flat [100] Si(001) cell (45 layers; builder, `build_reflection_cell` and
    `AtomicPotential`), summed over the slices of one period and averaged over y.
  * Method: an exact DFT over 20 layer periods from x_s - 30 a/4, with dx = a/256 and a/512.
  * Values: V0 = 13.9028426 V, V_004 = 2.7400937, V_008 = 1.0357425, V_012 = 0.5467016,
    V_016 = 0.3265205, V_020 = 0.2136469, V_024 = 0.1502739 V.
  * Imaginary (sine) parts <= 4.3e-14 V.
  * Identical at both pixels.
* So P2's used values (13.902843 V and 1.035742 V) hold. They agree with H2/H5's 1.036 V and the
  IAM MIP of 13.903 V (D3 F16).
* The only discrepancy is P2's dx = 0.01 A fit column (n1).

### 3.3 Two-beam form with the mean-potential step (question 3)

Derivation (DERIVED_HERE, Airy sum):
* Take the Fresnel step (vacuum to mean medium) with r_F = (K - q)/(K + q), transmissions t_F and
  t'_F, and inner reflection r'_F = -r_F.
* Put a crystal in the mean medium at the same plane with reflection R_D.
* Summing the multiple reflections: R = r_F + t_F t'_F R_D / (1 - r'_F R_D).
* With t_F t'_F = 1 - r_F^2 this is R = (r_F + R_D)/(1 + r_F R_D).
* The composition is exact if R_D is the embedded crystal's reflection at that plane. Darwin's rho
  is that reflection to first order: matching e^{-iqx} + rho e^{iqx} to c0 e^{-i kappa x} + c1
  e^{i(G - kappa)x} with kappa near G/2 near q gives rho = c1/c0.
* On the plateau, R_D = e^{i phi} gives abs(R) = 1 and arg R = phi - 2 atan[r_F sin phi/(1 + r_F
  cos phi)], i.e. +2 atan(abs(r_F)) at the centre.

Numbers (E7 out §5, 4001-point eta grids):
* r_F = -0.067547; 2 atan(abs(r_F)) = 0.134890 rad; exact minus Darwin at the centre = 0.137180 rad.
* Darwin + Fresnel against exact: 5.73e-3 (r = 0, abs(eta) <= 0.9); 1.04e-3 and 2.01e-3 rad
  (r = 0.05, abs(eta) <= 3); 4.96e-4 and 1.49e-3 rad (r = 0.1).
* Matched two-beam: 7.93e-3, 3.86e-3 and 2.94e-3.
* Darwin/TT: 0.138, 8.78e-2 and 7.60e-2.
* So P2's 5.7e-3 (r = 0) and 1.0e-3 (r = 0.05) are CONFIRMED. The "0.135 rad" is the refraction
  part only (m2).

### 3.4 Paraxial and "exact" propagators (question 4)

Why the Fresnel scheme has the exact stationary R(K):
* Beyond the front face the continuum potential is independent of z. The symmetric split step is
  then a z-periodic linear map, exp(-i dz H_eff) with H_eff = H + O(dz^2) (Strang splitting, BCH),
  where H = -(1/2k) d^2/dx^2 - sigma V(x) (with the numerical absorber and the band limit included).
* Its stationary states psi = u(x) exp(-i E z) satisfy u'' + (2kE + 2k sigma V) u = 0.
* The incident vacuum component exp(-iKx) fixes 2kE = K^2, so u'' + (K^2 + U) u = 0: P2's Helmholtz
  problem at the same K. Hence R_paraxial = R(K) identically, with no expansion in theta. Only the
  z-dispersion, and with it the z-scale of the transients, differs.

The equality needs these assumptions:
* (a) V is independent of z beyond the front face. True for the continuum class, false for atoms.
* (b) dz -> 0. In the engine, dz = 1 -> 0.5 A changes max abs(dR) by 6e-6 (4.48e-4 -> 4.42e-4,
  E7 out §9).
* (c) No aliasing of the quasi-energy: 2 pi/dz = 6.3 rad/A is far above E ~ K^2/2k = 0.03 rad/A.
* (d) The same K on both sides: launch frequency f, read-out bin +f, and division by P_L(f) of the
  same propagator.
* (e) A slice-constant potential, so the transmission exp(i sigma V dz) is exact per slice.
* The x discretisation (dx, the 2/3 band limit, the partial surface pixel) is a separate error and
  depends on the pixel position (M1, M2).
* Other generators that are functions of d^2/dx^2 + 2 k sigma V share these states. The engine's
  "exact" propagator with an additive sigma V does not.

The "exact" propagator:
* Uniform medium: the exact propagator plus the transmission gives q^2 = k^2 - (k_z - sigma V)^2.
  The paraxial problem gives q^2 = K^2 + 2 k sigma V.
* They are equal for dV0 = V0 (k_z/k - 1) - sigma V0^2/(2k): -2.0531, -2.0908 and -2.1285 mV at
  eta = -0.9, 0 and 0.9 (E7 out §6).
* P2's first-order form, [N(q_in) - N(K)]/sigma = -2.0911 mV, differs by 3e-7 V (order theta^4).
* Effect on arg R: -5.117e-3, -2.018e-3 and -4.206e-3 rad. Plateau shift +0.3770 urad.
* CONFIRMED: "V0 - 2.09 mV, -2.0e-3 rad".
* In the engine, the pair criterion (b) (r = 0.1, abs(eta) <= 0.9) gives: measured [-1.181e-3,
  -9.81e-4] rad, predicted [-1.199e-3, -1.032e-3]; max deviation 5.1e-5 rad against P2's 2e-4
  (E7 out §9).

Rung 1 (M2 section 2):
* Predicted exact-minus-Fresnel |r|, from the exact dispersion of both schemes: -0.0052, -0.0137
  and -0.0450 % at 10, 16.47 and 30 mrad (V0 = 12 V).
* M2 measured -0.005, -0.013 and -0.045 %. These are differences of 3-decimal printed numbers
  (+-0.001 %), so they agree within that resolution.

(e V)^2 term: dU0 = 5.0191e-5 rad^2/A^2 (9.886e-6 of U_0), i.e. V0 + 0.1374 mV, and arg R changes
by +1.326e-4 rad at the centre. CONFIRMED.

### 3.5 Build-up (question 5)

The closed form, derived again:
* From int_0^inf J1(t)/t e^{-st} dt = sqrt(s^2 + 1) - s with s = -i eta:
  R_D(E) = i ph int_0^inf J1(kc tau)/tau e^{i (E - E_B) tau} dtau.
* So h(tau) = i ph J1(kc tau)/tau e^{-i E_B tau} and A_D(Z) = int_0^Z h(tau) e^{i E_K tau} dtau.
* E = K^2/2k, kc = sigma V_g (1 + i r), E_K - E_B = eta kc(r = 0) + i r sigma V0.
* This matches P2 5.2 and H2 2.3 (the same Green's function).
* My integral is a cumulative Simpson rule with 5 A steps, 20 A grid for the lengths (E7 out §7).

Build-up lengths, sharp edge (E7 out §7; each cell gives abs 1e-2 / abs 1e-3 / phase 1e-2 rad):

| r | eta | length (A) | P2 |
|---|---|---|---|
| 0 | 0 | 22 580 / 113 560 / 0 | same |
| 0 | +-0.5 | 26 900 / 134 660 / 23 220 | same |
| 0 | 0.9 | 68 800 / 342 680 / 65 220 | same |
| 0.05 | -0.5 to 0.9 | 3480-3860 / 7100-7540 / 2900-4480 | same |
| 0.1 | -0.5 to 0.9 | 2560-2600 / 3720-3920 / 1960-3320 | same |

* The asymptote gives Z(1e-2) = 24 551 A and Z(1e-3) = 113 957 A at eta = 0.
* The orchestrator's 2.3 um, 11 um, 34 um, 0.71 um and 0.38 um are these lengths rounded:
  22 580 A, 113 560 A, 342 680 A, 7100-7120 A and 3760 A. CONFIRMED.
* Exact transient with a smooth edge (w = 400 A, my pole-subtracted contour integral of the exact
  R(E); E7 out §7):
  * r = 0: 0.327, 5.22e-2, 1.97e-2, 4.66e-3 and 1.65e-3 at Z = 1953 to 32031 A.
  * r = 0.1: 2.80e-2, 5.20e-4, 6.06e-6 and 1.46e-9.
  * Both = P2 5.4.

Comparison with H2 and H7:

| r | 1D two-beam, absolute (P2, E7) | 1D two-beam, relative (H2 2.3; E7) | engine, atomistic [100] (H2 2.4; H5; H7 output) |
|---|---|---|---|
| 0.1 | 2580 A (1e-2), 3760 A (1e-3), phase 1960 A | 3194 / 4290 A (E7: 3200 / 4300) | static 3000 A (phase 1e-2 at 1500 A, amplitude 1e-2 at 3000 A); phonon 3500 A |
| 0.05 | 3480 / 7120 A, phase 2900 A | 3721 / 7538 A (E7: 3720 / 7540) | 5000 A |
| 0 | 22 580 / 113 560 A (68 800 / 342 680 A at eta = 0.9) | 22 572 / 113 552 A | 9000 A, relative to a reference window inside the same 11 251 A strip |

Why they differ:
1. Criterion. P2 uses abs(A - R); H2 2.3 uses abs(A/R - 1), larger by 1/abs(R) = 1.87 (r = 0.05)
   and 3.0 (r = 0.1). The engine run-ins require phase 1e-2 rad AND relative amplitude 1e-2, per
   500 A bin, against the strip's own plateau window (H5 M2; H7).
2. Leading edge versus steady state. All three are leading-edge transients towards a steady state.
   The engine strips have 2 A sin^2 edges (124 A along z), a negligible smoothing.
3. Physics. The atomistic [100] (0,0,8) condition is four-beam (H2 2.2). The specular channel loses
   intensity to in-plane beams: plateau abs(R) is 0.271, 0.457 and 0.891 in the engine against
   0.338, 0.535 and 1.000 in 1D. This extra loss damps the transient, which is why the r = 0 engine
   strip settles relative to its own window after 9000 A while the lossless 1D transient decays
   only as (kc Z)^(-3/2). At r = 0.05 the engine needs longer (5000 A) than the 1D phase criterion
   (2900-4480 A) because of a many-beam overshoot (-0.027 rad around 3000-4000 A, H2 2.4).

Conclusion:
* For R2-A, a 1D continuum test, the 1D numbers are the right ones.
* For the atomistic sizing, H7's engine run-ins (3000, 3500, 5000 and 9000 A) are the right ones.
  The 1D lengths must not replace them. The r = 0 engine value (9000 A) is a lower bound relative to
  its own window (H5 m4).

### 3.6 The proposed engine test R2-A (question 6)

The engine was run with my stand-in class to P2 8.1 (E7 out §9). The class is point-sampled
harmonic times f_j from `ContinuumTerracePotential.fill`, with (1 + i r) and the front-face overlap.
Common settings: dz = 1 A, dx exact, band "2/3", complex128, numpy, 1 thread, 5 to 34 s per run.

| run | r | propagator | dx (A) | x_s pixel | Z_e (A) | max abs(dR), abs(eta) <= 3 | vs T_A = 1.5e-3 |
|---|---|---|---|---|---|---|---|
| F | 0.1 | Fresnel | 0.025 | centre | 5000 | 4.48e-4 | pass (3.3x) |
| X | 0.1 | exact (vs one-way model) | 0.025 | centre | 5000 | 4.63e-4 | pass |
| F_dz05 (dz 0.5 A) | 0.1 | Fresnel | 0.025 | centre | 5000 | 4.42e-4 | pass |
| F_xs_q | 0.1 | Fresnel | 0.025 | quarter | 5000 | 3.31e-4 | pass |
| F_xs_edge | 0.1 | Fresnel | 0.025 | boundary | 5000 | 2.79e-4 | pass |
| F_dx0125 | 0.1 | Fresnel | 0.0125 | centre | 5000 | 2.20e-4 | pass |
| F_dx05 | 0.1 | Fresnel | 0.05 | centre | 5000 | 1.44e-3 | (order run) |
| F_Ze10k | 0.1 | Fresnel | 0.025 | centre | 10000 | 3.52e-4 | pass |
| F_r005 | 0.05 | Fresnel | 0.025 | centre | 10000 | 5.14e-4 | pass (2.9x) |
| F_r005_dx0125 | 0.05 | Fresnel | 0.0125 | centre | 10000 | 2.44e-4 | pass |
| F_r005_Ze20k | 0.05 | Fresnel | 0.025 | centre | 20000 | 4.19e-4 | pass |
| WRONG: cell-averaged harmonic | 0.1 | Fresnel | 0.025 | centre | 5000 | 8.83e-4 | passes (not caught) |
| WRONG: V0 + 5 mV | 0.1 | Fresnel | 0.025 | centre | 5000 | 8.21e-4 | passes (not caught) |
| WRONG: V0 + 5 mV | 0.05 | Fresnel | 0.025 | centre | 10000 | 1.94e-3 | FAILS (caught) |

Budget and tolerance:
* T_A = 1.5e-3 is justified: a correct implementation stays at or below 5.1e-4 on the specified
  grid.
* The budget itself is misstated for r = 0.05 (M2).
* Criterion (b) is sound: 5.1e-5 against 2e-4.
* Criterion (c) is not sound as written (M1).

Cell length:
* The finite cell contributes about 1e-4, a fifth of the residual (m3). The exact transient at the
  exit distance is at most 2.2e-4 (r = 0.1) and 2.3e-4 (r = 0.05).
* Both Z_e are long enough for T_A.

dx and dz:
* Both are adequate: 0.025 A gives 2.8e-4 to 5.1e-4, and dz = 1 A contributes about 6e-6.
* A 2x coarser grid (dx 0.05 A) reaches T_A: 1.44e-3 at r = 0.1 (just below it) and 1.64e-3 at
  r = 0.05 (above it). The tolerance is therefore loose relative to the discretisation error; the
  dx = 0.0125 A variant with T_A = 6e-4 has 2.5x margin (2.44e-4, 2.20e-4).

Passing for the wrong reason:
* Read-out region. The whole-box FFT includes the crystal. Its field at the exit plane is part of
  the about 1e-4 finite-cell term and cannot hide a phase-origin error (0.001 A gives 3.1e-3 and
  5.0e-3).
* Absorbers. The bulk absorber's term is at most 1.8e-6 (r = 0.1, D = 100 A) and 3.3e-5 (r = 0.05,
  D = 150 A). The top absorber is not reached (vacuum 282.7 A and more, against 130.7 A needed by
  the engine's rule).
* Bookkeeping errors are caught: absorption missing on the harmonic (2.1e-2 to 2.7e-2), a cosine
  origin or reference plane off by dx/2 (3.9e-2 to 6.2e-2, or about 0.1 rad).
* Errors that are NOT caught: a V0 error below about 4 mV (m1), a relative sigma error of 1e-4
  (2.7e-4 and 6.0e-4), and a cell-averaged harmonic (8.8e-4 in the engine). These are small
  systematic errors, not failures of the solver. R2-A cannot see common-mode errors of the inputs
  (sigma, V0, V_g), which the reference shares by design. My sigma = 7.288401041e-4 rad/(V A) was
  derived here from the SI constants and equals the engine's.

### 3.7 The absorber at r = 0 and the clean depth (question 7)

Reproduced with my own transfer matrices, including P2 6.5's table in full (E7 out §8):
* r = 0, eta = -1.5: abs(R_cell - R_inf) = 0.38 (D = 60 A), 0.30 (100 A), 0.34 (150 A) and 0.32
  (250 A).
* r = 0, eta = +-3: 0.15 to 0.16 at every D.
* Inside the plateau, at eta = 0: 1.1e-2, 4.4e-4, 7.4e-6 and 2.1e-9 for D = 60, 100, 150 and 250 A.
* V_g = 0: 1.1e-4.
* Longer, weaker ramps (r = 0, D = 150 A): 400 A at 20 V gives 0.104 and 0.094, 800 A at 20 V gives
  0.0195 and 0.0179 (eta = -+1.5).
* With absorption: at most 3.3e-5 (r = 0.05, 150 A) and at most 1.8e-6 (r = 0.1, 100 A).
* The null-test predictions (21 A: -8.1e-3, -9.5e-3 and -6.0e-3 rad; abs(B/A) 1.066, 1.032 and
  1.013) are reproduced.

Clean depth, which criterion and which depth: see M3.
* R2-A keeps 100 and 150 A.
* R2-B keeps 250 A. R2-B was not rerun by me.
* The atomistic sizing keeps H7's 55 A (r = 0.1) and 65 A (r = 0.05) at [100].
* The null-study redesign uses at least 65 A (H2's [110] depth), together with r >= 0.05 and the
  engine run-ins.
* No depth fixes r = 0 outside the plateau.

## 4. Verdict table

| # | P2 claim | Verdict |
|---|---|---|
| 1 | exact R(theta) at x_s; plateau edges 15.94648 and 16.32008 mrad; arg R 1.708 rad at the centre; rocking table for r = 0, 0.05, 0.1; conventions | CONFIRMED by three independent solvers and by the unmodified engine without any fitted phase |
| 2 | V0 = 13.902843 V, V_008 = 1.035742 V from the engine's potential | CONFIRMED by an exact DFT of the engine-realised potential (13.9028426 and 1.0357425 V); the dx = 0.01 A fit column is 5e-6 V low (n1) |
| 3 | R = (r_F + R_D)/(1 + r_F R_D); 5.7e-3 (r = 0) and 1.0e-3 (r = 0.05); 0.135 rad | Form and deviations CONFIRMED; the Darwin error at the centre is 0.137 rad (m2) |
| 4 | Fresnel scheme: stationary R(K) exact; exact propagator = V0 - 2.09 mV, -2.0e-3 rad; M2 rung-1 differences | CONFIRMED, with the assumptions of 3.4; criterion (b) holds in the engine (5.1e-5 rad) |
| 5 | build-up closed form and lengths (2.3, 11, 34 um; 0.71, 0.38 um) | CONFIRMED; the differences to H2 and H7 are explained by criterion and physics (3.5) |
| 6a | R2-A tolerance T_A = 1.5e-3 | VALID: a correct engine gives 2.8e-4 to 5.1e-4 |
| 6b | budget 4.5e-4 and 3.2e-4, "3.3x and 4.7x" | WRONG for r = 0.05 on the specified grid: 5.1e-4, 2.9x (M2) |
| 6c | criterion (b), 2e-4 rad | VALID (engine 5.1e-5) |
| 6d | criterion (c), order >= 1.5 | NOT SOUND: fails a correct engine off pixel centres (M1) |
| 6e | cell length, dx 0.025 A, dz 1 A | ADEQUATE; the finite cell contributes about 1e-4 (m3) |
| 6f | "tests the effective potential at the mV level" | OVERSTATED: about 4 mV (m1) |
| 7a | the 15 A absorber reflects strongly at r = 0 (0.15-0.38) | CONFIRMED (every entry of P2 6.5) |
| 7b | ">= 100 A clean depth for atomistic null tests" | CONFLICTS with H2/H7's 55-65 A; not needed at the 1e-2 criteria; see the reconciliation in M3 |

## 5. Numbers CONFIRMED (recomputed with my own code, E7 out §n)

* §1: lambda = 0.0250793405 A, k = 250.5323184 rad/A, sigma = 7.288401041e-4 rad/(V A), and
  2 k sigma = 2 E_tot/(hbar c)^2 (P2 premise P2).
* §2: V0 = 13.902843 V, V_008 = 1.035742 V, V_004 = 2.740094, V_012 = 0.546702, V_016 = 0.326521,
  V_020 = 0.213647, V_024 = 0.150274 V (P2 6.1, 8 F/a^3 column); H2/H5 1.036 V; MIP 13.903 V.
* §3:
  * U_0 = 5.077263 and abs(U_g) = 0.378249 rad^2/A^2; G = 9.255461 rad/A; d = 0.678863 A.
  * K_c = 4.042107 rad/A; 16.13477 mrad external and 18.47189 mrad internal.
  * Two-beam edges 15.94690 to 16.32049 mrad (373.59 urad).
  * Exact edges 15.94648 to 16.32008 mrad (373.595 urad), midpoint 16.13328 mrad, shifts -0.416
    and -0.409 urad.
  * Full layer gap 15.98286 to 16.31535 mrad (332.492 urad, -11.0 %, +15.83 urad).
  * 24.469 A; 1/kc = 1324.7 A; xi_g = 4161.7 A; 5.355 rad/mrad; 0.9655 rad/V.
* §4:
  * Every "ex" entry of P2 6.3.
  * arg R = 1.707976 rad (centre), 1.700074 rad (midpoint), sweep pi.
  * t = d/4: -3.13195 rad; t = d/2: -1.70360 rad.
  * Full layer potential: 1.67006 rad.
  * Peak values 0.54226 and 0.34697 (their positions: n3).
* §5:
  * r_F = -0.06755; 2 atan(abs(r_F)) = 0.13489 rad.
  * The complete P2 3.4 table: 7.93e-3, 5.73e-3, 0.138; 3.86e-3 (9.87e-3 rad), 1.04e-3 (2.01e-3
    rad), 8.78e-2 (0.180 rad); 2.94e-3 (1.80e-2 rad), 4.96e-4 (1.49e-3 rad), 7.60e-2 (0.348 rad).
  * The centre phases 1.5708, 1.7013, 1.7057 and 1.7080 rad.
* §6:
  * dV0 = -2.05 to -2.13 mV (-2.09 mV at the centre).
  * arg R changes -5.117e-3, -2.018e-3, -4.206e-3 rad; plateau shift +0.377 urad.
  * Rung 1: -0.0052, -0.0137, -0.0450 %.
  * (e V)^2: 9.886e-6 of U_0 and 1.33e-4 rad.
* §7:
  * Z_a = 2133 and 1066 A (fast components 1837 and 918 A).
  * All two-beam build-up lengths of P2 5.3.
  * The asymptote 24 551 and 113 957 A.
  * H2's relative lengths to the 20 A grid.
  * P2 5.4's exact-transient table.
* §8:
  * All of P2 6.5's absorber table, the V_g = 0 value (1.1e-4) and the two long ramps.
  * The null-test predictions at 21, 60 and 100 A (55 and 65 A added).
* §9 and §10:
  * P2's split step equals the engine's scheme (to 7.6e-14 on identical grids).
  * Criterion (b) holds in the engine.
  * The one-way reference model, the two-beam forms, the engine-geometry cell and the build-up
    lengths of the P2 tool agree with mine to 1e-6 or better. The exception is the one-way model at
    the two r = 0 angles that lie within 0.05 urad of the shifted band edges (0.11 there), which is
    irrelevant to R2-A.

## 6. Is R2-A as proposed a valid test?

Yes, with two corrections before it is used as the pass/fail record of rung 2:
1. M1: fix x_s on a pixel centre of every grid (it already is in P2's and E1's geometry), and
   replace criterion (c) by the per-bin guard, or lower it to order >= 1.
2. M2: correct the budget for r = 0.05 (5.1e-4, margin 2.9x).

What the test establishes:
* Criterion (a) with T_A = 1.5e-3 and criterion (b) are correct. A correct engine passes (a) with
  margin at both absorptions and every surface pixel position tested.
* It fails an engine with a wrong phase origin, reference plane or absorption model, or with a V0
  error of about 4 mV or more.
* It cannot fail an engine for errors below about 4 mV in V0 or 1e-4 in sigma, or for a
  cell-averaged harmonic.

Its limits must be stated:
* It validates the solver (propagation, refraction at the mean-potential step, coupling, phase
  origin, read-out, absorbers at r > 0).
* It does not validate the potential values, the atomistic many-beam physics, or r = 0.
* The phrase "at the mV level" should go (m1).

## 7. Reproducibility and limits of this review

* Saved run: `venv/bin/python -u tools/review/e7_recompute.py` (2026-09-24; wall 7 min 59 s,
  single-threaded BLAS and FFT, shared 4-core machine), 25 self-checks, 0 failed. The output is in
  `tools/review/e7_recompute_output.txt`.
* Engine state for the §2, §9 and §10 runs: the working tree on top of snapshot 3e99722. Other
  agents had uncommitted edits in engine.py, illumination.py and potentials.py (y-tilt and E1's
  class), not used by my stand-in. First 16 hex of sha256, identical before and after the saved runs:

  | file | hash |
  |---|---|
  | engine.py | 9fa0e15faf45e994 |
  | illumination.py | f569b65d032e0290 |
  | potentials.py | e67f98cce6f57b81 |
  | propagator.py | 1915ab10d1aac9e8 |
  | analysis.py | 8dc6e4f37a6aa31e |
  | grid.py | 9b2f3981f275ffcf |
  | physics.py | 1bd9568746131b12 |
  | backend.py | 453d3c889a518e69 |
  | forward/cell.py | ab284f5128f77fa1 |

* Not verified by me:
  * R2-B (r = 0, 30 000 A cells) was not rerun.
  * E1's ContinuumPeriodicPotential was not run. My stand-in follows P2 8.1 as written. E1's class
    must reproduce it (a bit-level check, stand-in against class, is a cheap first step for E1).
  * The 1D model's relevance to atomistic cells is only as far as H2 2.4's engine profiles allow
    (3.5, M3).
  * The Kirkland parameterisation itself remains UNVERIFIED (SM17). I read its data file only.
* Evidence labels in P2 are used correctly: SECTION_READ only for sections read, per its log; no
  REPRODUCED label claimed. The only issue is the unsourced names (n4).

Status: FINAL (2026-09-24). No BLOCKER; MAJOR M1, M2, M3; MINOR m1-m4; NIT n1-n4.
