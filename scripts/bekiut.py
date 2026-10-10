"""Map Sefaria URLs to Bekiut URLs.

Bekiut section anchors use the Sefaria segment number (checked on
bekiut.com/talmud/Berakhot/2a: section #n links to Sefaria Berakhot.2a.n).

Routes:
  Bavli       Berakhot.2a.2                    -> /talmud/Berakhot/2a#2
  Yerushalmi  Jerusalem_Talmud_Berakhot.3.1.19 -> /yerushalmi/Berakhot/3.1#19
  Mishnah     Mishnah_Shekalim.1.4             -> /mishnah/Shekalim/1#4
  Bible       I_Chronicles.4.5                 -> /bible/i-chronicles/4#5
  Jastrow     Jastrow,_<headword>.1            -> /jastrow?q=<headword>
Anything else (Midrash, Tosefta, commentaries, sheets, search) stays on Sefaria.
"""
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

BASE = "https://bekiut.com"


class Sitemap:
    def __init__(self, path: Path):
        urls = path.read_text(encoding="utf-8").split()
        self.paths = {urlsplit(u).path for u in urls}
        self.talmud = {p.split("/")[2] for p in self.paths if p.startswith("/talmud/") and p.count("/") == 3}
        self.yerushalmi = {p.split("/")[2] for p in self.paths if p.startswith("/yerushalmi/") and p.count("/") >= 2}
        self.mishnah = {p.split("/")[2] for p in self.paths if p.startswith("/mishnah/") and p.count("/") >= 2}
        self.bible = {p.split("/")[2] for p in self.paths if p.startswith("/bible/") and p.count("/") >= 2}

    def has(self, path: str) -> bool:
        return path in self.paths


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _match(name: str, options: set) -> str | None:
    if name in options:
        return name
    n = _norm(name)
    for o in options:
        if _norm(o) == n:
            return o
    return None


def _bible_slug(book: str, options: set) -> str | None:
    slug = book.replace("_", "-").lower()
    if slug in options:
        return slug
    return _match(book, options)


SEG = r"(\d+)(?:[-–]\S+)?"  # first segment number; ranges point at the first segment


def to_bekiut(url: str, sm: Sitemap):
    """Return (bekiut_url, kind, sefaria_ref) or (None, reason, ref)."""
    parts = urlsplit(url)
    if "sefaria.org" not in parts.netloc:
        return None, "not-sefaria", ""
    ref = unquote(parts.path.lstrip("/"))
    if not ref or ref.startswith(("search", "sheets", "texts", "topics")):
        return None, "keep:search-or-sheet", ref

    m = re.match(r"^Jastrow,[ _](.+?)(?:\.\d+)*$", ref)
    if m:
        hw = m.group(1).replace("_", " ")
        return f"{BASE}/jastrow?q={quote(hw)}", "jastrow", ref

    m = re.match(r"^Jerusalem_Talmud_(.+?)\.(\d+)\.(\d+)(?:\.(\d+))?(?:[-–].*)?$", ref)
    if m:
        tr = _match(m.group(1), sm.yerushalmi)
        if not tr:
            return None, "no-bekiut-tractate", ref
        path = f"/yerushalmi/{tr}/{m.group(2)}.{m.group(3)}"
        anchor = f"#{m.group(4)}" if m.group(4) else ""
        return BASE + path + anchor, "yerushalmi", ref

    m = re.match(r"^Mishnah_(.+?)\.(\d+)(?:\.(\d+))?(?:[-–].*)?$", ref)
    if m:
        tr = _match(m.group(1), sm.mishnah)
        if not tr:
            return None, "no-bekiut-tractate", ref
        anchor = f"#{m.group(3)}" if m.group(3) else ""
        return f"{BASE}/mishnah/{tr}/{m.group(2)}{anchor}", "mishnah", ref

    m = re.match(r"^([A-Z][A-Za-z_']+?)\.(\d+[ab])(?:\.(\d+))?(?:[-–:].*)?$", ref)
    if m:
        tr = _match(m.group(1), sm.talmud)
        if tr:
            anchor = f"#{m.group(3)}" if m.group(3) else ""
            return f"{BASE}/talmud/{tr}/{m.group(2)}{anchor}", "bavli", ref
        return None, "no-bekiut-tractate", ref

    m = re.match(r"^([A-Za-z_]+?)\.(\d+)(?:\.(\d+))?(?:[-–].*)?$", ref)
    if m:
        slug = _bible_slug(m.group(1), sm.bible)
        if slug:
            anchor = f"#{m.group(3)}" if m.group(3) else ""
            return f"{BASE}/bible/{slug}/{m.group(2)}{anchor}", "bible", ref
    return None, "keep:not-on-bekiut", ref
