"""Download the Bavli (William Davidson Edition: Aramaic + Steinsaltz English) from the
public Sefaria export bucket. Bekiut serves the same Sefaria data, so array index n
(1-based) of a daf is the Bekiut anchor #n.

Usage: py -3.13 -I scripts/fetch_sefaria_bavli.py data/bekiut_sitemap_urls.txt external/sefaria-export/
"""
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests

sitemap, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
tractates = sorted({urlsplit(u).path.split("/")[2] for u in sitemap.read_text(encoding="utf-8").split()
                    if urlsplit(u).path.startswith("/talmud/") and urlsplit(u).path.count("/") == 3})
S = requests.Session()
BUCKET = "https://storage.googleapis.com/sefaria-export/json/"
for tr in tractates:
    title = tr.replace("_", " ")
    idx = S.get(f"https://www.sefaria.org/api/v2/raw/index/{quote(title)}", timeout=60).json()
    cats = idx["categories"]  # e.g. ['Talmud', 'Bavli', 'Seder Zeraim']
    for lang, version in (("Hebrew", "William Davidson Edition - Aramaic"),
                          ("English", "William Davidson Edition - English")):
        dest = out / f"{tr}.{lang}.json"
        if dest.exists():
            continue
        url = BUCKET + quote("/".join(cats + [title, lang, version]) + ".json")
        r = S.get(url, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(tr, lang, len(r.content))
        time.sleep(0.2)
print("tractates", len(tractates))
