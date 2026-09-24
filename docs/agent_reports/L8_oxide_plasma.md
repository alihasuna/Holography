# L8 - Oxide overlayer on air-exposed, O2/Ar-plasma-cleaned, ion-milled Si(001): sourced parameters for the multislice overlayer

Prepared: 2026-09-24 by agent L8 (literature). Status: IN PROGRESS (written incrementally).
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
| O2 | R. E. Dunin-Borkowski, A. Kovacs, T. Kasama, M. R. McCartney, D. J. Smith, "Electron Holography", ch. 16 in P. W. Hawkes, J. C. H. Spence (eds.), Springer Handbook of Microscopy (Springer, 2019), pp. 767-818, DOI 10.1007/978-3-030-00069-1_16 | Author copy on the first author's site: `https://rafaldb.com/papers/B-2019-Science-of-Microscopy-Electron-holography.pdf` (52 pages); SHA-256 695e05e3ccea0055fce570aa44239c90c0d5ef88febcc334d5725c0ac6514445; p. 772 read as a rendered image; reference list read in the text layer. OpenAlex lists the chapter as closed; the author copy was read | SECTION_READ (sec. 16.2, p. 772-773; refs. 16.60-16.66, 16.76-16.82) + METADATA_VERIFIED (Crossref) |
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
* O4: the thermal-oxide and deposited-oxide values carried by the OpenAlex abstract index (about 10.5-11.2 V) are NOT
  used (index only; the AIP page is blocked). Upload item.

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

* Measured MIP of amorphous SiO2 spans 10.1 ± 0.6 V (2 nm native oxide shell on 20-40 nm Si spheres, O2 citing O5)
  to 11.5 ± 0.3 V (220-270 nm colloidal-type spheres, O1); the two differ by 1.4 V, about twice their combined 1-sigma
  (0.67 V). Neither is a plasma-grown oxide on Si(001). A defensible bracket for a thin oxide on Si is 10.1-11.5 V
  (centre 10.8 V, half-range 0.7 V); O4 (thermal and deposited gate oxides, index only) is expected to fall in the same
  range but is unread.
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

