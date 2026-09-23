# A3b: Re-audit of the S4 fixes for audit A3 (and A2c G1-G3 and the visibility residual)

Status: FINAL, 2026-09-23. Auditor: A3 (re-audit). No code was modified. A3
(`docs/agent_reports/A3_pipeline_audit.md`) was not edited.
Scratch: `/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/audit3b/`
(written `$T` below). A3's own scripts live in `.../scratchpad/audit3/` (`$S`).

Scope. The re-audited change set is `git diff 281074a 7bdfb79 -- reflection_holo tests configs scripts`.
The fix report is `docs/agent_reports/S4_pipeline_fixes.md`.

Repository state. HEAD moved during the re-audit (cb2eff0, then 2f40c9a, then c10ebf3). Since
7bdfb79, `git diff --stat 7bdfb79 HEAD -- reflection_holo tests configs scripts` shows only the new
`reflection_holo/structure/shapes.py`, and `pipeline/` does not import it. Every re-audited file is
therefore identical to 7bdfb79.

## For Ali tonight: what could still print a wrong number

1. The multislice HPC demo (`configs/demo_hpc_si001.yaml`) cannot print a height tonight.
   * The open reflection cell has K = 2 steps (a/2 up, a/4 down); the boundary step is absent, as
     `multislice_tiny` confirms.
   * With the declared 0.1 mrad angle calibration, the new joint rule is significant for K = 2 only
     if sigma_phi <= 0.00090 rad per step (`$T/hpc_k2.py`).
   * At sigma_phi = 0.003 rad the chance bound is already 9.06e-3, above alpha = 2.70e-3. P1's run
     had phase errors of about 0.1 rad.
   * A failed or unperformed no-step control now withholds every height.
   * Expected first result line: `NO HEIGHT: ...`. This is the correct outcome, not a fault.
   * S4's closing section assumes three steps at B32. That is wrong (N2), but the conclusion "no
     height" holds even more strongly.
2. The smoke demo prints correct heights: +2.7156 +- 0.0165, -1.3576 +- 0.0082 and -1.3580 +-
   0.0082 A, reproduced by me. The number printed next to them, "chance-acceptance bound
   0.000122", is wrong: the true chance rate is 2.0e-3, 17x larger (N1). The heights and their
   uncertainties are unaffected.
3. The SLURM runner no longer dies under `PYTHONUNBUFFERED=1` (0 of 8 failed). It refuses a missing
   `.git` (exit 2) and a missing cupy or GPU in the job (exit 4, in 0.2 s). Check two things on the
   cluster:
   * `bash --version` must be >= 4.4 (N4, NOT RUN here).
   * Every job manifest will read `dirty: true`. The job's own `reflholo_*` files in the repository
     root cause this, not a code change (N3).

## Verdicts

| Finding | Verdict | Evidence (rerun of the A3 reproduction unless stated) |
|---|---|---|
| B1 control gate | FIXED | `$T/repro_nostep.py 0.001` and `0.002`: the control fails (-0.0191 against 0.0169; -0.0360 against 0.0236) and every step says "no height: no-step control failed ... every height of this run is withheld". The CLI prints the NO HEIGHT verdict first. |
| B1 branch rule (joint) | FIXED with a new problem (N1) | Uniform single phases are never resolved. True lattice steps: 0 wrong of 20000 at the smoke sigma, 1.5e-4 at 4.5x (`$T/mc_wrong.py`). The printed chance bound is 17x too optimistic for runs with the closing step (N1). |
| M1 R2 | FIXED | `$T/repro_r2.py`: both shifts give "no height: R2 self-reference ... DIFFERENTIAL ...". The rule also excludes n = 0. |
| M2 comparison gate | FIXED | `$T/repro_comparison.py`, detailed below. |
| M3 correlated angle error | FIXED | The smoke run prints +2.7156 +- 0.0165 A and +- 0.0082 A (I expected 0.0165 and 0.0082); sigma_s = 0.0500997 rad/A = 2 k cos(theta) sigma_theta. The branch window uses the same sigma_s. Residual nit N7. |
| M4 SLURM pipefail (fdabd67) | FIXED; new minor N3 | 8 simulated smoke jobs with `PYTHONUNBUFFERED=1` all exit 0 (`$T/job_smoke_*`). The dry-run goes to a file, `head` reads the file, and `__main__._entry` handles `BrokenPipeError`. |
| M5 no `.git` | FIXED | `$T/nogit`: exit 6 in 0.29 s ("REFUSED (git state, before any computation)"), with no output directory. `--allow-no-git` records the error, `allowed_without_git` and a `package_tree` SHA-256 over 65 files. The SLURM script checks `git rev-parse` in both modes. |
| M6 inputs not represented | FIXED | `$T/repro_m6.py`: refused on both engines are convergence 0.5 mrad, an SiO2 overlayer, a pattern mesa, `{features: []}` and a target (0,0,12) with the (0,0,8) rule. With a typed angle, the item-9 value is listed "SUPPLIED, NOT USED on this path" with its reason. |
| m1 purpose everywhere | FIXED | `arrays.npz["purpose"]` = "demo; not comparable to experiment". The engine manifest records the config path and hash, the input and `extra.caller` (purpose, variant, test_only). |
| m2 list-inputs item 20 | FIXED | HPC config: `cfg_b.mean_inner_potential_V 12.0` is "NOT USED on this path", and `potential_mip 13.903` is "REPRODUCED, USED". |
| m3 in-crystal field | PARTLY FIXED | A_emp now uses lit pixels only (0.09158 changed to 0.09476 in `multislice_tiny`), and amplitude per trace status is recorded. NOT FIXED: the in-crystal field still enters the aperture unmasked (below-surface mean \|obj\| 0.094 against lit 0.069), and the engine band-limit check (`darkfield.py:149-153`) is still inert, because no engine sets `band_limit_cycles_per_A`. |
| m4 B32 sign degeneracy | FIXED (note) | `quantification.sign_degeneracy` exists and the CLI prints the note. S4's claim that "both a/4 steps" pin the sign does not apply to the HPC multislice demo, which has one a/4 step (N2). |
| m5 cupy/GPU pre-flight | FIXED | HPC `dry-run` without cupy runs the geometry checks, then exits 4 ("multislice backend cupy NOT available"). `run()` calls `require_engine` first. The SLURM job exits 4 in 0.2 s; submission only warns. |
| m6 SLURM robustness | FIXED; new minor N3 | Launching from another directory with `RH_REPO` exits 0. `SLURM_CPUS_PER_TASK=4` against threads 8 exits 2. A failed run now reaches "finished with status 5". |
| m7 run_study.py | FIXED | `load_yaml_unique`, refuses before computing when a result exists, `open(...,"x")`, and purpose plus `test_only` in every result and manifest (read; no study point computed). |
| m8 exit codes | FIXED; nit N5 | The B4 refusal via CLI (`$T/b4_110.yaml`, azimuth [1,1,0]) exits 3 with "REFUSED (model scope B4, configuration)". |
| n2, n3 | FIXED | Docstrings updated; `arrays.npz` is opened with "xb". n1, n5, n6 and n7 were not done, as S4 states. |
| A2c G1 | FIXED | `$T/repro_g.py`: CFG-A with surface [0,0,1] or [-1,1,-1], or azimuth [1,-1,0], is refused (PINNED). |
| A2c G2 | FIXED with a residual (N6) | Structured `supplied_by` / `supplied_on`; future dates are refused (09-24 refused, 09-23 accepted). The denylist lets through "TBD by Ali", "Ali (not yet supplied)", "?" and "n.a.". |
| A2c G3 | FIXED | A TEST_ONLY configuration handed to `run()` is refused before the output directory is created. |
| Visibility residual (reference_correction "none") | FIXED | Without `object_min_visibility` the gate refuses. With 0.3 the run gives +2.7156, -1.3577 and -1.3579 A. |

Comparison gate detail (`$T/repro_comparison.py`; supplies fabricated as `supplied_by: Auditor`):

| Case | Result |
|---|---|
| (a) A3 reproduction: blocking stand-ins supplied, rule-form angle labelled PROJECT_INPUT from B1 | refused ("computed angle cannot carry the label PROJECT_INPUT") |
| (a2) as (a) but with a typed supplied angle, demo stand-ins B24/B28/B29/B31/B27 left | refused ("refuses every demo stand-in (B19 ... B32)") |
| (b) every demo stand-in supplied, rule angle from B1 | refused |
| (c) as (b) with a typed angle | passes |
| (d) as (c) with `--variant multislice_tiny` (nested B30, variant-level B25 and B32) | refused |
| (e) dose relabelled ASSUMPTION B1 | refused (not registered for item 6) |
| (f) purpose demo, rule-form angle labelled PROJECT_INPUT | refused |

In case (c) the remaining ASSUMPTIONs are B2 (lattice parameter), B1 (V0, not used with a typed
angle), B17, B18 and B5 (reference model). All of them are listed in
`summary["assumptions_in_use"]`.

## New problems

### N1 (Major for geometric R1 runs; not tonight's multislice run). The chance bound assumes independent step phases, but the closing step is fixed by the other two, so noise is certified at up to 3.6 alpha

* Where:
  * `pipeline/quantify.py`: `chance_probability_bound` (the product over steps) and
    `lattice_branch` ("resolved" if `p_chance <= alpha`).
  * `pipeline/run.py:_field_steps` adds the non-adjacent pair (F-1, 0) for a periodic upstream
    with R1.
* What is wrong:
  * All step phases come from the same region medians. The closing step therefore satisfies
    phi_01 + phi_12 + phi_20 = 0 (mod 2 pi) exactly. The smoke run's summary gives -0.0.
  * A lattice assignment with n_3 = -(n_1 + n_2) is then satisfied automatically.
  * The bound nevertheless multiplies in a third box factor of about 0.01. For "phases carrying no
    height information", the correct null model is three region medians uniform on the circle,
    not three independent step phases.
* Reproduction (`$T/mc_dependent.py 200000`; the pipeline's own `lattice_branch`; the smoke run's
  s, sigma_s and sigma_phi):
  ```
  pipeline chance bound (assumes 3 independent phases): 0.00012153982377578622  alpha: 0.0026997960632601913
  dependent (pipeline geometry: 3 region medians): N=200000 {'inconsistent': 199591, 'resolved': 409}  resolved rate 2.04e-03 (bound 1.22e-04, alpha 2.70e-03)
  independent triples (the bound's model): N=200000 {'inconsistent': 199979, 'resolved': 21}  resolved rate 1.05e-04 (bound 1.22e-04, alpha 2.70e-03)
  ```
  With sigma_phi scaled by f (a lower dose; `$T/mc_dependent_scale.py 100000 ...`):
  ```
  f= 1.5 sigma_phi~0.0040 rad: printed bound 2.75e-04 (<= alpha 2.70e-03); true 'resolved' rate for no-information region medians 3.24e-03 +- 1.8e-04 (1.20 alpha)
  f= 2.0 sigma_phi~0.0054 rad: printed bound 4.90e-04 (<= alpha 2.70e-03); true 'resolved' rate ... 4.35e-03 +- 2.1e-04 (1.61 alpha)
  f= 3.0 sigma_phi~0.0081 rad: printed bound 1.11e-03 (<= alpha 2.70e-03); true 'resolved' rate ... 6.22e-03 +- 2.5e-04 (2.30 alpha)
  f= 4.0 sigma_phi~0.0108 rad: printed bound 1.99e-03 (<= alpha 2.70e-03); true 'resolved' rate ... 8.82e-03 +- 3.0e-04 (3.27 alpha)
  f= 4.6 sigma_phi~0.0124 rad: printed bound 2.65e-03 (<= alpha 2.70e-03); true 'resolved' rate ... 9.69e-03 +- 3.1e-04 (3.59 alpha)
  ```
  Examples of "resolved" heights from phases with no information: [+1.3512, +1.3519, -2.7031] A and
  [-2.748, +1.3748, +1.3731] A.
* Who is affected: every geometric run with transverse edges and a periodic upstream under R1. That
  covers the smoke demo, the `geometric_same_structure` variant and the R1 "none" case above.
* Who is not affected:
  * Open multislice cells, where K independent steps follow from K + 1 regions and the bound is
    valid for a uniform null.
  * True lattice steps: 0 wrong assignments in 20000 at the smoke sigma, and 1.5e-4 at 4.5x
    (`$T/mc_wrong.py`).
* Why the tests miss it: `test_three_random_phases_are_refused_at_the_three_sigma_rate` draws
  independent triples.
* Fix: compute the bound over the independent region differences, e.g. exclude the closing step
  from the product (K_eff = number of regions - 1), or leave it out of the joint rule. Add a test
  with dependent (region-median) nulls.
* A further limit, not new: the bound covers only a uniform null. Structured wrong phases (the
  multislice artefact) are guarded by the no-step control, not by the bound.

### N2 (Minor). S4's statements about tonight's run assume three steps at B32

S4 ("What tonight's HPC run will do", and m4) quotes three-step bounds and says two a/4 steps pin
the a/2 sign. The HPC multislice cell has two steps (the ms_tiny summary lists 0->1 and 1->2), and
for K = 2 the bound exceeds alpha unless sigma_phi <= 0.00090 rad (`$T/hpc_k2.py`: 9.06e-3 at
0.003 rad, 3.12e-2 at 0.01 rad). The printed outcome is still "NO HEIGHT". The README_HPC text
should say so.

### N3 (Minor). The SLURM runner writes `reflholo_<job>_dryrun.txt` into the repository root, which makes every job manifest "dirty", and it copies files into another run's directory

* Where: `scripts/hpc/run_pipeline.slurm:137-152`. `.gitignore` ignores neither `reflholo_*.txt`
  nor `reflholo_*.log`; the `#SBATCH --output` log also lands in the root, a pre-existing issue.
* Reproduction (a local clone, `$T/clone`, venv excluded through `.git/info/exclude`):
  ```
  manifest repository: dirty True untracked ['reflholo_6001_dryrun.txt', ..., 'reflholo_6008_dryrun.txt']
  ```
* A job refused for a non-empty `RH_OUT` (exit 5) still runs `cp "$DRYRUN_TXT" "$OUT/"` into the
  other run's directory: `$T/job_smoke_1` now contains `reflholo_7003_dryrun.txt`.
* Fix: write the dry-run text under a job-specific scratch or output directory, add `reflholo_*`
  to `.gitignore`, and copy only when this job created `$OUT`.

### N4 (Minor, pre-existing, NOT RUN). Under bash < 4.4, `set -u` plus empty arrays kills the job

`"${VARIANT_ARGS[@]}"`, `"${NOGIT_ARGS[@]}"` and `"${GRES[@]}"` are empty in the default runs
(lines 119, 134, 139, 148). Bash before 4.4 (e.g. RHEL/CentOS 7, bash 4.2) raises "unbound
variable" for an empty array under `set -u`. The job would then exit 1 at line 134 before the
run. It gives no result rather than a wrong one. This sandbox has bash 5.2, so this is untested.
Fix: `${VARIANT_ARGS[@]+"${VARIANT_ARGS[@]}"}`, or check the bash version.

### N5 (Nit). `__main__._entry` maps any BrokenPipeError to exit 0

The handler cannot tell a closed stdout from a BrokenPipeError raised inside the computation, so
it would report success with no outputs. Catch it around stdout writes only, or check `sys.stdout`.

### N6 (Minor). G2 is still a denylist

`check_supply` accepts `supplied_by` values of "TBD by Ali", "Ali (not yet supplied)", "?" and
"n.a.", and dates such as 1900-01-01 (`$T/repro_g.py`). Structured fields cannot prove a supply,
but these placeholders are cheap to refuse (non-alphabetic names; "tbd", "not yet" anywhere).

### N7 (Nit). The step heights of one run share a fully correlated scale error, and this is not stated

sigma_h per step is right, but averaging the two a/4 heights with sigma/sqrt(2) would understate
the angle part. Record the correlation, i.e. the common `h sigma_s/s` term.

### N8 (Nit). The value of a stand-in is not checked against its assumption row

B20 ("exact [100]") with the value [1,1,0] passes the gate. The engine's B4 check then refuses the
run (exit 3), after creating an empty output directory.

## Tests

* Full suite (my run): `724 passed, 12 warnings in 242.01s`. The suite left no stray files in the repository.
* The new tests check what they claim, except N1, where the null model has independent phases.
* The multislice tests assert exit 4 only because this machine has no cupy. The path with cupy
  present is NOT RUN, here and in S4.

## Commands run (repository root unless stated)

```
git log --oneline -15; git diff --stat 281074a 7bdfb79 -- reflection_holo tests configs scripts; git diff --stat 7bdfb79 HEAD -- ...
git diff 281074a 7bdfb79 -- <quantify.py, run.py, config.py, height.py, io/config.py, registry, engines.py, __main__.py, estimates.py, run_study.py, multislice/engine.py, optics>
venv/bin/python -m reflection_holo.pipeline run --config configs/demo_smoke_si001.yaml --out $T/smoke          (exit 0; heights above)
venv/bin/python -m reflection_holo.pipeline run --config configs/demo_smoke_si001.yaml --variant multislice_tiny --out $T/ms_tiny   (exit 0; NO HEIGHT, not performed)
venv/bin/python -m reflection_holo.pipeline list-inputs --config configs/demo_hpc_si001.yaml   (exit 0)
venv/bin/python -m reflection_holo.pipeline dry-run --config configs/demo_hpc_si001.yaml       (exit 4, cupy absent)
venv/bin/python -m reflection_holo.pipeline run --config $T/b4_110.yaml --out $T/b4_out         (exit 3)
venv/bin/python $T/{repro_nostep.py 0.001|0.002, repro_r2.py, repro_comparison.py, repro_m6.py, repro_g.py,
  mc_dependent.py 2000|200000, mc_dependent_scale.py 100000 1.5 2 3 4 4.6, mc_wrong.py 20000 1 3 4.5, hpc_k2.py}
PYTHONPATH=$T/nogit venv/bin/python -m reflection_holo.pipeline run ... [--allow-no-git]   (exit 6; exit 0)
git clone /home/user/Holography $T/clone; PATH=$T/fakebin:$PATH bash scripts/hpc/run_pipeline.slurm  (submission; job mode x8
  with PYTHONUNBUFFERED=1; cupy job; another cwd; SLURM_CPUS_PER_TASK=4; non-empty RH_OUT)
venv/bin/pytest -q -p no:cacheprovider      (724 passed, 12 warnings, 242 s)
```

## NOT RUN

* The HPC multislice run itself, a real `sbatch`, and anything with cupy present.
* Bash 4.2 (N4).
* `setup_env.sh`.
* `run_study.py` study points.
