# Gazetteer candidates — summary

Five passes (10-Oct-2026) compared the [talmud-nlp-indexer gazetteers](https://github.com/EzraBrand/talmud-nlp-indexer/tree/main/data) with the paper; two more (15-Oct-2026) checked the entries added to the gazetteers since then, and every Talmud-names entry of the shapes 'bar X' alone, 'name + second word' and 'X the y'. Every example ref was checked automatically to contain its Hebrew form. Each Hebrew form was searched in the Bavli (Sefaria export, same segments as Bekiut) and in the whole paper (body and footnotes).

| Pass | new | uncertain | variant-of-existing | already-in-paper | Details |
|---|---|---|---|---|---|
| anonymous | 35 | 10 | 13 | 39 | [anonymous.md](anonymous.md) |
| family-occupation-traits | 18 | 19 | 8 | 49 | [family-occupation-traits.md](family-occupation-traits.md) |
| given-names | 18 | 24 | 8 | 20 | [given-names.md](given-names.md) |
| honorifics | 39 | 8 | 8 | 9 | [honorifics.md](honorifics.md) |
| toponymic | 14 | 12 | 15 | 6 | [toponymic.md](toponymic.md) |
| update-2026-10 | 7 | 4 | 12 | 27 | [update-2026-10.md](update-2026-10.md) |
| update-2026-10b | 27 | 6 | 11 | 1 | [update-2026-10b.md](update-2026-10b.md) |
| **total** | **158** | **83** | **75** | **150** | |

Only `new` rows are in the paper, as *candidate* lists (`paper/lists/*-candidates.csv`), at the end of their section, marked `review = pending`. To accept a row, move it into the main list of that section and clear `added` and `review`; to reject it, delete it. `uncertain` and `variant-of-existing` rows are only in these CSVs; the notes say why.

Each pass's `.md` file also lists patterns the paper has no section for yet, and corrections (for example the spelling אבא סיקרא, which the Bavli spells אבא סקרא).
