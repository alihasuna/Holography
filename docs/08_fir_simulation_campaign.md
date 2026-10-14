# M2 reflection-multislice campaign for Fir: derivations (draft, main text in preparation)

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
