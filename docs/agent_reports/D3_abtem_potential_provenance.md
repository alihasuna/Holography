# D3: abTEM atomic-potential provenance for the custom multislice kernel (source-map row SM17)

Prepared: 2026-09-22. Scope: establish, from version-matched abTEM source, which projected atomic
potential parameterisations abTEM ships, how it forms the projected potential and the interaction
constant, whether the parameterisation can be called on our own atoms and slices, absorption,
propagator and tilt, licence, and the mean inner potential (MIP) that each parameterisation implies
for Si. Project: reflection-mode dark-field electron holography of Si(001) at 200 keV.

Evidence labels: `SECTION_READ` (code or documentation read; locator given), `REPRODUCED` (executed
here; command and output recorded), `DERIVED_HERE` (arithmetic on labelled facts), `UNVERIFIED`.

Terminology kept distinct throughout: abTEM is an ENGINE (Python package) that implements the
multislice ALGORITHM (and also PRISM, not used here); the parameterisations are published FITS
(Kirkland, Lobato and Van Dyck, Peng) that abTEM ships as JSON tables; Prismatic, pyprismatic and
prismatique are not involved in this report.

Status of this file: complete (written incrementally); section 8 holds the recommendation and blockers, section 9 the fact table.

---

## 0. Version pin and artifacts

| # | Item | Result | Label |
|---|---|---|---|
| 0.1 | `venv/bin/pip index versions abtem` | `abtem (1.0.10)`; available `1.0.10, 1.0.9, 1.0.8, 1.0.6, 1.0.5, 1.0.4, 1.0.3, 1.0.1, 1.0.0` | REPRODUCED |
| 0.2 | PyPI JSON `https://pypi.org/pypi/abtem/1.0.10/json` | wheel `abtem-1.0.10-py3-none-any.whl` sha256 `34e098662a26cedebd0154ae0660c49efb6149cba161a605f02ecf381f45515d`, uploaded 2026-07-06T11:26:53; sdist `abtem-1.0.10.tar.gz` sha256 `30717db9d339aed03ad5238aa7504b75694481a455e2cfc95f1453f49583f3a2`; `license_expression = GPL-3.0-or-later`; `requires_python >=3.11` | REPRODUCED |
| 0.3 | `/home/user/Holography/venv/bin/pip install "abtem==1.0.10"` | installed `abtem-1.0.10` plus dependencies, among them `ase-3.29.0 numba-0.67.0 pyfftw-0.15.1 dask-2026.8.0 distributed-2026.8.0 zarr-3.1.6 pandas-3.0.6 matplotlib-3.11.2`; numpy stayed `2.4.6`, scipy `1.17.1` | REPRODUCED |
| 0.4 | `venv/bin/python -c "import abtem; print(abtem.__version__)"` | `1.0.10`; `abtem/_version.py:3 __version__ = "1.0.10"` | REPRODUCED |
| 0.5 | `git ls-remote --tags https://github.com/abTEM/abTEM.git` | `164e644ff411167db23ec4ef26aeb4fe8f384b26 refs/tags/v1.0.10` (lightweight tag); remote `HEAD` at the time of reading `fba42a980cb3e5199b5b25190fccee8ab024732a` | REPRODUCED |
| 0.6 | `git clone --depth 1 --branch v1.0.10 https://github.com/abTEM/abTEM.git` | commit `164e644f...`, 2026-07-06T13:13:54+02:00, "Merge pull request #315 from abTEM/dev" | REPRODUCED |
| 0.7 | `diff -rq` of `abtem/` between (a) the tag v1.0.10 checkout, (b) the PyPI sdist and (c) the installed site-packages | no differences (empty output, `__pycache__` excluded) | REPRODUCED |
| 0.8 | `git clone --filter=blob:none --no-checkout https://github.com/abTEM/abTEM.git` (history only) | `origin/HEAD` `fba42a98`, 2026-09-22, `_version.py` `1.1.0`, 237 commits after v1.0.10; report D's `e78cb7b` is present | REPRODUCED |
| 0.9 | `curl -L https://sourceforge.net/projects/computem/files/source.zip/download` (Kirkland's own code) | `source.zip` sha256 `e578cc837dea17258f8117101912afca3e03858fa5d94c73e33c905375d40d84`; `source/temsim/slicelib.cpp` "Copyright 1998-2026 Earl J. Kirkland", GPL-3.0-or-later | REPRODUCED |
| 0.10 | `git clone --depth 1 --filter=blob:limit=2m https://github.com/Ivanlh20/MULTEM.git` (Lobato's own code) | commit `23c3713281f3e6e2654d8bfa1135a2258a776fbf`, 2025-07-03; `src/atomic_data.hpp` "Copyright 2020 Ivan Lobato", GPL-3.0-or-later | REPRODUCED |
| 0.11 | abTEM documentation pages fetched with curl from `https://abtem.github.io/doc/...` (cite, bibliography, conventions, multislice derivation, multislice and potentials walkthroughs, Bloch-wave tutorial, `PlaneWave` API page, `searchindex.js`) | every page footer reads "Tested against abTEM v1.0.10." | REPRODUCED |

All file:line locators below refer to the installed, identical tree
`/home/user/Holography/venv/lib/python3.11/site-packages/abtem/` (written `abtem/...`), i.e. abTEM
1.0.10 = git tag v1.0.10 = commit `164e644f`.

**Version caution (important for docs/05 section 4.3).** Report D read abTEM from GitHub HEAD
`e78cb7b` whose `_version.py` said `1.1.0`. That version is NOT on PyPI (0.1). Several statements
in docs/05 section 4.3 (exact propagator, "abTEM 1.1") come from that unreleased tree. The released
1.0.10 differs in the propagator; see section 5. Everything below is for 1.0.10.

Precision: abTEM's global precision is `float32` by default (`abtem/core/abtem.yaml:7-8`
`precision: float32`); `get_dtype` maps it to `float32`/`complex64` (`abtem/core/utils.py:366-388`).
It can be switched with `abtem.config.set({"precision": "float64"})` (used in section 7).
Physical constants: abTEM takes them from ASE (`abtem/core/constants.py:1-8`,
`abtem/core/energy.py:8`), and ASE 3.29.0 uses CODATA 2014 by default
(`ase/units.py:15 __codata_version__ = '2014'`), not the repository's CODATA 2018. The effect at
200 keV is 5e-9 relative in lambda and 6e-9 in sigma (section 2.2, REPRODUCED): negligible.
Seeds: nothing in this report is random; no seed is used.

Scratch artifacts (not committed): `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/`
(`dl/` wheel and sdist, `abtem_git_v1.0.10/` tag checkout, `abtem_hist/` history clone,
`computem/` Kirkland's own source, `multem/` Lobato's own source, `crossref/` Crossref JSON records,
`*.html`/`*.txt` documentation pages, and the scripts `cmp_kirkland.py`, `cmp_lobato.py`,
`sigma_check.py`, `api_example.py`, `sign_test.py`, `absorb_test.py`, `tilt_check.py`,
`finite_conv.py`). Inside the repository only `tools/provenance_checks/abtem_mip.py` and this report
were written, besides the abTEM installation into `venv/` (row 0.3).

---

## 1. Parameterisations shipped by abTEM 1.0.10

### 1.1 Classes, tables and defaults (SECTION_READ)

| Parameterisation | Class | Table file | Array shape per element | Elements in table | Default where |
|---|---|---|---|---|---|
| Lobato and Van Dyck | `LobatoParametrization`, `abtem/parametrizations/__init__.py:466-553` | `abtem/parametrizations/data/lobato.json` | (2, 5) | 103 (H..Lr) | default of `Potential` (`abtem/potentials/iam.py:1037 parametrization="lobato"`) and of `ScatteringFactorProjectionIntegrals` (`abtem/integrals.py:416`) |
| Kirkland | `KirklandParametrization`, `__init__.py:377-463` | `data/kirkland.json` | (4, 3) | 103 | selectable as `"kirkland"` (`__init__.py:656-667`) |
| Peng (neutral, "high") | `PengParametrization`, `__init__.py:556-636` | `data/peng_high.json` (class default, `__init__.py:587`) | (2, 5) | 98 | used as the Gaussian basis of `GaussianProjectionIntegrals` (`abtem/integrals.py:166-297`) |
| Peng (neutral, "low") | same class with `parameters="peng_low.json"` | `data/peng_low.json` | (2, 5) | 98 | not referenced by any `.py` file (grep, REPRODUCED) |
| Peng (ions) | same class with `parameters="peng_ionic.json"` | `data/peng_ionic.json` | (2, 5) | 106 ion keys (`O-`, `O--`, `Si++++`, ...) | not referenced by any `.py` file; `get_function` raises `NotImplementedError` for `charge > 0` (`__init__.py:289-290`) |
| Ewald (point charge minus Gaussian charge) | `EwaldParametrization`, `__init__.py:639-653`; `functions/ewald.py:9-22` | none (width, Z) | - | - | used for DFT (GPAW) potentials, not IAM |
| Waasmaier and Kirfel (X-ray) | no class | `data/waasmaier_kirfel.json` (11 numbers per species, 211 species) | - | - | not referenced by any `.py` file |

`validate_parametrization` maps the strings `"ewald" "lobato" "peng" "kirkland"` to these classes
(`abtem/parametrizations/__init__.py:656-667`). The `Potential` docstring says only
`'lobato' or 'kirkland'` and "Two of the most accurate parametrizations are available (by Lobato
et al. and Kirkland; default is 'lobato'). See the citation guide for references."
(`abtem/potentials/iam.py:981-985`).

Coverage of Si (Z = 14) and O (Z = 8), read from the JSON files with `json.load` (REPRODUCED):

| Table | Si | O |
|---|---|---|
| `kirkland.json` | `[[1.06543892, 0.120143691, 0.180915263], [1.04118455, 68.7113368, 0.0887533926], [1.1206562, 0.0305452816, 1.59963502], [3.70062619, 0.214097897, 9.99096638]]` | `[[0.339969204, 0.307570172, 0.130369072], [0.38157028, 0.381571436, 19.1919745], [0.0883326058, 0.1965867, 0.00099622], [0.760635525, 2.07401094, 0.0303266869]]` |
| `lobato.json` | `[[2.87189142611612, -2.06173501195173, 2.17114024204478, -0.0663073633058801, 0.00301070709670513], [5.08487103642989, 0.429178185305126, 0.366485434192162, 0.119710611296903, 0.0143994536128397]]` | `[[29.9474045242362, -77.6101266255278, 99.8817764623144, -51.2127005505673, 0.00819618954446032], [1.3028398788001, 1.15794105258309, 1.00988549338025, 0.943327971433266, 0.0433197611321825]]` |
| `peng_high.json` | `[[0.0567, 0.3365, 0.8104, 2.496, 2.1186], [0.0582, 0.6155, 3.2522, 16.7929, 57.6767]]` | `[[0.0365, 0.1729, 0.5805, 0.8814, 0.3121], [0.0652, 0.6184, 2.9449, 9.6298, 28.2194]]` |
| `peng_low.json` | `[[0.2519, 0.6372, 1.3795, 2.5082, 1.05], [0.3075, 2.0174, 9.6746, 29.3744, 80.4732]]` | `[[0.0974, 0.2921, 0.691, 0.699, 0.2039], [0.2067, 1.3815, 4.6943, 12.7105, 32.4726]]` |
| `peng_ionic.json` | no neutral Si; `Si++++` present | `O-` present (`O--` also a key) |

All three neutral tables cover Si and O. The Kirkland JSON layout is `[a(3), b(3), c(3), d(3)]`,
a re-ordering of Kirkland's `a1 b1 a2 b2 a3 b3 c1 d1 c2 d2 c3 d3`.

### 1.2 Independent check of the Kirkland table against Kirkland's own code (REPRODUCED)

Kirkland's own simulation code (computem/temsim, GPL-3.0-or-later, "Copyright 1998-2026 Earl J.
Kirkland", `source/temsim/slicelib.cpp:1-17`) was downloaded from
`https://sourceforge.net/projects/computem/files/source.zip/download` (sha256
`e578cc837dea17258f8117101912afca3e03858fa5d94c73e33c905375d40d84`). Its hard-coded table
`fparams[Z][0..11]` (`slicelib.cpp:697-1948`, `ReadfeTable()`; Si at `slicelib.cpp:864ff`, O at
`slicelib.cpp:792ff`) was parsed and compared with abTEM's `kirkland.json`
(`scratchpad/cmp_kirkland.py`):

```
$ venv/bin/python cmp_kirkland.py
elements compared: 103  elements with any parameter rel. diff > 1e-6: 1
max relative difference over all 103x12 parameters: 6.220e-05 at (2, 'He')
O max rel diff 2.811e-08
Si max rel diff 0.000e+00
```

So abTEM's Kirkland Si entry is bit-identical to Kirkland's current code and O agrees to the
printed precision (abTEM truncates `9.96220028e-4` to `0.00099622`). This fixes the TABLE
provenance independently of abTEM. It does not establish which book edition prints the same
numbers: Kirkland's book was not read (B06 remains unread; UNVERIFIED that the 2nd-edition
Appendix C table is numerically identical).

The Lobato and Peng tables were NOT checked against the papers (papers not read): UNVERIFIED.

### 1.3 Citations as given by abTEM, and Crossref verification

abTEM source docstrings (SECTION_READ, verbatim):

* Kirkland: `E.J. Kirkland. Advanced computing in electron microscopy. Springer, 2. edition, 2010`
  (`abtem/parametrizations/__init__.py:393-395`).
* Lobato: `Ivan Lobato and Dirk Van Dyck. Acta Crystallographica Section A, 70:636-649, 2014.`
  (`__init__.py:482-484`).
* Peng: `L. Peng. Micron, 30(6):625–648, 1999.` (`__init__.py:572-574`).
* Projection method: `W. Van den Broek et al. Ultramicroscopy, 158:89-97, 2015.
  doi:10.1016/j.ultramic.2015.07.005.` (`abtem/integrals.py:410-413`).
* Order-2 propagator correction: `# Eq. (4) from Microscopy and Microanalysis (2020), 26, 1147-1157`
  (`abtem/multislice.py:72`); no author or DOI given.

abTEM documentation, bibliography page `https://abtem.github.io/doc/user_guide/bibliography.html`
(page footer "Tested against abTEM v1.0.10", so version-matched; SECTION_READ, verbatim):

* `[Kir10] Earl J. Kirkland. Advanced computing in electron microscopy. Springer, 2 edition, 2010. ISBN 978-1-4419-6532-5.`
* `[LD14] Ivan Lobato and Dirk Van Dyck. An accurate parameterization for the scattering factors, electron densities and electrostatic potentials for neutral atoms that obey all physical constraints. Acta Crystallographica Section A, 70:636–649, 2014. doi:10.1107/S205327331401643X.`
* `[Pen99] Lian-Mao Peng. Electron atomic scattering factors and scattering potentials of crystals. Micron, 30(6):625–648, 1999. doi:10.1016/S0968-4328(99)00033-5.`
* `[VdBJK15] W. Van den Broek, X. Jiang, and C.T. Koch. Fdes, a gpu-based multislice algorithm with increased efficiency of the computation of the projected potential. Ultramicroscopy, 158:89–97, 2015. doi:10.1016/j.ultramic.2015.07.005.`

Citation page `https://abtem.github.io/doc/abtem/cite.html` (footer "Tested against abTEM v1.0.10"):
"If you use abTEM in your research, we kindly ask that you cite our main paper: Jacob Madsen and Toma
Susi. The abTEM code: transmission electron microscopy from first principles. Open Research Europe
1:24, 2021. doi:10.12688/openreseurope.13015.1." and "we recommend that you also cite the original
works of any relevant methods and algorithms that your use relies on (e.g. PRISM, GPAW, or potential
parametrizations ...)".

Crossref (`https://api.crossref.org/works/<DOI>`, all HTTP 200, JSON kept in `scratchpad/crossref/`;
REPRODUCED; no DOI was typed from memory: each was copied from the abTEM page or found by a
Crossref bibliographic query):

| DOI | Crossref title / authors / container | Agrees with abTEM citation |
|---|---|---|
| `10.1107/S205327331401643X` | "An accurate parameterization for scattering factors, electron densities and electrostatic potentials for neutral atoms that obey all physical constraints"; I. Lobato, D. Van Dyck; Acta Cryst. A 70(6) 636-649, issued 2014-10-17 | yes (abTEM's title has an extra "the") |
| `10.1016/S0968-4328(99)00033-5` | "Electron atomic scattering factors and scattering potentials of crystals"; L.-M. Peng; Micron 30(6) 625-648, 1999-12 | yes |
| `10.1007/978-1-4419-6533-2` (found by Crossref query `Kirkland Advanced Computing in Electron Microscopy`) | "Advanced Computing in Electron Microscopy"; Earl J. Kirkland; Springer US, 2010; ISBN 9781441965325, 9781441965332 | yes: ISBN 978-1-4419-6532-5 of the abTEM bibliography is the first ISBN of this record. The repository's B06 is the 3rd edition, `10.1007/978-3-030-33260-0` (2020), a different edition from the one abTEM cites |
| `10.1016/j.ultramic.2015.07.005` | "FDES, a GPU-based multislice algorithm with increased efficiency of the computation of the projected potential"; W. Van den Broek, X. Jiang, C.T. Koch; Ultramicroscopy 158, 89-97, 2015-11 | yes |
| `10.1017/s1431927620024605` (found by Crossref query on "Microscopy and Microanalysis 2020 26 1147", filtered 2020-2021) | "Inelastic Scattering in Electron Backscatter Diffraction and Electron Channeling Contrast Imaging"; B.G. Mendis, J. Barthel, S.D. Findlay, L.J. Allen; Microsc. Microanal. 26(6) 1147-1157, 2020-11-16 | volume and pages match the code comment; identification by volume/page only (the comment names no author) |
| `10.12688/openreseurope.13015.1` and `.2` | "The abTEM code: transmission electron microscopy from first principles"; J. Madsen, T. Susi; Open Research Europe 1, 24; v1 2021-03-24, v2 2021-05-21 | docs cite v1; the repository cache `docs/agent_reports/crossref_cache/ABTEM.json` holds v2 |

Not cited by abTEM: the origin of `peng_high.json`, `peng_low.json`, `peng_ionic.json` and
`waasmaier_kirfel.json` (which Peng et al. table each file reproduces). UNVERIFIED; the only Peng
citation abTEM gives is the 1999 Micron review.

### 1.4 Functional forms and units (SECTION_READ of abTEM code; equivalence to the papers UNVERIFIED)

Units in abTEM: lengths in Angstrom, spatial frequency `k` in cycles/Angstrom (1/Angstrom, no 2 pi),
potential in V ("eV/e", `abtem/parametrizations/__init__.py:356`), projected potential in V
Angstrom, scattering factors in Angstrom (`__init__.py:366`).
The conversion constant is
`kappa = 4 pi eps0 / (2 pi Bohr e)` (`abtem/core/constants.py:7-8`), i.e. `1/kappa = 2 pi a0 e`
= 47.87764685 V Angstrom^2 (REPRODUCED, ASE CODATA 2014). Kirkland's own code uses the same
combination as `al = 150.4121417 = 2 pi^2 a0 e` and `ag = 266.5985798 = 2 pi^(5/2) a0 e`
(`computem slicelib.cpp:2442`, "constants from H. L. Anderson ... 1989").

**Kirkland** (`abtem/parametrizations/functions/kirkland.py`; scaling in `__init__.py:446-463`).
Electron scattering factor, `k2 = k^2` in 1/Angstrom^2 (`kirkland.py:8-17`):
`f_e(k) = sum_{i=1..3} a_i / (b_i + k^2) + sum_{i=1..3} c_i exp(-d_i k^2)`
(a in 1/Angstrom, b in 1/Angstrom^2, c in Angstrom, d in Angstrom^2). abTEM rescales
(`__init__.py:449-452`): `A_i = pi a_i / kappa`, `B_i = 2 pi sqrt(b_i)`,
`C_i = pi^(3/2) c_i / d_i^(3/2) / kappa`, `D_i = pi^2 / d_i`, and then
`V(r) = sum A_i exp(-B_i r)/r + C_i exp(-D_i r^2)` (`kirkland.py:20-29`);
projected (infinite) potential
`V_z(r) = sum 2 A_i K0(B_i r) + sqrt(pi/D_i) C_i exp(-D_i r^2)` (`kirkland.py:45-54`, scipy `kn(0, .)`);
projected scattering factor (2D Fourier transform of `V_z`, unit V Angstrom^3)
`F(k) = sum 4 pi A_i / (4 pi^2 k^2 + B_i^2) + sqrt(pi/D_i) C_i (pi/D_i) exp(-pi^2 k^2 / D_i)`
(`kirkland.py:57-80`). At `k = 0`, `F(0) = sum 4 pi A_i/B_i^2 + C_i (pi/D_i)^(3/2)`, which is
the 3D volume integral of `V(r)`. Note `kirkland.py:59` builds `pi` as float32 inside this numba
function (`pi = np.array(np.pi, dtype=np.float32)`), so the `k`-dependence carries float32 pi even in
float64 mode.

**Lobato and Van Dyck** (`functions/lobato.py`; scaling `__init__.py:537-553`).
`f_e(k) = sum_{i=1..5} a_i (2 + b_i k^2) / (1 + b_i k^2)^2` (`lobato.py:9-17`); scaled
`A_i = pi^2 a_i / b_i^(3/2) / kappa`, `B_i = 2 pi / sqrt(b_i)`;
`V(r) = sum A_i (2/(B_i r) + 1) exp(-B_i r)` (`lobato.py:20-28`);
`V_z(r) = 2 sum [2 A_i/B_i K0(B_i r) + A_i r K1(B_i r)]`, cast to float32 (`lobato.py:92-97`);
projected scattering factor
`F(k) = 8 pi sum [A_i/B_i/(4 pi^2 k^2 + B_i^2) + A_i B_i/(4 pi^2 k^2 + B_i^2)^2]` (`lobato.py:100-131`,
again with float32 pi and pi^2 at `lobato.py:102-103`).

**Peng** (`functions/peng.py`; scaling `__init__.py:591-636`). Gaussian sum
`f_e = sum_{i=1..5} a_i exp(-b_i s^2)`; abTEM converts the tabulated `b_i` from `s = k/2` to `k` by
`b_i / 4` (`__init__.py:593`, comment "convert scattering factor units"); scaled potential
`V(r) = sum pi^(3/2) a_i / b_i^(3/2) / kappa exp(-pi^2 r^2 / b_i)` and projected
`V_z(r) = sum (pi a_i / b_i / kappa) exp(-pi^2 r^2 / b_i)` (`__init__.py:595-610`), evaluated by the
generic Gaussian sum `peng.scattering_factor(k, p)` (`peng.py:8-16`); finite-slab projection with
`erf` limits (`peng.py:30-36`).

The formulas of the published papers were NOT read; that abTEM's rescalings reproduce the
papers' real-space forms is UNVERIFIED from the papers. For Kirkland it is REPRODUCED against
Kirkland's own code in section 3.2 (finding 2).

---

## 2. Projected potential, interaction constant and sign convention

### 2.1 How abTEM builds the projected potential (SECTION_READ)

* `abtem.Potential(atoms, gpts=None, sampling=None, slice_thickness=1, parametrization="lobato",
  projection="infinite", exit_planes=None, plane="xy", origin=(0,0,0), box=None, periodic=True,
  integrator=None, device=None)` (`abtem/potentials/iam.py:1031-1048`). `projection="infinite"`
  selects `ScatteringFactorProjectionIntegrals`, `"finite"` selects `QuadratureProjectionIntegrals`
  (`iam.py:1049-1059`). Docstring: "If 'infinite' (default), the infinite potential projection of
  each atom will be assigned to a single slice"; "If 'finite' the 3D potential is numerically
  integrated between the slice boundaries" (`iam.py:986-989`).
* Every slice is produced by one call per slice
  `integrator.integrate_on_grid(atoms_in_slice, a=slice_start, b=slice_end, gpts, sampling, device)`
  (`iam.py:853-863`); the atoms are wrapped into the cell and, for the finite integrator, padded with
  periodic images out to the cutoff (`iam.py:752-789`, `abtem/atoms.py:1043-1088 pad_atoms`).
* Infinite projection (Van den Broek et al. 2015 hybrid method, `abtem/integrals.py:398-505`): the atom
  positions are spread onto the grid as bilinear-weighted deltas with periodic wrap
  (`superpose_deltas`, `integrals.py:333-395`, modulo at `377-378`), Fourier transformed, multiplied by
  the projected scattering factor `F(k)` of the parameterisation and divided by a pixel `sinc`
  whose DC value is the pixel area (`integrals.py:300-330, 496-501`), then inverse transformed; the
  real part is kept. Unit of the slice array: V Angstrom, the slice-projected potential (it is
  multiplied by sigma in rad/(V A) to give the phase, section 2.3; summed slice means divided by the
  cell height give V0 in V, section 7), although the `PotentialArray` metadata label reads
  `"units": "eV / e"` (`iam.py:1403`). Because the DC term is
  `N F(0) / (pixel area)`, the slice mean is exactly `sum_j integral V_j d^3r / A_cell` (section 7).
  An optional isotropic displacement `sigmas` multiplies `F(k)` by `exp(-2 pi^2 sigma^2 k^2)`
  (`integrals.py:442-447`).
* Finite projection (`integrals.py:728-1027`): radial table of `integral_a^b V(sqrt(r^2+z^2)) dz` by
  fixed-order Gauss quadrature (`quad_order=8`), radial cutoff where `|V| < cutoff_tolerance`
  (default `1e-4` V, `integrals.py:756, 810-813`), cosine taper from `0.85` of the cutoff
  (`integrals.py:758, 821-831`), linear interpolation on a geometric radial grid starting at
  `min(sampling)/2` and clamped inside it (`integrals.py:546-554, 843-844`), evaluated at pixel
  centres in real space; NOT periodic (`periodic=False`, `integrals.py:781`; out-of-grid pixels are
  skipped, `integrals.py:540`).

### 2.2 Interaction constant sigma (SECTION_READ + REPRODUCED)

`energy2sigma(energy)` (`abtem/core/energy.py:73-96`) returns
`2 pi m(E) e lambda(E) / h^2` with the relativistic mass `m = (1 + eE/(m_e c^2)) m_e`
(`energy.py:13-43`) and `lambda = h c / sqrt(E (2 m_e c^2 / e + E)) / e * 1e10` Angstrom
(`energy.py:46-70`), all constants from ASE (CODATA 2014). The docstring gives the unit as
"Interaction parameter [1 / (Å * eV)]" (`energy.py:85`); with the potential in V (eV/e) and the
projected potential in V Angstrom, sigma is in rad / (V Angstrom). This is the same quantity as
Kirkland's `sigma = 2 pi / (lambda E) (m_e c^2 + eE) / (2 m_e c^2 + eE)` (form read in Kirkland's
code, `computem slicelib.cpp:2177-2191`, which returns rad/(kV A)). The abTEM docs
(`https://abtem.github.io/doc/user_guide/appendix/multislice_derivation.html`, "Tested against abTEM
v1.0.10") write `sigma = 2 pi m e lambda / h^2` and `t(x,y) = exp[i sigma integral V dz']`
(SECTION_READ).

`scratchpad/sigma_check.py` (REPRODUCED):

```
$ venv/bin/python sigma_check.py
abtem 1.0.10
abtem energy2wavelength(200e3) = 0.0250793403 A
abtem energy2sigma(200e3)      = 7.2884010859e-04 rad/(V A)
abtem relativistic_mass_correction(200e3) = 1.3913902396
closed form CODATA2018: lambda = 0.0250793405 A, sigma = 7.2884010410e-04 rad/(V A)
relative difference abtem vs CODATA2018 closed form: lambda -5.31e-09, sigma 6.17e-09
Kirkland slicelib sigma(200)/1000 = 7.2883988339e-04 rad/(V A); rel. diff abtem 3.09e-07
phase for 12 V x 1 A slice = 8.746081e-03 rad
```

**sigma(200 keV) = 7.28840e-4 rad V^-1 A^-1** (abTEM 1.0.10; 7.2884010e-4 to 6e-9 relative against
the repository's CODATA 2018 constants; lambda = 0.02507934 A agrees with
`docs/physics_conventions.md`).

### 2.3 Sign of the transmission function and of the propagator (SECTION_READ + REPRODUCED)

* Transmission: `PotentialArray._transmission_function` returns `complex_exponential(sigma * array)`
  (`abtem/potentials/iam.py:1415-1420`), and `complex_exponential(x) = cos(x) + i sin(x)`
  (`abtem/core/complex.py:8-15`; cupy path `cp.exp(1.0j * x)`, `complex.py:82-83`). So
  `t = exp(+i sigma V_z)`. It multiplies the wave (`iam.py:1568-1571`; `conjugate=True` would use
  `conj(t)`).
* Propagator: `exp(-i pi lambda dz k^2)` with `k` from `numpy.fft.fftfreq(n, d)` (cycles/A)
  (`abtem/multislice.py:63-69`; `abtem/core/grid.py:564-600`).
* The docs write the full wave as `psi_full = psi(x,y) exp(2 pi i z / lambda)` and propagation along
  +z (multislice-derivation and conventions pages, "Tested against abTEM v1.0.10").

`scratchpad/sign_test.py` (REPRODUCED, float64):

```
$ venv/bin/python sign_test.py
t at V_z=100 V A: arg = 0.072884 rad; sigma*100 = 0.072884; max|t-exp(i sigma V)| = 0.0e+00
carrier +q0: centroid x moves +9.797 A for dz = 1000 A; paraxial prediction +lambda q0 dz = +9.797 A
plane wave q0: phase change 0.544112 rad; -pi*lam*dz*q0^2 wrapped = 0.544112 rad
tilt_x = +10.0 mrad: centroid x moves +10.000 A; +dz tan(theta) = +10.000 A; <k_x> after = 0.00e+00 1/A (carrier run: 0.3906)
Si at (x=1.0, y=3.0) A -> argmax index (10, 30) (axis 0 = x, axis 1 = y)
```

Conclusion: a wave component `exp(+2 pi i q0 x)` travels toward +x and loses phase
`pi lambda dz q0^2` relative to the axial beam; a positive potential advances the phase by
`+sigma V_z`. This is exactly the `exp(+i(k.r - omega t))` convention with the numpy FFT sign used by
this repository (`docs/physics_conventions.md`, wave and Fourier rows): **abTEM phases need no
conjugation to be compared with the repository's.** Array axis 0 is x and axis 1 is y (REPRODUCED);
the `Waves` docstring says the opposite ("The second-to-last and last dimensions are the wave
function `y`- and `x`-axes", `abtem/waves.py:385-386`); trust the code.

Order within a slice: transmission first, then propagation over the slice thickness
(`abtem/multislice.py:417-421`; docs conventions page: "the transmission step is taken before the
free-space propagation, and thus effectively the potential within a slice is projected to its bottom
surface"). The transmission function is band-limited before use (`multislice.py:400-405`) and the
propagator carries the 2/3 antialias aperture (`multislice.py:173-177`; `abtem/antialias.py:40-53`;
`abtem/core/abtem.yaml:44-48`, cutoff `0.6666666`, taper `0.01`). After the last slice the wave has
been propagated to the far face of the cell.

---

## 3. Calling the parameterisation without abTEM's `Potential`

### 3.1 API (SECTION_READ; exact signatures)

Per-atom radial functions, `abtem/parametrizations/__init__.py`:

| Call | Returns | Locator |
|---|---|---|
| `KirklandParametrization(parameters="kirkland.json", sigmas=None)` | object | `__init__.py:405-408` |
| `LobatoParametrization(parameters="lobato.json", sigmas=None)` | object | `__init__.py:496-499` |
| `PengParametrization(parameters="peng_high.json", sigmas=None)` | object | `__init__.py:586-589` |
| `.potential(symbol, charge=0.0)` | callable `V(r)`, r in A, V in V | `__init__.py:120-137` |
| `.projected_potential(symbol, charge=0.0)` | callable `V_z(r)` (infinite projection), V A | `__init__.py:158-176` |
| `.scattering_factor(symbol, charge=0.0)` | callable `f_e(k^2)`, A | `__init__.py:139-156` |
| `.projected_scattering_factor(symbol, charge=0.0)` | callable `F(k^2)` = 2D Fourier transform of `V_z`, V A^3 | `__init__.py:178-196` |
| `.finite_projected_potential(symbol, charge=0.0)` | Peng only: callable `(r, a, b)` with erf limits | `__init__.py:234-249`, `582` |
| `.get_function(name, symbol, charge=0.0)` | generic; `charge > 0` raises `NotImplementedError` | `__init__.py:273-309` |
| `.scaled_parameters(symbol, name)` | rescaled arrays (section 1.4) | `__init__.py:446-463, 537-553, 591-636` |

Projected potential of one slice on a grid, `abtem/integrals.py`:

| Call | Behaviour | Locator |
|---|---|---|
| `ScatteringFactorProjectionIntegrals(parametrization="lobato").integrate_on_grid(atoms, a, b, gpts, sampling, device="cpu")` | infinite projection of all atoms passed (uses only `atoms.numbers` and `atoms.positions[:, :2]`; `a`, `b` ignored), periodic; returns real `(gpts[0], gpts[1])` array in V A | `integrals.py:398-505` |
| `QuadratureProjectionIntegrals(parametrization="lobato", cutoff_tolerance=1e-4, inner_cutoff_factor=2.0, taper=0.85, integration_step=0.02, quad_order=8).integrate_on_grid(atoms, a, b, gpts, sampling, device="cpu")` | finite projection between absolute z limits `a`, `b`; NOT periodic: the caller must add periodic images (`abtem.atoms.pad_atoms(atoms, margins, directions="xyz")`) | `integrals.py:728-1027`; `atoms.py:1043` |

`atoms` must be an `ase.Atoms` (or an object with `.numbers` and `.positions`). `device="gpu"`
uses cupy if installed (not tested here).

### 3.2 Minimal working example on a small Si cell (REPRODUCED)

`scratchpad/api_example.py` (8-atom Si cell, `a = 5.4309 A` from `reflection_holo.constants.A_SI_A`,
atomic planes shifted by `a/8` so that each lies in the middle of an `a/4` slice; float64):

```python
from abtem.parametrizations import KirklandParametrization
from abtem.integrals import ScatteringFactorProjectionIntegrals
vz = KirklandParametrization().projected_potential("Si")          # r [A] -> V_z [V A]
integ = ScatteringFactorProjectionIntegrals(parametrization="kirkland")
v0 = integ.integrate_on_grid(slice_atoms, a=0.0, b=dz, gpts=(64, 64), sampling=(a/64, a/64))
```

```
$ venv/bin/python api_example.py
abtem 1.0.10 precision float64
r [A]               [0.05 0.1  0.2  0.5  1.   2.  ]
Kirkland V_z(r) [V A] [646.5244 413.4692 222.6396  76.1161  19.6489   1.2742]
Lobato   V_z(r) [V A] [646.6046 413.6265 222.8021  76.3008  19.7637   1.352 ]
Kirkland V(r)   [V]   [2.9768e+03 1.1768e+03 3.7956e+02 6.6432e+01 1.2393e+01 5.8284e-01]
dtype of Lobato V_z: float32 (lobato.py:97 casts to float32)
Kirkland vzatom  [V A] [646.5248 413.4694 222.6397  76.1162  19.6489   1.2742]
max rel diff abTEM-Kirkland vs vzatom: 5.19e-07
atoms in slice 0: 2 xy = [[0.0, 0.0], [2.7154, 2.7154]]
slice 0: shape (64, 64) dtype float64 min 0.6566 max 879.3886 mean 18.876237 V A
Potential array shape (4, 64, 64) sampling (0.0848578125, 0.0848578125)
max |Potential slice 0 - integrate_on_grid| = 0.000e+00 V A
reuse of one integrator at a new sampling, same gpts: max |diff| = 1.163e+02 V A (0 means safe)
reuse at new gpts raises ValueError operands could not be broadcast together with shapes (64,64) (32,32)
finite: direct call mean 9.600681 V A, Potential(projection='finite') slice-0 mean 18.775760 V A
cutoff radius Si (tolerance 1e-4 V): 5.751 A
```

(One further output line, `argmax index (axis0, axis1) = (0, 0)`, is omitted: the atom at the
origin cannot distinguish the axes; the asymmetric test in section 2.3 does.)

Findings:
1. The per-slice call reproduces abTEM's own `Potential` slice bit-for-bit (difference 0.0), so the
   kernel can build each slice from its own atom list without the `Potential` object (REPRODUCED).
2. abTEM's Kirkland `V_z(r)` equals Kirkland's own `vzatom()` formula (re-implemented from
   `computem slicelib.cpp:2495-2527` with his constants) to 5.2e-7 relative, the size of the
   difference between Kirkland's 1989 constants and ASE's CODATA 2014 (REPRODUCED).
3. Caching trap: `ScatteringFactorProjectionIntegrals` caches the k-space factor per chemical symbol
   only (`integrals.py:451-460`). Reusing one integrator at a new sampling with the same `gpts` is
   silently wrong (116 V A error above); at new `gpts` it raises `ValueError`.
   `QuadratureProjectionIntegrals` also caches its table per symbol only (`integrals.py:905-911`).
   Instantiate one integrator per grid (REPRODUCED).
4. Calling the finite integrator directly without periodic images loses the parts of atoms that
   cross the cell edge (mean 9.60 instead of 18.78 V A above; REPRODUCED).
5. Precision: `lobato.projected_potential` always returns float32 (`lobato.py:97`); the Kirkland and
   Lobato projected scattering factors use a float32 `pi` inside numba (`kirkland.py:59`,
   `lobato.py:102-103`), about 3e-8 relative, irrelevant at k = 0.

---

## 4. Complex (absorptive) potential

SECTION_READ:
* No parameterisation, integrator or `Potential` option produces an imaginary part: all slice arrays
  are allocated real (`get_dtype(complex=False)`, `abtem/potentials/iam.py:846-848, 871-874`;
  `abtem/integrals.py:476-505, 922-924`). A grep of the package for `absorp`, `imaginary` and
  `optical potential` finds no absorption code (only measurement methods named `imag`).
* The only path that would carry an imaginary part is a user-built `PotentialArray` with a complex
  array: `complex_exponential` has a numba signature `complex64(complex64)` besides the two real
  ones (`abtem/core/complex.py:8-15`), and `cos(z) + i sin(z) = exp(iz)` for complex `z`, so
  `t = exp(i sigma (V + iW)) = exp(i sigma V) exp(-sigma W)`. There is no `complex128(complex128)`
  signature.
* Documentation: the Bloch-wave tutorial (not multislice) says "we can add an imaginary component to
  emulate absorption, with a typical but not generally very well justified value of 10%:
  F_absorption(g) = F(g) + 0.1 i F(g)" (`https://abtem.github.io/doc/user_guide/tutorials/blochwave.html`,
  "Tested against abTEM v1.0.10"); no API keyword for it was found in `abtem/bloch/dynamical.py`
  (grep). That 10 % rule is exactly the kind of tuned absorption the [B15] warning forbids.

REPRODUCED (`scratchpad/absorb_test.py`; V = 10 V A, W = 1 V A per slice, 3 slices):

```
float32 complex64 -> |t| = 0.99927133, exp(-sigma W) = 0.99927143; arg t = 0.007288, sigma V = 0.007288
   multislice over 3 slices: mean |psi| = 0.99781585; exp(-3 sigma W) = 0.99781587; dtype complex64
float64 complex128 -> transmission_function raises TypeError ufunc '_complex_exponential' not supported for the input types, ...
   multislice raises TypeError ufunc '_complex_exponential' not supported for the input types, ...
```

Answer: abTEM 1.0.10 has no absorptive-potential feature. An absorber can be injected only as a
hand-built complex64 `PotentialArray` in float32 mode (undocumented behaviour of a numba signature);
float64 fails. The sign is the physical one (`W > 0` damps). The optical potential itself must be
sourced elsewhere (docs/05 section 4.3 item 7). For the abTEM cross-check this is consistent with
docs/05's plan to compare with the absorber inert.

---

## 5. Propagator and tilt in abTEM 1.0.10

### 5.1 Propagator: Fresnel (paraxial) only in the release (SECTION_READ)

* `_fresnel_propagator_array(thickness, gpts, sampling, energy, device, order=1)`:
  `f = exp(-i k^2 pi dz lambda)`; with `order == 2` an extra factor
  `exp(-i pi dz lambda^3 k^4 / 4)` "Eq. (4) from Microscopy and Microanalysis (2020), 26, 1147-1157";
  `order > 2` raises "Only orders 1 and 2 are supported in Fourier space. For higher orders, use the
  realspace multislice instead." (`abtem/multislice.py:46-77`).
* `FourierMultislice` dataclass: `order: Literal[1, 2] = 1` (`multislice.py:495-515`), the default
  algorithm of `multislice_and_detect` (`multislice.py:546`). Class docstring: "The Fresnel
  propagator is used for propagating wave functions using the near-field approximation (Fresnel
  diffraction)." (`multislice.py:113-117`).
* There is no `"exact"` order in 1.0.10 and no evanescent handling. `RealSpaceMultislice`
  (finite-difference, `order`, `expansion_scope="propagator"|"full"`, `derivative_accuracy=6`,
  `max_terms=80`; `multislice.py:518-539`) is a separate real-space algorithm; with
  `expansion_scope="full"` it can return backscattered waves (`multislice.py:566-583`, citing
  Micron 190 (2025) 103778 in `abtem/finite_difference.py:510, 608, 662`). Not examined further.

Version contrast (REPRODUCED from git): on GitHub `HEAD` `fba42a98` (2026-09-22,
`abtem/_version.py: __version__ = "1.1.0"`, 237 commits after tag v1.0.10, unreleased on PyPI)
`_fresnel_propagator_array` has `order: Literal[1, 2, "exact"] = "exact"` (line 57), an exact branch
`sqrt(1 - x)` over propagating components (lines 72-90) and a paraxial phase-error warning
(lines 104-123). So the "exact propagator with evanescent handling" of report D and docs/05 section
4.3 item 9 exists only in the unreleased development tree, not in any PyPI release.

### 5.2 Tilt implementation (SECTION_READ + REPRODUCED)

* Tilt is not a phase ramp on the wave: `PlaneWave` builds a flat array and `tilt.apply` only tiles
  it and writes `base_tilt_x/y` into the metadata (`abtem/waves.py:1728-1755`;
  `abtem/tilt.py:107-123, 179-185, 304-317`).
* The propagator is multiplied by `exp(-2 pi i k_x tan(theta_x) dz) exp(-2 pi i k_y tan(theta_y) dz)`,
  angles in mrad (`abtem/multislice.py:80-110`, applied at `179-185` for a base tilt and `189-206`
  for tilt ensembles). This shifts the wave by `+dz tan(theta)` per slice (a shear); the potential is
  still projected along z.
* REPRODUCED (section 2.3): `base_tilt_x = +10 mrad` moves a packet by `+10.000 A` over 1000 A
  (`dz tan(theta) = 10.000 A`) with `<k_x> = 0` (no carrier). A positive abTEM tilt therefore
  corresponds to an illuminating Fourier component at `+q0 = sin(theta)/lambda`, the repository's
  sign (`docs/physics_conventions.md`, units table: "theta = +lambda q").
* Documentation sign conflict: the docs give
  `P(k) = exp[-i pi lambda k^2 dz + 2 pi i dz (k_x tan(theta_x) + k_y tan(theta_y))]`
  (`https://abtem.github.io/doc/user_guide/walkthrough/multislice.html`, "Small-angle beam tilt",
  "Tested against abTEM v1.0.10"), with the opposite sign of the tilt term to the code. The code and
  the REPRODUCED shift above are authoritative.

### 5.3 Documented tilt limits, quoted (SECTION_READ)

| Where | Text |
|---|---|
| `abtem/waves.py:1858-1860` (`Probe` docstring) | "tilt : two float, two 1D :class:`.BaseDistribution`, 2D :class:`.BaseDistribution`, optional / Small-angle beam tilt [mrad]. This value should generally not exceed one degree." |
| `abtem/waves.py:1679-1681` (`PlaneWave` docstring) | "Small-angle beam tilt [mrad] (default is (0., 0.)). Implemented by shifting the wave functions at every slice." (no limit stated) |
| `abtem/waves.py:1457-1458, 1706-1707` | "The small-angle tilt of applied to the Fresnel propagator [mrad]." |
| docs, multislice walkthrough, "Small-angle beam tilt" | "This is equivalent to shifting the wave function between slices and is only valid for very small tilts of no more than about 100 mrad." |

So the "should generally not exceed one degree" (17.45 mrad) statement of docs/05 is confirmed for
1.0.10 but it sits in the `Probe` docstring (line 1860), not the `PlaneWave` one; the version-matched
user guide gives a different limit (about 100 mrad). Report D's locator `abtem/waves.py:2351` was for
the 1.1.0 development tree.

### 5.4 Size of the shear error for the specular beam (REPRODUCED; DERIVED_HERE formula)

For a beam tilted by theta the specular beam leaves at -theta, i.e. at `q = -2 sin(theta)/lambda` on
the untilted Fourier grid; exact free-space propagation gives it the same `k_z` as the incident beam
(relative phase 0). abTEM's sheared Fresnel kernel gives
`(4 pi dz / lambda) sin^2(theta) (1/cos(theta) - 1)`, approximately `2 pi dz theta^4 / lambda`
(DERIVED_HERE). `scratchpad/tilt_check.py` evaluates abTEM's actual propagator array
(`FresnelPropagator().get_array`, 0.13 A pixels, 1 A slices, 889 A cell):

```
theta 10.000 mrad: specular q = -0.7982 1/A (20.0 mrad, band edge 64.3 mrad, |P| = 1.000); phase error 2.510e-06 rad per A, 0.002 rad over 889 A; 2 pi theta^4 / lambda = 2.505e-06 rad/A
theta 17.453 mrad: specular q = -1.3916 1/A (34.9 mrad, band edge 64.3 mrad, |P| = 1.000); phase error 2.324e-05 rad per A, 0.021 rad over 889 A; 2 pi theta^4 / lambda = 2.325e-05 rad/A
theta 24.000 mrad: specular q = -1.9137 1/A (48.0 mrad, band edge 64.3 mrad, |P| = 1.000); phase error 8.312e-05 rad per A, 0.074 rad over 889 A; 2 pi theta^4 / lambda = 8.312e-05 rad/A
theta 48.000 mrad: specular q = -3.8255 1/A (95.9 mrad, band edge 64.3 mrad, |P| = 0.000); phase error 0.000e+00 rad per A, 0.000 rad over 889 A; 2 pi theta^4 / lambda = 1.330e-03 rad/A
```

This is free-space kinematics only (no crystal, no refraction); the M2 convergence test of docs/05
is still required. At 48 mrad tilt the specular beam (96 mrad) lies outside the 2/3 band at 0.13 A
pixels and is removed by the aperture: a 48 mrad shear tilt needs pixels below about 0.087 A
(DERIVED_HERE: `2/3 / (2 dx) >= 2 sin(theta)/lambda`).

---

## 6. Licence and what a dependency on abTEM means

SECTION_READ / REPRODUCED:
* PyPI metadata of 1.0.10: `License-Expression: GPL-3.0-or-later` (METADATA of the wheel; PyPI JSON
  `license_expression`). `pyproject.toml:24 license = "GPL-3.0-or-later"`; `setup.cfg:7 license = GPL`,
  classifier `License :: OSI Approved :: GNU General Public License v3 (GPLv3)` (`setup.cfg:10`); the
  sdist ships `LICENSE`, the GPL v3 text (674 lines, "Version 3, 29 June 2007").
* Packaging defect: `pyproject.toml:25 license-files = ["LICENCE"]` names a file that does not exist
  (the file is `LICENSE`), and the installed wheel's `abtem-1.0.10.dist-info/` contains no licence
  file (REPRODUCED by listing). The licence is still GPL-3.0-or-later.
* The two independent code sources of the same tables are also GPL: Kirkland's computem
  (`slicelib.cpp:4-9`, "GNU General Public License ... either version 3 of the License, or (at your
  option) any later version") and Lobato's MULTEM (`src/atomic_data.hpp:1-17`, same wording).
* This repository declares no licence (no LICENSE file; `pyproject.toml` has no `license` field) and
  its remote is `https://github.com/alihasuna/Holography` (visibility not checked).

GNU GPL FAQ (`https://www.gnu.org/licenses/gpl-faq.html`, SECTION_READ): #IfLibraryIsGPL "Yes,
because the program actually links to the library. As such, the terms of the GPL apply to the entire
combination. The software modules that link with the library may be under various GPL compatible
licenses, but the work as a whole must be licensed under the GPL." #GPLRequireSourcePostedPublic
"You are free to make modifications and use them privately, without ever releasing them."

Consequences (interpretation, not legal advice; UNVERIFIED as law):
1. Private use (Ali's machine, the group) of a repository that imports abTEM carries no GPL
   obligation.
2. If the repository is distributed (a public GitHub repository counts as distribution) while it
   imports abTEM, the combined work must be offered under GPL-3.0(-or-later); the repository's own
   files may carry a GPL-compatible licence (e.g. MIT, BSD, Apache-2.0) but the whole is GPL. This
   matches the open item in docs/05 section 6 ("the distribution licence of this repository must be
   decided against them"): Prismatic, prismatique and sim-trhepd-rheed are already GPL.
3. Copying abTEM code (for example `kirkland.py`, the JSON tables, or the projection routine) into
   `reflection_holo/` makes that file a derivative work under GPL-3.0-or-later with its notices.
   Re-implementing the published formulas from the papers (Kirkland's form is a few lines) and
   loading the numbers at run time from the installed abTEM, or typing them from the paper, avoids
   copying code; whether a numeric table is protectable is a separate legal question (UNVERIFIED).
4. Practical recommendation: keep abTEM an optional cross-check dependency (an extra such as
   `crosscheck = ["abtem==1.0.10"]`; not added, since this task may not edit `pyproject.toml`), import
   it only in the cross-check and provenance tools, and let the manifest record its version, commit
   `164e644f` and licence.

---

## 7. Mean inner potential of Si implied by each parameterisation (SM17 planned test)

Definition: `V0 = (1/Omega) integral_cell V d^3r = (1/Omega) sum_j integral V_j d^3r` over the 8
atoms of the diamond cell, `Omega = a^3`, `a = 5.4309 A` (ASSUMPTION B2,
`reflection_holo.constants.A_SI_A`). Per-atom integral computed (1) analytically as abTEM's
`projected_scattering_factor(symbol)(k^2 = 0)`, (2) by radial quadrature
`4 pi integral r^2 V(r) dr` of abTEM's `potential(symbol)`, (3) as `f_e(0)/kappa` (asserted equal
to (1) to 1e-6); then V0 from the pixel mean of abTEM's own `Potential` for the cell (infinite and
finite projection). Script: `tools/provenance_checks/abtem_mip.py` (this task; run time 7 s).

```
$ venv/bin/python tools/provenance_checks/abtem_mip.py
abTEM 1.0.10; precision float64; 1/kappa = 2 pi a0 e = 47.87764685 V A^2
Si diamond cell: a = 5.4309 A (ASSUMPTION B2), Omega = 160.182629 A^3, 8 atoms
parameterisation                       f_e(0) Si [A] intV Si analytic  intV Si radial  rel.diff     intV O  V0 Si [V]  -12.0 V   /12.0  -12.53 V  /12.53
--------------------------------------------------------------------------------------------------------------------------------------------------------
kirkland (kirkland.json)                    5.814284       278.374232      278.374232   2.2e-16    95.2643    13.9028   +1.903  1.1586    +1.373  1.1096
lobato (lobato.json, abTEM default)         5.836000       279.413955      279.413947  -2.8e-08    97.1485    13.9548   +1.955  1.1629    +1.425  1.1137
peng (peng_high.json, class default)        5.818200       278.561725      278.561725   0.0e+00    94.9605    13.9122   +1.912  1.1594    +1.382  1.1103
peng (peng_low.json)                        5.826800       278.973473      278.973473  -2.2e-16    94.9605    13.9328   +1.933  1.1611    +1.403  1.1120
Units: f_e(0) in A; intV = integral V d^3r per atom in V A^3; V0 in V.
intV O is given for later use (SiO2 overlayer); it is not used for the Si V0.
Grid check with abtem.Potential on the 8-atom cell (48 x 48 pixels, 4 slices of a/4):
  kirkland  infinite projection: V0 = 13.902842 V (analytic 13.902842 V); finite projection: V0 = 13.775225 V (-9.18e-03 relative)
  lobato    infinite projection: V0 = 13.954769 V (analytic 13.954769 V); finite projection: V0 = 13.830853 V (-8.88e-03 relative)
  peng      infinite projection: V0 = 13.912206 V (analytic 13.912206 V)
  lobato    infinite projection, float32 (abTEM default precision): V0 = 13.954769 V (+3.0e-09 relative)
  lobato    infinite projection with sigmas={'Si': 0.1} (test value): V0 = 13.954769 V
```

Finite-projection convergence with pixel size (Kirkland, `scratchpad/finite_conv.py`, REPRODUCED):

```
gpts  24 (0.2263 A): kirkland finite V0 = 13.44780 V, infinite V0 = 13.90284 V
gpts  48 (0.1131 A): kirkland finite V0 = 13.77523 V, infinite V0 = 13.90284 V
gpts  96 (0.0566 A): kirkland finite V0 = 13.86862 V, infinite V0 = 13.90284 V
gpts 192 (0.0283 A): kirkland finite V0 = 13.89330 V, infinite V0 = 13.90284 V
```

Additional value (REPRODUCED, `scratchpad/cmp_lobato.py` plus the same formula): Lobato's own
MULTEM table gives Si `f_e(0) = 5.810700 A`, hence `V0 = 13.8943 V`.

Results (REPRODUCED unless marked):
* Every IAM parameterisation shipped by abTEM gives **V0(Si) = 13.90 to 13.95 V**: Kirkland
  13.903 V, Lobato (abTEM table) 13.955 V, Peng high 13.912 V, Peng low 13.933 V (Lobato, MULTEM table:
  13.894 V). The spread between parameterisations is 0.06 V (0.4 %).
* Against ASSUMPTION B1 (12.0 V): +1.90 to +1.96 V (ratio 1.159 to 1.163). Against the DFT value
  12.53 V (Schowalter, Kruse and Rosenauer, arXiv:2607.05948v1, Fig. 2c, as recorded in
  docs/model_assumptions.md B1): +1.37 to +1.43 V (ratio 1.110 to 1.114). The IAM therefore does
  NOT reproduce either value; the excess is the expected size of the bonding (charge-transfer)
  reduction that the IAM omits (abTEM's own docs: IAM "neglects bonding effects", potentials
  walkthrough; the magnitude attribution is DERIVED_HERE, not sourced).
* Indicative phase consequence (DERIVED_HERE, linear use of the B1 sensitivities
  -0.34 rad/V at (4,-4,4) and -0.20 rad/V at (6,-6,6)): using the Kirkland IAM potential unmodified
  instead of 12.0 V changes `|Delta_phi|` by about 0.65 rad at (4,-4,4) and 0.38 rad at (6,-6,6);
  instead of 12.53 V by about 0.47 and 0.27 rad. Refraction in the multislice kernel will follow
  V0 = 13.9 V unless the potential is corrected.
* Construction dependence: with the infinite (Fourier-space) projection the grid mean equals the
  analytic value to machine precision at any sampling, also in float32 (3e-9) and with a
  Debye-Waller `sigmas` (unchanged, because the factor is 1 at k = 0). The finite real-space
  projection underestimates V0 by 0.9 % at 0.113 A pixels and 3.3 % at 0.226 A, converging as the
  pixel shrinks (0.07 % at 0.028 A); the loss comes from the clamped core and the cutoff taper
  (section 2.1). A kernel that samples `V_z(r)` in real space must report the V0 of the grid it
  actually uses (docs/05 section 4.3 item 6), not the analytic value.
* Per-atom O integral (for a later SiO2 overlayer): 95.26 (Kirkland), 97.15 (Lobato abTEM),
  94.96 V A^3 (Peng high and low). Lobato's O value differs from Lobato's own MULTEM table by 2.05 %
  (section 8, blocker 4).

Suggested wording for source-map row SM17 (not written here: this task may not edit
`docs/source_map.tsv`): "Parameterisation read in version-matched code (abTEM 1.0.10, Kirkland table
verified bit-for-bit against Kirkland's computem source); MIP of the IAM parameterisation for Si
(a = 5.4309 A) 13.90 V (Kirkland; 13.89-13.95 V over all tables), REPRODUCED by
`tools/provenance_checks/abtem_mip.py`; exceeds B1 (12.0 V) by 1.90 V and the DFT value 12.53 V by
1.37 V: test RUN, result = IAM does not reproduce the sourced/assumed V0."

---

## 8. Recommendation for the kernel, and what blocks or constrains use

Recommended parameterisation: **Kirkland** (abTEM `KirklandParametrization`, table
`kirkland.json`). Reasons: the table is independently verified against Kirkland's own current code for
all 103 elements (Si bit-identical, section 1.2); the functional form (three Yukawa plus three
Gaussian terms, closed-form `V`, `V_z` with `K0`, and `F(k)`) is simple enough to re-implement from the
formula in numpy/cupy; abTEM's `V_z` matches Kirkland's `vzatom()` to 5e-7. Lobato (abTEM's
default) is the documented higher-angle choice but its table provenance is contested (blocker 4); use
it as a sensitivity run (V0 differs by +0.05 V, `f_e(0)` by +0.4 % for Si).

Recommended API for the kernel's potential (Fourier-space, infinite projection per slice, matching
abTEM's default so that the M2 cross-check compares like with like):
* per species, on the kernel's own grid: `F = KirklandParametrization().projected_scattering_factor("Si")(k2)`
  with `k2 = kx[:, None]**2 + ky[None, :]**2` from `numpy.fft.fftfreq` (V A^3), times the structure
  factor of the atoms in the slice, divided by the cell area; or, to reproduce abTEM exactly
  including its bilinear delta spreading and sinc correction,
  `ScatteringFactorProjectionIntegrals("kirkland").integrate_on_grid(atoms_in_slice, a, b, gpts, sampling)`
  with a fresh integrator per grid (section 3.2, finding 3);
* radial checks: `projected_potential("Si")(r)` (V A) and `potential("Si")(r)` (V);
* V0 check: `projected_scattering_factor("Si")(0.0)` = per-atom volume integral (V A^3).
* sigma: `abtem.core.energy.energy2sigma(200e3)` = 7.28840e-4 rad/(V A); `t = exp(+i sigma V_z)`.

Blockers and constraints (each labelled in the sections cited):
1. **No exact propagator in any released abTEM** (section 5.1). docs/05 section 4.3 item 9 ("abTEM
   provides one") and the "abTEM 1.1" cross-check refer to the unreleased development tree. Options:
   pin a git commit of the development branch (for example `fba42a98`, version string 1.1.0) for the
   cross-check, or cross-check with 1.0.10 `order=1`/`order=2` Fresnel and state the paraxial error.
   Decision needed by the orchestrator.
2. **Tilt**: 1.0.10 tilt is a propagator shear, documented as "should generally not exceed one
   degree" (Probe docstring, `waves.py:1860`) and "no more than about 100 mrad" (user guide); the
   user-guide formula has the opposite sign to the code. Free-space shear error for the specular
   beam: 0.074 rad over 889 A at 24 mrad; at 48 mrad the specular beam leaves the 2/3 band at
   0.13 A pixels (section 5.4). The M2 convergence test remains required.
3. **Absorption**: no optical-potential feature; only a hand-built complex64 `PotentialArray` in
   float32 works, complex128 raises `TypeError` (section 4). The absorber source is still missing.
4. **Lobato table provenance conflict**: abTEM's `lobato.json` and Lobato's own MULTEM table differ
   for all 103 elements (Si `f_e(0)` 5.8360 vs 5.8107 A, 0.44 %; O 2.0291 vs 1.9884 A, 2.05 %;
   REPRODUCED, `scratchpad/cmp_lobato.py`, MULTEM commit `23c37132`, 2025-07-03). Which one is the
   2014 paper's table is UNVERIFIED (paper not read). The Peng files' source tables are not cited by
   abTEM (UNVERIFIED).
5. **IAM MIP 13.9 V** exceeds both 12.0 V and 12.53 V (section 7). Whether the kernel keeps the IAM
   refraction, or adds a uniform correction inside the crystal to reach a sourced V0, is a modelling
   decision that must become a labelled ASSUMPTION; it is not made here.
6. **Licence**: GPL-3.0-or-later; importing abTEM in a distributed repository makes the combination
   GPL (section 6). Keep it an optional cross-check dependency; do not copy its code.
7. **Precision and traps**: abTEM defaults to float32 (`abtem.yaml:7-8`); set
   `abtem.config.set({"precision": "float64"})` for cross-checks. Integrators cache per symbol
   (silently wrong on grid change); the finite integrator is not periodic when called directly;
   `Waves` docstring axis order is wrong (axis 0 is x). Frozen-phonon seeds: with `seeds=None` abTEM
   draws configuration seeds from `np.random.default_rng(seed=None)` (`abtem/inelastic/phonons.py:235-244`),
   i.e. not reproducible; always pass an explicit seed and record it.
8. **Dependency weight**: abTEM 1.0.10 pulled numba, llvmlite, pyfftw, dask, distributed, zarr,
   pandas, matplotlib, ipywidgets and ipympl into the project venv (section 0.3). `pyproject.toml` does
   not list abTEM.
9. **Slice ordering for the M2 comparison**: abTEM transmits first and then propagates the full
   slice thickness, so its potential acts at the slice ENTRANCE and its output plane is the far face
   of the cell (section 2.3). A kernel that applies the transmission at the slice centre (symmetric
   split) differs by half-slice propagations at the two ends; the cross-check must either use the
   same ordering or propagate one result by half a slice before comparing.

Not verified here: the Kirkland book tables and formulas (B06 unread; abTEM cites the 2nd edition,
the repository lists the 3rd); the Lobato and Peng papers; GPU behaviour; any multislice run through
a crystal.

---

## 9. Fact table

| # | Fact | Locator | Label |
|---|---|---|---|
| F1 | abTEM pinned at 1.0.10 = tag v1.0.10 = commit `164e644f`; PyPI sdist, tag and installed tree identical | section 0 | REPRODUCED |
| F2 | Parameterisations shipped: Lobato (default), Kirkland, Peng (high default; low; ionic), Ewald; plus an unused Waasmaier-Kirfel X-ray table | `abtem/parametrizations/__init__.py:377-667`; `data/*.json` | SECTION_READ |
| F3 | Si and O present in kirkland, lobato, peng_high, peng_low | JSON files | REPRODUCED |
| F4 | Kirkland table = Kirkland's computem table (Si identical, max deviation 6.2e-5 for He only) | `computem slicelib.cpp:697-1948` | REPRODUCED |
| F5 | abTEM Lobato table differs from Lobato's MULTEM table for all elements (Si f_e(0) 0.44 %) | `multem src/atomic_data.hpp:1080-1185` (MULTEM commit `23c37132`) | REPRODUCED |
| F6 | Citations verified on Crossref: 10.1107/S205327331401643X, 10.1016/S0968-4328(99)00033-5, 10.1007/978-1-4419-6533-2, 10.1016/j.ultramic.2015.07.005, 10.1017/s1431927620024605, 10.12688/openreseurope.13015.1 | section 1.3 | REPRODUCED (metadata) |
| F7 | Functional forms and unit scaling via `1/kappa = 2 pi a0 e = 47.8776 V A^2` | `functions/*.py`; `__init__.py:446-636`; `core/constants.py:7-8` | SECTION_READ |
| F8 | sigma(200 keV) = 7.28840e-4 rad/(V A); lambda = 0.02507934 A | `core/energy.py:46-96` | REPRODUCED |
| F9 | `t = exp(+i sigma V_z)`, propagator `exp(-i pi lambda dz k^2)`: the exp(+ik.r) convention, no conjugation needed | `potentials/iam.py:1415-1420`; `multislice.py:69` | REPRODUCED |
| F10 | Parameterisation usable without `Potential`: `integrate_on_grid` reproduces a `Potential` slice exactly | `integrals.py:467-505` | REPRODUCED |
| F11 | No absorptive potential; complex64 `PotentialArray` works in float32 only | `core/complex.py:8-15` | REPRODUCED |
| F12 | Released propagator is Fresnel (order 1 default, 2 optional); "exact" only in unreleased 1.1.0 dev tree | `multislice.py:46-77, 495-515`; git `fba42a98` | SECTION_READ |
| F13 | Tilt = propagator shear `exp(-2 pi i k tan(theta) dz)`, +theta moves beam to +x | `multislice.py:80-110` | REPRODUCED |
| F14 | "should generally not exceed one degree" at `waves.py:1860` (Probe); docs: "no more than about 100 mrad" | section 5.3 | SECTION_READ |
| F15 | Licence GPL-3.0-or-later; LICENSE file missing from the wheel | section 6 | SECTION_READ, REPRODUCED |
| F16 | V0(Si) of the parameterisations: 13.903 V (Kirkland), 13.955 V (Lobato), 13.912 / 13.933 V (Peng high / low) at a = 5.4309 A; +1.90 V vs 12.0 V, +1.37 V vs 12.53 V (Kirkland) | `tools/provenance_checks/abtem_mip.py` | REPRODUCED |
| F17 | Finite real-space projection lowers the grid V0 by 0.9 % at 0.113 A pixels | section 7 | REPRODUCED |
