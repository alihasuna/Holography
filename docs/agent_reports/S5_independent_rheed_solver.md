# S5: an independent dynamical reflection solver for the flat Si(001) rocking curve (amplitude and phase)

Agent S5, 2026-09-23. Written incrementally; the final state is the summary at the end (section 9).
Branch `claude/electron-holography-orchestration-nakd7r` (HEAD `de9aa2d` at start). Nothing committed or
pushed by S5. Beam energy 200 keV throughout (PROJECT_INPUT item 1; 300 keV is never used).

Task (orchestrator): docs/05 section 4.4 asks for "a flat-surface rocking curve against a dynamical
solver" and states that intensity agreement is not sufficient: the reflection PHASE must be compared.
(1) provenance of sim-trhepd-rheed, trhepd-opt (the P49 fork) and the P49 code; (2) build in scratch;
(3) run the specular (0,0,8) rocking curve of flat bulk-terminated Si(001) at 200 keV, 12-22 mrad,
azimuths exact [100] and [110], without absorption and with an absorption comparable to the engine's
TEST_ONLY r = 0.1; (4) compare with the repository's engine in `tools/validation/rheed_solver_compare.py`.

Evidence labels: SECTION_READ (code or document read, with file:line at the recorded commit),
REPRODUCED (executed here; command and output recorded), DERIVED_HERE, ASSUMPTION, TEST_ONLY,
UNVERIFIED, MEASURED_HERE (a number from the repository's UNVALIDATED engine in this container).

Terminology used below: "sim-trhepd-rheed" is the ENGINE (Fortran programs bulk.exe and surf.exe);
its ALGORITHM is Ichimiya's surface-parallel multislice (transfer matrices of thin slices parallel to
the surface, combined by the recursive reflection-matrix technique); "trhepd-opt" is the P49
authors' repository containing a modified copy of the engine with a different ODE ALGORITHM (P49:
Runge-Kutta or splitting integrators with right-hand-side transformation); there is no Python
interface or wrapper for either. The repository's own engine is `reflection_holo.forward.multislice`
(Peng-Cowley-type forward multislice with slices perpendicular to the BEAM, report M2).

## 0. Log

- 22:15 UTC: read docs/05 4.3, 4.4, 9, 9.1; L2 section D (rows D1-D20, D-I1 to D-I4, E33);
  D_software_provenance headings and its sections 5.3-5.4 on RHEED; M2 (all); H2 sections 0-7;
  physics_conventions; the engine (`engine.py`, `potentials.py`, `analysis.py`, `illumination.py`,
  `propagator.py`, `grid.py`), `forward/cell.py` (layout), `structure/si001.py` (back-bond rule) and
  `tools/hpc/supercell_sizing.py` (flat strip and specular read-out, H2 `--measure`).
- 22:17 UTC: cloned both repositories into
  `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/rheed_solver/`
  (section 1.1); read the upstream Fortran listed in section 1.2 in full.
- 22:24 UTC: no Fortran compiler in the container; `apt-get install -y --no-install-recommends
  gfortran` (as root; exit 0) installed GNU Fortran (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0. Nothing
  else was installed.

## 1. Provenance and what the solver computes

### 1.1 Versions, commits, licences (REPRODUCED: `git ls-remote`, `git clone`, `sha256sum`, 2026-09-23)

| Item | Value | Label |
|---|---|---|
| upstream engine | `https://github.com/sim-trhepd-rheed/sim-trhepd-rheed`, branch `main` = HEAD `d98d6252f6be2c9da450d980251f04556ff2e75b` (2023-05-16, "Update strfac.f90", T. Hanada); tags `v1.0` = `63181db8`, `v1.0.2` = `b8305658`; other branches `add-license-1` `5b05a7ae`, `dev2022` `d018d7da`, `rwork_for_zgeev` `df61124c` | REPRODUCED (`git ls-remote`) |
| P49 `orig` | commit `df61124c` (2021-10-19) is the tip of branch `rwork_for_zgeev` and an ancestor of `main`; `main` differs from it by 125 files (src: `scpot.f90`, `strfac.f90`, `surfio.f90`, `bulkio.f90`, `asf.f90` and others rewritten in 2022-2023, the "v.5:2022/1" headers) | REPRODUCED (`git merge-base --is-ancestor`, `git diff --stat`) |
| version used here | `main` at `d98d625` (the current upstream; newer than both tags and than P49's `orig`) | DERIVED_HERE |
| upstream licence | `LICENSE` = GNU GPL version 3 (SHA-256 `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`); the manual says "distributed under GNU General Public License version 3 (GPL v3)" (`docs/html/_sources/index.rst.txt:44-46`) | SECTION_READ |
| citation request | README: cite Hanada, Motoyama, Yoshimi, Hoshi, Comput. Phys. Commun. 277, 108371 (2022) and, if possible, Hanada, Daimon, Ino, Phys. Rev. B 51, 13320 (1995); based on Ichimiya, Jpn. J. Appl. Phys. 22, 176 (1983) (`README.md:5-13`) | SECTION_READ |
| P49 fork | `https://github.com/shuheikudo/trhepd-opt`, HEAD `dc394bac5fb9d7d55865b853da733c72edd0c1a3` (2023-08-02); the same commit L2 read (its `sim-trhepd-rheed/src/surf.f90` SHA-256 `4d887cd7...` and `str-orig/src/surf.f90` `16c93b37...` equal L2 D.1 and D19b) | REPRODUCED |
| P49 fork licence | four `LICENSE` files (`sim-trhepd-rheed/`, `str-orig/`, `str-orig-plus/`, `str-lapack/`), all byte-identical to upstream's GPL-3 file (same SHA-256); README: "See the LICENSE file for each folder. Scripts under test folder are public domain." | REPRODUCED / SECTION_READ (`trhepd-opt/README.md`) |
| "P49 code" | the P49 data statement points to trhepd-opt (L2 D18); no other P49 code exists to fetch | SECTION_READ (L2) |
| repository metadata | the GitHub REST API is blocked for this session ("GitHub access to this repository is not enabled"); release pages were therefore not read; the tag list comes from `git ls-remote` | REPRODUCED |
| Python interface / wrapper | none in either repository (the `tool/` scripts are a Gaussian convolution of the output and a DFT input generator) | SECTION_READ (`README.md:31-37`) |
| build used here | gfortran 13.3.0, upstream `src/Makefile` (`FC = gfortran`, `FCFLAGS=-O3`, the bundled reference LAPACK `zgeev.f zgeevb.f`) | section 2 |

GPL-3.0 code is NOT copied into this repository: the build, the inputs and the patch live in the
scratch directory; this report contains only a short diff (section 2.2) as the orchestrator allowed.

SHA-256 of the upstream files read in full (commit `d98d625`): `bulkm.f90` `d8b30f12...`, `bulkio.f90`
`4a2d8987...`, `bulk.f90` `736b6d16...`, `bulksub.f90` `f483749a...`, `trmatg.f90` `9ec62902...`,
`gcmi.f90` `c10c9d5c...`, `scpot.f90` `0be2bd8b...`, `asf.f90` `bb8fdfaf...` (header, the Si rows and
the selection logic), `strfac.f90` `011346f2...` (lines 1-80), `surfm.f90` `c4e0c84a...`, `surf.f90`
`aca9d8ed...`, `surfio.f90` `2965dc1d...`, `surfsub.f90` `73a4af04...`, `Makefile` `2f718b45...`,
manual source `docs/html/_sources/index.rst.txt` `9dcb1b40...`.

### 1.2 What sim-trhepd-rheed computes (SECTION_READ at `d98d625` unless labelled otherwise)

| # | Fact | Locator | Label |
|---|---|---|---|
| F1 | Equation solved: `(Delta + K^2 - q U(r)) Psi = 0`, q the sign of the particle, U complex "owing to the inelastic effect", built from the atomic positions and "atomic scattering factors corrected by mean-square displacements" | manual `index.rst.txt:132-139` | SECTION_READ |
| F2 | Particle switch: `ep='P'` (positron) is the DEFAULT in `bulkm.f90:21` and `surfm.f90:12`; RHEED needs `ep='E'` in both (and in `U0.f90`) before compiling; `inegpos=0` for electrons (`bulkm.f90:23-24`); for positrons the real potential is negated (`scpot.f90:159-161`) | README "Mode switching"; `index.rst.txt:105-124` | SECTION_READ |
| F3 | Geometry: z perpendicular to the surface, "the region z -> infinity is the vacuum region"; bulk unit of thickness CC with atoms at 0 <= z < CC; the potential of a unit includes the atoms of the units directly below and above (`-CC <= z < 0`, `CC <= z < 2 CC`) and nothing further | `index.rst.txt:202-204, 433-437`; `bulkio.f90:192-200`, `surfio.f90:186-196` | SECTION_READ |
| F4 | Beams: the user lists the rods (IH/NH, IK/NK) of the 2D reciprocal lattice; only those rods are coupled; each rod carries the full z dependence (all l of a bulk reflection (h,k,l) on that rod) | `index.rst.txt:248-282`; `bulksub.f90:78-116`, `surfsub.f90:9-40` | SECTION_READ |
| F5 | Method: per slice of thickness dz the potential is taken constant in z at the slice CENTRE (`scpot.f90:133-156`, `zi=dz*0.5d0+zo` then `zi=zi+dz`); the beam Hamiltonian `H_ii = U_0 + iU'_0 + Gamma_i^2`, `H_ji = U(g_j - g_i) + iU'(g_j - g_i)`, `H_ij = conj(U - iU')` (`trmatg.f90:24-27`) is diagonalised by LAPACK `zgeev` (`:31`); the slice transfer matrix is `M D M^-1` with eigen-wavenumbers `x2 = sqrt(eigenvalue)` (principal root, `:38`), `D = diag(exp(+i x2 dz), exp(-i x2 dz))` (`:39-40`) and mode vectors `((Gamma_i + x2) X; (Gamma_i - x2) X)` (`:45-50`), where `Gamma_i = sqrt(K^2 - |k_par + G_i|^2)` is the vacuum normal wavenumber of rod i, imaginary for evanescent rods (`surf.f90:64-73`, `bulk.f90:71-80`) | as stated | SECTION_READ |
| F6 | Combination: the reflection matrix is carried upward slice by slice, `R <- (T11 R + T12)(T21 R + T22)^-1` (`surf.f90:88-107`, `bulk.f90:108-125`; inverse by Gauss elimination with partial pivoting, `gcmi.f90:5-69`): Ichimiya's recursive reflection technique (P49 Eqs. (24)-(28), L2 D6) | as stated | SECTION_READ |
| F7 | Bulk boundary condition: bulk.exe starts from R = 0 below the stack (no upward wave) and adds unit layers (thickness CC) up to ML; from layer 20 it stops when the largest change of any diagonal `|R_ii|^2` between successive layers is below `epsb = 1e-10` (`bulkio.f90:53`, `bulk.f90:126-140`). Without absorption R does not converge outside a stop band, so the result is that of a slab of ML units on vacuum | as stated | SECTION_READ; consequence DERIVED_HERE |
| F8 | Surface region: surf.exe reads the bulk R per angle (`surf.f90:75-86`) and carries it through `ns = int((max z_surface + dthick + CC)/dz) + 1` slices (`surfio.f90:81-89`; with no surface atoms `ns = int((dthick + CC)/dz) + 1`) that hold the surface atoms, the topmost bulk unit and the tail of the unit below; the output R is at the TOP plane of this region (`s_top = ns dz` above the bottom of the topmost bulk unit) | as stated | SECTION_READ; reference plane DERIVED_HERE (section 1.3) |
| F9 | dz is adjusted in bulk.exe to `dz = CC/ns` with `ns = int(CC/dz) + 1` (`bulkio.f90:118-123`) and passed to surf.exe through the binary file | as stated | SECTION_READ |
| F10 | Output: only intensities, `f2(i) = |f(i,nb0)|^2 K sin^2(theta)/Re(Gamma_i)` for propagating rods, 0 for evanescent ones (`surf.f90:109-117`), written with the glancing angle in DEGREES (`surf.f90:118`, format `ES12.4`). The complex amplitude `f(i,nb0)` exists in memory but is not written. The printed value is `sin(theta)` times the reflected flux fraction (for the specular rod `f2 = |R|^2 sin(theta)`), the same definition as P49 Eq. (13) | as stated | SECTION_READ; interpretation DERIVED_HERE |
| F11 | Scattering factors: `asfparam` uses the Doyle-Turner (1968) 4-Gaussian ELECTRON scattering factor fit when the element has one, otherwise Peng (1999) (`asf.f90:1-6, 415-430`); Si (Z = 14) has a Doyle-Turner entry: a = 2.1293, 2.5333, 0.8349, 0.3216 A, b = 57.7748, 16.4756, 2.8796, 0.3860 A^2 (`asf.f90:229, 329`) | as stated | SECTION_READ (code); agreement of these numbers with the published Doyle-Turner table: UNVERIFIED (paper not read) |
| F12 | Input correction `da1` is SUBTRACTED from the first (widest) Gaussian amplitude (`scpot.f90:46-50`; manual: "Typically, da1 is ~ 1.0", `index.rst.txt:343-345`; the Si sample uses 1.091). It lowers the forward scattering factor and hence the mean inner potential; `da1 = 0` gives the unmodified independent-atom table | as stated | SECTION_READ |
| F13 | Potential units and relativity: `K = sqrt(1e3 BE 0.262466 (1 + BE/(2 x 511.001)))` in rad/A with BE in keV (the relativistic wavenumber; 0.262466 = 2 m e / hbar^2 in A^-2 eV^-1), and every Fourier coefficient carries `(1 + BE/511.001) 4 pi / (cell area)` (`scpot.f90:25, 37-38, 53`), i.e. `U = 2 gamma m e V / hbar^2`, with the Gaussian z-profile of each atom from the analytic 1D transform (`scpot.f90:53-55, 139-144`) | as stated | SECTION_READ; `U = 2 gamma m e V/hbar^2` DERIVED_HERE |
| F14 | Debye-Waller: B = 8 pi^2 <u^2> per element, separately BH, BK (in-plane, `scpot.f90:75-89`, `exp(-...)` on each Fourier coefficient) and BZ (convolved into the z-Gaussians, `scpot.f90:53-55`); B = 0 is allowed (static lattice) | `index.rst.txt:354-369` | SECTION_READ |
| F15 | Absorption: `vi = i sap U` for every Fourier component when `sap > 0`, only the (0,0) component with `abs(sap)` when `sap < 0` (`scpot.f90:145-151`); the manual: "The imaginary part is sap times as large as the real part. Typically, sap is 0.12 to 0.15 for BE = 10 KeV and is approximately proportional to BE^-1/2" (`index.rst.txt:347-351`). This is a PROPORTIONAL optical potential including the same Debye-Waller factors as the real part; no Weickenmeier-Kohl or other TDS model is present | as stated | SECTION_READ |
| F16 | Numerical precision: `real(8)`/`complex(8)` (double) throughout the files read | the declarations | SECTION_READ |
| F17 | No random numbers, seeds, frozen phonons or parallelism in the files read | the files read | SECTION_READ |

Consequences (DERIVED_HERE from F1-F17):

* Relativity at 200 keV: the equation is the scalar Schroedinger equation with the relativistic
  wavenumber and the relativistically scaled potential (the standard high-energy form); the
  repository's engine uses the same `K^2 = k^2 + 2 k sigma V` (M2 section 4; `2 k sigma = 2 gamma m e /
  hbar^2`). The constants differ slightly (511.001 keV against CODATA 2018 510.99895 keV; `K` =
  250.53 rad/A against the engine's 250.5323): section 3 prints both. Spin and the Dirac corrections
  are neglected in both codes. Nothing in the code restricts the energy; the manual's examples are
  10-15 keV (sap scaling "approximately proportional to BE^-1/2" is an empirical remark, not a
  restriction).
* Like-for-like absorption: the engine's `PhysicalAbsorption(model="proportional", ratio=r)` gives
  `V_complex = V (1 + i r)` for every Fourier component of the (band-limited) slice potential
  (`potentials.py:307-308`); sim-trhepd-rheed with `sap = r > 0` gives `U' = r U` for every
  Fourier component (F15). With a static lattice in both (B = 0, no phonons) the absorption models
  are the same model (not the same number, because U itself differs, section 3).
* Where the complex amplitude lives: `f(i, nb0)` at the end of the slice loop of `srfref`
  (`surf.f90:107`) is the reflection-matrix column of the incident (0,0) rod at the plane `s_top`.

### 1.3 Convention of the complex amplitude (DERIVED_HERE from F5-F8; tested in section 4)

In vacuum the slice transfer matrix of F5 reduces to `diag(exp(+i Gamma dz), exp(-i Gamma dz))`
acting on the pair (first block; second block), with the coordinate s increasing towards the vacuum
(F3). The recursion of F6 starts from R = 0 at the bottom (F7), i.e. no FIRST-block wave below the
crystal. Hence the first block is the wave `exp(+i Gamma s)` that must vanish deep in the crystal:
the wave travelling UP (towards the vacuum) under the time factor `exp(-i omega t)`. The absorption
sign agrees: `U' = sap U > 0` for electrons gives `Im(Gamma^2) > 0` and both `exp(+i Gamma s)` and
`exp(-i Gamma s)` decay in their own direction of travel only under `exp(-i omega t)`.
Therefore sim-trhepd-rheed's `f(0, nb0)` at the plane `s_top` is

    R(s_top) = B/A  with  psi_00(s) = A exp(-i Gamma_0 s) + B exp(+i Gamma_0 s),  s >= s_top,

in the SAME convention as this repository (`exp(+i k.r - i omega t)`), NOT the conjugate. This
differs from L2 D-I3, which inferred an `exp(+i omega t)` factor from the P49 PAPER's notation
(Eqs. 9-14 with the crystal at z < 0) and noted `conjg` calls in the fork's `surf_prkn.f90`; the P49
notation and the fork's new integrator are not what is run here. The claim is tested in section 4
against an independent 1D integration of the same (0,0) potential with a known time convention.

Reference plane: the repository measures the specular amplitude relative to the plane of the top
atomic layer (`highest_surface_x_A`, the nuclei of the top layer, `forward/cell.py:124-135`). With
`s_a` the height of the top-layer nuclei in the solver's s coordinate,

    R(s_a) = R(s_top) exp(-2 i Gamma_0 (s_top - s_a)),   Gamma_0 = K sin(theta)

(DERIVED_HERE). At 16 mrad, `2 Gamma_0 = 8.1 rad/A`: 0.01 A of misplaced reference plane moves the
phase by 0.08 rad, so the reference plane is part of the comparison, not a detail.

## 2. Build (REPRODUCED)

### 2.1 What was needed

* Compiler: none present; `apt-get install -y --no-install-recommends gfortran` (root; no other
  package) gave GNU Fortran 13.3.0. The upstream Makefile compiles the bundled reference LAPACK
  (`zgeev.f`, `zgeevb.f`), so no BLAS/LAPACK package was needed.
* Two builds in the scratch directory `.../scratchpad/rheed_solver/`: `build_P/src` (upstream as is,
  positron default) and `build_E/src` (the patch of section 2.2). `make bulk surf`, exit 0, no warnings
  printed; `bulk.exe` and `surf.exe` SHA-256 are stored in `tools/validation/rheed_solver_results.json`.
* Build check (REPRODUCED): the unmodified build reproduces the upstream sample
  `sample/T4Al_on_Si_111` (positron, Si(111)-sqrt3-Al, 13 beams, 68 angles; 0.09 s + 0.77 s): all 68 x
  13 intensities agree with the stored `output/surf-bulkP.s` to max absolute difference 5.0e-6 (the
  stored file has 4 significant digits, maximum stored value 1.337e-2; largest relative difference
  4.7e-4 where the stored value exceeds 1e-4), i.e. to the stored rounding. The stored file was written
  by an older version (its log has a different layout), so this also shows that the 2022-2023 changes
  did not alter this sample's physics. (Command: `bulk.exe; surf.exe` in `build_P/run_T4Al`, numeric
  comparison of the two files; not part of the committed tool.)

### 2.2 The patch (kept in scratch as `s5_patch.diff`, SHA-256 `e3b439e9...`; applied to a copy of `src/`)

It (i) selects electrons (`ep='E'`, the documented upstream switch) and (ii) writes, for every angle,
the complex column `f(i, nb0)` of the final reflection matrix and the vacuum `Gamma_i` of every rod to
`amp.txt`, plus `dz`, `ns`, `s_top = ns dz` and `K` once per run. Only my added lines and the one-line
switch are shown (GPL-3.0 context lines omitted):

```
bulkm.f90:21   ep='P'  ->  ep='E'
surfm.f90:12   ep='P'  ->  ep='E'
U0.f90:18      ep='P'  ->  ep='E'
surfm.f90      + open (8,file='amp.txt') ! S5 patch: complex amplitudes         (after line 16)
surfio.f90     + write (8,'(A,ES25.17,1X,I0,2(1X,ES25.17))') '# S5 dz ns s_top wn ',dz,ns,ns*dz,wn
                                                                               (after line 131)
surf.f90       + write (8,'(*(ES25.17,:,1X))') ga,az,(dble(f(i,nb0)),dimag(f(i,nb0)),dble(gma(i)),
                 dimag(gma(i)),i=1,nb)                                         (after line 118)
```

No computation is changed. The glancing angle `ga` and azimuth `az` are written in radians.

## 3. Solver runs: model, convention test, numerical convergence

Tool: `tools/validation/rheed_solver_compare.py --solver-run` (writes the solver inputs, runs the two
executables, parses `amp.txt`; results in `tools/validation/rheed_solver_results.json`). Every number of
this section is printed by the tool's default (report) mode; the log below only records what was run.

### 3.1 Solver model of flat, bulk-terminated Si(001) (DERIVED_HERE; inputs written by the tool)

* Surface cell `a_s1 = (a/2)[1,1,0]`, `a_s2 = (a/2)[-1,1,0]` (3.8402 A, gamma = 90 deg, plane group p1),
  a = 5.4309 A (ASSUMPTION B2). Layer n (z = n a/4) holds one atom per cell at fractional (0,0),
  (1/2,0), (1/2,1/2), (0,1/2) for n mod 4 = 0..3 (from `DIAMOND_BASIS`). Odd layers have back-bonds
  along [1,1,0]; the top layer is odd, as in the engine's flat strips (`first_terrace_backbond_uvw =
  (1,1,0)`, H2).
* Bulk unit CC = a/2 (two layers) with the next unit shifted by (1/2,1/2) (the smallest unit with a
  constant shift; the Si(001) layers alternate between two shifts). A first trial with CC = a (four
  layers) gave |R|^2 up to 134 with absorption, i.e. garbage: bulk.exe multiplies the slice transfer
  matrices of a whole unit (`bulk.f90:82-98`) before the layer recursion, and an evanescent rod with
  |Gamma| ~ 14 rad/A grows by exp(14 x 5.43) ~ 1e33 across such a unit (DERIVED_HERE; the trial is in
  scratch `explore/a100_r01`, not in the tool).
* Two numerically different routes to the same semi-infinite crystal: approach A = bulk.exe unit
  recursion (up to ML = 300 units, stop when the diagonal |R|^2 change < 1e-10, F7) with an ideal
  bulk truncation in surf.exe (`src/idealsurf.txt:1`: "(NSGS /= 0 and NATM=0) means ideal bulk
  truncation surface"); approach B = ML = 0 (zero bulk reflection) and a slab of M = 90 layers
  (122 A) entered as surface atoms, which surf.exe carries slice by slice (always stable).
* Potential: Doyle-Turner Si as tabulated in the solver (F11), `da1 = 0`, static lattice (BH = BK =
  BZ = 0), absorption `sap = 0.1` (the engine's r = 0.1 model, section 1.2) or 0; dthick = 4 A of
  potential tail kept above the top layer; dz = 0.01 A (adjusted to CC/272 = 0.009983 A by F9).
* Rods: the zero-order Laue-zone row perpendicular to the beam, i.e. the rods whose in-plane vector
  is perpendicular to the azimuth, (h,-h) at [100] (|g| = 2h/a) and (0,k) at [110] (|g| = k sqrt(2)/a).
  N = 6 at [100] (13 rods) and N = 9 at [110] (19 rods) are exactly the rods inside the engine's 2/3
  band at dy = 0.13 A (|g| <= 2.56 1/A). [100] is run as the solver azimuth phi = 45 deg ([0,1,0]),
  equivalent to [1,0,0] by the (1,-1,0) mirror of the bulk-terminated surface; phi = -45 deg is run
  as a check.
* Reference plane: every solver amplitude below is `R(s_a)` of section 1.3, at the top-layer nuclei.

### 3.2 Log of solver runs

- 22:37 UTC: one-beam convention test (`onebeam_r010`, `onebeam_r000`): only the (0,0) rod, slab of
  60 layers, compared with a fixed-step RK4 integration of the same laterally averaged potential
  U_00(s) (continuous Gaussians, not slices) in the `exp(-i omega t)` convention (tool function
  `ode_1d_check`).
- 22:37-22:39 UTC: approach A against B, N = 4 and 6, 1 mrad grid; then rods N = 8, 10 (B), slab 180
  layers (B), dz = 0.005 and 0.02 A (A), phi = -45 deg (A), [110] with N = 9 (A and B), N = 12 (B),
  dz = 0.005 (A).
- 22:41-22:43 UTC: main curves on the 0.02 mrad grid, 12-22 mrad (501 angles): `fine_a100_N6_r010`
  (21 s + 42 s), `fine_a110_N9_r010` (50 s + 91 s).
- 22:52-23:00 UTC: solver at exactly the engine angles (N = 6 / 9, approach A), rod sensitivity at the
  engine angles (N = 8, 10 at [100], N = 12 at [110], approach B), r = 0 curves (ML = 150, 300).
- 23:10-23:16 UTC: a HOLZ test with every rod |g| <= 8/a on the 1 mrad grid was stopped after one
  angle (about 10 min per angle with 101 rods on the loaded machine, load average 14-17) and replaced by
  three angles with every rod |g| <= 6/a (61 rods) against the ZOLZ row |h| <= 3; solver at H2's angle
  16.1347 mrad (cross-check of H2's stored plateaus).
- 23:40 UTC: [110] orientation check (solver with the top-layer back-bonds perpendicular to the beam)
  and the (0,0)-rod-only fine curve.

### 3.3 Convention, reference plane and units: one-beam test (REPRODUCED; tool report section 3)

The solver's (0,0)-rod result for a 60-layer slab (s_top = 87.50338 A, dz = 0.009983 A) is compared
at 21 angles (12-22 mrad, 0.5 mrad) with a fixed-step RK4 integration of `psi'' = -(Gamma_0^2 +
U_00(s)) psi` for the same laterally averaged potential (continuous Doyle-Turner Gaussians, gamma =
1 + 200/511.001, 4 pi/cell area), started at s = 0 with a pure downward wave and decomposed at s_top
in the `exp(-i omega t)` convention (tool function `ode_1d_check`):

| case | max \|R_solver - R_RK4\| | max \|R_solver - conj(R_RK4)\| | RK4 h = 0.002 vs 0.001 A | max \|R\| |
|---|---|---|---|---|
| r = 0.1 | 9.61e-05 | 0.376 | 1.3e-09 | 0.2793 |
| r = 0 (finite slab) | 5.10e-04 | 1.707 | 1.7e-08 | 0.9735 |

At the largest |R| (16.0 mrad) arg R(s_top) is +2.6930 (solver) and +2.6931 (RK4) for r = 0.1, +2.0725
and +2.0730 for r = 0. Conclusions (REPRODUCED): (i) the patched output `f(0,nb0)` is the reflection
coefficient `B/A` at `s_top` in the `exp(+i k.r - i omega t)` convention of this repository, NOT its
conjugate: the phases of sim-trhepd-rheed need NO conjugation (this corrects the expectation in
docs/05 section 4.4 and L2 D-I3, which concern the P49 paper's notation); (ii) the header value
`s_top` is the reference plane; (iii) the potential scale `gamma 4 pi f / Omega` is as read (F13).
The residual (1e-4 to 5e-4) is the solver's slice discretisation (section 3.4: dz = 0.005 A changes R
by 6e-5).

### 3.4 Numerical convergence of the solver (REPRODUCED; tool report section 4)

Max |Delta R| over the angles (1 mrad grid unless stated), and max relative difference where |R| > 0.05:

| comparison | max \|Delta R\| | relative |
|---|---|---|
| [100] N = 6: approach A (bulk.exe) vs B (slab) | 2.18e-05 | 1.01e-04 |
| [100] N = 4: A vs B | 2.20e-05 | 1.04e-04 |
| [100] N = 6 B: slab 180 vs 90 layers | 1.32e-06 | 1.66e-06 |
| [100] N = 6 A: dz 0.005 vs 0.01 A | 5.94e-05 | 3.90e-04 |
| [100] N = 6 A: dz 0.02 vs 0.01 A | 2.37e-04 | 1.56e-03 |
| [100]: phi = -45 deg (rods (h,h)) vs +45 deg | 2.15e-09 | 8.33e-09 |
| [100] rods: N = 4 vs 6 (B) | 1.03e-02 | 4.27e-02 |
| [100] rods: N = 8 vs 6 (B) | 2.11e-03 | 8.80e-03 |
| [100] rods: N = 10 vs 6 (B) | 2.65e-03 | 1.10e-02 |
| [110] N = 9: A vs B | 1.26e-05 | 1.48e-04 |
| [110] N = 9 A: dz 0.005 vs 0.01 A | 8.04e-05 | 6.58e-04 |
| [110] rods: N = 12 vs 9 (B) | 2.24e-03 | 1.02e-02 |
| [100] engine angles (24): N = 8 (B) vs N = 6 (A) | 2.12e-03 | 1.04e-02 |
| [100] engine angles (24): N = 10 (B) vs N = 6 (A) | 2.66e-03 | 1.31e-02 |
| [110] engine angles (15): N = 12 (B) vs N = 9 (A) | 2.85e-03 | 1.36e-02 |

Reading: the two numerical routes agree to 2e-5, the slab and the slice thickness are converged to
better than 1e-4 in R, the [1,0,0] and [0,1,0] azimuths give the same R to 2e-9 (the mirror symmetry
of the bulk-terminated surface, a check of the input geometry), and the rods beyond the engine's band
change R by about 1 % (up to 1.4 % at the engine angles). The total reflected flux summed over all
propagating rods never exceeds 1 (largest value 1.000000, at total-reflection angles), with or
without absorption. [The HOLZ row of this table is added when the run finishes; section 3.5.]

## 4. Solver rocking curves (REPRODUCED; tool report section 5)

Doyle-Turner Si, static lattice, 0.02 mrad grid from 12 to 22 mrad (501 angles), R at the top-layer
nuclei in the repository's convention. Beams: [100] 13 rods (h,-h), |h| <= 6; [110] 19 rods (0,k),
|k| <= 9. The tool prints the full tables every 0.2 mrad; the rows below are a subset.

### 4.1 r = sap = 0.1 (the like-for-like absorption)

| theta (mrad) | [100] \|R\|^2 | [100] arg R | [110] \|R\|^2 | [110] arg R |
|---|---|---|---|---|
| 12.00 | 0.04650 | -2.533 | 0.06288 | -3.123 |
| 12.20 | 0.04801 | -2.162 | 0.07991 | -2.677 |
| 13.00 | 0.00955 | -1.474 | 0.01174 | -1.409 |
| 14.00 | 0.00167 | -1.510 | 0.01495 | -1.789 |
| 15.00 | 0.00001 | -0.007 | 0.04860 | -1.379 |
| 15.20 | 0.00026 | +1.313 | 0.04901 | -1.057 |
| 15.60 | 0.00765 | +1.717 | 0.02959 | -0.370 |
| 15.80 | 0.02953 | +2.158 | 0.01715 | -0.012 |
| 16.00 | 0.06678 | +2.843 | 0.00683 | +0.431 |
| 16.20 | 0.07881 | -2.712 | 0.00034 | +0.737 |
| 16.40 | 0.05303 | -2.017 | 0.00085 | -0.797 |
| 16.60 | 0.01784 | -1.576 | 0.00053 | -0.305 |
| 16.80 | 0.00764 | -1.517 | 0.00001 | -2.920 |
| 17.00 | 0.00448 | -1.463 | 0.00171 | -2.763 |
| 17.60 | 0.00080 | -1.181 | 0.04389 | -0.867 |
| 18.00 | 0.00006 | -0.508 | 0.00634 | +0.361 |
| 18.60 | 0.00068 | +2.802 | 0.03303 | +0.866 |
| 19.00 | 0.00083 | +3.113 | 0.01227 | +2.582 |
| 20.00 | 0.00126 | +2.916 | 0.00194 | +0.820 |
| 21.00 | 0.00986 | -2.364 | 0.00061 | -2.678 |
| 22.00 | 0.00017 | -2.888 | 0.00033 | -1.275 |

* [100] local maxima (|R|^2 > 0.005): 12.12 mrad (0.0494, arg -2.309), 16.16 mrad (0.0798, arg -2.855),
  20.96 mrad (0.0100, arg -2.497). The (0,0,8) peak (parabola on the fine grid): 16.1571 mrad,
  |R|^2 0.07977, FWHM 0.6065 mrad (15.856 to 16.463), arg R at the peak -2.8658 rad; arg R rises
  monotonically through the peak, unwrapped from +1.590 rad at 15.5 mrad to +4.783 rad at 16.9 mrad
  (+3.193 rad), the Bragg-case phase sweep that docs/05 4.4 rung 2 asks for. Near 15.0 and 18.1 mrad
  R passes close to zero and its phase jumps.
* [110] local maxima: 12.30 (0.0823, arg -2.451), 13.10 (0.0098), 13.78 (0.0160), 15.12 (0.0498, arg
  -1.189), 17.58 (0.0439, arg -0.949), 18.62 mrad (0.0332, arg +0.962). At [110] the (0,0,8)
  condition (about 16.13 mrad) is a near-ZERO of the specular reflectivity (|R|^2 = 3.4e-4 at 16.20
  mrad), consistent with H2's finding that [110] reflects six times more weakly there (section 6.4).
* The refraction-only (0,0,8) angle with the DT mean inner potential is 16.1327 mrad (tool section 2);
  the many-beam peak at [100] lies 0.024 mrad higher.

### 4.2 r = 0 (no absorption): finite slabs only

Without absorption the bulk recursion does not converge outside total-reflection bands (F7): the
results are those of a slab of ML units (ML = 150: 407 A; ML = 300: 815 A) on vacuum. The two
thicknesses differ by more than 1e-3 in R at 468 of 501 angles ([100]) and 469 of 501 ([110]); they
agree (max |Delta R| 3.9e-09 at [100], 1.7e-05 at [110]) only where the total reflected flux is 1
(19 angles at [100], e.g. 12.0-12.2 and 21.0 mrad; 29 at [110], e.g. 16.2, 17.4, 18.6 mrad). Largest
|R|^2: 0.9739 ([100]), 0.9003 ([110]). Example rows ([100], ML150 | ML300): 16.00 mrad 0.7744 / +2.648 |
0.8139 / +2.616; 16.20 mrad 0.8635 / -2.279 | 0.8306 / -2.441; 16.40 mrad 0.9667 / -1.502 | 0.6583 /
-1.265. A semi-infinite, non-absorbing rocking curve is therefore not a well-defined reference here,
in the solver as in the engine (H2: the engine's r = 0 strip has not settled within 8000 A); an
r = 0 comparison would need a stated tiny absorption or a Bloch-wave bulk boundary condition, neither
of which the upstream code provides.

## 5. Tolerances (DECLARED at 22:45 UTC, before the first engine run of this study and before any
## engine-solver difference was computed)

Like-for-like comparison = the engine run with the solver's Doyle-Turner scattering factors
(`DoyleTurnerPotential` in the tool: the engine's `AtomicPotential` with only its scattering-factor
function replaced; TEST_ONLY), static lattice in both, proportional absorption r = sap = 0.1 in both,
solver rods = the engine-band ZOLZ row. Per angle:

    |R_eng - R_sol| <= 0.05 |R_sol| + 0.005 + 2 s_eng

with `s_eng` the engine's own read-out spread at that angle (largest deviation of a 250 A bin in the
read-out window from the window mean). Basis: the solver's own rod-set sensitivity (N = 6 -> 8 or
10 changes R by up to 1.1 % of |R| and 2.7e-3 absolute, section 3.4) and the engine's band limit on
the normal-direction couplings, which H2 section 5 estimates at 2.8e-2 of V_g at [100]; 5 % and
0.005 are these rounded up. For |R_sol| >= 0.1 the criterion allows about 0.1 rad of phase error.
Curve level at the [100] (0,0,8) peak, both codes sampled at the same engine angles, peak by a
parabola through the three highest points: peak angle within 0.03 mrad (8 % of the two-beam Darwin
width 0.37 mrad, H2 2.1), peak |R|^2 within 10 %, FWHM within 10 %, phase sweep
`arg R(theta_pk + w) - arg R(theta_pk - w)` (w = half the solver's FWHM) within 0.1 rad.

What a bug would look like (decided now): a conjugated convention gives `arg R_eng ~ -arg R_sol`; a
misplaced reference plane gives a phase difference linear in `sin(theta)` (slope `2 k dx`); a wrong
refraction gives a peak shift not explained by the mean inner potentials; a wrong interaction
constant or absorption sign scales the widths or gives |R| > 1. Expected, not a bug: with the
Kirkland potential (production engine) peak shifts, widths and phases differ by amounts set by the
two parameterisations' V_0 and V_g (section 6 prints both); the ZOLZ-row solver omits HOLZ couplings
that the engine partly carries.

## 6. Engine against solver

### 6.1 Engine set-up (DERIVED_HERE from H2; tool `engine_flat_strip`, `engine_readout`)

* Flat bulk-terminated Si(001) strip built as in H2 (`build_si001_terraces` for one period along the
  beam with every builder assertion, tiled along z), top-layer back-bond (1,1,0), 1 period across the
  beam (5.43 A at [100], 3.84 A at [110]; the flat crystal has no other transverse periodicity),
  4500 A of surface after the first contact of the sheet beam, clean depth 55 A + 15 A bulk absorber
  (H2 section 3, r = 0.1), 10 A top absorber, 100 V sin^2 absorbers, sheet beam 2 A above the top
  layer with 2 A sin^2 edges whose top edge lands 1 A before the exit plane, vacuum from the engine's
  item-2 rule, dx = dy <= 0.13 A (derived pixel 0.1293-0.1296 A), dz = a/4 ([100]) or a/(4 sqrt 2)
  ([110]), exact propagator, 2/3 band, complex64, numpy backend, static lattice, proportional
  absorption r = 0.1 (TEST_ONLY stand-in for item 21), entrance vacuum 10 slices.
* Read-out (tool `engine_readout`, DERIVED_HERE, the formula of `analysis.flat_reflection_coefficient`
  applied to the vacuum part of the exit plane as in H2's `specular_column`): y-average, vacuum mask
  from 2 A above the top layer, band-pass |f_x - f_c| <= 0.1 1/A, demodulation, mean over the rays
  that left the surface 2500 A after first contact up to 750 A before the exit plane (H2 section 2.4:
  r = 0.1 phase settled within 1e-2 rad beyond 1500 A, amplitude within 3 % beyond 2500 A; exit-plane
  contamination over the last 500 A), then `R = <e> exp(+4 pi i f_c x_s) / P_L` with x_s the top-layer
  plane and `P_L = exp(i L_z (k_z - k))` the exact vacuum propagation factor. The spread `s_eng` is the
  largest deviation of a 250 A bin inside the window from the window mean. The y-averaged exit column
  is stored per angle (7 significant digits) so that every read-out choice can be re-evaluated from
  the committed results (section 6.5).
* Like-for-like potential: `DoyleTurnerPotential` (tool) = the engine's `AtomicPotential` with only
  `scattering_factor` replaced by `h^2/(2 pi m0 e) sum_j a_j exp(-b_j f^2/4)` with the solver's
  Doyle-Turner numbers; the engine's own slice construction, band limit, absorption and MIP code are
  used unchanged. TEST_ONLY: the orchestrator's decision "Kirkland only" (M2) is for production; this
  class exists only in the validation tool.
* Engine version: the main [100] and [110] Doyle-Turner runs were started at 23:08 UTC with the engine
  of commit `148e4f6`; another agent's snapshot `2a3a999` (23:13 UTC) added a REQUIRED
  `MultisliceParams.working_reflections_hkl` (a band assertion that the declared working reflection
  lies inside the transmission band) and a memory model to `engine.py` and `grid.py`; the slice loop,
  potentials, propagator and illumination are unchanged in that diff (SECTION_READ of `git diff
  148e4f6 2a3a999 -- reflection_holo/forward/multislice/`). The tool passes
  `working_reflections_hkl=((0,0,8),)` when the field exists. Check (REPRODUCED): the 16.2 mrad [100]
  run repeated with the new engine (tag `__bin_A=250.0`, identical settings) gives the same R as the
  run with the old engine (section 6.5 prints both).
