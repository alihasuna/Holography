#!/usr/bin/env python3
"""Step 1 of the research-folder plan: a free, local inventory. Nothing leaves the computer.

Walks a folder and writes:
  inventory.csv   one row per file: path, category, extension, size, modified date, duplicate group,
                  and for PDFs: page count, title, DOI and the first characters of text (if pypdf is
                  installed)
  summary.md      what is there: counts and sizes by category and by top-level folder, largest files,
                  duplicates, PDFs with a DOI, likely books, simulation outputs

Run it on a Mac (Python 3.9+; `pip install pypdf` for the PDF details, optional):
  python3 inventory.py ~/Desktop/"Research - 2026" --out ~/Desktop/research_inventory

It only reads. It never moves, renames or deletes anything. Folders such as .git, virtual
environments and caches are skipped (see SKIP_DIRS; add your own with --exclude).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", ".svn", ".hg", "__pycache__", ".ipynb_checkpoints", "node_modules", "venv", ".venv",
             "env", ".tox", ".mypy_cache", ".pytest_cache", ".idea", ".vscode", ".Trash", "site-packages",
             ".cache", "build", "dist", ".DS_Store"}
SKIP_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}

CATEGORIES = {
    "document": {".pdf", ".djvu", ".epub", ".ps", ".chm"},
    "text": {".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".tex", ".bib", ".pages", ".key", ".ppt", ".pptx",
             ".xls", ".xlsx", ".csv", ".numbers"},
    "code": {".py", ".ipynb", ".m", ".jl", ".c", ".cpp", ".h", ".f", ".f90", ".cu", ".sh", ".slurm", ".r", ".java",
             ".js", ".ts", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini", ".in", ".param", ".prm"},
    "microscopy": {".dm3", ".dm4", ".emd", ".ser", ".emi", ".mrc", ".mrcs", ".mib", ".hspy", ".prz", ".blo",
                   ".tvips", ".raw", ".xml"},
    "data": {".npz", ".npy", ".h5", ".hdf5", ".nxs", ".mat", ".nc", ".pkl", ".pickle", ".dat", ".bin", ".fits",
             ".zarr", ".parquet", ".xyz", ".cif", ".pdb", ".vasp", ".cfg"},
    "image": {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".eps", ".heic"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".gif"},
    "archive": {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar", ".dmg"},
}
EXT2CAT = {}
for cat, exts in CATEGORIES.items():
    for e in exts:
        EXT2CAT.setdefault(e, cat)

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.I)
ISBN_RE = re.compile(r"\bISBN(?:-1[03])?:?\s*([0-9Xx][0-9Xx\- ]{8,16}[0-9Xx])")


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024


def file_hash(path: Path, chunk=1 << 20) -> str:
    h = hashlib.blake2b(digest_size=16)
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def pdf_info(path: Path, max_chars=600):
    """(pages, title, doi, isbn, first_text) from the first pages; empty values without pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "", "", "", ""
    try:
        r = PdfReader(str(path), strict=False)
        pages = len(r.pages)
        meta = r.metadata or {}
        title = (meta.get("/Title") or "").strip() if hasattr(meta, "get") else ""
        text = ""
        for p in r.pages[:3]:
            try:
                text += (p.extract_text() or "") + "\n"
            except Exception:
                pass
            if len(text) > 4000:
                break
        doi = DOI_RE.search(text)
        isbn = ISBN_RE.search(text)
        first = re.sub(r"\s+", " ", text).strip()[:max_chars]
        return pages, title, doi.group(1).rstrip(".,;)") if doi else "", isbn.group(1) if isbn else "", first
    except Exception as e:  # damaged or encrypted PDF
        return "", "", "", "", f"[unreadable: {type(e).__name__}]"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, default=Path("research_inventory"))
    ap.add_argument("--exclude", nargs="*", default=[], help="extra folder names to skip")
    ap.add_argument("--no-pdf", action="store_true", help="skip reading PDFs (faster)")
    ap.add_argument("--no-hash", action="store_true", help="skip duplicate detection")
    args = ap.parse_args()
    logging.getLogger("pypdf").setLevel(logging.ERROR)  # damaged PDFs are reported in the CSV instead

    root = args.folder.expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"not a folder: {root}")
    skip = SKIP_DIRS | set(args.exclude)
    args.out.expanduser().mkdir(parents=True, exist_ok=True)
    out = args.out.expanduser()

    t0 = time.time()
    rows, skipped_dirs, errors = [], Counter(), 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        keep = []
        for d in dirnames:
            if d in skip or d.endswith(".app") or d.endswith(".egg-info"):
                skipped_dirs[d] += 1
            else:
                keep.append(d)
        dirnames[:] = keep
        for fn in filenames:
            if fn in SKIP_FILES or fn.startswith("~$"):
                continue
            p = Path(dirpath) / fn
            try:
                if p.is_symlink():
                    continue
                st = p.stat()
            except OSError:
                errors += 1
                continue
            rel = p.relative_to(root)
            ext = p.suffix.lower()
            rows.append({"path": str(rel), "top_folder": rel.parts[0] if len(rel.parts) > 1 else "(root)",
                         "category": EXT2CAT.get(ext, "other"), "ext": ext or "(none)", "size": st.st_size,
                         "modified": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime)),
                         "dup_group": "", "pages": "", "pdf_title": "", "doi": "", "isbn": "", "first_text": ""})
    print(f"walked {len(rows)} files in {time.time() - t0:.0f} s ({errors} unreadable)")

    # duplicates: hash only files that share a size (cheap on large data folders)
    if not args.no_hash:
        by_size = defaultdict(list)
        for i, r in enumerate(rows):
            if r["size"] > 0:
                by_size[r["size"]].append(i)
        cand = [ix for ix in by_size.values() if len(ix) > 1]
        n_cand = sum(len(ix) for ix in cand)
        print(f"hashing {n_cand} same-size files for duplicates ...")
        by_hash = defaultdict(list)
        for ix in cand:
            for i in ix:
                try:
                    by_hash[file_hash(root / rows[i]["path"])].append(i)
                except OSError:
                    pass
        g = 0
        for ix in by_hash.values():
            if len(ix) > 1:
                g += 1
                for i in ix:
                    rows[i]["dup_group"] = f"D{g:05d}"

    if not args.no_pdf:
        pdfs = [r for r in rows if r["ext"] == ".pdf"]
        print(f"reading first pages of {len(pdfs)} PDFs ...")
        for k, r in enumerate(pdfs, 1):
            r["pages"], r["pdf_title"], r["doi"], r["isbn"], r["first_text"] = pdf_info(root / r["path"])
            if k % 200 == 0:
                print(f"  {k}/{len(pdfs)}")

    fields = list(rows[0].keys()) if rows else []
    with open(out / "inventory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # summary
    tot = sum(r["size"] for r in rows)
    cat_n, cat_s = Counter(), Counter()
    top_n, top_s = Counter(), Counter()
    for r in rows:
        cat_n[r["category"]] += 1
        cat_s[r["category"]] += r["size"]
        top_n[r["top_folder"]] += 1
        top_s[r["top_folder"]] += r["size"]
    dups = defaultdict(list)
    for r in rows:
        if r["dup_group"]:
            dups[r["dup_group"]].append(r)
    dup_waste = sum(sum(x["size"] for x in g[1:]) for g in dups.values())
    pdfs = [r for r in rows if r["ext"] == ".pdf"]
    books = [r for r in pdfs if isinstance(r["pages"], int) and r["pages"] >= 150]
    with_doi = [r for r in pdfs if r["doi"]]
    ext_n = Counter(r["ext"] for r in rows)

    L = [f"# Inventory of `{root.name}`", "",
         f"{len(rows)} files, {human(tot)} (skipped folders: "
         f"{', '.join(f'{k} x{v}' for k, v in skipped_dirs.most_common(8)) or 'none'}).", "",
         "## By category", "", "| Category | Files | Size |", "|---|---|---|"]
    L += [f"| {c} | {cat_n[c]} | {human(cat_s[c])} |" for c, _ in cat_s.most_common()]
    L += ["", "## By top-level folder", "", "| Folder | Files | Size |", "|---|---|---|"]
    L += [f"| {t} | {top_n[t]} | {human(top_s[t])} |" for t, _ in top_s.most_common(40)]
    L += ["", "## Most common file types", "", ", ".join(f"`{e}` {n}" for e, n in ext_n.most_common(30))]
    L += ["", "## Documents", "",
          f"* PDFs: {len(pdfs)}; with a DOI on the first pages: {len(with_doi)}; "
          f"likely books (150 pages or more): {len(books)}"]
    if books:
        L += ["", "Likely books:", ""] + [f"* {r['path']} ({r['pages']} pp.)" for r in sorted(books, key=lambda r: r['path'])[:100]]
    L += ["", "## Duplicates", "",
          f"{len(dups)} groups of identical files; removing the extra copies would free {human(dup_waste)}."]
    for gname, g in sorted(dups.items(), key=lambda kv: -kv[1][0]["size"] * (len(kv[1]) - 1))[:25]:
        L.append(f"* {human(g[0]['size'])} x{len(g)}: " + " | ".join(x["path"] for x in g[:4]))
    L += ["", "## Largest files", ""]
    L += [f"* {human(r['size'])}  {r['path']}" for r in sorted(rows, key=lambda r: -r["size"])[:25]]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out / 'inventory.csv'} and {out / 'summary.md'} in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
