"""Build the link inventory of the paper and the Sefaria -> Bekiut mapping.

Usage: py -3.13 -I scripts/inventory.py source/v18.2.md data/bekiut_sitemap_urls.txt reports/
Writes reports/links_inventory.csv (one row per link occurrence).
"""
import csv
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bekiut import Sitemap, to_bekiut  # noqa: E402
from mdlinks import find_links, footnote_ref_sections, location_index  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
md_path, sitemap_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out_dir.mkdir(parents=True, exist_ok=True)


def master_text(paper_dir: Path) -> str:
    """paper/ (master files) -> one Markdown text: paper.md, then each list CSV as a section.
    sefaria:<Ref> links are turned back into Sefaria URLs so they can be checked and mapped."""
    import csv
    import re

    parts = [(paper_dir / "paper.md").read_text(encoding="utf-8")]
    for f in sorted((paper_dir / "lists").glob("*.csv")):
        parts.append(f"\n\n###### list:{f.stem} {{#list-{f.stem}}}\n")
        for row in csv.DictReader(open(f, encoding="utf-8-sig")):
            parts.append(f"{row['item']}\n\n{row['note']}\n")
    text = "\n".join(parts)
    return re.sub(r"\]\(sefaria:", "](https://www.sefaria.org/", text)


md = master_text(md_path) if md_path.is_dir() else md_path.read_text(encoding="utf-8")
sm = Sitemap(sitemap_path)
locate = location_index(md)
fn_section = footnote_ref_sections(md)

rows = []
for n, ln in enumerate(find_links(md), start=1):
    url = ln.url
    if url.startswith("#"):
        continue
    sec, fn = locate(ln.start)
    if fn:
        sec = fn_section.get(fn, sec)
    bk, kind, ref = to_bekiut(url, sm)
    rows.append({
        "paper_link_id": n,
        "paper_line": md.count("\n", 0, ln.start) + 1,
        "paper_section": sec,
        "paper_footnote": fn,
        "paper_link_text": ln.text,
        "paper_url": url,
        "paper_domain": urlsplit(url).netloc,
        "bekiut_kind": kind if bk else "",
        "bekiut_url": bk or "",
        "bekiut_note": "" if bk else (kind if "sefaria" in url else ""),
        "sefaria_ref": ref,
    })

with open(out_dir / "links_inventory.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

print("links", len(rows), "unique", len({r["paper_url"] for r in rows}))
print(Counter(r["bekiut_kind"] or r["bekiut_note"] or "-" for r in rows))
for r in rows:
    if r["bekiut_note"] and r["bekiut_note"] != "keep:search-or-sheet":
        print("  keep", r["bekiut_note"], r["sefaria_ref"])
