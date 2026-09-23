# L6 - Sourced silicon parameters for the reflection multislice: absorption, Debye-Waller factor, mean inner potential, benchmark rocking curves

Agent L6, 2026-09-23 (started 22:17 UTC). Branch `claude/electron-holography-orchestration-nakd7r`.
Written incrementally; the final state is the summary table, the recommendation and the upload list
at the end. Nothing committed or pushed. No repository file other than this report and
`docs/agent_reports/L6_new_refs.bib` was written.

Experiment (PROJECT_INPUT, Ali): Si(001), ion-milled, 200 keV (never 300 keV), reflection-mode
dark-field holography with the specular (0,0,8) beam at about 16 mrad glancing angle. Engine: our
multislice with the Kirkland independent-atom potential (abTEM 1.0.10), frozen phonons
(`FrozenPhonons`, independent Gaussian displacements, u = 0.076 A rms per axis, ASSUMPTION A7) and
`PhysicalAbsorption(model="proportional")`, V_imag(r) = ratio * V_real(r) with TEST_ONLY ratio 0.05 or
0.1 (`reflection_holo/forward/multislice/potentials.py`, class `PhysicalAbsorption`; PROJECT_INPUT
item 21 missing).

Label policy: METADATA_VERIFIED, SECTION_READ (only with a locator), REPRODUCED, PROJECT_INPUT,
ASSUMPTION, DERIVED_HERE, UNVERIFIED. Sub-labels as in L5: `+ABSTRACT(publisher)` (abstract read on
the publisher page), `+ABSTRACT(PubMed)` (abstract read in the Europe PMC record), `+ABSTRACT(index)`
(search-engine summary only; NOT evidence). A search-engine summary is never evidence; no value below
comes from one unless it is labelled UNVERIFIED. Raw downloads are kept outside the repository in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/l6/` (called
`l6/` below), with SHA-256 in section 0.

## 0. Log and files retrieved

- 22:17 UTC: read the task inputs: `docs/model_assumptions.md` (A7, B1, B6, B30, B32),
  `docs/06_project_inputs_required.md` (items 20, 21), `docs/references.bib` (header, MIP entries
  KRUSE06 to TANAKA24, unverified part), `docs/07_reading_plan.md`, `docs/source_map.tsv` (SM04,
  SM17), `docs/agent_reports/L5_open_access_check.md` (sections 0, 1, 4),
  `docs/agent_reports/H2_realistic_supercell_sizing.md` (sections 1, 2.5, 6, 10: N1, N2, N14), and the
  engine classes `PhysicalAbsorption` and `FrozenPhonons` (potentials.py).

- 22:20 UTC: Crossref identity checks (`api.crossref.org/works?query.bibliographic=...` and
  `/works/<doi>`, no mailto, User-Agent "L6-literature-check/1.0"; JSON cached in `l6/crossref/`).
  OpenAlex OA status and index abstracts (`api.openalex.org/works/doi:<doi>`, cached as
  `l6/oa_*.json`).
- 22:22 UTC: IUCr host (`journals.iucr.org`, all Acta Cryst. A papers below): Cloudflare managed
  challenge, HTTP 403 to curl and to WebFetch, for the landing page, the issue index page and the
  Crossref text-mining PDF link (`journals.iucr.org/a/issues/1996/03/00/zh0008/zh0008.pdf`). APS
  (`journals.aps.org`, abstract and PDF of PRB 60, 284): HTTP 403 to WebFetch. The Copenhagen
  research portal record of Flensburg and Stewart has no file. The Melbourne repository record of
  Allen et al. 2015 (hdl 11343/52385) says "This item is currently not available from this
  repository". Hosts unreadable here are recorded, not circumvented; no shadow library was used.
- 22:24 UTC: arXiv API (`export.arxiv.org/api/query`) answers HTTP 406; the arXiv HTML search
  (`arxiv.org/search/`) works and is used instead.
- 22:27 UTC: arXiv:2608.24679v1 (Hájek and Rusz, 25 Aug 2026) downloaded and read in full (11 PDF
  pages; text extracted with PyMuPDF 1.28.2 installed in a scratch venv).

### 0a. Documents read (URL, date 2026-09-23, SHA-256)

| file in l6/ | URL fetched | SHA-256 | what it is |
|---|---|---|---|
| hajek_2608.24679.pdf | https://arxiv.org/pdf/2608.24679 | 126a4c0167d05747a19e576b6727d7f59a84ed0a10eb491cdcbf1fb131582af6 | M. Hájek, J. Rusz, "Thermal diffuse scattering in TEM: complex absorptive potentials compared to the frozen phonon model", arXiv:2608.24679v1 [cond-mat.mtrl-sci], 25 Aug 2026, 11 pages |
| hajek_2608.24679_abs.html | https://arxiv.org/abs/2608.24679 | 321180a10432321e4956703974bfcb427cbcefca8dd1e6e31a59914aebcff2a6 | arXiv abstract page (v1 only) |

### 0b. Access and metadata records (Crossref JSON SHA-256 of the cached file)

| key | DOI (from Crossref) | Crossref record | OpenAlex OA status | host check |
|---|---|---|---|---|
| PENG96DW | 10.1107/s010876739600089x | Peng, Ren, Dudarev, Whelan, "Debye-Waller Factors and Absorptive Scattering Factors of Elemental Crystals", Acta Cryst. A 52(3) 456-470, 1996 (sha256 3620a5de...) | closed | IUCr 403 (Cloudflare) |
| PENG96ROBUST | 10.1107/s0108767395014371 | Peng, Ren, Dudarev, Whelan, "Robust Parameterization of Elastic and Absorptive Electron Atomic Scattering Factors", Acta Cryst. A 52(2) 257-276, 1996 (sha256 f322a13e...) | closed | IUCr 403 |
| BIRDKING90 | 10.1107/s0108767389011906 | Bird, King, "Absorptive form factors for high-energy electron diffraction", Acta Cryst. A 46, 202-208, 1990 | closed | IUCr 403 (same host) |
| WEICKENMEIER91 | 10.1107/s0108767391004804 | Weickenmeier, Kohl, "Computation of absorptive form factors for high-energy electron diffraction", Acta Cryst. A 47, 590-597, 1991 | closed | IUCr 403 (same host) |
| (not added) | 10.1107/s0108767397016899 | Weickenmeier, Kohl, "The Influence of Anisotropic Thermal Vibrations on Absorptive Form Factors for High-Energy Electron Diffraction", Acta Cryst. A 54, 283-289, 1998 | not checked | not needed for cubic Si |
| HALLHIRSCH65 | 10.1098/rspa.1965.0136 | Hall, Hirsch, "Effect of thermal diffuse scattering on propagation of high energy electrons through crystals", Proc. R. Soc. Lond. A 286, 158-177, 1965 | closed | royalsocietypublishing.org: Cloudflare challenge, HTTP 403 (checked 22:57 UTC) |
| RADI70 | 10.1107/s0567739470000050 | Radi, "Complex lattice potentials in electron diffraction calculated for a number of crystals", Acta Cryst. A 26, 41-56, 1970 | closed | IUCr 403 (same host) |
| SEARS91 | 10.1107/s0108767391002970 | Sears, Shelley, "Debye-Waller factor for elemental crystals", Acta Cryst. A 47, 441-446, 1991 | closed | IUCr 403 (same host) |
| FLENSBURG99 | 10.1103/physrevb.60.284 | Flensburg, Stewart, "Lattice dynamical Debye-Waller factor for silicon", Phys. Rev. B 60, 284-291, 1999 | closed (Copenhagen portal: metadata only) | APS 403 |
| DUDAREV95 | 10.1016/0039-6028(95)00464-5 | Dudarev, Peng, Whelan, "On the Doyle-Turner representation of the optical potential for RHEED calculations", Surf. Sci. 330, 86-100, 1995 | closed | not tried (Elsevier; L5 found ScienceDirect 403) |
| (lead) | 10.1016/0039-6028(92)90564-m | Dudarev, Peng, Whelan, "A treatment of RHEED from a rough surface of a crystal by an optical potential method", Surf. Sci. 279, 380-394, 1992 | closed | not tried |
| (lead) | 10.1016/0039-6028(96)00042-8 | Peng, Dudarev, Whelan, "Bethe potentials in dynamical RHEED calculations", Surf. Sci. 351, L245-L252, 1996 | closed | not tried |
| DUDAREV93 | 10.1103/physrevb.48.13408 | Dudarev, Peng, Whelan, "Correlations in space and time and dynamical diffraction of high-energy electrons by crystals", Phys. Rev. B 48, 13408-13429, 1993 | closed | not tried (APS 403 above) |
| ALLEN15 | 10.1016/j.ultramic.2014.10.011 | Allen, D'Alfonso, Findlay, "Modelling the inelastic scattering of fast electrons", Ultramicroscopy 151, 11-22, 2015 | closed (Melbourne record: file not available) | not tried |
| B08 chapter | 10.1093/oso/9780198500742.003.0014 | Peng, Dudarev, Whelan, "Temperature-Dependent Debye-Waller Factors", in High-Energy Electron Diffraction and Microscopy (OUP 2004), pp. 454-469 | n/a | OUP (L3: bot check) |

All of the above are METADATA_VERIFIED (Crossref, five fields: first author, title, container,
year, volume). The B08 chapter "Temperature-Dependent Debye-Waller Factors" (pp. 454-469) is new to
the project: `docs/07_reading_plan.md` lists B08 pp. 427-453 (ch. 13) but not this chapter.

## 1. Absorption for Si at 200 keV

### 1.1 What the candidate sources are (index abstracts only; bodies unread)

The OpenAlex records carry the publisher abstracts as an inverted index. They are reconstructed
verbatim here (`l6/oaabs.py`) and labelled `+ABSTRACT(OpenAlex)`: verbatim abstract text from an
index, stronger than a search-engine summary and weaker than an abstract read on the publisher's
page. **No number is taken from an abstract into the engine**; abstracts only say what each source
contains.

| source | what the abstract says it gives (verbatim fragment) | Si? energy? temperature? | label |
|---|---|---|---|
| Hall and Hirsch 1965 | "A simple theory is developed for calculating the contribution from thermal diffuse scattering to the absorption of high energy electrons passing through crystals. The Einstein model for a vibrating crystal is used ..." | theory; the abstract names no material | METADATA_VERIFIED +ABSTRACT(OpenAlex) |
| Radi 1970 | "Structure potentials, Vg, and absorption potentials for 100 keV-electrons are given in tabulated form for almost all monatomic crystals with elements Z = 3 to 90 ... at the temperatures 20, 93 and 293 °K." It also states that the ratio of the electronic-excitation absorption coefficient to Vg "lies between 0.005 and 0.012 for the lower reflexion vectors g and practically all Z", while the phonon part "is much larger and increases about linearly with Z" | Si presumably included (Z = 14 lies in 3-90; diamond-structure Si is a monatomic crystal), **100 keV, not 200 keV**; tables unread | METADATA_VERIFIED +ABSTRACT(OpenAlex) |
| Bird and King 1990 | TDS absorptive form factors "as a function of scattering vector s and temperature factor M", Einstein model, isotropic Debye-Waller factors, "a Fortran subroutine which calculates both the real and absorptive form factors for 54 atomic species" | computable for Si from a sourced B; the formula is unread | METADATA_VERIFIED +ABSTRACT(OpenAlex) |
| Weickenmeier and Kohl 1991 | "For an isotropic Einstein model all integrations could be performed analytically by using suitable functions to fit the elastic electron scattering amplitudes. The result is cast into a function subroutine ..." | computable for Si from a sourced B; the formula is unread | METADATA_VERIFIED +ABSTRACT(OpenAlex) |
| Peng, Ren, Dudarev, Whelan 1996a (robust parameterisation) | absorptive factors parameterised "for 17 important materials with the zinc blende structure over the temperature range 1 to 1000 K"; for other materials the program takes "the atomic number of the element, the Debye-Waller factor and the acceleration voltage" | whether elemental Si is among the 17 is not stated in the abstract | METADATA_VERIFIED +ABSTRACT(OpenAlex) |
| Peng, Ren, Dudarev, Whelan 1996b (elemental crystals) | "Debye-Waller factors and absorptive scattering factors are given of 44 elemental crystals over the temperature range from 1 to 1000 K ... The Debye-Waller factors are derived from the experimentally determined phonon density of states and the accuracy of these factors is typically 2 to 3%." | Si very likely one of the 44 (UNVERIFIED); the voltage at which the absorptive factors are given is not in the abstract | METADATA_VERIFIED +ABSTRACT(OpenAlex) |

Inference (not a fact about any source): every one of these computes the TDS absorptive potential
from an isotropic Debye-Waller factor B with the Einstein model, so the absorptive potential and the
frozen-phonon displacement are two views of the same B. A sourced B for Si (section 2) is the
common input.

### 1.2 Double counting of TDS absorption with explicit frozen phonons

Read: Hájek and Rusz, arXiv:2608.24679v1 (in full). Facts (SECTION_READ):

| fact | locator | quote (verbatim) |
|---|---|---|
| In the frozen-phonon model the potential has no imaginary part; absorption appears only after averaging | p. 2, sec. II.A, after Eq. (3) | "In frozen phonon models, the imaginary part in the projected potential is absent, but the multislice approach remains qualitatively the same. In the semi-classical FPM, each multislice calculation through a frozen snapshot is purely elastic, and absorption arises only after averaging." |
| Elastic channel = coherent (amplitude) average over snapshots; total = incoherent average; TDS = difference | p. 2, Eqs. (4)-(6) | "the elastic channel of the FPM is the coherent (amplitude-level) average over N snapshots" |
| The Einstein FPM and the complex absorptive potential (CAP) both need the Debye-Waller factor | p. 2, sec. II.B | "Note that, both the FPM in Einstein model and the CAP model require the knowledge of Debye-Waller factors [15]." ([15] = Peng et al. 1996a) |
| The CAP is implemented with the Weickenmeier-Kohl parameterisation in Dr. Probe, V_proj = V + iV' | p. 2, Eqs. (1)-(2) | none quoted beyond the equation |
| The Einstein FPM and the CAP agree better with each other than with the correlated (MD) FPM; for 50 nm diamond at 300 kV the CAP-MD difference at the central beam is about 1e-3 I0 | p. 5-6, sec. III.B; Fig. 4 | "The Einstein FPM and the CAP show considerably better mutual agreement than either of them does with the MD-FPM" |
| Agreement improves with the detector collection area (110 mrad aperture: about 10^-4.5 I0) | p. 6, sec. III.B; Fig. 5; p. 10, sec. IV | none quoted |
| Validity of the CAP: light elements, moderate thickness, large collection angles | p. 10, sec. IV | "light-element systems, moderate specimen thickness, and large detector collection angles" |

Conditions of that paper: transmission, parallel illumination, 300 kV, diamond (50 nm) and SrTiO3
(30 nm). No silicon, no reflection geometry, no 200 kV, no holography. The paper does not use the
words "double counting"; the statement it supports is that in the frozen-phonon model the TDS
absorption of the elastic (coherent) wave is produced by the configuration average itself.

Inferences for this project (DERIVED_HERE, not statements of the paper):
1. The engine averages intensities after hologram formation, per realisation
   (`FrozenPhonons.describe()`: "intensities are averaged AFTER squaring (after hologram
   formation)"). The sideband of the averaged hologram is then the coherent average of the object
   wave over the realisations, which is the elastic channel of Eq. (4). The TDS depletion of the
   elastic wave is therefore already present. Adding a TDS-derived imaginary potential
   (Hall-Hirsch, Bird-King, Weickenmeier-Kohl, Peng 1996) on top of explicit frozen phonons counts
   the same loss twice. This agrees with H2 section 6 and N2.
2. What frozen phonons do not supply is absorption by electronic excitations (plasmons,
   single-electron and core excitations). With explicit frozen phonons the only imaginary
   potential that may be added is the electronic part. The engine's single "proportional" ratio does
   not separate the two.
3. The engine's alternative is a static lattice with a Debye-Waller-smeared real potential plus a
   TDS imaginary potential (the CAP route). Hájek and Rusz find the two routes close for a light
   element in transmission. That has not been shown for grazing-incidence reflection, where the
   elastic wave travels thousands of Angstrom along the surface.

### 1.3 Open sources read for absorption (22:30-22:50 UTC)

Files (URL, SHA-256; all retrieved 2026-09-23):

| file in l6/ | URL | SHA-256 | what it is |
|---|---|---|---|
| PMC10913675.xml | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10913675/fullTextXML | b7807cae746139a6bec7e643dc3ae1c9c78f57df1f3021868c020e78fa300dd5 | Thomas, Cleverley, Beanland, "Parameterized absorptive electron scattering factors", Acta Cryst. A 80 (2024) 146-150, doi:10.1107/s2053273323010963 (Crossref), CC BY (licence in the XML) |
| PMC10913675_supp.zip | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10913675/supplementaryFiles | e71cc5593b83055ce5902a6b57167ad91bfdbc840277ff8a4ce02d76c8abf464 | equation images a-80-00146-efd1..3.jpg (Eqs. 1-3, read as images) and sup1.zip = `main_scattering_function.py` (sha256 bb1cf9f50bd732bca0ca45c7b7630fae185f66463d2d07263a78fc7e747786be) |
| PMC10913673.xml | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10913673/fullTextXML | 68f74ce701d7df12e2c30eedd9e2dff1351fa10ec7e4eb3eef1faf27b685e1c2 | B. Mendis, "Modelling dynamical 3D electron diffraction intensities. II. The role of inelastic scattering", Acta Cryst. A 80 (2024) 178-188, doi:10.1107/s2053273323010690 (Crossref), CC BY |
| PMC13060613.xml, PMC13060613_supp.zip | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13060613/fullTextXML and .../supplementaryFiles | 02bd5176285e84d362389d2dec92125dacfa45c2bbe296591fcc3251d60614c8; fb85059b10c73370e37875d6a7fe5817079d7267efa37173e6f05f5b7b9b3216 | Ni, Busch, Zuo, "PyExtal: a Python package for quantitative convergent-beam electron diffraction", J. Appl. Cryst. 59 (2026) 687-699, doi:10.1107/s1600576726001469 (Crossref); table-header images j-59-00687-efi63/82/64.jpg read (U111, U'111, U222) |
| drprobe_celslc.html | https://er-c.org/barthel/drprobe/celslc.html | dc858316edf713cd38d5a165069e5e142075239abd39adedb163dcc52818d0e7 | Dr. Probe `celslc` documentation page ("Last update: May 18, 2021") |
| drprobe-paper.pdf | https://er-c.org/barthel/drprobe/drprobe-paper.pdf | c966c03f46d330ff7644b18d1e268ea00a371b02a309c045d223b446ced99197 | J. Barthel, "Dr. Probe: A software for high-resolution STEM image simulation", author's preprint (30 pages) of Ultramicroscopy 193 (2018) 1-11, doi:10.1016/j.ultramic.2018.06.003 (Crossref) |
| mustem_manual.pdf | https://raw.githubusercontent.com/HamishGBrown/MuSTEM/master/Manual/muSTEM_manual.pdf (link from the repository readme, sha256 c803de8b...) | 4b8ec3c20fb7a317aa65b5042eae3fb228570303cd1e87817497f59edd5b3a50 | muSTEM v5.3 manual (Allen, Brown, D'Alfonso, Findlay, Forbes), 30 pages |

Not retrievable: Europe PMC's own PDF route (europepmc.org 403), github.com and api.github.com
(403), the Durham repository record of Mendis 2019 (durham-repository.worktribe.com 403 to curl and
WebFetch; old dro.dur.ac.uk link redirects there).

**(a) Thomas, Cleverley and Beanland 2024 (SECTION_READ in full, CC BY).**

| fact | locator | label |
|---|---|---|
| Complex structure factor with absorptive form factor: F_g = sum_j [f_g^(j) + i f_g^(j)'] exp(2 pi i g.r^(j)) exp(-B_iso^(j) s^2), s = sin(theta_B)/lambda = g/2 | sec. 1, Eq. (1) (image efd1) | SECTION_READ |
| The TDS absorptive factor, Bird and King's form: f'(s, B) = (2h/(beta m0 c)) integral d^2s' f(abs(s/2 + s')) f(abs(s/2 - s')) {1 - exp[-2B(s'^2 - s^2/4)]}, integrated over the Ewald sphere | sec. 2, Eq. (2) (image efd2) | SECTION_READ (Bird and King's own equation: UNVERIFIED, their paper is closed) |
| beta f' is voltage-independent and is parameterised as four Gaussians plus a constant, at 13 values of B_iso (0.1 to 4 A^2), for 103 elements; "In any implementation the accelerating voltage must be taken into account both by including beta and multiplying by the relativistic correction gamma" | sec. 2, Eq. (3); sec. 3 | SECTION_READ |
| Negative beta f' at large s (unphysical amplification) is set to zero | sec. 2 | SECTION_READ |
| Uses the Lobato and Van Dyck (2014) Born scattering factors for f | sec. 2 | SECTION_READ |
| Statement about Peng et al. 1996a,b: "some tabulated values were given for a limited set of elements and compounds for 100 kV electrons" | sec. 2, first paragraph | SECTION_READ of the statement; UNVERIFIED for Peng 1996 itself |
| Statement about the older practice: "most working calculations at the time instead used a proportional model in which f_g' = alpha f_g, typically with alpha ~ 0.1 (Humphreys & Hirsch, 1968)" | sec. 1 | SECTION_READ of the statement; UNVERIFIED for Humphreys and Hirsch 1968 |
| TDS versus higher-loss inelastic scattering: the latter "is strong only at very small scattering angles"; the parameterisation "neglects diffuse scattering due to higher-energy (plasmon and core-loss) inelastic scattering" | sec. 1; sec. 4 | SECTION_READ |
| Code: `main_scattering_function.py`, default `V = 200000`, `main(s, B, Z)` returns gamma (f + i f'); f' from the parameterisation (`useInterpolation = True`) or from direct quadrature of Eq. (2) (`fprime`) | supplementary sup1.zip | SECTION_READ (code) |

**(b) Mendis 2024 (SECTION_READ in full, CC BY). Si, 200 kV.**

| fact | locator | quote or value | label |
|---|---|---|---|
| Specimen and conditions | sec. 3 | "An ion-beam polished Si [110] single-crystal sample was examined at 200 kV in a JEOL 2100F" | SECTION_READ |
| Total inelastic mean free path used | sec. 3 | "~1990 Å for an inelastic mean free path value of ~830 Å, calculated using the method of Malis et al. (1988)" | SECTION_READ (a calculated value, not measured here) |
| Si plasmon mean free path at 200 kV (measured, cited) | sec. 3 | "the plasmon mean free path for silicon, which has been experimentally measured using EELS to be 1050 Å (Mendis, 2019)" | SECTION_READ of the statement; the measurement (Mendis 2019) is UNVERIFIED (Durham repository 403, Elsevier closed) |
| Si phonon (TDS) mean free path at 200 kV, calculated | sec. 3; sec. 5 | 7724 Å | SECTION_READ (calculated with their Eq. (9)) |
| Plasmon angles for Si at 200 kV | sec. 3 | theta_E = 0.04 mrad (17 eV loss); theta_c = 19.1 mrad "obtained by fitting simulation to experiment (Barthel et al., 2019)" and rescaled from 300 kV | SECTION_READ |
| Si thermal vibration (statement about Kirkland 2010) | sec. 3 | "The r.m.s. thermal vibration of silicon atoms is 0.078 Å (Kirkland, 2010), which gives a Debye–Waller factor B of 0.12 Å2" | SECTION_READ of the statement; UNVERIFIED for Kirkland's book. The B here follows a different convention: 2 pi^2 (0.078)^2 = 0.120 A^2, whereas the crystallographic B = 8 pi^2 u^2 = 0.480 A^2 (DERIVED_HERE arithmetic). Do not mix the two conventions. |

**(c) Ni, Busch and Zuo 2026 (PyExtal; SECTION_READ of sec. 2.3, 4.1, 4.2, 5 (units), 6.2 and Tables 1-3).**

The electron structure factor includes an absorption term, U_g + i U'_g, computed from "the known
atomic scattering factor f and absorption factor" with a temperature factor (sec. 2.3). The column
headers of Tables 1 to 3 are images, read as U_111, U'_111, U_222 (efi63, efi82, efi64). Units:
the text gives the structure factors in A^-2 (sec. 5, YIG example).

| quantity | value | conditions | locator | label |
|---|---|---|---|---|
| Si U_111, U'_111, U_222 (Extal) | 0.04731, 0.00086, 0.00093 | 200 kV, energy-filtered Si 111 systematic-row CBED, dataset of Zuo (1998) | Table 1; sec. 4.1 | SECTION_READ |
| same (PyExtal) | 0.04735, 0.00079, 0.00092 | same | Table 1 | SECTION_READ |
| Si U_111, U'_111, U_222: IAM | 0.05749, 0.00047, 0 | 300 kV; absorption model and B of the IAM row not stated in the parts read | Table 2 | SECTION_READ |
| same: CBED; LARBED | 0.05430, 0.00091, 0.001055; 0.05449, 0.00067, 0.001191 | 300 kV | Table 2 | SECTION_READ |
| LARBED, mean of 4 datasets x 5 ROIs | U'_111 = 0.00084(10) | 300 kV | Table 3 | SECTION_READ |

Ratios (DERIVED_HERE arithmetic): U'_111/U_111 = 0.0167 (PyExtal) and 0.0182 (Extal) at 200 kV;
0.0082 (IAM), 0.0168 (CBED), 0.0123 (LARBED) at 300 kV. These are **measured anomalous-absorption
ratios for one Si reflection**. They are not a mean absorptive potential. They can serve as a check
of any TDS calculation at s = 0.1595 A^-1 (section 1.5).

**(d) Dr. Probe (SECTION_READ of the celslc page and of preprint sec. 2.2 and 2.3).**

| fact | locator | quote |
|---|---|---|
| Two absorption options: Weickenmeier-Kohl (or Hall-Hirsch) absorptive potentials "describing the loss of electrons in the elastic channel", and "The option is available when applying Debye-Waller factors"; or a constant proportional parameter after Hashimoto, Howie and Whelan: "Typical values are on the range from 0.01 to 0.20" | celslc.html, paragraph "Two different options are provided to apply absorptive potentials" | as quoted |
| The absorptive form factors are for calculations with Debye-Waller-damped potentials; TDS calculations use a different approach (frozen lattice) without Debye-Waller factors | preprint p. 9, sec. 2.2 | "Absorptive form factors may be used for pure bright-field calculations when including damping of form factors by Debye-Waller factors" ... "Calculations including thermal-diffuse scattering and in particular scattering to large angles, e.g. HAADF STEM, should be done without Debye-Waller factors in a different approach" |
| Convention: B = 8 pi^2 <u_s^2>, <u_s^2> = <u_x^2> = <u_y^2> = <u_z^2> (mean square displacement per axis); frozen-lattice displacements are Gaussian with that per-axis rms | preprint p. 9 sec. 2.2; p. 11 sec. 2.3 | "〈u_s^2〉= U = B/(8π^2)" |

The celslc page gives the Hall and Hirsch reference as "Proc. R. Soc. Lond. A 286 (1957) 158-177";
Crossref gives 1965 for volume 286 (a typo on that page; recorded, not propagated).

**(e) muSTEM v5.3 manual (SECTION_READ of sec. 1, 3.8, 3.8.1, 3.8.2).**
Thermal scattering is treated "with one of two models": the absorptive potential (refs. Allen et al.
2003, Bird and King 1990, Hall and Hirsch 1965) or the QEP model, whose total intensity is
"numerically equivalent to what would be obtained in a frozen phonon (FPh) model calculation"
(p. 5, sec. 1; p. 16, sec. 3.8.2). In the QEP model "the atomic potentials are not thermally smeared
out as in the absorptive model but rather are quite sharp" (p. 16). The two are alternatives; the
manual offers no combination of TDS absorption with QEP.

### 1.4 Consolidated statement on double counting (facts, then inference)

Facts (SECTION_READ): Hájek and Rusz (p. 2) state that the frozen-phonon potential has no imaginary
part and absorption arises after averaging. The Dr. Probe preprint (p. 9) ties the Weickenmeier-Kohl
absorptive factors to Debye-Waller-damped static potentials and puts TDS into a separate
frozen-lattice approach. The muSTEM manual (sec. 1, 3.8) offers absorptive and QEP models as
alternatives. None of the sources read uses the phrase "double counting". None discusses
reflection (RHEED/REM) geometry.

Inference (DERIVED_HERE): with the engine's explicit frozen phonons the TDS part of the absorption
is already present in the coherent average, so a Bird-King/Weickenmeier-Kohl/Hall-Hirsch/Peng
absorptive potential must not be added. Electronic absorption (plasmon, single-electron, core)
is not produced by frozen phonons and must be added separately. For the hologram sideband a
plasmon-loss electron is lost (no longer coherent with the reference wave) even though it stays
inside the 3 mrad aperture (theta_E = 0.04 mrad for Si at 200 kV, Mendis 2024 sec. 3). So for
holography the electronic absorption acts on the object wave as true absorption.

### 1.5 Si TDS absorptive potential at 200 keV computed with the published code (DERIVED_HERE)

Script `l6/calc/si_tds_absorption.py` (sha256 97dd2dd2...) imports the unmodified supplementary
module of Thomas et al. 2024 (`main_scattering_function.py`, sha256 bb1cf9f5..., `V = 200000`)
and prints `l6/calc/si_tds_absorption.out` (sha256 3af417fe...). Environment: Python 3.11, numpy
2.4.6, scipy 1.17.1 in a scratch venv. Conventions: V_g = K F_g/Omega with K = h^2/(2 pi m0 e) =
47.87765 V A^2, Omega = a^3, a = 5.4309 A (ASSUMPTION B2); sigma(200 keV) = 7.288401e-4 rad/(V A);
the engine's transmission |T|^2 = exp(-2 sigma V' dz) gives an intensity attenuation length
1/(2 sigma V').

Check of the convention (REPRODUCED): the code's Lobato f_Si(0) = 5.83600 A gives an
independent-atom mean inner potential 8 K f(0)/a^3 = 13.9548 V, which matches the Lobato value
13.955 V of report D3/SM17.

| B (A^2) | source of B | u_rms per axis (A) | f'/f at 000, 111, 022, 004, 044, 008 | V0'(TDS) (V) | 1/(2 sigma V0') (A) |
|---|---|---|---|---|---|
| 0.4561 | A7 (u = 0.076 A, ASSUMPTION) | 0.0760 | 0.00626, 0.01075, 0.01773, 0.02677, 0.03892, 0.05252 | 0.0874 | 7849 |
| 0.4691 | Flensburg and Stewart, <u^2> = 0.005941 A^2 at 293 K (index abstract; section 2) | 0.0771 | 0.00637, 0.01093, 0.01801, 0.02718, 0.03948, 0.05317 | 0.0889 | 7718 |
| 0.4725 | BvK value scaled to 295.5 K as quoted by Heacock et al. (section 2) | 0.0774 | 0.00640, 0.01098, 0.01808, 0.02729, 0.03962, 0.05334 | 0.0893 | 7685 |
| 0.4761 | Heacock et al., neutron Pendellösung, 295.5 K (section 2) | 0.0777 | 0.00643, 0.01103, 0.01816, 0.02740, 0.03977, 0.05352 | 0.0897 | 7650 |
| 0.4804 | u = 0.078 A (Kirkland 2010 as stated by Mendis 2024) | 0.0780 | 0.00646, 0.01109, 0.01826, 0.02753, 0.03996, 0.05373 | 0.0902 | 7609 |

The rows use s = |g|/2 for Si with a = 5.4309 A: s = 0, 0.1595, 0.2604, 0.3683, 0.5208 and
0.7365 A^-1. A direct quadrature of Eq. (2) at B = 0.4725 (`fprime`) gives f'(0), f'(111) and
f'(008) = 0.037406, 0.035816 and 0.023109 A, within 0.2 % of the parameterised values. The
temperature factor exp(-B s^2) multiplies both f and f' (Eq. 1), so the ratio V'_g/V_g = f'(s)/f(s).

What these numbers say (DERIVED_HERE):
1. **The TDS mean absorptive potential of Si at 200 keV is about 0.089 V (0.64 % of the IAM mean
   inner potential).** Its attenuation length, about 7700 A, agrees with Mendis 2024's
   independently calculated phonon mean free path of 7724 A (their Eq. 9; sec. 3). This
   agreement between two different formulae is a consistency check, not a measurement.
2. The TDS absorption is strongly g-dependent: f'/f rises from 0.006 (g = 0) to 0.053 at (0,0,8).
   A proportional model with one ratio cannot represent it. The TEST_ONLY r = 0.05 happens to match
   the TDS ratio at (0,0,8), but its mean (0.695 V) is eight times the TDS mean.
3. Against measurement: Ni et al. 2026 refined U'_111/U_111 = 0.0167 (PyExtal) and 0.0182 (Extal)
   from 200 kV energy-filtered CBED. The computed TDS ratio at (111) is 0.0110. The measured
   anomalous absorption at (111) is therefore about 1.5 to 1.7 times the TDS-only value. Radi's
   index abstract puts an electronic contribution C(el)/V_g of 0.005 to 0.012 at 100 keV for low
   g. The difference 0.006 to 0.007 falls in that range, but this is an inference across energies
   and papers (Radi's tables unread).
4. Electronic (non-phonon) absorption, which frozen phonons do not provide, dominates the mean:
   V0'(el) = 1/(2 sigma Lambda) = 0.653 V for the Si plasmon mean free path of 1050 A at 200 kV
   (Mendis 2019, measured by EELS, as stated by Mendis 2024; the measurement itself is
   UNVERIFIED), or 0.827 V for the total inelastic mean free path of about 830 A (Malis formula,
   Mendis 2024). Plasmon scattering is delocalised (theta_E = 0.04 mrad), so its absorption is
   close to uniform in the crystal. A proportional V' = r V(r) concentrates it on the atom cores
   instead.
5. Caveat for reflection: these are bulk values. At glancing incidence the wave travels along the
   surface within tens of Angstrom of it, and surface-plasmon excitation (including in the vacuum
   above the surface) and the change of bulk-plasmon excitation near a surface are not
   represented. No source on REM/RHEED loss at 200 keV was read here (Z. L. Wang 1996, ZLWANG96,
   and Peng-Dudarev-Whelan B08 ch. 7-8 are closed).

## 2. Si thermal displacement (Debye-Waller factor) at room temperature

### 2.1 Sources

| file in l6/ | URL | SHA-256 | what it is |
|---|---|---|---|
| arx_2103.05428.pdf | https://arxiv.org/pdf/2103.05428 (v3, 19 Aug 2021) | d0502e34388df72f8c679813d78a6e58058cb604ff1882a13b9c2a456ec2ced3 | B. Heacock et al., "Pendellösung interferometry probes the neutron charge radius, lattice dynamics, and fifth forces", 45 pages incl. supplementary text; version of record Science 373 (2021) 1239-1243, doi:10.1126/science.abc2794 (Crossref, 14 authors). The arXiv v3 is the version read; the Science pagination is not. |
| arx_2203.12554.pdf | https://arxiv.org/pdf/2203.12554 | 75db1c41bfff2621d0a731f0b9ed0b074f9f69269e382c587b675c59987bfff5 | Chalise, Kenesei, Shastri, Cahill, "Temperature mapping of stacked silicon dies from x-ray diffraction intensities" (secondary use of Flensburg and Stewart) |
| arx_2608.27361.pdf | https://arxiv.org/pdf/2608.27361 | dbc602263a4ff3ca5de9c5cd1bdbd0dee736e378612cbd6e058246e9adbd3d4a | Nery et al. 2026 (first-principles T-dependent Si charge density); searched, no Si B value used here |

### 2.2 Values

| quantity | value | T | method | locator | label |
|---|---|---|---|---|---|
| B (Si) | 0.4761(17) A^2 | 295.5 K | neutron Pendellösung interferometry, (111), (220), (400) structure factors, B and the neutron charge radius fitted together (correlation -0.94) | arXiv v3 p. 6 (main text): "our results are B = 0.4761(17) Å2" | SECTION_READ |
| B (Si), constrained | 0.4767(6) A^2 | 295.5 K | same data with b(Q)/b(0) constrained to the world-average charge radius | arXiv v3 PDF p. 33 (Supplementary Text) | SECTION_READ |
| B_BvK (Si) | 0.4725(17) A^2 | scaled to 295.5 K | Flensburg and Stewart's Born-von Karman fit to inelastic neutron data, as quoted and rescaled by Heacock et al. | arXiv v3 PDF p. 6 and p. 32 (Supplementary Text) | SECTION_READ of the statement about Flensburg and Stewart |
| tension between the two | "The tension (p = 0.018) between BBvK and our result B = 0.4767(6)" | 295.5 K | | arXiv v3 p. 33 | SECTION_READ |
| dB/dT | 0.0014 A^2/K | at 295.5 K | "BvK model predicted slope" used to scale all results | arXiv v3 PDF p. 25 (Materials and Methods) | SECTION_READ |
| conservative B | 0.4714(57) A^2 | 295.5 K | chosen so that its 68 % region covers B from X-ray data (single B or separate 1s B) | arXiv v3 PDF p. 31 (Materials and Methods) | SECTION_READ |
| convention | <u^2> = B/(8 pi^2); W = B Q^2/(16 pi^2) with Q = 2 pi/d | | | arXiv v3 p. 3 | SECTION_READ |
| <u^2> (Si) | 0.005941 +- 0.000021 A^2 | 293 K | lattice dynamics (Born-von Karman, six neighbour shells) fitted to inelastic-neutron phonon dispersion | Flensburg and Stewart 1999 abstract (OpenAlex index); body closed (APS 403) | METADATA_VERIFIED +ABSTRACT(OpenAlex) |
| <u^2> (Si), statement | 0.0059 A^2 at room temperature, cited to Flensburg and Stewart | room T | | Chalise et al., arXiv:2203.12554 v2, PDF p. 3 (also: Debye-model estimate 0.0058 A^2) | SECTION_READ of a secondary statement |
| u_rms (Si), statement | 0.078 A (cited to Kirkland 2010) | not stated | | Mendis 2024, sec. 3 | SECTION_READ of a secondary statement; UNVERIFIED for Kirkland |

Cross-check (DERIVED_HERE): 8 pi^2 x 0.005941 = 0.4691 A^2 at 293 K; plus 2.5 K x 0.0014 A^2/K =
0.4726 A^2 at 295.5 K. This reproduces the 0.4725(17) A^2 that Heacock et al. attribute to
Flensburg and Stewart. It supports the index-abstract value and the per-axis reading of
Flensburg and Stewart's <u^2> without reading their body.

Sears and Shelley 1991 and Peng et al. 1996b (the tabulations named in the task) are closed (IUCr
403). Their Si values are UNVERIFIED and not quoted.

### 2.3 What this means for A7 (DERIVED_HERE)

The engine's `FrozenPhonons.rms_displacement_A` is the rms per Cartesian axis (independent
Gaussian per axis, `rng.normal(0, u, xyz.shape)`), the same convention as <u_s^2> = B/(8 pi^2) in
Dr. Probe (preprint p. 11) and in Heacock et al. (p. 3). Values:
* Heacock et al. 2021, measured: u = sqrt(0.4761/(8 pi^2)) = 0.07765 A (+-0.00014 A from the
  +-0.0017 A^2) at 295.5 K;
* Flensburg and Stewart (BvK) at 293 K: u = sqrt(0.005941) = 0.07708 A;
* A7: 0.076 A, i.e. B = 0.456 A^2, which is 4.2 % below the measured B (2.1 % below in u) and
  1.5 % below in u against the BvK value.

Einstein-model caveat (SECTION_READ in Hájek and Rusz 2026, p. 4-6): independent Gaussian
displacements miss phonon correlations. For light diamond at 300 kV the Einstein and correlated
(MD) frozen-phonon elastic intensities differ by about 1e-3 I0 at the central beam. The
single-site B is still the right input for the Einstein model.

### 1.6 How RHEED work on Si treats absorption (open J-STAGE papers; 10 kV, not 200 kV)

Files: `ejssnt2008_87.pdf` (https://www.jstage.jst.go.jp/article/ejssnt/6/0/6_0_87/_pdf, sha256
df3e052e323434538e706e48aafaaff5eec135d7e430a6e1d67cb3e8dee78d54), `ejssnt2014_380.pdf`
(https://www.jstage.jst.go.jp/article/ejssnt/12/0/12_380/_pdf, sha256
99ae4541976d8a488ad745bdc2fec9739097028fad2ded65a65f15d26f5fcbe3), `ejssnt2022_013.pdf`
(https://www.jstage.jst.go.jp/article/ejssnt/20/2/20_2022-013/_pdf, sha256
65170c7345e47f27c3ae60496943e1e54a603a3690fa210b0a737187e8c03e92). All open on J-STAGE; DOIs
Crossref-verified (section 6).

| source | conditions | absorption model used (as printed) | locator | label |
|---|---|---|---|---|
| Minami, Yamagata, Nakahara, Ichimiya, e-J. Surf. Sci. Nanotech. 6 (2008) 87-90 | Si(111)7x7, energy-filtered RHEED, 10 kV, glancing angle 0.5-4.8 deg | "U(S) = U_TDS e^(-2BS^2) + U_el e^(-50S^2)" (Eq. 1), with U_TDS the mean TDS imaginary potential, U_el the mean electronic-excitation imaginary potential, B the Debye parameter, cited to Ichimiya 1985 and 1987. Table I, bulk: U_TDS = 0.37 V, B = 0.38 A^2, and U_el = 0.01 V (with-loss patterns) or 1.28 V (no-loss patterns). Adatoms: 0.80 V, B = 3.00 A^2, U_el = 0.01 or 1.60 V | p. 2 Eq. (1); p. 3 Table I; p. 1 sec. II | SECTION_READ (values are fitted or chosen for 10 kV; the formula's source, Ichimiya 1985, is closed: UNVERIFIED) |
| same | | "it must be taken into account that strong electron absorption effects by plasmon excitation at surface selvedge for low glancing angles. In the present stage, the absorption effects are not known for fast electrons." | p. 2 | SECTION_READ |
| Horio, Takakuwa, Ogawa, e-J. Surf. Sci. Nanotech. 12 (2014) 380-386 | Si(001)2x1 many-beam rocking curves, 10 kV, [1-10] azimuth | "10% of the value was adopted as an imaginary potential" (proportional model, r = 0.1); Debye-Waller factor from a Debye temperature of 580 K (Radi 1970), "0.07 Å at RT"; Bragg angles "calculated using the mean inner potential of Si (12 eV)" | p. 4 (multislice paragraph); p. 5 | SECTION_READ |
| Horio, Nakahara, Yuhara, Takakuwa, e-J. Surf. Sci. Nanotech. 20 (2022) 76-84 | Si(111)7x7, energy-loss spectra of the specular beam, 10 keV | Inelastic Fourier coefficients "simply treated as 10% of those of the elastic-scattering potential"; "The mean inner potential of Si, V000 = 13.9 eV, was corrected to a more realistic value of 12 eV [19]" ([19] = Horio and Ichimiya, Surf. Sci. 133 (1983) 393); bulk vibration 0.071 A "from the data by Radi" | p. 4, sec. III.B "Calculation of rocking curve and wavefield" | SECTION_READ |
| same | same | Measured mean number of surface-plasmon excitations of the specular beam proportional to 1/sin(theta), fitted as beta times the Lucas value, n_s = beta e^2/(8 eps0 hbar v sin theta) (Eq. 1), with beta = 0.66 (one-beam condition) and 0.71 (<112> azimuth), "~70% of Lucas' theoretical value" | abstract; p. 4, Eq. (1) | SECTION_READ |

Inferences (DERIVED_HERE; extrapolations, not sourced values for 200 keV):
* The RHEED practice in the papers read is a proportional imaginary potential of 10 % (Horio 2014,
  2022) or Ichimiya's two-term form (Minami 2008). Both are used at 10 kV. Neither is a
  measurement for 200 keV.
* Energy scaling of the TDS term: by Thomas et al. Eq. (2), f' is proportional to 1/beta. The
  200 keV value V0'(TDS) = 0.089 V (section 1.5) therefore corresponds to 0.089 x 0.6953/0.1950 =
  0.32 V at 10 keV (beta = 0.1950 at 10 keV). That is the same size as Minami's U_TDS = 0.37 V
  (with B = 0.38 A^2). A consistency check only.
* Surface plasmons at 200 keV. The Lucas expression of Horio 2022 Eq. (1), evaluated with the
  relativistic velocity (beta = 0.6953), gives e^2/(8 eps0 hbar v) = (pi/2)(alpha/beta) = 0.01649.
  At theta = 16.13 mrad that is n_s = 1.02 x beta_corr, i.e. 0.67-0.73 excitations per
  reflection for beta_corr = 0.66-0.71 (the 10 keV Si(111)7x7 correction, **extrapolated**). If
  it holds at 200 keV, only exp(-0.7) = 0.50 of the specularly reflected electrons leave without
  a surface-plasmon loss. The loss happens mostly in the vacuum selvedge (interaction thickness
  about 3.6 A at 10 keV, Horio 2022 p. 7). No bulk imaginary potential represents it. For a
  hologram it lowers the coherent (sideband) amplitude and adds incoherent background. To first
  order it is common to identical terraces at the same angle, but a step changes the local
  selvedge geometry. This is the largest absorption-like effect identified here, and it is
  unsourced at 200 keV.

## 3. Mean inner potential of Si

### 3.1 Values found

| value (V) | method | conditions | source | locator | label |
|---|---|---|---|---|---|
| 12.48 +- 0.22 | beam refraction at a wedge edge in STEM micro-diffraction; DPC-STEM "gave very similar values" | Si wedge; energy not in the abstract | Wu and Spiecker, Ultramicroscopy 176 (2017) 233-245, doi:10.1016/j.ultramic.2017.03.029 (Crossref); PubMed abstract PMID 28366352 (Europe PMC record sha256 7d115963...) | abstract sentence 2: "Our measurement of MIP of Si and GaAs resulted in 12.48 ± 0.22 V and 14.15 ± 0.22 V, respectively, from directly evaluating beam refraction in micro-diffraction mode." | METADATA_VERIFIED +ABSTRACT(PubMed); body closed |
| "between approximately 11.5 and 12.5 V, with uncertainties ranging from a few tenths ... up to about 1.3 V" | off-axis electron holography | several | Zheng, arXiv:2603.10523v2 (Front. Phys. 21 (2026) 114201), a statement about Wang et al. 1997, Wu et al. 2004, Kruse et al. 2006 | PDF p. 30 | SECTION_READ of a secondary statement; the three originals are UNVERIFIED |
| 9.26 +- 0.08 | "Early off-axis electron holography combined with theoretical corrections" | | the same Zheng statement, attributed to Gajdardziska-Josifovska et al. 1993 | PDF p. 30 | SECTION_READ of a secondary statement; **UNVERIFIED and suspicious**: it lies 2-3 V below every other Si value; check against the original (upload list) |
| (Si measured; no number in the abstract) | off-axis holography plus shadow imaging to fix thickness and beam direction, for MIP and structure factors | | Wu, Schofield, Zhu, Tafto, Ultramicroscopy 98 (2004) 135-143, doi:10.1016/j.ultramic.2003.08.006 (Crossref) | PubMed abstract (PMID 15046792): "we present the results of mean-inner potential determination from silicon" | METADATA_VERIFIED +ABSTRACT(PubMed) |
| 12 | "more realistic value" used in RHEED dynamical calculations of Si(111), replacing the Doyle-Turner 13.9 V | 10 keV RHEED practice | Horio et al. 2022, citing Horio and Ichimiya, Surf. Sci. 133 (1983) 393-400 (doi:10.1016/0039-6028(83)90009-2, Crossref; closed) | Horio 2022 p. 4 | SECTION_READ of a secondary statement; the 1983 determination is UNVERIFIED |
| 12 | used to compute Bragg glancing angles for Si(001) | 10 kV RHEED | Horio et al. 2014 | p. 5 | SECTION_READ (a value used, not measured there) |
| 12.53 (fit intercept) | DFT (WIEN2k GGA), bulk-terminated slab, innermost monolayer | no uncertainty | Schowalter, Kruse, Rosenauer, arXiv:2607.05948v1 | Fig. 2c, p. 3 (read in L5) | SECTION_READ (L5) |
| 13.70 | first-principles pro-crystal (superposed free atoms) | | Zheng 2026 | PDF p. 30 | SECTION_READ |
| 13.91 | Hartree-Fock independent atoms (statement about Kruse et al. 2006) | | Zheng 2026 | PDF p. 30 | SECTION_READ of a secondary statement |
| 13.9 | Doyle-Turner independent atoms, as used before correction | | Horio et al. 2022 | p. 4 | SECTION_READ |
| 13.903 / 13.955 / 13.912 | Kirkland / Lobato / Peng independent-atom parameterisations at a = 5.4309 A | engine | report D3, SM17 | | REPRODUCED (D3); the Lobato value is reproduced again here, 13.9548 V (section 1.5) |

Files: `epmc_ws17b.json` (Europe PMC REST, `EXT_ID:28366352 AND SRC:MED`, sha256
7d115963e606528c95b134dd4801cf933dd87e8e68e2a3731bce7db793b589aa); `epmc_wu2017.json` (same
abstract under PMID 28189911, sha256 c174ecf8...); `epmc_wu2004.json` (PMID 15046792, sha256
9086205d...); `arx_2603.10523.pdf` (https://arxiv.org/pdf/2603.10523, v2, sha256
48c4a7ee08c6961a6ff949318b41846a2cd7110ff57af895f3f85d5e6627dfba).

Record discrepancy: Crossref gives Wu and Spiecker as Ultramicroscopy **176**, 233-245
(doi:10.1016/j.ultramic.2017.03.029). A second Crossref DOI, 10.1016/j.ultramic.2017.01.011, is a
"Publisher's note" in volume 177, pp. 1-13, with no authors. PubMed carries the same abstract under
both PMIDs (28366352: vol. 176, 233-245; 28189911: vol. 177, 1-13). Cite the volume 176 record.

Kruse et al. 2006, Gajdardziska-Josifovska et al. 1993, Wang et al. 1997 and Kim, Zuo and Spence 1998
remain closed (L5). Their values are known here only through Zheng's secondary statement.

### 3.2 Reading (DERIVED_HERE)

* The only first-hand measured value with an uncertainty found in an open record is 12.48 +- 0.22
  V (Wu and Spiecker, abstract level). It agrees with the DFT slab value 12.53 V (L5) within its
  uncertainty and is 0.48 V above the repository's B1 (12.0 V). The RHEED community's working value
  for Si surfaces is 12 V (Horio 2014, 2022, citing Horio and Ichimiya 1983).
* Every independent-atom value (13.7-13.96 V) exceeds every bonded or measured value by 1.2-1.9 V.
  The engine's 13.903 V (B32) is a model systematic, as B32 already says.
* The number that matters for the experiment is the potential step at the real surface. For
  ion-milled, oxide-covered Si(001) it is not bulk Si (Pennington 2015 and Auslender 2024
  abstracts, L5). A rocking-curve calibration on the sample (item 9) remains the better route.

### 1.7 A measured Si absorption potential (100 keV, open): Voss, Lehmpfuhl and Smith 1980

Found at 22:48 UTC. The Zeitschrift für Naturforschung A archive 1946-2001 is open (CC BY 4.0,
digitised 2013 by the publisher with the Max Planck Society). It sits in the MPG repository Edmond
as dataset doi:10.17617/3.GRUJYR (Dataverse record `l6/edmond_ds.json`), with `Reihe_A.zip`
(50 086 033 062 bytes, datafile 200989) served from an S3 object store that honours HTTP Range. The
three articles below were extracted as single zip members by range requests (`l6/rzip.py`,
`l6/rzip_get.py`: 26 215 members listed, 16 requests in all), not by downloading the archive.
The degruyter.com pages answer HTTP 202 with an empty body (bot check).

| file in l6/zfn/ | zip member | SHA-256 | article (Crossref-verified, section 6) |
|---|---|---|---|
| ZNA-1980-35a-0973.pdf | 35/ZNA-1980-35a-0973.pdf | 21aa1692f488e988e602a8549ac96fab4898a7a70128584483c0773595e12a92 | R. Voss, G. Lehmpfuhl, P. J. Smith, "Influence of Doping on the Crystal Potential of Silicon investigated by the Convergent Beam Electron Diffraction Technique", Z. Naturforsch. 35a (1980) 973-984, doi:10.1515/zna-1980-0913 |
| ZNA-1972-27a-0390.pdf | 27/ZNA-1972-27a-0390.pdf | 634cf192a9bb97991169035ff096bdc5e2a6f81d5c28372f3a645059881332d6 | A. R. Moon, "Calculation of Reflected Intensities for Medium and High Energy Electron Diffraction", Z. Naturforsch. 27a (1972) 390-395, doi:10.1515/zna-1972-0303 |
| ZNA-1972-27a-0382.pdf | 27/ZNA-1972-27a-0382.pdf | 3265c31de7c72df81383361bd493e809ad59d71d7c61039caf59d51ce214a176 | A. Howie, R. M. Stern, "The Optical Potential in Electron Diffraction", Z. Naturforsch. 27a (1972) 382-389, doi:10.1515/zna-1972-0302 (abstract and first page read only: Al, Cu, Au, 20 eV-100 keV; no Si) |

Voss et al. (SECTION_READ; pages read as rendered images at 110 dpi because the OCR text layer
garbles the equations and tables):

| fact | locator | label |
|---|---|---|
| CBED (Kossel-Möllenstedt) with 100 keV electrons; accelerating voltage refined from Kikuchi-line intersections to +-500 V; pure and doped Si plates parallel to (110), about 100 A probe | p. 975 (film calibration "for 100 keV electrons"); p. 980 | SECTION_READ |
| Absorption model: V_g^im = V_g^real (B abs(g) - C g^2) (Eq. 3), relation "due to Humphreys and Hirsch", constants B, C "determined experimentally by Ichimiya and one of us [12] and refined during this analysis" | p. 974, Eq. (3) | SECTION_READ |
| Fitted "consistently for all investigated specimens": B = 0.004, C = 0.0003, and "a mean absorption potential of V_000^im = 0.61 Volt", determined "by measuring the current of the incident electron beam and the current density distribution in the diffracted beams taking into consideration the crystal thickness" | p. 981; p. 983 | SECTION_READ |
| Table 5, "Absorption potentials of silicon (in volts)": present result 000 0.61, 111 0.031, 220 0.039, 311 0.025, 004 0.027; Ichimiya and Lehmpfuhl (1978): 111 0.044, 220 0.052, 311 0.032, 004 0.038 (B 0.0055, C 0.00045); Kreutle and Meyer-Ehmsen (1969, 500 K): 000 0.92, 111 0.15; Radi (1970): 000 0.70, 111 0.1, 220 0.11, 311 0.07, 004 0.09 | p. 983, Table 5 | SECTION_READ (the 1978, 1969 and 1970 columns are statements about those papers) |
| The g != 0 values "were calculated from relation (3) using the parameters B and C"; "The present values, which are very reliable, are very small and about 1/3 of the theoretical values" (Radi's) | p. 983 | SECTION_READ |
| Real structure potentials at room temperature, weakly doped Si (Table 1): V111 = -5.12, V220 = -4.40, V311 = -2.50, V222 = -0.15, V400 = -2.60 V, each +-0.03 V (Doyle-Turner: -5.43, -4.337, -2.435, 0, -2.566) | p. 982, Table 1 | SECTION_READ |
| Si Debye-Waller factor used to convert Aldred and Hart's X-ray structure factors: "B = 0.4613 at 293.2 K" | p. 982, Table 3 caption | SECTION_READ (a value used, source of the number not stated on the pages read) |

DERIVED_HERE from these numbers:
* Measured anomalous-absorption ratios at 100 keV: V'_g/V_g = 0.031/5.12 = 0.0061 (111),
  0.0089 (220), 0.0100 (311), 0.0104 (004). Radi's theory (via Table 5): 0.020 (111).
* By the 1/beta scaling of the TDS factor (Thomas et al. Eq. 2; beta = 0.5482 at 100 keV, 0.6953 at
  200 keV), the computed TDS ratio at (111) is 0.0110 x 1.268 = 0.0139 at 100 keV. That is 2.3 times
  Voss's value. Ni et al. 2026 measured 0.0167-0.0182 at 200 kV, i.e. 1.5-1.7 times the TDS value.
  **The published anomalous absorption of Si (111) therefore scatters by a factor of about 3 once
  scaled to a common energy.** This is the size of the uncertainty of any g-dependent imaginary
  potential for Si, independent of which parameterisation is chosen.
* Voss's measured mean V'_000 = 0.61 V at 100 keV is about 5.4 times the TDS-only value scaled to
  100 keV (0.089 x 1.268 = 0.113 V). The measured mean absorption therefore contains a large
  non-TDS (electronic) part. The pages read do not say how the film and Faraday-cup measurement
  treats small-angle inelastic electrons inside the discs. At 200 keV the sum TDS + plasmon from
  section 1.5 is 0.089 + 0.653 = 0.74 V, the same order as 0.61 V at 100 keV. No energy scaling of
  the electronic part is claimed here.
* The g-units of Eq. (3) are not stated on the pages read. With abs(g) = 2 pi/d in 1/A and the
  Table 1 V_g, Eq. (3) gives 0.035, 0.043, 0.027 and 0.031 V for 111, 220, 311 and 004, which is
  10-14 % above Table 5. The exact convention was not reproduced, so the Table 5 values are quoted
  and Eq. (3) is not re-used.

## 4. Published RHEED/REM rocking curves or reflectivities for Si usable as a benchmark

No open source with a measured Si(001) or Si(111) rocking curve or reflectivity at 100-300 keV was
found. What exists:

| source | surface, energy | what it gives | locator | access | label |
|---|---|---|---|---|---|
| Moon 1972 (open, CC BY via Edmond) | Si(111), 40 keV | Fig. 1: calculated "systematics" specular intensity against incident angle (about 10-55 mrad; peaks labelled 333, 444, 555, 666, 777) compared with Menadue's experimental values. Best agreement at the 555 peak with inner potential 12 V (curve 1; 8 V for curve 2) and V_imaginary = V_real/8 | p. 393 Fig. 1 and caption; p. 394 text | open | SECTION_READ (the experimental points are Menadue's, reproduced in Moon's figure) |
| Menadue, Acta Cryst. A 28 (1972) 1-11, doi:10.1107/s0567739472000014; Colella and Menadue, Acta Cryst. A 28 (1972) 16-22, doi:10.1107/s0567739472000038 | Si(111), glancing-incidence high-energy electron diffraction (40 keV per Moon) | the measured specular intensities | not read | closed (IUCr 403) | METADATA_VERIFIED (Crossref records). That Menadue 1972 is Moon's ref. 13 ("J. F. MENADUE, Acta Cryst., to be published") is an inference from author, journal, year and subject (DERIVED_HERE) |
| Lehmpfuhl and Dowell, Acta Cryst. A 42 (1986) 569-577, doi:10.1107/s0108767386098720 | Si(111), convergent-beam RHEED | CB-RHEED observations (a disc is a rocking curve); energy UNVERIFIED (Lehmpfuhl's camera worked at 100 keV in Voss 1980, p. 975; this is not evidence for the 1986 paper) | not read | closed (IUCr 403) | METADATA_VERIFIED |
| Hayakawa and Aizawa, Jpn. J. Appl. Phys. 21 (1982) L215, doi:10.1143/jjap.21.l215 | Si(111) RHEED surface-wave resonance | energy UNVERIFIED | not read | closed (IOP) | METADATA_VERIFIED |
| Horio, Takakuwa, Ogawa 2014 (open, J-STAGE) | Si(001)2x1, 10 kV, [1-10] azimuth, room temperature and 880/1031 K | Fig. 5: experimental (thick) and calculated (thin) rocking curves of five spots at RT, best fit with the asymmetric dimer (R = 0.0); absorption 10 % proportional; V0 = 12 V; Bragg peaks listed: 004 at 1.66 deg, 006 at 3.34 deg, 008 at 4.79 deg | p. 5 Fig. 5; p. 5 text | open | SECTION_READ (figure caption and text; data not digitised) |
| Minami et al. 2008 (open) | Si(111)7x7, 10 kV, energy-filtered | Figs. 3-5: with-loss and no-loss rocking curves and intensity ratios | p. 2-3 | open | SECTION_READ (captions and text) |
| Osakabe, Tanishiro, Yagi, Honjo, Surf. Sci. 97 (1980) 393-408, doi:10.1016/0039-6028(80)90675-5 (already [P14] in docs/references.bib) | REM of Si(111), clean and Au-covered | imaging; whether a rocking curve is given is UNVERIFIED | not read | closed | METADATA_VERIFIED (Crossref search result) |
| P18, P20-P23, P26 (Peng and Cowley 1986; Ma and Marks 1989, 1990a,b; Yagi 1987; Yao and Cowley 1990) | REM theory and conditions | whether any gives a Si rocking curve at 100-300 keV is UNVERIFIED | not read | closed | METADATA_VERIFIED (B3) |

Assessment (DERIVED_HERE): a quantitative 200 keV benchmark for Si(001) does not exist in any
source read. The best candidates are (i) Lehmpfuhl and Dowell 1986 (CB-RHEED Si(111), probably
100 keV, closed) and (ii) the Menadue 1972 Si(111) specular curve at 40 keV, whose data points
are visible in Moon's open Fig. 1 and could be digitised from the 110-dpi render with limited
accuracy. For rung 2 of the validation ladder the engine can be run at 10 kV against Horio 2014
Fig. 5 (Si(001), open). That comparison needs the 2x1 dimer reconstruction, which the engine does
not implement (H2 N4), so a bulk-terminated engine cannot be expected to match it. At 40 keV
against Menadue/Moon (Si(111), specular, 333-777 peaks), the bulk termination is also an
approximation (Si(111)7x7 or 2x1).

## 5. Summary table

"open?" means readable by an automated client from this environment on 2026-09-23. "DERIVED_HERE"
rows are L6 arithmetic or L6 runs of published code on the stated inputs.

| quantity | value | conditions | source | locator | label | open access? |
|---|---|---|---|---|---|---|
| Si Debye-Waller B | 0.4761(17) A^2 (u = 0.07765 A per axis) | 295.5 K; neutron Pendellösung (111), (220), (400) | Heacock et al. 2021 (Science 373, 1239) | arXiv:2103.05428v3 PDF p. 6 | SECTION_READ (arXiv v3) | yes (arXiv) |
| Si B, constrained fit | 0.4767(6) A^2 | 295.5 K, charge radius constrained | Heacock et al. 2021 | PDF p. 33 | SECTION_READ | yes |
| Si B, lattice dynamics | 0.4725(17) A^2 (u = 0.0774 A) | BvK fit to inelastic neutron data, scaled to 295.5 K | Flensburg and Stewart 1999, as quoted by Heacock et al. | PDF p. 6, p. 32 | SECTION_READ of a statement | yes (statement); original closed |
| Si <u^2> | 0.005941 +- 0.000021 A^2 (B = 0.4691 A^2) | 293 K, BvK | Flensburg and Stewart 1999 | abstract | METADATA_VERIFIED +ABSTRACT(OpenAlex) | no (APS 403) |
| dB/dT (Si) | 0.0014 A^2/K | at 295.5 K, BvK model | Heacock et al. 2021 | PDF p. 25 | SECTION_READ | yes |
| Si B used by CBED study | 0.4613 A^2 | 293.2 K | Voss et al. 1980 | p. 982, Table 3 caption | SECTION_READ (a value used) | yes (CC BY) |
| Si u_rms | 0.078 A | not stated | Kirkland 2010, as stated by Mendis 2024 | Mendis 2024 sec. 3 | SECTION_READ of a statement; UNVERIFIED for Kirkland | yes (statement) |
| A7 (repository) | 0.076 A (B = 0.456 A^2) | | inspected repository / Prismatic example | | ASSUMPTION | - |
| Si TDS absorptive factor f'(s, B) | f'/f = 0.0064 (g = 0), 0.0110 (111), 0.0181 (022), 0.0273 (004), 0.0396 (044), 0.0533 (008) | 200 keV, B = 0.4725 A^2, Bird-King integral, Lobato f | Thomas, Cleverley, Beanland 2024, Eq. (2) and supplementary code | l6/calc/si_tds_absorption.out | DERIVED_HERE (published code run by L6) | yes (CC BY) |
| Si mean TDS absorptive potential V0'(TDS) | 0.089 V (0.0874-0.0902 V for B = 0.456-0.480 A^2); attenuation length about 7700 A | 200 keV | as above | as above | DERIVED_HERE | yes |
| Si phonon mean free path | 7724 A | 200 kV, calculated | Mendis 2024 | sec. 3 | SECTION_READ | yes (CC BY) |
| Si plasmon mean free path | 1050 A (V0'(el) = 0.653 V by 1/(2 sigma Lambda), DERIVED_HERE) | 200 kV, EELS | Mendis 2019, as stated by Mendis 2024 | Mendis 2024 sec. 3 | SECTION_READ of a statement; original UNVERIFIED | statement yes; original no |
| Si total inelastic mean free path | about 830 A (V0' = 0.827 V, DERIVED_HERE) | 200 kV, Malis formula (calculated) | Mendis 2024 | sec. 3 | SECTION_READ | yes |
| Si plasmon characteristic angle theta_E; critical angle theta_c | 0.04 mrad; 19.1 mrad (fit, rescaled from 300 kV) | 200 kV, 17 eV loss | Mendis 2024 | sec. 3 | SECTION_READ | yes |
| Si U'_111/U_111 (measured) | 0.0167 (PyExtal), 0.0182 (Extal) | 200 kV energy-filtered CBED | Ni, Busch, Zuo 2026 | Table 1 | SECTION_READ (ratio DERIVED_HERE) | yes |
| Si U'_111/U_111 (measured) | 0.0168 (CBED), 0.0123 (LARBED); U'_111 = 0.00084(10) A^-2 over 20 fits | 300 kV | Ni, Busch, Zuo 2026 | Tables 2, 3 | SECTION_READ | yes |
| Si mean absorption potential V'_000 (measured) | 0.61 V | 100 keV CBED, room temperature | Voss, Lehmpfuhl, Smith 1980 | p. 981; Table 5, p. 983 | SECTION_READ | yes (CC BY, Edmond) |
| Si V'_111, V'_220, V'_311, V'_004 | 0.031, 0.039, 0.025, 0.027 V (from fitted Eq. (3), B = 0.004, C = 0.0003) | 100 keV, room temperature | Voss et al. 1980 | Table 5, p. 983 | SECTION_READ | yes |
| Si V'_g (theory, Radi 1970 via Voss) | 000 0.70, 111 0.1, 220 0.11, 311 0.07, 004 0.09 V | 100 keV | Voss et al. 1980 Table 5 | p. 983 | SECTION_READ of a statement; Radi UNVERIFIED | statement yes; Radi no |
| Electronic/structure-potential ratio (Radi) | C(el)/V_g = 0.005-0.012 for low g, "practically all Z" | 100 keV | Radi 1970 | abstract | METADATA_VERIFIED +ABSTRACT(OpenAlex) | no |
| RHEED imaginary potential for Si (practice) | proportional 10 % | 10 kV | Horio 2014, Horio 2022 | p. 4 (both) | SECTION_READ | yes (J-STAGE) |
| RHEED imaginary potential for Si (Ichimiya form) | U_TDS = 0.37 V, B = 0.38 A^2, U_el = 0.01 or 1.28 V (bulk) | 10 kV, Si(111)7x7 | Minami et al. 2008 | Eq. (1) p. 2; Table I p. 3 | SECTION_READ | yes |
| Surface-plasmon excitations per specular reflection | beta x e^2/(8 eps0 hbar v sin theta), beta = 0.66-0.71 (measured at 10 keV) | Si(111)7x7, 10 keV | Horio et al. 2022 | Eq. (1), p. 4 | SECTION_READ | yes |
| same, extrapolated | 0.67-0.73 per reflection | 200 keV, theta = 16.13 mrad | Horio 2022 Eq. (1) with beta from 10 keV | this report sec. 1.6 | DERIVED_HERE (extrapolation, unsourced at 200 keV) | - |
| Si mean inner potential (measured) | 12.48 +- 0.22 V | beam refraction at a wedge edge, STEM micro-diffraction | Wu and Spiecker 2017 (Ultramicroscopy 176, 233) | abstract sentence 2 | METADATA_VERIFIED +ABSTRACT(PubMed) | no (Elsevier) |
| Si MIP (holography, secondary) | about 11.5-12.5 V, uncertainties up to about 1.3 V | several | Zheng 2026, about Wang 1997, Wu 2004, Kruse 2006 | PDF p. 30 | SECTION_READ of a statement | statement yes |
| Si MIP (RHEED practice) | 12 V | RHEED, Si(111), Si(001) | Horio 2014, 2022 (citing Horio and Ichimiya 1983); Moon 1972 (best fit at 40 keV, V_im = V_real/8) | Horio 2022 p. 4; Moon 1972 p. 394 | SECTION_READ | yes |
| Si MIP (DFT slab) | 12.53 V | WIEN2k GGA, bulk-terminated slab | Schowalter et al. arXiv:2607.05948v1 | Fig. 2c (L5) | SECTION_READ (L5) | yes |
| Si MIP (independent atoms) | 13.70 (pro-crystal DFT), 13.9 (Doyle-Turner), 13.903 (Kirkland), 13.955 (Lobato; 13.9548 here) V | | Zheng 2026; Horio 2022; D3; this report | | SECTION_READ / REPRODUCED | - |
| Si MIP 9.26 +- 0.08 V (Gajdardziska-Josifovska 1993, as stated by Zheng) | 9.26 +- 0.08 V | | Zheng 2026 | PDF p. 30 | UNVERIFIED (suspicious; do not use) | original no |
| High-energy Si rocking curve | Si(111) specular, 333-777 peaks, 40 keV (Menadue's data in Moon's Fig. 1) | 40 keV | Moon 1972 | Fig. 1, p. 393 | SECTION_READ | yes (CC BY) |
| Si(001) rocking curves | five spots, RT, 10 kV, [1-10] | 10 kV | Horio 2014 | Fig. 5, p. 5 | SECTION_READ | yes |
| 100-300 keV Si rocking curve | none found | | best lead Lehmpfuhl and Dowell 1986 (CB-RHEED Si(111)) | | METADATA_VERIFIED only | no |

## 6. Crossref verification record

Every DOI in this report and in `L6_new_refs.bib` was read from a Crossref `/works/<doi>` record
fetched by L6 (cached in `l6/crossref/<KEY>.json`). Fields were generated from the JSON by
`l6/mkbib.py`. Identity was accepted when first author, title, container, year and volume matched
the citation that led to the record: a reference list read by L6 (Thomas 2024, Mendis 2024,
Hájek 2026, Dr. Probe, muSTEM, Voss 1980, Minami 2008, Horio 2022, Zheng 2026, Heacock 2021) or
the task's own citation. Three records came from Crossref searches with no prior citation
(Lehmpfuhl and Dowell 1986, Hayakawa and Aizawa 1982, Colella and Menadue 1972). For those,
identity is the Crossref record itself.

Not accepted:
* 10.15302/frontphys.2026.114201: the Crossref record has no authors, so it cannot be matched and
  Zheng 2026 is carried as arXiv only.
* 10.1016/j.ultramic.2017.01.011: this is a "Publisher's note" (vol. 177, pp. 1-13, no authors),
  not the Wu and Spiecker article (10.1016/j.ultramic.2017.03.029).

Osakabe et al. 1980 is already [P14] in `docs/references.bib` and is not duplicated. No key of
`L6_new_refs.bib` collides with `docs/references.bib`. No personal data was sent to any service:
Crossref without mailto; OpenAlex, Europe PMC, arXiv, J-STAGE, Edmond and er-c.org anonymously.

## 7. Recommendation (the orchestrator decides)

### 7.1 A7 (frozen-phonon rms displacement)

Adopt **u = 0.0777 A per axis (B = 0.4761 +- 0.0017 A^2 at 295.5 K)**, Heacock et al. 2021, as
SECTION_READ from arXiv:2103.05428v3 p. 6 (label on the paper's parameter:
SECTION_READ; value in the engine: sourced parameter at an assumed specimen temperature).

Why:
* It is a measurement with a stated uncertainty, in an open source, read with a locator. It uses
  the same per-axis convention as the engine (`rng.normal(0, u)` per coordinate; <u^2> = B/(8 pi^2),
  p. 3).
* The lattice-dynamical alternative (0.4725(17) A^2 at 295.5 K, u = 0.0774 A) differs by 0.8 % in B.
  That difference is negligible for the phase of a step between identical terraces. It changes the
  (008) Debye-Waller amplitude factor by 0.2 % (0.7739 against 0.7724).
* A7's 0.076 A is 4.2 % low in B. That changes the (008) Debye-Waller amplitude factor from 0.7808
  to 0.7724 (-1.1 %) and V0'(TDS) by 2.6 % (section 1.5). The effect is small but it is removable.

Conditions:
* The specimen temperature under the beam is an unstated input. dB/dT = 0.0014 A^2/K means 10 K
  moves B by 3 %. Record it as a PROJECT_INPUT (suggested new item) or an ASSUMPTION (295 K).
* The Einstein model misses phonon correlations (Hájek and Rusz 2026 find about 1e-3 I0
  differences for light diamond in transmission). This is an engine-model limitation, not a
  parameter problem.

### 7.2 PROJECT_INPUT item 21 (absorptive potential)

1. **With explicit frozen phonons (the production path): add no TDS absorptive potential.** The
   ensemble already depletes the coherent (sideband) wave by TDS (Hájek and Rusz p. 2; Dr. Probe
   preprint p. 9; muSTEM sec. 3.8). Adding Bird-King/Weickenmeier-Kohl/Peng TDS absorption on top
   double-counts it.
2. **Add only the electronic (plasmon plus single-electron) absorption, as a spatially uniform
   imaginary potential inside the crystal, not as V' = r V(r).** Candidate value: V0'(el) = 0.65 V
   from the Si plasmon mean free path 1050 A at 200 kV (Mendis 2019, measured by EELS, as stated
   by Mendis 2024). Upper variant: 0.83 V from the calculated total inelastic mean free path of
   830 A. The label stays UNVERIFIED for the 1050 A until Mendis 2019 is read (upload 1).
   * Reason for uniform: plasmon scattering is delocalised (theta_E = 0.04 mrad). A proportional
     r = 0.047 would put the same fraction on every Fourier coefficient. At (008) that is a ratio of
     0.047, about as large as the TDS ratio 0.053 that the phonons already produce, which would
     nearly double the anomalous absorption of the working reflection.
   * Engine consequence (inference from the code, `potentials.py` lines 289-311): the only
     physical model is `V*(1 + i*ratio)`. A uniform term needs a new model, for example a step
     profile like `absorber_profile_V` applied inside the crystal region, with its own evidence
     label. The mean of the TEST_ONLY r = 0.05 (0.695 V) is already close to 0.65 V, so H2's
     r = 0.05 run-in lengths are of the right order for the mean attenuation. The
     g-distribution is wrong.
3. **Static-lattice runs (no frozen phonons)**, if kept for speed: use a Debye-Waller-smeared real
   potential (B from 7.1) plus the TDS absorptive factor of Thomas et al. 2024 (Bird-King, open
   code, 200 keV) plus the uniform electronic term. The engine smears nothing today (no Debye-Waller
   code found), so this is an engine change. Results: f'/f from 0.0064 (g = 0) to 0.053 (008);
   V0'(TDS) = 0.089 V.
4. **Uncertainty to carry:** the measured anomalous absorption of Si (111) scatters by a factor of
   about 3 across sources once scaled to one energy: Voss 1980 0.0061 at 100 keV, TDS theory
   0.0139 at 100 keV, Ni 2026 0.0167-0.0182 at 200 kV. Treat any g-dependent V'_g as uncertain at
   the factor-2 level. Run the working condition at two absorption settings.
5. **Surface-plasmon loss at grazing incidence is not an imaginary bulk potential.** It is the
   largest absorption-like effect identified here: about 0.7 excitations per reflection at
   16 mrad if the 10 keV correction holds at 200 keV. That would reduce the coherent amplitude by
   about exp(-0.35) = 0.70 and add incoherent background. Keep it out of item 21. Record it as a
   separate optics/coherence factor with ASSUMPTION label, and request an energy-filtered REM
   measurement or a 200 keV source (uploads 7-8).

### 7.3 PROJECT_INPUT item 20 (mean inner potential)

* For the geometric engine and the angle computation, the best-sourced measured value found is
  **12.48 +- 0.22 V (Wu and Spiecker 2017)**. It is at abstract level only
  (METADATA_VERIFIED +ABSTRACT(PubMed)). Its conditions (specimen, surface, oxide, energy) must be
  read in the body (upload 2) before it replaces B1. It agrees with the DFT slab value 12.53 V (L5)
  and with the holography range of about 11.5-12.5 V (Zheng's secondary statement). The RHEED
  working value for Si is 12 V (Horio 2014, 2022; Moon 1972).
* Until the body is read, B1 (12.0 V) stays an ASSUMPTION. The sensitivity statement of B1 already
  covers a 0.5 V change: -0.17 rad at (4,-4,4), and about 0.5 % of a height at (0,0,8) (1.07 %/V)
  if the angle is computed.
* Multislice runs keep B32 (the engine's 13.903 V for internal consistency). That is a model
  systematic of 1.4-1.9 V against the bonded and measured values (12.0-12.53 V). For an ion-milled, oxidised Si(001)
  surface the rocking-curve calibration of the real sample (item 9) remains the decisive route.

## 8. Uploads needed from Ali (priority order)

| # | item | why | exact locator |
|---|---|---|---|
| 1 | Mendis, Ultramicroscopy 206 (2019) 112816, doi:10.1016/j.ultramic.2019.112816, **and** corrigendum Ultramicroscopy 212 (2020) 112957, doi:10.1016/j.ultramic.2020.112957 | source of the measured Si plasmon mean free path at 200 kV (1050 A), the only number behind the electronic absorption of 7.2; the corrigendum may change it | whole paper; the EELS mean-free-path measurement section and its table/figure. A browser download of the Durham accepted manuscript (durham-repository.worktribe.com/output/1297319) may work |
| 2 | Wu and Spiecker, Ultramicroscopy 176 (2017) 233-245, doi:10.1016/j.ultramic.2017.03.029 | measured Si MIP 12.48 +- 0.22 V: specimen preparation, oxide, beam energy, error budget | methods and results sections, table of MIP values |
| 3 | Kruse et al., Ultramicroscopy 106 (2006) 105-113, doi:10.1016/j.ultramic.2005.06.057 (already upload 11 of the reading plan) | measured (holography) and DFT Si MIP with uncertainty; the HF IAM 13.91 V | results table for Si |
| 4 | Gajdardziska-Josifovska et al., Ultramicroscopy 50 (1993) 285-299, doi:10.1016/0304-3991(93)90197-6 | settle the 9.26 +- 0.08 V attribution (Zheng 2026) and any Si value | the results table |
| 5 | Lehmpfuhl and Dowell, Acta Cryst. A 42 (1986) 569-577, doi:10.1107/s0108767386098720 | the best lead for a high-energy Si(111) rocking-curve benchmark; beam energy | experimental section, figures of CB-RHEED discs |
| 6 | Peng, Ren, Dudarev, Whelan, Acta Cryst. A 52 (1996) 456-470, doi:10.1107/s010876739600089x (and A 52 (1996) 257-276, doi:10.1107/s0108767395014371) | tabulated Si B(T) and absorptive factors; cross-check of the Thomas/Bird-King numbers of 1.5 | the Si rows of the tables; the voltage stated for the absorptive factors |
| 7 | Z. L. Wang, Reflection Electron Microscopy and Spectroscopy for Surface Analysis (CUP 1996; ZLWANG96), chapters on inelastic scattering/valence loss in RHEED and REM | surface- and bulk-plasmon excitation in REM at 100-200 keV (item 7.2.5) | the chapter(s) on inelastic excitation in reflection; Crossref lists the RHEED chapter as pp. 31-59 (doi:10.1017/cbo9780511525254.004) |
| 8 | Peng, Dudarev, Whelan, High-Energy Electron Diffraction and Microscopy (B08): pp. 228-263 and 264-310 (diffuse and inelastic scattering), pp. 454-469 (temperature-dependent Debye-Waller factors), with pp. 117-185 and 427-453 already on the plan | RHEED optical potential, TDS/inelastic absorption in reflection, Si B(T) tables | Crossref chapter DOIs 10.1093/oso/9780198500742.003.0007, .0008, .0014 |
| 9 | Radi, Acta Cryst. A 26 (1970) 41-56, doi:10.1107/s0567739470000050 | the separate electronic and phonon absorption coefficients for Si (100 keV, 293 K), to split 7.2 | the Si row of the tables |
| 10 | Dudarev, Peng, Whelan, Surf. Sci. 330 (1995) 86-100, doi:10.1016/0039-6028(95)00464-5 | optical potential for RHEED calculations | whole paper |
| 11 | Menadue, Acta Cryst. A 28 (1972) 1-11 and Colella and Menadue, ibid. 16-22 | the measured Si(111) 40 keV specular intensities behind Moon's Fig. 1 | data tables/figures |
| 12 | Ichimiya, Jpn. J. Appl. Phys. 24 (1985) 1579, doi:10.1143/jjap.24.1579; Horio and Ichimiya, Surf. Sci. 133 (1983) 393, doi:10.1016/0039-6028(83)90009-2 | the RHEED imaginary-potential formula and the origin of the RHEED V0 = 12 V for Si | whole papers (short) |
| 13 | Flensburg and Stewart, Phys. Rev. B 60 (1999) 284, doi:10.1103/physrevb.60.284 | body of the BvK B; low priority (Heacock covers the number) | results section |

New PROJECT_INPUT suggested (orchestrator's decision): the specimen temperature during holography
(A7 depends on it: 0.0014 A^2/K), and, if available, an energy-filtered REM or EELS measurement of
the specular beam's zero-loss fraction at the working angle (for 7.2.5).

## 9. Closing log

- 22:55 UTC: sections 5-8 written. OpenAlex's anonymous daily budget was exhausted at about
  22:45 UTC (HTTP error "Rate limit exceeded", resets at midnight UTC), so no further OpenAlex
  queries were made after that. Every OA verdict above was taken before then or from the host
  itself.
- Nothing in `docs/` other than this report and `L6_new_refs.bib` was written. No summary
  document, no other agent's report, no code and no configuration was edited. Nothing committed
  or pushed.
