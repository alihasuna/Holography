# Audit: legacy Bloch-wave / R-matrix reflection code (March 2026)

Status: complete, 2026-10-15. Auditor: Claude Code subagent.
Scope: every `.py` file in `legacy/march2026_bloch_rmatrix/` at commit 3859fbb (the `viewer*.py`,
`geometry_diagram.py` and `overlay.py` files only for imports and physics). Nothing under `legacy/` or
`reflection_holo/` was modified (`git status` is clean for both). Runs used a symlink
`simulation -> legacy/march2026_bloch_rmatrix` in the scratchpad, `PYTHONDONTWRITEBYTECODE=1`, and
`/home/user/Holography/venv/bin/python` (numpy 2.4.6, scipy 1.17.1). The audit scripts are copied to
`docs/dev/audits/legacy_bloch_rmatrix_scripts/` (section 6 explains how to rerun them).

Labels: REPRODUCED = I ran the legacy code and saw the output; DERIVED_HERE = my own derivation or my
own independent reference solver; SMOKE_TEST = an in-memory corrected variant that is not validated
beyond the stated check; SECTION_READ = read from a data file; UNVERIFIED = not checked against a source.

## 1. Verdict

**Not usable as an independent check as shipped, and not until it is fixed.** Every dynamical number
it produces is wrong. It leaves out the mean inner potential `U_0`, so there is no refraction and no
mean absorption. It drops the relativistic factor from `U_g`. It keeps the absorptive potential only
off the diagonal, so 77 % of the cell has gain. It then hides the resulting blow-ups (`sum|R|^2` up to
2e5) with an SVD truncation that breaks the boundary conditions by 26 %. Its own rocking-curve routine
tilts the beam out of the crystal and returns 1.000000 at every angle.

The core is salvageable. The 2N linearisation, the sign conventions, the `Im(gamma) > 0` selection and
the boundary equations are correct. With the fixes in section 5 applied in memory, the code's own matrix
layout reproduces an independent exact solution to `|d|R|^2| <= 1.4e-4` and to 0.005 rad in phase.
Treat it as "usable after fixes" for the specular-rod (1-D) limit only. The full 3-D (multi-rod) case
did not converge in this audit.

## 2. What each module does (traced to code)

| Module | What it actually computes |
|---|---|
| `constants.py` | Hard-coded λ = 0.025079 Å and K = 2π/λ. γ is computed but never used in any potential. a = 5.43102 Å; diamond basis with the origin on an atom. Scattering factors are 5 Gaussians labelled "Peng 1996" (they are not; F5). Fixed outward normal (-1,1,-1)/√3. Beam-tilt calibration matrix (PROJECT_INPUT; the source PDF is not here). |
| `structure_factors.py` | Diamond selection rules; `F_g = f_e(s) exp(-B s^2) Σ_j exp(-2πi g·x_j)`; `U_g = 4π F_g/Ω` with no γ. |
| `bloch_wave.py` | Beams ranked by 3-D `|s_g|`. Matrix `U_{g-h}(1 + 0.07i)` off the diagonal; diagonal = `2K s_g` (no `U_0`). 2N×2N companion matrix `[[0, I], [M, -2 diag(k_z)]]`; `numpy.linalg.eig`; keep the N eigenvalues with `Im(gamma) > 0`, with ad-hoc fallbacks. |
| `r_matrix.py` | Not an R-matrix or slice propagation. It is Bloch-wave boundary matching at one plane, with ψ and ∂ψ/∂z matched separately for every 3-D beam g. The N×N system is solved by an `lstsq` sweep over `rcond`, keeping the largest `rcond` that gives `Σ|R_g|^2 <= 1.05`. It returns complex `R_g` per 3-D g, referenced to the cut plane through the origin atom, and reports `|R_g|^2` as the "intensity". `compute_rocking_curve` scans the tilt. |
| `kinematical.py` | Builds the reciprocal lattice (diamond-forbidden g removed). Uses 3-D `s_g` with a 0.5 to 2.0 Å⁻¹ tolerance. Puts spots on the detector from `k_i + g`, not from the rod/Ewald intersection. |
| `calibration.py` | BTX/BTY → tilt (affine); grazing angle = `asin|k̂·n|` from the beam tilt only (the stage alpha is read but not used). |
| `supercell.py`, `multislice_3d.py` | Peng-Cowley edge geometry: slices perpendicular to the [110] beam, with the (1-11) surface as an edge in each slice. So it is a grazing multislice in geometry, not a transmission projection. But each atom is a made-up 2-D Gaussian, 24 V·Å peak and σ = 0.3 Å; the propagator is paraxial with a tilt; the start wave is ψ = 1 everywhere, crystal included. It cannot produce a specular beam (F8). |
| `run_simulation.py` | Pipeline: calibration → kinematical spots → `compute_reflected_intensities` → Hungarian matching to experimental spots → overlay plots. It needs `.hm` files and `tiff_exports/<stem>_spots.csv`. |
| `export_structure.py` | Writes CIF/XYZ/VESTA files of the supercell. No physics. |

## 3. Findings (ranked)

| # | Sev. | file:line | Defect | Evidence (REPRODUCED unless stated) | Fix / test |
|---|---|---|---|---|---|
| F1 | Critical | `r_matrix.py:181-196` | The SVD "adaptive truncation" keeps the **largest** `rcond` (≤ 0.1) that gives `Σ|R_g|^2 <= 1.05`, so it almost always uses `rcond = 0.1`. The returned α does not satisfy the boundary equations. | Experimental tilt (27.9 mrad), N = 21: exact solve of the code's own system gives `Σ|R|^2 = 199630`. The sweep picks `rcond = 1e-1` (9 of 21 singular values kept) with a **relative residual of 0.256**; this is what gives the published `Σ = 0.039`. Specular rod only: shipped `|R_000|^2 ≈ 0.99` at every angle above 13 mrad, with dips to ~0 exactly at the vacuum Bragg angles 12.0, 16.0, 20.0, 28.0 and 32.0 mrad (`t3`, `t7`). | Remove the sweep. Use `numpy.linalg.solve`, report the condition number, and assert that the residual is below 1e-10. The ill-conditioning is a symptom of F2 to F4 and F6, not something to regularise. |
| F2 | Critical | `bloch_wave.py:80-82, 161-163` | `U_0` is never put on the diagonal (`M[g,g] = 2K s_g`, with the vacuum K). So there is no refraction and no mean absorption. | With `Re U_0` removed, the (4,-4,4) peak of the exact 1-D solution moves from 13.36 to 16.12 mrad, a 2.8 mrad error. θ_c = 9.06 mrad for these f_e (DERIVED_HERE). The accompanying `RHEED_simulation_report.md` §1.3 says the refraction correction is "of order 0.1 mrad"; it is ~30× larger. This is probably where the omission came from. | `M[g,g] = 2K s_g + U_0(1 + iμ)`. Test: two-beam peak at `sqrt(θ_B^2 - U_0/K^2)` (below). |
| F3 | Critical | `structure_factors.py:114-117, 139-142`; `bloch_wave.py:90` | `U_g = 4π F_g/Ω` has no relativistic γ. The docstring says γ is "embedded in the Peng parameterization", which is false. | Every `U_g` is too small by 1/1.39139 (`t1`). The two-beam plateau width is 0.391 mrad instead of 0.544 mrad at (4,-4,4) (`t9`, DERIVED_HERE). | `U_g = 4π γ F_g/Ω`. |
| F4 | Critical | `bloch_wave.py:92` | Absorption `U_g(1 + 0.07i)` is applied to off-diagonal terms only; `U'_0` is missing. The absorptive potential `μ(U(r) - U_0)` is then negative (gain) over **77 %** of the 3-D cell and 55 % of the (111) rod-averaged z. The `Im(gamma) > 0` rule then picks unphysical waves. | Shipped rod-only scan: `Σ|R_g|^2` = 137 at 15 mrad and 178 at 17 mrad. Shipped two-beam `{000, (-4,4,-4)}`: `|R_g|^2` = 776. Si(001) rod: `|R_000|^2` up to 33.9 (`t3`, `t9`, `t12`). The experimental tilt gives 23 of 42 eigenvalues with `Im > 0`, so 2 are dropped ad hoc. | Use proportional absorption that includes `U'_0` (positive definite for neutral atoms), or a sourced optical potential. Use the same μ as `reflection_holo` (0.05) for comparisons. |
| F5 | Critical | `r_matrix.py:290-302` | `compute_rocking_curve` tilts the beam toward the **outward** normal (`tilt_dir` = projection of `SURFACE_NORMAL`), so the beam leaves the crystal. Then `κ_0 - κ_inc = 0`, α = 0 and `R_000 = -1`. | `k·n_out = +1.25` to `+19.98` Å⁻¹; specular = 1.000000 at all 100 angles; `run_simulation --rocking-curve` plots a flat line at 1 (`t7`). | Tilt along `-SURFACE_NORMAL`. Assert `k·n_out < 0`. |
| F6 | High | `kinematical.py:238-240`, `structure_factors.py:162-164` | Diamond-forbidden g (e.g. (2,-2,2), (0,0,2)) are removed from the **beam basis**. They have `U_g = 0` but are needed as intermediate states (for example 111 + 111 → 222). | Specular rod with allowed beams only: the corrected variant is off by up to 0.11 in `|R|^2` and 2.8 rad in phase, and gets **no better** with 13 to 37 beams. With forbidden beams kept, the error drops to ≤ 1.4e-4 (`t5` vs `t5b`). | Build the basis from all fcc-parity g (or all g) and keep `U_{g-h} = 0` where it is zero. |
| F7 | High | `r_matrix.py:251-264, 309-318` | Results are per 3-D g, not per reflection rod. Beams on one rod (e.g. 000, (1,-1,1), (-4,4,-4)) share one vacuum wave. The specular amplitude is `Σ_rod R_g`, not `R_000`. The "intensity" `|R_g|^2` has no current factor `Re κ_g/κ_0` and also lists beams that go into the crystal (e.g. (1,-1,5)). | Corrected variant: `|R_000|^2` differs from `|Σ_rod R|^2` by up to 0.31 (`t4`). (-2,2,-4) and (-1,1,-3) land on the same detector point, which the code reports as two spots (`kinematical` check). | Group beams by in-plane component; report `R_rod` and `|R_rod|^2 Re κ/κ_0`. |
| F8 | High | `supercell.py:192-205`; `multislice_3d.py:83, 177-200` | `multislice_3d` cannot simulate RHEED. (i) The atom potential integrates to 13.6 V·Å³ instead of 278.6 (×20.5 too weak), so the mean inner potential is 0.65 to 0.68 V. (ii) `ky0 = -θ/λ` moves the beam **away** from the crystal (+10.75 Å over 384 Å with the crystal at y < 0; the comment at line 174 contradicts `supercell.py`). (iii) With default sampling the 2/3 band stops at 21.4 mrad, while the specular beam is 56 mrad from the incident beam (the grid limit is 32 mrad). (iv) ψ = 1 fills the crystal, which is end-face illumination. | Default run (82 s): fraction of intensity beyond 21.4 mrad = 1.9e-32; `I(±56 mrad) = 0` (`t11`). | Do not use. `reflection_holo/forward/multislice.py` already does all four properly. |
| F9 | High | `bloch_wave.py:24-41` | Beams are ranked by 3-D `|s_g|`. RHEED needs whole rods (all `g_perp` per rod) and enough in-plane rods. | Corrected variant, Si(111) at 13.3 mrad: specular `|R|^2` = 0.0009, 0.054, 0.100, 0.132 for n = 20, 40, 80, 140 ranked beams. Rod-complete sets of 49 to 181 beams give 0.063, 0.046, 0.115, 0.130, 0.107, so multi-rod 3-D is **not converged** (SMOKE_TEST, `t13`). | Choose beams by in-plane cutoff × perpendicular cutoff; run convergence tests. |
| F10 | High | `bloch_wave.py:225-241` | Selection by `Im(gamma) > 0` only works when absorption is positive and nonzero. With μ = 0 the propagating modes have `Im = 0` and the fallback picks at random. The "> N" branch (keep the smallest Im) has no justification. | Corrected variant with μ = 0: 0 of 66 eigenvalues have `Im > 1e-12` at 6, 10, 16 and 20 mrad, and `|R|^2` comes out as 6.1 to 2272. The exact value is 0.08 to 0.10 (`t8`). | For real eigenvalues, select by current direction, `Re[(k_z + γ)]` weighted by `|C|^2`, i.e. by Poynting flux. Then run the flux test. |
| F11 | High | `constants.py:55-59` | Scattering factors are labelled "Peng, Ren, Dudarev, Whelan 1996". The first 4 pairs agree with Kirkland within 1 to 2 % for s ≤ 1 Å⁻¹; I believe they are the Doyle-Turner Si values (UNVERIFIED). A 5th pair (0.0862, 0.0120) matches nothing available here and adds a nearly constant +0.086 Å. | `|V_g|` is too large compared with Kirkland (abTEM 1.0.6 json, SECTION_READ): 111 ×1.02, 444 ×1.17, 008 ×1.21, 0,0,12 ×1.36. V_000 = 14.12 V against 13.90 to 13.93 V for Kirkland, Peng and Doyle-Turner. | Use the same table as `reflection_holo` (Peng high, abTEM json). |
| F12 | Medium | `bloch_wave.py`/`r_matrix.py` (design) | The surface is the bulk Fourier series cut off at the plane through the origin atom layer, so atoms are cut in half. There is no termination parameter. The phase of `R` is referenced to that plane only. The `reflection_holo` slab has whole atoms with the top bilayer intact. | Same parameters (Peng high, B = 0.46, μ = 0.05), same reference plane z = 0. (4,-4,4): truncated bulk gives a peak of 0.267 at 13.38 mrad with arg 2.51 rad; whole atoms give 0.197 at 13.31 mrad with arg 3.12 rad. (008): 0.195 at 16.19 mrad with arg 2.09 rad, against 0.178 at 16.15 mrad with arg 2.41 rad (DERIVED_HERE, inline run logged in section 6). | Add a slice/layer description of the surface region (Peng-Dudarev-Whelan "slices parallel to the surface", not implemented here), or at least a movable cut plane. |
| F13 | Medium | `r_matrix.py:241-249` | `compute_reflected_intensities` does not pass `surface_normal` on, so Si(001) needs the low-level functions. | `t12` used `solve_bloch(..., surface_normal=(0,0,1))` directly. | Pass the argument through. |
| F14 | Medium | `kinematical.py:252-347` | Spot positions come from `k_i + g` with a `|s_g|` tolerance of 0.5 to 2 Å⁻¹ (`run_simulation.py:321` uses 2.0), not from rod/Ewald intersections. | Error of 60 px for (-2,2,-4) and 133 px for (-1,1,-3) at the experimental tilt. | Use `k_f = (k + g)_t + κ_g n_out`. |
| F15 | Medium | `calibration.py:46-73` | The grazing angle comes from the beam tilt only. It assumes the crystal is exactly on [110] with the surface containing the zero-tilt beam; the stage tilt (≈ 4.1°) is ignored. | Code reading; the calibration PDF and `.hm` data are absent. | PROJECT_INPUT (ROADMAP Comparison 1). |
| F16 | Low | `constants.py:51-52`; `structure_factors.py:14`; `r_matrix.py:150-168, 319-320` | Dead `SI_MEAN_INNER_POTENTIAL_V = 12`, `SI_ABSORPTIVE_POTENTIAL_V = 0.9` and `RELATIVISTIC_GAMMA` import. The 2N boundary system is built and never used. `except Exception: 0` hides failures. The docstrings contain unfinished derivations ("wait, let me be more careful"). | Grep. | Clean up. |
| F17 | Low | `run_simulation.py:537-550` | The default `--dir` resolves to `legacy/`, so a default run writes `legacy/simulation_results/` into the repository. | Code reading; I ran it only with `--dir` set to the scratchpad. | Default to a scratch or `outputs/` path. |

Correct, and checked: the diamond selection rules and structure-factor geometry (`|F|` of 200, 002, 222,
666, 006, 442 and -2,2,-2 below 4e-15; 444 allowed, `|F| = 4.12 Å`); λ (−1.4e-5 relative to CODATA
2018), γ = 1.391390 and σ = 7.2885e-4 rad/(V·Å) (`multislice_3d`); the atom positions; the
Debye-Waller form `exp(-B s^2)` with B = 0.4632 Å² (the value is an ASSUMPTION, consistent with
`reflection_holo`'s 0.46); the 2N companion matrix and its signs for `ψ ∝ exp(i(k + g + γn)·r)` with n
pointing inward; and the per-g ψ/ψ' matching. These last three are shown correct by the corrected-variant
test, 5b in section 4.

## 4. Numbers computed

**Constants (DERIVED_HERE, `t1`).** λ(200 keV) = 0.0250793 Å (legacy 0.025079); K = 250.532 Å⁻¹
(legacy 250.536); h²/(2π m₀ e) = 47.8776 V·Å²; Ω = 160.193 Å³ (a = 5.43102 Å).

| Parametrisation | f_e(0) (Å) | V_000 (V) |
|---|---|---|
| legacy, 5 terms | 5.9053 | 14.120 |
| legacy first 4 terms (Doyle-Turner-like) | 5.8191 | 13.913 |
| Kirkland (abTEM 1.0.6) | 5.8143 | 13.902 |
| Peng low / high (abTEM 1.0.6) | 5.8268 / 5.8182 | 13.932 / 13.911 |

Neutral-atom parametrisations give 13.9 V, not 12 to 13 V. The 12 V figure is the bonded or measured
range (ASSUMPTION B1 in `model_assumptions.md`). θ_c = 9.064, 8.994 and 8.356 mrad for V0 = 14.12, 13.90
and 12.0 V.

`|V_g|` in volts (B = 0.4632), legacy against Kirkland: 111 5.576/5.450; 220 4.536/4.315; 004 2.758/2.573;
333 1.324/1.201; 444 1.233/1.051; 008 0.971/0.806; 555 0.593/0.486; 0,0,12 0.422/0.311. 222 and 666: 0.
`|U_g|` code against correct value: the ratio is 1.3914 for every g.

**5a. Exact 1-D reference (DERIVED_HERE, `harness.py`, `layered.py`).** Laterally averaged potential of
the surface (specular rod only), semi-infinite. The transfer matrix over one period is built from exact
2×2 steps, and the Bloch mode is the eigenvector with `|λ| < 1` (or, with μ = 0, the one with inward flux).
Checks: Fresnel step `R` = −0.148809 against −0.148809 analytic; converged to 1e-6 in steps and in
harmonics; with μ = 0, `max|R|^2 = 1.00000000`, and 15 points have total reflection.

**5b. Corrected in-memory variant against the exact reference (SMOKE_TEST for 1-D, `t5b`, `t6b`).** The
legacy matrix layout, `select_evanescent` and per-g equations, plus `U_0`, γ, μ on every `U_g`, forbidden
g in the basis, exact solve, and rod sums. On the Si(111) rod (33 beams), from 5 to 26.5 mrad:
`|d|R|^2| <= 1.4e-4`, `|d phase| <= 0.005 rad`. Rod-summed matching with a single Bloch wave gives the
same values.

**(a) Current conservation without absorption (`t8`).** Shipped, rod only: `n(Im γ > 0)` = 10 to 17 of
26; `|Σ_rod R|^2` = 0.040 at 13.2 mrad, where the exact value is 1.000 (total reflection), and 0.98 at
16 mrad, where the exact value is 0.021. Shipped 3-D: the totals of 0.03 to 0.23 that it prints are
artefacts of the `rcond` truncation. Corrected variant with legacy selection: 6 to 7e7. The flux test
cannot pass until F10 is fixed.

**(b) Two-beam limit {000, (-4,4,-4)} (`t9`).** Darwin form with refraction:
`R = -(A₀ ∓ sqrt(A₀² - U_G U_-G))/U_G`, `A₀ = K² sin²θ + U_0 - G²/4`. Its centre is
`sqrt(θ_B² - U_0/K²)` = 13.182 mrad (vacuum θ_B = 15.997) and its plateau width is
`|U_G|/(K² θ)` = 0.544 mrad.

| μ | Calculation | Centre (mrad) | FWHM (mrad) | Peak |
|---|---|---|---|---|
| 0 | Darwin analytic | 13.180 | 0.560 | 1.000 |
| 0 | exact 1-D, `U_0 + U_±444` | 13.180 | 0.560 | 1.000 |
| 0 | shipped `|R_000 + R_g|^2` | 11.58 | 2.74 | 1981 |
| 0.07 | Darwin analytic | 13.180 | 0.680 | 0.232 |
| 0.07 | exact 1-D | 13.290 | 0.700 | 0.249 |
| 0.07 | corrected 2-beam Bloch | 13.300 | 0.680 | 0.250 |
| 0.07 | shipped `|R_000|^2` | 17.71 | 0.58 | 0.016 |
| 0.07 | shipped `|R_g|^2` | 17.73 | 0.54 | 776 |

**(c) Rocking curves.**

* Si(111) rod, legacy parameters (`t3`, `t4`). Exact maxima (U₀ and γ included, μ = 0.07): 8.5, 13.25,
  18.0, 26.5 and 30.75 mrad, against refraction-corrected values (V0 = 14.12 V) of 7.86, 13.18, 17.83,
  26.49 and 30.69 for orders 3, 4, 5, 7 and 8. The shipped maxima are scattered between 7 and 36 mrad,
  with `|R|^2 > 1` and dips at the vacuum Bragg angles.
* Si(001) (008), legacy parameters (`t12`). Exact and corrected peak: 16.18 mrad, `|R|^2 = 0.159`. The
  refraction-corrected value is 16.10 (vacuum 18.47). Shipped `|R_000|^2` reaches 33.9 and
  `|Σ_rod R|^2` reaches 569.
* Layered full-atom reference with `reflection_holo`'s parameters: Peng high, B = 0.46, μ = 0.05,
  a = 5.4309, V0 = 13.912 V (`t10`).

| Reflection | θ_ext Bragg (mrad) | Peak offset (mrad) | FWHM (mrad) | `|R|^2` max |
|---|---|---|---|---|
| (008) | 16.133 | +0.02 | 0.34 | 0.178 |
| (0,0,12) | 26.209 | 0.00 | 0.16 | 0.037 |
| (4,-4,4) | 13.227 | +0.08 | 0.40 | 0.197 |
| (3,-3,3) | 7.937 | +0.26 | 0.84 | 0.302 |
| (5,-5,5) | 17.859 | +0.04 | 0.22 | 0.033 |

At `reflection_holo`'s operating angle of 16.933 mrad (Bragg + 0.8) the 1-D `|R|^2` is 0.0054, 33×
below the peak. `reflection_holo`'s own flat-surface scan (`outputs/rocking/*.json`, gitignored,
SECTION_READ) puts the (008) peak at +0.8 mrad and the (0,0,12) peak at −0.6 mrad, and finds **no**
(4,-4,4) peak within ±3 mrad. This disagreement has to be resolved in step 2. The 1-D model leaves out
multi-rod coupling (F9), so it is a flag, not proof of a kernel error.

**(d) Translation covariance and the step phase (`t10`).** The legacy code cannot move its surface plane
(F12). Its R is relative to its own cut plane, so a lattice translation leaves R unchanged, and the
vacuum factor has to be added by hand. In the layered reference, moving the crystal and its surface
outward by one bilayer (h = d₁₁₁ = 3.1355 Å) gives `R_shift/R = exp(−2iκ_vac h)` to 6e-13 at 10, 13.2,
13.5 and 20 mrad. That is `exp(−i(k_out − k_in)·R)` with vacuum vectors.

Single-bilayer step phase on Si(111), specular (4,-4,4):

| Angle | Value (mrad) | `|Δφ|` mod 2π (rad) |
|---|---|---|
| Reflectivity maximum | 13.317 | 2.07 |
| Refraction-corrected Bragg, V0 = 13.91 V | 13.227 | 1.93 |
| V0 = 12 V (`physics_summary.md` §3) | 13.642 | 2.58 (reproduced) |
| Vacuum Bragg (where the legacy physics puts the peak) | 15.997 | 0.001 (invisible) |

The difference between 2.58 and 1.93 is the V0 sensitivity of −0.34 rad/V stated in `physics_summary.md`.

**multislice_3d (`t11`).** Mean inner potential 0.654 V (numerical) and 0.678 V (analytic). There are 994
atoms against 1021 expected (−2.6 %).

## 5. What it would take to use it as validation step 2

Minimum fixes (about 100 lines; each one needs a pytest):

1. Put `U_0(1 + iμ)` on the diagonal.
2. Use `U_g = 4πγ F/Ω`.
3. Apply proportional absorption including `U'_0`, with the same μ as `reflection_holo`.
4. Replace the `rcond` sweep with an exact solve, a condition-number report and a residual assertion.
5. Keep forbidden g in the basis.
6. Sum by rod and use current-normalised intensities.
7. Select modes by flux for real eigenvalues.
8. Choose rod-complete beam sets and run convergence scans.
9. Fix the tilt sign in `compute_rocking_curve` and pass `surface_normal` through.
10. Use `reflection_holo`'s f_e table (Peng high), B = 0.46, a = 5.4309.
11. Model the surface region with whole atoms (layer slices) and a defined termination.

Then compare, in this order:

* **2a, specular rod only, flat surface.**
  * Geometry: Si(001), (008), [110] azimuth, θ_ext from 15.1 to 17.9 mrad in 0.02 mrad steps; and
    Si(111) `SI111_FRAME`, (4,-4,4) and (5,-5,5).
  * Reference: the fixed Bloch code restricted to the rod, cross-checked against the exact transfer
    matrix in `legacy_bloch_rmatrix_scripts/layered.py`. These two must agree to 1e-4 in `|R|^2`.
  * `reflection_holo`: run with a laterally averaged potential (a new option) so the physics is the
    same.
  * Normalisation: `reflection_holo`'s aperture fraction must be turned into a current reflectivity
    first.
  * Tolerances: peak position ±0.05 mrad, FWHM ±10 %, `|R|^2` at the peak ±10 % relative, and
    `arg R(θ)` across the peak ±0.05 rad after one common offset for the phase reference plane.
* **2b, full 3-D, flat surface.** Same geometries. The fixed Bloch code must first converge (`|R|^2`
  within 2 % from one rod-set enlargement to the next; F9 shows it does not at 181 beams). Then compare
  with `reflection_holo`: peak position ±0.1 mrad, `|R|^2` ±15 %.
* **2c, step phase.** Run two terraces in `reflection_holo` and compare the phase difference with
  `−(k_out − k_in)·R` in vacuum (1.93 to 2.07 rad near (4,-4,4) for V0 = 13.91 V) to ±0.02 rad.

Given the effort and the open 3-D convergence, the ROADMAP's choice for step 2 (`sim-trhepd-rheed`, an
established surface-parallel code) should remain the primary independent check. A fixed version of this
code, or the 1-D transfer matrix delivered here, is a cheap secondary check for 2a. The 2a check is
useful now: it already disagrees with the +0.8 mrad operating offset used in
`configs/si001_three_sections_cpu.yaml`.

## 6. Command log

All commands were run from the scratchpad with `PYTHONPATH=<scratch>/legacy_run:<scripts>` and
`PYTHONDONTWRITEBYTECODE=1`. `<scratch>` is
`/tmp/claude-0/-home-user-Holography/e65a7929-819b-5339-9a99-a18b5d68cf57/scratchpad`; the scripts are in
`docs/dev/audits/legacy_bloch_rmatrix_scripts/`.

| Command | Result |
|---|---|
| `python -m simulation.structure_factors` | 10/10 selection rules pass |
| `python -m simulation.calibration` | tilt (53.16, 26.73) mrad; grazing 27.92 mrad |
| `python -m simulation.bloch_wave` | 20 beams; `Im gamma` 0 to 2.07 |
| `python -m simulation.r_matrix` | total 0.039218; top beam (1,-1,5) |
| `python -m simulation.kinematical`, `python -m simulation.supercell` | ran; output in the audit |
| `python -m simulation.run_simulation --dir <scratch>/run_sim_out` | "0 patterns"; empty summary CSV |
| `python -m simulation.run_simulation --dir <scratch>/run_sim_out --rocking-curve` | flat curve at 1.0 |
| `pip download abtem==1.0.6 --no-deps` into `<scratch>/dl_abtem`, unzip data only | SECTION_READ of Si entries: `kirkland.json` sha256 a79b4f2e…; `peng_high.json` d0bc6b8b…; `peng_low.json` 61846f64… |
| inline comparison of truncated bulk and layered termination at equal parameters (F12) | as quoted in F12 |
| `t1_constants_sf.py` … `t13_beamsel.py` | section 4 (`t11` includes a full default `run_multislice`, 82 s) |
| `git status` | `legacy/` and `reflection_holo/` unchanged |

NOT RUN:

* `run_simulation` on real patterns. The `.hm` files, `tiff_exports/*_spots.csv` and
  `beam_tilt_calibration_formulas.pdf` are absent; they live in the research folder
  (`research-agent/MARCH/01_Si110_reflection_holography/2026-03-19_reflection_with_Arthur/07_VALID_measurements/diffraction_series/`,
  see `docs/dev/research_folder_findings.md`).
* `multislice_3d` `__main__` and `export_structure` (both write into `legacy/../simulation_results` by
  default).
* The viewer and GUI files.
* Any check against Peng-Dudarev-Whelan (2004) Eq. 5.45 itself (book not available: UNVERIFIED).
* `sim-trhepd-rheed`.

To rerun: `cd <any dir>; PYTHONPATH=<dir with simulation symlink>:docs/dev/audits/legacy_bloch_rmatrix_scripts PYTHONDONTWRITEBYTECODE=1 venv/bin/python docs/dev/audits/legacy_bloch_rmatrix_scripts/t9_twobeam.py`.
`t2`, `t3` and `t4` write small `.npy` files to the working directory.
