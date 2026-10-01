# Simulation parameters, explained

Status: 2026-10-01. This is the parameter reference for the Si(001) three-strip simulation behind
the figures in `docs/figures/` (results: `docs/11_si001_reconstruction_results.md`). Values come
from `configs/si001_three_sections_cpu.yaml` and the run manifests; derived numbers were
recomputed with the repository code. The Status column uses the project's evidence labels:

* **PROJECT_INPUT**: supplied by the laboratory.
* **ASSUMPTION**: a physical choice not yet sourced or measured; it must be replaced before
  quantitative comparison.
* **DERIVED_HERE**: computed by this repository from other inputs.
* **NUMERICAL**: a numerical setting with no physical meaning, chosen and checked for convergence.

Coordinates: x is the outward surface normal [001], y is in the surface across the beam [1-10],
and z is along the beam azimuth [110]. Lengths are in A (0.1 nm), angles are glancing angles
measured from the surface, and phases are in rad.

---

## 1. Electron beam

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Beam energy | 200 keV | Kinetic energy of the electrons. It sets the wavelength and how strongly the electrons interact with the crystal. All reflection holography work uses 200 keV. | PROJECT_INPUT |
| Wavelength λ | 0.025079 Å | Relativistic de Broglie wavelength at 200 keV. All phases scale with 1/λ. | DERIVED_HERE |
| Wavenumber k = 2π/λ | 250.53 rad/Å | Used to convert path differences into phase. | DERIVED_HERE |
| Lorentz factor γ | 1.391 | The relativistic mass increase. It enters the interaction constant and the refraction. | DERIVED_HERE |
| Interaction constant σ | 7.288 × 10⁻⁴ rad V⁻¹ Å⁻¹ | Phase shift the electron gains per volt-ångström of projected crystal potential. | DERIVED_HERE |

## 2. Crystal and sample (the supercell)

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Material, structure | Si, diamond cubic | Two interpenetrating fcc lattices; 8 atoms per cubic cell. | PROJECT_INPUT (surface: Si(001)) |
| Lattice constant a | 5.4309 Å | Room-temperature value. A 10⁻⁵ relative error has no visible effect on the phases. | ASSUMPTION (standard value) |
| Surface orientation | (001) | Surface plane of the sample. Its atomic layers are a/4 = 1.358 Å apart. | PROJECT_INPUT (item 11 still open) |
| Beam azimuth | [110] | In-plane direction of the beam. The strips, the step edges and the dislocation line all run parallel to it, so there is no shadowing and every strip appears side by side in one image. | ASSUMPTION (PROJECT_INPUT item 8) |
| Surface termination | bulk-terminated, no reconstruction | The top layer is a perfect continuation of the bulk. A real clean Si(001) surface has a 2×1 dimer reconstruction, and an air-exposed one has native oxide. Both change the reflected amplitude and phase. | ASSUMPTION (B3, B7) |
| Repeat along the beam | 3.840 Å = a/√2 | The crystal along [110] repeats every a/2[110]. The structure is uniform along the beam, so one repeat is stored and reused for every slice. This is exact here because the dislocation line also runs along the beam. | DERIVED_HERE |
| Width across the beam | 460.8 Å = 120 × 3.840 Å | Periodic width of the cell. It must be a whole number of lattice repeats (3.840 Å along [1-10]) so that the crystal joins itself across the periodic boundary. | NUMERICAL |
| Strips | 3 × 153.6 Å (40 repeats each) | 1 is the reference terrace; 2 is raised; 3 is at the reference height with the dislocation. Each strip is wide enough that its centre is more than 2.5 nm from a step edge and the dislocation field has room to decay. | ASSUMPTION (layout chosen with Ali) |
| Strip 2 height | +4 atomic layers = 5.431 Å (one lattice constant) | Four layers make a pure lattice translation, so the step phase has the exact value −(k_out − k_in)·R. One or three layers would give terraces rotated by 90° (the 4₁ screw relation), whose phase difference is dynamical. | ASSUMPTION (PROJECT_INPUT item 13) |
| Crystal depth | 56 Å below the reference surface | How much crystal is stored. The reflected beam probes only the top few nm, and the bottom 18 Å sits inside the absorber. | NUMERICAL |
| Atoms | 5199 (perfect) + 20 (inserted half-plane) = 5219 per 3.840 Å repeat | All atoms of one repeat. Repeated along the beam they make about 8.2 million atoms over the 6023 Å path at (008). | DERIVED_HERE |
| Lattice built as one continuous crystal | yes | All strips are cut from the same lattice, so the steps are genuine lattice steps and contain no hidden offsets. | method |

## 3. Buried dislocation (strip 3)

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Type | Lomer dislocation, pure edge | The usual misfit dislocation at (001) Si/SiGe interfaces. It matches your textbook picture: an extra half-plane of atoms that ends inside the crystal. | ASSUMPTION (PROJECT_INPUT items 23–24) |
| Burgers vector b | a/2[-110], length 3.840 Å | The closure failure of a loop of atomic steps around the line. Here it lies in the surface plane, perpendicular to the line. It is a full lattice vector, so the crystal is perfect away from the core. | ASSUMPTION |
| Sign convention | b = circuit integral of du, counter-clockwise about the line direction | With this sign the extra half-plane points up to the surface and the surface bulges upward. | convention (docs/08) |
| Line direction | [110], along the beam | The line runs along the beam, so the field varies only across the beam. | ASSUMPTION |
| Depth | 25 Å (2.5 nm) | Distance from the surface to the core. The surface bump is about 2 × depth = 5 nm wide; its height does not depend on depth. | ASSUMPTION (PROJECT_INPUT item 25) |
| Position | y = 384 Å (centre of strip 3) | | layout |
| Elastic model | isotropic, half-space with a traction-free surface | Displacement field of a straight dislocation below a free surface, from complex potentials. It is checked numerically: the surface is traction-free, the Burgers circuit closes to b and the bulk is in equilibrium. Si is in fact anisotropic (Zener ratio 1.56). | ASSUMPTION (D1) |
| Poisson ratio ν | 0.22 | Isotropic average for Si. It changes the field inside the crystal but not the surface relief, which is exactly independent of ν. | ASSUMPTION (D2) |
| Surface bump height | b/π = 1.22 Å | The surface rises by b/π above the core relative to far away. This is what the hologram mainly sees. | DERIVED_HERE |
| Core region | atoms within about 3 Å of the line | Linear elasticity fails here: 2 atoms come closer than 2.0 Å (bond length 2.35 Å). A relaxed core would need an interatomic potential or DFT. | limitation |
| Periodic seam | y = 76.8 Å (middle of strip 1) | The extra half-plane adds a plane of atoms. In a periodic cell that plane is inserted at a seam where the crystal is otherwise perfect. A small linear correction makes the seam close exactly. It leaves a tilt of 0.024 Å across the cell (about 0.2 rad of phase), which the ramp fit on strip 1 removes. | NUMERICAL |
| Seam merge tolerance | 0.5 Å | Atoms that land within 0.5 Å of each other at the seam are merged into one. | NUMERICAL |

## 4. Reflection and angles

| Parameter | (008) | (0,0,12) | Explanation | Status |
|---|---|---|---|---|
| Reflection | specular (008) | specular (0,0,12) | The Bragg reflection selected by the objective aperture (the "dark-field" beam). On Si(001) only (004), (008) and (0,0,12) are allowed; (002), (006) and (0,0,10) are forbidden. (008) is the working reflection. | ASSUMPTION (PROJECT_INPUT items 4, 9) |
| Plane spacing d | 0.679 Å | 0.453 Å | a/8 and a/12. | DERIVED_HERE |
| Mean inner potential V₀ of the simulation potential | 13.91 V | same | Average electrostatic potential of the crystal for this potential model. It refracts the beam at the surface. | DERIVED_HERE |
| V₀ used by the geometric model elsewhere | 12.0 V | same | Literature-type value. Changing V₀ by 1 V moves the Bragg angle by about 0.2 mrad and the step phase by about 0.3 rad. | ASSUMPTION (B1; PROJECT_INPUT item 20) |
| Critical angle θ_c | 9.00 mrad | same | Below this internal angle electrons cannot leave the crystal. | DERIVED_HERE |
| Internal Bragg angle | 18.47 mrad | 27.71 mrad | Bragg condition inside the crystal, where the wavelength is shortened by V₀. | DERIVED_HERE |
| External Bragg angle | 16.13 mrad | 26.21 mrad | The same condition seen from vacuum after refraction at the surface. | DERIVED_HERE |
| Operating angle | 16.93 mrad (+0.8) | 25.61 mrad (−0.6) | Angle of the incident beam used for the holograms: the maximum of the simulated flat-surface rocking curve, as one would set it in the microscope. Dynamical effects shift the maximum away from the simple Bragg angle. | DERIVED_HERE (rocking curve) |
| Height sensitivity q = 2k sin θ | 8.48 rad/Å | 12.83 rad/Å | Phase per ångström of surface height. | DERIVED_HERE |
| Wrap period λ/(2 sin θ) | 0.741 Å | 0.490 Å | Height change that gives a full 2π of phase, so heights are measured modulo this value. | DERIVED_HERE |
| Expected step phase (4 layers) | −46.1 rad, wrapped −2.09 | −69.7 rad, wrapped −0.57 | At a Bragg reflection a whole-lattice step nearly cancels to a multiple of 2π. What remains comes from refraction, so it is sensitive to V₀ and to the angle. | DERIVED_HERE |
| Expected dislocation phase (b/π relief only) | ≈ −10.4 rad | ≈ −15.7 rad | Surface bump × height sensitivity. The strain inside the crystal adds a little more. | DERIVED_HERE |
| Foreshortening 1/sin θ | 59 | 39 | Along the beam, the image is compressed by this factor relative to the surface. Across the beam it is not compressed. | DERIVED_HERE |
| (004) | 2.09 mrad, 1.05 rad/Å | | Exits barely above the critical angle and is 8 times less sensitive. Shown with the geometric model only. | DERIVED_HERE |

## 5. Multislice numerics

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Method | custom grazing-incidence multislice, numpy (cupy on GPU) | The wave is propagated along the beam through thin slices of crystal. Each slice adds a phase from its projected potential, and free-space propagation connects consecutive slices. | method (not yet validated against abTEM) |
| Grid | 1728 (x) × 3600 (y) pixels | Sampling of each slice. | NUMERICAL |
| Pixel along the normal dx | 0.100 Å | Converged: halving it changes the reflectivity by less than 2%. | NUMERICAL (converged) |
| Pixel across the beam dy | 0.128 Å | Must be 0.13 Å or smaller. At 0.39 Å the reflectivity is wrong by 40% at (008) and by a factor of 1.5 for Si(111). See fig_convergence a. | NUMERICAL (converged) |
| Cell along the normal | −58 to +114.8 Å (172.8 Å) | Crystal below 0, vacuum above. The vacuum must hold the incoming and reflected sheets, including the band reflected by strip 2, which exits 2h = 10.9 Å higher. | NUMERICAL |
| Slice thickness | 1.920 Å (2 slices per 3.840 Å repeat) | One atomic layer per slice, as the crystal structure along [110] requires. | NUMERICAL |
| Number of slices | 3137 (008), 2074 (0,0,12) | Enough for the sheet to descend to the surface, reflect and rise back to its starting height. | DERIVED_HERE |
| Path length along the beam | 6023 Å (008), 3982 Å (0,0,12) | 2 × (sheet centre height) / tan θ. | DERIVED_HERE |
| Anti-aliasing band | 2/3 of Nyquist: 3.33 Å⁻¹ (x), 2.60 Å⁻¹ (y) | Spatial frequencies above this are removed every slice, to avoid wrap-around errors. Both beams (at most 1.0 Å⁻¹) are well inside it. | NUMERICAL |
| Propagator | exact (non-paraxial) | The free-space step uses the exact dispersion relation, which avoids the paraxial phase error (0.026 rad at 45 mrad over a 198 A cell; docs/03 section 5). | method |
| Output plane | exit plane of the cell, no back-propagation | The wave is taken where it physically leaves the cell. The previous repository took it at the mid-plane by mistake. | method |
| Precision | complex64 waves, complex128 potential sums | Single precision for propagation, double for building the potentials. | NUMERICAL |
| Runtime | 26 min (008), 17 min (0,0,12) on a 4-core CPU | Expected to be minutes on the 12 GB GPU. | record |

## 6. Crystal potential, vibrations and absorption

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Atomic scattering factors | Peng et al. (1996), high-angle fit, Si coefficients from abTEM 1.0.6 | Converts atom positions into the electrostatic potential the electrons feel. The coefficients were read from abTEM's data file; the paper itself was not read. | SECTION_READ (data file) |
| Projection | each atom projected entirely into its own slice | Standard multislice approximation. It is exact here, because each slice holds exactly one atomic layer. | method |
| Debye–Waller factor B | 0.46 Å² (rms vibration 0.076 Å per axis) | Thermal vibrations smear the atoms and weaken high-angle scattering. A static average is used, not a frozen-phonon ensemble. | ASSUMPTION |
| Absorption (imaginary potential) | 5% of the real potential (0.70 V on average) | Represents electrons lost to inelastic scattering. It sets the absolute reflectivity and how deep the beam probes. This is a placeholder, not a sourced value. It matters for intensities more than for phases. | ASSUMPTION (placeholder; PROJECT_INPUT item 21) |
| Bulk absorber | from 38 Å below the surface: quadratic ramp over 14 Å to 60 V, then constant to the cell bottom | Absorbs everything that enters deep into the crystal, so nothing comes back through the periodic boundary. This mimics a semi-infinite crystal. | NUMERICAL |

## 7. Illumination

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Beam shape | plane-wave sheet, uniform across the beam | A beam limited in height only. It enters through vacuum above the crystal, never through the crystal's end face. | method |
| Sheet centre and height | 51 Å centre, 80 Å high (11–91 Å above strip 1), 4 Å soft edges | The height sets how long a stretch of surface is lit: 4724 Å at (008) and 3123 Å at (0,0,12). It must be long enough for the reflected wave to build up dynamically. A 30 Å sheet biased the (0,0,12) step by 0.8 rad (fig_convergence b). | NUMERICAL (checked) |
| Angular spread of the sheet | λ/H ≈ 0.31 mrad | A finite sheet contains a small range of angles. The real convergence of the microscope illumination is unknown and is critical for tall features. | NUMERICAL; real value PROJECT_INPUT item 3 |
| Tilt | entered as a phase ramp exp(−2πi sinθ x/λ) at the entrance plane | Exact representation of the glancing incidence, within the anti-aliasing band. | method |

## 8. Imaging optics

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Vacuum mask | keep x > 8 Å (3 Å soft edge) | Only the wave that has left the crystal is used. The mask sits above the raised strip. | NUMERICAL |
| Objective aperture | radius 0.06 Å⁻¹ = 1.5 mrad, centred on the specular beam | Selects the reflected beam (dark field) and sets the resolution, about 1/0.06 ≈ 17 Å. Phase gradients steeper than it passes are lost, which is why the amplitude drops near the core at (0,0,12). | ASSUMPTION (PROJECT_INPUT item 4) |
| Lens aberrations | none | Defocus, spherical aberration and drift are not included yet. | limitation |

## 9. Hologram and reconstruction

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Reference wave | tilted plane wave, uniform amplitude (model R1) | The wave that interferes with the reflected beam to make the hologram. The biprism's real reference may be curved or partly reflected. | ASSUMPTION (B5; PROJECT_INPUT item 15) |
| Fringe spacing | 5 Å at the specimen (carrier 0.2 Å⁻¹, reference tilted 5.0 mrad) | It must exceed 3 × the aperture radius (0.18 Å⁻¹) so that the sideband does not overlap the centre band. | ASSUMPTION (PROJECT_INPUT item 16) |
| Reference amplitude | equal to the mean object amplitude on strip 1 | Gives maximum fringe contrast. | NUMERICAL |
| Detector noise | Poisson, 400 counts per pixel, seed 20260930 | Shot noise of the recording. Pixels are simulation pixels (0.10 × 0.128 Å at the specimen), not detector pixels. | ASSUMPTION (PROJECT_INPUT items 5–6) |
| Carrier location | found on an empty (reference-only) hologram | Using the object hologram can lock onto the wrong peak. That defect was found in the previous code. | method |
| Sideband mask | circle of radius 0.06 Å⁻¹ | Cuts out the sideband that carries the object wave. Equal to the aperture, so no information is lost. | ASSUMPTION (PROJECT_INPUT item 19) |
| Reference correction | divide by the empty-hologram reconstruction | Removes the reference wave's own phase and amplitude. | method |
| Phase unwrapping | along y, with branches fixed by the profile averaged along the beam | Converts the wrapped phase (−π to π) into a continuous phase. | method |
| Ramp removal | linear fit on strip 1 only (25 Å from its edges) | Removes residual tilt, the way an experimenter would, using a known-flat area. | method |
| Image rows used | exit heights 28.8–80 Å (008), 54–67.6 Å (0,0,12) | The rows where both terrace heights are fully lit (more than 50% of their peak). | NUMERICAL |

## 10. Geometric (fast) model used for comparison

| Parameter | Value | Explanation | Status |
|---|---|---|---|
| Model | column (kinematic) model plus the surface path difference | Phase = average over depth of the lattice phase −G·u (weighted by penetration) minus the vacuum path change (q_ext − G)·u at the surface. It reduces exactly to −q_ext·R for a rigid step (tested). It contains no multiple scattering and no propagation. | DERIVED_HERE |
| Penetration depth Λ | 3 Å and 12 Å (scanned) | How deep the reflection samples. The phase changes by less than 3% across this range. In reality Λ is set by extinction and absorption. | ASSUMPTION (D3) |
| Layers summed | 120 × 1.358 Å = 163 Å | Far deeper than Λ, so the sum is complete. | NUMERICAL |
| Same displacement field | yes | Uses exactly the field applied to the atoms, so differences from the multislice are physics, not set-up. | method |

---

## Which parameters must come from the laboratory

Before any quantitative comparison with experiment, these assumptions must be replaced by
measured values (PROJECT_INPUT items in `docs/06_project_inputs_required.md`):

* the reflection and glancing angle, with a measured rocking curve (items 4, 7, 9);
* the beam azimuth (8);
* the illumination convergence (3), which is critical for any step taller than about 1 nm;
* the aperture size (4);
* the fringe spacing and reference-wave path (15, 16);
* the detector and dose (5, 6);
* V₀ (20);
* the absorptive potential (21);
* the surface state (12);
* the real defect type, depth and Burgers vector (23–27).
