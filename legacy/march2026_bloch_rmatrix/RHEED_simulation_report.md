# RHEED Simulation for Si(111) Surface: Comprehensive Analysis

## Report for Hussien Ballouk, PhD Candidate, UVic
## Date: 2026-04-05

---

# Table of Contents

1. [Physical Picture: RHEED from Si(111) along [110] at 200 kV](#1-physical-picture)
2. [Crystallography: Surface Reciprocal Lattice and Allowed Reflections](#2-crystallography)
3. [Expected Diffraction Pattern: Spot Positions and Indexing](#3-expected-pattern)
4. [Osakabe's Geometry and How Your Experiment Relates](#4-osakabe-geometry)
5. [Theoretical Frameworks for Simulating RHEED](#5-theoretical-frameworks)
6. [Adapting Transmission Multislice to Reflection Geometry](#6-adapting-multislice)
7. [Existing Codes and Implementations](#7-existing-codes)
8. [Recommended Simulation Strategy](#8-recommended-strategy)

---

# 1. Physical Picture

## 1.1 The Geometry

Your experiment:
- **200 kV electrons**, relativistic wavelength lambda = 0.02508 A
- **Si[110] crystal**, cleaved edge exposing the **(111) surface** (or a surface close to it)
- **Beam along the [110] azimuth** (confirmed by your diffraction pattern)
- **Grazing incidence angle alpha ~ 4.1 deg = 71.6 mrad**

At grazing incidence, the electron beam skims the crystal surface. The wavevector magnitude is:

    k = 2*pi / lambda = 2*pi / 0.02508 = 250.5 A^{-1}

The perpendicular component of the wavevector (into the surface):

    k_perp = k * sin(alpha) = 250.5 * sin(4.1 deg) = 250.5 * 0.0715 = 17.9 A^{-1}

The parallel component:

    k_parallel = k * cos(alpha) = 250.5 * cos(4.1 deg) ~ 250.4 A^{-1}

**Key point**: k_parallel >> k_perp. The electron "sees" many surface unit cells along its path but penetrates only a few nanometers into the bulk. This is why RHEED is surface-sensitive despite using 200 keV electrons.

## 1.2 Penetration Depth

The penetration depth at grazing incidence is approximately:

    d_penetration ~ 1 / (2 * mu * sin(alpha))

where mu is the absorption coefficient. For Si at 200 kV with alpha = 4.1 deg, the penetration depth is of order 1--5 nm (a few monolayers), making this a genuine surface probe.

## 1.3 What Happens Physically

1. The beam enters at grazing angle and refracts slightly upon entering the crystal (inner potential effect: V_0(Si) ~ 12 V, giving a correction to incidence angle of order 0.1 mrad at these energies -- small but relevant for rocking curves)
2. Inside the crystal, the electron Bloch waves propagate parallel to the surface
3. At Bragg conditions, strong specular and off-specular reflections occur
4. The diffracted beams exit at angles symmetric about the surface plane
5. On the RHEED screen (far downstream), these beams form spots arranged on **Laue circles**

---

# 2. Crystallography: Surface Reciprocal Lattice and Allowed Reflections

## 2.1 Real-Space Surface Geometry

The Si(111) surface has a hexagonal surface unit cell. The surface lattice vectors are:

    a_1 = (a/sqrt(2)) * [1, 0]  = 3.840 A * [1, 0]
    a_2 = (a/sqrt(2)) * [1/2, sqrt(3)/2] = 3.840 A * [1/2, sqrt(3)/2]

where a = 5.431 A is the Si cubic lattice parameter, and a/sqrt(2) = 3.840 A is the surface lattice parameter of the unreconstructed 1x1 Si(111) surface.

**Important**: In reality, Si(111) reconstructs to the famous 7x7 structure at room temperature. However, for the purposes of matching basic RHEED spots to Osakabe's experiment, you can start with the unreconstructed 1x1 surface. Reconstruction adds fractional-order streaks between the integer-order rods.

## 2.2 Reciprocal Lattice of the Si(111) Surface

The 2D reciprocal lattice vectors are:

    b_1 = (2*pi / |a_1|) * (perpendicular in surface plane)
    b_2 = similarly

For the hexagonal surface mesh with parameter a_s = a/sqrt(2) = 3.840 A:

    |b_1| = |b_2| = 4*pi / (sqrt(3) * a_s) = 4*pi / (sqrt(3) * 3.840) = 1.889 A^{-1}

The reciprocal lattice rods extend infinitely perpendicular to the surface (because the crystal is semi-infinite -- no periodicity in the surface-normal direction).

## 2.3 Beam Along [110] Azimuth

When the beam is along the [110] azimuth (one of the high-symmetry directions of Si(111)), you are looking along a row of reciprocal lattice rods. The rods in the RHEED screen plane (perpendicular to the beam) are spaced by:

For the [110] azimuth on Si(111), the row spacing seen on the screen is:

    d_row = a_s * sqrt(3) / 2 = 3.840 * sqrt(3) / 2 = 3.325 A

    => Delta_k_parallel = 2*pi / d_row = 1.889 A^{-1}

This is the spacing between the reciprocal lattice rods projected onto the RHEED screen plane.

## 2.4 Diamond Cubic Structure Factor Selection Rules

For bulk Si (diamond cubic, Fd-3m), the structure factor is:

    F_hkl = f_Si * [1 + (-1)^{h+k} + (-1)^{k+l} + (-1)^{h+l}] * [1 + (-i)^{h+k+l}]

The first bracket is the FCC condition. The second bracket is the diamond basis (two atoms per FCC point at (0,0,0) and (1/4,1/4,1/4)).

**Selection rules:**
| Condition on h+k+l | |F|^2 | Examples |
|---|---|---|
| h+k+l = 4N (all even, sum divisible by 4) | 64f^2 | (000), (220), (400), (444), (440) |
| h+k+l = 4N+2 (all even, sum = 4N+2) | **0 (FORBIDDEN)** | (200), (222), (420), **(666)** |
| h+k+l odd (mixed) | 32f^2 | (111), (311), (331), (333), (511) |

**CRITICAL REMINDER**: Si(666) is FORBIDDEN (h+k+l = 18 = 4*4+2). This has been noted in your CLAUDE.md and previous analyses. Osakabe used Pt(111) which is FCC (not diamond) -- for Pt, (666) IS allowed.

## 2.5 Allowed Reflections Relevant to Your Si(111) RHEED

In reflection geometry at the Si(111) surface, the relevant Bragg reflections are those with a large component of G perpendicular to the surface. The surface normal is [111].

For the (111) surface, the perpendicular reciprocal lattice vector is:

    G_111 = 2*pi/d_111, where d_111 = a/sqrt(3) = 3.135 A
    => G_111 = 2.004 A^{-1}

Key allowed reflections sorted by their perpendicular component (G_perp, projection onto [111]):

| Reflection (hkl) | G_perp / G_111 | Allowed? | Bragg angle at 200 kV |
|---|---|---|---|
| (111) | 1 | Yes (32f^2) | theta_B = lambda/(2*d_111) = 4.00 mrad |
| (220) | 0 (in-plane) | Yes (64f^2) | 4.61 mrad (from surface) |
| (333) | 3 | Yes (32f^2) | 12.0 mrad |
| (444) | 4 | Yes (64f^2) | 16.0 mrad |
| (555) | 5 | Yes (32f^2) | 20.0 mrad |
| (666) | 6 | **NO (FORBIDDEN)** | -- |

So the dominant specular reflections from Si(111) in the [110] azimuth are **(111), (333), (444), (555)** etc. The (222) and (666) are forbidden.

The specular beam in your experiment at alpha = 4.1 deg = 71.6 mrad is FAR from the low-order Bragg angles listed above (which are 4--20 mrad). This means:

**At alpha = 4.1 degrees, you are in a HIGH-ORDER reflection regime.** The Bragg angle of 71.6 mrad corresponds to:

    n * d_111 * sin(theta) = n * lambda / 2
    => 2 * d_111 * sin(alpha) / lambda = 2 * 3.135 * sin(4.1 deg) / 0.02508
    = 2 * 3.135 * 0.0715 / 0.02508 = 17.86

So the order is approximately n ~ 18, meaning the (18,18,18) equivalent -- but we must think in terms of which actual bulk reflections are excited.

**Let me recalculate more carefully.** The perpendicular momentum transfer for the specular beam is:

    Delta_k_perp = 2 * k * sin(alpha) = 2 * 250.5 * 0.0715 = 35.8 A^{-1}

The reciprocal lattice vector G_111 = 2*pi / d_111 = 2.004 A^{-1}. The order of the specular reflection is:

    n = Delta_k_perp / G_111 = 35.8 / 2.004 = 17.9

So the specular beam at alpha = 4.1 deg satisfies the Bragg condition for approximately the **18th order (111)** planes, i.e., effectively the (18,18,18) reflection -- but since this is equivalent to 6 times (333), and we need to check: is (18,18,18) allowed?

    h+k+l = 54 = 4*13 + 2 => FORBIDDEN by diamond cubic rules!

This is a problem. Let me reconsider. The issue is that in RHEED at such a large grazing angle, we are not exciting a single sharp Bragg reflection. Instead, the Ewald sphere cuts through many reciprocal lattice rods simultaneously, and the diffraction condition is more nuanced than a simple specular condition.

**IMPORTANT CORRECTION**: At alpha = 4.1 deg, the incidence angle is relatively large for RHEED (typical RHEED uses 1-5 deg). You are likely exciting MANY simultaneous reflections -- this is a many-beam dynamical diffraction regime. The spots you see on the screen are intersections of the Ewald sphere with the reciprocal lattice rods of the 2D surface lattice, NOT single bulk Bragg reflections. The pattern should be indexed by the 2D surface rod indices (h, k) and the Laue zone number.

---

# 3. Expected Diffraction Pattern: Spot Positions and Indexing

## 3.1 Ewald Sphere Construction for RHEED

The Ewald sphere has radius k = 250.5 A^{-1} and is centered at the reciprocal-space origin displaced by the incident wavevector. For grazing incidence at angle alpha, the sphere is nearly tangent to the reciprocal lattice plane (zeroth Laue zone).

The diffraction condition is:

    k_f = k_i + G_hk

where G_hk = h*b_1 + k*b_2 is a 2D reciprocal lattice vector. The Ewald sphere constraint |k_f| = |k_i| then determines the exit angle for each rod.

## 3.2 Spot Positions on the Screen

For a RHEED screen at distance L from the sample, with the specular spot at the center:

**Horizontal position** (parallel to surface, perpendicular to beam):

    x_hk = L * (k_fx / k_fz)

where k_fx is the lateral component and k_fz is the forward component.

**Vertical position** (perpendicular to surface):

    y_hk = L * (k_fy / k_fz)

where k_fy is the component normal to the surface.

For rod (h,k), the parallel momentum transfer is:

    K_parallel = h*b_1x + k*b_2x  (component perpendicular to beam direction)

And the exit angle is determined by:

    k_fy = sqrt(k^2 - (k_ix + K_parallel)^2) - but this must be evaluated carefully

## 3.3 Laue Zones

The Laue zones arise from the intersection of the Ewald sphere with rows of rods at different distances from the beam direction.

- **Zeroth Laue zone (L0)**: rods directly intersected by the beam plane. These form the bottom arc of spots closest to the shadow edge.
- **First Laue zone (L1)**: the next row of rods. These form a higher arc.
- **Higher Laue zones**: progressively higher arcs.

For Si(111) along [110] azimuth:

The zeroth Laue zone contains rods (h,0) for various h. The first Laue zone contains rods (h,1), etc.

The angular separation between Laue zones (in the vertical/exit-angle direction) depends on the rod row spacing perpendicular to the beam, which for [110] azimuth on Si(111) is:

    d_Laue = a_s * sqrt(3) / 2 = 3.325 A

Wait -- let me be more precise. The [110] direction in the cubic system projected onto the (111) surface plane corresponds to one of the nearest-neighbor directions of the hexagonal mesh. The reciprocal lattice row spacing perpendicular to [110] is:

    Delta_k_lateral = 2*pi / d_row

For the hexagonal surface mesh viewed along [110], the rod spacing along the beam is b_1 (or b_2) projected along [110], and the rod spacing perpendicular to the beam gives the Laue zone separation.

The key observable: **you should see spots arranged on concentric arcs (Laue circles)**. The spacing between arcs is determined by the reciprocal lattice periodicity perpendicular to the beam direction.

## 3.4 Expected Pattern for Si(111) 1x1 Along [110]

Along the [110] azimuth, the RHEED pattern should show:

1. **Specular spot (0,0)**: at exit angle = incidence angle (alpha ~ 4.1 deg)
2. **Zeroth Laue zone**: spots symmetrically placed on either side of the specular spot at the same height
3. **First Laue zone**: an arc of spots above the zeroth zone
4. **Kikuchi lines**: broad diffuse lines from inelastic/thermal diffuse scattering

The lateral spacing between zeroth-Laue-zone spots corresponds to the reciprocal lattice period along the direction perpendicular to both the beam and the surface normal.

For the 7x7 reconstruction (room temperature), additional fractional-order spots would appear at 1/7th of the spacing between integer-order spots.

## 3.5 What You Should See vs. What Osakabe Saw

**Osakabe** used Pt(111) with the (666) specular reflection. Pt is FCC, lattice parameter 3.923 A.
- For Pt(111): d_111 = 3.923/sqrt(3) = 2.265 A
- Osakabe at 100 kV: lambda = 0.0370 A, k = 169.8 A^{-1}
- His specular Bragg angle was tuned to excite the (666) reflection specifically

**Your experiment** uses Si(111) at 200 kV, alpha = 4.1 deg.
- d_111(Si) = 5.431/sqrt(3) = 3.135 A
- The specular beam excites high-order (111) planes, but many are forbidden in diamond cubic
- The STRONG allowed reflections near your incidence angle would be those whose Bragg angle is close to 4.1 deg:
  - (111): theta_B = 0.23 deg -- too small
  - (333): theta_B = 0.69 deg -- too small
  - Many-beam regime at 4.1 deg

The point is that at 4.1 deg, you are in a regime where the Ewald sphere intersects many rods simultaneously, and the intensity distribution is controlled by dynamical diffraction (multiple scattering), not by a single Bragg peak.

---

# 4. Osakabe's Geometry and How Your Experiment Relates

## 4.1 Osakabe's Setup (1988-1993)

From the patent (US4998788) and the Surface Science 298 (1993) paper:

| Parameter | Osakabe | Your Experiment |
|---|---|---|
| Microscope | Hitachi FE-TEM | Hitachi HF-3300 STEHM |
| Voltage | 100 kV (possibly up to 350 kV) | 200 kV |
| Sample (primary) | Pt(111), melt-grown wire | Si[110], cleaved edge |
| Surface | Pt(111) | Si(111) (cleaved from [110] crystal) |
| Specular reflection | (666) | TBD -- need to identify |
| Mode | REM + biprism holography | Initially: replicate REM/holography; goal: ptychography |
| Biprism | Single or triple biprism | Available on HF-3300 |
| Vacuum | < 10^{-7} Pa (liquid He cooling) | Room-temperature UHV |

## 4.2 Critical Difference: Pt is FCC, Si is Diamond

This is the single most important distinction. For Pt (FCC, no basis extinction):
- (666) is ALLOWED: h+k+l = 18, all even, all same parity => FCC allows it
- The (666) Bragg angle at 100 kV for Pt(111) is well-defined and gives strong intensity

For Si (diamond cubic, extra extinction from the basis):
- (666) is FORBIDDEN: h+k+l = 18 = 4*4+2 => diamond basis factor = 0
- You CANNOT use (666) for Si

**You must identify which reflection you are actually exciting at alpha = 4.1 deg.**

## 4.3 What Reflection Are You Exciting?

At 200 kV, lambda = 0.02508 A. The Bragg condition for (hkl) planes with spacing d is:

    sin(theta_B) = lambda / (2*d)

For alpha = 4.1 deg = 0.0716 rad:

    d = lambda / (2*sin(alpha)) = 0.02508 / (2 * 0.07156) = 0.1752 A

This is an extremely small d-spacing. The corresponding |G| = 2*pi/d = 35.87 A^{-1}.

For Si with a = 5.431 A:

    |G_hkl| = (2*pi/a) * sqrt(h^2 + k^2 + l^2)

Setting this equal to 35.87:

    sqrt(h^2 + k^2 + l^2) = 35.87 * 5.431 / (2*pi) = 31.01

    h^2 + k^2 + l^2 = 961

So you need (hkl) with h^2 + k^2 + l^2 ~ 961. Some candidates:
- (31,0,0): 961 -- not a special direction
- The specular reflection from (111) surface with G along [111]: G = n * G_111, so n = 35.87 / 2.004 = 17.9

The 18th order from (111) planes: (18,18,18) -- but h^2+k^2+l^2 = 972, and h+k+l = 54 = 4*13+2 => FORBIDDEN.

The 17th order: (17,17,17) -- h+k+l = 51 (odd) => ALLOWED (32f^2)!
- |G| = (2*pi/5.431)*sqrt(867) = 1.157 * 29.44 = 34.07 A^{-1}
- Bragg angle: sin(theta) = 34.07 * 0.02508 / (4*pi) = 0.0680 => theta = 3.90 deg

The 19th order: (19,19,19) -- h+k+l = 57 (odd) => ALLOWED.
- |G| = 1.157 * 32.91 = 38.08 A^{-1}
- theta = 4.35 deg

**So at alpha = 4.1 deg, you are between the (17,17,17) Bragg angle (3.90 deg) and the (19,19,19) Bragg angle (4.35 deg).**

Actually, let me reconsider. The specular reflection from the (111) surface does not need to correspond to a single bulk (hkl). In RHEED, the crystal truncation rods (CTRs) have intensity modulated by the bulk structure factor but are not strictly zero between Bragg peaks (due to the surface truncation). The specular rod -- the (0,0) rod of the 2D lattice -- has intensity maxima at the allowed bulk Bragg conditions and weaker but nonzero intensity elsewhere.

**At 4.1 deg, your specular beam is excited via the crystal truncation rod effect, sampling contributions from nearby allowed reflections like (17,17,17) and (19,19,19).**

[VERIFY: The above analysis assumes the specular beam direction is exactly along [111]. If the cleaved surface is slightly off from (111), the geometry could differ.]

---

# 5. Theoretical Frameworks for Simulating RHEED

## 5.1 Kinematical Theory (Simplest)

The kinematical approximation treats each atom as scattering independently (single scattering, Born approximation). This gives:

    I(G) ~ |F(G)|^2 * |S(G)|^2

where F is the structure factor and S is the shape/interference function.

**Pros**: Simple, fast, gives correct spot positions.
**Cons**: Wrong intensities (multiple scattering is STRONG in electron diffraction), cannot handle dynamical effects like surface resonances, Kikuchi lines, or extinction.

**Available code**: The Wolfram Mathematica program from arXiv:2207.06642 (Luo et al., 2022) does exactly this -- kinematical Ewald construction with exact geometric projection to the screen. This is the fastest way to predict SPOT POSITIONS, but not intensities.

## 5.2 Dynamical Theory: Bloch Wave Method

The Bloch wave method solves the Schrodinger equation inside the crystal as a set of coupled Bloch states. For RHEED, this requires:

1. Setting up the crystal potential as a Fourier series (reciprocal lattice components V_G)
2. Diagonalizing the dispersion matrix to find Bloch waves
3. Matching boundary conditions at the surface

This is the most rigorous approach for a perfect semi-infinite crystal. Key references:
- Ichimiya & Cohen textbook (Cambridge, 2004)
- Peng, Whelan, Dudarev monograph (Oxford)

**Pros**: Exact for perfect crystals, handles dynamical effects, surface resonances, absorption.
**Cons**: Computationally expensive for many beams, difficult to extend to surface defects (steps, reconstruction domains).

## 5.3 Dynamical Theory: Reflection Multislice (Surface-Parallel Slicing)

This is the approach developed by Maksym & Beeby (1981), Peng & Cowley (1986, 1988), and Ichimiya (1983, 1985). It adapts the standard transmission multislice to reflection geometry by:

**KEY MODIFICATION: Slices are taken PARALLEL TO THE SURFACE, not perpendicular to the beam.**

The standard transmission multislice propagates the wave through slices perpendicular to the beam direction (z-axis). In the reflection multislice:

1. The crystal is divided into layers parallel to the surface (each layer = one atomic plane or a fraction thereof)
2. The incident wave enters at glancing angle
3. At each layer, the wave is:
   a. **Phase-shifted** by the projected potential of that layer (phase grating):
      psi_n+1 = T_n * psi_n, where T_n(x) = exp(i * sigma * V_n(x) * Delta_z)
   b. **Propagated** to the next layer using the Fresnel propagator:
      psi_n+1 = F^{-1}{ P(k) * F{psi_n} }, where P(k) = exp(i * pi * lambda * Delta_z * |k|^2)

The crucial difference from transmission multislice: **the coordinate system is rotated so that the slicing direction is the surface normal**, and the beam enters obliquely. The propagation is along the surface-normal direction (into the crystal), not along the beam direction.

**Boundary condition**: The wave must be evanescent (decaying) deep in the crystal. An absorbing potential or absorbing boundary condition is applied at the bottom of the slab.

**This is exactly what the prismatique/holography.py code already does** -- it uses Prismatic's multislice with beam tilt to simulate a tilted beam on a slab, with an absorber at the bottom. The key issue is whether the slicing is truly parallel to the surface or parallel to the beam.

### Peng & Cowley (1988) formulation:

Reference: L.-M. Peng, J.M. Cowley, Surface Science 199 (1988) 609-622.

The multislice method based on Cowley-Moodie physical optics theory was applied to RHEED and REM. The crystal is sliced into layers parallel to the surface. For each layer, the transmission function and propagator are applied. The forward-scattering approximation is used (backscattering neglected within the multislice -- this is valid because the scattering at each layer is predominantly forward for high-energy electrons).

### Ichimiya (1983) formulation:

Reference: A. Ichimiya, Japanese Journal of Applied Physics 22 (1983) 176.

Ichimiya developed the dynamical theory of RHEED using the multislice method with surface-parallel slicing. This is the basis of the `sim-trhepd-rheed` code.

## 5.4 Tilted-Slab Transmission Multislice (Your Current Approach)

An alternative that leverages EXISTING transmission multislice codes (Prismatic, abTEM):

**Idea**: Instead of modifying the slicing scheme, keep the standard beam-perpendicular slicing but build a supercell with the crystal surface tilted relative to the beam.

Procedure:
1. Build a slab of Si with the (111) surface
2. Place the slab in a large supercell with vacuum above and below
3. Tilt the incident beam by (90 - alpha) degrees from the surface normal, so it arrives at grazing angle alpha
4. Run standard transmission multislice
5. The exit wave contains both transmitted and reflected beams

**This is essentially what your existing prismatique pipeline does.** The beam tilt parameter in Prismatic tilts the incident plane wave, and the absorber at the bottom prevents wrap-around.

**Limitations of this approach:**
- The supercell must be VERY large in the beam direction (because the beam travels a long distance along the surface before exiting)
- The number of slices along the beam direction becomes enormous (the beam crosses hundreds of atomic layers)
- Periodic boundary conditions along the beam direction create artifacts
- The absorber at the bottom is critical but ad hoc

**Despite these limitations, this is the most practical approach for a first simulation**, because you can use Prismatic/abTEM directly without writing new code.

---

# 6. Adapting Transmission Multislice to Reflection Geometry

## 6.1 The Core Problem

Standard multislice codes propagate the wave along the optical axis (z). For RHEED, the beam is nearly parallel to the surface. If you define z as the surface normal, the beam propagates nearly in the x-y plane. If you define z as the beam direction, the surface is nearly perpendicular to your slices.

**Three approaches:**

### Approach A: Surface-Parallel Slicing (True RHEED Multislice)

Slice the crystal into layers parallel to the surface. Propagate the wave from the surface into the bulk. This is the Ichimiya/Peng/Cowley method and requires custom code.

Advantages: Physically natural, correctly handles surface truncation, computationally efficient (few slices needed -- the beam only penetrates a few nm).

Disadvantage: No existing open-source code with a modern interface (sim-trhepd-rheed is Fortran, not trivial to use).

### Approach B: Tilted Beam in Standard Code (Your Current Approach)

Keep beam-perpendicular slicing, tilt the beam to grazing angle.

Advantages: Uses existing codes (Prismatic, abTEM).

Disadvantages:
- Need a very thick slab (beam travels far along surface -- if the surface is 100 nm long, you need ~100 nm * tan(alpha) ~ 7 nm of depth, but the lateral extent must be ~100 nm)
- The supercell in x (along surface, along beam) must accommodate the full illuminated region
- Computational cost scales badly
- Periodic boundary conditions along the beam create wrap-around

### Approach C: Supercell with Tilted Crystal

Build the crystal tilted in the supercell so the surface makes an angle (90 - alpha) with the z-axis. The beam enters along z (vertical) and the crystal surface is nearly vertical.

This is mathematically equivalent to Approach B but may be easier to set up geometrically.

## 6.2 Practical Recipe for Approach B (Recommended Starting Point)

1. **Build the slab**: 
   - Si(111) surface, unreconstructed 1x1
   - Dimensions: ~50 nm along beam (x), ~20 nm perpendicular (y), ~5 nm deep (z = surface normal)
   - Vacuum: ~10 nm above and below the slab
   - Total supercell: 50 nm x 20 nm x 25 nm

2. **Set up beam tilt**: 
   - Tilt the incident plane wave by alpha = 4.1 deg from the surface (= 85.9 deg from the surface normal)
   - In Prismatic: this is a beam tilt of 85.9 deg -- this is OUTSIDE the normal operating range of Prismatic (designed for small tilts in TEM/STEM)

**THIS IS THE FUNDAMENTAL PROBLEM**: Existing transmission multislice codes cannot handle 86-degree beam tilts. The paraxial approximation (Fresnel propagator) breaks down for large tilts.

## 6.3 The Paraxial Approximation Problem

The standard multislice propagator is:

    P(k_x, k_y) = exp(i * pi * lambda * Delta_z * (k_x^2 + k_y^2))

This is the **paraxial (Fresnel) approximation** to the exact propagator:

    P_exact(k_x, k_y) = exp(i * Delta_z * sqrt(k^2 - k_x^2 - k_y^2))

The paraxial approximation is valid when k_x, k_y << k, i.e., when the beam is close to the optical axis. For RHEED with alpha = 4.1 deg:

    k_x (along surface) ~ k * cos(alpha) = 0.997 * k
    k_z (into surface) ~ k * sin(alpha) = 0.072 * k

If z is the optical axis (beam direction), then k_x/k ~ 0.07 (OK, paraxial is fine). But if z is the surface normal, then k_x/k ~ 0.997 (TERRIBLE, paraxial fails completely).

**Resolution**: You MUST use the beam direction as z, not the surface normal. This means slicing the crystal perpendicular to the beam, which for grazing incidence means slices are nearly parallel to the surface normal.

But this creates the problem of needing a huge number of slices along the beam path, and the crystal must be set up in a rotated coordinate frame.

## 6.4 What Actually Works: The Two Viable Paths

### Path 1: Use sim-trhepd-rheed (Fortran, Ichimiya method)

This code implements the correct surface-parallel multislice for RHEED. It is designed for exactly this problem. The downside is it is Fortran-based and the documentation is sparse.

Steps:
1. Clone from GitHub
2. Set ep='E' for electron mode (default is positron)
3. Set up Si(111) surface structure (example with Al/Si(111) is provided)
4. Run bulk.exe then surf.exe
5. Output: rocking curves (intensity vs angle)

### Path 2: Write a Custom Surface-Parallel Multislice in Python

This is a medium-difficulty coding project (a few hundred lines). The algorithm:

```
For each layer n (from surface into bulk):
    1. Calculate projected potential V_n(x) for that atomic layer
    2. Transmission: psi = psi * exp(i * sigma * V_n * dz)
    3. Propagation: psi = IFFT( FFT(psi) * exp(i*pi*lambda*dz*(kx^2 + ky^2)) )
    4. If at bottom: apply absorber
```

Where x is the coordinate along the surface (beam direction projected onto surface), and z is into the crystal. The beam enters as:

    psi_0(x) = exp(i * k_x * x)  where k_x = k * cos(alpha)

And the Bragg-diffracted beams emerge as plane waves at different angles.

**The coordinate system**: x is along the surface (along beam), z is perpendicular to the surface (into crystal). Slicing is in z. Propagation is in z. The beam enters obliquely.

**For a 2D simulation** (one coordinate along surface + depth), this is straightforward. A 2D code would give you the rocking curve and diffraction pattern in the incidence plane. This is sufficient for matching specular and off-specular spots in the incidence plane.

---

# 7. Existing Codes and Implementations

## 7.1 sim-trhepd-rheed

- **URL**: https://github.com/sim-trhepd-rheed/sim-trhepd-rheed
- **Theory**: Dynamical multislice (Ichimiya method, surface-parallel slicing)
- **Language**: Fortran 90 with Python post-processing
- **Capability**: RHEED rocking curves, supports Si(111) (Al/Si example provided)
- **Status**: Last release v1.0.2, May 2022
- **Reference**: Computer Physics Communications 277 (2022) 108371; arXiv:2110.09477
- **How to switch to RHEED**: Change `ep='P'` to `ep='E'` in surfm.f90 and bulkm.f90, recompile

**This is your best option for a validated dynamical RHEED simulation.**

## 7.2 PyRHEED

- **URL**: https://github.com/yux1991/PyRHEED
- **Theory**: Kinematical ONLY
- **Language**: Python 3 + PyQt6
- **Capability**: Pattern simulation, Kikuchi line simulation, reciprocal space mapping
- **Limitation**: No dynamical diffraction -- gives correct spot positions but wrong intensities
- **Use case**: Quick check of spot positions and pattern indexing

## 7.3 Kinematical Ewald Construction (Wolfram)

- **Reference**: arXiv:2207.06642 (Luo et al., JVST B 40, 054002, 2022)
- **Theory**: Pure kinematical Ewald sphere + Bragg rod intersection
- **Language**: Wolfram Mathematica with GUI
- **Capability**: Exact geometric spot positions for any surface + azimuth
- **Limitation**: No intensities, kinematical only

## 7.4 FRHEED

- **URL**: https://github.com/ecyoung3/FRHEED
- **Theory**: Data analysis tool (not simulation)
- **Use case**: Real-time RHEED analysis during growth

## 7.5 Your Existing prismatique Pipeline

- **Tool**: Prismatic 2.0 via prismatique wrapper
- **Theory**: Transmission multislice with beam tilt
- **Limitation**: Designed for transmission geometry; the large beam tilt needed for RHEED (85+ deg from surface normal) is outside its design range
- **Potential**: Could work for SMALL incidence angles (< 1 deg) where the paraxial approximation still holds, but alpha = 4.1 deg is too large

---

# 8. Recommended Simulation Strategy

## Phase 1: Kinematical Pattern (Spot Positions Only)

**Goal**: Predict where spots should appear on the RHEED screen to match your experimental data.

**Method**: Write a Python script that:
1. Defines the Si(111) 1x1 surface reciprocal lattice
2. Constructs the Ewald sphere for 200 kV, alpha = 4.1 deg, [110] azimuth
3. Finds intersections with reciprocal lattice rods
4. Projects intersection points onto the RHEED screen
5. Labels each spot with its (h,k) rod index and Laue zone number
6. Marks which bulk reflections are allowed/forbidden by diamond cubic rules

This can be done in ~100 lines of Python (numpy + matplotlib). No dynamical theory needed -- just geometry.

**This should be your FIRST step.** It will let you index the experimental pattern.

## Phase 2: Dynamical Rocking Curves with sim-trhepd-rheed

**Goal**: Get correct intensities and verify which reflections are strong at alpha = 4.1 deg.

**Method**:
1. Clone and compile sim-trhepd-rheed (switch to electron mode)
2. Set up Si(111) 1x1 surface with appropriate number of layers
3. Run rocking curve calculation (intensity vs incidence angle) for the specular beam
4. Identify which incidence angles give strong specular reflection
5. Compare with your experimental tilt series data

## Phase 3: Custom 2D Reflection Multislice

**Goal**: Full simulation of RHEED pattern including surface steps, for eventual comparison with holographic phase maps.

**Method**: Write a 2D surface-parallel multislice code in Python:
1. Define Si(111) crystal layers (projected potentials for each layer)
2. Implement the multislice algorithm with surface-parallel slicing
3. Include absorbing boundary at the bottom
4. Input: plane wave at grazing angle alpha
5. Output: reflected wavefield (amplitude + phase for each diffracted beam)
6. Introduce surface steps and calculate phase shifts

This is the path toward simulating Osakabe's experiment for Si.

## Phase 4: Compare with prismatique Results

**Goal**: Cross-validate the custom 2D code against your existing pipeline.

**Method**: For small incidence angles where prismatique is valid, run both codes and compare. This builds confidence before extending to larger angles.

---

# Summary of Key Points

1. **Your experiment at alpha = 4.1 deg, 200 kV excites very high-order reflections from Si(111)**. The perpendicular momentum transfer corresponds to approximately the 18th order of (111) planes. Many of these high-order reflections are forbidden by diamond cubic symmetry.

2. **Si(666) is FORBIDDEN**. You cannot directly replicate Osakabe's (666) specular reflection with Si. The nearest allowed specular reflections are around (17,17,17) at 3.9 deg and (19,19,19) at 4.35 deg.

3. **The RHEED pattern should show spots on Laue circle arcs**, indexed by 2D surface rod indices (h,k). Spot positions are determined by kinematical Ewald construction and can be calculated purely geometrically.

4. **For correct intensities, dynamical theory is essential.** The sim-trhepd-rheed code (Ichimiya method) is the most appropriate existing tool.

5. **Standard transmission multislice codes (Prismatic, abTEM) cannot handle RHEED directly** due to the large beam tilt (85+ deg from surface normal) violating the paraxial approximation.

6. **A custom 2D reflection multislice is feasible** and would be the most valuable long-term tool for your research.

7. **Start with kinematical spot-position calculation** to index your experimental pattern, then move to dynamical simulations for intensity matching.

---

# References

## Key Papers
- A. Ichimiya, Jpn. J. Appl. Phys. 22 (1983) 176 -- original RHEED multislice
- L.-M. Peng, J.M. Cowley, Surface Science 199 (1988) 609 -- multislice for RHEED/REM
- P.A. Maksym, J.L. Beeby, Surface Science 110 (1981) 423 -- theory of RHEED
- N. Osakabe et al., Surface Science 298 (1993) 345 -- reflection electron holography
- N. Osakabe et al., Phys. Rev. Lett. 62 (1989) 2969 -- atomic step observation by REH

## Codes
- sim-trhepd-rheed: https://github.com/sim-trhepd-rheed/sim-trhepd-rheed
- PyRHEED: https://github.com/yux1991/PyRHEED
- FRHEED: https://github.com/ecyoung3/FRHEED
- Kinematical RHEED (Wolfram): arXiv:2207.06642

## Textbooks
- A. Ichimiya, P.I. Cohen, "Reflection High-Energy Electron Diffraction" (Cambridge, 2004) -- THE definitive RHEED reference
- L.-M. Peng, M.J. Whelan, S.L. Dudarev, "High Energy Electron Diffraction and Microscopy" (Oxford) -- theory reference you already have
- E.J. Kirkland, "Advanced Computing in Electron Microscopy" (Springer, 2020) -- multislice theory reference you already have

## Web Sources
- RHEED Wikipedia: https://en.wikipedia.org/wiki/Reflection_high-energy_electron_diffraction
- UBC RHEED notes: https://phas.ubc.ca/~berciu/TEACHING/PHYS502/PROJECTS/RHEED.pdf
- LibreTexts RHEED: https://chem.libretexts.org/Bookshelves/Physical_and_Theoretical_Chemistry_Textbook_Maps/Surface_Science_(Nix)/06:_Overlayer_Structures_and_Surface_Diffraction/6.03:_Reflection_High_Energy_Electron_Diffraction_(RHEED)
- Diamond cubic structure factor: https://en.wikipedia.org/wiki/Diamond_cubic
