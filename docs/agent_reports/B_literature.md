# B — Literature review: reflection electron holography, REM/RHEED simulation,
# dark-field holography, reflection-mode ptychography

Prepared: 2026-09-21
For: Si-surface reflection-mode dark-field electron holography paper + simulation repository
Companion file: `references.bib` (same directory)

---

## 0. READ THIS FIRST — ACCESS CONDITIONS OF THIS REVIEW

**This session had essentially no access to the scholarly literature.** The organisation's
egress proxy refused HTTPS CONNECT to every publisher, aggregator and metadata host I
attempted. This is not a transient failure and I did not route around it (the proxy README
explicitly forbids that).

Hosts confirmed **BLOCKED** (403 from the egress gateway, verified individually, each
attempted at least once and the important ones twice):

    api.crossref.org, search.crossref.org, api.openalex.org, openalex.org,
    api.semanticscholar.org, www.semanticscholar.org, pdfs.semanticscholar.org,
    doi.org, dx.doi.org, arxiv.org, export.arxiv.org,
    pmc.ncbi.nlm.nih.gov, www.ncbi.nlm.nih.gov, pubmed.ncbi.nlm.nih.gov, europepmc.org,
    journals.aps.org, link.aps.org, iopscience.iop.org, link.springer.com,
    www.sciencedirect.com, onlinelibrary.wiley.com,
    analyticalsciencejournals.onlinelibrary.wiley.com, academic.oup.com,
    www.cambridge.org, assets.cambridge.org, global.oup.com, journals.iucr.org,
    www.nature.com, pubs.aip.org, zenodo.org, www.osti.gov, ui.adsabs.harvard.edu,
    image-ppubs.uspto.gov, patents.google.com, www.researchgate.net, www.academia.edu,
    en.wikipedia.org, ouci.dntb.gov.ua, www.numis.northwestern.edu,
    www.jstage.jst.go.jp, www-surface.phys.s.u-tokyo.ac.jp, www.hitachi.com,
    mrfitzpa.github.io, scholar.archive.org, core.ac.uk, www.jsap.or.jp

Hosts **REACHABLE**: `github.com`, `raw.githubusercontent.com`, and the `WebSearch` tool.

### Consequences (non-negotiable honesty statement)

1. **No journal article, book chapter, thesis or patent was read in full or in part in this
   session.** There is therefore **no `SECTION_READ` evidence for any item of the
   literature** below. The instruction file's machine-readable verification route
   (Crossref / Semantic Scholar / OpenAlex / PMC) was unavailable.
2. The **only documents actually read** are five GitHub `README` files
   (`sim-trhepd-rheed`, `prismatique`, `prismatic`, `abTEM`, `py_multislice`) fetched from
   `raw.githubusercontent.com`. Those, and only those, carry `SECTION_READ`.
3. Everything else is built from the **WebSearch index**: literal result *titles* and
   *URLs* (which frequently embed the DOI), plus abstract-level text surfaced by the search
   tool's summariser.
4. **The search summariser demonstrably conflates sources.** It twice attributed the
   π / 0.9π monatomic-step phase shifts on Au(111)/Pt(111) — which belong to
   Banzhof, Herrmann & Lichte's paper — to Osakabe's 1988 JJAP paper, and once presented
   Peng & Cowley's 1988 *Surface Science* abstract as if it were their 1986 *Acta Cryst A*
   abstract. **I have corrected both and flagged them.** Treat every abstract-level
   statement below as second-hand until the PDF is opened.

### Evidence labels used here

Policy labels from the instruction file (§1.4), with a mandatory *route* qualifier:

| Label | Meaning here |
|---|---|
| `METADATA_VERIFIED(index)` | Title + authors + journal/volume/pages and, where shown, a DOI-bearing publisher URL were seen in the search index and corroborated across ≥2 independently-phrased queries. **Not** Crossref-verified. |
| `METADATA_VERIFIED(index, single)` | As above but only one query returned it. Weaker. |
| `+ABSTRACT(index)` | Abstract-level text was surfaced by the search summariser. This is **weaker than** `SECTION_READ` and is **not** a substitute for it. |
| `SECTION_READ` | I actually read the document (GitHub READMEs only). |
| `DERIVED_HERE` | My own derivation/arithmetic from stated premises. Reproducible; not attributed to any source. |
| `ASSUMPTION` | A chosen parameter (e.g. Si mean inner potential) that must be sourced or measured. |
| `UNVERIFIED` | Provenance unresolved, or the claim rests on one summariser sentence. |
| `PROJECT_INPUT` | Asserted by the project instruction file, not re-verified here. |

**All DOIs quoted below were seen either embedded in a publisher URL returned by the search
index, or stated by the search summariser. None was checked against Crossref.** Where I
noticed that a DOI's only source was a summariser sentence rather than a URL, I wrote
`DOI UNVERIFIED`; treat summariser-level provenance as the default elsewhere. Three DOIs are
stronger than the rest because I read them verbatim in a file:
10.1016/j.cpc.2022.108371, 10.12688/openreseurope.13015.2 and 10.5281/zenodo.14757400
(plus 10.5281/zenodo.18296081), which appear in GitHub READMEs I fetched.
**No DOI in this report or in `references.bib` was constructed, guessed or pattern-completed
by me. Any DOI I could not source is simply absent.**

---

## 1. PRIMARY REFLECTION-HOLOGRAPHY PAPERS

### 1.1 [P01] Osakabe, Matsuda, Endo & Tonomura, *Jpn. J. Appl. Phys.* **27**, L1772–L1774 (1988)
"Observation of Atomic Steps by Reflection Electron Holography"
DOI 10.1143/JJAP.27.L1772 (`PROJECT_INPUT`; publisher page `iopscience.iop.org` blocked).

* Evidence: `METADATA_VERIFIED(index)` for title/authors/journal/volume/year.
  Page numbers: the instruction file gives L1772–L1774; the search index repeatedly
  reported "27, 1772–1774" without the Letters `L` prefix. I kept the `L` form (JJAP
  Part-2 Letters convention) but this is `UNVERIFIED` at the digit level.
* **The abstract could not be obtained.** Five independently-phrased queries returned only
  the citation string. Every attempt to retrieve its content returned either nothing or
  text that actually belongs to [P09] (Banzhof/Herrmann/Lichte) — see §0.4.
* **Therefore: the surface studied, the electron energy, the reflection used, the glancing
  angle, the reference-wave arrangement, the measured phase values and the stated
  limitations of [P01] are ALL UNKNOWN to this review.** Do not cite any of these from me.
* What *is* supportable about the wider Osakabe reflection-holography programme comes from
  [P08] and the Hitachi patent — see §1.4, §1.5 and §9.

### 1.2 [P02] Osakabe, Endo, Matsuda, Tonomura & Fukuhara, *Phys. Rev. Lett.* **62**, 2969–2972 (1989)
"Observation of surface undulation due to single-atomic shear of a dislocation by
reflection-electron holography". DOI 10.1103/PhysRevLett.62.2969.

* Evidence: `METADATA_VERIFIED(index) +ABSTRACT(index)`. The publisher URL
  `journals.aps.org/prl/abstract/10.1103/PhysRevLett.62.2969` was returned with this exact
  title; authors and the Hitachi Advanced Research Laboratory affiliation were returned by
  two independent queries; issue date reported as 19 June 1989.
* Abstract-level content obtained (consistent across two queries, `+ABSTRACT(index)`):
  - system: a **screw dislocation emerging on a cleaved GaAs(110) surface**;
  - observable: a **spirally deformed surface** due to a single-atomic shear;
  - **precision ~0.01 Å** on the surface height, obtained "by interferometrically
    measuring the phase of the reflected electrons";
  - for an *obliquely* emerging dislocation the surface around the core is deformed
    **asymmetrically rather than uniformly**, explained by **surface stress relaxation**.
* **Not obtained:** microscope/energy, which Bragg reflection, glancing angle, biprism
  position, reference-wave trajectory, the explicit phase↔height equation and its sign
  convention, and the stated limitations.
* Relevance to Ali: this is a *cleaved* (110) surface of a diamond/zincblende crystal —
  the closest published analogue to the repository's cleaved-Si benchmark. Note the
  instruction file's warning: GaAs parameters must not be transferred to Si.

### 1.3 [P02E] Erratum, *Phys. Rev. Lett.* **63**, 584 (1989), DOI 10.1103/PhysRevLett.63.584.3
* Evidence: `METADATA_VERIFIED(index, single)` — existence corroborated only by the PRL
  volume-63 issue-5 table-of-contents page appearing in results.
* **What the erratum corrects could not be determined.** No accessible source states it.
  `UNVERIFIED`. **Any quantitative number taken from [P02] must be re-checked against this
  erratum before publication.**

### 1.4 [P08] Osakabe, *J. Electron Microsc. Tech. / Microsc. Res. Tech.* **20**(4), 457–462 (1992) — NEW, IMPORTANT
"Observation of surfaces by reflection electron holography". Single author: N. Osakabe.
DOI 10.1002/jemt.1070200415; PMID 1498359.

* Evidence: `METADATA_VERIFIED(index) +ABSTRACT(index)`. Title+DOI seen in the Wiley URL;
  the PubMed record `pubmed.ncbi.nlm.nih.gov/1498359/` with this title was returned by three
  independent queries; pages 457–462 and the 1992 date returned twice.
* Abstract-level content (returned near-verbatim and consistently by three queries):
  - "Reflection electron holography is a method to observe **sub-Å surface morphology**."
  - "**Phase shift of a Bragg-reflected electron wave** was measured by means of
    holographic interferometry using an electron microscope equipped with a **field
    emission electron gun and an electron biprism**."
  - "A **short wavelength of high energy electrons** is the essential key to the high
    vertical sensitivity of this method, since **geometrical path differences produced by
    the surface topography are measured in units of wavelengths**."
  - "**Phase shift at a monoatomic step** and the **displacement field around a dislocation
    emerging on the surface** were observed."
* This is the single most useful accessible statement of Osakabe's method: the object wave
  is a **Bragg-reflected** wave (not merely "the specular beam" in a vague sense), and the
  physical basis is explicitly stated as a **geometrical path difference measured in units
  of the wavelength** — i.e. the kinematic relation derived in §9.2, not a dynamical one.
* **This paper is a better citation target than [P01] for "what Osakabe's reflection
  holography measures", and it is the review-level summary by Osakabe himself.**
* Not obtained: surface(s) used, energy, glancing angle, reference-wave geometry, figures.

### 1.5 [PAT01] US 4,998,788 A — "Reflection electron holography apparatus" — NEW
Inventors reported: **N. Osakabe, J. Endo, A. Tonomura, M. Tomita, T. Furutsu**;
assignee **Hitachi, Ltd.**; US application 07/462,769; European family member EP 0 378 237 B1.

* Evidence: `METADATA_VERIFIED(index, single)` for inventors/assignee/application number;
  `UNVERIFIED` for the grant/priority dates (the summariser reported "filed 9 May 1991,
  granted 9 March 1993", which is inconsistent with a US patent number in the 4,998,xxx
  series — do not use those dates). Both `image-ppubs.uspto.gov` and `patents.google.com`
  are blocked, so the patent itself was not read.
* Two abstract/description-level statements surfaced (each `UNVERIFIED`, from the search
  summariser; the second may come from the patent or from a review, provenance unresolved):
  - "…a fraction of an electron wave from an electron source illuminates a specimen and is
    caused to be **reflected** thereat, while the **remaining electron wave does not
    illuminate the specimen but passes aside**, and the reflected electron wave and the
    electron wave not illuminating are **superimposed** one upon the other."
  - "A hologram through interference between the **reflected wave and direct wave** can be
    obtained by properly controlling the **focal distance and electron biprism potential**
    so as to make the **intersecting angle small enough to give a recordable fringe
    interval**"; a **single-stage biprism** is used, "advantageous in that it does not
    require angle adjustment of biprism wire directions."
* **If these statements are accurate, the Hitachi reference wave is a VACUUM ("direct")
  wave passing beside the specimen, not a second reflected beam.** This is the single most
  important design fact for Ali's forward model and it is currently only patent-level and
  second-hand. §9.3 shows that such a reference is *not* automatically parallel to the
  object wave, which is consistent with the patent's emphasis on making the "intersecting
  angle small enough".

### 1.6 [P03] Banzhof & Herrmann, *Ultramicroscopy* **48**, 475–481 (1993) — "Reflection electron holography"
* Evidence: `METADATA_VERIFIED(index, single)`. Citation string (authors, title, journal,
  volume 48, page 475, 1993) and DOI 10.1016/0304-3991(93)90123-F returned by the
  summariser; the ScienceDirect PII `030439919390123F` in the instruction file is
  consistent with that DOI. **Abstract not obtained.** No technical content available.
* Do **not** attribute any equation or number to [P03] from this review.

### 1.7 [P09] Banzhof, Herrmann & Lichte, *J. Electron Microsc. Tech.* **20**(4), 450–456 (1992) — NEW, QUANTITATIVE
"Reflection electron microscopy and interferometry of atomic steps on gold and platinum
single crystal surfaces". DOI 10.1002/jemt.1070200414.

* Evidence: `METADATA_VERIFIED(index) +ABSTRACT(index)` — title+DOI from the Wiley URL;
  author list and pages 450–456 returned by two independent queries.
* Abstract-level content (returned consistently by three queries):
  - **two-beam interference produced with an electrostatic biprism inserted at the position
    of the selected-area diaphragm of a commercial electron microscope**;
  - purpose: "to determine the phase shifts induced by structures on single crystal
    surfaces";
  - **measured phase shifts: π on a monatomic step of (111)Au, and 0.9π on (111)Pt.**
* **These π / 0.9π values belong to THIS paper, not to Osakabe [P01].** The search
  summariser mis-attributed them twice. Flagged loudly because the mis-attribution is
  exactly the kind of error the project's source policy exists to prevent.
* Useful cross-check (`DERIVED_HERE`): d₁₁₁(Au)=a/√3=2.3547 Å (a=4.0782 Å),
  d₁₁₁(Pt)=2.2652 Å (a=3.9236 Å); ratio 0.962. The measured ratio 0.9π/π = 0.90. At fixed
  sinθ/λ the geometric relation Δφ ∝ h predicts 0.962. Agreement to ~6 % — consistent with
  the geometric picture of §9.2 but not a proof of it (the operating angles for the two
  metals were probably not identical, and dynamical phases were not excluded).
* Note the biprism position: **selected-area-diaphragm plane**, i.e. an *image-side*
  biprism in a conventional TEM, not a gun-side/condenser biprism.

### 1.8 Other Osakabe / Tonomura material located
| ID | Record | Evidence |
|---|---|---|
| [P14] | Osakabe, Tanishiro, Yagi & Honjo, *Surf. Sci.* **97**, 393–408 (1980), "Reflection electron microscopy of clean and gold deposited (111) silicon surfaces" | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Establishes Osakabe's REM training in the Yagi/Honjo school on **Si(111)** steps: reports smooth atomic steps that change shape continually in the high-temperature (1×1) phase and transform into **zig-zag steps** in the (7×7) phase. |
| [P15] | Tonomura, *Rev. Mod. Phys.* **59**, 639–669 (1987), "Applications of electron holography" | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Review. |
| [P16] | Tonomura, *Adv. Phys.* **41**(1), 59–103 (1992), "Electron-holographic interference microscopy", DOI 10.1080/00018739200101473 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Abstract explicitly covers "the phase distribution of an electron beam **transmitted through or reflected from** an object **to within 1/100 of the electron wavelength**". That 1/100-fringe figure is the key sensitivity claim for the Hitachi programme (see §9.5). |
| [P27] | Cowley, *Ultramicroscopy* **41**, 335–348 (1992), "Twenty forms of electron holography", DOI 10.1016/0304-3991(92)90213-4 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Taxonomy: for every TEM mode a STEM equivalent, for every in-line mode an off-axis mode, and **bright-field and dark-field variants of each**. Cite as the origin of the systematic "dark-field holography" classification. |
| [P28] | Cowley, *Surf. Sci.* **298**, 336–344 (1993), "Electron holography and holographic diffraction for surface studies" | `METADATA_VERIFIED(index, single) +ABSTRACT(index)`. |

* **[B09] (Völkl/Allard/Joy 1999): no reflection-holography chapter and no Osakabe chapter
  was found.** The retrieved table of contents (see §7) contains no chapter on reflection
  geometry. Chapter 13, *"Electron Holography using Diffracted Electron Beams (DBH)"*, is
  the relevant one for **dark-field/diffracted-beam** holography. Chapter authorship and
  page range for ch. 13 could **not** be obtained.
* **1995 Elsevier "Electron Holography" workshop proceedings** (Tonomura, Allard, Pozzi,
  Joy & Ono, eds.; Int. Workshop on Electron Holography, Knoxville TN, 29–31 Aug 1994):
  existence `METADATA_VERIFIED(index, single)`. The summariser asserted an Osakabe
  reflection-holography contribution in it, but the text it produced was the [P02] PRL
  abstract, so **I treat "there is an Osakabe chapter in that volume" as `UNVERIFIED`.**
* **[B10] Tonomura, *Electron Holography*, 2nd ed.**: chapters located by DOI suffix are
  ch.1 *Introduction*, ch.2 *Principles of Holography*, ch.4 *Historical Development of
  Electron Holography*, ch.6 *Aharonov–Bohm Effect…*, ch.7 ***Electron-Holographic
  Interferometry***, ch.8 *High-Resolution Microscopy*. Chapter 7 is the most likely home
  of the surface/reflection material, but **I have no evidence that it contains it**.

---

## 2. [P07] HARADA, *Microscopy* **70**(1), 3–16 (2021) — **NOT OBTAINED**

"Interference and interferometry in electron holography", DOI 10.1093/jmicro/dfaa033;
PMID 32589205; open access at PMC7850541.

**The task designated this as the most reliable accessible secondary source and asked for a
full read. I could not obtain it.** `pmc.ncbi.nlm.nih.gov`, `academic.oup.com`,
`pdfs.semanticscholar.org` and `www.researchgate.net` are all blocked. Two fetch attempts
to PMC, one to OUP.

What the search index yielded (`METADATA_VERIFIED(index) +ABSTRACT(index)`):
* It is the introductory review of the holography section of a *Microscopy* special issue.
* Scope listed: general principle of holography and interferometry for phase measurement in
  optical holography; phenomena peculiar to electron waves; principles of electromagnetic
  field detection; **the interference optical systems of electron waves and their
  features**; methods of reconstruction of phase from electron holograms.
* Forward-looking statement: "**double biprism holography and split illumination
  holography are expected to be the mainstream of interference microscopy in the near
  future**", with double-biprism microscopes now common worldwide.

**Nothing about Osakabe's experiments, reference-wave arrangements, figure numbers or
section locators from [P07] could be extracted.** This is the largest single gap in the
review. Ali (or anyone with normal network access) should open PMC7850541 directly; it is
free.

Substitute primary sources for the biprism-arrangement material that [P07] reviews:
[P47] Harada et al. 2004 (double biprism), [P45] Tanigaki et al. 2012 (split illumination),
[P46] Tanigaki et al. 2014 (advanced split illumination) — see §6.

---

## 3. REM / RHEED THEORY FOR A REFLECTION FORWARD MODEL

All entries `METADATA_VERIFIED(index)` unless stated. No full text read.

### 3.1 The two multislice families

| ID | Record | Slicing | Evidence / content obtained |
|---|---|---|---|
| [P17] | A. Ichimiya, "Many-beam calculation of reflection high energy electron diffraction (RHEED) intensities by the multi-slice method", *Jpn. J. Appl. Phys.* **22**, 176–180 (1983) | **parallel to the surface** | Citation string **read verbatim** in the `sim-trhepd-rheed` README (`SECTION_READ` of the README, i.e. a verified *secondary* citation by the field's own software authors). Method description (`+ABSTRACT(index)`): the crystal is sliced into thin slabs **parallel to the surface**, the potential in each slab is taken as constant along the surface normal, and intensities are built from **products of matrices from Bethe's dynamical theory** for each slab. |
| [P18] | L.-M. Peng & J. M. Cowley, "Dynamical diffraction calculations for RHEED and REM", *Acta Cryst.* **A42**, 545–552 (1986). DOI 10.1107/S0108767386098756 (`DOI UNVERIFIED`) | **perpendicular to the beam** (transmission-type) | `METADATA_VERIFIED(index)` for volume/pages (corroborated twice, and by the Acta Cryst A42 part 6 (Nov 1986) issue TOC appearing in results). **Abstract not obtained** — the text the summariser first offered was actually [P19]'s abstract. |
| [P19] | L.-M. Peng & J. M. Cowley, "A multislice approach to the RHEED and REM calculation", *Surf. Sci.* **199**(3), 609–622 (1988). DOI 10.1016/0039-6028(88)90925-9 (PII consistent) | **perpendicular to the beam** | `METADATA_VERIFIED(index) +ABSTRACT(index)`, abstract returned near-verbatim: *"A computing method for the **forward dynamical scattering calculations which has been successfully applied to the Bragg case** of high energy electron diffraction is described. This method is based on the **physical optics theory of dynamical diffraction of Cowley and Moodie** and is used for calculations of RHEED diffraction amplitudes and the REM image intensities for the extended surface of a perfect crystal and also for **a crystal surface with a defect**."* |

**[P19] is the single most directly relevant citation for "a transmission-style multislice
code used in reflection".** It states, at abstract level, that the Cowley–Moodie
forward-scattering multislice has been *successfully applied to the Bragg case* including a
defective surface. That is precisely the claim repository instruction §9.3 asks to be
assessed rather than assumed — and [P19] is the source to read before asserting it.

### 3.2 Bloch-wave treatments of the Bragg case (Ma & Marks; Peng & Gjønnes)

| ID | Record | Evidence / content |
|---|---|---|
| [P20] | Y. Ma & L. D. Marks, "Bloch-wave solution in the Bragg case", *Acta Cryst.* **A45** (1989). IUCr paper code S0108767388010888 | `METADATA_VERIFIED(index)` for title/authors/journal/volume. **Page range conflicting**: one query returned 174–182, another 182–187. `UNVERIFIED` — resolve before citing. Content (`+ABSTRACT(index)`): develops the Bloch-wave method for reflection diffraction (RHEED/REM); introduces the **current-flow concept** that both explains reflection diffraction and **determines which Bloch waves are allowed**; results for GaAs near [010]; discusses **resonance diffraction and its relation to internal/external reflection, variations in boundary conditions, splitting of diffraction spots due to stepped surfaces, and the reflection equivalent of thickness fringes**. |
| [P21] | Y. Ma & L. D. Marks, "Bloch waves and multislice in transmission and reflection diffraction", *Acta Cryst.* **A46**, 11–32 (1990) | `METADATA_VERIFIED(index)`. Content (`+ABSTRACT(index)`): investigates **consistency between the Bloch-wave and multislice approaches in both transmission and reflection, with emphasis on reflection**. This is the correct citation for "is my transmission multislice compatible with the reflection Bloch-wave answer?" |
| [P22] | Y. Ma & L. D. Marks, "Surface phenomena in RHEED and REM", *Acta Cryst.* **A46**, 594–606 (1990) | `METADATA_VERIFIED(index)` — the volume/page string appears literally in a PDF title returned by the index. |
| [P13] | Y. Ma & L. D. Marks, "Developments in the dynamical theory of high energy electron reflection", *Microsc. Res. Tech.* **20**(4), 371–389 (1992). DOI 10.1002/jemt.1070200408; PMID 1498352 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Review. Notable statement: at that date "**a stationary dynamical solution for an arbitrary surface for HEER has not been obtained yet**". |
| [P12] | L.-M. Peng, K. Gjønnes & J. Gjønnes, "Bloch wave treatment of symmetry and multiple beam cases in RHEED and REM", *Microsc. Res. Tech.* **20**(4), 360–370 (1992). DOI 10.1002/jemt.1070200407; PMID 1498351 | `METADATA_VERIFIED(index) +ABSTRACT(index)`: derives Bloch-wave equations for multiple-beam RHEED from the integral equation using **forward- and back-scattering Green-function operators**. |
| [P29] | T. C. Zhao, H. C. Poon & S. Y. Tong, *Phys. Rev. B* **38**, 1172 (1988) | `METADATA_VERIFIED(index, single)`. Content (`+ABSTRACT(index)`): an **invariant-embedding R-matrix** scheme for RHEED rocking curves; Ag(001); demonstrates the **importance of evanescent beams**. Exact title `UNVERIFIED` (the summariser gave "Accurate Dynamical Theory of RHEED Rocking-curve Intensity Spectra", which I could not corroborate). |

### 3.3 REM imaging, steps and reviews

| ID | Record | Evidence / content |
|---|---|---|
| [P23] | K. Yagi, "Reflection electron microscopy", *J. Appl. Cryst.* **20**(3), 147–160 (1987). DOI 10.1107/S0021889887086916 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. UHV-REM characterises **monolayer-level surface structure: steps, reconstructed domains and their boundaries**, and dynamic processes (phase transitions, adsorption, oxidation, sublimation, sputter-anneal). |
| [P10] | T. Hsu, "Technique of reflection electron microscopy", *Microsc. Res. Tech.* **20**(4), 318–332 (1992). DOI 10.1002/jemt.1070200403 | `METADATA_VERIFIED(index)`. |
| [P11] | K. Yagi, A. Yamanaka & I. Homma, "Recent studies of surface dynamic processes by reflection electron microscopy", *Microsc. Res. Tech.* **20**(4), 333–340 (1992). DOI 10.1002/jemt.1070200404 | `METADATA_VERIFIED(index)`. |
| [P24] | N. Uchida, W. Jäger & G. Lehmpfuhl, "Direct imaging of atomic steps in reflection electron microscopy", *Ultramicroscopy* **13**, 325–328 (1984) | `METADATA_VERIFIED(index, single)`. |
| [P25] | N. Uchida & G. Lehmpfuhl, "Observation of double contours of monoatomic steps on single crystal surfaces in reflection electron microscopy", *Ultramicroscopy* **23**, 53–60 (1987) | `METADATA_VERIFIED(index, single)`. **The "double-contour" step contrast is the canonical REM step-imaging artefact your simulation must reproduce or explain.** |
| [P26] | N. Yao & J. M. Cowley, "Electron diffraction conditions and surface imaging in reflection electron microscopy", *Ultramicroscopy* **33**, 237–254 (1990). PII 0304-3991(90)90041-J | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Identifies **two distinct resonance conditions** enhancing the specular beam: **Bragg–channelling** and **Bragg–Bragg**; the surface image from the **Bragg–Bragg** condition gives the best topographic contrast; the anomalous **double-contour contrast of a single-atom-height step is closely associated with the Bragg–Bragg condition**; total reflectivity does not change much with diffraction condition, so *improved topographic contrast is not simply proportional to specular intensity*. |

### 3.4 Books used as reflection-theory references

* **[B07] Ichimiya & Cohen, *Reflection High-Energy Electron Diffraction*, CUP.**
  Chapter list obtained from the publisher's Cambridge Core chapter pages surfaced by the
  index (`METADATA_VERIFIED(index, single)`; `assets.cambridge.org` frontmatter blocked):
  Preface; Introduction; Historical survey; Instrumentation; Wave properties of electrons;
  The diffraction conditions; Geometrical features of the patterns; Kikuchi and resonance
  patterns; Real diffraction patterns; Electron scattering by atoms; Kinematic electron
  diffraction; Fourier components of the crystal potential; **Dynamical theory: transfer
  matrix method**; **Dynamical theory: embedded R-matrix method**; **Dynamical theory:
  integral method** (this last one is confirmed as chapter 14 by its Cambridge Core URL);
  Structural analysis of crystal surfaces; Inelastic scattering in a crystal; Weakly
  disordered surfaces; Strongly disordered surfaces; RHEED intensity oscillations;
  appendices (Fourier representations, Green's function, Kirchhoff's diffraction theory, a
  simpler eigenvalue problem, Waller–Hartree equation, optimisation of dynamical
  calculation).
  → **Read the three "Dynamical theory" chapters plus "The diffraction conditions" before
  implementing refraction, boundary conditions or the specular rod.**

* **[B08] Peng, Dudarev & Whelan, *High-Energy Electron Diffraction and Microscopy*, OUP.**
  Chapter list obtained from Oxford Academic chapter pages (`METADATA_VERIFIED(index)`;
  one chapter URL, `academic.oup.com/book/54675/chapter/422641330`, carries the literal
  title *"Dynamical Theory III. Reflection High-Energy Electron Diffraction"*):
  1 Basic concepts; 2 Kinematic theory; 3 Dynamical theory I — general theory;
  4 Dynamical theory II — THEED; **5 Dynamical theory III — Reflection high-energy electron
  diffraction**; 6 Resonance effects in diffraction; 7–8 Diffuse and inelastic scattering;
  9 Crystal and diffraction symmetry; 10 Perturbation methods and tensor theory;
  11 Digital electron microscopy; 12 Image formation and retrieval of the wave function;
  13 The atomic scattering factor and the optical potential; 14 Debye–Waller factors;
  appendices including **a FORTRAN listing of RHEED routines** and a parameterisation of the
  atomic scattering factor.
  → Chapters 5, 6, 13 and the RHEED-routine appendix are the ones to read.
  Note the publication-year discrepancy: the instruction file says OUP 2004; an IUCr book
  review returned by the index says "Pp. 544. Oxford University Press, 2003.
  ISBN 0-19-850074-2". `UNVERIFIED`; resolve before citing a year.

* **Z. L. Wang, *Reflection Electron Microscopy and Spectroscopy for Surface Analysis*,
  Cambridge, 1996** — identity `METADATA_VERIFIED(index)` (Cambridge Core book page,
  ISBN 9780521482660 hardback / 9780521017954 paperback reissue).
  Only a structural statement could be obtained: it is "divided into three parts:
  **diffraction, imaging and spectroscopy**" and covers REM, RHEED and REELS
  (`+ABSTRACT(index)`). **The chapter list could not be retrieved**, so I cannot name the
  step-contrast or dynamical-theory chapters. `UNVERIFIED` at chapter level.

---

## 4. DARK-FIELD ELECTRON HOLOGRAPHY (TRANSMISSION) — THE METHODOLOGICAL ANALOGUE

| ID | Record | Evidence / content |
|---|---|---|
| [P30] | M. J. Hÿtch, F. Houdellier, F. Hüe & E. Snoeck, "Nanoscale holographic interferometry for strain measurements in electronic devices", *Nature* **453**(7198), 1086–1089 (2008). DOI 10.1038/nature07049 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Abstract: combines **moiré interferometry and electron holography** to reach high spatial resolution *and* precision over a large field of view; motivated by strained-silicon transistors. Note: the correct title uses "**strain measurements**" (plural), not "strain measurement". |
| [P31] | M. J. Hÿtch, F. Houdellier, F. Hüe & E. Snoeck, "Dark-field electron holography for the measurement of geometric phase", *Ultramicroscopy* **111**(8), 1328–1337 (2011). PII S0304399111001586 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Key statement obtained twice: it "places **geometric phase within a unified theoretical framework** for phase measurements by electron holography, with the **total phase described as a sum of four contributions: crystalline, electrostatic, magnetic and geometric**." |
| [P32] | A. Lubk, E. Javon, N. Cherkashin, S. Reboh, C. Gatel & M. Hÿtch, "Dynamic scattering theory for dark-field electron holography of 3D strain fields", *Ultramicroscopy* **136**, 42–49 (2014) | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Perturbative **two-beam dynamical theory** giving **analytic linear projection rules** for 3D strain fields; the weighting integral depends analytically on **diffraction order, excitation error and specimen thickness**. |
| [P33] | L. Meißner, T. Niermann, D. Berger & M. Lehmann, "Dynamical diffraction effects on the geometric phase of inhomogeneous strain fields", *Ultramicroscopy* **207**, 112844 (2019) | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Experiment + theory on InGaAs/GaAs; phase and amplitude of the diffracted beam measured by DFEH; calculations by numerical propagation with the **Darwin–Howie–Whelan equations**; conclusion: "**a strong dependency on the excitation conditions is found showing that the interplay between dynamical effects and the strain field must be considered in the interpretation of the geometric phase**." |
| — | Additional located but unverified: "Dynamical effects in strain measurements by dark-field electron holography", *Ultramicroscopy* (2014), PII S0304399114001211; "Differential phase-contrast dark-field electron holography for strain mapping", *Ultramicroscopy* (2016), PII S0304399115300413, PMID 26476802; "Dynamical diffraction effects of inhomogeneous strain fields investigated by scanning CBED and dark-field electron holography", *Ultramicroscopy* (2025), PII S030439912500021X, PMID 40068240; "Four-wave dark-field electron holography for imaging strain fields"; commercial reconstruction plug-in **HoloDark for DigitalMicrograph** (HREM Research). | `METADATA_VERIFIED(index, single)` each. |

### The geometric-phase relation — status

* **I could not read [P31] and therefore cannot quote its equation, its equation number or
  its sign convention.** The widely used form is φ_g = −2π **g·u**, but *the sign as stated
  by Hÿtch et al. is `UNVERIFIED` here.* Do not put a sign in the paper on my authority.
* Conditions of validity that [P31]/[P32]/[P33] bear on (all abstract-level,
  `+ABSTRACT(index)`): the phase separates into crystalline + electrostatic + magnetic +
  geometric contributions [P31]; for a 3-D (non-rigid, depth-varying) displacement field the
  relation becomes a **weighted projection** depending on diffraction order, excitation
  error and thickness [P32]; and the excitation-condition dependence is **strong enough that
  dynamical effects must be included in the interpretation** [P33].
* **These are transmission results.** Two structural differences block direct transfer to
  reflection: (i) in transmission the object is a column through the foil and the column
  approximation projects **u** along the beam; in reflection there is no transmitted column —
  the reflected amplitude is generated within an extinction/absorption depth of a few nm
  below a *surface*, and the relevant "projection" is that shallow, complex-weighted depth
  average; (ii) the reflection amplitude R(θ) carries its own dynamical phase φ_R(θ) that
  varies rapidly near the surface resonances of [P26] — it cancels between two *identical*
  terraces but not between regions of different termination, reconstruction or strain.
  **The reflection analogue of φ_g must therefore be derived, not assumed.** §9 gives the
  kinematic starting point and the explicit list of terms that a derivation must keep.

---

## 5. REFLECTION-MODE PTYCHOGRAPHY

### 5.1 X-ray (mature; the transferable methodology)

| ID | Record | Evidence / content | Forward model |
|---|---|---|---|
| [P34] | S. Roy et al., "Lensless X-ray imaging in reflection geometry", *Nature Photonics* **5** (2011). DOI 10.1038/nphoton.2011.11 | `METADATA_VERIFIED(index) +ABSTRACT(index)`; **page numbers not obtained**. Lensless imaging in **Bragg and small-angle (reflection) scattering geometries**; demonstrated on a nanofabricated pseudorandom binary structure in **small-angle reflection**; works with extended objects, no sample-size restriction, no additional mask. | multiplicative/CDI-type |
| [P35] | P. Godard, G. Carbone, M. Allain, F. Mastropietro, G. Chen, L. Capello, A. Diaz, T. H. Metzger, J. Stangl & V. Chamard, "Three-dimensional high-resolution quantitative microscopy of extended crystals", *Nat. Commun.* **2**, 568 (2011). PMID 22127064 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Ptychography **in the Bragg geometry**; 3-D Bragg-peak intensity mapped and inverted with a **Bragg-adapted ptychographic phase-retrieval algorithm**. | multiplicative, Bragg-adapted |
| [P36] | C. Zhu, R. Harder, A. Diaz, V. Komanicky, A. Barbour, R. Xu, X. Huang, Y. Liu, M. S. Pierce, A. Menzel & H. You, "Ptychographic x-ray imaging of surfaces on crystal truncation rod", *Appl. Phys. Lett.* **106**(10), 101604 (2015). DOI 10.1063/1.4914927 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. **Ptychography used to image atomic step structures from coherent diffraction recorded along the crystal truncation rod**; proof of concept on **Pt(111)**; reconstructions show features consistent with surface steps; argued to extend to buried interfaces. **This is the closest published analogue of Ali's target measurement, in X-rays.** | CTR / kinematic-multiplicative |
| [P37] | S. O. Hruszkewycz, M. Allain, M. V. Holt, C. E. Murray, J. R. Holt, P. H. Fuoss & V. Chamard, "High-resolution three-dimensional structural microscopy by single-angle Bragg ptychography", *Nat. Mater.* **16**, 244–251 (2017). DOI 10.1038/nmat4798; PMID 27869823 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. 3-D Bragg projection ptychography (3DBPP): 3-D reconstruction from 2-D Bragg patterns at a **single incident angle**. | multiplicative + Bragg projection operator |
| [P38] | P. S. Jørgensen, L. Besley, A. M. Slyamov, A. Diaz, M. Guizar-Sicairos, M. Odstrčil, M. Holler, C. Silvestre, B. Chang, C. Detlefs & J. W. Andreasen, "Hard X-ray grazing-incidence ptychography: large field-of-view nanostructure imaging with ultra-high surface sensitivity", *Optica* **11**(2), 197–204 (2024); arXiv:2307.01735 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Combines **imaging + reflectometry + GISAXS**; high resolution transverse to the beam **and along the surface normal**. | multiplicative + reflection geometry correction |
| [P39] | P. Myint, A. Tripathi, M. J. Wojcik, J. Deng, M. J. Cherukara, N. Schwarz, S. Narayanan, J. Wang, M. Chu & Z. Jiang, "Three-dimensional hard X-ray ptychographic reflectometry imaging on extended mesoscopic surface structures", *APL Photonics* **9**(6), 066118 (2024). DOI 10.1063/5.0204240; arXiv:2402.06762 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Merges 2-D ptychography of extended objects with **X-ray reflectivity depth profiling**. | multiplicative + XRR depth model |
| [P40] | D. Guenzing, D. Y. Sasaki, A. S. Ditter, A. L. Levitan, E. M. Gullikson, S. Dhuey, A. Gashi, H. Ohldag, S. Roy, D. A. Shapiro, R. Comin & S. A. Morley, "Soft X-ray reflection ptychography", *Opt. Express* **34**(16), 30230 (2026). DOI 10.1364/OE.591755 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. **Reflection-geometry soft-X-ray ptychography as a robust imaging mode**; Siemens-star and barcode test patterns on a multilayer substrate; **~45 nm full-pitch resolution** by Fourier-ring correlation. Most recent item in this section. | multiplicative |
| [P41] | R. Wang, Q. Zhao, L. Loetgering et al., "Ptychography at all wavelengths", *Nat. Rev. Methods Primers* **5**, 68 (2025). DOI 10.1038/s43586-025-00438-3; PMID 41909173 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Current cross-wavelength Primer; cite as the review. | — |

**All of the X-ray reflection/Bragg ptychography above is, at abstract level, built on a
multiplicative (projection-approximation / kinematic) object model with a geometry-specific
projection or reflectivity operator. None of the abstracts obtained claims a dynamical
multiple-scattering forward model.** That matters: repository instruction §C03 warns that
"an algorithm derived for a multiplicative object is not automatically valid for dynamical
reflection scattering", and the X-ray literature does not resolve that for electrons,
because X-ray reflection from a surface is weak-scattering in a way that 100–300 keV
electrons at grazing incidence are not.

### 5.2 Electrons in reflection — essentially empty

* **I found no peer-reviewed electron reflection-mode ptychography or grazing-incidence
  4D-STEM paper.** Six differently-phrased queries (2015–2026 windows, including
  "RHEED ptychography", "reflection electron ptychography", "grazing incidence 4D-STEM")
  returned only transmission 4D-STEM/ptychography work.
* The one concrete hit is a **patent**: [PAT02] US 10,755,892 B?, *"Reflection-mode
  electron-beam inspection using ptychographic imaging"* — abstract (search summariser,
  `UNVERIFIED`): "systems and methods for ptychographic imaging using **particle beams** for
  efficient high-resolution inspection in a **reflection-mode configuration** suitable for
  inspection of semiconductor devices … reflective ptychographic imaging generates
  high-resolution output images by transforming **diffraction-plane** images using phase
  information from **sample-plane** images". Assignee and inventors **not obtained**
  (most likely a semiconductor-metrology company; do not state one without checking).
* Adjacent and reachable-by-analogy: [P42] Blackburn & McLeod 2021 (ptychography vs off-axis
  holography, transmission); "Sub-ångström resolution ptychography in a scanning electron
  microscope at 20 keV", *Nat. Commun.* (2025) — `METADATA_VERIFIED(index, single)`,
  transmission-in-SEM, relevant only as a low-energy ptychography precedent.
* **Conclusion for the paper: reflection-mode electron ptychography appears to be an open
  field with, as far as this (badly constrained) search can tell, no published
  demonstration. That is a claim worth making only after a proper Scopus/WoS search.**

---

## 6. CURRENT STATE (2015–2026)

### 6.1 Reflection electron holography itself
**No post-2015 reflection electron holography experiment was found.** Repeated searches
returned only [P01], [P02], [P03], [P08], [P09] and the Hitachi patent. Two caveats: (a) the
Semantic Scholar / OpenAlex citation endpoints that the task specified for this purpose were
blocked, so I could not enumerate citing works — this is a *search failure*, not evidence of
absence; (b) my only instrument was a general web search, which is weak for this.
**Do not write "no one has done this since 1993" on the strength of this review.**

### 6.2 Biprism architecture and reference-wave engineering (the live thread)
| ID | Record | Content (`+ABSTRACT(index)`) |
|---|---|---|
| [P47] | K. Harada, A. Tonomura, Y. Togawa, T. Akashi & T. Matsuda, "Double-biprism electron interferometry", *Appl. Phys. Lett.* **84**(17), 3229–3231 (2004). DOI 10.1063/1.1715155 | Upper biprism **on the image plane of the objective lens**, lower one **between the crossover and the image plane of the magnifying lens**; this **decouples fringe spacing from interference-region width** — the two hologram parameters become independently controllable. Demonstrated on a 1 MV FE microscope. |
| [P45] | T. Tanigaki, Y. Inada, S. Aizawa, T. Suzuki, H. S. Park, T. Matsuda, A. Taniyama, D. Shindo & A. Tonomura, "Split-illumination electron holography", *Appl. Phys. Lett.* **101**(4), 043101 (2012). DOI 10.1063/1.4737152 | **One biprism in the illumination system and two in the imaging system.** A **condenser biprism splits the illuminating wave into two mutually coherent waves**: one illuminates an area **far from the sample edge**, the other **passes through vacuum outside the sample**. Removes the "object must be near a vacuum edge" constraint. |
| [P46] | T. Tanigaki, S. Aizawa, H. S. Park, T. Matsuda, K. Harada & D. Shindo, "Advanced split-illumination electron holography without Fresnel fringes", *Ultramicroscopy* **137**, 7–11 (2014). DOI 10.1016/j.ultramic.2013.11.002; PMID 24269525 | **Two biprisms in the illumination system and two in the imaging system**; a **focused image of the upper condenser-biprism filament is formed on the sample plane** and all other filaments hidden in its shadow ⇒ reconstructed object waves **free of Fresnel-fringe modulation**, and holograms of objects distant from the reference. |

**This is the family Ali's gun-side/condenser biprism belongs to.** [P45]/[P46] are the
correct public citations for "a condenser-side biprism that splits the illumination and
provides a reference that has not touched the specimen". The instruction file's prohibition
stands: none of this establishes the geometry, voltage, conjugate planes or performance of
the specific biprism installed at UVic.

### 6.3 University of Victoria — public, citable work
| ID | Record | Evidence / content |
|---|---|---|
| [P42] | A. M. Blackburn & R. A. McLeod, "Practical implementation of high-resolution electron ptychography and comparison with off-axis electron holography", *Microscopy* **70**(1), 131–147 (2021) | `METADATA_VERIFIED(index) +ABSTRACT(index)`. **Same special issue as [P07].** Abstract points: ptychography recovers phase **without a biprism and without needing a minimally-structured region adjacent to the object**; the paper gives a **practical workflow** and compares HR ptychography with holography through experiment and modelling. Directly on-point for the lab's ptychography ambitions. |
| [P43] | R. A. Herring, "Diffracted beam interferometry — differential phase contrast image of an amorphous thin film material", *Micron* **160**, 103317 (2022). DOI 10.1016/j.micron.2022.103317; PMID 35753170 | `METADATA_VERIFIED(index) +ABSTRACT(index)`. Affiliation MENG/CAMTEC, University of Victoria. **An electron biprism interferes two symmetrically diffracted beams generated by an Au crystal substrate, which carry the phase of an amorphous overlayer**; Bragg diffraction from the substrate explains the strong phase contrast. |
| [P44] | R. A. Herring, "Phase imaging dislocations using diffracted beam interferometry", *Microscopy* **70**(3), 297–… (2021) | `METADATA_VERIFIED(index, single)`. Method: **interference of two symmetrically diffracted beams on the optic axis via a biprism, each carrying half the phase of the dislocation core**, recombining to give the full core phase shift. |
| — | A. M. Blackburn & J. C. Loudon, "Vortex beam production and contrast enhancement from a magnetic spiral phase plate", *Ultramicroscopy* **136**, 127–143 (2014); "Forbidden reflection moiré patterns in metal–2D material interfaces", *Microsc. Microanal.* **26**, 860–863 (2020) | `METADATA_VERIFIED(index, single)` each — listed for completeness of the public Blackburn record. |

**Diffracted-beam interferometry (Herring, UVic) is the local, in-house ancestor of
"dark-field holography with a biprism".** It is worth citing in Ali's paper as prior art on
interfering *diffracted* beams with a biprism, distinct from Hÿtch's DFEH (which interferes
one diffracted beam with a diffracted vacuum-side reference).

### 6.4 Modern step-phase holography (transmission)
[P51] Subakti, Daqiqshirazi, Wolf, Linck, Kern, Jain, Kretschmer, Krasheninnikov, Brumme &
Lubk, "Electron holographic mapping of structural (and electronic) reconstruction at mono-
and bilayer steps of h-BN", *Phys. Rev. Research* **5**, 033137 (2023); arXiv:2210.04027.
`METADATA_VERIFIED(index) +ABSTRACT(index)`: medium- and high-resolution **autocorrected
off-axis holography** probes the electrostatic potential and in/out-of-plane charge
delocalisation at edges and **steps** in multilayer h-BN, combined with ab-initio
calculations. Transmission, but the closest modern "holographic phase of an atomic step".

### 6.5 Modern reflection simulation software (the part I could actually verify)

Read directly (`SECTION_READ` of the README at `raw.githubusercontent.com`):

* **`sim-trhepd-rheed` (STR)** — Fortran, GPL, GitHub `sim-trhepd-rheed/sim-trhepd-rheed`.
  Implements **Ichimiya's surface-parallel multi-slice many-beam RHEED calculation**.
  Its README's reference list, **read verbatim**, is:
  [1] T. Hanada, Y. Motoyama, K. Yoshimi, T. Hoshi, *Comput. Phys. Commun.* **277**,
      108371/1–10 (2022), https://doi.org/10.1016/j.cpc.2022.108371;
  [2] T. Hanada, H. Daimon, S. Ino, *Phys. Rev. B* **51**, 13320–13325 (1995);
  [3] A. Ichimiya, *Jpn. J. Appl. Phys.* **22**, 176–180 (1983).
  Inputs: XYZ atomic positions + a TRHEPD/RHEED configuration; outputs: diffraction
  intensities, rocking curves, scattering-potential files, Quantum ESPRESSO inputs.
  **This is the only mature open-source dynamical reflection engine I located.**
* **`rheedium`** (`debangshu-mukherjee/rheedium`, JAX) — **kinematic** diffraction as the
  primary forward model with **optional dynamical multislice**; "every numerical function is
  pure, traceable, and `jit`/`grad`/`vmap`-friendly"; differentiable through Ewald
  construction, atomic form factors, Debye–Waller factors, **crystal truncation rods**,
  finite-domain broadening, instrument effects (divergence, energy spread, detector PSF),
  detector projection, and surface models (slabs, reconstructions, defects); explicitly aimed
  at **gradient-based inverse problems** ("the same code powers both simulation and
  reconstruction"). Cites itself as Mukherjee, *Rheedium*, 2025, DOI 10.5281/zenodo.14757400.
  Its README also states that a July-2026 internal "red-team audit" found and fixed ~60
  physics/implementation defects now guarded by `rh.audit.run_default_invariants()` —
  **treat as pre-1.0 research code, useful as a design reference, not as a benchmark.**
* **`abTEM`** — README **contains no mention of reflection, RHEED, grazing incidence or
  surface reflection geometry**; transmission multislice/PRISM only. Citation it requests:
  J. Madsen & T. Susi, "The abTEM code: transmission electron microscopy from first
  principles", *Open Research Europe* **1**:24 (2021), DOI 10.12688/openreseurope.13015.2.
* **`py_multislice` (HamishGBrown)** — README makes **no mention of reflection/RHEED/grazing
  incidence**; transmission only (PyTorch/GPU, STEM-EELS, PRISM).
* **`prismatic` (prism-em/prismatic)** — README carries the verbatim notice:
  *"Prismatic is no longer actively maintained. We appreciate any future interest or use,
  but will be less able to troubleshoot issues or push updates to the software in the
  future."* and points users to actively-maintained alternatives, **naming abTEM**.
  → **Directly relevant to this repository, which pins `prismatique==0.0.1` wrapping
  Prismatic.** Not a reason to change anything today (instruction §S: do not upgrade to make
  an assumed API work), but it is a dependency-risk fact that belongs in the repo's
  `model_assumptions.md`.
* **`prismatique` (mrfitzpa/prismatique)** — README read: "a wrapper to the Python library
  `pyprismatic`, which itself is a thin wrapper to `prismatic`, a CUDA/C++ package for fast
  image simulations in STEM and HRTEM". Install via pip/conda-forge; GPU needs CUDA ≥
  10.2.89. A Zenodo DOI badge `10.5281/zenodo.18296081` is present; **the README gives no
  explicit citation text and no version number** (documentation site `mrfitzpa.github.io`
  is blocked, so the version-matched API for `0.0.1` could not be checked — exactly the risk
  instruction §S01/§9.6 flags).
* Other RHEED repos located (metadata only, not read): `yux1991/PyRHEED` (analysis +
  simulation, Python), `ElsevierSoftwareX/SOFTX_2020_278` (`rheed++`, C++, RHEED intensity
  oscillations during epitaxial growth), plus several small kinematic MATLAB/Python projects.

* [P49] S. Kudo et al., "A fast and accurate computation method for reflective diffraction
  simulations" (arXiv:2306.00271, 2023); journal version title reported as "A fast and
  **efficient** computation method for reflective diffraction simulations", *Comput. Phys.
  Commun.* (Nov 2023), PII S0010465523003740. `METADATA_VERIFIED(index) +ABSTRACT(index)`,
  **title discrepancy `UNVERIFIED`**. Reformulates the RHEED/TRHEPD **boundary-value problem
  as an initial-value matrix ODE**, solved with high-order integrators (RK4, splitting
  methods) plus a generalised recursive-reflection technique; reported **up to ~2000×**
  speed-up at equal accuracy. This is the current state of the art for fast dynamical
  reflection solvers and is the natural benchmark partner for a multislice reflection code.

---

## 7. BOOK RECORDS [B01]–[B15]

**I could not verify any B-record against its publisher page or DOI resolver in this
session** — `doi.org`, `link.springer.com`, `global.oup.com`, `www.cambridge.org`,
`shop.elsevier.com` and `www.wiley.com` are all blocked. Their identities therefore rest on
the project instruction file (`PROJECT_INPUT`) plus, in a few cases, search-index
corroboration. The table below records exactly what extra information I obtained.

| ID | Status this session | Extra information obtained |
|---|---|---|
| B01 Spence, *HREM* 4th ed., OUP 2013 | `PROJECT_INPUT`, not re-verified | — |
| B02 De Graef, *Intro. to Conventional TEM*, CUP 2003 | `PROJECT_INPUT`, not re-verified | — |
| B03 Hawkes & Kasper, *Principles of Electron Optics* Vol. 3, 2nd ed., 2022 | `PROJECT_INPUT`, not re-verified | — |
| B04 Hawkes & Kasper, Vol. 4, 2nd ed., 2022 | `PROJECT_INPUT`, not re-verified | — |
| B05 Rose, *Geometrical Charged-Particle Optics*, 2nd ed. | `PROJECT_INPUT`, not re-verified | — |
| B06 Kirkland, *Advanced Computing in EM*, 3rd ed., Springer 2020 | `METADATA_VERIFIED(index, single)` for existence/edition (Springer book DOI page and ISBNs 9783030332594 / 9783030332624 appeared in the index) | **Table of contents NOT obtained.** Only a blurb-level statement that the 3rd edition expands aberration correction (incl. higher-order multipole aberrations), adds ABF, and covers GPU parallel processing. |
| B07 Ichimiya & Cohen, *RHEED*, CUP | `METADATA_VERIFIED(index)` | **Chapter list obtained** — see §3.4. Relevant: "The diffraction conditions"; "Kikuchi and resonance patterns"; "Dynamical theory: transfer matrix method"; "Dynamical theory: embedded R-matrix method"; "Dynamical theory: integral method" (ch. 14, confirmed by URL); "Structural analysis of crystal surfaces"; appendix "Optimization of dynamical calculation". |
| B08 Peng, Dudarev & Whelan, *High-Energy Electron Diffraction and Microscopy*, OUP | `METADATA_VERIFIED(index)` | **Chapter list obtained** — see §3.4. Relevant: **ch. 5 "Dynamical theory III — Reflection high-energy electron diffraction"** (title confirmed literally from the Oxford Academic chapter URL), ch. 6 "Resonance effects in diffraction", ch. 13 "The atomic scattering factor and the optical potential", and an appendix with a **FORTRAN listing of RHEED routines**. **Year discrepancy 2003 vs 2004 unresolved.** |
| B09 Völkl, Allard & Joy (eds.), *Introduction to Electron Holography*, 1999 | `METADATA_VERIFIED(index)` | **Full chapter-title list obtained** (§1.8): 1 The History of the Electron Biprism; 2 Principles and Theory of Electron Holography; 3 Optical Characteristics of a Holography Electron Microscope; 4 Practical Electron Holography; 5 Quantitative Electron Holography; **6 The Reconstruction of Off-Axis Electron Holograms** (= [C01]); 7 Electron Holography of Electromagnetic Fields; 8 On Recording, Processing and Interpretation of Low Magnification Electron Holograms; 9 High Resolution Off-Axis Electron Holography; 10 Off-Axis STEM Holography; 11 Focus Variation Electron Holography; 12 Applications of Electron Holography; **13 Electron Holography using Diffracted Electron Beams (DBH)**; 14 Electron Holography at Low Energy; 15 A Plus or Minus Sign in the Fourier Transform? — **No reflection-geometry chapter; no Osakabe chapter.** Chapter 13's authors and pages were not obtained. Chapter 15 is worth reading before fixing the repository's FFT sign convention (instruction §9.8). |
| B10 Tonomura, *Electron Holography*, 2nd ed., Springer | `METADATA_VERIFIED(index)` | Chapters located by DOI suffix: 1 Introduction; 2 Principles of Holography; 4 Historical Development of Electron Holography; 6 Aharonov–Bohm Effect…; **7 Electron-Holographic Interferometry**; 8 High-Resolution Microscopy. Chapters 3 and 5 not identified. **No evidence located that any chapter covers reflection/surface holography** — ch. 7 is the likely candidate, unverified. |
| B11 Shindo & Tomita, *Material Characterization Using Electron Holography*, Wiley-VCH 2022 | `PROJECT_INPUT` | One chapter DOI surfaced in the index: `10.1002/9783527829712.ch6` "Related Techniques and Specialized Instrumentation", and `…ch4` "Principles of Electron Holography". Note: the repository README cites this book as "**Tomita & Shindo (2022)**"; the publisher order in the instruction file is **Shindo & Tomita** — the README's author order should be corrected. |
| B12 Hawkes & Spence (eds.), *Springer Handbook of Microscopy*, 2019 | `PROJECT_INPUT` | Chapter pages for [C02] (`…00069-1_16`) and [C03] (`…00069-1_17`) both appeared in the index, consistent with the instruction file. |
| B13 Kohl & Reimer, *TEM: Physics of Image Formation*, 5th ed. | `PROJECT_INPUT`, not re-verified | — |
| B14 Williams & Carter, *TEM*, 2nd ed. | `PROJECT_INPUT`, not re-verified | — |
| B15 Egerton, *EELS in the Electron Microscope*, 3rd ed. | `PROJECT_INPUT`, not re-verified | — |

---

## 8. WHAT OSAKABE (1988) ACTUALLY DID, AS FAR AS ACCESSIBLE SOURCES ALLOW

### 8.1 Facts I can support

1. A paper with the exact title "Observation of Atomic Steps by Reflection Electron
   Holography" by N. Osakabe, T. Matsuda, J. Endo and A. Tonomura exists in *Jpn. J. Appl.
   Phys.* **27** (1988) at page L1772 (or 1772), DOI 10.1143/JJAP.27.L1772.
   `METADATA_VERIFIED(index)` + `PROJECT_INPUT`.
2. The authors were at **Hitachi Ltd, Advanced Research Laboratory, Kokubunji, Tokyo**
   (affiliation returned for the 1989 PRL [P02]). `METADATA_VERIFIED(index)`.
3. The method, as described by Osakabe himself four years later in [P08]:
   the **phase shift of a Bragg-reflected electron wave**, measured by **holographic
   interferometry** in an electron microscope with a **field-emission gun and an electron
   biprism**; the physical basis is a **geometrical path difference produced by surface
   topography, measured in units of the electron wavelength**; observables demonstrated were
   the **phase shift at a monatomic step** and the **displacement field around a dislocation
   emerging on the surface**; sensitivity described as "**sub-Å surface morphology**".
   `+ABSTRACT(index)` — from [P08], **not** from [P01].
4. Osakabe's REM lineage: he was a co-author of the Yagi/Honjo UHV-REM studies of **Si(111)
   clean and Au-covered surfaces** [P14], i.e. he came to holography already able to image
   Si(111) steps in REM. `METADATA_VERIFIED(index)`.
5. In the follow-up PRL [P02] the system was a **cleaved GaAs(110) surface** with a
   **screw dislocation**, height precision **~0.01 Å**, and the asymmetry of the deformation
   field was explained by **surface stress relaxation**. `+ABSTRACT(index)`.
6. Hitachi filed a patent, **US 4,998,788 "Reflection electron holography apparatus"**
   (Osakabe, Endo, Tonomura, Tomita, Furutsu), whose description — as reported second-hand —
   forms the hologram by superposing the **reflected wave** with a **direct wave that passes
   beside the specimen** using a **single biprism**, with the **objective focal length and
   biprism potential adjusted to reduce the intersecting angle to a recordable fringe
   spacing**. `METADATA_VERIFIED(index, single)` for the patent's identity;
   `UNVERIFIED` for the quoted description.

### 8.2 Inferences (clearly marked — these are mine, not the sources')

* **I1.** Given [P08]'s "geometrical path differences … measured in units of wavelengths"
  and "Bragg-reflected electron wave", Osakabe's working relation was almost certainly the
  kinematic path-difference relation Δφ = (4π/λ)·h·sinθ (equivalently 2π g·u), not a
  dynamical reflection-coefficient model. `DERIVED_HERE` inference from `+ABSTRACT(index)`
  text. **Confidence: moderate-high. Verify in [P01]/[P08] before citing.**
* **I2.** The reference wave in the Hitachi arrangement was a **vacuum wave**, not a second
  reflected beam. Based on §8.1.6. **Confidence: moderate (patent-level, second-hand).**
* **I3.** Operating regime bracket. [P16] states the Hitachi phase sensitivity as **1/100 of
  a wavelength** (≈ 0.063 rad). [P02] claims **0.01 Å** height precision. Combining with
  dΔφ/dh = 4π sinθ/λ: 0.01 Å at 0.063 rad requires sinθ/λ ≈ 0.50 Å⁻¹, i.e.
  **sinθ ≈ 0.019 at 100 kV (θ ≈ 19 mrad ≈ 1.1°) or sinθ ≈ 0.013 at 200 kV (≈ 13 mrad)**.
  Both are squarely in the normal REM glancing-angle range. `DERIVED_HERE`.
  **This is a consistency check, not a measurement: the actual energy and angle of [P02]
  are unknown to me.**

### 8.3 Explicitly NOT known about [P01]
Surface material and orientation; electron energy and microscope; which Bragg reflection
(specular order, or a non-specular reflection); glancing angle; biprism type, position and
voltage; reference-wave trajectory; hologram fringe spacing and interference-region width;
the exact phase-step equation and its sign and refraction/mean-inner-potential treatment;
the measured phase values; the image foreshortening quoted; the stated limitations.
**All `UNVERIFIED`.**

---

## 9. PHYSICS FACTS EXTRACTED FROM SOURCES (WITH LOCATORS AND EVIDENCE LABELS)

### 9.1 Conventions fixed for everything below (`DERIVED_HERE`)
Time convention exp(−iωt); a wave propagating a distance L in vacuum acquires phase **+kL**
with k = 2π/λ. θ always denotes the **glancing angle measured from the surface plane**
(never from the normal); 2θ is the total scattering angle of the specular beam. n̂ is the
**outward** surface normal. λ is the **relativistic vacuum** wavelength. **g** is written in
cycles per length (|g| = 1/d), so phases carry an explicit 2π; **q** = 2π**g** is the
angular-units version. Switching to the exp(+iωt) convention or to the opposite FFT sign
flips every phase sign below. *(Instruction §9.8 requires this paragraph to be mirrored into
`docs/physics_conventions.md`.)*

### 9.2 The step-phase relation — derivation (`DERIVED_HERE`)

Two terraces of the same crystal, the second lowered by h along −n̂. The scattering object
for terrace 2 is that of terrace 1 translated by **u** = −h n̂. With the first-Born /
projection convention ψ ∝ ∫V(**r**)e^(−i**q·r**)d³r and momentum transfer
**q** = **k**_out − **k**_in, a translation by **u** multiplies the scattered amplitude by
e^(−i**q·u**). Hence

&nbsp;&nbsp;&nbsp;&nbsp;**Δφ ≡ φ(lower terrace) − φ(upper terrace) = +h (q·n̂)**

and for the **specular** beam at external glancing angle θ, **q** = (4π sinθ/λ) n̂, so

&nbsp;&nbsp;&nbsp;&nbsp;**Δφ = (4π/λ)·h·sinθ = 2π·(2 sinθ/λ)·h = 2π **g·u**, |g| = 2 sinθ/λ.**   … (9.2.1)

Equivalently, path difference 2h sinθ, phase 2π×(2h sinθ)/λ — which is exactly the picture
[P08] describes ("geometrical path differences … measured in units of wavelengths").

**The extra path is travelled in VACUUM above the lower terrace, so the vacuum λ and the
EXTERNAL glancing angle are the correct ones. Do not substitute the refracted internal
angle here.** (This is the single most common error in the reflection literature's
folklore, and §9.4 shows it is a π-sized error for Si.)

**Repository check.** `pipeline/step_height_reflection_formula.py` implements
h = Δφ·λ / [4π sin θ_B (ĝ·n̂_surf)], i.e. Δφ = (4π/λ) h sinθ_B (ĝ·n̂). That **is**
(9.2.1) generalised to a non-specular reflection, and it is **correct as a kinematic,
rigid-displacement relation** provided:
(a) θ_B is the **half-scattering angle**, so that |g| = 2 sinθ_B/λ (for the specular beam
this is the glancing angle; it is **not** the angle to the normal);
(b) λ is the relativistic **vacuum** wavelength;
(c) **u** = h n̂ is a **rigid** translation of the whole scattering region;
(d) the two terraces are otherwise identical, so the dynamical reflection phase φ_R cancels;
(e) θ_B is the **external** angle (see 9.4);
(f) the measured Δφ has been unwrapped correctly (see 9.3).
It is **not** a "universal reflection-height relation", and (c)–(f) are exactly the
assumptions that a reflection experiment can violate.

### 9.3 Wrapping, invisibility, and choosing the reflection (`DERIVED_HERE`)

* The height is determined only **modulo** Δh₂π = **λ / (2 sinθ)**. At an exact Bragg
  condition, λ/(2 sinθ_B) = d_hkl, so **the height ambiguity period equals the interplanar
  spacing of the operating reflection.**
* **Invisibility.** If **g** is a bulk reciprocal-lattice vector and **u** is a lattice
  translation, e^(2πi g·u) = 1. For a surface step of height h = d_hkl observed in the n-th
  order specular reflection at its exact Bragg angle, g·u = n ∈ ℤ ⇒ **Δφ ≡ 0 and the step
  is invisible.** A naive reading of (9.2.1) therefore predicts that monatomic steps
  vanish at exactly the condition REM operators prefer.
* **The resolution is refraction** (§9.4): the *external* scattering vector is **not** a
  bulk reciprocal-lattice vector, so g·u is not an integer. Refraction is what makes the
  step visible.
* Practical consequences for the experiment and for the simulation:
  - the contrast of a step is a **continuous function of the glancing angle** along the (00)
    crystal-truncation rod; the choice of angle is a *design variable*, not a nuisance;
  - a dark-field (non-specular) reflection has **in-plane** components of **g** and is
    therefore sensitive to **in-plane** displacement (reconstruction, dislocation shear),
    which is exactly what [P02] measured;
  - the repository's "sensitivity denominator" sinθ_B(ĝ·n̂) is not the only thing that can
    kill sensitivity: **g·u ∈ ℤ kills it completely**, and that case must be detected and
    reported, not divided through.

### 9.4 Refraction by the mean inner potential (`DERIVED_HERE` from an `+ABSTRACT(index)` premise)

**Premise (source-level, `+ABSTRACT(index)`, from a ScienceDirect topic page surfaced by the
index; original not read):** for RHEED, Snell's law reads
cos θ_ext / cos θ_int = n = 1 + Φ₀/(2E), with Φ₀ the mean inner potential and E the
accelerating voltage; the resulting angular shift is of order 10⁻² rad, "comparable with the
Bragg angle for prominent lattice planes"; all RHEED peaks shift to **lower** angles.

**Derivation from that premise (`DERIVED_HERE`):**
cos²θ_ext = (1+Φ₀/E)(1 − sin²θ_int) ⇒

&nbsp;&nbsp;&nbsp;&nbsp;**sin²θ_int = (sin²θ_ext + Φ₀/E)/(1 + Φ₀/E) ≈ sin²θ_ext + Φ₀/E**   … (9.4.1)

(the approximation is excellent since Φ₀/E ~ 10⁻⁴). The **critical angle for total external
reflection** is θ_c = √(Φ₀/E).

*(Equivalent, and the form to implement: conservation of the surface-parallel wavevector
plus k_int² − k_ext² = 8π²m e Φ₀/h² gives (9.4.1) directly. Use the relativistically
corrected E; take the exact relativistic form from [B07] ch. "The diffraction conditions" or
[B08] ch. 5 before publishing a number.)*

**Consequence — the refraction-corrected step phase (`DERIVED_HERE`):** operating at the
n-th-order bulk Bragg condition means sin θ_int = nλ/(2d). The step phase uses the external
angle, so with h = d,

&nbsp;&nbsp;&nbsp;&nbsp;**Δφ = 2πn·√( 1 − θ_c² / sin²θ_int ) ,  θ_c = √(Φ₀/E).**   … (9.4.2)

Limits: Φ₀→0 gives Δφ→2πn (invisible); sinθ_int→θ_c gives Δφ→0. **Refraction is not a small
correction to the step phase — it is the whole signal.**

**Worked numbers for silicon** (`DERIVED_HERE`; λ from the standard relativistic de Broglie
expression; a_Si = 5.43102 Å ⇒ d₁₁₁ = 3.13560 Å; **Φ₀ = 12 V assumed — `ASSUMPTION`, must be
sourced or measured, and it is the dominant systematic below**):

λ = 0.037014 Å (100 kV), 0.025079 Å (200 kV), 0.019687 Å (300 kV).
θ_c(Si) = 10.95 mrad (100 kV), 7.75 mrad (200 kV), 6.32 mrad (300 kV).

Si{111} surface, specular order n (diamond structure factor forbids n = 2, 6, 10), 200 kV:

| n (nnn) | θ_int (mrad) | **θ_ext (mrad)** | θ_ext (deg) | foreshortening sinθ_ext | **Δφ for a 3.1356 Å step** |
|---|---|---|---|---|---|
| 3 | 12.00 | 9.16 | 0.525 | 1/109 | 4.582π ≡ **0.58π** |
| 4 | 16.00 | **14.00** | 0.802 | 1/71.5 | 6.999π ≡ **1.00π** |
| 5 | 19.99 | 18.43 | 1.056 | 1/54.3 | 9.219π ≡ **1.22π** |
| 7 | 27.99 | 26.90 | 1.541 | 1/37.2 | 13.453π ≡ **1.45π** |
| 8 | 31.99 | 31.03 | 1.778 | 1/32.2 | 15.524π ≡ **1.52π** |

**Read the n = 4 row.** At 200 kV the (444) condition sits at an *external* glancing angle
of **14.0 mrad (0.80°)**, not the naive 16.0 mrad, and a one-bilayer Si{111} step there
produces **exactly π** — maximum holographic contrast — rather than the zero that the
no-refraction argument predicts. The refraction correction to the step phase in this case is
itself ≈ π.

Si(001) (step height a/4 = 1.35776 Å; (002) forbidden, so use (004), (008), …), 200 kV:

| order m | θ_int (mrad) | θ_ext (mrad) | foreshortening | Δφ for a 1.3578 Å step |
|---|---|---|---|---|
| 1 (004) | 9.23 | 5.03 | 1/199 | 1.09π |
| 2 (008) | 18.47 | 16.77 | 1/59.6 | 3.63π ≡ 1.63π |
| 3 | 27.70 | 26.60 | 1/37.6 | 5.76π ≡ 1.76π |

**Reproducibility:** every number above follows from λ, d, Φ₀ and equations (9.2.1),
(9.4.1), (9.4.2). They should be regenerated by a unit test in the repository, not copied.

### 9.5 Height sensitivity (`DERIVED_HERE`)
dΔφ/dh = 4π sinθ_ext/λ. At 200 kV, n = 4 (θ_ext = 14.0 mrad): **7.01 rad/Å**, so
0.01 Å ↔ 0.070 rad ↔ **1/90 of a fringe** — consistent with the "1/100 of a wavelength"
figure that [P16] quotes for the Hitachi instruments and with the 0.01 Å precision claimed
in [P02]. This is a *consistency check between two abstract-level claims and my geometry*,
not a measurement.

### 9.6 Image foreshortening (`DERIVED_HERE` + `+ABSTRACT(index)`)
* Source level (`+ABSTRACT(index)`, provenance of the exact sentence unresolved): "REM
  images are severely foreshortened in one direction by a factor varying between **1/40 and
  1/70**"; "the image is foreshortened by a factor of **sin θ₀** in the direction of the
  propagating beam"; a separate snippet claims glancing angles "of the order of the Bragg
  angle (~5°)", which is **inconsistent** with 1/40–1/70 (5° ⇒ 1/11.5) — do not use the 5°
  figure.
* `DERIVED_HERE`: the foreshortening factor is sin θ_ext. The Si{111} table in §9.4 gives
  1/32 to 1/109 across the usable orders at 200 kV, and 1/42 for Si{111}(444) at 100 kV —
  which reproduces the quoted 1/40–1/70 range and identifies the angles that produce it.
* Consequences: the along-beam pixel size in a REM image is 1/sinθ times the across-beam
  one; a simulation box must be ~1/sinθ longer along the beam than across it to cover the
  same surface area; and **the along-beam resolution is not set by the lens but by the
  surface-parallel coherence/propagation length of the reflected wave** (the mechanism
  behind the extended step contrast and the "double contours" of [P25]/[P26]).

### 9.7 Validity of transmission-type multislice at grazing incidence
* Source level: [P19] (abstract, `+ABSTRACT(index)`) states that a forward-dynamical-
  scattering computing method based on the **Cowley–Moodie physical-optics theory** "has been
  **successfully applied to the Bragg case**" and is used for RHEED amplitudes and REM image
  intensities, **including a crystal surface with a defect**. [P21] investigates the
  **consistency of Bloch-wave and multislice results in reflection**. [P18] is the original
  Acta Cryst A statement of the method. **None of these was read.**
* Generic multislice accuracy criteria surfaced at abstract level (`UNVERIFIED` as to
  source): maximum slice thickness ≈ k d² where k is the wavenumber and d the scale over
  which the potential varies; enough beams to avoid aliasing of the convolution.
* `DERIVED_HERE` — why it can work, and what must be true:
  1. **Small-angle condition is satisfied.** The specular beam leaves at 2θ ≈ 25–60 mrad
     from the incident direction. Multislice neglects back-scattering, and grazing-incidence
     "reflection" is **not** back-scattering: it is forward scattering through a small angle
     off a surface that is nearly parallel to the beam. The surface-normal momentum
     component reverses; the along-axis component does not. *(This is the direct answer to
     repository instruction §9.3.)*
  2. **Box geometry is the hard part.** The box must be long along the beam (the
     interaction length along the surface is tens to hundreds of nm) and tall along n̂
     (vacuum above + the penetrated/evanescent region below).
  3. **Wraparound along n̂ is fatal if unmanaged.** FFT multislice is periodic transverse to
     the beam. Along the surface normal the problem is *not* periodic (vacuum above, crystal
     below), so the reflected/escaping wave wraps and re-enters the crystal from the top.
     Requires a generous vacuum margin plus an absorbing (imaginary-potential) or
     apodising layer at both n̂ boundaries; and the measurement region must be checked to be
     free of periodic-image contamination.
  4. **Absorption is not optional.** The component that penetrates deep must be removed, or
     it re-emerges spuriously. An optical potential is standard in RHEED/REM dynamical
     calculations ([P17], [P18], [B08] ch. 13). *Instruction §B15 warning applies: an
     absorptive parameter must be sourced, not tuned.*
  5. **Entrance boundary.** The incident plane wave must be launched in vacuum upstream of
     the surface at the correct glancing angle; a tilted-illumination multislice formulation
     is needed if the beam is not along the slice normal (see the inclined-illumination
     multislice literature, e.g. Ishizuka 1998 and *Phil. Mag. Lett.* **71**(1) 1995 —
     both `METADATA_VERIFIED(index, single)` only).
  6. **The alternative is surface-parallel slicing** ([P17], and the `sim-trhepd-rheed`
     implementation), which handles the semi-infinite crystal and the Bragg boundary
     condition natively and does not have the wraparound problem along n̂ — at the price of
     not reusing a transmission code. **A cross-check of the two is the right validation,
     and [P21] is the paper that says so.**

### 9.8 Cross-check of the repository's crystal geometry (`DERIVED_HERE`, arithmetic)
The repository README's prose names a "(1,1,−1) facet" while its diagram names [1,−1,1] as
the surface normal, with the beam along [110] (instruction §9.2 flags this).
Simple arithmetic settles which is self-consistent for a grazing-incidence geometry in which
the beam lies (almost) **in** the surface:
&nbsp;&nbsp;[1,−1,1]·[1,1,0] = 1 − 1 + 0 = **0** ⇒ [1,−1,1] ⊥ [110] ✔
&nbsp;&nbsp;[1,1,−1]·[1,1,0] = 1 + 1 + 0 = **2** ⇒ [1,1,−1] is **not** ⊥ [110] ✘
and the README's third axis [1,−1,−2] is orthogonal to both ([1,−1,−2]·[1,1,0] = 0,
[1,−1,−2]·[1,−1,1] = 1 + 1 − 2 = 0). **The diagram's [1,−1,1] is the consistent surface
normal; the prose's "(1,1,−1)" is not.** (Cubic system, so (hkl) ⟂ [hkl] and the dot
products are meaningful.) Also note the beam must be tilted **out** of the facet plane by
the glancing angle θ; "beam ∥ [110]" is only the zero-th-order description.

---

## 10. GAPS: WHAT REMAINS INACCESSIBLE OR UNVERIFIED

**Blocking (must be redone with normal network access):**
1. **[P01] Osakabe 1988 full text and even its abstract.** Nothing about its surface,
   energy, reflection, angle, reference wave, equations or numbers is established here.
2. **[P07] Harada 2021** — open access at PMC7850541, blocked here. Task item 2 is unmet.
3. **[P02E] the PRL erratum's content.**
4. **[P03] Banzhof & Herrmann 1993** — abstract not even obtained.
5. **[P31] Hÿtch et al. 2011** — the geometric-phase equation, its **sign**, its equation
   number and its stated validity conditions. I refuse to quote a sign I did not read.
6. **Citation graphs.** Semantic Scholar / OpenAlex / Crossref were all blocked, so the
   task's core discovery method ("everything that cites Osakabe 1988/1989 and Banzhof 1993")
   could not be executed. §6.1's "nothing found since 1993" is a search failure, not a
   result.
7. **All fifteen book records** — none re-verified against a publisher page or DOI.
   [B06] Kirkland's table of contents not obtained; Z. L. Wang 1996 chapter list not
   obtained; [B09] ch. 13 authors/pages not obtained.
8. **`prismatique` 0.0.1 version-matched API** — `mrfitzpa.github.io` blocked (this is the
   exact risk instruction §S01 and §9.6 warn about).

**Unresolved bibliographic details:**
* [P01] page prefix: L1772–L1774 vs 1772–1774.
* [P20] Ma & Marks 1989 page range: 174–182 vs 182–187 (two different summariser answers).
* [P18] DOI 10.1107/S0108767386098756 — reported by the summariser only.
* [B08] year 2003 (IUCr review) vs 2004 (instruction file / OUP record).
* [P29] Zhao–Poon–Tong exact title.
* [P34] Roy 2011 page numbers.
* [P49] journal title "accurate" vs "efficient".
* [PAT01] US 4,998,788 priority/grant dates (the reported dates are internally inconsistent);
  [PAT02] US 10,755,892 assignee and inventors.
* Existence of an Osakabe contribution in the 1995 Elsevier "Electron Holography"
  proceedings — asserted by the summariser, **not corroborated**.

**Physics that is derived here rather than sourced** (and therefore needs a textbook check
before it goes in a paper): the sign convention in (9.2.1); the exact relativistic form of
(9.4.1); Φ₀(Si) = 12 V; the claim that the diamond structure factor forbids n = 2, 6, 10 in
the (nnn) specular series (standard, but check against [B02]); and every number in the §9.4
tables.

---

## 11. IMPLICATIONS FOR THE SIMULATION REPOSITORY

Ordered by how much they change the code.

1. **Make refraction a first-class part of the geometry module, not a correction.**
   Equation (9.4.2) shows that for Si the mean-inner-potential refraction changes the step
   phase by ~π at the (444) condition and is the *reason* a monatomic step is visible at a
   bulk Bragg condition at all. A forward model that sets the external angle equal to the
   internal Bragg angle will predict *zero* step contrast. Implement (9.4.1), expose Φ₀ as a
   named, sourced parameter with an uncertainty, and add a regression test reproducing the
   §9.4 tables.
2. **Keep `step_height_reflection_formula.py`'s equation but rename and re-document it.**
   It is the *kinematic, rigid-displacement, external-angle* relation Δφ = 2π **g·u**. Put
   the six validity conditions of §9.2 in the docstring, state which angle θ_B is, and make
   the function refuse (not silently divide) when |g·u − round(g·u)| is small, i.e. near the
   invisibility condition. Report the wrap period λ/(2 sinθ) = d_hkl alongside every height.
3. **Add an explicit "reflection selection" step.** The observable depends on which point of
   the (00) CTR (or which non-specular reflection) is used. Make the operating order n / the
   external glancing angle an input with provenance, compute and log θ_int, θ_ext, θ_c,
   foreshortening, Δφ per unit height, and the height-wrap period. Forbid defaults.
4. **Treat the reference wave as a separate, explicitly specified branch — and check its
   tilt.** §9.3/§1.5: a vacuum ("direct") reference beside the specimen is **not parallel**
   to the object wave; in the specular-on-axis convention it arrives at 2θ ≈ 25–60 mrad to
   the axis, which is a huge intrinsic carrier and is also outside a small objective
   aperture. Any faithful model must state where the reference is selected, whether the
   biprism compensates that tilt, and what fringe spacing results. A reference reflected
   from a flat region of the *same* surface is automatically parallel — a different physical
   arrangement with different systematics. **Model both, name both, and never let the code
   silently choose.** (Instruction §9.4 requires this; §9.3 here gives the quantitative
   reason.)
5. **Cross-validate the propagation engine against a reflection benchmark, not a
   transmission one.** The right pairing is a transmission-style, beam-perpendicular
   multislice ([P18]/[P19], the family Prismatic/prismatique belongs to) against a
   surface-parallel dynamical solver ([P17], implemented openly in `sim-trhepd-rheed`) or a
   Bloch-wave Bragg-case solution ([P20]–[P22]); [P21] exists precisely to compare them.
   `sim-trhepd-rheed` is GPL Fortran, takes XYZ + a config, and outputs rocking curves —
   a realistic external benchmark for a Si surface.
6. **Engineer the box for reflection explicitly.** Vacuum margin and absorbing layers along
   the surface normal (wraparound), length along the beam set by 1/sinθ and by the
   surface-parallel interaction length, entrance boundary in vacuum, tilted-illumination
   multislice formulation, and a convergence test in each of those directions separately.
   Document slicing direction and lateral periodicity (instruction §9.3).
7. **Separate "complex-wave spot selection" from "hologram formation" from "hologram
   reconstruction" in the code, and test reconstruction on intensity only.** Nothing in this
   review changes instruction §9.1 — it reinforces it, because in reflection the object and
   reference beams differ in *direction* as well as phase, so an intensity hologram
   I = |u_obj + u_ref|² must be formed with the real relative tilt before the sideband is
   extracted.
8. **Expect, and test for, non-geometric phase.** The dynamical reflection phase φ_R(θ)
   varies rapidly near the Bragg–channelling and Bragg–Bragg resonances [P26]; the
   "double-contour" step contrast [P25]/[P26] is a real, published signature that a purely
   geometric model will not reproduce. A good acceptance test for the forward model is:
   *does it produce double-contour step contrast at the Bragg–Bragg condition?* If it does
   not, the model is not yet REM.
9. **Do not assume the DFEH geometric-phase machinery transfers.** [P31]–[P33] show that
   even in transmission the geometric phase needs a thickness/excitation-error-weighted
   projection and that dynamical effects are strong. In reflection there is no column; the
   weighting is over an extinction depth, and it must be derived. Mark any reflection
   analogue as `DERIVED_HERE` with a stated validity regime (instruction §1.7).
10. **Reflection-mode ptychography: adopt the X-ray forward-model vocabulary, not its
    physics.** [P36] (CTR ptychography of Pt(111) steps) is the closest published target;
    [P35]/[P37] give Bragg-adapted projection operators; [P38]–[P40] give reflection-geometry
    corrections. All are multiplicative-object models. For electrons at grazing incidence a
    multiplicative object is **not** a safe assumption, so a differentiable *dynamical*
    reflection forward model is the honest route — and `rheedium` (JAX, differentiable,
    CTR-aware, kinematic-with-optional-multislice) is the closest existing design reference.
    [P49]'s ODE reformulation is the speed route if a dynamical solver is needed in the loop.
11. **Fix the crystallography inconsistency using §9.8.** [1,−1,1] is the surface normal
    consistent with a [110] beam; "(1,1,−1)" is not. Add a numerical assertion
    (normal · beam ≈ 0 to within the glancing angle) to the generator, per instruction §9.2.
12. **Record the dependency risk.** Prismatic's own README now states it is no longer
    actively maintained and points to abTEM. abTEM and py_multislice have **no** reflection
    support in their READMEs. Note this in `docs/model_assumptions.md`; do **not** migrate
    on that basis alone (instruction §S).
13. **Bibliography hygiene.** The repository README cites [B11] as "Tomita & Shindo (2022)";
    the publisher order is **Shindo & Tomita**. Also add [P08] (Osakabe's own method
    summary) and [P19] (transmission-style multislice validated for the Bragg case) — these
    two are the most load-bearing citations the repository is currently missing.

---

## 12. HOW TO FINISH THIS REVIEW PROPERLY

With ordinary network access, in this order (about an hour of work):
1. PMC7850541 → read [P07] in full; extract its reflection-holography and biprism sections
   with figure numbers. (Free.)
2. `doi.org/10.1143/JJAP.27.L1772` → [P01]: surface, energy, reflection, glancing angle,
   reference wave, the phase equation **as written**, measured values, limitations.
3. `doi.org/10.1103/PhysRevLett.63.584.3` → what the erratum corrects.
4. `doi.org/10.1002/jemt.1070200415` → [P08] in full (Osakabe's own review of his method).
5. [P31] Hytch et al., *Ultramicroscopy* **111**(8), 1328-1337 (2011) - reach it via the
   ScienceDirect PII `S0304399111001586` (its DOI was not obtained here, so look it up
   rather than reconstructing it) -> the geometric-phase equation **with its sign**, its
   equation number, and its stated validity conditions.
6. Crossref each entry in `references.bib` and replace every
   `METADATA_VERIFIED(index)` with a genuine `METADATA_VERIFIED`.
7. Semantic Scholar citations of 10.1143/JJAP.27.L1772, 10.1103/PhysRevLett.62.2969 and
   10.1016/0304-3991(93)90123-F to settle §6.1 honestly.
