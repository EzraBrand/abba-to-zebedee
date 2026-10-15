# AGENTS.md — From Abba to Zebedee

Guide for AI agents (Claude Code, Codex) working in this repo. Read `README.md` for the layout,
build commands and the ref-link scheme. This file adds what the code and README do not tell you:
the owner's priorities, the gazetteer workflow, the checks, and known pitfalls.

## What this project is

Ezra Brand's survey of naming conventions in rabbinic literature, migrated from Google Docs (v18.2)
into a repo that builds a website (<https://ezrabrand.github.io/abba-to-zebedee/>).
- `paper/paper.md` is the master prose; `paper/lists/<id>.csv` are the master lists (one item per row,
  sources in `note`). `docs/` is built output; never edit it by hand.
- Since 15-Oct-2026 the paper also contains the author's separate paper *Figures on the Fringes:
  Named Non-rabbis in the Talmudic Literature* (last chapter: Jewish commoners, women, non-Jews,
  angels and demons), and the section "Patronymic, Not Father's Name" has the items of his *Ben Bag
  Bag, Ben He He, and Beyond* that were not elsewhere in the survey.

## What the owner values (15-Oct-2026)

- **Highest value: new list entries per section, found in the talmud-nlp-indexer gazetteers and
  checked against the Bavli.** He was not interested in audits, inventories, maps or statistics.
- Women and non-Jews go **only** to the Figures on the Fringes lists, not to the naming-pattern sections.
  Jewish non-rabbis go there too; rabbis known by one name go to Mononyms.
- An item is `new` only if it is **nowhere** in the paper (body, footnotes, any list).
- Edits to his own text (Fringes, Ben Bag Bag) need his OK. Report problems in `reports/`, do not fix
  silently. He did OK adding Bavli sources to unsourced Fringes items.
- Push to `main` only when he says so; pushing republishes the site.

## Gazetteer workflow

1. Inputs: `external/talmud-nlp-indexer/data/*.txt` (gazetteers; may be older than GitHub — compare)
   and the Bavli via `scripts/talmud_search.py` (Sefaria export, Aramaic + Steinsaltz English, same
   segments as Bekiut). `--en --show-other` finds an English name and shows the Aramaic of that segment.
2. Write a pass to `reports/gazetteer/<pass>.csv` (columns as in the existing passes) and a short
   `<pass>.md`. Statuses: `new`, `uncertain`, `variant-of-existing`, `already-in-paper`.
   **Name a new pass so it sorts last** (e.g. `update-2026-11.csv`): the merge reads reports in name
   order and numbers candidate rows in that order.
3. Run both checks on the pass, and fix every hit before merging:
   - `py -3.13 -I scripts/check_refs.py reports/gazetteer/<pass>.csv` — the example segment must contain
     the Hebrew form. Never write a ref from memory; this check caught several invented refs.
   - `py -3.13 -I scripts/check_spelling.py reports/gazetteer/<pass>.csv` — loose spelling match
     (consonant skeleton) against every list item and the body. Exact matching missed items such as
     שזבי = שיזבי, שעורים = סעורם, אצר פירי = אוצר פירי.
4. `py -3.13 -I scripts/merge_gazetteer.py reports/gazetteer/ paper/` → `*-candidates.csv` lists
   (`review = pending`) at the end of each section. It also links every Bavli ref in the notes.
5. `py -3.13 -I scripts/build_site.py`, check the page, commit.
6. Update the counts in `reports/gazetteer/SUMMARY.md`.

Passes done (see SUMMARY.md): anonymous, family-occupation-traits, given-names, honorifics,
toponymic (10-Oct); update-2026-10, -10b (shapes: 'bar X' alone, 'name + word', 'X the y'),
-10c (Hebrew-first X-ah / X-iyah / trait sweep: nothing new, these lists are complete for titled
names), -10d (one-word names), -10e (untitled names; Bar/Ben X toponymic) (15-Oct).

## Pitfalls

- Read CSVs with `open(..., encoding="utf-8-sig", newline="")` and write with `newline=""`.
  Without `newline=""`, notes with line breaks corrupt the file (this broke a list on 15-Oct).
- Do not scan all ~82k segments once per entry: build a word index first (minutes → seconds), and
  print progress.
- Sound-based alignment (English → Aramaic consonant skeleton) is noisy for short names and for names
  that start with ו/ד/ל/ב/מ/ש/כ; always read the segment.
- Bash heredocs on this Windows machine halve backslashes; put regex-heavy scripts in files.
- Use `py -3.13 -I`; the console is cp1252, so start scripts with `sys.stdout.reconfigure(encoding="utf-8")`.
- If a GitHub Pages deploy hangs at `updating_pages` and times out, request a fresh build
  (`gh api -X POST repos/EzraBrand/abba-to-zebedee/pages/builds`); re-running the failed job reuses the
  cancelled deployment ID and fails.
- `build/` and `external/` are git-ignored: put anything worth keeping in `scripts/` or `reports/`.

## Next todos

Gazetteer work (the owner's priority):
- [ ] The 76 shape-pass entries whose Aramaic form did not align (update-2026-10b): align by hand.
- [ ] Variants and hypocorisms: gazetteer clusters with several spellings of one person
      (Minyumi / Minyomi / Manyumi …) → pairs for "Variants, Hypocorisms, and Shortenings".
- [ ] The 93 `uncertain` rows across passes: resolve with more evidence.
- [ ] Gazetteer entries added after 15-Oct-2026: diff, as in update-2026-10.
- [ ] Sections still without candidates: No surname, Imma, Abba + toponym / occupation / trait,
      X, X-i, Double names, Surnames with Unclear Etymology, kotel / katol / katlan.

Waiting on the owner:
- [ ] Review the 159 pending candidates (accept = move into the main list, clear `added` / `review`).
- [ ] Figures on the Fringes: ישו and ניקנור are in two lists; אפרא הורמיז is listed as a Jewish woman
      (she was Shapur II's mother). See `reports/FRINGES_REVIEW.md`.
- [ ] Spelling corrections noted in the reports (e.g. the paper's אבא סיקרא; the Bavli has סקרא).

## Ideas (not started)

See `reports/IDEAS.md`: sources for every item, manuscript readings (AlHaTorah, with permission),
citable item IDs and a DOI dataset, topic essays, a Bekiut names layer that links the text to the lists.
