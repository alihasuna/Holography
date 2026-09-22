# C2: Phase 2 physics checks (a/4 step symmetry on Si(001), carrier-location trap, R2 twin)

Status: COMPLETE, 2026-09-22. Agent C2 (physics-deriver). Owned paths: this report and
`tools/physics_checks/`. No package, test, config or document file was edited. This agent committed
nothing; the orchestrator snapshotted in-progress versions of this report and of the Q1 script in
f5a2a00 and 7874c85 (not final).

## Inputs read

docs/physics_conventions.md (all); docs/03_physics_summary.md sections 2 and 6 (and 3, 7 for
context); docs/model_assumptions.md B4 and open question 3; docs/06_project_inputs_required.md
item 8; tools/reflection_step_phase_calculator.py (`screw_search`, `SpecularCondition`, section 4b,
`_sideband_wave`, `hologram_roundtrip`, checks T24/T25); docs/agent_reports/S1b (open issue 1, log
item 2); docs/agent_reports/S1c (log item 1-2, open issues 1-2); docs/agent_reports/C_physics_derivations.md
sections 2.3, 3.6 and 7 (the trap paragraph); reflection_holo/structure/si001.py and lattice.py,
reflection_holo/reconstruction/sideband.py, reflection_holo/optics/hologram.py and fields.py;
tests/reconstruction/holo_cases.py, test_carrier_trap.py, test_self_reference_R2.py. The quoted
document passages were re-checked on HEAD 7874c85 after concurrent commits by other agents (they
are unchanged; docs/06 item 11 and model_assumptions B11 to B14 are new and are taken into account);
all three scripts and the repository suite (`374 passed`) run on that tree.

Conventions (docs/physics_conventions.md): `exp(+i k.r)`; angular wavevectors in rad/A; glancing
angles to the surface plane; `n_hat` the outward normal; `Delta_phi = phi(upper) - phi(lower)`,
signed; numpy FFT sign (a wave `exp(+2 pi i q0.r)` appears at `+q0`). Beam energy 200 keV
(PROJECT_INPUT item 1). Crystal (cubic) axes are used for the symmetry work: outward normal
`[001]`; the package's slab frame is x = [001], z = beam azimuth, y = z x x.

No textbook passage was read for this report. Nothing below is attributed to a source; every
result is DERIVED_HERE from the stated premises and checked numerically, or REPRODUCED (an earlier
agent's number re-obtained by an independent script of this report).

## Scripts (all numpy only; `venv/bin/python tools/physics_checks/<name>.py`)

| Script | Question | Self-checks |
|---|---|---|
| `tools/physics_checks/q1_si001_quarter_step_symmetry.py` | 1 (a/4 step symmetry, amplitudes, reconstruction caveat, step phases) | 41/41 pass (about 20 s) |
| `tools/physics_checks/q2_carrier_trap.py` | 2 (carrier-location trap) | 21/21 pass (about 2 s) |
| `tools/physics_checks/q3_r2_twin.py` | 3 (R2 twin) | 7/7 pass (about 1 s) |

## 1. The a/4 single-layer step on bulk-terminated Si(001)

### 1.1 Premises, conventions, validity

* P1 Bulk-terminated, unrelaxed terraces (ASSUMPTION B3). Terrace N is the half crystal
  `H_N = {diamond sites n : n3 <= N}` (integer a/4 coordinates, `z = n3 a/4`, outward normal
  `[001]`). An a/4 up-step joins the lower terrace `H_0` (top layer on the even, fcc sublattice:
  top-layer back-bonds project on `[1-10]`) to the upper terrace `H_1` (odd sublattice, back-bonds
  on `[110]`); both are truncations of one lattice (the builder's rule).
* P2 Each terrace is laterally infinite and semi-infinite: the statements are about the terrace
  amplitude far from the riser (B4), not about the riser region or the shadow.
* P3 The scattering potential of a terrace (including an absorptive part and thermal averaging) has
  every symmetry of its atomic arrangement.
* P4 Elastic scattering of a monochromatic plane wave; reflection amplitudes `A(k_in -> k_out)` are
  coefficients of vacuum plane waves `exp(+i k.r)`; no magnetic field in the scattering region (the
  objective-lens field at the specimen is outside every model in this repository).
* P5 (used only where marked "reciprocity"): `A(k -> k') = A(-k' -> -k)` for the specular beam,
  from the symmetry `G(r, r') = G(r', r)` of the Green's function of a local, possibly complex
  potential. Checked on the toy model (check H2), not taken from a source.
* Crystal axes, origin on a top-layer atom of `H_0`; azimuth angle `phi` in the (001) plane from
  `[100]` towards `[010]`. `k_in = k(cos(theta) b_hat - sin(theta) n_hat)`,
  `k_out = k(cos(theta) b_hat + sin(theta) n_hat)` for the specular beam at azimuth `b_hat`.

### 1.2 Exhaustive search on the truncated half crystals (script sections A to D, G)

Method. All 48 point operations `M` of m-3m (signed permutation matrices, checked to form a group).
Translations are enumerated exhaustively rather than on a grid: if `S r = M r + t` maps `H_0` onto
`H_1`, the image of a fixed top-layer atom `p0` of `H_0` is an atom `q` of `H_1`, so
`t = q - M p0` with `q` running over every atom of `H_1` in a window larger than one surface-net
cell and eight layers deep (15 456 candidates for `H_0 -> H_1`). Each candidate is tested on the
atoms of both truncated half crystals, in both directions (`S(P_0)` inside `H_1` and `S^-1(P_1)`
inside `H_0`, patches of 33 x 33 a/4 in plane and 17 layers deep), and the successes are reduced
modulo the (001) surface net. Bulk-basis membership in Fd-3m is tested separately.

Result (script output, excerpt; the lines containing `...` are condensed, the full output is in
appendix A.1):

```
   a/4 up-step: lower H_0 -> upper H_1: 15456 (M, t) candidates tested (p0 = [0, 0, 0]); 128 succeed, 4 class(es) modulo the surface net:
       4+[0,0,1]  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
       4-[0,0,1]  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
        m(0,1,0)  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
        m(1,0,0)  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
   self-symmetry of the lower terrace H_0: 15888 (M, t) candidates tested (p0 = [0, 0, 0]); 164 succeed, 4 class(es) modulo the surface net:
               1  t = (a/4)*[0, 0, 0] ...    2[0,0,1] ...    m(1,-1,0) ...    m(1,1,0) ...   (all t = 0, t_z = 0)
   a/2 up-step: H_0 -> H_2: ... 1  t = (a/4)*[-2, 0, 2] (a pure lattice translation), 2[0,0,1], m(1,-1,0), m(1,1,0)
   Bulk versus half crystal: all 48 point operations are Fd-3m elements with a suitable translation; 40 of them do not fix [001] and map no half crystal onto another; of the 8 that fix [001], only the 4 of the non-Td coset reach t_z = a/4.
   m(0,1,0): glide reflection (no pure mirror exists: every glide vector has an in-plane component). Plane normal [0.0, 1.0, 0.0], the plane contains [001] and [1.0, -0.0, -0.0].
      plane offset u.r (units of a, mod a/2) | in-plane glide component along the plane (units of a, mod a) | glide component along [001] (units of a)
          0.1250 |    +0.2500 |  +0.2500
          0.3750 |    -0.2500 |  +0.2500
   m(1,0,0): glide reflection ... Plane normal [1.0, 0.0, 0.0], the plane contains [001] and [0.0, 1.0, 0.0].
          0.1250 |    +0.2500 |  +0.2500
          0.3750 |    -0.2500 |  +0.2500
   4-[0,0,1]: 4_3 screw (rotation -90 deg, +a/4 == 4_3^3); axis parallel to [001] through (x, y) = [-0.25, 0.0] a  (all axis positions modulo a/2: [(0.25, 0.0)]); translation along the axis = a/4 = 1.357725 A
   4+[0,0,1]: 4_1 screw (rotation +90 deg, +a/4); axis parallel to [001] through (x, y) = [0.0, -0.25] a  (all axis positions modulo a/2: [(0.0, 0.25)]); translation along the axis = a/4 = 1.357725 A
   [PASS] C1 H_0 -> H_1: exactly 4 classes: 4+[0,0,1], 4-[0,0,1], m(1,0,0), m(0,1,0)
   [PASS] C2 H_0 -> H_1: no pure translation (identity absent)
   [PASS] C3 H_0 -> H_1: no diagonal mirror m(1,1,0) or m(1,-1,0) and no 2-fold
   [PASS] C4 every H_0 -> H_1 operation has t_z = a/4 exactly
   [PASS] C7 H_0 self-symmetry point group = {1, 2[001], m(1,1,0), m(1,-1,0)} (2mm, diagonal mirrors)
   [PASS] D1 both <100> glides: planes at a/8 and 3a/8 (mod a/2) from the atom row, glide (+-a/4 in plane, a/4 along [001]); no zero in-plane glide
   [PASS] D2 glide component along the outward normal = a/4 = h (the step height)
   [PASS] G1 package relation finder: same four operations as the exhaustive search, and the incidence-plane glide exactly at [100] ((010)) and [010] ((100)), none at [110]
```

Why exactly these four (DERIVED_HERE, confirmed by checks B2, B3, C1 to C4). An isometry mapping a
half crystal `z <= c` onto a half crystal `z <= c'` must fix the outward normal, which leaves the
8 operations of 4mm. For every point operation of m-3m exactly one translation coset makes it a
symmetry of diamond: the fcc lattice for the 24 operations of -43m (Td, the site symmetry of the
atom at the origin) and `(a/4)(1,1,1) + fcc` for the other 24. Of the 8 operations of 4mm, the four
in Td (1, 2[001], m(110), m(1-10)) therefore have `t_z` in `(a/2) Z` and give only a/2 (and 0)
relations; the other four (4+[001], 4-[001], m(100), m(010)) have `t_z` in `a/4 + (a/2) Z` and are
exactly the a/4-step relations. A search on the bulk basis alone finds all 48 operations; the
half-crystal test removes 44 of them for the a/4 step.

**The operation.** The structure agent's claim (S1b open issue 1) is VERIFIED (DERIVED_HERE by
exhaustive enumeration on the truncated half crystals; cross-checked on atoms built by the package,
check G1). At beam azimuth `[100]` the terraces are related by the d-glide of Fd-3m whose plane is
(010), i.e. contains the beam `[100]` and the normal `[001]`:

* plane `y = a/8 + m a/4` (origin on a top-layer atom of the lower terrace; the planes lie a/8 from
  the nearest (010) atomic planes and contain no atom);
* glide vector `(+a/4, 0, +a/4)` on the planes `y = a/8 (mod a/2)` and `(-a/4, 0, +a/4)` on
  `y = 3a/8 (mod a/2)`: the in-plane component is `+-a/4` along the beam, never zero modulo the
  period a along `[100]`, so there is no pure mirror;
* the component along the outward normal is exactly `+a/4 = h = 1.357725 A`, the step height.
  In the package's slab frame at `[100]` (x = `[001]`, y = `[0,-1,0]`, z = `[100]`) the plane is
  `y_slab = const` and the glide vector is `(x, z) = (a/4, +-a/4)`.

At `[010]` the corresponding glide has plane (100) and vector `(0, +-a/4, a/4)`. The same two
glides and the 4_1 (rotation +90 degrees, +a/4) and 4_3^3 (rotation -90 degrees, +a/4) screws
relate the other terrace pair `H_1 -> H_2` (check C6). At `[110]` the plane containing the beam and
the normal is (1-10); m(1-10) is in Td, so its translations have `t_z` in `(a/2) Z`: it maps each
terrace onto itself or onto the a/2-shifted one, never across an a/4 step. **At `[110]` no
operation of any kind relates the two terraces while fixing the beam** (checks E3, G1).

### 1.3 What the symmetry implies for the specular (00)-rod amplitudes

Covariance (DERIVED_HERE, exact to all orders of scattering under P3, P4). Let the upper terrace be
`S(lower)`, `S r = M r + t`, so `V_up(r) = V_low(S^-1 r)`. If `psi_low(r; k')` is the scattering
state of the lower terrace for the incident wave `exp(i k'.r)`, then `psi_low(S^-1 r; k')` solves
the upper terrace's problem (the Laplacian is invariant under isometries) with incident part
`exp(i k'.M^T(r - t)) = exp(-i (M k').t) exp(i (M k').r)`. Choosing `k' = M^T k_in`, multiplying by
`exp(+i k_in.t)` and reading off the outgoing wave `exp(i k_out.r)` gives

```
A_up(k_in -> k_out) = exp(-i (k_out - k_in).t) A_low(M^T k_in -> M^T k_out).          (1.1)
```

Check H1 confirms (1.1), including the sign of the exponent in the `exp(+i k.r)` convention, on a
strongly multiple-scattering toy (Foldy-Lax point scatterers, `|f - f_Born|/|f_Born| = 1.92`):
maximum relative residual `1.64e-14`.

**Exact `[100]` azimuth.** The (010) glide has `M^T k_in = k_in` and `M^T k_out = k_out` for every
glancing angle (check E5: `max |M^T k - k| = 0` at the (008) condition), so

```
A_up = exp(-i (k_out - k_in).t) A_low,   (k_out - k_in).t = 2 k sin(theta_ext) t_z = 2 k sin(theta_ext) a/4,
Delta_phi = arg A_up - arg A_low = -(4 pi/lambda)(a/4) sin(theta_ext)   (mod 2 pi),   |A_up| = |A_low|.
```

The in-plane glide component drops out because `k_out - k_in` is parallel to `n_hat` (check E6).
Yes: the two complex amplitudes are equal up to the geometric phase `exp(-i (k_out - k_in).t)`, to
all orders, with absorption. Writing each amplitude as `|A| exp(i[phi_R - (k_out - k_in).n_hat z_top])`
with `phi_R` the dynamical reflection phase referred to the terrace's own top-layer plane, the
residual `delta_[100] = phi_R,up - phi_R,low = 0` exactly. The same conclusion follows from the (100)
glide combined with reciprocity (P5), and, equivalently, from the 4_1 screw (terrace B at `phi`
behaves like terrace A at `phi - 90 deg`, C report section 2.3) followed by the lower terrace's own
diagonal mirror and 2-fold axis, which bring `phi - 90 deg` back to `-phi`, i.e. to `phi` itself at
`phi = 0` (check F1). Toy confirmation: check H4, ratio `1.000000000000 + 0.000000000000 i`.

**Exact `[110]` azimuth.** No operation preserves `k_in, k_out` directly or via reciprocity (E3,
F1). All four relations give, via (1.1), `A_up(k at [110]) = exp(-i q.t) A_low(k at [1-10])` (toy
check H7: `1.9e-15`), and the lower terrace's own symmetries plus reciprocity connect `[1-10]` only
with `[-110]`, never with `[110]` (F1: the orbit of 45 degrees is {45, 225}, the four images are at
{135, 315}). Hence

```
Delta_phi_[110] = -(4 pi/lambda)(a/4) sin(theta_ext) + delta_[110](theta),
delta_[110] = phi_R,P(theta) - phi_R,T(theta)   (upper terrace P, lower terrace T),
```

where P and T are the terrace types whose top-layer back-bonds are parallel and transverse to the
beam azimuth (the lower terrace `H_0` is T at `[110]`, the upper `H_1` is P; the sign reverses for a
T terrace above a P terrace). The moduli differ as well. `delta_[110]` is the residual that only a
dynamical calculation can supply. Its properties (DERIVED_HERE):

* it vanishes in the first Born (kinematic) approximation: the Born specular amplitude depends only
  on the laterally averaged potential, which is the same for both terraces up to the a/4 shift
  (toy check H6: ratio 1 to `1e-12`), and for the same reason in any one-beam dynamical treatment
  that keeps only the laterally averaged potential;
* it is generally nonzero once the specular beam couples to non-specular beams, i.e. in a many-beam
  calculation (toy check H5; the toy's value `|ratio| = 0.95`, phase `-3.0 rad` has no physical
  meaning: toy k, f0 and cluster);
* along a monotonic staircase of a/4 steps the terrace types alternate, so successive step phases
  alternate between `-qh + delta` and `-qh - delta` and every pair of a/4 steps (an a/2 step, a pure
  translation) is clean. Two successive single steps imaged under the same conditions therefore differ by `2 delta` (mod 2 pi).

**Small azimuthal misalignment `epsilon` from `[100]`.** The (010) glide maps the azimuth `+epsilon`
onto `-epsilon`, so (1.1) gives `A_up(epsilon) = exp(-i q.t) A_low(-epsilon)` (all four relations
agree, check F1), and

```
delta(epsilon) = phi_R,low(-epsilon) - phi_R,low(+epsilon)   (odd in epsilon, delta(0) = 0).
```

The (010) plane is not a mirror plane of either terrace (their mirrors are the diagonal ones, C7),
so nothing forces `phi_R,low` to be even about `[100]`: `delta` is generically of first order,
`delta ~ -2 epsilon d(phi_R,low)/d(phi)` at `phi = 0`, and `|A_up|/|A_low| - 1` is first order too.
Toy confirmation: `delta(-epsilon) = -delta(epsilon)` to `1e-9` and
`delta(0.3 deg)/delta(0.1 deg) = 3.0094` (checks H8, H9; the toy's slope, 0.78 rad per degree, is not
physical). The slope at the working angle needs a dynamical calculation. The glancing angle itself
is free: the relation holds at every `theta` as long as the azimuth is exact. For an illumination
with a spread of azimuths the partial waves at `+epsilon` and `-epsilon` exchange roles between the
terraces; whether the ensemble-averaged sideband keeps the exact relation depends on the parity of
the tilt-dependent illumination and reference phases at the image point and is NOT analysed here
(B10, PROJECT_INPUT item 3).

**Other rods.** At `[100]` the relation is rod-by-rod only for rods in the incidence plane: a rod
`G_par = p (4 pi/a)[100]` carries the extra factor `exp(-i G_par.t_par) = (-1)^p` (check E8), while a
zeroth-Laue-zone rod `G` perpendicular to the beam on one terrace is related to the rod `-G` on the
other. Which beam the aperture selects is PROJECT_INPUT item 4.

Step phases of the clean `[100]` case (script section J; 200 keV, `V0 = 12 V` ASSUMPTION B1,
internal Bragg conditions of the (00L) rod; the phases equal the calculator's section 4b):

```
       (00L)  th_ext mrad  dphi = -2 K_ext a/4   wrapped  h_2pi (A)  dh per 0.1 rad of residual (A)
   (0, 0, 4)       3.9344              -2.6766   -2.6766     3.1872                          0.0507
   (0, 0, 8)      16.4743             -11.2071    1.3593     0.7612                          0.0121
   (0, 0, 12)      26.4205             -17.9720    0.8776     0.4747                          0.0076
   (0, 0, 16)      35.9936             -24.4814    0.6513     0.3485                          0.0055
```

The last column is the height error that an unmodelled residual of 0.1 rad would cause at `[110]`
(`dh = 0.1/(2 K_ext)`), for scale only: `delta_[110]` itself is unknown.

Side finding (check J1, J1b). The definition `Delta = (k_int^2 - k_ext^2)/k_ext^2` in
`docs/physics_conventions.md` is exact, but the closed form given there and in docs/03 section 3,
`Delta = V0 (1 + T/(m c^2)) / (T (1 + T/(2 m c^2)))`, is first order in `V0`; the exact closed form,
used by the calculator, is `Delta = U (2T + U + 2 E0)/(T (T + 2 E0))` (U = e V0, E0 = m c^2). They differ by
the relative amount `U/(2T + U + 2E0) = 8.439e-06` at 200 keV and 12 V, which changes `K_ext` by at
most `1.90e-05` (relative, at (004)) and the a/4 step phase by at most `5.09e-05 rad`. Negligible,
but the conventions line should say "to first order in V0" or give the exact form.

### 1.4 The reconstruction caveat (script section I)

This is a symmetry derivation for the bulk-terminated surface only. **A 2x1 reconstruction, which
is not modelled, can break it.** The relation is guaranteed by symmetry only if the upper
terrace's reconstruction is the image of the lower terrace's reconstruction under one of the two
<100> glides, up to an in-plane translation (which leaves the (00) amplitude unchanged); otherwise
the two amplitudes generically differ. A symmetry-only toy (TEST_ONLY
displacements; no dimer geometry has been sourced) takes the four Fd-3m images of a dimerised
lower terrace as the possible upper-terrace domains and searches for a `[100]`-compatible operation
(1 or m(010) directly; m(100) or 2[001] via reciprocity). Condensed from appendix A.1, section I:

```
   symmetric dimers:              every variant: ['m(0,1,0)', 'm(1,0,0)']
   buckled dimers p(2x1):         4+ image: ['m(1,0,0)']; 4- image: ['m(0,1,0)']; m(0,1,0) image: ['m(0,1,0)']; m(1,0,0) image: ['m(1,0,0)']
   twisted dimers (toy only):     4+ image: NONE; 4- image: NONE; m(0,1,0) image: both; m(1,0,0) image: both
   [PASS] I1 ... [PASS] I4   (no [110]-compatible operation for any toy or variant)
```

Coset argument (DERIVED_HERE, consistent with every toy result): the four upper-terrace variants
`S(X)` (`S` = 4_1, 4_3^3, (100) glide, (010) glide; `X` the reconstructed lower terrace) coincide in
pairs or all together according to the symmetry group K of `X` modulo in-plane translations. If K
contains one of the terrace's diagonal mirror (or glide) planes, the variants pair up as
{4_1, one <100> glide} and {4_3^3, the other <100> glide} (for m(1-10): 4+ with m(100), 4- with
m(010); for m(110) the other way round), so every variant has a <100> glide and the (00) relation
survives, for one of the pairs only through reciprocity P5. If K contains neither diagonal plane
(the twisted-dimer toy keeps only 2[001]), the screw variants have no [100]-compatible operation
and the relation is broken for them. The symmetric-dimer toy keeps both diagonal mirrors, the
buckled p(2x1) toy keeps the one containing the dimer bond; the twisted-dimer toy is a symmetry
probe, not a proposed Si(001) structure. Real dimer geometry, buckling order, dimer
flipping, domain populations, step-edge structure and the oxide/damage overlayer of the ion-milled
surface (B7; no crystal symmetry at all) are outside this derivation.

### 1.5 Conclusions for B4, open question 3 and item 8 (labels)

* At an exact <100> azimuth the bulk-terminated a/4 step is a clean geometric-phase step:
  `Delta_phi = -(4 pi/lambda)(a/4) sin(theta_ext)` exactly, dynamical scattering and absorption
  included (DERIVED_HERE, checks C1 to C8, D1, D2, E1 to E6, F1, G1, H1 to H4).
* At <110> (and at every azimuth other than <100>) the a/4 step phase contains the dynamical
  residual `delta_[110] = phi_R,P - phi_R,T`, zero kinematically and in a one-beam treatment; its
  value is UNKNOWN until a many-beam dynamical calculation is done (DERIVED_HERE for its existence
  and properties).
* An azimuthal misalignment `epsilon` from <100> gives a residual odd and generically first order in
  `epsilon` (DERIVED_HERE); its slope is unknown.
* The a/2 step is a pure translation and clean at every azimuth (check C8; unchanged).
* PROJECT_INPUT item 8 therefore decides whether a/4 steps are quantitative without a dynamical
  calculation: `[100]`/`[010]` yes for bulk-terminated terraces, `[110]` no.
* The clause added to item 11 on the current HEAD (which terrace type lies on which side of an a/4
  step) matters only away from <100>: at <110> it fixes the sign of `delta_[110]`; at an exact <100>
  azimuth the two bulk-terminated types reflect identically and the clause is not needed.
* The package's builder records `model_assumption_B4 = "does NOT apply (4_1 screw-related terraces)"`
  for every a/4 step (si001.py, step metadata). At a <100> azimuth this should become "applies for
  bulk-terminated terraces at the exact azimuth (d-glide in the incidence plane, C2)". Not edited.

### 1.6 Proposed wording (not applied)

docs/03 section 2, premise paragraph, replacing "NOT true for a Si(001) single-layer step `h = a/4`,
whose terraces are related by the diamond `4_1` screw operation and therefore have different
complex reflectivities at a general azimuth":

> NOT true for a Si(001) single-layer step `h = a/4`: its terraces are related by the 4_1 and 4_3
> screws and by the two <100> d-glides of Fd-3m, never by a translation (C2). At an exact <100>
> beam azimuth the d-glide whose plane contains the beam and the normal (plane (010) for `[100]`,
> glide vector `(a/4)[+-1,0,1]`, normal component a/4) leaves `k_in` and `k_out` unchanged, so for
> bulk-terminated terraces the complex reflectivities are equal up to `exp(-i (k_out - k_in).t)` and
> the step phase is exactly `-(4 pi/lambda)(a/4) sin(theta_ext)`. At a <110> azimuth no such
> operation exists: the terraces are the two types with top-layer back-bonds parallel (P) and
> transverse (T) to the beam, and the step phase contains a dynamical residual
> `delta = phi_R,P - phi_R,T` that vanishes kinematically and must be computed. A 2x1
> reconstruction (not modelled) can break the <100> result.

model_assumptions B4 (whole row):

> | B4 | Two terraces separated by a lattice-translation step, or by a bulk-terminated Si(001) a/4
> step viewed at an exact <100> azimuth (terraces related by the d-glide whose plane contains the
> beam and the normal; C2), have identical complex reflectivity up to `exp(-i (k_out - k_in).t)`,
> so the dynamical reflection phase cancels. | DERIVED_HERE | Exact for infinite terraces of a
> perfect crystal. Violated near the riser; for Si(001) a/4 steps at <110> and at any azimuth other
> than <100> (residual `delta = phi_R,P - phi_R,T`, zero kinematically, alternating in sign along a
> staircase); to first order in an azimuthal misalignment from <100> (the residual is odd in the
> misalignment); for reconstructed terraces whose upper-terrace domain is not a <100>-glide image of
> the lower one (a 2x1 reconstruction can break it; not modelled); for strained terraces and for any
> overlayer. |

model_assumptions open question 3:

> 3. How large is the dynamical reflection phase difference `delta(theta) = phi_R,P - phi_R,T`
> between the two terrace types of an Si(001) single-layer step at a <110> azimuth, and how fast does
> the residual grow with an azimuthal misalignment from <100>? At an exact <100> azimuth it is zero
> by symmetry for bulk-terminated terraces (C2); the kinematic and one-beam approximations give zero
> at every azimuth. Only a many-beam dynamical calculation (and, for real surfaces, the
> reconstruction and overlayer) can answer this.

docs/06 item 8:

> 8. (blocking) Beam azimuth relative to the surface net (for Si(001): [110] or [100]; for Si(111):
> [1-10] or [11-2]) and the accuracy of the azimuthal alignment. For Si(001) single-layer (a/4)
> steps a <100> azimuth makes the bulk-terminated step a clean geometric-phase step (C2); at <110>
> the step phase contains the dynamical residual of open question 3, alternating in sign between
> successive a/4 steps. The a/2 step is clean at every azimuth.

## 2. The carrier-location trap (docs/03 section 6; S1c open issue 1)

### 2.1 Premises and setup

The calculator's `hologram_roundtrip` exactly (T24 case), rebuilt from the calculator's own
functions and, separately, through the package chain (the two holograms and phase maps agree to
0.0, checks Q2-D1, Q2-D1b): 512 x 512 px, reference `u_r = exp(2 pi i x/8)` along axis 1, object
`u_o = exp(i Delta s(y))` with `s = 0.5 (1 + tanh((y - 256)/2))` and
`Delta = sc666.step_phase(d111)['wrapped'] = 2.359613 rad`, Hann aperture of radius `q_c/3`,
terrace medians with a 72 px pad. Bins are written `(k_y, k_x)` in cycles per field (the carrier is
`k_x = +-64`) and as the calculator's fftshifted indices `(256 + k_y, 256 + k_x)`. With the numpy
FFT sign, `I = 2 + u_o u_r^* + u_o^* u_r`: the sideband at `-q_c` (`k_x = -64`) holds
`phi_o - phi_r` (correct), the one at `+q_c` holds `phi_r - phi_o` (conjugate). Pixel size 1 A,
TEST_ONLY.

### 2.2 Derivation (DERIVED_HERE)

1. Because the fringe period divides the field (64 cycles), the sideband at `k_x = -64` is exactly
   the 1-D DFT along y of `exp(+i Delta s(y))`, and the one at `+64` that of `exp(-i Delta s(y))`.
   For any real hologram, noisy or not, `F(-q) = F(q)^*`: every bin has an exactly equal partner
   at `-q` in the other sideband.
2. For a sharp 50/50 step, `exp(i Delta s) = (1 + e^{i Delta})/2 + ((e^{i Delta} - 1)/2) sq(y)` with
   `sq = +-1`, whose Fourier coefficients vanish at even orders and have modulus `2/(pi |k|)` at odd
   `k`. The carrier bin has modulus `|cos(Delta/2)|`, the first harmonics `k_y = +-1` have
   `(2/pi)|sin(Delta/2)|`. The harmonic is brighter than the carrier when `|tan(Delta/2)| > pi/2`,
   i.e. `2 arctan(pi/2) = 2.0078 rad < |Delta| < 4.2754 rad` (mod 2 pi). At `Delta = 2.3596` the ratio
   is 1.5444 (sharp model) and 1.5377 in the calculator's hologram (check Q2-B1); the threshold is
   confirmed numerically to within 0.03 rad (Q2-C1).
3. For the sharp step the four first-harmonic bins (`k_y = +-1` in each sideband) are exactly equal
   (relative spread 1.9e-16, Q2-B2). The tanh edge (where `0 < s < 1`, `exp(i Delta s)` is not affine
   in `s`) splits them into two Hermitian pairs 1.56 % apart; the brighter pair is
   `{(-1, +64), (+1, -64)}` (Q2-B3), and its two members are exactly equal (difference 0.0, noiseless
   and at dose 1e4, Q2-A3).
4. The calculator takes `argmax` over the fftshifted array, which meets row 255 (`k_y = -1`) before
   row 257: it returns `(-1, +64)` = fftshifted (255, 320), the member in the CONJUGATE sideband
   (Q2-A1). numpy's unshifted order would return the other member, (1, 448) = `(+1, -64)` (Q2-B4).
   Which pair wins is set by the edge profile; which member, and therefore which sideband and sign,
   is set by array order.
5. Recentring on `(-1, +64)` gives the conjugate content times a one-bin ramp,
   `exp(-i Delta s(y)) exp(+2 pi i y/512)`. The ramp is worth `2 pi x 256/512 = pi` between the
   terrace medians (rows 127.5 and 383.5; Q2-A10), so the step is `-Delta + pi = +0.7820 rad`
   (Q2-A4; +0.7815 at dose 1e4, seed 12345, Q2-A5). The partner gives `Delta - pi = -0.7820`
   (Q2-A6). A ramp alone on the correct sideband gives `Delta +- pi = -0.7820` in either direction
   (Q2-A8): the magnitude 0.78 = pi - 2.36 comes from the ramp and the positive sign from the
   conjugate sideband. Dividing by the empty hologram demodulated at the same wrong bin cancels the
   ramp and leaves `-Delta = -2.3596` (Q2-A7). General rule, off-carrier cases whose terrace windows
   do not wrap: step = `sigma Delta + rho pi` with `sigma = -1` on the conjugate sideband and
   `rho = -k_y` (Q2-C2; e.g. `Delta = -2.3596` gives +0.7820 through the correct sideband, and
   `Delta = 2.04` and 2.10 give corrupted medians because the ramp wraps inside a window).

### 2.3 Script output (excerpt, `tools/physics_checks/q2_carrier_trap.py`, 21/21 checks pass)

```
   |F| at the carrier bins (k_y, k_x) = (0, -64): 1.011215e+05   (0, +64): 1.011215e+05
   |F| at first-harmonic bin (-1, +64) [fftshifted (255, 320)]: 1.554943692e+05
   |F| at first-harmonic bin (+1, -64) [fftshifted (257, 192)]: 1.554943692e+05
   |F| at first-harmonic bin (+1, +64) [fftshifted (257, 320)]: 1.530622443e+05
   |F| at first-harmonic bin (-1, -64) [fftshifted (255, 192)]: 1.530622443e+05
   calculator brightest object bin (fftshifted): (255, 320) -> (k_y, k_x) = (-1, +64): CONJUGATE sideband (+q_c), 1 row(s) off the carrier
   calculator brightest EMPTY-hologram bin: (256, 192)
   recentre on the brightest object bin, no division (the first version):  step = +0.7820 rad
   its Hermitian partner (257, 192), no division:                   step = -0.7820 rad
   brightest object bin, object/empty both demodulated there:           step = -2.3596 rad
   correct sideband one row off, (257, 192) / (255, 192), no division:  step = -0.7820 / -0.7820 rad
   correct path: carrier (256, 192) from the empty hologram, divided:   step = +2.3596 rad
   ramp term: pad = 72 px; median rows of the terrace interiors 127.5 and 383.5 (separation 256 rows); one-bin ramp 2 pi/512 rad per row -> 3.141593 rad between the medians (pi = 3.141593)
   sharp 50/50 model: |first harmonic| / |carrier| = (2/pi) |tan(Delta/2)| = 1.5444; calculator hologram (tanh edge): 1.5377
   sharp step: the four first-harmonic |F| = [154292.5111495739, 154292.5111495739, 154292.51114957393, 154292.51114957393]; relative spread 1.9e-16; calculator picks (255, 192)
   argmax in numpy's unshifted order picks unshifted bin (1, 448) = (k_y, k_x) = (+1, -64); the calculator (fftshifted order) picks (255, 320) = (-1, +64)
   sharp-step prediction: |Delta| > 2 arctan(pi/2) = 2.0078 rad (and < 2 pi - that = 4.2754 rad)
   Delta = +1.9800 (wrapped +1.9800): brightest bin (k_y, k_x) = (+0, -64) carrier (predicted carrier); naive step +1.9800 rad; no ramp
   Delta = +2.0400 (wrapped +2.0400): brightest bin (k_y, k_x) = (-1, +64) OFF carrier (predicted OFF); naive step +0.8808 rad; ramp wraps inside a terrace window: the median is corrupted
   Delta = +2.3596 (wrapped +2.3596): brightest bin (k_y, k_x) = (-1, +64) OFF carrier (predicted OFF); naive step +0.7820 rad; model sigma*Delta + rho*pi = +0.7820
   Delta = -2.3596 (wrapped -2.3596): brightest bin (k_y, k_x) = (-1, -64) OFF carrier (predicted OFF); naive step +0.7820 rad; model sigma*Delta + rho*pi = +0.7820
   package phase map at bin (511, 64) vs calculator _sideband_wave at (255, 320): max |difference| = 0.0e+00 rad (mask radius 0.041672 vs 0.041672 cycles/px)
   whole-plane search on the OBJECT hologram (allowed only for demonstration): bin (511, 64), CONJUGATE: phi_r - phi_o (sideband at +q_ref); step +0.7820 rad
   search restricted to the correct sideband, on the OBJECT hologram: bin (1, 448), phi_o - phi_r (sideband at -q_ref); step -0.7820 rad
   carrier located on the EMPTY hologram (correct sideband), divided: bin (0, 448), phi_o - phi_r (sideband at -q_ref); step +2.3596 rad
```

### 2.4 Conclusion and label

S1c's finding is VERIFIED (numbers REPRODUCED by an independent script; mechanism DERIVED_HERE):
0.78 rad is `-2.3596 + pi`, the conjugate sideband plus a one-bin ramp, and its sign is an argmax
tie-break outcome. One refinement: the tie that the tie-break resolves is exact only within a
Hermitian pair (always exact for a real hologram); which of the two pairs is brightest is decided by
the smoothed edge (1.56 %), and for a perfectly sharp 50/50 step all four harmonics tie and the
calculator's order would have picked the correct sideband, giving -0.78 rad. docs/03 section 6
("recentring on it produced a plausible but wrong step") describes the ramp only; the calculator
docstring and C report section 7 say the same ("injects a spurious phase ramp"); both omit the sign
inversion.

**Mechanism in one sentence:** the brightest off-centre bin of the object hologram is a first
harmonic of the 50/50 terrace pattern, one Fourier bin from the carrier along the step normal (it
outshines the carrier bin whenever `|tan(Delta/2)| > pi/2`, i.e. `|Delta| > 2.008 rad`), it comes as
an exactly equal Hermitian pair with one bin in each sideband, and the calculator's argmax
tie-break returned the member in the conjugate sideband, so recentring on it inverted the sign of
the step and added a one-bin ramp worth pi between the terrace medians: `-2.36 + pi = +0.78 rad`
instead of `+2.36 rad` (the other member gives -0.78 rad).

### 2.5 Proposed wording (not applied)

docs/03 section 6, replacing the "Processing trap" bullet:

> * Processing trap verified in the calculator (check T24, section 12 of its output) and in the
>   package (S1c, C2): for a 50/50 phase step of 2.36 rad the brightest off-centre Fourier bin of the
>   object hologram is not the carrier but a first harmonic of the terrace pattern, one bin off the
>   carrier along the step normal (for a sharp 50/50 step this happens whenever
>   `|Delta| > 2 arctan(pi/2) = 2.008 rad`), and it comes as an exactly equal Hermitian pair, one bin
>   in each sideband. The calculator's argmax returned the member in the conjugate sideband, so
>   recentring on it inverted the sign of the step and added a one-bin ramp worth pi between the
>   terrace medians: 0.78 rad = -2.36 + pi instead of 2.36 rad (the other member gives -0.78 rad).
>   The carrier must be located on an empty hologram or on the sideband envelope, inside a search
>   region that contains only the `phi_o - phi_r` sideband; which sideband that is for experimental
>   data is a declared input (PROJECT_INPUT items 10, 16, 19). The code audit found the same defect
>   in the inspected repository's `find_peak` (A report, C3).

model_assumptions: no existing row covers carrier location. If a row is wanted (the next free
number is B15):

> | B15 | The carrier is located on an empty or flat-region hologram, inside a search region that
> contains only the `phi_o - phi_r` sideband; for experimental holograms which sideband that is is a
> declared input (items 10, 16, 19). | DERIVED_HERE | A brightest-bin search on an object hologram,
> or over both sidebands, is refused: first harmonics of a 50/50 step beat the carrier when
> `|Delta| > 2.008 rad`, and between Hermitian partners the result depends on array order; the
> calculator's 0.78 rad for a 2.36 rad step is this error (C2 question 2; S1c). |

## 3. The R2 self-reference twin (docs/03 section 6; S1c open issue 2)

### 3.1 Premises

* The package's R2 model (`reference_r2_self_reference`; ASSUMPTION B5, R2 reading of P01
  DERIVED_HERE, SM22): `u_r(r) = c u_o(r + s) exp(i (2 pi q_c.r + phi_rel))`, `s` = `shift_A`.
  The overlap is a pure translation: no optical element inverts either partial image (the
  laboratory's arrangement is PROJECT_INPUT items 15 and 16).
* The carrier is located on a flat-region hologram; conventions as in section 2 (the `-q_c`
  sideband holds `u_o u_r^*`). Synthetic grid TEST_ONLY (512 x 512, 1 A pixels, carrier
  `(0, 1/8)` cycles/A, Hann mask `|q_c|/3`, resolution 24 px, interior at least 72 px from the field
  edge and from the band where the reference source lies outside the field).

### 3.2 Derivation (DERIVED_HERE)

```
I = |u_o|^2 + |u_r|^2 + u_o u_r^* + u_o^* u_r,
u_o u_r^* = c |u_o(r)| |u_o(r + s)| exp(i [phi(r) - phi(r + s) - phi_rel]) exp(-2 pi i q_c.r),
Phi(r) = phi(r) - phi(r + s) - phi_rel,     amplitude c |u_o(r)| |u_o(r + s)|     (band-limited by the mask).
```

A feature `f` centred at `r0` on a flat background gives `Phi(r) = f(r - r0) - f(r - (r0 - s))`:
the feature at its own position with its own sign, and a copy at `r0 - s` with the opposite sign
and the same orientation. Nothing is spatially mirrored; the copy is translated. In the
orchestrator's form, defining the reference at `r` as coming from `r - s'` (`s' = -s`), the result
is `phi(r) - phi(r - s')` and the twin sits at `r0 + s'`. Convention-free: if `d` is the vector
from the specimen point that supplies the object wave at an image point to the specimen point
that supplies its reference, the result is `phi(r) - phi(r + d)` and the twin of a feature at `r0`
sits at `r0 - d`. The conjugate sideband returns `-Phi` (features inverted, twins upright), so
which one is "the twin" depends on the declared sideband (items 10, 16). Because the demodulation
kernel of a real, even mask is real and even, the band-limited twin is exactly minus the
band-limited feature, up to the tails `f(d -+ s)`. A step `Delta` whose edge lies inside the overlap
appears twice: as the step at `y_s` and as a twin step of `-Delta` at `y_s - s_y`, i.e. a strip of
phase `-Delta` of width `|s_y|` (the shift component normal to the edge) between them.

### 3.3 Script output (`tools/physics_checks/q3_r2_twin.py`, 7/7 checks pass; excerpt, lines with `...` condensed, full output in appendix A.3)

```
   shift s = (40.0, 128.0) px (package: u_r(r) = u_o(r + s) ...); feature at r0 = (230.0, 300.0); carrier bin (0, 448); phi_o - phi_r (sideband at -q_ref)
   max |Phi - band-limited [phi(r) - phi(r + s)]| over the interior (78720 px): 1.01e-04 rad
   [PASS] Q3-A1 the reconstruction equals the band-limited phi(r) - phi(r + s) to 1e-3 rad
   feature peak Phi(r0) = +0.4461 rad; twin Phi(r0 - s) = -0.4461 rad at r0 - s = (190, 172)
   81 x 81 px windows: max |twin + feature| (sign-inverted translate) = 4.53e-04;  mirrored along axis 0: 0.212;  along axis 1: 0.217;  point-inverted: 0.217;  same sign: 0.896 rad
   [PASS] Q3-A2 twin = minus the feature, translated by -s (to 1e-3 rad)
   [PASS] Q3-A3 twin is NOT a spatial mirror (axis 0, axis 1 or point inversion: all > 0.1 rad) and NOT same-sign
   conjugate sideband (+q_c, bin (0, 64), CONJUGATE: phi_r - phi_o (sideband at +q_ref)): max |Phi_conj + Phi| = 4.44e-16 rad
   [PASS] Q3-A4 the conjugate sideband returns -Phi = phi(r + s) - phi(r) (1e-9 rad)
   phi_rel = 0.7 rad: max |Phi(0.7) - Phi(0) + 0.7| over the interior = 5.31e-05 rad (exact in the sideband; the residual is centre-band leakage from the reference's valid-mask edge, which does not rotate with phi_rel; same level as Q3-A1)
   s = (-40.0, -90.0): windows centred on (276, 301); twin window at -s (316, 391): max |twin + feature| = 4.40e-04 rad; window at +s (236, 211) (valid interior): max |Phi| = 3.84e-04 rad, max |Phi + feature| = 0.448 rad
   s = (-64.0, 90.0): ... twin at -s: 7.97e-05 rad; at +s: max |Phi| = 4.27e-05 rad
   s = (64.0, -90.0): ... twin at -s: 7.24e-05 rad; at +s: max |Phi| = 2.52e-05 rad
   s = (40.0, 90.0): ... twin at -s: 3.60e-04 rad; at +s: max |Phi| = 2.05e-04 rad
   [PASS] Q3-B1 for every shift the twin sits at r0 - s (package convention), never at r0 + s
   step of 1.0 rad at row 300 (phase 1.0 rad for rows > 300); s = (96.0, 40.0) px
   rows 228..276 (between twin step and step): median Phi = -1.0003 rad; rows 72..180: +0.0000; rows 324..344: -0.0002
   [PASS] Q3-C1 a step Delta at y_s appears as a strip of phase -Delta between the twin step at y_s - s_y and the step at y_s (1e-3 rad); 0 outside
```

The first draft of check Q3-A5 used a 1e-9 rad tolerance and failed (`5.3e-05`): `phi_rel` is an
exact constant inside the sideband, but the centre band leaks into the mask at the 1e-4 level
(the reference's valid-mask edge is sharp) and does not rotate with `phi_rel`. The tolerance was set
to the 1e-3 rad of check Q3-A1 (and of S1c's R2 test), not tuned to the observed value.

### 3.4 Conclusion and label

S1c's finding is VERIFIED (DERIVED_HERE within the R2 model; numbers from an independent script
with a two-dimensional asymmetric feature and shifts of both signs on both axes). An R2
reconstruction returns `phi(r) - phi(r + s)` (package convention; `phi(r) - phi(r - s')` with
`s' = -s`): every feature of the reference region reappears **sign-inverted, translated by `-s`
(from the reference source point towards the object point), with unchanged orientation; nothing is
spatially mirrored**. The copy also carries the amplitude of the reference region,
`|u_o(r)| |u_o(r + s)|`. docs/03's "mirrored twin" is wrong for this model; a mirror image would
need an optical element that inverts one partial image, which neither the model nor B5 contains.

### 3.5 Proposed wording (not applied)

docs/03 section 6, R2 clause, replacing "R2 self-reference from a flat region of the same surface
(common-mode phases cancel; a mirrored twin of the reference region appears in the result)":

> R2 self-reference from a flat region of the same surface: with the reference at image point `r`
> taken from specimen point `r + s`, the reconstruction returns `phi(r) - phi(r + s)`. Common-mode
> phases cancel, the object region is measured relative to the reference region, and every feature
> lying in the reference region appears a second time, sign-inverted and translated by `-s`
> (a translated copy, not a mirror image; the conjugate sideband returns the negative of the whole
> map). A step inside the overlap appears with its twin as a strip of phase `-Delta` whose width is
> the shift component normal to the step edge (C2, S1c).

model_assumptions B5, appended to the Sensitivity column:

> R2 returns `phi(r) - phi(r + s)` for `u_r(r) ~ u_o(r + s)`: features of the reference region appear
> sign-inverted and translated by `-s`, not mirrored (DERIVED_HERE, C2 question 3 and S1c). A real
> overlap that inverts one partial image would change this; items 15 and 16.

## 4. Summary of findings and recommendations

1. Q1: S1b's claim is correct. At an exact <100> azimuth the bulk-terminated a/4 terraces are
   related by the Fd-3m d-glide in the incidence plane (plane (010) for `[100]`, glide
   `(a/4)[+-1,0,1]`, normal component a/4). It fixes `k_in` and `k_out`, so
   `A_up = exp(-i (k_out - k_in).t) A_low` exactly and the a/4 step phase is purely geometric,
   `-(4 pi/lambda)(a/4) sin(theta_ext)`. At <110> no such operation exists; the residual
   `delta_[110] = phi_R,P - phi_R,T` is zero kinematically, nonzero only through multiple scattering,
   and unknown until a many-beam calculation is run. A misalignment `epsilon` from <100> gives a
   residual odd and generically linear in `epsilon`. A 2x1 reconstruction (not modelled) can break
   the <100> result. Recommended wording for docs/03 section 2, B4, open question 3 and item 8 is in
   section 1.6. The builder's per-step metadata ("B4 does NOT apply" for every a/4 step) and the
   CFG-B config comment ("diamond 4_1 screw") are incomplete at <100> (not edited). Strictly,
   `Rz(-90) + a/4` is a 4_3 operation (4_3^3); Fd-3m has both 4_1 and 4_3 axes along [001].
2. Q2: S1c's mechanism is correct: 0.78 rad is `-2.36 + pi`, the conjugate sideband plus a
   one-bin ramp, with the sign set by argmax tie-breaking within an exactly equal Hermitian pair.
   Which pair is brightest depends on the edge profile (1.56 % here); the harmonic beats the
   carrier for 50/50 steps with `|Delta| > 2.008 rad`. Wording in section 2.5.
3. Q3: R2 returns `phi(r) - phi(r + s)`; the twin is sign-inverted, translated by `-s`, not
   mirrored. Wording in section 3.5.
4. Side finding: the closed form of `Delta` in docs/physics_conventions.md and docs/03 section 3 is
   first order in `V0` (relative error 8.4e-6 in `Delta`, at most 5.1e-5 rad in an a/4 step phase);
   the calculator uses the exact form. Suggest "to first order in V0" or the exact expression.

## 5. Limitations, NOT RUN

* No dynamical (many-beam, Bloch-wave or multislice) reflection calculation was run: the value of
  `delta_[110](theta)`, its misalignment slope at <100> and the modulus differences are unknown.
* The Foldy-Lax point-scatterer model is a toy (k = 3 rad/A, f0 = 0.40 + 0.15i A, a 251-atom
  hemispherical cluster). It checks the covariance relation, its sign, reciprocity and the
  zero / nonzero / odd / first-order structure; none of its numbers is physical.
* The reconstruction toys use TEST_ONLY displacements chosen for their symmetry only; no Si(001)
  dimer geometry was read or used, and the twisted-dimer pattern is not a proposed structure.
* Illumination convergence and the ensemble average over incident azimuths were not analysed for
  the a/4 relation (section 1.3).
* No package, test, config or document file was edited; this agent committed nothing.

## Appendix: full script outputs (verbatim, final run on HEAD 7874c85)

### A.1 `venv/bin/python tools/physics_checks/q1_si001_quarter_step_symmetry.py` (exit 0)

```

====================================================================================================
A. DIAMOND SITE RULE (integer a/4 units) FROM reflection_holo.constants.DIAMOND_BASIS
====================================================================================================
   sites generated from the 8-atom basis in [-8, 8]^3: 621; sites satisfying the parity rule: 621
   rule: all even with n1+n2+n3 = 0 (mod 4), or all odd with n1+n2+n3 = 3 (mod 4)
   [PASS] A1 parity rule == basis-generated site set
   examples: layer n3 = 0 (top of H_0): [[-8, -8, 0], [-8, -4, 0], [-8, 0, 0]];  layer n3 = 1 (top of H_1): [[-7, -7, 1], [-7, -3, 1], [-7, 1, 1]]

====================================================================================================
B. THE 48 POINT OPERATIONS OF m-3m AND THEIR Fd-3m TRANSLATION COSETS
====================================================================================================
   [PASS] B1 48 distinct signed permutation matrices forming a group
   For every point operation M exactly one translation coset makes (M, t) a symmetry of
   the diamond structure: t in the fcc lattice (the 24 operations of -43m = Td, the site
   symmetry of the atom at the origin) or t in (a/4)(1,1,1) + fcc (the other 24).
   operations with t in fcc: 24;  with t in (a/4)(1,1,1) + fcc: 24
   [PASS] B2 every point operation has exactly one coset; 24 + 24
   Operations that fix the outward normal [001] (the only ones that can map a half crystal
   z <= c onto a half crystal z <= c'):
               1  M = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]   coset t in fcc   ->  t_z in (a/2) Z
        m(0,1,0)  M = [[1, 0, 0], [0, -1, 0], [0, 0, 1]]   coset t in (a/4)(1,1,1) + fcc   ->  t_z in a/4 + (a/2) Z
        m(1,0,0)  M = [[-1, 0, 0], [0, 1, 0], [0, 0, 1]]   coset t in (a/4)(1,1,1) + fcc   ->  t_z in a/4 + (a/2) Z
        2[0,0,1]  M = [[-1, 0, 0], [0, -1, 0], [0, 0, 1]]   coset t in fcc   ->  t_z in (a/2) Z
       m(1,-1,0)  M = [[0, 1, 0], [1, 0, 0], [0, 0, 1]]   coset t in fcc   ->  t_z in (a/2) Z
       4-[0,0,1]  M = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]   coset t in (a/4)(1,1,1) + fcc   ->  t_z in a/4 + (a/2) Z
       4+[0,0,1]  M = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]   coset t in (a/4)(1,1,1) + fcc   ->  t_z in a/4 + (a/2) Z
        m(1,1,0)  M = [[0, -1, 0], [-1, 0, 0], [0, 0, 1]]   coset t in fcc   ->  t_z in (a/2) Z
   [PASS] B3 exactly 8 operations fix [001] (point group 4mm)

====================================================================================================
C. EXHAUSTIVE SEARCH: ISOMETRIES (M in m-3m, any translation) MAPPING ONE TRUNCATED HALF CRYSTAL ONTO ANOTHER
====================================================================================================
   Test patch |n1|,|n2| <= 16, 16 layers deep (a/4 units); candidate window |q1|,|q2| <= 8, 8 layers deep.

   a/4 up-step: lower H_0 -> upper H_1: 15456 (M, t) candidates tested (p0 = [0, 0, 0]); 128 succeed, 4 class(es) modulo the surface net:
       4+[0,0,1]  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
       4-[0,0,1]  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
        m(0,1,0)  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
        m(1,0,0)  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True

   a/4 up-step, other terrace pair: H_1 -> H_2: 15840 (M, t) candidates tested (p0 = [-1, -1, 1]); 160 succeed, 4 class(es) modulo the surface net:
       4+[0,0,1]  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
       4-[0,0,1]  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
        m(0,1,0)  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True
        m(1,0,0)  t = (a/4)*[-1, -1, 1]  = [-1.357725, -1.357725, 1.357725] A   t_z = 1.357725 A   bulk Fd-3m element: True

   self-symmetry of the lower terrace H_0: 15888 (M, t) candidates tested (p0 = [0, 0, 0]); 164 succeed, 4 class(es) modulo the surface net:
               1  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True
        2[0,0,1]  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True
       m(1,-1,0)  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True
        m(1,1,0)  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True

   self-symmetry of H_1: 15456 (M, t) candidates tested (p0 = [-1, -1, 1]); 128 succeed, 4 class(es) modulo the surface net:
               1  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True
        2[0,0,1]  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True
       m(1,-1,0)  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True
        m(1,1,0)  t = (a/4)*[0, 0, 0]  = [0.0, 0.0, 0.0] A   t_z = 0.000000 A   bulk Fd-3m element: True

   a/2 up-step: H_0 -> H_2: 15840 (M, t) candidates tested (p0 = [0, 0, 0]); 160 succeed, 4 class(es) modulo the surface net:
               1  t = (a/4)*[-2, 0, 2]  = [-2.71545, 0.0, 2.71545] A   t_z = 2.715450 A   bulk Fd-3m element: True
        2[0,0,1]  t = (a/4)*[-2, 0, 2]  = [-2.71545, 0.0, 2.71545] A   t_z = 2.715450 A   bulk Fd-3m element: True
       m(1,-1,0)  t = (a/4)*[-2, 0, 2]  = [-2.71545, 0.0, 2.71545] A   t_z = 2.715450 A   bulk Fd-3m element: True
        m(1,1,0)  t = (a/4)*[-2, 0, 2]  = [-2.71545, 0.0, 2.71545] A   t_z = 2.715450 A   bulk Fd-3m element: True
   [PASS] C1 H_0 -> H_1: exactly 4 classes: 4+[0,0,1], 4-[0,0,1], m(1,0,0), m(0,1,0)   (['4+[0,0,1]', '4-[0,0,1]', 'm(0,1,0)', 'm(1,0,0)'])
   [PASS] C2 H_0 -> H_1: no pure translation (identity absent)
   [PASS] C3 H_0 -> H_1: no diagonal mirror m(1,1,0) or m(1,-1,0) and no 2-fold
   [PASS] C4 every H_0 -> H_1 operation has t_z = a/4 exactly
   [PASS] C5 every H_0 -> H_1 operation is an element of Fd-3m (bulk basis test)
   [PASS] C6 H_1 -> H_2 gives the same four point operations
   [PASS] C7 H_0 self-symmetry point group = {1, 2[001], m(1,1,0), m(1,-1,0)} (2mm, diagonal mirrors)   (['1', '2[0,0,1]', 'm(1,-1,0)', 'm(1,1,0)'])
   [PASS] C8 a/2 step H_0 -> H_2 includes the pure lattice translation   (['1', '2[0,0,1]', 'm(1,-1,0)', 'm(1,1,0)'])

   Bulk versus half crystal: all 48 point operations are Fd-3m elements with a suitable translation; 40 of them do not fix [001] and map no half crystal onto another; of the 8 that fix [001], only the 4 of the non-Td coset reach t_z = a/4.

====================================================================================================
D. CLASSIFICATION OF THE OPERATIONS MAPPING THE LOWER TERRACE H_0 ONTO THE UPPER H_1 (origin on a top-layer atom of H_0)
====================================================================================================
   m(0,1,0): glide reflection (no pure mirror exists: every glide vector has an in-plane component). Plane normal [0.0, 1.0, 0.0], the plane contains [001] and [1.0, -0.0, -0.0].
      plane offset u.r (units of a, mod a/2) | in-plane glide component along the plane (units of a, mod a) | glide component along [001] (units of a)
          0.1250 |    +0.2500 |  +0.2500
          0.3750 |    -0.2500 |  +0.2500
   m(1,0,0): glide reflection (no pure mirror exists: every glide vector has an in-plane component). Plane normal [1.0, 0.0, 0.0], the plane contains [001] and [0.0, 1.0, 0.0].
      plane offset u.r (units of a, mod a/2) | in-plane glide component along the plane (units of a, mod a) | glide component along [001] (units of a)
          0.1250 |    +0.2500 |  +0.2500
          0.3750 |    -0.2500 |  +0.2500
   4-[0,0,1]: 4_3 screw (rotation -90 deg, +a/4 == 4_3^3); axis parallel to [001] through (x, y) = [-0.25, 0.0] a  (all axis positions modulo a/2: [(0.25, 0.0)]); translation along the axis = a/4 = 1.357725 A
   4+[0,0,1]: 4_1 screw (rotation +90 deg, +a/4); axis parallel to [001] through (x, y) = [0.0, -0.25] a  (all axis positions modulo a/2: [(0.0, 0.25)]); translation along the axis = a/4 = 1.357725 A
   [PASS] D1 both <100> glides: planes at a/8 and 3a/8 (mod a/2) from the atom row, glide (+-a/4 in plane, a/4 along [001]); no zero in-plane glide
   [PASS] D2 glide component along the outward normal = a/4 = h (the step height)

====================================================================================================
E. WHICH H_0 -> H_1 OPERATION PRESERVES THE INCIDENT AND SPECULAR WAVEVECTORS?
====================================================================================================
   k_in = k (cos(theta) b_hat - sin(theta) n_hat), k_out = k (cos(theta) b_hat + sin(theta) n_hat); M fixes both for every theta iff M b = b.
   azimuth    [100]: direct ['m(0,1,0)'];  via reciprocity ['m(1,0,0)'];  4+[0,0,1]: azimuth -> [0,-1,0]; 4-[0,0,1]: azimuth -> [0,1,0]
   azimuth    [010]: direct ['m(1,0,0)'];  via reciprocity ['m(0,1,0)'];  4+[0,0,1]: azimuth -> [1,0,0]; 4-[0,0,1]: azimuth -> [-1,0,0]
   azimuth   [-100]: direct ['m(0,1,0)'];  via reciprocity ['m(1,0,0)'];  4+[0,0,1]: azimuth -> [0,1,0]; 4-[0,0,1]: azimuth -> [0,-1,0]
   azimuth   [0-10]: direct ['m(1,0,0)'];  via reciprocity ['m(0,1,0)'];  4+[0,0,1]: azimuth -> [-1,0,0]; 4-[0,0,1]: azimuth -> [1,0,0]
   azimuth    [110]: direct none;  via reciprocity none;  4+[0,0,1]: azimuth -> [1,-1,0]; 4-[0,0,1]: azimuth -> [-1,1,0]; m(0,1,0): azimuth -> [1,-1,0]; m(1,0,0): azimuth -> [-1,1,0]
   azimuth   [1-10]: direct none;  via reciprocity none;  4+[0,0,1]: azimuth -> [-1,-1,0]; 4-[0,0,1]: azimuth -> [1,1,0]; m(0,1,0): azimuth -> [1,1,0]; m(1,0,0): azimuth -> [-1,-1,0]
   azimuth   [-110]: direct none;  via reciprocity none;  4+[0,0,1]: azimuth -> [1,1,0]; 4-[0,0,1]: azimuth -> [-1,-1,0]; m(0,1,0): azimuth -> [-1,-1,0]; m(1,0,0): azimuth -> [1,1,0]
   azimuth  [-1-10]: direct none;  via reciprocity none;  4+[0,0,1]: azimuth -> [-1,1,0]; 4-[0,0,1]: azimuth -> [1,-1,0]; m(0,1,0): azimuth -> [-1,1,0]; m(1,0,0): azimuth -> [1,-1,0]
   azimuth    [210]: direct none;  via reciprocity none;  4+[0,0,1]: azimuth -> [1,-2,0]; 4-[0,0,1]: azimuth -> [-1,2,0]; m(0,1,0): azimuth -> [2,-1,0]; m(1,0,0): azimuth -> [-2,1,0]
   azimuth    [310]: direct none;  via reciprocity none;  4+[0,0,1]: azimuth -> [1,-3,0]; 4-[0,0,1]: azimuth -> [-1,3,0]; m(0,1,0): azimuth -> [3,-1,0]; m(1,0,0): azimuth -> [-3,1,0]
   azimuth   [1-20]: direct none;  via reciprocity none;  4+[0,0,1]: azimuth -> [-2,-1,0]; 4-[0,0,1]: azimuth -> [2,1,0]; m(0,1,0): azimuth -> [1,2,0]; m(1,0,0): azimuth -> [-1,-2,0]
   [PASS] E1 at [100] the (010) glide fixes k_in and k_out (plane contains beam and normal)
   [PASS] E2 at [010] the (100) glide fixes k_in and k_out
   [PASS] E3 at every <110> azimuth no H_0 -> H_1 operation preserves k_in, k_out (direct or via reciprocity)
   [PASS] E4 at generic azimuths [210], [310], [1-20] none either
   (008), theta_ext = 16.4743 mrad, azimuth [100], m(0,1,0): max |M^T k - k| = 0.000e+00 rad/A;  (k_out - k_in).t = 11.207113177 rad
   [PASS] E5 (008) at [100]: M^T k_in = k_in and M^T k_out = k_out to 1e-12 rad/A
   [PASS] E6 (k_out - k_in).t = 2 k sin(theta_ext) a/4 (only t_z enters): got 11.2071131768 rad want 11.2071131768 +/- 1e-10
   (008), theta_ext = 16.4743 mrad, azimuth [110], m(0,1,0): max |M^T k - k| = 3.543e+02 rad/A;  (k_out - k_in).t = 11.207113177 rad
   [PASS] E7 (008) at [110]: the (010) glide moves k_in by more than 1 rad/A (not preserved)   (354.258 rad/A)
   [100], (010) glide, rod G_par = 1 x (4 pi/a)[100] (in the incidence plane): exp(-i G.t_par) = -1.000000000000 +0.000000000000 i  (spread over 32 class representatives 2.0e-15)
   [100], (010) glide, rod G_par = 2 x (4 pi/a)[100] (in the incidence plane): exp(-i G.t_par) = +1.000000000000 -0.000000000000 i  (spread over 32 class representatives 4.0e-15)
   [100], (010) glide, rod G_par = 3 x (4 pi/a)[100] (in the incidence plane): exp(-i G.t_par) = -1.000000000000 -0.000000000000 i  (spread over 32 class representatives 9.8e-15)
   [100], (010) glide, zeroth-Laue-zone rod G_par = (4 pi/a)[010] (perpendicular to the beam) is mapped to M G = [0.0, -2.313865, 0.0] rad/A: it relates rod +G on one terrace to rod -G on the other
   [PASS] E8 in-plane rods G = p (4 pi/a)[100] at [100] carry the extra factor (-1)^p, the same for every representative of the glide class

====================================================================================================
F. AZIMUTH ORBITS: WHICH LOWER-TERRACE AZIMUTH DOES THE UPPER TERRACE REPRODUCE?
====================================================================================================
   phi =   0.00 deg: lower-terrace orbit (own symmetries + reciprocity) [0.0, 90.0, 180.0, 270.0];  M^T b for the four H_0->H_1 operations [0.0, 90.0, 180.0, 270.0];  all equivalent to lower terrace at -phi: True;  equivalent to lower terrace at +phi: True
   phi =   0.50 deg: lower-terrace orbit (own symmetries + reciprocity) [0.5, 89.5, 180.5, 269.5];  M^T b for the four H_0->H_1 operations [90.5, 179.5, 270.5, 359.5];  all equivalent to lower terrace at -phi: True;  equivalent to lower terrace at +phi: False
   phi =   2.00 deg: lower-terrace orbit (own symmetries + reciprocity) [2.0, 88.0, 182.0, 268.0];  M^T b for the four H_0->H_1 operations [92.0, 178.0, 272.0, 358.0];  all equivalent to lower terrace at -phi: True;  equivalent to lower terrace at +phi: False
   phi =  45.00 deg: lower-terrace orbit (own symmetries + reciprocity) [45.0, 225.0];  M^T b for the four H_0->H_1 operations [135.0, 135.0, 315.0, 315.0];  all equivalent to lower terrace at -phi: True;  equivalent to lower terrace at +phi: False
   phi =  90.00 deg: lower-terrace orbit (own symmetries + reciprocity) [0.0, 90.0, 180.0, 270.0];  M^T b for the four H_0->H_1 operations [90.0, 180.0, 270.0, 360.0];  all equivalent to lower terrace at -phi: True;  equivalent to lower terrace at +phi: True
   phi =  20.00 deg: lower-terrace orbit (own symmetries + reciprocity) [20.0, 70.0, 200.0, 250.0];  M^T b for the four H_0->H_1 operations [110.0, 160.0, 290.0, 340.0];  all equivalent to lower terrace at -phi: True;  equivalent to lower terrace at +phi: False
   [PASS] F1 A_upper(phi) = exp(-i q.t) A_lower(-phi) for all four operations; A_lower(-phi) is symmetry-equivalent to A_lower(phi) only at phi = 0, 90 deg (<100>)

====================================================================================================
G. CROSS-CHECK: reflection_holo.structure.build_si001_terraces (relations measured on the built atoms, 8 operations x a/8 grid)
====================================================================================================
   azimuth [100], terrace-0 back-bond [1, -1, 0]: step type screw; operations found ['4+[0,0,1]', '4-[0,0,1]', 'm(0,1,0)', 'm(1,0,0)']; incidence-plane mirrors ['mirror(010)']
   azimuth [100], terrace-0 back-bond [1, 1, 0]: step type screw; operations found ['4+[0,0,1]', '4-[0,0,1]', 'm(0,1,0)', 'm(1,0,0)']; incidence-plane mirrors ['mirror(010)']
   azimuth [110], terrace-0 back-bond [1, -1, 0]: step type screw; operations found ['4+[0,0,1]', '4-[0,0,1]', 'm(0,1,0)', 'm(1,0,0)']; incidence-plane mirrors []
   azimuth [110], terrace-0 back-bond [1, 1, 0]: step type screw; operations found ['4+[0,0,1]', '4-[0,0,1]', 'm(0,1,0)', 'm(1,0,0)']; incidence-plane mirrors []
   azimuth [010], terrace-0 back-bond [1, -1, 0]: step type screw; operations found ['4+[0,0,1]', '4-[0,0,1]', 'm(0,1,0)', 'm(1,0,0)']; incidence-plane mirrors ['mirror(100)']
   azimuth [010], terrace-0 back-bond [1, 1, 0]: step type screw; operations found ['4+[0,0,1]', '4-[0,0,1]', 'm(0,1,0)', 'm(1,0,0)']; incidence-plane mirrors ['mirror(100)']
   [PASS] G1 package relation finder: same four operations as the exhaustive search, and the incidence-plane glide exactly at [100] ((010)) and [010] ((100)), none at [110]

====================================================================================================
H. MULTIPLE-SCATTERING TOY (Foldy-Lax point scatterers; k, theta, f0 TEST_ONLY): covariance, reciprocity, [100] equality, [110] residual, misalignment
====================================================================================================
   toy: k = 3.0 rad/A, theta = 0.4 rad, f0 = (0.4+0.15j) A per atom; cluster = atoms of H_0 within 13.0 A of the top-layer atom at the origin (hemisphere)
   cluster atoms: 251; the images of the cluster under the four H_0 -> H_1 operations (all with t = (a/4)(1,1,1)) coincide: True
   [PASS] H0 the hemisphere is invariant under H_0's own 2mm symmetries, so its screw and glide images coincide
   covariance f_upper(k1->k2) = exp(-i (k2-k1).t) f_lower(M^T k1 -> M^T k2), random directions, 4_1 screw: max relative residual 1.64e-14
   reciprocity f(k1->k2) = f(-k2 -> -k1), random directions: max relative residual 1.61e-14
   [PASS] H1 covariance with the sign exp(-i (k_out - k_in).t) holds to 1e-9
   [PASS] H2 reciprocity of the toy (symmetric Green's function) holds to 1e-9
   multiple scattering is not a small correction in the toy: |f - f_Born| / |f_Born| = 1.923 at [100]
   [PASS] H3 toy is strongly multiple-scattering (|f - f_Born|/|f_Born| > 0.1)
   [100] exact:  f_up / (exp(-i q.t) f_low) = +1.000000000000 +0.000000000000 i
   [PASS] H4 [100]: f_upper = exp(-i q.t) f_lower (ratio 1 to 1e-9)
   [110] exact:  f_up / (exp(-i q.t) f_low) = |0.950005| exp(i -2.997732)   (Born: |1.000000000000| exp(i -8.944e-15))
   [PASS] H5 [110]: residual nonzero with multiple scattering (|ratio - 1| > 1e-3)   (1.9450)
   [PASS] H6 [110]: residual zero in the Born (kinematic) limit (ratio 1 to 1e-12)
   [PASS] H7 [110]: f_upper(45 deg) = exp(-i q.t) f_lower(-45 deg) (the [1-10] azimuth), to 1e-9   (1.9e-15)
   misalignment eps from [100] (delta(eps) = arg of the ratio):
      eps = -0.30 deg: |ratio| = 0.849825260, delta = +2.359928e-01 rad
      eps = -0.10 deg: |ratio| = 0.946616496, delta = +7.841980e-02 rad
      eps = +0.10 deg: |ratio| = 1.056394014, delta = -7.841980e-02 rad
      eps = +0.30 deg: |ratio| = 1.176712493, delta = -2.359928e-01 rad
   [PASS] H8 delta(eps) is odd: delta(-eps) = -delta(eps) to 1e-9
   [PASS] H9 delta(eps) is first order: delta(0.3 deg)/delta(0.1 deg) = 3 within 5 %   (3.0094)

====================================================================================================
I. RECONSTRUCTION SYMMETRY TOY: does a dimerised terrace pair keep a [100]-compatible operation? (displacements TEST_ONLY, symmetry only)
====================================================================================================

   symmetric dimers: displacements (pairing, z, buckling, twist) = (0.7, -0.1, 0.0, 0.0) A
      upper =  4+[0,0,1] image of lower: [100]-compatible operations found ['m(0,1,0)', 'm(1,0,0)'];  [110]-compatible NONE
      upper =  4-[0,0,1] image of lower: [100]-compatible operations found ['m(0,1,0)', 'm(1,0,0)'];  [110]-compatible NONE
      upper =   m(0,1,0) image of lower: [100]-compatible operations found ['m(0,1,0)', 'm(1,0,0)'];  [110]-compatible NONE
      upper =   m(1,0,0) image of lower: [100]-compatible operations found ['m(0,1,0)', 'm(1,0,0)'];  [110]-compatible NONE

   buckled dimers p(2x1): displacements (pairing, z, buckling, twist) = (0.7, -0.1, 0.35, 0.0) A
      upper =  4+[0,0,1] image of lower: [100]-compatible operations found ['m(1,0,0)'];  [110]-compatible NONE
      upper =  4-[0,0,1] image of lower: [100]-compatible operations found ['m(0,1,0)'];  [110]-compatible NONE
      upper =   m(0,1,0) image of lower: [100]-compatible operations found ['m(0,1,0)'];  [110]-compatible NONE
      upper =   m(1,0,0) image of lower: [100]-compatible operations found ['m(1,0,0)'];  [110]-compatible NONE

   twisted dimers (no diagonal mirror; toy only): displacements (pairing, z, buckling, twist) = (0.7, -0.1, 0.0, 0.2) A
      upper =  4+[0,0,1] image of lower: [100]-compatible operations found NONE;  [110]-compatible NONE
      upper =  4-[0,0,1] image of lower: [100]-compatible operations found NONE;  [110]-compatible NONE
      upper =   m(0,1,0) image of lower: [100]-compatible operations found ['m(0,1,0)', 'm(1,0,0)'];  [110]-compatible NONE
      upper =   m(1,0,0) image of lower: [100]-compatible operations found ['m(0,1,0)', 'm(1,0,0)'];  [110]-compatible NONE
   [PASS] I1 symmetric-dimer toy: both <100> glides survive for every upper-terrace variant
   [PASS] I2 buckled p(2x1) toy: exactly one <100> glide survives per variant (the (100) one needs reciprocity at [100])
   [PASS] I3 twisted-dimer toy (both diagonal mirrors removed): some variant has NO [100]-compatible operation, i.e. a reconstruction can break the relation
   [PASS] I4 no [110]-compatible operation for any toy or variant

====================================================================================================
J. GEOMETRIC PHASE OF THE a/4 STEP AT THE Si(001) SPECULAR (00L) CONDITIONS, 200 keV, V0 = 12 V (ASSUMPTION B1)
====================================================================================================
   lambda = 0.02507934 A, k = 250.5323 rad/A;  Delta exact = 6.982057e-05;  Delta (physics_conventions form, first order in V0) = 6.981998e-05;  relative difference = 8.439e-06 (= U/(2T+U+2E0) = 8.439e-06)
       (00L)  th_ext mrad  dphi = -2 K_ext a/4   wrapped  h_2pi (A)  dh per 0.1 rad of residual (A)
   (0, 0, 4)       3.9344              -2.6766   -2.6766     3.1872                          0.0507
   (0, 0, 8)      16.4743             -11.2071    1.3593     0.7612                          0.0121
   (0, 0, 12)      26.4205             -17.9720    0.8776     0.4747                          0.0076
   (0, 0, 16)      35.9936             -24.4814    0.6513     0.3485                          0.0055
   [PASS] J1 K_ext recomputed from the exact refraction relation equals the calculator's to 1e-12 (relative)   (0.0e+00)
   With the physics_conventions (first-order) Delta instead: max relative K_ext difference 1.90e-05 (at (004)); max change of the a/4 step phase 5.09e-05 rad
   [PASS] J1b the first-order Delta of physics_conventions.md changes K_ext by < 1e-4 and the a/4 step phase by < 1e-4 rad (negligible, but not exact)   (1.90e-05, 5.09e-05 rad)
   [PASS] J2 (008) wrapped a/4 step phase equals the calculator section 4b value 1.3593: got 1.35925743757 rad want 1.3593 +/- 5e-05

====================================================================================================
SUMMARY
====================================================================================================
   41/41 self-checks pass
```

### A.2 `venv/bin/python tools/physics_checks/q2_carrier_trap.py` (exit 0)

```
Delta (T24) = sc666.step_phase(d111)['wrapped'] = 2.359613 rad

====================================================================================================
A. THE CALCULATOR'S OWN PEAK SEARCH ON THE T24 OBJECT HOLOGRAM (calculator functions)
====================================================================================================

   dose = 0 e/px (seed 12345 when > 0)
   |F| at the carrier bins (k_y, k_x) = (0, -64): 1.011215e+05   (0, +64): 1.011215e+05
   |F| at first-harmonic bin (-1, +64) [fftshifted (255, 320)]: 1.554943692e+05
   |F| at first-harmonic bin (+1, -64) [fftshifted (257, 192)]: 1.554943692e+05
   |F| at first-harmonic bin (+1, +64) [fftshifted (257, 320)]: 1.530622443e+05
   |F| at first-harmonic bin (-1, -64) [fftshifted (255, 192)]: 1.530622443e+05
   Hermitian pairs: rel. |F(-1,+64)| - |F(+1,-64)| = 0.0e+00;  |F(+1,+64)| - |F(-1,-64)| = 0.0e+00
   within-sideband asymmetry (|F(-1,+64)| - |F(+1,+64)|)/|F(-1,+64)| = +1.564e-02
   calculator brightest object bin (fftshifted): (255, 320) -> (k_y, k_x) = (-1, +64): CONJUGATE sideband (+q_c), 1 row(s) off the carrier
   calculator brightest EMPTY-hologram bin: (256, 192)
   recentre on the brightest object bin, no division (the first version):  step = +0.7820 rad
   its Hermitian partner (257, 192), no division:                   step = -0.7820 rad
   brightest object bin, object/empty both demodulated there:           step = -2.3596 rad
   conjugate sideband at the true carrier (256, 320), divided:          step = -2.3596 rad
   correct sideband one row off, (257, 192) / (255, 192), no division:  step = -0.7820 / -0.7820 rad
   correct path: carrier (256, 192) from the empty hologram, divided:   step = +2.3596 rad
   -Delta + pi = +0.7820 rad;  Delta - pi = -0.7820 rad;  Delta = +2.3596 rad

   dose = 10000 e/px (seed 12345 when > 0)
   |F| at the carrier bins (k_y, k_x) = (0, -64): 5.056032e+08   (0, +64): 5.056032e+08
   |F| at first-harmonic bin (-1, +64) [fftshifted (255, 320)]: 7.774713396e+08
   |F| at first-harmonic bin (+1, -64) [fftshifted (257, 192)]: 7.774713396e+08
   |F| at first-harmonic bin (+1, +64) [fftshifted (257, 320)]: 7.653378798e+08
   |F| at first-harmonic bin (-1, -64) [fftshifted (255, 192)]: 7.653378798e+08
   Hermitian pairs: rel. |F(-1,+64)| - |F(+1,-64)| = 0.0e+00;  |F(+1,+64)| - |F(-1,-64)| = 0.0e+00
   within-sideband asymmetry (|F(-1,+64)| - |F(+1,+64)|)/|F(-1,+64)| = +1.561e-02
   calculator brightest object bin (fftshifted): (255, 320) -> (k_y, k_x) = (-1, +64): CONJUGATE sideband (+q_c), 1 row(s) off the carrier
   calculator brightest EMPTY-hologram bin: (256, 192)
   recentre on the brightest object bin, no division (the first version):  step = +0.7815 rad
   its Hermitian partner (257, 192), no division:                   step = -0.7815 rad
   brightest object bin, object/empty both demodulated there:           step = -2.3597 rad
   conjugate sideband at the true carrier (256, 320), divided:          step = -2.3597 rad
   correct sideband one row off, (257, 192) / (255, 192), no division:  step = -0.7815 / -0.7814 rad
   correct path: carrier (256, 192) from the empty hologram, divided:   step = +2.3597 rad
   -Delta + pi = +0.7820 rad;  Delta - pi = -0.7820 rad;  Delta = +2.3596 rad
   [PASS] Q2-A1 calculator brightest object bin is fftshifted (255, 320) = (k_y, k_x) = (-1, +64): conjugate sideband, one row off (noiseless and dose 1e4)
   [PASS] Q2-A2 empty hologram gives the true carrier of the correct sideband, (256, 192)
   [PASS] Q2-A3 the brightest bin and its Hermitian partner have equal |F| (rel. 1e-12), for the noiseless and the noisy hologram   (0.0e+00, 0.0e+00)
   [PASS] Q2-A4 recentring on it without division gives +0.78 (printed digits, tol 0.005) = -Delta + pi (tol 1e-3)   (+0.7820)
   [PASS] Q2-A5 the same with dose 1e4, seed 12345 (tol 1e-3 to -Delta + pi)   (+0.7815)
   [PASS] Q2-A6 the Hermitian partner gives -0.78 = Delta - pi (tol 1e-3)   (-0.7820)
   [PASS] Q2-A7 dividing by the empty hologram demodulated at the same wrong bin removes the ramp and leaves the conjugate sign: -Delta (T24 tol 5e-3)   (-2.3596)
   [PASS] Q2-A8 the ramp alone (correct sideband, one row off, either direction) gives Delta - pi = -0.78: the + sign of the printed 0.78 identifies the conjugate sideband   (-0.7820, -0.7820)
   [PASS] Q2-A9 correct path (carrier from the empty hologram, division) recovers Delta (T24 tol 5e-3)

   ramp term: pad = 72 px; median rows of the terrace interiors 127.5 and 383.5 (separation 256 rows); one-bin ramp 2 pi/512 rad per row -> 3.141593 rad between the medians (pi = 3.141593)
   [PASS] Q2-A10 the one-bin ramp is worth exactly pi between the terrace medians (1e-12)

====================================================================================================
B. WHY THAT BIN: HARMONIC VERSUS CARRIER, AND WHICH PAIR WINS
====================================================================================================
   sharp 50/50 model: |first harmonic| / |carrier| = (2/pi) |tan(Delta/2)| = 1.5444; calculator hologram (tanh edge): 1.5377
   [PASS] Q2-B1 the first harmonic outshines the carrier; ratio within 1 % of (2/pi)|tan(Delta/2)|
   sharp step: the four first-harmonic |F| = [154292.5111495739, 154292.5111495739, 154292.51114957393, 154292.51114957393]; relative spread 1.9e-16; calculator picks (255, 192)
   tanh edge: within-sideband asymmetry +1.564e-02 decides WHICH Hermitian pair is brightest; argmax order then decides WHICH MEMBER of that exactly tied pair is returned
   [PASS] Q2-B2 sharp 50/50 step: the four first-harmonic bins tie to 1e-9 (relative)   (1.9e-16)
   [PASS] Q2-B3 tanh edge: the pair {(-1,+64), (+1,-64)} is brighter than {(+1,+64), (-1,-64)}
   argmax in numpy's unshifted order picks unshifted bin (1, 448) = (k_y, k_x) = (+1, -64); the calculator (fftshifted order) picks (255, 320) = (-1, +64)
   [PASS] Q2-B4 unshifted-order argmax returns the other member (1, 448) = (+1, -64): the sign of the 0.78 is a tie-break outcome

====================================================================================================
C. THRESHOLD: FOR WHICH 50/50 STEPS IS THE BRIGHTEST OBJECT BIN NOT THE CARRIER?
====================================================================================================
   sharp-step prediction: |Delta| > 2 arctan(pi/2) = 2.0078 rad (and < 2 pi - that = 4.2754 rad)
   Delta = +1.0000 (wrapped +1.0000): brightest bin (k_y, k_x) = (+0, -64) carrier (predicted carrier); naive step +1.0000 rad; no ramp
   Delta = +1.9000 (wrapped +1.9000): brightest bin (k_y, k_x) = (+0, -64) carrier (predicted carrier); naive step +1.9000 rad; no ramp
   Delta = +1.9800 (wrapped +1.9800): brightest bin (k_y, k_x) = (+0, -64) carrier (predicted carrier); naive step +1.9800 rad; no ramp
   Delta = +2.0400 (wrapped +2.0400): brightest bin (k_y, k_x) = (-1, +64) OFF carrier (predicted OFF); naive step +0.8808 rad; ramp wraps inside a terrace window: the median is corrupted
   Delta = +2.1000 (wrapped +2.1000): brightest bin (k_y, k_x) = (-1, +64) OFF carrier (predicted OFF); naive step +0.8821 rad; ramp wraps inside a terrace window: the median is corrupted
   Delta = +2.3596 (wrapped +2.3596): brightest bin (k_y, k_x) = (-1, +64) OFF carrier (predicted OFF); naive step +0.7820 rad; model sigma*Delta + rho*pi = +0.7820
   Delta = +3.0000 (wrapped +3.0000): brightest bin (k_y, k_x) = (-1, +64) OFF carrier (predicted OFF); naive step +0.1416 rad; model sigma*Delta + rho*pi = +0.1416
   Delta = +3.9236 (wrapped -2.3596): brightest bin (k_y, k_x) = (-1, +64) OFF carrier (predicted OFF); naive step -0.7820 rad; model sigma*Delta + rho*pi = -0.7820
   Delta = -1.5640 (wrapped -1.5640): brightest bin (k_y, k_x) = (+0, -64) carrier (predicted carrier); naive step -1.5640 rad; no ramp
   Delta = -2.3596 (wrapped -2.3596): brightest bin (k_y, k_x) = (-1, -64) OFF carrier (predicted OFF); naive step +0.7820 rad; model sigma*Delta + rho*pi = +0.7820
   [PASS] Q2-C1 the brightest object bin leaves the carrier exactly when |Delta| > 2 arctan(pi/2) (values 0.03 rad or more from the threshold)
   [PASS] Q2-C2 off-carrier cases without wrapping follow sigma*Delta + rho*pi (sideband sign sigma, ramp sign rho) to 1e-3

====================================================================================================
D. THE PACKAGE CHAIN (reflection_holo.optics + reconstruction) ON THE SAME HOLOGRAMS
====================================================================================================
   package object hologram vs calculator's: max |difference| = 0.0e+00
   [PASS] Q2-D1 the package forms the calculator's hologram (1e-12)
   package phase map at bin (511, 64) vs calculator _sideband_wave at (255, 320): max |difference| = 0.0e+00 rad (mask radius 0.041672 vs 0.041672 cycles/px)
   [PASS] Q2-D1b package demodulation at the trap bin equals the calculator's (1e-12 rad)
   whole-plane search on the OBJECT hologram (allowed only for demonstration): bin (511, 64), CONJUGATE: phi_r - phi_o (sideband at +q_ref); step +0.7820 rad
   search restricted to the correct sideband, on the OBJECT hologram: bin (1, 448), phi_o - phi_r (sideband at -q_ref); step -0.7820 rad
   carrier located on the EMPTY hologram (correct sideband), divided: bin (0, 448), phi_o - phi_r (sideband at -q_ref); step +2.3596 rad
   the package refuses an object hologram by default: True
   [PASS] Q2-D2 package whole-plane object search: unshifted bin (511, 64) = fftshifted (255, 320), flagged CONJUGATE, step -Delta + pi
   [PASS] Q2-D3 package search restricted to the correct sideband still fails on the object hologram: (1, 448), step Delta - pi
   [PASS] Q2-D4 package correct path recovers Delta (T24 tol 5e-3) and refuses object holograms by default

====================================================================================================
SUMMARY
====================================================================================================
   21/21 self-checks pass
```

### A.3 `venv/bin/python tools/physics_checks/q3_r2_twin.py` (exit 0)

```

====================================================================================================
A. ASYMMETRIC FEATURE: RESULT = phi(r) - phi(r + s); TWIN SIGN, SHIFT AND ORIENTATION
====================================================================================================
   shift s = (40.0, 128.0) px (package: u_r(r) = u_o(r + s) ...); feature at r0 = (230.0, 300.0); carrier bin (0, 448); phi_o - phi_r (sideband at -q_ref)
   max |Phi - band-limited [phi(r) - phi(r + s)]| over the interior (78720 px): 1.01e-04 rad
   [PASS] Q3-A1 the reconstruction equals the band-limited phi(r) - phi(r + s) to 1e-3 rad
   feature peak Phi(r0) = +0.4461 rad; twin Phi(r0 - s) = -0.4461 rad at r0 - s = (190, 172)
   81 x 81 px windows: max |twin + feature| (sign-inverted translate) = 4.53e-04;  mirrored along axis 0: 0.212;  along axis 1: 0.217;  point-inverted: 0.217;  same sign: 0.896 rad
   [PASS] Q3-A2 twin = minus the feature, translated by -s (to 1e-3 rad)
   [PASS] Q3-A3 twin is NOT a spatial mirror (axis 0, axis 1 or point inversion: all > 0.1 rad) and NOT same-sign
   r0 + s = (270, 428): in the invalid band (its reference source lies outside the field) -- the direction of the twin is tested with valid r0 + s in section B
   conjugate sideband (+q_c, bin (0, 64), CONJUGATE: phi_r - phi_o (sideband at +q_ref)): max |Phi_conj + Phi| = 4.44e-16 rad
   [PASS] Q3-A4 the conjugate sideband returns -Phi = phi(r + s) - phi(r) (1e-9 rad)
   phi_rel = 0.7 rad: max |Phi(0.7) - Phi(0) + 0.7| over the interior = 5.31e-05 rad (exact in the sideband; the residual is centre-band leakage from the reference's valid-mask edge, which does not rotate with phi_rel; same level as Q3-A1)
   [PASS] Q3-A5 the relative phase phi_rel enters as the constant -phi_rel (to the 1e-3 rad leakage tolerance of Q3-A1)   (5.3e-05)

====================================================================================================
B. THE SAME WITH A DIFFERENT SHIFT (both signs of both components)
====================================================================================================
   s = (-40.0, -90.0): windows centred on (276, 301); twin window at -s (316, 391): max |twin + feature| = 4.40e-04 rad; window at +s (236, 211) (valid interior): max |Phi| = 3.84e-04 rad, max |Phi + feature| = 0.448 rad
   s = (-64.0, 90.0): windows centred on (288, 211); twin window at -s (352, 121): max |twin + feature| = 7.97e-05 rad; window at +s (224, 301) (valid interior): max |Phi| = 4.27e-05 rad, max |Phi + feature| = 0.448 rad
   s = (64.0, -90.0): windows centred on (224, 301); twin window at -s (160, 391): max |twin + feature| = 7.24e-05 rad; window at +s (288, 211) (valid interior): max |Phi| = 2.52e-05 rad, max |Phi + feature| = 0.448 rad
   s = (40.0, 90.0): windows centred on (236, 211); twin window at -s (196, 121): max |twin + feature| = 3.60e-04 rad; window at +s (276, 301) (valid interior): max |Phi| = 2.05e-04 rad, max |Phi + feature| = 0.448 rad
   [PASS] Q3-B1 for every shift the twin sits at r0 - s (package convention), never at r0 + s

====================================================================================================
C. A TERRACE STEP INSIDE THE OVERLAP: STEP AND TWIN STEP
====================================================================================================
   step of 1.0 rad at row 300 (phase 1.0 rad for rows > 300); s = (96.0, 40.0) px
   rows 228..276 (between twin step and step): median Phi = -1.0003 rad; rows 72..180: +0.0000; rows 324..344: -0.0002
   [PASS] Q3-C1 a step Delta at y_s appears as a strip of phase -Delta between the twin step at y_s - s_y and the step at y_s (1e-3 rad); 0 outside

====================================================================================================
SUMMARY
====================================================================================================
   7/7 self-checks pass
```
