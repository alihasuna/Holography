# E8: adversarial review of S5 (independent dynamical RHEED solver against the multislice engine)

Agent E8, 2026-09-24. Written incrementally; the final state is sections 8 to 12. Branch
`claude/electron-holography-orchestration-nakd7r`; S5's work reviewed at commit `872e949`. Nothing
committed or pushed by E8; no GPL-3.0 code or input copied into the repository.

Documents under review: `docs/agent_reports/S5_independent_rheed_solver.md` (the S5 report),
`tools/validation/rheed_solver_compare.py` (the S5 tool), `tools/validation/rheed_solver_results.json`,
`tools/validation/rheed_engine_results.json`; the solver sources, builds, runs and patch in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/rheed_solver/`
(upstream sim-trhepd-rheed `d98d6252`, P49 fork trhepd-opt `dc394ba`).

Method: every number below is printed by `tools/review/e8_recompute.py` (saved run
`tools/review/e8_recompute_output.txt`, section numbers "E8-n" below refer to its sections). The script
was written WITHOUT reading the S5 tool's implementation of the recomputed quantities (reflection
coefficient at the reference plane, one-beam reference, engine read-out, tolerance test, peak and
phase-sweep analysis, plane fit); it reads only the raw solver output files (`amp.txt`, the Fortran
inputs) and the stored engine exit columns. The S5 tool was read afterwards, only to locate the source
of a discrepancy, and its report mode was re-run as a black box.

Evidence labels as in the S5 report: SECTION_READ, REPRODUCED (executed here, saved output),
DERIVED_HERE, ASSUMPTION, UNVERIFIED, MEASURED_HERE (a number from the UNVALIDATED engine).

## 0. Log

- 01:00 UTC: read the S5 report (all), the patch, the upstream Fortran listed in S5 F1-F17, the
  P49 fork's `matcomp.f90`, `surf_rk.f90`, `surflf.f90`, `surfio.f90` (head); docs/05 4.4; L2 rows
  D1-D20, D-I1 to D-I4; the engine (`engine.py`, `potentials.py`, `analysis.py`, `illumination.py`,
  `propagator.py`, `grid.py`), H2's `flat_strip`; E1 Task 1 (rung 2 R2-A results).
- 01:05-01:17 UTC: script sections E8-1 to E8-7 written and run (provenance, own transfer-matrix
  convention check, R at the top-layer nuclei from `amp.txt`, own engine read-out of the stored
  columns, plane fit and tolerance power, curve level, engine-version history).
- 01:19-01:32 UTC: own engine runs at 16.2 mrad with the engine archived from commit `d3de34a`
  (a `git archive` in scratch, so that other agents' uncommitted edits cannot enter), 2 FFT threads,
  peak RSS 324 to 345 MB (E8-10); the S5 tool's report mode re-run as a black box (E8-12).
- 01:32-02:00 UTC: along-beam-averaged and full engine runs at six more angles and [110] (E8-10b);
  rung-2 continuum runs at four pixels (E8-11); final run of the whole script (all engine results
  read from the scratch cache `.../scratchpad/e8/engine_cache/`), saved as
  `tools/review/e8_recompute_output.txt` (10 of 10 self-checks pass).

## 1. Provenance, patch, physics inputs (question 1)

* Patch (REPRODUCED, E8-1): `build_E/src_orig` is byte-identical to upstream `src/` at `d98d6252`
  (35 of 35 files; clean clone). The patched tree differs in 5 files by exactly 3 removed lines (all
  `ep='P'`) and 6 added lines (3 `ep='E'`, one `open (8,file='amp.txt')`, two `write (8,...)`). No
  computational line is touched. The `U0.f90` switch is inert for this study (U0 belongs to the
  separate `potcalc` program; the Makefile's BULK and SURF lists do not contain it). The electron
  switch acts through `bulkm.f90` (`inegpos=0`), which bulk.exe writes into the binary that surf.exe
  reads (`surfio.f90`: `read (1) inegpos,...`); surf's own `ep` only selects the file name
  `bulkE.b`; the positron sign flip is applied only after the last `scpot` call and only for
  `negpos > 0`. Executable SHA-256 values equal the JSON record. S5's description (section 2.2) is
  correct.
* Relativity (E8-1b): solver `K` = 250.531079 rad/A against the engine's 250.532318 (relative
  -4.945e-06), gamma 1.39138867 against 1.39139024 (-1.128e-06); the solver's `2 m e/hbar^2` =
  0.262466 against CODATA 0.262468 (-9.24e-06). The solver's potential is `U = gamma 4 pi f_e/Omega`,
  the same relativistic scaling as the engine's `2 k sigma V`. These constant differences move the
  (0,0,8) peak by at most 8.0e-05 mrad. S5 is correct.
* Doyle-Turner table (E8-1c): the solver's Si row is `asf.f90:229` (a) and `:329` (b), row 14 of the
  `ad`/`bd` data statements; f_e(0) = 5.81910 A and the DT mean inner potential 13.9144 V agree with
  S5. The comparison of these numbers with the published table remains UNVERIFIED (as S5 says).
  The years "Doyle-Turner (1968)" and "Peng (1999)" in S5 F11 come from the code comment
  (`asf.f90:3-4`), not from the literature reports or `docs/references.bib` (finding m6).
* Absorption, like-for-like (SECTION_READ `scpot.f90:145-151`, engine `potentials.py`): `sap > 0`
  gives `vi = i sap v` for every Fourier component including the structure factor, i.e. the complex
  potential `U (1 + i sap)`; the engine's `PhysicalAbsorption("proportional", r)` gives
  `V_p (1 + i r)` for the projected slice potential. With a static lattice both are the same model
  applied to the same real potential, so the ABSORPTION MODEL is like-for-like. What is not
  like-for-like is the set of Fourier components that carry it (finding M1): the solver keeps all
  normal-direction components of 13 (19) in-plane rods but no along-beam variation; the engine keeps
  the along-beam variation (slices a/4) but only the components inside its circular (f_x, f_y) band.
* The bulk unit a/2 (question 1, E8-3): the CC = a input is legitimate (four layers, no shift);
  bulk.exe multiplies all slice matrices of one unit before the unit recursion (`bulk.f90:82-98`),
  and the output is unphysical: max |R|^2 = 2.57 and a total reflected flux of 96.6. This is a
  numerical limitation of the unit-product algorithm, not an error in S5's input, and the a/2 unit
  with the (1/2, 1/2) shift is an exact description of the diamond (001) stacking (E8-3 shows the
  top-layer shift (-1/2, 0), i.e. back-bonds along [1,1,0], in every approach-A and approach-B case).
  S5's quantitative explanation is weaker than stated (finding m4): with CC = a/2 the evanescent
  growth across one unit is 1.1e+15 to 9.6e+15 at [100] and 1.3e+16 to 1.0e+17 at [110], i.e. at or
  above 1/eps = 4.5e+15, yet routes A and B agree to 2.18e-05 ([100]) and 1.26e-05 ([110]). The a/2
  requirement is therefore established EMPIRICALLY by the A-B agreement, not by the growth figure.

## 2. The convention (question 2)

* Own check (REPRODUCED, E8-2): the one-beam problem is re-solved with E8's own transfer matrices
  (exact 2x2 exponentials of piecewise-constant U_00, the potential built from the Fortran inputs,
  start at s = 0 with a pure downward vacuum wave, decomposition in the vacuum basis at s_top). The
  code is first validated against the closed-form Fresnel coefficient of an absorbing step
  (difference 3.0e-15, Im R < 0 as required for exp(-i omega t)). Results: with the solver's own
  slicing (dz = 0.009983 A, slice-centre potential) E8 reproduces `f(0,nb0)` to 7.42e-12 (r = 0.1)
  and 3.27e-11 (r = 0); in the continuum limit (h = 0.0005 A) the difference is 9.59e-05 and
  5.09e-04, while the conjugate differs by 0.376 and 1.707. At 16.0 mrad arg R(s_top) is +2.6930
  (solver) and +2.6931 (E8) for r = 0.1. S5's RK4 conclusion is confirmed by an independent method:
  upstream sim-trhepd-rheed's patched output is R = (upward)/(downward) at s_top in the repository's
  exp(+i k.r - i omega t) convention; no conjugation is needed.
* Why (SECTION_READ, `trmatg.f90:24-50`, `surf.f90:88-107`): the state between slices is the vacuum
  decomposition (Gamma psi - i psi', Gamma psi + i psi'); the vacuum slice matrix is
  diag(exp(+i Gamma dz), exp(-i Gamma dz)) with s towards the vacuum; the recursion starts with R = 0
  at the bottom (no exp(+i Gamma s) wave below the crystal) and `sap > 0` makes Im Gamma^2 > 0. Both
  facts are consistent only with exp(-i omega t). The one-beam test checks only the NORMAL direction;
  the lateral Fourier sign convention (U_g vs U_-g) is not tested by a flat bulk-terminated Si(001)
  surface at all: every atom of the solver's slab sits at fractional (0 or 1/2, 0 or 1/2), so the
  two-fold rotation about the normal maps every layer onto itself (E8-3), and R_00 is the same for a
  structure and its inverse (finding M4).
* The P49 fork (SECTION_READ of `trhepd-opt` at `dc394ba`; not run): the new integrators start from
  the same bulk reflection matrix, map it to (q, p) = (psi, psi')/Gamma with `invstrans`
  (`matcomp.f90`: q = G^-1 (I + f), p = i (f - I)), integrate psi'' = -(Gamma^2 + U + i U') psi
  (`vvi2matf`: m = -(v + vi) - g^2), and map back with `strans`, f = (Gamma q - i p)(Gamma q + i p)^-1,
  i.e. again (upward)/(downward). The `conjg` calls in `surf_rk.f90`/`surf_prkn.f90`/`matcomp.f90`
  belong to the Hermitian-transposed storage of the `*h` variants (`invstransh` stores
  conj(P Q^-1), and the final `f = conjg(transpose(...))` undoes it), not to a change of convention.
  The printed P49 formula, Eq. (36) as recorded by L2 D9, rho(0) = (Gamma + i P Q^-1)(Gamma -
  i P Q^-1)^-1 tau(0), is the opposite assignment: applied to the code's (Q, P) it gives
  (downward)/(upward), and for the physical exp(+i omega t) solution it gives conj(R) (E8-13 checks
  this algebra numerically). Hence: L2 D-I3 is right about the PAPER's notation; it does not apply
  to the output of either CODE.

## 3. Reference plane and phase origin (question 3)

* Solver side (E8-3, own geometry from the Fortran inputs): for every case the top-layer nuclei are
  the highest atom of the slice region, at s_a = 2.0366 A (approach A: the upper atom of the topmost
  bulk unit) or at the top of the slab (approach B); s_top - s_a = 4.6822 A (A) or 4.0033 A (B).
  E8's conversion R(s_a) = R(s_top) exp(-2 i Gamma_0 (s_top - s_a)), with Gamma_0 taken from the
  solver's own output, equals S5's stored `R_layer` to 5.9e-14 for all 36 cases. Above s_top the
  solver has no potential (the DT tails of the top layer are cut 4.0-4.7 A above the nuclei; the
  engine keeps them); E8-2 shows that the solver slices the potential exactly as E8's model of it,
  so this truncation is part of both the RK4 and the TM checks and of the solver curves.
* Engine side (E8-10): in E8's rerun the reference plane `highest_surface_x_A` = 70.000000 A equals
  the largest atom x in the cell (70.000000 A): the engine's R is also referred to the top-layer
  nuclei. The engine's phase origin is the launched sheet beam (`exp(-2 pi i f_c x)` with x = 0 at
  the box bottom, `illumination.py`), removed by exp(+4 pi i f_c x_s)/P_L. Lateral origins and the
  truncation along the beam do not enter R_00.
* The fit (E8-5): with d arg = c + 2 Gamma_0 dx over the 12 [100] angles with |R_sol| >= 0.1,
  c = -0.0440 +- 0.0970 rad and dx = +0.0052 +- 0.0122 A (1 sigma, correlation -0.997: over 12-16.8
  mrad 2 Gamma_0 varies only from 6.01 to 8.37 rad/A, so c and dx are nearly degenerate); [110]:
  c = +0.0831 +- 0.0677, dx = -0.0120 +- 0.0088 A. S5's "fitted reference-plane offset 0.005-0.012 A"
  therefore carries uncertainties as large as the values (finding m2). The meaningful statement is
  the one-parameter fit with no constant offset: dx = -0.0003 +- 0.0009 A ([100] DT),
  -0.0013 +- 0.0015 A ([110]), +0.0003 +- 0.0009 A ([100] Kirkland). A plane error cannot hide in c
  unless a constant phase offset of the opposite sign is also present; the physics differences
  between the codes act like such an offset (the along-beam couplings alone move the engine's arg R
  by -0.0008 to -0.0264 rad, E8-10), which is why the one-parameter fit, not S5's two-parameter fit,
  is the relevant check. A 0.1 A error would give 0.601 rad at 12 mrad and 1.102 rad at 22 mrad
  (E8-5, as S5).

## 4. Tolerances (question 4)

* Were they fixed before comparing? (E8-7b, from `git show` of every commit that changed the tool):
  the tolerance block (TOL_REL 0.05, TOL_ABS 0.005, TOL_SPREAD_MULT 2.0, peak 0.03 mrad, peak |R|^2
  10 %, FWHM 10 %, sweep 0.1 rad) is identical in `242b566` (22:52:30 UTC), `2a3a999`, `64d740b`,
  `2da0216`, `db81b59` and `872e949`. The earliest of these already contains an engine result (the
  results file is stamped 2026-09-23T22:47:50Z; 16.2 mrad, engine `a84b4b3`, E8-7). Git therefore shows that the tolerances never changed after the first
  engine number existed, but it cannot show that they were written before it: "declared at 22:45 UTC"
  rests on S5's own log (finding m1). The report section 5 text with "DECLARED at 22:45 UTC" is
  already present at `242b566`.
* What the per-angle criterion means: |R_eng - R_sol| <= 0.05 |R_sol| + 0.005 + 2 s_eng is a bound on
  the COMPLEX amplitude difference in units of |R| (reflection coefficient at the top-layer nuclei).
  At 16.2 mrad it allows 0.112 of |R_sol| (+0.24/-0.21 in |R|^2) or a pure phase error of 0.112 rad;
  at 21.0 mrad the tolerance is 0.00496 + 0.005 + 2 x 0.0013 = 0.0125 in E8's read-out (0.0132 in
  S5's), and the failing quantity (|dR| 0.0136) is dominated by the engine's |R| being 13.5 % low
  with d arg -0.018 rad. S5's "exceeds it by 0.0003" is in units of |R|; with E8's independent
  read-out the excess is 0.0011 (the conclusion, a failure at 21.0 mrad, is the same).
* Power (E8-5b, all alternatives through the same test with the engine's spreads): a conjugated
  engine fails at 19 of 23 angles; a reference plane moved by 0.010, 0.015, 0.020, 0.050 A fails at
  2, 5, 12, 19 angles; the one-rod (0,0) model fails at 22 of 23 (|R_1rod - R_13rods| = 0.067 to
  0.278 over 15.6-16.8 mrad): the phase test does have power against convention, plane and
  missing-many-beam errors. It has NO power against a uniform amplitude error of 10 %: the solver's
  own R scaled by 0.90 (|R|^2 -19 %) with exact phases passes at all 23 angles, and scaled by 0.95
  (|R|^2 -9.75 %) it would also pass the curve-level peak test (10 %). The amplitude tolerance is
  loose (finding M2).
* The spread term makes the tolerance depend on the engine's own non-convergence and on read-out
  details: E8's independent band-passed read-out reproduces S5's stored R to 1.4e-03 ([100]),
  1.8e-03 ([110]), but the spreads differ by up to 6.0e-03 ([100]) and 8.1e-03 ([110]) (e.g. 12.0
  mrad: 0.0063 in E8's read-out against 0.0124 stored), which changes the tolerance by up to about 30 %
  (finding m3). The pass counts do not change (22/23 and 15/15).

## 5. Engine version during S5's runs (question 6)

* Recorded commits (E8-7): the 38 main DT runs ([100] 23, [110] 15) at `148e4f6` with a dirty tree;
  the variants bin 250 A, dz/2 and pixel 0.10 A at `2a3a999` (dirty); complex128, pixel 0.075 A and
  clean depth 80 A at `64d740b`; 7000 A at `2da0216`; the 15 Kirkland runs at `a1ef2a0`; the first,
  discarded pass at `a84b4b3`.
* Numerics (E8-7, `ast` source extraction at every one of those commits): `propagate_slices`,
  `run_realisation`, `_RealisedAtomic`, `absorber_profile_V`, `propagator_phase`,
  `propagator_kernel`, `sheet_beam_wave`, `SheetBeam`, `band_limit_mask`, `make_grid`,
  `beam_constants` and `build_reflection_cell` are textually identical at `a84b4b3`, `148e4f6`,
  `2a3a999`, `64d740b`, `2da0216` and `a1ef2a0`; `reflection_holo/structure` is unchanged between
  `a84b4b3` and `a1ef2a0` (E8-7). The dirty state of `148e4f6` cannot be reconstructed from git, but the
  16.2 mrad exit column of the main run and of the `2a3a999` repeat are identical element by element,
  and the discarded first pass (`a84b4b3`) gave the same r_top to all 17 digits. In the S5 tool
  (E8-7b) `DoyleTurnerPotential` never changed; `engine_readout` changed between `242b566` and
  `2a3a999`, but the final tool reproduces every stored read-out from the stored columns to 6e-09
  (its self-check, reproduced in E8-12); `engine_flat_strip` changed at `64d740b` (it gained `dz_div`
  and the `working_reflections_hkl` argument; SECTION_READ of the diff), which does not change a
  default run. S5's claim of consistent numerics is CONFIRMED.
* After S5 (not S5's responsibility, but relevant for quoting): at `d3de34a` (the HEAD E8 archived
  for its runs) the engine's `run_realisation`, `reflection_setup`, `_RealisedAtomic` (exponentials
  moved into the new `_phase_factors`), `sheet_beam_wave` (azimuthal tilt) and
  `build_si001_terraces` differ from `a1ef2a0`, while `propagate_slices`, `AtomicPotential`,
  `absorber_profile_V`, `propagator_kernel` and `band_limit_mask` do not (E8-7). E8's regression run with a `git archive` of HEAD reproduces S5's stored 16.2 mrad column
  (section 7, E8-10), so for this configuration the later changes are numerically inert.

## 6. What the comparison cannot show; what a like-for-like validation needs (question 7)

S5's lists (section 9) are right in what they contain, with one error and several gaps:

* Error (finding M1): "Both omit the same physics: HOLZ couplings" (S5 9, and "common omission" in
  S5 7) contradicts S5 5 ("the ZOLZ-row solver omits HOLZ couplings that the engine partly
  carries"), and the latter is right. The forward multislice resolves the potential ALONG the beam
  with slices a/4 (dz halving changed R by 1e-4, S5 6.5), so the engine contains the along-beam
  (higher-Laue-zone) couplings, while the solver's row (h,-h) is the potential averaged along the
  beam. The solver's own 61-rod disk test gives |R_disk|/|R_row| - 1 = -0.0123, -0.0109, -0.0089
  (12.0, 16.2, 21.0 mrad) and d arg -0.0167, -0.0086, -0.0145 rad: the same sign and about a third of
  the engine-solver differences. The comparison is therefore not like-for-like in this dimension,
  and E8's along-beam-averaged engine runs (section 7) measure how much of the deficit it explains.
* Missing from "cannot show":
  1. the LATERAL Fourier sign convention (a flat bulk-terminated Si(001) is invariant under the
     two-fold rotation about the normal, so U_g and U_-g give the same R_00; finding M4);
  2. the engine's circular (f_x, f_y) band against the solver's full normal structure per rod: at
     0.1293 A only rods |h| <= 5 carry the (0,0,8) normal component (E8-10), so the outer rods of
     the "matched" 13-rod set are not matched;
  3. only the specular rod, only 12-22 mrad, only [100] and [110], only one absorption ratio
     (0.1), a static lattice and one parameterisation per code; no other Bragg condition and not
     the larger glancing angles listed among docs/05's open questions;
  4. the engine's result is for a 4500 A strip read over departure points 2500-3751 A with a sheet
     beam whose top edge ends the window; the incident amplitude there is quantified in E8-9;
  5. the validated engine state is the atomic path of `148e4f6`-`a1ef2a0` (and, by E8's regression
     at 16.2 mrad, HEAD `d3de34a`); any later change to the slice loop, potential or sheet beam needs
     the regression point re-run.
* Missing from "needed for like-for-like": an engine run with the along-beam-averaged potential
  (or a solver rod disk matched to the engine's slice and band sampling), and a pixel at which the
  engine's band contains every (rod, normal-component) pair the solver carries.

## 7. The engine's amplitude deficit and its pixel dependence (question 5): explained

E8 re-ran the 16.2 mrad [100] point (DT, r = 0.1, static, 4500 A strip, S5's geometry recipe, E8's
own driver and read-out) with the engine archived from HEAD `d3de34a`, at four pixels, once with the
engine's normal potential ("full") and once with every crystal slice replaced by the mean of the
four slices of one along-beam period ("along-beam averaged": the potential projected along the
beam, i.e. exactly the physics of the solver's zero-order row of rods). E8-10:

* Regression: E8's default run reproduces S5's stored exit column to 6.9e-08 (column maximum 0.577;
  the column is stored with 7 significant digits); same grid 1764 x 42 x 3406 and 88296 atoms.
* Solver at 16.2 mrad: 13 rods |R|^2 0.07881, arg -2.7120; 17 rods 0.07902, -2.7066; 21 rods
  0.07908, -2.7053 (E8-10).

| pixel (A) | full: |R|/|R_21rods| - 1 | full: d arg (rad) | averaged: |R|/|R_21rods| - 1 | averaged: d arg (rad) |
|---|---|---|---|---|
| 0.1293 | -0.0465 | -0.0276 | -0.0252 | -0.0268 |
| 0.0990 | -0.0218 | -0.0231 | -0.0046 | -0.0058 |
| 0.0742 | -0.0316 | -0.0288 | +0.0013 | -0.0023 |
| 0.0646 | -0.0324 | -0.0228 | +0.0020 | -0.0022 |

Reading (DERIVED_HERE from these MEASURED_HERE runs):

1. With the solver's physics (along-beam average) the engine CONVERGES to the solver, monotonically
   in the pixel: |R| within +0.2 % and arg R within 0.002 rad at 0.0742 and 0.0646 A. At the
   production pixel 0.13 A it is 2.5 % low in |R| and 0.027 rad low in phase: this is the band limit
   (the engine's circular (f_x, f_y) band cuts normal-direction Fourier components of the outer
   rods and the (0,0,l >= 16) row, H2 section 5), and it is removed by refining the pixel.
2. The along-beam couplings, which the engine contains and the solver's row does not
   (|R_full|/|R_averaged| - 1 at the same pixel: -0.0219, -0.0173, -0.0329, -0.0344 at 0.1293,
   0.0990, 0.0742, 0.0646 A; phase -0.0008, -0.0172, -0.0264, -0.0206 rad), reach their full size
   once the first along-beam (Laue) ring, at 3.881 1/A for 16.2 mrad, lies inside the band (band
   radius 2.579, 3.368, 4.491, 5.158 1/A at the four pixels): -3.3 to -3.4 % in |R| and -0.021 to
   -0.026 rad (ratios -0.0329 and -0.0344 at the two finest pixels). At 0.0990 A the ring is still
   outside and only part of the effect appears; this is why S5's pixel study was not monotonic
   (|R|^2 +5.2 % at 0.099 A, then down at 0.074 A), while the averaged runs are monotonic.
3. S5's "unexplained about 3 % in |R|" is therefore the sum of a numerical engine error at 0.13 A
   (band limit, 2.5 % in |R| and 0.027 rad in the averaged runs) and a physics difference between
   the two models (along-beam couplings, 2.2 % at 0.13 A, 3.4 % converged), not an unexplained engine
   defect. S5's residual phase offset (-0.02 to -0.03 rad) has the same two sources. The peak shift
   has them too: from the parabola through 16.0/16.2/16.4 mrad the averaged engine at 0.075 A peaks
   +0.0028 mrad from the solver (same method), S5's full engine at 0.13 A +0.0150 mrad (E8-10b). The
   strip is long enough for the averaged physics: 7000 A against 4500 A changes |R| by +0.06 % and
   arg R by -0.0014 rad (0.0990 A).
4. The size of the along-beam effect is NOT validated: the engine's converged value (-3.4 % in |R|,
   -0.021 rad) is about three times the solver's 61-rod disk estimate (-1.1 %, -0.009 rad), whose
   disk is truncated at |g| <= 6/a with the row at |h| <= 3. Which is right needs a solver rod disk
   matched to (or larger than) the engine's along-beam and transverse sampling (findings M1, M3).
5. The candidates S5 lists (band limit, infinite projection per slice, band-pass near the surface)
   are thereby narrowed: the band limit is confirmed; the infinite projection per slice and the
   read-out cannot be large, because the averaged runs agree with the solver to 0.2 % at 16.2 mrad
   and to 1.1 % at every angle checked. At the production pixel only rods |h| <= 5 carry the (0,0,8)
   normal component (8/a = 1.4731 1/A) and the y band edge 2.577842 1/A coincides with the (7,-7)
   rod (E8-10).

The same holds at the other angles and at [110] (E8-10b; averaged potential and full engine at the
pixel 0.075 A, against the solver case S5 compared with, 13 rods at [100] and 19 at [110]):

| azimuth, theta (mrad) | averaged: |R|/|R_sol| - 1 | averaged: d arg (rad) | averaged: abs(dR) | full: |R|/|R_sol| - 1 | full: d arg (rad) |
|---|---|---|---|---|---|
| [100] 12.0 | -0.0064 | +0.0107 | 0.0027 | -0.0502 | -0.0143 |
| [100] 15.8 | +0.0088 | +0.0208 | 0.0039 | -0.0502 | -0.0072 |
| [100] 16.0 | -0.0080 | +0.0048 | 0.0024 | | |
| [100] 16.4 | -0.0099 | -0.0061 | 0.0027 | | |
| [100] 21.0 | -0.0046 | +0.0041 | 0.0006 | -0.0453 | -0.0163 |
| [110] 15.1 | +0.0063 | +0.0126 | 0.0032 | -0.0124 | -0.0115 |
| [110] 17.6 | -0.0112 | +0.0056 | 0.0026 | -0.0265 | -0.0359 |

With the solver's physics the engine agrees at every angle within 1.1 % in |R| and 0.021 rad
(largest abs(dR) 0.0039, against S5's 0.0249); the 21.0 mrad point that failed S5's tolerance
(abs(dR) 0.0135) agrees to 0.0006. The residual +-1 % is of the size of the solver's own rod
truncation (13 against 21 rods, section 3). At [110] 17.6 mrad the pixel effect is larger than at
[100]: the averaged potential at 0.13 A is 4.1 % low in |R| and 0.076 rad low in phase (E8-10b), so
S5's largest [110] phase difference (-0.075 rad at 17.6 mrad) is the band limit at 0.13 A.

Cross-check with the rung-2 exact reference (E8-11; question 5): E1's R2-A cell (laterally uniform
continuum potential V0 + V_008, r = 0.1, exact propagator, x_s on a pixel centre) read with
`flat_reflection_coefficient` against P2's exact semi-infinite solution, run here at the atomistic
pixels. max |r - R_ref| over |eta| <= 3 is 9.40e-03, 5.52e-03, 1.45e-03 and 4.62e-04 at dx = 0.12994,
0.10000, 0.05000 and 0.02500 A (the last equals E1's R2-A value); near the plateau centre the
amplitude error is only -0.0020, -0.0013, -0.0002, +0.0000 (mean over |eta| <= 1: -0.0040 to
-0.0004), while the phase error is -0.0282, -0.0164, -0.0042, -0.0012 rad, i.e. about proportional
to dx^2. So in one dimension the engine's AMPLITUDE at 0.13 A is right to 0.4 %: the 2.5 % amplitude
error of the atomistic averaged runs at 0.13 A is not a one-dimensional propagation or read-out
effect but comes from the Fourier components that the band removes from the atomic potential (the
outer rods' normal components and the (0,0,l >= 16) harmonics, which the single-harmonic rung-2
potential does not have; DERIVED_HERE). The engine's PHASE, however, carries a normal-sampling
error of about -0.03 rad at 0.13 A even without atoms, the same size as the atomistic phase error
at that pixel (-0.027 rad).

Read-out and strip (E8-9, E8-10): the sheet beam's incident amplitude at the surface varies from
0.8923 to 1.0992 (16.2 mrad; 0.8922 to 1.1728 at 12.0 mrad) across the read-out window, because the
window's last ray leaves the sheet 11.15 A below its diffracting top edge (8.00 A at 12.0 mrad,
14.75 A at 21.0 mrad); its window mean is 0.9950 (16.2 mrad), 1.0222 (12.0) and 1.0017 (21.0) while
the read-out assumes 1 (a row-by-row normalisation would change |R| by -0.0209, +0.0046, -0.0020). This is a read-out
systematic of up to about 2 % in |R| at 12 mrad that S5's spread term only partly represents
(finding m5). The 250 A bins at 16.2 mrad alternate in every run, full and averaged (default run:
0.2620, 0.2708, 0.2654, 0.2742, 0.2682; E8-10), so the window mean depends on where the window ends
within that oscillation.

## 8. Findings

Ranked BLOCKER, MAJOR (m-numbers: MINOR, n: NIT). Each gives the quoted text, the evidence and a
proposed correction. No BLOCKER was found: the comparison does not pass because of a convention,
reference-plane, geometry or provenance error; every such check of S5's was confirmed independently.
What passes "for the wrong reason" is the AMPLITUDE statement: the loose tolerance absorbed two
effects of 2.5 % and 3.4 % in |R| that S5 did not separate.

### M1 (MAJOR). The comparison is not like-for-like along the beam; "HOLZ: common omission" is wrong

* Quoted: S5 9 "Both omit the same physics: HOLZ couplings (about 1 % in |R| and 0.01-0.02 rad by the
  solver's 61-rod test)"; S5 7 row "HOLZ couplings (neither code in its compared form) ... common
  omission"; S5 3.1 "N = 6 at [100] (13 rods) and N = 9 at [110] (19 rods) are exactly the rods inside
  the engine's 2/3 band"; S5 5 "Like-for-like comparison = ... solver rods = the engine-band ZOLZ row".
* Evidence: the engine slices along the beam (a/4) and so contains the along-beam couplings that the
  solver's row of rods (h,-h) averages out; S5 5 itself says the engine "partly carries" them. E8-10:
  the engine's along-beam couplings, measured as |R_full|/|R_averaged| - 1 at the same pixel, are
  -0.0219, -0.0173, -0.0329, -0.0344 (pixels 0.1293, 0.0990, 0.0742, 0.0646 A) with phase changes
  -0.0008, -0.0172, -0.0264, -0.0206 rad; with the average (the solver's physics) the engine
  converges to the solver (|R| +0.20 %, arg -0.0022 rad at 0.0646 A). The engine's converged
  along-beam effect (-3.3 to -3.4 % in |R|, -0.021 to -0.026 rad) is about three times the solver's
  61-rod disk estimate (-1.1 %, -0.009 rad).
  Also, the circular (f_x, f_y) band at 0.1293 A lets only rods |h| <= 5 carry the (0,0,8) normal
  component (E8-10), so the 13-rod row (|h| <= 6) is not "exactly" the engine's band.
* Correction: in S5 5 and 9 replace the like-for-like claim by: "same potential, absorption, lattice
  and termination; NOT the same Fourier components: the solver has the along-beam average of the
  potential (zero-order row, all normal components), the engine has the along-beam structure (slices
  a/4) inside a circular (f_x, f_y) band"; delete "common omission"; add E8's decomposition (M3).

### M2 (MAJOR). The declared tolerance cannot validate the amplitude; the pass must not be quoted as an amplitude validation

* Quoted: S5 9 item 3 "the engine reproduces the solver's complex R at 22 of 23 angles at exact [100]
  and 15 of 15 at [110] within the tolerance declared before the comparison"; S5 6.3 "its peak
  reflectivity is 9.6 % lower (4.9 % in |R|), just inside the 10 % tolerance".
* Evidence (E8-5b): the per-angle rule allows 0.112 |R_sol| at 16.2 mrad (+0.24/-0.21 in |R|^2); the
  solver's own curve scaled by 0.90 in |R| (|R|^2 -19 %) passes at all 23 angles, and scaled by 0.95
  (|R|^2 -9.75 %) it passes the curve-level peak test too. Two real effects of 2.5 % (engine band
  limit at 0.13 A) and 3.4 % (model difference, M1) were inside the tolerance and went unseparated.
  The phase part of the test does have power (conjugation: 19 of 23 fail; plane moved by 0.02 A: 12
  fail; one-rod model: 22 fail).
* Correction: quote the result as "phase: agreement within 0.03 rad over the (0,0,8) peak; amplitude:
  the engine at 0.13 A is 2.5 % low from its band limit, and the two models differ by the along-beam
  couplings (engine -3.4 % in |R|, -0.021 rad, not validated); with the solver's physics the engine
  converges to it within 0.2 % in |R| and 0.002 rad (16.2 mrad, E8-10)". For the next comparison fix
  the tolerance from the solver's rod and slab convergence (13 to 21 rods: |R|^2 0.07881 to 0.07908
  at 16.2 mrad) plus the engine's demonstrated pixel convergence, not from 5 % + 0.005 + 2 s_eng.

### M3 (MAJOR). "About 3 % in |R| remains unexplained" is explained; the pixel non-monotonicity is physics entering the band

* Quoted: S5 9 item 5 "about 3 % in |R| remains unexplained"; S5 6.5 "the PIXEL is the largest
  engine-internal sensitivity ... not monotonic ... partly a sampling effect ... and partly
  unexplained"; S5 7 last row "UNRESOLVED".
* Evidence: section 7 above (E8-10, E8-10b). The along-beam-averaged engine converges monotonically
  (|R| -2.52 %, -0.46 %, +0.13 %, +0.20 % against the 21-rod solver at 0.1293, 0.0990, 0.0742,
  0.0646 A); the full engine is non-monotonic because the first along-beam Laue ring enters the band
  between 0.099 and 0.074 A (E8-10 prints the ring frequency and the band radii).
* Correction: replace by E8's decomposition; production statements about engine amplitudes at
  0.13 A should carry the band-limit error (2.5 % in |R|, 0.027 rad at 16.2 mrad) as a known,
  pixel-dependent bias, and the along-beam couplings as an unvalidated model component.

### M4 (MAJOR). "No convention bug" covers only the normal direction

* Quoted: S5 9 item 4 "No sign, convention, reference-plane, refraction or orientation bug is
  visible: the conjugate is excluded"; S5 3.3 "(this corrects the expectation in docs/05 section 4.4
  and L2 D-I3, which concern the P49 paper's notation)".
* Evidence: E8-2 confirms the normal-direction convention (own TM, 7e-12 with the solver's slices).
  The lateral Fourier sign convention (whether U_g or U_-g multiplies exp(+i g.r)) cannot be seen
  here: every atom of the solver's slab sits at fractional (0 or 1/2, 0 or 1/2) (E8-3), so the
  surface is invariant under the two-fold rotation about the normal and R_00 is identical for a
  structure and its inverse. For
  steps (the measurand) this sign matters. For P49's fork, E8's code reading (section 2) shows the
  same f as upstream; S5 left it open.
* Correction: S5 9 item 4: "no sign error in the normal direction (time convention, absorption sign,
  reference plane) is visible; the lateral Fourier sign convention is untested by a two-fold-symmetric
  flat surface and must be tested with a surface without that symmetry (e.g. a vicinal cell) before
  step phases are compared". Wording for docs/05 4.4 and L2 D-I3 in section 10.

### MINOR

* m1. "Tolerances (DECLARED at 22:45 UTC, before the first engine run and before any engine-solver
  difference was computed)" (S5 5). Git cannot confirm the order: the first snapshot containing the
  tolerance block (`242b566`, 22:52:30 UTC) already holds an engine result stamped 22:47:50 UTC. The
  block is unchanged from then to `872e949` (E8-7b). Proposed: "declared at 22:45 UTC (S5 log);
  first committed in `242b566` together with the first engine result; unchanged afterwards".
* m2. "a fit d arg = c + 2 Gamma_0 dx gives c = -0.044 rad and dx = +0.005 A, i.e. no reference-plane
  error" (S5 6.2) and "the fitted reference-plane offset is 0.005-0.012 A" (S5 9). With 1-sigma
  errors: dx = +0.0052 +- 0.0122 A (c = -0.0440 +- 0.0970 rad, correlation -0.997) at [100] and
  -0.0120 +- 0.0088 A at [110]. Proposed: quote the one-parameter fit (c = 0): dx = -0.0003 +- 0.0009 A
  ([100]) and -0.0013 +- 0.0015 A ([110]).
* m3. The tolerance term 2 s_eng depends on read-out details: E8's band-passed read-out reproduces the
  stored R to 1.4e-03 but the spreads to only 6.0e-03 (12.0 mrad: 0.0063 against 0.0124). The 21.0
  mrad excess is 0.0011 in E8's read-out and 0.0003 in S5's. Proposed: state the spread definition
  (full 250 A bins inside the window, sin^2 vacuum taper, band-pass 0.1 1/A) with the tolerance, or
  replace it by a convergence-based engine uncertainty (M2).
* m4. "A unit CC = a ... fails ... because ... the outermost rod (6,-6) ... grows by 2.2e+31 across
  such a unit, beyond double precision. With CC = a/2 the growth is 4.7e+15" (S5 3.1). At [110] with
  CC = a/2 the growth reaches 1.0e+17 > 1/eps = 4.5e+15, and route A still agrees with route B to
  1.26e-05 (E8-3). Proposed: "the CC = a unit gives unphysical output (max |R|^2 2.57, total flux
  96.6), consistent with the ill-conditioning of bulk.exe's unit product (bulk.f90:82-98); the a/2
  unit with the (1/2,1/2) shift is exact for diamond (001) and is validated empirically by the A-B
  agreement".
* m5. The read-out assumes a unit incident amplitude at the surface (S5 6.1, R = <e> exp(+4 pi i f_c
  x_s)/P_L). The window's last ray leaves the sheet 8.00 to 14.75 A below its top edge (12.0 to 21.0
  mrad), and the vacuum-propagated incident amplitude at x_s over the window ranges 0.8923-1.0992
  (16.2 mrad) and 0.8922-1.1728 (12.0 mrad), with
  window means 0.9950, 1.0222 and 1.0017 at 16.2, 12.0 and 21.0 mrad (E8-9). Proposed: add this as a
  read-out systematic (up to about 2 % in |R| at 12 mrad) and, for future runs, either a taller sheet
  (window ending several Fresnel zones below the edge) or normalisation by a crystal-free run.
* m6. "Doyle-Turner (1968) ... otherwise Peng (1999)" (S5 F11): the years are read from the code
  comment (`asf.f90:3-4`); neither reference is in the literature reports or `docs/references.bib`.
  Proposed: "the Doyle-Turner fit as cited in the code comment (asf.f90:3-4; bibliographic data not
  verified by the B reports)".
* m7. "the 2/3 band at 0.13 A drops the (0,0,l >= 14) couplings" (S5 6.5): (0,0,14) is kinematically
  forbidden in bulk Si and sits exactly on the band edge; the first allowed normal harmonic outside
  the band is (0,0,16) (2.9461 1/A, S5 tool section 2). Proposed: "(0,0,l >= 16)".
* m8. S5 9 "What it cannot show" and "What is needed" omit the items listed in section 6 (lateral
  sign convention; circular band vs full normal structure; single reflection, angle range, azimuths,
  absorption ratio; incident-amplitude normalisation; engine version).

### NIT

* n1. "|g| <= 2.56 1/A" (S5 3.1) is not printed by the S5 tool (it is 2/3 of the Nyquist frequency at
  0.13 A; at the actual dy = 0.12931 A the band edge 2.5778 1/A coincides with the (7,-7) rod).
* n2. "exceeds it by 0.0003" (S5 6.2): give the unit (|R|, the complex-amplitude difference).
* n3. S5 6.3 FWHM and phase sweep depend on the interpolation of 0.1 mrad samples: E8's linear
  interpolation gives FWHM -2.87 % (S5 -3.27 %) and a sweep difference of -0.0054 rad (S5 +0.0062);
  both far inside the tolerances (E8-6).

## 9. Verdict table

| Question | S5's claim | E8 verdict | Evidence |
|---|---|---|---|
| 1 Patch | switch to electrons and output of f, no computation changed | CONFIRMED | E8-1 (diff: 3 removed, 6 added lines) |
| 1 Relativity at 200 keV | same scaled equation, K differs by -4.95e-06 | CONFIRMED | E8-1b |
| 1 Doyle-Turner table | Si row a, b as in asf.f90 | CONFIRMED as read; publication UNVERIFIED; years from a code comment (m6) | E8-1c |
| 1 Absorption like-for-like | `sap` = r proportional model in both | CONFIRMED for the model; the Fourier sets carrying it differ (M1) | section 1 |
| 1 Bulk unit a/2 | CC = a fails from overflow | CONFIRMED empirically (|R|^2 2.57, flux 96.6; A-B 2e-05); growth argument not sufficient (m4) | E8-3 |
| 2 Convention | no conjugation for sim-trhepd-rheed | CONFIRMED (own TM, 7e-12 with the solver slices; conjugate 0.38-1.71 away) | E8-2 |
| 2 P49 fork | not run, left open | same f as upstream by code reading (DERIVED_HERE) | section 2, E8-13 |
| 2 Scope of "no convention bug" | general | normal direction only; lateral sign untested (M4) | section 2 |
| 3 Reference plane | top-layer nuclei in both; dx 0.005 A | CONFIRMED (engine x_s = top atom; solver R_layer to 6e-14); fit errors +-0.012 A (m2); c = 0 fit -0.0003 +- 0.0009 A | E8-3, E8-5, E8-10 |
| 4 Tolerances fixed first | declared 22:45 | unchanged after the first engine result; order not provable (m1) | E8-7, E8-7b |
| 4 Tolerances meaningful | 5 % + 0.005 + 2 s_eng; 10 % peak | phase part has power; amplitude part does not (M2); spread fragile (m3) | E8-5b, E8-4 |
| 4 21.0 mrad failure | excess 0.0003 in R | CONFIRMED as a failure (E8: excess 0.0011); quantity = complex amplitude difference | E8-4, E8-5b |
| 5 Amplitude deficit | 3-5 %, partly unexplained | EXPLAINED: band limit at 0.13 A (2.5 %) + along-beam couplings absent from the solver (3.4 %); like-for-like engine converges to +0.2 %, 0.002 rad | E8-10, E8-10b |
| 6 Engine version | consistent numerics | CONFIRMED; HEAD d3de34a reproduces the 16.2 mrad column to 6.9e-08 | E8-7, E8-10 |
| 7 Cannot-show list | as S5 9 | one error (HOLZ "common omission", M1) and gaps (m8, section 6) | section 6 |

## 10. Proposed wording for docs/05 section 4.4 and L2 D-I3

docs/05 4.4, replacing "`sim-trhepd-rheed`, as vendored for the P49 benchmark, and its P49 fork ...
so its phases must be conjugated before comparison with this repository's convention (DERIVED_HERE,
UNVERIFIED until rung 1 below is run)":

> `sim-trhepd-rheed` (the P49 benchmark copy `df61124c`, the current upstream `d98d6252`) and its P49
> fork `trhepd-opt` (GPL-3.0) compute the complex reflection matrix but write only intensities; a
> three-line output patch exposes it (report S5). P49 (Kudo, Yamamoto and Hoshi) recasts the
> boundary-value problem as a matrix initial-value problem and returns rho(0) (preprint Eq. (36));
> it validates intensities only. The PRINTED notation of P49 (Eqs. (9)-(12), (36): crystal at z < 0,
> the exp(+i Gamma z) component labelled incident) corresponds to an exp(+i omega t) time factor, so
> an amplitude evaluated from those printed formulas is the complex conjugate of this repository's
> R (DERIVED_HERE, L2 D-I3). The CODES do not follow that notation: upstream sim-trhepd-rheed's
> f(i, nb0) is R = (upward)/(downward) at the top of its slice region in this repository's
> exp(+i k.r - i omega t) convention (REPRODUCED: S5 3.3, one-beam RK4; E8 section 2, independent
> transfer matrices), and trhepd-opt maps its integration variables back to the same f
> (`invstrans`/`strans` in `matcomp.f90`; its `conjg` calls implement Hermitian-transposed storage;
> DERIVED_HERE from code reading, E8, not run). No conjugation is applied to either code's f. The
> in-plane (lateral) Fourier sign convention is not tested by a flat surface with a two-fold axis
> along the normal (bulk-terminated Si(001)); it needs a surface without that symmetry. Source map
> SM19.

and in the open questions (docs/05, list near line 429) replace "Whether the current upstream
`sim-trhepd-rheed` release writes complex amplitudes ..., and the sign convention of P49's phases"
by "answered (S5, E8): the current upstream also writes intensities only; both codes' f is in this
repository's convention; open: the lateral sign convention (needs a non-centrosymmetric surface)".

L2 D-I3 (the report is a record; add a status note rather than rewriting the inference):

> Status after S5 and E8 (2026-09-24): correct for P49's PRINTED notation (Eqs. (9)-(14), (36)).
> It does not apply to the codes: sim-trhepd-rheed's f(i, nb0) is already in the project's
> convention (REPRODUCED, S5 3.3 and E8 section 2), and trhepd-opt's integrators return the same f
> (the `conjg` calls in `surf_prkn.f90`, `surf_rk.f90` and `matcomp.f90` belong to Hermitian-
> transposed storage; DERIVED_HERE, E8 section 2, not run). The 1-beam step-barrier test proposed
> here was run as S5's RK4 test and E8's transfer-matrix test; neither tests the lateral sign.

## 11. Statements the summary documents may quote

Each is supported by the section and script output named; labels as used there.

1. "An independent dynamical RHEED solver, sim-trhepd-rheed (upstream `d98d6252`, GPL-3.0, built
   outside the repository; Ichimiya surface-parallel slicing with recursive reflection matrices),
   was compared with the multislice engine on flat bulk-terminated Si(001) at 200 keV, 12-22 mrad,
   exact [100] and [110], with the same Doyle-Turner potential, a static lattice and the same
   proportional absorption r = 0.1 (TEST_ONLY). The solver's complex reflection matrix was exposed
   by an output-only patch (S5; E8 section 1)."
2. "The solver's amplitude is in the repository's exp(+i k.r - i omega t) convention and needs no
   conjugation (REPRODUCED twice: S5's one-beam RK4 test and E8's transfer matrices, which reproduce
   the solver's output to 7e-12 with its own slicing). This tests the convention along the surface
   normal only; the in-plane Fourier sign convention is not tested by a flat Si(001) surface."
3. "Phase: over the (0,0,8) peak at [100] (15.6-16.8 mrad) the engine's arg R agrees with the
   solver's within 0.03 rad while arg R sweeps by about 3.2 rad; the reference planes agree to
   0.001 A (one-parameter fit, -0.0003 +- 0.0009 A) (MEASURED_HERE, S5 6.2; E8-4, E8-5)."
4. "Amplitude: at the production pixel 0.13 A the engine's |R| is 2-5 % below the solver's near the
   peak. Two causes were identified (E8, MEASURED_HERE at 16.2 mrad): the engine's band limit at
   0.13 A (-2.5 % in |R|, -0.027 rad; removed by refining the pixel) and the along-beam couplings,
   which the engine includes and the solver's row of rods does not (-3.4 % in |R|, -0.021 rad once
   converged). With the solver's physics (potential averaged along the beam) the engine converges to
   the solver within 0.2 % in |R| and 0.002 rad at 16.2 mrad, and agrees within 1.1 % and 0.021 rad
   at 12.0, 15.8, 16.0, 16.4, 21.0 mrad ([100]) and 15.1, 17.6 mrad ([110]) at a 0.075 A pixel."
5. "In a laterally uniform (rung-2) potential the engine's Bragg-case amplitude at 0.13 A is right
   to 0.4 %, but its phase is 0.03 rad low, an error that falls as dx^2 (E8-11)."
6. "Not validated by this comparison: the size of the along-beam (higher-Laue-zone) couplings (the
   engine's -3.4 % is about three times the solver's truncated-disk estimate), the in-plane sign
   convention, steps and finite features, thermal and absorption models other than proportional
   r = 0.1, other reflections and larger angles, and the r = 0 limit (no semi-infinite reference)."
7. "The validated engine is the atomic path of commits `148e4f6` to `a1ef2a0`; HEAD `d3de34a`
   reproduces the 16.2 mrad exit column to 6.9e-08 (E8-10)."

Not to be quoted: "the engine reproduces the solver's complex R within the declared tolerance at 22
of 23 angles" as an amplitude validation (M2); "about 3 % in |R| remains unexplained" (M3); "both
codes omit HOLZ couplings" (M1); "no convention bug" without the normal-direction qualifier (M4).

## 12. Verified as correct (E8 recomputation or reading)

* Provenance: upstream commit, clean clone, 35/35 source files, patch content (output only plus the
  documented electron switch), executable hashes, compiler record (E8-1).
* Physics inputs: relativistic K and gamma (-4.945e-06, -1.128e-06), the DT Si row and its MIP
  13.9144 V, the proportional absorption `sap` = r model, static lattice, the solver's potential scale
  gamma 4 pi f/Omega (reproduced to 7e-12 by E8's model of the solver's slicing) (E8-1, E8-2).
* Convention: S5's RK4 numbers (9.61e-05/0.376 and 5.10e-04/1.707) reproduced by an independent
  method (9.59e-05/0.376, 5.09e-04/1.707); arg R(s_top) at 16.0 mrad +2.6930/+2.0725 (E8-2).
* All 36 solver cases: R at the top-layer nuclei (5.9e-14), the approach A/B agreement (2.18e-05,
  1.26e-05), dz and rod sensitivities, the phi = +-45 deg symmetry (2.15e-09), the flux bound
  (1.000000), the CC = a failure (2.57), the r = 0 slab dependence (468 and 469 of 501 angles) (E8-3).
* Engine read-out: S5's stored R reproduced by an independent read-out to 1.4e-03 ([100]) and
  1.8e-03 ([110]); 22/23 and 15/15 within S5's tolerance; the 21.0 mrad failure; the conjugation
  medians 0.0080/0.1670 and 0.0082/0.1209 (E8-4).
* Curve level: solver fine-grid peak 16.1571 mrad, |R|^2 0.07977, FWHM 0.6064 (S5 0.6065) mrad,
  unwrapped sweep +3.198 rad from 15.50 to 16.90 mrad; engine peak shift +0.0180 mrad (E8-6).
* H2 cross-check: H2's stored plateaus converted to R at the top layer: 0.07327/-2.9713,
  0.00186/+0.7537, 0.79341/-2.9991, as S5 (E8-8).
* Engine version consistency across S5's runs (E8-7, E8-7b) and the regression of HEAD (E8-10).
* S5's code locators checked while reading (SECTION_READ): F2 (`bulkm.f90:21-24`,
  `scpot.f90:159-161`), F5 (`trmatg.f90:24-50`, `surf.f90:64-73`), F6 (`surf.f90:88-107`), F7
  (`bulk.f90:126-140`), F8 (`surfio.f90:81-89`), F9 (`bulkio.f90`, ns = int(CC/dz) + 1, dz = CC/ns),
  F10 (`surf.f90:109-118`; the flux normalisation |f_i0|^2 Gamma_0/Re Gamma_i is confirmed by the
  flux bound in E8-3), F11 (`asf.f90:229, 329, 415-430`), F12 (`scpot.f90:46-50`), F13
  (`scpot.f90:25, 37-38, 53`), F15 (`scpot.f90:145-151`).
* S5's committed tool reproduces its saved report output line for line apart from the run time
  (E8-12): every number of S5's sections 3-9 that E8 checked is printed by a committed script.
