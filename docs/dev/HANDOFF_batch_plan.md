# Handoff: theory-verification plan with the Claude Batch API (2026-10-15)

For the next Claude session working on this repository (for example in Claude Science). Read this
first, then `README.md` and `docs/guide/pipeline.md`.

## 1. Where things stand

* **Branch:** `trixode-studios-claude/ecstatic-euler-a2b4y1`.
* **Pull request:** open into a new `main`, alihasuna/Holography#1, not yet merged. After the merge,
  make `main` the default branch on GitHub.
* **Pipeline:** the code covers the whole chain (crystal, buried dislocations, grazing multislice on
  CPU and GPU, geometric model, hologram, reconstruction). 48 tests pass. Results are in
  `docs/results/`.
* **Validation status:**
  * the phase agrees with the geometric model to 0.05 rad;
  * the step phase matches Osakabe's 1990 formula;
  * there is **no independent validation yet** (abTEM, or a dynamical RHEED code);
  * the absorption value is a placeholder.
* **Fir jobs:** the 60° and Lomer 50 nm runs, both reflections, were submitted by Ali on Fir (Alliance
  H100 MIG slices; see `docs/guide/hpc_alliance.md`, section 5). Results are pending. Collect
  `summary.json`, `results.npz` and `rows_*.npz` from `$SCRATCH/holo_outputs/`.
* **Reading lists, verified:**
  * `docs/literature/reading_list_reflection_theory.md`
  * `docs/literature/reading_list_holography_dislocations.md`
  * `docs/literature/reading_list_ptychography.md`
  * surveys: `docs/literature/reflection_holography.md`, `docs/literature/dark_field_strain.md`
* **PDFs:** Ali is downloading them into `literature_pdfs/`, which is git-ignored and must
  **never** be committed.

## 2. Goal

The goal is a pipeline grounded entirely in theory, as the first step towards a **reflection-mode
electron ptychography engine**: simulate scanned-probe diffraction at grazing incidence, then
reconstruct. The literature search found no published electron ptychography in RHEED geometry. The
closest precedent is X-ray grazing-incidence multislice ptychography: Besley et al. 2025,
arXiv:2510.06877.

## 3. The plan

**Budget:** about $150 in Claude API credits, using the Message Batches API at 50 % off.

**Rule for the whole plan:** every equation in the theory specification either cites a source with
page numbers (SECTION_READ) or is DERIVED_HERE **and** backed by a passing pytest. Model answers
are claims to test, never proof.

| Phase | What | Model | Requests | Estimate |
|---|---|---|---|---|
| 0 | Extract equations, assumptions, validity limits, parameters and benchmark numbers from each PDF chapter or paper (page numbers mandatory; key chapters extracted twice, independently, then compared) | Sonnet 5.5 | ~100 | ~$8 |
| A | Theory specification, standard topics: relativistic wavelength and interaction constant, refraction and mean inner potential, hologram formation and reconstruction, dislocation elasticity (isotropic and anisotropic), coherence, detector and dose. 3 independent derivations each, then a comparison | Opus 5.5 | ~25 | ~$9 |
| A | Theory specification, hardest topics: dynamical RHEED theory, validity of grazing multislice (projection approximation, slice thickness, edge effects; see below), the reflection-ptychography forward model and inverse problem; plus final judging where the Opus derivations disagree | Fable 5.1 | ~10 | ~$12 |
| B | Code ↔ theory audit: each module of `reflection_holo/` with its theory section; 3 independent reviewers; findings with file:line and a proposed test | Opus 5.5 | ~30 | ~$11 |
| D | Ptychography engine design: forward model, scan geometry (footprint elongated about 59 × along the beam), reconstruction (ePIE, ML/LSQ-ML, gradient-based multislice), sampling and uniqueness; 3 proposals plus an adversarial review | Fable 5.1 + Opus 5.5 | ~10 | ~$10 |
| E | Draft pytest checks from A–D: analytic limits, round trips, benchmarks | Sonnet 5.5 | ~20 | ~$2 |

**Total:** about $52, leaving about $100 for re-runs and a second round.

### First priority in Phase A: illumination edge effects

Ma & Marks, Acta Cryst. A46, 11–32 (1990), pp. 30–32, report that a tilted, Gaussian-smoothed beam
towards the surface gives unstable results because of edge effects. That is close to the sheet-beam
illumination in `reflection_holo/forward/multislice.py`. The fix they give is edge patching: Acta
Cryst. A47, 707–715 (1991), pp. 707–709; free author copies are on numis.northwestern.edu. This
needs a dedicated derivation **and** a numerical test.

### Batch tool to build: `tools/llm_audit/`

| Script | Job |
|---|---|
| `build.py --phase X` | Assemble the requests (custom_id, model, cached shared context, task, structured-output schema), write them to disk, and print the token count and dollar estimate |
| `submit.py --phase X` | Ask for explicit confirmation, enforce a per-phase dollar cap, then submit and save the batch id |
| `status.py` | Poll the batch |
| `collect.py --phase X` | Download the results (key them by custom_id; results come in any order), write `docs/dev/audits/<phase>/<custom_id>.md` plus a summary that lists the disagreements between independent answers |

Implementation requirements:

* **SDK and models:** the official `anthropic` Python SDK, with the model ids `claude-fable-5-1`,
  `claude-opus-5-5` and `claude-sonnet-5-5`.
* **Thinking and effort:** adaptive thinking, with effort set explicitly (Opus 5.5 defaults to
  `medium`). Fable 5.1 thinking is always on. Forced `tool_choice` returns a 400 on these models, so
  use `output_config.format` structured outputs instead.
* **Caching:** prompt caching for the shared context.
* **Results:** check `stop_reason` (including `refusal`) before reading content. The server-side
  `fallbacks` parameter is not available on the Batches API.
* **Credentials:** the API key comes from `ANTHROPIC_API_KEY` in Ali's own environment, and is never
  in code, logs or chat.
* **PDFs:** read only from `literature_pdfs/`. Commit only the extracted notes.
* **Cost:** every phase that spends money needs Ali's explicit confirmation first.

## 4. Open items for Ali

1. Full names (and ORCIDs) for `LICENSE`, `CITATION.cff` and `pyproject.toml`; placeholders are
   marked `TO BE FILLED IN`.
2. Merge the pull request, then make `main` the default branch.
3. Check that the library licence allows uploading book chapters to an AI tool.
4. Collect the Fir results.
5. Optional: apply to Anthropic's science research-credit programme (eligibility unverified).

## 5. Conventions to keep

* **Evidence labels:** PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, SECTION_READ, SMOKE_TEST,
  METADATA_VERIFIED, UNVERIFIED (`docs/theory/model_assumptions.md`).
* **Figures:** Nature style (`reflection_holo/plotstyle.py`), with captions in
  `docs/figures/CAPTIONS.md`.
* **Communication with Ali:** short, structured answers with explicit next steps.
