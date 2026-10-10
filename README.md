# From Abba to Zebedee — update project

Working repo for updating Ezra Brand, *From Abba to Zebedee: A Comprehensive Survey of Naming
Conventions in the Mishnah, Talmud, and Late Antique Midrash*
([Academia.edu](https://www.academia.edu/94788129/From_Abba_to_Zebedee_A_Comprehensive_Survey_of_Naming_Conventions_in_the_Mishnah_Talmud_and_Late_Antique_Midrash)).

Goals:
1. Check all hyperlinks for link rot.
2. Move Sefaria links to [Bekiut](https://bekiut.com) where Bekiut has the text.
3. Add list items found in the gazetteers of
   [talmud-nlp-indexer](https://github.com/EzraBrand/talmud-nlp-indexer/tree/main/data).
4. Publish as a GitHub Page (later: inside Bekiut), with better presentation (tables etc.).

## Layout

| Path | What |
|---|---|
| `source/v18.2.md` | Google Docs Markdown export, v18.2 (5-Jun-2024). Never edited; the base for all output. |
| `data/bekiut_sitemap_urls.txt` | Bekiut sitemap snapshot, used to check that Bekiut targets exist. |
| `scripts/` | All processing (see below). |
| `reports/` | Generated CSVs: link inventory, link check, gazetteer candidates. |
| `build/`, `external/` | Ignored. Caches; the indexer repo clone; the Sefaria export download. |

## Scripts (run from the repo root, `py -3.13 -I`)

| Script | Does |
|---|---|
| `mdlinks.py` | Parses Markdown links (handles Google Docs `\(` `\)` escapes) and locates them by section/footnote. |
| `bekiut.py` | Sefaria URL → Bekiut URL mapping. |
| `inventory.py` | `source/v18.2.md` → `reports/links_inventory.csv`. |
| `check_links.py` | Link-rot check → `reports/link_check.csv`. |
| `fetch_sefaria_bavli.py` | Downloads the Bavli (Aramaic + Steinsaltz English) from the public Sefaria export bucket into `external/sefaria-export/`. |
| `talmud_search.py` | Regex search of that Bavli dump; prints Bekiut segment links. |

Setup after a fresh clone:

```bash
git clone --depth 1 https://github.com/EzraBrand/talmud-nlp-indexer.git external/talmud-nlp-indexer
py -3.13 -I scripts/fetch_sefaria_bavli.py data/bekiut_sitemap_urls.txt external/sefaria-export
py -3.13 -I scripts/inventory.py source/v18.2.md data/bekiut_sitemap_urls.txt reports
py -3.13 -I scripts/check_links.py reports/links_inventory.csv data/bekiut_sitemap_urls.txt reports
```

## Sefaria → Bekiut mapping

Bekiut serves Sefaria's text, and its section anchor `#n` is Sefaria segment *n*
(checked on `/talmud/Berakhot/2a`, `/yerushalmi/Berakhot/3.1`, `/yerushalmi/Taanit/1.4`).

| Sefaria | Bekiut |
|---|---|
| `Berakhot.2a.2` | `/talmud/Berakhot/2a#2` |
| `Jerusalem_Talmud_Berakhot.3.1.19` | `/yerushalmi/Berakhot/3.1#19` |
| `Mishnah_Shekalim.1.4` | `/mishnah/Shekalim/1#4` (only tractates with no Bavli) |
| `Mishnah_Sanhedrin.7.2` | the Bavli segment where Sefaria places that mishnah |
| `I_Chronicles.4.5` | `/bible/i-chronicles/4#5` |
| `Jastrow,_קַשָּׁא_II.1` | `/jastrow?q=קַשָּׁא II` |

Midrash, Tosefta, commentaries, sheets and Sefaria searches stay on Sefaria.
