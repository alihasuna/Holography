# D — Software provenance and semantics of the Prismatique/Prismatic HRTEM path

Prepared: 2026-09-21. Author: automated source audit for Ali (reflection-mode dark-field
electron holography of Si surfaces).

Scope: establish, from version-matched source code, what `prismatique` + `embeam` +
`pyprismatic` + `prismatic` actually compute in HRTEM mode, so that the interpretation of
`image_wavefunctions` in `si110-reflection-holography` can be checked. Written against the
project source policy (`ba72277e-si110_reflection_holography_agent_instructions.txt`),
sections 1.4 (evidence labels), 8 (software provenance), 9.5 (ensembles), 9.6 (HDF5 axes).

**Evidence labels used** (policy §1.4): `SECTION_READ` (the technical passage/code was
actually read, locator given), `REPRODUCED` (executed here, command + output recorded),
`DERIVED_HERE` (arithmetic from `SECTION_READ` facts), `METADATA_VERIFIED`, `UNVERIFIED`.

Nothing in `/home/user/Holography` was written or modified. The cloned repository under the
scratchpad was read only. No simulation was run (no `pyprismatic` binary is available here);
every claim about engine behaviour below is `SECTION_READ` of the C++/CUDA source, never an
executed simulation.

---

## 0. Artifacts obtained, and exact commands run

All work under
`/tmp/claude-0/-home-user-Holography/18767b2d-e54d-5b3c-9746-d58b7d31a320/scratchpad/`.

| # | Command | Result |
|---|---|---|
| 1 | `python3 -m pip index versions prismatique` | `0.0.4, 0.0.3, 0.0.2, 0.0.1` |
| 2 | `python3 -m pip index versions embeam` | `0.0.5, 0.0.4, 0.0.3, 0.0.2, 0.0.1` |
| 3 | `python3 -m pip index versions pyprismatic` | `1.1.16, 1.1.15, 1.1.14, 1.1.13, 1.1.12, 1.1.11, 1.1.1, 1.1.0` |
| 4 | `python3 -m pip download prismatique==0.0.1 --no-deps --no-binary :all: -d .` | `prismatique-0.0.1.tar.gz` (363 731 B) |
| 5 | `python3 -m pip download prismatique==0.0.1 --no-deps -d .` | `prismatique-0.0.1-py3-none-any.whl` (179 793 B) |
| 6 | `python3 -m pip download embeam==0.0.1 --no-deps -d .` | `embeam-0.0.1-py3-none-any.whl` (72 170 B) |
| 7 | `python3 -m pip download prismatique==0.0.4 --no-deps -d .` | `prismatique-0.0.4-py3-none-any.whl` (181 810 B) |
| 8 | `python3 -m pip download embeam==0.0.5 --no-deps -d .` | OK |
| 9 | PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`) | release dates, table in §1 |
| 10 | `git clone --depth 1 https://github.com/prism-em/prismatic.git prismatic-cpp` | HEAD `d155fb931abaa22d5d2442d2e1a28a6657ac74da`, 2026-01-30; `setup.py: version="1.2.0"` |
| 11 | `git clone --depth 1 https://github.com/abTEM/abTEM.git` | HEAD `e78cb7b29f6375098f6d9767585080dad537170d`, 2026-09-21; `abtem/_version.py: __version__ = "1.1.0"` |
| 12 | `git clone --depth 1 https://github.com/HamishGBrown/py_multislice.git` | HEAD `5e5e4d81c9e1caf600cfe6ab706f98a1e2f1f90f`, 2025-01-09 |
| 13 | `python3 -m venv venv_build/v001 && pip install prismatique==0.0.1 embeam==0.0.1` | success; **`pyprismatic` was NOT pulled in** (see §1.4) |
| 14 | `venv_build/v001/bin/python apitest/check_api.py` | §3 table; 1 FAIL (`absorbing_layers`) |
| 15 | `venv_build/v001/bin/python apitest/tilt_test.py` | §2c, §3 (tilt grid, 1309 tilts, IndexError case) |
| 16 | `venv_build/v001/bin/python apitest/schema_test.py` | §2b (exact dataset shape and axes) |
| 17 | `venv_build/v001/bin/python apitest/nan_test.py` | §2d/§3 (`tilt_weights = [nan]`) |

Scripts kept at `scratchpad/apitest/{check_api,tilt_test,schema_test,nan_test}.py`; the stub
`scratchpad/apitest/pyprismatic.py` only lets `import prismatique` succeed — its `go()` raises,
so no simulation was ever executed.

**NOT RUN / NOT ACCESSED.** The following were refused by this session's egress policy
(HTTP 403 at the proxy; per `/root/.ccr/README.md` these are organization policy denials and
were not retried or routed around): `prism-em.github.io`, `prism-em.com`,
`www.sciencedirect.com`, `www.osti.gov`, `link.springer.com`, `abtem.readthedocs.io`,
`www.researchgate.net`, `europepmc.org`, `pubmed.ncbi.nlm.nih.gov`, `ui.adsabs.harvard.edu`,
`www.semanticscholar.org`, `openalex.org`. Consequently **the Prismatic 2.0 paper (Micron 151,
103141) and the PRISM paper (Ophus 2017) full texts were not read here**, and the rendered
`prism-em.github.io/about-cite/` page was not read. Everything attributed to Prismatic below
comes from its own source tree (item 10), which is the version-matched primary source.

---

## 1. Versions and provenance

### 1.1 What exists on PyPI

`REPRODUCED` (commands 1–3, 9).

| Package | Versions | Upload dates (UTC) |
|---|---|---|
| `prismatique` | 0.0.1, 0.0.2, 0.0.3, 0.0.4 | 2025-03-13, 2025-10-27, 2026-01-19, 2026-01-19 |
| `embeam` | 0.0.1 … 0.0.5 | 2025-01-30, 2025-03-13, 2025-06-18, 2025-10-24, 2025-10-24 |
| `pyprismatic` | 1.1.0 … 1.1.16 | all **2017** (1.1.16: 2017-11-15) |

**`prismatique==0.0.1` and `embeam==0.0.1` both exist and were obtained** (sdist + wheel /
wheel). `prismatique` 0.0.1 `version.py` reports `__version__ = '0.0.1'`
(`src/prismatique-0.0.1-whl/prismatique/version.py:21`); `embeam` 0.0.1 likewise. `SECTION_READ`.

### 1.2 Declared requirements of the pinned versions

`SECTION_READ` — `src/prismatique-0.0.1-whl/prismatique-0.0.1.dist-info/METADATA` and
`src/prismatique-0.0.1/pyproject.toml:43-46`:

```
prismatique 0.0.1  Requires-Python >=3.8   Requires-Dist: embeam ; h5pywrappers
prismatique 0.0.4  Requires-Python >=3.9   Requires-Dist: embeam>=0.0.5 ; h5pywrappers ; hyperspy_gui_ipywidgets
embeam     0.0.1  Requires-Python >=3.8   Requires-Dist: empix ; hyperspy[all] ; pyFAI
```

Two provenance consequences:

* **`prismatique` never declares `pyprismatic` as a dependency.** `REPRODUCED` (command 13):
  a clean `pip install prismatique==0.0.1 embeam==0.0.1` completed without installing
  `pyprismatic`, yet `prismatique/hrtem/sim.py:54` does `import pyprismatic`. The engine
  therefore has to be built and installed out of band and is **completely unrecorded** by the
  repository's `requirements.txt`.
* **`prismatique==0.0.1` does not pin `embeam`.** Installing it today resolves `embeam` to
  0.0.5 unless pinned. The repository `requirements.txt` pins neither (it lists bare
  `prismatique` / `embeam`), so a fresh environment built from `requirements.txt` gets
  prismatique 0.0.4 + embeam 0.0.5, not the README's 0.0.1/0.0.1.

### 1.3 Does the pin matter? (checking the README's stated rationale)

The repository README §2 says the code "targets this exact release; later versions may break
the `prismatique.hrtem.*` schema".

`REPRODUCED`: `diff prismatique-0.0.1-whl/prismatique/hrtem/sim.py prismatique-0.0.4-whl/prismatique/hrtem/sim.py`
→ **0 differing lines**. A per-file diff of the whole package gives only:
`cbed.py` 5, `hrtem/image.py` 4, `hrtem/output.py` 4, `load.py` 48, `sample.py` 4,
`stem/__init__.py` 10, `thermal.py` 8, `tilt.py` 6, `version.py` 26 lines. `ctor_param_names`
blocks are **identical** in `sample.py`, `discretization.py`, `thermal.py`, `tilt.py`,
`aperture.py`, `hrtem/image.py`, `hrtem/output.py`, `hrtem/system.py`. Likewise
`embeam` 0.0.1 vs 0.0.5: `gun.ModelParams`, `lens.ModelParams` and
`stem.probe.ModelParams` `ctor_param_names` are identical, and `embeam.wavelength` is still
exported.

**Conclusion:** the HRTEM HDF5 schema and the constructor signatures the repository uses are
*unchanged* from 0.0.1 through 0.0.4/0.0.5. The README's stated reason for the pin is not
supported by the evidence. Pinning is still correct practice, but it should be done in
`requirements.txt` (it currently is not) and for the reason that *the engine build* is
unpinned, not that the wrapper schema drifts.

### 1.4 The engine actually executed

`SECTION_READ`. `pyprismatic` on PyPI is **1.1.x from 2017** and predates HRTEM mode entirely:
the HRTEM entry point `src/HRTEM_entry.cpp` and `Algorithm::HRTEM` exist only in the
Prismatic 2.x tree. The version that must be used is the one built from
`github.com/prism-em/prismatic` (`setup.py:152  version="1.2.0"`; HEAD here
`d155fb931abaa22d5d2442d2e1a28a6657ac74da`, 2026-01-30). The repository records **no**
Prismatic commit, build flags, or precision setting anywhere.

`SECTION_READ` — `prismatic-cpp/README.md`: *"Notice as of January 2026: Prismatic is no
longer actively maintained… For a recently updated and actively maintained TEM simulation
package, we especially recommend abTEM."* This is the upstream maintainers' own statement and
is directly relevant to §5.

### 1.5 Citation requirements of the Prismatic project

The rendered page `https://prism-em.github.io/about-cite/` was **blocked** (§0). The
equivalent statement is carried verbatim in every Prismatic source file
(`SECTION_READ`, e.g. `prismatic-cpp/src/HRTEM_entry.cpp:1-12`, identical header in 20 files
including `src/go.cpp`, `src/PRISM02_calcSMatrix.cpp`, `pyprismatic/__init__.py`):

```
// Prismatic is distributed under the GNU General Public License (GPL)
// If you use Prismatic, we kindly ask that you cite the following papers:
// 1. Ophus, C.: A fast image simulation algorithm for scanning
//    transmission electron microscopy. Advanced Structural and
//    Chemical Imaging 3(1), 13 (2017)
// 2. Pryor, Jr., A., Ophus, C., and Miao, J.: A Streaming Multi-GPU
//    Implementation of Image Simulation Algorithms for Scanning
//    Transmission Electron Microscopy. arXiv:1706.08563 (2017)
```

A web search result additionally reports the live page asks for Rangel DaCosta et al.,
*Prismatic 2.0* — consistent with the version actually used here, but that page itself was
**not read** (`METADATA_VERIFIED` only, from search snippets; label the DaCosta item
`METADATA_VERIFIED`, the two above `SECTION_READ`).

**Licensing note (`SECTION_READ`, `prismatic-cpp/LICENSE` + the per-file headers):** Prismatic
is **GPL**. `prismatique` is **GPLv3** (`prismatique-0.0.1.dist-info/METADATA`:
`Classifier: License :: OSI Approved :: GNU General Public License v3 (GPLv3)`). The
repository's own `LICENSE` is MIT. Distributing an MIT-licensed pipeline that imports GPLv3
`prismatique` needs a deliberate decision; that is a licence question, not a physics one, but
it belongs in the provenance record.

**Correct attribution for this pipeline** (policy §8: *distinguish PRISM (algorithm),
Prismatic (engine), pyprismatic (interface), Prismatique (wrapper)*): the HRTEM path executed
here is **not PRISM**. It is plain multislice run once per plane wave, re-using PRISM's
S-matrix *infrastructure* (`HRTEM_entry` → `PRISM02_calcSMatrix`, §2a). Ophus 2017 should be
cited for the S-matrix/plane-wave-basis machinery that the HRTEM path reuses, Rangel DaCosta
2021 for the HRTEM mode itself, Pryor 2017 if the GPU path is used, and `prismatique` as the
wrapper. Citing only the PRISM paper would misdescribe what was run.

---

## 2. HRTEM simulation semantics

### 2a. What `image_wavefunctions` actually contains — **the decisive result**

Follow the data backwards from the dataset.

1. `prismatique/hrtem/sim.py:1316-1334` — `_postprocess_and_reorganize_image_subset` loads the
   raw prismatic array, calls `_apply_objective_aperture(...)` (line 1323) and **then** writes
   the result to `/data/image_wavefunctions` (line 1334). `SECTION_READ`.
2. `prismatique/hrtem/sim.py:1366-1400` — the raw array is read from
   `<output_dirname>/prismatic_output.h5` at
   `4DSTEM_simulation/data/realslices/HRTEM_fp{iiii}/data`, then
   `np.transpose(dataset[()], axes=(2, 1, 0))[:, ::-1, :]` (line 1387). `SECTION_READ`.
3. `prismatique/hrtem/sim.py:1404-1454` — `_apply_objective_aperture` is an FFT → hard
   annular top-hat mask → IFFT. The mask is
   `(rel_angles <= max_r_angle) * (rel_angles >= min_r_angle)` (line 1452), with the window in
   mrad taken from `objective_aperture_params`. **No aberration function, no CTF, no
   envelope** is applied here. `SECTION_READ`.
4. `prismatique/aperture.py:113-114` — `_default_window = (0, float("inf"))`.
   `REPRODUCED` (command 14): `aperture.Params defaults: {'offset': (0.0, 0.0), 'window': (0.0, inf)}`.
   The repository never sets `objective_aperture_params`, so the mask is identically 1 and
   step 3 is a numerical no-op (an FFT round-trip).

So `prismatique` adds nothing optical. Everything that determines the plane of the wave is in
the engine:

5. `prismatic-cpp/src/HRTEM_entry.cpp:120-153` — `HRTEM_runFP` calls `PRISM01_calcPotential`
   then **`PRISM02_calcSMatrix(pars)`**; the HRTEM output *is* the compact S-matrix
   `pars.Scompact`. `SECTION_READ`.
6. `prismatic-cpp/src/PRISM02_calcSMatrix.cpp:480-495, 560-581` —
   `fill_Scompact_CPUOnly` launches only **`propagatePlaneWave_CPU_batch`** (line 574); the
   non-batch `propagatePlaneWave_CPU` is **commented out** at line 573. `SECTION_READ`.
7. `prismatic-cpp/src/PRISM02_calcSMatrix.cpp:376-478` — inside the batch routine, after the
   slice loop and the final forward FFT (line 429):

```cpp
433  if(pars.meta.algorithm == Algorithm::HRTEM) // center defocus at middle of cell if running HRTEM
434  {
436      for (auto batch_idx = 0; ...)
438          auto p_ptr = pars.propBack.begin();
442              *psi_ptr++ *= (*p_ptr++);     // propagate
445  }
```

8. `prismatic-cpp/src/PRISM02_calcSMatrix.cpp:105-116` — the two propagators:

```cpp
105  pars.prop.at(y,x)     = exp(-i*pi*lambda*sliceThickness*q2);          // forward, per slice
109  //propBack is only used to center defocus of HRTEM at center of cell
110  pars.propBack.at(y,x) = exp(+i*pi*lambda*(tiledCellDim[0]/2)*q2  -  i*chi(y,x));
```

with `chi = getChi(q1, qTheta, lambda, pars.meta.aberrations)` (line 96) built only when
`pars.meta.aberrations.size() > 0` (line 86), and `tiledCellDim[0]` being the **z** dimension
ΔZ (confirmed by `PRISM02_calcSMatrix.cpp:774  pars.sMatrix_defocus = pars.tiledCellDim[0];`
and `params.h:226-229` which builds `pixelSize` from `tiledCellDim[1], tiledCellDim[2]`).
The GPU path applies the same factor under the same condition
(`src/PRISM02_calcSMatrix.cu:889-895` and `:1008-1014`). `SECTION_READ`.

> ### The saved wave is **not** the exit-surface wave.
>
> `image_wavefunctions` holds the multislice exit wave **Fresnel back-propagated by ΔZ/2**,
> i.e. referred to the **mid-plane of the simulation supercell** (`z = ΔZ/2`), and then
> multiplied by `exp(-i·χ(q))` whenever any aberration is registered. It is then Fourier-cropped
> to the anti-aliased band and inverse-transformed onto a 2× coarser grid (§2b).
>
> For the repository's slab, ΔZ ≈ 198 Å, so the saved wave is defocused by **≈ −99 Å** relative
> to the exit surface. Interpreting it as an exit wave, or Fresnel-propagating it again in the
> pipeline, double-counts that propagation (policy §9.6: *"avoid applying lens transfer or
> propagation twice"*).

**Is any lens transfer applied by default via embeam?** No, with the repository's settings, but
by a narrow margin, and the mechanism is worth recording:

* `prismatique/sample.py:4269-4318` — `_unpack_lens_model_params_into_pyprismatic_sim_obj`
  sets `probeDefocus = NaN`, `C3 = NaN`, `C5 = NaN`; an embeam aberration with `(m,n)=(2,0)`
  is converted to `probeDefocus = wavelength*C_mag/pi` (line 4301); all other aberrations are
  written to a temporary `aberrations_file` as `"m n C_mag C_ang_deg"` (line 4303).
  `SECTION_READ`.
* `prismatique/sample.py:4695` — `_update_pyprismatic_sim_obj_for_next_prismatic_sim` then
  **overwrites** `probeDefocus = defocii[defocus_idx]`. `SECTION_READ`.
* `prismatique/hrtem/sim.py:841-859` — `_defocii` returns `Δf + √2·(Gauss–Hermite points)·σ_f`,
  with `Δf = λ·C_2_0_mag/π`. With the repository's
  `coherent_aberrations=()` and `chromatic_aberration_coef=0.0`, `REPRODUCED`
  (command 16): `defocii = [0.] Å`, one entry, `probe is_coherent: True` (command 14).
* `prismatic-cpp/src/aberration.cpp:135-222` — `updateAberrations(ab={}, C1=0.0, C3=NaN, C5=NaN)`
  pushes one entry `aberration{2, 0, mag = 0·π/λ = 0, 0.0}` (line 183). So
  `aberrations.size() == 1` and `chi ≡ 0`: `exp(-iχ) = 1`. `SECTION_READ`.

Therefore **with the repository's current parameters no defocus, no C3 and no aperture are
applied — but the ΔZ/2 back-propagation is applied unconditionally and is not optional.**

Two further engine facts recorded here because they are easy to get wrong:

* `refocus()` and `apply_aberrations()` (`PRISM02_calcSMatrix.cpp:604-736`) are **never called
  from the HRTEM path** — `grep` finds calls only in `src/PRISM_entry.cpp:170,242` (PRISM STEM).
  `SECTION_READ`.
* Upstream inconsistency (`SECTION_READ`, `src/aberration.cpp:173,183`): `updateAberrations`
  *searches* for defocus as `(m==0 && n==2)` but *creates* it as `aberration{2, 0, …}`.
  `getChi` (line 124) uses `m` as the radial power `(λq)^m`, so `{2,0}` is the physically
  correct entry and the search predicate can never match it. Benign for `prismatique`'s usage
  (it routes `(2,0)` through `probeDefocus` and never writes it to the file), but any
  hand-written aberration file must use `m` = radial order.

### 2b. Exact HDF5 output schema (prismatique 0.0.1, identical in 0.0.4)

`SECTION_READ` (`prismatique/hrtem/output.py:196-298`, `hrtem/sim.py:641-662, 774-836,
1012-1077, 1487`) and `REPRODUCED` (command 16).

Files written into `output_dirname`:

| File | Written when | Content |
|---|---|---|
| `hrtem_sim_wavefunction_output_of_subset_{i}.h5` | `image_params.save_wavefunctions=True` | complex waves, one file per frozen-phonon **subset** |
| `hrtem_sim_intensity_output.h5` | `image_params.save_final_intensity=True` | one 2D incoherently-averaged intensity image |
| `potential_slices_of_subset_{i}.h5` | `output_params.save_potential_slices=True` | projected potentials (repo: `False`) |
| `hrtem_simulation_parameters.json` | always | serialized `sim_params` |
| `prismatic_output.h5` | always (temp) | raw engine output, deleted by `_remove_temp_files` |

Wavefunction file layout:

```
/metadata/tilts     float32 (num_tilts, 2)   attrs: dim 1="tilt idx",
                                                    dim 2="vector component idx [0->x, 1->y]",
                                                    units="mrad"
/metadata/defocii   float32 (num_defocii,)   attrs: dim 1="defocus idx", units="Å"
/metadata/r_x       float32 (n_x,)           attrs: dim 1="r_x idx", units="Å"
/metadata/r_y       float32 (n_y,)           attrs: dim 1="r_y idx", units="Å"
/data/image_wavefunctions   complex64  (n_cfg, n_defocus, n_tilt, n_y, n_x)
        attrs: dim 1="atomic config idx"   dim 2="defocus idx"   dim 3="tilt idx"
               dim 4="r_y idx"             dim 5="r_x idx"       units="dimensionless"
```

Intensity file layout: `/metadata/{r_x,r_y}` and `/data/intensity_image` (float, shape
`(n_y, n_x)`, `units="dimensionless"`) — **no tilt or config axis: they have already been
collapsed** (see §4).

**dtype** is hard-coded `complex64` (`hrtem/sim.py:1065`), matching the engine, which is built
single-precision by default (`prismatic-cpp/CMakeLists.txt:20
`set(PRISMATIC_ENABLE_DOUBLE_PRECISION 0 …)`; `include/defines.h:113/127` selects
`NATIVE_DOUBLE`/`NATIVE_FLOAT`). `src/fileIO.cpp:474-478` moreover hard-codes the imaginary
member at byte offset 4, i.e. the HRTEM complex writer assumes float32 regardless of the build
flag. `SECTION_READ`.

**Axis calibration.** `hrtem/image.py:235-258` states Δx̃ = 2Δx, Δỹ = 2Δy and n_x = N_x/2,
n_y = N_y/2, "the result of an anti-aliasing operation performed in `prismatic`".
`_signal.py:261-278` builds the axes:

```python
r_x = 2Δx·arange(N_x/2) - ((N_x/2 - 1)·2Δx)/2          # ascending, centred on 0
r_y = -(2Δy·arange(N_y/2) - ((N_y/2 - 1)·2Δy)/2)       # DESCENDING, centred on 0
```

`REPRODUCED` (command 16), for a 800×600 potential grid on a 104.659 × 79.818 × 198.248 Å box:

```
potential grid N_x,N_y = (800,600); dx,dy = 0.13082,0.13303 A
image_wavefunctions shape = (1, 1, 1, 300, 400)  dtype=complex64
  dim4 'r_y idx'  size 300  r_y[0]=+39.7758  r_y[-1]=-39.7758 A  (step -0.26606)
  dim5 'r_x idx'  size 400  r_x[0]=-52.1989  r_x[-1]=+52.1989 A  (step +0.26165)
HRTEM image pixel = (0.26165, 0.26606) A == 2*(dx,dy) : True
```

**Three axis facts a loader must assert:** (i) the image pixel is **twice** the potential
pixel; (ii) `r_y` **decreases** with index (row 0 is the largest y) — `prismatique` produces
this by the `[:, ::-1, :]` flip at `hrtem/sim.py:1387`; (iii) `r_x`/`r_y` are centred on zero,
whereas the engine's own `dim1`/`dim2` in `prismatic_output.h5` run `0 … (n-1)·2Δx`
(`src/fileIO.cpp:506-507`) — a pure origin relabelling, no data movement.

**Both intensities and complex waves are stored**, in separate files, and they are *not*
consistent with one another: §4.

**Normalisation.** `src/fileIO.cpp:882-897` (`saveHRTEM`) writes
`output_buffer.at(i,j,k) = Scompact.at(order[k], j, i) * scale` with
`scale = dimi*dimj = n_x·n_y`. Tracking the FFT scalings through
`propagatePlaneWave_CPU_batch` (`:391-398` incident δ-function of amplitude 1 →
`/= N_x·N_y`; `:413-427` matched forward/backward pairs; `:429` final forward FFT;
`:447-471` crop and `/ N_small`, `N_small = n_x·n_y`) gives `|Scompact| = 1/(n_x n_y)` for a
vacuum plane wave, so **the saved `image_wavefunctions` has |ψ| = 1 in vacuum for a
unit-intensity incident plane wave** (`DERIVED_HERE` from `SECTION_READ` code). The stored
intensity image is *not* |ψ|²: `hrtem/sim.py:1572-1577` rescales it so that
`sum(image) == avg_num_electrons_per_postprocessed_image` (repo: 1.0).

### 2c. Beam tilt: how it is implemented, units, sign, axes, limits

`SECTION_READ` + `REPRODUCED`.

**Mechanism.** `prismatic-cpp/src/PRISM02_calcSMatrix.cpp:391`:
`psi_stack[batch*slice_size + pars.beamsIndex[jj]] = 1;` — the incident wave for a tilt is a
**single Fourier component of the simulation grid set to 1**, inverse-transformed. It is an
exact plane wave `exp(2πi(q_x x + q_y y))` that is periodic on the grid, so **tilt introduces
no aliasing of its own at any magnitude** — the tilt is, however, *quantised* to the FFT grid,
and is bounded by the anti-aliasing mask (below). The tilt enters **only through the entrance
plane**; the propagator `exp(-iπλ·dz·q²)` (line 105) is the same for all tilts and uses the
*absolute* spatial frequency including the tilt, which is the standard tilted-illumination
multislice treatment.

**Angle definition and units.** `prismatic-cpp/src/PRISM02_calcSMatrix.cpp:213-214`
`relTiltX = |qxa·λ − xTiltOffset_tem|`, i.e. θ_x = λ q_x, θ_y = λ q_y, in **radians**
internally; `prismatique/tilt.py:177-179` states the same relation (θ_x = λk_x, θ_y = λk_y).
`pyprismatic/core.cpp:204-215` divides every tilt field by 1000 on entry, so the
**pyprismatic-level and prismatique-level units are mrad** — and `prismatique/sample.py:4327-4337`
passes mrad. `SECTION_READ`. **No factor-1000 error exists in this chain.**

**Which component is x.** `x` is the **first** column of the `.xyz` second line and the first
`offset` element; `y` is the second. In the repository's cleave frame the generator writes
`Lx` = the **surface-normal** direction [1,−1,1], `Ly` = the in-plane step-normal [1,−1,−2],
`Lz` = the beam [110] (`sample_generators/si110_cleave_slab_generator.py:41,49,65-71`).
So `tilt offset[0]` tilts the beam **towards the surface normal** and `offset[1]` along the
step-normal. `SECTION_READ`.

**Sign.** `prismatique/tilt.py:671-673` records `x_tilt = angular_mesh[0][i][j]*1000` with the
mesh built from signed FFT frequencies (`sample.py:1866-1874`), and `src/fileIO.cpp:512-513`
writes the same signed values ×1000 into `/metadata/tilts`. The sign convention is therefore
"θ = +λq of the illuminating Fourier component", consistently in the engine, the wrapper and
the metadata — **but it is only defined relative to the sign of the x/y axes in the `.xyz`,
and it interacts with the z-flip of §2g.** No independent check of the handedness was possible
here: `UNVERIFIED`.

**The window is a *selection region*, not a list.** `prismatique/tilt.py:225-245` and
`:655-685`: `offset` (mrad) and `window` (radial `(min,max)` or rectangular `(min,max,min,max)`)
select **every** grid point of Θ_{f_x,f_y} inside the window, sorted by
`np.lexsort((ts[:,1], ts[:,0]))` — ascending in θ_x first, then θ_y. The engine sorts
identically (`src/fileIO.cpp:656-683`, `std::sort` on `std::pair<xTilt,yTilt>`). `SECTION_READ`.
Grid step = λ/ΔX, λ/ΔY times the interpolation factors
(`prismatique/tilt.py:509-551`).

**Anti-aliasing ceiling on tilt.** `src/PRISM02_calcSMatrix.cpp:65-79` builds `qMask = 1` only
on the inner quarter of the FFT grid in **each** axis (a rectangle |q_x| ≤ N_x/4·Δq_x,
|q_y| ≤ N_y/4·Δq_y), i.e. **half of Nyquist, not the usual 2/3**; line 62 sets
`qMax = min(dpx·ncx, dpy·ncy)/2`. `include/params.h:241-242` states the tilt ceiling
explicitly: `maxXtilt = lambda/(4*pixelSize[1])`, `maxYtilt = lambda/(4*pixelSize[0])`.
Beams outside `qMask` are rejected in `setupBeams_HRTEM` (line 222/230). `SECTION_READ`.

**Are 24 mrad tilts handled?** `REPRODUCED` (command 15), on a synthetic box matching the
repository generator's defaults (104.659 × 79.818 × 198.248 Å), 200 keV:

```
=== advisory px = 0.5 A ===                     (slab-generator default --advisory-px-A 0.5)
  potential pixel dx,dy = 0.4845,0.4989 A ; HRTEM image pixel = 0.9691,0.9977 A
  tilt.step_size = (0.2396, 0.3142) mrad
  Prismatic anti-alias tilt ceiling lam/(4*dx) = 12.940 mrad (x), 12.568 mrad (y)
  sweep [23.997,23.997] -> offset=(23.997,0), window=(0,0.10):
      IndexError: too many indices for array: array is 1-dimensional, but 2 were indexed

=== advisory px = 0.13 A ===                    (meta_tilt_examples.json)
  Prismatic anti-alias tilt ceiling lam/(4*dx) = 47.926 mrad (x), 47.131 mrad (y)
  sweep [23.997,23.997] -> 1 tilt; tilt_series[0] = [23.96282486  0.]
```

So: **at the repository's own default 0.5 Å pixel size a 24 mrad tilt is impossible** — the
selection returns an empty set and `prismatique.tilt._series` raises `IndexError` before the
engine is ever reached. The `meta_tilt_examples.json` value 0.13 Å is the setting that makes it
possible. `REPRODUCED`.

`DERIVED_HERE` (arithmetic on the verified ceiling, λ = 0.0250793 Å at 200 keV, Si a = 5.4309 Å):
at Δx = 0.1308 Å the usable half-angle is ±47.93 mrad per axis, and the output grid's own
Nyquist frequency is 1/(4Δx) = **1.911 Å⁻¹**. The (666) reflection the repository targets has
1/d₆₆₆ = 1/0.52259 = **1.9136 Å⁻¹** — marginally *outside* the representable band. And a beam
tilted to +θ_B = +23.96 mrad plus g₆₆₆ (λ|g| = 47.99 mrad) lands at ≈ 71.95 mrad, far outside
the 47.93 mrad ceiling, so that diffracted beam is removed by the anti-aliasing mask; only the
symmetric setting (−θ_B in, +θ_B out) keeps both beams inside. **The sampling must be chosen
from the *outgoing* beam angle, not the incident tilt.**

**Multiple tilts are stored along `dim 3`** of `image_wavefunctions`, in the lexicographic
order above, with the actual values in `/metadata/tilts` (mrad). There is no
`tilt_series_params` object: the only knobs are `tilt.Params(offset, window, spread)`.

### 2d. Frozen phonons / thermal configurations

`SECTION_READ` + `REPRODUCED`.

**Are complex waves averaged?** No. `hrtem/sim.py:1490-1494` writes each configuration into its
own `dim 1` slot; `output.py:231-235` states *"unlike the intensity data, the complex-valued
wavefunction data is not postprocessed"*. **Complex waves are saved per configuration and are
never averaged — coherently or otherwise.** Only the *intensity* file is averaged
(`hrtem/sim.py:1546-1549`, §4).

**What the repository actually gets.** Neither pipeline script ever constructs
`prismatique.thermal.Params` (`grep -rn -i thermal pipeline/*.py` → **no matches**), so the
default is taken. `REPRODUCED` (command 14):

```
thermal.Params defaults: {'enable_thermal_effects': False,
                          'num_frozen_phonon_configs_per_subset': 1,
                          'num_subsets': 1, 'rng_seed': None}
```

`thermal.py:375-385`: *"If `enable_thermal_effects` is set to `False`, then for each atom,
u_{i,rms} is set to zero."* The engine honours this at
`src/PRISM01_calcPotential.cpp:451-466` (`if (pars.meta.includeThermalEffects)` … `else
perturbX = perturbY = perturbZ = 0`).

> **The `sigma = 0.076 Å` written into every line of the `.xyz`
> (`sample_generators/si110_cleave_slab_generator.py:40,55,298`) is read by the engine but
> never used: thermal effects are off, there is exactly one configuration, `dim 1 = 1`, and
> the slab is a static zero-temperature lattice.** The generator even writes
> `enable_thermal_effects` / `num_frozen_phonon_configs_per_subset` / `num_subsets` into
> `meta.json` — and no script reads them.

**Meaning of `sigma`.** `prismatique/sample.py:268-289` defines the sixth column as
`u_x_rms = (1/√3)·u_{i,rms}`, with `u_{i,rms} = √⟨u_i²⟩` the **3-D** RMS displacement, from the
Einstein model `p_a(u) = (3/2π u_rms²)^{3/2} exp(−(3/2)(u/u_rms)²)` (`thermal.py:342-357`).
The engine uses that column directly as the **per-Cartesian-axis** standard deviation:
`src/PRISM01_calcPotential.cpp:453-455  perturbX = randn(de)*sigma[i]` (and `perturbY`,
`perturbZ`). `SECTION_READ`. So **0.076 Å is a per-axis RMS displacement**
(√⟨u_x²⟩), equivalent to u_rms(3D) = √3 × 0.076 = 0.132 Å and B = 8π²(0.076)² = 0.456 Å² —
a conventional room-temperature Si value. The value is dimensionally *correct*; it is simply
inert as configured.

Two engine behaviours to record if thermal effects are ever switched on:

* **Displacements are Gaussian, resampled per configuration; there is no Debye–Waller damping
  of the atomic form factors.** `SECTION_READ` (`PRISM01_calcPotential.cpp:451-466`; the
  potential lookup is the static Kirkland parameterisation).
* **In the 2-D potential path only `perturbX`/`perturbY` are applied — no z displacement**
  (`PRISM01_calcPotential.cpp:220-221`); the 3-D path (`potential3D = true`, which the
  repository selects via `z_supersampling = 4 > 0`) applies all three (lines 453-455).
* **Seeding is thread-dependent:** `srand(pars.meta.randomSeed + 1000*t)` and
  `std::mt19937 de(pars.meta.randomSeed + 1000*t)` with `t` the *thread index*
  (`PRISM01_calcPotential.cpp:193-194, 434-436`), and the per-configuration seed is drawn from
  the global C RNG (`HRTEM_entry.cpp:122  pars.meta.randomSeed = rand() % 100000;`).
  **Frozen-phonon realisations are therefore not reproducible across different thread counts**,
  even with `thermal_params.rng_seed` set. `SECTION_READ`.

**What the repository's loader does with the axis.** `pipeline/specular_filter.py:61-77`
(`_pick_first_2d_slice`) takes `dset[(0,)*(ndim-2) + (slice(None), slice(None))]`, i.e.
`[0, 0, 0, :, :]` — configuration 0, defocus 0, **tilt 0**. With the current settings
`dim 1 = dim 2 = 1`, so the first two indices are unambiguous; the third is not (§3).

### 2e. Propagator, slicing, anti-aliasing, PRISM-vs-multislice, precision

| Item | Fact | Locator | Label |
|---|---|---|---|
| Propagator | `exp(−iπ λ δz q²)` — **paraxial Fresnel**, no exact/√(1−λ²q²) option, no evanescent handling | `prismatic-cpp/src/PRISM02_calcSMatrix.cpp:105-107` | SECTION_READ |
| Transmission | `t = exp(+i σ V)`, σ = (2π/λE₀)(mc²+eE₀)/(2mc²+eE₀) | `src/PRISM02_calcSMatrix.cpp:494`; `include/params.h:215` | SECTION_READ |
| Slice count | `numPlanes = ceil(ΔZ / sliceThickness)`; `prismatique` sets `sliceThickness = ΔZ/num_slices + 1e-6` | `src/PRISM01_calcPotential.cpp:143`; `prismatique/sample.py:2588-2589` | SECTION_READ |
| Atom→slice | `slice = round((−z' + ΔZ)/δz + 0.5) − 1` — note the **z-flip**, §2g | `src/PRISM01_calcPotential.cpp:145-146` | SECTION_READ |
| 3-D potential | `potential3D = (z_supersampling > 0)`, `zSampling = z_supersampling`, sub-slice step `dzPot = sliceThickness/zSampling` | `prismatique/sample.py:4211-4213`; `src/PRISM01_calcPotential.cpp:588-591` | SECTION_READ |
| `potential_bound` | `potBound = atomic_potential_extent` (Å); prismatique default 3 Å, repo sets 8 Å | `prismatique/sample.py:4219-4220, 246-247`; docstring `sample.py:304-323` | SECTION_READ |
| Anti-aliasing | **1/2 of Nyquist**, applied as a *rectangular* per-axis mask on the propagator; output cropped to N/2 and pixel doubled | `src/PRISM02_calcSMatrix.cpp:62-79, 265-297`; `prismatique/hrtem/image.py:235-258` | SECTION_READ |
| Interpolation factors | HRTEM uses them only to *thin the tilt grid* (`Θ_{f_x,f_y}`), not to build an interpolated S-matrix | `src/PRISM02_calcSMatrix.cpp:198-199, 228-229`; `prismatique/tilt.py:205-213` | SECTION_READ |
| PRISM vs multislice | HRTEM is **plain multislice per plane wave**, re-using the S-matrix container; no PRISM interpolation/recombination step is executed | `src/HRTEM_entry.cpp:120-153`; `src/PRISM02_calcSMatrix.cpp:738-797` | SECTION_READ |
| Precision | `float32`/`complex64` by default (`PRISMATIC_ENABLE_DOUBLE_PRECISION 0`); HRTEM complex writer hard-codes offset 4 ⇒ float32 | `CMakeLists.txt:20,154-159`; `include/defines.h:113,127`; `src/fileIO.cpp:474-478` | SECTION_READ |

`DERIVED_HERE` — magnitude of the paraxial error for this geometry. The exact propagator phase
is (2π δz/λ)(√(1−λ²q²) − 1); expanding, the leading omitted term over the whole cell is
Δφ ≈ π ΔZ λ³ q⁴/4. At 200 keV (λ = 0.0250793 Å), ΔZ = 198.25 Å: a 24 mrad beam
(q = 0.957 Å⁻¹) accumulates **≈ 2.1 × 10⁻³ rad**; a 48 mrad beam (q = 1.914 Å⁻¹)
**≈ 3.3 × 10⁻² rad**; the *relative* phase between them, which is what a hologram measures, is
**≈ 3.1 × 10⁻² rad ≈ 0.005 × 2π**. So paraxiality is a ~1 %-of-a-fringe systematic, *not* the
dominant error — the dominant restrictions are the half-Nyquist band limit (§2c) and the
boundary conditions (§2f). This should be checked numerically before it is relied on.

### 2f. Periodic boundary conditions

`SECTION_READ`. `prismatique/discretization.py:168-175`: *"periodic boundary conditions are
imposed on the supercell in the x- and y-directions"*. The engine wraps atom footprints
explicitly (`src/PRISM01_calcPotential.cpp:474-475`
`for(auto &i : xp) i = (i % dim1 + dim1) % dim1;`) and every propagation step is an FFT, so the
wave is periodic in x and y at every slice. There is **no** absorbing boundary anywhere in
Prismatic — a grep for `absorb` in `prismatic-cpp/src` and `include` finds nothing relevant.

**What this means for the repository's slab.** In the cleave frame the generator makes
`x` = the **surface normal** (`si110_cleave_slab_generator.py:65-71`), with
`--x-vac-A` default 10 Å of vacuum on each face. The slab is therefore **periodically repeated
along its own surface normal with a 20 Å vacuum gap between the back face of one image and the
front face of the next**, and any wave leaving one surface re-enters at the other.
`DERIVED_HERE`: a beam at 48 mrad walks 0.048 × 198.25 = **9.5 Å** laterally over the cell —
comparable with the 20 Å gap; at 24 mrad it walks 4.8 Å. With only 10 Å of vacuum per face there
is no margin, and the "reflected" and "transmitted-through-the-next-image" contributions are
not separable. The repository's own intended mitigation — an absorbing layer on the bulk side —
**does not exist in this API and is silently discarded** (§3).

### 2g. How the cell is read from the `.xyz`, and tiling

`SECTION_READ`. `prismatique/sample.py:2233-2247` (`_supercell_dims`) skips line 1 and parses
line 2 as `(a, b, c)`, then multiplies by `unit_cell_tiling` component-wise; the engine tiles
in `src/atom.cpp:45-53`. The repository passes `unit_cell_tiling=(1,1,1)`
(`multislice_forward_model.py:259`), so **no tiling** — the `.xyz` cell *is* the supercell.
`prismatique.sample.check_atomic_coords_file_format` validates the format.

> **z-flip.** `prismatique/sample.py:280-285` documents the third coordinate column as `z'`,
> with `z = −z' + ΔZ`. The engine implements exactly this:
> `src/PRISM01_calcPotential.cpp:145-146`
> `round((−t_z + pars.tiledCellDim[0]) / sliceThickness + 0.5) − 1`.
> **The beam therefore enters at the *largest* `z` value in the file and exits at `z = 0`.**
> The repository's generator shifts all atoms into `[0, L]` and writes `z` directly
> (`si110_cleave_slab_generator.py:221,55`), with no flip, so the structure the engine
> propagates through is **mirrored along the beam** relative to what the generator drew.
> For a slab that is symmetric along the beam this may be harmless; it is *not* harmless for
> anything z-asymmetric (an intended entrance/exit surface, a z-dependent absorber window, or
> any statement about which face the beam strikes first). This must be checked explicitly.

### 2h. Normalisation and the definition of intensity

Covered in §2b: in vacuum `|image_wavefunctions| = 1` per unit-intensity incident plane wave
(`DERIVED_HERE` from `src/PRISM02_calcSMatrix.cpp:391-471` + `src/fileIO.cpp:885-897`); the
stored `intensity_image` is **not** `|ψ|²` but a renormalised electron-count image
(`prismatique/hrtem/sim.py:1572-1577`). The physical definition prismatique targets is
`I_HRTEM(x,y)Δx Δy ≈ N_e ⟨x,y|ρ̂_t|x,y⟩ Δx Δy` (`thermal.py:208-212`), with ρ̂_t the incoherent
mixture over defocus, tilt and phonon configuration (`thermal.py:250-260`).

---

## 3. The repository's use of the API

Checked call-by-call against prismatique 0.0.1 / embeam 0.0.1 actually installed
(`REPRODUCED`, command 14). **All calls succeed except one.**

| Repository call | Locator | Verdict |
|---|---|---|
| `prismatique.sample.check_atomic_coords_file_format(path)` | `multislice_forward_model.py:257` | OK |
| `sample.ModelParams(atomic_coords_filename, unit_cell_tiling, discretization_params, atomic_potential_extent)` | `:258-280` | OK |
| `sample.ModelParams(..., absorbing_layers=[...])` | `:269-276`, runner `:331-335` | **FAIL — `TypeError: ModelParams.__init__() got an unexpected keyword argument 'absorbing_layers'`** |
| `embeam.gun.ModelParams(mean_beam_energy, intrinsic_energy_spread)` | `:284-287` | OK (keV / keV) |
| `embeam.lens.ModelParams(coherent_aberrations=(), chromatic_aberration_coef=0.0)` | `:291-294` | OK |
| `prismatique.discretization.Params(sample_supercell_reduced_xy_dims_in_pixels, num_slices, z_supersampling, interpolation_factors)` | `:417-422` | OK; `gx//4` is correct because `N_x = 4·f_x·Ñ_x` with `f_x = 1` (`sample.py:2366`), verified `gx == N_x` |
| `prismatique.hrtem.image.Params(postprocessing_seq, avg_num_electrons_per_postprocessed_image, apply_shot_noise, save_wavefunctions, save_final_intensity)` | `:428-434` | OK |
| `prismatique.hrtem.output.Params(output_dirname, image_params, max_data_size, save_potential_slices)` | `:306-322` | OK |
| `prismatique.hrtem.system.ModelParams(sample_specification, gun_model_params, lens_model_params[, tilt_params])` | `:298-303`, runner `:413-421` | OK |
| `prismatique.worker.cpu.Params(enable_workers, num_worker_threads, batch_size)` | `:357-361` | OK |
| `prismatique.worker.gpu.Params(num_gpus, batch_size, data_transfer_mode, num_streams_per_gpu)` | `:365-370` | OK |
| `prismatique.tilt.Params(offset=[kx,ky], window=[0, span/2+0.1], spread=0.0)` | runner `:402-406` | Constructs OK; **semantics wrong**, see below |
| `prismatique.hrtem.sim.Params(...)`, `.dump(...)`, `prismatique.hrtem.sim.run(sim_params=...)` | `:611-629` | OK |

### 3.1 Silently swallowed defaults and dropped physics

**(a) The absorber is silently discarded.** `multislice_forward_model.py:275-280` wraps the
`ModelParams` construction in `try/except Exception` and, on failure, pops `absorbing_layers`
and retries. Since the keyword *always* raises (`REPRODUCED`), the absorbing layer configured
from `meta.json`'s `z_absorb_min_A`/`z_absorb_max_A` is **never applied**, and the script still
prints `Absorber window (z, Å): [...] (bulk side)` at line 510. Prismatic has no absorbing
boundary at all (§2f). In the tilt runner the absorber is dead code — `create_system_params` is
called without the `absorber` argument (`multislice_tilt_series_runner.py:800-807`).

**(b) Thermal parameters are never passed** → static lattice, one configuration (§2d).

**(c) `objective_aperture_params` is never passed** → window `(0, inf)`, no aperture (§2a).

**(d) Comment/behaviour mismatches worth cleaning up:** `max_data_size = 8_000_000_000` carries
the comment `# 2 GB` (`multislice_forward_model.py:317`); `z_sampling` is computed at
`:406-410` and never used; the source comments say "schema used by 0.0.2" while the README
pins 0.0.1 (the schema is in fact identical, §1.3).

### 3.2 Is the lens model turned into an image wave?

No — with `coherent_aberrations=()` and `chromatic_aberration_coef=0.0` the embeam objects
contribute nothing optical (`REPRODUCED`: `defocii = [0.] Å`, `is_coherent = True`). **But the
repository's belief that it is saving an "exit wave" is wrong for a different reason:** the
engine applies the ΔZ/2 Fresnel back-propagation unconditionally (§2a). The docstring of
`multislice_forward_model.py:7` ("Saves complex exit wave") and the print at line 639
("Saved: intensity + complex exit wave") are both incorrect: the saved wave is referred to the
**cell mid-plane**.

### 3.3 Tilt units and axes

Units are consistent (mrad throughout, §2c). The *axes* are consistent only by accident, and
the *selection* is wrong:

* The runner snaps the tilt **magnitude** to the x-grid step `λ/Lx` (`:378-389`) and *then*
  decomposes it into `(kx, ky)` through the azimuth (`:399-401`). For any azimuth other than 0
  the resulting offset is off-grid in **both** components (the grid steps differ: λ/Lx and λ/Ly).
  `REPRODUCED` (command 16): with az = 35.264°, the requested offset (19.5657, 13.8349) mrad
  resolves to the grid tilt (19.6495, 13.8252) mrad — an **0.084 mrad error in θ_x**, ≈ 0.35 %
  of the Bragg angle, i.e. a real excitation-error offset, not a rounding detail.
* The runner uses its own wavelength formula
  `12.2643/sqrt(V(1+V·0.978476e-6))` (`:381`) = 0.025079422 Å, while prismatique/embeam use
  0.025079337 Å (`REPRODUCED`) — a 0.0003 % difference that is harmless for physics but
  **fatal for the exact-equality test in `_tilt_weights`** (below).

### 3.4 The tilt axis the loader reads — the concrete defect

`pipeline/specular_filter.py:103-111` opens `data/image_wavefunctions` and
`_pick_first_2d_slice` (`:61-77`) returns `[0, 0, 0, :, :]`. `pipeline/process_all_tilts.py:33`
feeds it `hrtem_sim_wavefunction_output_of_subset_0.h5`.

* For **`multislice_forward_model.py`** (no `tilt_params` at all) the default is
  `offset=(0,0), window=(0,0)` → exactly one tilt at (0.0, 0.0) mrad with weight 1
  (`REPRODUCED`, command 17, case 4). Here `[0,0,0,:,:]` is the **only** slice and is correct —
  it is the on-axis wave.
* For **`multislice_tilt_series_runner.py`** it is generally **wrong**. `REPRODUCED`
  (command 15), repository default sweep 0 → 11 mrad step 0.15 (generator `--tilt-start/end/step`
  defaults), giving `offset = (5.5, 0)`, `window = (0, 5.6)`:

```
requested angles = 74;  SIMULATED tilts = 1309
tilt_series[0]   = [ 0.  -0.9426]   <-- what specular_filter.py [0,0,0,:,:] reads
nearest to offset= [5.5114  0.    ] at index 658
x-range 0.000..11.023  y-range -5.342..5.342 mrad
```

  The engine simulates **1309** plane waves (every grid point inside the 5.6 mrad disc), not the
  74 the script asked for, and slice 0 is a tilt of (0, −0.943) mrad at the edge of the disc —
  **not** the intended 5.5 mrad condition, which sits at index 658. The `--tilt-step` argument
  has no effect on what is simulated; only `min`/`max` do.

**And the intensity file is NaN.** `hrtem/sim.py:1604-1609`:

```python
if tilt_spread > 0: tilt_weights = exp(-0.5*(rel/spread)**2)
else:               tilt_weights = (rel_tilts == 0.0).astype(float)
tilt_weights /= np.linalg.norm(tilt_weights)
```

With `spread = 0` the weight is an **exact float equality test** against the offset.
`REPRODUCED` (command 17):

```
case 1: repo's own snapped offset 23.96290581324604, grid tilt 23.96282486 -> weights=[nan]
case 2: offset set EXACTLY to the grid value                              -> weights=[1.]
case 3: sweep 0..11 mrad, offset 5.5, 1309 tilts                          -> any NaN = True
```

Because the repository snaps with a slightly different λ, the offset never matches
bit-for-bit, all weights are zero, the L2 normalisation divides by zero, and
`hrtem_sim_intensity_output.h5` is filled with **NaN**. The repository never reads that file,
so the failure is invisible. (Even with an exact match, `spread = 0` makes the "incoherent tilt
average" a *single-tilt selection*, not an average.)

### 3.5 Pixel-size calibration — a factor of 2

`pipeline/process_all_tilts.py:41-51,67-74` passes `--dx/--dy = meta["advisory_pixel_size_A"]`
to `specular_filter.py`, whose `k_axes` (`:383-396`) builds `fftfreq(n, d=dx)`. The loader
**never reads `/metadata/r_x`, `/metadata/r_y`**.

But the HRTEM image pixel is **2Δx**, and Δx is the *achieved* pixel `Lx/N_x`, not the advisory
value. `REPRODUCED` (command 15/16): advisory 0.13 Å → Δx = 0.13082 Å → image pixel
**0.26165 Å**. The pipeline uses 0.13.

`DERIVED_HERE`: a k-axis built with `d` half the true value spans twice the true range, so a
peak found at a *requested* radius `1/d_target` in that axis is physically at `1/(2 d_target)`.
The filter searching for (666) at 1.9136 Å⁻¹ therefore selects the true frequency
0.9568 Å⁻¹ = 1/1.0452 Å = **1/d₃₃₃**; searching for the generator's default (2,−2,0) at
0.5208 Å⁻¹ selects 0.2604 Å⁻¹ = 1/3.840 Å = 1/(a/√2). **In general the factor-2 error makes the
filter lock onto the reflection at half the requested |g|.** Any step height derived from that
phase carries the corresponding error. (And, per §2c, 1.9136 Å⁻¹ exceeds the output grid's own
Nyquist 1.911 Å⁻¹ at Δx = 0.1308 Å, so the (666) spot is not representable at all.)

### 3.6 Could lens transfer or Fresnel propagation be applied twice?

**Yes, and one instance is already present.** The engine applies `exp(+iπλ(ΔZ/2)q²)` — a
Fresnel propagation by half the cell — before the wave is saved (§2a). The pipeline then treats
the array as an exit wave. Anything the pipeline adds — a defocus correction, a propagation to
a detector plane, or a CTF — would be a *second* optical transfer stacked on an undeclared
first one. The current `specular_filter.py` does not propagate, but it does apply a real-space
Tukey apodisation, zero-padding, a super-Gaussian k-space notch at the direct beam, and a
raised-cosine band-pass, then re-centres the carrier (`:452-599`) — all of which modify phase
and resolution and none of which is presently quantified (policy §9.8). If an aberration is ever
set through `embeam`, `exp(-iχ)` is folded into the *same* `propBack` factor
(`src/PRISM02_calcSMatrix.cpp:110-113`), so the aberration is applied at the cell mid-plane,
not at the exit surface — a further trap for any subsequent correction.

---

## 4. Ensemble semantics (policy §9.5)

**What the software gives for N frozen-phonon configurations in HRTEM mode.**
`SECTION_READ` (`prismatique/hrtem/sim.py:1326-1358, 1534-1579`; `output.py:231-275`;
`src/HRTEM_entry.cpp:64-101`):

1. Prismatic runs the whole multislice once per configuration
   (`HRTEM_entry.cpp:64  for(auto i = 0; i < pars.meta.numFP; i++)`), writing each complex
   result to its own group `HRTEM_fp{iiii}` when `saveComplexOutputWave = true` — which
   `prismatique` always sets (`sample.py:4385`).
2. `prismatique` copies each configuration into its own `dim 1` slot of
   `image_wavefunctions`: **N complex waves, per configuration, never averaged.**
3. The intensity file is built as

```python
dataset[()] += (np.einsum('ijk,i->jk', signal_data, tilt_weights)   # collapse tilt axis
                * _w_f_l(sim_params, l=defocus_idx)                  # Gauss-Hermite defocus weight
                / _total_num_frozen_phonon_configs(sim_params)       # incoherent phonon average
                / np.sqrt(np.pi))                                    # (cancels w_f_l for a coherent probe)
```
   (`hrtem/sim.py:1546-1549`) from `empix.abs_sq(...)` of the aperture-filtered complex wave
   (`:1339`). So the **intensity** is a correct |ψ|²-then-average over configurations, defocus
   and (weighted) tilt, and the tilt/config/defocus axes are **collapsed** in that file.

**Subsets vs configurations.** `num_subsets` × `num_frozen_phonon_configs_per_subset` is the
total; each subset gets its **own file**
`hrtem_sim_wavefunction_output_of_subset_{i}.h5` (`output.py:237-241`;
`hrtem/sim.py:445-465`). A loader that opens only `..._subset_0.h5`
(as `process_all_tilts.py:33` does) silently ignores every other subset.

**What the physically correct detector quantity is for an off-axis hologram.**
With an object branch u_o and a mutually coherent reference branch u_r sharing the *same*
realisation r (the same frozen-phonon configuration, the same defocus offset, the same
illumination tilt), the recorded hologram is

  I(x,y) = ⟨ |u_o^(r)(x,y) + u_r^(r)(x,y)|² ⟩_r
         = ⟨|u_o|²⟩ + ⟨|u_r|²⟩ + 2 Re ⟨ u_o^(r) u_r^(r)* ⟩ ,

the average being taken **over realisations, after squaring**, with the interference term
carrying the realisation-correlation ⟨u_o u_r*⟩. Coherent addition of waves from *different*
realisations, or averaging the complex waves first, is wrong (policy §9.5, [B03], [C02];
`prismatique/thermal.py:250-260` expresses exactly this mixture).

**Can the repository's data path produce it?** Partly.

* ✅ The wavefunction file **does** keep the per-configuration axis, so an intensity average
  over realisations is constructible in post-processing: `I = mean_c |ψ[c,d,t] + u_r|²`.
  This is the right way to do it, and it is available.
* ✅ Within one `[c, d, t]` slice the object and any reference derived from the *same* slice are
  automatically correlated, because the wave is a single coherent realisation.
* ❌ There is **no reference branch**. Prismatic simulates one specimen, one illumination.
  A biprism, a split illumination, or a vacuum reference path must be modelled by the
  pipeline, and the reference's curvature/carrier/amplitude must be stated as assumptions
  (policy §9.4). `specular_filter.py` does not do this: it Fourier-selects a spot from the
  *simulated complex field*, which is a different quantity from a hologram sideband
  (policy §9.1).
* ❌ As configured, N = 1 and the phonon axis is degenerate (§2d), so no ensemble exists to
  average.
* ❌ The intensity file that *would* be the ensemble-averaged detector signal is NaN whenever
  the tilt offset is off-grid (§3.4), and in any case it has already collapsed the tilt axis
  with a delta-function weight, which is not what a hologram at one tilt needs.
* ⚠️ The loader's `[0,0,0]` slice silently discards all three ensemble axes — exactly the
  failure policy §9.6 warns about ("Fail clearly on ambiguous axes or missing calibration").

**Recommended data path.** Keep the complex file as the primitive. For each realisation
`(c, d, t)` form `u_o = ψ[c,d,t]` and an explicitly specified `u_r`, compute
`|u_o + u_r|²`, then average over `c` (and over `d`, and over `t` with the *intended* weights)
**after** squaring. Never write an averaged complex field.

---

## 5. Recommendations

### 5.1 Provenance that must be pinned and recorded

Record all of the following with every output (policy §8), none of which is currently captured:

| Item | Why | How |
|---|---|---|
| `prismatique`, `embeam`, `h5pywrappers`, `empix`, `hyperspy`, `numpy`, `scipy`, `h5py`, `ase` versions | `requirements.txt` pins nothing; `prismatique==0.0.1` does not pin `embeam` | `pip freeze` into the output dir; pin `prismatique==0.0.1` **and** `embeam==0.0.1` in `requirements.txt` |
| **Prismatic/pyprismatic commit + build flags** | not a declared dependency; PyPI `pyprismatic` (1.1.x, 2017) has no HRTEM mode at all | record the git SHA, `PRISMATIC_ENABLE_DOUBLE_PRECISION`, CPU/GPU build, FFTW version |
| **Numeric precision** | float32/complex64 by default; the complex HDF5 writer assumes float32 | assert `dset.dtype == complex64` and record the CMake flag |
| **Thread count** | frozen-phonon RNG is seeded `randomSeed + 1000*thread_index` — realisations change with thread count | record `SLURM_CPUS_PER_TASK`, `num_worker_threads`, `batch_size`, GPU count/streams |
| `thermal_params.rng_seed` | currently `None`; and even when set it is not thread-invariant | set it explicitly and record it, with the caveat above |
| Input hashes | `.xyz`, `meta.json` | SHA-256 of each, plus the repo commit |
| Config | `hrtem_simulation_parameters.json` is already written by `sim_params.dump` — keep it, and hash it | |

Also record the derived quantities the engine computes but does not save in an obvious place:
`N_x, N_y`, `Δx, Δy`, image pixel `2Δx, 2Δy`, `num_slices`, `sliceThickness`, `potBound`,
`z_supersampling`, the anti-aliasing tilt ceiling `λ/(4Δx)`, and the realised tilt list from
`/metadata/tilts`.

### 5.2 API facts to encode as hard assertions in a corrected pipeline

A corrected loader should **fail loudly** rather than guess (policy §9.6). Minimum set:

1. `"/data/image_wavefunctions" in f` — no fallback search for "any complex dataset".
   Delete the `visititems` fallback in `specular_filter.py:129-156`.
2. `dset.ndim == 5` and
   `[dset.attrs[f"dim {i}"] for i in 1..5] == ["atomic config idx", "defocus idx", "tilt idx", "r_y idx", "r_x idx"]`.
3. `dset.dtype == np.complex64`.
4. Read `/metadata/r_x`, `/metadata/r_y` and derive `dx = r_x[1]-r_x[0]`,
   `dy = abs(r_y[1]-r_y[0])`. **Never** take the pixel size from `meta.json`.
   Assert `dx ≈ 2 * (Lx / N_x)` to catch the factor-2 error, and assert `r_y[1] < r_y[0]`
   (descending) so the row order is explicit.
5. Read `/metadata/tilts` (mrad) and select the tilt index by **matching the intended
   (θ_x, θ_y) to within half a grid step**, not by taking index 0. Fail if no tilt is within
   tolerance, and fail if more tilts were simulated than were requested without the user
   acknowledging it.
6. Assert `n_cfg == expected_num_configs` and iterate **all** subsets
   (`hrtem_sim_wavefunction_output_of_subset_*.h5`), not just subset 0.
7. Record, in the output metadata, that **the plane is the supercell mid-plane `z = ΔZ/2`,
   not the exit surface**, and that the wave has already been Fresnel-propagated by −ΔZ/2.
   Any further propagation must be stated relative to that plane.
8. Assert the sampling supports the target reflection:
   `1/d_target < 1/(4·Δx_potential)` (the output Nyquist) **and**
   `|θ_out| = |θ_in + λ/d_target| < λ/(4·Δx_potential)` (the anti-aliasing tilt ceiling).
   At Δx = 0.1308 Å these give 1.911 Å⁻¹ and 47.93 mrad respectively — the (666) target sits
   outside both unless the symmetric Bragg setting is used and the grid is made finer.
9. Assert the z-convention: either write the `.xyz` with `z' = ΔZ − z_physical`, or assert that
   the slab is z-symmetric within tolerance.
10. Refuse to read `hrtem_sim_intensity_output.h5` without an `isfinite` check (it is NaN
    whenever the tilt offset is off-grid), or set `save_final_intensity=False` and build the
    intensity in post-processing where the ensemble weights are explicit.

Minimum repository fixes, in priority order: (i) tilt-index selection from `/metadata/tilts`;
(ii) pixel size from `/metadata/r_x`; (iii) stop calling the saved array an exit wave;
(iv) remove or re-implement the absorber (it currently does nothing); (v) pass
`thermal.Params` explicitly if phonons are wanted; (vi) pin versions.

### 5.3 Is Prismatic's HRTEM path adequate for a grazing-incidence slab?

**Not without substantial compromise.** The blocking issues, in order of severity, all
`SECTION_READ`/`REPRODUCED` above:

1. **Periodic boundaries along the surface normal, with no absorber.** The slab is repeated
   along its own normal with a 20 Å gap and every slice is an FFT, so escaping flux re-enters.
   Prismatic has no absorbing boundary and `prismatique` has no API for one. For a *reflection*
   geometry this is the fundamental obstacle: it is precisely the direction in which the wave
   must be allowed to leave.
2. **Half-Nyquist anti-aliasing.** The usable half-angle is λ/(4Δx), one third smaller than the
   conventional 2/3 rule, and it bounds the *outgoing* beam as well as the tilt. Reaching the
   (666) condition needs Δx ≲ 0.13 Å over a ~105 × 80 Å cell → 800 × 600 potential pixels and
   only a 400 × 300 output — and the target spot still lands on the band edge.
3. **Paraxial propagator only.** Quantified in §2e as ≈ 0.03 rad of relative phase for this
   cell — tolerable, but with no way to check it inside Prismatic.
4. **Mandatory, undocumented ΔZ/2 back-propagation** of the saved wave.
5. **The tilt "series" is a window, not a list**, which makes a controlled tilt series awkward
   and expensive (1309 plane waves for a 74-point sweep).
6. **Upstream is unmaintained as of January 2026** (`prismatic-cpp/README.md`), and the
   maintainers themselves recommend abTEM.

These are properties of a transmission code being used in reflection; none of them is a bug in
Prismatic. Policy §9.3 is explicit that transmission multislice is neither automatically valid
nor automatically invalid here — but the *boundary conditions* above are a concrete, verified
obstacle, not a philosophical one.

### 5.4 Alternatives — what each can and cannot do

**abTEM 1.1.0** (`SECTION_READ`, source at HEAD `e78cb7b`; note the docs site
`abtem.readthedocs.io` was blocked, so all statements below come from the source):

* ✅ **Exact (non-paraxial) Fresnel propagator**, the *default*:
  `abtem/multislice.py:51-107`, `order: Literal[1, 2, "exact"] = "exact"`, phase
  `(2π dz/λ)(√(1−λ²k²) − 1)`, with explicit separation of propagating and **evanescent**
  components (`phase[evanescent] = (2π dz/λ)(i√(x−1) − 1)`). Orders 1 and 2 are available for
  comparison, and the code **warns when the paraxial phase error exceeds 1e-2 rad**
  (`:109-124`). This is a decisive advantage for grazing incidence.
* ✅ **Tilt implemented as a shear of the propagator**, `exp(−2πi k_x tan(θ_x) dz)` ×
  `exp(−2πi k_y tan(θ_y) dz)` (`abtem/multislice.py:129-159`), units mrad, applied at every
  slice — i.e. a *continuous* tilt, not quantised to the FFT grid. Documented limit:
  "This value should generally not exceed one degree" (`abtem/waves.py:2351`) ≈ 17 mrad, and
  `PlaneWave.tilt` is described as "Small-angle beam tilt [mrad]… Implemented by shifting the
  wave functions at every slice" (`:2106-2107`). **24 mrad is above the documented comfort
  zone** — this must be validated, not assumed.
* ✅ **2/3 anti-aliasing** with a soft taper: `abtem/core/abtem.yaml:91-95`
  `antialias: cutoff: 0.6666666, taper: 0.01`. ~33 % more usable band than Prismatic at the
  same pixel size.
* ✅ **Explicit separation of exit wave and image wave**: multislice returns `Waves`, and
  `apply_ctf` is a separate step — no hidden back-propagation.
* ✅ **Frozen phonons with an explicit `ensemble_mean` switch**
  (`abtem/inelastic/phonons.py:70-80, 306, 323`), so per-configuration waves can be retained.
* ❌ **No reflection/RHEED mode, and no absorbing boundary primitive** found in the source.
  Periodic x/y boundaries still apply. abTEM fixes the propagator, the band limit and the
  book-keeping — it does **not** fix the boundary-condition problem (issue 1 above).

**py_multislice** (`SECTION_READ`, HEAD `5e5e4d8`, 2025-01-09):

* ✅ Tilt "by shearing the propagator", units `'mrad' | 'pixels' | 'invA'`, documented for
  "(small < 50 mrad) tilt" (`pyms/py_multislice.py:101-137`) — a *higher* stated limit than
  abTEM's, and in the right range for 24/48 mrad.
* ✅ **2/3 band limit by default**: `make_propagators(..., bandwidth_limit=2/3)`
  (`pyms/py_multislice.py:108`).
* ✅ **Absorptive potentials** (thermally smeared elastic potential + TDS absorptive potential,
  `pyms/structure_routines.py:1033-1052, 1629-1650`; `Premixed_routines.py:1486-1495`) *and*
  frozen phonons — so both ensemble treatments are available.
* ✅ GPU via PyTorch; small, readable, easy to modify.
* ❌ No reflection/RHEED mode found. The absorptive potential models TDS loss, **not** an
  absorbing *boundary*; it does not solve issue 1 either.
* ❌ Propagator is Fresnel (built through `make_contrast_transfer_function`); no exact
  √(1−λ²k²) option found. `UNVERIFIED` — I did not read the full CTF construction.

**A custom NumPy/CuPy multislice.** For this specific problem this is the only option that
addresses the boundary condition. It costs ~200 lines and buys: an explicit complex absorbing
layer (a smooth `exp(−η(x))` ramp on the vacuum side of the surface normal, which is what the
repository already tried to configure and which *no* packaged code exposes); a choice of
2/3 or larger band limit; an exact propagator; a tilt applied exactly as an entrance-plane
Fourier component *or* as a propagator shear, so the two can be compared; per-realisation
output with no hidden propagation; and explicit control of the reference plane. It costs the
validated atomic potentials, the optimised FFT scheduling and the community scrutiny — so it
must be benchmarked against one of the above in a *transmission* configuration first, and
against a genuine dynamical reflection calculation (a RHEED/Bloch-wave or Peng–Dudarev–Whelan
style treatment, [B07]/[B08]) before any reflection result is trusted. Policy §9.3 requires
exactly that: *"a transmission-only benchmark does not settle reflection validity."*

**Suggested route.** Keep the existing Prismatic run as a *documented benchmark* of the
transmission path, with its true semantics recorded (mid-plane wave, half-Nyquist band, static
lattice, one tilt). Reproduce that same configuration in abTEM (exact propagator, 2/3 band,
explicit exit wave) as an independent cross-check of the forward model. Then build the
reflection-specific model — absorbing boundary on the vacuum side of the surface normal,
explicit reference branch, per-realisation intensity averaging — in whichever of abTEM or a
custom kernel gives the needed control, and validate it against a reflection benchmark rather
than a transmission one.

---

## 6. API fact → source locator → evidence label

| # | API / engine fact | Locator | Label |
|---|---|---|---|
| 1 | `prismatique` 0.0.1 and `embeam` 0.0.1 exist on PyPI (2025-03-13 / 2025-01-30) | PyPI JSON; `prismatique/version.py:21` | REPRODUCED |
| 2 | `prismatique` does not declare `pyprismatic`; PyPI `pyprismatic` is 2017 v1.1.x with no HRTEM | `prismatique-0.0.1.dist-info/METADATA`; `pip index versions pyprismatic`; absence of `Algorithm::HRTEM` pre-2.0 | REPRODUCED / SECTION_READ |
| 3 | `hrtem/sim.py` is byte-identical in 0.0.1 and 0.0.4; ctor signatures unchanged 0.0.1→0.0.4 and embeam 0.0.1→0.0.5 | `diff` (command 14 group) | REPRODUCED |
| 4 | Citation request: Ophus 2017 + Pryor 2017, verbatim in every source file; GPL | `prismatic-cpp/src/HRTEM_entry.cpp:1-12` (+19 files) | SECTION_READ |
| 5 | Dataset path `/data/image_wavefunctions`, 5-D, `complex64` | `prismatique/hrtem/sim.py:1063-1073, 1487` | SECTION_READ |
| 6 | Axis order (cfg, defocus, tilt, r_y, r_x) | same, `dataset.attrs["dim 1".."dim 5"]`; `hrtem/output.py:266-275` | SECTION_READ |
| 7 | Shape `(1,1,1,300,400)` for an 800×600 potential grid, 1 tilt | command 16 | REPRODUCED |
| 8 | Image pixel = 2 × potential pixel; image dims = N/2 | `hrtem/image.py:235-258`; `_signal.py:261-278`; command 16 | SECTION_READ + REPRODUCED |
| 9 | `r_y` **descends** with index; `r_x`/`r_y` centred on 0 | `_signal.py:276`; command 16 | SECTION_READ + REPRODUCED |
| 10 | `/metadata/tilts` (mrad), `/metadata/defocii` (Å), `/metadata/r_x`,`r_y` (Å) | `hrtem/sim.py:653-660, 780-784, 829-833` | SECTION_READ |
| 11 | HRTEM output = `pars.Scompact` from `PRISM02_calcSMatrix`; plain multislice per plane wave | `src/HRTEM_entry.cpp:120-153`; `src/PRISM02_calcSMatrix.cpp:738-797` | SECTION_READ |
| 12 | **Saved wave is back-propagated by ΔZ/2 (cell mid-plane) and multiplied by exp(−iχ)** | `src/PRISM02_calcSMatrix.cpp:105-116, 433-445`; CUDA `:889-895, 1008-1014` | SECTION_READ |
| 13 | Only the batch propagator is used (single-beam version commented out) | `src/PRISM02_calcSMatrix.cpp:573-575` | SECTION_READ |
| 14 | `refocus()` / `apply_aberrations()` never called in the HRTEM path | `grep`; `src/PRISM_entry.cpp:170,242` only | SECTION_READ |
| 15 | `prismatique` applies only a hard top-hat objective aperture; default window `(0, inf)` = none | `hrtem/sim.py:1404-1454`; `aperture.py:113-114`; command 14 | SECTION_READ + REPRODUCED |
| 16 | Propagator = paraxial `exp(−iπλ δz q²)` | `src/PRISM02_calcSMatrix.cpp:105-107` | SECTION_READ |
| 17 | Anti-aliasing = **1/2 Nyquist**, rectangular per axis; tilt ceiling `λ/(4Δx)` | `src/PRISM02_calcSMatrix.cpp:62-79`; `include/params.h:241-242` | SECTION_READ |
| 18 | Tilt = single FFT-grid Fourier component set to 1; θ = λq; entrance plane only | `src/PRISM02_calcSMatrix.cpp:391, 213-214`; `prismatique/tilt.py:177-179` | SECTION_READ |
| 19 | Tilt units are mrad at the pyprismatic boundary (`/1000` inside core.cpp) | `pyprismatic/core.cpp:204-215`; `prismatique/sample.py:4327-4337` | SECTION_READ |
| 20 | `window` selects **all** grid tilts in the region; lexsort by (θ_x, θ_y) | `prismatique/tilt.py:655-685`; `src/fileIO.cpp:656-683` | SECTION_READ |
| 21 | 74 requested angles → **1309** simulated tilts; slice 0 = (0, −0.943) mrad, not the 5.5 mrad centre | command 15 | REPRODUCED |
| 22 | 24 mrad tilt at 0.5 Å pixels → empty series → `IndexError` | command 15 | REPRODUCED |
| 23 | `tilt_weights` → `[nan]` unless the offset matches a grid tilt bit-for-bit ⇒ **NaN intensity file** | `hrtem/sim.py:1604-1609`; command 17 | SECTION_READ + REPRODUCED |
| 24 | Complex waves saved **per configuration**, never averaged; intensity averaged and axes collapsed | `hrtem/output.py:231-235`; `hrtem/sim.py:1546-1549` | SECTION_READ |
| 25 | `thermal` defaults: effects **off**, 1 config, 1 subset, seed `None` | `thermal.py:165-172, 375-385`; command 14 | SECTION_READ + REPRODUCED |
| 26 | `.xyz` column 6 = per-axis RMS = `u_rms/√3`; used directly as the Gaussian σ per axis | `prismatique/sample.py:268-289`; `src/PRISM01_calcPotential.cpp:453-455` | SECTION_READ |
| 27 | Phonon RNG seeded per **thread** (`randomSeed + 1000*t`); per-FP seed from global `rand()` | `src/PRISM01_calcPotential.cpp:193-194, 434-436`; `src/HRTEM_entry.cpp:122` | SECTION_READ |
| 28 | **z-flip**: `z_physical = ΔZ − z_file`; beam enters at the largest file-z | `prismatique/sample.py:280-285`; `src/PRISM01_calcPotential.cpp:145-146` | SECTION_READ |
| 29 | Cell from `.xyz` line 2 × `unit_cell_tiling`; repo uses (1,1,1) = no tiling | `prismatique/sample.py:2233-2247`; `src/atom.cpp:45-53` | SECTION_READ |
| 30 | `N_x = 4 f_x Ñ_x` ⇒ repo's `gx//4` is correct for `f=(1,1)`; verified `gx == N_x` | `prismatique/sample.py:2366`; command 15 | SECTION_READ + REPRODUCED |
| 31 | PBC in x and y; no absorbing boundary anywhere in Prismatic | `discretization.py:168-175`; `src/PRISM01_calcPotential.cpp:474-475`; grep | SECTION_READ |
| 32 | `absorbing_layers` is **not** a `sample.ModelParams` keyword → `TypeError`, silently swallowed | `sample.py:358-362`; repo `:275-280`; command 14 | REPRODUCED |
| 33 | `|image_wavefunctions| = 1` in vacuum; `intensity_image` renormalised to `avg_num_electrons` | `src/fileIO.cpp:885-897`; `hrtem/sim.py:1572-1577` | DERIVED_HERE + SECTION_READ |
| 34 | Default build is float32; HRTEM complex writer hard-codes float32 offsets | `CMakeLists.txt:20`; `include/defines.h:113,127`; `src/fileIO.cpp:474-478` | SECTION_READ |
| 35 | `potential3D = (z_supersampling>0)`, `potBound = atomic_potential_extent` (repo 8 Å; default 3 Å) | `prismatique/sample.py:4211-4220, 246-247` | SECTION_READ |
| 36 | abTEM default propagator is **exact**, with evanescent handling and a paraxial-error warning | `abTEM/abtem/multislice.py:51-124` | SECTION_READ |
| 37 | abTEM tilt = propagator shear, mrad, "should generally not exceed one degree" | `abTEM/abtem/multislice.py:129-159`; `abtem/waves.py:2106-2107, 2351` | SECTION_READ |
| 38 | abTEM anti-aliasing cutoff 2/3 with 0.01 taper | `abTEM/abtem/core/abtem.yaml:91-95`; `abtem/antialias.py:40-41` | SECTION_READ |
| 39 | abTEM frozen phonons expose `ensemble_mean` | `abTEM/abtem/inelastic/phonons.py:70-80, 306, 323` | SECTION_READ |
| 40 | py_multislice: tilt by propagator shear, "< 50 mrad", `bandwidth_limit=2/3`, absorptive potentials | `py_multislice/pyms/py_multislice.py:101-137`; `pyms/structure_routines.py:1033-1052, 1629-1650` | SECTION_READ |
| 41 | Prismatic upstream is unmaintained as of Jan 2026; maintainers recommend abTEM | `prismatic-cpp/README.md` | SECTION_READ |
| 42 | `specular_filter.py` reads `[0,0,0,:,:]` and takes `dx` from `meta["advisory_pixel_size_A"]` | repo `pipeline/specular_filter.py:61-77, 103-111, 456-457`; `process_all_tilts.py:41-51` | SECTION_READ |
| 43 | Pixel-size factor of 2 ⇒ filter selects the reflection at half the requested \|g\| | §3.5 arithmetic on facts 8 and 42 | DERIVED_HERE |
| 44 | Paraxial phase error ≈ 3.1 × 10⁻² rad between 24 and 48 mrad beams over 198 Å | §2e arithmetic on fact 16 | DERIVED_HERE |
| 45 | Prismatic `updateAberrations` searches `(m=0,n=2)` but creates `(m=2,n=0)` for defocus | `src/aberration.cpp:173,183`; `getChi` `:124` | SECTION_READ |

---

## 7. Everything I could **not** verify

1. **The Prismatic 2.0 paper (Micron 151, 103141) and the PRISM paper (Ophus 2017) were not
   read.** `sciencedirect.com`, `link.springer.com` and `osti.gov` are blocked by this
   session's egress policy. Every statement about Prismatic's HRTEM algorithm above comes from
   its source tree instead. The papers' own description of the HRTEM mode — in particular
   whether the ΔZ/2 back-propagation is documented there — remains **UNVERIFIED**.
2. **`prism-em.github.io/about-cite/` was not read.** The citation text quoted in §1.5 is the
   source-file version; the live page's exact wording (including whether DaCosta 2021 is
   required) is `METADATA_VERIFIED` from a search snippet only.
3. **No simulation was executed.** `pyprismatic` could not be built here. Everything about the
   engine is code reading; the ΔZ/2 back-propagation, the half-Nyquist mask and the
   normalisation have **not** been confirmed against a real output file. The single highest-value
   next step is to run one tiny HRTEM job (a few atoms, vacuum, one tilt) and check:
   `|ψ| ≈ 1` in vacuum; the dataset shape and `dim` attributes; `r_x`/`r_y` spacing = 2Δx;
   and the ΔZ/2 defocus, by comparing a two-cell-length run against an analytic Fresnel
   propagation of a known object.
4. **The handedness/sign of the tilt relative to the crystallographic frame** is consistent
   *inside* the software but was not checked against the repository's rotation matrices. This
   interacts with the z-flip (fact 28) and with the README's (1,1,−1) vs [1,−1,1] discrepancy
   (policy §9.2). `UNVERIFIED`.
5. **Whether the repository's slab is z-symmetric** (and hence whether the z-flip is harmless)
   was not checked — it requires generating a slab, which would mean running the generator.
6. **py_multislice's propagator form** (whether any exact option exists) was inferred from
   `make_propagators` delegating to `make_contrast_transfer_function`; I did not read that
   function. `UNVERIFIED`.
7. **abTEM's accuracy at 24–48 mrad tilt** — the source documents "should generally not exceed
   one degree" but the propagator-shear formula uses `tan(θ)` and may well be better than the
   docstring. Not tested. `UNVERIFIED`.
8. **The `empix`/`hyperspy` versions' effect on `_postprocess_2d_signal`** — irrelevant with an
   empty `postprocessing_seq`, but unchecked for any other setting.
9. **Whether Prismatic exits cleanly or crashes when `numberBeams == 0`** — `prismatique` raises
   `IndexError` first (fact 22), so the engine is never reached; the engine's own behaviour is
   `UNVERIFIED`.
10. **The MIT-vs-GPLv3 licence question** (§1.5) is flagged, not resolved. It is a legal
    question, not a technical one.
