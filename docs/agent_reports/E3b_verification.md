# E3b - Verification that the E3 findings were applied (commits 25e0106 and 9775bdb)

Reviewer: E3 (verification pass). Date: 2026-09-22. Scope:
`git diff 134331d 9775bdb -- README.md docs/*.md docs/source_map.tsv tools/phase1_numbers.py`.
Line numbers refer to the files at 9775bdb (identical at HEAD for these paths). `E3_review.md` is not
edited. No other file was written. `docs/references.bib`, the agent reports and the scripts under
`tools/bib`, `tools/lit` are unchanged by the two commits.

Status legend: APPLIED (correctly), APPLIED WITH A NEW PROBLEM, NOT APPLIED, DECLINED.

## 1. Verdict in brief

All 36 findings are applied except m10 (declined; the reason is valid and docs/00 and docs/05 now
agree). One application introduces a new problem. Acceptance criterion 3 (N15, docs/05:31-34) now makes
the Si(001) monatomic step the geometric-phase benchmark. On Si(001) that step is the single-layer
a/4 step, whose terraces are screw-related, so the rest of the documents say the geometric phase does
not hold for it. My N15 wording caused this; it was imprecise. Five minor residuals are listed in
section 4. `tools/phase1_numbers.py` passes 10/10, and its new asserted values equal my independent
values.

## 2. Finding by finding

| Finding | Status | Where (quote) |
|---|---|---|
| M1 V0 bias premise and scaling | APPLIED | docs/03:110-117 "If the glancing angle is not measured but taken as the external angle of the internal Bragg condition computed with the assumed `V0`, ... rises by 1.56 % of h per volt ... (0.049 A/V for a bilayer) and by 1.07 %/V at (0,0,8) (0.029 A/V for an a/2 step) ... If `theta_ext` is measured independently (item 7), `V0` does not enter the height"; docs/06:44 and model_assumptions:25 (B1) the same, conditional on item 7; `tools/phase1_numbers.py`:17-23 states premise A |
| M2 read in full | APPLIED | docs/02:19-24 "Read in full: P04 (text and captions), P07, ..., the P49 preprint and ... arXiv:2607.05948v1. Read in part: ..."; model_assumptions:46-49; docs/07:48 "read in part (sec. 3.4, 3.5, 5, 6.2, 9.1 ...)"; docs/07:86-90; docs/04:3-5; README:25, 42-43; docs/00:104-105; SM24 "in the sections read"; model_assumptions:72. Residual: see 4.2 |
| M3 docs/05 section 10 | APPLIED | docs/05:310 "## 10. Literature position (revision 3: ...)"; 312-317 P01 abstract only, P02/P03 metadata only, P08/P09 PubMed; 328-330 post-1993 answer with the absence caveat. Residual Nits: 4.4 |
| M4 forward models | APPLIED | docs/02:83-86 "Their forward models were not read. Report B (index level) found no abstract claiming a dynamical forward model, ... that each of these six papers uses it is UNVERIFIED." No other "all ... multiplicative" statement remains |
| m1 inferences labelled | APPLIED | (a) docs/00:76 "read here as a self-reference, type R2; DERIVED_HERE"; docs/05:224-225, 335-336; docs/07:90-91; B5. (b) docs/00:115 "bulk-terminated slab"; docs/02:133-134; B1; SM04 "(110) faces DERIVED_HERE". (c) docs/02:60-61; the phrase is removed from docs/00. (d) docs/02:110. (e) docs/02:116-117 "(DERIVED_HERE, L1 I7)" |
| m2 PAT01 about P01 | APPLIED | model_assumptions:29 "(col. 1 l. 13-33; SECTION_READ of PAT01, UNVERIFIED for P01)"; also docs/00:83-84 |
| m3 abstract status | APPLIED | model_assumptions:50-51 "P01, P06, P08, P09 and P31 ... abstracts; P02 and P03 ... metadata only"; docs/02:25-26; docs/00:105-106 now lists P09 |
| m4 stale docs/07 rows | APPLIED | docs/07:16 "P02 paywalled (APS), no abstract read; P02E read in full"; :17 "no abstract in any API record"; :19 "open access (CC BY 4.0) but not retrievable by automated clients"; :61-62; :69-71 "superseded by the upload list" |
| m5 post-1993 answer | APPLIED | docs/00:85-88 "... by one group only, ... not proof of absence"; docs/02:54; docs/05:328-330. The three documents agree |
| m6 identifier substitutions | APPLIED | docs/07:76-85 "Twelve records ... eight by ScienceDirect PII or ISBN ..., three by journal, volume and first page ... and HYTCH10 by article number ... Acceptance establishes identity only". I checked the note wording in references.bib for all twelve: it is as stated. Residual: 4.3 |
| m7 item 11 blocking | APPLIED | docs/06:26 "11. (blocking) ... (they fix the number and orientation of steps in a hologram)"; docs/06:27 no longer duplicated; docs/00:93-98 "Eight remain blocking: ... (3) ... (4) ... (5) ... (7) ... (8) ... (11) ... (12) ... (15)". This equals the 8 "(blocking)" items in docs/06 |
| m8 OpenAlex count | APPLIED | docs/02:32-33 "five OpenAlex topic queries and one Semantic Scholar relevance query ... so OpenAlex was used only for the citation graph"; docs/02:143; docs/07:126. Residual Nit: 4.1 |
| m9 title-only | APPLIED | docs/02:69 "(four of the nine classified from the title only, UNVERIFIED)" |
| m10 M1 tests | DECLINED | See section 3 |
| m11 measured Si | APPLIED | docs/02:136-137 "Candidate measured values (... Gajdardziska-Josifovska et al. 1993, crystal wedges, Si not confirmed)" |
| m12 Takeguchi DOI | APPLIED | docs/02:45-46 "Takeguchi 1990 is UNVERIFIED in references.bib"; docs/07:122-123 |
| m13 B05 year | APPLIED | docs/07:40 "2012 (Crossref published-print and copyright year; the Springer page gives publication on 2-3 February 2013, L3)" |
| m14 abstract labels | APPLIED | docs/02:45 "(abstract only, Crossref record)", "(abstract only, OpenAlex record ...)"; :56; :87 |
| m15 SM03/SM14 | APPLIED | SM03 source_id "P08 (Osakabe 1992, +ABSTRACT(PubMed), sentences 2-3 ...)"; SM14 "(Crossref records, B3)" |
| N1 | APPLIED | docs/02:51-52 "of the 60 records, 32 ... and 28 ..." |
| N2 | APPLIED | docs/02:42 "sentences 2-3 and the last sentence" |
| N3 | APPLIED | docs/02:123 "(Eq. (3); paraxial by inference, L2 A-I1)"; SM08 |
| N4 | APPLIED | docs/07:119 "the post-1993 reflection interferometry paper with the most complete abstract" |
| N5 | APPLIED | locator column of SM04 "arXiv:2607.05948v1 Fig. 2c, p. 3 (L5 section 4)", SM12 "P07 para 56, Eqs. (18)-(26)", SM14 "P49 sec. 2.2, Eqs. (14)-(28)", SM15 "P04 p. 3" |
| N6 | APPLIED | `tools/phase1_numbers.py`:2-6 (physics numbers only), :91-96 six new checks; 10/10 pass (section 5) |
| N7 | APPLIED | docs/03:122 "output section 4b" |
| N8 | APPLIED | docs/02:15-16 "... arXiv, a patent record or the project's own page" |
| N9 | APPLIED | docs/02:76-77 "that states a geometry ... (one, Shpiro et al. 2025, states none)" |
| N10 | APPLIED | docs/02:27 "(publisher pages or, where these were unreadable, the indices; L5 section 1)" |
| N11 | APPLIED | docs/04:32 "(P04 p. 3, Eq. (6), p. 4; S01 sec. 2.3.1, 2.6.18, 2.10.3)" |
| N12 | APPLIED | B1 and SM04 "(the principal value of the signed phase moves the other way)"; true for both reflections, because the signed phase is `-|Delta_phi|` plus a multiple of 2 pi |
| N13 | APPLIED | docs/07:127-129 "Later book uploads ... and the B08 RHEED-routine appendix (one of App. A-D, pp. 470-500)" |
| N14 | APPLIED | docs/07:30-32 "B01's chapter numbers on a model-mediated WebFetch of the OUP product page (flagged in L3)" |
| N15 | APPLIED WITH A NEW PROBLEM | docs/05:31-34. See section 4.0 |
| N16 | APPLIED | SM18 "prismatique 0.0.1's tilt.step_size requires embeam 0.0.1 to 0.0.3 ... (the simulation path tilt.series, hrtem.sim does not call it, L2 B-V4)"; docs/04:30 |
| N17 | APPLIED | README:57-63 (the two count commands, with "rewrites ..."). Residual: 4.3 |
| E3 section 4 (CFG-B order) | APPLIED | docs/05:59 "(008) as the proposed working condition (PROJECT_INPUT item 9)" |

## 3. m10 (declined): the reason is valid and the documents are consistent

The documents' reason is that Ali specified tests T1 to T25 for M1 in Phase 2 (docs/07:96-97;
docs/05:303 "(Ali's Phase 2 specification, 2026-09-22; T24 and T25 are re-run in M3 with the full
holography chain)"; docs/00:122-124).
* Validity. E3 m10 was a consistency finding only, docs/00 against docs/05. It did not argue that
  M1 must exclude T24 and T25. A specification by Ali outranks a reviewer's choice between the two
  wordings. It is also coherent. In the calculator, T24 and T25 are the hologram round trip and its
  no-step control (`tools/reflection_step_phase_calculator.py`:1064-1067). They are numpy-only, so M1
  can port them before the M3 chain exists.
* Consistency. The same statement now appears in four places: docs/00:122-124, docs/05:303 (M1 row),
  docs/05:305 (M3 row, "T24/T25 and the carrier trap") and docs/05:25 (acceptance criterion 2,
  "T1 to T25"). No contradiction remains.
* Record. The specification is attributed to Ali only in the orchestrator's text and commit message.
  The repository holds no other record of it. For uniformity with the other supplied inputs, write
  "(PROJECT_INPUT, Ali, 2026-09-22)" in docs/05:303 (Nit).

## 4. New problems and residual inconsistencies

**4.0 New problem introduced by the fixes (from N15): acceptance criterion 3 now benchmarks a step for
which the documents say the geometric phase does not hold.** Quoted: docs/05:31-34 "3. A monatomic-step
benchmark on CFG-B (Ali's Si(001)), with CFG-A as the translation-step validation case, reproduces the
refraction-corrected geometric phase versus glancing angle with a dynamical residual below a threshold
... (proposed initial value 0.1 rad, ASSUMPTION)."
On Si(001) the monatomic step is the single-layer a/4 step. The documents say its terraces are not
related by a translation, so the geometric phase is not expected to hold for it:
* docs/03 section 2: "NOT true for a Si(001) single-layer step `h = a/4`, whose terraces are related by
  the diamond `4_1` screw operation";
* docs/05:59 CFG-B: "screw-related terraces, dynamical difference expected";
* model_assumptions B4;
* SM03 validity: "not Si(001) a/4 steps";
* model_assumptions open question 3: "Only a dynamical calculation can answer this".
The criterion therefore presupposes the answer to an open question. It also clashes with docs/00:128,
which still calls CFG-A "the monatomic-step benchmark". My N15 wording ("CFG-B (Ali's Si(001)); CFG-A as
the translation-step validation case") omitted the a/2 qualification.
Proposed wording (docs/05:31-34): "3. Translation-related step benchmarks reproduce the
refraction-corrected geometric phase versus glancing angle with a dynamical residual below a threshold
recorded in `configs/benchmarks.yaml` (proposed initial value 0.1 rad, ASSUMPTION). The benchmarks are
the CFG-B double-layer a/2 step (Ali's Si(001)) and the CFG-A bilayer (validation case). For the CFG-B
single-layer a/4 step (screw-related terraces) the dynamical phase difference between the two terraces
is computed and reported (open question 3), not held to this threshold." In docs/00:128, write "the
translation-step validation case CFG-A".

**4.1 (Nit, m8 residual)** docs/02:66-68 "Nothing after 2003 ... was found in OpenAlex, Semantic Scholar,
COCI, ... with the queries recorded in L4 section 4". OpenAlex ran no topic query. docs/02:32-33 now
says so, but the sentence still lists OpenAlex among the query engines. Write "in OpenAlex (citation
graph only), Semantic Scholar, ...".

**4.2 (Minor, M2 residual outside the diff scope)** `docs/references.bib`:1212 (HYTCH10) still reads
"SECTION_READ (HAL hal-01742031 full text; L5 section 2.6)". docs/02:23-24, model_assumptions:49,
docs/07:89 and docs/05:322-323 now say Hÿtch et al. 2010 was read in sections 1-2 only. L5 2.6 supports
the documents. Write "SECTION_READ (HAL hal-01742031, sec. 1-2; L5 section 2.6)". docs/02:107 "(...;
read)" could read "(...; sec. 1-2 read)" (Nit).

**4.3 (Nit, m6/N17 residual)** README:62 now tells the reader to run `crossref_check.py report --pass 1`.
In a scratch copy that command rewrites 12 lines of the committed pass-1 block of
`B3_crossref_verification_log.md` (for example "HTTP failures ... 0" becomes 1). The B3 log's claim that
it "reproduces byte for byte" is therefore still untrue. The counts the documents cite (11) are unchanged. Add
"(the regenerated pass-1 block differs from the committed one in the HTTP-failure count and in
untestable-year verdicts)" or fix the script.

**4.4 (Nits, pre-existing text kept under the new docs/05 section 10 heading)** docs/05:318-321 is
headed "(identities Crossref-verified, none read)". Its content descriptors "Bragg-Bragg and
Bragg-channelling resonances, double-contour step contrast" (Yao and Cowley 1990) come from report B at
index level. Add "(content from report B, index level)". docs/05:324-325 "split-illumination
holography (Tanigaki et al. 2012, 2014)" is P07's statement about those papers, UNVERIFIED for them
(L1 S4). docs/05:322 "Hÿtch et al. ... 2011, not read" could add "(abstract only)" to match docs/02:110-111.

**4.5 (Nit, wording next to M1)** docs/03:117 "`V0` is a first-order systematic" is still true for the
predicted step phase (-0.34 rad/V). For the height it now holds only when the glancing angle is not
measured. Write "a first-order systematic of the predicted phase (and of the height when `theta_ext`
is not measured)".

## 5. Recomputation of the new asserted values

`venv/bin/python tools/phase1_numbers.py` (run 2026-09-22, exit 0):

```
Si(111) (4,-4,4), single-bilayer step h = d_111
   dh_inf/dV0(assumed) at 12.0 V = +0.0490 A/V = +1.563 % of h per volt
   height inferred with 12.0 V when V0 is 12.53 V: bias h_inf - h = -0.0261 A  (-0.0492 A per volt of underestimate)
Si(001) (0,0,8), double-layer step h = a/2
   dh_inf/dV0(assumed) at 12.0 V = +0.0291 A/V = +1.072 % of h per volt
Si(001) (0,0,12), double-layer step h = a/2
   dh_inf/dV0(assumed) at 12.0 V = +0.0113 A/V = +0.417 % of h per volt
   [PASS] dh/dV0 (4,-4,4) bilayer [A/V]: 0.0490 (expected 0.049 +- 0.001)
   [PASS] dh/dV0 (4,-4,4) [% of h per V]: 1.5634 (expected 1.56 +- 0.005)
   [PASS] dh/dV0 (0,0,8) a/2 step [A/V]: 0.0291 (expected 0.029 +- 0.001)
   [PASS] dh/dV0 (0,0,8) [% of h per V]: 1.0720 (expected 1.07 +- 0.005)
   [PASS] change of |dphi| (4,-4,4), 12.0 -> 12.53 V [rad]: -0.1783 (expected -0.178 +- 0.001)
   [PASS] change of |dphi| (0,0,8), 12.0 -> 12.53 V [rad]: -0.1277 (expected -0.128 +- 0.001)
   10/10 checks pass
```

My formula `dh_inf/dV0_assumed = h U0'/(2 k_z^2)` (E3_review.md Appendix A constants) gives analytic
and central-difference (+-0.01 V) values of: (4,-4,4) 0.049021 A/V (1.5634 %/V); (0,0,8) 0.029109 A/V
(1.0720 %/V); (0,0,12) 0.011320 A/V (0.4169 %/V). The unchanged values (theta_ext 13.642/13.528 and
16.474/16.380 mrad; |Delta_phi| changes -0.1783 and -0.1277 rad) equal E3_review.md Appendix B. Every
asserted value agrees with mine to all printed digits. The script now computes the derivative with
respect to the assumed V0, as docs/03 describes, and still prints the 0.53 V secant separately.
