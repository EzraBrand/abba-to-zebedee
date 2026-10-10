"""Write reports/LINK_REPORT.md from reports/link_check.csv.

Usage: py -3.13 -I scripts/link_report.py reports/link_check.csv reports/LINK_REPORT.md
Sites that answer scripts with 403/400 (Cloudflare, Facebook) are re-labelled "manual".
"""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
src, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
BLOCKERS = {"lsj.gr": "Cloudflare challenge", "judaism.stackexchange.com": "403 to scripts",
            "www.facebook.com": "Facebook refuses scripts"}
for r in rows:
    if r["check_status"] == "dead" and r["paper_domain"] in BLOCKERS:
        r["check_status"] = "manual"
        r["check_note"] = BLOCKERS[r["paper_domain"]] + "; check in browser" + ("; Wayback has a copy" if r["wayback_url"] else "")
with open(src, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

st = Counter(r["check_status"] for r in rows)
occ = sum(int(r["paper_occurrences"]) for r in rows)
lines = [
    "# Link check — v18.2", "",
    f"Checked {len(rows)} unique URLs ({occ} links in the paper). Run `scripts/check_links.py` to repeat.", "",
    "| Result | URLs |", "|---|---|",
    *[f"| {k} | {v} |" for k, v in st.most_common()], "",
    "- **ok**: the page exists (Wikimedia and Sefaria through their APIs; other sites by HTTP).",
    "- **redirect**: the page moved. Non-Sefaria redirects are now updated in `paper/` "
    "(`scripts/apply_link_fixes.py`). Sefaria search links only reorder their parameters.",
    "- **manual**: the site blocks scripts (Cloudflare, Academia.edu, Facebook). These need a check in a browser.",
    "- **dead**: the page does not exist.", "",
]
dead = [r for r in rows if r["check_status"] == "dead"]
lines += ["## Dead links", ""] + ([f"- {r['paper_url']} — {r['check_note']} (section: {r['paper_first_section']})"
                                  + (f" — archived: {r['wayback_url']}" if r["wayback_url"] else "") for r in dead]
                                 or ["None."]) + [""]
manual = [r for r in rows if r["check_status"] == "manual"]
by = Counter(r["paper_domain"] for r in manual)
lines += ["## Manual check needed", "", "| Site | URLs | Why |", "|---|---|---|"]
for d, n in by.most_common():
    note = next(r["check_note"] for r in manual if r["paper_domain"] == d).split(";")[0]
    lines.append(f"| {d} | {n} | {note} |")
alt = [r for r in manual if "he.wikipedia" in r["check_final_url"]]
if alt:
    lines += ["", "Hamichlol pages that also exist on he.wikipedia (possible replacement):", ""]
    lines += [f"- {r['paper_link_text']} → {r['check_final_url']}" for r in alt]
lines += ["", "The full list is in `reports/link_check.csv` (filter `check_status`)."]
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(st)
