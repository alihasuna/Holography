# P2: exact and two-beam reference for rung 2 of the phase-validation ladder

Prepared: 2026-09-23 (agent P2). Written incrementally; IN PROGRESS until section 10 says final.
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
U_g/(m G)^2 <= 4.4e-3, so the coefficients fall off faster than geometrically; M = 4 and M = 8 agree
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
half-period offset (surface between planes) adds pi. With exp(-i omega t) conventions all these
phases change sign.

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
(E = K^2/2k instead of k - sqrt(k^2 - K^2), relative difference K^2/4k^2 = 6.5e-5 at 16 mrad), i.e. the
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

and nothing else to this order (the two Bragg components have nearly equal |q|, their N differs by
~ q^3 delta/k^3, i.e. < 4e-4 V equivalent). Numbers (out §8): dV0_eff = -2.05 to -2.13 mV across the
plateau (-2.09 mV at the centre); the plateau moves by +0.377 urad (+1.0e-3 of its width, d(eta) =
+2.0e-3); |R| is unchanged to 1e-13 inside the plateau; arg R changes by -2.0e-3 rad at the centre,
-5.1e-3 rad at eta = -0.9 and -4.2e-3 rad at eta = +0.9 (r = 0), diverging like 1/sqrt(1 - eta^2) at
the edges. The tool reproduces this scheme with `model="engine_exact_propagator"`; an independent
split step confirms it (section 7: measured Fresnel-to-exact difference -1.18e-3 rad against the
predicted -1.21e-3 rad at r = 0.1, eta = -0.09). This is consistent with M2 rung 1 (exact and Fresnel
differ by < 0.05 % in |r|: the 2 mV shift changes the step coefficient by ~2e-4 relative).

### 4.3 Consequences for rung 2

* Run the rung-2 test with the Fresnel propagator against `model="exact"`: the a priori paraxial
  error is zero; any residual is discretisation, finite cell or finite depth (sections 5 to 8).
* Run it also with the exact propagator against `model="engine_exact_propagator"`; the difference
  between the two engine runs (same grid) is a sharp test of section 4.2 (predicted to 3e-5 rad in
  the split step), because the common discretisation error cancels.
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
fraction of the reflected packet that has not emerged at the exit plane is bounded by the same tail,
with Z the distance from the contact of the TOP edge of the beam to the exit plane.

### 5.2 Two-beam closed form (DERIVED_HERE)

The Laplace-transform identity int_0^inf J_1(t)/t exp(i eta t) dt = i (eta - sqrt(eta - 1) sqrt(eta + 1))
(principal roots, Im eta >= 0; the branch of 3.2; verified numerically for three complex eta to
< 3e-10, out §5, not cited) gives
R_D = i ph int_0^inf (J_1(t)/t) exp(i eta t) dt with ph = U_g/sqrt(U_g U_-g). Substituting
t = kc tau, eta = (E - E_B)/kc, with E_B = (G^2/4 - U_0)/(2k) and kc = sqrt(U_g U_-g)/(2k) = sigma V_g (1 + i r)
(both complex with absorption), identifies h and

    A_D(Z) = i ph int_0^Z [J_1(kc tau)/tau] exp(i (E_K - E_B) tau) d tau.

Without absorption the approach is a power law: from J_1(t) ~ sqrt(2/(pi t)) cos(t - 3 pi/4) and one
integration by parts, |A_D(Z) - R_D| <= sqrt(2/pi) (kc Z)^(-3/2) / (1 - eta^2) inside the plateau, with
oscillations at the two band-edge detunings kc (1 +- eta). With absorption the branch points
E_B +- kc move to Im E = -r sigma (V0 -+ V_g); the slowest decay is exp(-Z/Z_a),
Z_a = 1/(r sigma (V0 - V_g)). For (0,0,8): kc = 7.549e-4 rad/A (1/kc = 1324.7 A, xi_g = pi/kc = 4161.7 A),
Z_a = 2133 A (r = 0.05) and 1066 A (r = 0.1); the bound gives Z(1e-2) = 24 551 A and Z(1e-3) = 113 957 A
at eta = 0, r = 0 (out §9). The closed form tends to R_D to < 1e-13 for r > 0 and to 1.4e-4 at
Z = 4e5 A for r = 0 (checks, out §9).

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
estimated V_008 ~ 0.84 V; the engine's own value is 23 % larger. Static lattice: no Debye-Waller
factor (a frozen-phonon ensemble would reduce V_008; not computed here).

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
  16.31535 mrad, width 332.49 urad, midpoint 16.14910 mrad (+15.8 urad from the single-harmonic
  midpoint): the (0,0,4) and (0,0,12) harmonics narrow and shift the (0,0,8) plateau by 4 % to 11 %
  of its width. Relevant for later atomistic comparisons, not for the rung-2 continuum test.
* Extinction depth (amplitude) at the centre G/|U_g| = 24.47 A; kc = sigma V_g = 7.549e-4 rad/A,
  1/kc = 1324.7 A along z, extinction distance xi_g = pi/(sigma V_g) = 4161.7 A.

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

| r | eta | |R_D| | Z(|dA| <= 1e-2) (A) | Z(|dA| <= 1e-3) (A) | Z(|d arg| <= 1e-2 rad) (A) |
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
