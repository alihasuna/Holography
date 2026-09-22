# L5 - Open-access check of the paper items before any upload request to Ali

Status: in progress, 2026-09-22. Agent L5 (literature, open-access route). Network access: Full
(HTTPS through the preconfigured agent proxy). No file in the repository other than this report was
edited; nothing was committed or pushed.

Raw downloads are kept outside the repository, in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/oa/`
(called `oa/` below). Every file that was read is listed in section 0 with its URL, retrieval date
(2026-09-22) and SHA-256.

Label policy (project instruction file, section 1.4): METADATA_VERIFIED, SECTION_READ (only with a
locator), REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED; `+ABSTRACT(publisher)` is
used here for an abstract read by this agent on the publisher's own landing page (stronger than the
earlier `+ABSTRACT(index)`, weaker than SECTION_READ of the body). An OpenAlex OA flag is metadata,
not evidence of access: every "open" verdict below was checked on the host itself.

Method per item: (1) `https://api.openalex.org/works/doi:<doi>` (open_access, best_oa_location,
locations); (2) `https://api.crossref.org/works/<doi>` for metadata; (3) the publisher landing page
fetched directly with curl (access block read in the raw HTML); (4) every repository location listed
by OpenAlex (PMC, OSTI, eScholarship, HAL, institutional repositories) fetched directly. No shadow
library was used or searched.

## 0. Files retrieved (URL, date, SHA-256)

| file in oa/ | URL fetched | date | SHA-256 | what it is |
|---|---|---|---|---|
| p01_iop_landing_via_pdf_url.html | https://iopscience.iop.org/article/10.1143/JJAP.27.L1772/pdf (served the article landing page, not a PDF) | 2026-09-22 | 7c41d0c13925711318da1d06ce59c75744973e24407bae79b812144b5815c311 | IOP landing page of P01 with abstract and access block |
| P02E_PhysRevLett.63.584.3.pdf | https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.63.584.3 (retrieved through the WebFetch tool; curl receives a Cloudflare challenge) | 2026-09-22 | 2c1cced352ff0b08acbc5b29e5c67c4be22b9ac64539ccedb1a8adad78c46d70 | APS erratum page, 2 pages (scanned; read as rendered images) |
| epmc_10.1002_jemt.1070200415.json | Europe PMC REST search `DOI:10.1002/jemt.1070200415` (resultType=core) | 2026-09-22 | af90811f5e7bf689780822415fbe4db01f64bf651e63576b18996c874c3f6371 | PubMed record of P08 with abstract; full text "Subscription required" |
| epmc_10.1002_jemt.1070200414.json | Europe PMC REST, `DOI:10.1002/jemt.1070200414` | 2026-09-22 | 7f4231aa05a7d82d2f592dc38e80a38764aeb98375f65be994c702ab3d0d227a | PubMed record of P09 with abstract |
| epmc_10.1103_PhysRevLett.62.2969.json | Europe PMC REST, `DOI:10.1103/PhysRevLett.62.2969` | 2026-09-22 | a9f48c144b9d9563067c4a923a84f8bd3b8e658b08a96a299fd67549a77c2c26 | PubMed record of P02 (no abstract in the record) |
| epmc_10.1016_j.ultramic.2011.04.008.json | Europe PMC REST, `DOI:10.1016/j.ultramic.2011.04.008` | 2026-09-22 | c1160a05ed612809c521cc045591fca6b0c597e48a7d78f9eb6a1d6da279240e | PubMed record of P31 with abstract |
| epmc_10.1016_j.ultramic.2009.05.012.json | Europe PMC REST, `DOI:10.1016/j.ultramic.2009.05.012` | 2026-09-22 | 4d945ec82758cf367bb0a6d2461f124a777b7a9f38cffe7ad9584b7cb42a5b37 | PubMed record of P06 with abstract |
| epmc_10.1016_j.micron.2021.103141.json | Europe PMC REST, `DOI:10.1016/j.micron.2021.103141` | 2026-09-22 | 96b1489ad1ba9ac1bb7a9343bf138aa0d5c58eb52914cdde0528d7b12a7b5cc2 | PubMed record of P05 with abstract |
| epmc_10.1016_j.ultramic.2005.06.057.json | Europe PMC REST, `DOI:10.1016/j.ultramic.2005.06.057` | 2026-09-22 | b4f960e6f83e8b931943b3756e0e4e5914dd3afc1ef1879ce6e6dd6881ba1613 | PubMed record of Kruse et al. 2006 with abstract |
| P05_elsevier_api.xml | https://api.elsevier.com/content/article/PII:S0968432821001323?httpAccept=text/xml (Crossref TDM link; no API key) | 2026-09-22 | (see section 0b) | Elsevier coredata only: open-access flags and licence, no body |
| hal_p31.json | https://api.archives-ouvertes.fr/search/?q=halId_s:hal-01742047 (fields listed in the query) | 2026-09-22 | (see section 0b) | HAL record of P31: submitType "notice", openAccess false |
| whiterose_127795.html | https://eprints.whiterose.ac.uk/127795/ | 2026-09-22 | bcc30249f1ed74b1271c592985270f9c23d85383088ec91af4f3ebf7034fb33f | White Rose record of C03 (author-produced version, full_text_status public) |
| C03_whiterose_127795_AM.pdf | https://eprints.whiterose.ac.uk/id/eprint/127795/1/Ptychography_Chapter-Rodenburg%2BMaiden_final.pdf | 2026-09-22 | 861bcaa9785991a4e96197e7a7761077705c7d09b586e732a10f9a95983f06b5 | C03 author accepted manuscript, 138 PDF pages |
| openalex_*.json (11 files) | https://api.openalex.org/works/doi:<doi> for each DOI in section 1 | 2026-09-22 | listed in section 0b | OA metadata |

## 1. OA status table

(filled below as items are checked)

