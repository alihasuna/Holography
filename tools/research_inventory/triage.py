#!/usr/bin/env python3
"""Step 2: make sense of the research folder with the Claude Message Batches API (50 % price).

For each unique document (PDF, notes, LaTeX, Word, PowerPoint, notebooks) and each code folder,
Claude reads the beginning (about 6000 characters) and returns: what it is, title, topics,
relevance to the project (1-5), a short summary, key numbers/facts, linked experiment dates,
draft/final status and a suggested folder. Nothing on disk is moved or changed.

Commands (run them in order; all files go to <out>/triage/):
  build   free, local: choose the files, extract their beginnings, write requests.jsonl
  submit  shows the cost estimate, asks for "yes", enforces --max-usd, sends the batch
          (--sample N sends only N requests first, to check quality for a few cents)
  status  progress of the submitted batch(es)
  collect download the results to results.jsonl (when status says "ended")
  report  free, local: triage.csv + research_map.md from results.jsonl

Example (Mac, in the virtual environment; your key stays in your environment):
  export ANTHROPIC_API_KEY=...            # never paste it into chat or commit it
  P=~/venvs/holo-tools/bin/python; T=tools/research_inventory/triage.py
  $P $T build   --inventory ~/Desktop/research_inventory/inventory.csv --root ~/Desktop/"Research - 2026" --out ~/Desktop/research_inventory
  $P $T submit  --out ~/Desktop/research_inventory --sample 20
  $P $T status  --out ~/Desktop/research_inventory
  $P $T collect --out ~/Desktop/research_inventory
  $P $T report  --out ~/Desktop/research_inventory
  (then the full run: submit without --sample, and status / collect / report again)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import logging
import zipfile

logging.getLogger("pypdf").setLevel(logging.ERROR)
from collections import Counter, defaultdict
from pathlib import Path

MODEL = "claude-sonnet-5-5"
PRICE_PER_MTOK = {"input": 1.00, "output": 5.00, "cache_read": 0.10, "cache_write": 1.25}  # Batch API, Sonnet 5.5
MAX_CHARS = 6000
DOC_EXT = {".pdf", ".md", ".txt", ".tex", ".docx", ".pptx", ".ipynb", ".rtf"}
EXCLUDE_WORDS = ["magnetite", "Fe3O4", "CuSn", ".obsidian", "_build", "/build/", "site-packages", "node_modules",
                 ".ipynb_checkpoints", "egg-info", "__pycache__", "/.git/", "venv/",
                 # third-party packages downloaded into the folder (agent skills, paper-writing templates)
                 "scientific-agent-skills", "AI-Researcher", ".claude/skills", "writing_templates"]

KINDS = ["paper", "book_or_chapter", "thesis_or_report", "presentation_or_poster", "lecture_or_course_notes",
         "personal_research_notes", "meeting_or_supervisor_notes", "ai_generated_notes", "analysis_or_results",
         "simulation_setup_or_log", "code_project", "manual_or_datasheet", "admin", "other"]
TOPICS = ["reflection_holography", "offaxis_holography_general", "darkfield_holography",
          "RHEED_reflection_diffraction", "REM_reflection_imaging", "multislice_simulation", "prismatic_abtem_tools",
          "ptychography_4DSTEM", "dislocations_defects_strain", "surface_steps_reconstructions",
          "detector_MTF_calibration", "beam_tilt_stage_calibration", "microscope_alignment_instrumentation",
          "crystallography_diffraction_theory", "sample_preparation_cleaving", "image_processing_reconstruction",
          "transfer_exam_thesis_planning", "other_project_or_course", "admin", "other"]
FOLDERS = ["01_literature", "02_theory_notes", "03_experiments", "04_simulations", "05_analysis_results", "06_code",
           "07_reports_presentations", "08_admin_courses", "99_archive_or_superseded"]
SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": KINDS},
        "title": {"type": "string"},
        "authors_or_source": {"type": "string"},
        "year": {"type": "string"},
        "topics": {"type": "array", "items": {"type": "string", "enum": TOPICS}},
        "relevance": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "experiment_dates_or_sessions": {"type": "array", "items": {"type": "string"}},
        "status": {"type": "string", "enum": ["final", "draft", "superseded_version", "unclear"]},
        "suggested_folder": {"type": "string", "enum": FOLDERS},
    },
    "required": ["kind", "title", "authors_or_source", "year", "topics", "relevance", "summary", "key_points",
                 "experiment_dates_or_sessions", "status", "suggested_folder"],
    "additionalProperties": False,
}
SYSTEM = f"""You are helping a PhD student in electron microscopy make sense of a large research folder.

THE PROJECT. Reflection-mode (RHEED-geometry) off-axis electron holography of crystal surfaces at
200 kV on a Hitachi HF-3300 with a Merlin (Medipix) detector, and, as the end goal, reflection-mode
electron ptychography (4D-STEM in reflection). Samples: cleaved Si(110) wafers imaged on their
{{111}} cleavage facet (experiments in March 2026, partly with the supervisor Arthur), and now Si(100).
Simulation work: grazing-incidence multislice (earlier with Prismatic/prismatique on the Fir cluster,
now a custom code), buried dislocations, surface steps, Osakabe's 1989-1993 reflection holography as
the starting point. Calibration work: Merlin detector MTF at 25-350 keV, beam-tilt and stage-tilt
calibration, image-plane correction. There was a transfer exam (thesis milestone) with a report,
talk and posters. Some folders were written by an AI research agent; label those notes
"ai_generated_notes". A magnetite nanoparticle project is a separate course project.

YOUR TASK. You receive the path and the beginning of ONE file (or a listing of one code folder).
Classify it and summarise it for the student. Rules:
* Use only what the text shows; if unsure, say so in the summary and use "unclear" or "other".
* relevance: 5 = central to reflection holography/ptychography of Si surfaces or its calibrations;
  4 = directly useful theory, method or data; 3 = background; 2 = loosely related; 1 = unrelated.
* summary: at most 3 short sentences, plain language, saying what it is and what it contains.
* key_points: at most 5 items with concrete numbers, parameters, results or conclusions
  (e.g. "biprism 106.8 V", "fringe spacing 0.5 nm", "Si(111) facet at 4.1 deg stage tilt").
* experiment_dates_or_sessions: dates or session names the file refers to (YYYY-MM-DD when possible).
* status: "superseded_version" if the name or content shows a newer version exists (v1/v2, old, copy).
* suggested_folder: where it belongs in a clean structure ({", ".join(FOLDERS)}).
Return only the JSON object."""


def cid(path: str) -> str:
    return "f" + hashlib.sha1(path.encode("utf-8")).hexdigest()[:24]


def mostly_numbers(text: str) -> bool:
    s = re.sub(r"\s", "", text[:3000])
    return len(s) > 200 and sum(c in "0123456789.,-+eE" for c in s) / len(s) > 0.6


def extract(path: Path, ext: str) -> str:
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            r = PdfReader(str(path), strict=False)
            out = ""
            for p in r.pages[:4]:
                out += (p.extract_text() or "") + "\n"
                if len(out) > MAX_CHARS:
                    break
            return f"[PDF, {len(r.pages)} pages]\n" + out
        if ext in (".docx", ".pptx"):
            with zipfile.ZipFile(path) as z:
                names = sorted(n for n in z.namelist() if n.startswith(("word/document", "ppt/slides/slide")))
                xml = " ".join(z.read(n).decode("utf-8", "replace") for n in names[:30])
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", xml))
        if ext == ".ipynb":
            nb = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return "\n".join("".join(c.get("source", "")) for c in nb.get("cells", []))
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[could not extract text: {type(e).__name__}]"


def code_folder_text(folder: Path, files: list[str]) -> str:
    parts = [f"[code folder with {len(files)} Python files]", "files: " + ", ".join(sorted(files)[:60])]
    for name in ("README.md", "README.txt", "readme.md"):
        if (folder / name).exists():
            parts.append("README:\n" + (folder / name).read_text(errors="replace")[:1500])
            break
    for fn in sorted(files)[:15]:
        try:
            head = "".join((folder / fn).read_text(errors="replace").splitlines(keepends=True)[:25])
        except OSError:
            continue
        parts.append(f"--- {fn} (first lines)\n{head}")
    return "\n".join(parts)


def build(args):
    root = args.root.expanduser()
    tri = args.out.expanduser() / "triage"
    tri.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(args.inventory.expanduser(), encoding="utf-8")))
    seen, docs, code_dirs = set(), [], defaultdict(list)
    for r in sorted(rows, key=lambda r: (any(w in r["path"] for w in ("archiv", "_inbox", "copy")), len(r["path"]))):
        p = r["path"]
        if any(w.lower() in p.lower() for w in EXCLUDE_WORDS + args.exclude):
            continue
        g = r["dup_group"]
        if g and g in seen:
            continue
        if g:
            seen.add(g)
        if r["ext"] in DOC_EXT and int(r["size"]) >= 200:
            docs.append(r)
        elif r["ext"] == ".py":
            code_dirs[str(Path(p).parent)].append(Path(p).name)

    reqs, skipped = [], Counter()
    for r in docs:
        text = extract(root / r["path"], r["ext"])
        if r["ext"] == ".txt" and mostly_numbers(text):
            skipped["numeric .txt (data, not a document)"] += 1
            continue
        if len(text.strip()) < 80:
            skipped["no readable text (scanned PDF or empty)"] += 1
            continue
        reqs.append((r["path"], f"FILE: {r['path']}\nMODIFIED: {r['modified']}\n\n{text[:MAX_CHARS]}"))
    for d, files in code_dirs.items():
        reqs.append((d + "/", f"CODE FOLDER: {d}\n\n{code_folder_text(root / d, files)[:MAX_CHARS]}"))

    with open(tri / "requests.jsonl", "w", encoding="utf-8") as f:
        for path, content in reqs:
            params = {"model": MODEL, "max_tokens": 3000, "output_config": {"effort": "low", "format": {
                "type": "json_schema", "schema": SCHEMA}},
                "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
                "messages": [{"role": "user", "content": content}]}
            f.write(json.dumps({"custom_id": cid(path), "path": path, "params": params}) + "\n")
    n_in = sum(len(c) for _, c in reqs) / 3.5 + len(reqs) * len(SYSTEM) / 3.5
    print(f"{len(reqs)} requests ({len(docs)} documents considered, {len(code_dirs)} code folders); skipped: "
          f"{dict(skipped) or 'none'}")
    print(f"wrote {tri / 'requests.jsonl'}; rough estimate: {estimate(len(reqs), n_in)}")
    top = Counter("/".join(Path(path).parts[:2]) for path, _ in reqs).most_common(25)
    print("\nrequests per folder (check for downloaded packages or other projects; drop them with --exclude WORD):")
    for folder, n in top:
        print(f"  {n:5d}  {folder}")


def estimate(n, n_input_tokens, out_per_req=700):
    cost = n_input_tokens / 1e6 * PRICE_PER_MTOK["input"] + n * out_per_req / 1e6 * PRICE_PER_MTOK["output"]
    return f"~{n_input_tokens / 1e6:.1f} M input tokens, ~{n * out_per_req / 1e6:.1f} M output tokens, about ${cost:.2f}"


def load_requests(tri: Path):
    return [json.loads(line) for line in open(tri / "requests.jsonl", encoding="utf-8")]


def submit(args):
    import anthropic
    tri = args.out.expanduser() / "triage"
    reqs = load_requests(tri)
    done = set()
    if (tri / "batches.json").exists():
        for b in json.loads((tri / "batches.json").read_text()):
            done.update(b["custom_ids"])
    reqs = [r for r in reqs if r["custom_id"] not in done]
    if args.sample:
        reqs = reqs[:: max(1, len(reqs) // args.sample)][: args.sample]
    if not reqs:
        sys.exit("nothing left to submit (every request is already in a batch)")
    n_in = sum(len(r["params"]["messages"][0]["content"]) + len(SYSTEM) for r in reqs) / 3.5
    est = n_in / 1e6 * PRICE_PER_MTOK["input"] + len(reqs) * 700 / 1e6 * PRICE_PER_MTOK["output"]
    print(f"about to submit {len(reqs)} requests to {MODEL} (Batch API): {estimate(len(reqs), n_in)}")
    if est > args.max_usd:
        sys.exit(f"estimate ${est:.2f} exceeds --max-usd {args.max_usd}; raise it explicitly if intended")
    if input('type "yes" to submit: ').strip().lower() != "yes":
        sys.exit("not submitted")
    client = anthropic.Anthropic()
    batch = client.messages.batches.create(requests=[{"custom_id": r["custom_id"], "params": r["params"]}
                                                     for r in reqs])
    log = json.loads((tri / "batches.json").read_text()) if (tri / "batches.json").exists() else []
    log.append({"id": batch.id, "created": time.strftime("%Y-%m-%d %H:%M"), "n": len(reqs),
                "estimate_usd": round(est, 2), "custom_ids": [r["custom_id"] for r in reqs]})
    (tri / "batches.json").write_text(json.dumps(log, indent=1))
    print(f"submitted batch {batch.id} ({len(reqs)} requests). Check with: status")


def status(args):
    import anthropic
    tri = args.out.expanduser() / "triage"
    client = anthropic.Anthropic()
    for b in json.loads((tri / "batches.json").read_text()):
        s = client.messages.batches.retrieve(b["id"])
        c = s.request_counts
        print(f"{b['id']}  {s.processing_status:12s} processing {c.processing}, succeeded {c.succeeded}, "
              f"errored {c.errored}, expired {c.expired}  (submitted {b['created']}, {b['n']} requests)")


def collect(args):
    import anthropic
    tri = args.out.expanduser() / "triage"
    client = anthropic.Anthropic()
    have = set()
    if (tri / "results.jsonl").exists():
        have = {json.loads(line)["custom_id"] for line in open(tri / "results.jsonl", encoding="utf-8")}
    n = 0
    with open(tri / "results.jsonl", "a", encoding="utf-8") as f:
        for b in json.loads((tri / "batches.json").read_text()):
            if client.messages.batches.retrieve(b["id"]).processing_status != "ended":
                print(f"{b['id']} has not ended yet; skipped")
                continue
            for res in client.messages.batches.results(b["id"]):
                if res.custom_id in have:
                    continue
                rec = {"custom_id": res.custom_id, "type": res.result.type}
                if res.result.type == "succeeded":
                    m = res.result.message
                    rec["stop_reason"] = m.stop_reason
                    rec["text"] = next((x.text for x in m.content if x.type == "text"), "")
                    u = m.usage
                    rec["usage"] = {"input": u.input_tokens, "output": u.output_tokens,
                                    "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
                                    "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0}
                elif res.result.type == "errored":
                    rec["error"] = str(res.result.error)[:300]
                f.write(json.dumps(rec) + "\n")
                n += 1
    print(f"collected {n} new results into {tri / 'results.jsonl'}. Next: report")


def report(args):
    tri = args.out.expanduser() / "triage"
    paths = {r["custom_id"]: r["path"] for r in load_requests(tri)}
    recs, cost, problems = [], 0.0, Counter()
    for line in open(tri / "results.jsonl", encoding="utf-8"):
        r = json.loads(line)
        u = r.get("usage")
        if u:
            cost += sum(u[k] / 1e6 * PRICE_PER_MTOK[k] for k in PRICE_PER_MTOK)
        if r["type"] != "succeeded" or r.get("stop_reason") not in ("end_turn", None):
            problems[f"{r['type']}/{r.get('stop_reason')}"] += 1
            continue
        try:
            d = json.loads(r["text"])
        except ValueError:
            problems["invalid JSON"] += 1
            continue
        d["path"] = paths.get(r["custom_id"], r["custom_id"])
        recs.append(d)
    cols = ["relevance", "kind", "suggested_folder", "status", "title", "authors_or_source", "year", "topics",
            "summary", "key_points", "experiment_dates_or_sessions", "path"]
    with open(tri / "triage.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d in sorted(recs, key=lambda d: (-d["relevance"], d["path"])):
            w.writerow({c: "; ".join(d[c]) if isinstance(d[c], list) else d[c] for c in cols})

    by_topic = defaultdict(list)
    for d in recs:
        for t in d["topics"] or ["other"]:
            by_topic[t].append(d)
    kinds, folders = Counter(d["kind"] for d in recs), Counter(d["suggested_folder"] for d in recs)
    rel = Counter(d["relevance"] for d in recs)
    sessions = Counter(s for d in recs for s in d["experiment_dates_or_sessions"])
    L = ["# Research map", "",
         f"{len(recs)} files and code folders classified (actual cost ${cost:.2f}). "
         f"Problems: {dict(problems) or 'none'}. Full table: `triage/triage.csv`.", "",
         "## At a glance", "",
         "| Relevance | Files |", "|---|---|"] + [f"| {k} | {rel[k]} |" for k in (5, 4, 3, 2, 1)]
    L += ["", "**Kinds:** " + ", ".join(f"{k} {n}" for k, n in kinds.most_common()),
          "", "**Suggested folders:** " + ", ".join(f"{k} {n}" for k, n in sorted(folders.items())),
          "", "**Most referenced experiment dates/sessions:** " + ", ".join(f"{k} ({n})" for k, n in sessions.most_common(15)),
          "", "## Most relevant (5)", ""]
    for d in sorted((d for d in recs if d["relevance"] == 5), key=lambda d: d["path"]):
        L.append(f"* **{d['title']}** ({d['kind']}, {d['status']}): {d['summary']}  \n  `{d['path']}`")
    for t in TOPICS:
        if t not in by_topic:
            continue
        items = sorted(by_topic[t], key=lambda d: (-d["relevance"], d["path"]))
        L += ["", f"## {t} ({len(items)})", ""]
        for d in items[:40]:
            L.append(f"* [{d['relevance']}] **{d['title']}**: {d['summary']}  \n  `{d['path']}`")
        if len(items) > 40:
            L.append(f"* ... and {len(items) - 40} more in triage.csv")
    (tri / "research_map.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {tri / 'triage.csv'} and {tri / 'research_map.md'} ({len(recs)} entries, cost ${cost:.2f})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "submit", "status", "collect", "report"])
    ap.add_argument("--out", type=Path, required=True, help="the research_inventory folder")
    ap.add_argument("--inventory", type=Path, help="inventory.csv (build)")
    ap.add_argument("--root", type=Path, help="the research folder (build)")
    ap.add_argument("--exclude", nargs="*", default=[], help="build: also skip paths containing these words")
    ap.add_argument("--sample", type=int, default=0, help="submit only N requests (a quality check)")
    ap.add_argument("--max-usd", type=float, default=20.0, help="refuse to submit above this estimate")
    args = ap.parse_args()
    if args.command == "build" and not (args.inventory and args.root):
        sys.exit("build needs --inventory and --root")
    {"build": build, "submit": submit, "status": status, "collect": collect, "report": report}[args.command](args)


if __name__ == "__main__":
    main()
