# Reflection ptychography and off-axis reflection electron holography: literature, theory, simulation

All data in this report are **simulated** from the forward models derived below; no experimental data were used.

**Summary.** In both techniques the reflection geometry acts the same way. It turns the surface into a strongly foreshortened, angle-sensitive phase object, and the reconstruction is only as good as the geometric model behind it. For EUV reflection ptychography at 70° incidence, a correct tilted-plane mapping is not optional. Replacing it by the paraxial foreshortening approximation raised the object error from 0.14 to 0.94 (NRMSE). An incidence-angle error of 0.25° already roughly doubled the error, and the data residual alone located the angle to about 0.1°. For off-axis reflection electron holography in the Si(111)/(444) Bragg geometry, the kinematic phase 2k·u_z·sin θ_B makes lattice steps phase-invisible at exact Bragg. Fractional displacements remain visible: an 8 pm strain undulation was recovered to 0.15 pm rms. A surface-emergent dislocation appears as a phase vortex whose winding number (4) encodes b_z/d₄₄₄. The dose-limited phase noise matched the analytic shot-noise formula to within about 1% for doses of at least 100 e⁻/px.

---

## 1  Literature survey

### 1.1  Ptychographic phase retrieval

Ptychography started as an iterative scheme for shifting-illumination data ([Rodenburg & Faulkner 2004](https://doi.org/10.1063/1.1823034)). It became a practical high-resolution tool once probe and object were solved jointly ([Thibault et al. 2008](https://doi.org/10.1126/science.1158573); [Maiden & Rodenburg 2009](https://doi.org/10.1016/j.ultramic.2009.05.012)). The algorithm family used here comes from that line: ePIE ([Maiden & Rodenburg 2009](https://doi.org/10.1016/j.ultramic.2009.05.012)) and its regularised successors rPIE/mPIE ([Maiden, Johnson & Li 2017](https://doi.org/10.1364/optica.4.000736)). Overlap redundancy controls convergence ([Bunk et al. 2008](https://doi.org/10.1016/j.ultramic.2007.08.003)).

Statistically grounded and gradient-based solvers form a second branch: nonlinear optimisation with translation diversity ([Guizar-Sicairos & Fienup 2008](https://doi.org/10.1364/oe.16.007264)), maximum-likelihood refinement ([Thibault & Guizar-Sicairos 2012](https://doi.org/10.1088/1367-2630/14/6/063004)), and least-squares ML solvers ([Odstrčil, Menzel & Guizar-Sicairos 2018](https://doi.org/10.1364/oe.26.003108)). Mixed-state decomposition handles partial coherence ([Thibault & Menzel 2013](https://doi.org/10.1038/nature11806)). Multislice models handle thick samples ([Maiden, Humphry & Rodenburg 2012](https://doi.org/10.1364/josaa.29.001606)), and multislice ptychography is now routine in electron microscopy ([Jiang et al. 2018](https://doi.org/10.1038/s41586-018-0298-5)). These extensions matter in reflection because the geometry breaks the thin-object, normal-incidence assumptions they generalise.

### 1.2  Reflection ptychography: geometry is the dominant error source

The reflection literature is driven by tabletop high-harmonic EUV sources and semiconductor metrology. Its central technical theme is the curved, anamorphic mapping between detector pixels and surface spatial frequencies. Gardner et al. introduced tilted-plane correction (TPC) for high-NA reflection-mode coherent diffraction ([Gardner et al. 2012](https://doi.org/10.1364/oe.20.019050)). Seaberg et al. combined TPC with ptychography to image extended surfaces at 45° incidence ([Seaberg et al. 2014](https://doi.org/10.1364/optica.1.000039)), and Zhang et al. extended this to quantitative 3D surface imaging near the wavelength limit ([Zhang et al. 2015](https://doi.org/10.1016/j.ultramic.2015.07.006)). Recent work shows that TPC succeeds or fails on angle calibration. The aPIE algorithm estimates sample–detector tilt within a fraction of a degree ([de Beurs et al. 2022](https://doi.org/10.1364/ol.453655)). Automatic-differentiation (AD) models with tilted propagation inside the forward model jointly refine angle, probe and object, reaching ±0.05° at 70° incidence ([Senhorst et al. 2024](https://doi.org/10.1364/oe.542569)). AD frameworks also enable wavelength-multiplexed, multi-mode reconstructions with more than 200 million parameters ([Shao et al. 2024](https://doi.org/10.1038/s41377-024-01558-3)). Axial-distance calibration likewise improves resolution ([Chen et al. 2023](https://doi.org/10.1016/j.optlaseng.2023.107684)).

The same geometry has moved to other spectral ranges. Hard X-ray grazing-incidence ptychography combines imaging with GISAXS-like surface sensitivity over large fields ([Jørgensen et al. 2024](https://doi.org/10.1364/optica.505478)). A follow-up preprint replaces the projection model with grazing-incidence multislice ([Besley et al. 2025, arXiv:2510.06877](https://arxiv.org/abs/2510.06877)). Soft X-ray reflection ptychography has been demonstrated at ~45 nm full-pitch resolution (preprint: [Guenzing et al. 2026, arXiv:2601.20261](https://arxiv.org/abs/2601.20261)).

The most consequential recent result is theoretical. Senhorst, Witte & Coene show that the 2D thin-sample model "quickly breaks down" in reflection ([Senhorst et al. 2026](https://doi.org/10.1364/oe.601179)). Ewald-sphere rotation, rather than curvature, dominates the sampled axial frequencies, so the allowed thickness shrinks by one to two orders of magnitude compared with transmission. Multilayer interference is a related failure of the single-surface model ([Gao et al. 2024, arXiv:2412.11247](https://arxiv.org/abs/2412.11247)).

### 1.3  Reflection electron microscopy and holography

Reflection electron microscopy (REM) images surfaces with near-grazing Bragg-reflected electrons, giving strong foreshortening and contrast from steps and dislocations ([Osakabe et al. 1981](https://doi.org/10.1016/0039-6028%2881%2990038-8); [Cowley & Peng 1985](https://doi.org/10.1016/s0304-3991%2885%2980008-5); [Peng, Cowley & Hsu 1987](https://doi.org/10.1016/0739-6260%2887%2990054-2)). Standard references are the monographs by [Wang 1996](https://doi.org/10.1017/cbo9780511525254) and [Ichimiya & Cohen 2004](https://doi.org/10.1017/cbo9780511735097). Off-axis electron holography with the Möllenstedt biprism ([Möllenstedt & Düker 1956](https://doi.org/10.1007/bf01326780)) was applied in reflection by Osakabe, Tonomura and co-workers. They detected surface undulation from the single-atomic shear of a dislocation, a picometre-scale height signal ([Osakabe et al. 1989](https://doi.org/10.1103/physrevlett.62.2969); [Osakabe 1993](https://doi.org/10.1016/0039-6028%2893%2990047-n)). Banzhof & Herrmann developed reflection holography in a TEM ([Banzhof & Herrmann 1993](https://doi.org/10.1016/0304-3991%2893%2990123-f)), and Cowley discussed holographic diffraction for surface studies ([Cowley 1993](https://doi.org/10.1016/0039-6028%2893%2990046-m)).

The reconstruction and noise theory used here comes from transmission holography: Fourier sideband demodulation ([Takeda, Ina & Kobayashi 1982](https://doi.org/10.1364/josa.72.000156)) and the off-axis holography tutorial with its phase-noise analysis ([Lehmann & Lichte 2002](https://doi.org/10.1017/s1431927602020147)). Reviews cover applications ([Tonomura 1987](https://doi.org/10.1103/revmodphys.59.639); [Midgley & Dunin-Borkowski 2009](https://doi.org/10.1038/nmat2406)), and biprism engineering has continued to develop ([Harada 2005](https://doi.org/10.1093/jmicro/dfh098); [Röder et al. 2016](https://doi.org/10.1016/j.ultramic.2015.11.004)). Blackburn & McLeod compared high-resolution electron ptychography directly with off-axis holography in transmission ([Blackburn & McLeod 2020](https://doi.org/10.1093/jmicro/dfaa055)).

### 1.4  Gaps

Three gaps follow from the survey; the simulations below address parts of each.

1. **Reflection electron ptychography.** The Crossref/arXiv keyword sweep found no paper doing ptychography with Bragg-reflected electrons in REM/RHEED geometry, although both ingredients are mature. Foreshortening at θ_B ≈ 1° is about 20× worse than at 70° EUV incidence. The angle-calibration and thin-surface problems documented for EUV ([Senhorst et al. 2024](https://doi.org/10.1364/oe.542569); [Senhorst et al. 2026](https://doi.org/10.1364/oe.601179)) should therefore be far more severe. Treat the gap with caution: the search did not cover conference abstracts or full-text databases.
2. **Quantitative REH beyond kinematic phase.** The 1989–1993 reflection-holography work interpreted phase kinematically. Dynamical RHEED effects (surface resonance, refraction by the mean inner potential, step-contrast mechanisms from [Cowley & Peng 1985](https://doi.org/10.1016/s0304-3991%2885%2980008-5)) have not been built into a holographic inversion. The survey found no modern REH work with direct electron detectors and modern noise analysis.
3. **Reflection holography vs reflection ptychography.** Blackburn & McLeod's comparison was done in transmission ([Blackburn & McLeod 2020](https://doi.org/10.1093/jmicro/dfaa055)). No equivalent dose-normalised comparison exists in reflection.

---

## 2  Theory

### 2.1  Reflection ptychography forward model

**Geometry.** The surface is z = 0, and the plane of incidence is xz. The angle of incidence θ is measured from the surface normal. The incident wavevector is **k**_in = k(sin θ, 0, −cos θ), and the specular direction is **e**₃ = (sin θ, 0, cos θ). The detector is normal to **e**₃ at distance L, with in-plane axes **e**₁ = (cos θ, 0, −sin θ) and **e**₂ = ŷ.

**Exit-surface wave (2D / thin-surface approximation).** The exit wave is ψ_s(x,y) = P_s(x,y)·O(x,y), with O = r(x,y)·exp[i·2k h(x,y) cos θ]. Here r is the local Fresnel reflectivity and h the height; the factor 2 cos θ is the round-trip path. The surface probe is the 3D beam evaluated on the tilted plane: P_s(x,y) = P_beam(u = x cos θ, v = y; w = x sin θ). The footprint is therefore stretched by 1/cos θ, and its focus varies across the footprint (in the code, an exact angular-spectrum evaluation column by column). The 2D approximation fails for thick structures ([Senhorst et al. 2026](https://doi.org/10.1364/oe.601179)). The 4 nm features simulated here stay within it.

**Far field and tilted-plane mapping.** The outgoing direction is **α** = (X**e**₁ + Y**e**₂ + L**e**₃)/R, with R = √(X²+Y²+L²). The detector amplitude is Ψ(X,Y) = ℱ[ψ_s](f_x, f_y), with

  f_x = [(X cos θ + L sin θ)/R − sin θ]/λ,  f_y = Y/(Rλ),

and the pixel intensity is |Ψ|²·|∂(f_x,f_y)/∂(X,Y)|. The paraxial limit f_x ≈ X cos θ/(λL), f_y ≈ Y/(λL) is pure foreshortening. The higher-order terms bend the detector grid (Fig. 1a). The inverse map, needed for TPC, is

  α = (λf_x + sin θ, λf_y, α_z),  X = L(α·**e**₁)/(α·**e**₃),  Y = L(α·**e**₂)/(α·**e**₃).

**Consequences.**
- *Anisotropic resolution.* For λ = 13.5 nm, θ = 70° and detector NA ≈ 0.26, the measured band is λf_x ∈ [−0.146, +0.056] (width 0.202) and λf_y ∈ ±0.256 (width 0.512). The full-period resolution is therefore about 67 nm along the beam and 26 nm across it.
- *Asymmetric band.* The band is not centred on specular, because the grazing side of the detector saturates as α_x → 1.
- *Grid matching.* A reconstruction grid with isotropic pixel λL/(Np) leaves about 69% of its Fourier window unmeasured. Those unconstrained coefficients created a probe/object ambiguity: the residual was low but the reconstruction was wrong (NRMSE 0.66). Using anisotropic pixels (d, 2d) raised the measured fraction to 61% and removed the failure. In practice, choose the reconstruction grid to match the TPC-mapped band.
- *Angle sensitivity.* ∂f_x/∂θ ≈ −cos θ/λ + … shifts and warps the whole mapped band. To first order a pure shift is the benign linear-phase-ramp ambiguity of ptychography. The warp is not benign, so θ must be known to well below the angular size of a detector pixel (p/L ≈ 0.24° here).
- *Height sensitivity.* ∂φ/∂h = 4π cos θ/λ = 0.32 rad/nm at 70°; sensitivity is traded against footprint and resolution through cos θ.

**Reconstruction.** Detector intensities are divided by the Jacobian and interpolated (cubic) onto the uniform (f_x, f_y) grid of the reconstruction window. The modulus constraint is applied only inside the mapped band; unmeasured coefficients float. The updates are rPIE ([Maiden, Johnson & Li 2017](https://doi.org/10.1364/optica.4.000736)), and ePIE is the special case α = β = 1.

### 2.2  Off-axis reflection electron holography

**Geometry and foreshortening.** The beam strikes the surface at the Bragg angle θ_B of a surface-normal reflection (hkl). At 200 kV, λ = 2.508 pm. For Si (444), d = 78.39 pm and θ_B = 16.00 mrad (0.92°). An image coordinate ξ along the beam maps to surface x = ξ/sin θ_B, a foreshortening of 62.5×.

**Kinematic phase of a surface displacement.** A normal displacement u_z(x,y) changes the path of the reflected wave by 2u_z sin θ. The object wave is therefore

  o(x,y) = A(x,y)·exp[iφ],  φ = 2k·u_z·sin(θ_B + δθ).

At exact Bragg, 2k sin θ_B = 2π/d_hkl. This gives three consequences:
- *Lattice steps are phase-invisible.* A step h = n·d₁₁₁ = 4n·d₄₄₄ carries φ = 2π·4n, so contrast at exact Bragg comes only from amplitude effects (and dynamical effects beyond this model).
- *Steps become visible off-Bragg.* A deviation δθ gives φ_step ≡ 2k h cos θ_B·δθ (mod 2π), which is 1.571 rad per d₁₁₁ step at δθ = 1 mrad.
- *Displacement sensitivity.* For a fractional displacement, ∂φ/∂u_z = 2π/d_hkl = 0.080 rad/pm. This is why REH sees the pm-scale shear undulation of [Osakabe et al. 1989](https://doi.org/10.1103/physrevlett.62.2969).

**Dislocation topology.** A dislocation emerging at the surface with normal Burgers component b_z makes u_z a helicoid, so φ winds by 2π·(b_z/d_hkl) around the core. The winding number of the reconstructed wave is a topological integer, m = b_z/d_hkl, and is independent of δθ: off-Bragg, the fractional part reappears as a phase jump along the terminating step.

**Hologram and reconstruction.** The hologram is I = |o|² + 1 + 2μ|o|cos(2π**q**_c·**r** + φ − φ_ref). It is blurred by the detector MTF and recorded with Poisson statistics. The sideband at −**q**_c is isolated with a soft aperture of radius q_c/3, recentred and inverse-transformed, then divided by the reconstruction of an empty reference hologram. That division removes biprism and lens distortions ([Takeda et al. 1982](https://doi.org/10.1364/josa.72.000156); [Lehmann & Lichte 2002](https://doi.org/10.1017/s1431927602020147)).

**Phase-noise limit (derived; checked numerically).** With N₀ e⁻/px, the sideband amplitude is N₀μ_eff/2, where μ_eff = μ·MTF(q_c), and white noise of variance N₀ is passed through an aperture of area fraction a_w = ⟨w²⟩. The phase variance is then 2a_w/(N₀μ_eff²) = 2/(μ_eff²·N_res), with N_res = N₀/a_w electrons per resolution element. Normalising by an equal-dose reference hologram multiplies σ_φ by √2. The height sensitivity is σ_uz = σ_φ·d_hkl/2π.

---

## 3  Simulation results

### 3.1  Reflection ptychography (EUV-like: λ = 13.5 nm, θ = 70°, L = 30 mm, 128² detector, 125 µm pixels)

![Reflection ptychography: geometry, data, reconstructions, angle and dose dependence (simulated data)]({{artifact:dd11f7bd-e3ae-4b2f-a11e-250fb1cf9760})

*Fig. 1 (simulated data).* **a** Detector pixel grid mapped into surface-frequency space: exact (blue) vs paraxial foreshortening (dashed). **b** One measured pattern, 5×10⁶ counts with Poisson noise. **c** The same pattern after TPC on the (d, 2d) reconstruction grid; white is unmeasured. **d–f** Object phase: band-limited truth, TPC + rPIE, and paraxial mapping + rPIE. **g** Object error and data residual vs assumed incidence angle. **h** Object error vs dose, with known and blind probe. NRMSE is computed inside the directly measured band, after removing the global complex scale and linear phase ramp. 78 scan positions; 400 iterations in d–f and h, 300 in g.

Test surface: Siemens star, 300/200/140 nm gratings in both orientations, and a ring, with 4 nm height, a material contrast of 0.35 → 0.60 reflectivity plus 0.8 rad intrinsic phase, and 0.4 nm rms roughness. The true probe is a soft aperture with 1.8π defocus and trefoil, evaluated exactly on the tilted plane. The blind reconstructions start from a probe with the defocus 20% wrong and no trefoil.

| Condition (blind probe, 5×10⁶ counts) | NRMSE, 3 seeds | median |
|---|---|---|
| TPC + rPIE | 0.139, 0.398, 0.177 | 0.177 |
| TPC + ePIE | 0.258, 0.364, 0.137 | 0.258 |
| Paraxial foreshortening + rPIE | 0.942, 0.879, 0.836 | 0.879 |

Findings:
- **TPC is essential at high NA.** The paraxial mapping fails (NRMSE 0.84–0.94; data residual about 25× higher). The failure comes from the curvature terms of the mapping, not from foreshortening itself.
- **Angle calibration.** Object error at the best-residual seed rises from 0.13 at the true angle to 0.17–0.18 at ±0.1° and 0.27–0.35 at ±0.25°. Fitting a parabola to the residual minimum gives an angle offset of +0.12°, consistent with the ~0.1° grid. This is a residual-based self-calibration in the spirit of aPIE ([de Beurs et al. 2022](https://doi.org/10.1364/ol.453655)), though less precise than the ±0.05° from joint AD optimisation reported by [Senhorst et al. 2024](https://doi.org/10.1364/oe.542569).
- **Blind probe recovery is the fragile part.** Some runs stall in a worse state (e.g. 0.40). Those runs have about 2.8× higher residual, so multi-start selection by residual is a workable remedy, though not a perfect one. A flat-phase initial probe failed outright (NRMSE 0.99). With a known probe the median error falls from 0.81 at 10⁴ counts to 0.083 at 5×10⁶. A systematic floor of about 0.09, from intensity resampling and band-edge effects, limits higher doses.
- **rPIE vs ePIE.** At equal iteration count, rPIE had a lower median error (0.18 vs 0.26). Both reach the same best case (~0.14).

### 3.2  Off-axis reflection electron holography (200 kV, Si(111) surface, (444) reflection)

![Reflection electron holography: hologram, sideband, phase maps, noise limit and undulation recovery (simulated data)]({{artifact:905ca77e-d496-4511-a275-1a6217229ada})

*Fig. 2 (simulated data).* **a** Hologram crop (fringe period ≈ 4 px = 1 nm). **b** Hologram spectrum and sideband aperture. **c** Phase noise vs dose: simulation (flat object, 2 seeds) vs theory; the right axis converts to σ_uz. **d, e** Reconstructed phase at exact Bragg and at +1 mrad off-Bragg, in surface coordinates (note the 62.5× foreshortening of the x axis). **f** Recovered strain undulation profile vs truth. Settings: μ = 0.35, Gaussian MTF σ = 0.7 px (MTF(q_c) = 0.54), 1024² px of 0.25 nm (object-referred), N₀ = 500 e⁻/px for d–f.

Surface model:
- four meandering d₁₁₁ = 0.314 nm steps;
- one emergent dislocation with b_z = d₁₁₁;
- an illustrative 8 pm antisymmetric undulation of the form produced by a dislocation line buried 15 nm deep (not an elastic solution), with amplitude contrast at steps, core and strain field.

Findings:
- **Steps invisible at Bragg, visible off-Bragg.** Phase jumps change by −1.534, −1.475 and −1.518 rad per step from exact Bragg to δθ = +1 mrad. The kinematic prediction is −1.571 rad; the residual 2–6% comes from the global helicoid of the dislocation, which the ideal-wave control reproduces. Across all steps the reconstruction matches the ideal wave to ≤ 0.014 rad.
- **Topological readout.** The winding number around the dislocation core is exactly 4.00 at both angles, equal to b_z/d₄₄₄. A control loop away from the core gives 0.00.
- **pm sensitivity.** The 8 pm undulation is recovered with peak and trough of +8.05 and −8.13 pm, and 0.15 pm rms error after removing the arbitrary phase offset (190-column average).
- **Shot-noise limit validated.** Simulated σ_φ matches √2·√(2/(μ_eff²N_res)) to within 1% for N₀ ≥ 100 e⁻/px and within 2% at 30 e⁻/px. At 5 e⁻/px the simulation is 18% above theory, where the small-noise linearisation fails. At N₀ = 500 e⁻/px, theory gives σ_φ = 0.066 rad, i.e. σ_uz = 0.83 pm per resolution element (≈ 3 nm across the beam × 190 nm along it).

---

## 4  Limitations and next steps

Limitations:
- Both models are kinematic and 2D. The REH phase ignores dynamical RHEED effects (surface resonance, mean-inner-potential refraction, and the step-contrast mechanisms of [Cowley & Peng 1985](https://doi.org/10.1016/s0304-3991%2885%2980008-5)). Defocus variation along the tilted surface and Fresnel fringes from the biprism edge are also omitted.
- The ptychography model assumes a fully coherent probe, a point-like detector and integer scan positions.
- No experimental data were used. The dislocation undulation is an illustrative functional form, not an elasticity solution.

Natural next steps, in order of expected value:
1. Replace TPC resampling with an AD forward model that includes tilted propagation, then jointly refine θ, probe modes and positions. This would remove the ~0.09 interpolation floor and the seed fragility.
2. Simulate reflection electron ptychography at θ_B ≈ 16 mrad using the same machinery. Assess whether a multislice-in-reflection model is required, in the sense of [Senhorst et al. 2026](https://doi.org/10.1364/oe.601179).
3. Run a dose-normalised comparison of REH vs reflection ptychography on the same surface.
4. Benchmark gradient/ML-based solvers against rPIE on these datasets.

## Files
- [refl_ptycho.py]({{artifact:f58ecd6a-1ab2-4b28-b3c0-82b3d72186df}}): reflection ptychography forward model, TPC, rPIE/ePIE, metrics.
- [run_ptycho_experiments.py]({{artifact:c6428a44-eb33-4b5a-a30b-5fcfeceb31e8}}): reproduces all ptychography numbers.
- [refl_holo.py]({{artifact:ccb23133-411b-451b-9dff-1b3cedc9d24d}}): REH geometry, surface model, hologram formation, sideband reconstruction, noise theory.
- [ptycho_results.json]({{artifact:54db4d1e-7285-41e5-8f5f-98823e610e1a}}), [ptycho_results.npz]({{artifact:92a4f8ca-7cbd-41b4-9db0-3f453d49a987}}), [holo_results.npz]({{artifact:a2ee1448-ca6e-4007-8022-7a0afc1d407d}}): simulated results.
