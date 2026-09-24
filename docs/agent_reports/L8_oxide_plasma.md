# L8 - Oxide overlayer on air-exposed, O2/Ar-plasma-cleaned, ion-milled Si(001): sourced parameters for the multislice overlayer

Prepared: 2026-09-24 by agent L8 (literature). Status: COMPLETE (written incrementally, sections in order 0-12).
Branch `claude/electron-holography-orchestration-nakd7r`. No repository file other than this report and
`docs/agent_reports/L8_new_refs.bib` is edited; nothing is committed or pushed. Raw downloads are kept outside
the repository in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/l8/` (called `l8/` below).

Task input (PROJECT_INPUT, Ali, 2026-09-24): ion-milled Si(001), exposed to air; the only surface treatment
before holography is an oxygen-argon plasma clean of about 10 min in a typical TEM-specimen plasma cleaner;
no HF dip, no UHV anneal. Hologram: 200 keV, specular (0,0,8) at about 16.13 mrad glancing incidence
(ASSUMPTION B32 for the exact angle; item 7 open), reflection-mode dark-field electron holography.

Read before starting: L7 sections 2 and 6 (S3 scenario, D1-D11); E6 sections 8, 9, M4, m7-m9; L6 sections
1.3-1.4, 3, 7.2-7.3 (absorption framework: TDS by frozen phonons, electronic absorption as a uniform
imaginary potential V' = 1/(2 sigma Lambda), surface plasmons separate); `docs/model_assumptions.md` B6, B7,
B8, B12; `docs/06_project_inputs_required.md` items 12, 20-23; `docs/08_paper_readiness.md` row 2.6;
`docs/references.bib` (218 entries; oxide-related entries already present: MORITA1990, YASAKA1991,
AZUMA2007, TOKUTAKE2015, KOROBTSOV2007, WANG97, KRUSE06, GAJDARDZISKA93, PENNINGTON15, AUSLENDER24,
MENDIS19, MENDIS24, TANISHIRO2003, ZLWANG96, B08 chapters).

Labels (instruction file section 1.4): METADATA_VERIFIED, SECTION_READ (only with a locator), REPRODUCED,
PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED. Sub-labels as in L5-L7: `+ABSTRACT(publisher)` = the
abstract read on the publisher's own page; `+ABSTRACT(PubMed)` = read in the Europe PMC/PubMed record;
`+ABSTRACT(index)` = only a search-engine or index summary seen (NOT evidence). No fact below rests on a
search-engine summary.

Constants used in DERIVED_HERE numbers (from the repository, `docs/physics_conventions.md` and E6 section 8):
200 keV, lambda = 0.025079 A, k = 2 pi / lambda = 250.53 A^-1, sigma = 7.2884e-4 rad V^-1 A^-1,
theta = 16.1347 mrad (B32), path factor 2 / sin(theta) = 124.0.

## 0. Log of hosts and access

| Time (UTC) | Host / service | Result |
|---|---|---|
| 04:00 | Crossref API `api.crossref.org/works` and `/works/<doi>` (no mailto; User-Agent "L8-literature-check/1.0") | works; JSON cached in `l8/crossref/` |
| 04:00 | OpenAlex `api.openalex.org/works/doi:<doi>` | works (single-record lookups); used for OA status only; its abstract index is `+ABSTRACT(index)` (not evidence) |
| 04:01 | Europe PMC REST (`www.ebi.ac.uk/europepmc/webservices/rest/search`) | works; abstracts cached as `l8/epmc_*.json` |
| 04:02 | link.springer.com (Applied Microscopy 2026 article) | redirected to a Springer cookie/IdP page; springeropen host answered 404 "Application Unavailable"; Crossref abstract read instead (the paper is about in-column plasma cleaning, not specimen oxidation; not used further) |
| 04:04 | J-STAGE (article pages and PDFs), J-STAGE WebAPI, CiNii Research | work (script `l8/jp_search.py`, copied from L7; queries `l8/jp_q*.json`, output `l8/jp_out*.txt`) |
| 04:05 | rafaldb.com (R. E. Dunin-Borkowski's publication page) | serves the author copy of the Springer Handbook of Microscopy chapter 16 (read) |
| 04:06 | NIMS MDR (`mdr.nims.go.jp`) | serves the green copy of Iakoubovskii et al. PRB 77, 104102 (2008) (read) |
| 04:08 | pubs.aip.org (APL, JAP) | HTTP 403 Cloudflare "Just a moment..." (not bypassed); affects Rau et al. 1996 and Wang et al. 1997 |
| 04:03 | physics.byu.edu | serves the SVC 2004 proceedings paper of Robinson, Allred et al. (read) |

PDF tools: PyMuPDF 1.28.2 in the scratch venv `scratchpad/pdfenv`; scanned pages rendered at 130-150 dpi and read
as images (files in `l8/render/`).

## 1. Mean inner potential and inelastic mean free path of amorphous SiO2 (task 2, first part)

### 1.1 Sources read

| # | Source | Access, URL read, SHA-256 of the file (in `l8/pdf/`) | Label |
|---|---|---|---|
| O1 | C.-W. Lee, Y. Ikematsu, D. Shindo, "Thickness Measurement of Amorphous SiO2 by EELS and Electron Holography", Mater. Trans. JIM 41(9), 1129-1131 (2000), DOI 10.2320/matertrans1989.41.1129 | OPEN (J-STAGE, "diamond" OA): `https://www.jstage.jst.go.jp/article/matertrans1989/41/9/41_9_1129/_pdf/-char/en`; scanned, no text layer; all 3 pages read as rendered images; SHA-256 d1d25bcd8ad588da9a50e551082ca3311e4b8ef58e3a00e5383cf4b1d27e51d5 | SECTION_READ (abstract; sec. 2; sec. 3 pp. 1130-1131; Figs. 2, 5; sec. 4) + METADATA_VERIFIED (Crossref) |
| O2 | R. E. Dunin-Borkowski, A. Kovacs, T. Kasama, M. R. McCartney, D. J. Smith, "Electron Holography", ch. 16 in P. W. Hawkes, J. C. H. Spence (eds.), Springer Handbook of Microscopy (Springer, 2019), pp. 767-818, DOI 10.1007/978-3-030-00069-1_16 | Author copy on the first author's site: `https://rafaldb.com/papers/B-2019-Science-of-Microscopy-Electron-holography.pdf` (52 pages); SHA-256 695e05e3ccea0055fce570aa44239c90c0d5ef88febcc334d5725c0ac6514445; p. 772 read as a rendered image; reference list read in the text layer. OpenAlex lists the chapter as closed; the author copy was read. This is [C02] of references.bib (instruction-file reference C02, until now unread): its author copy is OPEN here | SECTION_READ (sec. 16.2, p. 772-773; refs. 16.60-16.66, 16.76-16.82) + METADATA_VERIFIED (Crossref) |
| O3 | K. Iakoubovskii, K. Mitsuishi, Y. Nakayama, K. Furuya, "Mean free path of inelastic electron scattering in elemental solids and oxides using transmission electron microscopy: Atomic number dependent oscillatory behavior", Phys. Rev. B 77, 104102 (2008), DOI 10.1103/PhysRevB.77.104102 | OPEN (green): NIMS MDR `https://mdr.nims.go.jp/filesets/a245390a-da00-4f5e-a2a0-14b4ad052df0/download` (APS typeset pages, 7 pages); SHA-256 34ef97d0d31b56c6a4c8653283c1409cce0f26570ee91bb68a9c909d49669844 | SECTION_READ (abstract; sec. II; sec. III A; Table I, p. 104102-4 as a rendered image) + METADATA_VERIFIED (Crossref) |
| O4 | W. D. Rau, F. H. Baumann, J. A. Rentschler, P. K. Roy, A. Ourmazd, "Characterization of stacked gate oxides by electron holography", Appl. Phys. Lett. 68, 3410-3412 (1996), DOI 10.1063/1.115776 | CLOSED (OpenAlex closed; pubs.aip.org Cloudflare 403). Only the OpenAlex abstract index was seen | METADATA_VERIFIED (Crossref) + ABSTRACT(index) only: content UNVERIFIED |
| O5 | Y. C. Wang, T. M. Chou, M. Libera, T. F. Kelly, APL 70, 1296 (1997) (WANG97, already in references.bib) | CLOSED (pubs.aip.org 403). Its SiO2 value is read here second-hand in O2 | METADATA_VERIFIED (references.bib); value SECTION_READ of O2's statement only |
| O6 | A. Basha, G. Levi, T. Amrani, Y. Li, G. Ankonina, P. Shekhter, L. Kornblum, I. Goldfarb, A. Kohn, "Elastic and inelastic mean free paths for scattering of fast electrons in thin-film oxides", Ultramicroscopy 240, 113570 (2022), DOI 10.1016/j.ultramic.2022.113570 | CLOSED (OpenAlex closed); abstract read in Europe PMC (PMID 35700667; `l8/epmc_35700667.json`, SHA-256 3310931d...acc) | +ABSTRACT(PubMed) + METADATA_VERIFIED (Crossref) |

### 1.2 Facts extracted

Mean inner potential (MIP) of amorphous SiO2:
* O1 (abstract; sec. 3, p. 1131; Fig. 5; conclusion (2)): off-axis holography of "Spherical amorphous SiO2 particles"
  (220-270 nm diameter, dispersed from butyl alcohol onto a carbon microgrid, sec. 2 and p. 1130) in a JEM-3000F FEG
  TEM "being operated at 300kV" with a 30 V biprism, 0.45 nm fringe spacing (sec. 2, pp. 1129-1130): "the mean inner
  potential of amorphous SiO2 was determined to be 11.5±0.3 V" (p. 1131). Fig. 5 compares the measured phase with
  curves for U = 10.5, 11.5 and 12.5 V; the phase accuracy is "±0.06π" (p. 1131). A phase of 2.73π at the 50th fringe
  where the sphere thickness is 113 nm gave the first estimate 11.5 V (pp. 1130-1131).
  REPRODUCED here: sigma(300 keV) = 6.526e-3 rad V^-1 nm^-1, so sigma U t = 6.526e-3 x 11.5 x 113 = 8.48 rad = 2.70 pi
  (printed 2.73 pi).
* O2 (sec. 16.2, p. 772): "Experimental measurements of V0 have been obtained from 20-40 nm-diameter Si nanospheres
  coated in layers of amorphous SiO2 [16.64]. The mean inner potential of crystalline Si was found to be 12.1 ± 1.3 V,
  that of amorphous Si 11.9 ± 0.9 V, and that of amorphous SiO2 10.1 ± 0.6 V." [16.64] is Wang, Chou, Libera, Kelly,
  APL 70, 1296-1298 (1997) (O2 reference list). Also p. 772: "wedge-shaped Si samples with stacked Si oxide layers on
  their surfaces were used to measure the mean inner potentials of the oxide layers [16.63]" = O4 (no value printed
  in O2). O2 p. 773: measurements of V0 may also be affected by "the chemical and physical state and the
  crystallographic orientation of the specimen surface [16.76], and specimen charging [16.77-82]". O2 p. 772 (Eq.
  16.12 context): independent-atom values of V0 "are invariably overestimated as a result of bonding".
* O4: no value is taken from it (only a search-index abstract was seen, which is not evidence; the AIP page is
  blocked). Upload item 2.

Inelastic mean free path (IMFP) at 200 keV:
* O1 (abstract; p. 1130; conclusion (1)): EELS of the amorphous SiO2 spheres on a JEM-2010 with an omega filter at
  200 kV, 5 nm probe, 30 particles: "the mean free path(λp) at 200kV under the condition of no objective aperture was
  evaluated to be 178±4nm"; at 100 kV "100±2nm under no objective aperture condition", consistent with the 99 nm of
  Egerton's book (O1 ref. 4). O1 (p. 1130) also warns that for t/λp below about 0.1 "surface excitations may be
  significant and would cause an overestimate of thickness".
* O3 (sec. II, p. 104102-2): 200 kV JEOL 2500SES STEM with an Enfina spectrometer, "The excitation and collection
  semiangles were set to 20 mrad"; thickness from the Kramers-Kronig sum rule or from layered FIB cross-sections
  calibrated with lambda(c-Si) = 145 nm. Table I (p. 104102-4; "Accuracies are ~5%-10% for λ and ~10%-30% for λP"):
  Si lambda = 145 nm, lambda_P = 168 nm; SiO2 lambda = 155 nm. Sec. III A (p. 104102-2): "The largest variation was
  observed for oxides of light elements, such as SiO2, Al2O3, and B2O3: λ for amorphous phase was 10% larger than for
  the crystalline. We attribute this effect to the smaller mass density ... Therefore, single crystalline regions were
  selected for all the measurements." So the Table I SiO2 value refers to crystalline SiO2.
* O6 (abstract, Europe PMC): total inelastic MFP of Si "(β∼157 mrad) ... of 145 ± 10 nm for 200 keV electrons";
  elastic and inelastic MFPs measured at 200 and 80 keV versus collection angle for "SiO2 (Thermal, CVD)" among other
  oxides; the SiO2 numbers are in the closed body (upload).

### 1.3 Inferences (DERIVED_HERE unless stated)

* Measured MIP of amorphous SiO2 spans 10.1 ± 0.6 V (amorphous SiO2 layers on 20-40 nm Si spheres, O2 citing O5; the
  layer thickness is not stated in O2 and O5 is unread)
  to 11.5 ± 0.3 V (220-270 nm amorphous SiO2 spheres, O1); the two differ by 1.4 V, about twice their combined 1-sigma
  (0.67 V). Neither is a plasma-grown oxide on Si(001). A defensible bracket for a thin oxide on Si is 10.1-11.5 V
  (centre 10.8 V, half-range 0.7 V). O4 (thermal and deposited gate oxides on Si) is the most relevant measurement
  but is unread (upload item 2).
* A-SiO2 electronic absorption for the continuum layer, from the IMFP with the L6 relation V' = 1/(2 sigma Lambda)
  (sigma = 7.2884e-4 rad V^-1 A^-1): Lambda = 1780 A (O1, amorphous, no aperture) gives V' = 0.385 V; Lambda = 1550 A
  (O3, crystalline SiO2, 20 mrad) gives 0.443 V; Lambda = 1.1 x 1550 = 1705 A (O3's "10% larger" for the amorphous
  phase) gives 0.402 V. Proposed bracket: V'(inelastic, a-SiO2) = 0.38-0.44 V, nominal 0.40 V. These are total
  inelastic (all losses, large collection angle) values, i.e. an upper bound for what removes electrons from a 3 mrad
  dark-field aperture in the coherent channel: plasmon-loss electrons stay inside the aperture (characteristic angle
  well below 1 mrad) and are partly coherent (E6 M2, Tanishiro 2003), so the same caveat as for Si (E6 M3) applies.
* Cross-check of L6's Si electronic term (outside this task, reported because it bears on item 21): O3 gives, at 200
  keV and 20 mrad, lambda(Si) = 1450 A (total) and lambda_P(Si) = 1680 A; O6 gives 1450 ± 100 A at 157 mrad. These
  correspond to V' = 0.473 V (total) and 0.408 V (plasmon), below L6's 0.653 V (Mendis 2019's 1050 A, UNVERIFIED).
  The bracket 0 / 0.65 V of B6 (ii) is not contradicted, but its upper end is above both measured totals.
* Elastic scattering by the amorphous network out of the 3 mrad aperture is a second loss channel of the specular wave
  that an atomistic overlayer produces explicitly but a continuum layer does not. O6 measured elastic MFPs of thermal
  and CVD SiO2 at 200 keV versus collection angle (abstract); the numbers are in the closed body. Until then the
  continuum layer carries no elastic-scattering loss (ASSUMPTION), and the atomistic layer is the check.

## 2. O2/Ar plasma cleaning of air-exposed, ion-milled Si: oxide growth, carbon removal, sputtering (task 1)

### 2.1 Sources read

| # | Source | Access, URL, SHA-256 | Label |
|---|---|---|---|
| P1 | E.A. Fischione Instruments, "Model 1020 Plasma Cleaner specifications", Document SP1020 Rev. 02 (05/2025), and "Model 1020 Plasma Cleaner" brochure PB1020 Rev. 02 (10/2014) (manufacturer documents, no DOI) | OPEN: `https://www.fischione.com/files/products/17/sp1020%2epdf` (SHA-256 cd77bf838ca3b30913a6f01a98407ebc30387b0a8e3acf8914dacda39aec0b33) and `.../pb1020%2epdf` (5abf7728d49164b2e8c3c3cf5afae5c3cdad8d2e5dd47e4ec828d405a22978c1); product page `https://www.fischione.com/products/m1020` | SECTION_READ (manufacturer's claims; not independently tested) |
| P2 | T. C. Isabell, P. E. Fischione, C. O'Keefe, M. U. Guruz, V. P. Dravid, "Plasma Cleaning and Its Applications for Electron Microscopy", Microsc. Microanal. 5(2), 126-135 (1999), DOI 10.1017/S1431927699000094 | CLOSED (OpenAlex closed); abstract read in Europe PMC (PMID 10341012; `l8/epmc_isabell1999.json`, SHA-256 13a6d360...afc) | +ABSTRACT(PubMed) + METADATA_VERIFIED (Crossref) |
| P3 | M. Kitajima, "Ellipsometric Study on Plasma Oxidation of Silicon" (シリコンのプラズマ酸化の偏光解析研究; review in Japanese), J. Vac. Soc. Jpn. (Shinku) 37(10), 815-825 (1994), DOI 10.3131/jvsj.37.815 | OPEN (J-STAGE): `https://www.jstage.jst.go.jp/article/jvsj1958/37/10/37_10_815/_pdf/-char/ja`; read in full (text layer; p. 823 read as a rendered image); SHA-256 7af71bf3898d379e366c27f36f247105c90462c0317faedc7273c62347c90009 | SECTION_READ (secs. 2-10, Figs. 3, 6, 15, 16, 18) + METADATA_VERIFIED (Crossref) |
| P4 | R. E. Robinson, R. L. Sandberg, D. D. Allred, A. L. Jackson, J. E. Johnson, W. Evans, T. Doughty, A. E. Baker, K. Adamson, A. Jacquier, "Removing Surface Contaminants from Silicon Wafers to Facilitate EUV Optical Characterization", Society of Vacuum Coaters, 47th Annual Technical Conference Proceedings (Dallas, 24-29 April 2004), pp. 368-376 (no DOI found in Crossref) | OPEN (author group's site): `https://physics.byu.edu/faculty/allred/docs/svc04.pdf`; read in full; SHA-256 99574c40268d5c47c89f6ed16fc65284b11739ba58a518ebe140c23c3f9a6172 | SECTION_READ (pp. 370-373, Figs. 4-5); bibliographic data from the PDF itself only (no registry record) |
| P5 | D. R. G. Mitchell, "Contamination mitigation strategies for scanning transmission electron microscopy", Micron 73, 36-46 (2015), DOI 10.1016/j.micron.2015.03.013 | Accepted manuscript at University of Wollongong Research Online (figshare 27792012; licence "Copyright - All rights reserved", file openly downloadable): `https://ndownloader.figshare.com/files/50561283`; SHA-256 f6b4c5c4eb893f23926d7dc408add3e093d8f3746fb4e406fc3dfd0a62a55d3f | SECTION_READ (AM secs. 2, 3.4, 3.6, 3.7, 4; AM pages 3, 5-6, 8-10, 12, 14) + METADATA_VERIFIED (Crossref) |
| P6 | Y. Yamamura, H. Tawara, "Energy dependence of ion-induced sputtering yields from monatomic solids at normal incidence", At. Data Nucl. Data Tables 62(2), 149-253 (1996), DOI 10.1006/adnd.1996.0005; read as the report NIFS-DATA-23 (National Institute for Fusion Science, 1995) | OPEN (NIFS repository, hdl 10655/0002000175): `https://nifs-repository.repo.nii.ac.jp/record/2000175/files/NIFS-DATA-023.pdf`; scanned; pp. 3-7 and 14 read as rendered images; SHA-256 4b34eaebc581767f58b874db5767ef38a49ecfff8ad5ecf38bd9e542e0201ac3 | SECTION_READ (report pp. 5-7, Eqs. (9), (18), (19); Table 1 p. 14) + METADATA_VERIFIED (Crossref, journal version; the report and the journal version are assumed to carry the same Eq. (18) and Table 1: ASSUMPTION) |
| P7 | N. Luhmann et al., "Effect of oxygen plasma on nanomechanical silicon nitride resonators", arXiv:1706.02957v1 (2017) | OPEN (arXiv PDF); SHA-256 aa400ae88607e65dd8afbd52a59c0028196dc00a16f953e8dddbd34a6cd3bd11 | SECTION_READ (abstract; sec. II; sec. III pp. 2-4). Silicon NITRIDE, not Si: context only |
| P8 | S. Hata (Crossref lists one author; CiNii lists H. Sosiati, S. Hata, N. Kuwano, M. Itakura, T. Nakano et al.), "Removing focused ion-beam damages on transmission electron microscopy specimens by using a plasma cleaner", J. Electron Microsc. 55(1), 23-26 (2006), DOI 10.1093/jmicro/dfl001 | CLOSED; not in Europe PMC; only the OpenAlex abstract index seen | METADATA_VERIFIED (Crossref, CiNii) + ABSTRACT(index) only: content UNVERIFIED (upload item) |

### 2.2 Facts extracted

What a typical TEM plasma cleaner does (manufacturer, P1):
* SP1020: "High frequency (13.56 MHz) oscillating field system coupled to a quartz and stainless steel plasma chamber";
  "Ion energies less than 12 eV"; gas "25% oxygen and 75% argon"; ultimate vacuum 1e-7 mbar.
* PB1020 p. 3: "A low-energy, inductively coupled, high-frequency plasma effectively cleans a specimen surface without
  changing its elemental composition or structural characteristics. Highly contaminated specimens can be cleaned in 2
  minutes or less." PB1020 p. 4: "The plasma ions impinge upon the surface with energies of less than 12 eV, which is
  below the specimen's sputtering threshold. Cleaning occurs when reactive gas compounds formed by the plasma chemically
  react with carbonaceous material"; "Fischione recommends a mixture of 25% oxygen and 75% argon to optimize cleaning";
  the plasma cleans "with negligible heating".
* P2 (abstract): TEM "shows an elimination of the carbonaceous contamination from the specimen"; after cleaning,
  specimens "may be examined in the electron microscope for several hours without exhibiting evidence of
  recontamination". Nothing about oxidation of the specimen in the abstract.
* The manufacturer's "no change to composition" statement concerns bulk composition; it does not address the growth of
  a nanometre oxide on Si (P3, P4 below show that oxygen plasmas oxidise Si at room temperature).

Sputtering thresholds (P6), to test the "below the sputtering threshold" claim:
* NIFS-DATA-23 p. 7, Eq. (18): E_th/U_s = 6.7/gamma for M1 >= M2, and (1 + 5.7 (M1/M2))/gamma for M1 <= M2; Eq. (19)
  (p. 8): gamma = 4 M1 M2 / (M1 + M2)^2. Table 1 (p. 14): Si U_s = 4.63 eV (Q 0.66, W 2.32, s 2.5).
* DERIVED_HERE: Ar+ on Si (M1 = 39.948, M2 = 28.086): gamma = 0.9696, E_th = 32.0 eV; O+ on Si (M1 = 15.999):
  gamma = 0.9248, E_th = 21.3 eV. Both exceed the manufacturer's "< 12 eV" ion energy, so physical sputtering of Si by
  the Ar component is not expected IF the ion energy claim holds for Ali's cleaner (it depends on the plasma potential
  and on whether the holder is grounded or floating; Kitajima (P3 p. 822) reports V_p - V_f of about 15 V for a
  floating sample in an RF oxygen plasma). SiO2 thresholds were not found; normal-incidence fits only.

Room-temperature plasma oxidation of Si (P3, review with the author's own RF work):
* p. 816 (Fig. 3): plasma oxidation rate far exceeds thermal oxidation (ECR, 2.7e-2 Pa O2, 140 W, ex-situ
  ellipsometry).
* p. 818, sec. 5: "プラズマ酸化中の膜厚変化は，酸化初期を除き，酸化時間の1/2乗で変化することが確かめられている" (apart
  from the initial stage the thickness grows as t^(1/2)); for thick films (> 2-3 nm) O- transport through the oxide
  limits the rate (p. 820, sec. 9-10).
* p. 820: under -20 V bias growth tends to stop at about 5 nm (Hess et al., as cited); activation energies 0.19, 0.4,
  0.25 eV (Joseph, Kimura, Vinckier, as cited): weak temperature dependence.
* pp. 820-821, sec. 7: at room temperature, 2 Pa O2, RF 300 and 500 W, Si(111) oxidises faster than Si(100) at all
  times up to 1000 s.
* pp. 821-822, sec. 8 (Hu et al., as cited): spectroscopic ellipsometry of plasma-oxidised Si fits best with SiO2 on
  top of a damaged interlayer of (a-Si + SiO2); 3/4 of the interlayer thickness forms within seconds; its a-Si fraction
  is 50 % (positive bias) or 75 % (negative bias), "正イオンのイオン衝撃による損傷を示唆している" (suggesting damage by
  positive-ion bombardment). p. 824: the interface also contains suboxides (SiO, Si2O3).
* p. 822, sec. 9, Fig. 16 (p. 823): low-density RF oxygen plasma (2.0 Pa; 200, 300, 500 W; plasma density 6.4e7 to
  2.2e8 cm^-3; the sample about 1 m from the coil; floating, V_p - V_f about 15 V), starting from HF-dipped Si annealed
  at 600 C in UHV (sec. 3, p. 818): "酸化膜の膜厚は実験終了時でも＜1.5nmと極めて薄い" (the oxide is still thinner than
  1.5 nm at the end of the experiment); Fig. 16 runs to 10^4 s, with a fast initial rise and a slow later rise of the
  ellipsometric delta.
  Figure reading (approximate, Fig. 16 rendered at 220 dpi; DERIVED_HERE): at 600 s delta is about 1.3 deg (200 W),
  2.2 deg (300 W) and 2.7 deg (500 W), i.e. about 40 %, 55 % and 70 % of the values at 10^4 s (3.4, 4.0, 4.0 deg). If
  delta is linear in thickness (thin-film limit, ASSUMPTION), 10 min of this plasma grows less than about 0.6-1.0 nm on
  an initially oxide-free surface.

O2 plasma on native-oxide-covered Si wafers (P4):
* p. 371: native oxide of the wafers "usually 1.6 to 1.9 nm" (ellipsometry); a Matrix commercial plasma etcher, "RF
  power of 250 Watts, 0.120 Torr of pressure, and an oxygen flow of 0.75 SCCM", chuck heating off.
* p. 372: about 1 nm of organic test layer (DADMAC) "was removed extremely rapidly. The shortest time used removed all
  the DADMAC"; about 2 A of contaminants re-accumulated during 20-40 min in transit to the ellipsometer.
* p. 373: "with increased exposure to the plasma, the "apparent oxide" thickness increases"; XPS shows no carbon, so
  the increase "must be due to oxide growth"; "O2 plasma processes is too aggressive for its use in general organic
  cleanup for our applications".
* Fig. 4 (p. 372), read off the plot rendered at 250 dpi (approximate): the change in apparent thickness is about -8
  to -10 A at 0.1-3 min (organic layer removed; the paper notes an upper and a lower trend differing by about 2 A of
  re-adsorbed contamination), about -6 A at 4-6 min, -4 A at 10 min, -1 A at 12 min and -2 A at 16 min. So the oxide
  grew by about 0.4-0.6 nm in 10 min and 0.7-0.8 nm in 12-16 min on top of a 1.6-1.9 nm native oxide (DERIVED_HERE
  from a figure; no table given).

Carbon removal on ion-milled Si (P5):
* AM p. 3, sec. 2: a JEOL EC-52000IC air plasma, DC 310 V, specimen about 1 cm outside the glow ("very gentle
  cleaning conditions"), 1.1 C temperature rise after 1 h.
* AM p. 9, sec. 3.6: "Plasmas containing oxidising species have been shown to be very effective at removing both
  hydrocarbons and any previously deposited carbon contamination. Air, pure oxygen, oxygen/argon and oxygen/hydrogen
  mixtures have all been used." "where valence state is being studied, oxidation may occur". Carbon film removal rate
  "approximately 5nm.hr-1" in this cleaner.
* AM pp. 9-10 and 12 (Fig. 10b): on an ion-milled Si DRAM cross-section the contamination deposited in a 30 s scan at
  20 Mx "decreases exponentially with plasma cleaning time and can be completely eliminated by plasma cleaning for 60
  mins"; "Contamination was still significant after 10mins of plasma cleaning with 22.5nm of carbon deposited within a
  30s scan". AM p. 10: "Higher power cleaners or those using oxygen-based plasmas may operate more rapidly".
* AM p. 9: "Low voltage milling (<500eV) is very effective final polishing step to remove amorphous/oxide and
  beam-damaged layers" (citing Mehrtens et al. 2012; not read).

Context (P7, silicon nitride, not Si): a parallel-plate RIE (STS 320PC, 49.5 sccm O2, 20 Pa) grew "An oxide layer of
1.5 nm ... in just 10 s in a 50 W oxygen plasma" on Si3N4 (abstract; sec. II), and the authors cite logarithmic
room-temperature growth (their ref. 33, Kim et al., JVST B 14, 2667 (1996), not read). An RIE with self-bias is far
more aggressive than an ICP TEM cleaner; this is an upper-end illustration only.

### 2.3 Inferences for Ali's preparation (DERIVED_HERE unless stated)

* A 10 min O2/Ar clean in a TEM cleaner oxidises the Si surface further; no source found measures the thickness grown
  by a TEM ICP cleaner on Si. Bounding evidence: a low-density RF O2 plasma grows less than 1.5 nm in 10^4 s from a
  bare surface (P3), less than about 0.6-1.0 nm in 10 min by figure reading; a 250 W O2 plasma etcher adds about 0.4-0.6 nm in 10 min (0.7-0.8 nm in
  12-16 min) to a 1.6-1.9 nm native oxide (P4). Growth slows as the oxide thickens (t^(1/2) or logarithmic; P3, P7). The
  25 % O2 of the Fischione mix lowers the oxygen supply relative to pure O2 (the effect on rate is not quantified in
  any source read).
* Before plasma: the air-exposed ion-milled surface carries a native oxide of about 0.5-1 nm (thermal-oxide-equivalent,
  XPS; Morita 1990 via L7 D1) or 1.6-1.9 nm (ellipsometric "native oxide" of commercial wafers, P4, which may include
  adsorbed hydrocarbons). Whether amorphised Si oxidises faster than crystalline Si in air or plasma was not found
  (ASSUMPTION: same).
* Resulting estimate for the oxide after the 10 min clean: 1.5-3 nm total (nominal 2 nm), with an uncertainty of about
  ± 1 nm that only a witness measurement can remove (PROJECT_INPUT). Below the oxide, any a-Si left by the milling
  (L7 D2/D3) remains unless it is fully oxidised; a plasma-damaged (a-Si + SiO2) interlayer and suboxides are expected
  at the interface (P3).
* Carbon: an oxidising plasma removes hydrocarbons, but removal time depends strongly on the cleaner: "2 minutes or
  less" (manufacturer, P1), still significant after 10 min and gone after 60 min in a gentle air plasma (P5). Ali's 10
  min in an ICP O2/Ar cleaner most likely removes most adsorbed hydrocarbon (ASSUMPTION); readsorption in air or in the
  microscope then restarts (L7 D6: 0.005-0.013 nm/h in air). A residual 0-0.2 nm carbon layer is the sourced range
  (L7 D6; P4's 2 A in 20-40 min).
* Sputtering and roughness: with ions below 12 eV (P1) and thresholds of 21 eV (O) and 32 eV (Ar) on Si (P6), no
  physical sputtering is expected; no source read measured the roughness change of Si by a TEM cleaner. The
  roughness is then set by the milling and by the oxidation front (section 3).

## 3. Reflection through thin amorphous oxide on Si; the SiO2/Si interface and atomic steps (task 3)

### 3.1 Sources read

| # | Source | Access, URL, SHA-256 | Label |
|---|---|---|---|
| R1 | H. Watanabe, N. Miyata, M. Ichikawa, "Layer-by-Layer Oxidation of Si Surfaces" (シリコン表面のLayer-by-Layer酸化), Hyomen Kagaku 20(4), 250-255 (1999), DOI 10.1380/jsssj.20.250 | OPEN (J-STAGE `.../jsssj1980/20/4/20_4_250/_pdf/-char/ja`); read in full (text layer); SHA-256 8fb5646d696266bb617b3cf56e8253a2650c23d3071f13b41528087bb823257c | SECTION_READ (abstract; secs. 2, 3.1-3.3; Figs. 1-7 captions) + METADATA_VERIFIED (Crossref) |
| R2 | H. Watanabe, N. Miyata, M. Ichikawa, "シリコン表面の原子層単位の酸化反応" (Layer-by-layer Oxidation of Si Surfaces), Butsuri (J. Phys. Soc. Jpn. members' journal) 55(11), 846-853 (2000), DOI 10.11316/butsuri1946.55.846 | OPEN (J-STAGE); scanned; pp. 846-850 and 853 read as rendered images; SHA-256 d0df5d6e951101282405c86ec12c7b5e7524936a983ba118688a3188fb105487 | SECTION_READ (secs. 1.2, 2.1, 2.2, 3, 3.1, 3.2; Figs. 2-8; refs.) + METADATA_VERIFIED (JaLC; not in Crossref) |
| R3 | M. Ichikawa, "シリコン表面界面のナノスケール観察技術" (nanoscale observation of Si surfaces and interfaces), J. IEE Japan 122(2), 87-89 (2002), DOI 10.1541/ieejjournal.122.87 | OPEN (J-STAGE); read (text layer); SHA-256 aa741254a9bca13cf978f45d221b94bb8a49eb92c4dc11cbe82b3738bc071b42 | SECTION_READ (secs. 2, 3.1, pp. 87-88) + METADATA_VERIFIED (Crossref; record lacks authors and carries the issue's feature title; the J-STAGE page gives author and title) |
| R4 | Y. Takakuwa, "Growth Kinetics of Very Thin Oxide Layers on Si(001) Surface Monitored in Real-time by Auger Electron Spectroscopy Combined with Reflection High Energy Electron Diffraction", Hyomen Kagaku 23(9), 536-552 (2002), DOI 10.1380/jsssj.23.536 | OPEN (J-STAGE); read (text layer) pp. 536-543; SHA-256 c5d5660c26165178362e14e728cb49db93ebaccfb9f82b16d6e869af9eb0675a | SECTION_READ (abstract; sec. 3 p. 540; sec. 4.1 p. 543; Fig. 6) + METADATA_VERIFIED (Crossref) |
| R5 | K. Honda, A. Ohsawa, "Reflection Electron Microscopy Observation of the Silicon Wafer Surface" (シリコンウエハ表面の反射電子顕微鏡法による観察), J. Vac. Soc. Jpn. (Shinku) 31(9), 783-788 (1988), DOI 10.3131/jvsj.31.783 | OPEN (J-STAGE); read in full (text layer; p. 786 as a rendered image); SHA-256 e062774d0a9f0ae574a30fe8fabc6f54c07f7b43dc8269b717b88f6bd23aa9e2 | SECTION_READ (abstract; secs. 2-4; Figs. 2-6) + METADATA_VERIFIED (Crossref) |
| R6 | T. Hattori, "Studies on Ultrathin Silicon Oxide Films and Their Current Problems" (極薄シリコン酸化膜に関する研究の現状と課題), J. Vac. Soc. Jpn. 44(8), 695-700 (2001), DOI 10.3131/jvsj.44.695 | OPEN (J-STAGE); read (text layer); SHA-256 e54d0ded81fb63f10394620e128a6d3da2fd89e0603230f085d14856d6e2cd3a | SECTION_READ (sec. 3, p. 697; refs. 42, 43) + METADATA_VERIFIED (Crossref; the record has no title field) |

### 3.2 Facts extracted

What an amorphous oxide does to the reflected beam (electron energies 10-200 keV):
* R3 p. 87 (SREM, 30 kV, 2-3 nm probe, 2-3 deg): "Si酸化膜は結晶ではなく非晶質であるため，電子線は酸化膜中では回折されず，強度が
  非弾性散乱により一様に減少する。電子線は結晶であるSi基板に到達して初めて回折され，再び酸化膜を通過して試料表面から放出される。"
  (the amorphous oxide does not diffract; the intensity is reduced uniformly by inelastic scattering; the beam is
  diffracted only by the crystalline Si and crosses the oxide again on exit.) This is a simplification: an amorphous
  layer also scatters elastically into a diffuse background (R4 below; L7 D8).
* R1 p. 251: "非晶質である酸化層は鏡面反射スポットには寄与しない。したがって，SREMでは酸化膜厚が数ナノメータ以下であれば，酸化膜を
  剥ぎ取ることなしにSiO2/Si界面を直接観察することができる。" (the amorphous oxide does not contribute to the specular spot;
  for oxides of up to a few nanometres SREM images the SiO2/Si interface directly without stripping the oxide.) R2 p.
  847 repeats it for "数nm程度" (about several nm).
* R4 p. 540 (10 keV, [100] azimuth, about 3 deg): the oxide gives "構造のないハローパターン" (a structureless halo), and
  "酸化膜の存在にもかかわらず界面平坦性についての情報が鏡面反射スポット強度I(0,0)に強く反映される" (despite the oxide, the
  interface flatness is strongly reflected in the specular intensity I(0,0)). R4 p. 543 (549 C, 2.8e-6 Torr O2):
  I(0,0) falls almost linearly with oxide coverage to about 50 % coverage, then recovers (sub-monolayer oxidation;
  roughness, not absorption, dominates at this stage).
* R2 p. 849 (Fig. 6): during first-layer oxidation of Si(001) the specular spot intensity (off-Bragg condition) falls
  from about 350 (clean) to a minimum at 0.5 ML and recovers to about 100 when the first layer is oxidised; "界面が酸化膜
  により下層に埋め込まれるため，3周期以降のRHEED強度の振動現象を観測することはできなかった" (oscillations beyond the third period
  could not be observed because the interface is buried under the oxide). Beam energy not stated in the pages read.
* R5 (200 kV and 100 kV REM in an ordinary TEM, Fujitsu): Si(001) CZ wafers, cleaned and HF-dipped "観察直前に" (just
  before observation) (p. 784); beam "〔110〕方向にほぼ平行", REM images with 006, 008 and 0010 excited (006 and 0010
  forbidden, excited by double diffraction) (p. 785, Fig. 2); Fig. 3: "008反射による高分解能のREM像", 200 kV; fringe-like
  contrast near focus is phase contrast from electrons reflected by the upper and lower terraces of monatomic steps
  (p. 785); resolution limit from surface-plasmon chromatic blur with C_c = 2.0 mm and 11.6 eV: 1.1 nm at 100 kV, 0.65
  nm at 200 kV (p. 784). Roughness of polished wafers 1.2-1.6 nm high, 200-500 nm period (100 kV, 006; p. 786).
  Through oxide (p. 786): "通常のデバイスの酸化膜厚は薄い場合でも10nm以上ある. 極めて浅い角度(1度程度)で入射した場合, 電子線が
  通過しなければならない距離は0.5μm以上になり酸化膜の影響が無視できなくなる. 薄い酸化膜はアモルファスと考えられるので反射回折に影響
  しない. 但し酸化膜を電子線が通過する際に非弾性散乱を受けてエネルギーのぼけを生じる." with dE = (dE1^2 + dE2^2)^(1/2) (surface
  plasmon and absorption terms), so "界面を観察するためには, 酸化膜を薄くするか, 除去してしまう必要がある"; native oxide regrowth
  after HF was "0.5 nm/h 以下" (p. 786). After 20 nm thermal oxidation at 1000 C and HF stripping, the interface REM
  (100 kV, 006) shows roughness below 1.0 nm with about 10 nm period, "界面の凹凸は酸化前の表面凹凸とあまり変わりがない"; after
  200 nm, 4-6 nm high with about 1 um period (p. 786, Fig. 5); after Cu+ implantation (1e15 cm^-2) and oxidation,
  5-15 nm high, 0.5-2 um period, stacking faults (pp. 786-788, Fig. 6).

Does oxidation keep the step structure? (all on UHV-clean or HF-last surfaces, thermal oxidation):
* R1 p. 251 (Si(111), about 1 nm oxide, 720 C, 1e-4 Torr O2, 60 min; the same area imaged before and after with an
  SiC island as marker): "酸化膜界面には初期の表面構造が保存され，原子スケールで平坦なテラスとステップが存在する"; "酸化に際して界面の
  ステップは面内方向に移動しない"; STM of the about 1 nm oxide surface shows steps "約0.3nm" high: "酸化前の初期表面の構造が酸化膜
  表面にも保存されている". Summary (p. 251-252, Fig. 3): (1) the initial atomic steps are preserved at the interface
  AND at the oxide surface; (2) interface steps do not move laterally; (3) terraces appear uniform in SREM. Mechanism:
  random 2-D nucleation of oxide islands below 10 nm and their lateral growth (p. 252).
* R1 p. 252: a 48 nm oxide grown at 900 C in a furnace on a UHV-prepared Si(111) (0.3 nm cap) still shows "明瞭な
  ステップとテラス構造" at the interface, steps not moved; terrace contrast non-uniform, i.e. atomic-scale roughness
  within terraces; RHEED (1,1) spot-profile fit: 2-D oxide nuclei of 5 nm diameter and one atomic layer thick.
* R1 p. 253 and R2 p. 848, Fig. 3: on Si(001)-2x1 the 2x1 streaks and the SREM terrace contrast vanish on O2 exposure,
  then the terrace contrast reappears (room temperature, 2e-6 Torr, 3 min) and reverses with each further oxidised
  layer while the terrace shapes are kept; R2 p. 848: "シリコン結晶基板が原子層ごとで非晶質酸化膜に変換する過程を観測している"
  (the crystal is converted into amorphous oxide one atomic layer at a time), and a uniform-thickness oxide over the
  whole field of view is inferred from the uniform contrast reversal.
* R2 p. 848, Fig. 4: a dynamical calculation of the specular intensity (angles 1.4-2.2 deg) for an abrupt interface
  between amorphous oxide and bulk-terminated Si(001) gives very different intensities for the two interface terrace
  types (Type A and Type B, different bond direction relative to the beam), "ブラッグ条件付近(矢印)で大きく異なる". R3 p. 88:
  the specular intensity is higher when the interfacial Si bond direction is parallel to the beam than when it is
  perpendicular.
* R2 p. 850, Fig. 7: STM after stripping 2-ML and 3-ML oxides with HF: after completed layers the interface is
  atomically flat with single steps; during the third-layer oxidation, 2-5 nm single-layer islands at under 10 nm
  spacing. R2 p. 850: oxidation proceeds "常に約2倍の体積膨張を伴って" (always with about a twofold volume expansion).
* R6 p. 697 (review): the compositional transition is very abrupt (only the interfacial Si are in intermediate oxidation
  states); a structural transition layer of about 1 nm exists on the oxide side, with an XRR density "バルクのSiO2に比べて
  5%程度高い" (about 5 % above bulk SiO2; Sugita et al., Appl. Surf. Sci. 100/101, 268 (1996), not read); AFM: oxide
  surface roughness at most 0.314 nm on Si(111) and at most 0.135 nm on Si(100) (700 C), varying periodically with the
  interface structure; on Si(100) the oxide-surface roughness follows the interface until the oxide exceeds the
  transition-layer thickness.

### 3.3 Inferences (DERIVED_HERE unless stated)

* Oxide growth consumes Si: with rho(Si) = 2.329 g/cm^3 (a = 5.431 A) and rho(SiO2) = 2.10-2.30 g/cm^3 the Si consumed is
  0.42-0.46 of the oxide thickness (0.44 at 2.20 g/cm^3; volume expansion 2.2-2.4, consistent with R2's "約2倍"). A
  2 nm oxide moves the Si interface about 0.9 nm into the crystal and its top surface about 1.1 nm above the original
  surface (`l8/l8_numbers.py`).
* Conformal, not planarising, for thin oxides grown layer by layer at a moving interface: R1 (steps at the interface and
  0.3 nm steps on the surface of a 1 nm oxide, Si(111)), R2 (uniform layer-by-layer conversion on Si(001)) and R6
  (surface roughness tracking the interface) support a CONFORMAL oxide of uniform thickness over terraces separated by
  single-layer steps. Under E6 M4 this keeps the step phase at 2 k_perp h (10.976 rad for a/4 at 16.1347 mrad); the
  planarising limit would give 12.15-12.31 rad for V_ox = 10.1-11.5 V (`l8/l8_numbers.py`). None of these sources
  treats a room-temperature plasma oxide on an ion-milled surface; P3 (section 2) reports an ion-damaged (a-Si + SiO2)
  interlayer for plasma oxidation. The conformal model is therefore the sourced default for an oxide on a stepped
  crystalline surface (ASSUMPTION for Ali's surface), and the planarising model is the bracket.
* Terrace-type dependence under oxide: R2 Fig. 4 and R3 p. 88 show, at 30 kV and a <110>-type azimuth, that the
  specular reflectivity of an oxide-covered Si(001) depends on whether the interfacial bonds are parallel or
  perpendicular to the beam. This is the reflectivity difference that B4 says cancels only at an exact <100> azimuth
  (bonds at 45 deg on both terraces). It supports B4's statement that an overlayer and a <110> azimuth produce a
  residual delta, and gives a first-hand measurement-plus-calculation precedent for it (at 30 kV, not 200 kV).
* Visibility of steps under oxide: at 30 kV the interface steps and terraces are imaged through oxides of up to "a few
  nm" (R1, R2); at 200 kV with (008) and the beam near [110], monatomic-step phase contrast on HF-last Si(001) was
  imaged in an ordinary TEM (R5); R5 removed thick (>= 10 nm) oxides because of the chromatic blur. No source read shows
  REM or reflection holography of steps through a 1-3 nm plasma oxide at 200 kV; by R1-R5 it is expected to be possible
  if the crystal under the oxide keeps its steps (ASSUMPTION).
* Attenuation of the specular beam by the oxide (continuum, total IMFP, section 1.3; `l8/l8_numbers.py`): path in+out
  2t/sin(theta) = 124 t outside refraction, 2t/sin(theta') = 111 t inside the oxide (theta' = 17.9-18.1 mrad for
  V_ox = 10.1-11.5 V). Intensity factor exp(-path/Lambda) with Lambda = 1550-1780 A: t = 1 nm 0.45-0.54; 2 nm 0.20-0.29;
  3 nm 0.09-0.15 (amplitude 0.67-0.73, 0.45-0.54, 0.30-0.39). These are upper bounds on the loss from the coherent
  elastic channel (plasmon-loss electrons stay in the aperture and are partly coherent, E6 M2) and ignore elastic
  diffuse scattering out of the aperture (not sourced; O6 upload). Any a-Si left under the oxide attenuates further:
  with Lambda(Si) = 1450 A (O3), 2 nm of a-Si gives 0.18 and 5 nm 0.014 in intensity; tens of nm of FIB a-Si (L7 D2)
  would extinguish the specular beam. A measurable specular hologram on Ali's sample therefore itself indicates that the
  total damaged-plus-oxide layer is at most a few nm (inference).

## 4. Density, stoichiometry and interface layer of thin oxides on Si (task 2, second part)

### 4.1 Source read (in addition to R6 and L7 D7)

| # | Source | Access, URL, SHA-256 | Label |
|---|---|---|---|
| X1 | S. Komiya, N. Awaji, Y. Horii, H. Tomita, "全反射を利用して超薄膜を調べる" (X-ray total-reflection study of ultrathin films; Crossref title of the issue feature: "Frontiers in Crystallography with Synchrotron Radiation. Utilizing of Various Properties o..."), Nihon Kessho Gakkaishi 39(1), 89-93 (1997), DOI 10.5940/jcrsj.39.89 | OPEN (J-STAGE `.../jcrsj1959/39/1/39_1_89/_pdf/-char/ja`); text layer and pp. 91-92 as rendered images; SHA-256 33c08418c23110a57cd18f62468bfc61f8b649defef37f88b41008c11f9e59a9 | SECTION_READ (secs. 3, 3.1, 3.2; Figs. 3-4, Table 1) + METADATA_VERIFIED (Crossref) |

### 4.2 Facts extracted

* X1 p. 90 (XRR, synchrotron and laboratory): standard precision "膜厚：±0.01nm，密度：±0.01g/cm3，凹凸：±0.02nm".
  Thermal oxides of about 7 nm (HCl/O2, dry O2, O3; 800-1000 C) cannot be fitted with one layer; a two-layer model with a
  denser interfacial layer is needed (p. 90). Fig. 3 (p. 91): interfacial layer thickness about 8-14 A; Fig. 4 (p. 91):
  interfacial-layer density about 2.35-2.41 g/cm^3 and upper (bulk) layer about 2.20-2.36 g/cm^3 depending on process
  and temperature (read off the figures); interface roughness "0.2～0.3nm" independent of process (p. 91).
* X1 p. 92, Table 1 (chemical "native" oxides, about 1 nm, after different cleaning solutions): thickness / density:
  HCl:H2O2:H2O 1.13 nm / 2.07 g/cm^3; NH4OH:H2O2:H2O 1.07 / 2.11; HNO3 1.23 / 2.16; H2SO4:H2O2 1.04 / 2.23; O3 water 1.05 /
  2.21; UVO3/HNO3 1.44 / 2.25. The interfacial-roughness column is printed 2.1-5.1 with the unit "(nm)"; for 1-1.4 nm
  films and the p. 90 precision of ±0.02 nm these can only be angstroms (0.21-0.51 nm): unit misprint suspected
  (DERIVED_HERE). p. 92: the low-density films contain more Cl and OH groups (infrared absorption).
* R6 p. 697: an oxide-side structural transition layer of about 1 nm, about 5 % denser than bulk SiO2 (XRR, Sugita et
  al. 1996 as cited); compositional transition (suboxides Si1+ to Si3+) confined to the interfacial Si layer.
* P3 p. 824 (Kitajima): suboxides (SiO, Si2O3) exist at plasma-oxide interfaces; ellipsometric models with a-Si/SiO2
  mixtures ignore them.
* L7 D7 (Tokutake et al. 2015, plasma oxides at 750 C, 4.5-7 nm): 2.11-2.28 g/cm^3; layered 2.03 (surface 1.15 nm) /
  2.14 (bulk 2.56 nm) / 2.19 g/cm^3 (interface 0.98 nm). Checked here only as quoted by L7 and E6 (not re-read).
* O3 sec. III A: lambda of amorphous SiO2 is about 10 % larger than of crystalline SiO2, attributed to the smaller
  density of the amorphous phase.

### 4.3 Inferences (DERIVED_HERE)

* A sourced density range for a 1-3 nm oxide on Si is 2.07-2.28 g/cm^3 for the film (X1 Table 1, L7 D7), with a denser
  (2.35-2.41 g/cm^3, X1 Fig. 4; or +5 %, R6) interfacial layer of about 1 nm for thermal oxides. No XRR of an air-grown
  native oxide on an ion-milled surface, or of a room-temperature plasma oxide, was found. Nominal 2.20 g/cm^3, range
  2.07-2.30.
* Stoichiometry: SiO2 except for about one monolayer of suboxide at the interface (R6; P3). For a continuum model the
  suboxide is not resolvable in thickness (a fraction of a nanometre); for an atomistic model it is part of the
  interface construction (section 5).
* Mean inner potential versus density: the engine's own independent-atom potential (Kirkland parameterisation, abTEM
  1.0.10, called through the repository venv) gives F_Si(0) = 278.374 and F_O(0) = 95.264 V A^3, hence V0(a-SiO2) =
  n_SiO2 (F_Si + 2 F_O) = 9.87, 10.25, 10.34, 10.67, 10.81 V at 2.10, 2.18, 2.20, 2.27, 2.30 g/cm^3 (the same calculation
  gives 13.902 V for Si at a = 5.431 A, the engine's B32 value, which checks the method). Unlike Si (IAM 13.90 V against
  about 12.0-12.5 V measured), the IAM value for a-SiO2 at 2.2 g/cm^3 (10.34 V) lies INSIDE the measured range 10.1-11.5 V
  (O1, O2). A density error of ± 0.1 g/cm^3 moves the IAM value by about ± 0.47 V.

## 5. An openly available atomistic amorphous SiO2 model (task 2, atomistic overlayer)

### 5.1 Source read and data retrieved

| # | Source | Access, URL, SHA-256 | Label |
|---|---|---|---|
| A1 | L. C. Erhard, J. Rohrer, K. Albe, V. L. Deringer, "Modelling atomic and nanoscale structure in the silicon-oxygen system through active machine learning", Nat. Commun. 15, 1927 (2024), DOI 10.1038/s41467-024-45840-9 | OPEN, CC BY 4.0 (licence statement in the XML): Europe PMC full text `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10908788/fullTextXML` (PMC10908788); SHA-256 189ee4c3b8ea181e4fa61b5059a499da83c5c9847286bfd54309f789f90ba2c8 | SECTION_READ (abstract; Methods "quench simulations"; Data availability; Table 1; SiO results text) + METADATA_VERIFIED (Crossref) |
| A2 | L. C. Erhard, J. Rohrer, K. Albe, V. L. Deringer, "Research data for 'Modelling atomic and nanoscale structure in the silicon-oxygen system through active machine-learning'", Zenodo, DOI 10.5281/zenodo.10419194 (2024-02-15), licence CC BY 4.0 | OPEN: Zenodo API `https://zenodo.org/api/records/10419194` (record JSON read); `results.zip` (9.35 GB) NOT downloaded whole: its central directory was read by HTTP range requests (2533 entries, list `l8/zenodo_results_list.tsv`) and individual members extracted (`l8/zip_get.py`), each checked against the CRC-32 stored in the zip | SECTION_READ (record description, licence, file list) + REPRODUCED (density, stoichiometry, coordination of two models, below) |

### 5.2 Facts extracted

* A1 Data availability: "The potential parameter files, the reference data with SCAN labels, and additional supporting
  data (including LAMMPS scripts and input configurations) generated in thus study are openly available in the Zenodo
  repository at 10.5281/zenodo.10419194". A2 licence: cc-by-4.0. A2 description: results include "SiO2: Contains SiO2
  structural models generated by the hybrid approach and using only the ACE potential", "the small-scale Si-SiO2
  interface models", and the ACE potential files.
* A1 Methods (quench simulations): "randomisation part at 6000 K for 10 ps (NVT). Afterwards the temperature is
  immediately reduced to 4000 K and held there for 100 ps (NPT, zero external pressure). From there the melt is quenched
  with different quench rates to 300 K (NPT, zero external pressure). At this temperature the structure is equilibrated
  for another 10 ps. In case of 'hybrid' simulations these quenches have been performed using the CHIK potential and
  afterwards the structure has been equilibrated for another 20 ps with the ACE potential." Time step 1 fs, LAMMPS.
* A1 Table 1: energy/force RMSE of the complex ACE model on a-SiO2 test sets 2.2-4.6 meV/atom and 0.10-0.19 eV/A.
* Files retrieved (A2 `results.zip`; CRC-32 matched the zip directory):
  - `results/SiO2/ace/4.in.data` (18,629,181 bytes, CRC 2985f408, SHA-256 b45ffe7d8ac2dedf333ed148a819f54a9edc885474453639a015ad429fb8794d); run script `run.sh`: `-var p 0.0 -var c 1000000000000.0` (zero pressure, 1e12 K/s), ACE potential.
  - `results/SiO2/hybrid/hybrid.out.data` (44,457,778 bytes, CRC 92ce332a, SHA-256 2d11ced0e6e267459d550266457aaf1dbbbf010338f8e88e6c62153a9526ac28); CHIK quench (`pair_style hybrid/overlay buck/coul/long ...` in `quenching.in`) then ACE equilibration.
  - `results/SiO/interfaces/interfaces/a-SiO2_c-Si/<0-24>/SCAN/out.xyz`: 25 small a-SiO2/c-Si interface cells (the one read, #0, has 160 atoms, 96 Si and 64 O, lattice 10.8577 x 10.8577 x 23.3951 A = 2a x 2a laterally, c-Si layers at z = 0-10 A, oxide at 10-24 A; periodic in z).
* REPRODUCED here (script `l8/analyse_asio2.py`, repository venv numpy; minimum-image Si-O distances < 2.0 A for 2000
  random Si):
  - ACE model: 139,968 atoms (46,656 Si, 93,312 O; O/Si = 2.000), cubic box 128.716 A, density 2.183 g/cm^3, Si-O
    coordination 4.003 (99.8 % fourfold), mean Si-O 1.619 A (s.d. 0.033 A).
  - Hybrid model: 331,776 atoms (110,592 Si, 221,184 O), cubic box 168.390 A, density 2.311 g/cm^3, 100 % fourfold,
    mean Si-O 1.618 A.

### 5.3 Inferences for the engine (DERIVED_HERE; the orchestrator decides)

* Best open atomistic a-SiO2 found: A2's ACE model (CC BY 4.0, 12.9 nm cube, 2.18 g/cm^3, inside the sourced thin-oxide
  range 2.07-2.30). A 1-3 nm slab cut from it (normal along any cube axis) gives 12.9 nm x 12.9 nm of distinct
  amorphous structure; the engine's IAM V0 for it is 10.25 V (section 4.3). The hybrid (CHIK) model is denser (2.31)
  and would give 10.8 V; it is the high-density bracket.
* The engine's supercell is much longer along the beam than 12.9 nm (H2). Tiling the cube periodically imposes a 12.9 nm
  period on the amorphous layer, i.e. artificial diffraction at multiples of lambda / 12.87 nm = 0.195 mrad, inside
  the 3 mrad aperture. Mitigation options (ASSUMPTION, to be tested): tile with random rotations/translations per tile,
  or cut from the 16.8 nm hybrid cube, and compare speckle statistics between tilings. The seams need re-relaxation;
  A2 provides the ACE potential (CC BY 4.0) with which the published structures were made.
* The interface: A2's small SCAN-relaxed a-SiO2/c-Si cells (10.86 A laterally) are too small to tile under a
  reflection beam without introducing a 1.086 nm period, but they show a DFT-relaxed bonding motif at c-Si(001) and can
  seed a larger interface relaxed with the ACE potential. A simpler first step: place the cut slab on the bulk-terminated
  Si(001) staircase with a 0-1 A gap chosen so that the local density at the interface matches (ASSUMPTION), and test
  the phase against the continuum layer of the same V0 and thickness.
* The atomistic layer carries its own electronic-absorption deficit: frozen phonons produce TDS but not plasmon
  absorption, so the uniform electronic term (section 1.3, 0.38-0.44 V) must be added inside the oxide region just as
  L6 7.2 proposes for Si.

## 6. Charging of oxide-covered surfaces under grazing illumination (task 4, item 22)

* No source read measures charging of a 1-3 nm oxide on conducting Si under a grazing electron beam. The SREM/REM/RHEED
  studies of oxidised Si read here (R1-R5, L7 D8) image through oxides of up to a few nm (and R5 through none thicker
  than a native regrowth) without reporting charging; absence of a report is not evidence of absence.
* O2 p. 773: measurements of V0 by holography may be affected by "specimen charging [16.77-82]" (refs. read in O2's
  list: Lloyd et al. 1997; McCartney et al., APL 80, 3213 (2002); Downing, McCartney, Glaeser, MAM 10, 783 (2004);
  McCartney, J. Electron Microsc. 54, 239 (2005); Dunin-Borkowski et al., Ultramicroscopy 103, 67 (2005)); none read
  (closed, UNVERIFIED).
* Inference (DERIVED_HERE, ASSUMPTION-level): a 1-3 nm SiO2 on doped Si passes charge by tunnelling, unlike the thick
  insulators for which charging is known in holography; the magnitude of any residual surface charge under the
  footprint current is not sourced. B8 and item 22 stand: the phase drift versus dose/time on a flat region of Ali's
  sample is the required measurement.

## 7. Table: quantity | value | conditions | source | locator | label | open?

Units: A = angstrom. "open?" = readable here without Ali. DERIVED_HERE rows are computed in `l8/l8_numbers.py`
(output `l8/l8_numbers_output.txt`, SHA-256 6ca68910...866) or `l8/analyse_asio2.py` from the sourced inputs.

| Quantity | Value | Conditions | Source | Locator | Label | Open? |
|---|---|---|---|---|---|---|
| MIP of amorphous SiO2 | 11.5 ± 0.3 V | a-SiO2 spheres 220-270 nm, off-axis holography at 300 kV | Lee, Ikematsu, Shindo 2000 (O1) | p. 1131, Fig. 5, concl. (2) | SECTION_READ | open |
| MIP of amorphous SiO2 | 10.1 ± 0.6 V | amorphous SiO2 layers on 20-40 nm Si spheres (layer thickness not stated in O2) | Wang et al. 1997 via Dunin-Borkowski et al. 2019 (O2 = C02) | O2 p. 772 | SECTION_READ of O2's statement; Wang 1997 UNVERIFIED | O2 open (author copy); Wang closed |
| MIP of thermal/deposited gate oxides | (index only) | stacked gate oxides on Si | Rau et al. 1996 (O4) | - | UNVERIFIED (index abstract only) | closed |
| MIP of a-Si, c-Si (same study) | 11.9 ± 0.9 V; 12.1 ± 1.3 V | Si nanospheres | Wang 1997 via O2 | O2 p. 772 | SECTION_READ of O2 | O2 open |
| IAM MIP of a-SiO2 (engine's Kirkland) | 9.87 / 10.25 / 10.34 / 10.67 / 10.81 V | 2.10 / 2.18 / 2.20 / 2.27 / 2.30 g/cm^3 | abTEM 1.0.10 KirklandParametrization, F_Si(0) 278.374, F_O(0) 95.264 V A^3 | section 4.3 | DERIVED_HERE (parameterisation UNVERIFIED, SM17) | - |
| Total inelastic MFP, a-SiO2, 200 keV | 178 ± 4 nm | no objective aperture, omega filter, 30 particles | O1 | abstract; p. 1130 | SECTION_READ | open |
| Total inelastic MFP, SiO2 (crystalline), 200 keV | 155 nm (± 5-10 %) | 20 mrad convergence and collection | Iakoubovskii et al. 2008 (O3) | Table I | SECTION_READ | open (green) |
| Amorphous vs crystalline SiO2 MFP | amorphous about 10 % larger | 200 keV | O3 | sec. III A | SECTION_READ | open |
| Total inelastic MFP, Si, 200 keV | 145 nm (plasmon part 168 nm); 145 ± 10 nm | 20 mrad; 157 mrad | O3; Basha et al. 2022 (O6) | O3 Table I; O6 abstract | SECTION_READ; +ABSTRACT(PubMed) | O3 open; O6 closed |
| Electronic absorptive potential, a-SiO2 | 0.385 / 0.402 / 0.443 V | V' = 1/(2 sigma Lambda), Lambda = 1780 / 1705 / 1550 A, sigma(200 keV) = 7.2884e-4 | from O1, O3 | section 1.3 | DERIVED_HERE | - |
| Elastic MFP of SiO2 vs collection angle | not read | thermal and CVD SiO2, 200 keV | O6 | body | UNVERIFIED | closed (upload) |
| Density, chemical native oxides (about 1 nm) | 2.07-2.25 g/cm^3 | XRR, six cleaning chemistries | Komiya et al. 1997 (X1) | Table 1, p. 92 | SECTION_READ | open |
| Density, thermal oxides (7 nm) | bulk about 2.20-2.36; interfacial layer 2.35-2.41 g/cm^3, 0.8-1.4 nm | XRR, 800-1000 C | X1 | Figs. 3-4, pp. 90-91 (figure reading) | SECTION_READ | open |
| Density, plasma oxides (4.5-7 nm, 750 C) | 2.11-2.28 g/cm^3 | XRR | Tokutake et al. 2015 (L7 D7) | Tables 2-3 | SECTION_READ (L7) | open |
| Interface transition layer | about 1 nm, about 5 % denser than bulk SiO2; suboxides only in the interfacial Si layer | thermal oxides | Hattori 2001 (R6), citing Sugita 1996 | p. 697 | SECTION_READ of R6; Sugita UNVERIFIED | R6 open; Sugita closed |
| Si/SiO2 interface roughness | 0.2-0.3 nm | thermal oxides, XRR | X1 | p. 91 | SECTION_READ | open |
| Oxide-surface roughness | at most 0.135 nm on Si(100), 0.314 nm on Si(111) | thermal oxidation 700 C, AFM | R6 | p. 697 | SECTION_READ | open |
| Steps preserved at interface and on oxide surface | yes; steps do not move; 0.3 nm steps on 1 nm oxide (Si(111)) | UHV thermal oxidation, SREM + STM | Watanabe et al. 1999 (R1) | pp. 251-252, Figs. 1-3 | SECTION_READ | open |
| Layer-by-layer conversion of Si(001) | contrast reversal per layer; uniform thickness | RT-700 C, 2e-6 Torr O2, SREM | R1; Watanabe et al. 2000 (R2) | R1 p. 253; R2 p. 848 | SECTION_READ | open |
| Terrace-type dependence of specular intensity under oxide | Type-A vs Type-B interfaces differ strongly near the Bragg angle | Si(001), dynamical calculation, 1.4-2.2 deg; SREM 30 kV | R2; Ichikawa 2002 (R3) | R2 Fig. 4, p. 848; R3 p. 88 | SECTION_READ | open |
| Volume expansion on oxidation | "約2倍"; 2.17-2.37 from densities | - | R2; densities above | R2 p. 850; section 3.3 | SECTION_READ; DERIVED_HERE | open |
| Si consumed per oxide thickness | 0.42-0.46 (0.44 at 2.20 g/cm^3) | rho_ox 2.10-2.30 | densities | section 3.3 | DERIVED_HERE | - |
| Amorphous oxide in RHEED/SREM | no diffraction, uniform inelastic loss; halo; interface flatness still in I(0,0) | 10-30 kV | R3, R4 | R3 p. 87; R4 p. 540 | SECTION_READ | open |
| SREM through oxide | interface imaged without stripping for oxides up to "a few nm" | 30 kV | R1, R2 | R1 p. 251; R2 p. 847 | SECTION_READ | open |
| REM of Si(001) with (008) at 200 kV in an ordinary TEM | monatomic-step phase contrast imaged; HF-dipped just before; >= 10 nm oxides removed because of chromatic blur | beam near [110] | Honda and Ohsawa 1988 (R5) | pp. 784-786, Figs. 2-3 | SECTION_READ | open |
| Specular attenuation by oxide (intensity) | 0.45-0.54 (1 nm), 0.20-0.29 (2 nm), 0.09-0.15 (3 nm) | 16.1347 mrad, Lambda 1550-1780 A, with/without refraction | this report | section 3.3 | DERIVED_HERE (upper bound on coherent loss; elastic diffuse loss not included) | - |
| Top-surface phase per A of oxide | 0.866-0.980 rad/A (refracted), 0.91-1.04 rad/A (projected); 0.107-0.121 A of apparent height per A | V_ox 10.1-11.5 V | E6 M4 formula | section 3.3 | DERIVED_HERE | - |
| a/4 step phase, planarising oxide | 12.15-12.31 rad (conformal 10.976 rad) | V_ox 10.1-11.5 V | E6 M4 formula | section 3.3 | DERIVED_HERE | - |
| TEM plasma cleaner (Fischione 1020) | 13.56 MHz ICP; ions < 12 eV; 25 % O2 / 75 % Ar; "2 minutes or less" | manufacturer | SP1020, PB1020 (P1) | SP1020; PB1020 pp. 3-4 | SECTION_READ (manufacturer claim) | open |
| Sputter threshold of Si | 32.0 eV (Ar+), 21.3 eV (O+) | normal incidence, Yamamura-Tawara Eq. (18), U_s(Si) = 4.63 eV | Yamamura and Tawara 1996 / NIFS-DATA-23 (P6) | Eqs. (18)-(19), Table 1 | SECTION_READ (inputs) + DERIVED_HERE | open |
| RT plasma oxide on bare Si | < 1.5 nm after 10^4 s; t^(1/2) growth; about 40-70 % of the final delta at 600 s | low-density RF O2, 2 Pa, 200-500 W | Kitajima 1994 (P3) | pp. 818, 822-823, Fig. 16 | SECTION_READ (+ figure reading DERIVED_HERE) | open |
| Plasma-oxide interface damage | (a-Si + SiO2) interlayer, 3/4 formed in seconds; a-Si fraction 50-75 % | ECR/RF O2 plasma | P3 (Hu et al. as cited) | pp. 821-822 | SECTION_READ of P3 | open |
| O2 plasma on native-oxide Si | native 1.6-1.9 nm; +0.4-0.6 nm in 10 min, +0.7-0.8 nm in 12-16 min; no carbon by XPS | 250 W, 0.120 Torr O2 | Robinson et al. 2004 (P4) | pp. 371-373, Fig. 4 | SECTION_READ (+ figure reading) | open |
| Hydrocarbon removal from ion-milled Si | still significant after 10 min, gone after 60 min | gentle air plasma (JEOL, DC 310 V, specimen outside glow) | Mitchell 2015 (P5) | AM pp. 9-10, 12 | SECTION_READ | open (AM) |
| a-SiO2 atomistic model (open) | 139,968 atoms, 128.716 A cube, 2.183 g/cm^3, O/Si 2.000, 99.8 % fourfold Si, Si-O 1.619 A | ACE potential, melt-quench 1e12 K/s, 0 bar | Erhard et al. 2024 (A1) data, Zenodo 10.5281/zenodo.10419194 (A2), CC BY 4.0 | `results/SiO2/ace/4.in.data` | SECTION_READ (A1, A2) + REPRODUCED (numbers) | open |
| a-SiO2 atomistic model (open, denser) | 331,776 atoms, 168.390 A cube, 2.311 g/cm^3 | CHIK quench + ACE equilibration | A2 | `results/SiO2/hybrid/hybrid.out.data` | as above | open |
| a-SiO2/c-Si(001) small interface cells | 25 cells, 160 atoms, 10.86 x 10.86 x 23.40 A | SCAN DFT data | A2 | `results/SiO/interfaces/interfaces/a-SiO2_c-Si/` | SECTION_READ (one cell inspected) | open |
| Native oxide before plasma | 0.5-0.8 nm (XPS, thermal-oxide-equivalent; HF-last Si in air); 1.6-1.9 nm (ellipsometry, commercial wafers) | days-months in air | Morita 1990 (L7 D1); P4 | L7 2.2; P4 p. 371 | SECTION_READ | open |
| Charging of 1-3 nm oxide on Si under grazing beam | not found | - | - | - | UNVERIFIED (gap) | - |

## 8. Recommended parameter set for the continuum oxide layer (the orchestrator decides)

Model: a uniform amorphous layer of thickness t_ox on the Si(001) surface, conformal to the steps (same thickness on
every terrace, the riser shifted with the terraces), with complex potential V_ox (1 + i r_ox) in the engine's continuum
convention, the crystal interface moved into the Si by 0.44 t_ox relative to the pre-oxidation surface.

| Parameter | Recommended nominal | Range for sensitivity runs | Reason and label |
|---|---|---|---|
| t_ox | 2.0 nm | 1.0-3.0 nm | Native 0.5-1 nm (Morita) or up to 1.6-1.9 nm (ellipsometric) before the clean; a 10 min O2-containing plasma adds under about 0.6-1.0 nm (low-density RF, P3 figure reading) to about 0.4-0.6 nm (250 W O2, P4); total about 1.5-3 nm, widened to 1-3 nm for the unknown cleaner power and O2 fraction. ASSUMPTION built from SECTION_READ inputs; replace by the witness measurement (PROJECT_INPUT). |
| V_ox (MIP) | 10.34 V (engine IAM at 2.20 g/cm^3) for runs that must match an atomistic layer; 10.8 V as the literature centre | 10.1-11.5 V | Measured 10.1 ± 0.6 V (oxide layers on Si nanospheres) and 11.5 ± 0.3 V (a-SiO2 spheres); the engine IAM at the sourced density lies inside this range (section 4.3), so, unlike Si (B32), no IAM systematic outside the measured range has to be carried for the oxide. SECTION_READ (values) + DERIVED_HERE (IAM). |
| V'_ox (electronic absorption), uniform in the layer | 0.40 V (r_ox = V'_ox / V_ox = 0.039 at 10.34 V) | 0.38-0.44 V (r_ox 0.033-0.044); plus a 0 V run | From measured total IMFPs 178 ± 4 nm (amorphous, O1) and 155 nm x 1.1 (O3). Upper bound for loss from the coherent channel (plasmon losses partly coherent, E6 M2). DERIVED_HERE from SECTION_READ. |
| TDS absorption in the oxide | none in frozen-phonon runs | - | as L6 7.2 / B6 (i): not added on top of explicit atoms; for a continuum layer there are no phonons, and the TDS part is small compared with 0.40 V for a light amorphous solid (not sourced; ASSUMPTION) |
| Elastic diffuse scattering out of the 3 mrad aperture | not represented in the continuum layer | - | unsourced (Basha 2022 closed); the atomistic layer produces it explicitly; the continuum-vs-atomistic comparison measures it |
| Density (for the atomistic layer and the IAM value) | 2.20 g/cm^3 | 2.07-2.30 g/cm^3 | X1 Table 1, L7 D7, A2 model 2.18. |
| Interface | abrupt, bulk-terminated Si under the oxide | optional 1 nm transition layer with +5 % density (R6) in a second run | R1, R2, R6; plasma damage interlayer (P3) and ion-milling a-Si are separate layers (below). |
| Carbon on top | none | 0-0.2 nm hydrocarbon (C, H) layer | Most removed by the O2 plasma (P1, P4, P5); readsorption in air/microscope (L7 D6). |
| a-Si under the oxide (milling damage) | 0 nm | 0-2 nm with V = 11.9 V (Wang 1997 via O2) or the IAM 13.6-13.8 V at 98-99 % of c-Si density, V' from Lambda(Si) = 1450 A (0.47 V) | Unknown milling (item 12); more than a few nm would extinguish the specular beam (section 3.3). |
| Shape | conformal | planarising bracket | R1/R2/R6 support conformal for layer-by-layer oxides on stepped Si; E6 M4 gives the bracket (+1.2-1.3 rad on a/4). |

Reason for choosing a continuum layer first: all its parameters are now sourced to a range, it isolates the
refraction/absorption effect of the oxide from the amorphous speckle, and its phase response is known analytically
(0.87-0.98 rad per A of top-surface thickness variation, 0.107-0.121 A of apparent height per A, section 3.3), so the
atomistic run can be checked against it. The atomistic layer (section 5, A2 ACE model, CC BY 4.0) should be run with the
same t_ox and density so that the difference measures only the effect of the amorphous structure.

## 9. What remains a PROJECT_INPUT (Ali)

1. Witness measurement of the actual surface (highest value; replaces the whole thickness bracket): a cross-sectional
   TEM/EELS of a piece milled, air-exposed and plasma-cleaned exactly like the holography sample, or XRR/ellipsometry of
   a flat witness wafer run through the same plasma recipe. Wanted: oxide thickness, a-Si thickness, interface
   roughness, any carbon.
2. Plasma cleaner model, RF power, gas composition (manufacturer's 25 % O2 / 75 % Ar or other), pressure, time (about
   10 min stated), holder grounded or floating, and the delay between cleaning and loading.
3. Ion-milling tool and final step (L7 6.3 checklist a): decides whether an a-Si layer remains under the oxide.
4. Time in air before the clean and storage atmosphere (native oxide before the clean).
5. Energy-filtered EELS of the specular beam at the working angle (item 21): the zero-loss fraction measures the
   oxide absorption directly and replaces V'_ox and the surface-plasmon transfer.
6. Charging test (item 22): phase drift versus dose/time on a flat region.
7. Specimen temperature (item 23) and microscope vacuum at the specimen (hydrocarbon regrowth).
8. If available: a RHEED pattern recorded in the holography session (1x1 streaks/spots under a halo indicate a thin
   amorphous layer on crystalline Si, as in L7 D8 and R4).

## 10. Upload list (priority order)

| Priority | Item | Exact locator | Why | Status |
|---|---|---|---|---|
| 1 | Basha, Levi, Amrani, Li, Ankonina, Shekhter, Kornblum, Goldfarb, Kohn, Ultramicroscopy 240, 113570 (2022) | DOI 10.1016/j.ultramic.2022.113570; the SiO2 (thermal, CVD) rows of the elastic and inelastic MFP tables/figures versus collection angle at 200 keV | elastic diffuse loss of the continuum layer; IMFP at small collection angle | CLOSED (Europe PMC abstract read) |
| 2 | Rau, Baumann, Rentschler, Roy, Ourmazd, APL 68, 3410 (1996) | DOI 10.1063/1.115776; MIP values and method | MIP of thermal and deposited oxide layers on Si by holography: the closest analogue of Ali's oxide | CLOSED (AIP Cloudflare) |
| 3 | Wang, Chou, Libera, Kelly, APL 70, 1296 (1997) | DOI 10.1063/1.118556 (WANG97) | conditions of the 10.1 ± 0.6 V native-oxide value (energy, thickness model, density) | CLOSED |
| 4 | Sosiati/Hata et al., J. Electron Microsc. 55, 23-26 (2006) | DOI 10.1093/jmicro/dfl001 | effect of a plasma cleaner on FIB damage layers (thinning/oxidation vs time and conditions) | CLOSED (index abstract only) |
| 5 | Isabell, Fischione, O'Keefe, Guruz, Dravid, Microsc. Microanal. 5, 126-135 (1999) | DOI 10.1017/S1431927699000094 | the Fischione O2/Ar cleaner's effect on specimens; whether Si oxidation was measured | CLOSED (PubMed abstract read) |
| 6 | Tinoco et al., Microelectron. Reliab. 43, 895 (2003) and Thin Solid Films 496, 546 (2006) | DOIs 10.1016/s0026-2714(03)00098-2; 10.1016/j.tsf.2005.08.351 | room-temperature plasma oxidation of Si: thickness versus time, power, gas (power law) | CLOSED |
| 7 | Kim, An, Shin, Suh, et al., JVST B 14, 2667 (1996) | DOI 10.1116/1.589002 | O2-plasma oxide growth on Si(100) at low temperature (logarithmic law cited by P7) | CLOSED |
| 8 | Sugita, Watanabe, Awaji, Komiya, Appl. Surf. Sci. 100-101, 268 (1996) | DOI 10.1016/0169-4332(96)00302-9 | XRR density of the interfacial layer (the "+5 %" of R6) | CLOSED |
| 9 | Z. L. Wang, Reflection Electron Microscopy and Spectroscopy for Surface Analysis (CUP 1996; ZLWANG96) | chapters on REM of oxide/insulator surfaces, charging, and valence-loss excitation in reflection | charging and inelastic losses in REM of oxide-covered surfaces | CLOSED (book) |
| 10 | McCartney, J. Electron Microsc. 54, 239 (2005) | DOI 10.1093/jmicro/dfi035 (a duplicate DOI 10.1093/jmicro/54.3.239 exists in Crossref) | charging of semiconductor device materials in holography | CLOSED |
| 11 | Watanabe et al., PRL 80, 345 (1998); Watanabe and Ichikawa, Rev. Sci. Instrum. 67, 4185 (1996) | DOI 10.1103/physrevlett.80.345 | SREM beam energy and the Type-A/Type-B specular calculation behind R2 Fig. 4 | CLOSED (lower priority) |
| 12 | Himpsel et al., PRB 38, 6084 (1988) | DOI 10.1103/physrevb.38.6084 | suboxide distribution at the Si/SiO2 interface (for the atomistic interface) | CLOSED (lower priority) |

Found OPEN in this session (no upload needed): O1 Lee 2000, O2 Dunin-Borkowski et al. 2019 (author copy), O3
Iakoubovskii 2008 (green), P1 Fischione documents, P3 Kitajima 1994, P4 Robinson et al. 2004, P5 Mitchell 2015 (AM), P6
NIFS-DATA-23, P7 arXiv:1706.02957, R1-R6, X1 Komiya 1997, A1 Erhard et al. 2024 and its Zenodo data A2 (CC BY 4.0).

## 11. Facts versus inferences, in brief

Facts (with the locators above): measured MIP of a-SiO2 10.1 ± 0.6 V (oxide layers on Si nanospheres; second-hand via O2) and 11.5 ± 0.3 V
(spheres, O1); total inelastic MFP of a-SiO2 at 200 keV 178 ± 4 nm (O1), of SiO2 155 nm with amorphous about 10 % longer
(O3); thin-oxide densities 2.07-2.28 g/cm^3 (X1, L7 D7) with a denser about 1 nm interfacial layer (X1, R6); thermal
oxidation of clean Si proceeds layer by layer, keeps the atomic steps at the interface and on the surface of a 1 nm
oxide, and the interface does not move laterally (R1, R2); the specular reflectivity of an oxidised Si(001) depends on
the interfacial terrace type (R2, R3); SREM images the interface through oxides of a few nm (R1, R2, R3); REM with (008)
at 200 kV images monatomic-step phase contrast on HF-last Si(001) in an ordinary TEM (R5); oxygen plasmas oxidise Si at
room temperature (P3, P4) and create an ion-damaged interlayer (P3); an O2/Ar TEM cleaner delivers ions below 12 eV
(manufacturer, P1), below the Si sputter thresholds of 21-32 eV (P6); gentle plasmas may need tens of minutes to remove
all hydrocarbon (P5); an open CC BY 4.0 a-SiO2 model of 139,968 atoms at 2.18 g/cm^3 exists (A1, A2).

Inferences (DERIVED_HERE/ASSUMPTION): Ali's oxide after the 10 min clean is about 1.5-3 nm (bracket 1-3 nm); the engine's
IAM gives 10.34 V for SiO2 at 2.20 g/cm^3, inside the measured range; the oxide's electronic absorption is 0.38-0.44 V;
a 2 nm oxide reduces the specular intensity by a factor 3.5-5 (total-IMFP bound); the oxide is conformal for
layer-by-layer growth, making the step phase 2 k_perp h (planarising bracket +1.2-1.3 rad); a measurable specular
hologram implies at most a few nm of total amorphous material; charging of a thin oxide on doped Si is expected to be
small but is unmeasured.

## 12. New BibTeX entries

Written to `docs/agent_reports/L8_new_refs.bib` (not merged into `docs/references.bib`). Every DOI was resolved on
2026-09-24 against Crossref (`https://api.crossref.org/works/<doi>`, no mailto) or, for Butsuri 55, 846 (not in
Crossref), the JaLC API (`https://api.japanlinkcenter.org/dois/<doi>`); the Zenodo dataset against the Zenodo API. Entries
already in references.bib (C02 = source O2, WANG97, TANISHIRO2003, MORITA1990, TOKUTAKE2015, KOROBTSOV2007, AZUMA2007,
ZLWANG96, MENDIS19, MENDIS24) are not repeated. New keys: LEE2000MT, IAKOUBOVSKII2008PRB, IAKOUBOVSKII2008MRT, RAU1996,
BASHA2022, ISABELL1999, FISCHIONE1020, KITAJIMA1994, ROBINSON2004SVC, MITCHELL2015, YAMAMURA1996, LUHMANN2017, HATA2006,
WATANABE1999HK, WATANABE2000BUTSURI, ICHIKAWA2002IEEJ, TAKAKUWA2002HK, HONDA1988, HATTORI2001, KOMIYA1997, ERHARD2024,
ERHARD2024DATA, TINOCO2003, TINOCO2006, KIM1996JVSTB, SUGITA1996, MCCARTNEY2005, WATANABE1998PRL, HIMPSEL1988 (29).
Note for docs/07: the instruction-file chapter C02 (Dunin-Borkowski et al., Electron Holography) has an open author
copy at rafaldb.com; L8 read only sec. 16.2 (pp. 772-773) and the reference list.

Status: COMPLETE for this session (2026-09-24).
