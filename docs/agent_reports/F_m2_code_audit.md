# F. M2 reflection-multislice code audit (pre-rocking/steps)

Status: IN PROGRESS (2026-10-14). Auditor: code-auditor subagent. Commit audited: d404587
(branch trixode-studios-claude/sweet-carson-2grkn2). The code under audit was not modified.
Scratch scripts: /tmp/claude-0/-home-user-Holography/57d40492-0c74-558e-a50e-ca09e117ea85/scratchpad/F_audit/
(abbreviated `$S/` below). Python: /tmp/claude-0/venv/bin/python (numpy 2.5.4, scipy 1.18.1, h5py 3.16.0,
pytest 9.1.1). Evidence labels: REPRODUCED (synthetic CPU reproduction in this audit), DERIVED_HERE,
PLAUSIBLE (not reproduced; what would confirm it is stated), SECTION_READ (code read, no run).

## Commands run (log)

| # | Command | Result |
|---|---|---|
| 1 | `python -m pytest -q -m "not slow" -p no:cacheprovider` (repo root) | 49 passed, 5 deselected, 0.74 s |
| 2 | `python -m reflection_holo.campaign plan --config configs/fir_m2_campaign.yaml --stage all --out $S/RUN_plan` | 36 / 172 / 1892 / 867 tasks (2967), max memory 0.72 / 7.47 / 15.98 / 17.40 GB: matches docs/08 |
| 3 | `python $S/mem_check.py $S/RUN_plan` | peak GPU memory incl. analysis temporaries <= 25.4 GB (planner says 17.4): no OOM risk on 80 GB |
| 4 | `python $S/r1_gate_failopen.py` | validation/convergence verdicts pass on missing inputs (F-01) |
| 5 | `python $S/r2_rung1_vacuous.py $S/RUN_plan` and `python $S/r2b_rung1_tolerance.py $S/RUN_plan $S/r2_rung1_vacuous.py` | rung-1 sub-checks at 0.2 A, 30/40 mrad are weak (F-07) |

(continued below as the audit proceeds)

## Findings (provisional, being filled in)

### F-01 (Major, type a+c) Validation and convergence verdicts fail open on missing or empty inputs — REPRODUCED

* `reflection_holo/aggregate.py:259-261`: `all_pass = all(... for d in S["rung1"] + S["rung2"]) and
  all(v.get("pass", True) ...)`. Empty lists are `True`; rung-3 and beam-independence entries without a
  `pass` key count as passing.
* `aggregate.py:243-245`: a rung-3 entry gets a `pass` key only `if ... and n` (n = points with
  |r| >= 1e-2); n = 0 means no key, i.e. pass. `aggregate.py:228-229`: if the level-0 task is missing
  the whole surface is skipped. `aggregate.py:255-257`: same for beam independence (`if c.get("n")`).
* `aggregate.py:296-297`: `converged` requires only that the gates PRESENT pass; missing gate tasks
  are not counted.
* `fir/run_stage.sbatch:44-55`: tasks that failed twice are excluded from REMAINING, so the stage goes
  to aggregation with them absent. Nothing compares `n_results` with the number of planned tasks.

Reproduction (`$S/r1_gate_failopen.py`, synthetic result dicts fed to the real functions):
```
(a) empty validation stage: all_pass = True
(b) only one rung-1 result: all_pass = True | rung2 entries: 0 | rung3 entries: 0
(c) rung-3 si111 L1 with |r|<1e-2: n = 0 | 'pass' key present: False | all_pass = True
(d) rung-3 level-1 result missing: rung3 entries = 0 | all_pass = True
(e) convergence with 1 of 5 gates present: converged = True | variants: ['delay 9.0 decay lengths']
(f) gate 30 pct off with bound 0.1: max_abs_diff = 0.060, max_abs_excess = -0.040, converged = True
```
Why it matters: a GPU-path exception that hits a whole task kind (for example `uniform_1d` or
`averaged_1d`, which `fir/gpu_selftest.py` does not exercise on CuPy) twice would remove that rung from
the ladder and the chain would still start convergence, rocking and steps. Item (f) is by design
(bounds are subtracted) but there is no cap on the bound or check of `stopped_at_cap`.
Fix: compare the number of results per rung, surface, level, waist and gate with the plan (36 and 172);
require n > 0 for every null test and beam-independence pair; treat a missing gate as a failure.
Immediate action for the running campaign: check `RUN/summary/validation/summary.json` `n_results == 36`,
`RUN/summary/convergence/summary.json` `n_results == 172`, every rung-3 translation/mirror entry has
`n > 0` and a `pass` key, and `RUN/failed/` is empty for these stages, before rocking starts.

### F-07 (Minor, type b for a stronger test; a for reporting) Rung-1 checks at 0.2 A width, 30 and 40 mrad are nearly vacuous — REPRODUCED

`configs/benchmarks.yaml` rung 1: amp_abs_floor 1e-6, phase only where |r| >= 1e-4. With the production
rung-1 tasks the Parratt |r| over the weight >= 0.05 window is 1.7e-5..4.3e-5 at 30 mrad and
5.8e-7..1.46e-6 at 40 mrad for the 0.2 A step. Largest uniform error that still passes
(`$S/r2b_rung1_tolerance.py`):
```
width  W   theta0  max eps passing   max phase error passing (rad)
 0.20  0.5   30.0     0.0230            0.0230
 0.20  0.5   40.0     0.6825            0.6961
(all 0.05 A cases and the 0.2 A cases at 6-20 mrad: 0.0030 and 0.002-0.003)
```
The 0.05 A step keeps rung 1 meaningful up to 40 mrad (|r| ~ 3e-3), so the ladder as a whole is not
vacuous; the 0.2 A / 40 mrad entries should not be quoted as passing checks.
