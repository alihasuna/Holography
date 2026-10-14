# Running the M2 reflection-multislice campaign on Fir

Fir (Alliance, Simon Fraser University) GPU nodes have 4 NVIDIA H100 SXM5 80 GB GPUs,
48 cores (one AMD EPYC 9454) and 1 TB of memory each. The campaign uses one full GPU
node per stage job, one worker process per H100. What the campaign computes and why is
in `docs/08_fir_simulation_campaign.md`.

## 0. Things to check once on Fir (not verifiable from outside the cluster)

* The Slurm GPU type string. The scripts request `--gpus-per-node=h100:4`. If Fir uses
  another name, edit the `#SBATCH --gpus-per-node` lines in `selftest.sbatch` and
  `run_stage.sbatch`. The Alliance page "Using GPUs with Slurm" lists the type
  specifiers.
* The module versions in `fir/env.sh` (`python/3.11`, default `cuda`). Override them
  with `RH_PYTHON_MODULE` and `RH_CUDA_MODULE` if needed. `module spider cuda` lists
  the installed versions.
* Your allocation name, for example `def-<pi>` or `rrg-<pi>-ac`. Every submission
  requires `FIR_ACCOUNT`; the scripts refuse to run without it.

## 1. One-time setup (login node, internet available)

```bash
git clone <this repository> && cd Holography
git checkout trixode-studios-claude/sweet-carson-2grkn2
bash fir/setup_env.sh                  # virtualenv in ~/envs/reflection_holo
source fir/env.sh && python -m pytest -q -m "not slow"     # CPU unit tests (seconds)
```

## 2. Submit the whole chain

```bash
export FIR_ACCOUNT=def-<pi>
bash fir/submit_campaign.sh $SCRATCH/rh_m2_v1
```

This plans every task (a dry geometric check that fails before anything is
submitted if a window, detector line or memory budget is inconsistent). It records
the repository commit, the configuration and `pip freeze` in the run directory. Then it
submits five dependent jobs:

| Job | Resources | Walltime requested | What it does | Gate |
|---|---|---|---|---|
| selftest | 1 H100 | 1 h | CPU unit tests; numpy versus CuPy equivalence (static and frozen-phonon task, tolerance 1e-9); throughput benchmark; cost estimate per stage written to `cost_estimate.txt` | fails if CPU and GPU disagree |
| validation | 4 H100 | 3 h | validation ladder at production sampling (rung 1 Fermi step, rung 2 laterally averaged crystals, rung 3 null tests, beam independence); 36 tasks | fails unless every check passes (`configs/benchmarks.yaml`) |
| convergence | 4 H100 | 12 h | sampling, delay, tail-tolerance, absorber and phonon-cell variants; 172 tasks | fails unless the refinements agree with production numerics |
| rocking | 4 H100 | 24 h | complex specular rocking curves, 7 to 45 mrad, three surfaces, all terraces, static / Debye-Waller / 64 frozen phonons, absorption and parametrisation scans; 1892 tasks | none |
| steps | 4 H100 | 24 h | steps parallel to the beam every 1 mrad (angle-resolved), steps across the beam with 30/60/120 A beams, 10 nm mesa edge, 32 frozen phonons at the Bragg conditions; 859 tasks | none |

The provisional estimate, with assumed rather than measured H100 throughput, is about 81
GPU-hours at the planned cell lengths, roughly 20 h of wall time on one 4 x H100 node.
The adaptive stop can lengthen individual runs. Once the self-test has run,
`cost_estimate.txt` gives the measured estimate. Each stage resubmits itself when its time
runs out (section 3), so the walltimes need not cover a whole stage.

## 3. Restarting, resubmission and monitoring

* Every task writes `results/<stage>/<task_id>.h5` atomically, so finished tasks are
  never recomputed. A resubmitted stage skips them.
* If a stage job reaches its time limit with tasks left, it resubmits itself, up to
  `RH_MAX_RESUBMIT=8` times, and moves the next stage's dependency to the new job.
* A task that fails twice is skipped. Its traceback is in `failed/`.
* Progress: `python -m reflection_holo.worker status --run-dir $RUN --stage rocking`.
  Worker logs are in `$RUN/logs/`, job logs in `rh-*-<jobid>.out`.
* To rerun one stage by hand:
  `sbatch --account=$FIR_ACCOUNT --time=04:00:00 fir/run_stage.sbatch $RUN rocking`.

## 4. Outputs

```
$RUN/
  tasks_<stage>.jsonl          every task, fully specified (physics with evidence labels)
  results/<stage>/*.h5         one file per task: result, task JSON and run manifest
                               (git commit, package versions, GPU, seeds, input hashes)
  summary/<stage>/summary.json numbers and verdicts; arrays.npz; PNG figures
  benchmark.json, gpu_info.txt, cost_estimate.txt, pip-freeze.txt, repository_commit.txt
```

Storage needs are about 15 GB for rocking and 20 GB for steps. `$SCRATCH` is fine while
the campaign runs. Copy `summary/` and the `.h5` files to `$PROJECT` afterwards, because
scratch is purged.

## 5. Bringing the results back

Copy `summary/` (small) back into the repository under `results/fir_m2_v1/`. Keep the
`.h5` files on `$PROJECT`. The summary JSON files are the inputs for the comparison
documents. Every number in them traces to a task file and a manifest.
