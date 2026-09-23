# E6 - Adversarial review of the literature reports L6 (sourced Si parameters) and L7 (surface realism)

Reviewer: agent E6, 2026-09-23 (started 23:49 UTC). Branch `claude/electron-holography-orchestration-nakd7r`.
Status: IN PROGRESS (written incrementally; the verdict table, the CONFIRM list and the DO-NOT-ADOPT list
at the end are the final state).

Scope: `docs/agent_reports/L6_sourced_si_parameters.md` (669 lines, commit 9aeb79d) and
`docs/agent_reports/L7_surface_realism.md` (576 lines, commit e5405a2), with the B4 merge
(`docs/agent_reports/B4_verification_log.md`, `docs/references.bib`, 218 entries). Neither report and
no other repository file was edited. Files written by E6: this report, `tools/review/e6_recompute.py`
and its saved output `tools/review/e6_recompute_output.txt`. Nothing committed or pushed.

Method: (1) every SECTION_READ claim that could be reached was re-read by E6 in the downloaded source
(L6 and L7 scratch directories `.../scratchpad/l6/` and `.../scratchpad/l7/`, SHA-256 re-checked where
the reports print one); page images were rendered with PyMuPDF where the text layer is unusable;
(2) every derived number was recomputed with E6's own script, written from the physics and the sources
without reading L6's `l6/calc/si_tds_absorption.py` or any L7 script; (3) the published Thomas et al.
(2024) code was re-run as a black box and compared with an independent E6 implementation of the same
Bird-King integral; (4) recommendations were checked for logic and against the repository documents.

Severity scale: BLOCKER (must be fixed before anything is adopted), MAJOR (must be fixed or re-worded
before the affected item is adopted), MINOR (fix when adopting), NIT.

