# L5 - Open-access check of the paper items before any upload request to Ali

Status: complete, 2026-09-22. Agent L5 (literature, open-access route). Network access: Full
(HTTPS through the preconfigured agent proxy). No repository file other than this report was edited.
Nothing was committed or pushed.

Raw downloads are kept outside the repository, in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/oa/`
(called `oa/` below). Section 0 lists every file that was read, with its URL, retrieval date
(2026-09-22) and SHA-256.

Label policy (project instruction file, section 1.4): METADATA_VERIFIED, SECTION_READ (only with a
locator), REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED. Two sub-labels are used
here:
* `+ABSTRACT(publisher)`: an abstract this agent read in the publisher's own landing-page HTML.
* `+ABSTRACT(PubMed)`: the PubMed abstract read in the Europe PMC REST record.

Both are stronger than the earlier `+ABSTRACT(index)` (search-engine summaries) and weaker than
SECTION_READ of the body. An abstract never counts as SECTION_READ of the paper. An OpenAlex or
Semantic Scholar OA flag is metadata, not evidence of access. Every "open" or "closed" verdict below
was checked on the host itself wherever the host could be reached.

Method per item:
1. `https://api.openalex.org/works/doi:<doi>` (open_access, best_oa_location, locations).
2. `https://api.crossref.org/works/<doi>` for metadata.
3. The publisher landing page, fetched with curl and, where curl met a bot challenge, with the
   WebFetch tool.
4. Where the landing page was unreachable, the Elsevier article API coredata
   (`openaccess`/`openaccessArticle` flags, fetched without an API key) or the Europe PMC record
   (`fullTextUrlList` availability).
5. Every repository location listed by OpenAlex (PMC, OSTI, eScholarship, HAL, White Rose, TARA,
   Minerva, DTU Orbit, CORE), fetched directly.
6. arXiv API searches.

No shadow library was used or searched. No bot challenge was circumvented. Where a host served a
challenge page (Cloudflare, AWS WAF, Radware, Imperva) this is recorded as "host unreadable".

## 0. Files retrieved (URL, date 2026-09-22, SHA-256)

### 0a. Documents read

| file in oa/ | URL fetched | SHA-256 | what it is |
|---|---|---|---|
| p01_iop_landing_via_pdf_url.html | https://iopscience.iop.org/article/10.1143/JJAP.27.L1772/pdf (IOP served the article landing page, not a PDF) | 7c41d0c13925711318da1d06ce59c75744973e24407bae79b812144b5815c311 | IOP landing page of P01: abstract, dates, access block, citation meta tags |
| P02E_PhysRevLett.63.584.3.pdf | https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.63.584.3 (retrieved through WebFetch; curl gets a Cloudflare challenge) | 2c1cced352ff0b08acbc5b29e5c67c4be22b9ac64539ccedb1a8adad78c46d70 | APS erratum page 584, 2 PDF pages (scanned; read as rendered images at 200 dpi) |
| C03_whiterose_127795_AM.pdf | https://eprints.whiterose.ac.uk/id/eprint/127795/1/Ptychography_Chapter-Rodenburg%2BMaiden_final.pdf | 861bcaa9785991a4e96197e7a7761077705c7d09b586e732a10f9a95983f06b5 | C03 author accepted manuscript, 138 PDF pages |
| whiterose_127795.html | https://eprints.whiterose.ac.uk/127795/ | bcc30249f1ed74b1271c592985270f9c23d85383088ec91af4f3ebf7034fb33f | White Rose record of C03 (version statement, full_text_status public) |
| HYTCH2010_hal-01742031.pdf | https://hal.science/hal-01742031/document | eae3b6f52ef9d3eba12dcac0b14be9bb559f4cda6ac7fe47dbede38a8b2d0a48 | Hÿtch, Houdellier, Hüe, Snoeck, J. Phys.: Conf. Ser. 241 (2010) 012027; companion paper to P31, 8 PDF pages (2 HAL/IOP cover pages plus the article) |
| MIP_arXiv_2607.05948v1.pdf | https://arxiv.org/pdf/2607.05948v1 | 72f7e54f350b14e66dfed2a7e879aa583e567842afec34d9d6e20d8984ece3b3 | Schowalter, Kruse, Rosenauer, arXiv:2607.05948v1 (7 Jul 2026), 5 pages |
| MIP_arXiv_2607.05948v1_abs.html | https://arxiv.org/abs/2607.05948v1 | 7d01da6fc46d31292d67f4605c7c57a4d3ae93f5020196ff7916c699cd448aa5 | arXiv abstract page |
| zenodo_18449230.json | https://zenodo.org/api/records/18449230 | 5a7aef1a445a7b5f0767df985131ec21443d336892f9768c74ce3cf19c8f61be | Zenodo record of the MIP preprint's data (CC BY 4.0) |
| zenodo_GeSi_11_2.tgz | https://zenodo.org/api/records/18449230/files/GeSi_11_2.tgz/content | 106c4ac88e1d2ed0d3085961a8960b946d968342cb6714e7721d031191c77e7f | GeSi supercell inputs and V96.out files; pure-Si file `GeSi_11_2/Ge0p0Si/Ge0p0SiSi_1/V96.out` has SHA-256 649ab8d30fc669532221e88ee208c9ea9a7ba5ebf83428d5fb28252256d3c39b |
| zenodo_go_lapw5.tgz | https://zenodo.org/api/records/18449230/files/go_lapw5.tgz/content | c40c5eef0f502e100b7344d0427edcd41b3c997e31477e0215f2533d6a46f682 | workflow scripts and Readme.txt files |

### 0b. Access and metadata evidence (JSON, XML, HTML records)

| file in oa/ | URL fetched | SHA-256 |
|---|---|---|
| openalex_10.1143_JJAP.27.L1772.json | https://api.openalex.org/works/doi:10.1143/JJAP.27.L1772 | 70d91067f982d33baf28c5693192298807e800ba3e9c701b705a9ba966af1205 |
| openalex_10.1002_jemt.1070200415.json | .../works/doi:10.1002/jemt.1070200415 | eb4203c72f9d55e6b94e5af57244e64cf1b34ea4ab45b698ed2e2d9e74a50756 |
| openalex_10.1002_jemt.1070200414.json | .../works/doi:10.1002/jemt.1070200414 | 2878af29812b240a9ca4b0b95ed6a822b42bac70c09615369f96854ff53977e1 |
| openalex_10.1103_PhysRevLett.62.2969.json | .../works/doi:10.1103/PhysRevLett.62.2969 | d6c3ebdc99f4dce2e9067d660ad0be01dce24cfc27a96adf8291aca1823a4e8a |
| openalex_10.1103_PhysRevLett.63.584.3.json | .../works/doi:10.1103/PhysRevLett.63.584.3 | d2fe2199bd212cc65b8e34e8f669ecc17d11aa4d0a18b0c7ef4d811ff01a4d9b |
| openalex_10.1016_0304-3991_93_90123-F.json | .../works/doi:10.1016/0304-3991(93)90123-F | cc513aa946e5dd785a19161198d5ccf596335f81a80949b33a0e2a6b08cedeb4 |
| openalex_P31.json | .../works/doi:10.1016/j.ultramic.2011.04.008 | 3bba1ee15e182bc5c8be58f75523ac7a333739c4ffcbf7399dcfde2a2d9b1081 |
| openalex_10.1016_j.micron.2021.103141.json | .../works/doi:10.1016/j.micron.2021.103141 | 3c241807c9f2223550cf6acdb16d48655f443dafa3509ab6f68b57abd0d06f72 |
| openalex_10.1016_j.ultramic.2009.05.012.json | .../works/doi:10.1016/j.ultramic.2009.05.012 | 14e9f515deced58593d291d4e618725f07bb32d5e457f0cbff779af4fe83dbfe |
| openalex_10.1007_978-3-030-00069-1_17.json | .../works/doi:10.1007/978-3-030-00069-1_17 | 7eee2ce06f6cd1b40019ce271746634cf6d228ff3382053f0ef89f4f9bd22eae |
| openalex_10.1007_978-1-4615-4817-1_6.json | .../works/doi:10.1007/978-1-4615-4817-1_6 (C01) | 0517fc051c3ead31ec365e372f99d16364e93bd0ae05944c824b15f699c474b0 |
| openalex_10.1007_978-3-030-00069-1_16.json | .../works/doi:10.1007/978-3-030-00069-1_16 (C02) | c60050dff331e3b4ef24042c33ceaf758536e411195164acc884d970704008ab |
| openalex_10.1007_978-3-540-37204-2_7.json | .../works/doi:10.1007/978-3-540-37204-2_7 (B10 ch. 7) | aac2dcae1fbf598532a8edb6004c02b31fb95fb37984e519cb738cca7c7e91cc |
| openalex_10.1016_j.ultramic.2005.06.057.json | .../works/doi:10.1016/j.ultramic.2005.06.057 (Kruse 2006) | f403fba48c54e389d34d5f7308ae4334375067b4f71377b37f175eb73d1a9966 |
| oamip_*.json (11 files) | .../works/doi:<doi> for the MIP candidates of section 4 | e.g. oamip_10.1016_j.micron.2026.104079.json 55f4eebbd3afb6480dff71e66b617ff87176613421aeccf3283a66ef54ac1a73; oamip_10.1016_0304-3991_93_90197-6.json 0dd743cb62a0f357868a41d629922fa4cd26291d889e8856411ca0bffa9a28c3; oamip_10.1063_1.118556.json 30d9d70d92a030c84d5648b05db3132b4f5a11a9187d31c8ba250f47c14c826f; oamip_10.1016_j.ultramic.2023.113862.json 568b707b91673ca5b5743c47d94c7965cd3bbe3e1cf55a2611e3d55f32454588; oamip_10.1016_j.ultramic.2015.07.011.json b821f99a9b48f44dcc35f847cf626c526890bf41ab2efbac0046ce1e2eee7269; oamip_10.1107_S010876739300474X.json 2cb6f68c392c0572746be733832ec9ad2b694e97ca790686e60a5a5ab3d355da; oamip_10.1107_S0108767393013200.json caa586d6a8ad5b4b1d9eeb63a524be368de98717b8b3586f9215819aa84da466; oamip_10.1103_PhysRevLett.81.2695.json 1701a962e8001f4a7b4ed5697dc6f28790f4dd82d066722dfcda689c7fcfc582; oamip_10.1007_3-540-31915-8_47.json e30c2acc83ae689427f3d892c12fb17003bd7e3fe24dcb4833749b3bfa069502; oamip_10.1007_978-4-431-56940-4_33.json d9c3b81c409ccd3e8f966ec438b134cc348feb29cb238ce4197a36cbe25071e9; oamip_10.1017_s0424820100121077.json 2ab276564dd68f3142b335a8c196dff894ce0ab452dfa3939097400b81683f69 |
| epmc_10.1002_jemt.1070200415.json | Europe PMC REST `search?query=DOI:10.1002/jemt.1070200415&resultType=core&format=json` | af90811f5e7bf689780822415fbe4db01f64bf651e63576b18996c874c3f6371 |
| epmc_10.1002_jemt.1070200414.json | same, DOI 10.1002/jemt.1070200414 | 7f4231aa05a7d82d2f592dc38e80a38764aeb98375f65be994c702ab3d0d227a |
| epmc_10.1103_PhysRevLett.62.2969.json | same, DOI 10.1103/PhysRevLett.62.2969 | a9f48c144b9d9563067c4a923a84f8bd3b8e658b08a96a299fd67549a77c2c26 |
| epmc_10.1016_j.ultramic.2011.04.008.json | same, P31 | c1160a05ed612809c521cc045591fca6b0c597e48a7d78f9eb6a1d6da279240e |
| epmc_10.1016_j.ultramic.2009.05.012.json | same, P06 | 4d945ec82758cf367bb0a6d2461f124a777b7a9f38cffe7ad9584b7cb42a5b37 |
| epmc_10.1016_j.micron.2021.103141.json | same, P05 | 96b1489ad1ba9ac1bb7a9343bf138aa0d5c58eb52914cdde0528d7b12a7b5cc2 |
| epmc_10.1016_j.ultramic.2005.06.057.json | same, Kruse 2006 | b4f960e6f83e8b931943b3756e0e4e5914dd3afc1ef1879ce6e6dd6881ba1613 |
| epmc_mip_pmid_37827007.json | Europe PMC `EXT_ID:37827007 AND SRC:MED` (Auslender 2024) | 9af6fed1b21939f8a2b0fd422be1be7395e38498d63bcb40a5f73a28e4e130ce |
| epmc_mip_pmid_26255119.json | Europe PMC `EXT_ID:26255119 AND SRC:MED` (Pennington 2015) | b9ed38f314609d3c0e4aec7384750b6318214d061b03eff9fe82b9f06087f2c4 |
| epmc_mip_10.1016_j.micron.2026.104079.json | Europe PMC, DOI 10.1016/j.micron.2026.104079 | 41ebc0f1763a8f4adbca0f95c37783dc51cfd5834ebcada0d38c754f359c2783 |
| P05_elsevier_api.xml | https://api.elsevier.com/content/article/PII:S0968432821001323?httpAccept=text/xml (Crossref TDM link, no API key; coredata only) | 7c8592822e1f99bf477bc290baadfacaa259481e8b31e1f90d97c452154022e6 |
| els_030439919390123F.xml | same API, PII 030439919390123F (P03) | 4854943cae4a49d1fe88b9bb0a9d405e2a32f5da39da34bcedfd5d5c677305be |
| els_S0304399109001284.xml | same API, PII S0304399109001284 (P06) | 01286ca8559bd9fbea8600ba357f44a31c439d2bda1b34e4b784e3ca3c4aa0d7 |
| els_S0304399111001586.xml | same API, PII S0304399111001586 (P31) | c0e28d2404af6cfc9c2baa5d5726e35a679d6e2f6211179f9dd6485ac0aff0f8 |
| els_micron2026.xml | https://api.elsevier.com/content/article/doi/10.1016/j.micron.2026.104079?httpAccept=text/xml | 8ea8398618caae5ef8fa65195745c634861bb198d0fcc0b3d9511f41492204ce |
| hal_p31.json | https://api.archives-ouvertes.fr/search/?q=halId_s:hal-01742047 | 1599d5dfb3ff3e3109f30c2832ed5fe5001860a47c89d70958a68308db1e3ee5 |
| hal_dfeh.json | HAL API search: dark-field holography, authors Hÿtch or Houdellier | bc10672d6c6a95e35d9c739c30042a949bc44bf7b0340a33866ff1532ed8a007 |
| hal_01742031.json | HAL API, halId hal-01742031 | 4486456e0acdbd8cf725dd9b31e130f4194a0cc2ab1bb2a48fa991d08e16d3e4 |
| osti_biblio_1819473.html | https://www.osti.gov/biblio/1819473 (1861395 redirects here) | 140869cd710197bf3fe5342d7c57ecaf67949c9d58ff71156527a1f6ec1cb14f |
| minerva_11343_290141.json | https://minerva-access.unimelb.edu.au/server/api/pid/find?id=11343/290141 | bbe47211eafa3469b01db9a26b6b81fb96fd9e829dd447ded6b1ac2202403275 |
| core_p05b.json | https://api.core.ac.uk/v3/search/works/?q=title:"Simulation software for scanning and high resolution transmission electron microscopy" | 04d21c7e6083c5d7c438e1603a25b5019ad158623f2d31081d8c47279e9fec70 |
| dtu_c02.html | https://orbit.dtu.dk/en/publications/ec85ac25-dff8-4f2a-b4cd-006c0ca865da | 15b395659b99275e469664810ccb7c860fc8a94a64062d3dddaa03317a16ad30 |

The Crossref records (`https://api.crossref.org/works/<doi>`) were read live and not archived. The
values used are quoted in sections 1, 4 and 5.

## 1. OA status table

| item | DOI | OA route checked | result | read? |
|---|---|---|---|---|
| P01 Osakabe, Matsuda, Endo, Tonomura, JJAP 27 (1988) L1772 | 10.1143/JJAP.27.L1772 (Crossref: issue 9A, first page L1772, no last page given) | OpenAlex (flags "bronze", pdf_url iopscience .../pdf); Semantic Scholar (flags BRONZE); IOP landing page and PDF URL (curl, WebFetch) | **CLOSED.** Both IOP URLs return the landing page, whose access block reads: "The computer you are using is not registered by an institution with a subscription to this article." The options offered are IOPscience login, JSAP member access, purchase (Article Galaxy, CCC RightFind) and rental. The OpenAlex and Semantic Scholar bronze flags are wrong as of 2026-09-22. | abstract only (`+ABSTRACT(publisher)`) |
| P08 Osakabe, Microsc. Res. Tech. 20 (1992) 457 | 10.1002/jemt.1070200415 | OpenAlex closed; Semantic Scholar CLOSED; Europe PMC (PMID 1498359): full text "Subscription required", not in PMC; Wiley landing page: Cloudflare 403 to curl and WebFetch | **CLOSED** (four indices agree; the host page itself is unreadable here) | abstract only (`+ABSTRACT(PubMed)`) |
| P09 Banzhof, Herrmann, Lichte, Microsc. Res. Tech. 20 (1992) 450 | 10.1002/jemt.1070200414 | OpenAlex closed; Europe PMC (PMID 1498358) "Subscription required"; Wiley: Cloudflare 403 | **CLOSED** | abstract only (`+ABSTRACT(PubMed)`) |
| P02 Osakabe et al., PRL 62 (1989) 2969 | 10.1103/PhysRevLett.62.2969 | OpenAlex closed; Europe PMC (PMID 10040140) "Subscription required", no abstract in the record; APS landing page: Cloudflare challenge to curl; WebFetch reports "Subscription required" | **CLOSED** | no (the abstract was seen only through the WebFetch summariser and is not counted) |
| P02E Erratum, PRL 63 (1989) 584 | 10.1103/PhysRevLett.63.584.3 | OpenAlex bronze; APS PDF served without login through WebFetch | **OPEN** (free to read at APS) | **yes, in full** |
| P03 Banzhof and Herrmann, Ultramicroscopy 48 (1993) 475 | 10.1016/0304-3991(93)90123-F (Crossref-confirmed, issue 4, pp. 475-481, April 1993) | OpenAlex closed; Semantic Scholar CLOSED; Elsevier API coredata `openaccess 0`, `openaccessArticle false`; ScienceDirect 403 | **CLOSED** | no |
| P31 Hÿtch, Houdellier, Hüe, Snoeck, Ultramicroscopy 111 (2011) 1328 | **10.1016/j.ultramic.2011.04.008** (new: found with Crossref `query.bibliographic`; Crossref gives vol 111, issue 8, pp. 1328-1337, July 2011) | OpenAlex closed; Semantic Scholar CLOSED; Europe PMC (PMID 21864773) "Subscription required"; Elsevier API `openaccess 0`; HAL hal-01742047 is a metadata notice (`submitType_s: notice`, `openAccess_bool: false`) whose only link is an ISTEX PDF, which is licence-restricted and not a free route | **CLOSED** | abstract only (`+ABSTRACT(PubMed)`). The open companion paper Hÿtch et al. 2010 (J. Phys.: Conf. Ser. 241, 012027) was read instead; section 2.6. |
| P05 Rangel DaCosta et al., Micron 151 (2021) 103141 | 10.1016/j.micron.2021.103141 | OpenAlex "hybrid", CC BY. Elsevier API coredata: `openaccessArticle true`, `openaccessType Full`, licence `http://creativecommons.org/licenses/by/4.0/`, sponsor "University of California (UC) 2021: Core Hybrid". ScienceDirect: 403 to curl and to WebFetch. eScholarship qt5ng2w3j4: AWS-WAF 202 with empty body to curl; the PDF exceeds WebFetch's 10 MB limit. TARA (Trinity College Dublin, accepted version): Cloudflare 403. Minerva (Melbourne): metadata only; the record points to the publisher, no bitstream. OSTI 1819473 (and 1861395, which redirects to it): citation only, `links` holds only citation URLs. CORE record 135745451: download returns "No repository ID". arXiv: no preprint. | **OPEN (publisher, CC BY 4.0) but NOT RETRIEVABLE from this environment** | no |
| P06 Maiden and Rodenburg, Ultramicroscopy 109 (2009) 1256 | 10.1016/j.ultramic.2009.05.012 | OpenAlex closed; Semantic Scholar CLOSED; Europe PMC (PMID 19541420) "Subscription required"; Elsevier API `openaccess 0`; arXiv (author Maiden, title word "ptychographical"): none; White Rose search returned no item | **CLOSED** | no (abstract read, `+ABSTRACT(PubMed)`; the ePIE update was read as stated in C03) |
| C03 Rodenburg and Maiden, Springer Handbook of Microscopy (2019) pp. 819-904 | 10.1007/978-3-030-00069-1_17 (Crossref pages 819-904) | OpenAlex lists a White Rose accepted version. White Rose record note: "This is an author-produced version of a chapter subsequently published in Hawkes P.W., Spence J.C.H. (eds) Springer Handbook of Microscopy. Uploaded in accordance with the publisher's self-archiving policy." Other record fields: `full_text_status public`, `hoa_date_foa 2021-01-01` (embargo ended) | **OPEN (author accepted manuscript)** | **yes** (sections listed in 2.5) |
| C01 Völkl and Lehmann, pp. 125-151 (not a paper item; checked in passing) | 10.1007/978-1-4615-4817-1_6 | OpenAlex closed, no repository location | CLOSED | no |
| C02 Dunin-Borkowski et al., pp. 767-818 (checked in passing) | 10.1007/978-3-030-00069-1_16 | OpenAlex closed; DTU Orbit record (submittedVersion per OpenAlex) carries only metadata and abstract, with no file link in the page | CLOSED | no |
| B10 ch. 7 Tonomura, "Electron-Holographic Interferometry", pp. 78-132 (checked in passing) | 10.1007/978-3-540-37204-2_7 | OpenAlex closed | CLOSED | no |
| Si MIP candidates | see section 4 | OpenAlex, Europe PMC, Elsevier API, arXiv | one open preprint (arXiv:2607.05948) and its CC BY version of record (Micron 207, 104079), which is not retrievable here; the rest are closed | preprint read in full |

Crossref also resolves several open metadata flags of `docs/references.bib`. These are
METADATA_VERIFIED (Crossref) and are proposals for the bibliography owner.
* P01: Crossref and the IOP `citation_firstpage` meta tag both give first page **L1772** (the L form
  is confirmed). Neither gives a last page, so "L1774" stays unverified. The issue is 9A. The IOP
  page gives "Received 12 July 1988, Accepted 17 August 1988" and an online date of 1988/09/01.
* P08 and P09: the Crossref container-title is **"Microscopy Research and Technique"**, volume 20,
  issue 4, print date 1992-02-15. P08 is pp. 457-462 and P09 is **pp. 450-456**, which settles the
  456 versus 466 conflict.
* P02: issue 25, pp. 2969-2972, online 19 June 1989.
* P02E: volume 63, issue 5, p. 584, 31 July 1989. The Crossref author list is identical to P02's,
  and the erratum page itself shows the same five names.
* P03: the DOI 10.1016/0304-3991(93)90123-F is confirmed by Crossref and by the Elsevier API
  (`prism:doi`). This removes the "weak provenance" flag.
* P05: full author list (Crossref): Luis Rangel DaCosta, Hamish G. Brown, Philipp M. Pelz,
  Alexander Rakowski, Natolya Barber, Peter O'Donovan, Patrick McBean, Lewys Jones, Jim Ciston,
  M. C. Scott, Colin Ophus.
* P31: DOI 10.1016/j.ultramic.2011.04.008 (Crossref).

## 2. Extraction per item read

Quotes are verbatim, at most two sentences each. "Statement about X" marks text in one source that
describes another paper; it is not evidence that X says it.

### 2.1 P01: publisher abstract only (the body is closed)

| fact | locator | label | note |
|---|---|---|---|
| "Reflection electron holography has been carried out successfully for the first time. Two regions in a reflection electron image of a Pt(111) surface at glancing angle incidence are overlapped by means of an electron biprism to form an off-axis electron hologram." | IOP landing page `oa/p01_iop_landing_via_pdf_url.html`, section "Abstract", sentences 1-2 | +ABSTRACT(publisher) | **Surface: Pt(111), not silicon.** Reference arrangement: the biprism overlaps two regions of the reflection electron image. |
| "The optically reconstructed interferogram displays the phase distribution of the diffracted electron wave which reflects surface topography. This method has been proved to have high sensitivity of the order of 0.01 nm for quantitatively measuring surface undulation by observing mono-atomic-height surface steps." | same, sentences 3-4 | +ABSTRACT(publisher) | Optical (not numerical) reconstruction; sensitivity of order 0.01 nm; mono-atomic steps observed. |
| Authors at the Advanced Research Laboratory, Hitachi, Ltd.; received 12 July 1988, accepted 17 August 1988 | same, "Article information" and `citation_author_institution` meta | METADATA_VERIFIED | none |
| NOT OBTAINED: electron energy, reflection order, glancing-angle value, phase-to-height relation (its sign and whether refraction is included), measured phase values, stated limitations | none | UNVERIFIED | Only the body of P01 can supply these. |

Inference (DERIVED_HERE, not a statement of P01). Both interfering waves come from the reflection
image of the specimen, so the reference is another surface region: the R2 "self-reference from a flat
region" of assumption B5, not a vacuum wave. This conflicts, at abstract level, with the vacuum
("direct") reference-wave reading attributed at second hand to the Hitachi patent in
`docs/00_executive_summary.md`. The body of P01 must settle it.

### 2.2 P08 and P09: PubMed abstracts only (the bodies are closed)

| fact | locator | label | note |
|---|---|---|---|
| P08: "Phase shift of a Bragg-reflected electron wave was measured by means of holographic interferometry using an electron microscope equipped with a field emission electron gun and an electron biprism. A short wavelength of high energy electrons is the essential key to the high vertical sensitivity of this method, since geometrical path differences produced by the surface topography are measured in units of wavelengths in interferometrical measuring." | `oa/epmc_10.1002_jemt.1070200415.json`, abstractText, sentences 2-3 | +ABSTRACT(PubMed) | This confirms the B report's near-verbatim `+ABSTRACT(index)` text. No equation or sign is stated. |
| P08: "Phase shift at a monoatomic step and the displacement field around a dislocation emerging on the surface were observed." | same, last sentence | +ABSTRACT(PubMed) | none |
| P09: "Two beam interferences produced using an electrostatic biprism, which is inserted in the position of the selected area diaphragm of a commercial electron microscope, may be used in reflection electron microscopy to determine the phase shifts induced by structures on single crystal surfaces." | `oa/epmc_10.1002_jemt.1070200414.json`, sentence 1 | +ABSTRACT(PubMed) | The biprism is image-side, at the selected-area diaphragm position. |
| P09: "A description of our interferometrical and holographical experiments on the phase shift at steps on (111)Au and (111)Pt single crystal surfaces is given and a straight forward interpretation of the results in terms of refraction will be discussed. As a particular result phase shifts of pi and 0.9 pi were measured for monatomic steps on (111)gold and (111)platinum surfaces, respectively." | same, sentences 2-3 | +ABSTRACT(PubMed) | **P09 interprets the step phase in terms of refraction.** The π and 0.9π values belong to P09 (Tübingen), not to P01. |

### 2.3 P02: nothing read (closed); the erratum is read in 2.4

### 2.4 P02E: read in full (PRL 63, 584, 31 July 1989; 2 PDF pages)

| fact | locator | label | note |
|---|---|---|---|
| "Figure 3 did not reproduce properly in print. A correct rendition is given here." | P02E, p. 584, right column, erratum text | SECTION_READ | **This is the whole correction.** No number, equation or sentence of P02 is corrected, so the references.bib warning to "re-check every number against the erratum" can be discharged. |
| Fig. 3 caption: "Reflection-electron micrograph of a GaAs(110) surface taken with (880) Bragg reflection. White arrow indicates screw dislocation." | P02E, p. 584, Fig. 3 caption (also PDF p. 2, which repeats the figure at higher quality) | SECTION_READ | P02's experiment used GaAs(110) and the (880) reflection. |
| "Black arrows show surface step generated by the dislocation. The foreshortening is a factor of 28." | same caption | SECTION_READ | 0.5 µm scale bar. |
| Erratum authors: Nobuyuki Osakabe, Junji Endo, Tsuyoshi Matsuda, Akira Tonomura, Akira Fukuhara, citing Phys. Rev. Lett. 62, 2969 (1989) | P02E, p. 584, erratum heading | SECTION_READ | This confirms the reconstructed author list in references.bib. |

The following are DERIVED_HERE, not statements of P02 or P02E.
* (880) is parallel to [110], so on GaAs(110) it is a specular reflection with g along the surface
  normal.
* Suppose the foreshortening factor equals 1/sin(theta) of the specular beam and refraction is
  neglected. Then theta = 35.7 mrad, and with a(GaAs) = 5.6533 A (ASSUMPTION: a standard value, not
  from P02), lambda = 2 d_880 sin(theta) = 0.0357 A, which corresponds to T = 107 keV. The range is
  103-110 keV if the printed 28 means 27.5 to 28.5.
* The energy is not stated in anything read. This number is a consistency estimate only and must not
  be entered as P02's energy.

### 2.5 C03: author accepted manuscript, read

Locators give the manuscript page number printed at the foot of the page ("AM p.") and the PDF page.
The AM pagination is not that of the version of record (book pp. 819-904). In the AM, the rPIE
update equation announced in section 9.1 is missing after "The object update function for this new
form of weighting is:" (AM p. 89). This is a gap in the manuscript and is not an extraction error.

| fact | locator | label | note |
|---|---|---|---|
| Forward model: exit wave psi_e = a . q, with a the 2D illumination and q a small area of the 2D object, multiplied pixel by pixel | Sec. 3.4, Eq. (2), AM p. 18 (PDF p. 19) | SECTION_READ | This is the multiplicative-object assumption. |
| PIE object update, Eq. (6): q_NEW = q + (abs(a)/abs(a)_MAX) (a*/(abs(a)^2 + epsilon)) (psi_NEW - psi_e) | Sec. 3.4, Eqs. (4)-(6), AM p. 19 (PDF p. 20); read from the rendered page | SECTION_READ | none |
| ePIE object update, Eq. (9): q_NEW = q + (a*/abs(a)^2_MAX)(psi_NEW - psi_e) = q + w Delta q, with weight w = abs(a)^2/abs(a)^2_MAX. "The ePIE algorithm makes a very basic change, replacing the normalized probe modulus with the normalized probe intensity..." | Sec. 9.1, Eqs. (8)-(9), AM p. 88 (PDF p. 89) | SECTION_READ (C03); **statement about P06** | C03 attributes ePIE to its ref. [32], which is the P06 record (AM reference list, item 32). The update as printed in P06 itself is not verified. |
| Probe update: "simply interchange the appearance of a and q in any of the object update functions above to produce a probe update function, then apply this function after the object has been updated" | Sec. 9.1, "The probe update", AM pp. 89-90 (PDF pp. 90-91) | SECTION_READ (C03); statement about P06 | none |
| Class 1 algorithms assume coherent illumination, no noise, accurately known shifts, "and the multiplicative approximation is satisfied" | Sec. 3.5, AM p. 20 (PDF p. 21) | SECTION_READ | none |
| "Last in our survey are the class 2 algorithms that relax the thin (or multiplicative) specimen assumption. Two approaches have been reported: multi-slice ptychography (see Section 6.2 and [58]) and diffraction tomographic ptychography [59]." | Sec. 3.5, AM p. 22 (PDF p. 23) | SECTION_READ | none |
| Section 5 (experimental configurations) assumes "that the exit wave is the illumination function times the transmission function" and perfect coherence | Sec. 5 introduction, AM p. 41 (PDF p. 42) | SECTION_READ | none |
| "The geometric and multiple scattering 3D effects then become intermixed so that the exit wave bears little or no relation to the projection of the object. This is particularly problematic for electrons, which for many materials of interest scatter very strongly." | Sec. 6.2, AM p. 72 (PDF p. 73) | SECTION_READ | This is the dynamical-scattering caveat. |
| Inverse multislice: each layer is updated with Eq. 6 or 9, with the probe replaced by the stored incident wave at that layer, which is then back-propagated to the previous layer | Sec. 6.2, Fig. 52 and text, AM p. 74 (PDF p. 75) | SECTION_READ | none |
| "This particular multi-slice formulation also does not account for backwardly propagating waves that have been reflected off the layers: forward-only scattering is a good approximation for the behaviour of high-energy electrons and X-rays, but not for visible light." | Sec. 6.2, AM p. 76 (PDF p. 77) | SECTION_READ | This is directly relevant to reflection mode. The chapter's multislice ptychography is forward-only. |
| "Reversing and removing multiple scattering effects in electron microscopy via ptychography could represent a major breakthrough, overcoming one of the biggest limitations of imaging with electrons, although whether this will be possible remains to be seen." | Sec. 6.2, AM p. 77 (PDF p. 78) | SECTION_READ | none |
| Glancing-angle reflection (EUV) ptychography for surface topology: "In this geometry, care must be taken to map the detector coordinates to the scattering configuration and the elongated probe shape and phase." | Sec. 5.9, AM p. 66 (PDF p. 67), Fig. 45 | SECTION_READ | This is a reflection precedent, in EUV. No electron-reflection ptychography is described. |
| Visible-light reflective ptychography: phase sensitive to topology; features taller than half the wavelength produce phase wraps; the remedy is a second wavelength giving a synthetic wavelength | Sec. 5.8, AM pp. 63-64 (PDF pp. 64-65), Figs. 42-43 | SECTION_READ | This is the optical analogue of the project's 2-pi branch problem (SM05). |
| Bragg ptychography: "The phase is proportional to displacement from the unstrained condition." | Sec. 5.7, Fig. 41 caption, AM p. 63 (PDF p. 64) | SECTION_READ | This is X-ray Bragg geometry. |

Inference (DERIVED_HERE): nothing in C03 derives a PIE or ePIE update for a Bragg-reflected electron
wave from a thick crystal. The multiplicative form (Eq. 2) and the forward-only multislice
formulation (AM p. 76) are both stated as assumptions. This supports the instruction-file caution
recorded under [C03] and [P06] in references.bib.

### 2.6 P31: PubMed abstract only; the open companion paper read instead

| fact | locator | label | note |
|---|---|---|---|
| P31: "The total phase of the transmitted and diffracted beams is described as a sum of four contributions: crystalline, electrostatic, magnetic and geometric. Each contribution is outlined briefly and leads to the proposal to measure geometric phase by dark-field electron holography (DFEH)." | `oa/epmc_10.1016_j.ultramic.2011.04.008.json`, abstractText, sentences 3-4 | +ABSTRACT(PubMed) | P31's own equations and sign convention remain UNVERIFIED. |
| Hÿtch et al. 2010 (same four authors; J. Phys.: Conf. Ser. 241, 012027; DOI 10.1088/1742-6596/241/1/012027 per HAL; HAL hal-01742031, deposited under "HAL Authorization"): Eq. (1) psi(r) = sum_g psi_g(r) exp{2 pi i g.r}, "where r is in the xy-plane, conjugate with the image plane, and the phase term due to the forward momentum is implicit" | Hÿtch 2010, Sec. 2 "Theory", Eq. (1), article p. 2 (PDF pp. 4-5) | SECTION_READ (Hÿtch 2010, not P31) | Fourier convention exp(+2 pi i g.r) |
| Eq. (2) psi_g(r) = a_g(r) exp{i phi_g(r)}. "The phases here refer uniquely to the phases of Fourier components in reciprocal space and not those of the wave function in real space." | Hÿtch 2010, Sec. 2, Eq. (2), article p. 3 (PDF p. 5) | SECTION_READ (Hÿtch 2010) | none |
| Eq. (3) phi_g(r) = phi_g^C(r) + phi_g^M(r) + phi_g^E(r) + phi_g^G(r): "crystalline, magnetic, electrostatic and geometric phase" | Hÿtch 2010, Sec. 2, Eq. (3), article p. 3 | SECTION_READ (Hÿtch 2010) | These are the same four contributions as P31's abstract. |
| "Crystalline phase is due to the (dynamical) diffraction of the fast electron by the crystalline potential, and electrostatic phase includes contributions from the mean inner potential of the material." | Hÿtch 2010, Sec. 2, text after Eq. (3) | SECTION_READ (Hÿtch 2010) | none |
| Eq. (4) phi_g^G(r) = -2 pi g.u(r), with the origin "chosen explicitly" to coincide with an axis of symmetry of the crystal; "Geometric phase therefore arises from any local displacement, u(r), of the crystal with respect to this axis" | Hÿtch 2010, Sec. 2, Eq. (4), article p. 3 (PDF p. 5); read from the rendered page | SECTION_READ (Hÿtch 2010) | **The sign is minus, with exp(+2 pi i g.r).** This is the sign of the 2010 companion paper. That P31 uses the same equation is plausible but UNVERIFIED. |
| Context: 200 kV Tecnai with Cs corrector (SACTEM-Toulouse); FIB specimens 100-200 nm thick; fringe spacing 1-2 nm | Hÿtch 2010, Sec. 1, article p. 2 | SECTION_READ (Hÿtch 2010) | Transmission geometry. |

Inference (DERIVED_HERE). The project's step phase SM03, Delta_phi = -(k_out - k_in).R in the
exp(+ik.r) convention, has the same sign structure as Hÿtch 2010 Eq. (4). For a Bragg reflection,
k_out - k_in = 2 pi g, so the project's form gives -2 pi g.R. This is a consistency check of
convention, not a validation of the reflection physics.

### 2.7 P05 and P06: not read

* P05: only the PubMed abstract (Europe PMC) was read. "In this paper, we introduce Prismatic version
  2.0, which adds many new algorithmic improvements, an updated graphical user interface (GUI),
  post-processing of simulation data, and additional operating modes such as plane-wave TEM."
  (`oa/epmc_10.1016_j.micron.2021.103141.json`; `+ABSTRACT(PubMed)`). The items the reading plan
  asks for (HRTEM output plane, anti-aliasing rule, tilt, frozen phonons) were **not obtained**. The
  D-report statements from the C++ source stay as they are.
* P06: only the PubMed abstract was read. The ePIE update is known here only as C03's statement
  (section 2.5).

## 3. CFG-O fill-in (Osakabe 1988 reproduction)

Rule: only text read in P01 or P08 themselves counts as SECTION_READ of those papers. **No body text
of P01 or P08 was read**, because both are closed. The fill-in is therefore at abstract level.

| CFG-O field | value | source and locator | label |
|---|---|---|---|
| surface | Pt(111) | P01, IOP landing page, Abstract, sentence 2 | +ABSTRACT(publisher) |
| geometry | glancing-angle incidence; reflection electron image | P01 abstract, sentence 2 | +ABSTRACT(publisher) |
| reference-wave arrangement | two regions of the reflection electron image overlapped by an electron biprism to form an off-axis hologram | P01 abstract, sentence 2 | +ABSTRACT(publisher); "self-reference, type R2" is DERIVED_HERE |
| reconstruction | optical reconstruction of the interferogram | P01 abstract, sentence 3 | +ABSTRACT(publisher) |
| quantity displayed | "the phase distribution of the diffracted electron wave which reflects surface topography" | P01 abstract, sentence 3 | +ABSTRACT(publisher) |
| sensitivity | "of the order of 0.01 nm" | P01 abstract, sentence 4 | +ABSTRACT(publisher) |
| features | mono-atomic-height surface steps | P01 abstract, sentence 4 | +ABSTRACT(publisher) |
| instrument (Osakabe's method in general) | field-emission gun and electron biprism; phase of a Bragg-reflected wave; path differences measured in units of the wavelength | P08 abstract, sentences 2-3 | +ABSTRACT(PubMed) (P08, not P01) |
| electron energy | not obtained | none | UNVERIFIED |
| reflection order | not obtained | none | UNVERIFIED |
| glancing-angle value | not obtained | none | UNVERIFIED |
| phase-step relation as written, sign, refraction included or not | not obtained. P08's abstract gives no equation. P09 (a different group, Au/Pt) interprets its step phases "in terms of refraction". | P09 abstract, sentence 2 | UNVERIFIED for P01 |
| measured phases | not obtained. π and 0.9π are P09's values (Au(111), Pt(111)), not P01's. | P09 abstract, sentence 3 | UNVERIFIED for P01 |
| limitations | not obtained | none | UNVERIFIED |

Related experiment, not CFG-O: Osakabe's GaAs(110) dislocation work (P02) used the (880) Bragg
reflection with a foreshortening factor of 28 (P02E Fig. 3 caption; SECTION_READ). Do not transfer it
to CFG-O.

Consequence for the specification (DERIVED_HERE). CFG-O is a Pt(111) benchmark, not a silicon one.
The `osakabe_1988_reproduction` configuration therefore cannot reuse Si structure, Si V0 or Si
structure factors. Its energy, reflection, angle and equation stay placeholders until the body of P01
is uploaded.

## 4. Si mean-inner-potential candidates

Metadata is from Crossref (`api.crossref.org/works/<doi>` or `query.bibliographic`). OA status is
from OpenAlex, checked against Europe PMC or the Elsevier API where available. **No value is quoted
unless it was read on the page.**

| # | citation (Crossref) | DOI | method (from title or abstract) | OA status | read? / what was read |
|---|---|---|---|---|---|
| M1 | M. Schowalter, P. Kruse, A. Rosenauer, "Modelling the mean inner potential of alloyed and strained materials", arXiv:2607.05948v1 [cond-mat.mtrl-sci], 7 Jul 2026 | none (arXiv) | DFT (WIEN2k APW+LO, GGA per their ref. [16] Perdew-Burke-Ernzerhof), slab with about 1 nm of vacuum, MIP from the innermost monolayer | **OPEN** (arXiv) | **read in full**; details below |
| M1' | M. Schowalter, P. Kruse, A. Rosenauer, "Estimating the strain and composition dependence of the mean inner potential of alloyed semiconductors", Micron 207 (2026) 104079 | 10.1016/j.micron.2026.104079 | same work (inference: its PubMed abstract is nearly word for word the arXiv abstract) | **OPEN**: Elsevier API `openaccess 1`, CC BY 4.0 (cover date 2026-11-30). Not retrievable here (ScienceDirect 403); Europe PMC lists it as "Subscription required", which is out of date | abstract only (`+ABSTRACT(PubMed)`); the version of record's Si value is UNVERIFIED |
| M2 | P. Kruse, M. Schowalter, D. Lamoen, A. Rosenauer, D. Gerthsen, "Determination of the mean inner potential in III-V semiconductors, Si and Ge by density functional theory and electron holography", Ultramicroscopy 106(2) (2006) 105-113 | 10.1016/j.ultramic.2005.06.057 | DFT slab and holography comparison | CLOSED (OpenAlex, Semantic Scholar, Europe PMC "Subscription required") | abstract only: "The computed values are in agreement with experimental values obtained by electron holography for Si and GaAs." (+ABSTRACT(PubMed); no number in the abstract) |
| M3 | M. Gajdardziska-Josifovska, M. R. McCartney, W. J. de Ruijter, D. J. Smith, J. K. Weiss, J. M. Zuo, "Accurate measurements of mean inner potential of crystal wedges using digital electron holograms", Ultramicroscopy 50 (1993) 285-299 | 10.1016/0304-3991(93)90197-6 | holography of wedges (measured) | CLOSED | no; whether Si is among the crystals is UNVERIFIED |
| M4 | M. Y. Kim, J. M. Zuo, J. C. H. Spence, "Ab-initio LDA Calculations of the Mean Coulomb Potential V0 in Slabs of Crystalline Si, Ge and MgO", phys. stat. sol. (a) 166 (1998) 445-451 | 10.1002/(SICI)1521-396X(199803)166:1<445::AID-PSSA445>3.0.CO;2-N (Crossref also lists a second DOI ending 3.3.CO;2-E) | DFT (LDA) slabs, Si explicitly | CLOSED | no. Statement about M4 in M1 (p. 1): Kim et al. found that for Si "the type of surface or surface relaxation changed the MIP by about 0.2 V, whereas the redistribution of charge resulted in a change by 1.7 V" |
| M5 | Y. C. Wang, T. M. Chou, M. Libera, T. F. Kelly, "Transmission electron holography of silicon nanospheres with surface oxide layers", Appl. Phys. Lett. 70 (1997) 1296-1298 | 10.1063/1.118556 | holography of Si spheres with oxide (measured) | CLOSED | no |
| M6 | A. Auslender, N. Pandey, A. Kohn, O. Diéguez, "Mean inner potential of elemental crystals from density-functional theory calculations: Efficient computation and trends", Ultramicroscopy 255 (2024) 113862 | 10.1016/j.ultramic.2023.113862 | DFT (PAW), 44 elemental solids | CLOSED | abstract only: V0 computed for 44 elemental solids; "We also report instances in which different surface terminations for the same material led to differences in V0 of more than 3 V, highlighting the dependence of the mean inner potential on the boundary conditions of the sample." (+ABSTRACT(PubMed); it is not said whether Si is one of those instances) |
| M7 | R. S. Pennington, C. B. Boothroyd, R. E. Dunin-Borkowski, "Surface effects on mean inner potentials studied using density functional theory", Ultramicroscopy 159 (2015) 34-45 | 10.1016/j.ultramic.2015.07.011 | DFT, surface and adsorbate dependence | CLOSED | abstract only: "We find that the mean inner potential is surface-dependent, with the strongest dependency on surface adsorbates." (+ABSTRACT(PubMed)) |
| M8 | M. O'Keeffe, J. C. H. Spence, "On the average Coulomb potential (Sigma0) and constraints on the electron density in crystals", Acta Cryst. A50 (1994) 33-45 | 10.1107/S010876739300474X | theory | CLOSED | no |
| M9 | D. Rez, P. Rez, I. Grant, "Dirac-Fock calculations of X-ray scattering factors and contributions to the mean inner potential for electron scattering", Acta Cryst. A50 (1994) 481-497; erratum A53 (1997) 522 | 10.1107/S0108767393013200 | isolated-atom Dirac-Fock (the independent-atom approximation) | CLOSED | no |
| M10 | D. K. Saldin, J. C. H. Spence, "On the mean inner potential in high- and low-energy electron diffraction", Ultramicroscopy 55 (1994) 397-406 | 10.1016/0304-3991(94)90175-9 | theory; the definition and its relevance to energy and surface dependence | CLOSED | no (M1 cites it for the surface dependence of the MIP) |
| M11 | A. Kawasuso, S. Okada, "Reflection High Energy Positron Diffraction from a Si(111) Surface", PRL 81 (1998) 2695-2698 | 10.1103/PhysRevLett.81.2695 | RHEPD on Si(111) | CLOSED | no; whether it states a Si crystal potential is UNVERIFIED |
| M12 | T. Hanada, S. Ino, H. Daimon, "Study of the Si(111)7x7 surface by RHEED rocking curve analysis", Surf. Sci. 313 (1994) 143-154 | 10.1016/0039-6028(94)91162-2 | RHEED rocking curves (inner potential possibly fitted; UNVERIFIED) | CLOSED | no |
| M13 | M. Schowalter, A. Rosenauer, D. Lamoen, P. Kruse, D. Gerthsen, "Ab initio computation of the mean inner Coulomb potential for technologically important semiconductors", Springer Proc. Phys. (2005) 233-236 | 10.1007/3-540-31915-8_47 | DFT | CLOSED | no |
| M14 | N. Tanaka, "Theoretical Basis of Electron Holography for Thick Crystals and Mean Inner Potential", in Electron Nano-imaging (Springer, 2024) 339-341 | 10.1007/978-4-431-56940-4_33 | textbook chapter | CLOSED | no |
| M15 | Ichimiya and Cohen [B07], ch. 11 "Fourier components of the crystal potential", pp. 154-160 | 10.1017/cbo9780511735097.012 | RHEED textbook definition of V0 | CLOSED | no |

**M1 extraction (arXiv:2607.05948v1, read in full)**

| fact | locator | label | note |
|---|---|---|---|
| Definition: V0 = (1/Omega) integral over Omega of V_c(r) d^3r. "The zero point of the Coulomb potential V_c is chosen such that it is zero at infinite distance from the crystal." The MIP therefore "depends on the crystal structure and the surface of the crystal [1]". | p. 1, Eq. (1) and the text after it | SECTION_READ | [1] is Saldin and Spence 1994 (M10). The MIP is defined as an electrostatic average, with no electron-energy dependence. |
| Si endpoint of the GexSi1-x series. The Fig. 2c panel prints the fit "V=12.533636 + 2.695412 x +-0.606985 x^2", where x is the Ge concentration, the points are Boltzmann-averaged DFT MIPs and the line is a second-order polynomial fit. | p. 3, Fig. 2c and its caption | SECTION_READ | **Si (x = 0): 12.53 V as a fit intercept.** This is not a tabulated value, and no uncertainty is given. |
| GexSi1-x biaxially stressed to Si: the Fig. 3 panel prints "V=12.541646 + 3.385597 x +-0.353855 x^2" | p. 3, Fig. 3 | SECTION_READ | At x = 0 this is again unstrained Si: 12.54 V (fit intercept). |
| Method: WIEN2k APW+LO, GGA, tetrahedron integration (smearing of 0.005 Ry for GeSi). Slabs have [1-10], [110] and [001] along x, y and z, with about 1 nm of vacuum "symmetrically added in y-direction". 2x1x2 supercells (88 atoms, 8 atoms per monolayer). The MIP is computed "from the innermost monolayer". | p. 2, methods paragraphs | SECTION_READ | Vacuum along [110] means the slab faces are (110) (DERIVED_HERE). The value is for a bulk-terminated (110) slab, not for oxidised Si(001). |
| Si lattice parameter used: 0.54311 nm; C11, C12, C44 = 163.8, 59.2, 81.7 GPa | p. 4, Table I | SECTION_READ | none |
| "Typical precisions for the measurement of MIPs with current techniques (electron holography) are in the range of about 0.1-0.4 V [8-11]" | p. 1 | SECTION_READ; statement about M3 and others | This is not an uncertainty on the Si value. |
| Energy dependence | none stated | none | The MIP as defined is energy-independent. Energy enters the refraction only through the relativistic factor already in SM04 (DERIVED_HERE). |

The Zenodo data (10.5281/zenodo.18449230, CC BY 4.0) contain the pure-Si output
`GeSi_11_2/Ge0p0Si/Ge0p0SiSi_1/V96.out`. Its per-atom lines lie between 12.40 V and 12.53 V. Its last
line reads "Pixel Mean of Atoms 44 + 88 == 12.405 +  12.405 =12.405". According to the workflow
Readme (`go_lapw5/Readme.txt`, step 7), 2x1x2 supercell values are instead obtained by
`EvalTernMIP_conf.m`, which averages the atoms of the innermost monolayer; the end-of-file line is
the 1x1x1 summary. This agent did not re-run that averaging. **The only Si number stated by the
authors in what was read is the Fig. 2c intercept of 12.53 V.** Reproducing it from V96.out is
proposed as a REPRODUCED check in section 6.

Statement of the problem for B1 (DERIVED_HERE). Refraction at the specimen surface depends on the
potential step between vacuum and crystal, which includes the surface dipole. M1 (via M4), M6 and M7
all report surface dependence, with M7 finding the strongest dependence on adsorbates. A bulk-slab DFT
value is therefore a lower-level proxy for an ion-milled, oxide-covered Si(001) surface. The
experimentally relevant V0 remains PROJECT_INPUT or ASSUMPTION until either an experimental Si value
(M2, M3, M5) is read or the rocking-curve fit of the real sample calibrates it.

## 5. Revised upload list for Ali (plan order; read items removed)

The following are removed from the list:
* **P02E**: read in full; free at APS.
* **C03**: the accepted manuscript is read. The version of record is needed only if AM-page locators
  must be converted to book pages 819-904.

**P05 is open access (CC BY 4.0)**. Ali need not buy it: a free browser download from
https://doi.org/10.1016/j.micron.2021.103141 (or eScholarship item qt5ng2w3j4), placed in the upload
area, is enough.

Chapter titles and pages below are METADATA_VERIFIED (Crossref). For B07 and B08 the chapter
numbers are inferred from the DOI-suffix order. For B07 the inference is consistent with the
references.bib record that "Dynamical theory: integral method" is ch. 14.

1. **P01**: N. Osakabe, T. Matsuda, J. Endo, A. Tonomura, "Observation of Atomic Steps by Reflection
   Electron Holography", Jpn. J. Appl. Phys. 27 (9A) (1988) L1772, doi:10.1143/JJAP.27.L1772.
   Closed: the IOP page says the computer is not registered by an institution with a subscription.
   JSAP members have access.
2. **P08**: N. Osakabe, "Observation of surfaces by reflection electron holography", Microsc. Res.
   Tech. 20(4) (1992) 457-462, doi:10.1002/jemt.1070200415. Closed: Europe PMC says "Subscription
   required" and OpenAlex says closed; the Wiley page could not be reached here.
3. **P02**: N. Osakabe, J. Endo, T. Matsuda, A. Tonomura, A. Fukuhara, "Observation of surface
   undulation due to single-atomic shear of a dislocation by reflection-electron holography", Phys.
   Rev. Lett. 62(25) (1989) 2969-2972, doi:10.1103/PhysRevLett.62.2969. Closed: the APS page shows
   "Subscription required". The erratum P02E is not needed.
4. **P03**: H. Banzhof, K.-H. Herrmann, "Reflection electron holography", Ultramicroscopy 48(4)
   (1993) 475-481, doi:10.1016/0304-3991(93)90123-F. Closed: Elsevier API `openaccess 0`.
5. **B07** Ichimiya and Cohen, Reflection High-Energy Electron Diffraction (CUP 2004):
   * ch. 5 "The diffraction conditions", pp. 28-42 (doi:10.1017/cbo9780511735097.006)
   * ch. 7 "Kikuchi and resonance patterns", pp. 62-76 (.008)
   * ch. 12 "Dynamical theory - transfer matrix method", pp. 161-172 (.013)
   * ch. 13 "Dynamical theory - embedded R-matrix method", pp. 173-191 (.014)
   * ch. 14 "Dynamical theory - integral method", pp. 192-194 (.015)
   * optional, new: ch. 11 "Fourier components of the crystal potential", pp. 154-160 (.012), for the
     RHEED definition of V0
6. **B08** Peng, Dudarev and Whelan, High-Energy Electron Diffraction and Microscopy (OUP):
   * ch. 5 "Dynamical Theory III. Reflection High-Energy Electron Diffraction", pp. 117-185
     (doi:10.1093/oso/9780198500742.003.0005)
   * ch. 13 "The Atomic Scattering Factor and the Optical Potential", pp. 427-453 (.003.0013)
   * optional: ch. 6 "Resonance Effects in Transmission and Reflection High-Energy Electron
     Diffraction", pp. 186-227 (.003.0006)
   * Crossref "issued" is 2004-01-08, which is the Oxford Academic record date. This does not by
     itself settle the 2003/2004 print-year conflict.
7. **B06** Kirkland, Advanced Computing in Electron Microscopy, 3rd ed. (Springer 2020):
   * ch. 4 "Sampling and the Fast Fourier Transform", pp. 81-98 (doi:10.1007/978-3-030-33260-0_4)
   * ch. 6 "Theory of Calculation of Images of Thick Specimens", pp. 143-195 (_6)
   * ch. 7 "Multislice Applications and Examples", pp. 197-239 (_7)
8. **C01**: E. Völkl, M. Lehmann, "The Reconstruction of Off-Axis Electron Holograms", in Völkl,
   Allard, Joy (eds.), Introduction to Electron Holography (1999) pp. 125-151,
   doi:10.1007/978-1-4615-4817-1_6. Closed (OpenAlex).
9. **C02**: R. E. Dunin-Borkowski, A. Kovács, T. Kasama, M. R. McCartney, D. J. Smith, "Electron
   Holography", in Springer Handbook of Microscopy (2019) pp. 767-818,
   doi:10.1007/978-3-030-00069-1_16. Closed: OpenAlex; the DTU Orbit record has no file.
10. **P31**: M. J. Hÿtch, F. Houdellier, F. Hüe, E. Snoeck, "Dark-field electron holography for the
    measurement of geometric phase", Ultramicroscopy 111(8) (2011) 1328-1337,
    doi:10.1016/j.ultramic.2011.04.008. Closed: Elsevier API `openaccess 0`; HAL holds a notice only.
    The 2010 companion paper was read (section 2.6), but P31 itself is still needed for its own
    equation and sign.
11. **Si mean inner potential, measured**: first choice M2, Kruse et al., Ultramicroscopy 106 (2006)
    105-113, doi:10.1016/j.ultramic.2005.06.057. It covers Si by DFT and compares with holography.
    Alternatively, M5 Wang et al., APL 70 (1997) 1296 gives a direct Si measurement. A DFT value
    (M1) is now read, so the upload is needed for a measured value and its uncertainty.
12. **P05**: download free (CC BY). No purchase is needed.
13. **P06**: A. M. Maiden, J. M. Rodenburg, "An improved ptychographical phase retrieval algorithm for
    diffractive imaging", Ultramicroscopy 109(10) (2009) 1256-1262, doi:10.1016/j.ultramic.2009.05.012.
    Closed: Elsevier API `openaccess 0`.
14. **B10 ch. 7**: A. Tonomura, "Electron-Holographic Interferometry", in Electron Holography, 2nd ed.
    (Springer 1999) pp. 78-132, doi:10.1007/978-3-540-37204-2_7. Closed (OpenAlex).

## 6. Proposed updates (proposals only; nothing below has been applied)

### 6.1 `docs/model_assumptions.md`

* **B1.** Keep `V0 = 12.0 V` labelled ASSUMPTION and add the following to its Status column:
  * One DFT value is now SECTION_READ: 12.53 V, the Fig. 2c fit intercept of
    Schowalter-Kruse-Rosenauer arXiv:2607.05948v1 (WIEN2k GGA, bulk-terminated (110) slab, innermost
    monolayer). No uncertainty is stated, and it is not an experimental value.
  * At B1's own sensitivities, moving from 12.0 V to 12.53 V changes |Delta_phi| at (4,-4,4) by
    about -0.18 rad. If 12.53 V were the right value, heights inferred with 12.0 V would be biased
    by about +0.03 A (DERIVED_HERE: 0.53 V x (-0.34 rad/V) and 0.53 V x 0.05 A/V).
  * The MIP is surface-dependent (M7 and M6 abstracts; M4 as reported by M1). An oxide-covered,
    ion-milled Si(001) surface may differ from any slab value, so a measured value (M2, M3, M5 after
    upload) or the rocking-curve calibration on the real sample is required.
  * Kruse et al. 2006 stays METADATA_VERIFIED with no value taken.
* **B5.** Add that P01's abstract (+ABSTRACT(publisher)) describes a biprism overlapping two regions
  of the reflection image of Pt(111), i.e. a self-reference arrangement (R2), and that this conflicts
  with the second-hand vacuum-reference reading of the patent. It is to be settled by P01's body.
* **Section 3, limitations.** Replace "All scholarly hosts ... were blocked" with the present status:
  * Network access is Full.
  * P02E, the C03 AM, the Hÿtch 2010 companion and the MIP preprint are read.
  * P01, P08, P09, P02, P03, P06 and P31 are closed and known only at abstract level.
  * P05 is open but was not retrievable here.
  * APS pages are reachable only through WebFetch; Wiley and ScienceDirect were unreachable.
* **Open question 1.** Record the partial answer at abstract level: Pt(111), glancing incidence,
  biprism overlap of two image regions, optical reconstruction, sensitivity of order 0.01 nm. The
  energy, reflection, angle, equation and measured values remain open.
* **New limitation (ptychography milestone).** C03 states the multiplicative exit-wave model (Eq. 2)
  and a forward-only multislice inversion that "does not account for backwardly propagating waves
  that have been reflected off the layers" (AM p. 76). No reflection-electron update is derived
  there.

### 6.2 `docs/source_map.tsv`

* **SM03.** Add a convention cross-check: Hÿtch et al. 2010, J. Phys.: Conf. Ser. 241, 012027,
  Sec. 2, Eqs. (1) and (4): phi_g^G = -2 pi g.u with psi = sum_g psi_g exp(+2 pi i g.r).
  SECTION_READ of the 2010 paper; P31's own sign is still UNVERIFIED. P08 moves from `+ABSTRACT(index)`
  to `+ABSTRACT(PubMed)`, with the abstract sentence 3 locator.
* **SM04.** Add under V0: "one DFT value read, arXiv:2607.05948v1 Fig. 2c, 12.53 V (fit intercept);
  surface-dependent; measured value pending (PROJECT_INPUT item 20)".
* **SM17.** V0 source: M1 is available for the MIP-of-parameterisation comparison as a DFT reference.
  Add a planned test that reproduces the Si endpoint from the Zenodo V96.out with the authors'
  EvalTernMIP_conf.m averaging (target label REPRODUCED).
* **New row SM18 (ptychography).** Claim: "ePIE object update q_NEW = q + a*/abs(a)^2_MAX (psi_NEW -
  psi_e) assumes psi_e = a.q". Source: C03 AM Sec. 3.4 Eq. (2) and Sec. 9.1 Eq. (9); SECTION_READ of
  C03 (AM), statement about P06; validity is a thin multiplicative object; test not yet written.
* **New row SM19 (P02 context).** "P02 used GaAs(110) with the (880) specular Bragg reflection, with
  foreshortening 28", from P02E p. 584 Fig. 3 caption; SECTION_READ; not a Si parameter.

### 6.3 `docs/references.bib` (for the bibliography owner)

* **P01.** Record the publisher abstract as read (+ABSTRACT(publisher), IOP landing page), with
  surface Pt(111). The first page L1772 is confirmed by Crossref and IOP; the last page is still
  unverified.
* **P02E.** Content is now SECTION_READ. The erratum only replaces the badly printed Fig. 3 (GaAs(110),
  (880) reflection, foreshortening 28), and the author list is confirmed on the page. Remove the
  "re-check every number" warning.
* **P03.** The DOI is confirmed (Crossref and Elsevier API).
* **P05.** Add the full author list and note "open access, CC BY 4.0 (Elsevier API coredata)".
* **P08 and P09.** Journal "Microscopy Research and Technique" is confirmed by Crossref; P09's pages
  are 450-456. Upgrade the abstract labels to +ABSTRACT(PubMed).
* **P31.** Add `doi = {10.1016/j.ultramic.2011.04.008}` (Crossref).
* **C03.** Add the note "author accepted manuscript at White Rose eprint 127795, read (SECTION_READ,
  AM pagination)".
* **New entries (METADATA_VERIFIED via Crossref or arXiv):**
  * Hÿtch et al. 2010 (J. Phys.: Conf. Ser. 241, 012027; HAL hal-01742031; SECTION_READ);
  * Schowalter, Kruse, Rosenauer arXiv:2607.05948 (SECTION_READ) and Micron 207 (2026) 104079;
  * candidates M3 to M15 (METADATA_VERIFIED only).
