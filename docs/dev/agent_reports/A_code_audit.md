# A. CODE AUDIT — si110-reflection-holography (commit 6694959)

STATUS: COMPLETE (2026-09-21). Sections 0-8 written. All 14 repository files read in full; generator, filter and step-height scripts executed; forward-model/runner NOT executed (prismatique deliberately not installed) - their defects are established from the pinned source. Target repository unmodified (git status clean at 6694959).

Auditor: Agent A (code audit). Target (read-only):
`/tmp/claude-0/-home-user-Holography/18767b2d-e54d-5b3c-9746-d58b7d31a320/scratchpad/si110-reflection-holography`
Evidence labels per instruction section 1.4: METADATA_VERIFIED / SECTION_READ /
REPRODUCED / PROJECT_INPUT / ASSUMPTION / DERIVED_HERE / UNVERIFIED.

---

## 0. Inventory, provenance of this audit, and method

Repository snapshot audited: commit `66949599f0cbaf232ac649ba46a123e945660a1d` (HEAD,
"Update CITATION.cff", 2026-05-21), the same commit named in the instruction file line 10.
Verified by `git log` in the read-only clone. Evidence label: `METADATA_VERIFIED`.

Complete file inventory (every tracked file; all were read in full):

| Path | Lines | Role |
|---|---|---|
| `README.md` | 81 | Architecture diagram, dependency table, citations |
| `docs/PIPELINE_LOG.md` | 68 | Flowchart; truncated (see §4) |
| `requirements.txt` | 17 | Unpinned deps |
| `CITATION.cff` | 1 | **Empty** (single blank line) |
| `LICENSE` | 21 | MIT, © 2026 Hussien Ballouk |
| `.gitignore` | 54 | Ignores `*.h5`, `*.npz`, `*.png`, `outputs/` |
| `pipeline/multislice_forward_model.py` | 673 | Single-run Prismatique HRTEM wrapper |
| `pipeline/multislice_tilt_series_runner.py` | 906 | Tilt-sweep wrapper (superset of the above) |
| `pipeline/specular_filter.py` | 749 | k-space spot selection + "phase reconstruction" |
| `pipeline/step_height_reflection_formula.py` | 198 | phase → step height |
| `pipeline/process_all_tilts.py` | 85 | Batch driver |
| `pipeline/hdf5_output_validator.py` | 12 | 12-line HDF5 probe with a hard-coded macOS path |
| `pipeline/meta_tilt_examples.json` | 47 | Four example `meta.json` blocks |
| `sample_generators/si110_cleave_slab_generator.py` | 435 | Slab builder |

Total Python: 3058 lines (+289 lines of non-Python). **There are no tests anywhere**
(no `tests/`, no `test_*.py`, no `conftest.py`, no CI config, no `.github/`). `REPRODUCED`
(`find`/`ls` over the whole tree, §5).

Git history: 12 commits, 2026-05-14 → 2026-05-21, authors
`TrixodeStudios <trixodestudios@gmail.com>` (initial import) and
`Hussien Ali Ballouk Hernandez <hussienb@uvic.ca>` (11 GitHub web edits). The initial commit
message claims the work "replicat[es] the geometry of Osakabe et al. (1993)" — note that
[P03] Ultramicroscopy **48**, 475-481 (1993) is by **Banzhof and Herrmann**, *not* Osakabe
(instruction file lines 329-337). The Osakabe reflection-holography papers are 1988 [P01] and
1989 [P02]. The commit message is therefore a misattribution carried in the repository's own
history. `METADATA_VERIFIED` against the instruction file; the papers themselves were not read
by me.

Three of the last five commits are deletions: `CITATION.cff` 118 → 1 lines, a 22-line deletion
from the slab generator, `docs/PIPELINE_LOG.md` 119 → 68 lines (§4 of that document, which the
flowchart still cross-references, was deleted). `REPRODUCED` (`git log --stat`).

---

## 1. ARCHITECTURE AND DATA FLOW

### 1.1 Intended chain (README lines 8-49)

```
si110_cleave_slab_generator.py  →  *.xyz + *.cif + meta.json
        →  multislice_forward_model.py   (single run, no tilt)      ┐
        →  multislice_tilt_series_runner.py (tilt sweep)            ┘ → hrtem_sim_wavefunction_output_of_subset_0.h5
        →  specular_filter.py       → <prefix>_bragg_filter/results_arrays.npz + results.h5 + PNGs
        →  step_height_reflection_formula.py → step_height_measurement_mesa.png + stdout
        (process_all_tilts.py drives the filter over a directory of per-tilt runs)
```

The two forward-model scripts are **alternatives, not a chain**: the README diagram
(lines 18-30) shows `multislice_forward_model.py` feeding
`multislice_tilt_series_runner.py`, but the runner reads a `.xyz` file, not an `.h5`
(`multislice_tilt_series_runner.py:883` `parser.add_argument("coords_file", help="Path to .xyz file")`).
The runner is a superset copy of the forward model. `REPRODUCED` (md5 of each extracted
function body): **all twelve** shared helpers are **byte-identical** — `env_float`, `env_int`,
`_count_visible_devices`, `_parse_gpu_env_value`, `detect_available_gpus`,
`normalize_transfer_mode`, `estimate_wave_memory_gb`, `read_meta`, `analyze_prismatic_xyz`,
`derive_grid_from_meta`, `relativistic_lambda_A`, `quick_phase_report` — as is the `timeout`
context manager; `diff` of forward-model lines 1-246 against runner lines 1-296 shows only the
docstring and the inserted `parse_tilt_angles`/`format_tilt_angle`. ~250 lines of duplicated
code with no shared module; the two copies have already diverged in three physically significant places (§1.3).

### 1.2 `sample_generators/si110_cleave_slab_generator.py`

* **Docstring, line 3**: `"""Si[110] cleave-edge slab - contains bugs. no ready."""` — the
  author's own status marker, still present at HEAD.
* **Inputs**: command line only. **Outputs**, into
  `<outdir>/si110_{object|reference}/` (`:336-338`):
  `si110_{tag}.xyz` (Prismatic format, `:363`), `si110_{tag}.cif` (ASE, `:365`),
  `meta.json` (`:426-427`). `tag = "object"` iff `--create-step`, else `"reference"` (`:336`).
* `.xyz` format (`write_prismatic_xyz`, `:40-56`): line 1 comment, line 2
  `Lx Ly Lz` at `%.10f`, then `Z x y z occ sigma` per atom at `%.10f`, terminated by `-1`
  with **no trailing newline** (`:56`). `occ` is hard-coded 1.0 (`:40` default, `:364`);
  `sigma` = `--thermal-sigma-A`.

**CLI arguments and every default (`:245-305`):**

| Flag | Type | Default | Note |
|---|---|---|---|
| `--energy-keV` | float | **200.0** | |
| `--a-A` | float | **5.4309** | Si lattice constant; no source cited anywhere |
| `--n-x-si` | int | **9** | x-periods (`a√3` = 9.4065 Å) → 84.659 Å of Si |
| `--n-y` | int | **12** | y-periods (`a√1.5` = 6.6514 Å) → 79.817 Å |
| `--n-z-si` | int | **36** | z-periods (`a/√2` = 3.8402 Å) → 138.248 Å |
| `--x-vac-A` | float | **10.0** | vacuum on **each** side in x |
| `--z-vac-A` | float | **30.0** | vacuum on each side in z |
| `--create-step` | flag | **False** | |
| `--n-terraces` | int | **4** | |
| `--terrace-heights-bilayers` | int+ | **None** → `[0,1,…,N-1]` (`:330`) | |
| `--step-height-A` | float | **None** → `a/√3` = 3.13553 Å (`:312`) | |
| `--target-hkl` | 3×int | **[2, -2, 0]** | |
| `--tilt-start` | float | **0.0** mrad | |
| `--tilt-end` | float | **11.0** mrad | |
| `--tilt-step` | float | **0.15** mrad | → 74 requested angles |
| `--discrete-tilts` | float* | **None** | overrides start/end/step |
| `--advisory-px-A` | float | **0.5** | **conflicts with `meta_tilt_examples.json`'s 0.13** |
| `--thermal-sigma-A` | float | **0.076** | written to the `.xyz` but inert (§2c) |
| `--enable-thermal` | flag | **False** | written to meta, **never read by any script** |
| `--num-configs` | int | **1** | written to meta, **never read by any script** |
| `--outdir` | str | **`outputs/si110_cleave`** | |

**Every `meta.json` key written (`:368-424`)** — with the default `(2,-2,0)` values I
recomputed (`REPRODUCED`, §5):
`material="Silicon"`, `structure="Diamond Cubic; cleave-edge slab; beam = [110]"`,
`a_A=5.4309`, `a0_A=5.4309`, `energy_keV=200.0`, `zone_axis=[1,1,0]`,
`beam_direction_hkl=[1,1,0]`, `surface_normal_hkl=[1,-1,1]`,
`step_edge_direction_hkl=[1,1,0]`, `step_normal_in_plane_hkl=[1,-1,-2]`,
`target_hkl=[2,-2,0]`, `target_d_A=1.9201131089730104`, `target_theta_B_mrad=6.530739934856616`,
`g_dot_n_surf=0.816496580927726`, `tilt_azimuth_deg=35.264389682754654`,
`step_hkl=[1,1,1]` or `None`, `bilayer_height_A=3.135531576941939`,
`step_height_A` (= `bilayer_height_A` if `--create-step` else `0.0`),
`n_terraces`, `terrace_heights_bilayers`, `terrace_heights_A`,
`Lx_A`, `Ly_A`, `Lz_A`, `Lx_si_A`, `Lz_si_A`, `x_vacuum_A`, `z_vacuum_A`,
`period_x_A`, `period_y_A`, `period_z_A`, `box_A`,
`alpha_deg=0.3741838353648263`, `advisory_pixel_size_A=0.5`, `thermal_sigma_A=0.076`,
`enable_thermal_effects=false`, `num_frozen_phonon_configs_per_subset=1`, `num_subsets=1`,
and either `tilt_angles_mrad` or (`tilt_start_mrad`, `tilt_end_mrad`, `tilt_step_mrad`).

Hard-coded in the generator: `occ=1.0`; the `(1,-1,1)/(1,-1,-2)/(1,1,0)` frame (`:70-72`);
`n = [1,-1,1]/√3` repeated as a literal inside `g_dot_n_surf` (`:94`) instead of reusing
`slab_rotation_matrix()`; the histogram bin count 200 (`:177`); the `1e-6` snap tolerances
(`:194`, `:202`); `num_subsets=1` (`:413`); `step_hkl=[1,1,1]` (`:390`) — written even when
`--terrace-heights-bilayers` is non-integral in bilayers or `--step-height-A` overrides
`d_111`, so it is a label, not a computed value.

**Keys that downstream scripts require but the generator never writes:**
`advisory_dz_A`, `z_supersampling`, `z_sampling_A`, `advisory_theta_max_deg`,
`z_absorb_min_A`, `z_absorb_max_A`, `d111_A`. Every one of them is silently replaced by a
default in the two forward-model scripts (§2c, §4).

### 1.3 `pipeline/multislice_forward_model.py` vs `pipeline/multislice_tilt_series_runner.py`

**Invocation.** Forward model: positional `sys.argv` parsing (`:644-669`), not `argparse` —
`python multislice_forward_model.py <coords.xyz> [output_dir] [--production] [--timeout-min N]`.
Defaults: `output_dir="./rem_holo_output"` (`:650`), `production=False` (`:651`),
`timeout_min=5` (`:652`) — overridden to **30** when `--production` is given (`:668`).
The `--timeout-min` parser at `:659-662` reads `sys.argv[i+1]`, but the loop also visits that
same value as `arg`, and because it does not start with `--` it is silently consumed as
`output_dir` when no output dir was given — i.e. `python … coords.xyz --timeout-min 20`
sets `output_dir="20"`. `SECTION_READ`, a real argument-parsing bug (`:659-666`).

Runner: proper `argparse` (`:880-896`): `coords_file` (positional),
`output_dir` (positional, default `"output"`), `--production` (False),
`--timeout-min` (**30**), `--sample-tilt-validation` (False).

**Environment-variable overrides (identical in both, `:459-502` / `:690-734`)** — all
undocumented in the README: `HRTEM_PIXEL_SCALE` (multiplies advisory px),
`HRTEM_PIXEL_SIZE_A` (absolute px), `HRTEM_MAX_PIXEL_SIZE_A` (clamp),
`HRTEM_DZ_SCALE`, `HRTEM_DZ_A`, `HRTEM_Z_SUPERSAMPLING`, `HRTEM_MEMORY_SAFETY_FACTOR`
(default 2.0), `HRTEM_TARGET_MEM_GB`, `HRTEM_NUM_GPUS`, `HRTEM_GPU_STREAMS_PER_DEVICE`,
`HRTEM_GPU_BATCH_SIZE`, `HRTEM_GPU_TRANSFER_MODE`, `HRTEM_CPU_WORKERS`,
`HRTEM_CPU_WORKERS_WITH_GPU`. Also `OMP/MKL/NUMBA_NUM_THREADS` are forced to `'1'` at import
time (`:27-29` / `:22-24`), before `import prismatique`.

**The three physically significant divergences between the two copies:**

| | forward model | tilt runner |
|---|---|---|
| `interpolation_factors` | `(1, 1)` (`:421`) | **`(4, 4)`** (`:540`) |
| `max_data_size` | `8_000_000_000` with comment `# 2 GB` (`:317`) | `64_000_000_000`, comment `# 64 GB` (`:436`) |
| `hrtem.image.Params` kwargs | 5 valid kwargs (`:428-434`) | 5 valid **+ `save_probe_complex` + `wavefunction_z_planes`** (`:547-556`) |

Both divergences are defects; see §4 (Critical-1 and Critical-2).

**Shared numerical choices.** `atomic_potential_extent = 8.0` Å hard-coded
(`:266` / `:328`); `unit_cell_tiling = (1,1,1)`; `gun` `intrinsic_energy_spread = 0.5e-3`
keV (`:286` / `:348`); `lens` `coherent_aberrations=()`, `chromatic_aberration_coef=0.0`;
`postprocessing_seq=()`; `avg_num_electrons_per_postprocessed_image=1.0`;
`apply_shot_noise=False`; `save_potential_slices=False`;
`z_supersampling` default **4** (`:498` / `:730`); `dz` default **1.0 Å** (`:487` / `:718`);
`num_slices = ceil(Lz/dz)` (`:413` / `:532`).

`derive_grid_from_meta` (`:185-217` / `:234-266`): `g_raw = max(128, ceil(L/px))`, then
`_nearest_fft_friendly` searches ±5 %, ±10 %, ±20 % for the nearest integer that is
divisible by 4 **and** 2-3-5-smooth. Note the search returns the first span that yields any
candidate and prefers the *larger* of two equidistant candidates (`:205`/`:254`); it can and
does return a grid **coarser** than the advisory pixel despite the `ceil`.

### 1.4 `pipeline/specular_filter.py`

**Input**: one `.h5`. **Output directory**: `<out-prefix>_bragg_filter/` (`:494`), default
prefix = input basename without extension (`:492`).
**Files written** (`:531-743`): `kspace_mag_raw.png`, `notch.png`, `kspace_mag.png`,
`kspace_mag_marked.png`, `mask_hann.png`, `mask_hamming.png`, `amp_hann.png`,
`amp_hamming.png`, `phase_hann_wrapped.png`, `phase_hamming_wrapped.png`,
`phase_hann_flat.png`, `phase_hamming_flat.png`, `results_arrays.npz`, `results.h5`.

`results_arrays.npz` keys (`:722-727`): `amp_hann`, `phase_hann_wrapped`, `phase_hann_flat`,
`amp_hamming`, `phase_hamming_wrapped`, `phase_hamming_flat`, `mask_hann`, `mask_hamming`,
`mask_valid_hann`, `mask_valid_hamm`, `iy0`, `ix0`.
`results.h5`: groups `hann` / `hamming`, each with `amplitude`, `phase_wrapped`,
`phase_flat`, `mask_kspace`; a root attribute `meta` holding a JSON string (`:730-743`).
Note the README (line 39) advertises `/hann/amp` and `/hann/phase`; the code writes
`/hann/amplitude`, `/hann/phase_wrapped`, `/hann/phase_flat`. The README is wrong.

**CLI arguments and every default (`:453-472`):**

| Flag | Default |
|---|---|
| `input` (positional) | required |
| `--out-prefix` | `None` → input basename |
| `--dx` | **0.5** Å/px |
| `--dy` | **0.5** Å/px |
| `--pad` | **2** |
| `--tukey-alpha` | **0.3** |
| `--exclude-center` | **20** px |
| `--target-radius` | **None** (→ `1/target_d_A` if `--meta`) |
| `--meta` | **None** |
| `--ring-frac` | **0.03** |
| `--manual-peak` | **None** |
| `--rin` | **8** px |
| `--rout` | **14** px |
| `--no-unwrap` | **False** (unwrapping ON) |
| `--no-detrend` | **False** (plane removal ON) |
| `--notch-sigma-inv-A` | **0.04** cycles/Å |
| `--notch-order` | **4** |

Hard-coded: the 10 % amplitude threshold (`:617`, `:621-622`); the marker radius 6 px
(`:583`); the 99th-percentile display stretch (`:697`); the ±π display clip (`:708`).

### 1.5 `pipeline/step_height_reflection_formula.py`

No module docstring. **Inputs**: `--results-dir` (required, must contain
`results_arrays.npz`), `--meta` (required), `--output` (default
`"step_height_measurement_mesa.png"`). Reads only `data['phase_hann_flat']` (`:57`) — the
Hamming branch computed by the filter is never used. **Outputs**: one PNG plus stdout; **no
machine-readable output at all** — the measured height is printed, never saved.
Hard-coded: half-window `width = 10` (`:100`), row/column stride 5 (`:106`, `:118`),
histogram `bins=60` (`:150`), `find_peaks(height=0.1*max, distance=5)` (`:25`),
percentile fallback 10/90 (`:30`), default `a_Si=5.4309` (`:159`).

### 1.6 `pipeline/process_all_tilts.py` and `pipeline/hdf5_output_validator.py`

`process_all_tilts.py` takes **no arguments**. Everything is hard-coded:
`base_dir = abspath("../outputs/job_12198643")` (`:10`) — a specific HPC job id;
`filter_script = abspath("specular_666_filter.py")` (`:13`) — **a filename that no longer
exists**: commit `81f1af0` renamed it to `specular_filter.py` and the driver was not
updated. It globs `tilt_*` subdirectories (`:20`), expects
`hrtem_sim_wavefunction_output_of_subset_0.h5` in each (`:33`), reads
`advisory_pixel_size_A` from a sibling `meta.json` and passes it as **both** `--dx` and
`--dy` (`:48-52`, `:72-73`), defaulting to **0.5** if absent (`:41-42`), and writes into
`<tilt_dir>/filtered/specular_666_*`. It never passes `--meta`, so
`--target-radius` stays `None` and the filter falls back to "brightest peak anywhere outside
the central 40×40 px square" (§2d).

Note the directory layout mismatch: the runner puts **all** tilts in **one** output
directory as one HDF5 file with a tilt axis (`:787-788`), while `process_all_tilts.py`
expects **one directory per tilt**. The two are incompatible; `.gitignore:37-38` records
"both naming conventions the runner has emitted historically", confirming the layout changed.

`hdf5_output_validator.py` is 12 lines with a hard-coded absolute path on the author's
laptop (`:4`, `/Users/hussienballouk/Desktop/…`, including spaces and a `#` in the path).
It cannot run anywhere else. It prints top-level keys, `data` keys, and the shape/dtype of
`data/image_wavefunctions`. No assertions, no exit code.

### 1.7 Referenced-but-missing scripts

`docs/PIPELINE_LOG.md` names six artefacts that **do not exist** in the repository
(`REPRODUCED`: `git ls-files` lists 14 files, none of these):

| Named at | Name | Status in the doc |
|---|---|---|
| `PIPELINE_LOG.md:18` | `si100_slab_generator.py` | the sample source of the whole flowchart |
| `:53` | `batch_tilt_series_analysis.py` | `[BROKEN — see §4]` |
| `:58` | `measure_all_steps.py` | `[BROKEN — see §4]` |
| `:59-60` | `figure_tilt_series_v1/v2/v3.py` | — |
| `:60-61` | `figure_hologram_publication.py` | — |
| `:38` | `specular_666_filter.py` | renamed to `specular_filter.py` in `81f1af0` |

`si100_slab_generator.py` is additionally cited as the source of the "physics helpers" in
the Si[110] generator (`si110_cleave_slab_generator.py:17`). Both "§4" cross-references are
dangling: `docs/PIPELINE_LOG.md` has no §4 — commit `e61e545` deleted lines 64-119 of the
document, leaving it ending at line 66 with a stray `\`.

---

## 2. THE PHYSICAL MODEL AS ACTUALLY IMPLEMENTED

All numbers in this section were produced by running the repository's own generator with its
own defaults and by re-implementing prismatique 0.0.1's tilt selection from its source; the
exact commands are in §5. Label: `REPRODUCED` unless marked otherwise.

### 2a. Sample geometry

**The slab frame.** `slab_rotation_matrix()` (`si110_cleave_slab_generator.py:61-73`) returns
the matrix whose *rows* are the slab basis expressed in cubic crystal coordinates:

```
x̂ = [ 1,-1, 1]/√3   (surface normal, out of the crystal)
ŷ = [ 1,-1,-2]/√6   (in-plane, normal to the step edges)
ẑ = [ 1, 1, 0]/√2   (beam)
```

`REPRODUCED`: `R·Rᵀ − I` has max |element| = 2.2×10⁻¹⁶; `det R = +1.0000000000`;
`x̂ × ŷ = (0.70710678, 0.70710678, 0) = ẑ` exactly. **Orthonormal and right-handed — PASS.**
Crystallographically: `[1,-1,1]` is a `<111>` direction, so in a cubic crystal the facet is a
`{111}` plane; `[1,1,0]` is `<110>` and `[1,1,0]·[1,-1,1] = 0`, so **the beam lies exactly in
the surface plane** at zero tilt; `[1,-1,-2]·[1,-1,1] = 0` and `[1,-1,-2]·[1,1,0] = 0`.
The frame is internally consistent. The README's "(1,1,-1) facet" (line 3) versus its own
diagram's `[1,-1,1]` (line 13) is a documentation inconsistency only — the code uses
`[1,-1,1]` everywhere (`:70`, `:94`, `:378`). (`(1,1,-1)` and `(1,-1,1)` are different members
of the same `{111}` family; the beam `[110]` lies in `(1,-1,1)` but **not** in `(1,1,-1)`
(`[1,1,0]·[1,1,-1] = 2 ≠ 0`), so the README's statement is not merely a relabelling — it
names a plane that is incompatible with the stated beam direction.)

**Construction.** A cubic diamond cell (ASE `bulk("Si","diamond",a,cubic=True)`, `:137`) is
repeated `n_cubic³` times with `n_cubic = ceil(√(Lx²+Ly²+Lz²)/a) + 2 = 45` for the defaults,
centred (`:140-141`), rotated into the slab frame by `positions @ R.T` (`:145`), and trimmed.

**The "terrace_heights_A" shave construction (`:152-218`).** The code folds the surviving
x-coordinates modulo `d_111 = a/√3` (`:174`), histograms them into 200 bins (`:177`), takes
the two tallest bins as the two sub-planes of a bilayer (`:180-181`), puts `narrow_mid` at
their midpoint and `wide_mid` half a `d_111` away (`:184-185`), then places the cut plane
`x_top_high` at the first `wide_mid` above the topmost atom (`:193-196`). Terrace *i* is
everything with `y` in the *i*-th of N equal-width bins, kept below
`x_top_high − terrace_heights_A[i]` (`:209-213`).

`REPRODUCED` — **this construction is correct.** For the flat default slab the x-coordinates
form 58 discrete `(1,-1,1)` planes whose gaps take exactly two values:
**0.78388 Å = d₁₁₁/4** (inside a bilayer) and **2.35165 Å = 3·d₁₁₁/4** (between bilayers),
summing to `d₁₁₁ = 3.135532 Å`. With `--create-step` (defaults, 4 terraces, 0/1/2/3 bilayers)
the measured surface heights are

| terrace | y-range (Å) | x_top (Å) | step vs terrace 0 (Å) | /d₁₁₁ | requested (Å) | error (Å) |
|---|---|---|---|---|---|---|
| 0 | 0.000–19.954 | 97.01100 | 0 | 0 | 0 | 0 |
| 1 | 19.954–39.909 | 93.87547 | 3.13553 | 1.00000 | 3.135532 | < 1e-5 |
| 2 | 39.909–59.863 | 90.73994 | 6.27106 | 2.00000 | 6.271063 | < 1e-5 |
| 3 | 59.863–79.818 | 87.60441 | 9.40659 | 3.00000 | 9.406595 | < 1e-5 |

**The step heights are exact integer multiples of d₁₁₁ to better than 10⁻⁵ Å**, every cut
plane falls in a **wide** (2.35165 Å) gap, and **no half-bilayers are produced**: each terrace
terminates on a complete bilayer with one dangling bond per surface atom — the standard ideal
Si(111) termination. The lattice is continuous across the steps: the upper-terrace planes
(97.011, 96.227, 93.875, …) are drawn from the *same* plane ladder as the lower terraces, so
the upper terrace is the same infinite lattice truncated higher — **not** a displaced block.
This distinction matters for the step-phase model (§2e). The `--terrace-heights-bilayers`
help text (`:274-278`) correctly predicts the resulting phases for (2,−2,0):
`Δφ = 2π·g·(h n̂) = 2π·(4m/3)` → 0, 2π/3, 4π/3, 2π for m = 0,1,2,3 — `DERIVED_HERE` and
consistent with the code's own comment. Note that terrace 3 therefore produces a phase step
that is **indistinguishable from zero**, which the help text flags ("wraps") but nothing in
the pipeline guards against.

**Actual cell and vacuum (defaults).** `REPRODUCED`:

```
cell line in the .xyz : Lx = 104.659353  Ly = 79.817603  Lz = 198.248144  Å   (matches meta box_A exactly)
atoms                 : 49357 (flat) / 46805 (4-terrace staircase) / 47628 (2-terrace 0,2)
all Z = 14, occ = 1.000, sigma = 0.076 for every atom
atom extent  x : 8.43223 … 97.01100 Å      y : 0 … 79.81760 Å      z : 31.92011 … 168.24814 Å
atoms outside the declared cell : 0
```

The declared and the realised geometry **disagree**:

| quantity | `meta.json` says | actually built | error |
|---|---|---|---|
| vacuum above the surface | `x_vacuum_A = 10.000` | **7.6484 Å** | −23.5 % |
| vacuum below the back face | `x_vacuum_A = 10.000` | **8.4322 Å** | −15.7 % |
| Si thickness along x | `Lx_si_A = 84.6594` | **88.5788 Å** | +3.9194 Å |
| Si length along the beam | `Lz_si_A = 138.2481` | **136.3280 Å** | −1.9201 Å (= period_z/2) |
| vacuum along z | `z_vacuum_A = 30.000` | front **31.9201**, back **30.0000** | asymmetric |

The cause is `:196` / `:204`: `x_top_high` and `x_back` are pushed outward from the extreme
*atoms* by up to a full `d₁₁₁` each, so the Si band grows beyond `Lx_si` while `Lx` stays
`Lx_si + 2·x_vac`. Nothing downstream ever learns the true surface position: the generator
computes `x_top_high_A`, `x_back_A` and `terrace_x_top_A` in `build_si110_step_slab`'s return
dict (`:232-234`) but **`main()` never copies them into `meta.json`** (`:368-414`).

**Boundary conditions — this is a thin plate, not a semi-infinite crystal.**
The Si slab is 88.58 Å thick along its own surface normal with vacuum on **both** faces, and
the cell is periodic in **all three** directions (`:225 big.set_pbc((True,True,True))`;
Prismatic is periodic in x and y by construction). The gap between a slab and its periodic
image *along the surface normal* is 7.648 + 8.432 = **16.081 Å** (atom centre to atom centre).
With the hard-coded `atomic_potential_extent = 8.0 Å` (`multislice_forward_model.py:266`,
runner `:328`) the projected potential of the topmost surface atoms reaches
97.011 + 8.0 = 105.011 Å > Lx = 104.659 Å and **wraps by 0.35 Å into the next image's
back-face vacuum**. More importantly, any flux scattered away from the surface re-enters
through the opposite face: there is no absorber (the `absorbing_layers` keyword is silently
discarded — sibling report §3.1a, independently confirmed here against
`prismatique/sample.py:123-134`, whose `ModelParams.__init__` accepts only
`atomic_coords_filename, unit_cell_tiling, discretization_params, atomic_potential_extent,
thermal_params, skip_validation_and_conversion`).

**Beam footprint at glancing incidence (`DERIVED_HERE`, ray geometry only).**
At glancing angle θ measured from the surface plane (here θ = θ_x, because x̂ is the outward
normal), a ray starting a height Δx above the surface meets the surface after Δx/tan θ of
propagation along z. The slab spans only L_slab = 136.328 Å of the beam path (the cell is
198.248 Å, of which 31.92 Å in front and 30.00 Å behind are vacuum). Hence only rays with
Δx ≤ L·tan θ ever touch the surface:

| θ | Δx_max, L = L_slab = 136.328 Å | fraction of the 7.648 Å above-surface vacuum | fraction of the whole 104.659 Å cell |
|---|---|---|---|
| 5.000 mrad | 0.682 Å | 8.91 % | 0.651 % |
| 6.531 mrad (θ_B of (2,−2,0)) | 0.890 Å | 11.64 % | 0.851 % |
| **8.000 mrad** | **1.091 Å** | **14.26 %** | **1.042 %** |
| 11.000 mrad | 1.500 Å | 19.61 % | 1.433 % |
| **24.000 mrad** | **3.273 Å** | **42.79 %** | **3.127 %** |

(Using the *nominal* 10 Å vacuum instead of the realised 7.648 Å the vacuum fractions become
10.91 % at 8 mrad and 32.73 % at 24 mrad. Using the whole cell length L = Lz = 198.248 Å —
i.e. allowing the ray to reach the surface anywhere, including outside the slab — gives
20.74 % and 62.22 % of the vacuum, 1.515 % and 4.547 % of the cell.)

**Conversely, the fraction of the incident plane wave that starts inside the crystal.**
Prismatic's HRTEM illumination is one Fourier component of the grid set to 1
(`PRISM02_calcSMatrix.cpp:391`, sibling §2c), i.e. a plane wave filling the entire periodic
cell. At the slab's entrance face (z = 31.92 Å) the crystal occupies x ∈ (8.432, 97.011) Å, so

* **84.64 %** of the incident wavefront enters the crystal **head-on, through a face
  perpendicular to the beam** — a transmission problem through ≈ 136 Å of Si along [110];
* 7.31 % is in the vacuum above the surface;
* 8.06 % is in the vacuum below the back face.

At 8 mrad only **1.04 %** of the full incident wavefront reaches the surface from the vacuum
side inside the slab; at 24 mrad only **3.13 %**. **This is a transmission simulation of a
thin plate with a ≈1–3 % grazing sliver, not a reflection simulation.** It is not
"reflection-mode" in the sense of [B07]/[P01]: there is no semi-infinite crystal, no
surface-normal boundary condition, and the overwhelming majority of the recorded wave has
travelled *through* the plate. Whether the ≈1 % grazing component nevertheless carries a
usable surface signal is not settled by this audit — but it is not the quantity the pipeline
extracts, because the filter integrates over the whole field of view (§2d).

**Periodicity defect in y.** `REPRODUCED`: `y.min() = 0` **exactly** and `y.max() = Ly`
**exactly**; 193 atoms sit at y = 0 and 172 at y = Ly, and the gap across the periodic
boundary is **0.000000 Å** where it should be one interplanar spacing (1.10858 Å). The cut at
`:214` is `(y > -Ly/2) & (y < Ly/2)`, i.e. strict on *both* ends, but floating-point rounding
lets atoms within ~1 ULP of −Ly/2 through while rejecting a different subset near +Ly/2 — the
two boundary planes are the *same* plane under PBC, so ≈193 atoms are **double-counted** and
the y-ladder has a duplicated, unevenly populated plane exactly at y = 0. That defect is a
line of anomalous projected potential running **parallel to the beam at a fixed y** — i.e.
geometrically identical to a step edge, in the very coordinate in which the step heights are
measured. 0.39 % of the atoms, but coherent and at a fixed position.

**z-flip (Prismatic writes z' = ΔZ − z, sibling §2g).** `REPRODUCED` with a KD-tree: after
the mirror, a rigid shift of +3.8402 Å along z brings **97.41 %** of the atoms onto original
lattice sites to within 10⁻⁵ Å (the remainder are the two end planes and the surface). So for
*this* orientation the mirror ⊥[110] is a symmetry of the diamond lattice and the z-flip is
**structurally benign**; its only effect is to translate the slab by ≈1.92 Å along the beam
inside the cell (changing how much free space precedes and follows it, and hence the relation
of the saved mid-plane wave to the exit surface). This **refines** the sibling's caution: the
z-flip is not a structural error here, but it would be for a non-mirror-symmetric orientation,
and nothing in the repository checks it.

### 2b. Energy, wavelength, Bragg angle, tilt

**Beam energy** is 200.0 keV by default, written to `meta["energy_keV"]` and read by both
forward-model scripts (`:480` / `:711`) and by the step-height script (`:67`,
`meta.get('energy_keV', 200.0)` — a silent default, §4).

**Three wavelength formulas exist in the repository.** `REPRODUCED`:

| Where | Formula | λ(200 keV), Å |
|---|---|---|
| `si110_cleave_slab_generator.py:19-25` | `hc/√(E(E+2m₀c²))`, `h=4.135667696e-15` eV·s, `m₀c²=510.99895` keV | **0.025079340** |
| `multislice_forward_model.py:220-228`, `multislice_tilt_series_runner.py:269-277`, `step_height_reflection_formula.py:9-17` | `h/√(2m₀V(1+V/2m₀c²))`, `h=6.62607015e-34`, `m₀=9.10938356e-31` | **0.025079341** |
| `multislice_tilt_series_runner.py:381` (tilt snapping only) | `12.2643/√(V(1+0.978476e-6 V))` | **0.025079422** |
| (embeam 0.0.1, what the engine actually uses; `embeam/constants.py:39-97`, `h=6.62607e-34`, `m_e=9.109383e-31`, `e=1.602177e-19`) | same as row 2 with rounded constants | **0.025079337** |

The first two are algebraically identical and differ only through the constants:
**−1.69×10⁻¹⁰ Å = −1×10⁻⁶ %** at 200 keV, and the resulting Bragg angles differ by
4.4×10⁻⁸ mrad. **So the "two wavelength formulas" issue is a maintainability defect, not a
numerical one** — I state this explicitly because it would be easy to over-claim. The
*third* formula (the 1970s-textbook fit at `:381`) is off by **+3.25×10⁻⁴ %**; that is also
physically negligible, but it is enough to break prismatique's exact-float tilt-weight test
(sibling §3.4), which is why it matters at all. `m₀ = 9.10938356e-31` kg is the CODATA-2014
value (CODATA-2018 is 9.1093837015e-31); nothing in the repository names a constants source,
contrary to instruction §9.8.

**Bragg-angle helper** `bragg_angle_mrad` (`:28-35`): `d = a/√(h²+k²+l²)`,
`θ_B = asin(λ/2d)·1000`. It returns **0.0** when `λ/2d > 1` (`:33-34`) instead of raising —
a silent failure mode. For the default `(2,−2,0)`: d = 1.9201131 Å, θ_B = **6.530740 mrad**;
`λ|g| = 13.0614 mrad = 2θ_B` ✓.

**`alpha_deg`, `tilt_mrad`, `target_theta_B_mrad` — are they consistent?**

* `alpha_deg` is written by the generator (`:405`) as `target_theta_B_mrad·180/π/1000`, i.e.
  **the Bragg angle expressed in degrees** — 0.374184° for (2,−2,0).
* Both forward-model scripts read `alpha_deg` (`:481` / `:712`) with the comment
  *"geometry already applied in coords"* and use it only for printing and for
  `theta_max_deg = 1.3·alpha_deg` (`:482` / `:713`), which is itself never used.
* `quick_phase_report` (`:231-246` / `:280-295`) reads `alpha_deg`, calls it `θ_B` in the
  printout, and evaluates `Δφ = 2·(2π/λ)·sin(α)·d₁₁₁` — the **specular** two-beam step phase
  with `d₁₁₁` as the height and `ĝ·n̂ = 1` implied. That is a *different* formula from the one
  the step-height script uses, applied to a *different* reflection. Neither is labelled.
  Additionally it needs `meta["d111_A"]`, which the generator never writes, so it falls back
  to `a/√3` (`:237` / `:286`).
* `step_height_reflection_formula.py:70-75` prefers `target_theta_B_mrad` and falls back to
  `alpha_deg`; when **both** are missing it uses `alpha_deg = 0.0` → `sin θ = 0` → division by
  zero, guarded only by `if denom != 0.0` (`:156`) which returns `NaN` silently.
* `meta_tilt_examples.json` sets `alpha_deg = 1.375` in all four examples — that is
  θ_B(6,6,6) = 23.9976 mrad = 1.37497°, i.e. **the examples describe a different reflection
  from the generator's default**, and they also label the structure `"Diamond Cubic (100)"`
  while the facet is `{111}`-type.

So `alpha_deg` means "Bragg angle in degrees" everywhere it is *written*, but it is *read* as
a grazing/incidence angle in `quick_phase_report` and as a fallback Bragg angle in the
step-height script. It is **not** the beam tilt: the tilt sweep is a separate set of keys
(`tilt_start/end/step_mrad` or `tilt_angles_mrad`) in mrad. Units are consistently mrad for
tilts and degrees for `alpha_deg`; no factor-1000 error was found.

**The tilt implementation (`multislice_tilt_series_runner.py:360-421`).**
`parse_tilt_angles` (`:154-191`) builds a *list* of scalar magnitudes. Then
`create_system_params` takes only `min`, `max` and the midpoint (`:370-373`):
`center_tilt = (min+max)/2`, `radial_span = max−min`. The **magnitude** is snapped to the
x-grid step `λ/Lx` (`:384-389`) using the third wavelength formula, and only then decomposed
into components with the azimuth (`:399-401`):
`offset = (|θ|cos az, |θ|sin az)`, `window = [0, span/2 + 0.1]`, `spread = 0` (`:402-406`).

Three consequences, all `REPRODUCED` by re-implementing
`prismatique.tilt._series` / `sample._angular_mesh_and_beam_mask` from the 0.0.1 source:

1. **`--tilt-step` / `tilt_step_mrad` has no effect whatsoever.** Only `min` and `max` reach
   prismatique. The window selects *every* grid point inside a disc.
2. **The snapping is undone by the azimuth.** Snapping the magnitude to the x-grid and then
   multiplying by cos/sin lands off-grid in both components (the grids differ: λ/Lx vs λ/Ly).
3. With the repository's own defaults (advisory px 0.5 Å, sweep 0→11 mrad step 0.15,
   azimuth 35.264°, and the runner's `interpolation_factors=(4,4)`):

```
74 requested angles;  centre 5.475 -> snapped 5.511468 mrad (x-grid step 0.239629 mrad)
offset = (4.5001, 3.1820) mrad ; window = [0, 5.575] mrad
tilt grid step with f=(4,4) : (0.95851, 1.25683) mrad
SIMULATED tilts = 80        (would be 1295 with interpolation_factors=(1,1))
tilt_series[0]  = (-0.95851, +2.51366) mrad   <-- the slice specular_filter.py reads
nearest grid tilt to the requested offset = index 42 = (4.79256, 3.77050) mrad, |err| = 0.657 mrad
theta_x range [-0.9585, 9.5851] ; theta_y range [-1.2568, 7.5410] mrad
```

The residual 0.657 mrad is **10 % of θ_B** — a large excitation error, not a rounding detail.
And `specular_filter.py`'s `[0,0,0,:,:]` reads θ = (−0.959, +2.514) mrad, not the intended
(4.500, 3.182). This confirms and refines the sibling's §3.4 (they used azimuth 0 and
`f=(1,1)`, obtaining 1309 tilts and slice 0 = (0, −0.943); with the runner's *actual*
`f=(4,4)` and the meta azimuth the numbers are 80 tilts and slice 0 = (−0.959, +2.514)).

**Sign of the tilt.** θ_x = +λq_x (engine and wrapper, sibling §2c), and +x̂ is the **outward**
surface normal. A *positive* θ_x therefore makes the beam climb **away from** the surface.
The runner always forms `offset_kx = |θ|·cos(az)` with `|θ| > 0` and, for the default
`(2,−2,0)`, `az = +35.264°` → `cos az > 0` → **the requested illumination is always tilted
away from the surface**, which also means it excites −g rather than +g. Nothing in the
repository states which sense is intended, and no test covers it. `UNVERIFIED` (intent);
`REPRODUCED` (the code's behaviour).

**Target reflection and the "666" legacy.** The generator's default is `[2,-2,0]` (`:283`),
which is **allowed**: all-even with h+k+l = 0, divisible by 4 → |F| = 8f. `DERIVED_HERE`
(standard diamond structure factor `F = f·F_fcc·(1+e^{iπ(h+k+l)/2})`; all-even with
h+k+l ≡ 2 mod 4 gives F = 0). For **(6,6,6)**: all even, h+k+l = 18, 18 mod 4 = 2 →
**|F| = 0, kinematically forbidden**, exactly as the initial commit message states. (Within
the independent-atom, spherical-potential approximation that Prismatic uses, (666) is
identically zero; whether a weak "forbidden" (666) exists in real Si through bonding-charge
asymmetry, as is known for (222), is a literature question I did **not** verify — `UNVERIFIED`.)
Nevertheless the repository still points at (666) in three places:
`process_all_tilts.py:13` calls `specular_666_filter.py` and `:65` names outputs
`specular_666`; `docs/PIPELINE_LOG.md:38` names `specular_666_filter.py`; and all four
`meta_tilt_examples.json` blocks carry `alpha_deg = 1.375` with example 3 labelled
*"for 666 Bragg condition"*. **There is no structure-factor check anywhere in the
repository** — `bragg_angle_mrad` only computes `d` from `√(h²+k²+l²)` and will happily hand
back θ_B for a forbidden reflection.

A further geometric point the code does not handle: `target_g_azimuth_deg` (`:76-84`)
projects `g` onto the slab (x,y) plane and returns `atan2(g_y, g_x)`. For `(2,−2,0)`,
`g·B = 0` so `g` is purely transverse and the projection is exact; and then
`cos(azimuth) = |ĝ·n̂| = √(2/3) = 0.816497` identically. For `(6,6,6)` or `(1,1,1)`,
`g·[110] = 12` and `2` respectively — `g` has a **component along the beam**, the azimuth is
only a projection, and `cos(az) = 0.5774 ≠ |ĝ·n̂| = 0.3333`. A pure transverse beam tilt
cannot reach the Bragg condition for such a `g` in the way the code assumes. `REPRODUCED`.

### 2c. Multislice parameters actually passed to prismatique

| Parameter | Forward model | Tilt runner | Source |
|---|---|---|---|
| grid `Ñ` | `(gx//4, gy//4)` | same | `:418` / `:537` |
| `interpolation_factors` | **(1,1)** | **(4,4)** | `:421` / `:540` |
| ⇒ actual potential grid `N = 4·f·Ñ` | `(216, 160)` | **(864, 640)** | `prismatique/sample.py:2366` |
| ⇒ actual potential pixel | (0.4845, 0.4989) Å | **(0.1211, 0.1247) Å** | |
| ⇒ HRTEM image pixel (= 2×) | (0.9691, 0.9977) Å | **(0.2423, 0.2494) Å** | |
| `num_slices` | `ceil(Lz/dz)` = **199** | same | `:413` / `:532` |
| slice thickness `dz` | `meta["advisory_dz_A"]` → **1.0 Å** (never in meta) | same | `:487` / `:718` |
| `z_supersampling` | `meta["z_supersampling"]` → **4** (never in meta) | same | `:498` / `:730` |
| `atomic_potential_extent` | **8.0 Å** hard-coded | same | `:266` / `:328` |
| `unit_cell_tiling` | (1,1,1) | same | `:259` / `:321` |
| `thermal_params` | **never passed** | **never passed** | — |
| `objective_aperture_params` | **never passed** | **never passed** | — |
| `tilt_params` | **never passed** (→ offset (0,0), window (0,0): one on-axis tilt) | `offset`, `window`, `spread=0` | `:298-303` / `:402-406` |
| `save_wavefunctions` | True | **requested True but the call fails — §4 Critical-2** | `:432` / `:551` |
| `save_final_intensity` | True | False (requested) | `:433` / `:552` |
| `save_potential_slices` | False | False | `:320` / `:439` |
| `max_data_size` | 8e9 (comment says "2 GB") | 6.4e10 | `:317` / `:436` |
| GPU/CPU | `worker.cpu.Params(enable_workers=True, num_worker_threads=N, batch_size=max(1, N//4 or 1))`, `worker.gpu.Params(num_gpus=detected, batch_size=1, data_transfer_mode="auto", num_streams_per_gpu=1)`; every failure swallowed by `except` → `worker_params=None` | identical | `:325-386` / `:444-505` |

**The `(1,1)` vs `(4,4)` divergence is a defect in both directions.** With `(4,4)` the runner
silently simulates a grid **16× larger in pixel count** than the "Grid (effective): 216 × 160"
it prints at `:737`, at a real pixel of 0.121 Å instead of the 0.5 Å the user asked for — a
~16–20× cost increase that is invisible in the log. With `(1,1)` the forward model's
anti-aliased band is only |k_x| ≤ 1/(4Δx) = 0.51596 cyc/Å, and the (2,−2,0) beam diffracted
from a beam tilted to the runner's own offset lands at k = (0.6047, 0.4276) cyc/Å — **outside
the band, i.e. removed by Prismatic's anti-aliasing mask** (`REPRODUCED`). At the generator's
default 0.5 Å pixel the *forward model* therefore cannot represent the target reflection at
all once the beam is tilted; the runner's unintended `(4,4)` is what rescues it.

**Thermal effects are never enabled.** The generator writes `enable_thermal_effects`,
`num_frozen_phonon_configs_per_subset` and `thermal_sigma_A` into `meta.json` (`:408-413`),
and writes σ = 0.076 Å into every `.xyz` row (`:55`), but **no script reads any of them** —
`grep` finds no `thermal_params` anywhere in `pipeline/`. The σ column is inert without
`thermal.Params`. `REPRODUCED` (sibling §2d, independently confirmed by grep here).

### 2d. The "reconstruction": `specular_filter.py`, step by step

1. **Loader** `load_complex_h5` (`:80-161`). Tries `data/image_wavefunctions` →
   `_pick_first_2d_slice` = `dset[(0,)*(ndim-2) + (slice(None),slice(None))]`, i.e.
   **`[0,0,0,:,:]`** for the 5-D prismatique array (`:61-77`, `:105-111`). Then `psi`,
   then `amplitude`+`phase`, then a `visititems` fallback that takes the *first* complex
   dataset sorted by "shallowest path, name containing 'wave' first" (`:129-156`). It never
   reads `/metadata/r_x`, `/metadata/r_y`, `/metadata/tilts`, `/metadata/defocii`, and never
   checks `dset.attrs["dim N"]`. Dead/broken code at `:152-155`: `_pick_first_2d_slice(psi)`
   is called on a **numpy array**, which works only because `ndarray` also supports
   `.ndim`/indexing, and its result is then immediately overwritten by a re-implementation of
   the same slice.
2. **Apodisation** `psi0 * tukey2d(Ny,Nx,alpha=0.3)` (`:510-511`, `:163-186`). The Tukey
   taper is applied in **real space to the wave itself**, before any transform. With
   α = 0.3 the outer 15 % of each edge is tapered — i.e. **≈ 28 % of the field of view is
   amplitude-modulated**, including the terraces near y = 0 and y = Ly.
3. **Zero-padding** by `--pad 2`: `pad_y = Ny·(pad−1)//2` each side (`:514-517`), so the array
   doubles in each dimension. Padding a *complex wave* with zeros is a hard aperture in real
   space; combined with step 2 it defines the effective window.
4. **FFT** `Psi = fftshift(fft2(psi_pad))` (`:523`) — unnormalised forward transform, DC moved
   to index `(Ny2//2, Nx2//2)`. **k axes** `fftshift(fftfreq(n, d=dx))` (`:383-397`), i.e.
   **cycles/Å, not angular wavevector** — no 2π. The axes use `--dx/--dy`, which
   `process_all_tilts.py:48-52` fills from `meta["advisory_pixel_size_A"]`. That is the
   *potential* pixel target, **not** the image pixel, which is 2× the *achieved* potential
   pixel. `REPRODUCED`: with advisory 0.13 the true image pixel is 0.26165 Å, a ratio of
   **2.013**; with advisory 0.5 (and `f=(1,1)`) it is 0.96907 Å, ratio 1.938.
5. **(000) notch** (`:540-548`): `notch = 1 − exp(−(K/σ)^{2n})` with σ = 0.04 cycles/Å, n = 4.
   Applied multiplicatively to `Psi`. This is a numerical beam stop applied in the *image*
   Fourier plane of the *simulated complex wave*; the docstring itself admits
   *"I do not know the limitations"* (`:17`).
6. **Peak finding** `find_peak` (`:334-381`). It zeroes a **square** of half-width
   `exclude_center_px = 20` around DC (`:368-369` — the docstring calls it a "radius"), and,
   if `target_radius` is given, keeps only the annulus `| |k| − r | ≤ 0.03 r` (`:372-375`).
   It then takes **`argmax` of |Psi|** in what survives. So: **the strongest peak on a ring of
   radius 1/d_target — the g azimuth is never used.** `tilt_azimuth_deg` and
   `target_hkl` are in `meta.json` and are ignored; only `target_d_A` is read (`:481-483`).
   If `--meta` is not given (and `process_all_tilts.py` never gives it, `:67-74`) then
   `target_radius = None` and the filter takes **the brightest pixel anywhere outside the
   central 40×40 px square**.
   **The ring radius is geometrically wrong for any tilted beam.** `REPRODUCED`: the spots of
   ψ_exit sit at `k_in + g`, not at `g`. At zero tilt |k_in+g| = 0.52080 = 1/d ✓; at the
   runner's own offset |k_in+g| = 0.74056 (outside the ±3 % ring); in the symmetric Bragg
   setting |k_in+g| = |g|/2 = 0.26040 (also outside). **Two errors nearly cancel**: because
   the k axis is stretched by ≈2.013 (step 4), a feature the filter *reports* at 0.52080 is
   physically at 0.25876 cyc/Å — within **0.63 %** of the symmetric-Bragg position 0.26040, i.e.
   inside the ±3 % ring. So in the symmetric setting the pipeline finds the right spot **for
   the wrong reason**, and any change to either bug alone breaks it.
7. **Mask and demodulation** `reconstruct_for_window` (`:399-450`): a raised-cosine disk
   (`:188-243`), 1 inside `rin = 8 px`, tapering to 0 at `rout = 14 px`, centred on the found
   peak; multiply; then `np.roll` the whole array by `(cy−iy0, cx−ix0)` to put the peak at DC
   (`:437-443`); then `ifft2(ifftshift(...))` (`:448`). The roll is **circular**, so any mask
   content that crosses the array edge wraps to the opposite side — a real wraparound risk
   that nothing checks. The radii are in **pixels of the padded grid**, so their physical
   meaning depends on `pad`, `dx` and the array size: with the 800×600 image, pad 2 and
   dx = 0.13, Δk = 1/(1600·0.13) = 0.004808 cyc/Å, so rin = 8 px = 0.03846 cyc/Å → a
   real-space resolution limit of ≈26 Å; with `--dx 0.5` the same 8 px is 0.01 cyc/Å → ≈100 Å.
   **The aperture is never specified in physical units and silently rescales with `--dx`.**
   No normalisation by the mask area is applied, so the reconstructed amplitude is not
   comparable between runs.
8. **Phase** `np.angle(psi_rec)` (`:596`, `:601`); validity mask `amp > 0.1·amp.max()`
   (`:621-624`); unwrapping `unwrap2d = np.unwrap(np.unwrap(φ, axis=0), axis=1)` (`:259-269`)
   — a naive row-then-column 1-D unwrap, **not** a 2-D (residue/quality-guided) algorithm, and
   it is applied to `np.where(mask_valid, φ, 0)` (`:635`), which injects **zeros** at invalid
   pixels and therefore corrupts the unwrap path wherever it crosses a masked region.
9. **Ramp removal** (`:646-688`): a least-squares plane `a·x + b·y + c` fitted over the valid
   pixels and subtracted. **This is on by default.** For a monotonic staircase (the
   generator's own default test object) the step signal *is* largely a linear ramp in y, so
   the default processing removes most of the quantity being measured. The module also
   contains an unused duplicate `detrend_plane` (`:271-290`) that fits over *all* pixels.
10. **Outputs**: §1.4. The **raw (pre-processing) phase is never saved** — only
    `phase_*_wrapped` (post-mask, post-notch, post-demodulation) and `phase_*_flat`. The
    fitted plane coefficients *are* saved into the `meta` JSON attribute (`:680`, `:684`).

**Is an intensity hologram ever formed? No.** `grep` over the whole repository finds no
`|u_obj + u_ref|²`, no addition of two fields, and no reference branch: the only `abs()` calls
on a wave are `np.abs(Psi)` for peak finding (`:354`), `np.abs(psi_hann/psi_hamm)` for display
(`:595`, `:600`) and `np.log1p(np.abs(Psi))` for the PNGs. **Is there a reference wave
anywhere? No.** There is no biprism model, no second branch, no carrier generation, no
`u_ref` of any kind in any of the 3058 lines. The pipeline's "phase" is
`np.angle(IFFT(mask·FFT(w(r)·ψ_sim)))` — **the argument of a band-pass-filtered, apodised,
demodulated copy of the simulated complex wave**. Instruction §9.1 is therefore **violated as
described**: the operation is complex-wave selection, presented throughout (README line 1
"off-axis electron-holographic reconstruction"; README line 34 "Sideband isolation";
`specular_filter.py:8` "virtual dark-field"; README citation 7 "off-axis electron holography
reconstruction … implemented in `specular_filter.py`") as hologram reconstruction.

### 2e. The step-height script

**Formula** (`:152-156`): `h = Δφ·λ / (4π·sin θ_B·(ĝ·n̂))`, matching README line 42 and
instruction §9.7. `DERIVED_HERE`: substituting `sin θ_B = λ|g|/2` gives
`h = Δφ / (2π·|g|·(ĝ·n̂)) = Δφ / (2π·g·n̂)`, i.e. the formula is exactly the kinematic
"scattering-vector · displacement" relation `Δφ = Q·u` with `Q = 2πg` and `u = h n̂`. It is
therefore valid for a rigid *displacement* of one terrace by `h n̂` at the exact Bragg
condition, in single scattering. **The generator does not build a displaced terrace** — it
truncates one continuous lattice at two heights (§2a) — and the geometry is not a specular
surface reflection, so the applicability of this expression here is exactly the open question
instruction §9.7 raises. It is **not** the RHEED/specular relation `Δφ = (4π/λ)h sin θ_graze`,
which the code's own `quick_phase_report` (`:231-246`) uses with a *different* angle and
without the `ĝ·n̂` factor. The two coexisting formulas are never reconciled.

**Where the variables come from (`:67-83`):**

| symbol | source | silent default |
|---|---|---|
| `E_keV` | `meta['energy_keV']` | **200.0** (`:67`) |
| `θ_B` | `meta['target_theta_B_mrad']` (preferred) | else `meta['alpha_deg']`, else **0.0** (`:74`) → `sin θ = 0` |
| `ĝ·n̂` | `meta['g_dot_n_surf']` | **1.0** (`:81`) |
| `λ` | computed from `E_keV` by its own formula (`:83`) | — |
| `h_theo` | `meta['step_height_A']` | else `a/√3` with `a` from `meta['a_A']` default **5.4309** (`:159-160`) |

Three of the five silently substitute a plausible value for missing measured metadata —
precisely what instruction §9.7 forbids for a quantitative result. Worst is `alpha_deg = 0.0`:
`denom = 0` → the `if denom != 0.0` guard (`:156`) returns `float('nan')` **with no message**,
and the script then prints `Calculated Step Height: nan A` and carries on to plot.
Note also `h_theo = float(meta.get('step_height_A') or a/√3)` (`:160`): because the generator
writes `step_height_A = 0.0` for a flat slab and `0.0` is falsy, **the no-step control case
silently reports a theoretical step of 3.136 Å instead of 0**.

**Terrace identification (`:98-150`).** Slides a ±10-row (or ±10-column) box in strides of 5
over the phase map, takes `np.nanmean` along the box, drops non-finite entries, and keeps the
profile of **highest variance** (`:106-125`); whichever of the two directions has the larger
variance wins (`:132-141`). Then `find_dominant_levels` (`:19-39`) histograms that one profile
into 60 bins with `density=True`, runs `scipy.signal.find_peaks(hist, height=0.1·max(hist),
distance=5)`, takes the two tallest peaks, and returns `(min, max)` of their bin centres;
if fewer than two peaks are found it prints a warning and returns the **10th and 90th
percentiles** (`:27-30`).

Consequences:
* `Δφ = level_high − level_low` (`:151`) is **forced non-negative** by the `min/max` at `:39`
  — the **sign of the step is destroyed**, so a down-step and an up-step are indistinguishable
  and `h` is always ≥ 0. Instruction §9.7 asks explicitly for signed differences.
* With **no step** the profile is unimodal, `find_peaks` finds one peak, and the percentile
  fallback returns P10 and P90 of the noise — a **non-zero** "step height" is reported for a
  flat surface, with only a printed warning.
* With **more than two** terraces (the generator's own default is four) only the two tallest
  histogram peaks are used; the result is the difference between two arbitrary terraces, not a
  step height. Nothing detects this.
* Because `phase_hann_flat` has already had a plane subtracted (§2d step 9), a monotonic
  staircase is largely flattened before it arrives.
* **No uncertainty of any kind is reported** — no fit residual, no level widths, no
  propagation of the θ_B or λ uncertainty, no ±. The script prints six numbers and a PNG.
* The profile is `phase_flat[best_y-10:best_y+10, :]` averaged (`:135`) — this averages
  **across** the step when the step runs along y, and the subsequent `profile[np.isfinite]`
  (`:143`) **silently re-indexes** the profile, so the plotted x-axis no longer corresponds to
  real-space position.

### 2f. Ensemble handling in the repository's own code

* The generator writes `num_frozen_phonon_configs_per_subset` and `num_subsets = 1`
  (`:412-413`); **no script reads them**.
* No script ever passes `thermal_params`, so prismatique produces exactly one configuration.
* `specular_filter.py` takes `[0, 0, 0, :, :]`: config index 0, defocus index 0, **tilt index
  0** (`:61-77`). Any additional configurations, defoci or tilts present in the file are
  discarded without comment.
* `process_all_tilts.py:33` reads only `hrtem_sim_wavefunction_output_of_subset_**0**.h5`;
  further subsets are never opened.
* Nothing anywhere performs an intensity average, and nothing distinguishes a coherent
  realisation from an ensemble average. Instruction §9.5's "do not silently discard ensemble
  axes" is violated by construction — but note that with the current parameters the discarded
  axes are of length 1 except the tilt axis, which is the one that matters (§2b).

---

## 3. CHECKLIST AGAINST INSTRUCTION SECTION 9

| § | Requirement | Verdict | Evidence |
|---|---|---|---|
| **9.1** | Distinguish a simulated complex wave from an experimental hologram; keep complex-wave selection, intensity-hologram generation and hologram reconstruction as separate, explicitly named operations; test reconstruction from `I = \|u_obj+u_ref\|²` without passing ground-truth phase in. | **FAIL** | No intensity hologram is ever formed and no reference wave exists in any of the 3058 lines. `specular_filter.py:500` loads the complex wave; `:523` FFTs it; `:594-601` masks one spot and takes `np.angle`. The output is the argument of a filtered copy of the simulated field. It is nevertheless described as holographic reconstruction in `README.md:1, 34`, `README.md:72` (citation 7 "…off-axis electron holography reconstruction … implemented in `specular_filter.py`") and `specular_filter.py:8`. |
| **9.2** | Audit orientation/coordinate conventions; resolve the README's `(1,1,-1)` vs `[1,-1,1]`; document planes vs directions, outward normal, beam axis, in-plane axes, handedness; check orthogonality numerically. | **PARTIAL** | The *code* is self-consistent and numerically clean: `slab_rotation_matrix()` (`:61-73`) is orthonormal to 2.2e-16 and right-handed, `det = +1`, `x̂ × ŷ = ẑ` (`REPRODUCED`). But the conflict is unresolved in the documentation (`README.md:3` "(1,1,-1) facet" vs `README.md:13` `[1,-1,1]`), and `(1,1,-1)` is incompatible with the stated `[110]` beam. Nothing states the outward sense of `x̂`, the tilt sign convention, active vs passive rotation, or the detector orientation; `meta_tilt_examples.json` labels the structure `"Diamond Cubic (100)"`. No reciprocal-space check and no structure-factor check exist. |
| **9.3** | Establish whether the propagation approximation fits the geometry; document slicing direction, paraxial assumptions, vacuum margins, lateral periodicity, wraparound, scattering channels and missing physics; validate against a reflection benchmark. | **FAIL** | Nothing in the repository documents or tests any of these. `REPRODUCED` here: 84.6 % of the incident wavefront enters the crystal head-on and only 1.0 % (8 mrad) / 3.1 % (24 mrad) of it reaches the surface from the vacuum side inside the slab; the cell is periodic along the surface normal with a 16.08 Å image gap; the 8 Å `atomic_potential_extent` wraps 0.35 Å past `Lx`; the configured absorber is silently dropped (`multislice_forward_model.py:275-280`). No benchmark of any kind is run. |
| **9.4** | Treat the reference beam as calibrated or explicitly idealised; separate object/reference branches; record curvature, carrier, amplitude balance, stability. | **NOT APPLICABLE / FAIL** | There is no reference beam anywhere, so none of the recording requirements can be met. Strictly the clause is not applicable to the code as written — but the README sells the pipeline as off-axis holography, so the absence is itself the finding. |
| **9.5** | Handle coherence and ensembles deliberately; do not silently discard ensemble axes. | **FAIL** | `_pick_first_2d_slice` (`specular_filter.py:61-77`) takes `[0,0,0,:,:]`, silently discarding the config, defocus and **tilt** axes; `process_all_tilts.py:33` opens only subset 0. `REPRODUCED` end-to-end (§5, case *A_step_5tilt*): a file whose tilt index 3 carries the +2π/3 step and whose index 0 carries none yields a reported step of **0.000 rad / 0.000 Å** — the signal is missed entirely, with no warning. Thermal/ensemble parameters are written to `meta.json` and never read. |
| **9.6** | Make the data plane and HDF5 axes explicit; require explicit axis interpretation; do not assume `image_wavefunctions` is an exit wave; fail clearly on ambiguous axes or missing calibration. | **FAIL** | The loader checks nothing: no `dim N` attributes, no `ndim`, no dtype, no `/metadata/r_x`, `/metadata/r_y` or `/metadata/tilts`, and it falls back to "the first complex dataset found anywhere" (`:129-156`). Pixel size comes from `meta.json`'s *advisory* value via `process_all_tilts.py:48-52`, a factor ≈2.01 error (sibling §3.5, `REPRODUCED` here). The saved wave is Fresnel back-propagated by ΔZ/2 (sibling §2a) yet is called "complex exit wave" in `multislice_forward_model.py:7, 580, 639` and the runner `:551, 854`. |
| **9.7** | Validate phase-to-height conversion; keep signs explicit; handle a small/uncertain denominator; account for wrapping; do not silently substitute defaults; preserve signed differences and report uncertainty; flag failed identification. | **FAIL** (every sub-clause) | Formula at `:152-156` is asserted, never derived or tested. `min/max` at `:39` destroys the sign — `REPRODUCED`: an imposed −2π/3 step is reported as **+1.146 rad, +0.429 Å**. Small denominator: only exact zero is guarded (`:156`), producing a silent `nan` — `REPRODUCED` with metadata lacking both angle keys. Wrapping is never considered: for the repository's own default the true phase is 8π/3 and only 2π/3 is observable, a **factor-4** underestimate (`DERIVED_HERE` + `REPRODUCED`). Defaults silently substitute for `energy_keV` (200.0), `alpha_deg` (0.0), `g_dot_n_surf` (1.0) — `REPRODUCED`: dropping `g_dot_n_surf` changes the answer from 0.122 to 0.099 Å with no warning. **No uncertainty is reported at all.** Failed identification prints a `Warning:` and continues. |
| **9.8** | Document units, Fourier conventions and processing bias; quantify how apodisation, padding, apertures, recentering, notching, unwrapping and ramp removal change phase and resolution; preserve raw phase, masks and fitted ramps; do not flatten away genuine long-wavelength phase; use a named, versioned constants source. | **FAIL** | Units are internally consistent (cycles/Å throughout the filter, no stray 2π; mrad for tilts; degrees for `alpha_deg`) and no factor-1000 error was found — that part is fine. Everything else fails: **no** quantification of apodisation (`α=0.3`, `:510`), padding (`:517`), aperture (`rin=8, rout=14` px, physical meaning undeclared and rescaling with `--dx`), notch (`σ=0.04, n=4`, `:543`, docstring `:17` "I do not know the limitations"), unwrapping (a naive row-then-column `np.unwrap`, `:259-269`, fed zeros at invalid pixels, `:635`), or ramp removal (**on by default**, `:646`). The raw phase is never saved. Constants are hard-coded and undocumented in four places with three different values (§2b); embeam itself uses a fourth, rounded set (`embeam/constants.py:39-97`). `REPRODUCED`: default processing removes 27 % of a single step and essentially all of a monotonic staircase (§5). |

---

## 4. CONCRETE DEFECTS AND INCONSISTENCIES (severity-ranked)

Severity: **Critical** = the script does not do what it claims, or produces a quantitatively
wrong physical number with no warning. **Major** = a real physical/numerical error that
changes a result or makes it unreproducible. **Minor** = correctness-neutral hygiene.

### CRITICAL

**C1 — `multislice_tilt_series_runner.py:547-556` silently disables ALL output. The
tilt-series runner writes no wavefunction file and no intensity file.**
The call passes `save_probe_complex=False` and `wavefunction_z_planes=[z_sampling]`.
Neither keyword exists in `prismatique.hrtem.image.Params`, whose `__init__`
(`prismatique/hrtem/image.py:376-388`) accepts exactly
`postprocessing_seq, avg_num_electrons_per_postprocessed_image, apply_shot_noise,
save_wavefunctions, save_final_intensity, skip_validation_and_conversion`; `grep` finds no
occurrence of either name anywhere in prismatique 0.0.1. Python therefore raises `TypeError`
at call-binding time, which `:557-559` swallows, printing
`Warning: Image params not applied: …` and setting `image_params = None`. `create_output_params`
then omits the keyword (`:428-433`), `hrtem.output.Params` takes
`_default_image_params = None` (`prismatique/hrtem/output.py:172-173`), and
`hrtem/image.py:427-434` converts `None` into `Params()` **with all defaults**, i.e.
`save_wavefunctions = False` and `save_final_intensity = False`
(`prismatique/hrtem/image.py:203-206` → `prismatique/cbed.py:188-191`). Since
`prismatique/hrtem/sim.py:439` and `output.py:550-552` branch on those two flags, **nothing is
written except `hrtem_simulation_parameters.json`**; the temporary `prismatic_output.h5` is
deleted. The full multislice runs, at 16× the intended cost (C2), and produces no data.
`SECTION_READ` of the pinned source; the `TypeError` follows from the signature with certainty.
*Fix*: delete the two invalid keywords (and, if a specific exit plane is wanted, note that
prismatique 0.0.1 has no such control — the plane is fixed at the cell mid-plane).
*This defect was not in the sibling report, which audited the forward model's call at `:428-434`.*

**C2 — `multislice_tilt_series_runner.py:540` `interpolation_factors=(4,4)` silently
multiplies the simulation grid by 16 and contradicts the forward model's `(1,1)` (`:421`).**
`prismatique/sample.py:2366`: `N = (4·f_x·Ñ_x, 4·f_y·Ñ_y)`. With `Ñ = (gx//4, gy//4)` and
`f = 4`, the potential grid is `4·gx × 4·gy`. `REPRODUCED`: the runner prints
`Grid (effective): 216 × 160   px≈0.485 Å` (`:737`) while actually building **864 × 640** at
**0.121 Å**. The tilt grid step is also 4× coarser (`prismatique/tilt.py:508-530`:
`step = (λ/ΔX, λ/ΔY)·f`), which is why the nearest available grid tilt is **0.657 mrad**
(10 % of θ_B) from the requested one. *Fix*: choose `f` deliberately and derive `Ñ` from it;
log the realised `N` and pixel, not `gx, gy`.

**C3 — `specular_filter.py:379` demodulates on the strongest FFT bin, which for the
repository's own default step is a *sideband*, not the carrier — injecting a spurious linear
phase ramp.** `find_peak` returns `argmax|Ψ|`. For a 50:50 two-level object with phase step Δ
the carrier amplitude is `|cos(Δ/2)|` and the first harmonic is `2|sin(Δ/2)|/π`; the harmonic
dominates when `|tan(Δ/2)| > π/2`, i.e. **|Δ| > 2.0078 rad = 115.0°** (`DERIVED_HERE`). The
repository's own one-bilayer step at (2,−2,0) is **Δ = 2π/3 = 2.0944 rad**, just past that
threshold. `REPRODUCED` on a synthetic wave whose carrier sits exactly on padded bin
(252, 490): `|Ψ|` there is 43 350, while bin (251, 490) — the sideband — is **74 586**, and
`find_peak` returns (251, 490). The 1-bin demodulation error is a phase ramp of 2π/600 per
row, i.e. **π/2 = 1.5708 rad** across the 150 rows between the terrace centres; the measured
step is 2.0944 − 1.5708 = **0.5236 rad**, matching the observed −0.5235 rad to 4 decimal
places. Forcing the true bin with `--manual-peak 252,490` and `--no-detrend` recovers
**2.130 rad** (1.7 % error). *Fix*: locate the spot from the known geometry
(`k_in + g`, both available in `meta.json`) and refine sub-pixel by a centroid of |Ψ|² over
the aperture — never by `argmax` of a single bin.

**C4 — the phase step for the repository's default configuration wraps, and nothing in the
pipeline accounts for it: the reported height is a factor 4 too small.**
`DERIVED_HERE`: for `g = (2,−2,0)`, `n̂ = [1,−1,1]/√3` and `h = m·d₁₁₁`,
`g·(h n̂) = 4m/3`, so `Δφ = 2π·4m/3 = 8πm/3`. For one bilayer the physical phase is
**8π/3 = 8.378 rad**, of which only **2π/3 = 2.094 rad** is observable. The step-height script
divides the *wrapped* value and returns **d₁₁₁/4 = 0.7839 Å** instead of **3.1355 Å**
(`REPRODUCED`: best-case end-to-end result 0.797 Å). The script itself prints
`Theoretical Delta Phi: 8.378 rad` next to a measured 0.325 rad and says nothing. For a
3-bilayer step `Δφ = 8π ≡ 0` — the step is invisible. The generator's own help text
(`si110_cleave_slab_generator.py:277-278`) flags the wrap; no code acts on it.
*Fix*: either choose a reflection with `g·n̂ h` integral or near-integral for the step unit,
or combine two reflections / a tilt series to resolve the order, and record explicitly that a
single Bragg phase determines the height only modulo `1/(g·n̂)`.

**C5 — `specular_filter.py:61-77` takes tilt index 0, so with any real tilt series the
measured object is the wrong one.** `REPRODUCED` end-to-end: a 5-tilt file whose index 3
(θ = 4.5001, 3.1820 mrad, the requested condition) carries the +2π/3 step and whose index 0
carries none yields **Δφ = 0.000 rad, h = 0.000 Å** from the repository's own scripts, with no
warning. With the runner's actual settings, `tilt_series[0] = (−0.9585, +2.5137) mrad` while
the requested offset is `(4.5001, 3.1820)` (`REPRODUCED`, §2b). *Fix*: read `/metadata/tilts`
and select by matching within half a grid step; fail if no match. (Sibling §3.4, §5.2 item 5.)

**C6 — pixel-size calibration is taken from `meta.json`'s advisory value, a factor ≈2.01
error, and the two errors partially cancel.** `process_all_tilts.py:48-52, 72-73` passes
`advisory_pixel_size_A` as `--dx/--dy`; the HRTEM image pixel is `2 × (L/N)`.
`REPRODUCED`: advisory 0.13 → true 0.261648 (ratio 2.013); advisory 0.5 with `f=(1,1)` →
true 0.96907 (ratio 1.938). Consequence (`REPRODUCED` on the synthetic set): with the **true**
pixel and a carrier at |g| the filter finds the right peak (|Ψ| = 7.46e4); with the advisory
pixel it locks onto a spurious feature 341× weaker (|Ψ| = 2.19e2, at `ix = 400 = kx = 0`).
Conversely, for the symmetric-Bragg carrier at |g|/2 the **true** pixel finds a wrong peak
(|Ψ| = 1.13e3) while the **wrong** pixel finds the right one (|Ψ| = 7.46e4), because the
factor-2 stretch maps the ring 1/d onto the true radius 0.2588 ≈ |g|/2 = 0.2604 (0.63 % apart,
inside the ±3 % ring). **The pipeline can therefore appear to work, and fixing either bug
alone breaks it.** *Fix*: read `/metadata/r_x`, `/metadata/r_y`; assert
`dx ≈ 2·Lx/N_x`; and set the search radius from `|k_in + g|`, not `|g|` (see C7).

**C7 — the filter's search radius `1/target_d_A` is the wrong radius for any tilted beam.**
The Fourier components of the exit wave lie at `k_in + g`, not at `g` (`REPRODUCED`):
zero tilt → 0.52080 ✓; the runner's own offset → **0.74056** (outside the ±3 % ring);
symmetric Bragg → **0.26040** (also outside). `specular_filter.py:481-483` uses
`1/meta["target_d_A"]` unconditionally and never reads `tilt_azimuth_deg` or the tilt
metadata. *Fix*: compute the expected spot position as a **vector** from `k_in` and `g` and
search a small neighbourhood of it.

**C8 — `step_height_reflection_formula.py:39, 151` destroys the sign of the step.**
`find_dominant_levels` returns `min(level1, level2), max(...)`, so
`Δφ = level_high − level_low ≥ 0` always. `REPRODUCED`: an imposed **−2π/3** step is reported
as **Δφ = +1.146 rad, h = +0.429 Å** — an up-step and a down-step are indistinguishable.
Instruction §9.7 requires signed differences. *Fix*: take the difference in a fixed spatial
order (e.g. terrace-with-larger-`y` minus terrace-with-smaller-`y`) from the identified
regions, not from sorted histogram levels.

### MAJOR

**M1 — no intensity hologram and no reference wave exist, yet the work is presented as
off-axis holography.** §2d, §3/9.1. The `.h5`/`.npz` "phase" is `np.angle` of a filtered
simulated complex field. *Fix*: split into three named stages
(`select_complex_sideband`, `form_intensity_hologram`, `reconstruct_hologram`) and test the
third on `|u_obj + u_ref|²` without access to the ground-truth phase.

**M2 — the geometry is a thin plate in a cell periodic along its own surface normal, with the
beam inside the crystal for 84.6 % of the wavefront.** §2a. Only 1.0 % (8 mrad) / 3.1 %
(24 mrad) of the incident wavefront reaches the surface from the vacuum side inside the slab.
The image gap along the normal is 16.08 Å; the 8 Å `atomic_potential_extent` wraps 0.35 Å past
`Lx`; there is no absorber. *Fix*: at minimum state the regime honestly; to model reflection,
increase the vacuum along the normal far beyond the lateral coherence length, add an absorbing
layer (which prismatique 0.0.1 cannot do — see M3), and lengthen the slab along the beam so
that `L·tanθ` exceeds the vacuum height.

**M3 — `absorbing_layers` is silently discarded, while the script prints that an absorber is
active.** `multislice_forward_model.py:268-280` wraps the construction in
`try/except Exception` and retries without the key. `prismatique.sample.ModelParams.__init__`
(`prismatique/sample.py:123-134`) has no such parameter, so the key **always** raises; `:510`
nevertheless prints `Absorber window (z, Å): [...] (bulk side)`. In the runner the absorber is
pure dead code — `create_system_params` is called without it (`:800-807`). *Fix*: remove the
code and the print, or implement absorption explicitly.

**M4 — the saved array is not an exit wave, but every message says it is.**
The engine applies `exp(+iπλ(ΔZ/2)q²)` unconditionally before saving (sibling §2a,
`PRISM02_calcSMatrix.cpp:433-445`), i.e. the wave is referred to the cell **mid-plane**
(≈ −99 Å of defocus for this cell). `multislice_forward_model.py:7, 580, 639` and the runner
`:551, 854` all call it the "complex exit wave". *Fix*: rename and record the plane in the
output metadata.

**M5 — the plane detrend is on by default and removes the signal being measured.**
`specular_filter.py:646`, `:652-676`. `REPRODUCED`: with the correct carrier bin, detrending
ON gives Δφ = 1.524 rad and OFF gives 2.130 rad against an imposed 2.094 — i.e. the default
removes **27 %** of a single step. For the 4-terrace monotonic staircase (the generator's own
default object) the successive differences collapse from 0.208/0.272/0.208 rad
(`--no-detrend`) to 0.124/0.060/0.124 rad (default), against an imposed 2.094 rad per step.
Instruction §9.8: "Do not flatten away genuine long-wavelength phase." *Fix*: default OFF;
when used, fit the ramp on an independent vacuum/flat region and save the fitted plane and the
raw phase.

**M6 — the k-space aperture is specified in pixels of the padded grid, so its physical
meaning changes silently with `--dx`, `--pad` and the array size, and the result is not a
monotonic function of it.** `rin = 8`, `rout = 14` (`:465-466`). At the true pixel that is a
passband radius of 0.0382 cyc/Å → a real-space resolution of ≈26 Å, against a 39.9 Å terrace.
`REPRODUCED` sweep (everything else fixed): `rin = 8/20/40/80` → reported
Δφ = 0.325 / 1.476 / 0.283 / **226.7** rad → h = 0.122 / 0.553 / 0.106 / **84.9 Å**. At
`rin = 80` the aperture overlaps neighbouring content and the answer becomes meaningless, with
no warning. *Fix*: specify the aperture in cyc/Å, check it against both the nearest
neighbouring spot and the required terrace resolution, and report the resulting resolution.

**M7 — the y-periodicity of the generated slab is broken: ~193 atoms are double-counted in a
duplicated plane at y = 0.** §2a. `si110_cleave_slab_generator.py:214` uses strict
inequalities at both ends of the periodic direction. The artefact is a line of anomalous
projected potential running **along the beam at fixed y** — geometrically identical to a step
edge. *Fix*: use `-Ly/2 <= y < Ly/2` (half-open) and assert that the number of atoms equals
the expected count for the volume.

**M8 — `meta.json` misreports the realised geometry.** `x_vacuum_A = 10.0` vs 7.6484 Å
actual; `Lx_si_A = 84.659` vs 88.579 Å actual; `Lz_si_A` 1.9201 Å too long; `z_vacuum_A`
asymmetric (31.92 front / 30.00 back). The true surface position (`x_top_high_A`, `x_back_A`,
`terrace_x_top_A`) is computed at `:232-234` and then **not written** (`:368-414`).
Anything downstream that reasons about the vacuum margin — including a future absorber or a
grazing-angle calculation — will be wrong. *Fix*: write the measured extents and assert them.

**M9 — the `--sample-tilt-validation` path breaks lateral periodicity and pushes atoms out of
the box.** `multislice_tilt_series_runner.py:597-665` rotates every atom by θ_B about
`(sin az, −cos az, 0)` but rewrites the **same** cell dimensions (`:644-649`). `REPRODUCED`:
`R·(0,Ly,0)` differs from `(0,Ly,0)` by **0.301 Å** and `R·(Lx,0,0)` from `(Lx,0,0)` by
**0.558 Å** (Si–Si bond 2.35 Å), so the periodic images no longer register; and **168 atoms
end up outside the y range** ([−0.2607, 80.0636] Å against a 0–79.8176 Å box). The "validation"
therefore compares a beam tilt against a *sheared, non-periodic* crystal. `_write_prismatic_xyz`
(`:586-594`) also drops to `%.6f`, undoing the generator's deliberate `%.10f`
(`si110_cleave_slab_generator.py:45-55`, whose comment explains that `%.6f` "can flip atoms
across step boundaries"). *Fix*: rotate only about an axis perpendicular to both the beam and
a lattice vector, rebuild the cell from the rotated lattice vectors, and keep `%.10f`.

**M10 — `process_all_tilts.py` cannot run: it calls a file that was renamed, and its expected
directory layout no longer matches the runner's.** `:13` `specular_666_filter.py` (renamed to
`specular_filter.py` in commit `81f1af0`); `:10` a hard-coded absolute HPC path
`../outputs/job_12198643`; `:20` expects one `tilt_*` directory per tilt while the runner
writes all tilts into one directory (`:787-788`). It exits **with status 0** after printing
`Error: Base directory not found` (`REPRODUCED`). It also never passes `--meta`, so the filter
loses its target radius. *Fix*: argparse, and select the tilt index inside the filter.

**M11 — `find_dominant_levels` has no no-step control and no failure mode.**
`step_height_reflection_formula.py:27-30`: fewer than two histogram peaks → prints a warning
and returns the 10th/90th percentiles of the noise, i.e. a non-zero "step". With more than two
terraces it silently returns the difference of the two *tallest* peaks, not a step height
(`REPRODUCED` on the 4-terrace case). `:160`
`h_theo = float(meta.get('step_height_A') or a/√3)` is a **falsy-zero bug**: for a flat
reference slab the generator writes `step_height_A = 0.0`, so the "theoretical" step is
reported as **3.136 Å** instead of 0 (`REPRODUCED`). *Fix*: `is None` rather than `or`;
identify terraces from the known geometry; return `None` and a diagnostic on failure.

**M12 — silent metadata defaults in `step_height_reflection_formula.py`.**
`energy_keV → 200.0` (`:67`), `alpha_deg → 0.0` (`:74`), `g_dot_n_surf → 1.0` (`:81`),
`a_A → 5.4309` (`:159`). `REPRODUCED`: with both angle keys removed, `θ_B = 0` and the script
prints `Calculated Step Height: nan A` and `Theoretical Delta Phi: 0.000 rad` and continues to
plot; with `g_dot_n_surf` removed the answer silently changes from 0.122 to 0.099 Å (the
factor 0.8165). Instruction §9.7 forbids exactly this. *Fix*: require the keys; the guard at
`:156` must also reject small denominators, not only exactly zero.

**M13 — `np.roll` demodulation is circular; content near the array edge wraps.**
`specular_filter.py:245-257`, `:443`. Nothing checks whether the mask (radius up to `rout`
px around a peak that can lie anywhere) crosses the boundary. With `--pad 2` the risk is small
but not zero; with `--pad 1` it is real. *Fix*: apply the carrier removal as a real-space
phase factor `exp(-2πi k₀·r)` rather than an integer roll (this also removes the ±½-bin
quantisation of the carrier).

**M14 — 2-D phase unwrapping is a row-then-column `np.unwrap` applied to an array in which
invalid pixels have been set to 0.** `:259-269`, `:635`, `:638`. This is not a 2-D unwrapping
algorithm; it has no residue handling and it will propagate errors along whole rows/columns.
The injected zeros guarantee artificial 2π jumps at every mask boundary. *Fix*: use a
quality-guided or least-squares 2-D unwrapper and mask properly (e.g. `skimage.restoration.unwrap_phase`).

**M15 — the raw, unprocessed phase is never saved; only post-apodisation, post-notch,
post-mask, post-demodulation arrays are.** `:722-741`. Instruction §9.8 requires preserving
raw phase, masks and fitted ramps. Masks and ramps *are* saved; raw phase is not.

**M16 — `requirements.txt` contradicts the README and pins nothing.**
`requirements.txt:3` "recent versions are fine"; `:11-12` bare `prismatique`, `embeam`.
`README.md:59` says `prismatique ==0.0.1` and "later versions may break the
`prismatique.hrtem.*` schema". No lockfile, no environment record. Instruction §8 requires
recorded versions, backend, precision and seeds. *Fix*: pin, and record the resolved
environment with each run.

**M17 — `estimate_wave_memory_gb` is wrong in structure and drives an automatic pixel-size
change.** `multislice_forward_model.py:126-142` counts `nx·ny·num_slices·z_supersampling`
voxels at 16 B (complex128; the data are complex64) with a ×2 safety factor, and is evaluated
on the **pre-interpolation** grid. `REPRODUCED`: it prints 0.82 GB for both `f=(1,1)` and
`f=(4,4)`, while the actual potential array is 0.026 GB and 0.410 GB respectively and the
saved waves are 0.005 GB and 0.082 GB. `HRTEM_TARGET_MEM_GB` (`:534-550`) then coarsens the
pixel from this number. *Fix*: model the arrays actually allocated, or delete the feature.

**M18 — README/docs vs code, physics-relevant.** (a) `README.md:3` "(1,1,-1) facet" vs
`README.md:13` `[1,-1,1]` vs the code's `[1,-1,1]` — and `(1,1,-1)` is **incompatible** with
the stated `[110]` beam (`[1,1,0]·[1,1,-1] = 2 ≠ 0`). (b) `meta_tilt_examples.json` labels the
structure `"Diamond Cubic (100)"` in all four blocks while the facet is `{111}`-type, and sets
`alpha_deg = 1.375` = θ_B(666), with example 3 explicitly "for 666 Bragg condition" — a
reflection that is **kinematically forbidden** in diamond Si (`DERIVED_HERE`: all even,
h+k+l = 18, 18 mod 4 = 2 → F = 0) and that the initial commit message already acknowledges as
forbidden. (c) `README.md:39` advertises `/hann/amp`, `/hann/phase`; the code writes
`/hann/amplitude`, `/hann/phase_wrapped`, `/hann/phase_flat` (`:731-741`). (d) `README.md:70`
claims Kirkland's "Debye–Waller treatments [are] used throughout this code" — **no thermal
treatment is ever enabled** (§2c). (e) `README.md:71` gives the author order
"Peng, Whelan, Dudarev" and `:72` "Tomita, Shindo"; the project's own reference library
([B08], [B11]) gives "Peng, Dudarev, Whelan" and "Shindo, Tomita" and instructs that those
orders be preserved. (f) The README cites no Osakabe paper at all, although
`step_height_reflection_formula.py:152` calls the relation "the projected Osakabe formula" and
the initial commit message claims to replicate "Osakabe et al. (1993)" — which is [P03], by
**Banzhof and Herrmann**, not Osakabe (instruction file lines 329-337). (g) README citation
numbering starts at 2; there is no citation 1.

**M19 — no tests, no CI, no validation of any kind.** `git ls-files` returns 14 files; there
is no `tests/`, `test_*.py`, `conftest.py`, `tox.ini`, `.github/` or any other harness
(`REPRODUCED`). Instruction §10 lists eight test categories, none of which exists. The only
"validator", `hdf5_output_validator.py`, is 12 lines with a hard-coded path on the author's
laptop (`:4`) and makes no assertions.

### MINOR

**m1** — `sample_generators/si110_cleave_slab_generator.py:3` docstring:
`"Si[110] cleave-edge slab - contains bugs. no ready."` and
`multislice_tilt_series_runner.py:5` `"UNDER TESTING, NO READY."` — the authors' own status
markers are still present at HEAD, in a repository whose initial commit is titled
"Initial public release … v0.1.0".
**m2** — `CITATION.cff` contains a single newline (`REPRODUCED`: `od -c` shows `\n`), which is
not valid CFF; the HEAD commit `6694959` is the one that emptied it (118 → 1 lines).
**m3** — `multislice_forward_model.py:659-666`: `--timeout-min 20` is also consumed as the
positional output directory. `REPRODUCED`: `coords.xyz --timeout-min 20` →
`output_dir = '20'`; `--production --timeout-min 60` → `output_dir = '60'` and the timeout is
forced to 30 anyway (`:668`).
**m4** — `multislice_forward_model.py:317` `max_data_size = 8_000_000_000  # 2 GB`.
**m5** — `specular_filter.py:1` is a blank line before the shebang, so the shebang is inert;
no pipeline file has the executable bit set (`REPRODUCED`: all `-rw-r--r--`).
**m6** — stale usage strings: `multislice_forward_model.py:10, 646`
`rem_holography_final.py`; `multislice_tilt_series_runner.py:8`
`holography_unified_snapped.py`; neither file exists.
**m7** — dead code: `specular_filter.py:271-290` (`detrend_plane`, superseded inline at
`:652-676`); `:152-155` (`_pick_first_2d_slice` called on a numpy array, result immediately
overwritten); `multislice_tilt_series_runner.py:194-205` (`format_tilt_angle`, never called,
and its docstring says "integer milliradians" while it actually encodes 0.01 mrad);
`multislice_forward_model.py:405-410` (`z_sampling`, computed and unused).
**m8** — `find_peak`'s `exclude_center_px` masks a **square** of half-width 20 px
(`:368-369`) while the docstring says "Radius in pixels" (`:344`).
**m9** — `raised_cosine_disk`'s "Hamming" branch (`:229-234`) is a rescaled raised cosine that
reaches 0 at `R_out`; it is not a Hamming window, and the two branches differ only in taper
shape. Running both and saving both doubles the output for no stated purpose; nothing
downstream uses the Hamming result (`step_height_reflection_formula.py:57` reads only
`phase_hann_flat`).
**m10** — `.gitignore:29-32` ignores `*.h5`, `*.npz` and `results_arrays.npz`, and `:51-53`
ignores `*.png` and `*.log`; combined with M19 nothing about a run can be archived in-repo.
**m11** — `docs/PIPELINE_LOG.md` cross-references a "§4" that commit `e61e545` deleted
(119 → 68 lines); the file now ends at line 66 with a stray `\`. It names six scripts that do
not exist (§1.7) and still shows `specular_666_filter.py` and a `si100_slab_generator.py`
source for the sample.
**m12** — `bragg_angle_mrad` (`:33-34`) returns `0.0` instead of raising when `λ/2d > 1`.
**m13** — `OMP/MKL/NUMBA_NUM_THREADS` are hard-forced to `'1'` at import
(`:27-29` / `:22-24`) and then a CPU worker pool of `os.cpu_count()` threads is configured
(`:336-338` / `:455-457`); the interaction is never documented.
**m14** — the `timeout` context manager (`:145-156`) uses `SIGALRM`, which cannot interrupt
the engine while control is inside compiled Prismatic code.
**m15** — every `prismatique` construction is wrapped in a bare `except Exception` that
degrades to `None` and continues (`:275-280, 283-296, 364-386, 416-437` and the runner's
equivalents). That pattern is what turns C1 and M3 into silent failures. `:501` also returns
`None` worker params on any error, which the caller then omits.
**m16** — `README.md:44` contains a stray `postprocessing>` line inside the code fence, and
`:27`/`:32` have broken box-drawing alignment.
**m17** — `si110_cleave_slab_generator.py:94` re-literals `[1,-1,1]/√3` instead of reusing
`slab_rotation_matrix()[0]`; a change to the frame would silently desynchronise them.
**m18** — `si110_cleave_slab_generator.py:250` documents `a*sqrt(3) = 9.408 Å`; with the
default `a = 5.4309` it is 9.4066 Å (the 9.408 value corresponds to `a = 5.431`).
Likewise `:154-156`'s "0.78 Å / 2.35 Å" are 0.78388 / 2.35165 Å.
**m19** — `step_height_reflection_formula.py:143` `profile = profile[np.isfinite(profile)]`
silently re-indexes the profile, so the plotted abscissa (`:176`) no longer maps to position.
**m20** — no module in `pipeline/` has a `if __name__` guard problem, but none is importable
as a package either (no `__init__.py`), so the ~250 duplicated lines between the two
forward-model scripts cannot be shared without restructuring.

---

## 5. WHAT ACTUALLY RAN

Environment (`REPRODUCED`): Python **3.11.15**, numpy **2.4.6**, scipy **1.17.1**,
h5py **3.16.0** (HDF5 2.0.0), ase **3.29.0**, matplotlib **3.11.2**, in the pre-existing venv
`…/scratchpad/venv`. `prismatique`, `embeam`, `pyprismatic` and the Prismatic engine were
**NOT** installed and **NOT** run (per instruction). Where prismatique behaviour is quoted it
is either from the sibling's `REPRODUCED` runs (report D) or from my own faithful
re-implementation of the 0.0.1 source (marked as such). The target repository was **not
modified**: `git status --porcelain` is empty and `git rev-parse HEAD` is
`66949599f0cbaf232ac649ba46a123e945660a1d` after all work. (Byte-compilation refreshed the
pre-existing, `.gitignore`d `pipeline/__pycache__/*.pyc`; all later runs used
`PYTHONPYCACHEPREFIX` pointing outside the repository.)

Shorthand used below: `REPO=…/scratchpad/si110-reflection-holography`,
`PY=…/scratchpad/venv/bin/python`, `W=…/scratchpad/audit`.
Every helper script I wrote is kept under `W/` for re-execution.

### 5.1 Byte-compilation — PASS

```
for f in $REPO/pipeline/*.py $REPO/sample_generators/*.py; do $PY -m py_compile "$f"; done
```
All **7** modules compile with return code 0: `hdf5_output_validator.py`,
`multislice_forward_model.py`, `multislice_tilt_series_runner.py`, `process_all_tilts.py`,
`specular_filter.py`, `step_height_reflection_formula.py`,
`si110_cleave_slab_generator.py`. (Compilation says nothing about the `TypeError`s in C1/M3:
those are raised at call time.)

Also run: `git ls-files` (14 files) and a `find` for `test_*`, `*_test.py`, `conftest.py`,
`tox.ini`, `*.yml`, `*.yaml`, `.github` → **no matches** (M19).

### 5.2 Slab generator — RUN, with numerical verification

```
$PY $REPO/sample_generators/si110_cleave_slab_generator.py --outdir $W/gen_default
$PY $REPO/sample_generators/si110_cleave_slab_generator.py --create-step --outdir $W/gen_step
$PY $REPO/sample_generators/si110_cleave_slab_generator.py --create-step --n-terraces 2 \
      --terrace-heights-bilayers 0 2 --outdir $W/gen_step2
```
All three succeeded in ≈8 s each, writing `.xyz`, `.cif` and `meta.json`.

| check | script | result |
|---|---|---|
| rotation orthonormal | `W/chk_geom.py` | `max‖R·Rᵀ−I‖ = 2.22e-16` — **PASS** |
| handedness | `W/chk_geom.py` | `det R = +1.0000000000`, `x̂ × ŷ = ẑ` — **PASS (right-handed)** |
| surface is {111}, beam is <110>, beam in the surface | `W/chk_geom.py` | `[1,-1,1]` is `<111>`; `[1,1,0]·[1,-1,1] = 0`; `[1,-1,-2]` ⟂ both — **PASS** |
| structure factor of the target | `W/chk_geom.py` | (2,−2,0) **allowed**; (6,6,6) **forbidden** (h+k+l = 18, 18 mod 4 = 2); no such check exists in the repository |
| terrace heights vs d₁₁₁ | `W/chk_bilayer.py` | 0 / 3.13553 / 6.27106 / 9.40659 Å = exactly 0/1/2/3 × d₁₁₁, error < 1e-5 Å — **PASS** |
| where the cut planes fall | `W/chk_bilayer.py` | 58 discrete x-planes; gaps take exactly two values **0.78388 Å** (= d₁₁₁/4, intra-bilayer) and **2.35165 Å** (= 3d₁₁₁/4, inter-bilayer); every terrace top sits above a **wide** gap — **no half-bilayers, PASS** |
| lattice continuity across steps | `W/chk_bilayer.py` | terrace tops are members of the same plane ladder as the flat slab — **PASS** (truncation, not displacement) |
| atom counts | `W/chk_slab.py` | flat **49357**, 4-terrace **46805**, 2-terrace(0,2) **47628**; all Z = 14, occ = 1.000, σ = 0.076 |
| cell line vs atom extent | `W/chk_slab.py` | `.xyz` line 2 = `104.659353 79.817603 198.248144`, identical to `meta["box_A"]`; **0 atoms outside the cell** — **PASS** |
| vacuum actually present | `W/chk_pbc.py` | above surface **7.6484 Å**, below back face **8.4322 Å** (meta claims 10.0) — **FAIL vs metadata** |
| no atoms in the intended vacuum | `W/chk_pbc.py` | none: the Si band is contiguous from 8.4322 to 97.0110 Å — **PASS** |
| y periodicity | `W/chk_pbc.py` | `y.min() = 0` and `y.max() = Ly` **exactly**; 193 atoms at y = 0, 172 at y = Ly; boundary gap **0.000000 Å** instead of 1.10858 Å — **FAIL (M7)** |
| z symmetry / Prismatic z-flip | `W/chk_zflip2.py` (KD-tree) | after `z → Lz − z` a shift of **+3.8402 Å** puts **97.41 %** of atoms back on original sites to < 1e-5 Å — the mirror is a lattice symmetry here, so the flip is **structurally benign** for this orientation; the residual 2.6 % are the two end planes. Net effect: the slab sits ≈1.92 Å further along the beam than written. |
| beam footprint | `W/chk_beam.py` | see the table in §2a: **84.64 %** of the wavefront enters the crystal head-on; only **1.04 %** (8 mrad) / **3.13 %** (24 mrad) of it reaches the surface from vacuum inside the slab |

### 5.3 Wavelength formulas — RUN (`W/chk_lambda.py`)

At 200 keV: generator `0.025079340`, forward-model/runner/step-height `0.025079341`
(difference **−1.69e-10 Å = −1e-6 %**; θ_B differs by 4.4e-8 mrad — **cosmetic, not numerical**),
runner's snapping formula `0.025079422` (**+3.25e-4 %**), embeam 0.0.1 `0.025079337`.

### 5.4 Tilt selection — RUN as a faithful re-implementation of prismatique 0.0.1

`W/chk_tilt.py` reimplements `sample._FFT_1D_freqs`, `_angular_mesh`, `_beam_idx_mesh`,
`_k_mask`, `_angular_mesh_and_beam_mask` and `tilt._series` from the pinned source
(`prismatique/sample.py:1787-1930, 2366, 2474-2480`; `prismatique/tilt.py:508-530, 655-685`)
and drives them with the repository's own defaults. Results in §2b. **NOT RUN**: the actual
prismatique/Prismatic engine (not installed, and installation was excluded by instruction),
so these numbers are a re-derivation from source, not an execution of the package. The
sibling's report D contains the corresponding `REPRODUCED` runs of the real package.

### 5.5 Synthetic 5-D HDF5 in the prismatique schema — BUILT and RUN

`W/make_synth5d.py` writes `/data/image_wavefunctions` as **complex64**, shape
**(n_cfg, n_defocus, n_tilt, r_y, r_x)**, with the five `dim N` attributes, plus
`/metadata/r_x` (ascending, centred), `/metadata/r_y` (**descending**, centred),
`/metadata/tilts` (mrad, with its two `dim` attributes) and `/metadata/defocii`. Image grid
300 × 400, image pixel **(0.261648, 0.266059) Å** = 2 × the potential pixel of an 800 × 600
grid on the generator's own 104.659 × 79.818 Å cell.

The field is `ψ = exp(i[2π(k₀·r) + φ(y)]) + 5`, with the "5" standing in for the unscattered
beam. Carriers are placed on exact FFT bins:

* **Case A** (zero-tilt geometry): bins (45, 24) → |k| = **0.524674 cyc/Å**, 0.74 % from
  |g₍₂₋₂₀₎| = 0.520803.
* **Case B** (symmetric-Bragg geometry): bins (22, 12) → |k| = **0.258436 cyc/Å**, 0.75 % from
  |g|/2 = 0.260401.

`φ(y)` is a two-level step of **+2π/3** (the true observable phase for one d₁₁₁ bilayer on
(2,−2,0)), or −2π/3, or 0, or a four-terrace staircase. Files:
`A_step_1tilt.h5`, `A_flat_1tilt.h5`, `A_neg_1tilt.h5`, `A_stair_1tilt.h5`,
`B_step_1tilt.h5`, `A_step_5tilt.h5` (5 tilts; the +2π/3 step is at **index 3**, index 0 has
**no** step).

Commands (all succeeded; `MPLBACKEND=Agg`):

```
$PY $REPO/pipeline/specular_filter.py <file>.h5 --out-prefix $W/out/<tag> \
       --meta $W/gen_step2/si110_object/meta.json --dx <dx> --dy <dy> [--rin R --rout R'] \
       [--no-detrend] [--manual-peak iy,ix]
$PY $REPO/pipeline/step_height_reflection_formula.py --results-dir $W/out/<tag>_bragg_filter \
       --meta <meta>.json --output $W/steps/<tag>.png
```

**Peak-selection outcomes** (padded grid 600 × 800, centre (300, 400); the true Case-A
carrier bin is **(252, 490)**, the true Case-B bin is **(276, 444)**):

| input | `--dx` given | peak found | \|Ψ\| at it | verdict |
|---|---|---|---|---|
| A (+2π/3) | **0.261648** (true) | (251, 490) | 7.46e4 | correct spot, **but 1 bin off in y** — the sideband (C3) |
| A (+2π/3) | 0.13 (advisory) | (259, **400**) | 2.19e2 | **wrong**: 341× weaker, on the k_x = 0 line |
| A, **no `--meta`** | 0.13 | (251, 490) | 7.46e4 | correct spot, by luck (global argmax, no ring) |
| B (symmetric) | **0.261648** (true) | (226, 444) | 1.13e3 | **wrong**: 66× weaker |
| B (symmetric) | 0.13 (advisory) | (275, 444) | 7.46e4 | **correct — the two errors cancel** (C6) |
| A flat control | 0.261648 | (252, 490) | 8.67e4 | correct (no sideband, so argmax = carrier) |
| A 5-tilt | 0.261648 | (252, 490) | 8.67e4 | correct spot, but of **tilt index 0** = the no-step wave |

**Direct FFT inspection** (`W/diag_peak.py`) of `A_step_1tilt.h5` after the filter's own
apodisation and padding: `|Ψ(252,490)| = 43 350` (carrier) vs `|Ψ(251,490)| = 74 586`
(sideband). Fourier-series check: `|c₀| = |cos(Δ/2)| = 0.5000`,
`|c₁| = 2|sin(Δ/2)|/π = 0.5513` for Δ = 2π/3 — the sideband wins whenever
**|Δ| > 2 arctan(π/2) = 2.0078 rad = 115.0°** (`DERIVED_HERE`).

**End-to-end step-height results** (the repository's own two scripts, chained). Imposed
Δφ = +2.0944 rad; wrapped-truth height by the repository's own formula = **0.7839 Å**; true
physical step = **3.1355 Å**:

| case | reported Δφ (rad) | reported h (Å) | comment |
|---|---|---|---|
| A, true pixel | 0.325 | **0.122** | sideband demodulation (C3) + detrend (M5) |
| A, advisory 0.13 pixel | 1.095 | 0.410 | wrong peak (C6) |
| A, no `--meta` (what `process_all_tilts.py` does) | 0.325 | 0.122 | same as row 1 |
| A, **flat control** | 0.000 | **0.000** | correct — but only because the detrended flat phase is identically 0 |
| A, **negative** step (−2π/3) | **+1.146** | **+0.429** | **sign destroyed** (C8) |
| A, 4-terrace staircase, detrend ON | 1.949 | 0.730 | two arbitrary histogram levels, not a step |
| A, 4-terrace staircase, `--no-detrend` | 1.288 | 0.482 | |
| A, single step, `--no-detrend` | 0.219 | 0.082 | |
| B symmetric, true pixel | 3.160 | 1.183 | wrong peak |
| B symmetric, advisory pixel | 0.941 | 0.352 | right peak, still wrong number |
| **A 5-tilt, step at index 3** | **0.000** | **0.000** | the step is missed entirely (C5) |
| A, `--manual-peak 252,490`, `--rin 20`, detrend ON | 1.524 | 0.571 | |
| **A, `--manual-peak 252,490`, `--rin 20`, `--no-detrend`** | **2.130** | **0.797** | **best achievable: 1.7 % phase error; still 4× below the true 3.1355 Å because of the wrap (C4)** |

**Aperture sensitivity** (case A, everything else fixed, default peak finding):

| `--rin` / `--rout` (px) | passband radius (cyc/Å) | real-space resolution (Å) | reported Δφ (rad) | reported h (Å) |
|---|---|---|---|---|
| 8 / 14 (default) | 0.0382 | 26.2 | 0.325 | 0.122 |
| 20 / 35 | 0.0955 | 10.5 | 1.476 | 0.553 |
| 40 / 70 | 0.1911 | 5.2 | 0.283 | 0.106 |
| 80 / 140 | 0.3822 | 2.6 | **226.734** | **84.861** |

Non-monotonic, and catastrophic at the largest aperture, with no warning (M6).

**Metadata-default failure modes** (same reconstruction, edited `meta.json`):

| meta | θ_B used | ĝ·n̂ used | reported h | note |
|---|---|---|---|---|
| full | 6.531 mrad | 0.8165 | 0.122 Å | baseline |
| `target_theta_B_mrad` **and** `alpha_deg` removed | **0.000 mrad** | 0.8165 | **nan** | printed as `Calculated Step Height: nan A`, no error, plotting continues (M12) |
| `g_dot_n_surf` removed | 6.531 mrad | **1.0000** | 0.099 Å | silent −18.4 % (M12) |
| `energy_keV` removed | 6.531 mrad | 0.8165 | 0.122 Å | silently uses 200 keV (M12) |
| flat slab's own meta (`step_height_A = 0.0`) | — | — | 0.000 Å measured, but **"Theoretical Step (meta): 3.136 A"** | falsy-zero bug (M11) |

### 5.6 Other executions

* `$PY $REPO/pipeline/process_all_tilts.py` → prints
  `Error: Base directory not found: …/outputs/job_12198643` and **exits 0** (M10).
* `W/chk_sampletilt.py` reimplements `_build_sample_tilt_variant`: max atom displacement
  0.390 Å; **168 atoms leave the y range** ([−0.2607, 80.0636] Å vs a 0–79.8176 Å box);
  `‖R·a₂ − a₂‖ = 0.301 Å`, `‖R·a₁ − a₁‖ = 0.558 Å` (M9).
* `W/chk_sampling.py`: anti-aliasing band and spot positions for every
  (advisory pixel, interpolation factor, tilt) combination (§2b, §2c).

### 5.7 NOT RUN

* `multislice_forward_model.py` and `multislice_tilt_series_runner.py` were **NOT** executed
  (they `import prismatique` at module level; prismatique/embeam/Prismatic were deliberately
  not installed). C1, C2, M3 are therefore established from the **pinned source** of
  prismatique 0.0.1 (signatures and default values quoted with file:line), not from a run.
  The sibling's report D contains `REPRODUCED` executions of the installed package for the
  overlapping claims.
* `hdf5_output_validator.py` was **NOT** run (hard-coded macOS path).
* No Prismatic/PRISM benchmark, no reflection/dynamical-diffraction benchmark, no convergence
  study in slice thickness or pixel size, no norm-preservation test: none of these exists in
  the repository and none was performed here.
* No experimental data was involved at any point.

---

## 6. SUMMARY: WHAT THE REPOSITORY SIMULATES vs WHAT THE EXPERIMENT MEASURES

Instruction §9.1 asks for three explicitly named, separate operations. The repository
implements **only the first**, and labels it as the third.

| # | Operation (instruction §9.1) | What a reflection-mode dark-field electron-holography experiment involves | What this repository does at commit 6694959 | Verdict |
|---|---|---|---|---|
| 1 | **Complex-wave selection** — pick one Fourier component of a known complex field | (no experimental counterpart; a simulation-only step) | `specular_filter.py:523-601`: FFT the simulated complex wave, notch (000), mask one spot, roll to DC, IFFT, `np.angle`. Peak chosen by `argmax` on a ±3 % ring of radius `1/d`; pixel size from `meta.json`. | **Implemented**, with defects C3, C5, C6, C7, M6, M13, M14 |
| 2 | **Intensity-hologram generation** — form `I = \|u_obj + u_ref\|²` in a common detector plane, then model detector effects | The biprism overlaps an object beam and a reference beam; the detector records an **intensity** fringe pattern; the object phase is *unknown* and encoded in the fringe positions | **Absent.** No second branch, no `u_ref`, no carrier generation, no `\|·\|²` of a sum, no shot noise (`apply_shot_noise=False`), no MTF/DQE. The one intensity file prismatique can write is switched off in the runner and NaN-filled in the forward model (sibling §3.4). | **NOT IMPLEMENTED** |
| 3 | **Hologram reconstruction** — recover phase from a *measured intensity* without using the hidden truth | Sideband isolation in the Fourier transform of the **intensity** hologram; the sideband is the cross-term `u_obj·u_ref*`; phase is obtained relative to a reference hologram | **Absent.** What is called reconstruction operates on the complex field itself, so the "recovered" phase was never unknown: it is `arg(mask ⊛ ψ_sim)`. A diffraction spot of a complex field and a cross-term sideband of an intensity hologram are different quantities (instruction §9.1). | **NOT IMPLEMENTED; the label is applied to operation 1** |

**Forward-model side, in the same terms:**

| aspect | reflection-mode experiment | this repository |
|---|---|---|
| specimen | semi-infinite crystal, one free surface, grazing incidence | 88.6 Å-thick plate, **two** free surfaces, **periodic along the surface normal** with a 16.1 Å image gap, no absorber |
| illumination | wave arriving from vacuum, meeting the surface at θ_graze | plane wave filling the whole cell; **84.6 %** starts inside the crystal; **1.0 %** (8 mrad) to **3.1 %** (24 mrad) of it reaches the surface from vacuum inside the slab |
| measured beam | specularly reflected / surface-diffracted beam leaving into vacuum | a lattice Bragg beam of the **(2,−2,0)** zone-axis reflection, computed by transmission multislice through the plate |
| recorded plane | detector plane after the imaging system | the supercell **mid-plane** `z = ΔZ/2` (Fresnel back-propagated by ΔZ/2 by the engine), mislabelled "exit wave" |
| what "phase" means | phase of the object wave relative to a physical reference beam | argument of a band-pass-filtered copy of the simulated field, after apodisation, zero padding, a k-space notch, an integer-bin carrier roll, a naive 2-D unwrap and (by default) a plane subtraction |
| step-height inversion | measured, calibrated, with sign, wrap order and uncertainty | `h = Δφλ/(4π sinθ_B (ĝ·n̂))` with the **sign discarded**, the **2π order ignored** (the true phase is 8π/3, so the answer is 4× low), silent defaults for θ_B, E and ĝ·n̂, and **no uncertainty at all** |
| ensembles / coherence | incoherent averaging over source, energy, phonons | one static configuration; the config, defocus and **tilt** axes are all collapsed by `[0,0,0,:,:]` |

**One-line summary.** The repository is a **transmission multislice simulation of a thin Si
plate viewed along [110] at near-zero glancing angle**, followed by a **virtual dark-field
complex-wave filter**. It is neither a reflection simulation nor a holography simulation, and
none of its quantitative outputs has been validated against anything.

---

## 7. WHAT WOULD HAVE TO CHANGE FIRST (priority order)

This is my recommendation, not a claim that any of it has been done.

1. **C1** — remove `save_probe_complex` / `wavefunction_z_planes` so the tilt runner writes
   output at all; replace every bare `except Exception: … = None` around a prismatique
   constructor with an explicit failure.
2. **C5 + C6 + C7 + 9.6** — rewrite the loader: assert the dataset name, `ndim`, `dim N`
   attributes and dtype; take the pixel size from `/metadata/r_x`, `/metadata/r_y`; select the
   tilt index by matching `/metadata/tilts` to the intended `(θ_x, θ_y)` within half a grid
   step and fail otherwise; compute the expected spot as the **vector** `k_in + g`.
3. **C4 + C8 + M11 + M12** — rewrite the step-height inversion: signed differences from
   geometrically defined terrace regions, explicit 2π-order handling (a single Bragg phase
   fixes `h` only modulo `1/(g·n̂)` = 3d₁₁₁/4 here), required metadata, a small-denominator
   guard, and a reported uncertainty.
4. **C3 + M5 + M6** — spot location from geometry with sub-pixel refinement rather than
   `argmax`; aperture specified in cyc/Å and checked against the terrace width and the nearest
   competing spot; detrend OFF by default; save the raw phase.
5. **C2 + M8 + M7** — make `interpolation_factors` explicit and log the realised grid; write
   the measured surface/vacuum extents into `meta.json`; fix the half-open cut in y.
6. **M1** — add `form_intensity_hologram` and `reconstruct_hologram` as separate, tested
   stages, and test stage 3 on synthetic intensity only.
7. **M19** — add the tests instruction §10 lists, starting with the ones in §5.5 of this
   report, which already fail.
8. **M2 + 9.3** — decide whether the reflection geometry is to be modelled at all with this
   engine; if yes, the vacuum, the slab length and the boundary conditions all have to change,
   and a reflection benchmark is required before any number is quoted.

---

## 8. EVIDENCE-LABEL INDEX FOR THIS REPORT

* `REPRODUCED` — everything in §5, and every number in §2a, §2b, §2c, §2d and §4 that is
  attributed to a run: slab geometry, bilayer ladder, terrace heights, vacuum, y-duplication,
  z-flip, beam footprint, wavelength comparison, peak selection, end-to-end step heights,
  aperture sweep, metadata-default failures, `process_all_tilts.py` exit behaviour,
  sample-tilt rotation.
* `SECTION_READ` — prismatique 0.0.1 source (`hrtem/image.py:376-388, 203-206, 427-434`;
  `hrtem/output.py:172-176, 371-389, 550-552`; `hrtem/sim.py:425-442`;
  `sample.py:123-134, 1787-1930, 2366, 2474-2480`; `tilt.py:149-155, 508-530, 655-685`;
  `cbed.py:180-191`), embeam 0.0.1 (`__init__.py:137-149`, `constants.py:39-97`), and all
  3058 lines of the target repository.
* `DERIVED_HERE` — the identity `h = Δφ/(2π g·n̂)`; `g·(h n̂) = 4m/3` for (2,−2,0) with
  `h = m d₁₁₁`, hence `Δφ = 8πm/3` and the factor-4 wrap; the diamond structure-factor rule
  and the (666) extinction; the sideband-dominance threshold `|Δ| > 2 arctan(π/2) = 2.0078` rad;
  the glancing-incidence footprint arithmetic.
* `UNVERIFIED` — the intended sign of the beam tilt (never stated in the repository); whether a
  weak, non-kinematic (666) exists in real Si; every bibliographic claim about the contents of
  [B01]–[B15] and [P01]–[P07], none of which I read (they are outside this audit's scope and
  are covered by report B).
* `PROJECT_INPUT` — the instruction file's statements about the laboratory, the biprism and
  the Si(100) samples; used only as context, never as evidence for code behaviour.

**END OF REPORT.**
