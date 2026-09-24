# A5 - Audit of the E2 (surface, thermal) and E3 (coherence, inelastic) physics code at f4ce75e

Agent A5, 2026-09-24. Status: IN PROGRESS (written incrementally).

Scope: commit f4ce75e, checked out as a detached worktree
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/a5_wt` (removed at
the end). Python: `/home/user/Holography/venv/bin/python` with `PYTHONPATH` set to the worktree;
nothing installed. No code under audit was modified; nothing committed or pushed. E1's files
(potentials.py, null tests) in the main tree are ignored.

Reports audited: docs/agent_reports/E2_surface_thermal.md, docs/agent_reports/E3_coherence_inelastic.md.

## 0. Log

* Worktree created at f4ce75e (`git worktree add --detach ... f4ce75e`).
* Read: E2 and E3 reports; L7 section 1.4; reconstruction.py; si001.py.

## 1. Verdict table

(filled at the end)

## 2. Findings

(filled incrementally)

## 3. Commands run

| # | command (cwd = worktree unless stated) | result |
|---|---|---|
| 1 | `git -C /home/user/Holography worktree add --detach <wt> f4ce75e` | HEAD f4ce75e |
| 2 | `git diff --stat 1ef0900 f4ce75e` (main repo) | 82 files changed |
