# B3 -- Crossref / publisher verification log for `docs/references.bib`

Prepared: 2026-09-22. Network access: Full (HTTPS proxy). This log replaces nothing: the
index-only record `B2_bib_verification_log.md` is kept unedited.

Status: IN PROGRESS (written incrementally; the generated block below is rewritten by
`tools/bib/crossref_check.py report`).

Baseline: `docs/references.bib` at commit `4a9df525a7d33ad974293e0cac04f31e479fc816`
(96 entries, 45 with a `doi` field, 18 in the UNVERIFIED section).

<!-- BEGIN GENERATED -->
## Counts (produced by `tools/bib/crossref_check.py report`)

| Quantity | Count |
|---|---|
| entries checked (baseline file) | 96 |
| baseline entries with a doi field | 45 |
| ... of which Crossref /works returned HTTP 200 | 44 |
| Crossref bibliographic searches run (entries without doi) | 43 |
| ... candidate accepted on the five-field rule | 24 |
| ... candidate accepted with identifier substitution | 7 |
| VERIFIED, record unchanged | 43 |
| VERIFIED, record corrected (fields and/or doi added) | 0 |
| newly found DOIs (copied from Crossref, never constructed) | 0 |
| entries moved out of the UNVERIFIED section | 0 |
| still unverified (no accepted record, or residual discrepancy) | 53 |
| HTTP failures (network error, 429 or 5xx after retries) | 0 |

Syntax validation of the current `references.bib`: {"entries": 96, "unique_keys": 96, "verified_section": 78, "unverified_section": 18, "with_doi": 45}; errors: none; entries whose doi is not backed by a cached registry record: none.

## Corrections (baseline -> current, every changed field except `note`)

| key | field | before | after |
|---|---|---|---|

## Per-entry record

Discrepancy kinds: `family`/`diacritics`/`given`/`count`/`incomplete` (names), `ratio=` (title similarity after case/punctuation folding), `container`, `volume`, `issue`, `pages`, `year`, `publisher`, `missing` (field absent in bib but present in record). Search verdicts: A first author, T title, C container or publisher, Y year, V volume, P first page, I PII/ISBN.

### B01 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1093/acprof:oso/9780199668632.001.0001
- Query URL: <https://api.crossref.org/works/10.1093/acprof:oso/9780199668632.001.0001>  (HTTP: 200)
- Crossref dates: {'published-print': '2013-9-12', 'issued': '2013-9-12', 'published': '2013-9-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B02 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1017/cbo9780511615092
- Query URL: <https://api.crossref.org/works/10.1017/CBO9780511615092>  (HTTP: 200)
- Crossref dates: {'published-print': '2003-3-27', 'published-online': '2009-12-2', 'issued': '2003-3-27', 'published': '2003-3-27'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B03 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Hawkes+Kasper+Principles+of+Electron+Optics%2C+Volume+3%3A+Fundamental+Wave+Optics+Academic+Press+2022&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/b978-0-12-818979-5.00058-9` score 72.6 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00056-5` score 67.6 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.326, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Relativistic Wave Equation"
  - `10.1016/b978-0-323-91646-2.00079-7` score 66.1 **REJECT(T,C,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.213, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'mismatch'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Wigner Optics"
  - `10.1016/b978-0-12-333354-4.50008-2` score 63.7 **REJECT(T,C,Y,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a', 'I': 'mismatch'} -- HAWKES; 1994; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-012333340-7/50237-4` score 63.7 **REJECT(T,C,Y,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a', 'I': 'mismatch'} -- Hawkes; 1996; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00102-9` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.09, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Index"
  - `10.1016/b978-0-12-818979-5.00084-x` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.176, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Preface to the Second Edition"
  - `10.1016/b978-0-12-818979-5.00060-7` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.28, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Elementary Diffraction Patterns"
  - `10.1016/b978-0-12-818979-5.00083-8` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.229, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Contents"
  - `10.1016/b978-0-12-818979-5.00061-9` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.244, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "General Introduction"
  - `10.1016/c2018-0-04650-2` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.76, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Elsevier; vol ; "Principles of Electron Optics, Volume 3"
  - `10.1016/b978-0-12-818979-5.00066-8` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.323, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Image Formation in the Conventional Transmission Electron Microscope"
  - `10.1016/b978-0-12-818979-5.00085-1` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.2, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Preface to the First Edition"
  - `10.1016/b978-0-12-818979-5.00068-1` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.178, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Statistical Parameter Estimation Theory"
  - `10.1016/b978-0-12-818979-5.00101-7` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.244, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Notes and References"
  - `10.1016/b978-0-12-818979-5.00059-0` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.397, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The General Theory of Electron Diffraction and Interference"
  - `10.1016/b978-0-12-818979-5.00086-3` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.139, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Dedication"
  - `10.1016/b978-0-12-818979-5.00064-4` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.244, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "General Introduction"
  - `10.1016/b978-0-12-818979-5.00055-3` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.209, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Schrödinger Equation"
  - `10.1016/b978-0-12-818979-5.00081-4` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.139, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Title page"
  - `10.1016/b978-0-12-818979-5.00067-x` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.317, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Image Formation in the Scanning Transmission Electron Microscope"
  - `10.1016/b978-0-12-818979-5.00082-6` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.113, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 3; vol ; "Copyright"
  - `10.1016/b978-0-12-818979-5.00065-6` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.323, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Fundamentals of Transfer Theory"
  - `10.1016/b978-0-12-818979-5.00058-9` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00056-5` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.326, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Relativistic Wave Equation"
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B04 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Hawkes+Kasper+Principles+of+Electron+Optics%2C+Volume+4%3A+Advanced+Wave+Optics+Academic+Press+2022&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/b978-0-12-818979-5.00058-9` score 72.6 **REJECT(T,C,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.405, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'mismatch'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-12-818979-5.00056-5` score 67.6 **REJECT(T,C,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.337, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'mismatch'} -- Hawkes; 2022; Principles of Electron Optics, Volume 3; vol ; "The Relativistic Wave Equation"
  - `10.1016/b978-0-323-91646-2.00079-7` score 66.1 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.222, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Wigner Optics"
  - `10.1016/b978-0-12-333354-4.50008-2` score 63.8 **REJECT(T,C,Y,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.405, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a', 'I': 'mismatch'} -- HAWKES; 1994; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-012333340-7/50237-4` score 63.7 **REJECT(T,C,Y,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.405, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a', 'I': 'mismatch'} -- Hawkes; 1996; Principles of Electron Optics; vol ; "Paraxial Wave Optics"
  - `10.1016/b978-0-323-91646-2.00089-x` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.145, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Dedication"
  - `10.1016/b978-0-323-91646-2.00072-4` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.2, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Enhancement"
  - `10.1016/b978-0-323-91646-2.00086-4` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.278, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Notes and References"
  - `10.1016/b978-0-323-91646-2.00075-x` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.264, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Three-Dimensional Reconstruction"
  - `10.1016/b978-0-323-91646-2.00082-7` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.118, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Copyright"
  - `10.1016/b978-0-323-91646-2.00021-9` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.438, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Corrections and additions to volumes 1, 2 and 3"
  - `10.1016/b978-0-323-91646-2.00070-0` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.254, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Introduction"
  - `10.1016/c2021-0-01238-4` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.784, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Elsevier; vol ; "Principles of Electron Optics, Volume 4"
  - `10.1016/b978-0-323-91646-2.00078-5` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.247, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Coherence and the Brightness Functions"
  - `10.1016/b978-0-323-91646-2.00085-2` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.207, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Preface to the First Edition"
  - `10.1016/b978-0-323-91646-2.00079-7` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.222, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Wigner Optics"
  - `10.1016/b978-0-323-91646-2.00083-9` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.149, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Contents"
  - `10.1016/b978-0-323-91646-2.00088-8` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.094, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Index"
  - `10.1016/b978-0-323-91646-2.00084-0` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.182, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Preface to the Second Edition"
  - `10.1016/b978-0-323-91646-2.00077-3` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.175, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Microscope Parameter Measurement and Instrument Control"
  - `10.1016/b978-0-323-91646-2.00071-2` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.333, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Acquisition, Sampling and Coding"
  - `10.1016/b978-0-323-91646-2.00080-3` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.303, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Orbital Angular Momentum, Vortex Beams and the Quantum Electron Microscope"
  - `10.1016/b978-0-323-91646-2.00074-8` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.327, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Nonlinear Restoration – The Phase Problem"
  - `10.1016/b978-0-323-91646-2.00081-5` score 0.0 **REJECT(A,T,C)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.145, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Principles of Electron Optics, Volume 4; vol ; "Title page"
  - `10.1016/b978-0-323-91646-2.00073-6` score 0.0 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.208, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Hawkes; 2022; Principles of Electron Optics, Volume 4; vol ; "Linear Restoration"
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B05 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1007/978-3-642-32119-1
- Query URL: <https://api.crossref.org/works/10.1007/978-3-642-32119-1>  (HTTP: 200)
- Crossref dates: {'published-print': '2012', 'issued': '2012', 'published': '2012'}; bib year matches: []
- publisher_form: bib 'Springer' vs Crossref 'Springer Berlin Heidelberg'
- type: book
- Discrepancies (baseline vs record): `year` '2013' vs 'published-print 2012; issued 2012; published 2012' (year)
- Remaining differences (current vs record): `year` '2013' vs 'published-print 2012; issued 2012; published 2012'
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B06 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-33260-0
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-33260-0>  (HTTP: 200)
- Crossref dates: {'published-print': '2020', 'issued': '2020', 'published': '2020'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index, single) (B report)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index, single) (B report)`

### B07 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1017/cbo9780511735097
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ichimiya+Cohen+Reflection+High-Energy+Electron+Diffraction+Cambridge+University+Press+2004&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2004-12-13', 'published-online': '2010-7-6', 'issued': '2004-12-13', 'published': '2004-12-13'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1017/cbo9780511735097` score 65.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Ichimiya; 2004/2010; Cambridge University Press; vol ; "Reflection High-Energy Electron Diffraction"
  - `10.1002/adma.200590112` score 47.7 **REJECT(A,T,C,Y)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.628, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Osten; 2005; Advanced Materials; vol 17; "Book Review: Reflection High Energy Electron Diffraction. By Ayahiko Ichimiya an"
  - `10.1017/cbo9780511735097.011` score 46.2 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.658, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2004; Reflection High-Energy Electron Diffraction; vol ; "Kinematic electron diffraction"
  - `10.1017/cbo9780511735097.023` score 45.1 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.41, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2004; Reflection High-Energy Electron Diffraction; vol ; "Appendix C: Kirchhoff's diffraction theory"
  - `10.1017/cbo9780511735097.009` score 44.5 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.441, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- -; 2004; Reflection High-Energy Electron Diffraction; vol ; "Real diffraction patterns"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)`

### B08 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1093/oso/9780198500742.001.0001
- Query URL: <https://api.crossref.org/works/10.1093/oso/9780198500742.001.0001>  (HTTP: 200)
- Crossref dates: {'published-print': '2004-1-8', 'issued': '2004-1-8', 'published': '2004-1-8'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Oxford University Press' vs Crossref 'Oxford University PressOxford'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)`

### B09 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-1-4615-4817-1
- Query URL: <https://api.crossref.org/works/10.1007/978-1-4615-4817-1>  (HTTP: 200)
- Crossref dates: {'published-print': '1999', 'issued': '1999', 'published': '1999'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer/Plenum' vs Crossref 'Springer US'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)`

### C01 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-1-4615-4817-1_6
- Query URL: <https://api.crossref.org/works/10.1007/978-1-4615-4817-1_6>  (HTTP: 200)
- Crossref dates: {'published-print': '1999', 'issued': '1999', 'published': '1999'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer/Plenum' vs Crossref 'Springer US'
- type: book-chapter
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B10 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-540-37204-2
- Query URL: <https://api.crossref.org/works/10.1007/978-3-540-37204-2>  (HTTP: 200)
- Crossref dates: {'published-print': '1999', 'issued': '1999', 'published': '1999'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer Berlin Heidelberg'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report)`

### B11 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/9783527829712
- Query URL: <https://api.crossref.org/works?query.bibliographic=Shindo+Tomita+Material+Characterization+Using+Electron+Holography+Wiley-VCH+2022&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2022-11-14', 'published-online': '2022-9-2', 'issued': '2022-9-2', 'published': '2022-9-2'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Wiley-VCH' vs Crossref 'Wiley'
- type: monograph
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1002/9783527829712` score 67.0 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Shindo; 2022; Wiley; vol ; "Material Characterization using Electron Holography"
  - `10.1002/9783527829712.ch4` score 46.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.595, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Principles of Electron Holography"
  - `10.1002/9783527829712.fmatter` score 43.8 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.19, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Front Matter"
  - `10.1002/9783527829712.part3` score 43.2 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.258, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Application"
  - `10.1002/9783527829712.index` score 43.2 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.107, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Index"
  - `10.1002/9783527829712.ch11` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.449, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Extension of Analysis of Collective Motions of Electrons"
  - `10.1002/9783527829712.part1` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.222, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Introduction"
  - `10.1002/9783527829712.ch2` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.409, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "M             axwell's Equations and Special Relativity"
  - `10.1002/9783527829712.fmatter` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.19, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Front Matter"
  - `10.1002/9783527829712.ch9` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.362, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Charging Effects and Secondary Electron Distribution of Biological Specimens"
  - `10.1002/9783527829712.part3` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.258, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Application"
  - `10.1002/9783527829712` score 0.0 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Shindo; 2022; Wiley; vol ; "Material Characterization using Electron Holography"
  - `10.1002/9783527829712.ch12` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.472, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Theoretical Consideration on Visualizing Collective Motions of Electrons"
  - `10.1002/9783527829712.app1` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.464, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Physical Constants, Conversion Factors, and Electron Wavelength"
  - `10.1002/9783527829712.part2` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.243, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Principles and Practice"
  - `10.1002/9783527829712.part4` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.387, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Visualization of Collective Motions of Electrons and Their Interpretation"
  - `10.1002/9783527829712.ch3` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.478, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Basis of Transmission Electron Microscopy"
  - `10.1002/9783527829712.ch8` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.216, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Magnetic Field Analysis"
  - `10.1002/9783527829712.ch6` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.257, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Related Techniques and Specialized Instrumentation"
  - `10.1002/9783527829712.ch10` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.379, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Collective Motions of Electrons Around Various Charged Insulators"
  - `10.1002/9783527829712.index` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.107, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Index"
  - `10.1002/9783527829712.ch5` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.412, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Microscope Constitution and Hologram Formation"
  - `10.1002/9783527829712.ch4` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.595, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Principles of Electron Holography"
  - `10.1002/9783527829712.ch1` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.296, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Importance of Electromagnetic Field and Its Visualization"
  - `10.1002/9783527829712.ch7` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.243, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 2022; Material Characterization using Electron Holography; vol ; "Electric Field Analysis"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED / PROJECT_INPUT` -> `METADATA_VERIFIED / PROJECT_INPUT`

### B12 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-00069-1
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-00069-1>  (HTTP: 200)
- Crossref dates: {'published-print': '2019', 'published-online': '2019-11-2', 'issued': '2019', 'published': '2019'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### C02 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-00069-1_16
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-00069-1_16>  (HTTP: 200)
- Crossref dates: {'published-print': '2019', 'published-online': '2019-11-2', 'issued': '2019', 'published': '2019'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book-chapter
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### C03 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-3-030-00069-1_17
- Query URL: <https://api.crossref.org/works/10.1007/978-3-030-00069-1_17>  (HTTP: 200)
- Crossref dates: {'published-print': '2019', 'published-online': '2019-11-2', 'issued': '2019', 'published': '2019'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer International Publishing'
- type: book-chapter
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B13 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1007/978-0-387-40093-8
- Query URL: <https://api.crossref.org/works/10.1007/978-0-387-40093-8>  (HTTP: 200)
- Crossref dates: {'published-print': '2008', 'issued': '2008', 'published': '2008'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer New York'
- type: book
- Discrepancies (baseline vs record): `author` '2 names' vs 'none in Crossref record' (names-missing-in-record)
- Remaining differences (current vs record): `author` '2 names' vs 'none in Crossref record'
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B14 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1007/978-0-387-76501-3
- Query URL: <https://api.crossref.org/works/10.1007/978-0-387-76501-3>  (HTTP: 200)
- Crossref dates: {'published-print': '2009', 'issued': '2009', 'published': '2009'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer US'
- type: book
- Discrepancies (baseline vs record): `title` 'Transmission Electron Microscopy: A Textbook for Materials Science' vs 'Transmission Electron Microscopy' (ratio=0.66)
- Remaining differences (current vs record): `title` 'Transmission Electron Microscopy: A Textbook for Materials Science' vs 'Transmission Electron Microscopy'
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### B15 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1007/978-1-4419-9583-4
- Query URL: <https://api.crossref.org/works/10.1007/978-1-4419-9583-4>  (HTTP: 200)
- Crossref dates: {'published-print': '2011', 'issued': '2011', 'published': '2011'}; bib year matches: ['published-print', 'issued', 'published']
- publisher_form: bib 'Springer' vs Crossref 'Springer US'
- type: book
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### P01 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1143/jjap.27.l1772
- Query URL: <https://api.crossref.org/works/10.1143/JJAP.27.L1772>  (HTTP: 200)
- Crossref dates: {'published-print': '1988-9-1', 'issued': '1988-9-1', 'published': '1988-9-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '9A' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '9A'
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report, authors/title/journal/volume/year only)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (B report, authors/title/journal/volume/year only)`

### P02 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1103/physrevlett.62.2969
- Query URL: <https://api.crossref.org/works/10.1103/PhysRevLett.62.2969>  (HTTP: 200)
- Crossref dates: {'published-online': '1989-6-19', 'issued': '1989-6-19', 'published': '1989-6-19'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '25' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '25'
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) +ABSTRACT(index) (B report, re-confirmed here)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) +ABSTRACT(index) (B report, re-confirmed here)`

### P02E -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1103/physrevlett.63.584.3
- Query URL: <https://api.crossref.org/works/10.1103/PhysRevLett.63.584.3>  (HTTP: 200)
- Crossref dates: {'published-online': '1989-7-31', 'issued': '1989-7-31', 'published': '1989-7-31'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `title` 'Erratum: Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography' vs 'Observation of Surface Undulation Due to Single-Atomic Shear of a Dislocation by Reflection-Electron Holography' (ratio=0.97); `issue` '(absent)' vs '5' (missing)
- Remaining differences (current vs record): `title` 'Erratum: Observation of surface undulation due to single-atomic shear of a dislocation by reflection-electron holography' vs 'Observation of Surface Undulation Due to Single-Atomic Shear of a Dislocation by Reflection-Electron Holography'; `issue` '(absent)' vs '5'
- Label: `existence METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (upgraded in this pass from "index, single"); CONTENT UNVERIFIED` -> `existence METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) (upgraded in this pass from "index, single"); CONTENT UNVERIFIED`

### P03 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0304-3991(93)90123-f
- Query URL: <https://api.crossref.org/works/10.1016/0304-3991(93)90123-F>  (HTTP: 200)
- Crossref dates: {'published-print': '1993-4', 'issued': '1993-4', 'published': '1993-4'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '4' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '4'
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index, single) (B report)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index, single) (B report)`

### P04 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1186/s40679-017-0046-1
- Query URL: <https://api.crossref.org/works/10.1186/s40679-017-0046-1>  (HTTP: 200)
- Crossref dates: {'published-print': '2017-12', 'published-online': '2017-5-10', 'issued': '2017-5-10', 'published': '2017-5-10'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- number_is_article_number: 13
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `SECTION_READ` -> `SECTION_READ`

### P05 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/j.micron.2021.103141
- Query URL: <https://api.crossref.org/works/10.1016/j.micron.2021.103141>  (HTTP: 200)
- Crossref dates: {'published-print': '2021-12', 'issued': '2021-12', 'published': '2021-12'}; bib year matches: ['published-print', 'issued', 'published']
- number_is_article_number: 103141
- type: journal-article
- Discrepancies (baseline vs record): `author-count` '1 + others' vs '11 (full list available)' (incomplete)
- Remaining differences (current vs record): `author-count` '1 + others' vs '11 (full list available)'
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### P06 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2009.05.012
- Query URL: <https://api.crossref.org/works/10.1016/j.ultramic.2009.05.012>  (HTTP: 200)
- Crossref dates: {'published-print': '2009-9', 'issued': '2009-9', 'published': '2009-9'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED` -> `METADATA_VERIFIED`

### P07 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1093/jmicro/dfaa033
- Query URL: <https://api.crossref.org/works?query.bibliographic=Harada+Interference+and+interferometry+in+electron+holography+Microscopy+70+2021+3&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2021-2-1', 'published-online': '2020-6-26', 'issued': '2020-6-26', 'published': '2020-6-26'}; bib year matches: ['published-print']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1093/jmicro/dfaa033` score 63.7 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Harada; 2020/2021; Microscopy; vol 70; "Interference and interferometry in electron holography"
  - `10.1093/jmicro/dfaa067` score 44.1 **REJECT(T,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.333, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Harada; 2020/2021; Microscopy; vol 70; "Introduction to ‘electron interference microscopy’"
  - `10.22443/rms.emc2020.134` score 37.7 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.479, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- RIKEN; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Lens-less Fourier Transform Electron Holography for Vortex Beam"
  - `10.1016/b978-044482051-8/50003-8` score 37.4 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.473, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 1995; Electron Holography; vol ; "Progress in Holographic Interference Electron Microscopy"
  - `10.1093/jmicro/dfh098` score 36.1 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.542, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Harada; 2005; Journal of Electron Microscopy; vol 54; "Optical system for double-biprism electron holography"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) +ABSTRACT(index) (B report)` -> `METADATA_VERIFIED (instruction file) + METADATA_VERIFIED(index) +ABSTRACT(index) (B report)`

### S01 -- UNVERIFIED

- Route: software
- Label: `METADATA_VERIFIED (instruction file, URLs) + SECTION_READ (GitHub README only)` -> `METADATA_VERIFIED (instruction file, URLs) + SECTION_READ (GitHub README only)`

### S02 -- UNVERIFIED

- Route: software
- Label: `METADATA_VERIFIED (instruction file, URLs) + SECTION_READ (GitHub README only)` -> `METADATA_VERIFIED (instruction file, URLs) + SECTION_READ (GitHub README only)`

### P08 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200415
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200415>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P09 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200414
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200414>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### PAT01 -- UNVERIFIED

- Route: patent
- Label: `identity METADATA_VERIFIED(index) (UPGRADED in this pass from "index, single"); INVENTORS, ASSIGNEE, ALL DATES AND THE ENTIRE DESCRIPTION UNVERIFIED` -> `identity METADATA_VERIFIED(index) (UPGRADED in this pass from "index, single"); INVENTORS, ASSIGNEE, ALL DATES AND THE ENTIRE DESCRIPTION UNVERIFIED`

### P14 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0039-6028(80)90675-5
- Query URL: <https://api.crossref.org/works?query.bibliographic=Osakabe+Tanishiro+Yagi+Reflection+electron+microscopy+of+clean+and+gold+deposited+%28111%29+silicon+surfaces+Surface+Science+97+1980+393&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1980-7', 'issued': '1980-7', 'published': '1980-7'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(80)90675-5` score 123.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Osakabe; 1980; Surface Science; vol 97; "Reflection electron microscopy of clean and gold deposited (111) silicon surface"
  - `10.1016/0167-2584(80)90432-6` score 115.6 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Osakabe; 1980; Surface Science Letters; vol 97; "Reflection electron microscopy of clean and gold deposited (111) silicon surface"
  - `10.1016/0167-2584(81)90396-0` score 72.2 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.328, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Osakabe; 1981; Surface Science Letters; vol 102; "Image contrast of dislocations and atomic steps on (111) silicon surface in refl"
  - `10.1016/0039-6028(81)90493-3` score 64.9 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.516, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Osakabe; 1981; Surface Science; vol 109; "Direct observation of the phase transition between the (7 × 7) and (1 × 1) struc"
  - `10.1143/jjap.19.l309` score 64.9 **REJECT(T,C,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.57, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Osakabe; 1980; Japanese Journal of Applied Physics; vol 19; "Reflection Electron Microscope Observations of Dislocations and Surface Structur"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2-3' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '2-3'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P15 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1103/revmodphys.59.639
- Query URL: <https://api.crossref.org/works?query.bibliographic=Tonomura+Applications+of+electron+holography+Reviews+of+Modern+Physics+59+1987+639&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '1987-7-1', 'issued': '1987-7-1', 'published': '1987-7-1'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/revmodphys.59.639` score 73.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Tonomura; 1987; Reviews of Modern Physics; vol 59; "Applications of electron holography"
  - `10.5772/14280` score 42.4 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.805, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 2011; Holography, Research and Technologies; vol ; "Fundamentals and Applications of Electron Holography"
  - `10.1063/1.338452` score 41.6 **REJECT(T,C,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.432, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 1987; Journal of Applied Physics; vol 61; "Electron holography to image magnetic domains (invited)"
  - `10.1002/3527600434.eap174` score 40.1 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.37, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Tonomura; 2003; digital Encyclopedia of Applied Physics; vol ; "Holography, Electron"
  - `10.1063/1.106019` score 37.0 **REJECT(A,T,C,Y,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.588, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'match', 'P': 'mismatch'} -- Ru; 1991; Applied Physics Letters; vol 59; "Phase-shifting electron holography by beam tilting"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '3' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '3'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P16 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1080/00018739200101473
- Query URL: <https://api.crossref.org/works/10.1080/00018739200101473>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2', 'issued': '1992-2', 'published': '1992-2'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P27 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0304-3991(92)90213-4
- Query URL: <https://api.crossref.org/works/10.1016/0304-3991(92)90213-4>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-6', 'issued': '1992-6', 'published': '1992-6'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '4' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '4'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P28 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0039-6028(93)90046-m
- Query URL: <https://api.crossref.org/works?query.bibliographic=Cowley+Electron+holography+and+holographic+diffraction+for+surface+studies+Surface+Science+298+1993+336&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1993-12', 'issued': '1993-12', 'published': '1993-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(93)90046-m` score 92.6 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match', 'I': 'match'} -- Cowley; 1993; Surface Science; vol 298; "Electron holography and holographic diffraction for surface studies"
  - `10.1016/0039-6028(93)90047-n` score 51.7 **REJECT(A,T,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.489, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch', 'I': 'mismatch'} -- Osakabe; 1993; Surface Science; vol 298; "Application of electron holography to surface topography observation"
  - `10.1016/0039-6028(93)90049-p` score 49.6 **REJECT(A,T,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.329, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch', 'I': 'mismatch'} -- Kono; 1993; Surface Science; vol 298; "Surface-structure analysis by forward scattering in photoelectron and Auger-elec"
  - `10.1016/0039-6028(93)90044-k` score 45.9 **REJECT(A,T,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch', 'I': 'mismatch'} -- Peng; 1993; Surface Science; vol 298; "Tensor theories of high energy electron diffraction and their use in surface cry"
  - `10.1016/0039-6028(73)90273-2` score 45.7 **REJECT(T,Y,V,P,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.525, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Cowley; 1973; Surface Science; vol 38; "Electron diffraction from a statistically rough surface"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2-3' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '2-3'
- Label: `METADATA_VERIFIED(index, single) +ABSTRACT(index)` -> `METADATA_VERIFIED(index, single) +ABSTRACT(index)`

### P17 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1143/jjap.22.176
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ichimiya+Many-beam+calculation+of+reflection+high+energy+electron+diffraction+%28RHEED%29+intensities+by+the+multi-slice+method+Japanese+Journal+of+Applied+Physics+22+1983+176&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1983-1-1', 'issued': '1983-1-1', 'published': '1983-1-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1143/jjap.22.176` score 126.3 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Ichimiya; 1983; Japanese Journal of Applied Physics; vol 22; "Many-Beam Calculation of Reflection High Energy Electron Diffraction (RHEED) Int"
  - `10.1143/jjap.24.1365` score 85.1 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.701, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ichimiya; 1985; Japanese Journal of Applied Physics; vol 24; "Correction to “Many-Beam Calculation of RHEED Intensities by the Multi-Slice Met"
  - `10.1007/bfb0109550` score 64.6 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.609, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- -; ; Springer Tracts in Modern Physics; vol ; "Reflection high-energy electron diffraction (RHEED)"
  - `10.1016/j.cpc.2022.108371` score 55.0 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.477, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Hanada; 2022; Computer Physics Communications; vol 277; "sim-trhepd-rheed – Open-source simulator of total-reflection high-energy positro"
  - `10.1016/0039-6028(90)90108-k` score 53.4 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.706, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ichimiya; 1990; Surface Science; vol 235; "Numerical convergence of dynamical calculations of reflection high-energy electr"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '1R' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '1R'
- Label: `METADATA_VERIFIED(index) + SECTION_READ (of the secondary citation only)` -> `METADATA_VERIFIED(index) + SECTION_READ (of the secondary citation only)`

### P18 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1107/s0108767386098756
- Query URL: <https://api.crossref.org/works?query.bibliographic=Peng+Cowley+Dynamical+diffraction+calculations+for+RHEED+and+REM+Acta+Crystallographica+Section+A+42+1986+545&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1986-11-1', 'issued': '1986-11-1', 'published': '1986-11-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767386098756` score 82.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Peng; 1986; Acta Crystallographica Section A Foundations of Crystallography; vol 42; "Dynamical diffraction calculations for RHEED and REM"
  - `10.1107/s0108767387078796` score 66.3 **REJECT(Y,V,P)** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Peng; 1987; Acta Crystallographica Section A Foundations of Crystallography; vol 43; "Dynamical diffraction calculations for RHEED and REM"
  - `10.1107/s0108767387078899` score 47.0 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.478, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Cowley; 1987; Acta Crystallographica Section A Foundations of Crystallography; vol 43; "Surface channeling in RHEED, REM and EELS"
  - `10.1107/s0108767396008057` score 44.6 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.466, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Peng; 1996; Acta Crystallographica Section A Foundations of Crystallography; vol 52; "Approximate Methods in Dynamical RHEED Calculations"
  - `10.1016/b978-0-444-88864-8.50150-3` score 43.2 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.73, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Peng; 1991; Computer Aided Innovation of New Materials; vol ; "DYNAMICAL DIFFRACTION CALCULATIONS FOR RHEED INTENSITY OSCILLATIONS DURING MBE G"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '6' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '6'
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED(index)`

### P19 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/0039-6028(88)90925-9
- Query URL: <https://api.crossref.org/works/10.1016/0039-6028(88)90925-9>  (HTTP: 200)
- Crossref dates: {'published-print': '1988-1', 'issued': '1988-1', 'published': '1988-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P20 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1107/s0108767388010888
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ma+Marks+Bloch-wave+solution+in+the+Bragg+case+Acta+Crystallographica+Section+A+45+1989&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1989-2-1', 'issued': '1989-2-1', 'published': '1989-2-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767388010888` score 65.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Ma; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Bloch-wave solution in the Bragg case"
  - `10.1107/s0108767389005982` score 39.1 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.306, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Peng; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Bloch-wave channeling and HOLZ effects in high-energy electron diffraction"
  - `10.1107/s0108767389001054` score 39.1 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.407, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Wright; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Observation of dependent to independent Bloch wave transition in Kikuchi pattern"
  - `10.1107/s0108767389007269` score 37.9 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.43, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Chukhovskii; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Theoretical study of X-ray diffraction in homogeneously bent crystals – the Brag"
  - `10.1107/s0108767388010657` score 35.8 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.361, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Durbin; 1989; Acta Crystallographica Section A Foundations of Crystallography; vol 45; "Grazing-incidence Bragg–Laue X-ray diffraction"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2' (missing); `pages` '(absent)' vs '174-182' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '2'; `pages` '(absent)' vs '174-182'
- Label: `identity METADATA_VERIFIED(index) (route UPGRADED in this pass to a publisher-URL route) +ABSTRACT(index); PAGE RANGE UNVERIFIED` -> `identity METADATA_VERIFIED(index) (route UPGRADED in this pass to a publisher-URL route) +ABSTRACT(index); PAGE RANGE UNVERIFIED`

### P21 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1107/s0108767389009141
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ma+Marks+Bloch+waves+and+multislice+in+transmission+and+reflection+diffraction+Acta+Crystallographica+Section+A+46+1990+11&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1990-1-1', 'issued': '1990-1-1', 'published': '1990-1-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767389009141` score 78.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Bloch waves and multislice in transmission and reflection diffraction"
  - `10.1107/s0108767390004810` score 75.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 0.945, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Bloch waves and multislice in transmission and reflection diffraction. Erratum"
  - `10.1111/aya.1990.46.issue-1` score 41.3 **REJECT(A,T,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- -; 1990; Acta Crystallographica Section A; vol 46; ""
  - `10.1107/s0108767390002781` score 40.0 **REJECT(T,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.291, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Surface phenomena in RHEED and REM"
  - `10.1107/s0108767306032892` score 39.5 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.452, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Own; 2006; Acta Crystallographica Section A Foundations of Crystallography; vol 62; "Precession electron diffraction 1: multislice simulation"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '1' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '1'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED and strengthened in this pass: title, journal, volume and year now rest on IUCr URLs rather than on prose)` -> `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED and strengthened in this pass: title, journal, volume and year now rest on IUCr URLs rather than on prose)`

### P22 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1107/s0108767390002781
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ma+Marks+Surface+phenomena+in+RHEED+and+REM+Acta+Crystallographica+Section+A+46+1990+594&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1990-7-1', 'issued': '1990-7-1', 'published': '1990-7-1'}; bib year matches: ['published-print', 'issued', 'published']
- container_form: bib 'Acta Crystallographica Section A' is a prefix form of Crossref 'Acta Crystallographica Section A Foundations of Crystallography'
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1107/s0108767390002781` score 73.5 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Ma; 1990; Acta Crystallographica Section A Foundations of Crystallography; vol 46; "Surface phenomena in RHEED and REM"
  - `10.1111/aya.1990.46.issue-1` score 41.3 **REJECT(A,T,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- -; 1990; Acta Crystallographica Section A; vol 46; ""
  - `10.1107/s010876739001011x` score 40.1 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.426, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ma; 1991; Acta Crystallographica Section A Foundations of Crystallography; vol 47; "A computational method for obtaining stationary solutions in RHEED and REM"
  - `10.1107/s0108767391005871` score 39.8 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.328, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ma; 1991; Acta Crystallographica Section A Foundations of Crystallography; vol 47; "A robust solution for RHEED"
  - `10.1107/s0108767387011243` score 39.0 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.311, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Marks; 1988; Acta Crystallographica Section A Foundations of Crystallography; vol 44; "Current flow in reflection electron microscopy and RHEED"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '7' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '7'
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED(index)`

### P13 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200408
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200408>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P12 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200407
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200407>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (route UPGRADED in this pass to a DOI-bearing publisher URL)` -> `METADATA_VERIFIED(index) +ABSTRACT(index) (route UPGRADED in this pass to a DOI-bearing publisher URL)`

### P10 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200403
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200403>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED(index)`

### P11 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1002/jemt.1070200404
- Query URL: <https://api.crossref.org/works/10.1002/jemt.1070200404>  (HTTP: 200)
- Crossref dates: {'published-print': '1992-2-15', 'published-online': '2005-2-4', 'issued': '1992-2-15', 'published': '1992-2-15'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index)` -> `METADATA_VERIFIED(index)`

### P23 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1107/s0021889887086916
- Query URL: <https://api.crossref.org/works/10.1107/S0021889887086916>  (HTTP: 200)
- Crossref dates: {'published-print': '1987-6-1', 'issued': '1987-6-1', 'published': '1987-6-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P24 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0304-3991(84)90210-9
- Query URL: <https://api.crossref.org/works?query.bibliographic=Uchida+J%C3%A4ger+Lehmpfuhl+Direct+imaging+of+atomic+steps+in+reflection+electron+microscopy+Ultramicroscopy+13+1984+325&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1984-1', 'issued': '1984-1', 'published': '1984-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0304-3991(84)90210-9` score 117.9 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Uchida; 1984; Ultramicroscopy; vol 13; "Direct imaging of atomic steps in reflection electron microscopy"
  - `10.1016/0304-3991(84)90080-9` score 74.4 **REJECT(T,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.6, 'C': 'match', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1984; Ultramicroscopy; vol 15; "Observation of surface treatments on single crystals by reflection electron micr"
  - `10.1016/0304-3991(87)90226-9` score 66.9 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.594, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1987; Ultramicroscopy; vol 23; "Observation of double contours of monoatomic steps on single crystal surfaces in"
  - `10.1016/0304-3991(92)90140-f` score 60.5 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.63, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; 1992; Ultramicroscopy; vol 45; "Method of directly imaging the reconstruction on Au(111) and Au(100) by reflecti"
  - `10.1016/s0304-3991(79)80037-6` score 57.5 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.326, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Lehmpfuhl; 1979; Ultramicroscopy; vol 4; "Darkfield and brightfield techniques for electron microscopic observation of ato"
- Discrepancies (baseline vs record): `author[1].given` 'N.' vs 'Y.' (given); `author[2].given` 'W.' vs 'J.' (given); `issue` '(absent)' vs '3' (missing); `pages` '325–328' vs '325-327' (pages)
- Remaining differences (current vs record): `author[1].given` 'N.' vs 'Y.'; `author[2].given` 'W.' vs 'J.'; `issue` '(absent)' vs '3'; `pages` '325–328' vs '325-327'
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED(index, single)`

### P25 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0304-3991(87)90226-9
- Query URL: <https://api.crossref.org/works?query.bibliographic=Uchida+Lehmpfuhl+Observation+of+double+contours+of+monoatomic+steps+on+single+crystal+surfaces+in+reflection+electron+microscopy+Ultramicroscopy+23+1987+53&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1987-1', 'issued': '1987-1', 'published': '1987-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0304-3991(87)90226-9` score 138.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Uchida; 1987; Ultramicroscopy; vol 23; "Observation of double contours of monoatomic steps on single crystal surfaces in"
  - `10.1016/s0304-3991(79)80037-6` score 75.7 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.468, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Lehmpfuhl; 1979; Ultramicroscopy; vol 4; "Darkfield and brightfield techniques for electron microscopic observation of ato"
  - `10.1016/0304-3991(84)90080-9` score 69.9 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.731, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1984; Ultramicroscopy; vol 15; "Observation of surface treatments on single crystals by reflection electron micr"
  - `10.1016/0304-3991(84)90210-9` score 69.4 **REJECT(T,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.617, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1984; Ultramicroscopy; vol 13; "Direct imaging of atomic steps in reflection electron microscopy"
  - `10.1002/jemt.1070200410` score 65.4 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.724, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Uchida; 1992/2005; Microscopy Research and Technique; vol 20; "Observation of atomic steps on single crystal surfaces by a commercial scanning "
- Discrepancies (baseline vs record): `author[1].given` 'N.' vs 'Y.' (given); `issue` '(absent)' vs '1' (missing); `pages` '53–60' vs '53-59' (pages)
- Remaining differences (current vs record): `author[1].given` 'N.' vs 'Y.'; `issue` '(absent)' vs '1'; `pages` '53–60' vs '53-59'
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED(index, single)`

### P26 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0304-3991(90)90041-j
- Query URL: <https://api.crossref.org/works?query.bibliographic=Yao+Cowley+Electron+diffraction+conditions+and+surface+imaging+in+reflection+electron+microscopy+Ultramicroscopy+33+1990+237&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1990-10', 'issued': '1990-10', 'published': '1990-10'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0304-3991(90)90041-j` score 108.1 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match', 'I': 'match'} -- Yao; 1990; Ultramicroscopy; vol 33; "Electron diffraction conditions and surface imaging in reflection electron micro"
  - `10.1016/0304-3991(90)90101-q` score 65.8 **REJECT(A,T,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.541, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch', 'I': 'mismatch'} -- Banzhof; 1990; Ultramicroscopy; vol 33; "Comparison of surface step images in reflection electron microscopy and scanning"
  - `10.1016/0304-3991(93)90116-f` score 57.9 **REJECT(A,T,Y,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.435, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Liu; 1993; Ultramicroscopy; vol 48; "Scanning reflection electron microscopy and associated techniques for surface st"
  - `10.1016/s0304-3991(85)80008-5` score 57.9 **REJECT(A,T,Y,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.662, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Cowley; 1985; Ultramicroscopy; vol 16; "The image contrast of surface steps in reflection electron microscopy"
  - `10.1017/s0424820100180410` score 57.3 **REJECT(T,C,V,P,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.471, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Yao; 1990/2020; Proceedings, annual meeting, Electron Microscopy Society of America; vol 48; "Characterization of Surface Resonance Conditions for Surface Imaging"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '4' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '4'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### ZLWANG96 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1017/cbo9780511525254
- Query URL: <https://api.crossref.org/works?query.bibliographic=Wang+Reflection+Electron+Microscopy+and+Spectroscopy+for+Surface+Analysis+Cambridge+University+Press+1996&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1996-5-23', 'published-online': '2010-1-18', 'issued': '1996-5-23', 'published': '1996-5-23'}; bib year matches: ['published-print', 'issued', 'published']
- type: monograph
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1017/cbo9780511525254` score 53.3 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Wang; 1996/2010; Cambridge University Press; vol ; "Reflection Electron Microscopy and Spectroscopy for Surface Analysis"
  - `10.1017/cbo9780511525254.004` score 49.8 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.486, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Reflection high-energy electron diffraction"
  - `10.1017/cbo9780511525254.017` score 49.0 **REJECT(A,T,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.137, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'mismatch'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Crystallographic structure systems"
  - `10.1017/cbo9780511525254.003` score 48.5 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.4, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Kinematical electron diffraction"
  - `10.1017/cbo9780511525254.014` score 48.5 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.359, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Novel techniques associated with reflection electron imaging"
  - `10.1017/cbo9780511525254.007` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.264, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Imaging surfaces in TEM"
  - `10.1017/cbo9780511525254.009` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.198, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Applications of UHV REM"
  - `10.1017/cbo9780511525254.011` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.191, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Phonon scattering in RHEED"
  - `10.1017/cbo9780511525254.008` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.342, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Contrast mechanisms of reflected electron imaging"
  - `10.1017/cbo9780511525254.004` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.486, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Reflection high-energy electron diffraction"
  - `10.1017/cbo9780511525254.001` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.16, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Preface"
  - `10.1017/cbo9780511525254.006` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.306, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Resonance reflections in RHEED"
  - `10.1017/cbo9780511525254.010` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.232, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Applications of non-UHV REM"
  - `10.1017/cbo9780511525254.002` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.15, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Introduction"
  - `10.1017/cbo9780511525254` score 0.0 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- Wang; 1996/2010; Cambridge University Press; vol ; "Reflection Electron Microscopy and Spectroscopy for Surface Analysis"
  - `10.1017/cbo9780511525254.012` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.253, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Valence excitation in RHEED"
  - `10.1017/cbo9780511525254.003` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.4, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Kinematical electron diffraction"
  - `10.1017/cbo9780511525254.025` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.205, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "References"
  - `10.1017/cbo9780511525254.013` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.262, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Atomic inner shell excitations in RHEED"
  - `10.1017/cbo9780511525254.014` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.359, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Novel techniques associated with reflection electron imaging"
  - `10.1017/cbo9780511525254.005` score 0.0 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.232, 'C': 'match', 'Y': 'match', 'V': 'n/a', 'I': 'match'} -- -; 1996; Reflection Electron Microscopy and Spectroscopy for Surface Analysis; vol ; "Dynamical theories of RHEED"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) (STRENGTHENED in this pass)` -> `METADATA_VERIFIED(index) (STRENGTHENED in this pass)`

### P30 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1038/nature07049
- Query URL: <https://api.crossref.org/works/10.1038/nature07049>  (HTTP: 200)
- Crossref dates: {'published-print': '2008-6', 'issued': '2008-6', 'published': '2008-6'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED and strengthened in this pass)` -> `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED and strengthened in this pass)`

### P31 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2011.04.008
- Query URL: <https://api.crossref.org/works?query.bibliographic=H%C3%BFtch+Houdellier+H%C3%BCe+Dark-field+electron+holography+for+the+measurement+of+geometric+phase+Ultramicroscopy+111+2011+1328&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2011-7', 'issued': '2011-7', 'published': '2011-7'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2011.04.008` score 122.8 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match', 'I': 'match'} -- Hÿtch; 2011; Ultramicroscopy; vol 111; "Dark-field electron holography for the measurement of geometric phase"
  - `10.1016/j.ultramic.2015.10.002` score 80.1 **REJECT(A,T,Y,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.562, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Denneulin; 2016; Ultramicroscopy; vol 160; "Differential phase-contrast dark-field electron holography for strain mapping"
  - `10.1007/978-3-540-85226-1_3` score 67.7 **REJECT(T,C,Y,V,P,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.742, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Hÿtch; ; EMC 2008 14th European Microscopy Congress 1–5 September 2008, Aachen, Germany; vol ; "Dark-field electron holography for the measurement of strain in nanostructures a"
  - `10.1007/978-3-540-85156-1_131` score 67.4 **REJECT(A,T,C,Y,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.488, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Houdellier; ; EMC 2008 14th European Microscopy Congress 1–5 September 2008, Aachen, Germany; vol ; "Strain determination by dark-field electron holography"
  - `10.1016/j.ultramic.2014.06.005` score 65.5 **REJECT(A,T,Y,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.42, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED in this pass via a publisher PII URL plus an independent bibliographic record)` -> `METADATA_VERIFIED(index) +ABSTRACT(index) (CONFIRMED in this pass via a publisher PII URL plus an independent bibliographic record)`

### P32 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2013.07.007
- Query URL: <https://api.crossref.org/works?query.bibliographic=Lubk+Javon+Cherkashin+Dynamic+scattering+theory+for+dark-field+electron+holography+of+3D+strain+fields+Ultramicroscopy+136+2014+42&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2014-1', 'issued': '2014-1', 'published': '2014-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2013.07.007` score 129.1 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match', 'I': 'match'} -- Lubk; 2014; Ultramicroscopy; vol 136; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1017/s1431927613008957` score 89.7 **REJECT(C,Y,V,P,I)** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Lubk; 2013; Microscopy and Microanalysis; vol 19; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1016/j.ultramic.2014.06.005` score 88.6 **REJECT(A,T,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.597, 'C': 'match', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
  - `10.1002/9781118579022.ch4` score 57.8 **REJECT(A,T,C,Y,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.636, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Hÿtch; 2012/2013; Transmission Electron Microscopy in Micro‐Nanoelectronics; vol ; "Dark‐Field Electron Holography for Strain Mapping"
  - `10.1016/j.ultramic.2014.04.002` score 56.5 **REJECT(A,T,V,P,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.512, 'C': 'match', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch', 'I': 'mismatch'} -- Röder; 2014; Ultramicroscopy; vol 144; "Noise estimation for off-axis electron holography"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index) (publisher URL added in this pass)` -> `METADATA_VERIFIED(index) +ABSTRACT(index) (publisher URL added in this pass)`

### P33 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2019.112844
- Query URL: <https://api.crossref.org/works?query.bibliographic=Mei%C3%9Fner+Niermann+Berger+Dynamical+diffraction+effects+on+the+geometric+phase+of+inhomogeneous+strain+fields+Ultramicroscopy+207+2019&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2019-12', 'issued': '2019-12', 'published': '2019-12'}; bib year matches: ['published-print', 'issued', 'published']
- number_is_article_number: 112844
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2019.112844` score 114.3 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Meißner; 2019; Ultramicroscopy; vol 207; "Dynamical diffraction effects on the geometric phase of inhomogeneous strain fie"
  - `10.1016/j.ultramic.2025.114122` score 72.4 **REJECT(A,T,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.5, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.1017/s1431927618005378` score 56.3 **REJECT(T,C,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.65, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Meißner; 2018; Microscopy and Microanalysis; vol 24; "Dynamical Effects on the Geometric Phase"
  - `10.22443/rms.emc2020.1137` score 41.4 **REJECT(A,T,C,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.231, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Technische Universität Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Determination of 3D strain fields by dark field electron holography utilizing dy"
  - `10.1016/j.ultramic.2019.112837` score 40.2 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.273, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Yuan; 2019; Ultramicroscopy; vol 207; "Lattice strain mapping using circular Hough transform for electron diffraction d"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P34 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1038/nphoton.2011.11
- Query URL: <https://api.crossref.org/works/10.1038/nphoton.2011.11>  (HTTP: 200)
- Crossref dates: {'published-print': '2011-4', 'published-online': '2011-2-20', 'issued': '2011-2-20', 'published': '2011-2-20'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): `author-count` '1 + others' vs '9 (full list available)' (incomplete); `issue` '(absent)' vs '4' (missing); `pages` '(absent)' vs '243-245' (missing)
- Remaining differences (current vs record): `author-count` '1 + others' vs '9 (full list available)'; `issue` '(absent)' vs '4'; `pages` '(absent)' vs '243-245'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P35 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1038/ncomms1569
- Query URL: <https://api.crossref.org/works?query.bibliographic=Godard+Carbone+Allain+Three-dimensional+high-resolution+quantitative+microscopy+of+extended+crystals+Nature+Communications+2+2011&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '2011-11-29', 'issued': '2011-11-29', 'published': '2011-11-29'}; bib year matches: ['published-online', 'issued', 'published']
- number_is_article_number: 568
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1038/ncomms1569` score 84.0 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Godard; 2011; Nature Communications; vol 2; "Three-dimensional high-resolution quantitative microscopy of extended crystals"
  - `10.1038/nmat4798` score 39.1 **REJECT(A,T,C,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.417, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Hruszkewycz; 2016/2017; Nature Materials; vol 16; "High-resolution three-dimensional structural microscopy by single-angle Bragg pt"
  - `10.1021/acsphotonics.4c01106.s001` score 36.7 **REJECT(A,T,C,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.349, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- -; ; American Chemical Society (ACS); vol ; "Spatiotemporal Three-Dimensional Quantitative Visualization of Macrophage Phagoc"
  - `10.1021/acsphotonics.4c01106.s002` score 36.6 **REJECT(A,T,C,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.349, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- -; ; American Chemical Society (ACS); vol ; "Spatiotemporal Three-Dimensional Quantitative Visualization of Macrophage Phagoc"
  - `10.4016/5116.01` score 35.2 **REJECT(A,T,C,Y,V)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.486, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- -; 2008; SciVee; vol ; "High Resolution Three Dimensional Lung Reconstruction by Synchrotron Radiation X"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P36 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/1.4914927
- Query URL: <https://api.crossref.org/works/10.1063/1.4914927>  (HTTP: 200)
- Crossref dates: {'published-print': '2015-3-9', 'published-online': '2015-3-12', 'issued': '2015-3-9', 'published': '2015-3-9'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P37 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1038/nmat4798
- Query URL: <https://api.crossref.org/works/10.1038/nmat4798>  (HTTP: 200)
- Crossref dates: {'published-print': '2017-2', 'published-online': '2016-11-21', 'issued': '2016-11-21', 'published': '2016-11-21'}; bib year matches: ['published-print']
- type: journal-article
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2' (missing)
- Remaining differences (current vs record): `issue` '(absent)' vs '2'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P38 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1364/optica.505478
- Query URL: <https://api.crossref.org/works?query.bibliographic=J%C3%B8rgensen+Besley+Slyamov+Hard+X-ray+grazing-incidence+ptychography%3A+large+field-of-view+nanostructure+imaging+with+ultra-high+surface+sensitivity+Optica+11+2024+197&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2024-2-20', 'published-online': '2024-2-1', 'issued': '2024-2-1', 'published': '2024-2-1'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1364/optica.505478` score 124.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Jørgensen; 2024; Optica; vol 11; "Hard x-ray grazing-incidence ptychography: large field-of-view nanostructure ima"
  - `10.1107/s2053273323083778` score 68.6 **REJECT(C,Y,V,P)** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Jørgensen; 2023; Acta Crystallographica Section A Foundations and Advances; vol 79; "Hard X-ray grazing-incidence ptychography: large field-of-view nanostructure ima"
  - `10.1117/12.3063903` score 41.4 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.377, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Sung; 2025; X-Ray Nanoimaging: Instruments and Methods VII; vol ; "Automatic differentiation for x-ray grazing-incidence surface imaging using ptyc"
  - `10.1364/optica.2.000933` score 40.2 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.197, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; 2015; Optica; vol 2; "Ultra-high-sensitivity color imaging via a transparent diffractive-filter array "
  - `10.1364/jsapo.2024.16p_a37_5` score 39.7 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.426, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Shibukawa; 2024; JSAP-Optica Joint Symposia 2024 Abstracts; vol ; "Ultra-wide field-of-view optical focusing with high-speed complex wavefront shap"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P39 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/5.0204240
- Query URL: <https://api.crossref.org/works/10.1063/5.0204240>  (HTTP: 200)
- Crossref dates: {'published-print': '2024-6-1', 'published-online': '2024-6-26', 'issued': '2024-6-1', 'published': '2024-6-1'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P40 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1364/oe.591755
- Query URL: <https://api.crossref.org/works/10.1364/OE.591755>  (HTTP: 200)
- Crossref dates: {'published-print': '2026-8-10', 'published-online': '2026-8-4', 'issued': '2026-8-4', 'published': '2026-8-4'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P41 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1038/s43586-025-00438-3
- Query URL: <https://api.crossref.org/works/10.1038/s43586-025-00438-3>  (HTTP: 200)
- Crossref dates: {'published-online': '2025-10-30', 'issued': '2025-10-30', 'published': '2025-10-30'}; bib year matches: ['published-online', 'issued', 'published']
- number_is_article_number: 68
- type: journal-article
- Discrepancies (baseline vs record): `author-count` '3 + others' vs '10 (full list available)' (incomplete)
- Remaining differences (current vs record): `author-count` '3 + others' vs '10 (full list available)'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P47 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/1.1715155
- Query URL: <https://api.crossref.org/works/10.1063/1.1715155>  (HTTP: 200)
- Crossref dates: {'published-print': '2004-4-26', 'issued': '2004-4-26', 'published': '2004-4-26'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P45 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1063/1.4737152
- Query URL: <https://api.crossref.org/works/10.1063/1.4737152>  (HTTP: 200)
- Crossref dates: {'published-print': '2012-7-23', 'issued': '2012-7-23', 'published': '2012-7-23'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P46 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2013.11.002
- Query URL: <https://api.crossref.org/works/10.1016/j.ultramic.2013.11.002>  (HTTP: 200)
- Crossref dates: {'published-print': '2014-2', 'issued': '2014-2', 'published': '2014-2'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P42 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1093/jmicro/dfaa055
- Query URL: <https://api.crossref.org/works?query.bibliographic=Blackburn+McLeod+Practical+implementation+of+high-resolution+electron+ptychography+and+comparison+with+off-axis+electron+holography+Microscopy+70+2021+131&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2021-2-1', 'published-online': '2020-8-27', 'issued': '2020-8-27', 'published': '2020-8-27'}; bib year matches: ['published-print']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1093/jmicro/dfaa055` score 116.8 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Blackburn; 2020/2021; Microscopy; vol 70; "Practical implementation of high-resolution electron ptychography and comparison"
  - `10.1007/978-1-4615-4817-1_9` score 57.6 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.557, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Rau; 1999; Introduction to Electron Holography; vol ; "High Resolution Off-Axis Electron Holography"
  - `10.22443/rms.emc2020.283` score 57.3 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.297, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Humboldt-Universität zu Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Comparison of off-axis electron holography, differential phase contrast, 4D STEM"
  - `10.22443/rms.emc2020.350` score 52.8 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.502, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Bhat; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Quantitative counting of Zn and O atoms by atomic resolution off-axis and in-lin"
  - `10.1201/9781482289510-124` score 50.8 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.273, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- -; 2001; Electron Microscopy and Analysis 2001; vol ; "Off-axis electron holography of nanomagnet arrays fabricated by interferometric "
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P43 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.micron.2022.103317
- Query URL: <https://api.crossref.org/works/10.1016/j.micron.2022.103317>  (HTTP: 200)
- Crossref dates: {'published-print': '2022-9', 'issued': '2022-9', 'published': '2022-9'}; bib year matches: ['published-print', 'issued', 'published']
- number_is_article_number: 103317
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P44 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1093/jmicro/dfaa066
- Query URL: <https://api.crossref.org/works?query.bibliographic=Herring+Phase+imaging+dislocations+using+diffracted+beam+interferometry+Microscopy+70+2021&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2021-6-6', 'published-online': '2020-12-2', 'issued': '2020-12-2', 'published': '2020-12-2'}; bib year matches: ['published-print']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1093/jmicro/dfaa066` score 87.2 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match'} -- Herring; 2020/2021; Microscopy; vol 70; "Phase imaging dislocations using diffracted beam interferometry"
  - `10.1093/jmicro/dfn027` score 52.2 **REJECT(T,C,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.612, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2009; Journal of Electron Microscopy; vol 58; "Electron beam coherence measurements using diffracted beam interferometry/hologr"
  - `10.1017/s1431927607073825` score 51.0 **REJECT(T,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.613, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2007; Microscopy and Microanalysis; vol 13; "Planar Diffracted-beam Interferometry/Holography"
  - `10.1017/s1431927607073886` score 49.5 **REJECT(T,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.497, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2007; Microscopy and Microanalysis; vol 13; "Coherence Property Measurements of Plasmons and Phonons using Planar Diffracted "
  - `10.1016/j.micron.2022.103317` score 45.7 **REJECT(T,C,Y,V)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.37, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch'} -- Herring; 2022; Micron; vol 160; "Diffracted beam interferometry – Differential phase contrast image of an amorpho"
- Discrepancies (baseline vs record): `pages` '(absent)' vs '297-301' (missing)
- Remaining differences (current vs record): `pages` '(absent)' vs '297-301'
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED(index, single)`

### P51 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1103/physrevresearch.5.033137
- Query URL: <https://api.crossref.org/works?query.bibliographic=Subakti+Daqiqshirazi+Wolf+Electron+holographic+mapping+of+structural+and+electronic+reconstruction+at+mono-+and+bilayer+steps+of+h-BN+Physical+Review+Research+5+2023+033137&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '2023-8-28', 'issued': '2023-8-28', 'published': '2023-8-28'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/physrevresearch.5.033137` score 86.4 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 0.918, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Subakti; 2023; Physical Review Research; vol 5; "Electron holographic mapping of structural reconstruction at mono- and bilayer s"
  - `10.32657/10356/199668` score 35.2 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.5, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; ; Nanyang Technological University; vol ; "Engineering moiré superlattices: structural and electronic properties of twisted"
  - `10.33612/diss.1276909022` score 35.2 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.5, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; ; University of Groningen Press; vol ; "Engineering Moiré Superlattices: Structural and Electronic Properties of Twisted"
  - `10.1103/physrevb.71.132503` score 32.0 **REJECT(A,T,C,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.435, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Arita; 2005; Physical Review B; vol 71; "Electronic structure of sodium cobalt oxide: Comparing mono- and bilayer hydrate"
  - `10.1103/physrevb.108.125126` score 30.3 **REJECT(A,T,C,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.367, 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Zollner; 2023; Physical Review B; vol 108; "Electronic and spin-orbit properties of  h -BN encapsulated bilayer graphene"
- Discrepancies (baseline vs record): `author[1].given` '(none)' vs 'Subakti' (given-missing); `title` 'Electron holographic mapping of structural and electronic reconstruction at mono- and bilayer steps of h-BN' vs 'Electron holographic mapping of structural reconstruction at mono- and bilayer steps of  h−BN' (ratio=0.92); `issue` '(absent)' vs '3' (missing)
- Remaining differences (current vs record): `author[1].given` '(none)' vs 'Subakti'; `title` 'Electron holographic mapping of structural and electronic reconstruction at mono- and bilayer steps of h-BN' vs 'Electron holographic mapping of structural reconstruction at mono- and bilayer steps of  h−BN'; `issue` '(absent)' vs '3'
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index)` -> `METADATA_VERIFIED(index) +ABSTRACT(index)`

### P49 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Kudo+A+fast+and+accurate+computation+method+for+reflective+diffraction+simulations+2023&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.cpc.2023.109029` score 51.3 **REJECT(Y)** {'A': 'match', 'T': 'match', 'T_ratio': 0.916, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable', 'I': 'match'} -- Kudo; 2024; Computer Physics Communications; vol 296; "A fast and efficient computation method for reflective diffraction simulations"
  - `10.1021/acs.langmuir.5c00924.s001` score 32.8 **REJECT(A,T,Y,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.623, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- -; ; American Chemical Society (ACS); vol ; "A Fast and Accurate Method for Contact Angle Calculation via Molecular Dynamic S"
  - `10.1021/acs.jctc.3c00674.s002` score 31.9 **REJECT(A,T,Y,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.431, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- -; ; American Chemical Society (ACS); vol ; "RPA, an Accurate and Fast Method for the Computation of Static Nonlinear Optical"
  - `10.1021/acs.jctc.3c00674.s001` score 31.8 **REJECT(A,T,Y,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.431, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- -; ; American Chemical Society (ACS); vol ; "RPA, an Accurate and Fast Method for the Computation of Static Nonlinear Optical"
  - `10.1109/ultsym.1986.198701` score 31.0 **REJECT(A,T,Y,I)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.62, 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Flory; 1986; IEEE 1986 Ultrasonics Symposium; vol ; "Fast and accurate computation of SAW diffraction effects using asymptotic expans"
- Label: `METADATA_VERIFIED(index) +ABSTRACT(index); TITLE OF THE JOURNAL VERSION UNVERIFIED` -> `METADATA_VERIFIED(index) +ABSTRACT(index); TITLE OF THE JOURNAL VERSION UNVERIFIED`

### SIMTRHEPD -- UNVERIFIED

- Route: software
- Label: `SECTION_READ (of the README only)` -> `SECTION_READ (of the README only)`

### SIMTRHEPD-CPC -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.cpc.2022.108371
- Query URL: <https://api.crossref.org/works/10.1016/j.cpc.2022.108371>  (HTTP: 200)
- Crossref dates: {'published-print': '2022-8', 'issued': '2022-8', 'published': '2022-8'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Remaining differences (current vs record): `title` '(placeholder)' vs 'sim-trhepd-rheed – Open-source simulator of total-reflection high-energy positron diffraction (TRHEPD) and reflection high-energy electron diffraction (RHEED)'
- Label: `SECTION_READ (of the citing README)` -> `SECTION_READ (of the citing README)`

### HANADA95 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1103/physrevb.51.13320
- Query URL: <https://api.crossref.org/works?query.bibliographic=Hanada+Daimon+Ino+Physical+Review+B+51+1995+13320&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '1995-5-15', 'issued': '1995-5-15', 'published': '1995-5-15'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/physrevb.51.13320` score 53.7 **ACCEPT-SUBSTITUTED(T<-P)** {'A': 'match', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Hanada; 1995; Physical Review B; vol 51; "Rocking-curve analysis of reflection high-energy electron diffraction from the S"
  - `10.1016/0039-6028(94)91162-2` score 31.5 **REJECT(C,Y,V,P)** {'A': 'match', 'T': 'untestable', 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Hanada; 1994; Surface Science; vol 313; "Study of the Si(111)7 × 7 surface by RHEED rocking curve analysis"
  - `10.1143/jpsj.53.1911` score 30.9 **REJECT(A,C,Y,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Ino; 1984; Journal of the Physical Society of Japan; vol 53; "New Models for the 7 ×7, 5 ×5, 2 ×8 Structures on Si(111) and Ge(111) Surfaces"
  - `10.1103/physrevlett.75.669` score 30.8 **REJECT(A,C,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Yamanaka; 1995; Physical Review Letters; vol 75; "Electron Standing Wave at a Surface during Reflection High Energy Electron Diffr"
  - `10.1016/0167-2584(89)90019-4` score 27.9 **REJECT(A,C,Y,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Daimon; 1989; Surface Science Letters; vol 221; "Study of Si(111)-Al surface structure by kinetic-energy dependence of polar-angl"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '19' (missing)
- Remaining differences (current vs record): `title` '(placeholder)' vs 'Rocking-curve analysis of reflection high-energy electron diffraction from the Si(111)-(√3 × √3 )R30°-Al, -Ga, and -In surfaces'; `issue` '(absent)' vs '19'
- Label: `SECTION_READ (of the citing README)` -> `SECTION_READ (of the citing README)`

### ABTEM -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.12688/openreseurope.13015.2
- Query URL: <https://api.crossref.org/works/10.12688/openreseurope.13015.2>  (HTTP: 200)
- Crossref dates: {'published-online': '2021-5-21', 'issued': '2021-5-21', 'published': '2021-5-21'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Discrepancies (baseline vs record): none
- Label: `SECTION_READ (of the citing README)` -> `SECTION_READ (of the citing README)`

### RHEEDIUM -- UNVERIFIED

- Route: doi
- Query URL: <https://api.crossref.org/works/10.5281/zenodo.14757400>  (HTTP: 404)
- Label: `SECTION_READ (of the README only)` -> `SECTION_READ (of the README only)`

### PYMULTISLICE -- UNVERIFIED

- Route: software
- Label: `SECTION_READ (of the README only)` -> `SECTION_READ (of the README only)`

### BLACKBURN14 -- VERIFIED-UNCHANGED

- Route: Crossref API /works/10.1016/j.ultramic.2013.08.009
- Query URL: <https://api.crossref.org/works?query.bibliographic=Blackburn+Loudon+Vortex+beam+production+and+contrast+enhancement+from+a+magnetic+spiral+phase+plate+Ultramicroscopy+136+2014+127&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2014-1', 'issued': '2014-1', 'published': '2014-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2013.08.009` score 122.1 **ACCEPT-5FIELD** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Blackburn; 2014; Ultramicroscopy; vol 136; "Vortex beam production and contrast enhancement from a magnetic spiral phase pla"
  - `10.1017/s1431927613007836` score 70.1 **REJECT(T,C,Y,V,P)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.676, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Blackburn; 2013; Microscopy and Microanalysis; vol 19; "Production of Vortex Beam Modes from a Magnetic Spiral Phase Plate"
  - `10.1016/j.ultramic.2013.09.004` score 43.2 **REJECT(A,T,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.309, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Edgcombe; 2014; Ultramicroscopy; vol 136; "Imaging of weak phase objects by a Zernike phase plate"
  - `10.1016/j.ultramic.2017.07.006` score 42.7 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.577, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Minoda; 2017; Ultramicroscopy; vol 182; "Contrast enhancement of nanomaterials using phase plate STEM"
  - `10.1016/j.ultramic.2012.02.004` score 40.8 **REJECT(A,T,Y,V,P)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.629, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Malac; 2012; Ultramicroscopy; vol 118; "Convenient contrast enhancement by a hole-free phase plate"
- Discrepancies (baseline vs record): none
- Label: `METADATA_VERIFIED(index, single)` -> `METADATA_VERIFIED(index, single)`

### U01 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0039-6028(93)90062-o
- Query URL: <https://api.crossref.org/works?query.bibliographic=McCoy+Maksym+Simulation+of+high-resolution+REM+images+Surface+Science&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1993-12', 'issued': '1993-12', 'published': '1993-12'}; bib year matches: n/a
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(93)90062-o` score 70.3 **ACCEPT-SUBSTITUTED(Y,V<-I)** {'A': 'match', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'match'} -- McCoy; 1993; Surface Science; vol 298; "Simulation of high-resolution REM images"
  - `10.1016/0039-6028(93)90254-h` score 53.6 **REJECT(T,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.468, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- McCoy; 1993; Surface Science; vol 297; "Simulation of reflection electron microscopy images: application to high-resolut"
  - `10.1016/0039-6028(94)91386-2` score 49.1 **REJECT(T,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.419, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- McCoy; 1994; Surface Science; vol 310; "Multiple scattering calculations of step contrast in REM images of the Si(001) s"
  - `10.1016/s0039-6028(96)01284-8` score 42.3 **REJECT(T,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.471, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- McCoy; 1997; Surface Science; vol 375; "Dynamical calculation of high-resolution reflection electron microscopy lattice "
  - `10.1016/0039-6028(91)90806-4` score 37.7 **REJECT(T,I)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.383, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- McCoy; 1991; Surface Science; vol 257; "Monte Carlo simulation of equilibrium thermal roughening of the Ge(001)2 × 1 sur"
- Discrepancies (baseline vs record): `title` 'Simulation of high-resolution REM images (title as displayed in the search index)' vs 'Simulation of high-resolution REM images' (ratio=0.67); `volume` '(absent)' vs '298' (missing); `issue` '(absent)' vs '2-3' (missing); `pages` '(absent)' vs '468-472' (missing); `year` '(absent)' vs 'published-print 1993-12; issued 1993-12; published 1993-12' (missing)
- Remaining differences (current vs record): `title` 'Simulation of high-resolution REM images (title as displayed in the search index)' vs 'Simulation of high-resolution REM images'; `volume` '(absent)' vs '298'; `issue` '(absent)' vs '2-3'; `pages` '(absent)' vs '468-472'; `year` '(absent)' vs 'published-print 1993-12; issued 1993-12; published 1993-12'
- Label: `UNVERIFIED` -> `UNVERIFIED`

### U02 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/0039-6028(93)90043-j
- Query URL: <https://api.crossref.org/works?query.bibliographic=Dynamical+theory+of+RHEED+from+stepped+surfaces+Surface+Science&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '1993-12', 'issued': '1993-12', 'published': '1993-12'}; bib year matches: n/a
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/0039-6028(93)90043-j` score 60.9 **ACCEPT-SUBSTITUTED(A,Y,V<-I)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'match'} -- Beeby; 1993; Surface Science; vol 298; "Dynamical theory of RHEED from stepped surfaces"
  - `10.1016/s0039-6028(87)80131-0` score 49.2 **REJECT(T,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.628, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- Ichimiya; 1987; Surface Science; vol 187; "Rheed intensities from stepped surfaces"
  - `10.1016/0167-2584(87)90877-2` score 48.3 **REJECT(T,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.628, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- Ichimiya; 1987; Surface Science Letters; vol 187; "RHEED intensities from stepped surfaces"
  - `10.1016/0039-6028(85)90724-1` score 47.3 **REJECT(T,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.378, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- Kawamura; 1985; Surface Science; vol 161; "RHEED from stepped surfaces and its relation to RHEED intensity oscillations obs"
  - `10.1016/0167-2584(85)90509-2` score 46.7 **REJECT(T,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.378, 'C': 'match', 'Y': 'untestable', 'V': 'untestable', 'I': 'mismatch'} -- Kawamura; 1985; Surface Science Letters; vol 161; "Rheed from stepped surfaces and its relation to rheed intensity oscillations obs"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Beeby, J.L.' (missing); `volume` '(absent)' vs '298' (missing); `issue` '(absent)' vs '2-3' (missing); `pages` '(absent)' vs '307-315' (missing); `year` '(absent)' vs 'published-print 1993-12; issued 1993-12; published 1993-12' (missing)
- Remaining differences (current vs record): `author` '(absent)' vs 'Beeby, J.L.'; `volume` '(absent)' vs '298'; `issue` '(absent)' vs '2-3'; `pages` '(absent)' vs '307-315'; `year` '(absent)' vs 'published-print 1993-12; issued 1993-12; published 1993-12'
- Label: `UNVERIFIED` -> `UNVERIFIED`

### U03 -- UNVERIFIED

- Route: patent
- Label: `UNVERIFIED` -> `UNVERIFIED`

### U04 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1103/physrevb.38.1172
- Query URL: <https://api.crossref.org/works?query.bibliographic=Zhao+Poon+Tong+Physical+Review+B+38+1988+1172&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-online': '1988-7-15', 'issued': '1988-7-15', 'published': '1988-7-15'}; bib year matches: ['published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1103/physrevb.38.1172` score 45.0 **ACCEPT-SUBSTITUTED(T<-P)** {'A': 'match', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Zhao; 1988; Physical Review B; vol 38; "Invariant-embeddingR-matrix scheme for reflection high-energy electron diffracti"
  - `10.1103/physrevb.38.5332` score 26.9 **REJECT(A,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Shen; 1988; Physical Review B; vol 38; "Stability and formation of Al-Cu-(Li,Mg) icosahedral phases"
  - `10.1103/physreva.38.1172` score 26.4 **REJECT(A,C)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Padial; 1988; Physical Review A; vol 38; "Impact broadening of thedtμformation resonances"
  - `10.1016/0375-9601(88)90128-4` score 25.7 **REJECT(A,C,V,P)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'mismatch'} -- Tong; 1988; Physics Letters A; vol 128; "Multiple scattering analysis of reflection high-energy electron diffraction inte"
  - `10.1086/ahr/93.4.1172-b` score 25.6 **REJECT(A,C,V)** {'A': 'mismatch', 'T': 'untestable', 'C': 'mismatch', 'Y': 'match', 'V': 'mismatch', 'P': 'match'} -- -; 1988; The American Historical Review; vol 93; "Erratum"
- Discrepancies (baseline vs record): `issue` '(absent)' vs '2' (missing); `pages` '1172' vs '1172-1182' (last-page-missing)
- Remaining differences (current vs record): `title` '(placeholder)' vs 'Invariant-embeddingR-matrix scheme for reflection high-energy electron diffraction'; `issue` '(absent)' vs '2'; `pages` '1172' vs '1172-1182'
- Label: `METADATA_VERIFIED(index, single) for the citation string; TITLE UNVERIFIED` -> `METADATA_VERIFIED(index, single) for the citation string; TITLE UNVERIFIED`

### U05 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Tonomura+Allard+Pozzi+Electron+Holography+International+Workshop+on+Electron+Holography+Elsevier+1995&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/b978-044482051-8/50000-2` score 80.0 **REJECT(T)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.154, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Tonomura; 1995; Electron Holography; vol ; "Preface"
  - `10.1016/b978-044482051-8/50014-2` score 67.8 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.384, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Bonevich; 1995; Electron Holography; vol ; "Magnetic field observation of vortices in superconductors by electron holography"
  - `10.1007/978-1-4615-4817-1_7` score 67.2 **REJECT(A,T,C,Y)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.594, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Bonevich; 1999; Introduction to Electron Holography; vol ; "Electron Holography of Electromagnetic Fields"
  - `10.1016/b978-044482051-8/50011-7` score 64.9 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.792, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Völkl; 1995; Electron Holography; vol ; "Practical Electron Holography"
  - `10.1016/b978-044482051-8/50025-7` score 62.9 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.447, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Matsumoto; 1995; Electron Holography; vol ; "Fraunhofer in-line electron holography of small weak-phase objects"
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED(index, single) for existence`

### U06 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Osakabe+1995&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1007/bf00032674` score 20.5 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Osakabe; 1995; Plant Molecular Biology; vol 28; "Characterization of the structure and determination of mRNA levels of the phenyl"
  - `10.1093/benz/9780199773787.article.b00133760` score 18.9 **REJECT(A,Y)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- -; 2011; Benezit Dictionary of Artists; vol ; "Osakabe, Tatsuo"
  - `10.1002/9780470015902.a0001319.pub2` score 18.3 **REJECT(Y)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'mismatch', 'V': 'untestable'} -- Osakabe; 2012; Encyclopedia of Life Sciences; vol ; "Plant Light Stress"
  - `10.1080/00150199508217339` score 18.3 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Horiuchi; 1995; Ferroelectrics; vol 169; "Nonlinear optical properties of new ferroelectric LaBGeO5"
  - `10.1063/1.1146208` score 17.8 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Isobe; 1995; Review of Scientific Instruments; vol 66; "Absolute calibration of neutron counters on the Compact Helical System"
- Label: `UNVERIFIED -- DO NOT CITE` -> `UNVERIFIED -- DO NOT CITE`

### U07 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=V%C3%B6lkl+Allard+Joy+Electron+Holography+using+Diffracted+Electron+Beams+%28DBH%29+Introduction+to+Electron+Holography+Springer%2FPlenum+1999&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1007/978-1-4615-4817-1_13` score 106.2 **REJECT(A)** {'A': 'mismatch', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Herring; 1999; Introduction to Electron Holography; vol ; "Electron Holography Using Diffracted Electron Beams (DBH)"
  - `10.1007/978-1-4615-4817-1` score 93.3 **REJECT(T,C)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.422, 'C': 'mismatch', 'Y': 'match', 'V': 'n/a'} -- Völkl; 1999; Springer US; vol ; "Introduction to Electron Holography"
  - `10.1007/978-1-4615-4817-1_3` score 87.9 **REJECT(A,T)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.487, 'C': 'match', 'Y': 'match', 'V': 'n/a'} -- Allard; 1999; Introduction to Electron Holography; vol ; "Optical Characteristics of an Holography Electron Microscope"
  - `10.1016/b978-044482051-8/50017-8` score 83.4 **REJECT(A,T,C,Y)** {'A': 'mismatch', 'T': 'mismatch', 'T_ratio': 0.517, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Frost; 1995; Electron Holography; vol ; "Holography of electrostatic fields"
  - `10.1016/b978-044482051-8/50011-7` score 80.1 **REJECT(T,C,Y)** {'A': 'match', 'T': 'mismatch', 'T_ratio': 0.452, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'n/a'} -- Völkl; 1995; Electron Holography; vol ; "Practical Electron Holography"
- Label: `chapter TITLE and NUMBER METADATA_VERIFIED(index) (it is chapter 13 of [B09], from the chapter-title list B_literature.md section 7 obtained); AUTHORS AND PAGES UNVERIFIED` -> `chapter TITLE and NUMBER METADATA_VERIFIED(index) (it is chapter 13 of [B09], from the chapter-title list B_literature.md section 7 obtained); AUTHORS AND PAGES UNVERIFIED`

### U08 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/j.ultramic.2014.06.005
- Query URL: <https://api.crossref.org/works?query.bibliographic=Dynamical+effects+in+strain+measurements+by+dark-field+electron+holography+Ultramicroscopy+2014&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2014-12', 'issued': '2014-12', 'published': '2014-12'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2014.06.005` score 66.8 **ACCEPT-SUBSTITUTED(A,V<-I)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'untestable', 'I': 'match'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
  - `10.1016/j.ultramic.2025.114122` score 59.6 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.589, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.1016/j.ultramic.2013.07.007` score 51.1 **REJECT(T,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.61, 'C': 'match', 'Y': 'match', 'V': 'untestable', 'I': 'mismatch'} -- Lubk; 2014; Ultramicroscopy; vol 136; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1016/j.ultramic.2015.10.002` score 50.8 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.596, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Denneulin; 2016; Ultramicroscopy; vol 160; "Differential phase-contrast dark-field electron holography for strain mapping"
  - `10.1016/j.ultramic.2010.11.030` score 50.4 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.472, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Béché; 2011; Ultramicroscopy; vol 111; "Dark field electron holography for strain measurement"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Javon, E. and Lubk, A. and Cours, R. and Reboh, S. and Cherkashin, N. and Houdellier, F. and Gatel, C. and H{\"y}tch, M.J.' (missing); `volume` '(absent)' vs '147' (missing); `pages` '(absent)' vs '70-85' (missing)
- Remaining differences (current vs record): `author` '(absent)' vs 'Javon, E. and Lubk, A. and Cours, R. and Reboh, S. and Cherkashin, N. and Houdellier, F. and Gatel, C. and H{\"y}tch, M.J.'; `volume` '(absent)' vs '147'; `pages` '(absent)' vs '70-85'
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED`

### U09 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1016/j.ultramic.2015.10.002
- Query URL: <https://api.crossref.org/works?query.bibliographic=Differential+phase-contrast+dark-field+electron+holography+for+strain+mapping+Ultramicroscopy+2016&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2016-1', 'issued': '2016-1', 'published': '2016-1'}; bib year matches: ['published-print', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2015.10.002` score 82.8 **ACCEPT-SUBSTITUTED(A,V<-I)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'untestable', 'I': 'match'} -- Denneulin; 2016; Ultramicroscopy; vol 160; "Differential phase-contrast dark-field electron holography for strain mapping"
  - `10.1016/j.ultramic.2012.07.010` score 52.0 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.443, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Song; 2013; Ultramicroscopy; vol 127; "Strain mapping of LED devices by dark-field inline electron holography: Comparis"
  - `10.1016/j.ultramic.2010.11.030` score 50.5 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.692, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Béché; 2011; Ultramicroscopy; vol 111; "Dark field electron holography for strain measurement"
  - `10.1016/j.ultramic.2021.113225` score 49.4 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.373, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Pofelski; 2021; Ultramicroscopy; vol 223; "Assessment of the strain depth sensitivity of Moiré sampling Scanning Transmissi"
  - `10.1016/j.ultramic.2025.114122` score 48.2 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.436, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Denneulin, Thibaud and Houdellier, Florent and H{\"y}tch, Martin' (missing); `volume` '(absent)' vs '160' (missing); `pages` '(absent)' vs '98-109' (missing)
- Remaining differences (current vs record): `author` '(absent)' vs 'Denneulin, Thibaud and Houdellier, Florent and H{\"y}tch, Martin'; `volume` '(absent)' vs '160'; `pages` '(absent)' vs '98-109'
- Label: `METADATA_VERIFIED(index, single), strengthened only in that a PubMed record URL carrying the exact title was seen in this pass; AUTHORS UNVERIFIED` -> `METADATA_VERIFIED(index, single), strengthened only in that a PubMed record URL carrying the exact title was seen in this pass; AUTHORS UNVERIFIED`

### U10 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Dynamical+diffraction+effects+of+inhomogeneous+strain+fields+investigated+by+scanning+CBED+and+dark-field+electron+holography+Ultramicroscopy+2025&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.ultramic.2025.114122` score 104.9 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.887, 'C': 'match', 'Y': 'match', 'V': 'untestable', 'I': 'match'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.22443/rms.emc2020.1137` score 58.7 **REJECT(T,C,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.527, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Technische Universität Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Determination of 3D strain fields by dark field electron holography utilizing dy"
  - `10.1016/j.ultramic.2019.112844` score 57.6 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.577, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Meißner; 2019; Ultramicroscopy; vol 207; "Dynamical diffraction effects on the geometric phase of inhomogeneous strain fie"
  - `10.1016/j.ultramic.2014.06.005` score 56.2 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.663, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Javon; 2014; Ultramicroscopy; vol 147; "Dynamical effects in strain measurements by dark-field electron holography"
  - `10.1016/j.ultramic.2013.03.014` score 55.3 **REJECT(T,Y,I)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.431, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable', 'I': 'mismatch'} -- Béché; 2013; Ultramicroscopy; vol 131; "Strain measurement at the nanoscale: Comparison between convergent beam electron"
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED`

### U11 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Four-wave+dark-field+electron+holography+for+imaging+strain+fields&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1088/0022-3727/49/24/244003` score 55.7 **NOT-ACCEPTED(untestable:A,C,Y,V)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Denneulin; 2016; Journal of Physics D: Applied Physics; vol 49; "Four-wave dark-field electron holography for imaging strain fields"
  - `10.22443/rms.emc2020.1137` score 42.9 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.545, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Technische Universität Berlin; 2021; Proceedings of the European Microscopy Congress 2020; vol ; "Determination of 3D strain fields by dark field electron holography utilizing dy"
  - `10.1016/j.ultramic.2025.114122` score 41.1 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.341, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Niermann; 2025; Ultramicroscopy; vol 271; "Dynamical diffraction effects of inhomogeneous strain fields investigated by sca"
  - `10.1016/j.ultramic.2013.07.007` score 39.2 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.699, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Lubk; 2014; Ultramicroscopy; vol 136; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
  - `10.1017/s1431927613008957` score 39.2 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.699, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Lubk; 2013; Microscopy and Microanalysis; vol 19; "Dynamic scattering theory for dark-field electron holography of 3D strain fields"
- Label: `METADATA_VERIFIED(index, single); AUTHORS, JOURNAL, YEAR, VOLUME AND PAGES ALL UNVERIFIED` -> `METADATA_VERIFIED(index, single); AUTHORS, JOURNAL, YEAR, VOLUME AND PAGES ALL UNVERIFIED`

### U12 -- UNVERIFIED

- Route: software
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED(index, single) for existence`

### U13 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Ishizuka+1998&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/s0010-2180(97)00266-6` score 18.7 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Ishizuka; 1998; Combustion and Flame; vol 113; "Flame Speeds in Combustible Vortex Rings"
  - `10.1097/00001756-199801260-00004` score 18.3 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Ishizuka; 1998; NeuroReport; vol 9; "Physiological properties of mouse hippocampal mossy cells"
  - `10.1007/978-1-4612-1642-1_10` score 17.8 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Catalano; 1998; Principles of Perinatal—Neonatal Metabolism; vol ; "Glucose Metabolism in Pregnancy"
  - `10.2514/6.1998-4329` score 17.4 **NOT-ACCEPTED(untestable:T,C,V)** {'A': 'match', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Ishizuka; 1998; Guidance, Navigation, and Control Conference and Exhibit; vol ; "A re-entry guidance law employing simple real-time integration"
  - `10.1016/s0168-0102(98)81946-9` score 17.1 **REJECT(A)** {'A': 'mismatch', 'T': 'untestable', 'C': 'untestable', 'Y': 'match', 'V': 'untestable'} -- Abe; 1998; Neuroscience Research; vol 31; "Synaphin/complexin binds to the H3 domain of syntaxin 1"
- Label: `METADATA_VERIFIED(index, single); TITLE, JOURNAL, VOLUME AND PAGES UNVERIFIED` -> `METADATA_VERIFIED(index, single); TITLE, JOURNAL, VOLUME AND PAGES UNVERIFIED`

### U14 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Philosophical+Magazine+Letters+71+1995&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1080/09500839508240524` score 41.5 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- -; 1995; Philosophical Magazine Letters; vol 71; "Erratum"
  - `10.1080/09500839508241283` score 38.3 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Sinha; 1995/2006; Philosophical Magazine Letters; vol 71; "On the grey Penrose tiling"
  - `10.1080/09500839508241002` score 37.5 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Vitta; 1995; Philosophical Magazine Letters; vol 71; "Thermal-history-dependent magnetization behaviour in Cr/Cu multilayers"
  - `10.1080/09500839508240514` score 37.5 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Watson; 1995/2006; Philosophical Magazine Letters; vol 71; "Quartz amorphization: A dynamical instability"
  - `10.1080/09500839508240523` score 36.8 **NOT-ACCEPTED(untestable:A,T)** {'A': 'untestable', 'T': 'untestable', 'C': 'match', 'Y': 'match', 'V': 'match'} -- Suzuki; 1995; Philosophical Magazine Letters; vol 71; "Grain boundary in cemented carbide"
- Label: `METADATA_VERIFIED(index, single) for the journal/volume/issue/year string only; AUTHORS, TITLE AND PAGES UNVERIFIED` -> `METADATA_VERIFIED(index, single) for the journal/volume/issue/year string only; AUTHORS, TITLE AND PAGES UNVERIFIED`

### U15 -- UNVERIFIED

- Route: search
- Query URL: <https://api.crossref.org/works?query.bibliographic=Sub-%C3%A5ngstr%C3%B6m+resolution+ptychography+in+a+scanning+electron+microscope+at+20+keV+Nature+Communications+2025&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1038/s41467-025-64133-3` score 82.3 **NOT-ACCEPTED(untestable:A,V)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'untestable'} -- Blackburn; 2025; Nature Communications; vol 16; "Sub-ångström resolution ptychography in a scanning electron microscope at 20 keV"
  - `10.1038/s41586-018-0298-5` score 39.4 **REJECT(T,Y)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.309, 'C': 'match', 'Y': 'mismatch', 'V': 'untestable'} -- Jiang; 2018; Nature; vol 559; "Electron ptychography of 2D materials to deep sub-ångström resolution"
  - `10.1126/sciadv.adr0438` score 38.2 **REJECT(T,C)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.507, 'C': 'mismatch', 'Y': 'match', 'V': 'untestable'} -- Venugopal; 2025; Science Advances; vol 11; "High-resolution cryo-EM using a common LaB             6             120-keV ele"
  - `10.1093/oxfordjournals.jmicro.a051100` score 35.9 **REJECT(T,C,Y)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.681, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'untestable'} -- -; 1994; Journal of Electron Microscopy; vol ; "Twenty-nm Resolution Spin-polarized Scanning Electron Microscope"
  - `10.1021/acs.nanolett.8b03166.s001` score 35.3 **REJECT(T,C,Y)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.557, 'C': 'mismatch', 'Y': 'mismatch', 'V': 'untestable'} -- -; ; American Chemical Society (ACS); vol ; "Probing Light Atoms at Subnanometer Resolution: Realization of Scanning Transmis"
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED`

### U16 -- RESIDUAL-DISCREPANCY

- Route: Crossref API /works/10.1017/s1431927620016104
- Query URL: <https://api.crossref.org/works?query.bibliographic=Forbidden+reflection+moir%C3%A9+patterns+in+metal%E2%80%932D+material+interfaces+Microscopy+and+Microanalysis+26+2020+860&rows=5>  (HTTP: search 200; works 200)
- Crossref dates: {'published-print': '2020-8', 'published-online': '2020-7-30', 'issued': '2020-7-30', 'published': '2020-7-30'}; bib year matches: ['published-print', 'published-online', 'issued', 'published']
- type: journal-article
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1017/s1431927620016104` score 82.5 **ACCEPT-SUBSTITUTED(A<-P)** {'A': 'untestable', 'T': 'match', 'T_ratio': 1.0, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'match'} -- Reidy; 2020; Microscopy and Microanalysis; vol 26; "Forbidden Reflection Moiré Patterns in Metal-2D Material Interfaces"
  - `10.1093/mam/ozag053.807` score 40.0 **REJECT(T,Y,V,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.267, 'C': 'match', 'Y': 'mismatch', 'V': 'mismatch', 'P': 'mismatch'} -- Wang; 2026; Microscopy and Microanalysis; vol 32; "Symmetry-Forbidden Oxide Interfaces with Moiré-Type Reconstruction in 3D Stacked"
  - `10.1017/s1431927620016906` score 36.8 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.309, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Warner; 2020; Microscopy and Microanalysis; vol 26; "In-Situ Atomic Level Studies of Unusual Phase Transformations in Metal-chalcogen"
  - `10.1017/s1431927620013859` score 36.2 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.415, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- de Graaf; 2020; Microscopy and Microanalysis; vol 26; "Resolving Hydrogen at Metal-metal Hydride Interfaces Using iDPC-STEM"
  - `10.1017/s1431927620016943` score 35.9 **REJECT(T,P)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.383, 'C': 'match', 'Y': 'match', 'V': 'match', 'P': 'mismatch'} -- Fu; 2020; Microscopy and Microanalysis; vol 26; "In-situ TEM Investigation of Lithiation and Sodiation of 2D Metal Sulfides"
- Discrepancies (baseline vs record): `author` '(absent)' vs 'Reidy, Kate and Varnavides, Georgios and Thomsen, Joachim Dahl and Blackburn, Arthur and Pham, Thang and Kumar, Abinash and LeBeau, James and Ross, Frances' (missing); `issue` '(absent)' vs 'S2' (missing)
- Remaining differences (current vs record): `author` '(absent)' vs 'Reidy, Kate and Varnavides, Georgios and Thomsen, Joachim Dahl and Blackburn, Arthur and Pham, Thang and Kumar, Abinash and LeBeau, James and Ross, Frances'; `issue` '(absent)' vs 'S2'
- Label: `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED` -> `METADATA_VERIFIED(index, single); AUTHORS UNVERIFIED`

### U17 -- UNVERIFIED

- Route: software
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED(index, single) for existence`

### U18 -- UNVERIFIED

- Route: software
- Query URL: <https://api.crossref.org/works?query.bibliographic=rheed%2B%2B+RHEED+intensity+oscillations+epitaxial+growth+SoftwareX&rows=5>  (HTTP: search 200)
- Candidates (DOI, score, verdict, first author, years, container, volume, title):
  - `10.1016/j.softx.2020.100593` score 79.1 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.63, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Daniluk; 2020; SoftwareX; vol 12; "rheed++: A C++ framework to simulation of RHEED intensity oscillations during th"
  - `10.1016/j.softx.2022.101040` score 65.9 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.402, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Daniluk; 2022; SoftwareX; vol 18; "Update 2.0 to rheed++: A complex computer model for dynamical one-beam calculati"
  - `10.1007/978-94-009-0245-9_8` score 54.4 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.433, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Papajová; 1996; Heterostructure Epitaxy and Devices; vol ; "Computer Simulations of Epitaxial Growth, Surface Kinetic Processes and Rheed In"
  - `10.1016/j.cpc.2005.04.005` score 54.3 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.615, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- Daniluk; 2005; Computer Physics Communications; vol 170; "Kinematical calculations of RHEED intensity oscillations during the growth of th"
  - `10.1007/bfb0109551` score 51.3 **REJECT(T)** {'A': 'untestable', 'T': 'mismatch', 'T_ratio': 0.474, 'C': 'untestable', 'Y': 'untestable', 'V': 'untestable'} -- -; ; Springer Tracts in Modern Physics; vol ; "RHEED oscillations"
- Label: `METADATA_VERIFIED(index, single) for existence` -> `METADATA_VERIFIED(index, single) for existence`

<!-- END GENERATED -->
