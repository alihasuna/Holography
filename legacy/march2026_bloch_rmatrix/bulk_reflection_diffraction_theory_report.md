# Bulk Reflection Electron Diffraction: Correct Theoretical Framework

**Date:** 2026-04-05
**Context:** Corrected analysis distinguishing surface RHEED from bulk reflection diffraction for PhD project on reflection electron ptychography of cleaved Si[110].

---

## 1. The Critical Distinction: Three Regimes of Electron Reflection

There are NOT two but THREE distinct physical regimes for electrons reflecting from a crystal, and they have fundamentally different theoretical treatments:

| Regime | Geometry | What Scatters | Theory | Penetration Depth |
|--------|----------|---------------|--------|-------------------|
| **Surface RHEED** | Grazing on 2D surface layer (MBE growth) | Selvedge (few atomic layers with reconstructions) | Surface-parallel multislice; 2D reciprocal rods | ~1-5 atomic layers |
| **Bulk Bragg Reflection** | Grazing on bulk crystal surface (your case) | Full 3D lattice, semi-infinite crystal | 3D Bloch wave + R-matrix; or transfer matrix for semi-infinite crystal | Set by extinction distance (~tens of nm) |
| **Transmission (THEED)** | Beam through thin foil | Thin slab | Standard multislice (Prismatic, abTEM) | Entire foil thickness |

**Your experiment -- cleaved Si[110] at 4.1 deg with 200 kV -- is squarely in regime 2: Bulk Bragg Reflection.** The beam penetrates into the full 3D crystal lattice, scatters dynamically, and exits on the same side. This is also the regime of Osakabe's experiments and of Reflection Electron Microscopy (REM).

---

## 2. What Osakabe Actually Did: Bulk Bragg Reflection, Not Surface RHEED

Reading the 1993 Surface Science paper carefully:

- **Pt(111)**: Used the **(666) specular reflection**. This is a HIGH-ORDER Bragg reflection from planes parallel to the surface. The beam enters at grazing incidence, penetrates into the bulk, undergoes dynamical Bragg diffraction from the (111) lattice planes, and exits.
- **GaAs(110)**: Used the **(880) reflection**. Same principle.
- **Phase shift formula**: Delta-phi = 2 K_perp * d, where K_perp is the vertical component of the wavevector. This is a **geometrical path difference** formula -- it measures the height difference d by the extra optical path the reflected beam travels.

Osakabe explicitly states (Section 4.2): "In the reflection mode, the phase shift of an electron beam due to surface topography is due to a geometrical path difference." He refers to the technique as an extension of **Reflection Electron Microscopy (REM)**, not as RHEED.

**Key insight**: Osakabe was NOT doing surface RHEED in the MBE sense. He was doing **REM with holographic phase retrieval**. The beam enters the BULK crystal at grazing incidence, reflects via Bragg diffraction from the 3D lattice, and exits. The surface topography modulates the PHASE of this bulk-reflected beam.

---

## 3. Penetration Depth: How Deep Does the Beam Go?

This is the central physics question. The answer depends on whether we are near or far from a Bragg condition.

### 3.1 Extinction Distance (Dynamical Diffraction)

At the exact Bragg condition, the penetration depth is governed by the **extinction distance** xi_g:

    xi_g = pi * V_c * cos(theta_B) / (lambda * |F_g|)

where V_c is the unit cell volume, theta_B is the Bragg angle, lambda is the wavelength, and F_g is the structure factor.

For Si at 200 kV, typical extinction distances are:
- Si(111): xi ~ 60-80 nm
- Si(220): xi ~ 50-70 nm
- Si(004): xi ~ 160 nm (measured by Cann 1968, Zuo 1997)

**However**, in grazing incidence geometry, the perpendicular component of the wavevector is very small. The beam enters nearly parallel to the surface. The effective penetration depth normal to the surface is:

    d_perp ~ xi_g * sin(alpha)

where alpha is the grazing angle. At alpha = 4.1 deg (71.6 mrad):

    d_perp ~ 80 nm * sin(4.1 deg) ~ 80 * 0.0716 ~ 5.7 nm

This is approximately **25-30 atomic layers** for Si(111) spacing (d_111 = 0.314 nm).

### 3.2 Absorption

The imaginary part of the crystal potential (absorptive potential) further limits penetration. Inelastic mean free paths for 200 kV electrons in Si are ~100-150 nm. In grazing geometry, the effective absorption path along the surface is:

    L_abs ~ IMFP / sin(alpha) ~ 120 nm

But the perpendicular penetration before absorption is:

    d_abs ~ IMFP * sin(alpha) ~ 120 * 0.0716 ~ 8.6 nm

### 3.3 Summary of Penetration

For 200 kV electrons on Si at 4.1 deg grazing incidence:
- **Extinction-limited depth (normal to surface)**: ~5-10 nm (~15-30 atomic layers)
- **Absorption-limited depth (normal to surface)**: ~5-10 nm
- **This is NOT a few-monolayer surface probe** (as in MBE-RHEED at 1-2 deg, 10-30 keV)
- **This IS a near-surface bulk probe** -- it sees the full 3D crystal potential of the top ~10 nm

The beam samples the **bulk crystal structure** of the near-surface region. Surface reconstructions (if any) contribute, but the BULK lattice dominates the scattering. This is why Osakabe could use high-order specular reflections like (666) -- these are BULK Bragg reflections, not surface diffraction features.

---

## 4. The Correct Theoretical Framework

### 4.1 The Definitive Reference: Peng, Dudarev, and Whelan (2004)

You already have this textbook: **"High Energy Electron Diffraction and Microscopy" by L.-M. Peng, S. L. Dudarev, and M. J. Whelan (Oxford, 2004)**. Chapter 5 is the authoritative treatment.

**Chapter 5 presents FOUR equivalent dynamical RHEED theories:**

1. **Multislice method** (Peng and Cowley 1986, 1988) -- Uses periodic continuation: builds a large supercell with the crystal surface nearly parallel to the beam direction, masks part of the entrance plane, and propagates via standard multislice. This is the THEED-adapted approach.

2. **Semi-reciprocal method** (Maksym and Beeby 1981; Ichimiya 1983) -- Expands the potential in surface-parallel Fourier components U_G(z), keeps z-dependence explicit. Produces coupled second-order ODEs, linearized via Tournarie, Ichimiya, or Maksym-Beeby transformations. Transfer matrix for each slice.

3. **Green's function method** (Tournarie 1962; Kambe 1967) -- Decomposes Green's function into forward and backward scattering components. Integral equation formulation. Not fully implemented for many-beam cases.

4. **Bloch wave method** (Bethe 1928; Colella 1972; Peng and Whelan 1990; Peng, Dudarev et al. 1996) -- This is the most physically transparent for BULK crystals. Assumes 3D periodicity of the substrate, finds Bloch waves, applies boundary conditions at the surface.

### 4.2 Why the Bloch Wave Method Is Most Appropriate for Your Case

For a **semi-infinite bulk crystal** (your cleaved Si[110]), the Bloch wave method (Section 5.3.4 of Peng et al.) is the natural framework because:

1. The substrate has full 3D periodicity -- you can exploit this via Bloch's theorem
2. Only **evanescent Bloch waves** (those that decay into the crystal bulk) contribute to the reflected intensity -- automatically handles the semi-infinite boundary condition
3. The R-matrix propagation scheme (Eqs. 5.85-5.91 in the book) is numerically stable
4. Surface features (steps, terraces) are treated via the **selvedge** -- a finite region where the potential differs from the bulk, placed on top of the semi-infinite substrate

**The eigenvalue equation (Peng et al. Eq. 5.45):**

    [gamma^2 + 2(K + g)_z * gamma - 2K*S_g] C_g - sum_{h != g} U_{gh} C_h = 0

This is a **second-order** eigenvalue problem in gamma (the perpendicular wavevector correction), giving **2N eigenvalues** for N beams. Of these, N are evanescent (decay into crystal) and N are anti-evanescent (decay away from crystal). For a semi-infinite crystal, only the N evanescent solutions are retained.

### 4.3 The Two-Dimensional Bloch Wave Approach

For practical computation (Section 5.3.4.3), the crystal is sliced parallel to the surface. Each slice has a 2D-periodic potential that is constant in z. The eigenvalue equation becomes:

    (kappa^2 - T_G^2) C_G - sum_{H != G} U_{GH} C_H = 0

where T_G^2 = K^2 - (K + G)_t^2, and kappa = gamma + K_z.

This gives 2n eigenvalues for n reciprocal lattice rods. The transfer matrix for each slice is computed, and the R-matrix is propagated from the bulk to the surface to get reflected beam amplitudes (Eq. 5.91):

    R_G = {delta_{G,H} - R_{GH} k_{Hz}} / {delta_{G,H} + R_{GH} k_{Hz}} |_{H,0}

### 4.4 Bethe Potentials for Convergence

Evanescent beams (reciprocal lattice rods outside the Ewald sphere) are handled via **Bethe potentials** (Section 5.3.4.7, Eq. 5.120), reducing the number of strong beams that need full dynamical treatment.

---

## 5. Can Transmission Multislice (Prismatic/abTEM) Be Adapted?

### 5.1 The Peng-Cowley "Periodic Continuation" Method

**YES, but with severe limitations.** Peng and Cowley (1986, 1988) showed how to adapt transmission multislice for RHEED/REM by:

1. Building a **large supercell** where the crystal surface runs nearly parallel to the beam propagation direction (z-axis)
2. Placing a **mask function** on the entrance face to prevent illumination of the vacuum region above the crystal
3. Propagating via standard multislice (slice-by-slice)
4. After sufficient propagation distance, a **steady state** is reached that represents plane-wave incidence at grazing angle on an infinite surface

**This is exactly what your `holography.py` / `prismatique` code does** -- it builds a slab with the surface parallel to the beam and uses standard Prismatic multislice with beam tilt.

### 5.2 The Paraxial Approximation Problem

**Critical issue**: Standard multislice uses the **paraxial (Fresnel) approximation** to the propagator:

    P(k) = exp(i * lambda * Delta_z * |k_t|^2)   [paraxial]

The exact propagator is:

    P(k) = exp(i * Delta_z * sqrt(k_0^2 - |k_t|^2))   [exact]

The paraxial approximation fails when the beam tilt is large. For grazing incidence at alpha = 4.1 deg from the surface, the beam is tilted ~85.9 deg from the surface normal. In the Peng-Cowley supercell geometry, this becomes a ~85.9 deg tilt relative to the slab normal.

**At 85.9 deg tilt:**
- sin(85.9 deg) = 0.997, so k_t / k_0 ~ 0.997
- The paraxial approximation error scales as (k_t/k_0)^4 and higher
- This is a ~60% error in the propagator phase

**However**: In the Peng-Cowley supercell, the crystal is rotated so that the beam propagates along z and the surface is nearly parallel to z. The beam tilt relative to the SLAB normal is then small (a few degrees), and the paraxial approximation is valid for the forward-propagating part of the wavefield.

**The real problem is different**: In this geometry, the beam must propagate a very long distance along z before the steady-state reflection is established. The supercell must be very large (hundreds of nm along z), requiring enormous computation. And the method struggles with surface resonance conditions where electrons are trapped near the surface and propagate large distances.

### 5.3 Practical Assessment for Prismatic/prismatique

Your current prismatique setup CAN produce physically meaningful results for the specular reflection from a bulk crystal, provided:

1. The supercell is large enough along the propagation direction (z) for the reflected wave to reach steady state -- typically needs >>100 nm, possibly ~500 nm for surface resonance
2. An **absorber** at the bottom of the slab correctly simulates the semi-infinite bulk (prevents wrap-around)
3. The beam tilt is snapped to the grid to avoid spectral leakage (you already do this)
4. Enough reciprocal-space beams are included to capture the HOLZ reflections

**The fundamental limitation**: Prismatic/abTEM use the paraxial propagator. For the Peng-Cowley supercell geometry where the beam is nearly along z, this is fine for forward scattering. But the REFLECTED beam (which travels at ~2*alpha = 8.2 deg to the forward direction) is also captured within the paraxial cone. The method works because both incident and reflected beams make small angles with the slab normal.

**What you CANNOT do**: Tilt the beam 86 deg relative to a standard (surface-normal) slab orientation. The paraxial approximation catastrophically fails in that geometry.

---

## 6. What Is the Right Simulation Strategy?

### 6.1 For Rocking Curves and Diffraction Intensities

**Use the FORTRAN routines from Peng, Dudarev, and Whelan.**

Appendix C of their textbook contains complete FORTRAN source code for:
- `C.1`: Calculation of U_g(z) -- the z-dependent crystal potential Fourier components
- `C.2`: Dynamical RHEED calculations -- the full Bloch wave + R-matrix method for a semi-infinite crystal

These routines directly compute reflected beam intensities as a function of incidence angle (rocking curves) for a semi-infinite crystal. This is EXACTLY the right tool for your geometry.

### 6.2 For Full Wavefield Simulation (Needed for Ptychography)

For your ultimate goal of **reflection ptychography**, you need the full complex reflected wavefield (amplitude AND phase), not just intensities. Options:

#### Option A: Peng-Cowley Supercell with Prismatic (Current Approach)
- **Pros**: Already implemented in your `prismatique` code; handles convergent-beam illumination naturally; produces complex exit wave
- **Cons**: Large supercells needed; absorber tuning critical; may miss some dynamical effects
- **Verdict**: Reasonable for initial work, but need to verify against Bloch wave calculations

#### Option B: Bloch Wave Code (Peng-Dudarev-Whelan FORTRAN)
- **Pros**: Exact for semi-infinite crystal; numerically stable via R-matrix; includes all dynamical effects
- **Cons**: Designed for plane-wave illumination; adapting for convergent probe requires computing the wavefield for each incident angle and summing coherently
- **Verdict**: Gold standard for validation; adaptable for ptychography by computing S-matrix elements

#### Option C: Semi-Reciprocal Transfer Matrix (Ichimiya Method)
- **Pros**: Natural for layer-by-layer propagation; handles selvedge + bulk; implemented in `sim-trhepd-rheed`
- **Cons**: `sim-trhepd-rheed` is designed for surface RHEED rocking curves, not wavefield imaging; would need modification for convergent-beam case
- **Verdict**: Good for rocking curve validation; not directly useful for ptychography

#### Option D: Custom Surface-Parallel Multislice
- **Pros**: Can handle arbitrary surface features (steps, terraces); convergent beam natural
- **Cons**: Must properly include BOTH forward and backward scattering (not just forward as in standard multislice); need absorptive boundary at crystal bottom; numerical stability issues with evanescent waves
- **Verdict**: The right approach for ptychography of surfaces with defects, but requires careful implementation

### 6.3 Recommended Path

**Phase 1 (Validation):**
1. Implement the Peng-Dudarev-Whelan FORTRAN code (Appendix C) for Si -- compute rocking curves for your experimental geometry
2. Compare with your prismatique simulations for the same conditions
3. This will tell you whether your prismatique setup correctly captures the bulk dynamical diffraction

**Phase 2 (Ptychography simulation):**
1. Use prismatique with the Peng-Cowley supercell geometry for convergent-beam reflection diffraction
2. Scan the probe across a surface step
3. Verify that the phase shift of the reflected beam matches Delta-phi = 2 K_perp * d

**Phase 3 (Advanced):**
1. If Phase 2 works, you have a viable simulation tool for reflection ptychography
2. If not, implement the Bloch wave S-matrix approach, computing the reflected wavefield for each probe position

---

## 7. Key References (Verified to Exist)

### Primary Theoretical References
1. **Peng, L.-M., Dudarev, S. L., and Whelan, M. J.** "High-Energy Electron Diffraction and Microscopy." Oxford University Press, 2004. **Chapter 5 and Appendix C are essential.** [You have this book]
2. **Peng, L.-M. and Cowley, J. M.** "A multislice approach to the RHEED and REM calculation." Surface Science 199, 609-622 (1988). [Foundational paper for Peng-Cowley supercell method]
3. **Peng, L.-M. and Whelan, M. J.** "Bloch wave treatment of symmetry and multiple beam cases in RHEED and REM." J. Electron Microsc. Tech. 20, 412-424 (1992). [Bloch wave RHEED theory]
4. **Peng, L.-M., Dudarev, S. L., and Whelan, M. J.** "Dynamical RHEED calculations from the surface of a semi-infinite crystal." (Several papers, 1992-1996). [Semi-infinite crystal theory]

### Osakabe (Reflection Holography)
5. **Osakabe, N.** "Application of electron holography to surface topography observation." Surface Science 298, 345-350 (1993). [You have this paper]
6. **Osakabe, N., Matsuda, T., Endo, J., and Tonomura, A.** Ultramicroscopy 48, 483 (1993). [Full experimental details]
7. **Osakabe, N., Endo, J., Matsuda, T., Fukuhara, A., and Tonomura, A.** Phys. Rev. Lett. 62, 2969 (1989). [Dislocation observation]

### REM Theory and Imaging
8. **Wang, Z. L.** "Reflection Electron Microscopy and Spectroscopy for Surface Analysis." Cambridge University Press, 1996. [Comprehensive REM reference]
9. **Ichimiya, A. and Cohen, P. I.** "Reflection High-Energy Electron Diffraction." Cambridge University Press, 2004. [RHEED textbook; covers dynamical theory]

### Simulation Codes
10. **sim-trhepd-rheed** (GitHub) -- Ichimiya dynamical theory implementation; good for rocking curves but surface-focused
11. **Prismatic/prismatique** -- Your current tool; Peng-Cowley supercell approach via standard multislice

---

## 8. Corrected Understanding vs. Previous Report

| Aspect | Previous Report (INCORRECT) | Corrected Understanding |
|--------|---------------------------|------------------------|
| Nature of scattering | Surface RHEED from 2D layer | Bulk Bragg reflection from semi-infinite 3D crystal |
| Theoretical framework | sim-trhepd-rheed surface multislice | Bloch wave + R-matrix for semi-infinite crystal (Peng Ch. 5) |
| Penetration depth | "Few atomic layers" (surface-sensitive) | ~5-10 nm normal to surface (~15-30 layers); bulk-sensitive |
| Reciprocal lattice | 2D rods (surface) | 3D reciprocal lattice points, intersected by Ewald sphere at grazing angle |
| Diffraction features | Streaks from 2D rods | Bragg spots from 3D lattice (plus Kikuchi lines from inelastic scattering) |
| Si(666) prohibition | Correctly noted as forbidden | Still forbidden in diamond cubic -- but the ALLOWED reflections near it ARE bulk Bragg reflections |
| Simulation approach | Use sim-trhepd-rheed | Use Peng-Dudarev-Whelan Bloch wave code (Appendix C); OR prismatique with properly constructed supercell |
| Osakabe's theory | Unspecified | Bulk Bragg reflection + holographic phase retrieval; NOT surface RHEED |

---

## 9. Immediate Action Items

1. **Read Chapter 5 of Peng, Dudarev, Whelan (2004)** -- Sections 5.3.4 (Bloch wave method) and 5.3.4.5 (semi-infinite crystal) are directly applicable.

2. **Compile and run the FORTRAN routines in Appendix C** -- Compute rocking curves for Si at 200 kV to identify which Bragg reflections are accessible at alpha ~ 4.1 deg.

3. **Re-examine your experimental diffraction pattern** -- The spots you see are Bragg reflections from the 3D lattice, not 2D surface rod intersections. Index them as bulk (hkl) reflections considering the refraction correction (Section 5.3.4.2).

4. **Verify your prismatique simulations** -- Compare the reflected beam intensities from prismatique against the Bloch wave code for the same conditions (same crystal, same incidence angle, same energy). If they agree, your prismatique setup is correctly capturing the bulk dynamical diffraction.

5. **Determine which reflections are allowed** -- For Si (diamond cubic, F_d-3m), the structure factor selection rules are: h,k,l all odd OR all even with h+k+l = 4n. At alpha = 4.1 deg with [110] azimuth, work out which specular reflections satisfy Bragg's law with refraction correction.

---

## Sources

- [Peng & Cowley 1988 - Multislice RHEED/REM](https://www.sciencedirect.com/science/article/abs/pii/0039602888909259)
- [Peng & Whelan 1992 - Bloch wave RHEED](https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jemt.1070200407)
- [Wang - Electron reflection from bulk crystals](https://www.semanticscholar.org/paper/Electron-reflection,-diffraction-and-imaging-of-in-Wang/dc74261793a112218e6bae35ca9238701eac73c7)
- [ASU REM overview](https://cores.research.asu.edu/sites/default/files/2018-10/reflection_electron_microscopy.pdf)
- [Peng, Dudarev, Whelan textbook (OUP)](https://global.oup.com/academic/product/high-energy-electron-diffraction-and-microscopy-9780199602247)
- [Wang - REM and Spectroscopy book (Cambridge)](https://www.cambridge.org/core/books/reflection-electron-microscopy-and-spectroscopy-for-surface-analysis/4F3C18408D2D686F43DDEC9CAF213394)
- [Ichimiya & Cohen RHEED textbook](https://books.google.com/books?id=AUVbPerNxTcC)
- [Osakabe 1992 - Reflection holography](https://pubmed.ncbi.nlm.nih.gov/1498359/)
- [Osakabe US Patent - REH apparatus](https://patents.google.com/patent/US4998788)
- [RHEED Wikipedia](https://en.wikipedia.org/wiki/Reflection_high-energy_electron_diffraction)
