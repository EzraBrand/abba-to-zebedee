"""Parse inline Markdown links from the Google Docs Markdown export.

Google Docs escapes parentheses inside URLs as \\( and \\), and link text can
contain nested brackets, so a plain regex is not reliable. This module scans
for "](" and reads the URL up to the matching unescaped ")".
"""
import re
from dataclasses import dataclass

FOOTNOTE_DEF = re.compile(r"^\[\^(\d+)\]:", re.M)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*(\{#[^}]*\})?\s*$", re.M)


@dataclass
class Link:
    start: int  # offset of "[" of the link text
    url_start: int  # offset of first URL char
    url_end: int  # offset after last URL char
    text: str
    raw_url: str  # as written in the file (may contain backslash escapes)

    @property
    def url(self) -> str:
        return unescape_url(self.raw_url)


def unescape_url(raw: str) -> str:
    return re.sub(r"\\([\\()\[\]_*#+\-.!~])", r"\1", raw)


def escape_url(url: str) -> str:
    return url.replace("(", r"\(").replace(")", r"\)")


def find_links(md: str) -> list[Link]:
    links = []
    i = 0
    while True:
        j = md.find("](", i)
        if j < 0:
            break
        # walk back to the matching "[" (same line, allow nested brackets)
        depth = 0
        k = j
        start = -1
        while k >= 0 and md[k] != "\n":
            c = md[k]
            if c == "]" and (k == 0 or md[k - 1] != "\\"):
                depth += 1
            elif c == "[" and (k == 0 or md[k - 1] != "\\"):
                depth -= 1
                if depth == 0:
                    start = k
                    break
            k -= 1
        # read URL to the matching unescaped ")"
        u0 = j + 2
        p = u0
        par = 0
        while p < len(md) and md[p] not in "\n":
            c = md[p]
            if c == "\\" and p + 1 < len(md):
                p += 2
                continue
            if c == "(":
                par += 1
            elif c == ")":
                if par == 0:
                    break
                par -= 1
            elif c == " ":
                break
            p += 1
        raw = md[u0:p]
        if start >= 0 and p < len(md) and md[p] == ")":
            text = md[start + 1: j]
            if text.startswith("^"):  # footnote reference like [^12] is not followed by "("
                pass
            links.append(Link(start, u0, p, text, raw))
        i = j + 2
    return links


def location_index(md: str):
    """Return a function offset -> (section heading, footnote number or '')."""
    heads = [(m.start(), m.group(2).strip()) for m in HEADING.finditer(md)]
    notes = [(m.start(), m.group(1)) for m in FOOTNOTE_DEF.finditer(md)]
    first_note = notes[0][0] if notes else len(md)

    def locate(off: int):
        sec = ""
        for s, h in heads:
            if s <= off:
                sec = h
            else:
                break
        fn = ""
        if off >= first_note:
            for s, n in notes:
                if s <= off:
                    fn = n
                else:
                    break
        return sec, fn

    return locate


def footnote_ref_sections(md: str) -> dict:
    """Map footnote number -> heading of the body text that cites it."""
    body_end = FOOTNOTE_DEF.search(md)
    body = md[: body_end.start()] if body_end else md
    heads = [(m.start(), m.group(2).strip()) for m in HEADING.finditer(body)]
    out = {}
    for m in re.finditer(r"\[\^(\d+)\](?!:)", body):
        sec = ""
        for s, h in heads:
            if s <= m.start():
                sec = h
            else:
                break
        out.setdefault(m.group(1), sec)
    return out
