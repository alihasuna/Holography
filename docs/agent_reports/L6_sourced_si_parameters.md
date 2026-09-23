# L6 - Sourced silicon parameters for the reflection multislice: absorption, Debye-Waller factor, mean inner potential, benchmark rocking curves

Agent L6, 2026-09-23 (started 22:17 UTC). Branch `claude/electron-holography-orchestration-nakd7r`.
Written incrementally; the final state is the summary table, the recommendation and the upload list
at the end. Nothing committed or pushed. No repository file other than this report and
`docs/agent_reports/L6_new_refs.bib` was written.

Experiment (PROJECT_INPUT, Ali): Si(001), ion-milled, 200 keV (never 300 keV), reflection-mode
dark-field holography with the specular (0,0,8) beam at about 16 mrad glancing angle. Engine: our
multislice with the Kirkland independent-atom potential (abTEM 1.0.10), frozen phonons
(`FrozenPhonons`, independent Gaussian displacements, u = 0.076 A rms per axis, ASSUMPTION A7) and
`PhysicalAbsorption(model="proportional")`, V_imag(r) = ratio * V_real(r) with TEST_ONLY ratio 0.05 or
0.1 (`reflection_holo/forward/multislice/potentials.py`, class `PhysicalAbsorption`; PROJECT_INPUT
item 21 missing).

Label policy: METADATA_VERIFIED, SECTION_READ (only with a locator), REPRODUCED, PROJECT_INPUT,
ASSUMPTION, DERIVED_HERE, UNVERIFIED. Sub-labels as in L5: `+ABSTRACT(publisher)` (abstract read on
the publisher page), `+ABSTRACT(PubMed)` (abstract read in the Europe PMC record), `+ABSTRACT(index)`
(search-engine summary only; NOT evidence). A search-engine summary is never evidence; no value below
comes from one unless it is labelled UNVERIFIED. Raw downloads are kept outside the repository in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/l6/` (called
`l6/` below), with SHA-256 in section 0.

## 0. Log and files retrieved

- 22:17 UTC: read the task inputs: `docs/model_assumptions.md` (A7, B1, B6, B30, B32),
  `docs/06_project_inputs_required.md` (items 20, 21), `docs/references.bib` (header, MIP entries
  KRUSE06 to TANAKA24, unverified part), `docs/07_reading_plan.md`, `docs/source_map.tsv` (SM04,
  SM17), `docs/agent_reports/L5_open_access_check.md` (sections 0, 1, 4),
  `docs/agent_reports/H2_realistic_supercell_sizing.md` (sections 1, 2.5, 6, 10: N1, N2, N14), and the
  engine classes `PhysicalAbsorption` and `FrozenPhonons` (potentials.py).

