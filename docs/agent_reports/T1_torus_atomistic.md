# T1: half-torus surface feature on Si(001), atomistic structure and small multislice runs

Agent T1 (second smoke test requested by Ali). Branch claude/electron-holography-orchestration-nakd7r;
nothing committed or pushed by this agent. Beam energy 200 keV throughout (300 keV never used).
Status of every multislice output below: UNVALIDATED (finite-cell build-up not converged, no
physical absorption, report M2 section 10).

## 0. Log

- 02:08 UTC: read shapes.py (fixed shared definition, not modified), structure/ (si001, lattice,
  checks), forward/contracts.py, forward/cell.py, forward/multislice/, M2 report sections 5, 7, 10,
  docs/05 section 4.2. Angle from the engine's MIP (B32): V0 = 13.9028 V (Kirkland independent
  atom), (0,0,8) external angle 16.1347 mrad, internal 18.4719 mrad; build-up length for
  D = 20 A: 1082.6 A along z.
- 02:14 UTC: wrote reflection_holo/structure/features.py (builder + assertions (a) to (g)) and
  reflection_holo/forward/feature_cell.py (ReflectionCell via forward.cell.build_reflection_cell
  unchanged + feature-aware checks F1 to F4). Full-size demo structures built (y 27 a = 146.63 A,
  z 276 a = 1498.93 A, 37 layers, R = 50 A, r = 12 A, ring centre (73.32, 1000.0) A): trench
  547 662 atoms (3 786 removed), 14.3 s, peak RSS 1.33 GB; ridge 554 721 atoms (3 273 added),
  12.8 s, peak RSS 1.35 GB. All builder assertions passed.
- 02:17 UTC: first run attempt (trench) computed its exit wave but was refused at the manifest
  step: `write_manifest` requires the outputs root to be a directory named `outputs`
  (ValueError, verbatim: "manifests are written under an 'outputs' directory, got
  .../scratchpad/torus/ms_trench"). The partial outputs (exit wave without manifest) were deleted;
  the engine outputs now go to ms_<kind>/outputs/{exit_waves,manifests}. Rerun started 02:23 UTC.
- 02:21 UTC: tests written: tests/structure/test_features_torus.py (30 tests, 30 passed in 11.6 s
  on first run) and tests/forward/test_feature_cell.py (6 passed in 2.2 s).

## 1. Files (new; nothing existing was modified; shapes.py untouched)

| file | content |
|---|---|
| reflection_holo/structure/features.py | builder `build_si001_with_feature`, flat reference `build_si001_flat_reference`, `Si001FeatureStructure`, `verify_feature_structure` and one function per assertion |
| reflection_holo/forward/feature_cell.py | `build_feature_reflection_cell` (calls forward.cell.build_reflection_cell unchanged), `check_feature_geometry` (F1 to F4) |
| scripts/torus/run_torus_multislice.py | demo case (every value labelled), estimate, run, manifest |
| tools/plots/torus_atomistic.py | supercell_{trench,ridge}.png and exitwave_{trench,ridge}.png from the saved files |
| tests/structure/test_features_torus.py | 30 tests: every assertion on the built and on corrupted structures |
| tests/forward/test_feature_cell.py | 6 tests: cell layout, F1 to F3 passing and failing |

## 2. API

```python
build_si001_with_feature(*, azimuth_uvw, azimuth_label, feature: HalfTorus, extent_y_A, extent_z_A,
                         depth_layers, lattice_parameter_A, lattice_label, ring_margin_A,
                         vacuum_above_A) -> Si001FeatureStructure
build_si001_flat_reference(*, azimuth_uvw, azimuth_label, extent_y_A, extent_z_A, depth_layers,
                           lattice_parameter_A, lattice_label, vacuum_above_A)
verify_feature_structure(s) -> dict            # re-runs (a) to (g) on s.positions_A
build_feature_reflection_cell(structure, *, vacuum_above_flat_surface_A, depth_below_A,
                              bulk_absorber_A, top_absorber_A, entrance_vacuum_z_A) -> ReflectionCell
check_feature_geometry(cell, *, beam, theta_out_ext_rad, theta_int_rad, buildup_depth_A,
                       footprint_margin_A) -> dict
```
All arguments keyword-only and required (no defaults). `extent_y_A`, `extent_z_A` must be integer
numbers of in-plane periods (a at <100>, a/sqrt(2) at <110>), otherwise refused (no rounding).
`Si001FeatureStructure` fields: positions_A (N, 3, slab frame), species "Si", Z = 14, cell_A,
pbc (False, True, True), frame, layer_index, crystal_origin_slab_A = 0, feature, feature_sites_A
(removed or added sites), request, metadata. metadata["feature"]: kind, centre, R, r, label,
source, project_input "item 13", x_surface_A, n_removed / n_added, top_layer_x_range_A;
metadata["checks"]: the numbers of every assertion; metadata["terrace_map"]: ONE flat terrace
(compatibility with forward.cell).

Construction: one diamond lattice (crystal origin at the slab origin, `lattice.diamond_sites_quarter`,
generated in 120 A chunks along z for memory only), flat slab = layers 0 .. depth_layers-1; trench
removes the slab sites with `feature.contains(x - x_surface, y, z)`; ridge adds the sites of the SAME
lattice above the slab where `contains` holds. No site is moved.

## 3. Assertions and stated tolerances (all run inside the builder; each tested)

(a) every atom on a site of one diamond lattice (1e-6 A) and obeying the feature rule at its site;
(b) half-open periodic window (1e-6 A), no duplicates under the PBC (0.5 A), count = analytic
flat-slab count -/+ feature sites from an INDEPENDENT enumeration over the ring's bounding box;
ring inside the cell with the stated margin ring_margin_A >= one in-plane period;
(c) minimum distance = a sqrt(3)/4 (1e-6 A), atoms below the lowest top layer 4-coordinated, no
isolated atom, every ridge atom bonded to the layer below;
(d) |N - n V| <= n (a/8) S, n = 8/a^3, V = pi^2 R r^2, S = 2 pi^2 R r + 4 pi R r (curved half
surface + flat annulus): the atoms in a shell of half the (001) layer spacing around the surface,
relative tolerance (a/8) S/V (18.5 % at R = 50, r = 12 A). A stated order-of-magnitude bound, not
a rigorous lattice-point bound. The layer x_rel = 0 is in the trench and not in the ridge, a
predicted bias of +-n (a/8) 4 pi R r = +-255.6 atoms, recorded;
(e) top-layer height map of the built atoms (per layer, the nearest lattice site of the layer to
each grid point is looked up among the built atoms; top = highest present layer; grid 0.25 A over
the ring box + 8 A) equals `layer_height_A(y, z, layer_spacing_A=a/4)` at every grid point more
than a/sqrt(2) = 3.84 A (one in-layer lattice spacing) from the ring boundary. INTERPRETATION: the
"ring boundary" is every circle where layer_height_A jumps (the rims AND each a/4 terrace edge);
equality is exact beyond the covering radius a/2 = 2.72 A of the layer net. With the rims alone
as the boundary the assertion would FAIL inside the ring, because near the rims the ideal
terraces are 0.1 to 1.3 A wide, narrower than the 3.84 A in-layer spacing (numbers in section 4);
(f) ring box + margin inside the window, >= 4 intact layers under the deepest removed layer,
ridge top below the box top, measured on the feature sites;
(g) right-handed frame, x = [001], z = beam azimuth.

## 4. Demo structures (ASSUMPTION B20 azimuth [100], B33/B34 feature, B2 lattice)

Cell y = 27 a = 146.634 A (>= 2R + 2r + 20 = 144 A), z = 276 a = 1498.93 A, 37 (001) layers
(flat top layer at 48.878 A), R = 50 A, r = 12 A, ring centre (y, z) = (73.317, 1000.0) A,
ring margin 2a = 10.86 A (measured gaps 11.32 A in y, 938.0 / 436.9 A in z).

| | trench | ridge |
|---|---|---|
| atoms | 547 662 | 554 721 |
| flat slab (analytic) | 551 448 | 551 448 |
| removed / added (built = independent enumeration) | 3 786 | 3 273 |
| n V (half-torus volume x density) | 3 549.0 | 3 549.0 |
| deviation (tolerance +-657.2) | +237.0 | -276.0 |
| deviation minus predicted flat-face bias (+-255.6) | -18.6 | -20.4 |
| layers changed | 0 .. -8 removed, floor at -9 a/4 = -12.22 A | +1 .. +8 added, crest +8 a/4 = +10.86 A |
| height map: grid points / checked / checked inside the ring | 313 600 / 167 108 / 12 728 | 313 600 / 167 844 / 12 728 |
| disagree within the excluded band | 35.7 % | 35.3 % |
| disagree inside the ring footprint (all points) | 39.6 % | 36.6 % |
| largest boundary distance of a disagreement (<= a/2 = 2.72 A) | 2.48 A | 2.42 A |
| coordination 1 / 2 / 3 / 4 | 56 / 29 587 / 670 / 517 349 | 35 / 29 610 / 601 / 524 475 |
| build time, peak RSS | 14.3 s, 1.33 GB | 12.8 s, 1.35 GB |

Inside the ring only the band within 1.26 A of the ring centre line is farther than 3.84 A from
every terrace edge, so the height-map equality is verified there and outside the ring; elsewhere
inside the ring it is not assertable at this lattice spacing (the disagreement fraction above).

## 5. Multislice runs (UNVALIDATED: finite-cell build-up, no absorption B30, M2 section 10)

Setup (scripts/torus/run_torus_multislice.py; every value in case_<kind>.json with its label):
Kirkland independent-atom potential (abTEM 1.0.10 functions), static lattice (ASSUMPTION), no
physical absorption (ASSUMPTION B30), glancing angle 16.1347 mrad = external angle of the (0,0,8)
internal Bragg condition with the engine's MIP 13.9028 V (B32; recomputed independently, agreement
< 5e-4 V asserted), azimuth [100] (B20), exact propagator, 2/3 band limit, complex128, numpy, 4
threads (OMP/OPENBLAS/MKL/NUMEXPR = 4, manifest thread check "consistent"). Cell: depth below the
flat surface 48.88 A (bulk absorber 15 A, sin^2, 100 V, NUMERICAL), vacuum above the flat surface
60 A, top absorber 10 A, entrance vacuum 20 a/4 = 27.15 A; box 118.88 x 146.63 x 1526.08 A; grid
945 x 1134 (dx 0.1258, dy 0.1293 A, derived), dz = a/4 = 1.3577 A, 1124 slices (every slice holds
one atomic plane at its upstream edge: max offset from the slice centre 0.679 A, recorded). Sheet
beam H = 22 A, sin^2 edges 2 A, bottom 1 A above the flat surface at launch (0.56 A at the front
face). The ring (crystal z 938 to 1062 A, i.e. 0.626 to 0.709 of the crystal length) lies in the
downstream half and inside the fully lit footprint core (cell z 186 to 1301 A) with clearances
779 A upstream and 212 A downstream (asserted >= 100 A).

Engine geometry assertions (forward.cell.check_reflection_geometry, run inside the engine): all
passed for all three cells (item 2 margin 60.0 > 46.63 A; item 3 footprint 1363 A < 1499 A; item 4
build-up 1464 A available > 1083 A required; clean depth 33.9 > 20 A). They are made for the FLAT
surface (the only terrace). Feature-aware checks F1 to F3 passed: vacuum above the ridge crest
49.14 > 46.63 A (trench 60.0 A); clean depth below the trench floor 21.66 > 20 A (ridge 33.88 A).
F4, recorded: read with the feature extremes as terrace surfaces, the engine's assertions would
demand a crystal of 1840 A (trench) / 1756 A (ridge) instead of 1083 A; the shadow / blocked-view
length of the feature is 757 A (trench) / 673 A (ridge), i.e. longer than the ring.

| run | atoms | estimate (x1.5) | simulate | structure build | peak RSS |
|---|---|---|---|---|---|
| trench | 547 662 | 213 s | 187.6 s | 13.3 s | 1.33 GB |
| ridge | 554 721 | 163 s | 207.3 s | 12.5 s | 1.35 GB |
| flat reference | 551 448 | 185 s | 196.7 s | 10.1 s | 1.34 GB |

(load average 3 to 5: another agent shared the 4 CPUs; engine arrays ~200 MB per run.) No cell
shrinking was needed. Outputs: <scratchpad>/torus/ms_{trench,ridge,flat}/outputs/exit_waves/
torus_<kind>_r0000.npz and outputs/manifests/torus_<kind>_<UTC>.json (package versions, engine
commit and dirty flag, repository commit 2471f76 + diff hash, precision complex128, seed None
(static), threads, input hashes of structure_<kind>.npz and the exit wave, case JSON hash,
configuration_sha256, validation status). All exit waves are finite.

Quick-look numbers (specular beam selected with a 0.2 1/A aperture about +sin(theta)/lambda;
UNVALIDATED, not to be used as results): specular power relative to the flat reference 0.872
(trench), 0.966 (ridge); specular phase difference to the flat reference over pixels where both
amplitudes exceed 5 % of their maximum: median |dphi| 0.144 rad (trench), 0.044 rad (ridge), 95th
percentile 0.54 / 0.60 rad; in the y strips outside the ring (y < 11.3 or > 135.3 A) median
|dphi| 0.007 / 0.004 rad. The largest differences sit at y ~ 25 and 120 A (the ring crossings at
y_c -+ R) and 5 to 20 A above the flat surface in the exit plane.

## 6. Figures (<scratchpad>/torus/figures/)

supercell_trench.png, supercell_ridge.png: (a) top view of the top-layer height map of the built
atoms (sequential single-hue "Blues", colour bar in A); (d) built top-layer height versus
rho - R (all azimuths) against the continuous half circle and the ideal a/4 terraces (1:1);
(b), (c) cross-sections through the ring centre along y and along z (two atomic planes; removed
sites open circles, added ridge atoms blue). exitwave_trench.png, exitwave_ridge.png: |psi|,
arg psi (cyclic "twilight"), log Fourier intensity with the specular beam and the selection
circle marked, raw phase minus the flat reference, specular |psi_s|, demodulated specular phase,
specular phase minus the flat reference, specular amplitude ratio; masked pixels mid grey.

## 7. Tests (verbatim)

```
$ venv/bin/pytest -q tests/structure
........................................................................ [ 44%]
........................................................................ [ 88%]
...................                                                      [100%]
163 passed in 13.61s
$ venv/bin/pytest -q tests/forward/test_feature_cell.py
......                                                                   [100%]
6 passed in 2.15s
```
Corrupted-structure tests (each must raise StructureAssertionError): displaced atom (a); a true
lattice site added above the trench's flat surface (a, feature rule); duplicate atom and periodic
image (b); missing atom far from the ring (b, count); atom moved 0.3 A towards a neighbour (c);
count doubled or wrong radius (d); missing flat top-layer atom, ridge crest layer removed, trench
floor refilled (e); feature site outside the ring box (f); left-handed frame (g), wrong-azimuth
frame (a).

## 8. NOT RUN / open

- Convergence of any multislice number with cell length, absorption, pixel, slice thickness or
  aperture: NOT RUN. The M2 section 10 finding applies: without absorption the reflection does
  not converge along z, so every exit wave here is UNVALIDATED and no phase or height may be read
  from it. Engine rung 2 and the abTEM cross-check: NOT RUN (engine status).
- Frozen phonons, a 2x1 reconstruction, an overlayer, wall relaxation: NOT IMPLEMENTED / not run.
- <110> azimuth: the builder supports and tests it; no multislice run.
- Hologram formation, reconstruction and the geometric-engine comparison of these exit waves:
  NOT RUN here (T2 / pipeline agent).
- The height-map assertion (e) is verified only beyond 3.84 A from every terrace edge of the ring
  (inside the ring: a 2.5 A wide band on the centre line); the interpretation of "ring boundary"
  as all terrace edges is mine (section 3) and should be confirmed.
- Registry rows B33/B34 are to be added by the orchestrator (the source strings already cite them).
- tests/structure was run while no other job of mine was running; the full repository test suite
  was NOT RUN by this agent.
