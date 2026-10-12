# Off-axis holography pipeline for ElectroSim, recorded by gemicro

The si110 reflection-holography pipeline (`hussienba/si110-reflection-holography` @ `6694959`), ported to
ElectroSim and fixed according to this repository's audit. Every stage is a script driven by one parameter file
and runs through `gemicro run`. The GPU stage uses abTEM in `em-abtem`; all holography stages run on the CPU in
`em-holography` with HoloSpy. The pipeline adds the stages the audit found missing: an intensity hologram with
a vacuum reference hologram, a true sideband reconstruction, and validation against the known truth with
controls that must fail.

Status (2026-10-12): developed and tested in local copies of the ElectroSim environments (same package versions,
Python 3.13 instead of 3.12, CPU only), then audited independently (findings and fixes in `PORTING.md` §3).
**Not yet run on ElectroSim and never run on a GPU.** The GPU code path (`device: gpu`) follows gemicro 0.5.6's
rules (`.get()` before any numpy use, memory pools released). The audit ran it with every abTEM array replaced by
a CuPy-like object that refuses implicit conversion, and it completed. A real GPU run will happen first on ElectroSim.

## 1. What is in this folder

```
electrosim/
  code/                       -> copy to <project>/code/
    si110_cleave_slab_generator.py   em-abtem   CPU   Si[110] cleave-edge slab with (1,-1,1) terraces
    multislice_forward_model.py      em-abtem   GPU   abTEM plane-wave exit wave (+ σ·V_proj ground truth)
    multislice_tilt_series_runner.py em-abtem   GPU   the same for a list of beam tilts
    specular_filter.py               em-holo    CPU   objective aperture on one spot -> image wave
    hologram_formation.py            em-holo    CPU   object + vacuum reference holograms (new stage)
    holo_recon.py                    em-holo    CPU   sideband reconstruction with HoloSpy (new stage)
    holo_validate.py                 em-holo    CPU   metrics against the truth, pass/fail, controls (new)
    step_height_reflection_formula.py em-holo   CPU   signed terrace step phases/heights (reflection)
    process_all_tilts.py             em-holo    CPU   filter -> hologram -> recon -> steps for a tilt series
    import_experimental_holograms.py em-holo    CPU   .dm4/.emd/.tif/.hspy holograms -> the same recon path
    output_validator.py              either     CPU   checks every stage folder (shapes, units, NaN, plots)
    holo_common.py, holo_optics.py, holo_sideband.py, holo_metrics.py   shared modules (numpy)
    run_pipeline.sh                  the whole first test as gemicro commands (copy it to code/ too)
  params/                     -> copy to <project>/params/   (YAML; every value commented)
  tests/                      -> copy to <project>/code/tests/ (optional; runs without pytest)
  PORTING.md                  file-by-file map from the si110 pipeline and the audit defect each change fixes
```

The environment each script needs is stated at the top of the file. No script installs anything; nothing
outside the ElectroSim environments is imported (numpy, scipy, ase, abTEM, CuPy, scikit-image, HoloSpy,
HyperSpy, matplotlib, PyYAML, which comes with dask and HyperSpy). JSON parameter files work as well as YAML.

## 2. On ElectroSim: the exact commands

Once, in a terminal on the hub (your own user):

```bash
cd /srv/lab-shared/projects
gemicro init holo-electrosim --group blackburn-uvic          # or your existing project
cd holo-electrosim
mkdir -p code params
cp -r <checkout>/electrosim/code/* code/
cp <checkout>/electrosim/run_pipeline.sh code/
cp <checkout>/electrosim/params/*.yaml params/
cp -r <checkout>/electrosim/tests code/tests                  # optional
git init && git add code params && git commit -m "holography pipeline"   # gemicro records the commit
```

Then either run everything with `bash code/run_pipeline.sh` (it prints each step, stops at the first error and
ends with `gemicro verify`), or step by step from the project root:

```bash
# 1. slab (CPU, em-abtem)
gemicro run --kind sim --name slab --params params/slab.yaml --output sims/slab -- \
  /opt/envs/em-abtem/bin/python code/si110_cleave_slab_generator.py --params params/slab.yaml --output sims/slab

# 2. exit wave on the GPU (em-abtem): look first
gemicro gpu
gemicro run --kind sim --name exit-wave --input sims/slab/si110_slab.extxyz --params params/exit_wave.yaml \
  --output sims/exit-wave -- /opt/envs/em-abtem/bin/python code/multislice_forward_model.py \
  --params params/exit_wave.yaml --structure sims/slab/si110_slab.extxyz --output sims/exit-wave

# 3. objective aperture -> image wave (CPU, em-holography)
gemicro run --kind process --name image-wave --input sims/exit-wave/exit_wave.npy \
  --params params/specular_filter.yaml --output derived/image-wave -- /opt/envs/em-holography/bin/python \
  code/specular_filter.py --params params/specular_filter.yaml --exit-wave sims/exit-wave --output derived/image-wave

# 4. object + reference holograms
gemicro run --kind process --name hologram --input derived/image-wave/image_wave.npy \
  --params params/hologram.yaml --output derived/hologram -- /opt/envs/em-holography/bin/python \
  code/hologram_formation.py --params params/hologram.yaml --image-wave derived/image-wave --output derived/hologram

# 5. reconstruction
gemicro run --kind analysis --name holo-recon --input derived/hologram/hologram.npy \
  --input derived/hologram/reference_hologram.npy --params params/holo.yaml --output derived/holo-recon -- \
  /opt/envs/em-holography/bin/python code/holo_recon.py --params params/holo.yaml --hologram derived/hologram \
  --output derived/holo-recon

# 6. validation (expected: "OUTCOME: PASS as expected", exit status 0)
gemicro run --kind analysis --name holo-validate --input derived/holo-recon/phase_unwrapped.npy \
  --input derived/hologram/image_wave_detector.npy --input sims/exit-wave/ground_truth_phase.npy \
  --params params/validate.yaml --output derived/holo-validate -- /opt/envs/em-holography/bin/python \
  code/holo_validate.py --params params/validate.yaml --recon derived/holo-recon --hologram derived/hologram \
  --exit-wave sims/exit-wave --slab sims/slab --output derived/holo-validate

# 7. the two controls: reconstruct with the control parameters, validate with validate_control.yaml
#    (expected: "OUTCOME: FAIL as expected", exit status 0). Shown for no_reference; repeat with wrong_sideband.
gemicro run --kind analysis --name holo-recon-control-no-reference --input derived/hologram/hologram.npy \
  --input derived/hologram/reference_hologram.npy --params params/holo_control_no_reference.yaml \
  --output derived/holo-recon-control-no-reference -- /opt/envs/em-holography/bin/python code/holo_recon.py \
  --params params/holo_control_no_reference.yaml --hologram derived/hologram --output derived/holo-recon-control-no-reference
gemicro run --kind analysis --name holo-validate-control-no-reference \
  --input derived/holo-recon-control-no-reference/phase_unwrapped.npy --params params/validate_control.yaml \
  --output derived/holo-validate-control-no-reference -- /opt/envs/em-holography/bin/python code/holo_validate.py \
  --params params/validate_control.yaml --recon derived/holo-recon-control-no-reference --hologram derived/hologram \
  --exit-wave sims/exit-wave --slab sims/slab --output derived/holo-validate-control-no-reference

# 8. check the folders, then the ledger
gemicro run --kind analysis --name check-outputs --params params/output_validator.yaml --output derived/check-outputs -- \
  /opt/envs/em-holography/bin/python code/output_validator.py --params params/output_validator.yaml \
  --stage sims/slab --stage sims/exit-wave --stage derived/image-wave --stage derived/hologram \
  --stage derived/holo-recon --stage derived/holo-validate --output derived/check-outputs
gemicro verify
```

Rules the scripts follow (the gemicro contract): every setting comes from the one `--params` file (a missing key
and an unknown key are both errors, so a typo never falls back to a default); inputs are named on the command line;
everything is written to `--output` only, through a staging folder that is renamed at the end (a crashed run never
looks finished); the scripts refuse to write inside `raw/`, `.gemicro/` or the project root, and refuse a
non-empty output folder unless `--overwrite` is given; seeds are in the parameter files; arrays are `.npy` with a
JSON sidecar (`<stage>.json`) giving dtype, shape, axes, units and sampling of every array, the physics, the
parameters, input SHA-256s and package versions; plots are PNG; a summary is printed at the end. Re-running a
step into the same folder needs `--overwrite`, and gemicro records the new files.

## 3. The first test case, and why

`params/slab.yaml`: the si110 cleave-edge slab seen in transmission along the [110] beam at zero tilt (the
profile view of the (1,-1,1) surface), 200 keV.

* The same structure, frame and generator as the reflection work, so the first GPU run exercises the code path
  the reflection runs will use.
* 99.8 Å (26 × 3.840 Å) along the beam: a phase of about 0.8 rad in the crystal, below π, typical of a holography
  specimen.
* 60 Å of vacuum on both sides of the slab inside the field: the phase reference region, and an edge a hologram
  must reproduce.
* Four 20 Å-wide terraces lowered by [0, 1, 2, 1] bilayers: every terrace boundary is a known ±3.1355 Å
  (d_111) shift of the surface edge, with both signs (a sign test) and no hidden step across the periodic boundary.
* Size: grid 2048 × 800 at 0.1 Å, 53 slices of 1.9201 Å (one (220) plane each: the box is 53 plane spacings long),
  33 696 atoms. The forward model estimates 0.43 GB of GPU memory and refuses to start above
  `limits.max_device_memory_GB` (6 GB). The exit wave is 13 MB.

Optics (`specular_filter.yaml`, `hologram.yaml`): a 6 mrad bright-field objective aperture (0.24 1/Å; it excludes the
(111) beams, so this is mean-inner-potential holography); 0.8 Å fringes at 30°, 0.2 Å detector pixels
(4 pixels per fringe, binning 2, detector 1024 × 400), carrier 5.2 × the object band limit; reference model R3 with
1.5 rad of curvature and a ramp (what reference normalisation has to remove); degree of coherence 0.40 and 0.1 Å
fringe drift; Gaussian MTF of 0.4 px; 5000 e/Å² (200 counts per pixel) for both holograms; Poisson noise. The
reconstruction (`holo.yaml`) uses HoloSpy's tanh aperture of 0.30 1/Å (3.3 Å resolution, 4.2 fringe spacings),
a Tukey window of 0.1 on both holograms, reference normalisation, scikit-image unwrapping, a vacuum reference
region and no detrending.

## 4. Expected outputs and numbers

Measured on 2026-10-12 with the exit wave computed on the CPU (`device: cpu`; the GPU result should agree to
float32 rounding), the whole chain run through gemicro 0.5.6 in a test project and `gemicro verify` passing:

| Quantity | Value | Where |
|---|---|---|
| exit-wave grid, sampling, slices, band limit | 2048 × 800, 0.0999 × 0.0998 Å, 53 × 1.9201 Å, 83.7 mrad | `sims/exit-wave/exit_wave.json` |
| mean inner potential of the Lobato parametrisation | 13.96 V over whole bilayer periods (neutral atoms; the sourced V0 is 12-12.5 V, ASSUMPTION) | same |
| vacuum fringe contrast, predicted / measured | 0.2960 / 0.2960 | `derived/hologram/hologram.json` |
| located carrier, spacing | (1.0813, 0.6264) 1/Å, 0.8003 Å (set: 0.8 Å at 30°) | `derived/holo-recon/recon.json` |
| HoloSpy engine vs numpy engine | max phase difference 3e-12 rad | same |
| vacuum phase noise, predicted √2/(μ√N) / measured | 0.0495 / 0.0492 rad | same |
| residues | 0 | same |
| **NCC against T_holo** (noise limit) | **0.988** (0.992) | `derived/holo-validate/validate.json` |
| **phase-scale slope against T_holo** | **1.0002** | same |
| residual RMS / local shot-noise prediction | 1.00 (1.25 against the vacuum value: noise is higher where the crystal lowers the amplitude) | same, `residual_map.png` |
| registration shift | (0, 0) px | same |
| terrace steps (true ±3.1355 Å) | -3.164, -3.110, +3.171, +3.102 Å | same, `terrace_profiles.png` |
| edge width 10-90 % of T_holo | 5.27 Å (aperture resolution 3.33 Å); single noisy profiles of the reconstruction give 5-7 Å | same |
| mask sensitivity ±20 % | RMS phase change 0.034-0.036 rad; steps move ≤ 0.06 Å | same |
| NCC / slope against σ·V_proj (projection approximation) | 0.970 / 0.75 | same |
| control: no reference normalisation | NCC 0.59, slope 1.33, residual 20 × noise; residual vs injected distortion NCC 0.97; holo_recon warns that the vacuum phase std is 7.7 × the prediction: FAIL as expected | `derived/holo-validate-control-no-reference/` |
| control: wrong sideband | NCC -0.988, slope -1.0002, residual 13 × noise: FAIL as expected | `derived/holo-validate-control-wrong-sideband/` |

Reading the two truths: **T_holo** is the image wave's phase band-limited by the same aperture: what a perfect
reconstruction of these holograms returns. It tests the hologram chain, and the reconstruction meets it to the
shot-noise limit. **T_proj** (σ·V_proj, the thin-object phase) is matched in shape (NCC 0.97) but not in scale (slope
0.75): on the [110] zone axis, dynamical scattering and the aperture (which removes the Bragg beams) lower the
direct-beam phase by about a quarter. That difference is physics, not a reconstruction error, and is why a
holographic mean-inner-potential measurement is made off the zone axis. The terrace-edge positions are
insensitive to both deliberate errors (a position survives a phase sign flip or a smooth distortion); the phase
values are not.

Run times on a 4-core cloud CPU (wall clock, from each sidecar's `wall_time_s`): slab 2 s; exit wave 18 s on the CPU
(the H100 slice should take a few seconds; not measured); image wave 3 s; holograms 2 s; reconstruction 3 s
(each control 3 s); validation 2 s; the whole `run_pipeline.sh` 47 s. Disk: about 120 MB for `sims/` and `derived/`.

Files: each stage writes its `.npy` arrays, its sidecar `<stage>.json`, and PNGs:
`exit_wave_phase.png`, `exit_wave_amplitude.png`, `ground_truth_phase.png`; `exit_wave_spectrum.png` (aperture),
`image_wave_*.png`; `hologram.png`, `hologram_zoom.png`, `reference_hologram.png`, `hologram_spectrum.png`;
`phase.png`, `phase_wrapped_raw.png`, `amplitude.png`, `sideband_selection.png`; `truth_T_holo.png`,
`reconstructed_phase.png`, `residual_map.png`, `phase_scale.png`, `terrace_profiles.png`.

## 5. Tests (laptop CPU, no GPU, under a minute)

```bash
/opt/envs/em-holography/bin/python code/tests/run_tests.py     # on ElectroSim (pytest is not in the envs)
/opt/envs/em-abtem/bin/python code/tests/run_tests.py          # adds the abTEM test, skips the HoloSpy ones
python -m pytest -q electrosim/tests                           # on a laptop with pytest
```

On a laptop: `python3.12 -m venv v && v/bin/pip install "abtem==1.0.10" "holospy==0.3" "hyperspy==2.4.0" scikit-image
pyyaml pytest` gives one environment in which all 30 tests pass (39 s with pytest; 29 run in em-holography alone,
the abTEM test in em-abtem). The physics checks include:

* the fringe spacing and orientation of a vacuum hologram match the biprism setting (< 0.5 %, < 0.5°);
* the vacuum fringe contrast equals coherence × drift sinc;
* a known phase step (1.0 and 2.5 rad, the latter above the 2.008 rad carrier trap) is recovered to 0.005 rad;
* the carrier trap itself: the brightest Fourier bin of the object hologram is a harmonic, while the reference
  hologram gives the carrier;
* a phase ramp of 6π is unwrapped without residues;
* the measured phase noise is within 15 % of √2/(μ√N);
* reference normalisation removes the injected reference distortion, and without it the residual is that
  distortion;
* the wrong sideband inverts the phase;
* biprism overlap and Fresnel edges behave as expected;
* seeds are deterministic;
* pixel-centre resampling registers with binning, including on grid sizes such as 400, 405 and 384 (the
  independent audit found wrong Fourier bins there);
* signed step heights, the branch and the no-step control;
* forbidden and non-specular reflections are refused;
* the specular spot at 2 sin θ_ext/λ;
* the step relation refused for a bulk-Bragg spot;
* a phase reference region outside the biprism overlap refused;
* strict parameters (a typo is refused);
* outputs refuse raw/ (and gemicro's declared raw roots) and NaN, and a failed run leaves nothing behind.

The tests also run the full CLI chain with the shipped parameter files and both controls. The abTEM test runs
the generator and forward model on the CPU, checks the vacuum amplitude and the sign of the phase, and checks
that a tilt series is selected by value (a missing tilt is an error, never index 0).

## 6. Assumptions and limits

* **The reflection geometry is not validated.** `slab_reflection.yaml`, `tilt_series.yaml` and
  `process_all_tilts.yaml` run the (4,-4,4) tilt series on the legacy CFG-A cell (θx from -12 to -16 mrad, through
  the 13.64 mrad refraction-shifted peak). This exercises the code path only.
  * The dark-field aperture is on the beam reflected into vacuum (`spot.mode: specular`, q = 2 sin θ_ext/λ along the
    surface normal: 1.088 1/Å at 13.64 mrad). That equals the (4,-4,4) g_x = 1.276 1/Å only at the 16.00 mrad vacuum
    Bragg angle. The measured spot centroids agree with this position, and `step_height_reflection_formula.py`
    takes θ_ext from the selected spot.
  * In this cell only 1e-4 to 1e-2 of the intensity reaches that spot. Of 20 terrace steps (5 tilts × 4 steps),
    19 are reported as "no step detected" (σ = 1-5 rad), and one crossed the 3σ threshold with a wrong value. So
    nothing from this cell is a reflection result.
  * The audit's milestone M2 (absorbing reflection cell with confined illumination, validated against a dynamical
    solver) is needed before any reflection phase is compared with experiment.
  * abTEM's propagator-shear tilt is recommended below about 17 mrad; the sweep stays below.
* The exit wave is in abTEM's incident-beam frame (the direct beam at q = 0, a bulk Bragg beam at q = g_xy, the
  beam reflected into vacuum at q = 2 sin θ_ext/λ n̂) and on the exit face of the potential box; thinner columns
  include vacuum propagation to that plane.
* The validation's residual criterion uses a local shot-noise prediction
  σ² = σ_obj²(a_o²|ψ|² + a_r²)/|ψ|² + σ_ref², with |ψ| from the band-limited truth wave. The detector MTF and pixel
  integration across the sideband are not in T_holo (about 0.002 rad).
* Hologram model: intensities are averaged over phonon configurations after squaring; the reference branch is
  common to all configurations; the MTF is applied to the expected intensity, then Poisson noise (white noise);
  aberrations are relative to the selected spot (centred dark field). The degree of coherence (0.40), MTF
  (Gaussian 0.4 px; the Merlin MTF is OPEN), drift, dose and R3 distortion are ASSUMPTIONs or PROJECT_INPUTs, listed
  in `docs/model_assumptions.md` section 5. Reference model R2 (self-reference from a flat region) is not
  implemented.
* Frozen phonons: `num_configs` > 0 runs one static multislice per configuration with seeded Gaussian
  displacements (σ per axis); the first test uses the static lattice.
* HoloSpy 0.3, checked against its source and by test:
  * `reconstruct()` takes the sideband at -sb_position, so its default `sb="lower"` returns -φ with this
    pipeline's carrier convention. The wrapper passes the conjugate index, so both engines select the same
    sideband.
  * `statistics()` swaps the axes on non-square images and assumes square pixels, so it is evaluated on a
    centred square crop. Its "Fringe contrast" is std/mean = μ/√2, not the visibility μ.

  Both are worth an upstream issue.
* Requests for ElectroSim: none essential. pytest is not in the environment list, so the suite has its own runner;
  adding pytest to `em-holography` would be convenient. The first GPU run will establish the GPU timing.
