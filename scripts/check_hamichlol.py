"""Second pass for hamichlol.org.il links, which return 403 (Cloudflare) to scripts.

For each title: try hamichlol's MediaWiki API; and look the same title up on he.wikipedia,
which hamichlol largely mirrors. Results are merged into reports/link_check.csv
(check_note and an alternative URL in check_final_url when the page is on he.wikipedia).

Usage: py -3.13 -I scripts/check_hamichlol.py reports/link_check.csv
"""
import csv
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import requests

sys.stdout.reconfigure(encoding="utf-8")
path = Path(sys.argv[1])
rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
fields = list(rows[0])
UA = "abba-to-zebedee-linkcheck/0.1 (personal research)"
targets = [r for r in rows if "hamichlol.org.il" in r["paper_domain"] and r["check_status"] == "dead"]
titles = {unquote(urlsplit(r["paper_url"]).path.lstrip("/")).replace("_", " "): r for r in targets}

api_ok = None
try:
    t = requests.post("https://www.hamichlol.org.il/w/api.php",
                      data={"action": "query", "titles": "|".join(list(titles)[:50]), "format": "json",
                            "formatversion": 2}, headers={"User-Agent": UA}, timeout=40)
    api_ok = t.status_code == 200 and "query" in t.text
    print("hamichlol api", t.status_code, api_ok)
except requests.RequestException as e:
    print("hamichlol api error", e)

names = list(titles)
found = {}
for i in range(0, len(names), 50):
    r = requests.post("https://he.wikipedia.org/w/api.php",
                      data={"action": "query", "titles": "|".join(names[i:i + 50]), "redirects": 1,
                            "format": "json", "formatversion": 2}, headers={"User-Agent": UA}, timeout=60).json()
    q = r["query"]
    norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
    red = {n["from"]: n["to"] for n in q.get("redirects", [])}
    pages = {p["title"]: p for p in q.get("pages", [])}
    for n in names[i:i + 50]:
        t1 = norm.get(n, n)
        t2 = red.get(t1, t1)
        if t2 in pages and not pages[t2].get("missing"):
            found[n] = t2

for n, r in titles.items():
    r["check_status"] = "manual"
    if n in found:
        r["check_final_url"] = "https://he.wikipedia.org/wiki/" + quote(found[n].replace(" ", "_"))
        r["check_note"] = "hamichlol blocks scripts (403); same article exists on he.wikipedia"
    else:
        r["check_note"] = "hamichlol blocks scripts (403); no he.wikipedia article — check in browser"
        if r["wayback_url"]:
            r["check_note"] += "; Wayback has a copy"

with open(path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
print("hamichlol links", len(titles), "on he.wikipedia", len(found))
