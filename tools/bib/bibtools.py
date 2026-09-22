"""Minimal, dependency-free BibTeX tools for docs/references.bib.

Brace-depth parser that keeps character offsets, so that field values can be
replaced in place without reformatting untouched entries; LaTeX <-> Unicode
conversion for name/title comparison; and a syntax validator.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

UNVERIFIED_RE = re.compile(r"^%% ===== UNVERIFIED CANDIDATES.*$", re.M)
END_UNVERIFIED_RE = re.compile(r"^%% ===== END OF UNVERIFIED CANDIDATES.*$", re.M)
ENTRY_RE = re.compile(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)
FIELD_NAME_RE = re.compile(r"\s*([A-Za-z][\w-]*)\s*=\s*")


@dataclass
class Field:
    name: str          # lower-case
    raw_name: str
    value: str         # raw text between the delimiters
    vstart: int        # offset of first char of value (inside braces)
    vend: int          # offset one past the last char of value
    fstart: int        # offset of the start of the line holding the field


@dataclass
class Entry:
    etype: str
    key: str
    start: int         # offset of '@'
    end: int           # offset one past the closing brace
    fields: list = field(default_factory=list)
    section: str = "verified"  # or "unverified"

    def get(self, name, default=None):
        for f in self.fields:
            if f.name == name:
                return f.value
        return default

    def fieldobj(self, name):
        for f in self.fields:
            if f.name == name:
                return f
        return None


class BibParseError(Exception):
    pass


def _match_brace(text, i):
    """text[i] == '{'; return index one past its matching '}'."""
    depth = 0
    n = len(text)
    j = i
    while j < n:
        c = text[j]
        if c == "\\" and j + 1 < n and text[j + 1] in "{}":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise BibParseError(f"unbalanced brace opened at offset {i}")


def parse(text):
    m = UNVERIFIED_RE.search(text)
    unv_start = m.start() if m else len(text) + 1
    entries = []
    for em in ENTRY_RE.finditer(text):
        etype, key = em.group(1).lower(), em.group(2)
        brace = text.index("{", em.start())
        end = _match_brace(text, brace)
        e = Entry(etype, key, em.start(), end,
                  section="unverified" if em.start() > unv_start else "verified")
        i = em.end()
        body_end = end - 1
        while i < body_end:
            while i < body_end and text[i] in " \t\r\n,":
                i += 1
            if i >= body_end:
                break
            fm = FIELD_NAME_RE.match(text, i)
            if not fm:
                raise BibParseError(f"{key}: cannot parse field at offset {i}: {text[i:i+40]!r}")
            j = fm.end()
            if text[j] == "{":
                k = _match_brace(text, j)
                vs, ve = j + 1, k - 1
                i = k
            elif text[j] == '"':
                k = j + 1
                while text[k] != '"' or text[k - 1] == "\\":
                    k += 1
                vs, ve = j + 1, k
                i = k + 1
            else:
                k = j
                while k < body_end and text[k] not in ",\n}":
                    k += 1
                vs, ve = j, k
                i = k
            ls = text.rfind("\n", 0, fm.start() + 1) + 1
            e.fields.append(Field(fm.group(1).lower(), fm.group(1), text[vs:ve], vs, ve, ls))
        entries.append(e)
    return entries


# ---------------------------------------------------------------- LaTeX <-> Unicode
_ACC = {'"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302", "~": "\u0303",
        "=": "\u0304", ".": "\u0307", "u": "\u0306", "v": "\u030c", "H": "\u030b",
        "c": "\u0327", "k": "\u0328", "r": "\u030a"}
_SPECIAL = {"o": "\u00f8", "O": "\u00d8", "ss": "\u00df", "aa": "\u00e5", "AA": "\u00c5",
            "ae": "\u00e6", "AE": "\u00c6", "l": "\u0142", "L": "\u0141", "i": "\u0131"}
_REV_ACC = {v: k for k, v in _ACC.items()}
_REV_SPECIAL = {v: k for k, v in _SPECIAL.items() if k != "i"}


def latex_to_unicode(s: str) -> str:
    if s is None:
        return ""
    s = re.sub(r"\\url\{([^}]*)\}", r"\1", s)
    # {\"o}  \"{o}  \"o  {\v{c}}  \v{c}  \c c
    s = re.sub(r"\{\\([\"'`^~=.])\s*\{?([A-Za-z])\}?\}", lambda m: m.group(2) + _ACC[m.group(1)], s)
    s = re.sub(r"\\([\"'`^~=.])\s*\{?([A-Za-z])\}?", lambda m: m.group(2) + _ACC[m.group(1)], s)
    s = re.sub(r"\{\\([uvHckr])\s*\{([A-Za-z])\}\}", lambda m: m.group(2) + _ACC[m.group(1)], s)
    s = re.sub(r"\\([uvHckr])\s*\{([A-Za-z])\}", lambda m: m.group(2) + _ACC[m.group(1)], s)
    s = re.sub(r"\\([uvHckr]) ([A-Za-z])", lambda m: m.group(2) + _ACC[m.group(1)], s)
    s = re.sub(r"\{\\(ss|aa|AA|ae|AE|o|O|l|L)\}", lambda m: _SPECIAL[m.group(1)], s)
    s = re.sub(r"\\(ss|aa|AA|ae|AE|o|O|l|L)(?![A-Za-z])\s?", lambda m: _SPECIAL[m.group(1)], s)
    for a, b in (("\\&", "&"), ("\\_", "_"), ("\\%", "%"), ("\\$", "$"), ("\\#", "#"),
                 ("---", "\u2014"), ("--", "\u2013"), ("~", " ")):
        s = s.replace(a, b)
    s = s.replace("{", "").replace("}", "")
    return unicodedata.normalize("NFC", s)


_PUNCT_TO_TEX = {"\u2013": "--", "\u2014": "---", "\u2018": "`", "\u2019": "'", "\u201c": "``",
                 "\u201d": "''", "\u00a0": " ", "\u2010": "-", "\u2011": "-", "\u2212": "-", "&": "\\&",
                 "_": "\\_", "%": "\\%", "#": "\\#", "$": "\\$", "\u00c5": "{\\AA}", "\u212b": "{\\AA}"}


def unicode_to_latex(s: str) -> tuple[str, list]:
    """Encode Unicode as BibTeX-safe LaTeX. Returns (text, [unencodable chars])."""
    out, bad = [], []
    for ch in unicodedata.normalize("NFC", s):
        if ord(ch) < 128 and ch not in "&_%#$":
            out.append(ch)
            continue
        if ch in _PUNCT_TO_TEX:
            out.append(_PUNCT_TO_TEX[ch])
            continue
        if ch in _REV_SPECIAL:
            out.append("{\\" + _REV_SPECIAL[ch] + "}")
            continue
        d = unicodedata.normalize("NFD", ch)
        if len(d) == 2 and d[1] in _REV_ACC and ord(d[0]) < 128:
            cmd = _REV_ACC[d[1]]
            base = "\\i" if d[0] == "i" and cmd in "\"'`^~=." else d[0]
            if cmd.isalpha():
                out.append("{\\" + cmd + "{" + base + "}}")
            else:
                out.append("{\\" + cmd + base + "}")
            continue
        out.append(ch)
        bad.append(ch)
    return "".join(out), bad


def fold(s: str) -> str:
    """Accent-free, case-free, punctuation-free form for matching."""
    s = unicodedata.normalize("NFKD", latex_to_unicode(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u00f8", "o").replace("\u00df", "ss").replace("\u0142", "l").replace("\u00e6", "ae")
    s = re.sub(r"<[^>]+>", " ", s)          # JATS/MathML tags in Crossref titles
    s = s.casefold()
    s = re.sub(r"[\u2010-\u2015\u2212\-/]", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- names
def split_names(s: str) -> list[str]:
    parts, depth, cur, i = [], 0, [], 0
    while i < len(s):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if depth == 0 and s.startswith(" and ", i):
            parts.append("".join(cur).strip())
            cur = []
            i += 5
            continue
        cur.append(c)
        i += 1
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def parse_name(n: str) -> dict:
    """Return {'family':..., 'given':...} in Unicode."""
    if n.strip() == "others":
        return {"others": True}
    depth, commas = 0, []
    for i, c in enumerate(n):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "," and depth == 0:
            commas.append(i)
    if commas:
        fam, giv = n[:commas[0]], n[commas[-1] + 1:]
    else:
        toks = n.split()
        fam, giv = (toks[-1], " ".join(toks[:-1])) if len(toks) > 1 else (n, "")
    return {"family": latex_to_unicode(fam).strip(), "given": latex_to_unicode(giv).strip()}


def initials(given: str) -> str:
    """'Lian-Mao' -> 'LM', 'L.-M.' -> 'LM', 'M. J.' -> 'MJ', 'R.F.' -> 'RF'."""
    g = unicodedata.normalize("NFKD", given)
    g = "".join(c for c in g if not unicodedata.combining(c)).replace(".", ". ")
    out = []
    for tok in re.split(r"[\s\-\u2010]+", g.strip()):
        tok = tok.strip(".")
        if tok:
            out.append(tok[0].upper())
    return "".join(out)


# ---------------------------------------------------------------- validation
def validate(text: str) -> tuple[list, list, dict]:
    errors, warnings = [], []
    stats = {}
    depth = 0
    for ln, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("%"):
            continue
        k = 0
        while k < len(line):
            c = line[k]
            if c == "\\" and k + 1 < len(line) and line[k + 1] in "{}":
                k += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth < 0:
                    errors.append(f"line {ln}: closing brace without opener")
                    depth = 0
            k += 1
    if depth != 0:
        errors.append(f"global brace depth at EOF = {depth}")
    try:
        entries = parse(text)
    except BibParseError as exc:
        return [str(exc)], warnings, stats
    # text outside entries must be comments/blank
    last = 0
    for e in entries:
        gap = text[last:e.start]
        for gl in gap.splitlines():
            if gl.strip() and not gl.lstrip().startswith("%"):
                errors.append(f"stray non-comment text before {e.key}: {gl.strip()[:60]!r}")
        last = e.end
    for gl in text[last:].splitlines():
        if gl.strip() and not gl.lstrip().startswith("%"):
            errors.append(f"stray non-comment text after last entry: {gl.strip()[:60]!r}")
    seen = {}
    for e in entries:
        kl = e.key.lower()
        if kl in seen:
            errors.append(f"duplicate key {e.key} (also {seen[kl]})")
        seen[kl] = e.key
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_:\-]*", e.key):
            errors.append(f"illegal key {e.key!r}")
        names = [f.name for f in e.fields]
        for nm in set(names):
            if names.count(nm) > 1:
                errors.append(f"{e.key}: duplicate field {nm}")
        if not e.get("title"):
            errors.append(f"{e.key}: no title")
        note = e.get("note") or ""
        if not note.startswith("evidence:") or "provenance:" not in note:
            errors.append(f"{e.key}: note must start with 'evidence:' and contain 'provenance:'")
        for f in e.fields:
            if f.value.count("{") != f.value.count("}"):
                errors.append(f"{e.key}.{f.name}: unbalanced braces in value")
        doi = e.get("doi")
        if doi is not None and not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
            errors.append(f"{e.key}: malformed doi {doi!r}")
        if e.section == "unverified" and doi:
            errors.append(f"{e.key}: doi field inside the UNVERIFIED section")
    if len(UNVERIFIED_RE.findall(text)) != 1:
        errors.append("UNVERIFIED delimiter must occur exactly once")
    stats = {
        "entries": len(entries),
        "unique_keys": len(seen),
        "verified_section": sum(e.section == "verified" for e in entries),
        "unverified_section": sum(e.section == "unverified" for e in entries),
        "with_doi": sum(bool(e.get("doi")) for e in entries),
    }
    return errors, warnings, stats
