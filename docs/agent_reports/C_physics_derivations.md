# C. Physics derivations for reflection-mode dark-field electron holography of Si surfaces

**Author of this document:** analysis agent, working to
`ba72277e-si110_reflection_holography_agent_instructions.txt` (sections 1, 9.3, 9.7).
**Date:** 2026-09-21.
**Companion script:** `reports/reflection_step_phase_calculator.py` (numpy only).
Every number in every table below is produced by that script; its complete,
unedited output is reproduced in **Appendix A**. The script self-validates with
25 assertions (all PASS, Appendix A §13).

**Repository read (read-only clone, nothing modified):**
`sample_generators/si110_cleave_slab_generator.py`,
`pipeline/step_height_reflection_formula.py`,
`pipeline/multislice_forward_model.py`,
`pipeline/multislice_tilt_series_runner.py`,
`pipeline/meta_tilt_examples.json`, `pipeline/specular_filter.py` (partial),
`README.md`, `docs/PIPELINE_LOG.md`, git log (HEAD = `6694959`).

---

## 0. Scope, evidence labels, and an honest statement about source access

### 0.1 Source access in this session

**All publisher, preprint, standards and indexing domains were blocked by this
session's egress proxy** (verified: `doi.org`, `sciencedirect.com`,
`pubmed.ncbi.nlm.nih.gov`, `arxiv.org`, `osti.gov`, `en.wikipedia.org`,
`api.crossref.org`, `rafaldb.com`, `server.ifp.uni-bremen.de` — each returned
`EGRESS_BLOCKED` or a proxy 403). Only a web *search* tool worked, which returns
titles, URLs and a machine-generated summary.

Consequently:

* **No equation, page number, or numerical value in this report is attributed to
  any book or paper in the instruction library.** Where a library source would
  normally be cited, I state only what is in the library record itself
  (bibliographic identity), i.e. `METADATA_VERIFIED` at best, and label the
  physics `DERIVED_HERE`.
* A search-engine summary is **not** a source. Per instruction 1.5 I do not use
  it as evidence for any number.
* The one material parameter that cannot be derived — the silicon mean inner
  potential — is carried as an explicit `ASSUMPTION` with a full sensitivity
  sweep (§3.2, §3.7), so that **every conclusion can be recomputed once Ali
  verifies a value from a source he can actually read.**

### 0.2 Evidence labels used (from instruction §1.4)

`DERIVED_HERE`, `ASSUMPTION`, `PROJECT_INPUT`, `METADATA_VERIFIED`,
`UNVERIFIED`. I add one session-specific qualifier, **`NOT_FETCHED_HERE`**,
meaning: a standard, definitional or textbook value that I state explicitly so
it can be checked in one step, but which I did **not** retrieve in this session.

### 0.3 Conventions (fixed once; every formula below obeys them)

| Quantity | Convention |
|---|---|
| Wave | `Psi(r,t) = exp(+i(k·r − ωt))`. With `exp(−i(k·r − ωt))` **every phase below changes sign**; amplitudes and `|F|` are unaffected. |
| Wavevector | **angular**: `|k| = 2π/λ`, units rad Å⁻¹. |
| Reciprocal lattice | crystallographic `g` in cycles Å⁻¹, `\|g_hkl\| = 1/d_hkl`; `G = 2πg` in rad Å⁻¹, `\|G_hkl\| = 2π/d_hkl`. |
| Angles | `θ` is always the **glancing** angle *to the surface*, never to the normal. Printed in mrad; degrees only where the repository uses them. |
| Surface normal | `n̂` = **outward** (pointing into vacuum). |
| Structure factor | `F_hkl = Σ_j f_j exp(+2πi(h x_j + k y_j + l z_j))`. |
| Step phase | `Δφ ≡ φ(upper terrace) − φ(lower terrace)`. |
| Lengths / energies | Å; keV for the beam, V/eV for potentials. |
| Charge | `e > 0`; `V0 > 0` is the (attractive) mean inner *potential* in volts, so the electron's potential *energy* inside the crystal is `−eV0 < 0`. |

### 0.4 Repository defaults extracted by reading the code (all `PROJECT_INPUT`)

| Parameter | Value | Where |
|---|---|---|
| `a` (Si) | 5.4309 Å | `si110_cleave_slab_generator.py`, `--a-A` default |
| `a` (Si) | 5.431 Å | `pipeline/meta_tilt_examples.json` (1.7e-5 relative difference; immaterial) |
| Beam energy | 200 keV | both |
| Slab frame | x ‖ [1,−1,1]/√3 (normal), y ‖ [1,−1,−2]/√6, z ‖ [1,1,0]/√2 (beam) | `slab_rotation_matrix()` |
| `n_x_si, n_y, n_z_si` | 9, 12, 36 | argparse defaults |
| Periods | x 9.4066 Å, y 6.6515 Å, z 3.8402 Å | `build_si110_step_slab()` |
| Si plate | `t_x = 84.659 Å`, `L_y = 79.818 Å`, `L_z,si = 138.248 Å` | derived |
| Vacuum | `x_vac = 10 Å` **each side** (above the surface *and* below the back face), `z_vac = 30 Å` each end | argparse defaults |
| Supercell | `L_x = 104.659`, `L_y = 79.818`, `L_z = 198.248` Å | derived |
| Terraces | 4, heights 0,1,2,3 × `d_111`, edges ‖ beam | `--n-terraces`, `--terrace-heights-bilayers` |
| Target reflection | `(2,−2,0)`, `θ_B = 6.531 mrad`, `ĝ·n̂ = 0.8165` | `--target-hkl` default |
| "(666) specular" | `alpha_deg = 1.375` = 23.998 mrad; `tilt_angles_mrad = 23.997` | `meta_tilt_examples.json` |
| Pixel | 0.5 Å (generator advisory) / **0.13 Å** (`meta_tilt_examples.json`) | both |
| Slice | `dz = 1.0 Å`, `z_supersampling = 4` | `multislice_forward_model.py` defaults |
| Tilt sweep | 0 → 11 mrad, step 0.15 mrad | generator defaults |

---

## 1. Relativistic electron wavelength `DERIVED_HERE`

**Premises.** Free electron, total energy `E = T + m_ec²`, momentum from
`(pc)² = T(T + 2m_ec²)`, de Broglie `λ = h/p`. No paraxial or non-relativistic
expansion.

```
λ = hc / sqrt( T (T + 2 m_e c²) ),    T = eU = kinetic energy
```

**Constants** (`NOT_FETCHED_HERE`, stated explicitly so they can be checked in
one step against `physics.nist.gov/cuu/Constants`):

* `h = 6.626 070 15e-34 J s` — exact by the 2019 SI redefinition
* `c = 299 792 458 m s⁻¹` — exact
* `e = 1.602 176 634e-19 C` — exact
* `m_e c² = 510 998.950 00 eV` — CODATA 2018 recommended value
* derived: `hc = 1.239 841 984 332e-6 eV m`

| E (keV) | λ (Å) | λ (pm) | k = 2π/λ (rad Å⁻¹) | γ | β |
|---|---|---|---|---|---|
| 100 | 0.037 014 37 | 3.701 437 | 169.7499 | 1.195 695 | 0.548 221 |
| 200 | **0.025 079 34** | 2.507 934 | **250.5323** | 1.391 390 | 0.695 314 |
| 300 | 0.019 687 49 | 1.968 749 | 319.1461 | 1.587 085 | 0.776 525 |

**Repository cross-check** (Appendix A §1). Both repository helpers
(`si110_cleave_slab_generator.relativistic_lambda_A` and
`step_height_reflection_formula.relativistic_lambda_A`) agree with the exact
formula to `<3e-7` relative. The pipeline version uses the pre-2019
`m0 = 9.10938356e-31 kg`; harmless here, but it should be replaced by a named
constants source per instruction §9.8.

---

## 2. Geometric (truncation) phase of a surface step

### 2.1 Statement and sign, for the specular beam `DERIVED_HERE`

**Premises.** (i) Far from the step edge the crystal under the upper terrace is a
*rigid copy* of the crystal under the lower terrace, displaced by a vector `R`
with `R·n̂ = h > 0`. (ii) Both terraces are illuminated by the *same* incident
plane wave `exp(i k_in·r)`. (iii) We compare the *vacuum* waves above the two
terraces.

**Derivation (exact, not kinematic).** Let `ψ(r)` solve the scattering problem
for crystal `C` with incident `exp(i k_in·r)`. For the translated crystal
`C' = C + R`, the function `ψ(r − R)` solves the problem with incident
`exp(i k_in·(r−R)) = e^{−i k_in·R} exp(i k_in·r)`; normalising the incident
amplitude,

```
ψ'(r) = e^{+i k_in·R} ψ(r − R).
```

Its outgoing plane-wave component `A exp(i k_out·r)` therefore becomes

```
A e^{i k_out·r} · exp( −i (k_out − k_in)·R ),
```

so with `q ≡ k_out − k_in` (both measured **in vacuum**),

> **`Δφ = φ_upper − φ_lower = − q·R`   (exp(+ik·r) convention)** … (2.1)

This is a **translation-covariance identity**, not a Born approximation: it holds
in full dynamical theory. Only the *amplitude* `A` is dynamical. (Numerically
confirmed to `1.2e-12 rad` in Appendix A §11(a) against an explicit truncated
(111) stack.)

**Specular case.** With `n̂` outward, `k_in = k(−sinθ n̂ + …)`,
`k_out = k(+sinθ n̂ + …)`, so `q = 2k sinθ n̂ ‖ n̂` and `q·R = 2k h sinθ`:

> **`Δφ = − (4π/λ) h sinθ`,  `|Δφ| = (4π/λ) h sinθ`** … (2.2)

**Sign in words.** An **up-step** (surface rising by `h` toward the source)
**shortens** the optical path by `2h sinθ` — the same `2d sinθ` that appears in
the Bragg construction — so the reflected wave from the higher terrace
**leads**, i.e. its phase `k·(path)` is *smaller*. With `exp(+i(k·r − ωt))` the
upper terrace is therefore **more negative** in phase. With
`exp(−i(k·r − ωt))` the sign reverses. The task statement's form
`Δφ = (k_out − k_in)·(h n̂)` is the same magnitude with the opposite sign
convention (or equivalently `φ_lower − φ_upper`); **the repository must pick one
and document it**, because the sign is what distinguishes an up-step from a
down-step.

**Up-step vs down-step *along the beam*.** For the specular beam `q ‖ n̂`, so
(2.2) does not care *where along the beam* the step sits. What does change is the
**image**: at grazing incidence an up-step shadows the surface behind it and a
down-step leaves a bright strip, and the step's projected width in the image is
`h/tanθ` = 131 Å at `h = d_111`, `θ = 22.5 mrad` — i.e. a single atomic step
occupies ~13 nm of REM image along the beam. In the repository's geometry the
step edges run **parallel** to the beam (along `z`), so the beam never climbs a
step; this is the favourable configuration and avoids the shadowing problem
entirely. It also means the phase step appears across `y`, which is *not*
foreshortened (§6).

### 2.2 General Bragg reflection `DERIVED_HERE`

Write `k_in = k(−sinθ_in n̂ + cosθ_in t̂_in)` and
`k_out = k(+sinθ_out n̂ + cosθ_out t̂_out)` with `t̂` in the surface plane. Then
`q·n̂ = k(sinθ_in + sinθ_out)` and, from (2.1),

> **`Δφ = − (2π/λ) h (sinθ_in + sinθ_out) − q_∥·R_∥`** … (2.3)

**Equivalence to the "`(4π/λ) h sinθ_B (ĝ·n̂)`" form.** If the Bragg condition is
satisfied **in vacuum**, `q = G` exactly, so `|q| = 2π/d_hkl` and, by Bragg's law
`λ = 2d sinθ_B`, `|q| = (4π/λ) sinθ_B`. Hence

```
q·n̂ = |G| (ĝ·n̂) = (4π/λ) sinθ_B (ĝ·n̂) = k(sinθ_in + sinθ_out).
```

Verified numerically to `<5e-16 rad Å⁻¹` for (666), (444), (2,−2,0), (2,2,0),
(3,3,1) in Appendix A §11(b). So the repository's denominator **is** the correct
*vacuum-Bragg* projection factor — but only for the term `q·n̂ h`, and only when
the reflection is excited at exactly the vacuum Bragg angle. Both provisos fail
in practice (§3, §4).

**This is the same `2π g·u` phase as transmission dark-field holography**, with
one crucial difference: in transmission, `u` is the *displacement field of the
lattice* inside a continuous crystal; here `u = R` is the **translation relating
two differently truncated crystals**. The lattice is not strained at all — the
phase comes entirely from *where the crystal stops*. This is why the answer is
sensitive to the surface termination and why a lattice-plane spacing is not
automatically the physical step height (instruction §9.7).

### 2.3 When is the two-terrace difference *only* a phase factor? `DERIVED_HERE`

Equation (2.1) requires the upper terrace's truncated crystal to be a rigid image
of the lower one. Numerical results, Appendix A §2b:

**Si(111) / Si(1,−1,1), single bilayer `h = d_111 = a/√3 = 3.135 532 Å`.**
`R = (a/2)[1,0,1]` is an **fcc lattice vector** (`2R/a = (1,0,1)`, component sum
even) with `R·n̂ = a/√3 = d_111` exactly, for **both** `n̂ = [111]/√3` and the
repository's `n̂ = [1,−1,1]/√3`. Its in-plane part has `|R_∥| = a/√6 = 2.217 Å`.
So **yes**: the two terraces are exact rigid translates, and (2.1) is exact to
all orders in the scattering. (Bilayer internal structure checked: sub-planes at
0 and `0.75 d_111`, giving gaps of `d_111/4 = 0.784 Å` and `3d_111/4 = 2.352 Å`
— exactly the 0.78/2.35 Å quoted in the generator's comments.)

**Si(001), single layer `h = a/4 = 1.3577 Å`.** Every fcc lattice vector has
`R·ẑ = (a/2)×integer`, so `a/4` is **unreachable by a pure translation**. A
brute-force enumeration (Appendix A §2b) finds exactly four operations that map
the 8-atom diamond basis onto itself with `t·ẑ = a/4`:

```
S = Rz(±90°) + t = a·[0.25, 0.25, 0.25]   and   a·[0.75, 0.75, 0.25]
```

i.e. the diamond **4₁ screw**. Consequences:

* **Kinematically**: if `V'(r) = V(S⁻¹r)` with `S: r ↦ Rr + t`, then
  `Ṽ'(q) = e^{−iq·t} Ṽ(Rᵀq)`. For the **specular** beam `q ‖ ẑ` and `R` a
  rotation about `ẑ`, so `Rᵀq = q` and the a/4 step gives **exactly**
  `exp(−i q h)` — the same formula as a translation.
* **Dynamically**: the incident grazing beam is *not* invariant under the 90°
  rotation. Terrace B at azimuth `φ` behaves like terrace A at azimuth `φ−90°`,
  so the two terraces have genuinely different reflection coefficients — moduli
  **and** dynamical phases. This is the same physics that makes S_A/S_B terraces
  (alternating (2×1)/(1×2) dimer domains) look different in RHEED/REM. For
  quantitative work on Si(001) single-layer steps the two-terrace waves are
  **not** related by a pure phase factor.
* **Si(001) double layer `h = a/2 = 2.7155 Å`**: `R = (a/2)[1,0,1]` *is* an fcc
  lattice vector with `R·ẑ = a/2`. (`(a/2)[0,0,1]` is **not** — component sum
  odd.) So the double-layer step **is** a pure translation and (2.1) is exact to
  all orders. This is the clean case to simulate on Si(001).

**Non-specular reflections break the "height only" picture.** For general `g`,
(2.3) contains `q_∥·R_∥`, which depends on the *in-plane* part of the step vector
and not on the height at all. Worked example (Appendix A §6), `(2,−2,0)` on the
(1,−1,1) facet with a `d_111` step:

| quantity | value |
|---|---|
| repository formula `(4π/λ) h sinθ_B (ĝ·n̂)` | 8.377 580 rad = **1.3333 × 2π** |
| exact `G·R`, `R = (a/2)[1,0,1]` | 6.283 185 rad = **1.000 000 × 2π** |
| dropped term `G_∥·R_∥` | 2.094 395 rad = 2π/3 |

On the vacuum Bragg condition `G·R` is `2π × integer` **for any lattice
translation** — the step is *invisible*. The staircase of `0, 2π/3, 4π/3, 2π`
that the generator docstring predicts for `(2,−2,0)` is an artefact of dropping
`R_∥`.

---

## 3. Refraction by the mean inner potential

### 3.1 Exact relativistic relation `DERIVED_HERE`

**Premises.** The surface-averaged crystal potential is a step of depth `V0 > 0`
(volts), uniform in the surface plane. The surface-parallel wavevector is then
conserved exactly; only the normal component changes.

Inside, the kinetic energy is `T + eV0`, so
`(ħ k_int c)² = (T+eV0)(T+eV0+2m_ec²)` while `(ħ k c)² = T(T+2m_ec²)`. Dividing,

```
k_int² − k²  =  k² · eV0 (2T + eV0 + 2 m_e c²) / [ T (T + 2 m_e c²) ]
             ≡  k² · V0 / E_eff
```

with the **exact effective energy**

> **`E_eff = T (T + 2 m_e c²) / (2T + eV0 + 2 m_e c²)`   [volts]** … (3.1)

Non-relativistic limit `E_eff → T`. Neglecting `eV0` in the denominator gives the
recognisable `E_eff = T(1 + T/2m_ec²)/(1 + T/m_ec²)`.

Define `ΔK ≡ sqrt(k_int² − k²) = k sqrt(V0/E_eff)` (rad Å⁻¹). Parallel-momentum
conservation `k cosθ_ext = k_int cosθ_int` gives, exactly,

> **`(k_int sinθ_int)² = (k sinθ_ext)² + ΔK²`**, i.e. `K_int² = K_ext² + ΔK²` … (3.2)

> **critical angle: `sinθ_c = ΔK/k = sqrt(V0/E_eff)`** … (3.3)

The popular form `sin²θ_int = sin²θ_ext + V0/E_eff` additionally assumes
`k_int ≈ k`; that is an amplitude error of `3.5e-5` at 200 keV and shifts
`θ_int` by `< 1.5 µrad` over 10–40 mrad (Appendix A §11(c)). **Use (3.2); quote
the approximate form only as a remark.**

| E (keV) | `E_eff` (V) | `V0/E_eff` | `ΔK` (rad Å⁻¹) | `θ_c` (mrad) | `k_int/k − 1` | `V0/T` (non-rel.) |
|---|---|---|---|---|---|---|
| 100 | 91 815.8 | 1.306 965e-4 | 1.940 625 | **11.4325** | 6.54e-5 | 1.2e-4 |
| 200 | 171 869.1 | 6.982 057e-5 | 2.093 416 | **8.3560** | 3.49e-5 | 6.0e-5 |
| 300 | 244 511.1 | 4.907 753e-5 | 2.235 789 | **7.0056** | 2.45e-5 | 4.0e-5 |

At 200 keV, `E_eff` is **14.1 % below** `T`, so a non-relativistic treatment
**underestimates the refraction by 16.4 %** in `sin²θ`. This is not a detail:
it moves the external (666) angle by ≈0.12 mrad.

### 3.2 The mean inner potential of Si — `ASSUMPTION`

> **`V0(Si) = 12.0 V` is adopted as an `ASSUMPTION` in this report. It was not
> verified against any source in this session.**

What I can honestly report about provenance:

* A web-search index returned a record for a paper whose title and authors match
  a standard reference on this quantity: **P. Kruse, M. Schowalter, D. Lamoen,
  A. Rosenauer, D. Gerthsen, "Determination of the mean inner potential in III–V
  semiconductors, Si and Ge by density functional theory and electron
  holography", *Ultramicroscopy* **106**(2), 105–113 (2006), DOI
  `10.1016/j.ultramic.2005.06.057`.** Its **bibliographic identity comes from a
  search index only** (the publisher record was unreachable), so it is at best
  `METADATA_VERIFIED`, and **no numerical value from it is used here**
  (`UNVERIFIED`).
* The same search summary asserted a spread of published Si values (roughly
  9–12.5 V). That summary is machine-generated text and, per instruction §1.5,
  is **not** evidence. It is mentioned only to justify carrying a wide
  sensitivity range.

**Action for Ali:** verify one value from a source you can read (Kruse *et al.*
2006 is the natural candidate; the Springer Handbook holography chapter [C02] in
the instruction library is another), then re-run the script with `V0_SI_V` set to
it. §3.7 gives everything over 9–14 V so the conclusions can be re-read
immediately.

### 3.3 Key result: the step phase at an *internal* specular Bragg condition `DERIVED_HERE`

**Premises.** (P1) the refraction model of §3.1; (P2) the specular Bragg
condition of order `n` on a rod of spacing `d` is satisfied by the **internal**
wavevectors, `2K_int = |G| = 2πn/d`, i.e. `K_int = πn/d`; (P3) the terraces are
rigid copies with `R·n̂ = h = m·d`; (P4) the observed phase is the *vacuum*
`Δφ = −q·R = −2 h K_ext`.

From (3.2), `K_ext = sqrt(K_int² − ΔK²)`, hence

```
|Δφ| = 2 (m d) K_ext = 2 m d (πn/d) · (K_ext/K_int) = 2π m n · ρ ,
```

> **`|Δφ| = 2π m n ρ`, with `ρ ≡ K_ext/K_int = sqrt(1 − (ΔK/K_int)²) < 1`** … (3.4)

The task's form `2π m n (sinθ_ext / sinθ_int)` is (3.4) with the extra
approximation `k_int ≈ k`, since
`ρ = (k sinθ_ext)/(k_int sinθ_int) = (k/k_int)·(sinθ_ext/sinθ_int)` and
`k/k_int = (1 + V0/E_eff)^(−1/2) = 1 − 3.5e-5` at 200 keV. **Use (3.4)** — it
costs nothing and is exact.

**Interpretation — this is the whole measurement.** Without refraction, `ρ = 1`
and `|Δφ| = 2π m n`, an exact multiple of 2π: *the step would be invisible*. That
is just `G·R = 2π × integer` for a lattice translation (§2.3). **The entire
holographic step signal at a specular Bragg condition is a refraction effect**,
and its size is set by `V0`.

**Accessibility rule** `DERIVED_HERE`. A reflection can be excited in true
Bragg-case (reflection) geometry only if **both** the incoming and outgoing beams
exceed the critical angle, i.e. `K_in^int > ΔK` and `K_out^int > ΔK`. Since
`K_in^int + K_out^int = G·n̂`,

> **`G·n̂ > 2ΔK = 2k sqrt(V0/E_eff)`** … (3.5)

independently of how the two angles are split. For the `(nnn)` rod this gives
`n ≥ 3` at 100–300 keV with `V0 = 12 V`: **(111) and (222) are inaccessible**
(total external reflection) at 200 and 300 keV; at 100 keV (111) is inaccessible
and (222) is only just accessible.

### 3.4 Diamond structure factor `DERIVED_HERE`

Conventional 8-atom cell: fcc sites `(0,0,0), (½,½,0), (½,0,½), (0,½,½)` plus the
same set shifted by `(¼,¼,¼)`.

```
F_hkl = f · [1 + e^{iπ(h+k)} + e^{iπ(h+l)} + e^{iπ(k+l)}] · [1 + i^(h+k+l)]
      = f · F_fcc · (1 + i^(h+k+l)),   F_fcc = 4 if h,k,l all same parity, else 0
```

so `|F| = 4f·|1 + i^(h+k+l)|` when h,k,l have the same parity:

| `h+k+l` mod 4 | parity | `\|F\|/f` | status |
|---|---|---|---|
| odd | all odd | `4√2 = 5.6569` | allowed |
| 0 | all even | `8` | allowed |
| 2 | all even | `0` | **forbidden** |

Verified against the explicit 8-atom sum to `2.2e-14` (Appendix A §2).
On the `(nnn)`/`(n,−n,n)` rod: **(222), (666), (10,10,10) are FORBIDDEN**
(and by the same token `(2,−2,2)`, `(6,−6,6)`, `(10,−10,10)`); (111), (333),
(555), (777), (999), (11,11,11) are allowed with `|F| = 4√2 f`; (444), (888),
(12,12,12) with `|F| = 8f`. On the `(00L)` rod, (004), (008), (0,0,12), (0,0,16)
are all allowed; (002) is forbidden.

### 3.5 Table A — Si(111)/(1,−1,1) specular rod, 200 keV, `V0 = 12 V`

`h₁ = d_111 = 3.1355 Å` (single bilayer), `h₂ = 2d_111 = 6.2711 Å` (double).
`θ_c = 8.356 mrad`. `B_vac` = vacuum Bragg angle (the repository's choice);
`θ_int` = internal glancing angle at the Bragg condition; **`θ_ext` = the angle
the beam must actually be set to**; `frac` = `|Δφ| mod 2π`;
`wrap` = signed `Δφ` wrapped into (−π,π].

| (nnn) | F? | `d_nnn` (Å) | `B_vac` (mrad) | `θ_int` (mrad) | **`θ_ext` (mrad)** | ρ | **`h_2π` (Å)** | `\|Δφ\|₁` (rad) | ÷2π | **frac₁ (rad)** | frac₁/2π | wrap₁ | frac₂ (rad) | frac₂/2π | wrap₂ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (111) | ALLOWED | 3.1355 | 3.999 | 3.999 | — | — | — | *inaccessible: below `θ_c`* ||||||||
| (222) | **FORBIDDEN** | 1.5678 | 7.999 | 7.998 | — | — | — | *inaccessible: below `θ_c`* ||||||||
| (333) | ALLOWED | 1.0452 | 11.998 | 11.998 | **8.610** | 0.7176 | 1.4565 | 13.5264 | 2.1528 | **0.9600** | 0.1528 | −0.9600 | 1.9200 | 0.3056 | −1.9200 |
| **(444)** | ALLOWED | 0.7839 | 15.998 | 15.997 | **13.642** | 0.8527 | 0.9193 | 21.4316 | 3.4109 | **2.5820** | 0.4109 | −2.5820 | 5.1640 | 0.8219 | 1.1192 |
| **(555)** | ALLOWED | 0.6271 | 19.997 | 19.997 | **18.168** | 0.9085 | 0.6903 | 28.5415 | 4.5425 | **3.4088** | 0.5425 | 2.8744 | 0.5343 | 0.0850 | −0.5343 |
| **(666)** | **FORBIDDEN** | 0.5226 | 23.998 | 23.997 | **22.495** | 0.9374 | **0.5575** | 35.3395 | 5.6245 | **3.9236** | 0.6245 | 2.3596 | 1.5640 | 0.2489 | −1.5640 |
| (777) | ALLOWED | 0.4479 | 27.998 | 27.997 | 26.722 | 0.9544 | 0.4693 | 41.9774 | 6.6809 | 4.2783 | 0.6809 | 2.0049 | 2.2733 | 0.3618 | −2.2733 |
| **(888)** | ALLOWED | 0.3919 | 31.999 | 31.998 | **30.888** | 0.9653 | 0.4060 | 48.5209 | 7.7223 | **4.5386** | 0.7223 | 1.7446 | 2.7940 | 0.4447 | −2.7940 |
| (999) | ALLOWED | 0.3484 | 36.001 | 35.999 | 35.017 | 0.9727 | 0.3582 | 55.0037 | 8.7541 | 4.7382 | 0.7541 | 1.5449 | 3.1933 | 0.5082 | 3.0899 |
| (10,10,10) | **FORBIDDEN** | 0.3136 | 40.003 | 40.001 | 39.119 | 0.9779 | 0.3206 | 61.4451 | 9.7793 | 4.8964 | 0.7793 | 1.3868 | 3.5097 | 0.5586 | 2.7735 |
| (11,11,11) | ALLOWED | 0.2850 | 44.006 | 44.004 | 43.204 | 0.9818 | 0.2903 | 67.8568 | 10.7997 | 5.0249 | 0.7997 | 1.2582 | 3.7667 | 0.5995 | 2.5165 |
| (12,12,12) | ALLOWED | 0.2613 | 48.009 | 48.007 | 47.275 | 0.9847 | 0.2653 | 74.2465 | 11.8167 | 5.1315 | 0.8167 | 1.1517 | 3.9798 | 0.6334 | 2.3034 |

The corresponding 100 keV and 300 keV tables are in Appendix A §4. Highlights:
at **100 keV** the only accessible orders are `n ≥ 2`, the (222) external angle
is only 2.94 mrad (`ρ = 0.249`, very strong refraction); at **300 keV** (333)
gives `ρ = 0.6684` and a near-zero fractional phase (0.032 rad) — a condition to
*avoid*.

**Comment on the repository's choice of (666).** Two independent problems:

1. **(666) is kinematically forbidden** (`F = 0` for spherical atoms in the
   harmonic approximation). There is no bulk Bragg peak there. Intensity at that
   position on the specular rod can come only from (a) the crystal-truncation rod
   (surface-truncation scattering), (b) multiple scattering (e.g. 111 + 555,
   222 + 444) — the standard explanation for the observed "forbidden 222" in Si,
   and (c) bonding-charge/anharmonic departures from spherical atoms. All three
   are *surface- or higher-order-sensitive*, so the reflected amplitude and its
   dynamical phase are exactly the quantities a simple model cannot predict. If
   surface sensitivity is the goal this can be argued for — but it must be
   *argued*, not assumed, and it cannot be modelled with a kinematic structure
   factor.
2. **The chosen angle is the one at which a `d_111` step is invisible** (§4.1).

The nearest **allowed** alternatives bracketing it are **(555) at `θ_ext` =
18.168 mrad** (frac = 3.409 rad) and **(777) at 26.722 mrad** (frac = 4.278 rad);
**(444) at 13.642 mrad** (frac = 2.582 rad) and **(888) at 30.888 mrad**
(frac = 4.539 rad) are the allowed even orders with `|F| = 8f`.

### 3.6 Table B — Si(001) specular rod `(00L)`, 200 keV, `V0 = 12 V`

`h = a/4 = 1.3577 Å` (single layer) and `a/2 = 2.7155 Å` (double layer).
On this rod `K_int = πL/a`, i.e. order `n = L/4` of `d = a/4`. All four
reflections are allowed.

| (00L) | `d_00L` (Å) | `B_vac` (mrad) | `θ_int` (mrad) | **`θ_ext` (mrad)** | ρ | `h_2π` (Å) | **frac(a/4)** (rad) | ÷2π | wrap | **frac(a/2)** (rad) | ÷2π | wrap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (004) | 1.3577 | 9.236 | 9.236 | **3.934** | 0.4260 | 3.1872 | **2.6766** | 0.4260 | −2.6766 | **5.3532** | 0.8520 | 0.9300 |
| (008) | 0.6789 | 18.473 | 18.472 | **16.474** | 0.8918 | 0.7612 | **4.9239** | 0.7837 | 1.3593 | **3.5647** | 0.5673 | 2.7185 |
| (0,0,12) | 0.4526 | 27.711 | 27.710 | **26.420** | 0.9534 | 0.4747 | **5.4056** | 0.8603 | 0.8776 | **4.5280** | 0.7207 | 1.7552 |
| (0,0,16) | 0.3394 | 36.952 | 36.950 | **35.994** | 0.9741 | 0.3485 | **5.6319** | 0.8963 | 0.6513 | **4.9806** | 0.7927 | 1.3026 |

100 and 300 keV versions in Appendix A §4b. Note the `(004)` condition at 200 keV
sits at `θ_ext = 3.93 mrad`, **below** the external critical angle of 8.36 mrad —
this is legitimate (the *internal* angle 9.24 mrad is above `θ_c`), but it means
the beam is within a few mrad of total external reflection, `ρ = 0.426`, and the
result is extremely `V0`-sensitive. Carrying `(004)` quantitatively requires a
measured `V0`.

**Reminder from §2.3:** at Si(001) the `a/4` step is a *screw*, not a translation,
so the phase relation is exact kinematically but the two terraces have different
dynamical reflectivities. The `a/2` double-layer step is the clean case.

### 3.7 Sensitivity to `V0`

Central differences at 200 keV (Appendix A §5), `h = d_111`:

| (nnn) | `θ_ext` @11 V | @12 V | @13 V | frac @11 V | @12 V | @13 V | `dθ_ext/dV0` (mrad/V) | `d\|Δφ\|/dV0` (rad/V) |
|---|---|---|---|---|---|---|---|---|
| (333) | 8.9411 | 8.6096 | 8.2648 | 1.4809 | 0.9600 | 0.4183 | −0.338 | −0.531 |
| (444) | 13.8532 | 13.6415 | 13.4265 | 2.9145 | 2.5820 | 2.2443 | −0.213 | −0.335 |
| (555) | 18.3270 | 18.1675 | 18.0066 | 3.6593 | 3.4088 | 3.1560 | −0.160 | −0.252 |
| (666) | 22.6243 | 22.4953 | 22.3656 | 4.1262 | 3.9236 | 3.7198 | **−0.129** | **−0.203** |
| (777) | 26.8303 | 26.7216 | 26.6124 | 4.4490 | 4.2783 | 4.1068 | −0.109 | −0.171 |
| (888) | 30.9823 | 30.8882 | 30.7938 | 4.6864 | 4.5386 | 4.3904 | −0.094 | −0.148 |

So `±1 V` in `V0` moves the required external angle by `∓0.13 mrad` at (666) —
**comparable to the repository's 0.15 mrad tilt step** — and moves the measured
step phase by `∓0.20 rad` (5 % of the 3.92 rad signal). A wider sweep
(`V0 = 9…14 V`) is tabulated in Appendix A §6. Conclusion: **`V0` must be a
declared, cited input of the pipeline, and a `±1 V` uncertainty must be
propagated into every quoted height.**

### 3.8 The 2π ambiguity and how a rocking series removes it `DERIVED_HERE`

> **`h_2π = λ / (2 sinθ_ext)`** — the height that costs exactly one 2π … (3.6)

At the (666) condition, 200 keV: **`h_2π = 0.5575 Å`**. A single `d_111` step
already spans **5.62 wraps**.

| feature | `h` (Å) | `\|Δφ\|` (rad) | wraps | `dφ/dθ` (rad/mrad) | max `Δθ` for `<π` (mrad) |
|---|---|---|---|---|---|
| 3 Å | 3.0 | 33.812 | 5.381 | 1.503 | **2.091** |
| `d_111` | 3.1355 | 35.340 | 5.625 | 1.571 | **2.000** |
| 1 nm | 10.0 | 112.707 | 17.938 | 5.009 | **0.627** |
| 10 nm | 100.0 | 1127.066 | 179.378 | 50.094 | **0.063** |

Derivation of the last two columns: from (2.2),

> **`d|Δφ|/dθ = (4π h/λ) cosθ`  ⇒  `Δθ_max = λ / (4h cosθ)`** … (3.7)

For the **ion-milled, nanometre-scale patterns** that motivate this work, a
single hologram is hopeless: 10 nm of topography is 179 wraps of phase. The
standard cure is a **tilt (rocking) series**: `|Δφ(θ)| = (4π h/λ) sinθ` is a
*known, monotonic* function of `θ` with `h` as the only unknown, so unwrapping
in `θ` recovers `h` absolutely, provided consecutive tilts differ by less than
half a fringe. The repository's default `--tilt-step 0.15 mrad` is adequate only
for `h < λ/(4·1.5e-4) = 41.8 Å = 4.2 nm`; for 10 nm features the step must be
`≤ 0.063 mrad`.

(An independent, cheaper unwrap: two different *energies*, or two different rod
orders `n`, give incommensurate `h_2π` and a Chinese-remainder style
disambiguation. Not developed here.)

---

## 4. Assessment of the repository formula `h = Δφ λ / (4π sinθ_B (ĝ·n̂))`

`pipeline/step_height_reflection_formula.py` L155–156:

```python
denom = 4 * np.pi * np.sin(theta_rad) * g_dot_n
h_A = delta_phi * lam / denom
```

with `theta_rad = meta['target_theta_B_mrad'] * 1e-3` (L70–72) — i.e. the
**vacuum Bragg angle** written by the generator — and `g_dot_n` from meta.

### 4.1 Which angle it must use — and what happens at the repository's angle

**It must use the external glancing angles of the actual in and out beams.** The
defensible general form is (2.3); for the specular beam,

> **`h = Δφ λ / (4π sinθ_ext)`,  `θ_ext` = the *measured external* glancing angle** … (4.1)

and, for a general reflection, the normal component alone is not enough — one
must use `Δφ = −q·R` with the full `R` (§2.3).

**At the repository's own setting the effect is catastrophic and easy to miss.**
The meta files set `alpha_deg = 1.375` (= 23.998 mrad), which the calculator
confirms *is* the exact vacuum (666) Bragg angle (23.9976 mrad for `a = 5.4309`,
23.9972 for `a = 5.431`). Feeding that **external** angle into (2.2):

| external setting | `K_ext` (rad Å⁻¹) | `K_int` (rad Å⁻¹) | effective rod order `n_eff` | `\|Δφ\|` for `h = d_111` | mod 2π |
|---|---|---|---|---|---|
| 1.375° (`meta alpha_deg`) | 6.011 767 | 6.365 825 | 6.3535 | 37.700 170 rad = 6.000 168 × 2π | **0.0011 rad** |
| 23.9976 mrad (exact vacuum Bragg of 666) | 6.011 598 | 6.365 666 | 6.3534 | 37.699 112 rad = **6.000 000 × 2π** | **0.000 000 rad** |
| **22.4953 mrad (refraction-corrected)** | 5.635 328 | 6.011 598 | **6.0000** | 35.339 499 rad = 5.624 456 × 2π | **3.9236 rad** |

> **Headline: at the repository's own beam setting, a single-bilayer step is
> phase-invisible to ~1e-3 rad, and the beam is 0.35 rod orders away from the
> true (666) condition.** `DERIVED_HERE`

The reason is structural, not numerical: `|Δφ| = 2 d_111 · k sinθ_ext` equals
`2πn` **whenever** `sinθ_ext = nλ/(2 d_111)`, i.e. at *every* vacuum `(nnn)`
Bragg angle. The rocking table (Appendix A §6) makes this explicit — the
fractional phase passes through 0 at 20.0 mrad ((555) vacuum Bragg) and at
23.9976 mrad ((666) vacuum Bragg), and through π exactly halfway between.

### 4.2 Size of the error for a 3.1 Å step

Two separate errors, of very different size:

1. **Angle error alone.** `h_reported/h_true = sinθ_ext/sinθ_B = 0.937 38`, i.e.
   **−6.26 %**; for `h = d_111 = 3.1355 Å` that is **−0.196 Å**. (Direction: the
   formula uses too *large* an angle, so it reports too *small* a height.)
2. **Wrapping error, which dominates.** The quantity a hologram delivers is the
   phase *modulo* 2π. With the correct external angle the measured value is
   3.9236 rad; substituting it into (4.1) gives

   | denominator used | recovered `h` |
   |---|---|
   | `θ_B` = 23.997 mrad | **0.3263 Å** (true 3.1355 Å — a factor 9.61 low) |
   | `θ_ext` = 22.495 mrad | **0.3481 Å** (= `h_2π × 0.6245`) |

   i.e. the naive read-out returns roughly `h mod h_2π`, not `h`.

**Therefore the repository formula, even with the angle corrected, cannot return
an atomic step height from one hologram.** It needs either (i) a rocking series
(§3.8), or (ii) prior knowledge that `h` is an integer multiple of `d_111`, used
as a lattice constraint rather than a free fit.

### 4.3 Behaviour for non-specular `g` (`ĝ·n̂` small)

* `1/(ĝ·n̂)` diverges as `g` approaches the surface plane. The repository's
  default `(2,2,0)` sibling has `ĝ·n̂ = 0` exactly (Appendix A §11b) — the
  formula would divide by zero. The code only guards `denom != 0.0` exactly
  (L156), so a `ĝ·n̂` of `1e-9` silently yields a `1e9 Å` height. **Instruction
  §9.7 explicitly asks for a small/uncertain-denominator policy, not just a
  zero check.** A defensible guard: refuse when
  `|q·n̂| < (some multiple of) the phase uncertainty / h_target`, and report the
  height *uncertainty* `σ_h = σ_φ λ/(4π sinθ_ext)` alongside `h`.
* Worse, as shown in §2.3, for non-specular `g` the height is **not** the only
  thing that sets the phase: `q_∥·R_∥` contributes and is not a function of `h`
  at all. `h = Δφ λ/(4π sinθ_B (ĝ·n̂))` is therefore **not a height formula for
  non-specular reflections**, whatever angle is used.
* The repository's default target `(2,−2,0)` is additionally **inaccessible in
  reflection geometry** at 200 keV: `G·n̂ = 2.671 821 rad Å⁻¹` while
  `2ΔK = 4.186 831 rad Å⁻¹`, so (3.5) fails. Concretely, the reflection needs
  `θ_in + θ_out = 10.665 mrad` while both beams individually need
  `> θ_c = 8.356 mrad` — impossible for any split. Any `(2,−2,0)` intensity
  produced by the current simulation is **Laue transmission through the plate**
  (§5.3), not surface reflection.

### 4.4 Off the Bragg peak, and what dynamical theory adds

**The phase is robust; the amplitude is not.** Equation (2.1) is a
translation-covariance identity, so **off the Bragg peak the phase still follows
`−q·R` with the *actual* in/out wavevectors** — there is no "deviation-parameter
correction" to the geometric phase between two rigidly translated terraces. What
the excitation error changes is:

* the **reflected amplitude** `A` (rocking-curve shape, width, asymmetry);
* the **common dynamical phase** of `A`, which cancels between two identical
  terraces but *not* between a terrace and a different reference (§7);
* for Si(001) `a/4` steps, the **difference** in `A` between the two
  90°-rotated terraces (§2.3), which does not cancel.

What a dynamical treatment adds, stated only at the level I can support without
reading the sources:

* **Bragg-case Bloch waves / dispersion surface.** Matching at the surface with
  the internal normal wavevector complex inside the total-reflection domain gives
  an evanescent wave, a Darwin-type plateau of unit reflectivity, and a
  reflection phase that sweeps across the plateau. Both the plateau width and the
  penetration depth scale with the Fourier coefficient `V_g` of the potential —
  **which is exactly zero for (666)** in the spherical-atom approximation (§3.4),
  so no such plateau exists at the repository's chosen reflection.
* **Surface resonance.** At particular grazing conditions the beam couples into a
  surface-parallel resonance channel, greatly enhancing the specular intensity
  and surface sensitivity. This is a standard feature of RHEED/REM.
* **Absorption.** Thermal diffuse and inelastic scattering give an imaginary
  optical potential; in reflection this limits the penetration depth and damps
  the dynamical oscillations. It is not optional at these path lengths.

**Sources, at the level I can support.** `[B07]` Ichimiya & Cohen, *Reflection
High-Energy Electron Diffraction*, Cambridge 2004, and `[B08]` Peng, Dudarev &
Whelan, *High-Energy Electron Diffraction and Microscopy*, OUP 2004, are the
appropriate texts for grazing-incidence dynamical theory — `METADATA_VERIFIED`
from the instruction library only; **I read neither, and I attribute no equation
to either.** A web-search index also returned a record for *Peng & Cowley,
"Dynamical diffraction calculations for RHEED and REM", Acta Cryst. A42, 545–552
(1986)*; **`UNVERIFIED`** — search-index provenance only, full text not seen.

---

## 5. Is a *transmission* multislice valid for this geometry?

Per instruction §9.3: the answer is neither "automatically yes" nor
"automatically no". Below, each sub-question separately.

### 5.1 (a) The paraxial propagator is **not** the problem `DERIVED_HERE`

Specular reflection changes the surface-normal wavevector component by
`2k sinθ = 11.27 rad Å⁻¹` — but that is a **transverse** component in the
simulation frame, because the surface normal `x` is transverse to the beam axis
`z`. The **longitudinal** component changes only from `k cos θ` to `k cos θ`: it
does not change at all, and both waves propagate forward with
`k_z/k = cos(22.5 mrad) = 0.999 747`. The scattering angle is `2θ = 45.0 mrad`.

Paraxial (Fresnel) phase error accumulated over the full cell (`L_z = 198.2 Å`,
200 keV), `|k L (sqrt(1−sin²α) − (1 − α²/2))|`:

| transverse angle α | error (rad) |
|---|---|
| 24.0 mrad | 0.0007 |
| 45.0 mrad (full specular scattering angle) | 0.0085 |
| 48.0 mrad | 0.0110 |
| 64.3 mrad (the 2/3-rule bandwidth limit at 0.13 Å) | 0.0354 |

All `≪ 1 rad`. **The Fresnel propagator is fine here.** The obstacles are
geometric and boundary-related, not paraxial.

### 5.2 (b) Geometry, footprint and wrap-around — with the repository defaults

Numbers from Appendix A §8, at the refraction-corrected `θ_ext = 22.495 mrad`
(the repository's 23.997 mrad value is also tabulated there; the differences are
small).

| quantity | value |
|---|---|
| rise of the reflected beam over the full cell, `L_z tanθ` | **4.460 Å** (`< x_vac = 10 Å`, so it does not re-enter the periodic image) |
| rise over the Si length only, `L_z,si tanθ` | 3.111 Å |
| `z` needed for a ray to fall the whole 10 Å gap, `x_vac/tanθ` | **444.5 Å** (the Si is only 138.2 Å long) |
| entrance-plane heights above the surface that land on the crystal | 0.675 … 3.785 Å |
| **fraction of the nominal 10 Å top gap that reaches the surface within the slab** | **31.10 %** |
| **fraction of the *true* 20 Å inter-plate vacuum channel (PBC in x)** | **15.55 %** |
| **fraction of the incident plane wave entering through the front END FACE** | **80.89 %** (81.54 % counting rays that descend into it) |
| useful surface-reflection fraction of the *whole* incident wave | **2.97 %** |
| ratio end-face transmission : useful surface reflection | **27 : 1** |

Two things require care about the "10 Å vacuum":

* The generator puts 10 Å above the surface **and** 10 Å below the back face. With
  periodic boundaries in `x`, those merge into a **single 20 Å vacuum channel**
  between successive plates, bounded below by our top surface and above by the
  *back face of the periodic image plate*. Quoting "10 Å of vacuum" understates
  the channel and overstates the isolation.
* The required margin is `L_z tanθ + (illumination height)`. With a plane wave
  that fills the whole cell, the illumination height *is* the whole channel, so
  the condition can never be met: the measurement band above the surface always
  contains un-interacted incident wave. That is not fatal (it is in fact a
  built-in self-reference, §7), but it must be recognised, and the incident wave
  and the reflected wave must be separated in `k`-space (they are 45 mrad apart)
  and/or in `x`.

**Conclusion:** the default cell is **far too short along the beam**. To use the
vacuum illumination at all, `L_z,si ≥ x_vac/tanθ = 444 Å`; the default is 138 Å.

### 5.3 (c) The thin-plate problem: three beams share one `k`-space spot

The slab is a **free-standing plate** of thickness `t_x = 84.66 Å = 8.47 nm =
27.0 bilayers`, with vacuum on both faces and a finite length along the beam.
Consequences `DERIVED_HERE`:

1. **The Laue-transmitted `(n,−n,n)` beam and the specular leave in the same
   direction.** Specular reflection at the (1,−1,1) surface is defined by
   `k_out − k_in = 2k sinθ n̂`, which at the Bragg condition *is* `G_(n,−n,n)`.
   Any wave inside the plate that Bragg-scatters off the same `(1,−1,1)` planes
   acquires the same `k_out`, whether it entered through the top surface, through
   the **front end face** (81 % of the illumination!), or after reflecting off the
   **back face**. A `k`-space aperture therefore **cannot** separate
   (i) top-surface reflection, (ii) Laue diffraction of the end-on transmitted
   beam, and (iii) back-face reflection. They can only be separated in *real
   space* at the exit plane — and the top-surface reflection occupies only a
   3–4.5 Å band there (§5.2), ~24–34 pixels at 0.13 Å.
2. **The beam barely enters the crystal.** A ray refracted into the surface at
   `θ_int = 23.997 mrad` descends only `L_z,si tanθ_int = 3.318 Å` over the whole
   138.2 Å of crystal — it crosses **1.06 (1,−1,1) bilayers**. There is simply not
   enough crystal along the beam for a Bragg-case dynamical reflection to build
   up. Required `L_z,si` to reach a normal penetration depth `δ_x`:

   | `δ_x` | required `L_z,si` |
   |---|---|
   | 0.5 nm | 20.8 nm (208 Å) |
   | 1 nm | 41.7 nm (417 Å) |
   | 2 nm | 83.3 nm (833 Å) |
   | 5 nm | 208.3 nm (2083 Å) |
   | 10 nm | 416.6 nm (4166 Å) |

3. **What plate thickness would make the top-surface reflection dominate?** The
   criterion is `t_x ≫ δ_x` (the Bragg-case normal penetration/extinction depth
   *measured along the normal*) **and** the end-face transmission must be removed.
   `δ_x` is set by the extinction distance of the reflection used,
   `ξ_g = π V_c cosθ_B/(λ F_g)`, projected onto the normal. **I cannot give a
   number for `ξ_g` here**: it requires electron atomic scattering factors
   (Doyle–Turner/Peng-type parameterisation) from a source I could not access;
   any value I wrote would be `UNVERIFIED`. What *can* be said without a lookup:
   for **(666), `F_g = 0`**, so `ξ_666 = ∞` and there is no Bragg-case
   total-reflection domain at all. Choosing an **allowed** reflection is a
   precondition for this question even being well posed.
4. **Absorption must be included, and the repository's hook is on the wrong
   axis.** Over 8.47 nm of Si the inelastic attenuation at 200 keV is a few per
   cent at most (mean free paths of order 10² nm; `UNVERIFIED`), so absorption
   cannot suppress the 81 % end-face transmission — geometry must (a much longer,
   thicker or semi-infinite slab, an aperture, or an explicit absorbing region).
   Separately: `multislice_forward_model.py` L269–273 defines the absorber by
   `zmin_A`/`zmax_A` and labels it "bulk side", but in this slab frame the bulk
   side is `−x`, not `±z`. That looks like a leftover from the Si(100) geometry;
   it is inert by default (meta supplies no `z_absorb_*`), but it must not be
   switched on as-is.

**Practical recommendation.** Either (i) make the slab semi-infinite in `−x` by
removing the lower vacuum and adding an absorbing bottom region **in x**, and
lengthen `L_z,si` to ≳0.5 µm; or (ii) abandon the transmission-multislice route
for the reflection amplitude and use a Bragg-case/RHEED formulation for the
reflectivity, keeping the multislice only for the vacuum propagation. The
*phase* result of §2–§3 does not depend on which route is taken.

### 5.4 (d) Sampling `DERIVED_HERE`

Antialias bandwidth (standard 2/3 rule: `q_max = (2/3)·1/(2Δ)`; the actual
Prismatic cutoff must be read from the version-matched source — `UNVERIFIED`):

| pixel Δ | `q_Nyq` (Å⁻¹) | `q_max` (Å⁻¹) | max angle @100 keV | @200 keV | @300 keV |
|---|---|---|---|---|---|
| **0.13 Å** | 3.8462 | 2.5641 | 94.91 mrad | **64.31 mrad** | 50.48 mrad |
| 0.50 Å | 1.0000 | 0.6667 | 24.68 mrad | **16.72 mrad** | 13.12 mrad |

* At **0.13 Å** (the value in `meta_tilt_examples.json`) the grid carries the
  incident beam at `−22.5 mrad`, the specular at `+22.5 mrad`, and
  `|g_666| = 1.9136 Å⁻¹ < q_max` — **adequate**.
* At **0.50 Å** (the *generator's* `--advisory-px-A` default, written into every
  `meta.json` it produces) `q_max` corresponds to **16.72 mrad at 200 keV** — the
  grid **cannot even represent the 24 mrad tilt**, let alone the reflected beam,
  and `|g_666|` is outside the band. **This default is unusable for the intended
  geometry and should be changed, or the generator should compute it from the
  required angular range.**
* **Slice thickness.** Default `dz = 1.0 Å`; the crystal `z`-period is
  `a/√2 = 3.8402 Å`, giving **3.8402 slices per period — incommensurate**, so
  atoms are binned into slightly different slices in successive periods.
  Commensurate choices: 0.96006 Å (4/period), 1.92011 Å (2/period). Also,
  `num_slices = ceil(L_z/dz) = 199` makes the *actual* `dz = 0.99622 Å`, not the
  requested 1.0 Å — the generator/runner should set `num_slices` so that `dz`
  divides the period.
* **Grazing-specific slice check:** the beam walks transversely by
  `dz·tanθ = 0.0225 Å = 0.17 pixel` per slice — sub-pixel, so the "stair-stepping"
  of a tilted beam across `z`-slices is *not* a limitation.
* **Favourable feature of this geometry:** the surface is *parallel* to the beam,
  so every slice sees essentially the same projected potential (except at the
  step, which varies in `y`). The multislice therefore reduces to propagation in
  a nearly `z`-invariant waveguide — well conditioned, and a good reason the
  transmission engine is not absurd here.

### 5.5 (e) The entrance-boundary problem, and what the REM literature did

**The problem `DERIVED_HERE`.** A `z`-sliced transmission multislice must start
the wave on a plane `z = const`. In a real REM/RHEED experiment there is no such
plane: the crystal extends upstream indefinitely and the beam enters through the
*top surface* at grazing incidence. Any finite simulation cell therefore invents
a **front end face** through which 81 % of the illumination enters the bulk
(§5.2) — a purely artificial Laue-transmission channel. Mitigations: illuminate
only a band of vacuum above the surface (not the whole cell), start the crystal
well downstream of the entrance plane, absorb at the end faces, or use a
formulation whose boundary is the *surface* rather than a `z`-plane.

**What the literature does**, stated only as far as I can support:

* **"Slices perpendicular to the beam" (Peng & Cowley type).** The
  Cowley–Moodie multislice can be run with the slicing normal to the *beam*, so
  that each slice cuts across the surface; this is the natural adaptation of
  transmission multislice to RHEED/REM and is the family the present repository
  belongs to. A search index returned *Peng & Cowley, Acta Cryst. A42, 545–552
  (1986)* — **`UNVERIFIED`**; I did not see the text and attribute no equation
  or method detail to it. `[B08]` (Peng, Dudarev & Whelan) is the book-level
  reference in the instruction library — `METADATA_VERIFIED` only.
* **"Slices parallel to the surface" (Ichimiya type).** The alternative slices
  along the surface **normal** and propagates into the crystal, using the
  surface's two-dimensional periodicity; this makes the surface the natural
  boundary and handles the entrance condition correctly, at the price of an
  evanescent-wave/boundary-matching problem. `[B07]` (Ichimiya & Cohen) is the
  library reference — **`METADATA_VERIFIED` only; not read.**
* **Bloch-wave Bragg case.** Solve the dispersion surface and match the vacuum
  and crystal solutions at the surface, with complex normal wavevectors inside
  the total-reflection domain. This is the formulation in which "extinction
  depth", "Darwin width" and "surface resonance" have precise meanings.

**Honest bottom line for §9.3:** the propagator is fine (§5.1) and the slicing
geometry is fine (§5.4); what is *not* established is the **boundary condition
and the scattering channel**. With the current cell the dominant channel is Laue
transmission through an 8.5 nm plate, not surface reflection. Validating against
a transmission benchmark would not detect this — as instruction §9.3 warns.

---

## 6. Image geometry: foreshortening and the correct projection

**Foreshortening `DERIVED_HERE`.** The surface makes an angle `θ_out` with
`k_out`, so a length `ℓ` along the beam direction *on the surface* projects to
`ℓ sinθ_out` in the plane perpendicular to `k_out`. The REM image is therefore
**compressed along the beam by `sinθ`**:

| `θ` | `sinθ` | foreshortening `1/sinθ` | surface length per 0.13 Å exit-plane pixel |
|---|---|---|---|
| 23.997 mrad (repository) | 0.023 996 | **41.67 ×** | 5.416 Å |
| 22.495 mrad (refraction-corrected) | 0.022 493 | **44.46 ×** | 5.778 Å |
| 50 mrad | 0.049 979 | **20.01 ×** | 2.598 Å |

Directions perpendicular to the beam are **not** foreshortened, so a reflection
hologram is sampled **anisotropically by a factor ≈42 at 24 mrad** (≈20 at
50 mrad). Any resolution, pixel-size or feature-size statement must say which
axis it refers to.

**In the repository's simulation** the whole 138.2 Å of Si surface maps onto
**3.110 Å of exit-plane height = 23.9 pixels** at 0.13 Å. The step edges run
along `y`, which is unforeshortened (614 pixels across `L_y = 79.8 Å`, ~153
pixels per 19.95 Å terrace), so the *step measurement* survives; but the
"image of the surface along the beam" is 24 pixels wide and cannot support any
claim about along-beam surface structure.

**Mapping the simulated exit wave to an image plane `DERIVED_HERE`.** The
simulation delivers `ψ(x,y)` on the plane `z = L_z`. That is **not** the image
plane. The correct procedure is:

1. **Select the outgoing beam** `k_out` in Fourier space (this is the dark-field
   selection) — the repository's `specular_filter.py` does this, but note
   instruction §9.1: selecting a spot of a *complex* field is not hologram
   reconstruction.
2. **Remove the carrier** `exp(i k_out·r)` (the "recenter" step), leaving the
   slowly varying envelope.
3. **Project along `k_out`, not along `z`.** Rotate the frame by `θ` about `ŷ`:
   `ζ = z cosθ + x sinθ`, `ξ = x cosθ − z sinθ`. The image plane is `ζ = const`.
   Since `cosθ = 0.99975` the `x → ξ` scaling is negligible; what matters is that
   a *feature at surface position* `z_s` appears at exit-plane height
   `x = x_0 + (L_z − z_s) tanθ`, so the surface coordinate must be recovered as

   > **`z_s = (x_0 − x)/tanθ`** — a 1/tanθ ≈ 44× magnification of the exit-plane
   > height axis into a surface-position axis.
4. Only then is the result comparable with an experimental REM image or hologram,
   which is itself a foreshortened picture of the surface.

Taking `arg(ψ)` on the raw `z = L_z` grid and treating `(x,y)` as image
coordinates conflates the surface-normal direction with the along-beam surface
coordinate. For the present geometry (steps parallel to the beam) this happens to
be harmless for the *step phase* but is wrong for any along-beam quantity.

---

## 7. Off-axis hologram formation and the reference wave

### 7.1 The measurement

With object wave `u_o(r)` (the selected reflected beam, imaged) and reference
`u_r(r)` carrying a tilt `q_c` (cycles Å⁻¹), coherent superposition in the
detector plane gives

```
I = |u_o + u_r|² = |u_o|² + |u_r|² + 2|u_o||u_r| cos(2π q_c·r + φ_o − φ_r)   … (7.1)
```

Isolating one sideband and recentring returns `u_o u_r*`, hence
**`φ_o − φ_r`** — never `φ_o` alone. This is the operation that must be kept
separate from "select a diffraction spot of a simulated complex wave"
(instruction §9.1).

### 7.2 The minimal set of reference-wave models the simulation must support

| model | definition | what the measured phase step means | pitfalls |
|---|---|---|---|
| **R1 — vacuum plane-wave reference** | `u_r = exp(2πi q_c·r)`, unscattered, ideal | `φ_o − const`: the **absolute** phase of the reflected beam, including the dynamical reflection phase `arg A` and the illumination phase. A step is the *difference* between two terraces, so `arg A` cancels **only if both terraces have the same `A`** (true for Si(111) `d_111` and Si(001) `a/2` steps; **false** for Si(001) `a/4` steps, §2.3). | Needs a genuinely unscattered path; in the repository's cell 69 % of the top-gap illumination *is* such a wave, which is convenient but must be modelled explicitly, not assumed. |
| **R2 — self-reference from a flat region of the same surface** | `u_r` = reflected wave from a step-free terrace | Common-mode phases (dynamical reflection phase, illumination, aberrations, mean-inner-potential offset) **cancel exactly**, leaving the pure geometric `−q·R`. This is the most robust quantity to compare with theory. | (i) **Twin/mirror problem**: a biprism overlaps the two halves of the field *reversed*, so the reconstruction returns `φ_o(r) − φ_r(Mr)` with `M` a mirror map — the "reference" terrace's own topography appears mirrored in the result. (ii) The reference region must be verified flat; a step there is indistinguishable from a step in the object. (iii) The two beams must be mutually coherent and take nearly equal paths. |
| **R3 — reference with residual curvature/tilt** | `u_r = exp(i[2π q_c·r + φ_curv(r)])` | The measurement is `φ_o − φ_r` with a smooth background; the *local* step is still recovered, but any **long-wavelength** surface phase is entangled with `φ_curv`. | Ramp/plane fitting removes `φ_curv` **and** genuine long-wavelength topography (instruction §9.8). Preserve raw phase, masks and fitted ramps; never tune the fit to recover a known answer. |

**The instruction document's §9.4 constraint applies:** the custom biprism's
geometry, transfer function and phase-control capability are unknown; R1/R2/R3
are *idealisations we impose*, and the simulation must state which one it used.
A freely adjustable relative-phase parameter in the simulation is not evidence of
hardware phase control.

### 7.3 `arg()` of a complex wave vs reconstruction from an intensity hologram

| | `arg(ψ)` of a simulated wave | reconstruction from `I` |
|---|---|---|
| carrier | none needed | required; `q_c` must exceed ~3× the object bandwidth |
| resolution | grid-limited | **aperture-limited**: `≈ 1/B = 3 × fringe spacing` |
| noise | none | `σ_φ = √2 /(μ √N)` (§7.4) |
| artefacts | none | centre-band leakage, twin image, aperture ringing, unwrapping errors |
| what it is | the exact phase of the field | `φ_o − φ_r` plus processing |

**Carrier requirement `DERIVED_HERE`.** If `u_o` is band-limited to `|q| < B`, the
`|u_o|²` centre band occupies `|q| < 2B` and each sideband occupies a disc of
radius `B` centred on `±q_c`. Non-overlap requires `q_c − B > 2B`, i.e.

> **`q_c > 3B`, equivalently fringe spacing `s = 1/q_c < 1/(3B)`, and
> reconstructed resolution `≈ 1/B = 3s`** … (7.2)

| fringe `s` (Å) | `q_c` (Å⁻¹) | `B_max = q_c/3` | resolution `1/B` (Å) | pixel for 4 samples/fringe |
|---|---|---|---|---|
| 0.5 | 2.000 | 0.667 | 1.50 | 0.125 |
| 1.0 | 1.000 | 0.333 | 3.00 | 0.250 |
| 2.0 | 0.500 | 0.167 | 6.00 | 0.500 |
| 5.0 | 0.200 | 0.067 | 15.00 | 1.250 |

**Nyquist:** the fringes must be sampled at `≥2` px/fringe in principle, `3–4` in
practice. **For the repository's geometry the binding constraint is the 3–4 Å
band of reflected wave above the surface** (§5.2): at 0.13 Å pixels that band is
24–34 pixels, so the carrier direction should lie **along `y`** (where there are
614 pixels) and not along `x`.

### 7.4 Phase noise `DERIVED_HERE`

Model `I(r) = Ī[1 + μ cos(2π q_c·r + φ)]` in detected counts. The sideband
estimate over `M` detector pixels is `c = (1/M) Σ_j I_j e^{−2πi q_c·r_j}`, with
`⟨c⟩ = Ī μ e^{iφ}/2`. Shot noise (Poisson, variance `Ī` per pixel) gives
`var(c) = Ī/M`, split equally between quadratures, so

> **`σ_φ = sqrt(Ī/(2M)) / (Īμ/2) = √2 / (μ √N)`**, `N = MĪ` = total counts in the
> reconstruction aperture area … (7.3)

| μ | N=10² | 10³ | 10⁴ | 10⁶ |
|---|---|---|---|---|
| 1.0 | 0.1414 | 0.0447 | 0.0141 | 0.0014 |
| 0.5 | 0.2828 | 0.0894 | 0.0283 | 0.0028 |
| 0.2 | 0.7071 | 0.2236 | 0.0707 | 0.0071 |
| 0.1 | 1.4142 | 0.4472 | 0.1414 | 0.0141 |

Converted to height at the (666) condition (`h_2π = 0.5575 Å`,
`σ_h = h_2π σ_φ/2π`): `σ_φ = 0.01 rad → σ_h = 0.0009 Å`;
`0.1 rad → 0.0089 Å`; `0.5 rad → 0.044 Å`. **The height *precision* is excellent;
it is the *branch* (which multiple of `h_2π`) that is the problem (§3.8).**

### 7.5 Verified round trip (Appendix A §12)

A synthetic intensity hologram was formed from an object with a *known* phase
step and reconstructed **without the reconstruction ever seeing the true value**.
The carrier is located on a separate **empty (vacuum) hologram** — exactly what
an experiment does — and the object reconstruction is divided by the empty one.

| `Δφ_true` (rad) | fringe (px) | dose (e/px) | recovered | error | σ (terrace) | resolution (px) |
|---|---|---|---|---|---|---|
| 2.3596 | 8 | 0 (noiseless) | 2.3596 | +0.0000 | 0.0001 | 24 |
| 2.3596 | 8 | 10⁴ | 2.3597 | +0.0001 | 0.0006 | 24 |
| 2.3596 | 8 | 10² | 2.3597 | +0.0001 | 0.0059 | 24 |
| 2.3596 | 4 | 10⁴ | 2.3596 | −0.0000 | 0.0012 | 12 |
| 2.3596 | 16 | 10⁴ | 2.3585 | −0.0011 | 0.0003 | 48 |
| **3.9236** | 8 | 10⁴ | **−2.3594** | +0.0003 | 0.0006 | 24 |
| 0.0000 (control) | 8 | 10⁴ | 0.0003 | +0.0003 | 0.0006 | 24 |
| −1.5640 (666 double step) | 8 | 10⁴ | −1.5637 | +0.0003 | 0.0006 | 24 |

**A processing trap worth recording.** The brightest bin of the *object* hologram
is generally **not** the carrier — for a 50/50 phase step it sits one bin off, on
the square-wave fundamental of the terrace pattern. Recentring on it injects a
spurious phase ramp; in a first version of this script it produced a *plausible
but wrong* step of 0.78 rad instead of 2.36 rad, with no other symptom. Locating
the carrier on an empty hologram (or on the *envelope* of the sideband lobe)
fixes it. `specular_filter.py` should be audited for exactly this.

---

## 8. Test plan — numbers a corrected repository must reproduce

All values at **200 keV, `a = 5.4309 Å`, `V0 = 12.0 V (ASSUMPTION)`**, produced
and asserted by `reflection_step_phase_calculator.py` §13 (**25/25 PASS**).

| ID | check | expected | tolerance |
|---|---|---|---|
| T1 | `λ(200 keV)` | 0.025 0793 Å | 1e-6 |
| T2 | `λ(100 keV)` | 0.037 0144 Å | 1e-6 |
| T3 | `λ(300 keV)` | 0.019 6875 Å | 1e-6 |
| T4 | vacuum Bragg angle (666) | 23.9976 mrad | 1e-3 mrad |
| T5 | critical angle | 8.3560 mrad | 1e-3 mrad |
| T6 | **external angle at the (666) internal condition** | **22.4953 mrad** | 1e-3 mrad |
| T7 | `\|F(666)\|/f` — **must be 0** | 0 | 1e-9 |
| T8 | `\|F(444)\|/f` | 8 | 1e-9 |
| T9 | `\|F(555)\|/f` | 4√2 = 5.656 854 | 1e-9 |
| T10 | **step phase (666), `h=d_111`, mod 2π** | **3.9236 rad** | 2e-3 |
| T11 | step phase (444), `h=d_111`, mod 2π | 2.5820 rad | 2e-3 |
| T12 | step phase (555), `h=d_111`, mod 2π | 3.4088 rad | 2e-3 |
| T13 | step phase (888), `h=d_111`, mod 2π | 4.5386 rad | 2e-3 |
| T14 | `h_2π` at the (666) condition | 0.5575 Å | 1e-3 |
| T15 | (2,−2,0) accessible in reflection geometry? | **no** (`G·n̂ = 2.672 < 2ΔK = 4.187`) | — |
| T16 | exact `G·R/2π` for (2,−2,0) with a `d_111` step | **1.000 000 (integer ⇒ invisible)** | 1e-9 |
| T17 | top-gap illumination reaching the surface | 31.10 % | 0.05 % |
| T18 | incident wave entering the front end face | 80.89 % | 0.05 % |
| T19 | reflected-beam rise over the cell (must stay `< x_vac`) | 4.4604 Å | 1e-3 |
| T20 | foreshortening `1/sinθ_ext` | 44.46 × | 0.02 |
| T21 | antialiased max angle at 0.13 Å | 64.31 mrad | 0.02 |
| T22 | antialiased max angle at 0.50 Å (**too small for a 24 mrad tilt**) | 16.72 mrad | 0.02 |
| T23 | max tilt step for `h = 1 nm` (increment `< π`) | 0.6270 mrad | 1e-3 |
| T24 | synthetic hologram recovers the (666) single-step phase | +2.3596 rad | 5e-3 |
| T25 | synthetic hologram, **no-step control** | 0.000 rad | 5e-3 |

**Additional qualitative checks the repository should carry (no number needed):**

* **Sign test.** Build a slab with a *down*-step and confirm the reconstructed
  phase changes sign, with the documented convention.
* **Forbidden-reflection guard.** Refuse, or loudly warn, when
  `target_hkl` has `F = 0` (222, 666, 10 10 10, 002, …).
* **Accessibility guard.** Refuse, or warn, when `G·n̂ ≤ 2ΔK` (the (2,−2,0)
  default currently fails this).
* **Small-denominator guard.** Replace `if denom != 0.0` by a check against the
  propagated height uncertainty, and always return `σ_h` with `h`.
* **PBC continuity of the staircase.** The default terrace profile `0,1,2,3`
  bilayers is **discontinuous under the `y` periodic boundary** — there is an
  artificial 3-bilayer down-step at the cell edge. Use a symmetric profile
  (`0,1,1,0` or `0,1,2,1`) or state the artefact explicitly.
* **Wrap-around / footprint assertion.** Assert `L_z tanθ < x_vac` and report the
  three fractions of T17/T18 in the run log.
* **Rocking-series unwrap.** Simulate ≥3 tilts spanning more than one `h_2π` and
  demonstrate that `h` is recovered absolutely, not modulo `h_2π`.
* **Carrier-location test.** Feed the reconstruction a hologram whose brightest
  FFT bin is *not* the carrier and confirm it still returns the right phase
  (§7.5).

---

## 9. Summary of substantive findings about the repository

1. **The chosen beam angle makes the signal vanish.** `alpha_deg = 1.375` is the
   *vacuum* (666) Bragg angle; at that **external** angle
   `|Δφ| = 6.000168 × 2π` for a `d_111` step — invisible to 1e-3 rad. The
   external angle must be **22.4953 mrad** (`V0 = 12 V`), where the phase is
   **3.9236 rad**.
2. **(666) is kinematically forbidden** (`F = 0`); (555)/(777) or (444)/(888) are
   the allowed neighbours.
3. **The default target `(2,−2,0)` cannot be excited in reflection geometry**
   (`G·n̂ = 2.672 < 2ΔK = 4.187 Å⁻¹`), and for non-specular `g` the phase depends
   on the in-plane part of the step vector, which the repository formula drops
   (predicting 4π/3 where the exact answer is 2π ≡ 0).
4. **`h = Δφ λ/(4π sinθ_B (ĝ·n̂))` uses the wrong angle (−6.26 % on `h`) and, more
   importantly, cannot resolve the 2π ambiguity** (`h_2π = 0.5575 Å`; a `d_111`
   step is 5.62 wraps, and the naive read-out returns 0.33 Å).
5. **The cell is too short along the beam by ~3–30×** for the surface reflection
   to be either illuminated (needs `L_z,si ≥ 444 Å`) or dynamically developed
   (the refracted ray crosses **1.06 bilayers** over the whole 138 Å).
   81 % of the incident wave enters the **front end face**, and the
   Laue-transmitted `(n,−n,n)` beam is **collinear with the specular** — they
   cannot be separated in `k`-space.
6. **The generator's default 0.5 Å pixel cannot represent the 24 mrad tilt**
   (2/3-rule limit 16.72 mrad at 200 keV); 0.13 Å can (64.31 mrad).
7. **The default staircase is discontinuous under the `y` PBC.**
8. **`V0` is nowhere in the pipeline.** It must become a declared, cited input
   with a `±1 V` uncertainty propagated (`∓0.13 mrad` in angle, `∓0.20 rad` in
   phase at (666)).

---

## Appendix A — full output of `reflection_step_phase_calculator.py`

Run: `python3 reports/reflection_step_phase_calculator.py` (numpy 2.4.6,
CPython 3.11.15). Reproduced verbatim.

```text

====================================================================================================
reflection_step_phase_calculator.py  --  all numbers used in C_physics_derivations.md
====================================================================================================
numpy 2.4.6
Conventions: exp(+i(k.r - wt)); |k| = 2pi/lambda [rad/A]; theta = GLANCING angle to the surface.
Delta_phi = phi(upper terrace) - phi(lower terrace) = -(k_out-k_in).R .

====================================================================================================
1.  RELATIVISTIC ELECTRON WAVELENGTH  (DERIVED_HERE from lambda = hc/sqrt(T(T+2mc^2)))
====================================================================================================
Constants: h = 6.62607015e-34 J s (SI-2019 exact), c = 299792458 m/s (exact),
           e = 1.602176634e-19 C (exact), m_e c^2 = 510998.95000 eV (CODATA 2018).
           hc = 1.239841984332e-06 eV m  (derived from the three exact values)

  E (keV)     lambda (A)   lambda (pm)   k=2pi/lam (rad/A)     gamma      beta
    100.0     0.03701437      3.701437            169.7499  1.195695  0.548221
    200.0     0.02507934      2.507934            250.5323  1.391390  0.695314
    300.0     0.01968749      1.968749            319.1461  1.587085  0.776525

Cross-check of the repository's own wavelength helpers at 200 keV:
   this script                      : 0.02507934 A
   si110_cleave_slab_generator.py   : 0.02507934 A  (rel. diff 2.23e-10)
   step_height_reflection_formula.py: 0.02507934 A  (rel. diff 6.50e-09)
   -> both repository helpers agree with the exact relativistic formula to <3e-7 relative;
      the m0 = 9.10938356e-31 kg used in the pipeline is the pre-2019 CODATA value (harmless here).

====================================================================================================
2.  DIAMOND-CUBIC STRUCTURE FACTOR AND THE (nnn) / (n,-n,n) RODS
====================================================================================================
F_hkl/f from the explicit 8-atom basis vs the closed form 4*[same parity]*|1+i^(h+k+l)| :
         hkl   |F|/f (8-atom sum)   |F|/f (closed form)   h+k+l   allowed?
   (1, 1, 1)             5.656854              5.656854       3    ALLOWED
   (2, 2, 2)             0.000000              0.000000       6  forbidden
   (3, 3, 3)             5.656854              5.656854       9    ALLOWED
   (4, 4, 4)             8.000000              8.000000      12    ALLOWED
   (5, 5, 5)             5.656854              5.656854      15    ALLOWED
   (6, 6, 6)             0.000000              0.000000      18  forbidden
   (7, 7, 7)             5.656854              5.656854      21    ALLOWED
   (8, 8, 8)             8.000000              8.000000      24    ALLOWED
   (9, 9, 9)             5.656854              5.656854      27    ALLOWED
(10, 10, 10)             0.000000              0.000000      30  forbidden
(11, 11, 11)             5.656854              5.656854      33    ALLOWED
(12, 12, 12)             8.000000              8.000000      36    ALLOWED
  (1, -1, 1)             5.656854              5.656854       1    ALLOWED
  (2, -2, 2)             0.000000              0.000000       2  forbidden
  (4, -4, 4)             8.000000              8.000000       4    ALLOWED
  (6, -6, 6)             0.000000              0.000000       6  forbidden
  (8, -8, 8)             8.000000              8.000000       8    ALLOWED
   (0, 0, 2)             0.000000              0.000000       2  forbidden
   (0, 0, 4)             8.000000              8.000000       4    ALLOWED
   (0, 0, 8)             8.000000              8.000000       8    ALLOWED
  (0, 0, 12)             8.000000              8.000000      12    ALLOWED
  (0, 0, 16)             8.000000              8.000000      16    ALLOWED
  (2, -2, 0)             8.000000              8.000000       0    ALLOWED
   (2, 2, 0)             8.000000              8.000000       4    ALLOWED

   max |explicit sum - closed form| over the test set = 2.16e-14  -> selection rule confirmed numerically.
   Rule: all-odd ALLOWED (|F|=4*sqrt(2)*f); all-even ALLOWED only if h+k+l = 4n (|F|=8f); otherwise F = 0.
   => 222, 666, (10,10,10) and their (n,-n,n) partners are FORBIDDEN.

====================================================================================================
2b.  STEP VECTORS: IS THE UPPER TERRACE A RIGID TRANSLATE OF THE LOWER?
====================================================================================================
a(Si) = 5.4309 A   d_111 = a/sqrt(3) = 3.135532 A (bilayer repeat along <111>)
   intra-bilayer gap  = d_111/4  = 0.7839 A;  inter-bilayer gap = 3 d_111/4 = 2.3516 A
   (matches the 0.78 / 2.35 A gaps quoted in si110_cleave_slab_generator.py)

Si(111)/(1,-1,1) single-BILAYER step, h = d_111:
   R = (a/2)[1,0,1] = [2.71545 0.      2.71545]  with n = [1,1,1]/sqrt3
      is an fcc lattice vector : True
      R.n_hat = 3.135532 A   (= d_111? True)
      in-plane part |R_par|   = 2.217156 A = a/sqrt(6) = 2.217156 A
   R = (a/2)[1,0,1] = [2.71545 0.      2.71545]  with n = [1,-1,1]/sqrt3 (repo)
      is an fcc lattice vector : True
      R.n_hat = 3.135532 A   (= d_111? True)
      in-plane part |R_par|   = 2.217156 A = a/sqrt(6) = 2.217156 A
   -> the two terraces of a d_111 step ARE exact rigid translates; the phase factor is the ONLY difference (far from the step edge).

Si(001) steps (n_hat = [0,0,1]):
   R = (a/4)[0,0,1] single layer  -> fcc lattice vector? False   R.n = 1.357725 A
   R = (a/2)[0,0,1]               -> fcc lattice vector? False   R.n = 2.715450 A
   R = (a/2)[1,0,1] double layer  -> fcc lattice vector? True   R.n = 2.715450 A
   Any fcc lattice vector has R.z_hat = (a/2)*integer, so h = a/4 is
   UNREACHABLE by a pure translation.  Brute-force search over the 90 deg
   rotations about [001] and translations on an a/8 grid, for operations
   S(r) = R r + t with t.z_hat = a/4 that map the 8-atom basis onto itself:
      S = Rz(+90) + t = a*[0.25 0.25 0.25]   -> maps diamond onto itself
      S = Rz(+90) + t = a*[0.75 0.75 0.25]   -> maps diamond onto itself
      S = Rz(-90) + t = a*[0.25 0.25 0.25]   -> maps diamond onto itself
      S = Rz(-90) + t = a*[0.75 0.75 0.25]   -> maps diamond onto itself
      (4 such operations found; these are the diamond 4_1 screws.)
   Consequence (report 2.3):
    * KINEMATICALLY the specular amplitude obeys Vt'(q) = exp(-i q.t) Vt(R^T q),
      and R^T q = q for q || n_hat, so the a/4 step gives EXACTLY exp(-i q h).
    * DYNAMICALLY the two terraces are 90 deg-rotated crystals, so terrace B at
      azimuth phi behaves like terrace A at azimuth phi-90 deg: the reflection
      coefficients (moduli AND dynamical phases) differ.  Only the a/2 double
      step, a PURE translation, is exact to all orders.

====================================================================================================
3.  REFRACTION BY THE MEAN INNER POTENTIAL  (V0 = 12.0 V, ASSUMPTION)
====================================================================================================
  E (keV)     E_eff (V)     V0/E_eff    dK (rad/A)  theta_c (mrad)   k_int/k - 1  V0/T (nonrel)
    100.0       91815.8 1.306965e-04      1.940625         11.4325     6.535e-05   1.200000e-04
    200.0      171869.1 6.982057e-05      2.093416          8.3560     3.491e-05   6.000000e-05
    300.0      244511.1 4.907753e-05      2.235789          7.0056     2.454e-05   4.000000e-05

   E_eff = T(T+2mc^2)/(2T + eV0 + 2mc^2)  (DERIVED_HERE, exact).
   The relativistic E_eff is ~14% BELOW T at 200 keV, so the non-relativistic V0/T
   underestimates the refraction by ~16% in sin^2(theta).
   sin^2(theta_int) = sin^2(theta_ext) + V0/E_eff holds exactly for the NORMAL
   wavevector components: (k_int sin th_int)^2 = (k sin th_ext)^2 + k^2 V0/E_eff.
   Writing it as sin^2 th_int = sin^2 th_ext + V0/E_eff additionally assumes k_int ~ k,
   an error of only 3.49e-05 in amplitude at 200 keV (negligible) -- see report 3.3.

====================================================================================================
4.  Si(111) SPECULAR ROD (n,-n,n) == (nnn):  REFRACTION-SHIFTED ANGLES AND STEP PHASES
====================================================================================================
h1 = d_111 = 3.1355 A (single bilayer);  h2 = 2 d_111 = 6.2711 A (double bilayer)
V0 = 12.0 V (ASSUMPTION).  'B_vac' = vacuum Bragg angle (what the repository uses).
'th_int' = internal glancing angle at the Bragg condition; 'th_ext' = the angle you must actually set.
frac = (|Delta_phi| mod 2pi).  wrap = Delta_phi wrapped into (-pi,pi] (signed, exp(+ik.r)).

--- E = 100 keV  (lambda = 0.037014 A, theta_c = 11.433 mrad) ---
     (nnn)        F?  d_nnn(A)    B_vac   th_int   th_ext     rho  h_2pi(A) |   |dphi|1     /2pi    frac1  f1/2pi    wrap1 |    frac2  f2/2pi    wrap2
------------------------------------------------------------------------------------------------------------------------------------------------------
 (1, 1, 1)   ALLOWED    3.1355    5.902    5.902       --      --        -- | INACCESSIBLE: internal Bragg angle is below the critical angle (total external reflection)
 (2, 2, 2) FORBIDDEN    1.5678   11.805   11.804    2.942  0.2492    6.2900 |    3.1321   0.4985   3.1321  0.4985  -3.1321 |   6.2642  0.9970   0.0190
 (3, 3, 3)   ALLOWED    1.0452   17.708   17.707   13.523  0.7637    1.3687 |   14.3945   2.2910   1.8282  0.2910  -1.8282 |   3.6563  0.5819   2.6269
 (4, 4, 4)   ALLOWED    0.7839   23.612   23.610   20.659  0.8749    0.8959 |   21.9898   3.4998   3.1402  0.4998  -3.1402 |   6.2805  0.9996   0.0027
 (5, 5, 5)   ALLOWED    0.6271   29.516   29.514   27.211  0.9219    0.6802 |   28.9630   4.6096   3.8303  0.6096   2.4529 |   1.3774  0.2192  -1.3774
 (6, 6, 6) FORBIDDEN    0.5226   35.422   35.420   33.525  0.9465    0.5521 |   35.6808   5.6788   4.2649  0.6788   2.0183 |   2.2466  0.3576  -2.2466
 (7, 7, 7)   ALLOWED    0.4479   41.329   41.326   39.714  0.9610    0.4661 |   42.2651   6.7267   4.5660  0.7267   1.7172 |   2.8488  0.4534  -2.8488
 (8, 8, 8)   ALLOWED    0.3919   47.237   47.234   45.830  0.9702    0.4040 |   48.7700   7.7620   4.7877  0.7620   1.4955 |   3.2923  0.5240   2.9909
 (9, 9, 9)   ALLOWED    0.3484   53.147   53.143   51.900  0.9766    0.3568 |   55.2236   8.7891   4.9581  0.7891   1.3250 |   3.6331  0.5782   2.6501
(10, 10, 10) FORBIDDEN    0.3136   59.058   59.055   57.939  0.9811    0.3196 |   61.6420   9.8106   5.0933  0.8106   1.1898 |   3.9035  0.6213   2.3797
(11, 11, 11)   ALLOWED    0.2850   64.972   64.968   63.956  0.9844    0.2896 |   68.0352  10.8281   5.2033  0.8281   1.0799 |   4.1235  0.6563   2.1597
(12, 12, 12)   ALLOWED    0.2613   70.888   70.884   69.957  0.9869    0.2648 |   74.4096  11.8427   5.2946  0.8427   0.9886 |   4.3059  0.6853   1.9772

--- E = 200 keV  (lambda = 0.025079 A, theta_c = 8.356 mrad) ---
     (nnn)        F?  d_nnn(A)    B_vac   th_int   th_ext     rho  h_2pi(A) |   |dphi|1     /2pi    frac1  f1/2pi    wrap1 |    frac2  f2/2pi    wrap2
------------------------------------------------------------------------------------------------------------------------------------------------------
 (1, 1, 1)   ALLOWED    3.1355    3.999    3.999       --      --        -- | INACCESSIBLE: internal Bragg angle is below the critical angle (total external reflection)
 (2, 2, 2) FORBIDDEN    1.5678    7.999    7.998       --      --        -- | INACCESSIBLE: internal Bragg angle is below the critical angle (total external reflection)
 (3, 3, 3)   ALLOWED    1.0452   11.998   11.998    8.610  0.7176    1.4565 |   13.5264   2.1528   0.9600  0.1528  -0.9600 |   1.9200  0.3056  -1.9200
 (4, 4, 4)   ALLOWED    0.7839   15.998   15.997   13.642  0.8527    0.9193 |   21.4316   3.4109   2.5820  0.4109  -2.5820 |   5.1640  0.8219   1.1192
 (5, 5, 5)   ALLOWED    0.6271   19.997   19.997   18.168  0.9085    0.6903 |   28.5415   4.5425   3.4088  0.5425   2.8744 |   0.5343  0.0850  -0.5343
 (6, 6, 6) FORBIDDEN    0.5226   23.998   23.997   22.495  0.9374    0.5575 |   35.3395   5.6245   3.9236  0.6245   2.3596 |   1.5640  0.2489  -1.5640
 (7, 7, 7)   ALLOWED    0.4479   27.998   27.997   26.722  0.9544    0.4693 |   41.9774   6.6809   4.2783  0.6809   2.0049 |   2.2733  0.3618  -2.2733
 (8, 8, 8)   ALLOWED    0.3919   31.999   31.998   30.888  0.9653    0.4060 |   48.5209   7.7223   4.5386  0.7223   1.7446 |   2.7940  0.4447  -2.7940
 (9, 9, 9)   ALLOWED    0.3484   36.001   35.999   35.017  0.9727    0.3582 |   55.0037   8.7541   4.7382  0.7541   1.5449 |   3.1933  0.5082   3.0899
(10, 10, 10) FORBIDDEN    0.3136   40.003   40.001   39.119  0.9779    0.3206 |   61.4451   9.7793   4.8964  0.7793   1.3868 |   3.5097  0.5586   2.7735
(11, 11, 11)   ALLOWED    0.2850   44.006   44.004   43.204  0.9818    0.2903 |   67.8568  10.7997   5.0249  0.7997   1.2582 |   3.7667  0.5995   2.5165
(12, 12, 12)   ALLOWED    0.2613   48.009   48.007   47.275  0.9847    0.2653 |   74.2465  11.8167   5.1315  0.8167   1.1517 |   3.9798  0.6334   2.3034

--- E = 300 keV  (lambda = 0.019687 A, theta_c = 7.006 mrad) ---
     (nnn)        F?  d_nnn(A)    B_vac   th_int   th_ext     rho  h_2pi(A) |   |dphi|1     /2pi    frac1  f1/2pi    wrap1 |    frac2  f2/2pi    wrap2
------------------------------------------------------------------------------------------------------------------------------------------------------
 (1, 1, 1)   ALLOWED    3.1355    3.139    3.139       --      --        -- | INACCESSIBLE: internal Bragg angle is below the critical angle (total external reflection)
 (2, 2, 2) FORBIDDEN    1.5678    6.279    6.279       --      --        -- | INACCESSIBLE: internal Bragg angle is below the critical angle (total external reflection)
 (3, 3, 3)   ALLOWED    1.0452    9.418    9.418    6.295  0.6684    1.5638 |   12.5986   2.0051   0.0322  0.0051  -0.0322 |   0.0644  0.0102  -0.0644
 (4, 4, 4)   ALLOWED    0.7839   12.558   12.558   10.422  0.8299    0.9445 |   20.8584   3.3197   2.0088  0.3197  -2.0088 |   4.0177  0.6394   2.2655
 (5, 5, 5)   ALLOWED    0.6271   15.698   15.697   14.048  0.8949    0.7008 |   28.1137   4.4744   2.9809  0.4744  -2.9809 |   5.9619  0.9489   0.3213
 (6, 6, 6) FORBIDDEN    0.5226   18.838   18.837   17.486  0.9283    0.5630 |   34.9949   5.5696   3.5789  0.5696   2.7042 |   0.8747  0.1392  -0.8747
 (7, 7, 7)   ALLOWED    0.4479   21.978   21.977   20.831  0.9478    0.4726 |   41.6877   6.6348   3.9885  0.6348   2.2946 |   1.6939  0.2696  -1.6939
 (8, 8, 8)   ALLOWED    0.3919   25.118   25.117   24.121  0.9603    0.4081 |   48.2705   7.6825   4.2882  0.6825   1.9950 |   2.2931  0.3650  -2.2931
 (9, 9, 9)   ALLOWED    0.3484   28.259   28.258   27.376  0.9688    0.3596 |   54.7829   8.7190   4.5174  0.7190   1.7657 |   2.7517  0.4379  -2.7517
(10, 10, 10) FORBIDDEN    0.3136   31.399   31.399   30.607  0.9748    0.3217 |   61.2475   9.7478   4.6989  0.7478   1.5843 |   3.1145  0.4957  -3.1145
(11, 11, 11)   ALLOWED    0.2850   34.540   34.540   33.822  0.9792    0.2911 |   67.6780  10.7713   4.8461  0.7713   1.4371 |   3.4090  0.5426   2.8742
(12, 12, 12)   ALLOWED    0.2613   37.682   37.681   37.024  0.9826    0.2659 |   74.0831  11.7907   4.9681  0.7907   1.3151 |   3.6530  0.5814   2.6302

   Accessibility rule (DERIVED_HERE): a reflection can be excited in TRUE reflection
   (Bragg-case) geometry only if  G.n_hat > 2 dK,  i.e. |G| cos(angle(G,n)) > 2 k sqrt(V0/E_eff).
   For the (nnn) rod this means n >= 3 at 100-300 keV with V0 = 12 V.

====================================================================================================
4b.  Si(001) SPECULAR ROD (0,0,L):  a/4 AND a/2 STEPS
====================================================================================================
single-layer step a/4 = 1.3577 A;  double-layer step a/2 = 2.7155 A
The (0,0,L) rod has K_int = pi L / a at the Bragg condition; equivalently order n = L/4 of d = a/4.

--- E = 100 keV (theta_c = 11.433 mrad) ---
     (00L)        F?  d_00L(A)    B_vac   th_int   th_ext     rho  h_2pi(A) |  frac(a/4)    /2pi     wrap |  frac(a/2)    /2pi     wrap
---------------------------------------------------------------------------------------------------------------------------------------
 (0, 0, 4)   ALLOWED    1.3577   13.631   13.631    7.424  0.5446    2.4931 |     3.4218  0.5446   2.8613 |     0.5605  0.0892  -0.5605
 (0, 0, 8)   ALLOWED    0.6789   27.265   27.264   24.752  0.9078    0.7478 |     5.1249  0.8157   1.1583 |     3.9666  0.6313   2.3166
(0, 0, 12)   ALLOWED    0.4526   40.904   40.902   39.273  0.9601    0.4714 |     5.5316  0.8804   0.7516 |     4.7800  0.7608   1.5032
(0, 0, 16)   ALLOWED    0.3394   54.551   54.548   53.337  0.9778    0.3471 |     5.7245  0.9111   0.5587 |     5.1659  0.8222   1.1173

--- E = 200 keV (theta_c = 8.356 mrad) ---
     (00L)        F?  d_00L(A)    B_vac   th_int   th_ext     rho  h_2pi(A) |  frac(a/4)    /2pi     wrap |  frac(a/2)    /2pi     wrap
---------------------------------------------------------------------------------------------------------------------------------------
 (0, 0, 4)   ALLOWED    1.3577    9.236    9.236    3.934  0.4260    3.1872 |     2.6766  0.4260  -2.6766 |     5.3532  0.8520   0.9300
 (0, 0, 8)   ALLOWED    0.6789   18.473   18.472   16.474  0.8918    0.7612 |     4.9239  0.7837   1.3593 |     3.5647  0.5673   2.7185
(0, 0, 12)   ALLOWED    0.4526   27.711   27.710   26.420  0.9534    0.4747 |     5.4056  0.8603   0.8776 |     4.5280  0.7207   1.7552
(0, 0, 16)   ALLOWED    0.3394   36.952   36.950   35.994  0.9741    0.3485 |     5.6319  0.8963   0.6513 |     4.9806  0.7927   1.3026

--- E = 300 keV (theta_c = 7.006 mrad) ---
     (00L)        F?  d_00L(A)    B_vac   th_int   th_ext     rho  h_2pi(A) |  frac(a/4)    /2pi     wrap |  frac(a/2)    /2pi     wrap
---------------------------------------------------------------------------------------------------------------------------------------
 (0, 0, 4)   ALLOWED    1.3577    7.250    7.250    1.867  0.2576    5.2711 |     1.6184  0.2576  -1.6184 |     3.2368  0.5152   3.0464
 (0, 0, 8)   ALLOWED    0.6789   14.501   14.501   12.696  0.8755    0.7754 |     4.7193  0.7511   1.5639 |     3.1554  0.5022   3.1278
(0, 0, 12)   ALLOWED    0.4526   21.752   21.752   20.593  0.9467    0.4781 |     5.2787  0.8401   1.0045 |     4.2742  0.6803   2.0090
(0, 0, 16)   ALLOWED    0.3394   29.005   29.004   28.146  0.9704    0.3498 |     5.5389  0.8815   0.7443 |     4.7946  0.7631   1.4886

====================================================================================================
5.  SENSITIVITY OF THE (nnn) RESULTS TO V0  (+/- 1 V, 200 keV)
====================================================================================================
     (nnn) |                 th_ext(mrad) |              frac(d_111) [rad] |   dth/dV0  dfrac/dV0
           |      11 V      12 V      13 V |      11 V      12 V      13 V    |    mrad/V      rad/V
-------------------------------------------------------------------------------------------------
 (3, 3, 3) |    8.9411    8.6096    8.2648 |    1.4809    0.9600    0.4183    |   -0.3382    -0.5313
 (4, 4, 4) |   13.8532   13.6415   13.4265 |    2.9145    2.5820    2.2443    |   -0.2133    -0.3351
 (5, 5, 5) |   18.3270   18.1675   18.0066 |    3.6593    3.4088    3.1560    |   -0.1602    -0.2516
 (6, 6, 6) |   22.6243   22.4953   22.3656 |    4.1262    3.9236    3.7198    |   -0.1294    -0.2032
 (7, 7, 7) |   26.8303   26.7216   26.6124 |    4.4490    4.2783    4.1068    |   -0.1089    -0.1711
 (8, 8, 8) |   30.9823   30.8882   30.7938 |    4.6864    4.5386    4.3904    |   -0.0942    -0.1480

   (dfrac/dV0 is a central difference of the fractional phase; where the
    phase wraps between 11 and 13 V the difference is meaningless and the
    unwrapped derivative d|dphi|/dV0 = 2 h dK_ext/dV0 should be used:)
      (nnn) = (444): d|Delta_phi|/dV0 = -0.3351 rad/V
      (nnn) = (555): d|Delta_phi|/dV0 = -0.2516 rad/V
      (nnn) = (666): d|Delta_phi|/dV0 = -0.2032 rad/V
      (nnn) = (888): d|Delta_phi|/dV0 = -0.1480 rad/V

====================================================================================================
6.  THE REPOSITORY (666) CHOICE, AND THE REPOSITORY FORMULA h = dphi*lam/(4 pi sin(th_B) (g.n))
====================================================================================================
Repository meta (pipeline/meta_tilt_examples.json): alpha_deg = 1.375 -> 23.9983 mrad
   vacuum Bragg angle of (666) with a = 5.4309 A (generator default)  : 23.9976 mrad = 1.37496 deg   (d_666 = 0.522589 A)
   vacuum Bragg angle of (666) with a = 5.431  A (meta_tilt_examples) : 23.9972 mrad = 1.37494 deg   (d_666 = 0.522598 A)
   -> 1.375 deg = 23.997 mrad IS the VACUUM (666) Bragg angle. It ignores refraction.

With refraction (V0 = 12.0 V):
   internal Bragg glancing angle       = 23.9968 mrad
   REQUIRED EXTERNAL glancing angle    = 22.4953 mrad
   offset from the repository setting  = -1.5030 mrad (-6.26 %)
   |Delta_phi| for h = d_111           = 35.3395 rad = 5.6245 x 2pi
   fractional (mod 2pi)                = 3.9236 rad = 0.6245 x 2pi   (signed, wrapped: +2.3596 rad)
   height per 2pi  h_2pi               = 0.5575 A
   WITHOUT refraction the vacuum momentum transfer would equal G_666 exactly and
   Delta_phi = -G.R = -2pi*integer == 0 : a d_111 step would be INVISIBLE.  The whole
   measurable signal at a specular Bragg condition is a refraction effect.

*** What the repository actually simulates: the beam is set to the EXTERNAL angle 1.375 deg. ***
   theta_ext = 1.375 deg (meta alpha_deg)                
      K_ext = 6.011767 rad/A,  K_int = 6.365825 rad/A  -> effective rod order n_eff = K_int d_111/pi = 6.3535
      |Delta_phi| for h = d_111 = 37.700170 rad = 6.000168 x 2pi  ->  mod 2pi = 0.001058 rad
   theta_ext = 23.9976 mrad (exact vacuum Bragg of 666)  
      K_ext = 6.011598 rad/A,  K_int = 6.365666 rad/A  -> effective rod order n_eff = K_int d_111/pi = 6.3534
      |Delta_phi| for h = d_111 = 37.699112 rad = 6.000000 x 2pi  ->  mod 2pi = 0.000000 rad
   theta_ext = 22.4953 mrad (refraction-corrected)       
      K_ext = 5.635328 rad/A,  K_int = 6.011598 rad/A  -> effective rod order n_eff = K_int d_111/pi = 6.0000
      |Delta_phi| for h = d_111 = 35.339499 rad = 5.624456 x 2pi  ->  mod 2pi = 3.923572 rad
   => AT THE REPOSITORY'S OWN SETTING A SINGLE-BILAYER STEP IS PHASE-INVISIBLE to ~3e-3 rad.
   The setting is 0.35 rod orders away from the true (666) condition, and it is exactly
   the angle at which q_vacuum = G_666 and the geometric phase is a multiple of 2pi.

Rocking curve of the d_111 step phase (h = d_111) vs EXTERNAL angle, 200 keV:
 th_ext(mrad)  th_int(mrad)    n_eff  |dphi| (rad)      /2pi  mod 2pi (rad)  wrapped (rad)
      18.0000       19.8446   4.9620       28.2783    4.5006         3.1456         3.1376
      20.0000       21.6751   5.4196       31.4200    5.0006         0.0041        -0.0041
      21.0000       22.6010   5.6511       32.9908    5.2506         1.5748        -1.5748
      22.0000       23.5331   5.8841       34.5615    5.5006         3.1456         3.1376
      22.4953       23.9968   6.0000       35.3395    5.6245         3.9235         2.3596
      23.0000       24.4705   6.1184       36.1322    5.7506         4.7163         1.5669
      23.9976       25.4104   6.3534       37.6991    6.0000         6.2832         0.0000
      25.0000       26.3591   6.5905       39.2735    6.2506         1.5744        -1.5744
      26.0000       27.3094   6.8281       40.8441    6.5005         3.1450         3.1382
      26.7216       27.9972   7.0000       41.9774    6.6809         4.2783         2.0049

Sweep over the ASSUMED mean inner potential (200 keV, h = d_111):
  V0 (V)  th_c(mrad) |      (444) th_ext / frac |      (555) th_ext / frac |      (666) th_ext / frac |      (888) th_ext / frac
     9.0      7.2365 |    14.2670 /     3.5647 |    18.6418 /     4.1538 |    22.8801 /     4.5280 |    31.1697 /     4.9806
    10.0      7.6279 |    14.0616 /     3.2420 |    18.4851 /     3.9076 |    22.7526 /     4.3277 |    31.0761 /     4.8337
    11.0      8.0002 |    13.8532 /     2.9145 |    18.3270 /     3.6593 |    22.6243 /     4.1262 |    30.9823 /     4.6864
    12.0      8.3560 |    13.6415 /     2.5820 |    18.1675 /     3.4088 |    22.4953 /     3.9236 |    30.8882 /     4.5386
    13.0      8.6972 |    13.4265 /     2.2443 |    18.0066 /     3.1560 |    22.3656 /     3.7198 |    30.7938 /     4.3904
    14.0      9.0255 |    13.2080 /     1.9011 |    17.8443 /     2.9011 |    22.2351 /     3.5148 |    30.6991 /     4.2417

Error of the repository read-out h = Delta_phi*lambda/(4 pi sin(th_B)(g.n)):
   (i)  wrong angle only (using th_B = 23.997 mrad instead of th_ext = 22.495 mrad):
        h_reported / h_true = sin(th_ext)/sin(th_B) = 0.93738  -> -6.26 %
        for a true h = d_111 = 3.1355 A this is an error of -0.1963 A
   (ii) with the WRAPPED phase actually measured (3.9236 rad) fed into the formula:
        with th_B  = 23.997 mrad -> h = 0.3263 A (true 3.1355 A, factor 9.61 low)
        with th_ext= 22.495 mrad -> h = 0.3481 A  (= h_2pi * frac = 0.3481 A)
        -> the 2pi ambiguity, NOT the angle error, dominates.

Repository DEFAULT target reflection (2,-2,0) off the (1,-1,1) facet:
   d_220 = 1.920113 A, |G| = 3.272300 rad/A, g_hat.n_hat = 0.816497 (repo prints 0.8165)
   vacuum Bragg angle = 6.5307 mrad (repo meta target_theta_B_mrad)
   G.n_hat = 2.671821 rad/A     2*dK = 4.186831 rad/A
   ACCESSIBLE IN REFLECTION GEOMETRY?  G.n > 2 dK  ->  False
   sin(th_in)+sin(th_out) available in vacuum = 1.066458e-02  -> th_in+th_out = 10.665 mrad,
   but BOTH beams need > theta_c = 8.356 mrad, i.e. a sum > 16.712 mrad.
   -> (2,-2,0) CANNOT be excited in Bragg (reflection) geometry from this surface at 200 keV.

   Vacuum-Bragg phase of a d_111 step for a NON-specular g (the repository formula vs the exact answer):
      repository:   (4 pi/lam) h sin(th_B) (g.n) = 8.377580 rad = 1.333333 x 2pi
      exact:        G.R with R = (a/2)[1,0,1] = 6.283185 rad = 1.000000 x 2pi
      The repository formula keeps only the NORMAL component of R (h n_hat) and drops
      G_par . R_par, which for (2,-2,0) contributes -2.094395 rad = 2pi/3.
      Exact answer on the vacuum Bragg condition: G.R = 2pi x integer -> the step is INVISIBLE.
      The repository's predicted 2pi/3-per-bilayer staircase is an artefact of dropping R_par.

====================================================================================================
7.  2*pi AMBIGUITY AND THE ROCKING-SERIES REQUIREMENT
====================================================================================================
h_2pi = lambda / (2 sin theta_ext).  At 200 keV, (666) condition, h_2pi = 0.5575 A
         h     h (A)  |dphi| (rad)  /2pi wraps  dphi/dtheta (rad/mrad)  max dtheta for <pi (mrad)
       3 A    3.0000       33.8120      5.3813                  1.5028                     2.0905
     d_111    3.1355       35.3395      5.6245                  1.5707                     2.0001
      1 nm   10.0000      112.7066     17.9378                  5.0094                     0.6271
     10 nm  100.0000     1127.0656    179.3781                 50.0938                     0.0627

   Rule of thumb (DERIVED_HERE): d(|dphi|)/d(theta) = (4 pi h/lambda) cos(theta)
   => the tilt step must satisfy  dtheta < lambda / (4 h cos theta).
   The repository's default tilt step (0.15 mrad, si110_cleave_slab_generator.py) is
   adequate only for h < lambda/(4*0.15e-3) = 41.8 A = 4.18 nm.

====================================================================================================
8.  MULTISLICE GEOMETRY WITH THE REPOSITORY DEFAULT SLAB
====================================================================================================
Defaults read from sample_generators/si110_cleave_slab_generator.py:
   periods: x 9.4066 A (a sqrt3), y 6.6515 A (a sqrt1.5), z 3.8402 A (a/sqrt2)
   n_x_si=9, n_y=12, n_z_si=36, x_vac=10 A/side, z_vac=30 A/side
   Si plate : t_x = Lx_si = 84.659 A, Ly = 79.818 A, Lz_si = 138.248 A
   supercell: Lx = 104.659 A, Ly = 79.818 A, Lz = 198.248 A
   4 terraces of Ly/4 = 19.954 A across y (step edges || beam)

-- at theta = repository 23.997 mrad (tan = 0.024003) --
   rise of the reflected beam over the full cell   : 4.7585 A   (x_vac = 10 A -> no re-entry: True)
   rise over the Si length only                    : 3.3184 A
   z needed for a ray to fall the whole 10 A gap   : 416.6 A   (Si is only 138.2 A long)
   fraction of the NOMINAL 10 A top gap that reaches the surface within the slab : 33.18 %
   fraction of the TRUE 20 A inter-plate vacuum channel (PBC in x)                 : 16.59 %
   entrance-plane heights above the surface that land on the crystal: 0.720 .. 4.038 A
   fraction of the incident plane wave entering through the FRONT END FACE     : 80.89 % (81.58 % counting the rays that descend into it)
   ratio (end-face transmission)/(useful surface reflection) = 25.5 : 1
   useful surface-reflection fraction of the whole incident wave = 3.17 %

-- at theta = refraction-corrected 22.495 mrad (tan = 0.022499) --
   rise of the reflected beam over the full cell   : 4.4604 A   (x_vac = 10 A -> no re-entry: True)
   rise over the Si length only                    : 3.1105 A
   z needed for a ray to fall the whole 10 A gap   : 444.5 A   (Si is only 138.2 A long)
   fraction of the NOMINAL 10 A top gap that reaches the surface within the slab : 31.10 %
   fraction of the TRUE 20 A inter-plate vacuum channel (PBC in x)                 : 15.55 %
   entrance-plane heights above the surface that land on the crystal: 0.675 .. 3.785 A
   fraction of the incident plane wave entering through the FRONT END FACE     : 80.89 % (81.54 % counting the rays that descend into it)
   ratio (end-face transmission)/(useful surface reflection) = 27.2 : 1
   useful surface-reflection fraction of the whole incident wave = 2.97 %

Interaction length available to the surface reflection (DERIVED_HERE, geometric):
   internal glancing angle at the (666) condition: 23.9968 mrad
   a refracted ray entering at the top surface descends only Lz_si*tan(th_int) = 3.318 A
   over the whole 138.2 A of crystal, i.e. it crosses 1.058 (1,-1,1) bilayers.
   -> the beam barely enters the crystal: no Bragg-case dynamical reflection can build up.
   Lz_si required for a normal penetration depth delta_x (= delta_x / tan(th_int)):
      delta_x =   0.5 nm -> Lz_si >=      20.8 nm (      208 A)
      delta_x =   1.0 nm -> Lz_si >=      41.7 nm (      417 A)
      delta_x =   2.0 nm -> Lz_si >=      83.3 nm (      833 A)
      delta_x =   5.0 nm -> Lz_si >=     208.3 nm (     2083 A)
      delta_x =  10.0 nm -> Lz_si >=     416.6 nm (     4166 A)
   Also needed just to use the vacuum illumination: Lz_si >= x_vac/tan(th_ext) = 444 A. The default is 138 A.
   Plate thickness t_x = Lx_si = 84.7 A = 27.0 bilayers = 8.47 nm.

Foreshortening / image sampling:
   theta = 23.997 mrad   : sin(theta) = 0.023996  -> foreshortening 1/sin =   41.67 x ;  surface length per 0.13 A exit-plane pixel =    5.416 A
   theta = 22.495 mrad   : sin(theta) = 0.022493  -> foreshortening 1/sin =   44.46 x ;  surface length per 0.13 A exit-plane pixel =    5.778 A
   theta = 50 mrad       : sin(theta) = 0.049979  -> foreshortening 1/sin =   20.01 x ;  surface length per 0.13 A exit-plane pixel =    2.598 A
   the whole 138.2 A Si surface maps onto 3.110 A of exit-plane height = 23.9 pixels at 0.13 A.

====================================================================================================
9.  SAMPLING / BANDWIDTH / SLICE THICKNESS
====================================================================================================
   px = 0.13 A, E = 100.0 keV: q_Nyq = 3.8462 1/A ( 142.36 mrad), q_max(2/3) = 2.5641 1/A (  94.91 mrad)
   px = 0.13 A, E = 200.0 keV: q_Nyq = 3.8462 1/A (  96.46 mrad), q_max(2/3) = 2.5641 1/A (  64.31 mrad)
   px = 0.13 A, E = 300.0 keV: q_Nyq = 3.8462 1/A (  75.72 mrad), q_max(2/3) = 2.5641 1/A (  50.48 mrad)
   px = 0.50 A, E = 100.0 keV: q_Nyq = 1.0000 1/A (  37.01 mrad), q_max(2/3) = 0.6667 1/A (  24.68 mrad)
   px = 0.50 A, E = 200.0 keV: q_Nyq = 1.0000 1/A (  25.08 mrad), q_max(2/3) = 0.6667 1/A (  16.72 mrad)
   px = 0.50 A, E = 300.0 keV: q_Nyq = 1.0000 1/A (  19.69 mrad), q_max(2/3) = 0.6667 1/A (  13.12 mrad)

   The reflected beam sits at +theta and the incident at -theta, so the grid must
   carry at least |k_x| = k sin(theta): 2*theta = 44.99 mrad of angular span (specular) plus the crystal's own beams.
   px = 0.50 A (generator default advisory_pixel_size_A) gives q_max = 0.6667 1/A = 16.72 mrad at 200 keV
   -> CANNOT represent a 24 mrad tilt at all.  px = 0.13 A (meta_tilt_examples.json) gives
      64.31 mrad, which is adequate.

   |g_666| = 1.91355 1/A must be inside q_max: 0.13 A -> True, 0.50 A -> False

   Paraxial (Fresnel) propagator error over the cell, |phase_exact - phase_paraxial|:
      alpha =  24.0 mrad over Lz = 198.2 A: |Dphi| = 0.00069 rad  (~k L alpha^4/8 = 0.00206 rad)
      alpha =  45.0 mrad over Lz = 198.2 A: |Dphi| = 0.00849 rad  (~k L alpha^4/8 = 0.02546 rad)
      alpha =  48.0 mrad over Lz = 198.2 A: |Dphi| = 0.01098 rad  (~k L alpha^4/8 = 0.03296 rad)
      alpha =  64.3 mrad over Lz = 198.2 A: |Dphi| = 0.03537 rad  (~k L alpha^4/8 = 0.10613 rad)
   -> the paraxial propagator is NOT the limiting approximation here.

   Slice thickness: default dz = 1.00 A; crystal z-period a/sqrt2 = 3.8402 A
      slices per z-period = 3.8402 (NOT an integer -> incommensurate slicing)
      commensurate alternative: 2 slices/period -> dz = 1.92011 A
      commensurate alternative: 4 slices/period -> dz = 0.96006 A
      commensurate alternative: 8 slices/period -> dz = 0.48003 A
      num_slices = ceil(Lz/dz) = 199 -> actual dz = 0.99622 A
      transverse walk of the beam per slice = dz*tan(theta) = 0.02250 A (0.1731 px) -> sub-pixel, not a limitation

====================================================================================================
10.  OFF-AXIS HOLOGRAPHY: CARRIER, RESOLUTION, NOISE
====================================================================================================
I = |u_o + u_r|^2 = |u_o|^2 + |u_r|^2 + 2|u_o||u_r| cos(2 pi q_c.r + phi_o - phi_r)
Sideband isolation returns arg(u_o u_r*) = phi_o - phi_r.

Carrier requirement (DERIVED_HERE): if the object phase/amplitude is band-limited to |q| < B,
the autocorrelation centre band occupies |q| < 2B and the sidebands sit at +/- q_c with
radius B, so clean separation needs q_c > 3B, i.e. fringe spacing s = 1/q_c < 1/(3B).
Equivalently: reconstructed resolution ~ 1/B = 3 s  -> '3 fringes per resolved feature'.

 fringe s (A)   q_c (1/A)  B_max=q_c/3  resolution 1/B (A)  px for 4/fringe (A)
        0.500      2.0000       0.6667               1.500               0.1250
        1.000      1.0000       0.3333               3.000               0.2500
        2.000      0.5000       0.1667               6.000               0.5000
        5.000      0.2000       0.0667              15.000               1.2500

Phase noise (DERIVED_HERE, see report 7.4): for a reconstruction aperture collecting
N detected electrons with fringe contrast mu, sigma_phi = sqrt(2)/(mu sqrt(N)).
    mu     N=1e2     N=1e3     N=1e4     N=1e6   [rad]
  1.00    0.1414    0.0447    0.0141    0.0014
  0.50    0.2828    0.0894    0.0283    0.0028
  0.20    0.7071    0.2236    0.0707    0.0071
  0.10    1.4142    0.4472    0.1414    0.0141

Height precision implied by the phase precision at the (666) condition (200 keV):
   sigma_phi = 0.010 rad -> sigma_h = h_2pi*sigma/2pi = 0.00089 A
   sigma_phi = 0.050 rad -> sigma_h = h_2pi*sigma/2pi = 0.00444 A
   sigma_phi = 0.100 rad -> sigma_h = h_2pi*sigma/2pi = 0.00887 A
   sigma_phi = 0.500 rad -> sigma_h = h_2pi*sigma/2pi = 0.04436 A

====================================================================================================
11.  NUMERICAL SELF-CHECKS
====================================================================================================
(a) Translation theorem for the specular beam, truncated (111) stack
    (q = 2 K_ext = 11.270656 rad/A, depth attenuation 1/200 A, 4000 bilayers):
    arg(A_upper/A_lower) = +2.359612947 rad
    predicted -q*h mod 2pi = +2.359612947 rad
    |A_upper/A_lower|    = 0.999999999998  (must be 1)
    agreement: 1.23e-12 rad

(b) Equivalence of the two forms of the vacuum step phase,
    (2 pi/lam) h (sin th_in + sin th_out)  ==  (4 pi/lam) h sin(th_B)(g.n),
    i.e.  q.n_hat = G.n_hat  when the Bragg condition holds in VACUUM:
      (6, 6, 6): g.n = 0.333333, th_B =  23.998 mrad, |G.n| = 4.00773212, 2k sin(th_B)(g.n) = 4.00773212, diff = 0.00e+00 rad/A
      (4, 4, 4): g.n = 0.333333, th_B =  15.998 mrad, |G.n| = 2.67182141, 2k sin(th_B)(g.n) = 2.67182141, diff = 0.00e+00 rad/A
     (2, -2, 0): g.n = 0.816497, th_B =   6.531 mrad, |G.n| = 2.67182141, 2k sin(th_B)(g.n) = 2.67182141, diff = 4.44e-16 rad/A
      (2, 2, 0): g.n = 0.000000, th_B =   6.531 mrad, |G.n| = 0.00000000, 2k sin(th_B)(g.n) = 0.00000000, diff = 1.95e-17 rad/A
      (3, 3, 1): g.n = 0.132453, th_B =  10.065 mrad, |G.n| = 0.66795535, 2k sin(th_B)(g.n) = 0.66795535, diff = 0.00e+00 rad/A

(c) exact  sin^2(th_int) = [ (k sin th_ext)^2 + dK^2 ] / k_int^2   vs
    approx sin^2(th_int) = sin^2(th_ext) + V0/E_eff :
    th_ext =  10.000 mrad -> th_int exact  13.0313 mrad, approx  13.0318 mrad, diff -0.45 urad
    th_ext =  20.000 mrad -> th_int exact  21.6751 mrad, approx  21.6758 mrad, diff -0.76 urad
    th_ext =  22.495 mrad -> th_int exact  23.9968 mrad, approx  23.9976 mrad, diff -0.84 urad
    th_ext =  40.000 mrad -> th_int exact  40.8629 mrad, approx  40.8644 mrad, diff -1.43 urad

====================================================================================================
12.  SYNTHETIC INTENSITY-HOLOGRAM RECONSTRUCTION (no ground truth passed to the reconstruction)
====================================================================================================
Object: two terraces, phase step dphi_true, unit amplitude. Reference: unit plane wave with
carrier of 'fringe' pixels.  Reconstruction: carrier located on an EMPTY hologram, Hann
sideband aperture of radius q_c/3, reference-hologram division, medians of terrace interiors.

 dphi_true  fringe(px)  dose(e/px)  recovered     error  sigma_terr  res(px)
    2.3596         8.0           0     2.3596   +0.0000      0.0001     24.0
    2.3596         8.0       10000     2.3597   +0.0001      0.0006     24.0
    2.3596         8.0         100     2.3597   +0.0001      0.0059     24.0
    2.3596         4.0       10000     2.3596   -0.0000      0.0012     12.0
    2.3596        16.0       10000     2.3585   -0.0011      0.0003     48.0
    3.9236         8.0       10000    -2.3594   +0.0003      0.0006     24.0
    0.0000         8.0       10000     0.0003   +0.0003      0.0006     24.0
   -1.5640         8.0       10000    -1.5637   +0.0003      0.0006     24.0

   Row 6 uses dphi_true = 3.9236 rad (> pi): the reconstruction returns
   -2.3596 rad, i.e. exactly the same number as a -2.3596 rad step.
   A single hologram cannot resolve the branch; a tilt series can (section 7).
   Row 7 is the no-step control; row 8 is the (666) double-bilayer value.

====================================================================================================
13.  TEST PLAN: NUMBERS A CORRECTED REPOSITORY MUST REPRODUCE (200 keV, a = 5.4309 A, V0 = 12 V)
====================================================================================================
   [PASS] T1  lambda(200 keV)                                        got       0.025079 A      want     0.025079 +/- 1e-06
   [PASS] T2  lambda(100 keV)                                        got       0.037014 A      want     0.037014 +/- 1e-06
   [PASS] T3  lambda(300 keV)                                        got       0.019687 A      want     0.019688 +/- 1e-06
   [PASS] T4  vacuum Bragg angle (666)                               got      23.997603 mrad   want    23.997600 +/- 0.001
   [PASS] T5  critical angle (V0=12 V)                               got       8.355968 mrad   want     8.356000 +/- 0.001
   [PASS] T6  external angle at the (666) internal condition         got      22.495315 mrad   want    22.495300 +/- 0.001
   [PASS] T7  |F(666)|/f  (must be 0)                                got       0.000000        want     0.000000 +/- 1e-09
   [PASS] T8  |F(444)|/f                                             got       8.000000        want     8.000000 +/- 1e-09
   [PASS] T9  |F(555)|/f                                             got       5.656854        want     5.656854 +/- 1e-09
   [PASS] T10 step phase (666), h = d_111, mod 2pi                   got       3.923572 rad    want     3.923600 +/- 0.002
   [PASS] T11 step phase (444), h = d_111, mod 2pi                   got       2.582006 rad    want     2.582000 +/- 0.002
   [PASS] T12 step phase (555), h = d_111, mod 2pi                   got       3.408765 rad    want     3.408800 +/- 0.002
   [PASS] T13 step phase (888), h = d_111, mod 2pi                   got       4.538584 rad    want     4.538600 +/- 0.002
   [PASS] T14 h_2pi at the (666) condition                           got       0.557482 A      want     0.557500 +/- 0.001
   [PASS] T15 (2,-2,0) reflection-geometry accessibility  (0=no, 1=yes) got       0.000000        want     0.000000 +/- 0.5
   [PASS] T16 exact G.R / 2pi for (2,-2,0) and a d_111 step (integer!) got       1.000000        want     1.000000 +/- 1e-09
   [PASS] T17 top-gap illumination reaching the surface (theta_ext)  got      31.104603 %      want    31.100000 +/- 0.05
   [PASS] T18 incident wave entering the front end face              got      80.890384 %      want    80.890000 +/- 0.05
   [PASS] T19 reflected-beam rise over the cell (must stay < x_vac)  got       4.460407 A      want     4.460400 +/- 0.001
   [PASS] T20 foreshortening 1/sin(theta_ext)                        got      44.457450        want    44.460000 +/- 0.02
   [PASS] T21 antialiased max angle at 0.13 A, 200 keV               got      64.306001 mrad   want    64.310000 +/- 0.02
   [PASS] T22 antialiased max angle at 0.50 A, 200 keV (too small for 24 mrad) got      16.719560 mrad   want    16.720000 +/- 0.02
   [PASS] T23 max tilt step for h = 1 nm (phase increment < pi)      got       0.626984 mrad   want     0.627000 +/- 0.001
   [PASS] T24 hologram round trip recovers the (666) single-step phase got       2.359698 rad    want     2.359613 +/- 0.005
   [PASS] T25 hologram round trip, no-step control                   got       0.000274 rad    want     0.000000 +/- 0.005

   25/25 checks pass in this script itself.

====================================================================================================
END OF OUTPUT
====================================================================================================
```

---

## Appendix B — source ledger

| ID | Item | Evidence label | Note |
|---|---|---|---|
| — | `h`, `c`, `e` (SI-2019 exact); `m_ec² = 510998.95000 eV` (CODATA 2018) | `NOT_FETCHED_HERE` | stated explicitly; one-step check against NIST CUU. All egress to standards sites blocked this session. |
| — | `λ = hc/√(T(T+2mc²))`; diamond structure factor; step-phase identity (2.1)–(2.3); refraction (3.1)–(3.5); `ρ`-form (3.4); accessibility rule (3.5); `h_2π` (3.6); tilt criterion (3.7); carrier rule (7.2); phase noise (7.3); all geometry/sampling numbers | `DERIVED_HERE` | premises stated in-line; all reproduced by the script; 25/25 self-checks pass. |
| — | `V0(Si) = 12.0 V` | **`ASSUMPTION`** | not verified in this session; full sensitivity given for 9–14 V. |
| — | Kruse, Schowalter, Lamoen, Rosenauer, Gerthsen, *Ultramicroscopy* **106**(2) 105–113 (2006), DOI `10.1016/j.ultramic.2005.06.057` | `METADATA_VERIFIED` (weak — search index only) | candidate source for `V0(Si)`; **no value taken from it**. |
| [B07] | Ichimiya & Cohen, *Reflection High-Energy Electron Diffraction*, CUP 2004 | `METADATA_VERIFIED` | library record only; **not read**; cited only as "the appropriate text for slices-parallel-to-surface RHEED theory". |
| [B08] | Peng, Dudarev & Whelan, *High-Energy Electron Diffraction and Microscopy*, OUP 2004 | `METADATA_VERIFIED` | library record only; **not read**. |
| [B06] | Kirkland, *Advanced Computing in Electron Microscopy*, 3rd ed., Springer 2020 | `METADATA_VERIFIED` | library record only; the 2/3 antialias rule is stated here as a standard rule, **not attributed to a page**. |
| [B09]/[C01]/[C02] | Völkl/Allard/Joy (eds.); Völkl & Lehmann; Dunin-Borkowski *et al.* | `METADATA_VERIFIED` | library records only; §7 derivations are `DERIVED_HERE`, not taken from them. |
| — | Peng & Cowley, *Acta Cryst.* A42 545–552 (1986) | **`UNVERIFIED`** | search-index provenance only; no method detail attributed. |
| — | Si inelastic mean free path "of order 10² nm at 200 keV" | **`UNVERIFIED`** | used only qualitatively (absorption cannot suppress 81 % end-face transmission over 8.5 nm). |
| — | Prismatic/prismatique antialias cutoff and tilt implementation | **`UNVERIFIED`** | must be read from the version-matched source (`prismatique==0.0.1`) before any quantitative claim. |
| — | All repository defaults in §0.4 | `PROJECT_INPUT` | read directly from the cloned code at commit `6694959`. |
