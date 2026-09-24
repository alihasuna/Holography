# E9 - Adversarial review of L8 (oxide overlayer on air-exposed, O2/Ar-plasma-cleaned, ion-milled Si(001))

Reviewer: agent E9, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`.
Status: FINAL (written incrementally; sections 7-9 are the final state).

Scope: `docs/agent_reports/L8_oxide_plasma.md` (629 lines, commit 4ec4cda) and
`docs/agent_reports/L8_new_refs.bib` (351 lines, 29 entries), before the orchestrator adopts a continuum
oxide layer into the engine and the summary documents. Context read: PROJECT_INPUT item 12 (Ali,
2026-09-24: ion-milled Si(001), air-exposed, O2/Ar plasma clean about 10 min, no HF, no UHV anneal);
`docs/agent_reports/E6_literature_review.md` (M3, M4, sections 8-9); L6 sections 1.3-1.5; L7 sections 2,
5, 6; `docs/model_assumptions.md` (B4, B6, B7, B12, B30, B32, B38); `docs/06_project_inputs_required.md`
(items 12, 20-22); `docs/08_paper_readiness.md` (rows 1.6, 2.6); `docs/source_map.tsv` (SM17, SM32);
`docs/physics_conventions.md`.

Files written by E9: this report, `tools/review/e9_recompute.py` and its saved output
`tools/review/e9_recompute_output.txt`. No other repository file is edited; nothing is committed or
pushed by E9 (the orchestrator's snapshot commit 3694f14 picked up in-progress copies). Raw downloads
are kept outside the repository in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/e9/` (called `e9/`).
Every source below was downloaded again by E9 through the session proxy (no personal data sent); L8's
own copies and scripts were not used as inputs. L8's scratch scripts (`l8/l8_numbers.py`,
`l8/analyse_asio2.py`) were not opened at any time (only hashed); L8's saved output file was read only
after E9's own numbers existed.

Severity scale (as E6): BLOCKER (must be fixed before anything is adopted), MAJOR (must be fixed or
re-worded before the affected item is adopted), MINOR (fix when adopting), NIT.

## 0. Log and evidence

* Sources downloaded again by E9 (curl through the session proxy, 2026-09-24 04:44-05:10 UTC; files in
  `e9/pdf/`). SHA-256 of every file equals the value printed by L8 (or L7 for Morita 1990):
  Lee 2000 d1d25bcd...51d5; Dunin-Borkowski et al. 2019 author copy 695e05e3...4445; Iakoubovskii 2008
  34ef97d0...9844; Fischione SP1020 cd77bf83...0b33 and PB1020 5abf7728...78c1; Kitajima 1994
  7af71bf3...0009; Robinson 2004 99574c40...6172; NIFS-DATA-23 4b34eaeb...01ac3; Morita 1990
  aa31b7b2...d3a6; Watanabe 1999 8fb5646d...257c; Watanabe 2000 d0df5d6e...8105487; Honda and Ohsawa
  1988 e062774d...aa9e2; Ichikawa 2002 aa741254...b42; Hattori 2001 e54d0ded...cd3a; Komiya 1997
  33c08418...e9a9; Mitchell 2015 AM f6b4c5c4...a55d3f; Erhard 2024 PMC XML 189ee4c3...ba2c8.
* Zenodo 10.5281/zenodo.10419194: record JSON read through the Zenodo API (licence `cc-by-4.0`,
  `results.zip` 9,345,033,679 bytes); E9 wrote its own range-request extractor (`e9/zipfetch.py`, ZIP64
  end-of-central-directory, 2533 entries) and extracted `results/SiO2/ace/4.in.data`,
  `results/SiO2/hybrid/hybrid.out.data`, both run scripts, `quenching.in`, `equilibrate.in` and
  interface cell 0; every member's CRC-32 equals the zip directory value, and the two structure files
  have the SHA-256 printed by L8 (b45ffe7d...8794d, 2d11ced0...6ac28). DataCite record: CC BY 4.0.
* Page images: PyMuPDF 1.28.2 (scratch venv), rendered at 90-400 dpi and read visually; the two figure
  readings (Kitajima Fig. 16, Robinson Fig. 4) were digitised by pixel analysis of the rendered images
  (axis ticks located automatically; `e9/render/`).
* Bibliography: all 27 DOIs of `L8_new_refs.bib` resolved (25 in Crossref, the Butsuri DOI in JaLC,
  the Zenodo DOI in DataCite; JSON in `e9/cr/`); for every Crossref record the first author, author
  count, year, volume, issue and first page equal the bib entry; title differences are markup only
  (`<SUB>`, MathML). Every DOI printed in the L8 report is in `L8_new_refs.bib` or in
  `docs/references.bib` (C02, WANG97); the duplicate DOI 10.1093/jmicro/54.3.239 named in a note also
  resolves (McCartney 2005, same metadata). No DOI, page or year in L8 was found that is absent from
  the literature report or the instruction-file records.
* Script: `venv/bin/python tools/review/e9_recompute.py <e9/zen>` (SHA-256 3a2f80ca...a0e3), saved
  output `tools/review/e9_recompute_output.txt` (288 lines, SHA-256 a450e42b...2dbe). "out:N" below
  means line N of that output (label REPRODUCED). L8's own saved output (`l8/l8_numbers_output.txt`, 35
  lines, SHA-256 6ca68910...e866, read after E9's run) agrees with E9 wherever it prints a number.

## 1. SECTION_READ claims re-read by E9 (every value the L8 recommendation rests on)

| claim (L8 locator) | E9 reading of the source | verdict |
|---|---|---|
| Lee, Ikematsu, Shindo 2000 (O1): MIP of amorphous SiO2 11.5 +- 0.3 V, holography at 300 kV on 220-270 nm spheres; 2.73 pi at the 50th fringe, t = 113 nm; +-0.06 pi; Fig. 5 curves 10.5/11.5/12.5 V (1.2, 8) | abstract (p. 1129) "11.5+-0.3 V"; sec. 2 (pp. 1129-1130) JEM-3000F FEG "operated at 300kV", 30 V biprism, 0.45 nm fringes; p. 1130 diameters "between 220 and 270 nm"; p. 1131 "2.73pi", "113 nm", "+-0.06pi", conclusion (2) "11.5+-0.3 V"; Fig. 5 caption U = 10.5, 11.5, 12.5 V (rendered pages) | CONFIRMED |
| O1: IMFP 178 +- 4 nm at 200 kV, no objective aperture, JEM-2010 omega filter, 5 nm probe, 30 particles; 100 +- 2 nm at 100 kV; t/lambda < 0.1 warning | p. 1129 Eq. (1) "lambda_p is the mean free path for all inelastic scattering", dependent on "the range of scattering angles (beta)"; sec. 2 JEM-2010, Omega filter, 200 kV, 5 nm, 30 particles; p. 1130 "178+-4nm", "100+-2nm"; p. 1130 "if the relative thickness (t/lambda_p) is smaller than about 0.1, surface excitations may be significant"; conclusion (1): EELS thickness limited to films thicker than about 20 nm at 200 kV | CONFIRMED (the <0.1 and 20 nm statements bear on the thin-layer use of the IMFP: M1) |
| Dunin-Borkowski et al. 2019 (O2 = C02): "20-40 nm-diameter Si nanospheres coated in layers of amorphous SiO2 [16.64] ... amorphous SiO2 10.1 +- 0.6 V"; [16.64] = Wang, Chou, Libera, Kelly, APL 70, 1296-1298 (1997); IAM values "invariably overestimated as a result of bonding"; p. 773 surface state [16.76] and charging [16.77-82] (1.2) | author copy, printed p. 772 (PDF p. 6): verbatim, including 12.1 +- 1.3 V (c-Si) and 11.9 +- 0.9 V (a-Si); ref. list: 16.64 = Wang et al., "Transmission electron holography of silicon nanospheres with surface oxide layers", APL 70, 1296-1298 (1997); 16.63 = Rau et al. APL 68, 3410-3412 (1996); p. 773 verbatim. The chapter states NO beam energy, oxide-layer thickness, density or thickness model for the 10.1 V value | CONFIRMED; conditions of Wang 1997 remain UNVERIFIED (as L8 says) |
| Iakoubovskii et al. 2008 (O3): 200 keV, excitation and collection semi-angles 20 mrad; Table I Si 145 / 168 nm, SiO2 155 nm; accuracies 5-10 % and 10-30 %; amorphous lambda 10 % larger, "single crystalline regions were selected"; 145 nm the "well-calibrated" c-Si value (1.2, Table I "p. 104102-4") | p. 104102-2 sec. II "The excitation and collection semiangles were set to 20 mrad"; relative profiles "converted into absolute ones using the well-calibrated lambda=145 nm value for crystalline Si"; sec. III A "Preliminary results ... lambda values varied within 10% among single crystal, polycrystalline, and amorphous forms. The largest variation was observed for oxides of light elements, such as SiO2, Al2O3, and B2O3: lambda for amorphous phase was 10% larger than for the crystalline ... single crystalline regions were selected for all the measurements"; Table I (printed on p. 104102-5, continued on -6; "copied from Figs. 1 and 4"): Si 145 / 168 nm, SiO2 155 nm | CONFIRMED; the factor 1.1 is the paper's "10% larger" for amorphous light-element oxides, a preliminary result, not a SiO2-specific measurement; the Si 145 nm is the calibration input, not a result of the paper; Table I locator is p. 104102-5 (NIT n1) |
| Basha et al. 2022 (O6), abstract only: Si total inelastic MFP 145 +- 10 nm at 200 keV (beta about 157 mrad); elastic and inelastic MFPs vs collection angle at 200 and 80 keV for SiO2 (thermal, CVD) (1.2) | Europe PMC record PMID 35700667 (E9 fetch): "we measured a total Inelastic MFP (beta~157 mrad) in Si of 145 +- 10 nm for 200 keV electrons"; "SiO2 (Thermal, CVD)" among the oxides; SiO2 values not in the abstract | CONFIRMED at abstract level (+ABSTRACT(PubMed), as L8 labels it) |
| Fischione SP1020 "Ion energies less than 12 eV", 25 % O2 / 75 % Ar, 13.56 MHz, 1e-7 mbar; PB1020 "2 minutes or less", "below the specimen's sputtering threshold", "negligible heating" (2.2) | SP1020 p. 1 verbatim; PB1020 printed p. 3: "energies of less than 12 eV, which is below the specimen's sputtering threshold", "25% oxygen and 75% argon", "2 minutes or less", "without changing its elemental composition or structural characteristics"; p. 4 "negligible heating" | CONFIRMED (the 12 eV and 25/75 statements are on PB1020 p. 3, not p. 4: NIT n2). Manufacturer claim for one instrument; Ali's cleaner is unidentified |
| Yamamura and Tawara (NIFS-DATA-23): Eq. (18) E_th/U_s = 6.7/gamma (M1 >= M2), (1 + 5.7 M1/M2)/gamma (M1 <= M2); Eq. (19) gamma = 4 M1 M2/(M1+M2)^2; Table 1 Si U_s = 4.63 eV, Q 0.66, W 2.32, s 2.5 (2.2) | printed p. 7 Eq. (18) and p. 8 Eq. (19) exactly as quoted; Table 1 printed p. 14: Si 14, 4.63, 0.66, 2.32, 2.5 (rendered pages) | CONFIRMED (formula branch for O is M1 <= M2, as L8 uses) |
| Kitajima 1994 (P3): RF O2 plasma, 2.0 Pa, 200/300/500 W, 6.4e7-2.2e8 cm^-3, floating sample, V_p - V_f about 15 V, coil about 1 m away, HF-dipped Si annealed at 600 C in vacuum; oxide "<1.5 nm" at the end (Fig. 16, to 1e4 s); t^1/2 growth; damaged (a-Si + SiO2) interlayer, 3/4 in seconds, a-Si 50 %/75 % (2.2) | sec. 3 p. 818 (coil "およそ1m", 5e-8 Pa UHV chamber, HF then 600 C vacuum anneal); sec. 5 p. 818 (1/2-power law "酸化初期を除き"); sec. 8 p. 821 (Hu et al.: SiO2 over (a-Si+SiO2), "損傷層の厚さの3/4は数秒で形成", a-Si 50 % positive / 75 % negative bias, damage by positive ions); sec. 9 p. 822 and Fig. 16 caption p. 823 (densities, 2.0 Pa, V_p - V_f ~ 15 V, "＜1.5nm") | CONFIRMED. NOT carried by L8: p. 823 (Fig. 18 and text) shows a delta-Delta PEAK near 100 s at 2.7 Pa that Kitajima attributes to the change of the film's refractive index from Si to SiO2 during ultrathin growth, i.e. delta-Delta is not linear in thickness in exactly this regime (M3) |
| Kitajima Fig. 16 reading: at 600 s delta-Delta about 1.3/2.2/2.7 deg (a/b/c), 40/55/70 % of the 1e4 s values 3.4/4.0/4.0 deg; "<0.6-1.0 nm in 10 min" if linear (2.2) | E9 digitisation (400 dpi, axis ticks 132.1 px/deg and 0.0790 px/s): 600 s: 1.45 / 2.26 / 2.71 deg; 9900 s: 3.42 / 4.01 / 4.01 deg; fractions 0.42 / 0.56 / 0.68; bound 0.64 / 0.85 / 1.01 nm if linear (out:212-214). Reading uncertainty +-0.1 deg (line width about 0.07 deg; slope at 600 s about 0.1 deg per 100 s) | CONFIRMED within the reading uncertainty (curve a reads 0.15 deg higher than L8); the linear conversion is contradicted by the source (M3) |
| Robinson et al. 2004 (P4): native oxide "usually 1.6 to 1.9 nm" by ellipsometry; Matrix etcher, 250 W, 0.120 Torr, 0.75 sccm; DADMAC removed in the shortest time; about 2 A re-adsorbed in 20-40 min; apparent oxide increases, XPS no carbon, "too aggressive" (2.2, "p. 371") | the native-oxide sentence is on p. 370 (not 371: NIT n3), with "ellipsometry is unable to distinguish between the DADMAC and the silicon dioxide underneath" (p. 370); p. 371: 250 W, 0.120 Torr, 0.75 SCCM, chuck heating off; the etcher is a capacitively coupled parallel-plate system whose ions "bombard" the sample (p. 370-371, Fig. 2); pp. 372-373 verbatim | CONFIRMED (the etcher is not an ICP TEM cleaner; P4's own caveat that ellipsometry cannot separate organics from oxide applies to its 1.6-1.9 nm) |
| Robinson Fig. 4 reading: -8 to -10 A at 0.1-3 min; about -6 A at 4-6 min; -4 A at 10 min; -1 A at 12 min; -2 A at 16 min; growth 0.4-0.6 nm in 10 min, 0.7-0.8 nm in 12-16 min (2.2) | the embedded figure is a 244 x 173 px 1-bit image; E9 digitisation (out:216): 0.20 min -8.2; 0.42 -10.1; 0.94 -7.6; 1.31 -9.4; 1.98 -6.9; 2.97 -9.0; 3.98 -5.7; 6.01 -5.4; 7.97 -4.7; 9.99 -4.05; 11.93 -1.35; 15.95 -2.4 A (+-0.3 A). Early points span -6.9 to -10.1 A, so growth at 10 min is 0.29-0.61 nm and at 12-16 min 0.45-0.88 nm depending on the baseline (out:217-219); P4 attributes the lower trend (15 s, 80 s, 3 min) to a shorter wait before measurement (about 2 A of contamination re-adsorbs in the 20-40 min wait of the others) | CONFIRMED to +-0.1-0.2 nm; state as "0.3-0.6 nm in 10 min" (MINOR m6) |
| Morita et al. 1990 (via L7 D1): native oxide 0.5-1 nm (2.3, 8) or 0.5-0.8 nm (table, 7); XPS thermal-oxide-equivalent convention | p. 1273 (rendered): thickness by XPS calibrated with ellipsometry of 70-140 A thermal oxides, "correct as long as the atomic density of the native oxide is equal to that of the thermal oxide"; AND "The native oxide thickness measured by ellipsometry has been demonstrated experimentally thicker than that by XPS" (p. 1273, ref. 3); Fig. 1: n-Si 5.4 -> 7.6 A, n+-Si (1e20 cm^-3) rising to about 10.5 A after about 3e4-1e5 min, p+-Si about 8 A | CONFIRMED for both numbers (0.5-0.8 nm is n-Si; 1.0 nm is reached only by the n+ curve). L8 does not carry Morita's ellipsometry-versus-XPS statement, which decides how P4's 1.6-1.9 nm may be combined with Morita's values (M3) |
| Watanabe, Miyata, Ichikawa 1999 (R1): amorphous oxide does not contribute to the specular spot; interface visible through a few nm; Si(111) about 1 nm oxide at 720 C, 1e-4 Torr, 60 min: steps preserved at the interface and on the oxide surface (STM 0.3 nm), no lateral motion; 48 nm furnace oxide keeps steps; Si(001) contrast reversal per layer (3.2) | p. 251 verbatim (both sentences); samples prepared by DC heating in UHV (clean 7x7 and 2x1) before oxidation (p. 251); p. 252 48 nm at 900 C, HF-thinned, 5 nm one-layer nuclei; p. 253 Si(001) at 2e-6 Torr, RT, 3 min, repeated reversal; interface modelled as amorphous oxide on bulk-positioned Si, two interface types relative to the beam | CONFIRMED; scope: UHV-clean surfaces, thermal O2 |
| Watanabe et al. 2000 (R2): Fig. 4 calculated specular intensity for Type-A/Type-B interfaces, 1.4-2.2 deg, "ブラッグ条件付近(矢印)で大きく異なる"; conversion one atomic layer at a time; uniform thickness over the field of view; "約2倍の体積膨張" (3.2) | p. 848 Fig. 4 and caption verbatim (beam direction drawn perpendicular to a <110>-projection schematic; energy not stated); p. 848 text; p. 850 "常に約2倍の体積膨張を伴って"; Fig. 3 conditions RT 2e-6 Torr, then 635 C and 700 C (2e-5 Torr) | CONFIRMED |
| Ichikawa 2002 (R3): SREM 30 kV, 2-3 nm probe, 2-3 deg; oxide reduces the intensity uniformly by inelastic scattering; specular intensity higher for interfacial bonds parallel to the beam (3.2) | p. 87-88 verbatim; p. 88 adds "さらに一原子層酸化が進行すると,界面のボンドの向きは垂直になり" (each further oxidised layer swaps the interfacial bond direction) | CONFIRMED; the swap per consumed layer is used in section 3 below |
| Honda and Ohsawa 1988 (R5): CZ (001) wafers HF-dipped "観察直前に"; beam near [110]; 006/008/0010 (006, 0010 by double diffraction); Fig. 3 (008) at 200 kV, step phase contrast; C_c 2.0 mm, 11.6 eV, 1.1 nm (100 kV), 0.65 nm (200 kV); thick-oxide statements; regrowth "0.5 nm/h 以下" (3.2) | p. 784 (HF just before observation; beam "〔110〕方向にほぼ平行"; C_c, 11.6 eV, 1.1/0.65 nm); p. 785 (Fig. 2, Fig. 3 "008反射による高分解能のREM像", 200 kV; fringe contrast "ステップの上面と下面で反射した電子線の位相差による干渉で生じ, 表面のステップに対応すると考えられる"); roughness 1.2-1.6 nm / 200-500 nm is on p. 785 (L8: p. 786, NIT n4); p. 786 oxide statements and 0.5 nm/h verbatim | CONFIRMED (the step attribution is the authors' interpretation, "考えられる"; the surfaces were polished wafers, not ion-milled) |
| Hattori 2001 (R6): transition layer about 1 nm, about 5 % denser (XRR); oxide-surface roughness at most 0.314 nm (111), 0.135 nm (100) at 700 C (3.2, 4.2) | p. 697 verbatim ("0.135nm以下", "5%程度高い") | CONFIRMED |
| Komiya et al. 1997 (X1) Table 1 densities 2.07-2.25 g/cm^3 for about 1 nm chemical oxides (4.2) | p. 92 Table 1 (rendered): 1.13/2.07, 1.07/2.11, 1.23/2.16, 1.04/2.23, 1.05/2.21, 1.44/2.25; roughness column "(nm)" 2.1-5.1 | CONFIRMED (the unit remark is a reasonable inference) |
| Mitchell 2015 AM (P5): JEOL EC-52000IC air plasma, DC 310 V, 1 cm outside the glow; 5 nm/h carbon removal; ion-milled Si contamination still significant after 10 min, eliminated after 60 min (2.2) | AM pp. 3, 8-11 verbatim (spot check) | CONFIRMED |
| Erhard et al. 2024 (A1) and Zenodo record (A2): CC BY 4.0; data availability; quench protocol; ACE model 139,968 atoms, 128.716 A cube, 2.183 g/cm^3, O/Si 2.000, 99.8 % fourfold, Si-O 1.619 A; hybrid 331,776 atoms, 168.390 A, 2.311 g/cm^3, "100 % fourfold", 1.618 A; 25 interface cells, #0 160 atoms, 10.8577 x 10.8577 x 23.3951 A (5) | A1 licence and data-availability text verbatim (PMC XML); `4.in.data` is the file written after the final 300 K equilibration of `quenching.in` (ACE, 1e12 K/s, 0 bar, `replicate 3 3 3`); hybrid = CHIK quench at 1e11 K/s (`replicate 4 4 4`) then 20 ps ACE NPT at 300 K (`equilibrate.in` -> `hybrid.out.data`). E9 recount (all Si, periodic KD-tree; out:252-269): ACE 46,656 Si + 93,312 O, box 128.7163 A, 2.1828 g/cm^3, coordination 4.0012 at 2.0 A (99.78 % fourfold, insensitive to 1.9-2.4 A), Si-O pairs 1.6189 +- 0.0322 A; hybrid 110,592 + 221,184, 168.3903 A, 2.3109 g/cm^3, 99.90 % fourfold, 1.6175 A; 25 interface cells, #0: 64 O + 96 Si, 10.857726 x 10.857726 x 23.395123 A, O at z = 10.65-22.43 A | CONFIRMED (hybrid "100 %" is 99.90 %: NIT n5) |

## 2. Recomputation (`tools/review/e9_recompute_output.txt`; label REPRODUCED)

| quantity (L8 locator) | L8 value | E9 value (out:line) | status |
|---|---|---|---|
| lambda, k, sigma(200 keV), 2/sin(theta) (header) | 0.025079 A, 250.53 A^-1, 7.2884e-4, 124.0 | 0.02507934 A, 250.5323, 7.2884010e-4, 123.962 (out:6-12) | agrees (L8's scratch output prints k = 250.54: NIT n6) |
| V' = 1/(2 sigma Lambda) for 1780 / 1705 / 1550 A (1.3, 7) | 0.385 / 0.402 / 0.443 V | 0.3854 / 0.4024 / 0.4426 V (out:19-21); Lee +-1 sigma 0.377-0.394 V (out:22-23) | agrees |
| r_ox = V'/V0 (8) | 0.039 at 10.34 V; 0.033-0.044 | 0.0387; 0.0335-0.0439 (out:28-29); at fixed 10.34 V: 0.0373-0.0428 (out:25) | agrees |
| internal angle in the oxide (3.3) | 17.9-18.1 mrad | 17.863-18.090 mrad for 10.1-11.5 V (out:35-38) | agrees |
| specular intensity through 1 / 2 / 3 nm, in + out (3.3, 7) | 0.45-0.54 / 0.20-0.29 / 0.09-0.15 | with refraction: 0.486-0.537 / 0.236-0.289 / 0.115-0.155; without: 0.449-0.498 / 0.202-0.248 / 0.091-0.124 (out:61-75); complex-k form identical to the refracted path form to 1e-4 (out:49-60) | arithmetic agrees; L8's ranges are the union of the refracted and the unrefracted geometry; interpretation is M1 |
| 1/intensity at 2 nm (11) | "factor 3.5-5" | 3.46-4.24 with refraction (out:70); 5.0 only without refraction and with the crystalline Lambda | MINOR m7 |
| a-Si attenuation, Lambda(Si) = 1450 A (3.3) | 0.18 (2 nm), 0.014 (5 nm) | 0.181 / 0.0139 without refraction, 0.219 / 0.0224 with refraction at 11.9 V (out:78, 80) | arithmetic agrees; inconsistent geometry with the oxide numbers (m7) |
| top-surface phase per A, refracted / projected; apparent height per A (3.3, 7, 8) | 0.866-0.980 / 0.91-1.04 rad/A; 0.107-0.121 A/A | 0.8661-0.9797 / 0.9125-1.0390 rad/A; 0.1071-0.1212 A/A (out:96-103) | agrees; incomplete for a grown oxide (M2) |
| a/4 step phase conformal / planarising (3.3, 7, 8) | 10.976 / 12.15-12.31 rad (+1.2-1.3 rad) | 10.9761 / 12.1521-12.3062 rad, excess 1.176-1.330 rad (out:91, 97, 103); E6's 12.141 rad at 10 V reproduced (out:95) | agrees |
| Si consumed per oxide thickness; expansion; 2 nm oxide (3.3, 7) | 0.42-0.46 (0.44 at 2.20); 2.2-2.4 and 2.17-2.37; 0.9 nm down, 1.1 nm up | 0.4214-0.4616 (0.4415); 2.3728-2.1665 over 2.10-2.30 g/cm^3 (2.4072 at 2.07); 8.83 A down, 11.17 A up (out:139-147) | agrees (derivation: Si atoms conserved, f = (rho_ox/M_SiO2)/(rho_Si/M_Si), rho_Si from a = 5.4309 A) |
| Kirkland f-integrals and IAM V0 of SiO2 (4.3, 7) | F_Si 278.374, F_O 95.264 V A^3; 9.87 / 10.25 / 10.34 / 10.67 / 10.81 V at 2.10 / 2.18 / 2.20 / 2.27 / 2.30; +-0.47 V per 0.1 g/cm^3; Si 13.902 V | f_e(0) = sum a_i/b_i + sum c_i from abTEM 1.0.10 `kirkland.json`: 5.8142839 A (Si), 1.9897443 A (O); K_F f = 278.3742 / 95.2643 V A^3; the same from abTEM's `scattering_factor(k=0)`, from a radial integral of abTEM's V(r) and from the engine's method (out:155-160); V0 = 9.8694 / 10.2454 / 10.3394 / 10.6684 / 10.8094 V; 4.6997 V per g/cm^3; Si 13.9028 V (out:161-171) | agrees; the engine's own `AtomicPotential.scattering_factor` (reflection_holo/forward/multislice/potentials.py:251-253, symbol map with O at :228), called on a stub, returns the same 278.37423 / 95.26427 V A^3 (out:159-160); the engine's `mean_inner_potential_V` refuses any cell that is not pure Si (potentials.py:258-259), so V0(SiO2) = n (F_Si + 2 F_O) is formed outside it |
| IAM of the ACE / hybrid models (5.3) | 10.25 V / about 10.86 V | 10.2586 V / 10.8606 V from the actual atom counts and boxes (out:260, 269) | agrees (10.26 V is the value at the model's own 2.183 g/cm^3: NIT n7) |
| measured MIP difference (1.3) | 1.4 V, about twice 0.67 V | 1.400 V, 2.09 x 0.671 V (out:172) | agrees |
| sputter thresholds (2.2, 7) | 32.0 eV (Ar), 21.3 eV (O) | 31.99 eV (gamma 0.9696), 21.26 eV (gamma 0.9248) (out:178-181); an O2+ ion needs about 42.5 eV if it splits evenly (out:182) | agrees |
| tiling period in the aperture (5.3) | lambda/12.87 nm = 0.195 mrad | 0.1948 mrad for periodicity ACROSS the beam; for periodicity ALONG the beam (L8's stated case) the first satellite lies 9.36 mrad from the specular spot (7.49 mrad for the 168 A cube), outside a 3 mrad aperture; along-beam periods below 474 A never enter it (out:187-190) | MINOR m1 |
| Si IMFP -> V' (1.3) | 0.473 V (1450 A), 0.408 V (1680 A), vs 0.653 V | 0.4731 / 0.4083 / 0.6534 V (out:196-198) | agrees |
| Lee check sigma(300 keV) U t (1.2) | 6.526e-3 rad V^-1 nm^-1; 8.48 rad = 2.70 pi | 6.526161e-3; 8.4807 rad = 2.6995 pi; 2.73 pi implies 11.63 V (out:204-206) | agrees |
| Zenodo model statistics (5.2) | see section 1 | see section 1 (out:252-269) | agrees |

## 3. Phase consequences for the step measurement (task 3; DERIVED_HERE, out:90-133)

Formalism: E6 M4 (specular beam, phase referenced to a fixed plane in vacuum, parallel wavevector
conserved, k'_perp = k sqrt(sin^2 theta + Delta(V)) with the exact relativistic Delta of
`docs/physics_conventions.md`); theta = 16.1347 mrad (B32); a = 5.4309 A (B2); f = Si consumed per
unit oxide thickness = (rho_ox/M_SiO2)/(rho_Si/M_Si) = 0.4214 / 0.4415 / 0.4616 at 2.10 / 2.20 /
2.30 g/cm^3 (out:139-147).

1. **Conformal continuum layer (same t_ox, V_ox, V'_ox on both terraces, following the riser).** The
   whole stack of the upper terrace (crystal, interface, layer, vacuum boundary) is the lower one
   translated by R with R.n = h, so the specular step phase is -(k_out - k_in).R with the VACUUM
   wavevectors: 2 k_perp h = 10.9761 rad (a/4) and 21.9522 rad (a/2) (out:91), independent of t_ox,
   V_ox, V'_ox and of any specular reflection by the layer itself (every partial wave is translated
   with the stack). E6 M4 is CONFIRMED. The interface moved by f t_ox keeps the step height at the
   interface and at the top surface exactly, PROVIDED the same number N of Si layers is consumed on both
   terraces. Valid on terraces long compared with the riser region (the layer's shape over the riser
   enters only near it, as for B9).
2. **Buried interface at a <110> azimuth.** N = f t_ox/(a/4) = 3.25 / 4.88 / 6.50 / 9.76 layers for
   t_ox = 1 / 1.5 / 2 / 3 nm (out:125-128). Each consumed layer swaps the interfacial bond direction
   relative to the beam (R3 p. 88, "さらに一原子層酸化が進行すると,界面のボンドの向きは垂直になり";
   R1 p. 253, R2 p. 848 contrast reversal). Hence at <110> the terrace type on each side of a buried a/4
   step, and so the SIGN of the B4 residual delta, depends on N mod 2, which no source fixes for Ali's
   sample. At an exact <100> azimuth the bulk-terminated terminations are glide-related for any N (B4
   unaffected); a/2 steps join terraces of the same type at any azimuth.
3. **Top-surface-only thickness difference** (a non-consuming layer: contamination, deposited or
   reflowed material, density change): 2 (k'_perp - k_perp) = 0.866-0.980 rad per A for V_ox =
   10.1-11.5 V, 0.107-0.121 A of apparent height per A (L8's numbers, out:96-103). 0.01 rad needs
   0.010-0.012 A; 0.1 A of height needs 0.83-0.93 A (out:118-121).
4. **Grown-oxide thickness difference Dt between terraces** (the physical case for an oxide grown from
   the crystal): the interface on the thicker terrace is lower by f Dt and its top higher by (1 - f) Dt,
   so the step phase changes by [2 k'_perp - 2 k_perp (1 - f)] Dt = 4.27-4.71 rad per A, i.e.
   0.53-0.58 A of apparent height per A (out:109-117) - five times L8's top-surface figure. 0.01 rad
   needs only 0.0021-0.0023 A; 0.1 A of height needs 0.17-0.19 A of oxide difference, i.e. an interface
   offset of 0.080 A = 5.9 % of one consumed layer (a/4) at 2.20 g/cm^3 (out:113).
5. **Layer quantisation.** In the layer-by-layer picture (R1-R3) differences come in whole consumed
   layers: one extra layer on one terrace = 3.075 A of oxide, top raised 1.72 A, extra phase 13.70 rad =
   1.25 times the a/4 step phase (out:123): the buried step becomes 0 or a/2 and the phase is nowhere
   near 10.98 rad. Partly oxidised layers (2-5 nm single-layer islands at under 10 nm spacing, R2 Fig. 7)
   act as a coverage-weighted mean interface in a resolution element plus diffuse scattering; the 0.1 A
   criterion of item 4 then requires the mean coverage of the partly oxidised layer to agree on the two
   terraces to about 6 % of a monolayer.
6. **Planarising limit** (flat top, buried step h, NON-consuming layer): 12.152-12.306 rad for a/4,
   +1.18 to +1.33 rad, +0.146-0.165 A of apparent height (out:97-103), as E6 M4 and L8 state. For an oxide
   GROWN from the crystal a flat top is not self-consistent with a preserved buried step (it would need
   Dt = h/(1 - f) and a buried step of h/(1 - f)); the planarising bracket therefore belongs to
   contamination or deposited layers, not to the plasma oxide.
7. **Sharp-edged continuum layer.** A step of V_ox at the vacuum side reflects |r|^2 = 2.6-3.3e-3 by
   itself (out:233-235; 1-D multislice 2.70e-3 at 10.34 V, out:284); common-mode for item 1, but for
   items 3-6 it adds an interference term of up to 0.36 rad at [100] and dominates at [110] (out:245-247;
   M4 below).

Answers to the task: a conformal layer leaves the a/4 and a/2 step phases unchanged (item 1), also with
the interface moved by f t_ox (same N on both terraces); the moved interface keeps the step height. A
0.01 rad error corresponds to 0.011 A of top-surface-only or 0.0022 A of grown-oxide thickness
difference; a 0.1 A height error to 0.91 A or 0.18 A respectively (V_ox = 10.34 V, 2.20 g/cm^3). Only the
conformal case is compatible with a geometric height conversion; it is an ASSUMPTION for Ali's surface.

## 4. Findings

### BLOCKER

None. Every SECTION_READ value the recommendation rests on was found at (or next to) the stated
locator, every DOI resolves to the cited work, and every L8 number recomputes (sections 1-2). The
MAJOR findings concern what the numbers are said to mean, one physics consequence L8 did not derive,
one engine artefact of the recommended model, and provenance.

### MAJOR

**M1. The oxide attenuation is not an "upper bound on the coherent loss", its lower ends use an
unrefracted path, and it must not be stacked on B38 unexamined (L8 3.3, 7 row "Specular attenuation",
8 row V'_ox, 11).**
Quoted (3.3): "Intensity factor exp(-path/Lambda) with Lambda = 1550-1780 A: t = 1 nm 0.45-0.54; 2 nm
0.20-0.29; 3 nm 0.09-0.15 ... These are upper bounds on the loss from the coherent elastic channel
(plasmon-loss electrons stay in the aperture and are partly coherent, E6 M2) and ignore elastic diffuse
scattering out of the aperture"; (7): "DERIVED_HERE (upper bound on coherent loss; elastic diffuse loss
not included)"; (11): "a 2 nm oxide reduces the specular intensity by a factor 3.5-5 (total-IMFP bound)".
Evidence: (a) exp(-path/Lambda_total) is the full inelastic depletion of the elastic (zero-loss) wave
in a bulk medium, not a bound on it; the only effect that makes the fringe-forming loss smaller is the
partial coherence of loss electrons (E6 M2), while the omitted elastic diffuse scattering by the
amorphous network makes it larger, so the statement as a whole bounds nothing. (b) The bulk IMFP is
used for a layer with t/Lambda = 0.006-0.019 (out:83-85); O1 itself (p. 1130) warns that below t/lambda
of about 0.1 "surface excitations may be significant" and limits its EELS method to films thicker than
about 20 nm at 200 kV (conclusion (1)); the project's own plasmon length scales (Si bulk v/omega_p
8.1-8.2 nm and surface-plasmon decay about 6 nm at 200 keV, E6 M1/M3) exceed the 1-3 nm layer, so
interface suppression of bulk losses and interface/surface plasmons change the loss in both directions.
(c) The lower ends 0.45 / 0.20 / 0.09 are the UNREFRACTED path 2t/sin(theta); inside a layer of
10.1-11.5 V the beam travels at 17.86-18.09 mrad (out:35-38, L8 computes this too). With refraction:
0.486-0.537 / 0.236-0.289 / 0.115-0.155, and 0.269-0.289 at 2 nm with the amorphous IMFPs only
(1705-1780 A; out:61-75); the reduction factor at 2 nm is 3.46-4.24, not 3.5-5 (out:70). (d) B38
(zero-loss fraction 0.288, a transfer from clean Si(111)7x7) and V'_ox both remove elastic intensity by
valence excitation at and near the surface; the product at 2 nm is 0.069-0.083 (out:274-277) with no
source for combining them, the same double count E6 M3 flagged for Si; B38's clean-surface transfer does
not describe an oxide-covered surface.
Required wording (3.3, 7, 8, 11): "Zero-loss transmission of a continuum a-SiO2 layer with the bulk
total IMFP and refraction into the layer (V_ox 10.1-11.5 V): 0.49-0.54 (1 nm), 0.24-0.29 (2 nm),
0.115-0.155 (3 nm) in intensity; 0.27-0.29 at 2 nm with the amorphous IMFPs 170.5-178 nm (E9 out:61-75).
This is a model value, NOT a bound: it omits elastic diffuse scattering by the amorphous network, uses a
bulk IMFP for a layer 50-180 times thinner than the IMFP (O1 p. 1130: surface excitations significant
below t/lambda of about 0.1), and ignores partially coherent loss electrons. It is not to be multiplied
with B38 (clean-surface transfer) without stating which surface and interface losses each factor
carries; the energy-filtered zero-loss fraction of item 21 on the actual surface replaces both."

**M2. A terrace-to-terrace difference of a GROWN oxide shifts the step phase five times more than L8's
"phase response known analytically" (L8 3.3, 7 row "Top-surface phase per A", 8 last paragraph).**
Quoted (8): "its phase response is known analytically (0.87-0.98 rad per A of top-surface thickness
variation, 0.107-0.121 A of apparent height per A, section 3.3)". L8 3.3 derives the 0.44 t_ox
consumption but never applies it to a thickness difference between terraces.
Evidence (section 3 items 3-5): for an oxide grown from the crystal a difference Dt moves the buried
interface by f Dt; the step phase changes by 4.27-4.71 rad/A, 0.53-0.58 A of apparent height per A
(out:109-117). A 0.1 A height error needs only 0.17-0.19 A of oxide difference (interface offset
0.078-0.081 A, 5.7-6.0 % of a consumed layer); 0.01 rad needs 0.002 A. Differences are quantised in
consumed layers: one extra layer = 13.70 rad, 1.25 times the a/4 phase (out:123). L8's 0.107-0.121 A/A
(correct arithmetic) applies only to a non-consuming layer on a fixed crystal.
Required wording (3.3 and 8): "Conformal oxide (equal number of consumed Si layers on neighbouring
terraces): step phase 2 k_perp h unchanged (10.976 rad a/4, 21.952 rad a/2). A thickness difference Dt
between terraces changes it by 0.87-0.98 rad/A (0.11-0.12 A/A) if only the top surface differs, and by
4.3-4.7 rad/A (0.53-0.58 A/A) if the difference was grown from the crystal (interface displaced by
0.42-0.46 Dt); 0.1 A of height error corresponds to 0.18 A of grown-oxide difference (6 % of a consumed
layer) and one extra consumed layer to 13.7 rad. The height conversion under an oxide therefore rests on
the ASSUMPTION of equal consumption on neighbouring terraces, supported only for thermal oxidation of
UHV-clean Si (R1-R3)."

**M3. The oxide-thickness nominal and range mix two thickness conventions, contain an arithmetic slip,
and use a delta-Delta linearity the source contradicts (L8 2.2, 2.3, 8 row t_ox, 11).**
Quoted (8): "Native 0.5-1 nm (Morita) or up to 1.6-1.9 nm (ellipsometric) before the clean; a 10 min
O2-containing plasma adds under about 0.6-1.0 nm (low-density RF, P3 figure reading) to about 0.4-0.6
nm (250 W O2, P4); total about 1.5-3 nm, widened to 1-3 nm"; (2.3) "1.5-3 nm total (nominal 2 nm)".
Evidence: (a) the stated inputs give 0.9-2.9 nm, not 1.5-3 nm (out:224-227). (b) Morita p. 1273: "The
native oxide thickness measured by ellipsometry has been demonstrated experimentally thicker than that by
XPS", and P4 p. 370: ellipsometry "is unable to distinguish between the DADMAC and the silicon dioxide
underneath"; P4's 1.6-1.9 nm is the ellipsometric apparent thickness of as-received wafers, Morita's
0.5-1.0 nm the XPS thermal-oxide-equivalent thickness of freshly HF-etched Si (n+ reaches about 1.0 nm,
n-Si about 0.8 nm, Fig. 1, E9 reading). The engine's t_ox at a fixed 2.20 g/cm^3 is an areal-density
thickness, i.e. Morita's convention; a freshly milled surface starts oxide-free like Morita's. On that
route the total is 0.9-2.0 nm (0.9-1.8 nm with n-Si; 0.9-1.6 nm with P4's growth only; out:224-228); the
ellipsometric route gives 2.0-2.9 nm (out:226). (c) The P3 increment converts delta-Delta fractions into
thickness "if delta is linear in thickness"; Kitajima p. 823 (Fig. 18 and text) reports a delta-Delta
peak near 100 s caused by the refractive-index change from Si to SiO2 in exactly this ultrathin regime,
so only "< 1.5 nm after 1e4 s from a bare surface" is sourced. (d) Both plasma sources differ from a TEM
cleaner (P4: capacitively coupled etcher with ion bombardment in pure O2; P3: pure O2, floating sample
1 m from the coil); no source measures a TEM cleaner on Si (L8 says so).
Required wording (2.3, 8, 11): "t_ox (thermal-oxide-equivalent at 2.20 g/cm^3), ASSUMPTION, range
1.0-3.0 nm. Routes: fresh milled surface, Morita's XPS convention plus plasma growth 0.9-2.0 nm;
as-received-wafer ellipsometric thickness (includes adsorbed organics; ellipsometry reads thicker than
XPS, Morita p. 1273) plus plasma growth 2.0-2.9 nm. Nominal 1.5 nm (the route that matches a milled
surface), 2.0 and 3.0 nm as sensitivity runs [or: nominal 2.0 nm = midpoint of the union 0.9-2.9 nm, no
source preference]. Plasma growth: < 1.5 nm in 1e4 s on bare Si in a low-density RF O2 plasma (P3 p.
822; delta-Delta not linear in thickness in this regime, p. 823); 0.3-0.6 nm in 10 min on native-oxide
wafers in a 250 W O2 etcher (P4 Fig. 4, E9 reading). The witness measurement replaces all of this."

**M4. A sharp-edged continuum layer reflects the specular beam by itself; the engine layer needs a
graded edge before adoption (L8 8 "Model", "its phase response is known analytically"; R1 as quoted in
3.2).**
Evidence (DERIVED_HERE, out:233-247): a potential step of 10.1-11.5 V at the vacuum side has a specular
Fresnel reflectivity |r|^2 = 2.6-3.3e-3 at 16.1347 mrad (|r| = 0.051-0.057); the oxide/Si step to the
engine's 13.903 V adds 1-3e-4. Against the crystal's (0,0,8) reflectivity attenuated by a 2 nm oxide
(x 0.27): 12.5 % in intensity (amplitude ratio 0.35, phase perturbation up to 0.36 rad) for S5's 13-rod
[100] peak |R|^2 = 0.0798 (S5 4.1), 3.4 % for P2's two-beam |R| = 0.542 (r = 0.05); at [110], where S5
4.1 finds a near-zero (|R|^2 = 3.4e-4 at 16.20 mrad), the layer's own reflection is 29 times the
crystal's and would dominate the simulated specular image. A physical oxide surface does not do this: R1
p. 251 says the amorphous oxide does not contribute to the specular spot (R3 p. 87: it is not
diffracted), and the oxide surface is rough at the A scale (R6 p. 697: at most 0.135 nm on Si(100)); an
erf edge of width 0.25 A reduces |r| by 0.10 and of 0.5 A by 1.1e-4 at q = 8.53 A^-1 (out:236-241). For
conformal terraces the term is common-mode (section 3 item 1), but amplitudes, the flat-region phase, the
non-conformal response and the whole [110] case are affected. The engine's transverse grid must resolve
2 k'_perp = 2 x 4.628 A^-1 in Si for the (0,0,8) reflection itself (out:42), which exceeds q = 8.53 A^-1,
so a grid-sharp layer edge produces the term: a 1-D paraxial split-step multislice of the engine's form
(t = exp(+i sigma V dz), P = exp(-i pi lambda dz q^2)) gives |r|^2 = 2.704e-3 for the sharp 10.34 V edge
(analytic 2.697e-3), 1.307e-3 at w = 0.1 A and 3.1e-5 at w = 0.25 A, converged in dz (2.700-2.712e-3
for dz = 1-4 A) (out:284-288; REPRODUCED in 1-D; the engine itself was not run).
Required addition (8): "The continuum layer's vacuum edge and oxide/Si transition are graded over at
least 0.5 A (ASSUMPTION, motivated by the measured oxide-surface roughness, Hattori 2001 p. 697); an
oxide-only control cell (no crystal) must return a specular intensity below 1e-3 of the crystal's before
the layer is used, and the [110] configuration is compared with the atomistic layer, not with the
continuum layer alone."

**M5. "a-Si under the oxide: 0 nm" nominal and an abrupt bulk-terminated interface are the optimistic
bound, not a nominal (L8 2.3, 3.3, 8 rows "Interface" and "a-Si under the oxide").**
Quoted (8): "a-Si under the oxide (milling damage) | 0 nm | 0-2 nm ... | Unknown milling (item 12); more
than a few nm would extinguish the specular beam (section 3.3)"; "Interface | abrupt, bulk-terminated Si
under the oxide".
Evidence: a 1-3 nm oxide consumes only 0.44-1.32 nm of Si (out:125-128, f from out:139-147); the sourced
Ga+ FIB amorphous thicknesses are about 1, 4, 7, 22 nm at 2, 5, 8, 30 keV (Uzuhashi and Ohkubo 2024 pp.
4-5, SECTION_READ via L7 D2, confirmed by E6), broad-beam Ar+ values are closed (L7), so only a final Ga+
polish at 2 keV or below can be consumed by the oxide, and its about 1 nm of a-Si only by 2.22-2.24 nm of
oxide (out:148-149); P3 p. 821 reports a plasma-damaged (a-Si + SiO2) interlayer (biased samples). "Would
extinguish" rests on the same bulk-IMFP model as M1 and is dose-dependent: with refraction 2 nm of a-Si
transmits 0.22 and 5 nm 0.022 in intensity (out:78-80). The abrupt interface is sourced only for thermal
oxides on UHV-clean or HF-last Si (R1, R2, R6).
Required wording (8): "a-Si under the oxide: unknown (item 12a); 0 nm only if the final milling step was
a Ga+ polish at 2 keV or below (or an equivalent low-energy step), because a 1-3 nm oxide consumes only
0.4-1.3 nm of Si; sensitivity 0-5 nm (intensity 1 to 0.022 with Lambda(Si) = 1450 A and refraction). The
abrupt bulk-terminated interface is an ASSUMPTION transferred from thermal oxides on UHV-clean Si; the
plasma-damaged (a-Si + SiO2) interlayer (P3 p. 821) is a separate optional layer."

**M6. Labels stronger than the evidence: REPRODUCED without saved output, DERIVED_HERE numbers printed
by no saved script, scripts outside the repository (L8 1.2, 4.3, 5.1, 7 preamble).**
Quoted: (1.2) "REPRODUCED here: sigma(300 keV) = 6.526e-3 ... 2.70 pi"; (5.1) "REPRODUCED (density,
stoichiometry, coordination of two models, below)"; (7) "DERIVED_HERE rows are computed in
`l8/l8_numbers.py` (output `l8/l8_numbers_output.txt` ...) or `l8/analyse_asio2.py`"; (4.3) "the
engine's own independent-atom potential ... gives F_Si(0) = 278.374 and F_O(0) = 95.264 V A^3".
Evidence: `l8/l8_numbers_output.txt` (35 lines, SHA-256 6ca68910...e866) prints the attenuation, phase,
consumption and sputter numbers only; it prints none of the IAM integrals or V0(rho) values of 4.3/7/8,
the sigma(300 keV) check, V'(Si) 0.473/0.408 V, r_ox, the 0.195 mrad, or the IAM of the two models;
`l8/analyse_asio2.py` has no saved output; both scripts live in the session scratchpad, not in the
repository. The numbers are right (section 2), the labels are not yet earned under the project rules
("REPRODUCED only for executed checks with saved output"; "every number printed by a committed
script").
Required correction: cite `tools/review/e9_recompute_output.txt` (committed with this review) for each
adopted number, or commit L8's scripts with saved outputs; until then label the sigma(300 keV) check and
the model statistics DERIVED_HERE, and the IAM values "computed, output not saved".

### MINOR

**m1. The 0.195 mrad tiling artefact is assigned to the wrong direction (L8 5.3).** Quoted: "The
engine's supercell is much longer along the beam than 12.9 nm (H2). Tiling the cube periodically imposes
a 12.9 nm period ... artificial diffraction at multiples of lambda / 12.87 nm = 0.195 mrad, inside the
3 mrad aperture". lambda/L is the rod spacing for a period ACROSS the beam. For a period L ALONG the beam
at grazing incidence the satellites satisfy theta_out^2 + phi_out^2 = theta^2 + 2 n lambda/L: the n = -1
circle passes 9.36 mrad from the specular spot for the 128.7 A cube (7.49 mrad for the 168.4 A cube),
n = +1 does not exist, and no along-beam period below 474 A reaches a 3 mrad aperture (out:187-190). H2's
transverse width (86.9 A for transverse steps) is below the cube size, so no across-beam tiling is
needed there; the cell's own period already gives rods every 0.289 mrad (out:191). Correct to: "Tiling
along the beam produces satellites at least 9.4 mrad (7.5 mrad for the hybrid cube) from the specular
spot, outside a 3 mrad aperture; tiling across the beam (cells wider than the cube) imposes rods every
0.195 mrad inside it and should be avoided or randomised." The seam and speckle-statistics tests remain
useful.

**m2. The Watanabe/Ichikawa precedent is for an intensity difference at <110>, not for a phase residual,
and not specific to overlayers (L8 3.3 third bullet, 7 row "Terrace-type dependence").** Quoted: "It
supports B4's statement that an overlayer and a <110> azimuth produce a residual delta, and gives a
first-hand measurement-plus-calculation precedent for it (at 30 kV, not 200 kV)." R2 Fig. 4 and R3 p. 88
concern the specular INTENSITY of the two interfacial terrace types for an abrupt amorphous oxide on
bulk-positioned Si (the oxide does not diffract in that model, so the difference comes from the crystal
termination at a <110>-type azimuth, i.e. B4's <110> clause, which holds without any overlayer); no
phase is reported; the calculation's beam energy is not stated in R2 (R3 gives 30 kV for SREM).
Wording: "precedent (SREM, 30 kV class; calculation energy not stated) for a strong terrace-type
dependence of the specular INTENSITY at a <110>-type azimuth under an abrupt amorphous-oxide interface;
consistent with B4's <110> clause; delta itself is not reported. Because each consumed layer swaps the
terrace type (R3 p. 88), the sign of delta at a buried a/4 step depends on the parity of the consumed
layer count (section 3 item 2)."

**m3. "No IAM systematic ... has to be carried for the oxide" is an inference stated as a finding (L8
4.3, 8 row V_ox).** The IAM value 10.34 V lies between two measurements that disagree by 2.09 combined
standard deviations (out:172), one of them with unread conditions (Wang 1997); C02 p. 772 states that
independent-atom values "are invariably overestimated as a result of bonding"; being inside a wide,
internally inconsistent range does not show the absence of a bonding systematic. Wording: "the engine's
IAM value (10.34 V at 2.20 g/cm^3) lies within the span of the two measurements (10.1 +- 0.6 V, 11.5 +-
0.3 V), which disagree with each other; whether the IAM overestimates the oxide's MIP as it does for Si
(C02 p. 772) cannot be decided from them." Note also that V_ox does not enter the conformal step phase
at all (section 3 item 1); it matters for amplitudes and non-conformal cases only.

**m4. "The conformal model is therefore the sourced default" overstates the transfer (L8 3.3 second
bullet, 8 row Shape, 11).** R1, R2, R3 and R6 are thermal oxidations of UHV-flashed (R1 p. 251) or
HF-last surfaces; ion irradiation removes the REM step image until annealing (Yagi et al. 1986 p. 1048,
via L7/E6), so conformality to atomic steps presupposes steps that no source shows on Ali's milled
surface. Wording: "conformal is the behaviour of thermal oxides grown layer by layer on UHV-clean stepped
Si (R1-R3, R6); for Ali's ion-milled, plasma-oxidised surface it is an ASSUMPTION (the case in which a
geometric height conversion is possible at all), with the non-conformal and planarising cases of section
3 as brackets."

**m5. The oxide absorption must follow the conformal region, not a planar mask (L8 5.3 last bullet, 8
row V'_ox).** E6 m12 applies unchanged: a planar (x-only) absorbing slab on a stepped cell puts an extra
layer of thickness h on one terrace; for V'_ox = 0.385-0.443 V that is an amplitude factor 0.952-0.958
(a/4) or 0.907-0.918 (a/2) on one terrace only (out:129-133), which breaks the terrace equivalence B4
rests on. Wording: "V'_ox is applied on the recorded overlayer region of B12 (conformal), never as a
function of the surface-normal coordinate alone."

**m6. Robinson Fig. 4 growth should be quoted with its baseline spread (L8 2.2, 2.3, 7, 8).** The early
points span -6.9 to -10.1 A, so the 10 min growth is 0.29-0.61 nm and the 12-16 min growth 0.45-0.88
nm (out:216-219), rather than "0.4-0.6" and "0.7-0.8" nm. Use "0.3-0.6 nm in 10 min".

**m7. The attenuation of a-Si is computed without refraction while the oxide values mix both (L8 3.3,
8 row a-Si).** 2 nm and 5 nm of a-Si give 0.181 and 0.0139 unrefracted, 0.219 and 0.0224 with refraction
at 11.9 V (out:78-80). Use the refracted values throughout, and "3.5-4.2" for the 2 nm reduction factor
(out:70).

**m8. One native-oxide range, stated with its doping dependence (L8 2.3 and 8 "0.5-1 nm" versus 7
"0.5-0.8 nm").** Morita Fig. 1 shows n-Si reaching about 0.8 nm (7.6 A in the text) and heavily doped
n+-Si about 1.0 nm (E9 reading); both ranges are in the source, but the same quantity must carry one
value: "0.5-1.0 nm (XPS, thermal-oxide equivalent; 1.0 nm only for n+ at 1e20 cm^-3)", and the substrate
doping becomes a PROJECT_INPUT line (section 5).

**m9. The upper end of the V'_ox bracket is a crystalline-SiO2 value (L8 1.3, 8).** 0.443 V comes from
Iakoubovskii's 155 nm, which is for single-crystalline regions (sec. III A); the amorphous values are
0.385 V (Lee) and 0.402 V (155 nm x 1.1, a "preliminary" 10 % from the same paper). Keep 0.38-0.44 V
as the bracket but label the 0.44 V end "crystalline SiO2 (quartz regions), short-IMFP end".

### NIT

* n1. Iakoubovskii Table I is printed on p. 104102-5 (continued on -6), not p. 104102-4 (L8 1.1, 1.2).
* n2. Fischione PB1020: "less than 12 eV", "below the specimen's sputtering threshold" and "25% oxygen and
  75% argon" are on printed p. 3; p. 4 carries "negligible heating" (L8 2.2 says p. 4 for all).
* n3. Robinson 2004: the native-oxide sentence "usually 1.6 to 1.9 nm" is on p. 370 (L8: p. 371).
* n4. Honda and Ohsawa 1988: the 1.2-1.6 nm / 200-500 nm roughness is on p. 785 (L8: p. 786).
* n5. Hybrid model: 99.90 % fourfold Si (L8: "100 %"; out:264-266).
* n6. L8's scratch output prints k = 250.54 A^-1; the report header and docs/physics_conventions.md give
  250.53 (250.5323, out:7). Same quantity, one value.
* n7. The ACE model's IAM is 10.26 V at its own 2.183 g/cm^3 (out:260); L8 5.3 quotes 10.25 V (the
  2.18 g/cm^3 row).
* n8. L8 P6 row cites "report pp. 5-7" for Eqs. (9), (18), (19); Eq. (19) is on p. 8 (the bib note says
  pp. 5-8).
* n9. R2 Fig. 3(d) is at 2e-5 Torr and 700 C (L8 7 row "RT-700 C, 2e-6 Torr").

## 5. Logic of the recommendation (task 4)

1. **"Conformal, nominal 2.0 nm, 1.0-3.0 nm" as an ASSUMPTION.** The RANGE 1.0-3.0 nm is defensible
   as an envelope of the two routes the sources allow (0.9-2.0 nm in Morita's convention for a freshly
   milled surface, 2.0-2.9 nm from ellipsometric as-received-wafer values; M3), provided it is labelled
   ASSUMPTION and the convention is stated (thermal-oxide equivalent at 2.20 g/cm^3). The NOMINAL is a
   choice, not a sourced centre: 2.0 nm is the midpoint of the union, 1.5 nm the midpoint of the route
   that matches a milled surface. "Conformal" is the behaviour of thermal oxides grown layer by layer on
   UHV-clean stepped Si (R1-R3, R6) and of air-grown native oxide on HF-last Si (Morita p. 1273, layer by
   layer); no source measures a TEM plasma cleaner on Si (L8 says so), and no source shows that atomic
   steps exist under the damage of an ion-milled surface (Yagi 1986 via L7/E6). It is therefore the
   ASSUMPTION under which a geometric height conversion is possible at all, and section 3 gives the
   penalties when it fails (0.53-0.58 A of height per A of grown-oxide difference).
2. **What must stay PROJECT_INPUT** (L8 section 9 is right; it lacks the two entries marked NEW): witness
   measurement (oxide thickness with its convention, a-Si thickness, interface roughness, carbon);
   cleaner model, RF power, gas mixture, pressure, time, holder grounded or floating, delay to loading;
   final milling step (ion, energy, angle); time in air and storage; the energy-filtered zero-loss
   fraction at the working angle (item 21), which replaces V'_ox, B38 and M1's model value; charging
   (item 22); specimen temperature (item 23); any RHEED pattern; NEW: the substrate doping (Morita Fig.
   1: n+ at 1e20 cm^-3 grows about 1.0 nm against about 0.8 nm for n-Si, E9 reading); NEW: the beam
   azimuth becomes decisive for a/4 steps under an oxide, because at <110> the terrace type at the buried
   interface depends on the parity of the consumed-layer count (section 3 item 2).
3. **The Watanabe precedent for the B4 residual at <110>.** Valid as a precedent for a large
   terrace-type dependence of the specular INTENSITY at a <110>-type azimuth (R2 Fig. 4 calculation, R1/R3
   SREM contrast reversal at 30 kV), under an abrupt oxide on bulk-positioned Si. It supports B4's <110>
   clause (which needs no overlayer), reports no phase, and adds one new fact the repository must carry:
   each consumed layer swaps the terrace type (m2).
4. **Amorphous Si under the oxide.** Yes, it can remain: a 1-3 nm oxide consumes only 0.44-1.32 nm of Si,
   while every Ga+ FIB energy above 2 keV leaves 4-22 nm of a-Si (L7 D2); only a final polish at 2 keV or
   below can be consumed, and then only by 2.22-2.24 nm of oxide or more (out:148-149). A plasma-damaged
   (a-Si + SiO2) interlayer is reported for biased plasma oxidation (P3 p. 821). Nominal 0 nm is the
   optimistic bound (M5).
5. **Continuum layer first, atomistic second.** The order is right, with two conditions: a graded edge
   (M4) and the understanding that the continuum layer tests only the conformal case and amplitude
   effects, not the structural speckle nor the elastic diffuse loss. The ACE model (CC BY 4.0, 12.87 nm
   cube, 2.183 g/cm^3, O/Si 2.000, 99.8 % fourfold) is a sound open choice; along-beam tiling does not put
   satellites into a 3 mrad aperture (m1).
6. **Sputtering.** 32.0 eV (Ar) and 21.3 eV (O) are the Yamamura-Tawara normal-incidence thresholds of
   Si (not SiO2) and exceed both the manufacturer's "< 12 eV" and Kitajima's V_p - V_f of about 15 V for a
   floating sample; "no physical sputtering expected IF the ion-energy claim holds for Ali's cleaner" is
   the correct scope (L8 has it). An O2+ ion splitting evenly needs about 42.5 eV (out:182).

## 6. Repository statements that must change if L8 is adopted (file:line; proposed content)

| file:line | current statement (abridged) | change |
|---|---|---|
| docs/model_assumptions.md:33 (B7) | "at 20 mrad the beam crosses a 1 nm layer over about 50 nm ... about 100 nm ... in total"; overlayer "not implemented" | at the working angle 16.1347 mrad (B32): 62 nm per pass outside, 56 nm inside a 10.34 V layer (2t/sin theta = 124 t outside, 111.7 t refracted; out:12, 36); add the continuum oxide model of L8 section 8 with E9 corrections (t_ox 1.0-3.0 nm ASSUMPTION in the thermal-oxide-equivalent convention, M3; V_ox 10.34 V IAM for consistency with the atomistic layer, 10.1-11.5 V measured span; V'_ox 0 or 0.38-0.44 V; density 2.07-2.30 g/cm^3; graded edge, M4), the zero-loss model value of M1 (not a bound) and the grown-oxide sensitivity of M2 (B7's "1 A of overlayer variation reads as about 0.11-0.13 A of height" holds for a non-consuming layer only; a grown-oxide difference reads as 0.53-0.58 A per A); "not implemented: the engine accepts Si only" is imprecise: `AtomicPotential` already maps Z = 8 to O (potentials.py:228); what refuses is `mean_inner_potential_V` for non-Si cells (:258-259) and the pipeline overlayer gate (pipeline/config.py:864-869) |
| docs/model_assumptions.md:38 (B12) | conformal overlayer; thickness and density "PROJECT_INPUT item 12 (required arguments)" | keep them required arguments; put L8/E9 values in a NEW demo stand-in row (e.g. B41: demo continuum oxide t_ox 2.0 nm or 1.5 nm, V_ox 10.34 V, V'_ox 0.40 V and 0 V variants, 2.20 g/cm^3, 0.5 A graded edge; refused in comparison runs like B19-B40); define "conformal" as equal thickness AND equal number of consumed Si layers on neighbouring terraces (M2); V'_ox applied on the recorded region (m5) |
| docs/model_assumptions.md:32 (B6) | (ii) bracket 0 / 0.65 V for Si; (iii) Tanishiro transfer | (ii) unchanged for Si; add the cross-check lambda(c-Si) = 145 nm (Iakoubovskii calibration value) -> 0.473 V and lambda_P = 168 nm -> 0.408 V, both below the 0.653 V upper end that rests on Mendis 2019 (UNVERIFIED); add the oxide electronic term 0 / 0.38-0.44 V as a model value (M1, m9); (iii) the surface-plasmon transfer is a clean-surface value and is not combined with V'_ox without a statement (M1) |
| docs/model_assumptions.md:56 (B30) | "Revision 5: sourced routes now exist (B6 (i)-(iii))" | add "and for a continuum oxide (L8 1.3 with E9 M1)"; B30 stays the demo stand-in (item 21 open) |
| docs/model_assumptions.md:64 (B38) | 1.246 excitations, zero-loss 0.288, Si(111)7x7 transfer | add "clean-surface transfer; not the oxide-covered production surface; its product with the oxide zero-loss value (0.069-0.083 at 2 nm, E9 out:274-277) is not a sourced quantity" |
| docs/model_assumptions.md:30 (B4), :44 (B18); docs/05_final_repository_specification.md:38 | "for any overlayer"; "not for ... an overlayer" | "a conformal continuum overlayer (equal thickness and consumed-layer count) preserves B4 at <100>; an atomistic amorphous overlayer breaks it statistically; at <110> the terrace type at a buried interface, hence the sign of delta, depends on the parity of the consumed-layer count (E9 section 3 item 2)" |
| docs/06_project_inputs_required.md:29 (item 12) | preparation checklist; "At 20 mrad ... about 50 nm ... about 100 nm" | add: oxide thickness with its convention (XPS thermal-oxide equivalent or XRR areal density), a-Si, interface roughness, carbon from a witness piece; cleaner model, RF power, gas mixture, pressure, time, holder potential, delay to loading; substrate doping (Morita Fig. 1); replace the 20 mrad sentence by the 16.1347 mrad values |
| docs/06_project_inputs_required.md:46 (item 20) | Si V0 only | add the oxide: measured 10.1 +- 0.6 V (Wang 1997 via C02 p. 772; conditions unread) and 11.5 +- 0.3 V (Lee et al. 2000 p. 1131; 300 kV, 220-270 nm spheres); engine IAM 10.34 V at 2.20 g/cm^3; V_ox does not enter a conformal step phase |
| docs/06_project_inputs_required.md:47 (item 21) | "replaces both the transfer and the bracket" | "replaces the transfer, the Si bracket and the oxide absorption of the continuum layer" |
| docs/06_project_inputs_required.md:22, 28 (items 8, 11) | terrace types at <110> | add: under an oxide the terrace type at each buried a/4 step depends on the parity of the consumed-layer count, so item 11's "which type lies on which side" is not knowable at <110>; an exact <100> azimuth avoids it |
| docs/08_paper_readiness.md:38 (row 2.6) | "needs sourced oxide inner potential and absorption, a continuum layer first" | "OPEN, sourced ranges exist (L8 with E9 corrections: t_ox 1.0-3.0 nm ASSUMPTION; V_ox 10.1-11.5 V measured, 10.34 V IAM; V'_ox 0 / 0.38-0.44 V model value; 2.07-2.30 g/cm^3); graded edge required (E9 M4); open atomistic a-SiO2 exists (Zenodo 10.5281/zenodo.10419194, CC BY 4.0); not implemented (the pipeline refuses an overlayer, pipeline/config.py:864-869; the engine's MIP routine is Si-only, potentials.py:258-259); conformal case only is height-convertible (E9 M2)"; replace "engine accepts Si only" accordingly |
| docs/08_paper_readiness.md:21 (row 1.6) | NEEDS ALI list | add cleaner model and gas mixture, holder potential, substrate doping |
| docs/source_map.tsv:36 (SM32) | Morita, Uzuhashi, Yagi; overlayer phase 0.0903 rad/(A V) | add LEE2000MT pp. 1130-1131, C02 p. 772, IAKOUBOVSKII2008PRB sec. II/III A/Table I p. 104102-5, KITAJIMA1994 pp. 818-823, ROBINSON2004SVC pp. 370-373, WATANABE1999HK, WATANABE2000BUTSURI, ICHIKAWA2002IEEJ, HONDA1988, HATTORI2001, KOMIYA1997, ERHARD2024DATA; numbers from `tools/review/e9_recompute_output.txt`; add the grown-oxide term 4.3-4.7 rad/A |
| docs/05_final_repository_specification.md:126 | "amorphous SiO2/damage overlayer of given thickness and density" | add "with a graded vacuum edge (E9 M4) and an optional a-Si layer" |
| docs/references.bib | 218 entries | the 29 entries of L8_new_refs.bib may be merged: every DOI resolves and matches its registry record (E9 section 0) |
| docs/07_reading_plan.md upload list | - | add L8 uploads 1-8 (Basha 2022, Rau 1996, Wang 1997, Hata 2006, Isabell 1999, Tinoco 2003/2006, Kim 1996, Sugita 1996); note the open C02 author copy (p. 772-773 read) |

## 7. Verdict table

| L8 item | verdict |
|---|---|
| 1.1-1.2 MIP and IMFP sources (Lee 2000, C02 p. 772, Iakoubovskii 2008, Basha abstract) | CONFIRMED (n1 locator) |
| 1.3 MIP bracket 10.1-11.5 V (centre 10.8 V) | CONFIRMED as a span of two mutually inconsistent measurements (m3) |
| 1.3 V'_ox 0.385 / 0.402 / 0.443 V, nominal 0.40 V, r_ox 0.039 | ARITHMETIC CONFIRMED; adopt as a model value with 0 V variant, not as a bound (M1); label the 0.443 V end crystalline (m9) |
| 1.3 Si cross-check 0.473 / 0.408 V vs 0.653 V | CONFIRMED |
| 2.1-2.2 plasma sources (Fischione, Kitajima, Robinson, Mitchell, Yamamura-Tawara) | CONFIRMED (n2, n3, n8); Kitajima figure reading CONFIRMED within +-0.1 deg but its thickness conversion is not supported (M3); Robinson reading CONFIRMED to +-0.1-0.2 nm (m6) |
| 2.2 sputter thresholds 32.0 / 21.3 eV | REPRODUCED (31.99 / 21.26 eV) |
| 2.3 oxide after the clean "1.5-3 nm (nominal 2 nm)" | REWORD (M3: 0.9-2.9 nm, two conventions, nominal is a choice) |
| 2.3 carbon 0-0.2 nm | CONFIRMED as sourced range (L7 D6, P4) |
| 3.1-3.2 reflection-through-oxide and step sources (R1-R6) | CONFIRMED (n4, n9) |
| 3.3 Si consumption 0.44 t_ox (0.42-0.46), expansion 2.2-2.4 | REPRODUCED |
| 3.3 conformal keeps 2 k_perp h (10.976 rad); planarising 12.15-12.31 rad | REPRODUCED; conformal wording (m4); planarising belongs to non-consuming layers (section 3 item 6) |
| 3.3 terrace-type precedent | REWORD (m2) |
| 3.3 attenuation 0.45-0.54 / 0.20-0.29 / 0.09-0.15 "upper bounds" | ARITHMETIC CONFIRMED; REJECT the bound and the unrefracted lower ends (M1, m7) |
| 4.3 IAM V0 of SiO2 (9.87-10.81 V; 10.34 V at 2.20 g/cm^3) | REPRODUCED (out:161-171); m3 on the interpretation; provenance M6 |
| 5 Zenodo ACE / hybrid models and interface cells | REPRODUCED (n5, n7); licence CC BY 4.0 CONFIRMED |
| 5.3 0.195 mrad tiling artefact | CORRECT the direction (m1) |
| 6 charging | CONFIRMED (no source; item 22 stands) |
| 7 table | CONFIRMED except the rows named in M1, M3, m6-m9, n1-n9 |
| 8 recommended parameter set | ADOPT the structure (continuum first, then ACE atomistic; conformal; V_ox; V'_ox with 0 V variant; density) ONLY WITH M1-M5: t_ox convention and nominal (M3), graded edge (M4), a-Si and interface as optimistic bounds (M5), grown-oxide sensitivity carried (M2) |
| 9 PROJECT_INPUT list | CONFIRMED; add substrate doping and the azimuth consequence (section 5 item 2) |
| 10 upload list | CONFIRMED |
| 12 and L8_new_refs.bib (29 entries) | CONFIRMED (every DOI resolves and matches; section 0) |

## 8. Values E9 CONFIRMS (quotable with the locator)

* Mean inner potential of amorphous SiO2: 11.5 +- 0.3 V (off-axis holography at 300 kV, 220-270 nm
  spheres; Lee, Ikematsu, Shindo 2000, p. 1131 and abstract); 10.1 +- 0.6 V (amorphous SiO2 layers on
  20-40 nm Si nanospheres, Wang et al. 1997 as stated in C02 p. 772; conditions not stated there).
* Total inelastic mean free path of amorphous SiO2 at 200 kV, no objective aperture: 178 +- 4 nm (Lee
  et al. 2000, p. 1130); SiO2 (single-crystalline regions, 20 mrad) 155 nm, amorphous about 10 % larger
  (preliminary), c-Si 145 nm (calibration value), plasmon part of Si 168 nm (Iakoubovskii et al. 2008,
  p. 104102-2 and Table I p. 104102-5).
* V' = 1/(2 sigma Lambda) at 200 keV (sigma = 7.2884010e-4 rad V^-1 A^-1): 0.3854 V (1780 A), 0.4024 V
  (1705 A), 0.4426 V (1550 A); Si 0.4731 V (1450 A), 0.4083 V (1680 A), 0.6534 V (1050 A) (out:19-21,
  196-198).
* Kirkland (abTEM 1.0.10) f_e(0): Si 5.8142839 A, O 1.9897443 A; integrals 278.3742 and 95.2643 V A^3;
  IAM V0 of SiO2 = 4.6997 V per g/cm^3 x rho: 10.339 V at 2.20 g/cm^3, 9.869-10.809 V over 2.10-2.30;
  Si check 13.9028 V (out:155-171).
* Si consumed per unit oxide thickness f = 0.4214 / 0.4415 / 0.4616 at 2.10 / 2.20 / 2.30 g/cm^3; a
  2 nm oxide lowers the interface 8.83 A and raises the top 11.17 A (out:139-147).
* Specular step phase at 16.1347 mrad, conformal layer: 10.9761 rad (a/4), 21.9522 rad (a/2); planarising
  non-consuming layer: 12.152-12.306 rad (a/4) for 10.1-11.5 V; top-surface term 0.866-0.980 rad/A;
  grown-oxide term 4.27-4.71 rad/A (0.53-0.58 A/A); one consumed layer 13.70 rad (out:91-123).
* Zero-loss transmission of a continuum oxide (bulk IMFP, refracted path; model value, not a bound):
  0.486-0.537 (1 nm), 0.236-0.289 (2 nm), 0.115-0.155 (3 nm) (out:61-75).
* Fresnel reflectivity of a sharp 10.1-11.5 V layer edge at 16.1347 mrad: 2.6-3.3e-3 (out:233-235);
  a 1-D paraxial split-step multislice reproduces it (2.704e-3 against 2.697e-3 at 10.34 V) and its
  suppression by a graded edge (out:284-288).
* Yamamura-Tawara thresholds on Si: 31.99 eV (Ar), 21.26 eV (O) with U_s = 4.63 eV (NIFS-DATA-23 p. 7
  Eq. (18), p. 8 Eq. (19), Table 1 p. 14; out:178-179).
* Fischione Model 1020 (manufacturer): 13.56 MHz inductively coupled plasma, ion energies below 12 eV, 25 %
  O2 / 75 % Ar (SP1020; PB1020 p. 3).
* Kitajima 1994: low-density RF O2 plasma (2.0 Pa, 200-500 W, floating, V_p - V_f about 15 V) on bare
  Si: oxide < 1.5 nm after 1e4 s (p. 822, Fig. 16 p. 823); damaged (a-Si + SiO2) interlayer under bias
  (p. 821); delta-Delta not linear in thickness in the ultrathin regime (p. 823).
* Robinson et al. 2004: O2 plasma (250 W, 0.120 Torr, 0.75 sccm, capacitively coupled etcher) grows
  0.3-0.6 nm of oxide in 10 min on wafers with an ellipsometric native oxide of 1.6-1.9 nm (p. 370-373,
  Fig. 4, E9 reading); no carbon by XPS.
* Morita et al. 1990: native oxide on HF-last Si(100) in clean-room air 0.5-1.0 nm (n-Si 5.4 -> 7.6 A in the
  text, about 0.8 nm and n+ about 1.0 nm in Fig. 1 by E9 reading), XPS thermal-oxide equivalent;
  ellipsometry reads thicker than XPS (p. 1273, Fig. 1).
* Watanabe et al. 1999/2000, Ichikawa 2002: layer-by-layer thermal oxidation of UHV-clean Si keeps the
  steps at the interface and on a 1 nm oxide surface, the steps do not move laterally, and each consumed
  layer swaps the interfacial terrace type (R1 pp. 251-253; R2 p. 848; R3 p. 88).
* Honda and Ohsawa 1988: (008) REM at 200 kV of HF-last Si(001) wafers in an ordinary TEM, beam near
  [110], fringe contrast attributed to monatomic steps (pp. 784-785, Fig. 3).
* Erhard et al. 2024 data (Zenodo 10.5281/zenodo.10419194, CC BY 4.0): ACE a-SiO2, 139,968 atoms,
  128.716 A cube, 2.1828 g/cm^3, O/Si 2.000, 99.78 % fourfold Si, Si-O 1.619 A; hybrid 331,776 atoms,
  168.390 A, 2.3109 g/cm^3 (out:252-269).

## 9. The orchestrator must NOT adopt yet

1. The attenuation numbers as "upper bounds on the coherent loss" and the unrefracted lower ends 0.45 /
   0.20 / 0.09, the "factor 3.5-5", and any product of the oxide zero-loss value with B38 (M1, m7).
2. L8's "phase response known analytically (0.87-0.98 rad/A, 0.107-0.121 A/A)" as the oxide's phase
   sensitivity without the grown-oxide term 4.3-4.7 rad/A (M2).
3. "1.5-3 nm total", "nominal 2 nm" as a sourced value, and the "< 0.6-1.0 nm in 10 min" plasma
   increment (M3).
4. A sharp-edged continuum layer in the engine (M4).
5. "a-Si under the oxide: 0 nm" and "abrupt, bulk-terminated interface" as nominal values (M5).
6. The REPRODUCED labels of L8 1.2 and 5.1 and the IAM values of 4.3 without a committed output; cite
   `tools/review/e9_recompute_output.txt` instead (M6).
7. "Tiling ... 0.195 mrad inside the 3 mrad aperture" for along-beam tiling (m1); "supports B4's statement
   that an overlayer ... produce[s] a residual delta" (m2); "no IAM systematic ... has to be carried"
   (m3); "the sourced default" (m4).

Status: FINAL for this session (2026-09-24). Files: this report; `tools/review/e9_recompute.py`;
`tools/review/e9_recompute_output.txt`. Nothing committed or pushed by E9.
