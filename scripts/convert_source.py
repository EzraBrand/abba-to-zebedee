"""One-time migration: Google Docs Markdown export -> master files of this repo.

Usage: py -3.13 -I scripts/convert_source.py source/v18.2.md paper/

Writes
  paper/paper.md          prose, with {{list:<id>}} and {{table:<id>}} placeholders
  paper/lists/<id>.csv    one row per list item: n, item, note, added, review
  paper/tables/<id>.csv   the pipe tables, as plain CSV
and prints a summary of every list it found, for review.

Conversions
  * The title block becomes YAML front matter; the hand-made "Outline" (PDF page numbers)
    is dropped, since the build makes the table of contents.
  * Heading ids are re-slugged to safe ids; internal #links are updated.
  * Sefaria links become  [text](sefaria:<Ref>)  — the build resolves them to Bekiut or Sefaria.
  * The footnote of each list item moves into that row's "note" column.
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdlinks import escape_url, find_links  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
src, out = Path(sys.argv[1]), Path(sys.argv[2])
md = src.read_text(encoding="utf-8").replace("\r\n", "\n")

# ------------------------------------------------------------------ split body / footnotes
first_def = re.search(r"^\[\^\d+\]:", md, re.M).start()
body, notes_txt = md[:first_def], md[first_def:]
notes = {}
for m in re.finditer(r"^\[\^(\d+)\]:[ \t]*(.*?)(?=^\[\^\d+\]:|\Z)", notes_txt, re.M | re.S):
    notes[m.group(1)] = m.group(2).rstrip()


# ------------------------------------------------------------------ Sefaria links -> sefaria:
def to_ref_links(text: str) -> str:
    out_parts, last = [], 0
    for ln in find_links(text):
        u = ln.url
        p = urlsplit(u)
        if "sefaria.org" in p.netloc:
            ref = unquote(p.path.lstrip("/"))
            if ref and not ref.startswith(("search", "sheets", "texts", "topics")):
                out_parts.append(text[last:ln.url_start])
                out_parts.append(escape_url("sefaria:" + ref.replace(" ", "_")))
                last = ln.url_end
    out_parts.append(text[last:])
    return "".join(out_parts)


body = to_ref_links(body)
notes = {k: to_ref_links(v) for k, v in notes.items()}

# ------------------------------------------------------------------ front matter, outline
lines = body.split("\n")
title = lines[0].lstrip("# ").strip()
assert lines[2].startswith("## v18") and lines[4].startswith("## By"), lines[:5]
author = lines[4][len("## By "):].strip()
rest = "\n".join(lines[5:])
o0 = rest.index("# Outline")
o1 = rest.index("# Bibliography")
rest = rest[:o0] + rest[o1:]
rest = re.sub(r"^#[ \t]*$\n", "", rest, flags=re.M)  # empty headings from page breaks

# ------------------------------------------------------------------ heading ids
used = set()


def slug(text: str) -> str:
    t = re.sub(r"\[\^\d+\]", "", text)
    t = re.sub(r"[*\\]", "", t)
    t = unicodedata.normalize("NFKC", t).lower()
    t = t.replace("’", "").replace("'", "").replace("“", "").replace("”", "")
    t = re.sub(r"[^\w]+", "-", t).strip("-")
    base, i = t or "section", 2
    while t in used:
        t = f"{base}-{i}"
        i += 1
    used.add(t)
    return t


idmap = {}


def fix_heading(m):
    hashes, text, old = m.group(1), m.group(2).rstrip(), m.group(3)
    new = slug(text)
    if old:
        idmap[old[2:-1]] = new
    return f"{hashes} {text} {{#{new}}}"


rest = re.sub(r"^(#{1,6})[ \t]+(.*?)[ \t]*(\{#[^}]*\})?[ \t]*$", fix_heading, rest, flags=re.M)


def fix_anchor(m):
    old = m.group(1).replace("\\", "")
    return "](#" + idmap.get(old, idmap.get(m.group(1), old)) + ")"


rest = re.sub(r"\]\(#((?:\\.|[^)\\])+)\)", fix_anchor, rest)

# ------------------------------------------------------------------ lists and tables
LIST_NUM = re.compile(r"^(\d+)\.\s+(.*?)\s*$")
FN = re.compile(r"\s*\[\^(\d+)\]")
HEB = re.compile(r"[א-ת]")


def plain_item(line: str) -> bool:
    """A short un-numbered list line: Hebrew, with a footnote ref or a link."""
    s = line.strip()
    core = FN.sub("", s)
    core = re.sub(r"\]\([^)]*\)", "]", core)
    if not s or len(core) > 70 or not HEB.search(core[:3] + core[:4]):
        return False
    return bool(FN.search(s) or "](" in s)


heading_stack = []
lists, tables = [], []
out_lines = []
L = rest.split("\n")
i = 0
cur_heading = "intro"
list_ids = set()


def new_id(prefix):
    base = cur_heading
    n, k = base, 2
    while n in list_ids:
        n = f"{base}-{k}"
        k += 1
    list_ids.add(n)
    return n


def make_row(n, text):
    refs = FN.findall(text)
    item = FN.sub("", text).strip()
    item = re.sub(r"\s+$", "", item)
    # footnote continuation lines are indented 4 spaces; outside a footnote that would be code
    note = "\n\n".join(re.sub(r"^ {4}", "", notes.pop(r), flags=re.M) for r in refs)
    return {"n": n, "item": item, "note": note, "added": "", "review": ""}


while i < len(L):
    line = L[i]
    hm = re.match(r"^#{1,6} .*\{#([^}]+)\}$", line)
    if hm:
        cur_heading = hm.group(1)
    # pipe table
    if line.startswith("|"):
        j = i
        while j < len(L) and L[j].startswith("|"):
            j += 1
        block = L[i:j]
        rows = [[c.strip().replace("\\#", "#").replace("\\-", "-").replace("\\_", "_")
                 for c in r.strip().strip("|").split("|")] for r in block if not re.match(r"^\|\s*:?-", r)]
        tid = new_id("table")
        cells_with_fn = [c for r in rows for c in r if FN.search(c)]
        for r_ in rows:
            for k, c in enumerate(r_):
                refs = FN.findall(c)
                if refs:
                    r_[k] = FN.sub("", c).strip() + " " + " ".join(f"(note: {notes.pop(x)})" for x in refs)
        tables.append((tid, rows))
        out_lines.append(f"{{{{table:{tid}}}}}")
        print(f"TABLE {tid}: {len(rows) - 1} rows x {len(rows[0])} cols; cells with notes: {len(cells_with_fn)}")
        i = j
        continue
    # numbered list
    if LIST_NUM.match(line):
        j = i
        items = []
        while j < len(L) and LIST_NUM.match(L[j]):
            items.append(LIST_NUM.match(L[j]).group(2))
            j += 1
        if HEB.search("".join(items)) and len(items) >= 1:
            lid = new_id("list")
            rows = [make_row(k + 1, t) for k, t in enumerate(items)]
            lists.append((lid, "numbered", rows))
            out_lines.append(f"{{{{list:{lid}}}}}")
            i = j
            continue
    # un-numbered list (hard-break lines)
    if plain_item(line):
        j = i
        while j < len(L) and plain_item(L[j]):
            j += 1
        if j - i >= 2:
            lid = new_id("list")
            rows = [make_row(k + 1, t.strip()) for k, t in enumerate(L[i:j])]
            lists.append((lid, "plain", rows))
            out_lines.append(f"{{{{list:{lid}}}}}")
            i = j
            continue
    out_lines.append(line)
    i += 1

body_out = "\n".join(out_lines).strip() + "\n"
body_out = re.sub(r"(\{\{(?:list|table):[^}]+\}\})\n(?!\n)", r"\1\n\n", body_out)
body_out = re.sub(r"([^\n])\n(\{\{(?:list|table):)", r"\1\n\n\2", body_out)

# ------------------------------------------------------------------ write
out.mkdir(parents=True, exist_ok=True)
(out / "lists").mkdir(exist_ok=True)
(out / "tables").mkdir(exist_ok=True)
front = (f"---\ntitle: \"{title}\"\nauthor: \"{author}\"\nversion: \"19.0-draft\"\n"
         f"date: \"\"\nprevious_version: \"v18.2, 5-Jun-2024 (Google Docs)\"\n---\n\n")
remaining = "\n\n".join(f"[^{k}]: {v}" for k, v in notes.items())
(out / "paper.md").write_text(front + body_out + "\n" + remaining + "\n", encoding="utf-8")

for lid, kind, rows in lists:
    with open(out / "lists" / f"{lid}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["n", "item", "note", "added", "review"])
        w.writeheader()
        w.writerows(rows)
for tid, rows in tables:
    with open(out / "tables" / f"{tid}.csv", "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)

print(f"\nlists: {len(lists)}, items: {sum(len(r) for _, _, r in lists)}, tables: {len(tables)}")
print(f"footnotes moved into lists: {735 - len(notes)}, left in prose: {len(notes)}")
for lid, kind, rows in lists:
    print(f"  {lid:55s} {kind:8s} {len(rows):3d}  e.g. {rows[0]['item'][:50]}")
