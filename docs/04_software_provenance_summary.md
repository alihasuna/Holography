# Software provenance summary (full report in `docs/agent_reports/D_software_provenance.md`)

Status: 2026-09-21; revision 3, 2026-09-22 (public documentation read: P04 in full; the prismatique
rendered docs and the Prismatic project pages in the parts listed in
`docs/agent_reports/L2_computational_open_sources.md` section 1).
Established from version-matched source code (prismatique 0.0.1 and 0.0.4,
embeam 0.0.1 and 0.0.5 from PyPI; Prismatic from `prism-em/prismatic` at commit d155fb9,
2026-01-30, `setup.py` version 1.2.0, the HRTEM-capable 2.x generation) and by exercising the Python
API in a clean virtual environment without the compiled engine. No simulation was run; engine
behaviour is SECTION_READ of the C++/CUDA source and has not been confirmed against an executed
output file (report D, section 7, item 3, names the one small run that would confirm it).

## Decisive facts

| Fact | Locator | Label |
|---|---|---|
| `/data/image_wavefunctions` is 5-D `(atomic config, defocus, tilt, r_y, r_x)`, complex64; image pixel is twice the potential pixel; `r_y` descends; tilts (mrad) in `/metadata/tilts` | prismatique `hrtem/sim.py:1063-1073, 1487`; `_signal.py:261-278`; D command 16 | SECTION_READ + REPRODUCED |
| The saved wave is the multislice exit wave Fresnel back-propagated by half the cell length to the supercell mid-plane, times `exp(-i chi)` if any aberration is set; with the repository's settings `chi = 0` but the back-propagation is unconditional | Prismatic `PRISM02_calcSMatrix.cpp:105-116, 433-445`; CUDA `:889-895, 1008-1014` | SECTION_READ |
| The HRTEM path is plain multislice per plane wave reusing the S-matrix container; not PRISM interpolation | `HRTEM_entry.cpp:120-153`; `PRISM02_calcSMatrix.cpp:738-797` | SECTION_READ |
| Propagator is paraxial Fresnel `exp(-i pi lambda dz q^2)`; anti-aliasing at half Nyquist (rectangular per axis); tilt ceiling `lambda/(4 dx)` | `PRISM02_calcSMatrix.cpp:62-79, 105-107`; `params.h:241-242` | SECTION_READ |
| Beam tilt is one FFT-grid Fourier component set to 1 (quantised, entrance plane only); the tilt "window" selects every grid tilt inside it: 1309 simulated tilts for the repository's 74-point sweep | `PRISM02_calcSMatrix.cpp:391`; prismatique `tilt.py:655-685`; D command 15 | SECTION_READ + REPRODUCED |
| Periodic boundaries in x and y; no absorbing boundary anywhere in Prismatic; `absorbing_layers` is not a prismatique keyword (`TypeError`, swallowed by the repository) | `discretization.py:168-175`; `PRISM01_calcPotential.cpp:474-475`; D command 14 | SECTION_READ + REPRODUCED |
| Thermal effects off by default and never enabled by the repository; the per-atom sigma 0.076 A (per-axis RMS) is inert; complex waves are stored per configuration, never averaged; only the intensity file averages | `thermal.py:375-385`; `hrtem/sim.py:1490-1494, 1546-1549` | SECTION_READ + REPRODUCED |
| Tilt weights use an exact float comparison against the offset; the repository's snapped offset never matches, so the intensity file is NaN | `hrtem/sim.py:1604-1609`; D command 17 | SECTION_READ + REPRODUCED |
| `.xyz` z is mirrored by the engine (`z = L_z - z_file`); benign for the inspected slab (mirror perpendicular to [110] is a lattice symmetry) | `sample.py:280-285`; `PRISM01_calcPotential.cpp:145-146`; A section 2a | SECTION_READ + REPRODUCED |
| `prismatique` does not declare `pyprismatic`; PyPI `pyprismatic` (2017, 1.1.x) has no HRTEM mode; the engine used is unrecorded by the repository. Correction (L2 E23): the engine need not be built from source, because prismatique documents a prebuilt conda-forge `pyprismatic=2.*` (uploads 2021-10-12 to 2023-10-07); which Prismatic commit those builds used is UNVERIFIED, so the conda build string must be recorded | `prismatique-0.0.1.dist-info/METADATA`; D command 13; L2 rows B23, B24 | REPRODUCED (PyPI part); SECTION_READ (conda-forge route) |
| `hrtem/sim.py` is byte-identical in prismatique 0.0.1 and 0.0.4; the README's pin rationale (schema drift) is unsupported | D command 14 group | REPRODUCED |
| Prismatic upstream is no longer actively maintained (January 2026 notice) and recommends abTEM | `prismatic-cpp/README.md` | SECTION_READ |
| Licences: Prismatic GPL-3.0, prismatique GPLv3, the inspected repository MIT | `LICENSE`, `METADATA`; L2 rows C4, B22 | SECTION_READ |
| prismatique 0.0.1's `tilt.step_size` raises `TypeError` with embeam 0.0.4 or later (`tilt.py:548`; fixed upstream in v0.0.2; the simulation path `tilt.series`, `hrtem.sim` does not call it, L2 B-V4); `embeam==0.0.1` must be pinned together with `prismatique==0.0.1`, and `tools/provenance_checks/tilt_test.py` fails with the embeam the resolver installs today | L2 section B.3, B-V3; source map SM18 | REPRODUCED |
| Prismatic's citation page asks users to cite three papers: Ophus 2017 (P04), Pryor et al. 2017 (Adv. Struct. Chem. Imaging 3, 15) and Rangel DaCosta et al. 2021 (P05), with no GPU condition (report D's advice to cite Pryor only for the GPU path is superseded) | prism-em.com citation page; L2 rows C3, E25, E26; SM20 | SECTION_READ |
| Public documentation confirms the half-maximum-angle anti-aliasing aperture, the grid-quantised entrance-plane tilt, periodic x-y boundaries and the absence of an absorber (P04 p. 3, Eq. (6), p. 4; S01 sec. 2.3.1, 2.6.18, 2.10.3). The back-propagation of the saved HRTEM wave by half the supercell length is stated in NO public document read (P04 predates HRTEM mode; P05 not read) and rests on the C++ source only | L2 rows E4, E7, E10, E19 | SECTION_READ (docs and source); back-propagation source-only |
| The engine's own default is thermal effects ON, the wrapper's default OFF; any direct Prismatic or pyprismatic run must set it explicitly. The aberration-file example on the Prismatic website contradicts the engine's convention (m = radial power) | L2 rows E16, E30 | SECTION_READ |

## Consequences for the final repository

* A loader must assert the dataset name, the five `dim` attributes, the dtype, the pixel size from
  `/metadata/r_x` and `/metadata/r_y` (never from `meta.json`), the tilt by value from `/metadata/tilts`,
  all subsets, and the plane of the wave (mid-plane, already propagated by `-L_z/2`).
* Prismatic cannot be the reference engine for a reflection cell: periodic along the surface normal
  with no absorber, half-Nyquist band, paraxial propagator, mandatory back-propagation, tilt window
  semantics, unmaintained upstream. abTEM (exact propagator, 2/3 band, explicit exit wave, ensemble
  switch; tilt documented for angles below about 17 mrad, so 24 to 48 mrad must be tested) is the
  packaged cross-check; a custom kernel supplies the absorber and the declared output plane.
* Citations for any Prismatic-based figure: P04, Pryor et al. 2017 and P05 (SM20). Pin `embeam==0.0.1`
  with `prismatique==0.0.1` (SM18). Before any Prismatic number is cited as a benchmark, the one tiny
  engine run of report D section 7 item 3 must confirm the mid-plane back-propagation, because no
  public document states it.
* Provenance to record with every run: package versions, engine commit and build flags, licence,
  precision (float32 by default), seeds and thread count (frozen-phonon seeding depends on the thread
  index), input hashes, configuration hash, repository commit.

## Scripts

`tools/provenance_checks/` contains the four API-level checks (report D commands 14 to 17) and the
stub that lets `import prismatique` succeed without the engine; see its README.
