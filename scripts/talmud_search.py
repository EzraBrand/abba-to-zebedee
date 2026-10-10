"""Search the Bavli (Sefaria export: William Davidson Aramaic + Steinsaltz English) and
return Bekiut segment links.

Sefaria stores each tractate as an array of dapim (index 0 = 1a, 1 = 1b, 2 = 2a ...),
each an array of segments. Segment n (1-based) is the Bekiut anchor #n.

Usage:
  py -3.13 -I scripts/talmud_search.py "<regex>" [--en] [--max 20] [--count] [--show-other]
  --en          search the English (Steinsaltz) text instead of the Hebrew
  --show-other  also print the other language of each matching segment
Hebrew matching ignores nikud and HTML; the pattern is a Python regex.
"""
import argparse
import json
import pickle
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "external" / "sefaria-export"
CACHE = ROOT / "build" / "bavli_segments_sefaria.pkl"
NIKUD = re.compile(r"[֑-ׇ]")
TAGS = re.compile(r"<[^>]+>")


def daf_name(i: int) -> str:
    return f"{i // 2 + 1}{'a' if i % 2 == 0 else 'b'}"


def clean(s: str, he: bool) -> str:
    s = TAGS.sub("", s)
    if he:
        s = NIKUD.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def load():
    files = sorted(SRC.glob("*.Hebrew.json"))
    newest = max(f.stat().st_mtime for f in SRC.glob("*.json"))
    if CACHE.exists() and CACHE.stat().st_mtime > newest:
        return pickle.loads(CACHE.read_bytes())
    segs = []
    for fh in files:
        tr = fh.name.split(".")[0]
        he = json.loads(fh.read_text(encoding="utf-8"))["text"]
        en = json.loads((SRC / f"{tr}.English.json").read_text(encoding="utf-8"))["text"]
        for i, daf in enumerate(he):
            en_daf = en[i] if i < len(en) else []
            for n, seg in enumerate(daf, start=1):
                e = en_daf[n - 1] if n - 1 < len(en_daf) else ""
                segs.append((tr, daf_name(i), n, clean(seg, True), clean(e, False)))
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_bytes(pickle.dumps(segs))
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--en", action="store_true")
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--show-other", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    rx = re.compile(a.pattern, re.I if a.en else 0)
    col = 4 if a.en else 3
    hits = [s for s in load() if rx.search(s[col])]
    print(f"{len(hits)} segments")
    if a.count:
        return
    for s in hits[: a.max]:
        tr, daf, n = s[:3]
        text = s[col]
        m = rx.search(text)
        lo, hi = max(0, m.start() - 80), m.end() + 80
        print(f"{tr} {daf}:{n}\thttps://bekiut.com/talmud/{tr}/{daf}#{n}\t…{text[lo:hi]}…")
        if a.show_other:
            other = s[3] if a.en else s[4]
            print(f"    [{'he' if a.en else 'en'}] {other[:400]}")


if __name__ == "__main__":
    main()
