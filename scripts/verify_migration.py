"""Check that the migration kept all text and that internal anchors resolve.

Usage: py -3.13 -I scripts/verify_migration.py source/v18.2.md paper/
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
src, paper = Path(sys.argv[1]), Path(sys.argv[2])
old = src.read_text(encoding="utf-8")
new_parts = [(paper / "paper.md").read_text(encoding="utf-8")]
for f in sorted((paper / "lists").glob("*.csv")) + sorted((paper / "tables").glob("*.csv")):
    for row in csv.reader(open(f, encoding="utf-8-sig")):
        new_parts.append(" ".join(row))
new = "\n".join(new_parts)


def strip_urls(s):
    return re.sub(r"\]\([^)\s]*\)", "]", s)


def letters(s):
    s = strip_urls(s)
    return Counter(c for c in s if c.isalpha())


# The dropped Outline and title lines account for some Latin letters; compare Hebrew exactly.
o0, o1 = old.index("# Outline"), old.index("# Bibliography")
old_wo_outline = old[:o0] + old[o1:]
a, b = letters(old_wo_outline), letters(new)
heb = lambda c: "א" <= c <= "ת"  # noqa: E731
ha = sum(v for k, v in a.items() if heb(k))
hb = sum(v for k, v in b.items() if heb(k))
la = sum(v for k, v in a.items() if not heb(k))
lb = sum(v for k, v in b.items() if not heb(k))
print(f"Hebrew letters: source {ha}, new {hb}, diff {hb - ha}")
print(f"Other letters:  source {la}, new {lb}, diff {lb - la} (front matter + CSV headers + 'sefaria:' scheme expected)")

# Internal anchors
md = new_parts[0]
ids = set(re.findall(r"\{#([^}]+)\}", md))
bad = [m for m in re.findall(r"\]\(#([^)]+)\)", md) if m not in ids]
print("internal links:", len(re.findall(r"\]\(#", md)), "broken:", bad[:10])
# Footnotes in prose
refs = re.findall(r"\[\^(\d+)\](?!:)", md)
defs = re.findall(r"^\[\^(\d+)\]:", md, re.M)
print("prose footnote refs", len(refs), "defs", len(defs), "unmatched", set(refs) ^ set(defs))
# Placeholders
ph = re.findall(r"\{\{(list|table):([^}]+)\}\}", md)
missing = [p for k, p in ph if not (paper / (k + "s") / f"{p}.csv").exists()]
print("placeholders", len(ph), "missing files", missing)
