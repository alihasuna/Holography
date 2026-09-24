# X6 - Fixes after the re-audit A10b of X5 (item-12 label policy of comparison runs)

Agent X6, 2026-09-24. Branch `claude/electron-holography-orchestration-nakd7r`, HEAD cff596d when
work started. Status: IN PROGRESS (written incrementally; final status at the end).

Input, read in full: `docs/agent_reports/A10b_X5_reaudit.md` with its scratch
(`SP/a10b/`, SP = `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad`),
`docs/agent_reports/X5_a9b_fixes.md`, rows B7, B12, B41, B43 of `docs/model_assumptions.md`, item 12
of `docs/06_project_inputs_required.md` (with the orchestrator's interim wording of 477fad5), and the
orchestrator's six decisions.

Rules kept: no docs/ file edited except this report; no other report edited; nothing committed;
nothing written under outputs/; `scripts/hpc/alliance/` untouched; T5's files
(`tools/plots/buried_torus.py`, `tests/forward/test_buried_torus_analysis.py`) untouched; scratch in
`SP/x6/`.

Baseline before any change (oxide files and `tests/io/test_io_config_stand_ins.py`, 10 files):
`268 passed in 16.91s` (`SP/x6/baseline_oxide.txt`).

## Progress log

* (started) reading done; design in section 1.
* code changed: `structure/oxide.py` (item12_count_interval, parity-variant spec field and check),
  `pipeline/config.py` (parity key, structured records, uncertainty keys, item-12 record),
  `forward/cell.py` (n1 guard); X5's and X4's tests migrated to the new keys (section 3);
  `tools/review/x6/x6_oxide_numbers.py` written and run (output saved). Tests of the new behaviour
  and the mutation run follow.
* new tests written: `tests/structure/test_oxide_structure_a10b_fixes.py` (41),
  `tests/forward/test_oxide_multislice_a10b_fixes.py` (4), `tests/pipeline/test_oxide_pipeline_a10b_fixes.py`
  (187); the 13 oxide files together: `501 passed in 21.71s`.
* B41 demo bit-identity (`SP/x6/d_bitid.py`, outputs in `SP/x6/pipe/`): geometric `oxide_2p0nm`
  26/26 arrays bitwise identical to A10b's, X5's and A9b's runs; `multislice_tiny_oxide_2p0nm` 26/26
  identical to A10b's and A9b's; spec_sha256 equal to A10b's (094102ed...); per-parameter labels
  and headline unchanged; the item-12 record gains `consumed_layers` and `measurement_rule`.
