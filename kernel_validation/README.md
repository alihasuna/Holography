# kernel_validation — independent Peng–Cowley kernel, its validation, and the cross-check against this repository's engine

This folder is self-contained and was developed alongside `reflection_holo/` (the repository engine), not as a
modification of it. Nothing outside `kernel_validation/` is changed on this branch. Its package is also named
`reflection_holo`; scripts here put this folder first on `sys.path`, and it has its own `pytest.ini`.

Base: branch `trixode-studios-claude/ecstatic-euler-a2b4y1` at `4ea1c31`.
System: Si(001) bulk-terminated, beam azimuth [110], specular (008), 200 keV (HF-3300), W = 0 unless stated.

## 1. Engine-to-engine cross-check (main finding)

| Run | R_this / R_repo (31 angles) | shape correlation | peak |
|---|---|---|---|
| this kernel under the repository's `rocking_flat.py` setup, repository B = 0.46 Å² | median 0.913 (0.880–0.949) | 0.9994 | +0.8 mrad, both |
| same, repository engine rerun with B = 0.5261 Å² | median 1.006 (0.991–1.028) | 0.9999 | +0.8 mrad, both |

* The whole 5–12 % offset is the Debye–Waller factor. 0.5261 Å² is the Gao & Peng (1999) polynomial for Si,
  T > 80 K, evaluated at 300 K (Peng, Dudarev & Whelan 2004, Table 14.2, p. 462; coefficients checked against
  the book). The repository's 0.46 Å² is labelled ASSUMPTION in `docs/guide/parameters.md`.
  The specimen temperature (300 K) is itself an assumption.
* With matched B the two kernels agree to ±3 % (Peng-1996 vs Kirkland scattering factors, exact vs Fresnel
  propagator, sampling, mask shape).
* The repository's published curve (`docs/figures/data/rocking_001_008.json`, R_peak 0.019 at θ_B + 0.8 mrad
  = 16.93 mrad) is a property of its setup, not of its kernel: 20 Å sheet beam, cell 2·22 Å/tanθ ≈ 0.27 µm,
  ≈ 0.12 µm illuminated footprint, V_i = 0.05 V_r. Under converged conditions (below) R ≈ 0.55–0.60 near
  16.15–16.30 mrad (W = 0). How much of the peak shift is footprint and how much absorption has not been separated.

Scripts: `scripts/crosscheck_their_conditions.py` (≈ 8 min), `scripts/crosscheck_B_attribution.py` (≈ 30 s).
Data: `outputs/crosscheck_their_conditions.npz`, `outputs/crosscheck_B_attribution.npz`.

## 2. Validation of this kernel (executed)

* Sampling (SAMPLING_QUANT, dy 0.075 Å, dz 0.04 Å): finer grids change R by ~1e-5.
* Cell length governs convergence: |r|² at 16.25 mrad = 0.482 / 0.610 / 0.584 for L = 0.88 / 1.77 / 3.0 µm
  (`outputs/R2_length_convergence.npz`). Use L ≥ ~2 µm. The length rule in `multislice/cell.py`
  (from the one-beam extinction depth) is NOT adequate; `outputs/R2_results_QUANT.npz` and any R2 figure made at
  0.9 µm are not converged.
* Like-for-like with the 1D (one-beam) solver on the same averaged potential: median |Δr| 0.009
  (`validation/kernel_vs_1d.py`, INTEGRATION_NOTES.md F2).
* Exact test, a/2 step (lattice translation): far downstream |ratio| 0.9995, arg −3.030 rad vs exact −3.024 rad
  (`outputs/step_a2_validation.npz`).
* Exit wave of the a/4 step (`scripts/fig_exit_wave.py`, `outputs/fig_exit_wave.log`): 99.2 % of outgoing flux in
  vacuum; side rods m = 1, 2 leave at 14.88 and 9.66 mrad vs √(θ² − (mλ/b)²) = 14.88, 9.67 mrad; terrace B/A
  phase −1.665 rad (geometric 2Kh sinθ mod 2π: −1.512 rad).
* Tests: `pytest` in this folder (fast suite; slow suite recorded in TEST_OUTPUT_SLOW.txt).
  Two fixes (F1 Nyquist terms, F2 spectral-ratio extraction) and the post-hoc rewrite of three slow tests are
  declared in INTEGRATION_NOTES.md.

## 3. What is NOT established (read before using absolute numbers)

1. Absorption: W = 0 here; no sourced Si absorptive potential (the repository's 5 % is also a placeholder).
2. Mean inner potential: IAM 13.89 V vs measured ≈ 12 V — shifts all angles.
3. Debye–Waller B and specimen temperature (≈ 9 % in R between 0.46 and 0.526 Å²).
4. Bulk-terminated surface; no 2×1 dimer reconstruction, no TDS / frozen phonons, ideal straight step.
5. No comparison with measurement; no independent audit was run.

The kernel is verified as a solver; absolute R and A/B contrast are provisional until 1–4 are supplied.

## 4. Layout

| Path | Content |
|---|---|
| `reflection_holo/` | this kernel: constants (sourced), geometry, cell, potential, propagate, illumination, reflectivity, 1D solver |
| `tests/`, `validation/` | unit tests; abTEM transmission check, kernel-vs-1D |
| `scripts/run_R0.py … run_R2.py` | error budget, geometry, flat rocking curve |
| `scripts/run_step_quick.py` | a/4 or a/2 step, 5 µm cell (≈ 7–12 min); `SAVE_FULL=1` writes the 20 MB full exit wave (not committed) |
| `scripts/analyse_step_quick.py` | imaging, hologram (assumed μ, dose, MTF), reconstruction |
| `scripts/fig_step_structure.py`, `scripts/fig_exit_wave.py` | figures (repository Nature style, `reflection_holo/plotstyle.py`) |
| `figures/` | step structure, exit wave, step hologram |
| `outputs/` | small result files (force-added; the root .gitignore excludes `outputs/` and `*.npz`) |
| `task1_euv_ptycho_kinematic_reh/` | earlier work: EUV reflection ptychography and kinematic REH (code, report, figures) |
| `NOTES_*.md`, `REPORT_R0_R1.md`, `INTEGRATION_NOTES.md` | build notes (REPORT_R0_R1 states its expected outputs were not executed when written) |

Regenerate the exit-wave figure:
```
cd kernel_validation
N_LAYERS=1 OUT_NAME=step_quick_a4.npz FLAT_FROM=step_quick.npz SAVE_FULL=1 python scripts/run_step_quick.py
python scripts/fig_exit_wave.py
```
