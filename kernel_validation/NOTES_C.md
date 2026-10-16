# NOTES_C — R2 items 2c (illumination), 2d (cell), 2e (reflectivity)

Status: **code written; not executed in this session.** No number below is a result. Expected outputs
are stated as predictions or acceptance criteria. Results come only from running the commands:
```
pytest tests/test_illumination.py tests/test_cell.py tests/test_reflectivity.py -v
RH_SLOW=1 pytest tests/test_reflectivity.py -v      # T-unitarity reflection part, T-kinematic, T-convergence
python scripts/run_R2.py --quick                    # then without --quick for production
```
Expected outcomes:
- **Fast tests:** all pass, except `test_published_si_rocking_curves`, which reports XFAIL (strict, by design).
- **`test_unitarity_per_slice_real_potential` — known risk.** If it fails, the measured per-slice loss
  is the Kirkland bandwidth loss [card:kirkland_ch06, p.41]. The remedy is a smaller dz; the 1e-6
  tolerance from the task is not loosened.

## 1. Illumination (2c)
- **Window.** Peng's mask passes only the beam that hits the surface. A sharp edge causes Fresnel
  fringes, so the edge is rounded [card:peng_ch05, p.8]. We use a compact cos² edge (ASSUMPTION; Peng
  used a Gaussian). Because the support is compact, the end-face fraction at x = 0 is exactly 0. After
  one vacuum slice it must be < 1e-3 (test).
- **Incident wave.** ψ0 = w(z)·exp(−iK sinθ (z − z_s)), with K = 2π/λ (DERIVED_HERE from exp(+ik·r)). The
  test checks the FFT sign: the peak is at −sinθ/λ.
- **Bandwidth guard.** The guard is sinθ/λ + 1/s < 1/(3 dz) [card:kirkland_ch06, p.35–36]. With dz = 0.08 Å
  the band is 4.17 Å⁻¹, i.e. 104 mrad at 200 keV. This covers the specular beam plus G(0,0,12) = 2.21 Å⁻¹.

## 2. Cell criteria (2d), DERIVED_HERE
Premises:
- (P1) K_z,int² = K_z,vac² + 2meγV/ħ² (repo conventions).
- (P2) 2meγ/ħ² = 2Kσ, which follows from σ = 2πmeλ/h² [card:kirkland_ch06, eq. 6.7, 6.43].
- (P3) Two-beam Bragg band with Im γ ≤ U_g/(2k₀z) [card:peng_ch05, p.21–22].
- (P4) A slab much thicker than the absorption length gives semi-infinite reflection coefficients
  [card:peng_ch05, p.34].
- (P5) A steady state is reached after a distance [card:peng_ch05, p.9].

Criteria:
1. **Penetration depth.**
   - With absorption, Λ_abs = K_z,int/(2Kσ W0), where W0 is the bulk mean of Im V measured from
     `potential.py`.
   - With W0 = 0, Λ_ext = K_z,int/(2Kσ|V_G|), where V_G is the rod coefficient at G = 2K_z,int.
   - Crystal depth: D = n_depth·Λ with n_depth = 4 (round-trip amplitude e⁻⁴ ≈ 0.018), clipped to
     [2 pz, 300 Å].
2. **Length.** L = (gap + H_w)/tanθ_e + D/tanθ_i.
   - A surface point reflects in steady state only if illuminated crystal extends D/tanθ_i upstream.
   - The decaying tail must also have emerged before the exit plane.
3. **Window height.** H_w = D·T + 2s + w_extract, with T = tanθ_e/tanθ_i.
   - The steady exit band is h ∈ [D·T, H_w], trimmed by s on each side.
   - The usable band width is then w_extract.
4. **Vacuum height.** H_vac ≥ max(gap + H_w, L tanθ_e) + 3√(λL) + guard.
   - The rise term reproduces calculator T19 (4.4604 Å over 198.248 Å at 22.495 mrad); this is tested.
   - Anything wrapping through the top of the z grid enters the bottom absorber.
5. **Slicing** [card:kirkland_ch06, p.30–33; card:kirkland_ch07, p.43].
   - The x period is a/√2 = 3.8402 Å for both azimuths.
   - Default: 2 sub-slices of 1.920 Å; the convergence variant uses 0.960 Å. Both are commensurate
     (calculator section 9).
   - Kirkland's ≈1 Å minimum for projected potentials makes 0.96 Å the lower limit.
6. **Termination and 2×1 option.**
   - Si(111) is bulk-terminated above the 2.35 Å gap (tested against calculator 2b).
   - The Si(001) 2×1 option is a symmetric dimer with bond length 2.35 Å. This is ASSUMPTION/UNVERIFIED:
     no card gives Si reconstruction geometry (all cards say NOT IN THIS DOCUMENT).

Scale estimate (DERIVED_HERE arithmetic; the run prints the actual values). Assumed inputs: W0 ≈ 0.5 V,
which is UNVERIFIED and comes from the absorption card via potential.py, and σ ≈ 7.3e-4 rad/(V·Å).
- Λ_abs ≈ 30 Å, so D ≈ 120 Å.
- L ≈ 5–6×10³ Å, i.e. ≈ 3000 slices.
- H_vac ≈ 200 Å.

## 3. Specular extraction (2e)
- **Vacuum field.** The vacuum G_y = 0 field is a_inc[e^{−iK_z(z−z_s)} + r e^{+iK_z(z−z_s)}]·e^{−iπλq²x}.
  This is Peng 5.109 [card:peng_ch05, p.38], with z flipped to point outward.
- **Projection.** r is a Hann-windowed projection of the y-averaged exit wave onto e^{+iK_z(z−z_s)} over
  the steady band. It is then divided by a_inc·e^{−iπλq²L}.
- **Phase reference.** The top atomic plane z_s.
- **Paraxial error.**
  - Incident and specular share |q|, so the common error ~kLα⁴/8 cancels. Without the cancellation
    this term is about 0.3 rad over 5000 Å at 40 mrad.
  - The residual comes from the internal-angle path inside D. Its estimate is (k/8)(D/tanθ_i)(θ_i⁴ − θ_e⁴),
    which is ≪ 0.01 rad. This is DERIVED_HERE from Kirkland 6.65 and is unverified numerically until
    the convergence run.
- **Validation of the extraction.** A synthetic-wave round trip (test, 1e-3), and a vacuum-only run
  giving r ≈ 0 (< 1e-2).

## 4. Tests in scope
| Test | External fact | Tolerance |
|---|---|---|
| T-unitarity (vacuum) | Kirkland 6.73: free propagation conserves flux | 1e-6 |
| T-unitarity (crystal, W=0, no absorber) | unitary t and P [card:kirkland_ch06, p.52] | 1e-6 per slice |
| T-unitarity (W=0, absorber on) | Darwin total reflection band [card:peng_ch05, p.30] | max\|r\| = 1 ± 1e-3 |
| T-kinematic | calculator 4b: (0,0,12) at 26.420 mrad; peak below vacuum Bragg 27.711 mrad [card:peng_ch05, p.29] | 0.5 mrad |
| T-convergence | Kirkland sampling invariance | ΔR < 0.02, Δarg < 0.1 rad |
| T-published | no Si curve on any card | strict xfail |

Notes on the table:
- **T-unitarity, absorber-on case.** This deviates from the task wording "|r|=1 below θ_c". The repo
  conventions state that every external beam enters with θ_int ≥ θ_c, so no external angle lies below
  θ_c. The Darwin total-reflection band is used instead.
- **T-published.** Peng's READ-FROM-PLOT curves are for Ag(001), NiO, UO₂ and Pt(111). Reproducing them
  needs non-Si potentials, which are out of scope. The ±1–2 mrad plot-reading uncertainty is recorded
  in the cards.

## 5. Convergence protocol
The base is the default sampling: dx 1.92 Å, dz 0.08 Å, dy 0.15 Å, vacuum and L from the criteria.
Each variant is run separately at the (008) kernel peak:
- dx/2;
- dz/2 and dy/2;
- 2× vacuum;
- 2× L (with 2× vacuum).

`run_R2.py` prints |r|², Δ|r|², arg r and Δarg for each variant.

## 6. Expected timing (estimate, not measured)
- **Per-slice cost.** Two FFTs of nz·ny ≈ 3840 × 26 points, a few ms each.
- **Per angle.** ≈ 3000 slices, i.e. ≈ 10–30 s.
- **100-angle default curve.** ≈ 20–50 CPU minutes.
- **`--quick`.** About 4× faster.

The script prints the measured seconds per angle and the extrapolated 100-angle time per target. If
the measured time exceeds "minutes", the levers are, in order of priority:
- n_depth 4 → 3;
- dz 0.08 → 0.1, which the (0,0,12) bandwidth still allows;
- w_extract 20 → 10 Å.

Each change must be re-checked against the convergence table.
