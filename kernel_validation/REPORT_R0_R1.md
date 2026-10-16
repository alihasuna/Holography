# REPORT R0–R1 — error budget and geometry (Si, HF-3300, 200 keV)

All numbers below are printed by `scripts/run_R0.py` or `scripts/run_R1.py`; the expected outputs
are reproduced in section 3. **Honesty note:** these expected outputs were derived by hand from the
code and from the attached calculator output; they were not executed in this authoring session.
Digits may differ by ±1 in the last printed place. The pytest tolerances in section 4 are the binding checks.

## 1. Error budget (R0) — Si(001) specular (0,0,8), 200 keV

### Separation criterion
Two hypotheses whose predicted phases differ by D, taken as a circular distance, are separable when
|D| ≥ 5σ. This is an ASSUMPTION; with a midpoint decision the misclassification rate is 0.6 %.
The required precision is therefore σ = |D|/5.

### Achievable precision: inputs used
Every achievable entry uses placeholders, because each of these inputs is MISSING:

| Input | Placeholder | Basis |
|---|---|---|
| V0 | 12 V | repository ASSUMPTION |
| fringe contrast | 0.3 | ASSUMPTION |
| camera MTF at the carrier | 0.5 | ASSUMPTION |
| drift | 0.05 fringe rms | ASSUMPTION |
| convergence | 1e-6 rad | Shindo & Tomita p.31, a different instrument; the HF-3300 cards give no number |
| dose | 100 e/px | ASSUMPTION |
| terrace area | 1000 px | ASSUMPTION |
| energy spread | 0.45 eV | HF-3300 card, voltage unstated / 300 kV |
| reference | vacuum | ASSUMPTION |

| comparison | required sigma_phi | achievable sigma_phi | feasible? | limiting input |
|---|---|---|---|---|
| (a) Si(001) a/4 vs a/2 step at (0,0,8) | 0.272 rad | 0.0443 rad | YES (N_min = 2.66e+03 e) | items 6, 16 (dose, fringe contrast); a/4 terraces are 4_1-screw related, dynamical residual not included (R2) |
| (b1) V0 12 vs 13 V: (0,0,8) peak shift -0.178 mrad | 35.5 urad in theta_ext (angle) | not computable from the cards | UNDETERMINED | items 7, 9 (angle calibration, measured rocking curve) |
| (b2) V0 12 vs 13 V: a/2 step phase at the peak | 0.0483 rad | 0.0443 rad | YES (N_min = 8.41e+04 e) | items 6, 16; equivalent to locating the peak to 35.5 urad (item 7) |
| (c) overlayer 0 vs 1 nm, reduced-density layer (ASSUMPTION) | 0.363 rad | 0.0443 rad | YES if the reference avoids the layer (reference_trajectory = vacuum) (N_min = 1.49e+03 e) | items 12, 15 (layer state, reference trajectory); layer absorption item 21 |

### Reading the budget
1. **(a) is robust.** Discriminating the a/4 and a/2 steps needs only about 2.7e3 electrons per
   terrace at the placeholder contrast.
   - The geometric phases are +1.359 and +2.718 rad.
   - The a/4 terraces are related by the 4_1 screw (calculator §2b). Their dynamical phases
     therefore differ by an amount R2 must quantify. If that residual approaches 1.36 rad, the
     comparison fails, whatever the dose.
2. **(b) is one measurement, not two.**
   - At a fixed external angle the geometric step phase is independent of V0.
   - V0 moves the (0,0,8) peak by −0.178 mrad per volt.
   - The step phase taken *at the peak* changes by 0.242 rad, which is (dφ/dθ = 1360.4 rad/rad) × Δθ.
   - So (b2) is only as good as the angle calibration (item 7/9). The angle requirement is 35.5 µrad.
   - The phase margin is thin: 0.0443 vs 0.0483 rad. It is feasible only with N ≥ 8.4e4 e per terrace.
3. **(c) depends on the reference trajectory (item 15).**
   - The modelled layer adds +8.097 rad, i.e. +1.814 rad wrapped. The model is t = 1 nm,
     V_layer = 0.8 V0, refraction only, no internal reflections.
   - That is easily measurable *if* the reference does not cross the layer.
   - Osakabe's reference was "a diffracted beam from an area with no imperfections"
     [osakabe1993 p.5]. With such a reference a conformal layer is common-mode and phase-blind.
   - Layer absorption, which changes the contrast, cannot be computed because the absorptive
     parameters are MISSING (item 21).
4. **Illumination convergence is not limiting at the placeholder.** The coherence envelope for the
   a/2 step falls to 0.5 only at a 0.865 mrad Gaussian spread.
   - The HF-3300 cards give no convergence number.
   - The 18–27 mrad tableau tilts and the 20 mrad STEM α are not holography illumination.
   - Item 3 therefore stays blocking until it is measured.
5. **Energy spread is negligible.** It produces 2.9e-5 rad of a/2 step-phase spread.
6. **Cross-check on the noise level.** The placeholder σ_terrace of 0.0313 rad is of the same order
   as the ±0.03 rad that Shindo & Tomita report in a Si substrate (transmission)
   [ch06 p.46/pr.60]. This is a plausibility anchor only.
7. **V0 itself is suspect.** The neutral-atom V0 implied by the Peng parameters that R2 will use is
   13.91 V (DERIVED_HERE, printed by run_R1). That is 1.9 V above the 12 V placeholder, which is
   larger than the 1 V separation in (b). R2 must report which V0 its potential actually contains
   (spec 4.3.6).

### Formula provenance
| Formula | Label and source |
|---|---|
| σ_region = √2/(μ√N) | from repo calculator §10, where it is DERIVED_HERE; no card states a dose–noise law, so UNVERIFIED |
| step = two regions (×√2) | DERIVED_HERE |
| drift and convergence envelopes | Gaussian averages of e^{iδφ}, DERIVED_HERE |
| dφ/dθ = 2hk cosθ | the task's (4πh/λ)cosθ |
| overlayer phase 2t(K_L − K_ext) | DERIVED_HERE; the model is an ASSUMPTION |

## 2. Geometry (R1) summary

### Constants and frames
- λ, σ and γ are relativistic.
  - λ reproduces Shindo & Tomita App. A (0.00250793 nm) and the parallax card (2.508 pm).
  - σ reproduces Shindo & Tomita App. A (0.0072884 V⁻¹nm⁻¹). Its form is identical to their eq. 4.3.
- Frames follow the CONTRACT: rows are x_beam, y, z_normal, with an outward normal; handedness and
  in-plane azimuth are asserted.
  - The README "(1,1,-1)" facet is rejected.
  - The mapping to the conventions-document frame is tested.

### Refraction
- The non-negotiable form is used: dK² = 2γm₀eV0/ħ².
- It is tested equal to k²Δ, with Δ = 6.98e-5. Δ is 16 % above V0/T.
- θ_c = 8.356 mrad (internal).
- The calculator's exact (T+U)(T+U+2E0) kinematics differ by 8.4e-6 in dK². That is invisible at
  every calculator tolerance, but it can flip the last printed digit of the low-angle (0,0,4) row.

### Rods
- Si(1,−1,1): allowed n ≤ 12 are 1, 3, 4, 5, 7, 8, 9, 11, 12.
  - (1,−1,1) is inaccessible.
  - (2,−2,2), (6,−6,6) and (10,−10,10) are refused by the guard.
  - The legacy (6,−6,6) numbers (T4/T6/T10/T14/T20) are reproduced only with an explicit
    `allow_forbidden=True`.
- Si(001): (004), (008), (0,0,12) and (0,0,16) are allowed.
- (2,−2,0) is inaccessible in reflection: G·n = 2.6718 < 2dK = 4.1868 rad/Å.
- G·R/2π = 1 for that reflection.

### Lattice parameter
- a = 5.4309 Å is an ASSUMPTION. No card prints a Si lattice parameter; this is the repository
  default, kept so the calculator is reproducible.

### Debye–Waller factor
- B(300 K) = 0.5261 Å², from the Peng ch.14 Table 14.2 polynomial.
- The 80 K fit-boundary mismatch is 0.93 %.

## 3. Commands and expected output

`python scripts/run_R0.py` (no flag) → exit code 2:
