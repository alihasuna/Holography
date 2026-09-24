# X2: fixes of audit A6 (E1 engine wave 2a)

Agent X2, 2026-09-24. Written incrementally: finding -> fixed/declined -> file:line -> test ->
results verbatim -> NOT RUN. Scope: docs/agent_reports/A6_e1_audit.md applied to E1's work
(docs/agent_reports/E1_engine_wave2a.md) with the orchestrator's decisions. Nothing committed or
pushed. Base: HEAD b6e06bf (snapshot commits of X1/X2 in progress; X1 edits E2/E3 files in
parallel, which were not touched here). Machine shared (4 cores); load averages are quoted with
the runs. `<scratch>` = the session scratchpad (not in the repository).

Status: IN PROGRESS.

## Baseline taken before any edit

* A6's `study_points_fingerprint.py` (hashes of every built cell, atom set, beam, params, R and
  absorption, via the tree's own `run_study._build`) on study.yaml (17 points) and
  study_depth100.yaml (24 points) at b6e06bf: `<scratch>/x2/fp_before.txt`,
  `<scratch>/x2/fp100_before.txt` (24 s and 60 s).
