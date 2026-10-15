# Roadmap: a reflection electron microscopy platform

**Goal.** One physical model of a crystal surface inside the microscope. Every reflection
measurement (RHEED patterns, REM images, off-axis holograms, 4D-STEM in reflection) is simulated
from it, and it can be inverted to recover the surface: heights, strain and defects.

**End point.** Reflection-mode electron ptychography. The literature search
(`docs/literature/reading_list_ptychography.md`) found no published electron ptychography in RHEED
geometry.

```
  SAMPLE                  FORWARD MODEL               MEASUREMENTS              INVERSION
  any crystal and facet   grazing multislice          RHEED, rocking curves     holography -> phase
  steps, reconstructions  (+ Bloch-wave check)        REM bright/dark field     ptychography -> heights,
  oxide, adsorbates       + the microscope:           off-axis holography          strain, defects
  buried defects            tilts, biprism,           4D-STEM in reflection
  atoms from MD/DFT         aberrations, coherence,
                            detector (measured MTF)
```

## Samples

| Sample | Surface imaged | Frame in the code | Status |
|---|---|---|---|
| Cleaved Si(110) wafer, March 2026 data (holograms 13 Mar, dark field 16 Mar, reflection session 19 Mar) | **{111} cleavage facet** | `geometry.SI111_FRAME`: (1-11) surface, beam along [110] | used for the first benchmarks; to be compared with the March data |
| Si(100), current work | **(001)** | `geometry.SI001_FRAME`: (001) surface, beam along [110] | three-strip sample, 50 nm dislocations (`docs/results/`) |
| Later: GaN, oxides, other materials | any (hkl) and azimuth | to add: a general `SlabFrame` from (hkl) and azimuth | Stage 5 |

## Stages

### Stage 1: reflection holography simulation (done; validation continues)

* **Built:** Si(001) and Si(111) slabs, terraces, buried dislocations (isotropic half-space,
  periodic images, slip steps), a grazing multislice on CPU and GPU, a geometric model, and the
  hologram and reconstruction chain.
* **Results:** `docs/results/three_strips_results.md` and `docs/results/dislocations_50nm.md`.
* **Open item:** the illumination edge effects reported by Ma & Marks (1990) for tilted, smoothed
  beams; the fix is edge patching (Ma & Marks 1991).

### Stage 2: validation and a digital twin of the microscope (next)

**Validation ladder**, each step a pytest test:
1. Analytic limits: the wavelength, the refraction and step phase (Osakabe 1990), and the g·b
   fringe count.
2. An independent dynamical code: a Bloch-wave RHEED code on flat surfaces (sim-trhepd-rheed,
   checked first at 200 keV) and abTEM in transmission.
3. Published experiments: Osakabe 1989/1993, Banzhof & Herrmann 1993.
4. **Your own data.**

**Digital twin of the HF-3300 and the Merlin detector.** These come from measurements already in the
research folder:
* the **Merlin MTF, NNPS and relative DQE** (slanted edge, flat field). Note: the "50-350 keV" series are
  threshold settings at a fixed 200 keV beam, not beam energies (`MTF_CALIBRATIN_MERLIN/results/report.md`);
* the beam-tilt and stage-tilt calibration on Si(100) (Nov 2025);
* the image-plane correction (Jan 2026);
* the biprism settings (106.8 V, 0.0242 nm per pixel).

Simulated data then come out in the same format as the real data (`.dm3`/`.hm` stacks) and go
through **the same** processing code.

**Comparison 1: the March cleaved-Si data** ({111} facet).
* Find the reflection and glancing angle behind the stage alpha of about 4.1°. The mount ("vertical
  prototype") sets the relation between the two.
* Then compare holograms, phase and dark-field contrast.

**Comparison 2: the new Si(100) data.** Plan these measurements with the simulation: which
reflection, angle, aperture, biprism voltage and dose give the clearest signal.

**Batch API theory audit.** Phases 0, A, B and E of `docs/dev/HANDOFF_batch_plan.md`.

### Stage 3: a differentiable forward model and 4D-STEM in reflection

* **Port:** move the multislice kernel to **PyTorch on the GPU**, so that gradients with respect to
  the sample (and the probe and geometry) come for free. The numpy kernel stays as the reference
  that the tests compare against.
* **New simulation:** a scanned, convergent probe at grazing incidence, giving the diffraction
  pattern at every scan position (4D-STEM in reflection).
* **Footprint:** the probe footprint is stretched about 59 × along the beam at 16.9 mrad, so the
  scan steps are anisotropic.
* **Detector and sampling:** the detector collects more than one reflection; a single reflection
  in a small aperture gives only a smooth field, not atoms.
* **Prior art:** X-ray grazing-incidence multislice ptychography (Besley et al. 2025, PyGRAPES).
  Electron ptychography codes: PtyRAD, py4DSTEM.

### Stage 4: reflection ptychography (the thesis goal)

* **Reconstruction:** gradient-based, through the multislice model, recovering the surface potential
  or heights, the probe and the positions. Also ePIE and least-squares ML as baselines.
* **Synthetic data first:** known surfaces (steps, reconstructions, buried dislocations). Measure
  recovery against dose, overlap, angle and detector.
* **Theory:** the sampling and uniqueness conditions specific to reflection (one-sided penetration,
  the elongated footprint), derived and tested.
* **Then real data:** 4D-STEM in reflection on the HF-3300 with the Merlin detector.

### Stage 5: applications

* surface strain and buried defects;
* surface reconstructions (Si(001) 2×1, Si(111) 7×7);
* oxide/Si interfaces and adsorbates;
* other materials.

## Shared foundations (all stages)

* **Provenance:** every parameter carries an evidence label, and every equation cites a source page
  or is backed by a test (`docs/theory/model_assumptions.md`).
* **Compute:** the Alliance clusters (Fir, H100), using `hpc/` for job scripts and sweeps.
* **Literature:** `docs/literature/` (reading lists, surveys, the download checklist).
* **Research archive:** `tools/research_inventory/` maps the experimental sessions in the research
  folder, so that every comparison names its data set.
