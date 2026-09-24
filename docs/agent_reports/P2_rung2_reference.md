# P2: exact and two-beam reference for rung 2 of the phase-validation ladder

Prepared: 2026-09-23 (agent P2). Written incrementally; FINAL (section 10).
Scope (orchestrator task): the reference for docs/05 section 4.4 rung 2 ("Bragg-case Bloch-wave
two-beam solution for one allowed reflection ... the multislice must reproduce the phase sweep, not
only the width"). Deliverables: `tools/physics_checks/rung2_reference.py` (importable functions and a
`__main__` that prints every number quoted here, with self-checks) and this report. No engine code,
summary document or other report was edited; nothing was committed.

## 0. Log

* read: docs/physics_conventions.md, docs/03_physics_summary.md, docs/05 section 4.4 (and 4.3),
  reflection_holo/constants.py, tools/reflection_step_phase_calculator.py (sections 0 to 4, 4b),
  docs/agent_reports/M2_multislice_engine.md (all), the engine modules physics.py, potentials.py,
  propagator.py, engine.py, analysis.py, illumination.py, grid.py, backend.py, cell.py,
  reflection_holo/geometry/{refraction,wavelength,specular}.py, tests/forward/ladder_cases.py,
  test_rung1_refraction.py, smoke_case.py, null_test_cases.py (head).
* NOT read before the derivation and code were finished (independence, orchestrator rule):
  docs/agent_reports/H2_realistic_supercell_sizing.md sections 2.1 to 2.3.
* prototype (scratchpad, later moved into the tool): laterally averaged Kirkland potential of a
  flat 41-layer Si(001) cell built by the repository's builder and realised by the engine's
  `AtomicPotential` (dx = 0.01 A): least-squares Fourier fit over 16 layer periods in the bulk gives
  V0 = 13.9028 V, V_(0,0,4) = 2.7401 V, V_(0,0,8) = 1.0357 V, V_(0,0,12) = 0.5467 V (origin at an
  atomic plane; sine terms < 1e-7 V), equal to 8 F(f^2)/a^3 from the engine's own scattering factor
  to 6e-6 V. (M2 section 10.2 used a rough estimate of 0.84 V; not used here.)
* first full run of `tools/physics_checks/rung2_reference.py` (48 self-checks, 0 failed): exact
  solvers agree to < 1e-9; the Darwin (Takagi-Taupin) form misses the refraction correction of the
  boundary condition (0.14 rad at the plateau centre); the two-beam closed form with exact matching
  is within 8e-3 of the exact solution. Side finding: with r = 0 the engine-style bulk absorber
  (15 A, sin^2, 100 V) reflects the Bragg-case Bloch waves outside the plateau strongly (|dR| up to
  0.38), and a clean depth of 21 A (the M2 null-test cells) is inside the extinction depth (24.5 A).
* added: refracted Darwin form, one-way propagator model, independent 1D split step, transfer-matrix
  check, absorber-ramp and null-test-geometry predictions; derivations and code then final.
* only then read H2 sections 2.1 to 2.3 (comparison in section 9); no change to the code or to the
  derivations followed from it.
* concurrent edits by other agents seen during the work (not mine): the engine's MultisliceParams
  gained a required `working_reflections_hkl` (() for continuum cells), tests/forward/ladder_cases.py
  changed; the tool uses neither.

Evidence labels used: DERIVED_HERE (derived in this report from the stated premises, numbers from
the tool), PROJECT_INPUT, ASSUMPTION, TEST_ONLY, UNVERIFIED, SECTION_READ (as in the instruction file).
No textbook passage was read for any formula below; none is cited. Every number is printed by
`venv/bin/python tools/physics_checks/rung2_reference.py` (section numbers of its output are given
as "out §n"); the final verbatim run is in section 11.

## 1. The exact problem, premises, conventions

Premises (each is used by the tool exactly as written):

* P1 Beam: 200 keV (PROJECT_INPUT item 1; the tool refuses any other energy),
  lambda = 0.02507934 A, k = 250.5323 rad/A, sigma = 7.288401e-4 rad/(V A), from
  `reflection_holo/constants.py` only (out §1; equal to the package's wavelength and to the engine's
  `interaction_constant_rad_per_VA` to machine precision).
* P2 Wave equation: grad^2 psi + [k^2 + U(r)] psi = 0 with U = 2 k sigma V. DERIVED_HERE from the
  Klein-Gordon dispersion (E_tot + e V)^2 = (hbar c k_loc)^2 + (m c^2)^2, which gives
  k_loc^2 = k^2 + [2 E_tot e V + (e V)^2]/(hbar c)^2, and 2 k sigma = 2 E_tot e/(hbar c)^2 exactly
  (sigma = 2 pi (T + m c^2) lambda/(h c)^2). The (e V)^2 term is dropped: it is 9.9e-6 of U_0 and
  changes arg R at the plateau centre by 1.3e-4 rad (out §8, option `klein_gordon_V2=True`); the
  engine does not contain it either, so it is not a test error. Spin is neglected (ASSUMPTION, not
  quantified here). This is the equation whose paraxial form the engine integrates (transmission
  exp(+i sigma V_p)).
* P3 Potential: V depends on the depth x only,
  V(x) = (1 + i r) [V0 + sum_n 2 V_n cos(2 pi n g (x - x_s + t))] for x < x_s, V = 0 for x > x_s,
  V_n real, g the fundamental spatial frequency in cycles/A (G = 2 pi g in rad/A), t >= 0 the depth
  of a cosine maximum below the truncation plane x_s (t = 0 is the orchestrator's form
  V0 + 2 V_g cos(G (x - x_s)): the truncation plane is at a maximum, i.e. at an atomic plane of a
  layer potential). This is exactly the potential of the proposed continuum test class (section 8).
  For an atomistic crystal it is its laterally averaged potential only: the in-plane Fourier
  components (non-specular rods) are dropped (the one-dimensional, "one-beam" model of the specular
  rod); that approximation is NOT quantified here.
* P4 Absorption: the engine's proportional model V_imag = r V_real applied to V0 and to every V_n;
  r = 0, 0.05, 0.1 are TEST_ONLY stand-ins for PROJECT_INPUT item 21.
* P5 Potential values: the engine's own Kirkland independent-atom potential, static lattice,
  a = 5.4309 A (ASSUMPTION B2); the parameterisation is UNVERIFIED (SM17). Section 6.1.
* P6 Sharp truncation at x_s (no relaxation, no smooth surface tail): part of the definition of the
  continuum test potential.
* P7 Semi-infinite crystal: in x < x_s the physical solution is the one Bloch (Floquet) solution that
  decays towards -x, or, where no solution decays (r = 0 inside an allowed band), the one that
  carries its flux towards -x. It is the r -> 0+ limit of the absorbing solution (checked, out §4:
  5e-9 between r = 0 and r = 1e-10).

Reduction to one dimension (DERIVED_HERE). Because V does not depend on y or z, the surface-parallel
wavevector is conserved: psi(x, z) = u(x) exp(i k_z z), k_z = k cos(theta) in vacuum and inside, and

    u''(x) + [K^2 + U(x)] u(x) = 0,     K = k sin(theta),  U = 2 k sigma V,

exactly. The only vacuum beam is the specular one; every (0,0,n) Bragg reflection of the laterally
uniform potential feeds it.

Conventions and phase origin (docs/physics_conventions.md): exp(+i(k.r - omega t)); x is the OUTWARD
normal; theta is the EXTERNAL glancing angle. In vacuum u = exp(-i K (x - x_s)) + R exp(+i K (x - x_s)):
R is the ratio of the reflected to the incident amplitude, BOTH EVALUATED AT THE TRUNCATION PLANE
x = x_s. Referred to another plane x_r, R_r = R exp(2 i K (x_r - x_s)). This is the quantity the
engine's `flat_reflection_coefficient(x_surface_A = x_s)` returns (its factor exp(+i 4 pi f (x_s - x0))
moves the reference from the box origin x0 to x_s; M2 section 2). With the opposite time convention
exp(-i omega t + ...) every phase in this report changes sign.

## 2. Exact solution (item 1)

### 2.1 Matching at the surface (DERIVED_HERE)

u and u' are continuous at x_s (U has a finite jump there). With L = b'(x_s)/b(x_s) the logarithmic
derivative of the physical crystal solution b (premise P7):

    1 + R = c b(x_s),   -i K (1 - R) = c b'(x_s)   =>   R = (L + i K)/(i K - L).

Limit V_n = 0 (rung 1): b = exp(-i q (x - x_s)), q = sqrt(K^2 + U_0), L = -i q, R = (K - q)/(K + q),
the Fresnel step that rung 1 already tests (out §5: identical to 1e-16; differs from the M2 analytic
value, which uses the SM04 Delta with the (e V0)^2 term, by 1.5e-7 to 8.5e-7).

### 2.2 Bloch waves (DERIVED_HERE)

b(x') = sum_m c_m exp(i (m G_f - kappa) x'), x' = x - x_s, m = -M..M, G_f = 2 pi g. Inserting into
u'' + (K^2 + U) u = 0 with U(x') = sum_n U_n exp(i n G_f x') (U_n = 2 k sigma V_n^(s), V_n^(s) the
coefficients referred to x_s, including exp(+-i n G_f t) and (1 + i r)) gives for every m

    [K^2 - (m G_f - kappa)^2] c_m + sum_m' U_(m-m') c_m' = 0,

a quadratic eigenvalue problem (A + kappa B - kappa^2) c = 0 with A = diag(K^2 - m^2 G_f^2) + [U_(m-m')]
and B = diag(2 m G_f), solved exactly by the linearisation [[0, I], [A, B]] [c; kappa c] = kappa [c; kappa c]
(2(2M+1) eigenvalues). Selection (P7): Im kappa > 0 (decay towards -x), or, for real kappa, flux
sum_m |c_m|^2 (m G_f - kappa) < 0; of the equivalent representatives kappa + j G_f the one with
Re kappa closest to Re sqrt(K^2 + U_0) is used. Then u(x_s) = sum_m c_m, u'(x_s) = sum_m i (m G_f - kappa) c_m.
Convergence: for the single harmonic the coupling between successive plane waves is
U_g/(m G)^2 <= 4.4e-3 (out §3), so the coefficients fall off faster than geometrically; M = 4 and M = 8 agree
to 2.2e-12 (out §4). For the full laterally averaged Si layer potential (12 harmonics (0,0,4) ...
(0,0,48), g = 4/a) M = 24 and M = 48 agree to 3.0e-10.

### 2.3 Floquet monodromy (independent of the plane-wave truncation; DERIVED_HERE)

The 2x2 matrix mapping (u, u')(x_s) to (u, u')(x_s - d), d = 1/g, is integrated with DOP853
(rtol 1e-12). Its eigenvectors are the Floquet solutions, y(x_s - d) = mu y(x_s); the physical one has
|mu| < 1, or |mu| = 1 and Im(conj(u) u') < 0; L = u'/u of that eigenvector. Bloch and Floquet agree to
6.3e-12 (r = 0), 9.1e-13 (r = 0.05), 3.9e-13 (r = 0.1) for the single harmonic and to 3.0e-10 for the
full potential (out §4). The exact gap edges (r = 0) are the roots of tr(M) = 2 (-1)^n for the n-th
gap (Floquet multiplier (-1)^n at kappa d = n pi); they are independent of t (checked to 1e-12:
a bulk property).

### 2.4 Finite crystal with a radiation condition (independent of the Floquet selection)

A crystal of thickness D on a uniform substrate with the potential (1 + i r) V0, an outgoing
(decaying) wave exp(-i q_s (x - x_b)) below it, integrated upwards (the physical solution grows
upwards, so the integration is stable). With absorption it converges to the semi-infinite result:
1.1e-11 at D = 600 A (r = 0.05), 5.3e-12 at D = 400 A (r = 0.1). Without absorption it converges only
inside the gap, as the evanescent Bloch wave dies (plateau centre: 5.6e-4 at D = 100 A, 1.6e-7 at
200 A, 1.7e-11 at 400 A; amplitude extinction depth G/|U_g| = 24.47 A). Inside an allowed band at
r = 0 it does NOT converge: at eta = 1.5 |R_D - R_inf| = 0.27 to 0.29 for D = 300 to 601 A (a
Fabry-Perot cavity between the surface and the crystal/substrate junction, which reflects a Bragg-
case Bloch wave strongly). The same effect appears with the engine's numerical absorber (section 6.5).

### 2.5 Further checks (out §5)

|R| <= 1 + 1.6e-13 over eta in [-4, 4] at r = 0; |R| = 1 to 1.6e-13 inside the exact gap; |R| < 1 for
r = 0.05 and 0.1 (maxima 0.5423 and 0.3470); an independent piecewise-constant transfer-matrix
discretisation of a finite cell agrees with the ODE solution (out §11).

## 3. Two-beam Bragg-case closed forms (item 2)

### 3.1 Two-beam Bloch wave with exact matching (DERIVED_HERE)

Keep two plane waves, b = c_0 exp(-i kappa x') + c_1 exp(i (G - kappa) x'), for the reflection with
reciprocal vector G (G = 2 pi g; for the single harmonic G = G_f). With q^2 = K^2 + U_0,
eps = q^2 - G^2/4 (deviation from the INTERNAL Bragg condition) and kappa = G/2 + delta, the two
secular equations (q^2 - kappa^2) c_0 + U_-g c_1 = 0, U_g c_0 + (q^2 - (G - kappa)^2) c_1 = 0 give the
exact quartic (eps - G delta - delta^2)(eps + G delta - delta^2) = U_g U_-g, whose physical root is

    delta^2 = 2 (eps^2 - U_g U_-g) / [(2 eps + G^2) + sqrt(G^4 + 4 eps G^2 + 4 U_g U_-g)],
    rho = c_1/c_0 = -U_g / (eps + G delta - delta^2),

delta chosen with Im delta > 0, or for real delta with flux -(G/2 + delta) + (G/2 - delta)|rho|^2 < 0.
Matching (section 2.1) with L = i[-kappa + (G - kappa) rho]/(1 + rho):

    R_2b = [(K - G/2 - delta) + rho (K + G/2 - delta)] / [(K + G/2 + delta) + rho (K - G/2 + delta)].

It equals the Bloch method restricted to the basis {0, 1} to 2.2e-13 (out §5). Here U_g = U_(+g)^(s)
is the coefficient of exp(+i G x') referred to x_s: U_g = 2 k sigma V_g exp(+i G t)(1 + i r).

### 3.2 Darwin (Takagi-Taupin) limit and its refraction correction (DERIVED_HERE)

Dropping delta^2, evaluating the prefactors at q = G/2 and dropping the reflection at the mean-
potential step gives R_D = rho with (eps - G delta)(eps + G delta) = U_g U_-g:

    R_D = -(U_g / sqrt(U_g U_-g)) (eta - sqrt(eta^2 - 1)),   eta = (K^2 + U_0 - G^2/4)/sqrt(U_g U_-g),

with the branch Im(G delta) > 0, i.e. |R_D| < 1 for real |eta| > 1. For r = 0 and the truncation at a
cosine maximum (t = 0, U_g > 0): inside the plateau |eta| <= 1, R_D = -eta + i sqrt(1 - eta^2), |R_D| = 1
and arg R_D = arccos(-eta): 0 at the low-angle edge (eta = -1), pi/2 at the centre, pi at the
high-angle edge (checked to 4e-8, out §5). The phase sweeps by exactly pi across the plateau.
Interpretation: at eta = -1, c_1 = c_0 and the internal standing wave 2 cos(G x'/2) has its antinodes
on the potential maxima (atomic planes), the low-energy band edge; the vacuum standing wave 1 + R = 2
has an antinode at x_s. With a truncation offset t the Darwin amplitude acquires exp(+i G t); a
half-period offset (surface between planes) adds pi. The exact solution follows this only
approximately because the refraction correction below changes sign with R_D: at the plateau centre
arg R = +1.70798 (t = 0), -3.13195 (t = d/4 = 0.16972 A) and -1.70360 rad (t = d/2 = 0.33943 A), i.e.
+1.4433 and +2.8716 rad (mod 2 pi) instead of pi/2 and pi (out §7). With exp(-i omega t) conventions
all these phases change sign.

Keeping the step (delta -> 0 in the prefactors of R_2b, q in place of G/2) gives the refracted Darwin
form, an Airy-type composition of the Fresnel step and the Darwin amplitude at the same plane:

    R_DR = (r_F + R_D) / (1 + r_F R_D),     r_F = (K - q)/(K + q),  q = sqrt(K^2 + U_0).

Inside the plateau (|R_D| = 1, R_D = exp(i phi)) it keeps |R| = 1 and the edge phases 0 and pi, but
shifts the phase in between by -2 atan[r_F sin(phi)/(1 + r_F cos(phi))], i.e. by +2 atan|r_F| at the
centre. At the (0,0,8) centre r_F = -0.06755, so the Darwin/TT phase is too small by 0.135 rad there
(section 3.4): the refraction at the mean-potential step is NOT negligible at 16 mrad.

### 3.3 Plateau parameters (definitions; numbers in section 6.2)

Darwin centre eps = 0: K_c^2 = G^2/4 - U_0; edges K^2 = K_c^2 -+ |U_g| (r = 0); external angles
theta = asin(K/k). Amplitude extinction depth at the centre 1/Im(kappa) = G/|U_g|. Coupling constant
along the beam kc = sigma |V_g| (rad/A): the time-like variable of section 5.

### 3.4 Validity of the closed forms against the exact solution (out §7)

Single harmonic V_008, truncation at a cosine maximum; max over the angle range of |R - R_exact|
(the complex difference) and of |arg(R/R_exact)|:

| form | r = 0, abs(eta) <= 0.9 | r = 0.05, abs(eta) <= 3 | r = 0.1, abs(eta) <= 3 |
|---|---|---|---|
| two-beam matched (3.1) | 7.9e-3 (7.9e-3 rad) | 3.9e-3 (9.9e-3 rad) | 2.9e-3 (1.8e-2 rad) |
| Darwin + Fresnel step (3.2) | 5.7e-3 (5.7e-3 rad) | 1.0e-3 (2.0e-3 rad) | 5.0e-4 (1.5e-3 rad) |
| Darwin / Takagi-Taupin (3.2) | 0.138 (0.138 rad) | 8.8e-2 (0.18 rad) | 7.6e-2 (0.35 rad) |

For r = 0 the range is limited to |eta| <= 0.9 because the exact gap edges lie 0.41 urad below the
two-beam ones (third-beam shift): within that distance of an edge any two-beam form is off by up to
0.08 (the reflectivity drops from 1 with infinite slope). Validity range: the Darwin/TT form is
wrong by ~2 atan|r_F| in phase wherever the Fresnel amplitude r_F of the mean-potential step is not
negligible, i.e. at every grazing angle of interest (|r_F| = 0.0676 at 16.1 mrad); the refracted
Darwin form is the most accurate closed form (<= 2e-3 rad with absorption, <= 5.7e-3 rad for r = 0
inside the plateau); none of them replaces the exact solution within 0.5 urad of the r = 0 band
edges. The phase sweep across the r = 0 plateau is pi for every form (exact: 3.14158 rad between the
exact band edges); the forms differ in its shape: arg R at the centre is pi/2 = 1.5708 (Darwin/TT),
1.7013 (matched), 1.7057 (refracted Darwin), 1.7080 (exact, single harmonic), 1.6701 at the same
angle for the full layer potential (whose plateau is shifted, section 6.2).

## 4. What the paraxial multislice changes (item 3)

### 4.1 Fresnel propagator: no change of the stationary R(K) (DERIVED_HERE)

The engine marches the envelope psi (full wave psi exp(i k z)) along z. With the Fresnel propagator
exp(-i pi lambda dz f^2) and the transmission exp(i sigma V dz), the split step converges (dz -> 0) to

    i d psi/dz = -(1/2k) d^2 psi/dx^2 - sigma V(x) psi.

For a laterally uniform V (independent of z) this is a z-invariant problem; its stationary solutions
psi = u(x) exp(-i E z) satisfy u'' + (2 k E + 2 k sigma V) u = 0. In vacuum the incident component
exp(-i K x) has 2 k E = K^2. Hence u'' + (K^2 + U) u = 0, IDENTICAL to the Helmholtz problem of section 1
at the same K. The stationary reflection coefficient of the paraxial problem is therefore exactly
R(K) of the exact problem, for every K, with no expansion in theta. More generally every generator
that is a function of the operator d^2/dx^2 + 2 k sigma V (the paraxial one, or the exact one-way
sqrt(k^2 + d^2/dx^2 + 2 k sigma V) - k) has the same stationary scattering states. The engine launches
each incident component by its transverse frequency f = -K/(2 pi) (SheetBeam, entrance-plane Fourier
component) and its read-out divides by the vacuum factor P_L(f) of the same propagator, so it
compares R at the same K. What the paraxial approximation does change is only the dispersion along z
(E = K^2/2k instead of k - sqrt(k^2 - K^2), relative difference K^2/4k^2 = 6.5e-5 at the (0,0,8)
centre, out §3), i.e. the
z-scale of transients (section 5), not R(K). A priori paraxial error of the Fresnel scheme for
rung 2: zero.

### 4.2 The engine's "exact" propagator with an additive potential phase (DERIVED_HERE)

The engine's default propagator exp(i dz (sqrt(k^2 - (2 pi f)^2) - k)) combined with exp(i sigma V dz)
converges to the generator sqrt(k^2 + d^2/dx^2) - k + sigma V, which is NOT a function of
d^2/dx^2 + 2 k sigma V. Write it as the paraxial generator plus N(d/dx), N(q) = sqrt(k^2 - q^2) - k +
q^2/(2k) = -q^4/(2k (k + sqrt(k^2 - q^2))^2) (about -q^4/8k^3). A stationary state has the same
z-constant beta in vacuum (wavenumber K) and inside (wavenumbers near q_in = Re sqrt(K^2 + U_0),
= G/2 at the Bragg centre). To first order in N the crystal therefore sees the paraxial problem with
its mean potential changed by

    dV0_eff(K) = [N(q_in) - N(K)] / sigma < 0,

and nothing else to this order (the two Bragg components have nearly equal |q|; that the remainder
is negligible is confirmed by the split step, section 7). Numbers (out §8): dV0_eff = -2.05 to -2.13 mV across the
plateau (-2.09 mV at the centre); the plateau moves by +0.377 urad (+1.0e-3 of its width, d(eta) =
+2.0e-3); |R| is unchanged to 1e-13 inside the plateau; arg R changes by -2.0e-3 rad at the centre,
-5.1e-3 rad at eta = -0.9 and -4.2e-3 rad at eta = +0.9 (r = 0), diverging like 1/sqrt(1 - eta^2) at
the edges. The tool reproduces this scheme with `model="engine_exact_propagator"`. Two independent
confirmations: (a) the independent split step (section 7) measures arg(r_exact-prop/r_Fresnel) in
[-1.18e-3, -1.07e-3] rad against the predicted [-1.20e-3, -1.10e-3] rad (r = 0.1, |eta| <= 0.9; max
deviation 4.7e-5 rad); (b) the same model predicts M2's measured rung-1 difference between the two
propagators, -0.0052 %, -0.0137 %, -0.0451 % of |r| at 10, 16.47, 30 mrad (V0 = 12 V) against the
measured -0.005 %, -0.013 %, -0.045 % (M2 section 2, SECTION_READ; out §8).

### 4.3 Consequences for rung 2

* Run the rung-2 test with the Fresnel propagator against `model="exact"`: the a priori paraxial
  error is zero; any residual is discretisation, finite cell or finite depth (sections 5 to 8).
* Run it also with the exact propagator against `model="engine_exact_propagator"`; the difference
  between the two engine runs (same grid) is a sharp test of section 4.2 (reproduced to 4.7e-5 rad
  by the split step), because the common discretisation error cancels.
* The atomistic potential is not z-invariant: its in-plane Fourier components along z couple k_z to
  k_z + 2 pi h_z, and the paraxial treatment of those couplings is outside this derivation.

## 5. Build-up along the surface after a leading edge (item 4)

### 5.1 Model (DERIVED_HERE)

For a laterally uniform crystal the multislice is a z-invariant linear system in which z plays the
role of time (section 4.1: "energy" E = K^2/2k, dependence exp(-i E z)). A sheet beam whose lower
edge first touches the surface at z_c switches the incident field at the surface on at z_c. With
h(tau) the causal response of the surface (R(E) = int_0^inf h(tau) exp(i E tau) d tau, analytic for
Im E > 0), the reflected amplitude, normalised by the incident carrier, at distance Z = z - z_c
downstream of first contact is the step response

    A(Z) = int_0^Z h(tau) exp(i E_K tau) d tau  ->  R(E_K)   (Z -> inf).

On the exit plane the reflected ray from surface point z_s arrives at height (L - z_s) tan(theta)
above x_s, so A(Z) is visible as a profile along x. For a finite sheet (the rung-2 test beam) the
fraction of the reflected packet that has not emerged at the exit plane is of the order of the same
tail with Z the distance from the contact of the TOP edge of the beam to the exit plane (an estimate:
the earlier parts of the packet have had longer), and the field still inside the crystal at the exit
plane leaks into the read-out at a similar level (section 7).

### 5.2 Two-beam closed form (DERIVED_HERE)

The Laplace-transform identity int_0^inf J_1(t)/t exp(i eta t) dt = i (eta - sqrt(eta - 1) sqrt(eta + 1))
(principal roots, Im eta >= 0; the branch of 3.2; verified numerically for three complex eta to
< 3e-10, out §5, not cited) gives
R_D = i ph int_0^inf (J_1(t)/t) exp(i eta t) dt with ph = U_g/sqrt(U_g U_-g). Substituting
t = kc tau, eta = (E - E_B)/kc, with E_B = (G^2/4 - U_0)/(2k) and kc = sqrt(U_g U_-g)/(2k) = sigma V_g (1 + i r)
(both complex with absorption), identifies h and

    A_D(Z) = i ph int_0^Z [J_1(kc tau)/tau] exp(i (E_K - E_B) tau) d tau.

Without absorption the approach is a power law: from J_1(t) ~ sqrt(2/(pi t)) cos(t - 3 pi/4) and one
integration by parts, for large kc Z the deviation |A_D(Z) - R_D| is at most about
sqrt(2/pi) (kc Z)^(-3/2) / (1 - eta^2) inside the plateau (leading asymptotic order, not a rigorous
bound), with oscillations at the two band-edge detunings kc (1 +- eta). With absorption the branch points
E_B +- kc move to Im E = -r sigma (V0 -+ V_g); the slowest decay is exp(-Z/Z_a),
Z_a = 1/(r sigma (V0 - V_g)). For (0,0,8): kc = 7.549e-4 rad/A (1/kc = 1324.7 A, xi_g = pi/kc = 4161.7 A),
Z_a = 2133 A (r = 0.05) and 1066 A (r = 0.1); the asymptotic estimate gives Z(1e-2) = 24 551 A and Z(1e-3) = 113 957 A
at eta = 0, r = 0 (out §9). The closed form tends to R_D to < 1e-13 for r > 0 and to 1.4e-4 at
Z = 4e5 A for r = 0 (checks, out §9).

### 5.3 Two-beam build-up numbers for (0,0,8) (sharp edge; out §9)

|A_D(Z) - R_D| (and |arg(A_D/R_D)| in rad) at Z downstream of first contact:

```
            Z = 1000 A          2000 A            4000 A            8000 A            16000 A           32000 A
r=0.00 eta=-0.5: 6.7e-01(3.4e-01)  3.6e-01(1.6e-01)  8.0e-02(7.5e-02)  3.5e-02(1.3e-02)  1.2e-02(6.2e-03)  4.8e-03(4.3e-03)
r=0.00 eta=+0.0: 6.3e-01(4.3e-36)  3.1e-01(1.8e-34)  5.1e-02(1.5e-18)  1.9e-02(4.0e-18)  3.9e-03(3.1e-18)  1.6e-03(1.8e-18)
r=0.00 eta=+0.5: 6.7e-01(3.4e-01)  3.6e-01(1.6e-01)  8.0e-02(7.5e-02)  3.5e-02(1.3e-02)  1.2e-02(6.2e-03)  4.8e-03(4.3e-03)
r=0.05 eta=-0.5: 2.3e-01(2.6e-01)  9.0e-02(1.3e-01)  1.6e-03(2.5e-03)  1.4e-04(2.3e-05)  2.4e-06(1.5e-06)  6.5e-10(3.3e-11)
r=0.05 eta=+0.0: 2.4e-01(2.0e-02)  9.1e-02(1.5e-02)  2.4e-03(4.4e-03)  2.4e-04(4.4e-04)  3.4e-06(5.6e-06)  8.5e-10(1.1e-09)
r=0.05 eta=+0.5: 2.4e-01(2.3e-01)  9.5e-02(1.1e-01)  5.8e-03(4.9e-04)  4.7e-04(9.1e-04)  5.3e-06(1.0e-05)  1.2e-09(2.3e-09)
r=0.10 eta=-0.5: 9.5e-02(1.5e-01)  2.4e-02(5.6e-02)  4.7e-04(1.2e-03)  5.7e-06(1.2e-05)  1.4e-09(2.6e-09)  6.9e-15(6.7e-15)
r=0.10 eta=+0.0: 9.9e-02(1.6e-02)  2.5e-02(9.7e-03)  5.7e-04(1.5e-03)  6.9e-06(1.8e-05)  1.7e-09(4.2e-09)  3.9e-14(8.7e-15)
r=0.10 eta=+0.5: 9.8e-02(1.3e-01)  2.5e-02(4.4e-02)  7.3e-04(7.8e-04)  8.4e-06(2.5e-05)  2.0e-09(5.8e-09)  7.2e-15(7.0e-15)
```

Build-up lengths (smallest Z beyond which the criterion holds up to 4e5 A):

| r | eta | abs(R_D) | Z for abs(dA) <= 1e-2 (A) | Z for abs(dA) <= 1e-3 (A) | Z for abs(d arg) <= 1e-2 rad (A) |
|---|---|---|---|---|---|
| 0 | -0.5 | 1.0000 | 26 900 | 134 660 | 23 220 |
| 0 | 0 | 1.0000 | 22 580 | 113 560 | 0 (phase fixed at pi/2 by symmetry of the two-beam model) |
| 0 | +0.5 | 1.0000 | 26 900 | 134 660 | 23 220 |
| 0 | +0.9 | 1.0000 | 68 800 | 342 680 | 65 220 |
| 0.05 | -0.5 | 0.5007 | 3 500 | 7 100 | 3 720 |
| 0.05 | 0 | 0.5338 | 3 480 | 7 120 | 2 900 |
| 0.05 | +0.5 | 0.5143 | 3 660 | 7 340 | 3 560 |
| 0.05 | +0.9 | 0.4536 | 3 860 | 7 540 | 4 480 |
| 0.10 | -0.5 | 0.3186 | 2 560 | 3 720 | 3 180 |
| 0.10 | 0 | 0.3333 | 2 580 | 3 760 | 1 960 |
| 0.10 | +0.5 | 0.3249 | 2 600 | 3 860 | 3 020 |
| 0.10 | +0.9 | 0.3020 | 2 600 | 3 920 | 3 320 |

Reading: without absorption the reflected amplitude approaches its stationary value only as
(kc Z)^(-3/2): 2.3 to 2.7 um for 1 % in the central half of the plateau, 11 to 13 um for 0.1 %, and
7 to 34 um at eta = 0.9 (1 % and 0.1 %). With r = 0.05 (0.1) 1e-3 is reached after 7 100 to 7 540 A
(3 720 to 3 920 A), set by Z_a = 2133 A (1066 A). The atomistic M2 cells (1100 A after first contact at
the minimum build-up, up to +6600 A in the diagnosis, M2 section 10.2) are therefore far shorter
than the r = 0 build-up, consistent with M2's observation that the fixed-beam translation error does
not converge without absorption and decays with r = 0.1 (the atomistic potential adds non-specular
couplings that this 1D estimate does not contain).

### 5.4 Exact step response versus the two-beam one (out §10)

The exact R(E) (Bloch method, complex E) gives the exact step response by a damped FFT
(`step_response_fft`, DERIVED_HERE: by causality R is analytic for Im E > 0, so the Fourier integral
can be taken on Im E = gamma with the result multiplied by exp(gamma Z); period 2e5 A, gamma T = 25,
aliasing ~exp(-25)). A smooth leading edge S(z) = (1 + erf(z/w))/2, w = 400 A (about the sin^2 edge
of a sheet beam, e/tan(theta) = 124 to 496 A for e = 2 to 8 A, out §3), keeps the spectrum finite; the same
machinery applied to R_D reproduces the sharp-edge closed form convolved with S' to 7.0e-7 (r = 0)
and 9.0e-9 (r = 0.1). At the plateau centre:

| Z (A) | r = 0: abs(A_ex - R_ex) | r = 0: abs(A_D - R_D) | r = 0: abs(arg(A_ex/R_ex)) (rad) | r = 0.1: abs(A_ex - R_ex) | r = 0.1: abs(A_D - R_D) |
|---|---|---|---|---|---|
| 1953 | 0.327 | 0.330 | 9.6e-3 | 2.8e-2 | 2.9e-2 |
| 4004 | 5.22e-2 | 4.74e-2 | 2.0e-2 | 5.2e-4 | 6.7e-4 |
| 8008 | 1.97e-2 | 1.82e-2 | 8.2e-3 | 6.1e-6 | 7.3e-6 |
| 16016 | 4.66e-3 | 3.89e-3 | 2.8e-3 | 1.5e-9 | 1.7e-9 |
| 32031 | 1.65e-3 | 1.40e-3 | 7.5e-4 | 5e-12 | 5e-12 |

Beyond 4000 A the exact transient is 8 to 20 % larger than the two-beam one for r = 0 (the exact R(E)
also contains the Fresnel step and the third beams) and slightly smaller for r = 0.1; the two-beam lengths of 5.3 are
therefore good estimates, not bounds. Unlike the two-beam model, the exact phase at the centre is not
stationary during the build-up (|arg(A/R)| = 8e-3 rad at 8000 A for r = 0).

## 6. Numbers for the engine's conditions (item 5)

### 6.1 The engine's own potential (out §2)

Flat bulk-terminated Si(001) terrace from `reflection_holo.structure.build_si001_terraces` (41 layers,
[110] azimuth, one in-plane period, TEST_ONLY), wrapped by `build_reflection_cell`, realised slice by
slice by the engine's `AtomicPotential` (Kirkland, abTEM 1.0.10 scattering factors, static lattice),
averaged over y and z; least-squares Fourier fit V0 + sum_n [2 V_n cos + 2 W_n sin](2 pi n x'/(a/4)),
n <= 60, over 16 layer periods in the bulk, x' from an atomic plane. DERIVED_HERE: for infinite
projection the lateral average has the Fourier coefficients (1/Omega) sum_j F_j(f^2) exp(-2 pi i f x_j),
i.e. V_(0,0,4n) = 8 F((4n/a)^2)/a^3 (all eight atoms of the cubic cell in phase for (0,0,4n)), with F
the engine's `scattering_factor` (3D Fourier transform of the atomic potential, V A^3).

| (0,0,l) | f = l/a (1/A) | V_l fit, dx = 0.01 A (V) | V_l fit, dx = 0.02 A (V) | 8 F(f^2)/a^3 (V) |
|---|---|---|---|---|
| (0,0,0) | 0 | 13.902837 | 13.902842 | 13.902843 (= engine MIP) |
| (0,0,4) | 0.73653 | 2.740088 | 2.740093 | 2.740094 |
| (0,0,8) | 1.47305 | 1.035737 | 1.035742 | 1.035742 |
| (0,0,12) | 2.20958 | 0.546696 | 0.546701 | 0.546702 |
| (0,0,16) | 2.94610 | 0.326515 | 0.326520 | 0.326521 |
| (0,0,20) | 3.68263 | 0.213642 | 0.213647 | 0.213647 |
| (0,0,24) | 4.41916 | 0.150269 | 0.150274 | 0.150274 |

Sine terms <= 4e-8 V (centrosymmetric layer potential about an atomic plane); fit residuals 5.5e-3 V
(dx 0.01) and 2.8e-4 V rms. Used: V0 = 13.902843 V, V_008 = 1.035742 V (and V_004 ... V_048 for the
full layer potential). The value is independent of the pixel as long as 8/a lies below the grid's
Nyquist frequency (the engine builds the potential from exact structure factors). M2 section 10.2
estimated V_008 ~ 0.84 V; the engine's own value is 23.3 % larger (out §3). Static lattice: no Debye-Waller
factor (for Gaussian displacements of rms u per axis the ensemble average multiplies V_g by
exp(-2 pi^2 g^2 u^2) < 1, DERIVED_HERE; not evaluated here because u is a caller's input).

### 6.2 Plateau of (0,0,8), single harmonic, r = 0 (out §3)

* G = 2 pi (8/a) = 9.255461 rad/A (g = 1.473052 cycles/A, d = a/8 = 0.678863 A);
  U_0 = 5.077263 rad^2/A^2; |U_g| = 0.378249 rad^2/A^2.
* Two-beam centre: K_c = 4.042107 rad/A, theta_ext = 16.13477 mrad (theta_int = 18.47189 mrad); the
  package's `specular_condition_for((0,0,8))` with the same V0 gives 16.134748 mrad (it includes the
  (e V0)^2 term; difference 2.5e-8 rad).
* Two-beam edges 15.94690 to 16.32049 mrad: width 373.59 urad.
* EXACT gap edges (single harmonic): 15.94648 to 16.32008 mrad, width 373.595 urad, midpoint
  16.13328 mrad; both edges 0.41 urad below the two-beam ones (third-beam shift).
* EXACT gap of the FULL laterally averaged layer potential (V_004 ... V_048): 15.98286 to
  16.31535 mrad, width 332.49 urad, midpoint 16.14910 mrad: the (0,0,4), (0,0,12), ... harmonics
  narrow the (0,0,8) plateau by 11.0 % and shift its midpoint by +15.83 urad (+4.2 % of the
  single-harmonic width) (out §3). Relevant for later atomistic comparisons, not for the rung-2 continuum test.
* Extinction depth (amplitude) at the centre G/|U_g| = 24.47 A; kc = sigma V_g = 7.549e-4 rad/A,
  1/kc = 1324.7 A along z, extinction distance xi_g = pi/(sigma V_g) = 4161.7 A.

### 6.3 Rocking curves (out §6)

theta_ext (mrad), dth = theta - 16.13477 mrad (urad), eta the r = 0 two-beam deviation parameter (the
same angles for every r); R at x_s, truncation at a cosine maximum (t = 0). ex = exact (single
harmonic V_008 = 1.035742 V, V0 = 13.902843 V); 2b = two-beam matched; DR = Darwin + Fresnel step;
TT = Darwin/Takagi-Taupin; full = exact for the full layer potential (V_004 ... V_048, g = 4/a,
all cosine maxima at x_s).

```
--- r = 0.0 ---
  eta     theta     dth |   |R|ex  arg ex |   |R|2b  arg 2b |   |R|DR  arg DR |   |R|TT  arg TT | |R|full arg full
 -3.0  15.56435  -570.4 | 0.10099 -0.0000 | 0.10318 +0.0000 | 0.10091 +0.0000 | 0.17157 +0.0000 | 0.04624  +0.0000
 -2.0  15.75678  -378.0 | 0.20165 +0.0000 | 0.20353 +0.0000 | 0.20135 +0.0000 | 0.26795 +0.0000 | 0.12795  +0.0000
 -1.5  15.85213  -282.6 | 0.32159 +0.0000 | 0.32286 +0.0000 | 0.32084 +0.0000 | 0.38197 +0.0000 | 0.21648  -0.0000
 -1.0  15.94690  -187.9 | 1.00000 +0.0762 | 1.00000 +0.0000 | 1.00000 +0.0000 | 1.00000 +0.0000 | 0.45149  -0.0000
 -0.9  15.96579  -169.0 | 1.00000 +0.5207 | 1.00000 +0.5127 | 1.00000 +0.5149 | 1.00000 +0.4510 | 0.57827  -0.0000
 -0.5  16.04111   -93.7 | 1.00000 +1.1722 | 1.00000 +1.1653 | 1.00000 +1.1694 | 1.00000 +1.0472 | 1.00000  +1.0152
  0.0  16.13477     0.0 | 1.00000 +1.7080 | 1.00000 +1.7013 | 1.00000 +1.7057 | 1.00000 +1.5708 | 1.00000  +1.6701
  0.5  16.22789    93.1 | 1.00000 +2.2088 | 1.00000 +2.2028 | 1.00000 +2.2064 | 1.00000 +2.0944 | 1.00000  +2.2188
  0.9  16.30201   167.2 | 1.00000 +2.7497 | 1.00000 +2.7434 | 1.00000 +2.7451 | 1.00000 +2.6906 | 1.00000  +2.8040
  1.0  16.32049   185.7 | 0.94342 +3.1416 | 1.00000 +3.1416 | 1.00000 +3.1416 | 1.00000 +3.1416 | 0.81349  +3.1416
  1.5  16.41255   277.8 | 0.43592 +3.1416 | 0.43484 +3.1416 | 0.43659 +3.1416 | 0.38197 +3.1416 | 0.43116  +3.1416
  2.0  16.50411   369.3 | 0.32690 -3.1416 | 0.32526 +3.1416 | 0.32718 +3.1416 | 0.26795 +3.1416 | 0.32986  +3.1416
  3.0  16.68571   550.9 | 0.23263 -3.1416 | 0.23071 +3.1416 | 0.23272 +3.1416 | 0.17157 +3.1416 | 0.24203  +3.1416

--- r = 0.05 ---
  eta     theta     dth |   |R|ex  arg ex |   |R|2b  arg 2b |   |R|DR  arg DR |   |R|TT  arg TT | |R|full arg full
 -3.0  15.56435  -570.4 | 0.09949 +0.4651 | 0.10150 +0.4552 | 0.09942 +0.4646 | 0.16668 +0.2847 | 0.05064  +0.7471
 -2.0  15.75678  -378.0 | 0.18661 +0.5665 | 0.18830 +0.5595 | 0.18639 +0.5658 | 0.24729 +0.4172 | 0.12382  +0.6696
 -1.5  15.85213  -282.6 | 0.26631 +0.7042 | 0.26761 +0.6974 | 0.26594 +0.7030 | 0.31952 +0.5583 | 0.19205  +0.7495
 -1.0  15.94690  -187.9 | 0.37881 +0.9693 | 0.37955 +0.9621 | 0.37837 +0.9675 | 0.41768 +0.8153 | 0.29869  +0.9566
 -0.9  15.96579  -169.0 | 0.40233 +1.0399 | 0.40296 +1.0326 | 0.40191 +1.0380 | 0.43741 +0.8832 | 0.32419  +1.0191
 -0.5  16.04111   -93.7 | 0.48204 +1.3547 | 0.48228 +1.3471 | 0.48180 +1.3526 | 0.50069 +1.1891 | 0.42274  +1.3284
  0.0  16.13477     0.0 | 0.53532 +1.7627 | 0.53512 +1.7555 | 0.53530 +1.7608 | 0.53382 +1.5986 | 0.50143  +1.7621
  0.5  16.22789    93.1 | 0.53497 +2.1636 | 0.53441 +2.1573 | 0.53518 +2.1618 | 0.51431 +2.0185 | 0.51645  +2.1846
  0.9  16.30201   167.2 | 0.48919 +2.4676 | 0.48838 +2.4625 | 0.48960 +2.4661 | 0.45363 +2.3471 | 0.47778  +2.4954
  1.0  16.32049   185.7 | 0.47167 +2.5353 | 0.47078 +2.5305 | 0.47211 +2.5339 | 0.43270 +2.4211 | 0.46179  +2.5632
  1.5  16.41255   277.8 | 0.37711 +2.7829 | 0.37577 +2.7796 | 0.37748 +2.7821 | 0.32581 +2.6932 | 0.37486  +2.8066
  2.0  16.50411   369.3 | 0.30632 +2.9101 | 0.30466 +2.9077 | 0.30653 +2.9098 | 0.24951 +2.8336 | 0.30976  +2.9300
  3.0  16.68571   550.9 | 0.22725 +3.0251 | 0.22533 +3.0234 | 0.22732 +3.0249 | 0.16711 +2.9619 | 0.23673  +3.0401

--- r = 0.1 ---
  eta     theta     dth |   |R|ex  arg ex |   |R|2b  arg 2b |   |R|DR  arg DR |   |R|TT  arg TT | |R|full arg full
 -3.0  15.56435  -570.4 | 0.09611 +0.8888 | 0.09765 +0.8708 | 0.09605 +0.8880 | 0.15464 +0.5413 | 0.06020  +1.3169
 -2.0  15.75678  -378.0 | 0.16092 +1.0177 | 0.16213 +1.0051 | 0.16079 +1.0168 | 0.20975 +0.7343 | 0.11709  +1.2171
 -1.5  15.85213  -282.6 | 0.20675 +1.1544 | 0.20766 +1.1432 | 0.20660 +1.1532 | 0.24692 +0.8900 | 0.16113  +1.2881
 -1.0  15.94690  -187.9 | 0.25860 +1.3508 | 0.25910 +1.3406 | 0.25844 +1.3494 | 0.28641 +1.0998 | 0.21521  +1.4391
 -0.9  15.96579  -169.0 | 0.26890 +1.3970 | 0.26932 +1.3869 | 0.26875 +1.3955 | 0.29381 +1.1482 | 0.22665  +1.4786
 -0.5  16.04111   -93.7 | 0.30648 +1.5991 | 0.30654 +1.5896 | 0.30638 +1.5976 | 0.31865 +1.3597 | 0.27093  +1.6624
  0.0  16.13477     0.0 | 0.33836 +1.8755 | 0.33797 +1.8669 | 0.33835 +1.8740 | 0.33335 +1.6506 | 0.31374  +1.9299
  0.5  16.22789    93.1 | 0.34655 +2.1544 | 0.34575 +2.1468 | 0.34664 +2.1530 | 0.32486 +1.9488 | 0.33222  +2.2061
  0.9  16.30201   167.2 | 0.33531 +2.3614 | 0.33422 +2.3547 | 0.33546 +2.3602 | 0.30195 +2.1733 | 0.32766  +2.4108
  1.0  16.32049   185.7 | 0.33045 +2.4089 | 0.32930 +2.4025 | 0.33060 +2.4078 | 0.29453 +2.2252 | 0.32425  +2.4576
  1.5  16.41255   277.8 | 0.29920 +2.6125 | 0.29776 +2.6073 | 0.29936 +2.6117 | 0.25308 +2.4492 | 0.29912  +2.6563
  2.0  16.50411   369.3 | 0.26579 +2.7585 | 0.26413 +2.7541 | 0.26591 +2.7580 | 0.21342 +2.6113 | 0.27016  +2.7970
  3.0  16.68571   550.9 | 0.21364 +2.9306 | 0.21175 +2.9274 | 0.21370 +2.9304 | 0.15581 +2.8057 | 0.22338  +2.9601
```

### 6.4 Plateau summary (out §7)

| r | form | max abs(R) | abs(R)^2 FWHM (urad) | FWHM centre (mrad) | arg R at 16.13477 mrad | arg R at the FWHM edges | sweep across FWHM (rad) |
|---|---|---|---|---|---|---|---|
| 0 | exact | 1 (flat plateau) | 395.94 | 16.13636 | 1.7080 | 0.0000 -> 3.1416 | 3.1416 |
| 0 | two-beam matched | 1 | 395.94 | 16.13636 | 1.7013 | 0.0000 -> 3.1416 | 3.1416 |
| 0 | Darwin + Fresnel | 1 | 395.94 | 16.13636 | 1.7057 | 0.0000 -> 3.1416 | 3.1416 |
| 0 | Darwin/TT | 1 | 396.01 | 16.13356 | 1.5708 | 0.0000 -> 3.1416 | 3.1416 |
| 0.05 | exact | 0.54226 at 16.18140 mrad | 454.53 | 16.17794 | 1.7627 | 0.9830 -> 2.7685 | 1.7855 |
| 0.05 | two-beam matched | 0.54186 | 453.61 | 16.17748 | 1.7555 | 0.9758 -> 2.7633 | 1.7875 |
| 0.05 | Darwin + Fresnel | 0.54234 | 454.50 | 16.17887 | 1.7608 | 0.9847 -> 2.7696 | 1.7849 |
| 0.05 | Darwin/TT | 0.53439 | 454.71 | 16.13831 | 1.5986 | 0.7008 -> 2.5756 | 1.8749 |
| 0.1 | exact | 0.34697 at 16.21117 mrad | 642.82 | 16.24467 | 1.8755 | 1.2962 -> 2.8311 | 1.5350 |
| 0.1 | two-beam matched | 0.34624 | 641.07 | 16.24190 | 1.8669 | 1.2815 -> 2.8234 | 1.5419 |
| 0.1 | Darwin + Fresnel | 0.34704 | 641.87 | 16.24514 | 1.8740 | 1.2970 -> 2.8307 | 1.5337 |
| 0.1 | Darwin/TT | 0.33361 | 624.66 | 16.13782 | 1.6506 | 0.8412 -> 2.5226 | 1.6814 |

r = 0: the exact plateau (|R| = 1 to 1.6e-13) runs between the exact gap edges 15.94648 and
16.32008 mrad (373.60 urad, section 6.2); arg R = 0.00000 at the lower edge, 1.70007 at the midpoint
16.13328 mrad and pi at the upper edge (sweep 3.14158 rad). Closed-form width 2 sigma V_g/K_c =
373.51 urad; phase slope at the centre 5.355 rad/mrad; d(arg R)/dV0 = 1/V_g = 0.9655 rad/V (out §3).
With absorption the reflectivity peak moves to higher angle (16.181 and 16.211 mrad for r = 0.05 and
0.1: the proportional model also absorbs the mean potential, and the Darwin/TT form, which has no
step reflection, misses this shift), the curve broadens and the phase sweep across the FWHM falls
to 1.79 and 1.54 rad.

### 6.5 The engine's finite cell: clean depth above the numerical absorber (out §11)

`reflection_amplitude_engine_geometry`: clean crystal of depth D above the engine's bulk absorber
(W(x) = 100 V sin^2 over 15 A, the crystal potential continuing through it), then a strongly lossy
substrate (the engine instead wraps into its top absorber; the amplitude reaching the box bottom is
~exp(-30)). Checked against an independent piecewise-constant transfer-matrix discretisation of the
same cell (1.2e-8). |R_cell - R_inf| (single harmonic):

```
r = 0.00 D =    60 A: at eta -3.0:1.6e-01 -1.5:3.8e-01 -1.0:3.4e-01 -0.9:1.1e-01 +0.0:1.1e-02 +0.9:9.0e-02 +1.0:3.0e-01 +1.5:3.6e-01 +3.0:1.6e-01
r = 0.00 D =   100 A: at eta -3.0:1.6e-01 -1.5:3.0e-01 -1.0:2.0e-01 -0.9:2.4e-02 +0.0:4.4e-04 +0.9:2.1e-02 +1.0:1.9e-01 +1.5:2.6e-01 +3.0:1.6e-01
r = 0.00 D =   150 A: at eta -3.0:1.6e-01 -1.5:3.4e-01 -1.0:1.2e-01 -0.9:4.0e-03 +0.0:7.4e-06 +0.9:3.6e-03 +1.0:1.3e-01 +1.5:3.1e-01 +3.0:1.5e-01
r = 0.00 D =   250 A: at eta -3.0:1.6e-01 -1.5:3.2e-01 -1.0:5.1e-02 -0.9:1.1e-04 +0.0:2.1e-09 +0.9:1.1e-04 +1.0:8.6e-02 +1.5:2.8e-01 +3.0:1.6e-01
r = 0.05 D =    60 A: at eta -3.0:3.5e-03 -1.5:3.7e-03 -1.0:2.6e-03 -0.9:2.4e-03 +0.0:1.4e-03 +0.9:3.0e-03 +1.0:3.4e-03 +1.5:5.0e-03 +3.0:4.8e-03
r = 0.05 D =   100 A: at eta -3.0:3.0e-04 -1.5:2.2e-04 -1.0:1.0e-04 -0.9:8.2e-05 +0.0:2.7e-05 +0.9:1.2e-04 +1.0:1.6e-04 +1.5:3.8e-04 +3.0:5.2e-04
r = 0.05 D =   150 A: at eta -3.0:1.4e-05 -1.5:6.4e-06 -1.0:1.7e-06 -0.9:1.2e-06 +0.0:2.0e-07 +0.9:2.3e-06 +1.0:3.5e-06 +1.5:1.5e-05 +3.0:3.3e-05
r = 0.10 D =    60 A: at eta -3.0:7.7e-05 -1.5:8.0e-05 -1.0:7.2e-05 -0.9:7.1e-05 +0.0:6.8e-05 +0.9:9.8e-05 +1.0:1.0e-04 +1.5:1.3e-04 +3.0:1.4e-04
r = 0.10 D =   100 A: at eta -3.0:6.3e-07 -1.5:4.7e-07 -1.0:3.6e-07 -0.9:3.4e-07 +0.0:2.9e-07 +0.9:5.9e-07 +1.0:6.6e-07 +1.5:1.1e-06 +3.0:1.8e-06
```

Finding (DERIVED_HERE, 1D model). Without absorption the engine's absorber does NOT emulate a
semi-infinite crystal outside the plateau, whatever the clean depth (|dR| = 0.15 to 0.38 at
|eta| = 1.5 and 3 for every D from 60 to 250 A; 0.05 to 0.34 at |eta| = 1), although for V_g = 0
(rung 1) the same absorber reflects only 1.2e-4. Reason: near a Bragg condition the forward and backward Bloch waves differ in normal
wavevector only by 2 delta (0.2312 rad/A at eta = 3, 0 at the band edge), so the absorber ramp,
abrupt on the Bloch-wave beat length pi/delta (27.2 A at eta = 3, longer nearer the edge), reflects one
into the other; for V_g = 0 the momentum to be supplied is 2 q = 9.255 rad/A and the smooth ramp
cannot supply it (numbers out §3). Longer, weaker ramps
help only slowly (r = 0, D = 150 A: 400 A at 20 V leaves 0.10 at eta = +-1.5, 800 A at 20 V 0.02).
Inside the plateau the Bloch wave is evanescent and the error falls as exp(-2D/Lambda): 4.4e-4 at
D = 100 A, 7.4e-6 at 150 A, 2.1e-9 at 250 A at the centre (1.1e-4 at eta = +-0.9 for D = 250 A). With
physical absorption the transmitted wave dies before the absorber: r = 0.05, D = 150 A: <= 3.3e-5;
r = 0.1, D = 100 A: <= 1.8e-6 over |eta| <= 3.

Prediction for the M2 atomistic null-test cells (1D laterally averaged model only; H2 section 2.2
shows that in-plane beams matter for the atomistic crystal, so this is indicative): crystal A has
21 A of clean crystal above the absorber, crystal B (A plus two layers) 21 + a/2 A. In the fully
built-up (long-cell) limit the 1D model gives, at 16.1347 mrad, for the full layer potential:
|R_A| = 0.705 instead of 1 (r = 0), and a translation residual arg(R_B/R_A) = -8.1e-3, -9.5e-3,
-6.0e-3 rad with |R_B/R_A| = 1.066, 1.032, 1.013 for r = 0, 0.05, 0.1 (single harmonic: -1.8e-3 to
-4.4e-3 rad, 1.013 to 1.058). The M2 pass criterion |B/A - 1| <= 1e-2 would therefore fail for any
absorption in these cells even after complete build-up; M2 measured B/A = 1.014 at +5000 A with
r = 0.1 (M2 section 10.2, SECTION_READ), close to the 1.013 predicted here (the phase residuals are not
comparable: the measured +0.017 rad still contains the build-up transient and in-plane effects). With
D = 100 A (150 A) the predicted residuals fall to 1.6e-5 rad and 1.7e-5 (2.2e-7 rad and 1.2e-7) at
r = 0.05. Recommendation for the atomistic null-test study (not an engine change): a clean depth of
at least 100 A for r = 0.05 to 0.1; for r = 0 no clean depth gives a converged reflection with this
absorber outside the plateau.

## 7. Independent minimal 1D split step (NOT the engine; out §12)

To check sections 4 and 5 and the proposed protocol before the engine is run, the tool contains a
short re-implementation of the engine's DOCUMENTED 1D scheme (`split_step_1d`): symmetric split
step, 2/3 band limit on the propagator and on the transmission function, sin^2 numerical absorbers
(100 V, 15 A bulk, 10 A top), entrance vacuum 10 A, sheet beam (H = 24 A, 4 A edges, 2 A above x_s)
projected onto f < 0, the potential of section 8.1 (point-sampled harmonic times the cell-averaged
crystal fraction), and the read-out formula of `flat_reflection_coefficient` (threshold 0.05). It
is written from the engine's docstrings, shares no code with it, and validates nothing about the
engine. theta0 = 16.13477 mrad, extra vacuum 150 A (run F: bins every 2.453e-3 1/A = 61.5 urad), bins with
|eta| <= 3 compared with the reference at their own K (max over bins):

| run | r | propagator (reference model) | dx (A) | dz (A) | D (A) | Z_e (A) | nx, slices | max abs(dR) (abs(eta) <= 0.9) | max abs(d arg) (abs(eta) <= 0.9) |
|---|---|---|---|---|---|---|---|---|---|
| F | 0.1 | Fresnel (exact) | 0.025 | 1 | 100 | 5000 | 16308, 6612 | 4.39e-4 (4.39e-4) | 1.82e-3 (1.40e-3) rad |
| X | 0.1 | exact (engine_exact_propagator) | 0.025 | 1 | 100 | 5000 | 16308, 6612 | 4.47e-4 (4.40e-4) | 1.80e-3 (1.38e-3) rad |
| F_dx05 | 0.1 | Fresnel | 0.05 | 1 | 100 | 5000 | 8154, 6612 | 1.44e-3 (1.44e-3) | 7.38e-3 (4.58e-3) rad |
| F_dx0125 | 0.1 | Fresnel | 0.0125 | 1 | 100 | 5000 | 32616, 6612 | 2.02e-4 (1.92e-4) | 7.45e-4 (5.78e-4) rad |
| F_dz05 | 0.1 | Fresnel | 0.025 | 0.5 | 100 | 5000 | 16308, 13223 | 3.88e-4 (3.80e-4) | 1.52e-3 (1.21e-3) rad |
| F_r005 | 0.05 | Fresnel | 0.025 | 1 | 150 | 10000 | 21536, 11612 | 2.78e-4 (2.78e-4) | 9.17e-4 (5.82e-4) rad |

Run F, bins inside the plateau (r_ss = split step, R_ref = exact reference):

```
   F bin eta = -1.073: r_ss = 0.25108 exp(+1.31778 i), R_ref = 0.25100 exp(+1.31861 i)
   F bin eta = -0.747: r_ss = 0.28407 exp(+1.47024 i), R_ref = 0.28415 exp(+1.47135 i)
   F bin eta = -0.420: r_ss = 0.31292 exp(+1.64089 i), R_ref = 0.31296 exp(+1.64229 i)
   F bin eta = -0.091: r_ss = 0.33422 exp(+1.82296 i), R_ref = 0.33417 exp(+1.82412 i)
   F bin eta = +0.238: r_ss = 0.34544 exp(+2.00911 i), R_ref = 0.34546 exp(+2.00968 i)
   F bin eta = +0.569: r_ss = 0.34541 exp(+2.19120 i), R_ref = 0.34567 exp(+2.19179 i)
   F bin eta = +0.902: r_ss = 0.33499 exp(+2.36103 i), R_ref = 0.33524 exp(+2.36209 i)
```

Readings: (i) the Fresnel split step reproduces the Helmholtz R(K) over the whole rocking range to
4.4e-4, the residual being mainly discretisation (dx order 1.71 between 0.05 and 0.025 A; at 0.0125 A
the dx term no longer dominates, 2.0e-4, the rest being dz and the finite cell); section 4.1 is
confirmed. (ii) The exact-propagator run
agrees with the one-way model of section 4.2 as well as the Fresnel run agrees with the exact
reference, and the difference between the two runs (same grid, so the discretisation cancels) is
arg(r_X/r_F) in [-1.18e-3, -1.07e-3] rad against the predicted [-1.20e-3, -1.10e-3] rad
(max deviation 4.7e-5 rad) for |eta| <= 0.9. The model also reproduces M2's measured rung-1
difference between the two propagators: predicted -0.0052 %, -0.0137 %, -0.0451 % of |r| at 10,
16.47, 30 mrad (V0 = 12 V), measured -0.005 %, -0.013 %, -0.045 % (M2 section 2, SECTION_READ; out §8).
(iii) With Z_e = 5000 A (r = 0.1) and 10000 A (r = 0.05) the finite cell no longer limits the
accuracy.

## 8. Proposed engine test for rung 2 (cell, potential class, read-out, a priori tolerance)

Rationale. Rung 1 cannot see an error of the effective mean potential: its reflection coefficient
is real and negative for every K, so its phase is pi whatever V0 is. On the (0,0,8) plateau the phase
moves by 0.97 rad per volt of V0 (d arg R/dV0 = 1/V_g at the centre, out §3) and by 5.35 rad per mrad
of angle; rung 2 therefore tests the engine's effective potential at the mV level, the coupling
V_g through the width, and the phase origin through the phase at the plateau centre (1.708 rad, not
the Darwin pi/2, because of the refraction at the mean-potential step, section 3.2).

### 8.1 Potential class (to be written by the engine owner; NOT written here)

A laterally uniform periodic continuum potential, e.g. `ContinuumPeriodicPotential(cell, *, V0_V,
V0_label, harmonics, harmonics_label, physical_absorption, surface_profile="sharp")`, harmonics =
((g_per_A, V_g_V, t_A), ...), with

    V_j = f_j [V0 + sum 2 V_g cos(2 pi g (x_j - x_s + t))] (1 + i r),   uniform along y and along z
    for z >= crystal_start_z (front-face overlap fraction as in ContinuumTerracePotential),

f_j the crystal fraction of pixel j exactly as in `ContinuumTerracePotential.fill` (so V_g = 0
reproduces the rung-1 class bit for bit), the harmonic POINT-SAMPLED at the pixel centres (it is then
represented exactly on the grid; cell-averaging it would multiply V_g by sinc(pi g dx) = 0.99777 at
dx = 0.025 A, which changes R by up to 6.1e-4 (r = 0.1) and 9.6e-4 (r = 0.05), 40 to 65 % of the
tolerance of section 8.4; out §3, §12b), `mean_inner_potential_V()` = V0, and provenance recording V0, every
(g, V_g, t) with labels, and the realised V0 and V_g from a DFT of the interior samples over an
integer number of periods. Values for rung 2: V0 = 13.902843 V and V_g = 1.035742 V (the engine's own
Kirkland values, section 6.1; label e.g. "TEST_ONLY: Kirkland IAM values of the engine, P2 report"),
g = 8/a = 1.473052 cycles/A, t = 0 (cosine maximum at x_s). With the current engine tree
(MultisliceParams now requires `working_reflections_hkl`, () for a continuum cell) the class and
the band assertion must agree on whether the harmonic is declared; that choice is the engine
owner's.

### 8.2 Cell, beam and run parameters (all TEST_ONLY; the cell passes the engine's assertions)

| item | R2-A (primary, absorbing) | R2-B (secondary, r = 0, Darwin sweep) |
|---|---|---|
| cell | `build_continuum_cell`, one terrace, extent_y 10 A, ny = 1 | same |
| absorption r | 0.1 and 0.05 | 0 |
| clean depth D (x_s = 15 A + D) | 100 A (r = 0.1), 150 A (r = 0.05) | 250 A |
| bulk / top absorber | 15 A / 10 A, NumericalAbsorber(100 V, "sin2") | same |
| entrance vacuum | 10 A | same |
| beam | SheetBeam H = 24 A, edge 4 A, x_bottom = x_s + 2 A | same |
| theta_in | 16.13477 mrad (two-beam centre with V0 = 13.902843 V) | same |
| exit distance Z_e = L - z_top, z_top = (2 + 24)/tan(theta) = 1611.3 A | 5000 A (r = 0.1), 10000 A (r = 0.05) | 30000 A |
| vacuum above x_s | H + 2 + L tan(theta) + 150 A (bins every 2.45e-3 1/A = 61.5 urad for r = 0.1) | same |
| grid | dx = 0.025 A (and 0.05 A for the order check), dz = 1 A | dx 0.025 A, dz 1 A |
| propagator | "fresnel" (reference model "exact") and "exact" (reference model "engine_exact_propagator") | "fresnel" |
| other | band "2/3", complex128, numpy, buildup_depth_A = 20 | same |

### 8.3 Read-out

`flat_reflection_coefficient(ew, psi0, x_surface_A = x_s, propagator = <same>, rel_threshold = 0.05)`
gives r(f) per incident bin; each bin is compared with
`reflection_amplitude(asin(lambda f), 200, V0, [V_g], g, r, plane_offset_A = t, model = ...)` at its
own K = 2 pi f, over the bins with |eta| <= 3 for R2-A and |eta| <= 0.5 for R2-B (R2-B with the
vacuum-only read-out of section 8.4)
(eta = (K^2 - K_c^2)/|U_g| with K_c = 4.042107 rad/A, |U_g| = 0.378249 rad^2/A^2). No fitted phase or
angle offset is allowed: the reference plane is x_s and the angle of a bin is fixed by its frequency.

### 8.4 A priori tolerance (set before any engine run)

Criterion (a), R2-A: max over the bins with |eta| <= 3 of |r_engine - R_ref| <= T_A = 1.5e-3 (the
complex difference; it implies |arg(r/R_ref)| <= T_A/|R_ref|, i.e. <= 2.8e-3 rad (r = 0.05) and
<= 4.4e-3 rad (r = 0.1) at the plateau centre and <= 1.6e-2 rad at |eta| = 3). Budget (maxima over the
same bins):

| contribution | r = 0.1 (D 100 A, Z_e 5000 A) | r = 0.05 (D 150 A, Z_e 10000 A) | source |
|---|---|---|---|
| reference solver | <= 1e-9 | <= 1e-9 | section 2 |
| paraxial error, Fresnel propagator | 0 (identity) | 0 | section 4.1 |
| exact propagator | modelled (`engine_exact_propagator`), residual <= 5e-5 rad | same | sections 4.2, 7 |
| (e V)^2 term | absent from engine and reference | same | section 1 |
| clean depth + numerical absorber | <= 1.8e-6 | <= 3.3e-5 | section 6.5 |
| finite cell + discretisation (dx 0.025 A, dz 1 A) | 4.4e-4 (split step F; 2.0e-4 at dx 0.0125 A) | 2.8e-4 (split step F_r005) | section 7 |
| total | <= 4.5e-4 | <= 3.2e-4 | |
| tolerance T_A | 1.5e-3 | 1.5e-3 | 3.3x and 4.7x the budget, for a different sub-pixel position of x_s and implementation details of the class |

Criterion (b), propagator pair (R2-A, r = 0.1): for |eta| <= 0.9,
|arg(r_exact-prop/r_Fresnel) - arg(R_engine_exact_propagator/R_exact)| <= 2e-4 rad (split step: 4.7e-5).
Criterion (c), convergence: max |dR| at dx = 0.05 A over that at dx = 0.025 A >= 2^1.5 (split step:
3.3, order 1.71).

What T_A detects (out §12b; same angles as the R2-A bins):

| perturbation of the reference | r = 0.1: max abs(dR) (max abs(d arg)) | r = 0.05: max abs(dR) (max abs(d arg)) | caught by (a)? |
|---|---|---|---|
| V0 + 1 mV | 2.0e-4 (5.8e-4 rad) | 4.3e-4 (8.2e-4 rad) | no |
| V0 + 5 mV | 9.8e-4 (2.9e-3 rad) | 2.1e-3 (4.1e-3 rad) | yes at r = 0.05 |
| V_g x sinc(pi g dx), dx = 0.025 A (cell-averaged harmonic) | 6.1e-4 (1.1e-3 rad) | 9.6e-4 (9.0e-4 rad) | no: point-sample the harmonic |
| V_g x sinc(pi g dx), dx = 0.05 A | 2.4e-3 (4.3e-3 rad) | 3.8e-3 (3.6e-3 rad) | yes |
| cosine origin 0.01 A below x_s | 3.1e-2 (0.14 rad) | 5.0e-2 (0.16 rad) | yes (phase-origin bookkeeping to ~5e-4 A) |
| read-out plane 0.01 A off x_s | arg R changes by 0.078 to 0.084 rad | same | yes |
| exact propagator compared with the Helmholtz reference | 4.1e-4 (1.2e-3 rad) | 9.0e-4 (1.7e-3 rad) | no; criterion (b) catches it |
| Darwin/TT used as the reference | 7.6e-2 | 8.8e-2 | yes |

A tighter variant (dx = 0.0125 A, budget 2.0e-4, T_A = 6e-4) would catch a 2 mV error of V0 at
r = 0.05; it costs twice the points.

R2-B (r = 0, Darwin sweep): optional, qualitative. With r = 0 the whole-box read-out is contaminated by the
field that the numerical absorber traps between itself and the surface (section 6.5): in the split
step (section 7, out §12 --long; D = 250 A, Z_e = 30000 A) its error is 1.8e-2 to 2.3e-2 in
|eta| <= 0.5, with a phase error alternating in sign from bin to bin (the signature of a contribution
located about half a box away from the reflected packet), and up to 0.19 outside the plateau. A
vacuum-only read-out, multiplying the exit wave by w(x) = sin^2(pi/2 clip((x - x_s - 60 A)/40 A, 0, 1))
before `flat_reflection_coefficient` (a test-side operation, no engine change), removes most of it:
max |dR| = 1.1e-2 in |eta| <= 0.5 (3.6e-2 in |eta| <= 0.9, the r = 0 build-up being slow near the
edges; 2e-3 to 8e-3 far outside the plateau). Criterion: max over |eta| <= 0.5 of |r - R_ref| <=
T_B = 3e-2 with the vacuum-only read-out. It checks the Darwin sweep (exact arg R from 1.1722 to
2.2088 rad across these bins) and rejects the Darwin/TT reference (1.38e-1) and a 0.01 A phase-origin
error (1.0e-1), but not a 5 mV error of V0 (5.9e-3, out §12b); the absorbing cases R2-A are the
quantitative test.

### 8.5 What rung 2 does not test

The in-plane (non-specular) scattering of an atomistic crystal (H2 section 2.2), the atomistic
potential construction (already cross-checked against abTEM, M2 section 4), the numerical absorber
for r = 0 outside the plateau (a property of the cell, section 6.5), frozen phonons, and steps. The
test does test the effective mean potential and coupling, the phase origin (surface plane, cosine
origin, read-out plane), the refraction at the mean-potential step, the propagators, the absorption
model and the build-up in z.

### 8.6 Cost

1D (ny = 1): two FFTs of nx points per slice, nx x slices = 16308 x 6612 (r = 0.1), 21536 x 11612
(r = 0.05), 38444 x 31612 (R2-B), as in the split step (section 7), which performs the same FFTs as
the engine. The whole tool run including all split steps took 20 min 27 s wall (13 min 24 s CPU) on
this shared 4-core machine (load average 11 to 18 seen with `uptime` during the runs; section 11); memory is tens of MB per run (tool peak
389 MB including the atomistic potential analysis).

## 9. Comparison with H2 sections 2.1 to 2.3 (read only after the derivations and the code were final)

H2 (`docs/agent_reports/H2_realistic_supercell_sizing.md`, sections 2.1 to 2.3, SECTION_READ) sizes an
atomistic cell; this report builds a reference for the laterally uniform continuum test. Agreement
and every difference:

| item | H2 | this report | status |
|---|---|---|---|
| V_(0,0,8) of the engine's Kirkland potential | 1.0357 V (Kirkland F at 1.4731 1/A, abs(S) = 8); M2's 0.84 V is 23 % low | 1.035742 V, from the engine's realised potential of a built flat cell AND from 8 F(f^2)/a^3 (agree to 3.7e-7 V at dx 0.02 A) | agree |
| penetration at the centre | Lambda = 1/b = G/u_g = 24.47 A | 24.469 A | agree |
| extinction distance | xi_g = 4161.7 A | 4161.7 A | agree |
| build-up scale along z | L_b = 1/(b tan theta_int) = 1324.5 A = xi_g/pi to 1.3e-4 | 1/kc = 1/(sigma V_g) = 1324.7 A (paraxial E-units) | agree; the 1.3e-4 is the exact-vs-paraxial z-scale cos(theta) (section 4.1) |
| Darwin width | 0.3736 mrad external (0.3263 internal), two-beam | 373.59 urad two-beam; EXACT gap 373.595 urad, both edges 0.41 urad lower | agree; the exact edge shift is new |
| two-beam amplitude | X = -(eta + q)/c (H2's eta = kappa0 - G/2, first order in eta/G; its X is the Darwin/TT ratio) | same function as R_D (section 3.2) with eta_here = eta_H2/c to first order | agree as a function |
| amplitude at the Bragg angle with absorption | abs(X) = 0.534 (r = 0.05), 0.333 (r = 0.1) | R_D: 0.53382, 0.33335; EXACT at the same angle 0.53532, 0.33836; exact maxima 0.54226 at 16.18140 mrad and 0.34697 at 16.21117 mrad | DIFFERENCE: X omits the Fresnel reflection at the mean-potential step; harmless for sizing, but the TT/Darwin phase is 0.135 rad too small at the centre (r = 0) and misses the +33 and +62 urad peak shifts with absorption (section 3.4) |
| premise "the exact propagator reproduces K^2 = k^2 + 2 k sigma V for the mean potential" (H2 P2) | stated as exact (SM04 vs 2 k sigma V agree to 4e-10) | exact only for the FRESNEL propagator (section 4.1); the engine's exact propagator acts like V0 - 2.09 mV at (0,0,8) (+0.377 urad plateau shift, -2.0e-3 rad at the centre; confirmed by the split step and by M2's rung-1 exact-vs-Fresnel differences, section 4.2) | DIFFERENCE (small; matters for rung-2 phases, not for sizing). The (e V0)^2 term: external Bragg angle 2.5e-8 rad, U_0 9.9e-6 relative (H2's 4e-10 compares a different quantity; not a contradiction) |
| leading-edge transient | g(s) = i J1(c s) exp(i eta0 s)/s, s = z tan(theta_int); relative error E = 1 - A/X | A_D(Z) = i ph int_0^Z J_1(kc tau)/tau exp(i (E_K - E_B) tau) d tau: the same Green's function (c s = kc tau, eta0 s = (E_K - E_B) tau to first order in eta/G and O(theta^2)) | agree |
| r = 0 run-in at the Bragg angle | 22 572 A (1e-2), 113 552 A (1e-3); envelope sqrt(2/pi)(b s)^(-3/2) | 22 580 A and 113 560 A (20 A grid) at eta = 0; asymptotic estimate sqrt(2/pi)(kc Z)^(-3/2)/(1 - eta^2) | agree; NEW: off-centre it is much longer (eta = 0.9: 68 800 A for 1e-2, 342 680 A for 1e-3) |
| r = 0.05, 0.1 run-in | relative error: 3721 / 7538 A (r = 0.05), 3194 / 4290 A (r = 0.1) for 1e-2 / 1e-3 | absolute error at eta = 0: 3480 / 7120 A and 2580 / 3760 A; H2's relative values at 1000 and 2000 A (0.46, 0.17; 0.30, 0.074) equal mine divided by abs(R) | agree (different criterion: H2 relative, here absolute and phase) |
| slow and fast absorption decay | exp(-sigma r (V0 -+ V_g) L) | Z_a = 1/(r sigma (V0 - V_g)) = 2133 A / 1066 A; fast 1837 / 918 A | agree |
| two-beam vs exact transient | two-beam only | exact step response from the exact R(E) (damped FFT) is 8 to 20 % larger than the two-beam one beyond 4000 A for r = 0 (section 5.4) | NEW |
| validity of two beams | section 2.2: for the ATOMISTIC crystal the (0,0,8) condition is many-beam (in-plane (0,+-4,4) exactly excited at [100], admixtures 0.2 to 0.35 at [110]); two-beam numbers are order-of-magnitude guides | for the laterally UNIFORM test potential the 1D problem is exact and the refracted Darwin form is within 5.7e-3 (r = 0, abs(eta) <= 0.9) of it; the specular-rod systematic row of the atomistic layer potential (V_004, V_012, ...) narrows the plateau by 11 % and shifts it by +15.8 urad | different scope, no contradiction: H2's in-plane beams are outside the 1D model (premise P3), which is why rung 2 must use the continuum potential and why my 1D predictions for atomistic cells (section 6.5) are indicative only |
| penetration with absorption | 20.3 A (r = 0.05), 14.6 A (r = 0.1) | not computed | H2 only |

## 10. Files, API, status

* `tools/physics_checks/rung2_reference.py` (new; importable, numpy/scipy; the engine potential
  analysis imports the repository and abTEM lazily):
  * `reflection_amplitude(theta_rad, energy_keV, V0_V, Vg_list, g_per_A, absorption_ratio, *,
    plane_offset_A=0.0, method="bloch"|"floquet"|"depth", model="exact"|"engine_exact_propagator",
    n_plane_waves=None, klein_gordon_V2=False, depth_A=None) -> complex | ndarray`: the exact R(theta)
    at the truncation plane (sections 1, 2); `reflection_amplitude_K(K, ...)` the same versus the
    normal wavevector (complex K allowed).
  * `two_beam_reflection(theta_rad, ..., order, form="bloch_matched"|"darwin_refracted"|"darwin")`
    (section 3); `darwin_plateau(...)`, `theta_of_eta(...)`, `exact_band_edges(...)`.
  * `build_up_two_beam(Z_A, theta_rad, ...)`, `build_up_length(theta_rad, ..., tols=(("abs", 1e-3),
    ("phase", 1e-2)))`, `step_response_fft(theta_rad, ..., switch_width_A, R_of_K)` (section 5).
  * `oneway_V0_shift_V(K, slab, bc)` (section 4.2); `reflection_amplitude_engine_geometry(...)`
    (finite clean depth above the engine's numerical absorber, section 6.5).
  * `engine_potential_harmonics(dx_A=...)` (section 6.1); `split_step_1d(...)` (section 7; NOT the
    engine).
  * `main()`: every number of this report and the self-checks; exit status 1 if a check fails.
* `docs/agent_reports/P2_rung2_reference.md` (this report).
* No engine code, test, summary document or other report was modified; nothing was committed.

NOT RUN and open items:

* The engine itself was NOT run for rung 2 (deliberately: the continuum periodic potential class does
  not exist, and the tolerance above is set before any engine result). Status of rung 2: reference
  and protocol ready; engine test NOT RUN.
* The one-dimensional model is exact only for the laterally uniform test potential. For atomistic
  cells its predictions (section 6.5, the M2 null-test geometry) are indicative: H2 section 2.2 shows
  strong in-plane beams at this condition. Not quantified here.
* Static lattice (no Debye-Waller reduction of V_008), independent-atom Kirkland potential (SM17
  UNVERIFIED), proportional absorption with TEST_ONLY ratios (PROJECT_INPUT item 21 open), spin
  neglected, (e V)^2 term quantified (1.3e-4 rad) but not included.
* The engine owner must decide how the new class declares its harmonic to the band assertion
  (`working_reflections_hkl`, currently () for continuum cells).
* Recommendations that follow from this work (none applied): (1) implement the class of 8.1 and run
  R2-A (and optionally R2-B) with the tolerances of 8.4; (2) compare flat-surface R(K) with the
  Fresnel propagator, or apply `oneway_V0_shift_V` to references for the exact propagator; (3) for
  atomistic (0,0,8) null tests use >= 100 A of clean crystal above the absorber with r >= 0.05 (21 A
  gives a 1.3 to 6.6 % amplitude residual even after complete build-up in the 1D model); with r = 0
  the absorber cannot emulate a semi-infinite crystal outside the plateau.

Status: final (2026-09-23). Tool run: 57 self-checks, 0 failed (section 11).

## 11. Verbatim output of the final run

`venv/bin/python -u tools/physics_checks/rung2_reference.py --long` (2026-09-23, shared 4-core
machine; `time`: real	20m27.457s user	13m23.522s sys	0m1.462s):

```

====================================================================================================
1. Beam constants (reflection_holo.constants only) and cross-checks against the package
====================================================================================================
lambda = 0.02507934 A, k = 250.5323 rad/A, sigma = 7.288401e-04 rad/(V A), gamma = 1.391390, hbar c = 1973.2698 eV A
   CHECK PASS  lambda vs reflection_holo.geometry.wavelength: got 0.02507934045 want 0.02507934045 err 0.000e+00 tol 1.0e-14 (relative)
   CHECK PASS  lambda vs physics_conventions 0.02507934 A: got 0.02507934045 want 0.02507934 err 4.505e-10 tol 5.0e-09
   CHECK PASS  k vs reflection_holo.geometry.wavelength: got 250.5323184 want 250.5323184 err 0.000e+00 tol 1.0e-14 (relative)
   CHECK PASS  sigma vs engine physics.interaction_constant: got 0.0007288401041 want 0.0007288401041 err 0.000e+00 tol 1.0e-14 (relative)
   CHECK PASS  300 keV refused 

====================================================================================================
2. Engine potential: laterally averaged Kirkland potential of a flat Si(001) cell
====================================================================================================
dx = 0.01000 A, nx = 7931, 41 atoms, fit rms residual 5.46e-03 V; MIP (8 F(0)/a^3) = 13.902843 V; fitted V0 = 13.902837 V
   (0,0, 4): f = 0.73653 1/A  V_n(fit) = 2.740088 V  W_n(sine) = -6.7e-09 V  8F(f^2)/a^3 = 2.740094 V
   (0,0, 8): f = 1.47305 1/A  V_n(fit) = 1.035737 V  W_n(sine) = -1.3e-08 V  8F(f^2)/a^3 = 1.035742 V
   (0,0,12): f = 2.20958 1/A  V_n(fit) = 0.546696 V  W_n(sine) = -2.0e-08 V  8F(f^2)/a^3 = 0.546702 V
   (0,0,16): f = 2.94610 1/A  V_n(fit) = 0.326515 V  W_n(sine) = -2.7e-08 V  8F(f^2)/a^3 = 0.326521 V
   (0,0,20): f = 3.68263 1/A  V_n(fit) = 0.213642 V  W_n(sine) = -3.4e-08 V  8F(f^2)/a^3 = 0.213647 V
   (0,0,24): f = 4.41916 1/A  V_n(fit) = 0.150269 V  W_n(sine) = -4.0e-08 V  8F(f^2)/a^3 = 0.150274 V
dx = 0.02000 A, nx = 3966, 41 atoms, fit rms residual 2.82e-04 V; MIP (8 F(0)/a^3) = 13.902843 V; fitted V0 = 13.902842 V
   (0,0, 4): f = 0.73653 1/A  V_n(fit) = 2.740093 V  W_n(sine) = -2.6e-09 V  8F(f^2)/a^3 = 2.740094 V
   (0,0, 8): f = 1.47305 1/A  V_n(fit) = 1.035742 V  W_n(sine) = -5.2e-09 V  8F(f^2)/a^3 = 1.035742 V
   (0,0,12): f = 2.20958 1/A  V_n(fit) = 0.546701 V  W_n(sine) = -7.8e-09 V  8F(f^2)/a^3 = 0.546702 V
   (0,0,16): f = 2.94610 1/A  V_n(fit) = 0.326520 V  W_n(sine) = -1.0e-08 V  8F(f^2)/a^3 = 0.326521 V
   (0,0,20): f = 3.68263 1/A  V_n(fit) = 0.213647 V  W_n(sine) = -1.3e-08 V  8F(f^2)/a^3 = 0.213647 V
   (0,0,24): f = 4.41916 1/A  V_n(fit) = 0.150274 V  W_n(sine) = -1.6e-08 V  8F(f^2)/a^3 = 0.150274 V
   CHECK PASS  fitted V_008 vs analytic 8F/a^3 (dx 0.01): got 1.035737148 want 1.035742493 err 5.345e-06 tol 1.0e-04
   CHECK PASS  fitted V0 vs MIP (dx 0.01): got 13.90283721 want 13.90284255 err 5.341e-06 tol 1.0e-04
   CHECK PASS  sine term of (0,0,8) vanishes (dx 0.01): got -1.33954049e-08 want 0 err 1.340e-08 tol 1.0e-05
   CHECK PASS  fitted V_008 vs analytic 8F/a^3 (dx 0.02): got 1.035742127 want 1.035742493 err 3.657e-07 tol 1.0e-04
   CHECK PASS  fitted V0 vs MIP (dx 0.02): got 13.90284219 want 13.90284255 err 3.650e-07 tol 1.0e-04
   CHECK PASS  sine term of (0,0,8) vanishes (dx 0.02): got -5.206919673e-09 want 0 err 5.207e-09 tol 1.0e-05
   CHECK PASS  MIP 13.903 V (M2, D3 F16): got 13.90284255 want 13.903 err 1.574e-04 tol 5.0e-04
USED: V0 = 13.902843 V, V_004 = 2.740094 V, V_008 = 1.035742 V, V_012 = 0.546702 V, V_016 = 0.326521 V (static lattice, independent atoms; ASSUMPTION of the engine)
(0,0,8): g = 8/a = 1.473052 cycles/A, G = 2 pi g = 9.255461 rad/A, d = a/8 = 0.678863 A; (0,0,4) fundamental g = 0.736526 cycles/A

====================================================================================================
3. Two-beam plateau parameters of (0,0,8) (r = 0) and exact band edges
====================================================================================================
U_0 = 2 k sigma V0 = 5.077263 rad^2/A^2, |U_g| = 0.378249 rad^2/A^2
centre: K_c = 4.042107 rad/A, theta_ext = 16.13477 mrad (theta_int = 18.47189 mrad)
two-beam edges: 15.94690 to 16.32049 mrad, width 0.37359 mrad = 373.59 urad
extinction (amplitude) depth at the centre G/|U_g| = 24.469 A; coupling kc = sigma V_g = 7.548907e-04 rad/A; 1/kc = 1324.7 A along z; xi_g = pi/(sigma V_g) = 4161.7 A
closed-form width 2 sigma V_g / K_c = 373.51 urad (= 2 kc in E-units: 1.5098e-03 rad/A); Darwin phase slope at the centre d(arg R)/d(theta) = K_c/(sigma V_g) = 5.355 rad/mrad; d(arg R)/dV0 = 1/V_g = 0.9655 rad/V; d(arg R)/dV_g = 0 at the centre
derived quantities quoted in the report: U_g/G^2 = 4.416e-03; K_c^2/(4 k^2) = 6.51e-05 (paraxial vs exact z-dispersion); 2 q_c = 9.255 rad/A (momentum a smooth absorber ramp must supply for V_g = 0); at eta = 3 the Bloch waves differ by 2 delta = 0.2312 rad/A (beat length pi/delta = 27.2 A); sinc(pi g dx) = 0.99777 (dx 0.025 A), 0.99110 (dx 0.05 A); sheet-beam edge along z e/tan(theta_c) = 124 to 496 A for e = 2 to 8 A; top-edge contact of the test beam z_top = (2 + 24 A)/tan(theta_c) = 1611.3 A; V_008/0.84 V - 1 = +0.233 (M2 estimate)
package specular_condition_for((0,0,8)) theta_ext = 16.134748 mrad (exact SM04 Delta incl. V0^2 term)
   CHECK PASS  TT centre vs package specular condition: got 0.01613477295 want 0.01613474844 err 2.451e-08 tol 1.0e-07
EXACT band edges (single harmonic): 15.94648 to 16.32008 mrad, width 373.595 urad, midpoint 16.13328 mrad; shifts vs two-beam: low -0.416 urad, high -0.409 urad
full layer potential vs single harmonic: width change -11.0 %, midpoint shift +15.83 urad = +4.2 % of the single-harmonic width
EXACT band edges (full layer potential, harmonics (0,0,4)...(0,0,48)): 15.98286 to 16.31535 mrad, width 332.492 urad, midpoint 16.14910 mrad

====================================================================================================
4. Exact solver cross-checks (r = 0, 0.05, 0.1)
====================================================================================================
r = 0.0: max |R_bloch(M=8) - R_floquet| = 6.27e-12; max |R(M=8) - R(M=4)| = 2.15e-12
   CHECK PASS  Bloch vs Floquet-ODE, single harmonic, r = 0.0: got 6.267289713e-12 want 0 err 6.267e-12 tol 1.0e-09
   CHECK PASS  plane-wave convergence M=4 vs 8, r = 0.0: got 2.146122375e-12 want 0 err 2.146e-12 tol 1.0e-09
r = 0.05: max |R_bloch(M=8) - R_floquet| = 9.10e-13; max |R(M=8) - R(M=4)| = 3.36e-13
   CHECK PASS  Bloch vs Floquet-ODE, single harmonic, r = 0.05: got 9.097082819e-13 want 0 err 9.097e-13 tol 1.0e-09
   CHECK PASS  plane-wave convergence M=4 vs 8, r = 0.05: got 3.359813196e-13 want 0 err 3.360e-13 tol 1.0e-09
r = 0.1: max |R_bloch(M=8) - R_floquet| = 3.90e-13; max |R(M=8) - R(M=4)| = 2.21e-13
   CHECK PASS  Bloch vs Floquet-ODE, single harmonic, r = 0.1: got 3.900092791e-13 want 0 err 3.900e-13 tol 1.0e-09
   CHECK PASS  plane-wave convergence M=4 vs 8, r = 0.1: got 2.214892569e-13 want 0 err 2.215e-13 tol 1.0e-09
full layer potential (12 harmonics): max |R(M=48) - R(M=24)|, |R(M=48) - R_floquet| = 2.98e-10
   CHECK PASS  multi-harmonic Bloch M=24/48 vs Floquet: got 2.977355375e-10 want 0 err 2.977e-10 tol 1.0e-08
r = 0.05: finite crystal D = 600 A on a uniform substrate vs semi-infinite: max |dR| = 1.10e-11
   CHECK PASS  finite depth -> semi-infinite, r = 0.05: got 1.101086947e-11 want 0 err 1.101e-11 tol 1.0e-07
r = 0.1: finite crystal D = 400 A on a uniform substrate vs semi-infinite: max |dR| = 5.29e-12
   CHECK PASS  finite depth -> semi-infinite, r = 0.1: got 5.289654028e-12 want 0 err 5.290e-12 tol 1.0e-07
r = 0, plateau centre, D = 100 A: |R_D - R_inf| = 5.60e-04 (expected ~ exp(-2 D / 24.47 A) = 2.8e-04)
r = 0, plateau centre, D = 200 A: |R_D - R_inf| = 1.57e-07 (expected ~ exp(-2 D / 24.47 A) = 8.0e-08)
r = 0, plateau centre, D = 400 A: |R_D - R_inf| = 1.72e-11 (expected ~ exp(-2 D / 24.47 A) = 6.3e-15)
   CHECK PASS  r = 0 plateau centre: finite depth 400 A = semi-infinite: got 1.722928846e-11 want 0 err 1.723e-11 tol 1.0e-09
r = 0, eta = 1.5 (band, propagating): |R_D - R_inf| for D = 300..303, 600, 601 A: 0.280, 0.276, 0.274, 0.271, 0.286, 0.290  (no convergence without absorption)
   CHECK PASS  r = 0 selection equals the r -> 0+ limit: got 5.137406781e-09 want 0 err 5.137e-09 tol 1.0e-07

====================================================================================================
5. Limits: Fresnel step (rung 1), unitarity, two-beam basis, Darwin form
====================================================================================================
V_g = 0, V0 = 12 V, 10.00 mrad: R = -0.131627-0.0e+00i; (K-q)/(K+q) = -0.131627; M2 analytic (SM04 dK) = -0.131628
   CHECK PASS  Fresnel limit at 10.00 mrad: got -0.1316274352 want -0.1316274352 err 1.665e-16 tol 1.0e-12
   CHECK PASS  rung-1 analytic (SM04 dK incl. V0^2) at 10.00 mrad: got -0.1316274352 want -0.1316282876 err 8.524e-07 tol 1.0e-05
V_g = 0, V0 = 12 V, 16.47 mrad: R = -0.057202-0.0e+00i; (K-q)/(K+q) = -0.057202; M2 analytic (SM04 dK) = -0.057202
   CHECK PASS  Fresnel limit at 16.47 mrad: got -0.05720175534 want -0.05720175534 err 1.041e-16 tol 1.0e-12
   CHECK PASS  rung-1 analytic (SM04 dK incl. V0^2) at 16.47 mrad: got -0.05720175534 want -0.05720218582 err 4.305e-07 tol 1.0e-05
V_g = 0, V0 = 12 V, 30.00 mrad: R = -0.018682-0.0e+00i; (K-q)/(K+q) = -0.018682; M2 analytic (SM04 dK) = -0.018682
   CHECK PASS  Fresnel limit at 30.00 mrad: got -0.01868215331 want -0.01868215331 err 5.551e-17 tol 1.0e-12
   CHECK PASS  rung-1 analytic (SM04 dK incl. V0^2) at 30.00 mrad: got -0.01868215331 want -0.01868230518 err 1.519e-07 tol 1.0e-05
r = 0, 161 angles over eta in [-4, 4]: max |R| - 1 = +1.57e-13
   CHECK PASS  |R| <= 1 + 1e-12 without absorption 
   CHECK PASS  |R| = 1 inside the exact gap: got 1.574296249e-13 want 0 err 1.574e-13 tol 1.0e-10
   CHECK PASS  |R| < 1 with absorption r = 0.05 (max |R| = 0.5423)
   CHECK PASS  |R| < 1 with absorption r = 0.1 (max |R| = 0.3470)
   CHECK PASS  two-beam closed form = Bloch method in the basis {0, 1}: got 2.185589922e-13 want 0 err 2.186e-13 tol 1.0e-10
   CHECK PASS  Darwin arg R at eta = -1: got 4.178482285e-08 want 0 err 4.178e-08 tol 1.0e-06
   CHECK PASS  Darwin arg R at eta = +0: got 1.570796327 want 1.570796327 err 0.000e+00 tol 1.0e-06
   CHECK PASS  Darwin arg R at eta = +1: got 3.141592612 want 3.141592654 err 4.178e-08 tol 1.0e-06
   CHECK PASS  i int J1(t)/t exp(i eta t) dt = -(eta - sqrt(eta^2-1)), eta = (0.3+0.2j): got (-0.2385632261+0.776613781j) want (-0.2385632262+0.776613781j) err 7.892e-13 tol 1.0e-06
   CHECK PASS  i int J1(t)/t exp(i eta t) dt = -(eta - sqrt(eta^2-1)), eta = (-0.7+0.5j): got (0.330373629+0.4469021355j) want (0.330373629+0.4469021355j) err 1.241e-16 tol 1.0e-06
   CHECK PASS  i int J1(t)/t exp(i eta t) dt = -(eta - sqrt(eta^2-1)), eta = (1.4+0.1j): got (-0.415011686+0.04213366611j) want (-0.4150116859+0.04213366594j) err 2.036e-10 tol 1.0e-06

====================================================================================================
6. Rocking curves of (0,0,8): exact (single harmonic) vs two-beam, r = 0, 0.05, 0.1
====================================================================================================
theta_ext in mrad; dth = theta - theta_c(two-beam centre) in urad; eta = two-beam deviation parameter (r = 0 definition); phases in rad; R referenced at x_s (cosine maximum at x_s);
ex = exact (single harmonic V_008); 2b = two-beam matched closed form; DR = Darwin composed with the Fresnel step; TT = Darwin/Takagi-Taupin; full = exact, full layer potential (V_004 ... V_048, g = 4/a)

--- r = 0.0 ---
  eta     theta     dth |   |R|ex  arg ex |   |R|2b  arg 2b |   |R|DR  arg DR |   |R|TT  arg TT | |R|full arg full
 -3.0  15.56435  -570.4 | 0.10099 -0.0000 | 0.10318 +0.0000 | 0.10091 +0.0000 | 0.17157 +0.0000 | 0.04624  +0.0000
 -2.0  15.75678  -378.0 | 0.20165 +0.0000 | 0.20353 +0.0000 | 0.20135 +0.0000 | 0.26795 +0.0000 | 0.12795  +0.0000
 -1.5  15.85213  -282.6 | 0.32159 +0.0000 | 0.32286 +0.0000 | 0.32084 +0.0000 | 0.38197 +0.0000 | 0.21648  -0.0000
 -1.0  15.94690  -187.9 | 1.00000 +0.0762 | 1.00000 +0.0000 | 1.00000 +0.0000 | 1.00000 +0.0000 | 0.45149  -0.0000
 -0.9  15.96579  -169.0 | 1.00000 +0.5207 | 1.00000 +0.5127 | 1.00000 +0.5149 | 1.00000 +0.4510 | 0.57827  -0.0000
 -0.5  16.04111   -93.7 | 1.00000 +1.1722 | 1.00000 +1.1653 | 1.00000 +1.1694 | 1.00000 +1.0472 | 1.00000  +1.0152
  0.0  16.13477     0.0 | 1.00000 +1.7080 | 1.00000 +1.7013 | 1.00000 +1.7057 | 1.00000 +1.5708 | 1.00000  +1.6701
  0.5  16.22789    93.1 | 1.00000 +2.2088 | 1.00000 +2.2028 | 1.00000 +2.2064 | 1.00000 +2.0944 | 1.00000  +2.2188
  0.9  16.30201   167.2 | 1.00000 +2.7497 | 1.00000 +2.7434 | 1.00000 +2.7451 | 1.00000 +2.6906 | 1.00000  +2.8040
  1.0  16.32049   185.7 | 0.94342 +3.1416 | 1.00000 +3.1416 | 1.00000 +3.1416 | 1.00000 +3.1416 | 0.81349  +3.1416
  1.5  16.41255   277.8 | 0.43592 +3.1416 | 0.43484 +3.1416 | 0.43659 +3.1416 | 0.38197 +3.1416 | 0.43116  +3.1416
  2.0  16.50411   369.3 | 0.32690 -3.1416 | 0.32526 +3.1416 | 0.32718 +3.1416 | 0.26795 +3.1416 | 0.32986  +3.1416
  3.0  16.68571   550.9 | 0.23263 -3.1416 | 0.23071 +3.1416 | 0.23272 +3.1416 | 0.17157 +3.1416 | 0.24203  +3.1416

--- r = 0.05 ---
  eta     theta     dth |   |R|ex  arg ex |   |R|2b  arg 2b |   |R|DR  arg DR |   |R|TT  arg TT | |R|full arg full
 -3.0  15.56435  -570.4 | 0.09949 +0.4651 | 0.10150 +0.4552 | 0.09942 +0.4646 | 0.16668 +0.2847 | 0.05064  +0.7471
 -2.0  15.75678  -378.0 | 0.18661 +0.5665 | 0.18830 +0.5595 | 0.18639 +0.5658 | 0.24729 +0.4172 | 0.12382  +0.6696
 -1.5  15.85213  -282.6 | 0.26631 +0.7042 | 0.26761 +0.6974 | 0.26594 +0.7030 | 0.31952 +0.5583 | 0.19205  +0.7495
 -1.0  15.94690  -187.9 | 0.37881 +0.9693 | 0.37955 +0.9621 | 0.37837 +0.9675 | 0.41768 +0.8153 | 0.29869  +0.9566
 -0.9  15.96579  -169.0 | 0.40233 +1.0399 | 0.40296 +1.0326 | 0.40191 +1.0380 | 0.43741 +0.8832 | 0.32419  +1.0191
 -0.5  16.04111   -93.7 | 0.48204 +1.3547 | 0.48228 +1.3471 | 0.48180 +1.3526 | 0.50069 +1.1891 | 0.42274  +1.3284
  0.0  16.13477     0.0 | 0.53532 +1.7627 | 0.53512 +1.7555 | 0.53530 +1.7608 | 0.53382 +1.5986 | 0.50143  +1.7621
  0.5  16.22789    93.1 | 0.53497 +2.1636 | 0.53441 +2.1573 | 0.53518 +2.1618 | 0.51431 +2.0185 | 0.51645  +2.1846
  0.9  16.30201   167.2 | 0.48919 +2.4676 | 0.48838 +2.4625 | 0.48960 +2.4661 | 0.45363 +2.3471 | 0.47778  +2.4954
  1.0  16.32049   185.7 | 0.47167 +2.5353 | 0.47078 +2.5305 | 0.47211 +2.5339 | 0.43270 +2.4211 | 0.46179  +2.5632
  1.5  16.41255   277.8 | 0.37711 +2.7829 | 0.37577 +2.7796 | 0.37748 +2.7821 | 0.32581 +2.6932 | 0.37486  +2.8066
  2.0  16.50411   369.3 | 0.30632 +2.9101 | 0.30466 +2.9077 | 0.30653 +2.9098 | 0.24951 +2.8336 | 0.30976  +2.9300
  3.0  16.68571   550.9 | 0.22725 +3.0251 | 0.22533 +3.0234 | 0.22732 +3.0249 | 0.16711 +2.9619 | 0.23673  +3.0401

--- r = 0.1 ---
  eta     theta     dth |   |R|ex  arg ex |   |R|2b  arg 2b |   |R|DR  arg DR |   |R|TT  arg TT | |R|full arg full
 -3.0  15.56435  -570.4 | 0.09611 +0.8888 | 0.09765 +0.8708 | 0.09605 +0.8880 | 0.15464 +0.5413 | 0.06020  +1.3169
 -2.0  15.75678  -378.0 | 0.16092 +1.0177 | 0.16213 +1.0051 | 0.16079 +1.0168 | 0.20975 +0.7343 | 0.11709  +1.2171
 -1.5  15.85213  -282.6 | 0.20675 +1.1544 | 0.20766 +1.1432 | 0.20660 +1.1532 | 0.24692 +0.8900 | 0.16113  +1.2881
 -1.0  15.94690  -187.9 | 0.25860 +1.3508 | 0.25910 +1.3406 | 0.25844 +1.3494 | 0.28641 +1.0998 | 0.21521  +1.4391
 -0.9  15.96579  -169.0 | 0.26890 +1.3970 | 0.26932 +1.3869 | 0.26875 +1.3955 | 0.29381 +1.1482 | 0.22665  +1.4786
 -0.5  16.04111   -93.7 | 0.30648 +1.5991 | 0.30654 +1.5896 | 0.30638 +1.5976 | 0.31865 +1.3597 | 0.27093  +1.6624
  0.0  16.13477     0.0 | 0.33836 +1.8755 | 0.33797 +1.8669 | 0.33835 +1.8740 | 0.33335 +1.6506 | 0.31374  +1.9299
  0.5  16.22789    93.1 | 0.34655 +2.1544 | 0.34575 +2.1468 | 0.34664 +2.1530 | 0.32486 +1.9488 | 0.33222  +2.2061
  0.9  16.30201   167.2 | 0.33531 +2.3614 | 0.33422 +2.3547 | 0.33546 +2.3602 | 0.30195 +2.1733 | 0.32766  +2.4108
  1.0  16.32049   185.7 | 0.33045 +2.4089 | 0.32930 +2.4025 | 0.33060 +2.4078 | 0.29453 +2.2252 | 0.32425  +2.4576
  1.5  16.41255   277.8 | 0.29920 +2.6125 | 0.29776 +2.6073 | 0.29936 +2.6117 | 0.25308 +2.4492 | 0.29912  +2.6563
  2.0  16.50411   369.3 | 0.26579 +2.7585 | 0.26413 +2.7541 | 0.26591 +2.7580 | 0.21342 +2.6113 | 0.27016  +2.7970
  3.0  16.68571   550.9 | 0.21364 +2.9306 | 0.21175 +2.9274 | 0.21370 +2.9304 | 0.15581 +2.8057 | 0.22338  +2.9601

====================================================================================================
7. Plateau summary: centre, width, phase sweep (exact vs two-beam)
====================================================================================================
r = 0.00 exact            : max|R| = 1.00000 at 15.95351 mrad; |R|^2 FWHM  395.94 urad centred 16.13636 mrad; arg R at eta=0: +1.7080; arg R at FWHM edges -0.0000 -> +3.1416 (sweep +3.1416)
r = 0.00 two-beam matched : max|R| = 1.00000 at 15.95823 mrad; |R|^2 FWHM  395.94 urad centred 16.13636 mrad; arg R at eta=0: +1.7013; arg R at FWHM edges +0.0000 -> +3.1416 (sweep +3.1416)
r = 0.00 Darwin+Fresnel   : max|R| = 1.00000 at 16.05519 mrad; |R|^2 FWHM  395.94 urad centred 16.13636 mrad; arg R at eta=0: +1.7057; arg R at FWHM edges +0.0000 -> +3.1416 (sweep +3.1416)
r = 0.00 Darwin/TT        : max|R| = 1.00000 at 15.94784 mrad; |R|^2 FWHM  396.01 urad centred 16.13356 mrad; arg R at eta=0: +1.5708; arg R at FWHM edges +0.0000 -> +3.1416 (sweep +3.1416)
      two-beam matched  vs exact, r = 0.00, |eta|<=0.9: max |dR| = 7.93e-03, max |arg(R/R_ex)| = 7.93e-03 rad
      two-beam matched  vs exact, r = 0.00, |eta|<=3  : max |dR| = 7.62e-02, max |arg(R/R_ex)| = 7.62e-02 rad
      Darwin+Fresnel    vs exact, r = 0.00, |eta|<=0.9: max |dR| = 5.73e-03, max |arg(R/R_ex)| = 5.73e-03 rad
      Darwin+Fresnel    vs exact, r = 0.00, |eta|<=3  : max |dR| = 7.62e-02, max |arg(R/R_ex)| = 7.62e-02 rad
      Darwin/TT         vs exact, r = 0.00, |eta|<=0.9: max |dR| = 1.38e-01, max |arg(R/R_ex)| = 1.38e-01 rad
      Darwin/TT         vs exact, r = 0.00, |eta|<=3  : max |dR| = 1.38e-01, max |arg(R/R_ex)| = 1.38e-01 rad
r = 0.05 exact            : max|R| = 0.54226 at 16.18140 mrad; |R|^2 FWHM  454.53 urad centred 16.17794 mrad; arg R at eta=0: +1.7627; arg R at FWHM edges +0.9830 -> +2.7685 (sweep +1.7855)
r = 0.05 two-beam matched : max|R| = 0.54186 at 16.18140 mrad; |R|^2 FWHM  453.61 urad centred 16.17748 mrad; arg R at eta=0: +1.7555; arg R at FWHM edges +0.9758 -> +2.7633 (sweep +1.7875)
r = 0.05 Darwin+Fresnel   : max|R| = 0.54234 at 16.18233 mrad; |R|^2 FWHM  454.50 urad centred 16.17887 mrad; arg R at eta=0: +1.7608; arg R at FWHM edges +0.9847 -> +2.7696 (sweep +1.7849)
r = 0.05 Darwin/TT        : max|R| = 0.53439 at 16.14878 mrad; |R|^2 FWHM  454.71 urad centred 16.13831 mrad; arg R at eta=0: +1.5986; arg R at FWHM edges +0.7008 -> +2.5756 (sweep +1.8749)
      two-beam matched  vs exact, r = 0.05, |eta|<=0.9: max |dR| = 3.86e-03, max |arg(R/R_ex)| = 7.52e-03 rad
      two-beam matched  vs exact, r = 0.05, |eta|<=3  : max |dR| = 3.86e-03, max |arg(R/R_ex)| = 9.87e-03 rad
      Darwin+Fresnel    vs exact, r = 0.05, |eta|<=0.9: max |dR| = 1.04e-03, max |arg(R/R_ex)| = 2.01e-03 rad
      Darwin+Fresnel    vs exact, r = 0.05, |eta|<=3  : max |dR| = 1.04e-03, max |arg(R/R_ex)| = 2.01e-03 rad
      Darwin/TT         vs exact, r = 0.05, |eta|<=0.9: max |dR| = 8.78e-02, max |arg(R/R_ex)| = 1.67e-01 rad
      Darwin/TT         vs exact, r = 0.05, |eta|<=3  : max |dR| = 8.78e-02, max |arg(R/R_ex)| = 1.80e-01 rad
r = 0.10 exact            : max|R| = 0.34697 at 16.21117 mrad; |R|^2 FWHM  642.82 urad centred 16.24467 mrad; arg R at eta=0: +1.8755; arg R at FWHM edges +1.2962 -> +2.8311 (sweep +1.5350)
r = 0.10 two-beam matched : max|R| = 0.34624 at 16.20931 mrad; |R|^2 FWHM  641.07 urad centred 16.24190 mrad; arg R at eta=0: +1.8669; arg R at FWHM edges +1.2815 -> +2.8234 (sweep +1.5419)
r = 0.10 Darwin+Fresnel   : max|R| = 0.34704 at 16.21117 mrad; |R|^2 FWHM  641.87 urad centred 16.24514 mrad; arg R at eta=0: +1.8740; arg R at FWHM edges +1.2970 -> +2.8307 (sweep +1.5337)
r = 0.10 Darwin/TT        : max|R| = 0.33361 at 16.14878 mrad; |R|^2 FWHM  624.66 urad centred 16.13782 mrad; arg R at eta=0: +1.6506; arg R at FWHM edges +0.8412 -> +2.5226 (sweep +1.6814)
      two-beam matched  vs exact, r = 0.10, |eta|<=0.9: max |dR| = 2.94e-03, max |arg(R/R_ex)| = 1.01e-02 rad
      two-beam matched  vs exact, r = 0.10, |eta|<=3  : max |dR| = 2.94e-03, max |arg(R/R_ex)| = 1.80e-02 rad
      Darwin+Fresnel    vs exact, r = 0.10, |eta|<=0.9: max |dR| = 4.96e-04, max |arg(R/R_ex)| = 1.49e-03 rad
      Darwin+Fresnel    vs exact, r = 0.10, |eta|<=3  : max |dR| = 4.96e-04, max |arg(R/R_ex)| = 1.49e-03 rad
      Darwin/TT         vs exact, r = 0.10, |eta|<=0.9: max |dR| = 7.60e-02, max |arg(R/R_ex)| = 2.49e-01 rad
      Darwin/TT         vs exact, r = 0.10, |eta|<=3  : max |dR| = 7.60e-02, max |arg(R/R_ex)| = 3.48e-01 rad
r = 0 exact: arg R at the band edges +0.00000 (low) and +3.14159 (high), at the midpoint +1.70007; sweep across the gap 3.14158 rad (Darwin: pi = 3.14159)
Fresnel step amplitude at the (0,0,8) centre r_F = (K - q)/(K + q) = -0.06755; refraction phase at the centre 2 atan(|r_F|) = 0.13489 rad
   CHECK PASS  two-beam matched: V_g = 0 gives the Fresnel step: got -0.02151959822 want -0.02151959822 err 2.429e-17 tol 1.0e-12
   CHECK PASS  Darwin+Fresnel: V_g = 0 gives the Fresnel step: got -0.02151959822 want -0.02151959822 err 0.000e+00 tol 1.0e-12
truncation plane offset t = 0.00000 A (cosine maximum t below x_s): R(centre) = 1.00000 exp(+1.70798 i); two-beam phase factor exp(i G t) adds +0.00000 rad
truncation plane offset t = 0.16972 A (cosine maximum t below x_s): R(centre) = 1.00000 exp(-3.13195 i); two-beam phase factor exp(i G t) adds +1.57080 rad
truncation plane offset t = 0.33943 A (cosine maximum t below x_s): R(centre) = 1.00000 exp(-1.70360 i); two-beam phase factor exp(i G t) adds -3.14159 rad
   CHECK PASS  band edges independent of the truncation plane (bulk property): got 5.551115123e-17 want 0 err 5.551e-17 tol 1.0e-12
full layer potential with the truncation plane a/8 above the top atomic plane (t = a/8): band edges 15.98286 to 16.31535 mrad (bulk property, unchanged); R at the band midpoint: t = 0 +1.7553 rad, t = a/8 +1.6453 rad

====================================================================================================
8. Paraxial / propagator models (stationary R(K), laterally uniform potential)
====================================================================================================
eta = -0.9: one-way ('exact' propagator) effective dV0 = -2.0534 mV; |R_oneway| - |R| = +2.85e-14, arg(R_oneway/R) = -5.118e-03 rad
eta = +0.0: one-way ('exact' propagator) effective dV0 = -2.0911 mV; |R_oneway| - |R| = +2.63e-14, arg(R_oneway/R) = -2.018e-03 rad
eta = +0.9: one-way ('exact' propagator) effective dV0 = -2.1289 mV; |R_oneway| - |R| = -1.45e-13, arg(R_oneway/R) = -4.207e-03 rad
centre shift for the one-way scheme: d(K^2) = 7.637e-04 rad^2/A^2, d(theta) = +0.3771 urad = +1.01e-03 of the plateau width, d(eta) = +2.02e-03
rung 1, V0 = 12 V, 10.00 mrad: predicted |r_exact-prop|/|r_Fresnel| - 1 = -0.0052 %; M2 section 2 measured (dx 0.025, dz 1): -0.005 % (exact -0.020 %, Fresnel -0.015 %)
rung 1, V0 = 12 V, 16.47 mrad: predicted |r_exact-prop|/|r_Fresnel| - 1 = -0.0137 %; M2 section 2 measured (dx 0.025, dz 1): -0.013 % (exact -0.404 %, Fresnel -0.391 %)
rung 1, V0 = 12 V, 30.00 mrad: predicted |r_exact-prop|/|r_Fresnel| - 1 = -0.0451 %; M2 section 2 measured (dx 0.025, dz 1): -0.045 % (exact -1.254 %, Fresnel -1.209 %)
(e V)^2 term at eta = 0: arg(R_KG/R) = +1.33e-04 rad, |R_KG|-|R| = +3.7e-14; U_0 changes by 5.019e-05 rad^2/A^2 (relative 9.89e-06)

====================================================================================================
9. Build-up along the surface after a leading edge (two-beam closed form, sharp edge)
====================================================================================================
|A(Z) - R_TT| (and |arg(A/R_TT)| in rad) versus Z downstream of first contact
r=0.00 eta=-0.5: 6.7e-01(3.4e-01)  3.6e-01(1.6e-01)  8.0e-02(7.5e-02)  3.5e-02(1.3e-02)  1.2e-02(6.2e-03)  4.8e-03(4.3e-03)
r=0.00 eta=+0.0: 6.3e-01(4.3e-36)  3.1e-01(1.8e-34)  5.1e-02(1.5e-18)  1.9e-02(4.0e-18)  3.9e-03(3.1e-18)  1.6e-03(1.8e-18)
r=0.00 eta=+0.5: 6.7e-01(3.4e-01)  3.6e-01(1.6e-01)  8.0e-02(7.5e-02)  3.5e-02(1.3e-02)  1.2e-02(6.2e-03)  4.8e-03(4.3e-03)
r=0.05 eta=-0.5: 2.3e-01(2.6e-01)  9.0e-02(1.3e-01)  1.6e-03(2.5e-03)  1.4e-04(2.3e-05)  2.4e-06(1.5e-06)  6.5e-10(3.3e-11)
r=0.05 eta=+0.0: 2.4e-01(2.0e-02)  9.1e-02(1.5e-02)  2.4e-03(4.4e-03)  2.4e-04(4.4e-04)  3.4e-06(5.6e-06)  8.5e-10(1.1e-09)
r=0.05 eta=+0.5: 2.4e-01(2.3e-01)  9.5e-02(1.1e-01)  5.8e-03(4.9e-04)  4.7e-04(9.1e-04)  5.3e-06(1.0e-05)  1.2e-09(2.3e-09)
r=0.10 eta=-0.5: 9.5e-02(1.5e-01)  2.4e-02(5.6e-02)  4.7e-04(1.2e-03)  5.7e-06(1.2e-05)  1.4e-09(2.6e-09)  6.9e-15(6.7e-15)
r=0.10 eta=+0.0: 9.9e-02(1.6e-02)  2.5e-02(9.7e-03)  5.7e-04(1.5e-03)  6.9e-06(1.8e-05)  1.7e-09(4.2e-09)  3.9e-14(8.7e-15)
r=0.10 eta=+0.5: 9.8e-02(1.3e-01)  2.5e-02(4.4e-02)  7.3e-04(7.8e-04)  8.4e-06(2.5e-05)  2.0e-09(5.8e-09)  7.2e-15(7.0e-15)

build-up lengths (two-beam, sharp edge): smallest Z beyond which |A - R| <= tol (or |arg(A/R)| <= tol)
r = 0.00 eta = -0.5 |R_TT| = 1.0000: Z(|dA|<=1e-2) =     26900 A, Z(|dA|<=1e-3) =    134660 A, Z(|d arg|<=1e-2 rad) =     23220 A
r = 0.00 eta = +0.0 |R_TT| = 1.0000: Z(|dA|<=1e-2) =     22580 A, Z(|dA|<=1e-3) =    113560 A, Z(|d arg|<=1e-2 rad) =         0 A
r = 0.00 eta = +0.5 |R_TT| = 1.0000: Z(|dA|<=1e-2) =     26900 A, Z(|dA|<=1e-3) =    134660 A, Z(|d arg|<=1e-2 rad) =     23220 A
r = 0.00 eta = +0.9 |R_TT| = 1.0000: Z(|dA|<=1e-2) =     68800 A, Z(|dA|<=1e-3) =    342680 A, Z(|d arg|<=1e-2 rad) =     65220 A
r = 0.05 eta = -0.5 |R_TT| = 0.5007: Z(|dA|<=1e-2) =      3500 A, Z(|dA|<=1e-3) =      7100 A, Z(|d arg|<=1e-2 rad) =      3720 A
r = 0.05 eta = +0.0 |R_TT| = 0.5338: Z(|dA|<=1e-2) =      3480 A, Z(|dA|<=1e-3) =      7120 A, Z(|d arg|<=1e-2 rad) =      2900 A
r = 0.05 eta = +0.5 |R_TT| = 0.5143: Z(|dA|<=1e-2) =      3660 A, Z(|dA|<=1e-3) =      7340 A, Z(|d arg|<=1e-2 rad) =      3560 A
r = 0.05 eta = +0.9 |R_TT| = 0.4536: Z(|dA|<=1e-2) =      3860 A, Z(|dA|<=1e-3) =      7540 A, Z(|d arg|<=1e-2 rad) =      4480 A
r = 0.10 eta = -0.5 |R_TT| = 0.3186: Z(|dA|<=1e-2) =      2560 A, Z(|dA|<=1e-3) =      3720 A, Z(|d arg|<=1e-2 rad) =      3180 A
r = 0.10 eta = +0.0 |R_TT| = 0.3333: Z(|dA|<=1e-2) =      2580 A, Z(|dA|<=1e-3) =      3760 A, Z(|d arg|<=1e-2 rad) =      1960 A
r = 0.10 eta = +0.5 |R_TT| = 0.3249: Z(|dA|<=1e-2) =      2600 A, Z(|dA|<=1e-3) =      3860 A, Z(|d arg|<=1e-2 rad) =      3020 A
r = 0.10 eta = +0.9 |R_TT| = 0.3020: Z(|dA|<=1e-2) =      2600 A, Z(|dA|<=1e-3) =      3920 A, Z(|d arg|<=1e-2 rad) =      3320 A
asymptote (r = 0, sharp edge): |A - R| ~ sqrt(2/pi) (kc Z)^(-3/2) / (1 - eta^2), kc = 7.5489e-04 rad/A -> at eta = 0: Z(1e-2) ~ 24551 A, Z(1e-3) ~ 113957 A
r = 0.05: slowest decay exp(-Z/Z_a), Z_a = 1/(r sigma (V0 - V_g)) = 2133 A; fastest 1/(r sigma (V0 + V_g)) = 1837 A; mean absorption 1/(r sigma V0) = 1974 A
r = 0.1: slowest decay exp(-Z/Z_a), Z_a = 1/(r sigma (V0 - V_g)) = 1066 A; fastest 1/(r sigma (V0 + V_g)) = 918 A; mean absorption 1/(r sigma V0) = 987 A
   CHECK PASS  build-up A(Z -> inf) = R_TT, r = 0.05: got 4.851677226e-14 want 0 err 4.852e-14 tol 1.0e-08
   CHECK PASS  build-up A(Z -> inf) = R_TT, r = 0.1: got 3.908040488e-14 want 0 err 3.908e-14 tol 1.0e-08
   CHECK PASS  build-up A(4e5 A) -> R_TT, r = 0 (power law): got 0.0001384851129 want 0 err 1.385e-04 tol 2.0e-04

====================================================================================================
10. Exact step response (smooth edge, w = 400 A) vs two-beam, from R(E) by damped FFT
====================================================================================================
r = 0.0: FFT two-beam vs convolved closed form (5000 < Z < 50000 A): max |dA| = 6.99e-07
   CHECK PASS  damped-FFT machinery vs closed form, r = 0.0: got 6.988958663e-07 want 0 err 6.989e-07 tol 2.0e-03
   Z =    1953 A: |A_ex - R_ex| = 3.27e-01  |A_TT - R_TT| = 3.30e-01  |arg(A_ex/R_ex)| = 9.59e-03
   Z =    4004 A: |A_ex - R_ex| = 5.22e-02  |A_TT - R_TT| = 4.74e-02  |arg(A_ex/R_ex)| = 1.97e-02
   Z =    8008 A: |A_ex - R_ex| = 1.97e-02  |A_TT - R_TT| = 1.82e-02  |arg(A_ex/R_ex)| = 8.22e-03
   Z =   16016 A: |A_ex - R_ex| = 4.66e-03  |A_TT - R_TT| = 3.89e-03  |arg(A_ex/R_ex)| = 2.78e-03
   Z =   32031 A: |A_ex - R_ex| = 1.65e-03  |A_TT - R_TT| = 1.40e-03  |arg(A_ex/R_ex)| = 7.48e-04
   CHECK PASS  exact step response -> R_exact at large Z, r = 0.0: got 0.002376258686 want 0 err 2.376e-03 tol 3.0e-03
r = 0.1: FFT two-beam vs convolved closed form (5000 < Z < 50000 A): max |dA| = 8.98e-09
   CHECK PASS  damped-FFT machinery vs closed form, r = 0.1: got 8.975805214e-09 want 0 err 8.976e-09 tol 2.0e-03
   Z =    1953 A: |A_ex - R_ex| = 2.80e-02  |A_TT - R_TT| = 2.87e-02  |arg(A_ex/R_ex)| = 2.21e-02
   Z =    4004 A: |A_ex - R_ex| = 5.20e-04  |A_TT - R_TT| = 6.65e-04  |arg(A_ex/R_ex)| = 1.13e-03
   Z =    8008 A: |A_ex - R_ex| = 6.06e-06  |A_TT - R_TT| = 7.30e-06  |arg(A_ex/R_ex)| = 1.61e-05
   Z =   16016 A: |A_ex - R_ex| = 1.47e-09  |A_TT - R_TT| = 1.69e-09  |arg(A_ex/R_ex)| = 3.92e-09
   Z =   32031 A: |A_ex - R_ex| = 4.95e-12  |A_TT - R_TT| = 4.63e-12  |arg(A_ex/R_ex)| = 4.03e-13
   CHECK PASS  exact step response -> R_exact at large Z, r = 0.1: got 1.711785954e-09 want 0 err 1.712e-09 tol 1.0e-06

====================================================================================================
11. Engine geometry: finite clean depth above the numerical absorber (sin^2, 100 V, 15 A)
====================================================================================================
r = 0.00 D =    60 A: |R_cell - R_inf| at eta -3.0:1.6e-01 -1.5:3.8e-01 -1.0:3.4e-01 -0.9:1.1e-01 +0.0:1.1e-02 +0.9:9.0e-02 +1.0:3.0e-01 +1.5:3.6e-01 +3.0:1.6e-01
r = 0.00 D =   100 A: |R_cell - R_inf| at eta -3.0:1.6e-01 -1.5:3.0e-01 -1.0:2.0e-01 -0.9:2.4e-02 +0.0:4.4e-04 +0.9:2.1e-02 +1.0:1.9e-01 +1.5:2.6e-01 +3.0:1.6e-01
r = 0.00 D =   150 A: |R_cell - R_inf| at eta -3.0:1.6e-01 -1.5:3.4e-01 -1.0:1.2e-01 -0.9:4.0e-03 +0.0:7.4e-06 +0.9:3.6e-03 +1.0:1.3e-01 +1.5:3.1e-01 +3.0:1.5e-01
r = 0.00 D =   250 A: |R_cell - R_inf| at eta -3.0:1.6e-01 -1.5:3.2e-01 -1.0:5.1e-02 -0.9:1.1e-04 +0.0:2.1e-09 +0.9:1.1e-04 +1.0:8.6e-02 +1.5:2.8e-01 +3.0:1.6e-01
r = 0.05 D =    60 A: |R_cell - R_inf| at eta -3.0:3.5e-03 -1.5:3.7e-03 -1.0:2.6e-03 -0.9:2.4e-03 +0.0:1.4e-03 +0.9:3.0e-03 +1.0:3.4e-03 +1.5:5.0e-03 +3.0:4.8e-03
r = 0.05 D =   100 A: |R_cell - R_inf| at eta -3.0:3.0e-04 -1.5:2.2e-04 -1.0:1.0e-04 -0.9:8.2e-05 +0.0:2.7e-05 +0.9:1.2e-04 +1.0:1.6e-04 +1.5:3.8e-04 +3.0:5.2e-04
r = 0.05 D =   150 A: |R_cell - R_inf| at eta -3.0:1.4e-05 -1.5:6.4e-06 -1.0:1.7e-06 -0.9:1.2e-06 +0.0:2.0e-07 +0.9:2.3e-06 +1.0:3.5e-06 +1.5:1.5e-05 +3.0:3.3e-05
r = 0.05 D =   250 A: |R_cell - R_inf| at eta -3.0:3.3e-08 -1.5:5.5e-09 -1.0:5.1e-10 -0.9:2.6e-10 +0.0:4.2e-12 +0.9:8.1e-10 +1.0:1.7e-09 +1.5:2.4e-08 +3.0:1.3e-07
r = 0.10 D =    60 A: |R_cell - R_inf| at eta -3.0:7.7e-05 -1.5:8.0e-05 -1.0:7.2e-05 -0.9:7.1e-05 +0.0:6.8e-05 +0.9:9.8e-05 +1.0:1.0e-04 +1.5:1.3e-04 +3.0:1.4e-04
r = 0.10 D =   100 A: |R_cell - R_inf| at eta -3.0:6.3e-07 -1.5:4.7e-07 -1.0:3.6e-07 -0.9:3.4e-07 +0.0:2.9e-07 +0.9:5.9e-07 +1.0:6.6e-07 +1.5:1.1e-06 +3.0:1.8e-06
r = 0.10 D =   150 A: |R_cell - R_inf| at eta -3.0:1.5e-09 -1.5:7.7e-10 -1.0:4.7e-10 -0.9:4.3e-10 +0.0:3.0e-10 +0.9:9.9e-10 +1.0:1.2e-09 +1.5:2.6e-09 +3.0:7.2e-09
r = 0.10 D =   250 A: |R_cell - R_inf| at eta -3.0:3.4e-12 -1.5:4.9e-12 -1.0:5.2e-12 -0.9:5.6e-12 +0.0:5.0e-12 +0.9:4.0e-12 +1.0:3.8e-12 +1.5:3.1e-12 +3.0:3.2e-12
V_g = 0 (rung-1 geometry), D = 150 A: max |R_cell - R_Fresnel| = 1.2e-04 (absorber reflection)
eta = 1.5, r = 0, D = 150 A: R_cell ODE = -0.420438+0.313894j, transfer matrices (h = 0.004, 0.002 A, Richardson) = -0.420438+0.313894j
   CHECK PASS  finite cell: ODE vs transfer-matrix discretisation: got 1.180081294e-08 want 0 err 1.180e-08 tol 1.0e-06

r = 0: absorber reflection of Bragg-case Bloch waves versus the absorber ramp (D = 150 A)
   ramp    15 A, W0 = 100.0 V: |R_cell - R_inf| at eta -3.0, -1.5, +1.5, +3.0 = 1.6e-01, 3.4e-01, 3.1e-01, 1.5e-01
   ramp   400 A, W0 =  20.0 V: |R_cell - R_inf| at eta -3.0, -1.5, +1.5, +3.0 = 7.1e-04, 1.0e-01, 9.4e-02, 7.1e-04
   ramp   800 A, W0 =  20.0 V: |R_cell - R_inf| at eta -3.0, -1.5, +1.5, +3.0 = 1.7e-04, 2.0e-02, 1.8e-02, 1.7e-04

M2 null-test geometry (tests/forward/null_test_cases.py: clean depth 21 A above a 15 A, 100 V sin^2 absorber for crystal A; crystal B = A plus two layers, clean depth 21 + a/2 A), stationary 1D prediction at theta = 16.1347 mrad (R at each crystal's own surface):
   single (0,0,8)        r = 0.00: |R_inf| = 1.0000; |R_A| = 0.7544, |R_B| = 0.7984; arg(R_B/R_A) = -0.0018 rad, |R_B/R_A| = 1.0582; arg(R_A/R_inf) = +0.0045 rad
   single (0,0,8)        r = 0.05: |R_inf| = 0.5353; |R_A| = 0.4734, |R_B| = 0.4876; arg(R_B/R_A) = -0.0044 rad, |R_B/R_A| = 1.0302; arg(R_A/R_inf) = +0.0201 rad
   single (0,0,8)        r = 0.10: |R_inf| = 0.3383; |R_A| = 0.3249, |R_B| = 0.3291; arg(R_B/R_A) = -0.0032 rad, |R_B/R_A| = 1.0128; arg(R_A/R_inf) = +0.0109 rad
   full layer potential  r = 0.00: |R_inf| = 1.0000; |R_A| = 0.7047, |R_B| = 0.7508; arg(R_B/R_A) = -0.0081 rad, |R_B/R_A| = 1.0655; arg(R_A/R_inf) = +0.0384 rad
   full layer potential  r = 0.05: |R_inf| = 0.5014; |R_A| = 0.4367, |R_B| = 0.4508; arg(R_B/R_A) = -0.0095 rad, |R_B/R_A| = 1.0322; arg(R_A/R_inf) = +0.0479 rad
   full layer potential  r = 0.10: |R_inf| = 0.3137; |R_A| = 0.3010, |R_B| = 0.3049; arg(R_B/R_A) = -0.0060 rad, |R_B/R_A| = 1.0129; arg(R_A/R_inf) = +0.0218 rad
   same pair with deeper clean crystal (full layer potential):
      D =    60 A, r = 0.05: arg(R_B/R_A) = -4.24e-04 rad, |R_B/R_A| - 1 = +7.82e-04
      D =    60 A, r = 0.10: arg(R_B/R_A) = -5.67e-05 rad, |R_B/R_A| - 1 = +6.13e-05
      D =   100 A, r = 0.05: arg(R_B/R_A) = -1.59e-05 rad, |R_B/R_A| - 1 = +1.71e-05
      D =   100 A, r = 0.10: arg(R_B/R_A) = -3.91e-07 rad, |R_B/R_A| - 1 = +2.09e-07
      D =   150 A, r = 0.05: arg(R_B/R_A) = -2.16e-07 rad, |R_B/R_A| - 1 = +1.20e-07
      D =   150 A, r = 0.10: arg(R_B/R_A) = -6.33e-10 rad, |R_B/R_A| - 1 = +4.77e-11

====================================================================================================
12. Independent minimal 1D split step (NOT the engine): paraxial claims and test protocol
====================================================================================================
F         r = 0.10 fresnel dx = 0.02500 A dz = 1.0 A D = 100 A Z_e = 5000 A: nx = 16308, 6612 slices, bins |eta|<=3: 18; vs reference (exact): max |dR| = 4.39e-04 (|eta|<=0.9: 4.39e-04), max |d arg| = 1.82e-03 (|eta|<=0.9: 1.40e-03) rad
X         r = 0.10 exact   dx = 0.02500 A dz = 1.0 A D = 100 A Z_e = 5000 A: nx = 16308, 6612 slices, bins |eta|<=3: 18; vs reference (engine_exact_propagator): max |dR| = 4.47e-04 (|eta|<=0.9: 4.40e-04), max |d arg| = 1.80e-03 (|eta|<=0.9: 1.38e-03) rad
F_dx05    r = 0.10 fresnel dx = 0.05000 A dz = 1.0 A D = 100 A Z_e = 5000 A: nx = 8154, 6612 slices, bins |eta|<=3: 18; vs reference (exact): max |dR| = 1.44e-03 (|eta|<=0.9: 1.44e-03), max |d arg| = 7.38e-03 (|eta|<=0.9: 4.58e-03) rad
F_dx0125  r = 0.10 fresnel dx = 0.01250 A dz = 1.0 A D = 100 A Z_e = 5000 A: nx = 32616, 6612 slices, bins |eta|<=3: 18; vs reference (exact): max |dR| = 2.02e-04 (|eta|<=0.9: 1.92e-04), max |d arg| = 7.45e-04 (|eta|<=0.9: 5.78e-04) rad
F_dz05    r = 0.10 fresnel dx = 0.02500 A dz = 0.5 A D = 100 A Z_e = 5000 A: nx = 16308, 13223 slices, bins |eta|<=3: 18; vs reference (exact): max |dR| = 3.88e-04 (|eta|<=0.9: 3.80e-04), max |d arg| = 1.52e-03 (|eta|<=0.9: 1.21e-03) rad
F_r005    r = 0.05 fresnel dx = 0.02500 A dz = 1.0 A D = 150 A Z_e = 10000 A: nx = 21536, 11612 slices, bins |eta|<=3: 24; vs reference (exact): max |dR| = 2.78e-04 (|eta|<=0.9: 2.78e-04), max |d arg| = 9.17e-04 (|eta|<=0.9: 5.82e-04) rad
bin spacing of run F: 1/extent = 2.453e-03 1/A = 61.5 urad in theta; L = 6612 A
   F bin eta = -1.073: r_ss = 0.25108 exp(+1.31778 i), R_ref = 0.25100 exp(+1.31861 i)
   F bin eta = -0.747: r_ss = 0.28407 exp(+1.47024 i), R_ref = 0.28415 exp(+1.47135 i)
   F bin eta = -0.420: r_ss = 0.31292 exp(+1.64089 i), R_ref = 0.31296 exp(+1.64229 i)
   F bin eta = -0.091: r_ss = 0.33422 exp(+1.82296 i), R_ref = 0.33417 exp(+1.82412 i)
   F bin eta = +0.238: r_ss = 0.34544 exp(+2.00911 i), R_ref = 0.34546 exp(+2.00968 i)
   F bin eta = +0.569: r_ss = 0.34541 exp(+2.19120 i), R_ref = 0.34567 exp(+2.19179 i)
   F bin eta = +0.902: r_ss = 0.33499 exp(+2.36103 i), R_ref = 0.33524 exp(+2.36209 i)
   CHECK PASS  split step (Fresnel, dx 0.025, dz 1) vs Helmholtz reference, |eta| <= 3: got 0.0004390498177 want 0 err 4.390e-04 tol 1.0e-03
   CHECK PASS  split step (exact propagator) vs one-way reference model: got 0.0004473952693 want 0 err 4.474e-04 tol 1.0e-03
   CHECK PASS  F and X runs share their bins 
exact minus Fresnel propagator, r = 0.1, |eta| <= 0.9: measured arg(r_X/r_F) in [-1.18e-03, -1.07e-03] rad, predicted [-1.20e-03, -1.10e-03] rad; max |measured - predicted| = 4.7e-05
   CHECK PASS  propagator difference measured vs one-way prediction (|eta| <= 0.9): got 4.673035566e-05 want 0 err 4.673e-05 tol 2.0e-04
dx convergence (max |dR|, |eta| <= 3): 0.05 A 1.44e-03, 0.025 A 4.39e-04, 0.0125 A 2.02e-04; observed orders 1.71, 1.12
   CHECK PASS  dx convergence order >= 1.5 between 0.05 and 0.025 A 
dz 0.5 A (dx 0.025): max |dR| = 3.88e-04
r = 0.05 (D = 150 A, Z_e = 10000 A): max |dR| = 2.78e-04
r = 0 (D = 250 A, Z_e = 30000 A): nx = 38444, 31612 slices; whole-box read-out and vacuum-only read-out (window from x_s + 60 A, full from x_s + 100 A)
   eta = -2.924: whole box |dR| = 1.16e-01, d arg = +1.48e+00 rad; vacuum-only |dR| = 2.31e-03, d arg = +2.08e-02 rad
   eta = -2.789: whole box |dR| = 1.10e-01, d arg = -3.05e-01 rad; vacuum-only |dR| = 2.31e-03, d arg = -1.66e-02 rad
   eta = -2.654: whole box |dR| = 1.03e-01, d arg = +9.47e-01 rad; vacuum-only |dR| = 2.92e-03, d arg = +6.29e-03 rad
   eta = -2.518: whole box |dR| = 9.72e-02, d arg = -3.48e-01 rad; vacuum-only |dR| = 2.63e-03, d arg = +4.28e-03 rad
   eta = -2.383: whole box |dR| = 9.05e-02, d arg = +6.39e-01 rad; vacuum-only |dR| = 3.44e-03, d arg = -1.41e-02 rad
   eta = -2.247: whole box |dR| = 8.42e-02, d arg = -3.37e-01 rad; vacuum-only |dR| = 3.46e-03, d arg = +2.02e-02 rad
   eta = -2.111: whole box |dR| = 7.75e-02, d arg = +4.32e-01 rad; vacuum-only |dR| = 4.03e-03, d arg = -2.17e-02 rad
   eta = -1.974: whole box |dR| = 7.18e-02, d arg = -2.86e-01 rad; vacuum-only |dR| = 4.79e-03, d arg = +1.69e-02 rad
   eta = -1.838: whole box |dR| = 6.58e-02, d arg = +2.89e-01 rad; vacuum-only |dR| = 5.22e-03, d arg = -9.33e-03 rad
   eta = -1.701: whole box |dR| = 6.05e-02, d arg = -2.13e-01 rad; vacuum-only |dR| = 6.86e-03, d arg = -2.22e-03 rad
   eta = -1.564: whole box |dR| = 5.56e-02, d arg = +1.86e-01 rad; vacuum-only |dR| = 8.04e-03, d arg = +1.45e-02 rad
   eta = -1.426: whole box |dR| = 5.22e-02, d arg = -1.46e-01 rad; vacuum-only |dR| = 1.12e-02, d arg = -2.58e-02 rad
   eta = -1.289: whole box |dR| = 5.04e-02, d arg = +1.19e-01 rad; vacuum-only |dR| = 1.61e-02, d arg = +3.79e-02 rad
   eta = -1.151: whole box |dR| = 5.58e-02, d arg = -1.04e-01 rad; vacuum-only |dR| = 2.90e-02, d arg = -5.40e-02 rad
   eta = -1.013: whole box |dR| = 1.35e-01, d arg = +1.60e-01 rad; vacuum-only |dR| = 1.15e-01, d arg = +1.37e-01 rad
   eta = -0.875: whole box |dR| = 4.49e-02, d arg = -3.97e-02 rad; vacuum-only |dR| = 3.61e-02, d arg = -2.62e-02 rad
   eta = -0.737: whole box |dR| = 3.09e-02, d arg = +3.08e-02 rad; vacuum-only |dR| = 1.97e-02, d arg = +1.92e-02 rad
   eta = -0.598: whole box |dR| = 2.71e-02, d arg = -2.70e-02 rad; vacuum-only |dR| = 1.51e-02, d arg = -1.45e-02 rad
   eta = -0.459: whole box |dR| = 2.31e-02, d arg = +2.24e-02 rad; vacuum-only |dR| = 1.12e-02, d arg = +6.93e-03 rad
   eta = -0.320: whole box |dR| = 2.25e-02, d arg = -2.20e-02 rad; vacuum-only |dR| = 1.02e-02, d arg = -2.58e-03 rad
   eta = -0.181: whole box |dR| = 1.96e-02, d arg = +1.89e-02 rad; vacuum-only |dR| = 9.34e-03, d arg = -3.62e-03 rad
   eta = -0.041: whole box |dR| = 1.98e-02, d arg = -1.95e-02 rad; vacuum-only |dR| = 8.19e-03, d arg = +5.83e-03 rad
   eta = +0.099: whole box |dR| = 1.82e-02, d arg = +1.80e-02 rad; vacuum-only |dR| = 9.21e-03, d arg = -8.99e-03 rad
   eta = +0.239: whole box |dR| = 1.99e-02, d arg = -1.99e-02 rad; vacuum-only |dR| = 8.27e-03, d arg = +7.90e-03 rad
   eta = +0.379: whole box |dR| = 1.98e-02, d arg = +1.97e-02 rad; vacuum-only |dR| = 1.01e-02, d arg = -7.57e-03 rad
   eta = +0.519: whole box |dR| = 2.30e-02, d arg = -2.25e-02 rad; vacuum-only |dR| = 1.09e-02, d arg = +2.88e-03 rad
   eta = +0.660: whole box |dR| = 2.65e-02, d arg = +2.57e-02 rad; vacuum-only |dR| = 1.40e-02, d arg = +1.97e-03 rad
   eta = +0.801: whole box |dR| = 3.61e-02, d arg = -3.39e-02 rad; vacuum-only |dR| = 2.10e-02, d arg = -1.25e-02 rad
   eta = +0.942: whole box |dR| = 6.28e-02, d arg = +5.94e-02 rad; vacuum-only |dR| = 4.73e-02, d arg = +3.92e-02 rad
   eta = +1.083: whole box |dR| = 3.17e-02, d arg = -1.52e-02 rad; vacuum-only |dR| = 3.33e-02, d arg = +1.30e-02 rad
   eta = +1.225: whole box |dR| = 3.13e-02, d arg = +4.18e-02 rad; vacuum-only |dR| = 1.51e-02, d arg = -3.14e-03 rad
   eta = +1.367: whole box |dR| = 4.05e-02, d arg = -5.99e-02 rad; vacuum-only |dR| = 9.06e-03, d arg = -4.21e-03 rad
   eta = +1.509: whole box |dR| = 5.10e-02, d arg = +9.24e-02 rad; vacuum-only |dR| = 6.86e-03, d arg = +9.21e-03 rad
   eta = +1.651: whole box |dR| = 6.18e-02, d arg = -9.70e-02 rad; vacuum-only |dR| = 5.15e-03, d arg = -1.16e-02 rad
   eta = +1.794: whole box |dR| = 7.50e-02, d arg = +1.58e-01 rad; vacuum-only |dR| = 4.50e-03, d arg = +1.24e-02 rad
   eta = +1.936: whole box |dR| = 8.84e-02, d arg = -1.32e-01 rad; vacuum-only |dR| = 4.13e-03, d arg = -1.10e-02 rad
   eta = +2.079: whole box |dR| = 1.03e-01, d arg = +2.49e-01 rad; vacuum-only |dR| = 3.64e-03, d arg = +7.88e-03 rad
   eta = +2.222: whole box |dR| = 1.17e-01, d arg = -1.61e-01 rad; vacuum-only |dR| = 4.03e-03, d arg = -3.38e-03 rad
   eta = +2.366: whole box |dR| = 1.33e-01, d arg = +3.90e-01 rad; vacuum-only |dR| = 3.58e-03, d arg = -2.06e-03 rad
   eta = +2.509: whole box |dR| = 1.48e-01, d arg = -1.81e-01 rad; vacuum-only |dR| = 4.25e-03, d arg = +8.07e-03 rad
   eta = +2.653: whole box |dR| = 1.62e-01, d arg = +5.90e-01 rad; vacuum-only |dR| = 4.07e-03, d arg = -1.32e-02 rad
   eta = +2.797: whole box |dR| = 1.75e-01, d arg = -1.95e-01 rad; vacuum-only |dR| = 4.63e-03, d arg = +1.80e-02 rad
   eta = +2.942: whole box |dR| = 1.87e-01, d arg = +8.72e-01 rad; vacuum-only |dR| = 4.89e-03, d arg = -2.05e-02 rad
   |eta| <= 0.5: max |dR| whole box 2.31e-02, vacuum-only 1.12e-02
   |eta| <= 0.9: max |dR| whole box 4.49e-02, vacuum-only 3.61e-02

====================================================================================================
12b. Sensitivity of the rung-2 read-out (what a given tolerance can detect)
====================================================================================================
max over the bins of |R_perturbed - R| (and of |arg(R_perturbed/R)|), same angles
   r = 0.10, |eta| <= 3.0: V0 + 1 mV                                                 : max |dR| = 1.96e-04, max |d arg| = 5.75e-04 rad
   r = 0.10, |eta| <= 3.0: V0 + 5 mV                                                 : max |dR| = 9.78e-04, max |d arg| = 2.88e-03 rad
   r = 0.10, |eta| <= 3.0: V_g x sinc(pi g dx), dx = 0.025 A (cell-averaged harmonic): max |dR| = 6.12e-04, max |d arg| = 1.07e-03 rad
   r = 0.10, |eta| <= 3.0: V_g x sinc(pi g dx), dx = 0.05 A                          : max |dR| = 2.45e-03, max |d arg| = 4.33e-03 rad
   r = 0.10, |eta| <= 3.0: cosine origin 0.01 A below x_s (t = 0.01 A)               : max |dR| = 3.09e-02, max |d arg| = 1.43e-01 rad
   r = 0.10, |eta| <= 3.0: engine exact propagator (one-way model)                   : max |dR| = 4.10e-04, max |d arg| = 1.20e-03 rad
   r = 0.10: read-out reference plane moved by 0.01 A changes arg R by 2 K (0.01 A) = 0.0780 to 0.0836 rad
   r = 0.10: Darwin/TT instead of exact: max |dR| = 7.60e-02
   r = 0.05, |eta| <= 3.0: V0 + 1 mV                                                 : max |dR| = 4.29e-04, max |d arg| = 8.19e-04 rad
   r = 0.05, |eta| <= 3.0: V0 + 5 mV                                                 : max |dR| = 2.14e-03, max |d arg| = 4.10e-03 rad
   r = 0.05, |eta| <= 3.0: V_g x sinc(pi g dx), dx = 0.025 A (cell-averaged harmonic): max |dR| = 9.59e-04, max |d arg| = 9.03e-04 rad
   r = 0.05, |eta| <= 3.0: V_g x sinc(pi g dx), dx = 0.05 A                          : max |dR| = 3.83e-03, max |d arg| = 3.61e-03 rad
   r = 0.05, |eta| <= 3.0: cosine origin 0.01 A below x_s (t = 0.01 A)               : max |dR| = 4.96e-02, max |d arg| = 1.59e-01 rad
   r = 0.05, |eta| <= 3.0: engine exact propagator (one-way model)                   : max |dR| = 8.98e-04, max |d arg| = 1.70e-03 rad
   r = 0.05: read-out reference plane moved by 0.01 A changes arg R by 2 K (0.01 A) = 0.0780 to 0.0836 rad
   r = 0.05: Darwin/TT instead of exact: max |dR| = 8.78e-02
   r = 0.00, |eta| <= 0.5: V0 + 1 mV                                                 : max |dR| = 1.19e-03, max |d arg| = 1.19e-03 rad
   r = 0.00, |eta| <= 0.5: V0 + 5 mV                                                 : max |dR| = 5.94e-03, max |d arg| = 5.94e-03 rad
   r = 0.00, |eta| <= 0.5: V_g x sinc(pi g dx), dx = 0.025 A (cell-averaged harmonic): max |dR| = 1.38e-03, max |d arg| = 1.38e-03 rad
   r = 0.00, |eta| <= 0.5: V_g x sinc(pi g dx), dx = 0.05 A                          : max |dR| = 5.54e-03, max |d arg| = 5.54e-03 rad
   r = 0.00, |eta| <= 0.5: cosine origin 0.01 A below x_s (t = 0.01 A)               : max |dR| = 9.98e-02, max |d arg| = 9.98e-02 rad
   r = 0.00, |eta| <= 0.5: engine exact propagator (one-way model)                   : max |dR| = 2.47e-03, max |d arg| = 2.47e-03 rad
   r = 0.00: read-out reference plane moved by 0.01 A changes arg R by 2 K (0.01 A) = 0.0804 to 0.0813 rad
   r = 0.00: Darwin/TT instead of exact: max |dR| = 1.38e-01

====================================================================================================
13. Summary of self-checks
====================================================================================================
peak resident memory of this process: 389 MB
57 checks, 0 failed
exit 0
```
