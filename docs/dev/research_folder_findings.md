# Findings from the research-folder triage (2026-10-15)

Source: the Batch-API triage of Ali's research folder (`tools/research_inventory/triage.py`, Sonnet 5.5,
low effort, 534 files and code folders). The model read only the **first ~6000 characters** of each file,
so every item below is a pointer to check, not a verified result. Paths are relative to
`Research - 2026/`.

## 1. Conflicts between the transfer report and this repository's theory (check first)

| Claim in the transfer-exam material | This repository | Where |
|---|---|---|
| A symmetric specular reflection on the {111} facet is "phase-blind" to a single d111 step (phase exactly 2π). | Not blind: refraction makes the measured step phase `2π m n sin θ_ext / sin θ_int`, not an integer multiple of 2π (`docs/theory/physics_summary.md`, section 2, table of rod orders). | `transfer exam/claude-figures/fig_crystallography_standalone.pdf`; `transfer exam/outputs/figures/4_silicon_reciprocal_space.pdf`; `transfer exam/DATA/APRIL/make_reflection_selection_figure.py` |
| The asymmetric Si(2,-2,0) reflection gives 2π/3 per bilayer step, so it is the one to use. | The full `G·R` for (2,-2,0) is exactly 2π (invisible at the vacuum Bragg condition); 2π/3 comes from dropping the in-plane term `g_par·R_par` (`physics_summary.md`, section 2). | same files |

Both claims entered the transfer report. They need a derivation and a numerical test (Phase A of
`HANDOFF_batch_plan.md`) before they are repeated.

## 2. Facts that change the plan

* **Merlin "50-350 keV" series are threshold settings at a fixed 200 keV beam**, not beam energies.
  The detector report gives MTF, NNPS and relative DQE versus threshold.
  `MTF_CALIBRATIN_MERLIN/results/report.md`, code in `MTF_CALIBRATIN_MERLIN/merlin/` (15 modules, with tests).
  `docs/ROADMAP.md` is corrected.
* **Si(666) is forbidden** in diamond cubic (and beyond Nyquist at the stored sampling), so the earlier
  Prismatique simulations that isolate Si(666) are illustrative only.
  `transfer exam/committee_deck_extracted/README_committee_deck.md`; `research/progress_report_2026-06-12.md`.
* **The March phase step (1.84 rad) is degenerate** with a lens plus dynamical phase ramp; the proposed fix
  is split illumination with a flat reference terrace (objective O1). This is the same layout as the
  repository's three-strip sample (reference strip, step strip, defect strip).
  `transfer exam/report/figures/fig_honest_standalone.pdf`.
* **Measured phase noise is about 1.7 x the shot-noise prediction** (March holograms).
  `transfer exam/report/figures/fig_holo_diag.pdf`; analysis in
  `research-agent/MARCH/01_Si110_reflection_holography/analysis_2026-05-23/REPORT.md` (differential phase:
  the reference is a re-acquisition of the same region).
* **A Bloch-wave / R-matrix dynamical diffraction package (10 modules)** is mentioned in
  `research-agent/computational_simulations_3min_talk.md`. If it exists and works, it is a candidate for
  step 2 of the validation ladder (an independent dynamical code). Found in
  `research-agent/MARCH/01_Si110_reflection_holography/2026-03-19_reflection_with_Arthur/07_VALID_measurements/diffraction_series/simulation/`
  (`bloch_wave.py`, `r_matrix.py`, `multislice_3d.py`, `structure_factors.py`, `run_simulation.py`), with
  the theory in `research-agent/MARCH/01_Si110_reflection_holography/bulk_reflection_diffraction_theory_report.md`
  and `RHEED_simulation_report.md` (same folder). Not yet reviewed.
* **Known open issues from the June progress report:** the Si(100) versus Si(110) model mismatch and the
  "666" filter Nyquist bug. `research/progress_report_2026-06-12.md`.

## 3. Useful existing material

* Transfer report: many versions. Candidates for the latest: `transfer exam/report/transfer_report.pdf`
  (24 pp.) and `transfer exam/outputs/deliverables/transfer_report.pdf` (17 pp.). Talk:
  `transfer exam/presentation/transfer_talk.pdf` (29 June 2026). Committee Q&A prep:
  `transfer exam/prep/defense_qa.pdf`.
* PtyRAD offline install bundle for Fir: `CODE/ptyrad_fir_1.0/`.
* Beam-tilt calibration code (BTX/BTY to mrad from Au 111 rings): `Research - 2025 2/`,
  `beam tilt and gold powder /`, `beam_tilt_calibration_verification/`.
* Reflection-diffraction processing of Merlin `.hm` files:
  `research-agent/MARCH/01_Si110_reflection_holography/2026-03-19_reflection_with_Arthur/07_VALID_measurements/diffraction_series/`.
* A reflection-ptychography paper already in the folder: aPIE, angle calibration for reflection
  ptychography (Optics Letters 47(8), 1949; optical, near-infrared): `papers/ol-47-8-1949 (1).pdf`.
  Citation not yet verified for `docs/literature/`.

## 4. Not part of this project

PHYS550 lecture boards (`_inbox_loose/Lecture boards.html/`), the magnetite/Mn-ferrite course project,
TurboQuant notes (`research-agent/MARCH/ENGINEERING_REVIEW.md`, `RUNNING.md`), the third-party Sphinx docs
in `Research - 2025 2/tilt_beam_BT/1.3.0/html/`, and a stray Nature Nanotechnology paper on spin helicity.
