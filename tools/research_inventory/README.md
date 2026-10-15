# Research-folder tools

Make sense of a large research folder (books, papers, results, simulations) in steps, from free to
paid. Nothing is ever moved, renamed or deleted by these tools.

| Step | What | Cost | Status |
|---|---|---|---|
| 1. Inventory | `inventory.py`: every file with its type, size, date and duplicates; PDF page counts, titles, DOIs and first text | free, local | ready |
| 1b. Duplicate plan | `dedupe_plan.py`: one copy to keep per group of identical files (100 KB or more), the rest listed as extras; nothing is touched | free, local | ready |
| 1c. Experiment catalogue | `experiments.py`: settings read from the headers of your raw microscope files (.dm3/.dm4 via rosettasciio, .mib, .mrc), grouped by session; magnetite course project excluded | free, local | ready |
| 2. Triage | Claude reads the first 2-3 pages of each document: kind, topic, relevance 1-5, 3-line summary (Batch API) | about $3-6 per 1000 documents (Sonnet 5.5) | next |
| 3. Deep reading | equations, parameters and page numbers from the relevant documents (Phase 0 of `docs/dev/HANDOFF_batch_plan.md`) | per document | later |
| 4. Own results | each simulation or analysis folder summarised from its scripts, parameters, logs and figures; raw data is never uploaded | small | later |

## Step 1 on a Mac

```bash
python3 -m pip install --user pypdf            # optional: PDF titles, DOIs, page counts
python3 tools/research_inventory/inventory.py ~/Desktop/"Research - 2026" --out ~/Desktop/research_inventory
```

The output goes to `~/Desktop/research_inventory/`: `summary.md` (read this first) and
`inventory.csv` (open it in Numbers or Excel). Use `--no-pdf` for a quick first pass and
`--exclude "Private" "Old stuff"` to skip folders. The inventory stays on your Mac; share only
`summary.md` if you want help reading it.

## Steps 1b and 1c on a Mac

```bash
cd ~/Desktop/Holography && git pull
~/venvs/holo-tools/bin/pip install rosettasciio
~/venvs/holo-tools/bin/python tools/research_inventory/dedupe_plan.py ~/Desktop/research_inventory/inventory.csv --out ~/Desktop/research_inventory
~/venvs/holo-tools/bin/python tools/research_inventory/experiments.py ~/Desktop/research_inventory/inventory.csv --root ~/Desktop/"Research - 2026" --out ~/Desktop/research_inventory
```
