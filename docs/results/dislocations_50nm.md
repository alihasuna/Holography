# Buried dislocations 50 nm below Si(001): 60° and Lomer, (008), 200 keV

Status: 2026-10-14. The 60° case was simulated by multislice at (008) on a 4-core CPU. The Lomer
case has only the geometric (column) model so far. (0,0,12) and the Lomer multislice are queued
for Fir (docs/guide/hpc_alliance.md section 5). The multislice kernel is not validated against abTEM or a dynamical
solver (docs/theory/buried_defects.md), so absolute values are smoke-test results; multislice and geometric mode go
through the identical hologram and reconstruction chain.

## 1. Samples

| | 60° dislocation | Lomer dislocation |
|---|---|---|
| Config | `configs/si001_60deg_50nm.yaml` | `configs/si001_lomer_50nm.yaml` |
| Burgers vector | a/2[011]: 2.72 Å normal, 1.92 Å in-plane edge, 1.92 Å screw | a/2[-110], 3.84 Å, in the surface plane |
| g·b at (008) | 4 | 0 |
| Depth, line | 50 nm, along the beam [110] | same |
| Origin | glided in on (1-11) from the surface: a 2-layer slip step 35 nm from the core | sessile (reaction product), no slip step |
| Surface relief | +0.8 Å before the step, −2.6 Å step, recovers through −0.8 Å over the core | symmetric 1.2 Å bump, FWHM about 100 nm |

* **Cell.** Three strips: reference 123 nm, raised by 5.43 Å 123 nm, dislocation 492 nm. The cell
  is 0.74 µm wide, 1728 × 57 600 grid points, with 81 952 atoms per 3.84 Å repeat.
* **Field.** The cell is a periodic array of dislocations 0.74 µm apart. The field is summed over
  ±20 images and is converged to < 0.001 Å; for the 60° case the seam sits on the slip trace.

## 2. Results at (008)

| Quantity | 60° multislice | 60° geometric (Λ 3 Å) | Lomer geometric |
|---|---|---|---|
| Operating angle | 16.93 mrad (effective 16.96) | same | same |
| Specular fraction in the aperture | 0.0165 | n/a | n/a |
| Step, strip 2 − strip 1 | −2.138 rad | −2.154 rad | −2.22 rad |
| −q_ext h alone | −2.159 rad | | |
| Phase far beyond the core | −25.43 rad (−8π = −25.13) | same to 0.01 rad | returns to −0.5 rad |
| Largest excursion from strip 1 | −25.80 rad | −25.80 rad | −10.5 rad, FWHM 101 nm |
| Core minus strip-3 flanks | −5.79 rad | −5.78 rad | −9.47 rad |
| Phase difference multislice − geometric | ≤ 0.05 rad (0.57 rad only at step edges, aperture ringing) | | |
| Amplitude | dip to 0.82 at 31 nm before the core (3.5 nm past the slip step), 0.96 at the core, back to 1.00 by +25 nm; strip 2 at 0.974 | 1.00 (no contrast) | 1.00 |
| Noisy hologram (400 counts per pixel) | identical to 0.001 rad | | |

Runtime: 797 s for the potentials and 6641 s for 3137 slices, on 4 CPU cores with scipy.fft.

## 3. Reading

* **The 60° dislocation is identified by its net phase offset.** Across the dislocation the phase
  does not return: it settles at −2π g·b = −8π, which is four extra hologram fringes, most of them
  within 50 nm of the core. A Lomer dislocation (g·b = 0) gives a closed bump instead. The count of
  net fringes measures g·b, the reflection-geometry analogue of the g·b criterion of
  diffraction-contrast TEM. At (0,0,12), g·b = 6.
* **The slip step is nearly invisible in phase.** A 2-layer step is a lattice translation, which
  the dark-field wave sees only modulo the reflecting planes, so it leaves the refraction residual.
  It shows up as an abrupt fringe shift in the hologram (fig_hologram_60deg_50nm, a).
* **Multislice adds amplitude contrast.** The phase agrees with the column model to 0.05 rad. The
  amplitude, however, drops by up to 18 % between the slip step and the core, where the lattice
  planes are most tilted (rotations of order b/(2π r), about 1 mrad, comparable to the rocking
  width). It recovers over about 50 nm, and the column model has no such contrast. This is the
  strain signature at 50 nm depth. Its size depends on the operating angle and on the unsourced
  absorption (PROJECT_INPUT item 21), so treat it as qualitative.
* **The image depends on exit height.** The multislice wave varies with exit height
  (fig_hologram_60deg_50nm, c and e: a darker band near 5 to 6 nm): the reflected band builds up
  dynamically along the footprint. The 1D results average over the rows used (2.8 to 7.9 nm).

## 4. Figures and commands

| Figure | Content |
|---|---|
| `docs/figures/fig_60deg_50nm` | relief and cross-section; (008) phase and amplitude across the cell and over the core; 60° multislice (solid) with geometric (dashed), Lomer geometric |
| `docs/figures/fig_hologram_60deg_50nm` | recorded holograms, reconstructed complex wave (multislice, real exit-height rows) and cos φ interferograms; 60° next to Lomer |
| `docs/figures/fig_50nm_geometric_preview`, `fig_hologram_50nm_geometric_preview` | the same, geometric model only |

```bash
python scripts/run_sections.py --config configs/si001_60deg_50nm.yaml --only "(0,0,8)"        # about 2 h on 4 cores
python scripts/run_sections.py --config configs/si001_lomer_50nm.yaml --geometric-only --out outputs/geometric_only
python scripts/figures_60deg.py --config configs/si001_60deg_50nm.yaml \
    --results outputs/si001_60deg_50nm/reconstruction/results.npz \
    --compare-config configs/si001_lomer_50nm.yaml \
    --compare-results outputs/geometric_only/si001_lomer_50nm/reconstruction/results.npz --stem fig_60deg_50nm
python scripts/figures_hologram_50nm.py --results60 outputs/si001_60deg_50nm/reconstruction/results.npz \
    --resultsL outputs/geometric_only/si001_lomer_50nm/reconstruction/results.npz --kind ms \
    --rows60 outputs/si001_60deg_50nm/reconstruction/rows_008.npz --stem fig_hologram_60deg_50nm
```

Open: (0,0,12) and the Lomer multislice (Fir), the absorption value, validation of the kernel
(milestone M2), anisotropic elasticity (silicon has a Zener ratio of 1.56; the field here is
isotropic), and the 2×1 surface reconstruction.
