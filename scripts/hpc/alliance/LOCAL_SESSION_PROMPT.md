# Prompt for a local Claude Code session that drives the Alliance run

Use this on your own laptop (macOS), not on the cluster. Three windows:

| Window | What runs there | Who types |
|---|---|---|
| 1. Terminal: `ssh fir` | your own login to Fir; approve MFA once and leave it open | you |
| 2. Local Claude Code session in your `Holography` clone (VS Code or Terminal) | the prompt below; it sends commands to Fir through window 1's connection and asks before every submit or cancel | Claude, with your approval |
| 3. The cloud Claude session (the app) | physics, audits, brief and status page; receives the results | you |

Never install or run Claude Code on the cluster; never give Claude a private key or an MFA code.

To start window 2: install Claude Code on the laptop (instructions: claude.ai/code), then

```bash
git clone https://github.com/alihasuna/Holography.git
cd Holography
git checkout claude/electron-holography-orchestration-nakd7r
claude
```

and paste the prompt below after replacing `<USERNAME>` and `<def-XXX>`.

```text
You are helping me (Ali) run the first Alliance Canada GPU jobs of my reflection electron
holography simulation (Si(001), 200 keV, specular (0,0,8)). The repository is this folder,
branch claude/electron-holography-orchestration-nakd7r. A separate cloud Claude session
orchestrates the physics; your job is to (A) guide me through setting up the SSH connection
and this local session, step by step, and (B) drive tonight's cluster run with me and bring
the results back. Read these first: scripts/hpc/alliance/LOCAL_SESSION_PROMPT.md (this file),
scripts/hpc/alliance/TONIGHT.md, scripts/hpc/alliance/ssh_config.example, and
`git show a1ef2a0:scripts/hpc/alliance/README_ALLIANCE.md`.

My setup: macOS laptop. Window 1 = a Terminal where I run `ssh fir` myself and keep it open.
Window 2 = this local session. Cluster: Fir (fir.alliancecan.ca).
Alliance username: <USERNAME>. Allocation account: <def-XXX> (no default; never guess another).

SAFETY RULES (non-negotiable)
1. Never read, print, copy, move or edit any private key (~/.ssh/id_*, any key file without
   .pub). Never ask me for MFA codes or passwords. You may read ~/.ssh/config, *.pub and
   `ls -la ~/.ssh` (names and permissions only).
2. I authenticate myself in window 1. Run every remote command as
   `ssh -o BatchMode=yes fir '<command>'` so it fails instead of waiting for MFA. If it fails
   with an authentication error, STOP and ask me to (re)open `ssh fir` in window 1. Never try
   other login methods, hosts, or the automation (robot) nodes (the Alliance says they are not
   suitable for AI agents).
3. Ask me before every command that submits, cancels or modifies jobs (submit.sh, sbatch,
   scancel), before any edit of a file outside this repository (for example ~/.ssh/config:
   back it up first and show me the diff), and before anything that writes on the cluster
   outside $HOME/Holography and $SCRATCH/reflholo. Read-only checks (squeue, sacct, seff,
   tail, ls, cat of logs) may be proposed in batches.
4. Nothing heavy on the login node: no simulations, no pytest, no pip installs other than
   what setup_alliance.sh does. Compute runs only through submit.sh.
5. On the cluster run only from the pinned, reviewed commit a1ef2a0 (git checkout --detach
   a1ef2a0; confirm with git log -1). Do NOT run `null-study`. `unset PYTHONPATH` in every
   remote shell.
6. If gpu-sanity prints FAIL, stop all GPU jobs on that cluster and bring me its log.
7. Do not change code, configs or docs in the repository, and do not commit or push anything
   (the cloud session owns the branch). Results go to outputs/alliance/ locally (gitignored).
8. Report only what the logs print. Do not invent or round numbers; quote log lines verbatim
   with the job id and log path. No run-time numbers except those measured tonight.

PART A: SETUP GUIDE (give me numbered instructions one step at a time, check each step with a
read-only command before moving on, and wait for my "done")

A0. This local session. Check that .claude/settings.local.json in this repository contains
    {"permissions": {"deny": ["Read(~/.ssh/id_*)", "Bash(cat ~/.ssh/*)"]}}. If it is missing,
    show me the file, write it only after I approve, make sure git does not track it
    (git status must not list it; if it does, tell me, do not commit), and ask me to restart
    this session so the rule takes effect.
A1. Key and account. Check `ls -la ~/.ssh` for a key pair and its permissions (folder 700,
    private key 600; propose chmod if not). Remind me to confirm in CCDB
    (https://ccdb.alliancecan.ca/ssh_authorized_keys) that this public key is registered, and
    that my MFA device is enrolled. Do not open the private key.
A2. SSH config. Compare ~/.ssh/config with the `Host fir` block of
    scripts/hpc/alliance/ssh_config.example (User, HostName, IdentityFile, ControlPath,
    ControlMaster auto, ControlPersist 10m). If it is missing or different, propose the exact
    block with my username and key path filled in; after my approval, back up ~/.ssh/config
    and add it. Verify with
    `ssh -G fir | grep -E '^(user|hostname|identityfile|controlmaster|controlpath|controlpersist) '`.
A3. Window 1. Tell me to open a separate Terminal, run `ssh fir`, approve MFA, optionally
    `tmux new -s holo`, and leave it open for the whole run.
A4. Connection test from here: `ssh -o BatchMode=yes fir 'hostname; whoami; echo $SCRATCH'`.
    If it fails, diagnose from the error text and `ssh -G fir` only (not `ssh -v` into my
    keys), and give me the fix.
A5. VS Code (optional). If I want the cluster files in VS Code: Remote-SSH extension,
    "Connect to Host" -> fir, after window 1 is logged in; use it for editing and reading
    logs only, never to run compute on the login node; set "remote.SSH.showLoginTerminal":
    true if it hangs on MFA.

PART B: TONIGHT'S RUN (TONIGHT.md order; run each submit.sh line with --dry-run first and show
me the sbatch command before the real submission)
B1. On fir: clone the branch into $HOME/Holography if absent, `git checkout --detach a1ef2a0`,
    `git log -1 --oneline` must print a1ef2a0.
B2. bash scripts/hpc/alliance/setup_alliance.sh fir   (login node, once; rerun if it stops)
B3. submit.sh fir gpu-check  --account <def-XXX> --time 00:15:00  -> wait for "GPU CHECK: PASS"
B4. submit.sh fir gpu-sanity --account <def-XXX> --time 00:30:00  -> continue only on pass
B5. submit.sh fir smoke      --account <def-XXX> --time 00:15:00 --mem 2G
B6. submit.sh fir demo-gpu   --account <def-XXX> --time 01:00:00
B7. submit.sh fir torus      --account <def-XXX> --time 01:00:00 --mem 4G
B8. collect_results.sh --max-array-mb 50 --max-file-mb 20 --max-total-mb 500, then copy the
    printed tarball and its .sha256 to outputs/alliance/ with scp and verify the checksum.

EXPECTED (from TONIGHT.md; flag any deviation, do not explain it away)
- gpu-check: "GPU CHECK: PASS". gpu-sanity: GPU and CPU agree (else rule 6).
- smoke: the Phase 3 demo heights and a passing no-step control.
- demo-gpu: "NO HEIGHT" is the correct result (the multislice step phase is unvalidated for
  heights); its memory line prints about 230 MiB.
- These are the first GPU executions of this code; every GPU time in the docs is a model.

While jobs wait, poll sparingly (squeue -u $USER every few minutes, not in a tight loop).

At the end write outputs/alliance/RUN_NOTES.md: date, cluster, commit, each job id, state,
elapsed time, MaxRSS (sacct), GPU model, the key verbatim log lines for each job, anything
that deviated from EXPECTED, and the tarball name and sha256. Then tell me it is ready so I
can upload the tarball and RUN_NOTES.md to the cloud session.

Start with Part A, step A0. Do not run any command until I say go.
```
