# Reflection-mode dark-field electron holography of Si surfaces: analysis and specification of the theoretical simulation repository

Prepared 2026-09-21 for Ali (analysis of `https://github.com/hussienba/si110-reflection-holography`,
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
| `docs/03_physics_summary.md` | The physics the simulation must reproduce: step phase, refraction, wrap period, multislice validity, hologram formation, with numbers. |
| `docs/05_final_repository_specification.md` | What the final theoretical simulation repository must look like: acceptance criteria, configurations, architecture, forward-model and holography requirements, provenance, comparison protocol, tests, milestones. |
| `docs/06_project_inputs_required.md` | Laboratory inputs the simulation cannot supply (PROJECT_INPUT list). |
| `docs/physics_conventions.md`, `docs/model_assumptions.md`, `docs/source_map.tsv`, `docs/references.bib` | Provenance files required by the instruction file (section 10). |
| `docs/agent_reports/` | The full reports of the four delegated audits: A (code), B (literature), C (physics derivations), D (software provenance), plus calculator output and the orchestrator's independent sanity numbers. |
| `tools/reflection_step_phase_calculator.py` | Numpy-only reference calculator reproducing every number in the physics report; 25 self-checks. |
| `tools/provenance_checks/` | Scripts that exercise the prismatique 0.0.1 API exactly as the inspected pipeline does (no simulation run). |

## Evidence labels

METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED, as
defined in the instruction file. Two session-specific qualifiers are used in the literature report:
`METADATA_VERIFIED(index)` (seen in a search index, not in a publisher record) and `+ABSTRACT(index)`.

## Limitations of this analysis (read before citing anything)

* The analysis environment blocked every scholarly host (publishers, doi.org, Crossref, Semantic Scholar,
  OpenAlex, PMC, arXiv). No paper or book chapter was read; literature evidence is index-level only and
  Osakabe et al. 1988 could not be read at all.
* No multislice or dynamical reflection simulation was executed. Software statements come from reading the
  version-matched source code and exercising the Python API without the compiled engine.
* All physics is derived from stated premises and reproduced numerically; it has not been checked against
  the textbook sections it would normally be attributed to.

## Reproducing the numbers

```
python3 -m venv venv && venv/bin/pip install numpy
venv/bin/python tools/reflection_step_phase_calculator.py   # prints 25/25 checks pass
```
