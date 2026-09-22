# E3 - Adversarial review of revision 3 of the summary documents (diff since 54050f3)

Reviewer: E3 (adversarial scientific reviewer). Date: 2026-09-22. Branch
`claude/electron-holography-orchestration-nakd7r`, HEAD `134331d`. Status: written incrementally.

Scope: `git diff 54050f3 --` README.md, docs/00, docs/02, docs/03 (one sentence), docs/04, docs/05,
docs/06, docs/07, docs/model_assumptions.md, docs/source_map.tsv, tools/phase1_numbers.py. Evidence
record (not under review): B3 (log, results TSV, pass-2 TSV), L1, L2, L3, L4 (with TSV), L5, the
cached records in `docs/agent_reports/crossref_cache/` and `citation_cache/`, and `docs/references.bib`.
The instruction file is not in the repository or anywhere on this machine; the source-policy check is
therefore made against the agent reports, the caches and `references.bib` only. No web access.

Method. (1) The physics numbers were recomputed with my own script
(`e3_recompute.py`, Appendix A, output in Appendix B), written and run BEFORE I opened
`tools/phase1_numbers.py` or any part of the calculator; only afterwards was `tools/phase1_numbers.py`
run and read. (2) Every count was re-derived by running the committed scripts. Scripts that write
into the repository (`crossref_check.py report`, `citation_lists.py build`) were run in a scratch copy
of the repository (`tar` copy of the working tree including `.git`), so nothing under review or in
the record was modified. (3) Every quantitative or bibliographic claim in the diff was traced to the
report and locator it implies. Labels: Blocker, Major, Minor, Nit.

## 0. Verdict in brief

No Blocker. Four Major items: M1 the V0 height-bias sentence (docs/03, docs/06 item 20, B1) has the
right sign and size (+0.049 A per volt of assumed V0 for a bilayer at (4,-4,4); too small when V0 is
underestimated) but omits the premise that the glancing angle is computed from the assumed V0 (with a
measured angle the bias is zero) and that the bias scales with h (1.56 %/V; 1.07 %/V at (0,0,8)); M2
"read in full" is claimed for the C03 manuscript, Hytch 2010, S01, S02 and the P49 code, which the
reports read only in part; M3 docs/05 section 10 is still revision 2 ("index-level evidence only",
"P01 could not be read", "the citation-graph search could not be run"); M4 docs/02 states "All use
multiplicative-object forward models" for six papers whose forward models no revision-3 report
read (a revision-2 index-level inference, two of the six known at identity level only). Counts (60,
57, 32/28, 9, 11, seven blocking) reproduce from the committed scripts; "six OpenAlex" queries are five
OpenAlex plus one Semantic Scholar. The eleven identifier-substitution acceptances should be kept
(verdict in m6), but the justification in docs/07 needs correcting (twelve, not eleven; notes not
uniformly marked).

## 1. Independent physics recomputation (200 keV, a = 5.4309 A)

Premises (mine, stated before reading the repository code): CODATA 2018 / SI-2019 constants,
`m_e c^2 = 510998.950 eV`; inside the crystal `K^2 = k^2 + U0` with
`U0 = [2 e V0 (T + m c^2) + (e V0)^2]/(hbar c)^2` (the `(e V0)^2` term, dropped in the docs, moves
`theta_ext` by 2e-5 mrad and is negligible); specular reflection from planes parallel to the surface;
internal Bragg condition `K_z = g/2`; parallel wave-vector conserved, so
`k_z = k sin(theta_ext) = sqrt(g^2/4 - U0)`; step phase between translation-related terraces
`Delta_phi = -(k_out - k_in).R = -2 k_z h` (vacuum wavelength, external angle). `|Delta_phi|` below is
the magnitude of the unwrapped phase `2 k_z h`, as in docs/03.

| Reflection, step | V0 (V) | theta_ext (mrad) | abs(Delta_phi) (rad) | mod 2 pi in [0, 2 pi) | principal value of `-2 k_z h` | h_2pi (A) |
|---|---|---|---|---|---|---|
| (4,-4,4), h = d_111 = 3.1355 A | 12.00 | 13.6415 | 21.43156 | 2.58201 | -2.58201 | 0.9193 |
| (4,-4,4), h = d_111 | 12.53 | 13.5280 | 21.25323 | 2.40368 | -2.40368 | 0.9270 |
| (0,0,8), h = a/2 = 2.7155 A | 12.00 | 16.4743 | 22.41423 | 3.56467 | +2.71851 | 0.7612 |
| (0,0,8), h = a/2 | 12.53 | 16.3805 | 22.28651 | 3.43696 | +2.84623 | 0.7656 |
| (0,0,12), h = a/2 | 12.00 | 26.4205 | 35.94393 | 4.52800 | +1.75518 | 0.4747 |
| (0,0,12), h = a/2 | 12.53 | 26.3620 | 35.86443 | 4.44850 | +1.83469 | 0.4757 |

Change from 12.0 V to 12.53 V: (4,-4,4) `-0.1783 rad`, `theta_ext -0.1135 mrad`; (0,0,8)
`-0.1277 rad`, `-0.0939 mrad`; (0,0,12) `-0.0795 rad`, `-0.0585 mrad`. At (0,0,8) and (0,0,12) the
principal-value magnitude moves the other way (+0.128 and +0.080 rad), because the unwrapped phase
sits above an odd multiple of pi there; the documents' "-0.128 rad" is right in their own convention
(`|Delta_phi|`, or its value in [0, 2 pi)).

Derivatives at 12.0 V (analytic): (4,-4,4) `d|Delta_phi|/dV0 = -0.3351 rad/V`,
`dtheta_ext/dV0 = -0.2133 mrad/V`; (6,-6,6) setting `-0.2032 rad/V`, `-0.1294 mrad/V`; (0,0,8), a/2:
`-0.2403 rad/V`, `-0.1766 mrad/V`; (0,0,12), a/2: `-0.1498 rad/V`, `-0.1102 mrad/V`.

`tools/phase1_numbers.py` (run after the above) prints the same values to every printed digit
(13.642/13.528 mrad, 21.4316/21.2532 rad, -0.1783 rad; 16.474/16.380 mrad, 22.4142/22.2865 rad,
-0.1277 rad; 26.420/26.362 mrad, 35.9439/35.8644 rad, -0.0795 rad) and passes 4/4 checks.
The (0,0,8) angles agree with CFG-B in docs/05 (theta_int 18.47, theta_ext 16.47 mrad, wrap period
0.761 A, foreshortening 60.7).

### 1.1 Sign and size of the height bias: the revision-3 reversal is RIGHT, under a premise the documents do not state

Premise A (the only one under which V0 enters a height at all): the phase is measured at the
reflectivity peak and unwrapped on the correct branch; the glancing angle is NOT measured but taken
as the external angle of the internal Bragg condition computed with the assumed V0, so
`h_inf = |Delta_phi| / (2 k sin theta_ext(V0_assumed)) = |Delta_phi| / (2 sqrt(g^2/4 - U0(V0_assumed)))`.
Then `dh_inf/dV0_assumed = + h U0' / (2 k_z^2)`:

| Case | dh_inf/dV0_assumed (analytic, 12 V) | relative | bias when V0 is underestimated by 1 V |
|---|---|---|---|
| (4,-4,4), h = d_111 | +0.04902 A/V | +1.563 %/V | -0.0479 A (assumed 11 V, true 12 V); -0.0494 A (assumed 12 V, true 13 V); -0.0492 A/V secant for true 12.53 V |
| (0,0,8), h = a/2 | +0.02911 A/V | +1.072 %/V | -0.029 A/V (script: -0.0292 A/V secant) |
| (0,0,12), h = a/2 | +0.01132 A/V | +0.417 %/V | -0.011 A/V (script: -0.0113 A/V secant) |

So an underestimated V0 makes the inferred height too SMALL, by about 0.049 A per volt for a single
bilayer at (4,-4,4). The old wording "biased by about +0.05 A per volt of underestimate" was wrong in
sign. The two earlier figures are not two premises with opposite physics: E's -0.0486 A/V is the
derivative with respect to the TRUE V0 at fixed assumed V0 (phase change re-expressed as a height at
fixed `k_ext`), E2's +0.0492 A/V the derivative with respect to the ASSUMED V0 at fixed measured phase;
by construction they have opposite signs and both mean "too small when V0 is underestimated" (my
finite differences give 0.0479 to 0.0494 A/V depending on the interval). The error was introduced when
E2 F19's "+0.0492 A/V" was re-worded as "+ per volt by which V0 is underestimated".

Premise B: if `theta_ext` is measured (PROJECT_INPUT item 7, blocking), `h = |Delta_phi|/(2 k sin
theta_ext)` contains no V0 and the bias is zero. Premise C (for contrast only): reading the wrapped
phase as the refractive departure `(g - 2 k_z) h` would give the opposite sign and -0.284 A/V at
(4,-4,4); this reading is valid only for lattice-translation steps and is not what the documents or
the script do. The documents state neither premise A nor that the bias scales with h (see Major M1).

## 2. Counts re-derived from the committed scripts

| Claim (file:line) | Script run (in a scratch copy) | Printed value | Verdict |
|---|---|---|---|
| "60 records, 57 distinct works, 32 classified from an abstract and 28 from the title only" (docs/02:48-49) | `venv/bin/python tools/lit/citation_lists.py build --list` (runs offline from `citation_cache/`; exit 0; rewrote `L4_citing_works.tsv` identically) | "Unique citing records overall: 60"; "distinct works ...: 57"; "classified from an abstract: 32; from the title only (UNVERIFIED): 28" | correct; 32 + 28 = 60 counts records (rows), not distinct works (Nit N1) |
| "The nine citing works after 2003" (docs/02:64) | same | "Rows published after 2003 ... (total 9)"; none of the three same-content pairs is post-2003, so 9 rows = 9 distinct works | correct; but 4 of the 9 are classified from the title only (Minor m9) |
| Semantic Scholar zero hits (q18, q19, q21), arXiv zero (q26) (docs/02:70-72) | cached `citation_cache/search/q18_B_s2-bulk.json`, `q19`, `q21` (`total` 0) and `q26_B_arxiv.xml` (`totalResults` 0) | 0, 0, 0, 0 | correct |
| "six OpenAlex search queries failed on the rate limit" (docs/02:30; also docs/02:133-134, docs/07:114) | no script prints "six"; the cache lacks q01, q02, q03, q16, q28 (OpenAlex) and q09 (Semantic Scholar relevance) | 5 OpenAlex + 1 Semantic Scholar | wrong attribution (Minor m8) |
| "Eleven records were accepted with an identifier ... standing in" (docs/07:74-78) | `venv/bin/python tools/bib/crossref_check.py report --pass 1` | `"search_accept_subst": 11` | count correct; not printed by the default `report` (which prints the pass-2 block), and see m6 |
| bibliography totals (docs/02:16, docs/07:73-74 "counts printed by ... report") | `venv/bin/python tools/bib/crossref_check.py report` (default = pass 2) | entries 99 -> 132; verified 93 -> 125; unverified 6 -> 7; with doi 82 -> 114; 33 proposed, 30 + 1 verified, 2 unverified; validate: no errors | reproduced; the committed pass-2 block and TSV were regenerated byte-identical |
| (record, not a summary) B3 log: "`report --pass 1` regenerates it ... byte for byte" | `report --pass 1` | 12 lines differ from the committed pass-1 block: "HTTP failures ... 0" becomes 1, and several REJECT verdicts change 'Y': 'mismatch' to 'untestable' (pass-2 acceptance-test fix) | the pass-1 block is no longer reproduced byte for byte; the counts cited by the summaries (11) are unchanged (Minor m6) |
| "Seven remain blocking" (docs/00:90) | count of "(blocking)" in docs/06 | items 3, 4, 5, 7, 8, 12, 15 = 7 | consistent |
| "22 items" (README:22) | docs/06 | 22 | consistent |
| 0.049 A/V, -0.178 rad, -0.128 rad (docs/03, docs/06, B1, SM04) | `venv/bin/python tools/phase1_numbers.py` | -0.0492 A per volt of underestimate; -0.1783; -0.1277; 4/4 checks | consistent with my recomputation |
| 25 self-checks (README, docs/00) | `venv/bin/python tools/reflection_step_phase_calculator.py` | "25/25 checks pass" | consistent |

Every other number added in the diff traces to a report locator (Section 5). No number in the diff was
found that neither a committed script nor a report produces, except "six" (m8).

## 3. Findings

### Blocker

None found. No DOI, page, year or equation in the diff lacks a source in the reports, the caches or
`references.bib`; no count contradicts its script; the sign reversal is correct.

### Major

**M1. The V0 height-bias sentence omits the premise under which it holds and quotes a value that is
specific to one step height and one reflection.**
Quoted: docs/03:110-113 "A height inferred from a fixed measured phase with an assumed `V0` rises by
0.049 A per volt of assumed `V0` at (4,-4,4), so underestimating `V0` makes the inferred height too
SMALL by about 0.049 A per volt"; docs/06:44 "a height inferred from a fixed measured phase is too
small by about 0.049 A per volt by which `V0` is underestimated"; model_assumptions.md:25 (B1), same.
Evidence: Section 1.1. The sign is right and the size is right for h = d_111 at (4,-4,4) (+0.04902 A/V
analytic; 0.0479 to 0.0494 A/V by finite differences). But V0 enters the height only if the glancing
angle is taken from the internal Bragg condition computed with the assumed V0 (premise A, stated only
in the docstring of `tools/phase1_numbers.py`, lines 15-17). If `theta_ext` is measured (item 7,
blocking) the bias is zero. The bias is proportional to h (1.563 % of h per volt at (4,-4,4), 1.072 %/V
at (0,0,8), 0.417 %/V at (0,0,12)), so "0.049 A per volt" applied to a 10 nm patterned step
understates it by a factor of about 30; and Ali's sample is Si(001), for which the (0,0,8) value
(0.029 A/V for an a/2 step) is the relevant one.
Proposed wording (docs/03; shorten for docs/06 item 20 and B1): "If the glancing angle is not measured
but taken as the external angle of the internal Bragg condition computed with the assumed `V0`, a
height inferred from a fixed, correctly unwrapped phase scales as
`h_inf = |Delta_phi|/(2 k sin theta_ext(V0))` and rises by 1.56 % of h per volt of assumed `V0` at
(4,-4,4) (0.049 A/V for a bilayer) and by 1.07 %/V at (0,0,8) (0.029 A/V for an a/2 step).
Underestimating `V0` therefore makes the height too small. If `theta_ext` is measured independently
(item 7), `V0` does not enter the height (`tools/phase1_numbers.py`, premise in its docstring;
revision 3 corrects the sign of the earlier wording)."

**M2. "Read in full" is claimed for sources the reports read only in part.**
Quoted: docs/02:19-22 "Read in full: ... the prismatique rendered documentation (S01), the Prismatic
project pages (S02), the P49 preprint and its code, ... the accepted manuscript of chapter C03, Hÿtch et
al. 2010 (companion of P31), ..."; model_assumptions.md:46-48 "... the C03 accepted manuscript and the
Hytch et al. 2010 companion of P31 are read in full (reports L1, L2, L5)"; docs/07:47 "the author
accepted manuscript is READ"; docs/07:79 "S01, S02, P49 (preprint and code) ... read in full";
docs/04:3 "public documentation read in full: P04, the prismatique rendered docs and the Prismatic
project pages"; README:42 and docs/00:101 "the open sources are read in full".
Evidence: L5 section 1, C03 row: "yes (sections listed in 2.5)" - the sections are 3.4, 3.5, 5 (intro,
5.7-5.9), 6.2 and 9.1 of a 138-page manuscript; L5 section 2.6 extracts Hÿtch 2010 sections 1-2 only and
never says "in full" (the "full text" in the references.bib label was written in B3 pass 2 "as
instructed" by the coordinator, not taken from L5); L2 section 1: S01 "Not read: examples, STEM pages", S02 "Not read: GUI and STEM tutorials",
Compiling page "read for precision and CUDA statements only"; L2 D.1: of the P49 code only the README
and `surf.f90` were read, "The rest of the Fortran was only grepped". Open sources NOT read: P05 (open,
CC BY, not retrievable), the J-STAGE PDF of Tanishiro 2003 (abstract, captions and references only),
US 5,192,867 (cols. 3-4 and part of col. 7), Suzuki 2001 (flagged free, not retrieved). The negative
claim "glancing-angle reflection ptychography described only for EUV" (SM24; model_assumptions open
question 7) is supported only for the sections read.
Proposed wording (docs/02:19-22): "Read in full: P04 (text and captions), P07, US 4,998,788, P02E, the
P49 preprint and arXiv:2607.05948v1. Read in part: US 5,192,867 (cols. 3-4, 7), the prismatique
documentation (API, literature and licence pages; examples and STEM pages not read), the Prismatic
pages listed in L2 C.1, the P49 code (README and output routine), the C03 accepted manuscript (sec. 3.4,
3.5, 5, 6.2, 9.1; L5 2.5), Hÿtch et al. 2010 (sec. 1-2; L5 2.6)." Replace "READ" in docs/07:47 by "read
in part (sec. 3.4, 3.5, 5, 6.2, 9.1; L5 section 2.5)"; in SM24 write "glancing-angle reflection
ptychography appears only as EUV in the sections read"; README:42 and docs/00:101: "the open sources
named in docs/02 are read (in full or in the parts listed there)".

**M3. docs/05 section 10 is left at revision 2 and contradicts revision 3 in the same document set.**
Quoted: docs/05:309 "## 10. Literature position (from `docs/agent_reports/B_literature.md`, index-level
evidence only)"; docs/05:311-312 "1989 (P02, GaAs(110), dislocation surface undulation, 0.01 A
precision claimed at abstract level)"; docs/05:314-316 "P08 is reported at abstract-index level ...
(`+ABSTRACT(index)`; the paper was not read). The content of P01 itself could not be read here.";
docs/05:326-328 "No published electron reflection-mode ptychography and no post-2015 reflection
electron holography experiment was found, but the citation-graph search could not be run (blocked), so
this is a search failure, not evidence of absence."
Evidence: the header of docs/05 claims version 0.3 after Phase 1 (docs/05:3-6). L4 ran the citation
graph (60 records) and found post-1993 reflection interferometry (Suzuki 2001, Tanishiro 2003); L5 2.1
read the P01 abstract (Pt(111), sensitivity "of the order of 0.01 nm", i.e. 0.1 A); L5 2.2 read P08 on
PubMed; P02's abstract was NOT read (L5 section 1: "the abstract was seen only through the WebFetch
summariser and is not counted"), so "0.01 A precision claimed at abstract level" for P02 has no
revision-3 support. The B3 log already flagged docs/05:290 for update ("Findings that change what the
summary documents say").
Proposed wording: replace section 10 by a pointer: "Literature position: `docs/02_literature_position.md`
(revision 3). In brief: P01 is known from its abstract only (Pt(111), two regions of the reflection
image overlapped by a biprism, optical reconstruction, sensitivity of the order of 0.01 nm); P02 and P03 from their metadata only; after 1993
the citation graph and the searches of L4 found reflection interferometry only by the Tokyo Tech group
(2001-2003) and no electron reflection-mode ptychography, an absence in the databases searched, not a
proof of absence."

**M4. An index-level inference about six ptychography papers is restated as a fact.**
Quoted: docs/02:75-78 "Zhu et al. 2015 ..., Jørgensen et al. 2024, Myint et al. 2024 and Guenzing et
al. 2026 are confirmed at abstract level; Godard et al. 2011 and Hruszkewycz et al. 2017 at identity
level (L4 section 4.3). All use multiplicative-object forward models."
Evidence: L4 4.3 confirms topic and identity only; none of the abstract quotations in L4 mentions the
forward model, and for Godard 2011 and Hruszkewycz 2017 L4 found no abstract at all ("identity only").
The sentence descends from B_literature.md section 5 ("at abstract level [index] ... built on a
multiplicative ... object model"), an index-level inference that revision 3 says it supersedes
(docs/02:6-8). The only revision-3 evidence is Senhorst et al. 2026 (abstract): reflection
ptychography is "commonly interpreted with the same two-dimensional thin-sample model used in
transmission" (L4 4.3), which is weaker than "all".
Proposed wording: "Their forward models were not read. B_literature.md (index level) found no abstract
claiming a dynamical forward model, and Senhorst et al. 2026 (abstract) state that reflection
ptychography is commonly interpreted with the two-dimensional thin-sample (multiplicative) model; that
each of these six papers uses it is UNVERIFIED."

### Minor

**m1. Inferences are stated as facts in five places (the reports label each one DERIVED_HERE).**
(a) R2 reading of P01: docs/00:75-76 "its abstract ... gives ... an electron biprism overlapping two
regions of the reflection image (a self-reference, type R2)"; docs/05:223-224 "R2 is the arrangement
of the P01 abstract"; docs/05:332-334 "the P01 abstract gives the surface and the self-reference
arrangement"; docs/07:82 "the P01 abstract gives Pt(111) and a self-reference". L5 2.1 and L5 3 label
the R2 reading DERIVED_HERE, as do docs/02:36, the CFG-O row and SM22. (b) "(110) slab": docs/00:112,
docs/02:125, model_assumptions B1 and SM04 (both under a SECTION_READ label). L5 4: "Vacuum along [110]
means the slab faces are (110) (DERIVED_HERE)". (c) "both waves reflected" for the Tokyo Tech
holograms: docs/00:84, docs/02:57; L4 5.1 labels it "Inference (DERIVED_HERE) from the Fig. 4 caption".
(d) docs/02:101-102 "the same sign structure as this repository's step phase": L5 2.6 "Inference
(DERIVED_HERE) ... a consistency check of convention, not a validation". (e) docs/02:108-109 "PAT01
embodiment 2 is a published reflection-mode split-illumination arrangement": L1 4.3 inference I7.
Proposed wording: append "(DERIVED_HERE, L5 2.1)", "(DERIVED_HERE from the vacuum direction, L5 4)",
"(DERIVED_HERE from the Fig. 4 caption, L4 5.1)", "(DERIVED_HERE, L5 2.6)", "(DERIVED_HERE, L1 I7)"
respectively; in docs/00:76 write "... two regions of the reflection image (read here as a
self-reference, type R2; DERIVED_HERE) ...".

**m2. A statement by PAT01 about the prior art is attached to P01 without the UNVERIFIED label.**
Quoted: model_assumptions.md:29 (B5) "R2 is the arrangement of the P01 abstract (...; SM22), which the
same patent describes as the prior art (interference between reflected waves, about ten fringes;
col. 1 l. 13-33)". Evidence: L1 4.2 S1: SECTION_READ(PAT01), UNVERIFIED for P01; the patent cites P01
and "Optik Suppl. 3, 77 (1987) p. 4" jointly and "does not say which statement applies to which of the
two". docs/02:37 and SM22 label it correctly. Proposed wording: "... which the patent describes, for
the prior art P01 and an unidentified 1987 Optik report jointly, as interference between reflected
waves giving about ten fringes (col. 1 l. 13-33; SECTION_READ of PAT01, UNVERIFIED for P01)".

**m3. What is "known only from abstracts" differs between documents and overstates P02 and P03.**
Quoted: model_assumptions.md:49-50 "P01, P08, P09, P02, P03, P06 and P31 are closed and are known only
from their abstracts"; docs/02:23 "Read at abstract level only: P01 (IOP page), P08, P09, P31, P05
(PubMed)"; docs/00:102 "the paywalled papers (P01, P02, P03, P08, P31, P06)". Evidence: L5 section 1:
P02 "no (the abstract was seen only through the WebFetch summariser and is not counted)"; P03 "no"
(L4 3.3: P03 classified from the title only); P06 "abstract read, +ABSTRACT(PubMed)"; P09 is paywalled
and unread (L5 2.2). (The model_assumptions wording copies L5's own proposal 6.1, which contradicts L5's
table.) Proposed wording (model_assumptions): "P01, P06, P08, P09 and P31 are closed and known only from
their abstracts; P02 and P03 are closed and known from their metadata only"; add P06 to docs/02:23 and
P09 to docs/00:102.

**m4. Rows of docs/07 left from revision 1/2 contradict the Phase 1 record.**
Quoted: docs/07:16 "P02, P02E | ... | paywalled (APS); abstract readable | same items for GaAs(110);
what the erratum corrects"; docs/07:17 "P03 | ... | paywalled (Elsevier); abstract readable";
docs/07:19 "P05 | ... | paywalled (Elsevier); check OSTI or eScholarship"; docs/07:67-68 step 4
"Request uploads, in this order: P01, P08, P02 with P02E, ..., P06, C03, B10 ch. 7"; docs/07:60
"Details and current labels: `docs/agent_reports/B_literature.md`". Evidence: L5 2.4 (P02E free and
read in full: "This is the whole correction"); L5 section 1 (P02 abstract not counted; P05 "OPEN
(publisher, CC BY 4.0) but NOT RETRIEVABLE"; OSTI holds a citation only); L4 3.1 (no abstract for P03 in
any API record); current labels are in `references.bib` (B3 pass 2). The new upload list (docs/07:88-105)
is right, so the document contradicts itself. Proposed wording: P02/P02E row "P02 paywalled (APS), no
abstract read; P02E read in full (only reprints Fig. 3)"; P03 "paywalled; no abstract in any API
record"; P05 "open access (CC BY 4.0), not retrievable by automated clients: browser download";
step 4: "superseded by the upload list under 'Status after Phase 1'"; line 60: "current labels:
`docs/references.bib` (B3)".

**m5. The post-1993 answer is stronger in docs/00 than in docs/02 and L4.**
Quoted: docs/00:83-85 "After 1993 the citation graph shows reflection electron holography only by the
Tokyo Institute of Technology group (Si(111)7x7, 2001 to 2003, both waves reflected)". Evidence: L4 5.1
"yes, at least by one group"; docs/02:62-66 adds "This is an absence in the databases and queries
named, not proof of absence; the Japanese databases are the most likely place for more work". Proposed
wording: "The citation graph and the searches of L4 found post-1993 reflection interferometry by one
group only, the Tokyo Institute of Technology (Si(111)7x7, 2001 to 2003); the Japanese databases were
not searched, so this is an absence in the sources searched, not proof of absence."

**m6. docs/07 "Status after Phase 1", item 1 (the eleven identifier substitutions): decision
justified, stated justification incomplete and one factual claim wrong.** Quoted: docs/07:74-78
"Eleven records were accepted with an identifier ... standing in for a field the entry lacked; the
orchestrator keeps them, because a PII or ISBN match with the title, container and year identifies the
record more strictly than the volume would, and each is marked 'accepted by identifier substitution'
in its note. New records added in the second pass follow the strict rule." Evidence: B3 Method 3 and
per-entry records. (a) The rationale covers the eight PII/ISBN cases (U01, U02, U08, U09, U10 by PII;
B03, B04 by ISBN; U07 by parent ISBN and exact title) but not the three first-page cases, where the
first page stands in for a placeholder TITLE (U04, HANADA95) or for the missing AUTHOR (U16), not for a
volume. (b) Only six notes (U01, U02, U07, U08, U09, U10) contain "accepted by identifier
substitution"; U04, U16 and HANADA95 say "accepted with the first page standing in for ..."; B03 and
B04 say only "edited-book record matched by ISBN" and do not disclose the relaxed rule. (c) HYTCH10, added
in pass 1 at the coordinator's request, was also accepted by substitution ("the article number standing
in for the title"), so twelve verified entries rest on substitution. (d) The count 11 is printed by
`report --pass 1`, not by the default `report` cited at docs/07:73-74, and `report --pass 1` no longer
regenerates the committed pass-1 block byte for byte (Section 2).
Verdict (check 5): KEEP. Every one of the twelve rests on a unique identifier (PII, ISBN, or journal +
volume + first page, a unique citation key), no tested field mismatched, and every competing candidate
in the per-entry tables is rejected on several fields. The acceptance identifies the record; it does
not show that the content B_literature.md attributed to the entry belongs to it (B3 notes two closer
McCoy-Maksym papers for U01), which is why these entries must not be used for content without reading.
Proposed wording: "Twelve records were accepted with an identifier the entry already carried standing
in for a missing field: eight by ScienceDirect PII or ISBN (U01, U02, U07-U10, B03, B04), three by
journal, volume and first page (U04, HANADA95 for a placeholder title; U16 for the missing author) and
HYTCH10 by article number (pass 1, at the coordinator's request). Each is a unique identifier and no
tested field mismatched, so the orchestrator keeps them; the notes say 'accepted by identifier
substitution' (U01, U02, U07-U10), 'first page standing in' (U04, U16, HANADA95), 'article number
standing in' (HYTCH10) or 'matched by ISBN' (B03, B04). Count: `crossref_check.py report --pass 1`.
Acceptance establishes identity only, not the content attributed to the entry in B_literature.md."

**m7. Item 11 loses its "(blocking)" flag on a criterion that is not the file's definition; item 12
repeats itself.** Quoted: docs/06:26 "Still to be supplied: miscut angle and direction, typical
terrace widths (no longer blocking for the choice of configuration, which is CFG-B)"; docs/06:6 "Items
marked (blocking) prevent a quantitative comparison with experiment"; docs/06:27 "... ion-milling
parameters (ion, energy, angle), expected amorphous damage-layer thickness, any annealing. Surface
preparation state: native oxide, HF-last, UHV flash, ion-milling parameters, expected amorphous
damage-layer thickness, any annealing." Evidence: the choice of configuration is not the criterion;
step spacing (terrace width) and miscut still fix how many steps lie in a hologram and their
orientation to the beam. No default replaces the inputs (they remain "still to be supplied"), so this is
not a silent substitution (check 6), but the blocking count (seven, docs/00:90) depends on it.
Proposed wording: either keep "(blocking)" on item 11 (then eight blocking items in docs/00), or write
"(not blocking: they do not enter a single-step height comparison; they do enter step-density
comparisons)"; delete the second list in item 12.

**m8. "six OpenAlex search queries".** Quoted: docs/02:30 "six OpenAlex search queries failed on the
rate limit (L4 section 4.5)"; docs/02:133-134 and docs/07:114 "an OpenAlex API key to rerun the six
rate-limited searches"; docs/02:62-63 "Nothing after 2003 ... was found in OpenAlex, ... with the
queries recorded in L4 section 4". Evidence: L4 4.1 "All 5 OpenAlex queries were NOT RUN"; L4 4.5
lists q01-q03, q16, q28 (OpenAlex) and q09 (Semantic Scholar relevance); the cache has no file for any
of the six. OpenAlex contributed only through the citation-graph reverse check. Proposed wording:
"five OpenAlex topic queries and one Semantic Scholar relevance query failed on rate limits (L4 4.5);
OpenAlex was used only for the citation graph"; "an OpenAlex API key to rerun the five OpenAlex
queries".

**m9. Four of the nine post-2003 citing works are classified from the title only.** Quoted:
docs/02:64-65 "The nine citing works after 2003 are reviews, transmission holography, one REM
encyclopedia entry and three unrelated papers." Evidence: `L4_citing_works.tsv`, evidence column:
Jiang 2013, Cowley 2015 (the encyclopedia entry), Dunin-Borkowski 2019 (= C02) and "Notes and
References" 2022 are "UNVERIFIED classification (title only)". C02 has a section 16.6 "Alternative Forms
of Electron Holography" (L3), unread. Proposed wording: add "(four of the nine classified from the title
only, UNVERIFIED)".

**m10. Test range of milestone M1 differs between docs/00 and docs/05.** Quoted: docs/00:119 "Build
milestone M1 (geometry and quantification core, tests T1 to T25 and the shadow-length test)";
docs/05:302 "M1 Physics core | ... tests T1 to T23 and the shadow-length test"; docs/05:304 "M3
Holography chain | ... T24/T25". Proposed wording: docs/00:119 "tests T1 to T23 and the shadow-length
test (T24, T25 belong to M3)".

**m11. A measured Si value is attributed to a paper whose Si content is unverified.** Quoted:
docs/02:127-128 "Measured silicon values (Kruse et al. 2006, Gajdardziska-Josifovska et al. 1993, Wang
et al. 1997) are closed." Evidence: L5 4, M3: "whether Si is among the crystals is UNVERIFIED"; M2 (Kruse
2006) is "DFT slab and holography comparison" whose abstract gives no number. Proposed wording:
"Candidate measured values (Kruse et al. 2006, DFT and holography; Wang et al. 1997, Si nanospheres;
Gajdardziska-Josifovska et al. 1993, crystal wedges, Si not confirmed) are closed."

**m12. A DOI is given for a record the bibliography keeps UNVERIFIED without a DOI.** Quoted:
docs/07:110-111 "18 Takeguchi, Harada and Shimizu, J. Electron Microsc. (1990),
doi:10.1093/oxfordjournals.jmicro.a050815"; docs/02:42 "METADATA_VERIFIED where Crossref is complete
(L4 section 6.2)". Evidence: the DOI is in L4 6.2 (so it is sourced), but B3 pass 2 put TAKEGUCHI1990
in the UNVERIFIED section with no DOI ("no Crossref record passed the acceptance test"; the record has no
authors, volume or pages). Proposed wording: "doi:10.1093/oxfordjournals.jmicro.a050815 (per L4; the
Crossref record lacks authors, volume and pages, so references.bib keeps TAKEGUCHI1990 UNVERIFIED)";
in docs/02:42 add "Takeguchi 1990: UNVERIFIED in references.bib".

**m13. B05's year drops a fact that L3 read.** Quoted: docs/07:39 "Rose, Geometrical Charged-Particle
Optics, 2nd ed., 2012 (Crossref; revision 1 gave 2012/2013)". Evidence: L3 B05 read the Springer page:
"Copyright information: Springer-Verlag Berlin Heidelberg 2012"; hardcover "Published: 03 February
2013", eBook "02 February 2013"; B3 Limitations says "the 2012 year rests on the Crossref deposit alone
(Springer page not readable)", which L3 contradicts. Proposed wording: "2012 (Crossref published-print
and copyright year; the Springer page gives publication on 2-3 February 2013, L3)".

**m14. An undefined abstract label.** Quoted: docs/02:53 "(`+ABSTRACT`: energy-filtered interferometry
in REM geometry, ...)". Evidence: docs/02:8-11 and README define only `+ABSTRACT(publisher)` and
`+ABSTRACT(PubMed)`; L4 labels this "SECTION_READ (abstract only), Crossref record". Proposed wording:
"(abstract only, Crossref record: ...)"; use the same form for Osakabe 1989 EMSA, Takeguchi 1990
(OpenAlex record) and Senhorst 2026 (OpenAlex record).

**m15. Revision-2 labels survive in two source-map rows next to the revision-3 labels.** Quoted: SM03
source_id "P08 (Osakabe 1992, abstract-index level: geometrical path differences measured in units of
wavelength)" while its evidence column says "P08 abstract read on PubMed (+ABSTRACT(PubMed))"; SM14
source_id "P18, P19, P17, P20, P21 (index-level records)" while its evidence says "METADATA_VERIFIED
(Crossref, report B3 ...)". Proposed wording: SM03 "P08 (Osakabe 1992, +ABSTRACT(PubMed), sentences
2-3)"; SM14 "P18, P19, P17, P20, P21 (Crossref records, B3)".

### Nit

* **N1.** docs/02:48-49: "32 classified from an abstract and 28 from the title only" counts the 60
  records, not the 57 distinct works. Write "of the 60 records, 32 ... and 28 ...".
* **N2.** docs/02:39: P08 "sentences 2 and 3: ... a monatomic-step phase and a dislocation displacement
  field observed" - the last item is the abstract's last sentence (L5 2.2). Write "sentences 2-3 and
  the last sentence".
* **N3.** docs/02:115 "P04 (read) prints the paraxial propagator" and SM08 "Eq. (1), p. 2, for the
  paraxial equation": P04 does not use the word; "paraxial" is L2 inference A-I1 (DERIVED_HERE). Write
  "prints the propagator `exp(-i pi lambda |q|^2 t)` (Eq. (3); paraxial by inference, L2 A-I1)".
* **N4.** docs/07:108 "the only post-1993 reflection interferometry paper with a stated specimen":
  Tanishiro 2003 names Si(111) 7x7 in its Fig. 1 caption and "clean silicon surfaces" in its abstract
  (L4 5.1). Write "the post-1993 reflection interferometry paper with the most complete abstract".
* **N5.** SM04, SM12, SM14, SM15: the new SECTION_READ locators (arXiv:2607.05948v1 Fig. 2c, p. 3;
  P07 para 56; P49 sec. 2.2, Eqs. (14)-(28); P04 p. 3) sit in `source_id`, while `locator_inspected`
  still holds only the old C/D locators. Copy them into `locator_inspected`.
* **N6.** `tools/phase1_numbers.py`:4-5 "Every number that the Phase 1 synthesis adds to docs/ is
  printed by this script": the L4 and B3 counts are not. Its four checks assert two angles and two
  signs but none of the three values the documents quote (0.049 A/V, -0.178 rad, -0.128 rad); add
  checks at +-0.001. The printed "-0.0492 A per volt of underestimate" is a secant over 0.53 V, while
  docs/03 describes the derivative with respect to the assumed V0 (0.0490 A/V); equal to two figures.
* **N7.** docs/03:117-118 (not in the diff): "see the calculator output section 5" for Si(001); the
  Si(001) rod is section 4b of `C_calculator_output.txt`, section 5 is the V0 sensitivity.
* **N8.** docs/02:15 "checked against Crossref, DataCite, arXiv or the patent office": software and web
  records were checked on project pages, READMEs and a vendor page, and PAT01 and U03 on Google Patents
  (B3 Method 4). Write "... arXiv, a patent record or the project's own page".
* **N9.** docs/02:72 "Every electron-ptychography abstract read is in transmission": the Shpiro et al.
  2025 abstract was read and states no geometry (L4 4.2, UNVERIFIED). Add "(one abstract read states no
  geometry)".
* **N10.** docs/02:25 "Closed here (landing pages checked, L5 section 1)": for P08 and P09 (Wiley,
  Cloudflare 403 to curl and WebFetch) the host page itself was unreadable; the closed verdict comes
  from OpenAlex, Semantic Scholar and Europe PMC. Write "(publisher pages or, where unreadable, the
  indices; L5 section 1)".
* **N11.** docs/04 new row: "(P04 p. 3, Eqs. (3), (6); prismatique docs)": Eq. (3) is the propagator,
  not one of the four facts; periodic boundaries are P04 p. 4 and S01 sec. 2.3.1 (L2 E19). Use
  "P04 p. 3, Eq. (6), p. 4; S01 2.3.1, 2.6.18, 2.10.3".
* **N12.** B1 and SM04: "-0.128 rad" for the a/2 step at (0,0,8) is the change of `|Delta_phi|` (or of
  its value in [0, 2 pi)); the principal value of the signed phase moves by +0.128 rad (Section 1).
  Add "(|Delta_phi|; the principal value moves the other way)".
* **N13.** docs/07 upload list versus L3: L3's "Book items ... NOT in the step-4 list (upload later)"
  (B09 ch. 13; B03 ch. 58, 63, 65-66; B04 ch. 71, 74, 78; B11 ch. 4, 6.2; B13; B15) appear only in the
  book table, and upload item 6 (B08) omits the RHEED-routine appendix (one of App. A-D, pp. 470-500)
  that L3's row 6 lists. Add one line: "later uploads: the book-table locators of L3's second table".
* **N14.** docs/07:30-31 "B01 and B08 rest on OUP's Crossref deposit": B01's chapter numbers come from
  a model-mediated WebFetch of the OUP product page (L3 B01, route 2, flagged there).
* **N15.** docs/05:31 acceptance criterion 3 "on the configuration Ali specifies (CFG-A or CFG-B)":
  Ali has now specified Si(001); write "CFG-B (Ali's Si(001)); CFG-A as the translation-step validation
  case".
* **N16.** SM18 "prismatique 0.0.1 requires embeam 0.0.1 to 0.0.3": L2 B-V4 finds that the simulation
  path (`tilt.series`, `hrtem.sim`) does not call `step_size`; the requirement is for `tilt.step_size`
  and `tilt_test.py`. Write "prismatique 0.0.1's `tilt.step_size` requires embeam 0.0.1 to 0.0.3".
* **N17.** README "Reproduce" block lists only the two physics scripts. The revision-3 counts come
  from `venv/bin/python tools/lit/citation_lists.py build --list` (offline) and
  `venv/bin/python tools/bib/crossref_check.py report [--pass 1]`; both rewrite files under
  `docs/agent_reports/` (TSV, generated log blocks), which the README should say.

## 4. Check 6: PROJECT_INPUT replaced by a default

None found in the diff. `tools/phase1_numbers.py` labels 200 keV as PROJECT_INPUT and 12.0 V as
ASSUMPTION; the CFG-O row makes every unlisted field fail on load; docs/05 section 5 item 3 and B5 make
the R1 aperture treatment a declared choice; docs/06 items 11 and 12 keep the missing parts "still to
be supplied". The one change of status is the dropped "(blocking)" on item 11 (m7). Outside the diff,
the CFG-B row (docs/05:58) still names "(008) as the working condition" without saying that the order
is PROJECT_INPUT item 9; mark it "(proposed; item 9)".

## 5. Verified as correct

Physics and scripts
* theta_ext, |Delta_phi| and their 12.0 -> 12.53 V changes for (4,-4,4)/d_111, (0,0,8)/(a/2) and
  (0,0,12)/(a/2): my values equal `tools/phase1_numbers.py` to every printed digit; "-0.178 rad" and
  "-0.128 rad" (B1, SM04) are right in the documents' convention.
* The sign reversal of the height bias (docs/03, docs/06 item 20, B1): correct under premise A; the
  value 0.049 A/V for a bilayer at (4,-4,4) is correct (M1 asks for the premise and the scaling).
* Unchanged numbers re-checked: -0.34 and -0.20 rad/V, -0.21 and -0.13 mrad/V (docs/03, B1, SM04,
  docs/06, docs/00); CFG-B (008) theta_int 18.5, theta_ext 16.5 mrad, wrap 0.76 A, 61x; (004) exits at
  3.9 mrad; theta_c 8.356 mrad; the docs/03 table rows (3,-3,3) to (8,-8,8); shadows 230 A and 102 A per
  bilayer, 444 nm and 733 nm for 10 nm; 0.020 mrad convergence for 1 rad at 10 nm; 50 nm path through
  1 nm at 20 mrad; 2 theta_ext = 17 to 62 mrad.
* `tools/phase1_numbers.py`: 4/4 checks pass; its premise (docstring lines 15-17) is premise A; (0,0,8)
  and (0,0,12) are built correctly as orders 2 and 3 of d = a/4. `tools/reflection_step_phase_calculator.py`:
  25/25.

Counts
* 60 records, 57 distinct works, 32/28, 9 after 2003 (citation_lists.py build, offline); zero-hit
  searches q18, q19, q21, q26 (cache); 11 substituted acceptances (report --pass 1); pass-2 totals
  132/125/7/114 (report, regenerated byte-identical); seven blocking items; 22 items.

Evidence labels and locators
* CFG-O row (docs/05:59): every field traces to L5 2.1 and L5 3 with the right sentence (Pt(111) and
  glancing incidence sentence 2, optical reconstruction sentence 3, "of the order of 0.01 nm" and
  monatomic steps sentence 4), the R2 reading is labelled DERIVED_HERE, and unlisted fields fail on load.
* SM03 (apart from m15), SM19, SM20, SM21, SM22, SM23, SM24 (apart from the "only" of M2), SM25: every
  locator exists in the report cited (L1 3.1-3.2 and 4.1-4.3, L2 D9/D19/D19b/D-I3, C1-C4/E25/E26, L5
  2.4-2.6); statements of one source about another stay UNVERIFIED: PAT01 about P01 (docs/02:37,
  SM22), P07 about P01/P02 (SM03 uses P07 only for the geometric-path premise), C03 about P06 (SM24),
  Hytch 2010 versus P31 (docs/02:102-103, SM03, docs/07:101).
* docs/04 new rows: all locators exist in L2 (B23, B24, B-V1 to B-V4, C3, C4, B22, E4, E7, E10, E16,
  E19, E23, E25, E26, E30).
* SM08, SM10a, SM10b, SM11a, SM11c, SM15, SM17, SM18: locators exist in L2 (A3, A8, A22, B1, B2, B4, B8,
  B14, E11) and L5 4 (V96.out).

Bibliographic claims (all found in the reports, the caches or references.bib)
* P01: authors, JJAP 27 (9A) L1772 (1988), doi:10.1143/JJAP.27.L1772; abstract sentences 1-4 as quoted.
* PAT01: Osakabe and Tonomura only; filed 1990-01-10, JP priority 1989-01-13, issued 1991-03-12;
  Eq. (1) `d = Cs alpha^3 - Delta f alpha`; two embodiments; col. 1 l. 13-33, l. 36-41; Eq. (2)
  defective in US and EP prints; 100 kV only in a worked example; five inventors and 1991/1993 dates
  belong to US 5,192,867 (L1 PAT-1 to PAT-27, section 6). Consistent in docs/00, docs/02, SM21, B5.
* P02/P02E: five authors, PRL 62, 2969-2972, erratum PRL 63, 584; erratum only reprints Fig. 3 (GaAs(110),
  (880), foreshortening 28). Apart from docs/07:16 ("what the erratum corrects", m4), no summary
  document still asks for P02E to be re-checked; references.bib withdrew the warning (B3 pass 2).
* P08 457-462, P09 450-456 (Microsc. Res. Tech. 20(4)); P03 475-481, doi:10.1016/0304-3991(93)90123-F;
  P31 doi and pages; P05, P06, C01, C02 DOIs and pages; Kruse 2006 and Wang 1997 DOIs; Suzuki 2001,
  Tanishiro 2003, Herring 1995, Osakabe 1989 EMSA, Osakabe 1993 (two), Senhorst 2026, Blackburn 2025,
  Zhu, Jørgensen, Myint, Guenzing, Godard, Hruszkewycz; P49 CPC 296, 109029 (2024); Pryor et al. 2017,
  Adv. Struct. Chem. Imaging 3, 15.
* Book locators of docs/07 (B01-B15, C01-C03) and the upload list 1-14: all equal L3's tables and L5
  section 5, including "pp. 268-279" (B09 ch. 12 sec. 2-4) and "p. 83-84" (B10 sec. 7.2), which are in
  L3's upload table.
* MIP preprint: 12.53 V as the Fig. 2c fit intercept, WIEN2k GGA, innermost monolayer, no uncertainty
  (L5 4); Pennington 2015 and Auslender 2024 abstract quotations (L5 4).
* C03: sec. 3.4 Eq. (2) AM p. 18, Eq. (6) p. 19, sec. 9.1 Eq. (9) p. 88, sec. 6.2 p. 76 (verbatim
  quotation correct), sec. 5.9 p. 66; Hytch 2010 sec. 2 Eqs. (1), (3), (4) and the sign
  `phi_g^G = -2 pi g.u` with `exp(+2 pi i g.r)`.
* PAT02 key reassignment: documented identically in docs/02:17-18, references.bib PAT02 and U03 notes and
  the B3 pass-2 log; no summary document uses PAT02 in the old sense.
* The P01 surface (Pt(111)) is the same in README, docs/00, docs/02, docs/05, model_assumptions and
  SM22; the vacuum ("direct") reference is attributed to PAT01, not to P01, everywhere in the diff; no
  summary still says "index-level only" or "no reflection electron holography since 1993" except
  docs/05 section 10 (M3) and two source-map `source_id` cells (m15); the "nine of them blocking" of revision 2 is replaced consistently by seven.
* "Tokyo Institute of Technology" (docs/00, docs/02): the affiliation is carried by the cached OpenAlex
  records (`citation_cache/`), although L4 gives no locator for it.

## Appendix A. Recomputation script (`e3_recompute.py`, kept in the session scratchpad; run with `venv/bin/python`)

```python
"""E3 independent recomputation (written without reading tools/phase1_numbers.py or the
calculator's implementation of these quantities).

Premises (stated, not taken from the repository code):
  * CODATA 2018 / SI-2019 exact constants; m_e c^2 = 510998.950 eV.
  * 200 keV kinetic energy T.
  * Inside the crystal K^2 = k^2 + U0, U0 = [2 e V0 (T + m c^2) + (e V0)^2] / (hbar c)^2 (exact
    relativistic energy conservation); the docs drop the (e V0)^2 term, shown here to be negligible.
  * Specular reflection from planes parallel to the surface; internal Bragg condition K_z = g/2;
    parallel wavevector conserved, so k_z(ext) = sqrt(g^2/4 - U0), theta_ext = asin(k_z/k).
  * Step phase between translation-related terraces: Delta_phi = -(k_out - k_in).R = -2 k_z h
    (vacuum wavelength, external angle). |Delta_phi| below = 2 k_z h (unwrapped magnitude).
  * a = 5.4309 A; (4,-4,4) with h = d_111 = a/sqrt(3); (0,0,8), (0,0,12) with h = a/2.
Height-inference premises:
  A: fixed measured (unwrapped, correct-branch) phase; theta_ext NOT measured but computed from the
     internal Bragg condition with the ASSUMED V0: h_inf = |phi| / (2 k_z(V0_assumed)).
  B: theta_ext measured independently: h_inf = |phi| / (2 k sin(theta_meas)); V0 does not enter.
  C: (for contrast only) the wrapped phase read as the refractive departure (g - 2 k_z) h, i.e.
     h_inf = phi_dep / (g - 2 k_z(V0_assumed)); only meaningful for lattice-translation steps.
"""
import numpy as np

h_pl = 6.62607015e-34
hbar = h_pl / (2 * np.pi)
e = 1.602176634e-19
c = 299792458.0
mc2_eV = 510998.950
a = 5.4309  # A

T = 200e3  # eV
gamma = 1 + T / mc2_eV
hbar_c_eVA = hbar * c / e * 1e10  # eV*A
k = np.sqrt(T * (T + 2 * mc2_eV)) / hbar_c_eVA  # 1/A
lam = 2 * np.pi / k


def U0(V0, exact=True):
    q = 2 * V0 * (T + mc2_eV) + (V0 ** 2 if exact else 0.0)
    return q / hbar_c_eVA ** 2  # 1/A^2


dU0dV = 2 * (T + mc2_eV) / hbar_c_eVA ** 2

refl = {
    "(4,-4,4)": (2 * np.pi * np.sqrt(48) / a, a / np.sqrt(3)),
    "(0,0,8)": (2 * np.pi * 8 / a, a / 2),
    "(0,0,12)": (2 * np.pi * 12 / a, a / 2),
    "(6,-6,6)": (2 * np.pi * np.sqrt(108) / a, a / np.sqrt(3)),
    "(3,-3,3)": (2 * np.pi * np.sqrt(27) / a, a / np.sqrt(3)),
    "(8,-8,8)": (2 * np.pi * np.sqrt(192) / a, a / np.sqrt(3)),
    "(0,0,4)": (2 * np.pi * 4 / a, a / 2),
}


def kz(g, V0, exact=True):
    return np.sqrt(g ** 2 / 4 - U0(V0, exact))


def th_ext(g, V0, exact=True):
    return np.arcsin(kz(g, V0, exact) / k)


def th_int(g, V0, exact=True):
    K = np.sqrt(k ** 2 + U0(V0, exact))
    return np.arcsin(g / 2 / K)


def wrap0(x):  # [0, 2pi)
    return np.mod(x, 2 * np.pi)


def wrapc(x):  # (-pi, pi]
    y = np.mod(x + np.pi, 2 * np.pi) - np.pi
    return y


print(f"T = {T/1e3:.0f} keV, gamma = {gamma:.6f}, lambda = {lam:.6f} A, k = {k:.4f} 1/A")
print(f"dU0/dV0 = {dU0dV:.6f} A^-2/V; U0(12.0) = {U0(12.0):.6f} (docs form {U0(12.0, False):.6f})")
print(f"Delta(12 V) = U0/k^2 = {U0(12.0, False)/k**2:.4e}; theta_c = asin(sqrt(D/(1+D))) = "
      f"{1e3*np.arcsin(np.sqrt((U0(12.0,False)/k**2)/(1+U0(12.0,False)/k**2))):.4f} mrad")
print()
hdr = ("refl", "h(A)", "V0", "th_int", "th_ext", "|dphi|", "mod2pi", "(-pi,pi]", "h_2pi", "1/sin")
print("%-9s %7s %6s %8s %8s %9s %8s %9s %7s %6s" % hdr)
for name, (g, hstep) in refl.items():
    for V0 in (12.0, 12.53):
        kzz = kz(g, V0)
        ph = 2 * kzz * hstep
        print("%-9s %7.4f %6.2f %8.4f %8.4f %9.5f %8.5f %9.5f %7.4f %6.1f" % (
            name, hstep, V0, 1e3 * th_int(g, V0), 1e3 * th_ext(g, V0), ph, wrap0(ph),
            wrapc(-ph), np.pi / kzz, 1 / np.sin(th_ext(g, V0))))
print()
print("Change 12.0 V -> 12.53 V (unwrapped |dphi| = 2 k_z h; the wrapped -2 k_z h moves by the "
      "opposite amount)")
for name in ("(4,-4,4)", "(0,0,8)", "(0,0,12)"):
    g, hstep = refl[name]
    d_ph = 2 * hstep * (kz(g, 12.53) - kz(g, 12.0))
    d_th = 1e3 * (th_ext(g, 12.53) - th_ext(g, 12.0))
    w0 = wrapc(-2 * kz(g, 12.0) * hstep)
    w1 = wrapc(-2 * kz(g, 12.53) * hstep)
    print(f"  {name:9s} d|dphi| = {d_ph:+.4f} rad; d theta_ext = {d_th:+.4f} mrad; "
          f"wrapped -2k_z h (-pi,pi]: {w0:+.4f} -> {w1:+.4f}; |wrapped| change {abs(w1)-abs(w0):+.4f}")
print()
print("Derivatives at V0 = 12.0 V (analytic):")
for name in ("(4,-4,4)", "(6,-6,6)", "(0,0,8)", "(0,0,12)"):
    g, hstep = refl[name]
    kzz = kz(g, 12.0)
    dph = -hstep * dU0dV / kzz               # d(2 k_z h)/dV0
    dth = -dU0dV / (2 * kzz) / (k * np.cos(th_ext(g, 12.0)))
    dhA = hstep * dU0dV / (2 * kzz ** 2)      # premise A, d h_inf / d V0_assumed
    dep = g - 2 * kzz
    dhC = -hstep * (dU0dV / kzz) / dep        # premise C
    print(f"  {name:9s} d|dphi|/dV0 = {dph:+.4f} rad/V; dtheta_ext/dV0 = {1e3*dth:+.4f} mrad/V; "
          f"A: dh_inf/dV0_ass = {dhA:+.5f} A/V ({100*dhA/hstep:+.3f} %/V); C: {dhC:+.4f} A/V")
print()
print("Premise A, finite differences at (4,-4,4), h_true = d_111, V0_true = 12.0 V:")
g, hstep = refl["(4,-4,4)"]
phi_true = 2 * kz(g, 12.0) * hstep
for Vass in (11.0, 11.47, 12.0, 12.53, 13.0):
    hinf = phi_true / (2 * kz(g, Vass))
    print(f"  V0_assumed = {Vass:5.2f} V: h_inf = {hinf:.5f} A, bias = {hinf-hstep:+.5f} A")
print("  -> underestimating V0 by 1 V (assumed 11 V, true 12 V) gives h_inf - h = "
      f"{phi_true/(2*kz(g,11.0)) - hstep:+.5f} A (too SMALL)")
print("Premise A with V0_true varied, V0_assumed = 12.0 V:")
for Vtrue in (12.53, 13.0):
    phi = 2 * kz(g, Vtrue) * hstep
    hinf = phi / (2 * kz(g, 12.0))
    print(f"  V0_true = {Vtrue:5.2f} V (assumed 12.0 V, i.e. underestimated by {Vtrue-12:.2f} V): "
          f"bias = {hinf-hstep:+.5f} A ({(hinf-hstep)/(Vtrue-12):+.5f} A per volt of underestimate)")
print("Premise B (angle measured): bias = 0 for any V0 error (V0 does not enter -2 k h sin(theta_ext)).")
print()
print("Other numbers quoted in the docs:")
g8, h8 = refl["(0,0,8)"]
print(f"  (0,0,8): theta_int {1e3*th_int(g8,12.0):.3f} mrad, theta_ext {1e3*th_ext(g8,12.0):.3f} mrad, "
      f"wrap {np.pi/kz(g8,12.0):.4f} A, foreshortening {1/np.sin(th_ext(g8,12.0)):.1f}")
g4, _ = refl["(0,0,4)"]
arg = g4 ** 2 / 4 - U0(12.0)
print(f"  (0,0,4): k_z^2 = {arg:.4f}; theta_ext = {1e3*np.arcsin(np.sqrt(arg)/k):.3f} mrad")
g3, h3 = refl["(3,-3,3)"]
print(f"  (3,-3,3): theta_ext {1e3*th_ext(g3,12.0):.3f} mrad, 1/sin {1/np.sin(th_ext(g3,12.0)):.1f}")
for name in ("(4,-4,4)", "(8,-8,8)"):
    gg, hh = refl[name]
    print(f"  shadow per bilayer at {name}: {hh/np.tan(th_ext(gg,12.0)):.1f} A")
print(f"  10 nm shadow at 22.5 mrad: {100/np.tan(22.5e-3)/10:.1f} nm; at (4,-4,4) angle: "
      f"{100/np.tan(th_ext(refl['(4,-4,4)'][0],12.0))/10:.1f} nm")
print(f"  convergence for 1 rad spread, 10 nm step at 22.5 mrad: "
      f"{1e3/(4*np.pi*100/lam*np.cos(22.5e-3)):.4f} mrad")
print(f"  1 nm overlayer path at 20 mrad: {1/np.sin(20e-3):.1f} nm one way")
print(f"  effect of the (e V0)^2 term on theta_ext(4,-4,4): "
      f"{1e3*(th_ext(refl['(4,-4,4)'][0],12.0,True)-th_ext(refl['(4,-4,4)'][0],12.0,False)):+.2e} mrad")
```

## Appendix B. Output of `e3_recompute.py` (2026-09-22)

```
T = 200 keV, gamma = 1.391390, lambda = 0.025079 A, k = 250.5323 1/A
dU0/dV0 = 0.365196 A^-2/V; U0(12.0) = 4.382389 (docs form 4.382352)
Delta(12 V) = U0/k^2 = 6.9820e-05; theta_c = asin(sqrt(D/(1+D))) = 8.3556 mrad

refl         h(A)     V0   th_int   th_ext    |dphi|   mod2pi  (-pi,pi]   h_2pi  1/sin
(4,-4,4)   3.1355  12.00  15.9970  13.6415  21.43156  2.58201  -2.58201  0.9193   73.3
(4,-4,4)   3.1355  12.53  15.9970  13.5280  21.25323  2.40368  -2.40368  0.9270   73.9
(0,0,8)    2.7155  12.00  18.4720  16.4743  22.41423  3.56467   2.71851  0.7612   60.7
(0,0,8)    2.7155  12.53  18.4720  16.3805  22.28651  3.43696   2.84623  0.7656   61.1
(0,0,12)   2.7155  12.00  27.7100  26.4205  35.94393  4.52800   1.75518  0.4747   37.9
(0,0,12)   2.7155  12.53  27.7099  26.3620  35.86443  4.44850   1.83469  0.4757   37.9
(6,-6,6)   3.1355  12.00  23.9968  22.4953  35.33950  3.92357   2.35961  0.5575   44.5
(6,-6,6)   3.1355  12.53  23.9967  22.4266  35.23164  3.81571   2.46747  0.5592   44.6
(3,-3,3)   3.1355  12.00  11.9975   8.6096  13.52638  0.96001  -0.96001  1.4565  116.2
(3,-3,3)   3.1355  12.53  11.9975   8.4286  13.24202  0.67565  -0.67565  1.4878  118.6
(8,-8,8)   3.1355  12.00  31.9981  30.8882  48.52088  4.53858   1.74460  0.4060   32.4
(8,-8,8)   3.1355  12.53  31.9980  30.8382  48.44238  4.46008   1.82310  0.4067   32.4
(0,0,4)    2.7155  12.00   9.2356   3.9344   5.35318  5.35318   0.93001  3.1872  254.2
(0,0,4)    2.7155  12.53   9.2356   3.5207   4.79037  4.79037   1.49282  3.5617  284.0

Change 12.0 V -> 12.53 V (unwrapped |dphi| = 2 k_z h; the wrapped -2 k_z h moves by the opposite amount)
  (4,-4,4)  d|dphi| = -0.1783 rad; d theta_ext = -0.1135 mrad; wrapped -2k_z h (-pi,pi]: -2.5820 -> -2.4037; |wrapped| change -0.1783
  (0,0,8)   d|dphi| = -0.1277 rad; d theta_ext = -0.0939 mrad; wrapped -2k_z h (-pi,pi]: +2.7185 -> +2.8462; |wrapped| change +0.1277
  (0,0,12)  d|dphi| = -0.0795 rad; d theta_ext = -0.0585 mrad; wrapped -2k_z h (-pi,pi]: +1.7552 -> +1.8347; |wrapped| change +0.0795

Derivatives at V0 = 12.0 V (analytic):
  (4,-4,4)  d|dphi|/dV0 = -0.3351 rad/V; dtheta_ext/dV0 = -0.2133 mrad/V; A: dh_inf/dV0_ass = +0.04902 A/V (+1.563 %/V); C: -0.2839 A/V
  (6,-6,6)  d|dphi|/dV0 = -0.2032 rad/V; dtheta_ext/dV0 = -0.1294 mrad/V; A: dh_inf/dV0_ass = +0.01803 A/V (+0.575 %/V); C: -0.2700 A/V
  (0,0,8)   d|dphi|/dV0 = -0.2403 rad/V; dtheta_ext/dV0 = -0.1766 mrad/V; A: dh_inf/dV0_ass = +0.02911 A/V (+1.072 %/V); C: -0.2400 A/V
  (0,0,12)  d|dphi|/dV0 = -0.1498 rad/V; dtheta_ext/dV0 = -0.1102 mrad/V; A: dh_inf/dV0_ass = +0.01132 A/V (+0.417 %/V); C: -0.2318 A/V

Premise A, finite differences at (4,-4,4), h_true = d_111, V0_true = 12.0 V:
  V0_assumed = 11.00 V: h_inf = 3.08763 A, bias = -0.04790 A
  V0_assumed = 11.47 V: h_inf = 3.10987 A, bias = -0.02566 A
  V0_assumed = 12.00 V: h_inf = 3.13553 A, bias = -0.00000 A
  V0_assumed = 12.53 V: h_inf = 3.16184 A, bias = +0.02631 A
  V0_assumed = 13.00 V: h_inf = 3.18573 A, bias = +0.05020 A
  -> underestimating V0 by 1 V (assumed 11 V, true 12 V) gives h_inf - h = -0.04790 A (too SMALL)
Premise A with V0_true varied, V0_assumed = 12.0 V:
  V0_true = 12.53 V (assumed 12.0 V, i.e. underestimated by 0.53 V): bias = -0.02609 A (-0.04923 A per volt of underestimate)
  V0_true = 13.00 V (assumed 12.0 V, i.e. underestimated by 1.00 V): bias = -0.04941 A (-0.04941 A per volt of underestimate)
Premise B (angle measured): bias = 0 for any V0 error (V0 does not enter -2 k h sin(theta_ext)).

Other numbers quoted in the docs:
  (0,0,8): theta_int 18.472 mrad, theta_ext 16.474 mrad, wrap 0.7612 A, foreshortening 60.7
  (0,0,4): k_z^2 = 0.9716; theta_ext = 3.934 mrad
  (3,-3,3): theta_ext 8.610 mrad, 1/sin 116.2
  shadow per bilayer at (4,-4,4): 229.8 A
  shadow per bilayer at (8,-8,8): 101.5 A
  10 nm shadow at 22.5 mrad: 444.4 nm; at (4,-4,4) angle: 733.0 nm
  convergence for 1 rad spread, 10 nm step at 22.5 mrad: 0.0200 mrad
  1 nm overlayer path at 20 mrad: 50.0 nm one way
  effect of the (e V0)^2 term on theta_ext(4,-4,4): -2.16e-05 mrad
```

## Appendix C. Other commands run and their output

C.1 `venv/bin/python tools/phase1_numbers.py` (repository, read-only; run after Appendix B was produced):

```
================================================================================================
PHASE 1 NUMBERS (200 keV; V0 12.0 V ASSUMPTION versus 12.53 V DFT endpoint)
================================================================================================
Si(111) (4,-4,4), single-bilayer step h = d_111
   h = 3.1355 A;  theta_ext = 13.642 mrad (12.0 V), 13.528 mrad (12.53 V)
   |Delta_phi| = 21.4316 rad (12.0 V), 21.2532 rad (12.53 V); change = -0.1783 rad
   height inferred with 12.0 V when V0 is 12.53 V: bias h_inf - h = -0.0261 A  (-0.0492 A per volt of underestimate)
Si(001) (0,0,8), double-layer step h = a/2
   h = 2.7155 A;  theta_ext = 16.474 mrad (12.0 V), 16.380 mrad (12.53 V)
   |Delta_phi| = 22.4142 rad (12.0 V), 22.2865 rad (12.53 V); change = -0.1277 rad
   height inferred with 12.0 V when V0 is 12.53 V: bias h_inf - h = -0.0155 A  (-0.0292 A per volt of underestimate)
Si(001) (0,0,12), double-layer step h = a/2
   h = 2.7155 A;  theta_ext = 26.420 mrad (12.0 V), 26.362 mrad (12.53 V)
   |Delta_phi| = 35.9439 rad (12.0 V), 35.8644 rad (12.53 V); change = -0.0795 rad
   height inferred with 12.0 V when V0 is 12.53 V: bias h_inf - h = -0.0060 A  (-0.0113 A per volt of underestimate)
------------------------------------------------------------------------------------------------
   [PASS] theta_ext (4,-4,4) at 12.0 V [mrad]: 13.6415 (expected 13.64 +- 0.005)
   [PASS] theta_ext (0,0,8) at 12.0 V [mrad]: 16.4743 (expected 16.5 +- 0.05)
   [PASS] sign of dphi for V0 increase (must be < 0): 1.0000 (expected 1.0 +- 0.0)
   [PASS] sign of bias for underestimated V0 (must be < 0): 1.0000 (expected 1.0 +- 0.0)
   4/4 checks pass
```

C.2 `venv/bin/python tools/bib/crossref_check.py report` (scratch copy of the repository; the regenerated pass-2 block and TSV were byte-identical to the committed ones):

```
TAKEGUCHI1990: added to the UNVERIFIED section (no Crossref record passed the acceptance test (see search candidates))
SCHOWALTER05: added to the UNVERIFIED section (ACCEPT-SUBSTITUTED(Y<-P) {"A": "match", "T": "match", "T_ratio": 1.0, "C": "match", "Y": "untestable", "V": "n/a", "P": "match"})
{
 "entries_before": 99,
 "entries_after": 132,
 "verified_before": 93,
 "verified_after": 125,
 "unverified_before": 6,
 "unverified_after": 7,
 "doi_before": 82,
 "doi_after": 114,
 "existing_ops": 20,
 "existing_fields_changed": 2,
 "labels_changed": 16,
 "moved_to_verified": 1,
 "new_proposed": 33,
 "new_verified_crossref": 30,
 "new_verified_other": 1,
 "new_unverified": 2,
 "claims_tested": 34,
 "claims_accepted_5field": 32,
 "http_failures": 1,
 "residual_entries": 0
}
validate: {'entries': 132, 'unique_keys': 132, 'verified_section': 125, 'unverified_section': 7, 'with_doi': 114} errors: [] doi-backing: []
```

C.3 `venv/bin/python tools/bib/crossref_check.py report --pass 1` (scratch copy; the regenerated pass-1 block differs from the committed one in 12 lines, e.g. "HTTP failures ... | 0 |" becomes "| 1 |" and several REJECT verdicts change 'Y': 'mismatch' to 'Y': 'untestable'):

```
{
 "checked": 96,
 "verified_unchanged": 33,
 "verified_corrected": 55,
 "new_doi": 35,
 "still_unverified": 6,
 "http_failures": 1,
 "moved_to_verified": 12,
 "doi_resolved": 44,
 "doi_total": 45,
 "search_run": 43,
 "search_accept_strict": 24,
 "search_accept_subst": 11,
 "verified_partial": 2,
 "added": 3
}
validate: {'entries': 99, 'unique_keys': 99, 'verified_section': 93, 'unverified_section': 6, 'with_doi': 82} errors: [] doi-backing: []
```

C.4 `venv/bin/python tools/lit/citation_lists.py build --list` (scratch copy, offline; the lines used in Section 2):

```
== Unique citing records overall: 60 after merging 1 hand-verified alias record(s)  (citing at least one of P01/P02/P02E/P03: 58;  citing only P08 and/or P09: 2)
   distinct works after counting 3 same-content DOI pair(s) once: 57  (citing P01/P02/P02E/P03: 55)
== Wrote 60 rows to docs/agent_reports/L4_citing_works.tsv
   classified from an abstract: 32;  from the title only (UNVERIFIED): 28
== Rows published after 2003, by class: REH-experiment=0, REH-method/theory=0, REM/RHEED imaging=1, transmission holography=2, review/history=3, reflection ptychography=0, other=3  (total 9)
   2007  transmission holography  Rafal E. Dunin‐Borkowski  Electron Holography of Nanostructured Materials
   2013  other                    Chiping Jiang  The interaction of a screw dislocation with a circular inhomogeneity n
   2015  other                    Hongbo Zhang  Development of lossy and near-lossless compression methods for wafer s
   2015  transmission holography  Rafal E. Dunin‐Borkowski  Electron Holography of Nanostructured Materials
   2015  REM/RHEED imaging        JOHN M. COWLEY  Electron Microscopy: Surface Diffraction
   2019  other                    S. C. Lee  Elastic Variation of Quasi-One-Dimensional Cubic-Phase GaN at Nanoscal
   2019  review/history           Rafal E. Dunin‐Borkowski  Electron Holography
   2020  review/history           Ken Harada  Interference and interferometry in electron holography
   2022  review/history             Notes and References
   2001  REH-experiment     Takayuki Suzuki  Energy-filtered Electron Interferometry in Reflection Electron Microscopy  10.1143/jjap.40.2527
   2003  REH-experiment     Y. Tanishiro  Electron Energy Loss Spectroscopy in REM-RHEED: Energy Filtering by Omega-type Energy Filt  10.1380/jsssj.24.166
```

C.5 `venv/bin/python tools/reflection_step_phase_calculator.py`: "25/25 checks pass in this script itself."

C.6 Missing search caches (the six rate-limited queries): `ls docs/agent_reports/citation_cache/search` has no file for q01, q02, q03, q16, q28 (OpenAlex) or q09 (Semantic Scholar relevance).
