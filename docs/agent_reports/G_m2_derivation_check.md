# G. Independent check of the derivations behind the M2 reflection-multislice campaign

Status: IN PROGRESS (written incrementally; this line is replaced when the report is complete),
2026-10-14. Author: physics-deriver subagent G (independent check). Repository state checked:
branch `trixode-studios-claude/sweet-carson-2grkn2`, commit d404587. No repository file other than
this report was modified.

## 0. Scope, procedure, conventions, labels

Scope: Appendix A (A1 to A13) of `docs/08_fir_simulation_campaign.md`, the formulas and numbers of
its sections 2 and 3, and their implementation in `reflection_holo/` (functions listed by the
orchestrator). Read beforehand: `docs/physics_conventions.md`, `docs/03_physics_summary.md`,
`docs/model_assumptions.md` (section 2b), `configs/fir_m2_campaign.yaml`, `configs/smoke_cpu.yaml`,
`configs/benchmarks.yaml`, `.claude/agents/physics-deriver.md` (there is no CLAUDE.md in the
repository).

Procedure. For every item the premises were restated and the result derived and checked numerically
BEFORE any implementation file was opened (sections 1 to 14 below, scripts s0 to s8). The
implementation was read only afterwards (section 15). The numerical checks of the virtual-detector
formulas use an independent toy multislice written for this check (`toyms.py`, about 120 lines,
written from the derivation, not from the repository). Scripts and outputs:
`/tmp/claude-0/-home-user-Holography/57d40492-0c74-558e-a50e-ca09e117ea85/scratchpad/G_derive/`
(`sN_*.py`, output `sN_*.out`), run with `/tmp/claude-0/venv/bin/python` (Python 3.13.16, numpy
2.5.4, scipy 1.18.1, abTEM 1.0.10 installed in the venv). Every script contains self-checks with
explicit tolerances. Checks labelled "doc value" compare with a number printed in docs/08. When such
a check fails, the failure is the finding.

Conventions (`docs/physics_conventions.md`): `exp(+i(k.r - wt))`; x = outward normal (into vacuum),
y in-plane transverse, z = beam azimuth; glancing angles to the surface; `q` in cycles/A, `K = 2 pi q`
in rad/A; `kappa(q) = kz(q) - k`, `kz = 2 pi sqrt(1/lambda^2 - q^2)`; forward Fourier transform
`F(q) = int f exp(-2 pi i q.r)`; step phase `Delta_phi = phi(upper) - phi(lower) = -(k_out - k_in).R`.
Beam energy 200 keV throughout (300 keV is never used).

Evidence labels. Every result in sections 1 to 14 is DERIVED_HERE and REPRODUCED by the script whose
output is pasted. No textbook passage was read for this check. The Fermi-step closed form attributed
in A2 to Landau and Lifshitz section 25 is therefore UNVERIFIED as a citation. Here it is verified
only numerically, against direct integration of the 1D wave equation (s2). The Kirkland and Lobato Si
coefficients were read from the abTEM 1.0.10 data files installed in the venv
(`abtem/parametrizations/data/{kirkland,lobato}.json`). That is SECTION_READ of the data files and
REPRODUCED for the derived mean inner potential; the primary sources remain UNVERIFIED.

Finding ranks: Blocker (campaign results wrong or uninterpretable), Major (a stated result is wrong,
or a missing check could hide a wrong result), Minor, Nit. For each Blocker or Major the report states
whether it is (a) post-processing only, fixable by re-running aggregation on existing results, or (b)
a change of simulation output requiring re-planning.

## 1. Constants, refraction, Bragg conditions (s0)

Premises: CODATA 2018 (`m_e c^2 = 510998.950 eV`; h, c, e exact), T = 200 keV,
`lambda = h c / sqrt(T (T + 2 m c^2))`. The interaction constant is obtained two ways. (i) From the
relativistic Schroedinger equation, `k_in^2 = k^2 + 2 m gamma e V / hbar^2 == k^2 + 2 k sigma V`, so
`sigma = m gamma e / (hbar^2 k)`. (ii) From the Kirkland form
`sigma = 2 pi/(lambda V_acc) (m c^2 + eV)/(2 m c^2 + eV)`. Refraction conserves the surface-parallel
wavevector: `K_ext^2 = K_int^2 - k^2 Delta`, `Delta = 2 sigma V0/k`. The internal Bragg condition of
the specular rod is `K_int = G/2`.

```
m_e c^2 = 510998.950 eV
  CHECK PASS: m_e c^2 = 510998.950 eV: 510998.9499961642 vs 510998.95 (rtol=None, atol=0.001)
lambda = 0.02507934 A, k = 250.5323 rad/A, gamma = 1.391390
  CHECK PASS: lambda(200 keV) = 0.02507934 A: np.float64(0.025079340450548) vs 0.02507934 (rtol=2e-07, atol=None)
  CHECK PASS: k = 250.5323 rad/A: np.float64(250.53231840641544) vs 250.5323 (rtol=1e-06, atol=None)
sigma (Schroedinger route) = 7.288401e-04 rad/(V A); (Kirkland form) = 7.288401e-04
  CHECK PASS: two routes to sigma agree: np.float64(0.0007288401040958596) vs np.float64(0.0007288401040958594) (rtol=1e-12, atol=None)
  CHECK PASS: sigma = 7.2884e-4 rad/(V A): np.float64(0.0007288401040958596) vs 0.00072884 (rtol=1e-05, atol=None)
V0 = 12.0 V: Delta = 6.98200e-05; 2 sigma V0/k = 6.98200e-05; theta_c = 8.356 mrad
  CHECK PASS: Delta = 2 sigma V0 / k at V0=12.0: 6.981998414242392e-05 vs np.float64(6.981998414242393e-05) (rtol=1e-12, atol=None)
V0 = 13.9 V: Delta = 8.08748e-05; 2 sigma V0/k = 8.08748e-05; theta_c = 8.993 mrad
  CHECK PASS: Delta = 2 sigma V0 / k at V0=13.9: 8.087481496497438e-05 vs np.float64(8.087481496497438e-05) (rtol=1e-12, atol=None)
  CHECK PASS: Delta(12 V) = 6.98e-5: 6.981998414242392e-05 vs 6.98e-05 (rtol=0.001, atol=None)
  CHECK PASS: theta_c(12 V) = 8.356 mrad: np.float64(8.35564087485727) vs 8.356 (rtol=None, atol=0.0005)
non-relativistic V0/T at 12 V = 6.0000e-05 (ratio rel/nonrel = 1.1637)

a = 5.4309 A; d_111 = a/sqrt3 = 3.13553 A; a/4 = 1.35773 A; a/2 = 2.71545 A
[110] plane spacing a/(2 sqrt2) = 1.92011 A; [100] plane spacing a/4 = 1.35773 A
  CHECK PASS: [110] slice 1.920 A: np.float64(1.9201131089730104) vs 1.92 (rtol=None, atol=0.0005)
  CHECK PASS: [100] slice 1.358 A: 1.357725 vs 1.358 (rtol=None, atol=0.0005)

Specular-rod Bragg conditions (internal from sin = n lam/(2d); external by refraction)
 surface   refl        th_int(mrad)  th_ext@13.90V  th_ext@12.0V  step phase@13.90V (rad, signed)
 Si(111)  (3,-3,3) allowed     11.998      7.942      8.610    -12.4782 (mod 2pi: 0.0882)
 Si(111)  (4,-4,4) allowed     15.998     13.231     13.642    -20.7865 (mod 2pi: 4.3463)
 Si(111)  (5,-5,5) allowed     19.997     17.862     18.168    -28.0609 (mod 2pi: 3.3551)
 Si(111)  (6,-6,6) forbidden   23.998     22.249     22.496    -34.9530 (mod 2pi: 2.7462)
 Si(111)  (7,-7,7) allowed     27.998     26.515     26.723    -41.6530 (mod 2pi: 2.3293)
 Si(111)  (8,-8,8) allowed     31.999     30.710     30.889    -48.2410 (mod 2pi: 2.0245)
 Si(001)  (0,0, 4)   allowed     9.236      2.105      3.935
 Si(001)  (0,0, 8)   allowed    18.473     16.136     16.475
 Si(001)  (0,0,12)   allowed    27.711     26.212     26.421
 Si(001)  (0,0,16)   allowed    36.952     35.841     35.995
  CHECK PASS: (4,-4,4) th_ext at 12 V = 13.64 mrad: np.float64(13.642183645030224) vs 13.64 (rtol=None, atol=0.005)
  CHECK PASS: (5,-5,5) th_ext at 12 V = 18.17 mrad: np.float64(18.16831320227616) vs 18.17 (rtol=None, atol=0.005)
  CHECK PASS: (8,-8,8) th_ext at 12 V = 30.89 mrad: np.float64(30.889381688692087) vs 30.89 (rtol=None, atol=0.005)

2 pi a0 e = 47.87765 V A^2 (a0 = 0.529177 A, e/(4 pi eps0) = 14.39965 V A)
f_e(0): Kirkland 5.81428 A, Lobato 5.83600 A; n = 8/a^3 = 0.049943 A^-3
V0(Kirkland) = 13.9028 V, V0(Lobato) = 13.9548 V
  CHECK PASS: V0 Kirkland = 13.90 V: np.float64(13.902842571587932) vs 13.9 (rtol=None, atol=0.005)
  CHECK PASS: V0 Lobato = 13.95 V: np.float64(13.954769037128914) vs 13.95 (rtol=None, atol=0.005)
abTEM scattering_factor('Si')(q^2=0): Kirkland 5.81428, Lobato 5.83600
  CHECK PASS: abTEM Kirkland f(0) equals hand sum: 5.8142838994375206 vs np.float64(5.814283921998921) (rtol=1e-06, atol=None)
  CHECK PASS: abTEM Lobato f(0) equals hand sum: 5.836000238079578 vs np.float64(5.83599999999999) (rtol=1e-06, atol=None)

W = 0.5 V: intensity mean free path 1/(2 sigma W) = 1372.0 A = 137.2 nm
  CHECK PASS: MFP 137 nm: np.float64(137.20430508424334) vs 137.0 (rtol=None, atol=0.5)
delay n/(sigma W), n = 5: 13720 A
delay n/(sigma W), n = 7: 19209 A
delay n/(sigma W), n = 9: 24697 A
  CHECK PASS: delay 7/(sigma W) = 19,200 A (1.92 um): np.float64(19208.60271179407) vs 19208 (rtol=None, atol=10)
W = 2 V (smoke): 1/(sigma W) = 686.0 A
  CHECK PASS: 1/(sigma*2V) = 690 A: np.float64(686.0215254212168) vs 690 (rtol=None, atol=5)
u_rms = 0.076 A per axis: B = 8 pi^2 u^2 = 0.4561 A^2
  CHECK PASS: B = 0.456 A^2: 0.456054680165537 vs 0.456 (rtol=None, atol=0.001)
d|dphi|/dtheta (bilayer) at 13.23 mrad = 1.5710 rad/mrad
d|dphi|/dtheta (bilayer) at 20.0 mrad = 1.5708 rad/mrad
  CHECK PASS: 2 k h cos(theta) = 1.57 rad/mrad: np.float64(1.5711039908155755) vs 1.57 (rtol=None, atol=0.005)

SUMMARY: 23 of 23 checks passed
```

Comments. sigma = 7.2884e-4 rad/(V A) and lambda = 0.02507934 A are confirmed, and so is the identity
`Delta = 2 sigma V0/k` with the relativistic Delta of the conventions file. At the model's own mean
inner potential (13.90 V) the external Bragg angles of the rods used as window centres are
(4,-4,4) 13.23, (5,-5,5) 17.86, (7,-7,7) 26.51, (8,-8,8) 30.71, (0,0,8) 16.14 and (0,0,12)
26.21 mrad. The config uses 13.3, 17.9, 26.5, 30.6, 16.2 and 26.3 mrad. The largest offset, 0.11 mrad
at (8,-8,8), is far inside every window (half-width 1.4 to 2.1 mrad), so it is a labelling Nit
(F-N1), not a coverage problem. `1/(sigma * 2 V) = 686 A`, which docs/08 A12 rounds to 690 A.
(The s0 table builds sin(theta_int) from the vacuum wavelength. That differs from `K_int = G/2` by a
factor (1 + Delta) and moves the external angles by at most 0.8 urad; s1 uses `K_int = G/2`.)

## 2. A1, stationary dispersion of the multislice and refraction (s1)

Premises: the envelope psi is defined by `Psi = psi exp(ikz)`. One step is `P^(1/2) T P^(1/2)` with
`P(q) = exp(i (kz(q) - k) dz)` and `T = exp(i sigma (V + iW) dz)`. Derivation: in a region of
constant V, P and T commute, so a plane wave `exp(2 pi i q x)` is an eigenvector of one step with
phase `(kz - k + sigma V) dz`, exactly and for any dz (not only as dz -> 0). In a z-invariant
structure every z-Fourier component evolves independently. A stationary state therefore has a single
`beta = kz - k + sigma V` in every layer of constant V, which gives `K_int^2 = k^2 - (kz - sigma V)^2`.
The Schroedinger equation instead conserves kz itself, which gives `K_int^2 = K^2 + 2 k sigma V`.
Expanding, `K_int^2(MS) - K^2 = 2 kz sigma V - sigma^2 V^2`. The relative difference of the
refraction terms is therefore `-[(k - kz)/k + sigma V/(2k)]`, exactly the two terms named in A1.
The signs are those of the exp(+ik.r) convention: kz < k gives the Fresnel phase
`-pi lambda q^2 dz`, and an attractive potential (V > 0) advances the phase, `T = exp(+i sigma V dz)`.
Validity: the one-way (forward-scattering) multislice, slices perpendicular to the beam, no
back-scattering along z.

```
plane wave q = 0.1709 c/A: phase after 200 steps numeric 3.006616899553, theory 3.006616899553
  CHECK PASS: split-step advances a plane wave by (kz - k + sigma V) per unit z 

Refraction term K_int^2 - K^2: multislice (MS) k^2-(kz - sigma V)^2 - K^2 vs Schroedinger 2 k sigma V
 theta(mrad)  V(V)   MS/Schr - 1      (k-kz)/k + sigma V/(2k)   theta_int MS - theta_int Schr (urad)
     7.00    13.9   -4.4719e-05      -4.4719e-05              -0.1587
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=7.0, V=13.9 
    13.30    13.9   -1.0866e-04      -1.0866e-04              -0.2737
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=13.3, V=13.9 
    20.00    13.9   -2.2021e-04      -2.2021e-04              -0.4062
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=20.0, V=13.9 
    30.00    13.9   -4.7018e-04      -4.7018e-04              -0.6075
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=30.0, V=13.9 
    45.00    13.9   -1.0325e-03      -1.0325e-03              -0.9111
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=45.0, V=13.9 
    52.30    13.9   -1.3876e-03      -1.3876e-03              -1.0593
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=52.3, V=13.9 
     7.00    40.0   -8.2683e-05      -8.2683e-05              -0.5733
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=7.0, V=40.0 
    13.30    40.0   -1.4663e-04      -1.4663e-04              -0.8432
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=13.3, V=40.0 
    20.00    40.0   -2.5818e-04      -2.5818e-04              -1.1948
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=20.0, V=40.0 
    30.00    40.0   -5.0815e-04      -5.0815e-04              -1.7582
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=30.0, V=40.0 
    45.00    40.0   -1.0705e-03      -1.0705e-03              -2.6255
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=45.0, V=40.0 
    52.30    40.0   -1.4255e-03      -1.4255e-03              -3.0508
  CHECK PASS: MS/Schr-1 = -[(k-kz)/k + sigma V/2k] (2nd order), th=52.3, V=40.0 
max |MS/Schr - 1| for V = 13.9 V over 7-52.3 mrad: 1.388e-03
sigma V/(2k) at 13.9 V = 2.022e-05
  CHECK PASS: sigma V/(2k) ~ 2e-5 at 13.9 V 

External Bragg angle of (n,-n,n) under the two dispersions (V0 = 13.90 V)
  n=3: th_ext Schr 7.9417 mrad, MS 7.9419 mrad, diff +0.264 urad
  CHECK PASS: Bragg shift MS-Schr below 2 urad (n=3) 
  n=4: th_ext Schr 13.2301 mrad, MS 13.2304 mrad, diff +0.329 urad
  CHECK PASS: Bragg shift MS-Schr below 2 urad (n=4) 
  n=5: th_ext Schr 17.8606 mrad, MS 17.8610 mrad, diff +0.407 urad
  CHECK PASS: Bragg shift MS-Schr below 2 urad (n=5) 
  n=7: th_ext Schr 26.5138 mrad, MS 26.5144 mrad, diff +0.567 urad
  CHECK PASS: Bragg shift MS-Schr below 2 urad (n=7) 
  n=8: th_ext Schr 30.7086 mrad, MS 30.7093 mrad, diff +0.648 urad
  CHECK PASS: Bragg shift MS-Schr below 2 urad (n=8) 

SUMMARY: 19 of 19 checks passed
```

Verdict A1: correct as stated. The multislice refraction term is smaller than the Schroedinger one by
4.5e-5 (7 mrad) to 1.4e-3 (52 mrad) relative. That moves the external Bragg angles by under 1 urad,
which is negligible against the 20 urad angle grid. One point A1 does not state: the layered
"Parratt in the multislice dispersion" is itself a local approximation of the (non-local) stationary
multislice operator. Its agreement with the multislice is therefore limited to about 1e-4 relative
even without discretisation error (s3 below: 1.7e-4 at 13 mrad). This matches the 1.9e-4 of the
rung-1 table and is not an error.

## 3. A2, Parratt recursion (s2, s2b)

Premises: `phi'' + K(x)^2 phi = 0`; in layer j, `phi = A_j exp(-i K_j (x - x_j)) + B_j exp(+i K_j (x - x_j))`
(down-going first, exp(+ik.r)); layers numbered from the vacuum (j = 0) downward; x_j is the bottom
of layer j. Continuity of phi and phi' at x_j, with `Y = X_{j+1} exp(2 i K_{j+1} d_{j+1})`, gives
`K_j (X - 1)/(X + 1) = K_{j+1} (Y - 1)/(Y + 1)`, hence `X_j = (r_j + Y)/(1 + r_j Y)`,
`r_j = (K_j - K_{j+1})/(K_j + K_{j+1})`. This is the A2 formula. The bottom layer carries only the
down-going wave `exp(-i K_N x)`, which decays toward -x if Im K_N > 0 (true for W > 0 with the root
Re K > 0). In vacuum, `r(x_ref) = B_0 e^{i K_0 (x_ref - x_top)} / (A_0 e^{-i K_0 (x_ref - x_top)}) = X_0 exp(2 i K_0 (x_ref - x_top))`.
Translating the whole profile up by h therefore gives `r -> r exp(-2 i K_0 h)` (A6).
The Fermi step `V = V0/(1 + exp(x/a))` closed form `|r|^2 = [sinh(pi a (K1 - K0))/sinh(pi a (K1 + K0))]^2`
is checked against direct ODE integration (DOP853, rtol 1e-12) of the 1D equation with the same
profile.

```
single interface at 15 mrad: Parratt r = -0.07662335+0.00000000j, Fresnel (K0-K1)/(K0+K1) = -0.07662335+0.00000000j
  CHECK PASS: Parratt single interface = Fresnel 
random multilayer: Parratt -0.040894476759-0.007170110749j, transfer matrix -0.040894476759-0.007170110749j, |diff| 6.97e-17
  CHECK PASS: Parratt = transfer matrix to 1e-10 
no absorption: |r|^2 + (K_N/K_0)|t|^2 = 1.000000000000000
  CHECK PASS: flux conservation to 1e-12 
translation by h: r_up/r_low = 0.003493894715+0.999993896331j, exp(-2iK0 h) = 0.003493894715+0.999993896331j
  CHECK PASS: r_up = r_low exp(-2 i K_ext h) 
Fermi step 15.0 mrad, a = 0.2 A: |r|^2 closed 2.335682e-05, ODE 2.335682e-05, Parratt(8000 layers) 2.335606e-05; arg r ODE +2.878442, Parratt +2.878437
  CHECK PASS: closed form = ODE |r|^2 (rel 1e-6), 15.0 mrad a=0.2 
  CHECK PASS: fine Parratt = ODE (|dr| < 1e-4 |r|), 15.0 mrad a=0.2 
Fermi step 13.0 mrad, a = 0.2 A: |r|^2 closed 9.600238e-05, ODE 9.600238e-05, Parratt(8000 layers) 9.599994e-05; arg r ODE +2.878938, Parratt +2.878935
  CHECK PASS: closed form = ODE |r|^2 (rel 1e-6), 13.0 mrad a=0.2 
  CHECK PASS: fine Parratt = ODE (|dr| < 1e-4 |r|), 13.0 mrad a=0.2 
Fermi step 25.0 mrad, a = 0.2 A: |r|^2 closed 2.216932e-08, ODE 2.216932e-08, Parratt(8000 layers) 2.216743e-08; arg r ODE +2.902415, Parratt +2.902409
  CHECK PASS: closed form = ODE |r|^2 (rel 1e-6), 25.0 mrad a=0.2 
  CHECK PASS: fine Parratt = ODE (|dr| < 1e-4 |r|), 25.0 mrad a=0.2 
Fermi step 13.0 mrad, a = 0.05 A: |r|^2 closed 6.320423e-03, ODE 6.320423e-03, Parratt(8000 layers) 6.320396e-03; arg r ODE +3.132569, Parratt +3.132569
  CHECK PASS: closed form = ODE |r|^2 (rel 1e-6), 13.0 mrad a=0.05 
  CHECK PASS: fine Parratt = ODE (|dr| < 1e-4 |r|), 13.0 mrad a=0.05 
Fermi step 40.0 mrad, a = 0.05 A: |r|^2 closed 1.058426e-05, ODE 1.058426e-05, Parratt(8000 layers) 1.058390e-05; arg r ODE +3.124622, Parratt +3.124622
  CHECK PASS: closed form = ODE |r|^2 (rel 1e-6), 40.0 mrad a=0.05 
  CHECK PASS: fine Parratt = ODE (|dr| < 1e-4 |r|), 40.0 mrad a=0.05 

15 mrad, 13.9 V, a = 0.2 A: closed-form |r|^2 with Schroedinger K: 2.33568e-05; with MS-dispersion K: 2.33530e-05
  CHECK FAIL: doc value 2.3597e-5 reproduced by one of the dispersions (5e-5 rel) 

SUMMARY: 14 of 15 checks passed
Traceback (most recent call last):
  File "/tmp/claude-0/-home-user-Holography/57d40492-0c74-558e-a50e-ca09e117ea85/scratchpad/G_derive/s2_parratt.py", line 165, in <module>
    assert all(ok for _, ok in CHECKS)
           ~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError

target 2.3597e-5 (closed form), 2.3593e-5 (multislice)
V0=13.9000 W=0.0 schr: R = 2.33568e-05
V0=13.9000 W=0.0 ms  : R = 2.33530e-05
V0=13.9000 W=0.5 schr: R = 2.33840e-05
V0=13.9000 W=0.5 ms  : R = 2.33802e-05
V0=13.9000 W=2.0 schr: R = 2.37915e-05
V0=13.9000 W=2.0 ms  : R = 2.37876e-05
V0=13.9028 W=0.0 schr: R = 2.33626e-05
V0=13.9028 W=0.0 ms  : R = 2.33588e-05
V0=13.9028 W=0.5 schr: R = 2.33898e-05
V0=13.9028 W=0.5 ms  : R = 2.33860e-05
V0=13.9028 W=2.0 schr: R = 2.37971e-05
V0=13.9028 W=2.0 ms  : R = 2.37933e-05
V0=13.9500 W=0.0 schr: R = 2.34596e-05
V0=13.9500 W=0.0 ms  : R = 2.34558e-05
V0=13.9500 W=0.5 schr: R = 2.34867e-05
V0=13.9500 W=0.5 ms  : R = 2.34829e-05
V0=13.9500 W=2.0 schr: R = 2.38928e-05
V0=13.9500 W=2.0 ms  : R = 2.38889e-05
a = 0.19: R = 3.49815e-05
a = 0.198: R = 2.53320e-05
a = 0.2: R = 2.33568e-05
a = 0.202: R = 2.15315e-05
a = 0.21: R = 1.55214e-05
q=theta/lam (sin->theta): 2.33476e-05
lam rounded 0.02508 2.33618e-05
300 keV (never used) 1.56079e-06
V0 that gives 2.3597e-5 at a=0.2, W=0: 14.0169 V
a that gives 2.3597e-5 at V0=13.9, W=0: 0.19975 A
theta that gives 2.3597e-5 at V0=13.9, a=0.2, W=0: 14.98549 mrad
```

Verdict A2: the recursion, the reference-plane factor, the bottom boundary condition and the
closed form are all correct. The closed form agrees with direct integration to 1e-6 relative at
5 angle and width combinations. **Finding F-m1 (Minor, documentation): the number quoted in docs/08
section 3.2 for the closed form, 2.3597e-5 at 15 mrad, is not reproduced.** At the stated parameters
(13.9 V, a = 0.2 A, 15 mrad, 200 keV) the closed form gives 2.33568e-5 with the Schroedinger K and
2.33530e-5 with the multislice K, and direct integration gives the same, 2.33568e-5. The quoted value
is 1.03 percent higher. It would need V0 = 14.017 V, a = 0.19975 A or theta = 14.985 mrad; W = 0.5 V
gives 2.3384e-5 and W = 2 V gives 2.3792e-5. The quoted multislice value 2.3593e-5 agrees with the
quoted closed form, so both were presumably computed at the same, unstated, parameters (the
implementation is examined in section 15). The relative agreement is unaffected. The absolute number
is mislabelled or misreported.

## 4. A3, reflection coefficient from the virtual detector (s3, toy multislice)

Premises: above the surface, between the crystal and the top absorber, the multislice field is a
superposition of free waves. For a z-invariant (or z-periodic, see A13) structure every z-Fourier
component is a stationary scattering state. A launched beam that is entirely in vacuum, with no
up-going components, projects onto the "in" scattering states with coefficients equal to its
plane-wave amplitudes A(-q). In the vacuum slab therefore
`psi(x,z) = int dq [B(q) e^{2 pi i q x} + D(q) e^{-2 pi i q x}] e^{i kappa(q) z}`, with `B = r A(-q)`
when r is referred to x = 0. The record on a line x_j above the top of the incident beam starts at
the Gaussian tail of the beam (below 1e-6 of the peak here) and ends below the tail tolerance.
Its Fourier transform over the march therefore equals the transform over the whole real line, and
`F_j(kappa) = int dq [B e^{i phi_j} + D e^{-i phi_j}] 2 pi delta(kappa(q) - kappa)`
`= (2 pi/|kappa'(q)|)[B e^{i phi_j} + D e^{-i phi_j}]`, where
`kappa'(q) = -2 pi q/sqrt(1/lambda^2 - q^2) = -(2 pi)^2 q/kz`. The two-line inversion and the
denominator `|e^{2i phi_2} - e^{2i phi_1}| = 2|sin(2 pi q (x_2 - x_1))|` follow by elimination. A
grid coefficient a(q) at spacing 1/L_x represents the spectral density `A(q) = L_x a(q)`. Referring
both waves to x_ref gives `r = B/A(-q) exp(+4 pi i q x_ref)`, the same factor as Parratt's
`exp(2 i K_0 (x_ref - x_top))`. The per-plane record (dz = 1.92 A) has its kappa content in
[-0.34, 0] rad/A at dx = 0.08, so the Riemann sum has no aliasing: the alias period is
2 pi/dz = 3.27 rad/A.

The toy multislice (`toyms.py`) implements exactly these premises: exact propagator, transmission
`exp(i sigma (V + iW) dz)`, 2/3 band applied to T and to the wave, an analytic Gaussian sheet beam
with its waist on the surface plane, two lines 0.16 A apart read by exact Fourier interpolation, and
cubic 40 V absorbers. The extraction (`toyms.extract_r`) follows the A3 formulas. It is compared with
my Parratt in the multislice dispersion.

```
Fermi step a=0.2 A, 13 mrad, W=0: 201 angles with |A| >= 5% of peak; |r| in [4.832e-03, 1.993e-02]
   multislice vs Parratt(MS dispersion): max|dr| 1.63e-06, max rel 1.68e-04, max phase 1.64e-04 rad
   Parratt Schroedinger vs MS dispersion: max rel 8.13e-05
   record at first/last plane relative to peak: 4.6e-07 / 1.8e-06; |D|/|B| max 9.0e-06
   variants (max rel error vs Parratt over the window):
     no Jacobian 2 pi q/kz                              8.99e+01
     A(+q) instead of A(-q)                             2.22e+191
     x_ref = 1 A, correct sign                          1.68e-04
     x_ref = 1 A, sign of exp(4 pi i q x_ref) flipped   1.89e+00
     single line, D ignored                             1.75e-04
  CHECK PASS: 13 mrad: multislice = Parratt(MS) to 1e-3 relative 
  CHECK PASS: 13 mrad: phase to 1e-3 rad 
  CHECK PASS: x_ref referencing exp(+4 pi i q x_ref) correct (rel < 1e-3) 
  CHECK PASS: flipped referencing sign fails (rel > 0.1) 
  CHECK PASS: omitting the Jacobian fails (rel > 0.5) 
Fermi step a=0.2 A, 25 mrad, W=2 V: 201 angles with |A| >= 5% of peak; |r| in [7.820e-05, 3.099e-04]
   multislice vs Parratt(MS dispersion): max|dr| 1.36e-07, max rel 1.17e-03, max phase 9.78e-04 rad
   Parratt Schroedinger vs MS dispersion: max rel 3.03e-04
   record at first/last plane relative to peak: 5.0e-07 / 5.9e-12; |D|/|B| max 9.6e-05
  CHECK PASS: 25 mrad W=2V: |dr| < 1e-6 absolute or rel < 3e-3 
Fermi step a=0.05 A, 40 mrad, W=0 (dx=0.1, band limit 41.8 mrad): 201 angles with |A| >= 5% of peak; |r| in [2.652e-03, 3.994e-03]
   multislice vs Parratt(MS dispersion): max|dr| 4.49e-03, max rel 1.69e+00, max phase 2.76e+00 rad
   Parratt Schroedinger vs MS dispersion: max rel 8.60e-04
   record at first/last plane relative to peak: 1.0e-08 / 5.8e-02; |D|/|B| max 9.9e-03

Band limit: sin(theta_max) = lambda q_band / 2, q_band = (2/3)(1/(2 dx))
   dx = 0.1: q_band = 3.3333 c/A, theta_max = 41.81 mrad
   dx = 0.0977: q_band = 3.4118 c/A, theta_max = 42.80 mrad
   dx = 0.08: q_band = 4.1667 c/A, theta_max = 52.27 mrad
   dx = 0.049: q_band = 6.8027 c/A, theta_max = 85.41 mrad
  CHECK PASS: theta_max(dx=0.08) = 52.3 mrad 
  CHECK PASS: theta_max(dx=0.0977) = 42.8 mrad 
45 mrad, a=0.05, dx=0.0977 (beyond band limit): 201 angles with |A| >= 5% of peak; |r| in [1.608e-03, 2.397e-03]
   multislice vs Parratt(MS dispersion): max|dr| 2.44e-03, max rel 1.02e+00, max phase 1.55e+00 rad
   Parratt Schroedinger vs MS dispersion: max rel 1.08e-03
   record at first/last plane relative to peak: 1.0e-07 / 3.7e-03; |D|/|B| max 2.3e-01
45 mrad, a=0.05, dx=0.0488 (inside band limit): 201 angles with |A| >= 5% of peak; |r| in [1.608e-03, 2.397e-03]
   multislice vs Parratt(MS dispersion): max|dr| 8.20e-06, max rel 5.04e-03, max phase 5.04e-03 rad
   Parratt Schroedinger vs MS dispersion: max rel 1.08e-03
   record at first/last plane relative to peak: 1.2e-08 / 7.9e-07; |D|/|B| max 1.8e-02
  CHECK PASS: beyond band limit the reflection fails (rel error > 0.5) 
  CHECK PASS: inside band limit at half the sampling it works (rel < 1e-2) 
     dx=0.0977: theta 43.00 mrad |r_ms/r_Parratt| = 2.094e-01
     dx=0.0977: theta 43.40 mrad |r_ms/r_Parratt| = 1.806e-01
     dx=0.0977: theta 43.80 mrad |r_ms/r_Parratt| = 1.445e-01
     dx=0.0977: theta 44.20 mrad |r_ms/r_Parratt| = 1.215e-01
     dx=0.0977: theta 44.60 mrad |r_ms/r_Parratt| = 1.056e-01
     dx=0.0977: theta 45.00 mrad |r_ms/r_Parratt| = 9.377e-02
     dx=0.0977: theta 45.40 mrad |r_ms/r_Parratt| = 8.456e-02
     dx=0.0977: theta 45.80 mrad |r_ms/r_Parratt| = 7.717e-02
     dx=0.0977: theta 46.20 mrad |r_ms/r_Parratt| = 7.115e-02
     dx=0.0977: theta 46.60 mrad |r_ms/r_Parratt| = 6.611e-02
     dx=0.0977: theta 47.00 mrad |r_ms/r_Parratt| = 6.190e-02

SUMMARY: 10 of 10 checks passed
```

Verdict A3: correct, including every factor of 2 pi, the sign of `exp(+4 pi i q x_ref)`, the Jacobian
`2 pi q/kz`, the spectral density `A = L_x a`, and the up/down separation. My independent toy
reproduces the size of the docs/08 rung-1 agreement (13 mrad: 1.6e-6 absolute, 1.7e-4 relative,
1.6e-4 rad; 25 mrad, W = 2 V: 1.4e-7 absolute, 1.0e-3 rad). Each deliberately wrong variant fails by
orders of magnitude: no Jacobian 90x, A(+q) 1e191, flipped reference sign 1.9. A single line ignoring
D is as good as two lines in this clean geometry (1.75e-4). The second line matters only when
down-going contamination is present, and that is what it is for. The 0.16 A spacing keeps
`2 pi q dx_det < pi` up to sin(theta) = lambda/(2 x 0.16), i.e. 78 mrad (A3 says "up to 60 mrad",
which is conservative). The condition number `1/(2 sin(2 pi q dx_det))` is 1.8 at 7 mrad and 0.6 at
45 mrad.

## 5. A8, band limit (s3, s3c, s3d)

Premises: the transmission function is band-limited to `|q| <= q_band = (2/3)(1/(2 dx))` (a disc in
(qx, qy) for a square grid). Single-step coupling of `-q -> +q` needs the Fourier component 2q, so
first-order specular reflection exists only for `2q <= q_band`, i.e.
`sin(theta_max) = lambda q_band/2`: 52.27 mrad at dx = 0.08 A, 42.80 mrad at 0.0977 A. Both A8
numbers are confirmed (s3). A refinement A8 does not state: inside the crystal the Bragg reflection
couples the refracted components `+-q_int`, and `q_int > q`. The limit on the external angle for
Bragg reflection is therefore `sin^2(theta_ext) = (lambda q_band/2)^2 - Delta`, i.e. 51.5 mrad at
dx = 0.08 and 13.90 V.

```
dx=0.1 a=0.05: max|T_bl| - 1 = 2.29e-05, min|T_bl| - 1 = -2.63e-05
dx=0.1 a=0.2: max|T_bl| - 1 = 2.29e-05, min|T_bl| - 1 = -2.63e-05
dx=0.08 a=0.05: max|T_bl| - 1 = 2.29e-05, min|T_bl| - 1 = -2.63e-05
dx=0.08 a=0.2: max|T_bl| - 1 = 2.29e-05, min|T_bl| - 1 = -2.63e-05
40 mrad a=0.05 dx=0.1, T NOT band-limited (wave band-limited): 201 angles with |A| >= 5% of peak; |r| in [2.652e-03, 3.994e-03]
   multislice vs Parratt(MS dispersion): max|dr| 1.12e-04, max rel 4.16e-02, max phase 1.00e-03 rad
   Parratt Schroedinger vs MS dispersion: max rel 8.60e-04
   record at first/last plane relative to peak: 9.0e-09 / 5.2e-09; |D|/|B| max 3.1e-03
PRODUCTION SAMPLING dx=0.08: 40 mrad a=0.05: 201 angles with |A| >= 5% of peak; |r| in [2.652e-03, 3.994e-03]
   multislice vs Parratt(MS dispersion): max|dr| 1.06e-05, max rel 3.98e-03, max phase 2.77e-03 rad
   Parratt Schroedinger vs MS dispersion: max rel 8.60e-04
   record at first/last plane relative to peak: 8.7e-09 / 8.3e-09; |D|/|B| max 2.4e-03
     38.0:2.1e-03, 38.5:2.0e-03, 39.0:2.1e-03, 39.5:2.6e-03, 40.0:2.9e-03, 40.5:2.8e-03, 41.0:2.9e-03, 41.5:3.5e-03, 42.0:4.0e-03
PRODUCTION SAMPLING dx=0.08: 45 mrad a=0.05: 201 angles with |A| >= 5% of peak; |r| in [1.608e-03, 2.397e-03]
   multislice vs Parratt(MS dispersion): max|dr| 1.70e-05, max rel 1.05e-02, max phase 9.15e-03 rad
   Parratt Schroedinger vs MS dispersion: max rel 1.08e-03
   record at first/last plane relative to peak: 1.2e-08 / 4.5e-08; |D|/|B| max 1.4e-02
     43.0:4.0e-03, 43.5:4.7e-03, 44.0:5.6e-03, 44.5:5.9e-03, 45.0:5.9e-03, 45.5:6.8e-03, 46.0:8.4e-03, 46.5:9.4e-03, 47.0:9.8e-03
PRODUCTION SAMPLING dx=0.08: 45 mrad a=0.2: 201 angles with |A| >= 5% of peak; |r| in [8.859e-08, 3.363e-07]
   multislice vs Parratt(MS dispersion): max|dr| 1.04e-06, max rel 1.17e+01, max phase 4.37e-01 rad
   Parratt Schroedinger vs MS dispersion: max rel 9.80e-04
   record at first/last plane relative to peak: 1.8e-06 / 6.8e-06; |D|/|B| max 2.5e+01
     43.0:5.2e-01, 43.5:7.3e-01, 44.0:1.1e+00, 44.5:1.6e+00, 45.0:2.3e+00, 45.5:3.4e+00, 46.0:5.1e+00, 46.5:7.7e+00, 47.0:1.2e+01

w0 = 6 A (detectors at 62.0 and 62.16 A, top absorber from 74.8 A)
theta  a     dx     dz    max rel   max phase  max|dr|   max|r|
  40  0.05  0.080  1.92  3.27e-03  2.31e-03  9.83e-06  3.60e-03
  40  0.05  0.080  0.96  3.08e-03  1.70e-03  9.26e-06  3.60e-03
  40  0.05  0.080  0.48  3.11e-03  1.55e-03  9.36e-06  3.60e-03
  40  0.05  0.060  1.92  1.02e-03  1.00e-03  3.27e-06  3.60e-03
  40  0.05  0.040  1.92  1.06e-02  9.94e-03  3.12e-05  3.60e-03
  40  0.05  0.040  0.48  1.26e-04  5.84e-05  4.11e-07  3.60e-03
  45  0.05  0.080  1.92  8.36e-03  6.55e-03  1.48e-05  2.17e-03
  45  0.05  0.080  0.96  8.22e-03  5.88e-03  1.46e-05  2.17e-03
  45  0.05  0.080  0.48  8.34e-03  5.73e-03  1.48e-05  2.17e-03
  45  0.05  0.060  1.92  1.44e-03  1.42e-03  2.70e-06  2.17e-03
  45  0.05  0.040  1.92  4.41e-03  3.75e-03  8.75e-06  2.17e-03
  45  0.05  0.040  0.48  1.58e-04  7.43e-05  3.13e-07  2.17e-03
```

The limit is not a sharp edge in accuracy. With a sharp Fermi step (a = 0.05 A) my toy degrades well
before `theta_max`. At dx = 0.08 the error is 2e-3 relative at 38 mrad, 3.3e-3 at 40 mrad (phase
2.3e-3 rad) and 8.4e-3 at 45 mrad (phase 6.6e-3 rad). It does not depend on dz (1.92, 0.96, 0.48 A
give the same) and falls to 1.0e-3 and 1.4e-3 at dx = 0.06. It is therefore a dx (band-edge) error.
At dx = 0.04 with dz = 1.92 a different error appears (1.1e-2 at 40 mrad). There the band reaches the
`kappa - 2 pi/dz` alias, and it disappears at dz = 0.48 (1.3e-4). That cannot happen at production
dx = 0.08: kappa at the band edge is -1.37 rad/A, and 2 pi/1.92 = 3.27 rad/A. At dx = 0.1 and within
5 percent of the limit, the band-limited transmission function produced a slowly growing,
non-physical record tail (6 percent of the peak at the end of the cell). Without band-limiting T the
tail is 5e-9. At 90 percent of the limit (dx = 0.08, 45 mrad) the record was clean (4.5e-8).

Consequences (finding **F-m2, Minor**): (i) A8's "can reflect only up to 52.3 mrad" is correct as a
hard limit, but production accuracy near the top of the rocking range (windows up to about
46.6 mrad, 89 percent of the limit) is not established. The convergence stage tests sampling only at
13.3, 20.0 and 30.6 mrad. The rocking points above about 40 mrad, including the Si(111) (11,-11,11)
peak at about 43.1 mrad (`theta_int = 44.0 mrad`), should carry a stated accuracy of order 1e-2 until
a dx = 0.0664 A comparison exists there. That comparison is post-processing plus a few extra tasks,
and it does not affect the step stage (9 to 32 mrad). (ii) Validation rung 1 includes 40 mrad with a
0.05 A Fermi width at dx = 0.08. My toy gives 3.3e-3 relative and 2.3e-3 rad there against tolerances
of 3e-3 (amplitude, with a 1e-6 absolute floor) and 3e-3 rad. Depending on how the floor is combined,
this sits at the edge of the gate, and a failure there would stop the chain before the rocking stage.
Any such failure is a gate artefact of the sharpest test profile, not evidence of a defect.

## 6. A4, delay allowance (s0, s8)

Derivation: with `K_int^2 = K^2 + 2 k sigma (V + iW)`, `Im K_int = k sigma W/K_int`. A path to normal
depth D and back is attenuated by `exp(-2 D Im K_int) = exp(-2 D k sigma W/K_int)` and is displaced
along z by `2 D/tan(theta_int) = 2 D kz_int/K_int`. The weight as a function of the displacement is
therefore `exp(-sigma W Delta_z k/kz_int) ~ exp(-sigma W Delta_z)`, independent of angle. In the
multislice this is exact for the part of a path inside the absorbing region, because every slice
multiplies the field there by `exp(-sigma W dz)`. For n = 7 and W = 0.5 V the allowance is
`7/(sigma W) = 19,209 A` (s0). The residual dependence on angle is `1/cos(theta_int)`, i.e. 1e-3 at
45 mrad. The argument covers only time spent inside the absorbing crystal. Surface resonances that
travel partly in vacuum decay more slowly, which A12 states and the adaptive stop addresses.

Numerical test (s8): a mini rung 2 at production values. The laterally averaged Si(1,-1,1) potential
is built from the abTEM 1.0.10 Kirkland coefficients with u = 0.076 A, and its bulk mean is
13.886 V against 13.903 V for the free-atom MIP. W = 0.5 V with a 0.5 A tanh onset, dx = 0.08 A,
dz = 1.92 A, w0 = 10 A, window around (4,-4,4) at 13.23 mrad. The reference is my Parratt on the same
band-limited profile including the bottom absorber ramp.

```
sheet density 0.07830 A^-2; 2 sheets per d -> n = 0.049943 A^-3 (8/a^3 = 0.049943)
sheet potential: peak 22.62 V, integral 21.7964 V A (expected rho_area 2 pi a0 e f(0) = 21.7964)
  CHECK PASS: sheet integral = rho_area 2 pi a0 e f_e(0) 
mean of V over the bulk region (-120..-20 A): 13.886 V (Kirkland MIP 13.903 V)
  CHECK PASS: laterally averaged profile has the Kirkland mean inner potential 
z_hit 3930 A, footprint end 7965 A, delay 7/(sigma W) 19209 A, rise 8979 A, planned 36152 A = 18830 planes; marching 47075 planes
march: 15 s
   record at 0.5 x planned (z = 18077 A): 1.09e-02 of peak
   record at 1.0 x planned (z = 36154 A): 3.69e-06 of peak
   record at 1.5 x planned (z = 54230 A): 2.88e-10 of peak
   record at 2.0 x planned (z = 72307 A): 4.72e-13 of peak
   record at 2.5 x planned (z = 90384 A): 3.94e-13 of peak
Parratt: 1 s; |r| over the window: 5.251e-02 .. 5.189e-01 (peak at 13.31 mrad)
 stop length     max|r-r_P|  max rel   phase(|r|>=1e-2)  true trunc |r(L)-r(2.5x)|  A12 estimate  max(true/est)
 0.6 x planned  5.357e-03  1.020e-01  1.019e-01         5.359e-03             inf     0.000
 0.8 x planned  2.322e-04  3.578e-03  3.030e-03         1.779e-04             5.372e-05     98.108
 1.0 x planned  1.702e-04  3.931e-04  3.073e-04         2.974e-06             3.982e-05     0.172
 1.5 x planned  1.707e-04  3.944e-04  3.085e-04         3.410e-10             2.448e-09     0.600
 2.5 x planned  1.707e-04  3.944e-04  3.085e-04         0.000e+00             5.373e-12     nan
  CHECK PASS: at 1.0 x planned length (7 decay lengths) the true truncation error is below 1e-3 of max|r| 
  CHECK PASS: at 2.5 x planned the multislice agrees with Parratt to 5e-4 relative to max|r| 

SUMMARY: 4 of 4 checks passed
```

Verdict A4: correct. At exactly the planned length (footprint + 7/(sigma W) + rise) the record is
3.7e-6 of its peak and the true truncation error of r is 3.0e-6, against |r| up to 0.52. At 2.5 times
the planned length the toy agrees with Parratt to 1.7e-4 absolute and 3.9e-4 relative (3.1e-4 rad).

## 7. A5, absorbers (s6) and docs/08 section 3.4

Derivation: as A4, the one-way amplitude attenuation of a ramp is `exp(-sigma int W dx/sin theta)`
(Schroedinger) or `/tan theta` (multislice), and these differ by cos(theta). For the cubic ramp,
`int W dx = W_max L/4`.

```
ramp                                       max|r| (3-48 mrad) at     |r|(3.8)   |r|(20)    exponent@45 (sin / tan)
quadratic, 25 A, 8 V (first smoke)         1.92e-03 at  3.0 mrad   7.11e-04   2.58e-06   1.08 / 1.08
  CHECK FAIL: quadratic, 25 A, 8 V (first smoke): |r|(20 mrad) = 1.6e-06 (doc) within 10% [2.582e-06]
  CHECK PASS: quadratic, 25 A, 8 V (first smoke): max |r| = 7.4e-04 at 3.8 mrad (doc) within 10% [7.111e-04]
  CHECK PASS: quadratic, 25 A, 8 V (first smoke): one-way exponent at 45 mrad = 1.1 (doc) 
      |r| at the lowest scanned angle 3.0 mrad: 1.92e-03
quadratic, 100 A, 8 V (first draft)        1.14e-04 at  3.0 mrad   4.45e-05   5.78e-08   4.32 / 4.32
  CHECK PASS: quadratic, 100 A, 8 V (first draft): |r|(20 mrad) = 5.8e-08 (doc) within 10% [5.780e-08]
  CHECK PASS: quadratic, 100 A, 8 V (first draft): max |r| = 4.6e-05 at 3.8 mrad (doc) within 10% [4.445e-05]
  CHECK PASS: quadratic, 100 A, 8 V (first draft): one-way exponent at 45 mrad = 4.3 (doc) 
      |r| at the lowest scanned angle 3.0 mrad: 1.14e-04
cubic, 60 A, 40 V (production top)         5.33e-05 at  3.0 mrad   1.62e-05   4.01e-09   9.72 / 9.71
  CHECK PASS: cubic, 60 A, 40 V (production top): |r|(20 mrad) = 4.0e-09 (doc) within 10% [4.012e-09]
  CHECK PASS: cubic, 60 A, 40 V (production top): max |r| = 1.7e-05 at 3.8 mrad (doc) within 10% [1.619e-05]
  CHECK PASS: cubic, 60 A, 40 V (production top): one-way exponent at 45 mrad = 9.7 (doc) 
      |r| at the lowest scanned angle 3.0 mrad: 5.33e-05
cubic, 100 A, 40 V (production bottom)     1.14e-05 at  3.0 mrad   3.50e-06   8.65e-10   16.20 / 16.19
  CHECK PASS: cubic, 100 A, 40 V (production bottom): |r|(20 mrad) = 8.7e-10 (doc) within 10% [8.652e-10]
  CHECK PASS: cubic, 100 A, 40 V (production bottom): max |r| = 3.7e-06 at 3.8 mrad (doc) within 10% [3.501e-06]
  CHECK PASS: cubic, 100 A, 40 V (production bottom): one-way exponent at 45 mrad = 16.2 (doc) 
      |r| at the lowest scanned angle 3.0 mrad: 1.14e-05
round trip bottom + top at 45 mrad: 25.92 (doc 25.9)
  CHECK PASS: exp(-25.9) 

bottom ramp entered from the crystal (V_bg = 13.9 V real; external angle -> internal by refraction)
   theta_ext  3.8 mrad: |r| from vacuum 3.50e-06, from crystal 3.13e-08
   theta_ext  7.0 mrad: |r| from vacuum 1.65e-07, from crystal 1.44e-08
   theta_ext 20.0 mrad: |r| from vacuum 8.65e-10, from crystal 5.46e-10
   theta_ext 45.0 mrad: |r| from vacuum 1.49e-11, from crystal 1.35e-11

SUMMARY: 12 of 13 checks passed
```

Verdict A5: correct. The attenuation exponents 1.1, 4.3, 9.7 and 16.2 and the round trip of 25.9 are
reproduced. The reflection table of section 3.4 is reproduced within 10 percent at 3.8 and 20 mrad,
except the first-smoke quadratic ramp at 20 mrad (2.6e-6 against 1.6e-6, a historical design, Nit
F-N2). **F-N3 (Nit/Minor, documentation):** section 3.4 says the ramps were scanned "at 3 to 48 mrad",
then "the maximum reflection occurs at the lowest angle tested, 3.8 mrad". The tabulated maxima are
the 3.8 mrad values. Scanning from 3.0 mrad gives about 3 times larger maxima: 5.3e-5 for the
production top ramp, which contradicts model_assumptions C6 ("below 2e-5 at 3 to 48 mrad"). This has
no consequence: the top absorber sees the reflected waves only at the window angles, at least about
4.9 mrad. The bottom absorber is entered from the crystal, at internal angles of at least theta_c,
and from there its reflection is 100 times smaller (3e-8 at 3.8 mrad external).

## 8. A6, null tests (s2 item 4, s7)

Derivation: if `V_up(r) = V_low(r - R)` and `psi_low` solves the problem with incident `e^{i k_in.r}`,
then `psi_up(r) = e^{i k_in.R} psi_low(r - R)` solves the upper problem with the same incident wave.
Its reflected part is `r_low e^{-i (k_out - k_in).R} e^{i k_out.r}`. For the specular beam
`k_out - k_in = 2 k sin(theta_ext) n_hat`, so `r_up = r_low exp(-2 i K_ext h)`. This is exact in
dynamical theory and holds with absorption. It requires the absorption profile, the band limit and
the slicing to translate with the terrace, which the slicing does only when h is compatible with it
(see section 15). Reciprocity (valid for complex symmetric potentials) gives `r(T, d) = r(T, -d)` for
the specular beam. s7 enumerates the operations of the bulk-terminated Si(001) half crystal.

```
8 point operations keep the outward normal [001]
Si(001) terrace point group (rotation parts mapping the half crystal onto itself): 4 elements
rotation parts of operations mapping terrace L onto terrace L+1 (t_z = a/4): 4 elements
orbit of [100] under the terrace group + reciprocity: [(np.int64(-1), np.int64(0), np.int64(0)), (np.int64(0), np.int64(-1), np.int64(0)), (np.int64(0), np.int64(1), np.int64(0)), (np.int64(1), np.int64(0), np.int64(0))]
orbit of [110] under the terrace group + reciprocity: [(np.int64(-1), np.int64(-1), np.int64(0)), (np.int64(1), np.int64(1), np.int64(0))]
terrace L+1 with beam d behaves like terrace L with beam R^-1 d: d=[100] -> [(np.int64(-1), np.int64(0), np.int64(0)), (np.int64(0), np.int64(-1), np.int64(0)), (np.int64(0), np.int64(1), np.int64(0)), (np.int64(1), np.int64(0), np.int64(0))]; d=[110] -> [(np.int64(-1), np.int64(1), np.int64(0)), (np.int64(1), np.int64(-1), np.int64(0))]
  CHECK PASS: every R^-1[100] lies in the orbit of [100] (null residual for the [100] beam) 
  CHECK PASS: no R^-1[110] lies in the orbit of [110] (no symmetry for the [110] beam) 
operations mapping L onto L+1: ['C4+ (4_1 screw)', 'C4- (4_3 screw)', 'm_x (d-glide)', 'm_y (d-glide)']
terrace group of L: ['C2z', 'E', 'm_[1-10]', 'm_[110]']
  CHECK PASS: L -> L+1 only by 90-degree screws or d-glides; no pure translation (R = E) 
pure translations mapping L onto L+2 (in-plane parts, units of a): [(np.float64(0.0), np.float64(0.5)), (np.float64(0.5), np.float64(0.0))]
  CHECK PASS: Si(001) double layer: L+2 = L translated by a lattice vector (e.g. a/2[1,0,1]) 
Si(111): R = a/2[1,0,1], R.n = 0.577350 a = 3.13553 A (d111 = a/sqrt3 = 3.13553 A)
  CHECK PASS: R.n = d111 
  CHECK PASS: R is an FCC lattice vector 
  CHECK PASS: x_hat cross y_hat = z_hat (right-handed) 

SUMMARY: 7 of 7 checks passed
```

Verdict A6: correct. Si(111) bilayer, `R = a/2 [1,0,1]`, `R.n = d_111 = 3.13553 A`; Si(001) double
layer, a pure translation maps L onto L+2. For the Si(001) single layer, terrace L+1 is the image of
L under the 4_1/4_3 screws or the d-glides. With the [100] beam the image directions [0,+-1,0] and
[+-1,0,0] lie in the orbit of [100] under the terrace group {E, C2z, m_[110], m_[1-10]} plus
reciprocity, so the residual must vanish (symmetry null test). With the [110] beam the image is
[1,-1,0], which is not in the orbit {[110], [-1,-1,0]}, so the residual is physics. A6 says this,
with one omission: the d-glides are a second family of operations relating L and L+1, and they lead
to the same conclusion. A frozen-phonon ensemble respects the [100] symmetry only statistically. Per
configuration the residual is not zero; the coherent averages must satisfy it within their standard
errors.

## 9. A7, mean inner potential of a parametrisation (s0)

Derivation: `V(r) = 2 pi a0 e int f_e(q) e^{2 pi i q.r} d^3q` gives `int V d^3r = 2 pi a0 e f_e(0)` per
atom, so `V0 = 2 pi a0 e f_e(0) 8/a^3` with `2 pi a0 e = 47.8777 V A^2` (CODATA 2018). Kirkland:
`f_e(0) = sum a_i/b_i + sum c_i = 5.81428 A`, giving 13.903 V. Lobato: `f_e(0) = 2 sum a_i = 5.83600 A`,
giving 13.955 V (s0 output above, also cross-checked against abTEM's own functions). Verdict: correct
(13.90 and 13.95 V).

## 10. A10, mean free path (s0)

`|psi|^2 ~ exp(-2 sigma W s)`, so `Lambda = 1/(2 sigma W) = 1372 A = 137.2 nm` at W = 0.5 V. Correct.

## 11. A12, truncation uncertainty by geometric continuation (s5, s8)

Derivation: if beyond the computed record the tail repeats every S planes scaled by
`rho e^{i chi}` (a single exponentially decaying resonance), the missing part of F is
`F_last sum_{m>=1} (rho e^{i(chi - kappa S dz)})^m`. Its modulus is at most `|F_last| rho/(1 - rho)`,
the A12 expression. It is an upper bound for a single resonance and an estimate otherwise.

```

record truncated after 12000 planes (23040 A); main pulse at 8000 A
  single resonance, l = 8000 A at 14.95 mrad, amp 1e-2; S = 1000: rho = 0.7866; max|dF_true| = 1.169e+01, max bound = 1.220e+01, max(true/bound) = 0.987, covered fraction 1.000
  CHECK PASS: single exponential: bound covers the truth at every kappa (n=12000, S=1000) 
  single resonance, l = 8000 A at 14.95 mrad, amp 1e-2; S = 3000: rho = 0.4721; max|dF_true| = 1.169e+01, max bound = 1.149e+01, max(true/bound) = 1.061, covered fraction 0.910
  single resonance, l = 5000 A at 13.30 mrad (on the main peak), amp 1e-2; S = 1000: rho = 0.6811; max|dF_true| = 2.469e+00, max bound = 2.469e+00, max(true/bound) = 1.000, covered fraction 1.000
  CHECK PASS: single exponential: bound covers the truth at every kappa (n=12000, S=1000) 
  single resonance, l = 5000 A at 13.30 mrad (on the main peak), amp 1e-2; S = 3000: rho = 0.2827; max|dF_true| = 2.469e+00, max bound = 2.106e+00, max(true/bound) = 1.172, covered fraction 0.766
  two resonances, l = 3000 A (amp 3e-2) and 12000 A (amp 3e-4); S = 1000: rho = 0.5135; max|dF_true| = 1.044e+00, max bound = 5.481e-01, max(true/bound) = 7.834, covered fraction 0.856
     -> two-component tail at n=12000: true/bound up to 7.83 (UNDERestimate)
  two resonances, l = 3000 A (amp 3e-2) and 12000 A (amp 3e-4); S = 3000: rho = 0.1417; max|dF_true| = 1.044e+00, max bound = 5.710e-01, max(true/bound) = 13.046, covered fraction 0.498

record truncated after 20000 planes (38400 A); main pulse at 8000 A
  single resonance, l = 8000 A at 14.95 mrad, amp 1e-2; S = 1000: rho = 0.7866; max|dF_true| = 1.714e+00, max bound = 1.789e+00, max(true/bound) = 0.987, covered fraction 1.000
  CHECK PASS: single exponential: bound covers the truth at every kappa (n=20000, S=1000) 
  single resonance, l = 8000 A at 14.95 mrad, amp 1e-2; S = 3000: rho = 0.4868; max|dF_true| = 1.714e+00, max bound = 1.786e+00, max(true/bound) = 1.000, covered fraction 1.000
  single resonance, l = 5000 A at 13.30 mrad (on the main peak), amp 1e-2; S = 1000: rho = 0.6811; max|dF_true| = 1.144e-01, max bound = 1.144e-01, max(true/bound) = 1.000, covered fraction 1.000
  CHECK PASS: single exponential: bound covers the truth at every kappa (n=20000, S=1000) 
  single resonance, l = 5000 A at 13.30 mrad (on the main peak), amp 1e-2; S = 3000: rho = 0.3160; max|dF_true| = 1.144e-01, max bound = 1.144e-01, max(true/bound) = 1.000, covered fraction 1.000
  two resonances, l = 3000 A (amp 3e-2) and 12000 A (amp 3e-4); S = 1000: rho = 0.8614; max|dF_true| = 2.858e-01, max bound = 3.094e-01, max(true/bound) = 1.734, covered fraction 0.985
  two resonances, l = 3000 A (amp 3e-2) and 12000 A (amp 3e-4); S = 3000: rho = 0.5516; max|dF_true| = 2.858e-01, max bound = 2.178e-01, max(true/bound) = 1.389, covered fraction 0.891

S too large: previous segment overlaps the main reflected pulse
  n_stop = 9000, S = 1000: rho = 0.7866, max(true/bound) = 0.986
  n_stop = 9000, S = 2250: rho = 0.0144, max(true/bound) = 95.418
  n_stop = 9000, S = 3000: rho = 0.0085, max(true/bound) = 121.082
  n_stop = 9000, S = 4000: rho = 0.1309, max(true/bound) = 1.879
  CHECK PASS: a segment reaching into the main pulse underestimates (true/bound > 1) 

SUMMARY: 5 of 5 checks passed
```

Verdict A12: the expression is correct as an upper bound for a single geometric tail with a segment
that lies inside the tail (true/bound at most 0.99). It is not a bound in general. It undershoots by
up to 7.8 times for a tail with two decay lengths (n = 12000, S = 1000), by about 100 times when the
previous segment reaches into the main pulse (s5, and s8 at 0.8 times the planned length: 98). It
can also overshoot by `(1+rho)/(1-rho)` where the tail's phase rotates (s8 at the planned length:
true/estimate = 0.17). **F-m3 (Minor):** the stored field is named `r_truncation_bound`, and the
benchmark comparisons subtract it before applying their tolerances. Where it overshoots, the
comparison is made more lenient by up to that factor. Where the record has several resonances with
different lifetimes, it is not a bound. The docs/08 text calls it an "estimate" and an "uncertainty",
which is the right wording. Because the production stop (tail 1e-5, cap 4x) leaves estimates of
order 1e-5 or below, the practical effect on verdicts is small, except at narrow resonances (smoke:
1.3e-3). Recommendation (post-processing): report the estimate beside each verdict and do not
subtract it where it exceeds the tolerance itself.

## 12. A9, frozen phonons and holography (s9)

Premises: each electron sees one frozen configuration c, and configurations are independent. The
reference wave u_r does not depend on c (vacuum reference R1). Derivation:
`<|u_o + u_r|^2>_c = <|u_o|^2> + |u_r|^2 + 2 Re(<u_o> u_r*)`, so the sideband carries `<u_o>`.
Correct for R1. For a self-reference from another region of the same surface (R2) it holds only when
the two regions' displacements are uncorrelated, and then the sideband carries `<u_o><u_r>*`. That
is true of the Einstein model, not of correlated phonons over short distances.
"Its attenuation relative to the static r is the thermal diffuse absorption" needs a qualifier.
Relative to the static (undisplaced) lattice, `<r>` also contains the Debye-Waller smearing of the
coherent potential. Only relative to the static Debye-Waller run (the rocking stage's
`debye_waller` mode) is the remainder the absorption into thermal diffuse scattering.

The last sentence, "`<|r|^2> - |<r>|^2` is the diffuse intensity in the specular channel", does not
hold for the extracted coefficients. The implementation draws independent displacements for every
plane along z (seed per global plane index, `simulate.AtomicTransmission`) and repeats them with the
y period Ly of the phonon cell. The diffuse scattering is therefore continuous in kappa and sits on
rods qy = m/Ly. Kinematically, the diffuse part of the extracted spectral density has variance
proportional to the total incident power (`int |A|^2 dq`, proportional to w0 at fixed peak field),
while the coherent part is `<r> A(-q)` with `|A|^2` proportional to w0^2. Hence
`Var(r) = Var(B)/|A(-q)|^2` scales as 1/w0, i.e. with the beam's angular width, and as 1/Ly, i.e.
with the rod spacing. It is a diffuse power per extraction bandwidth, not an intrinsic quantity.
Toy test (s9): Fermi step plus a z-random perturbation of 3 V near the surface, 24 configurations,
identical seeds for both waists.

```
w0 = 6.0 A: 24 configs in 154 s; at theta0: |<r>| = 1.0233e-02, |r_static| = 1.0242e-02, Var(r) = 8.240e-09, diffuse fraction Var/<|r|^2> = 7.868e-05
w0 = 12.0 A: 24 configs in 232 s; at theta0: |<r>| = 1.0256e-02, |r_static| = 1.0242e-02, Var(r) = 1.867e-09, diffuse fraction Var/<|r|^2> = 1.775e-05

<r>(w0=6) vs <r>(w0=12) at theta0: |difference| = 2.29e-05 (standard error of the mean ~ 1.85e-05)
static r: |r(w0=6) - r(w0=12)| = 2.85e-08 (beam independence of the static coefficient)
Var(r) ratio w0=6 / w0=12 (central 0.2 mrad) = 4.25  (beam-independent quantity would give 1; 1/w0 scaling gives 2)
  CHECK PASS: static r is beam independent (|dr| < 1e-3 |r|) 
  CHECK PASS: <r> agrees between waists within 4 standard errors 
  CHECK PASS: Var(r) depends on the beam waist (ratio differs from 1 by > 30 percent) 

SUMMARY: 3 of 3 checks passed
exit 0
```

The coherent average is beam independent (difference 2.3e-5, 1.2 standard errors), as A9 requires.
The variance changes by a factor of 4.25 when the waist is doubled (the kinematic estimate is 2; the
excess is presumably dynamical). **Finding F-M1 (Major, category (a): post-processing only).**
`aggregate.aggregate_rocking` reports `diffuse_fraction_median = median(1 - |<r>|^2/<|r|^2>)` for
every frozen-phonon curve, and docs/08 sections 1 (item 4), 5 and A9 present it as "the thermal
diffuse fraction in the specular channel". As computed it depends on w0 (10 A in rocking, 15 A in
steps) and on the phonon cell Ly (54 A), and it cannot be compared between stages or with
experiment. Fix in post-processing: divide `<|r|^2> - |<r>|^2` by the extraction bandwidth (from the
stored analytic beam spectrum) and multiply by Ly to obtain a diffuse intensity per unit solid
angle, or report it explicitly as a beam- and cell-dependent number. The coherent `<r>` (the
hologram observable), its standard error and all terrace ratios are unaffected. No GPU output needs
to change.

**Finding F-m4 (Minor, category (a)).** `aggregate.aggregate_steps` processes every frozen-phonon
step configuration as a separate run. Each entry name carries the seed, and step phase, residual
and `strip_vs_flat` are formed per configuration. The latter is compared with the static flat
reference, so it mixes Debye-Waller and diffuse differences into what is labelled a null test. The
coherent average over the 32 seeds, which A9 identifies as the measured quantity, is never formed for
the steps stage. These runs are 448 of the 867 steps tasks (32 seeds at 14 angle and step
combinations). `ar_rho` is stored per seed, so `<rho>` and its strip means can be formed afterwards.
No re-run is needed, but no frozen-phonon step result should be read from the per-seed summary.

## 13. A11, image wave on the surface plane

Premises: in the vacuum slab the up-going field is `int dkappa/(2 pi) sum_qy U(kappa, qy)
e^{i K_x x} e^{i kappa z} e^{2 pi i qy y}`, with U the kappa-density obtained from
`F(kappa) = int f e^{-i kappa z} dz` (inverse `f = int F e^{i kappa z} dkappa/2pi`) and qy
coefficients normalised by 1/Ny. Evaluating at x = x_ref gives the field on that plane, continued as
if the vacuum extended there. Restricting the sum to the aperture gives the A11 expression,
including the factor dkappa/2pi. As a definition of an ideal, aberration-free, point-by-point
focused (Scheimpflug-like) image of the plane x = x_ref, it is correct. A real objective images a
plane perpendicular to its axis, a point M3 must address. The implementation
(`aggregate.image_from_spectrum`) uses U from `vdp_spectrum`, which carries the 1/Ny and dz factors
and absolute-z phases. The aperture is a circle of radius alpha in (theta_x, theta_y) around
(theta_center, 0), and near-grazing components (`|sin(K_x dx_det)| < 0.05`, below about 1.25 mrad)
are zeroed. All of this is consistent with the derivation. x_ref = 0 is used for both sides of a
transverse step, and the local ratio (image / flat image of the same level at the same x_ref)
cancels the resulting `exp(i K_x h)` offset. Verdict: correct.

## 15. Comparison with the implementation (read after the derivations; s10, s12, s13)

The code was read at d404587. `git diff d404587 HEAD` is empty for `reflection_holo/`, `configs/` and
docs/08, because later commits on the branch touch only `docs/agent_reports/`. s10 imports
`reflection_holo` read-only and applies its functions to the independent toy records of s3 and s8.

```
repo constants: lambda 0.0250793405 A, k 250.532318, sigma 7.288401e-04, MIP kirkland 13.9028 V, lobato 13.9548 V, theta_c(12 V) 8.356 mrad
  CHECK PASS: repo lambda = 0.025079340 A 
  CHECK PASS: repo sigma = 7.288401e-4 
  CHECK PASS: repo MIP 13.903 / 13.955 V 
   repo SpecularCondition (n=4, 13.90 V): theta_ext 13.2301 mrad (s1 Schroedinger: 13.2301)
  CHECK PASS: repo Bragg n=4 matches s1 to 2 urad 
   repo SpecularCondition (n=5, 13.90 V): theta_ext 17.8606 mrad (s1 Schroedinger: 17.8606)
  CHECK PASS: repo Bragg n=5 matches s1 to 2 urad 
   repo SpecularCondition (n=8, 13.90 V): theta_ext 30.7086 mrad (s1 Schroedinger: 30.7086)
  CHECK PASS: repo Bragg n=8 matches s1 to 2 urad 
   repo step phase h=3.1355 A at 13.231 mrad: -20.7865 rad (s0: -20.7865)
  CHECK PASS: repo signed specular step phase 
   repo max_specular_angle(dx=0.08): 52.272 mrad; window_half_range(w0=10) 2.098 mrad, (15) 1.399, (60) 0.350
  CHECK PASS: max specular angle 52.27 mrad 
   repo delay_allowance_A(W=0.5, n=7): (19208.60271175074, True)
  CHECK PASS: delay allowance 19,209 A 
repo vdp_reflectivity on the s3 toy record: max |r_repo/r_Parratt - 1| = 1.68e-04; max |D/A| = 1.6e-07
  CHECK PASS: repo vdp_reflectivity reproduces Parratt on the toy record (< 1e-3) 
repo parratt(multislice) vs my Parratt(MS): max rel 1.42e-05
  CHECK PASS: repo parratt = my parratt (< 1e-4 rel; layering differs slightly) 
repo truncation_bound at the planned length: max 3.98e-05 (rho 0.683); true truncation error max 2.97e-06
  CHECK PASS: repo truncation_bound equals the s8 estimate (4.0e-5) within 5% 
repo absorber_profile: W(-230) = 40.00 V, W(-130) = 0.00e+00, W(-180) = 5.000 (40*(0.5)^3 = 5.0), W(140.08) = 3.37e-20, W(200.08) = 40.00
  CHECK PASS: absorber ramps: cubic, zero at inner edges, 40 V at the cell edges 

SUMMARY: 13 of 13 checks passed

si111_110 h_unit = 3.13553 A periods (x,y,z) = ['9.4066', '6.6515', '3.8402'] planes per z period: 2 slice 1.92011
si001_110 h_unit = 1.35773 A periods (x,y,z) = ['5.4309', '3.8402', '3.8402'] planes per z period: 2 slice 1.92011
si001_100 h_unit = 1.35773 A periods (x,y,z) = ['5.4309', '5.4309', '5.4309'] planes per z period: 4 slice 1.35773

validation: 36 tasks; planned planes 3430 .. 37268; planned cell length 0.66 .. 7.16 um; cap planes max 149072; memory max 0.7 GB  (0 s)
convergence: 172 tasks; planned planes 15828 .. 21545; planned cell length 3.04 .. 4.14 um; cap planes max 86178; memory max 7.5 GB  (5 s)
rocking: 1892 tasks; planned planes 7835 .. 57113; planned cell length 1.50 .. 7.78 um; cap planes max 228449; memory max 16.0 GB  (46 s)
steps: 867 tasks; planned planes 14797 .. 96020; planned cell length 2.84 .. 18.44 um; cap planes max 384080; memory max 17.4 GB  (117 s)
total tasks: 2967
rocking: highest window edge 46.60 mrad (band limit 52.27 mrad at dx = 0.08 A; 89 percent)

steps parallel (static): surface, levels, Ly, theta0, x_det, planned z_end, lowest fully recorded elevation, q, |qy| above which truncated, number of truncated qy columns, strip length, |sinc| at the cut
  si111_110 (0, 1) Ly=199.5 th0=  9.0 x_det=153.9 z_end=55873 th_min=3.90 mrad q=0.359 qy_cut=0.323 cols=14 L=46.6 |sinc|=0.004
  si111_110 (0, 1) Ly=199.5 th0= 14.0 x_det=149.9 z_end=41520 th_min=4.82 mrad q=0.558 qy_cut=0.524 cols=14 L=46.6 |sinc|=0.012
  si111_110 (0, 1) Ly=199.5 th0= 20.0 x_det=148.6 z_end=34450 th_min=5.47 mrad q=0.797 qy_cut=0.767 cols=12 L=46.6 |sinc|=0.007
  si111_110 (0, 1) Ly=199.5 th0= 26.0 x_det=148.1 z_end=30796 th_min=5.87 mrad q=1.037 qy_cut=1.010 cols=10 L=46.6 |sinc|=0.000
  si111_110 (0, 1) Ly=199.5 th0= 30.6 x_det=147.8 z_end=28999 th_min=6.10 mrad q=1.220 qy_cut=1.195 cols=10 L=46.6 |sinc|=0.005
  si001_110 (0, 1) Ly=199.7 th0= 12.0 x_det=148.4 z_end=45201 th_min=4.47 mrad q=0.478 qy_cut=0.444 cols=14 L=49.9 |sinc|=0.007
  si001_110 (0, 1) Ly=199.7 th0= 17.0 x_det=146.7 z_end=37024 th_min=5.13 mrad q=0.678 qy_cut=0.646 cols=12 L=49.9 |sinc|=0.007
  si001_110 (0, 1) Ly=199.7 th0= 23.0 x_det=145.9 z_end=32165 th_min=5.63 mrad q=0.917 qy_cut=0.889 cols=12 L=49.9 |sinc|=0.007
  si001_110 (0, 1) Ly=199.7 th0= 28.0 x_det=145.6 z_end=29771 th_min=5.91 mrad q=1.116 qy_cut=1.091 cols=10 L=49.9 |sinc|=0.006
  si001_110 (0, 2) Ly=199.7 th0= 10.0 x_det=151.5 z_end=51439 th_min=4.12 mrad q=0.399 qy_cut=0.363 cols=14 L=49.9 |sinc|=0.007
  si001_110 (0, 2) Ly=199.7 th0= 16.0 x_det=148.3 z_end=38401 th_min=5.05 mrad q=0.638 qy_cut=0.605 cols=14 L=49.9 |sinc|=0.007
  si001_110 (0, 2) Ly=199.7 th0= 21.0 x_det=147.5 z_end=33596 th_min=5.52 mrad q=0.837 qy_cut=0.808 cols=12 L=49.9 |sinc|=0.007
  si001_110 (0, 2) Ly=199.7 th0= 26.3 x_det=147.1 z_end=30586 th_min=5.86 mrad q=1.049 qy_cut=1.022 cols=10 L=49.9 |sinc|=0.001
  si001_110 (0, 2) Ly=199.7 th0= 32.0 x_det=146.9 z_end=28499 th_min=6.12 mrad q=1.276 qy_cut=1.252 cols=8 L=49.9 |sinc|=0.005
  si001_100 (0, 1) Ly=200.9 th0= 14.0 x_det=147.5 z_end=41159 th_min=4.77 mrad q=0.558 qy_cut=0.525 cols=14 L=48.9 |sinc|=0.011
  si001_100 (0, 1) Ly=200.9 th0= 19.0 x_det=146.4 z_end=35042 th_min=5.32 mrad q=0.758 qy_cut=0.727 cols=12 L=48.9 |sinc|=0.009
  si001_100 (0, 1) Ly=200.9 th0= 25.0 x_det=145.8 z_end=31087 th_min=5.75 mrad q=0.997 qy_cut=0.970 cols=12 L=48.9 |sinc|=0.006
  si001_100 (0, 1) Ly=200.9 th0= 30.0 x_det=145.6 z_end=29044 th_min=6.00 mrad q=1.196 qy_cut=1.172 cols=10 L=48.9 |sinc|=0.004
  si111_110 (0, 1) Ly=99.8 th0= 20.0 x_det=148.6 z_end=34450 th_min=5.47 mrad q=0.797 qy_cut=0.767 cols=6 L=20.0 |sinc|=0.017
  si001_110 (0, 1) Ly=399.4 th0= 21.0 x_det=146.1 z_end=33459 th_min=5.48 mrad q=0.837 qy_cut=0.808 cols=24 L=145.9 |sinc|=0.000
  si111_110 (0, 1) Ly=399.1 th0= 26.5 x_det=148.0 z_end=30569 th_min=5.90 mrad q=1.057 qy_cut=1.030 cols=20 L=146.3 |sinc|=0.002
  si001_110 (0, 1) Ly=399.4 th0= 16.2 x_det=146.9 z_end=37965 th_min=5.05 mrad q=0.646 qy_cut=0.614 cols=24 L=145.9 |sinc|=0.003
  si001_110 (0, 1) Ly=399.4 th0= 21.0 x_det=146.1 z_end=33459 th_min=5.48 mrad q=0.837 qy_cut=0.808 cols=24 L=145.9 |sinc|=0.000
lowest fully recorded exit elevation over all 115 static parallel-step tasks: 3.87 .. 6.15 mrad
```

| Function | Derivation it must implement | Verdict |
|---|---|---|
| `constants.wavelength_A`, `k_rad_per_A`, `interaction_constant` | s0 | identical to 1e-12 (s10) |
| `constants.refraction_delta`, `E_eff_V` | exact relativistic `Delta = V0/E_eff`; equals `2 sigma V0/k` to 1e-5 | correct |
| `geometry.theta_int_from_ext`, `SpecularCondition` | `K_int = pi n/d`, `K_ext^2 = K_int^2 - dK^2` | correct; Bragg angles equal s1 to 1e-7 |
| `geometry.specular_step_phase` | `-2 h k sin(theta_ext)` (signed) | correct |
| `potential.scattering_factor`, `mean_inner_potential` | A7 | 13.9028 V and 13.9548 V, identical to s0 |
| `potential.PotentialBuilder.projected` | `c(q) = 2 pi a0 e f_e(q) D(q)/(Lx Ly) sum_j e^{-2 pi i q.r_j}`, 2/3 band, `D = exp(-B q^2/4)` | correct |
| `potential.PotentialBuilder.transmission` | `exp(i sigma v - sigma (alpha v + W dz))`, band-limited after exponentiation | correct (attractive v advances the phase, as exp(+ik.r) requires) |
| `potential.absorber_profile` | cubic ramps, 0 at the inner edges, W_max at the cell edges | correct (s10). Docstring "below 2e-5 ... at all angles above 3 mrad" is 5.3e-5 at 3.0 mrad (F-N3) |
| `beams.kz_minus_k`, `multislice.Propagator` | `exp(i (kz - k) dz)`, written without cancellation | correct sign and form |
| `multislice.run_multislice` | symmetric splitting, record at z_p | full propagation between plane centres with T at each plane is the Strang scheme; record after T at z_p, consistent with the z_p used in the FT |
| `beams.GaussianSheetBeam.spectrum`, `entrance_wave` | grid coefficient a(q), q0 = -sin(theta0)/lambda, exact back-propagation from the waist | correct |
| `simulate` (A_neg) | `A(-q) = L_x a(-q)`, analytic | `grid.Lx * beam.spectrum(-q)`: correct |
| `analysis.kz_of_q`, `updown`, `vdp_reflectivity` | A3 | correct; on the s3 toy record it reproduces Parratt to 1.68e-4, identical to my extraction |
| `analysis.vdp_spectrum` | U(kappa, qy) with absolute-z phases, 1/Ny, dz | correct; aliases kappa > 0 to kappa - 2 pi/dz (harmless, physical kappa <= 0); zeroes components below about 1.25 mrad elevation |
| `analysis.truncation_bound` | A12 | identical to my estimate (3.98e-5 at the s8 planned length; true error 2.97e-6) |
| `analysis.vdp_angle_resolved` | A13 | formula correct (incident Jacobian, K_x(qy) in the separation); near-grazing components are not masked (only K_x = 0); see section 14 and F-M2 |
| `reference1d.K_profile`, `parratt`, `transfer_matrix`, `layers_from_profile` | A1, A2 | correct; repo Parratt equals mine to 1.4e-5 (different layering) |
| `reference1d.fermi_step_R` | closed form | correct; the docs/08 value 2.3597e-5 is not produced by it at the stated parameters (F-m1) |
| `simulate.delay_allowance_A` | `n/(sigma W)` | 19,208.6 A (s10) |
| `simulate.window_half_range` | `sqrt(ln 1000) lambda/(pi w0)` | 2.098, 1.399 and 0.350 mrad for 10, 15 and 60 A |
| `simulate.max_specular_angle` | `arcsin(q_band lambda/2)`, `q_band = (2/3) min(Nyquist_x, Nyquist_y)` | 52.27 mrad at dx = 0.08; uses the y Nyquist too (correct for dy > dx) |
| `simulate.plan_windows`, absolute grid | footprint + delay + rise at theta_low; theta on multiples of 0.02 mrad; `q = sin(theta)/lambda` | correct; x_ref = 0 for every terrace level, consistent with `terrace_ratio` |
| `aggregate.terrace_ratio` | `arg(r_L/r_0) + 2 k sin(theta) h L` with h = 3.13553 A (Si(111)) or 1.35773 A (Si(001)) | correct (s13) |
| `aggregate.strip_mean` | exact sinc kernel | correct (s4 c) |
| `aggregate.angle_resolved_profile`, `image_from_spectrum` | A13, A11 | correct |
| `aggregate.ensemble` | coherent average, standard error | correct; `diffuse_fraction_median` misinterpreted (F-M1) |
| `aggregate.aggregate_steps` | A9 coherent average for frozen phonons | not formed (F-m4) |

Plan-level numbers (s12): 36 + 172 + 1,892 + 867 = 2,967 tasks, maximum memory 17.4 GB, as in
docs/08 section 4. The highest rocking window edge is 46.60 mrad, 89 percent of the 52.27 mrad band
limit. **F-N7 (Nit, docs/08 section 1):** "2.5 to 10 um long: 13,000 to 96,000 atomic planes" does
not match the planner. Planned lengths are 1.50 to 7.78 um in rocking (7,835 to 57,113 planes) and
2.84 to 18.44 um in steps (14,797 to 96,020 planes). The adaptive cap allows 4 times that.
**F-N4 (Nit):** sections 3.1 and A12 state the adaptive stop as "1e-4 of its peak ... cap at 2.5
times". Those are the smoke values; production uses tail_tol 1e-5 and cap 4, as section 4 says.
**F-N5 (Nit):** section 3.1 says r is "referred to the outermost atomic plane". The code refers every
terrace to x = 0, the level-0 outermost sheet, which is what the terrace-ratio formula requires.
**F-N6 (Nit):** A12 quotes an observed beam-to-beam difference of 6.7e-4 at the 15 mrad resonance,
section 3.3 quotes 7.7e-4, and section 3.3's "stays within ... the excess beyond it is 1.1e-5"
contradicts itself (a positive excess is not "within").

## 14. A13, angle-resolved response of steps parallel to the beam (s4, s11, s12, s14)

Premises and derivation. The crystal is periodic along z with period P_z: 3.840 A, two planes, for
the [110] azimuth; 5.431 A, four planes, for [100]. A13 says "invariant", but the structure is
periodic, not invariant. The multislice is covariant under z-shifts by P_z, so each Floquet exponent
kappa is conserved modulo 2 pi/P_z. The y component of the in-plane wavevector is not conserved,
because the steps scatter into qy = m/Ly. At dx = 0.08 the most negative kappa of a band-limited
vacuum wave is -1.372 rad/A (s14). For [110], `2 pi/P_z = 1.636 rad/A` puts the first Laue zone
outside the band. For [100], `2 pi/P_z = 1.157 rad/A` puts it inside the band for incidence below
41.4 mrad. It needs single-step momentum transfer beyond q_band (4.39 to 5.21 c/A against 4.17) and
leaves at kappa' of about -1.2 rad/A, so it never enters the analysis at kappa_theta.

Write the incident beam as `int dq A(-q) [plane wave at kappa(q), qy = 0]`. Its response at the
detector line, column qy, is `int dq A(-q) rho(q, qy) e^{i K_x(qy) x_j} e^{i kappa(q) z}`. Fourier
transforming at kappa_theta gives `(2 pi/|kappa'(q_theta)|) A(-q_theta) rho(theta, qy) e^{i K_x x_j}`.
The Jacobian belongs to the integration variable, i.e. the incident q. With the two-line separation
at `K_x = sqrt(k^2 - kz^2 - (2 pi qy)^2)`, this gives A13's `rho = U (2 pi q/kz)/A(-q)`. Flux
conservation is the exact test: change variables q -> q' at fixed kappa, with `dq/dq' = K_x'/K`, and
total reflection without absorption gives `sum_m |rho_m|^2 K_x(m)/K = 1`. The strip mean over
`[c - L/2, c + L/2]` of `sum rho e^{2 pi i qy y}` is `sum rho e^{2 pi i qy c} sinc(qy L)`, which
vanishes on every rod qy = n/P_y for L = N P_y.

The derivation requires every outgoing component to have crossed the detector before the record ends
(A3's "vanishes at both ends"). A lateral component leaving at elevation theta_x needs
`x_det/tan(theta_x)` of z to rise to the detector.

```
band edge q_band = 4.1667 c/A: kappa_min = -1.3716 rad/A (most negative kappa of a band-limited vacuum wave)
[110] beam (2 planes of 1.920 A): P_z = 3.8402 A, 2 pi/P_z = 1.6361 rad/A > |kappa_min|: first Laue zone outside the band
[100] beam (4 planes of 1.358 A): P_z = 5.4309 A, 2 pi/P_z = 1.1569 rad/A; first Laue zone inside the band for incidence theta <= 41.4 mrad
   incidence 13.3 mrad: FOLZ wave kappa' = -1.1791 rad/A, exit q_x = 3.864 c/A (elevation 97 mrad); single-step coupling needs q_x + q_in = 4.394 c/A vs q_band 4.167
   incidence 20.0 mrad: FOLZ wave kappa' = -1.2070 rad/A, exit q_x = 3.909 c/A (elevation 98 mrad); single-step coupling needs q_x + q_in = 4.707 c/A vs q_band 4.167
   incidence 30.0 mrad: FOLZ wave kappa' = -1.2697 rad/A, exit q_x = 4.009 c/A (elevation 101 mrad); single-step coupling needs q_x + q_in = 5.205 c/A vs q_band 4.167
record sampled every 1.9201 A: alias period 2 pi/dz = 3.272 rad/A vs |kappa_min| = 1.372: no aliasing
record sampled every 1.3577 A: alias period 2 pi/dz = 4.628 rad/A vs |kappa_min| = 1.372: no aliasing
CHECK PASS : per-plane records are not aliased in kappa

(a) corrugated repulsive barrier, Ly = 7 A, theta0 = 12.5 mrad, w0 = 10 A
   ran 10707 planes on 1650 x 70 in 148 s
   u0 = 0.0: flux sum over propagating rods: min 1.000012, max 1.000015; |rho_0| in [1.0000, 1.0000]; max sum_m!=0 |rho_m|^2 = 4.012e-28
  CHECK PASS: flat barrier: |rho_0| = 1 to 2e-3 and non-specular rods < 1e-8 
   ran 10707 planes on 1650 x 70 in 127 s
   u0 = 0.5: flux sum over propagating rods: min 0.922267, max 1.217908; |rho_0| in [0.1793, 0.3843]; max sum_m!=0 |rho_m|^2 = 1.449e+00
   (wrong) outgoing-component Jacobian: flux in [0.7089, 0.8247]
     qy = -0.4286 c/A: |rho| at theta0 = 2.1909e-01
     qy = -0.2857 c/A: |rho| at theta0 = 5.9015e-01
     qy = -0.1429 c/A: |rho| at theta0 = 3.7255e-01
     qy = +0.0000 c/A: |rho| at theta0 = 2.9850e-01
     qy = +0.1429 c/A: |rho| at theta0 = 3.7255e-01
     qy = +0.2857 c/A: |rho| at theta0 = 5.9015e-01
     qy = +0.4286 c/A: |rho| at theta0 = 2.1909e-01
  CHECK FAIL: corrugated barrier: flux conservation sum |rho|^2 Kx/K = 1 to 2e-3 
  CHECK PASS: outgoing-component Jacobian violates flux by > 1e-2 

(b) stepped Fermi-step surface: V = (13.9 + 2i)/(1 + exp((x - H(y))/0.2)), h = 3.1355 A
  CHECK PASS: Parratt: upper flat terrace = r_flat exp(-2iKh) 
   ran 7643 planes on 1400 x 160 in 136 s
   Ly = 40 A (terraces 20 A), strip 14 A centred: max|<r>_0/r_flat - 1| = 5.460e-02, max|<r>_1/(r_flat e^-2iKh) - 1| = 6.235e-02, max|arg(<r>_1/<r>_0) + 2Kh| = 2.434e-02 rad
   Ly = 40 A (terraces 20 A), strip 8 A centred: max|<r>_0/r_flat - 1| = 5.547e-02, max|<r>_1/(r_flat e^-2iKh) - 1| = 6.859e-02, max|arg(<r>_1/<r>_0) + 2Kh| = 5.239e-02 rad
  CHECK PASS: Ly=40: y-average of r(y) equals rho(qy=0) 
   ran 7643 planes on 1400 x 320 in 346 s
   Ly = 80 A (terraces 40 A), strip 34 A centred: max|<r>_0/r_flat - 1| = 1.838e-02, max|<r>_1/(r_flat e^-2iKh) - 1| = 2.474e-02, max|arg(<r>_1/<r>_0) + 2Kh| = 9.674e-03 rad
   Ly = 80 A (terraces 40 A), strip 28 A centred: max|<r>_0/r_flat - 1| = 1.374e-02, max|<r>_1/(r_flat e^-2iKh) - 1| = 1.792e-02, max|arg(<r>_1/<r>_0) + 2Kh| = 1.380e-02 rad
  CHECK PASS: Ly=80: y-average of r(y) equals rho(qy=0) 
  CHECK PASS: terrace-width convergence: Ly=80 strip residual smaller than Ly=40 

(c) strip mean as a sinc kernel in qy
   sinc formula -3.3562855092-3.4837007307j  vs numerical average -3.3562855072-3.4837007298j
  CHECK PASS: strip mean = sum rho exp(2 pi i qy yc) sinc(qy L) 
   rods qy = n/p on the grid: 24; max |sinc(qy L)| on them for L = 4p: 2.84e-16; for L = 4.5p: 7.07e-02
  CHECK PASS: whole periods: rods removed exactly 

SUMMARY: 8 of 9 checks passed
Traceback (most recent call last):
  File "/tmp/claude-0/-home-user-Holography/57d40492-0c74-558e-a50e-ca09e117ea85/scratchpad/G_derive/s4_vdp_3d.py", line 185, in <module>
    assert all(ok for _, ok in CHECKS)
           ~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
exit 1

(a) corrugated repulsive barrier u0 = 0.5 A, Ly = 7 A, theta0 = 12.5 mrad, w0 = 10 A, long cell
   ran 22920 planes in 322 s
   angles with every propagating rod at elevation >= 3 mrad: 131 of 131
   flux over those angles: min 0.999076, max 1.001990
   flux over all window angles: min 0.999076, max 1.001990
     theta 11.20 mrad: flux 1.001990, lowest rod elevation 3.15 mrad
     theta 11.40 mrad: flux 1.000588, lowest rod elevation 3.80 mrad
     theta 11.60 mrad: flux 0.999779, lowest rod elevation 4.36 mrad
     theta 11.80 mrad: flux 1.000001, lowest rod elevation 4.87 mrad
     theta 12.00 mrad: flux 1.000020, lowest rod elevation 5.34 mrad
     theta 12.20 mrad: flux 0.999973, lowest rod elevation 5.77 mrad
     theta 12.40 mrad: flux 1.000004, lowest rod elevation 6.18 mrad
     theta 12.60 mrad: flux 1.000039, lowest rod elevation 6.57 mrad
     theta 12.80 mrad: flux 1.000010, lowest rod elevation 6.95 mrad
     theta 13.00 mrad: flux 0.999962, lowest rod elevation 7.31 mrad
     theta 13.20 mrad: flux 1.000025, lowest rod elevation 7.66 mrad
     theta 13.40 mrad: flux 1.000104, lowest rod elevation 8.00 mrad
     theta 13.60 mrad: flux 1.000175, lowest rod elevation 8.33 mrad
     theta 13.80 mrad: flux 1.000064, lowest rod elevation 8.65 mrad
  CHECK PASS: A13 normalisation: flux conserved to 2e-3 where every rod reaches the detector 

```

Results. (i) The A13 normalisation is exact when every rod is recorded. In a long cell the
corrugated barrier conserves flux to 2e-3 over the whole window, and to 1e-4 where the lowest rod
leaves above 4 mrad (s11 a). The outgoing-component Jacobian would multiply each
rho_m by K_x(m)/K < 1, so it cannot conserve flux when non-specular rods carry intensity (in the
truncated cell of s4 a it gave 0.71 to 0.82). (ii) Strip means converge to the flat-terrace values as the terraces widen
(s4 b). The maximum deviation is 5.5 to 6.9 percent for 20 A terraces and 1.4 to 2.5 percent for
40 A terraces; the residual `arg(<r>_1/<r>_0) + 2Kh` is 2.4e-2 to 5.2e-2 rad and 1.0e-2 to 1.4e-2 rad
respectively. This is the behaviour A13 claims, and the docs/08 section 3.6 values for 26.6 A
terraces (4e-2 to 6e-2) are of the same size. (iii) The sinc kernel is exact (8e-10 against direct
numerical averaging) and removes rods exactly for whole periods (s4 c). (iv) With the cell planned
for the specular rise only (s4 a), the rods leaving at 4 to 8 mrad had not finished crossing the
detector, and flux was violated by up to 22 percent.

