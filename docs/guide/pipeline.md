# The simulation pipeline, step by step

From atoms to a reconstructed phase map. Each step names the code that does it and the
numbers used in the realistic case (`configs/si001_60deg_50nm.yaml`).

```
config ─► 1 crystal ─► 2 defect field ─► 3 forward model ─► 4 hologram ─► 5 reconstruction ─► 6 analysis
                                          (multislice or geometric)
```

## 0. Configuration

* **File:** one YAML file per sample (`configs/`).
* **Content:** every number the run uses: beam, crystal, sample, defects, multislice grid,
  holography.
* **Evidence labels:** every value carries a label, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE or
  SMOKE_TEST, plus a note on where it comes from. `reflection_holo/provenance.py` refuses
  unlabelled values.
* **Reference:** every parameter is explained in `docs/guide/parameters.md`.

## 1. Build the crystal

**Code:** `reflection_holo/crystal.py`, `reflection_holo/structure/sections.py`

* **Slab frame:**
  * x is the outward surface normal, [001];
  * y lies in the surface, across the beam, [1-10];
  * z is the beam azimuth, [110].
* **Strips:** side-by-side strips parallel to the beam, all cut from one continuous lattice, so
  every strip appears in the same image and strip 1 is the in-image reference.
  1. Strip 1: the reference.
  2. Strip 2: raised by 4 atomic layers (0.54 nm, one lattice constant), a known calibration step.
  3. Strip 3: holds the buried defect.
* **Periodicity:** the crystal is periodic along the beam with a 3.84 Å repeat, so one repeat is
  enough. The realistic cell is 0.74 µm wide and 5.6 nm deep, with 82 000 atoms per repeat.

## 2. Apply the defect's elastic field

**Code:** `reflection_holo/defects/dislocation.py`

* **Field:** the analytic displacement of a straight dislocation parallel to a free surface,
  using isotropic elasticity (complex potentials plus image terms). It is checked in
  `tests/test_dislocation.py`: traction-free surface, Burgers-circuit closure, equilibrium.
* **Periodic cell:** the cell is periodic across the beam, so the field is summed over ±20
  periodic images. Each image is taken relative to its value above the primary line; the sum
  converges, and the cell advances by exactly one b.
* **Extra plane:** a net Burgers vector needs an extra (or missing) plane of atoms. The builder
  inserts it at a seam.
* **60° dislocation:** the seam sits where its glide plane meets the surface, which reproduces the
  slip step of a dislocation that glided in from the surface.
* **Result:** sub-ångström surface relief and tilted near-surface planes. The core, 50 nm down, is
  never reached by the electrons.

## 3. Forward model: the reflected wave

### 3a. Multislice (full dynamical scattering)

**Code:** `reflection_holo/forward/multislice.py`. Runs on numpy (CPU, with multithreaded
`scipy.fft`) or cupy (GPU).

1. **Potential.**
   * The atoms become projected potentials: Peng 1996 scattering factors, a Debye–Waller factor,
     and an absorptive imaginary part.
   * This gives two slice potentials per 3.84 Å repeat, each 1.92 Å thick.
   * A bulk absorber below the slab emulates a semi-infinite crystal.
2. **Illumination.**
   * A sheet beam in the vacuum above the surface: 200 keV, λ = 0.0251 Å.
   * It is tilted towards the surface by the glancing angle, 16.93 mrad for (008): the maximum of
     the flat-surface rocking curve (`scripts/rocking_flat.py`).
3. **Propagation.**
   * Transmit through a slice, then propagate with the exact Fresnel propagator; repeat.
   * About 3100 slices for (008), so the beam enters the surface, reflects and leaves.
   * The 2/3 band limit and the beam angles are checked at every run.
4. **Dark field.**
   * A vacuum mask keeps the wave that has left the surface.
   * An objective aperture of radius 0.06 Å⁻¹ (1.5 mrad) around the specular (008) beam selects
     the reflection.
   * The result is the complex dark-field wave ψ(x, y): image rows are exit heights, columns run
     across the beam.

**Sampling that matters:**
* across the beam, dy ≤ 0.13 Å;
* sheet height of 80 Å (a long enough footprint);
* see `docs/results/three_strips_results.md`, section 4.

### 3b. Geometric (column) model

**Code:** `reflection_holo/forward/geometric.py`

* **Method:** each atomic layer contributes a phase −q·u, with u the displacement of that layer,
  weighted by an absorption depth.
* **Refraction:** included through the internal and external momentum transfer.
* **Cost and limits:** it takes seconds and has no multiple scattering, so it gives no
  strain-induced amplitude contrast.
* **Use:** as an independent check of the multislice phase, which agrees to 0.05 rad for the
  50 nm cases.

## 4. Form the hologram

**Code:** `reflection_holo/holography.py`, `form_hologram`

* **Intensity:** I = |ψ + R|², with R a tilted plane-wave reference whose fringes are 5 Å apart
  at the specimen.
* **Noise:** Poisson counting noise at 400 counts per pixel.
* **Empty hologram:** an empty hologram (R alone) is recorded with the same noise.

## 5. Reconstruct

**Code:** `reflection_holo/holography.py`, `reconstruct`

1. Take the FFT of the hologram; the carrier is located on the empty hologram.
2. Cut out the sideband with a circular mask equal to the objective aperture, then inverse-FFT it.
3. Divide by the empty hologram's sideband, which removes the reference and detector imperfections.
4. Average over image rows, unwrap the phase along y, and remove a linear ramp fitted on strip 1
   only.

The chain is exact (to 10⁻⁹) for a band-limited object when the carrier exceeds 3 × the aperture
radius (`tests/test_holography.py`).

## 6. Analyse

**Code:** `scripts/run_sections.py` (metrics, `summary.json`) and `scripts/figures_*.py`
(Nature-style figures, captions in `docs/figures/CAPTIONS.md`).

**Metrics:**
* step phase between strips 2 and 1;
* dislocation phase signal and width;
* amplitude contrast;
* multislice against geometric model;
* noisy against noiseless.

**Reading the phase:**
* **Width ≈ 2 × depth:** the width of the surface signal is about twice the dislocation depth.
* **g·b:** the net phase offset across a dislocation is −2π g·b, the number of extra fringes. For
  a 60° dislocation at (008), g·b = 4; for a Lomer dislocation, 0.

## Where to start

| Goal | Command |
|---|---|
| See the whole chain in 2 s | `python examples/01_first_hologram.py` |
| Size a run before starting it | `python scripts/run_sections.py --config <cfg> --dry-run` |
| Geometric model at full size, any CPU | `python scripts/run_sections.py --config <cfg> --geometric-only` |
| Full multislice, CPU | `python scripts/run_sections.py --config <cfg> --only "(0,0,8)"` |
| Full multislice, GPU cluster | `docs/guide/hpc_alliance.md` |
