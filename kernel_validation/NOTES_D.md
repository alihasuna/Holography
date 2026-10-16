# NOTES_D — one-beam check (2f), T-transmission-limit, T-1D-agreement harness, T-step-invisibility

Scope: `reflection_holo/reflectivity1d.py`, `validation/abtem_transmission.py`, `tests/test_reflectivity1d.py`,
`tests/test_transmission_limit.py`, `tests/test_step_invisibility.py`. Nothing here was executed while
authoring. The expected outputs below are predictions; see section 7.

## 1. The one-beam equation (DERIVED_HERE from SECTION_READ premises)

The equation solved is

    psi''(z) + [k_z^2 + U(z)] psi(z) = 0,    k_z = K sin(theta_ext),    U = 2 K sigma (V + iW)   [Å^-2]

Premises:

* **Starting point.** Peng eqn 5.8 [peng_ch05 p.10–11] is the semi-reciprocal equation
  psi_G'' + Gamma_G^2 psi_G + sum_H U_GH psi_H = 0. The equation above keeps only the G = H = 0 rod, so
  U_00(z) is the laterally averaged potential. The card calls this the one-rod / systematic case
  [p.10, p.28]; the reduction itself is INFERRED on the card and DERIVED_HERE in this repository.
* **U in terms of V.**
  * Kirkland 6.6–6.7 [ch06 p.6] give U_cyc = 2meV/h^2 = sigma V/(pi lambda) in 1/lambda units.
    Converting to angular units, U = 4 pi^2 U_cyc = 2 K sigma V, with relativistic sigma and lambda
    [ch06 p.3, p.5].
  * Kirkland's eqn 6.107 check, 4 pi sigma/lambda = 2me/hbar^2 [p.49], is the same identity.
  * The result matches the repository convention K_z,int^2 = K_z,vac^2 + 2meV0/hbar^2.
* **Signs and frame.**
  * z is the outward normal. The repository convention uses exp(+ik.r).
  * W > 0 absorbs. This follows from the outgoing +i0 Green's function [peng_ch13 p.3] and from
    |exp(i sigma (V+iW))| < 1.
  * Peng's z points into the crystal [ch05 p.16, 5.109]. Our vacuum field is therefore Peng 5.109 with
    z -> -z:
    psi_vac = exp(-ik_z(z - z_ref)) + r exp(+ik_z(z - z_ref)).

Boundary conditions:

* psi and psi' are continuous at every slice boundary [Peng 5.58–5.59, p.25].
* Semi-infinite substrate: only the decaying, downgoing wave is kept, with Im q >= 0 [Peng p.27, p.36].

Algorithm:

* The potential is treated as piecewise constant on dz slices.
* The solver is a Parratt recursion of rho = up/down. The recursion formulas are derived in the
  `reflect_1d` docstring. |rho| <= 1 for W >= 0, so the recursion is stable at any depth. This addresses
  Peng's warning that the transfer matrix diverges [p.34].
* A 2x2 characteristic matrix is also implemented and is used only for test cross-checks.

The one-beam equation is the exact scalar Helmholtz equation in z; there is no paraxial step. The
paraxial kernel gives the same refraction law: for exp(i kappa x - i q z), the paraxial equation yields
kappa = -q^2/2K + sigma V, and conservation of kappa gives q^2 = k_z^2 + U. The two codes therefore
share the refraction law exactly.

## 2. Potential (DERIVED_HERE; parameters SECTION_READ)

* **Lateral average.**
  * The lateral average of one atom follows from Kirkland C.5/C.19 [appC p.6, p.10]. Integrating over
    x and y selects q_x = q_y = 0.
  * Each Lorentzian term a/(q^2+b) becomes a pi/sqrt(b) e^{-2 pi sqrt(b)|z|}.
  * Each Gaussian term c e^{-dq^2} becomes c sqrt(pi/d) e^{-pi^2 z^2/d}.
  * The prefactor is h^2/(2 pi m0 e) = 47.878 V·Å^2 from CODATA; Kirkland prints 47.86 [ch06 p.7].
* **Si parameters.** The Si row is taken from [appC p.12]. f_e(0) = 5.814 Å, which agrees with the Peng
  Table 13.3 sum, 5.8182 Å [ch13 p.24], to 0.07 %.
* **Debye–Waller.**
  * T = exp(-B s^2) with s = q/2 [Peng 13.52; appC p.7]. This is a Gaussian smearing in z with
    sigma^2 = B/8pi^2 [ch13 13.51, ch14 14.3].
  * The smearing is applied analytically: an erfcx form for the Lorentzians, and d -> d + B/4 for the
    Gaussians.
  * B defaults to `constants.B_SI_300K`; Peng ch14 Table 14.2 gives ≈ 0.526 Å^2 at 300 K [p.9].
* **Planes.**
  * (001): one plane every a/4, 2/a^2 atoms per plane.
  * (1,-1,1): cleaved bilayers {0, -d/4} + m d, with 4/(sqrt(3) a^2) atoms per plane.
  * The derivation is in the `plane_list` docstring.
  * Alternatively, `averaged_potential_z(EdgeOnCell)` averages the kernel's own atoms. Use this for
    reconstruction and overlayer cases.
* **Mean inner potential.** The isolated-atom superposition gives V0 = 2 pi a0 e f_e(0)·8/a^3 ≈ 13.9 V.
  This value is printed by `python -m reflection_holo.reflectivity1d`.
  * It is not the `V0_SI = 12 V` ASSUMPTION used by geometry.py.
  * Kirkland flags a 5–10 % bonding error at q -> 0 [appC p.7].
  * Both the kernel and the 1D solver build V from atoms, so they share about 13.9 V. Any comparison
    against geometry.py angles must state which V0 it used.
* **Absorption W.** Si parameters are NOT IN any card, so W is UNVERIFIED and `absorption` is a required
  input. The accepted forms are:
  * `False`: W = 0.
  * A ratio W/V: ASSUMPTION. Peng ch13 explicitly says W is not proportional to V.
  * Peng 13.90 Gaussians `dict(a_im, b_im, E_ref_eV)`: these use B/2 smearing and the β scaling of
    Peng 5.128.
  * `None`: raises `MissingProjectInput` unless `accept_assumptions=True`. In that case W/V = 0.1 is
    used, recorded and printed.

## 3. Phase reference

* arg r is referred to z_ref = 0, the outermost atomic plane.
* Moving the reference by δz multiplies r by exp(2 i k_z δz).
* The kernel's reference plane is the exit-plane band chosen by builder B. The harness therefore fits
  δz rather than assuming it (section 4).

## 4. How T-1D-agreement is evaluated against the kernel

The comparison runs the kernel with `rocking_curve(Surface((0,0,1),(1,1,0)), 200e3, θ, absorber=True,
absorption=False)` and the 1D solver with `rocking_curve_1d('si001', 200e3, θ, absorption=False)`.

Setup:

* Both runs use the same B and no reconstruction.
* W = 0 is used in both runs, because the codes cannot be guaranteed to share an imaginary potential.
* The kernel's graded absorber plays the role of the 1D semi-infinite substrate.
* The window is 21 angles spanning ±1.5 FWHM around the 1D (008) band.

The metrics come from `reflectivity1d.agreement_metrics`:

1. **Peak position.** |centre_k − centre_1D| ≤ 0.25·FWHM_1D.
2. **Width.** |FWHM_k/FWHM_1D − 1| ≤ 0.25.
3. **Phase.**
   * The comparison uses only angles where both |r|^2 ≥ 0.1·max. This excludes the reflectivity minima,
     where arg r is ill-conditioned.
   * The phase difference is fitted as arg r_k − arg r_1D = φ0 + 2 k_z δz.
   * The wrapped residual must be ≤ 0.3 rad.
   * δz must be reported. It is the offset between the two reference planes and is expected to be
     about the kernel's surface-plane offset.

The tolerances are ASSUMPTION. Their reasons are the expected sources of difference listed next.

Expected sources of difference (documented, not hidden):

* **Missing lateral Fourier components (largest).** The 1D model has no G ≠ 0 rods, so it has no
  non-specular beams and no surface resonances [Peng p.32]. The kernel has them. Peng warns that weak
  beams act collectively [p.48]. Disagreement will therefore be largest near emergence and resonance
  angles and smallest at a pure one-rod condition. Peng recommends tilting the azimuth 20–30 mrad off a
  zone axis to approach the systematic case [p.28].
* **Finite cell length.** The kernel reaches a steady state only after a finite length along x
  [Peng p.9]. The 1D model is the infinite-surface limit.
* **Thermal treatment.** The 1D model uses a DW-smeared average potential. With `n_phonon=1` the kernel
  uses either static or frozen atoms, depending on builder B.
* **Multislice error.** The multislice slice error is O(Δx² v) [Kirkland p.25]. The paraxial
  propagator neglects ∂²/∂x² [Kirkland p.17]. Neither affects the shared refraction law.
* **Bottom boundary.** The absorber's residual reflection, compared with the exact substrate in 1D.

If the test fails at (008), repeat it at an off-axis azimuth before concluding that the kernel is wrong.

## 5. T-transmission-limit (`validation/abtem_transmission.py`)

* **Setup.**
  * Si, beam along [100], transverse 1×1 conventional cell, 128² px (0.042 Å).
  * 10 cells thick (54.3 Å), with a/4 slices aligned on the atomic planes [Kirkland p.30–31].
  * Real potential, B = 0, 200 keV.
* **Kernel side.** The kernel's projected potential is checked for periodic wrapping. If it does not
  wrap, 3×3 images are added.
* **Frame map.** The kernel array equals the abTEM array transposed. Inverted-k mapping is also tried,
  to absorb any FFT sign difference.
* **Tolerances (ASSUMPTION).**
  * 15 strongest beams: |ΔI| ≤ 0.01 + 0.05 I.
  * Both total intensities in [0.95, 1]. Kirkland's well-behaved range is [0.95, 1.00] [p.41].
  * Reason: both codes implement the same Kirkland 6.86 algorithm. The remaining differences come from
    the near-axis sampling of the K0 singularity [appC p.11] and from details of antialiasing.
* If abTEM or ASE cannot be imported, the test is **xfail** with the reason. It is never deleted.

## 6. T-step-invisibility findings (DERIVED_HERE)

* **Internal Bragg condition.** If k_out − k_in = G, any lattice translation gives Δφ = −G·R ∈ 2πZ.
  For Si(001), a single a/4 layer gives Δφ = −2π l/4. This is in 2πZ exactly at the allowed orders
  l = 4n and is π mod 2π at the forbidden orders.
* **Vacuum phase.** The hologram measures the vacuum phase, Δφ = −2K sinθ_ext h (conventions). At the
  refraction-shifted peak, Δφ − 2πn = −2h(K sinθ_ext − K_int sinθ_int).
  * For (008) and h = a/4 with V0 = 12 V this exceeds 0.5 rad; the size is asserted by the test.
  * A lattice step is therefore phase-invisible only in the V0 → 0 limit.
  * This refraction term is what makes the step phase sensitive to V0 (R0 item b).
* **Diagnostic check of geometry.py.** `test_specular_orders_use_internal_bragg` checks that
  `specular_orders` uses the crystal wavelength (Peng 5.75/5.76). A failure is a genuine finding about
  geometry.py, not a flaw in the test.

## 7. Commands and expected output (not executed here)

Print the numbers quoted above:

```
python -m reflection_holo.reflectivity1d
```

Expected lines:

* `Kirkland prefactor ... = 47.877x V*A^2`
* `f_e(0) Kirkland C.15 = 5.8143 A ; Peng ... = 5.8182 A`
* `V0 = 12.0 V: Delta = 6.98xxe-05, theta_c = 8.356 mrad`
* `isolated-atom superposition V0 = 13.9x V`
* three peak lines and one timing line. Their values are not predicted here.

Run the tests:

```
pytest -q tests/test_reflectivity1d.py tests/test_step_invisibility.py tests/test_transmission_limit.py
```

Expected results:

* **Self-contained tests.** All tests in test_reflectivity1d.py except the last are expected to PASS.
  Only constants.py and project_inputs.py are needed for them, plus geometry.is_forbidden for
  `test_forbidden_harmonics_vanish`.
* **`test_1d_agreement_with_kernel`.** XFAIL if the kernel is absent. Otherwise PASS/FAIL is decided by
  the kernel; no result is claimed.
* **test_step_invisibility.py.** PASS, provided geometry.py follows the CONTRACT:
  * `frame` row 2 = +hkl/|hkl|;
  * `specular_orders` dicts contain `hkl`, `theta_int`, `theta_ext`;
  * `step_phase` = −(k_out−k_in)·R.

  `test_specular_orders_use_internal_bragg` is a diagnostic; see section 6.
* **test_transmission_limit.py.**
  * `test_slab_builder_diamond_cell`: PASS.
  * `test_kernel_matches_abtem_transmission`: XFAIL ("abTEM/ASE not importable") unless abTEM is
    installed.
