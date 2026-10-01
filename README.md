# Reflection-mode dark-field electron holography of Si surfaces: analysis and specification of the theoretical simulation repository

Prepared 2026-09-21 for Ali (analysis of `https://github.com/hussienba/si110-reflection-holography`,
commit `6694959`), following the source policy in the project instruction file
(`ba72277e-si110_reflection_holography_agent_instructions.txt`).

Since 2026-09-30 it also contains a first code subset (`reflection_holo/`): the geometry core, buried
dislocations in a half-space, a geometric-phase forward model and a grazing-incidence multislice kernel
(numpy/cupy), with smoke-test results only (`docs/08_buried_defects.md`; the kernel is not yet validated).
Beyond that, it contains the audit of the existing simulation
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
| `docs/08_buried_defects.md` | Buried dislocations: why they are visible in reflection (depth-independent surface bump `b_parallel/pi`), the models, verification and the geometry-mode and multislice smoke-test results. |
| `docs/11_si001_reconstruction_results.md` | Simulated holograms and reconstructed phase and amplitude of the three-strip sample at (008) and (0,0,12), with convergence findings. |
| `docs/10_si001_three_sections_plan.md` | Proposal: Si(001) sample in three strips (reference, raised 4 layers, buried Lomer edge dislocation), renders and what will be measured. |
| `docs/09_gpu_runbook_arbutus.md` | How to run the multislice on the Arbutus GPU VM (driver check, cupy, tmux, acceptance checks). |
| `docs/physics_conventions.md`, `docs/model_assumptions.md`, `docs/source_map.tsv`, `docs/references.bib` | Provenance files required by the instruction file (section 10). |
| `docs/agent_reports/` | The full reports of the delegated audits: A (code), B (literature) with B2 (bibliography verification log), C (physics derivations) with the calculator output, D (software provenance), E and E2 (two adversarial review passes of the summary documents; every finding is applied in revision 2 of the summaries or explicitly declined with a reason), plus the orchestrator's independent sanity numbers. |
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
  the textbook sections it would normally be attributed to. The adversarial review found and the summaries
  correct two numerical slips in the physics report (paraxial error, step projection width); the agent
  reports themselves are kept unedited as the record.

## Reproducing the numbers

```
python3 -m venv venv && venv/bin/pip install numpy
venv/bin/python tools/reflection_step_phase_calculator.py   # prints 25/25 checks pass
```

## Running the code (buried-dislocation smoke tests)

```
python3 -m venv venv && venv/bin/pip install numpy scipy matplotlib pytest pyyaml
venv/bin/python -m pytest -q                      # 40 pass; the cupy test is skipped without a GPU
venv/bin/python scripts/run_buried_dislocation.py geometric  --config configs/smoke/buried_dislocation_cpu.yaml
venv/bin/python scripts/run_buried_dislocation.py multislice --config configs/smoke/buried_dislocation_cpu.yaml   # about 1 min on CPU
venv/bin/python scripts/run_sections.py --config configs/si001_three_sections_cpu.yaml          # Si(001) three strips: holograms and reconstructions (about 45 min on CPU)
venv/bin/python scripts/figures_holography.py --config configs/si001_three_sections_cpu.yaml --data outputs/si001_three_sections_cpu/reconstruction --geo outputs/si001_three_sections_cpu/reconstruction/results.npz   # Nature-style figures, captions in docs/figures/CAPTIONS.md
# GPU: add --backend cupy and use configs/smoke/buried_dislocation_gpu.yaml; see docs/09
```
