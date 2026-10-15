"""Loose check of 'new' report rows against every list item word and the paper body: compare consonant
skeletons (drop ו י א ה ע; ש=ס, ת=ט, כ=ק, ב=ו). Prints possible matches for manual review.
Usage: py -3.13 -I scripts/check_spelling.py reports/gazetteer/<file>.csv ..."""
import csv, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
NIK = re.compile(r"[֑-ׇ]")
FIN = str.maketrans("ךםןףץ", "כמנפצ")


def skel(w):
    w = NIK.sub("", w).translate(FIN)
    w = re.sub(r"^[ודה](?=.{3})", "", w)          # one prefix letter
    w = re.sub(r"[ויאהע]", "", w)
    return w.translate(str.maketrans("שתכב", "סטקו"))


words = {}
for f in (ROOT / "paper" / "lists").glob("*.csv"):
    if f.stem.endswith("-candidates"):
        continue
    for r in csv.DictReader(open(f, encoding="utf-8-sig", newline="")):
        for w in re.findall(r"[א-ת]{3,}", NIK.sub("", r["item"])):
            words.setdefault(skel(w), set()).add(f"{f.stem}: {NIK.sub('', r['item'])[:40]}")
body = {}
for w in re.findall(r"[א-ת]{3,}", NIK.sub("", (ROOT / "paper" / "paper.md").read_text(encoding="utf-8"))):
    body.setdefault(skel(w), w)
GENERIC = {"בר", "בן", "רב", "רבי", "של", "בית", "בי", "איש"}
for path in sys.argv[1:]:
    print("==", Path(path).name)
    for r in csv.DictReader(open(path, encoding="utf-8-sig", newline="")):
        if r["Generated: status"] != "new":
            continue
        form = re.sub(r"\(.*?\)|X", " ", r["Generated: Hebrew form"])
        ws = [w for w in re.findall(r"[א-ת]{3,}", form) if w not in GENERIC]
        hits = sorted({h for w in ws for h in words.get(skel(w), set())})
        bh = sorted({body[skel(w)] for w in ws if skel(w) in body})
        if hits or bh:
            print(f"  {r['Generated: Hebrew form']} | items: {' || '.join(hits)[:200]} | body: {', '.join(bh)}")
