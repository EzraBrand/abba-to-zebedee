"""Check that each report row's example segment contains its Hebrew form (first word of each '/' variant,
parentheses removed). Usage: py -3.13 -I scripts/check_refs.py reports/gazetteer/<file>.csv"""
import csv, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from talmud_search import load  # noqa: E402
seg = {(s[0].replace("_", " "), s[1], s[2]): s[3] for s in load()}
bad = 0
for r in csv.DictReader(open(sys.argv[1], encoding="utf-8-sig", newline="")):
    m = re.match(r"(.+) (\d+[ab]):(\d+)$", r["Bavli: example ref"].strip())
    he = seg.get((m.group(1).replace("_", " "), m.group(2), int(m.group(3)))) if m else None
    form = re.sub(r"\(.*?\)", "", r["Generated: Hebrew form"])
    keys = [re.sub(r"X", "", v).split()[-1] if re.sub(r"X", "", v).split() else "" for v in form.split("/")]
    keys = [k.strip() for k in keys if k.strip() and re.search(r"[א-ת]", k)]
    ok = he is not None and any(k.rstrip("ד") in he or k in he for k in keys)
    if not ok:
        bad += 1
        print("MISMATCH", r["Generated: status"], "|", r["Gazetteer: entry"], "|", r["Generated: Hebrew form"], "|", r["Bavli: example ref"], "|", (he or "NO SEGMENT")[:100])
print("rows checked; mismatches:", bad)
