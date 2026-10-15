# Gazetteer candidates — summary

Five passes (10-Oct-2026) compared the [talmud-nlp-indexer gazetteers](https://github.com/EzraBrand/talmud-nlp-indexer/tree/main/data) with the paper; three more (15-Oct-2026) checked the entries added to the gazetteers since then, and every Talmud-names entry of the shapes 'bar X' alone, 'name + second word' and 'X the y', plus a Hebrew-first sweep for X-ah, X-iyah and Physical trait. Every example ref was checked automatically to contain its Hebrew form, and every new item was checked against all list items with a loose spelling match (consonant skeleton). Each Hebrew form was searched in the Bavli (Sefaria export, same segments as Bekiut) and in the whole paper (body and footnotes).

| Pass | new | uncertain | variant-of-existing | already-in-paper | Details |
|---|---|---|---|---|---|
| anonymous | 35 | 10 | 13 | 39 | [anonymous.md](anonymous.md) |
| family-occupation-traits | 18 | 19 | 8 | 49 | [family-occupation-traits.md](family-occupation-traits.md) |
| given-names | 17 | 24 | 9 | 20 | [given-names.md](given-names.md) |
| honorifics | 39 | 8 | 8 | 9 | [honorifics.md](honorifics.md) |
| toponymic | 14 | 12 | 15 | 6 | [toponymic.md](toponymic.md) |
| update-2026-10 | 6 | 4 | 13 | 27 | [update-2026-10.md](update-2026-10.md) |
| update-2026-10b | 22 | 7 | 13 | 3 | [update-2026-10b.md](update-2026-10b.md) |
| update-2026-10c | 0 | 0 | 3 | 0 | [update-2026-10c.md](update-2026-10c.md) |
| **total** | **151** | **84** | **82** | **153** | |

Only `new` rows are in the paper, as *candidate* lists (`paper/lists/*-candidates.csv`), at the end of their section, marked `review = pending`. To accept a row, move it into the main list of that section and clear `added` and `review`; to reject it, delete it. `uncertain` and `variant-of-existing` rows are only in these CSVs; the notes say why.

Each pass's `.md` file also lists patterns the paper has no section for yet, and corrections (for example the spelling אבא סיקרא, which the Bavli spells אבא סקרא).
