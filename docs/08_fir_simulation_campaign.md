# M2 reflection-multislice campaign for the Fir cluster

Status: 2026-10-14, version 0.1 (code, configuration and local CPU validation complete; GPU stages
NOT RUN). Conventions: `docs/physics_conventions.md`. Evidence labels follow the instruction file.
Derivations behind every formula of the code are in appendix A. How to run it:
`fir/README.md`.

## 1. What the campaign computes and why it needs Fir

Milestone M2 of `docs/05_final_repository_specification.md` is a validated reflection forward model.
This campaign builds and runs it for the two named configurations and answers questions that no
smaller calculation can:

1. **Complex specular rocking curves.** Amplitude and phase of the reflection coefficient
   r(theta) from 7 to 45 mrad at 200 keV are computed for Si(1,-1,1) with a [110] beam (CFG-A)
   and for Si(001) with [110] and [100] beams (CFG-B, both azimuths because PROJECT_INPUT item 8
   is open). The lattice is static, Debye-Waller smeared, and frozen-phonon averaged. These give
   the peak positions that calibrate the angle scale and the mean inner potential, and they give
   the reflected intensity available for holography at each condition.
2. **Terrace-ratio step phases.** The ratio r(level L)/r(level 0) for flat terraces gives the
   step phase including its dynamical residual. The residual is exactly zero for translation
   steps (Si(111) bilayer, Si(001) double layer) and for the Si(001) single-layer step at the
   [100] azimuth by symmetry. Both are null tests of the whole numerical chain. For the Si(001)
   single-layer step at the [110] azimuth the residual is the dynamical phase difference between
   screw-related terraces, which is open question 3 of `docs/model_assumptions.md`.
3. **Explicit step images.** The dark-field image wave on the surface plane is computed for
   steps parallel to the beam (two terraces side by side over a 200 A cell) and transverse to
   it (up and down steps, with shadowing), and for a 10 nm mesa edge. These give the near-riser
   dynamical residual, the shadow lengths and the phase maps that the hologram chain (M3) will
   take as its object wave.
4. **RHEED patterns and diffuse fraction.** Rod intensities and the thermal diffuse fraction in
   the specular channel versus angle.

The cost comes from the physics. With an inelastic mean free path of order 100 nm, the reflected
wave keeps emerging for about 2 um downstream of where the beam lands (appendix A4). The cell must
therefore be 2.5 to 10 um long: 13,000 to 96,000 atomic planes on grids sampled at 0.08 A, with
5376 or more points across the normal. Frozen-phonon ensembles and 200 A wide step cells
multiply that. The planned campaign is 2,967 tasks of up to 17.4 GB each.

## 2. Model and inputs

Every physical input carries value, label and source in `configs/fir_m2_campaign.yaml`; the runner
refuses a task in which any is missing. The assumptions are tabulated in
`docs/model_assumptions.md` section 2b (C1 to C8).

| Input | Value | Label |
|---|---|---|
| Beam energy | 200 keV (lambda = 0.0250793 A, sigma = 7.2884e-4 rad/(V A)) | PROJECT_INPUT (item 1, supplied) |
| Lattice parameter | 5.4309 A | ASSUMPTION B2 |
| Atomic scattering factors | Kirkland (free Si atoms); Lobato as a scan; mean inner potential 13.90 V and 13.95 V | SECTION_READ of the abTEM 1.0.10 data files; primary sources UNVERIFIED |
| Inelastic absorption | uniform imaginary potential 0.5 V inside the crystal (mean free path 137 nm), tanh onset 0.5 A wide at the mid-gap plane; scanned 0.25 and 1.0 V, onset 0.25 and 1.0 A | ASSUMPTION C3 (placeholder for PROJECT_INPUT 21) |
| Thermal vibration | Einstein model, u_rms = 0.076 A per axis (B = 0.456 A^2) | ASSUMPTION C4 (value from A7) |
| Surface termination | bulk-terminated, unreconstructed | ASSUMPTION C5 |
| Absorption proportional to the atomic potential | none | ASSUMPTION |

The model's refraction is set by the parametrisation's mean inner potential (13.90 V), not by the
12.0 V working value of ASSUMPTION B1. Peak positions from the campaign must be compared with the
refraction formula at 13.90 V; the difference to experiment then measures the bonding contribution
plus calibration errors (comparison protocol, docs/05 section 7 step 1).

## 3. Numerical method and its local validation
### 3.1 Method in brief

* **Frame and slicing.** x is the outward normal, y in-plane transverse, z the beam azimuth.
  Every atomic plane perpendicular to the beam is one slice: 1.920 A for a [110] beam,
  1.358 A for [100]. Each atom's full projected potential sits on its plane. Planes are
  linked by the exact propagator `exp(i (kz - k) dz)` in a symmetric splitting (appendix A1).
* **Potentials.** For each plane the structure factor is a matrix product `Ex @ Ey` of exact
  phase factors, with arguments reduced modulo 1 in float64. It is multiplied by
  `2 pi a0 e f_e(q)` and kept only inside the 2/3 anti-aliasing band. Transmission functions
  are band-limited again after exponentiation. Static planes are cached; frozen-phonon planes
  are rebuilt for every configuration on the GPU.
* **Semi-infinite crystal.** Atoms continue into a 100 A bulk-side absorber. A 60 A absorber
  sits at the top of the vacuum. Both are cubic imaginary ramps up to 40 V, so nothing crosses
  the periodic boundary. Inelastic absorption W_in acts inside the crystal and follows the
  local terrace.
* **Illumination.** A coherent Gaussian sheet beam, uniform along y, enters at z = 0 entirely
  above the structure, with 4.5 widths plus 5 A of clearance. Its waist lies on the surface
  plane. A 10 A waist covers ±2.1 mrad of angle; four such beams share one march.
* **Measurement: the virtual detector.** The wave is recorded at every plane on two lines
  0.16 A apart, placed above the top of the incident beam. Only reflected waves cross them,
  plus any down-going contamination, which the two-line decomposition rejects. The
  z-Fourier transform of the record gives the reflection coefficient at any angle inside
  the beam, r(theta), referred to the outermost atomic plane. It also gives the up-going
  spectrum over (kappa, qy), which yields the RHEED pattern and the image wave
  (appendix A3, A11).
* **Cell length.** Each beam is marched at least to its planned length: footprint, plus the
  absorption delay `7/(sigma W)`, plus the rise to the detector. It then stops when its
  detector record has fallen below 1e-4 of its peak over the last 400 planes, with a cap at
  2.5 times the planned length. The adaptive part is needed because surface resonances decay
  far more slowly than the bulk absorption predicts (section 3.3).
* **Precision.** complex128 throughout. A complex64 run is an informational variant in the
  convergence stage.

### 3.2 Local validation: rungs 1 and 2 (refraction and the laterally averaged crystal)

All numbers in sections 3.2 and 3.3 come from the CPU smoke configuration
(`configs/smoke_cpu.yaml`): 0.1 A sampling, a 230 A cell, W_in = 2 V to shorten the cells, and
6 A beam waists. They test the method and the code at reduced size; the same checks run at
production sampling in the Fir `validation` stage. Commands:
`python -m reflection_holo.campaign plan --config configs/smoke_cpu.yaml --stage all --out RUN`,
then `python -m reflection_holo.worker run ...` and `python -m reflection_holo.aggregate ...`.

**Rung 1, Fermi potential step against Parratt.** The step is
`V = 13.9 V/(1 + exp(x/0.2 A))`; the comparison is with the Parratt recursion in the
multislice's own stationary dispersion.

| Angle | W_in | max \|dr\| | max relative | max phase error |
|---|---|---|---|---|
| 13 mrad | 0 | 2.2e-6 | 1.9e-4 | 1.8e-4 rad |
| 13 mrad | 2 V | 2.0e-6 | 1.7e-4 | 1.6e-4 rad |
| 25 mrad | 0 | 1.6e-7 | 1.5e-3 | 1.0e-3 rad |
| 25 mrad | 2 V | 1.5e-7 | 1.5e-3 | 9.5e-4 rad |

At 25 mrad |r| is only 1e-4, so the relative errors there reflect an absolute accuracy of 2e-7.
Earlier runs with the same kernel gave three further checks:
- The squared reflectivity at 15 mrad, 2.3593e-5, matches the closed-form Fermi-step value of
  2.3597e-5 (appendix A2).
- At 45 mrad the reflection fails at 0.0977 A sampling and matches the closed form to
  0.2 percent at 0.049 A, as the band limit predicts (appendix A8).
- Halving and quartering the 1.92 A slice thickness changed the agreement by less than 3e-5
  relative (5.4e-4, 5.1e-4, 5.1e-4 at 15 mrad).

The Schroedinger and multislice stationary models differ by up to 3e-4 relative here
(appendix A1).

**Rung 2, laterally averaged crystal against Parratt.** The y and z average of the atomic
potential of each surface, a one-dimensional periodic crystal with W_in = 2 V, is marched by the
multislice and compared with Parratt on the same band-limited profile, layered at dx/16.

| Surface | Window | max \|dr\| | max relative | max phase error (\|r\| >= 1e-2) |
|---|---|---|---|---|
| Si(111), Bragg (4,-4,4) | 13.3 mrad | 4.7e-5 | 3.4e-4 | 2.0e-4 rad |
| Si(111), between orders | 20.0 mrad | 4.7e-5 | 4.8e-3 (at \|r\| = 1.8e-3) | 6.9e-4 rad |
| Si(001) [100], (008) | 16.2 mrad | 3.6e-5 | 3.6e-4 | 9.6e-5 rad |
| Si(001) [110], (008) | 16.2 mrad | 4.6e-5 | 3.6e-4 | 1.8e-4 rad |

The absolute floor of about 4e-5 is shared by the reference and the multislice. Refining the
reference layering from dx/8 to dx/32 lowered it from 9.4e-5 to 3.8e-5. The rest is the coarse
smoke sampling. The rung 2 phase is checked where |r| >= 1e-2 (configs/benchmarks.yaml). At
|r| = 1.8e-3 the 4e-5 floor alone gives 4.8e-3 rad.

### 3.3 Local validation: rung 3, beam independence, surface resonances

**Null tests.** Flat terraces at levels 0 and 1 were run with identical beams. The residual
`arg(r_1/r_0) + 2 K_ext h` and the amplitude ratio were evaluated over every angle with
|r| >= 0.01 inside the beam windows (13.3 and 20.0 mrad for Si(111); 16.2 mrad for Si(001)):

| Terraces | Relation | Points | max \|residual\| | max \|amplitude ratio - 1\| |
|---|---|---|---|---|
| Si(111) bilayer, h = 3.1355 A | lattice translation | 451 | 1.3e-3 rad | 9.6e-4 |
| Si(001) single layer, h = 1.358 A, [100] beam | screw + mirror symmetry | 215 | 1.6e-3 rad | 1.9e-3 |
| Si(001) single layer, h = 1.358 A, [110] beam | screw, no symmetry | 231 | up to pi | up to 5 |

The first two vanish to within 2e-3, as translation covariance and the mirror argument require
(appendix A6). That covers the potential, the truncation, the propagation and the extraction
together. The third is not a null test. At the [110] azimuth the two terraces of a single-layer
step reflect very differently at some angles. This is the dynamical residual of open question 3,
here only at smoke numerics and for bulk-terminated surfaces; the production `rocking` stage
computes it properly.

**Beam independence.** The same Si(111) terrace was illuminated by waists of 6 and 8 A, with
different detector heights and cell lengths. Over the shared angles the reflection coefficients
agree to about 1e-5 and 1e-4 rad. The exception is a narrow surface resonance at 14.9 to
15.0 mrad, where the difference reaches 7.7e-4 and 0.027 rad. There it stays within the stated
truncation uncertainty: the excess beyond it is 1.1e-5 and 5e-5 rad.

Two defects were found and fixed on the way:
- An angle grid anchored at each window's own edge made the two waists sample angles offset by
  a fraction of the 0.02 mrad step. Near a Bragg peak that produced an apparent 0.014 rad
  difference. All windows now share an absolute grid.
- A fixed cell length cut the resonance tail: lengthening the cell changed the phase at the
  resonance by 0.024 rad and nowhere else beyond 1e-4. The march now stops adaptively, and the
  remaining uncertainty is estimated and carried through every comparison (appendix A12).

### 3.4 Absorbers

The first smoke validation (quadratic 50 A and 25 A ramps, 8 V) left an absolute error floor of
3.6e-5 in r. It was attributed by single-parameter variations, each at 25 mrad on the Fermi step
with W_in = 2 V:

| Variation | max \|r - r_Parratt\| |
|---|---|
| base | 3.6e-5 |
| longer cell, extra 8000 A | 3.6e-5 |
| detector 10 A higher | 3.6e-5 |
| half the slice thickness | 3.6e-5 |
| sampling 0.08 A instead of 0.1 A | 3.6e-5 |
| absorbers 60/40 A at 40 V | 3.0e-7 |

The cause was a transmitted wave crossing the bulk-side absorber. It wrapped through the periodic
boundary and came down across the detector line. The production absorbers were then designed
with the Parratt recursion, entering each ramp from vacuum at 3 to 48 mrad:

| Ramp | Max reflection | Reflection at 20 mrad | One-way attenuation exponent at 45 mrad |
|---|---|---|---|
| quadratic, 25 A, 8 V (first smoke) | 7.4e-4 | 1.6e-6 | 1.1 |
| quadratic, 100 A, 8 V (first draft) | 4.6e-5 | 5.8e-8 | 4.3 |
| cubic, 60 A, 40 V (production top) | 1.7e-5 | 4.0e-9 | 9.7 |
| cubic, 100 A, 40 V (production bottom) | 3.7e-6 | 8.7e-10 | 16.2 |

The maximum reflection occurs at the lowest angle tested, 3.8 mrad. Production uses the cubic
ramps: attenuation of exp(-25.9) for a wave that wraps from the bulk side to the top at 45 mrad,
more at smaller angles. The two-line detector rejects any down-going remainder.

### 3.5 abTEM cross-check in transmission

`validation/abtem_crosscheck.py` runs the same Si slab through both codes and compares the exit
waves. The slab is 28.2 x 26.6 x 38.4 A with 1440 atoms and the beam along [110]. Both runs use
Kirkland potentials, 1.92 A slices, a 2/3 antialias cutoff without taper and the Fresnel
propagator, with abTEM 1.0.10 in float64. Differences are relative L2 norms within
|q| <= 1 A^-1, after removing the best global phase.

| Case | 288 x 256 grid (0.098 A) | 576 x 512 grid (0.049 A) |
|---|---|---|
| normal incidence | 8.0e-3 (global phase 1.4e-3 rad) | 2.0e-3 (3.6e-4 rad) |
| 24 mrad: explicit Fourier component vs abTEM shear tilt | 5.4e-3 | 1.3e-3 |
| 48 mrad: explicit Fourier component vs abTEM shear tilt | 3.7e-3 | 1.1e-3 |

The difference falls about four-fold when the sampling is halved. That is the signature of two
correct discretisations converging, not of a normalisation error. abTEM places atoms as sub-pixel
deltas corrected by a sinc; this code uses exact structure-factor phases. The tilt rows answer
the question left open in docs/05 section 11: abTEM's propagator-shear tilt agrees with an
explicit tilted beam at 48 mrad to 1e-3 over this 38 A slab. The long reflection cells are a
different regime and are not covered by this comparison.

### 3.6 Steps parallel to the beam (CPU test)

A Si(111) bilayer step was run in a 53 A cell, eight surface periods with two 26.6 A terraces,
at 13.3 mrad. A no-step control with both strips at level 0, and flat references of levels 0
and 1 sharing the beam, ran alongside it. All used smoke numerics with a 6 A waist.

| Check | Result |
|---|---|
| Exact angle-resolved response, averaged over y, against the flat terrace's own r | 5e-8 relative |
| No-step control: terrace strips against the flat terrace | 3.0e-4 |
| Bilayer step: strips against the flat terraces | 4e-2 to 6e-2 |
| Bilayer step: residual `arg(r_1/r_0) + 2 K h` | up to 1 rad (median 0.19 rad) |
| Flat references: residual of the same quantity | 1.9e-3 rad |

The control's 3.0e-4 comes from the different y-sampling of the 8-period and 1-period cells at
0.1 A. It was 2.5e-3 before strip averages were made exact in qy space. With terraces this
narrow, about 13 A from the nearest riser, the step array acts as a lateral grating, and the
strips are not yet infinite terraces. Production uses 100 A terraces. The steps stage adds a
terrace-width series (cells of 100, 200 and 400 A) and a no-step control, so the far-from-riser
step phase can be shown to converge.

### 3.7 Unit tests and what was not run

`python -m pytest -q -m "not slow"` passes 49 tests in under a second:
- geometry against the reference calculator (T1 to T14 values);
- crystal cells, terminations, and the translation and screw relations of the steps;
- potential normalisation against the analytic projection;
- propagation identities, including the adaptive stop;
- the Parratt recursion against the transfer matrix, flux conservation and the closed form;
- an import test of every module.

`python -m pytest -m slow` runs the reduced validation ladder (rungs 1 to 3) in about 30 minutes
on four cores.

The CPU run of the explicit-step stage first exposed the beam-smearing problem in real-space
step images (section 5). That led to the angle-resolved analysis of appendix A13. The parallel
step was then rerun with a 53 A cell, a no-step control and its flat references (section 3.7).

NOT RUN:
- any GPU execution;
- the production numerics;
- the convergence and rocking stages beyond pipeline checks;
- an independent many-beam reflection code (docs/05 section 4.4);
- the hologram chain (milestone M3).

## 4. Campaign stages on Fir

One stage is one job on one Fir GPU node: 4 H100 SXM5 80 GB, 48 cores, 1 TB. Four workers, one
per GPU, take tasks longest-first from the stage's task list. The chain is
selftest, then validation, then convergence, then rocking, then steps. A stage starts only if the
previous one succeeded. Validation and convergence fail their job unless their verdicts pass, so
no production result exists without a passing validation.

| Stage | Tasks | Content | Gate (configs/benchmarks.yaml) |
|---|---|---|---|
| selftest | 1 GPU | CPU unit tests; numpy versus CuPy on a static and a frozen-phonon task (agreement 1e-9); throughput benchmark; abTEM cross-check if abTEM is installed | CPU and GPU agree |
| validation | 36 | rung 1: Fermi step, 2 widths x 2 absorptions x 5 angles; rung 2: laterally averaged crystal of each surface at 2 absorptions; rung 3: terrace ratios of every level of the three surfaces; beam independence (waists 8, 10, 14 A) | every rung within tolerance |
| convergence | 172 | Si(111) level 0 at 13.3, 20.0, 30.6 mrad: sampling (dx 0.0996, 0.080, 0.0664 A at fixed cell height); complex64; Fresnel propagator; delay 5/7/9 decay lengths; adaptive tail tolerance 1e-6; absorber width and strength; frozen-phonon cell 1, 2, 4, 8, 16 periods x 32 configurations | refinements agree with production numerics |
| rocking | 1892 | 7 terraces x 16 windows (7.0 to 44.5 mrad, 4 windows per task): static; 64 frozen-phonon configurations in a 54 A cell; for level 0 also Debye-Waller, W_in 0.25 and 1.0 V, onset 0.25 and 1.0 A, Lobato parametrisation | none |
| steps | 867 | see below | none |

The steps stage runs the following:
- **Steps parallel to the beam, in a 200 A cell.** Static runs every 1 mrad from 9 to 32 mrad
  for the Si(111) bilayer, the Si(001) single and double layers at [110], and the Si(001) single
  layer at [100]. Each run uses a 15 A waist and comes with flat references sharing its beam.
  Frozen phonons, 32 configurations, run at every Bragg condition. A no-step control is included.
- **Terrace-width series.** The Si(111) bilayer at 13.3, 20.0 and 26.5 mrad in 100 and 400 A
  cells, and the Si(001) single layer at [110] at 16.2 and 21.0 mrad in a 400 A cell, beside the
  200 A production cell. The step phase far from the riser must converge with terrace width.
- **Steps across the beam.** Up and down steps at every Bragg condition with a 60 A waist. The
  Si(111) bilayer is also run at 30 and 120 A waists to measure the dependence on illumination.
- **10 nm mesa edge.** 74 x a/4, up and down, at 16.2 and 26.3 mrad.

Cell heights for the cross-beam steps are chosen automatically to hold each beam.

**Cost.** Before submission the planner checks every task geometrically: angle windows inside
the band, detector lines below the top absorber, and memory. It estimates the work as grid
points times planes, plus the structure-factor GEMM for frozen phonons. With an assumed H100
throughput of 5e9 point-planes per second and 3e12 complex multiply-adds per second:

| Quantity | Value |
|---|---|
| Tasks | 2,967 |
| GPU-hours at the planned cell lengths | 80.9 |
| Wall time on one 4 x H100 node | about 20 h |
| Largest task memory | 17.4 GB |

The self-test replaces the assumed throughput with a measured one and writes
`cost_estimate.txt`. The adaptive stop (tail 1e-5, cap 4x) lengthens runs that see slow surface
resonances. Each stage job therefore requests 24 h and resubmits itself up to 8 times; a
resubmission moves the next stage's dependency to the new job.

## 5. Outputs and how they answer the questions

`summary/<stage>/summary.json` holds every number and verdict; `arrays.npz` the curves and maps;
PNG figures where matplotlib is available. Every `results/<stage>/<task>.h5` file stores the
task (with evidence labels), the result, and a manifest: git commit, package versions, GPU,
seeds, precision and input checksums.

* `rocking`: stitched complex r(theta) per surface, terrace and mode, with overlap consistency
  between neighbouring windows; frozen-phonon coherent average `<r>` with its standard error and
  the diffuse fraction; local maxima of |r| next to the Bragg conditions of the rod computed at
  13.90 V and at 12.0 V; terrace-ratio residuals `arg(r_L/r_0) + 2 K h L` for every step type;
  RHEED rod intensities per window.
* `steps`, steps parallel to the beam: the exact plane-wave profile r(y; theta) across the
  steps for every angle (appendix A13). From it come:
  - the step phase and its dynamical residual `arg(r_1/r_0) + 2 K h` versus angle;
  - the null test of each terrace against its flat reference;
  - the step-induced envelope near the risers, with the profile low-passed below the first
    surface rod.

  The 1 mrad scan gives the step phase as a continuous function of angle from 9 to 32 mrad.
  That is the rocking series that resolves the 2 pi branch (docs/03 section 4).
* `steps`, steps across the beam: image waves through objective apertures of 1, 2 and 4 mrad.
  The aperture is PROJECT_INPUT 4 and is scanned here. Each side of the edge is divided by the
  flat-terrace image of its own level under the same beam. What remains is the riser's
  influence (its extent up- and downstream is reported) and the shadow, against the geometric
  `h/tan(theta)`. These images depend on the illumination; a bilayer's step phase moves by
  1.57 rad per mrad of angle, so the waist scan quantifies that dependence.

The acceptance criteria of docs/05 section 0 that this campaign addresses are items 2 (validation
ladder and rocking curves) and 3 (monatomic-step benchmark with a dynamical residual below the
proposed 0.1 rad). Item 1 (the full observable chain to reconstructed holograms) needs milestone
M3.

## 6. Limitations

* The GPU stages have not been run. All numbers in section 3 come from CPU runs at reduced size
  (0.1 A sampling, strong absorption, short cells). They validate the method, not the production
  results.
* No dynamical RHEED reference has been run (sim-trhepd-rheed or a Bloch-wave Bragg solver,
  docs/05 section 4.4). Rung 2 tests the specular-rod physics only for the laterally averaged
  potential. The full 3D rocking curves are validated only by the null tests and beam
  independence. They are not validated against an independent many-beam reflection code.
* The inelastic absorption (C3) and the vibration amplitude (C4) are assumptions. Reflectivities
  and resonance widths depend on them; the scans quantify how much. Step phases between
  translation-related terraces do not depend on them.
* Bulk-terminated surfaces only (C5). Reconstructions, oxide and damage layers (ASSUMPTION B7,
  PROJECT_INPUT 12) are not modelled.
* The image wave is ideal: point-by-point focus, no aberrations, no partial coherence, no
  reference wave, no detector. Hologram formation and reconstruction are milestone M3.
  Real-space images of steps across the beam depend on the coherent illumination. The
  angle-resolved results for steps parallel to the beam do not.
* Fir-specific details could not be verified from here: the Slurm GPU type string, the module
  versions and the wheelhouse contents. `fir/README.md` section 0 lists what to check.

## Appendix A. Derivations used by the code (all DERIVED_HERE)

Conventions of `docs/physics_conventions.md`: `exp(+i(k.r - wt))`, x = outward normal,
z = beam azimuth, glancing angles, `q` in cycles/A, `K = 2 pi q` in rad/A,
`kappa(q) = kz(q) - k` with `kz = 2 pi sqrt(1/lambda^2 - q^2)`.

**A1. Stationary dispersion of the multislice and refraction.** Per unit length along z
the split-step scheme (exact propagator, transmission `exp(i sigma V)`) advances a plane
wave `exp(i K x)` in a region of constant potential `V` by `sqrt(k^2 - K^2) - k + sigma V`
in the limit `dz -> 0`. A stationary solution has one value of this quantity everywhere
across a potential step that depends only on x. Hence
`K_int^2 = k^2 - (kz - sigma V)^2`. The relativistically corrected Schroedinger equation
gives `K_int^2 = K^2 + 2 k sigma V` to first order in `V/(T + m c^2)`. The two differ by
`(k - kz)/k ~ theta^2/2` and `sigma V/(2k) ~ 2e-5`, so refraction by the mean inner
potential is reproduced. `reference1d.py` implements both forms and the validation
reports their difference.

**A2. Parratt recursion.** In layer j, `phi = A_j exp(-i K_j (x - x_j)) + B_j exp(+i K_j (x - x_j))`,
with `x_j` the bottom of the layer. Continuity of `phi` and `phi'` at the boundary between
layers j and j+1, with `Y = X_{j+1} exp(2 i K_{j+1} d_{j+1})` the up/down ratio at the top
of layer j+1, gives
`X_j = (r_j + Y)/(1 + r_j Y)` with `r_j = (K_j - K_{j+1})/(K_j + K_{j+1})`. The
semi-infinite bottom layer has `X_N = 0` (`Im K_N > 0`). Referred to a plane `x_ref`,
`r = X_0 exp(2 i K_0 (x_ref - x_top))`. Tests: agreement with an independent 2x2 transfer
matrix to 1e-10, flux conservation without absorption, the single-interface Fresnel
coefficient, and the closed-form Fermi-step reflectivity recalled from Landau and
Lifshitz section 25 (UNVERIFIED as a citation; used only as a cross-check).

**A3. Reflection coefficient from the virtual detector.** Above the surface, in vacuum,
`psi(x, z) = int dq [B(q) e^{2 pi i q x} + D(q) e^{-2 pi i q x}] e^{i kappa(q) z}` (q > 0;
B up-going, D down-going). The record on the line `x = x_j` is `f_j(z) = psi(x_j, z)`. It
vanishes at both ends of the cell: the incident beam starts below the line, and every
reflected contribution has crossed the line and been absorbed by the end. Hence
`F_j(kappa) = int f_j e^{-i kappa z} dz = (2 pi / |kappa'(q)|) [B e^{i phi_j} + D e^{-i phi_j}]`
with `phi_j = 2 pi q x_j` and `|kappa'| = (2 pi)^2 q / kz`. With
`G_j = F_j 2 pi q / kz`, two lines give
`B = (G_2 e^{i phi_2} - G_1 e^{i phi_1})/(e^{2 i phi_2} - e^{2 i phi_1})`, and D similarly.
The denominator has modulus `2|sin(2 pi q (x_2 - x_1))|`. The line spacing (0.16 A) keeps
`2 pi q (x_2 - x_1) < pi` up to 60 mrad. The incident wave has spectral density
`A(q) = L_x a(q)`, where a(q) is its grid coefficient, known analytically. The reflection
coefficient referred to `x_ref` is `r(q) = B(q)/A(-q) exp(4 pi i q x_ref)`. The z integral
is evaluated as a Riemann sum over the uniformly spaced planes, which is spectrally
accurate because f is band-limited and vanishes at both ends. The same decomposition,
per `(kappa, qy)` with `K_x = sqrt(k^2 - (k + kappa)^2 - (2 pi qy)^2)`, gives the
up-going 2D spectrum used for the RHEED pattern and for the images (A8).

**A4. Delay allowance.** A contribution reflected at normal depth D re-emerges
`2 D / tan(theta_int)` downstream. It is weighted by `exp(-2 D Im K_int)`, where
`Im K_int = k sigma W / K_int` for a uniform imaginary potential W. Setting the weight
to `e^{-n}` gives a delay of `n/(sigma W)`, independent of the angle:
1.92 um (19 200 A) for n = 7 and W = 0.5 V at 200 keV (`sigma = 7.288e-4 rad/(V A)`). The cell must
extend that far beyond the far end of the illuminated footprint. Without inelastic
absorption (W = 0) the reflected wave of a non-absorbing crystal never completes inside
a finite cell. Static non-absorbing runs are therefore flagged as not stationary and are
used only where the reflection is prompt.

**A5. Absorbers.** A wave crossing an imaginary potential W(x) at glancing angle theta
is attenuated in amplitude by `exp(-sigma int W dx / sin(theta))`. The cubic ramps
(`W = W_max s^3`) used here have continuous value, slope and curvature at their inner
edge, so their own reflection is small. It was computed with the Parratt recursion for
angles of 3 to 48 mrad (section 3.4).

**A6. Null tests.** If the upper terrace is the lower one translated by a lattice
vector R with `R.n = h`, the scattering problem is covariant. The specular coefficient
referred to a fixed plane obeys `r_up = r_low exp(-2 i K_ext h)` with
`K_ext = k sin(theta_ext)`. This is exact in dynamical theory, so
`arg(r_L/r_0) + 2 K_ext h L = 0` and `|r_L/r_0| = 1` test the whole numerical chain. This
covers the Si(111) bilayer step and the Si(001) double-layer step. For a Si(001)
single-layer step the terraces are related by the diamond 4_1 screw: a 90 degree rotation
about [001] plus a/4. Terrace L+1 with the beam along d behaves like terrace L with the
beam along the rotated direction. For d = [100] the rotated direction is [010] or
[0,-1,0]. A {110} mirror of the bulk-terminated crystal maps it back to [100], so the
residual must vanish: a symmetry null test. For d = [110] the rotated direction is
[1,-1,0], which no symmetry of the terrace maps onto [110]. The residual there is
physics: the dynamical difference between the two terraces of an a/4 step (open
question 3 of `docs/model_assumptions.md`).

**A7. Mean inner potential of a parametrisation.** Integrating
`V(r) = 2 pi a0 e int f_e(q) e^{2 pi i q.r} d^3q` over all space gives
`2 pi a0 e f_e(0)` per atom. Hence `V0 = 2 pi a0 e f_e(0) n` with n = 8/a^3. For the
Kirkland and Lobato Si parameters: 13.90 and 13.95 V. These are free-atom values; the
project's working value is 12.0 V (ASSUMPTION B1).

**A8. Band limit on reflection.** The specular reflection couples q_in = -q to q_out = +q
through the Fourier component 2q of the transmission function. That component is
discarded beyond the anti-aliasing band. A grid can therefore reflect only up to
`sin(theta_max) = q_band lambda/2`: 42.8 mrad at dx = 0.0977 A and 52.3 mrad at
dx = 0.08 A. This was demonstrated in rung 1 at 45 mrad (section 3.1). The planner
refuses windows beyond the limit.

**A9. Frozen phonons and holography.** The reference wave does not depend on the phonon
configuration. The configuration-averaged hologram
`<|u_o + u_r|^2> = <|u_o|^2> + |u_r|^2 + 2 Re(<u_o> u_r*)` therefore carries the
configuration-averaged object wave `<u_o>` in its sideband. The coherent average
`<r>` over frozen-phonon seeds is the quantity the hologram measures. Its attenuation
relative to the static r is the thermal diffuse absorption, which no tuned parameter
supplies. `<|r|^2> - |<r>|^2` is the diffuse intensity in the specular channel.

**A10. Inelastic absorption and mean free path.** A uniform imaginary potential W
attenuates the elastic intensity as `exp(-2 sigma W s)` along the path s. The intensity
mean free path is therefore `Lambda = 1/(2 sigma W)`: 137 nm for W = 0.5 V at 200 keV.

**A11. Image wave on the surface plane.** The up-going spectrum `U(kappa, qy)` (field
referred to x = 0) determines the reflected vacuum field everywhere above the surface.
The image wave at the surface plane, through an objective aperture centred on the
specular direction, is
`psi(x_ref, y, z_s) = sum U exp(i K_x x_ref + i kappa z_s + 2 pi i qy y) dkappa / 2 pi`
over the components inside the aperture. This is the ideal, aberration-free dark-field
image of the plane `x = x_ref`, focused point by point. Instrument transfer, the reference
wave and hologram formation are milestone M3 and are not applied here.

**A12. Truncation uncertainty of r (adaptive cell length).** A flat surface can host long-lived
surface resonances: waves trapped along the surface that leak into the specular channel slowly.
They decay far more slowly than the bulk absorption predicts, because they spend most of their
path outside the absorbing crystal. In the smoke validation, the amplitude e-folding length of
the record tail along the beam was 5,000 to 12,000 A at W_in = 2 V, depending on the run and on
the segment used to measure it, against 1/(sigma W) = 690 A for a wave inside the crystal. The march therefore
stops adaptively, when the detector record over the last 400 planes has fallen below 1e-4 of its
peak, or at 2.5 times the planned length. The part of the record that is never computed is
estimated by geometric continuation of the last segment of S planes (S = min(1000, n/4)), scaled
by `rho = rms(last segment)/rms(previous segment)` per segment:
`delta F(kappa) ~ F_last(kappa) rho/(1 - rho)`. It is converted to r units like the record
itself. The estimate is stored with every point as `r_truncation_bound`. All validation and
convergence comparisons subtract it before applying their tolerances. On the smoke validation it
is 6e-6 at a Bragg peak, 3e-5 typically and 1.3e-3 at the narrow resonance near 15 mrad, where
it covered the observed beam-to-beam difference of 6.7e-4. A 3000-plane segment underestimated
it, because the previous segment then reached back into the main reflected pulse.

**A13. Angle-resolved response of steps parallel to the beam.** If the structure does not vary
along the beam, the multislice is invariant under translation in z, and kappa is conserved. An
incident plane wave of angle theta (`kappa_theta`, `qy = 0`) excites only outgoing components
with the same kappa: the specular rod and every lateral component `qy` that the steps scatter
into. Incidence and reflection are linear, so for each qy column the detector records,
Fourier-transformed at exactly `kappa_theta`, give
`2 pi rho(qy) A(-q) |dq/dkappa| exp(i K_x(qy) x_j)`. Here `rho(qy)` is the plane-wave response,
A the incident spectral density, and `|dq/dkappa| = kz/((2 pi)^2 q)`, evaluated for the incident
component because the incident wave has qy = 0 only. After the two-line up/down separation
with `K_x(kappa_theta, qy) = sqrt(k^2 - kz^2 - (2 pi qy)^2)`:
`rho(theta, qy) = U(kappa_theta, qy) (2 pi q/kz) / A(-q)`.
The reflected field at the surface plane under unit plane-wave incidence is
`r(y; theta) = sum_qy rho(theta, qy) exp(2 pi i qy y)`. Its qy = 0 term is the specular r of
A3. Averaging r(y; theta) over a whole number of lateral periods inside a terrace gives that
terrace's reflection coefficient. A partial period would mix in the non-specular rods. Away
from the risers this must equal the flat terrace's r, a null test of every step run. The ratio
of the two terraces gives the step phase at every angle of the window, free of the beam's
angular spread. That spread smears a bilayer step phase by 2 k h cos(theta) = 1.57 rad per mrad
in any real-space image.
