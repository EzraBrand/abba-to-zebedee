# Link check — v18.2

Checked 1001 unique URLs (1086 links in the paper). Run `scripts/check_links.py` to repeat.

| Result | URLs |
|---|---|
| ok | 904 |
| manual | 70 |
| redirect | 27 |

- **ok**: the page exists (Wikimedia and Sefaria through their APIs; other sites by HTTP).
- **redirect**: the page moved. Non-Sefaria redirects are now updated in `paper/` (`scripts/apply_link_fixes.py`). Sefaria search links only reorder their parameters.
- **manual**: the site blocks scripts (Cloudflare, Academia.edu, Facebook). These need a check in a browser.
- **dead**: the page does not exist.

## Dead links

None.

## Manual check needed

| Site | URLs | Why |
|---|---|---|
| www.hamichlol.org.il | 54 | hamichlol blocks scripts (403) |
| www.academia.edu | 11 | site blocks scripts |
| lsj.gr | 2 | Cloudflare challenge |
| academic.oup.com | 1 | site blocks scripts |
| judaism.stackexchange.com | 1 | 403 to scripts |
| www.facebook.com | 1 | Facebook refuses scripts |

Hamichlol pages that also exist on he.wikipedia (possible replacement):

- מר עוקבא – המכלול → https://he.wikipedia.org/wiki/%D7%9E%D7%A8_%D7%A2%D7%95%D7%A7%D7%91%D7%90
- רבה יוסי – המכלול → https://he.wikipedia.org/wiki/%D7%A8%D7%91%D7%94_%D7%99%D7%95%D7%A1%D7%99
- רבינא האחרון – המכלול → https://he.wikipedia.org/wiki/%D7%A8%D7%91%D7%99%D7%A0%D7%90_%D7%94%D7%90%D7%97%D7%A8%D7%95%D7%9F
- רבי שמעון בר אבא – המכלול → https://he.wikipedia.org/wiki/%D7%A8%D7%91%D7%99_%D7%A9%D7%9E%D7%A2%D7%95%D7%9F_%D7%91%D7%A8_%D7%90%D7%91%D7%90
- רב אהרן → https://he.wikipedia.org/wiki/%D7%A8%D7%91_%D7%90%D7%94%D7%A8%D7%9F
- רפרם (אמורא בדור השביעי) – המכלול → https://he.wikipedia.org/wiki/%D7%99%D7%A9%D7%99%D7%91%D7%AA_%D7%A4%D7%95%D7%9E%D7%91%D7%93%D7%99%D7%AA%D7%90
- שמעון אחי עזריה – המכלול → https://he.wikipedia.org/wiki/%D7%A9%D7%9E%D7%A2%D7%95%D7%9F_%D7%90%D7%97%D7%99_%D7%A2%D7%96%D7%A8%D7%99%D7%94

The full list is in `reports/link_check.csv` (filter `check_status`).
