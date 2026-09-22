# Reflection-mode dark-field electron holography of Si surfaces: analysis and specification of the theoretical simulation repository

Prepared 2026-09-21 for Ali, revised 2026-09-22 after the Phase 1 literature pass (analysis of `https://github.com/hussienba/si110-reflection-holography`,
commit `6694959`), following the source policy in the project instruction file
(`ba72277e-si110_reflection_holography_agent_instructions.txt`).

This repository contains no simulation results yet. It contains the audit of the existing simulation
repository, the physics it must reproduce, the software facts that determine what it currently computes,
the literature position (with the access limitations stated), and the specification of the final version
that can be contrasted with the real reflection-mode dark-field holography experiment.

## Read in this order

| File | What it is |
|---|---|
| `docs/00_executive_summary.md` | Findings and decisions in two pages. |
| `docs/01_repository_audit.md` | What the inspected repository actually simulates, defect list with file:line, section-9 checklist. |
| `docs/02_literature_position.md` | Osakabe as the starting point, the theory to read, current analogues; access limitations. |
| `docs/03_physics_summary.md` | The physics the simulation must reproduce: step phase, refraction, wrap period, coherence and shadowing, multislice validity, hologram formation, with numbers. |
| `docs/04_software_provenance_summary.md` | What prismatique/Prismatic actually compute (mid-plane wave, schema, tilt, ensembles) and the consequences. |
| `docs/05_final_repository_specification.md` | What the final theoretical simulation repository must look like: acceptance criteria, configurations, architecture, forward-model and holography requirements, phase-validation ladder, provenance, comparison protocol, tests, milestones. |
| `docs/06_project_inputs_required.md` | Laboratory inputs the simulation cannot supply (PROJECT_INPUT list, 22 items). |
| `docs/07_reading_plan.md` | Every reference of the instruction file (B01-B15, C01-C03, P01-P07, S01-S02) with its expected access, what to extract, and the upload order for paywalled items. |
| `docs/physics_conventions.md`, `docs/model_assumptions.md`, `docs/source_map.tsv`, `docs/references.bib` | Provenance files required by the instruction file (section 10). |
| `docs/agent_reports/` (Phase 1) | B3 (Crossref verification of every bibliography record, with `crossref_cache/` and `tools/bib/`), L1 (P07 and the Hitachi patent read in full), L2 (P04, prismatique docs, Prismatic pages, P49 read in full), L3 (publisher tables of contents of B01-B15), L4 (citation lists of P01-P03, P08, P09, with `citation_cache/` and `tools/lit/citation_lists.py`), L5 (open-access check, P02E, C03 manuscript, Hÿtch 2010, a Si mean-inner-potential preprint), E3 (adversarial review of revision 3). |
| `docs/agent_reports/` (analysis) | The full reports of the delegated audits: A (code), B (literature) with B2 (bibliography verification log), C (physics derivations) with the calculator output, D (software provenance), E and E2 (two adversarial review passes of the summary documents; every finding is applied in revision 2 of the summaries or explicitly declined with a reason), plus the orchestrator's independent sanity numbers. |
| `tools/reflection_step_phase_calculator.py` | Numpy-only reference calculator reproducing every number in the physics report; 25 self-checks. |
| `tools/phase1_numbers.py` | The numbers added in revision 3 (mean-inner-potential sensitivity at 12.53 V, sign of the height bias); 4 self-checks. |
| `tools/provenance_checks/` | Scripts that exercise the prismatique 0.0.1 API exactly as the inspected pipeline does (no simulation run). |

## Evidence labels

METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED, as
defined in the instruction file. Session-specific qualifiers: `METADATA_VERIFIED(index)` and
`+ABSTRACT(index)` (revision 2: seen in a search index only); `+ABSTRACT(publisher)` and
`+ABSTRACT(PubMed)` (revision 3: the abstract read on the publisher's page or on PubMed/Europe PMC,
with the sentence as locator; SECTION_READ of the abstract and of nothing else).

## Limitations of this analysis (read before citing anything)

* Revision 2 was written with every scholarly host blocked. In revision 3 (network Full) every
  bibliography record is Crossref- or publisher-checked and the open sources are read in full, but the
  paywalled papers (including the body of Osakabe et al. 1988, whose abstract gives Pt(111)) and every
  book chapter are still unread; the upload list is in `docs/07_reading_plan.md`. The instruction file
  (`ba72277e-si110_reflection_holography_agent_instructions.txt`) was not attached to the Phase 1
  session; the source policy was applied as recorded in this repository and in `.claude/agents/`.
* No multislice or dynamical reflection simulation was executed. Software statements come from reading the
  version-matched source code and exercising the Python API without the compiled engine.
* All physics is derived from stated premises and reproduced numerically; it has not been checked against
  the textbook sections it would normally be attributed to. The adversarial review found and the summaries
  correct two numerical slips in the physics report (paraxial error, step projection width); the agent
  reports themselves are kept unedited as the record.

## Reproducing the numbers

```
python3 -m venv venv && venv/bin/pip install numpy
venv/bin/python tools/reflection_step_phase_calculator.py   # prints 25/25 checks pass
venv/bin/python tools/phase1_numbers.py                     # prints 4/4 checks pass
```
