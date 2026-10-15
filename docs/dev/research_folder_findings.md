# Research folder: what the new simulation may use (2026-10-15)

**Rule (Ali, 2026-10-15).** The simulation is being redone so that it rests only on
**the literature** (papers, books, manuals) and **real measurements** (raw microscope files). Earlier
AI-generated material is not a source: notes, simulations, reports, figures, and the claims built on
them, including those in the transfer-exam documents. Any of it may be re-derived from the
literature, but it is never cited as evidence.

Folder map: `tools/research_inventory/` (inventory, duplicates, experiment catalogue, Batch-API
triage). `sources.py` writes the list of usable sources (`sources.md`) on Ali's Mac.

## 1. Real measurements (to compare with the simulation)

Catalogued from file headers in `experiments.csv` (317 unique raw files, 82 session folders). Main sets:

* **March 2026, cleaved Si(110) wafer, {111} facet, HF-3300 at 200 kV:**
  * off-axis holograms (13 March; biprism 106.8 V, 0.0242 nm per pixel);
  * dark field (16 March);
  * reflection session with Arthur (19 March; stage alpha 3.5-4.5 deg, camera length 500, diffraction at
    tilt 4.1 deg), Merlin `.hm` files in `research-agent/MARCH/01_Si110_reflection_holography/2026-03-19_reflection_with_Arthur/07_VALID_measurements/`.
* **Merlin (Medipix3) detector series:** raw files in `MTF_CALIBRATIN_MERLIN/`. Whether the
  "50-350 keV" labels are beam energies or threshold settings must be read from the raw headers
  (an AI-written report says thresholds at a fixed 200 keV; not yet checked).
* **Beam-tilt calibration** with Au powder rings (Nov 2025), `Research - 2025 2/` and
  `beam_tilt_calibration_verification/`; **image-plane correction** (Jan 2026).
* **SEM** of the cleaved Si(110) edge (18 March 2026, S-4800), `research-agent/SILICON (110)/`.

## 2. Literature already in the folder

Listed by `sources.py` (papers, books and chapters, manuals; relevance 3 or more). Examples: Kirkland,
*Advanced Computing in Electron Microscopy* (3rd ed., 2020); the aPIE paper on angle calibration for
reflection ptychography (Optics Letters 47(8), 1949; optical). Books from shadow libraries should be
replaced by library-licensed copies before any text is sent to an API. Missing items:
`docs/literature/download_checklist.md`.

## 3. Not used

* **The March 2026 Bloch-wave / R-matrix code** (`legacy/march2026_bloch_rmatrix/`, AI-written). An
  audit found that every reflectivity it outputs is wrong: no mean inner potential, no relativistic
  factor, sign errors in absorption, and a regularised boundary solve
  (`docs/dev/audits/legacy_bloch_rmatrix_review.md`). It is kept only as a record.
* **Earlier Prismatique simulations, AI-written reports, posters and figures.**
* **Not this project:** PHYS550 lecture boards, the magnetite/Mn-ferrite course project, TurboQuant
  notes, the third-party Sphinx docs in `Research - 2025 2/tilt_beam_BT/1.3.0/html/`.

## 4. Open question for the repository's own simulation (from the audit, to settle from the literature)

The audit's independent one-rod model puts the Si(001) (008) reflectivity maximum only about 0.02 mrad
above the refraction-corrected Bragg angle. The repository's multislice puts it 0.8 mrad above, and
the holograms are simulated there (16.93 mrad, `docs/guide/parameters.md`). The audit's 3-D check did not
converge, so the difference may come from coupling between rods, or from the illumination edge
effects of Ma & Marks (1990). This is the first test in Phase A (`HANDOFF_batch_plan.md`).
