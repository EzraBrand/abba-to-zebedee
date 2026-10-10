"""Add the gazetteer candidates (status "new") to the master files, as one
"candidates" list per paper section, placed at the end of that section.

Usage: py -3.13 -I scripts/merge_gazetteer.py reports/gazetteer/ paper/
Re-runnable: candidate CSVs are rewritten; placeholders are inserted only once.
To accept a candidate, move its row into the section's main list and clear "added"/"review".
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
gaz_dir, paper = Path(sys.argv[1]), Path(sys.argv[2])
md_path = paper / "paper.md"
md = md_path.read_text(encoding="utf-8")

HEAD = re.compile(r"^(#{1,6}) (.*?) \{#([^}]+)\}$", re.M)


def norm(s: str) -> str:
    s = re.sub(r"\[\^\d+\]", "", s).replace("\\", "").replace("*", "")
    s = re.sub(r"\(.*?\)", "", s)
    s = s.replace("’", "'").replace("“", '"').replace("”", '"').lower()
    return re.sub(r"[^\w]+", " ", s).strip()


# heading -> (id, level, chain of parent titles)
heads = []
stack = []
for m in HEAD.finditer(md):
    level, title, hid = len(m.group(1)), norm(m.group(2)), m.group(3)
    stack = [s for s in stack if s[0] < level] + [(level, title)]
    heads.append({"id": hid, "level": level, "title": title, "chain": [t for _, t in stack], "pos": m.start()})


def find_heading(target: str):
    parts = [norm(p) for p in target.split(">")]
    last = parts[-1]
    cands = [h for h in heads if h["title"] == last]
    if len(cands) > 1:
        cands = [h for h in cands if all(p in h["chain"] for p in parts[:-1])] or cands
    return cands[0] if cands else None


def ref_to_sefaria(ref: str) -> str:
    m = re.match(r"^(.+?) (\d+[ab]):(\d+)", ref.strip())
    return f"{m.group(1).replace(' ', '_')}.{m.group(2)}.{m.group(3)}" if m else ""


groups = defaultdict(list)
unmapped = []
for f in sorted(gaz_dir.glob("*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r["Generated: status"].strip() != "new":
            continue
        h = find_heading(r["Paper: target section"])
        if not h:
            unmapped.append((f.stem, r["Paper: target section"], r["Generated: Hebrew form"]))
            continue
        sref = ref_to_sefaria(r["Bavli: example ref"])
        src = f"[{r['Bavli: example ref'].strip()}](sefaria:{sref})" if sref else r["Bavli: example ref"]
        note = (f"Bavli: {src} ({r['Bavli: hits']} segments). "
                f"Gazetteer: “{r['Gazetteer: entry']}”. {r['Generated: note'].strip()}")
        groups[h["id"]].append({"item": r["Generated: Hebrew form"].strip(), "note": note.strip(),
                                "added": "gazetteer candidate", "review": "pending", "_src": f.stem})

INTRO = ("*Candidate additions from the [Talmud gazetteers](https://github.com/EzraBrand/talmud-nlp-indexer/tree/main/data), "
         "checked against the Bavli text; not yet reviewed:*")
inserted = 0
# insert from the end of the file backwards so offsets stay valid
order = sorted(groups, key=lambda hid: next(h["pos"] for h in heads if h["id"] == hid), reverse=True)
for hid in order:
    lid = f"{hid}-candidates"
    rows = groups[hid]
    with open(paper / "lists" / f"{lid}.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["n", "item", "note", "added", "review"])
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            w.writerow({"n": i, **{k: v for k, v in r.items() if not k.startswith("_")}})
    if f"{{{{list:{lid}}}}}" in md:
        continue
    h = next(h for h in heads if h["id"] == hid)
    nxt = [x for x in heads if x["pos"] > h["pos"]]
    end = nxt[0]["pos"] if nxt else md.find("\n[^")
    block = f"{INTRO}\n\n{{{{list:{lid}}}}}\n\n"
    md = md[:end].rstrip("\n") + "\n\n" + block + md[end:]
    inserted += 1

md_path.write_text(md, encoding="utf-8")
print("sections with candidates:", len(groups), "rows:", sum(len(v) for v in groups.values()), "new placeholders:", inserted)
for u in unmapped:
    print("  unmapped:", u)
