# M2: reflection multislice engine (custom numpy/cupy kernel), build report

Prepared: 2026-09-22 (Phase 3, agent M2). Written incrementally; the final state is section 9.
Scope (orchestrator task): `reflection_holo/forward/cell.py`, `reflection_holo/forward/multislice/`,
`tests/forward/`, this report. Interface: `reflection_holo/forward/contracts.py` (ReflectionCell,
ExitWave), unchanged; only metadata keys are added.

Status label of the engine: UNVALIDATED for atomistic reflection. Rung 1 (refraction-only analytic
limit) and rung 3 (continuum null tests) of the docs/05 section 4.4 ladder are run below; rung 2
(Bragg-case two-beam phase sweep), the abTEM cross-check (transmission and reflection-like
configurations, docs/05 section 4.3 engine plan) and the flat-surface rocking curve against a
dynamical solver are NOT RUN.

## 0. Log

* started: read docs/05 4.3, 4.4, 9.1; docs/03 3, 5; physics_conventions; model_assumptions A1, A2,
  B6, B7; 06 items 3, 12, 21; contracts.py; structure/si001.py; constants; geometry/.
* abTEM 1.0.10 was already installed in the venv (D3 section 0.3); its parameterisation functions
  were read in `abtem/parametrizations/__init__.py` and `abtem/parametrizations/functions/lobato.py`,
  `kirkland.py`; `projected_scattering_factor(symbol)(k2)` returns the 2D Fourier transform of the
  infinite projected potential in V A^3 (checked here by a Hankel transform against
  `projected_potential(r)`: 222.45 vs 222.80 V A at r = 0.2 A, 19.73 vs 19.76 at 1.0 A with the
  transform truncated at k = 60 1/A).
* orchestrator decisions after D3 applied: Kirkland parameterisation only (Lobato refused, D3 F5);
  abTEM imported lazily as an OPTIONAL dependency with a clear error, version 1.0.10 and commit
  164e644f recorded; no abTEM code or table copied; `potential_mean_inner_potential_V(potential)`
  exposed and the value recorded in every ExitWave (13.903 V for Kirkland Si, D3 F16); abTEM 1.0.10
  has only a Fresnel propagator, so an abTEM cross-check compares like with like only in Fresnel
  mode; slice ordering (below) differs from abTEM's transmit-then-propagate.
* The potential is built as D3 section 8 recommends (Kirkland `projected_scattering_factor` times
  the exact structure factor of the slice's atoms, divided by the pixel area); abTEM's
  `ScatteringFactorProjectionIntegrals("kirkland").integrate_on_grid`, with a fresh integrator per
  grid, is used as a cross-check in tests/forward, not in the engine.

## 1. Slice ordering and scheme

Symmetric split step: `psi(L) = P(dz/2) T_{N-1} P(dz) ... P(dz) T_0 P(dz/2) psi_0`, `L = N dz`, slice
i = `[i dz, (i+1) dz)`, each slice's potential acting at its centre. abTEM 1.0.10 transmits and then
propagates the full slice (potential at the slice entrance, output at the far face); the two
orderings differ by half-slice propagations at the ends (D3 blocker 9). The transmission function
and the wave are both band-limited (as abTEM does). The tilt is an entrance-plane Fourier component.

## 2. Rung 1: refraction-only analytic limit (docs/05 section 4.4)

Case (`tests/forward/ladder_cases.py::rung1_case`): flat half-space of constant `V0 = 12.0 V`
(ASSUMPTION B1, passed explicitly), sharp cell-averaged step, no physical absorption (ASSUMPTION,
item 21), sheet beam H = 48 A with 8 A sin^2 edges, 2 A above the surface, projected onto downward
components; 1D grid (ny = 1); numerical absorbers sin^2, 100 V, 15 A bulk side and >= 10 A top.
The exit plane is placed where the refracted ray of the TOP edge of the beam is 20 A deep.
Measurement: `r(f) = Psi_exit(+f) exp(+i 4 pi f x_s) / (Psi_0(-f) P_L(f))` per incident bin, compared
with `r = (q1 - q2)/(q1 + q2)`, `q2 = sqrt(q1^2 + dK^2)`, dK from SM04 (analytic phase: pi);
refracted angle from the |psi|^2-weighted phase gradient over the central third of the refracted
sheet, against `theta_int_from_ext_rad` (SM04).

Two findings during the study (both fixed before any tolerance was set):
1. Per-bin ripples of 1 to 2 % in |r|: the sin^2-edged sheet has an upward-travelling spectral tail
   (~1e-3) that reaches the exit plane without touching the surface. Fix: the launched wave is
   projected onto f_x < 0 (illumination.py docstring).
2. A 3.5e-3 rad phase residual independent of dx and of the propagator: incomplete scattering of the
   trailing part of the packet when the top-edge refracted ray was only 5 A deep at the exit plane;
   20 A removes it (6e-5 rad).

Convergence study (central incident bin; `err` = |r|/|r_analytic| - 1; `model` = -((q1+q2) dx)^2/12,
the measured second-order discretisation law of the cell-averaged step; `ph` = arg(r/r_analytic);
`dth` = theta_int(measured) - theta_int(SM04) in mrad):

```
exact    10.00 mrad dx=0.0500 dz=1.0 |r|=0.13068 analytic=0.13138 err=-0.538% model=-0.695% err-model=+0.157% ph=-3.51e-04 dth=+8.5e-04 t=2.3s
exact    10.00 mrad dx=0.0250 dz=1.0 |r|=0.13136 analytic=0.13138 err=-0.020% model=-0.174% err-model=+0.154% ph=-2.48e-04 dth=+7.0e-04 t=4.0s
exact    10.00 mrad dx=0.0125 dz=1.0 |r|=0.13153 analytic=0.13138 err=+0.113% model=-0.043% err-model=+0.157% ph=-2.25e-04 dth=+5.5e-04 t=10.7s
exact    10.00 mrad dx=0.0250 dz=2.0 |r|=0.13138 analytic=0.13138 err=-0.003% model=-0.174% err-model=+0.171% ph=+3.58e-05 dth=+4.8e-04 t=2.1s
exact    10.00 mrad dx=0.0250 dz=0.5 |r|=0.13135 analytic=0.13138 err=-0.024% model=-0.174% err-model=+0.149% ph=-3.44e-04 dth=+7.0e-04 t=8.2s
exact    16.47 mrad dx=0.0500 dz=1.0 |r|=0.05656 analytic=0.05748 err=-1.602% model=-1.588% err-model=-0.014% ph=-1.22e-04 dth=+1.1e-03 t=1.3s
exact    16.47 mrad dx=0.0250 dz=1.0 |r|=0.05725 analytic=0.05748 err=-0.404% model=-0.397% err-model=-0.007% ph=+5.20e-05 dth=+1.1e-03 t=2.4s
exact    16.47 mrad dx=0.0125 dz=1.0 |r|=0.05742 analytic=0.05748 err=-0.100% model=-0.099% err-model=-0.001% ph=+8.11e-05 dth=+1.2e-03 t=6.3s
exact    16.47 mrad dx=0.0250 dz=2.0 |r|=0.05726 analytic=0.05748 err=-0.376% model=-0.397% err-model=+0.022% ph=+5.19e-04 dth=+1.1e-03 t=1.2s
exact    16.47 mrad dx=0.0250 dz=0.5 |r|=0.05724 analytic=0.05748 err=-0.411% model=-0.397% err-model=-0.014% ph=-1.02e-04 dth=+1.2e-03 t=4.8s
exact    30.00 mrad dx=0.0500 dz=1.0 |r|=0.01780 analytic=0.01873 err=-4.960% model=-4.875% err-model=-0.085% ph=+8.69e-05 dth=-6.6e-04 t=2.0s
exact    30.00 mrad dx=0.0250 dz=1.0 |r|=0.01849 analytic=0.01873 err=-1.254% model=-1.219% err-model=-0.035% ph=+3.94e-04 dth=-6.5e-04 t=4.6s
exact    30.00 mrad dx=0.0125 dz=1.0 |r|=0.01867 analytic=0.01873 err=-0.322% model=-0.305% err-model=-0.017% ph=+4.75e-04 dth=-6.4e-04 t=8.9s
exact    30.00 mrad dx=0.0250 dz=2.0 |r|=0.01850 analytic=0.01873 err=-1.203% model=-1.219% err-model=+0.015% ph=+1.26e-03 dth=-6.5e-04 t=1.6s
exact    30.00 mrad dx=0.0250 dz=0.5 |r|=0.01849 analytic=0.01873 err=-1.267% model=-1.219% err-model=-0.048% ph=+1.06e-04 dth=-6.5e-04 t=6.7s
fresnel  10.00 mrad dx=0.0500 dz=1.0 |r|=0.13068 analytic=0.13138 err=-0.533% model=-0.695% err-model=+0.162% ph=-3.53e-04 dth=+9.6e-04 t=2.2s
fresnel  10.00 mrad dx=0.0250 dz=1.0 |r|=0.13137 analytic=0.13138 err=-0.015% model=-0.174% err-model=+0.159% ph=-2.46e-04 dth=+7.4e-04 t=4.3s
fresnel  10.00 mrad dx=0.0125 dz=1.0 |r|=0.13154 analytic=0.13138 err=+0.118% model=-0.043% err-model=+0.161% ph=-2.24e-04 dth=+7.9e-04 t=10.8s
fresnel  10.00 mrad dx=0.0250 dz=2.0 |r|=0.13139 analytic=0.13138 err=+0.002% model=-0.174% err-model=+0.176% ph=+3.63e-05 dth=+7.1e-04 t=2.0s
fresnel  10.00 mrad dx=0.0250 dz=0.5 |r|=0.13136 analytic=0.13138 err=-0.019% model=-0.174% err-model=+0.154% ph=-3.43e-04 dth=+7.3e-04 t=8.4s
fresnel  16.47 mrad dx=0.0500 dz=1.0 |r|=0.05657 analytic=0.05748 err=-1.589% model=-1.588% err-model=-0.001% ph=-1.20e-04 dth=+1.5e-03 t=1.3s
fresnel  16.47 mrad dx=0.0250 dz=1.0 |r|=0.05726 analytic=0.05748 err=-0.391% model=-0.397% err-model=+0.006% ph=+6.00e-05 dth=+1.5e-03 t=2.4s
fresnel  16.47 mrad dx=0.0125 dz=1.0 |r|=0.05743 analytic=0.05748 err=-0.085% model=-0.099% err-model=+0.014% ph=+8.91e-05 dth=+1.4e-03 t=6.4s
fresnel  16.47 mrad dx=0.0250 dz=2.0 |r|=0.05727 analytic=0.05748 err=-0.363% model=-0.397% err-model=+0.034% ph=+5.26e-04 dth=+1.5e-03 t=1.2s
fresnel  16.47 mrad dx=0.0250 dz=0.5 |r|=0.05725 analytic=0.05748 err=-0.399% model=-0.397% err-model=-0.002% ph=-9.70e-05 dth=+1.4e-03 t=4.8s
fresnel  30.00 mrad dx=0.0500 dz=1.0 |r|=0.01781 analytic=0.01873 err=-4.918% model=-4.875% err-model=-0.042% ph=+9.10e-05 dth=-1.4e-04 t=1.8s
fresnel  30.00 mrad dx=0.0250 dz=1.0 |r|=0.01850 analytic=0.01873 err=-1.209% model=-1.219% err-model=+0.010% ph=+3.96e-04 dth=-1.0e-04 t=4.5s
fresnel  30.00 mrad dx=0.0125 dz=1.0 |r|=0.01867 analytic=0.01873 err=-0.278% model=-0.305% err-model=+0.026% ph=+4.65e-04 dth=-1.0e-04 t=8.7s
fresnel  30.00 mrad dx=0.0250 dz=2.0 |r|=0.01851 analytic=0.01873 err=-1.159% model=-1.219% err-model=+0.060% ph=+1.26e-03 dth=-1.1e-04 t=1.7s
fresnel  30.00 mrad dx=0.0250 dz=0.5 |r|=0.01850 analytic=0.01873 err=-1.223% model=-1.219% err-model=-0.004% ph=+1.06e-04 dth=-1.3e-04 t=6.7s
```

Reading: |r| converges at second order in dx (16.47 mrad: -1.60, -0.40, -0.10 %; observed order
2.0) and follows the law `-((q1+q2) dx)^2/12` to within 0.18 % at every angle, dx, dz and propagator
(largest residual +0.18 % at 10 mrad, dx-independent). The phase error is at most 4.8e-4 rad at
dz = 1 A (1.3e-3 rad at dz = 2 A, 30 mrad: Strang O(dz^2)). The refracted angle agrees with SM04 to
1.5e-3 mrad (1.5 urad) or better. Exact and Fresnel propagators agree to 0.05 % in |r| (the analytic
limit is the paraxial 1D Schroedinger problem; the non-paraxial correction is O(theta^2)).

Tolerances adopted for the tests (dx = 0.025 A, dz = 1 A):
* |r|: `| err - model | <= 3.5e-3` (2 x the largest residual, 0.176 %);
* phase: `|arg(r / r_analytic)| <= 1.0e-3 rad` (2.1 x the largest dz = 1 A value, 4.75e-4);
* refracted angle: `|dth| <= 5e-3 mrad` (3.3 x the largest, 1.5e-3 mrad);
* convergence: observed order in dx between 0.05 and 0.025 A at 16.47 mrad >= 1.8 (observed 1.99).

## 3. Rung 3: null tests on constant-potential terraces

Case (`ladder_cases.py::rung3_case`): two terraces of constant V0 = 12.0 V (ASSUMPTION B1), step
edges PARALLEL to the beam (y periodic), 16.47 mrad, sheet beam H = 8 A (2 A edges) 2 A above the
upper terrace, exit plane where the top-edge refracted ray is 20 A below the lower surface,
dy = 0.6 A, dz = 1 A. Step phase = arg of the specular beam selected in k-space (circular aperture
of radius 0.5 1/A about (+sin(theta)/lambda, 0)), demodulated at exactly f_c = sin(theta)/lambda and
summed over the central half of each terrace (`analysis.terrace_step_phase`), Delta_phi =
phi(B) - phi(A) with B at height h.

Sub-pixel study (1D, rung-1 geometry): moving the step by a fraction u of a pixel changes the
reflection phase by up to 1.1e-2 rad at dx = 0.1 A, 1.4e-3 at 0.05 A and 2.4e-4 at 0.025 A (third
order); rung 3 therefore runs at dx <= 0.05 A.

Terrace-width study (dx = 0.05 A): with 24 A terraces the errors were 6.9e-3 (h_2pi), 1.7e-3 (a/4),
1.3e-2 (a/2) rad and the upper/lower amplitudes differed by up to 3.3 %; they did not decrease with
dx (0.1 -> 0.05 -> 0.025 A: a/2 -2.0e-2, -1.3e-2, -1.2e-2) nor consistently with a deeper exit plane
or a wider beam; widening the terraces to 40 A reduced them to the values below. The residual is
step-edge diffraction reaching the measured regions.

Study at 40 A terraces (err = measured - (-(4 pi/lambda) h sin theta), wrapped):

```
complex64  dx=0.0500 h2pi      h=+0.7614 dphi=+0.00236 expected=+0.00000 err=+2.36e-03 ampU/ampL-1=+0.508% nx=1836 ny=133 N=1738 t=8.1s
complex64  dx=0.0500 a4        h=+1.3577 dphi=+1.36217 expected=+1.36220 err=-3.71e-05 ampU/ampL-1=-0.677% nx=1868 ny=133 N=1774 t=12.2s
complex64  dx=0.0500 minus_a4  h=-1.3577 dphi=-1.36218 expected=-1.36220 err=+2.00e-05 ampU/ampL-1=+0.681% nx=1868 ny=133 N=1774 t=11.9s
complex64  dx=0.0500 a2        h=+2.7155 dphi=+2.72360 expected=+2.72441 err=-8.13e-04 ampU/ampL-1=+0.362% nx=1915 ny=133 N=1856 t=17.0s
complex128 dx=0.0500 h2pi      h=+0.7614 dphi=+0.00234 expected=+0.00000 err=+2.34e-03 ampU/ampL-1=+0.489% nx=1836 ny=133 N=1738 t=14.0s
complex128 dx=0.0500 a4        h=+1.3577 dphi=+1.36176 expected=+1.36220 err=-4.40e-04 ampU/ampL-1=-0.662% nx=1868 ny=133 N=1774 t=19.3s
complex128 dx=0.0500 minus_a4  h=-1.3577 dphi=-1.36176 expected=-1.36220 err=+4.40e-04 ampU/ampL-1=+0.666% nx=1868 ny=133 N=1774 t=18.1s
complex128 dx=0.0500 a2        h=+2.7155 dphi=+2.72321 expected=+2.72441 err=-1.20e-03 ampU/ampL-1=+0.366% nx=1915 ny=133 N=1856 t=27.2s
complex128 dx=0.0250 h2pi      h=+0.7614 dphi=+0.00359 expected=+0.00000 err=+3.59e-03 ampU/ampL-1=+0.486% nx=3671 ny=133 N=1738 t=67.3s
complex128 dx=0.0250 a4        h=+1.3577 dphi=+1.36266 expected=+1.36220 err=+4.57e-04 ampU/ampL-1=-0.655% nx=3735 ny=133 N=1774 t=65.7s
complex128 dx=0.0250 minus_a4  h=-1.3577 dphi=-1.36266 expected=-1.36220 err=-4.57e-04 ampU/ampL-1=+0.659% nx=3735 ny=133 N=1774 t=55.0s
complex128 dx=0.0250 a2        h=+2.7155 dphi=+2.72483 expected=+2.72441 err=+4.18e-04 ampU/ampL-1=-0.263% nx=3829 ny=133 N=1856 t=64.8s
```

Largest |err| 3.6e-3 rad (h_2pi, dx = 0.025 A); complex64 and complex128 agree to 4e-4 rad. The
reversed step is the same configuration translated by one terrace width in y, so the sign reversal
is exact to round-off in complex128 (it tests the measurement's sign convention, not the physics).
Tolerance adopted: 1.0e-2 rad (2.8 x the largest error) at dx = 0.05 A, complex128.

## 4. Interaction constant, atomic potential, mean inner potential

* sigma(200 keV) = 7.28840e-4 rad/(V A), DERIVED_HERE as 2 pi (T + m_e c^2) lambda / (h c)^2 from
  reflection_holo.constants; equals abTEM `energy2sigma(200e3)` to < 1e-7 relative (D3: 6e-9, CODATA
  2014 vs 2018); 2 k sigma V0 equals k^2 Delta(first order) exactly and differs from the exact SM04
  Delta by 8.4e-6 relative (as documented in physics_conventions).
* Potential: Kirkland (abTEM 1.0.10, commit 164e644f, `KirklandParametrization().
  projected_scattering_factor("Si")`), infinite projection per slice, exact structure factors,
  `V_p = IFFT2[F S] / (dx dy)`. Provenance in ExitWave.metadata["potential"]: parameterisation name,
  abTEM version and commit, source files (`abtem/parametrizations/__init__.py`,
  `abtem/parametrizations/functions/kirkland.py`), data file `kirkland.json` with its SHA-256,
  `provenance_label` SECTION_READ of abTEM source (D3), `parameterisation_label` UNVERIFIED: not
  read by us (SM17).
* Cross-check against a FRESH `ScatteringFactorProjectionIntegrals("kirkland").integrate_on_grid`
  (float64; 5 random Si positions, 9.6 x 6.4 A slice): identical mean (same F(0) and normalisation);
  low-frequency (|f| <= 2.5 1/A) coefficient differences 5.35e-3, 1.62e-3, 2.97e-4, 8.70e-5 of the
  largest coefficient at dx = 0.1, 0.05, 0.025, 0.0125 A, i.e. abTEM's bilinear spreading with sinc
  compensation converges to the exact structure factor used here. Real-space peaks differ by up to
  ~9 % (abTEM smooths sub-pixel atoms). Test tolerance 1e-3 at dx = 0.025 A (3.4 x).
* Mean inner potential of the potential actually used: 13.903 V (Kirkland, a = 5.4309 A; matches D3
  F16), +1.90 V above V0 = 12.0 V (ASSUMPTION B1) and +1.37 V above the DFT 12.53 V. No correction
  towards a sourced V0 is applied (D3 blocker 5: an open modelling decision). Exposed as
  `potential_mean_inner_potential_V(potential)` and recorded in ExitWave.metadata
  ["mean_inner_potential_V"]; the engine uses it for the internal angles of the band and geometry
  assertions, and the smoke run uses it for the (0,0,8) angle (16.1347 mrad instead of 16.4743 mrad
  at 12 V).
* Physical absorption (item 21): required `PhysicalAbsorption(model="proportional", ratio, label)`;
  ratio = 0 accepted only with an ASSUMPTION (or TEST_ONLY) label. The proportional model is the only
  one implemented; no named parameterisation (e.g. Weickenmeier-Kohl) is available: item 21 open.
* Slice assignment: slice i holds atoms with i dz - 1e-9 <= z < (i+1) dz - 1e-9 A. For Si(001) at a
  [110] azimuth with dz = p/4 = 0.9601 A every (1-10) atomic plane lies on a slice boundary, is
  alone in its slice and acts dz/2 downstream (a uniform z-translation of the crystal by 0.48 A);
  half the slices are empty (propagation only).

## 5. (d) Atomistic smoke run (UNVALIDATED)

`tests/forward/test_smoke_atomistic.py` with `smoke_case.py`: Si(001), [110] azimuth (TEST_ONLY),
two 8-period (30.7 A) terraces with an a/2 step PARALLEL to the beam, 200 keV, (0,0,8) specular
condition theta_ext = 16.1347 mrad (with the potential's own MIP 13.903 V), Kirkland, static lattice
(ASSUMPTION), no physical absorption (ASSUMPTION), sheet beam 8 A, numerical absorbers sin^2 100 V
(15 A bulk, 10 A top), build-up depth D = 20 A, exact propagator, 2/3 band, complex64, 4 threads.

Result (run 2026-09-22 23:58 UTC while the pipeline agent's CPU job used ~3 of the 4 cores, load
average 5.9):
```
SMOKE: 159936 atoms, grid 640 x 480 (dx 0.1292, dy 0.1280 A), 1438 slices of 0.9601 A, theta_ext 16.1347 mrad, MIP 13.903 V
SMOKE: build 7.0 s, propagation 38.6 s, total 45.8 s, peak RSS 808 MB
SMOKE: geometric a/2 step phase -21.9522 rad (wrapped -3.1027)
SMOKE: aperture 0.1 1/A: Delta_phi -2.5205 rad, difference to geometric +0.5822 rad, |A_up| 1.2083, |A_low| 1.1850
SMOKE: aperture 0.2 1/A: Delta_phi -2.5218 rad, difference to geometric +0.5809 rad, |A_up| 1.2171, |A_low| 1.2129
```
Rerun after the float64 phase-argument fix of the structure factors (2026-09-23 00:12 UTC, load
average 6.6): identical phases to 1e-4 rad (Delta_phi -2.5205 / -2.5218 rad), build 7.7 s,
propagation 66.1 s, total 73.9 s (< 120 s), peak RSS 808 MB; the runtime varies 46 to 74 s with the
other agent's load.
Peak RSS includes Python, abTEM/numba imports and the structure build; the engine's own arrays for
this grid are ~7 MB (estimate_resources).

The measured a/2 step phase differs from the geometric (translation) expectation by +0.58 rad.
Diagnostic (same case, build-up depth D = 60 A instead of 20 A: 3690 slices, grid 1215 x 480,
420 s under load, `scratchpad/smoke_diag.py`):
```
D=60.0 slices=3690 grid=1215x480 dphi=-1.9765 geo=-3.1027 diff=+1.1261 |A_up|=0.8049 |A_low|=0.9964 t=420s
```
The discrepancy GROWS with the cell length (+0.58 -> +1.13 rad) and the two terraces' amplitudes
diverge (1.2 % -> 19 %), so the first hypothesis (incomplete dynamical build-up) is refuted. A
candidate explanation, NOT TESTED: lateral coupling between the 30.7 A terraces through in-plane
diffraction (the (0,+-1) rods travel at lambda/p = 6.5 mrad in y, i.e. 9 to 24 A over 1400 to
3700 A), with no absorption (item 21 set to zero) to limit it; B4 holds only for terraces much
wider than that spread. The atomistic a/2 null test is therefore NOT PASSED (inconclusive): it needs
terraces >> L lambda/p and a sourced absorption, i.e. an HPC-size run. The smoke run only
demonstrates that the atomistic pipeline executes within budget; its step phase must not be used.

## 6. Files and API

* `reflection_holo/forward/cell.py`: `build_reflection_cell(structure, *, vacuum_above_A,
  depth_below_A, bulk_absorber_A, top_absorber_A, entrance_vacuum_z_A) -> ReflectionCell` (layout
  in `metadata["layout"]`: absorber ranges, lowest/highest surface, z period, entrance vacuum);
  `build_continuum_cell(...)` (structureless terraces, rungs 1 and 3);
  `check_reflection_geometry(cell, *, beam_height_A, beam_x_bottom_A, theta_in_ext_rad,
  theta_out_ext_rad, theta_int_rad, buildup_depth_A)` (spec 4.3 items 1 to 4, called by the engine;
  raises `ReflectionGeometryError`).
* `reflection_holo/forward/multislice/`:
  `physics.py` (energy guard 200 keV, sigma), `grid.py` (derived pixel, "2/3" UNVERIFIED and
  "half_nyquist" SECTION_READ band limits, `check_band`, `fft_friendly`), `backend.py` (numpy with
  scipy.fft workers, or cupy imported lazily; complex64/complex128), `propagator.py` ("exact" with
  evanescent components removed, "fresnel"), `potentials.py` (`AtomicPotential` Kirkland,
  `ContinuumTerracePotential`, `PhysicalAbsorption`, `FrozenPhonons`, `NumericalAbsorber`,
  `potential_mean_inner_potential_V`), `illumination.py` (`SheetBeam`, downward projection),
  `engine.py` (`MultisliceParams`, `run_realisation`, `simulate` (writes the manifest),
  `propagate_slices`, `reflection_setup`, `estimate_resources`), `analysis.py`
  (`terrace_step_phase`, `flat_reflection_coefficient`, `select_beam`, `geometric_step_phase`),
  `exitwave_io.py` (`save_exit_wave`, `load_exit_wave(path, *, expected_plane)` asserting schema,
  axes, units, pixel sizes against the grid, plane, 200 keV, dtype).
* Contract: `ExitWave` unchanged; `psi` axes (x = normal, y = transverse), `plane =
  "exit plane z = L_z (no further propagation)"`, `z_A = L_z`, x0 = 0 at the bottom of the box.
  `psi` is the envelope relative to exp(i k z). Added metadata keys: engine, validation_status,
  carrier, axes, grid, beam (lambda, k, sigma), illumination, theta_out_ext_rad, theta_int_*,
  propagator (kind, evanescent count, paraxial-error estimate), band_limit, slices, absorbers,
  potential (provenance, MIP, absorption, phonons, realised slice statistics),
  mean_inner_potential_V, geometry_checks, cell, backend, params, timing_s.
* Manifest (`simulate`): package versions, engine commit (= repository commit) and dirty flag,
  abTEM version and commit, precision, seeds, thread count and environment check, input hashes
  (atoms, structure positions, Kirkland data file), configuration SHA-256, wave planes, 200 keV.
* Tests: `tests/forward/` (`ladder_cases.py`, `smoke_case.py` shared helpers; `test_cell.py`,
  `test_vacuum_propagation.py`, `test_rung1_refraction.py`, `test_rung3_null.py`,
  `test_potential_atomic.py`, `test_engine_contract.py`, `test_smoke_atomistic.py`).

## 7. Resource estimates (HPC planning; `estimate_resources`)

HPC-size cell: Si(001) [110], 80.0 A (x) by 38.4 A (y; 10 periods) cross-section, 1000.4 A long,
72 240 atoms, pixel 0.128 A (625 x 300, derived), dz = p/4 = 0.960 A (1 A-class, commensurate),
1042 slices (516 hold atoms, 140 atoms each), exact propagator, 2/3 band, 4 threads.

| precision | engine arrays per realisation | CPU s per realisation (measured components, 4 threads) | GPU s per realisation |
|---|---|---|---|
| complex64 | 18.0 MB | 24.1 | 0.23 (ASSUMPTION model, NOT MEASURED) |
| complex128 | 32.6 MB | 25.3 | 0.37 (ASSUMPTION model, NOT MEASURED) |

Calibration check: for the smoke cell (640 x 480, 1438 slices) the same estimator gave 26.6 s while
the measured propagation took 38.6 s, so multiply the CPU figures by ~1.5 (both measured with the
4 cores shared with another agent's job, load average 6 to 9). Process overhead (Python, abTEM and
numba imports, structure build) was ~0.8 GB peak RSS in the smoke run. GPU model constants
(`engine.GPU_ASSUMED`): ~1 TB/s bandwidth, cuFFT at 1/3 of it, 10 TFLOP/s GEMM, 10 us per launch;
at this size the GPU time is launch-bound. The cupy backend has NOT been executed (no GPU here).
Frozen-phonon realisations are independent: wall time scales with realisations / concurrent jobs.

## 8. Tests, tolerances and verbatim results

| Test file | What | Tolerance and justification |
|---|---|---|
| test_vacuum_propagation.py | tilted plane wave per-slice phase (exact, Fresnel); forward/inverse identity; norm with a real potential, no absorbers; band limit on the propagated wave; SamplingError outside the band (64.31/48.23 mrad at 0.13 A); Fresnel minus exact at 45 mrad over 198 A; evanescent removal | 1e-11 (round-off <= 3e-14 measured); out-of-band power < 1e-28; paraxial vs analytic 1e-9 |
| test_rung1_refraction.py | r amplitude and phase vs (q1-q2)/(q1+q2), refracted angle vs SM04 at 10, 16.47, 30 mrad (exact) and 16.47 (Fresnel); dx order | section 2 |
| test_rung3_null.py | h_2pi -> 0; +-a/4 reverses the sign; translation step = -(4 pi/lambda) h sin theta | 1.0e-2 rad, section 3; sign reversal 1e-9 (mirror configuration) |
| test_potential_atomic.py | sigma vs abTEM; 2 k sigma V0 vs Delta; Kirkland MIP 13.903 V; Lobato refused; slice vs fresh abTEM integrator; absorption and phonon inputs; slice assignment | section 4 |
| test_cell.py | required arguments; layout; items 1 to 4 on both sides of each bound | exact inequalities |
| test_engine_contract.py | no defaults; 300 keV refused; names; cupy lazy; slicing and commensurability; ExitWave plane, dtype, metadata labels; .npz round trip and loader refusals; manifest content; frozen-phonon seeds reproducible; estimate | exact |
| test_smoke_atomistic.py | (d), < 120 s, finite wave, checks pass, manifest | runtime only; step phase reported, not asserted |

Findings made while writing the tests (reported, not hidden):
* `test_paraxial_error_matches_documented_value` first FAILED:
  `E Obtained: 0.024773604581845632 / E Expected: 0.026 +- 0.001`. Two causes: my test evaluated the
  nearest FFT bin (44.7 mrad) instead of 45 mrad (test error, fixed by placing a bin at 45 mrad),
  and docs/03 section 5 and docs/05 section 4.3 item 9 print 0.026 rad where k L sin^4(alpha)/8 at
  45 mrad over 198 A is 0.02539 (exact difference 0.02542): E_review computed 0.0255 and its
  proposed wording rounded it up. The documents should read 0.025 rad (not edited: not my files).
  The test now asserts the formula (1e-9) and the leading term (2e-3 relative).
* `test_item3_footprint_and_item4_buildup` and `test_frozen_phonon_realisations_and_seeds` first
  failed because the test geometry triggered an earlier assertion than the one targeted (test
  design errors; the engine behaved as specified); fixed in the tests, no tolerance involved.

Verbatim final runs (2026-09-23, 4 CPUs shared with another agent's job):
```
$ venv/bin/pytest tests/forward -q -p no:cacheprovider
.....................................                                    [100%]
37 passed in 175.72s (0:02:55)

$ venv/bin/pytest -q -p no:cacheprovider --ignore=tests/forward
FAILED tests/io/test_io_config_stand_ins.py::test_registry_is_package_data_mapping_ids_to_items
FAILED tests/io/test_io_config_stand_ins.py::test_registry_ids_exist_in_model_assumptions
2 failed, 604 passed, 6 warnings in 77.58s (0:01:17)
```
The two failures are outside this agent's files: `reflection_holo/io/assumption_registry.yaml` was
modified by another agent (entries B19 to B22 added; the test expects only B1, B17, B18).

## 9. NOT RUN and open items

* Ladder rung 2 (Bragg-case two-beam Bloch-wave phase sweep): NOT RUN.
* abTEM multislice cross-check (transmission and reflection-like configurations; abTEM 1.0.10 has
  only a Fresnel propagator, so in Fresnel mode only; slice ordering differs by half-slice
  propagations): NOT RUN. Only the slice POTENTIAL was cross-checked against abTEM.
* abTEM shear-tilt versus Fourier-component tilt at 24 and 48 mrad (spec M2): NOT RUN.
* Flat-surface rocking curve against a dynamical solver (sim-trhepd-rheed): NOT RUN.
* Atomistic a/2 null test: run as the smoke case, NOT PASSED (+0.58 rad at D = 20 A, +1.13 rad at
  D = 60 A; cause not established, section 5). Wider terraces and a sourced absorption: NOT RUN.
* Absorber effectiveness was not measured by a dedicated test (rung 1 is converged to 0.18 % with
  100 V sin^2 absorbers, and the refracted sheet never reached the absorber in rung 1).
* cupy backend: implemented, NOT EXECUTED (no GPU). GPU timings are an ASSUMPTION model.
* Physical absorption: only the proportional model; item 21 (a named parameterisation) open.
* MIP: the Kirkland IAM gives 13.903 V, not the sourced V0; no correction applied (D3 blocker 5).
* Sub-slice (finite) projection of the potential and step edges transverse to the beam in the
  continuum cells: not implemented.
