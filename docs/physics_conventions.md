# Physics conventions for the reflection-holography simulation repository

Status: revision 2, 2026-09-21 (corrected after `docs/agent_reports/E_review.md`). Every formula in
this repository must obey these conventions or state explicitly where it deviates. (Required by
instruction file section 9.8; the same conventions are used in
`docs/agent_reports/C_physics_derivations.md` and `tools/reflection_step_phase_calculator.py`.)

## Wave and sign conventions

| Quantity | Convention |
|---|---|
| Electron wave | `Psi(r, t) = exp(+i(k.r - omega t))`. Switching to `exp(-i(k.r - omega t))` flips the sign of every phase quoted in this repository; amplitudes and structure-factor magnitudes are unchanged. |
| Wavevector | Angular: `|k| = 2 pi / lambda` in rad/A. The crystallographic reciprocal vector `g_hkl` is in cycles/A with `|g_hkl| = 1/d_hkl`; `G = 2 pi g` in rad/A. Any equation must say which one it uses. |
| Fourier transform | Forward `F(q) = integral f(r) exp(-2 pi i q.r) dr` (numpy `fft` sign convention), `q` in cycles/A. A tilted plane wave `exp(+2 pi i q0.r)` therefore appears at `+q0`. |
| Wavelength | Relativistic vacuum wavelength `lambda = h c / sqrt(T (T + 2 m_e c^2))`, constants from CODATA 2018 (`m_e c^2 = 510998.950 eV`; `h`, `c`, `e` exact SI-2019 values). The beam energy is 200 keV for every configuration (PROJECT_INPUT, Ali, 2026-09-22; 300 keV is never used): `lambda = 0.02507934 A`, `k = 250.5323 rad/A`. |
| Energies | Beam energy is stored in keV and converted to eV in every formula that contains `V0`; potentials in V; the potential energy of the electron inside the crystal is `-e V0 < 0` for a positive mean inner potential `V0`. Charge `e > 0`. |
| Angles | `theta` is always the GLANCING angle between the beam and the SURFACE PLANE, never the angle to the normal. Internal (`theta_int`) and external (`theta_ext`) glancing angles are distinguished; `theta_B` (Bragg angle) is a half-scattering angle. Stored in radians; printed in mrad, degrees only where an experimental convention requires it. |
| Surface normal | `n_hat` is the OUTWARD normal (pointing into vacuum). |
| Step phase | `Delta_phi = phi(upper terrace) - phi(lower terrace) = -(k_out - k_in).R` in the `exp(+ik.r)` convention, where `R` is the translation that maps the lower-terrace truncated crystal onto the upper-terrace one and `R.n_hat = h`. For the specular beam this is `Delta_phi = -(4 pi / lambda) h sin(theta_ext)`; the sign is reported with the convention, never dropped, and the inverse relation is `h = -Delta_phi lambda / (2 pi (sin theta_in,ext + sin theta_out,ext))`. |
| Structure factor | `F_hkl = sum_j f_j exp(+2 pi i (h x_j + k y_j + l z_j))` over the 8-atom diamond cell. Kinematically forbidden means `F_hkl = 0` for spherical atoms. |
| Lengths | Angstrom everywhere in code and metadata. Pixel sizes are read from data files, never from advisory parameters. |

## Crystallographic frame (benchmark configuration `si111_cleaved_110azimuth`)

Slab frame rows expressed in cubic crystal coordinates (active rotation `r_slab = R r_crystal`):

```
x_hat = [ 1, -1,  1] / sqrt(3)   outward surface normal, plane (1,-1,1)
y_hat = [ 1, -1, -2] / sqrt(6)   in-plane, perpendicular to the beam (step edges run along z)
z_hat = [ 1,  1,  0] / sqrt(2)   beam azimuth (the beam is then tilted OUT of the surface by theta)
```

`x_hat x y_hat = z_hat` (right-handed). `(hkl)` denotes a plane, `[uvw]` a direction; in the cubic
system `[hkl]` is normal to `(hkl)`. The README statement "(1,1,-1) facet" in the inspected
repository is inconsistent with a [110] beam because `[1,1,-1].[1,1,0] = 2 != 0`; the generator's
`[1,-1,1]` is the consistent normal (`[1,-1,1].[1,1,0] = 0`).

Specular rod: the reflections `G` parallel to `n_hat`, i.e. `(n,-n,n)`. `(n,-n,n)` and `(n,n,n)` have
identical `d` and `|F|`, but only `(n,-n,n)` is specular for this surface; `(4,4,4)` is inclined at
70.5 degrees to the rod. Target reflections must be written with their signs.

## Reflection geometry

* Vacuum Bragg condition of order `n` along the (1,-1,1) rod: `sin(theta_B) = n lambda / (2 d_111)`.
* Refraction (conservation of the surface-parallel wavevector; relativistic; `T` in eV, `V0` in V):
  `sin^2(theta_int) = (sin^2(theta_ext) + Delta) / (1 + Delta)`, with
  `Delta = (k_int^2 - k_ext^2)/k_ext^2 = V0 (1 + T/(m_e c^2)) / (T (1 + T/(2 m_e c^2)))`.
  This closed form is first order in `V0`; the exact relativistic expression,
  `Delta = V0 (2 (T + m_e c^2) + V0) / (T (T + 2 m_e c^2))` (all in eV), which the calculator and the
  package use, differs by 8.4e-6 relative; the a/4 step phase changes by at most 5.1e-5 rad over the (004) to (0,0,16)
  Bragg conditions (C2 checks J1, J1b), and by 1.0e-4 rad at 2 mrad and 2.0e-4 rad at 1 mrad exit angle
  (review E4 appendix A.3).
  At 200 keV and `V0 = 12 V` (ASSUMPTION), `Delta = 6.98e-5`. The non-relativistic form
  `Delta = V0/T` is 14 percent too small at 200 keV (the relativistic value is 16 percent larger); do not use it.
* Critical angle `theta_c`, `sin(theta_c) = dK/k_int` with `dK = k sqrt(Delta)`, is the INTERNAL
  glancing angle below which a beam inside the crystal cannot escape into vacuum (total internal
  reflection at the surface barrier). At 200 keV, `V0 = 12 V`: 8.356 mrad. Because `V0 > 0` every
  externally incident beam enters the crystal, with `theta_int >= theta_c`; there is no total external
  reflection for electrons.
* Step-height wrap period for the specular beam: `h_2pi = lambda / (2 sin(theta_ext))`.
* Foreshortening of the REM image along the beam: factor `sin(theta_ext)`; directions perpendicular
  to the beam are not foreshortened. Exit-plane mapping: a surface feature at `z_s` along the beam
  appears at exit-plane height `x = x_0 - z_s tan(theta)`.
* Shadow length of a step of height `h` transverse to the beam: `h / tan(theta_ext)` on the surface.
* Reflection accessibility: a bulk reflection `G` can connect two vacuum-propagating beams only if
  `G.n_hat >= 2 dK` (equal to `2 k sin(theta_c)` to 3.5e-5 relative).
  At equality both the incident and the exit beams are exactly grazing and unusable; any usable
  reflection lies strictly inside the bound (A2 nit, A2c, E4b).

## Units of stored quantities

| Stored quantity | Unit |
|---|---|
| Positions, cell sizes, pixel sizes | A |
| Tilts | mrad, as `(theta_x, theta_y)` components in the simulation frame, sign as `theta = +lambda q` of the illuminating Fourier component |
| Phases | rad, unwrapped where stated; raw wrapped phase always preserved |
| Heights | A, with the wrap period `h_2pi` and the branch index stated |
| Energies | keV (beam, stored), eV (spreads and every formula containing `V0`), V (potentials) |
