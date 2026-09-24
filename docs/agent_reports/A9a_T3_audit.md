# A9a: audit of T3 (buried torus void in Si(001), reflection multislice demo)

Auditor A9a, 2026-09-24. Branch claude/electron-holography-orchestration-nakd7r. HEAD when the audit
started: 4c4a78b; the orchestrator committed ebb9ec7 (B42 gate, row B42) and db376ce (snapshot of
this draft) during the audit. Nothing in the repository edited by A9a except this file; nothing
committed; nothing written under outputs/. Scratch: SP/a9a/ with
SP = /tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad; T3's
run outputs are SP/buried/.
Status: IN PROGRESS (written incrementally).

## 0. Command log (every command run by A9a; anything not listed was NOT RUN)

C1. `git status; git log --oneline | head -30` (tree clean after ebb9ec7/db376ce).
C2. `git show --stat b96bc6e 39b6151 4c4a78b`; `git diff 39b6151 4c4a78b -- reflection_holo/...`
    (engine.py, cell.py, overlayer.py, si001.py, assumption_registry.yaml, tests/io);
    `git diff 4c4a78b ebb9ec7 -- reflection_holo/pipeline/config.py tests/pipeline/test_pipeline_feature.py`.
C3. Manifest provenance of the 7 runs: python one-liner over SP/buried/ms_*/outputs/manifests/*.json
    (commit, dirty, diff_head_sha256, untracked_sha256, package_tree.sha256, timestamps).
C4. Package-tree hash of committed trees: `git archive <c> reflection_holo | tar -x -C SP/a9a/tree_<c>`
    for 39b6151, 4c4a78b, ebb9ec7, HEAD, then
    `reflection_holo.provenance.manifest.package_tree_sha256(SP/a9a/tree_<c>)`.
C5. `venv/bin/python SP/a9a/causality.py` -> SP/a9a/causality.out (independent refraction law and
    section 4.1 numbers; physical constants hard-coded, no repository physics imported).
C6. `venv/bin/python SP/a9a/geometry_check.py` -> SP/a9a/geometry_check.out (independent torus rule
    on the saved structure files; 37 s).
C7. Read the five PNGs in SP/buried/figures/ and SP/buried/figures/analysis_output.txt in full.

## 1. Findings (ranked; filled in as the audit proceeds)

(pending)

## 2. Item-by-item record

### Item 1. Geometry (verified, no defect)

C6 output (verbatim excerpts, SP/a9a/geometry_check.out):

```
flat r010 == flat r000 bitwise: True ; cells equal: True
flat atoms 1102896; top plane x = 99.113925 A; layers 74; Ly 146.6343 Lz 1498.9284
cap 5 r010: ... removed == own-rule set: True (own rule 7166); feature_sites == removed rows: True
   removed x_rel range [-28.5122, -5.4309] A (void [-29.0, -5]); any removed at x_rel >= -cap: False; layers with x_rel >= -cap (4) complete: True
cap 10 r010: ... True (own rule 7083) ... removed x_rel range [-33.9431, -10.8618] ... (8) complete: True
cap 20 r010: ... True (own rule 7123) ... removed x_rel range [-43.4472, -20.3659] ... (15) complete: True
cap 30 r010: ... True (own rule 7031) ... removed x_rel range [-52.9513, -31.2277] ... (23) complete: True
cap 10 r000: ... identical to cap 10 r010
```

The own rule is distance to the circle (rho = 50, x_rel = -(cap + 12)) < 12 A with x_rel measured
from the TOP atomic plane (max x of the flat atoms), not the equivalent boundary: the removed sets
are exactly that rule's sets, bitwise; no site is removed at x_rel >= -cap; every cap layer is
complete; every cap-run atom is a bitwise row of the flat structure, and the two flat structures
(r010, r000) are bitwise identical. The analysis's own assertion (flat = cap + void,
tools/plots/buried_torus.py:150-153) is therefore confirmed independently. No site lies within
1e-6 A of the wall (smallest kept-atom margin 3.0e-5 A at cap 30), so no rounding convention can
flip a site. DERIVED_HERE (C6).

Quantisation note (feeds finding n-1): the first REMOVED layer lies at 5.43, 10.86, 20.37, 31.23 A
below the top plane (last intact layer 4.07, 9.50, 19.01, 29.87 A), so the lattice cap differs
from the nominal cap by 0.4 to 1.2 A, not by a constant.

### Item 3. Causality numbers (verified)

C5 output (SP/a9a/causality.out), refraction law k cos(theta_ext) = k_in cos(theta_int), relativistic
k(T) = sqrt(T (T + 2 m c^2)) / (h c), internal Bragg condition 2 k_in sin(theta_int) = 8/a:

```
V0 = 13.903 V (task): lambda = 0.025079 A, theta_int = 18.4719 mrad, theta_ext = 16.1347 mrad, 1/tan(theta_int) = 54.130, tan(out)/tan(int) = 0.8735
L_z 1526.0829, ring z 965.1545-1089.1545; crystal after ring 436.93-560.93 A
  cap 5: surfacing distance of void top 270.65 A ... cap 10: 541.30 ... cap 20: 1082.60 ... cap 30: 1623.90
max depth reaching vacuum before exit plane: 8.072-10.363 A
first contact z 61.973 A (bottom edge, zero amplitude); full amplitude contact 185.918 A
illumination reach at ring 16.685-18.976 A, exit 27.048 A
projected ring x_rel 7.050-9.051 A
```

Every number of T3 section 4.1 (18.472 mrad, 54.1 t, 437-561 A, 8.1-10.4 A, 16.7-19.0 A, 27.0 A,
P at 7.05-9.05 A, -0.87 t) is reproduced independently of the engine. They are two-beam
characteristic (Takagi-Taupin region-of-influence) statements; whether they bound the ENGINE is a
separate question (finding M-1).
