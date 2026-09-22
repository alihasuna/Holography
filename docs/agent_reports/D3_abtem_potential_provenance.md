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

Status of this file: written incrementally; section 9 is the summary.

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
(`dl/` wheel and sdist, `abtem_git_v1.0.10/` tag checkout, `computem/` Kirkland's own source,
`crossref/` Crossref JSON records, `cmp_kirkland.py`, `sigma_check.py`, `api_example.py`,
`sign_test.py`, `absorb_test.py`, `tilt_check.py`).

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
Kirkland's own code in section 3.3.

