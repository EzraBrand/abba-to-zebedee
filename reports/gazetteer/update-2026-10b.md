# Gazetteer pass: update 2026-10b (all Talmud-names entries of three shapes)

Earlier passes picked gazetteer entries with filters. This pass took every entry of the current
`talmud_names_gazetteer.txt` (15-Oct) that has one of three English shapes:
- 'bar X' alone (133 entries),
- 'name + second word' (430),
- 'X the y' (47).

For each entry, a script found the Steinsaltz segments and picked the Aramaic word that sounds like
the surname or patronymic (consonant skeleton). It then searched the paper (`paper.md` and all lists,
without nikud): 445 forms were already in the paper and 91 were not. I reviewed the 91 by hand;
most 'name + second word' rows were misalignments of bare 'Title + Name' entries. A second script
checked that every example segment contains its Hebrew form (0 mismatches here and in the five
10-Oct passes).

45 rows in `update-2026-10b.csv`: **4 new**, 9 uncertain, 14 variant-of-existing, 18 already-in-paper.

New items:
- Patronymic Alone, No Given Name (18): בר קמצא, בן סירא, בן בתירא (used alone), בן קטין, בן דרוסאי,
  בן אלעשה, בן קמצר, בן ביבאי, בן ארזא, בן מגוסת, בן דונאי, בן תמליון (a demon), בן אבטיח, בן תדל,
  בר פיולי, בר ביניתוס, בר שישך, בר קיפוק / קיפוף.
- Given names not in the paper: פדת (20 segments), אביתר, יחזקאל (Hebrew origin).
- Pseudonyms and Epithets: יוסף שידא.

Variants of existing items: בר תאוטני / תוטיני (listed בר תוטני), בן דמא (listed בן דמה),
בר המדודי (listed המדורי), זוטראי, מנשי, אילפי, יודאפה, קרחינא, אבא סקרא, and (corrected later on 15-Oct)
שזבי (listed רב שיזבי), שעורים (listed רב סעורם). Already in the paper: אצר פירי (listed אוצר פירי),
הסגן (Non-Semitic word). סמיא is uncertain: possibly the listed סמא / סימאי.

Update (15-Oct, later): after *Figures on the Fringes* and the Ben Bag Bag list were added to the paper, most of the Patronymic Alone items above are already in the paper (בן סירא, בן קטין, בר פיולי, בר קמצא …), and so are בן דרוסאי, בר שישך, בן תמליון, יוסף שידא. בר קיפוק and בן דונאי moved to update-2026-10d (Fringes: Jewish Commoners). Still new: בן בתירא (used alone), פדת, אביתר, יחזקאל.
