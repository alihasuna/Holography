# L7 - Surface realism for the Si(001) reflection-holography simulation (literature)

Prepared: 2026-09-23 by agent L7 (literature). Status: IN PROGRESS (written incrementally).
Branch `claude/electron-holography-orchestration-nakd7r`. No repository file other than this report and
`docs/agent_reports/L7_new_refs.bib` is edited; nothing is committed or pushed.
Raw downloads are kept outside the repository in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/l7/`
(called `l7/` below).

Labels (instruction file section 1.4): METADATA_VERIFIED, SECTION_READ (only with a locator),
REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED. Sub-labels as in L5:
`+ABSTRACT(publisher)` = abstract read on the publisher's own page; `+ABSTRACT(index)` = only a
search-engine or index summary seen (not evidence). A search-engine summary is never evidence and no
fact below rests on one.

Read before starting: `docs/model_assumptions.md` (B3, B4, B20, B26), spec section 4.2,
`docs/06_project_inputs_required.md` (items 8, 11, 12, 13), `docs/references.bib` (132 entries),
`docs/07_reading_plan.md`, `docs/02_literature_position.md`, L4, L5, H2 section 10 (N4 to N6), and the
code refusing the dimer termination and overlayer atoms (`reflection_holo/structure/si001.py`,
`_termination_option` and `_overlayer_option`, lines about 414-457).

## 0. Log of hosts and access (filled as the work proceeds)

| Host / service | Result (2026-09-23) |
|---|---|
| J-STAGE WebAPI `https://api.jstage.jst.go.jp/searchapi/do?service=3` | works with `text`, `article`, `author`, `keyword`; a Japanese-only `text` query of one token returns status ERR_001 (no usable result), the same query split or with a variant spelling works |
| CiNii Research OpenSearch `https://cir.nii.ac.jp/opensearch/all` and record JSON `https://cir.nii.ac.jp/crid/<id>.json` | works |
| NDL Digital Collections (`dl.ndl.go.jp`), NDL Search (`ndlsearch.ndl.go.jp`) | pages reachable; restricted items return `checkResult NG` on the IIIF manifest |
| Osaka University repository OUKA (`ir.library.osaka-u.ac.jp`) | works |
| Query script | `l7/jp_search.py`, queries `l7/jp_queries*.json`, raw responses cached in `l7/jp_cache/`, printed output `l7/jp_out*.txt` |

## 3. Reflection-holography sources in the Japanese databases (task 3; written first because it was never searched before)

### 3.1 Queries run (J-STAGE WebAPI and CiNii Research; totals as returned on 2026-09-23)

Batch 1 (`l7/jp_queries1.json`, output `l7/jp_out1.txt`): J01 text 反射電子ホログラフィー (ERR_001), J02 text
反射電子ホログラフィ (2), J03 article 反射電子ホログラフィー (ERR_001), J04 article "reflection electron holography"
(2), J05 text 反射 電子線ホログラフィー 表面 (118), J06 text "reflection electron holography surface step" (45),
J07 author 長我部 (31), J08 author "Osakabe Nobuyuki" (23), J09 author 谷城 (260), J10 author Tanishiro (172),
J11 text 電子線ホログラフィー 原子ステップ (16), J12 text 反射電子顕微鏡 ホログラフィー (30), J13 text "REM holography
biprism" (4), J14 text "reflection electron microscopy interferometry" (57), J15 author 竹口 雅樹 (67); CiNii C01
反射電子ホログラフィー (1), C02 反射電子ホログラフィ (1), C03 "reflection electron holography" (94), C04 反射
電子線ホログラフィー (12), C05 長我部 ホログラフィー (13), C06 "Osakabe holography" (35), C07 反射電子干渉 (0),
C08 "reflection electron interferometry" (93), C09 谷城 ホログラフィ (1), C10 竹口 反射 ホログラフィー (1), C11
"Takeguchi reflection electron holography GaAs" (1), C12 電子線ホログラフィー 表面 ステップ (3).
Batch 2 (`l7/jp_queries2.json`, `l7/jp_out2.txt`): J20 text 反射型電子線ホログラフィー (4), J21 (19), C20 (6),
C21 "reflection electron holography silicon" (2), C22 "scanning reflection electron holography" (7), and the
surface-science queries J22-J37 used in sections 1 and 2. For J-STAGE lists above 100 only the first 100
records were screened (the API page size); titles were screened with keyword filters (script in the log).
Japanese key term found in use by the Hitachi and Osaka groups: 反射型電子線ホログラフィー (the query term
反射電子ホログラフィー suggested in docs/02 finds only the Tokyo Tech items).

### 3.2 New items found, what was read, locators

| # | Item | Access and what was read | Facts extracted (locator) | Label |
|---|---|---|---|---|
| J-a | Osakabe, "反射型電子線ホログラフィー法による表面の観察" (Observation of Surfaces by Reflection Electron Holography), 2a-T-7, 日本物理学会 年会講演予稿集 45(2), 451-452 (1990), DOI 10.11316/jpsgaiyod.45.2.0_451 | OPEN on J-STAGE: `https://www.jstage.jst.go.jp/article/jpsgaiyod/45.2/0/45.2_451/_pdf/-char/ja` (2 pages, scanned; read in full as page images; SHA-256 baf94580...f4b2) | see 3.3 | SECTION_READ (p. 451 sec. 2-2, 2-3, 3-1; p. 452 sec. 3-1, 3-2, Figs. 2-3, refs.) |
| J-b | Osakabe, Endo, Matsuda, Fukuhara, Tonomura, "反射型電子線ホログラフィーによる結晶表面の観察", 6p-T-5, JPS 秋の分科会予稿集 1989(2), 439, DOI 10.11316/jpsgaiyok.1989.2.0_439_1 | OPEN, J-STAGE PDF `.../jpsgaiyok/1989.2/0/1989.2_439_1/_pdf/-char/ja` (1 page with the next abstract; SHA-256 280fa380...5c257) | see 3.3 | SECTION_READ (p. 439, text and Figs. 1-2) |
| J-c | Osakabe, "電子線ホログラフィーによる格子欠陥研究の可能性", 3p-E-4, JPS 秋の分科会予稿集 1990(2), 515, DOI 10.11316/jpsgaiyok.1990.2.0_515 | OPEN, J-STAGE PDF (1 page; SHA-256 d1fb9531...9053) | sec. 3: "鏡面反射の場合には、ΔΦ = 2K sinθ d と書ける。K は波数ベクトル、θ は反射の視斜角、d は高さの変位である。" Surface-normal resolution "理想的な場合 0.01Å のオーダー", lateral resolution set by the mean path in the solid, "数百Å". Cites Lichte, Herrmann and Lenz, Optik 77, 135 (1987) (for aberration determination, not reflection). | SECTION_READ (p. 515, sec. 3) |
| J-d | Suzuki, Ishiguro, Minoda, Tanishiro, Yagi, "反射電子顕微鏡法における Energy filtered holography", 22aT-11, JPS 年次大会概要集 55(1-4), 747 (2000), DOI 10.11316/jpsgaiyo.55.1.4.0_747_4 | OPEN, J-STAGE PDF (shared page; SHA-256 86facc73...2d5b) | REM holography of Si(111)7x7 in a UHV microscope with biprism and omega filter; "物体波・参照波共に試料表面で反射した電子を使う"; surface plasmon 11.3 eV; point 3: amplitude and phase reconstructed from elastic holograms, "表面ステップの上下のテラス間での電子線の位相差等を観察することができた", but the biprism-filament Fresnel fringes must be removed for accurate work. No step-phase value is printed. | SECTION_READ (p. 747, 22aT-11, points 1-3) |
| J-e | Tanishiro, Suzuki, Minoda, Yagi, "反射電子顕微鏡法における energy-filtered electron interferometry II", 28aXC-7, JPS 概要集 56(1-4), 852 (2001), DOI 10.11316/jpsgaiyo.56.1.4.0_852_2 | OPEN, J-STAGE PDF (SHA-256 53d9c2e4...bbb1) | "試料表面の2領域からの反射電子顕微鏡(REM)像をバイプリズムを用いて重ね合わせるとホログラムを作成できる"; "オメガフィルターを装着した200kV・電界放出型電子顕微鏡を用いて、シリコン表面 (ħωs = 11.3 eV) のエネルギー選別されたREMホログラム (エネルギーウィンドウ幅: 10 eV) を観察"; one-plasmon-loss interference distance about 45 nm. | SECTION_READ (p. 852, 28aXC-7). **Upgrades docs/02: the 200 kV of the Tokyo Tech REH work is now read, not inferred.** |
| J-f | Takeguchi, 超高真空-反射型電子線ホログラフィー顕微鏡の開発 (Development of an UHV reflection electron holography microscope), doctoral thesis, Osaka University, 1993 (degree 1993-03-25, 甲第04794号 / 学位記番号 10743), hdl 11094/38196, NDL DOI 10.11501/3065914 | Full text CLOSED (OUKA: "著者からインターネット公開の許諾が得られていないため、論文の要旨のみを公開"; NDL: in-library only, transmission service to registered users resident in Japan). Abstract and examiners' summary OPEN: `https://ir.library.osaka-u.ac.jp/repo/ouka/all/38196/10743_Abstract.pdf` (read in full, 3 pages; SHA-256 17e3b839...72db6). Table of contents read in the CiNii record. | Abstract p. 383-384: a 200 kV TEM was converted to a Zr-O/W(100) thermal-field-emission gun; biprism holograms of about 1.4 nm^-1 spatial frequency; a UHV specimen chamber in the 10^-9 Torr range; Si(111) heat-cleaned in situ, steps, surface dislocations and the 1x1 to 7x7 transition seen by RHEED and REM; holograms formed with Bragg-reflected waves from the surface. | SECTION_READ (abstract, pp. 383-384) |
| J-g | Osakabe, 電子線ホログラフィー干渉法による極限的計測, doctoral thesis (博士(理学)), Tokyo Institute of Technology, 1995-01-31, 乙第2714号, NDL DOI 10.11501/3104578, NDL call number UT51-95-T584 | CLOSED online: NDL "オンライン閲覧公開範囲 国立国会図書館内限定公開"; "図書館・個人送信対象" (individual transmission only for registered users resident in Japan); IIIF manifest returns `checkResult NG`; **"遠隔複写可否（NDL） 可" (remote photocopy can be ordered)**. Table of contents read in the CiNii record `https://cir.nii.ac.jp/crid/1920865334626313088.json`. | Ch. 4 "反射型電子線ホログラフィー干渉計測法の開発と表面地形観察への応用" with sections "結晶表面からの反射電子の位相", "装置ならびに光学系", "表面地形観察への応用"; App. B "電子線バイプリズム"; App. E "表面での応力緩和を考慮した歪み場の計算". | METADATA_VERIFIED (NDL and CiNii records); content UNVERIFIED. **Most complete single source for Osakabe's arrangement, phase relation and measured phases; request chapter 4 by NDL remote copy.** |
| J-h | Osakabe, "反射型電子線ホログラフィー法による結晶表面の研究", 固体物理 (Kotai Butsuri, AGNE) 25(9), 591-596 (1990-09) | CLOSED: NDL digitised, "国立国会図書館内限定公開", "図書館・個人送信対象外" (NDL Search R000000004-I3675842) | none read | METADATA_VERIFIED (NDL/CiNii record); content UNVERIFIED; library request |
| J-i | Takeguchi, Harada, Shimizu, "Observation of GaAs(110) Surface Defect by Reflection Electron Holography", J. Electron Microsc. **39(4), 269-272 (1990)** (TAKEGUCHI1990) | Body closed (OUP). Volume, issue and pages from the NDL article index via CiNii `https://cir.nii.ac.jp/crid/1521417755419074304.json` (NDL bib 3675815, NAID 40005328351); authors "Masaki Takeguchi; Ken Harada; Ryuichi Shimizu" in the same record; the Crossref DOI 10.1093/oxfordjournals.jmicro.a050815 carries the same title and 1990-08-01 but no volume or pages. | fills the missing fields of `references.bib` TAKEGUCHI1990 | METADATA_VERIFIED (NDL/CiNii for volume 39(4), pp. 269-272 and authors; Crossref for DOI and title); the pairing of the DOI with 39(4) 269 rests on identical title, journal and year (DERIVED_HERE) |
| J-j | KAKEN project 05402028 (1993-1994), 志水隆一 (Shimizu), 生田, 木村, 高井 (Takai), Osaka University, "Development of Scanning Reflection Electron Holography Microscopy (SREHM)" | Project abstract read in the CiNii project record `https://cir.nii.ac.jp/crid/1040000781609643904.json` | UHV reflection microscope built; Pt(100) reconstructed domains observed in REM; a UHV two-axis sample holder setting incidence and azimuth angles; Zr-O/W(100) emitter with infrared heating in UHV "本格的な走査型反射電子線ホログラフィー顕微鏡観察が可能になった". No reflection-holography measurement result is stated. | SECTION_READ (grant abstract only) |
| J-k | Joy and Frost, "Transmission and Reflection Holography at Low Energies", e-J. Surf. Sci. Nanotech. 2, 81-88 (2004), DOI 10.1380/ejssnt.2004.81 | OPEN (read in full) | a lensless point-projection microscope at 150-300 V; reflection-mode images of a Cu grid and a stainless-steel surface "with only a few fringes" (Fig. 12 caption, p. 86; p. 87). Not crystalline, not high energy: not a precedent for the project's observable. | SECTION_READ (pp. 81-88) |
| J-l | Banzhof et al., Proc. 9th Eur. Congr. Electron Microscopy, York 1988, p. 263 | cited as ref. [4] by J-a (p. 452): step phases on Pt and Au(111) "反射の次数を変えて測定" | a pre-P09 conference paper on the Au/Pt step phase vs reflection order | UNVERIFIED (second-hand citation; not in any database searched); library request |

### 3.3 Osakabe's arrangement, phase relation and measured step phase, as read in J-a and J-b

Quotations are transcribed from the page images (spacing normalised); translations are mine.

* Arrangement (J-a p. 451, sec. 2-2): "装置は通常の電子顕微鏡を用いている。反射顕微鏡法(REM)と同じ配置で試料表面からの
  鏡面Bragg反射を対物絞りによって選択し結像する。対物レンズの下部にバイプリズムを配置し、波面分割によって電子線を重畳し
  干渉縞即ちホログラムを形成する。この時にバイプリズムの片側を通る電子線は、参照波として扱うので試料上の欠陥等の無い領域に
  合わせておく。" (An ordinary electron microscope in the REM configuration; the specular Bragg reflection is selected
  by the objective aperture; a biprism below the objective lens; the wave passing on one side of the biprism is the
  reference and is set on a defect-free region of the specimen.) J-b p. 439 says the same: the reflected wave from a
  defect-free surface region is superposed as reference on the reflected wave from the observed region. Reconstruction
  was optical (Mach-Zehnder interferometer, J-a sec. 2-2).
  **Fact:** P01-era Hitachi REH used a surface self-reference (type R2 of assumption B5), the specular Bragg beam, and
  an image-side biprism. This settles, at first-hand level for the Hitachi group's own description, the question left
  open in docs/02 (the abstract-level reading of P01 was already R2; the patent PAT01 describes a vacuum reference as a
  later invention). The body of P01 itself remains unread.
* Coherence (J-a sec. 2-1 and 3-2): cold FEG; at 10,000x and exposures of a few seconds, "temporal coherence length 3 μm,
  spatial coherence length 1 μm"; "入射電子線は開き角が10⁻⁶rad以下に平行化されて数μmの可干渉距離がある" (the incident
  beam is collimated to an opening angle below 1e-6 rad, coherence distance several μm). Relevant to PROJECT_INPUT item 3
  as a literature benchmark of the convergence used in REH (not a value for Ali's microscope).
* Phase relation, geometric (J-a sec. 2-3): "結晶内部での電子の振まいが場所的に一様であるとみなせる時には反射波の位相差は
  純粋に幾何学的関係で決定することができる。表面垂直方向の真空中の波数ベクトルをK⊥とし、表面の垂直方向の変位をΔzとすると、
  位相差はΔφ = 2K⊥Δzと書くことができる。" "実験的には入射の視斜角は数10mradなので、1波長の位相差はsub Åに対応する。"
  J-b Fig. 1: "Δφ = 2KΔz sinθ" ("反射電子の位相差"); J-c: "ΔΦ = 2K sinθ d". No sign convention is stated in any of the three.
* Phase relation with refraction (J-a sec. 3-1, pp. 451-452): the monatomic step height equals the fundamental plane
  spacing of the Bragg reflection, so the phase is 2nπ for reflection order n, but refraction shifts it; "運動学的近似では、
  Δφ = √((2πn)² − (2kd)² V₀/E) と書ける。" Under dynamical conditions exciting simultaneous reflections the phase departs
  from this, "しかしそれは屈折をおこす平均内部電位が同時反射を起こしているポテンシャルの分増減する程度のもの" (by about the
  amount by which the potential of the simultaneous reflection adds to or subtracts from the refracting mean inner
  potential). Symbols k, d, V₀, E are not defined further in the abstract (inference: k vacuum wavenumber, d step height,
  V₀ mean inner potential, E accelerating potential; DERIVED_HERE: this is 2K⊥d evaluated at the internal Bragg condition
  2 k_in⊥ d = 2πn with K⊥² = k_in⊥² − k²V₀/E, the same refraction structure as docs/03; not a validation of the sign).
* Measured step phase (J-a p. 452): Pt(111): "2.3Åの単原子ステップが観察されている。そこでの約0.5λの位相差は、上式によって
  説明できる。" (a 2.3 Å monatomic step shows a phase difference of about 0.5 λ, explained by the formula). Energy,
  reflection order and glancing angle for this figure are not stated in the abstract.
* Phase ambiguity (J-a sec. 3-2): "一般にはステップでの、位相差の整数部分は観測されなかった" (in general the integer part of
  the step phase was not observed); around a dislocation the integer part was recovered by following fringe continuity
  from the core. This is the published statement of the 2π-ambiguity that assumption B16 addresses.
* GaAs(110) (J-b): screw dislocation with b = a/2[101] ("[iOl]" in the OCR; bar position not legible); "干渉縞1本のずれは、
  0.5Åの高さの変位に対応する" (one fringe = 0.5 Å height). DERIVED_HERE: equals d_880 = a/(8√2) = 0.4997 Å for
  a = 5.653 Å, consistent with the (880) reflection of P02E's caption at the kinematic Bragg condition without refraction.

### 3.4 Status of each item of the docs/07 upload list after this search (task 3)

| docs/07 # | Item | Open copy found? | Result |
|---|---|---|---|
| 1 | P01 Osakabe et al. JJAP 27, L1772 (1988) | NO | CiNii record carries the abstract only (identical to L5); its JaLC link returns "JOI_Not_Found". The Hitachi group's own description of the arrangement and phase relation is now read in J-a and J-b (section 3.3), which reduces but does not remove the need for P01's body (energy, order, glancing angle). |
| 2 | P08 Osakabe, Microsc. Res. Tech. 20, 457 (1992) | NO | CiNii record only (crid 1360298343635449472). |
| 3 | P02 Osakabe et al. PRL 62, 2969 (1989) | NO | CiNii record only; J-b Fig. 2 and J-a Fig. 3 reproduce its GaAs(110) screw-dislocation interferogram. |
| 4 | P03 Banzhof and Herrmann, Ultramicroscopy 48, 475 (1993) | NO | CiNii record only. New related lead J-l (EUREM 88, p. 263), UNVERIFIED. |
| 15 | Suzuki et al. JJAP 40, 2527 (2001) | NO | Tokyo Tech T2R2 record `CTT100448344` is metadata only (vol. 40, no. 4, pp. 2527-2532; no file); J-d and J-e give the conference versions (read). |
| 16 | Osakabe et al. Ultramicroscopy 48, 483 (1993); Osakabe, Surf. Sci. 298, 345 (1993) | NO | CiNii records only (crid 1870025018705594240 for the former). |
| 17 | Herring, Proc. MSA 53, 116 (1995) | NO | not in J-STAGE or CiNii. |
| 18 | Takeguchi, Harada, Shimizu, J. Electron Microsc. (1990) | NO (body) | volume 39(4), pp. 269-272 now METADATA_VERIFIED (J-i). The author's thesis abstract (J-f) is open and read. |
| new | Osakabe thesis 1995, ch. 4 (J-g) | NO (NDL remote copy possible) | highest-value new request |
| new | Osakabe, Kotai Butsuri 25(9), 591-596 (1990) (J-h) | NO | library request |

## 1. Si(001) surface structure and steps (task 1)

### 1.1 Sources found and read

| # | Source | Access, URL read, hash (file in `l7/pdf/`) | Label |
|---|---|---|---|
| R1 | A. Ramstad, G. Brocks, P. J. Kelly, "Theoretical study of the Si(100) surface reconstruction", Phys. Rev. B 51, 14504-14523 (1995), DOI 10.1103/PhysRevB.51.14504 | OPEN (green): University of Twente file `https://ris.utwente.nl/ws/files/125986814/PhysRevB.51.14504.pdf` (the APS typeset pages; OpenAlex calls it "submittedVersion"); read in full (21 PDF pages); SHA-256 f7000f88...c68 | SECTION_READ (sec. II, IV A, IV C; Tables III, IV; Figs. 16, 18) + METADATA_VERIFIED (Crossref) |
| R2 | H. J. W. Zandvliet, "Energetics of Si(001)", Rev. Mod. Phys. 72, 593-602 (2000), DOI 10.1103/RevModPhys.72.593 (an erratum exists: RMP 73, 247 (2001), DOI 10.1103/revmodphys.73.247, not read) | OPEN: `https://ris.utwente.nl/ws/files/6767412/Zandvliet00energetics.pdf` ("Final published version" on the Twente record `https://research.utwente.nl/en/publications/energetics-of-si001/`; the `research.utwente.nl/files/...` link served a Cloudflare challenge, not bypassed; the `ris.utwente.nl` file host served the PDF directly); read in full; SHA-256 ad9eaf47...a02f | SECTION_READ (sec. II, IV, V B; Tables I, II; Eqs. (1), (19); Figs. 1, 8) + METADATA_VERIFIED (Crossref) |
| R3 | Y. Horio, Y. Takakuwa, S. Ogawa, "Dimer Configuration of Si(001)2x1 Surface by Projected Potential Approach of Reflection High-Energy Electron Diffraction", e-J. Surf. Sci. Nanotech. 12, 380-386 (2014), DOI 10.1380/ejssnt.2014.380 | OPEN (J-STAGE `.../ejssnt/12/0/12_380/_pdf/-char/ja`); read in full; SHA-256 99ae4541...cbe3 | SECTION_READ (secs. I-V, Table I, Figs. 2-3) |
| R4 | T. Shirasawa, S. Mizuno, H. Tochihara, "Si(001), Ge(001)表面における c(4x2)構造の解析と c(4x2)-p(2x1)相転移の臨界現象", 27aYB-8, JPS 概要集 61(1-4), 865 (2006), DOI 10.11316/jpsgaiyo.61.1.4.0_865_1 | OPEN (J-STAGE); read; SHA-256 97c0a727...23f | SECTION_READ (p. 865, 27aYB-8) |
| R5 | T. Shirasawa, S. Mizuno, H. Tochihara, "Structural Modification of Si(001)-c(4x2) Induced by Electron Beam at Low Temperatures", Hyomen Kagaku 26(8), 480-485 (2005), DOI 10.1380/jsssj.26.480 | OPEN (J-STAGE); read in full; SHA-256 9b7d8a4b...7cc1 | SECTION_READ (abstract; sec. 1, p. 480; sec. 5) |
| R6 | K. Hayashi, A. Kawasuso, A. Ichimiya, "Adsorption of Oxygen on Si(001) Surfaces Studied by Reflection High-Energy Positron Diffraction", e-J. Surf. Sci. Nanotech. 4, 510-513 (2006), DOI 10.1380/ejssnt.2006.510 | OPEN; read in full; SHA-256 cb465cb7...14bc | SECTION_READ (Fig. 4 and its tables, p. 512) |
| R7 | T. Ogino, H. Hibino, Y. Homma, "シリコン表面の原子ステップ配列制御", Oyo Buturi 66(12), 1289-1297 (1997), DOI 10.11470/oubutsu1932.66.1289 | OPEN; read in full; SHA-256 6ff4a1db...0570 | SECTION_READ (p. 1289 sec. 1; p. 1293 sec. 3.1). Mostly Si(111); gives the step heights only |

Closed or not attempted (identity METADATA_VERIFIED by Crossref on 2026-09-23; OpenAlex `open_access` = closed for each; content UNVERIFIED): D. J. Chadi, PRL 59, 1691 (1987), 10.1103/physrevlett.59.1691; H. Over et al., PRB 55, 4731 (1997) (LEED of Si(001)-(2x1)), 10.1103/physrevb.55.4731; R. Felici et al., "Room temperature Si(001)-(2x1) reconstruction solved by X-ray diffraction", Surf. Sci. 375, 55 (1997), 10.1016/s0039-6028(97)80005-2; M. Takahasi et al., "Surface X-ray diffraction study on the Si(001)2x1 structure", Surf. Sci. 338, L846 (1995), 10.1016/0039-6028(95)00663-x; T. Shirasawa et al., Surf. Sci. 600, 815 (2006) (LEED of c(4x2), 8 layers), 10.1016/j.susc.2005.11.031; T. Tabata et al., Surf. Sci. 179, L63 (1987), 10.1016/0039-6028(87)90114-2; T. Abukawa et al., PRB 62, 16069 (2000), 10.1103/physrevb.62.16069; O. L. Alerhand et al., PRL 64, 2406 (1990), 10.1103/physrevlett.64.2406; E. Pehlke and J. Tersoff, PRL 67, 465 and 1290 (1991); P. E. Wierenga et al., PRL 59, 2169 (1987); B. S. Swartzentruber et al., PRL 65, 1913 (1990); T. Shirasawa et al., PRL 94, 195502 (2005).

### 1.2 Facts extracted (with locators)

Dimer geometry (T = 0 DFT, R1):
* Method (R1 sec. II, p. 14506): LDA (Ceperley-Alder, Perdew-Zunger), norm-conserving pseudopotentials, 12-layer slab, vacuum "= 9.5 Å", five outermost layers relaxed on each side, two central layers at bulk positions, experimental a = 5.43 Å; geometries at 16 Ry and four k points (sec. IV C).
* Coordinates (R1 Table III caption, p. 14516): ideal positions R_klm = (k√2, l√2, m) a/4 with a = 5.431 Å, i.e. x and y in units of 1.920 Å and z in units of 1.358 Å, z < 0 into the bulk; x along the dimer bond, y along the dimer row (Fig. 1). Displacements (Å) are tabulated for five layers: Table III for p(2x1)s and p(2x1)a (2 atoms per layer, Δy = 0), Table IV (p. 14517) for p(2x2) and c(4x2) (4 atoms per layer, Δx, Δy, Δz). Example rows, Table IV, c(4x2): layer 1 (0,0,0) Δx 0.989, Δz −0.789; (2,0,0) −0.685, −0.055; (0,2,0) 0.675, −0.045; (2,2,0) −1.001, −0.788; layer 2 (0,1,−1) 0.108, 0.120, −0.079; layer 3 (1,1,−2) Δz −0.223, (3,1,−2) Δz 0.066; layer 5 Δz −0.023 to −0.040. The full tables are transcribed in section 1.4 below for the builder.
* Bond lengths and buckling (R1 p. 14516-14517, Fig. 18): p(2x1)s dimer 2.23 Å, back bonds 2.27 Å, top-layer vertical relaxation 0.524 Å; p(2x1)a dimer 2.26 Å, buckling 18.3°, back bonds 2.34/2.29 Å; p(2x2) dimer 2.28 Å, buckling 18.9° and 19.3°; c(4x2) dimer 2.29 Å, buckling 18.7° and 18.9°; bulk bond 2.35 Å.
* Energies (R1 Fig. 16, sec. IV A): ideal → p(2x1)s 1.8 ± 0.1 eV/dimer; p(2x1)s → p(2x1)a 0.12 ± 0.01; p(2x1)a → p(2x2) 0.048 ± 0.018; p(2x2) → c(4x2) 0.003 ± 0.013 eV/dimer.
* Temperature caveat (R1 p. 14518): "the calculated geometries should only be compared with geometries determined experimentally at low temperature"; room-temperature TED and grazing-incidence x-ray analyses "were fitted assuming a uniform structure with p(2 x 1) periodicity" and gave buckling angles "about 5° and 7°", "substantially smaller than the 19° which we calculate for zero temperature". R1 p. 14520: "STM clearly indicates that the p(2x1) structure at room temperature does not consist of static disordered buckled dimers"; low-temperature LEED and STM indicate a c(4x2) ground state.

Room-temperature structure (R3, R4, R5):
* R4 (p. 865): "ダイマーの傾斜の向きは室温では頻繁に変化しており、みかけの周期は p(2x1) になる"; below the transition the c(4x2) forms; LEED I-V at 80 K determined atom positions "表面から8原子層まで"; c(4x2)-p(2x1) transition at 205 ± 3 K for Si(001) (276 ± 6 K for Ge(001)), 2-D Ising exponents. (The 8-layer coordinates are in Surf. Sci. 600, 815, closed.)
* R5 (p. 480): near room temperature the dimers are tilted and fluctuate by thermally activated flip-flop, STM sees apparently symmetric dimers, LEED shows streaks (loss of inter-row order); "約150 K以下では flip-flop 運動は凍結し" the c(4x2) forms. Electron-beam-induced disordering of c(4x2) occurs only below about 40 K (abstract), so it is irrelevant at room temperature.
* R3 (abstract; sec. V, p. 385): many-beam RHEED rocking curves (10 kV, [1-10] azimuth, UHV 1e-7 Pa, sample flashed to about 1200 °C, p. 381) fitted with a "projected potential approach" that superimposes the time-averaged up and down atoms of each flipping dimer (sec. III, p. 382): at RT the dimers are "fundamentally the same as that for the static Si(001)c(4x2) surface"; az − bz = 0.71 Å, α = 18.1° (Table I "Present": rAB 2.28 Å, az 1.38, bz 0.67, xCD 3.60, yCC' 3.60, yDD' 4.08 Å, heights relative to the second layer, a0 = 3.84 Å); at 880 K 0.43 Å and 10.9°, at 1031 K 0.29 Å and 7.4°. R3 Table I also reprints the c(4x2) parameters of CTDS (α 18 ± 1°, rAB 2.28 Å), R1 (18.8°, 2.29 Å), PED (18.6 ± 1°, 2.26 Å) and SXRD (Felici 1997; 20 ± 3°, 2.67 Å). R3 notes that the RT SXRD of Takahasi et al. gives az − bz = 0.87 Å and one-beam RHEED 0.6 Å (sec. V). R3 used a 10 % imaginary potential and a Debye vibration amplitude of 0.07 Å at RT (p. 383): model choices of that paper, not measured absorption.
* R3 (p. 383): the 2x1 and 1x2 domains on adjacent terraces were summed "not with respect to coherency but to intensity, because the averaged terrace width is considered to be almost equal to or larger than the coherence length for the incident electron beam".
* R6 (Fig. 4, p. 512): RHEPD at 110 K, the unoxidised Si(001) region modelled with asymmetric dimers, vertical spacings 0.8 Å (between the two dimer atoms) and 0.7 Å (to the next layer), with per-atom Debye parameters B = 1.01 Å² (top) and 0.22 Å² (lower) used in the positron calculation. Not transferable to 200 keV electrons as absorption values.

Steps (R2, R7):
* Step height (R2 Fig. 1 caption and p. 601; R7 p. 1289): a0/4 = 1.36 Å on (001) ("0.136nm", R7), with a0 = 5.43 Å and surface lattice a = 3.84 Å.
* Step types (R2 p. 594): "those that run along the dimer rows of the upper terrace (SA steps) and those that run perpendicular to the dimer row direction of the upper terrace (SB steps)"; on surfaces miscut along [110] they alternate; SA smooth, SB with "a high density of thermally excited kinks"; the dimer direction rotates by 90° at each single-layer step (2x1/1x2 domains); a double-layer-stepped surface is single-domain; rebonded SB steps are much more frequent than non-bonded ones (p. 595). The Si(001) step structure "is static at room temperature" with a freeze-in temperature between 750 and 875 K (p. 596).
* Step energies: Chadi's 1987 tight-binding values as reprinted in R2 Table I (p. 596): SA 0.02, SB 0.30, DA 1.08, DB 0.10 eV/2a (a = 3.84 Å). Measured values, R2 Table II (p. 597): SA 0.052-0.064, SB 0.12-0.18, DA 0.30, DB 0.092-0.10 eV/2a (Swartzentruber 1990, Eaglesham 1993, Pearson 1995, Bartelt and Tromp 1996, Laracuente and Whitman 2000, Zandvliet et al. 1992). Surface stress anisotropy 0.9 ± 0.2 eV/a² (p. 598). Chadi's own paper is closed; its values are cited here from R2, i.e. second-hand.
* Terrace width vs miscut (R2 p. 595, below Eq. (1)): "The average spacing between the steps is given by L = d/tan(θ)".
* Single- to double-layer transition (R2): "For miscut angles larger than about 1.5° toward [110], double-layer steps begin to form and their fraction increases with increasing miscut angle toward a maximum of nearly 100% at 5-6°" (p. 594); "for θ larger than 4-5°, the surface contains predominantly double-layer steps (Wierenga et al., 1987; Aumann et al., 1988)"; below about 0.03° hill-and-valley with step loops; 0.03-0.1° wavy and straight steps; 0.1° to 1.5-2° alternating SA/SB (p. 600); the model of Eq. (19) with T_f = 825 K predicts the transition "at ~2°"; "STM experiments have revealed that Si(001) is single-layer stepped for a miscut angle below 1° and double-layer stepped above 4°. In the range 1-4° single- and double-layer steps have been found experimentally to coexist" (p. 601). Only DB double steps are found (DA has a much higher energy, p. 600). All of this is for thermally equilibrated (UHV-annealed) surfaces.

### 1.3 Inferences for the model (DERIVED_HERE unless stated)

* Terrace widths for the a/4 step (d = a/4 = 1.35775 Å, a = 5.431 Å): L = d/tan θ = 1555.9 Å at 0.05°, 777.9 Å at 0.1°, 311.2 Å at 0.25°, 155.6 Å at 0.5°, 77.8 Å at 1°; for DB steps (2d) double these, but DB steps dominate only above about 4° (L_DB = 38.8 Å at 4°). These agree with H2 section 4 to rounding (H2 prints 1555.8 Å at 0.05°).
* REPRODUCED here from R1 Table IV (c(4x2), layer 1): horizontal dimer projection a/√2 − 0.989 − 0.685 = 2.166 Å, height difference 0.789 − 0.055 = 0.734 Å, bond 2.287 Å and buckling 18.7°; second dimer 2.288 Å and 18.9°; p(2x1)s 2.230 Å; p(2x1)a 2.258 Å and 18.3°. These match R1's printed values (Fig. 18, p. 14517), which checks the transcription and the frame (atoms k = 0 and k = 2 are a/√2 = 3.840 Å apart before dimerisation).
* Consequence for Ali's a/2 steps: on an annealed surface a/2 (DB) steps are the equilibrium step only above a few degrees of miscut. On a nominal (001) wafer (R3's sample: "cut within ±0.1°", p. 381) single-layer steps dominate. a/2 height differences on a low-miscut surface therefore indicate either a large local miscut, two single steps closer than the resolution, or a non-equilibrium (ion-milled, unannealed) topography. This should be stated in the paper; which applies is PROJECT_INPUT item 11 and 12.
* Which termination for a room-temperature 200 keV experiment: the time average of flip-flopping buckled dimers (R3, R4, R5). Three sourced ways to put it in a static multislice, each an ASSUMPTION to be labelled: (a) frozen snapshots with random buckling per dimer (or c(4x2)/p(2x2) domains of R1 Table IV coordinates) averaged incoherently like frozen phonons; (b) R3's projected-potential superposition (both buckling states at half weight, one static potential); (c) the symmetric p(2x1)s of R1 Table III as a limiting case. (a) is the physically closest to a flip-flop time much shorter than the exposure; (b) is what RHEED rocking-curve work uses. The differences between (a), (b), (c) in the step phase are unknown and are a candidate sensitivity test.
* B4 scope: with a 2x1 reconstruction the upper and lower terraces of a single-layer step carry dimer rows rotated by 90° (R2 p. 594). At an exact <100> azimuth, which is at 45° to both <110> dimer-row directions, the two terrace types remain related by the d-glide (C2 sec. 1) only if the reconstructed layer maps onto itself under that operation; for the symmetric and time-averaged (b) models this is plausible by the 4_1 screw relation of the diamond lattice (spec 4.2), but it must be checked in the builder with the R1 coordinates, not assumed. At a <110> azimuth the beam is parallel to the dimer rows on one terrace and perpendicular on the next, so the reflectivities differ and the phase residual δ of B4 is expected to be non-zero.

### 1.4 Transcription of R1 Tables III and IV (for the dimer_2x1 option of `si001.py`)

Source: R1 Table III (p. 14516) and Table IV (p. 14517), SECTION_READ; transcribed from the page images of the Twente
PDF; the transcription is checked by the REPRODUCED bond lengths and angles in 1.3. Frame (Table III caption): ideal
position R_klm = (k√2, l√2, m)·a/4, a = 5.431 Å (x, y unit 1.920 Å; z unit 1.358 Å; z < 0 into the bulk); x along
the dimer bond, y along the dimer row. Layers 6 and deeper: ideal bulk positions (R1 relaxed five layers per side).
Displacements in Å. For p(2x1)s and p(2x1)a all Δy = 0 (R1: of order 1e-5 Å).

p(2x1) cell (2 atoms per layer; period 4 units in x = 7.681 Å, 2 units in y = 3.840 Å):

| layer | (k, l, m) | p(2x1)s Δx | p(2x1)s Δz | p(2x1)a Δx | p(2x1)a Δz |
|---|---|---|---|---|---|
| 1 | (0,0,0) | 0.805 | −0.524 | 1.162 | −0.921 |
| 1 | (2,0,0) | −0.805 | −0.524 | −0.534 | −0.213 |
| 2 | (0,1,−1) | 0.075 | −0.141 | 0.066 | −0.141 |
| 2 | (2,1,−1) | −0.075 | −0.141 | −0.099 | −0.112 |
| 3 | (1,1,−2) | 0.000 | −0.216 | 0.031 | −0.240 |
| 3 | (3,1,−2) | 0.000 | 0.005 | −0.025 | −0.003 |
| 4 | (1,0,−3) | 0.000 | −0.139 | −0.013 | −0.155 |
| 4 | (3,0,−3) | 0.000 | 0.002 | −0.005 | 0.002 |
| 5 | (0,0,−4) | −0.022 | −0.040 | −0.042 | −0.044 |
| 5 | (2,0,−4) | 0.022 | −0.040 | 0.022 | −0.040 |

p(2x2) and c(4x2) (4 atoms per layer, same ideal positions for both; Table IV):

| layer | (k, l, m) | p(2x2) Δx | Δy | Δz | c(4x2) Δx | Δy | Δz |
|---|---|---|---|---|---|---|---|
| 1 | (0,0,0) | 0.992 | 0.000 | −0.832 | 0.989 | 0.000 | −0.789 |
| 1 | (2,0,0) | −0.688 | 0.000 | −0.094 | −0.685 | 0.000 | −0.055 |
| 1 | (0,2,0) | 0.675 | 0.000 | −0.076 | 0.675 | 0.000 | −0.045 |
| 1 | (2,2,0) | −1.010 | 0.000 | −0.829 | −1.001 | 0.000 | −0.788 |
| 2 | (0,1,−1) | 0.105 | 0.119 | −0.101 | 0.108 | 0.120 | −0.079 |
| 2 | (2,1,−1) | −0.118 | −0.112 | −0.109 | −0.120 | −0.117 | −0.086 |
| 2 | (0,3,−1) | 0.105 | −0.118 | −0.101 | 0.108 | −0.119 | −0.079 |
| 2 | (2,3,−1) | −0.118 | 0.113 | −0.109 | −0.120 | 0.117 | −0.086 |
| 3 | (1,1,−2) | −0.011 | 0.001 | −0.237 | −0.009 | 0.001 | −0.223 |
| 3 | (3,1,−2) | −0.003 | 0.002 | 0.050 | −0.003 | 0.020 | 0.066 |
| 3 | (1,3,−2) | −0.011 | 0.000 | −0.237 | −0.009 | 0.000 | −0.223 |
| 3 | (3,3,−2) | −0.003 | −0.002 | 0.050 | −0.003 | −0.020 | 0.066 |
| 4 | (1,0,−3) | 0.024 | 0.000 | −0.160 | 0.006 | 0.000 | −0.153 |
| 4 | (3,0,−3) | 0.037 | 0.000 | 0.037 | −0.005 | 0.000 | 0.069 |
| 4 | (1,2,−3) | −0.031 | 0.000 | −0.164 | −0.011 | 0.000 | −0.155 |
| 4 | (3,2,−3) | −0.048 | 0.000 | 0.034 | −0.006 | 0.000 | 0.028 |
| 5 | (0,0,−4) | −0.012 | 0.000 | −0.039 | −0.041 | 0.000 | −0.023 |
| 5 | (2,0,−4) | 0.066 | 0.000 | −0.030 | 0.039 | 0.000 | −0.040 |
| 5 | (0,2,−4) | −0.074 | 0.000 | −0.031 | −0.045 | 0.000 | −0.038 |
| 5 | (2,2,−4) | 0.007 | 0.000 | −0.041 | 0.037 | 0.000 | −0.023 |

Cell vectors (DERIVED_HERE, not printed in R1's tables; check against R1 Fig. 1 before use): p(2x2): (4, 0) and
(0, 4) in 1.920 Å units; c(4x2) primitive cell: (4, 2) and (0, 4), i.e. neighbouring dimer rows shifted by one dimer
along y so that their buckling is in antiphase. Both cells contain 4 atoms per layer, which is why R1 lists identical
ideal positions. Along a row, both have the buckling alternating from dimer to dimer (layer-1 rows (0,0,0)/(2,0,0)
and (0,2,0)/(2,2,0) have opposite up/down sides in Table IV).

Caveats (ASSUMPTION when used): T = 0 LDA geometries; the room-temperature surface is a flip-flopping average
(1.2); R1's five-layer relaxation is truncated at layer 5 (the layer-5 Δz of −0.02 to −0.04 Å is not zero, so a
builder should check the continuity to bulk); experimental LEED/SXRD coordinates exist but are closed (1.1).

## 2. Ion-milled Si surfaces: damage layer, oxide, densities, preparation practice (task 2)

### 2.1 Sources read

| # | Source | Access, URL, hash | Label |
|---|---|---|---|
| D1 | M. Morita, T. Ohmi, E. Hasegawa, M. Kawakami, M. Ohwada, "Growth of native oxide on a silicon surface", J. Appl. Phys. 68(3), 1272-1281 (1990), DOI 10.1063/1.347181 | OPEN (green, publisher version): Tohoku University repository `https://tohoku.repo.nii.ac.jp/record/53635/files/JApplPhys_68_1272.pdf`; read in full; SHA-256 aa31b7b2...d3a6 | SECTION_READ (sec. II; III A; III C; Table I; Table III; Figs. 1, 8, 14; Appendix) + METADATA_VERIFIED (Crossref) |
| D2 | J. Uzuhashi, T. Ohkubo, "Systematic study of FIB-induced damage for the high-quality TEM sample preparation", Ultramicroscopy 262, 113980 (2024), DOI 10.1016/j.ultramic.2024.113980 | OPEN: accepted manuscript, CC BY-NC-ND 4.0, NIMS MDR `https://mdr.nims.go.jp/filesets/d635fe8c-8039-453c-9964-3f0e550c6746/download` (MDR DOI 10.48505/nims.4497); read in full; SHA-256 cba59d51...9989 | SECTION_READ (Methods; Results pp. 4-5; Discussion pp. 6-7; Figs. 1, 2, 4, 5) + METADATA_VERIFIED (Crossref) |
| D3 | L. Pastewka, R. Salzer, A. Graff, F. Altmann, M. Moseler, "Surface amorphization, sputter rate, and intrinsic stresses of silicon during low energy Ga+ focused-ion beam milling", Nucl. Instrum. Methods B 267(18), 3072-3075 (2009), DOI 10.1016/j.nimb.2009.06.094 | OPEN: preprint "submitted to Elsevier June 16, 2009", Fraunhofer publica `http://publica.fraunhofer.de/bitstreams/a5602adc-db41-4b6c-a3e7-82b989035951/download`; read in full; file `l7/pdf/rommel2009.pdf`, SHA-256 e9148c5c...28d1. Locators are preprint pages; the published version may differ | SECTION_READ (preprint: abstract; sec. 3-4, 6; Figs. 2, 4) + METADATA_VERIFIED (Crossref) |

### 2.2 Facts extracted

Native oxide (D1; n-, n+- and p+-Si(100) wafers, chemically cleaned and HF-etched, then exposed to clean-room air at
23.7 °C and 42 % humidity, sec. II and III A):
* Thickness method (sec. II, p. 1273): XPS Si2p oxide/substrate area ratio calibrated against ellipsometry of 70-140 Å
  thermal oxides; "The native oxide film thickness determined by above-described method is considered to be correct as
  long as the atomic density of the native oxide is equal to that of the thermal oxide" (i.e. thickness in
  thermal-oxide-equivalent units).
* Growth in air (Fig. 1 and text, p. 1273): layer-by-layer, "approximately successive step functionlike increase"; for
  n-Si "the growth to 5.4 Å and the succeeding increase to 7.6 Å correspond to two molecular layers of growth followed by
  one additional layer"; initial thickness after dilute HF 4.4 Å (n+), 1.9 Å (n), 2.3 Å (p+) (Fig. 1 time axis 10^0
  to 10^5 min).
* Table I (7 days): air with about 1.2 % H2O (42 % RH) 6.7 Å; O2/N2 with < 0.1 ppm H2O 1.7 Å; N2 < 0.1 ppm H2O 1.9 Å.
  "the native oxide hardly grows at all even after 7 days exposure to the air when the H2O concentration in air is
  suppressed less than 0.1 ppm" (p. 1273).
* Fig. 8 legend: n-Si(100) "IN AIR 73days 8.2Å"; Table III: in air 4 days 5.6 Å.
* p. 1279: at room temperature the Si atoms of the overlayer "converts to the amorphous phase".
* Scope: HF-last wafers, not ion-milled surfaces (DERIVED_HERE caveat: oxidation of an ion-amorphised Si surface in air
  is not covered by D1).

Ga+ FIB damage in Si (D2, D3):
* D2 (p. 3; Fig. 2): sidewalls milled at 30 keV (90 pA), 8, 5 and 2 keV, observed by cross-sectional LAADF-STEM at 200
  keV; amorphous thicknesses "~22 nm (30 keV), ~7 nm (8 keV), ~4 nm (5 keV), and ~1 nm (2 keV)" (pp. 4-5); SRIM Ga
  implantation depth (99 % of ions, 89.5° incidence) 25, 8, 5, 5 nm at 30, 8, 5, 2 keV (Fig. 4c legend); a
  "crystal distortion" layer below the amorphous layer (brighter LAADF contrast from about 22 to 29 nm at 30 keV, p. 4);
  amorphous/total damage about 75 % for Si at 30 keV (p. 7); "the FIB-damaged amorphous thickness is changed by
  accelerating voltage irrespective of the beam current" (p. 5, confirming Kato et al.). Fig. 2(c) also plots Mayer et
  al. 2007, Giannuzzi et al. 2005, Burnett et al. 2016 and Kato et al. 1999 (values read off the figure are not quoted
  here).
* D3 (abstract; Fig. 2c-d; sec. 6): sidewall damage "around 20 to 30 nm for silicon at typical beam energies of 30 keV";
  measured amorphous layers 1.4 nm (2 kV polish) and 4.6 nm (5 kV polish) (Fig. 2c, 2d); MD at 1-5 keV and 10° grazing
  (80° from the normal): thickness "depends linearly on the beam energy"; the thickness "scales approximately linear with
  the cosine of the incident angle ... at 80° a variation of ±5° can lead to a change in thickness of ±50 %" (sec. 6,
  p. 10); experimental error about 2 nm between positions (Fig. 4 caption).

