# L2 — Computational open sources read in full (reading plan step 2: P04, S01, S02, P49)

Prepared 2026-09-22 for Ali's project: reflection-mode dark-field electron holography of ion-milled
Si(001) at 200 keV. Author: literature agent L2. Written incrementally; the status line below
says which sections are complete.

Status: COMPLETE (2026-09-22). Sections: 0, 1 (sources read), A (P04), B (S01), C (S02), D (P49), E (confirm/contradict), F (source-map proposals), G (consequences, inference), H (references), I (unverified).

Source policy applied: no DOI, page, equation, quotation or result below is invented. Labels:
METADATA_VERIFIED (identity checked against Crossref or the publisher), SECTION_READ (the passage was
read; locator given), REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE (my arithmetic or algebra
on read facts, marked as inference), UNVERIFIED. Verbatim quotations are at most two sentences and are
in double quotes. Raw files are in the scratchpad (never in the repository):
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/sources/`.
Retrieval date for every file: 2026-09-22.

---

## 0. Inputs read before starting

`docs/07_reading_plan.md`; `docs/04_software_provenance_summary.md`; `docs/agent_reports/D_software_provenance.md`
(sections 0, 1.4, 1.5, 2a to 2h, 3, 5.3, 5.4, 6, 7); `docs/source_map.tsv` rows SM08, SM10a, SM10b,
SM15 (and SM11a, SM11c for context); `docs/agent_reports/B_literature.md` section 6.5 and the
unresolved-details list; `docs/references.bib` entries P04, P05, P49, S01, S02; `docs/05` sections 4.3
and 4.4. The P49 arXiv identifier used below (2306.00271) is the one recorded in `docs/references.bib`
and `B_literature.md` section 6.5; it was then checked on export.arxiv.org (section D).

---

## 1. Sources read (summary; details, all hashes and locators in A.1, B.1, C.1, D.1)

| ID | What | URL actually read | Version | SHA-256 (main file) | Read | Not read |
|---|---|---|---|---|---|---|
| P04 | Ophus 2017 | `https://ascimaging.springeropen.com/articles/10.1186/s40679-017-0046-1` and its PDF (redirected to link.springer.com) | published version, CC BY 4.0 | PDF `847056a080957fa3866cb04e534317907602a7f223e4ae0fd8abb0435e50c98f` | whole text, Eqs. (1)-(13), captions | figure images |
| S01 | prismatique docs | `https://mrfitzpa.github.io/prismatique/` ("latest") and `/0.0/en/` ("0.0") | both built from v0.0.4 (`fb217b3`); no rendered 0.0.1 exists; v0.0.1 docstrings read from tag `7ff247c` (= PyPI wheel) | `hrtem.output.Params` page `799554c8f62a7214c2108c2df96c4c475d6ef33628991f0661b39ac6f21fdbca` | 13 API pages, literature, licence, README, CITATION.cff, build script | examples, STEM pages |
| S02 | Prismatic project | `https://prism-em.com/` (also reached via `prism-em.github.io`), `/about-cite/`, `/docs-params/`, `/docs-outputs/`, `/docs-inputs/`, `/docs-change-log/`, `/downloads-conda-forge/`, `/resources-sim-codes/`, `/docs-compiling/`; `raw.githubusercontent.com/prism-em/prismatic/master/README.md` | site as served 2026-09-22; repo HEAD `d155fb9` (2026-01-30) | README `1066ee7a490f24c404b38706568b8f1da2b59af76fd8c4c4dedcff5e769a2670` | pages listed, README, LICENSE, `src/aberration.cpp` | GUI and STEM tutorials |
| P49 | Kudo, Yamamoto, Hoshi | `https://export.arxiv.org/api/query?id_list=2306.00271`; `https://arxiv.org/pdf/2306.00271v1`; `https://arxiv.org/e-print/2306.00271v1`; `github.com/shuheikudo/trhepd-opt`; Crossref record of the CPC version | arXiv v1 (2023-06-01); code `dc394ba` | PDF `e14fa4a791d886d4be6b25a4de6f71bed47da319fc9f486a306702ceb8970db3` | whole preprint (PDF + LaTeX), code README and output routine | CPC journal full text (paywalled) |
| Crossref | identity checks | `https://api.crossref.org/works/<DOI>` for 9 DOIs (section H) | 2026-09-22 | per DOI in H | metadata | |
| PyPI/conda | package facts | PyPI wheels prismatique 0.0.1, embeam 0.0.1 to 0.0.5; `https://api.anaconda.org/package/conda-forge/pyprismatic` | as listed | prismatique 0.0.1 wheel `343c1ce1c72ebe2d1c4fe789a836169d4107523211bb158d4b7031ffd8ad1051` | embeam `_wavelength`; conda versions | conda-forge feedstock recipe (unreachable) |

Blocked or paywalled: none of the four targets was blocked in this session. Paywalled and needed: P05 (Micron 151,
103141) and the CPC version of P49 (section I).

---

## A. P04 — Ophus, "A fast image simulation algorithm for scanning transmission electron microscopy", Adv. Struct. Chem. Imaging 3, 13 (2017)

### A.1 What was read

| Item | Value |
|---|---|
| Identity | Crossref `https://api.crossref.org/works/10.1186/s40679-017-0046-1` (JSON SHA-256 `66c8ba7ffb84891fddc4b7901fb8866fa3aefdef0e2ad6f1cfedab078846a1ac`): title as above, container "Advanced Structural and Chemical Imaging", volume 3, article number 13, issued 2017-05-10, single author Ophus, licence CC BY 4.0. METADATA_VERIFIED |
| HTML read | `https://ascimaging.springeropen.com/articles/10.1186/s40679-017-0046-1` (redirected to `https://link.springer.com/article/10.1186/s40679-017-0046-1`); file `P04_ophus2017.html`, SHA-256 `3f0397a3c158af0532c6462ce90285a8144fe9832c500a338f48683f6469d87b` |
| PDF read | `https://ascimaging.springeropen.com/counter/pdf/10.1186/s40679-017-0046-1.pdf` (redirected to `link.springer.com/content/pdf/...`); file `P04_ophus2017.pdf`, 11 pages, SHA-256 `847056a080957fa3866cb04e534317907602a7f223e4ae0fd8abb0435e50c98f`; text extracted with pypdf 6.19.0 (scratch venv) for page locators |
| Coverage | Read in full: Abstract, Background, Theory and methods (all four subsections), Results and discussion (both subsections), Conclusion, figure captions 1 to 5, reference list entries [18] to [23] and [38]. Figures themselves were not inspected as images (no renderer available); only their captions and the text that describes them |
| Previous label | `docs/references.bib` said SECTION_READ on the strength of the instruction file only; it is now SECTION_READ by this agent with the locators below |

Page map (PDF): Eqs. 1-2 p. 2; Eqs. 3-7 p. 3; Eqs. 8-10 p. 4; Fig. 1 caption p. 4; Eq. 11 p. 5; Eqs. 12-13 and the start
of "Comparison of accuracy" p. 6; the 1 - R^2 error figures p. 7; the peak-position errors and
"PRISM simulations with varying probe size" p. 9; Conclusion p. 10.

### A.2 Extraction table

| # | Fact (as printed, or paraphrased where marked) | Locator | Label | Note |
|---|---|---|---|---|
| A1 | Governing equation, printed as Eq. (1): dpsi(r)/dz = (i lambda / 4 pi) nabla_xy^2 psi(r) + i sigma V(r) psi(r), described as "the Schrödinger equation for fast electrons [20]" for "the slow-moving portion of the wavefunction along the optical axis z" | Theory and methods, "The multislice and Bloch wave methods", Eq. (1), p. 2 | SECTION_READ | lambda relativistic wavelength, sigma "relativistic beam sample interaction constant", V electrostatic potential. The word "paraxial" does not occur; see A-I1 |
| A2 | Eq. (2): psi_f(r) = S psi_0(r), "where psi_0 and psi_f are the incident and exit wavefunctions, respectively" | same subsection, Eq. (2), p. 2 | SECTION_READ | Defines the S-matrix output as the exit wave |
| A3 | Propagator, Eq. (3): Psi_{p+1}(q) = Psi_p(q) exp(-i pi lambda abs(q)^2 t), t = slice thickness, applied in Fourier space; "the left term is interpreted as a Fresnel propagation operator" | same subsection, Eq. (3), p. 3 | SECTION_READ | Sign convention of the propagator: exp(-i pi lambda q^2 t). Identical in form to Prismatic `PRISM02_calcSMatrix.cpp:105` as quoted in report D section 2a |
| A4 | Fourier-transform convention: the paper states only "Psi(q) = F{psi(r)} is the Fourier transform of psi(r)" with q = (q_x, q_y) the 2D Fourier coordinate; F^-1 is "the inverse Fourier transform". No kernel sign, no 2 pi placement statement, no normalisation | Eq. (3) text and Eq. (5) text, p. 3 | SECTION_READ (absence) | The FT sign convention is NOT stated in P04. See A-I2 and A-I3 for what can be inferred |
| A5 | Transmission, Eq. (4): psi_{p+1}(r) = psi_p(r) exp[i sigma V_p^2D(r)], V_p^2D = potential of the atoms in slice p integrated along the beam | Eq. (4), p. 3 | SECTION_READ | Positive sign of the transmission phase |
| A6 | Full step, Eq. (5): psi_{p+1}(r) = F^-1{ F{ psi_p(r) e^{i sigma V_p^2D(r)} } e^{-i pi lambda abs(q)^2 t} } (transmit, then propagate) | Eq. (5), p. 3 | SECTION_READ | Order: transmission first, propagation second, within one step |
| A7 | Slicing rule: slices "can have unequal thickness to better match the atomic coordinates, but should not have thicknesses larger than the average atomic spacing as this could cause errors [20]" | "The PRISM algorithm for STEM simulations", p. 3 | SECTION_READ | Cited to Kirkland 2010 |
| A8 | Anti-aliasing / band limit: "These output wave dimensions can be reduced by a factor of 4, if the multislice simulation uses an antialiasing aperture positioned at half of the maximum scattering angle [20]." | same subsection, after Eq. (6), p. 3 | SECTION_READ | The only band-limit statement in the paper. No 2/3 rule anywhere in P04. The shape of the aperture (circular or rectangular) is not stated |
| A9 | The same rule reappears in the timing estimate: the cut-out reduces multiplications to N^2/(4 f^2), "(note the extra factor of 1/4 is due to storing only the part of S inside the anti-aliasing aperture)" | "Calculation time for PRISM simulations", before Eq. (12), p. 6 | SECTION_READ | Factor 4 in area = factor 2 per axis in the stored output |
| A10 | Plane-wave set, Eq. (6): Psi_{m,n}(q) = delta(q_x - m f Delta_q, q_y - n f Delta_q), with sqrt(m^2+n^2) f lambda Delta_q <= alpha_max; (m, n) integers; "we compute only a subset of all possible periodic plane waves for the simulation cell size, reducing the number of waves calculated by a factor of f^2" | Eq. (6) and following text, p. 3 | SECTION_READ | Incident plane waves are single Fourier components of the periodic cell, on a grid of step f Delta_q (quantised). alpha_max should equal the largest desired probe semi-angle plus f Delta_q (p. 3) |
| A11 | Tilt, algorithmic: Eq. (8) coefficients alpha_{m,n}(r_0) = A(q) exp[-i chi(q)] exp(-2 i pi q . [x_0 - h tan(theta_x), y_0 - h tan(theta_y)]); "the terms h tan(theta_x) and h tan(theta_y) shift the probe back to the center of a cutout region for a given simulation cell of height h and probe tilt angles theta_x and theta_y" | Eq. (8) and text after Eq. (9), p. 4 | SECTION_READ | Tilt in PRISM enters through the probe coefficients plus a geometric recentring shift h tan(theta); nothing is done to the propagator |
| A12 | Tilt placement versus Chen et al. 1995 [38]: "where they include tilts of the various beams in the propagation operator, we have included it in the initial conditions of each beam, which negates the need for an offset term to relate the relative phases of the beams." | end of "The PRISM algorithm for STEM simulations", after Eq. (10), p. 4 | SECTION_READ | Direct statement that PRISM carries beam tilt in the entrance-plane initial condition, not in the propagator |
| A13 | Relative probe/sample tilt is obtained "by moving the probe center away from q = (0,0)" (paraphrase of the sentence listing reusable S-matrix changes) | "PRISM simulations with varying probe size", p. 9 | SECTION_READ | Same mechanism as A11 to A12 |
| A14 | Aberration function, Eq. (9): chi(q) = pi lambda abs(q)^2 C_1 + (pi/2) lambda^3 abs(q)^4 C_3 + ...; enters the PROBE coefficients as exp[-i chi(q)] (Eq. 8) | Eq. (9), p. 4 | SECTION_READ | Sign of the probe aberration phase: exp(-i chi). The reference plane of C_1 is not defined in P04 |
| A15 | Error statements for PRISM interpolation (all for STEM intensities, 80 kV Pt decahedron on 5 nm a-C): "In general, PRISM will always be less accurate than corresponding multislice calculations, unless the PRISM speedup allows for finer pixel sampling, inclusion of higher scattering angles, or a similar improvement." | "Comparison of accuracy between multislice and PRISM", p. 6 | SECTION_READ | |
| A16 | Error sources named: Fourier-interpolation "blurring" growing with f (mixing of adjacent detector angle bins); a small intensity decrease at the highest angles "probably" from the interpolation step; cropping of probe tails at f = 16 (Fig. 3i). Stated exceptions: very large probes (highly defocused or delocalised) and fine diffraction detail such as HOLZ lines | same subsection, p. 6 | SECTION_READ (paraphrase) | None of these is a phase-error statement |
| A17 | Quantitative errors, 1 - R^2 between multislice and PRISM pixel intensities: f = 5 about 0.005 % at all scattering angles; f = 10 about 0.05 % (low), about 1 % (intermediate), about 10 % (high); f = 20 about 1 % (small) and 10 % (medium and high); the f = 20 error is attributed to the cut-out cropping a significant part of the probe | same subsection, Fig. 4e discussion, p. 7 | SECTION_READ | |
| A18 | Peak-fit errors (360 LAADF peaks, 22.5 to 105 mrad detector): mean 2D position error 0.86, 2.8 and 21 pm for f = 5, 10, 20; peak-intensity differences about 1 % for f = 5 and 10, rising rapidly at f = 20 | same subsection, p. 9 | SECTION_READ | Speed-ups quoted: about 40, 280 and 2100 for f = 5, 10, 20 (p. 7) |
| A19 | Output plane: the S-matrix rows are the plane waves after multislice propagation through the sample (Fig. 1c caption; Eq. 2 "exit wavefunctions"); the final probe wave "is typically Fourier transformed" and output as CBED or virtual-detector intensity (Fig. 1f caption) | Eq. (2) p. 2; Fig. 1 caption p. 4 | SECTION_READ | P04 contains no back-propagation of the stored waves and no mid-plane reference. It predates HRTEM mode |
| A20 | HRTEM: P04 is a STEM paper. The only TEM-imaging statement is that multislice "is very efficient for plane wave, conventional TEM image, or diffraction simulations" | Background, p. 2 | SECTION_READ | HRTEM output plane, HRTEM tilt and HRTEM anti-aliasing are NOT ADDRESSED |
| A21 | Implementation of the paper's own results: custom Matlab; multislice methods and atomic potentials "taken from Kirkland [20]"; thermal effects by frozen phonons, "repeating the calculation with different phonon configurations ... and summing the results incoherently"; 80 kV, slice 0.2 nm, pixel 0.01 nm | "Simulation and analysis implementation", p. 4 | SECTION_READ | |
| A22 | Reference [20] is "Kirkland, E.: Advanced Computing in Electron Microscopy. Springer Science & Business Media, New York (2010)" | reference list, p. 10 | SECTION_READ | This is the 2010 (second) edition, not the 3rd edition 2020 recorded as B06; P04 does not settle what the 3rd edition says |
| A23 | Bloch-wave basis "satisfies Eq. 1 everywhere inside the sample boundary, which is assumed to be periodic in all directions" | "The multislice and Bloch wave methods", p. 2 | SECTION_READ | Transmission (Laue-case) framing throughout; no reflection, Bragg case or absorbing boundary is mentioned anywhere in P04 |

Inferences from P04 (not statements of the paper):

| # | Inference | Basis | Label |
|---|---|---|---|
| A-I1 | Eq. (1) omits the second z-derivative and is therefore the paraxial (forward-scattering) equation; Eq. (3) is its exact solution for V = 0 over a slice t. The paraxial error estimate of SM08 is therefore about the form P04 prints, but P04 itself gives no error estimate | A1, A3 | DERIVED_HERE |
| A-I2 | The propagator sign follows from Eq. (1) independently of the FT kernel sign: with nabla_xy^2 mapping to -4 pi^2 q^2 under either sign, dPsi/dz = -i pi lambda q^2 Psi, giving exp(-i pi lambda q^2 t). Eq. (1) with +i lambda/(4 pi) corresponds to a full wave exp(+2 pi i z / lambda) psi, i.e. the exp(+i k.r) convention the project uses (SM03) | A1, A3 | DERIVED_HERE |
| A-I3 | Eq. (8) shifts the probe to r_0 with exp(-2 pi i q . r_0), which is the shift theorem for a synthesis psi(r) = sum Psi(q) exp(+2 pi i q . r) (forward kernel exp(-2 pi i q . r)), the numpy convention. This is consistent with, but not a statement of, a convention | A11 | DERIVED_HERE |
| A-I4 | "Half of the maximum scattering angle" with maximum angle lambda/(2 dx) (Nyquist) gives lambda/(4 dx), the Prismatic tilt ceiling of `params.h:241-242` quoted in report D | A8 | DERIVED_HERE |

---

## B. S01 — prismatique rendered documentation, README and version-matched docstrings

### B.1 What was read, and which version

| Item | Value |
|---|---|
| Rendered site, "latest" | `https://mrfitzpa.github.io/prismatique/` (landing page; SHA-256 `7582463f9b44cb4112b3393a8951cf3c743bed427031919d3137c458d61c1704`) and the `_autosummary` pages for `hrtem.image.Params`, `hrtem.output.Params`, `hrtem.sim.Params`, `hrtem.sim.run`, `hrtem.system.ModelParams`, `sample.ModelParams`, `tilt.Params`, `thermal.Params`, `discretization.Params`, `aperture.Params`, `version`, `hrtem.image.blank_unprocessed_image_signal` |
| Rendered site, "0.0" | the same pages under `https://mrfitzpa.github.io/prismatique/0.0/en/`, plus `literature.html` (SHA-256 `cc0560b3ccd48efb5c19241fe54648ae20375a7bab4b1fc080872c3d729a6e38`), `license.html` (`e8471735ce4695669e205d93e121d05ce869b654883d0df64f21e04dac6eefd1`) and `searchindex.js` (`7dcfe4f7e706f8d1257c025d2de118dca4813bcde8fbe05ff32eb9fd425d3abb`) |
| Page hashes (0.0 copies) | `hrtem.image.Params` `0b0bf04a7931684d27e2af8699b42a0b1da630e22dd19e0f0180dae78edc4767`; `hrtem.output.Params` `799554c8f62a7214c2108c2df96c4c475d6ef33628991f0661b39ac6f21fdbca`; `sample.ModelParams` `356fcbcd915e7eea76fe7ffccffc80ded85ce1fc909b0107b543316d11d444f6`; `tilt.Params` `4f19afd8897781e17f969e937cd75ddb9817347d2964683ca2f7876ad63e0d74`; `thermal.Params` `c6f67ec429a43d1a0d56efe1bf3278c15e34f437b1600242268df22d5cea85b2`; `discretization.Params` `e203d8274a6796f33d105b3c112de2d627c2c32dcfe6e00517c222b94a7b807c`; `aperture.Params` `c3b162e2417bfc4e9c5fdbbf28969e5fdc87a6953640bb8153f4c42120b45733`; `hrtem.system.ModelParams` `d7fbd267c0d7e704ff0528415460d8ef0b23f39e4b510080969e6fa2765573a7`; `hrtem.sim.Params` `e569f312e88056746594948e17885cb28d7dc00acbb0f1f18b898c896aced95d`; `hrtem.sim.run` `0ee8def64403c795399d9b4187dd7f3ea968850a843216c587b0f7da20f0a20e`; `version` `e25b747fd2b58832728690d4efdc37584a40a9f2ce0133a82e39dbbec73d46f9` (the rendered version page prints no version string) |
| Version selector | The site offers exactly two versions, "latest" and "0.0" (landing page, version menu). A line-by-line diff of the 13 downloaded page pairs (path prefix and version label masked) gives 0 differing lines. REPRODUCED |
| What "0.0" is | `docs/build_docs.py` in the repository (read in full; SHA-256 `743de7dddc2f60face1c334bb4afb7dbd24dc7d43bd8b1cd1014a104eceb1140`) builds "latest" from `main` and, for each major.minor, ONE build from the highest patch tag (`version_subset[major][minor] = max(..., patch)`). With tags v0.0.1 to v0.0.4, "0.0" is built from v0.0.4. `main` HEAD is `fb217b3ce9033a8607c5f7ab4b2ae2b4bf518e9d` (2026-01-18) = tag v0.0.4. So both rendered versions document 0.0.4. SECTION_READ |
| Rendered docs for 0.0.1 | DO NOT EXIST. The version-matched 0.0.1 text is the docstrings at git tag v0.0.1 (`7ff247c`, 2025-03-13). The PyPI wheel `prismatique-0.0.1-py3-none-any.whl` (SHA-256 `343c1ce1c72ebe2d1c4fe789a836169d4107523211bb158d4b7031ffd8ad1051`) is byte-identical to `git archive v0.0.1 prismatique` except `version.py`, which is generated at build time (`diff -r -q`). REPRODUCED |
| 0.0.1 vs 0.0.4 docstrings | `git diff v0.0.1 v0.0.4 -- prismatique/` for the classes above: `hrtem/image.py` one typo ("as mixed state" to "as a mixed state"); `thermal.py` units formatting of 10^-13 s and 10^-16 s; no docstring change in `hrtem/output.py`, `tilt.py`, `discretization.py`, `aperture.py`, `hrtem/system.py`, `sample.py`. The rendered 0.0.4 text therefore applies verbatim to 0.0.1 for every item in B.2. REPRODUCED |
| README | `https://github.com/mrfitzpa/prismatique` cloned in full (HEAD `fb217b3`); `README.md` SHA-256 `952a01ea1fa9b54c6c6b1cd6a1b854e1292bac3867733047419a3f78e050147a`; `CITATION.cff` SHA-256 `88b8a012ec33518214194f8c068269721418fa4bcf1e459810d490ab977284cb`. The v0.0.1 README (read with `git show v0.0.1:README.md`) has no install section and defers to the website; `docs/INSTALL.rst` at v0.0.1 carries the install text |
| Not read | the Examples pages, `prismatique.stem.*`, `prismatique.load`, `prismatique.cbed`, the worker pages |

### B.2 Extraction table (rendered 0.0 / latest = v0.0.4 text; identical in v0.0.1 per B.1)

Locators are the section numbers and equation numbers printed on the rendered pages.

| # | Fact | Locator | Label | Note |
|---|---|---|---|---|
| B1 | Signature `hrtem.image.Params(postprocessing_seq=(), avg_num_electrons_per_postprocessed_image=1, apply_shot_noise=False, save_wavefunctions=False, save_final_intensity=False, ...)` | 2.4.1.2 `prismatique.hrtem.image.Params`, signature line | SECTION_READ | Both save flags default to False: with defaults nothing is saved |
| B2 | Image pixel size: Eq. (2.4.1.2.1) Delta x~ = 2 Delta x, Delta y~ = 2 Delta y; Eq. (2.4.1.2.2) n_x = N_x/2, n_y = N_y/2; "The factors of 2 in Eqs. (2.4.1.2.1) and (2.4.1.2.2) are the result of an anti-aliasing operation performed in prismatic." | 2.4.1.2, Eqs. (2.4.1.2.1)-(2.4.1.2.2) | SECTION_READ | |
| B3 | Display convention: when converted to a hyperspy signal, x is horizontal increasing left to right and y "increasing from bottom to top", in angstrom | 2.4.1.2, parameter `postprocessing_seq` | SECTION_READ | Consistent with row 0 = largest y (descending r_y), but the docs do not state the HDF5 row order of `r_y` |
| B4 | Wavefunction file: one file per frozen-phonon subset, basename `"hrtem_sim_wavefunction_output_of_subset_"+str(i)+".h5"`; groups `metadata` (`tilts` 2-D, dims "tilt idx", "vector component idx [0->x, 1->y]", units "mrad"; `defocii` 1-D, "Å"; `r_x`, `r_y` 1-D, "Å") and `data/image_wavefunctions`, "<HDF5 5D dataset>", dims "atomic config idx", "defocus idx", "tilt idx", "r_y idx", "r_x idx", units "dimensionless" | 2.4.2.2 `prismatique.hrtem.output.Params`, file-structure listing | SECTION_READ | dtype (complex64) is not stated in the docs |
| B5 | "Note that, unlike the intensity data, the complex-valued wavefunction data is not postprocessed." | 2.4.2.2 | SECTION_READ | |
| B6 | Intensity file `hrtem_sim_intensity_output.h5`: `metadata/r_x`, `metadata/r_y`, `data/intensity_image` 2-D (dims "r_y idx", "r_x idx") | 2.4.2.2 | SECTION_READ | No tilt or configuration axis |
| B7 | `hrtem.output.Params(output_dirname='sim_output_files', max_data_size=2000000000, image_params=None, save_potential_slices=False, ...)` | 2.4.2.2 signature | SECTION_READ | Internal inconsistencies in this page: the potential-slice basename is given both as `"potential_slices_"+str(i)+".h5"` and `"potential_slices_of_subset_"+str(i)+".h5"`, and a file `"hrtem_simulation_output.h5"` is mentioned that the listing does not define |
| B8 | `sample.ModelParams(atomic_coords_filename, unit_cell_tiling=(1, 1, 1), discretization_params=None, atomic_potential_extent=3, thermal_params=None, skip_validation_and_conversion=False)` | 2.6.18 `prismatique.sample.ModelParams`, signature | SECTION_READ | No `absorbing_layers` or any absorber parameter. The string "absorb" occurs nowhere in the 0.0 `searchindex.js` (grep count 0). REPRODUCED for the grep |
| B9 | Coordinate file: sixth column is (1/sqrt(3)) u_i,rms; third column is z' with z = -z' + Delta Z; "occ" is ignored in prismatique | 2.6.18, parameter `atomic_coords_filename` | SECTION_READ | |
| B10 | "periodic boundary conditions are imposed on the supercell in the x- and y-directions" | 2.3.1 `prismatique.discretization.Params`, first paragraph | SECTION_READ | |
| B11 | Slicing: Eqs. (2.3.1.4)-(2.3.1.7), delta z = Delta Z / N_slices; "z = z_0 and z = z_{N_slices} are the z-coordinates of the entrance and exit surfaces of the sample's supercell respectively" | 2.3.1, text after Eq. (2.3.1.7) | SECTION_READ | Together with B9: the beam enters at file z' = Delta Z |
| B12 | Grid: Eq. (2.3.1.10) Delta x = Delta X / N_x; Eq. (2.3.1.11) (N~_x, N~_y) = (N_x/(4 f_x), N_y/(4 f_y)); users set N~ directly | 2.3.1 | SECTION_READ | |
| B13 | `discretization.Params(z_supersampling=16, sample_supercell_reduced_xy_dims_in_pixels=(64, 64), interpolation_factors=(1, 1), num_slices=25, ...)`; `z_supersampling = 0` selects the projected (Eq. 2.3.1.8) route, a positive value the numerical integration of Eq. (2.3.1.7) | 2.3.1 signature and parameter text | SECTION_READ | Isolated-atom approximation; potentials from Hartree-Fock scattering factors [Kirkland1], [DaCosta1] |
| B14 | Tilt: Eq. (2.10.3.1) theta_x = lambda k_x, theta_y = lambda k_y; Eq. (2.10.3.2) Delta k = 1/Delta X; Eq. (2.10.3.3) Theta_{f_x,f_y} = {(l_x f_x lambda Delta k_x, l_y f_y lambda Delta k_y)}; "users can select all the angles from either a rectangular or radial window/region of the discretized angular-space" | 2.10.3 `prismatique.tilt.Params` | SECTION_READ | |
| B15 | `tilt.Params(offset=(0, 0), window=(0, 0), spread=0, ...)`; offset and window in mrad; a length-2 window is radial (min, max) about the offset, a length-4 window rectangular in absolute x and y tilt about the offset; `spread` is sigma_beta of Eq. (2.9.1.5), nonnegative | 2.10.3 signature and parameters | SECTION_READ | The docs do not mention the anti-aliasing tilt ceiling, nor that `spread = 0` turns the weight into an exact equality test |
| B16 | `thermal.Params(enable_thermal_effects=False, num_frozen_phonon_configs_per_subset=1, num_subsets=1, rng_seed=None, ...)`; with thermal effects off "u_i,rms is set to zero" | 2.9.1 `prismatique.thermal.Params` | SECTION_READ | |
| B17 | Mixed-state model Eq. (2.9.1.3): rho_t is an incoherent integral over defocal offset (Gaussian, Eq. 2.9.1.4), atomic configuration (Einstein model, Eqs. 2.9.1.9-2.9.1.11) and beam-tilt deviation (Gaussian, Eq. 2.9.1.5) of pure states; HRTEM intensity is <x,y|rho_t|x,y> (Eq. 2.9.1.2) | 2.9.1 | SECTION_READ | Intensity is averaged after squaring; matches report D section 4 |
| B18 | |psi_t> is "the state vector of a transmitted beam electron for a perfectly coherent beam operating at a defocus of Delta f + delta_f" | 2.9.1, text after Eq. (2.9.1.6) | SECTION_READ | The reference plane of the defocus, and the plane at which the saved wave is referred, are not stated anywhere in the pages read |
| B19 | `aperture.Params(offset=(0, 0), window=(0, inf), ...)`; annular objective aperture, angles in mrad | 2.1.1 `prismatique.aperture.Params` | SECTION_READ | Default = no aperture |
| B20 | `hrtem.system.ModelParams(sample_specification, gun_model_params=None, lens_model_params=None, tilt_params=None, objective_aperture_params=None, defocal_offset_supersampling=9, ...)` | 2.4.4.1 | SECTION_READ | Gauss-Hermite quadrature with N_f = 9 points by default for the defocal offset |
| B21 | Literature page lists [Pryor1] Adv. Struct. Chem. Imag. 3:15 (2017), [DaCosta1] Micron 151, 103141 (2021), [Loane1] Acta Cryst. A 47, 267 (1991), [Ophus1] 3:13 (2017), [Kirkland1] "Springer (2010)" with DOI 10.1007/978-3-030-33260-0, [Cowley1], [Hinitt1] | 4 "Literature" | SECTION_READ | Internal inconsistency: Crossref gives 2020 for that DOI (section H), not 2010 |
| B22 | Licence GPL version 3 | 5 "License"; README badge; `CITATION.cff` `license: GPL-3.0` | SECTION_READ | |
| B23 | Install route for the engine: `conda install -c conda-forge pyprismatic=2.\*=gpu\* ...` or `pyprismatic=2.\*=cpu\*`, then `pip install prismatique` | README (HEAD) "Installing prismatique using pip and conda together"; identical instruction in `docs/INSTALL.rst` at tag v0.0.1, lines 60 and 67 | SECTION_READ | The documented engine is conda-forge `pyprismatic` 2.x, not PyPI `pyprismatic` |
| B24 | conda-forge `pyprismatic` exists in versions 1.2.1 and 2.0; the 2.0 files were uploaded 2021-10-12 to 2023-10-07; licence GPL-3.0-only | `https://api.anaconda.org/package/conda-forge/pyprismatic` (JSON, SHA-256 `0c2aa78067027b7a11863da50b3a2cbacb8819142881fbc7617f56728b6d3878`) | METADATA_VERIFIED | Which Prismatic commit the conda-forge 2.0 builds were made from is UNVERIFIED (feedstock recipe not reachable; the in-repo `recipe/meta.yaml` versions from `GIT_DESCRIBE_TAG`) |
| B25 | `CITATION.cff` (version 0.0.4, 2026-01-18): author Matthew R. C. Fitzpatrick, University of Victoria, ORCID 0000-0001-5347-0629; concept DOI 10.5281/zenodo.18296081 ("collection of archived snapshots of all versions"); references Rangel DaCosta et al. 2021 as the publication whose algorithms prismatique wraps, and the Prismatic software (Ophus, Rangel DaCosta) | `CITATION.cff` at HEAD | SECTION_READ | Resolves the author caution in `references.bib` S01 (full name and affiliation now read from the project's own citation file) |

### B.3 Version-matching findings from the v0.0.1 tag (code, not docs)

| # | Finding | Locator | Label |
|---|---|---|---|
| B-V1 | In v0.0.1, `tilt._calc_smallest_possible_angular_space_pixel_size` computes `electron_beam_wavelength / sample_supercell_dims[:2] * 1000` with `sample_supercell_dims` a Python tuple (`sample._supercell_dims`, v0.0.1 `sample.py:2229-2259`). v0.0.2 wraps it in `np.array(...)`; the fix is commit `64528f9` (2025-10-27), message "Updated documentation. Also fixed a bug in the 'tilt' module." | `git diff v0.0.1 v0.0.4 -- prismatique/tilt.py` (v0.0.1 `tilt.py:548`) | SECTION_READ |
| B-V2 | `embeam._wavelength` returns a numpy scalar in embeam 0.0.1 to 0.0.3 and a Python float (`.item()`) from embeam 0.0.4 onward (wheels downloaded from PyPI; embeam 0.0.1 SHA-256 `27a23ce93b267c953bba8b7c5d4ba54939e9169fb60fab06b68dc85dc75637ff`, 0.0.5 `8e828430c48cebfd7f59c32b93194932d02d2abef5b83a2abc5651687e1976e7`) | `embeam/__init__.py:137-149` in each wheel | SECTION_READ |
| B-V3 | In a clean scratch venv with `pip install prismatique==0.0.1 embeam==0.0.5` (Python 3.11, numpy 2.4.6, hyperspy 2.4.0) and the repository's `pyprismatic_stub.py`: `prismatique.tilt.step_size(...)` raises `TypeError: unsupported operand type(s) for /: 'float' and 'tuple'` at `prismatique/tilt.py` line 548, while `prismatique.tilt.series(...)` with offset (5.5, 0) and window (0, 5.6) still returns 1309 tilts with first element (0.0, -0.9426...), identical to report D command 15. The numpy-scalar path reproduces D's step (0.2396, 0.3142) mrad | scratch script `stubdir/tilt_embeam_check.py`, `tilt_embeam_check2.py` | REPRODUCED |
| B-V4 | Consequence: `prismatique==0.0.1` does not pin `embeam` (D section 1.2), so today's resolver installs embeam 0.0.5 and the public `tilt.step_size` fails; the repository's own `tools/provenance_checks/tilt_test.py:60` calls it and therefore only runs with embeam 0.0.1 to 0.0.3. The simulation path (`tilt.series`, `hrtem.sim`) does not call `step_size` in v0.0.1 (grep) | grep of the installed v0.0.1 package | DERIVED_HERE from B-V1 to B-V3 |
| B-V5 | In v0.0.1 the public `prismatique.hrtem.output.data_size(...)` ends with `return None` (fixed to `return output_data_size` in the same commit); the internal size check `hrtem/sim.py:488-512` calls the private `_data_size` and is unaffected | `git diff v0.0.1 v0.0.4 -- prismatique/hrtem/output.py`; `git show v0.0.1:prismatique/hrtem/sim.py` lines 488-512 | SECTION_READ |

---

## C. S02 — Prismatic project pages and repository README

### C.1 What was read

| Item | URL (as fetched) | SHA-256 | Notes |
|---|---|---|---|
| Home | `https://prism-em.com/`; `https://prism-em.github.io/` redirects to it (identical bytes) | `7bf1962d1fa6d3e0c7261444d93b776e9aad177e80c89518541753b588ef9521` | read in full |
| Citing Prismatic | `https://prism-em.github.io/about-cite/` redirects to `https://prism-em.com/about-cite/` | `840ef19f973f50926c20387ab6528547abfc118a5d2d7ef589723f9000fa4bf2` | read in full |
| Input Parameters | `https://prism-em.com/docs-params/` | `282242362f7278a867cb1da4dd50b81ca438d444c0ef4f4d77374b2bc4be2e55` | read in full |
| Output File Format | `https://prism-em.com/docs-outputs/` | `a9af4fa29f9e044e8e35fc01df7811983b65b9d0e8f1290c4e0ec3b6a245fdcf` | read in full |
| Input File Formats | `https://prism-em.com/docs-inputs/` | `fc9b3689733d6f6413b9c432427a0b97c455f17bb523007545ed8e1f70298a9d` | read in full |
| Change log | `https://prism-em.com/docs-change-log/` | `ea1f3cea3801969d921bd3357d7125955886f8948ea7f48dfc36786d96a3546e` | read in full |
| Compiling | `https://prism-em.com/docs-compiling/` | `48eb85d6016904badce8afed138e408ab6485b58ed792ee396804bddb507923b` | read for precision and CUDA statements only |
| Conda-forge | `https://prism-em.com/downloads-conda-forge/` | `9c09110d7b76a297bb2b158611ac9a8cd8e4c43e870c8355a17ddb8f718baa6b` | read in full |
| Other codes | `https://prism-em.com/resources-sim-codes/` | `e3cfc451aa253b764aba1521d9e323743b8d8e9b1c40f498794caadafb45c485` | abTEM entry read |
| Python tutorial | `https://prism-em.com/tutorial-python/` | `7d21a60e5a2558190c3dfd05f8b5cb476eecf68a6d4e4231c9875c9a18189a31` | grep only: no HRTEM or tilt content |
| README | `https://raw.githubusercontent.com/prism-em/prismatic/master/README.md` | `1066ee7a490f24c404b38706568b8f1da2b59af76fd8c4c4dedcff5e769a2670` | read in full |
| Repository | `git clone https://github.com/prism-em/prismatic.git`, HEAD `d155fb931abaa22d5d2442d2e1a28a6657ac74da` (2026-01-30, "update README with maintenance notice", author Luis RD); tag v2.0 = `2470f58f613cb72959b0c7ab2ae06b8e6a1c5316` (2021-10-11) | `LICENSE` `589ed823e9a84c56feb95ac58e7cf384626b9cbf4fda2a907bc36e103de1bad2`; `src/aberration.cpp` `0242ec34ddec5aa79fcf702c85792eb76af194ffbc909a190ef76630d7cd2fb9` | `git log v2.0..master`: 2 commits (a Dockerfile, 2021-10-13, and the README notice); no change under `src/` or `include/`. `setup.py` says `version="1.2.0"` at both v2.0 and HEAD |
| 404 | `https://prism-em.com/about/` and `/tutorials/` return HTTP 404 (the parameter page still links to `prism-em.com/about`) | | |

### C.2 Extraction table

| # | Fact | Locator | Label | Note |
|---|---|---|---|---|
| C1 | Maintenance notice, website, verbatim: "Notice as of January 2026: Prismatic is no longer actively maintained. We appreciate any future interest or use, but will be less able to troubleshoot issues or push updates to the software in the future." The next sentence points to the site's page of other (S)TEM codes | prism-em.com home, first paragraph under the title | SECTION_READ | The website notice does not name abTEM |
| C2 | Maintenance notice, README: same two sentences in bold-prefixed form ("**Notice as of January 2026**: ..."), then a pointer to `https://prism-em.com/resources-sim-codes/` and "For a recently updated and actively maintained TEM simulation package, we especially recommend [abTEM](https://abtem.github.io/doc/intro.html) (link to [their Github](https://github.com/abTEM/abTEM))." Added by commit `d155fb9` dated 2026-01-30 | `README.md` line 5 at HEAD; `git show --stat d155fb93` | SECTION_READ | Only the README names abTEM |
| C3 | Citation request, verbatim opening: "If you use Prismatic in your research, we kindly ask that you cite the following papers:" followed by THREE items: C. Ophus, Adv. Struct. Chem. Imaging 3(1), 13 (2017); A. Pryor Jr, C. Ophus and J. Miao, "A streaming multi-GPU implementation of image simulation algorithms for scanning transmission electron microscopy", Adv. Struct. Chem. Imaging 3 (2017); L. Rangel DaCosta et al., "Prismatic 2.0 - Simulation software for scanning and high resolution transmission electron microscopy (STEM and HRTEM)", Micron 151, 103141 (2021) | `prism-em.com/about-cite/` | SECTION_READ | The source-file header (report D section 1.5) lists only the first two and gives Pryor as arXiv:1706.08563 |
| C4 | Licence: GNU GPL version 3 (`LICENSE` first line "GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007"); conda-forge licence field GPL-3.0-only | `prismatic-git/LICENSE`; anaconda API | SECTION_READ; METADATA_VERIFIED | Report D wrote "GPL" without the version |
| C5 | Home page: Prismatic implements "both the plane-wave reciprocal-space interpolated scattering matrix (PRISM) and multislice algorithms" for STEM and HRTEM; multislice described as a split-step alternation of transmission and propagation operators; "please keep in mind that Prismatic is beta software" and the authors "strongly recommend that all users carefully test the convergence and accuracy of their simulations" | prism-em.com home | SECTION_READ | |
| C6 | HRTEM in the change log: version 2.0 introduced "Simulation capabilities for HRTEM imaging modes", 3D potential with subpixel shifting, S-matrix refocusing for PRISM, simulation series, "Support for including arbitrary sets of aberrations in the imaging wavefunction", a soft-probe aperture "for improved aliasing behavior for PRISM simulations", and potential coefficients updated to "3rd ed. of Kirland's [sic] Advanced Computing in Electron Microscopy" | docs-change-log, "Changes introduced in Prismatic version 2.0" | SECTION_READ | |
| C7 | HRTEM tilt parameters (CLI): `--xtilt-tem (-xtt) min max step` and `--ytilt-tem (-ytt) min max step`, "plane wave tilt selection for HRTEM" in mrad (default 0 0 1); `--rtilt-tem (-rtt) min max` radial selection (default 0 0); `--tilt-offset-tem (-tot) xOffset yOffset` (default 0 0); pyprismatic fields `minXtilt`, `maxXtilt`, `minYtilt`, `maxYtilt`, `minRtilt`, `maxRtilt`, `xTiltOffset`, `yTiltOffset`, all "to include in HRTEM plane wave selection (in mrad)" | docs-params, CLI list and "List of PyPrismatic Metadata parameters" | SECTION_READ | Tilt is a SELECTION of plane waves, consistent with report D section 2c. No tilt ceiling is documented |
| C8 | Complex output: `--save-complex (-com)`: "Save the complex valued output probes (STEM) or plane waves (HRTEM), instead of integrating intensity. Saves each frozen phonon individually." pyprismatic `saveComplexOutputWave` "Only affects the 4D output and HRTEM simulations." | docs-params | SECTION_READ | |
| C9 | Thermal default at the engine level: `--thermal-effects (-te)` "(default: True)", described as Debye-Waller factors; `includeThermalEffects` "to apply random thermal displacements (Debye-Waller effect)" | docs-params | SECTION_READ | Engine default is ON; prismatique's default is OFF (B16). Any direct engine run must set it explicitly |
| C10 | Aberration file format: "m, n, C_mag, C_ang, where m is the radial order of the aberration, n is the azimuthal order", magnitude "in rads"; the example file's comment line reads "defocus, spherical, 3-fold coma, 3-fold astig" and its four lines are `1 0 100 0`, `3 0 1000 0`, `3 1 5000 1.57`, `3 3 7500 0.75`, i.e. defocus is written with m = 1, spherical aberration with m = 3, and angles look like radians (1.57) | docs-inputs, "Aberration file input format" | SECTION_READ | CONTRADICTED by the engine: `src/aberration.cpp:124-125` multiplies by pow(lambda q, m), `:120` converts the angle from degrees, and `:183`, `:200`, `:217` create defocus, C3 and C5 as m = 2, 4, 6. The website example would apply (lambda q)^1 and (lambda q)^3 terms. See C-I2 |
| C11 | Output file format page documents STEM outputs only (2D, 3D, 4D, DPC, potential slices under `/4DSTEM_experiment/...`); it has no HRTEM section | docs-outputs | SECTION_READ | The HRTEM output group, its plane and its crop are undocumented on the website |
| C12 | Precision: default single precision (type float), double with `PRISMATIC_ENABLE_DOUBLE_PRECISION=1`; conda-forge ships `prismatic-double` for the CLI | docs-compiling "Enabling Double Precision"; downloads-conda-forge | SECTION_READ | Matches report D fact 34 (float32 default) |
| C13 | The website nowhere states the plane of the saved HRTEM wave, a back-propagation, a mid-plane reference, or the anti-aliasing fraction | all pages in C.1 (grep for exit, propagat, anti-alias, antialias, tilt ceiling) | SECTION_READ (absence) | |
| C14 | Input format: comment line, cell a b c, lines "Z, x, y, z, occ, thermal_sigma" with thermal_sigma "the standard deviation of random thermal motion in Angstroms (Debye-Waller effect)", "-1" terminator; example SI100.XYZ with 0.076 | docs-inputs | SECTION_READ | Per-axis sigma, consistent with report D fact 26 |

Inferences for S02 (not statements of the pages):

| # | Inference | Label |
|---|---|---|
| C-I1 | The engine report D read (HEAD `d155fb9`) is source-identical to tag v2.0 in `src/` and `include/`, so D's engine facts are version-matched to "Prismatic 2.0" as named in the Micron paper and on conda-forge (up to the unverified mapping of conda-forge builds to that tag) | DERIVED_HERE from C.1 |
| C-I2 | Any hand-written aberration file must follow the source (m = power of lambda q, angle in degrees), not the website example; this confirms D fact 45's warning and extends it to the published documentation | DERIVED_HERE from C10 |
| C-I3 | A citation of the HRTEM path used here must include Rangel DaCosta et al. 2021 (it is on the project's own citation page), in addition to Ophus 2017 and Pryor et al. 2017 | DERIVED_HERE from C3 |

---

## D. P49 — Kudo, Yamamoto and Hoshi, arXiv:2306.00271 (2023), journal version Comput. Phys. Commun. 296, 109029 (2024)

### D.1 What was read

| Item | Value |
|---|---|
| Identifier check | `https://export.arxiv.org/api/query?id_list=2306.00271` (SHA-256 `67a9212413bcdcd8b7da91abfaa92e196729a15e850b7c4aa09d23268abe528f`): id `2306.00271v1`, title "A fast and accurate computation method for reflective diffraction simulations", authors Shuhei Kudo, Yusaku Yamamoto, Takeo Hoshi, submitted 2023-06-01, primary category math.NA, no DOI or journal-ref field on the arXiv record, single version v1. METADATA_VERIFIED |
| Preprint PDF | `https://arxiv.org/pdf/2306.00271v1`, 10 pages, SHA-256 `e14fa4a791d886d4be6b25a4de6f71bed47da319fc9f486a306702ceb8970db3`; text extracted with pypdf for page and equation locators |
| LaTeX source | `https://arxiv.org/e-print/2306.00271v1` (served from `arxiv.org/src/...`), SHA-256 `684c691fcfce13a627a93f34663715f1f70f29546167db800b407acad0d41720`; `trhepd3.tex` (SHA-256 `5fd6199c8030f1213b148b9e4b3d6386d87a2c68d50b7b283dae4d3ab6c35dea`), `table.tex` (`ae8aef1dce3bc34ba0bed0df031508e082548f911b94a6ec26200b07aa6bd4ab`), `trhepd3.bbl` (`ea2b137743c887bc06480adb12849b2ff47d653051d7480abc7fbe7c8850ec92`) read in full |
| Coverage | Entire preprint: abstract, sections 1 to 6, Algorithm 1, Tables 1 to 3, Figure 1 and 2 captions, data statement, reference list entries used below. The figure images were not inspected (captions only) |
| Code | Data statement URL `github.com/shuheikudo/trhepd-opt`: exists (`git ls-remote` HEAD `dc394bac5fb9d7d55865b853da733c72edd0c1a3`, last commit 2023-08-02); cloned; `README.md` (SHA-256 `7ef9f786adf514351c4d25996743263b6adf645ddb6b725866dc0ade273ec87b`) and the output routine `sim-trhepd-rheed/src/surf.f90` (SHA-256 `4d887cd76f8a6b8b841b280de1c6ebec9f79e6be05c586a7fb1194a50152f956`) read; `sim-trhepd-rheed/LICENSE` is GPL version 3. The rest of the Fortran was only grepped |
| Journal version | Crossref `https://api.crossref.org/works/10.1016/j.cpc.2023.109029` (SHA-256 `a513fb8bbe3c4fa828102fc64c93dcd78534a717195eebacf43c5596319f263e`): "A fast and efficient computation method for reflective diffraction simulations", Computer Physics Communications 296, article 109029, issued 2024-03 (print), authors Shuhei Kudo, Yusaku Yamamoto, Takeo Hoshi, Elsevier alternative-id S0010465523003740, "© 2023 Elsevier B.V. All rights reserved." METADATA_VERIFIED. The journal full text is paywalled and was NOT read |

Title difference, now resolved: the preprint says "fast and ACCURATE", the journal article "fast and EFFICIENT". Whether the
journal text differs in content (equations, tables, validity statements) is UNVERIFIED; to settle it, request the CPC
accepted manuscript or PDF from Ali.

Page and equation map (preprint PDF): Eqs. (1)-(10) and Fig. 1 on p. 2; Eqs. (11)-(28), section 2.2, p. 3; section 3.1,
Eqs. (29)-(36), p. 4; section 3.2 to 3.3, Eqs. (37)-(42), Algorithm 1, p. 5; section 3.4, Eqs. (43)-(49), p. 6;
section 4, Table 2, section 5 begins, p. 7; Fig. 2, section 5 end, section 6, p. 8; Table 3 and data statement, p. 9.

### D.2 Extraction table

| # | Fact | Locator | Label | Note |
|---|---|---|---|---|
| D1 | Geometry: the surface is the x-y plane at z = 0, the bottom boundary is at z = z_e; atoms are two-dimensionally periodic parallel to x-y "but not periodic along the z-axis"; slices run z_0 = z_e < z_1 < ... < z_L = 0 | section 2.1 p. 2; section 2.2 text before Eq. (18), p. 3 | SECTION_READ | Surface-parallel slicing (Ichimiya type), crystal at z < 0 |
| D2 | Governing equation, Eq. (1): (Delta + gamma^2 + v(r)) psi(r) = 0, the stationary Schrödinger equation, gamma = vacuum wave number, v = potential of the atoms | Eq. (1), p. 2 | SECTION_READ | Full second-order equation in z: no paraxial or forward-scattering approximation. Units and scaling of v are not stated |
| D3 | Beam expansion: psi = e^{i b.r} phi with phi 2-D periodic (Eqs. 3-4); v and psi expanded in reciprocal rods k_j (Eqs. 5-6); truncated to n components giving Eq. (7) and, in matrix form, Eq. (8): d^2 c/dz^2 = -(U(z) + Gamma^2) c, with (Gamma)_jj = sqrt(gamma^2 - abs(b_0 + k_j)^2) | Eqs. (3)-(8), p. 2 | SECTION_READ | "The number of components n is n = 10^1 -- 10^2 in the present paper" (p. 2) |
| D4 | "The boundary condition of the problem is Robin (third type)." Incident and reflected fields defined as tau(z) = (-i d/dz + Gamma) c(z) (Eq. 9) and rho(z) = (i d/dz + Gamma) c(z) (Eq. 10); boundary conditions tau(0) = (1, 0, ..., 0)^T (Eq. 11, k_1 = 0) and rho(z_e) = 0 (Eq. 12); "The reflection wave at the top rho(0) is the term that we aim to compute" | Eqs. (9)-(12), pp. 2-3 | SECTION_READ | This is the boundary-value problem (BVP) the paper reformulates |
| D5 | Intensity, Eq. (13): (eta)_i = abs((rho(0))_i)^2 sin(theta_0) sqrt(gamma^2 - abs(b_0)^2) / sqrt(gamma^2 - abs(b_0 + k_i)^2) if gamma^2 > abs(b_0 + k_i)^2, else 0; theta_0 = altitude (glancing angle) of the incident wave; eta as a function of (theta_0, theta_1) is the rocking curve | Eq. (13) and following text, p. 3 | SECTION_READ | Evanescent beams are assigned zero intensity |
| D6 | Conventional method (Ichimiya): first-order system for (tau, rho), Eqs. (14)-(17); A(z) approximated as step-wise constant at slice mid-points, Eq. (18); per-slice transfer matrix e^{(z_{i+1}-z_i) A_i}, Eq. (19); the full product is ill-conditioned; the recursive reflection technique builds R_i = (Z_i + W_i R_{i-1})(X_i + Y_i R_{i-1})^{-1} from the bottom up, Eqs. (24)-(28), so that rho(0) = R_{L-1} tau(0) | section 2.2, Eqs. (14)-(28), p. 3 | SECTION_READ | The bulk layer is handled by stopping when R_i converges to a precomputed R_bulk (p. 4, "Treatment for the bulk layer") |
| D7 | The conventional discretisation "is known as the second-order Magnus method" and needs a matrix exponential (eigen-decomposition) per slice | section 2.2, "Strategy for a faster computational method", p. 4 | SECTION_READ | |
| D8 | Reformulation: y = (c, dc/dz), dy/dz = B(z) y with B = [[O_n, I_n], [-(U + Gamma^2), O_n]] (Eq. 29); (tau, rho) = S y with S = [[Gamma, -i I_n], [Gamma, i I_n]] (Eq. 30); the matrix initial-value problem dY/dz = B Y, Y(z_e) = I_2n (Eq. 32); economical form dZ/dz = B Z, Z(z_e) = S^{-1} [I_n; O_n] (Eq. 34) | section 3.1, Eqs. (29)-(34), p. 4 | SECTION_READ | This is the BVP-to-initial-value reformulation recorded at index level in report B |
| D9 | Reflection amplitude from the integrated solution, Eq. (36): rho(0) = (Gamma + i P_L Q_L^{-1})(Gamma - i P_L Q_L^{-1})^{-1} tau(0), with Z_L = [Q_L; P_L] the numerical Z(0) | Eq. (36), p. 4 | SECTION_READ | rho(0) is a COMPLEX vector; the method yields complex reflection amplitudes by construction |
| D10 | Right-hand-side transformation (RHST): after each step, if the Gershgorin estimate of cond(Q) exceeds a threshold (1000 in Algorithm 1), Z is right-multiplied by Q^{-1}; right multiplications do not change rho(0) (Eqs. 37-40); the recursive reflection technique is the special case with the second-order Magnus step (Eqs. 41-42) | section 3.2 to 3.3, Eqs. (37)-(42), Algorithm 1, p. 5 | SECTION_READ | Algorithm 1 returns rho(0) <- R_L(:, 1), "Reflection of the plane wave k_1 = 0" |
| D11 | ODE solvers: explicit s-stage Runge-Kutta (Eqs. 43-46) and "BAB" splitting methods (Eqs. 47-49), SRKN_6^b and SRKN_11^b of Blanes and Moan 2002 for 4th and 6th order; both linear and single-step, hence compatible with the RHST | section 3.4, pp. 5-6; section 4 method list, p. 6 to 7 | SECTION_READ | |
| D12 | Claimed step-size gain: "the slice size h can be chosen to be more than 10 fold larger than the original one to achieve the same accuracy" | section 1, p. 1 | SECTION_READ | |
| D13 | Test problem: TRHEPD simulator for Si(111)-7x7 (p3m1, 37 atoms per cell, surface domain 9.910955 Å without bulk layer), n = 23, 47 (69 angles, azimuth 60°) and n = 521 (one angle 1.3°, azimuth -30°); altitudes printed as "0.1°, 0.2°, ... 69.0°" | Table 2 and section 4 text, p. 7 | SECTION_READ | 69 angles in 0.1° steps would end at 6.9°, so "69.0°" is probably a typo (DERIVED_HERE). Beam energy of the test is not stated. No electron RHEED test and no 200 keV test |
| D14 | Errors are relative max-norm differences of intensities: eorig against the conventional default (dz = 0.01 Å) and eacc against a fine-step run of the new method; no comparison with an analytic solution ("the latter is difficult to compute for this simulation") | section 4, error definitions, p. 7 | SECTION_READ | Only intensities are compared; no phase or complex-amplitude accuracy is reported |
| D15 | Speed-ups at eacc below that of `orig` (Table 3): n = 23: rk4 513x, sp4 1004x, sp6 1202x; n = 47: rk4 703x, sp4 2041x, sp6 1848x; n = 521: rk4 144x, sp4 494x, sp6 664x; `opt` (conventional method with BLAS/LAPACK and OpenMP) 21.6x, 28.5x, 5.78x | Table 3, p. 9 (values from `table.tex`, rounded here to 3 figures as the table specifies) | SECTION_READ | "up to 2,000 times" is the n = 47 sp4 case. Hardware: Intel i7-12700, 8 P-cores fixed at 2.1 GHz, oneMKL 2022.1.0 (p. 7) |
| D16 | Absorption: "the potential v has an artificial imaginary component that represents the absorption effect" | section 5, "Need for structure preservation", p. 8 | SECTION_READ | The sign convention of the imaginary part is not stated |
| D17 | Scope statement: "At this stage, the proposed method is specific to RHEED/TRHEPD, but may possibly be applicable to other many-beam reflective diffraction simulations that have severe ill-conditionedness." | section 5, p. 8 | SECTION_READ | |
| D18 | Code: "All the source codes and obtained data are available at github.com/shuheikudo/trhepd-opt." | Data statement, p. 9 | SECTION_READ | Repository exists (D.1). Its README lists folders `str-org` ("original sim-trhepd-rheed"; the folder on disk is named `str-orig`, next to an undocumented `str-orig-plus`), `str-lapack`, `sim-trhepd-rheed` ("new one") and `test`; `orig` in the paper is sim-trhepd-rheed commit `df61124c` (p. 7) |
| D19 | Output of the released code: `surf.f90:117` computes `f2(i)=dble(f(i,nb0)*dconjg(f(i,nb0)))*wnsga2/s` and `:122` writes `angle,(f2(i),i=1,nb)`; a line writing `abs(f(i, nb0))` is commented out (`:123`) | `trhepd-opt/sim-trhepd-rheed/src/surf.f90:112-123` at `dc394ba` | SECTION_READ | Only intensities are written. The complex amplitude `f(i, nb0)` exists in memory but is not output |
| D19b | The copy of the ORIGINAL sim-trhepd-rheed vendored in the same repository (`str-orig/src/surf.f90`, SHA-256 `16c93b376d21ce71e604c9d7788f1b61249b1eca00a28e8f94f4dc5945ef9fbd`) has the same intensity-only output: `f2(i)=dble(f(i,nb0)*dconjg(f(i,nb0)))*wnsga2/s` at `:109` and the write at `:114` | `trhepd-opt/str-orig/src/surf.f90:109-114` | SECTION_READ | Answers, for the version benchmarked in P49 (commit `df61124c`), the open question in `docs/05` section 4.4: complex amplitudes are computed but not written. The current upstream sim-trhepd-rheed was not checked |
| D20 | The paper's own reference list gives sim-trhepd-rheed's paper as Hanada, Motoyama, Yoshimi, Hoshi, Comput. Phys. Commun. 277 (2022), doi 10.1016/j.cpc.2022.108371, and Ichimiya 1983 as Jpn. J. Appl. Phys. 22 (1R) 176-180 | `trhepd3.bbl` entries Hanada2022 and Ichimiya1983 | SECTION_READ | Both Crossref-verified in section H |

Inferences from P49 (not statements of the paper):

| # | Inference | Basis | Label |
|---|---|---|---|
| D-I1 | Validity regime: exact (non-paraxial) stationary scattering by a potential that is 2-D periodic parallel to the surface and arbitrary along the normal, truncated to n beams, with a no-upward-wave condition at the bottom (or a converged bulk reflection matrix). This is the flat, laterally periodic surface; a step or finite feature needs a supercell with many more rods (n grows with supercell area) | D1-D6 | DERIVED_HERE |
| D-I2 | Complex reflection amplitudes are available: rho(0) of Eq. (36) and `f(i, nb0)` in the code are complex; exposing the phase needs only an extra output line. But the paper validates intensities only (D14), so the accuracy of the phase is untested | D9, D14, D19 | DERIVED_HERE |
| D-I3 | Sign convention to check before any phase comparison: from Eq. (14) with U = 0, d tau/dz = i Gamma tau, so tau is proportional to exp(+i Gamma z), and rho to exp(-i Gamma z). With the crystal at z < 0 (D1) and tau labelled incident (Eq. 11), the incident wave travels towards -z only under an exp(+i omega t) time factor. Under the exp(-i omega t) time factor that goes with the project's exp(+i k.r) travelling-wave convention (SM03), the paper's complex amplitudes correspond to the complex conjugates of the project's (for real Gamma; with absorption the potential must be conjugated too). The same flip governs the sign of the absorptive imaginary potential (D16). `surf_prkn.f90` applies `conjg` in several places, consistent with a convention change inside the code, but this was not traced | D1, D4, Eq. (14), D16 | DERIVED_HERE (to be confirmed by a 1-beam step-barrier test, ladder rung 1) |
| D-I4 | The method is a solver for the same BVP that sim-trhepd-rheed solves (it replaces the per-slice exponential and generalises the recursive reflection technique); it is therefore a faster route to the same reference quantity, not an independent physical model | D6, D8, D10 | DERIVED_HERE |

---

## E. CONFIRMS / CONTRADICTS against report D, `docs/04` and the source map

"NOT ADDRESSED" means none of the documents read here states the point; the earlier label stands. Locators refer to
the extraction rows above (A = P04, B = S01, C = S02, D = P49).

| # | Claim (where it is made) | Verdict | Locator | Comment |
|---|---|---|---|---|
| E1 | Per-slice propagator is the paraxial Fresnel `exp(-i pi lambda dz q^2)` (D 2e fact 16; SM08; `docs/04`) | CONFIRMS (form and sign) | A3 (P04 Eq. 3, p. 3); A1 and A-I1 | P04 now supplies a SECTION_READ source for the form, which SM08 attributed to unread B06 |
| E2 | Paraxial error k L sin^4(alpha)/8, numbers at 24, 45, 64.3 mrad (SM08) | NOT ADDRESSED | P04 gives no error estimate | Numbers stay DERIVED_HERE |
| E3 | Transmission `t = exp(+i sigma V)` (D 2e) | CONFIRMS | A5 (P04 Eq. 4) | |
| E4 | Anti-aliasing at half Nyquist, output cropped to N/2 and image pixel = 2 x potential pixel (D 2b, 2c, 2e; SM10a, SM10b, SM15) | CONFIRMS | A8, A9 (P04 p. 3 and p. 6); B2 (S01 Eqs. 2.4.1.2.1-2) | P04: aperture "at half of the maximum scattering angle", output reduced "by a factor of 4"; S01: factors of 2 "are the result of an anti-aliasing operation performed in prismatic". The RECTANGULAR per-axis shape is NOT ADDRESSED by any document (source only) |
| E5 | Tilt ceiling `lambda/(4 dx)` (D 2c; SM15) | CONFIRMS (by derivation, A-I4) | A-I4 | No document states the ceiling explicitly (S01 B15, S02 C7 silent) |
| E6 | 2/3 anti-aliasing rule attributed to Kirkland B06 (SM15; `docs/05` 4.3 item 5) | NOT ADDRESSED | A8, A22 | Caution: P04 cites Kirkland 2010 (2nd ed.) [20] for the HALF-angle aperture. The attribution of the 2/3 rule to B06 must be checked when B06 is read |
| E7 | Tilt = one grid Fourier component, quantised to the FFT grid, entrance plane only (D 2c, fact 18; SM10b) | CONFIRMS | A10, A12, A13 (P04 Eq. 6, p. 3; Eq. 8 and the Chen et al. comparison, p. 4; p. 9); B14 (S01 Eq. 2.10.3.3); C7 | P04 states the design choice explicitly: tilt in "the initial conditions of each beam", not in the propagator as in Chen et al. 1995 |
| E8 | Interpolation factors in HRTEM only thin the tilt grid (D 2e) | CONFIRMS | B14 (Theta_{f_x,f_y} = grid with step f lambda Delta k); A10 | |
| E9 | HRTEM path is plain multislice per plane wave, not PRISM interpolation (D 2a, 2e; `docs/04`) | NOT ADDRESSED | A20; C5, C6 | P04 is STEM-only; the website names both algorithms for "STEM and HRTEM" without saying which HRTEM uses. Remains SECTION_READ of source |
| E10 | Saved wave is back-propagated by Delta Z/2 to the supercell mid-plane (D 2a, fact 12; SM10b; `docs/04`) | NOT ADDRESSED | A19, B18, C11, C13 | No public document read here mentions it: P04 predates HRTEM; S01 defines psi_t only as a transmitted state "operating at a defocus of Delta f + delta_f"; the website has no HRTEM output section. The claim remains SECTION_READ of source only, undocumented in S01 and S02; P05 (paywalled) was not read |
| E11 | SM10b wording "back-propagated by dz/2" | CONTRADICTS report D | D section 2a, `PRISM02_calcSMatrix.cpp:110` (`tiledCellDim[0]/2`) | Report D says half the CELL length (Delta Z/2, about 99 Å), not half a slice. The source map row is mis-worded (proposal F3) |
| E12 | 5-D dataset `(atomic config, defocus, tilt, r_y, r_x)` at `/data/image_wavefunctions`, tilts in mrad at `/metadata/tilts` (D 2b; SM10a) | CONFIRMS | B4 | |
| E13 | dtype complex64; `r_y` descending (D 2b; SM10a) | NOT ADDRESSED | B3, B4 | The docs' display convention (y increasing bottom to top) is consistent with descending rows but does not state the HDF5 order |
| E14 | Complex waves saved per configuration, never averaged; intensity averaged (D 2d, 4) | CONFIRMS | B5, B17; C8 ("Saves each frozen phonon individually") | |
| E15 | `save_wavefunctions` and `save_final_intensity` default False, so defaults save nothing (SM11c) | CONFIRMS | B1 | |
| E16 | Thermal effects off by default in prismatique; 1 config, 1 subset, seed None (D 2d, fact 25) | CONFIRMS | B16 | Nuance: the ENGINE's own CLI default is thermal effects ON (C9). Any direct Prismatic or pyprismatic run must set it explicitly |
| E17 | `.xyz` sixth column is the per-axis RMS `u_rms/sqrt(3)` (D 2d, fact 26) | CONFIRMS | B9; C14 | |
| E18 | z-flip `z = Delta Z - z_file`; beam enters at the largest file z (D 2g, fact 28) | CONFIRMS | B9, B11 | S01 also states z_0 and z_{N_slices} are the entrance and exit surfaces |
| E19 | Periodic x and y boundaries; no absorbing boundary; `absorbing_layers` is not a keyword (D 2f, 3.1, facts 31-32; SM11a) | CONFIRMS | B8, B10; A23 and P04 p. 4 ("periodically wrapped") | Absence confirmed in the rendered API and the search index |
| E20 | Tilt "window" selects every grid tilt inside it; 1309 tilts for the 74-point sweep (D 2c, 3.4, fact 21) | CONFIRMS and REPRODUCED again | B14, B15; B-V3 (1309 tilts, first (0, -0.9426) mrad with embeam 0.0.5 as well) | |
| E21 | `spread = 0` makes the tilt weight an exact float equality, hence NaN (D 3.4, fact 23) | NOT ADDRESSED | B15, B17 | Docs present spread only as the Gaussian sigma_beta |
| E22 | Float32 default precision (D fact 34) | CONFIRMS | C12 | |
| E23 | "PyPI pyprismatic 1.1.x has no HRTEM; the engine must be built from the 2.x tree" (D 1.4; `docs/04`) | CONTRADICTS the "must be built" wording (PyPI part not re-checked) | B23, B24 | prismatique documents, from v0.0.1 onward, installing the prebuilt conda-forge `pyprismatic=2.*`; conda-forge carries `pyprismatic` 2.0 (uploads 2021-10-12 to 2023-10-07). The provenance record then needs the conda build string; which commit those builds used is UNVERIFIED |
| E24 | Engine read by D (HEAD `d155fb9`) is the 2.x generation (D 1.4; `docs/04`) | CONFIRMS | C.1 row "Repository"; C-I1 | `src/` and `include/` are identical to tag v2.0 (`2470f58`, 2021-10-11); `setup.py` still says 1.2.0 |
| E25 | Citation request = Ophus 2017 + Pryor 2017 (source headers); DaCosta 2021 only METADATA_VERIFIED from a snippet (D 1.5, fact 4) | CONFIRMS (and upgrades DaCosta to SECTION_READ) | C3 | The live page asks for all three, and gives Pryor et al. as the journal article (Adv. Struct. Chem. Imaging 3, 2017), not the arXiv preprint |
| E26 | D's advice "Pryor 2017 if the GPU path is used" (D 1.5) | CONTRADICTS | C3 | The project page asks users of Prismatic to cite all three papers, without a GPU condition |
| E27 | Maintenance notice of January 2026 recommending abTEM (D 1.4, fact 41; `docs/04`; B report 6.5) | CONFIRMS | C1, C2 | The abTEM recommendation is in the README only; the website notice points to its list of other codes. README commit dated 2026-01-30 |
| E28 | Licences: Prismatic "GPL", prismatique GPLv3 (D 1.5; `docs/04`) | CONFIRMS | C4, B22 | Prismatic is GPL version 3 |
| E29 | `hrtem/sim.py` byte-identical 0.0.1 to 0.0.4; ctor signatures unchanged; the README's schema-drift pin rationale is unsupported (D 1.3, fact 3; `docs/04`) | CONFIRMS for the schema; a new pin-relevant failure found | B.1 docstring diff; B-V1 to B-V5 | The pin does matter, for a different reason: prismatique 0.0.1 with embeam 0.0.4 or later breaks `tilt.step_size` (REPRODUCED). This supports D's recommendation 5.1 to pin `embeam==0.0.1` too |
| E30 | Hand-written aberration files must use m = radial power (D fact 45) | CONFIRMS (source); the website example CONTRADICTS the engine | C10; `src/aberration.cpp:120-125, 183, 200, 217` | The published example would apply the wrong terms |
| E31 | P49 journal version "fast and efficient", CPC, PII S0010465523003740, "(reported November 2023)"; author list incomplete (B report 6.5; `references.bib` P49) | CONFIRMS title and PII; "November 2023" NOT ADDRESSED by Crossref | D.1 | Crossref: volume 296, article 109029, issued 2024-03, DOI 10.1016/j.cpc.2023.109029; three authors. "November 2023" is not in the Crossref record (UNVERIFIED) |
| E32 | P49 content at abstract level: BVP to initial-value matrix ODE, RK4 and splitting, generalised recursive reflection, up to about 2000x (B report 6.5) | CONFIRMS | D8, D10, D11, D15 | |
| E33 | `docs/05` 4.4: "Whether sim-trhepd-rheed exposes complex amplitudes is UNVERIFIED" | ANSWERED (was an open question) | D19, D19b | Both the original code (as vendored for P49's benchmark) and the P49 fork compute the complex amplitude and write only intensities. Current upstream unchecked |

---

## F. Proposed `docs/source_map.tsv` changes (proposals only; nothing was edited)

| # | Row | Proposed change |
|---|---|---|
| F1 | SM08 | `source_id`: add "P04 (Ophus 2017) Eq. (3), p. 3, for the propagator form; Eq. (1), p. 2, for the paraxial equation". `evidence_level`: "SECTION_READ (P04) for the form; numbers DERIVED_HERE; B06 METADATA_VERIFIED". `locator_inspected`: add "P04 Eqs. (1), (3), (5)". Keep the test status NOT RUN |
| F2 | SM10a | `source_id`: "S01 (prismatique 0.0.1 source; rendered docs 'latest' and '0.0', both built from v0.0.4, docstrings identical to v0.0.1)". `locator_inspected`: add "rendered 2.4.1.2 Eqs. (2.4.1.2.1)-(2.4.1.2.2); 2.4.2.2 file listing". Note in `validity_regime`: "complex64 and r_y order are source-only (not in the docs)" |
| F3 | SM10b | `claim`: replace "back-propagated by dz/2" with "back-propagated by Delta Z/2 (half the supercell length along the beam, `tiledCellDim[0]/2`)". `source_id`: add "P04 p. 3 (anti-aliasing aperture at half the maximum scattering angle) and Eq. (6) (grid plane waves); S01 Eq. (2.10.3.3)". `evidence_level`: "SECTION_READ (source) for the back-propagation, not documented in P04, S01 docs or the S02 website; SECTION_READ (P04, S01, source) for the band and the tilt grid" |
| F4 | SM15 | `source_id`: add "P04 p. 3 for the half-angle aperture (cited there to Kirkland 2010, 2nd ed.)". `adaptation_or_convention`: add "the 2/3 rule remains unsourced until B06 is read; P04 does not state it" |
| F5 | SM11a | `source_id`: add "S01 rendered 2.6.18 `sample.ModelParams` signature; 0.0 searchindex.js has no 'absorb'". Label unchanged (REPRODUCED) plus SECTION_READ of the docs |
| F6 | SM11c | `evidence_level`: add "SECTION_READ of the rendered 2.4.1.2 signature (both save flags default False)" |
| F7 | SM14 | `source_id`: add "P49 section 2.2 (secondary, SECTION_READ description of Ichimiya's surface-parallel multislice and recursive reflection technique, Eqs. 14-28)"; note P17's DOI 10.1143/JJAP.22.176 is now Crossref-verified (section H) |
| F8 | new SM18 | claim "prismatique 0.0.1 needs embeam 0.0.1 to 0.0.3: with embeam 0.0.4 or later `tilt.step_size` raises TypeError (`tilt.py:548`); fixed upstream in commit 64528f9 (v0.0.2)"; source S01 (git tags v0.0.1, v0.0.4; embeam wheels); evidence REPRODUCED (B-V3); implementation "pin `embeam==0.0.1` next to `prismatique==0.0.1`"; test `tools/provenance_checks/tilt_test.py` (fails with embeam 0.0.5) |
| F9 | new SM19 | claim "Flat-surface complex reflection amplitude rho(0) from the stationary BVP (Delta + gamma^2 + v) psi = 0 with Robin conditions tau(0) = e_1, rho(z_e) = 0; rho(0) = (Gamma + i P Q^-1)(Gamma - i P Q^-1)^-1 tau(0)"; source P49 Eqs. (1), (9)-(12), (36); evidence SECTION_READ; convention "P49's labels imply an exp(+i omega t) time factor: conjugate before comparing with SM03 (DERIVED_HERE, D-I3)"; validity "laterally periodic surface, n beams, intensities validated only"; test "ladder rung 1 (one beam, constant V0) reproduces the analytic step-barrier amplitude and fixes the sign"; status NOT RUN |
| F10 | new SM20 | claim "Prismatic citation requirement: Ophus 2017, Pryor et al. 2017 (journal article), Rangel DaCosta et al. 2021"; source S02 `prism-em.com/about-cite/`; SECTION_READ (C3); DOIs Crossref-verified (section H) |

Also proposed outside the source map: `docs/references.bib` P49 becomes an `@article` with the Crossref record
(section H) and keeps the arXiv id as `eprint`; P05 gets the full Crossref author list; S01 gets the author from
`CITATION.cff` (B25); S02 records GPL-3.0 and the three-paper citation request; `docs/04` licence row reads
"Prismatic GPL-3.0".

---

## G. Consequences for `docs/05` sections 4.3 and 4.4 (INFERENCE, not source statements)

Everything in this section is DERIVED_HERE from the rows cited; none of it is a claim made by the sources.

1. Engine plan (4.3), Prismatic as legacy benchmark. The public documents confirm the band limit (half the maximum
   angle), the grid-quantised entrance-plane tilt, the periodic x-y boundaries and the absence of an absorber
   (E4, E7, E19), so the reasons for not using Prismatic as the reference engine now rest on documents as well as
   source. The mid-plane back-propagation (E10) is documented NOWHERE that was read; that makes the "one tiny
   engine run" of report D section 7 item 3 a precondition for citing any Prismatic number as a benchmark. If that
   run uses conda-forge `pyprismatic` 2.0 (E23), record the conda build string. Set thermal effects explicitly,
   because the engine default (ON) and the wrapper default (OFF) differ (E16). Never write an aberration file from
   the website example (E30).
2. Engine plan (4.3), tilt implementation test. P04 A12 documents the two ways of carrying beam tilt: in the
   initial condition (PRISM, Prismatic) or in the propagator (Chen et al. 1995, section H). The planned M2
   comparison of entrance-plane Fourier-component tilt against propagator-shear tilt at 24 and 48 mrad therefore
   has a published precedent on each side. Neither source gives an accuracy statement at those angles, so the
   test is still needed.
3. Engine plan (4.3), paraxial error. No source read here quantifies the paraxial error, so item 9's numbers stay
   DERIVED_HERE (E2). P49 gives an exact, non-paraxial alternative for the flat surface (D2), which can serve as
   the exact reference.
4. Provenance (4.3 and section 6). Pin `embeam==0.0.1` with `prismatique==0.0.1` (E29, F8). The repository's own
   `tools/provenance_checks/tilt_test.py` fails with the embeam the resolver installs today. Citations for any
   Prismatic-based figure: all three papers (E25, E26).
5. Phase-validation ladder (4.4), rung 2. The P49 formulation is an exact stationary Bragg-case solver for a
   laterally periodic surface that yields the complex amplitude rho(0) (D9). With the released GPLv3 Fortran,
   which already computes `f(i, nb0)` (D19, D19b), exposing arg rho(0) is a small output change. That would give a
   many-beam reference for arg A(theta) across the rocking curve of the flat Si(001) surface, in addition to the
   two-beam closed form. Caveats: (a) the sign convention must be fixed first (D-I3): the ladder's rung 1
   (constant V0, one beam, analytic step barrier) is the n = 1, constant-U limit of Eqs. (8)-(12) and settles it;
   (b) P49 validated intensities only, for TRHEPD on Si(111)-7x7 at an unstated energy, so convergence in n and dz
   for 200 keV electrons at 20 to 50 mrad must be shown before use; (c) the absorptive potential's sign follows
   the same convention flip (D16).
6. Phase-validation ladder (4.4), scope. P49's method needs lateral periodicity (D-I1). It validates the
   flat-terrace reflection phase, not the step: step phases still come from the multislice engine and the
   geometric model, with rung 3's null tests.
7. Speed. The reported 100x to 2000x gains (D15) make many-angle rocking-curve references cheap on a CPU. That
   supports running the rung-2 reference over the whole tilt range rather than at a few angles.

---

## H. New or upgraded references (Crossref-verified DOIs only)

Each DOI below was resolved on `https://api.crossref.org/works/<DOI>` on 2026-09-22; raw JSON is in
`scratchpad/sources/crossref/` or `scratchpad/sources/P49/` with the SHA-256 given. All METADATA_VERIFIED.

| Key (proposed) | Record | DOI | JSON SHA-256 | Why |
|---|---|---|---|---|
| P49 (upgrade) | S. Kudo, Y. Yamamoto, T. Hoshi, "A fast and efficient computation method for reflective diffraction simulations", Comput. Phys. Commun. 296, 109029 (2024); preprint arXiv:2306.00271v1 "A fast and accurate ..." | 10.1016/j.cpc.2023.109029 | `a513fb8bbe3c4fa828102fc64c93dcd78534a717195eebacf43c5596319f263e` | Resolves the title discrepancy and the author list |
| PRYOR17 (new) | A. Pryor, C. Ophus, J. Miao, "A streaming multi-GPU implementation of image simulation algorithms for scanning transmission electron microscopy", Adv. Struct. Chem. Imaging 3, 15 (2017) | 10.1186/s40679-017-0048-z | `90a13ec15fe17a13dbdb2fafe2574cede24966299de3f132e3704d4800c649f9` | Required by the Prismatic citation page (C3) |
| P05 (upgrade) | L. Rangel DaCosta, H. G. Brown, P. M. Pelz, A. Rakowski, N. Barber, P. O'Donovan, P. McBean, L. Jones, J. Ciston, M. C. Scott, C. Ophus, "Prismatic 2.0 – Simulation software for scanning and high resolution transmission electron microscopy (STEM and HRTEM)", Micron 151, 103141 (2021-12) | 10.1016/j.micron.2021.103141 | `9aec2ec2ee3598ab76207a9b9e92835cb3123f5624cf71fd1ab13cc0fb126dd3` | Full author list; also required by C3 |
| P04 (confirm) | C. Ophus, Adv. Struct. Chem. Imaging 3, 13 (2017-05-10), CC BY 4.0 | 10.1186/s40679-017-0046-1 | `66c8ba7ffb84891fddc4b7901fb8866fa3aefdef0e2ad6f1cfedab078846a1ac` | Identity confirmed |
| P17 (upgrade) | A. Ichimiya, "Many-Beam Calculation of Reflection High Energy Electron Diffraction (RHEED) Intensities by the Multi-Slice Method", Jpn. J. Appl. Phys. 22 (1R), 176 (1983) | 10.1143/JJAP.22.176 | `39cdb5ed0180006fa58f63409ee5baeaa2bfb5845fcf56077ed941798f856ec5` | The DOI was withheld in B2 as unverified; Crossref now confirms it (first page 176; P49 cites 176-180) |
| SIMTRHEPD-CPC (confirm) | T. Hanada, Y. Motoyama, K. Yoshimi, T. Hoshi, "sim-trhepd-rheed – Open-source simulator of total-reflection high-energy positron diffraction (TRHEPD) and reflection high-energy electron diffraction (RHEED)", Comput. Phys. Commun. 277, 108371 (2022-08) | 10.1016/j.cpc.2022.108371 | `ca58b29fda6c9dba88cd4811ea2ea07abf515e3edb478a104f2c64ac2f171762` | Upgrades the README-only provenance to Crossref |
| CHEN95 (new) | J. H. Chen, D. Van Dyck, M. Op de Beeck, J. Broeckx, J. Van Landuyt, "Modification of the multislice method for calculating coherent STEM images", Phys. Status Solidi (a) 150(1), 13-22 (1995) | 10.1002/pssa.2211500103 | `edd8bb2b03b30ea3373295f136a6de10bce31cab6dd33212adfd6432746663bb` | P04 reference [38]; the tilt-in-propagator precedent (A12). Not read |
| LOANE91 (new, optional) | R. F. Loane, P. Xu, J. Silcox, "Thermal vibrations in convergent-beam electron diffraction", Acta Cryst. A 47, 267-278 (1991) | 10.1107/S0108767391000375 | `29c692e1f8f4dda02830c95bab4daef065aa13f5c6f5a6dd78f8788c15e2521c` | Source of prismatique's Einstein-model frozen phonons (B17). Not read |
| B06 (note) | E. J. Kirkland, Advanced Computing in Electron Microscopy, Springer; Crossref `issued` 2020 | 10.1007/978-3-030-33260-0 | `74acf38aa2c259955e2c4ebad2b507b1a9584f95ec3373541e93d797b6bd1627` | Confirms the B06 DOI and year; the Crossref record carries no edition number. prismatique's literature page pairs this DOI with "(2010)" (B21), which is wrong |

Software identifiers (not DOIs): prismatique Zenodo concept DOI 10.5281/zenodo.18296081 (read in `CITATION.cff`,
not resolved on Crossref or DataCite; UNVERIFIED as a resolvable DOI); `github.com/shuheikudo/trhepd-opt` at
`dc394bac5fb9d7d55865b853da733c72edd0c1a3` (GPL-3.0).

---

## I. What remains UNVERIFIED

1. The Delta Z/2 back-propagation of the saved HRTEM wave (SM10b): still source-only. No public document read here
   states it. Needs either the engine run of report D section 7 item 3 or reading P05.
2. P05 (Rangel DaCosta et al. 2021, Micron): not read (Elsevier, paywalled). Its HRTEM description (output plane,
   band limit, tilt, frozen phonons) is unread. Request from Ali: the P05 PDF or accepted manuscript (the reading
   plan also suggests OSTI or eScholarship).
3. The P49 journal version (CPC 296, 109029): content not read (paywalled). Whether equations, tables or claims
   changed from arXiv v1 is UNVERIFIED. Request from Ali: the CPC PDF or accepted manuscript.
4. The online publication date "November 2023" for the CPC article: not in the Crossref record.
5. The mapping of conda-forge `pyprismatic` 2.0 builds to a Prismatic commit or tag: the feedstock recipe was not
   reachable (raw URLs 404; GitHub API access for the conda-forge org not enabled in this session).
6. The sign convention of P49 (D-I3) is DERIVED_HERE from Eqs. (9)-(14) and the slice ordering of section 2.2 (the Fig. 1 image was not inspected). It was not checked
   against the Fortran (only `conjg` occurrences were seen) and has not been tested.
7. Whether the current upstream `sim-trhepd-rheed` (as opposed to the copy in `trhepd-opt/str-orig`) writes
   complex amplitudes.
8. The rectangular per-axis shape of Prismatic's anti-aliasing mask, complex64 dtype, descending `r_y`, the
   exact-equality tilt weights and the vacuum normalisation remain source-only (not in any document).
9. The 2/3 anti-aliasing rule's attribution to Kirkland (B06): nothing read here states it. P04 cites the
   2nd edition for the half-angle aperture instead.
10. P04's figures were not inspected as images (no renderer). Only captions and text were used.
11. The prismatique Zenodo DOI was not resolved.
12. Chen et al. 1995 and Loane et al. 1991: metadata only (not read).

