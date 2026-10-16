# NOTES_B: rung R2, items 2a (potential.py, already written) and 2b (propagate.py)

Conventions: exp(+i k.r); numpy FFT forward exp(-2 pi i q.r), q in cycles/A; x is the beam axis;
z is the outward normal (vacuum at +z); slices are (z, y) arrays.

## 1. Equations used, with card references

| Id | Equation | Source | Label |
|---|---|---|---|
| E1 | f_e(q) = sum a/(q^2+b) + sum c exp(-d q^2) | kirkland_appC p.8 Eq. C.15; Si row p.12 | SECTION_READ |
| E2 | V_z(q) = 2 pi e a0 f_e T e^{-2 pi i q.r_j}; V(r) = (1/A) sum V(q) e^{+2 pi i q.r} | kirkland_ch04-05 p.33 Eqs. 5.20-5.22; prefactor 47.86 kirkland_ch06 p.7 | SECTION_READ; FFT sign DERIVED_HERE |
| E4 | T = exp(-B s^2), s = q/2 | peng_ch14 Eqs. 14.1-14.3; s = q/2 from kirkland_appC p.7 | SECTION_READ / INFERRED |
| E5 | per-axis <u_x^2> = B/(8 pi^2) | peng_ch14 Eq. 14.3 | DERIVED_HERE |
| E6 | imaginary part i a_Im exp(-(b_Im+B/2)s^2) | peng_ch13 p.21 Eq. 13.87; Si parameters NOT on card (p.20) | form SECTION_READ, parameters UNVERIFIED (run raises) |
| E7 | t = exp(i sigma v), with Im v > 0 attenuating | kirkland_ch06 Eq. 6.59 | SECTION_READ / DERIVED_HERE |
| P1 | d psi/dx = [i lam/(4pi) lap + i sigma V] psi | kirkland_ch06 Eq. 6.43 | SECTION_READ |
| P2 | P = exp(-i pi lam q^2 dx) | kirkland_ch06 Eq. 6.65 | SECTION_READ |
| P3 | psi_{n+1} = IFFT{P FFT[t psi]} | kirkland_ch06 Eq. 6.86 | SECTION_READ |
| P4 | band limit 2/3 k_max on P and t, k_max = min(1/2dy, 1/2dz) | kirkland_ch06 p.35-36, Eq. 6.92 | SECTION_READ |
| P5 | P(a)P(b) = P(a+b) | kirkland_ch06 Eq. 6.88 | SECTION_READ |
| P6 | propagator tilt (not used by the engine), valid only up to about 1 degree | kirkland_ch06 Eq. 6.93, p.39 | SECTION_READ |
| P8 | sub-slicing: n_sub steps of dx/n_sub carrying v/n_sub | built from Eq. 6.86 | DERIVED_HERE |
| P9 | flux check | kirkland_ch06 Eq. 6.95, p.52 | SECTION_READ |

**Refraction consistency (DERIVED_HERE).**
- Inside a uniform V0, P1 gives the transverse dispersion q_z,int^2 = q_z,ext^2 + sigma V0/(pi lam).
- Kirkland Eq. 6.7 gives sigma/(pi lam) = 2 m e/h^2, with m = gamma m0 [kirkland_ch06 p.6].
- In angular units this becomes K_z,int^2 = K_z,ext^2 + 2 gamma m0 e V0/hbar^2.
- That is the repository refraction law. The relation Delta k^2 = 2 gamma m0 e V0/hbar^2 equals the conventions' Delta exactly.
- The paraxial kernel therefore refracts the surface-normal component exactly. Only the (eV_s)^2 term of Kirkland Eq. 5.3 is dropped, which is valid for V_s/V << 1 [kirkland_ch04-05 p.21].

## 2. Paraxial-propagator error at 20 mrad

**Definition.**
- The angular-spectrum phase is not on any card. The error formula is DERIVED_HERE from the expansion of R, Eq. 6.81 [kirkland_ch06 p.27].
- The error is d_phi/dx = (2pi/lam)(sqrt(1-a^2)-1) + pi a^2/lam ≈ -pi a^4/(4 lam), where a = lam q is the angle to the beam axis.
- The relative error of the phase is a^2/4.

**Values at 200 keV** (lam = 0.02507934 A). The command `python -m reflection_holo.multislice.propagate` should print these values. They are hand values, also asserted in `test_paraxial_error_20mrad`.

| angle | error (rad/A) | error over 1 um (rad) | relative error |
|---|---|---|---|
| 10 mrad | -3.13e-7 | -0.0031 | 2.5e-5 |
| 20 mrad | -5.011e-6 | -0.0501 | 1.0e-4 |
| 30 mrad | -2.54e-5 | -0.254 | 2.25e-4 |

**Consequences for the engine.**
- The transverse wavevector q_z (the Bragg and refraction variable) is exact.
- The error affects only the phase accumulated along x. It is common to both terraces of a flat-step comparison at the same angle.
- It is an absolute-phase error of about 0.05 rad/um at 20 mrad. It must be included in the R0 budget for any comparison spanning different angles or path lengths.
- The paraxial ray direction is sin(theta) rather than tan(theta), an angle error of theta^3/2 = 4e-6 rad at 20 mrad. This is negligible against rocking widths.

## 3. Graded absorber: design and reflection test

**Profile.** W(z) = W_max sin^2(pi xi/2), with xi = (z_top - z)/(z_top - z0). The profile has zero value and zero slope at z_top (`absorber_profile`, label ASSUMPTION: a numerical device).

**Design criterion (E10, DERIVED_HERE from P1).**
- k_z^2(z) = (K sin theta)^2 + i 4 pi sigma W(z)/lam.
- One-way attenuation is exp(-integral of Im k_z dz).
- Reflection is small when W varies slowly compared with the wavelength along z, 1/q_z ≈ 1.25 A at 20 mrad.
- Default: W_max = 10 V over 60 A.
- At 20 mrad: K sin theta = 5.01 /A and 4 pi sigma W_max/lam = 3.65 /A^2. Then Im k_z ≈ 0.36 /A at full strength, so the round trip is exp(-4I) with I of order 10, i.e. negligible.
- `potential._main` prints the WKB round-trip intensities at 8.4, 18.5 and 27.7 mrad.

**Test.** `measure_absorber_reflection`, run by `tests/test_propagate.py`:
- A 15 A Gaussian packet with carrier exp(-i K sin theta z) starts at z = 200 A in a 307 A free-space column.
- It is propagated (dx = 5 A) until its reflection would return to z = 200 A.
- The reflected flux is measured as the fraction at q_z > 0.

**Stated level.** R < 1e-6 and unabsorbed fraction < 1e-6, for the cos2 profile at 8.4 and 20 mrad.

**Sensitivity control.**
- An abrupt 10 V step at 20 mrad must reflect more than 1e-4.
- The expected value is |(k-k')/(k+k')|^2 ≈ (0.364/10.02)^2 ≈ 1.3e-3 (DERIVED_HERE).
- If the step control failed, the cos2 pass would be meaningless.
- The measured values are printed by `python -m reflection_holo.multislice.propagate`. They are not quoted here, because they are not yet recorded from a run.

## 4. Commands and expected output

    pytest tests/test_potential.py tests/test_propagate.py -v

Expected: every listed test PASSED, with 0 failed and 0 xfail. The tolerance and the external fact for each test are in its docstring.

    python -m reflection_holo.multislice.propagate
    python -m reflection_holo.multislice.potential

These print the numbers in sections 2 and 3, and the potential checks: the prefactor against 47.86, f_e(0) against 5.814, v_z(0.1 A) against 410 V*A, and the IAM V0.

## 5. Deviations from CONTRACT

- `multislice()` takes the keyword-only arguments `grid` and `record_flux`.
- `fresnel_propagator(bandwidth=None)` means no limit. This differs from `potential.bandwidth_mask(None)`, which removes the Nyquist lines.
- A `tilt` option is present but unused by the engine (it is outside the card's validity at grazing angles).
- `absorber_profile` requires `dx_slice`, as already documented in potential.py.
