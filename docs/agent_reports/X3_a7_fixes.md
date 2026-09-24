# X3 - Fixes of A7's remaining MINOR findings (A7-3, A7-4) and of A7-5 (documentation only)

Agent X3, 2026-09-24. Status: FINAL (written after the runs of section 5).

Base: branch claude/electron-holography-orchestration-nakd7r at 83fa75f when X3 started. During the
work the orchestrator committed 4112842 (tools/plots/torus_compact.py, unrelated) and the snapshots
68ad1a2, 30156ac, cf712e4, 95b2747 and a965404. These contain X3's edits as they stood at the time,
and at a965404 all of X3's code, script and test changes. `git diff --stat 83fa75f a965404 --
reflection_holo tests scripts configs tools` lists only X3's files plus torus_compact.py. "Before"
below means 83fa75f (a `git archive` export in X3's scratchpad); "after" means the working tree
(= a965404 for those directories; the later snapshot b96bc6e touched only this report). X3 committed
and pushed nothing and wrote nothing under outputs/ (3 files there, unchanged, before and after).
Oxide code (structure/oxide.py, the E4 parts of forward/cell.py, engines and pipeline) was not
touched. In docs/, only this report was written. The scratch scripts are in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/x3/`
(`<sp>` below).

## 1. Finding -> fix -> file:line -> test

| finding | fix | file:line (working tree) | test |
|---|---|---|---|
| A7-3 `converged_beyond_A` holds a distance when NOT converged | E1's rule restored: `converged_beyond_A` is `d` only when converged, else None. The distance X2 had put there when not converged, the end of the last included (failing) bin, is now in a separate field `last_examined_A`, returned next to `excluded` (the exclusion report). The field is defined for every verdict: the end of the last INCLUDED bin, or None when no bin is included. The verdict text names it. | tests/forward/null_test_cases.py:372-385 (contract), 441-457 (code: 450 `conv = d if n_after >= 1 else None`, 449 and 456 `last_examined_A`) | tests/forward/test_null_study_readout.py:153-176 (not converged: `is None` plus `last_examined_A`; new no-bin-included case: both None), 107, 193-194, 218-219; tests/forward/test_null_readout_known_answer.py:148-152 (engine, short cell), 156-186 (NEW: A7's case, B shifted half a pixel, engine run) |
| A7-3 consumers | run_study.py docstring names the fields and prints the verdict line after each translation point. The null-study README describes the fields. No other code reads the field: grep of reflection_holo/, scripts/, tools/ and tests/; tools/hpc/review_h5_recompute.py has its own unrelated `converged_beyond`, which already returns None. | scripts/hpc/null_test_study/run_study.py:28-31, 189-194; scripts/hpc/null_test_study/README.md:33-35 | the print line was evaluated on three synthetic results (section 3.1). run_study.py without `--estimate` was NOT RUN. |
| A7-4 dry-run memory need bound to the engine package only | Report schema /3. The report adds `package_tree`: the SHA-256 of the whole reflection_holo package tree of the IMPORTED package, with the definition that the run manifests already record (provenance.manifest.package_tree_sha256: every *.py and *.yaml file, which covers every tracked file of the package). The kit re-implements the same definition (`package_tree_sha256(repo)`). It refuses schema /2 and /1 reports, and it refuses a report without the tree hash or with a tree hash that differs from the submitting clone's. This check comes after the engine check, which is kept. The kit records `package_tree_sha256` in the submission record and prints it in the NOTE line. `--accept-need-below-dry-run` is unchanged. | reflection_holo/pipeline/__main__.py:81-85 (comment, schema /3), 118-136 (`package_tree_identity`), 191 (written into the report); scripts/hpc/alliance/kit.py:93-101 (comment, schema), 250-273 (`package_tree_sha256`), 374-377 (docstring), 416-423 (check), 440 (record), 448-451 (NOTE line); scripts/hpc/alliance/README_ALLIANCE.md:333-337 | tests/hpc/test_kit_gpu_mem_from_dry_run.py:35-69 (fake reports carry `package_tree`, schema /3), 157-174 (schema /2 refused; other tree refused; missing tree refused), 219-220, 223-243 (pipeline report: /3, tree hash equal to the kit's and to the manifest's), 246-257 (emulated dry-run job), 260-283 (NEW: cell.py, si001.py and estimates.py changes leave the engine hash unchanged and change the tree hash; the definitions are equal on changed copies; every git-tracked package file is *.py or *.yaml) |
| A7-5 (NIT) sqrt(2) in the disc bound not needed | Documentation only, as instructed: the factor is kept (behaviour unchanged, no test touched). The module docstring and the code comment now call it CONSERVATIVE, not necessary, with A7's derivation (real-linear remainder, phi = arg R[h]), which X3 re-checked. The line-branch sqrt(2) is called conservative in the same sense. | reflection_holo/optics/coherence.py:64-75 (module docstring), 173-174 (comment) | tests/optics unchanged, 75 passed (section 5) |

A7-3 design note. The rule is: converged iff at least one included bin starts at or after d, where d
is the end of the last failing included bin (or the start of the first included bin if none fails).
It is unchanged, so `converged`, `n_bins_beyond` and the verdict's decision are identical to X2's
for every input. Only the distance fields differ, and so does the wording of the NOT-converged
verdict text, which now names `last_examined_A`. When not converged, `last_examined_A` equals the end
of the last failing included bin, which is the value A7 proposed for `last_failing_..._end_A`. When
converged, the last failing distance is `converged_beyond_A` itself (if any bin failed), so a third
field would be redundant. A7's optional NIT, a minimum number of passing bins, was not applied (not
requested).

`scripts/hpc/null_test_study/study_depth100.yaml` was NOT edited. Its comment (lines 43-45: "the
first distance beyond which every included bin passes, `converged` says whether an included bin
lies beyond it") is consistent with the new contract, and an edit would change the file's SHA-256
17af7ca8..., which study_depth100_estimate_numpy4.txt records.

## 2. Reproductions, before (83fa75f) and after (working tree)

### 2.1 A7-3: crystal B translated half a pixel too far (A7's `n2_probe.py shiftB`)

`<sp>/shift_probe.py` is A7's `n2_probe.py` (`<sp>/../a7/n2_probe.py`), changed only to also print
`last_examined_A`
(`diff` in `<sp>`). It runs the rung-2 continuum, the study's beam and surface_resolved block, L_z of
the [110] L5k points, and B translated by R_x + 0.0125 A.

Before (`PYTHONPATH=<sp>/head_tree`, cwd `<sp>/head_tree/tests/forward`; 06:44-06:45 UTC):
```
  fixed: converged=False converged_beyond_A=4500.0 last_examined_A=<field absent> n_bins_beyond=0 n_included=9/10; verdict: NOT converged: the last included bin (ending 4500.0 A from the later contact) fails
  moved: converged=False converged_beyond_A=4500.0 last_examined_A=<field absent> n_bins_beyond=0 n_included=9/10; verdict: NOT converged: the last included bin (ending 4500.0 A from the later contact) fails
```
After (`PYTHONPATH=/home/user/Holography`; 06:47-06:48 UTC):
```
  fixed: converged=False converged_beyond_A=None last_examined_A=4500.0 n_bins_beyond=0 n_included=9/10; verdict: NOT converged: the last included bin (ending 4500.0 A from the later contact, last_examined_A) fails
  moved: converged=False converged_beyond_A=None last_examined_A=4500.0 n_bins_beyond=0 n_included=9/10; verdict: NOT converged: the last included bin (ending 4500.0 A from the later contact, last_examined_A) fails
```
The 20 per-bin lines (err, amp, |E_A|, status) are byte-identical before and after (`diff` of the
`d ...` lines is empty). Only the distance fields changed.

The same case is now a test at the a6_case geometry (L 6000 A; B re-run shifted, A's moved-beam run
reused), with the derived phase error -2 k sin(theta) dB = -0.101 rad asserted in every included bin
(tolerance 5e-3 rad). Output with `-s`: every included bin reads `err -9.99e-02` to `-1.01e-01 rad`
and fails; `moved beam: NOT converged: the last included bin (ending 4000.0 A from the later
contact, last_examined_A) fails`; `1 passed, 5 deselected in 59.90s`.

### 2.2 A7-4: a dry-run report of changed cell code, same engine and configuration

A7 left this unreproduced. `<sp>/a74/repro_a74.sh <submitting checkout> <tag>` does the following:
- copies the checkout's reflection_holo/ and changes forward/cell.py:108
  `bottom = lowest - dep` -> `bottom = lowest - dep - 1.5`, which keeps 1.5 A more crystal below the
  lowest terrace;
- runs `python -m reflection_holo.pipeline dry-run --report-json` from both trees on
  `<sp>/a74/demo_smoke_cupy.yaml`, which is configs/demo_smoke_si001.yaml (unchanged since 83fa75f)
  with the multislice_tiny variant's backend set to cupy, because the kit accepts only cupy
  configurations;
- asks the checkout's kit (`gpu_need_from_dry_run`, margin 0.5) to use each report.

Before (checkout = 83fa75f export; 06:53 UTC):
```
kit schema: reflholo_pipeline_dry_run_report/2
report orig: schema reflholo_pipeline_dry_run_report/2, engine c02579f11b77, package_tree absent, grid {'nx': 432, 'ny': 48, 'dx_A': 0.1961005787037037, 'dy_A': 0.2262875}, n_slices 1095, n_atoms 27000, device_peak_cupy 3687818 B
  kit of head_tree: ACCEPTED, need 0.005532 GB, n_atoms 27000
report mod: schema reflholo_pipeline_dry_run_report/2, engine c02579f11b77, package_tree absent, grid {'nx': 432, 'ny': 48, 'dx_A': 0.19957280092592594, 'dy_A': 0.2262875}, n_slices 1095, n_atoms 28080, device_peak_cupy 3703228 B
  kit of head_tree: ACCEPTED, need 0.005555 GB, n_atoms 28080
```
The engine hash is the same, but the atom count, the pixel size and the device peak differ, and the
kit ACCEPTS the other code's need. A7-4 is reproduced.

After (checkout = the final working tree, identical to HEAD a965404 in reflection_holo/, scripts/
and tests/; 08:06 UTC, after the suites. A first run at 06:53, before the A7-5 docstring edit, gave
the same verdicts with other tree hashes):
```
kit schema: reflholo_pipeline_dry_run_report/3
report orig: schema reflholo_pipeline_dry_run_report/3, engine c02579f11b77, package_tree 520735b26079, grid {'nx': 432, 'ny': 48, 'dx_A': 0.1961005787037037, 'dy_A': 0.2262875}, n_slices 1095, n_atoms 27000, device_peak_cupy 3687818 B
  kit of Holography: ACCEPTED, need 0.005532 GB, n_atoms 27000
report mod: schema reflholo_pipeline_dry_run_report/3, engine c02579f11b77, package_tree b280a8a39446, grid {'nx': 432, 'ny': 48, 'dx_A': 0.19957280092592594, 'dy_A': 0.2262875}, n_slices 1095, n_atoms 28080, device_peak_cupy 3703228 B
  kit of Holography: REFUSED: /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/x3/a74/after/rep_mod.json was made with the reflection_holo package tree b280a8a39446..., not with the package tree of /home/user/Holography (520735b26079...): the grid, the atom count or the memory model behind its estimate may differ (code outside the engine, e.g. forward/cell.py, structure/ or pipeline/, changed; audit A7-4); rerun the `dry-run` job with this code
```
The report of the submitting tree itself is still accepted, with the same need as before the fix.
The dry-run exit status 4 is expected: a cupy configuration on a machine without a GPU exits 4
after it has written the report.

Mutation checks of the new tests, run in a scratch git copy of the working tree (`<sp>/mut_tree`,
its own `git init`, not the project repository):
- M1, the kit's package-tree check disabled: `1 failed, 8 passed`
  (test_report_must_belong_to_this_configuration);
- M2, the report without `package_tree`: `2 failed, 7 passed` (the pipeline report test and the
  emulated dry-run job);
- M4, the kit's hash with paths relative to the repository instead of the package: `3 failed,
  6 passed` (the two above plus test_package_tree_hash_covers_code_outside_the_engine);
- M3 (A7-3), X2's rule `conv = d` restored: `4 failed, 12 passed, 2 skipped` (exactly the four
  not-converged assertions: synthetic unconverged, amplitude floor 0, engine short cell, shifted
  crystal).

The unmutated copy gives `9 passed`.

Consequence, stated for the kit's users: the tree hash covers every file of the package, including
docstrings and code unrelated to the grid (e.g. the A7-5 edit, or oxide work). After ANY change of
reflection_holo/, the `dry-run` job must be rerun before `--gpu-mem-from-dry-run` accepts its
report. Reports written at earlier commits (schema /2, e.g. at a1ef2a0, which TONIGHT.md pins)
are refused by this kit. The kit at a1ef2a0 is unaffected.

## 3. Checks outside the test suite

### 3.1 run_study.py's new verdict line

`<sp>/print_line_check.py` evaluates the print statement copied from run_study.py's source on three
synthetic read-outs:
```
[not converged]   surface-resolved: NOT converged: the last included bin (ending 7000.0 A from the later contact, last_examined_A) fails (converged False, converged_beyond_A None, last_examined_A 7000.0, 14 of 17 bins included)
[converged]   surface-resolved: converged beyond 0.0 A from the later contact (14 included bin(s) beyond, all within tolerance) (converged True, converged_beyond_A 0.0, last_examined_A 7000.0, 14 of 17 bins included)
[not assessed]   surface-resolved: no bin included (none under the lit core above the amplitude floor): convergence not assessed (converged False, converged_beyond_A None, last_examined_A None, 0 of 17 bins included)
```
In the result JSON, None is written as null (`json.dumps`).

### 3.2 A7-5 derivation re-checked

The Gauss-Legendre remainder R[f] = I[f] - Q[f] is complex-linear, and R maps real functions to
real numbers (real nodes and weights). For complex h, set phi = arg R[h]. Then |R[h]| =
R[e^(-i phi) h], which is real, and it equals R[g] with the real function g = Re(e^(-i phi) h). The
one-point form gives R[g] = C_n g^(2n)(eta), and |g^(2n)| = |Re(e^(-i phi) h^(2n))| <= |h^(2n)|.
Factor 1 therefore suffices, and A7 is right. The code keeps sqrt(2) (instruction: a documentation
change only), which is on the safe side.

## 4. Assertions changed (none weakened)

| test | before (83fa75f) | after | why |
|---|---|---|---|
| test_null_study_readout.py::test_unconverged_last_bin_gives_not_converged | `converged_beyond_A == inc[-1]["d_end_A"]` | `converged_beyond_A is None` AND `last_examined_A == inc[-1]["d_end_A"]` AND the last included bin fails; plus a no-bin-included case (both fields None, "no bin included") | A7-3 contract change. X2's value is still asserted in its own field and E1's None is asserted again, so the test is stronger. |
| test_null_study_readout.py::test_amplitude_floor_... (floor 0) | `r0["converged_beyond_A"] == low[-1]["d_end_A"]` | `is None` AND `r0["last_examined_A"] == low[-1]["d_end_A"]` | same |
| test_null_readout_known_answer.py::test_short_cell_with_the_study_beam_is_not_converged | `converged_beyond_A == inc[-1]["d_end_A"]` | `is None` AND `last_examined_A == inc[-1]["d_end_A"]` | same |
| test_kit_gpu_mem_from_dry_run.py (pipeline report, emulated job) | `schema == ".../2"` | `schema == ".../3"` plus the package-tree hash assertions | A7-4 schema bump (intentional). Schema /2 is now asserted to be REFUSED. |
| test_kit_gpu_mem_from_dry_run.py `_report` | fake reports /2 without a tree hash | /3 with the current tree hash (default) | the fake reports must carry the new field (instruction). Every earlier refusal and acceptance assertion is kept, including K-2 and `--accept-need-below-dry-run`. |

Assertions added: the covariant and excluded-bins tests assert `last_examined_A`; the new engine test
(A7's case); the new kit test (tree versus engine hash, definition equality, file types); the
refusals of another or a missing tree; the tree hash in the submission record and the NOTE line. No
tolerance was changed. No test was deleted or skipped.

## 5. Test runs (verbatim count lines)

Commands, from /home/user/Holography: `venv/bin/python -m pytest -q -p no:cacheprovider -rs
--basetemp=<sp>/pt_<name> <dir>`, run one after the other by `<sp>/run_suites.sh`. The machine was
shared: A8's worktree suite, A8 scripts and a torus run were running, and the load was 13-17 on 4
cores.

| run | UTC, load | result |
|---|---|---|
| tests/forward | 07:01:44-07:30:15, load 13.2 -> 11.4 | `1 failed, 134 passed, 3 skipped in 1708.72s (0:28:28)` |
| tests/hpc | 07:30:15-07:35:26, load 11.4 -> 10.0 | `118 passed, 5 skipped in 309.97s (0:05:09)` (`SKIPPED [5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed`) |
| full suite (`venv/bin/python -m pytest -q`, plus the options above) | 07:35:26-08:04:57, load 10.0 -> 1.6 | `1 failed, 1293 passed, 8 skipped, 12 warnings in 1768.61s (0:29:28)`; skips: `[2] tests/forward/test_null_readout_known_answer.py:225: L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1`, `[1] tests/forward/test_rung2_bragg.py:138: R2-B (r = 0) is optional and qualitative (P2 8.4); RH_RUNG2_R2B=1`, `[5] tests/hpc/test_alliance_kit.py:393: shellcheck not installed` |
| rerun of the failing test alone, `-s` | 08:05:13-08:06:09, load 1.3 | `1 passed in 54.36s`; `SMOKE: build 8.9 s, propagation 45.3 s, total 54.3 s, peak RSS 806 MB` |

Both failures are the same wall-time assertion of the atomistic smoke test. Verbatim:
- tests/forward: `tests/forward/test_smoke_atomistic.py:52: AssertionError`, `E       assert
  148.3391484849999 < 120.0` (`SMOKE: build 11.2 s, propagation 136.6 s, total 148.3 s, peak RSS
  1027 MB`);
- full suite: `E       assert 142.56896668000263 < 120.0` (`SMOKE: build 8.9 s, propagation
  133.4 s, total 142.6 s, peak RSS 1017 MB`).

The machine had 4 cores at load 10-17. Alone, at load 1.3, the same test passes in 54.3 s, and its
remaining assertions (exit plane, finite field, geometry checks, UNVALIDATED status), which the
failing runs never reached, pass too. X3 changed no engine code: the engine hash is c02579f11b77
before and after (section 2.2). The 120 s limit was not changed.

X3 added two test functions: one in tests/forward (the shifted crystal) and one in tests/hpc (tree
hash versus engine hash). The other count changes since A7's 1165 passed at 685e434 come from later
work (E4, E10, torus), which X3 did not audit.

Earlier targeted runs (same command form):
- tests/forward/test_null_study_readout.py: `12 passed in 4.94s`;
- tests/forward/test_null_readout_known_answer.py: `4 passed, 2 skipped in 116.31s (0:01:56)`
  (skips: `L10k study-beam proofs (about 6 min): RH_NULL_READOUT_LONG=1`);
- tests/hpc/test_kit_gpu_mem_from_dry_run.py: `9 passed in 34.07s`, then together with the
  synthetic read-out file `21 passed in 41.64s`;
- tests/optics: `75 passed in 5.83s`.

## 6. NOT RUN

- run_study.py without `--estimate` (any engine run of a study point), so the new verdict print
  line ran only in the evaluation of section 3.1. No study point was run on a GPU or a cluster.
- The optional long proofs (RH_NULL_READOUT_LONG=1, L10k) and R2-B (RH_RUNG2_R2B=1). The code they
  exercise changed only in the distance fields, and they assert `converged` and `== 0.0` on
  converged cases, which are unchanged.
- The kit with a real Slurm, a real GPU, or a real `dry-run` job on a cluster. The kit ran only via
  the fake login node of tests/hpc and the direct `gpu_need_from_dry_run` calls of section 2.2.
- A7's optional NIT (a minimum number of passing bins) and the removal of the sqrt(2) (A7-5 allows
  it, but it is a behaviour change, and the instruction limited A7-5 to documentation).
- Not compared by the kit (out of A7-4's scope): the installed numpy/scipy versions of the dry-run
  job versus the GPU job.
