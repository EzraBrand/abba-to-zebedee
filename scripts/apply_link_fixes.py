"""Replace redirected URLs in the master files with their final URL.

Usage: py -3.13 -I scripts/apply_link_fixes.py reports/link_check.csv paper/
Only "redirect" rows outside Sefaria are applied (Sefaria redirects only reorder
search parameters). Dead links are not changed here; see reports/LINK_REPORT.md.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdlinks import escape_url  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
check, paper = Path(sys.argv[1]), Path(sys.argv[2])
fixes = {r["paper_url"]: r["check_final_url"] for r in csv.DictReader(open(check, encoding="utf-8-sig"))
         if r["check_status"] == "redirect" and r["check_final_url"] and "sefaria.org" not in r["paper_domain"]}
files = [paper / "paper.md"] + sorted((paper / "lists").glob("*.csv"))
done = {}
for f in files:
    text = f.read_text(encoding="utf-8-sig" if f.suffix == ".csv" else "utf-8")
    orig = text
    for old, new in fixes.items():
        for o, n in ((escape_url(old), escape_url(new)), (old, new)):
            if f"]({o})" in text:
                text = text.replace(f"]({o})", f"]({n})")
                done[old] = new
    if text != orig:
        f.write_text(text, encoding="utf-8-sig" if f.suffix == ".csv" else "utf-8")
print(f"applied {len(done)} of {len(fixes)} redirects")
for o in fixes:
    if o not in done:
        print("  not found:", o)
