# A8 - Audit of E4 (continuum oxide overlayer) at commit 83fa75f

Auditor: agent A8, 2026-09-24. Status: IN PROGRESS (written incrementally).

Scope: the continuum oxide overlayer of report E4 at commit 83fa75f, audited in a detached worktree
(`git worktree add --detach <scratchpad>/a8_wt 83fa75f`; `venv` symlinked into it, gitignored;
PYTHONPATH at the worktree; nothing installed). Base for diffs: 685e434. Context: PROJECT_INPUT
(Ali, 2026-09-24): air-exposed, O2/Ar plasma-cleaned ion-milled Si(001); holograms through an oxide;
200 keV, specular (0,0,8), 16.1347 mrad.

Nothing in the code under audit was modified; nothing committed or pushed; nothing written under
the repository's outputs/. Scratch scripts and their outputs live in the session scratchpad
(`<scratchpad>/a8/`), not in the repository.

## 0. Command log

(appended as the audit proceeds)

Abbreviations: WT = the audit worktree at 83fa75f; SP = the session scratchpad
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`; PY =
`/home/user/Holography/venv/bin/python`; every run below with `PYTHONPATH=<tree>`.

| # | command (cwd) | purpose | result |
|---|---|---|---|
| C1 | `git -C /home/user/Holography worktree add --detach SP/a8_wt 83fa75f`; `ln -s /home/user/Holography/venv SP/a8_wt/venv` | audit tree | HEAD 83fa75f, clean |
| C2 | `git diff --stat 685e434 83fa75f`; `git diff --stat 54de605 83fa75f`; `git log 685e434..83fa75f` | scope; E4's own change is 54de605..83fa75f (24 files) | see section 9 |
| C3 | `git diff 685e434 83fa75f -- <every code file in scope>` | read the change | - |
| C4 | `SP/a8/run_dirs.sh` (WT; `PY -m pytest -q tests/<d> -p no:cacheprovider` for d = structure, io, pipeline, forward) | directory runs | section 11 |
| C5 | `PY SP/a8/a8_analytic.py` (first-principles recomputation, no package import) -> `SP/a8/a8_analytic.out` | item (3) | section 3 |
| C6 | `PY SP/a8/a8_exact1d.py` (exact 1-D transfer-matrix reflectivity of the erf-graded edge) -> `SP/a8/a8_exact1d.out` | item (3) | section 3 |
| C7 | `git -C /home/user/Holography archive 54de605 \| tar -x -C SP/a8/base_54de605` (same for 685e434) | bit-identity baselines (outside the repository) | - |
| C8 | `SP/a8/run_bitid.sh` (`PY SP/a8/a8_bitid.py <tree> <npz>` for base_54de605 and WT) | item (6) | section 6 |
