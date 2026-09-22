# Project subagents

Claude Code loads these definitions automatically for any session on this repository. Each agent is
pinned to a model and an effort level (frontmatter), restricted to the tools it needs, and carries the
project's source policy in its body. The orchestrator (the main session) delegates to them with the
Agent tool and verifies their reports; agents never edit the summary documents directly.

| Agent | Model / effort | Purpose |
|---|---|---|
| physics-deriver | opus / max | derivations with explicit premises, numbers reproduced by a script |
| code-auditor | opus / xhigh | file:line audits of simulation code, synthetic reproduction of defects |
| literature-researcher | opus / xhigh | source retrieval and reading with evidence labels and locators |
| bibliography-verifier | opus / high | DOI and record verification, BibTeX hygiene |
| software-provenance | opus / xhigh | version-matched source reading of engines and wrappers, API checks |
| simulation-runner | opus / xhigh | builds and runs simulations and tests, records provenance manifests |
| adversarial-reviewer | opus / max | independent recomputation and review of documents before they are called final |

Common rules for every agent: write reports incrementally (the container can restart); never invent a
DOI, page, equation or result; label every claim (METADATA_VERIFIED, SECTION_READ, REPRODUCED,
PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED); state what was not read or not run; the beam
energy is 200 keV, never 300 keV; reply to the orchestrator with a summary of at most 400 words and
the path of the full report.
