# Tonight's run sheet (Alliance clusters), pinned to commit a1ef2a0

Reviewed state: the kit and engine at commit `a1ef2a0` passed the re-audit
`docs/agent_reports/H4b_kit_reaudit.md` ("ready for tonight's job list, under conditions"). The branch tip
moves while other work continues and is NOT reviewed for cluster use: always run from `a1ef2a0`.
The commands and their options are those of `scripts/hpc/alliance/README_ALLIANCE.md` at `a1ef2a0`
(read it there for details: `git show a1ef2a0:scripts/hpc/alliance/README_ALLIANCE.md`).

## Conditions (H4b)

1. Right after cloning, check out `a1ef2a0` and confirm with `git log -1`.
2. Do NOT run `null-study` (its cells are shallower than the extinction depth; being redesigned).
3. If `gpu-sanity` prints FAIL on a cluster, stop all GPU jobs on that cluster and bring back its output.
4. `PYTHONPATH` must be empty in the login shell (`unset PYTHONPATH`); an exported one overrides the venv.
5. `demo-gpu` prints about 230 MiB in its memory line (the README's 127 MiB predates the corrected
   memory model of report H7).

## Cluster

Fir first (4 x H100 80 GB per node, 7 days max walltime; report H1). Nibi or Rorqual are equivalent
alternatives (H100 80 GB); Narval (A100 40 GB) also fits every job below. Trillium: GPU login node only,
and `torus` is not supported there.

## Commands (replace `def-XXX` by your allocation; there is no default)

```bash
ssh fir                                   # MFA; ssh config example: scripts/hpc/alliance/ssh_config.example
unset PYTHONPATH
cd $HOME
git clone --branch claude/electron-holography-orchestration-nakd7r https://github.com/alihasuna/Holography.git Holography
cd Holography
git checkout --detach a1ef2a0 && git log -1 --oneline      # must print a1ef2a0

bash scripts/hpc/alliance/setup_alliance.sh fir             # once per cluster, login node; rerun the same command if it stops

bash scripts/hpc/alliance/submit.sh fir gpu-check  --account def-XXX --time 00:15:00
#   wait for "GPU CHECK: PASS" at the end of $SCRATCH/reflholo/logs/gpu-check_<jobid>.log  (squeue -u $USER)
bash scripts/hpc/alliance/submit.sh fir gpu-sanity --account def-XXX --time 00:30:00
#   continue only if it passes (condition 3)
bash scripts/hpc/alliance/submit.sh fir smoke      --account def-XXX --time 00:15:00 --mem 2G
bash scripts/hpc/alliance/submit.sh fir demo-gpu   --account def-XXX --time 01:00:00
bash scripts/hpc/alliance/submit.sh fir torus      --account def-XXX --time 01:00:00 --mem 4G

bash scripts/hpc/alliance/collect_results.sh --max-array-mb 50 --max-file-mb 20 --max-total-mb 500
#   prints the tarball path under $SCRATCH/reflholo/collect/; copy it (and its .sha256) to your laptop
```

Add `--dry-run` to any `submit.sh` line to see the sbatch command without submitting.

## What to expect

* `smoke` (geometric engine): the demo heights of the Phase 3 smoke test and a passing no-step control.
* `demo-gpu` (multislice): "NO HEIGHT". This is correct: the multislice step phase is UNVALIDATED for
  heights (rung-2 and independent-solver checks are in progress on the branch, not in a1ef2a0).
* `gpu-check` and `gpu-sanity`: the first GPU executions of this code. No GPU runtime has been measured;
  every GPU time quoted in the reports is an assumption model.

Send the tarball back; it goes to `outputs/alliance/` (gitignored) and into the next report.
