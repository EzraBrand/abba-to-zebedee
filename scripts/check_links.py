"""Check every link in the inventory for link rot, and validate Bekiut targets.

Usage: py -3.13 -I scripts/check_links.py reports/links_inventory.csv data/bekiut_sitemap_urls.txt reports/
Writes:
  reports/link_check.csv          one row per unique original URL
  reports/sefaria_refs.json       cache of Sefaria API answers (re-used on re-runs)
"""
import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bekiut import BASE, Sitemap  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
inv_path, sitemap_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sm = Sitemap(sitemap_path)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0 Safari/537.36")
BOT_UA = "abba-to-zebedee-linkcheck/0.1 (https://github.com/EzraBrand; personal research)"
S = requests.Session()
S.headers["User-Agent"] = UA

rows = list(csv.DictReader(open(inv_path, encoding="utf-8-sig")))
urls = sorted({r["paper_url"] for r in rows})
by_url = {r["paper_url"]: r for r in rows}
result = {u: {"check_status": "", "check_http": "", "check_final_url": "", "check_note": ""} for u in urls}

# ---------------------------------------------------------------- Wikimedia
WIKI = re.compile(r"^(?:https?://)?([a-z\-]+)\.(?:m\.)?(wikipedia|wikisource|wiktionary)\.org/wiki/([^#?]+)(#.*)?$")
wiki_groups = {}
for u in urls:
    m = WIKI.match(u)
    if m:
        host = f"{m.group(1)}.{m.group(2)}.org"
        title = unquote(m.group(3)).replace("_", " ")
        wiki_groups.setdefault(host, {}).setdefault(title, []).append(u)


def wiki_query(api, titles):
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        r = S.post(api, data={"action": "query", "titles": "|".join(chunk), "redirects": 1,
                              "prop": "pageprops", "ppprop": "disambiguation",
                              "format": "json", "formatversion": 2},
                   headers={"User-Agent": BOT_UA}, timeout=60)
        r.raise_for_status()
        q = r.json()["query"]
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redir = {n["from"]: n["to"] for n in q.get("redirects", [])}
        pages = {p["title"]: p for p in q.get("pages", [])}
        for t in chunk:
            t1 = norm.get(t, t)
            t2 = redir.get(t1, t1)
            p = pages.get(t2, {})
            if p.get("missing") or p.get("invalid"):
                out[t] = ("dead", "", "page does not exist")
            elif t2 != t1:
                out[t] = ("redirect", t2, f"redirects to “{t2}”")
            elif "pageprops" in p and "disambiguation" in p["pageprops"]:
                out[t] = ("ok", "", "disambiguation page")
            else:
                out[t] = ("ok", "", "")
        time.sleep(0.5)
    return out


for host, titles in wiki_groups.items():
    ans = wiki_query(f"https://{host}/w/api.php", list(titles))
    for t, (status, target, note) in ans.items():
        for u in titles[t]:
            frag = WIKI.match(u).group(4) or ""
            final = ""
            if target:
                final = f"https://{host}/wiki/{quote(target.replace(' ', '_'))}{frag}"
            result[u].update(check_status=status, check_final_url=final, check_note=note,
                             check_http="api")
    print("wiki", host, len(titles))

# ---------------------------------------------------------------- Sefaria refs
cache_path = out_dir / "sefaria_refs.json"
cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}


def sefaria_text(ref):
    if ref in cache:
        return cache[ref]
    r = S.get(f"https://www.sefaria.org/api/texts/{quote(ref)}",
              params={"context": 0, "pad": 0, "commentary": 0}, timeout=60,
              headers={"User-Agent": BOT_UA})
    try:
        j = r.json()
    except ValueError:
        j = {"error": f"HTTP {r.status_code}"}
    he = j.get("he")
    ans = {"error": j.get("error", ""), "has_text": bool(he and (he if isinstance(he, str) else any(he))),
           "ref": j.get("ref", ""), "length": len(he) if isinstance(he, list) else None}
    cache[ref] = ans
    time.sleep(0.25)
    return ans


def sefaria_mishnah_in_bavli(ref):
    key = "links:" + ref
    if key not in cache:
        r = S.get(f"https://www.sefaria.org/api/links/{quote(ref)}", params={"with_text": 0},
                  timeout=60, headers={"User-Agent": BOT_UA})
        hits = [l["ref"] for l in r.json() if l.get("type") == "mishnah in talmud"
                and l.get("category") == "Talmud" and not l["ref"].startswith("Jerusalem")]
        cache[key] = hits
        time.sleep(0.25)
    return cache[key]


SEF = [u for u in urls if "sefaria.org" in urlsplit(u).netloc]
for u in SEF:
    r = by_url[u]
    ref = r["sefaria_ref"]
    if not ref or r["bekiut_note"] == "keep:search-or-sheet":
        continue
    if r["bekiut_kind"] == "jastrow":
        # The text API returns no text for dictionary entries; the site links these to Bekiut's Jastrow.
        result[u].update(check_status="ok", check_http="-", check_note="Jastrow entry; links to Bekiut")
        continue
    a = sefaria_text(ref)
    if a["error"]:
        result[u].update(check_status="dead", check_http="api", check_note=f"Sefaria: {a['error']}")
    elif not a["has_text"]:
        result[u].update(check_status="dead", check_http="api", check_note="Sefaria: ref resolves but has no text")
    else:
        result[u].update(check_status="ok", check_http="api")
print("sefaria refs", len(SEF))

# Mishnah links in tractates that have Bavli: Bekiut has no Mishnah page, so use the Bavli page.
bekiut_fix = {}
for u in SEF:
    r = by_url[u]
    if r["bekiut_note"] == "no-bekiut-tractate" and r["sefaria_ref"].startswith("Mishnah_"):
        ref = r["sefaria_ref"].replace("Ta'anit", "Taanit")
        hits = sefaria_mishnah_in_bavli(ref)
        if hits:
            m = re.match(r"^(.+?) (\d+[ab]):(\d+)", hits[0])
            tr = m.group(1).replace(" ", "_")
            if tr in sm.talmud:
                bekiut_fix[u] = (f"{BASE}/talmud/{tr}/{m.group(2)}#{m.group(3)}", f"mishnah-via-bavli ({hits[0]})")

cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------------------------------------------------------------- everything else
BOT_BLOCKERS = ("academia.edu", "facebook.com", "jstor.org", "cambridge.org", "academic.oup.com",
                "researchgate.net")


def http_check(u):
    try:
        resp = S.get(u, timeout=40, allow_redirects=True, stream=True)
        code = resp.status_code
        final = resp.url
        resp.close()
    except requests.RequestException as e:
        return u, ("dead", "error", "", type(e).__name__)
    host = urlsplit(u).netloc
    if code >= 400:
        if code in (401, 403, 429, 999) and any(b in host for b in BOT_BLOCKERS):
            return u, ("manual", str(code), final if final != u else "", "site blocks scripts; check in browser")
        return u, ("dead", str(code), final if final != u else "", "")
    moved = final.rstrip("/") != u.rstrip("/")
    return u, ("redirect" if moved else "ok", str(code), final if moved else "", "")


rest = [u for u in urls if not result[u]["check_status"] and not
        ("sefaria.org" in u and by_url[u]["bekiut_note"] != "keep:search-or-sheet" and by_url[u]["sefaria_ref"])]
with ThreadPoolExecutor(max_workers=6) as ex:
    for u, (st, code, final, note) in ex.map(http_check, rest):
        result[u].update(check_status=st, check_http=code, check_final_url=final, check_note=note)
print("http", len(rest))

# ---------------------------------------------------------------- Wayback for dead links


def wayback(u):
    try:
        r = S.get("https://archive.org/wayback/available", params={"url": u}, timeout=40,
                  headers={"User-Agent": BOT_UA})
        snap = r.json().get("archived_snapshots", {}).get("closest", {})
        return snap.get("url", "") if snap.get("available") else ""
    except (requests.RequestException, ValueError):
        return ""


dead = [u for u in urls if result[u]["check_status"] == "dead" and "sefaria.org" not in u]
for u in dead:
    result[u]["wayback_url"] = wayback(u)
    time.sleep(1)

# ---------------------------------------------------------------- write
fields = ["paper_url", "paper_domain", "paper_occurrences", "paper_first_section", "paper_first_footnote",
          "paper_link_text", "check_status", "check_http", "check_final_url", "check_note", "wayback_url",
          "bekiut_url", "bekiut_kind"]
occ = {}
for r in rows:
    occ[r["paper_url"]] = occ.get(r["paper_url"], 0) + 1
with open(out_dir / "link_check.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for u in urls:
        r = by_url[u]
        bk, kind = r["bekiut_url"], r["bekiut_kind"]
        if u in bekiut_fix:
            bk, kind = bekiut_fix[u]
        w.writerow({"paper_url": u, "paper_domain": r["paper_domain"], "paper_occurrences": occ[u],
                    "paper_first_section": r["paper_section"], "paper_first_footnote": r["paper_footnote"],
                    "paper_link_text": r["paper_link_text"], **result[u],
                    "wayback_url": result[u].get("wayback_url", ""), "bekiut_url": bk, "bekiut_kind": kind})

from collections import Counter  # noqa: E402
print(Counter(v["check_status"] for v in result.values()))
