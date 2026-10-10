"""Build the GitHub Pages site from the master files.

Usage: py -3.13 -I scripts/build_site.py
Reads   paper/paper.md, paper/lists/*.csv, paper/tables/*.csv,
        data/bekiut_sitemap_urls.txt, data/ref_overrides.csv, site/*
Writes  docs/index.html   the paper, lists shown as tables
        docs/names.html   every list item in one filterable table
        docs/data/        the list CSVs plus all-items.csv, for download
Needs pandoc on PATH.
"""
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from bekiut import Resolver  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
PAPER, SITE, DOCS = ROOT / "paper", ROOT / "site", ROOT / "docs"
resolve = Resolver(ROOT / "data" / "bekiut_sitemap_urls.txt", ROOT / "data" / "ref_overrides.csv")


def resolve_refs(md: str) -> str:
    """[text](sefaria:Ref) -> [text](https://bekiut.com/... or https://www.sefaria.org/...)."""
    def sub(m):
        ref = m.group(1).replace("\\(", "(").replace("\\)", ")")
        return "](" + resolve(ref).replace("(", "%28").replace(")", "%29") + ")"
    return re.sub(r"\]\(sefaria:((?:\\.|[^)\s\\])+)\)", sub, md)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cell(md: str) -> str:
    md = md.strip()
    return md if md else " "


def list_block(lid: str) -> str:
    rows = read_csv(PAPER / "lists" / f"{lid}.csv")
    out = [f'::::: {{.name-list #list-{lid} data-list="{lid}"}}',
           ":::: {.nl-row .nl-head}", "::: nl-n\n\\#\n:::", "::: nl-item\nName\n:::",
           "::: nl-note\nSources and notes\n:::", "::::"]
    for r in rows:
        cls = ".nl-row .added" if r.get("added") else ".nl-row"
        badge = f' [{r["added"]}]{{.badge}}' if r.get("added") else ""
        out += [f'::::{{{cls} #{lid}-{r["n"]}}}',
                f"::: nl-n\n[{r['n']}](#{lid}-{r['n']})\n:::",
                f"::: nl-item\n{cell(r['item'])}{badge}\n:::",
                f"::: nl-note\n{cell(r['note'])}\n:::",
                "::::"]
    out.append(":::::")
    return "\n\n".join(out)


def table_block(tid: str) -> str:
    rows = list(csv.reader(open(PAPER / "tables" / f"{tid}.csv", encoding="utf-8-sig")))
    esc = lambda c: c.replace("|", "\\|") or " "  # noqa: E731
    lines = ["| " + " | ".join(esc(c) for c in rows[0]) + " |",
             "|" + "|".join("---" for _ in rows[0]) + "|"]
    lines += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows[1:]]
    return f"::: {{.data-table #table-{tid}}}\n\n" + "\n".join(lines) + "\n\n:::"


def pandoc(md: str, out: Path, template: Path, toc: bool, meta: dict):
    args = ["pandoc", "-f", "markdown-smart", "-t", "html5", "--standalone",
            "--template", str(template), "--wrap=none"]
    if toc:
        args += ["--toc", "--toc-depth=3"]
    for k, v in meta.items():
        args += ["-M", f"{k}={v}"]
    args += ["-o", str(out)]
    subprocess.run(args, input=md.encode("utf-8"), check=True)


def main():
    text = (PAPER / "paper.md").read_text(encoding="utf-8")
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = dict(re.findall(r'^(\w+):\s*"(.*)"\s*$', fm.group(1), re.M))
    body = text[fm.end():]

    # section heading for each placeholder, for the names index
    section_of, current = {}, ("", "")
    for line in body.split("\n"):
        h = re.match(r"^#{1,6} (.*?) \{#([^}]+)\}$", line)
        if h:
            current = (re.sub(r"\[\^\d+\]", "", h.group(1)).replace("\\", "").strip(), h.group(2))
        p = re.match(r"^\{\{list:([^}]+)\}\}$", line)
        if p:
            section_of[p.group(1)] = current

    body = re.sub(r"^\{\{list:([^}]+)\}\}$", lambda m: list_block(m.group(1)), body, flags=re.M)
    body = re.sub(r"^\{\{table:([^}]+)\}\}$", lambda m: table_block(m.group(1)), body, flags=re.M)
    body = resolve_refs(body)

    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "data").mkdir(parents=True)
    for f in ("style.css", "app.js"):
        shutil.copy(SITE / f, DOCS / f)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    meta_all = {"title": meta.get("title", ""), "author": meta.get("author", ""),
                "version": meta.get("version", ""), "lang": "en"}
    pandoc(body, DOCS / "index.html", SITE / "template.html", True, {**meta_all, "page": "paper"})

    # names index: one row per list item, with its section
    all_rows = []
    parts = ["::::: {.name-list .names-index #names-index}",
             ":::: {.nl-row .nl-head}", "::: nl-sec\nSection\n:::", "::: nl-item\nName\n:::",
             "::: nl-note\nSources and notes\n:::", "::::"]
    for lid, (sec, sid) in section_of.items():
        for r in read_csv(PAPER / "lists" / f"{lid}.csv"):
            all_rows.append({"list": lid, "section": sec, **r})
            cls = ".nl-row .added" if r.get("added") else ".nl-row"
            badge = f' [{r["added"]}]{{.badge}}' if r.get("added") else ""
            parts += [f"::::{{{cls}}}",
                      f"::: nl-sec\n[{sec}](index.html#{lid}-{r['n']})\n:::",
                      f"::: nl-item\n{cell(r['item'])}{badge}\n:::",
                      f"::: nl-note\n{cell(r['note'])}\n:::", "::::"]
    parts.append(":::::")
    pandoc(resolve_refs("\n\n".join(parts)), DOCS / "names.html", SITE / "template.html", False,
           {**meta_all, "page": "names", "pagetitle": "All list items — " + meta.get("title", "")})

    for f in (PAPER / "lists").glob("*.csv"):
        shutil.copy(f, DOCS / "data" / f.name)
    for f in (PAPER / "tables").glob("*.csv"):
        shutil.copy(f, DOCS / "data" / f"table-{f.name}")
    with open(DOCS / "data" / "all-items.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["list", "section", "n", "item", "note", "added", "review"])
        w.writeheader()
        w.writerows(all_rows)

    print("built docs/: lists", len(section_of), "items", len(all_rows))
    print("ref links:", resolve.stats)


if __name__ == "__main__":
    main()
