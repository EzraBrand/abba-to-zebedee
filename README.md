# From Abba to Zebedee

Master copy of Ezra Brand, *From Abba to Zebedee: A Comprehensive Survey of Naming Conventions in the
Mishnah, Talmud, and Late Antique Midrash* — the prose, the name lists as data, and the website.

- **Site:** <https://ezrabrand.github.io/abba-to-zebedee/> (built into `docs/`)
- **Earlier versions:** v18.2 (Google Docs, 5-Jun-2024) is in `source/`; PDF on
  [Academia.edu](https://www.academia.edu/94788129/From_Abba_to_Zebedee_A_Comprehensive_Survey_of_Naming_Conventions_in_the_Mishnah_Talmud_and_Late_Antique_Midrash).

## Layout

| Path | What |
|---|---|
| `paper/paper.md` | **Master** prose (pandoc Markdown). `{{list:<id>}}` and `{{table:<id>}}` mark where a list or table goes. |
| `paper/lists/<id>.csv` | **Master** name lists: `n, item, note, added, review`. One row per item; `note` holds the sources (Markdown). |
| `paper/lists/<id>-candidates.csv` | Gazetteer candidates for a section, `review = pending`. Accept: move the row into the main list. |
| `paper/tables/<id>.csv` | The frequency tables. |
| `site/` | Page template, CSS, JS. |
| `docs/` | Built site (GitHub Pages). Do not edit; run the build. |
| `data/` | Bekiut sitemap snapshot; `ref_overrides.csv` (Mishnah refs that Bekiut shows on a Bavli page). |
| `reports/` | Link check (`LINK_REPORT.md`, `link_check.csv`), gazetteer passes (`gazetteer/SUMMARY.md`). |
| `source/` | v18.2 Google Docs export. Never edited. |
| `scripts/` | Everything else (below). |

## Links: store refs, not URLs

Links to texts are written as `[Berakhot 2a](sefaria:Berakhot.2a.2)`. The build turns each ref into a URL:
Bekiut when Bekiut has the text, else Sefaria. Bekiut's section anchor `#n` is Sefaria segment *n*.

| Ref | Link |
|---|---|
| `sefaria:Berakhot.2a.2` | `https://bekiut.com/talmud/Berakhot/2a#2` |
| `sefaria:Jerusalem_Talmud_Berakhot.3.1.19` | `https://bekiut.com/yerushalmi/Berakhot/3.1#19` |
| `sefaria:Mishnah_Shekalim.1.4` | `https://bekiut.com/mishnah/Shekalim/1#4` (tractates with no Bavli) |
| `sefaria:Mishnah_Sanhedrin.7.2` | the Bavli segment, from `data/ref_overrides.csv` |
| `sefaria:I_Chronicles.4.5` | `https://bekiut.com/bible/i-chronicles/4#5` |
| `sefaria:Jastrow,_קַשָּׁא_II.1` | `https://bekiut.com/jastrow?q=קַשָּׁא II` |
| `sefaria:Bereishit_Rabbah.42.5` | `https://www.sefaria.org/Bereishit_Rabbah.42.5` (not on Bekiut) |

## Build and check (run from the repo root; needs Python 3.13 and pandoc)

```bash
py -3.13 -I scripts/build_site.py
```

```bash
py -3.13 -I scripts/inventory.py paper data/bekiut_sitemap_urls.txt reports
```

```bash
py -3.13 -I scripts/check_links.py reports/links_inventory.csv data/bekiut_sitemap_urls.txt reports
```

The link check also runs monthly as a GitHub Action (report as an artifact; it changes nothing).

| Script | Does |
|---|---|
| `build_site.py` | `paper/` → `docs/`: the paper, the all-items page, CSV downloads. |
| `bekiut.py` | Ref → Bekiut/Sefaria URL. |
| `inventory.py`, `check_links.py`, `check_hamichlol.py`, `link_report.py` | Link inventory and link-rot check. |
| `apply_link_fixes.py` | Writes redirect targets into `paper/`. |
| `merge_gazetteer.py` | `reports/gazetteer/*.csv` (status `new`) → candidate lists in `paper/`. Files merge in name order, so name a new pass so it sorts last (e.g. `update-2026-10.csv`). |
| `fetch_sefaria_bavli.py`, `talmud_search.py` | Download the Bavli (Aramaic + Steinsaltz English) from the Sefaria export; regex search with Bekiut links. |
| `convert_source.py`, `verify_migration.py` | One-time migration from the Google Docs export (kept for the record). |

Gazetteer work needs two downloads into `external/` (ignored by git):

```bash
git clone --depth 1 https://github.com/EzraBrand/talmud-nlp-indexer.git external/talmud-nlp-indexer
```

```bash
py -3.13 -I scripts/fetch_sefaria_bavli.py data/bekiut_sitemap_urls.txt external/sefaria-export
```
