# E3 - Partial coherence from illumination convergence and surface-plasmon (inelastic) losses in hologram formation

Agent E3, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`. Status: IN PROGRESS
(written incrementally).

Scope (orchestrator task): (A) partial coherence from the illumination convergence (PROJECT_INPUT
item 3): an azimuthally tilted sheet beam, an ensemble generator with a stated, recorded quadrature,
incoherent summation of hologram intensities, the pipeline gate lifted only when item 3 is supplied,
an interface for running ensemble members as separate jobs; (B) surface-plasmon losses in hologram
formation (zero-loss factor, loss-electron fringes, R1 and R2 separately, noise from the reduced
visibility). Inputs read: H2 section 10 (N3), E6 (M1, M2, sections 8, 9), L6 section 1.6 with E6's
correction, `tools/review/e6_recompute.py` section F and its saved output, docs/03 sections 4 and 6,
docs/05 sections 4-6, docs/06 items 2, 3, 15, 16, 21, `docs/physics_conventions.md`,
`docs/model_assumptions.md` (B5, B6, B10, B21, B28), the illumination, engine, grid, propagator,
optics, reconstruction, pipeline and registry code.

Not edited (other agents): `reflection_holo/forward/multislice/potentials.py` (E1),
`reflection_holo/structure/` (E2), `scripts/hpc/alliance/`, every file under `docs/` except this
report. Nothing committed or pushed.

## 0. Log

* 2026-09-24: read the inputs above; baseline full test suite started before any edit (section 9).
* 2026-09-24: implemented (A) the y-tilted sheet beam (Bloch form), the convergence quadrature,
  members and illumination phases, the member runs, the pipeline gate and ensemble path, the CLI
  job interface; (B) the surface-plasmon loss model, its hologram formation, the noise model with
  the reduced contrast; registry rows B38-B40 reserved and used. Derivations below; tests and
  verbatim results in section 7.

## 1. Result in brief

* A convergence ensemble is now a set of INDEPENDENT engine runs, one per incidence direction of a
  declared quadrature (PROJECT_INPUT item 3, no default), each launched as a sheet beam tilted in
  x-z AND in y; the partially coherent hologram is the weighted mean of the member INTENSITIES.
  The azimuthal tilt is carried exactly by the Bloch (twisted-boundary) form of the y-periodic cell,
  so no tilt has to be commensurate with the cell; u_y = 0 reproduces the existing exit wave bit for
  bit.
* The number of directions is a declared, recorded parameter (n_radial, n_azimuthal); it is
  accepted only if a DERIVED_HERE error bound of the ensemble mean, for a phase extent the pipeline
  computes from the geometry, is below the declared tolerance (the smallest quadrature that would
  pass is printed on refusal).
* Physics found on the way (DERIVED_HERE, tested): with an R1 vacuum reference compensated by a
  condenser-biprism pre-tilt, the member phase between the object (reflected) and the reference
  (direct) arm has a ramp of -2 k delta per unit image coordinate u along the beam (a Lloyd's-mirror
  geometry): the fringes stay coherent only within |u - u*| of order 1/(2 k alpha) of the line
  where object and reference coincide (fringe contrast 0.5 at |u - u*| = 0.176 lambda/alpha: 44 nm
  at alpha = 10 urad, 4.4 nm at 0.1 mrad). With R2 the coherence depends only on the shift
  (contrast 0.5 at |s| = 0.353 lambda/alpha). This is a requirement on item 3 as strong as the
  step-phase spread of docs/03 section 4.
* Surface-plasmon losses: zero-loss factor exp(-n/2) per reflected arm (Poisson), loss electrons
  with their own mutual visibility V_loss. R1: fringe factor exp(-n/2) = 0.536 at E6's n = 1.25,
  INDEPENDENT of V_loss (the vacuum reference carries no loss electron, so the object arm's loss
  electrons are background). R2: exp(-n) + V_loss (1 - exp(-n)) = 0.358 at V_loss = 0.1. The
  reconstructed phase is unchanged (the factor is real and positive); the noise model now uses the
  reduced contrast (1.87 times the lossless phase noise for R1 at n = 1.25, measured 1.8735 +- 4 x
  0.0135 in the test).

## 2. Convergence: derivations (DERIVED_HERE unless stated)

### 2.1 Members and frame (optics/coherence.py:1-80)

Central incident direction b0 = (-sin th0, 0, cos th0) (x outward normal, y transverse, z beam;
docs/physics_conventions.md). Transverse unit vectors e_a = (-cos th0, 0, -sin th0) (t_a > 0
increases the glancing angle) and e_b = (0, 1, 0). Member direction, exact:
u_s = sqrt(1 - t_a^2 - t_b^2) b0 + t_a e_a + t_b e_b; glancing angle th_s = asin(-u_x); y direction
cosine u_y = t_b; tilt of the conventions (theta_x, theta_y) = lambda (q - q0) = (u_x + sin th0, t_b).
Specular outgoing direction: u_x reversed (parallel momentum conserved), so the outgoing glancing
angle of every member equals its incident one and the band assertion uses the member's own angle.

### 2.2 Azimuthal tilt on a y-periodic cell: the Bloch form (illumination.py docstring, engine.py)

For a transmission function t(x, y) periodic in y, psi = exp(2 pi i f_y y) u with u periodic in y:
t psi = exp(2 pi i f_y y) (t u), and the free propagator acting on psi is the propagator acting on u
evaluated at the physical frequencies (f_x, f_y' + f_y). The engine therefore launches the untilted
envelope and builds its kernels on a frequency-shifted grid view (BlochShiftedGrid); the band mask
(anti-aliasing of the products t u on the grid) stays on the native frequencies, on which every beam
of the member has f_y' = 0. Consequences: no commensurability constraint on the tilt; the band
assertion for a tilted member is the x-angle assertion with the member's own glancing angles; the
exit wave is the envelope (recorded in ExitWave.metadata["bloch"]); the dark-field aperture, fixed on
the CENTRAL k_out, is applied to the physical directions (darkfield.py), and the pipeline multiplies
the resampled detector wave by exp(2 pi i f_y y) (y periodic up to that point, so the DFT resampling
stays exact). A flat mirror reflects member s with the exit-plane phase dk_out,s . Q +
2 dk_in,s,x x_m relative to the central member (Q the exit-plane point, x_m the mirror height).

### 2.3 Coherence factors and the R1 Lloyd's-mirror confinement (tests/optics/test_coherence.py)

If the two interfering waves of member s differ only by the illumination phase dk_s . E, the
ensemble fringe term is multiplied by mu = sum_s w_s exp(i dk_s . E). For E perpendicular to b0,
dk_s . E = k t_s . E exactly; for a uniform disc |t| <= alpha, mu = (1/pi) int_0^1 rho d rho
int_0^2pi exp(i v rho cos phi) d phi = 2 int_0^1 J0(v rho) rho d rho = 2 J1(v)/v, v = k alpha |E|; for a
uniform line, (1/2) int_-1^1 exp(i v xi) d xi = sin(v)/v. Beyond the first zero (v = 3.8317) the
fringes reverse (arg mu = pi), tested.

R1 with the condenser-biprism pre-tilt (B28): the reference beam is split from the same source point
and deflected by R_y(2 th0), so dk_ref,s = R_y(2 th0) dk_in,s; with R e_a = (-c, 0, s), mirror(e_a) =
(c, 0, -s) and R b0 = mirror(b0), the member phase between the object at Q and the reference at
Q - D0 (D0 the object-reference separation, PROJECT_INPUT item 16) is exactly

    phi_s(Q) = k [t_a E_a(Q) + t_b E_b] - kappa_s,   E_a = 2c (Q_x - x_m) - 2s Q_z - c D0_x + s D0_z,
    E_b = D0_y,   kappa_s = k (1 - sqrt(1 - t_s^2)) (mirror(b0) . D0 - 2 s x_m)  (Q-independent).

Along the exit plane, Q_x - x_m = (L_z - z_s) tan th for the ray from surface point z_s, so
E_a = -2 sin(th) z_s + const = -2 u + const (u the image coordinate): the coherence falls as
|2 J1(v)/v| with v = 2 k alpha |u - u*|. Numbers (k = 250.53 rad/A): contrast 0.5 at v = 2.215, i.e.
|u - u*| = 1.1075/(k alpha) = 0.176 lambda/alpha: 442 A at 10 urad, 44 A at 0.1 mrad, 4.4 A at 1 mrad.
Only the reference passage "condenser_biprism_pretilt" is implemented under convergence; a
reference inclined to the imaging axis (second aperture hole, no aperture) needs the conjugate
plane of the imaging (not declared) and is refused. R2: the reference is the shifted object, so the
member phase is -dk_out,s . s (constant): E = (c s_x, s_y) on the exit plane, contrast 0.5 at
|s| = 0.353 lambda/alpha.

### 2.4 Quadrature, error bound, number of directions (optics/coherence.py)

Disc: Gauss-Legendre in s = (|t|/alpha)^2 (n_radial) x n_azimuthal equispaced azimuths (m = 0 in the
incidence plane; symmetric under t_b -> -t_b, which the d-glide argument of B4 needs); exact for
polynomials of total degree <= min(n_azimuthal - 1, 4 n_radial - 1) (tested, and not exact at the
next degree). Line: Gauss-Legendre (degree 2 n_radial - 1). Bound on |quadrature - exact| of the
ensemble mean of exp(i dk.E) with phase extent v and curvature kappa (module docstring): azimuthal
aliasing E_az = 2 sum_p (v/2)^(p m)/(p m)! (|J_n(x)| <= (x/2)^n/n!), radial Gauss-Legendre remainder
with a Cauchy estimate of the 2n-th derivative (M(R) = I0(v sqrt(1+R)) exp(kappa R), minimised over
R), plus a rounding floor of 8 eps per member. The pipeline computes v from the geometry, max of
k alpha |E_perp| over the whole exit plane (R1: formula above; R2: the shift) and of the step-phase
extent (4 pi h_max/lambda) cos(th) alpha (docs/03 section 4), and refuses the declared
(n_radial, n_azimuthal) if the bound exceeds the declared tolerance. Example: v = 3, tolerance 1e-6
needs 3 x 13 = 39 members; v = 0.3, tolerance 1e-2 needs 1 x 4. Limitation: the bound covers phases
linear in t (illumination phases, step phases); the variation of the reflection amplitude along
the rocking curve inside the convergence disc is not bounded (a member count for it needs the
rocking-curve width, H2 section 7).

Cost remark (not implemented, recommendation): the illumination phases are analytic; only the
object response needs engine runs, and it varies on the scale of the rocking-curve width, not of
lambda/(|E| alpha). A two-level scheme (few engine members, many analytic phase nodes, object
response interpolated in t) would cut the engine cost by the ratio of the two node counts.

## 3. Surface-plasmon losses: derivation (optics/inelastic.py docstring; DERIVED_HERE)

Premises: P1 (SECTION_READ via E6, Tanishiro 2003 pp. 166-167, 170): for the specular beam the main
inelastic process is surface-plasmon excitation, mostly outside the crystal (decay length about
6 nm at 200 keV); the number of excitations per reflection is Poisson distributed with mean n
(ASSUMPTION: independent excitations of a linearly coupled boson field, the model behind the
Lucas-Sunjic mean cited there). P2 (ASSUMPTION): a loss electron keeps the spatial wave of the
elastic object wave (theta_E = 2.8e-5 rad, far inside the 3 mrad aperture); without an energy filter
every electron is detected. P3 (coherent-state bookkeeping): an electron passing along arm P leaves
the plasmon field in a coherent state |alpha_P>, n_P = sum_m |alpha_P,m|^2; tracing out the plasmons
multiplies the fringe term by <alpha_R|alpha_O> = exp(-(n_O + n_R)/2 + c), c = sum_m alpha_R,m^*
alpha_O,m. The k = 0 term of exp(c) is the zero-loss channel (amplitude factors exp(-n_P/2): the
Poisson zero-loss probability exp(-n) in intensity); the k >= 1 terms are the loss channels, which
interfere only through excitations shared by both arms (c != 0).

Model, with the loss channels summarised by one declared mutual visibility V_loss in [0, 1]:

    I = |e^(-n_O/2) u_o + e^(-n_R/2) u_r|^2 + L_O |u_o|^2 + L_R |u_r|^2
        + 2 V_loss sqrt(L_O L_R) Re(u_o u_r^*),          L_P = 1 - e^(-n_P).

Fringe (sideband) factor F = e^(-(n_O + n_R)/2) + V_loss sqrt(L_O L_R); DC unchanged (A_O^2 + A_R^2);
visibility mu = mu_0 F; zero-loss filter: F = e^(-(n_O+n_R)/2), DC e^(-n_O) A_O^2 + e^(-n_R) A_R^2.

* R1 (vacuum reference, does not reflect; n_R = 0): F = e^(-n/2) whatever V_loss. The object arm's
  loss electrons cannot interfere with a reference-arm electron that left the plasmon field in its
  ground state (orthogonal final states): they are background. With E6's n = 1.25: F = 0.536,
  zero-loss intensity fraction 0.288 (REPRODUCES tools/review/e6_recompute_output.txt section F).
  Tanishiro's 0.1 (p. 171) is a one-plasmon-loss visibility measured in an R2 arrangement; applied to
  R1 it has no effect in this model (stated in B39's source text).
* R2 (both arms reflect from the same, uniform surface; n_O = n_R = n): F = e^(-n) + V_loss
  (1 - e^(-n)); n = 1.25: 0.287 + 0.713 V_loss = 0.358 at V_loss = 0.1 (E6's R2 factor 0.288 is the
  V_loss = 0 limit). Tanishiro's measured one-plasmon visibility 0.1 against 0.4 at zero loss
  (p. 171) suggests an intrinsic relative coherence of about 0.25 for that separation; 0.1 is the
  stand-in asked for (B39), 0.25 the other reading (bracket).
* Phase: F is real and positive, so the reconstructed phase (phi_o - phi_r for R1, phi(r) -
  phi(r + s) for R2) is unchanged by a uniform n, exactly in this model. What changes near a
  structure of the zero-order (DC) term: the DC leakage through the sideband mask is unchanged while
  the sideband is scaled by F, so its relative effect grows by 1/F (bounded pixel by pixel in the
  test; with R2 it matters near the edge of the reference field). Not modelled: a mode-structure
  phase of c (complex c), spatially varying n (nm-scale features within about 1 um along the beam,
  E6 M1), multiple-loss channels with different coherence (one V_loss for all), an energy filter in
  the pipeline.
* Noise: sigma_phi = sqrt(2)/(mu sqrt(N)) (SM12) with the REDUCED mu. For R1 at n = 1.25 the phase
  noise is 1/0.536 = 1.87 times the lossless one at the same dose (test: measured/predicted =
  1.0047, measured/lossless-predicted = 1.8735; 4 standard errors = 0.054).

Pipeline consequences found with the plasmon_losses variant (section 7): R1 contrast of the empty
hologram 0.536; with R2 at n = 1.25, V_loss = 0.1 the contrast 0.358 is below the demo's minimum
empty-hologram visibility 0.5 (B29), so every pixel of an R2 demo hologram would be rejected; the
no-step control of the A3 B1 reproduction (a 0.001 rad/A charging slope at 500 e/px) passes instead
of failing because its tolerance (3 measured standard errors) grows with the noise (0.0205 rad
against the injected 0.0183 rad).

## 4. Pipeline (reflection_holo/pipeline/)

* Gate (config.py `_check_convergence`, replacing the former refusal of every non-zero item 3):
  a non-zero `cfg_b.convergence_semi_angle` is accepted only as a supplied PROJECT_INPUT or a
  registered stand-in whose row states a convergence (B21 states a plane wave and is refused with a
  non-zero value; B40 is refused with zero), with the multislice engine (the geometric engine is
  plane-wave only), with `sections.illumination.convergence_quadrature` = {source_profile,
  n_radial, n_azimuthal, line_azimuth_rad, tolerance} (every key required), and, for R1, only with
  the condenser-biprism passage and `sections.reference.separation` {x, y, z} (item 16; missing:
  MissingProjectInputError item 16); for R2 the separation is refused (the shift is used). With a
  zero convergence the quadrature and the separation are refused rather than ignored. The
  existing test `test_nonzero_convergence_is_refused_on_every_engine_path` still passes unchanged
  (its 0.5 mrad TEST_ONLY value has no quadrature, so both variants are refused with a message
  containing "convergen").
* Losses (both engines): `sections.optics.surface_plasmon_excitations` (item 21, >= 0) and
  `sections.optics.loss_electron_visibility` (item 16, [0, 1]) are REQUIRED records; a missing one
  fails naming its item. The four demo configurations state n = 0 with stand-in B30 ("B6 not
  represented": no surface-plasmon loss, stated, not defaulted) and V_loss = 0.1 with B39, so their
  results are unchanged; `configs/demo_smoke_si001.yaml` and `configs/demo_hpc_si001.yaml` gain a
  variant `plasmon_losses` with B38 (n = 1.25). Holograms are unfiltered (energy filter NOT
  IMPLEMENTED in the pipeline; the optics function supports "zero_loss").
* Run (run.py): one engine run per member (`pipeline/convergence.py engine_members`) or the member
  jobs (`--members-dir`); dark field with the aperture fixed on the CENTRAL k_out, Bloch factor
  restored after the detector resampling; R1 references carry exp(i dk_ref,s.(Q - D0)); the empty
  hologram models a flat region of the same surface (flat-mirror member phases at the lowest terrace
  top; same loss model); object and empty holograms are `partially_coherent_hologram` (weighted
  member means after squaring). The noise model uses the reduced contrast
  (`summary["reference"]["fringe_contrast"]`: lossless, with losses, the convergence coherence of
  the empty ensemble (median, min, max over the lit pixels), and the value used). The quadrature's
  design phase extent is computed from the cell (`design_extent`, conservative over the whole exit
  plane), and the run, the member jobs and the dry run refuse a quadrature whose bound exceeds the
  declared tolerance, printing the smallest one that passes.
* Dry run: for a convergence ensemble also the member count, the design extent, the quadrature
  record and the band and geometry assertions of EVERY member; costs are per member.

## 5. Interface for the HPC kit (not edited: scripts/hpc/alliance/)

    python -m reflection_holo.pipeline members    --config C [--variant V]
        -> JSON: n_members, quadrature record with every member (index, t_a, t_b, weight, glancing
           angle, y direction cosine), quadrature_member_sha256, pipeline_config_sha256_resolved
    python -m reflection_holo.pipeline run-member --config C [--variant V] --member K --out D_K
           [--allow-no-git]
        -> D_K/outputs/exit_waves/<run>_multislice_m<KKKK>_r<RRRR>.npz, D_K/outputs/manifests/...
           (the engine manifest: packages, commit, precision, seeds, threads, input hashes,
           configuration hash, caller record with the member and the quadrature hash),
           D_K/member.json (schema reflection_holo.pipeline.convergence_member/1: member, quadrature
           identity SHA-256, resolved configuration SHA-256, SHA-256 of every exit-wave file)
    python -m reflection_holo.pipeline run --config C [--variant V] --out D --members-dir M
        -> assembles every M/*/member.json (same resolved configuration and quadrature, each member
           exactly once, file hashes checked, planes asserted); no engine backend is needed

Exit codes as `run` (3 configuration or bad member index, 4 engine, 5 output directory not empty,
6 git). A job array of size n_members maps SLURM_ARRAY_TASK_ID to --member; memory and time per job
are those of one plane-wave run of the same cell (dry-run prints them per member). Engine-level
API: `reflection_holo.forward.multislice.convergence` (`simulate_member`, `check_members`,
`member_beam`, `member_params`, `quadrature_sha256`).

## 6. Registry rows (reflection_holo/io/assumption_registry.yaml; tests/io expected registry)

Reserved and used: B38 -> item 21, B39 -> item 16, B40 -> items 3 and 16; all three demo-only. E2's
B35-B37 were left as found (re-read before each edit). Proposed docs/model_assumptions.md rows (the
orchestrator writes them; until then `test_registry_ids_exist_in_model_assumptions` fails, see
section 7):

| B38 | Demo surface-plasmon excitation number of the object path: n = 1.25 excitations per specular reflection, E6's 1/sin(theta) transfer (tools/review/e6_recompute_output.txt section F) of the 200 kV measurement 1.44 on Si(111)7x7 at 0.8 deg, (444) (Tanishiro 2003 p. 167) to Si(001) at the (0,0,8) condition (16.13 mrad): zero-loss amplitude exp(-n/2) = 0.536 of each reflected arm, loss fraction 1 - exp(-n) = 0.71 of its intensity. Stands in for PROJECT_INPUT item 21 (new request: an energy-filtered EELS of the specular beam at the working angle) in the demo configurations only (variant `plasmon_losses` of `configs/demo_smoke_si001.yaml` and `configs/demo_hpc_si001.yaml`; purpose demo; a run with purpose "comparison" refuses it); not comparable to experiment. | ASSUMPTION (transfer DERIVED_HERE by E6; 1.44 SECTION_READ via E6) | Surface, temperature and Bragg condition differ from the source. Fringe factor 0.536 (R1) and 0.358 (R2, with B39); phase noise x 1.87 (R1) at the same dose; the reconstructed phase is unchanged (report E3). |
| B39 | Demo mutual visibility of the surface-plasmon-loss electrons of the two arms, V_loss = 0.1 (one-plasmon-loss hologram, Tanishiro 2003 p. 171, via E6 M2; an R2 arrangement). Stands in for PROJECT_INPUT item 16 (it depends on the object-reference separation) in the demo configurations only (`configs/demo_*.yaml`, purpose demo; a run with purpose "comparison" refuses it); not comparable to experiment. | ASSUMPTION (value SECTION_READ via E6) | With an R1 vacuum reference the reference arm carries no loss electron and V_loss has no effect (DERIVED_HERE, report E3 section 3); for R2 the fringe factor is exp(-n) + V_loss (1 - exp(-n)). The 0.1 includes the instrumental factor that limited the zero-loss visibility to 0.4 on the same page (intrinsic relative value about 0.25; bracket 0.1-0.25). |
| B40 | Demo convergent illumination: a uniform disc (or line) of transverse directions of semi-angle per configuration, sampled by the declared quadrature of `sections.illumination.convergence_quadrature`, and, with an R1 reference, the object-reference separation D0 at the specimen (per configuration; the E3 tests use 0.01 mrad and D0 = (0, 20, 0) A). Stands in for PROJECT_INPUT items 3 and 16 in demo configurations only (purpose demo; a run with purpose "comparison" refuses it); not comparable to experiment. | ASSUMPTION | With R1 the fringe coherence is confined to about 0.18 lambda/alpha (contrast 0.5) around the zero-path-difference line (report E3 section 2.3). |

Proposed amendment of B30 (now also used for the loss record of the four demos): "No physical
absorption in the multislice demos and no surface-plasmon loss in any demo (imaginary potential 0;
sections.optics.surface_plasmon_excitations n = 0; B6 not represented). ..." (rest unchanged).
Proposed notes: B10 and B21 "a convergence ensemble is implemented (report E3); B21 remains the
plane-wave stand-in of the demos"; B6 "surface-plasmon loss: optics.inelastic (report E3)".
Proposed docs/06 text: item 3, add the source profile (uniform disc or other) and that an R1
reference confines the coherent field to about 0.18 lambda/alpha along the beam; item 16, the
separation D0 as a 3-vector at the specimen and the loss-electron visibility; item 21, the new
request "an energy-filtered EELS of the specular beam at the working angle (mean surface-plasmon
excitation number, zero-loss fraction)".
